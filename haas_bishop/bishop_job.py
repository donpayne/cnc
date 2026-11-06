"""Everything the checks need to know about the Bishop, its tools and the machine, for haas_knight's replay code.

Named fields match knight_job.py. All lengths are millimetres.
"""
import os
from typing import NamedTuple

FACES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bishop_faces.json")

# G54 is the finial's tip, the top of the 73% model.
G54_MODEL_Z_MM = 72.9111

# Face numbers are the index in bishop_faces.json. The mill only cuts the slit: its floor and two walls.
SLIT_FACES = frozenset({35, 38, 39})


class Tool(NamedTuple):
    diameter_mm: float
    rpm: int
    gauge_to_tip_mm: float
    is_ball: bool
    # The cutter or relieved neck runs this far above the tip, and the shank starts there.
    neck_length_mm: float
    shank_diameter_mm: float


# All of these are estimates, from catalog-style dimensions and an estimated holder. Measure the real tools.
TOOLS = {
    9: Tool(1.5875, 10000, 114.3, is_ball=True, neck_length_mm=19.05, shank_diameter_mm=3.175),
    13: Tool(2.0, 10000, 115.6, is_ball=False, neck_length_mm=14.0, shank_diameter_mm=3.175),
}

# Haas UMC-350HD-EDU, from Fusion's machine file, as on the Knight.
Z_LIMIT_MM = -305.0
B_PIVOT_Z_MM = -8.59
NOSE_HEIGHT_AT_Z0_MM = 406.0

# The post writes links as G1 F5000 in a metric program, and no cutting feed comes near this.
LINK_FEED_MM_PER_MIN = 4000.0
