"""Generate the diagrams used in docs/07_learned-models/04_3d-models/.

Each document's pictures go to a folder named after it, under
docs/images/3d-models/.

Run with:  pixi run python ../docs/diagrams/three_d_models.py
or, from the repo root:  python3 docs/diagrams/three_d_models.py --png <dir>

Every point cloud here is made up for the picture from a simple mug shape and a
table top. The numbers written in the pictures are examples chosen to show the
idea. They are not the output of any real model.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / '3d-models'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

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

# Colours for the things in the scenes, picked from the palette above.
MUG: str = LINK
TABLE: str = '#9a9a9a'
BOX: str = SLIDE
NEW: str = WRIST          # points a model added, or guessed
HOT: str = GRIP           # points that match a question


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
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=7)


def _title(ax: Axes, x: float, y: float, text: str) -> None:
    ax.text(x, y, text, fontsize=13, ha='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='top', color=MUTED)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=6)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = LINK_PALE, size: float = 10) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                                facecolor=face, edgecolor=INK, lw=0.8, zorder=3))
    _label(ax, x + w / 2, y + h / 2, text, size=size)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 3D points drawn on a flat page
# --------------------------------------------------------------------------

def _iso(p: NDArray[np.float64]) -> NDArray[np.float64]:
    """Project (x, y, z) points onto the page: y goes back and to the right."""
    p = np.atleast_2d(p)
    u = p[:, 0] + 0.5 * p[:, 1]
    v = p[:, 2] + 0.32 * p[:, 1]
    return np.stack([u, v], axis=1)


def _scatter(ax: Axes, pts: NDArray[np.float64], color: str | list[str], size: float = 9,
             offset: tuple[float, float] = (0.0, 0.0), hollow: bool = False,
             z: int = 3) -> None:
    """Draw 3D points, the ones further back first."""
    order = np.argsort(-pts[:, 1])
    uv = _iso(pts[order]) + np.array(offset)
    cols = color if isinstance(color, str) else [color[i] for i in order]
    if hollow:
        ax.scatter(uv[:, 0], uv[:, 1], s=size, facecolors='white', edgecolors=cols,
                   linewidths=0.8, zorder=z)
    else:
        ax.scatter(uv[:, 0], uv[:, 1], s=size, c=cols, linewidths=0, zorder=z)


def _mug_points(n_side: int = 26, n_up: int = 9, radius: float = 0.4,
                height: float = 0.9) -> NDArray[np.float64]:
    """Points on the outside of a mug: a cylinder wall, a bottom rim and a handle."""
    pts: list[tuple[float, float, float]] = []
    for i in range(n_side):
        a = 2 * math.pi * i / n_side
        for j in range(n_up):
            z = 0.05 + (height - 0.05) * j / (n_up - 1)
            pts.append((radius * math.cos(a), radius * math.sin(a), z))
    for i in range(n_side):                       # the top rim, inside edge
        a = 2 * math.pi * (i + 0.5) / n_side
        pts.append((0.8 * radius * math.cos(a), 0.8 * radius * math.sin(a), height))
    for k in range(13):                           # the handle, a half ring on +x
        t = -math.pi / 2 + math.pi * k / 12
        pts.append((radius + 0.22 * math.cos(t), 0.0, 0.45 + 0.24 * math.sin(t)))
        pts.append((radius + 0.22 * math.cos(t), 0.05, 0.45 + 0.24 * math.sin(t)))
    return np.array(pts)


def _is_handle(pts: NDArray[np.float64], radius: float = 0.4) -> NDArray[np.bool_]:
    return np.hypot(pts[:, 0], pts[:, 1]) > radius + 0.05


def _table_points(x0: float, x1: float, y0: float, y1: float, step: float = 0.18,
                  seed: int = 1) -> NDArray[np.float64]:
    rng = np.random.default_rng(seed)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1e-9, step), np.arange(y0, y1 + 1e-9, step))
    pts = np.stack([xs.ravel(), ys.ravel(), np.zeros(xs.size)], axis=1)
    pts[:, :2] += rng.normal(0, 0.02, size=(len(pts), 2))
    return pts


def _box_points(cx: float, cy: float, w: float, d: float, h: float,
                step: float = 0.13) -> NDArray[np.float64]:
    """Points on the top and the four sides of a closed box."""
    pts: list[tuple[float, float, float]] = []
    for x in np.arange(-w / 2, w / 2 + 1e-9, step):
        for y in np.arange(-d / 2, d / 2 + 1e-9, step):
            pts.append((cx + x, cy + y, h))
        for z in np.arange(0.05, h, step):
            pts.append((cx + x, cy - d / 2, z))
            pts.append((cx + x, cy + d / 2, z))
    for y in np.arange(-d / 2, d / 2 + 1e-9, step):
        for z in np.arange(0.05, h, step):
            pts.append((cx - w / 2, cy + y, z))
            pts.append((cx + w / 2, cy + y, z))
    return np.array(pts)


def _seen_from_front(pts: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Which mug points a camera in front (towards -y) can see: the front half."""
    return (pts[:, 1] < 0.02) | (np.hypot(pts[:, 0], pts[:, 1]) < 0.39)


