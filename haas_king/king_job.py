"""Everything the checks need to know about the King, its tools and the machine, for haas_knight's replay code.

Named fields match knight_job.py. All lengths are millimetres.
"""
import os
from typing import NamedTuple

FACES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "king_faces.json")

# G54 is the finial's tip, the top of the 73% model.
G54_MODEL_Z_MM = 86.2316

BAR_RADIUS_MM = 19.05


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
    1: Tool(6.35, 7600, 118.9, is_ball=False, neck_length_mm=19.05, shank_diameter_mm=6.35),
    2: Tool(6.35, 7600, 133.6, is_ball=False, neck_length_mm=25.4, shank_diameter_mm=6.35),
    3: Tool(4.7625, 8000, 118.9, is_ball=True, neck_length_mm=15.88, shank_diameter_mm=4.7625),
    # 6.1 longer than the Queen's, so Octagon Strips at B90 stays inside the Z limit (needs 115.0).
    4: Tool(3.175, 10000, 120.0, is_ball=True, neck_length_mm=25.0, shank_diameter_mm=6.35),
    10: Tool(1.5875, 10000, 114.3, is_ball=True, neck_length_mm=19.05, shank_diameter_mm=3.175),
    11: Tool(2.0, 10000, 102.9, is_ball=False, neck_length_mm=6.0, shank_diameter_mm=3.0),
    14: Tool(2.0, 10000, 108.9, is_ball=True, neck_length_mm=10.0, shank_diameter_mm=3.175),
}

# Haas UMC-350HD-EDU, from Fusion's machine file, as on the Knight.
Z_LIMIT_MM = -305.0
B_PIVOT_Z_MM = -8.59
NOSE_HEIGHT_AT_Z0_MM = 406.0

# The post writes links as G1 F5000 in a metric program, and no cutting feed comes near this.
LINK_FEED_MM_PER_MIN = 4000.0
