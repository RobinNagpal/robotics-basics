"""The pictures for the six pages of solution 4, a world model then plan with it.

Three drawings, each carrying one shape the prose on its page cannot carry. The
chapter already has five pictures from ``make_10_images.py`` and two flow charts
from ``make_solution_flows_b.py``, so nothing here repeats the model's question
and answer, the cross-entropy search contracting, the sequence that beats one
push at a time, the friction the model absorbs, the data it takes, or the five
copies and what they are for.

    worldmodel-pages-the-pushs-own-frame.png   the same glass and the same
                                        neighbour pushed on two headings: two
                                        readings in the table's frame, one row
                                        in the push's own.
    worldmodel-pages-the-jitter-check.png  why a candidate is asked about on
                                        five readings of the table rather than
                                        one: a hole narrow enough to be found
                                        by luck does not survive a shift.
    worldmodel-pages-what-the-push-says.png  the five numbers of a push, and
                                        which three the search chooses and
                                        which two are arithmetic on a measured
                                        width.

Every number written into these pictures is read out of ``code/src/``, and the
constant that holds it is named in a comment beside it below. Each picture's own
claim is computed here from those constants and asserted, so a run stops rather
than drawing something untrue.

One picture is a drawing of a mechanism rather than a measurement, and says so
on its face: the trained weights are not in the repository, so the shape of the
model's topple opinion in the jitter picture is drawn. The limit it is compared
against, the number of extra readings and their sizes are all real.

The sheets are the inch-coordinate sheets ``make_solution_flows_a`` draws its
flow charts on, so a millimetre on the table is a fixed number of inches on the
paper and every circle comes out round. The same module's audit is run on each
sheet.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_world_model_pages.py
"""

from __future__ import annotations

import math

import numpy as np
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    WARN,
    save,
)
from make_solution_flows_a import _tint, box, finish, note, sheet, title
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

# ------------------------------------------------------------------ the numbers
#
# All of these are read out of code/src/09_pushing-the-glasses-apart/, and the
# constant that holds each one is named so that a reader can check it in one
# step.

GRIP_ROOM_MM = 70.0        # bench/bench.py GRIP_ROOM = 0.070

STANDOFF_MM = 20.0         # 04-a-world-model/features.py STANDOFF = 0.02
FEEL_PAST_MM = 10.0        # 04-a-world-model/features.py FEEL_PAST = 0.01
OFFSET_SHARE = 0.7         # 04-a-world-model/features.py OFFSET = 0.7
TRAVEL_MM = (10.0, 100.0)  # 04-a-world-model/features.py TRAVEL = (0.01, 0.10)
OTHERS = 5                 # 04-a-world-model/features.py OTHERS
INPUTS = 34                # 04-a-world-model/features.py INPUTS, with KINDS of 4

TOPPLE_LIMIT = 0.01        # 04-a-world-model/plan.py TOPPLE_LIMIT = 0.01
JITTERS = 4                # 04-a-world-model/plan.py JITTERS = 4
JITTER_POSITION_MM = 1.0   # 04-a-world-model/plan.py JITTER_POSITION = 0.001
JITTER_WIDTH_MM = 3.0      # 04-a-world-model/plan.py JITTER_WIDTH = 0.003
ENSEMBLE = 5               # 04-a-world-model/model.py ENSEMBLE = 5

# The range a kind's widest width is drawn from, so that every width used below
# is one the cell could really produce.
KIND_WIDEST_MM = 105.0     # diagram_style.KIND_WIDEST
KIND_NARROWEST_MM = 65.0   # diagram_style.KIND_NARROWEST

# Chosen for the drawings, not read from anywhere: a width inside the declared
# range, and a push length inside the declared range.
DRAWN_RIM_MM = 90.0
DRAWN_NARROW_RIM_MM = 78.0
DRAWN_TRAVEL_MM = 40.0

