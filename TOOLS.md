# Tool sheet: 73% chess set, Haas ST-15 and UMC-350HD-EDU

Every tool the six pieces use, read from their Fusion documents on 2026-11-07: Pawn v7, Rook v5, Bishop v3, Knight v12, Queen v4 and King v25. The tool lists in the posted programs under each piece's `nc/` folder match.

**Nothing here is measured yet.** Holder envelopes are estimates, CT40 is assumed from Haas's "40 taper", T9 to T14 have estimated dimensions, and the lathe inserts are placeholders. Measure each tool at the machine and update its Fusion document, because the Z-travel and holder checks are only as good as these lengths.

## Mill: UMC-350HD-EDU

Set each tool to the stickout shown. Gauge length is tip to spindle gauge line: the holder's 88.9 or 101.6 plus the stickout. Feeds change from pass to pass and are in the programs.

| T | Tool | Ø mm | Flutes | Flute / reach mm | Collet | Stickout mm | Holder | Gauge mm | rpm | Passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Bull nose, r 0.5, AlTiN | 6.35 | 5 | 19.05 / 19.05 | 1/4 in | 30.0 | ER16 x 3.5 in | 118.9 | 7600 | Knight 16, Rook 1 |
| 2 | Flat, AlTiN, flank and swarf | 6.35 | 4 | 25.4 / 32.0 | 1/4 in | 32.0 | **ER16 x 4 in** | 133.6 | 7600 | Knight 4, Rook 5, King 4 |
| 3 | Ball, AlTiN, semi-finish | 4.763 | 4 | 15.875 / 30.0 | 3/16 in | 30.0 | ER16 x 3.5 in | 118.9 | 8000 | Knight 8, Queen 1 |
| 4 | Ball, AlTiN, relieved neck, finish | 3.175 | 2 | 9.525 / 25.0 | 1/4 in | **31.1** | ER16 x 3.5 in | **120.0** | 10000 | Knight 8, Queen 2, King 10 |
| 5 | Ball, AlTiN, relieved neck, detail | 2.381 | 2 | 7.14 / 25.0 | 1/4 in | 25.0 | ER16 x 3.5 in | 113.9 | 10000 | Knight 2 |
| 9 | Ball, AlTiN, relieved neck, tightest detail | 1.588 | 2 | 4.76 / 19.05 | 1/8 in | 25.4 | ER16 x 3.5 in | 114.3 | 10000 | Knight 5, Bishop 3 |
| 10 | Same tool as T9, kept fresh for last finish passes | 1.588 | 2 | 4.76 / 19.05 | 1/8 in | 25.4 | ER16 x 3.5 in | 114.3 | 10000 | Knight 2, Queen 2, King 1 |
| 11 | Flat, AlTiN, pocket corners and walls | 2.0 | 2 | 6.0 / 6.0 | 3 mm | 14.0 | ER16 x 3.5 in | 102.9 | 10000 | Rook 3, King 2 |
| 12 | Flat, AlTiN, notches | 1.588 | 2 | 4.76 / 6.35 | 1/8 in | 12.7 | ER16 x 3.5 in | 101.6 | 10000 | Rook 2 |
| 13 | Flat, AlTiN, slit flanks | 2.0 | 2 | 8.0 / 14.0 | 1/8 in | 14.0 | **ER16 x 4 in** | 115.6 | 10000 | Bishop 2 |
| 14 | Ball, relieved neck, flutes | 2.0 | 2 | 3.0 / 10.0 | 1/8 in | 20.0 | ER16 x 3.5 in | 108.9 | 10000 | Queen 4, King 3 |

All are carbide with flood coolant. Reach is the relieved neck, or the shoulder where there's no neck.

**T4 must stick out 31.1 mm, 120 gauge, on every piece.** Shorter, and the King's `Octagon Strips` runs out of Z travel at B90. The King's document lists T4's overall length as 69.6 mm and the Knight's and Queen's as 63.5. That doesn't change the gauge length or the programs, but it's the same physical tool, so use the measured length in all three.

## Lathe: ST-15

All are carbide with flood coolant, and are called as `T606`, `T707` and so on, with the offset matching the tool. They run at constant surface speed (`G96`), with each pass clamped at 2000 to 4000 rpm by `G50`.

| T | Insert | Nose r mm | Hand | Holder | Speed m/min | Passes |
|---|---|---|---|---|---|---|
| 5 | 0.8 mm full-radius grooving | 0.4 | R | 20 x 20 external grooving | 100 | Queen 2 |
| 6 | CNMG 80°, face and rough | 0.8 | R | 20 x 20, L type | 150 | every piece: Pawn 3, Rook 2, Bishop 3, Knight 2, Queen 3, King 3 |
| 7 | VNMG 35°, finish profile | 0.4 | Neutral | 20 x 20, V type, centred on its tip | 150 | every piece: Pawn 4, Rook 2, Bishop 4, Knight 4, Queen 4, King 2 |
| 8 | 3 mm OD grooving, necks | 0.2 | R | 20 x 20 external grooving | 100 to 150 | every piece: Pawn 4, Rook 2, Bishop 3, Knight 2, Queen 5, King 5 |

T7's holder is 20 mm wide and centred on its tip, so it reaches about 10 mm past the tip toward the chuck and the head. Several pieces' lathe passes are ordered around it, so keep T7 in that holder size or recheck them.

## By piece

| Piece | Lathe program | Lathe tools | Mill program | Mill tools |
|---|---|---|---|---|
| Pawn | O01006 | 6, 7, 8 | none | none |
| Rook | O01002 | 6, 7, 8 | O02002 | 1, 2, 11, 12 |
| Bishop | O01003 | 6, 7, 8 | O02003 | 9, 13 |
| Knight | O01001 | 6, 7, 8 | O02001 | 1, 2, 3, 4, 5, 9, 10 |
| Queen | O01004 | **5**, 6, 7, 8 | O02004 | 3, 4, 10, 14 |
| King | O01005 | 6, 7, 8 | **O01001** | 2, 4, 10, 11, 14 |

The whole set needs 11 tools in the mill's carousel (T1 to T5 and T9 to T14) and 4 on the lathe turret (T5 to T8).

## Watch for

- **T5 means two different tools.** On the mill it's the Knight's 3/32 in ball; on the lathe it's the Queen's 0.8 mm grooving insert. The machines have separate tool tables, so the programs are right, but don't load by number alone.
- **The King's mill program is O01001,** where the other mill programs are O02001 to O02004. The UMC has no other O01001, but the Knight's lathe program on the ST-15 does, so check which file you're loading.
- **Two holder lengths.** T2 and T13 are in 4 in holders and the rest in 3.5 in. The Z-travel checks used those lengths.
