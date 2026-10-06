"""Pictures for the examiner — the one all six solutions are marked by.

Each diagram carries one point from the examiner chapter:

    03-the-ordinary-family.png      the spacing the cell's own spawner gives
    03-the-crowded-family.png       the same zone, as close as the cell allows
    03-three-stations.png           three pictures rather than one, and why they overlap
    03-what-a-solution-is-given.png the grey picture, the depth, the pose, and nothing else
    03-what-the-examiner-keeps.png     the id picture, and its two separate jobs
    03-matching-by-pixels.png       which real glass a report is talking about
    03-the-two-mask-numbers.png     covered, and not the glass

Everything drawn from above is drawn through the splay model in
``diagram_style``: a camera 450 mm over the table sees the rim of a standing
glass thrown outwards from the point below the lens, and the taller the glass
the further out it goes. A plan view drawn with plain circles would show a
problem this cell does not have. The grey, depth and id pictures in these
figures are built from that same stack of circles, so a pixel is shaded by the
distance to whichever glass surface is highest along its ray, which is what the
renderer's own depth and id pictures hold.

Every number written on these pictures is either read out of
``code/src/08_seeing-the-glasses/`` — see the constants below, each with the
file it came from — or measured from the picture being drawn. None of them is
typed in by hand twice.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_examiner_pictures.py

Needs matplotlib, numpy and opencv.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2
import numpy as np
from diagram_style import (
    FX,
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    SHORT_A,
    SHORT_B,
    SURVEY_H,
    TALL_A,
    TALL_B,
    TITLE_SIZE,
    WARN,
    bare,
    new,
    save,
    splay_circles,
    splay_covers,
    splay_patch,
)
from matplotlib.colors import to_rgba
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle, Wedge

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[3] / "code" / "src" / "08_seeing-the-glasses" / "work_cell"),
)

from work_cell.glasses.shapes import build  # noqa: E402

# --------------------------------------------------------------------------- #
# the cell's own numbers, in millimetres
# --------------------------------------------------------------------------- #

# rack/layout.py GLASS_ZONE, in metres: (0.32, 0.64, -0.44, -0.08).
ZONE = (320.0, 640.0, -440.0, -80.0)

# glasses/spawn.py MIN_SEPARATION: no two centres may come closer than this.
MIN_SEPARATION = 150.0

# bench/data.py CROWDED_GAP: a crowded line stands its glasses 0.3 to 0.7 of
# that separation apart. CROWDED_LINES and CROWDED_DEEP: two lines of three.
CROWDED_SHARE = (0.3, 0.7)
CROWDED_GAP = tuple(share * MIN_SEPARATION for share in CROWDED_SHARE)
CROWDED_LINES, CROWDED_DEEP = 2, 3

# render.py WIDTH, HEIGHT and FOCAL: a 320 by 240 picture from a lens whose
# horizontal field of view is 1.047 rad, which is 277 pixels of focal length.
FRAME_PX = (320, 240)

# How many millimetres of table one pixel covers at the table top.
PIXEL_MM = SURVEY_H / FX

# arm/dimensions.py SURVEY_BASELINE and GRIPPER_MAX_OPENING: the two margins
# bench/data.py shared() takes off one picture.
BASELINE = 120.0
GRIPPER_OPENING = 95.0

# What one picture covers at the survey height, and the part of it a station can
# be credited with. The same arithmetic as bench/data.py frame() and shared().
PICTURE = (SURVEY_H * FRAME_PX[0] / FX, SURVEY_H * FRAME_PX[1] / FX)
CREDITED = (PICTURE[0] - GRIPPER_OPENING, PICTURE[1] - BASELINE - GRIPPER_OPENING)

# Where the camera stands, from arm/dimensions.py survey_stations() run on the
# glass zone with that credited patch. Three places, 93 mm apart in y.
STATIONS = ((480.0, -352.7), (480.0, -260.0), (480.0, -167.3))

# render.py TEST_SEEDS: which arrangements a method may be fitted on.
TEST_SEEDS = 10_000

# bench/masks_to_glasses.py RIM_BAND and SPREAD: the shared step that turns a
# mask into a place and a width.
RIM_BAND = 8.0
SPREAD = 95

# bench/scoring.py MERGED_SHARE.
MERGED_SHARE = 0.2

# Measured mask numbers for a stemmed glass, from the two solutions this book
# compares on them: 01-rules-on-the-table/README.md and
# 02-train-from-scratch/README.md, spawned layouts, median over 100 glasses.
RULE_STEMMED = (86.6, 0.0)
FITTED_STEMMED = (98.6, 1.3)

# The one stemmed glass the last picture is drawn from, in metres, and how far
# out from under the camera it stands, in millimetres. Every proportion is
# inside glasses/shapes.py KIND_RANGES["stemmed_glass"], and the distance is the
# furthest out such a glass can stand with its whole outline still in the
# picture, which stemmed_view() checks.
STEMMED = {"height": 0.210, "bowl_diameter": 0.085, "stem_diameter": 0.008,
           "foot_fraction": 0.82, "stem_fraction": 0.42}
STEMMED_OUT_BY = 95.0

FAINT = "#eef1f4"


def tint(fraction: float) -> tuple[float, float, float, float]:
    """``GLASS`` mixed with white. 0 is white, 1 is the colour itself.

    An id picture of four glasses needs four marks, and this palette has not got
    four colours that mean nothing, so the glasses are told apart by a number
    written on each and the shading only keeps them visibly separate.
    """
    base = np.array(to_rgba(GLASS))
    white = np.array([1.0, 1.0, 1.0, 1.0])
    return tuple(white + (base - white) * fraction)


ID_TINTS = [tint(f) for f in (0.30, 0.52, 0.74, 0.96, 0.41, 0.63)]


# --------------------------------------------------------------------------- #
# the scenes these pictures are drawn from
# --------------------------------------------------------------------------- #

MIDDLE = np.array(STATIONS[1])

# An arrangement the cell's spawner could have produced: five glasses of one
# kind in the zone, the closest pair exactly MIN_SEPARATION apart.
SPAWNED = {
    1: (np.array([360.0, -400.0]), TALL_A),
    2: (np.array([360.0, -250.0]), SHORT_B),
    3: (np.array([570.0, -410.0]), TALL_B),
    4: (np.array([600.0, -240.0]), SHORT_A),
    5: (np.array([470.0, -110.0]), TALL_A),
}


def crowded_scene() -> dict[int, tuple[np.ndarray, tuple[float, float]]]:
    """Two lines of three, built the way bench/data.py builds a crowded one.

    A line starts a short way out from under the camera and runs outwards, and
    each step along it is shorter than the separation the layout rule
    guarantees. The two lines point opposite ways so that neither runs into the
    other.
    """
    sizes = ((TALL_A, SHORT_A, TALL_B), (SHORT_B, TALL_A, SHORT_A))
    steps = ((45.0, 90.0, 170.0), (50.0, 125.0, 200.0))
    scene, index = {}, 1
    for line in range(CROWDED_LINES):
        angle = math.radians(230.0 + line * 360.0 / CROWDED_LINES)
        direction = np.array([math.cos(angle), math.sin(angle)])
        for deep in range(CROWDED_DEEP):
            scene[index] = (MIDDLE + direction * steps[line][deep], sizes[line][deep])
            index += 1
    return scene


CROWDED = crowded_scene()


def check_inside_the_zone(scene, name: str) -> None:
    """Every glass in an arrangement stands inside the glass zone.

    The outline of a standing glass spills well outside the zone in an overhead
    picture, which is the point of several of these diagrams, but the glass
    itself never does: the spawner draws its places inside the zone and the
    crowded arrangements are built inside it too. A picture showing a glass
    standing outside the rectangle would be showing something the cell cannot
    produce, so the places are checked here rather than trusted.
    """
    x0, x1, y0, y1 = ZONE
    for key, (centre, _) in scene.items():
        if not (x0 <= centre[0] <= x1 and y0 <= centre[1] <= y1):
            raise SystemExit(f"{name} glass {key} stands at {centre}, outside the glass zone {ZONE}")


check_inside_the_zone(SPAWNED, "spawned")
check_inside_the_zone(CROWDED, "crowded")

# The arrangement the input picture and the id picture are drawn from. Four
# glasses, all of them inside one station's picture.
IN_FRAME = {
    1: (np.array([400.0, -330.0]), TALL_A),
    2: (np.array([555.0, -330.0]), SHORT_A),
    3: (np.array([420.0, -180.0]), TALL_B),
    4: (np.array([575.0, -165.0]), SHORT_B),
}

# Two glasses for the matching picture: a short one with a taller one beside it,
# standing closer than the layout rule allows, which is where the mask of one
# glass runs onto the next.
NEIGHBOURS = {
    1: (MIDDLE + np.array([72.0, -28.0]), SHORT_A),
    2: (MIDDLE + np.array([-25.0, 10.0]), TALL_A),
}


# --------------------------------------------------------------------------- #
# the splay model, with the heights kept
# --------------------------------------------------------------------------- #


def stack(nadir, centre, glass, slices: int = 60):
    """``splay_circles`` with the height of each circle kept beside it.

    ``splay_circles`` returns the stack of circles a standing glass draws in an
    overhead picture. Shading a pixel needs the height of the circle that
    claimed it as well, because that height is what the depth reading is made
    of, so this pairs each circle with the height it was taken at — the same
    heights ``splay_circles`` walks up.
    """
    height, rim = glass
    circles = splay_circles(nadir, centre, height, rim, slices=slices)
    heights = [height * i / (slices - 1) for i in range(slices)]
    return [(c, r, z) for (c, r), z in zip(circles, heights, strict=True)]


def stack_of_outline(nadir, centre, outline, slices: int = 90):
    """The same stack for a real outline out of ``work_cell.glasses.shapes``.

    ``splay_circles`` walks straight from the base radius to the rim radius,
    which is what a tumbler or a tapered glass does. A stemmed glass does not:
    it is a wide foot, then a stem a few millimetres across, then a bowl. That
    thin stem is the whole point of the last picture here, so that picture
    follows the cell's own outline, scaled by the same ``H / (H - z)``.
    """
    offset = np.asarray(centre, dtype=float) - np.asarray(nadir, dtype=float)
    heights = np.asarray(outline.height) * 1000.0
    radii = np.asarray(outline.radius) * 1000.0
    pick = np.linspace(0, len(heights) - 1, slices).round().astype(int)
    out = []
    for index in pick:
        z = float(heights[index])
        k = SURVEY_H / (SURVEY_H - z)
        out.append((offset * k, float(radii[index]) * k, z))
    return out


def circles_of(stacked):
    """Just the circles, for ``splay_patch`` and ``splay_covers``."""
    return [(c, r) for c, r, _ in stacked]


def shifted(circles, origin):
    """The same circles, moved from nadir-relative into table coordinates."""
    return [(c + np.asarray(origin, dtype=float), r) for c, r in circles]


def bounds_of(scenes, nadir) -> tuple[float, float, float, float]:
    """A box holding every outline in these scenes, in table coordinates."""
    xs, ys = [], []
    for scene in scenes:
        for centre, glass in scene.values():
            for c, r in shifted(circles_of(stack(nadir, centre, glass)), nadir):
                xs += [c[0] - r, c[0] + r]
                ys += [c[1] - r, c[1] + r]
    return min(xs), max(xs), min(ys), max(ys)


def paint(grid_x, grid_y, scene, nadir):
    """Which glass each pixel shows, and how high the surface it shows is.

    A pixel takes the highest circle that contains it, because that is the
    surface the ray struck first. ``ids`` is 0 where the ray reached the table.
    """
    top = np.zeros_like(grid_x)
    ids = np.zeros(grid_x.shape, dtype=int)
    for key, (centre, glass) in sorted(scene.items()):
        for c, r, z in stack(nadir, centre, glass):
            inside = (grid_x - c[0]) ** 2 + (grid_y - c[1]) ** 2 <= r * r
            nearer = inside & (z > top)
            top[nearer] = z
            ids[nearer] = key
    return ids, top


def overhead(scene, nadir=MIDDLE, pixels=FRAME_PX):
    """The id picture and the depth picture one station sees of one arrangement.

    Returned in the table's own millimetres rather than in pixel rows, because
    every other panel in these figures is a plan view and the two have to be
    read against each other. A camera looking straight down makes that honest:
    the picture is the table, scaled.

    ``distance`` holds how far the surface at each pixel is from the lens, in
    millimetres. ``extent`` is what ``imshow`` wants, in millimetres from the
    point below the camera.
    """
    width, height = pixels
    half_x, half_y = PIXEL_MM * width / 2.0, PIXEL_MM * height / 2.0
    grid_x, grid_y = np.meshgrid(np.linspace(-half_x, half_x, width),
                                 np.linspace(-half_y, half_y, height))
    ids, top = paint(grid_x, grid_y, scene, nadir)

    # The ray through a pixel is at horizontal offset q * (H - z) / H when it
    # reaches height z, so that is how far out the surface it struck is.
    reach = np.hypot(grid_x, grid_y) * (SURVEY_H - top) / SURVEY_H
    distance = np.hypot(reach, SURVEY_H - top)
    return ids, distance, top, (-half_x, half_x, -half_y, half_y), (grid_x, grid_y)


def grey_of(distance):
    """The grey picture: shaded from how far away each surface is.

    Near is bright. Kept off both ends of the scale so that an outline drawn
    over it in ink still reads.
    """
    low, high = distance.min(), distance.max()
    return 0.28 + 0.64 * (high - distance) / (high - low)


def patches_in(ids) -> int:
    """How many separate patches of glass pixels this picture holds.

    A method that cuts a picture into connected patches can return at best one
    report per patch, so this is the number that says whether two glasses can
    be told apart at all from this one picture.
    """
    count, _ = cv2.connectedComponents((ids > 0).astype(np.uint8), connectivity=8)
    return count - 1


def place_and_width(mask, top, grid, nadir=MIDDLE):
    """The examiner's shared step, run on the pixels of one mask.

    The same arithmetic as bench/masks_to_glasses.py one_glass(): every mask
    pixel becomes a point in the room, the axis is the middle of the points
    within RIM_BAND of the highest one, and the width is twice the SPREAD-th
    percentile of how far the cloud reaches from that axis.
    """
    grid_x, grid_y = grid
    z = top[mask]
    scale = (SURVEY_H - z) / SURVEY_H
    x = np.asarray(nadir)[0] + grid_x[mask] * scale
    y = np.asarray(nadir)[1] + grid_y[mask] * scale
    band = z >= z.max() - RIM_BAND
    axis = np.array([x[band].mean(), y[band].mean()])
    reach = float(np.percentile(np.hypot(x - axis[0], y - axis[1]), SPREAD))
    return axis, 2.0 * reach


# --------------------------------------------------------------------------- #
# drawing helpers
# --------------------------------------------------------------------------- #


def titles(figure, axes, labels, colours=None, *, heading: str | None = None,
           lift: float = 0.03) -> None:
    """Panel titles on one line, whatever the panels' shapes do to their boxes.

    ``set_title`` hangs a title off the axes box, and an equal-aspect plan view
    has a shorter box than the picture beside it, so two titles set that way
    come out at different heights. Reading the boxes back once the layout is
    settled and placing the text in figure coordinates keeps them level. The
    same helper as make_03_images.py, for the same reason.
    """
    figure.canvas.draw()
    boxes = [axis.get_position() for axis in axes]
    top = max(box.y1 for box in boxes)
    colours = colours or [INK] * len(labels)
    for box, label, colour in zip(boxes, labels, colours, strict=True):
        figure.text((box.x0 + box.x1) / 2.0, top + lift, label, ha="center",
                    va="bottom", fontsize=TITLE_SIZE, color=colour)
    if heading:
        figure.text(0.5, top + lift + 0.085, heading, ha="center", va="bottom",
                    fontsize=TITLE_SIZE + 1, color=INK)


def under(figure, axes, texts, colours=None, *, y=0.10) -> None:
    """A block of sentences under each panel, in figure coordinates.

    Text this long does not fit inside a plan view without landing on a glass,
    and a white box over the drawing hides the thing being described.
    """
    figure.canvas.draw()
    colours = colours or [INK] * len(texts)
    for axis, text, colour in zip(axes, texts, colours, strict=True):
        box = axis.get_position()
        figure.text((box.x0 + box.x1) / 2.0, y, text, ha="center", va="top",
                    fontsize=NOTE_SIZE, color=colour)


def note(axis, x, y, text, *, colour=INK, ha="left", va="top", size=NOTE_SIZE, alpha=0.88):
    """A block of text that stays readable over a shaded drawing."""
    return axis.text(x, y, text, ha=ha, va=va, color=colour, fontsize=size, zorder=14,
                     bbox={"facecolor": "white", "edgecolor": "none", "alpha": alpha, "pad": 2.6})


def pointer(axis, text, at, to, *, colour=WARN, ha="left", va="top"):
    """A sentence set clear of the drawing, with a line to what it is about."""
    axis.annotate(text, xy=at, xytext=to, fontsize=NOTE_SIZE, color=colour, ha=ha, va=va,
                  zorder=15, arrowprops={"arrowstyle": "->", "color": colour, "linewidth": 1.1},
                  bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2.6})


def caption(figure, text, *, y=0.012) -> None:
    figure.text(0.5, y, text, ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED)


def zone_patch(axis, *, label=None, fill=True, zorder=1) -> None:
    """The glass zone, 320 mm across by 360 mm deep, as the layout file gives it.

    The label goes inside the top left corner rather than under the rectangle,
    because the outlines of the glasses spill well outside the zone and any
    label put outside it lands on one of them.
    """
    x0, x1, y0, y1 = ZONE
    axis.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                             facecolor=FAINT if fill else "none", edgecolor=MUTED,
                             linestyle=":", linewidth=1.2, zorder=zorder))
    if label:
        axis.text(x0 + 6.0, y1 - 6.0, label, ha="left", va="top", fontsize=NOTE_SIZE,
                  color=MUTED, zorder=zorder + 1)


def silhouette_edge(axis, circles, *, colour, step=1.5, **line):
    """The boundary of a splayed outline, as one line rather than a stack.

    ``splay_patch`` draws the silhouette as sixty overlapping circles, and sixty
    transparent circles on top of each other come out solid, so a faint stack is
    not faint. Where only the shape of the outline is wanted the shape is
    rasterised and its edge drawn as a single line instead.
    """
    xs = [c[0] - r for c, r in circles] + [c[0] + r for c, r in circles]
    ys = [c[1] - r for c, r in circles] + [c[1] + r for c, r in circles]
    grid_x, grid_y = np.meshgrid(np.arange(min(xs) - step, max(xs) + step, step),
                                 np.arange(min(ys) - step, max(ys) + step, step))
    inside = np.zeros(grid_x.shape, dtype=bool)
    for c, r in circles:
        inside |= (grid_x - c[0]) ** 2 + (grid_y - c[1]) ** 2 <= r * r
    axis.contour(grid_x, grid_y, inside.astype(float), levels=[0.5], colors=[colour], **line)


def draw_glass_from_above(axis, nadir, centre, glass, *, colour=GLASS, alpha=0.26,
                          key=None, clip=None, ghost=False):
    """One standing glass as the overhead camera sees it, plus where it stands.

    ``clip`` is a rectangle the outline is cut to, for showing what one
    station's picture actually holds. ``ghost`` draws the edge of the whole
    outline as a dashed line, so that a glass cut off at the frame edge can be
    seen to be cut and the part the picture has not got can be seen.
    """
    circles = shifted(circles_of(stack(nadir, centre, glass)), nadir)
    if ghost:
        silhouette_edge(axis, circles, colour=colour, linewidths=1.1,
                        linestyles=[(0, (4, 3))], zorder=2)
    first = len(axis.patches)
    splay_patch(axis, circles, colour=colour, alpha=alpha, zorder=3)
    if clip is not None:
        for patch in axis.patches[first:]:
            patch.set_clip_path(clip)
    base = circles[0][1]
    axis.add_patch(Circle(centre, base, facecolor="none", edgecolor=INK, linewidth=1.0, zorder=6))
    axis.plot(*centre, marker="+", ms=5, color=INK, zorder=7)
    if key is not None:
        axis.text(centre[0], centre[1] - base - 6.0, str(key), ha="center", va="top",
                  fontsize=LABEL_SIZE, color=INK, fontweight="bold", zorder=8)


def measure(axis, start, end, text, *, colour=INK, offset=(0.0, 0.0), ha="center",
            va="bottom", size=NOTE_SIZE):
    """A double-headed arrow between two points, with the distance written clear of it.

    The text is set off the line rather than on it, because a line drawn
    through a word is harder to read than a word a little way away from what
    it measures, and its box is opaque so that nothing shows through.
    """
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    axis.add_patch(FancyArrowPatch(start, end, arrowstyle="<|-|>", mutation_scale=9,
                                   color=colour, linewidth=1.2, shrinkA=0, shrinkB=0,
                                   zorder=11))
    middle = (start + end) / 2.0 + np.asarray(offset, dtype=float)
    note(axis, middle[0], middle[1], text, colour=colour, ha=ha, va=va, size=size, alpha=1.0)


def hidden_share(scene, key, nadir=MIDDLE):
    """How much of one glass's outline the other glasses stand in front of."""
    ids, _, _, _, _ = overhead(scene, nadir, pixels=(640, 480))
    alone, _, _, _, _ = overhead({key: scene[key]}, nadir, pixels=(640, 480))
    whole = np.count_nonzero(alone == key)
    return 1.0 - np.count_nonzero(ids == key) / whole if whole else 0.0


