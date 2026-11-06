"""Audits the finishing passes: contact angle on the ball, real cutting speed, climb or conventional, entries, segment length, and which faces each pass touches.

The per-face table at the end is how to spot retouching and leftover. Takes a few minutes.

Usage: python3 -B check_finish.py <program.nc>
"""
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay
import knight_job as job

AUDITED_PASSES = ("Finish", "Flank", "Semi", "Detail", "Trace")
BULK_SEMI_PASSES = ("Semi Upper", "Semi Lower")
SAMPLE_SPACING_MM = 0.15
PATH_STEP_MM = 0.1
CONTACT_BAND_MM = 0.02
TOUCH_BAND_MM = 0.015
# Contact angle bins, in degrees from the ball's tip. Near the tip the surface speed falls toward zero.
ANGLE_BINS_DEG = [0, 5, 15, 30, 60, 90, 181]
ANGLE_LABELS = ["0-5", "5-15", "15-30", "30-60", "60-90", ">90"]
# Below this angle, or nearly square to the feed, a sample can't be called climb or conventional.
MIN_DIRECTION_ANGLE_DEG = 10
MIN_DIRECTION_SINE = 0.3
# A share under this is sampling noise, not a pass really touching a face.
MIN_SHARE_PERCENT = 2
TOP_SHARES_PER_FACE = 4


def motion_stats(moves):
    """Feed-move statistics for one pass: segment lengths, arc count, entries and feed time."""
    segments = []
    arc_count = entry_count = 0
    minutes = 0.0
    was_cutting = False
    for move in moves:
        if move.is_link:
            was_cutting = False
            continue
        if not was_cutting:
            entry_count += 1
        was_cutting = True
        arc_count += move.motion in (2, 3)
        samples = replay.sample_move(move, PATH_STEP_MM)
        length = float(np.linalg.norm(np.diff(samples, axis=0), axis=1).sum())
        segments.append(length)
        minutes += length / move.feed_mm_per_min
    return np.array(segments), arc_count, entry_count, minutes


def motion_columns(one_pass, segments, arc_count, entry_count, minutes):
    return (
        f"{one_pass.name}|T{one_pass.tool}|{one_pass.b_deg}|{one_pass.c_deg}|{len(segments)}|{arc_count}|{entry_count}"
        f"|{segments.sum():.0f}|{minutes:.2f}|{np.median(segments):.3f}|{np.percentile(segments, 95):.3f}"
    )


def flat_pass_leftover(tips, frame, radius):
    """A flat tool cuts with its side, so only the distance across the tool axis matters."""
    across_distance, _ = cKDTree(tips[:, :2]).query(frame[:, :2], distance_upper_bound=radius + 1)
    return np.where(frame[:, 2] >= tips[:, 2].min() - 0.01, across_distance - radius, np.inf)


def ball_contact_columns(tips, frame, tool, allowance):
    """Contact angle histogram, surface speed and climb share for one ball pass."""
    radius = tool.diameter_mm / 2
    centers = tips + np.array([0, 0, radius])
    distance, index = cKDTree(frame).query(centers, distance_upper_bound=radius + 1)
    is_in_contact = np.isfinite(distance) & (np.abs(distance - radius - allowance) <= CONTACT_BAND_MM)
    to_surface = frame[np.minimum(index, len(frame) - 1)] - centers
    lengths = np.linalg.norm(to_surface, axis=1)
    lengths[lengths == 0] = 1
    to_surface /= lengths[:, None]
    angle = np.degrees(np.arccos(np.clip(-to_surface[:, 2], -1, 1)))
    contact_angle = angle[is_in_contact]
    histogram, _ = np.histogram(contact_angle, bins=ANGLE_BINS_DEG)
    speed_m_per_min = math.pi * tool.diameter_mm * np.sin(np.radians(np.minimum(contact_angle, 90))) * tool.rpm / 1000

    forward = np.zeros_like(tips)
    forward[:-1] = tips[1:] - tips[:-1]
    forward_size = np.linalg.norm(forward[:, :2], axis=1)
    forward_size[forward_size == 0] = 1
    lateral_size = np.linalg.norm(to_surface[:, :2], axis=1)
    lateral_size[lateral_size == 0] = 1
    sine = (forward[:, 0] * to_surface[:, 1] - forward[:, 1] * to_surface[:, 0]) / forward_size / lateral_size
    is_decided = is_in_contact & (angle > MIN_DIRECTION_ANGLE_DEG) & (np.abs(sine) > MIN_DIRECTION_SINE)
    climb_count = (is_decided & (sine < 0)).sum()
    conventional_count = (is_decided & (sine > 0)).sum()
    total = max(1, is_in_contact.sum())

    has_speed = len(speed_m_per_min) > 0
    median_speed = np.median(speed_m_per_min) if has_speed else 0
    low_speed = np.percentile(speed_m_per_min, 10) if has_speed else 0
    return (
        f"{100 * is_in_contact.mean():.0f}|" + "|".join(f"{100 * count / total:.0f}" for count in histogram)
        + f"|{median_speed:.1f}|{low_speed:.1f}|{100 * climb_count / total:.0f}|{100 * conventional_count / total:.0f}"
        + f"|{100 * (total - climb_count - conventional_count) / total:.0f}"
    )


