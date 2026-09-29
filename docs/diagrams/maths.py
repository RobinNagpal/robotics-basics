"""Generate the diagrams used in the docs/01_robotics-intro/02_maths/ docs.

Each doc's images go to a folder named after it, under docs/images/maths/:
angles-and-trigonometry/ and vectors-and-matrices/.

Run with:  pixi run python ../docs/diagrams/maths.py

There is one picture per idea. They draw the same arm as the frames doc, link 1
3 m and link 2 2 m at q1 = 30 degrees and q2 = 60 degrees, so a reader can carry
numbers from one doc to the next.
"""

import math
import os
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Wedge  # noqa: E402  (must follow matplotlib.use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'maths'
ANGLES_DIR: pathlib.Path = IMAGES / 'angles-and-trigonometry'
VECTORS_DIR: pathlib.Path = IMAGES / 'vectors-and-matrices'

GRID: str = '#d6d6d6'
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b82c4'
LINK: str = '#3b82c4'
LINK_PALE: str = '#b9d3ea'
JOINT: str = '#f0a500'
GRIP: str = '#e05555'
RESULT: str = '#7b3fbf'
INK: str = '#222222'
MUTED: str = '#777777'
BLOCKED: str = '#f4c7c7'

L1: float = 3.0
L2: float = 2.0
Q1: float = math.radians(30.0)
Q2: float = math.radians(60.0)
ELBOW: tuple[float, float] = (L1 * math.cos(Q1), L1 * math.sin(Q1))
GRIPPER: tuple[float, float] = (ELBOW[0] + L2 * math.cos(Q1 + Q2),
                                ELBOW[1] + L2 * math.sin(Q1 + Q2))

Point = tuple[float, float]


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(xlim: tuple[float, float], ylim: tuple[float, float],
          size: tuple[float, float] = (6.4, 5.6), ax: Axes | None = None) -> tuple[Figure, Axes]:
    fig: Figure
    if ax is None:
        fig, ax = plt.subplots(figsize=size, facecolor='white')
    else:
        fig = ax.figure  # type: ignore[assignment]
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _arrow(ax: Axes, start: Point, end: Point, color: str, lw: float = 2.2,
           style: str = '-|>') -> None:
    ax.annotate('', xy=end, xytext=start,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0, 'mutation_scale': 16},
                zorder=4)


def _link(ax: Axes, start: Point, end: Point, color: str = LINK, width: float = 7) -> None:
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=width,
            solid_capstyle='round', zorder=2)


def _dot(ax: Axes, point: Point, color: str = JOINT, size: float = 12) -> None:
    ax.plot([point[0]], [point[1]], 'o', color=color, ms=size, zorder=5)


def _dashed(ax: Axes, start: Point, end: Point, color: str = GRID, lw: float = 1.0) -> None:
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=lw,
            ls=(0, (4, 3)), zorder=1)


def _arc(ax: Axes, centre: Point, radius: float, a1: float, a2: float,
         color: str = MUTED, lw: float = 1.3) -> None:
    """Draw an arc from angle a1 to a2 (radians, a1 < a2)."""
    ax.add_patch(Arc(centre, 2 * radius, 2 * radius, theta1=math.degrees(a1),
                     theta2=math.degrees(a2), color=color, lw=lw, zorder=3))


def _label(ax: Axes, x: float, y: float, text: str, color: str = INK, size: float = 10,
           ha: str = 'center', mono: bool = True) -> None:
    ax.text(x, y, text, color=color, fontsize=size, ha=ha, va='center',
            family='monospace' if mono else None, zorder=6)


def _title(ax: Axes, x: float, y: float, text: str) -> None:
    ax.text(x, y, text, fontsize=13, ha='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', color=MUTED)


