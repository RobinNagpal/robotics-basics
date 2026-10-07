"""Four pictures for the two chapters on solutions 1 and 2.

Each one carries a shape its page's prose cannot carry on its own, and each one
makes a claim that is computed here from the code's own constants and asserted
before the figure is drawn, so a picture cannot quietly go stale when a constant
moves.

    05-one-split-is-not-enough.png
        Three glasses of one kind run together into one patch of dots. One cut
        leaves two parts that are both still too wide to be one glass, and the
        same question asked again settles every part. The widths written on it
        come from this file running the code's own ``halve`` and ``footprint``
        on the drawn arrangement.

    05-why-two-outlines-meet.png
        The same two places on the table, drawn twice. With the two glasses the
        same height the gap between their outlines grows; with the near one at
        the tall end of the kind and the far one at the short end it closes to
        nothing. Which of the two happens is a question about the difference in
        height, and the picture is the only honest way to say that.

    06-what-the-deepest-unit-sees.png
        How much table one unit of TopNet's deepest layer depends on, against
        the 150 mm the cell guarantees between two glass centres, and against
        what the same stack would see without its two dilated convolutions.

    06-the-vote-has-to-land-in-the-picture.png
        One survey station's picture, and the box a glass has to stand inside
        for its own rim's middle to be imaged within that picture at all. A
        vote landing outside is dropped, so a glass standing outside the box
        casts no pile anywhere.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_rules_and_network_pages.py
"""

from __future__ import annotations

import math

import numpy as np
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    KIND_NARROWEST,
    KIND_SHORTEST,
    KIND_TALLEST,
    KIND_WIDEST,
    LABEL_SIZE,
    MUTED,
    WARN,
    save,
    splay_circles,
    splay_patch,
)
from make_solution_flows_a import _audit, _figure, _note, _title, _tint
from matplotlib.patches import Ellipse, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Every one of these is a constant in code/src/08_seeing-the-glasses/, and the
# comment after it says which file it lives in.

GROUPING_MM = 25.0        # GROUPING in 01-rules-on-the-table/find.py
CENTRES_MM = 150.0        # MIN_SEPARATION in work_cell/glasses/spawn.py
SURVEY_MM = 450.0         # SURVEY_HEIGHT in work_cell/arm/dimensions.py
FOCAL_PX = (320 / 2.0) / math.tan(1.047 / 2.0)   # FOCAL in bench/render.py
FRAME_PX = (320, 240)     # WIDTH, HEIGHT in bench/render.py
SHRINK = 2                # SHRINK in 02-train-from-scratch/models.py
ZONE_MM = (320.0, 360.0)  # GLASS_ZONE in work_cell/rack/layout.py, as a size

# TopNet's layers in order, as (window, dilation, stride), read off models.py:
# at_full, at_half, at_quarter, and nothing below that.
TOP_NET = ((3, 1, 1), (3, 1, 1), (3, 1, 2), (3, 1, 1), (3, 1, 2), (3, 2, 1), (3, 4, 1))
NO_DILATION = 5           # how many of those layers come before the dilated pair

# What one pixel of the full-size picture covers on the table top, in mm.
MM_PER_PIXEL = SURVEY_MM / FOCAL_PX


def splay(height_mm: float) -> float:
    """How much further out than its own place a slice at this height is drawn."""
    return SURVEY_MM / (SURVEY_MM - height_mm)


def receptive_field(layers) -> int:
    """How many pixels of the input one unit after these layers depends on."""
    reach, stride = 1, 1
    for window, dilation, step in layers:
        reach += (window - 1) * dilation * stride
        stride *= step
    return reach


# ------------------------------------------------- the code's own split, re-run
#
# ``halve`` and the circle fit are copied from 01-rules-on-the-table/find.py so
# that the widths written on the first picture are the ones that code produces,
# and not a drawing of what somebody expected it to produce. The convex hull is
# written out here because this environment has no OpenCV.


