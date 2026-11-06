"""Replays the Bishop's posted lathe program with each insert's nose against the revolved model, per pass.

It reports the stock left and any gouge after the last pass, in bands along the part. The ST-15 post comes out
metric here, so this replaces the inch reading in haas_knight/check_lathe_nose.py, but keeps its nose shapes.
It doesn't model the inserts' flank clearance or the holders.

Usage: python3 -B check_lathe.py <program.nc>
"""
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))
import bishop_job as job
import check_lathe_nose as nose

nose.STOCK_TOP_Z_MM = job.G54_MODEL_Z_MM
nose.Z_HIGH_MM = job.G54_MODEL_Z_MM + 1.0
nose.Z_LOW_MM = -6.0

# Each face as (radius, z) nodes, from a finer mesh than bishop_faces.json: chord sag there reads as false gouges.
PROFILE_PATH = os.path.join(HERE, "bishop_profile.json")
NECK_RADIUS_MM = 12.6086
NECK_BOTTOM_Z_MM = -5.0
# The slit is the mill's, and faces 40 and 41 are the base's flat underside, which no lathe pass cuts yet.
FACES_OUTSIDE_THE_PROFILE = job.SLIT_FACES | {40, 41}
PASS_NAMES = (
    "Face top", "Rough head", "Rough head detail", "Finish head", "Rough body", "Rough waist",
    "Rough neck groove", "Groove under collar", "Finish body", "Groove neck",
)
GROOVE_CORNER_RADIUS_MM = 0.2
LEFTOVER_BAND_MM = 0.03
GOUGE_BAND_MM = 0.01
MM_PER_INCH = 25.4


def model_radius_by_z(z_of_row):
    """The model's largest radius at each z row, with the neck below z 0 and nothing above the top."""
    radius_mm = np.where(z_of_row < 0, NECK_RADIUS_MM, 0.0)
    with open(PROFILE_PATH) as profile_file:
        faces = json.load(profile_file)
    for face in faces:
        if face["index"] in FACES_OUTSIDE_THE_PROFILE:
            continue
        nodes = np.array(face["rz_mm"])
        unique_z, row_of_node = np.unique(np.round(nodes[:, 1], 4), return_inverse=True)
        largest_radius = np.zeros_like(unique_z)
        np.maximum.at(largest_radius, row_of_node, nodes[:, 0])
        if len(unique_z) < 2:
            continue
        in_face = (z_of_row >= unique_z[0]) & (z_of_row <= unique_z[-1])
        radius_mm[in_face] = np.maximum(radius_mm[in_face], np.interp(z_of_row[in_face], unique_z, largest_radius))
    radius_mm[z_of_row > job.G54_MODEL_Z_MM] = 0
    return radius_mm


def cut_with_rounded_groove(radius_mm, tool, tip_radius_mm, tip_z_mm):
    """The shared check models the groove insert with sharp corners, which reads as a false gouge at its r 0.2."""
    if tool[0] != "groove":
        nose.cut(radius_mm, tool, tip_radius_mm, tip_z_mm)
        return
    width_mm = tool[1]
    first_row = max(nose.index_of(tip_z_mm), 0)
    last_row = min(nose.index_of(tip_z_mm + width_mm), len(radius_mm) - 1)
    for row in range(first_row, last_row + 1):
        z_mm = nose.z_of(row)
        edge_gap_mm = max(min(z_mm - tip_z_mm, tip_z_mm + width_mm - z_mm), 0)
        lift_mm = 0.0
        if edge_gap_mm < GROOVE_CORNER_RADIUS_MM:
            lift_mm = GROOVE_CORNER_RADIUS_MM - math.sqrt(GROOVE_CORNER_RADIUS_MM ** 2 - (GROOVE_CORNER_RADIUS_MM - edge_gap_mm) ** 2)
        radius_mm[row] = min(radius_mm[row], max(tip_radius_mm + lift_mm, 0))


def turned_radius_after_program(path, row_count):
    """The bar's radius at each z row after the whole program, following each cutting move with its insert."""
    radius_mm = [nose.BAR_RADIUS_MM] * row_count
    tool = None
    in_a_pass = False
    radial_mm = axial_mm = None
    motion = 0
    with open(path) as program:
        for line in program:
            if line.strip().strip("()") in PASS_NAMES:
                in_a_pass = True
                continue
            if not in_a_pass or "G53" in line:
                continue
            code = re.sub(r"\([^)]*\)", "", line)
            selected_tool = re.match(r"T(\d)\d\d", code)
            if selected_tool:
                tool = nose.TOOLS[int(selected_tool.group(1))]
            for g_code in map(int, re.findall(r"G(\d+)", code)):
                if g_code in (0, 1, 2, 3):
                    motion = g_code
            words = dict(re.findall(r"([XZIK])(-?\d*\.?\d+)", code))
            previous = (radial_mm, axial_mm)
            if "X" in words:
                radial_mm = float(words["X"]) / 2
            if "Z" in words:
                axial_mm = float(words["Z"]) + job.G54_MODEL_Z_MM
            current = (radial_mm, axial_mm)
            if None in previous or None in current or previous == current or motion == 0:
                continue
            # move_points divides by the inch scale it was written for, so hand it inch arc centres.
            inch_words = {letter: str(float(value) / MM_PER_INCH) for letter, value in words.items()}
            for tip_radius_mm, tip_z_mm in nose.move_points(previous, current, motion, inch_words):
                cut_with_rounded_groove(radius_mm, tool, tip_radius_mm, tip_z_mm)
    return np.array(radius_mm)


def print_bands(title, is_in_band, values, z_of_row, worst):
    print(title)
    start = None
    for row in range(len(is_in_band)):
        if is_in_band[row] and start is None:
            start = row
        band_ended = start is not None and (not is_in_band[row] or row == len(is_in_band) - 1)
        if band_ended:
            print(f"  z {z_of_row[start]:.2f} to {z_of_row[row - 1]:.2f}: {worst(values[start:row]):.3f} mm")
            start = None


def main():
    row_count = nose.index_of(nose.Z_HIGH_MM) + 1
    z_of_row = np.array([nose.z_of(row) for row in range(row_count)])
    leftover_mm = turned_radius_after_program(sys.argv[1], row_count) - model_radius_by_z(z_of_row)
    is_part = z_of_row >= NECK_BOTTOM_Z_MM
    below_the_tip = is_part & (z_of_row < job.G54_MODEL_Z_MM)
    print(f"most stock left {leftover_mm[below_the_tip].max():.3f} mm, deepest gouge {leftover_mm[is_part].min():.3f} mm")
    print_bands(f"stock left over {LEFTOVER_BAND_MM} mm:", (leftover_mm > LEFTOVER_BAND_MM) & below_the_tip, leftover_mm, z_of_row, np.max)
    print_bands(f"gouges over {GOUGE_BAND_MM} mm:", (leftover_mm < -GOUGE_BAND_MM) & is_part, leftover_mm, z_of_row, np.min)


if __name__ == "__main__":
    main()
