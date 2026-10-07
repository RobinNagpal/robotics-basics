"""The pictures for the six short pages of the six-solutions chapter.

The chapter already carries one or two flow charts per solution, drawn by
``make_solution_flows_a.py`` and ``make_solution_flows_b.py``, and those say
what each solution does. Nothing is redrawn here. These are the pictures the
short pages were missing: the three cross-cutting shapes the overview argues
about, and one measured result each for four of the six solutions.

    six-where-the-learned-part-sits.png   the ladder from a model that only
                                          prefers to a model that decides, and
                                          where the refusal gate sits on it.
    six-who-learns-from-whom.png          which solutions owe their score to
                                          another solution's.
    six-racked-against-toppled.png        the two columns the book cares most
                                          about, which disagree.
    nudge-the-rule-and-the-planner.png    the one box of solution 1's loop that
                                          the built planner and the designed
                                          rule fill differently.
    ranked-the-label-is-not-the-score.png the quantity solution 2's model is
                                          fitted on is not the quantity the
                                          run is marked on.
    imitation-a-heading-thirty-degrees-out.png  why the measured heading error
                                          lands the jaw's own body on a
                                          neighbour.
    smolvla-the-jaw-hovers.png            how far above the table the borrowed
                                          model's chunks stop.
    smolvla-finetuned-where-the-pushes-went.png  where the same pair's pushes
                                          ended, before and after fine-tuning.

Every number drawn below is read out of ``code/src/09_pushing-the-glasses-apart/``
and the file it came from is named in a comment beside it. The two pictures
that need arithmetic rather than a reading — the candidate comparison and the
heading error — do that arithmetic here, from the cell's own constants, and
print it, so that what is drawn can be checked against what the run reports.

The drawing helpers, and the audit that measures the finished picture for
overlapping text and lines through boxes, are imported from
``make_solution_flows_a.py`` so that these pictures sit beside those.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_six_solutions_pages.py
"""

from __future__ import annotations

import math

import numpy as np
from diagram_style import (
    GLASS,
    GOOD,
    GRIP_ROOM,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    WARN,
    save,
)
from make_solution_flows_a import (
    GAP,
    _tint,
    arrow,
    band,
    box,
    finish,
    note,
    run,
    sheet,
    title,
)
from matplotlib.patches import Circle, Polygon, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Each solution's own results.json, under
# code/src/09_pushing-the-glasses-apart/. For the three solutions the examiner
# requires several runs of, the figure is the "spread" block's median.

HELD_OUT_TABLES = 50
GLASSES = 251

# name, glasses racked, glasses toppled
RESULTS = [
    ("1 one fixed nudge", 195, 0),
    ("2 geometry ranked", 185, 0),
    ("3 imitation, ACT", 68, 1),
    ("4 a world model", 202, 1),
    ("5 SmolVLA as it downloads", 56, 6),
    ("6 SmolVLA fine-tuned", 77, 46),
]

# 01-one-fixed-nudge/plan.py: the enumerator solutions 1 and 2 share.
HEADINGS = 72              # HEADINGS
STEP_MM = 2                # STEP = 0.002
LONGEST_PUSH_MM = 150      # LONGEST_PUSH = 0.15
LEAST_EASING_MM = 10       # LEAST_EASING = 0.010
APPROACH_GAP_MM = 10       # APPROACH_GAP = 0.010
CLEARANCE_MM = 8           # CLEARANCE = 0.008

# bench/bench.py, the jaw as arm/gripper.urdf.xacro declares it.
TOOL_LENGTH_MM = 270       # TOOL_LENGTH = FINGER_LENGTH + BODY_LENGTH + WRIST_LENGTH
BODY_SIZE_MM = 90          # BODY_SIZE
PUSH_HEIGHT_MM = 50        # PUSH_HEIGHT = LOWEST_GRIP
JAW_TOP_MM = 65            # JAW_TOP = PUSH_HEIGHT + FINGER_HEIGHT / 2
TRAVEL_HEIGHT_MM = 300     # TRAVEL_HEIGHT = 0.30

# glasses/shapes.py KIND_RANGES, by way of diagram_style: the declared range of
# heights a glass on these tables may be drawn with.
GLASS_SHORTEST_MM = 90
GLASS_TALLEST_MM = 230

# 05-smolvla-as-it-downloads/asking.json and 06-smolvla-fine-tuned/asking.json,
# each over all three evaluation runs of its solution.
DOWNLOADED_ASKED = 2260
DOWNLOADED_LOWEST_MM = 209.1
FINETUNED_LOWEST_MM = 50.0

# The push outcomes of one run each rather than the median of three, because
# the parts of one run add up to that run's total and medians taken column by
# column do not. The run chosen is the one whose push count is the median.
# 05-smolvla-as-it-downloads/results.json, "each"[2].
DOWNLOADED_PUSHES = 754
DOWNLOADED_BLOCKED = 0
DOWNLOADED_NEVER_TOUCHED = 674
# 06-smolvla-fine-tuned/results.json, "each"[0].
FINETUNED_PUSHES = 400
FINETUNED_BLOCKED = 247
FINETUNED_NEVER_TOUCHED = 39

