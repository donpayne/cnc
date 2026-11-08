"""Replays the Pawn's posted lathe program with each insert's nose, and measures stock left and gouges normal to the
profile.

The Bishop's check measures radially, one radius per z row. That misreads faces lying near radial, and the Pawn has
two: the collar's underside (13.5 deg from radial) and the lower bead's (17 deg). Here the turned and model radii are
both kept per 0.002 mm row, each is joined into a polyline, and every turned point is measured to the nearest model
point. Inserts follow haas_knight/check_lathe_nose.py: T6 nose r 0.8 centred at (r + 0.8, z + 0.8), T7 r 0.4 at
(r + 0.4, z), and T8 a 3 mm groove from z up, with r 0.2 corners as in haas_bishop/check_lathe.py. It doesn't model the
inserts' flank clearance or the holders.

Usage: python3 -B check_lathe.py nc/pawn_lathe.nc
"""
import json
import math
import os
import re
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(HERE, "pawn_profile.json")

G54_MODEL_Z_MM = 46.0172  # The ball's top.
BAR_RADIUS_MM = 15.875
NECK_RADIUS_MM = 10.3304  # The foot's radius, carried down the 5 mm stub.
Z_LOW_MM, Z_HIGH_MM = -5.0, G54_MODEL_Z_MM + 1.0
ROW_MM = 0.002
NOSES = {6: (0.8, 0.8), 7: (0.4, 0.0)}  # Nose radius, centre's height above the programmed point.
GROOVE_TOOL = 8
GROOVE_WIDTH_MM = 3.0
GROOVE_CORNER_RADIUS_MM = 0.2
# The foot's underside, z 0, is cut by the part-off, which has no pass yet.
PART_BOTTOM_Z_MM = 0.0
LEFTOVER_REPORT_MM = 0.03
GOUGE_REPORT_MM = 0.005
SAMPLE_MM = 0.005


def row_of(z_mm):
    return int(round((z_mm - Z_LOW_MM) / ROW_MM))


ROW_COUNT = row_of(Z_HIGH_MM) + 1
Z_OF_ROW = Z_LOW_MM + ROW_MM * np.arange(ROW_COUNT)


def model_radius_by_row():
    """The model's radius at each row: the section's polylines, the stub below z 0, nothing above the top."""
    with open(PROFILE_PATH) as profile_file:
        curves = json.load(profile_file)["curves_rz_mm"]
    radius_mm = np.where(Z_OF_ROW < PART_BOTTOM_Z_MM, NECK_RADIUS_MM, 0.0)
    for curve in curves:
        for (r0, z0), (r1, z1) in zip(curve, curve[1:]):
            low, high = sorted((z0, z1))
            rows = np.arange(max(row_of(low), 0), min(row_of(high), ROW_COUNT - 1) + 1)
            if len(rows) == 0:
                continue
            if abs(z1 - z0) < 1e-9:
                radius_along = np.full(len(rows), max(r0, r1))
            else:
                radius_along = r0 + (r1 - r0) * (Z_OF_ROW[rows] - z0) / (z1 - z0)
            radius_mm[rows] = np.maximum(radius_mm[rows], radius_along)
    return radius_mm


def arc_points(start, end, motion, center):
    """Points along an arc in (r, z), turning as haas_knight/check_lathe_nose.py found for this post."""
    radius = math.dist(start, center)
    end_error = abs(math.dist(end, center) - radius)
    assert end_error < 0.005, f"arc centre is inconsistent by {end_error:.4f} mm"
    angle_start = math.atan2(start[0] - center[0], start[1] - center[1])
    sweep = math.atan2(end[0] - center[0], end[1] - center[1]) - angle_start
    if motion == 3 and sweep < 0:
        sweep += 2 * math.pi
    if motion == 2 and sweep > 0:
        sweep -= 2 * math.pi
    count = max(2, int(abs(sweep) * radius / SAMPLE_MM))
    angles = angle_start + sweep * np.arange(count + 1) / count
    return np.column_stack((center[0] + radius * np.sin(angles), center[1] + radius * np.cos(angles)))


def line_points(start, end):
    count = max(2, int(math.dist(start, end) / SAMPLE_MM))
    fraction = np.arange(count + 1)[:, None] / count
    return np.asarray(start) + (np.asarray(end) - np.asarray(start)) * fraction


