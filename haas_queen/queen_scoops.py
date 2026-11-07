"""The straight strokes that cut the Queen's crown scoops. Plain Python, so it can be tested outside Fusion.

Each scoop is a cylinder r 4.44 whose axis points out and down. Any ball kept inside that cylinder can't touch the
finished part, because the model has no metal inside it, so straight strokes along the cylinder need no surface check.
Lengths are mm at 73%, in the plane of the scoop at C 0: u runs along the cylinder's axis, outward and downward, y is
across the scoop, and w points out of the scoop's floor, up and outward.
"""
import json
import math
import os

FACES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queen_faces.json")
TARGET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queen_lathe_profile.json")

SCOOP_RADIUS_MM = 4.44
AXIS_ORIGIN_R_MM = 11.883
AXIS_ORIGIN_Z_MM = 77.925
AXIS_SIN = 0.867
AXIS_COS = 0.499
SCOOP_FACE_AT_C0 = 270
TILT_B_DEG = 60.0

T3_RADIUS_MM = 2.38125
T4_RADIUS_MM = 1.5875
ROUGH_STOCK_MM = 0.2
ROUGH_LAYERS_ABOVE_FLOOR_MM = (1.86, 1.2, 0.6, 0.0)
ROUGH_STEPOVER_MM = 1.2
FINISH_STEPOVER_MM = 0.15
# How far a finish stroke runs past the face's own ends.
STROKE_OVERRUN_MM = 0.3
# A roughing stroke starts and stops this far outside the lathe's stock, so it enters in air.
STOCK_CLEARANCE_MM = 0.5
# T3 can't come closer than this to the part axis: the turned stub under the finial is r 2.
CLOSEST_TOOL_R_MM = 2.3


def to_section(r_mm, z_mm):
    """(r, z) in the plane of the scoop to (u, w) from the cylinder's axis."""
    dr, dz = r_mm - AXIS_ORIGIN_R_MM, z_mm - AXIS_ORIGIN_Z_MM
    return dr * AXIS_SIN - dz * AXIS_COS, dr * AXIS_COS + dz * AXIS_SIN


def from_section(u_mm, w_mm):
    """(u, w) from the cylinder's axis to (r, z) in the plane of the scoop."""
    return (
        AXIS_ORIGIN_R_MM + u_mm * AXIS_SIN + w_mm * AXIS_COS,
        AXIS_ORIGIN_Z_MM - u_mm * AXIS_COS + w_mm * AXIS_SIN,
    )


def tip_of(u_mm, y_mm, w_mm, ball_radius_mm, c_deg):
    """The tool tip for a ball center at this point, as (x, y, z) in the model, turned to this C."""
    r_mm, z_mm = from_section(u_mm, w_mm)
    b_rad = math.radians(TILT_B_DEG)
    x_tip = r_mm - ball_radius_mm * math.sin(b_rad)
    z_tip = z_mm - ball_radius_mm * math.cos(b_rad)
    c_rad = math.radians(c_deg)
    return (
        x_tip * math.cos(c_rad) - y_mm * math.sin(c_rad),
        x_tip * math.sin(c_rad) + y_mm * math.cos(c_rad),
        z_tip,
    )


def face_samples():
    """The scoop face's nodes as (angle around the cylinder in degrees, u)."""
    with open(FACES_PATH) as faces_file:
        face = next(entry for entry in json.load(faces_file) if entry["index"] == SCOOP_FACE_AT_C0)
    samples = []
    nodes = face["nodes_mm"]
    for start in range(0, len(nodes), 3):
        x_mm, y_mm, z_mm = nodes[start:start + 3]
        u_mm, w_mm = to_section(x_mm, z_mm)
        samples.append((math.degrees(math.atan2(y_mm, -w_mm)), u_mm))
    return samples


