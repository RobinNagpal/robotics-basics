"""The five pictures for docs/08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md.

That document states the problem: four to six glasses of one kind on the table,
which kind the worked examples use, what an answer is given and what it must
hand back. The two difficulties are drawn in make_difficulty_pictures.py,
three views each, rather than here.

Each picture shows one thing, so the arrangement on the table and the four
kinds of glass are two pictures and not two panels of one.

Every length here is read out of the cell's own constants, so the pictures
cannot drift from the code:

  * the kinds and their ranges of size, from ``glasses/shapes.py KIND_RANGES``;
  * the guaranteed smallest gap between two centres, from
    ``glasses/spawn.py MIN_SEPARATION``;
  * the glass zone, from ``rack/layout.py GLASS_ZONE``;
  * the survey height, the sideways step between the two pictures of a pair and
    the stations themselves, from ``arm/dimensions.py``;
  * how much table one picture covers, worked out from the wrist camera's own
    lens exactly as ``bench/data.py frame()`` works it out.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_problem_pictures.py
"""

from __future__ import annotations

import math
import sys
from functools import cache
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from diagram_style import (  # noqa: E402
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
    save,
    splay_circles,
    splay_covers,
    splay_patch,
    splay_width,
)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code" / "src" / "08_seeing-the-glasses" / "work_cell"))

from work_cell.arm.dimensions import (  # noqa: E402
    GRIPPER_MAX_OPENING,
    SURVEY_BASELINE,
    SURVEY_HEIGHT,
    survey_stations,
)
from work_cell.glasses.shapes import KIND_RANGES, build  # noqa: E402
from work_cell.glasses.spawn import MIN_SEPARATION  # noqa: E402
from work_cell.rack.layout import GLASS_ZONE  # noqa: E402

# ----------------------------------------------------------------- the numbers
#
# Millimetres everywhere in this file, because every label in these pictures is
# in millimetres. The cell's own constants are in metres.

MM = 1000.0

ZONE = tuple(v * MM for v in GLASS_ZONE)          # x from, x to, y from, y to
ZONE_W = ZONE[1] - ZONE[0]
ZONE_D = ZONE[3] - ZONE[2]
SEPARATION = MIN_SEPARATION * MM
HEIGHT = SURVEY_HEIGHT * MM
BASELINE = SURVEY_BASELINE * MM

# The wrist camera, as arm/camera/wrist_camera.urdf.xacro declares it and as
# bench/render.py reads it. bench/ cannot be imported here because its modules
# import each other by bare name, so the three numbers are repeated and the
# frame is worked out from them the way bench/data.py frame() does.
PIXELS_ACROSS, PIXELS_DOWN = 320, 240
HORIZONTAL_FOV = 1.047
FOCAL = (PIXELS_ACROSS / 2.0) / math.tan(HORIZONTAL_FOV / 2.0)
FRAME = (HEIGHT * PIXELS_ACROSS / FOCAL, HEIGHT * PIXELS_DOWN / FOCAL)

# The part of one picture a station can be credited with, and from it the
# stations themselves. Same arithmetic as bench/data.py shared().
SHARED = (
    FRAME[0] - GRIPPER_MAX_OPENING * MM,
    FRAME[1] - BASELINE - GRIPPER_MAX_OPENING * MM,
)
STATIONS = [
    (float(s[0]) * MM, float(s[1]) * MM)
    for s in survey_stations(GLASS_ZONE, tuple(v / MM for v in SHARED))
]

KINDS = ("straight_glass", "tapered_glass", "stemmed_glass", "short_stemmed_glass")
PLAIN = {
    "straight_glass": "straight",
    "tapered_glass": "tapered",
    "stemmed_glass": "stemmed",
    "short_stemmed_glass": "short stemmed",
}

def span(kind: str, name: str) -> tuple[float, float]:
    """One of a kind's ranges, in millimetres."""
    low, high = KIND_RANGES[kind][name]
    return low * MM, high * MM

def widest(kind: str) -> str:
    """Which range gives the widest part of a glass of this kind."""
    return "rim_diameter" if "rim_diameter" in KIND_RANGES[kind] else "bowl_diameter"

def outline_mm(kind: str, tall: bool):
    """The cell's own outline for the tallest or shortest glass of a kind.

    Returns (height above the table, radius) as two arrays in millimetres.
    Only the proportions with a range are given; the rest keep their defaults,
    which is how shapes.build is meant to be called.
    """
    picked = {}
    for name, (low, high) in KIND_RANGES[kind].items():
        if name == "height":
            picked[name] = high if tall else low
        elif name in ("rim_diameter", "bowl_diameter", "stem_diameter"):
            picked[name] = high if tall else low
        else:
            picked[name] = (low + high) / 2.0
    line = build(kind, **picked)
    return np.asarray(line.height) * MM, np.asarray(line.radius) * MM

