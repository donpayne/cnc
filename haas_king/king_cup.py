"""Contact rings for the cup and the finial's underside, cut by turning C at a fixed B45.

Plain Python, so Fusion's interpreter can import it too. Lengths are mm in the 73% model's frame, as (r, z): r from
the part axis, z up from the base.

Each ring is a circle on a revolved surface, and Fusion's Multi-Axis Contour, in 4-axis mode with the tool tilted a
fixed angle to the rotary axis, puts the ball in contact with it there. A stock to leave pushes the ball out along the
surface normal, which is how the roughing layers are made. Because the surfaces are revolved, a ball whose meridian
section clears the profile clears the solid, so every check here is 2D.
"""
import math
from typing import List, NamedTuple, Tuple

Point = Tuple[float, float]

# B45 reaches the whole profile: the cup cone faces up and in, the finial cone out and down, so every contact lies
# between 67 deg and 70 deg off the ball's tip, and the line along the tool clears the rim and the finial's head.
TILT_DEG = 45.0
TOOL_AXIS = (math.sin(math.radians(TILT_DEG)), math.cos(math.radians(TILT_DEG)))

# Exact surfaces, read from the King body's faces in Fusion.
CUP_CONE_ORIGIN = (8.017220, 77.564990)
CUP_CONE_HALF_ANGLE_DEG = 68.114197
FLOOR_CENTER = (2.883281, 76.751521)
FLOOR_RADIUS = 1.158875
FINIAL_CONE_ORIGIN = (3.390088, 80.577711)
FINIAL_CONE_HALF_ANGLE_DEG = 25.018373
HEAD_CONE_ORIGIN = (3.207683, 85.028700)  # Widens downward to the head's edge
HEAD_CONE_HALF_ANGLE_DEG = 57.340704
BEAD_CENTER = (15.571 * 0.73, 107.69 * 0.73)
BEAD_RADIUS = 0.381 * 0.73
CORNER_CONE_ORIGIN = (8.832474, 71.206513)  # The crown's revolved corner cone, below the bead
CORNER_CONE_HALF_ANGLE_DEG = 20.933826
# The lathe turns the bead over its top. The mill takes its inner side, from the top down to the cup cone.
BEAD_TOP = (BEAD_CENTER[0], BEAD_CENTER[1] + BEAD_RADIUS)
# What the lathe leaves above the cup: a floor at z 79.1 out to the bead, and under the head a staircase of T8 plunges,
# as (radius, top z) from the bottom step up. Each radius is the finial cone's at the step's top, plus 0.02.
LATHE_FLOOR_Z = 79.1
LATHE_STEPS = ((4.1205, 82.1), (4.4706, 82.85), (4.9373, 83.914))


class Ring(NamedTuple):
    contact: Point
    center: Point  # Ball center, at this pass's stock to leave


class Layer(NamedTuple):
    stock_to_leave_mm: float
    rings: List[Ring]


def _unit(vector):
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _line_direction(half_angle_deg):
    """Up the cone's generator, in (r, z)."""
    half = math.radians(half_angle_deg)
    return (math.sin(half), math.cos(half))


CUP_DIRECTION = _line_direction(CUP_CONE_HALF_ANGLE_DEG)  # Outward and up
CUP_NORMAL = (-CUP_DIRECTION[1], CUP_DIRECTION[0])  # Into the air: up and in
FINIAL_DIRECTION = _line_direction(FINIAL_CONE_HALF_ANGLE_DEG)
FINIAL_NORMAL = (FINIAL_DIRECTION[1], -FINIAL_DIRECTION[0])  # Into the air: out and down

FLOOR_OUTER = (FLOOR_CENTER[0] - FLOOR_RADIUS * CUP_NORMAL[0], FLOOR_CENTER[1] - FLOOR_RADIUS * CUP_NORMAL[1])
NECK = (FLOOR_CENTER[0] - FLOOR_RADIUS * FINIAL_NORMAL[0], FLOOR_CENTER[1] - FLOOR_RADIUS * FINIAL_NORMAL[1])
CUP_RIM = (BEAD_CENTER[0] + BEAD_RADIUS * CUP_NORMAL[0], BEAD_CENTER[1] + BEAD_RADIUS * CUP_NORMAL[1])


def _head_edge():
    """Where the finial's cone meets the head's underside cone."""
    head_slope = math.tan(math.radians(HEAD_CONE_HALF_ANGLE_DEG))  # r gained per mm of z downward
    finial_slope = math.tan(math.radians(FINIAL_CONE_HALF_ANGLE_DEG))
    # finial: r = r0 + s (z - z0); head: r = h0 + k (zh - z)
    z = (HEAD_CONE_ORIGIN[0] + head_slope * HEAD_CONE_ORIGIN[1] - FINIAL_CONE_ORIGIN[0] + finial_slope * FINIAL_CONE_ORIGIN[1]) / (
        finial_slope + head_slope
    )
    return (FINIAL_CONE_ORIGIN[0] + finial_slope * (z - FINIAL_CONE_ORIGIN[1]), z)


