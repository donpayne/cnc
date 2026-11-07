"""Fusion helpers that build the Queen's milling passes. Run through the Fusion MCP with the Queen's document active.

Features repeat every 45 deg of C, so each one is built once and repeated with a circular CAM pattern. All lengths are
mm in the model's frame, with the base at z 0 and G54 on the part axis at the finial's tip.
"""
import importlib
import math

import adsk.cam
import adsk.core
import adsk.fusion

import queen_flutes
import queen_scoops

importlib.reload(queen_flutes)
importlib.reload(queen_scoops)

MM_TO_CM = 0.1

T14_FEEDS = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "150 mm/min",
    "tool_feedEntry": "150 mm/min",
    "tool_feedExit": "150 mm/min",
    "tool_feedTransition": "150 mm/min",
    "tool_feedPlunge": "60 mm/min",
    "tool_feedRamp": "60 mm/min",
    "tool_coolant": "'flood'",
}

# B 90 on the crown: the floor slopes 18.5 deg, so the ball already cuts off its tip. The stem's lower band also slopes
# enough, and its end needs B 90, because the end is a radial cylinder. The upper band's floor is nearly parallel to
# the axis, so B 95 moves the contact 5 to 10 deg off the ball's tip, where surface speed is at least 5 m/min rather than 0.
# Leaning the other way, B 75 ran T14's neck 48 um into the top of the flute's radial run-out. Further this way, B 100 and
# up drive the holder's flange into the jaws at the diagonal C angles.
CROWN_B_DEG = 90.0
STEM_LOWER_B_DEG = 90.0
STEM_UPPER_B_DEG = 95.0

# Pass prefix, floor curves, low cap, high cap, B.
FLUTE_BANDS = {
    "Trace Crown Flute": (
        queen_flutes.CROWN_FLOOR,
        (queen_flutes.CROWN_LOWER_END, queen_flutes.CROWN_LOWER_EXIT_R_MM),
        (queen_flutes.CROWN_UPPER_END, queen_flutes.CROWN_UPPER_EXIT_R_MM),
        CROWN_B_DEG,
    ),
    "Trace Stem Upper": (
        queen_flutes.STEM_UPPER_FLOOR,
        None,
        (queen_flutes.STEM_UPPER_END, queen_flutes.STEM_UPPER_EXIT_R_MM),
        STEM_UPPER_B_DEG,
    ),
    "Trace Stem Lower": (
        queen_flutes.STEM_LOWER_FLOOR,
        (queen_flutes.STEM_LOWER_END, queen_flutes.STEM_LOWER_EXIT_R_MM),
        None,
        STEM_LOWER_B_DEG,
    ),
}


def active_design_and_cam():
    document = adsk.core.Application.get().activeDocument
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(document.products.itemByProductType("CAMProductType"))
    return design, cam


def find_tool(cam, tool_number):
    for tool in cam.documentToolLibrary:
        if tool.parameters.itemByName("tool_number").value.value == tool_number:
            return tool
    raise ValueError(f"no T{tool_number} in the document's tool library")


def set_expressions(params, expressions):
    for name, expression in expressions.items():
        params.itemByName(name).expression = expression


def tool_axis_lines(root, c_deg, b_deg):
    """Returns a line along the tool axis at this pose, and one along +Z for view X, so B and C come out predictable."""
    sketch = root.sketches.itemByName("Tool Axes")
    if sketch is None:
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Tool Axes"
    up = root.sketches.itemByName("Tool Axis Up")
    if up is None:
        up = root.sketches.add(root.xZConstructionPlane)
        up.name = "Tool Axis Up"
        up.sketchCurves.sketchLines.addByTwoPoints(
            up.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0)),
            up.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 2)),
        )
    b_rad, c_rad = math.radians(b_deg), math.radians(c_deg)
    start = sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0))
    end = sketch.modelToSketchSpace(
        adsk.core.Point3D.create(2 * math.sin(b_rad) * math.cos(c_rad), 2 * math.sin(b_rad) * math.sin(c_rad), 2 * math.cos(b_rad))
    )
    axis = next(
        (line for line in sketch.sketchCurves.sketchLines if line.endSketchPoint.geometry.distanceTo(end) < 1e-6),
        None,
    )
    if axis is None:
        axis = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    return axis, up.sketchCurves.sketchLines.item(0)


