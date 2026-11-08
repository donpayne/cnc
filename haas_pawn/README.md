# Pawn on the Haas ST-15

The posted program and its check for a 73% chess Pawn in 1215 steel. It uses the same scale, bar and lathe inserts as the [Bishop](../haas_bishop/README.md). The Pawn is round all over, so it's the first piece in the set with nothing for the UMC-350HD-EDU to cut. There's no mill setup or mill program.

**Status: nothing here has cut metal.** Feeds and speeds are untested estimates, and the inserts are the Knight's placeholders. The user ran Simulate in Fusion on the posted program (version 7) and it showed no collisions. Simulate with Machine hasn't been run. The toolpaths are in the Fusion document `Chess Pawn 73pct Haas UMC-350HD-EDU`, in the project `Chess Pawn - Haas UMC-350HD-EDU`. That document is a copy of the Bishop's with the Bishop's model, slit and mill setup removed. `nc/` holds a copy of what was posted from it.

## The part

Scaled from `Solid Of Pon` in the `Chess Set` document. At 73% it's 46.02 mm tall with a 25.84 mm base, and its volume is 7,887 mm3. All 30 faces are planes, cones, cylinders, tori and a sphere on the part's axis. Heights below are measured up from the base's underside.

| Feature | Heights | Size |
|---|---|---|
| Foot | z 0 to 0.52 | r 10.33, under a fillet and a bevel |
| Base | z 0.9 to 10.8 | r 12.92 at its widest |
| Waist | z 10.8 to 26.4 | Concave, r 22.6 |
| Neck | z 26.4 to 28.08 | r 4.01 |
| Lower bead, collar, upper bead | z 28.08 to 36.63 | The collar is r 7.45 |
| Ball | z 36.63 to 46.02 | r 5.79 |

Two concave corners are r 0.209, tighter than T7's r 0.4 nose: one at z 29.4 and one at z 33.5. Leaving a little stock there was accepted, as on the Rook and Bishop.

## Lathe

The program is 1006 and runs about 7.4 min. The blank is 1-1/4 in bar, 85 mm long, with a 30 mm grip, so 55 mm stands out of the jaws. The top face takes 0.49 mm. The turning stops at the bottom of a 5 mm neck under the foot (z -5), at the foot's radius.

The program turns to the `Pawn Lathe Target` body: the Pawn joined with that neck and the bar below it. Using the target, not the model, keeps Fusion from cutting into the stub.

| Pass | Tool | From z | To z | Min |
|---|---|---|---|---|
| `Face top` | T6 | top | | 0.07 |
| `Rough head` | T6 | top | 15.0 | 1.05 |
| `Rough head detail` | T7 | top | 28.08 | 2.00 |
| `Finish head` | T7 | top | 28.08 | 0.08 |
| `Rough body` | T6 | 15.0 | -5 | 0.44 |
| `Rough waist` | T7 | 28.08 | 0.90 | 2.32 |
| `Rough neck groove` | T8 | 0.90 | -5 | 0.89 |
| `Groove under collar` | T8 | 32.25 | 28.5 | 0.06 |
| `Groove under bead` | T8 | 29.0 | 25.0 | 0.05 |
| `Finish body` | T7 | 28.08 | 0.90 | 0.17 |
| `Groove neck` | T8 | 0.90 | -5 | 0.23 |

T6, T7 and T8 are the placeholder inserts from the Knight: a CNMG r 0.8, a VNMG 35 deg r 0.4, and a 3 mm groove insert r 0.2. Part-off and the foot's underside have no pass yet, as on every piece in the set.

`pawn_lathe_cam.py` sets the passes. These choices differ from the Bishop's:
- **The head is finished before the waist is finished.** T6 roughs the head and the top of the waist down to z 15, leaving 0.25 mm. It can't stop sooner: T7's neutral holder is 20 mm wide and centered on its tip, so while T7 works under the lower bead (z 28) the holder reaches about 10 mm lower. With T6 stopped at z 26, Simulate showed 5 collisions, with that holder running into the raw bar.
- **T8 cuts both undersides.** The collar's underside is 13.5 deg from radial and the lower bead's is 17 deg, both too steep for T7's V. Each groove's back limit sets where T8's lower corner stops, 3 mm below the upper one. Under the collar the lower corner runs beside the lower bead, clearing its rim (r 5.35) by staying at r 5.35 or more.
- **The spun profile is fitted at 0.002 mm, not Fusion's 0.01.** At 0.01 with smoothing, Fusion merged the neck and the top of the waist into one arc that ran 0.015 mm inside the neck. Tightening only the finishing passes' tolerance didn't change it. The finishing passes are at 0.002 mm too.
- **`Groove neck` has no lead-out.** Its 2 mm lead-out at 45 deg ran into the bar's shoulder at z -5, and Fusion warned that it had bent it. Now the insert leaves straight out in X, and no pass has a warning.
- **Feeds were read from the posted file.** No cutting move feeds faster than 0.15 mm/rev.

Stock left by the replay:

| Where | Left | Why |
|---|---|---|
| z 45.93 to 46.02, r 0.9 | 0.067 mm | A small nib at the ball's top |
| z 33.49 to 33.67, r 5.5 | 0.048 mm | The upper r 0.209 corner, accepted |

Everything else is within 0.03 mm, including the other r 0.209 corner. The deepest reading inside the model is 0.006 mm, at z 32.42 to 32.46 on the collar's rounded top.

## Running the check

It needs Python 3.9 or newer, with NumPy and SciPy. Run this from this folder:

```bash
python3 -B check_lathe.py nc/pawn_lathe.nc
```

Without them installed, `uv` can supply them:

```bash
uv run --no-project --with numpy --with scipy python -B check_lathe.py nc/pawn_lathe.nc
```

It takes about 5 s. It replays each insert's nose along the posted moves, then measures stock left and any cut into the part normal to the profile, not radially. The Bishop's check reads one radius per z row, which misreads faces lying near radial, and the Pawn's two undersides are such faces. It reads metric programs, doesn't model the inserts' flank clearance or the holders, and doesn't replace Simulate.

## Files

| File | Purpose |
|---|---|
| `pawn_lathe_cam.py` | Fusion script that sets the lathe passes' limits and adds the groove under the bead. |
| `check_lathe.py` | Replay check for the lathe program. |
| `pawn_profile.json` | The Pawn's section as (r, z) polylines, for the check. |
| `nc/pawn_lathe.nc` | The lathe program, program 1006, posted in G21. |