HEAD_EDGE = _head_edge()


def _sample_profile(step_mm=0.01):
    """Mill-owned profile from the bead's top to the head's edge, as (point, air normal) pairs."""
    samples = []
    start = math.pi / 2
    end = math.atan2(CUP_NORMAL[1], CUP_NORMAL[0])
    count = max(2, int(BEAD_RADIUS * (end - start) / step_mm))
    for i in range(count):
        angle = start + (end - start) * i / count
        normal = (math.cos(angle), math.sin(angle))
        samples.append(((BEAD_CENTER[0] + BEAD_RADIUS * normal[0], BEAD_CENTER[1] + BEAD_RADIUS * normal[1]), normal))
    cup_length = math.hypot(CUP_RIM[0] - FLOOR_OUTER[0], CUP_RIM[1] - FLOOR_OUTER[1])
    count = int(cup_length / step_mm)
    for i in range(count):
        t = cup_length * (1 - i / count)
        samples.append(((FLOOR_OUTER[0] + t * CUP_DIRECTION[0], FLOOR_OUTER[1] + t * CUP_DIRECTION[1]), CUP_NORMAL))
    start = math.atan2(-CUP_NORMAL[1], -CUP_NORMAL[0])
    end = math.atan2(-FINIAL_NORMAL[1], -FINIAL_NORMAL[0])
    # The floor runs clockwise round its center, under it from the cup cone to the neck.
    if end > start:
        end -= 2 * math.pi
    count = max(2, int(FLOOR_RADIUS * abs(end - start) / step_mm))
    for i in range(count):
        angle = start + (end - start) * i / count
        outward = (math.cos(angle), math.sin(angle))
        point = (FLOOR_CENTER[0] + FLOOR_RADIUS * outward[0], FLOOR_CENTER[1] + FLOOR_RADIUS * outward[1])
        samples.append((point, (-outward[0], -outward[1])))
    finial_length = math.hypot(HEAD_EDGE[0] - NECK[0], HEAD_EDGE[1] - NECK[1])
    count = int(finial_length / step_mm)
    for i in range(count + 1):
        t = finial_length * i / count
        samples.append(((NECK[0] + t * FINIAL_DIRECTION[0], NECK[1] + t * FINIAL_DIRECTION[1]), FINIAL_NORMAL))
    return samples


def _part_outline(step_mm=0.01):
    """Points on every finished surface near the cup, for clearance checks."""
    points = [point for point, _ in _sample_profile(step_mm)]
    for i in range(int(2 * math.pi * BEAD_RADIUS / step_mm)):
        angle = 2 * math.pi * i * step_mm / (2 * math.pi * BEAD_RADIUS)
        points.append((BEAD_CENTER[0] + BEAD_RADIUS * math.cos(angle), BEAD_CENTER[1] + BEAD_RADIUS * math.sin(angle)))
    head_direction = _unit((HEAD_CONE_ORIGIN[0] - HEAD_EDGE[0], HEAD_CONE_ORIGIN[1] - HEAD_EDGE[1]))
    for i in range(int(3.0 / step_mm)):
        points.append((HEAD_EDGE[0] + i * step_mm * head_direction[0], HEAD_EDGE[1] + i * step_mm * head_direction[1]))
    corner = _line_direction(CORNER_CONE_HALF_ANGLE_DEG)
    for i in range(int(9.0 / step_mm)):
        z = 70.0 + i * step_mm * corner[1]
        points.append((CORNER_CONE_ORIGIN[0] + corner[0] / corner[1] * (z - CORNER_CONE_ORIGIN[1]), z))
    return points


_OUTLINE = None


def clearance_mm(center):
    """Distance from a ball center to the nearest finished surface."""
    global _OUTLINE
    if _OUTLINE is None:
        _OUTLINE = _part_outline()
    return min(math.hypot(center[0] - p[0], center[1] - p[1]) for p in _OUTLINE)


def _rings_along(samples, offset_mm, spacing_mm):
    """Rings whose ball centers sit spacing_mm apart along the offset path, keeping only gouge-free ones."""
    rings = []
    previous_center = None
    travelled = spacing_mm
    for contact, normal in samples:
        center = (contact[0] + offset_mm * normal[0], contact[1] + offset_mm * normal[1])
        if previous_center is not None:
            travelled += math.hypot(center[0] - previous_center[0], center[1] - previous_center[1])
        previous_center = center
        if travelled < spacing_mm or _dot(normal, TOOL_AXIS) < 0:
            continue
        if clearance_mm(center) < offset_mm - 1e-4:
            continue
        rings.append(Ring(contact, center))
        travelled = 0.0
    return rings


