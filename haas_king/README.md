# King on the Haas UMC-350HD-EDU

Checks and posted programs for a 73% chess King in 1215 steel, turned on a Haas ST-15 and then milled on a Haas UMC-350HD-EDU. It's the same scale, bar, vise and steel as the [Queen](../haas_queen/README.md). It's the first piece in the set with a simultaneous cut: the cup is turned by C at a fixed B.

**Status: nothing here has cut metal.** Simulate in Fusion was run on the crown setup, but not Simulate with Machine. Feeds and speeds are untested estimates, and tool and holder sizes are estimates too. The toolpaths live in the Fusion document `Chess King 73pct Haas UMC-350HD-EDU`, in the project `Chess King - Haas UMC-350HD-EDU`. `nc/` holds copies of what was posted from it, and the `king_*_cam.py` scripts record how the passes were built.

## The part

Scaled from `Solid Of the King` in the `Chess Set` document: 86.23 mm tall at 73%, r 17.98 at the base, 223 faces, with no cross on top. It's round except for 8-fold features centered on C 0, 45 and so on.

| Feature | Size | Who cuts it |
|---|---|---|
| All revolved faces | z -5 to 86.23 | ST-15 |
| Octagonal shaft | z 25.8 to 48.7, flats 5.65 from the axis, ruled sideways | UMC, T2 then T4 |
| 8 crown facets | z 63.9 to 77.6, flat, 22.9 deg from vertical | UMC, T2 |
| Waist under the facets | Concave fillet r 0.556 into an octagonal ledge | UMC, T10 |
| 8 rim notches | At C 22.5 and so on, 60 deg V with r 1.724 round bottoms | UMC, T4 |
| Cup and the finial's underside | A cone from the rim down to a fillet floor at z 75.6, under the head at r 4.65 | UMC, T4 and T14, turning C |
| 8 finial flutes | Vertical cylinders r 1.724, axes at r 4.95, z 80.2 to 85.0 | UMC, T11 |

**The waist fillet stays a little proud of the model, by choice.** T10's ball is r 0.794, larger than the fillet's r 0.556, so it leaves up to 0.103 mm in the corner.

## Lathe

Program 1005, about 15.2 min. The blank is 1-1/2 in bar, 125 mm long, with a 30 mm grip. Jaws must be bored for 38.1 mm on both machines. Cutting stops at the neck bottom, z -5. The passes are the Queen's, with the King's Z limits.

| Pass | Tool | Min |
|---|---|---|
| `Face top` | T6 | 0.09 |
| `Rough profile` | T6 | 3.08 |
| `Finish tip` | T6 | 0.02 |
| `Rough detail` | T7 | 9.98 |
| `Finish profile` | T7 | 0.57 |
| `Rough under head` | T8 | 0.08 |
| `Groove under head` | T8 | 0.21 |
| `Groove under collar` | T8 | 0.13 |
| `Rough neck groove` | T8 | 1.14 |
| `Groove neck` | T8 | 0.28 |

T6, T7 and T8 are the placeholder inserts from the Knight: CNMG r 0.8, VNMG 35 deg r 0.4, and a 3 mm groove r 0.2. Part-off and the base's underside have no pass yet.

**T6 finishes the finial's tip, not T7.** T7's neutral holder is 20 mm wide, centred on its tip, so it reaches 10 mm below the tip. Near the axis it sat over the head's top, r 11.65, and Simulate flagged a collision in `Rough detail`. `Finish tip` has T6, whose right-hand holder sits above its tip, finish the dome and cone right after its roughing, down to their corner with the r 4.937 cylinder at z 83.85. Both T7 passes start there. Measured square to the surface, `Finish tip` cuts in by at most 0.0002 mm and leaves at most 0.004 mm. `check_lathe.py`'s -0.143 at z 86.20 to 86.22 is its radial measure on the nearly flat top of the dome. `finish_tip_with_t6()` in `king_lathe_cam.py` made the change. You reported Simulate good on this lathe program and the T4 mill program (version 24).

**T8 plunges under the finial's head** to a staircase over a floor at z 79.1, so the mill's cup roughing has less to take. `Groove under collar` cuts the collar's steep underside, z 55.6 to 51.0.

**The target is the mill's stock, not the model.** It's the `Lathe Target` body, revolved from the sketch `Lathe Target Profile`, which is drawn in the plane at C 22.5, through the corners:
- **It stands 0.1 mm outside the 8-fold corners**, on the octagon (z 27.65 to 45.41) and on the crown's seams (z 63.18 to 65.05). Turned exactly to the corners, the lathe's small undercuts left a turned strip along every seam. With the extra stock the two mill passes on either side meet in a sharp seam.
- **The extra tapers to 0 at each end,** over 1 mm on the octagon and 0.5 mm of profile on the crown. Past the ends are revolved cones, collars and fillets that no mill pass touches, so the lathe must finish them to size.
- `grow_target_corners()` and `grow_target_crown_seams()` in `king_lathe_cam.py` made those changes. After changing the target, set the lathe setup's model to another body and back, or Fusion keeps turning to the old silhouette, then re-export `king_lathe_profile.json`.

