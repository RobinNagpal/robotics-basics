"""The two pictures for the chapter on the borrowed model, used as it downloads.

The chapter already carries the flow chart of what the solution does, drawn by
``make_solution_flows_b.py``, and the height ladder that says how far above the
table its answers stop, drawn by ``make_six_solutions_pages.py``. Neither is
redrawn here. These are the two shapes the chapter's own pages argue about and
cannot draw in words.

    smolvla-the-parked-jaw.png        the box the reading can describe, seen
                                      from above, and the spot outside it where
                                      the examiner parks the jaw, which is why
                                      the pose the model is handed is the same
                                      on every ask.
    smolvla-the-spacing-is-the-speed.png  the examiner eats a waypoint every
                                      fixed period, so the spacing of a run of
                                      waypoints is the speed it asks for.

Every number drawn below is read out of ``code/src/09_pushing-the-glasses-apart/``
and the file it came from is named in a comment beside it. The three claims the
pictures make that are arithmetic rather than readings — how wide the frame is,
where the parked jaw clips to, and how the model's waypoint spacing compares
with the cell's two speeds — are computed here from the cell's own constants
and asserted, so a run stops rather than drawing something untrue.

The drawing helpers, and the audit that measures the finished picture for
overlapping text and lines through boxes, come from ``make_solution_flows_a.py``
so that these pictures sit beside the rest of the chapter's.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_borrowed_vla_pages.py
"""

from __future__ import annotations

from diagram_style import (
    GLASS,
    GOOD,
    GRIP_ROOM,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    WARN,
    save,
)
from make_solution_flows_a import _tint, finish, note, run, sheet, title
from matplotlib.patches import Circle, Rectangle

# ------------------------------------------------------------------ the numbers
#
# All of these are read out of code/src/09_pushing-the-glasses-apart/, and the
# constant that holds each one is named so that a reader can check it in one
# step. Lengths are millimetres and speeds are millimetres a second.

# bench/bench.py
GLASS_ZONE = (320.0, 640.0, -440.0, -80.0)   # rack/layout.py GLASS_ZONE, in mm
TOP_VIEW_HEIGHT_MM = 750.0                   # TOP_VIEW_HEIGHT = 0.75
TRAVEL_HEIGHT_MM = 300.0                     # TRAVEL_HEIGHT = 0.30
PUSH_HEIGHT_MM = 50.0                        # PUSH_HEIGHT = LOWEST_GRIP
TABLE_TOP_MM = 750.0                         # table/layout.py TABLE_TOP_Z = 0.75
WAYPOINT_PERIOD_S = 0.05                     # WAYPOINT_PERIOD
TOP_SPEED_MMS = 200.0                        # TOP_SPEED = DESCEND_SPEED = 0.20
PUSH_SPEED_MMS = 20.0                        # PUSH_SPEED = 0.02

# bench/bench.py _lift(): between actions the jaw is parked here, in world
# coordinates. The height below the table top is what jaw_now() reports.
PARK_WORLD = (0.0, 500.0, 1300.0)            # mocap_pos[0] = [0.0, 0.5, 1.3]

# 05-smolvla-as-it-downloads/joining.py
ACTION_SPAN = 2.0                            # ACTION_SPAN
CHUNK = 50                                   # the actions in one answer

# 05-smolvla-as-it-downloads/asking.json, over all three evaluation runs.
ASKED = 2260                                 # "asked"
STEP_MM = 14.3                               # "step_mm_median"
LOWEST_MM = 209.1                            # "lowest_mm_median"

# 05-smolvla-as-it-downloads/results.json, "each"[2]: the run whose push count
# is the median of the three. The parts of one run add up and medians taken
# column by column do not.
PUSHES = 754
NEVER_TOUCHED = 674
JAMMED = 69


# ------------------------------------------------------------------- the arithmetic
#
# bench/bench.py computes the half frame this way, and the pictures below draw
# it, so it is recomputed here rather than copied.

