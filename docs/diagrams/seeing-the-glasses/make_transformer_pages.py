"""Five pictures for the chapter on solution 6, the transformer segmenter.

The chapter already had six pictures before these: two flow charts in
``make_solution_flows_b.py`` and four geometry panels in ``make_10_images.py``.
Each picture here carries a shape none of those carry and none of the prose can
carry on its own, and each one makes a claim that is computed before the figure
is drawn and asserted, so a picture cannot quietly go stale when a constant
moves or a run is repeated.

    10-no-rectangle-to-escape.png
        The one structural fact the whole chapter rests on. The same partly
        covered glass twice: once with the smallest rectangle round the pixels
        the camera saw, which is the frame the older shape paints a mask in,
        and once with no rectangle at all. The share of the hidden part lying
        outside that rectangle is measured off the rasters.

    10-the-overlap-number.png
        How much two different glasses' rectangles overlap, as they are stood
        closer together, against the 0.7 a pruning step is set to. The curve
        never reaches the line, which is the honest version of "set prediction
        removes a number somebody has to justify": the number is not currently
        losing glasses here, it is a number somebody has to keep justifying.

    10-who-owns-a-contested-pixel.png
        The split in ``hidden_by_others``, drawn. Two reports claim the same
        pixels; the one whose own uncontested part sits nearer the point below
        the camera is in front and keeps them, and the other must call them
        asserted. Both distances are measured off the drawn arrangement.

    10-how-wrong-a-width-can-be.png
        The kind's own range of footprints on one axis, with the two directions
        a width can be wrong marked on it: narrow, where there is slack and
        nothing refuses, and wide, where there is none. This is why a mask cut
        short is a quiet failure and a merged pair is a loud one.

    10-read-the-brackets.png
        Every solution's crowded score with the spread of its five blocks, read
        out of ``results/results-averaged-crowded.json`` when this script runs.
        The claim the chapter makes — that this solution is the only one
        standing clear of the group — is a claim about those brackets.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_transformer_pages.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    KIND_NARROWEST,
    KIND_TALLEST,
    KIND_WIDEST,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    TITLE_SIZE,
    WARN,
    bare,
    new,
    save,
)
from make_10_images import (
    BITTEN,
    NADIR,
    OCCLUDER_FAR,
    area_of,
    camera_mark,
    mask_window,
    note,
    outline,
    paint,
    panel_title,
    plan_panel,
    scene_masks,
    stack_of,
)
from make_solution_flows_a import _tint
from matplotlib.patches import Rectangle

# ------------------------------------------------------------------ the numbers
#
# Every one of these is a constant in code/src/08_seeing-the-glasses/, and the
# comment beside it says which file it lives in.

MIN_SEPARATION_MM = 150.0     # MIN_SEPARATION in work_cell/glasses/spawn.py, in mm
CROWDED_GAP = (0.3, 0.7)      # CROWDED_GAP in bench/data.py, as a share of the above
PRUNING_OVERLAP = 0.7         # OVERLAP in 04-yolo-fine-tuned/yolo_fine_tuned.py

# code/src/08_seeing-the-glasses/results/, written by bench/average_blocks.py.
RESULTS = (
    Path(__file__).resolve().parents[3]
    / "code" / "src" / "08_seeing-the-glasses" / "results"
)

# What each solution is called on the brackets chart, in the order the results
# file holds them. The folder names are the addresses; these are the words.
SOLUTIONS = {
    "01-rules-on-the-table": "1  rules on the table",
    "02-train-from-scratch": "2  trained from scratch",
    "03-yolo-zero-shot": "3  YOLO as it downloads",
    "04-yolo-fine-tuned": "4  YOLO fine-tuned",
    "05-sam2-with-a-keeper": "5  SAM 2 with a keeper",
    "06-rf-detr-fine-tuned": "6  this solution",
}
MINE = "06-rf-detr-fine-tuned"


def _look_over(figure, name: str) -> None:
    """Measure the drawn figure and say what a glance at the PNG can miss.

    The same two faults ``make_solution_flows_a._audit`` looks for, over every
    panel of a figure rather than over the first one: two pieces of text sharing
    a patch of page, and a label landing outside the panel it belongs to. These
    pictures are drawings rather than chains of boxes, so there are no boxes to
    check text against.
    """
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    faults = []

    def first_line(label, limit=44):
        return label.get_text().splitlines()[0][:limit]

    def clashes(a, b, room=1.0):
        return (min(a.x1, b.x1) - max(a.x0, b.x0) > room
                and min(a.y1, b.y1) - max(a.y0, b.y0) > room)

    for axis in figure.axes:
        drawn = [(t, t.get_window_extent(renderer))
                 for t in axis.texts if t.get_text().strip()]
        for index, (one, a) in enumerate(drawn):
            for two, b in drawn[index + 1:]:
                if clashes(a, b):
                    faults.append(
                        f"  text over text: {first_line(one, 32)!r}"
                        f" and {first_line(two, 32)!r}"
                    )
        room = axis.get_window_extent(renderer)
        for words, where in drawn:
            if (where.x0 < room.x0 - 1.0 or where.x1 > room.x1 + 1.0
                    or where.y0 < room.y0 - 1.0 or where.y1 > room.y1 + 1.0):
                faults.append(f"  text outside its panel: {first_line(words)!r}")

    if faults:
        print(f"{name}: {len(faults)} thing(s) to fix")
        print("\n".join(faults))


# --------------------------------------------------------------------------- #
# 1. there is no rectangle for a mask to escape
# --------------------------------------------------------------------------- #

def figure_no_rectangle_to_escape() -> None:
    """The frame the older shape paints a mask in, beside no frame at all.

    One partly covered glass, drawn twice. On the left the smallest rectangle
    round the pixels the camera saw of it, which is where a detector of the
    older shape finds its object and where it paints the mask. On the right the
    same glass with nothing round it. The number that matters is how much of the
    hidden part falls outside that rectangle, because that is the part of the
    answer the older shape cannot reach however it is trained.
    """
    grid_x, grid_y, extent, masks, step = scene_masks(1.2)
    name, _, _ = BITTEN
    whole, seen = masks[name]
    hidden = whole & ~seen

    # The rectangle a detector of the older shape would work in: the smallest
    # one round the pixels the picture actually holds of this glass.
    x0, x1 = float(grid_x[seen].min()), float(grid_x[seen].max())
    y0, y1 = float(grid_y[seen].min()), float(grid_y[seen].max())
    boxed = (grid_x >= x0) & (grid_x <= x1) & (grid_y >= y0) & (grid_y <= y1)
    unreachable = hidden & ~boxed
    share = 100.0 * unreachable.sum() / hidden.sum()
    assert share > 50.0, f"only {share:.0f}% of the hidden part falls outside the rectangle"

    window = mask_window(whole, grid_x, grid_y, pad=34.0)
    figure, (left, right) = new(11.4, 5.4, columns=2)

    for axis in (left, right):
        plan_panel(axis, window)
        paint(axis, masks[OCCLUDER_FAR[0]][1], MUTED, extent, alpha=0.22)
        paint(axis, seen, GLASS, extent, alpha=0.60, zorder=3)

    panel_title(left, "The older shape: a mask lives inside a rectangle", colour=WARN)
    paint(left, hidden & boxed, WARN, extent, alpha=0.16, zorder=4)
    paint(left, unreachable, WARN, extent, alpha=0.50, zorder=4)
    outline(left, whole, grid_x, grid_y, MUTED, ls="dashed")
    left.add_patch(
        Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor=WARN,
                  lw=1.6, ls=(0, (5, 3)), zorder=7)
    )
    note(left, window[0] + 8, window[2] + 8,
         f"Orange: {share:.0f}% of the hidden part, outside the rectangle.\n"
         "No amount of training reaches it.", colour=INK, va="bottom")

    panel_title(right, "This model: a mask is the whole picture's answer", colour=GOOD)
    paint(right, hidden, WARN, extent, alpha=0.45, zorder=4)
    outline(right, whole, grid_x, grid_y, GOOD, ls="solid", lw=1.5)
    note(right, window[0] + 8, window[2] + 8,
         "No rectangle. Any pixel of the picture\nis one this mask may claim.",
         colour=INK, va="bottom")

    figure.suptitle(
        "The rectangle is drawn from what the camera saw, so it is the wrong size for the glass.",
        fontsize=TITLE_SIZE, color=INK, y=1.02,
    )
    figure.tight_layout()
    figure.text(
        0.5, -0.02,
        "The blue is where this glass's own surface was seen, the grey is the glass standing in "
        "front of it, and the dashed line is where the glass really ends.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    print(f"  no-rectangle: {share:.0f}% of the hidden part lies outside the visible rectangle")
    _look_over(figure, "10-no-rectangle-to-escape.png")
    save(figure, "10-no-rectangle-to-escape.png")


# --------------------------------------------------------------------------- #
# 2. the overlap number a pruning step needs
# --------------------------------------------------------------------------- #

def _rectangle(circles) -> tuple[float, float, float, float]:
    """The smallest rectangle round a splayed silhouette."""
    xs = [c[0] - r for c, r in circles] + [c[0] + r for c, r in circles]
    ys = [c[1] - r for c, r in circles] + [c[1] + r for c, r in circles]
    return min(xs), min(ys), max(xs), max(ys)


def _overlap(first, second) -> float:
    """How much two rectangles share, over how much they cover between them."""
    ax0, ay0, ax1, ay1 = _rectangle(first)
    bx0, by0, bx1, by1 = _rectangle(second)
    across = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    down = max(0.0, min(ay1, by1) - max(ay0, by0))
    shared = across * down
    return shared / ((ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - shared)


def figure_the_overlap_number() -> None:
    """What the worst honest overlap in this cell is, against where the number sits.

    A pruning step throws away a claim overlapping a better-scoring one by more
    than a chosen amount, and the fear is that two genuinely different glasses
    overlap that much. Here they do not: the curve is drawn for the pair that
    overlaps most, two glasses at the tall and wide corner of the kind on a line
    running out from the camera, and it stays well under the number.
    """
    tallest = (KIND_TALLEST, KIND_WIDEST)
    inner = 60.0      # how far out from the camera the nearer glass stands
    gaps = np.arange(40.0, 170.0, 2.0)
    overlaps = np.array([
        _overlap(stack_of(np.array([inner, 0.0]), tallest)[0],
                 stack_of(np.array([inner + gap, 0.0]), tallest)[0])
        for gap in gaps
    ])

    closest = CROWDED_GAP[0] * MIN_SEPARATION_MM
    reachable = overlaps[gaps >= closest]
    worst = float(reachable.max())
    assert worst < PRUNING_OVERLAP, f"overlap reaches {worst:.2f}, which the pruning number cuts"

    figure, axis = new(10.0, 4.8)
    bare(axis)
    axis.set_xlim(gaps.min(), gaps.max())
    axis.set_ylim(-0.14, 0.92)

    axis.add_patch(
        Rectangle((closest, 0.0), CROWDED_GAP[1] * MIN_SEPARATION_MM - closest, 0.92,
                  facecolor=_tint(WARN, 0.90), edgecolor="none", zorder=1)
    )
    axis.plot(gaps, overlaps, color=GLASS, lw=2.2, zorder=4)
    axis.axhline(PRUNING_OVERLAP, color=WARN, lw=1.5, ls=(0, (5, 3)), zorder=3)
    axis.plot([MIN_SEPARATION_MM, MIN_SEPARATION_MM], [0.0, 0.62],
              color=MUTED, lw=1.1, ls=(0, (2, 3)), zorder=2)
    axis.scatter([closest], [worst], s=46, color=GLASS, zorder=5)

    # the axis, drawn rather than ticked, so the picture reads as a drawing
    axis.plot([gaps.min(), gaps.max()], [0.0, 0.0], color=INK, lw=1.0, zorder=3)
    for gap in (45.0, 75.0, 105.0, 150.0):
        axis.plot([gap, gap], [0.0, -0.018], color=INK, lw=1.0, clip_on=False, zorder=3)
        note(axis, gap, -0.028, f"{gap:.0f}", colour=INK, ha="center", va="top")
    note(axis, (gaps.min() + gaps.max()) / 2.0, -0.072,
         "how far apart the two glasses stand, in mm", colour=INK, ha="center", va="top")

    note(axis, closest + 4.0, 0.88, "the gaps the examiner's crowded lines use",
         colour=WARN, ha="left", va="top")
    note(axis, MIN_SEPARATION_MM - 5.0, 0.60, "what the cell's own\nlayout rule guarantees",
         colour=MUTED, ha="right", va="top")
    note(axis, MIN_SEPARATION_MM - 8.0, PRUNING_OVERLAP + 0.03,
         f"{PRUNING_OVERLAP}: where a pruning step's number sits",
         colour=WARN, ha="right", va="bottom")
    note(axis, closest + 5.0, worst + 0.035,
         f"the worst two different glasses reach: {worst:.2f}",
         colour=GLASS, ha="left", va="bottom", weight="bold")

    axis.set_title(
        "In this cell two different glasses never look enough alike to be pruned",
        fontsize=TITLE_SIZE, color=INK, pad=12,
    )
    figure.tight_layout()
    figure.text(
        0.5, -0.04,
        "How much the two rectangles share, over how much they cover between them, for the pair "
        "that overlaps most: two glasses at the tall, wide corner of the kind, on a line out from "
        "the camera.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    print(f"  overlap: worst reachable {worst:.2f} against the pruning number {PRUNING_OVERLAP}")
    _look_over(figure, "10-the-overlap-number.png")
    save(figure, "10-the-overlap-number.png")


# --------------------------------------------------------------------------- #
# 3. who owns a contested pixel
# --------------------------------------------------------------------------- #

def figure_who_owns_a_contested_pixel() -> None:
    """The split, worked out from the answer rather than from the truth.

    Two reports claim the same pixels. Splay throws every outline outwards from
    the point below the camera, so the report standing nearer that point is the
    one in front: it keeps the contested pixels, and the other must call them
    asserted so that their depth readings are left out of its measurement.
    """
    grid_x, grid_y, extent, masks, step = scene_masks(1.2)
    near, far = OCCLUDER_FAR[0], BITTEN[0]
    contested = masks[near][0] & masks[far][0]
    assert contested.any(), "the two reports have to overlap for there to be anything to split"

    middles, aways = {}, {}
    for who in (near, far):
        alone = masks[who][0] & ~contested
        middles[who] = (float(grid_x[alone].mean()), float(grid_y[alone].mean()))
        aways[who] = float(np.hypot(*middles[who]))
    assert aways[near] < aways[far], "the covering glass has to be the one nearer the camera"
    shared = area_of(contested, step)

    window = (grid_x[masks[far][0]].min() - 36.0, 90.0,
              -70.0, grid_y[masks[far][0]].max() + 40.0)

    figure, (plan, key) = new(13.2, 5.6, columns=2)

    # ---- the two reports, and the pixels they both claim -------------------
    plan_panel(plan, window)
    colours = {near: GLASS, far: GOOD}
    for who in (near, far):
        paint(plan, masks[who][0], colours[who], extent, alpha=0.26)
        outline(plan, masks[who][0], grid_x, grid_y, colours[who], ls="solid", lw=1.3)
    paint(plan, contested, WARN, extent, alpha=0.55, zorder=4)

    # One ray out from the camera, with both middles on it, because the whole
    # rule is an ordering along that ray and two rays would only overlap.
    plan.plot([NADIR[0], middles[far][0]], [NADIR[1], middles[far][1]],
              color=MUTED, lw=1.1, ls=(0, (4, 3)), zorder=5)
    for who in (near, far):
        plan.scatter([middles[who][0]], [middles[who][1]], s=40, color=colours[who],
                     edgecolor="white", linewidth=0.8, zorder=7)
        side = 1.0 if who == near else -1.0
        note(plan, middles[who][0] + 16.0 * side, middles[who][1] - 4.0 * side, who,
             colour=colours[who], ha="left" if who == near else "right",
             va="top" if who == near else "bottom", size=LABEL_SIZE, weight="bold")
    camera_mark(plan, dx=-12.0, dy=-12.0, ha="right")

    # ---- what the rule then says ------------------------------------------
    bare(key)
    key.set_xlim(0.0, 100.0)
    key.set_ylim(0.0, 100.0)
    note(key, 0.0, 96.0, "The rule, and what it decides", colour=INK,
         size=LABEL_SIZE + 1.0, va="top", weight="bold")
    note(key, 0.0, 86.0,
         "Splay throws every outline outwards from the point\n"
         "below the camera, so of two reports whose masks\n"
         "overlap, the one standing nearer that point is in front.",
         colour=INK, va="top")
    lines = (
        (colours[near], near, f"{aways[near]:.0f} mm out",
         f"Nearer, so it is in front. It keeps all {shared:.0f} mm²."),
        (colours[far], far, f"{aways[far]:.0f} mm out",
         "Further, so it calls those pixels asserted, and\ntheir depth readings are left out of its answer."),
    )
    for index, (colour, who, distance, what) in enumerate(lines):
        y = 58.0 - index * 24.0
        key.add_patch(Rectangle((0.0, y - 3.4), 4.0, 4.0, facecolor=_tint(colour, 0.40),
                                edgecolor=colour, lw=1.0, zorder=3))
        note(key, 7.0, y, f"{who} — {distance}", colour=colour, va="center",
             size=LABEL_SIZE, weight="bold")
        note(key, 7.0, y - 6.0, what, colour=INK, va="top")
    note(key, 0.0, 16.0,
         "Neither distance asks the simulator anything. Each comes\n"
         "from the pixels no other report claims, and the point below\n"
         "the camera comes from the camera's own pose.",
         colour=MUTED, va="top")

    figure.suptitle(
        "Of two reports claiming one pixel, the one nearer the point below the camera owns it",
        fontsize=TITLE_SIZE, color=INK, y=1.0,
    )
    figure.tight_layout()
    print(f"  split: {near} {aways[near]:.0f} mm, {far} {aways[far]:.0f} mm, "
          f"{shared:.0f} mm2 contested")
    _look_over(figure, "10-who-owns-a-contested-pixel.png")
    save(figure, "10-who-owns-a-contested-pixel.png")


# --------------------------------------------------------------------------- #
# 4. how wrong a width can be before anything refuses it
# --------------------------------------------------------------------------- #

def figure_how_wrong_a_width_can_be() -> None:
    """The kind's own range of footprints, with both ways of being wrong on it.

    The width check can only refuse a width outside the range the kind allows,
    and the range is not symmetric about any one glass. A mask cut short reads
    narrower than the glass and has the whole width of the range to fall through
    before it leaves it. A region covering two glasses reads wider than any
    glass of the kind, and leaves the range at once.
    """
    narrow, wide = KIND_NARROWEST, KIND_WIDEST
    slack = 100.0 * (1.0 - narrow / wide)
    crowded_merge = CROWDED_GAP[0] * MIN_SEPARATION_MM + narrow
    spaced_merge = MIN_SEPARATION_MM + narrow
    assert crowded_merge > wide, "a merged pair has to read wider than one glass of the kind"

    figure, axis = new(10.6, 3.4)
    bare(axis)
    axis.set_xlim(40.0, 248.0)
    axis.set_ylim(-0.95, 0.98)

    axis.add_patch(
        Rectangle((narrow, -0.16), wide - narrow, 0.32, facecolor=_tint(GOOD, 0.80),
                  edgecolor=GOOD, lw=1.4, zorder=3)
    )
    axis.plot([40.0, 248.0], [0.0, 0.0], color=INK, lw=1.0, zorder=2)
    for width in (narrow, wide, spaced_merge):
        axis.plot([width, width], [0.0, -0.24], color=INK, lw=1.0, zorder=4)
        note(axis, width, -0.30, f"{width:.0f}", colour=INK, ha="center", va="top")
    note(axis, (40.0 + 248.0) / 2.0, -0.74,
         "the footprint width a report comes back with, in mm",
         colour=INK, ha="center", va="top")
    note(axis, spaced_merge, -0.52, "two glasses at the cell's own spacing",
         colour=MUTED, ha="center", va="top")

    note(axis, (narrow + wide) / 2.0, 0.0, "nothing refuses", colour=GOOD,
         ha="center", va="center", size=LABEL_SIZE, weight="bold")

    # the one case that only just leaves the band, marked above the axis so its
    # label has room the crowded tick marks below do not
    axis.plot([crowded_merge, crowded_merge], [0.0, 0.20], color=WARN, lw=1.2, zorder=4)
    note(axis, crowded_merge + 3.0, 0.21,
         f"{crowded_merge:.0f}: two glasses as close as the examiner ever crowds them",
         colour=WARN, ha="left", va="bottom")

    axis.annotate("", xy=(narrow + 1.0, 0.56), xytext=(wide - 1.0, 0.56),
                  arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.3,
                              "shrinkA": 0, "shrinkB": 0}, zorder=5)
    note(axis, (narrow + wide) / 2.0, 0.62,
         f"a mask cut short reads narrow: {slack:.0f}% of the width can go, quietly",
         colour=INK, ha="center", va="bottom")

    axis.annotate("", xy=(248.0, 0.56), xytext=(wide + 2.0, 0.56),
                  arrowprops={"arrowstyle": "-|>", "color": WARN, "lw": 1.3,
                              "shrinkA": 0, "shrinkB": 0}, zorder=5)
    note(axis, (wide + 248.0) / 2.0, 0.62,
         "two glasses in one region: refused at once", colour=WARN,
         ha="center", va="bottom")

    axis.set_title(
        "The check has room on one side and none on the other",
        fontsize=TITLE_SIZE, color=INK, pad=12,
    )
    figure.tight_layout()
    figure.text(
        0.5, -0.03,
        f"The green band is every footprint this kind of glass can have, {narrow:.0f} to "
        f"{wide:.0f} mm, worked out by building the kind at the corners of its own range.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    print(f"  width: band {narrow:.0f}-{wide:.0f} mm, {slack:.0f}% slack, "
          f"merged pair {crowded_merge:.0f} mm at worst")
    _look_over(figure, "10-how-wrong-a-width-can-be.png")
    save(figure, "10-how-wrong-a-width-can-be.png")


# --------------------------------------------------------------------------- #
# 5. read the brackets before the ranking
# --------------------------------------------------------------------------- #

def figure_read_the_brackets() -> None:
    """Every solution's crowded score with the spread of its five blocks.

    The chapter claims this solution is the only one standing clear of the group
    on crowded tables. That is a claim about where the brackets fall, so it is a
    claim a column of numbers states badly and a row of ranges states exactly.
    """
    scored = json.loads((RESULTS / "results-averaged-crowded.json").read_text())

    mine = scored[MINE]
    others = [key for key in SOLUTIONS if key != MINE]
    assert all(mine["found_per_100"] > scored[key]["found_per_100"] for key in others), \
        "this solution is supposed to lead the crowded table"
    assert all(mine["found_per_100_lowest"] > scored[key]["found_per_100"] for key in others), \
        "its worst block is supposed to beat every other solution's average"

    rows = sorted(SOLUTIONS, key=lambda key: scored[key]["found_per_100"])
    figure, axis = new(12.2, 5.0)
    bare(axis)
    axis.set_xlim(-3.0, 103.0)
    axis.set_ylim(-1.15, len(rows) + 0.75)

    for place, key in enumerate(rows):
        card = scored[key]
        colour = GOOD if key == MINE else MUTED
        axis.plot([card["found_per_100_lowest"], card["found_per_100_highest"]],
                  [place, place], color=colour, lw=3.0, solid_capstyle="round", zorder=4)
        axis.scatter([card["found_per_100"]], [place], s=58, color=colour,
                     edgecolor="white", linewidth=0.8, zorder=5)
        note(axis, 0.0, place + 0.30, SOLUTIONS[key],
             colour=INK if key == MINE else MUTED, va="bottom",
             weight="bold" if key == MINE else "normal")
        note(axis, card["found_per_100_highest"] + 1.6, place,
             f"{card['found_per_100']:.1f}", colour=colour, va="center",
             weight="bold" if key == MINE else "normal")

    floor = 86.4   # bench/floor.py over the same five blocks; the README carries it
    axis.axvline(floor, color=INK, lw=1.2, ls=(0, (5, 3)), zorder=3)
    note(axis, floor - 2.0, len(rows) + 0.05,
         f"the floor, {floor}: a glass standing wholly behind another is in no picture",
         colour=INK, ha="right", va="bottom")

    for mark in (0, 25, 50, 75, 100):
        axis.plot([mark, mark], [-0.72, -0.78], color=INK, lw=1.0, zorder=3)
        note(axis, mark, -0.84, str(mark), colour=INK, ha="center", va="top")
    axis.plot([0.0, 100.0], [-0.72, -0.72], color=INK, lw=1.0, zorder=3)

    axis.set_title(
        "Crowded tables: the average of five blocks, and how far the blocks spread",
        fontsize=TITLE_SIZE, color=INK, pad=12,
    )
    figure.tight_layout()
    figure.text(
        0.5, -0.02,
        "Glasses found per 100 put out. The bar runs from the lowest block to the highest, and "
        "four of the six overlap each other completely.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    print(f"  brackets: this solution {mine['found_per_100']} "
          f"({mine['found_per_100_lowest']} to {mine['found_per_100_highest']})")
    _look_over(figure, "10-read-the-brackets.png")
    save(figure, "10-read-the-brackets.png")


def main() -> None:
    figure_no_rectangle_to_escape()
    figure_the_overlap_number()
    figure_who_owns_a_contested_pixel()
    figure_how_wrong_a_width_can_be()
    figure_read_the_brackets()


if __name__ == "__main__":
    main()