# features.py builds its input row out of these pieces, and this is the sum it
# has to come to: one yes-or-no column per kind, three measurements of the
# pushed glass, two numbers for the push, and five numbers for each other slot.
assert INPUTS == 4 + 3 + 2 + OTHERS * 5

assert KIND_NARROWEST_MM <= DRAWN_RIM_MM <= KIND_WIDEST_MM
assert KIND_NARROWEST_MM <= DRAWN_NARROW_RIM_MM <= KIND_WIDEST_MM
assert TRAVEL_MM[0] <= DRAWN_TRAVEL_MM <= TRAVEL_MM[1]


# --------------------------------------------------------------------------- #
# Drawing on an inch sheet, in millimetres
# --------------------------------------------------------------------------- #


class Patch:
    """A patch of table top on an inch sheet: millimetres in, inches out."""

    def __init__(self, axis, origin: tuple[float, float], scale: float):
        self.axis = axis
        self.origin = origin
        self.scale = scale

    def at(self, x: float, y: float = 0.0) -> tuple[float, float]:
        return self.origin[0] + self.scale * x, self.origin[1] + self.scale * y

    def length(self, mm: float) -> float:
        return self.scale * mm

    def glass(self, centre, rim: float, *, colour=GLASS, alpha=0.30, lw=1.1, zorder=3):
        self.axis.add_patch(
            Circle(self.at(*centre), self.length(rim / 2.0), facecolor=colour, alpha=alpha,
                   edgecolor=colour, lw=lw, zorder=zorder)
        )
        self.axis.add_patch(
            Circle(self.at(*centre), self.length(rim * 0.48 / 2.0), facecolor="none",
                   edgecolor=colour, lw=0.9, ls=(0, (3, 2)), alpha=0.9, zorder=zorder + 1)
        )

    def arrow(self, start, end, *, colour=INK, lw=1.5, zorder=6, head=11.0):
        self.axis.add_patch(
            FancyArrowPatch(self.at(*start), self.at(*end), arrowstyle="-|>",
                            mutation_scale=head, linewidth=lw, color=colour,
                            shrinkA=0, shrinkB=0, zorder=zorder)
        )

    def line(self, start, end, *, colour=MUTED, lw=1.0, dashed=False, zorder=2):
        self.axis.plot(
            [self.at(*start)[0], self.at(*end)[0]],
            [self.at(*start)[1], self.at(*end)[1]],
            color=colour, lw=lw, ls=(0, (3, 2)) if dashed else "solid", zorder=zorder,
        )


