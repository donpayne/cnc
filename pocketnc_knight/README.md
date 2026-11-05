# Chess Knight on a Pocket NC V2-10

G-code and Fusion scripts for cutting an 80% scale chess Knight from round wax, held in a 1 in ER40 collet. Every operation uses one 1/8 in ball end mill, so the program needs no tool change.

**Status: not ready to cut yet.** Nothing here has run on a real machine. The program changed after the last Simulate with Machine, so run that first, then Penta's simulator with your real offsets.

## What you get

| | |
|---|---|
| Size | 66.2 mm tall, 34.6 mm base, scaled to 80% from `Solid Of Knight` in the Chess Set document |
| Cutting time | Fusion estimates about 78 min: 45 roughing, 33 finishing. The real run may take longer, because the estimate assumes full programmed feed, even through very short moves |
| Setups | One. Saw the neck after cutting, then sand the bottom of the base flat |
| Tool directions | 3+2 only. Roughing runs at A0, side-on to the part, and the main finishes run at A20. Sides 90 and 270 run first, including a deeper pass at the ears from side 90, then 0 and 180, then small patches from 0 and 180 |

**Why 80%.** Two limits set the size. At A0 the tip's distance up the part axis is limited by Y travel, which ends 64.77 mm above the A axis. The holder's clearance to the B table limits how low the part can sit. Tilting doesn't rescue a taller part, because higher A runs out of Z travel. At 80% the program reaches Y 63.7, leaving 1.07 mm, and the holder clears the table by 3.2 mm, so there's almost no room for a larger `KNIGHT_SCALE`.

**Depth on each side.** Sides 90 and 270 face the nose and back, and stop 7.94 mm above the part axis, so the 9.5 mm flutes reach the top of the stock and the shank never touches wax. Sides 0 and 180 face the Knight's thin flanks, and cut through to half a tool diameter past the axis, because a ball only reaches its full width one radius above its tip. **The valley between the ears** is the exception: sides 0 and 180 can't reach past the ears, so `Rough ears 90` and `Finish ears 90` go past the axis from side 90, above Y 54.3 only. If your tool's flute length differs, change `TOOL_FLUTE_LENGTH_MM` in `build_cam.py`.

**What won't come out.** A 1/8 in cutter can't enter the fine grooves in the mane, so those stay shallow or blank, and inside corners keep a 1.6 mm radius. The 0.4 mm finish stepover leaves ridges of about 0.01 to 0.03 mm.

## Before you start

**Stock.** Turn this from one piece of round wax in a single lathe setup, so the stump runs true to the head.

| Feature | Size                                                                |
| ------- | ------------------------------------------------------------------- |
| Head    | 34.9 mm (1.375 in) diameter x 73.7 mm long, with the top faced flat |
| Stump   | 25.4 mm (1 in) diameter x 36 mm long                                |
| Overall | 109.7 mm                                                            |

The head clears the Knight's base by only 0.18 mm per side, so turn the head and stump in one setup to keep them concentric. Don't turn it larger: with 3/8 in flutes, the deep pass at the ears keeps the shank out of the wax only up to this diameter.

**The stump stands 5 mm proud of the nut,** and the other 31 mm grips in the collet. The holder passes below the shoulder on the lowest passes, so the part can't sit much lower without reaching the B table, and can't sit much higher without running out of Y travel.

**Cuts left in the wax.** A 28 mm neck sits between the base and a 2 mm shoulder. It undercuts the base by 3.3 mm. A narrower neck made the tool reach past its flutes, so the shank rubbed the shoulder.

**Tooling.** 1/8 in ball end mill as T11, in the extended holder, with 1 in (25.4 mm) of stickout and at least 3/8 in of flute. Measure the tool length offset in Kinetic Control.

**Roughing is faster than Penta's recipe.** It runs at 3 mm stepdown and 45 in/min, against Penta's 1.5 mm and 30 in/min for a flat end mill, and neither has been tried. If the tool chatters or the wax melts, set `ROUGH_STEPDOWN_MM` and `ROUGH_FEED_MM_PER_MIN` in `build_cam.py` back. Finishing stays at 30 in/min.

**Roughing leaves a little more wax in spots.** Flat-area levels are off, and the later roughs ignore slivers under 0.4 mm, which saves about 5 minutes in all. The finishes take that extra wax, up to about 0.5 mm in places that used to carry 0.15 mm.

**The main finishes tilt 20 deg so the flutes cut, not the ball's center.** At A0, walls facing the tool met the ball's center, which barely cuts. It's a fixed 3+2 tilt, not a lead or lag angle that follows the cut, so every direction of travel gets the same tool angle. `FINISH_TILT_DEG` in `knight_geometry.py` sets it. Tilting also lifts the holder off the B table. The ears, top and snout passes stay at A0, because they reach surfaces a downward tilt can't.

