"""Paths and limits for the King's milled features, in plain Python so they can be checked outside Fusion.

Lengths are mm at 73% in the model frame: base at z 0, part axis on Z. Every feature repeats every 45 deg of C, and
each is laid out once here, on its seed: the flute and side at C 0, the notch at C 22.5.
"""
import math

# Finial flutes: vertical cylinders cut into the head, read from the model.
FLUTE_AXIS_R_MM = 4.94703
FLUTE_RADIUS_MM = 1.72441
# Where the flute runs out on the finial's cone. Under it the flute's cylinder is outside the cone, so the tool can go
# lower and cut only air, which makes sure the wall is cut to its bottom edge.
FLUTE_RUN_OUT_Z_MM = 80.219
FLUTE_BOTTOM_Z_MM = 80.1
# The flute's top edge is at z 85.02, on the head's upper cone.
FLUTE_TOP_Z_MM = 85.15
T11_RADIUS_MM = 1.0
FLUTE_ROUGH_STOCK_MM = 0.05
# Each depth starts here, with the tool's edge 1 mm clear of the head's widest ridge at r 4.947.
FLUTE_ENTRY_R_MM = 6.95


# The gap left in T11's circle, next to the entry, on the flute's outer side where the head has no metal.
FLUTE_GAP_DEG = 15.0


def _on_circle(radius_mm, angle_deg):
    angle_rad = math.radians(angle_deg)
    return FLUTE_AXIS_R_MM + radius_mm * math.cos(angle_rad), radius_mm * math.sin(angle_rad)


def flute_tool_center_path(stock_mm):
    """Key points of T11's center path in the C 0 flute, as (x, y): entry, two arcs as (start, middle, end), exit.

    Index 0 to 1 is the entry line, 1-2-3 and 3-4-5 the arcs, and 5 to 6 the exit line.
    """
    radius_mm = FLUTE_RADIUS_MM - T11_RADIUS_MM - stock_mm
    last_deg = 360.0 - FLUTE_GAP_DEG
    arc_end = _on_circle(radius_mm, last_deg)
    return [
        (FLUTE_ENTRY_R_MM, 0.0),
        _on_circle(radius_mm, 0.0),
        _on_circle(radius_mm, 90.0),
        _on_circle(radius_mm, 180.0),
        _on_circle(radius_mm, (180.0 + last_deg) / 2),
        arc_end,
        (FLUTE_ENTRY_R_MM, arc_end[1]),
    ]


# Rim notches. Each is a 60 deg V with a round bottom, running through the crown's wall along the cone's normal, and
# every edge is rounded r 0.278. Frame at the C 22.5 seed, read from the model: a point on the bottom cylinder's axis,
# the axis, which runs inward and up, and `NOTCH_UP`, square to it in the radial plane, pointing up the V.
NOTCH_C_DEG = 22.5
NOTCH_ORIGIN_MM = (10.21704, 4.23203, 76.57287)
NOTCH_AXIS = (-0.851186, -0.352573, 0.388811)
NOTCH_UP = (0.359215, 0.148793, 0.921318)
NOTCH_SIDE = (-0.382683, 0.923880, 0.0)
NOTCH_RADIUS_MM = 1.72441
NOTCH_HALF_ANGLE_DEG = 30.0
# T4 runs with its axis along NOTCH_UP: B 22.88 at C 22.5.
NOTCH_B_DEG = math.degrees(math.acos(NOTCH_UP[2]))
T4_RADIUS_MM = 1.5875
NOTCH_ROUGH_STOCK_MM = 0.1
NOTCH_LEVEL_STEP_MM = 0.3
NOTCH_STROKE_STEP_MM = 1.2
# Each stroke starts and ends with the ball this far clear of the metal.
NOTCH_CLEARANCE_MM = 0.4

# What's left around the notch when it's cut: the lathe's crown cone outside, the rings' cup cone inside, and the rim.
CROWN_OUTER_PROFILE = ((6.476, 65.046), (10.197, 74.773), (11.627, 78.514), (11.627, 78.89))
CUP_CONE_LOW = (3.315, 75.676)
CUP_CONE_HIGH = (11.264, 78.869)
RIM_TOP_Z_MM = 78.89


def _interpolate(profile, z_mm):
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z0 <= z_mm <= z1:
            return r0 + (r1 - r0) * (z_mm - z0) / (z1 - z0) if z1 > z0 else max(r0, r1)
    return None


