"""Replay posted lathe moves with each insert's nose circle, to find the stock each pass really leaves.

Nose center offsets from the programmed point were checked by hand against the top cone: T6 (right hand, R0.8)
is at (r+R, z+R), and T7 (neutral, R0.4) at (r+R, z). Arcs use I and K as radial and axial offsets to the center.
Tool bodies aren't modelled. Reads an inch lathe post.

Usage: python3 -B check_lathe_nose.py nc/knight_lathe.nc
"""
import re
import sys
import math

STOCK_TOP_Z_MM = 60.917
BAR_RADIUS_MM = 15.875
Z_LOW_MM, Z_HIGH_MM, STEP_MM = -6.0, 61.0, 0.02
TOOLS = {6: ('nose', 0.8, 0.8), 7: ('nose', 0.4, 0.0), 8: ('groove', 3.0, 0.0)}
OPS = ('Face top', 'Rough profile', 'Rough waist', 'Rough neck groove', 'Finish profile', 'Groove neck')


def index_of(z_mm):
    return int(round((z_mm - Z_LOW_MM) / STEP_MM))


def z_of(i):
    return Z_LOW_MM + i * STEP_MM


def cut(radius, tool, r_tip, z_tip):
    kind, size, z_offset = tool
    if kind == 'groove':
        for i in range(max(index_of(z_tip), 0), min(index_of(z_tip + size), len(radius) - 1) + 1):
            radius[i] = min(radius[i], max(r_tip, 0))
        return
    r_center, z_center = r_tip + size, z_tip + z_offset
    for i in range(max(index_of(z_center - size), 0), min(index_of(z_center + size), len(radius) - 1) + 1):
        half = math.sqrt(max(size ** 2 - (z_of(i) - z_center) ** 2, 0))
        radius[i] = min(radius[i], max(r_center - half, 0))


def move_points(start, end, motion, words):
    if motion == 1:
        samples = max(2, int(math.hypot(end[0] - start[0], end[1] - start[1]) / 0.01))
        return [(start[0] + (end[0] - start[0]) * n / samples, start[1] + (end[1] - start[1]) * n / samples) for n in range(samples + 1)]
    r_center = start[0] + float(words.get('I', 0)) * 25.4
    z_center = start[1] + float(words.get('K', 0)) * 25.4
    arc_radius = math.hypot(start[0] - r_center, start[1] - z_center)
    end_error = abs(math.hypot(end[0] - r_center, end[1] - z_center) - arc_radius)
    assert end_error < 0.01, f'arc center is inconsistent by {end_error} mm'
    # With Z to the right and X up, G3 turns counterclockwise, as checked on a finish arc that bulges outward.
    angle_start = math.atan2(start[0] - r_center, start[1] - z_center)
    angle_end = math.atan2(end[0] - r_center, end[1] - z_center)
    sweep = angle_end - angle_start
    if motion == 3 and sweep < 0:
        sweep += 2 * math.pi
    if motion == 2 and sweep > 0:
        sweep -= 2 * math.pi
    samples = max(2, int(abs(sweep) * arc_radius / 0.01))
    return [(r_center + arc_radius * math.sin(angle_start + sweep * n / samples), z_center + arc_radius * math.cos(angle_start + sweep * n / samples)) for n in range(samples + 1)]


def main():
    radius = [BAR_RADIUS_MM] * (index_of(Z_HIGH_MM) + 1)
    snapshots = {}
    x = z = None
    motion = 0
    op = tool = None
    for line in open(sys.argv[1]):
        stripped = line.strip()
        if stripped.startswith('(') and stripped.strip('()') in OPS:
            if op:
                snapshots[op] = list(radius)
            op = stripped.strip('()')
            continue
        if op is None or 'G53' in line:
            continue
        code = re.sub(r'\([^)]*\)', '', line)
        selected = re.match(r'T(\d)\d\d', code)
        if selected:
            tool = TOOLS[int(selected.group(1))]
        for g in re.findall(r'G(\d+)', code):
            if int(g) in (0, 1, 2, 3):
                motion = int(g)
        words = dict(re.findall(r'([XZIK])(-?\d*\.?\d+)', code))
        previous = (x, z)
        x = float(words['X']) * 25.4 / 2 if 'X' in words else x
        z = float(words['Z']) * 25.4 + STOCK_TOP_Z_MM if 'Z' in words else z
        if None in previous or None in (x, z) or previous == (x, z) or motion == 0:
            continue
        for r_tip, z_tip in move_points(previous, (x, z), motion, words):
            cut(radius, tool, r_tip, z_tip)
    snapshots[op] = list(radius)
    finished = snapshots['Finish profile']
    print('    z | after Rough profile | after Rough waist | after Finish | finish takes (radial)')
    for z_mm in [0.5, 1, 2, 3, 3.5, 4, 5, 5.5, 6, 6.5, 7, 7.5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 18.5, 19, 20, 21, 22, 30, 45, 50, 55, 60]:
        i = index_of(z_mm)
        print(f"{z_mm:5.1f} | {snapshots['Rough profile'][i]:19.3f} | {snapshots['Rough waist'][i]:17.3f} | {finished[i]:12.3f} | {snapshots['Rough waist'][i] - finished[i]:6.3f}")
    takes = [(snapshots['Rough neck groove'][i] - finished[i], z_of(i)) for i in range(index_of(0.1), index_of(60.9))]
    print('largest radial take by Finish profile:', max(takes))
    print('neck after Rough neck groove / Groove neck:', [(z_mm, round(snapshots['Rough neck groove'][index_of(z_mm)], 3), round(snapshots['Groove neck'][index_of(z_mm)], 3)) for z_mm in (-4.95, -4.5, -3, -1, -0.05)])


if __name__ == "__main__":
    main()
