# CNC Programs

The [Haas Knight checks](haas_knight/README.md) replay posted programs for chess pieces cut on a Haas ST-15 and UMC-350HD-EDU. They need Python with NumPy and SciPy, and none of the setup below.

The [Haas Rook](haas_rook/README.md) is the next piece on those machines, and uses the same checks.

The [Haas Bishop](haas_bishop/README.md) follows, with its own slit and metric lathe checks.

The [Haas Queen](haas_queen/README.md) is next, on larger bar, with its flutes and scoops cut from computed paths.

## Setup

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
