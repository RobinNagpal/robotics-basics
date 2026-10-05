"""The three flow charts for the test bench document.

The document beside these pictures argues one thing above all: the bench owns
every step of a run except one, and the one step it does not own is the mask. A
reader who believes that can read a difference between two scorecards as a
difference between two masks, and a reader who does not cannot read the results
at all. These three pictures are drawn to make that argument visible.

    03-what-the-bench-does.png   the whole run, with the bench's many steps in
                                 one band and the solution's single step in
                                 another, and both hand-over points named.
    03-what-must-come-back.png   the record per glass, with the fields the
                                 solution supplies separated from the fields
                                 the bench computes, and the two honest
                                 statements that come beside the records.
    03-the-floor.png             the solution's masks and the bench's own id
                                 masks through the same arithmetic, and the
                                 trap of a mask that asserts pixels.

Every number written into these pictures comes out of
``code/src/08_seeing-the-glasses/``:

* the three stations and the survey height from ``bench/data.py``, which gets
  them from ``work_cell/arm/dimensions.py``;
* the five counts from ``FIND`` in ``bench/marking.py``;
* ``SPREAD = 95`` from ``bench/masks_to_glasses.py``;
* the floor itself, and what naming the asserted pixels is worth, from
  ``bench/results-floor.json`` and ``bench/results-floor-crowded.json``.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_bench_flows.py
"""

from __future__ import annotations

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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Read out of the code rather than typed from memory. The comment after each one
# says where it came from, so that a reader can check it in one step.

STATION_X = 0.48                       # m; bench/data.stations()
STATION_Y = (-0.353, -0.260, -0.167)   # m; the same, rounded to the millimetre
SURVEY_MM = 450                        # mm; SURVEY_HEIGHT in arm/dimensions.py
SPREAD = 95                            # bench/masks_to_glasses.SPREAD
COUNTS = "found, missed, merged, split and false"   # bench/marking.FIND

# bench/results-floor.json, "exact visible masks" on the spawned layouts.
FLOOR_GLASSES = 100
FLOOR_MEDIAN_MM = 6.3
FLOOR_WORST_MM = 46.5

# bench/results-floor-crowded.json, "one glass at a time".
HIDDEN_GLASSES = 133
NAMED_MM = 12.2
FED_IN_MM = 46.1


def _minus(value: float) -> str:
    """A negative number written with a proper minus sign rather than a hyphen."""
    return f"{value:.3f}".replace("-", "−")


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill.

    Blending with white rather than setting an alpha, because these fills sit
    on top of each other and a stack of transparent fills darkens.
    """
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


def _band(axis, x, y, width, height, colour, label) -> None:
    """A lane of the chart, with its owner's name down the left of it."""
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
        x + 4.0,
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


def _box(
    axis,
    x,
    y,
    width,
    height,
    text,
    *,
    edge=INK,
    face=PAPER,
    size=NOTE_SIZE,
    ink=INK,
    weight="normal",
    lw=1.2,
) -> None:
    """A rounded box with centred text, given its centre."""
    axis.add_patch(
        FancyBboxPatch(
            (x - width / 2.0, y - height / 2.0),
            width,
            height,
            boxstyle="round,pad=0.4,rounding_size=1.2",
            linewidth=lw,
            edgecolor=edge,
            facecolor=face,
            zorder=3,
        )
    )
    axis.text(
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


def _arrow(axis, start, end, *, colour=INK, lw=1.4, dashed=False) -> None:
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
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


def _panel(axis, xlim, ylim) -> None:
    bare(axis)
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)


# --------------------------------------------------------------------------- #
# 1. the whole run, and the one step of it a solution owns
# --------------------------------------------------------------------------- #