def _mug_outline(ax: Axes, x: float, y: float, w: float = 0.8, h: float = 0.9,
                 color: str = MUG, fill: str = LINK_PALE) -> None:
    """A flat side view of a mug, as it would look in a photo."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=fill, edgecolor=color, lw=1.6,
                           zorder=3))
    ax.add_patch(Ellipse((x, y + h), w, 0.16, facecolor='white', edgecolor=color, lw=1.6,
                         zorder=4))
    t = np.linspace(-math.pi / 2, math.pi / 2, 30)
    ax.plot(x + w / 2 + 0.22 * np.cos(t), y + h / 2 + 0.24 * np.sin(t), color=color, lw=4,
            solid_capstyle='round', zorder=2)


def _camera(ax: Axes, x: float, y: float, angle: float, size: float = 0.22,
            color: str = INK) -> None:
    """A small camera: a body with a lens triangle pointing along `angle` (radians)."""
    c, s = math.cos(angle), math.sin(angle)

    def rot(px: float, py: float) -> tuple[float, float]:
        return (x + px * c - py * s, y + px * s + py * c)

    body = [rot(-size, -size * 0.7), rot(size * 0.2, -size * 0.7), rot(size * 0.2, size * 0.7),
            rot(-size, size * 0.7)]
    lens = [rot(size * 0.2, 0), rot(size * 0.8, -size * 0.55), rot(size * 0.8, size * 0.55)]
    ax.add_patch(Polygon(body, closed=True, facecolor=color, edgecolor=color, zorder=5))
    ax.add_patch(Polygon(lens, closed=True, facecolor=color, edgecolor=color, zorder=5))


def _little_net(ax: Axes, x: float, y: float, w: float = 0.9, h: float = 0.8,
                layers: tuple[int, ...] = (3, 4, 3), color: str = LINK) -> None:
    """A tiny drawing of a neural network: columns of circles joined by lines."""
    cols = len(layers)
    centres: list[list[tuple[float, float]]] = []
    for i, n in enumerate(layers):
        cx = x + w * i / (cols - 1)
        centres.append([(cx, y + h * (k + 0.5) / n - h / 2) for k in range(n)])
    for a_col, b_col in zip(centres[:-1], centres[1:]):
        for a in a_col:
            for b in b_col:
                ax.plot([a[0], b[0]], [a[1], b[1]], color=GRID, lw=0.7, zorder=2)
    r = min(0.07, h / (2.6 * max(layers)))
    for col in centres:
        for c in col:
            ax.add_patch(Circle(c, r, facecolor=color, edgecolor='white', lw=0.6, zorder=3))


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'


def what_a_point_cloud_is() -> None:
    """A photo of a mug next to the point cloud a depth camera makes of the same scene."""
    fig, (left, right) = _panels(2, (11.0, 4.8))

    _axes(left, (-1.9, 1.9), (-1.2, 2.4))
    left.add_patch(Rectangle((-1.6, -0.4), 3.2, 2.5, facecolor='#f4f4f4', edgecolor=INK,
                             lw=1.2, zorder=1))
    left.add_patch(Rectangle((-1.6, -0.4), 3.2, 0.75, facecolor='#e2e2e2', edgecolor='none',
                             zorder=1))
    _mug_outline(left, -0.1, 0.1)
    _title(left, 0.0, 2.25, 'A photo')
    _caption(left, 0.0, -0.55, 'A flat grid of coloured pixels.\n'
             'It does not say how far away the mug is.')

    _axes(right, (-1.9, 2.3), (-1.2, 2.4))
    mug = _mug_points()
    seen = mug[_seen_from_front(mug)]
    table = _table_points(-1.3, 1.3, -0.7, 0.9)
    table = table[np.hypot(table[:, 0], table[:, 1]) > 0.42]
    _scatter(right, table, TABLE, size=7)
    _scatter(right, seen, MUG, size=10)
    picks = [(np.array([-0.2, -0.35, 0.72]), '(0.42, 0.10, 0.08)', (-1.55, 1.75)),
             (np.array([1.0, -0.4, 0.0]), '(0.60, 0.05, 0.00)', (1.55, -0.55))]
    for p, text, at in picks:
        uv = _iso(p)[0]
        right.plot(uv[0], uv[1], 'o', ms=9, mfc='none', mec=GRIP, mew=1.8, zorder=6)
        right.plot([uv[0], at[0]], [uv[1], at[1]], color=GRIP, lw=0.9, zorder=5)
        _label(right, at[0], at[1] + (0.17 if at[1] > 0 else -0.17), text, color=GRIP)
    _title(right, 0.2, 2.25, 'A point cloud of the same scene')
    _caption(right, 0.2, -0.85, 'Many dots, each one a spot on a surface.\n'
             'Each dot is three numbers: x, y and z, in metres.')
    _save(fig, OVERVIEW, 'what-a-point-cloud-is.svg')


def four_questions() -> None:
    """The four subcategories, each shown as the question it answers about one mug."""
    fig, axes = _panels(4, (14.0, 4.4))
    mug = _mug_points()
    front = _seen_from_front(mug)
    handle = _is_handle(mug)

    for ax in axes:
        _axes(ax, (-1.3, 1.5), (-0.9, 1.9))

    table = _table_points(-0.9, 0.9, -0.5, 0.6, step=0.22)
    table = table[np.hypot(table[:, 0], table[:, 1]) > 0.42]
    _scatter(axes[0], table, TABLE, size=6)
    _scatter(axes[0], mug[front], MUG, size=8)
    _title(axes[0], 0.1, 1.55, 'Point cloud models')
    _caption(axes[0], 0.1, -0.5, 'Which dots belong to the mug?\n'
             'blue = mug, grey = table')

    _scatter(axes[1], mug, [MUG if f else NEW for f in front], size=8)
    _title(axes[1], 0.1, 1.55, 'Shape completion')
    _caption(axes[1], 0.1, -0.5, 'What does the hidden back look like?\n'
             'blue = seen, orange = guessed')

    ax = axes[2]
    _mug_outline(ax, 0.0, -0.05, w=0.5, h=0.6)
    for k in range(6):
        a = math.pi * (0.1 + 0.8 * k / 5)
        cx, cy = 0.1 + 1.05 * math.cos(a), 0.2 + 0.95 * math.sin(a)
        _camera(ax, cx, cy, math.atan2(0.3 - cy, 0.0 - cx), size=0.13)
    _title(ax, 0.1, 1.55, 'Scene reconstruction')
    _caption(ax, 0.1, -0.5, 'What does the whole scene look like,\n'
             'from any point of view?')

    heat = [HOT if h else LINK_PALE for h in handle[front]]
    _scatter(axes[3], mug[front], heat, size=9)
    _label(axes[3], 0.1, 1.28, '"the handle"', color=HOT)
    _title(axes[3], 0.1, 1.55, '3D feature maps')
    _caption(axes[3], 0.1, -0.5, 'Where in 3D is the thing\n'
             'these words describe?')
    _save(fig, OVERVIEW, 'four-questions.svg')


# --------------------------------------------------------------------------
# 02_point-cloud-models
# --------------------------------------------------------------------------

POINTS_DOC: str = 'point-cloud-models'

# Five points of a small shape, used to show that their order does not matter.
FIVE: NDArray[np.float64] = np.array([[0.0, 0.0], [1.0, 0.2], [1.3, 1.1], [0.4, 1.5],
                                      [-0.3, 0.8]])


def order_does_not_matter() -> None:
    """The same five points written in two orders give the model the same answer."""
    fig, (left, mid, right) = _panels(3, (13.0, 4.6))
    orders = ([0, 1, 2, 3, 4], [3, 0, 4, 2, 1])
    for ax, order, name in ((left, orders[0], 'List A'), (right, orders[1], 'List B')):
        _axes(ax, (-1.0, 3.9), (-1.8, 2.3))
        for rank, idx in enumerate(order):
            x, y = FIVE[idx]
            ax.plot(x, y, 'o', color=MUG, ms=12, zorder=3)
            _label(ax, x, y, str(rank + 1), size=8, color='white', weight='bold')
            _label(ax, 2.0, 1.6 - 0.42 * rank,
                   f'{rank + 1}:  ({x:+.1f}, {y:+.1f})', size=10, ha='left')
        _label(ax, 2.0, 2.05, name, size=11, ha='left', weight='bold')
        _caption(ax, 1.4, -0.55, 'The same five dots.\nThe numbers say which\n'
                 'row of the list each one is.')

    _axes(mid, (-1.6, 1.6), (-1.8, 2.3))
    _box(mid, -0.9, 0.05, 1.8, 0.9, 'point cloud\nmodel')
    _arrow(mid, (-1.55, 0.95), (-0.95, 0.6))
    _arrow(mid, (-1.55, 0.05), (-0.95, 0.4))
    _arrow(mid, (0.0, 0.0), (0.0, -0.55))
    _label(mid, 0.0, -0.8, '"mug", both times', size=11, color=SLIDE, weight='bold')
    _caption(mid, 0.0, -1.1, 'A point cloud model must give\nthe same answer for any order.')
    _save(fig, POINTS_DOC, 'order-does-not-matter.svg')


def shared_network_then_max() -> None:
    """PointNet's idea: the same small network on every point, then the largest of each column."""
    fig, ax = plt.subplots(figsize=(12.0, 5.8), facecolor='white')
    _axes(ax, (-0.8, 12.4), (-2.0, 4.5))
    values = np.array([[0.1, 0.8, 0.3, 0.0],
                       [0.9, 0.2, 0.4, 0.1],
                       [0.0, 0.3, 0.7, 0.2],
                       [0.2, 0.1, 0.5, 0.6]])       # one row per point
    ys = [3.4, 2.6, 1.8, 1.0]
    x0 = 3.6
    for k, y in enumerate(ys):
        ax.plot(0.0, y, 'o', color=MUG, ms=11, zorder=3)
        _label(ax, -0.25, y, f'point {k + 1}', size=9, color=MUTED, ha='right')
        _arrow(ax, (0.25, y), (1.05, y))
        _little_net(ax, 1.3, y, w=1.0, h=0.55)
        _arrow(ax, (2.55, y), (3.4, y))
        for c in range(4):
            cx = x0 + 0.72 * c
            ax.add_patch(Rectangle((cx, y - 0.3), 0.6, 0.6, facecolor='white',
                                   edgecolor=GRID, lw=1.0, zorder=2))
            is_max = values[k, c] == values[:, c].max()
            _label(ax, cx + 0.3, y, f'{values[k, c]:.1f}', size=10,
                   color=GRIP if is_max else INK, weight='bold' if is_max else 'normal')
    _label(ax, 1.8, 4.1, 'the same small network,\nused once per point', size=10)
    _label(ax, x0 + 1.38, 4.1, 'four numbers for each point', size=10)

    # The largest number in each column, for the whole cloud.
    _label(ax, x0 - 0.2, -0.1, 'largest in\neach column', size=9, color=GRIP, ha='right')
    for c in range(4):
        cx = x0 + 0.72 * c
        _arrow(ax, (cx + 0.3, 0.6), (cx + 0.3, 0.25), color=GRIP, lw=1.0)
        ax.add_patch(Rectangle((cx, -0.4), 0.6, 0.6, facecolor='#fde7e7', edgecolor=GRIP,
                               lw=1.2, zorder=2))
        _label(ax, cx + 0.3, -0.1, f'{values[:, c].max():.1f}', size=10, color=GRIP,
               weight='bold')
    _arrow(ax, (x0 + 2.95, -0.1), (8.2, -0.1))
    _label(ax, 7.35, 0.2, 'the whole cloud', size=9, color=MUTED)
    _little_net(ax, 8.45, -0.1, w=0.9, h=0.7, layers=(4, 3, 2))
    _arrow(ax, (9.55, -0.1), (10.3, -0.1))
    _label(ax, 10.8, -0.1, '"mug"', size=12, color=SLIDE, weight='bold')
    _caption(ax, 5.6, -0.95, 'The largest number in a column does not depend on the '
             'order of the rows,\nso the order of the points no longer changes the answer.')
    _save(fig, POINTS_DOC, 'shared-network-then-max.svg')


