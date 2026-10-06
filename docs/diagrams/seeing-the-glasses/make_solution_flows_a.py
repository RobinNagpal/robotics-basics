"""The flow charts for the first three solutions: what each one actually does.

Each solution in this book opens its chapter with a "what it is" document, and a
reader should be able to look at the charts there and say what the solution does
from end to end without reading the prose. The same charts are shown again on
the solution's short page in the six-solutions chapter, so each one has to stand
on its own.

    rules-flow-what-it-does.png     solution 1 as one chain, with the real step
                                    names, drawn in four lanes that say where
                                    the question is being asked: in the picture,
                                    in the room, on the table, and back in the
                                    picture.
    rules-flow-each-group.png       what one group has to pass before it is
                                    reported, with the three outcomes and the
                                    window the one setting is pinned inside.
    network-flow-what-it-does.png   solution 2: one network, two heads, and the
                                    votes, with the blob coming apart drawn
                                    underneath the chain.
    network-flow-labels.png         the two places solution 2's training labels
                                    can come from, side by side, because nothing
                                    else about the method differs between them.
    borrowed-flow-what-it-does.png  solution 3, which is four boxes long, and
                                    the chart is short on purpose.

Every number written on these charts comes out of
``code/src/08_seeing-the-glasses/``, and the constant it came from is named in
the comment beside it below.

The layout works in one unit of height per line of text, so a box's height is
its line count plus padding and no text can spill out of it. The figure's height
in inches follows from the number of units the content uses, which is what keeps
a figure from being much larger than what it holds.

``_audit`` then measures the drawn figure and prints anything a glance can miss:
words outside the box they belong to, two pieces of text sharing a patch of page,
two boxes on top of each other, and a caption landing on a box. It prints nothing
now, and a chart should not be committed while it prints anything.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_solution_flows_a.py
"""

from __future__ import annotations

import matplotlib.colors as mcolors
import numpy as np
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
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Read out of the code rather than from the prose. The comment after each one
# says which constant it is, so a reader can check it in one step.

CLEARANCE_MM = 5          # STANDING_CLEARANCE in work_cell/glasses/detect.py
GROUPING_MM = 25          # GROUPING in 01-rules-on-the-table/find.py
MIN_POINTS = 100          # MIN_POINTS in 01-rules-on-the-table/find.py
RIM_LOW_MM = 65           # KIND_RANGES["tapered_glass"]["rim_diameter"], low end
RIM_HIGH_MM = 105         # the same, high end, in work_cell/glasses/shapes.py
CENTRES_MM = 150          # MIN_SEPARATION in work_cell/glasses/spawn.py
STRIP_MM = CENTRES_MM - RIM_HIGH_MM   # 45 mm, and spawn.py's own comment says so

MIN_VOTES = 30            # MIN_VOTES in 02-train-from-scratch/pipeline.py
SHRINK = 2                # SHRINK in 02-train-from-scratch/models.py

MODEL_FILE = "yolo26n-seg.pt"         # MODEL in 03-yolo-zero-shot/yolo_zero_shot.py
KEPT_NAMES = "wine glass, cup, bowl, vase or bottle"   # VESSELS + NEIGHBOURS in
                                      # 03-yolo-zero-shot/drinking_vessels.py
CONFIDENCE_BAR = 0.25     # CONFIDENCE_BAR_SET_BY_HAND in yolo_zero_shot.py


# --------------------------------------------------------------------- the look
#
# One unit of height is one line of text. A box of n lines is therefore n units
# tall plus padding, and the figure is as many inches tall as the content needs.

_PAIRS: list[tuple] = []     # (words, the box they belong in), for the audit
_SOLID: list = []            # shapes that must not land on each other
_FREE: list = []             # captions that must not land on a shape