# --------------------------------------------------------------------------- #
# 1. the two families of arrangement
# --------------------------------------------------------------------------- #


def _family_panel(axis, scene):
    """One family of arrangement, drawn from straight above, on its own axes.

    The two families are two separate pictures rather than two panels of one,
    because they are two different ideas and a reader meets them a paragraph
    apart. Both panels use the same limits so that the spacing in one can be
    compared with the spacing in the other by eye.
    """
    x0, x1, y0, y1 = bounds_of((SPAWNED, CROWDED), MIDDLE)
    bare(axis)
    axis.set_xlim(x0 - 30.0, x1 + 30.0)
    axis.set_ylim(y0 - 30.0, y1 + 30.0)
    axis.set_aspect("equal")
    zone_patch(axis)
    axis.plot(*MIDDLE, marker="x", ms=8, mew=1.8, color=MUTED, zorder=9)
    for key, (centre, glass) in scene.items():
        draw_glass_from_above(axis, MIDDLE, centre, glass, key=key)


def ordinary_family() -> None:
    """The spacing the cell's own spawner gives, and the guarantee under it.

    One thing only: no second centre may lie inside the dashed circle, so there
    is always bare table between two glasses. What that spacing costs a reader
    in words belongs in the prose; the picture carries the circle.
    """
    figure, axis = new(6.4, 6.6)
    figure.subplots_adjust(bottom=0.06, top=0.88, left=0.06, right=0.96)
    _family_panel(axis, SPAWNED)

    first, second = SPAWNED[1][0], SPAWNED[2][0]
    axis.add_patch(Circle(first, MIN_SEPARATION, facecolor="none", edgecolor=GOOD,
                          linestyle=(0, (5, 4)), linewidth=1.3, zorder=10))
    measure(axis, first, second, f"{np.linalg.norm(second - first):.0f} mm", colour=GOOD,
            offset=(8.0, 0.0), ha="left", va="center")

    figure.text(0.5, 0.955, "The ordinary family: spaced as the cell's spawner spaces it",
                ha="center", va="top", fontsize=TITLE_SIZE, color=INK)
    figure.text(0.5, 0.905, "No other centre may lie inside the dashed circle.",
                ha="center", va="top", fontsize=NOTE_SIZE, color=GOOD)
    save(figure, "03-the-ordinary-family.png")


