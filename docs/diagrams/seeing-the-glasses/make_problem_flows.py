"""The three flow charts for "what is asked for".

That document states the question all six solutions answer. Three of its claims
are easier to see as a picture than to hold in the head while reading, and
these are the three charts:

    the-three-difficulties.png  the three difficulties in two orders at once,
                                because the most dangerous of them is the last
                                one anybody would notice, and then what each
                                one needs: the pictures already taken, or
                                something those pictures cannot give.
    a-complete-answer.png       the three parts of a complete answer, with the
                                one part that differs between the six solutions
                                separated from the two parts that are the same
                                for all of them, and the reason those two
                                cannot be got at by working harder on pixels.
    what-done-means.png         the three conditions a run has to meet, the two
                                measurements the answers are compared on, why
                                "missed" is the count to watch hardest, and why
                                the mask has to be measured as well as the
                                place.

Every number in these pictures was read out of
``code/src/08_seeing-the-glasses/``:

* the smallest distance between two glass centres, 150 mm, from the layout
  rule in ``bench/render.py``;
* the three stations, the 450 mm survey height and the 120 mm between the two
  pictures of a pair, from ``bench/data.py`` with ``SURVEY_HEIGHT`` and
  ``SURVEY_BASELINE`` in ``work_cell/arm/dimensions.py``;
* the five counts from ``FIND`` in ``bench/marking.py``;
* the 95th percentile that makes the mask-to-place step forgiving, from
  ``SPREAD`` in ``bench/masks_to_glasses.py``.

The box, band, arrow and note helpers follow make_bench_flows.py, so that the
charts of two neighbouring documents look like charts of one book. They are
extended in one way: a box is given its text rather than its height, and works
the height out from how many lines that text has, so that no box is drawn
taller than its words.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_problem_flows.py
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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# ------------------------------------------------------------------ the numbers

MIN_CENTRES_MM = 150     # bench/render.py, the rule the layouts are drawn under
SURVEY_MM = 450          # SURVEY_HEIGHT in work_cell/arm/dimensions.py
BASELINE_MM = 120        # SURVEY_BASELINE in the same file
SPREAD = 95              # bench/masks_to_glasses.SPREAD
COUNTS = "found, missed, merged, split and false"   # bench/marking.FIND

SHOW_FIT = False         # print where the drawing ends, when tuning a figure


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill."""
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


