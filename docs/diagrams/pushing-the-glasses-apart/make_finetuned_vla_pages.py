"""The pictures for the same-model-fine-tuned-here pages past the first one.

The first page of that solution already carries two charts from
``make_solution_flows_b.py``: the chain with the training step put in front of
it, and what a low-rank correction is. The chapter's own measurements were not
drawn anywhere, and four of them are shape rather than sentence. Those four are
here.

    finetuned-how-far-the-answer-was.png     how it works, the domain gap: the
                                        untrained model's waypoints land a
                                        median of 321 mm from the teacher's,
                                        which is wider than the glass zone.
    finetuned-the-height-not-the-length.png  how it works, what the training
                                        bought: the chunk came down to the
                                        height a push happens at and stayed
                                        three times too long.
    finetuned-the-same-push-in-fewer-waypoints.png  the code, ``resampled``:
                                        the same 89 mm of table in fewer
                                        waypoints is the same path carried out
                                        faster, because the period is fixed.
    finetuned-where-the-jaw-comes-down.png   a worked example: the chunk's
                                        first waypoint decides whether the
                                        descent reaches push height or meets a
                                        glass, which is this solution's whole
                                        failure.

Two pages were considered and left with no picture of their own. "What it
needs" is a bill — libraries, a machine, data, a licence — and every item on it
is a sentence, so a picture of it would be a picture of a list. "How it
compares" names seven general ideas and five comparisons, which read as prose;
the one thing on it that is shape, where the pushes went before and after the
training, is already drawn by ``make_six_solutions_pages.py`` and that picture
is simply shown there.

Every number below is read out of ``code/src/09_pushing-the-glasses-apart/``
and the file it came from is named beside it. Every claim a picture makes is
computed here from those numbers and asserted, so a picture that stopped being
true would stop the run rather than be written.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_finetuned_vla_pages.py
"""

from __future__ import annotations

import numpy as np
from diagram_style import (
    GLASS,
    GLASS_ZONE,
    GOOD,
    INK,
    KIND_TALLEST,
    LABEL_SIZE,
    MIDDLING,
    MUTED,
    NOTE_SIZE,
    TITLE_SIZE,
    WARN,
    bare,
    base_width,
    glass_from_the_side,
    new,
    save,
)
from make_solution_flows_a import audit
from matplotlib.patches import Circle, Rectangle

# ------------------------------------------------------------------ the numbers

# bench/bench.py
WAYPOINT_MS = 50.0        # WAYPOINT_PERIOD = 0.05 s
PUSH_HEIGHT_MM = 50.0     # PUSH_HEIGHT = LOWEST_GRIP = 0.050
TRAVEL_HEIGHT_MM = 300.0  # TRAVEL_HEIGHT = 0.30
FEEL_SPEED_MM_S = 10.0    # FEEL_SPEED = 0.01 m/s
PUSH_SPEED_MM_S = 20.0    # PUSH_SPEED = 0.02 m/s
FINGER_LENGTH_MM = 120.0  # FINGER_LENGTH = 0.12
FINGER_HEIGHT_MM = 30.0   # FINGER_HEIGHT = 0.03
APPROACH_GAP_MM = 10.0    # 01-one-fixed-nudge/plan.py APPROACH_GAP = 0.010

# 06-smolvla-fine-tuned/chunks.py CHUNK, which is SmolVLA's own chunk_size.
CHUNK = 50

# 06-smolvla-fine-tuned/demonstrations-check/collected.json: the teacher's own
# pushes, cut and resampled, over the 50 tuning tables.
TEACHER_ACROSS_MM = 89.1
TEACHER_STEP_MM = 1.8

# 06-smolvla-fine-tuned/asking.json, over the 3 evaluation runs of the
# held-out tables.
FITTED_ACROSS_MM = 315.2
FITTED_STEP_MM = 4.5
FITTED_LOWEST_MM = 50.0

# 05-smolvla-as-it-downloads/asking.json, the same three figures untrained.
BORROWED_ACROSS_MM = 844.2
BORROWED_STEP_MM = 14.3
BORROWED_LOWEST_MM = 209.1

