"""Fusion helpers that build the Rook's milling passes. Run through the Fusion MCP with the Rook document active.

Octagon sides are named by the angle of their outward normal: 0 is +X and 90 is +Y. All lengths are mm in the model's
frame, with the base at z 0 and G54 on the part axis at z 56.788.
"""
import math

import adsk.cam
import adsk.core
import adsk.fusion

MM_TO_CM = 0.1
TOP_Z_MM = 56.788
SIDE_ANGLES_DEG = (0, 45, 90, 135, 180, 225, 270, 315)

# The side profile at 73%, read from the section through a flat: slope, then a tangent arc, then the flat.
SLOPE_BOTTOM = (9.874, 19.104)
SLOPE_TOP = (8.837, 22.182)
WAIST_CENTER = (51.679, 36.612)
WAIST_RADIUS_MM = 45.207
FLAT_APOTHEM_MM = 6.472
WAIST_TOP_Z_MM = 36.612

# T2's end cuts the flat from here up to the first step, so the side flank stops here.
TOOL_DIAMETER_T2_MM = 6.35
FIRST_STEP_Z_MM = 47.701
FLANK_TOP_Z_MM = FIRST_STEP_Z_MM - TOOL_DIAMETER_T2_MM
# The rim of the side's lowest edge is 4.02 mm from the flat's center, and the tip runs 1 mm past it.
FLANK_TIP_PAST_AXIS_MM = 5.02


def active_design_and_cam():
    app = adsk.core.Application.get()
    document = app.activeDocument
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(document.products.itemByProductType("CAMProductType"))
    return design, cam


def find_tool(cam, tool_number):
    for tool in cam.documentToolLibrary:
        if tool.parameters.itemByName("tool_number").value.value == tool_number:
            return tool
    raise ValueError(f"no T{tool_number} in the document's tool library")


def side_directions(angle_deg):
    """Returns the side's outward normal and its tangent, each as (x, y)."""
    angle_rad = math.radians(angle_deg)
    normal = (math.cos(angle_rad), math.sin(angle_rad))
    return normal, (-normal[1], normal[0])


def world_point(normal, apothem_mm, z_mm, along_tangent_mm=0.0):
    tangent = (-normal[1], normal[0])
    return adsk.core.Point3D.create(
        (normal[0] * apothem_mm + tangent[0] * along_tangent_mm) * MM_TO_CM,
        (normal[1] * apothem_mm + tangent[1] * along_tangent_mm) * MM_TO_CM,
        z_mm * MM_TO_CM,
    )


def plane_through_axis(root, angle_deg):
    """The construction plane holding the part axis and this side's normal. Opposite sides share one."""
    folded_deg = angle_deg % 180
    if folded_deg == 0:
        return root.xZConstructionPlane
    if folded_deg == 90:
        return root.yZConstructionPlane
    name = f"Side Plane {folded_deg:03d}"
    existing = root.constructionPlanes.itemByName(name)
    if existing:
        return existing
    plane_input = root.constructionPlanes.createInput()
    plane_input.setByAngle(root.zConstructionAxis, adsk.core.ValueInput.createByString(f"{folded_deg} deg"), root.xZConstructionPlane)
    plane = root.constructionPlanes.add(plane_input)
    plane.name = name
    return plane


def add_flank_sketch(root, angle_deg):
    """Draws the side's profile from its top down, so the pieces share points and chain as one."""
    name = f"Flank Profile {angle_deg:03d}"
    existing = root.sketches.itemByName(name)
    if existing:
        return existing
    normal, _tangent = side_directions(angle_deg)
    sketch = root.sketches.add(plane_through_axis(root, angle_deg))
    sketch.name = name

    def to_sketch(apothem_mm, z_mm):
        return sketch.modelToSketchSpace(world_point(normal, apothem_mm, z_mm))

    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    flat = lines.addByTwoPoints(to_sketch(FLAT_APOTHEM_MM, FLANK_TOP_Z_MM), to_sketch(FLAT_APOTHEM_MM, WAIST_TOP_Z_MM))
    chord_z_mm = (WAIST_TOP_Z_MM + SLOPE_TOP[1]) / 2
    chord_apothem_mm = WAIST_CENTER[0] - math.sqrt(WAIST_RADIUS_MM ** 2 - (chord_z_mm - WAIST_CENTER[1]) ** 2)
    arc = arcs.addByThreePoints(flat.endSketchPoint, to_sketch(chord_apothem_mm, chord_z_mm), to_sketch(*SLOPE_TOP))
    target = to_sketch(*SLOPE_TOP)
    arc_end = min((arc.startSketchPoint, arc.endSketchPoint), key=lambda point: point.geometry.distanceTo(target))
    lines.addByTwoPoints(arc_end, to_sketch(*SLOPE_BOTTOM))
    return sketch