def cut(turned_mm, tool_number, tip_r_mm, tip_z_mm):
    if tool_number == GROOVE_TOOL:
        rows = np.arange(max(row_of(tip_z_mm), 0), min(row_of(tip_z_mm + GROOVE_WIDTH_MM), ROW_COUNT - 1) + 1)
        if len(rows) == 0:
            return
        edge_gap = np.clip(np.minimum(Z_OF_ROW[rows] - tip_z_mm, tip_z_mm + GROOVE_WIDTH_MM - Z_OF_ROW[rows]), 0, None)
        corner = GROOVE_CORNER_RADIUS_MM
        lift = np.where(edge_gap < corner, corner - np.sqrt(np.clip(corner ** 2 - (corner - edge_gap) ** 2, 0, None)), 0)
        turned_mm[rows] = np.minimum(turned_mm[rows], np.maximum(tip_r_mm + lift, 0))
        return
    nose_mm, centre_lift_mm = NOSES[tool_number]
    centre_r, centre_z = tip_r_mm + nose_mm, tip_z_mm + centre_lift_mm
    rows = np.arange(max(row_of(centre_z - nose_mm), 0), min(row_of(centre_z + nose_mm), ROW_COUNT - 1) + 1)
    if len(rows) == 0:
        return
    half = np.sqrt(np.clip(nose_mm ** 2 - (Z_OF_ROW[rows] - centre_z) ** 2, 0, None))
    turned_mm[rows] = np.minimum(turned_mm[rows], np.maximum(centre_r - half, 0))


def replay(path):
    """The turned radius per row after the whole program, and each pass's largest feed per rev."""
    turned_mm = np.full(ROW_COUNT, BAR_RADIUS_MM)
    feeds = {}
    pass_name = tool_number = None
    position = (None, None)
    motion = 0
    feed = 0.0
    with open(path) as program:
        for line in program:
            stripped = line.strip()
            if stripped.startswith("(") and stripped.endswith(")"):
                pass_name = stripped.strip("()")
                continue
            if pass_name is None or "G53" in line:
                continue
            assert not re.search(r"G4[12]\b", line), "the replay assumes no nose compensation"
            selected = re.match(r"T(\d)\d\d", stripped)
            if selected:
                tool_number = int(selected.group(1))
            for g_code in map(int, re.findall(r"G(\d+)", stripped)):
                if g_code in (0, 1, 2, 3):
                    motion = g_code
            words = {letter: float(value) for letter, value in re.findall(r"([XZIKF])(-?\d*\.?\d+)", stripped)}
            if "F" in words:
                feed = words["F"]
            previous = position
            position = (
                words["X"] / 2 if "X" in words else position[0],
                words["Z"] + G54_MODEL_Z_MM if "Z" in words else position[1],
            )
            if None in previous or None in position or previous == position or motion == 0:
                continue
            feeds[pass_name] = max(feeds.get(pass_name, 0.0), feed)
            if motion == 1:
                points = line_points(previous, position)
            else:
                centre = (previous[0] + words.get("I", 0.0), previous[1] + words.get("K", 0.0))
                points = arc_points(previous, position, motion, centre)
            for tip_r, tip_z in points:
                cut(turned_mm, tool_number, tip_r, tip_z)
    return turned_mm, feeds


def profile_polyline(radius_mm):
    """The rows' (r, z) points, with each radial jump between rows filled in, so near-radial faces are represented."""
    points = []
    for row in range(ROW_COUNT - 1):
        r0, r1 = radius_mm[row], radius_mm[row + 1]
        steps = max(1, int(abs(r1 - r0) / ROW_MM))
        fraction = np.arange(steps) / steps
        points.append(np.column_stack((r0 + (r1 - r0) * fraction, Z_OF_ROW[row] + ROW_MM * fraction)))
    return np.vstack(points)


def print_bands(title, points, depth_mm, is_reported):
    print(title)
    order = np.argsort(points[:, 1])
    points, depth_mm, is_reported = points[order], depth_mm[order], is_reported[order]
    start = None
    for index in range(len(points) + 1):
        is_on = index < len(points) and is_reported[index]
        if is_on and start is None:
            start = index
        if not is_on and start is not None:
            band = slice(start, index)
            worst = np.argmax(depth_mm[band]) + start
            print(f"  z {points[start, 1]:.3f} to {points[index - 1, 1]:.3f}: {depth_mm[worst]:.3f} mm at r {points[worst, 0]:.3f}")
            start = None


def main():
    model_mm = model_radius_by_row()
    turned_mm, feeds = replay(sys.argv[1])
    model_points = profile_polyline(model_mm)
    turned_points = profile_polyline(turned_mm)
    distance_mm, _ = cKDTree(model_points).query(turned_points)
    model_at_point = np.interp(turned_points[:, 1], Z_OF_ROW, model_mm)
    is_outside = turned_points[:, 0] > model_at_point
    on_part = (turned_points[:, 1] >= PART_BOTTOM_Z_MM) & (turned_points[:, 1] < G54_MODEL_Z_MM)
    leftover = np.where(is_outside & on_part, distance_mm, 0.0)
    gouge = np.where(~is_outside & on_part, distance_mm, 0.0)
    print(f"most stock left {leftover.max():.3f} mm, deepest gouge {gouge.max():.3f} mm, measured normal to the profile")
    print_bands(f"stock left over {LEFTOVER_REPORT_MM} mm:", turned_points, leftover, leftover > LEFTOVER_REPORT_MM)
    print_bands(f"gouges over {GOUGE_REPORT_MM} mm:", turned_points, gouge, gouge > GOUGE_REPORT_MM)
    print("largest feed per pass, mm/rev:")
    for pass_name, feed in feeds.items():
        print(f"  {pass_name}: {feed:g}")


if __name__ == "__main__":
    main()