def crowded_family() -> None:
    """The same zone with the glasses pushed as close as the cell allows.

    One thing only: at this spacing two outlines run together and a short glass
    can go behind a tall one. Both are measured off the drawing rather than
    asserted, and both are named in two or three words.
    """
    figure, axis = new(6.4, 6.6)
    figure.subplots_adjust(bottom=0.06, top=0.88, left=0.06, right=0.96)
    _family_panel(axis, CROWDED)

    gap_close = np.linalg.norm(CROWDED[2][0] - CROWDED[1][0])
    gap_far = np.linalg.norm(CROWDED[5][0] - CROWDED[4][0])
    measure(axis, CROWDED[1][0], CROWDED[2][0], f"{gap_close:.0f} mm", colour=WARN,
            offset=(-44.0, 16.0), ha="right", va="center")
    # Up and to the left of the pair, because the straight-across position puts
    # the label's own white box over glass 5's centre marker and the reader then
    # sees a line of two glasses numbered 4 and 6.
    measure(axis, CROWDED[4][0], CROWDED[5][0], f"{gap_far:.0f} mm", colour=WARN,
            offset=(-14.0, 24.0), ha="right", va="center")

    # The two things this spacing causes — glass 2 with no pixels at all, and
    # glasses 4, 5 and 6 running into one patch — are visible in the drawing and
    # named in the prose under it. A pointer to either one has to cross a glass
    # to reach it, and a line through the thing being described is worse than a
    # sentence beside the picture.
    swallowed = splay_covers(circles_of(stack(MIDDLE, CROWDED[1][0], CROWDED[1][1])),
                             circles_of(stack(MIDDLE, CROWDED[2][0], CROWDED[2][1])))
    print(f"  crowded: glass 2 completely hidden by glass 1: {swallowed}; "
          f"patches of pixels: {patches_in(overhead(CROWDED)[0])}; "
          f"glass 2 loses {100 * hidden_share(CROWDED, 2):.0f} per cent of its outline")

    figure.text(0.5, 0.955, "The crowded family: as close as the cell allows",
                ha="center", va="top", fontsize=TITLE_SIZE, color=INK)
    figure.text(0.5, 0.905, "Each step is a third to two thirds of the ordinary spacing.",
                ha="center", va="top", fontsize=NOTE_SIZE, color=WARN)
    save(figure, "03-the-crowded-family.png")


