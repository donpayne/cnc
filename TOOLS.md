# Tool sheet: 73% chess set, Haas ST-15 and UMC-350HD-EDU

Every tool the six pieces use, read from their Fusion documents: Pawn v7, Rook v5, Bishop v3, Knight v12, Queen v4 and King v26. The tool lists in the posted programs under each piece's `nc/` folder match.

For printing, `TOOLS.pdf` is this sheet on landscape letter pages. Rebuild it with `tools_pdf.py` after any edit.

**Nothing here is measured yet.** Holder envelopes are estimates, CT40 is assumed from Haas's "40 taper", T9 to T14 have estimated dimensions, and the lathe inserts are placeholders. Measure each tool at the machine and update its Fusion document, because the Z-travel and holder checks are only as good as these lengths.

## Mill: UMC-350HD-EDU

All are carbide with flood coolant. Feeds change from pass to pass and are in the programs.

### Endmills to order

Lengths are in mm, with the inch size for inch tools. Order two of the 1/16 in ball: T9 and T10 are the same tool. Only the Knight uses both: T9 does its long detail passes, and a fresh T10 its last finish passes on the chin and lower mane. The Bishop uses only T9, and the Queen and King only T10. All but the 2 mm ball are AlTiN coated in the documents.

Neck is how far the relieved neck reaches from the tip. Fusion models each neck at the cutting diameter, so buy necks at or just under it; the 2 mm ball's is 1.9 mm. T9 to T14 are estimates of catalog tools, so match them to what you can buy and update the documents.

| T     | Type             | Cut Ø           | Flutes | Flute length   | Neck           | Shank Ø         | Overall length  |
| ----- | ---------------- | --------------- | ------ | -------------- | -------------- | --------------- | --------------- |
| 2     | Flat             | 6.35 (1/4 in)   | 4      | 25.4 (1 in)    | none           | 6.35 (1/4 in)   | 76.2 (3 in)     |
| 11    | Flat             | 2.0             | 2      | 6.0            | none           | 3.0             | 38.0            |
| 13    | Flat             | 2.0             | 2      | 8.0            | 14.0           | 3.175 (1/8 in)  | 50.0            |
| 12    | Flat             | 1.588 (1/16 in) | 2      | 4.76 (3/16 in) | 6.35 (1/4 in)  | 3.175 (1/8 in)  | 38.1 (1-1/2 in) |
| 1     | Bull nose, r 0.5 | 6.35 (1/4 in)   | 5      | 19.05 (3/4 in) | none           | 6.35 (1/4 in)   | 63.5 (2-1/2 in) |
| 3     | Ball             | 4.763 (3/16 in) | 4      | 15.88 (5/8 in) | none           | 4.763 (3/16 in) | 63.5 (2-1/2 in) |
| 4     | Ball             | 3.175 (1/8 in)  | 2      | 9.53 (3/8 in)  | 25.0 (0.98 in) | 6.35 (1/4 in)   | 63.5 (2-1/2 in) |
| 5     | Ball             | 2.381 (3/32 in) | 2      | 7.14 (9/32 in) | 25.0 (0.98 in) | 6.35 (1/4 in)   | 63.5 (2-1/2 in) |
| 14    | Ball             | 2.0             | 2      | 3.0            | 10.0           | 3.175 (1/8 in)  | 50.0            |
| 9, 10 | Ball             | 1.588 (1/16 in) | 2      | 4.76 (3/16 in) | 19.05 (3/4 in) | 3.175 (1/8 in)  | 63.5 (2-1/2 in) |

The King's document lists T4's overall length as 69.6 mm and the Knight's and Queen's as 63.5. It's the same tool, and the programs don't depend on it, so buy the 63.5 (2-1/2 in) one and update the King's document to match.

### Tool holders

Set each tool to the stickout shown. Gauge length is tip to spindle gauge line: the holder's 88.9 or 101.6 plus the stickout.

