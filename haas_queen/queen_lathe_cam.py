"""Fusion script: adds the Queen's lathe passes, copying each one's settings from the Bishop's document.

Run through the Fusion MCP with the Queen's document active and the Bishop's open. Only the Z limits differ: they
are distances below G54, at the finial's tip. Everything else, including insert feeds, is the Bishop's.
"""
import adsk.cam
import adsk.core

TOP_Z_MM = 81.003
HEAD_BOTTOM_Z_MM = 50.814  # The lower flange's underside edge, the head's lowest face.
STEM_ROUGH_LIMIT_Z_MM = 44.0  # T6 stays clear of the flange, as on the Bishop.
BASE_UNDERSIDE_Z_MM = 0.966  # Top of the base's lower fillet, where T8 takes over.
NECK_BOTTOM_Z_MM = -5.0
UNDER_COLLAR_BOTTOM_Z_MM = 43.4
CROWN_RIM_Z_MM = 76.4  # Where the crest envelope meets the crown's top cone, the outer end of T8's cut.
UPPER_FLANGE_TOP_Z_MM = 55.6
# Low enough that the insert's upper corner runs down the blend under the flange and clears what T7 can't reach, and
# high enough that its lower corner stays above the lower flange.
UPPER_FLANGE_BOTTOM_Z_MM = 51.3

# T7's lower edge hits the crown's flat top on the way to the stub, and the cone under the upper flange is too flat
# for its V. T8's flat end can do both. Settings come from the Bishop's groove under its collar.
GROOVE_SOURCE = "Groove under collar"
EXTRA_GROOVES = (
    ("Groove crown cone", None, CROWN_RIM_Z_MM),
    ("Groove under flange", UPPER_FLANGE_TOP_Z_MM, UPPER_FLANGE_BOTTOM_Z_MM),
)
# Any lead-out here runs toward the lower flange, and Fusion warns that it had to bend it. Straight out in X is clear,
# because the cone rises away from the insert's upper corner and the flange is below its lower one.
NO_LEAD_OUT = frozenset({"Groove under flange"})

# T5 cuts the finial's neck, which T7 and T8 can't reach. The front limit is the ball's equator, where T7 stops. The back
# limit is on the crown's cone, past where the neck's fillet meets it.
FINIAL_NECK_SOURCES = (("Rough finial neck", "Rough neck groove"), ("Finish finial neck", "Groove neck"))
FINIAL_NECK_FRONT_Z_MM = 79.93
FINIAL_NECK_BACK_Z_MM = 77.9
FINIAL_NECK_FEEDS = {
    # r 1.1 at 2,000 rpm is only 14 m/min, so this pass alone runs up to the program's top speed.
    "tool_maximumSpindleSpeed": "4000 rpm",
    "tool_feedCuttingRel": "0.02 mm",
    "tool_feedEntryRel": "0.02 mm",
    "tool_feedExitRel": "0.02 mm",
    "tolerance": "0.005 mm",
}
FINIAL_NECK_ROUGH_STEPS = {
    # Half the insert's width, so a roughing plunge never cuts with its full radius.
    "maximumGrooveStepover": "0.4 mm",
    "maximumGrooveStepdown": "0.3 mm",
    # Fusion measures from the bar's surface, r 19.05, and T8 has already cleared this down to r 2.1. Left at the bar, each
    # plunge feeds through air at 0.02 mm/rev and the pass takes 6 minutes. r 5.05 is still above the crown's cone.
    "outerRadius_offset": "-14 mm",
}

