"""Generate the diagrams used in docs/04_numpy/numpy-intro.md.

The images go to docs/images/numpy/numpy-intro/.

Run with:  pixi run python docs/diagrams/numpy_intro.py

The numbers in every diagram come from the files in src/numpy, so the diagrams
match what those files print. This script is not called numpy.py, because a
file called numpy.py in this folder would be imported instead of NumPy itself
by every script here.
"""

from collections.abc import Callable
import math
import pathlib
import sys

# The files in src/numpy (arrays, indexing, linear_algebra, maths and sampling) are
# imported from there, so this adds that folder to where Python looks.
REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'src' / 'numpy'))

import arrays  # noqa: E402
import indexing  # noqa: E402
import linear_algebra  # noqa: E402
import maths  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
import sampling  # noqa: E402

IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'numpy' / 'numpy-intro'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
GREY: str = '#9a9a9a'
PALE_GREEN: str = '#dff2e2'
PALE_BLUE: str = '#e3ecf7'
PALE_ORANGE: str = '#fdebd3'
PALE_GREY: str = '#eeeeee'

# A cell's colour, chosen from its row and column.
Colour = Callable[[int, int], str]


def _save(fig: Figure, name: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {IMAGES / name}')


def _canvas(width: float, height: float, x_range: tuple[float, float],
            y_range: tuple[float, float]) -> tuple[Figure, Axes]:
    """Make a blank drawing area, with y growing downwards like rows of a table."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(width, height), facecolor='white')
    ax.set_xlim(*x_range)
    ax.set_ylim(y_range[1], y_range[0])
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def _table(ax: Axes, values: NDArray[np.generic], left: float, top: float,
           text: Callable[[object], str] = lambda value: f'{value:g}',
           colour: Colour = lambda row, col: 'white',
           width: float = 1.1, height: float = 0.6, alpha: float = 1.0) -> None:
    """Draw an array as a table of cells, one number in each."""
    grid: NDArray[np.generic] = values.reshape(1, -1) if values.ndim == 1 else values
    for row in range(grid.shape[0]):
        for col in range(grid.shape[1]):
            ax.add_patch(Rectangle((left + col * width, top + row * height), width, height,
                                   facecolor=colour(row, col), edgecolor=GREY, lw=0.8,
                                   alpha=alpha))
            ax.text(left + (col + 0.5) * width, top + (row + 0.5) * height,
                    text(grid[row, col]), ha='center', va='center', fontsize=8.5,
                    color=INK, family='monospace', alpha=alpha)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
           colour: str = BLUE) -> None:
    ax.annotate('', xy=end, xytext=start,
                arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.3})


def axes() -> None:
    """Draw three robotics arrays, with one, two and three axes."""
    fig: Figure
    ax: Axes
    fig, ax = _canvas(13, 4.4, (-0.8, 25.5), (-1.2, 6.2))

    # One axis: the joint angles.
    _table(ax, np.radians([0.0, 30.0, 60.0]), 0.0, 1.6,
           text=lambda v: f'{v:.2f}', colour=lambda r, c: PALE_BLUE)
    ax.text(1.65, 0.6, 'joints\nshape (3,)', ha='center', fontsize=10, color=INK)
    _arrow(ax, (0.0, 2.7), (3.3, 2.7))
    ax.text(1.65, 3.3, 'axis 0: 3 joints', ha='center', fontsize=9, color=BLUE)

    # Two axes: points, one per row.
    left: float = 7.2
    _table(ax, arrays.POINTS, left, 1.6, text=lambda v: f'{v:g}',
           colour=lambda r, c: PALE_GREEN)
    for col, name in enumerate('xyz'):
        ax.text(left + (col + 0.5) * 1.1, 1.35, name, ha='center', fontsize=9, color=MUTED)
    ax.text(left + 1.65, -0.2, 'POINTS\nshape (4, 3)', ha='center', fontsize=10, color=INK)
    _arrow(ax, (left - 0.4, 1.6), (left - 0.4, 4.0))
    ax.text(left - 0.6, 2.8, 'axis 0:\n4 points\n(rows)', ha='right', va='center',
            fontsize=9, color=BLUE)
    _arrow(ax, (left, 4.4), (left + 3.3, 4.4), colour=ORANGE)
    ax.text(left + 1.65, 5.0, 'axis 1: x, y, z (columns)', ha='center', fontsize=9,
            color=ORANGE)

    # Three axes: a picture, drawn as its red, green and blue layers.
    left = 16.8
    for layer, (name, tint) in enumerate(reversed(list(zip(('red', 'green', 'blue'),
                                                           ('#f6d5d9', '#d6efd9', '#d7e4f4'))))):
        shift: float = (2 - layer) * 0.45
        for row in range(4):
            for col in range(6):
                ax.add_patch(Rectangle((left + shift + col * 0.8, 1.6 - shift + row * 0.6),
                                       0.8, 0.6, facecolor=tint, edgecolor=GREY, lw=0.6))
    ax.text(left + 3.3, -0.2, 'picture\nshape (240, 320, 3)', ha='center', fontsize=10,
            color=INK)
    _arrow(ax, (left - 0.4, 1.6), (left - 0.4, 4.0))
    ax.text(left - 0.6, 2.8, 'axis 0:\n240 rows', ha='right', va='center', fontsize=9,
            color=BLUE)
    _arrow(ax, (left, 4.4), (left + 4.8, 4.4), colour=ORANGE)
    ax.text(left + 2.4, 5.0, 'axis 1: 320 columns', ha='center', fontsize=9, color=ORANGE)
    _arrow(ax, (left + 5.0, 1.6), (left + 5.9, 0.7), colour=GREEN)
    ax.text(left + 6.1, 1.2, 'axis 2:\nred, green,\nblue', ha='left', va='center', fontsize=9,
            color=GREEN)
    ax.text(left + 2.4, 5.7, '(drawn with 4 rows and 6 columns)', ha='center', fontsize=8,
            color=MUTED)
    _save(fig, 'axes.svg')


def views() -> None:
    """Draw a slice as a window onto the same numbers."""
    picture: NDArray[np.uint8] = np.zeros((4, 6), dtype=np.uint8)
    corner: NDArray[np.uint8] = picture[0:2, 0:3]
    corner[:, :] = 255
    fig: Figure
    ax: Axes
    fig, ax = _canvas(8, 3.8, (-4.5, 8.0), (-1.3, 4.2))
    _table(ax, picture, 0.0, 0.4, width=1.0, height=0.6,
           colour=lambda r, c: PALE_ORANGE if r < 2 and c < 3 else 'white')
    ax.add_patch(Rectangle((0.0, 0.4), 3.0, 1.2, fill=False, edgecolor=ORANGE, lw=2.2))
    ax.text(3.0, -0.4, 'picture, shape (4, 6)', ha='center', fontsize=10, color=INK)
    ax.text(-0.3, 1.0, 'corner =\npicture[0:2, 0:3]', ha='right', va='center', fontsize=9.5,
            color=ORANGE, family='monospace')
    ax.text(3.0, 3.7, 'corner[:, :] = 255 wrote into the picture itself: a slice is a view,\n'
            'another window onto the same numbers, not a copy of them',
            ha='center', fontsize=9, color=MUTED)
    _save(fig, 'views.svg')


def mask() -> None:
    """Draw a comparison making a mask, and the mask picking rows."""
    points: NDArray[np.float64] = indexing.POINTS
    standing: NDArray[np.bool_] = points[:, 2] > 0.01
    fig: Figure
    ax: Axes
    fig, ax = _canvas(13, 4.6, (-0.5, 21.5), (-1.3, 4.6))
    top: float = 0.4

    _table(ax, points[:, 2][:, np.newaxis], 0.0, top, text=lambda v: f'{v:.3f}')
    ax.text(0.55, top - 0.5, 'POINTS[:, 2]', ha='center', fontsize=9.5, color=INK,
            family='monospace')

    _arrow(ax, (1.3, top + 1.8), (2.7, top + 1.8))
    ax.text(2.0, top + 1.5, '> 0.01', ha='center', fontsize=9.5, color=BLUE, family='monospace')

    _table(ax, standing[:, np.newaxis], 2.9, top, text=str,
           colour=lambda r, c: PALE_GREEN if standing[r] else PALE_GREY)
    ax.text(3.45, top - 0.5, 'standing', ha='center', fontsize=9.5, color=INK,
            family='monospace')

    _table(ax, points, 5.8, top, text=lambda v: f'{v:g}',
           colour=lambda r, c: PALE_GREEN if standing[r] else PALE_GREY)
    ax.text(7.45, top - 0.5, 'POINTS', ha='center', fontsize=9.5, color=INK,
            family='monospace')
    for row in np.nonzero(~standing)[0]:
        ax.plot([5.8, 9.1], [top + (row + 0.5) * 0.6] * 2, color=GREY, lw=1)

    _arrow(ax, (9.5, top + 1.8), (11.3, top + 1.8), colour=GREEN)
    _table(ax, points[standing], 11.6, top + 0.6, text=lambda v: f'{v:g}',
           colour=lambda r, c: PALE_GREEN)
    ax.text(13.25, top + 0.1, 'POINTS[standing]', ha='center', fontsize=9.5, color=INK,
            family='monospace')
    ax.text(18.2, top + 1.8, 'the rows where\nthe mask is True:\nthe 4 points on the box',
            ha='center', va='center', fontsize=9, color=GREEN)
    _save(fig, 'mask.svg')


def broadcasting() -> None:
    """Draw a small array stretched to match a bigger one."""
    points: NDArray[np.float64] = maths.POINTS
    shift: NDArray[np.float64] = np.array([0.0, 0.0, 0.40])
    fig: Figure
    ax: Axes
    fig, ax = _canvas(13, 6.6, (-0.5, 21.5), (-1.0, 9.8))

    def sign(x: float, y: float, text: str) -> None:
        ax.text(x, y, text, ha='center', va='center', fontsize=14, color=INK)

    # A (4, 3) array plus a (3,) array.
    _table(ax, points, 0.0, 0.4, text=lambda v: f'{v:g}')
    ax.text(1.65, -0.3, 'POINTS  (6, 3)', ha='center', fontsize=9.5, color=INK)
    sign(4.0, 2.2, '+')
    _table(ax, shift, 4.7, 0.4, text=lambda v: f'{v:g}', colour=lambda r, c: PALE_ORANGE)
    for row in range(1, 6):
        _table(ax, shift, 4.7, 0.4 + row * 0.6, text=lambda v: f'{v:g}',
               colour=lambda r, c: PALE_ORANGE, alpha=0.35)
    ax.text(6.35, -0.3, 'shift  (3,)', ha='center', fontsize=9.5, color=ORANGE)
    sign(8.7, 2.2, '=')
    _table(ax, points + shift, 9.4, 0.4, text=lambda v: f'{v:g}')
    ax.text(11.05, -0.3, '(6, 3)', ha='center', fontsize=9.5, color=INK)
    ax.text(17.2, 2.2, 'the one row of shift is used\nfor every row of POINTS\n'
            '(the faded rows are not\nstored: NumPy reuses the row)',
            ha='center', va='center', fontsize=9, color=MUTED)

    # A (4, 1) column plus a (1, 3) row.
    top: float = 6.4
    rows: NDArray[np.float64] = np.arange(4.0)[:, np.newaxis] * 10
    cols: NDArray[np.float64] = np.arange(3.0)[np.newaxis, :]
    for col in range(3):
        _table(ax, rows, col * 1.1, top, colour=lambda r, c: PALE_BLUE,
               alpha=1.0 if col == 0 else 0.35)
    ax.text(1.65, top - 0.7, 'rows * 10  (4, 1)', ha='center', fontsize=9.5, color=BLUE)
    sign(4.0, top + 1.2, '+')
    for row in range(4):
        _table(ax, cols, 4.7, top + row * 0.6, colour=lambda r, c: PALE_GREEN,
               alpha=1.0 if row == 0 else 0.35)
    ax.text(6.35, top - 0.7, 'cols  (1, 3)', ha='center', fontsize=9.5, color=GREEN)
    sign(8.7, top + 1.2, '=')
    _table(ax, rows + cols, 9.4, top)
    ax.text(11.05, top - 0.7, '(4, 3)', ha='center', fontsize=9.5, color=INK)
    ax.text(17.2, top + 1.2, 'a column and a row both stretch,\nand every row value meets\n'
            'every column value', ha='center', va='center', fontsize=9, color=MUTED)
    _save(fig, 'broadcasting.svg')


def reductions() -> None:
    """Draw mean along axis 0 and norm along axis 1."""
    box: NDArray[np.float64] = indexing.POINTS[indexing.POINTS[:, 2] > 0.01]
    camera: NDArray[np.float64] = np.array([0.0, 0.0, 0.40])
    fig: Figure
    ax: Axes
    fig, ax = _canvas(11, 4.8, (-5.0, 13.5), (-1.0, 6.0))
    _table(ax, box, 0.0, 0.4, text=lambda v: f'{v:g}')
    for col, name in enumerate('xyz'):
        ax.text((col + 0.5) * 1.1, 0.15, name, ha='center', fontsize=9, color=MUTED)
    ax.text(1.65, -0.5, 'box  (4, 3)', ha='center', fontsize=10, color=INK)

    _arrow(ax, (1.65, 2.9), (1.65, 3.8), colour=ORANGE)
    _table(ax, box.mean(axis=0), 0.0, 4.0, text=lambda v: f'{v:.4f}',
           colour=lambda r, c: PALE_ORANGE)
    ax.text(-0.4, 4.3, 'box.mean(axis=0)', ha='right', va='center', fontsize=9.5,
            color=ORANGE, family='monospace')
    ax.text(1.65, 5.2, 'down the rows: one answer per column,\nthe middle of the points',
            ha='center', va='center', fontsize=9, color=ORANGE)

    _arrow(ax, (3.5, 1.6), (4.6, 1.6), colour=BLUE)
    _table(ax, np.linalg.norm(box - camera, axis=1)[:, np.newaxis], 4.8, 0.4,
           text=lambda v: f'{v:.4f}', colour=lambda r, c: PALE_BLUE, width=1.3)
    ax.text(6.4, 1.6, 'np.linalg.norm(box - camera, axis=1)\nalong each row: one answer\n'
            'per point, its distance\nfrom the camera', ha='left', va='center', fontsize=9,
            color=BLUE)
    _save(fig, 'reductions.svg')


def transform() -> None:
    """Draw a 4 x 4 transform's parts, and the arm it describes."""
    q1: float = math.radians(30)
    q2: float = math.radians(60)
    rz: Callable[[float], NDArray[np.float64]] = linear_algebra.rotation_z
    make: Callable[[NDArray[np.float64], NDArray[np.float64]], NDArray[np.float64]] = \
        linear_algebra.transform
    base_to_link1: NDArray[np.float64] = make(rz(q1), np.zeros(3))
    base_to_link2: NDArray[np.float64] = base_to_link1 @ make(
        rz(q2), np.array([linear_algebra.LINK1, 0.0, 0.0]))
    base_to_gripper: NDArray[np.float64] = base_to_link2 @ make(
        np.eye(3), np.array([linear_algebra.LINK2, 0.0, 0.0]))

    fig: Figure
    left: Axes
    right: Axes
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor='white',
                                      gridspec_kw={'width_ratios': (1.25, 1)})
    left.set_xlim(-3.2, 7.2)
    left.set_ylim(4.6, -1.2)
    left.set_aspect('equal')
    left.axis('off')

    def part(row: int, col: int) -> str:
        if row == 3:
            return PALE_GREY
        return PALE_BLUE if col < 3 else PALE_ORANGE

    _table(left, base_to_gripper + 0.0, 0.0, 0.2, text=lambda v: f'{v:.3f}', colour=part,
           width=1.25, height=0.8)
    left.text(2.5, -0.5, 'base_to_gripper, shape (4, 4)', ha='center', fontsize=10, color=INK)
    left.text(-0.3, 1.4, 'R: the turn\n[:3, :3]', ha='right', va='center', fontsize=9.5,
              color=BLUE)
    left.text(5.3, 1.4, 't: the shift\n[:3, 3]\nwhere the\ngripper is', ha='left',
              va='center', fontsize=9.5, color=ORANGE)
    left.text(-0.3, 2.8, 'always\n0 0 0 1', ha='right', va='center', fontsize=9.5, color=MUTED)
    left.text(2.5, 4.1, 'base_to_link1 @ link1_to_link2 @ link2_to_gripper', ha='center',
              fontsize=9, color=INK, family='monospace')

    # The arm itself, drawn from the same transforms.
    joints: NDArray[np.float64] = np.array([
        base_to_link1[:2, 3], base_to_link2[:2, 3], base_to_gripper[:2, 3]])
    right.plot(joints[:, 0], joints[:, 1], color=GREY, lw=6, solid_capstyle='round', zorder=1)
    right.scatter(joints[:2, 0], joints[:2, 1], s=70, color=INK, zorder=2)
    for frame, name in ((np.eye(4), 'base'), (base_to_gripper, 'gripper')):
        origin: NDArray[np.float64] = frame[:2, 3]
        for axis_col, colour in ((0, RED), (1, GREEN)):
            tip: NDArray[np.float64] = origin + 0.8 * frame[:2, axis_col]
            right.annotate('', xy=tuple(tip), xytext=tuple(origin),
                           arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.6})
        right.text(origin[0] + 0.25, origin[1] - 0.35, name, fontsize=9.5, color=INK)
    gx: float = float(base_to_gripper[0, 3])
    gy: float = float(base_to_gripper[1, 3])
    right.text(gx + 0.25, gy + 0.2, f'({gx:.3f}, {gy:.1f})', fontsize=9.5, color=ORANGE)
    right.text(1.2, 0.3, '30°', fontsize=9, color=MUTED)
    right.text(2.75, 1.95, '60°', fontsize=9, color=MUTED)
    right.set_xlim(-0.8, 5.0)
    right.set_ylim(-0.8, 4.6)
    right.set_aspect('equal')
    right.grid(color=PALE_GREY)
    right.set_axisbelow(True)                      # keep the grid behind the arm
    right.tick_params(labelsize=8, colors=MUTED)
    right.set_title('the arm at 30 and 60 degrees: red x, green y', fontsize=9.5, color=INK)
    _save(fig, 'transform.svg')