# 03-imitation-from-demonstrations/README.md, "Why it scores that way".
HEADING_ERROR_DEG = 30


# --------------------------------------------------------------------------- #
# 1. the overview: where the learned part sits
# --------------------------------------------------------------------------- #


def where_the_learned_part_sits() -> None:
    """The ladder from a model that only prefers to a model that decides.

    One idea: how much of the pushing the fitted part owns decides what a
    wrong answer costs, and in five of the six the refusal that matters most
    is settled by arithmetic before the model is asked anything at all.
    """
    width, height = 12.4, 6.8
    figure, axis = sheet(width, height)
    rung_x, rung_w = 4.75, 6.0
    cost_x, cost_w = 10.1, 3.6

    y = title(figure, axis, width, height - 0.12,
              "The six, by how much of the pushing the fitted part owns") - 0.28
    note(axis, rung_x, y, "what is fitted", colour=INK, size=LABEL_SIZE,
         ha="center", weight="bold", figure=figure)
    y = note(axis, cost_x, y, "what a wrong answer costs", colour=INK,
             size=LABEL_SIZE, ha="center", weight="bold", figure=figure) - 0.18

    rungs = [
        ("1 one fixed nudge", "Nothing. Every number in it was written down.",
         "Nothing is fitted, so nothing\ncan be wrongly fitted.", MUTED),
        ("2 geometry generates, a model ranks",
         "A preference over candidates the geometry already passed.",
         "One wasted push. The model\ncannot add a candidate.", GOOD),
        ("3 imitation from demonstrations",
         "The push itself, copied from a teacher.",
         "The push is carried out\non the real table.", WARN),
        ("4 a world model, then plan with it",
         "What a push will do, which a search then uses.",
         "The push is carried out, and\nthe refusal rests on it too.", WARN),
        ("5 a foundation model as it downloads",
         "Nothing here. All of it somewhere else.",
         "The push is carried out\non the real table.", WARN),
        ("6 the same model, fine-tuned here",
         "All of it, from a borrowed start.",
         "The push is carried out\non the real table.", WARN),
    ]

    levels = []
    for name, fitted, cost, colour in rungs:
        top_of_row = y
        bottom = box(figure, axis, rung_x, top_of_row, rung_w,
                     f"{name}\n{fitted}", edge=colour,
                     face=PAPER if colour is MUTED else _tint(colour, 0.90))
        box(figure, axis, cost_x, top_of_row, cost_w, cost,
            edge=MUTED, face=PAPER, size=NOTE_SIZE - 0.4)
        levels.append((top_of_row + bottom) / 2.0)
        y = bottom - 0.24

    # The band's label is drawn rotated, so it reads from the bottom of the
    # chart upwards: the end of the string lands at the top of the band.
    band_left = 0.55
    band(axis, band_left, y + 0.24, rung_w + 1.4, levels[0] - (y + 0.24) + 0.44,
         MUTED, "the model decides                    the model only prefers")

    bottom = note(
        axis, band_left, y - 0.04,
        "In solutions 1, 2, 3, 5 and 6 the rule that refuses a glass which tips before it slides is arithmetic applied before any\n"
        "model is asked, so no model can cause the one failure this cell cannot take back. Solution 4 holds no friction value to\n"
        "put in that rule and refuses on its own model's evidence instead, which is why its row carries a second cost.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "six-where-the-learned-part-sits.png", bottom - 0.10)
    save(figure, "six-where-the-learned-part-sits.png")


# --------------------------------------------------------------------------- #
# 2. the overview: who learns from whom
# --------------------------------------------------------------------------- #


def who_learns_from_whom() -> None:
    """Which of the six have a score that depends on another solution's.

    One idea: solutions 3 and 6 are fitted on solution 2's recorded pushes, so
    their ceiling is its quality, and no other pair in the set is tied that
    way.
    """
    width, height = 11.8, 3.65
    figure, axis = sheet(width, height)
    teacher_x, teacher_w = 3.3, 5.0
    student_x, student_w = 9.0, 4.6

    y = title(figure, axis, width, height - 0.12,
              "Where each solution's training examples come from") - 0.30

    teacher_top = y
    teacher_bottom = box(
        figure, axis, teacher_x, teacher_top, teacher_w,
        "2 geometry generates, a model ranks\n"
        "Every push it makes is recorded with a picture of the table and the\n"
        f"waypoints the jaw followed. It racked {RESULTS[1][1]} of the {GLASSES} glasses itself.",
        edge=GLASS, face=_tint(GLASS, 0.88), lw=1.6,
    )
    teacher_mid = (teacher_top + teacher_bottom) / 2.0

    y = teacher_bottom - 0.40
    others_bottom = box(
        figure, axis, teacher_x, y, teacher_w,
        "1 one fixed nudge — nothing is fitted, so there is nothing to learn from.\n"
        "4 a world model — makes its own pushes, random ones first and then its\n"
        "own planner's, and nobody labels any of them.\n"
        "5 a foundation model as it downloads — fitted somewhere else entirely.",
        edge=MUTED, face=PAPER,
    )

    students = []
    y = teacher_top
    for name, racked in (
        ("3 imitation from demonstrations", RESULTS[2][1]),
        ("6 the same model, fine-tuned here", RESULTS[5][1]),
    ):
        top_of_box = y
        y = box(figure, axis, student_x, top_of_box, student_w,
                f"{name}\nfitted to copy those pushes, and racked {racked}.",
                edge=WARN, face=_tint(WARN, 0.92))
        students.append((top_of_box + y) / 2.0)
        y -= 0.38

    corridor = teacher_x + teacher_w / 2.0 + 0.55
    run(axis, (teacher_x + teacher_w / 2.0, teacher_mid), (corridor, teacher_mid))
    run(axis, (corridor, students[0]), (corridor, students[-1]))
    for level in students:
        arrow(axis, (corridor, level), (student_x - student_w / 2.0, level), colour=WARN)

    bottom = note(
        axis, 0.55, min(others_bottom, y) - 0.22,
        "So two of the six have a score that depends on another solution's. Whatever solution 2 cannot do, neither of them can\n"
        "learn to do, because nothing in copying a teacher ever compares one outcome against another. The recordings are also\n"
        "filtered to the pushes that worked, which thins them exactly in the arrangements solution 2 found hard.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "six-who-learns-from-whom.png", bottom - 0.10)
    save(figure, "six-who-learns-from-whom.png")


# --------------------------------------------------------------------------- #
# 3. the overview: the two columns that matter, against each other
# --------------------------------------------------------------------------- #


def racked_against_toppled() -> None:
    """Glasses racked against glasses toppled, one point per solution.

    One idea: the column that says a solution did the job and the column that
    says it broke something do not order the six the same way.
    """
    width, height = 10.6, 5.9
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              f"What the six did to the same {HELD_OUT_TABLES} tables: the job done, against the damage done") - 0.34

    left, right = 1.60, 9.9
    floor, ceiling = 1.42, y - 0.30
    racked_max, toppled_max = 220.0, 50.0

    def place(racked: float, toppled: float) -> tuple[float, float]:
        return (left + (right - left) * racked / racked_max,
                floor + (ceiling - floor) * toppled / toppled_max)

    axis.add_patch(Rectangle((left, floor), right - left, ceiling - floor,
                             facecolor=_tint(MUTED, 0.95), edgecolor="none", zorder=0))
    axis.plot([left, right], [floor, floor], color=INK, lw=1.1, zorder=2)
    axis.plot([left, left], [floor, ceiling], color=INK, lw=1.1, zorder=2)

    for racked in (0, 50, 100, 150, 200):
        x = place(racked, 0)[0]
        axis.plot([x, x], [floor, floor - 0.08], color=INK, lw=1.0, zorder=2)
        note(axis, x, floor - 0.19, str(racked), colour=MUTED,
             size=NOTE_SIZE - 0.6, ha="center", figure=figure)
    for toppled in (0, 10, 20, 30, 40, 50):
        yy = place(0, toppled)[1]
        axis.plot([left, left - 0.08], [yy, yy], color=INK, lw=1.0, zorder=2)
        note(axis, left - 0.14, yy, str(toppled), colour=MUTED,
             size=NOTE_SIZE - 0.6, ha="right", figure=figure)

    note(axis, (left + right) / 2.0, floor - 0.44,
         f"glasses racked, out of {GLASSES}", colour=INK, size=LABEL_SIZE,
         ha="center", figure=figure)
    axis.text(left - 0.52, (floor + ceiling) / 2.0, "glasses toppled",
              rotation=90, ha="center", va="center", fontsize=LABEL_SIZE, color=INK,
              zorder=5)

    # Where each label sits relative to its point, with a leader line back to
    # the marker, because three of the six land within a few glasses of each
    # other in the bottom right corner.
    offsets = {
        "1 one fixed nudge": (-0.22, 0.58, "right"),
        "2 geometry ranked": (-0.22, 0.20, "right"),
        "3 imitation, ACT": (0.22, 0.20, "left"),
        "4 a world model": (-0.22, 0.98, "right"),
        "5 SmolVLA as it downloads": (-0.22, 0.04, "right"),
        "6 SmolVLA fine-tuned": (0.22, 0.00, "left"),
    }
    for name, racked, toppled in RESULTS:
        x, yy = place(racked, toppled)
        dx, dy, ha = offsets[name]
        axis.plot([x, x + dx], [yy, yy + dy], color=MUTED, lw=0.9, zorder=4)
        colour = GOOD if toppled == 0 else (WARN if toppled > 5 else GLASS)
        axis.add_patch(Circle((x, yy), 0.085, facecolor=colour, edgecolor=INK,
                              lw=1.0, zorder=6))
        note(axis, x + dx, yy + dy, name, colour=INK, size=NOTE_SIZE - 0.3,
             ha=ha, figure=figure)

    note(axis, right - 0.12, ceiling - 0.14,
         "further right is more of the job done\nhigher up is more of it broken",
         colour=MUTED, size=NOTE_SIZE - 0.4, ha="right", figure=figure)

    bottom = note(
        axis, 0.55, floor - 0.76,
        "A toppled glass cannot be stood back up, so the two axes are not worth the same. The three solutions that let written\n"
        "geometry choose the push sit together in the bottom right; the three that produce the push themselves come nowhere near\n"
        "them. The only trade worth arguing about is between solutions 1 and 4: seven more glasses racked, for one glass broken.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "six-racked-against-toppled.png", bottom - 0.10)
    save(figure, "six-racked-against-toppled.png")


# --------------------------------------------------------------------------- #
# 4. solution 1: the one box the built planner and the designed rule differ in
# --------------------------------------------------------------------------- #


def the_rule_and_the_planner() -> None:
    """Solution 1's loop, with the one step that was run and the one designed.

    One idea: everything round the choosing step exists in the repository and
    produced the row on this page; the choosing step itself is where the
    document's rule would go, and what ran there was a search.
    """
    width, height = 12.3, 6.1
    figure, axis = sheet(width, height)
    chain_x, chain_w = 3.5, 5.1
    alt_x, alt_w = 9.3, 5.3

    y = title(figure, axis, width, height - 0.12,
              "One pass of solution 1's loop, and the one step the two versions fill differently") - 0.30

    top_of_chain = y
    for text in (
        "look(): the camera measures every glass — where it stands, how tall it is,\n"
        "how wide at its widest and how wide the foot it stands on is.",
        "Take every glass that already has clear room, and look again.",
        f"Refuse every glass that tips before it slides. The jaw's top edge rides {JAW_TOP_MM} mm\n"
        "above the table, and the friction is never measured.",
    ):
        y = box(figure, axis, chain_x, y, chain_w, text)
        arrow(axis, (chain_x, y), (chain_x, y - GAP))
        y -= GAP

    slot_top = y
    y = box(figure, axis, chain_x, y, chain_w,
            "Choose one push: a heading and a travel.",
            edge=WARN, face=_tint(WARN, 0.88), lw=2.0, weight="bold", size=LABEL_SIZE)
    slot_mid = (slot_top + y) / 2.0

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "Hand it over as three numbers, make the push, and look again.",
            edge=GLASS, face=_tint(GLASS, 0.88))
    chain_bottom = y

    band(axis, 0.55, chain_bottom - 0.26, chain_w + 1.1,
         top_of_chain + 0.26 - (chain_bottom - 0.26), MUTED,
         "built, and run against the examiner")

    y = note(axis, alt_x, top_of_chain, "The two ways that one step is filled",
             colour=INK, size=LABEL_SIZE, ha="center", weight="bold", figure=figure) - 0.26

    first_top = y
    y = box(
        figure, axis, alt_x, y, alt_w,
        "What ran, and produced the row in section 4\n"
        f"Sweep all {HEADINGS} headings and step the travel out in {STEP_MM} mm stages to {LONGEST_PUSH_MM} mm.\n"
        "Drop every candidate the arm cannot reach, that leaves the glass zone,\n"
        "that brings the glass nearer a neighbour, or whose jaw or body would\n"
        "foul one. Take the shortest survivor that leaves a glass with room;\n"
        f"failing that, the one that eases the table most, by at least {LEAST_EASING_MM} mm.",
        edge=GOOD, face=_tint(GOOD, 0.90), lw=1.6,
    )
    first_mid = (first_top + y) / 2.0

    y -= 0.40
    second_top = y
    y = box(
        figure, axis, alt_x, y, alt_w,
        "What this page describes, which is a design\n"
        "Take the glass with the worst shortfall of room and the neighbour\n"
        "responsible for it. Point straight away from that neighbour, and\n"
        "travel a fixed fraction of the shortfall. One multiplication, no search.",
        edge=MUTED, face=PAPER,
    )
    second_mid = (second_top + y) / 2.0

    corridor = chain_x + chain_w / 2.0 + 0.50
    run(axis, (chain_x + chain_w / 2.0, slot_mid), (corridor, slot_mid))
    run(axis, (corridor, first_mid), (corridor, second_mid))
    arrow(axis, (corridor, first_mid), (alt_x - alt_w / 2.0, first_mid), colour=GOOD)
    arrow(axis, (corridor, second_mid), (alt_x - alt_w / 2.0, second_mid), colour=MUTED)

    bottom = note(
        axis, 0.55, min(chain_bottom, y) - 0.46,
        "That search is also what solution 2 generates its candidates with, so solutions 1 and 2 differ in who picks from the same\n"
        "list and in nothing else. The rule in the lower box would replace the search with one heading and one multiplication. It\n"
        "is written out in full in the chapter, and it has not been run.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "nudge-the-rule-and-the-planner.png", bottom - 0.10)
    save(figure, "nudge-the-rule-and-the-planner.png")


# --------------------------------------------------------------------------- #
# 5. solution 2: the label and the score are not the same quantity
# --------------------------------------------------------------------------- #


def _shortfall(layout) -> float:
    """How much room a table is short of, summed over its glasses, millimetres.

    The same arithmetic as ``shortfall()`` in
    code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py, which is
    the quantity solution 2's model is fitted to predict the change in.
    ``layout`` is (x, y, widest width) per glass.
    """
    total = 0.0
    for i, (x, y, _) in enumerate(layout):
        worst = max(
            (GRIP_ROOM + w / 2.0 - math.dist((x, y), (ox, oy))
             for j, (ox, oy, w) in enumerate(layout) if j != i),
            default=0.0,
        )
        total += max(0.0, worst)
    return total


def _has_room(index, layout) -> bool:
    """Whether one glass of a layout could be gripped, by the examiner's own test."""
    x, y, _ = layout[index]
    return all(math.dist((x, y), (ox, oy)) >= GRIP_ROOM + w / 2.0
               for j, (ox, oy, w) in enumerate(layout) if j != index)


def the_label_is_not_the_score() -> None:
    """One table, two legal candidate pushes, and the two numbers they earn.

    One idea: the quantity the model is fitted on, room gained over the whole
    table, and the quantity the run is marked on, glasses that end up
    grippable, pick different candidates out of the same list.
    """
    width, height = 11.6, 6.4
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "Two legal pushes on one table, scored by the two different quantities") - 0.34

    # The table, in millimetres, drawn into a panel measured in inches. Three
    # glasses in a tight line, and a crowded pair, all of one kind.
    rim = 90.0
    panel_x, panel_w = 0.90, 6.2
    span_mm, depth_mm = 580.0, 430.0
    scale = panel_w / span_mm
    panel_h = depth_mm * scale
    panel_y = y - panel_h - 0.06

    def at(mx: float, my: float) -> tuple[float, float]:
        return panel_x + (mx + 20.0) * scale, panel_y + (my - 55.0) * scale

    start = [(120.0, 220.0, rim), (120.0, 380.0, rim), (120.0, 300.0, rim),
             (430.0, 120.0, rim), (330.0, 120.0, rim)]
    pushed_a, to_a = 3, (470.0, 120.0, rim)      # the pair's outer glass, 40 mm right
    pushed_b, to_b = 2, (60.0, 300.0, rim)       # the line's middle glass, 60 mm left

    after_a = [to_a if i == pushed_a else g for i, g in enumerate(start)]
    after_b = [to_b if i == pushed_b else g for i, g in enumerate(start)]
    before = _shortfall(start)
    gain_a = before - _shortfall(after_a)
    gain_b = before - _shortfall(after_b)
    free_a = sum(_has_room(i, after_a) for i in range(len(start)))
    free_b = sum(_has_room(i, after_b) for i in range(len(start)))
    print(f"  the-label-is-not-the-score: the table is short of {before:.0f} mm of room and no "
          f"glass can be gripped; push a gains {gain_a:.0f} mm and leaves {free_a} grippable, "
          f"push b gains {gain_b:.0f} mm and leaves {free_b}")
    assert gain_b > gain_a and free_a > free_b, "the two scores must disagree"

    axis.add_patch(Rectangle((panel_x, panel_y), panel_w, panel_h,
                             facecolor=_tint(MUTED, 0.95), edgecolor=MUTED,
                             lw=1.0, zorder=0))

    for index, (mx, my, w) in enumerate(start):
        cx, cy = at(mx, my)
        axis.add_patch(Circle((cx, cy), GRIP_ROOM * scale, facecolor="none",
                              edgecolor=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2))
        moved = index in (pushed_a, pushed_b)
        axis.add_patch(Circle((cx, cy), w / 2.0 * scale,
                              facecolor=_tint(GLASS if moved else MUTED, 0.45),
                              edgecolor=GLASS if moved else MUTED, lw=1.3, zorder=3))

    for index, to, colour, label in ((pushed_a, to_a, GOOD, "a"), (pushed_b, to_b, WARN, "b")):
        sx, sy = at(*start[index][:2])
        ex, ey = at(*to[:2])
        axis.add_patch(Circle((ex, ey), GRIP_ROOM * scale, facecolor="none",
                              edgecolor=colour, lw=1.1, ls=(0, (4, 3)), zorder=4))
        axis.add_patch(Circle((ex, ey), rim / 2.0 * scale, facecolor="none",
                              edgecolor=colour, lw=1.5, zorder=4))
        axis.annotate("", xy=(ex, ey), xytext=(sx, sy), zorder=6,
                      arrowprops=dict(arrowstyle="-|>", color=colour, lw=2.2))
        note(axis, ex, ey + GRIP_ROOM * scale + 0.16, label, colour=colour,
             size=LABEL_SIZE + 1.0, ha="center", weight="bold", figure=figure)

    note(axis, *at(250.0, 420.0),
         "solid circle: a glass.\n"
         "dashed ring: the clear room the open jaw needs round it.\n"
         "another glass reaching inside that ring is what makes\n"
         "the first one impossible to pick up.\n"
         "coloured outline: where a pushed glass would come to rest.",
         colour=MUTED, size=NOTE_SIZE - 0.6, figure=figure)

    cell_x, cell_w = 9.3, 4.0
    y = panel_y + panel_h - 0.20
    y = box(figure, axis, cell_x, y, cell_w,
            f"Push a moves one glass of the crowded pair "
            f"{to_a[0] - start[pushed_a][0]:.0f} mm\nfurther from the other.\n"
            f"room gained over the table: {gain_a:.0f} mm\n"
            f"glasses that can now be picked up: {free_a}",
            edge=GOOD, face=_tint(GOOD, 0.90), lw=1.6)
    y = box(figure, axis, cell_x, y - 0.46, cell_w,
            f"Push b moves the middle glass of the line "
            f"{start[pushed_b][0] - to_b[0]:.0f} mm\naway from both its neighbours.\n"
            f"room gained over the table: {gain_b:.0f} mm\n"
            f"glasses that can now be picked up: {free_b}",
            edge=WARN, face=_tint(WARN, 0.90), lw=1.6)
    y = box(figure, axis, cell_x, y - 0.46, cell_w,
            "The model is fitted on the first of those\ntwo lines. The run is marked on the second.",
            edge=INK, face=PAPER, weight="bold")

    bottom = note(
        axis, 0.55, min(panel_y, y) - 0.28,
        "So push b is the better candidate by the label the model was fitted on, and the worse one on the scorecard. No amount of\n"
        "fitting makes a model prefer a quantity it was never shown. Every figure above is this picture's own arithmetic over the\n"
        "examiner's room test and the planner's own shortfall, and the script that drew it prints them.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "ranked-the-label-is-not-the-score.png", bottom - 0.10)
    save(figure, "ranked-the-label-is-not-the-score.png")


# --------------------------------------------------------------------------- #
# 6. solution 3: what a heading thirty degrees out does
# --------------------------------------------------------------------------- #


def a_heading_thirty_degrees_out() -> None:
    """The teacher's heading and the fitted policy's, with the jaw drawn on both.

    One idea: what has to be clear is not the line the glass travels along but
    the long body standing behind it, so a heading a little out of true swings
    that body onto a neighbour even when the glass's own path is empty.
    """
    width, height = 11.2, 7.9
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "Why a heading thirty degrees out is a push that never reaches the glass") - 0.34

    rim = 90.0
    panel_x, panel_w = 0.80, 7.2
    span_mm, depth_mm = 720.0, 560.0
    scale = panel_w / span_mm
    panel_h = depth_mm * scale
    panel_y = y - panel_h - 0.06
    glass_mm = (340.0, 330.0)
    neighbour_mm = (340.0, 225.0)                # 105 mm below, so neither has room

    def at(mx: float, my: float) -> tuple[float, float]:
        return panel_x + mx * scale, panel_y + my * scale

    # How far the jaw's centre line has to stay from a neighbour's middle, and
    # therefore how far out of true a heading may be before it does not.
    clear_mm = BODY_SIZE_MM / 2.0 + rim / 2.0 + CLEARANCE_MM
    apart_mm = math.dist(glass_mm, neighbour_mm)
    least_deg = math.degrees(math.asin(min(1.0, clear_mm / apart_mm)))
    teacher_deg = 90.0 + least_deg + 6.0
    policy_deg = teacher_deg - HEADING_ERROR_DEG
    print(f"  a-heading-thirty-degrees-out: a neighbour {apart_mm:.0f} mm away needs the jaw's "
          f"line {clear_mm:.0f} mm clear of it, so a heading has to be at least {least_deg:.0f} "
          f"degrees off the line towards it; the teacher's is {teacher_deg:.0f} degrees and the "
          f"policy's {policy_deg:.0f}")
    assert policy_deg - 90.0 < least_deg < teacher_deg - 90.0

    axis.add_patch(Rectangle((panel_x, panel_y), panel_w, panel_h,
                             facecolor=_tint(MUTED, 0.95), edgecolor=MUTED, lw=1.0, zorder=0))

    for centre, colour in ((neighbour_mm, MUTED), (glass_mm, GLASS)):
        cx, cy = at(*centre)
        axis.add_patch(Circle((cx, cy), GRIP_ROOM * scale, facecolor="none",
                              edgecolor=colour, lw=1.0, ls=(0, (4, 3)), zorder=2))
        axis.add_patch(Circle((cx, cy), rim / 2.0 * scale, facecolor=_tint(colour, 0.45),
                              edgecolor=colour, lw=1.4, zorder=6))

    def jaw(heading_deg: float, colour: str, filled: bool) -> None:
        """The jaw placed to push along ``heading_deg``: fingertips just outside
        the glass, and the tool and body reaching back behind them."""
        u = np.array([math.cos(math.radians(heading_deg)), math.sin(math.radians(heading_deg))])
        across = np.array([-u[1], u[0]])
        tip = np.array(glass_mm) - (rim / 2.0 + APPROACH_GAP_MM) * u
        back = tip - TOOL_LENGTH_MM * u
        half = BODY_SIZE_MM / 2.0
        corners = [tip + half * across, tip - half * across,
                   back - half * across, back + half * across]
        axis.add_patch(Polygon([at(*c) for c in corners], closed=True,
                               facecolor=_tint(colour, 0.60) if filled else "none",
                               edgecolor=colour, lw=1.6,
                               ls="solid" if filled else (0, (4, 3)), zorder=4))
        axis.annotate("", xy=at(*(np.array(glass_mm) + 150.0 * u)),
                      xytext=at(*(np.array(glass_mm) + (rim / 2.0) * u)), zorder=7,
                      arrowprops=dict(arrowstyle="-|>", color=colour, lw=2.2))

    jaw(teacher_deg, GOOD, False)
    jaw(policy_deg, WARN, True)

    note(axis, *at(10.0, 548.0),
         "the teacher's heading, which leans far enough over\nthat the jaw's body misses the neighbour",
         colour=GOOD, size=NOTE_SIZE - 0.2, figure=figure)
    note(axis, *at(10.0, 126.0),
         f"the fitted policy's heading, {HEADING_ERROR_DEG} degrees off it, with\nthe jaw's body over the neighbour",
         colour=WARN, size=NOTE_SIZE - 0.2, figure=figure)
    note(axis, *at(340.0, 146.0), "the neighbour crowding the glass",
         colour=INK, size=NOTE_SIZE - 0.2, ha="center", figure=figure)

    bottom = box(
        figure, axis, width / 2.0, panel_y - 0.26, 10.2,
        f"The jaw is {TOOL_LENGTH_MM} mm long behind its fingertips and {BODY_SIZE_MM} mm across, so what has to be clear of a neighbour is that whole\n"
        f"rectangle, not the short path the glass travels. A neighbour {apart_mm:.0f} mm away leaves only the headings more than about {least_deg:.0f}\n"
        f"degrees off the line towards it, and a {HEADING_ERROR_DEG}-degree error is wider than that window.",
        edge=INK, face=PAPER,
    )

    finish(figure, axis, "imitation-a-heading-thirty-degrees-out.png", bottom - 0.10)
    save(figure, "imitation-a-heading-thirty-degrees-out.png")


# --------------------------------------------------------------------------- #
# 7. solution 5: how far above the table the chunks stop
# --------------------------------------------------------------------------- #


def the_jaw_hovers() -> None:
    """The height the borrowed model's chunks come down to, against the table.

    One idea: the solution is not choosing bad pushes, it is not reaching the
    table at all, and one measured height says so.
    """
    width, height = 11.0, 6.6
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "How low the downloaded model brings the jaw, against how low a push has to be") - 0.38

    floor, ceiling = 1.30, y - 0.22
    scale = (ceiling - floor) / TRAVEL_HEIGHT_MM
    axis_x, rule_end, text_x = 1.95, 3.55, 3.70

    def level(mm: float) -> float:
        return floor + mm * scale

    axis.add_patch(Rectangle((axis_x - 0.45, floor - 0.17), 2.6, 0.17,
                             facecolor=_tint(MUTED, 0.55), edgecolor=MUTED, lw=1.0, zorder=2))
    axis.add_patch(Rectangle((axis_x + 0.26, level(GLASS_SHORTEST_MM)), 1.22,
                             level(GLASS_TALLEST_MM) - level(GLASS_SHORTEST_MM),
                             facecolor=_tint(GLASS, 0.82), edgecolor=GLASS, lw=1.0,
                             ls=(0, (4, 3)), zorder=3))
    note(axis, axis_x + 0.87, level(150.0) + 0.24,
         f"every glass on\nthese tables stands\n{GLASS_SHORTEST_MM} to {GLASS_TALLEST_MM} mm tall",
         colour=GLASS, size=NOTE_SIZE - 1.0, ha="center", figure=figure)

    axis.plot([axis_x, axis_x], [floor, ceiling], color=INK, lw=1.2, zorder=4)
    for mm in (50, 100, 150, 200, 250, 300):
        yy = level(mm)
        axis.plot([axis_x - 0.09, axis_x], [yy, yy], color=INK, lw=1.0, zorder=4)
        note(axis, axis_x - 0.15, yy, f"{mm}", colour=MUTED, size=NOTE_SIZE - 0.6,
             ha="right", figure=figure)
    axis.text(axis_x - 0.62, (floor + ceiling) / 2.0, "millimetres above the table",
              rotation=90, ha="center", va="center", fontsize=LABEL_SIZE, color=INK, zorder=5)

    marks = [
        (TRAVEL_HEIGHT_MM, MUTED, True,
         "the highest a waypoint may ask for: the height the jaw travels at"),
        (DOWNLOADED_LOWEST_MM, WARN, False,
         f"the lowest point of a chunk the downloaded model returns,\nthe median over {DOWNLOADED_ASKED:,} asks"),
        (JAW_TOP_MM, INK, False,
         "the top edge of the jaw, where a glass wider higher up meets it"),
        (PUSH_HEIGHT_MM, GOOD, False,
         "where the jaw has to ride to move anything: as low as it goes"),
    ]
    for mm, colour, dashed, text in marks:
        yy = level(mm)
        axis.plot([axis_x, rule_end], [yy, yy], color=colour, lw=2.0,
                  ls=(0, (5, 4)) if dashed else "solid", zorder=5)
        note(axis, text_x, yy, f"{mm:g} mm — {text}", colour=colour,
             size=NOTE_SIZE - 0.2, figure=figure)

    bottom = note(
        axis, 0.55, floor - 0.38,
        f"So the chunks stop about {DOWNLOADED_LOWEST_MM - PUSH_HEIGHT_MM:.0f} mm above the one height at which the jaw can move a glass, and above the rims of all\n"
        "but the tallest kinds. The consequence is in the run: about nine of its pushes in ten touched nothing whatever. It is not\n"
        "choosing badly among pushes. It is mostly not arriving at the table.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "smolvla-the-jaw-hovers.png", bottom - 0.10)
    save(figure, "smolvla-the-jaw-hovers.png")


# --------------------------------------------------------------------------- #
# 8. solutions 5 and 6: where the pushes of the pair ended
# --------------------------------------------------------------------------- #


def where_the_pushes_went() -> None:
    """The same measurement for both halves of the pair, before and after.

    One idea: the training did not turn missed pushes into good pushes, it
    turned them into pushes that reach the table and are stopped on the way
    down.
    """
    width, height = 11.4, 5.3
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "Where the pushes went, before and after this model's training") - 0.40

    left, right = 2.5, 10.1
    scale = (right - left) / max(DOWNLOADED_PUSHES, FINETUNED_PUSHES)
    bar_h = 0.58

    parts = (
        ("never touched anything", WARN),
        ("blocked coming down", GLASS),
        ("touched a glass", GOOD),
    )
    rows = (
        ("5 as it downloads", DOWNLOADED_PUSHES, DOWNLOADED_NEVER_TOUCHED,
         DOWNLOADED_BLOCKED, DOWNLOADED_LOWEST_MM),
        ("6 fine-tuned here", FINETUNED_PUSHES, FINETUNED_NEVER_TOUCHED,
         FINETUNED_BLOCKED, FINETUNED_LOWEST_MM),
    )

    for name, total, never, blocked, lowest in rows:
        note(axis, left - 0.14, y - bar_h / 2.0, name, colour=INK, size=LABEL_SIZE,
             ha="right", weight="bold", figure=figure)
        x = left
        for count, (_label, colour) in zip((never, blocked, total - never - blocked), parts):
            if count == 0:
                continue
            axis.add_patch(Rectangle((x, y - bar_h), count * scale, bar_h,
                                     facecolor=_tint(colour, 0.40), edgecolor=colour,
                                     lw=1.2, zorder=3))
            note(axis, x + count * scale / 2.0, y - bar_h / 2.0, str(count),
                 colour=INK, size=NOTE_SIZE, ha="center", figure=figure)
            x += count * scale
        note(axis, left, y - bar_h - 0.13,
             f"{total} pushes in all; the lowest point of a chunk is a median of {lowest:g} mm above the table",
             colour=MUTED, size=NOTE_SIZE - 0.4, figure=figure)
        y -= bar_h + 0.62

    key_y = y - 0.02
    x = left
    for label, colour in parts:
        axis.add_patch(Rectangle((x, key_y - 0.16), 0.28, 0.16,
                                 facecolor=_tint(colour, 0.40), edgecolor=colour,
                                 lw=1.2, zorder=3))
        note(axis, x + 0.38, key_y - 0.08, label, colour=INK, size=NOTE_SIZE - 0.2,
             figure=figure)
        x += 2.5
    y = key_y - 0.46

    bottom = box(
        figure, axis, width / 2.0, y, 10.4,
        f"The training taught it the height a push happens at: its chunks now come down to exactly the {PUSH_HEIGHT_MM} mm the jaw pushes from,\n"
        f"where before they stopped {DOWNLOADED_LOWEST_MM:.0f} mm up, clear of every glass but the tallest. It did not teach it where to put the jaw down,\n"
        "so most of those pushes are now stopped by a neighbour while still descending, and the glasses that go over are the price.",
        edge=INK, face=PAPER,
    )

    note(axis, left - 0.14, bottom - 0.22,
         "One evaluation run of the three for each, chosen as the run whose push count is the middle of its three, so that the parts add up to the total.",
         colour=MUTED, size=NOTE_SIZE - 0.6, ha="left", figure=figure)

    finish(figure, axis, "smolvla-finetuned-where-the-pushes-went.png", bottom - 0.46)
    save(figure, "smolvla-finetuned-where-the-pushes-went.png")


def main() -> None:
    where_the_learned_part_sits()
    who_learns_from_whom()
    racked_against_toppled()
    the_rule_and_the_planner()
    the_label_is_not_the_score()
    a_heading_thirty_degrees_out()
    the_jaw_hovers()
    where_the_pushes_went()


if __name__ == "__main__":
    main()
