"""Replays the Queen's posted lathe program against the Lathe Target's revolved faces, per pass.

It runs the Bishop's check with the Queen's numbers. The target is the model here, since the crests above z 75.69
aren't revolved and the mill owns them. It doesn't model the inserts' flank clearance or the holders.

Usage: python3 -B check_lathe.py <program.nc>
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))

import queen_job

# The Bishop's check reads these names from its job file. The Queen has no slit.
queen_job.SLIT_FACES = frozenset()
sys.modules["bishop_job"] = queen_job

# Loaded by path, because this file has the same name.
spec = importlib.util.spec_from_file_location("bishop_check_lathe", os.path.join(HERE, "..", "haas_bishop", "check_lathe.py"))
bishop_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bishop_check)

bishop_check.PROFILE_PATH = os.path.join(HERE, "queen_lathe_profile.json")
bishop_check.NECK_RADIUS_MM = 14.468
bishop_check.nose.BAR_RADIUS_MM = queen_job.BAR_RADIUS_MM

T5_WIDTH_MM = 0.8
T5_CORNER_RADIUS_MM = 0.4
T8_CORNER_RADIUS_MM = 0.2
bishop_check.nose.TOOLS[5] = ("groove", T5_WIDTH_MM, 0.0)
cut_with_one_groove_corner = bishop_check.cut_with_rounded_groove


def cut_with_either_groove(radius_mm, tool, tip_radius_mm, tip_z_mm):
    """The Bishop's check has one groove insert, so its corner radius is set here for whichever is cutting."""
    bishop_check.GROOVE_CORNER_RADIUS_MM = T5_CORNER_RADIUS_MM if tool[1] == T5_WIDTH_MM else T8_CORNER_RADIUS_MM
    cut_with_one_groove_corner(radius_mm, tool, tip_radius_mm, tip_z_mm)


bishop_check.cut_with_rounded_groove = cut_with_either_groove


def stub_faces():
    """The bar's own surface below the neck, which no pass cuts. Left in, it would read as the model's radius."""
    with open(bishop_check.PROFILE_PATH) as profile_file:
        faces = json.load(profile_file)
    return frozenset(face["index"] for face in faces if min(r_mm for r_mm, _ in face["rz_mm"]) >= queen_job.BAR_RADIUS_MM - 1e-3)


bishop_check.FACES_OUTSIDE_THE_PROFILE = stub_faces()

if __name__ == "__main__":
    bishop_check.main()
