"""Fusion helpers that build the King's cup passes. Run through the Fusion MCP with the King's document active.

The ring passes come from king_cup_rings.json, which `python3 king_cup.py` writes. Each is a Multi-Axis Contour in
4-axis mode with the tool tilted a fixed 45 deg to the rotary axis, so it posts B45 held while C turns.

The rings run in their own setup, whose model is `King Revolved`, the lathe target with the cup cut out. On the real
King a ring breaks at each notch and retracts, and the operations' model override is disabled in this document. That
model covers the King everywhere, so it can't let a tool into the part. Rough Cup runs before them in a setup of its own
on the real King: regenerating it on `King Revolved` crashed Fusion's CAM kernel.
"""
import json
import os
import time

import adsk.cam
import adsk.core
import adsk.fusion

from king_cup import FLOOR_RADIUS as FLOOR_RADIUS_MM
from king_cup import ROUGH_CUP_MAX_CENTER_R_MM

FOLDER = "/Users/don.payne/src/cnc/haas_king"
SETUP_NAME = "Mill King cup rings"
ROUGH_CUP_SETUP_NAME = "Mill King rough cup"
MM_TO_CM = 0.1
G54_MODEL_Z_MM = 86.2316
CUP_ROUGH_FLOOR_Z_MM = 74.9
# Just above the lathe's floor at z 79.1. From the stock top instead, Adaptive also slots the finial's flutes from above
# (z 80.2 up), which T11 cuts.
CUP_ROUGH_TOP_Z_MM = 79.2

FEEDS = {
    4: {
        "tool_spindleSpeed": "10000 rpm",
        "tool_rampSpindleSpeed": "10000 rpm",
        "tool_feedCutting": "305 mm/min",
        "tool_feedEntry": "305 mm/min",
        "tool_feedExit": "305 mm/min",
        "tool_feedTransition": "305 mm/min",
        "tool_feedPlunge": "100 mm/min",
        "tool_feedRamp": "100 mm/min",
        "tool_coolant": "'flood'",
    },
    14: {
        "tool_spindleSpeed": "10000 rpm",
        "tool_rampSpindleSpeed": "10000 rpm",
        "tool_feedCutting": "150 mm/min",
        "tool_feedEntry": "150 mm/min",
        "tool_feedExit": "150 mm/min",
        "tool_feedTransition": "150 mm/min",
        "tool_feedPlunge": "60 mm/min",
        "tool_feedRamp": "60 mm/min",
        "tool_coolant": "'flood'",
    },
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


def generate(cam, operation):
    future = cam.generateToolpath(operation)
    while not future.isGenerationCompleted:
        time.sleep(0.2)


def ring_sketch(root, name, contacts_mm):
    """Draws one circle per contact point, around the part axis, and returns them in order."""
    old = root.sketches.itemByName(name)
    if old is not None:
        old.deleteMe()
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    circles = sketch.sketchCurves.sketchCircles
    rings = []
    for r_mm, z_mm in contacts_mm:
        center = sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, z_mm * MM_TO_CM))
        rings.append(circles.addByCenterRadius(center, r_mm * MM_TO_CM))
    return rings


def add_ring_pass(design, cam, entry, before=None):
    # Fusion offsets the whole model by the stock to leave. The floor's fillet is concave, so an offset this big has no
    # surface there: Fusion gave an empty toolpath, and with the curve moved off the part, crashed its CAM kernel.
    stock_mm = entry["stock_to_leave_mm"]
    if stock_mm >= FLOOR_RADIUS_MM:
        raise ValueError(f"{entry['name']}: a {stock_mm} mm offset turns the cup floor's fillet inside out")
    root = design.rootComponent
    rings = ring_sketch(root, f"Rings {entry['name']}", entry["contacts_mm"])
    setup = cam.setups.itemByName(SETUP_NAME)
    operation_input = setup.operations.createInput("multi_axis_contour")
    operation_input.tool = find_tool(cam, entry["tool"])
    operation_input.parameters.itemByName("multiAxisMachiningType").expression = "'four_axis'"
    operation = setup.operations.add(operation_input)
    operation.name = entry["name"]
    params = operation.parameters
    settings = dict(FEEDS[entry["tool"]])
    settings.update(
        {
            "toolAxisMode": "'tilt_to_rotary_axis'",
            "multiAxisTiltAngleFixed": "45 deg",
            "useStockToLeave": "true" if stock_mm > 0 else "false",
            "stockToLeave": f"{stock_mm} mm",
            "retractionPolicy": "'minimum'",
        }
    )
    set_expressions(params, settings)
    value = params.itemByName("curves").value
    selections = value.getCurveSelections()
    for ring in rings:
        chain = selections.createNewChainSelection()
        chain.inputGeometry = [ring]
    value.applyCurveSelections(selections)
    if before is not None:
        operation.moveBefore(before)
    generate(cam, operation)
    return operation