# --------------------------------------------------------------------------- #
# 2. three stations rather than one
# --------------------------------------------------------------------------- #


def three_stations() -> None:
    """Why the survey takes three pictures, and why they have to overlap.

    One picture covers more table than the zone is deep, so it is not the size
    of the frame that forces three stations. It is the edge of the frame: a
    glass caught there is cut off, and a cut-off outline has its middle in the
    wrong place. So a station is credited only with the middle of its picture,
    and the stations stand close enough that whatever is cut off at one is well
    inside another. The glass drawn here is the case that settles it.
    """
    figure, axes = new(11.6, 6.8, columns=2)
    figure.subplots_adjust(bottom=0.24, top=0.89, left=0.04, right=0.98)
    one, three = axes

    # A glass standing 12 mm inside the top edge of the first station's picture.
    edge_y = STATIONS[0][1] + PICTURE[1] / 2.0
    victim_at, victim_glass = np.array([520.0, edge_y - 12.0]), TALL_A

    # The top of the view holds the rest of the cut-off glass's outline, which
    # reaches 115 mm beyond the far edge of the zone, so the limits are set from
    # that rather than from the zone.
    for axis in axes:
        bare(axis)
        axis.set_xlim(195.0, 775.0)
        axis.set_ylim(-575.0, 155.0)
        axis.set_aspect("equal")

    # ---- what one station's picture holds
    station = np.array(STATIONS[0])
    frame = Rectangle((station[0] - PICTURE[0] / 2.0, station[1] - PICTURE[1] / 2.0),
                      *PICTURE, facecolor="none", edgecolor=MUTED, linestyle=(0, (5, 3)),
                      linewidth=1.3, zorder=5)
    one.add_patch(frame)
    zone_patch(one)
    one.add_patch(Rectangle((station[0] - CREDITED[0] / 2.0, station[1] - CREDITED[1] / 2.0),
                            *CREDITED, facecolor=to_rgba(GOOD, 0.14), edgecolor=GOOD,
                            linewidth=1.3, zorder=3))
    draw_glass_from_above(one, station, victim_at, victim_glass, colour=WARN, alpha=0.34,
                          clip=frame, ghost=True)
    one.plot(*station, marker="o", ms=7, color=INK, zorder=10)
    note(one, station[0] + 12.0, station[1] - 6.0, "station 1", colour=INK, ha="left", va="top")
    pointer(one, "this glass is cut off at the top\nedge of the picture. The dashed\nline is the rest of its "
                 "outline,\nwhich this picture has not got,\nso a middle read off it is in the\nwrong place.",
            (victim_at[0] - 30.0, edge_y - 4.0), (205.0, 145.0), colour=WARN, ha="left", va="top")
    measure(one, (station[0] - PICTURE[0] / 2.0, -556.0), (station[0] + PICTURE[0] / 2.0, -556.0),
            f"one picture covers {PICTURE[0]:.0f} mm by {PICTURE[1]:.0f} mm", colour=MUTED,
            offset=(0.0, -12.0), va="top")
    measure(one, (station[0] - CREDITED[0] / 2.0, station[1] - CREDITED[1] / 2.0 - 20.0),
            (station[0] + CREDITED[0] / 2.0, station[1] - CREDITED[1] / 2.0 - 20.0),
            f"credited with {CREDITED[0]:.0f} mm by {CREDITED[1]:.0f} mm", colour=GOOD,
            offset=(0.0, -12.0), va="top")

    # ---- the three stations
    zone_patch(three, fill=False, zorder=8)
    for index, place in enumerate(STATIONS, start=1):
        place = np.array(place)
        three.add_patch(Rectangle((place[0] - CREDITED[0] / 2.0, place[1] - CREDITED[1] / 2.0),
                                  *CREDITED, facecolor=to_rgba(GOOD, 0.09), edgecolor=GOOD,
                                  linewidth=1.2, zorder=4))
        three.plot(*place, marker="o", ms=7, color=INK, zorder=10)
        three.text(place[0] - CREDITED[0] / 2.0 - 8.0, place[1], f"station {index}", ha="right",
                   va="center", fontsize=NOTE_SIZE, color=INK, zorder=11)
    draw_glass_from_above(three, np.array(STATIONS[2]), victim_at, victim_glass,
                          colour=GOOD, alpha=0.30)
    gap = STATIONS[1][1] - STATIONS[0][1]
    measure(three, (740.0, STATIONS[0][1]), (740.0, STATIONS[1][1]), f"{gap:.0f} mm",
            colour=MUTED, offset=(6.0, 0.0), ha="left", va="center")
    inside_by = (STATIONS[2][1] + CREDITED[1] / 2.0) - victim_at[1]
    pointer(three, f"the same glass stands {inside_by:.0f} mm inside station 3's\n"
                   "patch, and station 3 looks almost straight down\non it, so station 3 is where it is counted",
            victim_at, (205.0, -555.0), colour=GOOD, ha="left", va="bottom")

    titles(figure, axes, ["What one station's picture holds", "The three stations the survey uses"],
           heading="Three pictures rather than one, and why they overlap", lift=0.02)
    under(figure, axes, [
        "A station is credited only with the part of the table both of its\n"
        f"pictures hold: the second picture slides {BASELINE:.0f} mm sideways, and the\n"
        f"widest glass the gripper closes on is {GRIPPER_OPENING:.0f} mm across.",
        "The three credited patches cover the zone's whole depth and overlap\n"
        "their neighbours, so a glass cut off at one station's frame edge sits\n"
        "well inside another station's patch.",
    ], y=0.195)
    caption(figure,
            "The dotted rectangle is the glass zone. Each outline is drawn through the camera that sees it, so the "
            "same glass leans away from station 1\nand stands almost upright for station 3, which is directly "
            "above it.", y=0.01)
    save(figure, "03-three-stations.png")