**The tilted finishes also run over the shoulder and neck.** A boundary projects along the tilted tool, so reaching the base's rim takes one that also takes in the neck and the shoulder's top. The ball rides the shoulder's top without cutting below it. Those surfaces stay on the stump or get sawn off, so that only adds time.

**Finishing uses scallop rings, not parallel passes.** Parallel passes cross the silhouette, so the tool ran straight down the part's edge about 100 to 140 times per side. Scallop rings follow the walls instead, which adds about a minute per deep side.

**Finish sides 0 and 180 skip what 90 and 270 already finished.** They use rest machining, ignoring skins under 0.03 mm, which halves their time. Rest machining also skips two areas near the part axis that sides 90 and 270 can't reach, so `Finish top` and `Finish snout` cut those from sides 0 and 180. `TOP_PATCH_MM`, `SNOUT_PATCH_MM` and `EARS_LOW_Y_MM` in `build_model.py` are fixed positions, and don't follow `KNIGHT_SCALE`. For 80% they were scaled from the 65% values about the Knight's base. If you change the Knight, run `check_leftover.py` and re-measure them.

**Rest machining rides down more walls, but doesn't plunge.** Its rings start partway down a wall, so the ball follows steep surfaces with its side. On a steep wall the 0.15 mm skin measures up to about 0.9 mm along the tool axis, but the ball's center isn't cutting. `check_plunge.py` measures only the center.

**The base's underside isn't finished.** The finishes stop 0.5 mm under the base, because the neck gets sawn off. The underside keeps its roughing skin until you sand it.

**Also needed:** a fine hand saw.

## Run order

1. Install the ER40 fixture and put the stump in the collet with the head's shoulder **5.0 mm above the nut**, set with a shim or calipers. Stay within 1 mm: higher uses up the 1.07 mm of Y travel the program leaves, and lower brings the holder closer to the table. Tighten by hand, then with the spanner, and re-measure. Stop if the drive gear slips: too much force damages the B-axis drive.
2. Home the machine and activate T11.
3. Touch off **Y only**, on top of the stock, and set G54 Y, allowing for the tool radius as in Penta's WCS tutorial. X and Z stay at the machine's own center, because the stock is on the B axis (same tutorial, Appendix A).
4. Run `nc/knight.ngc`.
5. Hold the Knight and saw through the neck under its base. Sand the bottom flat.

## Checks

Run these from this folder. On Windows, use `py -3` in place of `python3`.

```bash
python3 -B check_gcode.py nc/knight.ngc
```

```bash
python3 -B check_machine.py nc/knight.ngc
```

```bash
python3 -B check_stock_contact.py nc/knight.ngc
```

```bash
python3 -B check_leftover.py nc/knight.ngc
```

```bash
python3 -B check_plunge.py nc/knight.ngc
```

`check_gcode.py` tests travel, speed, the ball cutter against the Knight's mesh, the shoulder, and the shank and holder against the collet nut and B table. `check_machine.py` tests the tool, holder and spindle against Penta's A, B and Y bodies. `check_stock_contact.py` replays the program against the shrinking stock, modeling the ball's true shape, and takes several minutes. `check_leftover.py` reports the wax left outside the Knight, which the others can't see. `check_plunge.py` reports steep descents where the ball's center cuts.

Results for the current `nc/knight.ngc`:

| Check | Result |
|---|---|
| Fusion Simulate with Machine | **Not yet run on this program** |
| Y travel | Reaches 63.7 mm, against the 64.77 mm limit |
| Holder to collet nut and B table | 3.2 mm, against the 2.0 mm minimum, on the A0 roughs |
| Ball to shoulder | 0.29 mm on the roughs; the tilted finishes ride its top |
| Tool, holder and spindle to machine bodies | 2.79 mm |
| Rapids, shank and holder into wax | None deeper than the replay's 0.15 mm limit |
| Wax left outside the Knight | 137 mm3 in all, 2.5 mm3 of it above Y 55 |
| Plunges with the ball's center | 27 moves, 0.16 mm at most, against the 0.2 mm limit |

`check_gcode.py` lists two problems, which aren't real gouges: 0.059 mm and 0.067 mm into the Knight on Finish sides 90 and 0. Its 0.2 mm map cells overstate these. An exact sphere-to-mesh test on this program found the roughs at least 0.09 mm clear of the Knight, and the finishes no more than 0.033 mm into the mesh, which is about the size of its facets.

The replay doesn't catch everything: it found no rapids in the program where Simulate with Machine flagged one, so treat Simulate as the authority on collisions.

## What has not been checked

