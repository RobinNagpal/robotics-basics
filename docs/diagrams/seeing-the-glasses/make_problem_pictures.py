"""The six pictures for docs/08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md.

That document states the problem: four to six glasses of one kind on the table,
what an answer is given, what it must hand back, and the two difficulties that
live inside a single station's pictures. These six pictures draw those
statements.

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

The two difficulty pictures are drawn with ``splay_circles``, ``splay_covers``
and ``splay_width`` from diagram_style, which model what a camera looking
straight down does to a standing glass: a slice at height z is imaged as though
the scene were scaled about the point directly below the camera by H / (H - z).
Nothing in those two pictures is placed by eye. The arrangement in
``a-glass-missing-altogether`` is asserted with ``splay_covers`` before it is
drawn, and the script stops if the assertion fails.

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


def waisted(r) -> bool:
    """Does this radius profile narrow and then widen again?

    True for the two kinds with a stem and false for the two tumblers, which
    only ever widen going up. The script checks this rather than trusting it,
    because the whole claim about the harder pair rests on it.
    """
    rising = np.diff(np.asarray(r))
    return bool(np.any(rising[:-1] < -0.1) and np.any(rising[1:] > 0.1)
                and np.argmax(np.asarray(r)) > int(np.argmin(np.asarray(r)[1:]) + 1))


def measured_coverage():
    """The median per cent of each glass the mask covered, per kind.

    Read out of the two solutions' own results.json rather than typed in: the
    one built from rules written by hand, and the one fitted on this cell's own
    pictures. These are the numbers behind the claim that the two kinds with a
    stem are the harder pair for the first and not for the second.
    """
    import json

    folder = ROOT / "code" / "src" / "08_seeing-the-glasses"
    out = {}
    for label, where in (("rules", "01-rules-on-the-table"), ("fitted", "02-train-from-scratch")):
        path = folder / where / "results.json"
        if not path.exists():
            raise SystemExit(f"no marking to read the per-kind coverage from: {path}")
        by_kind = json.loads(path.read_text())["mask"]["by_kind"]
        out[label] = {kind: by_kind[kind]["covered_median"] for kind in KINDS}
    return out


# ------------------------------------------------------- 1. what is on the table

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


def silhouette_rasters(kind: str, out: float, cells: int = 460):
    """Where a glass of ``kind`` lands in an overhead picture, as two rasters.

    The glass stands ``out`` millimetres from the point below the camera. The
    first raster is its whole silhouette. The second is the part of that
    silhouette outside the one thrown circle of its widest slice, which is what
    an outline that follows only the widest part of the glass leaves behind.
    Returns the two rasters, the extent they cover in millimetres, the thrown
    widest circle, and how wide the glass really is.
    """
    height, radius = outline_mm(kind, tall=True)
    circles = splay_outline((0.0, 0.0), (out, 0.0), height, radius)
    broad = int(np.argmax([r for _c, r in circles]))
    x_from = min(c[0] - r for c, r in circles)
    x_to = max(c[0] + r for c, r in circles)
    reach = max(r for _c, r in circles)
    extent = (x_from - 4, x_to + 4, -reach - 4, reach + 4)
    down = max(40, int(cells * (reach + 4) * 2 / (extent[1] - extent[0])))
    gx, gy = np.meshgrid(
        np.linspace(extent[0], extent[1], cells), np.linspace(extent[2], extent[3], down)
    )
    whole = np.zeros_like(gx, dtype=bool)
    for c, r in circles:
        whole |= (gx - c[0]) ** 2 + (gy - c[1]) ** 2 <= r**2
    wide_c, wide_r = circles[broad]
    blob = (gx - wide_c[0]) ** 2 + (gy - wide_c[1]) ** 2 <= wide_r**2
    return whole, whole & ~blob, extent, (float(wide_c[0]), float(wide_r)), float(radius.max())


def shade(axis, mask, extent, colour, alpha, shift=0.0, zorder=3):
    """Paint a boolean raster in one colour, leaving everything else clear."""
    from matplotlib.colors import to_rgb

    rgba = np.zeros(mask.shape + (4,))
    rgba[..., :3] = to_rgb(colour)
    rgba[..., 3] = np.where(mask, alpha, 0.0)
    axis.imshow(
        rgba, origin="lower", zorder=zorder, interpolation="nearest",
        extent=(extent[0] + shift, extent[1] + shift, extent[2], extent[3]),
    )


def what_is_on_the_table() -> None:
    """Four to six glasses of one kind, and why two of the four kinds are harder."""
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

    out = 100.0
    rasters = {kind: silhouette_rasters(kind, out) for kind in KINDS}
    pitch = max(e[1] - e[0] for _w, _l, e, _b, _r in rasters.values()) + 56.0
    tallest = max(e[3] for _w, _l, e, _b, _r in rasters.values())

    figure = plt.figure(figsize=(12.8, 8.2))
    figure.patch.set_facecolor(PAPER)
    grid = figure.add_gridspec(
        2, 2, height_ratios=[1.0, 0.94], width_ratios=[0.50, 1.0], hspace=0.30, wspace=0.06
    )
    plan = figure.add_subplot(grid[0, 0])
    side = figure.add_subplot(grid[0, 1])
    top = figure.add_subplot(grid[1, :])
    for axis in (plan, side, top):
        axis.set_facecolor(PAPER)
        bare(axis)

    # -- the arrangement, in plan
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
        f"{gap:.0f} mm, the guaranteed smallest gap\n"
        f"between centres. At the widest rim the kind\n"
        f"allows that still leaves {SEPARATION - rim_high:.0f} mm of bare table.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    plan.set_title(
        "Five glasses of one kind, every centre inside the zone",
        fontsize=LABEL_SIZE + 0.6, color=INK, pad=10,
    )
    plan.set_xlim(ZONE[0] - 50, ZONE[1] + 50)
    plan.set_ylim(ZONE[2] - 150, ZONE[3] + 54)

    # -- the four kinds, in side elevation at their tallest
    side.set_aspect("equal")
    pitch_side = 178.0
    for index, kind in enumerate(KINDS):
        x = index * pitch_side
        colour = WARN if "stemmed" in kind else GLASS
        side_glass(side, x, kind, tall=True, colour=colour, alpha=0.26)
        low, high = span(kind, "height")
        wide_low, wide_high = span(kind, widest(kind))
        part = "rim" if widest(kind) == "rim_diameter" else "bowl"
        lines = [f"{low:.0f} to {high:.0f} mm tall", f"{part} {wide_low:.0f} to {wide_high:.0f} mm"]
        if "stem_diameter" in KIND_RANGES[kind]:
            stem_low, stem_high = span(kind, "stem_diameter")
            lines.append(f"stem {stem_low:.0f} to {stem_high:.0f} mm")
        side.text(x, -16, PLAIN[kind], ha="center", va="top", fontsize=LABEL_SIZE, color=colour)
        side.text(x, -44, "\n".join(lines), ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED)
    side.plot([-80, 3 * pitch_side + 80], [0, 0], color=INK, lw=1.1)
    side.text(-80, 5, "the table", ha="left", va="bottom", fontsize=NOTE_SIZE, color=INK)
    side.set_title(
        "The cell's four kinds, each at the tallest its range allows",
        fontsize=LABEL_SIZE + 0.6, color=INK, pad=10,
    )
    side.set_xlim(-95, 3 * pitch_side + 95)
    side.set_ylim(-128, 244)

    # -- the same four from straight above
    top.set_aspect("equal")
    coverage = measured_coverage()
    for index, kind in enumerate(KINDS):
        whole, lost, extent, (wide_x, wide_r), _true_r = rasters[kind]
        shift = index * pitch - extent[0]
        stemmed = "stemmed" in kind
        _h, r = outline_mm(kind, tall=True)
        if waisted(r) != stemmed:
            raise SystemExit(f"{kind} does not have the shape this picture claims for it")
        shade(top, whole, extent, GLASS, 0.22, shift=shift, zorder=3)
        shade(top, lost, extent, WARN if stemmed else MUTED, 0.60, shift=shift, zorder=4)
        top.add_patch(Circle((wide_x + shift, 0.0), wide_r, fill=False, ec=INK, lw=1.0,
                             ls=(0, (4, 3)), zorder=5))
        top.plot(out + shift, 0.0, marker="+", ms=7, mew=1.3, color=INK, zorder=6)
        colour = WARN if stemmed else GLASS
        top.text(out + shift, -tallest - 14, PLAIN[kind], ha="center", va="top",
                 fontsize=LABEL_SIZE, color=colour)
        top.text(
            out + shift, -tallest - 38,
            f"rules cover {coverage['rules'][kind]:.1f}%\n"
            f"fitted cover {coverage['fitted'][kind]:.1f}%",
            ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED,
        )
    top.text(
        0.5 * pitch, tallest + 104,
        "The dashed circle is the widest slice of\n"
        "the glass, thrown outwards. On a tumbler\n"
        "what it leaves out is the base, which is\n"
        "nearly as wide as the rim and lies against it.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    top.text(
        2.5 * pitch, tallest + 104,
        "On a glass with a stem the bowl is thrown\n"
        "far enough to swallow the stem. What is\n"
        "left out is the foot, and the sliver of stem\n"
        "beside it. These two are the harder pair.",
        ha="center", va="top", fontsize=NOTE_SIZE, color=WARN,
    )
    top.text(
        -60, 0, f"the point below\nthe camera is\n{out:.0f} mm this way",
        ha="right", va="center", fontsize=NOTE_SIZE, color=MUTED,
    )
    top.add_patch(FancyArrowPatch((-52, 0), (14, 0), arrowstyle="-|>", mutation_scale=9,
                                  color=MUTED, lw=1.0))
    top.set_title(
        "The same four kinds from straight above, each standing "
        f"{out:.0f} mm from the point below the camera",
        fontsize=LABEL_SIZE + 0.6, color=INK, pad=10,
    )
    last = rasters[KINDS[-1]][2]
    top.set_xlim(-250, 3 * pitch + (last[1] - last[0]) + 24)
    top.set_ylim(-tallest - 118, tallest + 120)

    save(figure, "four-to-six-of-one-kind.png")


# ---------------------------------------------- 2. the widest range of sizes


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


# ------------------------------------------------------------- 3. what goes in


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


# ------------------------------------------------------- 4. what must come out


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


# ------------------------------------------- 5. a glass missing altogether

# The tallest tapered glass hides the shortest one only where the throw is
# largest, which is as far out from a station as the zone and that station's own
# picture both allow. These two centres are the furthest apart that splay_covers
# will still call a complete cover, found by sweeping the separation downwards;
# the script finds them again every run and refuses to draw anything else.
HIDING_KIND = "tapered_glass"


def a_glass_missing_altogether() -> None:
    """A tall glass whose outline covers a short neighbour completely."""
    separation, nadir, tall, short = hiding_separation(HIDING_KIND)
    tall_h = span(HIDING_KIND, "height")[1]
    tall_w = span(HIDING_KIND, "rim_diameter")[1]
    short_h = span(HIDING_KIND, "height")[0]
    short_w = span(HIDING_KIND, "rim_diameter")[0]
    big = splay_circles(nadir, tall, tall_h, tall_w)
    small = splay_circles(nadir, short, short_h, short_w)
    if not splay_covers(big, small):
        raise SystemExit("the arrangement this picture is about does not actually hide anything")
    for name, point in (("the tall glass", tall), ("the short glass", short)):
        if not in_zone(point) or not in_frame(point, nadir):
            raise SystemExit(f"{name} stands where no station could have seen it")

    # The same short glass at the guaranteed separation. The tall glass then has
    # to stand further in, where it is thrown less far, and no longer reaches
    # over its neighbour.
    direction = (np.asarray(short) - np.asarray(nadir))
    direction = direction / float(np.linalg.norm(direction))
    pulled = np.asarray(short) - SEPARATION * direction
    pulled_big = splay_circles(nadir, pulled, tall_h, tall_w)
    if splay_covers(pulled_big, small):
        raise SystemExit("the comparison panel is supposed to show a glass that is not hidden")
    # how far out along the line each silhouette reaches, and so how much of the
    # short glass is left outside the tall one
    def along(circles):
        return max(float(np.dot(c, direction)) + r for c, r in circles)

    survives = along(small) - along(pulled_big)

    figure, (table, hidden, spared) = panels(13.4, 5.4, ratios=(0.92, 1.0, 1.0))

    # -- on the table
    table.set_aspect("equal")
    draw_zone(table, label=False)
    table.text((ZONE[0] + ZONE[1]) / 2.0, ZONE[3] + 10, "the glass zone",
               ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED)
    table.plot(*nadir, marker="+", ms=10, mew=1.4, color=INK, zorder=7)
    table.text(nadir[0] + 12, nadir[1] + 8, "the point below\nthe camera",
               ha="left", va="bottom", fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=7)
    table.plot([nadir[0], short[0]], [nadir[1], short[1]], color=MUTED, lw=0.9, ls=(0, (4, 3)))
    for point, width, label, colour in (
        (tall, tall_w, f"the tallest the kind\nallows, {tall_h:.0f} mm", GLASS),
        (short, short_w, f"the shortest,\n{short_h:.0f} mm", WARN),
    ):
        table.add_patch(Circle(point, width / 2.0, fc=colour, alpha=0.28, ec=colour, lw=1.4))
        table.plot(*point, marker="+", ms=7, mew=1.4, color=colour)
        table.text(point[0] - width / 2.0 - 12, point[1], label, ha="right", va="center",
                   fontsize=NOTE_SIZE, color=colour, bbox=MASK, zorder=7)
    double_arrow(table, tuple(tall), tuple(short))
    table.text(
        (tall[0] + short[0]) / 2.0 + 12, (tall[1] + short[1]) / 2.0,
        f"{separation:.0f} mm\nbetween centres",
        ha="left", va="center", fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=7,
    )
    table.text(
        ZONE[0], ZONE[2] - 16,
        "both centres inside the glass zone, and both\ninside this station's own picture",
        ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    table.set_title("On the table", fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    table.set_xlim(ZONE[0] - 160, ZONE[1] + 40)
    table.set_ylim(ZONE[2] - 76, ZONE[3] + 34)

    # -- in the picture, twice
    for axis, shapes, title in (
        (hidden, (big, small), f"In the picture, {separation:.0f} mm apart"),
        (spared, (pulled_big, small), f"In the picture, {SEPARATION:.0f} mm apart"),
    ):
        axis.set_aspect("equal")
        axis.plot(0, 0, marker="+", ms=10, mew=1.4, color=INK, zorder=7)
        splay_patch(axis, shapes[0], colour=GLASS, alpha=0.28, zorder=3)
        # what is left of the short glass once the tall one is drawn over it
        mask, extent, gx, gy = union_raster(shapes[1])
        shade(axis, mask & ~covered_by(shapes[0], gx, gy), extent, WARN, 0.75, zorder=5)
        trace(axis, shapes[1], WARN)
        axis.set_title(title, fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
        fit(axis, list(big) + list(small) + list(pulled_big), points=[(0.0, 0.0)],
            pad=40.0, headroom=0.34)
        axis.text(0.0, 6.0, "the point below\nthe camera", ha="center", va="bottom",
                  fontsize=NOTE_SIZE, color=INK)

    hidden.text(
        0.02, 0.99,
        "The tall glass's rim is nearer the lens than the table is,\n"
        "so its outline is thrown outwards and lands over its\n"
        "neighbour. The short glass is in there, and not one pixel\n"
        "of the picture is its own: the dashed line is where it stands,\n"
        "and nothing inside it is left over. There is no bad number to\n"
        "find and no check that fails.",
        transform=hidden.transAxes, ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    spared.text(
        0.02, 0.99,
        f"The layout rule keeps every pair of centres at least\n"
        f"{SEPARATION:.0f} mm apart. The tall glass then stands further in,\n"
        f"where it is thrown less far, and {survives:.0f} mm of the short glass\n"
        f"is left outside it, shaded here. A complete cover needs\n"
        f"{separation:.0f} mm, so in a spawned arrangement this shows up as\n"
        f"a merge rather than as a loss.",
        transform=spared.transAxes, ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    save(figure, "a-glass-missing-altogether.png")


# -------------------------------------- 6. merged though they stand apart


def merged_though_they_stand_apart() -> None:
    """Two glasses with bare table between them, and one shape in the picture."""
    nadir = STATIONS[1]
    corner = (ZONE[1], ZONE[3])
    reach = math.dist(nadir, corner)
    direction = np.array([corner[0] - nadir[0], corner[1] - nadir[1]]) / reach
    near = np.asarray(nadir) + 70.0 * direction
    far = np.asarray(nadir) + (70.0 + SEPARATION) * direction
    near_h, near_w = 225.0, 102.0
    far_h, far_w = 208.0, 96.0
    for point in (near, far):
        if not in_zone(point) or not in_frame(point, nadir):
            raise SystemExit("this picture stands a glass where no station could have seen it")
    first = splay_circles(nadir, near, near_h, near_w)
    second = splay_circles(nadir, far, far_h, far_w)
    if not connected(first, second):
        raise SystemExit("the two silhouettes this picture is about do not actually meet")
    bare_table = SEPARATION - (near_w + far_w) / 2.0

    figure, (table, shot, depth) = panels(13.4, 4.8, ratios=(0.95, 1.0, 0.92))

    table.set_aspect("equal")
    draw_zone(table, label=False)
    table.plot(*nadir, marker="+", ms=10, mew=1.4, color=INK, zorder=7)
    table.text(nadir[0] - 12, nadir[1], "the point below\nthe camera",
               ha="right", va="center", fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=7)
    for point, width, colour in ((near, near_w, GLASS), (far, far_w, GLASS)):
        table.add_patch(Circle(point, width / 2.0, fc=colour, alpha=0.28, ec=colour, lw=1.4))
        table.plot(*point, marker="+", ms=7, mew=1.4, color=colour)
    inner = near + direction * near_w / 2.0
    outer = far - direction * far_w / 2.0
    double_arrow(table, tuple(inner), tuple(outer), colour=GOOD)
    table.text(
        (inner[0] + outer[0]) / 2.0 + 16, (inner[1] + outer[1]) / 2.0 - 26,
        f"{bare_table:.0f} mm of bare table\nbetween the two rims",
        ha="left", va="top", fontsize=NOTE_SIZE, color=GOOD, bbox=MASK, zorder=7,
    )
    table.text(
        ZONE[0], ZONE[2] - 18,
        f"centres {SEPARATION:.0f} mm apart, the smallest the\nlayout rule allows",
        ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )
    table.set_title("On the table: a clear gap", fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    table.set_xlim(ZONE[0] - 40, ZONE[1] + 70)
    table.set_ylim(ZONE[2] - 86, ZONE[3] + 30)

    shot.set_aspect("equal")
    shot.plot(0, 0, marker="+", ms=10, mew=1.4, color=INK)
    shot.text(-12, -6, "the point below\nthe camera", ha="right", va="top",
              fontsize=NOTE_SIZE, color=INK)
    splay_patch(shot, first, colour=GLASS, alpha=0.26, zorder=3)
    splay_patch(shot, second, colour=GLASS, alpha=0.26, zorder=3)
    shot.annotate(
        "no gap anywhere along here: each glass\ncovers more of the picture than its\n"
        "footprint deserves, and the two smears meet",
        xy=(float(first[-1][0][0]) + 10, float(first[-1][0][1]) + 10), xytext=(-44, 486),
        ha="left", va="top", fontsize=NOTE_SIZE, color=WARN,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=8, color=WARN, lw=0.9),
    )
    line = np.array([direction * t for t in np.linspace(0.0, 520.0, 2)])
    shot.plot(line[:, 0], line[:, 1], color=INK, lw=0.8, ls=(0, (4, 3)), zorder=6)
    shot.set_title("In the picture: one connected shape",
                   fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    shot.set_xlim(-50, 450)
    shot.set_ylim(-60, 500)

    # the depth reading along the dashed line, which still separates the two
    steps = np.linspace(0.0, 520.0, 700)
    surface = np.zeros_like(steps)
    for circles, h in ((first, near_h), (second, far_h)):
        for index, (c, radius) in enumerate(circles):
            z = h * index / (len(circles) - 1)
            points = np.outer(steps, direction)
            inside = np.hypot(points[:, 0] - c[0], points[:, 1] - c[1]) <= radius
            surface = np.where(inside, np.maximum(surface, z), surface)
    reading = HEIGHT - surface
    depth.plot(steps, reading, color=GOOD, lw=1.6)
    depth.axhline(HEIGHT, color=MUTED, lw=0.9, ls=(0, (4, 3)))
    depth.text(14, HEIGHT - 4, f"the bare table, {HEIGHT:.0f} mm from the lens",
               ha="left", va="bottom", fontsize=NOTE_SIZE, color=MUTED, bbox=MASK)
    half = len(steps) // 2
    first = int(np.argmin(reading[:half]))
    second = half + int(np.argmin(reading[half:]))
    valley = first + int(np.argmax(reading[first:second]))
    depth.annotate(
        "between the two glasses the depth climbs\nback towards the table, so the readings\n"
        "still say where one ends and the next begins",
        xy=(steps[valley], reading[valley]), xytext=(steps[valley] + 18, reading[valley] + 46),
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=8, color=INK, lw=0.9),
    )
    depth.set_xlim(0, 520)
    depth.set_ylim(470, 190)
    depth.set_xticks([0, 130, 260, 390, 520])
    depth.set_yticks([200, 250, 300, 350, 400, 450])
    depth.tick_params(labelsize=NOTE_SIZE - 0.4, colors=MUTED, length=3)
    for side in ("left", "bottom"):
        depth.spines[side].set_visible(True)
        depth.spines[side].set_color(MUTED)
    depth.set_xlabel("millimetres along the dashed line", fontsize=NOTE_SIZE, color=MUTED)
    depth.set_ylabel("depth reading, millimetres from the lens", fontsize=NOTE_SIZE, color=MUTED)
    depth.set_title("The depth readings still tell them apart",
                    fontsize=LABEL_SIZE + 0.8, color=INK, pad=8)
    save(figure, "merged-though-they-stand-apart.png")


def main() -> None:
    what_is_on_the_table()
    the_widest_range_of_sizes()
    what_goes_in()
    what_must_come_out()
    a_glass_missing_altogether()
    merged_though_they_stand_apart()


if __name__ == "__main__":
    main()
