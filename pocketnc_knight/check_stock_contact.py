"""Replays the posted program against the stock as it shrinks, to find contact with uncut wax.

check_gcode.py only tests the finished Knight and fixed hardware, so it can't see these:
  rapid   a rapid or high-feed move passes through wax
  shank   the smooth shank above the flutes reaches wax the flutes haven't cut
  holder  the holder reaches uncut wax

Each operation builds a map in its tool frame: for each XY cell, the highest wax still there. Moves
are tested against the map in program order, and cutting moves lower it. Sampling limits precision, so
only contact deeper than 0.15 mm is reported, and coarser grids invent contact, so don't raise SAMPLE_MM
or CELL_MM. Takes several minutes.

Usage: python3 -B check_stock_contact.py nc/knight.ngc   (exit 1 if contact is found)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_gcode
import knight_geometry as geo

SAMPLE_MM = 0.25
CELL_MM = 0.25
REPORT_DEPTH_MM = 0.15
FLUTE_LENGTH_MM = 9.525
TOOL_RADIUS_MM = check_gcode.TOOL_RADIUS_MM
STICKOUT_MM = check_gcode.STICKOUT_MM
HOLDER_RADIUS_MM = 8.0


def _disc(radius_mm):
    """Cells whose whole area lies inside the radius, so a neighboring wall isn't counted."""
    reach = int(radius_mm / CELL_MM) + 1
    margin = radius_mm - CELL_MM * 0.71
    return [(i, j) for i in range(-reach, reach + 1) for j in range(-reach, reach + 1)
            if (i * CELL_MM) ** 2 + (j * CELL_MM) ** 2 <= margin ** 2]


_TOOL_DISC = _disc(TOOL_RADIUS_MM)
# Removal reaches the cutter's true edge. Stopping at the contact disc above would leave a false
# sliver along every wall, and the next pass would report it as a shank touching wax.
_CUT_CELLS = [(i, j, TOOL_RADIUS_MM - math.sqrt(TOOL_RADIUS_MM ** 2 - (i * CELL_MM) ** 2 - (j * CELL_MM) ** 2))
              for i in range(-7, 8) for j in range(-7, 8)
              if (i * CELL_MM) ** 2 + (j * CELL_MM) ** 2 <= TOOL_RADIUS_MM ** 2]
_HOLDER_DISC = _disc(HOLDER_RADIUS_MM)
_BALL_RISE = {(i, j): rise for i, j, rise in _CUT_CELLS}


def _head_points():
    radius = geo.HEAD_RADIUS_MM
    count = int(radius / SAMPLE_MM)
    points = []
    for i in range(-count, count + 1):
        for k in range(-count, count + 1):
            x, z = i * SAMPLE_MM, k * SAMPLE_MM
            if x * x + z * z > radius * radius:
                continue
            y = geo.STOCK_TOP_Y_MM - SAMPLE_MM / 2
            while y > geo.SHOULDER_BOTTOM_Y_MM:
                points.append((x, y, z))
                y -= SAMPLE_MM
    return points


def _cell(value):
    return int(math.floor(value / CELL_MM + 0.5))


def _replay(name, a_deg, b_deg, moves, points):
    matrix = check_gcode.rotation_matrix(a_deg, b_deg)
    origin = geo.WORK_ORIGIN_MM
    top = {}
    tool_points = [check_gcode.apply(matrix, (p[0] - origin[0], p[1] - origin[1], p[2] - origin[2])) for p in points]
    for x, y, z in tool_points:
        key = (_cell(x), _cell(y))
        if z > top.get(key, -math.inf):
            top[key] = z

    worst = {"rapid": 0.0, "shank": 0.0, "holder": 0.0}
    first = {}
    for move_index, (start, end, is_rapid) in enumerate(moves):
        steps = max(1, int(math.dist(start, end) / CELL_MM) + 1)
        for step in range(1, steps + 1):
            f = step / steps
            x, y, z = tuple(start[i] + (end[i] - start[i]) * f for i in range(3))
            cx, cy = _cell(x), _cell(y)
            for i, j in _TOOL_DISC:
                wax = top.get((cx + i, cy + j))
                if wax is None:
                    continue
                ball_surface = z + _BALL_RISE[(i, j)]
                if is_rapid and wax - ball_surface > REPORT_DEPTH_MM:
                    worst["rapid"] = max(worst["rapid"], wax - ball_surface)
                    first.setdefault("rapid", (move_index, round(x, 1), round(y, 1), round(z, 1)))
                if wax - (z + FLUTE_LENGTH_MM) > REPORT_DEPTH_MM:
                    worst["shank"] = max(worst["shank"], wax - z - FLUTE_LENGTH_MM)
                    first.setdefault("shank", (move_index, round(x, 1), round(y, 1), round(z, 1)))
            for i, j, rise in _CUT_CELLS:
                wax = top.get((cx + i, cy + j))
                if wax is not None and wax > z + rise:
                    top[(cx + i, cy + j)] = z + rise
            holder_bottom = z + STICKOUT_MM
            for i, j in _HOLDER_DISC:
                wax = top.get((cx + i, cy + j))
                if wax is not None and wax - holder_bottom > REPORT_DEPTH_MM:
                    worst["holder"] = max(worst["holder"], wax - holder_bottom)
                    first.setdefault("holder", (move_index, round(x, 1), round(y, 1), round(z, 1)))

    remaining = []
    for point, (x, y, z) in zip(points, tool_points):
        wax_top = top.get((_cell(x), _cell(y)))
        if wax_top is None or z <= wax_top + 1e-9:
            remaining.append(point)
    print(f"{name:22s} {a_deg:7.2f} {b_deg:8.2f} | rapid {worst['rapid']:5.2f} | shank {worst['shank']:5.2f} | holder {worst['holder']:5.2f}", flush=True)
    for kind, where in first.items():
        print(f"    first {kind}: move {where[0]} at tool-frame X{where[1]} Y{where[2]} Z{where[3]}", flush=True)
    return bool(first), remaining


def main():
    points = _head_points()
    print(f"{len(points)} stock samples", flush=True)
    contact = 0
    for name, a_deg, b_deg, moves, _, _ in check_gcode.read_operations(sys.argv[1]):
        has_contact, points = _replay(name, a_deg, b_deg, moves, points)
        contact += has_contact
    print(f"\nOperations with contact deeper than {REPORT_DEPTH_MM} mm: {contact}")
    sys.exit(1 if contact else 0)


if __name__ == "__main__":
    main()
