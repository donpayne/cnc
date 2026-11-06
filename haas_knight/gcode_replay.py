"""Reads metric posted mill programs and the model's faces for the checks in this folder."""
import json
import math
import re
from typing import NamedTuple

import numpy as np

import knight_job as job

PASS_HEADER = re.compile(r"\(((?:Rough|Semi|Flank|Finish|Detail|Trace)[^)]*)\)")
B_WORD = re.compile(r"\bB(-?\d*\.?\d+)")
C_WORD = re.compile(r"\bC(-?\d*\.?\d+)")
TOOL_CHANGE = re.compile(r"\bT(\d+)\s*M0?6")
LINEAR_AXIS_WORD = re.compile(r"\b[XYZ]-?\d")
MOVE_WORD = re.compile(r"([XYZIJKF])(-?\d*\.?\d+)")
# Axis order per plane keeps G2 and G3 true in all three: G18 is viewed from +Y, so it runs Z to X.
PLANE_AXES = {17: (0, 1, 2), 18: (2, 0, 1), 19: (1, 2, 0)}


class Pass(NamedTuple):
    name: str
    tool: int
    b_deg: float
    c_deg: float
    lines: list


class Move(NamedTuple):
    start: tuple
    end: tuple
    motion: int
    plane: int
    arc_center_offsets: tuple
    feed_mm_per_min: float
    source: str

    @property
    def is_link(self):
        return self.motion == 0 or self.feed_mm_per_min >= job.LINK_FEED_MM_PER_MIN


def code_of(line):
    """A G-code line without its comment or N number."""
    return re.sub(r"^N\d+\s*", "", re.sub(r"\([^)]*\)", "", line)).strip()


def surface_samples(spacing_mm, skipped_faces=frozenset()):
    """Points spread over the model's triangles, with the face each one lies on."""
    points, owners = [], []
    with open(job.FACES_PATH) as faces_file:
        faces = json.load(faces_file)
    for face in faces:
        if face["index"] in skipped_faces:
            continue
        nodes = np.array(face["nodes_mm"]).reshape(-1, 3)
        for a, b, c in nodes[np.array(face["tris"]).reshape(-1, 3)]:
            longest = max(np.linalg.norm(a - b), np.linalg.norm(b - c), np.linalg.norm(c - a))
            divisions = max(1, int(math.ceil(longest / spacing_mm)))
            grid = np.array([(i, j) for i in range(divisions + 1) for j in range(divisions + 1 - i)]) / divisions
            points.append(grid[:, :1] * a + grid[:, 1:] * b + (1 - grid.sum(axis=1, keepdims=True)) * c)
            owners.append(np.full(len(grid), face["index"]))
    return np.vstack(points), np.concatenate(owners)


def read_passes(path):
    """Every pass in program order. The post omits an unchanged tool, B or C, so each pass inherits them."""
    passes = []
    tool = b_deg = c_deg = None
    for name, lines in _split_by_pass_header(path):
        tool = _tool_after(lines, tool)
        b_deg, c_deg = _pose_after(lines, b_deg, c_deg)
        passes.append(Pass(name, tool, b_deg, c_deg, lines))
    return passes


def _split_by_pass_header(path):
    sections = []
    with open(path, errors="replace") as program:
        for line in program:
            header = PASS_HEADER.fullmatch(line.strip())
            if header:
                sections.append((header.group(1), []))
            elif sections:
                sections[-1][1].append(line)
    return sections


def _tool_after(lines, tool):
    for line in lines:
        change = TOOL_CHANGE.search(code_of(line))
        if change:
            return int(change.group(1))
    return tool


def _pose_after(lines, b_deg, c_deg):
    # Only the rotary words before the first cut count: the end of the program sends B and C home.
    for line in lines:
        code = code_of(line)
        found_b, found_c = B_WORD.search(code), C_WORD.search(code)
        if found_b:
            b_deg = float(found_b.group(1))
        if found_c:
            c_deg = float(found_c.group(1))
        is_first_cut = not (found_b or found_c) and LINEAR_AXIS_WORD.search(code) and "G53" not in code
        if is_first_cut:
            break
    return b_deg, c_deg


def read_moves(lines):
    """Moves with a known start and end, in the program's work frame."""
    moves = []
    position, motion, plane, feed = [None, None, None], 0, 17, 0.0
    for line in lines:
        code = code_of(line)
        if "G53" in code:
            continue
        for g_code in map(int, re.findall(r"\bG(\d+)", code)):
            if g_code in (0, 1, 2, 3):
                motion = g_code
            elif g_code in PLANE_AXES:
                plane = g_code
        words = dict(MOVE_WORD.findall(code))
        feed = float(words.get("F", feed))
        start = tuple(position)
        for axis, letter in enumerate("XYZ"):
            if letter in words:
                position[axis] = float(words[letter])
        end = tuple(position)
        if None in start or None in end or start == end:
            continue
        offsets = tuple(float(words.get(letter, 0.0)) for letter in "IJK")
        moves.append(Move(start, end, motion, plane, offsets, feed, code))
    return moves


def sample_move(move, step_mm):
    """Points along a move. Arcs are followed, because reading them as chords shows false errors."""
    if move.motion in (2, 3):
        return _sample_arc(move, step_mm)
    begin, end = np.array(move.start), np.array(move.end)
    count = max(1, int(np.linalg.norm(end - begin) / step_mm))
    return begin + (end - begin) * np.linspace(0, 1, count + 1)[:, None]


def _sample_arc(move, step_mm):
    first, second, third = PLANE_AXES[move.plane]
    start, end = move.start, move.end
    center_first = start[first] + move.arc_center_offsets[first]
    center_second = start[second] + move.arc_center_offsets[second]
    radius = math.hypot(start[first] - center_first, start[second] - center_second)
    begin_angle = math.atan2(start[second] - center_second, start[first] - center_first)
    sweep = math.atan2(end[second] - center_second, end[first] - center_first) - begin_angle
    if move.motion == 3 and sweep <= 0:
        sweep += 2 * math.pi
    if move.motion == 2 and sweep >= 0:
        sweep -= 2 * math.pi
    count = max(1, int(abs(sweep) * radius / step_mm))
    fraction = np.linspace(0, 1, count + 1)
    points = np.zeros((count + 1, 3))
    points[:, first] = center_first + radius * np.cos(begin_angle + sweep * fraction)
    points[:, second] = center_second + radius * np.sin(begin_angle + sweep * fraction)
    points[:, third] = start[third] + (end[third] - start[third]) * fraction
    return points


def cut_and_link_points(moves, step_mm):
    cut = [sample_move(move, step_mm) for move in moves if not move.is_link]
    link = [sample_move(move, step_mm) for move in moves if move.is_link]
    return (np.vstack(cut) if cut else np.empty((0, 3))), (np.vstack(link) if link else np.empty((0, 3)))


def machine_frame(points, b_deg, c_deg):
    """Model points in the frame the G-code commands at this B and C (Haas G254)."""
    beta, theta = math.radians(b_deg), math.radians(c_deg)
    along = points[:, 0] * math.cos(theta) + points[:, 1] * math.sin(theta)
    across = -points[:, 0] * math.sin(theta) + points[:, 1] * math.cos(theta)
    height = points[:, 2] - job.G54_MODEL_Z_MM
    return np.column_stack((along * math.cos(beta) - height * math.sin(beta), across, height * math.cos(beta) + along * math.sin(beta)))
