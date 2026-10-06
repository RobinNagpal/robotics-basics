"""Six pictures of the two difficulties in docs/08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md.

That document names two difficulties, and both come from the same thing: what a
camera looking straight down does to a glass standing on a table. A glass is
nearer the lens at its rim than the table is, so its outline is thrown outwards,
away from the point directly below the camera. Each difficulty is drawn here on
one arrangement of three glasses, in three pictures:

  * ``<set>-on-the-table.png`` — where the three glasses really stand, in plan;
  * ``<set>-from-the-side.png`` — the same three seen edge on, with the camera
    above them and the line of sight drawn, which is where the cause is visible;
  * ``<set>-what-the-camera-sees.png`` — the picture that comes back.

One picture shows one thing, so each of the six is a single panel. The three
pictures of a set hold the same three glasses, numbered the same way, in the
same places, so a reader can move between them.

Nothing is placed by eye. The arrangements are built from the cell's own
constants, and both claims are tested with ``splay_covers`` from diagram_style
before anything is drawn:

  * the hidden set asserts that glass 1's silhouette covers glass 2's
    completely;
  * the merge set asserts that neither silhouette covers the other, and that
    the two nevertheless touch, which is what makes it a merge and not a loss.

The script stops without writing if either assertion fails.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_difficulty_pictures.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from diagram_style import (  # noqa: E402
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    WARN,
    bare,
    save,
    splay_circles,
    splay_covers,
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
# Millimetres everywhere, because every label in these pictures is in
# millimetres. The cell's own constants are in metres.

MM = 1000.0
KIND = "tapered_glass"

ZONE = tuple(v * MM for v in GLASS_ZONE)          # x from, x to, y from, y to
ZONE_W = ZONE[1] - ZONE[0]
ZONE_D = ZONE[3] - ZONE[2]
SEPARATION = MIN_SEPARATION * MM                  # the guaranteed smallest gap
HEIGHT = SURVEY_HEIGHT * MM                       # how far up the camera looks from

# The wrist camera's frame, worked out from its own lens the way bench/data.py
# frame() works it out. bench/ cannot be imported here because its modules
# import each other by bare name, so the three numbers are repeated.
PIXELS_ACROSS, PIXELS_DOWN = 320, 240
HORIZONTAL_FOV = 1.047
FOCAL = (PIXELS_ACROSS / 2.0) / math.tan(HORIZONTAL_FOV / 2.0)
FRAME = (HEIGHT * PIXELS_ACROSS / FOCAL, HEIGHT * PIXELS_DOWN / FOCAL)
SHARED = (
    FRAME[0] - GRIPPER_MAX_OPENING * MM,
    FRAME[1] - SURVEY_BASELINE * MM - GRIPPER_MAX_OPENING * MM,
)
STATIONS = [
    (float(s[0]) * MM, float(s[1]) * MM)
    for s in survey_stations(GLASS_ZONE, tuple(v / MM for v in SHARED))
]

# The base of a tapered glass, as a fraction of its rim. shapes.tapered and
# splay_circles both default to this, so the side view and the camera view of
# one glass are the same solid.
BASE_FRACTION = 0.45

# Where the camera stands for both sets, and the line the three glasses stand
# on. The middle survey station, looking at the far corner of the glass zone:
# the outward throw grows with distance from the point below the camera, so the
# corner is where there is most of it to see.
NADIR = STATIONS[1]
CORNER = (ZONE[1], ZONE[3])
REACH = math.dist(NADIR, CORNER)
DIRECTION = np.array([CORNER[0] - NADIR[0], CORNER[1] - NADIR[1]]) / REACH
SIDEWAYS = np.array([DIRECTION[1], -DIRECTION[0]])   # across the line, to its right

MASK = dict(facecolor=PAPER, edgecolor="none", pad=1.4)
TITLE = LABEL_SIZE + 0.8


# ---------------------------------------------------------------- the scenes
#
# A glass is written down as how far along the line it stands, measured from the
# point below the camera, together with its height and the width of its rim. A
# negative distance is on the near side of that point, which is the other half
# of the same straight line.


class Glass:
    """One glass of the tapered kind, standing on the line out from the camera."""

    def __init__(self, number: int, out: float, height: float, rim: float, colour: str):
        self.number = number
        self.out = out
        self.height = height
        self.rim = rim
        self.colour = colour
        self.centre = np.asarray(NADIR) + out * DIRECTION
        self.circles = splay_circles(NADIR, self.centre, height, rim, BASE_FRACTION)

    @property
    def profile(self):
        """Height above the table and radius, in millimetres, from the cell's own code."""
        line = build(KIND, height=self.height / MM, rim_diameter=self.rim / MM,
                     base_fraction=BASE_FRACTION)
        return np.asarray(line.height) * MM, np.asarray(line.radius) * MM

    def lands(self) -> tuple[float, float]:
        """How far out along the line this glass's silhouette reaches, from and to."""
        along = [(float(np.dot(c, DIRECTION)) - r, float(np.dot(c, DIRECTION)) + r)
                 for c, r in self.circles]
        return min(a for a, _b in along), max(b for _a, b in along)


