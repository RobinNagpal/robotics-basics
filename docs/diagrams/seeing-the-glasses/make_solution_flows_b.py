"""The flow charts for solutions 4, 5 and 6 of this book.

Each of the three solutions has a chapter, and the chapter opens with a document
called "what it is". A reader who looks at the two pictures drawn here for that
solution should be able to say what the solution does, end to end, without
reading the prose, because the same two pictures also stand alone on that
solution's short page in the six-solutions chapter.

The pairing is the same in all three cases: one chart for what the solution does
on a run, and one chart for the single structural fact the solution exists to
demonstrate.

    finetuned-flow-what-it-does.png          the training phase and the run, in
                                             one chart, because solution 4 is
                                             the borrowed model with a training
                                             step put in front of it.
    finetuned-flow-what-training-changes.png what the training moved, beside what
                                             it left exactly as it was.
    keeper-flow-what-it-does.png             the run, split by which half is
                                             borrowed whole and which half is
                                             fitted in this cell.
    keeper-flow-fitting-the-keeper.png       where the keeper's training labels
                                             come from, and which step of the
                                             fitting actually costs anything.
    transformer-flow-what-it-does.png        the run, from the grey picture to
                                             one mask per glass, through the
                                             fixed array of queries.
    transformer-flow-set-prediction.png      the older shape beside this one, and
                                             the two things set prediction
                                             removes.

Every number written on these pictures is read out of
``code/src/08_seeing-the-glasses/`` rather than from the prose; the constant each
one comes from is named in a comment beside it below. The number of queries the
transformer carries is not one of those constants, so no chart here states it.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_solution_flows_b.py
"""

from __future__ import annotations

import matplotlib.colors as mcolors
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    KIND_NARROWEST,
    KIND_WIDEST,
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

# ------------------------------------------------------------------ the numbers
#
# Read out of the code. The comment after each one says which constant it is, so
# that a reader can check it in one step.

# code/src/08_seeing-the-glasses/04-yolo-fine-tuned/yolo_fine_tuned.py
YOLO_MODEL = "yolo26n-seg.pt"       # MODEL
YOLO_BAR = 0.25                     # CONFIDENCE
YOLO_OVERLAP = 0.7                  # OVERLAP

# code/src/08_seeing-the-glasses/bench/masks_to_glasses.py
SPREAD = 95                         # SPREAD

# code/src/08_seeing-the-glasses/05-sam2-with-a-keeper/sam_keeper.py
KEEPER_MEASUREMENTS = 8             # len(MEASUREMENTS)
POINTS_ACROSS_SMALLEST = 3          # POINTS_ACROSS_SMALLEST
GOOD_ENOUGH = 0.8                   # GOOD_ENOUGH
STEADY = 0.92                       # STEADY
DUPLICATE = 0.7                     # DUPLICATE
MOSTLY = 0.5                        # MOSTLY
ROUNDS, DEPTH = 60, 3               # ROUNDS, DEPTH
FOLDS = 3                           # FOLDS
SURE_ONE_GLASS = 0.7                # SURE_ONE_GLASS
SURE_NOT_ONE_GLASS = 0.3            # SURE_NOT_ONE_GLASS

# What the two halves of a training run measured on this machine, from
# 05-sam2-with-a-keeper/README.md. The strip below is drawn to this scale.
PROPOSALS_SECONDS = 273.0           # the borrowed model over 36 training pictures
FIT_SECONDS = 1.0                   # fitting the keeper: under a second

# code/src/08_seeing-the-glasses/06-rf-detr-fine-tuned/rf_detr_seg.py
DETR_SIZE = "RFDETRSegNano"         # SIZE
FILLED = 0.5                        # FILLED

# code/src/08_seeing-the-glasses/work_cell/work_cell/glasses/shapes.py,
# KIND_RANGES["tapered_glass"]["rim_diameter"], in millimetres. The same two
# numbers diagram_style already carries for the rest of this book's pictures.
NARROWEST_MM = int(KIND_NARROWEST)
WIDEST_MM = int(KIND_WIDEST)


