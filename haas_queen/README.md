# Queen on the Haas UMC-350HD-EDU

Checks and posted programs for a 73% chess Queen in 1215 steel, turned on a Haas ST-15 and then milled on a Haas UMC-350HD-EDU. It's the same scale, vise and steel as the [Bishop](../haas_bishop/README.md), [Rook](../haas_rook/README.md) and [Knight](../haas_knight/README.md), but on larger bar, because its 35.96 mm base doesn't fit 1-1/4 in.

**Status: nothing here has cut metal.** Simulate in Fusion was reported good on these programs, but it hasn't been confirmed that this was Simulate with Machine. Feeds and speeds are untested estimates, and tool and holder sizes are estimates too. The toolpaths live in the Fusion document `Chess Queen 73pct Haas UMC-350HD-EDU`, in the project of the same piece. `nc/` holds copies of what was posted from it, and the `queen_*_cam.py` scripts record how the passes were built.

## The part

Scaled from `Solid Of Queen Piece` in the `Chess Set` document: 81.003 mm tall, r 17.98 at the base, 442 faces. It's round everywhere except for 8-fold features centered on C 0, 45 and so on.

| Feature | Size | Who cuts it |
|---|---|---|
| All revolved faces | z -5 to 81.003 | ST-15 |
| Finial's neck | Model r 0.96 at its narrowest | ST-15, T5, leaving at most 0.11 mm |
| 8 scoops | Cylinders r 4.44, axis 60 deg from the part axis | UMC, T3 then T4 |
| Scoop rims, inner ends and crests | Convex blends, crests at C 22.5 and so on | UMC, T4 and T10 |
| 8 crown flutes | z 64.33 to 73.165, r 1.136 with a 0.046 flat | UMC, T14 |
| 8 stem flutes | z 25.88 to 49.39, same section | UMC, T14 |

**The neck stays a little thicker than the model.** T5's r 0.4 nose can't fill the neck's r 0.30 fillet, so it leaves up to 0.11 mm per side, at z 78.24 to 78.74. T7 and T8 can't get in: T7's lower edge hits the crown's flat top, and T8 is 3 mm wide.

## Lathe

Program 1004, about 15.9 min. The blank is 1-1/2 in bar, 120 mm long, with a 30 mm grip. Jaws must be bored for 38.1 mm on both machines. Cutting stops at the neck bottom, z -5.

The target is the mill's stock, so it isn't the model everywhere. Above z 75.69 it's an envelope over the crests.

1. `Face top`
2. `Rough head` (T6), `Rough head detail` (T7), `Finish head` (T7)
3. `Groove crown cone` (T8), `Rough finial neck` (T5), `Finish finial neck` (T5), `Groove under flange` (T8)
4. `Rough body` (T6), `Rough waist` (T7)
5. `Rough neck groove` (T8), `Groove under collar` (T8)
6. `Finish body` (T7), `Groove neck` (T8)

T6, T7 and T8 are the placeholder inserts from the Knight: CNMG r 0.8, VNMG 35 deg r 0.4, and a 3 mm groove r 0.2. Part-off and the base's underside have no pass yet.

**T5 is a placeholder too:** 0.8 mm wide, full radius r 0.4, modeled with 10.5 mm of depth so its holder clears the crown's rim at r 10.1. A real insert needs that reach, or a holder whose head sits above z 78. It runs at 0.02 mm/rev, up to 4,000 rpm, which is only about 27 m/min at the neck, so expect a poorer finish there than elsewhere.

**After this the finial hangs on a neck about 2.1 mm thick,** and G54 on the mill is the finial's tip. Touch off gently, or from another surface with a known offset.

`Groove under flange` has no lead-out, because any lead-out there runs toward the lower flange and Fusion warned that it had to bend it. It retracts straight out in X, which is clear of both flanges.

Stock left by the replay:

| Where | Left | Why |
|---|---|---|
| z -5 to -4.92 | 0.200 mm | T8's corner at the neck bottom, which comes off with the stub |
| z 25.12 to 25.24 | 0.040 mm | A small step in the profile, at r 8.9 to 9.1 |
| z 60.70 to 61.06 | 0.080 mm | Small steps in the profile, at r 5.8 to 6.5 |
| z 78.24 to 78.74 | 0.108 mm | The finial's neck, where T5's nose can't fill the fillet |
| z 80.90 to 80.98 | 0.210 mm | A small nib at the finial's tip |

**Readings the other way:**
- **z 77.54 to 77.98, -0.323 mm: not real.** `check_lathe.py` keeps one radius per z row, so it can't represent the envelope's small notch at r 4.59 to 4.70. `check_grooves.py` has no rows, and it reads 0 for `Groove crown cone`.
- **Everything else, 0.019 mm or less along the surface normal.** The largest is at z 23.40 to 23.50, and z 35.24 to 37.08 reads 0.016 mm on a nearly straight face. These are close to the check's 0.02 mm grid, so they may be noise, but the check can't prove that.

## Mill

Program 2004, about 63 min. Jergens 130 mm vise, aluminum soft jaws, no riser, 30 mm grip on the stub. G54 is the finial's tip, model z 81.003, and the stock is the `Lathe Target` body. Passes run far from the vise first.

| Stage | Tool | Pose | Settings | Min, all passes |
|---|---|---|---|---|
| `Rough Scoop` x 8 | T3 | B60 | Straight strokes in 4 layers, leaves 0.2 | 5.5 |
| `Finish Scoop` x 8 | T4 | B60 | Straight strokes, stepover 0.15 | 6.9 |
| `Finish Rim` x 8 | T4 | B75 | Scallop, stepover 0.15 | 6.4 |
| `Detail Inner` x 8 | T10 | B60 | Scallop, stepover 0.08 | 4.7 |
| `Detail Crest` x 8 | T10 | B60, C 22.5 and so on | Scallop, stepover 0.08 | 15.2 |
| `Trace Crown Flute` x 8 | T14 | B90 | 3 rough, 5 finish cuts | 8.1 |
| `Trace Stem Upper` x 8 | T14 | B95 | Same | 9.1 |
| `Trace Stem Lower` x 8 | T14 | B90 | Same | 7.0 |

Every pass is at a fixed tilt, so the program needs no TCPC.

**Scoops and flutes are computed paths.** A ball inside a scoop's r 4.44 cylinder can't touch the finished part, so `queen_scoops.py` draws straight strokes with no surface check. `queen_flutes.py` does the same for the channels, checked against the model's exact cylinders to 0.0003 mm. Scallops need all other faces avoided, or they machine the whole part.

**Repeats are circular CAM patterns.** Each `x 8` stage is one pass at C 0 (C 22.5 for the crest) in a pattern around the part's Z axis, so a full rebuild of the mill setup is 8 generations, about 15 s. The pattern's angle is the step between instances, 45 deg. Set to 360 deg it puts all 8 at C 0, which cuts one feature 8 times with no warning from Fusion. Fusion's API can't create a pattern, so the first is made by hand in the `Add to New Pattern` dialog, and `pattern_around_c` copies it for the rest.

**`Trace Stem Upper` tilts to B95.** The floor is nearly parallel to the part's axis, so B90 would cut on the ball's tip, where surface speed is 0. B95 cuts 5 to 10 deg off the tip, at 5 m/min or more. B75 ran T14's neck 48 um into the top of the flute's run-out, and B105 drops the holder's flange 13.5 mm into the jaws at C 45, 135, 225 and 315.

C climbs across the program, to 2,835 deg on the last flute, because the post doesn't reset it between passes. It only sends C home at the very end, with `G28 G91 C0`. Confirm the control accepts that.

## Tools

Mill tools. Lengths in mm. Total is gauge line to tip.

