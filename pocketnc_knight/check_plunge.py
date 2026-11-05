"""Reports real plunges: steep descents where the middle of the ball cuts wax.

A ball's center barely cuts, so that's the contact to avoid. Measuring wax removed anywhere under the
ball is misleading: following a steep wall with a 0.15 mm skin at 80 deg shows as 0.9 mm along the tool
axis, though only the ball's side is cutting. Takes several minutes.

Usage: python3 -B check_plunge.py nc/knight.ngc   (exit 1 if a plunge is deeper than the limit)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_gcode
import check_stock_contact as stock
import knight_geometry as geo

STEEPEST_RAMP_DEG = 60.0
BALL_CENTER_RADIUS_MM = 0.6
REPORT_DEPTH_MM = 0.05
MAX_PLUNGE_DEPTH_MM = 0.2
_CENTER_CELLS = {(i, j) for i, j, _ in stock._CUT_CELLS
                 if (i * stock.CELL_MM) ** 2 + (j * stock.CELL_MM) ** 2 <= BALL_CENTER_RADIUS_MM ** 2}


def _is_steep_descent(start, end):
    drop = start[2] - end[2]
    return drop > 0.001 and math.degrees(math.atan2(drop, math.hypot(end[0] - start[0], end[1] - start[1]))) > STEEPEST_RAMP_DEG


def _cut_move(start, end, top):
    """Lower the wax map along one move. Returns the deepest wax the ball's center removed."""
    center_depth = 0.0
    steps = max(1, int(math.dist(start, end) / stock.CELL_MM) + 1)
    for step in range(1, steps + 1):
        fraction = step / steps
        x, y, z = tuple(start[i] + (end[i] - start[i]) * fraction for i in range(3))
        cx, cy = stock._cell(x), stock._cell(y)
        for i, j, rise in stock._CUT_CELLS:
            wax = top.get((cx + i, cy + j))
            if wax is not None and wax > z + rise:
                if (i, j) in _CENTER_CELLS:
                    center_depth = max(center_depth, wax - z - rise)
                top[(cx + i, cy + j)] = z + rise
    return center_depth


def _replay(name, a_deg, b_deg, moves, points):
    """Print this operation's plunges. Returns the deepest, and the stock points still standing."""
    matrix = check_gcode.rotation_matrix(a_deg, b_deg)
    origin = geo.WORK_ORIGIN_MM
    tool_points = [check_gcode.apply(matrix, (p[0] - origin[0], p[1] - origin[1], p[2] - origin[2])) for p in points]
    top = {}
    for x, y, z in tool_points:
        key = (stock._cell(x), stock._cell(y))
        top[key] = max(z, top.get(key, -math.inf))
    plunge_depths = []
    for start, end, _ in moves:
        center_depth = _cut_move(start, end, top)
        if _is_steep_descent(start, end) and center_depth > REPORT_DEPTH_MM:
            plunge_depths.append(center_depth)
    deepest = max(plunge_depths, default=0.0)
    print(f"{name:22s} plunges {len(plunge_depths):4d}   deepest {deepest:.2f} mm", flush=True)
    remaining = [point for point, (x, y, z) in zip(points, tool_points)
                 if z <= top.get((stock._cell(x), stock._cell(y)), math.inf) + 1e-9]
    return deepest, remaining


def main():
    points = stock._head_points()
    deepest_overall = 0.0
    for name, a_deg, b_deg, moves, _, _ in check_gcode.read_operations(sys.argv[1]):
        deepest, points = _replay(name, a_deg, b_deg, moves, points)
        deepest_overall = max(deepest_overall, deepest)
    print(f"\nDeepest plunge: {deepest_overall:.2f} mm, against the {MAX_PLUNGE_DEPTH_MM} mm limit")
    sys.exit(1 if deepest_overall > MAX_PLUNGE_DEPTH_MM else 0)


if __name__ == "__main__":
    main()
