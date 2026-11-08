"""Fusion script: sets the Knight's lathe passes to finish the head first, at the Pawn's 0.002 mm profile tolerance, and
posts them.

Run through the Fusion MCP with the Knight's document active. Z values here are model heights above the base's
underside; Fusion takes them as distances below G54, the turned top at model z 60.917.
"""
import adsk.cam
import adsk.core

TOP_Z_MM = 60.917
# Bottom of the waist's long curve, where the profile below is nearly a cylinder (r 12.44 to 12.48 down to z 12.47), so
# the head's finish can leave straight out in X without touching what's below. Splitting at the neck's narrowest point
# (z 17.97) would leave from the bottom of a valley.
HEAD_BOTTOM_Z_MM = 13.230
# T7's neutral holder is 20 mm wide, centred on its tip, so while T7 works at the head's bottom the holder reaches about
# 10 mm lower. On the Pawn, T6 stopping 2 mm below T7's lowest point let the holder run into raw bar. Here T6 roughs
# 13.2 mm below it, as on the Pawn.
HEAD_ROUGH_LIMIT_Z_MM = 0.0
NECK_BOTTOM_Z_MM = -5.0

# New name, current name (or None to copy from SOURCES), front Z or None for the model's front, back Z.
PASSES = (
    ("Face top", "Face top", None, None),
    ("Rough head", "Rough profile", None, HEAD_ROUGH_LIMIT_Z_MM),
    ("Rough head detail", "Rough waist", None, HEAD_BOTTOM_Z_MM),
    ("Finish head", None, None, HEAD_BOTTOM_Z_MM),
    ("Rough waist", None, HEAD_BOTTOM_Z_MM, HEAD_ROUGH_LIMIT_Z_MM),
    ("Rough neck groove", "Rough neck groove", None, None),
    ("Finish body", "Finish profile", HEAD_BOTTOM_Z_MM, NECK_BOTTOM_Z_MM),
    ("Groove neck", "Groove neck", None, None),
)
SOURCES = {"Finish head": "Finish body", "Rough waist": "Rough head detail"}
SETUP_NAME = "Lathe turn blank"
# Fusion's 0.01 mm default with smoothing ran the Pawn's finish 0.015 mm inside its neck, and finish tolerances alone
# didn't change it.
SPUN_PROFILE_TOLERANCE = "0.002 mm"
FINISH_PASSES = ("Finish head", "Finish body", "Groove neck")
FINISH_TOLERANCE = "0.002 mm"
# A lead-out from the head's bottom would run down and out, into the waist below. With none, T7 leaves straight out in X.
NO_LEAD_OUT = frozenset({"Finish head"})
HEIGHT_PREFIXES = ("frontHeight", "backHeight")
PROGRAM_NAME = "knight_lathe"


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


def add_copy(setup, source, name):
    operation_input = setup.operations.createInput(source.strategy)
    operation_input.tool = source.tool
    operation = setup.operations.add(operation_input)
    operation.name = name
    copy_settings(source.parameters, operation.parameters)
    return operation


def set_lathe_passes(cam):
    setup = cam.setups.itemByName(SETUP_NAME)
    setup.parameters.itemByName("job_spunProfileTolerance").expression = SPUN_PROFILE_TOLERANCE
    by_name = {operation.name: operation for operation in setup.allOperations}
    for new_name, current_name, _, _ in PASSES:
        if current_name and current_name in by_name and new_name not in by_name:
            by_name[current_name].name = new_name
            by_name[new_name] = by_name.pop(current_name)
    for new_name, source_name in SOURCES.items():
        if new_name not in by_name:
            by_name[new_name] = add_copy(setup, by_name[source_name], new_name)
    previous = None
    for name, _, front_z_mm, back_z_mm in PASSES:
        operation = by_name[name]
        params = operation.parameters
        if name in NO_LEAD_OUT:
            params.itemByName("exit_distance").expression = "0 mm"
        if name in FINISH_PASSES:
            params.itemByName("tolerance").expression = FINISH_TOLERANCE
        if front_z_mm is not None:
            set_z_limit(params, "frontHeight", front_z_mm)
        if back_z_mm is not None:
            set_z_limit(params, "backHeight", back_z_mm)
        if previous is not None:
            operation.moveAfter(previous)
        previous = operation
    return [operation.name for operation in setup.allOperations]


def add_or_update_program(cam, output_folder):
    """An NC program over the lathe setup, in metric, with the ST-15 machine's own post."""
    setup = cam.setups.itemByName(SETUP_NAME)
    program = next((p for p in cam.ncPrograms if p.name == PROGRAM_NAME), None)
    if program is None:
        program_input = cam.ncPrograms.createInput()
        program_input.displayName = PROGRAM_NAME
        program_input.operations = [setup]
        program = cam.ncPrograms.add(program_input)
    params = program.parameters
    params.itemByName("nc_program_filename").value.value = PROGRAM_NAME
    params.itemByName("nc_program_output_folder").value.value = output_folder
    params.itemByName("nc_program_openInEditor").value.value = False
    params.itemByName("nc_program_name").value.value = setup.parameters.itemByName("job_programName").value.value
    params.itemByName("nc_program_unit").expression = "'Millimeters'"
    params.itemByName("nc_program_post").value.value = setup.machine.postURL.toString()
    return program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())


def run(_context):
    document = adsk.core.Application.get().activeDocument
    assert document.name.startswith("Chess Knight"), document.name
    cam = adsk.cam.CAM.cast(document.products.itemByProductType("CAMProductType"))
    print(set_lathe_passes(cam))
