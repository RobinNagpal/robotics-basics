"""The two flow charts for "what is asked for".

That document states the question all six solutions answer, and two of its
claims are easier to see as a picture than to hold in the head while reading:

    what-done-means.png              the three conditions a run has to meet.
    missed-is-the-one-to-watch.png   why a missed glass is the worst of the
                                     three ways of getting a glass wrong.

One chart to a picture, because two charts in one image give a reader no way
of telling where the first argument ends and the second begins.

Three other charts lived here: two putting the difficulties in their orders and
laying out the parts of a complete answer, and one arguing that the mask has to
be measured as well as the place. The document now shows each difficulty as
three drawings of a real arrangement, and the mask argument has a chapter of
its own, so all three went with the sections that held them.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_problem_flows.py
"""

from __future__ import annotations

import matplotlib.colors as mcolors
from diagram_style import (
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

COUNTS = "found, missed, merged, split and false"   # bench/marking.py FIND

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
    """The three conditions a finished run has to meet.

    The three go across rather than down because no one of them comes before
    the others or matters more than the others. A run that misses any one of
    them is not done.
    """
    sheet = Sheet(8.2, 1.12)
    line = sheet.line

    conditions = (
        "Every glass has a mask, a place on\n"
        "the table and a rough width.",
        "Every glass that could not be told\n"
        "apart from its neighbour is listed,\n"
        "with the reason.",
        "Every region that could not be seen\n"
        "is listed as unsearched, not treated\n"
        "as empty.",
    )
    condition_h = sheet.height_for(*conditions)
    y = 95.0 - condition_h / 2.0
    for x, text in zip((17.5, 50.0, 82.5), conditions):
        sheet.box(x, y, 31.0, text, height=condition_h, edge=GOOD,
                  face=_tint(GOOD, 0.90), lw=1.5, name="done")

    y -= condition_h / 2.0 + 1.6 * line
    sheet.note(50.0, y, "All three have to hold. Two out of the three is not a finished run.",
               colour=INK, ha="center", weight="bold")

    sheet.finish("What “done” means", "what-done-means.png")


def missed_is_the_one_to_watch() -> None:
    """Why a missed glass is the worst of the three ways of getting one wrong.

    The three are stacked in the order they are hard to spot in, because that
    order is the whole argument. A split glass contradicts itself, a merged
    pair does not, and a missed glass leaves nothing behind to contradict.
    """
    sheet = Sheet(6.6, 2.6)
    line, gap = sheet.line, sheet.gap
    column_x, column_w = 60.0, 70.0

    y = 95.0
    sheet.note(column_x, y, f"The examiner counts {COUNTS}.",
               colour=MUTED, ha="center")

    outcomes = (
        ("Split: one glass comes back as two reports.\n"
         "Both halves are too small to be a glass.", GOOD, 1.3),
        ("Merged: two glasses come back as one.\n"
         "Nothing about that report looks wrong.", WARN, 1.3),
        ("Missed: nothing comes back at all. No report,\n"
         "no mask, no number out of place.", WARN, 2.0),
    )
    outcome_h = sheet.height_for(*(text for text, _, _ in outcomes))
    cursor = y - 1.8 * line
    first_top, last_bottom = cursor, cursor
    for text, colour, lw in outcomes:
        row = cursor - outcome_h / 2.0
        sheet.box(column_x, row, column_w, text, height=outcome_h, edge=colour,
                  face=_tint(colour, 0.88), lw=lw, name="outcome")
        last_bottom = row - outcome_h / 2.0
        cursor = last_bottom - 0.8 * gap

    sheet.arrow((12.0, first_top - 0.5), (12.0, last_bottom + 0.5), colour=WARN, lw=1.6)
    sheet.note(8.0, (first_top + last_bottom) / 2.0, "harder to spot, so worse",
               colour=WARN, ha="center", weight="bold", rotation=90)

    sheet.note(column_x, last_bottom - 1.7 * line,
               "So missed is the count to watch hardest. It is the only one of\n"
               "the three that nothing in the results points at.",
               colour=INK, ha="center", weight="bold")

    sheet.finish(
        "Three ways of getting a glass wrong, hardest to spot last",
        "missed-is-the-one-to-watch.png",
    )


def main() -> None:
    what_done_means()
    missed_is_the_one_to_watch()


if __name__ == "__main__":
    main()