# Difficulty 1. Glass 1 is near the tall end of the kind's range and glass 2
# near the short end, standing beyond it on the same line. 90 mm between their
# centres is six tenths of the guaranteed gap, which is in the middle of what a
# crowded arrangement produces: spawn.py stands a crowded pair at 0.3 to 0.7 of
# the guarantee. Glass 3 stands on the near side of the camera, far enough from
# both to behave normally.
CROWDED = 0.6 * SEPARATION
HIDDEN = (
    Glass(1, 135.0, 225.0, 102.0, GLASS),
    Glass(2, 135.0 + CROWDED, 95.0, 67.0, WARN),
    Glass(3, -160.0, 208.0, 96.0, GLASS),
)

# Difficulty 2. Glasses 1 and 2 stand exactly the guaranteed gap apart, so there
# is bare table between their rims, and both are near the tall end of the range.
# Glass 3 again stands clear on the near side.
MERGE = (
    Glass(1, 70.0, 225.0, 102.0, GLASS),
    Glass(2, 70.0 + SEPARATION, 208.0, 96.0, GLASS),
    Glass(3, -170.0, 160.0, 88.0, GLASS),
)


def check(scene, crowded_pair=None) -> None:
    """Every glass is a glass this cell could have spawned, where it could be seen."""
    for glass in scene:
        low, high = (v * MM for v in KIND_RANGES[KIND]["height"])
        rim_low, rim_high = (v * MM for v in KIND_RANGES[KIND]["rim_diameter"])
        if not low <= glass.height <= high or not rim_low <= glass.rim <= rim_high:
            raise SystemExit(
                f"glass {glass.number} is {glass.height:.0f} mm tall and {glass.rim:.0f} mm "
                f"across, which the tapered kind's range does not allow"
            )
        x, y = glass.centre
        if not (ZONE[0] <= x <= ZONE[1] and ZONE[2] <= y <= ZONE[3]):
            raise SystemExit(f"glass {glass.number} stands outside the glass zone")
        if abs(x - NADIR[0]) > FRAME[0] / 2.0 or abs(y - NADIR[1]) > FRAME[1] / 2.0:
            raise SystemExit(f"glass {glass.number} is outside this station's own picture")
    for index, first in enumerate(scene):
        for second in scene[index + 1:]:
            gap = math.dist(first.centre, second.centre)
            pair = (first.number, second.number)
            if pair == crowded_pair:
                if gap >= SEPARATION:
                    raise SystemExit(f"glasses {pair} are not crowded: {gap:.0f} mm apart")
            elif gap < SEPARATION - 0.05:
                raise SystemExit(f"glasses {pair} stand {gap:.0f} mm apart, inside the guarantee")


def touching(first: Glass, second: Glass) -> bool:
    """Do two splayed silhouettes form one shape? True if any two circles meet."""
    return any(
        math.hypot(*(c1 - c2)) <= r1 + r2
        for c1, r1 in first.circles
        for c2, r2 in second.circles
    )


def cover_limit(tall: Glass, short: Glass, tolerance: float = 0.5) -> float:
    """How far apart these two centres may stand with the cover still complete.

    Reported rather than drawn. The tall glass keeps its place and the short one
    is moved further out along the line, because moving it out both shrinks the
    tall glass's reach over it and grows its own. splay_covers answers each
    time; the number is the helper's, not arithmetic done here.
    """
    low, high = 1.0, REACH
    while high - low > tolerance:
        middle = (low + high) / 2.0
        moved = Glass(short.number, tall.out + middle, short.height, short.rim, short.colour)
        if splay_covers(tall.circles, moved.circles):
            low = middle
        else:
            high = middle
    return low


