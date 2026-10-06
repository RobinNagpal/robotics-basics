"""The four flow charts and sketches for the test bench document.

The document beside these pictures argues one thing above all: the examiner owns
every step of a run except one, and the one step it does not own is the mask. A
reader who believes that can read a difference between two scorecards as a
difference between two masks, and a reader who does not cannot read the results
at all. These pictures are drawn to make that argument visible.

    03-what-the-examiner-does.png    the whole run as one chain, in three bands,
                                     with the single box a solution owns picked
                                     out between two named hand-over points.
    03-what-must-come-back.png       the record per glass, with the fields the
                                     solution supplies separated from the fields
                                     the examiner computes.
    03-the-floor.png                 a solution's masks and the examiner's own
                                     id masks through the one arithmetic, which
                                     is what makes the floor of error readable.
    03-the-asserted-pixel-trap.png   why a mask that claims pixels the camera
                                     never saw must say which ones, drawn
                                     side-on with the measured cost beside it.

Every box here holds a phrase rather than a sentence. The explanation belongs in
the prose under the picture, and a chart whose boxes have to be read as
paragraphs is slower than the paragraph it replaced.

Every number written into these pictures comes out of
``code/src/08_seeing-the-glasses/``:

* the number of stations and the survey height from ``bench/data.py``, which
  gets them from ``work_cell/arm/dimensions.py``;
* the floor itself, and what naming the asserted pixels is worth, from
  ``bench/results-floor.json`` and ``bench/results-floor-crowded.json``.

The glass sizes in the side-on sketch are the shared cast from
``diagram_style``, so the tall glass and the short one are two real sizes of the
one kind rather than two shapes chosen to make the drawing work.

The layout works in one unit of height per line of text, so a box's height is
its line count plus padding and no text can spill out of it. The figure's height
in inches follows from the number of units the content uses, which is what keeps
a figure from being much larger than what it holds.

``_audit`` then measures the drawn figure and prints anything a glance can miss:
words outside the box they belong to, two pieces of text sharing a patch of page,
two boxes on top of each other, and a caption landing on a box. It prints nothing
now, and a chart should not be committed while it prints anything.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_examiner_flows.py
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
    SHORT_A,
    TALL_A,
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

STATIONS = 3                           # bench/data.stations() returns three
SURVEY_MM = 450                        # mm; SURVEY_HEIGHT in arm/dimensions.py

# bench/results-floor.json, "exact visible masks" on the spawned layouts.
FLOOR_GLASSES = 100
FLOOR_MEDIAN_MM = 6.3
FLOOR_WORST_MM = 46.5

# bench/results-floor-crowded.json, "one glass at a time".
HIDDEN_GLASSES = 133
NAMED_MM = 12.2
FED_IN_MM = 46.1

# The two glasses the side-on sketch draws, in millimetres, from the shared cast.
TALL_MM, TALL_RIM_MM = TALL_A
SHORT_MM, SHORT_RIM_MM = SHORT_A
SEPARATION_MM = 150.0     # MIN_SEPARATION in work_cell/glasses/spawn.py


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
    # How much taller than wide a unit is, so a drawing can keep its proportions.
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


class Chain:
    """A column of boxes running down the chart, each as tall as its own text.

    The cursor starts at the top and moves down as things are added, so nothing
    has to be positioned by hand and no box can be made shorter than the words
    inside it. ``extents`` keeps every box's top and bottom, so a band can be
    drawn around a run of them once their heights are known.
    """

    def __init__(self, axis, top: float, centre: float, width: float,
                 chain_x: float | None = None):
        self.axis = axis
        self.y = top
        self.centre = centre
        self.width = width
        self.chain_x = centre if chain_x is None else chain_x
        self.extents: list[tuple[float, float]] = []

    def box(self, text: str, *, link=False, gap=GAP, width=None, **kw) -> tuple[float, float]:
        """One box. ``link`` draws the arrow down from the box above it."""
        width = self.width if width is None else width
        outer = _height(text)
        if link and self.extents:
            _arrow(self.axis, (self.chain_x, self.extents[-1][1]), (self.chain_x, self.y))
        _box(self.axis, self.centre, self.y - outer / 2.0, width, text, **kw)
        self.extents.append((self.y, self.y - outer))
        self.y -= outer + gap
        return self.extents[-1]

    def note(self, text: str, *, gap=GAP, x=None, ha="center", **kw) -> float:
        lines = text.count("\n") + 1
        middle = self.y - lines / 2.0
        _note(self.axis, self.centre if x is None else x, middle, text, ha=ha, **kw)
        self.y -= lines + gap
        return middle

    def arrow(self, length=2.6, **kw) -> None:
        _arrow(self.axis, (self.chain_x, self.y), (self.chain_x, self.y - length), **kw)
        self.y -= length + GAP

    def skip(self, units: float) -> None:
        self.y -= units

    def beside(self, text: str, x: float, *, rise: float = GAP / 2.0, **kw) -> None:
        """A one-line caption in the gap the cursor is sitting in, off to a side.

        ``rise`` lifts the caption above the cursor. A band drawn round the box
        below starts a little above that box, so a caption left at the default
        height has the band's own edge ruled through it.
        """
        _note(self.axis, x, self.y + rise, text, **kw)


# --------------------------------------------------------------------------- #
# 1. the whole run, and the one step of it a solution owns
# --------------------------------------------------------------------------- #


def what_the_examiner_does() -> None:
    """Every step of a run, in three bands: the examiner, the solution, the
    examiner again.

    The chart exists for the separation rather than for the sequence. A reader
    who counts the boxes in each band has the document's central claim: the
    examiner owns every step but one, so a difference between two scorecards is
    a difference between two sets of masks.
    """
    figure, axis, _ = _figure(9.6, 37.0)
    flow = Chain(axis, 35.5, 54.0, 68.0, chain_x=27.0)

    flow.box("Draws an arrangement: four to six glasses of one kind")
    flow.box(
        f"Parks the camera at {STATIONS} stations, {SURVEY_MM} mm above the table, and renders\n"
        "a grey picture, a depth reading, a camera pose and an id image",
        link=True,
    )

    flow.skip(3.2)
    flow.beside(
        "Hand-over 1: the grey picture, the depth reading, the camera's pose",
        31.0, rise=2.0, colour=INK, weight="bold",
    )
    flow.box(
        "Turns those into one mask per glass, and names the pixels it only asserts",
        link=True, edge=GLASS, face=_tint(GLASS, 0.72), size=LABEL_SIZE, lw=1.8,
        weight="bold",
    )

    flow.skip(3.2)
    flow.beside(
        "Hand-over 2: one mask per glass, and whether the picture held it whole",
        31.0, rise=2.0, colour=INK, weight="bold",
    )
    flow.box("Turns each mask into a place on the table and a rough width", link=True)
    flow.box("Matches each report to the glass that owns most of its pixels", link=True)
    flow.box("Counts the outcomes, and measures how far out each reported place is", link=True)
    flow.box(
        "One scorecard, marked the same way for every solution",
        link=True, size=LABEL_SIZE, weight="bold",
    )

    ends = flow.extents
    for first, last, colour, label in (
        (0, 1, MUTED, "the examiner"),
        (2, 2, GLASS, "the solution"),
        (3, 6, MUTED, "the examiner again"),
    ):
        top = ends[first][0] + 0.7
        bottom = ends[last][1] - 0.7
        _band(axis, 5.0, bottom, 92.0, top - bottom, colour, label)

    _note(
        axis, 50.0, flow.y - 0.6,
        "One box in this chain belongs to a solution, so a difference between two scorecards "
        "belongs to the mask.",
        colour=INK, ha="center",
    )

    _title(axis, "What the examiner does, and the one step of it a solution owns")
    _audit(figure, "03-what-the-examiner-does.png")
    save(figure, "03-what-the-examiner-does.png")


# --------------------------------------------------------------------------- #
# 2. what a solution has to return, and what the examiner does with each piece
# --------------------------------------------------------------------------- #


def what_must_come_back() -> None:
    """The record per glass, split by who fills each field in.

    Two of the four fields in a record come from the solution and two are
    computed by the examiner from the first of them. Drawing the record as four
    fields of one colour would hide the whole point, so the fields are grouped by
    their owner and the arithmetic that makes the examiner's two sits between the
    groups.
    """
    figure, axis, _ = _figure(10.0, 32.0)

    top = 29.5
    wide = 44.0
    left = Chain(axis, top, 26.0, wide)
    right = Chain(axis, top, 74.0, wide)

    left.note("One record per glass", colour=INK, size=LABEL_SIZE + 1.0, weight="bold",
              gap=1.0)
    left.box("the mask pixels, with the asserted ones named",
             edge=GLASS, face=_tint(GLASS, 0.72), lw=1.6, gap=1.0)
    left.box("whether the picture held the whole glass",
             edge=GLASS, face=_tint(GLASS, 0.72), lw=1.6, gap=1.0)
    left.note("The solution supplies these two, and only these two.",
              colour=GLASS, weight="bold", gap=1.0)
    left.arrow(colour=GLASS)
    left.box("the examiner's shared arithmetic, run on the mask")
    left.arrow()
    left.box("the place on the table", face=_tint(MUTED, 0.86), edge=MUTED,
             size=LABEL_SIZE, gap=1.0)
    left.box("a rough width of the footprint", face=_tint(MUTED, 0.86), edge=MUTED,
             size=LABEL_SIZE, gap=1.0)
    left.note("The examiner fills these two in from the mask itself.", colour=INK)

    right.note("Beside the records, two honest statements", colour=INK,
               size=LABEL_SIZE + 1.0, weight="bold", gap=1.0)
    right.box("which glasses could not be separated, and why",
              edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.6, gap=1.0)
    right.box("which parts of the table could not be seen at all",
              edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.6, gap=1.0)
    right.note("Neither statement is a list of glasses.", colour=WARN, weight="bold",
               gap=1.0)
    right.arrow(colour=WARN)
    right.box("A reported doubt is counted as a reported doubt.",
              edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6, size=LABEL_SIZE)
    right.note("Saying nothing instead is counted as a miss.", colour=INK)

    # which colour means which owner, said once rather than on every box
    for row, (colour, text) in enumerate((
        (GLASS, "a field the solution supplies"),
        (MUTED, "a field the examiner computes from the mask"),
    )):
        y = right.y - 1.0 - row * 2.2
        axis.add_patch(
            Rectangle(
                (56.0, y - 0.6), 2.6, 1.2,
                facecolor=_tint(colour, 0.78), edgecolor=colour, lw=1.3, zorder=3,
            )
        )
        _note(axis, 60.0, y, text, colour=INK)

    _title(axis, "What must come back from a solution, and what the examiner does with each piece")
    _audit(figure, "03-what-must-come-back.png")
    save(figure, "03-what-must-come-back.png")


# --------------------------------------------------------------------------- #
# 3. the floor of error: two kinds of mask through one arithmetic
# --------------------------------------------------------------------------- #


def the_floor() -> None:
    """The two paths through the one arithmetic.

    A solution's masks and the examiner's own id masks go through the same step,
    because the floor only means anything if both sides of the comparison went
    through identical arithmetic. What comes out on the right is the best the
    step can do from a mask that is exactly right.
    """
    figure, axis, _ = _figure(9.8, 20.0)

    left, right, wide = 27.0, 73.0, 44.0
    top = 18.0

    one = Chain(axis, top, left, wide)
    two = Chain(axis, top, right, wide)

    one.box("A solution's masks", edge=GLASS, face=_tint(GLASS, 0.72),
            size=LABEL_SIZE, lw=1.6, gap=0.0)
    two.box("The examiner's own id masks, as a perfect answer",
            edge=GOOD, face=_tint(GOOD, 0.80), size=LABEL_SIZE, lw=1.6, gap=0.0)
    _arrow(axis, (left, one.y), (left, one.y - 2.2), colour=GLASS)
    _arrow(axis, (right, two.y), (right, two.y - 2.2), colour=GOOD)

    middle = Chain(axis, one.y - 2.2 - 1.0, 50.0, 92.0)
    middle.box("The same shared arithmetic, run the same way on both", gap=0.0)
    _arrow(axis, (left, middle.y), (left, middle.y - 2.2), colour=GLASS)
    _arrow(axis, (right, middle.y), (right, middle.y - 2.2), colour=GOOD)

    out = middle.y - 2.2 - 1.0
    three = Chain(axis, out, left, wide)
    four = Chain(axis, out, right, wide)
    three.box("The method's place and width,\nwhich its scorecard reports",
              edge=GLASS, lw=1.4, gap=1.0)
    four.box(
        f"The floor of error: {FLOOR_MEDIAN_MM} mm out at the middle\n"
        f"glass and {FLOOR_WORST_MM} mm at the worst, over {FLOOR_GLASSES} glasses",
        edge=GOOD, lw=1.4, gap=1.0,
    )

    _note(
        axis, 50.0, min(three.y, four.y) - 0.4,
        "A method close to the floor has little error left that is its own doing.",
        colour=INK, ha="center",
    )

    _title(axis, "The floor of error: two kinds of mask through one arithmetic")
    _audit(figure, "03-the-floor.png")
    save(figure, "03-the-floor.png")


# --------------------------------------------------------------------------- #
# 4. the trap the floor exposes: a mask that asserts pixels
# --------------------------------------------------------------------------- #


def the_asserted_pixel_trap() -> None:
    """Why a mask that claims unseen pixels has to say which ones.

    The sketch is drawn side-on and to scale: the camera sits the survey height
    above the table, the two glasses are the tall and the short end of the one
    kind, and they stand the closest apart the arrangements allow. The line of
    sight to the asserted pixel therefore really does stop on the tall glass's
    rim, which is the whole of the argument.
    """
    units = 32.0
    figure, axis, aspect = _figure(10.0, units)

    k = 0.05                        # units of height per millimetre
    def dy(mm: float) -> float:
        return mm * k

    def dx(mm: float) -> float:
        return mm * k / aspect

    table_y = 4.5
    tall_x = 18.0
    tall_half = dx(TALL_RIM_MM / 2.0)
    short_x = tall_x + dx(SEPARATION_MM)
    short_half = dx(SHORT_RIM_MM / 2.0)
    tall_top = table_y + dy(TALL_MM)
    camera_y = table_y + dy(SURVEY_MM)
    # The camera sits where the ray grazing the tall rim lands on the short
    # glass's middle, which is what the drawing is about.
    camera_x = 2.0 * (tall_x + tall_half) - short_x

    axis.plot([3, 50], [table_y, table_y], color=INK, lw=1.6, zorder=2)
    _note(axis, 3.0, table_y - 1.0, "the table", colour=MUTED, size=NOTE_SIZE - 0.4)

    axis.add_patch(
        Polygon(
            [(camera_x - 1.8, camera_y - 0.9), (camera_x + 1.8, camera_y - 0.9),
             (camera_x + 1.1, camera_y + 0.9), (camera_x - 1.1, camera_y + 0.9)],
            closed=True, facecolor=INK, edgecolor=INK, zorder=5,
        )
    )
    _note(axis, camera_x + 2.6, camera_y, "the camera", colour=INK)

    def tumbler(x, top, half, colour):
        axis.add_patch(
            Polygon(
                [(x - half * 0.78, table_y), (x - half, top),
                 (x + half, top), (x + half * 0.78, table_y)],
                closed=True, facecolor=_tint(colour, 0.55), edgecolor=colour, lw=1.4,
                zorder=4,
            )
        )

    tumbler(tall_x, tall_top, tall_half, MUTED)
    tumbler(short_x, table_y + dy(SHORT_MM), short_half, GLASS)
    _note(axis, tall_x - tall_half - 1.0, table_y + dy(TALL_MM) * 0.55,
          "a tall glass\nin front", colour=INK, ha="right")
    _note(axis, short_x + short_half + 1.2, table_y + dy(SHORT_MM) * 0.6,
          "the short glass\nthe mask is about", colour=GLASS, ha="left")

    # The line of sight to an asserted pixel stops on the tall glass's rim, well
    # above the table the pixel would otherwise have landed on.
    rim = (tall_x + tall_half, tall_top)
    reach = (rim[0] - camera_x) * (rim[1] - table_y) / (camera_y - rim[1])
    ground = (rim[0] + reach, table_y)
    axis.plot([camera_x, rim[0]], [camera_y - 1.0, rim[1]], color=WARN, lw=1.4, zorder=5)
    axis.plot([rim[0], ground[0]], [rim[1], ground[1]], color=WARN, lw=1.1,
              ls=(0, (3, 3)), zorder=5)
    axis.plot(*rim, marker="o", ms=5.5, color=WARN, zorder=6)
    _note(axis, rim[0] + 1.0, rim[1] + 1.1, "the depth reading\nstops here",
          colour=WARN, va="bottom")
    axis.plot(*ground, marker="x", ms=6, mew=1.6, color=WARN, zorder=6)

    _arrow(axis, (ground[0], table_y - 2.6), (rim[0], table_y - 2.6), colour=WARN, lw=1.6)
    _note(axis, ground[0] + 1.4, table_y - 2.6, "the place is dragged this way",
          colour=WARN)

    # ---- the measured cost, beside the sketch
    side = Chain(axis, units - 1.5, 76.0, 44.0)
    side.box(f"Fed in: the place lands {FED_IN_MM} mm out",
             edge=WARN, face=_tint(WARN, 0.86), size=LABEL_SIZE, lw=1.6, gap=1.2)
    side.box(f"Named and left out: {NAMED_MM} mm out instead",
             edge=GOOD, face=_tint(GOOD, 0.86), size=LABEL_SIZE, lw=1.6, gap=1.2)
    side.note(
        "Exact masks on the crowded arrangements,\n"
        f"over the {HIDDEN_GLASSES} glasses something stood in front of.",
        colour=MUTED,
    )
    side.note("So a mask that asserts pixels must say which ones.",
              colour=INK, weight="bold")

    _title(axis, "The trap: a mask that asserts pixels the camera never saw the glass at")
    _audit(figure, "03-the-asserted-pixel-trap.png")
    save(figure, "03-the-asserted-pixel-trap.png")


def main() -> None:
    what_the_examiner_does()
    what_must_come_back()
    the_floor()
    the_asserted_pixel_trap()


if __name__ == "__main__":
    main()