# 06-smolvla-fine-tuned/correction/training.json "history": how far the model's
# waypoints land from the teacher's on tuning tables nothing was fitted on.
# Step 0 is the correction at zero, which is solution 5 exactly.
UNTRAINED_MM = 320.7
UNTRAINED_WORST_MM = 658.4
HALF_TRAINED_MM = 84.3
TRAINED_MM = 90.0

# 06-smolvla-fine-tuned/results.json "each": pushes that were stopped by a
# glass while the jaw was still coming down, against every push that run made.
BLOCKED_PER_RUN = ((247, 400), (259, 386), (275, 461))

# The glass zone, from rack/layout.py by way of diagram_style.
ZONE_WIDE_MM = GLASS_ZONE[1] - GLASS_ZONE[0]
ZONE_DEEP_MM = GLASS_ZONE[3] - GLASS_ZONE[2]


# ------------------------------------------------------- what the pictures claim
#
# Each of these is the arithmetic behind a sentence drawn into a picture. They
# are computed rather than written down, and asserted, so that a figure can
# never say something the measurements stopped supporting.

# "a waypoint period apart, so the spacing is the speed"
PERIOD_S = WAYPOINT_MS / 1000.0
TEACHER_PUSH_STEP_MM = PUSH_SPEED_MM_S * PERIOD_S     # 1.0 mm, the teacher's fastest
TEACHER_FEEL_STEP_MM = FEEL_SPEED_MM_S * PERIOD_S     # 0.5 mm, while it feels forward
DEMO_STEP_MM = TEACHER_ACROSS_MM / (CHUNK - 1)        # the resampled spacing
DEMO_SPEED_MM_S = DEMO_STEP_MM / PERIOD_S
FITTED_SPEED_MM_S = FITTED_STEP_MM / PERIOD_S
CHUNK_SECONDS = (CHUNK - 1) * PERIOD_S

# The resampling is the only thing that changes the speed, so the spacing a
# demonstration ends up with has to be the one the collected set reports.
assert round(DEMO_STEP_MM, 1) == TEACHER_STEP_MM, (DEMO_STEP_MM, TEACHER_STEP_MM)
assert round(DEMO_SPEED_MM_S) == 36, DEMO_SPEED_MM_S
assert round(FITTED_SPEED_MM_S) == 90, FITTED_SPEED_MM_S
assert DEMO_STEP_MM > TEACHER_PUSH_STEP_MM > TEACHER_FEEL_STEP_MM

# The examiner holds a commanded path to the jaw's top speed. That cap never
# binds on a demonstration and does bind on the borrowed model's own chunks,
# which is why only the first two rows above are speeds the jaw really reaches.
TOP_SPEED_MM_S = 200.0                                # bench/bench.py TOP_SPEED = 0.20 m/s
assert DEMO_SPEED_MM_S < FITTED_SPEED_MM_S < TOP_SPEED_MM_S
assert BORROWED_STEP_MM / PERIOD_S > TOP_SPEED_MM_S, BORROWED_STEP_MM

# "still three times too far"
TOO_LONG_BY = FITTED_ACROSS_MM / TEACHER_ACROSS_MM
assert 3.0 <= TOO_LONG_BY <= 4.0, TOO_LONG_BY

# "the borrowed model is clear of every glass but the tallest"
assert MIDDLING[0] < BORROWED_LOWEST_MM < KIND_TALLEST, BORROWED_LOWEST_MM
# "and the fine-tuned one comes down to exactly the height the jaw pushes at"
assert FITTED_LOWEST_MM == PUSH_HEIGHT_MM

# "the untrained answer is a zone's width away"
assert UNTRAINED_MM > ZONE_WIDE_MM, (UNTRAINED_MM, ZONE_WIDE_MM)
assert HALF_TRAINED_MM < UNTRAINED_MM / 3.0

# "about three of its pushes in five are blocked on the way down" — the share
# is taken per run and the middle one reported, because a median blocked count
# over one set of runs and a median total over another do not divide.
BLOCKED_SHARES = sorted(blocked / total for blocked, total in BLOCKED_PER_RUN)
BLOCKED_SHARE = BLOCKED_SHARES[1]
assert 0.55 <= BLOCKED_SHARE <= 0.68, BLOCKED_SHARES
# Which is why the picture says three in five and not two thirds.
assert abs(BLOCKED_SHARE - 0.6) < abs(BLOCKED_SHARE - 2 / 3), BLOCKED_SHARE


