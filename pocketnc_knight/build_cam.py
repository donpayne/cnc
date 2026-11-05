"""Creates the setup, the 1/8 in tool and the side-on toolpaths in the active Knight document.

Every operation uses one 1/8 in ball end mill, so the program needs no tool change.
Run inside Fusion after build_model.py (see README).
"""
import importlib
import json
import math
import os
import sys

import adsk.cam
import adsk.core
import adsk.fusion

# Code pasted into Fusion through its MCP connection has no __file__, so the caller defines SOURCE_DIR.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else SOURCE_DIR)
import knight_geometry as geo

importlib.reload(geo)

MACHINE_VENDOR = "Penta Machine"
MACHINE_MODEL = "Pocket NC V2-10"
SYSTEM_MACHINE_URL = "system://Penta Machine/penta machine pocket nc v2-10.mch"
# Penta's current post, which that machine names. Fusion's post library listing omits it.
POST_URL = "system://penta machine.cps"

# Penta's V2-10 recipe for wax with a 1/8 in single-flute tool: 10,000 rpm at 0.003 in
# per tooth, which is 30 in/min. It sits well under the 60 in/min axis limit.
SPINDLE_RPM = 10000
CUT_FEED_MM_PER_MIN = 762
RAMP_FEED_MM_PER_MIN = 381
PLUNGE_FEED_MM_PER_MIN = 254
RAMP_ANGLE_DEG = 3  # Shallow, because a single-flute 1/8 in tool is slender and cuts poorly on plunge.
RETRACT_ABOVE_STOCK_MM = 2
CLEARANCE_ABOVE_RETRACT_MM = 1
SHANK_CLEARANCE_MM = 0.5  # The shank is the same diameter as the cutter, so keep this small.
HOLDER_CLEARANCE_MM = 3.0
# Faster than Penta's recipe of 50% of tool diameter and 30 in/min, to cut roughing time. Not yet tried
# on the machine: if the tool chatters or the wax melts, go back to 1.5 mm and 762 mm/min.
ROUGH_STEPDOWN_MM = 3.0
ROUGH_FEED_MM_PER_MIN = 1143  # 45 in/min, against the 60 in/min axis limit.
ROUGH_STAY_DOWN_LEVEL = "level4"  # Fusion's "Most" stay-down setting.
ROUGH_RAPID_STOP_ABOVE_LEVEL_MM = 6.0  # 3 mm above the previous level's floor.
# Rapids returning to a level stop this lead's radius plus 0.3 mm above it, so with Fusion's default
# 0.32 mm they can hit the ridges a ball leaves, which stand up to one tool radius tall.
ROUGH_ENTRY_LEAD_RADIUS_MM = 1.7
ROUGH_MAX_STAY_DOWN_MM = 80.0  # Longer than the part, so more links stay down than retract and drop back in.
FINISH_RAPID_STOP_ABOVE_MODEL_MM = 5.0
ROUGH_LOAD_MM = 2.1  # Penta: 70% of tool diameter.
# A ball's center doesn't cut, and Fusion's default 0.79 mm helix for a ball is close to a straight
# plunge. These keep the center moving sideways through the wax as the tool descends.
ROUGH_HELIX_DIAMETER_MM = 2.4
ROUGH_MIN_HELIX_DIAMETER_MM = 1.6
# A 1/8 in ball leaves about 0.013 mm ridges at this stepover on surfaces facing the tool, and
# about twice that on the 45 deg slopes where one side hands off to the next.
FINISH_STEPOVER_MM = 0.4
FINISH_LEAD_ALLOWANCE_MM = 0.35  # Scallop's 0.32 mm leads run past the boundary, toward the shoulder.
ROUGH_STOCK_TO_LEAVE_MM = 0.15  # Thin enough for the finish pass to take in one go.
# The later roughs chase the ridges earlier ones left, and over half of their feed moves touch no wax.
# Skipping thin slivers saves about 10% per side. The finish takes what's left, still well under a roughing cut.
ROUGH_IGNORE_REST_THINNER_THAN_MM = 0.4
# Finish sides 0 and 180 skip wax that 90 and 270 already finished. A skin as thin as 0.02 mm counts
# as still there, and ridges alone are that tall, so at 0.02 mm the tool keeps re-cutting them. 0.03 mm halves the time.
FINISH_IGNORE_REST_THINNER_THAN_MM = 0.03
# Rest machining wrongly skips some surfaces near the part axis that only sides 0 and 180 can reach,
# because 90 and 270 stop short of them. Those get their own passes, without rest machining.