def set_tool_axis(params, axis_line, up_line):
    params.itemByName("overrideToolView").expression = "true"
    params.itemByName("view_orientation_mode").expression = "'axesZX'"
    params.itemByName("view_orientation_axisZ").value.value = [axis_line]
    params.itemByName("view_orientation_axisX").value.value = [up_line]


def add_path(sketch, tips_mm):
    """Draws connected lines through these points and returns them in order."""
    lines = sketch.sketchCurves.sketchLines
    to_sketch = lambda tip: sketch.modelToSketchSpace(adsk.core.Point3D.create(tip[0] * MM_TO_CM, tip[1] * MM_TO_CM, tip[2] * MM_TO_CM))
    previous = sketch.sketchPoints.add(to_sketch(tips_mm[0]))
    curves = []
    for tip in tips_mm[1:]:
        line = lines.addByTwoPoints(previous, to_sketch(tip))
        previous = line.endSketchPoint
        curves.append(line)
    return curves


def flute_paths(floor, low_cap, high_cap):
    """Roughing steps from the air end inward, then finish cuts. Directions make each wall a climb cut."""
    enters_from_high_end = low_cap is None
    paths = []
    for depth_mm in queen_flutes.ROUGH_DEPTHS_ABOVE_FLOOR_MM:
        path = queen_flutes.rough_path(floor, depth_mm, low_cap, high_cap)
        paths.append(list(reversed(path)) if enters_from_high_end else path)
    for side_deg in queen_flutes.FINISH_SIDES_DEG:
        path = queen_flutes.finish_path(floor, side_deg, low_cap, high_cap)
        paths.append(list(reversed(path)) if side_deg < 0 else path)
    return paths


def add_flute_sketch(root, prefix, c_deg):
    """One sketch per flute, with one list of curves per cut."""
    floor, low_cap, high_cap, b_deg = FLUTE_BANDS[prefix]
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = f"{prefix} {c_deg:03d}"
    sketch.isComputeDeferred = True
    chains = [add_path(sketch, [queen_flutes.tip_of(center, c_deg, b_deg) for center in path]) for path in flute_paths(floor, low_cap, high_cap)]
    sketch.isComputeDeferred = False
    return chains


def set_chains(params, parameter_name, chains):
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    for curves in chains:
        chain = selections.createNewChainSelection()
        # Listing every curve matters: given only the first, a chain stopped at the next joint.
        chain.inputGeometry = list(curves)
        chain.isOpen = True
        chain.isReverted = False
    selection_value.applyCurveSelections(selections)


def add_trace_pass(cam, setup, root, name, tool_number, chains, c_deg, b_deg, feeds):
    """A trace of these sketch chains, with no stock and no leads: the sketched paths already enter and leave in air."""
    axis, up = tool_axis_lines(root, c_deg, b_deg)
    operation_input = setup.operations.createInput("trace")
    operation_input.tool = find_tool(cam, tool_number)
    params = operation_input.parameters
    set_tool_axis(params, axis, up)
    set_chains(params, "curves", chains)
    set_expressions(params, {
        "tolerance": "0.002 mm",
        # The default measures from the surface top, r 19 on this part, and plunges from there at the plunge feed.
        "feedHeight_mode": "'from contour'",
        "feedHeight_offset": "1 mm",
        "retractHeight_offset": "1 mm",
        "useStockToLeave": "false",
        "doLeadIn": "false",
        "doLeadOut": "false",
    })
    operation = setup.operations.add(operation_input)
    operation.name = name
    set_expressions(operation.parameters, feeds)
    return operation


def add_flute_pass(cam, setup, root, prefix, c_deg):
    chains = add_flute_sketch(root, prefix, c_deg)
    return add_trace_pass(cam, setup, root, f"{prefix} {c_deg:03d}", 14, chains, c_deg, FLUTE_BANDS[prefix][3], T14_FEEDS)


