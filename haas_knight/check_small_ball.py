"""Replays the smallest ball's passes: leftover, gouge and touch per face, plus neck and shank contact.

Faces come from knight_job.SMALL_BALL_OWNED_FACES, so a touch on any other face shows as a retouch.
Takes a few minutes.

Usage: python3 -B check_small_ball.py <program.nc>
"""
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay
import knight_job as job

CHECKED_PASSES = ("Detail", "Rough Mouth", "Trace")
BALL_RADIUS_MM = job.TOOLS[9].diameter_mm / 2
# Estimated for a 1/16 in ball with a relieved neck. Measure the real tool.
NECK_RADIUS_MM = 0.75
NECK_END_FROM_TIP_MM = 19.05
SHANK_RADIUS_MM = 1.5875
# Where the ball's own curve hands over to the neck, above the tip.
NECK_START_ABOVE_BALL_MM = 0.26
SAMPLE_SPACING_MM = 0.1
PATH_STEP_MM = 0.1
TOUCH_BAND_MM = 0.015
GOUGE_REPORT_MM = 0.03
# Any leftover deeper than this reads as "not reached", which is enough for a finish pass.
SEARCH_RADIUS_MM = 4.0


def body_contact(frame, owners, tips):
    """Deepest intrusion of the surface into neck and shank along the whole pass, links included."""
    tree = cKDTree(frame[:, :2])
    worst = dict(neck=0.0, shank=0.0)
    neck_faces = defaultdict(float)
    for tip in tips[::2]:
        near = tree.query_ball_point(tip[:2], SHANK_RADIUS_MM)
        if not near:
            continue
        near = np.array(near)
        lateral = np.hypot(frame[near, 0] - tip[0], frame[near, 1] - tip[1])
        above_tip = frame[near, 2] - tip[2]
        is_in_neck = (above_tip > BALL_RADIUS_MM + NECK_START_ABOVE_BALL_MM) & (above_tip < NECK_END_FROM_TIP_MM) & (lateral < NECK_RADIUS_MM)
        is_in_shank = (above_tip >= NECK_END_FROM_TIP_MM) & (lateral < SHANK_RADIUS_MM)
        if is_in_neck.any():
            worst["neck"] = max(worst["neck"], float((NECK_RADIUS_MM - lateral[is_in_neck]).max()))
            neck_faces[int(owners[near[is_in_neck]][0])] += 1
        if is_in_shank.any():
            worst["shank"] = max(worst["shank"], float((SHANK_RADIUS_MM - lateral[is_in_shank]).max()))
    return worst, dict(neck_faces)


def report_owned_faces(owned, owners, leftover, is_touched):
    for face in sorted(owned):
        is_on_face = owners == face
        reached = leftover[is_on_face & np.isfinite(leftover)]
        mean = reached.mean() if len(reached) else float("nan")
        worst = reached.max() if len(reached) else float("nan")
        print(f"  owned {face:2d} touched {is_touched[is_on_face].mean() * 100:5.1f}%  leftover mean {mean:.3f} worst {worst:.3f}")


def report_pass(one_pass, points, owners):
    cut, link = replay.cut_and_link_points(replay.read_moves(one_pass.lines), PATH_STEP_MM)
    frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
    ball_centers = cut + np.array([0, 0, BALL_RADIUS_MM])
    distance, _ = cKDTree(ball_centers).query(frame, distance_upper_bound=SEARCH_RADIUS_MM)
    leftover = distance - BALL_RADIUS_MM
    is_gouged = leftover < -GOUGE_REPORT_MM
    is_touched = np.abs(leftover) <= TOUCH_BAND_MM
    owned = job.SMALL_BALL_OWNED_FACES.get(one_pass.name, set())
    print(f"\n{one_pass.name} B{one_pass.b_deg} C{one_pass.c_deg} cut samples {len(cut)} links {len(link)} deepest {max(0, -leftover.min()):.3f}", flush=True)
    if is_gouged.any():
        print("  GOUGE by face", {int(face): round(float(-leftover[is_gouged & (owners == face)].min()), 3) for face in np.unique(owners[is_gouged])})
    report_owned_faces(owned, owners, leftover, is_touched)
    others = [(int(face), round(float(is_touched[owners == face].mean() * 100), 1)) for face in np.unique(owners) if face not in owned and is_touched[owners == face].any()]
    print("  non-owned touched %", sorted(others, key=lambda item: -item[1])[:12], flush=True)
    worst, neck_faces = body_contact(frame, owners, np.vstack((cut, link)))
    print("  neck", round(worst["neck"], 3), "shank", round(worst["shank"], 3), "neck faces", neck_faces, flush=True)


def main():
    points, owners = replay.surface_samples(SAMPLE_SPACING_MM, job.LATHE_FACES)
    print("samples", len(points), flush=True)
    for one_pass in replay.read_passes(sys.argv[1]):
        if one_pass.name.startswith(CHECKED_PASSES):
            report_pass(one_pass, points, owners)


if __name__ == "__main__":
    main()
