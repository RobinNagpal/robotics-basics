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
    figure, axis = new(10.4, 13.4)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 53.0, 80.0

    training = [
        "The examiner renders arrangements and, beside every picture, an answer key saying\n"
        "which glass owns each pixel. Only the training half of the arrangements is handed\n"
        "out, so nothing is ever tested on an arrangement it learned from.",

        "Every label is a selection over that key: one glass's mask is the pixels carrying its\n"
        "identity, under a class that is always \"glass\". So an exact mask for every glass\n"
        "costs nothing. Nobody draws an outline, and there is no annotator's mistake in it.",

        "The borrowed model's list of everyday categories is replaced by the single class\n"
        "\"glass\", so the model is no longer asked which everyday object it is looking at. It\n"
        "is asked only where the instances are, and every instance it finds is a glass or\n"
        "is nothing.",

        f"Training continues from the downloaded weights, {YOLO_MODEL}, rather than from\n"
        "random numbers, on this cell's own grey pictures shaded from depth. Most of the\n"
        "weights already sit at values that work, so the training only has to adjust them.",
    ]
    run = [
        "One grey picture shaded from depth goes in. A survey is three of them, from three\n"
        "overlapping stations, and each is asked about on its own.",

        "The fitted model returns, for each thing it believes it has found, a box, a number\n"
        "saying how sure it is, and an outline of the pixels inside that box that belong to\n"
        "the object.",

        f"A candidate covering more than {YOLO_OVERLAP} of a better-scoring candidate is discarded as\n"
        "the same object arriving twice.",

        f"The outlines whose confidence number reaches the bar of {YOLO_BAR} are kept. Below it a\n"
        "candidate is ignored.",
    ]

    bridge = (
        "the fitted weights: a file that describes this cell's grey pictures\n"
        "and nothing else"
    )
    result = "Each kept outline is one mask of one glass, and that is what this solution reports."

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

    _note(
        axis, middle, result_centre - result_h / 2.0 - 5.0,
        "The examiner's shared arithmetic then turns each mask into a place on the table and a rough width,\n"
        f"as the {SPREAD}th percentile of how far the mask's cloud of points reaches from its axis. That step belongs\n"
        "to the examiner and is the same for all six solutions.",
        colour=INK, ha="center",
    )

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
    figure, axis = new(13.2, 8.2)
    _panel(figure, axis, (0, 100), (0, 100))

    left, right, wide = 26.0, 74.0, 44.0
    top = 82.0

    moved = [
        "The gap between the two kinds of picture closes. The model was\n"
        "fitted on photographs, where a glass is transparent, carries a\n"
        "highlight on its rim and bends what is behind it. It is now fitted on\n"
        "the grey pictures this renderer draws, where a glass is an opaque\n"
        "shape and a step in brightness is a step in distance. It stops\n"
        "looking for the light passing through a glass and starts\n"
        "recognising the shapes this renderer draws.",

        "The naming failures close. With one class a glass cannot arrive\n"
        "twice under two neighbouring everyday names, and cannot be\n"
        "dropped because the model called it a bowl, a vase or a bottle.",

        "The confidence number now comes from weights fitted on this\n"
        "cell's own pictures, so a bar set on it has a claim to mean\n"
        "something rather than being a knob set by hand.",

        "The thin part of a glass survives. After training the stemmed\n"
        "glass is covered as completely as the two kinds with no stem, so\n"
        "the stem is not where a fitted model loses pixels.",
    ]
    kept = [
        "The shape of the output does not change. The model still computes\n"
        "a short list of coarse pattern images for the whole picture, returns\n"
        "a few weights per object, cuts the weighted sum at a threshold,\n"
        "and enlarges the result to the size of the picture. The outline is\n"
        "built coarsely inside a rectangle and then enlarged, and training\n"
        "cannot make a coarse outline fine.",

        "So the edge of the outline stays approximate, and the width is\n"
        f"read from the edge: the examiner takes it as the {SPREAD}th percentile of\n"
        "how far the mask's points reach from the glass's axis. The\n"
        "enlargement errs the same way each time, so the error in the\n"
        "width does not average away over many glasses.",

        "The mask still marks only the pixels where the camera actually\n"
        "saw the glass. A glass standing partly behind another comes back\n"
        "as a slice cut along one side, so it is reported narrower than it is\n"
        "and standing where no glass stands.",

        "A glass hidden completely behind another stays invisible. It leaves\n"
        "no pixels for anything to find, so no amount of training on this\n"
        "cell's pictures can reach it.",
    ]

    _note(axis, left, 95.0, "What the training moved",
          colour=GOOD, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, left, 89.5,
          "the three failures of the untrained borrowed model,\nand one that was expected and did not happen",
          colour=INK, ha="center")
    _note(axis, right, 95.0, "What the training did not touch",
          colour=WARN, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, right, 89.5,
          "the limits that survive any amount of training, because they\nbelong to the shape of the output or to what the picture never held",
          colour=INK, ha="center")

    axis.plot([50.0, 50.0], [8.0, 85.0], color=MUTED, lw=1.0, ls=(0, (5, 4)), zorder=1)

    _stack(axis, left, wide, top, moved, gap=3.0, edge=GOOD,
           face=_tint(GOOD, 0.90), arrows=False)
    _stack(axis, right, wide, top, kept, gap=3.0, edge=WARN,
           face=_tint(WARN, 0.90), arrows=False)

    _note(
        axis, 50.0, 3.0,
        "Same library, same model and same downloaded weights as the borrowed model that fits nothing. The training is the only\n"
        "difference between the two, so the gap between their two scorecards measures what fine-tuning buys and nothing else.",
        colour=INK, ha="center", weight="bold",
    )

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
    figure, axis = new(10.8, 15.0)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 53.0, 80.0

    before = [
        "The depth readings are shaded into a grey picture, normalised to the range of depth\n"
        "that picture holds, and the single grey channel is repeated across all three colour\n"
        "channels, because the borrowed model takes a photograph.",
    ]
    borrowed = [
        "SAM 2's picture encoder reads that picture once. This is the expensive part, and it\n"
        "runs once per picture rather than once per prompt.",

        "A plain grid of point prompts, aimed at nothing and spread over the whole picture,\n"
        f"goes through the cheap mask decoder. The grid is fine enough to put\n"
        f"{POINTS_ACROSS_SMALLEST} points across the narrowest glass this kind allows.",

        "A heap of outlines of everything comes back: each glass, the table, a rim on its own,\n"
        "two glasses that ran together into one shape. Not one of them carries a name, because\n"
        "this model returns regions and never labels them.",

        f"Scoring, a stability check and duplicate removal cut the heap down to a shortlist of\n"
        f"proposals: the model's own quality estimate must reach {GOOD_ENOUGH}, the mask must change\n"
        f"less than {STEADY} when the cut-off is nudged, and two masks overlapping by more\n"
        f"than {DUPLICATE} are one region arriving twice.",
    ]
    fitted = [
        f"Each proposal's pixels and their depth readings become {KEEPER_MEASUREMENTS} measurements on the\n"
        "table: how its width falls in the range this kind allows, how round it is, how far it\n"
        "stands above the table, how far it sits from the point below the camera, how many\n"
        "prompt points returned it, how much of its outline is a step in depth, its area on\n"
        "the table, and whether another proposal contains it. Every one is a length, a count\n"
        "or a ratio, and not one of them is an address in the picture.",

        f"The keeper reads those measurements and answers keep, drop, or this is more than\n"
        f"one glass. It is {ROUNDS} rounds of trees {DEPTH} questions deep, one set per answer, and its\n"
        f"score is straightened into an honest probability in {FOLDS} folds. Above {SURE_ONE_GLASS} the proposal\n"
        f"is reported, below {SURE_NOT_ONE_GLASS} it is dropped, and between the two the keeper cannot tell,\n"
        "which is a reason to take another picture rather than to guess.",
    ]
    arithmetic = [
        f"A proposal the keeper wants to keep still has its width measured against the {NARROWEST_MM} to\n"
        f"{WIDEST_MM} mm this known kind allows. Outside that range it is not reported as a glass,\n"
        "whatever the keeper said: it becomes a doubtful report carrying its reason. The\n"
        "check is not put to a proposal whose mask reaches the edge of the frame, because\n"
        "there the measured width is part of a width.",
    ]
    result = (
        "The proposals that survive all of that are the masks this solution reports.\n"
        "A proposal the keeper called more than one glass is prompted again with a fresh grid\n"
        "inside it, and if that does not separate it, it is reported as an unseparated pair."
    )

    top = 96.0
    gap = 3.6
    before_h = _measure(before)
    borrowed_h = _measure(borrowed)
    fitted_h = _measure(fitted)
    arith_h = _measure(arithmetic)
    result_h = _height(result, LABEL_SIZE)

    before_top = top
    borrowed_top = before_top - before_h - 5.0
    fitted_top = borrowed_top - borrowed_h - 5.5
    arith_top = fitted_top - fitted_h - 5.5
    result_centre = arith_top - arith_h - 5.0 - result_h / 2.0

    _band(axis, 2.0, borrowed_top - borrowed_h - 1.5, 96.0, borrowed_h + 3.0, GLASS,
          "borrowed whole, and never trained here")
    _band(axis, 2.0, fitted_top - fitted_h - 1.5, 96.0, fitted_h + 3.0, GOOD,
          "fitted in this cell")
    _band(axis, 2.0, arith_top - arith_h - 1.5, 96.0, arith_h + 3.0, MUTED,
          "arithmetic nobody fitted")

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
    _note(
        axis, middle, result_centre - result_h / 2.0 - 9.5,
        "No gradient is ever computed through the borrowed model, no layer of it is replaced, and nothing about this cell reaches\n"
        "its numbers: running it is a forward pass. So it cannot fall out of step with the cell, and there is no way to teach it\n"
        "anything either. Every difficulty peculiar to this cell has to be met before it, in the picture it is handed, or after it,\n"
        "in the keeper.",
        colour=INK, ha="center", va="top",
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
    figure, axis = new(11.0, 11.6)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 52.0, 82.0

    steps = [
        "Render the training half of the examiner's arrangements, the ordinary ones and the\n"
        "crowded ones together. Nothing here is ever an arrangement a score is claimed on.",

        "Run the borrowed model over every one of them and collect the proposals: the picture\n"
        "encoder once per picture, then the whole grid of point prompts through the mask\n"
        "decoder, then the same scoring, stability and duplicate cleanup as at run time.",

        f"Measure each proposal the way the keeper will see it at run time: the same {KEEPER_MEASUREMENTS}\n"
        "lengths, counts and ratios on the table, and nothing measured in pixels.",

        "The examiner's answer key turns a proposal into a label by arithmetic, because the key\n"
        "says which glass owns each pixel. Overlap the proposal with each real glass's pixels:\n"
        f"more than {MOSTLY} of one glass inside it and nothing else is a keep, a proposal spread\n"
        "across two glasses is a more-than-one, and a proposal holding neither is a drop.\n"
        "There is no annotator, so there are none of an annotator's mistakes either.",

        "What comes out is a short table of named numbers: one row per proposal, one column\n"
        "per measurement, and one of three answers in the last column.",

        f"Fit {ROUNDS} rounds of trees {DEPTH} questions deep, one set per answer, and fit the correction\n"
        f"from the raw score to an honest probability in {FOLDS} folds, each fold's correction fitted\n"
        "only on rows the trees behind it never saw. Seconds on an ordinary processor, with\n"
        "no graphics card involved.",
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

    # The strip: which step the time goes into. Drawn by area rather than by a
    # measured length, because this project has no timing of either step to
    # quote, so the strip says so in its own caption.
    strip_y, strip_h = foot - 15.0, 5.0
    _note(axis, 52.0, foot - 6.0, "Where the time goes",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")
    axis.add_patch(
        Rectangle((11.0, strip_y), 70.0, strip_h, facecolor=_tint(WARN, 0.80),
                  edgecolor=WARN, lw=1.4, zorder=3)
    )
    axis.add_patch(
        Rectangle((81.0, strip_y), 12.0, strip_h, facecolor=_tint(GOOD, 0.74),
                  edgecolor=GOOD, lw=1.4, zorder=3)
    )
    _note(axis, 46.0, strip_y + strip_h / 2.0,
          "running the borrowed model to collect the proposals",
          colour=INK, ha="center", weight="bold")
    _note(axis, 87.0, strip_y + strip_h + 1.4, "the fit",
          colour=GOOD, ha="center", va="bottom", weight="bold")
    _note(axis, 52.0, strip_y - 2.4,
          "The borrowed model's weights are large and the keeper's numbers are a rounding error beside them, so the graphics\n"
          "card is busy collecting the proposals and idle during the fit. Drawn to show which step costs; neither part has been\n"
          "timed here, so no length in this strip is a measurement.",
          colour=INK, ha="center", va="top")

    _note(
        axis, 52.0, strip_y - 12.0,
        "So the keeper is cheap to refit and the proposals are expensive to collect, which is why the proposals are\n"
        "collected once and kept. The labels come only from the training half, and the keeper is never run on the answer key.",
        colour=INK, ha="center", weight="bold",
    )

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
    figure, axis = new(12.6, 10.8)
    _panel(figure, axis, (0, 100), (0, 100))

    middle, span = 25.0, 44.0

    steps = [
        "The grey picture shaded from depth goes in, one of the three\n"
        "stations at a time.",

        "The model's body turns that picture into a description of every\n"
        "part of the picture, and almost all of its weights are in this part.",

        "A fixed number of queries read that description. A query is not a\n"
        "rectangle and not a region: it is a small list of numbers the model\n"
        "carries along and updates as it reads the picture, and its job is to\n"
        "ask one question over the whole picture, which is whether there\n"
        "is an object here and which pixels are it.",

        "Each query returns a class, a rectangle, and a mask computed\n"
        "pixel by pixel over the whole picture. The rectangle is a result of\n"
        "the answer rather than a container the answer was built inside.",

        f"A query whose class answer does not reach {FILLED} is reporting\n"
        "\"nothing\", and its slot is dropped.",

        "Each surviving mask is one glass. No step has to cut a joined\n"
        "region apart, because nothing ever treated the joined region as\n"
        "one thing.",
    ]

    top = 86.0
    foot = _stack(axis, middle, span, top, steps, gap=3.2, edge=GLASS, arrow_colour=GLASS)

    _box(
        axis, middle, foot - 9.0, span,
        "One mask per glass, handed to the examiner,\n"
        "which back-projects its pixels with their depth\n"
        "readings and the camera's own pose.",
        edge=GLASS, face=_tint(GLASS, 0.76), size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    # ---- the fixed array of slots, drawn beside the chain
    centre = 74.0
    _note(axis, centre, 88.0, "What the queries hand back is an array of slots",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")
    _note(axis, centre, 85.0,
          "The array is the same length for every picture, declared before training and\n"
          "never changed, and chosen to be comfortably longer than the number of glasses\n"
          "any picture is expected to hold. Every slot is either filled with one object or\n"
          "left empty, and nothing is ever appended to it or removed from it.",
          colour=INK, ha="center", va="top")

    slot_x, slot_w, slot_h = 52.0, 44.0, 4.6
    rows = [
        ("query 1: glass, and a mask over the whole picture", GOOD),
        ("query 2: glass, and a mask over the whole picture", GOOD),
        ("query 3: glass, and a mask over the whole picture", GOOD),
        ("query 4: nothing, so this slot is dropped", MUTED),
        ("query 5: nothing, so this slot is dropped", MUTED),
    ]
    for index, (text, colour) in enumerate(rows):
        y = 70.0 - index * (slot_h + 1.6)
        box = Rectangle((slot_x, y - slot_h), slot_w, slot_h,
                        facecolor=_tint(colour, 0.84), edgecolor=colour, lw=1.4, zorder=3)
        axis.add_patch(box)
        _SOLID.append(box)
        _note(axis, slot_x + slot_w / 2.0, y - slot_h / 2.0, text,
              colour=INK, ha="center", free=False)
    _note(axis, slot_x + slot_w / 2.0, 70.0 - 5 * (slot_h + 1.6) + 1.0,
          "and so on, to the end of the array",
          colour=MUTED, ha="center", va="top")

    # ---- where the numbers come from
    _box(
        axis, centre, 26.0, 46.0,
        f"Where the numbers come from. The model is {DETR_SIZE},\n"
        "the smallest of its family, and it arrives already fitted to a\n"
        "large collection of ordinary labelled pictures. Training then\n"
        "continues from those downloaded weights on this cell's own\n"
        "pictures, with the list of classes cut down to the single class\n"
        "\"glass\", so a query's class answer is a choice between\n"
        "\"glass\" and \"nothing\" and nothing else.",
        edge=GOOD, face=_tint(GOOD, 0.90), lw=1.6,
    )
    _box(
        axis, centre, 8.0, 46.0,
        "The labels cost nothing. The examiner renders, beside every\n"
        "picture, an image saying which glass owns each pixel, so one\n"
        "glass's mask is the set of pixels carrying its identity and the\n"
        "class is always \"glass\". Nobody draws a mask by hand, and\n"
        "the labels are handed out only for the training half of the\n"
        "arrangements.",
        edge=GOOD, face=_tint(GOOD, 0.90), lw=1.6,
    )

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
    figure, axis = new(13.4, 10.6)
    _panel(figure, axis, (0, 100), (0, 100))

    left, right, wide = 26.0, 74.0, 44.0
    top = 84.0

    older = [
        "Look over the picture and propose many candidate\n"
        "rectangles that might hold an object. The list has no fixed\n"
        "length: it starts long and is then cut down.",

        "Score every candidate. Several reference rectangles at\n"
        "neighbouring positions really do contain most of one glass,\n"
        "so one object comes back as a cluster of overlapping claims\n"
        "that all score highly.",

        "Reduce the cluster with a step of its own, called non-maximum\n"
        "suppression: sort the claims by score, keep the best, discard\n"
        "every later claim that overlaps a kept one too heavily, and\n"
        "repeat down the list.",

        "That step needs a number saying how much overlap is too\n"
        "much, and it assumes heavy overlap means duplication. In this\n"
        "cell that assumption is awkward, because splay can push one\n"
        "glass's stretched outline right across another's, so two\n"
        "genuinely different glasses can overlap heavily and one of\n"
        "them can be thrown away for looking like a duplicate.",
    ]
    here = [
        "Carry a fixed number of queries. Every query is a slot that is\n"
        "either filled with one object or left empty, and the array is the\n"
        "same length for every picture.",

        "During training the filled slots are matched to the real glasses\n"
        "one to one: each real glass is assigned exactly one query, each\n"
        "query gets at most one real glass, and the pairing chosen is the\n"
        "one that fits best overall.",

        "Every query left over is told that the right answer for it was\n"
        "\"nothing\". A query reporting a glass another query was already\n"
        "matched to is not rewarded for being nearly right, so each query\n"
        "learns to be responsible for at most one glass.",

        "The duplicates are therefore trained out of the model rather\n"
        "than pruned out of its output. There is nothing to prune, and the\n"
        "number saying how much overlap is too much does not exist. The\n"
        f"only number left is {FILLED}, what a query's class answer has to reach\n"
        "for its slot to count as filled.",
    ]

    _note(axis, left, 95.0, "The older shape: propose, score, then prune",
          colour=WARN, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, right, 95.0, "This model: one set of answers, matched one to one",
          colour=GOOD, size=LABEL_SIZE + 2.0, ha="center", weight="bold")
    _note(axis, left, 89.5, "a list that grows and is then cut down",
          colour=INK, ha="center")
    _note(axis, right, 89.5, "a fixed-size array of optional values, declared once",
          colour=INK, ha="center")

    axis.plot([50.0, 50.0], [27.0, 87.0], color=MUTED, lw=1.0, ls=(0, (5, 4)), zorder=1)

    _stack(axis, left, wide, top, older, gap=3.0, edge=WARN,
           face=_tint(WARN, 0.90), arrow_colour=WARN)
    _stack(axis, right, wide, top, here, gap=3.0, edge=GOOD,
           face=_tint(GOOD, 0.90), arrow_colour=GOOD)

    _note(axis, 50.0, 24.0, "The second consequence, and the one the rest of this chapter rests on",
          colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")

    _box(
        axis, left, 13.0, wide,
        "In the older shape the mask is painted on a small grid\n"
        "covering the rectangle and then stretched to the rectangle's\n"
        "size, so it physically cannot reach past that edge. A glass\n"
        "partly covered by the one in front has evidence on one side\n"
        "only, so the rectangle is smaller than the glass, and a mask\n"
        "that should cover the whole glass is clipped by the evidence.",
        edge=WARN, face=_tint(WARN, 0.90), lw=1.6,
    )
    _box(
        axis, right, 13.0, wide,
        "Here the mask is computed over the whole picture from the\n"
        "start, as \"which pixels match this query's description\", so\n"
        "there is no rectangle for it to escape. A mask may claim any\n"
        "pixel in the frame, which is why this is the only one of the six\n"
        "that could be asked for the part of a glass nobody saw: the\n"
        "request changes what the mask is scored against, not its shape.",
        edge=GOOD, face=_tint(GOOD, 0.90), lw=1.6,
    )

    axis.set_title(
        "Solution 6: what set prediction removes, and what a mask over the whole picture allows",
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
