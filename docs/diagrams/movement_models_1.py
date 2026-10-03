"""Generate the diagrams for the first half of the movement-models chapter.

The chapter is docs/07_learned-models/06_movement-models/. This script
draws the pictures for three of its documents:

    01_overview.md
    02_behaviour-cloning.md
    03_action-chunking-transformers.md

Each document's pictures go to a folder named after it, under
docs/images/movement-models/.

Run with:  pixi run python ../docs/diagrams/movement_models_1.py
Add --png <dir> to also write PNG copies for checking by eye.

The paths in these pictures are drawn by hand to show one idea each. They are
not measured from a real robot, and no picture claims a measured number.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'movement-models'
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
MUG: str = '#8a5a44'
PALE_GREEN: str = '#dff0e2'
PALE_RED: str = '#f8dede'
PALE_YELLOW: str = '#fdf1d6'

OVERVIEW_DOC: str = 'overview'
BC_DOC: str = 'behaviour-cloning'
ACT_DOC: str = 'action-chunking-transformers'


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


def _title(ax: Axes, x: float, y: float, text: str, size: float = 13) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _floor(ax: Axes, x0: float, x1: float, y: float = 0.0) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.2, zorder=1)
    for x in np.arange(x0 + 0.1, x1, 0.3):
        ax.plot([x, x - 0.15], [y, y - 0.15], color=GRID, lw=1.0, zorder=1)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, style: str = '-|>', rad: float = 0.0, z: int = 3,
           ms: float = 14) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, color=color, lw=lw,
                                 mutation_scale=ms, connectionstyle=f'arc3,rad={rad}',
                                 zorder=z))


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = 'white',
         edge: str = INK, lw: float = 1.2, z: int = 2) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=z))


def _mug(ax: Axes, x: float, y: float, s: float = 1.0, color: str = MUG) -> None:
    """A side view of a mug standing on y, centred on x."""
    w, h = 0.6 * s, 0.7 * s
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=0.8,
                           zorder=3))
    ax.add_patch(Circle((x + w / 2 + 0.1 * s, y + h / 2), 0.17 * s, facecolor='none',
                        edgecolor=color, lw=3.0 * s, zorder=2))


def _mug_top(ax: Axes, x: float, y: float, r: float = 0.4) -> None:
    """A mug seen from above: a ring and a handle."""
    ax.add_patch(Circle((x, y), r, facecolor=MUG, edgecolor=INK, lw=0.8, zorder=3))
    ax.add_patch(Circle((x, y), r * 0.7, facecolor='#b88a70', edgecolor='none', zorder=4))
    ax.add_patch(Rectangle((x + r * 0.9, y - r * 0.2), r * 0.45, r * 0.4, facecolor=MUG,
                           edgecolor=INK, lw=0.8, zorder=2))


def _gripper(ax: Axes, p: tuple[float, float], angle: float, size: float = 0.35,
             open_: bool = True, color: str = INK, spread: float | None = None) -> None:
    """Two short fingers pointing in the direction of angle (radians)."""
    c, s = math.cos(angle), math.sin(angle)
    nx, ny = -s, c
    if spread is None:
        spread = 0.6 if open_ else 0.25
    ax.plot([p[0] + spread * size * nx, p[0] - spread * size * nx],
            [p[1] + spread * size * ny, p[1] - spread * size * ny], color=color, lw=2.2,
            solid_capstyle='round', zorder=5)
    for side in (1, -1):
        root = (p[0] + side * spread * size * nx, p[1] + side * spread * size * ny)
        tip = (root[0] + size * c, root[1] + size * s)
        ax.plot([root[0], tip[0]], [root[1], tip[1]], color=color, lw=2.2,
                solid_capstyle='round', zorder=5)


def _arm(ax: Axes, base: tuple[float, float], lengths: tuple[float, float],
         angles_deg: tuple[float, float], color: str = LINK, width: float = 7,
         grip_open: bool = True, grip_size: float = 0.3) -> tuple[float, float]:
    """A two-link arm standing on a base block. Returns the gripper point."""
    ax.add_patch(Rectangle((base[0] - 0.3, base[1]), 0.6, 0.35, facecolor=MUTED,
                           edgecolor='none', zorder=2))
    p0 = (base[0], base[1] + 0.35)
    a1 = math.radians(angles_deg[0])
    p1 = (p0[0] + lengths[0] * math.cos(a1), p0[1] + lengths[0] * math.sin(a1))
    a2 = a1 + math.radians(angles_deg[1])
    p2 = (p1[0] + lengths[1] * math.cos(a2), p1[1] + lengths[1] * math.sin(a2))
    for a, b in ((p0, p1), (p1, p2)):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width, solid_capstyle='round',
                zorder=3)
    for p in (p0, p1):
        ax.plot([p[0]], [p[1]], 'o', color=JOINT, ms=width * 1.5, zorder=4)
    _gripper(ax, p2, a2, size=grip_size, open_=grip_open)
    return p2


def _camera(ax: Axes, x: float, y: float, angle_deg: float = -90, s: float = 1.0) -> None:
    """A small camera body with a lens, pointing along angle_deg."""
    ax.add_patch(Rectangle((x - 0.25 * s, y - 0.15 * s), 0.5 * s, 0.3 * s, facecolor=INK,
                           edgecolor='none', zorder=5))
    a = math.radians(angle_deg)
    lx, ly = x + 0.22 * s * math.cos(a), y + 0.22 * s * math.sin(a)
    ax.add_patch(Circle((lx, ly), 0.1 * s, facecolor=MUTED, edgecolor=INK, zorder=6))


def _network(ax: Axes, x0: float, y0: float, w: float, h: float,
             layers: tuple[int, ...] = (3, 4, 4, 3), color: str = LINK) -> None:
    """A little network of circles joined by lines, filling the box (x0, y0, w, h)."""
    xs = np.linspace(x0, x0 + w, len(layers))
    cols: list[list[tuple[float, float]]] = []
    for x, n in zip(xs, layers):
        ys = np.linspace(y0 + h * 0.1, y0 + h * 0.9, n) if n > 1 else [y0 + h / 2]
        cols.append([(float(x), float(y)) for y in ys])
    for a_col, b_col in zip(cols[:-1], cols[1:]):
        for a in a_col:
            for b in b_col:
                ax.plot([a[0], b[0]], [a[1], b[1]], color=GRID, lw=0.8, zorder=2)
    r = min(w / len(layers), h / max(layers)) * 0.18
    for col in cols:
        for p in col:
            ax.add_patch(Circle(p, r, facecolor=color, edgecolor=INK, lw=0.6, zorder=3))


def _obstacle(ax: Axes, x: float, y: float, w: float, h: float) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor='#e8e8e8', edgecolor=MUTED, lw=1.0,
                           hatch='///', zorder=2))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

def policy_loop() -> None:
    """A policy looks, chooses one small move, the arm makes it, and it looks again."""
    fig, ax = plt.subplots(figsize=(13.0, 5.6), facecolor='white')
    _axes(ax, (-0.5, 16.0), (-2.6, 5.0))

    # The scene: arm, mug, camera.
    _floor(ax, 0.0, 4.6)
    _arm(ax, (0.9, 0.0), (1.9, 1.7), (70, -95), grip_size=0.3)
    _mug(ax, 3.7, 0.0, s=0.9)
    _camera(ax, 3.2, 3.9, angle_deg=-100)
    ax.plot([3.2, 2.7], [3.7, 0.3], color=GRID, lw=1.0, ls='--', zorder=1)
    ax.plot([3.2, 4.3], [3.7, 0.3], color=GRID, lw=1.0, ls='--', zorder=1)
    _label(ax, 2.3, 4.5, 'the arm, the mug and a camera', size=10, color=MUTED)

    # What goes in.
    _box(ax, 5.2, 1.3, 2.5, 2.1, face=PALE_YELLOW, edge=JOINT)
    ax.add_patch(Rectangle((5.45, 2.35), 1.0, 0.8, facecolor='white', edgecolor=INK,
                           lw=0.8, zorder=3))
    _mug(ax, 5.95, 2.45, s=0.5)
    _label(ax, 7.1, 2.75, 'picture', size=9)
    _label(ax, 6.45, 1.85, 'joint angles\n70°, −95°, open', size=9)
    _label(ax, 6.45, 3.75, 'what it sees', size=10, weight='bold')
    _arrow(ax, (4.7, 2.3), (5.1, 2.3))

    # The policy.
    _arrow(ax, (7.8, 2.3), (8.4, 2.3))
    _box(ax, 8.5, 0.9, 2.7, 2.8, face='white', edge=LINK, lw=1.6)
    _network(ax, 8.8, 1.1, 2.1, 2.3, layers=(3, 5, 5, 3))
    _label(ax, 9.85, 4.05, 'the policy', size=11, weight='bold', color=LINK)
    _label(ax, 9.85, 0.55, 'a trained neural network', size=9, color=MUTED)

    # What comes out.
    _arrow(ax, (11.3, 2.3), (11.9, 2.3))
    _box(ax, 12.0, 1.1, 3.6, 2.4, face=PALE_GREEN, edge=SLIDE)
    _label(ax, 13.8, 3.9, 'what to do next', size=10, weight='bold')
    _label(ax, 13.8, 2.3, 'joint 1: +2°\njoint 2: −1°\ngripper: stay open', size=10)

    # And round again.
    _arrow(ax, (13.8, 1.0), (2.4, -0.55), color=SLIDE, lw=2.0, rad=-0.18)
    _label(ax, 8.1, -1.95, 'the arm makes that small move, the world changes, and the '
           'policy looks again,\nmany times a second, until the job is done',
           size=10, color=INK)
    _save(fig, OVERVIEW_DOC, 'policy-loop.svg')


def five_kinds() -> None:
    """One small picture of the idea behind each of the five kinds of movement model."""
    fig, axes = _panels(5, (18.0, 4.6))
    for ax in axes:
        _axes(ax, (-0.3, 4.3), (-1.6, 3.4))

    # 1. Behaviour cloning: copy a recorded path.
    ax = axes[0]
    xs = np.linspace(0.2, 3.3, 30)
    demo = 0.6 + 1.6 * np.sin(xs / 3.3 * math.pi * 0.9)
    ax.plot(xs, demo, color=SLIDE, lw=2.5, ls='--', zorder=2)
    ax.plot(xs, demo + 0.12, color=LINK, lw=2.0, zorder=3)
    _mug_top(ax, 3.6, 0.9, r=0.3)
    _label(ax, 1.2, 2.7, 'person', size=9, color=SLIDE)
    _label(ax, 2.4, 2.75, 'copy', size=9, color=LINK)
    _title(ax, 2.0, 3.2, 'Behaviour cloning', size=12)
    _caption(ax, 2.0, -0.9, 'Copy the moves a person\nmade in recorded examples.')

    # 2. Action chunking: few decisions, each a burst of moves.
    ax = axes[1]
    pts = [(0.3 + 0.35 * i, 0.5 + 0.18 * i) for i in range(10)]
    for k, (x, y) in enumerate(pts[:-1]):
        nx, ny = pts[k + 1]
        _arrow(ax, (x, y), (nx, ny), color=LINK if k < 5 else WRIST, lw=1.4, ms=9)
    for (x, y), c in ((pts[0], LINK), (pts[5], WRIST)):
        ax.plot([x], [y], 'o', ms=12, color=c, mec=INK, zorder=5)
    _label(ax, 0.3, 1.05, 'decide', size=9, color=LINK)
    _label(ax, 2.05, 1.95, 'decide', size=9, color=WRIST)
    _title(ax, 2.0, 3.2, 'Action chunking', size=12)
    _caption(ax, 2.0, -0.9, 'Choose a whole burst of\nmoves at each decision.')

    # 3. Diffusion and flow: turn a noisy guess into a clean path.
    ax = axes[2]
    rng = np.random.default_rng(3)
    xs = np.linspace(0.3, 3.7, 10)
    noise = np.clip(rng.normal(0, 1.0, xs.size), -1.0, 1.0)
    for row, (amount, color) in enumerate(((0.3, MUTED), (0.12, LINK_PALE), (0.0, LINK))):
        y0 = 2.1 - row * 0.95
        ax.plot(xs, y0 + 0.08 * (xs - 2.0) + amount * noise, color=color, lw=1.8,
                marker='o', ms=4, zorder=3)
        if row < 2:
            _arrow(ax, (4.1, y0 - 0.05), (4.1, y0 - 0.6), color=INK, lw=1.2, ms=10)
    _label(ax, 0.1, 2.75, 'random guess', size=9, color=MUTED, ha='left')
    _label(ax, 0.1, -0.3, 'clean path', size=9, color=LINK, ha='left')
    _title(ax, 2.0, 3.2, 'Diffusion and flow', size=12)
    _caption(ax, 2.0, -0.9, 'Clean up a random guess,\nstep by step, into a path.')

    # 4. Reinforcement learning: try, get a score, try again.
    ax = axes[3]
    _mug_top(ax, 3.55, 1.2, r=0.3)
    start = (0.3, 1.2)
    tries = (((1.8, 2.6), (3.0, 2.5), '0', GRIP), ((1.8, -0.2), (3.0, 0.0), '0', GRIP),
             ((1.6, 1.3), (3.1, 1.2), '1', SLIDE))
    for mid, end, score, c in tries:
        path = np.array([start, mid, end])
        ax.plot(path[:, 0], path[:, 1], color=c, lw=1.8, zorder=2)
        dy = -0.35 if score == '1' else 0.3
        _label(ax, end[0] - 0.4, end[1] + dy, f'score {score}', size=9, color=c)
    ax.plot([start[0]], [start[1]], 'o', ms=9, color=INK, zorder=5)
    _title(ax, 2.0, 3.2, 'Reinforcement learning', size=12)
    _caption(ax, 2.0, -0.9, 'Try many times; keep what\nearned a good score.')

    # 5. Learned planner: a route around an obstacle, straight from the dots.
    ax = axes[4]
    rng = np.random.default_rng(7)
    ox, oy = rng.uniform(1.5, 2.5, 60), rng.uniform(0.3, 1.9, 60)
    ax.plot(ox, oy, '.', color=MUTED, ms=4, zorder=2)
    route = np.array([(0.3, 0.9), (1.1, 2.3), (2.0, 2.6), (2.9, 2.3), (3.7, 0.9)])
    ax.plot(route[:, 0], route[:, 1], color=LINK, lw=2.2, zorder=3)
    ax.plot([0.3], [0.9], 'o', ms=8, color=INK, zorder=5)
    ax.plot([3.7], [0.9], '*', ms=13, color=JOINT, mec=INK, zorder=5)
    _label(ax, 2.0, 0.0, 'obstacle, as 3D dots', size=9, color=MUTED)
    _title(ax, 2.0, 3.2, 'Learned motion planner', size=12)
    _caption(ax, 2.0, -0.9, 'Draw a safe route round\nobstacles in one quick step.')
    fig.subplots_adjust(wspace=0.12)
    _save(fig, OVERVIEW_DOC, 'five-kinds.svg')


# --------------------------------------------------------------------------
# 02_behaviour-cloning
# --------------------------------------------------------------------------

def demonstration_pairs() -> None:
    """A recording is a list of moments; each moment pairs what was seen with what was done."""
    fig, ax = plt.subplots(figsize=(14.0, 6.2), facecolor='white')
    _axes(ax, (-2.6, 16.2), (-3.4, 4.8))
    # (left edge, gripper x from the edge, gripper top height, finger spread, lifted,
    #  joint angles, what the person did next)
    frames = ((0.0, 0.8, 3.0, 0.6, False, '60°, −80°', 'move right'),
              (4.0, 1.7, 2.9, 0.6, False, '63°, −82°', 'move down'),
              (8.0, 1.7, 1.92, 0.6, False, '65°, −85°', 'close gripper'),
              (12.0, 1.7, 2.42, 0.52, True, '65°, −85°', 'lift'))
    for k, (x0, gx, gy, spread, lifted, angles, action) in enumerate(frames):
        # the picture the camera took
        ax.add_patch(Rectangle((x0, 1.0), 3.2, 2.6, facecolor='white', edgecolor=INK,
                               lw=1.0, zorder=1))
        ax.plot([x0 + 0.1, x0 + 3.1], [1.3, 1.3], color=MUTED, lw=1.0, zorder=2)
        _mug(ax, x0 + 1.7, 1.3 + (0.5 if lifted else 0.0), s=0.6)
        top = (x0 + gx, gy)
        ax.plot([top[0], top[0]], [top[1], 3.6], color=LINK, lw=5, zorder=3)
        _gripper(ax, top, -math.pi / 2, size=0.35, spread=spread)
        _label(ax, x0 + 1.6, 4.15, f'moment {k + 1}', size=10, color=MUTED)
        # the numbers and the answer
        _box(ax, x0 + 0.1, -0.35, 3.0, 0.9, face=PALE_YELLOW, edge=JOINT)
        _label(ax, x0 + 1.6, 0.1, f'joint angles {angles}', size=9)
        _box(ax, x0 + 0.1, -1.85, 3.0, 1.0, face=PALE_GREEN, edge=SLIDE)
        _label(ax, x0 + 1.6, -1.35, action, size=10)
        _arrow(ax, (x0 + 1.6, -0.4), (x0 + 1.6, -0.8), color=MUTED, lw=1.2, ms=10)
    _label(ax, -0.4, 2.3, 'what the\ncamera\nsaw', size=10, ha='right', weight='bold')
    _label(ax, -0.4, 0.1, 'where the\njoints were', size=10, ha='right', weight='bold')
    _label(ax, -0.4, -1.35, 'what the\nperson did\nnext', size=10, ha='right',
           weight='bold', color=SLIDE)
    _caption(ax, 6.8, -2.8, 'The top two rows become the question. The green row is the '
             'answer the network must learn to give.', size=10)
    _save(fig, BC_DOC, 'demonstration-pairs.svg')


def compounding_error() -> None:
    """Small mistakes carry the arm out of the region it was trained on, and they grow."""
    fig, ax = plt.subplots(figsize=(12.0, 5.8), facecolor='white')
    _axes(ax, (-1.2, 12.6), (-1.6, 5.0))
    ax.add_patch(Rectangle((0.0, -0.6), 10.2, 1.2, facecolor=PALE_GREEN, edgecolor='none',
                           zorder=1))
    _label(ax, 5.0, -1.0, 'the band where the demonstrations went (the network has seen '
           'these places)', size=9, color=SLIDE)
    ax.plot([0, 10.2], [0, 0], color=SLIDE, lw=2.2, ls='--', zorder=2)
    _mug_top(ax, 10.8, 0.0, r=0.45)
    _label(ax, 10.8, -0.85, 'mug', size=9, color=MUTED)

    xs = np.arange(0, 11, 1.0)
    drift = np.array([0.0, 0.08, 0.2, 0.38, 0.62, 0.95, 1.38, 1.92, 2.55, 3.25, 4.0])
    ax.plot(xs, drift, color=GRIP, lw=2.2, marker='o', ms=6, zorder=3)
    for k in (2, 5, 8):
        ax.plot([xs[k], xs[k]], [0, drift[k]], color=GRIP, lw=1.0, ls=':', zorder=2)
    _label(ax, 2.0, 0.95, 'tiny error', size=9, color=GRIP)
    _label(ax, 5.95, 1.6, 'now outside the band:\nit has never seen this', size=9, color=GRIP,
           ha='right')
    _label(ax, 8.7, 3.4, 'each guess is worse\nthan the one before', size=9, color=GRIP,
           ha='right')
    _label(ax, 10.1, 4.35, 'misses the mug', size=10, color=GRIP, weight='bold')
    ax.plot([0], [0], 'o', ms=10, color=INK, zorder=5)
    _label(ax, 0.0, 0.8, 'start', size=9)
    ax.plot([], [], color=SLIDE, lw=2.2, ls='--', label='what the person did')
    ax.plot([], [], color=GRIP, lw=2.2, marker='o', label='the copy, one decision per dot')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    _save(fig, BC_DOC, 'compounding-error.svg')


def averaging_left_and_right() -> None:
    """Half the people go left of the box, half go right; the average goes through it."""
    fig, ax = plt.subplots(figsize=(10.0, 5.6), facecolor='white')
    _axes(ax, (-1.0, 10.8), (-3.2, 3.6))
    _obstacle(ax, 4.0, -0.9, 1.8, 1.8)
    _label(ax, 4.9, -1.2, 'box', size=10, weight='bold')
    _mug_top(ax, 9.5, 0.0, r=0.45)
    t = np.linspace(0, 1, 60)
    x = t * 9.0
    bump = 2.1 * np.sin(math.pi * t)
    for off in (-0.12, 0.0, 0.12):
        ax.plot(x, bump + off * 2, color=SLIDE, lw=1.6, zorder=3)
        ax.plot(x, -bump + off * 2, color=LINK, lw=1.6, zorder=3)
    ax.plot(x, np.zeros_like(x), color=GRIP, lw=2.6, zorder=4)
    ax.plot([4.9], [0.0], 'X', ms=16, color=GRIP, mec='white', zorder=6)
    ax.plot([0], [0], 'o', ms=10, color=INK, zorder=5)
    _label(ax, 4.9, 2.75, 'some people went round the top', size=10, color=SLIDE)
    _label(ax, 4.9, -2.75, 'some people went round the bottom', size=10, color=LINK)
    _label(ax, 2.6, 0.4, 'the average of the two', size=10, color=GRIP)
    _label(ax, 0.0, -0.55, 'start', size=9)
    _save(fig, BC_DOC, 'averaging-left-and-right.svg')


def dagger_corrections() -> None:
    """Let the copy drive, have a person say what they would do there, add that to the data."""
    fig, ax = plt.subplots(figsize=(12.0, 5.4), facecolor='white')
    _axes(ax, (-1.2, 12.6), (-1.6, 4.6))
    ax.add_patch(Rectangle((0.0, -0.6), 10.2, 1.2, facecolor=PALE_GREEN, edgecolor='none',
                           zorder=1))
    ax.add_patch(Rectangle((1.5, 0.6), 8.7, 2.9, facecolor=PALE_YELLOW, edgecolor='none',
                           zorder=1))
    _label(ax, 5.8, 3.8, 'new places the copy reached, now covered by corrections', size=9,
           color=WRIST)
    ax.plot([0, 10.2], [0, 0], color=SLIDE, lw=2.2, ls='--', zorder=2)
    _mug_top(ax, 10.8, 0.0, r=0.45)
    xs = np.arange(0, 11, 1.0)
    drift = np.array([0.0, 0.08, 0.2, 0.38, 0.62, 0.95, 1.38, 1.92, 2.55, 3.0, 3.3])
    ax.plot(xs, drift, color=GRIP, lw=2.0, marker='o', ms=5, zorder=3)
    for k in (3, 5, 7, 9):
        tip = (xs[k] + 0.8, drift[k] - 0.55 * drift[k])
        _arrow(ax, (xs[k], drift[k]), tip, color=SLIDE, lw=2.0, z=4)
    _label(ax, 9.9, 1.25, 'what the person\nsays to do here', size=9, color=SLIDE,
           ha='left')
    _label(ax, 4.0, 1.6, 'the copy drives\nand drifts', size=9, color=GRIP)
    ax.plot([0], [0], 'o', ms=10, color=INK, zorder=5)
    _label(ax, 5.0, -1.0, 'the original demonstrations', size=9, color=SLIDE)
    _save(fig, BC_DOC, 'dagger-corrections.svg')


# --------------------------------------------------------------------------
# 03_action-chunking-transformers
# --------------------------------------------------------------------------

def one_step_vs_chunk() -> None:
    """Twelve decisions, one move each, against two decisions of six moves each."""
    fig, axes = _panels(2, (13.0, 5.2))
    xs = np.linspace(0.3, 7.5, 13)
    ys = 0.6 + 2.2 * np.sin(np.linspace(0, math.pi * 0.85, 13))
    for ax in axes:
        _axes(ax, (-0.3, 9.0), (-1.4, 4.4))
        _mug_top(ax, 8.3, ys[-1], r=0.4)

    ax = axes[0]
    for k in range(12):
        _arrow(ax, (xs[k], ys[k]), (xs[k + 1], ys[k + 1]), color=LINK, lw=1.6, ms=10)
        ax.plot([xs[k]], [ys[k]], 'o', ms=9, color=LINK, mec=INK, zorder=5)
    _title(ax, 4.2, 4.1, 'One move at a time')
    _caption(ax, 4.2, -0.8, '12 decisions. Each dot is a new guess,\n'
             'and each guess can add a little error.')

    ax = axes[1]
    for k in range(12):
        c = LINK if k < 6 else WRIST
        _arrow(ax, (xs[k], ys[k]), (xs[k + 1], ys[k + 1]), color=c, lw=1.6, ms=10)
    for k, c in ((0, LINK), (6, WRIST)):
        ax.plot([xs[k]], [ys[k]], 'o', ms=15, color=c, mec=INK, zorder=5)
    _label(ax, xs[0] + 0.2, ys[0] - 0.55, 'decide 6 moves', size=10, color=LINK)
    _label(ax, xs[6] + 0.1, ys[6] + 0.6, 'decide the next 6', size=10, color=WRIST)
    _title(ax, 4.2, 4.1, 'A chunk of moves at a time')
    _caption(ax, 4.2, -0.8, '2 decisions. Each one plans a whole burst.\n'
             'ACT uses much longer chunks, about 100 moves.')
    _save(fig, ACT_DOC, 'one-step-vs-chunk.svg')


def aloha_rig() -> None:
    """The person moves two small leader arms; two bigger follower arms copy them joint by joint."""
    fig, ax = plt.subplots(figsize=(13.0, 6.0), facecolor='white')
    _axes(ax, (-0.8, 16.8), (-2.2, 6.2))
    _floor(ax, -0.5, 5.0)
    _floor(ax, 6.6, 15.4)

    # leader arms, held by the person
    for bx in (0.8, 3.2):
        tip = _arm(ax, (bx, 0.0), (1.1, 1.0), (65, -110), color=MUTED, width=5, grip_size=0.2)
        ax.add_patch(Circle((tip[0] - 0.05, tip[1] + 0.3), 0.28, facecolor='#f2c9a5',
                            edgecolor=INK, lw=0.8, zorder=6))
    _label(ax, 2.2, 3.4, 'leader arms\nthe person holds these', size=10, weight='bold')

    # follower arms, doing the task
    for bx in (8.0, 12.8):
        _arm(ax, (bx, 0.0), (2.0, 1.8), (65, -110), color=LINK, width=7, grip_size=0.3)
    _mug(ax, 11.0, 0.0, s=0.9)
    _label(ax, 11.0, 4.7, 'follower arms\nthese do the task', size=10, weight='bold',
           color=LINK)

    # joint by joint copying
    _arrow(ax, (4.8, 1.5), (7.2, 1.5), color=JOINT, lw=2.2)
    _label(ax, 6.0, 2.05, 'same joint\nangles', size=9, color=WRIST)

    # four cameras
    _camera(ax, 11.0, 5.8, angle_deg=-90, s=1.1)
    _label(ax, 12.2, 5.8, 'top camera', size=9, ha='left')
    _camera(ax, 16.2, 1.2, angle_deg=180, s=1.1)
    _label(ax, 16.2, 1.8, 'front camera', size=9)
    _label(ax, 11.0, -1.1, 'plus one camera on each follower wrist: four cameras in all',
           size=9, color=MUTED)
    _label(ax, 2.2, -1.1, 'recorded: the pictures and all 14 joint angles', size=9,
           color=MUTED)
    _save(fig, ACT_DOC, 'aloha-rig.svg')


def inside_act() -> None:
    """Four pictures and the joint angles go in; a chunk of future joint targets comes out."""
    fig = plt.figure(figsize=(15.0, 6.0), facecolor='white')
    ax = fig.add_axes((0.0, 0.0, 0.66, 1.0))
    _axes(ax, (-0.5, 12.0), (-1.8, 6.0))

    # inputs: four camera pictures and the joint angles
    names = ('top', 'front', 'left wrist', 'right wrist')
    for i, name in enumerate(names):
        y = 4.6 - i * 1.3
        ax.add_patch(Rectangle((0.0, y), 1.4, 1.0, facecolor='white', edgecolor=INK,
                               lw=0.8, zorder=2))
        _mug(ax, 0.6, y + 0.15, s=0.45)
        _label(ax, 1.6, y + 0.5, name, size=9, ha='left')
    _box(ax, 0.0, -0.9, 2.8, 0.8, face=PALE_YELLOW, edge=JOINT)
    _label(ax, 1.4, -0.5, '14 joint angles', size=9)

    # step 1: image encoder turns each picture into a grid of numbers
    _arrow(ax, (2.9, 3.3), (3.6, 3.3))
    for j in range(4):
        for i in range(4):
            ax.add_patch(Rectangle((3.8 + i * 0.35, 2.6 + j * 0.35), 0.33, 0.33,
                                   facecolor=LINK_PALE if (i + j) % 2 else LINK,
                                   edgecolor='white', zorder=2))
    _label(ax, 4.5, 4.4, 'step 1\nimage encoder', size=10, weight='bold')
    _label(ax, 4.5, 1.95, 'each picture becomes\na grid of numbers', size=9, color=MUTED)

    # step 2: the transformer mixes everything together
    _arrow(ax, (5.4, 3.3), (6.3, 3.3))
    _arrow(ax, (2.9, -0.5), (6.35, 2.2), color=MUTED, lw=1.2, rad=0.15)
    _box(ax, 6.4, 1.8, 2.9, 3.0, face='white', edge=LINK, lw=1.6)
    rng = np.random.default_rng(1)
    pts = [(6.8 + rng.uniform(0, 2.1), 2.1 + rng.uniform(0, 2.4)) for _ in range(9)]
    for a in pts:
        for b in pts:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=GRID, lw=0.6, zorder=2)
    for p in pts:
        ax.add_patch(Circle(p, 0.12, facecolor=WRIST, edgecolor=INK, lw=0.5, zorder=3))
    _label(ax, 7.85, 5.35, 'step 2\ntransformer', size=10, weight='bold')
    _label(ax, 7.85, 1.2, 'every piece is compared\nwith every other piece', size=9,
           color=MUTED)
    _arrow(ax, (9.4, 3.3), (11.8, 3.3))
    _label(ax, 10.6, 3.85, 'step 3\nchunk out', size=10, weight='bold')

    # output: the chunk, drawn as one joint's target angle over the next two seconds
    out = fig.add_axes((0.69, 0.2, 0.29, 0.6))
    t = np.arange(100) / 50.0
    angle = 40 + 25 * (1 - np.cos(math.pi * t / 2.0)) / 2 + 3 * np.sin(3 * t)
    out.plot(t, angle, 'o', ms=2.5, color=WRIST)
    out.set_xlabel('time from now (seconds)', fontsize=10, color=INK)
    out.set_ylabel('elbow target (degrees)', fontsize=10, color=INK)
    out.set_title('the chunk: 100 targets for each joint\n(2 seconds at 50 per second)',
                  fontsize=10, color=INK)
    out.set_xlim(0, 2.0)
    for side in ('top', 'right'):
        out.spines[side].set_visible(False)
    out.tick_params(labelsize=9)
    out.grid(color=GRID, lw=0.6)
    _save(fig, ACT_DOC, 'inside-act.svg')


def temporal_ensembling() -> None:
    """Several overlapping chunks each predict the same moment; the arm uses their average."""
    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _axes(ax, (-2.6, 11.4), (-1.6, 5.4))
    rows = ((0, 3.8, 0.10), (1, 2.9, -0.12), (2, 2.0, 0.05), (3, 1.1, -0.04))
    now = 3
    for start, y, bias in rows:
        cells = [start + k for k in range(6)]
        for c in cells:
            face = PALE_YELLOW if c == now else LINK_PALE
            ax.add_patch(Rectangle((c * 1.2, y), 1.1, 0.7, facecolor=face, edgecolor=LINK,
                                   lw=0.8, zorder=2))
        _label(ax, -0.2, y + 0.35, f'chunk made at step {start}', size=9, ha='right')
        _label(ax, now * 1.2 + 0.55, y + 0.35, f'{30 + bias * 10:.1f}°', size=9)
    ax.add_patch(Rectangle((now * 1.2 - 0.08, 0.95), 1.26, 3.7, facecolor='none',
                           edgecolor=WRIST, lw=2.0, zorder=3))
    _arrow(ax, (now * 1.2 + 0.55, 0.9), (now * 1.2 + 0.55, 0.05), color=WRIST, lw=2.0)
    _box(ax, now * 1.2 - 0.9, -1.05, 3.0, 0.95, face=PALE_GREEN, edge=SLIDE)
    _label(ax, now * 1.2 + 0.6, -0.58, 'weighted average\nsent to the arm', size=9)
    for c in range(9):
        _label(ax, c * 1.2 + 0.55, 4.95, f'{c}', size=9, color=MUTED)
    _label(ax, 4.8, 5.3, 'time step', size=9, color=MUTED)
    _label(ax, 7.8, -0.6, 'Four chunks all predicted the elbow angle for step 3.\n'
           'The arm uses a blend of the four, so one bad guess cannot jerk it.',
           size=10, color=INK, ha='left')
    _save(fig, ACT_DOC, 'temporal-ensembling.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    policy_loop()
    five_kinds()
    demonstration_pairs()
    compounding_error()
    averaging_left_and_right()
    dagger_corrections()
    one_step_vs_chunk()
    aloha_rig()
    inside_act()
    temporal_ensembling()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
