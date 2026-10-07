"""The pictures for the six pages of "geometry generates, a model ranks".

Those pages already had six pictures between them, covering the pipeline, the
position of the fitted part, the fan of job-finishing pushes and the spread of
the label. Five things in them were still prose that is really a shape, and
those five are drawn here. Everything else on those pages is a list or an
argument, and a picture of a list is padding.

    ranked-pages-the-inputs-slide.png       the same arrangement in two places
                                            in the zone, and which of the eight
                                            inputs that moves.
    ranked-pages-a-push-is-five-numbers.png what the solution actually hands
                                            back, and why it cannot curve.
    ranked-pages-what-the-fit-leaned-on.png which inputs the fitted trees used.
    ranked-pages-the-ablation.png           the ranker against the printed rule
                                            on the same tables, against the
                                            spread of the fit itself.
    ranked-pages-fitted-on-one-thing-marked-on-another.png
                                            the ranker winning on its own label
                                            and losing on the run's score.

A sixth was drawn and thrown away: a chart of boosting, one tree fitted to what
the sum of the previous ones got wrong. It came out as a textbook figure that
would sit as happily in any other document, and this repository asks a picture
to illustrate one specific idea from its own page.

Every number drawn here is read out of ``code/src/09_pushing-the-glasses-apart``
rather than out of a document. The three fitted figures are read straight from
the files the training run wrote, so nothing is transcribed by hand; the
geometric constants are copied with the file and the constant named beside
them.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_ranked_pages.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from diagram_style import (
    GLASS,
    GLASS_ZONE,
    GOOD,
    GRIP_ROOM,
    INK,
    MUTED,
    PAPER,
    WARN,
    bare,
    glass_from_above,
    has_room,
    new,
    push_arrow,
    save,
)
import matplotlib.pyplot as plt
from make_solution_flows_a import _tint
from matplotlib.patches import Circle, Rectangle

# ------------------------------------------------------------------ the numbers
#
# The geometry, in millimetres, each with the file and the constant it is a
# copy of. Nothing here is measured by eye.

APPROACH_GAP = 10.0        # 01-one-fixed-nudge/plan.py APPROACH_GAP = 0.010
FEEL_BEYOND = 30.0         # 01-one-fixed-nudge/plan.py FEEL_BEYOND = 0.030
AIM_MARGIN = 10.0          # 01-one-fixed-nudge/plan.py AIM_MARGIN = 0.010
STEP = 2.0                 # 01-one-fixed-nudge/plan.py STEP = 0.002
# GRIP_ROOM (70 mm) and GLASS_ZONE come from diagram_style, which copies them
# from bench/bench.py and rack/layout.py.

# The ablation, from the two files the runs wrote. Both ran the same loop over
# the same held-out tables with the same candidate set.
GLASSES = 251              # 02-geometry-ranked/results.json and rule.json, "glasses"
HELD_OUT = 50              # both files, "scenes"
RANKER_RACKED = 185        # results.json glasses_end.racked
RANKER_PUSHES = 229        # results.json pushes.total
RULE_RACKED = 195          # rule.json glasses_end.racked
RULE_PUSHES = 213          # rule.json pushes.total
# Three more rankers, each fitted on a bootstrap resample of the same rows and
# run over the same tables. 02-geometry-ranked/README.md records the three
# counts; the fit itself is deterministic, so resampling the rows is the only
# variation this method has.
RESAMPLED_RACKED = (180, 181, 184)

_TRAINING = (
    Path(__file__).resolve().parents[3]
    / "code" / "src" / "09_pushing-the-glasses-apart" / "02-geometry-ranked" / "training.json"
)


def _fit() -> dict:
    """What the training run recorded, read rather than copied out by hand."""
    if not _TRAINING.exists():
        raise SystemExit(f"{_TRAINING} is missing: run `make train` in that folder first")
    return json.loads(_TRAINING.read_text())


# The two inputs that describe the glass rather than the push. Named here
# because the picture of the importances groups them, and the names have to
# match features.py exactly or the grouping is a guess.
ABOUT_THE_GLASS = ("push height over the topple limit", "foot width")

# Shorter display names for the same eight inputs. Only the wording is
# shortened; nothing is merged or dropped.
SHORTER = {
    "contact angle, from the line to the nearest edge": "contact angle to the nearest edge",
}


# --------------------------------------------------------------------------- #
# 1. The inputs are relations, so most of them do not move with the arrangement
# --------------------------------------------------------------------------- #


def inputs_slide() -> None:
    """One crowded pair drawn twice in the glass zone, once slid across it.

    The page claims that the model cannot tell the two apart. Six of the eight
    inputs really are identical, because they are relations inside the
    arrangement and the arrangement moved as one piece. The other two are
    distances to the cell's own features, which did not move, so they change —
    and the picture is worth drawing because that is the half a reader gets
    wrong.
    """
    figure, axis = new(8.0, 6.8)
    bare(axis)
    axis.set_aspect("equal")

    x_min, x_max, y_min, y_max = GLASS_ZONE
    axis.add_patch(Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                             facecolor=_tint(MUTED, 0.94), edgecolor=MUTED,
                             lw=1.2, ls=(0, (5, 4)), zorder=0))
    axis.text(x_max - 8, y_max - 10, "the glass zone", fontsize=9.5, color=MUTED,
              ha="right", va="top", zorder=2)

    pushed_rim, neighbour_rim = 80.0, 95.0
    travel = 20.0 * STEP          # 40 mm, a whole number of the enumerator's steps
    apart = 95.0                  # between middles, which leaves the pushed glass short of room

    # Two places for the same pair. The second is the first slid up and across,
    # so every length and angle inside the pair is carried over unchanged.
    anchors = ((440.0, -370.0), (470.0, -210.0))
    distances = []

    for anchor in anchors:
        middle = anchor
        neighbour = (anchor[0] + apart, anchor[1])
        aim = (anchor[0] - travel, anchor[1])
        crowd = [(neighbour[0], neighbour[1], neighbour_rim)]

        # The pushed glass has no room where it stands, and has room with the
        # planner's aiming margin to spare where the push would put it. Checked
        # with the cell's own test rather than claimed.
        if has_room(middle, crowd):
            raise SystemExit(f"the pair at {anchor} is not crowded, so there is nothing to push")
        if math.dist(aim, neighbour) < GRIP_ROOM + neighbour_rim / 2.0 + AIM_MARGIN:
            raise SystemExit(f"the push from {anchor} does not free the glass")

        glass_from_above(axis, neighbour, neighbour_rim, colour=MUTED, alpha=0.22, edge=MUTED)
        glass_from_above(axis, middle, pushed_rim, colour=GLASS, alpha=0.30, edge=GLASS)
        # The jaw comes in on the far side of the glass from the way it travels,
        # so the push line starts outside the rim and ends where the glass lands.
        push_arrow(axis, (middle[0] + pushed_rim / 2.0 + 3, middle[1]), aim,
                   colour=INK, lw=1.6)
        axis.plot([aim[0]], [aim[1]], marker="o", markersize=7, color=INK, zorder=7)

        # How far the destination is from leaving the zone: the smaller of its
        # four distances to the sides, which is features.py zone_edge_distance.
        gaps = ((aim[0] - x_min, (x_min, aim[1])), (x_max - aim[0], (x_max, aim[1])),
                (aim[1] - y_min, (aim[0], y_min)), (y_max - aim[1], (aim[0], y_max)))
        gap, edge_point = min(gaps, key=lambda pair: pair[0])
        distances.append(gap)
        axis.plot([aim[0], edge_point[0]], [aim[1], edge_point[1]], color=WARN,
                  lw=1.5, ls=(0, (2, 2)), zorder=5)
        # Hung beside the middle of its own leader, on whichever side of the
        # line has clear paper: the labels are the only writing in the picture
        # and must not land on a glass.
        sideways = edge_point[1] == aim[1]
        axis.text((aim[0] + edge_point[0]) / 2.0 + (0 if sideways else -9),
                  (aim[1] + edge_point[1]) / 2.0 + (9 if sideways else 0),
                  f"{gap:.0f} mm", fontsize=10, color=WARN,
                  ha="center" if sideways else "right",
                  va="bottom" if sideways else "center",
                  weight="bold", zorder=7,
                  bbox=dict(boxstyle="round,pad=0.18", facecolor=PAPER, edgecolor="none"))

    axis.annotate("", xy=(466.0, -256.0), xytext=(442.0, -324.0), zorder=6,
                  arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.8))
    axis.text(482.0, -290.0, "the same pair,\nslid across the zone", fontsize=10,
              color=GOOD, ha="left", va="center", weight="bold", zorder=7)

    axis.set_xlim(x_min - 25, x_max + 25)
    axis.set_ylim(y_min - 60, y_max + 30)
    axis.set_title("Slide the arrangement and only its distance to the cell changes",
                   fontsize=12.5, color=INK, pad=12)
    axis.text(0.5, -0.03,
              "Each destination is marked with how far it is from leaving the zone. The angle, the "
              "travel, the room\nat the destination, the neighbour count, the foot width and the "
              "topple ratio are the same in both.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.8, color=MUTED)

    if abs(distances[0] - distances[1]) < 1.0:
        raise SystemExit("both destinations are the same distance from the zone edge: "
                         "the picture would show nothing")
    print(f"  destination to the zone edge: {distances[0]:.0f} mm, then {distances[1]:.0f} mm")
    save(figure, "ranked-pages-the-inputs-slide.png")


# --------------------------------------------------------------------------- #
# 2. What the solution hands back
# --------------------------------------------------------------------------- #


def a_push_is_five_numbers() -> None:
    """The parameterised push, drawn on the table, with its five numbers marked.

    The page says that this is the whole of what the solution contributes and
    that it cannot describe a push that curves. Both are easier to see on one
    straight line with the numbers hung off it than in a sentence.
    """
    figure, axis = new(9.0, 3.9)
    bare(axis)
    axis.set_aspect("equal")

    rim = 90.0
    travel = 32.0 * STEP                       # 64 mm, a whole number of steps
    reach = rim / 2.0 + APPROACH_GAP + FEEL_BEYOND
    middle = (0.0, 0.0)
    start = (-(rim / 2.0 + APPROACH_GAP), 0.0)
    aim = (travel, 0.0)

    glass_from_above(axis, middle, rim, colour=GLASS, alpha=0.28, edge=GLASS)
    axis.add_patch(Circle(aim, rim / 2.0, facecolor="none", edgecolor=GLASS,
                          lw=1.1, ls=(0, (3, 2)), zorder=4))
    axis.plot([start[0]], [start[1]], marker="o", markersize=7, color=INK, zorder=7)
    push_arrow(axis, start, (aim[0] + rim / 2.0, 0.0), colour=INK, lw=1.5)

    axis.text(start[0], 16, "start", fontsize=10, color=INK, ha="center",
              va="bottom", weight="bold")
    axis.text(aim[0] + rim / 2.0 + 6, 4, "heading", fontsize=10, color=INK,
              ha="left", va="bottom", weight="bold")
    axis.text(middle[0], -rim / 2.0 - 8, "the glass to move", fontsize=10,
              color=GLASS, ha="center", va="top", weight="bold")

    # The two lengths, on opposite sides of the line, because they start at
    # different points and overlap along it.
    def span(y, left, right, label, colour):
        axis.annotate("", xy=(right, y), xytext=(left, y), zorder=6,
                      arrowprops=dict(arrowstyle="<|-|>", color=colour, lw=1.2,
                                      shrinkA=0, shrinkB=0))
        axis.plot([left, left], [0, y], color=colour, lw=0.7, ls=(0, (2, 2)), zorder=3)
        axis.plot([right, right], [0, y], color=colour, lw=0.7, ls=(0, (2, 2)), zorder=3)
        axis.text((left + right) / 2.0, y + (6 if y > 0 else -6), label, fontsize=9.5,
                  color=colour, ha="center", va="bottom" if y > 0 else "top", weight="bold")

    span(72, middle[0], aim[0], f"travel, {travel:.0f} mm", GOOD)
    span(-96, start[0], start[0] + reach, f"reach, {reach:.0f} mm", WARN)

    axis.set_xlim(start[0] - 55, aim[0] + rim / 2.0 + 88)
    axis.set_ylim(-146, 116)
    axis.set_title("A push is five numbers, and every one of them is on one straight line",
                   fontsize=12.5, color=INK, pad=10)
    axis.text(0.5, -0.04,
              "Which glass, where the fingertips come down, which way the jaw points, how far to "
              "feel forward, how far to push.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.6, color=MUTED)

    print(f"  start {start[0]:.0f} mm behind the middle, reach {reach:.0f} mm, "
          f"travel {travel:.0f} mm, aiming {AIM_MARGIN:.0f} mm past where the room begins")
    save(figure, "ranked-pages-a-push-is-five-numbers.png")


# --------------------------------------------------------------------------- #
# 3. What the fit leaned on
# --------------------------------------------------------------------------- #


def what_the_fit_leaned_on() -> None:
    """The eight inputs, with the share of the fit each one carried.

    The page says the model mostly learned which glass is risky to push rather
    than which push is good. That claim is one number beside another, and the
    gap between the first two bars and the other six is the whole of it.
    """
    fit = _fit()
    pairs = [(name, share) for name, share in fit["importances"]]
    pairs.sort(key=lambda pair: pair[1])

    figure, axis = new(9.0, 4.4)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.set_yticks([])

    about_glass = sum(share for name, share in pairs if name in ABOUT_THE_GLASS)
    about_push = sum(share for name, share in pairs if name not in ABOUT_THE_GLASS)

    for index, (name, share) in enumerate(pairs):
        glassy = name in ABOUT_THE_GLASS
        colour = WARN if glassy else GLASS
        axis.barh(index, share, height=0.62, color=_tint(colour, 0.55),
                  edgecolor=colour, lw=1.2, zorder=3)
        axis.text(-0.006, index, SHORTER.get(name, name), fontsize=9.5,
                  color=INK if glassy else MUTED, ha="right", va="center",
                  weight="bold" if glassy else "normal")
        axis.text(share + 0.008, index, f"{share:.3f}", fontsize=9, color=colour,
                  ha="left", va="center", weight="bold" if glassy else "normal")

    # The two group notes stand to the right of the longest bar, because every
    # row to their left is drawn on.
    for low, high, share, colour, words in (
        (6, 7, about_glass, WARN, "these two describe the glass"),
        (0, 5, about_push, GLASS, "these six describe the push"),
    ):
        axis.plot([0.475, 0.49, 0.49, 0.475], [low, low, high, high], color=colour,
                  lw=1.2, zorder=3)
        axis.text(0.505, (low + high) / 2.0, f"{words}: {share:.2f}", fontsize=10,
                  color=colour, ha="left", va="center", weight="bold")

    axis.set_xlim(0, 0.72)
    # No tick beyond the longest bar: the empty half of the axis is there for
    # the two notes, not for a scale nothing reaches.
    axis.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4])
    axis.set_ylim(-0.8, len(pairs) - 0.2)
    axis.set_xlabel("share of the fitted trees' predictions this input accounted for",
                    fontsize=9, color=MUTED)
    axis.tick_params(axis="x", colors=MUTED, labelsize=8.5)
    axis.set_title("What the fit leaned on", fontsize=12.5, color=INK, pad=12)

    print(f"  about the glass {about_glass:.3f}, about the push {about_push:.3f}, "
          f"over {fit['rows']} rows from {fit['tables']} tables")
    save(figure, "ranked-pages-what-the-fit-leaned-on.png")


# --------------------------------------------------------------------------- #
# 4. The ablation
# --------------------------------------------------------------------------- #


def the_ablation() -> None:
    """Glasses racked by the rule and by the ranker, against the spread of the fit.

    A reader's first answer to "the ranker racked ten fewer" is that the fit
    was unlucky. Putting the three resampled fits on the same line answers that
    without a sentence: the gap is wider than anything the fitting moves.
    """
    figure, axis = new(9.0, 2.7)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.set_yticks([])

    fits = sorted((RANKER_RACKED, *RESAMPLED_RACKED))
    axis.add_patch(Rectangle((fits[0] - 0.4, -0.42), fits[-1] - fits[0] + 0.8, 0.84,
                             facecolor=_tint(WARN, 0.84), edgecolor="none", zorder=1))
    for racked in RESAMPLED_RACKED:
        axis.plot([racked], [0], marker="o", markersize=8, markerfacecolor="white",
                  markeredgecolor=WARN, markeredgewidth=1.6, zorder=4)
    axis.plot([RANKER_RACKED], [0], marker="o", markersize=11, color=WARN, zorder=5)
    axis.plot([RULE_RACKED], [0], marker="o", markersize=11, color=GOOD, zorder=5)

    axis.text(RANKER_RACKED, 0.30, "the ranker", fontsize=10.5, color=WARN,
              ha="center", va="bottom", weight="bold")
    axis.text(RULE_RACKED, 0.30, "the printed rule", fontsize=10.5, color=GOOD,
              ha="center", va="bottom", weight="bold")
    axis.text((fits[0] + fits[-1]) / 2.0, -0.52,
              f"four fits of the same model:\n{fits[0]} to {fits[-1]}",
              fontsize=9, color=WARN, ha="center", va="top")

    axis.annotate("", xy=(RULE_RACKED, 0.78), xytext=(RANKER_RACKED, 0.78), zorder=6,
                  arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.2, shrinkA=0, shrinkB=0))
    axis.text((RANKER_RACKED + RULE_RACKED) / 2.0, 0.84,
              f"{RULE_RACKED - RANKER_RACKED} glasses", fontsize=10, color=INK,
              ha="center", va="bottom", weight="bold")

    axis.set_xlim(177.5, 198.5)
    axis.set_ylim(-1.15, 1.3)
    # Whole glasses: a tick reading 182.5 would be a count of nothing.
    axis.set_xticks([180, 185, 190, 195])
    axis.set_xlabel(f"glasses racked, of {GLASSES}, over the same {HELD_OUT} held-out tables",
                    fontsize=9, color=MUTED)
    axis.tick_params(axis="x", colors=MUTED, labelsize=8.5)
    axis.set_title("The ranker loses by more than the fitting varies",
                   fontsize=12.5, color=INK, pad=12)
    axis.text(0.5, -0.40,
              f"Same candidates, same budget; only the choosing differs. "
              f"The rule spent {RULE_PUSHES} pushes and the ranker {RANKER_PUSHES}.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.6, color=MUTED)

    print(f"  rule {RULE_RACKED}, ranker {RANKER_RACKED}, resampled fits {RESAMPLED_RACKED}")
    save(figure, "ranked-pages-the-ablation.png")


# --------------------------------------------------------------------------- #
# 5. Fitted on one thing, marked on another
# --------------------------------------------------------------------------- #


def fitted_on_one_thing() -> None:
    """The same two choosers, measured by the label and by the run's score.

    This is the finding of the whole solution and it is a reversal, which is
    the one shape a sentence carries badly: the ranker is the better chooser of
    the two by the quantity it was fitted to, and the worse one by the quantity
    the run is marked on.
    """
    fit = _fit()
    decision = fit["validation"]["a decision"]
    offering = decision["groups_offering_a_job_finishing_push"]
    ranker_takes = decision["where_the_rankers_top_pick_finishes_the_job"]
    regret = decision["regret_mm_mean"]

    figure, (top, bottom) = plt.subplots(2, 1, figsize=(9.0, 4.4))
    figure.patch.set_facecolor(PAPER)
    figure.subplots_adjust(top=0.80, bottom=0.14, left=0.26, right=0.97, hspace=0.75)

    def row(axis, values, limit, title, unit):
        for side in axis.spines.values():
            side.set_visible(False)
        axis.set_yticks([])
        for index, (label, value, colour) in enumerate(values):
            axis.barh(index, value, height=0.5, color=_tint(colour, 0.55),
                      edgecolor=colour, lw=1.2, zorder=3)
            axis.text(-limit * 0.015, index, label, fontsize=10, color=colour,
                      ha="right", va="center", weight="bold")
            axis.text(value + limit * 0.015, index, unit.format(value), fontsize=9.5,
                      color=colour, ha="left", va="center", weight="bold")
        axis.set_xlim(0, limit)
        axis.set_ylim(-0.6, 1.6)
        axis.set_xticks([])
        axis.set_title(title, fontsize=11, color=INK, pad=8, loc="left")

    row(top,
        [("the ranker", ranker_takes, WARN), ("the printed rule", offering, GOOD)],
        offering * 1.24,
        f"What the run is marked on: top picks that finish a glass, of {offering}",
        "{:.0f}")
    row(bottom,
        [("the ranker", regret["ranker"], GOOD), ("the printed rule", regret["printed rule"], WARN)],
        regret["printed rule"] * 1.24,
        "What the model was fitted on: room given up against the best candidate",
        "{:.1f} mm")

    figure.suptitle("The ranker wins on its own label and loses on the score",
                    fontsize=12.5, color=INK, y=0.99)
    figure.text(0.5, 0.02,
                "Room gained and glasses made grippable are not the same quantity, and the "
                "second is the one the run is marked on.",
                ha="center", va="bottom", fontsize=8.6, color=MUTED)

    print(f"  finishes a glass: ranker {ranker_takes} of {offering}, rule {offering} of {offering}; "
          f"room given up: ranker {regret['ranker']:.2f} mm, rule {regret['printed rule']:.2f} mm")
    save(figure, "ranked-pages-fitted-on-one-thing-marked-on-another.png")


def main() -> None:
    inputs_slide()
    a_push_is_five_numbers()
    what_the_fit_leaned_on()
    the_ablation()
    fitted_on_one_thing()


if __name__ == "__main__":
    main()