def a_label_on_every_point() -> None:
    """Segmentation: every point of a scene gets a name, shown as its colour."""
    fig, (left, right) = _panels(2, (12.0, 4.8))
    mug = _mug_points() + np.array([-0.55, 0.0, 0.0])
    box = _box_points(0.75, 0.15, 0.6, 0.5, 0.45)
    table = _table_points(-1.4, 1.5, -0.7, 0.9)
    keep = (np.hypot(table[:, 0] + 0.55, table[:, 1]) > 0.42) & ~(
        (abs(table[:, 0] - 0.75) < 0.32) & (abs(table[:, 1] - 0.15) < 0.27))
    table = table[keep]
    scene = [(table, TABLE), (mug[_seen_from_front(mug - np.array([-0.55, 0, 0]))], MUG),
             (box[box[:, 1] < 0.4], BOX)]

    for ax in (left, right):
        _axes(ax, (-1.8, 2.3), (-1.3, 2.1))
    allpts = np.concatenate([p for p, _ in scene])
    _scatter(left, allpts, INK, size=7)
    _title(left, 0.25, 1.8, 'What goes in')
    _caption(left, 0.25, -0.75, 'Only positions. Every dot looks the same.')
    for pts, col in scene:
        _scatter(right, pts, col, size=8)
    _title(right, 0.25, 1.8, 'What comes out')
    _caption(right, 0.25, -0.75, 'A name for every dot.')
    for k, (text, col) in enumerate((('mug', MUG), ('box', BOX), ('table', TABLE))):
        right.plot(1.75, 1.35 - 0.3 * k, 'o', color=col, ms=8)
        _label(right, 1.9, 1.35 - 0.3 * k, text, ha='left')
    _save(fig, POINTS_DOC, 'a-label-on-every-point.svg')


