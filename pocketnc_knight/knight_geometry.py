"""Dimensions for the chess Knight: no Fusion imports, so plain Python checks can share them.

World frame matches the Pocket NC at A0 B0: +Y runs up the part axis from the B table, +Z points at
the spindle, and the origin sits where the part axis meets the A axis. All lengths are millimetres.
"""
# Y travel stops 64.77 mm from the A axis and the tool works side-on at A0, so the part's top must
# stay under that. The full-size Knight is 82.8 mm tall and would end near 89 mm.
KNIGHT_SCALE = 0.65
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
# Grips 30 mm of the 44.5 mm collet, meeting the two-thirds rule. The collet's top is 0.11 mm below
# the nut's, so 17 mm of the stump stands out above the collet.
STUMP_LENGTH_MM = 47.0
# 1.125 in. Clears the 14.04 mm Knight base by 0.25 mm, which is enough only because the head and
# stump are turned in one lathe setup. 1.25 in meant 39% more wax to rough out.
HEAD_RADIUS_MM = 14.2875
# Puts the shoulder where nc/knight.ngc was programmed. A shoulder 2 mm above the nut would bring the
# holder level with the B table's top on the lowest passes, leaving no clearance.
SHOULDER_ABOVE_NUT_MM = 16.9
SHOULDER_BOTTOM_Y_MM = NUT_TOP_Y_MM + SHOULDER_ABOVE_NUT_MM
SHOULDER_THICKNESS_MM = 2.0  # The wax disc left above the stump after cutting.
# Undercuts the 14 mm base by only 3 mm. A 6 mm neck made the tool reach 9.9 mm in from the shoulder's
# rim, past its 9.5 mm flutes, so the smooth shank rubbed the shoulder. Sawn through at the end.
NECK_RADIUS_MM = 11.0
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

# Tool directions as azimuth about the part axis, measured from +Z, all at A0. A tool at right angles
# to the part axis sees every surface of this shape, including the snout's overhang, and A0
# keeps tip Z well below its limit. Tilting toward A90 would run out of Z travel at the top.
# Cut in this order: the user wants sides 90 and 270 done before 0 and 180, for how the part looks.
SIDE_AZIMUTHS_DEG = (90, 270, 0, 180)

if __name__ == "__main__":
    print(f"Knight {KNIGHT_HEIGHT_MM:.2f} tall, base dia {2 * KNIGHT_BASE_RADIUS_MM:.2f}")
    print(f"stock Y {STOCK_BOTTOM_Y_MM:.2f}..{STOCK_TOP_Y_MM:.2f}, overall {STOCK_TOP_Y_MM - STOCK_BOTTOM_Y_MM:.2f}")
    print(f"head {STOCK_TOP_Y_MM - SHOULDER_BOTTOM_Y_MM:.2f} long, base Y {KNIGHT_BASE_Y_MM:.2f}, Y travel left {64.77 - STOCK_TOP_Y_MM:.2f}")
