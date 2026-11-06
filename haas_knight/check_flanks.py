"""Replays every flank pass against the model and reports overcut and which faces it touches.

Tessellation adds several microns of noise to absolute readings, so run a baseline and the new post
together and trust the change between them at this scale. Takes a few minutes.

Usage: python3 -B check_flanks.py <program.nc> [<program.nc> ...]
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay
import knight_job as job

SURFACE_SPACING_MM = 0.1
PATH_STEP_MM = 0.01
TOUCH_BAND_MM = 0.015


def report_flank(flank, surface, owners):
    radius = job.TOOLS[flank.tool].diameter_mm / 2
    frame = replay.machine_frame(surface, flank.b_deg, flank.c_deg)
    cut, _ = replay.cut_and_link_points(replay.read_moves(flank.lines), PATH_STEP_MM)
    tip_z = cut[:, 2].min()
    # The side of the tool only cuts model points at or above its tip along the tool axis.
    is_within_reach = frame[:, 2] >= tip_z
    clearance = cKDTree(cut[:, :2]).query(frame[is_within_reach][:, :2])[0] - radius
    owner = owners[is_within_reach]
    is_touched = np.abs(clearance) < TOUCH_BAND_MM
    shares = {
        int(face): round(100 * is_touched[owner == face].mean())
        for face in sorted(set(owner[is_touched]))
        if is_touched[owner == face].mean() >= 0.05
    }
    print(
        f"  {flank.name}: tip Z {tip_z:.3f}, worst overcut {clearance.min() * 1000:.1f} um, "
        f"below -5 um {(clearance < -0.005).sum()}, below -15 um {(clearance < -0.015).sum()}, "
        f"touched pts {is_touched.sum()}, faces >=5% {shares}",
        flush=True,
    )


def main():
    surface, owners = replay.surface_samples(SURFACE_SPACING_MM)
    print("model samples", len(surface), flush=True)
    for path in sys.argv[1:]:
        print(path)
        for one_pass in replay.read_passes(path):
            if one_pass.name.startswith("Flank"):
                report_flank(one_pass, surface, owners)


if __name__ == "__main__":
    main()