def small_neighbourhoods() -> None:
    """PointNet++: pick some centre points, look at the dots near each one, repeat bigger."""
    fig, (left, right) = _panels(2, (11.0, 4.6))
    rng = np.random.default_rng(3)
    # A flat top view of a mug: a ring of dots and a handle.
    a = rng.uniform(0, 2 * math.pi, 170)
    r = 1.0 + rng.normal(0, 0.04, 170)
    ring = np.stack([r * np.cos(a), r * np.sin(a)], axis=1)
    t = rng.uniform(-1.2, 1.2, 30)
    handle = np.stack([1.0 + 0.45 * np.cos(t), 0.45 * np.sin(t)], axis=1)
    dots = np.concatenate([ring, handle])

    for ax, radius, n, title, cap in (
            (left, 0.32, 8, 'Step 1: small groups',
             'A few centre dots are picked.\nEach looks only at the dots near it.'),
            (right, 0.72, 3, 'Step 2: bigger groups',
             'The groups are grouped again,\nso each one now covers a larger area.')):
        _axes(ax, (-2.0, 2.0), (-2.6, 2.1))
        ax.scatter(dots[:, 0], dots[:, 1], s=8, c=LINK_PALE if ax is right else MUG,
                   linewidths=0, zorder=2)
        for k in range(n):
            ang = 2 * math.pi * k / n + 0.3
            c = (math.cos(ang), math.sin(ang))
            ax.add_patch(Circle(c, radius, facecolor='none', edgecolor=GRIP, lw=1.3,
                                ls='--', zorder=3))
            ax.plot(*c, 'o', color=GRIP, ms=6, zorder=4)
        _title(ax, 0.0, 1.85, title)
        _caption(ax, 0.0, -1.9, cap)
    _save(fig, POINTS_DOC, 'small-neighbourhoods.svg')


