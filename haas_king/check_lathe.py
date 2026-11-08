"""Replays the King's posted lathe program against the Lathe Target's revolved faces, per pass.

It runs the Bishop's check with the King's numbers. The target is the mill's stock, not the model: it covers the
octagon and crown corners, and over the cup it stops at T8's staircase under the head. It doesn't model the inserts'
flank clearance or the holders.

Usage: python3 -B check_lathe.py <program.nc>
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "haas_knight"))

import king_job

# The Bishop's check reads these names from its job file. The King has no slit.
king_job.SLIT_FACES = frozenset()
sys.modules["bishop_job"] = king_job

# Loaded by path, because this file has the same name.
spec = importlib.util.spec_from_file_location("bishop_check_lathe", os.path.join(HERE, "..", "haas_bishop", "check_lathe.py"))
bishop_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bishop_check)

bishop_check.PROFILE_PATH = os.path.join(HERE, "king_lathe_profile.json")
bishop_check.PASS_NAMES = (
    "Face top", "Rough profile", "Rough detail", "Finish profile", "Rough under head", "Groove under head", "Groove under collar",
    "Rough neck groove", "Groove neck",
)
bishop_check.NECK_RADIUS_MM = 14.468
bishop_check.nose.BAR_RADIUS_MM = king_job.BAR_RADIUS_MM

# The King's only groove insert is T8, whose 0.2 mm corner radius is the Bishop's check default.


def stub_faces():
    """The bar's own surface below the neck, which no pass cuts. Left in, it would read as the model's radius."""
    with open(bishop_check.PROFILE_PATH) as profile_file:
        faces = json.load(profile_file)
    return frozenset(face["index"] for face in faces if min(r_mm for r_mm, _ in face["rz_mm"]) >= king_job.BAR_RADIUS_MM - 1e-3)


bishop_check.FACES_OUTSIDE_THE_PROFILE = stub_faces()

if __name__ == "__main__":
    bishop_check.main()