# --------------------------------------------------------------------------- #
# 3. what a solution is given
# --------------------------------------------------------------------------- #


def what_a_solution_is_given() -> None:
    """The three things a solution may read, side by side for one arrangement.

    The point is that this is the whole input: two pictures and a pose, handed
    over by the examiner, with nothing for a solution to go and fetch.
    """
    _, distance, _, extent, _ = overhead(IN_FRAME)
    figure, axes = new(12.4, 5.2, columns=3)
    # What there is to say about each picture goes under it: a box of text over
    # a picture hides the glasses the picture is of.
    figure.subplots_adjust(bottom=0.22, top=0.86, left=0.03, right=0.98)
    grey_axis, depth_axis, pose_axis = axes

    grey_axis.imshow(grey_of(distance), cmap="gray", vmin=0.0, vmax=1.0, origin="lower",
                     extent=extent, interpolation="nearest")
    depth_image = depth_axis.imshow(distance, cmap="Blues", origin="lower", extent=extent,
                                    interpolation="nearest")
    for axis in (grey_axis, depth_axis):
        bare(axis)
        axis.set_aspect("equal")
    bar = figure.colorbar(depth_image, ax=depth_axis, fraction=0.04, pad=0.03)
    bar.set_label("millimetres from the lens", fontsize=NOTE_SIZE, color=INK)
    bar.ax.tick_params(labelsize=NOTE_SIZE - 0.8, colors=INK)
    bar.outline.set_visible(False)

    under(figure, axes, [
        f"{FRAME_PX[0]} by {FRAME_PX[1]} pixels, one shade per pixel,\n"
        "bright where the surface is near the lens.",
        f"The nearest rim reads {distance.min():.0f} mm and the\nbare table reads {distance.max():.0f} mm.",
        "",
    ], y=0.175)

    # ---- the pose, drawn from the side
    bare(pose_axis)
    pose_axis.set_xlim(-320.0, 320.0)
    pose_axis.set_ylim(-150.0, 600.0)
    pose_axis.plot([-300.0, 300.0], [0.0, 0.0], color=INK, linewidth=1.6)
    pose_axis.text(300.0, -12.0, "the table top", ha="right", va="top", fontsize=NOTE_SIZE, color=INK)
    for centre, (height, rim) in sorted(IN_FRAME.values(), key=lambda item: item[0][0]):
        across = centre[0] - MIDDLE[0]
        pose_axis.add_patch(Polygon([(across - rim * 0.22, 0.0), (across + rim * 0.22, 0.0),
                                     (across + rim / 2.0, height), (across - rim / 2.0, height)],
                                    closed=True, facecolor=GLASS, alpha=0.30, edgecolor=GLASS,
                                    linewidth=1.0, zorder=3))
    camera_at = np.array([0.0, SURVEY_H])
    pose_axis.add_patch(Wedge(camera_at, 54.0, 248.0, 292.0, facecolor=INK, edgecolor="none", zorder=6))
    pose_axis.add_patch(Circle(camera_at, 18.0, facecolor=INK, edgecolor="none", zorder=6))
    pose_axis.plot([0.0, 0.0], [0.0, SURVEY_H - 54.0], color=INK, linestyle=(0, (4, 3)),
                   linewidth=1.0, zorder=2)
    measure(pose_axis, (-280.0, 0.0), (-280.0, SURVEY_H), f"{SURVEY_H:.0f} mm", colour=INK,
            offset=(10.0, 0.0), ha="left", va="center")
    note(pose_axis, 0.0, SURVEY_H + 44.0,
         f"x = {MIDDLE[0]:.0f} mm, y = {MIDDLE[1]:.0f} mm, {SURVEY_H:.0f} mm up,\nlooking straight down",
         colour=INK, ha="center", va="bottom")
    pose_axis.text(0.0, -60.0,
                   "The same arrangement, seen edge on. The arm knows this pose\n"
                   "from its own joint encoders, and the examiner hands it over with\nthe two pictures.",
                   ha="center", va="top", fontsize=NOTE_SIZE, color=MUTED)

    titles(figure, axes, ["The grey picture", "The depth reading at every pixel", "The camera's pose"],
           heading="What a solution is given, and nothing else", lift=0.02)
    caption(figure,
            "All three come from one station looking at one arrangement, and all six solutions are handed the same "
            "three.\nA solution is given them; it does not fetch them, so no solution can quietly read anything "
            "else.")
    save(figure, "03-what-a-solution-is-given.png")