# ------------------------------------------------------------- the machinery


def panel(width: float, height: float):
    """One bare panel on white paper. Every picture here is a single panel."""
    figure, axis = plt.subplots(1, 1, figsize=(width, height))
    figure.patch.set_facecolor(PAPER)
    axis.set_facecolor(PAPER)
    bare(axis)
    axis.set_aspect("equal")
    return figure, axis


def draw_zone(axis) -> None:
    """The glass zone in plan, with its size said once, below it."""
    axis.add_patch(
        Rectangle((ZONE[0], ZONE[2]), ZONE_W, ZONE_D, fill=False, ec=MUTED, lw=1.2,
                  ls=(0, (6, 4)))
    )
    axis.text(
        ZONE[0], ZONE[2] - 12, f"the glass zone, {ZONE_W:.0f} by {ZONE_D:.0f} mm",
        ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED,
    )


def draw_nadir(axis, point=(0.0, 0.0)) -> None:
    axis.plot(*point, marker="+", ms=11, mew=1.5, color=INK, zorder=8)


def footprint(axis, glass: Glass) -> None:
    """Where one glass really stands, as the circle its rim encloses."""
    axis.add_patch(Circle(tuple(glass.centre), glass.rim / 2.0, fc=glass.colour, alpha=0.26,
                          ec=glass.colour, lw=1.4, zorder=4))
    axis.plot(*glass.centre, marker="+", ms=7, mew=1.4, color=glass.colour, zorder=5)
    axis.text(*glass.centre, str(glass.number), ha="center", va="center", fontsize=LABEL_SIZE,
              color=INK, zorder=7, bbox=MASK)


def arrow(axis, start, end, colour=INK, lw=1.1) -> None:
    axis.add_patch(
        FancyArrowPatch(tuple(start), tuple(end), arrowstyle="<|-|>", mutation_scale=9,
                        color=colour, lw=lw, zorder=5)
    )


def union(circles, cells: int = 620, pad: float = 3.0):
    """A splayed silhouette as one flat shape: a boolean raster and its extent."""
    x_from = min(float(c[0]) - r for c, r in circles) - pad
    x_to = max(float(c[0]) + r for c, r in circles) + pad
    y_from = min(float(c[1]) - r for c, r in circles) - pad
    y_to = max(float(c[1]) + r for c, r in circles) + pad
    down = max(60, int(cells * (y_to - y_from) / (x_to - x_from)))
    gx, gy = np.meshgrid(np.linspace(x_from, x_to, cells), np.linspace(y_from, y_to, down))
    inside = np.zeros_like(gx, dtype=bool)
    for c, r in circles:
        inside |= (gx - float(c[0])) ** 2 + (gy - float(c[1])) ** 2 <= r**2
    return inside, (x_from, x_to, y_from, y_to)


def blob(axis, circles, colour, alpha=0.30, edge=True, zorder=3) -> None:
    """Draw a splayed silhouette flat, so its edge is the only hard line in it.

    Painting the circles one on top of another, as splay_patch does, shades the
    middle of the shape far more heavily than its ends. These pictures are about
    where the edge of a shape falls, so the union is rastered once and filled at
    one strength.
    """
    inside, extent = union(circles)
    rgba = np.zeros(inside.shape + (4,))
    rgba[..., :3] = to_rgb(colour)
    rgba[..., 3] = np.where(inside, alpha, 0.0)
    axis.imshow(rgba, origin="lower", extent=extent, interpolation="nearest", zorder=zorder)
    if edge:
        axis.contour(inside.astype(float), levels=[0.5], colors=[colour], linewidths=1.1,
                     extent=extent, zorder=zorder + 1)


def outline(axis, circles, colour, zorder=6) -> None:
    """The edge of a splayed silhouette and nothing inside it."""
    inside, extent = union(circles)
    axis.contour(inside.astype(float), levels=[0.5], colors=[colour], linewidths=1.3,
                 linestyles=[(0, (4, 3))], extent=extent, zorder=zorder)