MACHINE_TABLE_ATTACH_Y_MM = -21.0  # Table attach frame, relative to the A axis, from the .mch file.
PROGRAM_NUMBER = 1001
OUTPUT_FILE_NAME = "knight"

TOOL_NUMBER = 11  # T10 in Penta's library is the flat end mill, so a ball gets its own number.
TOOL_DIAMETER_MM = 3.175
TOOL_STICKOUT_MM = 25.4  # Penta's first-part tutorial uses 1 in with the extended holder.
TOOL_FLUTE_LENGTH_MM = 9.525  # Assumed: measure the real tool.
EARS_SIDE_DEG = 90  # The valley between the ears runs along X. Sides 0 and 180 can't reach past the ears.
# Past the axis by a radius, so the ball's full width clears the valley's end at X 0. By then side 90's
# main pass has cleared the wax beyond X 7.94, which keeps the shank clear with 9.5 mm flutes.
EARS_FLOOR_ABOVE_AXIS_MM = -TOOL_DIAMETER_MM / 2

# Extended holder envelope, estimated from Penta's "about 3 in long". Dimensions are
# deliberately a little oversize so Fusion's collision checks err on the safe side.
HOLDER_SEGMENTS_MM = [(12.0, 16.0, 16.0), (64.0, 19.0, 19.0)]


def _set(params, name, expression):
    params.itemByName(name).expression = expression


def _select(params, name, entities):
    params.itemByName(name).value.value = entities


def _tool_json():
    return json.dumps({
        "BMC": "carbide",
        "description": "1/8 in ball end mill",
        "guid": "7f3d0a12-5c1e-4b7e-9a10-0a10c0ffee12",
        "type": "ball end mill",
        "unit": "millimeters",
        "vendor": "Pocket NC",
        "geometry": {
            "CSP": False, "DC": TOOL_DIAMETER_MM, "HAND": True, "LB": TOOL_STICKOUT_MM,
            "LCF": TOOL_FLUTE_LENGTH_MM, "NOF": 1, "OAL": 38.1, "SFDM": TOOL_DIAMETER_MM,
            "assemblyGaugeLength": TOOL_STICKOUT_MM + sum(s[0] for s in HOLDER_SEGMENTS_MM),
            "shoulder-diameter": TOOL_DIAMETER_MM, "shoulder-length": TOOL_FLUTE_LENGTH_MM,
            "RE": TOOL_DIAMETER_MM / 2,
        },
        "holder": {
            "description": "Pocket NC extended holder (estimated envelope)",
            "guid": "7f3d0a11-5c1e-4b7e-9a10-0a10c0ffee11",
            "type": "holder",
            "unit": "millimeters",
            "gaugeLength": sum(s[0] for s in HOLDER_SEGMENTS_MM),
            "segments": [
                {"height": height, "lower-diameter": lower, "upper-diameter": upper}
                for height, lower, upper in HOLDER_SEGMENTS_MM
            ],
        },
        "post-process": {
            "break-control": False, "comment": "", "diameter-offset": TOOL_NUMBER,
            "length-offset": TOOL_NUMBER, "live": True, "manual-tool-change": False,
            "number": TOOL_NUMBER, "turret": 0,
        },
    })


def ensure_tool(cam):
    """Return the document's tool, adding it on the first run so reruns don't duplicate it."""
    def find_tool():
        for tool in cam.documentToolLibrary:
            if tool.parameters.itemByName("tool_number").value.value == TOOL_NUMBER:
                return tool
        return None

    if find_tool() is None:
        cam.documentToolLibrary.add(adsk.cam.Tool.createFromJson(_tool_json()))
    return find_tool()


