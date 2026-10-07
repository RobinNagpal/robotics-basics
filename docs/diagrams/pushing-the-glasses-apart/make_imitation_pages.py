"""The pictures for the imitation-from-demonstrations pages past the first one.

The first page of that solution already had two flow charts, drawn by
``make_solution_flows_a.py``. The four pages after it had none, and four things
on them are shape rather than sentence. Those four are drawn here, two of them
twice over because the page makes two separate points about the same geometry.

    imitation-the-waypoint-spacing-is-the-speed.png   how it works, action chunking:
                                        one chunk is a fixed number of waypoints
                                        eaten at a fixed rate, so their spacing
                                        is the jaw's speed.
    imitation-the-average-of-two-good-pushes.png      how it works, the second rung:
                                        two demonstrations that disagree, and the
                                        chunk halfway between them, computed
                                        rather than asserted.
    imitation-what-a-demonstration-keeps.png          the code: a recorded path has
                                        five legs and ``push_segment`` keeps two.
    imitation-heading-as-cosine-and-sine.png          the code: the same two pushes
                                        as an angle, which wraps, and as a cosine
                                        and sine pair, which does not.
    imitation-where-a-refusal-comes-from.png          a worked example: every glass
                                        taken out of play is taken out in front of
                                        the policy, because a chunk of waypoints
                                        has no channel for a refusal.
    imitation-thirty-degrees-of-heading.png           a worked example: the measured
                                        failure. Same fingertip, thirty degrees of
                                        heading, and the jaw's own 270 mm tail is
                                        over a glass.

Three things were considered and left out, because a picture of a list is
padding. "What it needs" is a bill: libraries, a machine, data, a licence, and
every item on it is a sentence. "How it compares" is five named ideas and five
comparisons, which read as prose. And the offline-then-online shape of the
whole solution is already ``imitation-flow-what-it-does.png`` on the first page,
so drawing it again two pages later would be the same chart twice.

Every number drawn into these pictures is read out of ``code/src/`` and the
constant it came from is named beside it below. Three of the pictures also
check their own claim: the crowded pair is crowded by the bench's own
``has_room``, the averaged chunk really does stand still, and the jaw really
does clear the third glass at the teacher's heading and not at thirty degrees
off it. A picture that stopped being true would stop the run rather than be
written.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_imitation_pages.py
"""

from __future__ import annotations

import math

import numpy as np
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
    glass_from_above,
    new,
    save,
)
from make_solution_flows_a import GAP, _tint, arrow, box, elbow, finish, note, sheet, title
from matplotlib.patches import Circle, Polygon, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Read out of code/src/09_pushing-the-glasses-apart/, with the file and the
# constant named so that a reader can check each one in a single step.

CHUNK = 120              # 03-imitation-from-demonstrations/chunks.py CHUNK
ACTION_WIDTH = 5         # 03-imitation-from-demonstrations/chunks.py ACTION_WIDTH

WAYPOINT_MS = 50         # bench/bench.py WAYPOINT_PERIOD = 0.05 s
FEEL_SPEED = 10.0        # bench/bench.py FEEL_SPEED = 0.01 m/s, in mm/s
PUSH_SPEED = 20.0        # bench/bench.py PUSH_SPEED = 0.02 m/s, in mm/s
TOP_SPEED = 200.0        # bench/bench.py TOP_SPEED = DESCEND_SPEED = 0.20 m/s, in mm/s

# How far the jaw gets in one waypoint period at each of those speeds.
FEEL_STEP_MM = FEEL_SPEED * WAYPOINT_MS / 1000.0          # 0.5 mm
PUSH_STEP_MM = PUSH_SPEED * WAYPOINT_MS / 1000.0          # 1.0 mm
CAP_MM = TOP_SPEED * WAYPOINT_MS / 1000.0                 # 10 mm, the furthest a leg may be

PUSH_HEIGHT_MM = 50.0    # bench/bench.py PUSH_HEIGHT = LOWEST_GRIP = 0.050
TRAVEL_HEIGHT_MM = 300.0  # bench/bench.py TRAVEL_HEIGHT = 0.30
JAW_TOP_MM = 65.0        # bench/bench.py JAW_TOP = PUSH_HEIGHT + FINGER_HEIGHT / 2
RETREAT_MM = 20.0        # bench/bench.py RETREAT = 0.02

# The closed jaw in plan, as bench.py declares its three boxes. Everything is
# measured back from the fingertip, which is where the jaw's own frame sits.
FINGER_LENGTH_MM = 120.0  # bench/bench.py FINGER_LENGTH = 0.12
JAW_THICKNESS_MM = 28.0   # bench/bench.py JAW_THICKNESS = 2 * (0.010 + 0.004)
BODY_SIZE_MM = 90.0      # bench/bench.py BODY_SIZE = 0.09
BODY_LENGTH_MM = 50.0    # bench/bench.py BODY_LENGTH = 0.05
WRIST_LENGTH_MM = 100.0  # bench/bench.py WRIST_LENGTH = 0.10
TOOL_LENGTH_MM = FINGER_LENGTH_MM + BODY_LENGTH_MM + WRIST_LENGTH_MM   # 270 mm

