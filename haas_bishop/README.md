# Bishop on the Haas UMC-350HD-EDU

Checks and posted programs for a 73% chess Bishop in 1215 steel, turned on a Haas ST-15 and then milled on a Haas UMC-350HD-EDU. It's the same scale, bar and vise as the [Rook](../haas_rook/README.md) and [Knight](../haas_knight/README.md).

**Status: nothing here has cut metal.** Feeds and speeds are untested estimates, and tool and holder sizes are estimates too. The toolpaths live in the Fusion document `Chess Bishop 73pct Haas UMC-350HD-EDU`. `nc/` holds copies of what was posted from it, so the checks have something to run on.

## The part

Scaled from `Solid Of Bishop` in the `Chess Set` document: 72.91 mm tall, 31.54 mm base, 15,095 mm3. The narrowest point is the waist, r 4.25 at about z 41.8.

| Feature | Size | Who cuts it |
|---|---|---|
| All revolved faces | z -5 to 72.91 | ST-15 |
| Slit floor, face 35 | r 1.159, lowest point about z 58.26 | UMC, T13 |
| Slit walls, faces 38 and 39 | 2.318 apart, tilted 30.3 deg, up to 7 mm deep | UMC, T13 |

## Lathe

Program 1003, about 8.6 min. The blank is 1-1/4 in bar, 112 mm long, with a 30 mm grip, so 82 mm stands out of the jaws. The top face takes 0.54 mm, and cutting stops at the neck bottom, 3.5 mm above the jaws.

The head is finished before the waist is cut, so the far end is done while the part is stiffest.

1. `Face top`
2. `Rough head` (T6), `Rough head detail` (T7), `Finish head` (T7)
3. `Rough body` (T6), `Rough waist` (T7)
4. `Rough neck groove` (T8), `Groove under collar` (T8)
5. `Finish body` (T7), `Groove neck` (T8)

T6, T7 and T8 are the placeholder inserts from the Knight: CNMG r 0.8, VNMG 35 deg r 0.4, and a 3 mm groove r 0.2. Part-off and the base's underside have no pass yet.

Stock left by the replay, because these inserts can't reach:

| Where | Left | Why |
|---|---|---|
| z -5 to -4.92 | 0.200 mm | T8's corner at the neck bottom, which comes off with the stub |
| z 45.72 to 45.78 | 0.109 mm | T8's r 0.2 corner on the 0.195 mm wide shoulder under the collar |
| z 72.88 to 72.90 | 0.109 mm | A small nib at the finial's tip |
| z 5.76 to 6.02, 51.46 to 51.64, 54.20 to 54.36 | 0.040 to 0.047 mm | Small fillets |

The deepest reading the other way is 0.016 mm, at z 49.62 to 50.00 and z 50.24 to 50.32. That's smaller than the check's 0.02 mm grid, so it may be noise, but the check can't prove that.

## Mill

Program 2003, about 20 min. Jergens 130 mm vise, aluminum soft jaws, no riser, 30 mm grip on the stub. G54 is the finial's tip, model z 72.9111, and the stock is the `Lathe Target` body.

| Pass | Tool | Pose | Settings | Min |
|---|---|---|---|---|
| `Rough Slit Center` | T9 | B30.299 C0 | Slot on the slit's centre, 0.1 stepdown | 9.09 |
| `Rough Slit Side A`, `Side B` | T9 | B30.299 C0 | Offset 0.315 each way, 0.2 stepdown | 4.55 each |
| `Flank Slit +Y` | T13 | B90 C90 | 0.5 past the axis, spring pass | 0.95 |
| `Flank Slit -Y` | T13 | B90 C-90 | 0.5 past the axis, spring pass | 0.95 |

An Adaptive rough came out at 127 min and 22 m of cutting in this narrow slot, so straight slot passes replaced it.

The roughs leave 0.05 mm on the walls by geometry, and the replay's closest reading on any slit face is 0.026 mm, near the floor.

Both flanks run 0.5 mm past the axis, so they both cut a band about 1 mm wide across the middle of the floor and walls. That overlap comes with flanking from both sides, and it may leave a witness line. The replay doesn't measure that.

The two flanks use opposite chain directions, since they view the slit from opposite ends. With the same direction, one of them ran outside the slit and would have cut the part. Read the arc radius in the posted code: it's 0.159 mm when the tool is inside the U and 2.159 mm when it's outside.

## Tools

Lengths in mm. Total is gauge line to tip.

| Tool | Type | Flute | Stickout | Total | Holder | rpm | mm/min |
|---|---|---|---|---|---|---|---|
| T9 | 1/16 in ball, 2-flute, relieved neck to 19.05 | 4.76 | 25.4 | 114.3 | 3.5 in | 10,000 | 180 |
| T13 | 2 mm flat, 2-flute | 8 | 14 | 115.6 | 4 in | 10,000 | 150 |

T13 is new, so all of its numbers are estimates until a real tool is chosen. It needs 8 mm of flute to span the wall from 0.5 past the axis out to y 7.31, and at least 110.09 total length to reach at B90, which leaves 5.51 mm of Z margin as modeled.

The program has no G41 or G42, so any error in T13's diameter goes straight into the slit's width. Measure the real tool.

## Running the checks

They need Python 3.9 or newer, with NumPy and SciPy.

```bash
python3 -B check_slit.py nc/bishop_mill.nc
```

```bash
python3 -B check_lathe.py nc/bishop_lathe.nc
```

`check_slit.py` takes about a minute. It replays both tools with their full shape, neck and shank included, and reports gouges and how much of each slit face the flanks finish. On the posted program it found no gouges, and the flanks finish all three faces.

`check_lathe.py` takes seconds. It reads metric programs, because this ST-15 post comes out in G21, where the Rook's came out in G20. It doesn't model the inserts' flank clearance or the holders.

To check Z travel, run the Knight's check through this job file, from the repo root:

```bash
python3 -B -c "import sys; sys.path[:0] = ['haas_bishop', 'haas_knight']; import bishop_job; sys.modules['knight_job'] = bishop_job; sys.argv = ['', 'haas_bishop/nc/bishop_mill.nc']; import check_z_travel; check_z_travel.main()"
```

These read the program, not the machine. They don't replace Simulate with Machine, and they don't model the holders or the vise.

## Files

| File | Purpose |
|---|---|
| `bishop_job.py` | What the checks need to know about the part, tools and machine. |
| `check_slit.py` | Replay check for the mill's slit passes. |
| `check_lathe.py` | Replay check for the metric lathe program. |
| `bishop_faces.json` | The Bishop's 42 faces as meshes. |
| `bishop_profile.json` | The revolved faces as (r, z) nodes, finer than the meshes, for the lathe check. |
| `nc/bishop_mill.nc` | The milling program, program 2003, posted in G21. |
| `nc/bishop_lathe.nc` | The lathe program, program 1003, posted in G21. |