def finish_rings(ball_radius_mm, spacing_mm, samples=None):
    return _rings_along(samples or _sample_profile(), ball_radius_mm, spacing_mm)


def split_finish(large_radius_mm, large_spacing_mm, small_radius_mm, small_spacing_mm):
    """The large ball finishes everything it can reach. The small one takes the stretch between, with no overlap."""
    samples = _sample_profile()
    large = _rings_along(samples, large_radius_mm, large_spacing_mm)
    gap = max(
        (b for b in zip(large, large[1:])),
        key=lambda pair: math.hypot(pair[0].contact[0] - pair[1].contact[0], pair[0].contact[1] - pair[1].contact[1]),
    )
    contacts = [contact for contact, _ in samples]
    first = contacts.index(gap[0].contact)
    last = contacts.index(gap[1].contact)
    small = _rings_along(samples[first + 1 : last], small_radius_mm, small_spacing_mm)
    return large, small


def _inside_stock(point):
    """Whether a point lies in what the lathe leaves above the finished cup. Points inside the part count too, so
    callers pair this with a clearance check."""
    r, z = point
    if z <= LATHE_FLOOR_Z:
        return r <= BEAD_TOP[0]
    for step_r, step_top_z in LATHE_STEPS:
        if z <= step_top_z:
            return r <= step_r
    return False


ROUGH_CUP_STOCK_MM = 0.25
# Rough Cup's boundary keeps its center inside this. Its model is the real King, and past this Adaptive went down the
# notches from above, over half its path; the notch passes cut those. The cup cone's offset already holds the ball's
# tip above z 78.96 here, so it gives up almost nothing in the cup.
ROUGH_CUP_MAX_CENTER_R_MM = 10.5


def _rough_cup_center_gap_mm(point, ball_radius_mm=3.175 / 2):
    """How far a point is from where Rough Cup (Adaptive at B0) can put its ball's center, less the ball's radius.

    Coming straight down, the ball stays out of the head's shadow, so its center keeps to r >= the head's edge plus
    the ball and the stock, and the boundary keeps it to r <= ROUGH_CUP_MAX_CENTER_R_MM. Between those it can go down
    to the cup cone's offset. 0 or less means the ball reached it.
    """
    offset = ball_radius_mm + ROUGH_CUP_STOCK_MM
    min_r, max_r = HEAD_EDGE[0] + offset, ROUGH_CUP_MAX_CENTER_R_MM
    # The cup cone's offset line, z = z0 + (r - r0) * slope, with the center's z at least this.
    slope = CUP_DIRECTION[1] / CUP_DIRECTION[0]
    lift = offset / CUP_DIRECTION[0]  # Vertical lift of a line moved offset along its normal

    def offset_z(r):
        return CUP_CONE_ORIGIN[1] + (r - CUP_CONE_ORIGIN[0]) * slope + lift

    r, z = point
    if min_r <= r <= max_r and z >= offset_z(r):
        return -ball_radius_mm
    # The reachable centers are bounded by two vertical rays and the offset line between them.
    candidates = [(edge_r, max(z, offset_z(edge_r))) for edge_r in (min_r, max_r)]
    segment_length = (max_r - min_r) / CUP_DIRECTION[0]
    t = (r - min_r) * CUP_DIRECTION[0] + (z - offset_z(min_r)) * CUP_DIRECTION[1]
    t = min(max(t, 0.0), segment_length)
    candidates.append((min_r + t * CUP_DIRECTION[0], offset_z(min_r) + t * CUP_DIRECTION[1]))
    return min(math.hypot(r - cr, z - cz) for cr, cz in candidates) - ball_radius_mm


def rough_cup_left_it(point):
    """Stock that Rough Cup can't reach, which the B45 rings under the head have to clear."""
    # The margin skips rings that would only skim Adaptive's 0.25 mm and its cusps, which Semi Cup takes.
    return _inside_stock(point) and _rough_cup_center_gap_mm(point) > 0.05


# Fusion offsets the whole model by a pass's stock, and the floor's concave fillet (r 1.159) has no offset past its
# radius, so the thickest layer stays under it.
MAX_ROUGH_STOCK_MM = 1.0


def _disk_points(center, radius_mm, rings=4, per_ring=16):
    points = [center]
    for i in range(1, rings + 1):
        rho = radius_mm * i / rings
        for j in range(per_ring):
            angle = 2 * math.pi * j / per_ring
            points.append((center[0] + rho * math.cos(angle), center[1] + rho * math.sin(angle)))
    return points