def is_crown_metal(point_mm):
    """Whether a point is in the crown's wall as it stands before the notches."""
    r_mm = math.hypot(point_mm[0], point_mm[1])
    z_mm = point_mm[2]
    if z_mm > RIM_TOP_Z_MM or z_mm < CROWN_OUTER_PROFILE[0][1]:
        return False
    outer_r_mm = _interpolate(CROWN_OUTER_PROFILE, z_mm)
    if outer_r_mm is None or r_mm > outer_r_mm:
        return False
    cup_slope = (CUP_CONE_HIGH[1] - CUP_CONE_LOW[1]) / (CUP_CONE_HIGH[0] - CUP_CONE_LOW[0])
    return z_mm <= CUP_CONE_LOW[1] + (r_mm - CUP_CONE_LOW[0]) * cup_slope


def _sphere_offsets(radius_mm, count=150):
    """Points spread over a sphere, by the golden-angle spiral, plus its center."""
    offsets = [(0.0, 0.0, 0.0)]
    for index in range(count):
        z = 1 - 2 * (index + 0.5) / count
        ring = math.sqrt(1 - z * z)
        angle = index * math.pi * (3 - math.sqrt(5))
        offsets.append((radius_mm * ring * math.cos(angle), radius_mm * ring * math.sin(angle), radius_mm * z))
    return offsets


BALL_OFFSETS = _sphere_offsets(T4_RADIUS_MM)


def does_ball_touch_crown(center_mm, offsets=BALL_OFFSETS):
    return any(is_crown_metal((center_mm[0] + dx, center_mm[1] + dy, center_mm[2] + dz)) for dx, dy, dz in offsets)


def notch_point(s_mm, t_mm, h_mm):
    """Model point at distance s along the notch's axis, t across it and h up the V, from NOTCH_ORIGIN_MM."""
    return tuple(
        NOTCH_ORIGIN_MM[index] + s_mm * NOTCH_AXIS[index] + t_mm * NOTCH_SIDE[index] + h_mm * NOTCH_UP[index]
        for index in range(3)
    )


def notch_half_width_mm(h_mm, stock_mm):
    """How far across the V the ball's center may go at this height and still leave this much on both walls."""
    half_angle_rad = math.radians(NOTCH_HALF_ANGLE_DEG)
    clearance_mm = NOTCH_RADIUS_MM - T4_RADIUS_MM - stock_mm
    return max(0.0, (h_mm * math.sin(half_angle_rad) + clearance_mm) / math.cos(half_angle_rad))


def _stroke_ends(t_mm, h_mm, step_mm=0.05):
    """The s range over which the ball meets metal at this t and h, widened by the clearance, or None."""
    touching = [
        index * step_mm
        for index in range(int(-4 / step_mm), int(9 / step_mm))
        if does_ball_touch_crown(notch_point(index * step_mm, t_mm, h_mm))
    ]
    if not touching:
        return None
    return touching[0] - NOTCH_CLEARANCE_MM, touching[-1] + NOTCH_CLEARANCE_MM


def notch_rough_levels():
    """Ball-center strokes for roughing the seed notch, by level from the top down: lists of (start, end) model points.

    Each level is cut as a zigzag, so a stroke runs the opposite way to the one before it.
    """
    levels = []
    level_count = int(4.0 / NOTCH_LEVEL_STEP_MM)
    for level_index in reversed(range(level_count + 1)):
        h_mm = level_index * NOTCH_LEVEL_STEP_MM
        half_width_mm = notch_half_width_mm(h_mm, NOTCH_ROUGH_STOCK_MM)
        stroke_count = max(1, math.ceil(2 * half_width_mm / NOTCH_STROKE_STEP_MM) + 1)
        if half_width_mm < 0.05:
            sides_mm = [0.0]
        else:
            sides_mm = [-half_width_mm + 2 * half_width_mm * index / (stroke_count - 1) for index in range(stroke_count)]
        strokes = []
        for t_mm in sides_mm:
            ends = _stroke_ends(t_mm, h_mm)
            if ends is None:
                continue
            start, end = notch_point(ends[0], t_mm, h_mm), notch_point(ends[1], t_mm, h_mm)
            strokes.append((end, start) if len(strokes) % 2 else (start, end))
        if strokes:
            levels.append(strokes)
    return levels


def tip_from_center(center_mm, axis, radius_mm=T4_RADIUS_MM):
    return tuple(center_mm[index] - radius_mm * axis[index] for index in range(3))


