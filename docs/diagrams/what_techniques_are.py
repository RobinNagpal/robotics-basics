"""Generate the diagrams for docs/06_programming-techniques/01_what-techniques-are/.

This covers 01_programmed-not-learned, 02_the-building-blocks,
03_choosing-a-technique and 04_the-map-of-techniques. Each document's pictures go
to a folder named after it, under docs/images/what-techniques-are/.

Run with:  pixi run python ../docs/diagrams/what_techniques_are.py
Add --png <dir> to also write PNG copies for checking.

Every number drawn on a picture is computed here, and the script prints the
numbers the documents quote, so the text and the pictures agree.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'what-techniques-are'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
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
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'

# One colour per category of technique, used on the map pictures.
CATEGORIES: list[tuple[str, str]] = [
    ('Geometry and cameras', '#3b82c4'),
    ('Searching and matching', '#2a9d3f'),
    ('Fitting and estimation', '#8e5bb5'),
    ('Image and point cloud processing', '#e07b39'),
    ('Planning and search', '#d1495b'),
    ('Control and motion', '#f0a500'),
    ('Decisions and task logic', '#555555'),
]


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, style: str = '-|>') -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': style, 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=8)


def _plot_style(ax: Axes) -> None:
    """A light style for ordinary x-y plots."""
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9.5)
    ax.grid(True, color='#eeeeee', lw=0.8, zorder=0)


def _top_mug(ax: Axes, p: tuple[float, float], r: float, color: str, z: int = 4) -> None:
    """A mug seen from above: a ring with a handle."""
    ax.add_patch(Rectangle((p[0] + r * 0.8, p[1] - r * 0.25), r * 0.7, r * 0.5,
                           facecolor=color, edgecolor=INK, lw=0.8, zorder=z - 1))
    ax.add_patch(Circle(p, r, facecolor=color, edgecolor=INK, lw=0.8, zorder=z))
    ax.add_patch(Circle(p, r * 0.7, facecolor='white', edgecolor=INK, lw=0.6, zorder=z))


def _side_mug(ax: Axes, x: float, y: float, w: float, h: float, color: str) -> None:
    """A mug seen from the side, standing on y, handle on the right."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=INK, lw=0.8, zorder=4))
    ax.add_patch(Rectangle((x + w, y + h * 0.3), w * 0.28, h * 0.4, facecolor='none',
                           edgecolor=color, lw=3, zorder=3))


def _frame(ax: Axes, origin: tuple[float, float], angle_deg: float, length: float,
           name: str, name_offset: tuple[float, float]) -> None:
    """A 2D frame: a red x arrow and a green y arrow."""
    a = math.radians(angle_deg)
    ex = (math.cos(a), math.sin(a))
    ey = (-math.sin(a), math.cos(a))
    _arrow(ax, origin, (origin[0] + length * ex[0], origin[1] + length * ex[1]),
           color=AXIS_X, lw=2.2)
    _arrow(ax, origin, (origin[0] + length * ey[0], origin[1] + length * ey[1]),
           color=AXIS_Y, lw=2.2)
    _label(ax, origin[0] + (length + 16) * ex[0], origin[1] + (length + 16) * ex[1],
           'x', size=10, color=AXIS_X, weight='bold')
    _label(ax, origin[0] + (length + 16) * ey[0], origin[1] + (length + 16) * ey[1],
           'y', size=10, color=AXIS_Y, weight='bold')
    _label(ax, origin[0] + name_offset[0], origin[1] + name_offset[1], name, size=10,
           weight='bold')


# --------------------------------------------------------------------------
# 01_programmed-not-learned
# --------------------------------------------------------------------------

PROG_DOC: str = 'programmed-not-learned'

GRIPPER_TIP: tuple[float, float] = (250.0, 100.0)
MUGS: dict[str, tuple[float, float]] = {
    'A': (470.0, 210.0),
    'B': (180.0, 380.0),
    'C': (520.0, -60.0),
    'D': (330.0, 180.0),
}


def mug_distances() -> dict[str, float]:
    """Straight-line distance from the gripper tip to each mug, in millimetres."""
    gx, gy = GRIPPER_TIP
    return {k: math.hypot(x - gx, y - gy) for k, (x, y) in MUGS.items()}


