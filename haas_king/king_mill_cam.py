"""Fusion helpers that build the King's crown, notch, flute and shaft passes in `Mill King crown and cup`.

Run through the Fusion MCP with the King's document active, after putting FOLDER on sys.path. Each feature is built
once, on its seed side, from the paths in king_mill.py. The other seven come from circular CAM patterns.
"""
import importlib
import math

import adsk.cam
import adsk.core
import adsk.fusion

import king_cup_cam
import king_mill

importlib.reload(king_mill)

SETUP_NAME = "Mill King crown and cup"
MM_TO_CM = 0.1

T11_FEEDS = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "200 mm/min",
    "tool_feedEntry": "200 mm/min",
    "tool_feedExit": "200 mm/min",
    "tool_feedTransition": "200 mm/min",
    # Every plunge is at the entry point, in air.
    "tool_feedPlunge": "200 mm/min",
    "tool_feedRamp": "200 mm/min",
    "tool_coolant": "'flood'",
}


def point_mm(sketch, x_mm, y_mm, z_mm):
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(x_mm * MM_TO_CM, y_mm * MM_TO_CM, z_mm * MM_TO_CM))


def add_flute_sketch(root, name, stock_mm):
    """In from air, most of the way round the circle T11's center follows, and back out, at the flute's bottom height.

    A closed circle made Fusion cut the circle and the entry line as separate pieces, plunging on the circle. Leaving
    out the arc next to the entry is safe, because the head has no metal on the flute's outer side.
    """
    old = root.sketches.itemByName(name)
    if old is not None:
        old.deleteMe()
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    z_mm = king_mill.FLUTE_BOTTOM_Z_MM
    points = [point_mm(sketch, x_mm, y_mm, z_mm) for x_mm, y_mm in king_mill.flute_tool_center_path(stock_mm)]
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    entry = lines.addByTwoPoints(points[0], points[1])
    first_half = arcs.addByThreePoints(entry.endSketchPoint, points[2], points[3])
    second_half = arcs.addByThreePoints(_end_at(first_half, points[3]), points[4], points[5])
    exit_line = lines.addByTwoPoints(_end_at(second_half, points[5]), points[6])
    return [entry, first_half, second_half, exit_line]


def _end_at(arc, point):
    """The arc's end sketch point nearest this point, since an arc's start and end can come out either way round."""
    return min((arc.startSketchPoint, arc.endSketchPoint), key=lambda end: end.geometry.distanceTo(point))


def set_open_chain(params, curves):
    selection_value = params.itemByName("contours").value
    selections = selection_value.getCurveSelections()
    selections.clear()
    chain = selections.createNewChainSelection()
    # Listing every curve matters: given only the first, a chain stopped at the next joint.
    chain.inputGeometry = list(curves)
    chain.isOpen = True
    chain.isReverted = False
    selection_value.applyCurveSelections(selections)


def add_flute_pass(cam, setup, root, name, stock_mm, settings):
    curves = add_flute_sketch(root, f"{name} Path", stock_mm)
    operation_input = setup.operations.createInput("contour2d")
    operation_input.tool = king_cup_cam.find_tool(cam, 11)
    operation = setup.operations.add(operation_input)
    operation.name = name
    params = operation.parameters
    set_open_chain(params, curves)
    king_cup_cam.set_expressions(params, T11_FEEDS)
    height_mm = king_mill.FLUTE_TOP_Z_MM - king_mill.FLUTE_BOTTOM_Z_MM
    king_cup_cam.set_expressions(params, {
        # The sketch is the tool center's path, so Fusion mustn't offset it again.
        "compensationType": "'off'",
        "doLeadIn": "false",
        "doLeadOut": "false",
        "useStockToLeave": "false",
        "tolerance": "0.002 mm",
        "bottomHeight_mode": "'from contour'",
        "bottomHeight_offset": "0 mm",
        "topHeight_mode": "'from contour'",
        "topHeight_offset": f"{height_mm:.3f} mm",
        # Fusion's default 5 mm feed height, at the plunge feed, made the rough pass 7 min for one flute.
        "feedHeight_mode": "'from top'",
        "feedHeight_offset": "0.5 mm",
    })
    king_cup_cam.set_expressions(params, settings)
    king_cup_cam.generate(cam, operation)
    return operation


def add_flute_passes():
    design, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    root = design.rootComponent
    rough = add_flute_pass(cam, setup, root, "Rough Flute", king_mill.FLUTE_ROUGH_STOCK_MM, {
        "doMultipleDepths": "true", "maximumStepdown": "0.25 mm", "nullPass": "false",
    })
    # One full-depth pass, cut twice, so the wall comes out the same top to bottom.
    finish = add_flute_pass(cam, setup, root, "Finish Flute", 0.0, {"doMultipleDepths": "false", "nullPass": "true"})
    return rough, finish