def _axes_lines(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    """Draw the table's x and y axes as thin grey lines through the origin."""
    ax.plot(xlim, [0, 0], color=GRID, lw=1.0, zorder=0)
    ax.plot([0, 0], ylim, color=GRID, lw=1.0, zorder=0)


def _save(fig: Figure, folder: pathlib.Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    # Set PNG_DIR to also write a PNG of each picture, for checking it by eye.
    png_dir: str | None = os.environ.get('PNG_DIR')
    if png_dir:
        fig.savefig(pathlib.Path(png_dir) / name.replace('.svg', '.png'), dpi=110,
                    bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)


def _polar(radius: float, angle: float, centre: Point = (0.0, 0.0)) -> Point:
    return (centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle))


# --------------------------------------------------------------------------
# angles and trigonometry
# --------------------------------------------------------------------------

def radians() -> None:
    """Two links turning the same 30 degrees: the longer one's tip travels further."""
    fig, ax = _axes((-0.6, 3.9), (-0.9, 2.3), size=(6.8, 3.9))
    turn: float = Q1
    for length, pale in ((3.0, True), (1.0, True)):
        _link(ax, (0, 0), (length, 0), color=LINK_PALE, width=5)
    for length in (3.0, 1.0):
        _link(ax, (0, 0), _polar(length, turn), width=5)
        _arc(ax, (0, 0), length, 0.0, turn, color=GRIP, lw=2.6)
        _dot(ax, _polar(length, turn), color=GRIP, size=8)
    _dot(ax, (0, 0))

    _label(ax, 3.06, 0.78, 'arc = 3 × 0.524\n    = 1.571 m', ha='left', color=GRIP)
    _label(ax, 1.08, 0.28, 'arc = 1 × 0.524\n    = 0.524 m', ha='left', color=GRIP, size=9)
    _label(ax, 1.5, -0.3, 'link 3 m, before the turn', color=MUTED, size=9)
    _label(ax, 0.62, 0.80, 'turned\n30° = 0.524 rad', color=INK, size=9, ha='right')

    _title(ax, 1.65, 2.05, 'Radians: arc length per metre of link')
    _caption(ax, 1.65, -0.75, "same turn, 30°; the 3 m link's tip travels three times as far")
    _save(fig, ANGLES_DIR, 'radians.svg')


def across_and_up() -> None:
    """Draw a 3 m link at 30 and at 120 degrees: cos gives across, sin gives up."""
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), facecolor='white')
    for ax, degrees in zip(axes, (30.0, 120.0)):
        xlim: tuple[float, float] = (-2.6, 3.6)
        ylim: tuple[float, float] = (-0.9, 3.4)
        _axes(xlim, ylim, ax=ax)
        _axes_lines(ax, xlim, ylim)
        a: float = math.radians(degrees)
        tip: Point = _polar(3.0, a)
        _dashed(ax, (tip[0], 0.0), tip, color=AXIS_Y, lw=1.6)
        ax.plot([0, tip[0]], [0, 0], color=AXIS_X, lw=3.0, zorder=2)
        _link(ax, (0, 0), tip, width=6)
        _dot(ax, (0, 0))
        _dot(ax, tip, color=GRIP, size=9)
        _arc(ax, (0, 0), 0.7, 0.0, a)
        mid_a: float = a / 2
        ax.text(*_polar(1.05, mid_a), f'{degrees:.0f}°', fontsize=10, ha='center',
                va='center', color=INK, family='monospace')
        across: float = 3.0 * math.cos(a)
        up: float = 3.0 * math.sin(a)
        _label(ax, across / 2, -0.35, f'across = 3·cos({degrees:.0f}°) = {across:.3f}',
               color=AXIS_X, size=9)
        side: float = 0.12 if across > 0 else -0.12
        _label(ax, tip[0] + side, tip[1] / 2, f'up = 3·sin({degrees:.0f}°)\n   = {up:.3f}',
               color=AXIS_Y, size=9, ha='left' if across > 0 else 'right')
        _title(ax, 0.5, 3.2, f'Link at {degrees:.0f}°')
    _caption(axes[1], 0.5, -0.8, 'past 90°, cos goes negative: the link reaches backwards')
    _caption(axes[0], 0.5, -0.8, 'cos gives across, sin gives up')
    _save(fig, ANGLES_DIR, 'across-and-up.svg')