def closest_mug() -> None:
    """Top view: the gripper tip, four mugs, and the distance to each."""
    d = mug_distances()
    best = min(d, key=d.get)
    fig, ax = plt.subplots(figsize=(8.6, 7.0), facecolor='white')
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(80, 640)
    ax.set_ylim(-140, 470)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9.5)
    ax.grid(True, color='#eeeeee', lw=0.8, zorder=0)
    ax.set_xlabel('x on the table (mm)', fontsize=10, color=INK)
    ax.set_ylabel('y on the table (mm)', fontsize=10, color=INK)
    ax.set_title('Which mug is closest to the gripper?  Work out every distance, keep the '
                 'smallest', fontsize=11.5, color=INK, weight='bold', pad=12)

    gx, gy = GRIPPER_TIP
    offsets = {'A': (0, -16), 'B': (-40, 0), 'C': (10, -20), 'D': (-30, 12)}
    for k, (x, y) in MUGS.items():
        win = k == best
        ax.plot([gx, x], [gy, y], color=GRIP if win else MUTED, lw=2.4 if win else 1.3,
                ls='-' if win else '--', zorder=2)
        f = 0.5 if win else 0.62
        mx, my = gx + f * (x - gx) + offsets[k][0], gy + f * (y - gy) + offsets[k][1]
        ax.text(mx, my, f'{d[k]:.1f} mm', fontsize=10, ha='center', va='center',
                color=GRIP if win else INK, weight='bold' if win else 'normal', zorder=9,
                bbox={'boxstyle': 'round,pad=0.2', 'facecolor': 'white',
                      'edgecolor': 'none'})
        _top_mug(ax, (x, y), 24, LINK if not win else GRIP)
        ax.text(x, y + 40, f'mug {k}\n({x:.0f}, {y:.0f})', fontsize=9.5, ha='center',
                va='bottom', color=INK, zorder=9)
    ax.add_patch(Circle(GRIPPER_TIP, 14, facecolor=JOINT, edgecolor=INK, lw=1, zorder=6))
    ax.text(gx, gy - 26, f'gripper tip\n({gx:.0f}, {gy:.0f})', fontsize=9.5, ha='center',
            va='top', color=INK, zorder=9)
    ax.text(630, -125, f'closest: mug {best}, {d[best]:.1f} mm', fontsize=10.5, ha='right',
            va='bottom', color=GRIP, weight='bold')
    _save(fig, PROG_DOC, 'closest-mug.svg')


# One row of 16 depth readings, in millimetres from the camera.
TABLE_DEPTH: float = 600.0
DEPTH_LIMIT: float = 580.0
ROW_MUG: list[float] = [601, 600, 599, 601, 600, 512, 505, 503, 504, 507, 600, 599, 601,
                        600, 600, 601]
ROW_GLASS: list[float] = [601, 600, 599, 601, 600, 0, 0, 0, 0, 0, 600, 599, 601, 600, 600,
                          601]


def depth_rule() -> None:
    """The rule 'closer than 580 mm is an object' on a mug row and on a glass row."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white', sharey=True)
    cases = [(axes[0], ROW_MUG, 'A mug: the rule finds 5 object pixels'),
             (axes[1], ROW_GLASS, 'A glass: the camera returns no reading (0),\n'
                                  'so the rule finds 0 object pixels')]
    for ax, row, title in cases:
        _plot_style(ax)
        xs = np.arange(len(row))
        hits = [0 < v < DEPTH_LIMIT for v in row]
        colours = [GRIP if h else (MUTED if v == 0 else LINK_PALE) for v, h in zip(row, hits)]
        ax.bar(xs, row, color=colours, edgecolor=INK, lw=0.5, zorder=3, width=0.8)
        ax.axhline(DEPTH_LIMIT, color=INK, lw=1.4, ls='--', zorder=4)
        ax.text(15.6, 660, 'limit: 580 mm (dashed line)', fontsize=9.5, ha='right',
                va='center',
                color=INK, zorder=9, bbox={'boxstyle': 'round,pad=0.15',
                                           'facecolor': 'white', 'edgecolor': 'none'})
        for x, v in zip(xs, row):
            if v == 0:
                ax.text(x, 25, '0', fontsize=9, ha='center', va='bottom', color=INK)
        ax.set_ylim(0, 700)
        ax.set_xlim(-0.7, 15.7)
        ax.set_xticks(xs)
        ax.set_xlabel('pixel number along one row of the depth picture', fontsize=10)
        ax.set_title(title, fontsize=11, color=INK, weight='bold')
        n = sum(hits)
        print(f'depth rule: {n} object pixels in {"mug" if row is ROW_MUG else "glass"} row')
    axes[0].set_ylabel('depth reading (mm from the camera)', fontsize=10)
    _save(fig, PROG_DOC, 'depth-rule.svg')


# --------------------------------------------------------------------------
# 02_the-building-blocks
# --------------------------------------------------------------------------

BLOCKS_DOC: str = 'the-building-blocks'

CAM_ORIGIN: tuple[float, float] = (400.0, 100.0)
CAM_ANGLE: float = 90.0
POINT_IN_CAMERA: tuple[float, float] = (50.0, 120.0)


def camera_to_base_point() -> tuple[float, float]:
    """Rotate the camera-frame point by the camera's angle, then add its origin."""
    a = math.radians(CAM_ANGLE)
    px, py = POINT_IN_CAMERA
    rx = math.cos(a) * px - math.sin(a) * py
    ry = math.sin(a) * px + math.cos(a) * py
    return (round(rx + CAM_ORIGIN[0], 6), round(ry + CAM_ORIGIN[1], 6))