T4_FEEDS = dict(king_cup_cam.FEEDS[4])
# The notch's own faces at the C 22.5 seed: bottom, two walls, the r 0.278 rounds on every edge, and the rim bead's two
# end caps.
NOTCH_FACES = (72, 134, 216, 218, 221, 217, 219, 222, 220, 25, 26)
# The API has no enum for this value.
AVOID_MACHINE_MODE = 0


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
        up.sketchCurves.sketchLines.addByTwoPoints(point_mm(up, 0, 0, 0), point_mm(up, 0, 0, 20))
    b_rad, c_rad = math.radians(b_deg), math.radians(c_deg)
    end = point_mm(sketch, 20 * math.sin(b_rad) * math.cos(c_rad), 20 * math.sin(b_rad) * math.sin(c_rad), 20 * math.cos(b_rad))
    axis = next((line for line in sketch.sketchCurves.sketchLines if line.endSketchPoint.geometry.distanceTo(end) < 1e-6), None)
    if axis is None:
        axis = sketch.sketchCurves.sketchLines.addByTwoPoints(point_mm(sketch, 0, 0, 0), end)
    return axis, up.sketchCurves.sketchLines.item(0)


def set_tool_axis(params, c_deg, b_deg, root):
    axis, up = tool_axis_lines(root, c_deg, b_deg)
    params.itemByName("overrideToolView").expression = "true"
    params.itemByName("view_orientation_mode").expression = "'axesZX'"
    params.itemByName("view_orientation_axisZ").value.value = [axis]
    params.itemByName("view_orientation_axisX").value.value = [up]


def add_polyline(sketch, points_mm):
    lines = sketch.sketchCurves.sketchLines
    previous = sketch.sketchPoints.add(point_mm(sketch, *points_mm[0]))
    curves = []
    for point in points_mm[1:]:
        line = lines.addByTwoPoints(previous, point_mm(sketch, *point))
        previous = line.endSketchPoint
        curves.append(line)
    return curves


def set_chains(params, parameter_name, chains):
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    for curves in chains:
        chain = selections.createNewChainSelection()
        chain.inputGeometry = list(curves)
        chain.isOpen = True
        chain.isReverted = False
    selection_value.applyCurveSelections(selections)


def fresh_sketch(root, name):
    old = root.sketches.itemByName(name)
    if old is not None:
        old.deleteMe()
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    return sketch


def add_trace_pass(cam, setup, root, name, tool_number, chains, c_deg, b_deg, feeds):
    """A trace of sketched tip paths, with no stock and no leads: the paths already start and end in air."""
    operation_input = setup.operations.createInput("trace")
    operation_input.tool = king_cup_cam.find_tool(cam, tool_number)
    params = operation_input.parameters
    set_tool_axis(params, c_deg, b_deg, root)
    set_chains(params, "curves", chains)
    king_cup_cam.set_expressions(params, {
        "tolerance": "0.002 mm",
        # The default measures from the stock's top and plunges from there at the plunge feed.
        "feedHeight_mode": "'from contour'",
        "feedHeight_offset": "1 mm",
        "retractHeight_offset": "1 mm",
        "useStockToLeave": "false",
        "doLeadIn": "false",
        "doLeadOut": "false",
    })
    operation = setup.operations.add(operation_input)
    operation.name = name
    king_cup_cam.set_expressions(operation.parameters, feeds)
    king_cup_cam.generate(cam, operation)
    return operation


def add_notch_rough(cam, setup, root):
    """One chain per level, because a link from one level down to the next would cut through the wall."""
    sketch = fresh_sketch(root, "Rough Notch Path")
    sketch.isComputeDeferred = True
    chains = []
    for strokes in king_mill.notch_rough_levels():
        points = [point for stroke in strokes for point in stroke]
        chains.append(add_polyline(sketch, [king_mill.tip_from_center(point, king_mill.NOTCH_UP) for point in points]))
    sketch.isComputeDeferred = False
    return add_trace_pass(cam, setup, root, "Rough Notch", 4, chains, king_mill.NOTCH_C_DEG, king_mill.NOTCH_B_DEG, T4_FEEDS)


def set_avoid_faces(params, faces):
    selection_value = params.itemByName("checkSurfaceSelectionSets").value
    groups = selection_value.getMachineAvoidGroups()
    group = groups.createNewMachineAvoidDirectSelectionGroup()
    group.inputGeometry = list(faces)
    # New groups come out as Machine and do nothing until they're set to Avoid.
    group.machineMode = AVOID_MACHINE_MODE
    selection_value.applyMachineAvoidGroups(groups)


