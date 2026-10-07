"""The flow charts for the first three solutions: what each one actually does.

Each solution in this book opens with a document called "what it is", and a
reader should be able to look at the charts there and say what the solution
does, end to end, without reading the prose. The same charts appear again in
the short page about that solution in the six-solutions chapter, so each one
has to stand on its own.

    nudge-flow-what-it-does.png         solution 1 as the loop it is, with the
                                        three ways the loop ends.
    nudge-flow-why-prediction-fails.png why aiming at where the glass will stop
                                        needs a number nothing here measures
    nudge-flow-repeat-not-predict.png   the loop that predicts nothing and
                                        looks again instead, which is
                                        solution 1's whole idea.
    ranked-flow-what-it-does.png        solution 2 in three stages, only the
                                        last of which is fitted.
    ranked-flow-where-the-model-sits.png  what the placement of the fitted part
                                        buys, which is the point of solution 2.
    imitation-flow-what-it-does.png     solution 3 trained once and then run.
    imitation-flow-the-demonstrations.png  where the demonstrations come from
                                        and what they cost.

Every number written into these pictures is read out of the code rather than
out of a document, and the constant it came from is named in a comment beside
it below.

The boxes size themselves. A box's height comes from measuring its own text
with the renderer, so text cannot spill out of a box, and a box too narrow for
its longest line stops the run rather than producing a picture nobody looked
at.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_solution_flows_a.py
"""

from __future__ import annotations

import math

import matplotlib.colors as mcolors
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    TITLE_SIZE,
    WARN,
    bare,
    new,
    save,
)
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.transforms import Bbox

# ------------------------------------------------------------------ the numbers
#
# All of these are read out of code/src/, and the constant that holds each one
# is named so that a reader can check it in one step.

GRIP_ROOM_MM = 70          # bench/bench.py GRIP_ROOM = 0.070
JAW_TOP_MM = 65            # bench/bench.py JAW_TOP = PUSH_HEIGHT + FINGER_HEIGHT / 2
MU_LOWEST = 0.2            # 01-one-fixed-nudge/plan.py MU_LOWEST
MU_HIGHEST = 0.5           # 01-one-fixed-nudge/plan.py MU_HIGHEST
PROBE_MM = 5               # 01-one-fixed-nudge/plan.py PROBE = 0.005
PUSHES_PER_GLASS = 4       # bench/bench.py PUSHES_PER_GLASS
PUSHES_PER_TABLE = 16      # bench/bench.py PUSHES_PER_TABLE

HEADINGS = 72              # 01-one-fixed-nudge/plan.py HEADINGS
HEADING_STEP_DEG = 5       # 360 / HEADINGS
STEP_MM = 2                # 01-one-fixed-nudge/plan.py STEP = 0.002
LONGEST_PUSH_MM = 150      # 01-one-fixed-nudge/plan.py LONGEST_PUSH = 0.15
AIM_MARGIN_MM = 10         # 01-one-fixed-nudge/plan.py AIM_MARGIN = 0.010

TREES = 200                # 02-geometry-ranked/ranker.py TREES
DEPTH = 3                  # 02-geometry-ranked/ranker.py DEPTH
INPUTS = 8                 # len(02-geometry-ranked/features.py NAMES)

# 02-geometry-ranked/spread.json, over the training tables.
CROWDED_GROUPS = 269       # "a glass" -> "groups"
CANDIDATES_MEDIAN = 84     # "a glass" -> "candidates_per_group_median"

# The ablation: 02-geometry-ranked/results.json is the ranker's run and
# rule.json is the printed rule's, over the same held-out tables.
HELD_OUT = 50              # both files, "scenes"
GLASSES = 251              # both files, "glasses"
RANKER_RACKED = 185        # results.json glasses_end.racked
RANKER_PUSHES = 229        # results.json pushes.total
RULE_RACKED = 195          # rule.json glasses_end.racked
RULE_PUSHES = 213          # rule.json pushes.total

CHUNK = 120                # 03-imitation-from-demonstrations/chunks.py CHUNK
SEEN_SIZE = 192            # 03-imitation-from-demonstrations/pictures.py SEEN_SIZE
TEST_FROM = 10_000         # bench/bench.py TEST_SEEDS, the dividing line

LINESPACING = 1.42
PAD_X = 0.17               # inches of clear paper either side of a box's text
PAD_Y = 0.13               # and above and below it
GAP = 0.40                 # the length of the arrow between two stacked boxes

# What the audit at the end of each chart measures. A box records the paper it
# covers, a line records where it runs, and a caption records that it belongs to
# no box, so the audit can say when one has landed on another.
_BOXES: list[tuple[float, float, float, float, str]] = []
_LINES: list[tuple[float, float, float, float]] = []
_CAPTIONS: list = []


# --------------------------------------------------------------------------- #
# Drawing, in inches
#
# A sheet's data coordinates are inches, because the axes are told to fill the
# whole figure. That is what lets a box's height be measured text plus padding
# rather than a number guessed by eye.
# --------------------------------------------------------------------------- #


def sheet(width: float, height: float):
    """A figure whose data coordinates are inches from the bottom left corner."""
    figure, axis = new(width, height)
    axis.set_position((0.0, 0.0, 1.0, 1.0))
    bare(axis)
    axis.set_xlim(0.0, width)
    axis.set_ylim(0.0, height)
    _BOXES.clear()
    _LINES.clear()
    _CAPTIONS.clear()
    return figure, axis