# Crown facets: flat, 22.9 deg from vertical, facing out and down, read from the model at C 0. Between neighbours the
# crown's cone is left, so a facet is only 2.478 wide each side of its middle. Under each, a concave fillet r 0.556 runs
# into a flat ledge facing up and out.
FACET_NORMAL = (0.921317, 0.0, -0.388811)
FACET_UP = (0.388811, 0.0, 0.921317)
FACET_PLANE_OFFSET_MM = -19.77846
LEDGE_NORMAL = (0.365426, 0.0, 0.930840)
LEDGE_PLANE_OFFSET_MM = 60.94433
FACET_HALF_WIDTH_MM = 2.478
# T2 cuts with its side, its axis up the facet, so one stroke along Y cuts the facet's whole 15.3 mm height.
FACET_B_DEG = math.degrees(math.acos(FACET_UP[2]))
T2_RADIUS_MM = 3.175
# Up the facet from the facet and ledge planes' meeting line. The fillet ends at 0.571 and T10's ball, which cuts the
# fillet, meets the facet at 0.815, so T2's tip sits between them and its end stays clear of the fillet.
FACET_TIP_HEIGHT_MM = 0.75
# The tool's edge stays 0.85 clear of the facet's side, beyond which the cone is inside the facet's plane.
FACET_STROKE_HALF_LENGTH_MM = 6.5
# How far out each return to +Y runs. A trace retracts only along the tool axis, which would drag the flank along the
# face just cut.
FACET_RETURN_OUT_MM = 1.0


def facet_ledge_vertex():
    """Where the facet and ledge planes meet, in the C 0 radial plane, as (x, 0, z)."""
    a, b, c, d = FACET_NORMAL[0], FACET_NORMAL[2], LEDGE_NORMAL[0], LEDGE_NORMAL[2]
    determinant = a * d - b * c
    x_mm = (FACET_PLANE_OFFSET_MM * d - b * LEDGE_PLANE_OFFSET_MM) / determinant
    z_mm = (a * LEDGE_PLANE_OFFSET_MM - c * FACET_PLANE_OFFSET_MM) / determinant
    return x_mm, 0.0, z_mm


def facet_tip_point(y_mm, offset_mm):
    """T2's tip with its side this far out from the facet's plane, at this Y."""
    vertex = facet_ledge_vertex()
    out_mm = T2_RADIUS_MM + offset_mm
    return tuple(
        vertex[index] + FACET_TIP_HEIGHT_MM * FACET_UP[index] + out_mm * FACET_NORMAL[index] + (y_mm if index == 1 else 0.0)
        for index in range(3)
    )


def facet_tip_path(offsets_mm):
    """One chain of strokes from +Y to -Y, a climb cut, each followed by a return out in air."""
    half_mm = FACET_STROKE_HALF_LENGTH_MM
    points = []
    for offset_mm in offsets_mm:
        points += [facet_tip_point(half_mm, offset_mm), facet_tip_point(-half_mm, offset_mm)]
        points += [facet_tip_point(-half_mm, offset_mm + FACET_RETURN_OUT_MM), facet_tip_point(half_mm, offset_mm + FACET_RETURN_OUT_MM)]
    return points[:-1]


# Waist: T10 cuts the fillet under each facet with its axis on the facet and ledge corner's bisector. Its ball, r 0.794,
# is bigger than the fillet's r 0.556, which the user accepted, so it leaves at most 0.1 in the corner.
T10_RADIUS_MM = 0.79375
LEDGE_OUT = (0.930840, 0.0, -0.365426)
# The ledge ends 1.358 out from the vertex, at the collar.
LEDGE_EDGE_MM = 1.358
# The corner stroke runs this much farther out first, so the finishing strokes take a light, even cut.
WAIST_ROUGH_OUT_MM = 0.25
# 0.14 between ledge strokes leaves 0.003 scallops with T10's ball.
WAIST_LEDGE_STEP_MM = 0.14
WAIST_STROKE_HALF_LENGTH_MM = 3.8


