"""Generate the diagrams used in docs/06_learned-models/05_grasp-models/.

Each document's pictures go to a folder named after it, under
docs/images/grasp-models/.

Every picture is a drawing of one idea from its document: a grasp rectangle on
a depth picture, the three maps a GG-CNN-style network paints, a point cloud
whose points each propose a grip, a suction cup that seals or leaks, and so on.
No picture shows a measured result, so no picture carries a number that a
reader could mistake for one. The scores printed next to candidate grips are
made up for the drawing and the documents say so.

Run with:  python3 docs/diagrams/grasp_models.py
      or:  pixi run python ../docs/diagrams/grasp_models.py   (from code/)
Add --png <dir> to also write PNG copies for checking.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'grasp-models'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as docs/diagrams/arm_types.py.
GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b6fd1'

# A few extra names for this area, built from the palette above.
GOOD: str = SLIDE          # a grip that is kept or that held
BAD: str = GRIP            # a grip that is rejected or that failed
OBJ: str = LINK_PALE       # the fill of an object
OBJ_EDGE: str = LINK       # the outline of an object
HAND: str = '#555555'      # the gripper itself
TABLE: str = '#bbbbbb'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, style: str = '-|>', z: int = 8) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=z)


def _tick(ax: Axes, x: float, y: float, size: float = 0.25) -> None:
    ax.plot([x - size, x - size * 0.3, x + size], [y, y - size * 0.7, y + size * 0.8],
            color=GOOD, lw=3, solid_capstyle='round', zorder=9)


def _cross(ax: Axes, x: float, y: float, size: float = 0.2) -> None:
    ax.plot([x - size, x + size], [y - size, y + size], color=BAD, lw=3,
            solid_capstyle='round', zorder=9)
    ax.plot([x - size, x + size], [y + size, y - size], color=BAD, lw=3,
            solid_capstyle='round', zorder=9)


def _rot(v: tuple[float, float], ang: float) -> tuple[float, float]:
    c, s = math.cos(ang), math.sin(ang)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _mug_top(ax: Axes, c: tuple[float, float], r: float, handle: float = 0.0,
             z: int = 3) -> None:
    """A mug seen from above: a ring, the dark inside, and a handle."""
    hx, hy = math.cos(handle), math.sin(handle)
    px, py = -hy, hx
    w = r * 0.28
    base = (c[0] + hx * r * 0.9, c[1] + hy * r * 0.9)
    tip = (c[0] + hx * r * 1.55, c[1] + hy * r * 1.55)
    corners = [(base[0] + px * w, base[1] + py * w), (tip[0] + px * w, tip[1] + py * w),
               (tip[0] - px * w, tip[1] - py * w), (base[0] - px * w, base[1] - py * w)]
    ax.add_patch(Polygon(corners, closed=True, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.4,
                         zorder=z))
    ax.add_patch(Circle(c, r, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6, zorder=z + 1))
    ax.add_patch(Circle(c, r * 0.78, facecolor='#8fb3d6', edgecolor=OBJ_EDGE, lw=1.0,
                        zorder=z + 1))


def _mug_side(ax: Axes, x0: float, y0: float, w: float, h: float, z: int = 3,
              handle: bool = True) -> None:
    """A mug seen from the side: a body and a handle loop on the right."""
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=z))
    if handle:
        ax.add_patch(Arc((x0 + w, y0 + h * 0.55), w * 0.55, h * 0.55, theta1=-90,
                         theta2=90, color=OBJ_EDGE, lw=5, zorder=z - 1))


def _grasp_rect(ax: Axes, c: tuple[float, float], ang: float, width: float,
                jaw: float = 0.35, color: str = GOOD, lw: float = 2.0,
                alpha: float = 1.0, z: int = 6) -> None:
    """A grasp rectangle seen from above: two jaw plates and the line between them.

    `ang` is the closing direction, `width` the opening between the jaws and
    `jaw` the length of each jaw plate.
    """
    d = _rot((width / 2, 0), ang)
    n = _rot((0, jaw / 2), ang)
    corners = [(c[0] - d[0] - n[0], c[1] - d[1] - n[1]), (c[0] + d[0] - n[0], c[1] + d[1] - n[1]),
               (c[0] + d[0] + n[0], c[1] + d[1] + n[1]), (c[0] - d[0] + n[0], c[1] - d[1] + n[1])]
    ax.add_patch(Polygon(corners, closed=True, fill=False, edgecolor=color, lw=lw * 0.6,
                         ls='--', alpha=alpha, zorder=z))
    for side in (1, -1):
        e = (c[0] + side * d[0], c[1] + side * d[1])
        ax.plot([e[0] - n[0], e[0] + n[0]], [e[1] - n[1], e[1] + n[1]], color=color,
                lw=lw * 2.4, solid_capstyle='butt', alpha=alpha, zorder=z + 1)


def _gripper_side(ax: Axes, tip: tuple[float, float], approach: float, opening: float,
                  finger: float = 0.7, color: str = HAND, lw: float = 4.0,
                  alpha: float = 1.0, z: int = 6, wrist: float = 0.5) -> None:
    """A two-finger gripper drawn from the side of its closing direction.

    `tip` is the point midway between the fingertips, `approach` the direction
    (radians) the gripper travels in as it closes in on the object, and
    `opening` the gap between the fingers.
    """
    a = (math.cos(approach), math.sin(approach))
    n = (-a[1], a[0])
    palm = (tip[0] - a[0] * finger, tip[1] - a[1] * finger)
    half = opening / 2
    for side in (1, -1):
        root = (palm[0] + side * n[0] * half, palm[1] + side * n[1] * half)
        end = (tip[0] + side * n[0] * half, tip[1] + side * n[1] * half)
        ax.plot([root[0], end[0]], [root[1], end[1]], color=color, lw=lw, alpha=alpha,
                solid_capstyle='round', zorder=z)
    pa = (palm[0] + n[0] * (half + 0.06), palm[1] + n[1] * (half + 0.06))
    pb = (palm[0] - n[0] * (half + 0.06), palm[1] - n[1] * (half + 0.06))
    ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=color, lw=lw * 1.3, alpha=alpha,
            solid_capstyle='round', zorder=z)
    back = (palm[0] - a[0] * wrist, palm[1] - a[1] * wrist)
    ax.plot([palm[0], back[0]], [palm[1], back[1]], color=color, lw=lw * 1.8, alpha=alpha,
            solid_capstyle='butt', zorder=z)


def _gripper_edge_on(ax: Axes, tip: tuple[float, float], approach: float,
                     finger: float = 0.7, color: str = HAND, lw: float = 4.0,
                     wrist: float = 0.5, z: int = 7) -> None:
    """A two-finger gripper whose fingers close in and out of the page.

    Seen this way the two fingers lie one behind the other, so only one shows.
    """
    a = (math.cos(approach), math.sin(approach))
    n = (-a[1], a[0])
    palm = (tip[0] - a[0] * finger, tip[1] - a[1] * finger)
    ax.plot([palm[0], tip[0]], [palm[1], tip[1]], color=color, lw=lw, solid_capstyle='round',
            zorder=z)
    pa = (palm[0] + n[0] * 0.18, palm[1] + n[1] * 0.18)
    pb = (palm[0] - n[0] * 0.18, palm[1] - n[1] * 0.18)
    ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=color, lw=lw * 2.6, solid_capstyle='butt',
            zorder=z)
    back = (palm[0] - a[0] * wrist, palm[1] - a[1] * wrist)
    ax.plot([palm[0], back[0]], [palm[1], back[1]], color=color, lw=lw * 1.8,
            solid_capstyle='butt', zorder=z)


def _suction(ax: Axes, tip: tuple[float, float], approach: float = -math.pi / 2,
             size: float = 0.35, color: str = HAND, z: int = 6) -> None:
    """A suction cup on a tube, drawn from the side, mouth at `tip`."""
    a = (math.cos(approach), math.sin(approach))
    n = (-a[1], a[0])
    neck = (tip[0] - a[0] * size * 0.8, tip[1] - a[1] * size * 0.8)
    cup = [(tip[0] + n[0] * size, tip[1] + n[1] * size),
           (tip[0] - n[0] * size, tip[1] - n[1] * size),
           (neck[0] - n[0] * size * 0.25, neck[1] - n[1] * size * 0.25),
           (neck[0] + n[0] * size * 0.25, neck[1] + n[1] * size * 0.25)]
    ax.add_patch(Polygon(cup, closed=True, facecolor=JOINT, edgecolor=INK, lw=1.0, zorder=z))
    top = (neck[0] - a[0] * size * 2.2, neck[1] - a[1] * size * 2.2)
    ax.plot([neck[0], top[0]], [neck[1], top[1]], color=color, lw=6, solid_capstyle='butt',
            zorder=z - 1)


def _table(ax: Axes, x0: float, x1: float, y: float = 0.0) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.4, zorder=1)
    for x in np.arange(x0 + 0.1, x1, 0.3):
        ax.plot([x, x - 0.15], [y, y - 0.15], color=GRID, lw=1.0, zorder=1)


def _network(ax: Axes, x0: float, y0: float, w: float, h: float,
             layers: tuple[int, ...] = (4, 5, 5, 2), color: str = LINK) -> None:
    """A small drawing of a neural network: columns of circles joined by lines."""
    xs = np.linspace(x0, x0 + w, len(layers))
    pts: list[list[tuple[float, float]]] = []
    for x, n in zip(xs, layers):
        ys = np.linspace(y0 + h * 0.1, y0 + h * 0.9, n) if n > 1 else [y0 + h / 2]
        pts.append([(float(x), float(y)) for y in ys])
    for left, right in zip(pts, pts[1:]):
        for p in left:
            for q in right:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRID, lw=0.7, zorder=2)
    for col in pts:
        for p in col:
            ax.add_patch(Circle(p, h * 0.045, facecolor='white', edgecolor=color, lw=1.4,
                                zorder=3))


def _depth_image(size: int, objects: list[tuple[str, tuple[float, float], float, float]],
                 table: float = 1.0) -> NDArray[np.float64]:
    """A small fake depth picture seen from above: table far, objects nearer.

    Each object is (kind, centre, radius or half-size, height). Pixel values are
    distance from the camera, so a tall object is a small number.
    """
    yy, xx = np.mgrid[0:size, 0:size]
    img = np.full((size, size), table)
    for kind, c, r, h in objects:
        if kind == 'disc':
            m = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r ** 2
        else:
            m = (abs(xx - c[0]) <= r) & (abs(yy - c[1]) <= r * 0.7)
        img[m] = np.minimum(img[m], table - h)
    return img


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 01_overview.md
# --------------------------------------------------------------------------

def four_answers() -> None:
    """The four kinds of answer a grasp model gives, one per subcategory page."""
    fig, axes = _panels(4, (17.5, 5.2))
    for ax in axes:
        _axes(ax, (0, 4), (-0.9, 4.1))

    # 1. a rectangle on a picture seen from above
    ax = axes[0]
    ax.add_patch(Rectangle((0.2, 0.2), 3.6, 3.2, facecolor='#eeeeee', edgecolor=MUTED, lw=1))
    _mug_top(ax, (1.9, 1.8), 0.75, handle=math.radians(-20))
    _grasp_rect(ax, (1.9, 1.8), math.radians(60), 1.9)
    _title(ax, 2, 3.85, 'A rectangle on a picture')
    _caption(ax, 2, -0.3, 'top-down grasp detection:\nwhere to close, straight down')

    # 2. a full pose in space
    ax = axes[1]
    _table(ax, 0.2, 3.8, 0.4)
    _mug_side(ax, 1.3, 0.4, 1.0, 1.4)
    _gripper_side(ax, (2.6, 1.17), math.radians(180), 0.6, finger=0.55, color=GOOD,
                  wrist=0.4)
    _label(ax, 3.3, 2.0, 'from the side,\non the handle', size=10, color=GOOD)
    _title(ax, 2, 3.85, 'A full pose in 3D')
    _caption(ax, 2, -0.3, 'six-degree-of-freedom grasps:\nwhere, and from which direction')

    # 3. a spot to suck, and a part to hold
    ax = axes[2]
    ax.add_patch(Rectangle((0.2, 0.2), 3.6, 3.2, facecolor='#eeeeee', edgecolor=MUTED, lw=1))
    ax.add_patch(Rectangle((0.7, 0.8), 2.6, 1.9, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    for r, a in ((0.75, 0.25), (0.5, 0.45), (0.28, 0.8)):
        ax.add_patch(Ellipse((2.0, 1.75), r * 2.2, r * 1.6, facecolor=GOOD, alpha=a,
                             lw=0, zorder=4))
    ax.plot([2.0], [1.75], marker='*', color=INK, ms=15, zorder=6)
    _title(ax, 2, 3.85, 'A spot to suck')
    _caption(ax, 2, -0.3, 'suction and affordance:\nwhich patch seals, which part to hold')

    # 4. a score for one candidate grip
    ax = axes[3]
    ax.add_patch(Rectangle((0.2, 0.2), 3.6, 3.2, facecolor='#eeeeee', edgecolor=MUTED, lw=1))
    _mug_top(ax, (1.7, 1.8), 0.75, handle=math.radians(-20))
    _grasp_rect(ax, (1.7, 1.8), math.radians(90), 1.9, color=LINK)
    ax.add_patch(FancyBboxPatch((2.75, 2.55), 0.9, 0.5, boxstyle='round,pad=0.05',
                                facecolor='white', edgecolor=LINK, lw=1.4, zorder=8))
    _label(ax, 3.2, 2.8, '0.91', size=13, color=LINK, weight='bold')
    _title(ax, 2, 3.85, 'A score for one grip')
    _caption(ax, 2, -0.3, 'grasp quality models:\nhow likely is this grip to hold?')
    _save(fig, 'overview', 'four-answers.svg')


def did_it_hold() -> None:
    """The one training label every grasp model shares: did the object stay held."""
    fig, axes = _panels(3, (15, 5.2))
    cases = [('lifted, still held', True), ('lifted, fell out', False),
             ('lifted, still held', True)]
    for ax, (text, held) in zip(axes, cases):
        _axes(ax, (0, 4), (-1.2, 4.2))
        _table(ax, 0.2, 3.8, 0.3)
        if held:
            _mug_side(ax, 1.5, 1.8, 0.9, 1.1)
            _gripper_side(ax, (1.95, 2.35), math.radians(-90), 1.0, finger=0.8)
            _arrow(ax, (0.6, 1.4), (0.6, 2.6), color=MUTED)
            _label(ax, 0.6, 1.15, 'lift', color=MUTED)
            _tick(ax, 3.3, 2.4)
            _label(ax, 2, -0.35, 'label = 1', size=13, color=GOOD, weight='bold')
        else:
            poly = [(1.3, 0.3), (2.4, 0.3), (2.4, 1.2), (1.3, 1.2)]
            ax.add_patch(Polygon(poly, closed=True, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                                 zorder=3))
            ax.add_patch(Arc((1.3, 0.75), 0.5, 0.55, theta1=90, theta2=270, color=OBJ_EDGE,
                             lw=5, zorder=2))
            _gripper_side(ax, (1.95, 2.35), math.radians(-90), 1.0, finger=0.8)
            _arrow(ax, (0.6, 1.4), (0.6, 2.6), color=MUTED)
            _label(ax, 0.6, 1.15, 'lift', color=MUTED)
            _cross(ax, 3.3, 2.4)
            _label(ax, 2, -0.35, 'label = 0', size=13, color=BAD, weight='bold')
        _caption(ax, 2, 3.95, text, size=11.5)
    fig.suptitle('Every attempt is saved with one number: 1 if the object stayed in the '
                 'gripper, 0 if it fell', fontsize=13, weight='bold', y=1.0)
    _save(fig, 'overview', 'did-it-hold.svg')


# --------------------------------------------------------------------------
# 02_top-down-grasp-detection.md
# --------------------------------------------------------------------------

def grasp_rectangle() -> None:
    """What one grasp rectangle means, from above and from the side."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    _axes(ax, (-0.3, 5.3), (-0.6, 5.0))
    for i in range(11):
        ax.plot([0, 5], [i * 0.45, i * 0.45], color=GRID, lw=0.6, zorder=1)
        ax.plot([i * 0.5, i * 0.5], [0, 4.5], color=GRID, lw=0.6, zorder=1)
    c = (2.3, 2.2)
    ang = math.radians(35)
    _mug_top(ax, c, 0.9, handle=math.radians(-60))
    _grasp_rect(ax, c, ang, 2.3, jaw=0.7)
    ax.plot([c[0]], [c[1]], 'o', color=INK, ms=7, zorder=10)
    _label(ax, c[0] - 0.5, c[1] + 0.2, 'centre\n(x, y)', size=10.5, ha='right')
    # angle arc against the picture's horizontal
    ax.plot([c[0], c[0] + 1.9], [c[1], c[1]], color=MUTED, lw=1, ls=':', zorder=7)
    ax.add_patch(Arc(c, 2.4, 2.4, theta1=0, theta2=35, color=JOINT, lw=2, zorder=8))
    _label(ax, c[0] + 1.55, c[1] + 0.4, 'angle', size=10.5, color=WRIST, ha='left')
    # width dimension line, beside the rectangle
    d = _rot((1.15, 0), ang)
    off = _rot((0, -0.62), ang)
    p1 = (c[0] - d[0] + off[0], c[1] - d[1] + off[1])
    p2 = (c[0] + d[0] + off[0], c[1] + d[1] + off[1])
    _arrow(ax, p1, p2, color=LINK, style='<|-|>')
    _label(ax, p1[0] - 0.2, p1[1] - 0.35, 'opening width', size=10.5, color=LINK,
           ha='left')
    e = (c[0] + d[0], c[1] + d[1])
    _label(ax, e[0] + 0.35, e[1] + 0.3, 'jaw', size=10.5, color=GOOD, ha='left')
    _title(ax, 2.5, 4.8, 'Seen from above: four numbers on the picture')

    ax = axes[1]
    _axes(ax, (0, 4.5), (-0.6, 5.0))
    _table(ax, 0.2, 4.3, 0.3)
    _mug_side(ax, 1.55, 0.3, 1.2, 1.5)
    _gripper_side(ax, (2.15, 1.4), math.radians(-90), 1.45, finger=0.9, wrist=0.8)
    ax.plot([2.15, 2.15], [3.2, 4.2], color=AXIS_Z, lw=1.2, ls='--', zorder=2)
    ax.add_patch(Rectangle((1.85, 4.2), 0.6, 0.3, facecolor=INK, zorder=3))
    _label(ax, 2.6, 4.35, 'camera', ha='left')
    _arrow(ax, (3.6, 3.6), (3.6, 2.4), color=AXIS_Z)
    _label(ax, 3.6, 2.15, 'always\nstraight down', size=10.5, color=AXIS_Z)
    _title(ax, 2.25, 4.8, 'Seen from the side: the approach is fixed')
    _save(fig, 'top-down-grasp-detection', 'grasp-rectangle.svg')