def atan2_picture() -> None:
    """Two opposite points have the same y/x; only atan2 tells them apart."""
    fig, ax = _axes((-3.4, 3.4), (-3.2, 3.2), size=(6.2, 6.0))
    _axes_lines(ax, (-3.2, 3.2), (-3.0, 3.0))
    for point, color in (((2.0, 2.0), LINK), ((-2.0, -2.0), GRIP)):
        _arrow(ax, (0, 0), point, color)
        _dot(ax, point, color=color, size=8)
    _dot(ax, (0, 0))

    _arc(ax, (0, 0), 0.8, 0.0, math.radians(45), color=LINK, lw=2)
    _arc(ax, (0, 0), 1.3, math.radians(-135), 0.0, color=GRIP, lw=2)
    _label(ax, 2.1, 2.45, '(2, 2)', color=LINK)
    _label(ax, -2.1, -2.45, '(-2, -2)', color=GRIP)
    _label(ax, 1.0, 0.33, '45°', color=LINK, size=9, ha='left')
    _label(ax, 1.05, -1.25, '-135°', color=GRIP, size=9, ha='left')

    _label(ax, -3.2, 2.7, 'atan(y/x):', ha='left', mono=True)
    _label(ax, -3.2, 2.3, '  (2, 2)   -> 45°', ha='left', color=LINK, size=9)
    _label(ax, -3.2, 1.95, '  (-2, -2) -> 45°  wrong', ha='left', color=GRIP, size=9)
    _label(ax, 0.6, -2.2, 'atan2(y, x):', ha='left')
    _label(ax, 0.6, -2.6, '  (2, 2)   -> 45°', ha='left', color=LINK, size=9)
    _label(ax, 0.6, -2.95, '  (-2, -2) -> -135°', ha='left', color=GRIP, size=9)

    _title(ax, 0, 3.15, 'Opposite points, same y / x')
    _save(fig, ANGLES_DIR, 'atan2.svg')


def law_of_cosines() -> None:
    """Draw the triangle made by the two links and the shoulder-to-gripper line."""
    fig, ax = _axes((-0.9, 4.4), (-0.9, 4.3), size=(6.0, 5.2))
    _dashed(ax, (0, 0), GRIPPER, color=RESULT, lw=2.0)
    _link(ax, (0, 0), ELBOW)
    _link(ax, ELBOW, GRIPPER)
    ext: Point = _polar(1.3, Q1, ELBOW)
    _dashed(ax, ELBOW, ext)
    _dot(ax, (0, 0))
    _dot(ax, ELBOW)
    _dot(ax, GRIPPER, color=GRIP, size=10)

    # The inside angle at the elbow runs from the direction back to the shoulder
    # (210 degrees) round to link 2 (90 degrees), going clockwise: 120 degrees.
    _arc(ax, ELBOW, 0.5, Q1 + Q2, Q1 + math.pi, color=RESULT, lw=2)
    _label(ax, ELBOW[0] - 0.55, ELBOW[1] + 0.52, '120°', color=RESULT, size=10)
    _arc(ax, ELBOW, 0.85, Q1, Q1 + Q2)
    _label(ax, ELBOW[0] + 0.95, ELBOW[1] + 0.62, 'q2 = 60°', size=10, ha='left')

    _label(ax, 1.55, 0.35, 'L1 = 3', color=LINK, size=10, ha='left')
    _label(ax, ELBOW[0] + 0.12, ELBOW[1] + 1.35, 'L2 = 2', color=LINK, size=10, ha='left')
    _label(ax, 0.75, 1.8, 'd = 4.359', color=RESULT, size=10, ha='right')
    _label(ax, -0.1, -0.35, 'shoulder', color=MUTED, size=9)
    _label(ax, ELBOW[0] + 0.1, ELBOW[1] - 0.35, 'elbow', color=MUTED, size=9, ha='left')
    _label(ax, GRIPPER[0] + 0.2, GRIPPER[1] + 0.1, 'gripper', color=MUTED, size=9, ha='left')

    _title(ax, 1.75, 4.1, 'Two links make a triangle')
    _caption(ax, 1.75, -0.8, 'd² = 3² + 2² - 2·3·2·cos(120°) = 19,  so d = 4.359 m')
    _save(fig, ANGLES_DIR, 'law-of-cosines.svg')