T10_FEEDS = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "120 mm/min",
    "tool_feedEntry": "120 mm/min",
    "tool_feedExit": "120 mm/min",
    "tool_feedTransition": "120 mm/min",
    "tool_feedPlunge": "40 mm/min",
    "tool_feedRamp": "40 mm/min",
    "tool_coolant": "'flood'",
}

T3_FEEDS = {
    "tool_spindleSpeed": "8000 rpm",
    "tool_rampSpindleSpeed": "8000 rpm",
    "tool_feedCutting": "400 mm/min",
    "tool_feedEntry": "400 mm/min",
    "tool_feedExit": "400 mm/min",
    "tool_feedTransition": "400 mm/min",
    "tool_feedPlunge": "200 mm/min",
    "tool_feedRamp": "200 mm/min",
    "tool_coolant": "'flood'",
}
T4_FEEDS = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "305 mm/min",
    "tool_feedEntry": "305 mm/min",
    "tool_feedExit": "305 mm/min",
    "tool_feedTransition": "305 mm/min",
    "tool_feedPlunge": "150 mm/min",
    "tool_feedRamp": "150 mm/min",
    "tool_coolant": "'flood'",
}


def _scoop_chains(root, name, paths, ball_radius_mm, c_deg):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    sketch.isComputeDeferred = True
    chains = [add_path(sketch, [queen_scoops.tip_of(*center, ball_radius_mm, c_deg) for center in path]) for path in paths]
    sketch.isComputeDeferred = False
    return chains


def add_scoop_rough(cam, setup, root, c_deg):
    name = f"Rough Scoop {c_deg:03d}"
    chains = _scoop_chains(root, name, queen_scoops.rough_strokes(), queen_scoops.T3_RADIUS_MM, c_deg)
    return add_trace_pass(cam, setup, root, name, 3, chains, c_deg, queen_scoops.TILT_B_DEG, T3_FEEDS)


def add_scoop_finish(cam, setup, root, c_deg):
    name = f"Finish Scoop {c_deg:03d}"
    chains = _scoop_chains(root, name, [queen_scoops.finish_path()], queen_scoops.T4_RADIUS_MM, c_deg)
    return add_trace_pass(cam, setup, root, name, 4, chains, c_deg, queen_scoops.TILT_B_DEG, T4_FEEDS)


# The faces that aren't cylinders, so Fusion follows them, as indices at the first sector. The rim and inner end sit on
# C 0 and the crest between two scoops, on C 22.5.
RIM_FACE = 265
INNER_FACE = 292
CREST_FACES = (271, 108, 117)
CREST_OFFSET_DEG = 22.5
RIM_B_DEG = 75.0
# The API has no enum for this value.
AVOID_MACHINE_MODE = 0


def queen_body(root):
    return root.bRepBodies.itemByName("Queen")


def turned_face_index(body, template_index, turn_deg):
    """The face this many degrees around the part from the template, which it matches in area."""
    template = body.faces.item(template_index)
    turn_rad = math.radians(turn_deg)
    x_cm = template.centroid.x * math.cos(turn_rad) - template.centroid.y * math.sin(turn_rad)
    y_cm = template.centroid.x * math.sin(turn_rad) + template.centroid.y * math.cos(turn_rad)
    wanted = adsk.core.Point3D.create(x_cm, y_cm, template.centroid.z)
    candidates = [
        index for index in range(body.faces.count)
        if abs(body.faces.item(index).area - template.area) < 0.25 * template.area
    ]
    return min(candidates, key=lambda index: body.faces.item(index).centroid.distanceTo(wanted))


def other_faces(body, owned_faces):
    """Scallop machines every face it isn't told to avoid, so nearby faces alone leave the rest of the part in the pass."""
    owned_ids = {face.tempId for face in owned_faces}
    return [face for face in body.faces if face.tempId not in owned_ids]


def set_avoid_faces(params, faces):
    selection_value = params.itemByName("checkSurfaceSelectionSets").value
    groups = selection_value.getMachineAvoidGroups()
    group = groups.createNewMachineAvoidDirectSelectionGroup()
    group.inputGeometry = list(faces)
    # New groups come out as Machine and do nothing until they're set to Avoid.
    group.machineMode = AVOID_MACHINE_MODE
    selection_value.applyMachineAvoidGroups(groups)