def camera_to_base() -> None:
    """One point, measured in the camera frame and in the base frame."""
    bx, by = camera_to_base_point()
    fig, ax = plt.subplots(figsize=(9.6, 6.4), facecolor='white')
    _axes(ax, (-90, 560), (-80, 260))
    _title(ax, 235, 245, 'One mug, two sets of numbers: (50, 120) from the camera, '
           f'({bx:.0f}, {by:.0f}) from the base')

    _frame(ax, (0, 0), 0, 110, 'base frame', (-10, -40))
    cx, cy = CAM_ORIGIN
    _frame(ax, CAM_ORIGIN, CAM_ANGLE, 80, 'camera frame', (70, -28))

    # measurements in the base frame
    ax.plot([0, bx], [by, by], color=AXIS_X, lw=1, ls=':', zorder=2)
    ax.plot([bx, bx], [0, by], color=AXIS_Y, lw=1, ls=':', zorder=2)
    _label(ax, bx / 2, -22, f'x = {bx:.0f} mm from the base', size=9.5, color=AXIS_X)
    _label(ax, -12, by, f'y = {by:.0f}', size=9.5, color=AXIS_Y, ha='right')

    # measurements in the camera frame: camera x runs along base +y, camera y along base -x
    ax.plot([cx, cx], [cy, cy + POINT_IN_CAMERA[0]], color=AXIS_X, lw=2.6, zorder=3,
            alpha=0.6)
    ax.plot([cx, bx], [cy + POINT_IN_CAMERA[0], by], color=AXIS_Y, lw=2.6, zorder=3,
            alpha=0.6)
    _label(ax, cx + 12, cy + 25 + 12, 'camera x = 50', size=9.5, color=AXIS_X, ha='left')
    _label(ax, (cx + bx) / 2, by + 18, 'camera y = 120', size=9.5, color=AXIS_Y)

    _top_mug(ax, (bx, by), 13, GRIP, z=6)
    ax.add_patch(Rectangle((cx - 16, cy - 12), 32, 24, facecolor=MUTED, edgecolor=INK,
                           lw=0.8, zorder=5))
    _label(ax, bx + 30, by + 34, 'mug', size=10, weight='bold', ha='left')
    _save(fig, BLOCKS_DOC, 'camera-to-base.svg')


DEPTH_GRID: np.ndarray = np.array([
    [600, 600, 601, 600, 599, 600, 600, 601],
    [600, 599, 512, 506, 508, 600, 600, 600],
    [601, 600, 507, 503, 505, 600, 599, 600],
    [600, 600, 509, 504, 510, 600, 600, 601],
    [599, 600, 600, 601, 600, 600, 600, 600],
    [600, 601, 600, 600, 600, 599, 601, 600],
])

POSES: dict[str, tuple[float, float]] = {
    'home': (0.0, 3.0),
    'above mug': (3.0, 3.6),
    'grasp': (3.0, 1.2),
    'side': (1.4, 0.4),
    'above rack': (6.0, 3.2),
    'on rack': (6.0, 1.4),
}
EDGES: list[tuple[str, str]] = [
    ('home', 'above mug'), ('home', 'side'), ('above mug', 'grasp'), ('side', 'grasp'),
    ('above mug', 'above rack'), ('above rack', 'on rack'), ('grasp', 'on rack'),
]


