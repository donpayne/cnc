"""Replays the posted Bishop mill program with each tool's full shape and reports gouges and slit coverage.

For each model sample it keeps the deepest the tool came, by pass. Positive means inside the tool, which is a gouge.
Near zero means the pass cut that point. Lathe faces meet the slit at its edges, so they show a few touches there.

Usage: python3 -B check_slit.py <program.nc>
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))
import bishop_job as job

sys.modules["knight_job"] = job
import gcode_replay as replay

SAMPLE_SPACING_MM = 0.25
PATH_STEP_MM = 0.08
# The flat tool's sides are read against a faceted model, so readings this small are grid noise.
GOUGE_MM = 0.012
TOUCH_MM = 0.012
NEAR_RADIUS_MARGIN_MM = 0.05


def depth_inside_tool(radial_mm, height_mm, tool):
    """Signed depth of points inside the tool. height_mm is measured from the tip along the tool axis."""
    tip_radius_mm = tool.diameter_mm / 2
    body_radius_mm = np.where(height_mm < tool.neck_length_mm, tip_radius_mm, tool.shank_diameter_mm / 2)
    body_depth_mm = np.minimum(body_radius_mm - radial_mm, height_mm)
    if not tool.is_ball:
        return body_depth_mm
    ball_depth_mm = tip_radius_mm - np.hypot(radial_mm, height_mm - tip_radius_mm)
    return np.where(height_mm < tip_radius_mm, ball_depth_mm, body_depth_mm)


def deepest_tool_reach(one_pass, frame, tree):
    """The largest signed depth of each sample inside the tool, over all of this pass's moves."""
    tool = job.TOOLS[one_pass.tool]
    search_radius_mm = max(tool.diameter_mm, tool.shank_diameter_mm) / 2 + NEAR_RADIUS_MARGIN_MM
    deepest_mm = np.full(len(frame), -np.inf)
    moves = replay.read_moves(one_pass.lines)
    for tip in np.vstack([replay.sample_move(move, PATH_STEP_MM) for move in moves]):
        nearby = tree.query_ball_point(tip[:2], search_radius_mm)
        if not nearby:
            continue
        nearby = np.array(nearby)
        radial_mm = np.hypot(frame[nearby, 0] - tip[0], frame[nearby, 1] - tip[1])
        depth_mm = depth_inside_tool(radial_mm, frame[nearby, 2] - tip[2], tool)
        deepest_mm[nearby] = np.maximum(deepest_mm[nearby], depth_mm)
    return deepest_mm


def report_pass(one_pass, deepest_mm, owners):
    is_gouge = deepest_mm > GOUGE_MM
    is_slit = np.isin(owners, sorted(job.SLIT_FACES))
    touched_lathe_faces = sorted(set(owners[(deepest_mm > -TOUCH_MM) & ~is_slit].tolist()))
    slit_worst_mm = float(deepest_mm[is_slit].max())
    lathe_worst_mm = float(deepest_mm[~is_slit].max())
    print(
        f"{one_pass.name} T{one_pass.tool} B{one_pass.b_deg} C{one_pass.c_deg}: "
        f"slit worst {slit_worst_mm * 1000:.0f} um, lathe faces worst {lathe_worst_mm * 1000:.0f} um, "
        f"gouge pts {int(is_gouge.sum())} on faces {sorted(set(owners[is_gouge].tolist()))}, "
        f"lathe faces touched {touched_lathe_faces}",
        flush=True,
    )


def main():
    points, owners = replay.surface_samples(SAMPLE_SPACING_MM)
    print("samples", len(points), flush=True)
    is_finished = np.zeros(len(points), dtype=bool)
    closest_to_finish_mm = np.full(len(points), -np.inf)
    for one_pass in replay.read_passes(sys.argv[1]):
        frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
        deepest_mm = deepest_tool_reach(one_pass, frame, cKDTree(frame[:, :2]))
        report_pass(one_pass, deepest_mm, owners)
        if one_pass.name.startswith("Flank"):
            is_finished |= np.abs(deepest_mm) <= TOUCH_MM
            closest_to_finish_mm = np.maximum(closest_to_finish_mm, deepest_mm)
    print("\nslit face | share finished by a flank | largest leftover after the flanks (um)")
    for face in sorted(job.SLIT_FACES):
        on_face = owners == face
        print(f"{face} | {is_finished[on_face].mean() * 100:.1f}% | {-closest_to_finish_mm[on_face].min() * 1000:.0f}")


if __name__ == "__main__":
    main()