def three_maps() -> None:
    """A GG-CNN-style network paints a quality, an angle and a width for every pixel."""
    n = 40
    mug_c, mug_r = (17.0, 21.0), 8.0
    box_c, box_r = (32.0, 9.0), 5.0
    depth = _depth_image(n, [('disc', mug_c, mug_r, 0.35), ('box', box_c, box_r, 0.15)])
    yy, xx = np.mgrid[0:n, 0:n]
    q = 0.95 * np.exp(-(((xx - mug_c[0]) ** 2 + (yy - mug_c[1]) ** 2) / (2 * 2.6 ** 2)))
    q += 0.6 * np.exp(-(((xx - box_c[0]) ** 2 + ((yy - box_c[1]) / 0.6) ** 2) / (2 * 2.2 ** 2)))
    ang = np.where(depth < 0.9, math.pi / 3, np.nan)
    ang = np.where((abs(xx - box_c[0]) <= box_r) & (abs(yy - box_c[1]) <= box_r * 0.7),
                   math.pi / 2, ang)
    width = np.where(depth < 0.9, 0.3, np.nan)
    width = np.where(((xx - mug_c[0]) ** 2 + (yy - mug_c[1]) ** 2) <= mug_r ** 2, 0.85, width)
    best = np.unravel_index(np.nanargmax(q), q.shape)

    fig, axes = _panels(4, (17, 5.0))
    shows = [(depth, 'Greys_r', 'depth picture (in)', 'darker = nearer the camera'),
             (q, 'Greens', 'quality map (out)', 'how good a grip centred here is'),
             (ang, 'twilight', 'angle map (out)', 'which way the jaws close (arrows)'),
             (width, 'Blues', 'width map (out)', 'how far to open')]
    for ax, (img, cmap, title, cap) in zip(axes, shows):
        ax.imshow(img, cmap=cmap, origin='lower', interpolation='nearest',
                  vmin={'Greys_r': 0.3, 'twilight': 0.0}.get(cmap, 0.0),
                  vmax={'Greys_r': 1.1, 'twilight': math.pi}.get(cmap, 1.0))
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(MUTED)
        ax.set_title(title, fontsize=12.5, weight='bold', color=INK, pad=8)
        ax.set_xlabel(cap, fontsize=10.5, color=MUTED, labelpad=8)
        ax.plot([best[1]], [best[0]], marker='+', color=BAD, ms=18, mew=2.5)
    # the angle map uses arrows as well as colour so it does not rely on hue alone
    for y in range(3, n, 5):
        for x in range(3, n, 5):
            a = ang[y, x]
            if not np.isnan(a):
                axes[2].annotate('', xy=(x + 1.8 * math.cos(a), y + 1.8 * math.sin(a)),
                                 xytext=(x - 1.8 * math.cos(a), y - 1.8 * math.sin(a)),
                                 arrowprops={'arrowstyle': '<|-|>', 'color': INK, 'lw': 1.2,
                                             'mutation_scale': 8})
    fig.suptitle('One pass of the network fills in three numbers for every pixel. '
                 'The red cross is the pixel with the best quality.', fontsize=12.5,
                 y=1.04, color=INK)
    _save(fig, 'top-down-grasp-detection', 'three-maps.svg')