def wrapping() -> None:
    """Left: 350 and -10 degrees end at the same place. Right: a limit forces the long way."""
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.0), facecolor='white')

    ax = axes[0]
    _axes((-1.9, 1.9), (-1.9, 1.9), ax=ax)
    _axes_lines(ax, (-1.6, 1.6), (-1.6, 1.6))
    _arc(ax, (0, 0), 0.8, 0.0, math.radians(350), color=LINK, lw=2)
    _arc(ax, (0, 0), 1.2, math.radians(-10), 0.0, color=GRIP, lw=2.4)
    _link(ax, (0, 0), _polar(1.5, math.radians(-10)), width=5)
    _dot(ax, (0, 0))
    _label(ax, -0.2, 1.0, '+350°, the long way', color=LINK, size=9)
    _label(ax, 1.3, 0.45, '-10°', color=GRIP, size=10, ha='left')
    _title(ax, 0, 1.75, 'Two numbers, one direction')
    _caption(ax, 0, -1.8, 'the link ends at the same place either way')

    ax = axes[1]
    _axes((-1.9, 1.9), (-1.9, 1.9), ax=ax)
    ax.add_patch(Wedge((0, 0), 1.45, 175, 185, color=BLOCKED, zorder=1))
    start: float = math.radians(170)
    goal: float = math.radians(-170)
    _link(ax, (0, 0), _polar(1.45, start), color=LINK_PALE, width=5)
    _link(ax, (0, 0), _polar(1.45, goal), width=5)
    _dot(ax, (0, 0))
    ax.add_patch(Arc((0, 0), 2.1, 2.1, theta1=170, theta2=190, color=GRIP, lw=2,
                     ls=(0, (3, 2)), zorder=3))
    _arc(ax, (0, 0), 0.7, math.radians(-170), math.radians(170), color=AXIS_Y, lw=2.2)
    _label(ax, -1.6, 0.0, 'no-go past ±175°:\nthe +20° turn\nis blocked', color=GRIP, size=9,
           ha='right')
    _label(ax, -1.2, 0.62, 'start 170°', color=MUTED, size=9, ha='right')
    _label(ax, -1.2, -0.62, 'goal -170°', color=LINK, size=9, ha='right')
    _label(ax, 0.9, -0.9, '-340°: allowed', color=AXIS_Y, size=9, ha='left')
    _title(ax, 0, 1.75, 'A joint limit forces the long way')
    _caption(ax, 0, -1.8, 'the short turn would pass through 180°')
    _save(fig, ANGLES_DIR, 'wrapping.svg')


# --------------------------------------------------------------------------
# vectors and matrices
# --------------------------------------------------------------------------

def tip_to_tail() -> None:
    """Add the two link arrows tip to tail to get the arrow from base to gripper."""
    fig, ax = _axes((-0.9, 4.4), (-0.9, 4.3), size=(6.0, 5.2))
    _arrow(ax, (0, 0), ELBOW, LINK, lw=3)
    _arrow(ax, ELBOW, GRIPPER, AXIS_Y, lw=3)
    _arrow(ax, (0, 0), GRIPPER, RESULT, lw=2.2)
    _dot(ax, (0, 0), size=9)

    _label(ax, 1.75, 0.55, 'link 1\n(2.598, 1.5)', color=LINK, size=9, ha='left')
    _label(ax, ELBOW[0] + 0.15, ELBOW[1] + 1.0, 'link 2\n(0, 2)', color=AXIS_Y, size=9,
           ha='left')
    _label(ax, 1.1, 2.35, 'sum\n(2.598, 3.5)', color=RESULT, size=9, ha='right')
    _label(ax, GRIPPER[0] + 0.15, GRIPPER[1] + 0.15, 'gripper', color=MUTED, size=9, ha='left')
    _label(ax, -0.1, -0.35, 'base', color=MUTED, size=9)

    _title(ax, 1.75, 4.1, 'Add the links tip to tail')
    _caption(ax, 1.75, -0.8, '(2.598, 1.5) + (0, 2) = (2.598, 3.5), length 4.359')
    _save(fig, VECTORS_DIR, 'tip-to-tail.svg')