def grid() -> None:
    """Draw the row and column of every pixel, as np.mgrid gives them."""
    v: NDArray[np.float64]
    u: NDArray[np.float64]
    v, u = np.mgrid[0:3, 0:4] + 0.5
    fig: Figure
    ax: Axes
    fig, ax = _canvas(10, 3.2, (-0.5, 12.5), (-1.3, 3.3))
    _table(ax, v, 0.0, 0.2, colour=lambda r, c: PALE_GREEN, width=1.2, height=0.8)
    ax.text(2.4, -0.5, 'v: the row of every pixel', ha='center', fontsize=10, color=GREEN)
    _table(ax, u, 7.0, 0.2, colour=lambda r, c: PALE_BLUE, width=1.2, height=0.8)
    ax.text(9.4, -0.5, 'u: the column of every pixel', ha='center', fontsize=10, color=BLUE)
    ax.text(6.0, 3.0, 'v, u = np.mgrid[0:3, 0:4] + 0.5    (the middle of each pixel of a '
            '3 x 4 picture)', ha='center', fontsize=9, color=INK, family='monospace')
    _save(fig, 'grid.svg')


def interp() -> None:
    """Plot waypoints and the in-between angles np.interp fills in."""
    times: NDArray[np.float64] = np.arange(0.0, 3.01, 0.1)
    angles: NDArray[np.float64] = np.interp(times, sampling.WAYPOINT_TIMES,
                                            sampling.WAYPOINT_ANGLES)
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(7.5, 3.6), facecolor='white')
    ax.plot(times, angles, 'o', color=BLUE, markersize=3.5, label='np.interp, every 0.1 s')
    ax.plot(sampling.WAYPOINT_TIMES, sampling.WAYPOINT_ANGLES, 'o', color=RED, markersize=9,
            label='the waypoints', zorder=3)
    ax.set_xlabel('time (s)', fontsize=9.5, color=INK)
    ax.set_ylabel('joint angle (degrees)', fontsize=9.5, color=INK)
    ax.grid(color=PALE_GREY)
    ax.legend(fontsize=9, frameon=False)
    ax.tick_params(labelsize=8.5, colors=MUTED)
    ax.set_title('np.interp(times, WAYPOINT_TIMES, WAYPOINT_ANGLES)', fontsize=10,
                 color=INK, family='monospace')
    _save(fig, 'interp.svg')