GRIP_ROOM_MM = 70.0      # bench/bench.py GRIP_ROOM = 0.070
APPROACH_GAP_MM = 10.0   # 01-one-fixed-nudge/plan.py APPROACH_GAP = 0.010
AIM_MARGIN_MM = 10.0     # 01-one-fixed-nudge/plan.py AIM_MARGIN = 0.010
CLEARANCE_MM = 8.0       # 01-one-fixed-nudge/plan.py CLEARANCE = 0.008
STEP_MM = 2.0            # 01-one-fixed-nudge/plan.py STEP = 0.002
MU_LOWEST = 0.2          # 01-one-fixed-nudge/plan.py MU_LOWEST
MU_HIGHEST = 0.5         # 01-one-fixed-nudge/plan.py MU_HIGHEST
PROBE_MM = 5             # 01-one-fixed-nudge/plan.py PROBE = 0.005

PUSHES_PER_GLASS = 4     # bench/bench.py PUSHES_PER_GLASS
PUSHES_PER_TABLE = 16    # bench/bench.py PUSHES_PER_TABLE

# The two glass sizes used below, both inside the declared range in
# glasses/shapes.py as diagram_style records it: KIND_WIDEST 105 mm,
# KIND_NARROWEST 65 mm.
WIDE_RIM_MM = 100.0
NARROW_RIM_MM = 70.0

# The heading error the fitted policy actually shows, from
# 03-imitation-from-demonstrations/README.md: "its heading is around 30 degrees
# out".
HEADING_ERROR_DEG = 30.0

# One chunk, split the way the teacher's own push splits it. The fingertip
# starts APPROACH_GAP outside the glass's widest point and feels in, so the
# feeling leg is about that long; whatever is left of the chunk is the push.
FEEL_WAYPOINTS = round(APPROACH_GAP_MM / FEEL_STEP_MM)          # 20
PUSH_WAYPOINTS = CHUNK - FEEL_WAYPOINTS                          # 100
FEEL_MM = FEEL_WAYPOINTS * FEEL_STEP_MM                          # 10 mm
PUSH_MM = PUSH_WAYPOINTS * PUSH_STEP_MM                          # 100 mm


# --------------------------------------------------------------------------- #
# The bench's own arithmetic, copied rather than guessed
# --------------------------------------------------------------------------- #


def has_room(point, others, margin: float = 0.0) -> bool:
    """bench/bench.py ``has_room``: no other glass's edge inside GRIP_ROOM."""
    return all(
        math.hypot(point[0] - x, point[1] - y) >= GRIP_ROOM_MM + width / 2.0 + margin
        for x, y, width in others
    )


def _segment_distance(point, a, b) -> float:
    """01-one-fixed-nudge/plan.py ``segment_distance``."""
    point, a, b = (np.asarray(v, dtype=float) for v in (point, a, b))
    along = b - a
    t = float(np.clip((point - a) @ along / max(along @ along, 1e-12), 0.0, 1.0))
    return float(np.linalg.norm(point - (a + t * along)))


def jaw_parts(fingertip, heading: float):
    """The three boxes of the closed jaw in plan, as (corners, label) pairs.

    The jaw points the way it pushes, so everything is behind the fingertip.
    """
    forward = np.array([math.cos(heading), math.sin(heading)])
    side = np.array([-forward[1], forward[0]])
    fingertip = np.asarray(fingertip, dtype=float)
    out = []
    for near, far, half, label in (
        (0.0, FINGER_LENGTH_MM, JAW_THICKNESS_MM / 2.0, "fingers"),
        (FINGER_LENGTH_MM, FINGER_LENGTH_MM + BODY_LENGTH_MM, BODY_SIZE_MM / 2.0, "body"),
        (FINGER_LENGTH_MM + BODY_LENGTH_MM, TOOL_LENGTH_MM, BODY_SIZE_MM / 2.0, "wrist"),
    ):
        a = fingertip - near * forward
        b = fingertip - far * forward
        out.append(([a + half * side, b + half * side, b - half * side, a - half * side], label))
    return out


def body_clearance(fingertip, heading: float, glass) -> float:
    """Millimetres between the jaw's body-and-wrist box and a glass's rim.

    The box is checked as the segment plan.py checks it, from the wrist to the
    back of the fingers, against half the body plus the glass's radius.
    Negative means the jaw is through the glass.
    """
    forward = np.array([math.cos(heading), math.sin(heading)])
    fingertip = np.asarray(fingertip, dtype=float)
    wrist = fingertip - TOOL_LENGTH_MM * forward
    back_of_fingers = fingertip - FINGER_LENGTH_MM * forward
    reach = BODY_SIZE_MM / 2.0 + glass[2] / 2.0
    return _segment_distance(glass[:2], wrist, back_of_fingers) - reach