Stock left by the replay, against the target:

| Where | Left | Why |
|---|---|---|
| z -5 to -4.92 | 0.188 mm | T8's corner at the neck bottom, which comes off with the stub |
| z 60.68 to 61.06 | 0.078 mm | Small steps in the collar's profile |
| z 78.88 to 79.18 | 0.187 mm | The staircase's floor under the head, which the mill's cup passes take |
| z 82.02 to 82.84 | 0.139 mm | The staircase's steps under the head, same |

Four other bands read 0.039 to 0.096 mm, all small steps under 0.2 mm long.

**Readings the other way:**
- **z 82.10, -0.150 mm: probably not real.** It's a single row at the staircase's step, where `check_lathe.py`'s one radius per z row can't represent a vertical face. It hasn't been proven.
- **z 86.20 to 86.22, -0.143 mm: not real.** It's the radial measure on the nearly flat top of the dome. Measured square to the surface, T6's `Finish tip` is within 0.0002 mm. The 0.437 mm nib T7 used to leave there is gone.
- **Everything else, 0.031 mm or less.** The largest is at z 24.02 to 24.30. On the crown's seams the target is 0.1 out, so -0.011 there still turns 0.089 proud of the model's corner.

## Mill

Program 1001, about 106 min. Jergens 130 mm vise, aluminum soft jaws, no riser, 30 mm grip on the stub. G54 is the finial's tip, model z 86.2316. Passes run far from the vise first, after the cup.

The program is three setups posted as one file. The cup's ring passes need their own model, `King Revolved` (the lathe target with the cup cut out), because Fusion's per-operation model override is disabled in the API. Rough Cup sits in a setup of its own before them, because regenerating it on `King Revolved` crashed Fusion's CAM kernel.

| Setup | Stage | Tool | Pose | Min, all passes |
|---|---|---|---|---|
| `Mill King rough cup` | `Rough Cup` | T4 | B0, Adaptive | 26.8 |
| `Mill King cup rings` | `Rough Under Head` 1.00, 0.75, 0.50, 0.25 | T4 | B45, turning C | 14.1 |
| | `Rough Floor` 0.33, 0.08 | T14 | B45, turning C | 6.8 |
| | `Semi Cup`, `Finish Cup` | T4 | B45, turning C | 13.0 |
| | `Finish Floor` | T14 | B45, turning C | 3.3 |
| `Mill King crown and cup` | `Rough Flute`, `Finish Flute` x 8 | T11 | B0 | 9.5 |
| | `Rough Notch`, `Finish Notch` x 8 | T4 | B22.88 at C 22.5 and so on | 26.8 |
| | `Semi Facet`, `Finish Facet` x 8 | T2 | B22.88 | 1.0 |
| | `Waist` x 8 | T10 | B67.16 | 3.4 |
| | `Semi Octagon`, `Finish Octagon` x 8 | T2 | B90, C 90 and so on | 1.1 |
| | `Octagon Strips` x 8 | T4 | B90 | 0.5 |

Simulate reads 43:36 for the crown setup, with 5 tool changes.

**The cup is cut in rings.** Each ring pass is a 4-axis Multi-Axis Contour with the tool held 45 deg to the C axis, so it posts B45 held while C turns. `king_cup.py` writes the contact rings to `king_cup_rings.json`, and a stock to leave pushes the ball out along the surface normal, which makes the roughing layers. The layers stop at 1.00, because a stock at or above the floor fillet's r 1.159 gives an empty path, and once crashed Fusion. Fusion skips a few rings at the bead and the head's edge, which leaves up to 0.028 mm there.

**The crown and shaft passes are computed paths.** `king_mill.py` lays out each feature's tool path once, on its seed side, and `king_mill_cam.py` traces it. Each flank pass's chain carries its own move out and back in air, because a trace retracts only along the tool axis, which would drag the flank along the face just cut. The octagon is cut by T2's flank lying along each side, but T2 would hit the base's fillet and the collar near the ends, so T4 flanks the last strips.

**Repeats are circular CAM patterns.** Each `x 8` stage is one pass at C 0 (C 22.5 for the notches) in a pattern around the part's Z axis, 45 deg a step. Fusion's API can't create a pattern, so the first, on `Rough Flute`, was made by hand, and `pattern_all_seeds()` copies it onto the other nine.

