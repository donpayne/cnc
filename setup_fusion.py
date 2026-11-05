"""Installs the Knight's Fusion script and confirms this computer can run the repo's check scripts.

Run through setup_macos.sh or setup_windows.cmd. Run it again after changing a file in SCRIPT_FILES,
because Fusion runs the installed copy. Fusion's own library supplies the Pocket NC machine and Penta's post.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

MINIMUM_PYTHON = (3, 9)  # The oldest version the check scripts have run on, and macOS's own python3.
SCRIPT_NAME = "KnightBuild"
KNIGHT_DIR = Path(__file__).resolve().parent / "pocketnc_knight"
SCRIPT_FILES = (
    KNIGHT_DIR / "fusion_script" / f"{SCRIPT_NAME}.py",
    KNIGHT_DIR / "fusion_script" / f"{SCRIPT_NAME}.manifest",
    KNIGHT_DIR / "build_model.py",
    KNIGHT_DIR / "build_cam.py",
    KNIGHT_DIR / "knight_geometry.py",
    KNIGHT_DIR / "knight_source.sat",
)


def fusion_data_dir(platform_name, environ, home_dir):
    """Return the folder where Fusion keeps its per-user data."""
    if platform_name == "win32":
        return Path(environ["APPDATA"]) / "Autodesk" / "Autodesk Fusion 360"
    if platform_name == "darwin":
        return home_dir / "Library" / "Application Support" / "Autodesk" / "Autodesk Fusion 360"
    raise ValueError(f"Fusion runs only on Windows and macOS, not {platform_name}")


def install_script(fusion_dir):
    """Copy the script to where Fusion lists it, and return that folder. Fusion needs a folder and script of one name."""
    script_dir = fusion_dir / "API" / "Scripts" / SCRIPT_NAME
    script_dir.mkdir(parents=True, exist_ok=True)
    for source_path in SCRIPT_FILES:
        shutil.copy2(source_path, script_dir / source_path.name)
    return script_dir


def check_scripts_run():
    """Run the fastest check. check_gcode.py can't serve here: it exits 1 on the program's known warnings."""
    result = subprocess.run(
        [sys.executable, "-B", "check_machine.py", str(Path("nc") / "knight.ngc")],
        cwd=KNIGHT_DIR, stdout=subprocess.DEVNULL)
    return result.returncode == 0


def main():
    if sys.version_info < MINIMUM_PYTHON:
        print(f"Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer is required, found {sys.version.split()[0]}.")
        return 1

    fusion_dir = fusion_data_dir(sys.platform, os.environ, Path.home())
    if fusion_dir.is_dir():
        print(f"Installed the {SCRIPT_NAME} script in {install_script(fusion_dir)}")
    else:
        print(f"Fusion not found at {fusion_dir}, so the {SCRIPT_NAME} script wasn't installed.")
        print("Install Fusion, open it once and run this again. The G-code and checks don't need it.")

    if not check_scripts_run():
        print("check_machine.py failed, so the check scripts aren't working on this computer.")
        return 1
    print("Check scripts work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