def one_chunk(fingertip, heading: float) -> np.ndarray:
    """One demonstration as the (CHUNK, 5) numbers chunks.py would fit on.

    The fingertip feels forward at FEEL_SPEED and then pushes at PUSH_SPEED,
    one waypoint every WAYPOINT_PERIOD, and the heading is carried as its
    cosine and sine. That is ``to_action`` applied to the path the bench's own
    macro produces.
    """
    forward = np.array([math.cos(heading), math.sin(heading)])
    gone = np.concatenate(
        [
            np.arange(1, FEEL_WAYPOINTS + 1) * FEEL_STEP_MM,
            FEEL_MM + np.arange(1, PUSH_WAYPOINTS + 1) * PUSH_STEP_MM,
        ]
    )
    points = np.asarray(fingertip, dtype=float) + gone[:, None] * forward
    return np.column_stack(
        [
            points,
            np.full(CHUNK, PUSH_HEIGHT_MM),
            np.full(CHUNK, math.cos(heading)),
            np.full(CHUNK, math.sin(heading)),
        ]
    )


# --------------------------------------------------------------------------- #
# 1. how it works: the waypoint spacing is the speed
# --------------------------------------------------------------------------- #


def waypoint_spacing_is_the_speed() -> None:
    """One chunk drawn at its true waypoint spacing, between two looks.

    The page says two things about a chunk that are hard to picture from the
    words: that how far apart the waypoints are is how fast the jaw goes, and
    that the whole chunk is one span in which nothing is read. Both are in this
    one drawing, because they are the same fact about a fixed consumption rate.
    """
    figure, axis = new(11.4, 3.1)
    bare(axis)

    feel = np.arange(1, FEEL_WAYPOINTS + 1) * FEEL_STEP_MM
    push = FEEL_MM + np.arange(1, PUSH_WAYPOINTS + 1) * PUSH_STEP_MM
    total = float(push[-1])

    axis.plot([0, total], [0, 0], color=MUTED, lw=1.0, zorder=1)
    axis.scatter(feel, np.zeros_like(feel), s=16, color=GOOD, zorder=4)
    axis.scatter(push, np.zeros_like(push), s=16, color=GLASS, zorder=4)

    # The two looks, which are the only moments the table is read.
    for where, label in ((0.0, "look()"), (total, "look() again")):
        axis.plot([where, where], [-0.52, 0.52], color=INK, lw=1.4, zorder=5)
        axis.text(where, 0.60, label, fontsize=LABEL_SIZE, color=INK, ha="center",
                  va="bottom", weight="bold", zorder=6)

    axis.annotate("", xy=(total, 0.40), xytext=(0.0, 0.40), zorder=6,
                  arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.0,
                                  shrinkA=0, shrinkB=0))
    axis.text(total / 2.0, 0.46,
              f"one chunk: {CHUNK} waypoints, {WAYPOINT_MS} ms apart, "
              f"{CHUNK * WAYPOINT_MS / 1000:.0f} s with nothing read",
              fontsize=LABEL_SIZE, color=INK, ha="center", va="bottom", zorder=6)

    for span, colour, label, where in (
        ((0.0, FEEL_MM), GOOD, f"feeling for the glass:\n{FEEL_WAYPOINTS} waypoints, "
                               f"{FEEL_STEP_MM:.1f} mm apart", "left"),
        ((FEEL_MM, total), GLASS, f"pushing it:\n{PUSH_WAYPOINTS} waypoints, "
                                  f"{PUSH_STEP_MM:.0f} mm apart", "center"),
    ):
        axis.annotate("", xy=(span[1], -0.36), xytext=(span[0], -0.36), zorder=6,
                      arrowprops=dict(arrowstyle="<|-|>", color=colour, lw=1.0,
                                      shrinkA=0, shrinkB=0))
        axis.text(span[0] + 2 if where == "left" else sum(span) / 2.0, -0.46, label,
                  fontsize=LABEL_SIZE, color=colour,
                  ha="left" if where == "left" else "center", va="top", zorder=6)

    # The cap, drawn to the same scale as the dots so the gap between them can
    # be compared against it by eye.
    axis.plot([0.0, CAP_MM], [-1.30, -1.30], color=WARN, lw=3.5,
              solid_capstyle="butt", zorder=5)
    axis.text(CAP_MM + 4, -1.30,
              f"{CAP_MM:.0f} mm: as far as the jaw can travel in one period, so no two "
              "waypoints may be further apart than this",
              fontsize=NOTE_SIZE, color=WARN, ha="left", va="center", zorder=6)

    axis.set_xlim(-6, total + 10)
    axis.set_ylim(-1.60, 1.05)
    axis.set_title("How far apart the waypoints are is how fast the jaw goes",
                   fontsize=TITLE_SIZE, color=INK, pad=14)
    print(f"  chunk: {FEEL_WAYPOINTS} + {PUSH_WAYPOINTS} = {CHUNK} waypoints "
          f"over {total:.0f} mm, cap {CAP_MM:.0f} mm")
    save(figure, "imitation-the-waypoint-spacing-is-the-speed.png")


# --------------------------------------------------------------------------- #
# 2. how it works: what averaging two good pushes produces
# --------------------------------------------------------------------------- #