def add_notch_finish(cam, setup, root, stepover_mm=0.15):
    """A scallop of the notch's own faces with every other face avoided, so it follows the edge rounds too."""
    king = root.bRepBodies.itemByName("King")
    owned_ids = {king.faces.item(index).tempId for index in NOTCH_FACES}
    operation_input = setup.operations.createInput("scallop")
    operation_input.tool = king_cup_cam.find_tool(cam, 4)
    params = operation_input.parameters
    set_tool_axis(params, king_mill.NOTCH_C_DEG, king_mill.NOTCH_B_DEG, root)
    set_avoid_faces(params, [face for face in king.faces if face.tempId not in owned_ids])
    king_cup_cam.set_expressions(params, {"tolerance": "0.002 mm", "stepover": f"{stepover_mm} mm", "useStockToLeave": "false"})
    operation = setup.operations.add(operation_input)
    operation.name = "Finish Notch"
    king_cup_cam.set_expressions(operation.parameters, T4_FEEDS)
    king_cup_cam.generate(cam, operation)
    return operation


def add_notch_passes():
    design, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    root = design.rootComponent
    return add_notch_rough(cam, setup, root), add_notch_finish(cam, setup, root)


T2_FEEDS = {
    "tool_spindleSpeed": "7600 rpm",
    "tool_rampSpindleSpeed": "7600 rpm",
    "tool_feedCutting": "762 mm/min",
    "tool_feedEntry": "762 mm/min",
    "tool_feedExit": "762 mm/min",
    "tool_feedTransition": "762 mm/min",
    # The only plunge is at the first stroke's start, in air.
    "tool_feedPlunge": "400 mm/min",
    "tool_feedRamp": "400 mm/min",
    "tool_coolant": "'flood'",
}
# The lathe leaves up to 0.47 on a facet, so the semi takes it in two strokes. The finish stroke runs twice, so the
# second takes off whatever the first left as T2 sprang.
FACET_SEMI_OFFSETS_MM = (0.3, 0.1)
FACET_FINISH_OFFSETS_MM = (0.0, 0.0)


def add_facet_pass(cam, setup, root, name, offsets_mm):
    sketch = fresh_sketch(root, f"{name} Path")
    chain = add_polyline(sketch, king_mill.facet_tip_path(offsets_mm))
    return add_trace_pass(cam, setup, root, name, 2, [chain], 0.0, king_mill.FACET_B_DEG, T2_FEEDS)


def add_facet_passes():
    design, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    root = design.rootComponent
    return (
        add_facet_pass(cam, setup, root, "Semi Facet", FACET_SEMI_OFFSETS_MM),
        add_facet_pass(cam, setup, root, "Finish Facet", FACET_FINISH_OFFSETS_MM),
    )


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


def add_waist_pass():
    """T10's strokes under the C 0 facet: one chain, since every link between strokes is at a stroke's end, in air."""
    design, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    root = design.rootComponent
    sketch = fresh_sketch(root, "Waist Path")
    chain = add_polyline(sketch, king_mill.waist_tip_path())
    return add_trace_pass(cam, setup, root, "Waist", 10, [chain], 0.0, king_mill.WAIST_B_DEG, T10_FEEDS)


# The lathe leaves up to 0.73 on a side, at its bottom corners, so the semi takes it in two contours. The finish runs
# twice, the second as a spring pass.
OCTAGON_SEMI_OFFSETS_MM = (0.35, 0.1)
OCTAGON_FINISH_OFFSETS_MM = (0.0, 0.0)
# T2 and T4 lie along +Y, flat to the C 0 side's rulings.
OCTAGON_C_DEG = 90.0
OCTAGON_B_DEG = 90.0


def add_octagon_pass(cam, setup, root, name, tool_number, chains_points, feeds):
    sketch = fresh_sketch(root, f"{name} Path")
    sketch.isComputeDeferred = True
    chains = [add_polyline(sketch, points) for points in chains_points]
    sketch.isComputeDeferred = False
    return add_trace_pass(cam, setup, root, name, tool_number, chains, OCTAGON_C_DEG, OCTAGON_B_DEG, feeds)


def add_octagon_passes():
    design, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    root = design.rootComponent

    def t2_chains(offsets_mm):
        return [
            king_mill.octagon_tip_chain(king_mill.T2_RADIUS_MM, offset_mm, king_mill.OCTAGON_T2_CONTACT_Z_MM,
                                        king_mill.OCTAGON_T2_TIP_Y_MM, True)
            for offset_mm in offsets_mm
        ]

    bottom_strip, top_strip = king_mill.OCTAGON_T4_STRIPS_Z_MM
    strips = [
        king_mill.octagon_tip_chain(king_mill.T4_RADIUS_MM, 0.0, bottom_strip, king_mill.OCTAGON_T4_TIP_Y_MM, False),
        king_mill.octagon_tip_chain(king_mill.T4_RADIUS_MM, 0.0, top_strip, king_mill.OCTAGON_T4_TIP_Y_MM, True),
    ]
    return (
        add_octagon_pass(cam, setup, root, "Semi Octagon", 2, t2_chains(OCTAGON_SEMI_OFFSETS_MM), T2_FEEDS),
        add_octagon_pass(cam, setup, root, "Finish Octagon", 2, t2_chains(OCTAGON_FINISH_OFFSETS_MM), T2_FEEDS),
        add_octagon_pass(cam, setup, root, "Octagon Strips", 4, strips, T4_FEEDS),
    )