def _apply_recipe(params):
    _set(params, "tool_spindleSpeed", f"{SPINDLE_RPM} rpm")
    _set(params, "tool_rampSpindleSpeed", f"{SPINDLE_RPM} rpm")
    _set(params, "tool_feedCutting", f"{CUT_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_feedEntry", f"{CUT_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_feedExit", f"{CUT_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_feedTransition", f"{CUT_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_feedRamp", f"{RAMP_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_feedPlunge", f"{PLUNGE_FEED_MM_PER_MIN} mm/min")
    _set(params, "tool_coolant", "'disabled'")  # The machine has no coolant system.
    _set(params, "tool_rampAngle", f"{RAMP_ANGLE_DEG} deg")
    # Most moves are under 0.5 mm, where the controller's acceleration limits speed more than the
    # programmed feed does. Fitting arcs merges them. Fusion's time estimate doesn't show this gain.
    _set(params, "smoothingFilter", "true")
    # Fusion's default 15 mm clearance is wasted air time: the holder already clears the stock.
    _set(params, "retractHeight_mode", "'from stock top'")
    _set(params, "retractHeight_offset", f"{RETRACT_ABOVE_STOCK_MM} mm")
    _set(params, "clearanceHeight_mode", "'from retract height'")
    _set(params, "clearanceHeight_offset", f"{CLEARANCE_ABOVE_RETRACT_MM} mm")


def _avoid_uncut_stock(params, avoidance_mode="'non trimmed'"):
    """Keep the shank and holder off wax that hasn't been cut yet; Fusion's default is off.

    Scallop doesn't offer Adaptive's 'non trimmed' mode, so it passes 'trimmed'.
    """
    _set(params, "useShaftAndHolder", "true")
    _set(params, "shaftAndHolderMode", avoidance_mode)
    _set(params, "useShaft", "true")
    _set(params, "useHolder", "true")
    _set(params, "shaftClearance", f"{SHANK_CLEARANCE_MM} mm")
    _set(params, "holderClearance", f"{HOLDER_CLEARANCE_MM} mm")


def _sketch_line(root, sketch_name, index):
    return root.sketches.itemByName(sketch_name).sketchCurves.sketchLines.item(index)


def _aim_tool(params, root, azimuth_deg, axes_sketch_name="Tool Axes"):
    """Aim the tool along one side direction. Each axes sketch's lines run in azimuth order, 90 deg apart.

    The tool's X axis stays on a level Tool Axes line, which is square to the tilted lines too.
    """
    line_index = azimuth_deg // 90
    _set(params, "overrideToolView", "true")
    _set(params, "view_orientation_mode", "'axesZX'")
    _select(params, "view_orientation_axisZ", [_sketch_line(root, axes_sketch_name, line_index)])
    _select(params, "view_orientation_axisX", [_sketch_line(root, "Tool Axes", (line_index + 1) % 4)])


def _side_boundary_name(prefix, azimuth_deg):
    return f"{prefix} YZ" if azimuth_deg in (90, 270) else f"{prefix} XY"


def _limit_to_sketch(params, root, sketch_name):
    """Keep the tool center inside one of build_model's rectangles, away from the stump and collet."""
    _set(params, "boundaryMode", "'selection'")
    contours = params.itemByName("machiningBoundarySel").value
    selections = contours.getCurveSelections()
    selections.clear()
    selections.createNewChainSelection().inputGeometry = [_sketch_line(root, sketch_name, 0)]
    contours.applyCurveSelections(selections)
    _set(params, "boundaryContainment", "'center'")
    _set(params, "boundaryOffset", "0 mm")


def _floor_above_part_axis_mm(azimuth_deg):
    """Return how far above the part axis the tool tip stops on this side.

    Sides 0 and 180 face the Knight's flanks, which are thin, so these sides can cut all the way
    through and still keep the head's walls within the flutes. A ball only reaches its full width one
    radius above its tip, so the tip goes half a diameter past the axis to clear the silhouette.

    Sides 90 and 270 face the nose and back. Wax as tall as the stock stands beside the tool there,
    so they stop where the shank clears the stock's top, and sides 0 and 180 cut what remains.
    """
    if azimuth_deg in (0, 180):
        return -TOOL_DIAMETER_MM / 2
    return geo.HEAD_RADIUS_MM - TOOL_FLUTE_LENGTH_MM


