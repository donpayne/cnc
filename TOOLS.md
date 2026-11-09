# Tool sheet: 73% chess set, Haas ST-15 and UMC-350HD-EDU

Every tool the six pieces use, read from their Fusion documents: Pawn v7, Rook v5, Bishop v3, Knight v12, Queen v4 and King v26. The tool lists in the posted programs under each piece's `nc/` folder match.

**Nothing here is measured yet.** Holder envelopes are estimates, CT40 is assumed from Haas's "40 taper", T9 to T14 have estimated dimensions, and the lathe inserts are placeholders. Measure each tool at the machine and update its Fusion document, because the Z-travel and holder checks are only as good as these lengths.

## Mill: UMC-350HD-EDU

All are carbide with flood coolant. Feeds change from pass to pass and are in the programs.

### Loading

Set each tool to the stickout shown. Gauge length is tip to spindle gauge line: the holder's 88.9 or 101.6 plus the stickout.

| T | Tool | Collet | Holder | Stickout / gauge mm |
|---|---|---|---|---|
| 1 | 1/4 in bull nose, r 0.5 | 1/4 in | ER16 x 3.5 in | 30.0 / 118.9 |
| 2 | 1/4 in flat, flank and swarf | 1/4 in | **ER16 x 4 in** | 32.0 / 133.6 |
| 3 | 3/16 in ball, semi-finish | 3/16 in | ER16 x 3.5 in | 30.0 / 118.9 |
| 4 | 1/8 in ball, finish | 1/4 in | ER16 x 3.5 in | **31.1 / 120.0** |
| 5 | 3/32 in ball, detail | 1/4 in | ER16 x 3.5 in | 25.0 / 113.9 |
| 9 | 1/16 in ball, tightest detail | 1/8 in | ER16 x 3.5 in | 25.4 / 114.3 |
| 10 | 1/16 in ball, a fresh T9 | 1/8 in | ER16 x 3.5 in | 25.4 / 114.3 |
| 11 | 2 mm flat, pocket corners | 3 mm | ER16 x 3.5 in | 14.0 / 102.9 |
| 12 | 1/16 in flat, notches | 1/8 in | ER16 x 3.5 in | 12.7 / 101.6 |
| 13 | 2 mm flat, slit flanks | 1/8 in | **ER16 x 4 in** | 14.0 / 115.6 |
| 14 | 2 mm ball, flutes | 1/8 in | ER16 x 3.5 in | 20.0 / 108.9 |

**T4 must stick out 31.1 mm, 120 gauge, on every piece.** Shorter, and the King's `Octagon Strips` runs out of Z travel at B90. The King's document lists T4's overall length as 69.6 mm and the Knight's and Queen's as 63.5. That doesn't change the gauge length or the programs, but it's the same physical tool, so use the measured length in all three.

### Cutting

Reach is the relieved neck, or the shoulder where there's no neck. T10 is the same tool as T9, kept fresh for the last finish passes.

| T | Ø mm | Flutes | Flute / reach mm | rpm |
|---|---|---|---|---|
| 1 | 6.35 | 5 | 19.05 / 19.05 | 7600 |
| 2 | 6.35 | 4 | 25.4 / 32.0 | 7600 |
| 3 | 4.763 | 4 | 15.875 / 30.0 | 8000 |
| 4 | 3.175 | 2 | 9.525 / 25.0 | 10000 |
| 5 | 2.381 | 2 | 7.14 / 25.0 | 10000 |
| 9 | 1.588 | 2 | 4.76 / 19.05 | 10000 |
| 10 | 1.588 | 2 | 4.76 / 19.05 | 10000 |
| 11 | 2.0 | 2 | 6.0 / 6.0 | 10000 |
| 12 | 1.588 | 2 | 4.76 / 6.35 | 10000 |
| 13 | 2.0 | 2 | 8.0 / 14.0 | 10000 |
| 14 | 2.0 | 2 | 3.0 / 10.0 | 10000 |

## Lathe: ST-15

All are carbide with flood coolant on 20 x 20 mm shanks, and are called as `T606`, `T707` and so on, with the offset matching the tool. They run at constant surface speed (`G96`), with each pass clamped at 2000 to 4000 rpm by `G50`. T6, T7 and T8 are used on every piece, and T5 only on the Queen.

| T | Insert | Nose r mm | Hand | m/min |
|---|---|---|---|---|
| 5 | 0.8 mm full-radius groove | 0.4 | R | 100 |
| 6 | CNMG 80°, face and rough | 0.8 | R | 150 |
| 7 | VNMG 35°, finish profile | 0.4 | Neutral | 150 |
| 8 | 3 mm OD groove, necks | 0.2 | R | 100 to 150 |

T6 is in an L-type holder, T7 in a V-type, and T5 and T8 in external grooving holders. T7's holder is 20 mm wide and centred on its tip, so it reaches about 10 mm past the tip toward the chuck and the head. Several pieces' lathe passes are ordered around it, so keep T7 in that holder size or recheck them.

## By piece

| Piece | Lathe | Lathe tools | Mill | Mill tools |
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