# --------------------------------------------------------------------------
# 03_shape-completion
# --------------------------------------------------------------------------

COMPLETION_DOC: str = 'shape-completion'


def camera_sees_one_side() -> None:
    """A top view: the camera's rays reach the front of the mug and never the back."""
    fig, ax = plt.subplots(figsize=(7.2, 6.0), facecolor='white')
    _axes(ax, (-2.6, 3.0), (-3.6, 1.8))
    cam = (0.0, -3.0)
    _camera(ax, cam[0], cam[1], math.pi / 2, size=0.25)
    _label(ax, 0.45, -3.05, 'depth camera', ha='left')
    ax.add_patch(Circle((0, 0), 1.0, facecolor='#f4f4f4', edgecolor=GRID, lw=1.0, zorder=1))
    ax.add_patch(Rectangle((1.0, -0.12), 0.55, 0.24, facecolor='#f4f4f4', edgecolor=GRID,
                           lw=1.0, zorder=1))
    for k in range(9):
        ang = math.pi + math.pi * (k + 0.5) / 9       # the front half, facing the camera
        hit = (math.cos(ang), math.sin(ang))
        ax.plot([cam[0], hit[0]], [cam[1] + 0.2, hit[1]], color=JOINT, lw=0.8, zorder=2)
    front = np.linspace(math.pi, 2 * math.pi, 22)
    back = np.linspace(0, math.pi, 22)
    ax.scatter(np.cos(front), np.sin(front), s=22, c=MUG, zorder=4)
    ax.scatter(np.cos(back), np.sin(back), s=22, facecolors='white', edgecolors=MUTED,
               linewidths=0.9, zorder=4)
    _label(ax, 0.0, 1.35, 'back: no dots at all', color=MUTED)
    _label(ax, -1.0, -0.95, 'front: dots', color=MUG, ha='right')
    _label(ax, 0.0, 0.0, 'mug\n(seen from above)', size=9, color=MUTED)
    _label(ax, 1.75, 0.35, 'handle:\nhidden', size=9, color=MUTED, ha='left')
    _save(fig, COMPLETION_DOC, 'camera-sees-one-side.svg')


def partial_in_complete_out() -> None:
    """What goes in (the front half) and what comes out (the whole mug)."""
    fig, ax = plt.subplots(figsize=(11.0, 4.4), facecolor='white')
    _axes(ax, (-1.2, 8.6), (-1.1, 2.0))
    mug = _mug_points()
    front = _seen_from_front(mug)
    _scatter(ax, mug[front], MUG, size=10, offset=(0.0, 0.0))
    _label(ax, 0.2, 1.75, 'What goes in', size=12, weight='bold')
    _caption(ax, 0.2, -0.3, 'the dots the camera saw')
    _arrow(ax, (1.3, 0.6), (2.3, 0.6))
    _box(ax, 2.4, 0.15, 1.9, 0.9, 'shape\ncompletion\nmodel')
    _arrow(ax, (4.4, 0.6), (5.4, 0.6))
    _scatter(ax, mug, [MUG if f else NEW for f in front], size=10, offset=(6.4, 0.0))
    _label(ax, 6.6, 1.75, 'What comes out', size=12, weight='bold')
    _caption(ax, 6.6, -0.3, 'the whole mug:\nblue = seen, orange = guessed')
    _save(fig, COMPLETION_DOC, 'partial-in-complete-out.svg')