# Every seed pass repeats around the part in its own circular pattern, in cutting order. Fusion's API can't create a
# pattern, so the first, on Rough Flute, is made by hand (circular, Z axis, 45 deg x 8) and the rest are its copies.
SEED_PASSES = (
    "Rough Flute", "Finish Flute", "Rough Notch", "Finish Notch", "Semi Facet", "Finish Facet", "Waist",
    "Semi Octagon", "Finish Octagon", "Octagon Strips",
)
PATTERN_STEP_DEG = 45.0
PATTERN_INSTANCES = 8


def check_seed_pattern(pattern):
    """Refuses a pattern that would cut the wrong places: a circular angle is the step, so 360 stacks all 8 in one."""
    params = pattern.parameters
    pattern_type = params.itemByName("patternType").expression
    step_deg = params.itemByName("angle").value.value
    instances = int(params.itemByName("numberOfInstances").value.value)
    is_right_pattern = pattern_type == "'circular'" and abs(step_deg - PATTERN_STEP_DEG) < 1e-6 and instances == PATTERN_INSTANCES
    if not is_right_pattern:
        raise ValueError(f"seed pattern is {pattern_type}, {step_deg} deg x {instances}; needs circular, 45 deg x 8")


def _pattern_ids(setup):
    return {setup.patterns.item(index).operationId for index in range(setup.patterns.count)}


def pattern_pass(setup, seed_pattern, operation):
    """Moves a pass into a copy of the seed pattern, placed where the pass was, and returns the copy."""
    known_ids = _pattern_ids(setup)
    seed_pattern.duplicate()
    new_pattern = next(
        setup.patterns.item(index) for index in range(setup.patterns.count) if setup.patterns.item(index).operationId not in known_ids
    )
    copied_pass = new_pattern.operations.item(0)
    new_pattern.moveBefore(operation)
    operation.moveInto(new_pattern)
    copied_pass.deleteMe()
    new_pattern.name = f"{operation.name} x8"
    return new_pattern


def pattern_all_seeds():
    """Puts each seed pass not yet in a pattern into a copy of the seed pattern, which holds Rough Flute."""
    _, cam = king_cup_cam.active_design_and_cam()
    setup = cam.setups.itemByName(SETUP_NAME)
    seed_pattern = next(
        setup.patterns.item(index) for index in range(setup.patterns.count)
        if setup.patterns.item(index).operations.item(0).name == SEED_PASSES[0]
    )
    check_seed_pattern(seed_pattern)
    seed_pattern.name = f"{SEED_PASSES[0]} x8"
    top_level = {setup.children.item(index).name: setup.children.item(index) for index in range(setup.children.count)}
    return [pattern_pass(setup, seed_pattern, top_level[name]) for name in SEED_PASSES[1:] if name in top_level]


POST_URL = "system://haas next generation.cps"
NC_OUTPUT_FOLDER = "/Users/don.payne/src/cnc/haas_king/nc"
MILL_SETUPS = ("Mill King rough cup", "Mill King cup rings", SETUP_NAME)


def post_mill(file_name="king_mill"):
    """Posts the three mill setups through a throwaway NC program, then removes it, as on the Rook."""
    _, cam = king_cup_cam.active_design_and_cam()
    program_input = cam.ncPrograms.createInput()
    program_input.displayName = file_name
    params = program_input.parameters
    params.itemByName("nc_program_filename").value.value = file_name
    params.itemByName("nc_program_output_folder").value.value = NC_OUTPUT_FOLDER
    params.itemByName("nc_program_openInEditor").value.value = False
    params.itemByName("nc_program_unit").expression = "'Millimeters'"
    program_input.operations = [cam.setups.itemByName(name) for name in MILL_SETUPS]
    program = cam.ncPrograms.add(program_input)
    program.parameters.itemByName("nc_program_post").value.value = POST_URL
    post_params = program.postParameters
    post_params.itemByName("metric").value.value = True
    # 9999 is the post's value for Automatic.
    post_params.itemByName("useSmoothing").value.value = "9999"
    program.updatePostParameters(post_params)
    is_posted = program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())
    program.deleteMe()
    return is_posted