def _unit(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


WAIST_AXIS = _unit(tuple(FACET_NORMAL[index] + LEDGE_NORMAL[index] for index in range(3)))
WAIST_B_DEG = math.degrees(math.acos(WAIST_AXIS[2]))


def _corner_half_angle_rad():
    cosine_between_normals = sum(FACET_NORMAL[index] * LEDGE_NORMAL[index] for index in range(3))
    return (math.pi - math.acos(cosine_between_normals)) / 2


def waist_corner_contact_mm():
    """How far from the vertex T10's ball meets both the facet and the ledge, sitting in the corner."""
    return T10_RADIUS_MM / math.tan(_corner_half_angle_rad())


def waist_ball_centers():
    """T10's ball centers in the C 0 radial plane, in cutting order: rough corner, corner, then out along the ledge."""
    vertex = facet_ledge_vertex()
    corner_center_mm = T10_RADIUS_MM / math.sin(_corner_half_angle_rad())
    centers = [
        tuple(vertex[index] + (corner_center_mm + WAIST_ROUGH_OUT_MM) * WAIST_AXIS[index] for index in range(3)),
        tuple(vertex[index] + corner_center_mm * WAIST_AXIS[index] for index in range(3)),
    ]
    contact_mm = waist_corner_contact_mm()
    step_count = math.ceil((LEDGE_EDGE_MM - contact_mm) / WAIST_LEDGE_STEP_MM)
    for step in range(1, step_count + 1):
        along_mm = contact_mm + (LEDGE_EDGE_MM - contact_mm) * step / step_count
        centers.append(tuple(vertex[index] + along_mm * LEDGE_OUT[index] + T10_RADIUS_MM * LEDGE_NORMAL[index] for index in range(3)))
    return centers


def waist_tip_path():
    """A zigzag of strokes along Y through the ball centers, as T10 tip points."""
    half_mm = WAIST_STROKE_HALF_LENGTH_MM
    points = []
    for index, (x_mm, _, z_mm) in enumerate(waist_ball_centers()):
        ends = [(x_mm, half_mm, z_mm), (x_mm, -half_mm, z_mm)]
        points += ends if index % 2 == 0 else ends[::-1]
    return [tip_from_center(point, WAIST_AXIS, T10_RADIUS_MM) for point in points]


# Octagonal shaft: each side is ruled along Y at C 0, so a tool lying along Y (B 90, C 90) cuts a whole side with its
# flank in one contour. The C 0 profile, bottom up, read from the model: (start, end, arc center or None for a line).
# Both arcs are concave, with their centers outside the part.
OCTAGON_PROFILE = (
    ((8.8243, 25.8435), (6.1011, 34.6589), (28.1859, 36.6528)),
    ((6.1011, 34.6589), (5.8780, 37.1308), None),
    ((5.8780, 37.1308), (5.6385, 42.7548), (64.9348, 42.4629)),
    ((5.6385, 42.7548), (5.6675, 48.6570), None),
)
OCTAGON_SIDE_HALF_WIDTH_MM = 3.66
OCTAGON_PROFILE_STEP_MM = 0.02


def _profile_piece_points(start, end, center, step_mm):
    """Points along one piece with their outward normals, as ((x, z), (nx, nz))."""
    if center is None:
        length_mm = math.dist(start, end)
        count = max(1, math.ceil(length_mm / step_mm))
        tangent = ((end[0] - start[0]) / length_mm, (end[1] - start[1]) / length_mm)
        normal = (tangent[1], -tangent[0])
        return [((start[0] + (end[0] - start[0]) * i / count, start[1] + (end[1] - start[1]) * i / count), normal) for i in range(count + 1)]
    radius_mm = math.dist(start, center)
    angle_start = math.atan2(start[1] - center[1], start[0] - center[0])
    angle_end = math.atan2(end[1] - center[1], end[0] - center[0])
    # The shorter way round: the R 59.3 arc's ends straddle the angle's wrap at 180 deg.
    angle_end = angle_start + math.remainder(angle_end - angle_start, 2 * math.pi)
    count = max(1, math.ceil(abs(angle_end - angle_start) * radius_mm / step_mm))
    points = []
    for i in range(count + 1):
        angle = angle_start + (angle_end - angle_start) * i / count
        offset = (math.cos(angle), math.sin(angle))
        # Concave, so outward from the metal is toward the center.
        points.append(((center[0] + radius_mm * offset[0], center[1] + radius_mm * offset[1]), (-offset[0], -offset[1])))
    return points


def octagon_profile_points(step_mm=OCTAGON_PROFILE_STEP_MM):
    """The C 0 profile, bottom up, as ((x, z), outward normal) pairs."""
    points = []
    for start, end, center in OCTAGON_PROFILE:
        piece = _profile_piece_points(start, end, center, step_mm)
        points += piece if not points else piece[1:]
    return points


def octagon_center_path(tool_radius_mm, z_low_mm, z_high_mm):
    """The tool's center in XZ for contact between these heights: the profile pushed out by the tool's radius."""
    return [
        (x_mm + tool_radius_mm * nx, z_mm + tool_radius_mm * nz)
        for (x_mm, z_mm), (nx, nz) in octagon_profile_points()
        if z_low_mm <= z_mm <= z_high_mm
    ]


# Where each tool can touch the side, from octagon_reach in the checks: the base stops T2 below 25.966 and the collar's
# underside above 47.939. T4 reaches the whole side and cleans the two strips T2 can't.
OCTAGON_T2_CONTACT_Z_MM = (25.97, 47.93)
OCTAGON_T4_STRIPS_Z_MM = ((25.844, 26.3), (47.6, 48.657))
# Tips past the side's -Y edge, so the flank spans the side's 3.66 half width. A ball's flank starts a radius up.
OCTAGON_T2_TIP_Y_MM = -4.5
OCTAGON_T4_TIP_Y_MM = -5.4
# Each contour starts and ends this far out, clear of the lathe's corner stock, up to 0.73 thick.
OCTAGON_ENTRY_OUT_MM = 1.5
# Leaving under the collar, a move straight out would rise into its underside, so the exit drops as it goes out.
OCTAGON_EXIT_UNDER_COLLAR = (math.sqrt(0.5), -math.sqrt(0.5))
OCTAGON_PATH_STEP_MM = 0.25


def octagon_tip_chain(tool_radius_mm, offset_mm, z_range_mm, tip_y_mm, is_exit_under_collar):
    """Tip points for one contour up the C 0 side, from an entry in air to an exit in air: climb, since up is climb."""
    reach_mm = tool_radius_mm + offset_mm
    profile = [point for point in octagon_profile_points() if z_range_mm[0] <= point[0][1] <= z_range_mm[1]]
    stride = max(1, round(OCTAGON_PATH_STEP_MM / OCTAGON_PROFILE_STEP_MM))
    profile = profile[::stride] + ([profile[-1]] if (len(profile) - 1) % stride else [])
    centers = [(x + reach_mm * nx, z + reach_mm * nz) for (x, z), (nx, nz) in profile]
    first_normal, last_normal = profile[0][1], profile[-1][1]
    exit_direction = OCTAGON_EXIT_UNDER_COLLAR if is_exit_under_collar else last_normal
    entry = (centers[0][0] + OCTAGON_ENTRY_OUT_MM * first_normal[0], centers[0][1] + OCTAGON_ENTRY_OUT_MM * first_normal[1])
    exit_point = (centers[-1][0] + OCTAGON_ENTRY_OUT_MM * exit_direction[0], centers[-1][1] + OCTAGON_ENTRY_OUT_MM * exit_direction[1])
    return [(x, tip_y_mm, z) for x, z in [entry] + centers + [exit_point]]


# The lathe leaves this much outside the octagon's corners, so each seam is cut by the two side passes and comes out
# sharp. Turned exactly to the corner radius, the lathe's own small undercuts left a turned strip along every seam.
CORNER_STOCK_MM = 0.1
# The stock tapers to nothing over this length at each end, where revolved cones clip the corners. No mill pass touches
# those cones, so the lathe must finish them to size.
CORNER_STOCK_RAMP_MM = 1.0
# Where the clipping cones meet the corner edges, read from the lathe target's sketch.
CORNER_EDGE_Z_MM = (27.6482, 45.4075)


def octagon_corner_radius_mm(z_mm):
    """The corner edge's distance from the part axis at this height: the side's apothem over cos 22.5 deg."""
    profile = octagon_profile_points()
    for ((x0, z0), _), ((x1, z1), _) in zip(profile, profile[1:]):
        if z0 <= z_mm <= z1:
            apothem_mm = x0 + (x1 - x0) * (z_mm - z0) / (z1 - z0)
            return apothem_mm / math.cos(math.radians(22.5))
    raise ValueError(f"z {z_mm} is outside the octagon's profile")


def corner_stock_points(step_mm=0.25):
    """The lathe target's (r, z) through the corner span, bottom up, with the stock ramped in and out at the ends."""
    z_low, z_high = CORNER_EDGE_Z_MM
    count = math.ceil((z_high - z_low) / step_mm)
    points = []
    for index in range(count + 1):
        z_mm = z_low + (z_high - z_low) * index / count
        from_end_mm = min(z_mm - z_low, z_high - z_mm)
        ramp = min(1.0, from_end_mm / CORNER_STOCK_RAMP_MM)
        # Smoothstep, so the target meets the clipping cones without a kink.
        stock_mm = CORNER_STOCK_MM * ramp * ramp * (3 - 2 * ramp)
        points.append((octagon_corner_radius_mm(z_mm) + stock_mm, z_mm))
    return points
