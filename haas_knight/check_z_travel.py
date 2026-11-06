"""Shows how close each tool and pass comes to the lower Z limit, and the shortest tool that still reaches.

At B90 the part axis sits at the B pivot height, so:
  machine Z = pivot Z + work Z + gauge-to-tip length - nose height above the table at Z0.
This matched Simulate's readings. Tilted passes lift the work origin well above the pivot, so B90 sets
the limit. Tool lengths come from knight_job.TOOLS.

Usage: python3 -B check_z_travel.py <program.nc>
"""
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


def shortest_tool_mm(work_z):
    return job.Z_LIMIT_MM - job.B_PIVOT_Z_MM + job.NOSE_HEIGHT_AT_Z0_MM - work_z


def main():
    passes = replay.read_passes(sys.argv[1])
    b90_rows = []
    for one_pass in passes:
        work_z = lowest_work_z(one_pass)
        if work_z is None or one_pass.b_deg != B90_DEG:
            continue
        margin = job.TOOLS[one_pass.tool].gauge_to_tip_mm - shortest_tool_mm(work_z)
        b90_rows.append((margin, one_pass.name, one_pass.tool, work_z))

    print("tool | deepest B90 work Z | pass | shortest length | modeled | margin")
    for tool_number in sorted({row[2] for row in b90_rows}):
        margin, name, _, work_z = min(row for row in b90_rows if row[2] == tool_number)
        print(f"T{tool_number} | {work_z} | {name} | {shortest_tool_mm(work_z):.2f} | {job.TOOLS[tool_number].gauge_to_tip_mm} | {margin:.2f}")

    print(f"\npasses under {TIGHT_MARGIN_MM:.0f} mm of margin:")
    for margin, name, tool_number, work_z in sorted(row for row in b90_rows if row[0] < TIGHT_MARGIN_MM):
        print(f"  {margin:6.2f} | {name} | T{tool_number} | work Z {work_z}")

    print(f"\nnot at B90, so not checked: { {one_pass.name: one_pass.b_deg for one_pass in passes if one_pass.b_deg != B90_DEG} }")


if __name__ == "__main__":
    main()
