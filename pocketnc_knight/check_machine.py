"""Clearance from the tool, holder and spindle to Penta's real machine model, from posted G-code.

Works in the Y carriage frame, where the tool axis is +Z, with the A and B bodies rotated into that
frame per operation. On an earlier part it reproduced the exact point where Fusion's machine
simulation stopped, to within 0.06 mm. It samples about 45 positions per operation including the
extremes, skips the Static, X and Z bodies, and depends on the estimated holder size.

Usage: python3 -B check_machine.py nc/knight.ngc   (exit 1 if anything touches)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import check_gcode

B_AXIS_X = check_gcode.B_AXIS_X_MM
SHANK_R = 3.175 / 2


def tool_profile(stickout):
    """(from_mm, to_mm, radius_mm, name) measured up the axis from the tip."""
    return [(0.0, stickout, SHANK_R, 'shank'),
            (stickout, stickout + 12.0, 8.0, 'holder lower'),
            (stickout + 12.0, stickout + 76.0, 9.5, 'holder upper'),
            (stickout + 76.0, stickout + 76.0 + 45.1, 15.0, 'spindle')]


def rx(deg, p):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0], c * p[1] - s * p[2], s * p[1] + c * p[2])


def ry(deg, p):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (c * p[0] + s * p[2], p[1], -s * p[0] + c * p[2])


def on_b(deg, p):
    x, y, z = ry(deg, (p[0] - B_AXIS_X, p[1], p[2]))
    return (x + B_AXIS_X, y, z)


def load(path, key):
    data = json.load(open(path))[key]
    n, idx = data['nodes'], data['indices']
    nodes = [(n[i], n[i + 1], n[i + 2]) for i in range(0, len(n), 3)]
    return [(nodes[idx[i]], nodes[idx[i + 1]], nodes[idx[i + 2]]) for i in range(0, len(idx), 3)]


def closest_distance(p, tri):
    a, b, c = tri
    ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2]); ac = (c[0]-a[0], c[1]-a[1], c[2]-a[2]); ap = (p[0]-a[0], p[1]-a[1], p[2]-a[2])
    d1 = ab[0]*ap[0]+ab[1]*ap[1]+ab[2]*ap[2]; d2 = ac[0]*ap[0]+ac[1]*ap[1]+ac[2]*ap[2]
    if d1 <= 0 and d2 <= 0: return math.sqrt(ap[0]**2+ap[1]**2+ap[2]**2)
    bp = (p[0]-b[0], p[1]-b[1], p[2]-b[2])
    d3 = ab[0]*bp[0]+ab[1]*bp[1]+ab[2]*bp[2]; d4 = ac[0]*bp[0]+ac[1]*bp[1]+ac[2]*bp[2]
    if d3 >= 0 and d4 <= d3: return math.sqrt(bp[0]**2+bp[1]**2+bp[2]**2)
    vc = d1*d4 - d3*d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1/(d1-d3); q = (a[0]+v*ab[0]-p[0], a[1]+v*ab[1]-p[1], a[2]+v*ab[2]-p[2])
        return math.sqrt(q[0]**2+q[1]**2+q[2]**2)
    cp = (p[0]-c[0], p[1]-c[1], p[2]-c[2])
    d5 = ab[0]*cp[0]+ab[1]*cp[1]+ab[2]*cp[2]; d6 = ac[0]*cp[0]+ac[1]*cp[1]+ac[2]*cp[2]
    if d6 >= 0 and d5 <= d6: return math.sqrt(cp[0]**2+cp[1]**2+cp[2]**2)
    vb = d5*d2 - d1*d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2/(d2-d6); q = (a[0]+w*ac[0]-p[0], a[1]+w*ac[1]-p[1], a[2]+w*ac[2]-p[2])
        return math.sqrt(q[0]**2+q[1]**2+q[2]**2)
    va = d3*d6 - d5*d4
    if va <= 0 and d4-d3 >= 0 and d5-d6 >= 0:
        w = (d4-d3)/((d4-d3)+(d5-d6))
        q = (b[0]+w*(c[0]-b[0])-p[0], b[1]+w*(c[1]-b[1])-p[1], b[2]+w*(c[2]-b[2])-p[2])
        return math.sqrt(q[0]**2+q[1]**2+q[2]**2)
    denom = 1.0/(va+vb+vc); v = vb*denom; w = vc*denom
    q = (a[0]+ab[0]*v+ac[0]*w-p[0], a[1]+ab[1]*v+ac[1]*w-p[1], a[2]+ab[2]*v+ac[2]*w-p[2])
    return math.sqrt(q[0]**2+q[1]**2+q[2]**2)


def axis_crossings(x, y, triangles):
    """Z values where the vertical line through (x, y) crosses the mesh, for an inside test."""
    z_values = []
    for a, b, c in triangles:
        d = (b[0]-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(b[1]-a[1])
        if abs(d) < 1e-12: continue
        u = ((x-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(y-a[1])) / d
        v = ((b[0]-a[0])*(y-a[1]) - (x-a[0])*(b[1]-a[1])) / d
        if u >= 0 and v >= 0 and u+v <= 1:
            z_values.append(a[2] + u*(b[2]-a[2]) + v*(c[2]-a[2]))
    return z_values


def prepared(triangles):
    return [(t, min(p[0] for p in t), max(p[0] for p in t), min(p[1] for p in t), max(p[1] for p in t), max(p[2] for p in t)) for t in triangles]


def tool_gap(tip, bodies, profile, search_mm=26.0):
    """Smallest gap over bodies, as (gap, body name, tool section, station mm)."""
    best = (math.inf, '', '', 0.0)
    x, y, z = tip
    for name, tris in bodies:
        near = [e[0] for e in tris if e[1]-search_mm <= x <= e[2]+search_mm and e[3]-search_mm <= y <= e[4]+search_mm and e[5] >= z]
        if not near: continue
        crossings = axis_crossings(x, y, near)
        for start, end, radius, section in profile:
            s = start
            while s <= end + 1e-9:
                point = (x, y, z + s)
                inside = sum(1 for c in crossings if c > z + s) % 2 == 1
                distance = min(closest_distance(point, t) for t in near)
                gap = -(distance + radius) if inside else distance - radius
                if gap < best[0]: best = (gap, name, section, s)
                s += 2.0
    return best


def representative(tips, count=45):
    """Extremes in many directions plus an even spread, since the tool's reach is set by extremes."""
    picks = set(range(0, len(tips), max(1, len(tips) // count)))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx or dy or dz:
                    picks.add(max(range(len(tips)), key=lambda i: dx*tips[i][0]+dy*tips[i][1]+dz*tips[i][2]))
    return [tips[i] for i in sorted(picks)]


def main():
    profile = tool_profile(check_gcode.STICKOUT_MM)
    mesh_path = os.path.join(HERE, "machine_mesh.json")
    a_body = load(mesh_path, "A Axis:1/a_axis_table")
    b_body = load(mesh_path, "B Axis:1/b_axis_table")
    y_body = load(mesh_path, "Y Axis:1/y_axis_table")
    touching = 0
    print(f"{'operation':22s} {'A':>7s} {'B':>8s}  gap mm  body    section")
    for name, a_deg, b_deg, moves, _, _ in check_gcode.read_operations(sys.argv[1]):
        matrix = check_gcode.rotation_matrix(a_deg, b_deg)
        tips = [check_gcode.part_to_carriage(matrix, check_gcode.tool_frame_to_part(matrix, end)) for _, end, _ in moves]
        bodies = [("A body", prepared([tuple(rx(a_deg, p) for p in t) for t in a_body])),
                  ("B body", prepared([tuple(rx(a_deg, on_b(b_deg, p)) for p in t) for t in b_body])),
                  ("Y body", prepared(y_body))]
        worst = min((tool_gap(t, bodies, profile) for t in representative(tips)), key=lambda r: r[0])
        touching += worst[0] < 0
        print(f"{name:22s} {a_deg:7.2f} {b_deg:8.2f} {worst[0]:7.2f}  {worst[1]:7s} {worst[2]}", flush=True)
    print(f"\nOperations touching the machine: {touching}")
    sys.exit(1 if touching else 0)


if __name__ == "__main__":
    main()