def _limit_depth(params, root, floor_above_axis_mm):
    _set(params, "topHeight_mode", "'from stock top'")
    _set(params, "topHeight_offset", "0 mm")
    _set(params, "bottomHeight_mode", "'from point'")
    _select(params, "bottomHeight_ref", [root.sketches.itemByName("Work Origin (G54)").sketchPoints.item(1)])
    _set(params, "bottomHeight_offset", f"{floor_above_axis_mm} mm")


def _tilted_floor_mm(floor_above_axis_mm):
    """Floor offset from the stock-top G54 point, along the tilted tool, passing the axis at the finish's low end.

    A floor square to a tilted tool slopes through the part, and the G54 point is far up it. Measured
    at the stock top, a level-tool floor would cut off everything below the Knight's top.
    """
    tilt_rad = math.radians(geo.FINISH_TILT_DEG)
    return (geo.FINISH_LOW_Y_MM - geo.STOCK_TOP_Y_MM) * math.sin(tilt_rad) + floor_above_axis_mm * math.cos(tilt_rad)


def _use_rest_material(params, ignore_thinner_than_mm):
    _set(params, "useRestMachining", "true")
    _set(params, "restMaterialSource", "'previousOperations'")
    _set(params, "ignoreStockLessThan", f"{ignore_thinner_than_mm} mm")


def _adaptive_input(setup, tool, root, azimuth_deg, display_name, boundary_sketch_name, floor_above_axis_mm):
    op_input = setup.operations.createInput("adaptive")
    op_input.displayName = display_name
    op_input.tool = tool
    params = op_input.parameters
    _apply_recipe(params)
    for feed_name in ("tool_feedCutting", "tool_feedEntry", "tool_feedExit", "tool_feedTransition"):
        _set(params, feed_name, f"{ROUGH_FEED_MM_PER_MIN} mm/min")
    _aim_tool(params, root, azimuth_deg)
    _limit_to_sketch(params, root, boundary_sketch_name)
    _limit_depth(params, root, floor_above_axis_mm)
    _set(params, "optimalLoad", f"{ROUGH_LOAD_MM} mm")
    _set(params, "maximumStepdown", f"{ROUGH_STEPDOWN_MM} mm")
    _set(params, "useStockToLeave", "true")
    _set(params, "stockToLeave", f"{ROUGH_STOCK_TO_LEAVE_MM} mm")
    _set(params, "verticalStockToLeave", f"{ROUGH_STOCK_TO_LEAVE_MM} mm")
    _avoid_uncut_stock(params)
    # Fusion's Simulate flagged rapids going down into the part. Staying down means fewer of them.
    # The default 2.5 mm stop sits only 0.5 mm above the previous 3 mm level, below a ball's ridges.
    _set(params, "stayDownLevel", f"'{ROUGH_STAY_DOWN_LEVEL}'")
    _set(params, "rampClearanceHeight", f"{ROUGH_RAPID_STOP_ABOVE_LEVEL_MM} mm")
    _set(params, "verticalLeadRadius", f"{ROUGH_ENTRY_LEAD_RADIUS_MM} mm")
    _set(params, "stayDownDistance", f"{ROUGH_MAX_STAY_DOWN_MM} mm")
    _set(params, "helicalRampDiameter", f"{ROUGH_HELIX_DIAMETER_MM} mm")
    _set(params, "minimumRampDiameter", f"{ROUGH_MIN_HELIX_DIAMETER_MM} mm")
    # Extra levels for flat areas add over a minute per side. A later finish takes that wax instead.
    _set(params, "flatAreaMachining", "false")
    return op_input


def add_rough(setup, tool, root, azimuth_deg, use_rest_material):
    op_input = _adaptive_input(setup, tool, root, azimuth_deg, f"Rough side {azimuth_deg}",
                               _side_boundary_name("Boundary", azimuth_deg), _floor_above_part_axis_mm(azimuth_deg))
    if use_rest_material:
        _use_rest_material(op_input.parameters, ROUGH_IGNORE_REST_THINNER_THAN_MM)
    return setup.operations.add(op_input)


