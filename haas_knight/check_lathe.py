"""Replays the Knight's posted metric lathe program and measures stock left and gouges normal to the profile.

It runs the Pawn's check with the Knight's numbers, against the `Lathe Target` body's section: the model up to z 18.5,
the envelope of cones above it that the mill starts from, and the 5 mm neck. `check_lathe_nose.py` measures radially
and reads inch posts; this one reads metric and handles faces lying near radial, such as the head's underside. Neither
models the inserts' flank clearance or the holders.

Usage: python3 -B check_lathe.py nc/knight_lathe.nc
"""
import importlib.util
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("pawn_check_lathe", os.path.join(HERE, "..", "haas_pawn", "check_lathe.py"))
pawn_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pawn_check)

pawn_check.PROFILE_PATH = os.path.join(HERE, "knight_lathe_profile.json")
pawn_check.G54_MODEL_Z_MM = 60.917  # The turned top.
pawn_check.NECK_RADIUS_MM = 12.609  # The base's radius, carried down the 5 mm neck.
# The rows depend on the top's height, so they're rebuilt for the Knight.
pawn_check.Z_HIGH_MM = pawn_check.G54_MODEL_Z_MM + 1.0
pawn_check.ROW_COUNT = pawn_check.row_of(pawn_check.Z_HIGH_MM) + 1
pawn_check.Z_OF_ROW = pawn_check.Z_LOW_MM + pawn_check.ROW_MM * np.arange(pawn_check.ROW_COUNT)

if __name__ == "__main__":
    pawn_check.main()
