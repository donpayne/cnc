"""Replays the Queen's mill program with the holder and shank, and reports how close they come to the vise and the part.

Positive clearance is air. Negative means the holder or shank is inside the vise or the part's envelope. The envelope is
the model's largest radius at each height, so a shank can read negative inside a scoop that's already been cut. It leaves
out the finial's r 2.0 stub and the bar below z 0.

The holder is Fusion's estimated `CT40 ER16 x 3.5 in` envelope and the lengths are estimates, so measure them and rerun.
The vise is three boxes, sampled every few mm, and tool positions every 3 mm, so a reading can be high by a little.

Usage: python3 -B check_holder.py <program.nc>
"""
import os
import sys
from typing import NamedTuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_bishop"))
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))

import queen_job as job

# The Knight's code reads these names from its job file.
job.SLIT_FACES = frozenset()
sys.modules["knight_job"] = job
import gcode_replay as replay


class Band(NamedTuple):
    """A length of round tool, in mm measured up from the tip."""
    start_mm: float
    end_mm: float
    radius_mm: float


NOSE_LENGTH_MM = 63.5
NOSE_RADIUS_MM = 16.5
FLANGE_LENGTH_MM = 25.4
FLANGE_RADIUS_MM = 31.75


def _holder_from(height_mm):
    flange_start_mm = height_mm + NOSE_LENGTH_MM
    return [
        Band(height_mm, flange_start_mm, NOSE_RADIUS_MM),
        Band(flange_start_mm, flange_start_mm + FLANGE_LENGTH_MM, FLANGE_RADIUS_MM),
    ]


# The bands above each tool's cutter, from Fusion's tool library.
SHANKS = {
    3: [Band(15.875, 30.0, 2.381)],
    4: [Band(9.525, 25.0, 1.5875)],
    10: [Band(4.7625, 19.05, 0.794), Band(19.05, 25.4, 1.5875)],
    14: [Band(3.0, 10.0, 1.0), Band(10.0, 20.0, 1.5875)],
}
HOLDERS = {tool: _holder_from(bands[-1].end_mm) for tool, bands in SHANKS.items()}

# In the model's frame, measured from the part's axis and its z 0.
JAW_X_MM = (-65.0, 65.0)
JAW_Y_MM = (0.5, 74.5)
JAW_Z_MM = (-58.0, -8.0)
VISE_BODY_Y_MM = (-80.0, 80.0)
VISE_BODY_Z_MM = (-111.0, -58.0)
JAW_SAMPLE_MM = 2.5
VISE_BODY_SAMPLE_MM = 4.0

TOOL_POSITION_STEP_MM = 3.0
ENVELOPE_SAMPLE_MM = 0.5
ENVELOPE_ROW_MM = 0.25
ENVELOPE_ANGLE_STEP_DEG = 4
THIN_CLEARANCE_MM = 5.0


def box_surface(x_range, y_range, z_range, spacing_mm):
    """Sample points on a box's six faces."""
    xs, ys, zs = [np.arange(low, high + spacing_mm, spacing_mm).clip(max=high) for low, high in (x_range, y_range, z_range)]
    faces = [np.array(np.meshgrid(xs, ys, [z])).reshape(3, -1).T for z in (zs[0], zs[-1])]
    faces += [np.array(np.meshgrid([x], ys, zs)).reshape(3, -1).T for x in (xs[0], xs[-1])]
    faces += [np.array(np.meshgrid(xs, [y], zs)).reshape(3, -1).T for y in (ys[0], ys[-1])]
    return np.vstack(faces)


def vise_points():
    near_jaw_y_mm = (-JAW_Y_MM[1], -JAW_Y_MM[0])
    return np.vstack([
        box_surface(JAW_X_MM, JAW_Y_MM, JAW_Z_MM, JAW_SAMPLE_MM),
        box_surface(JAW_X_MM, near_jaw_y_mm, JAW_Z_MM, JAW_SAMPLE_MM),
        box_surface(JAW_X_MM, VISE_BODY_Y_MM, VISE_BODY_Z_MM, VISE_BODY_SAMPLE_MM),
    ])


def envelope_points():
    """Circles at the model's largest radius for each height, which is what the part looks like before the mill cuts it."""
    samples, _ = replay.surface_samples(ENVELOPE_SAMPLE_MM)
    rows = np.round(samples[:, 2] / ENVELOPE_ROW_MM).astype(int)
    angles_rad = np.radians(np.arange(0, 360, ENVELOPE_ANGLE_STEP_DEG))
    circles = []
    for row in np.unique(rows):
        radius_mm = np.hypot(*samples[rows == row, :2].T).max()
        height_mm = np.full_like(angles_rad, row * ENVELOPE_ROW_MM)
        circles.append(np.c_[radius_mm * np.cos(angles_rad), radius_mm * np.sin(angles_rad), height_mm])
    return np.vstack(circles)


def tool_positions(one_pass):
    return np.vstack([replay.sample_move(move, TOOL_POSITION_STEP_MM) for move in replay.read_moves(one_pass.lines)])


def smallest_clearance(tips, points_in_machine_frame, bands):
    """The closest any band comes to any point, in mm. Infinity means no point was ever level with a band."""
    closest_mm = np.inf
    for band in bands:
        for tip in tips:
            height_mm = points_in_machine_frame[:, 2] - tip[2]
            is_level = (height_mm > band.start_mm) & (height_mm < band.end_mm)
            if not is_level.any():
                continue
            level_points = points_in_machine_frame[is_level]
            distance_mm = np.hypot(level_points[:, 0] - tip[0], level_points[:, 1] - tip[1])
            closest_mm = min(closest_mm, distance_mm.min() - band.radius_mm)
    return closest_mm


def main():
    vise = vise_points()
    envelope = envelope_points()
    print("pass | tool | B | C | to vise | holder to part | shank to part")
    thin_passes = []
    for one_pass in replay.read_passes(sys.argv[1]):
        tips = tool_positions(one_pass)
        shank, holder = SHANKS[one_pass.tool], HOLDERS[one_pass.tool]
        vise_frame = replay.machine_frame(vise, one_pass.b_deg, one_pass.c_deg)
        envelope_frame = replay.machine_frame(envelope, one_pass.b_deg, one_pass.c_deg)
        to_vise_mm = smallest_clearance(tips, vise_frame, shank + holder)
        holder_to_part_mm = smallest_clearance(tips, envelope_frame, holder)
        shank_to_part_mm = smallest_clearance(tips, envelope_frame, shank)
        c_deg = one_pass.c_deg % 360
        print(
            f"{one_pass.name} | T{one_pass.tool} | {one_pass.b_deg:.0f} | {c_deg:.1f} | "
            f"{to_vise_mm:.2f} | {holder_to_part_mm:.2f} | {shank_to_part_mm:.2f}",
            flush=True,
        )
        if min(to_vise_mm, holder_to_part_mm) < THIN_CLEARANCE_MM:
            thin_passes.append(f"{one_pass.name} at C {c_deg:.1f}")
    print(f"\nholder within {THIN_CLEARANCE_MM:.0f} mm of the vise or part: {thin_passes or 'none'}")


if __name__ == "__main__":
    main()
