"""How much of the scaled Knight's surface can't a ball of each radius touch, from any direction?

Morphological closing of the voxelized mesh: anything outside the solid that a ball can't sweep is
material a ball that size must leave behind. Ignores tool access and shanks, so real results can only be worse.

Usage: python3 -B check_ball_reach.py ../pocketnc_knight/knight_mesh.json 0.73
"""
import json
import math
import sys
from collections import defaultdict

PITCH_MM = 0.3
BALL_DIAMETERS_IN = (1 / 16, 3 / 32, 1 / 8, 3 / 16, 1 / 4)
MM_PER_IN = 25.4
PAD_MM = 4.5  # Past the largest ball radius, so the grid's edge is always free space for a ball's center.
BAND_MM = 10.0
NOISE_THICKNESS_MM = 1.5 * PITCH_MM  # A curved surface's staircase leaves about one voxel behind.


def load_triangles(path, scale):
    mesh = json.load(open(path))
    nodes = mesh["nodes_mm"]
    points = [tuple(scale * c for c in nodes[3 * i:3 * i + 3]) for i in range(len(nodes) // 3)]
    indices = mesh["tris"]
    return [(points[indices[i]], points[indices[i + 1]], points[indices[i + 2]]) for i in range(0, len(indices), 3)]


def voxelize(triangles):
    lows = [min(p[axis] for tri in triangles for p in tri) - PAD_MM for axis in range(3)]
    highs = [max(p[axis] for tri in triangles for p in tri) + PAD_MM for axis in range(3)]
    nx, ny, nz = (int(math.ceil((highs[a] - lows[a]) / PITCH_MM)) for a in range(3))
    crossings = defaultdict(list)
    for p, q, r in triangles:
        det = (q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1])
        if abs(det) < 1e-12:
            continue
        i_low = int((min(p[0], q[0], r[0]) - lows[0]) / PITCH_MM)
        i_high = int((max(p[0], q[0], r[0]) - lows[0]) / PITCH_MM) + 1
        j_low = int((min(p[1], q[1], r[1]) - lows[1]) / PITCH_MM)
        j_high = int((max(p[1], q[1], r[1]) - lows[1]) / PITCH_MM) + 1
        for i in range(i_low, i_high + 1):
            # The half-pitch shift keeps sample columns off mesh vertices, which would break parity.
            x = lows[0] + (i + 0.5) * PITCH_MM
            for j in range(j_low, j_high + 1):
                y = lows[1] + (j + 0.5) * PITCH_MM
                u = ((x - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (y - p[1])) / det
                v = ((q[0] - p[0]) * (y - p[1]) - (x - p[0]) * (q[1] - p[1])) / det
                if u < 0 or v < 0 or u + v > 1:
                    continue
                crossings[(i, j)].append(p[2] + u * (q[2] - p[2]) + v * (r[2] - p[2]))
    solid = bytearray(nx * ny * nz)
    odd_columns = 0
    for (i, j), heights in crossings.items():
        if not 0 <= i < nx or not 0 <= j < ny:
            continue
        heights.sort()
        odd_columns += len(heights) % 2
        for enter, leave in zip(heights[::2], heights[1::2]):
            k_low = max(0, int(math.ceil((enter - lows[2]) / PITCH_MM - 0.5)))
            k_high = min(nz - 1, int(math.floor((leave - lows[2]) / PITCH_MM - 0.5)))
            base = (i * ny + j) * nz
            for k in range(k_low, k_high + 1):
                solid[base + k] = 1
    print(f"grid {nx}x{ny}x{nz}, solid volume {sum(solid) * PITCH_MM ** 3:.0f} mm3, columns with odd crossings {odd_columns}", flush=True)
    return solid, (nx, ny, nz), lows


def distance_1d(line, n, parabola_at, boundaries, out):
    """Felzenszwalb's squared distance transform along one line, in voxel units."""
    INF = float("inf")
    top = -1
    for q in range(n):
        value = line[q]
        if value == INF:
            continue
        while top >= 0:
            p = parabola_at[top]
            s = (value + q * q - line[p] - p * p) / (2 * (q - p))
            if s > boundaries[top]:
                break
            top -= 1
        top += 1
        parabola_at[top] = q
        boundaries[top] = s if top > 0 else -INF
    if top < 0:
        return False
    boundaries[top + 1] = INF
    segment = 0
    for q in range(n):
        while boundaries[segment + 1] < q:
            segment += 1
        p = parabola_at[segment]
        out[q] = (q - p) ** 2 + line[p]
    return True


def squared_distance_to(seeds, shape):
    """Squared distance from every voxel to the nearest seed, in voxel units."""
    nx, ny, nz = shape
    INF = float("inf")
    grid = [0.0 if seed else INF for seed in seeds]
    for n, step, starts in (
        (nz, 1, [(i * ny + j) * nz for i in range(nx) for j in range(ny)]),
        (ny, nz, [i * ny * nz + k for i in range(nx) for k in range(nz)]),
        (nx, ny * nz, [j * nz + k for j in range(ny) for k in range(nz)]),
    ):
        parabola_at, boundaries, out = [0] * n, [0.0] * (n + 1), [0.0] * n
        stop_offset = n * step
        for start in starts:
            line = grid[start:start + stop_offset:step]
            if distance_1d(line, n, parabola_at, boundaries, out):
                grid[start:start + stop_offset:step] = out
    return grid


def report_ball(radius_mm, solid, to_solid, shape, lows):
    radius_voxels_sq = (radius_mm / PITCH_MM) ** 2
    free_centers = bytearray(1 if d > radius_voxels_sq else 0 for d in to_solid)
    to_center = squared_distance_to(free_centers, shape)
    nz = shape[2]
    left = 0
    thickest_mm = 0.0
    by_band = defaultdict(int)
    for index, is_solid in enumerate(solid):
        if is_solid or to_center[index] <= radius_voxels_sq:
            continue
        thickness_mm = math.sqrt(to_solid[index]) * PITCH_MM
        if thickness_mm < NOISE_THICKNESS_MM:
            continue
        left += 1
        thickest_mm = max(thickest_mm, thickness_mm)
        height_mm = (index % nz + 0.5) * PITCH_MM + lows[2] + PAD_MM
        by_band[int(height_mm // BAND_MM) * int(BAND_MM)] += 1
    voxel_mm3 = PITCH_MM ** 3
    bands = ", ".join(f"{band}-{band + int(BAND_MM)}mm: {count * voxel_mm3:.1f}" for band, count in sorted(by_band.items()))
    print(f"ball dia {2 * radius_mm:.3f} mm ({2 * radius_mm / MM_PER_IN:.4f} in): left behind {left * voxel_mm3:.1f} mm3, thickest {thickest_mm:.2f} mm | mm3 by height above base: {bands}", flush=True)


def main():
    triangles = load_triangles(sys.argv[1], float(sys.argv[2]))
    solid, shape, lows = voxelize(triangles)
    to_solid = squared_distance_to(solid, shape)
    print("distance field done", flush=True)
    for diameter_in in BALL_DIAMETERS_IN:
        report_ball(diameter_in * MM_PER_IN / 2, solid, to_solid, shape, lows)


if __name__ == "__main__":
    main()