# --------------------------------------------------------------- the machinery

def panels(width: float, height: float, ratios=(1.0,)):
    """A figure with bare panels of unequal width.

    diagram_style.new gives panels of equal width, which suits a picture whose
    two halves hold the same amount. Most of these do not: a plan view of the
    zone is nearly square and a row of four glasses is wide and shallow, and
    forcing both into the same box leaves one of them in a large empty margin.
    So this mirrors ``new`` and adds the width ratios.
    """
    figure, axes = plt.subplots(
        1, len(ratios), figsize=(width, height), gridspec_kw={"width_ratios": list(ratios)}
    )
    figure.patch.set_facecolor(PAPER)
    axes = [axes] if len(ratios) == 1 else list(axes)
    for axis in axes:
        axis.set_facecolor(PAPER)
        bare(axis)
    return figure, axes

def frame_box(axis, x, y, w, h, **kw):
    kw.setdefault("fill", False)
    axis.add_patch(Rectangle((x, y), w, h, **kw))

def draw_zone(axis, label=True, colour=MUTED):
    """The glass zone, in plan, in millimetres of table."""
    frame_box(axis, ZONE[0], ZONE[2], ZONE_W, ZONE_D, ec=colour, lw=1.2, ls=(0, (6, 4)))
    if label:
        axis.text(
            (ZONE[0] + ZONE[1]) / 2.0, ZONE[2] - 14,
            f"the glass zone, {ZONE_W:.0f} mm across by {ZONE_D:.0f} mm deep",
            ha="center", va="top", fontsize=NOTE_SIZE, color=colour,
        )

def side_glass(axis, x, kind, tall, colour=GLASS, alpha=0.55, lw=1.4, base=0.0):
    """One glass of a kind, in side elevation, from the cell's own outline."""
    h, r = outline_mm(kind, tall)
    axis.fill_betweenx(h + base, x - r, x + r, facecolor=colour, alpha=alpha, lw=0.0)
    axis.plot(x + r, h + base, color=colour, lw=lw)
    axis.plot(x - r, h + base, color=colour, lw=lw)
    axis.plot([x - r[-1], x + r[-1]], [h[-1] + base] * 2, color=colour, lw=lw)
    return h, r

def height_map(nadir, glasses, grid=(PIXELS_ACROSS, PIXELS_DOWN)):
    """What one overhead picture sees, as the height of the nearest surface.

    The picture covers FRAME millimetres of table about ``nadir``, at the
    camera's own pixel count. Each glass is splayed with splay_circles, and a
    pixel takes the highest slice whose circle covers it, because that slice is
    the nearest surface along that ray. A pixel no glass covers keeps 0, the
    table.
    """
    xs = np.linspace(-FRAME[0] / 2.0, FRAME[0] / 2.0, grid[0])
    ys = np.linspace(-FRAME[1] / 2.0, FRAME[1] / 2.0, grid[1])
    gx, gy = np.meshgrid(xs, ys)
    out = np.zeros_like(gx)
    for centre, h, rim in glasses:
        circles = splay_circles(nadir, centre, h, rim)
        for index, (c, radius) in enumerate(circles):
            z = h * index / (len(circles) - 1)
            inside = (gx - c[0]) ** 2 + (gy - c[1]) ** 2 <= radius**2
            out = np.where(inside, np.maximum(out, z), out)
    return out, (-FRAME[0] / 2.0, FRAME[0] / 2.0, -FRAME[1] / 2.0, FRAME[1] / 2.0)

def connected(first, second):
    """Do two splayed silhouettes form one shape? True if any circles meet."""
    for c1, r1 in first:
        for c2, r2 in second:
            if math.hypot(*(c1 - c2)) <= r1 + r2:
                return True
    return False

def in_zone(point) -> bool:
    return ZONE[0] <= point[0] <= ZONE[1] and ZONE[2] <= point[1] <= ZONE[3]

def in_frame(point, nadir) -> bool:
    return abs(point[0] - nadir[0]) <= FRAME[0] / 2.0 and abs(point[1] - nadir[1]) <= FRAME[1] / 2.0

def double_arrow(axis, a, b, colour=INK, lw=1.1):
    axis.add_patch(
        FancyArrowPatch(a, b, arrowstyle="<|-|>", mutation_scale=9, color=colour, lw=lw, zorder=6)
    )

MASK = dict(facecolor=PAPER, edgecolor="none", pad=1.2)

def card(axis, x, y, w, h, colour=MUTED, lw=1.0, ls="-", fc="none"):
    axis.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0,rounding_size=4",
            ec=colour, fc=fc, lw=lw, ls=ls, zorder=2,
        )
    )