def add_ears_rough(setup, tool, root):
    op_input = _adaptive_input(setup, tool, root, EARS_SIDE_DEG, f"Rough ears {EARS_SIDE_DEG}",
                               "Ears Boundary YZ", EARS_FLOOR_ABOVE_AXIS_MM)
    _use_rest_material(op_input.parameters, ROUGH_IGNORE_REST_THINNER_THAN_MM)
    return setup.operations.add(op_input)


def _scallop_input(setup, tool, root, azimuth_deg, display_name, boundary_sketch_name, floor_above_axis_mm):
    # Parallel passes cross the silhouette, so the tool runs straight down the part's edge on nearly
    # every pass. Scallop rings follow the walls instead.
    op_input = setup.operations.createInput("scallop")
    op_input.displayName = display_name
    op_input.tool = tool
    params = op_input.parameters
    _apply_recipe(params)
    _aim_tool(params, root, azimuth_deg)
    _limit_to_sketch(params, root, boundary_sketch_name)
    _limit_depth(params, root, floor_above_axis_mm)
    _set(params, "boundaryOffset", f"{-FINISH_LEAD_ALLOWANCE_MM} mm")
    _set(params, "stepover", f"{FINISH_STEPOVER_MM} mm")
    _set(params, "useStockToLeave", "false")
    # Roughing can leave more than the default 2 mm in spots a 1/8 in ball can't reach.
    _set(params, "safeDistance", f"{FINISH_RAPID_STOP_ABOVE_MODEL_MM} mm")
    return op_input


def add_finish(setup, tool, root, azimuth_deg, use_rest_material):
    op_input = _scallop_input(setup, tool, root, azimuth_deg, f"Finish side {azimuth_deg}",
                              _side_boundary_name("Finish Boundary", azimuth_deg),
                              _tilted_floor_mm(_floor_above_part_axis_mm(azimuth_deg)))
    _aim_tool(op_input.parameters, root, azimuth_deg, "Tilted Tool Axes")
    # The sloped floor reaches past the level passes' depth, so the shank needs its own protection.
    _avoid_uncut_stock(op_input.parameters, "'trimmed'")
    if use_rest_material:
        _use_rest_material(op_input.parameters, FINISH_IGNORE_REST_THINNER_THAN_MM)
    return setup.operations.add(op_input)


def add_patch_finish(setup, tool, root, azimuth_deg, patch_name):
    """Finish a small area that rest machining misses. patch_name is "Top" or "Snout"."""
    display_name = f"Finish {patch_name.lower()} {azimuth_deg}"
    op_input = _scallop_input(setup, tool, root, azimuth_deg, display_name, f"{patch_name} Patch XY",
                              _floor_above_part_axis_mm(azimuth_deg))
    return setup.operations.add(op_input)


def add_ears_finish(setup, tool, root):
    op_input = _scallop_input(setup, tool, root, EARS_SIDE_DEG, f"Finish ears {EARS_SIDE_DEG}",
                              "Ears Boundary YZ", EARS_FLOOR_ABOVE_AXIS_MM)
    return setup.operations.add(op_input)


def _mount_part_in_collet(params, origin_point):
    """Tell machine simulation where the collet holds the part. Only the simulation reads this.

    By default Fusion attaches the bottom of the model's box, measured along WCS Z, to the table
    center. WCS Z runs sideways through this part, so the default puts the part off the B axis and
    too low, and Simulate with Machine reports false collisions.
    """
    _set(params, "job_positionReference_origin_mode", "'point'")
    _select(params, "job_positionReference_origin_point", [origin_point])
    _set(params, "job_positionYOffset", f"{geo.STOCK_TOP_Y_MM - MACHINE_TABLE_ATTACH_Y_MM} mm")