**C unwinds before every operation.** The C axis's reset is set to "before every operation" in the 3 mill setups' machines and in the Local `.mch`, so each operation starts near C 0 and the post sends `G28 G91 C0` between them. Inside a ring pass C still winds, up to 21,456 deg in `Finish Cup`. Confirm the control takes that before cutting. When editing a setup's machine from a script, assign it back (`setup.machine = machine`), or the post keeps the old one.

## Tools

Mill tools. Lengths in mm. Total is gauge line to tip.

| Tool | Type | Total | rpm | mm/min |
|---|---|---|---|---|
| T2 | 1/4 in flat, 25.4 flute | 133.6 | 7,600 | 762 |
| T4 | 1/8 in ball, 6.35 shank from 25 up | 120.0 | 10,000 | 305 |
| T10 | 1/16 in ball, relieved neck to 19.05 | 114.3 | 10,000 | 120 |
| T11 | 2 mm flat, 3.175 shank from 6 up | 102.9 | 10,000 | 200 |
| T14 | 2 mm ball, relieved neck to 10, 3.175 shank | 108.9 | 10,000 | 150 |

**T4 must be 120 mm gauge to tip, 31.1 out of the holder,** or `Octagon Strips` runs out of Z travel at B90. That's the length for every piece in the set. In Fusion, set the tool's stored assembly gauge length as well as its body length, because the gauge doesn't follow the body length. By version 18 the document had gone back to 113.9. Version 21 restores 120, and regenerating changed only `Rough Cup`. All lengths should be measured, because the Z and holder margins below depend on them.

## What the checks found

On the posted programs:

- **Flutes, notches, facets and octagon cut to the model.** Checked exactly in each tool's frame against the model's planes and cylinders: Rough Notch leaves 0.100 and Finish Notch at most 0.02 mm; all 16 facet copies are within 0.0005 mm of their planes; all 8 octagon sides within 0.0003 mm. The octagon passes' moves in air clear the stock by 0.87 mm or more.
- **The waist leaves at most 0.103 mm in the fillet,** as accepted, and 0.037 mm on the bands above it.
- **Every ring pass holds its stock to within 0.009 mm.**
- **Z margin at B90:** T2 19.51 mm, T4 5.01 mm, both on the octagon. Passes at other tilts aren't measured by this check.
- **The holder clears the vise by 3.8 mm at the closest,** on the octagon passes at B90, at C 45, 135 and 315. The holder is estimated, so measure it and rerun this before cutting. The shank reads negative inside the cup and the notches, which is expected: the envelope there is the uncut model's.

These read the program, not the machine. **The lathe check doesn't model the inserts' flank clearance or the holders, the exact checks of the crown and shaft are scratch scripts that aren't in this folder, and none of this replaces Simulate with Machine.**

## Running the checks

They need Python 3.9 or newer, with NumPy and SciPy, and they reuse code in `../haas_bishop` and `../haas_knight`. Run these from this folder:

```bash
python3 -B check_lathe.py nc/king_lathe.nc
```

```bash
python3 -B check_holder.py nc/king_mill.nc
```

`check_lathe.py` takes a few seconds and `check_holder.py` about 90 s.

To check Z travel, run the Knight's check through this job file, from the repo root:

```bash
python3 -B -c "import sys; sys.path[:0] = ['haas_king', 'haas_knight']; import king_job; sys.modules['knight_job'] = king_job; sys.argv = ['', 'haas_king/nc/king_mill.nc']; import check_z_travel; check_z_travel.main()"
```

It labels T4's deepest point `Finish Octagon`, but T4 runs only `Octagon Strips` at B90.

## Files

| File | Purpose |
|---|---|
| `king_job.py` | What the checks need to know about the part, tools and machine. |
| `king_mill.py` | Tool paths and limits for the crown, notches, flutes and octagon, and the lathe target's corner stock. Plain Python. |
| `king_cup.py` | Contact rings for the cup and the finial's underside. Plain Python; run it to write `king_cup_rings.json`. |
| `king_mill_cam.py` | Fusion helpers that build the crown and shaft passes, copy the pattern and post the mill program. |
| `king_cup_cam.py` | Fusion helpers that build the cup's setups and ring passes. |
| `king_lathe_cam.py` | Fusion helpers that copy the lathe passes from the Queen's document, and grow the lathe target at the corners. |
| `check_lathe.py` | Replay check for the lathe program, using the Bishop's. |
| `check_holder.py` | Replay of the mill program with the holder and shank, against the vise and the part. |
| `king_faces.json` | The King's faces as meshes. |
| `king_cup_rings.json` | The cup's contact rings, written by `king_cup.py`. |
| `king_lathe_profile.json` | The lathe target's faces as (r, z) nodes. |
| `nc/king_mill.nc` | The milling program, program 1001, posted in G21. |
| `nc/king_lathe.nc` | The lathe program, program 1005, posted in G21. |