UNIT_IN = 1.45 * NOTE_SIZE / 72.0     # inches per line, at the body text size
AXES_FRAC = 0.90                      # of the figure's height, leaving the title
BOX_PAD = 0.3                         # the rounded box's own padding, in units
BOX_SLACK = 0.7                       # spare height inside a box, in units
GAP = 1.5                             # between one box's edge and the next


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill.

    Blending with white rather than setting an alpha, because these fills sit on
    top of each other and a stack of transparent fills darkens.
    """
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


def _figure(width_in: float, units: float):
    """A figure whose height comes from how many lines of text it has to hold."""
    height_in = units * UNIT_IN / AXES_FRAC
    figure, axis = new(width_in, height_in)
    figure.subplots_adjust(left=0.012, right=0.988, bottom=0.015, top=0.015 + AXES_FRAC)
    bare(axis)
    axis.set_xlim(0, 100)
    axis.set_ylim(0, units)
    _PAIRS.clear()
    _SOLID.clear()
    _FREE.clear()
    # How much taller than wide a unit is, so a circle can be drawn as a circle.
    aspect = (0.976 * width_in / 100.0) / UNIT_IN
    return figure, axis, aspect


def _height(text: str) -> float:
    """The outer height of a box holding this text, in units."""
    return text.count("\n") + 1 + BOX_SLACK + 2 * BOX_PAD


def _box(
    axis,
    x: float,
    y: float,
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
    """A rounded box with centred text, given its centre. Returns its height."""
    outer = _height(text)
    inner = outer - 2 * BOX_PAD
    patch = FancyBboxPatch(
        (x - width / 2.0, y - inner / 2.0),
        width,
        inner,
        boxstyle=f"round,pad={BOX_PAD},rounding_size=0.9",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
        zorder=3,
    )
    axis.add_patch(patch)
    words = axis.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=ink,
        weight=weight,
        linespacing=1.45,
        zorder=5,
    )
    _PAIRS.append((words, patch))
    _SOLID.append(patch)
    return outer


def _arrow(axis, start, end, *, colour=INK, lw=1.4, dashed=False) -> None:
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


def _note(axis, x, y, text, *, colour=MUTED, size=NOTE_SIZE, ha="left", va="center",
          weight="normal") -> None:
    _FREE.append(
        axis.text(
            x,
            y,
            text,
            ha=ha,
            va=va,
            fontsize=size,
            color=colour,
            weight=weight,
            linespacing=1.45,
            zorder=7,
        )
    )


def _band(axis, x, y, width, height, colour, label) -> None:
    """A lane of the chart, with its name down the left of it."""
    axis.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor=_tint(colour, 0.90),
            edgecolor=colour,
            linewidth=1.0,
            zorder=1,
        )
    )
    axis.text(
        x + 3.2,
        y + height / 2.0,
        label,
        rotation=90,
        ha="center",
        va="center",
        fontsize=LABEL_SIZE,
        color=colour if colour != MUTED else INK,
        weight="bold",
        zorder=2,
    )


def _title(axis, text) -> None:
    axis.set_title(text, fontsize=TITLE_SIZE, color=INK, pad=10)



def _audit(figure, name: str) -> None:
    """Measure the drawn figure, and say what a glance at the PNG can miss.

    Four faults are looked for: words outside the box they belong to, two pieces
    of text sharing the same patch of page, two boxes on top of each other, and a
    caption landing on a box. Everything is measured on the rendered artists, and
    the complaints are printed rather than raised, so the picture is still written
    and can be looked at beside them.
    """
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    faults = []

    def first_line(label, limit=46):
        return label.get_text().splitlines()[0][:limit]

    for words, patch in _PAIRS:
        inside = words.get_window_extent(renderer)
        room = patch.get_window_extent(renderer)
        if (inside.x0 < room.x0 - 0.5 or inside.x1 > room.x1 + 0.5
                or inside.y0 < room.y0 - 0.5 or inside.y1 > room.y1 + 0.5):
            faults.append(f"  text spills its box: {first_line(words)!r}")

    def clashes(a, b, room=1.0):
        return (min(a.x1, b.x1) - max(a.x0, b.x0) > room
                and min(a.y1, b.y1) - max(a.y0, b.y0) > room)

    drawn = [(t, t.get_window_extent(renderer))
             for t in figure.axes[0].texts if t.get_text().strip()]
    for index, (one, a) in enumerate(drawn):
        for two, b in drawn[index + 1:]:
            if clashes(a, b):
                faults.append(
                    f"  text over text: {first_line(one, 32)!r} and {first_line(two, 32)!r}"
                )

    shapes = [(patch, patch.get_window_extent(renderer)) for patch in _SOLID]
    owner = {id(patch): words for words, patch in _PAIRS}
    for index, (one, a) in enumerate(shapes):
        for two, b in shapes[index + 1:]:
            if clashes(a, b, room=2.0):
                here, there = owner.get(id(one)), owner.get(id(two))
                faults.append(
                    "  box over box: "
                    f"{(first_line(here, 28) if here else 'a shape')!r} and "
                    f"{(first_line(there, 28) if there else 'a shape')!r}"
                )
    for label in _FREE:
        a = label.get_window_extent(renderer)
        for _patch, b in shapes:
            if clashes(a, b, room=2.0):
                faults.append(f"  caption over a box: {first_line(label)!r}")
                break

    if faults:
        print(f"{name}: {len(faults)} thing(s) to fix")
        print("\n".join(faults))


class Flow:
    """A chain of boxes running down the chart, with the arrows between them.

    Boxes are placed from the top down, each one as tall as its own text, and the
    arrow into a box starts exactly on the box above it. ``extents`` keeps every
    box's top and bottom so that a lane can be drawn around a run of them.
    """

    def __init__(self, axis, top: float, centre: float, width: float, chain_x: float):
        self.axis = axis
        self.y = top
        self.centre = centre
        self.width = width
        self.chain_x = chain_x
        self.extents: list[tuple[float, float]] = []

    def box(self, text: str, *, width: float | None = None, arrow=True, **kw) -> tuple[float, float]:
        width = self.width if width is None else width
        outer = _height(text)
        middle = self.y - outer / 2.0
        if arrow and self.extents:
            _arrow(self.axis, (self.chain_x, self.extents[-1][1]), (self.chain_x, self.y))
        _box(self.axis, self.centre, middle, width, text, **kw)
        top, bottom = self.y, self.y - outer
        self.extents.append((top, bottom))
        self.y = bottom - GAP
        return top, bottom

    def skip(self, units: float) -> None:
        self.y -= units


# --------------------------------------------------------------------------- #
# 1. solution 1, the whole method as one chain
# --------------------------------------------------------------------------- #


def rules_what_it_does() -> None:
    """Every step of rules on the table, in the document's own words.

    The lanes are the point of the drawing as much as the sequence is. The method
    starts in the picture, moves into the room, does its real work on the table,
    and only comes back to the picture to hand the pixels over. A reader who sees
    that has the solution's one idea, which is that the question stops being
    about the picture and becomes a question about distance on the table.
    """
    figure, axis, _ = _figure(10.6, 46.0)
    flow = Flow(axis, 44.0, 54.0, 76.0, 27.0)

    flow.box(
        "From each picture, keep the pixels whose points stand more than "
        f"{CLEARANCE_MM} mm above the known\n"
        "table top, and drop the pixels that came back with no depth reading at all.",
    )
    flow.box(
        "Turn each kept pixel into a point in the room: the pixel's offsets from the middle of\n"
        "the picture give the direction the camera was looking, the depth reading gives how far\n"
        "along that direction to travel, and the camera's own pose says where the ray begins.",
    )
    flow.box(
        "Drop the height, so each glass becomes a flat patch of dots on the table. The gap\n"
        "inside one glass closes to nothing, and the strip of bare table between two glasses\n"
        "stays exactly as wide as it was.",
    )
    flow.box(
        "Join dots lying within one chosen distance of each other into groups, and keep joining\n"
        f"until nothing new joins. That distance is {GROUPING_MM} mm, and it is the method's only setting.",
    )
    flow.box(
        "Fit a circle to each group's outer dots and check its width against the range this kind\n"
        f"of glass allows, which is {RIM_LOW_MM} to {RIM_HIGH_MM} mm across the rim for the tapered glass. A group\n"
        "too wide to be one glass is split in two, and each part is asked the same question again.",
    )
    flow.box(
        "Hand back, for each surviving group, the picture pixels its dots came from.",
    )
    flow.box(
        "Those pixels are the masks, and the mask is the whole contribution.",
        edge=GLASS, face=_tint(GLASS, 0.72), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    # the lanes, drawn around the boxes now that their extents are known
    ends = flow.extents
    for first, last, colour, label in (
        (0, 0, MUTED, "in the\npicture"),
        (1, 1, GLASS, "in the\nroom"),
        (2, 4, GOOD, "on the table"),
        (5, 6, MUTED, "back in the\npicture"),
    ):
        top = ends[first][0] + 0.7
        bottom = ends[last][1] - 0.7
        _band(axis, 7.0, bottom, 94.0, top - bottom, colour, label)

    _note(
        axis, 54.0, flow.y - 1.4,
        "The masks are a consequence of the grouping on the table rather than the thing the method\n"
        "produces directly. Nothing here draws an outline or measures a mask: the dots decide which\n"
        "group they join, and the picture pixels behind them follow.",
        colour=INK, ha="center", va="top",
    )
    _note(
        axis, 54.0, flow.y - 6.0,
        "Not one number in this chain was fitted to anything. There is no model, no weights file and no\n"
        f"training data. The table top, the {RIM_LOW_MM} to {RIM_HIGH_MM} mm the width is checked against, and the "
        f"{GROUPING_MM} mm the\n"
        "grouping uses were all known before the run started.",
        colour=GOOD, ha="center", va="top", weight="bold",
    )

    _title(axis, "Rules on the table: what the method does, from a picture to the masks")
    _audit(figure, "rules-flow-what-it-does.png")
    save(figure, "rules-flow-what-it-does.png")


# --------------------------------------------------------------------------- #
# 2. solution 1, what one group has to pass
# --------------------------------------------------------------------------- #


def rules_each_group() -> None:
    """The two questions asked of every group, and the three ways out.

    The setting is drawn at the top rather than at the bottom, because the
    grouping distance is what made the group in the first place: it enters the
    chart where the group enters it. The window it sits in is drawn as a measured
    line, since the whole claim about this method is that both ends of that
    window were known before the run started.
    """
    figure, axis, _ = _figure(12.4, 59.5)

    # ------------------------------------------- the one setting, and its window
    _note(
        axis, 50.0, 58.0,
        "The one setting: how far apart two dots may be and still be joined into one group",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", va="top", weight="bold",
    )

    bar_left, bar_right, bar_y, bar_h = 12.0, 90.0, 52.5, 1.6
    span_mm = 60.0

    def at(mm: float) -> float:
        return bar_left + (bar_right - bar_left) * mm / span_mm

    low_mm = 7.0   # the dot mesh's widest stretch, drawn rather than quoted
    axis.add_patch(
        Rectangle((bar_left, bar_y), at(low_mm) - bar_left, bar_h,
                  facecolor=_tint(WARN, 0.80), edgecolor=WARN, lw=1.0, zorder=3)
    )
    axis.add_patch(
        Rectangle((at(low_mm), bar_y), at(STRIP_MM) - at(low_mm), bar_h,
                  facecolor=_tint(GOOD, 0.62), edgecolor=GOOD, lw=1.2, zorder=3)
    )
    axis.add_patch(
        Rectangle((at(STRIP_MM), bar_y), bar_right - at(STRIP_MM), bar_h,
                  facecolor=_tint(WARN, 0.80), edgecolor=WARN, lw=1.0, zorder=3)
    )
    _note(axis, (bar_left + at(low_mm)) / 2.0, bar_y + bar_h + 0.9, "too small",
          colour=WARN, ha="center", va="bottom", weight="bold")
    _note(axis, (at(low_mm) + at(STRIP_MM)) / 2.0, bar_y + bar_h + 0.9,
          "any distance in here holds one glass together and keeps its neighbour out",
          colour=GOOD, ha="center", va="bottom", weight="bold")
    _note(axis, (at(STRIP_MM) + bar_right) / 2.0, bar_y + bar_h + 0.9, "too large",
          colour=WARN, ha="center", va="bottom", weight="bold")

    axis.plot([at(GROUPING_MM), at(GROUPING_MM)], [bar_y - 1.1, bar_y + bar_h + 0.2],
              color=INK, lw=1.6, zorder=6)
    _note(axis, at(GROUPING_MM), bar_y - 1.4, f"{GROUPING_MM} mm, the value the code uses",
          colour=INK, ha="center", va="top", weight="bold")

    _note(
        axis, bar_left, bar_y - 4.4,
        "The lower end is the widest stretch between two\n"
        "neighbouring dots on one glass. Below it the chain\n"
        "breaks in the middle of a single glass, and one glass\n"
        "comes back as two groups.",
        colour=INK, ha="left", va="top",
    )
    _note(
        axis, bar_right, bar_y - 4.4,
        f"The upper end is {STRIP_MM} mm, the narrowest strip of bare table\n"
        f"two glasses can leave: {CENTRES_MM} mm between centres, less half\n"
        "of each of the two widest rims this kind allows, which are\n"
        f"{RIM_HIGH_MM} mm. Above it the chain hops the strip and two glasses\n"
        "come back as one group.",
        colour=INK, ha="right", va="top",
    )

    # ------------------------------------------------------------- the main chain
    centre, width, chain_x = 50.0, 58.0, 30.0
    left_edge = centre - width / 2.0 - BOX_PAD
    right_edge = centre + width / 2.0 + BOX_PAD

    _arrow(axis, (chain_x, 42.1), (chain_x, 40.0))
    _note(axis, chain_x + 1.4, 41.1,
          "every dot in a group is within this distance of another dot in it",
          colour=MUTED, va="center")

    flow = Flow(axis, 40.0, centre, width, chain_x)
    flow.box(
        "One group of dots on the table",
        arrow=False, edge=GLASS, face=_tint(GLASS, 0.76), size=LABEL_SIZE, lw=1.6,
        weight="bold",
    )
    flow.box(
        f"Does the group hold at least {MIN_POINTS} dots that have a depth reading?",
        weight="bold",
    )
    q1_top, q1_bottom = flow.extents[-1]
    q1_middle = (q1_top + q1_bottom) / 2.0

    flow.box(
        "Fit a circle to the dots on the outside of the patch. Multiplying the circle's equation out makes\n"
        "the fit linear, so it has a direct solution: no starting guess and nothing to iterate. The width it\n"
        "returns decides this check and nothing else, because the width that goes into the record is\n"
        "measured by the examiner from the mask pixels, the same way for every solution.",
    )
    flow.box(
        "Is that fitted width inside the range this kind of glass allows,\n"
        f"which is {RIM_LOW_MM} to {RIM_HIGH_MM} mm across the rim for the tapered glass?",
        weight="bold",
    )
    q2_bottom = flow.extents[-1][1]

    # ------------------------------------------------------- the three ways out
    out_top = q2_bottom - 5.0
    out_width = 28.0
    refused_x, reported_x, split_x = 20.0, 50.0, 80.0

    refused = (
        "Refused, and handed over whole.\n"
        "\n"
        "Either too few dots with a depth reading to\n"
        "place the group at all, or a width narrower\n"
        "than any glass of this kind with the whole of\n"
        "the group inside the frame.\n"
        "\n"
        "Splitting cannot repair a width that is too\n"
        "narrow, because both halves of a footprint\n"
        "are narrower still. Which side of the range\n"
        "the group failed is reported, rather than the\n"
        "count being guessed at."
    )
    reported = (
        "Reported.\n"
        "\n"
        "The group is one glass, and the picture\n"
        "pixels its dots came from are that glass's\n"
        "mask.\n"
        "\n"
        "That mask is the whole of what this solution\n"
        "hands over."
    )
    split = (
        "Split in two, and asked again.\n"
        "\n"
        "Two seeds at the ends of the group's longest\n"
        "direction, each dot to the nearer seed, each\n"
        "seed to the middle of the dots it was given,\n"
        "until nothing moves.\n"
        "\n"
        "Both parts go back through the same two\n"
        "questions, so a part still too wide is split\n"
        "again. Nothing counts the rounds down: each\n"
        "part has fewer dots than the part it came\n"
        "from, so the splitting runs out on its own."
    )
    heights = [_height(text) for text in (refused, reported, split)]
    for x, text, height, edge, face in (
        (refused_x, refused, heights[0], WARN, _tint(WARN, 0.86)),
        (reported_x, reported, heights[1], GOOD, _tint(GOOD, 0.80)),
        (split_x, split, heights[2], GLASS, _tint(GLASS, 0.80)),
    ):
        _box(axis, x, out_top - height / 2.0, out_width, text, edge=edge, face=face, lw=1.8)

    _arrow(axis, (centre - 14.0, q2_bottom), (refused_x + 4.0, out_top), colour=WARN)
    _arrow(axis, (centre, q2_bottom), (reported_x, out_top), colour=GOOD)
    _arrow(axis, (centre + 14.0, q2_bottom), (split_x - 4.0, out_top), colour=GLASS)
    _note(axis, 26.0, q2_bottom - 2.4, "too narrow", colour=WARN, ha="right", weight="bold")
    _note(axis, 52.0, q2_bottom - 2.4, "inside the range", colour=GOOD, ha="left", weight="bold")
    _note(axis, 78.0, q2_bottom - 2.4, "too wide", colour=GLASS, ha="left", weight="bold")

    # the "no" branch from the first question, down the left margin
    margin_x, entry_y = 3.5, out_top - heights[0] / 2.0
    axis.plot([left_edge, margin_x], [q1_middle, q1_middle], color=WARN, lw=1.3, zorder=6)
    axis.plot([margin_x, margin_x], [q1_middle, entry_y], color=WARN, lw=1.3, zorder=6)
    _arrow(axis, (margin_x, entry_y), (refused_x - out_width / 2.0 - BOX_PAD, entry_y), colour=WARN)
    _note(axis, margin_x + 1.4, q1_middle + 0.9, "no", colour=WARN, va="bottom", weight="bold")

    # the loop back, because a part is asked the same two questions as a group
    loop_x = 96.5
    split_middle = out_top - heights[2] / 2.0
    axis.plot([split_x + out_width / 2.0 + BOX_PAD, loop_x], [split_middle, split_middle],
              color=GLASS, lw=1.3, zorder=6)
    axis.plot([loop_x, loop_x], [split_middle, q1_middle], color=GLASS, lw=1.3, zorder=6)
    _arrow(axis, (loop_x, q1_middle), (right_edge, q1_middle), colour=GLASS)
    _note(axis, loop_x, q1_middle + 0.9, "each part, as its own group",
          colour=GLASS, ha="right", va="bottom", weight="bold")

    _note(
        axis, 50.0, 1.4,
        "Three outcomes and no fourth: a report, a split, or a refusal. Both questions are arithmetic over quantities known\n"
        "before the run started, so a refusal can be explained and a split can be justified.",
        colour=INK, ha="center", va="bottom",
    )

    _title(axis, "Rules on the table: what every group has to pass before it is reported")
    _audit(figure, "rules-flow-each-group.png")
    save(figure, "rules-flow-each-group.png")


# --------------------------------------------------------------------------- #
# 3. solution 2, one network, two heads and the votes
# --------------------------------------------------------------------------- #


def network_what_it_does() -> None:
    """The chain from a picture to the masks, and the blob coming apart.

    The chain alone would leave the solution's whole claim unsaid, so the lower
    half of the chart draws it: one connected patch of glass pixels, the arrows
    inside it pointing two different ways, and the two piles those arrows make.
    Nothing in that drawing is a cut, because nothing in the method cuts.
    """
    figure, axis, aspect = _figure(11.6, 63.0)

    flow = Flow(axis, 61.0, 50.0, 80.0, 22.0)
    flow.box(
        "A survey picture from the top and its depth reading, turned into something like a height above the\n"
        "table, with two further channels saying where in the frame each pixel sits. A camera looking straight\n"
        f"down throws a glass's outline outwards, so where a pixel sits is the one fact it cannot see. All of it\n"
        f"goes in at half size, which is {SHRINK * SHRINK} times quicker to train on and still leaves a glass many pixels across.",
    )
    flow.box(
        "One network: a down path that halves the picture while doubling the channels, an up path that enlarges\n"
        "it back, and the copies set aside before each halving carried across so that fine detail survives the\n"
        "journey. Both heads sit on the end of that one up path, which is why they are one network and not two.",
    )
    network_bottom = flow.extents[-1][1]

    # the two heads, side by side under the one network
    left_x, right_x, head_width = 28.0, 72.0, 40.0
    head_left = (
        "The first head: one number per pixel,\n"
        "how sure the network is that the pixel is\n"
        "glass. Squashed into nought to one and\n"
        "cut at a threshold, that is the mask of\n"
        "glass pixels."
    )
    head_right = (
        "The second head: two numbers per glass\n"
        "pixel, the parts of a short arrow towards\n"
        "the middle of that pixel's own glass. It is\n"
        "asked only of the glass pixels, because a\n"
        "table pixel has no glass to point at."
    )
    head_height = max(_height(head_left), _height(head_right))
    head_middle = network_bottom - GAP - head_height / 2.0
    _box(axis, left_x, head_middle, head_width, head_left, edge=GLASS,
         face=_tint(GLASS, 0.82), lw=1.6)
    _box(axis, right_x, head_middle, head_width, head_right, edge=GLASS,
         face=_tint(GLASS, 0.82), lw=1.6)
    _arrow(axis, (left_x, network_bottom), (left_x, head_middle + head_height / 2.0),
           colour=GLASS)
    _arrow(axis, (right_x, network_bottom), (right_x, head_middle + head_height / 2.0),
           colour=GLASS)

    flow.y = head_middle - head_height / 2.0 - GAP
    flow.extents.append((head_middle + head_height / 2.0, head_middle - head_height / 2.0))

    vote_top = flow.y
    _arrow(axis, (left_x, head_middle - head_height / 2.0), (left_x, vote_top), colour=GLASS)
    _arrow(axis, (right_x, head_middle - head_height / 2.0), (right_x, vote_top), colour=GLASS)

    flow.box(
        "Each glass pixel adds its own arrow to its own position and casts one vote at the place the arrow points.",
        arrow=False,
    )
    flow.box(
        "The votes are added into a tally the size of the picture and smoothed a little, so that votes landing on\n"
        "neighbouring places reinforce each other. Then the largest place in the tally is taken as one glass's\n"
        f"middle, the votes around it are set aside, and the next largest is taken, until no place has {MIN_VOTES} votes left.",
    )
    flow.box(
        "The pixels that voted into one peak are one glass's mask.",
        edge=GLASS, face=_tint(GLASS, 0.70), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    # ------------------------------------------------- what the votes buy, drawn
    rule_y = flow.y - 0.4
    axis.plot([4, 96], [rule_y, rule_y], color=MUTED, lw=0.9, ls=(0, (5, 4)), zorder=1)

    _note(
        axis, 50.0, rule_y - 1.3,
        "Why the arrow is asked for instead of a boundary",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", va="top", weight="bold",
    )

    # One unit across the chart is not one unit up it, so a circle of radius r in
    # units across needs a radius of r * aspect in units up, and a distance has to
    # be measured with the upward part divided by the same number.
    def across(offset):
        return np.array([offset[0], offset[1] / aspect])

    sketch_top = rule_y - 3.4
    radius = 5.5
    a_centre = np.array([21.0, sketch_top - 7.0])
    b_centre = np.array([28.0, sketch_top - 9.0])

    for centre in (a_centre, b_centre):
        axis.add_patch(
            Ellipse(tuple(centre), 2 * radius, 2 * radius * aspect,
                    facecolor=_tint(GLASS, 0.74), edgecolor=GLASS, lw=1.3, zorder=3)
        )

    rng = np.random.default_rng(7)
    for _ in range(320):
        point = np.array([rng.uniform(14.0, 35.0), rng.uniform(sketch_top - 15.0, sketch_top - 1.0)])
        in_a = np.hypot(*across(point - a_centre)) <= radius * 0.93
        in_b = np.hypot(*across(point - b_centre)) <= radius * 0.93
        if not (in_a or in_b):
            continue
        # The overlap belongs to the glass whose outline was thrown over the
        # other, which here is A, so its pixels are the ones that point at A.
        target = a_centre if in_a else b_centre
        step = (target - point) * 0.5
        if np.hypot(*across(step)) < 0.6:
            continue
        _arrow(axis, tuple(point), tuple(point + step),
               colour=GOOD if in_a else WARN, lw=0.7)

    for centre, colour in ((a_centre, GOOD), (b_centre, WARN)):
        axis.plot(*centre, marker="o", ms=6.0, color=colour, zorder=8)

    _note(axis, 4.0, sketch_top, "One connected patch of glass pixels,\nwith no gap anywhere in it",
          colour=INK, ha="left", va="top", weight="bold")
    _note(axis, 4.0, sketch_top - 15.0,
          "The pixels along the seam are no different from any other\n"
          "pixel. What changes across the seam is the direction the\n"
          "arrows point, so nothing had to find the seam.",
          colour=INK, ha="left", va="top")

    # the two piles of votes, to the right
    pile_a = a_centre + np.array([45.0, 0.0])
    pile_b = b_centre + np.array([45.0, 0.0])
    for centre, colour in ((pile_a, GOOD), (pile_b, WARN)):
        cloud = rng.normal(0.0, 1.0, size=(110, 2)) * np.array([1.1, 1.1 * aspect])
        axis.plot(centre[0] + cloud[:, 0], centre[1] + cloud[:, 1], marker="o", ms=1.8,
                  ls="none", color=colour, alpha=0.75, zorder=5)
        axis.plot(*centre, marker="o", ms=6.0, color=colour, zorder=8)
    _note(axis, 58.0, sketch_top, "Two piles of votes, because each glass's\npixels point at their own middle",
          colour=INK, ha="left", va="top", weight="bold")
    _note(axis, 58.0, sketch_top - 15.0,
          "Counting glasses is counting piles, and nothing had to be\n"
          "told how many piles to expect. A handful of arrows pointing\n"
          "the wrong way are outvoted rather than fatal.",
          colour=INK, ha="left", va="top")

    _arrow(axis, (40.0, (a_centre[1] + b_centre[1]) / 2.0),
           (52.0, (a_centre[1] + b_centre[1]) / 2.0), colour=INK, lw=1.6)

    _note(
        axis, 50.0, 1.4,
        "A connected blob comes apart into separate glasses without any rule for cutting it having been written down.\n"
        "Nothing has to find a boundary, so nothing can get a boundary wrong.",
        colour=GOOD, ha="center", va="bottom", weight="bold",
    )

    _title(axis, "A network trained from scratch: one network, two heads, and the votes")
    _audit(figure, "network-flow-what-it-does.png")
    save(figure, "network-flow-what-it-does.png")


# --------------------------------------------------------------------------- #
# 4. solution 2, the two places the labels come from
# --------------------------------------------------------------------------- #


def network_labels() -> None:
    """The two ways, side by side, because only the labels differ.

    Drawing them one after the other would suggest a sequence, and drawing only
    one of them would hide the comparison the document is really for. So the
    chart puts the shared method in one box across the top, the two sources of
    labels in two columns under it, and the one difference that outlives this
    problem at the bottom of the second column.
    """
    figure, axis, _ = _figure(12.4, 49.5)

    _box(
        axis, 50.0, 46.2, 92.0,
        "The network, the two heads, the votes and the checks are the same in both columns.\n"
        "Only the source of the training labels changes, which is why these are two ways of one solution.",
        edge=INK, face=_tint(MUTED, 0.90), size=LABEL_SIZE, lw=1.6, weight="bold",
    )

    left_x, right_x, width = 26.0, 74.0, 44.0
    chain_left, chain_right = 8.0, 56.0

    _note(axis, left_x, 42.4, "The first way: labels from the answer key",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", va="top", weight="bold")
    _note(axis, right_x, 42.4, "The second way: labels from the arm's own movement",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", va="top", weight="bold")

    first = Flow(axis, 40.8, left_x, width, chain_left)
    first.box(
        "The examiner rendered the picture itself, so\n"
        "beside the grey picture and the depth reading\n"
        "it has an id image: at every pixel, which glass\n"
        "that pixel shows, or nothing.",
    )
    first.box(
        "The first head's label is the id image with the\n"
        "identities forgotten. A pixel is glass if the id\n"
        "image names any glass there, with nothing to\n"
        "judge and nothing to draw.",
    )
    first.box(
        "The second head's label is a subtraction: that\n"
        "glass's middle minus the pixel's own position.\n"
        "The examiner knows both ends exactly, because\n"
        "it put the glass there.",
    )
    first.box(
        "What it costs: render time, and nothing else.\n"
        "There is no annotator, so no annotator's budget\n"
        "and no annotator's mistakes. Both heads' labels\n"
        "fall out of the id image by arithmetic.",
        edge=MUTED, face=_tint(MUTED, 0.88),
    )
    first.box(
        "What it depends on: the simulator's own record.\n"
        "A real camera on a real table has no id image,\n"
        "so the day this cell meets real glasses this way\n"
        "has to be labelled again by somebody drawing\n"
        "round things.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6,
    )

    second = Flow(axis, 40.8, right_x, width, chain_right)
    second.box(
        "The camera slides a known distance between\n"
        "two pictures of a scene that stood still. The arm\n"
        "commanded that slide and reads it back from its\n"
        "own joint encoders, so it is measured and not\n"
        "estimated from the pictures.",
    )
    second.box(
        "Points on one surface shift across the picture\n"
        "together, and points on a surface at a different\n"
        "distance shift by a different amount, because the\n"
        "shift is the slide divided by the depth.",
    )
    second.box(
        "Two pixels whose shifts agree to within the noise\n"
        "belong together and two whose shifts clearly\n"
        "differ do not. That agreement is the label, and\n"
        "training pulls the pixels that belong together\n"
        "into one neighbourhood of a map it draws itself.",
    )
    second.box(
        "What it costs: arm time rather than render time,\n"
        "because collecting a label means moving the arm.\n"
        "The labels are weakest from the top, where two\n"
        "rims sit at almost the same distance, and the top\n"
        "is where the merge happens.",
        edge=MUTED, face=_tint(MUTED, 0.88),
    )
    second.box(
        "What it buys: this is the only supervision a real\n"
        "arm would also have. A real arm has joint\n"
        "encoders and a wrist camera, and that is all this\n"
        "way needs, so this is the one way that would not\n"
        "have to be labelled again outside the simulator.",
        edge=GOOD, face=_tint(GOOD, 0.80), lw=1.8, weight="bold",
    )

    _note(
        axis, 50.0, 1.4,
        "So the first way is the one to build for this problem, and the second is the one to reach for when the cell leaves the simulator.",
        colour=INK, ha="center", va="bottom", weight="bold",
    )

    _title(axis, "A network trained from scratch: the two places the training labels can come from")
    _audit(figure, "network-flow-labels.png")
    save(figure, "network-flow-labels.png")


# --------------------------------------------------------------------------- #
# 5. solution 3, the shortest chain in the book
# --------------------------------------------------------------------------- #


def borrowed_what_it_does() -> None:
    """Four boxes, and the chart is short because the method is short.

    The length of this picture is part of what it says. Everything that makes
    the other five solutions long — a training set, a training run, a weights
    file to keep in step with the cell — is missing here, so the chart is drawn
    at the height its own content needs and no more.
    """
    figure, axis, _ = _figure(10.4, 36.5)

    flow = Flow(axis, 34.4, 50.0, 78.0, 24.0)
    flow.box(
        "The grey picture, shaded from the depth reading, goes to the downloaded model unchanged.\n"
        f"The weights are Ultralytics YOLO26-seg at the small end of the family, the file {MODEL_FILE},\n"
        "and they fetch themselves the first time the model is used.",
    )
    flow.box(
        "The model returns, for each object it believes it found, four things together: a box around the\n"
        "object, a name from its own fixed list of everyday categories, a number saying how sure it is,\n"
        f"and an outline marking which pixels inside the box are that object. Outlines scoring below a\n"
        f"bar set by hand at {CONFIDENCE_BAR} are never built.",
    )
    flow.box(
        f"Keep the outlines whose name is a drinking vessel — {KEPT_NAMES} —\n"
        "and drop every other object the model named. The filter is generous on purpose, because the\n"
        "boundary the model draws between its own categories was never meant to tell this cell's\n"
        "kinds of glass apart.",
        edge=GLASS, face=_tint(GLASS, 0.84), lw=1.6,
    )
    flow.box(
        "Discard the names. The kept outlines are the masks.",
        edge=GLASS, face=_tint(GLASS, 0.70), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    _note(
        axis, 50.0, flow.y - 1.2,
        "Nothing in this solution was fitted in this cell. Every number inside the model came from somebody\n"
        f"else's photographs of everyday scenes, and the one number beside it, the {CONFIDENCE_BAR} bar, was set by hand\n"
        "and claims nothing about how often an outline above it is really a glass.",
        colour=GOOD, ha="center", va="top", weight="bold",
    )
    _note(
        axis, 50.0, flow.y - 5.8,
        "The name is a filter and never an answer. A borrowed category carries an implied size with it, because the\n"
        "model's idea of a cup was formed from photographs of real cups at the sizes real cups come in, so a name\n"
        "that travelled any further would bring a belief about how big a glass is into a cell where no glass's size is\n"
        "written down. Dropping it immediately after the filter is what stops that.",
        colour=WARN, ha="center", va="top",
    )

    _title(axis, "A borrowed model as it downloads: the whole method, from the picture to the masks")
    _audit(figure, "borrowed-flow-what-it-does.png")
    save(figure, "borrowed-flow-what-it-does.png")


def main() -> None:
    rules_what_it_does()
    rules_each_group()
    network_what_it_does()
    network_labels()
    borrowed_what_it_does()


if __name__ == "__main__":
    main()