| Tool | Type | Total | rpm | mm/min |
|---|---|---|---|---|
| T3 | 3/16 in ball | 118.9 | 8,000 | 400 |
| T4 | 1/8 in ball, 6.35 shank from 25 up | 113.9 | 10,000 | 305 |
| T10 | 1/16 in ball, 2-flute, relieved neck to 19.05 | 114.3 | 10,000 | 120 |
| T14 | 2 mm ball, relieved neck to 10, 3.175 shank | 108.9 | 10,000 | 150 |

T14 is new, so all of its numbers are estimates until a real tool is chosen. All four should be measured, because the Z and holder margins below depend on these lengths.

## What the checks found

On the posted programs:

- **No gouges on any of the 64 mill passes, links included.** The deepest any tool came into the model is 16 um, on the flutes, where readings include the mesh's chord error.
- **Every milled face is covered.** All non-revolved faces read at least 86% touched, with at most 17 um left on the samples that weren't. The rest are at those faces' edges.
- **T5's and T8's grooves stay out of the target.** `Groove crown cone`, `Rough finial neck` and `Finish finial neck` read 0, and `Groove under flange` 0.003 mm. T5 gets to r 1.056, against the model's 0.96.
- **Z margin at B90:** T14 4.07 mm. Passes at other tilts aren't measured by this check, and tilted poses lift the work origin well above the pivot.

- **The holder clears the vise by 3.07 mm at the closest,** at C 45, 135, 225 and 315 on `Trace Stem Upper` and `Trace Stem Lower`. Other C angles clear by 18 mm or more. The holder never reaches the part's height, and the shank clears the part's envelope by 1.13 mm. The holder is estimated, so measure it and rerun this before cutting.

These read the program, not the machine. **The lathe checks don't model the inserts' flank clearance or the holders, and none of this replaces Simulate with Machine.**

## Running the checks

They need Python 3.9 or newer, with NumPy and SciPy, and they reuse code in `../haas_bishop` and `../haas_knight`.

```bash
python3 -B check_lathe.py nc/queen_lathe.nc
```

```bash
python3 -B check_grooves.py nc/queen_lathe.nc
```

```bash
python3 -B check_faces.py nc/queen_mill.nc
```

```bash
python3 -B check_holder.py nc/queen_mill.nc
```

The lathe checks take seconds, and `check_holder.py` takes a few minutes. `check_faces.py` takes about 6 minutes, and it takes pass name starts to limit it, such as `Finish Scoop`.

To check Z travel, run the Knight's check through this job file, from the repo root:

```bash
python3 -B -c "import sys; sys.path[:0] = ['haas_queen', 'haas_knight']; import queen_job; sys.modules['knight_job'] = queen_job; sys.argv = ['', 'haas_queen/nc/queen_mill.nc']; import check_z_travel; check_z_travel.main()"
```

## Files

| File | Purpose |
|---|---|
| `queen_job.py` | What the checks need to know about the part, tools and machine. |
| `queen_flutes.py` | Ball-center paths for the flutes. Plain Python. |
| `queen_scoops.py` | Ball-center strokes for the scoops. Plain Python. |
| `queen_mill_cam.py` | Fusion helpers that build the mill passes. |
| `queen_lathe_cam.py` | Fusion helpers that copy the lathe passes from the Bishop's document. |
| `check_faces.py` | Replay check for the mill program. |
| `check_lathe.py` | Replay check for the lathe program, using the Bishop's. |
| `check_grooves.py` | True 2D check of T5's and T8's grooves near the crown. |
| `check_holder.py` | Replay of the mill program with the holder and shank, against the vise and the part. |
| `queen_faces.json` | The Queen's 442 faces as meshes. |
| `queen_lathe_profile.json` | The lathe target's faces as (r, z) nodes. |
| `nc/queen_mill.nc` | The milling program, program 2004, posted in G21. |
| `nc/queen_lathe.nc` | The lathe program, program 1004, posted in G21. |