def legal_push(middle, radius: float, others, heading: float) -> float | None:
    """The shortest push along ``heading`` that frees the glass, or None.

    01-one-fixed-nudge/plan.py ``along``, cut down to the part this picture
    needs: the fingertip path, the finger segment and the wrist-and-body
    segment are each checked against every other glass, and the search stops
    at the first length that gives the glass room with AIM_MARGIN to spare.
    """
    forward = np.array([math.cos(heading), math.sin(heading)])
    middle = np.asarray(middle, dtype=float)
    start = middle - (radius + APPROACH_GAP_MM) * forward
    wrist = start - TOOL_LENGTH_MM * forward
    for travel in np.arange(STEP_MM, 200.0 + 1e-9, STEP_MM):
        end = middle + travel * forward
        for x, y, width in others:
            centre, other = (x, y), width / 2.0
            passing = min(radius + other + CLEARANCE_MM,
                          float(np.linalg.norm(np.array(centre) - middle)) - 1.0)
            if (_segment_distance(centre, middle, end) < passing
                    or _segment_distance(centre, start - FINGER_LENGTH_MM * forward, end)
                    < JAW_THICKNESS_MM / 2.0 + other + CLEARANCE_MM
                    or _segment_distance(centre, wrist, end - FINGER_LENGTH_MM * forward)
                    < BODY_SIZE_MM / 2.0 + other + CLEARANCE_MM):
                return None
        if has_room(end, others, AIM_MARGIN_MM):
            return float(travel)
    return None