def grid_and_graph() -> None:
    """Left: a depth picture as a grid of numbers. Right: arm poses as a graph."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.0, 1.1]})
    rows, cols = DEPTH_GRID.shape
    _axes(a1, (-0.6, cols + 0.1), (-0.9, rows + 1.1))
    _title(a1, cols / 2, rows + 0.7, 'A grid: a small depth picture, one number per pixel',
           size=11.5)
    for r in range(rows):
        for c in range(cols):
            v = int(DEPTH_GRID[r, c])
            near = v < DEPTH_LIMIT
            y = rows - 1 - r
            a1.add_patch(Rectangle((c, y), 1, 1, facecolor='#f6c9c9' if near else 'white',
                                   edgecolor=GRID, lw=1, zorder=2))
            _label(a1, c + 0.5, y + 0.5, str(v), size=9.5, color=GRIP if near else INK)
    _label(a1, -0.15, rows - 0.5, 'row 0', size=9, color=MUTED, ha='right')
    _label(a1, 0.5, -0.35, 'column 0', size=9, color=MUTED)
    _label(a1, cols / 2, -0.75, 'The shaded pixels are closer than 580 mm: the top of a mug.',
           size=10)

    _axes(a2, (-1.0, 7.3), (-0.6, 4.9))
    _title(a2, 3.1, 4.55, 'A graph: poses of the gripper, and the moves between them',
           size=11.5)
    for a, b in EDGES:
        pa, pb = POSES[a], POSES[b]
        a2.plot([pa[0], pb[0]], [pa[1], pb[1]], color=LINK, lw=1.8, zorder=2)
        dist = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) * 100
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        a2.text(mx, my, f'{dist:.0f}', fontsize=9, ha='center', va='center', color=LINK,
                zorder=6, bbox={'boxstyle': 'round,pad=0.15', 'facecolor': 'white',
                                'edgecolor': 'none'})
    place = {'home': (0, 0.42), 'above mug': (0, 0.42), 'grasp': (0.75, -0.05),
             'side': (0, -0.42), 'above rack': (0, 0.42), 'on rack': (0, -0.42)}
    for k, p in POSES.items():
        a2.add_patch(Circle(p, 0.2, facecolor=JOINT, edgecolor=INK, lw=0.8, zorder=5))
        _label(a2, p[0] + place[k][0], p[1] + place[k][1], k, size=10)
    _label(a2, 3.1, -0.45, 'Each dot is a node. Each line is an edge, labelled with its '
           'length in mm.', size=10)
    _save(fig, BLOCKS_DOC, 'grid-and-graph.svg')


def noisy_readings() -> np.ndarray:
    rng = np.random.default_rng(7)
    return np.round(412.0 + rng.normal(0.0, 3.0, 20), 1)


def noise_and_cost() -> None:
    """Twenty noisy readings of one distance, and the cost of each possible answer."""
    readings = noisy_readings()
    mean = float(readings.mean())
    cands = np.linspace(400, 424, 241)
    cost = np.array([np.sum((readings - c) ** 2) for c in cands])
    best = float(cands[np.argmin(cost)])
    print(f'noise: readings {readings.tolist()}')
    print(f'noise: min {readings.min()} max {readings.max()} mean {mean:.2f} best-cost '
          f'{best:.1f}')
    for c in (405.0, 410.0, round(mean, 1), 415.0):
        print(f'noise: cost at {c} = {np.sum((readings - c) ** 2):.1f}')

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor='white')
    _plot_style(a1)
    a1.plot(np.arange(1, 21), readings, 'o', color=LINK, ms=6, zorder=3)
    a1.axhline(mean, color=GRIP, lw=1.6, zorder=2, label=f'average {mean:.1f} mm')
    a1.legend(loc='lower left', fontsize=9.5, frameon=False)
    a1.set_xlabel('reading number', fontsize=10)
    a1.set_ylabel('measured distance to the mug (mm)', fontsize=10)
    a1.set_xticks([1, 5, 10, 15, 20])
    a1.set_title('Noise: 20 readings of a mug that did not move', fontsize=11,
                 weight='bold', color=INK)

    _plot_style(a2)
    a2.plot(cands, cost, color=PURPLE, lw=2, zorder=3)
    a2.plot([best], [cost.min()], 'o', color=GRIP, ms=8, zorder=4)
    a2.annotate(f'lowest cost at {best:.1f} mm,\nthe same as the average',
                xy=(best, cost.min()), xytext=(best, cost.max() * 0.78), ha='center', fontsize=9.5,
                color=GRIP, arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    a2.set_xlabel('a possible answer for the distance (mm)', fontsize=10)
    a2.set_ylabel('cost: sum of squared differences', fontsize=10)
    a2.set_title('Cost: how badly each answer disagrees with the readings', fontsize=11,
                 weight='bold', color=INK)
    fig.tight_layout(w_pad=3)
    _save(fig, BLOCKS_DOC, 'noise-and-cost.svg')


# --------------------------------------------------------------------------
# 03_choosing-a-technique
# --------------------------------------------------------------------------

CHOOSE_DOC: str = 'choosing-a-technique'

LOOPS: list[tuple[str, float]] = [
    ('joint position loop, 1000 times a second', 1000.0),
    ('force limit check, 500 times a second', 500.0),
    ('colour camera, 30 pictures a second', 30.0),
    ('depth camera, 15 pictures a second', 15.0),
    ('a plan before each move, once a second', 1.0),
]


def time_budgets() -> None:
    """How much time each loop leaves for the technique that runs inside it."""
    fig, ax = plt.subplots(figsize=(10.8, 4.4), facecolor='white')
    _plot_style(ax)
    ax.grid(False)
    ax.grid(True, axis='x', color='#eeeeee', lw=0.8, zorder=0)
    names = [n for n, _ in LOOPS][::-1]
    ms = [1000.0 / r for _, r in LOOPS][::-1]
    colours = [SLIDE, WRIST, LINK, LINK, JOINT][::-1]
    ax.barh(range(len(ms)), ms, color=colours, edgecolor=INK, lw=0.5, zorder=3, height=0.6)
    ax.set_xscale('log')
    ax.set_xlim(0.3, 6000)
    ax.set_yticks(range(len(ms)))
    ax.set_yticklabels(names, fontsize=10)
    for i, v in enumerate(ms):
        text = f'{v:.1f} ms' if v < 100 else f'{v:.0f} ms'
        ax.text(v * 1.15, i, text, va='center', ha='left', fontsize=10, color=INK)
        print(f'budget: {names[i]} -> {text}')
    ax.set_xlabel('time available for one run of the technique (milliseconds, log scale)',
                  fontsize=10)
    ax.set_title('The time budget: one run must finish before the next reading arrives',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, CHOOSE_DOC, 'time-budgets.svg')


def line_points() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Points along a table edge seen by a depth camera, with some wrong readings."""
    rng = np.random.default_rng(3)
    x = np.linspace(0, 300, 24)
    y = 0.5 * x + 40 + rng.normal(0, 3, x.size)
    bad = np.array([4, 9, 13, 17, 21])
    y[bad] = y[bad] - np.array([70, 90, 60, 85, 75])
    inlier = np.ones(x.size, bool)
    inlier[bad] = False
    return x, y, inlier


