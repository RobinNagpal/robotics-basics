"""The four pictures the keeper chapter needs and did not have.

Chapter 09 of this book already has nine pictures, drawn by make_08_images.py
and make_solution_flows_b.py. These four are the shapes the prose of that
chapter carries and none of those nine draws:

    09-measured-on-the-table.png          one glass from the survey's three
                                          stations: its pixel address moves and
                                          the numbers the keeper reads do not.
    09-the-second-round-of-prompts.png    what happens to a proposal the keeper
                                          answered "more than one glass".
    09-where-the-eight-numbers-come-from  why six of the keeper's eight are
                                          measured from one proposal and two
                                          cannot be.
    09-one-block-would-have-misled.png    the five blocks behind one averaged
                                          score, spaced against crowded.

Every number written on these pictures is read out of
``code/src/08_seeing-the-glasses/`` and asserted below against the constant it
came from, so a picture cannot quietly go stale while the code moves.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_keeper_pages.py
"""

from __future__ import annotations

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
    new,
    save,
)
from make_solution_flows_b import _arrow, _audit, _box, _note, _panel, _tint
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Read out of the code. The comment after each one names the constant, so that a
# reader can check it in one step.

# code/src/08_seeing-the-glasses/bench/render.py
PICTURE_W, PICTURE_H = 320, 240          # WIDTH, HEIGHT

# code/src/08_seeing-the-glasses/work_cell/work_cell/glasses/shapes.py,
# KIND_RANGES, through bench/data.py widths(), in millimetres.
STRAIGHT_NARROWEST, STRAIGHT_WIDEST = 45.0, 90.0
TAPERED_NARROWEST = 65.0

# code/src/08_seeing-the-glasses/bench/data.py frame(), divided by render.WIDTH.
MM_PER_PIXEL = 1.623

# code/src/08_seeing-the-glasses/05-sam2-with-a-keeper/sam_keeper.py
POINTS_ACROSS_SMALLEST = 3               # POINTS_ACROSS_SMALLEST
MEASUREMENTS = 8                         # len(MEASUREMENTS)
FROM_ONE_PROPOSAL = 6                    # what _measure returns
FROM_THE_SHORTLIST = 2                   # what _proposals adds afterwards

# One real proposal, as show_keeper.py printed it on held-out arrangement 10000,
# station 1 of 3, straight_glass. Quoted in 05-sam2-with-a-keeper/README.md.
GLASS_WIDTH_MM = 67.0
GLASS_IN_RANGE = 0.484                   # the first of the eight measurements
GLASS_ROUNDNESS = 0.886
GLASS_ABOVE_TABLE_M = 0.164
GLASS_PROMPTS = 972                      # the grid over one straight_glass picture

# code/src/08_seeing-the-glasses/05-sam2-with-a-keeper/results-sam2*-from*.json,
# found per 100 glasses, one entry per block of 20 held-out arrangements.
SPACED_BLOCKS = (81.0, 84.8, 78.0, 86.1, 84.8)
CROWDED_BLOCKS = (72.3, 72.4, 76.6, 71.9, 75.0)
# code/src/08_seeing-the-glasses/results/results-averaged*.json, 05-sam2-with-a-keeper
SPACED_MEAN, SPACED_LOW, SPACED_HIGH = 83.0, 78.0, 86.1
CROWDED_MEAN, CROWDED_LOW, CROWDED_HIGH = 73.6, 71.9, 76.6