def ball_leftover(tips, frame, radius):
    surface_distance, _ = cKDTree(tips + np.array([0, 0, radius])).query(frame, distance_upper_bound=radius + 2)
    return surface_distance - radius


def semi_allowance(pass_name):
    return next((stock for prefix, stock in job.SEMI_STOCK_MM.items() if pass_name.startswith(prefix)), 0.0)


def format_stats(values):
    reached = values[np.isfinite(values)]
    if not len(reached):
        return "none"
    return f"{reached.mean():.3f} {np.percentile(reached, 95):.3f} {reached.max():.3f}"


def report_faces(owners, leftover_by_pass, touched_by_pass):
    names = list(leftover_by_pass)
    finish_names = [name for name in names if not name.startswith(BULK_SEMI_PASSES)]
    semi_names = [name for name in names if name.startswith(BULK_SEMI_PASSES)]
    after_semi = np.min([leftover_by_pass[name] for name in semi_names], axis=0)
    after_finish = np.min([leftover_by_pass[name] for name in finish_names], axis=0)
    print("\nface|samples|top passes by touched %|stock after semi mean p95 worst|final leftover mean p95 worst")
    for face in sorted(set(owners.tolist())):
        is_on_face = owners == face
        shares = sorted(((float(touched_by_pass[name][is_on_face].mean() * 100), name) for name in finish_names), reverse=True)
        top_shares = [(round(share, 1), name) for share, name in shares if share >= MIN_SHARE_PERCENT][:TOP_SHARES_PER_FACE]
        print(f"{face}|{is_on_face.sum()}|{top_shares}|{format_stats(after_semi[is_on_face])}|{format_stats(after_finish[is_on_face])}")


def main():
    points, owners = replay.surface_samples(SAMPLE_SPACING_MM, job.LATHE_FACES)
    print("surface samples", len(points), flush=True)
    print("pass|tool|B|C|segs|arcs|entries|cut_len_mm|feed_min|median_seg_mm|p95_seg_mm|contact%|" + "|".join(ANGLE_LABELS) + "|med_speed_m_min|p10_speed|climb%|conv%|neutral%", flush=True)
    leftover_by_pass, touched_by_pass = {}, {}
    for one_pass in replay.read_passes(sys.argv[1]):
        if not one_pass.name.startswith(AUDITED_PASSES):
            continue
        tool = job.TOOLS[one_pass.tool]
        radius = tool.diameter_mm / 2
        moves = replay.read_moves(one_pass.lines)
        tips, _ = replay.cut_and_link_points(moves, PATH_STEP_MM)
        frame = replay.machine_frame(points, one_pass.b_deg, one_pass.c_deg)
        allowance = semi_allowance(one_pass.name)
        columns = motion_columns(one_pass, *motion_stats(moves))
        if tool.is_ball:
            columns += "|" + ball_contact_columns(tips, frame, tool, allowance)
            leftover = ball_leftover(tips, frame, radius)
        else:
            leftover = flat_pass_leftover(tips, frame, radius)
        print(columns, flush=True)
        leftover_by_pass[one_pass.name] = leftover
        touched_by_pass[one_pass.name] = np.abs(leftover - allowance) <= TOUCH_BAND_MM
    report_faces(owners, leftover_by_pass, touched_by_pass)


if __name__ == "__main__":
    main()