ZONE_REACH_MM = max(
    (GLASS_ZONE[1] - GLASS_ZONE[0]) / 2.0,
    (GLASS_ZONE[3] - GLASS_ZONE[2]) / 2.0,
)
HALF_FRAME_MM = (
    (ZONE_REACH_MM + GRIP_ROOM / 2.0)
    * TOP_VIEW_HEIGHT_MM
    / (TOP_VIEW_HEIGHT_MM - TRAVEL_HEIGHT_MM)
)
VIEW_CENTRE_MM = (
    (GLASS_ZONE[0] + GLASS_ZONE[1]) / 2.0,
    (GLASS_ZONE[2] + GLASS_ZONE[3]) / 2.0,
)
FRAME = (
    VIEW_CENTRE_MM[0] - HALF_FRAME_MM,
    VIEW_CENTRE_MM[0] + HALF_FRAME_MM,
    VIEW_CENTRE_MM[1] - HALF_FRAME_MM,
    VIEW_CENTRE_MM[1] + HALF_FRAME_MM,
)
PARK_MM = (PARK_WORLD[0], PARK_WORLD[1], PARK_WORLD[2] - TABLE_TOP_MM)
CLIPPED_MM = (
    min(max(PARK_MM[0], FRAME[0]), FRAME[1]),
    min(max(PARK_MM[1], FRAME[2]), FRAME[3]),
    min(max(PARK_MM[2], PUSH_HEIGHT_MM), TRAVEL_HEIGHT_MM),
)

# How far the jaw is asked to travel in one waypoint period, at each of the
# cell's two speeds and at the spacing the model's own answers come back with.
PUSH_STEP_MM = PUSH_SPEED_MMS * WAYPOINT_PERIOD_S
TOP_STEP_MM = TOP_SPEED_MMS * WAYPOINT_PERIOD_S
MODEL_SPEED_MMS = STEP_MM / WAYPOINT_PERIOD_S


def _check() -> None:
    """Everything the two pictures claim, checked before either is drawn."""
    assert round(HALF_FRAME_MM, 1) == 358.3, HALF_FRAME_MM
    assert VIEW_CENTRE_MM == (480.0, -260.0), VIEW_CENTRE_MM
    # Picture 1's whole claim: the parked jaw is outside the box on all three
    # axes, so all three numbers the model is handed clip to an edge.
    assert not FRAME[0] <= PARK_MM[0] <= FRAME[1], PARK_MM
    assert not FRAME[2] <= PARK_MM[1] <= FRAME[3], PARK_MM
    assert PARK_MM[2] > TRAVEL_HEIGHT_MM, PARK_MM
    assert CLIPPED_MM == (FRAME[0], FRAME[3], TRAVEL_HEIGHT_MM), CLIPPED_MM
    # Picture 2's whole claim: the model's spacing asks for more than the arm
    # has, and many times what a push is made at.
    assert PUSH_STEP_MM == 1.0, PUSH_STEP_MM
    assert TOP_STEP_MM == 10.0, TOP_STEP_MM
    assert STEP_MM > TOP_STEP_MM, (STEP_MM, TOP_STEP_MM)
    assert round(STEP_MM / PUSH_STEP_MM, 1) == 14.3
    print(
        f"  the frame is {2 * HALF_FRAME_MM:.0f} mm across, centred on {VIEW_CENTRE_MM};\n"
        f"  the jaw parks at {PARK_MM} and clips to {tuple(round(v, 1) for v in CLIPPED_MM)};\n"
        f"  one waypoint period is {PUSH_STEP_MM:.0f} mm at push speed, {TOP_STEP_MM:.0f} mm at the arm's top\n"
        f"  speed, and {STEP_MM} mm in the model's own answers, which is {MODEL_SPEED_MMS:.0f} mm/s."
    )


# --------------------------------------------------------------------------- #
# 1. the box the reading can describe, and the spot outside it
# --------------------------------------------------------------------------- #


