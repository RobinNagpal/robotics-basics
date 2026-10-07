"""The pictures for the six pages of solution 1, one fixed nudge.

Six drawings, each carrying one shape the prose on its page cannot carry.

    nudge-pages-the-error.png            what the shortfall is, on the table:
                                         how far the neighbour's edge reaches
                                         inside the ring the open jaw needs.
    nudge-pages-the-gain.png             what is left of the shortfall after
                                         each push, for four values of the
                                         product the method does not know.
    nudge-pages-three-answers.png        where the tipping arithmetic can
                                         answer and where it has to spend a
                                         push to find out, against the feet
                                         the four kinds of glass stand on.
    nudge-pages-the-parameters.png       a parameterised push drawn on the
                                         table, with its five numbers.
    nudge-pages-crowded-from-two-sides.png  the same table on three passes,
                                         with the glass driven back and forth.
    nudge-pages-nowhere-to-stand.png     why the approach is the harder
                                         constraint: the tool has to lie
                                         where the blocking neighbour stands.

Every number written into these pictures is read out of ``code/src/``, and the
constant that holds it is named in a comment beside it below. A few lengths
are drawn rather than quoted, because the repository holds no value for them:
the gain, and the two distances a picture has to choose before it can draw a
push at all. Each of those is marked where it is set, and the picture that
leans on the gain says on its face that there is none.

The sheets are the inch-coordinate sheets ``make_solution_flows_a`` draws its
flow charts on, so a millimetre on the table is a fixed number of inches on the
paper and every circle comes out round. The same module's audit is run on each
sheet, so two labels landing on the same patch of paper is a printed complaint
rather than something a reader finds.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_nudge_pages.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from diagram_style import (
    GLASS,
    GOOD,
    INK,
    KIND_NARROWEST,
    KIND_WIDEST,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    WARN,
    save,
)
from make_solution_flows_a import _tint, finish, note, sheet, title
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Wedge

sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "code" / "src" / "08_seeing-the-glasses" / "work_cell")
)

from work_cell.glasses.shapes import family  # noqa: E402

# ------------------------------------------------------------------ the numbers
#
# All of these are read out of code/src/, and the constant that holds each one
# is named so that a reader can check it in one step.

GRIP_ROOM_MM = 70.0        # bench/bench.py GRIP_ROOM = 0.070
JAW_TOP_MM = 65.0          # bench/bench.py JAW_TOP = PUSH_HEIGHT + FINGER_HEIGHT / 2
MU_LOWEST = 0.2            # 01-one-fixed-nudge/plan.py MU_LOWEST
MU_HIGHEST = 0.5           # 01-one-fixed-nudge/plan.py MU_HIGHEST
PROBE_MM = 5.0             # 01-one-fixed-nudge/plan.py PROBE = 0.005
APPROACH_GAP_MM = 10.0     # 01-one-fixed-nudge/plan.py APPROACH_GAP = 0.010
FEEL_BEYOND_MM = 30.0      # 01-one-fixed-nudge/plan.py FEEL_BEYOND = 0.030

FINGER_LENGTH_MM = 120.0   # bench/bench.py FINGER_LENGTH = 0.12
BODY_LENGTH_MM = 50.0      # bench/bench.py BODY_LENGTH = 0.05
WRIST_LENGTH_MM = 100.0    # bench/bench.py WRIST_LENGTH = 0.10
TOOL_LENGTH_MM = FINGER_LENGTH_MM + BODY_LENGTH_MM + WRIST_LENGTH_MM   # bench.py TOOL_LENGTH, 270 mm
BODY_SIZE_MM = 90.0        # bench/bench.py BODY_SIZE = 0.09
JAW_THICKNESS_MM = 28.0    # bench/bench.py JAW_THICKNESS = 2 * (0.010 + 0.004)

# The foot a glass has to stand on before the arithmetic can decide it on its
# own. Both ends are the same rule, h < a / mu, read backwards at the height
# the push really lands: a glass slides at every friction in the range when
# its foot is wider than 2 * MU_HIGHEST * JAW_TOP, and tips at every friction
# in the range when it is narrower than 2 * MU_LOWEST * JAW_TOP.
SLIDES_ABOVE_MM = 2.0 * MU_HIGHEST * JAW_TOP_MM     # 65 mm
TIPS_BELOW_MM = 2.0 * MU_LOWEST * JAW_TOP_MM        # 26 mm

# The four kinds, in the order bench/bench.py KINDS cycles them, and how many
# of each are drawn to measure the feet the kind really stands on. The same
# count and seed as 01-one-fixed-nudge/measure_peel.py uses.
KINDS = ("straight_glass", "tapered_glass", "stemmed_glass", "short_stemmed_glass")
KIND_NAMES = {
    "straight_glass": "straight",
    "tapered_glass": "tapered",
    "stemmed_glass": "stemmed",
    "short_stemmed_glass": "short stemmed",
}
DRAWN = 400
DRAW_SEED = 7

# The gain has no value in the repository: 02_how-it-works.md says it is
# argued and then frozen, and nothing in plan.py holds it. So the picture that
# needs one draws four values of the product g * k instead of a gain, and says
# on its face that the product is what nobody measures.
PRODUCTS = (
    (0.3, "slow, and it shrinks"),
    (1.0, "exact, if g is exactly 1"),
    (1.8, "it overshoots, but shrinks"),
    (2.4, "it grows"),
)
ILLUSTRATIVE_GAIN = 0.5    # for the three passes of the oscillation picture only


def spans() -> dict[str, tuple[float, float]]:
    """The narrowest and widest foot each kind is really drawn on, millimetres."""
    found = {}
    for kind in KINDS:
        feet = [2000.0 * float(outline.radius[0]) for outline, _ in family(kind, DRAWN, DRAW_SEED)]
        found[kind] = (min(feet), max(feet))
    return found


# --------------------------------------------------------------------------- #
# Drawing on an inch sheet, in millimetres
# --------------------------------------------------------------------------- #


class Table:
    """A patch of table top on an inch sheet: millimetres in, inches out."""

    def __init__(self, axis, origin: tuple[float, float], scale: float):
        self.axis = axis
        self.origin = origin
        self.scale = scale

    def at(self, x: float, y: float = 0.0) -> tuple[float, float]:
        return self.origin[0] + self.scale * x, self.origin[1] + self.scale * y

    def length(self, mm: float) -> float:
        return self.scale * mm

    def glass(self, centre, rim: float, *, colour=GLASS, alpha=0.30, lw=1.1, zorder=3):
        self.axis.add_patch(
            Circle(self.at(*centre), self.length(rim / 2.0), facecolor=colour, alpha=alpha,
                   edgecolor=colour, lw=lw, zorder=zorder)
        )

    def ring(self, centre, *, colour=MUTED, lw=1.2, zorder=2):
        self.axis.add_patch(
            Circle(self.at(*centre), self.length(GRIP_ROOM_MM), facecolor="none",
                   edgecolor=colour, lw=lw, ls=(0, (4, 3)), zorder=zorder)
        )

    def arrow(self, start, end, *, colour=INK, lw=1.5, zorder=6):
        self.axis.add_patch(
            FancyArrowPatch(self.at(*start), self.at(*end), arrowstyle="-|>", mutation_scale=11,
                            linewidth=lw, color=colour, shrinkA=0, shrinkB=0, zorder=zorder)
        )


def span(axis, left: float, right: float, y: float, *, colour=INK, lw=1.0, zorder=7) -> None:
    """A measured distance on the paper, drawn as a line with a tick at each end."""
    axis.add_patch(
        FancyArrowPatch((left, y), (right, y), arrowstyle="|-|", mutation_scale=4,
                        linewidth=lw, color=colour, shrinkA=0, shrinkB=0, zorder=zorder)
    )


def tick(axis, x: float, bottom: float, top: float, *, colour=MUTED, lw=0.9) -> None:
    axis.plot([x, x], [bottom, top], color=colour, lw=lw, ls=(0, (2, 2)), zorder=2)




# --------------------------------------------------------------------------- #
# 1. what the shortfall is
# --------------------------------------------------------------------------- #


def the_error() -> None:
    """The error the loop corrects, drawn as a length on the table.

    Algebraically the shortfall is 70 mm, plus half the neighbour's widest
    width, minus the distance between the two middles. On the table it is one
    thing: how far the neighbour's edge reaches inside the ring. The picture is
    here because the prose has to say it as a subtraction, and a reader cannot
    see a subtraction.
    """
    width, height = 8.7, 5.8
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "The shortfall: how far the neighbour's edge reaches inside the ring")

    scale = 0.0225                 # inches per millimetre
    table = Table(axis, (2.20, 3.55), scale)

    # The crowded glass is drawn at the narrow end of the tapered kind's
    # declared range and its neighbour at the wide end, because the room one
    # glass needs is set by how wide the other is. Neither is any glass's
    # measurement; both are the range glasses/shapes.py may draw from.
    crowded_rim, neighbour_rim = KIND_NARROWEST, KIND_WIDEST
    apart = 100.0                  # millimetres between the two middles
    needs = GRIP_ROOM_MM + neighbour_rim / 2.0
    short_by = needs - apart
    edge = apart - neighbour_rim / 2.0

    table.ring((0.0, 0.0), colour=WARN)
    table.glass((0.0, 0.0), crowded_rim, colour=WARN)
    table.glass((apart, 0.0), neighbour_rim, colour=GLASS)

    # The piece of the ring the neighbour has eaten into, shaded.
    half = math.degrees(math.acos(max(-1.0, min(1.0, edge / GRIP_ROOM_MM))))
    axis.add_patch(
        Wedge(table.at(0.0, 0.0), table.length(GRIP_ROOM_MM), -half, half,
              width=table.length(short_by), facecolor=_tint(WARN, 0.55), edgecolor="none",
              zorder=1)
    )

    # The two names sit above their middles, because the measuring lines run
    # down from the middles and would otherwise be drawn through them.
    note(axis, *table.at(0.0, 12.0), "the crowded\nglass", colour=INK, ha="center", size=NOTE_SIZE)
    note(axis, *table.at(apart, 12.0), "the\nneighbour", colour=INK, ha="center", size=NOTE_SIZE)
    note(axis, *table.at(-GRIP_ROOM_MM * 0.80, GRIP_ROOM_MM * 0.80),
         f"{GRIP_ROOM_MM:.0f} mm", colour=WARN, ha="right", size=LABEL_SIZE, weight="bold")

    # The three lengths, stacked under the drawing with their names in a
    # column to the right, so that no measuring line is drawn through a label.
    x_middle, x_edge, x_ring, x_neighbour = (
        table.at(v, 0.0)[0] for v in (0.0, edge, GRIP_ROOM_MM, apart)
    )
    first = table.at(0.0, -GRIP_ROOM_MM)[1] - 0.38
    names_x = table.at(apart + neighbour_rim / 2.0, 0.0)[0] + 0.30
    for x in (x_middle, x_edge, x_ring, x_neighbour):
        tick(axis, x, first - 0.92, table.at(0.0, 0.0)[1])

    rows = (
        (first, x_edge, x_ring, WARN, 1.8, "the shortfall", LABEL_SIZE, "bold"),
        (first - 0.42, x_middle, x_ring, INK, 1.0,
         f"{GRIP_ROOM_MM:.0f} mm, plus half the neighbour's width", NOTE_SIZE, "normal"),
        (first - 0.84, x_middle, x_neighbour, INK, 1.0,
         "how far apart their middles are", NOTE_SIZE, "normal"),
    )
    for y, left, right, colour, lw, label, size, weight in rows:
        span(axis, left, right, y, colour=colour, lw=lw)
        note(axis, names_x, y, label, colour=colour, ha="left", size=size, weight=weight)

    bottom = note(axis, width / 2.0, first - 1.30,
                  "The first length is the second minus the third, and the push travels a "
                  "fraction of it, straight away from the neighbour.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-the-error.png", bottom - 0.10)
    save(figure, "nudge-pages-the-error.png")


# --------------------------------------------------------------------------- #
# 2. why the push is a fraction of the shortfall
# --------------------------------------------------------------------------- #


def the_gain() -> None:
    """What is left of the shortfall after each push, for four values of g * k.

    One push multiplies the shortfall by 1 - g * k, so the whole argument for a
    small gain is which side of a line the product lands on. That is a shape,
    and four rows of it say at a glance what a paragraph of algebra says slowly.
    """
    width, height = 9.3, 5.6
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "One push multiplies the shortfall by 1 − g · k, so the product decides everything")

    passes = 4
    zero_x = 5.45                  # the line the glass needed to reach
    unit = 1.25                    # inches standing for the shortfall it started with
    names_x = 1.80                 # the column the row names are right-aligned in
    row_top = height - 1.15
    row_gap = 0.95
    bar_h = 0.115
    bar_gap = 0.055
    row_depth = passes * (bar_h + bar_gap)

    for row, (product, ending) in enumerate(PRODUCTS):
        y_top = row_top - row * row_gap
        for n in range(passes):
            value = pow(1.0 - product, n)
            y = y_top - n * (bar_h + bar_gap) - bar_h
            if abs(value) < 1e-9:
                # Nothing left to push. Drawn as a mark rather than as a bar of
                # no length, so that an exact landing is not an empty row.
                axis.add_patch(
                    Circle((zero_x, y + bar_h / 2.0), 0.05, facecolor=GOOD, edgecolor=GOOD,
                           zorder=4)
                )
                continue
            colour = WARN if value < 0.0 else GLASS
            axis.add_patch(
                Rectangle((min(zero_x, zero_x + unit * value), y), abs(unit * value), bar_h,
                          facecolor=_tint(colour, 0.35), edgecolor=colour, lw=0.8, zorder=4)
            )
        axis.plot([zero_x, zero_x], [y_top - row_depth - 0.04, y_top + 0.08],
                  color=MUTED, lw=0.9, zorder=2)
        middle = y_top - row_depth / 2.0
        note(axis, names_x, middle + 0.11, f"g · k = {product}", colour=INK, ha="right",
             size=LABEL_SIZE, weight="bold")
        note(axis, names_x, middle - 0.11, ending,
             colour=WARN if "grows" in ending else INK, ha="right", size=NOTE_SIZE)
        if row < len(PRODUCTS) - 1:
            axis.plot([names_x - 1.30, width - 0.55], [y_top - row_depth - 0.26] * 2,
                      color=MUTED, lw=0.5, alpha=0.5, zorder=1)

    note(axis, zero_x, row_top + 0.44, "where the glass needed to get to", colour=MUTED,
         ha="center", size=NOTE_SIZE)
    note(axis, zero_x - 0.14, row_top + 0.24, "carried past it", colour=MUTED, ha="right",
         size=NOTE_SIZE)
    note(axis, zero_x + 0.14, row_top + 0.24, "still short of it", colour=MUTED, ha="left",
         size=NOTE_SIZE)
    note(axis, zero_x + unit + 0.22, row_top - row_depth / 2.0,
         "one bar\nfor each\nof four\npasses", colour=MUTED, ha="left", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, 0.66,
                  "k is the fraction the method pushes and g is everything the friction decides. "
                  "Nothing in the cell measures g, and the gain k has no value in the repository.\n"
                  "The shortfall shrinks for every product between 0 and 2, so a small k is the "
                  "one choice that converges whatever g turns out to be.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-the-gain.png", bottom - 0.10)
    save(figure, "nudge-pages-the-gain.png")


# --------------------------------------------------------------------------- #
# 3. the three answers the tipping arithmetic gives
# --------------------------------------------------------------------------- #


def three_answers() -> None:
    """Where ``slides()`` can decide on its own, and where it has to spend a push.

    The whole of that function is two comparisons against the same quantity,
    half the foot over the friction, at the two ends of a range nobody
    measured. Drawn against the feet the four kinds really stand on, it shows
    which kinds the arithmetic can never settle.
    """
    feet = spans()

    width, height = 10.4, 4.7
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "The tipping arithmetic has three answers, and the foot decides which")

    # The kinds are named in a gutter to the left of the zones, so that
    # neither of the two lines is ever drawn through a label.
    left, right_mm = 1.95, 110.0
    scale = (width - left - 0.45) / right_mm
    axis_y = height - 1.40
    bar_top = axis_y - 0.48

    def x_of(mm: float) -> float:
        return left + scale * mm

    zones = (
        (0.0, TIPS_BELOW_MM, WARN, "it tips at every friction\nin the range: refuse it"),
        (TIPS_BELOW_MM, SLIDES_ABOVE_MM, MUTED,
         f"the friction decides: push it {PROBE_MM:.0f} mm\nand look, then push it properly"),
        (SLIDES_ABOVE_MM, right_mm, GOOD, "it slides at every friction\nin the range: push it"),
    )
    zone_bottom = bar_top - 3 * 0.40 - 0.26
    for start, stop, colour, label in zones:
        axis.add_patch(
            Rectangle((x_of(start), zone_bottom), scale * (stop - start), axis_y - zone_bottom,
                      facecolor=_tint(colour, 0.88), edgecolor="none", zorder=1)
        )
        note(axis, (x_of(start) + x_of(stop)) / 2.0, axis_y + 0.30, label,
             colour=colour if colour != MUTED else INK, ha="center", size=NOTE_SIZE)

    axis.plot([x_of(0.0), x_of(right_mm)], [axis_y, axis_y], color=INK, lw=1.1, zorder=5)
    # Each line is named beside itself rather than over itself, because a line
    # drawn through its own label is the commonest fault in a picture like this.
    for mm, side in ((TIPS_BELOW_MM, "right"), (SLIDES_ABOVE_MM, "left")):
        axis.plot([x_of(mm), x_of(mm)], [zone_bottom, axis_y + 0.08], color=INK, lw=1.1, zorder=5)
        nudge = -0.07 if side == "right" else 0.07
        note(axis, x_of(mm) + nudge, axis_y - 0.19, f"{mm:.0f} mm", colour=INK, ha=side,
             size=LABEL_SIZE, weight="bold")

    # The name and the range go together to the left of each bar, so that
    # neither of the two lines above is drawn through a label.
    for row, kind in enumerate(KINDS):
        low, high = feet[kind]
        y = bar_top - row * 0.40
        axis.add_patch(
            Rectangle((x_of(low), y - 0.11), scale * (high - low), 0.22,
                      facecolor=_tint(GLASS, 0.45), edgecolor=GLASS, lw=1.0, zorder=4)
        )
        note(axis, 0.30, y, f"{KIND_NAMES[kind]}, {low:.0f}–{high:.0f} mm",
             colour=INK, ha="left", size=NOTE_SIZE)

    note(axis, x_of(right_mm / 2.0), zone_bottom - 0.24,
         "the foot the glass stands on, over the range each kind is drawn from",
         colour=INK, ha="center", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, zone_bottom - 0.62,
                  f"A push slides a glass while it is lower than half the foot over the friction, "
                  f"and it lands on the jaw's top edge at {JAW_TOP_MM:.0f} mm. Read backwards at "
                  f"the two ends of the range,\n{MU_LOWEST} and {MU_HIGHEST}, that is where the "
                  f"two lines above come from. Neither the tapered kind nor the short stemmed one "
                  f"ever reaches the right-hand zone.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-three-answers.png", bottom - 0.10)
    save(figure, "nudge-pages-three-answers.png")


# --------------------------------------------------------------------------- #
# 4. what a parameterised push is
# --------------------------------------------------------------------------- #


def the_parameters() -> None:
    """One parameterised push drawn on the table, with the numbers it carries.

    The prose can only list the fields. Every one of them is a place, a
    direction or a length on the table, and the list stops being a list as soon
    as they are drawn on one line.
    """
    width, height = 8.6, 4.7
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "What this solution hands over: one push, drawn on the table")

    scale = 0.030
    rim = KIND_NARROWEST
    travel = 40.0                  # drawn: the gain has no value in the repository
    table = Table(axis, (3.30, 2.70), scale)

    start = -(rim / 2.0 + APPROACH_GAP_MM)
    reach = rim / 2.0 + APPROACH_GAP_MM + FEEL_BEYOND_MM
    jaw = 25.0                     # how much of the fingers is drawn, not a constant

    # The heading, as the line everything else is laid along.
    heading = [table.at(start - jaw - 30.0, 0.0), table.at(travel + rim / 2.0 + 4.0, 0.0)]
    axis.plot([heading[0][0], heading[1][0]], [heading[0][1], heading[1][1]],
              color=MUTED, lw=0.9, ls=(0, (5, 4)), zorder=1)

    table.glass((0.0, 0.0), rim, colour=GLASS)
    table.glass((travel, 0.0), rim, colour=GOOD, alpha=0.16)

    corner = table.at(start - jaw, -JAW_THICKNESS_MM / 2.0)
    axis.add_patch(
        Rectangle(corner, table.length(jaw), table.length(JAW_THICKNESS_MM),
                  facecolor=_tint(INK, 0.78), edgecolor=INK, lw=1.0, zorder=5)
    )

    table.arrow((0.0, 0.0), (travel, 0.0), colour=INK, lw=1.8)

    above = table.at(0.0, rim / 2.0)[1] + 0.22
    below = table.at(0.0, -rim / 2.0)[1] - 0.22
    span(axis, table.at(0.0, 0.0)[0], table.at(travel, 0.0)[0], above)
    note(axis, table.at(travel / 2.0, 0.0)[0], above + 0.17, "how far to push",
         colour=INK, ha="center", size=NOTE_SIZE)
    span(axis, table.at(start, 0.0)[0], table.at(start + reach, 0.0)[0], below, colour=MUTED)
    note(axis, table.at(start + reach / 2.0, 0.0)[0], below - 0.17,
         f"how far to feel forward: {FEEL_BEYOND_MM:.0f} mm past the glass's middle",
         colour=MUTED, ha="center", size=NOTE_SIZE)

    note(axis, heading[0][0] - 0.08, table.at(0.0, 0.0)[1] + 0.20, "the heading",
         colour=MUTED, ha="left", size=NOTE_SIZE)
    note(axis, table.at(start - jaw / 2.0, 0.0)[0], table.at(0.0, 0.0)[1] + 0.95,
         f"where the fingertips come down:\n{APPROACH_GAP_MM:.0f} mm outside the widest part",
         colour=INK, ha="center", size=NOTE_SIZE)
    note(axis, table.at(travel + rim / 2.0 + 12.0, 0.0)[0], table.at(0.0, 0.0)[1],
         "where the glass is\nexpected to arrive", colour=GOOD, ha="left", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, 0.72,
                  "The examiner's own macro turns those numbers into the descent, the feel, the "
                  "push, the retreat and the lift, and it expands every solution's push the same "
                  "way.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-the-parameters.png", bottom - 0.10)
    save(figure, "nudge-pages-the-parameters.png")


# --------------------------------------------------------------------------- #
# 5. a glass crowded from two sides
# --------------------------------------------------------------------------- #


def crowded_from_two_sides() -> None:
    """Three passes of the loop on the table it cannot clear.

    The method takes the worst shortfall and pushes straight away from the
    glass that caused it. With a neighbour on each side, away from one is
    towards the other, so the worst shortfall changes hands every pass and the
    glass is carried back and forth. Three passes of one table, stacked, is the
    only way to show something that exists only over time.
    """
    width, height = 7.8, 7.3
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "A glass crowded from both sides: every push undoes the one before it")

    crowded_rim, neighbour_rim = KIND_NARROWEST, KIND_WIDEST
    needs = GRIP_ROOM_MM + neighbour_rim / 2.0
    left_at, right_at = -85.0, 95.0

    # Each pass worked out with the two rules the method has: take the worst
    # shortfall, and travel the gain times it, straight away from the neighbour
    # that caused it. The gain is illustrative, because there is none in the
    # repository.
    where = 0.0
    passes, worst = [], []
    for _ in range(3):
        short_left = needs - (where - left_at)
        short_right = needs - (right_at - where)
        worst.append(max(short_left, short_right))
        if short_left >= short_right:
            moved = where + ILLUSTRATIVE_GAIN * short_left
            passes.append((where, moved, "B"))
        else:
            moved = where - ILLUSTRATIVE_GAIN * short_right
            passes.append((where, moved, "C"))
        where = moved
    # What the picture says underneath has to be true of the arithmetic above
    # it, so the worst shortfall is carried out of the loop and checked.
    ended = max(needs - (where - left_at), needs - (right_at - where))
    print(f"    crowded from two sides, gain {ILLUSTRATIVE_GAIN}: worst shortfall "
          f"{', '.join(f'{v:.1f}' for v in worst)} mm over the three passes, "
          f"{ended:.1f} mm when they are done")
    assert ended >= worst[0], "the three passes have to leave A no better off"

    scale = 0.013
    for panel, (was, now, away_from) in enumerate(passes):
        table = Table(axis, (1.95, 5.95 - panel * 2.05), scale)
        for at in (left_at, right_at):
            table.glass((at, 0.0), neighbour_rim, colour=GLASS)
        table.ring((was, 0.0), colour=WARN)
        table.glass((now, 0.0), crowded_rim, colour=WARN, alpha=0.12)
        table.glass((was, 0.0), crowded_rim, colour=WARN)
        table.arrow((was, 0.0), (now, 0.0), colour=WARN, lw=1.8)
        # The names ride above their middles, where the dashed ring never
        # reaches, so the arrow has the middle line to itself.
        for at, name in ((left_at, "B"), (right_at, "C"), (was, "A")):
            note(axis, *table.at(at, 34.0), name, colour=INK, ha="center", size=LABEL_SIZE,
                 weight="bold")
        note(axis, table.at(left_at - neighbour_rim / 2.0, 0.0)[0] - 0.14,
             table.at(0.0, 0.0)[1], f"pass {panel + 1}", colour=INK, ha="right",
             size=LABEL_SIZE, weight="bold")
        note(axis, table.at(right_at + neighbour_rim / 2.0, 0.0)[0] + 0.30,
             table.at(0.0, 0.0)[1],
             f"A is shortest of room against {away_from},\nso it is pushed away from "
             f"{away_from}", colour=INK, ha="left", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, 0.78,
                  "The dashed ring is the room A needs. Three pushes carry A right, then "
                  "left, then right again, and leave it no closer to having room than when it "
                  "started.\nNo gain changes that, because the trouble is the direction and not "
                  "the distance. The budget is what ends it.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-crowded-from-two-sides.png", bottom - 0.10)
    save(figure, "nudge-pages-crowded-from-two-sides.png")


# --------------------------------------------------------------------------- #
# 6. nowhere to stand
# --------------------------------------------------------------------------- #


def nowhere_to_stand() -> None:
    """Why the approach binds harder than the departure.

    The jaw pushes along the line it points, so the approach runs along the
    push. Pushing a glass straight away from its neighbour therefore asks for
    the whole length of the tool to lie on the neighbour's side of it, and in a
    tight group that is where the neighbour is standing. Drawing the tool to
    scale is the only honest way to show how much room it wants.
    """
    width, height = 10.3, 5.2
    figure, axis = sheet(width, height)
    title(figure, axis, width, height - 0.12,
          "The approach runs along the push, and the tool is longer than the gap")

    crowded_rim, neighbour_rim = KIND_NARROWEST, KIND_WIDEST
    apart = 100.0
    scale = 0.0205
    table = Table(axis, (6.80, 3.00), scale)

    table.ring((0.0, 0.0), colour=WARN)
    table.glass((0.0, 0.0), crowded_rim, colour=WARN)

    # The closed jaw and the tool behind it, to scale, lying where the approach
    # has to put them: behind the glass, on the neighbour's side.
    tip = -(crowded_rim / 2.0 + APPROACH_GAP_MM)
    pieces = (
        (tip - FINGER_LENGTH_MM, FINGER_LENGTH_MM, JAW_THICKNESS_MM),
        (tip - FINGER_LENGTH_MM - BODY_LENGTH_MM, BODY_LENGTH_MM, BODY_SIZE_MM),
        (tip - FINGER_LENGTH_MM - BODY_LENGTH_MM - WRIST_LENGTH_MM, WRIST_LENGTH_MM, BODY_SIZE_MM),
    )
    for start, along, across in pieces:
        axis.add_patch(
            Rectangle(table.at(start, -across / 2.0), table.length(along), table.length(across),
                      facecolor=_tint(INK, 0.82), edgecolor=INK, lw=1.0, zorder=5)
        )
    # The neighbour last and half seen through, so the clash is the thing the
    # eye lands on.
    table.glass((-apart, 0.0), neighbour_rim, colour=GLASS, alpha=0.52, lw=1.4, zorder=6)
    table.arrow((0.0, 0.0), (48.0, 0.0), colour=WARN, lw=1.8)

    span(axis, table.at(tip - TOOL_LENGTH_MM, 0.0)[0], table.at(tip, 0.0)[0],
         table.at(0.0, -95.0)[1], colour=INK)
    note(axis, table.at(tip - TOOL_LENGTH_MM / 2.0, 0.0)[0], table.at(0.0, -106.0)[1],
         f"{TOOL_LENGTH_MM:.0f} mm of tool behind the fingertips, "
         f"{BODY_SIZE_MM:.0f} mm across at its widest",
         colour=INK, ha="center", size=NOTE_SIZE)
    note(axis, *table.at(-apart, 62.0), "the blocking neighbour\nis standing in it",
         colour=WARN, ha="center", size=NOTE_SIZE, weight="bold")
    note(axis, *table.at(0.0, -46.0), "the glass to be pushed", colour=INK, ha="center",
         size=NOTE_SIZE)
    note(axis, table.at(GRIP_ROOM_MM + 16.0, 0.0)[0], table.at(0.0, 0.0)[1],
         "the only heading\nthis method has", colour=WARN, ha="left", size=NOTE_SIZE)

    bottom = note(axis, width / 2.0, 0.60,
                  "A method that may choose another heading can ask for an approach the tool fits "
                  "into. This one has one heading, so when that heading is blocked the only honest "
                  "answer is a refusal.",
                  colour=INK, ha="center", size=NOTE_SIZE, figure=figure)
    finish(figure, axis, "nudge-pages-nowhere-to-stand.png", bottom - 0.10)
    save(figure, "nudge-pages-nowhere-to-stand.png")


def main() -> None:
    found = spans()
    print(f"the feet {DRAWN} drawn glasses of each kind stand on, seed {DRAW_SEED}:")
    for kind in KINDS:
        low, high = found[kind]
        print(f"    {KIND_NAMES[kind]:14s} {low:5.1f}-{high:5.1f} mm   "
              f"(tips at every friction below {TIPS_BELOW_MM:.0f} mm, "
              f"slides at every friction above {SLIDES_ABOVE_MM:.0f} mm)")
    the_error()
    the_gain()
    three_answers()
    the_parameters()
    crowded_from_two_sides()
    nowhere_to_stand()


if __name__ == "__main__":
    main()