def dot_product() -> None:
    """Draw the two link arrows tail to tail, with the angle the dot product gives."""
    fig, ax = _axes((-0.6, 3.3), (-0.6, 2.6), size=(5.6, 4.4))
    link1: Point = ELBOW
    link2: Point = (0.0, 2.0)
    _arrow(ax, (0, 0), link1, LINK, lw=3)
    _arrow(ax, (0, 0), link2, AXIS_Y, lw=3)
    _dot(ax, (0, 0), size=9)
    _arc(ax, (0, 0), 0.7, Q1, math.radians(90), color=RESULT, lw=2)
    _label(ax, 0.55, 0.75, '60°', color=RESULT, size=10)
    _label(ax, link1[0] + 0.1, link1[1] + 0.1, 'link 1 (2.598, 1.5)', color=LINK, size=9,
           ha='right')
    _label(ax, 0.15, 2.05, 'link 2 (0, 2)', color=AXIS_Y, size=9, ha='left')

    _title(ax, 1.35, 2.45, 'Both links from one point')
    _caption(ax, 1.35, -0.5, 'dot = 2.598·0 + 1.5·2 = 3;  3 / (3·2) = 0.5 = cos(60°)')
    _save(fig, VECTORS_DIR, 'dot-product.svg')


def rotation_columns() -> None:
    """Show that the 30 degree rotation matrix's columns are the turned x and y axes."""
    fig, ax = _axes((-1.3, 1.9), (-0.55, 1.6), size=(6.0, 4.3))
    for angle, color in ((0.0, AXIS_X), (math.pi / 2, AXIS_Y)):
        _arrow(ax, (0, 0), _polar(1.0, angle), GRID, lw=1.6)
    x_new: Point = _polar(1.0, Q1)
    y_new: Point = _polar(1.0, Q1 + math.pi / 2)
    _arrow(ax, (0, 0), x_new, AXIS_X, lw=2.6)
    _arrow(ax, (0, 0), y_new, AXIS_Y, lw=2.6)
    _arc(ax, (0, 0), 0.45, 0.0, Q1)
    _label(ax, 0.58, 0.14, '30°', size=9, ha='left')
    _label(ax, 1.05, -0.12, 'old x', color=MUTED, size=9, ha='left')
    _label(ax, 0.07, 1.08, 'old y', color=MUTED, size=9, ha='left')
    _label(ax, x_new[0] + 0.07, x_new[1] + 0.05, 'column 1\n(0.866, 0.5)', color=AXIS_X,
           size=9, ha='left')
    _label(ax, y_new[0] - 0.07, y_new[1] + 0.1, 'column 2\n(-0.5, 0.866)', color=AXIS_Y,
           size=9, ha='right')
    _dot(ax, (0, 0), size=8)

    _label(ax, 1.0, 1.35, '[ 0.866  -0.5  ]\n[ 0.5     0.866]', size=10, ha='left')
    _caption(ax, 0.3, -0.45, 'turn by 30°: each column is where one axis ends up')
    _save(fig, VECTORS_DIR, 'rotation-columns.svg')


def transform_columns() -> None:
    """Draw a 3 x 3 transform matrix as the frame it describes."""
    fig, ax = _axes((-1.0, 5.3), (-1.2, 4.9), size=(6.6, 6.2))
    _link(ax, (0, 0), ELBOW, color=LINK_PALE, width=6)
    _link(ax, ELBOW, GRIPPER, color=LINK_PALE, width=6)
    _dot(ax, (0, 0), size=9)
    _dot(ax, GRIPPER, color=GRIP, size=9)

    # The base frame, in grey, and the arrow to the gripper: the third column.
    _arrow(ax, (0, 0), (1.0, 0.0), AXIS_X, lw=1.6)
    _arrow(ax, (0, 0), (0.0, 1.0), AXIS_Y, lw=1.6)
    _arrow(ax, (0, 0), GRIPPER, RESULT, lw=2.0)
    _label(ax, 1.4, 2.6, 'column 3\n(2.598, 3.5)\nwhere it is', color=RESULT, size=9,
           ha='right')

    # The gripper frame: its x axis points up the table, its y axis points left.
    _arrow(ax, GRIPPER, (GRIPPER[0], GRIPPER[1] + 1.0), AXIS_X, lw=2.6)
    _arrow(ax, GRIPPER, (GRIPPER[0] - 1.0, GRIPPER[1]), AXIS_Y, lw=2.6)
    _label(ax, GRIPPER[0] + 0.12, GRIPPER[1] + 0.8, 'column 1 (0, 1)\ngripper x axis',
           color=AXIS_X, size=9, ha='left')
    _label(ax, GRIPPER[0] - 1.3, GRIPPER[1] + 0.4, 'column 2 (-1, 0)\ngripper y axis',
           color=AXIS_Y, size=9)
    _label(ax, 0.1, -0.35, 'base', color=MUTED, size=9)

    _label(ax, 2.7, 0.9, '[ 0  -1   2.598 ]\n[ 1   0   3.5   ]\n[ 0   0   1     ]', size=10,
           ha='left')
    _title(ax, 2.15, 4.95, 'A transform matrix is a frame')
    _caption(ax, 2.15, -1.05, 'base -> gripper at q1 = 30°, q2 = 60°')
    _save(fig, VECTORS_DIR, 'transform-columns.svg')