def grasp_with_and_without() -> None:
    """A top view of a box grasped from the side, with and without the hidden back."""
    fig, (left, right) = _panels(2, (11.0, 5.0))
    for ax, complete, title, cap in (
            (left, False, 'Only the seen dots',
             'The middle of the dots is near the front.\n'
             'The fingers close there and catch only the front edge.'),
            (right, True, 'With the back filled in',
             'The middle of the whole box is further back.\n'
             'The fingers close across its full depth.')):
        _axes(ax, (-2.3, 2.3), (-3.0, 2.2))
        ax.add_patch(Rectangle((-0.8, -0.6), 1.6, 1.4, facecolor='#f4f4f4',
                               edgecolor=GRID, lw=1.0, zorder=1))
        xs = np.linspace(-0.8, 0.8, 9)
        ax.scatter(xs, np.full(9, -0.6), s=22, c=MUG, zorder=4)
        side = np.linspace(-0.6, -0.25, 3)
        ax.scatter(np.full(3, -0.8), side, s=22, c=MUG, zorder=4)
        ax.scatter(np.full(3, 0.8), side, s=22, c=MUG, zorder=4)
        if complete:
            ys = np.linspace(-0.08, 0.8, 5)
            ax.scatter(np.full(5, -0.8), ys, s=22, c=NEW, zorder=4)
            ax.scatter(np.full(5, 0.8), ys, s=22, c=NEW, zorder=4)
            ax.scatter(xs, np.full(9, 0.8), s=22, c=NEW, zorder=4)
            cy = 0.1
        else:
            cy = -0.5
        ax.plot(0, cy, 'x', color=GRIP, ms=11, mew=2.2, zorder=5)
        _label(ax, 0.0, cy + 0.25, 'middle', size=9, color=GRIP)
        for sgn in (-1, 1):
            ax.add_patch(Rectangle((sgn * 0.8 + (0.0 if sgn > 0 else -0.25), cy - 0.3),
                                   0.25, 0.6, facecolor=GRIP, edgecolor=INK, lw=0.8,
                                   zorder=6, alpha=0.85))
        _camera(ax, 0.0, -1.45, math.pi / 2, size=0.2)
        _label(ax, 0.35, -1.5, 'camera', size=9, color=MUTED, ha='left')
        _title(ax, 0.0, 1.8, title)
        _caption(ax, 0.0, -1.95, cap)
    _save(fig, COMPLETION_DOC, 'grasp-with-and-without.svg')


def training_pairs() -> None:
    """Training data: a full 3D model, the part of it one camera would see, as a pair."""
    fig, ax = plt.subplots(figsize=(12.0, 4.4), facecolor='white')
    _axes(ax, (-1.2, 10.6), (-1.3, 2.4))
    mug = _mug_points()
    front = _seen_from_front(mug)
    _scatter(ax, mug, INK, size=8)
    _label(ax, 0.2, 1.8, 'A full 3D model', size=12, weight='bold')
    _caption(ax, 0.2, -0.3, 'from a collection\nof 3D shapes')
    _arrow(ax, (1.4, 0.6), (2.6, 0.6))
    _label(ax, 2.0, 1.0, 'pretend a camera\nlooks from the front', size=9, color=MUTED)
    _scatter(ax, mug[front], MUG, size=8, offset=(3.8, 0.0))
    _label(ax, 4.0, 1.8, 'The part it would see', size=12, weight='bold')
    _caption(ax, 4.0, -0.3, 'the question')
    ax.add_patch(Rectangle((2.85, -1.25), 6.3, 3.3, facecolor='none', edgecolor=JOINT,
                           lw=1.4, ls='--', zorder=1))
    _scatter(ax, mug, INK, size=8, offset=(7.6, 0.0))
    _label(ax, 7.8, 1.8, 'The whole shape', size=12, weight='bold')
    _caption(ax, 7.8, -0.3, 'the right answer')
    _label(ax, 6.0, -1.0, 'one training pair', color=JOINT)
    _save(fig, COMPLETION_DOC, 'training-pairs.svg')


# --------------------------------------------------------------------------
# 04_scene-reconstruction
# --------------------------------------------------------------------------

SCENE_DOC: str = 'scene-reconstruction'


def pictures_from_many_places() -> None:
    """A top view: a wrist camera takes pictures of a mug from many known places."""
    fig, ax = plt.subplots(figsize=(7.4, 6.4), facecolor='white')
    _axes(ax, (-3.0, 3.4), (-3.0, 2.8))
    ax.add_patch(Circle((0, 0), 0.5, facecolor=LINK_PALE, edgecolor=MUG, lw=1.6, zorder=3))
    ax.add_patch(Rectangle((0.5, -0.1), 0.3, 0.2, facecolor=LINK_PALE, edgecolor=MUG,
                           lw=1.6, zorder=2))
    _label(ax, 0.0, 0.0, 'mug', size=9)
    n = 10
    for k in range(n):
        a = math.pi * 1.1 + 2 * math.pi * 0.8 * k / (n - 1)
        x, y = 2.0 * math.cos(a), 2.0 * math.sin(a)
        _camera(ax, x, y, math.atan2(-y, -x), size=0.18)
        ax.plot([x * 0.9, x * 0.3], [y * 0.9, y * 0.3], color=GRID, lw=0.8, ls=':',
                zorder=1)
        _label(ax, x * 1.22, y * 1.22, str(k + 1), size=9, color=MUTED)
    ax.plot(2.0 * np.cos(np.linspace(math.pi * 1.1, math.pi * 2.7, 80)),
            2.0 * np.sin(np.linspace(math.pi * 1.1, math.pi * 2.7, 80)),
            color=JOINT, lw=1.0, ls='--', zorder=1)
    _caption(ax, 0.2, -2.55, 'The arm moves its wrist camera round the mug and takes a '
             'picture at each place.\nThe arm\'s joint readings say exactly where '
             'the camera was each time.', size=9)
    _save(fig, SCENE_DOC, 'pictures-from-many-places.svg')


