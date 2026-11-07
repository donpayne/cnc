"""Checks the grooves T5 and T8 cut near the crown in true 2D: how far any point of the lathe target sits inside the insert.

check_lathe.py keeps one radius per z row, so it can't represent the crest envelope's small notch at r 4.59-4.70 on the
crown's cone, and it reads -0.32 mm there. This check has no rows, and that reading is 0 here.

Usage: python3 -B check_grooves.py <program.nc>
"""
import json
import os
import re
import sys
from typing import NamedTuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))
import check_lathe_nose as nose


class Insert(NamedTuple):
    width_mm: float
    corner_mm: float


T5 = Insert(0.8, 0.4)
T8 = Insert(3.0, 0.2)
GROOVES = {
    "Groove crown cone": T8,
    "Rough finial neck": T5,
    "Finish finial neck": T5,
    "Groove under flange": T8,
}
PROFILE_PATH = os.path.join(HERE, "queen_lathe_profile.json")
MM_PER_INCH = 25.4
TOP_Z_MM = 81.003
POINT_SPACING_MM = 0.01
PATH_STEP_MM = 0.01
# Below this the target is the bar's stub, and at the bar's radius it's the bar's own surface.
LOWEST_Z_MM = -4.99
BAR_RADIUS_MM = 19.04


def target_points():
    chunks = []
    with open(PROFILE_PATH) as profile_file:
        faces = json.load(profile_file)
    for face in faces:
        # The nodes come from a mesh and aren't in path order, so joining neighbours unsorted draws false chords.
        nodes = np.array(sorted(map(tuple, face["rz_mm"]), key=lambda node: (node[1], node[0])))
        for start, end in zip(nodes, nodes[1:]):
            count = max(1, int(np.hypot(*(end - start)) / POINT_SPACING_MM))
            chunks.append(start + np.outer(np.arange(count + 1) / count, end - start))
    points = np.vstack(chunks)
    return points[(points[:, 1] > LOWEST_Z_MM) & (points[:, 0] < BAR_RADIUS_MM)]


def deepest_inside(points, insert, insert_r_mm, insert_z_mm):
    """The insert's reference point is its lower corner at its flat end, as the post writes it."""
    width_mm, corner_mm = insert
    near = points[(points[:, 1] > insert_z_mm) & (points[:, 1] < insert_z_mm + width_mm) & (points[:, 0] > insert_r_mm)]
    if not len(near):
        return 0.0
    r_mm, z_mm = near[:, 0] - insert_r_mm, near[:, 1] - insert_z_mm
    depth_mm = np.minimum.reduce([r_mm, z_mm, width_mm - z_mm])
    for corner_z_mm, is_beside_corner in (
        (corner_mm, z_mm < corner_mm),
        (width_mm - corner_mm, z_mm > width_mm - corner_mm),
    ):
        is_in_corner = is_beside_corner & (r_mm < corner_mm)
        depth_mm[is_in_corner] = np.maximum(corner_mm - np.hypot(r_mm[is_in_corner] - corner_mm, z_mm[is_in_corner] - corner_z_mm), 0)
    return float(depth_mm.max())


def tip_positions_of_pass(path, name):
    """Every position of the reference point, with arcs followed rather than joined by chords."""
    tips = []
    is_in_pass = False
    r_mm = z_mm = None
    motion = 0
    with open(path) as program:
        for line in program:
            if line.strip() == f"({name})":
                is_in_pass = True
                continue
            if is_in_pass and line.startswith("("):
                break
            if not is_in_pass or "G53" in line:
                continue
            for g_code in map(int, re.findall(r"G(\d+)", line)):
                if g_code in (0, 1, 2, 3):
                    motion = g_code
            words = dict(re.findall(r"([XZIK])(-?\d*\.?\d+)", line))
            previous = (r_mm, z_mm)
            if "X" in words:
                r_mm = float(words["X"]) / 2
            if "Z" in words:
                z_mm = float(words["Z"]) + TOP_Z_MM
            if None in previous + (r_mm, z_mm) or previous == (r_mm, z_mm) or motion == 0:
                continue
            # move_points divides by the inch scale it was written for, so it gets inch arc centres.
            inch_words = {letter: str(float(value) / MM_PER_INCH) for letter, value in words.items()}
            tips.extend(nose.move_points(previous, (r_mm, z_mm), motion, inch_words))
    return tips


def main():
    points = target_points()
    for name, insert in GROOVES.items():
        tips = tip_positions_of_pass(sys.argv[1], name)
        deepest_mm = max(deepest_inside(points, insert, tip_r_mm, tip_z_mm) for tip_r_mm, tip_z_mm in tips)
        print(f"{name}: deepest target point inside the insert {deepest_mm:.3f} mm, closest to the axis r {min(tip[0] for tip in tips):.3f}")


if __name__ == "__main__":
    main()