def the_parked_jaw() -> None:
    """Where the jaw stands when the model is asked, against what the reading can say.

    One idea: the pose handed to the model is pinned at a corner it could not
    actually be at, so it is the same number on every ask on every table.
    """
    width, height = 12.2, 7.4
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "The jaw is parked outside everything the model's pose input can describe") - 0.30

    # Millimetres to inches, with the plan drawn down the left of the sheet.
    # The window has to hold both the frame and the spot the jaw parks at,
    # which is the whole point of the picture.
    low_x, high_x = min(PARK_MM[0], FRAME[0]) - 70.0, FRAME[1] + 70.0
    low_y, high_y = FRAME[2] - 110.0, PARK_MM[1] + 110.0
    plan_left, plan_bottom, plan_top = 0.70, 0.78, y - 0.14
    scale = (plan_top - plan_bottom) / (high_y - low_y)

    def at(x_mm: float, y_mm: float) -> tuple[float, float]:
        return plan_left + (x_mm - low_x) * scale, plan_bottom + (y_mm - low_y) * scale

    # The frame of the straight-down picture: the one thing in this solution
    # with a metric extent that the model can see.
    corner = at(FRAME[0], FRAME[2])
    axis.add_patch(Rectangle(corner, 2 * HALF_FRAME_MM * scale, 2 * HALF_FRAME_MM * scale,
                             facecolor=_tint(GLASS, 0.90), edgecolor=GLASS, lw=1.3, zorder=2))
    # The glass zone, which is what the frame was sized to hold.
    zone = at(GLASS_ZONE[0], GLASS_ZONE[2])
    axis.add_patch(Rectangle(zone, (GLASS_ZONE[1] - GLASS_ZONE[0]) * scale,
                             (GLASS_ZONE[3] - GLASS_ZONE[2]) * scale,
                             facecolor=_tint(MUTED, 0.80), edgecolor=MUTED, lw=1.1,
                             ls=(0, (4, 3)), zorder=3))
    note(axis, *at(*VIEW_CENTRE_MM), "the glass\nzone", colour=INK,
         size=NOTE_SIZE - 0.8, ha="center", figure=figure)

    # Where the examiner parks the jaw between actions, and where that clips to.
    park, clip = at(PARK_MM[0], PARK_MM[1]), at(CLIPPED_MM[0], CLIPPED_MM[1])
    axis.add_patch(Circle(park, 0.085, facecolor=WARN, edgecolor=WARN, zorder=6))
    axis.add_patch(Circle(clip, 0.075, facecolor="white", edgecolor=WARN, lw=1.6, zorder=6))
    run(axis, park, clip, colour=WARN, lw=1.3)

    note(axis, park[0] + 0.16, park[1],
         f"the jaw, parked, and {PARK_MM[2]:.0f} mm up", colour=WARN,
         size=NOTE_SIZE - 0.6, figure=figure)
    note(axis, clip[0] + 0.16, clip[1] + 0.24,
         f"what the model is told, and {CLIPPED_MM[2]:.0f} mm up", colour=WARN,
         size=NOTE_SIZE - 0.6, figure=figure)

    # The frame's own width, marked along its bottom edge.
    base = at(FRAME[0], FRAME[2])[1] - 0.20
    run(axis, (at(FRAME[0], 0)[0], base), (at(FRAME[1], 0)[0], base), colour=GLASS, lw=1.1)
    note(axis, *at(VIEW_CENTRE_MM[0], FRAME[2] - 90.0), f"{2 * HALF_FRAME_MM:.0f} mm",
         colour=GLASS, size=NOTE_SIZE - 0.6, ha="center", figure=figure)
    note(axis, at(low_x, 0)[0], plan_bottom - 0.16,
         "the table seen from above, in the cell's own x and y, millimetres from the arm's base",
         colour=MUTED, size=NOTE_SIZE - 1.0, figure=figure)

    # The text column, down the right of the plan.
    text_x = plan_left + (high_x - low_x) * scale + 0.45
    yy = plan_top - 0.10
    for gap_after, colour, lines in (
        (1.55, GLASS,
         "The box the reading can describe\n"
         f"Two standard deviations of the model's output span the picture's frame, so a\n"
         f"waypoint can land anywhere in these {2 * HALF_FRAME_MM:.0f} mm and nowhere outside them. Heights run\n"
         f"from {PUSH_HEIGHT_MM:.0f} mm, where the jaw must ride to move a glass, to {TRAVEL_HEIGHT_MM:.0f} mm, where it travels."),
        (1.70, WARN,
         "Where the jaw actually is when the model is asked\n"
         f"The examiner parks it at x {PARK_MM[0]:.0f}, y {PARK_MM[1]:.0f}, {PARK_MM[2]:.0f} mm up, and lifts it back there after\n"
         "every answer. That is outside the box on all three axes, so all three clip to an\n"
         "edge and the model is told the same thing at every ask on every table."),
    ):
        yy = note(axis, text_x, yy, lines, colour=colour, size=NOTE_SIZE, figure=figure) - gap_after

    bottom = note(
        axis, text_x, yy - 0.06,
        "Only the fourth number, the jaw's heading, carries anything, and it carries where the\n"
        "last answer happened to end. So the pose input is as constant here as the instruction is.\n"
        "It matters because this model emits absolute targets and stays near the pose it is given:\n"
        f"told the jaw is as high as it goes, it answers high, and its answers stop {LOWEST_MM:.0f} mm up.",
        colour=INK, size=NOTE_SIZE, figure=figure,
    )

    finish(figure, axis, "smolvla-the-parked-jaw.png", min(bottom, plan_bottom - 0.45))
    save(figure, "smolvla-the-parked-jaw.png")