def _turn(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def hull(points: np.ndarray) -> np.ndarray:
    """The outside of a patch of dots, by the monotone chain. cv2.convexHull's job."""
    ordered = sorted(map(tuple, points))

    def side(sequence):
        out: list = []
        for point in sequence:
            while len(out) >= 2 and _turn(out[-2], out[-1], point) <= 0:
                out.pop()
            out.append(point)
        return out[:-1]

    return np.array(side(ordered) + side(ordered[::-1]))


def circle_width(dots: np.ndarray) -> float:
    """find.circle_width: the one-shot least-squares circle through a ring of dots."""
    terms = np.column_stack([dots, np.ones(len(dots))])
    solved = np.linalg.lstsq(terms, (dots**2).sum(1), rcond=None)[0]
    x, y = solved[0] / 2.0, solved[1] / 2.0
    return 2.0 * float(np.sqrt(max(solved[2] + x * x + y * y, 0.0)))


def footprint(dots: np.ndarray) -> float:
    """find.footprint: the width of the circle round the patch the dots mark."""
    return circle_width(hull(dots))


def halve(dots: np.ndarray) -> np.ndarray:
    """find.halve: k-means with two centres, seeded at the ends of the long axis."""
    middle = dots.mean(0)
    along = (dots - middle) @ np.linalg.svd(dots - middle, full_matrices=False)[2][0]
    seeds = dots[[int(along.argmin()), int(along.argmax())]]
    mine = along > 0
    for _ in range(20):
        nearer = np.linalg.norm(dots - seeds[1], axis=1) < np.linalg.norm(dots - seeds[0], axis=1)
        if not nearer.any() or nearer.all() or (nearer == mine).all():
            break
        mine = nearer
        seeds = np.stack([dots[~mine].mean(0), dots[mine].mean(0)])
    return mine


# --------------------------------------------------------------------------- #
# 1. one split is not enough
# --------------------------------------------------------------------------- #

SPLIT_RIM_MM = 70.0       # inside the kind's 65-105 mm
SPLIT_CENTRES_MM = 74.0   # about half of the 150 mm the layout rule guarantees
SPLIT_STEP_MM = 3.0       # how far apart the drawn dots are laid


def _three_glasses() -> np.ndarray:
    """The dots three glasses of one kind leave when they stand 80 mm apart."""
    radius = SPLIT_RIM_MM / 2.0
    grid = np.arange(-radius, radius + 1e-9, SPLIT_STEP_MM)
    dots = [
        (which * SPLIT_CENTRES_MM + across, up)
        for which in (-1, 0, 1)
        for across in grid
        for up in grid
        if across * across + up * up <= radius * radius
    ]
    return np.array(dots)


def one_split_is_not_enough() -> None:
    """Why the width check is asked again of every part a split produces.

    The arrangement is drawn once and cut twice, which is the one idea: a chain
    of three glasses cannot be settled by halving it once, because half of three
    is still more than one. The widths are this file running the code's own
    functions over the dots it drew.
    """
    dots = _three_glasses()
    whole = footprint(dots)
    cut = halve(dots)
    halves = [dots[~cut], dots[cut]]
    widths = [footprint(part) for part in halves]

    quarters, quarter_widths = [], []
    for part in halves:
        again = halve(part)
        for piece in (part[~again], part[again]):
            quarters.append(piece)
            quarter_widths.append(footprint(piece))

    # The claim the picture makes, checked before it is drawn.
    assert whole > KIND_WIDEST, whole
    assert min(widths) > KIND_WIDEST, widths
    assert all(KIND_NARROWEST <= w <= KIND_WIDEST for w in quarter_widths), quarter_widths
    # And the arrangement really is one group: the strip of bare table between
    # two of these glasses is narrower than the grouping distance.
    assert SPLIT_CENTRES_MM - SPLIT_RIM_MM < GROUPING_MM

    figure, axis, aspect = _figure(10.4, 42.0)

    left, right = 50.0, 94.0
    span_mm = 2 * SPLIT_CENTRES_MM + SPLIT_RIM_MM
    scale = (right - left) / span_mm          # chart units per mm, across
    middle_x = (left + right) / 2.0
    half_tall = SPLIT_RIM_MM / 2.0 * scale * aspect

    def place(part, row_y, colour):
        axis.plot(
            middle_x + part[:, 0] * scale,
            row_y + part[:, 1] * scale * aspect,
            marker="o", ms=1.6, ls="none", color=colour, alpha=0.85, zorder=4,
        )

    rows = (34.0, 22.0, 10.0)
    headings = (
        ("One group", f"{whole:.0f} mm across, too wide for one glass", WARN),
        ("One cut", "both parts are still too wide", WARN),
        ("Asked again", "every part is a width the kind allows", GOOD),
    )
    for row_y, (heading, verdict, colour) in zip(rows, headings, strict=True):
        _note(axis, 4.0, row_y + 0.8, heading, colour=INK, ha="left", va="bottom",
              weight="bold", size=LABEL_SIZE + 0.6)
        _note(axis, 4.0, row_y - 0.8, verdict, colour=colour, ha="left", va="top")

    def widths_on(parts, values, row_y, colours, size=None):
        """A span line as wide as the fitted circle, under each part, and its width."""
        for part, value, colour in zip(parts, values, colours, strict=True):
            at = middle_x + part[:, 0].mean() * scale
            reach = value / 2.0 * scale
            line_y = row_y - half_tall - 1.0
            axis.plot([at - reach, at + reach], [line_y, line_y], color=colour, lw=1.2,
                      zorder=6)
            for end in (at - reach, at + reach):
                axis.plot([end, end], [line_y - 0.3, line_y + 0.3], color=colour, lw=1.2,
                          zorder=6)
            _note(axis, at, line_y - 0.6, f"{value:.0f} mm", colour=colour, ha="center",
                  va="top", weight="bold", size=size or 8.4)

    place(dots, rows[0], GLASS)
    widths_on([dots], [whole], rows[0], [WARN])

    for part, colour in zip(halves, (GOOD, GLASS), strict=True):
        place(part, rows[1], colour)
    widths_on(halves, widths, rows[1], (WARN, WARN))

    for part, colour in zip(quarters, (GOOD, GLASS, GOOD, GLASS), strict=True):
        place(part, rows[2], colour)
    widths_on(quarters, quarter_widths, rows[2], (GOOD,) * 4, size=7.6)

    _note(axis, 50.0, 0.6,
          f"Three glasses of one kind, {SPLIT_CENTRES_MM:.0f} mm between centres, which "
          f"leaves {SPLIT_CENTRES_MM - SPLIT_RIM_MM:.0f} mm of bare table: under the "
          f"{GROUPING_MM:.0f} mm grouping distance, so the three are one group.\n"
          f"The kind allows {KIND_NARROWEST:.0f} to {KIND_WIDEST:.0f} mm.",
          colour=INK, ha="center", va="bottom")

    _title(axis, "One cut cannot settle a chain of three, because half of three is still more than one")
    _audit(figure, "05-one-split-is-not-enough.png")
    save(figure, "05-one-split-is-not-enough.png")


# --------------------------------------------------------------------------- #
# 2. the two routes by which two outlines meet
# --------------------------------------------------------------------------- #

NEAR_MM = 100.0    # how far the near glass stands from the point below the camera
FAR_MM = 220.0     # and the far one, on the same line out from it
PAIR_RIM_MM = 90.0
SAME_HEIGHT_MM = 150.0


def _gap(near_height: float, far_height: float) -> float:
    """The bare table between the two outlines, in the picture, in millimetres."""
    near_edge = NEAR_MM * splay(near_height) + PAIR_RIM_MM / 2.0 * splay(near_height)
    far_edge = FAR_MM * splay(far_height) - PAIR_RIM_MM / 2.0 * splay(far_height)
    return far_edge - near_edge


def why_two_outlines_meet() -> None:
    """The same two places, drawn with two glasses of one height and of two.

    Both panels hold the same two places on the table, so the only thing that
    changes between them is how tall each glass is. That is the whole claim:
    whether two outlines meet is a question about the difference in their
    heights, and a reader who has only been told that splay throws outlines
    outwards will expect the left panel to be the dangerous one.
    """
    on_the_table = (FAR_MM - PAIR_RIM_MM / 2.0) - (NEAR_MM + PAIR_RIM_MM / 2.0)
    same = _gap(SAME_HEIGHT_MM, SAME_HEIGHT_MM)
    differing = _gap(KIND_TALLEST, KIND_SHORTEST)

    # The claim: equal heights push the two outlines further apart than they
    # stand, and a tall glass in front of a short one closes the gap entirely.
    assert same > on_the_table > 0.0, (same, on_the_table)
    assert differing < 0.0, differing

    figure, axis, aspect = _figure(11.0, 33.0)

    nadir_x, scale = 6.0, 0.105        # chart units per mm, across
    panels = (
        (24.0, SAME_HEIGHT_MM, SAME_HEIGHT_MM, GOOD,
         "Both glasses the same height",
         f"the gap grows:\n{on_the_table:.0f} mm on the table,\n{same:.0f} mm in the picture"),
        (9.5, KIND_TALLEST, KIND_SHORTEST, WARN,
         "The near one tall, the far one short",
         "the gap closes:\nthe two outlines run\n"
         f"together over {abs(differing):.0f} mm"),
    )

    for line_y, near_height, far_height, colour, heading, verdict in panels:
        axis.plot([nadir_x, 54.0], [line_y, line_y], color=MUTED, lw=1.0,
                  ls=(0, (5, 4)), zorder=2)
        axis.plot([nadir_x], [line_y], marker="x", ms=8.0, color=INK, zorder=6)
        _note(axis, nadir_x, line_y - 1.0, "camera\nabove here", colour=MUTED, ha="center",
              va="top", size=LABEL_SIZE - 1.2)

        for stand, height in ((NEAR_MM, near_height), (FAR_MM, far_height)):
            circles = splay_circles((0.0, 0.0), (stand, 0.0), height, PAIR_RIM_MM,
                                    survey_h=SURVEY_MM)
            for offset, radius in circles:
                axis.add_patch(
                    Ellipse(
                        (nadir_x + offset[0] * scale, line_y + offset[1] * scale * aspect),
                        2 * radius * scale, 2 * radius * scale * aspect,
                        facecolor=_tint(colour, 0.55), edgecolor="none", alpha=0.20,
                        zorder=3,
                    )
                )
            axis.add_patch(
                Ellipse((nadir_x + stand * scale, line_y),
                        PAIR_RIM_MM * scale, PAIR_RIM_MM * scale * aspect,
                        facecolor="none", edgecolor=INK, lw=1.2, zorder=7)
            )

        _note(axis, nadir_x, line_y + 7.2, heading, colour=INK, ha="left", va="bottom",
              size=LABEL_SIZE + 0.6, weight="bold")
        _note(axis, 60.0, line_y, verdict, colour=colour, ha="left", va="center",
              weight="bold")

    _note(axis, 50.0, 0.6,
          "The same two places on the table in both, the rings. "
          "The pale shapes are what the camera draws.",
          colour=MUTED, ha="center", va="bottom")

    _title(axis, "Whether two outlines meet is a question about the difference in their heights")
    _audit(figure, "05-why-two-outlines-meet.png")
    save(figure, "05-why-two-outlines-meet.png")


# --------------------------------------------------------------------------- #
# 3. how much table the deepest unit of the network sees
# --------------------------------------------------------------------------- #


def what_the_deepest_unit_sees() -> None:
    """The deepest layer's reach, turned into a distance on the table.

    The section it belongs to asks one question — can the one layer with enough
    context to reason about a neighbour see two glasses at once? — and the
    answer is a comparison between two lengths, which is what the picture is.
    """
    deep = receptive_field(TOP_NET)
    shallow = receptive_field(TOP_NET[:NO_DILATION])
    deep_mm = deep * SHRINK * MM_PER_PIXEL
    shallow_mm = shallow * SHRINK * MM_PER_PIXEL

    # The claim: with the dilated pair the deepest unit reaches across the gap
    # the cell guarantees, and without them it does not reach across one glass.
    assert deep_mm > CENTRES_MM > shallow_mm, (deep_mm, CENTRES_MM, shallow_mm)
    assert shallow_mm < KIND_WIDEST, shallow_mm

    figure, axis, aspect = _figure(9.8, 28.0)

    scale = 0.13                     # chart units per mm, across
    middle_x, middle_y = 50.0, 15.0

    def box(width_mm, colour, lw, dashed=False):
        half = width_mm / 2.0 * scale
        axis.add_patch(
            Rectangle(
                (middle_x - half, middle_y - half * aspect),
                2 * half, 2 * half * aspect,
                facecolor="none", edgecolor=colour, lw=lw, zorder=5,
                linestyle=(0, (5, 4)) if dashed else "solid",
            )
        )
        return half

    deep_half = box(deep_mm, GOOD, 2.0)
    shallow_half = box(shallow_mm, WARN, 1.6, dashed=True)

    for side in (-1, 1):
        axis.add_patch(
            Ellipse((middle_x + side * CENTRES_MM / 2.0 * scale, middle_y),
                    KIND_WIDEST * scale, KIND_WIDEST * scale * aspect,
                    facecolor=_tint(GLASS, 0.70), edgecolor=GLASS, lw=1.3, zorder=4)
        )
    arrow_y = middle_y + 0.45 * deep_half * aspect
    axis.annotate(
        "", xy=(middle_x - CENTRES_MM / 2.0 * scale, arrow_y),
        xytext=(middle_x + CENTRES_MM / 2.0 * scale, arrow_y),
        arrowprops={"arrowstyle": "<|-|>", "color": INK, "lw": 1.3}, zorder=8,
    )
    _note(axis, middle_x, arrow_y + 0.6,
          f"{CENTRES_MM:.0f} mm:\nthe closest two glasses stand", colour=INK,
          ha="center", va="bottom", weight="bold")

    _note(axis, middle_x, middle_y + deep_half * aspect + 1.0,
          f"{deep_mm:.0f} mm: what one unit of the deepest layer sees",
          colour=GOOD, ha="center", va="bottom", weight="bold")
    axis.annotate(
        "", xy=(middle_x - shallow_half, middle_y - shallow_half * aspect),
        xytext=(middle_x - 6.0, middle_y - deep_half * aspect - 2.2),
        arrowprops={"arrowstyle": "-|>", "color": WARN, "lw": 1.2}, zorder=8,
    )
    _note(axis, middle_x - 6.0, middle_y - deep_half * aspect - 2.4,
          f"{shallow_mm:.0f} mm without the two dilated convolutions",
          colour=WARN, ha="center", va="top", weight="bold")

    _note(axis, 50.0, 0.6,
          f"{deep} pixels of the half-size picture, {deep * SHRINK} of the full one, "
          f"at {MM_PER_PIXEL:.2f} mm of table each.",
          colour=MUTED, ha="center", va="bottom")

    _title(axis, "The deepest unit reaches across the gap the cell guarantees, because of the dilations")
    _audit(figure, "06-what-the-deepest-unit-sees.png")
    save(figure, "06-what-the-deepest-unit-sees.png")


# --------------------------------------------------------------------------- #
# 4. a vote has to land inside the picture
# --------------------------------------------------------------------------- #


def vote_has_to_land_in_the_picture() -> None:
    """The box a glass stands inside if its own middle is to be imaged at all.

    One station's picture, drawn as the table it covers, with the box for the
    tall end of the kind and the box for the short end marked on it. The idea
    the picture carries is that the box shrinks as the glass gets taller, which
    no amount of prose makes as plain as two rectangles inside one frame.
    """
    frame_mm = (FRAME_PX[0] * MM_PER_PIXEL, FRAME_PX[1] * MM_PER_PIXEL)
    tall = tuple(side / splay(KIND_TALLEST) for side in frame_mm)
    short = tuple(side / splay(KIND_SHORTEST) for side in frame_mm)

    # The claim: a glass at the tall end of the kind has to stand well inside
    # the zone for its own middle to be in the picture, and one at the short
    # end does not.
    assert tall[0] < ZONE_MM[0] and tall[1] < ZONE_MM[1], tall
    assert short[0] > ZONE_MM[0], short

    figure, axis, aspect = _figure(10.2, 36.0)

    scale = 0.135
    middle_x, middle_y = 42.0, 18.0

    def box(size, colour, lw, dashed=False, fill=None):
        half = (size[0] / 2.0 * scale, size[1] / 2.0 * scale * aspect)
        axis.add_patch(
            Rectangle(
                (middle_x - half[0], middle_y - half[1]), 2 * half[0], 2 * half[1],
                facecolor="none" if fill is None else fill, edgecolor=colour, lw=lw,
                linestyle=(0, (5, 4)) if dashed else "solid", zorder=4,
            )
        )
        return half

    box(ZONE_MM, MUTED, 1.2, fill=_tint(MUTED, 0.94))
    frame_half = box(frame_mm, INK, 1.6)
    zone_half = (ZONE_MM[0] / 2.0 * scale, ZONE_MM[1] / 2.0 * scale * aspect)
    short_half = box(short, GLASS, 1.4, dashed=True)
    tall_half = box(tall, GOOD, 2.0)

    axis.plot([middle_x], [middle_y], marker="x", ms=8.0, color=INK, zorder=8)

    # One tall glass standing outside the box, and where its own middle lands.
    stands = (145.0, 40.0)
    lands = tuple(value * splay(KIND_TALLEST) for value in stands)
    assert abs(lands[0]) > frame_mm[0] / 2.0, lands
    here = (middle_x + stands[0] * scale, middle_y + stands[1] * scale * aspect)
    there = (middle_x + lands[0] * scale, middle_y + lands[1] * scale * aspect)
    axis.add_patch(Ellipse(here, KIND_WIDEST * scale, KIND_WIDEST * scale * aspect,
                           facecolor=_tint(WARN, 0.72), edgecolor=WARN, lw=1.3, zorder=6))
    axis.annotate("", xy=there, xytext=here,
                  arrowprops={"arrowstyle": "-|>", "color": WARN, "lw": 1.5,
                              "linestyle": (0, (4, 3))}, zorder=7)
    axis.plot([there[0]], [there[1]], marker="x", ms=9.0, mew=2.0, color=WARN, zorder=8)

    for half, text, colour in (
        (frame_half, "one station's picture", INK),
        (zone_half, "the glass zone", MUTED),
        (short_half, "the shortest glass of the kind may stand here", GLASS),
        (tall_half, "and the tallest, only here", GOOD),
    ):
        _note(axis, middle_x, middle_y + half[1] - 0.4, text, colour=colour,
              ha="center", va="top", weight="bold", size=8.0)

    _note(axis, here[0], here[1] - KIND_WIDEST / 2.0 * scale * aspect - 0.5,
          "a tall glass\nstands here", colour=WARN, ha="center", va="top", weight="bold")
    _note(axis, middle_x, middle_y - 1.0, "the camera is\nabove here", colour=INK,
          ha="center", va="top", size=8.0)
    _note(axis, there[0] + 0.8, there[1], "its own middle\nis drawn here,\nand the vote\nis dropped",
          colour=WARN, ha="left", va="center", weight="bold")

    _note(axis, 50.0, 0.6,
          "The three stations stand in a line along the zone, "
          "so it is the sideways edges that are beyond all of them.",
          colour=MUTED, ha="center", va="bottom")

    _title(axis, "A vote cast outside the picture is dropped, so the glass that cast it makes no pile")
    _audit(figure, "06-the-vote-has-to-land-in-the-picture.png")
    save(figure, "06-the-vote-has-to-land-in-the-picture.png")


def main() -> None:
    one_split_is_not_enough()
    why_two_outlines_meet()
    what_the_deepest_unit_sees()
    vote_has_to_land_in_the_picture()


if __name__ == "__main__":
    main()
