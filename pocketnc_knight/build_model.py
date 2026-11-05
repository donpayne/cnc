"""Builds the Knight, its mount and its stock in the active Fusion design. Run inside Fusion (see README).

Bodies created:
  Knight        knight_source.sat, scaled and standing on the part axis
  Mount         stump, shoulder and neck: the wax that stays after cutting
  Knight Stock  turned wax blank
"""
import importlib
import math
import os
import sys

import adsk.core
import adsk.fusion

# Code pasted into Fusion through its MCP connection has no __file__, so the caller defines SOURCE_DIR.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else SOURCE_DIR)
import knight_geometry as geo

importlib.reload(geo)

_CM_PER_MM = 0.1
TOOL_RADIUS_MM = 3.175 / 2
SHOULDER_CLEARANCE_MM = 0.3  # Nothing needs the shoulder's top cut true, so keep the tool from rubbing it.
BOUNDARY_MARGIN_MM = 2.6  # Lets the tool center run just past the stock, so its full width clears the wax.
# Rest machining misses these areas near the part axis: (X low, X high, Y low, Y high). Sides 90 and 270
# stop 7.94 mm from the axis, so only sides 0 and 180 can finish them, and the finish center pass does.
TOP_PATCH_MM = (-8.6, 8.6, 53.1, geo.STOCK_TOP_Y_MM + BOUNDARY_MARGIN_MM)
SNOUT_PATCH_MM = (-8.0, -1.85, 28.5, 34.7)
EARS_LOW_Y_MM = 54.3  # The valley between the ears bottoms out at about Y 56.3.


def _cylinder(temp, bottom_y_mm, top_y_mm, radius_mm):
    return temp.createCylinderOrCone(
        adsk.core.Point3D.create(0, bottom_y_mm * _CM_PER_MM, 0), radius_mm * _CM_PER_MM,
        adsk.core.Point3D.create(0, top_y_mm * _CM_PER_MM, 0), radius_mm * _CM_PER_MM)


def _union_all(temp, bodies):
    result = bodies[0]
    for body in bodies[1:]:
        temp.booleanOperation(result, body, adsk.fusion.BooleanTypes.UnionBooleanType)
    return result


def scaled_knight(temp, source_body):
    """Copy the Knight, stand its Z axis on world +Y and scale it about its base."""
    knight = temp.copy(source_body)
    matrix = adsk.core.Matrix3D.create()
    scale = geo.KNIGHT_SCALE
    base_z_cm = geo.SOURCE_BASE_Z_MM * _CM_PER_MM
    base_y_cm = geo.KNIGHT_BASE_Y_MM * _CM_PER_MM
    matrix.setWithArray([
        scale, 0, 0, 0,
        0, 0, scale, base_y_cm - scale * base_z_cm,
        0, -scale, 0, 0,
        0, 0, 0, 1,
    ])
    temp.transform(knight, matrix)
    return knight


def _mount(temp):
    return _union_all(temp, [
        _cylinder(temp, geo.STOCK_BOTTOM_Y_MM, geo.SHOULDER_BOTTOM_Y_MM, geo.STUMP_RADIUS_MM),
        _cylinder(temp, geo.SHOULDER_BOTTOM_Y_MM, geo.SHOULDER_TOP_Y_MM, geo.HEAD_RADIUS_MM),
        _cylinder(temp, geo.SHOULDER_TOP_Y_MM, geo.KNIGHT_BASE_Y_MM, geo.NECK_RADIUS_MM),
    ])


def _stock(temp):
    return _union_all(temp, [
        _cylinder(temp, geo.STOCK_BOTTOM_Y_MM, geo.SHOULDER_BOTTOM_Y_MM, geo.STUMP_RADIUS_MM),
        _cylinder(temp, geo.SHOULDER_BOTTOM_Y_MM, geo.STOCK_TOP_Y_MM, geo.HEAD_RADIUS_MM),
    ])


def add_bodies(root, knight):
    temp = adsk.fusion.TemporaryBRepManager.get()
    base = root.features.baseFeatures.add()
    base.startEdit()
    names = ("Knight", "Mount", "Knight Stock")
    for body in (knight, _mount(temp), _stock(temp)):
        root.bRepBodies.add(body, base)
    base.finishEdit()
    # Naming a body before finishEdit doesn't always stick, so name them once the feature is done.
    for index, name in enumerate(names):
        base.bodies.item(index).name = name
    root.bRepBodies.itemByName("Knight Stock").isLightBulbOn = False


def add_work_origin(root):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "Work Origin (G54)"
    origin_cm = [value * _CM_PER_MM for value in geo.WORK_ORIGIN_MM]
    sketch.sketchPoints.add(sketch.modelToSketchSpace(adsk.core.Point3D.create(*origin_cm)))
    return sketch


def report(root):
    for body in root.bRepBodies:
        box = body.boundingBox
        print(f"{body.name}: solid={body.isSolid} faces={body.faces.count} volume={body.volume * 1000:.0f} mm3 "
              f"X[{box.minPoint.x * 10:.2f},{box.maxPoint.x * 10:.2f}] "
              f"Y[{box.minPoint.y * 10:.2f},{box.maxPoint.y * 10:.2f}] "
              f"Z[{box.minPoint.z * 10:.2f},{box.maxPoint.z * 10:.2f}]")