def add_axis_line(root, angle_deg):
    """A line from the part axis toward the side, used to set a pass's tool axis."""
    sketch = root.sketches.itemByName("Tool Axes")
    if sketch is None:
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Tool Axes"
    normal, _tangent = side_directions(angle_deg)
    start = sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0))
    end = sketch.modelToSketchSpace(adsk.core.Point3D.create(normal[0] * 2, normal[1] * 2, 0))
    for line in sketch.sketchCurves.sketchLines:
        if line.endSketchPoint.geometry.distanceTo(end) < 1e-6 and line.startSketchPoint.geometry.distanceTo(start) < 1e-6:
            return line
    return sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)


def up_axis_line(root):
    """A line along +Z, used as every side pass's view X, so B and C come out predictable."""
    sketch = root.sketches.itemByName("Tool Axis Up")
    if sketch is None:
        sketch = root.sketches.add(root.xZConstructionPlane)
        sketch.name = "Tool Axis Up"
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0)),
            sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 2)),
        )
    return sketch.sketchCurves.sketchLines.item(0)


def set_tool_axis(params, axis_line, up_line):
    params.itemByName("overrideToolView").expression = "true"
    params.itemByName("view_orientation_mode").expression = "'axesZX'"
    params.itemByName("view_orientation_axisZ").value.value = [axis_line]
    params.itemByName("view_orientation_axisX").value.value = [up_line]


def set_chain(params, parameter_name, curves, is_reverted):
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    chain = selections.createNewChainSelection()
    # Listing every curve matters: given only the first, the chain stopped at the next joint.
    chain.inputGeometry = list(curves)
    chain.isOpen = True
    chain.isReverted = is_reverted
    selection_value.applyCurveSelections(selections)


def set_expressions(params, expressions):
    for name, expression in expressions.items():
        params.itemByName(name).expression = expression


T2_FEEDS = {
    "tool_spindleSpeed": "7600 rpm",
    "tool_rampSpindleSpeed": "7600 rpm",
    "tool_feedCutting": "762 mm/min",
    "tool_feedEntry": "762 mm/min",
    "tool_feedExit": "762 mm/min",
    "tool_feedTransition": "762 mm/min",
    "tool_feedPlunge": "200 mm/min",
    "tool_feedRamp": "400 mm/min",
    "tool_coolant": "'flood'",
}


POST_URL = "system://haas next generation.cps"
NC_OUTPUT_FOLDER = "/Users/don.payne/src/cnc/haas_rook/nc"


def post_operations(cam, operations, file_name, output_folder=NC_OUTPUT_FOLDER):
    """Posts passes through a throwaway NC program, then removes it, so the document keeps only the real one."""
    program_input = cam.ncPrograms.createInput()
    program_input.displayName = file_name
    params = program_input.parameters
    params.itemByName("nc_program_filename").value.value = file_name
    params.itemByName("nc_program_output_folder").value.value = output_folder
    params.itemByName("nc_program_openInEditor").value.value = False
    params.itemByName("nc_program_unit").expression = "'Millimeters'"
    program_input.operations = operations
    program = cam.ncPrograms.add(program_input)
    program.parameters.itemByName("nc_program_post").value.value = POST_URL
    post_params = program.postParameters
    post_params.itemByName("metric").value.value = True
    # 9999 is the post's value for Automatic, as on the Knight.
    post_params.itemByName("useSmoothing").value.value = "9999"
    program.updatePostParameters(post_params)
    is_posted = program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())
    program.deleteMe()
    return is_posted


# Steps under the head at 73%. T2 comes in end-on, with the top of the tool touching each underside, so the tool's
# center runs one radius below it. The last two passes at each level are the finish and its spring pass.
STEP_LEVELS = (
    # (underside z, roughing depths from the axis, wall apothem)
    (49.579, (9.0, 8.4), 8.100),
    (48.640, (7.9, 7.4), 7.161),
    (47.701, (7.0, 6.65), 6.472),
)
STEP_END_MM = 8.5  # Tool edge past the turned stock at every level, so each pass starts and ends in air.

HEAD_APOTHEM_MM = 9.071
# Just under the head flats, so the tool never meets the top underside, which the steps own.
HEAD_CONTOUR_BOTTOM_Z_MM = 49.39