def a_ray_through_the_scene() -> None:
    """NeRF: follow one pixel's line of sight and ask the network about points along it."""
    fig, ax = plt.subplots(figsize=(12.0, 5.4), facecolor='white')
    _axes(ax, (-1.4, 11.4), (-2.8, 2.6))
    _camera(ax, 0.0, 0.8, 0.0, size=0.3)
    _label(ax, 0.0, 1.4, 'camera', size=10)
    ax.add_patch(Rectangle((0.6, 0.2), 0.08, 1.2, facecolor=GRID, edgecolor=INK, lw=0.6))
    _label(ax, 0.64, 1.7, 'one pixel', size=9, color=MUTED)
    ax.plot([0.3, 10.9], [0.8, 0.8], color=JOINT, lw=1.2, zorder=2)
    walls = ((5.6, 6.3, 'near wall of the mug'), (9.0, 9.7, 'far wall'))
    for x_a, x_b, name in walls:
        ax.add_patch(Rectangle((x_a, -0.2), x_b - x_a, 2.0, facecolor=LINK_PALE,
                               edgecolor=MUG, lw=1.4, zorder=1))
        _label(ax, (x_a + x_b) / 2, 2.05, name, size=9, color=MUG)
    xs = np.arange(1.5, 10.7, 0.6)
    for x in xs:
        solid = any(a <= x <= b for a, b, _ in walls)
        hidden = solid and x > 7.0
        face = 'white' if not solid else (LINK_PALE if hidden else MUG)
        ax.plot(x, 0.8, 'o', ms=8, color=face, mec=INK, mew=0.8, zorder=4)
        if solid:
            ax.add_patch(Rectangle((x - 0.2, -2.0), 0.4, 1.3,
                                   facecolor=LINK_PALE if hidden else MUG,
                                   edgecolor='none', zorder=3))
    ax.plot([1.0, 10.9], [-2.0, -2.0], color=MUTED, lw=1.0)
    _label(ax, 1.0, -0.9, 'how solid the network\nsays each point is', size=9, ha='left',
           color=MUTED)
    _label(ax, 3.4, -2.35, 'empty air: adds nothing', size=9, color=MUTED)
    _label(ax, 5.95, -2.35, 'first solid point:\ngives the pixel its colour', size=9,
           color=MUG)
    _label(ax, 9.35, -2.35, 'behind it: hidden,\ncounts almost nothing', size=9,
           color=MUTED)
    _save(fig, SCENE_DOC, 'a-ray-through-the-scene.svg')


def mug_made_of_blobs() -> None:
    """Gaussian splatting: the scene is stored as many soft, coloured, see-through blobs."""
    fig, (left, right) = _panels(2, (12.0, 4.8))
    rng = np.random.default_rng(7)
    for ax in (left, right):
        _axes(ax, (-1.5, 3.1), (-0.9, 2.3))
    _mug_outline(left, 0.0, 0.0, w=1.4, h=1.6)
    _title(left, 0.1, 2.05, 'The real mug')
    _caption(left, 0.1, -0.3, 'One object, drawn as it looks.')
    for _ in range(170):
        x = rng.uniform(-0.65, 0.65)
        y = rng.uniform(0.1, 1.55)
        right.add_patch(Ellipse((x, y), rng.uniform(0.12, 0.35), rng.uniform(0.06, 0.22),
                                angle=rng.uniform(0, 180), facecolor=MUG, alpha=0.25,
                                edgecolor='none', zorder=2))
    for k in range(16):
        t = -math.pi / 2 + math.pi * k / 15
        right.add_patch(Ellipse((0.72 + 0.26 * math.cos(t), 0.8 + 0.3 * math.sin(t)),
                                0.16, 0.08, angle=math.degrees(t) + 90, facecolor=MUG,
                                alpha=0.45, edgecolor='none', zorder=2))
    # One blob, drawn larger, with what it stores.
    right.add_patch(Ellipse((2.1, 1.35), 0.9, 0.4, angle=20, facecolor=MUG, alpha=0.35,
                            edgecolor=GRIP, lw=1.0, ls='--', zorder=3))
    right.plot(2.1, 1.35, 'o', color=GRIP, ms=3, zorder=4)
    _label(right, 2.1, 0.6, 'one blob stores:\na place, a size,\na direction, a colour,\n'
           'how see-through it is', size=9, color=GRIP)
    _title(right, 0.8, 2.05, 'Stored as blobs')
    _caption(right, 0.0, -0.3, 'Thousands of soft blobs, drawn on\n'
             'top of each other, make the picture.')
    _save(fig, SCENE_DOC, 'mug-made-of-blobs.svg')


# --------------------------------------------------------------------------
# 05_3d-feature-maps
# --------------------------------------------------------------------------

FEATURES_DOC: str = '3d-feature-maps'