def robust_line(x: np.ndarray, y: np.ndarray, tries: int = 200,
                tol: float = 8.0) -> tuple[float, float, np.ndarray]:
    """Try lines through random pairs of points; keep the one most points agree with."""
    rng = np.random.default_rng(0)
    best_n = -1
    best: tuple[float, float] = (0.0, 0.0)
    best_mask = np.zeros(x.size, bool)
    for _ in range(tries):
        i, j = rng.choice(x.size, 2, replace=False)
        if x[i] == x[j]:
            continue
        m = (y[j] - y[i]) / (x[j] - x[i])
        c = y[i] - m * x[i]
        mask = np.abs(y - (m * x + c)) < tol
        if mask.sum() > best_n:
            best_n = int(mask.sum())
            best, best_mask = (m, c), mask
    m, c = np.polyfit(x[best_mask], y[best_mask], 1)   # refit on the agreeing points
    return float(m), float(c), best_mask


def outliers_pull() -> None:
    """A plain average-style fit is pulled by five bad readings; a robust fit is not."""
    x, y, _ = line_points()
    m_ls, c_ls = np.polyfit(x, y, 1)
    m_r, c_r, mask = robust_line(x, y)
    print(f'fit: least squares slope {m_ls:.3f} offset {c_ls:.1f}')
    print(f'fit: robust slope {m_r:.3f} offset {c_r:.1f}, points agreeing {mask.sum()} '
          f'of {x.size}')
    print(f'fit: true slope 0.500 offset 40.0')
    print(f'fit: at x=300 truth {0.5*300+40:.1f}, least squares {m_ls*300+c_ls:.1f}, '
          f'robust {m_r*300+c_r:.1f}')
    fig, ax = plt.subplots(figsize=(9.6, 5.6), facecolor='white')
    _plot_style(ax)
    ax.plot(x[mask], y[mask], 'o', color=LINK, ms=6, zorder=3, label='good readings')
    ax.plot(x[~mask], y[~mask], 'x', color=GRIP, ms=9, mew=2, zorder=3,
            label='wrong readings')
    xs = np.array([0, 300])
    ax.plot(xs, m_ls * xs + c_ls, color=MUTED, lw=2, ls='--', zorder=2,
            label=f'fit to every point (slope {m_ls:.2f})')
    ax.plot(xs, m_r * xs + c_r, color=SLIDE, lw=2.4, zorder=2,
            label=f'robust fit that ignores the wrong readings (slope {m_r:.2f})')
    ax.set_xlabel('position along the table edge (mm)', fontsize=10)
    ax.set_ylabel('height seen by the camera (mm)', fontsize=10)
    ax.set_ylim(-60, 230)
    ax.legend(loc='upper left', fontsize=9.5, frameon=False)
    ax.set_title('Robustness: five wrong readings drag one fit and not the other',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, CHOOSE_DOC, 'outliers-pull-the-line.svg')