def add_surface_pass(cam, setup, root, name, tool_number, owned_indices, c_deg, b_deg, stepover_mm, feeds):
    """A scallop of these faces alone, with every neighbour avoided so a finished face isn't touched again."""
    body = queen_body(root)
    owned = [body.faces.item(index) for index in owned_indices]
    axis, up = tool_axis_lines(root, c_deg, b_deg)
    operation_input = setup.operations.createInput("scallop")
    operation_input.tool = find_tool(cam, tool_number)
    params = operation_input.parameters
    set_tool_axis(params, axis, up)
    set_avoid_faces(params, other_faces(body, owned))
    set_expressions(params, {
        "tolerance": "0.002 mm",
        "stepover": f"{stepover_mm} mm",
        "useStockToLeave": "false",
    })
    operation = setup.operations.add(operation_input)
    operation.name = name
    set_expressions(operation.parameters, feeds)
    return operation


def add_crown_sector(cam, setup, root, c_deg):
    """All five passes of one sector, in the order they'll run within a stage."""
    body = queen_body(root)
    turned = lambda index: turned_face_index(body, index, c_deg)
    crest_c_deg = c_deg + CREST_OFFSET_DEG
    tilt_deg = queen_scoops.TILT_B_DEG
    return [
        add_scoop_rough(cam, setup, root, c_deg),
        add_scoop_finish(cam, setup, root, c_deg),
        add_surface_pass(cam, setup, root, f"Finish Rim {c_deg:03d}", 4, (turned(RIM_FACE),), c_deg, RIM_B_DEG, 0.15, T4_FEEDS),
        add_surface_pass(cam, setup, root, f"Detail Inner {c_deg:03d}", 10, (turned(INNER_FACE),), c_deg, tilt_deg, 0.08, T10_FEEDS),
        add_surface_pass(
            cam, setup, root, f"Detail Crest {int(crest_c_deg):03d}", 10, tuple(turned(index) for index in CREST_FACES),
            crest_c_deg, tilt_deg, 0.08, T10_FEEDS,
        ),
    ]


def generate(cam, operations):
    collection = adsk.core.ObjectCollection.create()
    for operation in operations:
        collection.add(operation)
    cam.generateToolpath(collection)


# The pattern's angle is the step between instances, not the total. At 360 deg every instance lands on C 0, which cuts
# one feature 8 times with no warning from Fusion.
PATTERN_STEP_EXPRESSION = "45 deg"

# Far from the vise first. The tool order follows from that: T3, T4 and T10 on the crown, then T14 down the flutes.
PATTERN_STAGES = (
    "Rough Scoop", "Finish Scoop", "Finish Rim", "Detail Inner", "Detail Crest",
    "Trace Crown Flute", "Trace Stem Upper", "Trace Stem Lower",
)


def _pattern_ids(setup):
    return {setup.patterns.item(index).operationId for index in range(setup.patterns.count)}


def pattern_around_c(setup, seed_pattern, operation, stage):
    """Moves a pass into a copy of a pattern. Fusion's API can't create a pattern, so the first has to be made by hand."""
    step = seed_pattern.parameters.itemByName("angle").expression
    if step != PATTERN_STEP_EXPRESSION:
        raise ValueError(f"the seed pattern steps {step}, and needs {PATTERN_STEP_EXPRESSION}")
    known_ids = _pattern_ids(setup)
    seed_pattern.duplicate()
    new_pattern = next(setup.patterns.item(index) for index in range(setup.patterns.count) if setup.patterns.item(index).operationId not in known_ids)
    copied_pass = new_pattern.operations.item(0)
    operation.moveInto(new_pattern)
    copied_pass.deleteMe()
    new_pattern.name = f"{stage} x8"
    return new_pattern


def order_patterns(setup):
    following = setup.patterns.itemByName(f"{PATTERN_STAGES[-1]} x8")
    for stage in reversed(PATTERN_STAGES[:-1]):
        pattern = setup.patterns.itemByName(f"{stage} x8")
        pattern.moveBefore(following)
        following = pattern
