# Rook on the Haas UMC-350HD-EDU

Fusion helpers, a replay check and posted programs for a 73% chess Rook in 1215 steel, turned on a Haas ST-15 and then milled on a Haas UMC-350HD-EDU. It's the same scale, bar and vise as the [Knight](../haas_knight/README.md).

**Status: nothing here has cut metal.** Feeds and speeds are untested estimates, and holder sizes are estimates too. The toolpaths live in the Fusion document `Chess Rook 73pct Haas UMC-350HD-EDU`. `nc/` holds copies of what was posted from it, so the checks have something to run on.

Version 2 of the document was reported clean in Simulate. That check used catalog vise dimensions and estimated holders, so measure both before running the program. The per-side passes have since become circular patterns, which post the same moves, but Simulate hasn't been rerun on the patterned document.

## The part

Scaled from `Solid Of Castle` in the `Chess Set` document: 56.79 mm tall, 31.54 mm base. Everything below z 19.6 is round, and everything above is an octagon whose flats face +X, +Y and so on.

| Feature | Size | Who cuts it |
|---|---|---|
| Base, collar and neck | up to z 19.6 | ST-15 |
| Merlon tops | z 56.788 | ST-15 facing, final |
| Head flats | 18.14 across flats | T2 side, from the top |
| 3 steps under the head | 0.69-0.97 mm | T2 end-on |
| Side: slope, waist and lower flat | z 19.1 to 41.35 | T2 flank, one path per side |
| Pocket | 14.46 across flats, 5.48 deep, r 1.085 corners | T1 rough, T11 finish |
| 8 notches | 1.88 wide, 3.76 deep | T12 |

## Passes

The order is top to bottom, and the head's outside comes before the pocket and notches, so no merlon wall is cut from outside after its inside is gone.

1. `Semi Head`, `Flank Head`: one contour around the head at B0.
2. `Trace Steps x8`: B90, end-on to each side, with the top of the tool on each underside so the inside corners stay sharp.
3. `Rough Pocket`, `Semi Pocket Walls`, `Finish Pocket Floor`, `Finish Pocket Walls`: B0.
4. `Rough Notches`, `Finish Notch Walls`: B0.
5. `Semi Shaft x8`, `Flank Shaft x8`: B90, with the tool along the side's ruling and a spring pass on the flank.

**The `x8` stages are circular CAM patterns,** as on the [Queen](../haas_queen/README.md). Each is one pass at side 000, repeated around the part's Z axis. Changing a side's settings now means editing one pass, not eight. The pattern's angle is the step between instances, 45 deg. Set to 360 deg it would put all 8 on C 0 and cut one side 8 times, with no warning from Fusion.

Fusion's API can't create a pattern. So `Trace Steps x8` was made by hand in the `Add to New Pattern` dialog, and `replace_sides_with_patterns` in `rook_cam.py` copied it for the shaft stages. Posted with patterns, the program matched the version with 8 separate passes line for line, apart from 21 comments. Every instance is labelled with its side-000 name, such as `(Flank Shaft 000)`, so tell them apart by the C word that follows. On `Trace Steps` C is the side's angle. On the shaft passes it's the side's angle minus 90, because the tool runs along the side, so side 000 is C270.

## Tools

Lengths in mm. Total is gauge line to tip.

| Tool | Type | Flute | Stickout | Total | Holder | rpm | mm/min |
|---|---|---|---|---|---|---|---|
| T1 | 1/4 in 5-flute, 0.5 corner radius | 19.05 | 30 | 118.9 | 3.5 in | 7,600 | 1448 |
| T2 | 1/4 in flat, 4-flute | 25.4 | 32 | 133.6 | 4 in | 7,600 | 762 |
| T11 | 2 mm flat, 2-flute | 6 | 14 | 102.9 | 3.5 in | 10,000 | 200 |
| T12 | 1/16 in flat, 2-flute, 6.35 reach | 4.76 | 12.7 | 101.6 | 3.5 in | 10,000 | 120 |

T1 and T2 match the Knight's. T11 and T12 are new, and their dimensions are estimates until the real tools are chosen.

**T2 must have a sharp corner.** The steps' inside corners and the head flats come from its end and side. A corner radius would leave that radius in every step.

## Running the check

`check_faces.py` replays the posted program with a flat tool and reports gouges, retouching and leftover per face. It needs Python 3.9 or newer, with NumPy and SciPy, and takes a few minutes.

```bash
python3 -B check_faces.py nc/rook_mill.nc
```

Face numbers are the `index` values in `rook_faces.json`. The Knight's checks also work here, through `rook_job.py`.

The check reads the program, not the machine. It doesn't replace Simulate with Machine, and it doesn't model the holder or the vise.

## Files

| File | Purpose |
|---|---|
| `rook_cam.py` | Fusion helpers that built the milling passes and their patterns, with the Rook's dimensions. |
| `rook_job.py` | What the checks need to know about the part, tools and machine. |
| `check_faces.py` | Replay check for flat tools. |
| `rook_faces.json` | The Rook's 114 faces as meshes. |
| `nc/rook_mill.nc` | The milling program, program 2002, posted in G21. |
| `nc/rook_lathe.nc` | The lathe program, program 1002, posted in G20, which is what `haas_knight/check_lathe_nose.py` reads. |
