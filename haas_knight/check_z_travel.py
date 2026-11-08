"""Shows how close each tool and pass comes to the lower Z limit, and the shortest tool that still reaches.

The work origin sits on the C axis, which passes through the B pivot, so at tilt B it is at
  pivot Z + (origin height above the table - pivot Z) x cos B,
and the post's Z words are measured from there along the tool:
  machine Z = that + work Z + gauge-to-tip length - nose height above the table at Z0.
At B90 the origin is at pivot height whatever its height, which matched Simulate's readings on the Knight. Below B90 it
rises, but past B90 it drops below the pivot: on the Queen, B95 lowered it 17.5 mm and ran out of travel.

Every pass is checked when the job file gives WORK_ORIGIN_ABOVE_TABLE_MM, Fusion's Part Position offset. Without it,
only B90 passes are. Tool lengths come from knight_job.TOOLS.

Usage: python3 -B check_z_travel.py <program.nc>
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode_replay as replay
import knight_job as job

TIGHT_MARGIN_MM = 5.0
Z_WORD = re.compile(r"\bZ(-?[\d.]+)")
B90_DEG = 90.0


def lowest_work_z(one_pass):
    z_values = []
    for line in one_pass.lines:
        code = replay.code_of(line)
        z_word = Z_WORD.search(code)
        if z_word and "G53" not in code:
            z_values.append(float(z_word.group(1)))
    return min(z_values, default=None)


def work_origin_z_mm(b_deg):
    if b_deg == B90_DEG:
        return job.B_PIVOT_Z_MM
    pivot_to_origin_mm = job.WORK_ORIGIN_ABOVE_TABLE_MM - job.B_PIVOT_Z_MM
    return job.B_PIVOT_Z_MM + pivot_to_origin_mm * math.cos(math.radians(b_deg))


def shortest_tool_mm(work_z, b_deg):
    return job.Z_LIMIT_MM - work_origin_z_mm(b_deg) + job.NOSE_HEIGHT_AT_Z0_MM - work_z


def main():
    passes = replay.read_passes(sys.argv[1])
    can_check_any_tilt = hasattr(job, "WORK_ORIGIN_ABOVE_TABLE_MM")
    rows = []
    unchecked = {}
    for one_pass in passes:
        work_z = lowest_work_z(one_pass)
        if work_z is None:
            continue
        if not can_check_any_tilt and one_pass.b_deg != B90_DEG:
            unchecked[one_pass.name] = one_pass.b_deg
            continue
        margin = job.TOOLS[one_pass.tool].gauge_to_tip_mm - shortest_tool_mm(work_z, one_pass.b_deg)
        rows.append((margin, one_pass.name, one_pass.tool, one_pass.b_deg, work_z))

    print("tool | B | deepest work Z | pass | shortest length | modeled | margin")
    for tool_number in sorted({row[2] for row in rows}):
        margin, name, _, b_deg, work_z = min(row for row in rows if row[2] == tool_number)
        shortest_mm = shortest_tool_mm(work_z, b_deg)
        print(f"T{tool_number} | {b_deg:g} | {work_z} | {name} | {shortest_mm:.2f} | {job.TOOLS[tool_number].gauge_to_tip_mm} | {margin:.2f}")

    print(f"\npasses under {TIGHT_MARGIN_MM:.0f} mm of margin:")
    for margin, name, tool_number, b_deg, work_z in sorted(row for row in rows if row[0] < TIGHT_MARGIN_MM):
        print(f"  {margin:6.2f} | {name} | T{tool_number} | B{b_deg:g} | work Z {work_z}")

    if unchecked:
        print(f"\nnot at B90, and the job file has no WORK_ORIGIN_ABOVE_TABLE_MM, so not checked: {unchecked}")


if __name__ == "__main__":
    main()