| T   | Endmill                       | Collet  | Holder          | Stickout / gauge mm | rpm   |
| --- | ----------------------------- | ------- | --------------- | ------------------- | ----- |
| 1   | 1/4 in bull nose, r 0.5       | 1/4 in  | ER16 x 3.5 in   | 30.0 / 118.9        | 7600  |
| 2   | 1/4 in flat, flank and swarf  | 1/4 in  | **ER16 x 4 in** | 32.0 / 133.6        | 7600  |
| 3   | 3/16 in ball, semi-finish     | 3/16 in | ER16 x 3.5 in   | 30.0 / 118.9        | 8000  |
| 4   | 1/8 in ball, finish           | 1/4 in  | ER16 x 3.5 in   | **31.1 / 120.0**    | 10000 |
| 5   | 3/32 in ball, detail          | 1/4 in  | ER16 x 3.5 in   | 25.0 / 113.9        | 10000 |
| 9   | 1/16 in ball, tightest detail | 1/8 in  | ER16 x 3.5 in   | 25.4 / 114.3        | 10000 |
| 10  | 1/16 in ball, a fresh T9      | 1/8 in  | ER16 x 3.5 in   | 25.4 / 114.3        | 10000 |
| 11  | 2 mm flat, pocket corners     | 3 mm    | ER16 x 3.5 in   | 14.0 / 102.9        | 10000 |
| 12  | 1/16 in flat, notches         | 1/8 in  | ER16 x 3.5 in   | 12.7 / 101.6        | 10000 |
| 13  | 2 mm flat, slit flanks        | 1/8 in  | **ER16 x 4 in** | 14.0 / 115.6        | 10000 |
| 14  | 2 mm ball, flutes             | 1/8 in  | ER16 x 3.5 in   | 20.0 / 108.9        | 10000 |

**T4 must stick out 31.1 mm, 120 gauge, on every piece.** Shorter, and the King's `Octagon Strips` runs out of Z travel at B90.

## Lathe: ST-15

All are carbide with flood coolant on 20 x 20 mm shanks, and are called as `T606`, `T707` and so on, with the offset matching the tool. They run at constant surface speed (`G96`), with each pass clamped at 2000 to 4000 rpm by `G50`. T6, T7 and T8 are used on every piece, and T5 only on the Queen.

| T   | Insert                    | Nose r mm | Hand    | m/min      |
| --- | ------------------------- | --------- | ------- | ---------- |
| 5   | 0.8 mm full-radius groove | 0.4       | R       | 100        |
| 6   | CNMG 80°, face and rough  | 0.8       | R       | 150        |
| 7   | VNMG 35°, finish profile  | 0.4       | Neutral | 150        |
| 8   | 3 mm OD groove, necks     | 0.2       | R       | 100 to 150 |

T6 is in an L-type holder, T7 in a V-type, and T5 and T8 in external grooving holders. T7's holder is 20 mm wide and centred on its tip, so it reaches about 10 mm past the tip toward the chuck and the head. Several pieces' lathe passes are ordered around it, so keep T7 in that holder size or recheck them.

## By piece

| Piece  | Lathe  | Lathe tools    | Mill       | Mill tools           |
| ------ | ------ | -------------- | ---------- | -------------------- |
| Pawn   | O01006 | 6, 7, 8        | none       | none                 |
| Rook   | O01002 | 6, 7, 8        | O02002     | 1, 2, 11, 12         |
| Bishop | O01003 | 6, 7, 8        | O02003     | 9, 13                |
| Knight | O01001 | 6, 7, 8        | O02001     | 1, 2, 3, 4, 5, 9, 10 |
| Queen  | O01004 | **5**, 6, 7, 8 | O02004     | 3, 4, 10, 14         |
| King   | O01005 | 6, 7, 8        | **O01001** | 2, 4, 10, 11, 14     |

The whole set needs 11 tools in the mill's carousel (T1 to T5 and T9 to T14) and 4 on the lathe turret (T5 to T8).

## Watch for

- **T5 means two different tools.** On the mill it's the Knight's 3/32 in ball; on the lathe it's the Queen's 0.8 mm grooving insert. The machines have separate tool tables, so the programs are right, but don't load by number alone.
- **The King's mill program is O01001,** where the other mill programs are O02001 to O02004. The UMC has no other O01001, but the Knight's lathe program on the ST-15 does, so check which file you're loading.
- **Two holder lengths.** T2 and T13 are in 4 in holders and the rest in 3.5 in. The Z-travel checks used those lengths.