def straight_down_only() -> None:
    """A rectangle can only describe a grip that comes straight down."""
    fig, axes = _panels(2, (13, 5.6))
    for ax in axes:
        _axes(ax, (0, 5), (-0.9, 4.6))

    ax = axes[0]
    ax.plot([0.5, 0.5, 4.5, 4.5], [2.6, 0.4, 0.4, 2.6], color=MUTED, lw=3, zorder=2)
    ax.add_patch(Rectangle((1.9, 0.4), 1.2, 0.6, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    _gripper_side(ax, (2.5, 0.75), math.radians(-90), 1.45, finger=0.8, color=GOOD)
    _tick(ax, 3.9, 3.4)
    _title(ax, 2.5, 4.3, 'A box lying flat in a bin')
    _caption(ax, 2.5, -0.45, 'straight down works, so a rectangle can describe it')

    ax = axes[1]
    # a shelf: floor, a board above, a back wall; open on the left
    ax.plot([0.3, 4.5, 4.5], [0.4, 0.4, 2.0], color=MUTED, lw=3, zorder=2)
    ax.add_patch(Rectangle((0.3, 2.0), 4.2, 0.18, facecolor=TABLE, edgecolor=MUTED, lw=1.5,
                           zorder=4))
    ax.add_patch(Rectangle((2.9, 0.4), 0.7, 1.2, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    _gripper_side(ax, (3.25, 2.55), math.radians(-90), 0.9, finger=0.5, color=BAD, wrist=0.4)
    _cross(ax, 4.1, 3.4)
    _label(ax, 1.35, 3.1, 'straight down:\nthe shelf board is in the way', size=10.5,
           color=BAD)
    _gripper_edge_on(ax, (3.25, 1.0), math.radians(0), finger=0.75, color=GOOD, wrist=0.8)
    _tick(ax, 4.05, 1.3, size=0.2)
    _label(ax, 1.4, 1.45, 'from the front', size=10.5, color=GOOD)
    _title(ax, 2.5, 4.3, 'A box on a shelf')
    _caption(ax, 2.5, -0.45, 'only a sideways grip fits, and a rectangle cannot describe it')
    _save(fig, 'top-down-grasp-detection', 'straight-down-only.svg')


# --------------------------------------------------------------------------
# 03_six-dof-grasps.md
# --------------------------------------------------------------------------

def many_directions() -> None:
    """A six-number grasp can come from any direction; a rectangle only from above."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor='white',
                             gridspec_kw={'width_ratios': [1.1, 1]})
    ax = axes[0]
    _axes(ax, (0, 5), (-0.7, 5.0))
    _table(ax, 0.2, 4.8, 0.4)
    _mug_side(ax, 1.7, 0.4, 1.3, 1.8)
    _gripper_side(ax, (1.72, 1.95), math.radians(-90), 0.32, finger=0.55, color=MUTED,
                  lw=3.4, wrist=0.4)
    _label(ax, 1.72, 3.35, 'from above,\npinching the rim', size=10, color=MUTED)
    _gripper_edge_on(ax, (2.35, 1.1), math.radians(0), finger=0.7, color=GOOD, wrist=0.6)
    _label(ax, 0.75, 0.75, 'from the side,\nround the body', size=10, color=GOOD)
    _gripper_side(ax, (3.3, 1.45), math.radians(-150), 0.45, finger=0.5, color=LINK, lw=3.4,
                  wrist=0.4)
    _label(ax, 4.3, 2.55, 'tilted, on\nthe handle', size=10, color=LINK)
    _title(ax, 2.5, 4.75, 'Three grips on one mug, from three directions')

    ax = axes[1]
    _axes(ax, (0, 4.6), (-0.7, 5.0))
    tip = (2.3, 1.6)
    approach = math.radians(-60)
    _gripper_side(ax, tip, approach, 1.1, finger=0.9, wrist=0.8)
    ax.plot([tip[0]], [tip[1]], 'o', color=INK, ms=8, zorder=10)
    _label(ax, tip[0] + 0.25, tip[1] - 0.45, 'position: x, y, z', size=11, ha='left')
    a = (math.cos(approach), math.sin(approach))
    n = (-a[1], a[0])
    s0 = (tip[0] - a[0] * 2.6 - n[0] * 0.75, tip[1] - a[1] * 2.6 - n[1] * 0.75)
    s1 = (tip[0] - a[0] * 1.4 - n[0] * 0.75, tip[1] - a[1] * 1.4 - n[1] * 0.75)
    _arrow(ax, s0, s1, color=AXIS_Z, lw=2.2)
    _label(ax, s0[0] + 0.2, s0[1] + 0.3, 'approach direction', size=11, color=AXIS_Z)
    _arrow(ax, (tip[0] + n[0] * 1.0, tip[1] + n[1] * 1.0),
           (tip[0] + n[0] * 0.62, tip[1] + n[1] * 0.62), color=AXIS_X, lw=2.2)
    _arrow(ax, (tip[0] - n[0] * 1.0, tip[1] - n[1] * 1.0),
           (tip[0] - n[0] * 0.62, tip[1] - n[1] * 0.62), color=AXIS_X, lw=2.2)
    _label(ax, tip[0] - n[0] * 1.1 + 0.05, tip[1] - n[1] * 1.1 - 0.35, 'closing direction',
           size=11, color=AXIS_X, ha='left')
    _label(ax, 2.3, -0.4, 'plus an opening width', size=11, color=MUTED)
    _title(ax, 2.3, 4.75, 'What the model must give for each one')
    _save(fig, 'six-dof-grasps', 'many-directions.svg')


def contact_points() -> None:
    """Each point the camera sees proposes one grasp in which it is a finger contact."""
    rng = np.random.default_rng(3)
    # The camera is above and to the left, so it sees the top and the left face
    # of a box and of a tall can. Each point is (x, y, score).
    pts: list[tuple[float, float, float]] = []
    for x in np.linspace(1.0, 2.2, 12):                      # top of the box
        pts.append((x + rng.normal(0, 0.02), 1.6 + rng.normal(0, 0.02), 0.2))
    for y in np.linspace(0.5, 1.5, 10):                      # left face of the box
        pts.append((1.0 + rng.normal(0, 0.02), y, 0.9 if 0.8 < y < 1.3 else 0.5))
    for y in np.linspace(0.5, 2.2, 15):                      # left side of the can
        pts.append((2.85 + rng.normal(0, 0.02), y, 0.9 if 1.6 < y < 2.15 else 0.5))
    for x in np.linspace(2.95, 3.9, 9):                      # top of the can
        pts.append((x + rng.normal(0, 0.02), 2.25 + rng.normal(0, 0.02), 0.2))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    fig, axes = _panels(2, (14, 5.8))
    for k, ax in enumerate(axes):
        _axes(ax, (0.2, 4.6), (-0.4, 3.7))
        _table(ax, 0.3, 4.5, 0.4)
        ax.add_patch(Rectangle((1.0, 0.4), 1.2, 1.2, facecolor='none', edgecolor=GRID,
                               lw=1.2, ls='--', zorder=1))
        ax.add_patch(Rectangle((2.85, 0.4), 1.1, 1.85, facecolor='none', edgecolor=GRID,
                               lw=1.2, ls='--', zorder=1))
        if k == 0:
            ax.scatter(xs, ys, s=26, color=LINK, zorder=5)
            ax.add_patch(Rectangle((0.3, 3.05), 0.45, 0.25, facecolor=INK, zorder=5))
            _label(ax, 0.9, 3.18, 'camera', ha='left')
            _title(ax, 2.4, 3.6, 'In: the points the camera saw')
            _caption(ax, 2.4, -0.15, 'dashed lines: the sides the camera did not see')
        else:
            cols = [GOOD if p[2] > 0.8 else (JOINT if p[2] > 0.4 else GRID) for p in pts]
            ax.scatter(xs, ys, s=26, color=cols, zorder=5)
            _gripper_side(ax, (1.6, 1.05), math.radians(-90), 1.35, finger=0.75,
                          color=GOOD, lw=3.2, wrist=0.4, alpha=0.8)
            ax.plot([1.0], [1.05], 'o', ms=13, mfc='none', mec=INK, mew=1.8, zorder=8)
            _gripper_side(ax, (3.4, 1.95), math.radians(-90), 1.35, finger=0.6,
                          color=GOOD, lw=3.2, wrist=0.4, alpha=0.8)
            ax.plot([2.85], [1.95], 'o', ms=13, mfc='none', mec=INK, mew=1.8, zorder=8)
            _title(ax, 2.4, 3.6, 'Out: a score and a grip for every point')
            _caption(ax, 2.4, -0.15, 'green = good contact, orange = so-so, grey = poor;\n'
                     'two circled points and the grips they propose')
    _save(fig, 'six-dof-grasps', 'contact-points.svg')


def propose_then_filter() -> None:
    """The model proposes many grips; checks it cannot do throw most of them away."""
    grips = [  # tip, approach in degrees, opening, why it was rejected (None = kept)
        ((1.45, 1.55), -90, 1.3, None),
        ((3.2, 1.05), -90, 1.15, None),
        ((4.75, 0.72), -90, 0.75, None),
        ((0.95, 1.45), -30, 0.6, 'wall'),
        ((5.35, 0.72), 180, 0.6, 'wall'),
        ((3.2, 0.85), -45, 1.75, 'wide'),
        ((4.95, 0.9), -135, 0.5, 'reach'),
    ]
    colours = {None: GOOD, 'wall': BAD, 'wide': JOINT, 'reach': MUTED}

    fig, axes = _panels(2, (15, 5.8))
    for k, ax in enumerate(axes):
        _axes(ax, (-0.2, 6.2), (-2.0, 4.3))
        ax.plot([0.4, 0.4, 5.6, 5.6], [2.8, 0.4, 0.4, 2.8], color=MUTED, lw=3, zorder=2)
        _mug_side(ax, 0.9, 0.4, 1.1, 1.4)
        ax.add_patch(Rectangle((2.7, 0.4), 1.0, 0.9, facecolor=OBJ, edgecolor=OBJ_EDGE,
                               lw=1.6, zorder=3))
        ax.add_patch(FancyBboxPatch((4.05, 0.45), 1.45, 0.55,
                                    boxstyle='round,pad=0.02,rounding_size=0.25',
                                    facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6, zorder=3))
        for tip, deg, op, why in grips:
            if k == 0:
                col, alpha = LINK, 0.85
            elif why is None:
                col, alpha = GOOD, 1.0
            else:
                col, alpha = colours[why], 0.35
            _gripper_side(ax, tip, math.radians(deg), op, finger=0.55, color=col, lw=3,
                          wrist=0.35, alpha=alpha)
    _title(axes[0], 3.0, 4.0, 'The model proposes 7 grips')
    _caption(axes[0], 3.0, -0.35, 'a tote seen from the side:\na mug, a box and a bottle '
             'lying down', size=10.5)
    _title(axes[1], 3.0, 4.0, 'After the checks: 3 kept')
    rows = [(GOOD, '3 kept'), (BAD, '2 hit the tote wall'),
            (JOINT, '1 needs a wider opening than the gripper has'),
            (MUTED, '1 needs a wrist angle the arm cannot reach')]
    for i, (col, text) in enumerate(rows):
        x = 0.6
        y = -0.25 - i * 0.45
        axes[1].plot([x, x + 0.35], [y, y], color=col, lw=5)
        _label(axes[1], x + 0.45, y, text, ha='left', size=10.5)
    _save(fig, 'six-dof-grasps', 'propose-then-filter.svg')


# --------------------------------------------------------------------------
# 04_suction-and-affordance.md
# --------------------------------------------------------------------------

def seal_or_leak() -> None:
    """A suction cup seals on a flat patch and leaks on an edge or a small curve."""
    fig, axes = _panels(3, (15, 5.2))
    for ax in axes:
        _axes(ax, (0, 4), (-0.8, 4.2))
        _table(ax, 0.2, 3.8, 0.3)

    ax = axes[0]
    ax.add_patch(Rectangle((0.8, 0.3), 2.4, 1.3, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    _suction(ax, (2.0, 1.6))
    _tick(ax, 3.3, 3.4)
    _title(ax, 2, 3.95, 'Flat top of a box')
    _caption(ax, 2, -0.4, 'the rim touches all the way round: it seals')

    ax = axes[1]
    ax.add_patch(Rectangle((0.5, 0.3), 1.8, 1.3, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    _suction(ax, (2.3, 1.6))
    for dx in (0.45, 0.62):
        _arrow(ax, (2.3 + dx - 0.1, 1.55), (2.3 + dx + 0.25, 1.2), color=BAD, lw=1.4)
    _cross(ax, 3.3, 3.4)
    _title(ax, 2, 3.95, 'Over the edge')
    _caption(ax, 2, -0.4, 'half the rim hangs in the air: air leaks in')

    ax = axes[2]
    ax.add_patch(Circle((2.0, 0.75), 0.45, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6, zorder=3))
    _suction(ax, (2.0, 1.2), size=0.45)
    for s in (1, -1):
        _arrow(ax, (2.0 + s * 0.5, 1.15), (2.0 + s * 0.8, 0.9), color=BAD, lw=1.4)
    _cross(ax, 3.3, 3.4)
    _title(ax, 2, 3.95, 'A small ball')
    _caption(ax, 2, -0.4, 'the surface curves away from the rim: it leaks')
    _save(fig, 'suction-and-affordance', 'seal-or-leak.svg')


def suction_map() -> None:
    """A picture of a tote, and the network's per-pixel suction score for it."""
    n = 60
    yy, xx = np.mgrid[0:n, 0:n]
    score = np.zeros((n, n))
    # a box: flat, high in the middle, falling to zero at its edges
    bx0, bx1, by0, by1 = 6, 30, 30, 52
    inside = (xx >= bx0) & (xx <= bx1) & (yy >= by0) & (yy <= by1)
    edge = np.minimum.reduce([xx - bx0, bx1 - xx, yy - by0, by1 - yy]).astype(float)
    score[inside] = np.clip(edge[inside] / 11.0, 0, 1)
    # a can seen from above: a flat round lid
    cc, cr = (45, 42), 9
    d = np.hypot(xx - cc[0], yy - cc[1])
    lid = d <= cr
    score[lid] = np.maximum(score[lid], np.clip((cr - d[lid]) / 5.0, 0, 0.85))
    # a ball: only a small patch at its very top
    bc, br = (18, 13), 7
    db = np.hypot(xx - bc[0], yy - bc[1])
    score[db <= br] = np.maximum(score[db <= br], np.clip(0.35 - db[db <= br] / 10, 0, 1))
    # a soft bag: lumpy, poor everywhere
    gc = (44, 14)
    bag = ((xx - gc[0]) / 11) ** 2 + ((yy - gc[1]) / 8) ** 2 <= 1
    score[bag] = np.maximum(score[bag], 0.15 + 0.1 * np.sin(xx[bag] * 0.9) * np.cos(yy[bag]))
    best = np.unravel_index(np.argmax(score), score.shape)

    fig, axes = _panels(2, (13, 6.2))
    ax = axes[0]
    _axes(ax, (0, n), (0, n))
    ax.add_patch(Rectangle((0, 0), n, n, facecolor='#eeeeee', edgecolor=MUTED, lw=1.2))
    ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, facecolor=OBJ,
                           edgecolor=OBJ_EDGE, lw=1.6))
    ax.add_patch(Circle(cc, cr, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6))
    ax.add_patch(Circle(bc, br, facecolor='#f3d9a4', edgecolor=WRIST, lw=1.6))
    ax.add_patch(Ellipse(gc, 22, 16, facecolor='#e6d3ef', edgecolor='#8a5aa8', lw=1.6))
    for (x, y), t in ((((bx0 + bx1) / 2, by1 + 3.5), 'box'), ((cc[0], cc[1] + cr + 3.5), 'can'),
                      ((bc[0], bc[1] + br + 3.5), 'ball'), ((gc[0], gc[1] + 11), 'soft bag')):
        _label(ax, x, y, t, size=11)
    _title(ax, n / 2, n + 4, 'In: a picture of the tote from above')

    ax = axes[1]
    ax.imshow(score, cmap='Greens', origin='lower', vmin=0, vmax=1, interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(MUTED)
    ax.plot([best[1]], [best[0]], marker='*', color=BAD, ms=20, mec='white', mew=1)
    ax.set_title('Out: a suction score for every pixel', fontsize=12.5, weight='bold',
                 color=INK, pad=12)
    ax.set_xlabel('dark green = likely to seal; the red star is the best spot',
                  fontsize=10.5, color=MUTED, labelpad=8)
    _save(fig, 'suction-and-affordance', 'suction-map.svg')


def parts_for_jobs() -> None:
    """An affordance model colours each part of an object by what it is for."""
    fig, axes = _panels(2, (13.5, 5.8))
    hold = GOOD
    other = JOINT
    third = LINK

    ax = axes[0]
    _axes(ax, (0, 5), (-0.6, 4.6))
    # a mug: the body is for wrapping a hand round, the inside holds liquid,
    # the handle is for holding
    ax.add_patch(Rectangle((1.2, 0.5), 1.8, 2.4, facecolor='#f6e1bd', edgecolor=other, lw=2,
                           zorder=3))
    ax.add_patch(Rectangle((1.4, 1.0), 1.4, 1.9, facecolor='#cfe0f1', edgecolor=third, lw=2,
                           zorder=4))
    ax.add_patch(Arc((3.0, 1.75), 1.3, 1.4, theta1=-90, theta2=90, color=hold, lw=9,
                     zorder=2))
    _label(ax, 4.25, 2.75, 'handle:\nhold here', color=hold, size=11, weight='bold')
    _arrow(ax, (3.9, 2.4), (3.6, 2.0), color=hold)
    _label(ax, 2.1, 3.55, 'inside: contains', color=third, size=11, weight='bold')
    _arrow(ax, (2.1, 3.35), (2.1, 2.6), color=third)
    _label(ax, 0.5, 0.25, 'outside:\nwrap a hand\nround', color=WRIST, size=11,
           weight='bold', ha='center')
    _arrow(ax, (0.55, 0.85), (1.15, 1.2), color=WRIST)
    _title(ax, 2.5, 4.35, 'A mug, coloured by what each part is for')

    ax = axes[1]
    _axes(ax, (0, 5.5), (-0.6, 4.6))
    ax.add_patch(FancyBboxPatch((0.5, 1.7), 1.8, 0.55, boxstyle='round,pad=0.05',
                                facecolor='#cdebd3', edgecolor=hold, lw=2, zorder=3))
    blade = [(2.35, 1.7), (5.0, 1.85), (5.0, 2.0), (2.35, 2.3)]
    ax.add_patch(Polygon(blade, closed=True, facecolor='#f6e1bd', edgecolor=other, lw=2,
                         zorder=3))
    _label(ax, 1.4, 2.85, 'handle: hold here', color=hold, size=11, weight='bold')
    _label(ax, 3.9, 2.85, 'blade: cuts', color=WRIST, size=11, weight='bold')
    _cross(ax, 3.9, 1.2, size=0.18)
    _label(ax, 3.9, 0.55, 'a grip model that only asks\n"will it hold?" may pick the blade',
           size=10.5, color=BAD)
    _title(ax, 2.75, 4.35, 'A knife: the handle is the only part to hold')
    _save(fig, 'suction-and-affordance', 'parts-for-jobs.svg')


# --------------------------------------------------------------------------
# 05_grasp-quality-models.md
# --------------------------------------------------------------------------

def sample_then_score() -> None:
    """Draw many candidate grips, score each one, keep the best."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1.2, 1]})
    ax = axes[0]
    _axes(ax, (0, 5), (-0.3, 5.0))
    ax.add_patch(Rectangle((0.1, 0.1), 4.8, 4.3, facecolor='#eeeeee', edgecolor=MUTED, lw=1))
    _mug_top(ax, (2.3, 2.2), 0.95, handle=math.radians(10))
    # (centre, angle in degrees, opening, score, which end carries the label)
    cands = [((2.3, 2.2), 90, 2.3, 0.91, 1),
             ((2.3, 2.2), 20, 2.3, 0.34, -1),
             ((2.3, 2.2), 140, 2.3, 0.62, 1),
             ((3.65, 2.35), 90, 0.75, 0.48, 1),
             ((2.3, 1.2), 0, 1.0, 0.05, 0)]
    top = max(c[3] for c in cands)
    for cc, deg, w, sc, end in cands:
        best = sc == top
        col = GOOD if best else MUTED
        a = math.radians(deg)
        _grasp_rect(ax, cc, a, w, jaw=0.45, color=col, lw=2.0 if best else 1.3,
                    alpha=1.0 if best else 0.8)
        r = w / 2 + 0.33
        lx, ly = cc[0] + end * r * math.cos(a), cc[1] + end * r * math.sin(a)
        if end == 0:
            lx, ly = cc[0], cc[1] - 0.6
        _label(ax, lx, ly,
               f'{sc:.2f}', size=11, color=GOOD if best else INK,
               weight='bold' if best else 'normal')
    _title(ax, 2.5, 4.75, 'Five candidate grips, each with a score')

    ax = axes[1]
    _axes(ax, (0, 5), (-0.3, 5.0))
    ranked = sorted(cands, key=lambda t: -t[3])
    for i, c in enumerate(ranked):
        y = 3.9 - i * 0.62
        first = i == 0
        ax.add_patch(Rectangle((1.2, y - 0.2), 3.2 * c[3], 0.4,
                               facecolor=GOOD if first else LINK_PALE,
                               edgecolor=GOOD if first else LINK, lw=1.2))
        _label(ax, 1.0, y, f'{c[3]:.2f}', ha='right', size=11)
    _label(ax, 2.8, 0.1, 'the arm tries only the top one', size=11, color=GOOD)
    _title(ax, 2.5, 4.75, 'Sorted by score')
    _save(fig, 'grasp-quality-models', 'sample-then-score.svg')


def crop_and_score() -> None:
    """A Dex-Net-style network looks at a small, turned crop around one candidate grip."""
    fig, ax = plt.subplots(figsize=(16, 5.6), facecolor='white')
    _axes(ax, (0, 16.5), (-0.9, 5.2))
    # the whole depth picture
    ax.add_patch(Rectangle((0.2, 0.3), 4.2, 4.0, facecolor='#eeeeee', edgecolor=MUTED, lw=1))
    c = (2.3, 2.3)
    ang = math.radians(35)
    _mug_top(ax, c, 0.85, handle=math.radians(-60))
    _grasp_rect(ax, c, ang, 2.2, jaw=0.55, color=LINK)
    sq = [_rot(v, ang) for v in ((-1.4, -1.0), (1.4, -1.0), (1.4, 1.0), (-1.4, 1.0))]
    ax.add_patch(Polygon([(c[0] + x, c[1] + y) for x, y in sq], closed=True, fill=False,
                         edgecolor=JOINT, lw=2, zorder=8))
    _title(ax, 2.3, 4.75, '1. One candidate on the picture')
    _caption(ax, 2.3, -0.2, 'orange square: the patch to cut out')
    _arrow(ax, (4.6, 2.3), (5.4, 2.3), lw=2)

    # the cut-out, turned so the jaws sit left and right
    ax.add_patch(Rectangle((5.6, 1.1), 3.2, 2.4, facecolor='#eeeeee', edgecolor=JOINT, lw=2))
    ax.add_patch(Rectangle((6.35, 1.1), 1.7, 2.4, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.4))
    _grasp_rect(ax, (7.2, 2.3), 0.0, 2.2, jaw=0.6, color=LINK)
    _title(ax, 7.2, 4.75, '2. Cut out and turned')
    _caption(ax, 7.2, -0.2, 'the jaws always sit\nleft and right, in the middle')
    _label(ax, 7.2, 0.55, 'plus: how deep the jaws go', size=10.5, color=LINK)
    _arrow(ax, (9.0, 2.3), (9.8, 2.3), lw=2)

    _network(ax, 10.0, 0.7, 2.6, 3.2, layers=(5, 6, 4, 1))
    _title(ax, 11.3, 4.75, '3. A small network')
    _arrow(ax, (12.8, 2.3), (13.6, 2.3), lw=2)

    ax.add_patch(FancyBboxPatch((13.8, 1.6), 2.4, 1.4, boxstyle='round,pad=0.08',
                                facecolor='white', edgecolor=GOOD, lw=2))
    _label(ax, 15.0, 2.55, '0.87', size=20, color=GOOD, weight='bold')
    _label(ax, 15.0, 1.95, 'chance it holds', size=10.5, color=GOOD)
    _title(ax, 15.0, 4.75, '4. One number out')
    _save(fig, 'grasp-quality-models', 'crop-and-score.svg')


def labels_without_a_robot() -> None:
    """Two ways to get labelled grips: calculate them on 3D models, or try them for real."""
    fig, axes = _panels(2, (15, 6.0))

    ax = axes[0]
    _axes(ax, (0, 6), (-0.9, 4.9))
    # a 3D model of a mug (wireframe-ish) with many grips around it
    _mug_side(ax, 1.0, 0.8, 1.4, 1.9)
    for y in np.linspace(1.0, 2.5, 4):
        ax.plot([1.0, 2.4], [y, y], color=OBJ_EDGE, lw=0.6, alpha=0.6, zorder=4)
    for tip, deg, op, col in (((2.38, 2.5), -90, 0.3, GOOD), ((2.72, 1.85), 180, 0.45, GOOD),
                              ((1.7, 0.95), 60, 1.0, BAD), ((1.0, 2.75), -45, 0.5, BAD)):
        _gripper_side(ax, tip, math.radians(deg), op, finger=0.45, color=col, lw=2.6,
                      wrist=0.3)
    _arrow(ax, (3.3, 1.7), (4.0, 1.7), lw=2)
    # a rendered depth picture and its label
    ax.add_patch(Rectangle((4.2, 1.0), 1.4, 1.4, facecolor='#dddddd', edgecolor=MUTED, lw=1))
    ax.add_patch(Circle((4.9, 1.7), 0.4, facecolor='#777777', edgecolor='none'))
    _label(ax, 4.9, 0.6, 'picture + grip\n+ 1 or 0', size=10.5)
    _title(ax, 3.0, 4.55, 'Calculated: 3D models in a computer')
    _caption(ax, 3.0, -0.55, 'green: calculated to hold; red: calculated to slip.\n'
             'Physics rules decide each label, so millions are cheap to make.')

    ax = axes[1]
    _axes(ax, (0, 6), (-0.9, 4.9))
    _table(ax, 0.2, 3.4, 0.4)
    # a simple arm reaching down to a box
    ax.add_patch(Rectangle((0.3, 0.4), 0.5, 0.3, facecolor=MUTED, zorder=3))
    ax.plot([0.55, 0.9, 2.3, 2.3], [0.7, 2.9, 3.1, 2.1], color=LINK, lw=7,
            solid_capstyle='round', zorder=3)
    for p in ((0.55, 0.7), (0.9, 2.9), (2.3, 3.1)):
        ax.plot([p[0]], [p[1]], 'o', color=JOINT, ms=12, zorder=4)
    _gripper_side(ax, (2.3, 1.25), math.radians(-90), 0.9, finger=0.5, wrist=0.35)
    ax.add_patch(Rectangle((1.85, 0.4), 0.9, 0.75, facecolor=OBJ, edgecolor=OBJ_EDGE, lw=1.6,
                           zorder=3))
    _arrow(ax, (3.3, 1.7), (4.0, 1.7), lw=2)
    ax.add_patch(Rectangle((4.2, 1.0), 1.4, 1.4, facecolor='#dddddd', edgecolor=MUTED, lw=1))
    ax.add_patch(Rectangle((4.6, 1.4), 0.6, 0.6, facecolor='#777777', edgecolor='none'))
    _label(ax, 4.9, 0.6, 'picture + grip\n+ 1 or 0', size=10.5)
    _title(ax, 3.0, 4.55, 'Tried: a real arm, over and over')
    _caption(ax, 3.0, -0.55, 'the arm grips, lifts and checks.\n'
             'The real world decides each label, and each try takes real time.')
    _save(fig, 'grasp-quality-models', 'labels-two-ways.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    four_answers()
    did_it_hold()
    grasp_rectangle()
    three_maps()
    straight_down_only()
    many_directions()
    contact_points()
    propose_then_filter()
    seal_or_leak()
    suction_map()
    parts_for_jobs()
    sample_then_score()
    crop_and_score()
    labels_without_a_robot()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
