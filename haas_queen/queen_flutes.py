"""The paths T14's ball center follows in the Queen's flutes. Plain Python, so it can be tested outside Fusion.

Each flute is a round-bottomed channel, r 1.1357, split down the middle by a 0.0464 mm flat, with a sphere at each end
and a radial cylinder running out past that. Sections are in the plane of the flute: r is distance from the part axis
and z is height. Offsets across the flute are y. Everything is in mm at 73%.

T14 is smaller than the channel, so the ball center follows the channel's center line at a distance of
CHANNEL_RADIUS_MM - BALL_RADIUS_MM, at several angles around it. That's what `side_deg` means: 0 is the floor, and +90
and -90 are the walls.
"""
import math
from typing import NamedTuple

TOP_Z_MM = 81.003
BALL_RADIUS_MM = 1.0
CHANNEL_RADIUS_MM = 1.1357
HALF_FLAT_MM = 0.0232
RING_OFFSET_MM = CHANNEL_RADIUS_MM - BALL_RADIUS_MM
# Arcs are split so the chord stays within this of the true curve, well inside the pass's 0.002 mm tolerance.
CHORD_ERROR_MM = 0.0005

FINISH_SIDES_DEG = (90.0, -90.0, 45.0, -45.0, 0.0)
# How far above the floor each roughing cut runs. The flute is about 1.16 mm deep, and the last cut leaves 0.03.
ROUGH_DEPTHS_ABOVE_FLOOR_MM = (0.75, 0.4, 0.03)


class Line(NamedTuple):
    start: tuple
    end: tuple


class Arc(NamedTuple):
    """A floor arc, concave toward its center, which is on the +r side of the floor."""
    start: tuple
    end: tuple
    center: tuple


# Floor curves from the low end to the high end, read from the model's faces.
STEM_LOWER_FLOOR = (Arc((6.9591, 26.5255), (4.7623, 34.5379), (28.1859, 36.6527)),)
STEM_UPPER_FLOOR = (
    Line((4.7623, 34.5379), (4.5391, 37.0098)),
    Arc((4.5391, 37.0098), (4.2942, 42.7613), (64.9348, 42.4628)),
    Line((4.2942, 42.7613), (4.3213, 48.2626)),
)
CROWN_FLOOR = (
    Line((5.4610, 65.7682), (7.2269, 71.0424)),
    Arc((7.2269, 71.0424), (7.7292, 72.4378), (38.5460, 60.5563)),
)

# Sphere centers at each end of a channel, in (r, z). A None means the path stops at the band's seam instead.
STEM_LOWER_END = (7.9841, 27.0145)
STEM_UPPER_END = (5.4569, 48.2570)
CROWN_LOWER_END = (6.5379, 65.4077)
CROWN_UPPER_END = (8.7888, 72.0292)
# Far enough along the radial run-out that the ball has left the part.
STEM_LOWER_EXIT_R_MM = 8.8
STEM_UPPER_EXIT_R_MM = 6.7
CROWN_LOWER_EXIT_R_MM = 7.7
CROWN_UPPER_EXIT_R_MM = 10.4


def _unit(vector):
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length)


def floor_points(curves):
    """Floor points in (r, z) with the normal pointing out of the floor toward the channel's center line."""
    points = []
    for curve in curves:
        if isinstance(curve, Line):
            direction = _unit((curve.end[0] - curve.start[0], curve.end[1] - curve.start[1]))
            # The channel opens toward +r, so of the two normals, take the one with positive r.
            normal = (direction[1], -direction[0]) if direction[1] > 0 else (-direction[1], direction[0])
            points.append((curve.start, normal))
            points.append((curve.end, normal))
            continue
        radius_mm = math.hypot(curve.start[0] - curve.center[0], curve.start[1] - curve.center[1])
        step_rad = 2 * math.acos(1 - CHORD_ERROR_MM / radius_mm)
        start_rad = math.atan2(curve.start[1] - curve.center[1], curve.start[0] - curve.center[0])
        end_rad = math.atan2(curve.end[1] - curve.center[1], curve.end[0] - curve.center[0])
        sweep_rad = (end_rad - start_rad + math.pi) % (2 * math.pi) - math.pi
        count = max(1, math.ceil(abs(sweep_rad) / step_rad))
        for index in range(count + 1):
            angle = start_rad + sweep_rad * index / count
            floor_point = (curve.center[0] + radius_mm * math.cos(angle), curve.center[1] + radius_mm * math.sin(angle))
            # Toward the arc's center, because that's the side the channel opens to.
            points.append((floor_point, (-math.cos(angle), -math.sin(angle))))
    return points


