"""Compares two posted programs pass by pass, to see exactly what a change touched.

Fusion leaves outdated passes out of a post with no error, so a missing or much shorter pass is the
first thing to look for. Passes whose text changed also get an arc-aware distance, split by cutting
moves and links, because a chord comparison overstates arcs by their sagitta.

Usage: python3 -B compare_posts.py <baseline.nc> <new.nc>
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay

PATH_STEP_MM = 0.01


def code_lines(one_pass):
    """N numbers shift whenever an earlier pass changes length, so they don't count as a change."""
    return [replay.code_of(line) for line in one_pass.lines]


def farthest_um(baseline_points, new_points):
    if not len(baseline_points) or not len(new_points):
        return float("nan"), float("nan")
    forward = cKDTree(new_points).query(baseline_points)[0]
    backward = cKDTree(baseline_points).query(new_points)[0]
    return max(forward.max(), backward.max()) * 1000, np.percentile(np.concatenate((forward, backward)), 99.9) * 1000


def describe_change(baseline, new):
    if baseline is None or new is None:
        return "MISSING"
    if code_lines(baseline) == code_lines(new):
        return "same"
    baseline_cut, baseline_link = replay.cut_and_link_points(replay.read_moves(baseline.lines), PATH_STEP_MM)
    new_cut, new_link = replay.cut_and_link_points(replay.read_moves(new.lines), PATH_STEP_MM)
    cut_max, cut_p999 = farthest_um(baseline_cut, new_cut)
    link_max, link_p999 = farthest_um(baseline_link, new_link)
    return f"cuts max {cut_max:.1f} p99.9 {cut_p999:.1f} um; links max {link_max:.1f} p99.9 {link_p999:.1f} um"


def main():
    baseline_passes = {one_pass.name: one_pass for one_pass in replay.read_passes(sys.argv[1])}
    new_passes = {one_pass.name: one_pass for one_pass in replay.read_passes(sys.argv[2])}
    print(f"{'pass':28s} {'lines':>8s} {'lines':>8s}  change")
    for name in list(baseline_passes) + [name for name in new_passes if name not in baseline_passes]:
        baseline, new = baseline_passes.get(name), new_passes.get(name)
        baseline_count = len(baseline.lines) if baseline else None
        new_count = len(new.lines) if new else None
        print(f"{name:28s} {baseline_count!s:>8} {new_count!s:>8}  {describe_change(baseline, new)}", flush=True)


if __name__ == "__main__":
    main()
