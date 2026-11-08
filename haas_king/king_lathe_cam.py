"""Fusion script helpers: add the King's lathe passes, copying each one's settings from the Queen's document.

Run through the Fusion MCP with the King's document active and the Queen's open. Only the Z limits differ: they are
distances below G54, at the finial's tip. Everything else, including insert feeds, is the Queen's.
"""
import importlib
import math

import adsk.cam
import adsk.core
import adsk.fusion

import king_mill

importlib.reload(king_mill)

TOP_Z_MM = 86.2316
BASE_UNDERSIDE_Z_MM = 0.966  # Top of the base's lower fillet, where T8 takes over, as on the Queen.
NECK_BOTTOM_Z_MM = -5.0
SETUP_NAME = "Lathe turn blank"
# T8 plunges under the finial's head, in the window between the rim's bead (top z 78.89) and the head's edge
# (z 83.914). The target is a staircase there, each step where a 3 mm plunge's upper corner meets the finial's cone,
# over a floor at z 79.1. Below the floor, and in the staircase's corners, the mill takes the rest.
HEAD_EDGE_Z_MM = 83.914
UNDER_HEAD_FLOOR_Z_MM = 79.1
# The big collar's underside faces the chuck and is too steep for T7's V, which leaves up to 0.49 mm radially there. T8's
# side takes it, from the collar's widest point down. The back limit is low enough for the insert's upper corner to follow
# the underside to its foot at z 54.6, 3 mm above the lower corner.
COLLAR_WIDEST_Z_MM = 55.6
UNDER_COLLAR_BOTTOM_Z_MM = 51.0