# Pass name, front Z or None for the model's front, back Z.
PASSES = (
    ("Face top", None, None),
    ("Rough head", None, STEM_ROUGH_LIMIT_Z_MM),
    ("Rough head detail", None, HEAD_BOTTOM_Z_MM),
    ("Finish head", None, HEAD_BOTTOM_Z_MM),
    ("Rough body", STEM_ROUGH_LIMIT_Z_MM, NECK_BOTTOM_Z_MM),
    ("Rough waist", HEAD_BOTTOM_Z_MM, BASE_UNDERSIDE_Z_MM),
    ("Rough neck groove", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
    ("Groove under collar", HEAD_BOTTOM_Z_MM, UNDER_COLLAR_BOTTOM_Z_MM),
    ("Finish body", HEAD_BOTTOM_Z_MM, BASE_UNDERSIDE_Z_MM),
    ("Groove neck", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
)
HEIGHT_PREFIXES = ("frontHeight", "backHeight")


def find_tool(cam, tool_number):
    for tool in cam.documentToolLibrary:
        if tool.parameters.itemByName("tool_number").value.value == tool_number:
            return tool
    raise ValueError(f"no T{tool_number} in the document's tool library")


def copy_settings(source_params, target_params):
    """Copies every setting that differs and returns the ones Fusion refused. Those are computed or read-only."""
    refused = []
    for index in range(source_params.count):
        source = source_params.item(index)
        target = target_params.itemByName(source.name)
        if target is None or source.name.startswith(HEIGHT_PREFIXES) or target.expression == source.expression:
            continue
        try:
            target.expression = source.expression
        except RuntimeError:
            refused.append(source.name)
    return refused


def set_z_limit(params, prefix, z_mm):
    params.itemByName(f"{prefix}_mode").expression = "'from wcs'"
    params.itemByName(f"{prefix}_offset").expression = f"{z_mm - TOP_Z_MM:.4f} mm"


def add_lathe_passes(cam, bishop_cam):
    bishop_setup = bishop_cam.setups.itemByName("Lathe turn blank")
    sources = {operation.name: operation for operation in bishop_setup.allOperations}
    setup = cam.setups.itemByName("Lathe turn blank")
    for name, front_z_mm, back_z_mm in PASSES:
        source = sources[name]
        tool_number = source.tool.parameters.itemByName("tool_number").value.value
        operation_input = setup.operations.createInput(source.strategy)
        operation_input.tool = find_tool(cam, tool_number)
        operation = setup.operations.add(operation_input)
        operation.name = name
        refused = copy_settings(source.parameters, operation.parameters)
        if front_z_mm is not None:
            set_z_limit(operation.parameters, "frontHeight", front_z_mm)
        if back_z_mm is not None:
            set_z_limit(operation.parameters, "backHeight", back_z_mm)
        print(name, "T", tool_number, "refused", refused[:8], "of", len(refused))


def add_extra_grooves(cam, bishop_cam):
    """Adds the two extra T8 passes right after Finish head, so the head is done before the body is cut."""
    bishop_setup = bishop_cam.setups.itemByName("Lathe turn blank")
    source = next(operation for operation in bishop_setup.allOperations if operation.name == GROOVE_SOURCE)
    setup = cam.setups.itemByName("Lathe turn blank")
    next_pass = next(operation for operation in setup.allOperations if operation.name == "Rough body")
    for name, front_z_mm, back_z_mm in EXTRA_GROOVES:
        operation_input = setup.operations.createInput(source.strategy)
        operation_input.tool = find_tool(cam, 8)
        operation = setup.operations.add(operation_input)
        operation.name = name
        copy_settings(source.parameters, operation.parameters)
        if front_z_mm is None:
            operation.parameters.itemByName("frontHeight_mode").expression = "'model front'"
        else:
            set_z_limit(operation.parameters, "frontHeight", front_z_mm)
        set_z_limit(operation.parameters, "backHeight", back_z_mm)
        if name in NO_LEAD_OUT:
            operation.parameters.itemByName("exit_sameAsEntry").expression = "false"
            operation.parameters.itemByName("exit_distance").expression = "0 mm"
        operation.moveBefore(next_pass)


def add_finial_neck_passes(cam):
    """Adds T5's two passes right after T8 cuts the crown's cone. Fusion needs T5 in the document's library first."""
    setup = cam.setups.itemByName("Lathe turn blank")
    operations = {operation.name: operation for operation in setup.allOperations}
    for name, source_name in FINIAL_NECK_SOURCES:
        source = operations[source_name]
        operation_input = setup.operations.createInput(source.strategy)
        operation_input.tool = find_tool(cam, 5)
        operation = setup.operations.add(operation_input)
        operation.name = name
        copy_settings(source.parameters, operation.parameters)
        set_z_limit(operation.parameters, "frontHeight", FINIAL_NECK_FRONT_Z_MM)
        set_z_limit(operation.parameters, "backHeight", FINIAL_NECK_BACK_Z_MM)
        settings = FINIAL_NECK_FEEDS | (FINIAL_NECK_ROUGH_STEPS if name.startswith("Rough") else {})
        for parameter_name, expression in settings.items():
            operation.parameters.itemByName(parameter_name).expression = expression
        operation.moveBefore(operations["Groove under flange"])