class Sheet:
    """One panel, and the arithmetic that keeps text inside its boxes.

    Everything is drawn in axis units, 0 to 100 across. How tall a line of text
    is in those units depends on the figure's size and on how much of the figure
    the axes actually covers, so both are worked out once here. A box can then
    be asked for by its text instead of by a guessed height, and the guessing
    that leaves a chart with empty margins or with text hanging over an edge
    does not have to happen at all.
    """

    def __init__(self, width: float, height: float):
        self.figure, self.axis = new(width, height)
        self.figure.subplots_adjust(left=0.012, right=0.988, bottom=0.012, top=0.945)
        bare(self.axis)
        self.axis.set_xlim(0, 100)
        self.axis.set_ylim(0, 100)
        box = self.axis.get_position()
        across = width * box.width        # inches the 100 units across cover
        down = height * box.height        # inches the 100 units down cover
        self.line = NOTE_SIZE / 72.0 * 1.45 * (100.0 / down)   # one text line, in units
        self.chars = 17.0 * across / 100.0                     # characters in one unit
        self.gap = 1.15 * self.line       # the usual space between two boxes
        self.low = 100.0                  # the lowest point anything has reached

    # ---------------------------------------------------------------- measuring
    def height_for(self, *texts: str, pad: float = 1.9) -> float:
        lines = max(text.count("\n") + 1 for text in texts)
        return lines * self.line + pad

    def _check(self, width: float, text: str, name: str) -> None:
        room = int(width * self.chars)
        for line in text.split("\n"):
            if len(line) > room:
                print(f"  too wide: {name}: {len(line)} characters, room for {room}")

    def _reached(self, y: float) -> None:
        self.low = min(self.low, y)

    # ----------------------------------------------------------------- drawing
    def box(self, x, y, width, text, *, height=None, edge=INK, face=PAPER,
            size=NOTE_SIZE, ink=INK, weight="normal", lw=1.2, name="box") -> float:
        """A rounded box with centred text, given its centre. Returns its height."""
        tall = self.height_for(text) if height is None else height
        self._check(width, text, name)
        self.axis.add_patch(
            FancyBboxPatch(
                (x - width / 2.0, y - tall / 2.0),
                width,
                tall,
                boxstyle="round,pad=0.3,rounding_size=1.0",
                linewidth=lw,
                edgecolor=edge,
                facecolor=face,
                zorder=3,
            )
        )
        self.axis.text(x, y, text, ha="center", va="center", fontsize=size, color=ink,
                       weight=weight, linespacing=1.45, zorder=5)
        self._reached(y - tall / 2.0 - 0.3)
        return tall

    def band(self, x, y, width, height, colour, label) -> None:
        """A lane of the chart, with its owner's name along the top of it."""
        self.axis.add_patch(
            Rectangle((x, y), width, height, facecolor=_tint(colour, 0.93),
                      edgecolor=colour, linewidth=1.0, zorder=1)
        )
        self.note(x + width / 2.0, y + height - 0.8 * self.line, label,
                  colour=colour if colour != MUTED else INK, size=LABEL_SIZE,
                  ha="center", weight="bold")
        self._reached(y)

    def arrow(self, start, end, *, colour=INK, lw=1.4, dashed=False) -> None:
        self.axis.add_patch(
            FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, linewidth=lw,
                            color=colour, linestyle=(0, (4, 3)) if dashed else "solid",
                            shrinkA=0, shrinkB=0, zorder=6)
        )
        self._reached(min(start[1], end[1]))

    def rule(self, y: float) -> None:
        self.axis.plot([2, 98], [y, y], color=MUTED, lw=0.9, ls=(0, (5, 4)), zorder=1)
        self._reached(y)

    def note(self, x, y, text, *, colour=MUTED, size=NOTE_SIZE, ha="left", va="center",
             weight="normal", rotation=0.0) -> None:
        self.axis.text(x, y, text, ha=ha, va=va, fontsize=size, color=colour, weight=weight,
                       linespacing=1.45, zorder=7, rotation=rotation)
        self._reached(y - (text.count("\n") + 1) * self.line / 2.0)

    def finish(self, title: str, name: str) -> None:
        self.axis.set_title(title, fontsize=TITLE_SIZE, color=INK, pad=10)
        if SHOW_FIT:
            print(f"  {name}: the drawing stops at y = {self.low:.1f}, one line is "
                  f"{self.line:.2f} units")
        save(self.figure, name)


# --------------------------------------------------------------------------- #
# 1. the three difficulties, in both of their orders
# --------------------------------------------------------------------------- #