def _measure(figure, text: str, size: float, weight: str = "normal") -> tuple[float, float]:
    """How many inches wide and tall this text will be when it is drawn."""
    renderer = figure.canvas.get_renderer()
    probe = figure.text(0.0, 0.0, text, fontsize=size, weight=weight, linespacing=LINESPACING)
    extent = probe.get_window_extent(renderer=renderer)
    probe.remove()
    return extent.width / figure.dpi, extent.height / figure.dpi


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill.

    Blending with white rather than setting an alpha, because these fills sit
    on top of each other and a stack of transparent fills darkens.
    """
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


def box(
    figure,
    axis,
    centre_x: float,
    top: float,
    width: float,
    text: str,
    *,
    edge=INK,
    face=PAPER,
    size=NOTE_SIZE,
    ink=INK,
    weight="normal",
    lw=1.2,
) -> float:
    """A rounded box of the given width, hung from ``top``. Returns its bottom.

    The height is measured text plus padding, so a box is never too short for
    what is in it, and a box too narrow for its longest line is an error rather
    than a picture with words hanging out of it.
    """
    text_width, text_height = _measure(figure, text, size, weight)
    if text_width > width - 2.0 * PAD_X:
        raise SystemExit(
            f"a box {width:.2f} in wide needs to be "
            f"{text_width + 2.0 * PAD_X:.2f} in for this text:\n{text}"
        )
    height = text_height + 2.0 * PAD_Y
    axis.add_patch(
        FancyBboxPatch(
            (centre_x - width / 2.0, top - height),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=0.09",
            linewidth=lw,
            edgecolor=edge,
            facecolor=face,
            zorder=3,
        )
    )
    axis.text(
        centre_x,
        top - height / 2.0,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=ink,
        weight=weight,
        linespacing=LINESPACING,
        zorder=5,
    )
    _BOXES.append((centre_x - width / 2.0, top - height, centre_x + width / 2.0, top,
                   text.splitlines()[0][:44]))
    return top - height


def note(
    axis,
    x: float,
    top: float,
    text: str,
    *,
    colour=MUTED,
    size=NOTE_SIZE,
    ha="left",
    weight="normal",
    figure=None,
) -> float:
    """A line or two of loose text hung from ``top``. Returns its bottom."""
    height = _measure(figure, text, size, weight)[1] if figure is not None else 0.0
    _CAPTIONS.append(
        axis.text(
            x,
            top - height / 2.0 if figure is not None else top,
            text,
            ha=ha,
            va="center",
            fontsize=size,
            color=colour,
            weight=weight,
            linespacing=LINESPACING,
            zorder=7,
        )
    )
    return top - height


def arrow(axis, start, end, *, colour=INK, lw=1.3, dashed=False) -> None:
    _LINES.append((start[0], start[1], end[0], end[1]))
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=lw,
            color=colour,
            linestyle=(0, (4, 3)) if dashed else "solid",
            shrinkA=0,
            shrinkB=0,
            zorder=6,
        )
    )


def run(axis, start, end, *, colour=INK, lw=1.3) -> None:
    """One straight leg of a route, with no head on it."""
    _LINES.append((start[0], start[1], end[0], end[1]))
    axis.plot([start[0], end[0]], [start[1], end[1]], color=colour, lw=lw, zorder=4)


def elbow(axis, start, end, by_way_of: float, *, colour=INK, lw=1.3) -> None:
    """An arrow that leaves one box sideways, runs down ``by_way_of``, and comes
    back in sideways. Used where one step hands off to a column beside it.
    """
    x0, y0 = start
    x1, y1 = end
    run(axis, (x0, y0), (by_way_of, y0), colour=colour, lw=lw)
    run(axis, (by_way_of, y0), (by_way_of, y1), colour=colour, lw=lw)
    arrow(axis, (by_way_of, y1), (x1, y1), colour=colour, lw=lw)


def loop_back(
    axis,
    chain_x: float,
    from_y: float,
    to_y: float,
    spine_x: float,
    *,
    colour=INK,
    lw=1.3,
    drop=0.24,
    rise=0.24,
) -> float:
    """The look-again arrow: down out of the last step, round the outside of the
    chain, and back into the top of the first. Returns the height of its lower
    run, so that a caption can be hung below it.

    Drawn with right angles rather than as one slanted line, because a slanted
    line across a chart this tall passes close to several boxes it has nothing
    to do with.
    """
    low, high = from_y - drop, to_y + rise
    run(axis, (chain_x, from_y), (chain_x, low), colour=colour, lw=lw)
    run(axis, (chain_x, low), (spine_x, low), colour=colour, lw=lw)
    run(axis, (spine_x, low), (spine_x, high), colour=colour, lw=lw)
    run(axis, (spine_x, high), (chain_x, high), colour=colour, lw=lw)
    arrow(axis, (chain_x, high), (chain_x, to_y), colour=colour, lw=lw)
    return low


def loop_back_into_the_side(
    axis,
    chain_x: float,
    from_y: float,
    box_left: float,
    box_middle: float,
    spine_x: float,
    *,
    colour=INK,
    lw=1.3,
    drop=0.42,
) -> float:
    """The same look-again arrow, but coming back into the side of the first step.

    Used where something else already arrives at the top of that step, so that
    two routes with different meanings do not end on the same point.
    """
    low = from_y - drop
    run(axis, (chain_x, from_y), (chain_x, low), colour=colour, lw=lw)
    run(axis, (chain_x, low), (spine_x, low), colour=colour, lw=lw)
    run(axis, (spine_x, low), (spine_x, box_middle), colour=colour, lw=lw)
    arrow(axis, (spine_x, box_middle), (box_left, box_middle), colour=colour, lw=lw)
    return low


def band(axis, left: float, bottom: float, width: float, height: float, colour, label) -> None:
    """A lane of the chart, with the name of whoever owns its steps down the left."""
    axis.add_patch(
        Rectangle(
            (left, bottom),
            width,
            height,
            facecolor=_tint(colour, 0.90),
            edgecolor=colour,
            linewidth=1.0,
            zorder=1,
        )
    )
    axis.text(
        left + 0.20,
        bottom + height / 2.0,
        label,
        rotation=90,
        ha="center",
        va="center",
        fontsize=LABEL_SIZE,
        color=colour if colour != MUTED else INK,
        weight="bold",
        zorder=2,
    )


def title(figure, axis, width: float, top: float, text: str) -> float:
    """The chart's own title, centred, as a text artist rather than an axes title.

    The axes fill the figure here, so an axes title would be drawn off the top
    of the paper.
    """
    return note(axis, width / 2.0, top, text, colour=INK, size=TITLE_SIZE, ha="center",
                figure=figure)


def _inside(segment, rect, shrink=0.045) -> float:
    """How far a line segment runs through the inside of a box, in inches.

    A segment that only touches the edge of a box, which is what every arrow
    between two boxes does, scores zero. A segment that crosses a box it has
    nothing to do with scores its length inside, and that is the fault worth
    finding.
    """
    x0, y0, x1, y1 = segment
    left, bottom, right, top = rect[0] + shrink, rect[1] + shrink, rect[2] - shrink, rect[3] - shrink
    dx, dy = x1 - x0, y1 - y0
    near, far = 0.0, 1.0
    for slope, room in ((-dx, x0 - left), (dx, right - x0), (-dy, y0 - bottom), (dy, top - y0)):
        if slope == 0.0:
            if room < 0.0:
                return 0.0
        else:
            cut = room / slope
            if slope < 0.0:
                if cut > far:
                    return 0.0
                near = max(near, cut)
            else:
                if cut < near:
                    return 0.0
                far = min(far, cut)
    return max(0.0, far - near) * math.hypot(dx, dy)


def audit(figure, axis, name: str) -> None:
    """Measure the drawn figure and name the faults a glance over the PNG misses.

    Four of them: two pieces of text sharing a patch of paper, two boxes
    overlapping, a caption landing on a box, and a line running through a box it
    does not connect. The faults are printed rather than raised, so the picture
    is still written and can be looked at beside the complaint.
    """
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    faults = []

    def overlap(a, b, room=1.0) -> bool:
        return (min(a.x1, b.x1) - max(a.x0, b.x0) > room
                and min(a.y1, b.y1) - max(a.y0, b.y0) > room)

    drawn = [(t, t.get_window_extent(renderer)) for t in axis.texts if t.get_text().strip()]
    for index, (one, here) in enumerate(drawn):
        for two, there in drawn[index + 1:]:
            if overlap(here, there):
                faults.append(
                    f"  text over text: {one.get_text().splitlines()[0][:34]!r}"
                    f" and {two.get_text().splitlines()[0][:34]!r}"
                )

    for index, first in enumerate(_BOXES):
        for second in _BOXES[index + 1:]:
            if (min(first[2], second[2]) - max(first[0], second[0]) > 0.02
                    and min(first[3], second[3]) - max(first[1], second[1]) > 0.02):
                faults.append(f"  box over box: {first[4]!r} and {second[4]!r}")

    for caption in _CAPTIONS:
        here = caption.get_window_extent(renderer)
        for rect in _BOXES:
            there = Bbox(axis.transData.transform([(rect[0], rect[1]), (rect[2], rect[3])]))
            if overlap(here, there, room=2.0):
                faults.append(
                    f"  caption over a box: {caption.get_text().splitlines()[0][:40]!r}"
                    f" on {rect[4]!r}"
                )
                break

    for segment in _LINES:
        for rect in _BOXES:
            through = _inside(segment, rect[:4])
            if through > 0.06:
                faults.append(f"  a line runs {through:.2f} in through the box {rect[4]!r}")

    if faults:
        print(f"{name}: {len(faults)} thing(s) to fix")
        print("\n".join(sorted(set(faults))))


def finish(figure, axis, name: str, bottom: float) -> None:
    """Audit the drawn chart, then say how much paper is spare below it."""
    if bottom < 0.0:
        raise SystemExit(f"{name}: the layout ran {-bottom:.2f} in off the bottom of the sheet")
    audit(figure, axis, name)
    print(f"  {name}: {bottom:.2f} in of spare paper at the bottom")


# --------------------------------------------------------------------------- #
# 1. solution 1, as the loop it is
# --------------------------------------------------------------------------- #


def nudge_what_it_does() -> None:
    """One fixed nudge: measure, choose, push, look again, and the three endings.

    The chart is drawn as one closed loop with the real step names in it,
    because the loop is the whole method: there is nothing inside it to
    describe separately. The three ways out hang off the one test that reads
    the fresh measurements.
    """
    width, height = 12.65, 10.35
    figure, axis = sheet(width, height)
    band_left, spine = 0.60, 0.25
    chain_w = 6.3
    chain_x = band_left + 0.95 + chain_w / 2.0
    corridor = band_left + chain_w + 1.25 + 0.30      # between the band and the endings
    end_x, end_w = 10.55, 3.6

    y = title(figure, axis, width, height - 0.12,
              "One fixed nudge: what it does, one pass at a time") - 0.26

    band_top = y
    first_top = y - 0.34

    y = box(
        figure, axis, chain_x, first_top, chain_w,
        "look(): the camera measures the table and hands back, for every glass, where it\n"
        "stands, how wide it is at its widest, and how wide the foot it stands on is.",
    )
    first_bottom = y

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Is this table finished, or is there nothing left to try?",
        face=_tint(MUTED, 0.88), weight="bold", size=LABEL_SIZE,
    )
    test_mid = y + 0.5 * (first_bottom - GAP - y)

    note(axis, chain_x + 0.14, y - 0.10, "no", colour=INK, size=NOTE_SIZE - 0.6, figure=figure)
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "For each glass, work out how much clear room the gripper is short of, measured to\n"
        f"the nearest edge of each neighbour: {GRIP_ROOM_MM} mm, plus half the neighbour's widest\n"
        "width, minus the distance between their two middles.",
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Take the glass with the worst shortfall, and the neighbour responsible for it.",
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Check that glass against the tipping rule, and refuse it if it fails. The top edge of\n"
        f"the jaw rides {JAW_TOP_MM} mm above the table, and a glass slides rather than tips only while\n"
        "that height is below a / μ, where 2a is its measured foot. Nothing in the cell\n"
        f"measures μ, so the rule is asked at both ends of {MU_LOWEST} to {MU_HIGHEST}, and a glass the two\n"
        f"ends disagree about is settled by a {PROBE_MM} mm test push and a look before and after.",
        edge=WARN, face=_tint(WARN, 0.93),
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Point the jaw along the line that runs from the neighbour's middle through the\n"
        "glass's middle, continued outwards.",
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Set the travel to a fixed fraction of the shortfall. The fraction is less than one, so\n"
        "the push closes part of the gap and the rest is left to the next pass.",
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Hand the push over as three numbers: where to put the jaw down, which way to point\n"
        "it, and how far to travel. The examiner's own macro expands those three into a jaw\n"
        "trajectory — come down, feel forward slowly, slide, back off, lift clear.",
        edge=GLASS, face=_tint(GLASS, 0.88),
    )

    band(axis, band_left, y - 0.32, chain_w + 1.25, band_top - (y - 0.32),
         MUTED, "one pass of the loop")

    low = loop_back(axis, chain_x, y, first_top, spine, drop=0.44, rise=0.46)
    bottom = note(
        axis, spine + 0.14, low - 0.26,
        "Look at the table again, and make the four decisions afresh from the new measurements.\n"
        "Nothing is carried from one pass to the next except how many pushes have been spent,\n"
        "because the fresh measurement is the only state this method has.",
        colour=INK, figure=figure,
    )

    # ---- the three ways the loop ends, which are alternatives rather than a sequence
    y = note(axis, end_x, test_mid - 0.90, "The loop ends in one of three ways",
             colour=INK, size=LABEL_SIZE, ha="center", weight="bold", figure=figure) - 0.26
    middles = []
    for face, edge, text in (
        (GOOD, GOOD,
         "Every glass has room, so the open jaw\n"
         "can close round each of them in turn,\n"
         "and this table is done."),
        (MUTED, MUTED,
         f"The push budget is spent: {PUSHES_PER_GLASS} pushes on\n"
         f"one glass, or {PUSHES_PER_TABLE} on one table. Pushes are\n"
         "arm time, and the budget is finite."),
        (WARN, WARN,
         "The only honest answer left is a refusal,\n"
         "recorded with its reason: this glass tips\n"
         "before it slides, or there is nowhere\n"
         "clear to push it to, or pushing it has\n"
         "stopped making it less crowded."),
    ):
        top_of_box = y
        y = box(figure, axis, end_x, top_of_box, end_w, text,
                edge=edge, face=_tint(face, 0.90))
        middles.append(((top_of_box + y) / 2.0, edge))
        y -= 0.22

    # One branch, taken when the test above answers yes, fanning out to whichever
    # of the three it was. They are alternatives, so none of them leads to another.
    note(axis, corridor + 0.10, test_mid - 0.16, "yes", colour=INK,
         size=NOTE_SIZE - 0.6, figure=figure)
    run(axis, (chain_x + chain_w / 2.0, test_mid), (corridor, test_mid))
    run(axis, (corridor, test_mid), (corridor, middles[-1][0]))
    for level, colour in middles:
        arrow(axis, (corridor, level), (end_x - end_w / 2.0, level), colour=colour)

    note(axis, end_x, y - 0.04,
         "A refusal is a result rather than a failure,\nand the scorecard counts it as one.",
         colour=INK, size=NOTE_SIZE - 0.4, ha="center", figure=figure)

    finish(figure, axis, "nudge-flow-what-it-does.png", min(bottom, y - 0.62))
    save(figure, "nudge-flow-what-it-does.png")


# --------------------------------------------------------------------------- #
# 2. why solution 1 repeats instead of predicting
# --------------------------------------------------------------------------- #


def nudge_why_prediction_fails() -> None:
    """One flow chart: why a method that predicts where the glass stops cannot work here.

    The chart ends in a claim that can be wrong, and the reason it can be wrong
    is one number nothing in this cell measures. The method that answers it is
    a chart of its own, because two charts in one picture halve the size of
    both.
    """
    width, height = 7.6, 4.4
    figure, axis = sheet(width, height)
    middle, span = width / 2.0, 5.6

    top = title(figure, axis, width, height - 0.12,
                "Why predicting where the glass stops does not work here") - 0.34

    y = box(figure, axis, middle, top, span,
            "Work out where the glass will come to rest, and aim the push there.")
    arrow(axis, (middle, y), (middle, y - GAP))
    y = box(figure, axis, middle, y - GAP, span,
            "That needs the friction with the table,\n"
            "and how the weight sits on the foot.")
    arrow(axis, (middle, y), (middle, y - GAP), colour=WARN)
    y = box(figure, axis, middle, y - GAP, span,
            "Nobody in this cell has measured either.\n"
            f"The most that can be believed is a range: {MU_LOWEST} to {MU_HIGHEST}.",
            edge=WARN, face=_tint(WARN, 0.93))
    arrow(axis, (middle, y), (middle, y - GAP), colour=WARN)
    bottom = box(figure, axis, middle, y - GAP, span,
                 "So the push lands somewhere else:\n"
                 "short of the room needed, or into the next glass.",
                 edge=WARN, face=_tint(WARN, 0.86), weight="bold")

    finish(figure, axis, "nudge-flow-why-prediction-fails.png", bottom - 0.30)
    save(figure, "nudge-flow-why-prediction-fails.png")


def nudge_repeat_not_predict() -> None:
    """One flow chart: the loop that predicts nothing and runs again instead."""
    width, height = 7.6, 4.7
    figure, axis = sheet(width, height)
    middle, span = width / 2.0 - 0.3, 5.4
    corridor = middle + span / 2.0 + 0.5

    top = title(figure, axis, width, height - 0.12,
                "One fixed nudge: measure, push a little, and look again") - 0.34

    y = box(figure, axis, middle, top, span,
            "Measure how much room the glass is short of.")
    measure_mid = y + 0.5 * (top - y)
    arrow(axis, (middle, y), (middle, y - GAP), colour=GOOD)
    y = box(figure, axis, middle, y - GAP, span,
            "Push straight away from the crowding neighbour.\n"
            "That direction opens the gap at any friction.",
            edge=GOOD, face=_tint(GOOD, 0.90))
    arrow(axis, (middle, y), (middle, y - GAP), colour=GOOD)
    y = box(figure, axis, middle, y - GAP, span,
            "Travel a fixed fraction of the shortfall,\n"
            "and the fraction is less than one.",
            edge=GOOD, face=_tint(GOOD, 0.90))
    arrow(axis, (middle, y), (middle, y - GAP), colour=GOOD)
    bottom = box(figure, axis, middle, y - GAP, span,
                 "Look at the table again.\n"
                 "The shortfall left is smaller than it was.")
    elbow(axis, (middle + span / 2.0, bottom + 0.22),
          (middle + span / 2.0, measure_mid), corridor, colour=GOOD)
    bottom = note(axis, middle, bottom - 0.22,
                  "and again, until the glass is no longer short of room",
                  colour=GOOD, ha="center", weight="bold", figure=figure)

    finish(figure, axis, "nudge-flow-repeat-not-predict.png", bottom - 0.20)
    save(figure, "nudge-flow-repeat-not-predict.png")


# --------------------------------------------------------------------------- #
# 3. solution 2, in three stages
# --------------------------------------------------------------------------- #


def ranked_what_it_does() -> None:
    """Geometry generates and a model ranks, as three stages in three bands.

    The bands are the argument: two stages of arithmetic and then one fitted
    stage, in that order and never the other way round. The counts on the
    middle band are what makes the third stage necessary at all, because a
    stage that returned one survivor would need nobody to choose.
    """
    width, height = 10.6, 12.3
    figure, axis = sheet(width, height)
    band_left, spine = 0.55, 0.22
    chain_w = 8.3
    chain_x = band_left + 0.95 + chain_w / 2.0
    left_edge = chain_x - chain_w / 2.0

    y = title(figure, axis, width, height - 0.12,
              "Geometry generates and a model ranks: what it does, one push at a time") - 0.34

    # ---- the geometry proposes
    band_top = y
    first_top = y - 0.30
    y = box(
        figure, axis, chain_x, first_top, chain_w,
        "look(): where every glass stands, how wide it is at its widest, and how wide its foot is.",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"For each crowded glass, sweep every heading around it: {HEADINGS} of them, one every {HEADING_STEP_DEG} degrees.",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"Along each heading, step the travel out in {STEP_MM} mm steps to {LONGEST_PUSH_MM} mm. The first step that fails a\n"
        "test below ends that heading, because a clash at one length is still there further along the same line.",
    )
    band(axis, band_left, y - 0.26, chain_w + 1.25, band_top - (y - 0.26),
         MUTED, "the geometry proposes")

    # ---- the geometry filters
    arrow(axis, (chain_x, y - 0.26), (chain_x, y - 0.26 - GAP))
    y = y - 0.26 - GAP
    band_top = y
    y = note(axis, chain_x, y - 0.22, "A candidate survives only if all four of these hold.",
             colour=INK, size=LABEL_SIZE, ha="center", weight="bold", figure=figure) - 0.14
    for text in (
        "The arm can reach it: the destination is inside the ring the arm stands over comfortably.",
        "The push drags the glass and swings the jaw, the gripper body and the wrist clear of every neighbour.",
        f"The glass lands inside the glass zone, and has the room the jaw needs with {AIM_MARGIN_MM} mm of aiming margin to spare.",
        f"The jaw touches the glass below the height at which it would tip instead of slide: its top edge at {JAW_TOP_MM} mm,\n"
        f"against a / μ for this glass's own measured foot, at the most pessimistic friction in {MU_LOWEST} to {MU_HIGHEST}.",
    ):
        y = box(figure, axis, chain_x, y, chain_w, text,
                edge=WARN, face=_tint(WARN, 0.94)) - 0.11
    y = note(
        axis, chain_x, y - 0.16,
        f"This is a set to choose from rather than an answer. Over {CROWDED_GROUPS} crowded glasses on the training tables, the\n"
        f"middle one is left with {CANDIDATES_MEDIAN} surviving candidates, and every one of them is a push nothing above can reject.",
        colour=INK, ha="center", figure=figure,
    )
    band(axis, band_left, y - 0.24, chain_w + 1.25, band_top - (y - 0.24),
         WARN, "the geometry filters")

    # ---- the model ranks
    arrow(axis, (chain_x, y - 0.24), (chain_x, y - 0.24 - GAP))
    y = y - 0.24 - GAP
    band_top = y
    y = box(
        figure, axis, chain_x, y - 0.26, chain_w,
        f"Describe each survivor by {INPUTS} numbers, every one of them a length, an angle, a count or a ratio: the\n"
        "contact angle from the line to the nearest edge, the push distance, the room the destination would\n"
        "have, how far the destination is from the edge of the zone and from the rack, how many neighbours sit\n"
        "within reach, the foot width of the glass being moved, and the push height over its topple limit.",
        edge=GLASS, face=_tint(GLASS, 0.92),
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP), colour=GLASS)
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"{TREES} boosted regression trees, each {DEPTH} questions deep, turn that list into one score. This is the only\n"
        "fitted part of the solution, and its whole output is a score: nothing downstream reads the number.",
        edge=GLASS, face=_tint(GLASS, 0.86), weight="bold",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP), colour=GLASS)
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "Sort the survivors by that score and make the first push on the sorted list. The examiner's macro\n"
        "expands it into a jaw trajectory, the push is made, and the arm looks at the table again.",
    )
    band(axis, band_left, y - 0.30, chain_w + 1.25, band_top - (y - 0.30),
         GLASS, "the model ranks what survived")

    low = loop_back(axis, chain_x, y, first_top, spine, drop=0.42, rise=0.42)
    bottom = note(
        axis, spine + 0.14, low - 0.26,
        "One push per pass, until every glass has room, the glasses that are left have been refused, or the\n"
        "push budget is spent. Nothing the model produced is carried over: the next pass enumerates afresh.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "ranked-flow-what-it-does.png", bottom - 0.10)
    save(figure, "ranked-flow-what-it-does.png")


# --------------------------------------------------------------------------- #
# 4. where the fitted part sits in solution 2
# --------------------------------------------------------------------------- #


def ranked_where_the_model_sits() -> None:
    """What the placement of the fitted part buys.

    Drawn as a funnel on purpose. The four failures nothing in this project can
    repair are settled above the model, so the only mistake left below it is an
    ordering, and the three boxes at the foot are what that costs.
    """
    width, height = 11.4, 9.3
    figure, axis = sheet(width, height)
    left_x, right_x, pair_w = 3.05, 8.45, 5.1
    middle, wide = 5.75, 9.2

    y = title(figure, axis, width, height - 0.12,
              "Where the fitted part sits, and what that placement buys") - 0.30
    y = note(
        axis, middle, y,
        "Every way a push can fail unrecoverably is settled by arithmetic, before the model is consulted at all.",
        colour=INK, size=LABEL_SIZE, ha="center", weight="bold", figure=figure,
    ) - 0.24

    row = y
    bottoms = []
    for column, text in (
        (left_x,
         "Toppling. A push whose contact height reaches\n"
         f"a / μ for this glass's measured foot is refused.\n"
         "Nothing in this project stands a toppled glass\n"
         "back up, which is why this one comes first."),
        (right_x,
         "Leaving the glass zone. A destination outside\n"
         "the zone the glasses are allowed to stand on is\n"
         "refused, with the aiming margin counted against\n"
         "it rather than ignored."),
    ):
        bottoms.append(box(figure, axis, column, row, pair_w, text,
                           edge=WARN, face=_tint(WARN, 0.92)))
    row = min(bottoms) - 0.18
    bottoms = []
    for column, text in (
        (left_x,
         "Leaving the arm's reach. A destination the arm\n"
         "cannot comfortably stand over is refused."),
        (right_x,
         "Striking the rack. A swept path that fouls the\n"
         "rack on the arm's other side is refused."),
    ):
        bottoms.append(box(figure, axis, column, row, pair_w, text,
                           edge=WARN, face=_tint(WARN, 0.92)))
    y = min(bottoms)

    for column in (left_x, right_x):
        run(axis, (column, y), (column, y - 0.26), colour=WARN)
    run(axis, (left_x, y - 0.26), (right_x, y - 0.26), colour=WARN)
    arrow(axis, (middle, y - 0.26), (middle, y - 0.26 - 0.30), colour=WARN)
    y = box(
        figure, axis, middle, y - 0.56, wide,
        "All four are geometric tests on the destination, all four run before the model, and not one of them consults it.\n"
        "A candidate they reject is gone: nothing later in the sequence reads a score back into the rejection.",
        edge=GOOD, face=_tint(GOOD, 0.90),
    )

    arrow(axis, (middle, y), (middle, y - GAP), colour=GOOD)
    y = box(
        figure, axis, middle, y - GAP, wide,
        "The model is handed whatever survived, and gives each survivor one score. Sorting by that score is its entire\n"
        "output, and the arm makes the first push on the sorted list.",
        edge=GLASS, face=_tint(GLASS, 0.86), weight="bold",
    )

    y -= 0.34
    for text in (
        "So the worst a badly fitted model can do is put a safe push before a better safe push. The arm then makes a\n"
        "push that was legal and less useful than another legal push would have been, looks at the table, and chooses\n"
        "again. That costs one push out of the budget and one contact with a glass, and nothing worse.",
        "The model can never add a candidate to the list, and never bring back one the geometry rejected, so the ceiling\n"
        "on how badly this can fail comes from the arrangement rather than from the model's accuracy. A better model\n"
        "makes wasted pushes rarer; only the geometry decides how bad things get.",
        "And deleting the model leaves a working system behind, because a printed rule picks instead: take the shortest\n"
        f"push that gives the glass room. Over the same {HELD_OUT} held-out tables the rule racked {RULE_RACKED} of {GLASSES} glasses in {RULE_PUSHES}\n"
        f"pushes, where the ranker racked {RANKER_RACKED} in {RANKER_PUSHES}. Neither toppled a glass, which is the point of the arrangement.",
    ):
        arrow(axis, (middle, y), (middle, y - 0.28), colour=GOOD)
        y = box(figure, axis, middle, y - 0.28, wide, text,
                edge=GOOD, face=_tint(GOOD, 0.95)) - 0.08

    bottom = note(
        axis, middle, y - 0.20,
        "A wasted look costs seconds of arm movement. A wasted push costs seconds and a contact with a glass, and contact is where\n"
        "things break, so a push ranker has to be the better of the two to be worth the same amount.",
        colour=INK, ha="center", figure=figure,
    )

    finish(figure, axis, "ranked-flow-where-the-model-sits.png", bottom - 0.10)
    save(figure, "ranked-flow-where-the-model-sits.png")


# --------------------------------------------------------------------------- #
# 5. solution 3, trained once and then run
# --------------------------------------------------------------------------- #


def imitation_what_it_does() -> None:
    """Imitation from demonstrations: the training that happens once, then the run.

    Two bands, because the two halves happen at different times and a reader
    who mixes them up thinks the teacher is present during a run. It is not:
    the only thing that crosses from the upper band to the lower one is the
    weights file.
    """
    width, height = 10.7, 10.6
    figure, axis = sheet(width, height)
    band_left, spine = 0.55, 0.22
    chain_w = 8.4
    chain_x = band_left + 0.95 + chain_w / 2.0
    left_edge = chain_x - chain_w / 2.0

    y = title(figure, axis, width, height - 0.12,
              "Imitation from demonstrations: fitted once, then run on every pass") - 0.30

    # ---- training, which happens once
    band_top = y
    y = box(
        figure, axis, chain_x, y - 0.26, chain_w,
        "The teacher is the solution before this one: geometry generates every legal push and a fitted model\n"
        f"ranks them. It is a program rather than a person. It runs over the training half of the tables, which are\n"
        f"the ones numbered below {TEST_FROM:,}, so no demonstration is ever drawn from a table this will be marked on.",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"Every push the teacher makes is recorded as one example: a {SEEN_SIZE} by {SEEN_SIZE} picture of the table from\n"
        "straight above, and the waypoints the jaw actually followed while making that push.",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "The recordings where something went wrong are dropped, on the examiner's own verdict about the\n"
        "outcome. A cloned policy has no notion of a good action and a bad one, so a push that toppled a glass\n"
        "would be a label like any other and the fitting would move towards producing it.",
        edge=WARN, face=_tint(WARN, 0.94),
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "ACT, an action chunking transformer, is fitted from random numbers on what is left. What it learns is\n"
        "one mapping: from a picture of a crowded table, to the chunk of waypoints the teacher would have followed.",
        edge=GLASS, face=_tint(GLASS, 0.88), weight="bold",
    )
    band(axis, band_left, y - 0.26, chain_w + 1.25, band_top - (y - 0.26),
         MUTED, "fitted once, before any run")

    arrow(axis, (chain_x, y - 0.26), (chain_x, y - 0.26 - 0.52), colour=GLASS)
    note(axis, chain_x + 0.14, y - 0.44, "the weights, and nothing else, cross into a run",
         colour=GLASS, size=NOTE_SIZE - 0.4, figure=figure)
    y = y - 0.78

    # ---- the run
    band_top = y
    first_top = y - 0.26
    y = box(
        figure, axis, chain_x, first_top, chain_w,
        "A view of the table from straight above goes in. No positions, no widths, no candidate list, no friction.",
    )
    first_middle = (first_top + y) / 2.0
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"The policy returns an action chunk: {CHUNK} consecutive jaw waypoints, predicted together in one pass.\n"
        "They are consistent with each other by construction, and nothing is read back while they run.",
        edge=GLASS, face=_tint(GLASS, 0.92),
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "The examiner follows those waypoints directly. There is nothing to expand, because a chunk already is a\n"
        "jaw trajectory, and the slow feel for the glass is part of the chunk, copied from the teacher's own push.",
    )
    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "The arm looks again, and the fresh picture is the next input. One push is one chunk, and the state the\n"
        "policy is asked about is always a measured table rather than a predicted one.",
    )
    band(axis, band_left, y - 0.30, chain_w + 1.25, band_top - (y - 0.30),
         GLASS, "once per push, at run time")

    low = loop_back_into_the_side(axis, chain_x, y, left_edge, first_middle, spine,
                                 colour=GLASS, drop=0.42)
    bottom = note(
        axis, spine + 0.14, low - 0.26,
        "The loop runs until every glass has room, the glasses that are left have been refused with a reason, or the\n"
        f"push budget is spent at {PUSHES_PER_GLASS} pushes on one glass and {PUSHES_PER_TABLE} on one table.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "imitation-flow-what-it-does.png", bottom - 0.10)
    save(figure, "imitation-flow-what-it-does.png")


# --------------------------------------------------------------------------- #
# 6. where solution 3's demonstrations come from, and what they cost
# --------------------------------------------------------------------------- #


def imitation_the_demonstrations() -> None:
    """The defining dependency of solution 3: a programmed teacher, and its price.

    The left column is why the demonstrations are nearly free. The right column
    is the bill, and the sketch at the foot is the part of that bill which is
    hardest to see from the method's description, because filtering the data
    changes which situations are covered and not only which actions are
    recommended.
    """
    width, height = 11.6, 8.9
    figure, axis = sheet(width, height)
    left_x, left_w = 2.95, 4.95
    right_x, right_w = 8.55, 5.25

    top = title(figure, axis, width, height - 0.12,
                "Where the demonstrations come from, and what they cost") - 0.30
    note(axis, left_x, top, "Free and plentiful, because the teacher is a program",
         colour=GOOD, size=LABEL_SIZE, ha="center", weight="bold", figure=figure)
    note(axis, right_x, top, "And the bill, which cannot be engineered away",
         colour=WARN, size=LABEL_SIZE, ha="center", weight="bold", figure=figure)
    row = top - 0.34

    y = row
    for text in (
        "The teacher is another one of the six, running\n"
        "on the same examiner: geometry generates the\n"
        "legal pushes and a fitted model ranks them.",
        "So no person teleoperates anything. There is\n"
        "no rig to build, no operator's hours to\n"
        "schedule, and no agreement to reach about\n"
        "what a good push looks like.",
        "The labels cost arm time on a simulated\n"
        "examiner and nothing else, and a push in\n"
        "MuJoCo is cheap, so the set is as large as\n"
        "there is patience for.",
        "Every table comes from a single number, so\n"
        "the set is regenerated rather than archived,\n"
        f"and the numbers used stay below {TEST_FROM:,}, which\n"
        "is where the tables it is marked on begin.",
        "And the teacher can be asked again, at any\n"
        "state, for nothing. A person who\n"
        "demonstrated a hundred pushes last week\n"
        "cannot be asked about a table that came up\n"
        "today; a program can, every time.",
    ):
        y = box(figure, axis, left_x, y, left_w, text,
                edge=GOOD, face=_tint(GOOD, 0.93)) - 0.16
    left_bottom = y

    y = row
    for text in (
        "The policy cannot beat the teacher by much,\n"
        "because nothing in behaviour cloning ever\n"
        "evaluates an outcome. The label is the action\n"
        "the teacher took, and the only thing measured\n"
        "during training is how far the network's action\n"
        "was from that one.",
        "So the demonstrations hold only the pushes the\n"
        "teacher could express. A push the heading sweep\n"
        "never wrote down appears in no example, and the\n"
        "student has no way to discover it.",
        "And filtering to the pushes that worked thins the\n"
        "data exactly where the teacher struggled. On a\n"
        "kind of table it handles badly, most of its pushes\n"
        "fail, so most are dropped, so few examples of that\n"
        "table survive.",
        "The student is therefore fitted most densely where\n"
        "help was least needed, and thinly where it was\n"
        "needed most. Filtering by outcome does not only\n"
        "change which actions are recommended. It changes\n"
        "which situations are covered at all.",
    ):
        y = box(figure, axis, right_x, y, right_w, text,
                edge=WARN, face=_tint(WARN, 0.92)) - 0.16
    right_bottom = y

    # ---- the thinning, sketched
    y = min(left_bottom, right_bottom) - 0.26
    axis.plot([0.4, width - 0.4], [y, y], color=MUTED, lw=0.9, ls=(0, (5, 4)), zorder=1)
    y = note(
        axis, width / 2.0, y - 0.24,
        "What the filtering does to the coverage, drawn rather than asserted. One square is one of the teacher's pushes.",
        colour=INK, size=LABEL_SIZE, ha="center", weight="bold", figure=figure,
    ) - 0.22

    side, step, start = 0.19, 0.265, 3.55
    for label, kept, dropped, colour in (
        ("A kind of table the teacher handles well:", 9, 1, GOOD),
        ("A kind of table it handles badly:", 2, 8, WARN),
    ):
        y = note(axis, start - 0.14, y, label, colour=INK, ha="right", figure=figure)
        middle = y + side / 2.0 - 0.02
        for index in range(kept + dropped):
            filled = index < kept
            axis.add_patch(
                Rectangle(
                    (start + index * step, middle - side / 2.0), side, side,
                    facecolor=_tint(colour, 0.25) if filled else PAPER,
                    edgecolor=colour if filled else MUTED,
                    linewidth=1.1, zorder=3,
                )
            )
        note(axis, start + (kept + dropped) * step + 0.14, middle,
             f"{kept} kept, {dropped} dropped", colour=colour, size=NOTE_SIZE - 0.4,
             figure=figure)
        y = middle - side / 2.0 - 0.30

    note(axis, start - 0.14, y + 0.08, "filled: the push worked, so it was kept\nhollow: it failed, so it was dropped",
         colour=MUTED, size=NOTE_SIZE - 0.6, ha="right", figure=figure)
    bottom = note(
        axis, start, y + 0.08,
        "The counts in this sketch stand for the mechanism and are not a measurement of these tables: the collection\n"
        "writes its own table of kept and dropped pushes, and the thinning it reports on the examiner's tables is small.\n"
        "Drawing more tables of the kind that thinned is the cheap repair here, and it is one only simulation allows.",
        colour=INK, figure=figure,
    )

    finish(figure, axis, "imitation-flow-the-demonstrations.png", bottom - 0.10)
    save(figure, "imitation-flow-the-demonstrations.png")


def main() -> None:
    nudge_what_it_does()
    nudge_why_prediction_fails()
    nudge_repeat_not_predict()
    ranked_what_it_does()
    ranked_where_the_model_sits()
    imitation_what_it_does()
    imitation_the_demonstrations()


if __name__ == "__main__":
    main()