JOBS: list[tuple[float, float, str]] = [
    (0.5, 1.0, 'go to a pose\ntaught by hand'),
    (1.5, -1.0, 'find the flat\ntable top'),
    (2.6, 1.0, 'find a red block\non a white table'),
    (4.0, -1.0, 'find mugs of one\nknown kind'),
    (5.1, 1.0, 'hang a mug\non a rack peg'),
    (6.9, -1.0, 'find any mug in\na messy kitchen'),
    (8.0, 1.0, 'grasp objects\nnever seen before'),
    (9.3, -1.0, 'fold a\ntowel'),
]


def rule_or_model() -> None:
    """Jobs placed along one line: how much the objects and the scene vary."""
    fig, ax = plt.subplots(figsize=(12.4, 4.4), facecolor='white')
    _axes(ax, (-0.4, 10.2), (-2.6, 2.6))
    ax.set_aspect('auto')
    ax.add_patch(Rectangle((0, -0.25), 3.3, 0.5, facecolor=LINK, alpha=0.85, zorder=2))
    ax.add_patch(Rectangle((3.3, -0.25), 2.9, 0.5, facecolor=PURPLE, alpha=0.55, zorder=2))
    ax.add_patch(Rectangle((6.2, -0.25), 3.8, 0.5, facecolor=GRIP, alpha=0.8, zorder=2))
    _label(ax, 1.65, 0, 'a written technique is enough', size=9.5, color='white',
           weight='bold')
    _label(ax, 4.75, 0, 'mix the two', size=9.5, color='white', weight='bold')
    _label(ax, 8.1, 0, 'a learned model usually wins', size=9.5, color='white',
           weight='bold')
    for x, side, text in JOBS:
        y_end = 0.3 * side
        ax.plot([x, x], [y_end, 0.85 * side], color=MUTED, lw=1, zorder=1)
        _label(ax, x, 1.25 * side, text, size=9.5)
    _arrow(ax, (0, -2.25), (10.0, -2.25), color=INK, lw=1.4)
    _label(ax, 0, -2.5, 'the same objects, the same place,\nthe same light every time',
           size=9, ha='left', color=MUTED, va='top')
    _label(ax, 10.0, -2.5, 'new objects, clutter, changing light,\nsoft or see-through things',
           size=9, ha='right', color=MUTED, va='top')
    _label(ax, 5.0, 2.45, 'The more the scene varies, the harder it is to write the rule '
           'down', size=11.5, weight='bold')
    _save(fig, CHOOSE_DOC, 'rule-or-model.svg')


# --------------------------------------------------------------------------
# 04_the-map-of-techniques
# --------------------------------------------------------------------------

MAP_DOC: str = 'the-map-of-techniques'


def _link(ax: Axes, a: tuple[float, float], b: tuple[float, float], w: float = 9) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=LINK, lw=w, solid_capstyle='round', zorder=3)