- **Fixture size.** The nut's 51.85 mm diameter and its top 3.62 mm above the B table come from Penta's simplified CAD model, not your fixture. Measure both before cutting. If they differ, update `COLLET_NUT_RADIUS_MM`, `NUT_TOP_ABOVE_TABLE_MM` and `SHOULDER_ABOVE_NUT_MM` in `knight_geometry.py` and run `check_gcode.py`.
- **Small margins.** The 3.2 mm and 2.79 mm holder clearances depend on the estimated holder size, and on the fixture numbers above. Measure the holder too.
- **Holder size and flute length.** The extended holder is an estimated envelope from Penta's "about 3 in long", and the flute length is assumed to be 3/8 in.
- **Machine simulation.** The scripts can't start Simulate with Machine or Penta's simulator, and Penta's hasn't been run. The Fusion machine model also has no collet or nut, so only `check_gcode.py` tests those.
- **B axis X position.** Fusion's machine file puts the B axis at machine X = 6.05 mm, while the run order keeps G54 X at the machine's center, following Penta's tutorial. Confirm in Penta's simulator that the tool lines up with the B axis.
- **Neck strength.** The 28 mm wax neck carries the whole Knight through finishing. It hasn't been tried.

## Known issues

- **Part Position sets the mount in machine simulation.** Fusion's default attaches the bottom of the model's box along WCS Z to the table center, which puts this part off the B axis and too low. `_mount_part_in_collet` attaches the G54 point instead. Only the simulation reads this setting.
- **Which machine the setup gets.** `_find_machine` uses a Pocket NC V2-10 from your Local machine library if there is one. Otherwise it uses Fusion's own copy with the 3D model cleared, because a setup rejects that copy's model (`setMachineResult.has_value()`). That copy posts G-code but can't run Simulate with Machine.
- **Machine 3D model version.** A Local machine must point at the latest version of its 3D model, or Fusion marks the machine as out of date. Fusion also rejects a machine swap on a document that already has another model version loaded, but accepts the machine when a setup is created.
- **Regenerating.** Fusion crashed once regenerating many operations at once, so generate one at a time. Scripts that change toolpaths or post also fail while Simulate is open.
- **Rapids near a ball's ridges.** Adaptive rapids stop the vertical lead radius plus about 0.3 mm above the level, whatever `rampClearanceHeight` says. A ball leaves ridges up to one radius tall, so `ROUGH_ENTRY_LEAD_RADIUS_MM` keeps that stop above them.
- **Replacing bodies in a saved document.** Switch to the Design workspace and back, then build setups in a separate script call. Skipping the switch gives "Model has one or more missing selections".

## Rebuilding

You don't need Fusion to cut `nc/knight.ngc`. The saved Fusion document it came from is `Knight 80pct Pocket NC V2-10`, in the author's Default Project. The scripts don't read it: they rebuild from this folder. To rebuild the toolpaths in your own account, for example after changing `KNIGHT_SCALE`:

1. Check your licence. Every operation uses a tilted tool orientation (3+2). Autodesk's 2020 terms kept that out of the free personal tier, so check its current terms.
2. Run the setup script from the [repo's README](../README.md#setup). Run it again after any change to the files it installs.
3. To use Simulate with Machine, add the Pocket NC V2-10 from the Fusion library to your Local library in Fusion's Machine Library.
4. In Fusion, open Utilities > Add-Ins > Scripts and Add-Ins, select `KnightBuild` and click Run. It builds everything in a new, unsaved document, which takes several minutes, and leaves your other documents alone.
5. Find the program at `Documents/Knight G-code/knight.ngc` in your home folder. It doesn't replace `nc/knight.ngc`.
6. Run every check on the new file, then both simulators, before cutting. A different Fusion version can produce different toolpaths, so these results don't carry over.

| File | Purpose |
|---|---|
| `knight_geometry.py` | All dimensions. Plain Python; start here to change the scale or stock. |
| `knight_source.sat` | The full-size Knight in its original position, which the build scales and moves. |
| `build_model.py` | Creates the Knight, mount, stock, G54 point and helper sketches. |
| `build_cam.py` | Creates the setup, T11 and the toolpaths, and posts the program. |
| `fusion_script/` | `KnightBuild`, the script that runs both of the above in order. |
| `check_gcode.py`, `check_machine.py`, `check_stock_contact.py`, `check_leftover.py`, `check_plunge.py` | Check the posted G-code in plain Python. |
| `knight_mesh.json`, `machine_mesh.json` | Meshes the checks read: the unscaled Knight, and Penta's machine bodies. |

The G-code must be posted with `system://penta machine.cps` and "Rotated Work Offsets WCS" set to 9 (G59.3), which `post_setup` does. Don't let an NC program pick its post by default, because it uses whichever post ran last.