POCKET_FLOOR_Z_MM = 51.306
NOTCH_FLOOR_Z_MM = 53.033
NOTCH_HALF_WIDTH_MM = 0.9415
NOTCH_INNER_APOTHEM_MM = 7.231
# How far past each end of a notch the T12's center runs, which clears the tool's edge by about 0.2 mm.
NOTCH_RUNOUT_MM = 1.0


def step_path_points(angle_deg):
    """The T2 tip's path along one side, from the top step down: climb cuts run toward -tangent."""
    normal, _tangent = side_directions(angle_deg)
    points = []
    for underside_z_mm, rough_depths_mm, wall_apothem_mm in STEP_LEVELS:
        center_z_mm = underside_z_mm - TOOL_DIAMETER_T2_MM / 2
        passes = (*rough_depths_mm, wall_apothem_mm, wall_apothem_mm)
        along_mm = STEP_END_MM
        for apothem_mm in passes:
            points.append(world_point(normal, apothem_mm, center_z_mm, along_mm))
            along_mm = -along_mm
            points.append(world_point(normal, apothem_mm, center_z_mm, along_mm))
    return points


def add_step_sketch(root, angle_deg):
    name = f"Step Path {angle_deg:03d}"
    existing = root.sketches.itemByName(name)
    if existing:
        return existing
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    lines = sketch.sketchCurves.sketchLines
    points = step_path_points(angle_deg)
    previous = sketch.sketchPoints.add(sketch.modelToSketchSpace(points[0]))
    for point in points[1:]:
        previous = lines.addByTwoPoints(previous, sketch.modelToSketchSpace(point)).endSketchPoint
    return sketch


def octagon_corners(apothem_mm, is_clockwise):
    corner_radius_mm = apothem_mm / math.cos(math.radians(22.5))
    angles_deg = [22.5 + 45 * index for index in range(8)]
    if is_clockwise:
        angles_deg.reverse()
    return [
        adsk.core.Point3D.create(
            corner_radius_mm * math.cos(math.radians(angle)) * MM_TO_CM,
            corner_radius_mm * math.sin(math.radians(angle)) * MM_TO_CM,
            0,
        )
        for angle in angles_deg
    ]


def add_head_sketch(root):
    """The head's outline, clockwise, because left compensation then puts the tool outside and climbing."""
    name = "Head Outline"
    existing = root.sketches.itemByName(name)
    if existing:
        return existing
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    lines = sketch.sketchCurves.sketchLines
    corners = [sketch.modelToSketchSpace(point) for point in octagon_corners(HEAD_APOTHEM_MM, is_clockwise=True)]
    first = sketch.sketchPoints.add(corners[0])
    previous = first
    for corner in corners[1:]:
        previous = lines.addByTwoPoints(previous, corner).endSketchPoint
    lines.addByTwoPoints(previous, first)
    return sketch


def add_notch_sketches(root):
    """Center lines for roughing each notch, and wall lines directed so left compensation stays inside the notch."""
    centers = root.sketches.itemByName("Notch Centers")
    walls = root.sketches.itemByName("Notch Walls")
    if centers and walls:
        return centers, walls
    centers = root.sketches.add(root.xYConstructionPlane)
    centers.name = "Notch Centers"
    walls = root.sketches.add(root.xYConstructionPlane)
    walls.name = "Notch Walls"
    inner_mm = NOTCH_INNER_APOTHEM_MM - NOTCH_RUNOUT_MM
    outer_mm = HEAD_APOTHEM_MM + NOTCH_RUNOUT_MM
    for angle in SIDE_ANGLES_DEG:
        normal, _tangent = side_directions(angle)

        def point_on(apothem_mm, along_mm, sketch):
            flat = world_point(normal, apothem_mm, 0, along_mm)
            return sketch.modelToSketchSpace(flat)

        centers.sketchCurves.sketchLines.addByTwoPoints(point_on(outer_mm, 0, centers), point_on(inner_mm, 0, centers))
        # Walking outward, left is +tangent, so that wall's tool sits inside only on the -tangent wall.
        walls.sketchCurves.sketchLines.addByTwoPoints(
            point_on(inner_mm, -NOTCH_HALF_WIDTH_MM, walls), point_on(outer_mm, -NOTCH_HALF_WIDTH_MM, walls)
        )
        walls.sketchCurves.sketchLines.addByTwoPoints(
            point_on(outer_mm, NOTCH_HALF_WIDTH_MM, walls), point_on(inner_mm, NOTCH_HALF_WIDTH_MM, walls)
        )
    return centers, walls