# King pass name, Queen pass it copies, front Z or None for the model's front, back Z.
PASSES = (
    ("Face top", "Face top", None, None),
    ("Rough profile", "Rough head", None, NECK_BOTTOM_Z_MM),
    ("Rough detail", "Rough head detail", None, BASE_UNDERSIDE_Z_MM),
    ("Finish profile", "Finish head", None, BASE_UNDERSIDE_Z_MM),
    ("Rough under head", "Rough neck groove", HEAD_EDGE_Z_MM, UNDER_HEAD_FLOOR_Z_MM - 0.1),
    ("Groove under head", "Groove crown cone", HEAD_EDGE_Z_MM, UNDER_HEAD_FLOOR_Z_MM - 0.1),
    ("Groove under collar", "Groove under collar", COLLAR_WIDEST_Z_MM, UNDER_COLLAR_BOTTOM_Z_MM),
    ("Rough neck groove", "Rough neck groove", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
    ("Groove neck", "Groove neck", BASE_UNDERSIDE_Z_MM, NECK_BOTTOM_Z_MM),
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


def add_pass(cam, queen_operation, name, front_z_mm, back_z_mm, before=None):
    setup = cam.setups.itemByName(SETUP_NAME)
    tool_number = queen_operation.tool.parameters.itemByName("tool_number").value.value
    operation_input = setup.operations.createInput(queen_operation.strategy)
    operation_input.tool = find_tool(cam, tool_number)
    operation = setup.operations.add(operation_input)
    operation.name = name
    refused = copy_settings(queen_operation.parameters, operation.parameters)
    if front_z_mm is None:
        operation.parameters.itemByName("frontHeight_mode").expression = "'model front'"
    else:
        set_z_limit(operation.parameters, "frontHeight", front_z_mm)
    if back_z_mm is not None:
        set_z_limit(operation.parameters, "backHeight", back_z_mm)
    if before is not None:
        operation.moveBefore(before)
    return operation, tool_number, refused


def add_lathe_passes(cam, queen_cam):
    sources = {operation.name: operation for operation in queen_cam.setups.itemByName(SETUP_NAME).allOperations}
    for name, source_name, front_z_mm, back_z_mm in PASSES:
        operation, tool_number, refused = add_pass(cam, sources[source_name], name, front_z_mm, back_z_mm)
        print(name, "T", tool_number, "refused", len(refused))


def add_passes_after_finish(cam, queen_cam, names):
    """Adds these T8 passes to a document that already has the others, right after Finish profile."""
    sources = {operation.name: operation for operation in queen_cam.setups.itemByName(SETUP_NAME).allOperations}
    setup = cam.setups.itemByName(SETUP_NAME)
    next_pass = next(operation for operation in setup.allOperations if operation.name == "Rough neck groove")
    for name, source_name, front_z_mm, back_z_mm in PASSES:
        if name in names:
            add_pass(cam, sources[source_name], name, front_z_mm, back_z_mm, before=next_pass)


def add_or_update_program(cam, source_cam, program_name, setup_names, output_folder):
    """Makes or refreshes an NC program over these setups, with the post and properties of the Queen's program of
    the same role (lathe or mill), and posts it."""
    role = "lathe" if program_name.endswith("lathe") else "mill"
    source = next(program for program in source_cam.ncPrograms if program.name.endswith(role))
    program = next((p for p in cam.ncPrograms if p.name == program_name), None)
    if program is None:
        program_input = cam.ncPrograms.createInput()
        program_input.displayName = program_name
        program_input.operations = [cam.setups.itemByName(name) for name in setup_names]
        program = cam.ncPrograms.add(program_input)
    params = program.parameters
    params.itemByName("nc_program_filename").value.value = program_name
    params.itemByName("nc_program_output_folder").value.value = output_folder
    params.itemByName("nc_program_openInEditor").value.value = False
    params.itemByName("nc_program_name").value.value = cam.setups.itemByName(setup_names[0]).parameters.itemByName(
        "job_programName"
    ).value.value
    params.itemByName("nc_program_unit").expression = "'Millimeters'"
    params.itemByName("nc_program_post").value.value = source.parameters.itemByName("nc_program_post").value.value
    post = program.postParameters
    source_post = source.postParameters
    for index in range(source_post.count):
        item = post.itemByName(source_post.item(index).name)
        if item is not None and item.expression != source_post.item(index).expression:
            item.expression = source_post.item(index).expression
    program.updatePostParameters(post)
    return program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())


TARGET_SKETCH_NAME = "Lathe Target Profile"
# The sketch is drawn in the plane through the part axis at C 22.5, through the octagon's corner edges.
CORNER_PLANE_DEG = 22.5


def _corner_plane_point(sketch, r_mm, z_mm):
    angle_rad = math.radians(CORNER_PLANE_DEG)
    model = adsk.core.Point3D.create(r_mm * math.cos(angle_rad) * 0.1, r_mm * math.sin(angle_rad) * 0.1, z_mm * 0.1)
    return sketch.modelToSketchSpace(model)


def _model_z_mm(sketch, sketch_point):
    return sketch.sketchToModelSpace(sketch_point.geometry).z * 10


def _target_sketch():
    design = adsk.fusion.Design.cast(adsk.core.Application.get().activeDocument.products.itemByProductType("DesignProductType"))
    return design.rootComponent.sketches.itemByName(TARGET_SKETCH_NAME)


def _span_curves(sketch, z_low_mm, z_high_mm):
    """The profile's curves between these heights, and the sketch point at each end, keyed by its height."""
    span = []
    for curve in sketch.sketchCurves:
        if curve.isConstruction or not hasattr(curve, "startSketchPoint"):
            continue
        ends_z = sorted((_model_z_mm(sketch, curve.startSketchPoint), _model_z_mm(sketch, curve.endSketchPoint)))
        is_inside_span = ends_z[0] > z_low_mm - 1e-3 and ends_z[1] < z_high_mm + 1e-3
        if is_inside_span and ends_z[1] - ends_z[0] > 1e-3:
            span.append(curve)
    ends = {}
    for curve in span:
        for point in (curve.startSketchPoint, curve.endSketchPoint):
            for end_z in (z_low_mm, z_high_mm):
                if abs(_model_z_mm(sketch, point) - end_z) < 1e-3:
                    ends[end_z] = point
    return span, ends


def _replace_span(sketch, z_low_mm, z_high_mm, points):
    """Swaps the span's curves for a spline through these (r, z) points, bottom up, ends included.

    Keeps the sketch points the span shares with its neighbours, so the profile stays closed and the revolve updates.
    """
    span, ends = _span_curves(sketch, z_low_mm, z_high_mm)
    # Each end point is shared with a neighbouring curve, so it outlives the span's curves.
    for curve in span:
        curve.deleteMe()
    fit_points = adsk.core.ObjectCollection.create()
    fit_points.add(ends[z_low_mm])
    for r_mm, z_mm in points[1:-1]:
        fit_points.add(_corner_plane_point(sketch, r_mm, z_mm))
    fit_points.add(ends[z_high_mm])
    sketch.sketchCurves.sketchFittedSplines.add(fit_points)
    return len(span)


def grow_target_corners():
    """Replaces the target's octagon corner span, between the clipping cones, with a spline CORNER_STOCK_MM outside."""
    z_low, z_high = king_mill.CORNER_EDGE_Z_MM
    return _replace_span(_target_sketch(), z_low, z_high, king_mill.corner_stock_points())


# The crown's seams, where neighbouring facets, fillets and ledges meet at C 22.5 and so on: from the collar's edge up
# to where the crown's cone clips the facets' corners. Read from the lathe target's sketch.
CROWN_SEAM_Z_MM = (63.1768, 65.0460)
# The seam is only 2.1 long, so the stock ramps in over less than the octagon's 1.0, along the profile.
CROWN_SEAM_RAMP_MM = 0.5
CROWN_SEAM_SAMPLE_MM = 0.05


def _span_profile_points(sketch, z_low_mm, z_high_mm):
    """(r, z) samples along the span's curves, bottom up. The seam's profile rises steadily, so z orders it."""
    samples = []
    for curve in _span_curves(sketch, z_low_mm, z_high_mm)[0]:
        evaluator = curve.geometry.evaluator
        _, start, end = evaluator.getParameterExtents()
        _, length_cm = evaluator.getLengthAtParameter(start, end)
        count = max(2, math.ceil(length_cm * 10 / CROWN_SEAM_SAMPLE_MM))
        for index in range(count + 1):
            _, point = evaluator.getPointAtParameter(start + (end - start) * index / count)
            model = sketch.sketchToModelSpace(point)
            samples.append((math.hypot(model.x, model.y) * 10, model.z * 10))
    samples.sort(key=lambda sample: sample[1])
    deduplicated = [samples[0]]
    for sample in samples[1:]:
        if math.dist(sample, deduplicated[-1]) > 1e-4:
            deduplicated.append(sample)
    return deduplicated


def offset_profile_points(points, stock_mm, ramp_mm):
    """Moves each (r, z) point out along the profile's normal, the stock ramped in from nothing at both ends.

    The profile runs bottom up with metal on the axis side, so (dz, -dr) points out of the part.
    """
    along_mm = [0.0]
    for previous, point in zip(points, points[1:]):
        along_mm.append(along_mm[-1] + math.dist(previous, point))
    total_mm = along_mm[-1]
    grown = []
    for index, (r_mm, z_mm) in enumerate(points):
        before = points[max(0, index - 1)]
        after = points[min(len(points) - 1, index + 1)]
        dr, dz = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dr, dz)
        ramp = min(1.0, along_mm[index] / ramp_mm, (total_mm - along_mm[index]) / ramp_mm)
        # Smoothstep, so the target meets its neighbours without a kink.
        out_mm = stock_mm * ramp * ramp * (3 - 2 * ramp)
        grown.append((r_mm + out_mm * dz / length, z_mm - out_mm * dr / length))
    return grown


def grow_target_crown_seams():
    """Replaces the target's crown seam span with a spline CORNER_STOCK_MM outside it, as on the octagon's corners."""
    sketch = _target_sketch()
    z_low, z_high = CROWN_SEAM_Z_MM
    points = offset_profile_points(_span_profile_points(sketch, z_low, z_high), king_mill.CORNER_STOCK_MM, CROWN_SEAM_RAMP_MM)
    return _replace_span(sketch, z_low, z_high, points)
