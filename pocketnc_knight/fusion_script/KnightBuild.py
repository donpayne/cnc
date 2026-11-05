"""Fusion script: builds the Knight in a new, unsaved document, generates its toolpaths and posts the G-code.

setup_macos.sh or setup_windows.cmd installs this, with the modules it imports, into Fusion's Scripts
folder. Run it from Utilities > Add-Ins > Scripts. It never touches the open documents, and it posts to
OUTPUT_DIR rather than the repo, so the checked nc/knight.ngc stays as it is.
"""
import importlib
import os
import sys
import time
import traceback

import adsk.cam
import adsk.core
import adsk.fusion

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import build_cam
import build_model

# Fusion keeps imported modules between runs, so edits wouldn't take effect without a reload.
importlib.reload(build_model)
importlib.reload(build_cam)

SOURCE_BODY_PATH = os.path.join(SCRIPT_DIR, "knight_source.sat")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Knight G-code")
GENERATION_POLL_SECS = 0.1


def _new_design(app):
    """Open a new design that reads every value the way the checked program did, whatever the user's defaults."""
    preferences = app.preferences.generalPreferences
    user_orientation = preferences.defaultModelingOrientation
    # The setup takes its axes from the model's orientation, so a Y-up default would turn the whole program.
    preferences.defaultModelingOrientation = adsk.core.DefaultModelingOrientations.ZUpModelingOrientation
    try:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    finally:
        preferences.defaultModelingOrientation = user_orientation
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    # Fusion's CAM defaults differ between inch and mm documents, so match the one the checked program came from.
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    return document, design


def _build_model(root):
    temp = adsk.fusion.TemporaryBRepManager.get()
    source_bodies = temp.createFromFile(SOURCE_BODY_PATH)
    if source_bodies is None or source_bodies.count != 1:
        raise RuntimeError(f"Expected one body in {SOURCE_BODY_PATH}")
    build_model.add_bodies(root, build_model.scaled_knight(temp, source_bodies.item(0)))
    build_model.add_work_origin(root)
    build_model.add_boundary_sketches(root)
    build_model.add_tool_axis_sketch(root)


def _generate_in_order(cam, setup):
    """Generate one operation at a time: rest machining reads the earlier ones, and doing many at once crashed Fusion."""
    for operation in setup.allOperations:
        future = cam.generateToolpath(operation)
        while not future.isGenerationCompleted:
            adsk.doEvents()
            time.sleep(GENERATION_POLL_SECS)
        if not operation.isToolpathValid:
            raise RuntimeError(f"{operation.name} has no valid toolpath: {operation.error or operation.warning}")


def rebuild_and_post(app, output_dir):
    """Return the path of the posted program."""
    document, design = _new_design(app)
    root = design.rootComponent
    _build_model(root)
    # A new document has no CAM product until the Manufacture workspace has been opened.
    app.userInterface.workspaces.itemById("CAMEnvironment").activate()
    cam = adsk.cam.CAM.cast(document.products.itemByProductType("CAMProductType"))
    setup = build_cam.build_all(cam, root)
    _generate_in_order(cam, setup)
    os.makedirs(output_dir, exist_ok=True)
    build_cam.post_setup(cam, setup, output_dir, build_cam.OUTPUT_FILE_NAME)
    return os.path.join(output_dir, build_cam.OUTPUT_FILE_NAME + ".ngc")


def run(_context):
    app = adsk.core.Application.get()
    try:
        output_path = rebuild_and_post(app, OUTPUT_DIR)
        app.userInterface.messageBox(
            f"Posted {output_path}\n\nThe document is unsaved. Run the checks and both simulators before cutting. "
            "Simulate with Machine needs the Pocket NC V2-10 in your Local machine library (see the README).")
    except Exception:
        app.userInterface.messageBox(traceback.format_exc())