# --------------------------------------------------------------------------- #
# 4. what the examiner keeps to itself
# --------------------------------------------------------------------------- #


def what_the_bench_keeps() -> None:
    """The id picture, beside the grey picture, and the two jobs it does.

    The two jobs are worth keeping apart because they are allowed at different
    times. As the answer key it is used on every arrangement, after the answers
    are in. As a training label it may only be read from arrangements drawn with
    a seed below the dividing line.
    """
    ids, distance, _, extent, _ = overhead(IN_FRAME)
    figure, axes = new(11.4, 5.2, columns=3)
    # The two pictures are full of glasses, so what there is to say about them
    # is said underneath rather than in a box over the picture.
    figure.subplots_adjust(bottom=0.22, top=0.86, left=0.03, right=0.98)
    grey_axis, id_axis, jobs_axis = axes

    grey_axis.imshow(grey_of(distance), cmap="gray", vmin=0.0, vmax=1.0, origin="lower",
                     extent=extent, interpolation="nearest")
    bare(grey_axis)
    grey_axis.set_aspect("equal")

    shown = np.zeros(ids.shape + (4,), dtype=float)
    shown[...] = to_rgba(FAINT)
    for order, key in enumerate(sorted(IN_FRAME)):
        shown[ids == key] = ID_TINTS[order % len(ID_TINTS)]
    id_axis.imshow(shown, origin="lower", extent=extent, interpolation="nearest")
    bare(id_axis)
    id_axis.set_aspect("equal")
    for key in sorted(IN_FRAME):
        rows = np.argwhere(ids == key)
        y = rows[:, 0].mean() / (ids.shape[0] - 1) * (extent[3] - extent[2]) + extent[2]
        x = rows[:, 1].mean() / (ids.shape[1] - 1) * (extent[1] - extent[0]) + extent[0]
        id_axis.text(x, y, str(key), ha="center", va="center", fontsize=LABEL_SIZE,
                     color=INK, fontweight="bold", zorder=9)
    nothing = 100.0 * np.count_nonzero(ids == 0) / ids.size

    # ---- the two jobs, against the line that separates them
    bare(jobs_axis)
    jobs_axis.set_xlim(0.0, 1.0)
    jobs_axis.set_ylim(0.0, 1.0)
    jobs_axis.text(0.5, 0.97, "The examiner renders this picture beside every other one\n"
                              "and never gives it to a solution at run time.",
                   ha="center", va="top", fontsize=NOTE_SIZE, color=INK)
    jobs_axis.text(0.5, 0.84, "every arrangement, split by the number it was drawn with",
                   ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED)
    jobs_axis.add_patch(Rectangle((0.00, 0.62), 0.47, 0.15, facecolor=to_rgba(GOOD, 0.14),
                                  edgecolor=GOOD, linewidth=1.2))
    jobs_axis.add_patch(Rectangle((0.53, 0.62), 0.47, 0.15, facecolor=to_rgba(GLASS, 0.14),
                                  edgecolor=GLASS, linewidth=1.2))
    jobs_axis.plot([0.50, 0.50], [0.58, 0.81], color=INK, linewidth=1.4)
    jobs_axis.text(0.235, 0.695, f"seeds below {TEST_SEEDS:,}", ha="center", va="center",
                   fontsize=NOTE_SIZE - 0.4, color=INK)
    jobs_axis.text(0.765, 0.695, f"seeds from {TEST_SEEDS:,} up", ha="center", va="center",
                   fontsize=NOTE_SIZE - 0.4, color=INK)
    for x, colour in ((0.235, GOOD), (0.765, GLASS)):
        jobs_axis.annotate("", xy=(x, 0.54), xytext=(x, 0.62),
                           arrowprops={"arrowstyle": "->", "color": colour, "linewidth": 1.2})
    jobs_axis.text(0.235, 0.50, "As a training label.\nA method may be\nfitted on the id\npicture here, and\n"
                                "nowhere else.", ha="center", va="top", fontsize=NOTE_SIZE, color=GOOD)
    jobs_axis.text(0.765, 0.50, "As the answer key.\nThe bench marks\nwith it once the\nanswers are in. No\n"
                                "method is run on it.", ha="center", va="top",
                   fontsize=NOTE_SIZE, color=GLASS)
    jobs_axis.text(0.5, 0.17, "A method may be trained on id pictures and is never run on one.\n"
                              "Any method that read one while answering would not be answering\nthis problem.",
                   ha="center", va="top", fontsize=NOTE_SIZE, color=INK)

    titles(figure, axes, ["The grey picture again", "The id picture, which it keeps", "Its two separate jobs"],
           heading="What the examiner keeps to itself", lift=0.02)
    under(figure, axes, [
        "This one is handed to the solution.",
        f"Four glasses and the table: {nothing:.0f} per cent of\nthe pixels show no glass at all.",
        "",
    ], y=0.175)
    caption(figure,
            "The id picture is the same arrangement from the same station: at each pixel, which glass that pixel "
            "shows, or nothing.\nIt is the examiner's whole power, because knowing who owns each pixel is what lets it "
            "decide what a returned mask\nis really a picture of.")
    save(figure, "03-what-the-examiner-keeps.png")


# --------------------------------------------------------------------------- #
# 5. matching a report to a real glass
# --------------------------------------------------------------------------- #


def report_over_two(ids, top, want: float = 0.15):
    """A mask of glass 1 that has run onto the side of the taller glass 2.

    Built by taking all of glass 1 and then as much of glass 2, on the side
    facing glass 1, as makes ``want`` of the report. That side carries part of
    glass 2's rim, which is the highest thing in the mask, and the highest
    points are what the shared step takes the axis from. The share is kept
    under the one at which the examiner would call the two glasses merged, so the
    picture is about matching and not about that count.
    """
    rows, columns = np.nonzero(ids == 2)
    best = None
    for percentile in np.arange(99.0, 40.0, -0.5):
        keep = columns >= np.percentile(columns, percentile)
        share = keep.sum() / (np.count_nonzero(ids == 1) + keep.sum())
        if best is None or abs(share - want) < abs(best[1] - want):
            best = (keep, share)
    keep, _ = best
    report = ids == 1
    report[rows[keep], columns[keep]] = True
    return report


