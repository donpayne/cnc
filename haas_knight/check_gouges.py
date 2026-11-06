"""Replays every move of the chosen passes, rapids and links included, and reports where the tool enters the part.

The other checks look at what a pass leaves. This one catches a link cutting through a finished face.
Pass names can be limited to save time, because it steps through every move. Takes several minutes on all of them.

Usage: python3 -B check_gouges.py <program.nc> [<pass name start> ...]
"""
import os
import sys
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay
import knight_job as job

# Rough passes leave 0.4 mm and take far longer to step through, so they're only checked on request.
DEFAULT_PASSES = ("Semi", "Flank", "Finish", "Detail", "Trace", "Rough Mouth")
SAMPLE_SPACING_MM = 0.3
PATH_STEP_MM = 0.1
# Fine tessellation and sampling put about this much noise on a tangent cut, so only deeper readings mean anything.
GOUGE_TOLERANCE_MM = 0.03


def tool_penetration(frame, xy_tree, tip, radius, is_ball):
    """Deepest intrusion of a surface point into the tool at this tip position, with the points that went deep."""
    hits = xy_tree.query_ball_point(tip[:2], radius)
    if not hits:
        return 0.0, []
    hits = np.array(hits)
    near = frame[hits]
    if is_ball:
        center_z = tip[2] + radius
        depth = radius - np.sqrt((near[:, 0] - tip[0]) ** 2 + (near[:, 1] - tip[1]) ** 2 + np.maximum(center_z - near[:, 2], 0) ** 2)
    else:
        xy_gap = radius - np.hypot(near[:, 0] - tip[0], near[:, 1] - tip[1])
        depth = np.where(near[:, 2] >= tip[2], xy_gap, -1.0)
    return float(depth.max()), hits[depth > GOUGE_TOLERANCE_MM]


def check_pass(one_pass, points, owners):
    tool = job.TOOLS[one_pass.tool]
    frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
    xy_tree = cKDTree(frame[:, :2])
    result = dict(cut=0.0, link=0.0, cut_moves=0, link_moves=0, faces=Counter(), worst_move="")
    for move in replay.read_moves(one_pass.lines):
        deepest = 0.0
        hit_faces = set()
        for tip in replay.sample_move(move, PATH_STEP_MM):
            depth, hits = tool_penetration(frame, xy_tree, tip, tool.diameter_mm / 2, tool.is_ball)
            deepest = max(deepest, depth)
            if len(hits):
                hit_faces.update(owners[hits].tolist())
        if deepest <= GOUGE_TOLERANCE_MM:
            continue
        kind = "link" if move.is_link else "cut"
        result[kind + "_moves"] += 1
        if deepest > max(result["cut"], result["link"]):
            result["worst_move"] = move.source
        result[kind] = max(result[kind], deepest)
        result["faces"].update(hit_faces)
    return result


def main():
    chosen_passes = tuple(sys.argv[2:]) or DEFAULT_PASSES
    points, owners = replay.surface_samples(SAMPLE_SPACING_MM)
    print("samples", len(points), flush=True)
    for one_pass in replay.read_passes(sys.argv[1]):
        if not one_pass.name.startswith(chosen_passes):
            continue
        result = check_pass(one_pass, points, owners)
        print(
            f"{one_pass.name} T{one_pass.tool} B{one_pass.b_deg} C{one_pass.c_deg}: "
            f"cut gouge moves {result['cut_moves']} max {result['cut']:.3f} | "
            f"link hits {result['link_moves']} max {result['link']:.3f} | "
            f"worst move {result['worst_move'] or 'none'} | faces {sorted(result['faces'])}",
            flush=True,
        )


if __name__ == "__main__":
    main()