def noise() -> None:
    """Plot a histogram of noisy readings, with the mean and one spread either side."""
    readings: NDArray[np.float64] = sampling.noisy_readings(10_000)
    within: float = float(np.mean(np.abs(readings - sampling.TABLE_DEPTH) < sampling.NOISE))
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(7.5, 3.6), facecolor='white')
    ax.axvspan(sampling.TABLE_DEPTH - sampling.NOISE, sampling.TABLE_DEPTH + sampling.NOISE,
               color=PALE_ORANGE, label=f'within one spread (5 mm): {within:.1%}')
    ax.hist(readings, bins=40, range=(0.38, 0.42), color=BLUE, alpha=0.8)
    ax.axvline(float(readings.mean()), color=RED, lw=1.5,
               label=f'mean {readings.mean():.4f} m')
    ax.set_xlabel('reading (m)', fontsize=9.5, color=INK)
    ax.set_ylabel('how many readings', fontsize=9.5, color=INK)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.tick_params(labelsize=8.5, colors=MUTED)
    ax.set_title('rng.normal(0.40, 0.005, 10_000): a table 0.40 m away, measured 10,000 times',
                 fontsize=10, color=INK)
    _save(fig, 'noise.svg')


if __name__ == '__main__':
    axes()
    views()
    mask()
    broadcasting()
    reductions()
    transform()
    grid()
    interp()
    noise()
