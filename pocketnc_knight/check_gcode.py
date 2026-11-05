"""Independent check of the posted Knight program. Plain Python; never imports Fusion.

Rebuilds each cutter position from the G-code alone and reports, per operation: A and B, travel
against the machine's limits, the ball cutter against the Knight's mesh, and the shank and
estimated holder against the collet nut and B table. Sampling makes the gouge check approximate, and
the holder is an estimate, so this doesn't replace Penta's simulator. Housing clearance is in
check_machine.py.

Usage: python3 -B check_gcode.py nc/knight.ngc
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import knight_geometry as geo

MM_PER_INCH = 25.4
A_LIMITS_DEG = (-25.0, 135.0)
X_TRAVEL_MM = (-50.8, 64.77)
Y_TRAVEL_MM = (-63.5, 64.77)
Z_TOP_TIP_MM = 151.9144 - 101.4 + 2.54  # Head attach height, gauge length and Z travel top.
B_AXIS_X_MM = 6.05039  # From the machine definition; not yet confirmed on the real machine.
MAX_RPM = 10000
MAX_FEED_IN_PER_MIN = 60.0
RAPID_FEED_IN_PER_MIN = 100.0

TOOL_RADIUS_MM = 3.175 / 2
STICKOUT_MM = 25.4
HOLDER_MM = ((12.0, 8.0), (64.0, 9.5))  # (length, radius); estimated, slightly oversize.
MIN_HARDWARE_GAP_MM = 2.0
ROUGH_STOCK_TO_LEAVE_MM = 0.15
GOUGE_TOLERANCE_MM = 0.05  # Mesh facets and the 0.2 mm map cells limit precision to about this.
CELL_MM = 0.2
MAX_SAMPLES_PER_OPERATION = 4000

_WORD = re.compile(r"([A-Z])(-?\d*\.?\d+)")
_ARC_PLANE_AXES = {"17": (0, 1), "18": (2, 0), "19": (1, 2)}
ARC_STEP_MM = 0.2  # Fitted arcs reach tens of mm in radius, so a straight chord would stray well off the path.


def rotation_matrix(a_deg, b_deg):
    """Part-to-machine rotation: B about table Y, then A about X, signs per the machine file."""
    a, b = math.radians(a_deg), math.radians(b_deg)
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    r_b = [[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]]
    r_a = [[1, 0, 0], [0, ca, -sa], [0, sa, ca]]
    return [[sum(r_a[i][k] * r_b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(matrix, point):
    return tuple(sum(matrix[i][j] * point[j] for j in range(3)) for i in range(3))


def apply_inverse(matrix, point):
    return tuple(sum(matrix[j][i] * point[j] for j in range(3)) for i in range(3))


def tool_frame_to_part(matrix, xyz):
    relative = apply_inverse(matrix, xyz)
    return tuple(relative[i] + geo.WORK_ORIGIN_MM[i] for i in range(3))


def part_to_carriage(matrix, point):
    """Tip position in the Y carriage frame, with the part axis on the B axis."""
    on_axis = apply(matrix, point)
    return (on_axis[0] + B_AXIS_X_MM, on_axis[1], on_axis[2])


def arc_points(start, end, center_offset, is_clockwise, plane_axes):
    """Points along a G2/G3 arc, ending at end. plane_axes are the two axes the arc turns in."""
    u_axis, v_axis = plane_axes
    center_u = start[u_axis] + center_offset[u_axis]
    center_v = start[v_axis] + center_offset[v_axis]
    start_angle = math.atan2(start[v_axis] - center_v, start[u_axis] - center_u)
    end_angle = math.atan2(end[v_axis] - center_v, end[u_axis] - center_u)
    sweep = end_angle - start_angle
    if is_clockwise and sweep >= 0:
        sweep -= 2 * math.pi
    if not is_clockwise and sweep <= 0:
        sweep += 2 * math.pi
    radius = math.hypot(center_offset[u_axis], center_offset[v_axis])
    count = max(1, int(abs(sweep) * radius / ARC_STEP_MM) + 1)
    points = []
    for step in range(1, count + 1):
        fraction = step / count
        angle = start_angle + sweep * fraction
        point = [start[i] + (end[i] - start[i]) * fraction for i in range(3)]
        point[u_axis] = center_u + radius * math.cos(angle)
        point[v_axis] = center_v + radius * math.sin(angle)
        points.append(tuple(point))
    points[-1] = tuple(end)
    return points


def read_operations(path):
    """Yield (name, A, B, moves, max rpm, max feed), each move being (start, end, is_rapid) in tool-frame mm."""
    name, moves, a_deg, b_deg = None, [], 0.0, 0.0
    op_a, op_b = 0.0, 0.0
    xyz, feed, motion, rpm, top_feed = [None] * 3, None, None, 0.0, 0.0
    arc_plane_axes = (0, 1)
    for raw in open(path):
        line = raw.strip()
        if line.startswith("(") and not line.startswith("(AXIS"):
            if moves:
                yield name, op_a, op_b, moves, rpm, top_feed
            name, moves, xyz, rpm, top_feed = line.strip("()"), [], [None] * 3, 0.0, 0.0
            continue
        if "G53" in line:
            xyz = [None] * 3
            continue
        words = dict(_WORD.findall(line))
        if "A" in words or "B" in words:
            a_deg, b_deg = float(words.get("A", a_deg)), float(words.get("B", b_deg))
            xyz = [None] * 3
            continue
        for code in re.findall(r"G(\d+(?:\.\d+)?)", line):
            if code in ("0", "1", "2", "3"):
                motion = code
            elif code in _ARC_PLANE_AXES:
                arc_plane_axes = _ARC_PLANE_AXES[code]
        if "S" in words:
            rpm = max(rpm, float(words["S"]))
        if "F" in words:
            feed = float(words["F"])
        if not any(axis in words for axis in "XYZ"):
            continue
        previous = tuple(xyz)
        for i, axis in enumerate("XYZ"):
            if axis in words:
                xyz[i] = float(words[axis]) * MM_PER_INCH
        if None in xyz or None in previous:
            continue
        if not moves:
            # The program's closing A0 B0 line would otherwise relabel the last section.
            op_a, op_b = a_deg, b_deg
        is_rapid = motion == "0" or (feed is not None and feed >= RAPID_FEED_IN_PER_MIN)
        if not is_rapid and feed is not None:
            top_feed = max(top_feed, feed)
        if motion in ("2", "3"):
            center_offset = tuple(float(words.get(axis, 0.0)) * MM_PER_INCH for axis in "IJK")
            segment_start = previous
            for point in arc_points(previous, tuple(xyz), center_offset, motion == "2", arc_plane_axes):
                moves.append((segment_start, point, is_rapid))
                segment_start = point
        else:
            moves.append((previous, tuple(xyz), is_rapid))
    if moves:
        yield name, op_a, op_b, moves, rpm, top_feed


def knight_triangles():
    """Knight mesh in world mm: same transform as build_model.scaled_knight."""
    mesh = json.load(open(os.path.join(HERE, "knight_mesh.json")))
    nodes = mesh["nodes_mm"]
    scale = geo.KNIGHT_SCALE

    def world(i):
        x, y, z = nodes[3 * i:3 * i + 3]
        return (scale * x, geo.KNIGHT_BASE_Y_MM + scale * (z - geo.SOURCE_BASE_Z_MM), -scale * y)

    points = [world(i) for i in range(len(nodes) // 3)]
    indices = mesh["tris"]
    return [(points[indices[i]], points[indices[i + 1]], points[indices[i + 2]]) for i in range(0, len(indices), 3)]


def height_map(triangles, matrix):
    """For each XY cell of the rotated Knight, the highest surface Z."""
    origin = geo.WORK_ORIGIN_MM
    top = {}
    for triangle in triangles:
        p, q, r = (apply(matrix, tuple(v[i] - origin[i] for i in range(3))) for v in triangle)
        det = (q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1])
        if abs(det) < 1e-12:
            continue
        for i in range(int(math.floor(min(p[0], q[0], r[0]) / CELL_MM)), int(math.ceil(max(p[0], q[0], r[0]) / CELL_MM)) + 1):
            for j in range(int(math.floor(min(p[1], q[1], r[1]) / CELL_MM)), int(math.ceil(max(p[1], q[1], r[1]) / CELL_MM)) + 1):
                x, y = i * CELL_MM, j * CELL_MM
                u = ((x - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (y - p[1])) / det
                v = ((q[0] - p[0]) * (y - p[1]) - (x - p[0]) * (q[1] - p[1])) / det
                if u < -1e-9 or v < -1e-9 or u + v > 1 + 1e-9:
                    continue
                z = p[2] + u * (q[2] - p[2]) + v * (r[2] - p[2])
                if z > top.get((i, j), -math.inf):
                    top[(i, j)] = z
    return top


def tool_disc():
    """Cells wholly under the cutter, so a neighboring wall isn't counted as a gouge."""
    reach = int(TOOL_RADIUS_MM / CELL_MM) + 1
    margin = TOOL_RADIUS_MM - CELL_MM * 0.71
    return [(i, j) for i in range(-reach, reach + 1) for j in range(-reach, reach + 1)
            if (i * CELL_MM) ** 2 + (j * CELL_MM) ** 2 <= margin ** 2]


