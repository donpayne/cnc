"""Everything the checks need to know about the Rook, its tools and the machine, for haas_knight's replay code.

Named fields match knight_job.py. All lengths are millimetres.
"""
import os
from typing import NamedTuple

FACES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rook_faces.json")

# G54 is the finished top, which the ST-15 faces.
G54_MODEL_Z_MM = 56.788

# Face numbers are the index in rook_faces.json: the revolved faces, the bottom and the merlon tops.
LATHE_FACES = frozenset({0, 1, 2, 3, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 32, 38, 43, 48, 53, 58, 63, 68})

SMALL_BALL_OWNED_FACES = {}
SEMI_STOCK_MM = {"Semi Head": 0.1, "Semi Shaft": 0.1, "Semi Pocket": 0.03}


class Tool(NamedTuple):
    diameter_mm: float
    rpm: int
    gauge_to_tip_mm: float
    is_ball: bool


# gauge_to_tip_mm comes from an estimated holder envelope plus stickout. Measure the real tools.
TOOLS = {
    1: Tool(6.35, 7600, 118.9, is_ball=False),
    2: Tool(6.35, 7600, 133.6, is_ball=False),
    11: Tool(2.0, 10000, 102.9, is_ball=False),
    12: Tool(1.5875, 10000, 101.6, is_ball=False),
}

# Haas UMC-350HD-EDU, from Fusion's machine file, as on the Knight.
Z_LIMIT_MM = -305.0
B_PIVOT_Z_MM = -8.59
NOSE_HEIGHT_AT_Z0_MM = 406.0

# The post writes links as G1 F5000 in a metric program, and no cutting feed comes near this.
LINK_FEED_MM_PER_MIN = 4000.0