def splay_outline(nadir, centre, h, r):
    """splay_circles for an outline the cell actually builds.

    splay_circles takes a height and a rim and assumes the glass widens evenly
    from base to rim, which is what a tumbler does. A stemmed glass does not,
    and the whole point of the overhead picture of a stemmed glass is the
    narrow place between its foot and its bowl. So this applies the same rule —
    a slice at height z is scaled about the point below the camera by
    H / (H - z) — to the radius profile shapes.build returns.
    """
    offset = np.asarray(centre, dtype=float) - np.asarray(nadir, dtype=float)
    k = HEIGHT / (HEIGHT - h)
    return [(offset * factor, radius * factor) for factor, radius in zip(k, r)]

# -------------------------------------------- 1. the arrangement on the table

# Five tapered glasses, written down here because a picture wants an
# arrangement a reader can take in rather than a random one. The two at the
# bottom are exactly MIN_SEPARATION apart, which is what the picture marks, and
# the script checks every pair before it draws.
ARRANGEMENT = (
    ((360.0, -410.0), 215.0, 98.0),
    ((510.0, -410.0), 112.0, 72.0),
    ((620.0, -290.0), 228.0, 105.0),
    ((430.0, -245.0), 160.0, 88.0),
    ((585.0, -125.0), 95.0, 67.0),
)

