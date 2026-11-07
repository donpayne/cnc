"""Replays the Queen's posted mill program with each tool's full shape and reports gouges, touches and coverage.

For each sample on the model it keeps the deepest the tool came, by pass, links included. Positive means inside the tool,
which is a gouge. Near zero means the pass cut that point. Readings on concave faces include the mesh's chord error, so
a few hundredths on the flutes' r 1.14 channels aren't real: queen_flutes.py was checked against the exact cylinders.

Usage: python3 -B check_faces.py <program.nc> [pass name starts...]
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_bishop"))
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))

import queen_job as job

# The Bishop's and the Knight's code read these names from their job files.
job.SLIT_FACES = frozenset()
sys.modules["bishop_job"] = job
sys.modules["knight_job"] = job
import check_slit
import gcode_replay as replay

check_slit.SAMPLE_SPACING_MM = 0.25
GOUGE_MM = 0.02
TOUCH_MM = 0.012
# The crown and stem hold everything the mill cuts, so the base's samples are skipped to save time.
LOWEST_MILLED_Z_MM = 24.0


def deepest_reach(one_pass, points):
    frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
    return check_slit.deepest_tool_reach(one_pass, frame, cKDTree(frame[:, :2]))


def report_pass(one_pass, deepest_mm, owners):
    is_gouge = deepest_mm > GOUGE_MM
    gouged_faces = sorted(set(owners[is_gouge].tolist()))
    touched_faces = sorted(set(owners[deepest_mm > -TOUCH_MM].tolist()))
    print(
        f"{one_pass.name} T{one_pass.tool} B{one_pass.b_deg} C{one_pass.c_deg}: deepest {deepest_mm.max() * 1000:.0f} um, "
        f"gouge pts {int(is_gouge.sum())} on {gouged_faces[:12]}, touches {touched_faces[:24]}",
        flush=True,
    )


def main():
    points, owners = replay.surface_samples(check_slit.SAMPLE_SPACING_MM)
    is_milled_zone = points[:, 2] > LOWEST_MILLED_Z_MM
    points, owners = points[is_milled_zone], owners[is_milled_zone]
    print("samples", len(points), flush=True)
    starts = tuple(sys.argv[2:])
    closest_mm = np.full(len(points), -np.inf)
    passes = replay.read_passes(sys.argv[1])
    for one_pass in passes:
        if starts and not one_pass.name.startswith(starts):
            continue
        deepest_mm = deepest_reach(one_pass, points)
        report_pass(one_pass, deepest_mm, owners)
        closest_mm = np.maximum(closest_mm, deepest_mm)
    print("\nface | share touched | largest leftover (um), for faces any pass came within 0.3 mm of")
    for face in sorted(set(owners.tolist())):
        on_face = owners == face
        if closest_mm[on_face].max() < -0.3:
            continue
        print(f"{face} | {(closest_mm[on_face] > -TOUCH_MM).mean() * 100:.0f}% | {-closest_mm[on_face].min() * 1000:.0f}")


if __name__ == "__main__":
    main()