def add_ring_passes(names=None):
    """Adds the planned ring passes in plan order, or only those named, and reports each one's state."""
    design, cam = active_design_and_cam()
    with open(os.path.join(FOLDER, "king_cup_rings.json")) as plan_file:
        plan = json.load(plan_file)
    for entry in plan:
        if names is not None and entry["name"] not in names:
            continue
        operation = add_ring_pass(design, cam, entry)
        warning = operation.warning.replace("\n", " ")[:120] if operation.hasWarning else ""
        print(entry["name"], "valid", operation.isToolpathValid, warning)


def set_center_boundary(root, operation, radius_mm):
    """Keeps the tool's center inside a circle around the part axis, drawn in its own sketch."""
    name = f"{operation.name} Boundary"
    old = root.sketches.itemByName(name)
    if old is not None:
        old.deleteMe()
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), radius_mm * MM_TO_CM)
    params = operation.parameters
    params.itemByName("boundaryMode").expression = "'selection'"
    params.itemByName("boundaryContainment").expression = "'center'"
    value = params.itemByName("machiningBoundarySel").value
    selections = value.getCurveSelections()
    selections.createNewChainSelection().inputGeometry = [circle]
    value.applyCurveSelections(selections)


def add_rough_cup(before=None):
    """T4 Adaptive at B0: everything in the cup that's open from above, outside the head's shadow.

    Its model is the real King, so a center boundary keeps it out of the notches. Nothing else is open from above: the
    crown widens upward over the facets and shaft.
    """
    design, cam = active_design_and_cam()
    setup = cam.setups.itemByName(ROUGH_CUP_SETUP_NAME)
    operation_input = setup.operations.createInput("adaptive")
    operation_input.tool = find_tool(cam, 4)
    operation = setup.operations.add(operation_input)
    operation.name = "Rough Cup"
    params = operation.parameters
    settings = dict(FEEDS[4])
    settings.update(
        {
            # At 13% engagement the chip thins to about 2/3 of the 0.025 mm/tooth this feed gives at 10,000 rpm.
            "optimalLoad": "0.4 mm",
            "tool_feedCutting": "500 mm/min",
            "maximumStepdown": "0.5 mm",
            "stockToLeave": "0.25 mm",
            # The copied tools carry no ramp angle, and Adaptive refuses to start without one. At 2 deg and the
            # 100 mm/min plunge feed, its helices took half the pass's time.
            "tool_rampAngle": "5 deg",
            "tool_feedRamp": "250 mm/min",
            # The stock includes the grip stub, which the King doesn't, so without a floor Adaptive clears the stub
            # too (288 min). The notches bottom out at z 75.13 and the cup at 75.59.
            "topHeight_mode": "'from wcs'",
            "topHeight_offset": f"{CUP_ROUGH_TOP_Z_MM - G54_MODEL_Z_MM:.4f} mm",
            "bottomHeight_mode": "'from wcs'",
            "bottomHeight_offset": f"{CUP_ROUGH_FLOOR_Z_MM - G54_MODEL_Z_MM:.4f} mm",
        }
    )
    set_expressions(params, settings)
    set_center_boundary(design.rootComponent, operation, ROUGH_CUP_MAX_CENTER_R_MM)
    if before is not None:
        operation.moveBefore(before)
    generate(cam, operation)
    return operation