def camera(axis) -> None:
    """The camera, the height it looks from, and the line straight down."""
    axis.plot([0.0, 0.0], [HEIGHT, 0.0], color=MUTED, lw=0.9, ls=(0, (4, 4)), zorder=2)
    axis.add_patch(Rectangle((-26, HEIGHT + 4), 52, 26, fc=INK, ec=INK, lw=1.0, zorder=5))
    axis.add_patch(Polygon([(-15, HEIGHT + 4), (15, HEIGHT + 4), (8, HEIGHT - 10),
                            (-8, HEIGHT - 10)], closed=True, fc=INK, ec=INK, zorder=5))
    axis.text(34, HEIGHT + 14, f"the camera, {HEIGHT:.0f} mm up", ha="left", va="center",
              fontsize=NOTE_SIZE, color=INK)
    axis.text(-10, 300, "straight down from the camera", ha="right", va="center",
              fontsize=NOTE_SIZE, color=MUTED)


def side_glass(axis, glass: Glass) -> None:
    """One glass edge on, at its own distance along the line, from the cell's outline."""
    h, r = glass.profile
    axis.fill_betweenx(h, glass.out - r, glass.out + r, facecolor=glass.colour, alpha=0.26,
                       lw=0.0, zorder=4)
    axis.plot(glass.out + r, h, color=glass.colour, lw=1.4, zorder=4)
    axis.plot(glass.out - r, h, color=glass.colour, lw=1.4, zorder=4)
    axis.plot([glass.out - r[-1], glass.out + r[-1]], [h[-1]] * 2, color=glass.colour, lw=1.4,
              zorder=4)
    axis.text(glass.out, glass.height + 12, str(glass.number), ha="center", va="bottom",
              fontsize=LABEL_SIZE, color=INK, zorder=6)


def table(axis, x_from: float, x_to: float) -> None:
    axis.plot([x_from, x_to], [0.0, 0.0], color=INK, lw=1.2, zorder=3)
    axis.text(x_from, 7, "the table", ha="left", va="bottom", fontsize=NOTE_SIZE, color=INK)


def landing(axis, glass: Glass, row: int, label: str, at, align: str) -> None:
    """A bar under the table line showing the strip of picture one glass fills.

    The side view says where a glass stands; the bar says where it ends up. Two
    bars one above the other is the whole of both difficulties: in the first the
    short glass's bar lies inside its neighbour's, and in the second the two
    bars overlap.
    """
    low, high = glass.lands()
    bottom = -62.0 - row * 22.0
    axis.add_patch(Rectangle((low, bottom), high - low, 11.0, fc=glass.colour, alpha=0.40,
                             ec=glass.colour, lw=0.9, zorder=4))
    axis.text(at, bottom + 5.5, label, ha=align, va="center", fontsize=NOTE_SIZE,
              color=glass.colour)


def grazing_ray(glass: Glass):
    """The ray from the camera over the far edge of one glass's rim.

    It leaves the lens, passes the rim, and reaches the table where that rim is
    drawn in the picture. Returns the rim point and the landing point.
    """
    rim = (glass.out + glass.rim / 2.0, glass.height)
    lands = rim[0] * HEIGHT / (HEIGHT - glass.height)
    return rim, (lands, 0.0)


def first_hit(glass: Glass, ray_from, ray_through):
    """Where a ray first touches a glass, going away from the camera.

    Used once, for the merge: the two silhouettes meet in the picture exactly
    because one ray touches both glasses, and that is the point to mark.
    """
    h, r = glass.profile
    start = np.asarray(ray_from, dtype=float)
    step = (np.asarray(ray_through, dtype=float) - start)
    for t in np.linspace(0.0, 4.0, 4000):
        x, y = start + t * step
        if 0.0 <= y <= glass.height and abs(x - glass.out) <= float(np.interp(y, h, r)):
            return x, y
    return None


# ------------------------------------------------- difficulty 1, three pictures