# --------------------------------------------------------------------------- #
# 1. how it works: how far the untrained answer was from the teacher's
# --------------------------------------------------------------------------- #


def how_far_the_answer_was() -> None:
    """The glass zone, a teacher's push on it, and the gap drawn round the push.

    The page says the untrained model's waypoints land a median of 321 mm from
    the teacher's and that the glass zone is 320 mm by 360 mm. Those two
    numbers beside each other in prose are a coincidence of digits. Drawn to
    one scale they are the finding: the borrowed model's answer is not a push
    at the wrong glass, it is a motion somewhere else on the table.
    """
    figure, axis = new(7.6, 7.0)
    bare(axis)
    axis.set_aspect("equal")

    # The zone, drawn where it stands, and a demonstration-length push in the
    # middle of it so that the rings have something real to be measured from.
    x0, x1, y0, y1 = GLASS_ZONE
    axis.add_patch(Rectangle((x0, y0), ZONE_WIDE_MM, ZONE_DEEP_MM, facecolor="none",
                             edgecolor=INK, lw=1.4, zorder=4))
    axis.text(x0 + ZONE_WIDE_MM / 2.0, y1 + 14, "the glass zone, "
              f"{ZONE_WIDE_MM:.0f} mm by {ZONE_DEEP_MM:.0f} mm",
              fontsize=LABEL_SIZE, color=INK, ha="center", va="bottom", zorder=6)

    middle = np.array([(x0 + x1) / 2.0, (y0 + y1) / 2.0])
    start = middle - np.array([TEACHER_ACROSS_MM / 2.0, 0.0])
    end = middle + np.array([TEACHER_ACROSS_MM / 2.0, 0.0])
    axis.annotate("", xy=tuple(end), xytext=tuple(start), zorder=7,
                  arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=2.4, shrinkA=0, shrinkB=0))
    axis.text(middle[0], middle[1] - HALF_TRAINED_MM - 26,
              f"one of the teacher's pushes, {TEACHER_ACROSS_MM:.0f} mm long",
              fontsize=LABEL_SIZE, color=GOOD, ha="center", va="top", zorder=7)

    for radius, colour, label in (
        (UNTRAINED_MM, WARN,
         f"before any training: a median of {UNTRAINED_MM:.0f} mm away,\n"
         f"and {UNTRAINED_WORST_MM:.0f} mm at the worst"),
        (HALF_TRAINED_MM, GLASS,
         f"after five hundred steps:\n{HALF_TRAINED_MM:.0f} mm"),
    ):
        axis.add_patch(Circle(tuple(middle), radius, facecolor="none", edgecolor=colour,
                              lw=1.6, ls=(0, (5, 4)), zorder=5))
        axis.text(middle[0], middle[1] + radius + 10, label, fontsize=LABEL_SIZE,
                  color=colour, ha="center", va="bottom", zorder=6)

    axis.set_xlim(middle[0] - UNTRAINED_MM - 40, middle[0] + UNTRAINED_MM + 40)
    axis.set_ylim(middle[1] - UNTRAINED_MM - 110, middle[1] + UNTRAINED_MM + 120)
    axis.set_title("How far the model's waypoints landed from the teacher's",
                   fontsize=TITLE_SIZE, color=INK, pad=10)
    axis.text(middle[0], middle[1] - UNTRAINED_MM - 70,
              "Measured on tuning tables nothing was fitted on. The ring before training "
              "is wider than the zone the glasses stand in.",
              fontsize=NOTE_SIZE, color=MUTED, ha="center", va="top", zorder=6)

    print(f"  untrained {UNTRAINED_MM:.0f} mm against a zone {ZONE_WIDE_MM:.0f} mm across")
    audit(figure, axis, "finetuned-how-far-the-answer-was.png")
    save(figure, "finetuned-how-far-the-answer-was.png")


# --------------------------------------------------------------------------- #
# 2. how it works: the height was learned and the length was not
# --------------------------------------------------------------------------- #