def matching_by_pixels() -> None:
    """Which real glass a report is talking about, decided by its pixels.

    The case drawn here is the one that makes the choice matter. The report's
    mask is plainly a picture of glass 1, but it has run onto a patch of the
    taller glass 2's rim, and that rim is the highest part of the cloud, so the
    shared step takes its axis from those few pixels and puts the glass a long
    way from where it stands. Matched by position the report would be credited
    to glass 2. Matched by pixels it is credited to glass 1, which is what it is
    a picture of.
    """
    ids, distance, top, extent, grid = overhead(NEIGHBOURS)
    report = report_over_two(ids, top)

    owned = ids[report]
    counts = {key: int(np.count_nonzero(owned == key)) for key in sorted(NEIGHBOURS)}
    on_a_glass = sum(counts.values())
    table = int(np.count_nonzero(owned == 0))
    shares = {key: value / on_a_glass for key, value in counts.items()}
    winner = max(shares, key=shares.get)
    other = min(shares, key=shares.get)

    axis_at, _ = place_and_width(report, top, grid)
    away = {key: float(np.linalg.norm(axis_at - centre)) for key, (centre, _) in NEIGHBOURS.items()}
    nearest = min(away, key=away.get)

    figure, axes = new(12.0, 5.6, columns=2)
    picture_axis, tally_axis = axes

    picture_axis.imshow(grey_of(distance), cmap="gray", vmin=0.0, vmax=1.0, origin="lower",
                        extent=extent, interpolation="nearest")
    bare(picture_axis)
    picture_axis.set_aspect("equal")
    picture_axis.contour(np.linspace(extent[0], extent[1], ids.shape[1]),
                         np.linspace(extent[2], extent[3], ids.shape[0]),
                         report.astype(float), levels=[0.5], colors=[WARN], linewidths=1.9)
    corners = {1: (extent[1] - 12.0, extent[2] + 12.0, "right", "bottom"),
               2: (extent[0] + 12.0, extent[3] - 12.0, "left", "top")}
    for key, (centre, _) in NEIGHBOURS.items():
        place = centre - MIDDLE
        picture_axis.plot(*place, marker="+", ms=10, mew=2.0, color=GOOD, zorder=9)
        x, y, ha, va = corners[key]
        pointer(picture_axis, f"glass {key} stands here", place, (x, y), colour=GOOD, ha=ha, va=va)
    computed = axis_at - MIDDLE
    picture_axis.plot(*computed, marker="x", ms=11, mew=2.2, color=WARN, zorder=10)
    pointer(picture_axis,
            f"the place this mask computes to,\n{away[winner]:.0f} mm from where glass {winner} stands",
            computed, (extent[0] + 12.0, extent[2] + 12.0), colour=WARN, ha="left", va="bottom")
    note(picture_axis, extent[1] - 12.0, extent[3] - 12.0,
         "the red outline is one report's mask, and the\nsliver down the side of glass 2 is part of it",
         colour=WARN, ha="right", va="top")

    # ---- what the id picture says those pixels are
    bare(tally_axis)
    tally_axis.set_xlim(0.0, 1.0)
    tally_axis.set_ylim(0.0, 1.0)
    tally_axis.text(0.0, 0.97, "Of the report's pixels that belong to a glass at all,\n"
                               "how many each real glass owns:",
                    ha="left", va="top", fontsize=NOTE_SIZE, color=INK)
    for index, key in enumerate(sorted(shares)):
        colour = GOOD if key == winner else GLASS
        y = 0.78 - index * 0.13
        tally_axis.add_patch(Rectangle((0.16, y), 0.56 * shares[key], 0.08,
                                       facecolor=to_rgba(colour, 0.75), edgecolor="none"))
        tally_axis.add_patch(Rectangle((0.16, y), 0.56, 0.08, facecolor="none",
                                       edgecolor=MUTED, linewidth=0.8))
        tally_axis.text(0.14, y + 0.04, f"glass {key}", ha="right", va="center",
                        fontsize=NOTE_SIZE, color=INK)
        tally_axis.text(0.74, y + 0.04, f"{100 * shares[key]:.0f} per cent", ha="left",
                        va="center", fontsize=NOTE_SIZE, color=colour)
    tally_axis.text(0.0, 0.50,
                    f"The majority owner is glass {winner}, so glass {winner} is what this report is about.\n"
                    f"A further {table} of its pixels are bare table, and they count towards neither.\n\n"
                    f"Matched by position instead, the computed place is {away[nearest]:.0f} mm from glass "
                    f"{nearest}\nand {away[winner]:.0f} mm from glass {winner}, so the report would have been "
                    f"credited to glass {nearest},\nwhich it is not a picture of. Matching by pixels still works "
                    "when a method is\nbadly wrong about where the glass stands, and that is why the examiner "
                    "matches\nthat way.\n\n"
                    f"Glass {other} holds {100 * shares[other]:.0f} per cent of this report, under the "
                    f"{100 * MERGED_SHARE:.0f} per cent at which the examiner\nwould have counted the two of them "
                    "merged into one report instead.",
                    ha="left", va="top", fontsize=NOTE_SIZE, color=INK)

    titles(figure, axes, ["One report, drawn over the grey picture", "What the id picture says those pixels are"],
           heading="How a report is matched to a real glass", lift=0.02)
    caption(figure,
            f"The place comes from the examiner's own shared step, which takes the axis from the points within "
            f"{RIM_BAND:.0f} mm of "
            "the highest point in the mask. The few\npixels of the taller glass's rim are the highest points in "
            "this mask, so they drag the place onto the neighbour while the mask itself stays\nplainly glass 1.")
    save(figure, "03-matching-by-pixels.png")


# --------------------------------------------------------------------------- #
# 6. the two numbers the examiner measures per mask
# --------------------------------------------------------------------------- #