def three_difficulties() -> None:
    """The three difficulties ranked by danger, against the same three ranked
    by how readily anybody would notice them.

    The document says the order is by danger and that this is not the order of
    noticing. That sentence is the whole reason this chart exists, so the two
    orders are drawn as two lists with lines between them, and the crossings
    are the point. Underneath, each difficulty gets a row with the one question
    that decides what a solution can do about it: whether the pictures already
    taken hold the answer.
    """
    sheet = Sheet(10.0, 8.4)
    line, gap = sheet.line, sheet.gap

    # ------------------------------------------------------ the two orders
    y = 97.0
    sheet.note(50.0, y, "The same three difficulties, put in order twice",
               colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")

    y -= 2.2 * line
    sheet.note(18.0, y, "Most dangerous first", colour=WARN, size=LABEL_SIZE,
               ha="center", weight="bold")
    sheet.note(74.0, y, "Easiest to notice first", colour=GLASS, size=LABEL_SIZE,
               ha="center", weight="bold")

    short = (
        "a glass missing from the\npicture altogether",
        "glasses merging though\nthey stand apart",
        "where the camera is still\nallowed to stand",
    )
    noticed = (
        "glasses merging: one connected shape is\nthere in the picture to be seen",
        "where the camera may stand: the problem\nappears as soon as a viewpoint is chosen",
        "a glass missing altogether: nothing in the\npictures says that a glass is absent",
    )
    # Which rank in the right-hand list each difficulty takes. The merging is
    # the one plainly visible in a picture; the missing glass leaves no trace.
    links = (2, 0, 1)

    tall = sheet.height_for(*short, *noticed)
    top = y - 1.4 * line - tall / 2.0
    rows = [top - index * (tall + 0.9 * gap) for index in range(3)]

    for index, (row, text) in enumerate(zip(rows, short)):
        sheet.box(18.0, row, 26.0, text, height=tall, edge=WARN if index == 0 else MUTED,
                  face=_tint(WARN, 0.88) if index == 0 else PAPER,
                  lw=1.7 if index == 0 else 1.1, name="danger")
        sheet.note(2.0, row, f"{index + 1}", colour=INK, size=LABEL_SIZE + 1.0,
                   ha="center", weight="bold")

    for index, (row, text) in enumerate(zip(rows, noticed)):
        sheet.box(74.0, row, 38.0, text, height=tall, edge=GLASS if index == 0 else MUTED,
                  face=_tint(GLASS, 0.90) if index == 0 else PAPER,
                  lw=1.7 if index == 0 else 1.1, name="noticed")
        sheet.note(52.0, row, f"{index + 1}", colour=INK, size=LABEL_SIZE + 1.0,
                   ha="center", weight="bold")

    for index, target in enumerate(links):
        sheet.arrow((31.6, rows[index]), (50.0, rows[target]),
                    colour=WARN if index == 0 else MUTED,
                    lw=1.7 if index == 0 else 1.0, dashed=index != 0)

    y = rows[2] - tall / 2.0 - 1.6 * line
    sheet.note(50.0, y, "The most dangerous of the three is the last one anybody would "
                        "notice, which is why the document puts it first.",
               colour=INK, ha="center", weight="bold")

    y -= 1.5 * line
    sheet.rule(y)

    # --------------------------------------------- a row for each difficulty
    claim_x, claim_w = 32.0, 54.0
    answer_x, answer_w = 79.0, 34.0

    y -= 1.5 * line
    sheet.note(claim_x, y, "What the difficulty is", colour=INK, size=LABEL_SIZE,
               ha="center", weight="bold")
    sheet.note(answer_x, y, "Can it be settled from the pictures already taken?",
               colour=INK, size=LABEL_SIZE, ha="center", weight="bold")

    rows_detail = (
        (
            "A glass can be missing from a picture altogether. The rim is nearer the lens\n"
            "than the table, so a glass's outline is thrown outwards, away from the point\n"
            "below the camera, and the taller the glass the further out it goes. A tall\n"
            "glass's outline can sweep over a short neighbour and cover it completely, and\n"
            "the short glass appears in no picture at all. It leaves no trace: there is no\n"
            "bad number to find and no check that fails.",
            "No, and no work on the pixels can change that. A\n"
            "glass that produced no pixels cannot be recovered\n"
            "from the pixels that exist. It needs geometry\n"
            "worked out in advance, saying where a glass could\n"
            f"have been hiding given the three stations {SURVEY_MM} mm\n"
            "above the table that the camera parked at, and\n"
            "then somebody has to go and look there.",
            WARN,
        ),
        (
            "Glasses merge in the picture even when they stand apart on the table. No two\n"
            f"glass centres are closer than {MIN_CENTRES_MM} mm, so there is always bare table between\n"
            "two rims, but the same outward throw makes each glass cover more of the\n"
            "picture than its footprint deserves, and the two can leave one connected\n"
            "shape. A method that treats each connected shape as one object then reports\n"
            "one glass where two are standing.",
            "Yes. The depth readings still hold what is\n"
            "needed to tell the two apart, and each station\n"
            f"took a pair of pictures {BASELINE_MM} mm apart to\n"
            "produce them.\n"
            "This is the difficulty that most of the six\n"
            "answers are really about.",
            GOOD,
        ),
        (
            "The camera can no longer stand wherever it likes. With one glass on the table\n"
            "the camera could be parked anywhere around it. With five, a glass that would\n"
            "give a clear view of one glass may stand inside another, or put a third\n"
            "squarely in the line of sight, so choosing where to look stops being free and\n"
            "becomes its own small problem.",
            "No. A glass with no clear viewpoint cannot be\n"
            "measured from the viewpoints available.\n"
            "It needs a place to park the camera picked out\n"
            "of what the other glasses leave free, and\n"
            "inside the arm's reach.",
            WARN,
        ),
    )

    cursor = y - 1.3 * line
    for index, (claim, answer, colour) in enumerate(rows_detail):
        tall = sheet.height_for(claim, answer)
        row = cursor - tall / 2.0
        sheet.box(claim_x, row, claim_w, claim, height=tall,
                  edge=WARN if index == 0 else INK, lw=1.8 if index == 0 else 1.2,
                  name="claim")
        sheet.box(answer_x, row, answer_w, answer, height=tall, edge=colour,
                  face=_tint(colour, 0.88), lw=1.6, name="answer")
        sheet.arrow((claim_x + claim_w / 2.0 + 0.7, row),
                    (answer_x - answer_w / 2.0 - 1.0, row), colour=colour, lw=1.5)
        sheet.note(2.0, row, f"{index + 1}", colour=INK, size=LABEL_SIZE + 1.0,
                   ha="center", weight="bold")
        cursor = row - tall / 2.0 - gap

    sheet.finish(
        "The three difficulties, in the order of their danger rather than of their plainness",
        "the-three-difficulties.png",
    )


# --------------------------------------------------------------------------- #
# 2. the three parts of a complete answer, and which part a solution owns
# --------------------------------------------------------------------------- #


def a_complete_answer() -> None:
    """Why one method is not enough, drawn as three columns.

    A complete answer has three parts and only the first differs between the
    six solutions. Three equal boxes side by side would hide that, so the first
    part stands in a band of its own and the other two share a band naming the
    document they live in. Under each part is the difficulty it answers, and
    under that the reason the pixels can or cannot supply it.
    """
    sheet = Sheet(10.2, 5.0)
    line, gap = sheet.line, sheet.gap
    columns = (19.0, 50.0, 81.0)
    width = 28.0

    y = 97.0
    sheet.note(50.0, y, "A complete answer is a combination of three parts, and only the "
                        "first of them is a solution's own work",
               colour=INK, size=LABEL_SIZE + 0.6, ha="center", weight="bold")

    parts = (
        (
            "A way to place what was seen: one\n"
            "mask per glass, saying which pixels of\n"
            "which picture are that glass, and then\n"
            "a place on the table and a rough width.",
            GLASS,
        ),
        (
            "A way to work out what could not have\n"
            "been seen: which patches of table no\n"
            "station could have shown, listed as\n"
            "unsearched rather than quietly empty.",
            GOOD,
        ),
        (
            "A way to go and look again: where to\n"
            "park the camera next, chosen from the\n"
            "space the other glasses leave free, and\n"
            "a fresh pair of pictures taken there.",
            GOOD,
        ),
    )

    part_h = sheet.height_for(*(text for text, _ in parts))
    band_top = y - 1.6 * line
    part_y = band_top - 1.5 * line - part_h / 2.0
    band_bottom = part_y - part_h / 2.0 - 0.6 * line
    sheet.band(3.5, band_bottom, 31.0, band_top - band_bottom, GLASS,
               "different in each of the six solutions")
    sheet.band(36.5, band_bottom, 60.0, band_top - band_bottom, GOOD,
               "the same for all six, so written down once in looking again at what was hidden")
    for x, (text, colour) in zip(columns, parts):
        sheet.box(x, part_y, width, text, height=part_h, edge=colour,
                  face=_tint(colour, 0.82), lw=1.7, name="part")

    answers = (
        "Answers the second difficulty: two\n"
        "glasses leave one connected shape in the\n"
        "picture although they stand apart.",
        "Answers the first difficulty: a tall glass's\n"
        "outline can cover a short neighbour, which\n"
        "then appears in no picture at all.",
        "Answers the third difficulty: the camera\n"
        "can no longer stand wherever it likes,\n"
        "because the glasses block the views.",
    )
    answer_h = sheet.height_for(*answers)
    answer_y = band_bottom - 1.9 * gap - answer_h / 2.0
    for x, text in zip(columns, answers):
        sheet.arrow((x, band_bottom - 0.3), (x, answer_y + answer_h / 2.0 + 0.6))
        sheet.box(x, answer_y, width, text, height=answer_h, name="answers")

    reasons = (
        (
            "The pixels can supply this. The depth\n"
            "readings at one station still hold what is\n"
            "needed to tell two merged glasses apart.",
            GOOD,
        ),
        (
            "The pixels cannot supply this. A glass that\n"
            "produced no pixels cannot be recovered by\n"
            "any work on the pixels that exist.",
            WARN,
        ),
        (
            "The pixels cannot supply this. A glass with\n"
            "no clear viewpoint cannot be measured\n"
            "from the viewpoints already available.",
            WARN,
        ),
    )
    reason_h = sheet.height_for(*(text for text, _ in reasons))
    reason_y = answer_y - answer_h / 2.0 - 1.9 * gap - reason_h / 2.0
    for x, (text, colour) in zip(columns, reasons):
        sheet.arrow((x, answer_y - answer_h / 2.0 - 0.3),
                    (x, reason_y + reason_h / 2.0 + 0.6), colour=colour)
        sheet.box(x, reason_y, width, text, height=reason_h, edge=colour,
                  face=_tint(colour, 0.88), lw=1.6, name="reason")

    y = reason_y - reason_h / 2.0 - 1.4 * line
    sheet.rule(y)
    y -= 1.6 * line
    sheet.note(50.0, y, "Working harder on the pixels improves the first part and can never "
                        "reach the other two. The second part is geometry worked out in\n"
                        "advance and the third is a second look taken afterwards, and the "
                        "patches the second part names are where the third look goes.",
               colour=INK, ha="center")
    y -= 2.1 * line
    sheet.note(50.0, y, "Both are the same for every solution, so they are written down once "
                        "and no solution has to restate them.",
               colour=GOOD, ha="center", weight="bold")

    sheet.finish(
        "Why one method is not enough: three parts, of which a solution supplies one",
        "a-complete-answer.png",
    )


# --------------------------------------------------------------------------- #
# 3. what "done" means, and the two measurements
# --------------------------------------------------------------------------- #


def what_done_means() -> None:
    """The three conditions for a finished run, then the two measurements.

    The conditions go across the top because no one of them matters more than
    the others: a run that misses any one of them is not done. The two
    measurements below are not alike, and the chart spends its space on what is
    unlike about them. One of the counts hides itself, and the other
    measurement exists only because the step that follows a mask is forgiving.
    """
    sheet = Sheet(11.0, 7.2)
    line, gap = sheet.line, sheet.gap

    # ------------------------------------------- done, in three conditions
    y = 97.0
    sheet.note(50.0, y, "A run is done when all three of these hold",
               colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")

    conditions = (
        "Every glass has a mask, a place on\n"
        "the table and a rough width of its\n"
        "footprint.",
        "Every glass that could not be\n"
        "separated from its neighbour is\n"
        "listed, with the reason.",
        "Every region of table that could not\n"
        "have been seen is listed as\n"
        "unsearched, not treated as empty.",
    )
    condition_h = sheet.height_for(*conditions)
    y -= 1.5 * line + condition_h / 2.0
    for x, text in zip((19.0, 50.0, 81.0), conditions):
        sheet.box(x, y, 30.0, text, height=condition_h, edge=GOOD,
                  face=_tint(GOOD, 0.90), lw=1.5, name="done")

    y -= condition_h / 2.0 + 1.3 * line
    sheet.rule(y)
    y -= 1.5 * line
    sheet.note(50.0, y, "And the six answers are compared on two measurements",
               colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold")

    left_x, right_x, column_w = 27.0, 74.0, 42.0

    measures = (
        "How many glasses were found, missed, merged or\n"
        "split. This says whether the method separated the\n"
        f"glasses at all, and the bench reports five counts:\n"
        f"{COUNTS}.",
        "How much of each glass the mask actually covered.\n"
        "This says how good the outline was, and it is the\n"
        "measurement that separates methods which the\n"
        "other measurements cannot.",
    )
    measure_h = sheet.height_for(*measures)
    y -= 1.4 * line + measure_h / 2.0
    for x, text in zip((left_x, right_x), measures):
        sheet.box(x, y, column_w, text, height=measure_h, lw=1.4, name="measure")
    columns_top = y - measure_h / 2.0

    # ---------------------------- why missed is the count to watch hardest
    head_y = columns_top - 1.5 * line
    sheet.note(left_x, head_y, "Three ways of getting a glass wrong, hardest to spot last",
               colour=INK, ha="center", weight="bold")
    sheet.note(right_x, head_y, "Why the mask is measured as well as the place",
               colour=INK, ha="center", weight="bold")

    outcomes = (
        (
            "A split glass announces itself: one glass comes\n"
            "back as two reports, and both halves are too\n"
            "small to be a glass.",
            GOOD, 1.3,
        ),
        (
            "A merged pair looks like one large glass, which is\n"
            "worse, because nothing about it looks wrong and\n"
            "everything downstream believes it.",
            WARN, 1.3,
        ),
        (
            "A missed glass leaves nothing at all: no report,\n"
            "no mask, and no number out of place for a check\n"
            "to catch.",
            WARN, 2.0,
        ),
    )
    outcome_h = sheet.height_for(*(text for text, _, _ in outcomes))
    cursor = head_y - 1.4 * line
    first_top, last_bottom = cursor, cursor
    for text, colour, lw in outcomes:
        row = cursor - outcome_h / 2.0
        sheet.box(left_x + 2.0, row, column_w - 4.0, text, height=outcome_h, edge=colour,
                  face=_tint(colour, 0.88), lw=lw, name="outcome")
        last_bottom = row - outcome_h / 2.0
        cursor = last_bottom - 0.8 * gap
    sheet.arrow((7.0, first_top - 0.5), (7.0, last_bottom + 0.5), colour=WARN, lw=1.6)
    sheet.note(5.0, (first_top + last_bottom) / 2.0, "harder to spot, so worse",
               colour=WARN, ha="center", weight="bold", rotation=90)

    left_end = last_bottom - 1.6 * line
    sheet.note(left_x + 2.0, left_end,
               "So missed is the count to watch hardest. It is the only\n"
               "one of the three that nothing in the results points at.",
               colour=INK, ha="center", weight="bold")

    # ------------------- why the mask has to be measured as well as the place
    forgiving = (
        "The shared step that turns a mask into a place is\n"
        "deliberately forgiving. It takes the axis from the points\n"
        "at the top of the glass, and the width as the "
        f"{SPREAD}th\n"
        "percentile of how far the cloud of points spreads from\n"
        "that axis."
    )
    forgiving_h = sheet.height_for(forgiving)
    forgiving_y = head_y - 1.4 * line - forgiving_h / 2.0
    sheet.box(right_x, forgiving_y, column_w, forgiving, height=forgiving_h, edge=GLASS,
              face=_tint(GLASS, 0.88), lw=1.6, name="forgiving")

    masks = (
        ("a mask that follows\nthe glass closely", GLASS, right_x - 11.0),
        ("a mask that is far\ntoo generous", WARN, right_x + 11.0),
    )
    mask_h = sheet.height_for(*(text for text, _, _ in masks))
    mask_y = forgiving_y - forgiving_h / 2.0 - 1.9 * gap - mask_h / 2.0
    for text, colour, x in masks:
        sheet.arrow((x, forgiving_y - forgiving_h / 2.0 - 0.3), (x, mask_y + mask_h / 2.0 + 0.6),
                    colour=colour)
        sheet.box(x, mask_y, 20.0, text, height=mask_h, edge=colour, lw=1.3, name="mask")

    same = "almost the same place on the table"
    same_h = sheet.height_for(same)
    same_y = mask_y - mask_h / 2.0 - 1.9 * gap - same_h / 2.0
    for _, colour, x in masks:
        sheet.arrow((x, mask_y - mask_h / 2.0 - 0.3),
                    (right_x + (4.0 if x > right_x else -4.0), same_y + same_h / 2.0 + 0.6),
                    colour=colour)
    sheet.box(right_x, same_y, 34.0, same, height=same_h, edge=MUTED,
              face=_tint(MUTED, 0.88), lw=1.3, name="same place")

    sheet.note(right_x, same_y - same_h / 2.0 - 1.6 * line,
               "The place cannot tell those two masks apart, so comparing\n"
               "the masks themselves is what shows the difference.",
               colour=INK, ha="center", weight="bold")

    y = min(left_end, same_y) - 3.2 * line
    sheet.rule(y)
    y -= 1.6 * line
    sheet.note(50.0, y, "The three conditions decide whether a run finished. The two "
                        "measurements decide which of the six answers did it better.\n"
                        "A run can score well on both measurements and still not be done, "
                        "because a region nobody looked at is counted by neither.",
               colour=INK, ha="center")

    sheet.finish(
        "What “done” means, and the two measurements the six answers are compared on",
        "what-done-means.png",
    )


def main() -> None:
    three_difficulties()
    a_complete_answer()
    what_done_means()


if __name__ == "__main__":
    main()