def numbers_on_every_point() -> None:
    """A plain point has 3 numbers; a point in a feature map also carries a list of meaning."""
    fig, ax = plt.subplots(figsize=(11.0, 4.8), facecolor='white')
    _axes(ax, (-1.4, 9.6), (-1.2, 2.4))
    mug = _mug_points()
    front = _seen_from_front(mug)
    _scatter(ax, mug[front], MUG, size=9)
    picks = [(np.array([0.54, 0.0, 0.62]), (2.4, 1.6),
              'x, y, z = 0.54, 0.00, 0.62', '[ 0.8, −0.1, 0.4, 0.9, … ]'),
             (np.array([0.2, -0.35, 0.3]), (2.4, 0.1),
              'x, y, z = 0.20, −0.35, 0.30', '[ 0.1, 0.7, −0.3, 0.2, … ]')]
    for p, at, pos, feat in picks:
        uv = _iso(p)[0]
        ax.plot(uv[0], uv[1], 'o', ms=10, mfc='none', mec=GRIP, mew=1.8, zorder=6)
        ax.plot([uv[0], at[0] - 0.1], [uv[1], at[1]], color=GRIP, lw=0.9, zorder=5)
        _label(ax, at[0], at[1] + 0.2, pos, ha='left')
        _label(ax, at[0], at[1] - 0.2, feat, ha='left', color=SLIDE)
    _label(ax, 6.9, 1.8, 'where the point is', ha='left')
    _label(ax, 6.9, 1.4, 'what the point is part of,\nas a list of numbers', ha='left',
           color=SLIDE)
    _caption(ax, 3.8, -0.6, 'In a 3D feature map every point keeps its position and also '
             'carries a list of numbers,\nlearned from pictures, that says what kind of '
             'thing it belongs to.')
    _save(fig, FEATURES_DOC, 'numbers-on-every-point.svg')


def from_pictures_to_3d() -> None:
    """Two views of the same spot give two lists of numbers; the map stores their average."""
    fig, ax = plt.subplots(figsize=(11.0, 5.6), facecolor='white')
    _axes(ax, (-0.5, 11.0), (-2.2, 3.4))
    for k, (x0, name) in enumerate(((0.0, 'picture 1'), (7.2, 'picture 2'))):
        ax.add_patch(Rectangle((x0, 0.6), 3.0, 2.2, facecolor='#f4f4f4', edgecolor=INK,
                               lw=1.0))
        mx = x0 + (1.3 if k == 0 else 1.7)
        ax.add_patch(Rectangle((mx - 0.5, 1.0), 1.0, 1.2, facecolor=LINK_PALE,
                               edgecolor=MUG, lw=1.4))
        hx = mx + 0.5 if k == 0 else mx - 0.5
        ax.plot(hx + (0.18 if k == 0 else -0.18), 1.6, 'o', ms=14, mfc='none', mec=MUG,
                mew=3)
        ax.plot(hx + (0.25 if k == 0 else -0.25), 1.6, 'o', ms=7, color=GRIP, zorder=5)
        _label(ax, x0 + 1.5, 3.1, name, weight='bold')
        _label(ax, x0 + 1.5, 0.3, '[ 0.9, 0.1, … ]' if k == 0 else '[ 0.7, 0.3, … ]',
               color=SLIDE)
        _arrow(ax, (x0 + 1.5, 0.05), (5.1 + (-0.35 if k == 0 else 0.35), -0.9))
    ax.scatter([5.1], [-1.1], s=90, c=GRIP, zorder=5)
    _label(ax, 5.1, -1.5, 'one point in the 3D map', size=10)
    _label(ax, 5.1, -1.9, 'stores the average:  [ 0.8, 0.2, … ]', size=10, color=SLIDE)
    _label(ax, 5.1, 2.3, 'An image model gives\na list of numbers for\nevery pixel.\n\n'
           'The camera positions\nsay which pixels\nshow the same spot.', size=9,
           color=MUTED)
    _save(fig, FEATURES_DOC, 'from-pictures-to-3d.svg')


def ask_with_a_word() -> None:
    """Type a word; the map colours each point by how well it matches that word."""
    fig, axes = _panels(3, (12.0, 4.4))
    mug = _mug_points()
    front = _seen_from_front(mug)
    handle = _is_handle(mug)
    rim = mug[:, 2] > 0.85
    for ax, words, mask in ((axes[0], None, None), (axes[1], '"handle"', handle),
                            (axes[2], '"where to drink from"', rim)):
        _axes(ax, (-1.1, 1.5), (-0.8, 1.9))
        if mask is None:
            _scatter(ax, mug[front], MUG, size=9)
            _title(ax, 0.2, 1.6, 'The map')
            _caption(ax, 0.2, -0.35, 'Every point has its\nlist of numbers.')
        else:
            cols = [HOT if m else LINK_PALE for m in mask[front]]
            _scatter(ax, mug[front], cols, size=10)
            _title(ax, 0.2, 1.6, words)
            _caption(ax, 0.2, -0.35, 'red = points whose numbers\nmatch the words best')
    _save(fig, FEATURES_DOC, 'ask-with-a-word.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    what_a_point_cloud_is()
    four_questions()
    order_does_not_matter()
    shared_network_then_max()
    a_label_on_every_point()
    small_neighbourhoods()
    camera_sees_one_side()
    partial_in_complete_out()
    grasp_with_and_without()
    training_pairs()
    pictures_from_many_places()
    a_ray_through_the_scene()
    mug_made_of_blobs()
    numbers_on_every_point()
    from_pictures_to_3d()
    ask_with_a_word()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