def center_at(floor_point, normal, side_deg):
    """The ball center in (r, y, z) for one floor point, at this angle around the channel."""
    side_rad = math.radians(side_deg)
    line_r = floor_point[0] + normal[0] * CHANNEL_RADIUS_MM
    line_z = floor_point[1] + normal[1] * CHANNEL_RADIUS_MM
    flat_offset_mm = math.copysign(HALF_FLAT_MM, side_deg) if side_deg else 0.0
    return (
        line_r - normal[0] * RING_OFFSET_MM * math.cos(side_rad),
        RING_OFFSET_MM * math.sin(side_rad) + flat_offset_mm,
        line_z - normal[1] * RING_OFFSET_MM * math.cos(side_rad),
    )


def _end_cap(end_center, normal, side_deg, end_direction_z, exit_r_mm):
    """From the channel's last point, around the end sphere, then straight out along the radial run-out."""
    side_rad = math.radians(side_deg)
    flat_offset_mm = math.copysign(HALF_FLAT_MM, side_deg) if side_deg else 0.0
    start_rad = math.atan2(-normal[1], -normal[0])
    end_rad = math.atan2(end_direction_z, 0.0)
    sweep_rad = (end_rad - start_rad + math.pi) % (2 * math.pi) - math.pi
    points = []
    steps = 6
    for index in range(1, steps + 1):
        angle = start_rad + sweep_rad * index / steps
        radial = RING_OFFSET_MM * math.cos(side_rad)
        points.append((
            end_center[0] + radial * math.cos(angle),
            RING_OFFSET_MM * math.sin(side_rad) + flat_offset_mm,
            end_center[1] + radial * math.sin(angle),
        ))
    last = points[-1]
    points.append((exit_r_mm, last[1], last[2]))
    return points


def finish_path(curves, side_deg, low_cap=None, high_cap=None):
    """Ball centers from the low end to the high end. Each cap is (sphere center, exit r), or None at a seam."""
    samples = floor_points(curves)
    path = []
    if low_cap:
        path.extend(reversed(_end_cap(low_cap[0], samples[0][1], side_deg, -1.0, low_cap[1])))
    path.extend(center_at(point, normal, side_deg) for point, normal in samples)
    if high_cap:
        path.extend(_end_cap(high_cap[0], samples[-1][1], side_deg, 1.0, high_cap[1]))
    return _without_repeats(path)


def rough_path(curves, depth_above_floor_mm, low_cap=None, high_cap=None):
    """A center-line cut raised off the floor along its normal, for clearing the channel in steps."""
    samples = floor_points(curves)
    path = []
    for point, normal in samples:
        center = center_at(point, normal, 0.0)
        path.append((center[0] + normal[0] * depth_above_floor_mm, 0.0, center[2] + normal[1] * depth_above_floor_mm))
    if low_cap:
        path.insert(0, (low_cap[1], 0.0, path[0][2]))
    if high_cap:
        path.append((high_cap[1], 0.0, path[-1][2]))
    return _without_repeats(path)


def _without_repeats(path):
    kept = [path[0]]
    for point in path[1:]:
        if math.dist(point, kept[-1]) > 1e-4:
            kept.append(point)
    return kept


def tip_of(center, c_deg, b_deg):
    """Moves a ball center to the tool tip and turns it to this C, as (x, y, z) in the model."""
    b_rad = math.radians(b_deg)
    along_radial = math.sin(b_rad)
    along_axis = math.cos(b_rad)
    r_mm = center[0] - BALL_RADIUS_MM * along_radial
    z_mm = center[2] - BALL_RADIUS_MM * along_axis
    c_rad = math.radians(c_deg)
    return (
        r_mm * math.cos(c_rad) - center[1] * math.sin(c_rad),
        r_mm * math.sin(c_rad) + center[1] * math.cos(c_rad),
        z_mm,
    )