# --------------------------------------------------------------------------- #
# the drawing helpers
#
# The same approach as make_examiner_flows.py: rounded boxes with centred text,
# arrows between them, a coloured band behind a run of boxes to say who owns
# them, and captions in the margin. The one addition is that a box's height is
# computed from the number of lines its text holds and from how many points of
# the page one unit of the panel is worth, so that no box can be shorter than
# the words inside it. _audit then measures the drawn result and complains if a
# word has landed outside its box or on top of another word.
# --------------------------------------------------------------------------- #

_PT: dict[str, float] = {}      # points of page per unit of the panel
_PAIRS: list[tuple] = []        # (text artist, box patch), for the audit
_SOLID: list = []               # shapes that must not overlap each other
_FREE: list = []                # captions that must not land on any shape

LINE = 1.45                     # line spacing, as in make_examiner_flows
PAD_PT = 7.0                    # blank space wanted above and below the words


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill.

    Blending with white rather than setting an alpha, because these fills sit on
    top of each other and a stack of transparent fills darkens.
    """
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


def _panel(figure, axis, xlim=(0.0, 100.0), ylim=(0.0, 100.0)) -> None:
    bare(axis)
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    _PAIRS.clear()
    _SOLID.clear()
    _FREE.clear()
    inches_wide, inches_high = figure.get_size_inches()
    place = axis.get_position()
    _PT["x"] = 72.0 * inches_wide * place.width / (xlim[1] - xlim[0])
    _PT["y"] = 72.0 * inches_high * place.height / (ylim[1] - ylim[0])


def _height(text: str, size: float = NOTE_SIZE) -> float:
    """How tall a box has to be, in panel units, to hold this text."""
    lines = text.count("\n") + 1
    points = (lines - 1) * size * LINE + size * 1.2 + 2.0 * PAD_PT
    return points / _PT["y"]


def _box(
    axis,
    x,
    y,
    width,
    text,
    *,
    height=None,
    edge=INK,
    face=PAPER,
    size=NOTE_SIZE,
    ink=INK,
    weight="normal",
    lw=1.2,
) -> float:
    """A rounded box with centred text, given its centre. Returns its height."""
    height = _height(text, size) if height is None else height
    patch = FancyBboxPatch(
        (x - width / 2.0, y - height / 2.0),
        width,
        height,
        boxstyle="round,pad=0.4,rounding_size=1.2",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
        zorder=3,
    )
    axis.add_patch(patch)
    _SOLID.append(patch)
    label = axis.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=ink,
        weight=weight,
        linespacing=LINE,
        zorder=5,
    )
    _PAIRS.append((label, patch))
    return height


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
          weight="normal", free=True) -> None:
    label = axis.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=size,
        color=colour,
        weight=weight,
        linespacing=LINE,
        zorder=7,
    )
    if free:
        _FREE.append(label)


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
        x + 2.6,
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


def _stack(
    axis,
    x,
    width,
    top,
    items,
    *,
    gap=3.6,
    size=NOTE_SIZE,
    edge=INK,
    face=PAPER,
    lw=1.2,
    arrow_colour=INK,
    arrows=True,
) -> float:
    """A column of boxes running downwards, joined by arrows. Returns its foot."""
    y = top
    previous = None
    for text in items:
        height = _height(text, size)
        centre = y - height / 2.0
        _box(axis, x, centre, width, text, height=height, edge=edge, face=face,
             size=size, lw=lw)
        if previous is not None and arrows:
            _arrow(axis, (x, previous), (x, centre + height / 2.0 + 0.5),
                   colour=arrow_colour)
        previous = centre - height / 2.0 - 0.5
        y = centre - height / 2.0 - gap
    return y + gap


def _measure(items, *, gap=3.6, size=NOTE_SIZE) -> float:
    """How tall the column those items make will be, in panel units."""
    return sum(_height(text, size) for text in items) + gap * (len(items) - 1)


def _audit(figure, axis, name: str) -> None:
    """Look for the two faults a glance at the PNG can miss.

    A word outside the box it belongs to, and two pieces of text sharing the
    same patch of page. Both are measured on the drawn figure rather than
    guessed at, and both are printed rather than raised, so that the picture is
    still written and can be looked at beside the complaint.
    """
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    faults = []

    for label, patch in _PAIRS:
        words = label.get_window_extent(renderer)
        room = patch.get_window_extent(renderer)
        if (words.x0 < room.x0 - 0.5 or words.x1 > room.x1 + 0.5
                or words.y0 < room.y0 - 0.5 or words.y1 > room.y1 + 0.5):
            faults.append(
                f"  text spills its box: {label.get_text().splitlines()[0][:52]!r}"
            )

    def clashes(a, b, room=1.0):
        return (min(a.x1, b.x1) - max(a.x0, b.x0) > room
                and min(a.y1, b.y1) - max(a.y0, b.y0) > room)

    texts = [t for t in axis.texts if t.get_text().strip()]
    drawn = [(t, t.get_window_extent(renderer)) for t in texts]
    for i, (one, a) in enumerate(drawn):
        for two, b in drawn[i + 1:]:
            if clashes(a, b):
                faults.append(
                    f"  text over text: {one.get_text().splitlines()[0][:34]!r}"
                    f" and {two.get_text().splitlines()[0][:34]!r}"
                )

    shapes = [(p, p.get_window_extent(renderer)) for p in _SOLID]
    owner = {id(patch): label for label, patch in _PAIRS}
    for i, (one, a) in enumerate(shapes):
        for two, b in shapes[i + 1:]:
            if clashes(a, b, room=2.0):
                here = owner.get(id(one))
                there = owner.get(id(two))
                faults.append(
                    "  box over box: "
                    f"{(here.get_text().splitlines()[0][:30] if here else 'a shape')!r}"
                    f" and {(there.get_text().splitlines()[0][:30] if there else 'a shape')!r}"
                )
    for label in _FREE:
        a = label.get_window_extent(renderer)
        for patch, b in shapes:
            if clashes(a, b, room=2.0):
                faults.append(
                    f"  caption over a box: {label.get_text().splitlines()[0][:40]!r}"
                )
                break

    if faults:
        print(f"{name}: {len(faults)} thing(s) to fix")
        print("\n".join(faults))


# --------------------------------------------------------------------------- #
# Solution 4, the same model fine-tuned
# --------------------------------------------------------------------------- #


def finetuned_what_it_does() -> None:
    """The training phase and the run, in one chart.

    This solution is the borrowed model with a training step put in front of it,
    so a chart of the run alone would draw solution 3 and leave out the only
    thing that differs. The two phases are therefore two bands of one picture,
    and the fitted weights are the one thing that passes between them.
    """
    figure, axis = new(10.4, 9.0)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 53.0, 80.0

    training = [
        "Take the training half of the examiner's arrangements, and its answer key",
        "Turn the key into labels: one mask per glass, all under one class",
        "Replace the borrowed list of everyday categories with the single class \"glass\"",
        f"Continue training from the downloaded weights, {YOLO_MODEL}, on this cell's pictures",
    ]
    run = [
        "One grey picture goes in",
        "Back comes a box, a confidence number and an outline per object",
        f"Discard a candidate covering more than {YOLO_OVERLAP} of a better-scoring one",
        f"Keep the outlines whose confidence reaches the bar of {YOLO_BAR}",
    ]

    bridge = "the fitted weights"
    result = "Each kept outline is one glass's mask."

    # The layout is computed before anything is drawn, so that the two bands can
    # be sized from the boxes that go in them rather than guessed at.
    top = 95.0
    train_h = _measure(training)
    bridge_h = _height(bridge, LABEL_SIZE)
    run_h = _measure(run)
    result_h = _height(result, LABEL_SIZE)

    train_top = top
    train_foot = train_top - train_h
    bridge_centre = train_foot - 5.0 - bridge_h / 2.0
    run_top = bridge_centre - bridge_h / 2.0 - 5.0
    run_foot = run_top - run_h
    result_centre = run_foot - 5.0 - result_h / 2.0

    _band(axis, 2.0, train_foot - 1.5, 96.0, train_h + 3.0, GOOD,
          "once, before any run: the training")
    _band(axis, 2.0, result_centre - result_h / 2.0 - 1.5, 96.0,
          run_top - result_centre + result_h / 2.0 + 3.0, GLASS,
          "every run: one picture at a time")

    _stack(axis, middle, span, train_top, training, edge=GOOD, arrow_colour=GOOD)
    _arrow(axis, (middle, train_foot - 0.5), (middle, bridge_centre + bridge_h / 2.0 + 0.5),
           colour=GOOD)
    _box(axis, middle, bridge_centre, 68.0, bridge, height=bridge_h,
         edge=GOOD, face=_tint(GOOD, 0.80), size=LABEL_SIZE, lw=1.8, weight="bold")
    _arrow(axis, (middle, bridge_centre - bridge_h / 2.0 - 0.5), (middle, run_top - 0.5),
           colour=GOOD)
    _stack(axis, middle, span, run_top, run, edge=GLASS, arrow_colour=GLASS)
    _arrow(axis, (middle, run_foot - 0.5), (middle, result_centre + result_h / 2.0 + 0.5),
           colour=GLASS)
    _box(axis, middle, result_centre, 86.0, result, height=result_h,
         edge=GLASS, face=_tint(GLASS, 0.76), size=LABEL_SIZE, lw=1.8, weight="bold")

    _note(axis, middle, result_centre - result_h / 2.0 - 4.0,
          "The examiner turns each mask into a place and a width, the same way for all six.",
          colour=INK, ha="center")

    axis.set_title(
        "Solution 4: the borrowed model with a training step put in front of it",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "finetuned-flow-what-it-does.png")
    save(figure, "finetuned-flow-what-it-does.png")


def finetuned_what_training_changes() -> None:
    """What the training moved, beside what it left exactly as it was.

    The whole reason this solution exists is that it is one half of a matched
    pair, so the chart that matters most is the one that separates the repairs
    from the inheritances. Two columns, one colour each, and nothing in the
    middle for an eye to get lost in.
    """
    figure, axis = new(12.0, 4.8)
    _panel(figure, axis, (0, 100), (0, 100))

    left, right, wide = 26.0, 74.0, 44.0
    top = 76.0

    moved = [
        "The gap between photographs and this renderer's grey pictures",
        "The naming failures: one class, so no glass is lost to a name",
        "The confidence number, now fitted on this cell's own pictures",
        "The thin part of a glass, covered as well as a glass with no stem",
    ]
    kept = [
        "The coarse outline, built inside a rectangle and then enlarged",
        "The width read off that outline, erring the same way every time",
        "The mask of a partly covered glass: still a slice, still too narrow",
        "A completely hidden glass, which leaves no pixels to find",
    ]

    _note(axis, left, 96.0, "What the training moved",
          colour=GOOD, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, left, 86.0, "what the untrained model got wrong",
          colour=INK, ha="center")
    _note(axis, right, 96.0, "What the training did not touch",
          colour=WARN, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, right, 86.0, "what no amount of training reaches",
          colour=INK, ha="center")

    axis.plot([50.0, 50.0], [10.0, 90.0], color=MUTED, lw=1.0, ls=(0, (5, 4)), zorder=1)

    _stack(axis, left, wide, top, moved, gap=3.0, edge=GOOD,
           face=_tint(GOOD, 0.90), arrows=False)
    _stack(axis, right, wide, top, kept, gap=3.0, edge=WARN,
           face=_tint(WARN, 0.90), arrows=False)

    _note(axis, 50.0, 4.0,
          "Training is the only difference from solution 3, so the gap between them measures it.",
          colour=INK, ha="center", weight="bold")

    axis.set_title(
        "Solution 4: what training this cell's pictures moved, and what it left where it was",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "finetuned-flow-what-training-changes.png")
    save(figure, "finetuned-flow-what-training-changes.png")


# --------------------------------------------------------------------------- #
# Solution 5, a foundation model with a keeper
# --------------------------------------------------------------------------- #


def keeper_what_it_does() -> None:
    """The run, split along the line that defines this solution.

    The whole design is one split: the half of the job that finds shapes is
    borrowed whole and never trained here, and the half that decides what a
    shape is gets replaced. Three bands say which half each step is in, because
    a chart that drew the steps in one colour would hide the only interesting
    thing about them.
    """
    figure, axis = new(10.6, 10.4)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 53.0, 80.0

    before = [
        "Shade the depth readings into a grey picture the borrowed model will take",
    ]
    borrowed = [
        "The picture encoder reads it once",
        f"A grid of point prompts, fine enough for {POINTS_ACROSS_SMALLEST} points across the narrowest glass",
        "Back comes a heap of unnamed outlines: glasses, table, rims, pairs",
        "Score, check for steadiness, drop duplicates: what is left is a proposal",
    ]
    fitted = [
        f"Turn each proposal into {KEEPER_MEASUREMENTS} measurements on the table",
        "The keeper answers: keep it, drop it, or this is more than one glass",
    ]
    arithmetic = [
        f"Check the width against the {NARROWEST_MM} to {WIDEST_MM} mm this kind allows",
    ]
    result = "What survives is the mask of one glass."

    top = 96.0
    gap = 3.6
    before_h = _measure(before)
    borrowed_h = _measure(borrowed)
    fitted_h = _measure(fitted)
    arith_h = _measure(arithmetic)
    result_h = _height(result, LABEL_SIZE)

    # The bands carry their names in rotated text down the left, so a band has to
    # be at least as tall as its own name. The boxes are short now, so the gaps
    # between the bands do that work instead of the boxes.
    before_top = top
    borrowed_top = before_top - before_h - 7.0
    fitted_top = borrowed_top - borrowed_h - 9.0
    arith_top = fitted_top - fitted_h - 13.0
    result_centre = arith_top - arith_h - 7.0 - result_h / 2.0

    _band(axis, 2.0, borrowed_top - borrowed_h - 1.5, 96.0, borrowed_h + 3.0, GLASS,
          "borrowed whole, and never trained here")
    _band(axis, 2.0, fitted_top - fitted_h - 1.5, 96.0, fitted_h + 3.0, GOOD,
          "fitted in this cell")
    _band(axis, 2.0, arith_top - arith_h - 1.5, 96.0, arith_h + 3.0, MUTED,
          "not fitted")

    _stack(axis, middle, span, before_top, before, gap=gap, edge=INK)
    foot = before_top - before_h
    _arrow(axis, (middle, foot - 0.5), (middle, borrowed_top - 0.5))

    _stack(axis, middle, span, borrowed_top, borrowed, gap=gap, edge=GLASS,
           arrow_colour=GLASS)
    _arrow(axis, (middle, borrowed_top - borrowed_h - 0.5), (middle, fitted_top - 0.5),
           colour=GLASS)

    _stack(axis, middle, span, fitted_top, fitted, gap=gap, edge=GOOD,
           arrow_colour=GOOD)
    _arrow(axis, (middle, fitted_top - fitted_h - 0.5), (middle, arith_top - 0.5),
           colour=GOOD)

    _stack(axis, middle, span, arith_top, arithmetic, gap=gap, edge=MUTED)
    _arrow(axis, (middle, arith_top - arith_h - 0.5),
           (middle, result_centre + result_h / 2.0 + 0.5))
    _box(axis, middle, result_centre, 84.0, result, height=result_h,
         edge=GOOD, face=_tint(GOOD, 0.82), size=LABEL_SIZE, lw=1.8, weight="bold")

    _note(
        axis, middle, result_centre - result_h / 2.0 - 4.5,
        "The borrowed model proposes, the keeper sorts, and the geometry disposes.",
        colour=INK, ha="center", weight="bold",
    )
    axis.set_title(
        "Solution 5: the finding is borrowed whole, and only the deciding is fitted here",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "keeper-flow-what-it-does.png")
    save(figure, "keeper-flow-what-it-does.png")


def keeper_fitting_the_keeper() -> None:
    """Where the keeper's training labels come from, and what the fitting costs.

    Two claims in one chart. The labels are arithmetic over the examiner's own
    answer key, so nobody draws anything; and nearly all the cost of fitting the
    keeper is spent running the borrowed model to collect the proposals, not on
    the fit itself. The strip at the foot says the second claim in the one way a
    column of boxes cannot.
    """
    figure, axis = new(10.6, 6.4)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 52.0, 82.0

    steps = [
        "Render the training half of the examiner's arrangements",
        "Run the borrowed model over all of them and collect the proposals",
        f"Measure each proposal the way the keeper will see it: the same {KEEPER_MEASUREMENTS} numbers",
        "Label each one from the answer key, by arithmetic: keep, drop, or more than one",
        "What comes out is a table: one row per proposal, one answer in the last column",
        f"Fit {ROUNDS} rounds of trees, and straighten the score into a probability",
    ]
    costly = 1      # which step in that list is the expensive one
    cheap = len(steps) - 1

    top = 92.0
    gap = 3.6
    heights = [_height(text) for text in steps]
    centres = []
    y = top
    for height in heights:
        centres.append(y - height / 2.0)
        y = y - height - gap
    foot = y + gap

    for index, (text, height, centre) in enumerate(zip(steps, heights, centres)):
        if index == costly:
            edge, face, lw = WARN, _tint(WARN, 0.88), 1.8
        elif index == cheap:
            edge, face, lw = GOOD, _tint(GOOD, 0.86), 1.8
        else:
            edge, face, lw = INK, PAPER, 1.2
        _box(axis, middle, centre, span, text, height=height, edge=edge, face=face, lw=lw)
        if index:
            _arrow(axis, (middle, centres[index - 1] - heights[index - 1] / 2.0 - 0.5),
                   (middle, centre + height / 2.0 + 0.5))

    _note(axis, 4.0, centres[costly], "nearly all\nof the cost",
          colour=WARN, ha="center", weight="bold")
    _note(axis, 4.0, centres[cheap], "seconds",
          colour=GOOD, ha="center", weight="bold")

    # The strip: which step the time goes into, drawn to the two measured times.
    # The fit is so much smaller that its share is under half a percent of the
    # strip, so it is drawn at a floor width and the caption gives both numbers.
    strip_left, strip_width, strip_h = 11.0, 82.0, 5.0
    strip_y = foot - 15.0
    total = PROPOSALS_SECONDS + FIT_SECONDS
    fit_share = FIT_SECONDS / total
    fit_width = max(strip_width * fit_share, 1.2)   # a floor, or it would vanish
    proposals_width = strip_width - fit_width
    _note(axis, 52.0, foot - 6.0, "Where the time goes in one training run",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")
    axis.add_patch(
        Rectangle((strip_left, strip_y), proposals_width, strip_h,
                  facecolor=_tint(WARN, 0.80), edgecolor=WARN, lw=1.4, zorder=3)
    )
    axis.add_patch(
        Rectangle((strip_left + proposals_width, strip_y), fit_width, strip_h,
                  facecolor=_tint(GOOD, 0.74), edgecolor=GOOD, lw=1.4, zorder=3)
    )
    _note(axis, strip_left + proposals_width / 2.0, strip_y + strip_h / 2.0,
          f"running the borrowed model to collect the proposals: {PROPOSALS_SECONDS:.0f} s",
          colour=INK, ha="center", weight="bold")
    _note(axis, strip_left + strip_width, strip_y + strip_h + 1.4,
          f"the fit: under {FIT_SECONDS:.0f} s", colour=GOOD, ha="right", va="bottom",
          weight="bold")
    _note(axis, 52.0, strip_y - 2.6,
          f"Drawn to the two measured times. The fit is {100.0 * fit_share:.1f} per cent of the run, "
          "too thin to see, so it is drawn wider than it is.",
          colour=MUTED, ha="center", va="top")

    axis.set_title(
        "Solution 5: where the keeper's training labels come from, and which step costs the time",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "keeper-flow-fitting-the-keeper.png")
    save(figure, "keeper-flow-fitting-the-keeper.png")


# --------------------------------------------------------------------------- #
# Solution 6, a transformer segmenter fine-tuned
# --------------------------------------------------------------------------- #


def transformer_what_it_does() -> None:
    """The run, from the grey picture to one mask per glass.

    The chart has a drawing of the queries beside the chain, because the fixed
    array of slots is the one part of this solution that a column of sentences
    describes badly. The array is drawn with its tail trailing off, because how
    many queries the model carries is not one of the constants in this
    project's code and no number for it is invented here.
    """
    figure, axis = new(11.6, 6.6)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 25.0, 44.0

    steps = [
        "One grey picture goes in",
        "The model's body describes every part of it",
        "A fixed number of queries read that description",
        "Each query returns a class, a rectangle and a mask",
        f"A query whose class answer is below {FILLED} says \"nothing\"",
        "Each surviving mask is one glass",
    ]

    top = 82.0
    foot = _stack(axis, middle, span, top, steps, gap=3.2, edge=GLASS, arrow_colour=GLASS)

    _box(
        axis, middle, foot - 7.0, span,
        "One mask per glass, handed to the examiner",
        edge=GLASS, face=_tint(GLASS, 0.76), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    # ---- the fixed array of slots, drawn beside the chain
    centre = 74.0
    _note(axis, centre, 84.0, "What the queries hand back is an array of slots",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")
    _note(axis, centre, 80.0,
          "The same length for every picture, and never added to or removed from.",
          colour=INK, ha="center", va="top")

    slot_x, slot_w, slot_h = 52.0, 44.0, 4.6
    rows = [
        ("query 1: glass, and a mask", GOOD),
        ("query 2: glass, and a mask", GOOD),
        ("query 3: glass, and a mask", GOOD),
        ("query 4: nothing", MUTED),
        ("query 5: nothing", MUTED),
    ]
    for index, (text, colour) in enumerate(rows):
        y = 68.0 - index * (slot_h + 1.6)
        box = Rectangle((slot_x, y - slot_h), slot_w, slot_h,
                        facecolor=_tint(colour, 0.84), edgecolor=colour, lw=1.4, zorder=3)
        axis.add_patch(box)
        _SOLID.append(box)
        _note(axis, slot_x + slot_w / 2.0, y - slot_h / 2.0, text,
              colour=INK, ha="center", free=False)
    _note(axis, slot_x + slot_w / 2.0, 68.0 - 5 * (slot_h + 1.6) + 1.0,
          "and so on, to the end of the array",
          colour=MUTED, ha="center", va="top")

    # ---- where the numbers come from
    # Where the weights and the labels come from used to be two more boxes down
    # here. They are a third idea in a picture that already holds two, and they
    # are prose in the document now.

    axis.set_title(
        "Solution 6: one picture in, one mask per glass out, through a fixed array of queries",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "transformer-flow-what-it-does.png")
    save(figure, "transformer-flow-what-it-does.png")


def transformer_set_prediction() -> None:
    """What set prediction removes, drawn as the older shape against this one.

    Two columns, because the claim is a difference rather than a sequence. The
    row across the foot carries the second consequence, which is the one the
    rest of this solution's chapter rests on: a mask predicted over the whole
    picture has somewhere to grow into.
    """
    figure, axis = new(12.4, 5.0)
    _panel(figure, axis, (0, 100), (0, 100))

    left, right, wide = 26.0, 74.0, 44.0
    top = 76.0

    older = [
        "Propose many candidate rectangles",
        "Score them all: one glass comes back as a cluster of claims",
        "Prune the cluster: keep the best, discard what overlaps it",
        "That needs a number saying how much overlap is too much",
    ]
    here = [
        "Carry a fixed number of queries, the same every picture",
        "In training, match the filled slots to the real glasses one to one",
        "Tell every query left over that the answer was \"nothing\"",
        f"No pruning, and no overlap number: only {FILLED}, the bar for a filled slot",
    ]

    _note(axis, left, 96.0, "The older shape: propose, score, then prune",
          colour=WARN, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, right, 96.0, "This model: one set of answers, matched one to one",
          colour=GOOD, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, left, 86.0, "a list that grows and is then cut down",
          colour=INK, ha="center")
    _note(axis, right, 86.0, "a fixed array of slots, declared once",
          colour=INK, ha="center")

    axis.plot([50.0, 50.0], [10.0, 90.0], color=MUTED, lw=1.0, ls=(0, (5, 4)), zorder=1)

    _stack(axis, left, wide, top, older, gap=3.0, edge=WARN,
           face=_tint(WARN, 0.90), arrow_colour=WARN)
    _stack(axis, right, wide, top, here, gap=3.0, edge=GOOD,
           face=_tint(GOOD, 0.90), arrow_colour=GOOD)

    # The second consequence — that a mask computed over the whole picture has
    # somewhere to grow into — used to sit under this comparison as a second row
    # of boxes. It is a different idea and it is prose in the document now.
    _note(axis, 50.0, 4.0,
          "The duplicates are trained out of the model rather than pruned out of its output.",
          colour=INK, ha="center", weight="bold")

    axis.set_title(
        "Solution 6: what set prediction removes",
        fontsize=TITLE_SIZE, color=INK, pad=14,
    )
    _audit(figure, axis, "transformer-flow-set-prediction.png")
    save(figure, "transformer-flow-set-prediction.png")


def main() -> None:
    finetuned_what_it_does()
    finetuned_what_training_changes()
    keeper_what_it_does()
    keeper_fitting_the_keeper()
    transformer_what_it_does()
    transformer_set_prediction()


if __name__ == "__main__":
    main()