def the_average_of_two_good_pushes() -> None:
    """Two demonstrations that disagree, and the chunk halfway between them.

    Everything here is computed. The pair is crowded by the bench's own
    ``has_room``; each demonstration is the shortest push that frees both
    glasses and clears the jaw, found the way plan.py finds it; and the third
    path is the two averaged waypoint by waypoint, which is the shape of answer
    a model fitted to name one chunk is pulled towards.
    """
    rim = NARROW_RIM_MM
    apart = 100.0
    left = (-apart / 2.0, 0.0)
    right = (apart / 2.0, 0.0)
    pair = [(*left, rim), (*right, rim)]
    assert not has_room(left, [pair[1]]) and not has_room(right, [pair[0]]), (
        "the picture claims the pair is crowded and it is not"
    )

    # Away from the neighbour is blocked by the neighbour, so both of the
    # teacher's answers push one glass sideways. They are mirror images.
    heading = -math.pi / 2.0
    travel = legal_push(left, rim / 2.0, [pair[1]], heading)
    assert travel is not None, "neither demonstration is a push the jaw could make"
    assert legal_push(right, rim / 2.0, [pair[0]], heading) == travel

    forward = np.array([math.cos(heading), math.sin(heading)])
    kept = FEEL_WAYPOINTS + round(travel / PUSH_STEP_MM)
    one = one_chunk(np.array(left) - (rim / 2.0 + APPROACH_GAP_MM) * forward, heading)[:kept]
    two = one_chunk(np.array(right) - (rim / 2.0 + APPROACH_GAP_MM) * forward, heading)[:kept]
    middle = (one + two) / 2.0

    # The averaged chunk is a legal push that touches nothing: it runs down the
    # midline, and the fingers are half their thickness from each glass's rim.
    to_spare = apart / 2.0 - rim / 2.0 - JAW_THICKNESS_MM / 2.0
    assert to_spare > 0.0, "the averaged chunk would not fit between the glasses"
    assert abs(middle[0, 0]) < 1e-9, "the averaged chunk is not on the midline"

    figure, axis = new(9.8, 5.4)
    bare(axis)
    axis.set_aspect("equal")

    for centre in (left, right):
        glass_from_above(axis, centre, rim, colour=GLASS, alpha=0.26, edge=GLASS)

    for route in (one, two):
        axis.annotate("", xy=route[-1, :2], xytext=route[0, :2], zorder=7,
                      arrowprops=dict(arrowstyle="-|>", mutation_scale=18, color=GOOD, lw=2.4,
                                      shrinkA=0, shrinkB=0))
    axis.text(left[0] - 46, 12, f"a demonstration:\nthis glass moves {travel:.0f} mm",
              fontsize=LABEL_SIZE, color=GOOD, ha="right", va="center", weight="bold", zorder=7)
    axis.text(right[0] + 46, 12, "and another:\nso does this one",
              fontsize=LABEL_SIZE, color=GOOD, ha="left", va="center", weight="bold", zorder=7)

    axis.add_patch(Rectangle((-JAW_THICKNESS_MM / 2.0, middle[-1, 1]), JAW_THICKNESS_MM,
                             middle[0, 1] - middle[-1, 1], facecolor=_tint(WARN, 0.80),
                             edgecolor=WARN, lw=1.0, zorder=4))
    axis.annotate("", xy=middle[-1, :2], xytext=middle[0, :2], zorder=8,
                  arrowprops=dict(arrowstyle="-|>", mutation_scale=18, color=WARN, lw=2.4,
                                  shrinkA=0, shrinkB=0))
    axis.annotate(
        f"halfway between the two: the jaw comes down\n"
        f"the middle with {to_spare:.0f} mm to spare and touches neither",
        xy=(-JAW_THICKNESS_MM / 2.0 - 2, middle[0, 1] - 18), xytext=(-104, 86),
        fontsize=LABEL_SIZE, color=WARN, ha="center", va="bottom", weight="bold", zorder=9,
        arrowprops=dict(arrowstyle="-|>", color=WARN, lw=1.2, shrinkA=4, shrinkB=2),
    )

    axis.set_xlim(-215, 215)
    axis.set_ylim(-62, 124)
    axis.set_title("Both demonstrations are right, and the chunk between them is not",
                   fontsize=TITLE_SIZE, color=INK, pad=12)
    axis.text(0.5, -0.03,
              f"The pair stands {apart:.0f} mm apart and each glass needs "
              f"{GRIP_ROOM_MM + rim / 2.0:.0f} mm clear, so neither can be gripped. The chunk between "
              "the two spends a push and changes nothing.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.6, color=MUTED)

    print(f"  pair {apart:.0f} mm apart, each push {travel:.0f} mm; the averaged chunk runs down "
          f"the midline with {to_spare:.0f} mm to spare")
    save(figure, "imitation-the-average-of-two-good-pushes.png")


# --------------------------------------------------------------------------- #
# 3. the code: what push_segment keeps
# --------------------------------------------------------------------------- #


def what_a_demonstration_keeps() -> None:
    """The recorded path as a height profile, with the two legs that are copied.

    The conversion is the join this solution lives on and it is three lines of
    indexing, which is exactly the kind of thing a reader believes and cannot
    picture. Drawn as height against distance, the five legs are obvious and so
    is which two of them are the demonstration.
    """
    figure, axis = new(10.0, 4.0)
    bare(axis)

    end = FEEL_MM + PUSH_MM
    legs = [
        ((0.0, TRAVEL_HEIGHT_MM), (0.0, PUSH_HEIGHT_MM), MUTED, "the examiner brings it down"),
        ((0.0, PUSH_HEIGHT_MM), (FEEL_MM, PUSH_HEIGHT_MM), GOOD, None),
        ((FEEL_MM, PUSH_HEIGHT_MM), (end, PUSH_HEIGHT_MM), GOOD, None),
        ((end - RETREAT_MM, TRAVEL_HEIGHT_MM), (end - RETREAT_MM, PUSH_HEIGHT_MM), MUTED, None),
    ]
    for (x0, y0), (x1, y1), colour, _ in legs:
        axis.plot([x0, x1], [y0, y1], color=colour, lw=2.6 if colour == GOOD else 1.8,
                  zorder=4, solid_capstyle="round")

    # The kept window: from the first waypoint at push height to the furthest
    # point reached from it, which is where the back-off starts.
    axis.add_patch(Rectangle((0.0, PUSH_HEIGHT_MM - 17), end, 34, facecolor=_tint(GOOD, 0.86),
                             edgecolor=GOOD, lw=1.1, zorder=2))

    axis.annotate("", xy=(0.0, TRAVEL_HEIGHT_MM - 18), xytext=(0.0, TRAVEL_HEIGHT_MM),
                  arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.8, shrinkA=0, shrinkB=0),
                  zorder=5)
    axis.annotate("", xy=(end - RETREAT_MM, TRAVEL_HEIGHT_MM),
                  xytext=(end - RETREAT_MM, TRAVEL_HEIGHT_MM - 18),
                  arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.8, shrinkA=0, shrinkB=0),
                  zorder=5)
    # The back-off retraces the push, so it is drawn above the line rather than on it.
    axis.annotate("", xy=(end - RETREAT_MM, PUSH_HEIGHT_MM + 40), xytext=(end, PUSH_HEIGHT_MM + 40),
                  arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.6, shrinkA=0, shrinkB=0),
                  zorder=6)

    axis.text(-7, TRAVEL_HEIGHT_MM / 2.0,
              f"down from\n{TRAVEL_HEIGHT_MM:.0f} mm",
              fontsize=NOTE_SIZE, color=MUTED, ha="right", va="center", zorder=7)
    axis.text(end - RETREAT_MM + 8, TRAVEL_HEIGHT_MM / 2.0 + 20,
              "up again", fontsize=NOTE_SIZE, color=MUTED, ha="left", va="center", zorder=7)
    axis.text(end + 6, PUSH_HEIGHT_MM + 40,
              f"back off\n{RETREAT_MM:.0f} mm", fontsize=NOTE_SIZE, color=MUTED,
              ha="left", va="center", zorder=7)

    axis.text(FEEL_MM / 2.0, PUSH_HEIGHT_MM - 26, "feel", fontsize=LABEL_SIZE, color=GOOD,
              ha="center", va="top", weight="bold", zorder=7)
    axis.text(FEEL_MM + PUSH_MM / 2.0, PUSH_HEIGHT_MM - 26, "push", fontsize=LABEL_SIZE,
              color=GOOD, ha="center", va="top", weight="bold", zorder=7)
    axis.text(end / 2.0, PUSH_HEIGHT_MM - 58,
              f"the demonstration: from the first waypoint at {PUSH_HEIGHT_MM:.0f} mm\n"
              "to the furthest point the jaw reached",
              fontsize=LABEL_SIZE, color=GOOD, ha="center", va="top", zorder=7)

    axis.plot([-14, end + 22], [PUSH_HEIGHT_MM, PUSH_HEIGHT_MM], color=MUTED, lw=0.7,
              ls=(0, (4, 4)), zorder=1)
    axis.text(end + 24, PUSH_HEIGHT_MM, f"{PUSH_HEIGHT_MM:.0f} mm", fontsize=NOTE_SIZE,
              color=MUTED, ha="left", va="center", zorder=7)

    axis.set_xlim(-48, end + 56)
    axis.set_ylim(-92, TRAVEL_HEIGHT_MM + 30)
    axis.set_title("A recorded path has five legs, and two of them are the demonstration",
                   fontsize=TITLE_SIZE, color=INK, pad=12)
    axis.text(0.5, -0.02,
              "Height above the table against distance travelled across it. The three grey legs "
              "are the examiner's own, so nothing copies them.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.6, color=MUTED)
    save(figure, "imitation-what-a-demonstration-keeps.png")


# --------------------------------------------------------------------------- #
# 4. the code: why the heading is carried as a cosine and a sine
# --------------------------------------------------------------------------- #


def heading_as_cosine_and_sine() -> None:
    """Two pushes two degrees apart, as one wrapping number and as two that do not.

    The same quantity in the two encodings, side by side, because that is the
    only way to see that the cliff is in the encoding and not in the pushes.
    """
    one, two = 179.0, -179.0
    figure, (left, right) = new(10.0, 3.9, columns=2)

    bare(left)
    left.plot([-180, 180], [0, 0], color=INK, lw=1.2, zorder=3)
    for tick in (-180, -90, 0, 90, 180):
        left.plot([tick, tick], [-0.05, 0.05], color=INK, lw=1.0, zorder=3)
        left.text(tick, -0.12, f"{tick}", fontsize=NOTE_SIZE, color=MUTED,
                  ha="center", va="top", zorder=4)
    for where, colour, label in ((one, GLASS, "one push"), (two, WARN, "the other")):
        left.scatter([where], [0], s=70, color=colour, zorder=6)
        left.text(where, 0.10, label, fontsize=LABEL_SIZE, color=colour, ha="center",
                  va="bottom", weight="bold", zorder=6)
    left.annotate("", xy=(two, 0.42), xytext=(one, 0.42), zorder=6,
                  arrowprops=dict(arrowstyle="<|-|>", color=WARN, lw=1.2,
                                  shrinkA=0, shrinkB=0))
    left.text(0, 0.47, f"{one - two:.0f} apart",
              fontsize=LABEL_SIZE, color=WARN, ha="center", va="bottom", weight="bold", zorder=6)
    left.set_xlim(-240, 240)
    left.set_ylim(-0.45, 0.72)
    left.set_title("As one angle, in degrees, which wraps", fontsize=11, color=INK, pad=10)

    bare(right)
    right.set_aspect("equal")
    right.add_patch(Circle((0, 0), 1.0, facecolor="none", edgecolor=MUTED, lw=1.0,
                           ls=(0, (4, 3)), zorder=2))
    right.plot([-1.15, 1.15], [0, 0], color=MUTED, lw=0.7, zorder=1)
    right.plot([0, 0], [-1.15, 1.15], color=MUTED, lw=0.7, zorder=1)
    for angle, colour in ((one, GLASS), (two, WARN)):
        point = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        right.annotate("", xy=point, xytext=(0, 0), zorder=5,
                       arrowprops=dict(arrowstyle="-|>", color=colour, lw=2.0,
                                       shrinkA=0, shrinkB=0))
        right.scatter([point[0]], [point[1]], s=70, color=colour, zorder=6)
    apart = math.dist(
        (math.cos(math.radians(one)), math.sin(math.radians(one))),
        (math.cos(math.radians(two)), math.sin(math.radians(two))),
    )
    right.annotate(f"{apart:.2f} apart", xy=(-1.0, 0.0), xytext=(-0.30, 0.62),
                   fontsize=LABEL_SIZE, color=GOOD, ha="center", va="bottom",
                   weight="bold", zorder=6,
                   arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.1, shrinkA=4, shrinkB=4))
    right.set_xlim(-1.30, 1.30)
    right.set_ylim(-1.20, 1.30)
    right.set_title("As a cosine and a sine, which do not", fontsize=11, color=INK, pad=10)

    figure.text(0.5, 0.055,
                "The same two pushes, two degrees apart on the table, in the two encodings. "
                "A model fitted on the angle learns the wrap as a cliff.",
                ha="center", va="bottom", fontsize=8.8, color=MUTED)
    print(f"  {one:.0f} and {two:.0f} degrees: {one - two:.0f} apart as an angle, "
          f"{apart:.2f} apart as a cosine and sine pair")
    save(figure, "imitation-heading-as-cosine-and-sine.png")


