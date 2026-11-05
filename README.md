# CNC Programs

## Setup

The `.cnc` programs are plain text with no install step. `lathe_jaws_o4001.cncprj` is a CNCSimulator Pro project, so it needs that program, which it expects in its default Windows install folder.

The [Pocket NC Knight](pocketnc_knight/README.md) has a Fusion script and Python checks. To install them, get [Python](https://www.python.org/downloads/) 3.9 or newer, open Fusion once if you plan to use it, then run this from the repo's folder.

On macOS:

```bash
./setup_macos.sh
```

On Windows, double-click `setup_windows.cmd`, or run:

```bash
setup_windows.cmd
```

Both copy the `KnightBuild` script into Fusion's Scripts folder and run one check to confirm Python works. You can run them again safely, and you need to after changing the Knight's Fusion scripts, because Fusion runs the installed copy. Without Fusion, they skip the script and still test the checks.

To test the setup code itself:

```bash
python3 -B -m unittest test_setup_fusion
```

## Gauge Tool
Initial machine setup with 3 passes along the tool path.