def the_height_not_the_length() -> None:
    """Three chunks over the same table, drawn to one scale, side on.

    The page makes two measurements about the same answer and they point
    opposite ways, which is exactly the case where a sentence each is harder
    to hold than one picture. Height and length are the two axes of this
    drawing, so both claims are read off the same two lines.
    """
    figure, axis = new(13.2, 4.7)
    bare(axis)
    axis.set_aspect("equal")

    height, rim, fraction = MIDDLING
    right = BORROWED_ACROSS_MM + 60
    axis.plot([-40, right], [0, 0], color=INK, lw=1.4, zorder=2)
    # Two glasses, drawn clear of the labels, so that the three heights have
    # something of a known size to be read against: the borrowed chunk passes
    # over the rims and the other two run along the feet.
    for where in (690.0, 810.0):
        glass_from_the_side(axis, where, height, rim, fraction, colour=GLASS, zorder=3)

    # The dashed line both fitted chunks sit on, labelled past the end of
    # everything else so that nothing shares a patch of paper with it.
    axis.plot([-40, right], [PUSH_HEIGHT_MM, PUSH_HEIGHT_MM], color=MUTED, lw=0.9,
              ls=(0, (4, 4)), zorder=1)
    axis.text(right + 12, PUSH_HEIGHT_MM, "the height the jaw pushes at",
              fontsize=NOTE_SIZE, color=MUTED, ha="left", va="center", zorder=6)

    for across, draw_at, colour, label, va, gap in (
        (BORROWED_ACROSS_MM, BORROWED_LOWEST_MM, WARN,
         f"as it downloads\n{BORROWED_ACROSS_MM:.0f} mm across, {BORROWED_LOWEST_MM:.0f} mm up",
         "bottom", 10.0),
        (FITTED_ACROSS_MM, PUSH_HEIGHT_MM + 6.0, GLASS,
         f"fine-tuned here\n{FITTED_ACROSS_MM:.0f} mm across, {FITTED_LOWEST_MM:.0f} mm up",
         "bottom", 14.0),
        (TEACHER_ACROSS_MM, PUSH_HEIGHT_MM - 6.0, GOOD,
         f"the teacher, {TEACHER_ACROSS_MM:.0f} mm across", "top", -12.0),
    ):
        axis.annotate("", xy=(across, draw_at), xytext=(0.0, draw_at), zorder=7,
                      arrowprops=dict(arrowstyle="-|>", color=colour, lw=2.2,
                                      shrinkA=0, shrinkB=0))
        axis.text(across + 14, draw_at + gap, label, fontsize=LABEL_SIZE, color=colour,
                  ha="left", va=va, zorder=8)

    axis.set_xlim(-60, right + 340)
    axis.set_ylim(-120, 300)
    axis.set_title("The training taught it the height of a push and not the length of one",
                   fontsize=TITLE_SIZE, color=INK, pad=8)
    axis.text(-50, -66,
              f"Drawn to one scale, the table seen from the side. The fine-tuned chunk is "
              f"{TOO_LONG_BY:.1f} times the teacher's, and on a crowded table a push that "
              "long is a push into a neighbour.",
              fontsize=NOTE_SIZE, color=MUTED, ha="left", va="top", zorder=6)

    print(f"  fine-tuned chunk {TOO_LONG_BY:.1f} times the teacher's")
    audit(figure, axis, "finetuned-the-height-not-the-length.png")
    save(figure, "finetuned-the-height-not-the-length.png")


# --------------------------------------------------------------------------- #
# 3. the code: the same push in fewer waypoints
# --------------------------------------------------------------------------- #