# --------------------------------------------------------------------------- #
# 5. a worked example: where a refusal comes from
# --------------------------------------------------------------------------- #


def where_a_refusal_comes_from() -> None:
    """One pass of the run-time loop, with everything that takes a glass out of play.

    The point of the chart is the shape of the route rather than the steps: two
    arrows reach "refused, with a reason" and neither of them passes through
    the policy, because the policy's only output is waypoints.
    """
    width, height = 11.5, 7.0
    figure, axis = sheet(width, height)
    chain_w = 6.4
    chain_x = 0.28 + chain_w / 2.0
    side_w = 3.9
    side_x = chain_x + chain_w / 2.0 + 0.70 + side_w / 2.0
    corridor = chain_x + chain_w / 2.0 + 0.35

    y = title(figure, axis, width, height - 0.12,
              "Every refusal is made in front of the policy") - 0.34
    first_top = y

    y = box(
        figure, axis, chain_x, y, chain_w,
        "look(): where every glass stands, how wide it is, and how wide\n"
        "the foot it stands on is.",
    )
    first_middle = (first_top + y) / 2.0

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        f"Rack every glass that already has {GRIP_ROOM_MM:.0f} mm of clear room, and\n"
        "look again. Only a crowded table reaches the rest of this.",
        edge=GOOD, face=_tint(GOOD, 0.93),
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    gate_top = y - GAP
    y = box(
        figure, axis, chain_x, gate_top, chain_w,
        f"The shared tipping limit, on the measured foot, at the jaw's top edge\n"
        f"{JAW_TOP_MM:.0f} mm up: a glass that tips rather than slides even at the\n"
        f"lowest friction the project allows, {MU_LOWEST}, is out of play.",
        edge=WARN, face=_tint(WARN, 0.92),
    )
    gate_middle = (gate_top + y) / 2.0

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    budget_top = y - GAP
    y = box(
        figure, axis, chain_x, budget_top, chain_w,
        f"The push budget: a glass already pushed {PUSHES_PER_GLASS} times, or a table that\n"
        f"has spent its {PUSHES_PER_TABLE}, is out of play too.",
        edge=WARN, face=_tint(WARN, 0.92),
    )
    budget_middle = (budget_top + y) / 2.0

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    policy_top = y - GAP
    y = box(
        figure, axis, chain_x, policy_top, chain_w,
        "The policy: one picture of the table in, one chunk of\n"
        f"{CHUNK} waypoints out. There is no channel in a chunk for\n"
        "\"I cannot move this glass, and here is why\".",
        edge=GLASS, face=_tint(GLASS, 0.88), weight="bold",
    )

    arrow(axis, (chain_x, y), (chain_x, y - GAP))
    y = box(
        figure, axis, chain_x, y - GAP, chain_w,
        "The chunk is charged to one of the glasses still in play, so a\n"
        "glass taken out above can never be pushed. The examiner follows\n"
        "the waypoints, and the arm looks again.",
    )

    side_top = gate_middle + 0.46
    side_bottom = box(
        figure, axis, side_x, side_top, side_w,
        "Refused, with a reason.\n\n"
        "Both routes reach this without\n"
        "passing through the policy.",
        edge=WARN, face=_tint(WARN, 0.95), weight="bold",
    )
    side_middle = (side_top + side_bottom) / 2.0
    elbow(axis, (chain_x + chain_w / 2.0, gate_middle),
          (side_x - side_w / 2.0, side_middle), corridor, colour=WARN)
    elbow(axis, (chain_x + chain_w / 2.0, budget_middle),
          (side_x - side_w / 2.0, side_middle - 0.0001), corridor, colour=WARN)

    note(
        axis, side_x, policy_top + 0.08,
        f"A glass the friction range leaves undecided\n"
        f"is handed to the policy as it is. This solution\n"
        f"never makes the teacher's {PROBE_MM} mm test push,\n"
        f"because a chunk cannot ask a question.",
        colour=INK, ha="center", figure=figure,
    )

    finish(figure, axis, "imitation-where-a-refusal-comes-from.png", y - 0.24)
    save(figure, "imitation-where-a-refusal-comes-from.png")


