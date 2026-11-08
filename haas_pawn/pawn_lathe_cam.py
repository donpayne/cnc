"""Fusion script: sets the Pawn's lathe passes, which came with the Bishop's document it was copied from.

Run through the Fusion MCP with the Pawn's document active. The document is a copy of the Bishop's, so the passes,
tools, stock and post are the Bishop's. Only the Z limits change, and one T8 groove is added under the lower bead.
Z values here are model heights above the base's underside; Fusion takes them as distances below G54, the ball's top.
"""
import adsk.cam
import adsk.core

TOP_Z_MM = 46.0172
# T6 roughs the head well down the waist. T7's neutral holder is 20 mm wide, centered on its tip, so while T7 works under
# the lower bead (z 28) the holder reaches about 10 mm lower. Stopped at z 26, T6 left the raw bar there, and Simulate
# showed the holder running into it.
STEM_ROUGH_LIMIT_Z_MM = 15.0
HEAD_BOTTOM_Z_MM = 28.0842  # Top of the 8 mm neck, under the lower bead's fillet.
BASE_UNDERSIDE_Z_MM = 0.8955  # Top of the foot's fillet, where T8 takes over.
NECK_BOTTOM_Z_MM = -5.0

# Both undersides face the chuck too steeply for T7's 35 deg V: the collar's cone is 13.5 deg from radial and the lower
# bead's 17 deg. T8's side takes them. Each back limit bounds the insert's lower corner, 3 mm below its upper one.
# Under the collar the upper corner must reach the cone's foot (z 31.86) and some of the fillet below, which T7 can't. The
# lower corner then sits beside the lower bead, but at r 5.9 and more it clears the bead's rim (r 5.35). At 28.95 it left
# 0.106 mm at the cone's foot. Under the bead it rides down the neck, clear of the waist.
COLLAR_RIM_Z_MM = 32.25
UNDER_COLLAR_BOTTOM_Z_MM = 28.5
BEAD_RIM_Z_MM = 29.0
UNDER_BEAD_BOTTOM_Z_MM = 25.0

# Pass name, front Z or None for the model's front, back Z or None to keep the pass's own.
PASSES = (
    ("Face top", None, None),
    ("Rough head", None, STEM_ROUGH_LIMIT_Z_MM),
    ("Rough head detail", None, HEAD_BOTTOM_Z_MM),
    ("Finish head", None, HEAD_BOTTOM_Z_MM),
    ("Rough body", STEM_ROUGH_LIMIT_Z_MM, NECK_BOTTOM_Z_MM),
    ("Rough waist", HEAD_BOTTOM_Z_MM, BASE_UNDERSIDE_Z_MM),
    ("Rough neck groove", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
    ("Groove under collar", COLLAR_RIM_Z_MM, UNDER_COLLAR_BOTTOM_Z_MM),
    ("Groove under bead", BEAD_RIM_Z_MM, UNDER_BEAD_BOTTOM_Z_MM),
    ("Finish body", HEAD_BOTTOM_Z_MM, BASE_UNDERSIDE_Z_MM),
    ("Groove neck", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
)
NEW_PASS_SOURCES = {"Groove under bead": "Groove under collar"}
SETUP_NAME = "Lathe turn blank"
# Groove neck's 2 mm lead-out at 45 deg ran into the bar's shoulder at z -5, and Fusion warned it had bent it. With no
# lead-out the insert leaves straight out in X, along the shoulder, as the Queen's flange groove does.
NO_LEAD_OUT = frozenset({"Groove neck"})
# Fusion turns to a spun profile fitted at 0.01 mm by default. With smoothing that merged the neck and the waist's top into
# one arc 0.015 mm inside the neck, and finish tolerances alone didn't change it.
SPUN_PROFILE_TOLERANCE = "0.002 mm"
# The finishing passes match it, rather than the Bishop's 0.01.
FINISH_PASSES = ("Finish head", "Groove under collar", "Groove under bead", "Finish body", "Groove neck")
FINISH_TOLERANCE = "0.002 mm"
HEIGHT_PREFIXES = ("frontHeight", "backHeight")


def set_z_limit(params, prefix, z_mm):
    params.itemByName(f"{prefix}_mode").expression = "'from wcs'"
    params.itemByName(f"{prefix}_offset").expression = f"{z_mm - TOP_Z_MM:.4f} mm"


def copy_settings(source_params, target_params):
    for index in range(source_params.count):
        source = source_params.item(index)
        target = target_params.itemByName(source.name)
        if target is None or source.name.startswith(HEIGHT_PREFIXES) or target.expression == source.expression:
            continue
        try:
            target.expression = source.expression
        except RuntimeError:
            pass  # Computed or read-only settings.


def add_copy(setup, source, name, after):
    operation_input = setup.operations.createInput(source.strategy)
    operation_input.tool = source.tool
    operation = setup.operations.add(operation_input)
    operation.name = name
    copy_settings(source.parameters, operation.parameters)
    operation.moveAfter(after)
    return operation


def set_lathe_passes(cam):
    setup = cam.setups.itemByName(SETUP_NAME)
    setup.parameters.itemByName("job_spunProfileTolerance").expression = SPUN_PROFILE_TOLERANCE
    by_name = {operation.name: operation for operation in setup.allOperations}
    for name, source_name in NEW_PASS_SOURCES.items():
        if name not in by_name:
            by_name[name] = add_copy(setup, by_name[source_name], name, by_name[source_name])
    for name, front_z_mm, back_z_mm in PASSES:
        params = by_name[name].parameters
        if name in NO_LEAD_OUT:
            params.itemByName("exit_distance").expression = "0 mm"
        if name in FINISH_PASSES:
            params.itemByName("tolerance").expression = FINISH_TOLERANCE
        if front_z_mm is None:
            params.itemByName("frontHeight_mode").expression = "'model front'"
        else:
            set_z_limit(params, "frontHeight", front_z_mm)
        if back_z_mm is not None:
            set_z_limit(params, "backHeight", back_z_mm)
    return [operation.name for operation in setup.allOperations]


def run(_context):
    document = adsk.core.Application.get().activeDocument
    assert document.name.startswith("Chess Pawn"), document.name
    cam = adsk.cam.CAM.cast(document.products.itemByProductType("CAMProductType"))
    print(set_lathe_passes(cam))