def the_arrangement() -> None:
    """Four to six glasses of one kind, standing in the glass zone."""
    rim_low, rim_high = span("tapered_glass", "rim_diameter")
    high_low, high_high = span("tapered_glass", "height")
    for (centre, height, rim) in ARRANGEMENT:
        if not in_zone(centre):
            raise SystemExit(f"glass at {centre} stands outside the glass zone")
        if not rim_low <= rim <= rim_high or not high_low <= height <= high_high:
            raise SystemExit(
                f"a tapered glass {height} mm tall and {rim} mm across is out of range"
            )
    pairs = [
        (a, b, math.dist(a[0], b[0]))
        for i, a in enumerate(ARRANGEMENT) for b in ARRANGEMENT[i + 1:]
    ]
    closest = min(pairs, key=lambda p: p[2])
    if closest[2] < SEPARATION - 0.05:
        raise SystemExit(f"two glasses stand {closest[2]:.1f} mm apart, inside the guarantee")

    figure, (plan,) = panels(6.4, 6.0)
    plan.set_aspect("equal")
    draw_zone(plan, label=False)
    plan.text(
        (ZONE[0] + ZONE[1]) / 2.0, ZONE[3] + 10,
        f"the glass zone, {ZONE_W:.0f} mm across by {ZONE_D:.0f} mm deep",
        ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED,
    )
    for centre, _height, rim in ARRANGEMENT:
        plan.add_patch(Circle(centre, rim / 2.0, fc=GLASS, alpha=0.30, ec=GLASS, lw=1.3))
        plan.plot(*centre, marker="+", ms=6, mew=1.2, color=GLASS)

    a, b, gap = closest
    double_arrow(plan, a[0], b[0])
    plan.plot(
        [a[0][0], a[0][0], b[0][0], b[0][0]],
        [a[0][1], ZONE[2] - 34, ZONE[2] - 34, b[0][1]],
        color=INK, lw=0.7, ls=(0, (3, 3)),
    )
    plan.text(
        (a[0][0] + b[0][0]) / 2.0, ZONE[2] - 42,
        f"{gap:.0f} mm, the guaranteed smallest gap between centres",
        ha="center", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    plan.set_title(
        "Four to six glasses of one kind stand in the glass zone",
        fontsize=TITLE_SIZE, color=INK, pad=20,
    )
    plan.text(
        0.5, 1.004, "This arrangement has five of them, seen from above.",
        transform=plan.transAxes, ha="center", va="bottom",
        fontsize=NOTE_SIZE, color=MUTED,
    )
    plan.set_xlim(ZONE[0] - 50, ZONE[1] + 50)
    plan.set_ylim(ZONE[2] - 90, ZONE[3] + 44)
    save(figure, "four-to-six-of-one-kind.png")


# ------------------------------------------- 2. the kind every example uses

def the_kind_this_book_uses() -> None:
    """The four kinds side on, with the one the book works in picked out.

    The cell has four kinds and its arrangements cycle through them, but every
    worked example in this book uses the tapered kind. The reason is in the
    ranges themselves: the tapered range of heights is much the widest of the
    four, and that width is what makes one glass able to hide another. So the
    picture draws each kind at the tallest and the shortest its range allows,
    and the script refuses to draw anything if tapered is not in fact the kind
    with the widest range.
    """
    spans = {kind: span(kind, "height") for kind in KINDS}
    picked = max(KINDS, key=lambda kind: spans[kind][1] - spans[kind][0])
    if picked != "tapered_glass":
        raise SystemExit(
            f"the widest range of heights belongs to {PLAIN[picked]}, not to tapered, "
            "so this picture would pick out the wrong kind"
        )

    pitch = 270.0
    offset = 62.0
    figure, (side,) = panels(11.6, 4.4)
    side.set_aspect("equal")

    for index, kind in enumerate(KINDS):
        base = index * pitch
        chosen = kind == picked
        colour = GLASS if chosen else MUTED
        if chosen:
            card(side, base - 120.0, -66.0, 240.0, 322.0, colour=GLASS, lw=1.6,
                 fc="#eaf2fb")
        side_glass(side, base - offset, kind, tall=True, colour=colour,
                   alpha=0.34 if chosen else 0.20)
        side_glass(side, base + offset, kind, tall=False, colour=colour,
                   alpha=0.34 if chosen else 0.20)
        low, high = spans[kind]
        side.text(base, -18, PLAIN[kind], ha="center", va="top",
                  fontsize=LABEL_SIZE, color=INK if chosen else MUTED,
                  weight="bold" if chosen else "normal")
        side.text(base, -38, f"{low:.0f} to {high:.0f} mm tall", ha="center", va="top",
                  fontsize=NOTE_SIZE, color=colour)

    side.text(
        (KINDS.index(picked)) * pitch, 268,
        "this book works in this kind:\nits range of heights is the widest",
        ha="center", va="bottom", fontsize=NOTE_SIZE, color=GLASS,
    )
    side.plot([-150, 3 * pitch + 150], [0, 0], color=INK, lw=1.1)
    side.text(-150, 6, "the table", ha="left", va="bottom", fontsize=NOTE_SIZE, color=INK)
    side.set_title(
        "The cell's four kinds, and the one this book uses",
        fontsize=TITLE_SIZE, color=INK, pad=20,
    )
    side.text(
        0.5, 1.004, "Each kind is drawn twice: the tallest and the shortest its range allows.",
        transform=side.transAxes, ha="center", va="bottom",
        fontsize=NOTE_SIZE, color=MUTED,
    )
    side.set_xlim(-160, 3 * pitch + 160)
    side.set_ylim(-80, 320)
    save(figure, "the-kind-this-book-uses.png")

# ---------------------------------------------- 3. the widest range of sizes

def best_ray():
    """The place in the zone where hiding is most likely, and how far it reaches.

    The outward throw grows with distance from the point below the camera, so a
    glass is most likely to be hidden as far out as it can stand. A glass has
    to be inside the zone, and it has to be inside the station's own picture or
    the station never saw it. So this returns the station and the direction
    whose line through zone and picture together runs furthest, with that
    distance.
    """
    inset = 12.0        # so that a glass at the end of the line is not standing
                        # on the edge of the zone or cut off at the frame edge
    best = None
    for nadir in STATIONS:
        x_from = max(ZONE[0], nadir[0] - FRAME[0] / 2.0) + inset
        x_to = min(ZONE[1], nadir[0] + FRAME[0] / 2.0) - inset
        y_from = max(ZONE[2], nadir[1] - FRAME[1] / 2.0) + inset
        y_to = min(ZONE[3], nadir[1] + FRAME[1] / 2.0) - inset
        for corner in ((x_from, y_from), (x_from, y_to), (x_to, y_from), (x_to, y_to)):
            reach = math.dist(nadir, corner)
            if best is None or reach > best[0]:
                direction = np.array([corner[0] - nadir[0], corner[1] - nadir[1]]) / reach
                best = (reach, nadir, direction)
    return best

@cache
def hiding_separation(kind: str, tolerance: float = 0.5):
    """How far apart two glasses of a kind may stand and one still hide the other.

    The tallest of the kind stands between the camera and the shortest of the
    kind, both on the line ``best_ray`` returns and as far out as that line
    allows. A smaller separation can only make hiding easier, because it leaves
    the tall glass further out and throws its outline further, so the answer is
    found by halving the interval and asking splay_covers each time. The number
    is the helper's own answer and not arithmetic done here. Returns the
    separation and the three points the picture needs.
    """
    reach, nadir, direction = best_ray()
    short = np.array(nadir) + reach * direction
    tall_h, tall_w = span(kind, "height")[1], span(kind, widest(kind))[1]
    short_h, short_w = span(kind, "height")[0], span(kind, widest(kind))[0]
    tall_line = outline_mm(kind, tall=True)
    short_line = outline_mm(kind, tall=False)

    def silhouette(centre, height, width, line):
        # A tumbler widens evenly from base to rim, which is what splay_circles
        # itself assumes, so the two difficulty pictures and this measurement
        # are the same model. A bowl on a stem does not, so for those kinds the
        # cell's own outline is splayed instead.
        if "rim_diameter" in KIND_RANGES[kind]:
            return splay_circles(nadir, centre, height, width)
        return splay_outline(nadir, centre, *line)

    def hides(separation: float) -> bool:
        out = reach - separation
        if out <= 0.0:
            return False
        tall = np.array(nadir) + out * direction
        return splay_covers(
            silhouette(tall, tall_h, tall_w, tall_line),
            silhouette(short, short_h, short_w, short_line),
        )

    low, high = 1.0, reach
    if not hides(low):
        raise SystemExit(f"a {kind} never hides another one anywhere in the zone")
    while high - low > tolerance:
        middle = (low + high) / 2.0
        if hides(middle):
            low = middle
        else:
            high = middle
    return low, nadir, np.array(nadir) + (reach - low) * direction, short

def the_widest_range_of_sizes() -> None:
    """The tapered kind's range of sizes, against a narrower kind's."""
    from diagram_style import new

    figure, axes = new(10.6, 5.2, columns=2)
    for axis in axes:
        bare(axis)
        axis.set_aspect("equal")

    pairs = (("tapered_glass", axes[0]), ("straight_glass", axes[1]))
    for kind, axis in pairs:
        low, high = span(kind, "height")
        wide_low, wide_high = span(kind, widest(kind))
        separation, _nadir, _tall, _short = hiding_separation(kind)
        colour = GLASS if kind == "tapered_glass" else MUTED
        side_glass(axis, 0.0, kind, tall=False, colour=colour, alpha=0.30)
        side_glass(axis, 150.0, kind, tall=True, colour=colour, alpha=0.30)
        axis.plot([-70, 232], [0, 0], color=INK, lw=1.1)

        # the range itself, as a bracket between the two ends
        bracket = 222.0
        double_arrow(axis, (bracket, low), (bracket, high))
        for level, name in ((low, "shortest"), (high, "tallest")):
            axis.plot([-66, bracket], [level, level], color=INK, lw=0.7, ls=(0, (3, 3)))
            axis.text(-70, level, f"{name} {level:.0f} mm", ha="right", va="center",
                      fontsize=NOTE_SIZE, color=INK)
        axis.text(bracket + 8, (low + high) / 2.0,
                  f"{high - low:.0f} mm\nof range", ha="left", va="center",
                  fontsize=NOTE_SIZE, color=INK)

        axis.set_title(
            f"the {PLAIN[kind]} kind: {high - low:.0f} mm from end to end",
            fontsize=LABEL_SIZE + 0.8, color=colour if kind == "tapered_glass" else INK, pad=8,
        )
        axis.text(
            75.0, -34,
            f"{wide_low:.0f} to {wide_high:.0f} mm across the rim\n"
            f"thrown out {HEIGHT / (HEIGHT - low):.2f} times at the shortest, "
            f"{HEIGHT / (HEIGHT - high):.2f} at the tallest\n"
            f"so the tallest hides the shortest up to {separation:.0f} mm apart",
            ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
        )
        axis.set_xlim(-150, 288)
        axis.set_ylim(-104, 248)

    figure.subplots_adjust(top=0.82, bottom=0.03, left=0.02, right=0.98, wspace=0.05)
    figure.suptitle(
        "A kind can only hide one of its own glasses where its tall end is thrown\n"
        "much further out from under the camera than its short end",
        fontsize=TITLE_SIZE, color=INK, y=0.99,
    )
    save(figure, "the-widest-range-of-sizes.png")

# ------------------------------------------------------------- 4. what goes in

def what_goes_in() -> None:
    """Everything an answer is given, and the one thing it is not."""
    figure, (plan, read) = panels(12.6, 6.0, ratios=(0.86, 1.2))

    # -- where the camera goes, in plan
    plan.set_aspect("equal")
    draw_zone(plan, label=False)
    plan.text(
        (ZONE[0] + ZONE[1]) / 2.0, ZONE[3] + 10,
        f"the glass zone, {ZONE_W:.0f} by {ZONE_D:.0f} mm",
        ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED, bbox=MASK, zorder=7,
    )
    for centre, _height, rim in ARRANGEMENT:
        plan.add_patch(Circle(centre, rim / 2.0, fc=GLASS, alpha=0.16, ec=GLASS, lw=0.8))
    for index, nadir in enumerate(STATIONS):
        frame_box(
            plan, nadir[0] - FRAME[0] / 2.0, nadir[1] - FRAME[1] / 2.0, FRAME[0], FRAME[1],
            ec=INK, lw=0.9, ls=(0, (4, 3)), alpha=0.55,
        )
        plan.plot(*nadir, marker="+", ms=9, mew=1.3, color=INK, zorder=7)
        plan.text(
            nadir[0] + 14, nadir[1], f"station {index + 1}",
            ha="left", va="center", fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=7,
        )
    middle = STATIONS[1]
    for sign in (-1, 1):
        plan.plot(middle[0], middle[1] + sign * BASELINE / 2.0, marker="s", ms=6, color=GOOD)
    double_arrow(
        plan, (middle[0], middle[1] - BASELINE / 2.0), (middle[0], middle[1] + BASELINE / 2.0),
        colour=GOOD,
    )
    plan.text(
        ZONE[0] - 8, middle[1], f"a pair of pictures\n{BASELINE:.0f} mm apart",
        ha="right", va="center", fontsize=NOTE_SIZE, color=GOOD, bbox=MASK, zorder=7,
    )
    plan.plot([ZONE[0] - 6, middle[0] - 8], [middle[1], middle[1]],
              color=GOOD, lw=0.8, zorder=1)
    plan.text(
        STATIONS[0][0] - FRAME[0] / 2.0, STATIONS[0][1] - FRAME[1] / 2.0 - 12,
        f"each picture covers {FRAME[0]:.0f} mm by {FRAME[1]:.0f} mm of table\n"
        f"from {HEIGHT:.0f} mm up, looking straight down",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    plan.set_title(
        "Three overlapping stations, a pair of pictures at each",
        fontsize=LABEL_SIZE + 0.8, color=INK, pad=8,
    )
    plan.set_xlim(STATIONS[0][0] - FRAME[0] / 2.0 - 30, STATIONS[0][0] + FRAME[0] / 2.0 + 30)
    plan.set_ylim(STATIONS[0][1] - FRAME[1] / 2.0 - 96, STATIONS[2][1] + FRAME[1] / 2.0 + 20)

    # -- what may be read out of one of those pictures
    read.set_xlim(0, 100)
    read.set_ylim(0, 100)
    surface, extent = height_map(middle, [(c, h, r) for c, h, r in ARRANGEMENT])
    distance = HEIGHT - surface

    read.text(50, 99, "From each picture, three things and no more",
              ha="center", va="top", fontsize=LABEL_SIZE + 0.8, color=INK)

    read.imshow(
        distance, cmap="gray", vmin=160.0, vmax=HEIGHT + 20.0, origin="lower",
        extent=(3, 45, 63, 94.5), aspect="auto", zorder=2,
    )
    frame_box(read, 3, 63, 42, 31.5, ec=INK, lw=0.8)
    read.text(3, 61,
              "the grey picture, shaded from how\n"
              "far away each surface is: the nearer\n"
              "a surface the darker it is here, and\n"
              f"the bare table is {HEIGHT:.0f} mm from the lens",
              ha="left", va="top", fontsize=NOTE_SIZE, color=INK)

    # the same picture as the numbers behind it, across one glass's rim
    rows, columns = distance.shape
    tallest = ARRANGEMENT[int(np.argmax([g[1] for g in ARRANGEMENT]))]
    at_x = int(round((tallest[0][0] - middle[0] - extent[0]) / (extent[1] - extent[0]) * columns))
    at_y = int(round((tallest[0][1] - middle[1] - extent[2]) / (extent[3] - extent[2]) * rows))
    step_x, step_y = 7, 7
    patch = np.array([
        [distance[min(rows - 1, max(0, at_y + 14 - row * step_y)),
                  min(columns - 1, max(0, at_x - 16 + column * step_x))]
         for column in range(5)]
        for row in range(4)
    ])
    card(read, 55, 63, 42, 31.5, colour=INK, lw=0.8)
    for row in range(patch.shape[0]):
        for column in range(patch.shape[1]):
            read.text(
                58.8 + column * 7.6, 89.5 - row * 7.2, f"{patch[row, column]:.0f}",
                ha="center", va="center", fontsize=NOTE_SIZE - 0.6, color=INK,
            )
    read.text(57, 61,
              "the depth reading at every pixel, in\n"
              "millimetres from the lens. These are\n"
              "twenty real pixels, read across the\n"
              "rim of the tallest glass in the picture",
              ha="left", va="top", fontsize=NOTE_SIZE, color=INK)

    # the pose
    card(read, 3, 27, 94, 19, colour=INK, lw=0.8)
    read.add_patch(FancyArrowPatch((13, 34), (13, 42), arrowstyle="-|>", mutation_scale=8,
                                   color=INK, lw=1.0))
    read.add_patch(FancyArrowPatch((13, 34), (21, 34), arrowstyle="-|>", mutation_scale=8,
                                   color=INK, lw=1.0))
    read.plot(13, 34, marker="s", ms=6, color=GOOD)
    read.text(
        28, 36.5,
        "the camera's own pose: where the lens was and which way it\n"
        "pointed, which the arm knows from its joint encoders",
        ha="left", va="center", fontsize=NOTE_SIZE, color=INK,
    )

    # the fence
    card(read, 3, 2, 94, 21, colour=WARN, lw=1.2, ls=(0, (5, 3)))
    read.text(
        50, 19.5, "the simulator's record of what it spawned",
        ha="center", va="top", fontsize=LABEL_SIZE, color=WARN,
    )
    read.text(
        50, 13,
        "every glass's kind, size, place and true mask. It exists, and it is how the run is\n"
        "marked afterwards. An answer that reads it is not answering this problem.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=WARN,
    )
    save(figure, "what-goes-in.png")

# ------------------------------------------------------- 5. what must come out

def union_raster(circles, cells=520):
    """A boolean picture of a splayed silhouette, with the extent it covers."""
    x_from = min(float(c[0]) - r for c, r in circles)
    x_to = max(float(c[0]) + r for c, r in circles)
    y_from = min(float(c[1]) - r for c, r in circles)
    y_to = max(float(c[1]) + r for c, r in circles)
    extent = (x_from - 3, x_to + 3, y_from - 3, y_to + 3)
    down = max(60, int(cells * (extent[3] - extent[2]) / (extent[1] - extent[0])))
    gx, gy = np.meshgrid(
        np.linspace(extent[0], extent[1], cells), np.linspace(extent[2], extent[3], down)
    )
    out = np.zeros_like(gx, dtype=bool)
    for c, r in circles:
        out |= (gx - float(c[0])) ** 2 + (gy - float(c[1])) ** 2 <= r**2
    return out, extent, gx, gy

def covered_by(circles, gx, gy):
    """Which points of a grid fall inside a splayed silhouette."""
    out = np.zeros_like(gx, dtype=bool)
    for c, r in circles:
        out |= (gx - float(c[0])) ** 2 + (gy - float(c[1])) ** 2 <= r**2
    return out

def trace(axis, circles, colour, lw=1.2, ls=(0, (4, 3)), zorder=6):
    """Draw the edge of a splayed silhouette and nothing inside it."""
    mask, extent, _gx, _gy = union_raster(circles)
    axis.contour(
        mask.astype(float), levels=[0.5], colors=[colour], linewidths=lw, linestyles=[ls],
        extent=extent, zorder=zorder,
    )

def fit(axis, circles, points=(), pad=34.0, headroom=0.0):
    """Set a panel's limits from what was drawn, with room above for a note.

    A drawing made of splayed circles can land anywhere, because where it lands
    depends on which corner of the zone the station looks towards. Reading the
    limits back off the circles keeps the picture inside its panel without a
    margin of empty paper around it.
    """
    xs, ys = [], []
    for c, r in circles:
        xs += [float(c[0]) - r, float(c[0]) + r]
        ys += [float(c[1]) - r, float(c[1]) + r]
    for p in points:
        xs.append(float(p[0]))
        ys.append(float(p[1]))
    x_from, x_to = min(xs) - pad, max(xs) + pad
    y_from, y_to = min(ys) - pad, max(ys) + pad
    axis.set_xlim(x_from, x_to)
    axis.set_ylim(y_from, y_to + headroom * (y_to - y_from))

def what_must_come_out() -> None:
    """One record per glass, and why its place is a position and not a pose."""
    figure, (plan, records, why) = panels(13.8, 5.2, ratios=(0.92, 0.86, 0.95))

    shown = ARRANGEMENT[1], ARRANGEMENT[2], ARRANGEMENT[3]
    nadir = STATIONS[1]
    masks = [splay_circles(nadir, centre, height, rim) for centre, height, rim in shown]

    plan.set_aspect("equal")
    draw_zone(plan, label=False)
    plan.text((ZONE[0] + ZONE[1]) / 2.0, ZONE[3] + 10, "the glass zone",
              ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED)
    plan.plot(0, 0, marker="^", ms=11, color=INK)
    plan.text(-14, 18, "the arm's base", ha="left", va="bottom", fontsize=NOTE_SIZE, color=INK)
    plan.add_patch(FancyArrowPatch((0, 0), (150, 0), arrowstyle="-|>", mutation_scale=9,
                                   color=INK, lw=1.0))
    plan.add_patch(FancyArrowPatch((0, 0), (0, -150), arrowstyle="-|>", mutation_scale=9,
                                   color=INK, lw=1.0))
    plan.text(156, 0, "x", ha="left", va="center", fontsize=NOTE_SIZE, color=INK, bbox=MASK)
    plan.text(0, -156, "y", ha="center", va="top", fontsize=NOTE_SIZE, color=INK, bbox=MASK)
    for index, (centre, _height, rim) in enumerate(shown):
        plan.add_patch(Circle(centre, rim / 2.0, fc=GLASS, alpha=0.28, ec=GLASS, lw=1.4))
        plan.plot(*centre, marker="+", ms=7, mew=1.4, color=GLASS)
        plan.text(centre[0], centre[1] + rim / 2.0 + 10, f"glass {index + 1}",
                  ha="center", va="bottom", fontsize=NOTE_SIZE, color=GLASS, bbox=MASK)
    # how one of those places is measured, drawn out from the base
    measured = shown[1][0]
    plan.plot([0, measured[0], measured[0]], [0, 0, measured[1]],
              color=MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)
    plan.text(measured[0] / 2.0, 8, f"x {measured[0]:.0f} mm", ha="center", va="bottom",
              fontsize=NOTE_SIZE, color=MUTED)
    plan.text(measured[0] + 10, measured[1] / 2.0, f"y {measured[1]:.0f} mm", ha="left",
              va="center", fontsize=NOTE_SIZE, color=MUTED, bbox=MASK)
    plan.set_title("Where the glasses stand", fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    plan.set_xlim(-70, ZONE[1] + 40)
    plan.set_ylim(ZONE[2] - 40, 60)

    # -- the records themselves
    records.set_xlim(0, 100)
    records.set_ylim(0, 100)
    records.set_aspect("equal")
    records.set_title("What must come out, once per glass",
                      fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    for index, ((centre, _height, rim), mask) in enumerate(zip(shown, masks)):
        bottom = 70 - index * 30
        card(records, 2, bottom, 96, 26, colour=MUTED, lw=1.0)
        scale = 17.0 / splay_width(mask)
        middle = np.mean([c for c, _r in mask], axis=0)
        for c, r in mask:
            at = (15 + (float(c[0]) - middle[0]) * scale,
                  bottom + 13.5 + (float(c[1]) - middle[1]) * scale)
            records.add_patch(Circle(at, r * scale, fc=GLASS, alpha=0.26, ec="none"))
        records.text(15, bottom + 1.5, "its mask", ha="center", va="bottom",
                     fontsize=NOTE_SIZE - 0.4, color=GLASS)
        records.text(31, bottom + 21.5, f"glass {index + 1}", ha="left", va="top",
                     fontsize=LABEL_SIZE, color=INK)
        records.text(
            31, bottom + 14.5,
            f"place: x {centre[0]:.0f} mm, y {centre[1]:.0f} mm\n"
            f"footprint about {rim:.0f} mm across",
            ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED,
        )
    records.text(
        2, 6, "The place is measured from the arm's base. The\n"
              "mask says which pixels of which picture are that\n"
              "glass and not another.",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )

    # -- why a place and not a full pose
    why.set_xlim(0, 100)
    why.set_ylim(0, 100)
    why.set_aspect("equal")
    why.set_title("Why a place and not a pose", fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    scale = 0.165
    base_x, base_y = 22.0, 46.0
    h, r = outline_mm("tapered_glass", tall=True)
    why.fill_betweenx(base_y + h * scale, base_x - r * scale, base_x + r * scale,
                      facecolor=GLASS, alpha=0.28, lw=0.0)
    why.plot(base_x + r * scale, base_y + h * scale, color=GLASS, lw=1.4)
    why.plot(base_x - r * scale, base_y + h * scale, color=GLASS, lw=1.4)
    why.plot([4, 46], [base_y, base_y], color=INK, lw=1.2)
    why.text(4, base_y - 2.5, "a flat table", ha="left", va="top",
             fontsize=NOTE_SIZE, color=INK)
    why.plot([base_x, base_x], [base_y - 4, base_y + h[-1] * scale + 7],
             color=GOOD, lw=1.1, ls=(0, (4, 3)))
    why.plot(base_x, base_y, marker="x", ms=9, mew=1.8, color=GOOD)
    why.text(
        50, 92,
        "The glass stands upright on a flat table,\n"
        "so its axis is vertical. Nothing has to\n"
        "work out which way the axis points.",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    why.annotate(
        "Where that axis meets the table is\nthe whole of what must be found.",
        xy=(base_x + 1, base_y + 1), xytext=(50, 66),
        ha="left", va="top", fontsize=NOTE_SIZE, color=GOOD,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=8, color=GOOD, lw=0.9),
    )
    why.text(
        4, 34,
        "A glass is the same shape from every side, so there is no turn to find:",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    for index, turn in enumerate((0, 55, 130)):
        cx = 20.0 + index * 30.0
        why.add_patch(Circle((cx, 16), 9.5, fc=GLASS, alpha=0.26, ec=GLASS, lw=1.2))
        why.plot(cx, 16, marker="+", ms=6, mew=1.2, color=GLASS)
        why.text(cx, 3.5, f"turned {turn}°", ha="center", va="bottom",
                 fontsize=NOTE_SIZE, color=MUTED)
    save(figure, "what-must-come-out.png")

# ------------------------------------------- 6. a glass missing altogether

# The tallest tapered glass hides the shortest one only where the throw is
# largest, which is as far out from a station as the zone and that station's own
# picture both allow. These two centres are the furthest apart that splay_covers
# will still call a complete cover, found by sweeping the separation downwards;
# the script finds them again every run and refuses to draw anything else.
HIDING_KIND = "tapered_glass"
def main() -> None:
    the_arrangement()
    the_kind_this_book_uses()
    the_widest_range_of_sizes()
    what_goes_in()
    what_must_come_out()

if __name__ == "__main__":
    main()