# --------------------------------------------------------------------------- #
# 6. a worked example: thirty degrees of heading
# --------------------------------------------------------------------------- #


def thirty_degrees_of_heading() -> None:
    """The measured failure, drawn: same fingertip, thirty degrees, body over a glass.

    The jaw is 270 mm of arm behind a 120 mm finger, so a heading error does
    not move the fingertip much and moves the far end of the wrist a long way.
    The picture checks its own claim with plan.py's own clearance test rather
    than asserting it.
    """
    rim = WIDE_RIM_MM
    target = (0.0, 0.0)
    crowder = (0.0, 110.0, rim)          # why there is a push at all: 110 < 70 + 50
    third = (260.0, 115.0, rim)          # a third glass, well clear of the straight jaw
    assert not has_room(target, [crowder]), "the target is not crowded, so the picture is wrong"

    heading = math.pi                     # push the target away along -x
    fingertip = np.array([rim / 2.0 + APPROACH_GAP_MM, 0.0])
    travel = None
    for candidate in np.arange(STEP_MM, 200.0 + 1e-9, STEP_MM):
        moved = (target[0] - candidate, target[1])
        if has_room(moved, [crowder, third], AIM_MARGIN_MM):
            travel = float(candidate)
            break
    assert travel is not None

    straight = body_clearance(fingertip, heading, third)
    skewed = body_clearance(fingertip, heading + math.radians(HEADING_ERROR_DEG), third)
    assert straight > CLEARANCE_MM, f"the teacher's own heading does not clear: {straight:.1f} mm"
    assert skewed < CLEARANCE_MM, f"{HEADING_ERROR_DEG:.0f} degrees off still clears: {skewed:.1f} mm"

    figure, axis = new(10.6, 5.6)
    bare(axis)
    axis.set_aspect("equal")

    skewed_heading = heading + math.radians(HEADING_ERROR_DEG)
    for which, colour, angle in (("off", WARN, skewed_heading), ("on", INK, heading)):
        for corners, _part in jaw_parts(fingertip, angle):
            axis.add_patch(Polygon(corners, closed=True,
                                   facecolor=_tint(colour, 0.80 if which == "on" else 0.74),
                                   edgecolor=colour, lw=1.3,
                                   ls="solid" if which == "on" else (0, (4, 3)),
                                   zorder=3 if which == "off" else 4))

    for centre in (target, crowder[:2], third[:2]):
        glass_from_above(axis, centre, rim, colour=GLASS, alpha=0.32, edge=GLASS, zorder=5)
    axis.scatter([fingertip[0]], [fingertip[1]], s=52, color=INK, zorder=9)
    axis.text(fingertip[0] - 14, -74, "the same fingertip in both", fontsize=NOTE_SIZE,
              color=INK, ha="right", va="center", zorder=9)

    axis.annotate("", xy=(target[0] - travel, 0.0), xytext=(target[0] - 6, 0.0), zorder=9,
                  arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=2.0, shrinkA=0, shrinkB=0))
    axis.text(target[0] - travel - 10, 0.0, f"the push:\n{travel:.0f} mm", fontsize=NOTE_SIZE,
              color=GOOD, ha="right", va="center", zorder=9)

    tail = fingertip - TOOL_LENGTH_MM * np.array([math.cos(heading), math.sin(heading)])
    axis.text(tail[0] - 6, -78, "the teacher's heading", fontsize=LABEL_SIZE, color=INK,
              ha="center", va="center", weight="bold", zorder=9)
    swing = TOOL_LENGTH_MM * math.sin(math.radians(HEADING_ERROR_DEG))
    skewed_tail = fingertip - TOOL_LENGTH_MM * np.array(
        [math.cos(skewed_heading), math.sin(skewed_heading)]
    )
    axis.annotate(
        f"{HEADING_ERROR_DEG:.0f} degrees off, and the far end of the\n"
        f"wrist moves {swing:.0f} mm, because it is {TOOL_LENGTH_MM:.0f} mm\n"
        "behind the fingertip",
        xy=(skewed_tail[0], skewed_tail[1] + 8), xytext=(205, 250),
        fontsize=LABEL_SIZE, color=WARN, ha="center", va="bottom", weight="bold", zorder=9,
        arrowprops=dict(arrowstyle="-|>", color=WARN, lw=1.2, shrinkA=4, shrinkB=4),
    )
    axis.text(130, -108,
              f"this glass is {straight:.0f} mm clear of the {BODY_SIZE_MM:.0f} mm body at the "
              f"teacher's heading, and under it at {HEADING_ERROR_DEG:.0f} degrees off",
              fontsize=LABEL_SIZE, color=INK, ha="center", va="top", zorder=9)

    axis.set_xlim(-160, 420)
    axis.set_ylim(-152, 296)
    axis.set_title("Thirty degrees of heading, and the jaw's own body is over a glass",
                   fontsize=TITLE_SIZE, color=INK, pad=12)
    axis.text(0.5, -0.03,
              "The examiner brings the jaw down to the chunk's first waypoint and stops if it "
              "touches anything, so a push that starts like this is reported blocked with nothing moved.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.6, color=MUTED)

    print(f"  body clearance from the third glass: {straight:.1f} mm at the teacher's heading, "
          f"{skewed:.1f} mm at {HEADING_ERROR_DEG:.0f} degrees off (veto at {CLEARANCE_MM:.0f} mm)")
    save(figure, "imitation-thirty-degrees-of-heading.png")


def main() -> None:
    waypoint_spacing_is_the_speed()
    the_average_of_two_good_pushes()
    what_a_demonstration_keeps()
    heading_as_cosine_and_sine()
    where_a_refusal_comes_from()
    thirty_degrees_of_heading()


if __name__ == "__main__":
    main()