def ball_rise(dx_mm, dy_mm):
    """Height of the ball's surface above the tool tip, this far off the tool axis.

    Uses the true offset, not the nearest cell's: the ball is steep near its edge, and rounding
    to a 0.2 mm cell there showed a false 0.36 mm gouge.
    """
    radial_sq = min(dx_mm ** 2 + dy_mm ** 2, TOOL_RADIUS_MM ** 2)
    return TOOL_RADIUS_MM - math.sqrt(TOOL_RADIUS_MM ** 2 - radial_sq)


def hardware_gap(tip, axis):
    """Smallest gap from the shank and holder to the collet nut and B table."""
    stations = [(float(d), TOOL_RADIUS_MM) for d in range(0, int(STICKOUT_MM) + 1, 2)]
    start = STICKOUT_MM
    for length, radius in HOLDER_MM:
        stations += [(start + float(d), radius) for d in range(0, int(length) + 1, 2)]
        start += length
    smallest, name = math.inf, ""
    for label, radius, top_y, bottom_y in (
        ("nut", geo.COLLET_NUT_RADIUS_MM, geo.NUT_TOP_Y_MM, geo.TABLE_TOP_Y_MM),
        ("table", geo.TABLE_RADIUS_MM, geo.TABLE_TOP_Y_MM, geo.TABLE_TOP_Y_MM - 10.0),
    ):
        for distance, tool_radius in stations:
            point = tuple(tip[i] + axis[i] * distance for i in range(3))
            radial_gap = math.hypot(point[0], point[2]) - radius
            tilt_sine = math.hypot(axis[0], axis[2])
            above = point[1] - tool_radius * tilt_sine - top_y
            if above > 0:
                gap = math.hypot(max(radial_gap, 0.0), above)
            else:
                gap = radial_gap - tool_radius * abs(axis[1])
            if gap < smallest:
                smallest, name = gap, label
    return smallest, name