def hidden_on_the_table() -> None:
    """Where the three glasses stand, and how crowded two of them are."""
    one, two, three = HIDDEN
    figure, axis = panel(7.6, 6.6)
    draw_zone(axis)
    axis.plot([NADIR[0] + 230 * -DIRECTION[0], CORNER[0]],
              [NADIR[1] + 230 * -DIRECTION[1], CORNER[1]],
              color=MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)
    draw_nadir(axis, NADIR)
    axis.text(NADIR[0] - 14, NADIR[1], "the point below\nthe camera", ha="right", va="center",
              fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    for glass in HIDDEN:
        footprint(axis, glass)

    left = np.asarray(one.centre) - SIDEWAYS * 76.0
    axis.text(*left, "the tall glass", ha="right", va="center", fontsize=NOTE_SIZE,
              color=one.colour, bbox=MASK, zorder=8)
    axis.text(two.centre[0], two.centre[1] + two.rim / 2.0 + 14, "the short glass",
              ha="center", va="bottom", fontsize=NOTE_SIZE, color=two.colour, bbox=MASK, zorder=8)
    axis.text(three.centre[0] - three.rim / 2.0 - 12, three.centre[1], "standing clear",
              ha="right", va="center", fontsize=NOTE_SIZE, color=three.colour, bbox=MASK, zorder=8)

    arrow(axis, one.centre, two.centre)
    beside = (np.asarray(one.centre) + np.asarray(two.centre)) / 2.0 + SIDEWAYS * 58.0
    axis.text(*beside, f"{CROWDED:.0f} mm\nbetween centres", ha="left", va="center",
              fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    axis.text(
        ZONE[0], ZONE[2] - 52,
        f"A crowded arrangement: the layout rule only guarantees {SEPARATION:.0f} mm.",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    beside_line = np.asarray(NADIR) - DIRECTION * 95.0 + SIDEWAYS * 22.0
    axis.text(*beside_line, "the line the side view follows", ha="left", va="top",
              fontsize=NOTE_SIZE, color=MUTED)
    axis.set_title("On the table: three glasses, two of them crowded",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(225, 800)
    axis.set_ylim(-520, -20)
    save(figure, "hidden-on-the-table.png")


def hidden_from_the_side() -> None:
    """Edge on: the ray over the tall glass's rim lands beyond the short one."""
    one, two, three = HIDDEN
    figure, axis = panel(11.2, 7.0)
    camera(axis)
    table(axis, three.out - 110, 400)
    for glass in HIDDEN:
        side_glass(axis, glass)

    rim, lands = grazing_ray(one)
    axis.plot([0.0, lands[0]], [HEIGHT, 0.0], color=WARN, lw=1.2, zorder=5)
    axis.plot(*rim, marker="o", ms=4, color=WARN, zorder=6)
    axis.plot([lands[0], lands[0]], [0.0, 16.0], color=WARN, lw=1.2, zorder=6)
    axis.text(lands[0] + 8, 24, f"the rim lands here,\n{lands[0] - two.lands()[1]:.0f} mm beyond glass 2",
              ha="left", va="bottom", fontsize=NOTE_SIZE, color=WARN)

    for glass, name, row in ((three, "standing clear", 0), (one, "the tall glass", 0),
                             (two, "the short glass", 1)):
        axis.text(glass.out, -14 - row * 22, name, ha="center", va="top", fontsize=NOTE_SIZE,
                  color=glass.colour)
    landing(axis, one, 0, "where glass 1 lands", one.lands()[1] + 10, "left")
    landing(axis, two, 1, "where glass 2 lands, inside it", two.lands()[1] + 10, "left")

    axis.set_title("From the side: the line of sight passes over the short glass",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(three.out - 120, 520)
    axis.set_ylim(-110, 500)
    save(figure, "hidden-from-the-side.png")


def hidden_what_the_camera_sees() -> None:
    """The picture: two shapes where there are three glasses."""
    one, two, three = HIDDEN
    figure, axis = panel(8.4, 7.2)
    blob(axis, one.circles, GLASS)
    blob(axis, three.circles, GLASS)
    outline(axis, two.circles, WARN)
    draw_nadir(axis)
    axis.text(*(-SIDEWAYS * 56.0), "the point below\nthe camera", ha="right", va="center",
              fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    for glass, along, across in ((one, 230.0, -62.0), (three, -250.0, 0.0)):
        at = DIRECTION * along + SIDEWAYS * across
        axis.text(*at, str(glass.number), ha="center", va="center", fontsize=LABEL_SIZE,
                  color=INK, bbox=MASK, zorder=8)
    axis.annotate(
        "glass 2 is in here, and not\none pixel of the picture is its own",
        xy=tuple(DIRECTION * 250.0), xytext=(305, 95),
        ha="left", va="center", fontsize=NOTE_SIZE, color=WARN,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=9, color=WARN, lw=1.0),
    )
    axis.set_title("What the camera sees: glass 2 is missing altogether",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(-300, 460)
    axis.set_ylim(-340, 310)
    save(figure, "hidden-what-the-camera-sees.png")


# ------------------------------------------------- difficulty 2, three pictures


def bare_strip(one: Glass, two: Glass):
    """The four corners of the bare table between two rims, on the line."""
    inner = one.out + one.rim / 2.0
    outer = two.out - two.rim / 2.0
    across = min(one.rim, two.rim) / 2.0
    return [
        DIRECTION * inner + SIDEWAYS * across,
        DIRECTION * outer + SIDEWAYS * across,
        DIRECTION * outer - SIDEWAYS * across,
        DIRECTION * inner - SIDEWAYS * across,
    ], outer - inner


def merge_on_the_table() -> None:
    """Two glasses the guaranteed gap apart, with bare table between their rims."""
    one, two, three = MERGE
    corners, width = bare_strip(one, two)
    figure, axis = panel(7.6, 6.6)
    draw_zone(axis)
    axis.plot([NADIR[0] + 240 * -DIRECTION[0], CORNER[0]],
              [NADIR[1] + 240 * -DIRECTION[1], CORNER[1]],
              color=MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)
    draw_nadir(axis, NADIR)
    axis.text(NADIR[0] - 14, NADIR[1] - 10, "the point below\nthe camera", ha="right", va="top",
              fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    axis.add_patch(Polygon([tuple(np.asarray(NADIR) + c) for c in corners], closed=True,
                           fc=GOOD, alpha=0.22, ec=GOOD, lw=1.1, zorder=3))
    for glass in MERGE:
        footprint(axis, glass)

    middle = np.asarray(NADIR) + DIRECTION * (one.out + SEPARATION / 2.0)
    across = SIDEWAYS * min(one.rim, two.rim) / 2.0
    arrow(axis, np.asarray(NADIR) + DIRECTION * (one.out + one.rim / 2.0) + across,
          np.asarray(NADIR) + DIRECTION * (two.out - two.rim / 2.0) + across, colour=GOOD)
    axis.text(*(middle + SIDEWAYS * 92.0), f"{width:.0f} mm of\nbare table", ha="left",
              va="center", fontsize=NOTE_SIZE, color=GOOD, bbox=MASK, zorder=8)
    arrow(axis, one.centre, two.centre)
    axis.text(*(middle - SIDEWAYS * 72.0), f"{SEPARATION:.0f} mm\nbetween centres", ha="right",
              va="center", fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    axis.text(three.centre[0] - three.rim / 2.0 - 12, three.centre[1], "standing clear",
              ha="right", va="center", fontsize=NOTE_SIZE, color=three.colour, bbox=MASK, zorder=8)
    axis.text(
        ZONE[0], ZONE[2] - 52,
        "The smallest gap the layout rule allows, so nothing here is crowded.",
        ha="left", va="top", fontsize=NOTE_SIZE, color=INK,
    )
    beside_line = np.asarray(NADIR) - DIRECTION * 95.0 + SIDEWAYS * 22.0
    axis.text(*beside_line, "the line the side view follows", ha="left", va="top",
              fontsize=NOTE_SIZE, color=MUTED)
    axis.set_title("On the table: bare table between glasses 1 and 2",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(225, 800)
    axis.set_ylim(-520, -20)
    save(figure, "merge-on-the-table.png")


def merge_from_the_side() -> None:
    """Edge on: one ray from the lens touches both glasses."""
    one, two, three = MERGE
    _corners, width = bare_strip(one, two)
    figure, axis = panel(11.6, 6.8)
    camera(axis)
    table(axis, three.out - 110, two.lands()[1] + 40)
    for glass in MERGE:
        side_glass(axis, glass)

    rim, _lands = grazing_ray(one)
    hit = first_hit(two, (0.0, HEIGHT), rim)
    if hit is None:
        raise SystemExit("the ray over glass 1's rim misses glass 2, so nothing merges")
    axis.plot([0.0, hit[0]], [HEIGHT, hit[1]], color=WARN, lw=1.2, zorder=5)
    axis.plot(*rim, marker="o", ms=4, color=WARN, zorder=6)
    axis.plot(*hit, marker="o", ms=4, color=WARN, zorder=6)
    axis.text(44, 392, "one ray touches both glasses", ha="left", va="bottom",
              fontsize=NOTE_SIZE, color=WARN)

    inner = one.out + one.rim / 2.0
    arrow(axis, (inner, 10.0), (two.out - two.rim / 2.0, 10.0), colour=GOOD)
    axis.text(inner + width / 2.0, 20, f"{width:.0f} mm of\nbare table", ha="center",
              va="bottom", fontsize=NOTE_SIZE, color=GOOD)

    for glass, name in ((three, "standing clear"), (one, "glass 1"), (two, "glass 2")):
        axis.text(glass.out, -14, name, ha="center", va="top", fontsize=NOTE_SIZE,
                  color=glass.colour)
    landing(axis, one, 0, "where glass 1 lands", one.lands()[1] + 10, "left")
    landing(axis, two, 1, "where glass 2 lands", two.lands()[0] - 10, "right")
    overlap = (two.lands()[0], one.lands()[1])
    axis.add_patch(Rectangle((overlap[0], -96), overlap[1] - overlap[0], 64, fc=WARN, alpha=0.22,
                             ec="none", zorder=6))
    axis.text(sum(overlap) / 2.0, -100, "the two bars overlap", ha="center", va="top",
              fontsize=NOTE_SIZE, color=WARN)

    axis.set_title("From the side: glass 1's rim is thrown across the bare table",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(three.out - 120, two.lands()[1] + 70)
    axis.set_ylim(-124, 500)
    save(figure, "merge-from-the-side.png")


def merge_what_the_camera_sees() -> None:
    """The picture: one shape where there are two glasses."""
    one, two, three = MERGE
    corners, width = bare_strip(one, two)
    figure, axis = panel(8.6, 7.4)
    blob(axis, one.circles, GLASS)
    blob(axis, two.circles, GLASS)
    blob(axis, three.circles, GLASS)
    axis.add_patch(Polygon([tuple(c) for c in corners], closed=True, fill=False, ec=GOOD,
                           lw=1.2, ls=(0, (4, 3)), zorder=7))
    draw_nadir(axis)
    axis.text(*(-SIDEWAYS * 56.0), "the point below\nthe camera", ha="right", va="center",
              fontsize=NOTE_SIZE, color=INK, bbox=MASK, zorder=8)
    for glass, where in ((one, 105.0), (two, 330.0), (three, -250.0)):
        axis.text(*(DIRECTION * where), str(glass.number), ha="center", va="center",
                  fontsize=LABEL_SIZE, color=INK, bbox=MASK, zorder=8)
    axis.annotate(
        "no bare table left here",
        xy=tuple(DIRECTION * 220.0), xytext=(330, 58),
        ha="left", va="center", fontsize=NOTE_SIZE, color=WARN,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=9, color=WARN, lw=1.0),
    )
    axis.annotate(
        f"the {width:.0f} mm of bare table\nis under glass 1's shape",
        xy=tuple(DIRECTION * 146.0 + SIDEWAYS * -20.0), xytext=(-110, 258),
        ha="right", va="center", fontsize=NOTE_SIZE, color=GOOD,
        arrowprops=dict(arrowstyle="-|>", mutation_scale=9, color=GOOD, lw=1.0),
    )
    axis.set_title("What the camera sees: one shape where there are two glasses",
                   fontsize=TITLE, color=INK, pad=10)
    axis.set_xlim(-290, 470)
    axis.set_ylim(-300, 420)
    save(figure, "merge-what-the-camera-sees.png")


# ----------------------------------------------------------------------- main


def main() -> None:
    one, two, three = HIDDEN
    check(HIDDEN, crowded_pair=(1, 2))
    if not splay_covers(one.circles, two.circles):
        raise SystemExit("glass 1 does not cover glass 2 completely, so nothing is missing")
    for other in (one, two):
        if touching(other, three):
            raise SystemExit("glass 3 is supposed to stand clear of the other two")
    print(f"hidden set: glass 1 covers glass 2 completely at {CROWDED:.0f} mm between centres; "
          f"the cover stays complete up to {cover_limit(one, two):.0f} mm")

    first, second, spare = MERGE
    check(MERGE)
    if splay_covers(first.circles, second.circles) or splay_covers(second.circles, first.circles):
        raise SystemExit("one merge glass covers the other, which is the first difficulty again")
    if not touching(first, second):
        raise SystemExit("the two merge silhouettes do not meet, so nothing merges")
    for other in (first, second):
        if touching(other, spare):
            raise SystemExit("glass 3 is supposed to stand clear of the other two")
    _corners, width = bare_strip(first, second)
    print(f"merge set: neither silhouette covers the other, the two touch, and "
          f"{width:.0f} mm of bare table lies between the rims")

    hidden_on_the_table()
    hidden_from_the_side()
    hidden_what_the_camera_sees()
    merge_on_the_table()
    merge_from_the_side()
    merge_what_the_camera_sees()


if __name__ == "__main__":
    main()