def the_same_push_in_fewer_waypoints() -> None:
    """One recorded push and its resampling, over the same ground.

    ``resampled`` does not move the jaw anywhere new. What it changes is how
    many waypoints the path is made of, and since the examiner eats waypoints a
    fixed period apart, that is the speed. The two rows are the same distance
    long on purpose: only the dots differ.
    """
    figure, axis = new(11.8, 3.3)
    bare(axis)

    teacher = np.arange(0.0, TEACHER_ACROSS_MM + 1e-9, TEACHER_PUSH_STEP_MM)
    student = np.linspace(0.0, TEACHER_ACROSS_MM, CHUNK)

    for y, points, colour, title_line, seconds in (
        (0.55, teacher, GOOD,
         f"as the teacher pushed it: no waypoint more than {TEACHER_PUSH_STEP_MM:.1f} mm "
         f"from the last, because it pushes at {PUSH_SPEED_MM_S:.0f} mm/s",
         (len(teacher) - 1) * PERIOD_S),
        (-0.55, student, GLASS,
         f"as the model is trained to emit it: {CHUNK} waypoints, "
         f"{DEMO_STEP_MM:.1f} mm apart",
         CHUNK_SECONDS),
    ):
        axis.plot([0, TEACHER_ACROSS_MM], [y, y], color=MUTED, lw=1.0, zorder=1)
        axis.scatter(points, np.full_like(points, y), s=20, color=colour, zorder=4)
        axis.text(0, y + 0.17, title_line, fontsize=LABEL_SIZE, color=colour,
                  ha="left", va="bottom", zorder=6)
        axis.text(TEACHER_ACROSS_MM + 3, y,
                  f"{len(points)} waypoints\n{seconds:.1f} s\n"
                  f"{TEACHER_ACROSS_MM / seconds:.0f} mm/s",
                  fontsize=LABEL_SIZE, color=colour, ha="left", va="center", zorder=6)

    axis.annotate("", xy=(TEACHER_ACROSS_MM, 0.0), xytext=(0.0, 0.0), zorder=5,
                  arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.0,
                                  shrinkA=0, shrinkB=0))
    axis.text(TEACHER_ACROSS_MM / 2.0, 0.06,
              f"the same {TEACHER_ACROSS_MM:.0f} mm of table",
              fontsize=LABEL_SIZE, color=INK, ha="center", va="bottom", zorder=6)

    axis.set_xlim(-4, TEACHER_ACROSS_MM + 34)
    axis.set_ylim(-1.35, 1.15)
    axis.set_title("The same push, resampled to the fifty waypoints the model emits",
                   fontsize=TITLE_SIZE, color=INK, pad=10)
    axis.text(0, -1.05,
              f"A waypoint is consumed every {WAYPOINT_MS:.0f} ms either way, so squeezing "
              "the path into fewer of them is the one place the borrowed model's shape "
              "reaches into the physics.",
              fontsize=NOTE_SIZE, color=MUTED, ha="left", va="top", zorder=6)

    print(f"  {len(teacher)} waypoints at {TEACHER_PUSH_STEP_MM:.1f} mm "
          f"against {CHUNK} at {DEMO_STEP_MM:.1f} mm")
    audit(figure, axis, "finetuned-the-same-push-in-fewer-waypoints.png")
    save(figure, "finetuned-the-same-push-in-fewer-waypoints.png")


# --------------------------------------------------------------------------- #
# 4. a worked example: where the jaw comes down
# --------------------------------------------------------------------------- #