def what_the_bench_does() -> None:
    """Every step of a run, in two bands: the bench's steps, and the one step
    that is the solution's.

    The chart exists for the separation rather than for the sequence. A reader
    who counts the boxes in each band has the document's central claim: the
    examiner owns every step but one, so a difference between two scorecards is
    a difference between two sets of masks.
    """
    figure, axis = new(9.8, 12.5)
    _panel(axis, (0, 100), (-25, 102))

    chain_x = 26.0          # the flow runs down here, left of the boxes' middle
    middle, span = 50.0, 72.0

    _band(axis, 3, 69.5, 94, 29.5, MUTED, "the bench")
    _band(axis, 3, 44.5, 94, 16.0, GLASS, "the solution")
    _band(axis, 3, -19.0, 94, 54.5, MUTED, "the bench again")

    _box(
        axis, middle, 92.5, span, 10.5,
        "The bench draws an arrangement: four to six glasses of one kind, from the cell's\n"
        "own glass shapes and its own table layout. The arrangements are split into a\n"
        "training half and a test half by the number that drew them, so a method is fitted\n"
        "only below the dividing line and marked only above it.",
    )
    _box(
        axis, middle, 77.5, span, 11.0,
        "It parks the camera at three overlapping stations, "
        f"{SURVEY_MM} mm above the table and\n"
        f"looking straight down, at x = {STATION_X:.2f} m and y = "
        f"{_minus(STATION_Y[0])}, {_minus(STATION_Y[1])} and {_minus(STATION_Y[2])} m, and\n"
        "renders from each station a grey picture, a depth reading, a camera pose and\n"
        "an id image.",
    )
    _arrow(axis, (chain_x, 87.25), (chain_x, 83.0))

    _arrow(axis, (chain_x, 72.0), (chain_x, 57.5))
    _note(
        axis, 31.0, 67.0,
        "Hand-over 1. The bench gives the solution the grey picture, the\n"
        "depth reading and the camera pose, and nothing else.",
        colour=INK, weight="bold",
    )
    _note(
        axis, 31.0, 62.8,
        "The id image was rendered too. The bench keeps it, because it is\n"
        "the answer key it will mark with.",
    )

    _box(
        axis, middle, 52.5, span, 10.5,
        "The solution turns those three pictures into one mask per glass, and says\n"
        "which pixels of a mask it only asserts.\n"
        "That is the whole of what a solution contributes.",
        edge=GLASS, face=_tint(GLASS, 0.72), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    _arrow(axis, (chain_x, 47.25), (chain_x, 33.5))
    _note(
        axis, 31.0, 42.2,
        "Hand-over 2. One mask per glass comes back, with a flag saying\n"
        "whether the picture held the whole glass.",
        colour=INK, weight="bold",
    )
    _note(
        axis, 31.0, 38.0,
        "No place, no width and no pose. Those are the bench's own\n"
        "arithmetic, the same arithmetic for every solution.",
    )

    _box(
        axis, middle, 28.0, span, 11.0,
        "The bench's own shared arithmetic turns each mask into a place on the table and\n"
        "a rough width. It takes the axis from the points at the top of the glass, and the\n"
        f"width as the {SPREAD}th percentile of how far the cloud of points reaches from that\n"
        "axis. The depth reading of an asserted pixel is left out rather than guessed at.",
    )
    _arrow(axis, (chain_x, 22.5), (chain_x, 19.0))

    _box(
        axis, middle, 14.0, span, 9.5,
        "The bench asks its id image which real glass owns most of the pixels a report is\n"
        "made of, and credits the report to that glass, however far out the place it\n"
        "computed may be.",
    )
    _arrow(axis, (chain_x, 9.25), (chain_x, 5.5))

    _box(
        axis, middle, 0.0, span, 11.0,
        f"The bench counts {COUNTS}, records how far each\n"
        "reported place is from the true one, and measures how much of each real glass\n"
        "the mask covered and how much of the mask was not that glass, broken down by\n"
        "the four kinds of glass.",
    )
    _arrow(axis, (chain_x, -5.5), (chain_x, -9.5))

    _box(
        axis, middle, -14.0, span, 8.0,
        "One scorecard, marked the same way for every solution",
        size=LABEL_SIZE, weight="bold",
    )

    _note(
        axis, middle, -22.5,
        "One box in this chain belongs to a solution, so a difference between two scorecards "
        "belongs to the mask.",
        colour=INK, ha="center",
    )

    axis.set_title(
        "What the bench does, and the one step of it a solution owns",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    save(figure, "03-what-the-bench-does.png")


# --------------------------------------------------------------------------- #
# 2. what a solution has to return, and what the bench does with each piece
# --------------------------------------------------------------------------- #


def what_must_come_back() -> None:
    """The record per glass, split by who fills each field in.

    Two of the four fields in a record come from the solution and two are
    computed by the bench from the first of them. Drawing the record as four
    fields of one colour would hide the whole point, so the fields are grouped
    by their owner and the arithmetic that makes the bench's two sits between
    the groups.
    """
    figure, axis = new(10.0, 7.8)
    _panel(axis, (0, 100), (0, 78))

    left, right = 26.0, 74.0
    wide = 46.0

    _note(
        axis, left, 73.0,
        "One record per glass",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )
    _note(
        axis, right, 73.0,
        "Beside the records, two honest statements",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )

    # ---- the solution's two fields
    _box(
        axis, left, 65.0, wide, 8.5,
        "the mask pixels: which pixels of this picture\n"
        "are this glass, and which of them are only asserted",
        edge=GLASS, face=_tint(GLASS, 0.72), lw=1.6,
    )
    _box(
        axis, left, 55.0, wide, 8.5,
        "whether the picture held the whole glass, or cut it\n"
        "off at the edge of the station's frame",
        edge=GLASS, face=_tint(GLASS, 0.72), lw=1.6,
    )
    _note(
        axis, left, 48.0,
        "The solution supplies these two, and only these two.",
        colour=GLASS, ha="center", weight="bold",
    )

    _arrow(axis, (left, 45.5), (left, 41.5), colour=GLASS)

    # ---- the bench's arithmetic, and the two fields it fills in itself
    _box(
        axis, left, 36.0, wide, 9.0,
        "the bench's shared arithmetic: the axis from the\n"
        f"points at the top of the glass, the width as the {SPREAD}th\n"
        "percentile of the spread around that axis",
    )
    _arrow(axis, (left, 31.5), (left, 27.0))

    _box(
        axis, left, 22.5, wide, 7.5,
        "the place on the table",
        face=_tint(MUTED, 0.86), edge=MUTED, size=LABEL_SIZE,
    )
    _box(
        axis, left, 13.5, wide, 7.5,
        "a rough width of the footprint",
        face=_tint(MUTED, 0.86), edge=MUTED, size=LABEL_SIZE,
    )
    _note(
        axis, left, 6.5,
        "The bench fills these two in from the mask itself, so no\n"
        "solution can win by measuring better or lose by measuring worse.",
        colour=INK, ha="center",
    )

    # ---- the two statements
    _box(
        axis, right, 65.0, wide, 8.5,
        "which glasses could not be separated, and why",
        edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.6,
    )
    _box(
        axis, right, 55.0, wide, 8.5,
        "which parts of the table could not have been\n"
        "seen at all",
        edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.6,
    )
    _note(
        axis, right, 48.0,
        "Neither statement is a list of glasses.",
        colour=WARN, ha="center", weight="bold",
    )

    _arrow(axis, (right, 45.5), (right, 41.5), colour=WARN)

    _box(
        axis, right, 35.0, wide, 11.0,
        "The bench counts a reported doubt as a reported\n"
        "doubt. A glass a solution says it could not separate\n"
        "is not marked as an answer that never arrived, and a\n"
        "patch of table it says it could not see is not marked\n"
        "as a glass it failed to find.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    _note(
        axis, right, 25.0,
        "A doubt is therefore worth stating. Saying nothing about\n"
        "a glass that was never visible is counted as a miss instead.",
        colour=INK, ha="center",
    )

    # which colour means which owner, said once rather than on every box
    for row, (colour, text) in enumerate((
        (GLASS, "a field the solution supplies"),
        (MUTED, "a field the bench computes from the mask"),
    )):
        y = 14.0 - row * 5.0
        axis.add_patch(
            Rectangle(
                (54.0, y - 1.4), 4.0, 2.8,
                facecolor=_tint(colour, 0.78), edgecolor=colour, lw=1.3, zorder=3,
            )
        )
        _note(axis, 59.5, y, text, colour=INK)

    axis.set_title(
        "What must come back from a solution, and what the bench does with each piece",
        fontsize=TITLE_SIZE, color=INK, pad=12,
    )
    save(figure, "03-what-must-come-back.png")


# --------------------------------------------------------------------------- #
# 3. the floor of error, and the trap it exposes
# --------------------------------------------------------------------------- #


def the_floor() -> None:
    """The two paths through the one arithmetic, and the asserted-pixel trap.

    The upper half sends a solution's masks and the bench's own id masks
    through the same step, because the floor only means anything if both sides
    of the comparison went through identical arithmetic. The lower half draws
    the trap the same section names, with the measured cost of falling into it.
    """
    figure, axis = new(10.0, 10.4)
    _panel(axis, (0, 100), (0, 104))

    left, right, wide = 27.0, 73.0, 44.0

    _note(
        axis, 50.0, 101.0,
        "Two kinds of mask, one arithmetic",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )

    _box(
        axis, left, 93.0, wide, 8.5,
        "A solution's masks: the pixels it says\n"
        "are each glass",
        edge=GLASS, face=_tint(GLASS, 0.72), lw=1.6,
    )
    _box(
        axis, right, 93.0, wide, 8.5,
        "The bench's own id masks, run as though a\n"
        "method had returned perfect masks",
        edge=GOOD, face=_tint(GOOD, 0.80), lw=1.6,
    )

    _arrow(axis, (left, 88.75), (left, 82.75), colour=GLASS)
    _arrow(axis, (right, 88.75), (right, 82.75), colour=GOOD)

    _box(
        axis, 50.0, 78.0, 92.0, 9.5,
        "The same shared arithmetic, run the same way on both: each mask pixel carries a depth reading and\n"
        "becomes a point in the room, the axis comes from the points at the top of the glass, and the width is\n"
        f"the {SPREAD}th percentile of how far the cloud reaches from that axis",
    )

    _arrow(axis, (left, 73.25), (left, 68.0), colour=GLASS)
    _arrow(axis, (right, 73.25), (right, 68.0), colour=GOOD)

    _box(
        axis, left, 62.0, wide, 10.5,
        "The method's place and width, which is\n"
        "what its scorecard reports. Nothing in this\n"
        "number is the method's measuring; all of it\n"
        "is the method's mask.",
        edge=GLASS, lw=1.4,
    )
    _box(
        axis, right, 62.0, wide, 10.5,
        "The floor of error: the best place this step can\n"
        f"produce when the mask is exactly right. Over\n"
        f"{FLOOR_GLASSES} glasses it is {FLOOR_MEDIAN_MM} mm out at the middle\n"
        f"glass and {FLOOR_WORST_MM} mm at the worst.",
        edge=GOOD, lw=1.4,
    )

    _note(
        axis, 50.0, 53.0,
        "A method within a hair of the floor is not a good method so much as a method whose remaining error is\n"
        "not its fault, which is what stops effort going into the wrong half of the pipeline.",
        colour=INK, ha="center",
    )

    axis.plot([3, 97], [48.0, 48.0], color=MUTED, lw=0.9, ls=(0, (5, 4)), zorder=1)

    # ---------------------------------------------------------------- the trap
    _note(
        axis, 50.0, 44.5,
        "The trap the floor exposes: a mask that asserts pixels the camera never saw the glass at",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )

    # A side-on sketch: a tall glass stands between the camera and part of the
    # footprint of a short one, so a pixel over the tall glass's body is a pixel
    # whose depth reading is the tall glass's own surface.
    table_y = 12.0
    axis.plot([5, 46], [table_y, table_y], color=INK, lw=1.6, zorder=2)
    _note(axis, 5.0, table_y + 1.6, "the table", colour=MUTED, size=NOTE_SIZE - 0.4)

    camera = (16.0, 40.0)
    axis.add_patch(
        Polygon(
            [(camera[0] - 2.4, camera[1] - 1.5), (camera[0] + 2.4, camera[1] - 1.5),
             (camera[0] + 1.5, camera[1] + 1.5), (camera[0] - 1.5, camera[1] + 1.5)],
            closed=True, facecolor=INK, edgecolor=INK, zorder=5,
        )
    )
    _note(
        axis, camera[0] + 3.4, camera[1],
        "the camera, looking straight down",
        colour=INK, size=NOTE_SIZE - 0.4,
    )

    def tumbler(x, height, half, colour):
        axis.add_patch(
            Polygon(
                [(x - half * 0.78, table_y), (x - half, table_y + height),
                 (x + half, table_y + height), (x + half * 0.78, table_y)],
                closed=True, facecolor=_tint(colour, 0.55), edgecolor=colour, lw=1.4, zorder=4,
            )
        )

    tall_x, tall_h, tall_half = 16.0, 17.0, 3.2
    short_x, short_h, short_half = 24.5, 8.0, 3.4
    tumbler(tall_x, tall_h, tall_half, MUTED)
    tumbler(short_x, short_h, short_half, GLASS)
    _note(axis, 8.5, 31.0, "a tall glass\nin front", colour=INK,
          size=NOTE_SIZE - 0.4, ha="center", va="center")
    _note(axis, 29.5, 22.5, "the short glass\nthe mask is about", colour=GLASS,
          size=NOTE_SIZE - 0.4, ha="left", va="center")

    # the line of sight to an asserted pixel: it stops on the tall glass's rim,
    # well above the table the pixel would otherwise have landed on
    rim = (tall_x + tall_half, table_y + tall_h)
    ground = (rim[0] + (rim[0] - camera[0]) * (rim[1] - table_y) / (camera[1] - rim[1]), table_y)
    axis.plot([camera[0], rim[0]], [camera[1] - 1.6, rim[1]], color=WARN, lw=1.4, zorder=5)
    axis.plot([rim[0], ground[0]], [rim[1], ground[1]], color=WARN, lw=1.1,
              ls=(0, (3, 3)), zorder=5)
    axis.plot(*rim, marker="o", ms=5.5, color=WARN, zorder=6)
    _note(axis, rim[0] + 1.2, rim[1] + 1.4, "the depth reading\nstops here",
          colour=WARN, size=NOTE_SIZE - 0.4, va="bottom")
    axis.plot(*ground, marker="x", ms=6, mew=1.6, color=WARN, zorder=6)

    _arrow(axis, (short_x, table_y - 2.6), (tall_x + 1.0, table_y - 2.6), colour=WARN, lw=1.6)
    _note(
        axis, short_x + 1.4, table_y - 2.6,
        "the place is dragged this way",
        colour=WARN, size=NOTE_SIZE - 0.4, va="center",
    )

    _note(
        axis, 3.0, 4.0,
        "The line of sight to an asserted pixel stops on the\n"
        "tall glass's rim, so the depth reading there belongs\n"
        "to the glass in front, not to the short glass the\n"
        "mask is about.",
        colour=INK,
    )

    # ---- the two measured outcomes
    _box(
        axis, 74.0, 34.0, 46.0, 10.0,
        "Fed in: the asserted pixels keep their depth\n"
        "readings, which belong to whatever stood in\n"
        f"front, and the place lands {FED_IN_MM} mm from the\n"
        "true one at the middle glass.",
        edge=WARN, face=_tint(WARN, 0.86), lw=1.6,
    )
    _box(
        axis, 74.0, 21.0, 46.0, 10.0,
        "Named and left out: the mask says which pixels\n"
        "it asserts, the bench drops their depth readings\n"
        f"rather than guessing a value, and the place lands\n"
        f"{NAMED_MM} mm out instead.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    _note(
        axis, 74.0, 12.0,
        "Both measured with exact masks on the crowded\n"
        f"arrangements, over the {HIDDEN_GLASSES} glasses that something\n"
        "really did stand in front of.",
        colour=MUTED, ha="center",
    )
    _note(
        axis, 74.0, 4.5,
        "So a mask that asserts pixels must say which ones.",
        colour=INK, ha="center", weight="bold",
    )

    axis.set_title(
        "The floor of error: the same arithmetic on a perfect mask, and the trap it exposes",
        fontsize=TITLE_SIZE, color=INK, pad=12,
    )
    save(figure, "03-the-floor.png")


def main() -> None:
    what_the_bench_does()
    what_must_come_back()
    the_floor()


if __name__ == "__main__":
    main()