def check(path):
    triangles = knight_triangles()
    disc = tool_disc()
    problems = []
    print(f"{'operation':22s} {'A':>7s} {'B':>8s} {'moves':>7s} {'X range':>15s} {'Y range':>15s} {'tip Z':>6s} {'knight gap':>10s} {'hardware':>12s} {'shoulder':>8s}")
    for name, a_deg, b_deg, moves, rpm, feed in read_operations(path):
        matrix = rotation_matrix(a_deg, b_deg)
        axis = apply_inverse(matrix, (0.0, 0.0, 1.0))
        top = height_map(triangles, matrix)
        allowed_gap = ROUGH_STOCK_TO_LEAVE_MM if name.upper().startswith("ROUGH") else 0.0
        step = max(1, len(moves) // MAX_SAMPLES_PER_OPERATION)
        knight_gap, hardware, hardware_name = math.inf, math.inf, ""
        xs, ys, zs, lowest_y = [], [], [], math.inf
        for index, (_, end, _) in enumerate(moves):
            tip = tool_frame_to_part(matrix, end)
            carriage = part_to_carriage(matrix, tip)
            xs.append(carriage[0]); ys.append(carriage[1]); zs.append(carriage[2])
            if index % step:
                continue
            cx, cy = int(round(end[0] / CELL_MM)), int(round(end[1] / CELL_MM))
            for i, j in disc:
                surface = top.get((cx + i, cy + j))
                if surface is not None:
                    rise = ball_rise((cx + i) * CELL_MM - end[0], (cy + j) * CELL_MM - end[1])
                    knight_gap = min(knight_gap, end[2] + rise - surface)
            if math.hypot(tip[0], tip[2]) < geo.HEAD_RADIUS_MM + TOOL_RADIUS_MM:
                lowest_y = min(lowest_y, tip[1] - TOOL_RADIUS_MM)
            gap, label = hardware_gap(tip, axis)
            if gap < hardware:
                hardware, hardware_name = gap, label
        shoulder_gap = lowest_y - geo.SHOULDER_TOP_Y_MM
        print(f"{name:22s} {a_deg:7.2f} {b_deg:8.2f} {len(moves):7d} {min(xs):7.1f}..{max(xs):6.1f} {min(ys):7.1f}..{max(ys):6.1f} "
              f"{max(zs):6.1f} {knight_gap:10.3f} {hardware:6.1f} {hardware_name:5s} {shoulder_gap:8.2f}")
        if not A_LIMITS_DEG[0] <= a_deg <= A_LIMITS_DEG[1]:
            problems.append(f"{name}: A{a_deg} outside A travel")
        if min(xs) < X_TRAVEL_MM[0] or max(xs) > X_TRAVEL_MM[1]:
            problems.append(f"{name}: X {min(xs):.1f}..{max(xs):.1f} outside travel")
        if min(ys) < Y_TRAVEL_MM[0] or max(ys) > Y_TRAVEL_MM[1]:
            problems.append(f"{name}: Y {min(ys):.1f}..{max(ys):.1f} outside travel")
        if max(zs) > Z_TOP_TIP_MM:
            problems.append(f"{name}: tip Z {max(zs):.1f} above the {Z_TOP_TIP_MM:.1f} limit")
        if rpm > MAX_RPM:
            problems.append(f"{name}: S{rpm} over {MAX_RPM} rpm")
        if feed > MAX_FEED_IN_PER_MIN:
            problems.append(f"{name}: feed {feed} over the axis limit")
        if knight_gap < allowed_gap - GOUGE_TOLERANCE_MM:
            problems.append(f"{name}: cutter {allowed_gap - knight_gap:.3f} mm into the Knight or its stock to leave")
        if hardware < MIN_HARDWARE_GAP_MM:
            problems.append(f"{name}: {hardware:.1f} mm from the {hardware_name}")
        if shoulder_gap < -GOUGE_TOLERANCE_MM:
            problems.append(f"{name}: cuts {-shoulder_gap:.2f} mm into the shoulder")
    return problems


if __name__ == "__main__":
    found = check(sys.argv[1])
    print("\nPROBLEMS:" if found else "\nNo problems found.")
    for problem in found:
        print(" -", problem)
    sys.exit(1 if found else 0)