def finish_path():
    """One zigzag of T4 centers. Links between strokes stay on the cylinder's chord, so they can't touch the part."""
    samples = face_samples()
    largest_angle_deg = max(abs(angle_deg) for angle_deg, _ in samples)
    step_deg = math.degrees(FINISH_STEPOVER_MM / SCOOP_RADIUS_MM)
    count = math.ceil(2 * largest_angle_deg / step_deg)
    center_radius_mm = SCOOP_RADIUS_MM - T4_RADIUS_MM
    path = []
    for index in range(count + 1):
        angle_deg = -largest_angle_deg + 2 * largest_angle_deg * index / count
        near = [u_mm for sample_deg, u_mm in samples if abs(sample_deg - angle_deg) <= 2 * step_deg]
        if not near:
            continue
        angle_rad = math.radians(angle_deg)
        y_mm = center_radius_mm * math.sin(angle_rad)
        w_mm = -center_radius_mm * math.cos(angle_rad)
        low = (min(near) - STROKE_OVERRUN_MM, y_mm, w_mm)
        high = (max(near) + STROKE_OVERRUN_MM, y_mm, w_mm)
        path.extend((low, high) if len(path) % 4 == 0 else (high, low))
    return path


def target_outline():
    """The lathe target's outline near the crown, as (r, z) segments, from the faces above the flutes."""
    with open(TARGET_PATH) as profile_file:
        faces = json.load(profile_file)
    segments = []
    for face in faces:
        nodes = sorted(map(tuple, face["rz_mm"]), key=lambda node: (node[1], node[0]))
        if nodes[-1][1] < 70.0:
            continue
        segments.extend(zip(nodes, nodes[1:]))
    return segments


def _distance_to_segment(point, segment):
    (ax, ay), (bx, by) = segment
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    fraction = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / length_sq))
    return math.hypot(point[0] - ax - fraction * dx, point[1] - ay - fraction * dy)


def _ball_is_near_stock(u_mm, y_mm, w_mm, segments, ball_radius_mm):
    r_mm, z_mm = from_section(u_mm, w_mm)
    part_radius_mm = math.hypot(r_mm, y_mm)
    gap_mm = min(_distance_to_segment((part_radius_mm, z_mm), segment) for segment in segments)
    is_under_outline = z_mm < 76.5 and part_radius_mm < 9.0
    return is_under_outline or gap_mm < ball_radius_mm + STOCK_CLEARANCE_MM


def rough_strokes():
    """T3 centers, one stroke per list, each from the inner end out, so the ball ramps into the stock from air."""
    center_radius_mm = SCOOP_RADIUS_MM - T3_RADIUS_MM - ROUGH_STOCK_MM
    segments = target_outline()
    strokes = []
    for height_mm in ROUGH_LAYERS_ABOVE_FLOOR_MM:
        half_width_mm = math.sqrt(max(center_radius_mm ** 2 - (center_radius_mm - height_mm) ** 2, 0.0))
        count = math.ceil(half_width_mm / ROUGH_STEPOVER_MM)
        w_mm = -center_radius_mm + height_mm
        offsets = [half_width_mm * index / count for index in range(-count, count + 1)] if count else [0.0]
        for y_mm in offsets:
            u_values = [-8.0 + index * 0.1 for index in range(141)]
            inside = [u_mm for u_mm in u_values if _ball_is_near_stock(u_mm, y_mm, w_mm, segments, T3_RADIUS_MM)]
            if inside:
                low_u_mm = max(min(inside), _closest_allowed_u(w_mm))
                strokes.append([(low_u_mm, y_mm, w_mm), (max(inside), y_mm, w_mm)])
    return strokes


def _closest_allowed_u(w_mm):
    """The smallest u where T3's side stays CLOSEST_TOOL_R_MM from the part axis."""
    return (CLOSEST_TOOL_R_MM + T3_RADIUS_MM - AXIS_ORIGIN_R_MM - w_mm * AXIS_COS) / AXIS_SIN