def rough_layers(
    ball_radius_mm, finish_stock_mm, layer_mm, spacing_mm, region=_inside_stock, samples=None, max_stock_mm=MAX_ROUGH_STOCK_MM
):
    """Layers from the outside in, down to finish_stock_mm, each keeping only rings whose ball reaches uncut stock."""
    samples = samples or _sample_profile()
    layers = []
    stock = finish_stock_mm
    # Thick spots can need a layer even where a thinner one above them found nothing, so this runs to a fixed depth.
    while stock <= max_stock_mm:
        rings = []
        for ring in _rings_along(samples, ball_radius_mm + stock, spacing_mm):
            # Every point of this ball is at least `stock` from the part, so a ball that reaches uncut stock anywhere
            # is needed at this layer. Near the cup's valley that's often away from the ball's innermost point.
            if any(region(point) for point in _disk_points(ring.center, ball_radius_mm)):
                rings.append(ring)
        if rings:
            layers.append(Layer(stock, rings))
        stock += layer_mm
    return list(reversed(layers))


T4_RADIUS_MM = 3.175 / 2
T14_RADIUS_MM = 1.0
SEMI_STOCK_MM = 0.08
ROUGH_STOCK_MM = 0.25
# A 2D replay of the plan (Adaptive approximated) gave the largest bite under the head as 0.9 mm2 of section and the
# mean as 0.2 at these. 0.4 and 0.6 gave 1.8 at the largest.
UNDER_HEAD_LAYER_MM = 0.25
UNDER_HEAD_SPACING_MM = 0.3
# Fusion gave an empty toolpath for T14's 0.58 layer: its two rings wedge the ball between the cup and finial cones.
# Without it the 0.33 layer's largest bite stays 0.54 mm2 of section in the 2D replay.
FLOOR_MAX_STOCK_MM = 0.5


def plan_passes():
    """Every ring pass, in program order, as (name, tool number, stock to leave, rings)."""
    samples = _sample_profile()
    finish_t4, finish_t14 = split_finish(T4_RADIUS_MM, 0.25, T14_RADIUS_MM, 0.12)
    semi_t4 = _rings_along(samples, T4_RADIUS_MM + SEMI_STOCK_MM, 0.5)
    passes = []
    rough_t4 = []
    for layer in rough_layers(T4_RADIUS_MM, ROUGH_STOCK_MM, UNDER_HEAD_LAYER_MM, UNDER_HEAD_SPACING_MM, region=rough_cup_left_it, samples=samples):
        # From the head's edge down, so each ring under the head finds the stock above it already gone.
        passes.append((f"Rough Under Head {layer.stock_to_leave_mm:.2f}", 4, layer.stock_to_leave_mm, layer.rings[::-1]))
        rough_t4.extend(layer.rings)

    def t4_left_it(point):
        """Stock no T4 pass so far reached, in the cup's valley, where T14 roughs before Semi Cup slides in deeper."""
        if not rough_cup_left_it(point) or clearance_mm(point) <= SEMI_STOCK_MM:
            return False
        return all(math.hypot(point[0] - ring.center[0], point[1] - ring.center[1]) > T4_RADIUS_MM for ring in rough_t4)

    first = samples.index(next(s for s in samples if s[0] == finish_t14[0].contact))
    last = samples.index(next(s for s in samples if s[0] == finish_t14[-1].contact))
    valley_samples = samples[max(0, first - 60) : last + 60]
    floor_layers = rough_layers(
        T14_RADIUS_MM, SEMI_STOCK_MM, 0.25, 0.3, region=t4_left_it, samples=valley_samples, max_stock_mm=FLOOR_MAX_STOCK_MM
    )
    for layer in floor_layers:
        passes.append((f"Rough Floor {layer.stock_to_leave_mm:.2f}", 14, layer.stock_to_leave_mm, layer.rings))
    passes.append(("Semi Cup", 4, SEMI_STOCK_MM, semi_t4))
    passes.append(("Finish Cup", 4, 0.0, finish_t4))
    passes.append(("Finish Floor", 14, 0.0, finish_t14))
    return passes


def write_plan(path):
    import json

    plan = [
        {"name": name, "tool": tool, "stock_to_leave_mm": round(stock, 4), "contacts_mm": [list(ring.contact) for ring in rings],
         "centers_mm": [list(ring.center) for ring in rings]}
        for name, tool, stock, rings in plan_passes()
    ]
    with open(path, "w") as output:
        json.dump(plan, output, indent=1)
    return plan


if __name__ == "__main__":
    import os

    for entry in write_plan(os.path.join(os.path.dirname(os.path.abspath(__file__)), "king_cup_rings.json")):
        length = sum(2 * math.pi * c[0] for c in entry["centers_mm"])
        print(f"{entry['name']:24s} T{entry['tool']:<3d} stock {entry['stock_to_leave_mm']:.2f} rings {len(entry['contacts_mm']):3d} path {length:6.0f} mm")