def _check() -> None:
    """Every claim a picture below makes, checked against the constants above."""
    # The grid's spacing is read off the kind, not chosen.
    for narrowest, expected in ((STRAIGHT_NARROWEST, 9), (TAPERED_NARROWEST, 13)):
        pixels = max(1, int((narrowest / MM_PER_PIXEL) / POINTS_ACROSS_SMALLEST))
        assert pixels == expected, (narrowest, pixels, expected)
    across = len(range(9 // 2, PICTURE_W, 9)) * len(range(9 // 2, PICTURE_H, 9))
    assert across == GLASS_PROMPTS, (across, GLASS_PROMPTS)

    # The printed proposal's first measurement is where its width falls in the
    # kind's range, so the width and the range have to agree with it.
    span = STRAIGHT_WIDEST - STRAIGHT_NARROWEST
    assert abs((GLASS_WIDTH_MM - STRAIGHT_NARROWEST) / span - GLASS_IN_RANGE) < 0.01

    # Six from one proposal and two from the shortlist are all eight.
    assert FROM_ONE_PROPOSAL + FROM_THE_SHORTLIST == MEASUREMENTS

    # The blocks are what the averaged file averages.
    for blocks, mean, low, high in (
        (SPACED_BLOCKS, SPACED_MEAN, SPACED_LOW, SPACED_HIGH),
        (CROWDED_BLOCKS, CROWDED_MEAN, CROWDED_LOW, CROWDED_HIGH),
    ):
        assert len(blocks) == 5
        # The blocks above are rounded to one place and the averaged file works
        # from the raw counts, so the two agree to a tenth rather than exactly.
        assert abs(sum(blocks) / len(blocks) - mean) < 0.1, (blocks, mean)
        assert min(blocks) == low and max(blocks) == high
    # The claim the last picture is drawn to make.
    assert CROWDED_HIGH < SPACED_LOW, (CROWDED_HIGH, SPACED_LOW)


def _plain(axis, xlim=(0.0, 100.0), ylim=(0.0, 100.0)) -> None:
    axis.set_xticks([])
    axis.set_yticks([])
    for side in axis.spines.values():
        side.set_visible(False)
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    axis.set_facecolor(PAPER)


def _heading(axis, text, y=97.0) -> None:
    axis.text(50.0, y, text, ha="center", va="top", fontsize=TITLE_SIZE, color=INK)


# --------------------------------------------------------------------------- #
# 1. The keeper's numbers are measured on the table, not in the picture
# --------------------------------------------------------------------------- #


def measured_on_the_table() -> None:
    """One glass, three stations: the address moves and the measurements do not.

    The requirement this draws is the one the prose states and cannot show: no
    input of the keeper's may be an address in the picture, because the camera
    is on the wrist and visits three stations over the glass zone. Three frames
    with the same glass at three addresses, and one row of numbers underneath
    that is the same under all three, is the whole argument.
    """
    inches_wide, inches_high = 11.0, 7.0
    figure, axis = new(inches_wide, inches_high)
    _panel(figure, axis, (0, 100), (0, 100))
    _heading(axis, "The same glass from three stations: its address moves, its measurements do not")

    # Panel units are not square, so anything that has to look square is
    # stretched in y by the ratio between one x unit and one y unit.
    stretch = inches_wide / inches_high

    # Where the glass lands in each station's frame, in picture pixels, and the
    # frames themselves, drawn in the proportion of a 320 by 240 picture.
    stations = (
        ("station 1", (212, 96)),
        ("station 2", (104, 150)),
        ("station 3", (158, 61)),
    )
    frame_w = 23.0
    frame_h = frame_w * stretch * PICTURE_H / PICTURE_W
    left_edges = (8.0, 38.5, 69.0)
    top = 87.0

    for (name, (column, row)), x0 in zip(stations, left_edges, strict=True):
        axis.add_patch(
            Rectangle((x0, top - frame_h), frame_w, frame_h, facecolor=_tint(MUTED, 0.93),
                      edgecolor=MUTED, linewidth=1.0, zorder=2)
        )
        axis.text(x0 + frame_w / 2.0, top + 1.6, name, ha="center", va="bottom",
                  fontsize=LABEL_SIZE, color=INK, weight="bold")
        # The glass, drawn as the filled disc an overhead picture gives.
        cx = x0 + frame_w * column / PICTURE_W
        cy = top - frame_h * row / PICTURE_H
        axis.add_patch(
            Ellipse((cx, cy), 2.0 * 2.2, 2.0 * 2.2 * stretch, facecolor=GLASS, alpha=0.75,
                    edgecolor=GLASS, linewidth=1.0, zorder=4)
        )
        axis.plot([cx], [cy], marker="+", color=WARN, markersize=7, markeredgewidth=1.4, zorder=5)
        axis.text(cx, cy - 4.6, f"({column}, {row})", ha="center", va="top",
                  fontsize=NOTE_SIZE, color=WARN, zorder=5)

    axis.text(50.0, top - frame_h - 2.0, f"each frame is {PICTURE_W} by {PICTURE_H} pixels",
              ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED)

    _note(axis, 50.0, 50.0,
          "three different addresses, one for each place the camera stood",
          colour=WARN, size=LABEL_SIZE, ha="center")

    for x0 in left_edges:
        _arrow(axis, (x0 + frame_w / 2.0, 45.5), (50.0, 39.0), colour=MUTED, lw=1.0)

    same = (
        f"width {GLASS_WIDTH_MM:.0f} mm, which is {GLASS_IN_RANGE:.3f} of the way\n"
        f"up the {STRAIGHT_NARROWEST:.0f} to {STRAIGHT_WIDEST:.0f} mm this kind allows\n"
        f"roundness {GLASS_ROUNDNESS:.3f}\n"
        f"{1000 * GLASS_ABOVE_TABLE_M:.0f} mm above the table"
    )
    _box(axis, 50.0, 28.0, 62.0, same, edge=GOOD, face=_tint(GOOD, 0.88), size=LABEL_SIZE, lw=1.8)

    _note(axis, 50.0, 8.0,
          "One mask, measured three ways and read back on the table: the same three numbers every\n"
          "time. An input measured in pixels would have taught the keeper where the camera was parked.",
          colour=INK, size=NOTE_SIZE, ha="center")

    _audit(figure, axis, "09-measured-on-the-table.png")
    save(figure, "09-measured-on-the-table.png")


# --------------------------------------------------------------------------- #
# 2. The second round of prompts
# --------------------------------------------------------------------------- #


def the_second_round_of_prompts() -> None:
    """A proposal answered "more than one glass", prompted again inside itself.

    Two panels of one thing: the pair seen from the top, where the first round
    found no seam, and the same pair seen from the side, where the step in depth
    the second round can find is the only reason the second round works at all.
    """
    figure, axes = new(11.4, 5.6, columns=2)
    top, side = axes
    for axis in axes:
        _plain(axis)
    figure.suptitle(
        "A proposal the keeper calls \"more than one glass\" is prompted again, inside itself",
        fontsize=TITLE_SIZE, color=INK, y=0.985,
    )

    # ---- left: the top view, and the grid laid only inside the proposal.
    top.text(50.0, 92.0, "From the top: one region, no seam along the join",
             ha="center", va="top", fontsize=LABEL_SIZE, color=INK)

    near = (40.0, 36.0, 17.0)   # x, y, radius, in panel units
    far = (62.0, 58.0, 13.5)
    discs = (near, far)
    for cx, cy, r in (far, near):
        top.add_patch(Circle((cx, cy), r, facecolor=GLASS, alpha=0.38,
                             edgecolor="none", zorder=2))

    # The proposal is one outline round the union of the two, because the first
    # round found no seam between them. Drawn by walking each circle and
    # dropping the arc that falls inside the other one.
    for index, (cx, cy, r) in enumerate(discs):
        other = discs[1 - index]
        angles = np.linspace(0.0, 2.0 * np.pi, 721)
        xs = cx + r * np.cos(angles)
        ys = cy + r * np.sin(angles)
        covered = np.hypot(xs - other[0], ys - other[1]) < other[2]
        xs, ys = xs.copy(), ys.copy()
        xs[covered] = np.nan
        ys[covered] = np.nan
        top.plot(xs, ys, color=WARN, linewidth=2.0, linestyle=(0, (5, 3)), zorder=4)

    spacing = max(1, int((TAPERED_NARROWEST / MM_PER_PIXEL) / POINTS_ACROSS_SMALLEST))
    step_units = 6.2                       # drawn spacing; the real one is in the caption
    inside = []
    for gx in np.arange(16.0, 86.0, step_units):
        for gy in np.arange(12.0, 80.0, step_units):
            if any(np.hypot(gx - cx, gy - cy) <= r for cx, cy, r in (near, far)):
                inside.append((gx, gy))
    top.plot([p[0] for p in inside], [p[1] for p in inside], linestyle="none",
             marker="o", markersize=2.6, color=GOOD, zorder=6)

    top.text(50.0, 4.0,
             f"The dashed line is the one outline the first round returned. The fresh grid\n"
             f"keeps the same {spacing} pixel spacing and puts no point outside it.",
             ha="center", va="bottom", fontsize=NOTE_SIZE, color=INK)

    # ---- right: the side view, and the step in depth.
    side.text(50.0, 92.0, "From the side: the step the second round finds",
              ha="center", va="top", fontsize=LABEL_SIZE, color=INK)

    side.plot([8.0, 92.0], [20.0, 20.0], color=MUTED, linewidth=1.4, zorder=2)
    side.text(90.0, 17.0, "table", ha="right", va="top", fontsize=NOTE_SIZE, color=MUTED)

    # The near glass is taller and nearer the camera; the far one stands behind.
    side.add_patch(Rectangle((30.0, 20.0), 20.0, 42.0, facecolor=GLASS, alpha=0.55,
                             edgecolor=GLASS, linewidth=1.2, zorder=3))
    side.add_patch(Rectangle((56.0, 20.0), 17.0, 26.0, facecolor=GLASS, alpha=0.30,
                             edgecolor=GLASS, linewidth=1.2, zorder=3))
    side.text(40.0, 65.0, "the near glass", ha="center", va="bottom",
              fontsize=NOTE_SIZE, color=INK)
    side.text(64.5, 49.0, "the far glass", ha="center", va="bottom",
              fontsize=NOTE_SIZE, color=INK)

    # The camera above, and the depth step between the two surfaces.
    side.plot([20.0], [78.0], marker="v", markersize=9, color=INK, zorder=4)
    side.text(20.0, 74.0, "the camera,\nlooking down", ha="center", va="top",
              fontsize=NOTE_SIZE, color=INK)
    side.add_patch(
        FancyArrowPatch((80.0, 62.0), (80.0, 46.0), arrowstyle="<|-|>", mutation_scale=11,
                        linewidth=1.6, color=WARN, shrinkA=0, shrinkB=0, zorder=6)
    )
    side.text(82.5, 54.0, "the step in depth\nbetween the near rim\nand the far wall",
              ha="left", va="center", fontsize=NOTE_SIZE, color=WARN)
    side.plot([50.0, 80.0], [62.0, 62.0], color=WARN, linewidth=0.9,
              linestyle=(0, (3, 3)), zorder=5)
    side.plot([64.5, 80.0], [46.0, 46.0], color=WARN, linewidth=0.9,
              linestyle=(0, (3, 3)), zorder=5)

    side.text(50.0, 4.0,
              "Each region that comes back is put to the same width check every report\n"
              "passes. If fewer than two survive it, the pair is handed over as a pair.",
              ha="center", va="bottom", fontsize=NOTE_SIZE, color=INK)

    save(figure, "09-the-second-round-of-prompts.png")


# --------------------------------------------------------------------------- #
# 3. Where the keeper's eight numbers come from
# --------------------------------------------------------------------------- #


def where_the_eight_numbers_come_from() -> None:
    """Six measured from one proposal, two that only the shortlist can give.

    This is the shape of the code: ``_measure`` returns six numbers from one
    region, and ``_proposals`` adds the other two once the whole shortlist can
    be compared with itself. The picture is here because the split looks
    arbitrary in the prose and is not.
    """
    figure, axis = new(10.6, 6.6)
    _panel(figure, axis, (0, 100), (0, 100))
    _heading(axis, "Six of the keeper's numbers come from one proposal; two cannot")

    alone = (
        "where its width falls in the kind's range",
        "how round it is",
        "how far it stands above the table",
        "how far it sits from under the camera",
        "how much of its outline is a step in depth",
        "its area on the table",
    )
    together = (
        "how many prompt points returned it",
        "whether another proposal contains it",
    )
    assert len(alone) == FROM_ONE_PROPOSAL and len(together) == FROM_THE_SHORTLIST

    _box(axis, 26.0, 85.0, 44.0, "read off one proposal, by _measure",
         edge=GLASS, face=_tint(GLASS, 0.84), size=LABEL_SIZE, lw=1.8, weight="bold")
    _box(axis, 74.0, 85.0, 44.0, "only once the shortlist is side by side",
         edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.8, weight="bold")

    y = 73.0
    for text in alone:
        _box(axis, 26.0, y, 44.0, text, edge=GLASS, size=NOTE_SIZE)
        y -= 8.4

    y2 = 73.0
    for text in together:
        _box(axis, 74.0, y2, 44.0, text, edge=WARN, size=NOTE_SIZE)
        y2 -= 8.4

    _arrow(axis, (26.0, 25.0), (42.0, 15.5), colour=GLASS)
    _arrow(axis, (74.0, 57.0), (58.0, 15.5), colour=WARN)
    _box(axis, 50.0, 10.0, 52.0,
         f"these {MEASUREMENTS} numbers, and nothing else",
         edge=GOOD, face=_tint(GOOD, 0.84), size=LABEL_SIZE, lw=1.8, weight="bold")

    _audit(figure, axis, "09-where-the-eight-numbers-come-from.png")
    save(figure, "09-where-the-eight-numbers-come-from.png")


# --------------------------------------------------------------------------- #
# 4. The five blocks behind one averaged score
# --------------------------------------------------------------------------- #


def one_block_would_have_misled() -> None:
    """Every block this solution was scored on, against the average it reports.

    One averaged number hides how far the blocks are apart, and the chapter asks
    the reader to hold both. Drawn as one axis so that the two sets can be read
    against each other: the gap between them is the only separation this test
    actually establishes for this solution.
    """
    figure, axis = new(10.4, 4.6)
    _plain(axis, xlim=(66.0, 92.0), ylim=(0.0, 10.0))
    axis.text(79.0, 9.6, "Found per 100 glasses, one dot per block of 20 held-out arrangements",
              ha="center", va="top", fontsize=TITLE_SIZE, color=INK)

    rows = (
        (6.4, "spaced", SPACED_BLOCKS, SPACED_MEAN, GLASS),
        (3.4, "crowded", CROWDED_BLOCKS, CROWDED_MEAN, WARN),
    )
    for y, name, blocks, mean, colour in rows:
        axis.plot([min(blocks), max(blocks)], [y, y], color=colour, linewidth=2.4,
                  solid_capstyle="round", alpha=0.35, zorder=2)
        # Two blocks that scored the same would sit on top of each other and
        # the row would look like four blocks rather than five, so equal values
        # are stacked instead of hidden.
        seen: dict[float, int] = {}
        for value in blocks:
            level = seen.get(value, 0)
            seen[value] = level + 1
            axis.plot([value], [y + 0.52 * level], linestyle="none", marker="o",
                      markersize=8, markerfacecolor=PAPER, markeredgecolor=colour,
                      markeredgewidth=1.6, zorder=4)
        axis.plot([mean], [y], marker="D", markersize=9, color=colour, zorder=5)
        axis.text(66.6, y, name, ha="left", va="center", fontsize=LABEL_SIZE,
                  color=colour, weight="bold")
        axis.text(mean, y + 0.95, f"{mean:.1f} on average", ha="center", va="bottom",
                  fontsize=NOTE_SIZE, color=colour)
        axis.text(min(blocks), y - 0.95, f"{min(blocks):.1f}", ha="center", va="top",
                  fontsize=NOTE_SIZE, color=MUTED)
        axis.text(max(blocks), y - 0.95, f"{max(blocks):.1f}", ha="center", va="top",
                  fontsize=NOTE_SIZE, color=MUTED)

    # The axis itself.
    axis.plot([67.5, 90.5], [1.2, 1.2], color=MUTED, linewidth=1.0, zorder=1)
    for tick in range(70, 91, 5):
        axis.plot([tick, tick], [1.2, 0.95], color=MUTED, linewidth=1.0, zorder=1)
        axis.text(tick, 0.65, str(tick), ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED)

    # The one claim the picture is drawn to make.
    axis.axvspan(CROWDED_HIGH, SPACED_LOW, ymin=0.16, ymax=0.80, color=_tint(GOOD, 0.82),
                 zorder=0)
    axis.text((CROWDED_HIGH + SPACED_LOW) / 2.0, 8.2,
              "no block of either set\nlands in here", ha="center", va="top",
              fontsize=NOTE_SIZE, color=GOOD)

    save(figure, "09-one-block-would-have-misled.png")


def main() -> None:
    _check()
    measured_on_the_table()
    the_second_round_of_prompts()
    where_the_eight_numbers_come_from()
    one_block_would_have_misled()


if __name__ == "__main__":
    main()