def _rot_x(a: float) -> NDArray[np.float64]:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def _rot_z(a: float) -> NDArray[np.float64]:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def order_3d() -> None:
    """Turn a tool about z then x, and about x then z, to show two different results."""
    fig = plt.figure(figsize=(10.4, 4.8), facecolor='white')
    quarter: float = math.pi / 2
    tool: NDArray[np.float64] = np.array([1.0, 0.0, 0.0])
    cases: tuple[tuple[str, list[NDArray[np.float64]], str], ...] = (
        ('about z, then about x', [_rot_z(quarter), _rot_x(quarter)], 'ends pointing up (z)'),
        ('about x, then about z', [_rot_x(quarter), _rot_z(quarter)], 'ends pointing along y'),
    )
    for index, (title, steps, result) in enumerate(cases):
        ax = fig.add_subplot(1, 2, index + 1, projection='3d')
        ax.set_proj_type('ortho')
        ax.view_init(elev=22, azim=35)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_zlim(-1.1, 1.1)
        ax.set_box_aspect((1, 1, 1))
        ax.set_axis_off()
        for axis, color, name in ((np.eye(3)[0], AXIS_X, 'x'), (np.eye(3)[1], AXIS_Y, 'y'),
                                  (np.eye(3)[2], AXIS_Z, 'z')):
            ax.plot([0, axis[0]], [0, axis[1]], [0, axis[2]], color=color, lw=1.2, alpha=0.6)
            ax.text(*(axis * 1.2), name, color=color, fontsize=11, ha='center')
        positions: list[NDArray[np.float64]] = [tool]
        for step in steps:
            positions.append(np.round(step @ positions[-1], 9))
        names: tuple[str, ...] = ('start', 'after 1st turn', 'after 2nd turn')
        shades: tuple[str, ...] = (GRID, MUTED, GRIP)
        # Where to write the label for an arrow along each axis, clear of the axis names.
        spots: dict[int, tuple[float, float, float]] = {0: (0.75, -0.05, -0.32),
                                                        1: (0.0, 0.62, -0.3),
                                                        2: (0.0, 0.1, 0.62)}
        # Arrows that end up along the same axis share one label.
        by_axis: dict[int, list[str]] = {}
        for shade, name, p in zip(shades, names, positions):
            ax.quiver(0, 0, 0, *(0.85 * p), color=shade, lw=3, arrow_length_ratio=0.18)
            by_axis.setdefault(int(np.argmax(np.abs(p))), []).append(name)
        for axis_index, group in by_axis.items():
            ax.text(*spots[axis_index], ' = '.join(group), color=INK, fontsize=9)
        ax.set_title(f'Turn 90° {title}', fontsize=12, color=INK, weight='bold', pad=0)
        ax.text2D(0.5, 0.02, result, transform=ax.transAxes, ha='center', color=MUTED,
                  fontsize=10)
    _save(fig, VECTORS_DIR, 'order-3d.svg')


if __name__ == '__main__':
    radians()
    across_and_up()
    atan2_picture()
    law_of_cosines()
    wrapping()
    tip_to_tail()
    dot_product()
    rotation_columns()
    transform_columns()
    order_3d()
    print(f'wrote {len(list(IMAGES.rglob("*.svg")))} diagrams under {IMAGES}')