def frame(heading_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Unit vectors along the push and to its left, as features.py builds them."""
    radians = math.radians(heading_deg)
    along = np.array([math.cos(radians), math.sin(radians)])
    return along, np.array([-along[1], along[0]])


# --------------------------------------------------------------------------- #
# 1. the push's own frame
# --------------------------------------------------------------------------- #

# Where the neighbour stands, written the way the model is shown it: so far
# ahead of the pushed glass along the push, and so far to the push's left. The
# whole point of the picture is that this pair of numbers is what goes in, and
# the heading does not.
AHEAD_MM, LEFT_MM = 30.0, 92.0
HEADINGS_DEG = (35.0, 160.0)


def the_pushs_own_frame() -> None:
    """Two pushes that differ only in heading, reaching the model as one row.

    In the table's north and east the neighbour sits at two unrelated pairs of
    numbers. Measured along the push and across it, it sits at one pair. The
    prose can state that; a reader cannot see a rotation stated.
    """
    # The pair is crowded and the push heads away from the neighbour, which is
    # the situation the planner really faces.
    gap = math.hypot(AHEAD_MM, LEFT_MM)
    assert gap > (DRAWN_RIM_MM + DRAWN_NARROW_RIM_MM) / 2.0, "the two glasses must not overlap"
    assert gap < GRIP_ROOM_MM + DRAWN_NARROW_RIM_MM / 2.0, "the pair has to be crowded"

    width, height = 10.0, 7.8
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "The same situation on two headings is one row, not two")

    scale = 0.014                  # inches per millimetre
    panels = ((2.80, 5.25), (7.40, 5.25))

    # The table's own north and east, drawn once for the sheet, because the
    # table does not turn when the push does.
    compass = Patch(axis, (0.78, 6.30), scale)
    compass.arrow((0.0, 0.0), (28.0, 0.0), colour=MUTED, lw=1.0, head=8.0)
    compass.arrow((0.0, 0.0), (0.0, 28.0), colour=MUTED, lw=1.0, head=8.0)
    note(axis, *compass.at(32.0, 0.0), "east", colour=MUTED, ha="left", size=NOTE_SIZE)
    note(axis, *compass.at(0.0, 34.0), "north", colour=MUTED, ha="center", size=NOTE_SIZE)
    note(axis, *compass.at(-10.0, -30.0), "the table's frame,\nthe same in both",
         colour=MUTED, ha="left", size=NOTE_SIZE)

    for (centre_x, centre_y), heading in zip(panels, HEADINGS_DEG, strict=True):
        along, left = frame(heading)
        offset = AHEAD_MM * along + LEFT_MM * left

        # The claim the panel makes, checked before it is drawn.
        assert abs(float(along @ offset) - AHEAD_MM) < 1e-9
        assert abs(float(left @ offset) - LEFT_MM) < 1e-9

        patch = Patch(axis, (centre_x, centre_y), scale)

        # The push, and the frame it carries with it.
        back = -(DRAWN_RIM_MM / 2.0 + STANDOFF_MM)
        patch.arrow(tuple(back * along), tuple(-DRAWN_RIM_MM / 2.0 * along),
                    colour=INK, lw=2.2)
        patch.arrow((0.0, 0.0), tuple(56.0 * along), colour=INK, lw=1.0, head=9.0)
        patch.arrow((0.0, 0.0), tuple(34.0 * left), colour=GOOD, lw=1.0, head=9.0)
        note(axis, *patch.at(*(42.0 * left)), "left", colour=GOOD, ha="center",
             size=NOTE_SIZE)
        note(axis, *patch.at(*(66.0 * along)), "ahead", colour=INK, ha="center",
             size=NOTE_SIZE)
        note(axis, *patch.at(*((back - 16.0) * along)), "the push", colour=INK,
             ha="center", size=NOTE_SIZE, weight="bold")

        patch.line((0.0, 0.0), tuple(offset), colour=WARN, lw=1.0, dashed=True, zorder=2)
        patch.glass((0.0, 0.0), DRAWN_RIM_MM, colour=GLASS)
        patch.glass(tuple(offset), DRAWN_NARROW_RIM_MM, colour=WARN)

        # Both names sit on the line between the two glasses, pushed outwards
        # past the rims, so they move with the heading instead of landing on it.
        outward = offset / gap
        note(axis, *patch.at(*(outward * (gap + DRAWN_NARROW_RIM_MM / 2.0 + 16.0))),
             "its neighbour", colour=WARN, ha="center", size=NOTE_SIZE)
        note(axis, *patch.at(*(-outward * (DRAWN_RIM_MM / 2.0 + 16.0))),
             "the glass being pushed", colour=INK, ha="center", size=NOTE_SIZE)

        east, north = float(offset[0]), float(offset[1])
        note(axis, centre_x, 3.00,
             f"heading {heading:+.0f}°, and in the table's frame\n"
             f"the neighbour is east {east:+.0f} mm, north {north:+.0f} mm",
             colour=WARN, ha="center", size=NOTE_SIZE, figure=figure)

    # Both readings arrive at the same row, so one box takes two arrows.
    row_top = 2.20
    row = (
        f"one row: the neighbour is {AHEAD_MM:.0f} mm ahead and {LEFT_MM:.0f} mm "
        f"to the left"
    )
    row_bottom = box(figure, axis, width / 2.0, row_top, 5.3, row,
                     edge=GOOD, face=_tint(GOOD, 0.90), size=LABEL_SIZE, weight="bold")
    for centre_x, into_x in ((panels[0][0], width / 2.0 - 1.3), (panels[1][0], width / 2.0 + 1.3)):
        axis.add_patch(
            FancyArrowPatch((centre_x, 2.64), (into_x, row_top + 0.03),
                            arrowstyle="-|>", mutation_scale=11, linewidth=1.2,
                            color=GOOD, shrinkA=0, shrinkB=0, zorder=6)
        )

    bottom = note(axis, width / 2.0, row_bottom - 0.30,
                  "The table's friction is the same everywhere and in every direction, so the "
                  "heading says nothing about what the push will do. Writing the inputs in the\n"
                  "table's frame would ask the model to learn the same relationship again for "
                  "every heading, out of the one thing this solution is short of, which is "
                  "recorded pushes.\n"
                  "The same symmetry gives every recorded push a mirror image, left and right "
                  "swapped, which is another true push and doubles the training set for nothing.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "worldmodel-pages-the-pushs-own-frame.png", bottom - 0.10)
    save(figure, "worldmodel-pages-the-pushs-own-frame.png")


# --------------------------------------------------------------------------- #
# 2. why the topple question is asked five times
# --------------------------------------------------------------------------- #

# The four extra readings, as shifts in millimetres. Four of them, because
# plan.py makes JITTERS of them; their sizes are about JITTER_POSITION_MM,
# which is what the camera's error comes to on a position.
SHIFTS_MM = (-1.5, -0.6, 0.9, 2.1)

# The drawn opinion of the worst copy. A safe push is low wherever the reading
# lands; a hole is a narrow dip in an otherwise high surface, and the dip is
# narrower than the shifts, which is the whole argument.
HOLE_CENTRE_MM, HOLE_HALF_WIDTH_MM = 0.0, 0.35


def _safe_curve(x: np.ndarray) -> np.ndarray:
    return 0.0018 + 0.0005 * np.sin(1.7 * x)


def _hole_curve(x: np.ndarray) -> np.ndarray:
    dip = np.exp(-(((x - HOLE_CENTRE_MM) / HOLE_HALF_WIDTH_MM) ** 2))
    return 0.044 - 0.0380 * dip


def the_jitter_check() -> None:
    """Why the topple question is put to five readings of the table, not one.

    The search tries fifteen hundred candidates and keeps whichever one the
    model likes best, so it finds the places where the model is wrong in a
    favourable direction. A hole that narrow is a shape, and a shape is what a
    picture is for.
    """
    width, height = 9.4, 6.4
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "The topple question is put to five readings of the table, and the worst answer counts")

    left_x, right_x = 1.55, width - 1.35
    base_y, plot_h = 2.30, 3.35
    span_mm, top_chance = 4.0, 0.06

    def at(mm: float, chance: float) -> tuple[float, float]:
        return (left_x + (mm + span_mm) / (2.0 * span_mm) * (right_x - left_x),
                base_y + chance / top_chance * plot_h)

    axis.add_patch(
        Rectangle((left_x, base_y), right_x - left_x, plot_h, facecolor=_tint(MUTED, 0.95),
                  edgecolor=MUTED, lw=0.8, zorder=1)
    )

    # The axes, named rather than ticked: the only value that has to be read off
    # is the limit, and that gets a line of its own.
    for mm in (-4.0, -2.0, 0.0, 2.0, 4.0):
        axis.plot([at(mm, 0.0)[0]] * 2, [base_y, base_y - 0.07], color=MUTED, lw=0.9, zorder=2)
        note(axis, at(mm, 0.0)[0], base_y - 0.22, f"{mm:+.0f}" if mm else "0",
             colour=MUTED, ha="center", size=NOTE_SIZE)
    note(axis, (left_x + right_x) / 2.0, base_y - 0.50,
         "how far the reading of the table is moved, millimetres", colour=INK,
         ha="center", size=NOTE_SIZE)
    for chance in (0.0, 0.02, 0.04, 0.06):
        note(axis, left_x - 0.12, at(0.0, chance)[1], f"{100 * chance:.0f}%", colour=MUTED,
             ha="right", size=NOTE_SIZE)
    note(axis, left_x - 0.75, base_y + plot_h / 2.0,
         f"the worst of the\n{ENSEMBLE} copies' chance\nthat this push\ntopples something",
         colour=INK, ha="center", size=NOTE_SIZE)

    grid = np.linspace(-span_mm, span_mm, 801)
    for curve, colour, label in (
        (_hole_curve, WARN, "a hole in the model"),
        (_safe_curve, GOOD, "a genuinely safe push"),
    ):
        values = curve(grid)
        points = [at(mm, float(v)) for mm, v in zip(grid, values, strict=True)]
        axis.plot([p[0] for p in points], [p[1] for p in points], color=colour, lw=1.8, zorder=4)
        note(axis, at(-3.9, float(curve(np.array([-3.9]))[0]))[0] + 0.10,
             at(0.0, float(curve(np.array([-3.9]))[0]))[1] + 0.17, label,
             colour=colour, ha="left", size=LABEL_SIZE, weight="bold")

    # The limit, and the five readings the candidate is judged on.
    limit_y = at(0.0, TOPPLE_LIMIT)[1]
    axis.plot([left_x, right_x], [limit_y, limit_y], color=INK, lw=1.1, ls=(0, (5, 3)), zorder=5)
    note(axis, right_x - 0.08, limit_y + 0.17,
         f"the limit: {100 * TOPPLE_LIMIT:.0f} in a hundred", colour=INK, ha="right",
         size=NOTE_SIZE, weight="bold")

    for curve, colour in ((_hole_curve, WARN), (_safe_curve, GOOD)):
        axis.add_patch(
            Circle(at(0.0, float(curve(np.array([0.0]))[0])), 0.055, facecolor=colour,
                   edgecolor=colour, zorder=7)
        )
        for shift in SHIFTS_MM:
            axis.add_patch(
                Circle(at(shift, float(curve(np.array([shift]))[0])), 0.055, facecolor="white",
                       edgecolor=colour, lw=1.4, zorder=7)
            )

    # The claim the picture makes, checked before anybody reads it.
    assert len(SHIFTS_MM) == JITTERS
    assert float(_hole_curve(np.array([0.0]))[0]) < TOPPLE_LIMIT, "the hole must look safe"
    assert all(float(_hole_curve(np.array([s]))[0]) > TOPPLE_LIMIT for s in SHIFTS_MM), (
        "every shifted reading must find the hole out"
    )
    assert all(float(_safe_curve(np.array([s]))[0]) < TOPPLE_LIMIT for s in (0.0, *SHIFTS_MM)), (
        "a genuinely safe push must stay under the limit on all five readings"
    )
    assert HOLE_HALF_WIDTH_MM < min(abs(s) for s in SHIFTS_MM)

    note(axis, right_x - 0.14, base_y + plot_h - 0.26,
         "filled: the reading as the camera gave it\n"
         "hollow: the four readings moved by about\nthe camera's error",
         colour=INK, ha="right", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, base_y - 0.86,
                  "Both candidates look safe on the reading the camera gave. The hole is a push "
                  "the search found precisely because the model is wrong about it in the push's\n"
                  f"favour, and moving the reading by {JITTER_POSITION_MM:.0f} mm on each "
                  f"position and {JITTER_WIDTH_MM:.0f} mm on each width finds it out, so the "
                  "candidate is thrown away.\nThe safe push is not. Drawn, not measured: the "
                  "trained weights are not in this repository, so the two curves are the shape "
                  "of the argument.\nThe limit, the number of extra readings and their sizes "
                  "are the ones plan.py uses.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "worldmodel-pages-the-jitter-check.png", bottom - 0.10)
    save(figure, "worldmodel-pages-the-jitter-check.png")


# --------------------------------------------------------------------------- #
# 3. the five numbers of a push
# --------------------------------------------------------------------------- #


def what_the_push_says() -> None:
    """A parameterised push drawn on the table, with the search's share marked.

    Three of the five numbers are the search's to choose and two are arithmetic
    on a width the camera measured. Which is which is the boundary between what
    this solution learned and what it did not have to, and it is a geometry.
    """
    half = DRAWN_RIM_MM / 2.0
    back_mm = half + STANDOFF_MM
    reach_mm = half + STANDOFF_MM + FEEL_PAST_MM
    offset_mm = OFFSET_SHARE * half

    # jaw_reach() in features.py is widest/2 + STANDOFF + FEEL_PAST, measured
    # forward from jaw_start(), which sits widest/2 + STANDOFF behind the middle.
    # So the feel ends exactly FEEL_PAST past the middle of the glass.
    assert abs((-back_mm + reach_mm) - FEEL_PAST_MM) < 1e-9

    width, height = 9.8, 7.3
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "A push is five numbers: the search chooses three and arithmetic settles two")

    scale = 0.0245                 # inches per millimetre
    patch = Patch(axis, (4.55, 5.30), scale)

    # The jaw's journey is drawn a little above the glass's, so that the feel and
    # the push are two lines rather than one line with two heads on it.
    jaw_y = 13.0
    tip_w, tip_l = 28.0, 16.0      # bench.py JAW_THICKNESS, and a stub of FINGER_LENGTH
    patch.arrow((-back_mm, jaw_y), (FEEL_PAST_MM, jaw_y), colour=MUTED, lw=1.2, head=9.0)
    patch.glass((0.0, 0.0), DRAWN_RIM_MM, colour=GLASS)
    patch.arrow((-half, 0.0), (-half + DRAWN_TRAVEL_MM, 0.0), colour=INK, lw=2.4)
    note(axis, *patch.at(-back_mm - tip_l - 8.0, jaw_y), "the jaw", colour=MUTED,
         ha="right", size=NOTE_SIZE)
    note(axis, *patch.at(-half + DRAWN_TRAVEL_MM / 2.0, -12.0), "the glass", colour=INK,
         ha="center", size=NOTE_SIZE)

    axis.add_patch(
        Polygon([patch.at(-back_mm - tip_l, jaw_y - tip_w / 2.0),
                 patch.at(-back_mm, jaw_y - tip_w / 2.0),
                 patch.at(-back_mm, jaw_y + tip_w / 2.0),
                 patch.at(-back_mm - tip_l, jaw_y + tip_w / 2.0)],
                closed=True, facecolor=_tint(INK, 0.75), edgecolor=INK, lw=1.0, zorder=5)
    )

    # The band the offset may be drawn from, across the back of the glass.
    axis.add_patch(
        Rectangle(patch.at(-back_mm - 3.0, -offset_mm), patch.length(6.0),
                  patch.length(2.0 * offset_mm), facecolor=_tint(GOOD, 0.55),
                  edgecolor=GOOD, lw=1.0, zorder=2)
    )
    axis.add_patch(
        FancyArrowPatch(patch.at(-back_mm, -offset_mm), patch.at(-back_mm, offset_mm),
                        arrowstyle="<|-|>", mutation_scale=9, linewidth=1.1, color=GOOD,
                        shrinkA=0, shrinkB=0, zorder=6)
    )
    note(axis, *patch.at(-back_mm, offset_mm + 12.0),
         f"offset: {offset_mm:.0f} mm either way,\nwhich is {OFFSET_SHARE:.1f} of the half width",
         colour=GOOD, ha="center", size=NOTE_SIZE)

    # The heading, drawn as the choice it is: the same push may come at the
    # glass from any direction at all, and the one drawn is only one of them.
    for degrees in (55.0, 110.0, 180.0, 245.0, 300.0):
        unit = np.array([math.cos(math.radians(degrees)), math.sin(math.radians(degrees))])
        patch.arrow(tuple(-(half + 19.0) * unit), tuple(-(half + 5.0) * unit),
                    colour=_tint(GOOD, 0.45), lw=1.6, head=9.0, zorder=4)
    note(axis, *patch.at(72.0, 42.0), "heading: any way round,\nand this is one of them",
         colour=GOOD, ha="left", size=NOTE_SIZE, weight="bold")

    # The three lengths, stacked under the drawing with their names in a column
    # to the right, so that no measuring line is drawn through a label.
    stations = {v: patch.at(v, 0.0)[0] for v in (-back_mm, -half, FEEL_PAST_MM,
                                                 -half + DRAWN_TRAVEL_MM)}
    first = patch.at(0.0, -half)[1] - 0.42
    names_x = patch.at(0.0, 0.0)[0] + 1.40
    for x in stations.values():
        axis.plot([x, x], [first - 0.80, patch.at(0.0, -half)[1] - 0.10],
                  color=MUTED, lw=0.9, ls=(0, (2, 2)), zorder=2)

    rows = (
        (first, -back_mm, -half, INK,
         f"the standoff: {STANDOFF_MM:.0f} mm behind the widest edge"),
        (first - 0.40, -back_mm, FEEL_PAST_MM, INK,
         f"the feel: forward to {FEEL_PAST_MM:.0f} mm past the middle"),
        (first - 0.80, -half, -half + DRAWN_TRAVEL_MM, GOOD,
         f"the travel: {TRAVEL_MM[0]:.0f} to {TRAVEL_MM[1]:.0f} mm, drawn here at "
         f"{DRAWN_TRAVEL_MM:.0f}"),
    )
    for y, left_mm, right_mm, colour, label in rows:
        axis.add_patch(
            FancyArrowPatch((stations[left_mm], y), (stations[right_mm], y),
                            arrowstyle="|-|", mutation_scale=4, linewidth=1.1,
                            color=colour, shrinkA=0, shrinkB=0, zorder=7)
        )
        note(axis, names_x, y, label, colour=colour, ha="left", size=NOTE_SIZE)

    # The two kinds of number, named under the drawing rather than beside it,
    # so that no label has to be squeezed between a box and the glass.
    column_x, column_w = width / 2.0, 8.6
    bottom_of = box(figure, axis, column_x, first - 1.30, column_w,
                    "The search chooses three: which way the jaw points \u00b7 where across the "
                    "glass it meets it \u00b7 how far it pushes",
                    edge=GOOD, face=_tint(GOOD, 0.90), size=NOTE_SIZE)
    bottom_of = box(figure, axis, column_x, bottom_of - 0.30, column_w,
                    f"Arithmetic settles two: {STANDOFF_MM:.0f} mm behind the widest edge, "
                    "which clears it despite the camera's error \u00b7 forward to\n"
                    f"{FEEL_PAST_MM:.0f} mm past the middle, because a stemmed glass is met at "
                    "its stem and a jaw that misses under the bowl tips it",
                    edge=INK, size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, bottom_of - 0.34,
                  "Neither of the two depends on anything nobody knows, so neither is learned. "
                  "The height is not a number at all: the jaw rides as low as the gripper\n"
                  f"goes, always. Drawn on a glass {DRAWN_RIM_MM:.0f} mm across, which is inside "
                  "the range the cell draws a kind from.",
                  colour=MUTED, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "worldmodel-pages-what-the-push-says.png", bottom - 0.10)
    save(figure, "worldmodel-pages-what-the-push-says.png")


def main() -> None:
    the_pushs_own_frame()
    the_jitter_check()
    what_the_push_says()


if __name__ == "__main__":
    main()