def _system_machine(library):
    machine = library.machineAtURL(adsk.core.URL.create(SYSTEM_MACHINE_URL))
    # A setup rejects a system-library machine with "setMachineResult.has_value()" unless its model is
    # cleared. This changes only this copy. The kinematics and post stay, so the G-code doesn't change.
    machine.clearSimulationModel()
    return machine


def _find_machine():
    """Prefer the user's Local library copy, because Simulate with Machine needs its 3D model."""
    library = adsk.cam.CAMManager.get().libraryManager.machineLibrary
    local_url = library.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)
    for machine in library.childMachines(local_url):
        if machine.vendor == MACHINE_VENDOR and machine.model == MACHINE_MODEL:
            return machine
    return _system_machine(library)


def create_setup(cam, root):
    bodies = root.bRepBodies
    setup_input = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
    setup_input.name = "Knight"
    setup_input.models = [bodies.itemByName("Knight"), bodies.itemByName("Mount")]
    setup_input.stockMode = adsk.cam.SetupStockModes.SolidStock
    setup_input.stockSolids = [bodies.itemByName("Knight Stock")]
    # Assign this when a setup is created. Swapping the machine on a document that already has
    # another version of its 3D model loaded fails with "setMachineResult.has_value()".
    setup_input.machine = _find_machine()
    params = setup_input.parameters
    _set(params, "wcs_orientation_mode", "'modelOrientation'")
    _set(params, "wcs_origin_mode", "'point'")
    origin_point = root.sketches.itemByName("Work Origin (G54)").sketchPoints.item(1)
    _select(params, "wcs_origin_point", [origin_point])
    _mount_part_in_collet(params, origin_point)
    _set(params, "job_workOffset", "1")
    _set(params, "job_programName", f"'{PROGRAM_NUMBER}'")
    return cam.setups.add(setup_input)


def report(cam, operations):
    for op in operations:
        minutes = None
        if op.hasToolpath and not op.isGenerating:
            rapid_cm_per_sec = 1524.0 / 10.0 / 60.0
            minutes = cam.getMachiningTime(op, 1.0, rapid_cm_per_sec, 15).machiningTime / 60.0
        print(f"{op.name}: generating={op.isGenerating} hasToolpath={op.hasToolpath} "
              f"valid={op.isToolpathValid} minutes={minutes} warn={op.warning!r} err={op.error!r}")


def post_setup(cam, setup, output_folder, file_name):
    """Post one setup with Penta's RWO settings: G54 on the stock top, rotations through G59.3."""
    program_input = cam.ncPrograms.createInput()
    program_input.displayName = file_name
    params = program_input.parameters
    params.itemByName("nc_program_filename").value.value = file_name
    params.itemByName("nc_program_output_folder").value.value = output_folder
    params.itemByName("nc_program_openInEditor").value.value = False
    program_input.operations = [setup]
    program = cam.ncPrograms.add(program_input)

    # Left unset, a program silently defaults to the last post used, which could be
    # for a different machine, so always name the post.
    program.parameters.itemByName("nc_program_post").value.value = POST_URL
    post_params = program.postParameters
    post_params.itemByName("useTiltedWorkplane").value.value = "9"  # RWO stores rotations in G59.3.
    program.updatePostParameters(post_params)
    program.postProcess(adsk.cam.NCProgramPostProcessOptions.create())
    return program


def build_all(cam, root):
    tool = ensure_tool(cam)
    setup = create_setup(cam, root)
    for index, azimuth_deg in enumerate(geo.SIDE_AZIMUTHS_DEG):
        add_rough(setup, tool, root, azimuth_deg, use_rest_material=index > 0)
        if azimuth_deg == EARS_SIDE_DEG:
            add_ears_rough(setup, tool, root)
    for azimuth_deg in geo.SIDE_AZIMUTHS_DEG:
        add_finish(setup, tool, root, azimuth_deg, use_rest_material=azimuth_deg in (0, 180))
        if azimuth_deg == EARS_SIDE_DEG:
            add_ears_finish(setup, tool, root)
    for azimuth_deg in (0, 180):
        add_patch_finish(setup, tool, root, azimuth_deg, "Top")
        add_patch_finish(setup, tool, root, azimuth_deg, "Snout")
    return setup
