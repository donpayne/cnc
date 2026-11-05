"""Dimensions for the chess Knight: no Fusion imports, so plain Python checks can share them.

World frame matches the Pocket NC at A0 B0: +Y runs up the part axis from the B table, +Z points at
the spindle, and the origin sits where the part axis meets the A axis. All lengths are millimetres.
"""
import math

# Y travel stops 64.77 mm from the A axis and the tool works side-on at A0, so the part's top must
# stay under that. The full-size Knight is 82.8 mm tall and would end near 89 mm.
KNIGHT_SCALE = 0.80
SOURCE_HEIGHT_MM = 82.7642
SOURCE_BASE_Z_MM = -82.7664  # Bottom of the Knight in knight_source.sat.
KNIGHT_HEIGHT_MM = SOURCE_HEIGHT_MM * KNIGHT_SCALE
KNIGHT_BASE_RADIUS_MM = 21.6027 * KNIGHT_SCALE

# From Penta's "B-table and Collet v1.step", with its assembly transforms applied. The parts' own
# coordinates don't include those: read alone, they gave 20.45 (the collet's rim) and 18.52 here.
NUT_TOP_ABOVE_TABLE_MM = 3.62
COLLET_NUT_RADIUS_MM = 25.925
TABLE_RADIUS_MM = 44.97
TABLE_TOP_Y_MM = -21.23  # Penta: machine origin is 0.836 in above the B table.
NUT_TOP_Y_MM = TABLE_TOP_Y_MM + NUT_TOP_ABOVE_TABLE_MM

STUMP_RADIUS_MM = 12.7  # Matches a 1 in ER40 collet.
# Grips about 31 mm of the 44.5 mm collet, meeting the two-thirds rule. Longer risks bottoming out.
STUMP_LENGTH_MM = 36.0
# 1.375 in. Clears the 17.28 mm Knight base by only 0.18 mm, which is enough only because the head and
# stump are turned in one lathe setup. It can't be larger: with 9.5 mm flutes, the deep pass at the ears
# keeps the shank out of the wax only up to this radius (2 x flute length - tool radius).
HEAD_RADIUS_MM = 17.4625
# The window is narrow at this scale. About 4 mm leaves the holder 2 mm from the B table on the lowest
# passes, and about 6 mm reaches the end of Y travel. 5 mm leaves about 1 mm of margin each way.
SHOULDER_ABOVE_NUT_MM = 5.0
SHOULDER_BOTTOM_Y_MM = NUT_TOP_Y_MM + SHOULDER_ABOVE_NUT_MM
SHOULDER_THICKNESS_MM = 2.0  # The wax disc left above the stump after cutting.
# Undercuts the 17.3 mm base by only 3.3 mm, and carries a Knight about 1.9 times the mass of the 65% one.
# Too narrow a neck makes the tool reach past its 9.5 mm flutes, so the smooth shank rubs the shoulder. Sawn through at the end.
NECK_RADIUS_MM = 14.0
NECK_LENGTH_MM = 5.0  # Slot under the Knight's base: 3.175 mm tool plus room to clear chips.

SHOULDER_TOP_Y_MM = SHOULDER_BOTTOM_Y_MM + SHOULDER_THICKNESS_MM
KNIGHT_BASE_Y_MM = SHOULDER_TOP_Y_MM + NECK_LENGTH_MM
KNIGHT_TOP_Y_MM = KNIGHT_BASE_Y_MM + KNIGHT_HEIGHT_MM
STOCK_ABOVE_KNIGHT_MM = 0.5  # Sawn stock varies, so leave a skin rather than air-cut.
STOCK_TOP_Y_MM = KNIGHT_TOP_Y_MM + STOCK_ABOVE_KNIGHT_MM
STOCK_BOTTOM_Y_MM = SHOULDER_BOTTOM_Y_MM - STUMP_LENGTH_MM

# With the stock on the B axis, X0 and Z0 are the machine's own center, so the only
# touch-off is Y on the top of the stock (Penta WCS tutorial, Appendix A).
WORK_ORIGIN_MM = (0.0, STOCK_TOP_Y_MM, 0.0)

# Tool directions as azimuth about the part axis, measured from +Z. Roughing runs at A0: a tool at right
# angles to the part axis sees every surface of this shape, including the snout's overhang.
# Cut in this order: the user wants sides 90 and 270 done before 0 and 180, for how the part looks.
SIDE_AZIMUTHS_DEG = (90, 270, 0, 180)

# The main finishes run 3+2 at this A angle, so walls meet the ball this far off its tip and the flutes
# do the cutting. Positive A looks down at the part, which also lifts the holder off the B table and
# eases Y travel. Too high runs out of Z travel, and hides more of the snout's underside.
FINISH_TILT_DEG = 20.0
# The neck gets sawn off, so finishing passes stop just under the base rather than running down it.
FINISH_BELOW_BASE_MM = 0.5
# A boundary projects along the tilted tool, so it climbs with distance from the part axis. Starting
# this low on the axis still reaches the rim of the base.
FINISH_LOW_Y_MM = KNIGHT_BASE_Y_MM - FINISH_BELOW_BASE_MM - HEAD_RADIUS_MM * math.tan(math.radians(FINISH_TILT_DEG))

if __name__ == "__main__":
    print(f"Knight {KNIGHT_HEIGHT_MM:.2f} tall, base dia {2 * KNIGHT_BASE_RADIUS_MM:.2f}")
    print(f"stock Y {STOCK_BOTTOM_Y_MM:.2f}..{STOCK_TOP_Y_MM:.2f}, overall {STOCK_TOP_Y_MM - STOCK_BOTTOM_Y_MM:.2f}")
    print(f"head {STOCK_TOP_Y_MM - SHOULDER_BOTTOM_Y_MM:.2f} long, base Y {KNIGHT_BASE_Y_MM:.2f}, Y travel left {64.77 - STOCK_TOP_Y_MM:.2f}")
