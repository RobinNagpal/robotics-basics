"""The flow chart for "what is asked for".

That document states the question all six solutions answer, and one of its
claims is easier to see as a picture than to hold in the head while reading:

    what-done-means.png         the three conditions a run has to meet, the two
                                measurements the answers are compared on, why
                                a missed glass is the one to watch hardest, and
                                why the mask is measured as well as the place.

Two other charts lived here, one putting the difficulties in their two orders
and one laying out the three parts of a complete answer. The document now shows
each difficulty as three drawings of a real arrangement instead, so both were
removed with the sections that held them.

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
    what_done_means()


if __name__ == "__main__":
    main()