def _hinge(ax: Axes, p: tuple[float, float], size: float = 11) -> None:
    ax.plot([p[0]], [p[1]], 'o', color=JOINT, ms=size, zorder=4)
    ax.plot([p[0]], [p[1]], 'o', color=INK, ms=size * 0.25, zorder=5)


def _marker(ax: Axes, p: tuple[float, float], n: int) -> None:
    colour = CATEGORIES[n - 1][1]
    ax.add_patch(Circle(p, 0.24, facecolor=colour, edgecolor='white', lw=1.5, zorder=10))
    ax.text(p[0], p[1], str(n), fontsize=11, ha='center', va='center', color='white',
            weight='bold', zorder=11)


def one_task() -> None:
    """The mug-to-rack task with each category of technique marked where it works."""
    fig, ax = plt.subplots(figsize=(14.0, 6.6), facecolor='white')
    _axes(ax, (-0.8, 17.6), (-1.4, 7.0))
    _title(ax, 8.4, 6.75, 'Find the mugs with the wrist camera and hang each one on the rack',
           size=12.5)

    # table
    ax.add_patch(Rectangle((-0.5, -0.35), 10.8, 0.35, facecolor=TABLE, edgecolor=INK,
                           lw=0.8, zorder=2))
    # arm
    base = (0.6, 0.0)
    ax.add_patch(Rectangle((base[0] - 0.45, 0), 0.9, 0.35, facecolor=MUTED, edgecolor=INK,
                           lw=0.8, zorder=3))
    j1 = (0.6, 0.35)
    j2 = (1.6, 3.6)
    j3 = (4.1, 4.6)
    wrist = (4.5, 3.6)
    _link(ax, j1, j2)
    _link(ax, j2, j3)
    _link(ax, j3, wrist, w=7)
    for p in (j1, j2, j3):
        _hinge(ax, p)
    # gripper pointing down
    for dx in (-0.22, 0.22):
        ax.plot([wrist[0], wrist[0] + dx, wrist[0] + dx], [wrist[1], wrist[1] - 0.1,
                wrist[1] - 0.5], color=GRIP, lw=3, zorder=5, solid_capstyle='round')
    # wrist camera and its view
    cam = (4.95, 3.85)
    ax.add_patch(Rectangle((cam[0] - 0.18, cam[1] - 0.14), 0.36, 0.28, facecolor=INK,
                           zorder=6))
    ax.add_patch(Polygon([cam, (3.6, 0.02), (8.2, 0.02)], closed=True, facecolor=LINK_PALE,
                         edgecolor='none', alpha=0.45, zorder=1))
    _label(ax, 6.3, 4.9, 'wrist camera', size=9.5, ha='left')
    ax.plot([6.25, cam[0] + 0.2], [4.85, cam[1] + 0.1], color=MUTED, lw=0.8, zorder=5)
    # mugs
    for x, c in ((4.4, '#5b8fd1'), (5.7, '#d9534f'), (6.95, '#5cb85c')):
        _side_mug(ax, x, 0.0, 0.62, 0.8, c)
    # rack
    ax.add_patch(Rectangle((9.2, 0.0), 0.18, 3.2, facecolor='#9b7b55', edgecolor=INK,
                           lw=0.8, zorder=3))
    for i, h in enumerate((1.2, 2.0, 2.8)):
        ax.plot([9.38, 9.95], [h, h + 0.25], color='#9b7b55', lw=4, zorder=3,
                solid_capstyle='round')
    _label(ax, 9.3, -0.8, 'rack with pegs', size=9.5)
    # planned path to the rack
    t = np.linspace(0, 1, 50)
    px = wrist[0] + (9.6 - wrist[0]) * t
    py = wrist[1] - 0.5 + 1.6 * np.sin(np.pi * t) * 0.8 - (wrist[1] - 0.5 - 2.4) * t
    ax.plot(px, py, color=CATEGORIES[4][1], lw=2, ls='--', zorder=2)
    _arrow(ax, (float(px[-3]), float(py[-3])), (float(px[-1]), float(py[-1])),
           color=CATEGORIES[4][1], lw=2)
    # task logic box
    ax.add_patch(FancyBboxPatch((-0.5, 5.25), 4.2, 0.9, boxstyle='round,pad=0.05',
                                facecolor='#f4f4f4', edgecolor=MUTED, lw=0.8, zorder=2))
    _label(ax, 1.6, 5.7, 'look  >  pick  >  hang  >  next mug', size=10)

    # markers
    _marker(ax, (5.3, 3.35), 1)          # camera: pixels to 3D
    _marker(ax, (6.1, 1.35), 2)          # which mug is which
    _marker(ax, (2.6, 0.55), 3)          # the table plane
    _marker(ax, (7.95, 1.1), 4)          # cutting out the mugs
    _marker(ax, (7.2, 3.95), 5)          # the path
    _marker(ax, (1.1, 2.0), 6)           # the joints
    _marker(ax, (-0.25, 4.95), 7)        # task logic

    # legend
    notes = [
        'pinhole camera model, rigid transforms, calibration',
        'nearest neighbours, matching mugs between pictures',
        'RANSAC for the table plane, a Kalman filter to smooth',
        'depth threshold, clustering the points into mugs',
        'inverse kinematics, then a path that misses the rack',
        'a smooth trajectory, PID on every joint, force limits',
        'a state machine, and greedy choice of the next mug',
    ]
    y = 6.0
    for i, ((name, colour), note) in enumerate(zip(CATEGORIES, notes)):
        _marker(ax, (11.1, y), i + 1)
        _label(ax, 11.5, y + 0.14, name, size=10, ha='left', weight='bold', color=colour)
        _label(ax, 11.5, y - 0.26, note, size=9, ha='left', color=INK)
        y -= 0.95
    _save(fig, MAP_DOC, 'one-task.svg')