def stemmed_view(out_by: float = STEMMED_OUT_BY):
    """One stemmed glass as the overhead camera sees it, and which part is bowl.

    Built from the cell's own stemmed outline, at the size in ``STEMMED``.

    It stands ``out_by`` millimetres out from the point below the camera, and
    that distance is the largest one the picture allows. Further out and the
    bowl, which is thrown out by 450 / (450 - 210), leaves the frame; nearer in
    and the foot hides under the bowl and there is nothing for a mask to lose.
    Seen from above, a stem is never a band of its own: the bowl is thrown out
    over it. What a mask of the bowl alone misses is the foot, and the sliver of
    stem beside it, which is the thin part of a stemmed glass as an overhead
    picture has it.

    The canvas is a crop of the station's own picture, at that picture's pixel
    size, so the pixels counted below are the size the examiner counts.
    """
    outline = build("stemmed_glass", **STEMMED)
    direction = np.array([-0.88, -0.48])
    direction = direction / np.linalg.norm(direction)
    stacked = stack_of_outline(np.zeros(2), direction * out_by, outline)

    xs = [c[0] - r for c, r, _ in stacked] + [c[0] + r for c, r, _ in stacked]
    ys = [c[1] - r for c, r, _ in stacked] + [c[1] + r for c, r, _ in stacked]
    if max(map(abs, xs)) > PICTURE[0] / 2.0 or max(map(abs, ys)) > PICTURE[1] / 2.0:
        raise SystemExit(f"a stemmed glass {out_by:.0f} mm out has part of its outline outside "
                         "the picture, so no station ever sees it whole")
    pad = 42.0
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    grid_x, grid_y = np.meshgrid(np.arange(x0, x1, PIXEL_MM), np.arange(y0, y1, PIXEL_MM))

    truth = np.zeros(grid_x.shape, dtype=bool)
    top = np.zeros(grid_x.shape)
    for c, r, z in stacked:
        inside = (grid_x - c[0]) ** 2 + (grid_y - c[1]) ** 2 <= r * r
        truth |= inside
        nearer = inside & (z > top)
        top[nearer] = z
    bowl = truth & (top >= STEMMED["stem_fraction"] * STEMMED["height"] * 1000.0)
    return truth, bowl, (x0, grid_x.max(), y0, grid_y.max())


def mask_numbers(mine, truth):
    """The examiner's two fractions, computed as bench/scoring.py mask() computes them."""
    whole = np.count_nonzero(truth)
    on_it = np.count_nonzero(mine & truth)
    return on_it / whole, (np.count_nonzero(mine) - on_it) / np.count_nonzero(mine)


def coarse_outline(truth, *, grow=3, shift=(2, 2)):
    """A learned outline: the shape followed coarsely, and sitting a little outside.

    Rounding the silhouette off is what a learned outline does to a part a few
    pixels wide, and the shift is its edge sitting a little off the glass. The
    first adds pixels that are not the glass, and the second both adds some and
    costs a little coverage on the side it moves away from. That pair of habits
    is what the two numbers tell apart.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1))
    rounded = cv2.morphologyEx(truth.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    rounded = cv2.dilate(rounded, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    moved = np.zeros_like(rounded)
    dy, dx = shift
    moved[dy:, dx:] = rounded[: rounded.shape[0] - dy, : rounded.shape[1] - dx]
    return moved.astype(bool)


def draw_mask_panel(axis, truth, mine, extent) -> None:
    """The real glass, the mask over it, and the two places they disagree."""
    shown = np.zeros(truth.shape + (4,), dtype=float)
    shown[...] = to_rgba(PAPER)
    shown[truth] = to_rgba(GLASS, 0.32)
    shown[truth & ~mine] = to_rgba(WARN, 0.60)
    shown[mine & ~truth] = to_rgba(WARN, 0.60)
    axis.imshow(shown, origin="lower", extent=extent, interpolation="nearest")
    axis.contour(np.linspace(extent[0], extent[1], truth.shape[1]),
                 np.linspace(extent[2], extent[3], truth.shape[0]),
                 mine.astype(float), levels=[0.5], colors=[INK], linewidths=1.2)
    bare(axis)
    axis.set_aspect("equal")
    axis.set_xlim(extent[0], extent[1])
    axis.set_ylim(extent[2], extent[3])


def the_two_mask_numbers() -> None:
    """Covered, and not the glass, on the two cases the document names.

    A rule written by hand keeps only the pixels it is sure about, so it loses
    the thin stem: coverage falls and nothing leaks. A learned outline follows
    the shape coarsely and sits a little outside the glass: coverage stays high
    and a thin margin of the mask is not the glass. Either number alone would
    call one of these two solutions the better one; the pair of them says what
    each actually did.
    """
    truth, bowl, extent = stemmed_view()
    drawn = {"rule": mask_numbers(bowl, truth), "fitted": mask_numbers(coarse_outline(truth), truth)}

    figure, axes = new(11.0, 7.0, columns=2)
    figure.subplots_adjust(bottom=0.34, top=0.90, left=0.06, right=0.96)
    left, right = axes
    draw_mask_panel(left, truth, bowl, extent)
    draw_mask_panel(right, truth, coarse_outline(truth), extent)

    pointer(left, "the foot, and the stem it carries, are not in\nthe mask, so coverage falls and nothing leaks",
            (extent[0] + (extent[1] - extent[0]) * 0.62, extent[2] + (extent[3] - extent[2]) * 0.74),
            (extent[0] + 6.0, extent[2] + 6.0), colour=WARN, ha="left", va="bottom")
    pointer(right, "the outline is rounded off and sits a little\noutside the glass, so a thin margin of the\n"
                   "mask is not the glass",
            (extent[0] + (extent[1] - extent[0]) * 0.30, extent[2] + (extent[3] - extent[2]) * 0.30),
            (extent[0] + 6.0, extent[2] + 6.0), colour=WARN, ha="left", va="bottom")

    under(figure, axes, [
        f"In this picture the mask covers {100 * drawn['rule'][0]:.0f} per cent of the glass,\n"
        f"and {100 * drawn['rule'][1]:.0f} per cent of the mask is not the glass.\n"
        f"Over the test arrangements a rule written by hand covered\n"
        f"{RULE_STEMMED[0]} per cent of a stemmed glass, with {RULE_STEMMED[1]} per cent not the glass.",
        f"In this picture the mask covers {100 * drawn['fitted'][0]:.0f} per cent of the glass,\n"
        f"and {100 * drawn['fitted'][1]:.0f} per cent of the mask is not the glass.\n"
        f"Over the test arrangements a model fitted on this cell covered\n"
        f"{FITTED_STEMMED[0]} per cent of a stemmed glass, with {FITTED_STEMMED[1]} per cent not the glass.",
    ], y=0.300)

    swatches = ((to_rgba(GLASS, 0.32), "the glass, and in the mask"),
                (to_rgba(WARN, 0.60), "the glass and not in the mask, or in the mask and not the glass"))
    for index, (colour, label) in enumerate(swatches):
        x = 0.15 + index * 0.27
        figure.patches.append(Rectangle((x, 0.135), 0.014, 0.018, facecolor=colour, edgecolor=MUTED,
                                        linewidth=0.6, transform=figure.transFigure, figure=figure))
        figure.text(x + 0.020, 0.144, label, ha="left", va="center", fontsize=NOTE_SIZE, color=INK)

    titles(figure, axes, ["A rule written by hand", "An outline a model learned"],
           heading="The two numbers the examiner measures for every mask", lift=0.02)
    caption(figure,
            "One stemmed glass, 210 mm tall with an 8 mm stem, standing 95 mm to the side of the point below the "
            "camera. The bowl is thrown further out\nthan the foot, so the foot shows beside it rather than under "
            "it, and that crescent of foot and stem is the thin part a mask can lose. Coverage alone\nwould prefer "
            "the model and leakage alone would prefer the rule, which is why the examiner reports both.", y=0.005)
    save(figure, "03-the-two-mask-numbers.png")


def main() -> None:
    ordinary_family()
    crowded_family()
    three_stations()
    what_a_solution_is_given()
    what_the_bench_keeps()
    matching_by_pixels()
    the_two_mask_numbers()


if __name__ == "__main__":
    main()
