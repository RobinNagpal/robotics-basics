"""Generate the diagrams for the second half of the movement-models chapter.

The documents are in docs/06_learned-models/06_movement-models/:
04_diffusion-and-flow-policies.md, 05_reinforcement-learning-policies.md and
06_learned-motion-planners.md. Each picture illustrates one idea from its own
document, and goes to docs/images/movement-models/<doc-name>/.

Run with:  pixi run python ../docs/diagrams/movement_models_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every curve here is drawn to show an idea, not measured. None of the pictures
carries a measured number, and the documents say so where it matters.
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
from numpy.fft import fft2, ifft2  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

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
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b6fd1'
OBSTACLE: str = '#9a9a9a'
OBSTACLE_PALE: str = '#e4e4e4'
PURPLE: str = '#7b5aa6'
MUG: str = '#c96f3b'

Point = tuple[float, float]


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
    ax.text(x, y, text, fontsize=12, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 9.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _arrow(ax: Axes, a: Point, b: Point, color: str = INK, lw: float = 1.6,
           style: str = '-|>', z: int = 6) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=z)


def _floor(ax: Axes, x0: float, x1: float, y: float = 0.0) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.2, zorder=1)
    for x in np.arange(x0 + 0.1, x1, 0.3):
        ax.plot([x, x - 0.15], [y, y - 0.15], color=GRID, lw=1.0, zorder=1)


def _box(ax: Axes, x: float, y: float, w: float, h: float, color: str = OBSTACLE,
         label: str = '') -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=INK, lw=0.8, zorder=2))
    if label:
        _label(ax, x + w / 2, y + h / 2, label, size=9, color='white')


def _mug(ax: Axes, x: float, y: float, w: float = 0.5, h: float = 0.6,
         angle_deg: float = 0.0, color: str = MUG) -> None:
    """A mug seen from the side, standing on (x, y), optionally tipped over."""
    body = np.array([(-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)])
    handle = np.array([(w / 2, h * 0.25), (w / 2 + w * 0.3, h * 0.3),
                       (w / 2 + w * 0.3, h * 0.7), (w / 2, h * 0.75)])
    a = math.radians(angle_deg)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    for shape, closed in ((body, True), (handle, False)):
        pts = shape @ rot.T + np.array([x, y])
        if closed:
            ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor=INK, lw=0.8,
                                 zorder=4))
        else:
            ax.plot(pts[:, 0], pts[:, 1], color=INK, lw=1.6, zorder=3)


def _gripper(ax: Axes, p: Point, angle: float, size: float = 0.3, color: str = GRIP) -> None:
    """Two short fingers opening in the direction the gripper points."""
    c = math.cos(angle)
    s = math.sin(angle)
    nx, ny = -s, c
    for side in (1, -1):
        root = (p[0] + side * size * 0.6 * nx, p[1] + side * size * 0.6 * ny)
        tip = (root[0] + size * c, root[1] + size * s)
        ax.plot([p[0], root[0], tip[0]], [p[1], root[1], tip[1]], color=color, lw=3,
                solid_capstyle='round', zorder=5)


def _planar_arm(ax: Axes, angles: list[float], lengths: list[float], base: Point = (0, 0),
                color: str = LINK, width: float = 6, joints: bool = True,
                z: int = 3) -> list[Point]:
    """Draw a flat arm from joint angles (radians, each relative to the last link)."""
    pts: list[Point] = [base]
    heading = 0.0
    for q, length in zip(angles, lengths):
        heading += q
        x, y = pts[-1]
        pts.append((x + length * math.cos(heading), y + length * math.sin(heading)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=width, solid_capstyle='round', zorder=z)
    if joints:
        for p in pts[:-1]:
            ax.plot([p[0]], [p[1]], 'o', color=JOINT, ms=8, zorder=z + 1)
    return pts


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _around(side: float, n: int = 40) -> NDArray[np.float64]:
    """A smooth path from (0, 0) to (6, 0) that bends round a box at x = 3.

    side = +1 goes over the top of the box on the page, -1 goes under it.
    """
    t = np.linspace(0, 1, n)
    x = 6 * t
    y = side * 1.7 * np.sin(np.pi * t) ** 1.3
    return np.stack([x, y], axis=1)


# --------------------------------------------------------------------------
# 04_diffusion-and-flow-policies
# --------------------------------------------------------------------------

DIFF_DOC: str = 'diffusion-and-flow-policies'


def _scene_around_box(ax: Axes) -> None:
    _axes(ax, (-0.8, 6.8), (-2.6, 2.7))
    _box(ax, 2.45, -0.75, 1.1, 1.5, label='box')
    ax.plot([0], [0], 'o', color=INK, ms=7, zorder=6)
    _label(ax, -0.1, -0.45, 'start', size=9)
    _mug(ax, 6.0, -0.3, w=0.45, h=0.55)
    _label(ax, 6.0, -0.65, 'mug', size=9)


def average_goes_through() -> None:
    """Demonstrations go left or right round a box; their average goes through it."""
    fig, axes = _panels(2, (12.0, 4.8))
    for ax in axes:
        _scene_around_box(ax)
    rng = np.random.default_rng(3)

    ax = axes[0]
    _title(ax, 3.0, 2.5, 'Plain copying: one answer, the average')
    for i in range(6):
        side = 1 if i % 2 == 0 else -1
        path = _around(side * (0.9 + 0.2 * rng.random()))
        ax.plot(path[:, 0], path[:, 1], color=LINK_PALE, lw=2, zorder=1)
    ax.plot([0, 6], [0, 0], color=GRIP, lw=3, ls=(0, (5, 3)), zorder=5)
    _label(ax, 1.2, 0.35, 'average', size=9.5, color=GRIP, weight='bold')
    _caption(ax, 3.0, -2.35, 'Half the people went over, half went under.\n'
             'The average of the two goes straight into the box.')

    ax = axes[1]
    _title(ax, 3.0, 2.5, 'Diffusion or flow policy: one of the real ways')
    for i in range(6):
        side = 1 if i % 2 == 0 else -1
        path = _around(side * (0.9 + 0.2 * rng.random()))
        ax.plot(path[:, 0], path[:, 1], color=LINK_PALE, lw=2, zorder=1)
    for side, label, y in ((1, 'run 1', 1.95), (-1, 'run 2', -1.95)):
        path = _around(side)
        ax.plot(path[:, 0], path[:, 1], color=SLIDE, lw=3, zorder=5)
        _label(ax, 1.0, y * 0.75, label, size=9.5, color=SLIDE, weight='bold')
    _caption(ax, 3.0, -2.35, 'Each run picks one whole path, over or under.\n'
             'No run goes through the middle.')
    _label(ax, 5.2, 2.05, 'pale lines:\nthe demonstrations', size=8.5, color=MUTED)
    _save(fig, DIFF_DOC, 'average-goes-through.svg')


def noise_to_path() -> None:
    """A path of waypoints starts as random dots and is cleaned up step by step."""
    target = _around(1, n=12)
    rng = np.random.default_rng(7)
    noise = np.stack([rng.uniform(0, 6, 12), rng.uniform(-2.0, 2.0, 12)], axis=1)
    stages = [(0.0, '1. start: random dots'), (0.35, '2. after a few steps'),
              (0.75, '3. after more steps'), (1.0, '4. last step: a clean path')]
    fig, axes = _panels(4, (15.0, 3.3))
    fig.subplots_adjust(wspace=0.25)
    for ax, (k, title) in zip(axes, stages):
        _axes(ax, (-0.8, 6.8), (-2.3, 2.9))
        _box(ax, 2.45, -0.75, 1.1, 1.5)
        pts = (1 - k) * noise + k * target
        ax.plot(pts[:, 0], pts[:, 1], color=LINK_PALE if k < 1 else LINK, lw=1.5, zorder=3)
        ax.plot(pts[:, 0], pts[:, 1], 'o', color=LINK, ms=6, zorder=4)
        ax.plot([0], [0], 'o', color=INK, ms=6, zorder=6)
        _mug(ax, 6.0, -0.3, w=0.45, h=0.55)
        _title(ax, 3.0, 2.75, title)
    fig.text(0.5, 0.0, 'Each dot is one planned position of the gripper. '
             'The network moves every dot a little at each step.',
             ha='center', fontsize=10, color=MUTED)
    _save(fig, DIFF_DOC, 'noise-to-path.svg')


def many_steps_or_few() -> None:
    """Diffusion walks from noise in many small steps; flow matching in a few straight ones."""
    fig, axes = _panels(2, (11.5, 4.8))
    start = np.array([0.4, 0.6])
    end = np.array([5.4, 3.4])
    rng = np.random.default_rng(11)

    ax = axes[0]
    _axes(ax, (-0.4, 6.4), (-0.6, 4.6))
    _title(ax, 3.0, 4.4, 'Diffusion: many small steps')
    n = 40
    pts = [start]
    for i in range(1, n + 1):
        base = start + (end - start) * (i / n)
        bend = np.array([-0.9, 0.9]) * math.sin(math.pi * i / n)
        wob = rng.normal(0, 0.12, 2) * (1 - i / n)
        pts.append(base + bend + wob)
    pts_arr = np.array(pts)
    pts_arr[-1] = end
    ax.plot(pts_arr[:, 0], pts_arr[:, 1], color=PURPLE, lw=1.2, zorder=3)
    ax.plot(pts_arr[:, 0], pts_arr[:, 1], 'o', color=PURPLE, ms=3, zorder=4)
    _caption(ax, 3.0, -0.35, 'The network is run once per step, so many steps take longer.')

    ax = axes[1]
    _axes(ax, (-0.4, 6.4), (-0.6, 4.6))
    _title(ax, 3.0, 4.4, 'Flow matching: a few straight steps')
    k = 5
    for i in range(k):
        a = start + (end - start) * (i / k)
        b = start + (end - start) * ((i + 1) / k)
        _arrow(ax, (a[0], a[1]), (b[0], b[1]), color=SLIDE, lw=2.2)
    _caption(ax, 3.0, -0.35, 'The network learned a straight direction, so fewer steps are enough.')

    for ax in axes:
        ax.plot([start[0]], [start[1]], 'o', color=MUTED, ms=12, zorder=5)
        _label(ax, start[0] + 0.1, start[1] - 0.45, 'random noise', size=9.5, color=MUTED)
        ax.plot([end[0]], [end[1]], '*', color=GRIP, ms=18, zorder=5)
        _label(ax, end[0], end[1] - 0.5, 'a good\naction chunk', size=9.5, color=GRIP)
    _save(fig, DIFF_DOC, 'many-steps-or-few.svg')


def predict_play_repeat() -> None:
    """Plan a chunk of 8 positions, play the first 4, look again, plan again."""
    fig, axes = plt.subplots(3, 1, figsize=(11.0, 6.6), facecolor='white')
    xs = np.linspace(0, 11, 21)
    ys = 1.3 * np.sin(xs / 11 * math.pi) + 0.25
    colors = [LINK, SLIDE, PURPLE]
    for c, ax in enumerate(axes):
        _axes(ax, (-2.6, 12.2), (-0.3, 2.0))
        _floor(ax, -0.2, 12.0, 0.0)
        _mug(ax, 11.5, 0.0, w=0.45, h=0.5)
        s = 4 * c
        done = slice(0, s + 1)
        ax.plot(xs[done], ys[done], color=INK, lw=2.5, zorder=2)
        px = xs[s:s + 8]
        py = ys[s:s + 8]
        # a plan made later sees the mug better, so it bends a little differently
        py = py + 0.12 * (np.arange(len(px)) / 8) * (1 - c)
        ax.plot(px, py, color=colors[c], lw=1, zorder=3)
        ax.plot(px[4:], py[4:], 'o', color=colors[c], ms=7, mfc='white', zorder=4)
        ax.plot(px[:4], py[:4], 'o', color=colors[c], ms=7, zorder=5)
        _gripper(ax, (xs[s], ys[s]), math.atan2(ys[s + 1] - ys[s], xs[s + 1] - xs[s]))
        _label(ax, -2.5, 1.0, f'plan {c + 1}', size=11, color=colors[c], ha='left',
               weight='bold')
    _label(axes[0], 5.0, 1.95, 'filled: played on the arm      hollow: thrown away',
           size=9.5, color=MUTED)
    _caption(axes[2], 5.0, -0.55, 'Each plan is 8 positions. The arm plays the first 4, '
             'the camera looks again, and a new plan starts where the arm now is. '
             'Black: where the gripper has been.', size=9)
    _save(fig, DIFF_DOC, 'predict-play-repeat.svg')


# --------------------------------------------------------------------------
# 05_reinforcement-learning-policies
# --------------------------------------------------------------------------

RL_DOC: str = 'reinforcement-learning-policies'


def _peg_scene(ax: Axes, peg_x: float, peg_y: float, tilt: float = 0.0) -> None:
    """A block with a hole, and a peg held by a gripper above it."""
    _floor(ax, -1.6, 1.6, 0.0)
    ax.add_patch(Rectangle((-1.4, 0), 1.15, 0.8, facecolor=OBSTACLE, edgecolor=INK, lw=0.8,
                           zorder=2))
    ax.add_patch(Rectangle((0.25, 0), 1.15, 0.8, facecolor=OBSTACLE, edgecolor=INK, lw=0.8,
                           zorder=2))
    ax.add_patch(Rectangle((-0.25, 0), 0.5, 0.8, facecolor='white', edgecolor=INK, lw=0.8,
                           zorder=1))
    a = math.radians(tilt)
    w, h = 0.4, 1.0
    corners = np.array([(-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)])
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = corners @ rot.T + np.array([peg_x, peg_y])
    ax.add_patch(Polygon(pts, closed=True, facecolor=JOINT, edgecolor=INK, lw=0.8, zorder=3))
    top = np.array([0, h]) @ rot.T + np.array([peg_x, peg_y])
    _gripper(ax, (top[0], top[1] + 0.3), -math.pi / 2 + a, size=0.45)
    ax.plot([top[0], top[0]], [top[1] + 0.3, top[1] + 0.9], color=LINK, lw=6,
            solid_capstyle='round', zorder=4)


def try_score_adjust() -> None:
    """Three attempts at a peg-in-hole, each given a reward number."""
    fig, axes = _panels(3, (12.0, 4.6))
    tries = [(-0.9, 0.85, 12.0, 'attempt 1', 'peg lands on the block', '0.1', GRIP),
             (0.35, 0.75, -6.0, 'attempt 40', 'peg catches the edge', '0.5', WRIST),
             (0.0, 0.2, 0.0, 'attempt 900', 'peg goes into the hole', '1.0', SLIDE)]
    for ax, (x, y, tilt, title, what, reward, color) in zip(axes, tries):
        _axes(ax, (-1.7, 1.7), (-1.3, 3.4))
        _peg_scene(ax, x, y, tilt)
        _title(ax, 0.0, 3.2, title)
        _label(ax, 0.0, -0.4, what, size=9.5)
        ax.add_patch(FancyBboxPatch((-0.7, -1.2), 1.4, 0.5, boxstyle='round,pad=0.05',
                                    facecolor='white', edgecolor=color, lw=1.6, zorder=5))
        _label(ax, 0.0, -0.95, f'reward {reward}', size=10.5, color=color, weight='bold')
    fig.text(0.5, 0.0, 'The reward is a number the program computes after each attempt. '
             'The policy is nudged towards whatever earned more.',
             ha='center', fontsize=10, color=MUTED)
    _save(fig, RL_DOC, 'try-score-adjust.svg')


def reward_loophole() -> None:
    """The reward said 'mug near the X'. The policy found that knocking it over counts."""
    fig, axes = _panels(2, (11.5, 4.6))
    for ax in axes:
        _axes(ax, (-0.4, 6.4), (-1.6, 3.3))
        _floor(ax, -0.2, 6.2, 0.0)
        ax.plot([4.6, 5.0], [0.05, 0.35], color=GRIP, lw=2.5, zorder=2)
        ax.plot([4.6, 5.0], [0.35, 0.05], color=GRIP, lw=2.5, zorder=2)
        _label(ax, 4.8, -0.35, 'target spot', size=9, color=GRIP)

    ax = axes[0]
    _title(ax, 3.0, 3.1, 'What the person meant')
    _mug(ax, 1.0, 0.0, w=0.4, h=0.75, color=LINK_PALE)
    _mug(ax, 4.8, 0.0, w=0.4, h=0.75)
    ax.plot([1.0, 1.0, 4.8, 4.8], [0.9, 2.2, 2.2, 0.9], color=SLIDE, lw=2, ls=(0, (4, 2)),
            zorder=3)
    _arrow(ax, (4.8, 1.3), (4.8, 0.85), color=SLIDE, lw=2)
    _label(ax, 2.9, 2.5, 'lift the mug, carry it, put it down', size=9.5, color=SLIDE)
    _caption(ax, 3.0, -1.1, 'reward: mug is near the target spot')

    ax = axes[1]
    _title(ax, 3.0, 3.1, 'What the policy learned')
    _mug(ax, 1.0, 0.0, w=0.4, h=0.75, color=LINK_PALE)
    _mug(ax, 4.8 + 0.375, 0.2, w=0.4, h=0.75, angle_deg=90)
    _arrow(ax, (0.2, 0.3), (0.65, 0.3), color=GRIP, lw=2.5)
    _label(ax, 0.3, 0.75, 'swipe', size=9.5, color=GRIP, weight='bold')
    ax.plot([1.4, 4.4], [0.35, 0.35], color=GRIP, lw=1.5, ls=(0, (2, 2)), zorder=2)
    _label(ax, 2.9, 0.7, 'mug slides and tips over', size=9.5, color=GRIP)
    _label(ax, 5.0, 1.05, 'on its side', size=9.5, color=INK)
    _caption(ax, 3.0, -1.1, 'same reward: the mug is near the target spot, on its side')
    _save(fig, RL_DOC, 'reward-loophole.svg')


def many_simulated_worlds() -> None:
    """Domain randomisation: train in many different simulated rooms, then the real one."""
    fig = plt.figure(figsize=(12.0, 5.4), facecolor='white')
    worlds = [('#f4f1ea', 0.50, 0.60, 1.0, 'light wood table'),
              ('#d9e4f0', 0.40, 0.50, 0.7, 'blue table, dim light'),
              ('#e8e8e8', 0.60, 0.70, 0.9, 'bigger mug'),
              ('#efe0d0', 0.45, 0.55, 0.5, 'dark room'),
              ('#e2efe2', 0.50, 0.45, 1.0, 'short mug, slippery'),
              ('#f0e4ef', 0.55, 0.65, 0.8, 'camera moved')]
    for i, (table, w, h, light, name) in enumerate(worlds):
        ax = fig.add_axes((0.02 + (i % 3) * 0.2, 0.52 - (i // 3) * 0.46, 0.18, 0.4))
        _axes(ax, (-1.4, 1.4), (-0.8, 1.6))
        shade = 1 - light
        ax.add_patch(Rectangle((-1.35, -0.75), 2.7, 2.3, facecolor=(shade * 0.5,) * 3,
                               alpha=0.35 * shade + 0.02, edgecolor=MUTED, lw=0.8, zorder=0))
        ax.add_patch(Rectangle((-1.35, -0.75), 2.7, 0.75, facecolor=table, edgecolor=MUTED,
                               lw=0.8, zorder=1))
        shift = 0.35 if name == 'camera moved' else 0.0
        _mug(ax, 0.2 + shift, 0.0, w=w, h=h)
        _label(ax, 0.0, 1.35, name, size=9)
        _label(ax, -1.2, -0.52, f'sim {i + 1}', size=8, color=MUTED, ha='left')
    fig.text(0.32, 0.03, 'Training: thousands of randomly changed simulated worlds',
             ha='center', fontsize=10, color=MUTED)
    fig.text(0.635, 0.5, '→', fontsize=30, ha='center', va='center', color=MUTED)
    ax = fig.add_axes((0.68, 0.2, 0.3, 0.62))
    _axes(ax, (-1.4, 1.4), (-0.8, 1.6))
    ax.add_patch(Rectangle((-1.35, -0.75), 2.7, 2.3, facecolor='white', edgecolor=INK,
                           lw=1.6, zorder=0))
    ax.add_patch(Rectangle((-1.35, -0.75), 2.7, 0.75, facecolor='#e9dcc8', edgecolor=INK,
                           lw=0.8, zorder=1))
    _mug(ax, 0.1, 0.0, w=0.5, h=0.58)
    _label(ax, 0.0, 1.3, 'the real table', size=11, weight='bold')
    fig.text(0.83, 0.1, 'The real world is one more\nvariation the policy has seen.',
             ha='center', fontsize=10, color=MUTED)
    _save(fig, RL_DOC, 'many-simulated-worlds.svg')


# --------------------------------------------------------------------------
# 06_learned-motion-planners
# --------------------------------------------------------------------------

PLAN_DOC: str = 'learned-motion-planners'


def time_to_answer() -> None:
    """A sampling planner's time varies a lot; a network's time is the same every run."""
    rng = np.random.default_rng(5)
    planner = np.concatenate([rng.lognormal(0.0, 0.55, 300), rng.lognormal(1.6, 0.35, 12)])
    network = rng.normal(1.1, 0.04, 300)
    fig, ax = plt.subplots(figsize=(10.0, 4.4), facecolor='white')
    bins = np.linspace(0, 8, 65)
    ax.hist(planner, bins=bins, color=LINK, alpha=0.75, label='sampling planner, 300 runs')
    ax.hist(network, bins=bins, color=SLIDE, alpha=0.85, label='learned planner, 300 runs')
    ax.set_xlabel('time to produce a path (no units: a drawing, not a measurement)',
                  color=INK)
    ax.set_ylabel('number of runs', color=INK)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc='upper right')
    ax.annotate('a few runs take\nmuch longer', xy=(7.1, 1.5), xytext=(6.6, 30),
                ha='center', color=LINK, fontsize=10,
                arrowprops={'arrowstyle': '-|>', 'color': LINK, 'lw': 1.2})
    ax.annotate('every run takes\nabout the same time', xy=(1.25, 60), xytext=(2.9, 72),
                ha='left', color=SLIDE, fontsize=10,
                arrowprops={'arrowstyle': '-|>', 'color': SLIDE, 'lw': 1.2})
    _save(fig, PLAN_DOC, 'time-to-answer.svg')


def next_waypoint() -> None:
    """An MPNet-style planner: the network proposes the next point, a checker tests each hop."""
    fig, axes = _panels(2, (12.0, 5.0))
    walls = [(2.0, -0.4, 0.8, 2.8), (4.2, 0.45, 0.8, 4.15)]
    points = [(0.4, 0.6), (1.6, 3.2), (3.4, 3.4), (3.9, 0.9), (5.6, 0.6), (6.6, 3.6)]
    for ax in axes:
        _axes(ax, (-0.3, 7.3), (-1.7, 4.9))
        ax.add_patch(Rectangle((-0.1, -0.4), 7.2, 5.0, facecolor='white', edgecolor=MUTED,
                               lw=0.8, zorder=0))
        for x, y, w, h in walls:
            _box(ax, x, y, w, h)
        ax.plot([points[0][0]], [points[0][1]], 'o', color=INK, ms=9, zorder=6)
        ax.plot([points[-1][0]], [points[-1][1]], '*', color=GRIP, ms=17, zorder=6)
        _label(ax, points[0][0], points[0][1] - 0.4, 'start', size=9)
        _label(ax, points[-1][0] - 0.1, points[-1][1] + 0.45, 'goal', size=9, color=GRIP)

    ax = axes[0]
    _title(ax, 3.5, 4.75, 'The network proposes the next point, again and again')
    for i in range(len(points) - 1):
        _arrow(ax, points[i], points[i + 1], color=LINK, lw=2)
        if 0 < i:
            ax.plot([points[i][0]], [points[i][1]], 'o', color=LINK, ms=7, zorder=6)
            dx = -0.3 if i == 3 else 0.3
            _label(ax, points[i][0] + dx, points[i][1] + 0.3, str(i), size=10, color=LINK,
                   weight='bold')
    _caption(ax, 3.5, -1.2, 'Each hop: look at the scene, the goal and where you are,\n'
             'then guess the next point.')

    ax = axes[1]
    _title(ax, 3.5, 4.75, 'A classical checker tests every hop, then repairs')
    bad_from, bad_to = points[3], points[4]
    for i in range(len(points) - 1):
        if i == 3:
            continue
        ax.plot([points[i][0], points[i + 1][0]], [points[i][1], points[i + 1][1]],
                color=SLIDE, lw=2.5, zorder=4)
    ax.plot([bad_from[0], bad_to[0]], [bad_from[1], bad_to[1]], color=GRIP, lw=2.5,
            ls=(0, (4, 2)), zorder=4)
    _label(ax, 5.15, 1.05, 'clips the wall', size=9.5, color=GRIP, ha='left')
    detour = [bad_from, (4.0, 0.1), (5.3, 0.1), bad_to]
    ax.plot([p[0] for p in detour], [p[1] for p in detour], color=WRIST, lw=2.5, zorder=5)
    _label(ax, 4.65, -0.65, 'orange: repair found by a normal planner', size=9, color=WRIST)
    for p in points[1:-1]:
        ax.plot([p[0]], [p[1]], 'o', color=SLIDE, ms=7, zorder=6)
    _caption(ax, 3.5, -1.2, 'Green hops passed the check.\nThe red one failed and was replaced.')
    _save(fig, PLAN_DOC, 'next-waypoint.svg')


def _two_link_hits(q1: NDArray[np.float64], q2: NDArray[np.float64]) -> NDArray[np.bool_]:
    """True where a two-link arm (links 1.0 and 0.8) touches a round post."""
    cx, cy, r = 1.05, 0.95, 0.28
    hit = np.zeros(q1.shape, dtype=bool)
    for t in np.linspace(0, 1, 12):
        x1 = t * np.cos(q1)
        y1 = t * np.sin(q1)
        hit |= (x1 - cx) ** 2 + (y1 - cy) ** 2 < r ** 2
        x2 = np.cos(q1) + t * 0.8 * np.cos(q1 + q2)
        y2 = np.sin(q1) + t * 0.8 * np.sin(q1 + q2)
        hit |= (x2 - cx) ** 2 + (y2 - cy) ** 2 < r ** 2
    return hit


def wrong_near_the_edge() -> None:
    """A two-joint arm, its collision region in joint space, and a learned guess of it."""
    fig, axes = _panels(2, (12.0, 5.2))

    ax = axes[0]
    _axes(ax, (-0.6, 2.2), (-1.2, 1.9))
    _title(ax, 0.8, 1.8, 'The arm and a post')
    ax.add_patch(Circle((1.05, 0.95), 0.28, facecolor=OBSTACLE, edgecolor=INK, lw=0.8,
                        zorder=2))
    _label(ax, 1.05, 0.95, 'post', size=9, color='white')
    _planar_arm(ax, [math.radians(-20), math.radians(90)], [1.0, 0.8])
    _planar_arm(ax, [math.radians(44), math.radians(23)], [1.0, 0.8], color=GRIP)
    _label(ax, 0.8, -0.8, 'blue: clear      red: touching the post', size=9.5)
    _caption(ax, 0.8, -1.05, 'Each arm pose is two joint angles.')

    ax = axes[1]
    n = 240
    q1 = np.linspace(-math.pi / 2, math.pi, n)
    q2 = np.linspace(-math.pi, math.pi, n)
    Q1, Q2 = np.meshgrid(q1, q2)
    hit = _two_link_hits(Q1, Q2).astype(float)
    ax.contourf(np.degrees(Q1), np.degrees(Q2), hit, levels=[0.5, 1.5], colors=[OBSTACLE])
    # the learned guess: the true boundary, smoothed and shifted a little
    k = np.exp(-((np.arange(n) - n // 2) ** 2) / (2 * 6.0 ** 2))
    kern = np.outer(k, k)
    kern /= kern.sum()
    smooth = np.real(ifft2(fft2(hit) * fft2(np.fft.ifftshift(kern))))
    guess = np.roll(smooth, (4, -5), axis=(0, 1))
    ax.contour(np.degrees(Q1), np.degrees(Q2), guess, levels=[0.5], colors=[GRIP],
               linewidths=2, linestyles='dashed')
    ax.plot([-20], [90], 'o', color=LINK, ms=9, zorder=5)
    ax.plot([44], [23], 'o', color=GRIP, ms=9, zorder=5)
    ax.annotate('the network says "clear" here,\nbut the arm touches the post',
                xy=(44, 23), xytext=(75, 110), fontsize=9.5, color=GRIP, ha='left',
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    ax.set_xlabel('joint 1 angle (degrees)')
    ax.set_ylabel('joint 2 angle (degrees)')
    ax.set_title('Every pose as a dot: grey = touches the post', fontsize=12, weight='bold',
                 color=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.plot([], [], color=GRIP, lw=2, ls='--', label="the network's guess of the edge")
    ax.legend(frameon=False, loc='lower left', fontsize=9.5)
    _save(fig, PLAN_DOC, 'wrong-near-the-edge.svg')


def many_ik_answers() -> None:
    """A three-joint flat arm reaching one point in several different ways."""
    fig, axes = _panels(2, (12.0, 5.0))
    lengths = [1.0, 0.8, 0.5]
    target = (1.4, 0.9)

    def solve(phi: float, elbow: int) -> list[float] | None:
        wx = target[0] - lengths[2] * math.cos(phi)
        wy = target[1] - lengths[2] * math.sin(phi)
        d2 = wx * wx + wy * wy
        c2 = (d2 - lengths[0] ** 2 - lengths[1] ** 2) / (2 * lengths[0] * lengths[1])
        if abs(c2) > 1:
            return None
        q2 = elbow * math.acos(c2)
        q1 = math.atan2(wy, wx) - math.atan2(lengths[1] * math.sin(q2),
                                             lengths[0] + lengths[1] * math.cos(q2))
        return [q1, q2, phi - q1 - q2]

    ax = axes[0]
    _axes(ax, (-0.6, 2.4), (-0.9, 2.0))
    _title(ax, 0.9, 1.9, 'A classical solver: one answer per call')
    q = solve(math.radians(-20), 1)
    assert q is not None
    _planar_arm(ax, q, lengths)
    ax.plot([target[0]], [target[1]], '*', color=GRIP, ms=17, zorder=7)
    _caption(ax, 0.9, -0.7, 'Which answer you get depends on where the solver started.')

    ax = axes[1]
    _axes(ax, (-0.6, 2.4), (-0.9, 2.0))
    _title(ax, 0.9, 1.9, 'A learned solver: many answers at once')
    count = 0
    for phi_deg in (-60, -30, 0, 30, 60):
        for elbow in (1,):
            q = solve(math.radians(phi_deg), elbow)
            if q is None:
                continue
            _planar_arm(ax, q, lengths, color=LINK_PALE if count else LINK, width=4,
                        joints=False, z=3 if count else 4)
            count += 1
    ax.plot([target[0]], [target[1]], '*', color=GRIP, ms=17, zorder=7)
    ax.plot([0], [0], 'o', color=JOINT, ms=9, zorder=6)
    _caption(ax, 0.9, -0.7, f'{count} different joint settings, all putting the gripper '
             'on the star.')
    _save(fig, PLAN_DOC, 'many-ik-answers.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    average_goes_through()
    noise_to_path()
    many_steps_or_few()
    predict_play_repeat()
    try_score_adjust()
    reward_loophole()
    many_simulated_worlds()
    time_to_answer()
    next_waypoint()
    wrong_near_the_edge()
    many_ik_answers()


if __name__ == '__main__':
    main()