T1_FEEDS = {
    "tool_spindleSpeed": "7600 rpm",
    "tool_rampSpindleSpeed": "7600 rpm",
    "tool_feedCutting": "1448 mm/min",
    "tool_feedEntry": "1448 mm/min",
    "tool_feedExit": "1448 mm/min",
    "tool_feedTransition": "1448 mm/min",
    "tool_feedPlunge": "200 mm/min",
    "tool_feedRamp": "400 mm/min",
    "tool_coolant": "'flood'",
}
T11_FEEDS = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "200 mm/min",
    "tool_feedEntry": "200 mm/min",
    "tool_feedExit": "200 mm/min",
    "tool_feedTransition": "200 mm/min",
    "tool_feedPlunge": "50 mm/min",
    "tool_feedRamp": "100 mm/min",
    "tool_coolant": "'flood'",
}
# Every T12 plunge lands past the end of a notch, in air, so the plunge feeds only need to be safe, not gentle.
T12_FEEDS_ROUGH = {
    "tool_spindleSpeed": "10000 rpm",
    "tool_rampSpindleSpeed": "10000 rpm",
    "tool_feedCutting": "120 mm/min",
    "tool_feedEntry": "120 mm/min",
    "tool_feedExit": "120 mm/min",
    "tool_feedTransition": "120 mm/min",
    "tool_feedPlunge": "60 mm/min",
    "tool_feedRamp": "60 mm/min",
    "tool_coolant": "'flood'",
}
T12_FEEDS_FINISH = {**T12_FEEDS_ROUGH, "tool_feedPlunge": "200 mm/min"}
FINISH_CONTOUR = {
    "tolerance": "0.002 mm",
    "smoothingFilter": "true",
    "smoothingFilterMode": "'fitArcs'",
    "nullPass": "true",
    "useStockToLeave": "false",
}
SEMI_CONTOUR = {
    "tolerance": "0.01 mm",
    "nullPass": "false",
    "useStockToLeave": "true",
    "stockToLeave": "0.1 mm",
    "verticalStockToLeave": "0 mm",
}


def bottom_from_origin(params, origin_point, offset_mm):
    params.itemByName("bottomHeight_mode").expression = "'from point'"
    params.itemByName("bottomHeight_ref").value.value = [origin_point]
    params.itemByName("bottomHeight_offset").expression = f"{offset_mm} mm"


def add_operation(cam, setup, strategy, name, tool_number, configure, feeds):
    """Adds a pass, setting feeds after creation, because assigning a tool resets them."""
    operation_input = setup.operations.createInput(strategy)
    operation_input.tool = find_tool(cam, tool_number)
    configure(operation_input.parameters)
    operation = setup.operations.add(operation_input)
    operation.name = name
    set_expressions(operation.parameters, feeds)
    return operation


def set_open_chains(params, parameter_name, curves):
    """One chain per curve, for passes that cut several separate lines."""
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    for curve in curves:
        chain = selections.createNewChainSelection()
        chain.inputGeometry = [curve]
        chain.isOpen = True
        chain.isReverted = False
    selection_value.applyCurveSelections(selections)


def set_face_contour(params, parameter_name, face):
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    contour = selections.createNewFaceContourSelection()
    contour.inputGeometry = [face]
    # The default ran the tool on the far side of the wall, inside the metal, with no warning from Fusion.
    contour.sideType = adsk.cam.SideTypes.AlwaysInsideSideType
    selection_value.applyCurveSelections(selections)


def set_pocket_face(params, parameter_name, face):
    selection_value = params.itemByName(parameter_name).value
    selections = selection_value.getCurveSelections()
    selections.clear()
    pocket = selections.createNewPocketSelection()
    pocket.inputGeometry = [face]
    selection_value.applyCurveSelections(selections)


