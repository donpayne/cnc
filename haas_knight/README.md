# Chess pieces on the Haas UMC-350HD-EDU

Python checks for a chess piece turned on a Haas ST-15 and then milled on a Haas UMC-350HD-EDU. They replay the posted G-code against the model and report what Fusion's own warnings don't show. They were built on the 73% Knight in 1215 steel, and they read one posted program, so they can be reused for other pieces.

**Status: nothing here has cut metal.** The toolpaths live in the Fusion document `Chess Knight 73pct Haas UMC-350HD-EDU` in the project of the same name, not in this repo. `nc/` holds copies of what was posted from it, so the checks have something to run on.

## Running the checks

You need Python 3.9 or newer, with NumPy and SciPy:

```bash
python3 -m pip install numpy scipy
```

Run them from this folder:

```bash
python3 -B check_z_travel.py nc/knight_mill.nc
```

| Script | What it tells you | Time |
|---|---|---|
| `check_ball_reach.py` | How much material each ball size must leave, ignoring access. Use it to pick tools before building anything. Reads a mesh and a scale, not a program. | Minutes |
| `check_z_travel.py` | How close each tool and pass comes to the lower Z limit, and the shortest tool that still reaches. Run it before Simulate with Machine. | Seconds |
| `check_flanks.py` | Overcut and touched faces on every flank pass. Run a baseline and the new post together, because only the change between them can be trusted at this scale. | Minutes |
| `check_finish.py` | Contact angle, surface speed and climb share per pass, then which pass touches each face. This is how to find retouching and slow-cutting faces. | Minutes |
| `check_small_ball.py` | Leftover, gouges and retouching on the smallest ball's passes, plus neck and shank contact. | Minutes |
| `check_gouges.py` | Whether any move, links included, enters the part. Add pass name starts to limit it, such as `Flank`. | Minutes |
| `check_lathe_nose.py` | What each lathe pass really leaves, with the insert's nose modeled. Reads an inch lathe post. | Seconds |
| `compare_posts.py` | What changed between two posts, pass by pass. Fusion leaves outdated passes out of a post with no error, so run it after any edit. | Up to a minute |

Face numbers in the output are the `index` values in `knight_faces.json`.

These checks read the program, not the machine. They don't replace Simulate with Machine, and they don't model the holder or the vise.

## Using them on another piece

1. In Fusion, set `BODY_NAME` and `OUTPUT_PATH` in `export_faces.py` and run it.
2. Change `knight_job.py`: G54's height, which faces the lathe owns, what each small-ball pass owns, semi stock and the tools.
3. Post the program in metric (`G21`) with `system://haas next generation.cps`.
4. Name passes the same way. The checks find passes by comment, and the name must start with `Rough`, `Semi`, `Flank`, `Finish`, `Detail` or `Trace`.

## Files

| File | Purpose |
|---|---|
| `knight_job.py` | Everything specific to the piece, its tools and the machine. Start here. |
| `gcode_replay.py` | Reads posted programs and the model's faces, for the checks. |
| `export_faces.py` | Fusion script that writes `knight_faces.json`. |
| `knight_faces.json` | The Knight's 66 faces as meshes. |
| `nc/knight_mill.nc` | The milling program posted from version 9 of the document, 45 passes. |
| `nc/knight_lathe.nc` | A lathe post from November 5, 2026, as an example. The lathe has no NC program in the document yet, so post it again before relying on this. |

The holder lengths in `knight_job.py` are estimates. Update them when the real tools are measured, because `check_z_travel.py` is only as good as those numbers.