# --------------------------------------------------------------------------- #
# 2. the spacing of a run of waypoints is the speed it asks for
# --------------------------------------------------------------------------- #


def the_spacing_is_the_speed() -> None:
    """Three runs of waypoints at the same period, drawn to the same scale.

    One idea: the examiner eats one waypoint every fixed period, so a run of
    waypoints has no separate speed to set — how far apart they are is it.
    """
    width, height = 11.6, 4.85
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "One waypoint every 50 milliseconds, so how far apart they are is how fast the jaw goes") - 0.46

    steps = 10                      # waypoints drawn in each row, so half a second
    left, right = 4.30, 11.20
    scale = (right - left) / (steps * STEP_MM)
    rows = (
        (PUSH_STEP_MM, GOOD,
         f"the examiner's push macro\n{PUSH_STEP_MM:g} mm apart, {PUSH_SPEED_MMS:.0f} mm a second"),
        (TOP_STEP_MM, INK,
         f"the fastest the arm moves\n{TOP_STEP_MM:g} mm apart, {TOP_SPEED_MMS:.0f} mm a second"),
        (STEP_MM, WARN,
         f"what the model's answers ask for\n{STEP_MM:g} mm apart, {MODEL_SPEED_MMS:.0f} mm a second"),
    )

    gap, dot = 0.92, 0.070
    for index, (step, colour, name) in enumerate(rows):
        line = y - 0.34 - index * gap
        axis.plot([left, left + steps * step * scale], [line, line],
                  color=colour, lw=1.1, zorder=4)
        for k in range(steps + 1):
            axis.add_patch(Circle((left + k * step * scale, line), dot,
                                  facecolor=colour, edgecolor=colour, zorder=5))
        note(axis, left - 0.26, line, name, colour=colour, size=NOTE_SIZE,
             ha="right", figure=figure)

    # The arm's own ceiling, which the examiner holds every commanded path to.
    ceiling_x = left + steps * TOP_STEP_MM * scale
    top_line, low_line = y - 0.34 + 0.36, y - 0.34 - 2 * gap - 0.36
    run(axis, (ceiling_x, top_line), (ceiling_x, low_line), colour=INK, lw=1.0)
    note(axis, ceiling_x - 0.10, low_line - 0.17,
         "as far as the arm can travel in half a second; the examiner holds every\n"
         "commanded path to this, so the rest of the model's answer is simply late",
         colour=INK, size=NOTE_SIZE - 0.6, ha="right", figure=figure)

    bottom = note(
        axis, 0.55, low_line - 0.72,
        f"The reading that turns the model's output into millimetres fixes one box, and fixing the box fixes the speed as well as the reach:\n"
        f"the two cannot be chosen separately. Measured over {ASKED:,} answers, the waypoints come back {STEP_MM} mm apart, which is "
        f"{STEP_MM / PUSH_STEP_MM:.1f} times\n"
        f"the spacing a push is made at. That is why {JAMMED} of the {PUSHES - NEVER_TOUCHED} pushes that reached a glass jammed against it "
        "instead of sliding it along.",
        colour=INK, size=NOTE_SIZE, figure=figure,
    )

    finish(figure, axis, "smolvla-the-spacing-is-the-speed.png", bottom - 0.10)
    save(figure, "smolvla-the-spacing-is-the-speed.png")


def main() -> None:
    _check()
    the_parked_jaw()
    the_spacing_is_the_speed()


if __name__ == "__main__":
    main()