def add_pocket_passes(cam, setup, root):
    rook = root.bRepBodies.itemByName("Rook")
    floor = next(
        face
        for face in rook.faces
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType
        and abs(face.centroid.z / MM_TO_CM - POCKET_FLOOR_Z_MM) < 0.01
    )

    def rough(params):
        set_pocket_face(params, "pockets", floor)
        set_expressions(params, {
            "optimalLoad": "0.64 mm", "maximumStepdown": "5.6 mm", "useStockToLeave": "true",
            "stockToLeave": "0.15 mm", "verticalStockToLeave": "0.1 mm", "rampAngle": "3 deg",
        })

    def semi_walls(params):
        set_face_contour(params, "contours", floor)
        set_expressions(params, {
            "useStockToLeave": "true", "stockToLeave": "0.03 mm", "verticalStockToLeave": "0.03 mm",
            "doMultipleDepths": "true", "maximumStepdown": "0.8 mm", "nullPass": "false",
        })

    def finish_floor(params):
        set_pocket_face(params, "pockets", floor)
        set_expressions(params, {
            "useStockToLeave": "true", "stockToLeave": "0.03 mm", "verticalStockToLeave": "0 mm",
            "maximumStepover": "0.9 mm", "rampAngle": "3 deg",
        })

    def finish_walls(params):
        set_face_contour(params, "contours", floor)
        set_expressions(params, FINISH_CONTOUR)

    add_operation(cam, setup, "adaptive2d", "Rough Pocket", 1, rough, T1_FEEDS)
    add_operation(cam, setup, "contour2d", "Semi Pocket Walls", 11, semi_walls, T11_FEEDS)
    add_operation(cam, setup, "pocket2d", "Finish Pocket Floor", 11, finish_floor, T11_FEEDS)
    add_operation(cam, setup, "contour2d", "Finish Pocket Walls", 11, finish_walls, T11_FEEDS)


def add_notch_passes(cam, setup, root, origin_point):
    centers, walls = add_notch_sketches(root)
    notch_bottom_mm = NOTCH_FLOOR_Z_MM - TOP_Z_MM

    def rough(params):
        set_open_chains(params, "contours", list(centers.sketchCurves))
        bottom_from_origin(params, origin_point, notch_bottom_mm)
        set_expressions(params, {
            "compensationType": "'off'", "doLeadIn": "false", "doLeadOut": "false", "useStockToLeave": "false",
            "doMultipleDepths": "true", "maximumStepdown": "0.15 mm", "bothWays": "true", "nullPass": "false",
        })

    def finish(params):
        set_open_chains(params, "contours", list(walls.sketchCurves))
        bottom_from_origin(params, origin_point, notch_bottom_mm)
        set_expressions(params, {"doLeadIn": "false", "doLeadOut": "false", "doMultipleDepths": "false"})
        set_expressions(params, FINISH_CONTOUR)

    add_operation(cam, setup, "contour2d", "Rough Notches", 12, rough, T12_FEEDS_ROUGH)
    add_operation(cam, setup, "contour2d", "Finish Notch Walls", 12, finish, T12_FEEDS_FINISH)


def add_shaft_passes(cam, setup, root, origin_point):
    """Each side twice, with the tool along the side's ruling, running down from the top of the flank."""
    up_line = up_axis_line(root)
    leads = {
        "doLeadIn": "true", "doLeadOut": "true", "entry_radius": "1 mm", "entry_distance": "0 mm",
        "exit_sameAsEntry": "false", "exit_radius": "0.25 mm", "exit_distance": "0 mm",
    }
    for prefix, settings in (("Semi Shaft", SEMI_CONTOUR), ("Flank Shaft", FINISH_CONTOUR)):
        for angle in SIDE_ANGLES_DEG:
            sketch = add_flank_sketch(root, angle)
            axis = add_axis_line(root, (angle - 90) % 360)

            def configure(params, sketch=sketch, axis=axis, settings=settings):
                set_tool_axis(params, axis, up_line)
                set_chain(params, "contours", list(sketch.sketchCurves), False)
                bottom_from_origin(params, origin_point, -FLANK_TIP_PAST_AXIS_MM)
                set_expressions(params, leads)
                set_expressions(params, settings)

            add_operation(cam, setup, "contour2d", f"{prefix} {angle:03d}", 2, configure, T2_FEEDS)


def generate_next(cam, setup, batch_size):
    """Queues a few passes and reports the rest. Call again until nothing is left."""
    operations = list(setup.allOperations)
    if any(operation.isGenerating for operation in operations):
        print("still generating:", [operation.name for operation in operations if operation.isGenerating])
        return False
    pending = [operation for operation in operations if not operation.isToolpathValid]
    for operation in pending[:batch_size]:
        cam.generateToolpath(operation)
    problems = [(operation.name, operation.warning[:120], operation.error[:120]) for operation in operations if operation.warning or operation.error]
    print("queued", [operation.name for operation in pending[:batch_size]], "left", max(0, len(pending) - batch_size), "problems", problems)
    return not pending