def where_the_jaw_comes_down() -> None:
    """The descent to a chunk's first waypoint, from two places, side on.

    ``follow()`` puts the jaw above the chunk's first waypoint and lowers it.
    Everything that goes wrong for this solution goes wrong in that one move,
    and it is a move the prose can only describe. The two jaws are the same
    jaw, drawn at the two heights its descent ends at.
    """
    figure, axis = new(10.4, 5.4)
    bare(axis)
    axis.set_aspect("equal")

    height, rim, fraction = MIDDLING
    half_rim, half_foot = rim / 2.0, base_width(rim, fraction) / 2.0
    axis.plot([-330, 220], [0, 0], color=INK, lw=1.4, zorder=2)
    glass_from_the_side(axis, 0.0, height, rim, fraction, colour=GLASS, zorder=3)

    # The jaw seen side on: the finger block, pointing the way it pushes. The
    # fingertip is at the leading edge, so the block runs back from it.
    def jaw(tip_x: float, centre_z: float, colour: str) -> None:
        axis.add_patch(Rectangle((tip_x - FINGER_LENGTH_MM, centre_z - FINGER_HEIGHT_MM / 2.0),
                                 FINGER_LENGTH_MM, FINGER_HEIGHT_MM,
                                 facecolor="white", edgecolor=colour, lw=1.6, zorder=6))

    # Behind the glass: the fingertip stands APPROACH_GAP clear of the rim, so
    # nothing of the jaw is over the glass and the descent reaches push height.
    good_tip = -(half_rim + APPROACH_GAP_MM)
    assert good_tip + 1e-9 <= -half_rim, good_tip
    jaw(good_tip, PUSH_HEIGHT_MM, GOOD)
    down_x = good_tip - FINGER_LENGTH_MM + 12
    axis.annotate("", xy=(down_x, PUSH_HEIGHT_MM + 26),
                  xytext=(down_x, TRAVEL_HEIGHT_MM - 14), zorder=5,
                  arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.6, shrinkA=0, shrinkB=0))
    axis.annotate("", xy=(good_tip - 6, PUSH_HEIGHT_MM + 34),
                  xytext=(down_x + 24, PUSH_HEIGHT_MM + 34), zorder=7,
                  arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=2.0, shrinkA=0, shrinkB=0))
    axis.text(down_x, TRAVEL_HEIGHT_MM + 16,
              f"first waypoint behind the glass:\nthe jaw reaches {PUSH_HEIGHT_MM:.0f} mm "
              "and pushes",
              fontsize=LABEL_SIZE, color=GOOD, ha="center", va="bottom", zorder=7)

    # Over the glass: the block meets the rim on the way down and stops there.
    bad_tip = half_rim
    assert bad_tip - FINGER_LENGTH_MM < -half_rim, bad_tip
    blocked_z = height + FINGER_HEIGHT_MM / 2.0
    jaw(bad_tip, blocked_z, WARN)
    axis.annotate("", xy=(bad_tip - FINGER_LENGTH_MM / 2.0, blocked_z + 26),
                  xytext=(bad_tip - FINGER_LENGTH_MM / 2.0, TRAVEL_HEIGHT_MM - 14), zorder=5,
                  arrowprops=dict(arrowstyle="-|>", color=WARN, lw=1.6, shrinkA=0, shrinkB=0))
    axis.plot([-half_rim, half_rim], [height, height], color=WARN, lw=3.0,
              solid_capstyle="butt", zorder=7)
    axis.text(bad_tip + 26, blocked_z,
              "first waypoint over the glass:\nthe jaw meets the rim and goes\n"
              "straight back up, pushing nothing",
              fontsize=LABEL_SIZE, color=WARN, ha="left", va="center", zorder=7)

    axis.plot([-330, 560], [TRAVEL_HEIGHT_MM, TRAVEL_HEIGHT_MM], color=MUTED, lw=0.9,
              ls=(0, (4, 4)), zorder=1)
    axis.text(560, TRAVEL_HEIGHT_MM - 8,
              f"travel height, {TRAVEL_HEIGHT_MM:.0f} mm: the jaw is placed here,\n"
              "above the chunk's first waypoint, and lowered",
              fontsize=NOTE_SIZE, color=MUTED, ha="right", va="top", zorder=6)
    axis.text(0, -14, f"foot {2 * half_foot:.0f} mm, rim {rim:.0f} mm",
              fontsize=NOTE_SIZE, color=MUTED, ha="center", va="top", zorder=6)

    axis.set_xlim(-370, 580)
    axis.set_ylim(-110, 420)
    axis.set_title("The chunk's first waypoint decides whether there is a push at all",
                   fontsize=TITLE_SIZE, color=INK, pad=8)
    runs = ", ".join(f"{blocked} of {total}" for blocked, total in BLOCKED_PER_RUN)
    axis.text(-356, -54,
              f"About {BLOCKED_SHARE:.0%} of this solution's pushes end the second way: "
              f"{runs} over the three evaluation runs.",
              fontsize=NOTE_SIZE, color=MUTED, ha="left", va="top", zorder=6)

    print(f"  blocked share {BLOCKED_SHARE:.0%} of {BLOCKED_PER_RUN}")
    audit(figure, axis, "finetuned-where-the-jaw-comes-down.png")
    save(figure, "finetuned-where-the-jaw-comes-down.png")


def main() -> None:
    how_far_the_answer_was()
    the_height_not_the_length()
    the_same_push_in_fewer_waypoints()
    where_the_jaw_comes_down()


if __name__ == "__main__":
    main()
