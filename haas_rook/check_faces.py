"""Replays the posted Rook program with a flat tool and reports gouges, retouching and leftover for every face.

For each model sample it keeps the deepest the tool came, by pass. Positive means inside the tool, which is a gouge.
Near zero means the pass cut that point. Takes a minute or two.

Usage: python3 -B check_faces.py <program.nc> [<pass name start> ...]
"""
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))
import rook_job

sys.modules["knight_job"] = rook_job
import gcode_replay as replay

SAMPLE_SPACING_MM = 0.25
PATH_STEP_MM = 0.08
GOUGE_MM = 0.012
TOUCH_MM = 0.012
# Roughing's T1 has a 0.5 mm corner radius, so its gouge reading only needs to catch real errors.
MIN_FACE_SHARE = 0.03
FINISHING_PREFIXES = ("Flank", "Finish", "Trace")


def deepest_tool_reach(one_pass, frame, tree):
    """The largest signed depth of each sample inside the flat tool, over all of this pass's moves."""
    radius = rook_job.TOOLS[one_pass.tool].diameter_mm / 2
    deepest = np.full(len(frame), -np.inf)
    moves = replay.read_moves(one_pass.lines)
    for tip in np.vstack([replay.sample_move(move, PATH_STEP_MM) for move in moves]):
        nearby = tree.query_ball_point(tip[:2], radius + 0.05)
        if not nearby:
            continue
        nearby = np.array(nearby)
        radial = radius - np.hypot(frame[nearby, 0] - tip[0], frame[nearby, 1] - tip[1])
        axial = frame[nearby, 2] - tip[2]
        depth = np.minimum(radial, axial)
        deepest[nearby] = np.maximum(deepest[nearby], depth)
    return deepest


def main():
    chosen = tuple(sys.argv[2:])
    points, owners = replay.surface_samples(SAMPLE_SPACING_MM)
    print("samples", len(points), flush=True)
    finished = np.zeros(len(points), dtype=bool)
    touch_by_face = defaultdict(lambda: defaultdict(float))
    face_ids = sorted(set(owners.tolist()))
    for one_pass in replay.read_passes(sys.argv[1]):
        if chosen and not one_pass.name.startswith(chosen):
            continue
        frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
        deepest = deepest_tool_reach(one_pass, frame, cKDTree(frame[:, :2]))
        milled = ~np.isin(owners, sorted(rook_job.LATHE_FACES))
        is_gouge = deepest > GOUGE_MM
        is_touch = np.abs(deepest) <= TOUCH_MM
        if one_pass.name.startswith(FINISHING_PREFIXES):
            finished |= is_touch
        for face in face_ids:
            share = is_touch[owners == face].mean()
            if share >= MIN_FACE_SHARE:
                touch_by_face[face][one_pass.name] = round(float(share) * 100)
        gouged_faces = sorted(set(owners[is_gouge].tolist()))
        lathe_touched = sorted(set(owners[(deepest > -TOUCH_MM) & ~milled].tolist()))
        worst = float(deepest.max()) if np.isfinite(deepest).any() else float("nan")
        print(
            f"{one_pass.name} T{one_pass.tool} B{one_pass.b_deg} C{one_pass.c_deg}: worst {worst * 1000:.0f} um, "
            f"gouge pts {int(is_gouge.sum())} on faces {gouged_faces}, lathe faces touched {lathe_touched}",
            flush=True,
        )
    print("\nface | area share finished by a Flank, Finish or Trace pass | passes touching at least 3%")
    for face in face_ids:
        if face in rook_job.LATHE_FACES:
            continue
        share = finished[owners == face].mean()
        print(f"{face:3d} | {share * 100:5.1f}% | {dict(touch_by_face[face])}")


if __name__ == "__main__":
    main()
