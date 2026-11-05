"""Reports the wax a program leaves outside the Knight, so an area no tool reached shows up.

The other checks only look for contact, so they pass when a pocket is simply never cut. This replays
each operation against the shrinking stock, then measures what stands outside the Knight's mesh, by
height up the part. Bands of about 25 mm3 are normal: they are the thin skin along the base's edges and
what the ball can't reach in the mane's grooves. Look at any band that grows. Takes several minutes.

Usage: python3 -B check_leftover.py nc/knight.ngc
"""
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_gcode
import check_stock_contact as stock
import knight_geometry as geo

CELL_MM = stock.CELL_MM
BAND_MM = 5.0


def _surface_heights_by_column():
    """For each XZ column, the sorted heights where the Knight's surface crosses it."""
    heights = defaultdict(list)
    for p, q, r in check_gcode.knight_triangles():
        det = (q[0] - p[0]) * (r[2] - p[2]) - (r[0] - p[0]) * (q[2] - p[2])
        if abs(det) < 1e-12:
            continue
        for i in range(int(math.floor(min(p[0], q[0], r[0]) / CELL_MM)), int(math.ceil(max(p[0], q[0], r[0]) / CELL_MM)) + 1):
            for k in range(int(math.floor(min(p[2], q[2], r[2]) / CELL_MM)), int(math.ceil(max(p[2], q[2], r[2]) / CELL_MM)) + 1):
                # The small shift keeps a column from landing exactly on a shared triangle edge.
                x, z = i * CELL_MM + 1e-5, k * CELL_MM + 1e-5
                u = ((x - p[0]) * (r[2] - p[2]) - (r[0] - p[0]) * (z - p[2])) / det
                v = ((q[0] - p[0]) * (z - p[2]) - (x - p[0]) * (q[2] - p[2])) / det
                if u >= 0 and v >= 0 and u + v <= 1:
                    heights[(i, k)].append(p[1] + u * (q[1] - p[1]) + v * (r[1] - p[1]))
    return heights


def _is_inside_knight(point, heights_by_column):
    column = heights_by_column.get((stock._cell(point[0]), stock._cell(point[2])), ())
    return sum(1 for height in column if height > point[1]) % 2 == 1


def _cut_operation(a_deg, b_deg, moves, points):
    """Return the stock points still standing after one operation's moves."""
    matrix = check_gcode.rotation_matrix(a_deg, b_deg)
    origin = geo.WORK_ORIGIN_MM
    tool_points = [check_gcode.apply(matrix, (p[0] - origin[0], p[1] - origin[1], p[2] - origin[2])) for p in points]
    top = {}
    for x, y, z in tool_points:
        key = (stock._cell(x), stock._cell(y))
        top[key] = max(z, top.get(key, -math.inf))
    for start, end, _ in moves:
        steps = max(1, int(math.dist(start, end) / CELL_MM) + 1)
        for step in range(1, steps + 1):
            fraction = step / steps
            x, y, z = tuple(start[i] + (end[i] - start[i]) * fraction for i in range(3))
            cx, cy = stock._cell(x), stock._cell(y)
            for i, j, rise in stock._CUT_CELLS:
                wax = top.get((cx + i, cy + j))
                if wax is not None and wax > z + rise:
                    top[(cx + i, cy + j)] = z + rise
    return [point for point, (x, y, z) in zip(points, tool_points)
            if z <= top.get((stock._cell(x), stock._cell(y)), math.inf) + 1e-9]


def main():
    heights_by_column = _surface_heights_by_column()
    mm3_per_point = CELL_MM ** 3
    points = stock._head_points()
    leftover = []
    for name, a_deg, b_deg, moves, _, _ in check_gcode.read_operations(sys.argv[1]):
        points = _cut_operation(a_deg, b_deg, moves, points)
        leftover = [p for p in points if p[1] >= geo.KNIGHT_BASE_Y_MM and not _is_inside_knight(p, heights_by_column)]
        print(f"{name:22s} {len(leftover) * mm3_per_point:9.0f} mm3 outside the Knight", flush=True)
    bands = Counter(int(p[1] // BAND_MM) * BAND_MM for p in leftover)
    print("\nLeft after the last operation, by height:")
    for band_low_mm, count in sorted(bands.items()):
        print(f"  Y {band_low_mm:4.0f} to {band_low_mm + BAND_MM:4.0f}: {count * mm3_per_point:6.1f} mm3")


if __name__ == "__main__":
    main()