def _add_rectangle(sketch, world_corner, across_low_mm, across_high_mm, low_y_mm, high_y_mm):
    corners = [
        sketch.modelToSketchSpace(adsk.core.Point3D.create(*world_corner(across * _CM_PER_MM, y * _CM_PER_MM)))
        for across, y in ((across_low_mm, low_y_mm), (across_high_mm, low_y_mm), (across_high_mm, high_y_mm), (across_low_mm, high_y_mm))
    ]
    lines = sketch.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])


def _add_boundary_sketch(sketch_name, plane, world_corner, half_width_mm, low_y_mm, high_y_mm):
    sketch = plane.component.sketches.add(plane)
    sketch.name = sketch_name
    _add_rectangle(sketch, world_corner, -half_width_mm, half_width_mm, low_y_mm, high_y_mm)


def _on_xy(across, y):
    return (across, y, 0)


def _on_yz(across, y):
    return (0, y, across)


def add_boundary_sketches(root):
    """Rectangles that keep every toolpath above the shoulder, off the stump and the unmodeled collet.

    One sketch serves each opposed pair of tool directions, since a boundary projects along the tool.
    """
    half_width_mm = geo.HEAD_RADIUS_MM + BOUNDARY_MARGIN_MM
    low_y_mm = geo.SHOULDER_TOP_Y_MM + TOOL_RADIUS_MM + SHOULDER_CLEARANCE_MM
    high_y_mm = geo.STOCK_TOP_Y_MM + BOUNDARY_MARGIN_MM
    _add_boundary_sketch("Boundary XY", root.xYConstructionPlane, _on_xy, half_width_mm, low_y_mm, high_y_mm)
    _add_boundary_sketch("Boundary YZ", root.yZConstructionPlane, _on_yz, half_width_mm, low_y_mm, high_y_mm)
    add_finish_boundary_sketches(root)
    add_ears_boundary_sketch(root)


def add_finish_boundary_sketches(root):
    """Rectangles for the finishes only: from just under the base up, and the patches rest machining misses."""
    half_width_mm = geo.HEAD_RADIUS_MM + BOUNDARY_MARGIN_MM
    low_y_mm = geo.FINISH_LOW_Y_MM
    high_y_mm = geo.STOCK_TOP_Y_MM + BOUNDARY_MARGIN_MM
    xy_plane, yz_plane = root.xYConstructionPlane, root.yZConstructionPlane
    _add_boundary_sketch("Finish Boundary XY", xy_plane, _on_xy, half_width_mm, low_y_mm, high_y_mm)
    _add_boundary_sketch("Finish Boundary YZ", yz_plane, _on_yz, half_width_mm, low_y_mm, high_y_mm)
    # Fusion misreads two rectangles in one boundary as everything below the first, so each gets a sketch.
    for sketch_name, patch_mm in (("Top Patch XY", TOP_PATCH_MM), ("Snout Patch XY", SNOUT_PATCH_MM)):
        patch_sketch = xy_plane.component.sketches.add(xy_plane)
        patch_sketch.name = sketch_name
        _add_rectangle(patch_sketch, _on_xy, *patch_mm)


def add_ears_boundary_sketch(root):
    """Rectangle for the deeper passes that reach the valley between the ears from side 90."""
    half_width_mm = geo.HEAD_RADIUS_MM + BOUNDARY_MARGIN_MM
    high_y_mm = geo.STOCK_TOP_Y_MM + BOUNDARY_MARGIN_MM
    _add_boundary_sketch("Ears Boundary YZ", root.yZConstructionPlane, _on_yz, half_width_mm, EARS_LOW_Y_MM, high_y_mm)


def add_tool_axis_sketch(root):
    """Lines to aim the tool at: Fusion's tool orientation needs geometry to select."""
    sketch = root.sketches.add(root.xZConstructionPlane)
    sketch.name = "Tool Axes"
    lines = sketch.sketchCurves.sketchLines
    origin = adsk.core.Point3D.create(0, 0, 0)
    for world_end in ((0, 0, 1), (1, 0, 0), (0, 0, -1), (-1, 0, 0)):
        lines.addByTwoPoints(sketch.modelToSketchSpace(origin), sketch.modelToSketchSpace(adsk.core.Point3D.create(*world_end)))
    add_tilted_tool_axis_sketch(root)


def add_tilted_tool_axis_sketch(root):
    """The same four directions, tilted up by the finish angle, in the same order as Tool Axes."""
    sketch = root.sketches.add(root.xZConstructionPlane)
    sketch.name = "Tilted Tool Axes"
    lines = sketch.sketchCurves.sketchLines
    origin = adsk.core.Point3D.create(0, 0, 0)
    tilt_rad = math.radians(geo.FINISH_TILT_DEG)
    for azimuth_deg in (0, 90, 180, 270):
        azimuth_rad = math.radians(azimuth_deg)
        world_end = adsk.core.Point3D.create(
            math.sin(azimuth_rad) * math.cos(tilt_rad), math.sin(tilt_rad), math.cos(azimuth_rad) * math.cos(tilt_rad))
        lines.addByTwoPoints(sketch.modelToSketchSpace(origin), sketch.modelToSketchSpace(world_end))