STEPS: list[str] = ['look from\nabove', 'find the\nmugs', 'choose the\nnext mug',
                    'plan the\nreach', 'reach and\ngrasp', 'carry to\nthe rack',
                    'hang it and\nlet go']
# Which steps each category is busy in (0-based step numbers).
BUSY: list[list[tuple[int, int]]] = [
    [(0, 1), (4, 4)],     # geometry and cameras
    [(1, 2)],             # searching and matching
    [(1, 1), (4, 4)],     # fitting and estimation
    [(0, 1)],             # image and point cloud processing
    [(3, 3), (5, 5)],     # planning and search
    [(4, 6)],             # control and motion
    [(0, 6)],             # decisions and task logic
]


def when_each_runs() -> None:
    """A timeline of one mug, showing which category is busy in each step."""
    fig, ax = plt.subplots(figsize=(13.0, 5.4), facecolor='white')
    n = len(STEPS)
    _axes(ax, (-4.4, n + 0.1), (-1.3, len(CATEGORIES) + 0.9))
    ax.set_aspect('auto')
    _title(ax, (n - 4.4) / 2 + 0.6, len(CATEGORIES) + 0.65,
           'One mug from start to finish: which kind of technique is busy in each step',
           size=12)
    for s, name in enumerate(STEPS):
        _label(ax, s + 0.5, -0.6, name, size=9.5)
        ax.plot([s, s], [-0.1, len(CATEGORIES)], color='#eeeeee', lw=1, zorder=0)
    ax.plot([n, n], [-0.1, len(CATEGORIES)], color='#eeeeee', lw=1, zorder=0)
    for i, ((name, colour), spans) in enumerate(zip(CATEGORIES, BUSY)):
        y = len(CATEGORIES) - 1 - i
        _label(ax, -0.15, y + 0.5, name, size=10, ha='right', color=colour, weight='bold')
        for a, b in spans:
            ax.add_patch(FancyBboxPatch((a + 0.08, y + 0.2), b - a + 0.84, 0.6,
                                        boxstyle='round,pad=0.02', facecolor=colour,
                                        edgecolor='none', alpha=0.9, zorder=2))
    _save(fig, MAP_DOC, 'when-each-runs.svg')


def print_numbers() -> None:
    d = mug_distances()
    for k, v in d.items():
        print(f'mug {k}: {v:.1f} mm')
    print(f'camera to base: {camera_to_base_point()}')
    for a, b in EDGES:
        pa, pb = POSES[a], POSES[b]
        print(f'edge {a} - {b}: {math.hypot(pb[0]-pa[0], pb[1]-pa[1])*100:.0f}')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    print_numbers()
    closest_mug()
    depth_rule()
    camera_to_base()
    grid_and_graph()
    noise_and_cost()
    time_budgets()
    outliers_pull()
    rule_or_model()
    one_task()
    when_each_runs()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
