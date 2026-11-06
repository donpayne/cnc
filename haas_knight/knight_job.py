"""Everything the checks need to know about this piece, its tools and the machine.

Plain Python, like pocketnc_knight/knight_geometry.py. For another piece, change these values and
re-export its faces with export_faces.py. All lengths are millimetres.
"""
import os
from typing import NamedTuple

FACES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knight_faces.json")

# G54 is the top of the turned stock, measured in the model's coordinates.
G54_MODEL_Z_MM = 60.917

# The ST-15 cuts these, so the mill's checks skip them.
LATHE_FACES = frozenset({1, 2, 3, 4, 15, 16, 17, 19, 20, 24, 28, 29, 30, 41})

# Faces each small-ball pass is meant to finish. Touching any other face counts as a retouch.
SMALL_BALL_OWNED_FACES = {
    "Detail Top Tilted": {45, 54, 62, 23, 27, 44, 53},
    "Detail Eye +Y": {21, 22},
    "Detail Eye -Y": {25, 26},
    "Trace Mane Upper +X": {9, 10, 11, 12, 13, 31, 32, 33, 34, 35},
    "Trace Mane Lower +X": {5, 6, 7, 8, 36, 37, 38, 39, 40},
    "Rough Mouth -X": {0, 14, 18, 61},
    "Detail Chin -X": {0, 14, 18, 61},
}

# Stock a semi pass leaves on purpose, so contact isn't measured against the bare model.
SEMI_STOCK_MM = {"Semi Upper": 0.1, "Semi Lower": 0.1, "Semi Eye": 0.03}


class Tool(NamedTuple):
    diameter_mm: float
    rpm: int
    gauge_to_tip_mm: float
    is_ball: bool


# gauge_to_tip_mm comes from an estimated holder envelope plus stickout. Measure the real tools.
TOOLS = {
    1: Tool(6.35, 7600, 118.9, is_ball=False),
    2: Tool(6.35, 7600, 133.6, is_ball=False),
    3: Tool(4.7625, 8000, 118.9, is_ball=True),
    4: Tool(3.175, 10000, 113.9, is_ball=True),
    5: Tool(2.38125, 10000, 113.9, is_ball=True),
    9: Tool(1.5875, 10000, 114.3, is_ball=True),
    10: Tool(1.5875, 10000, 114.3, is_ball=True),
}

# Haas UMC-350HD-EDU, from Fusion's machine file. The Z relation was checked against Simulate's readings.
Z_LIMIT_MM = -305.0
B_PIVOT_Z_MM = -8.59
NOSE_HEIGHT_AT_Z0_MM = 406.0

# The post writes links as G1 F5000 in a metric program, and no cutting feed comes near this.
LINK_FEED_MM_PER_MIN = 4000.0
