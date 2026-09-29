"""Generate the diagrams used in docs/01_robotics-intro/04_kinematics/.

Each doc's pictures go to a folder named after it:

  docs/images/kinematics/forward-kinematics/
  docs/images/kinematics/inverse-kinematics/

Run with:  pixi run python ../docs/diagrams/kinematics.py
Add --png DIR to also write a PNG copy of every picture into DIR, for checking.

Every picture draws the same arm as the frames area: link 1 is 3 m, link 2 is
2 m, and the third link, where there is one, is 1 m. The positions come from
code/src/kinematics/planar_arm.py, so a picture cannot disagree with the numbers
the doc quotes.
"""

from collections.abc import Callable
import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle  # noqa: E402  (must follow matplotlib.use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'code' / 'src' / 'kinematics'))
# Imported after the sys.path line above, which flake8's import rules cannot see.
from planar_arm import (forward, numerical_ik, points, three_joint_ik,  # noqa: E402,I100,I202
                        THREE_LINKS, two_joint_ik, TWO_LINKS)

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'kinematics'
FK_DIR: pathlib.Path = IMAGES / 'forward-kinematics'
IK_DIR: pathlib.Path = IMAGES / 'inverse-kinematics'
PNG_DIR: pathlib.Path | None = None

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
JOINT: str = '#f0a500'
GRIP: str = '#e05555'
INK: str = '#222222'
MUTED: str = '#777777'
GREEN: str = '#2b7d76'
PURPLE: str = '#8b4fa5'
REACH: str = '#dbe8f5'

L1: float = TWO_LINKS[0]
L2: float = TWO_LINKS[1]
TARGET: tuple[float, float] = (L1 * math.cos(math.radians(30.0)), 3.5)

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


def _figure(size: tuple[float, float]) -> tuple[Figure, Axes]:
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=size, facecolor='white')
    return fig, ax


def _arm(ax: Axes, pts: list[Point], color: str = LINK, width: float = 7,
         alpha: float = 1.0, joints: bool = True, gripper: bool = True) -> None:
    """Draw an arm through the given points: base, joints, gripper."""
    xs: list[float] = [p[0] for p in pts]
    ys: list[float] = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=width, solid_capstyle='round', alpha=alpha, zorder=2)
    if joints:
        ax.plot(xs[:-1], ys[:-1], 'o', color=JOINT, ms=11, alpha=alpha, zorder=4)
    if gripper:
        ax.plot([xs[-1]], [ys[-1]], 'o', color=GRIP, ms=9, alpha=alpha, zorder=4)


def _base(ax: Axes) -> None:
    """Draw the table the arm is bolted to, as a short hatched block under the base."""
    ax.plot([-0.45, 0.45], [-0.02, -0.02], color=INK, lw=1.4, zorder=1)
    for i in range(5):
        x0: float = -0.4 + 0.2 * i
        ax.plot([x0, x0 - 0.15], [-0.02, -0.22], color=INK, lw=0.9, zorder=1)


def _dashed(ax: Axes, start: Point, end: Point, color: str = GRID, lw: float = 1.0) -> None:
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=lw,
            ls=(0, (4, 3)), zorder=1)


def _arc(ax: Axes, centre: Point, radius: float, a1: float, a2: float,
         color: str = MUTED, lw: float = 1.3) -> None:
    """Draw an arc from angle a1 to a2 (radians), whichever way round is shorter."""
    lo, hi = min(a1, a2), max(a1, a2)
    ax.add_patch(Arc(centre, 2 * radius, 2 * radius, theta1=math.degrees(lo),
                     theta2=math.degrees(hi), color=color, lw=lw, zorder=3))


def _text(ax: Axes, x: float, y: float, text: str, color: str = INK, size: float = 10.5,
          ha: str = 'center', mono: bool = True, weight: str = 'normal',
          box: bool = False) -> None:
    ax.text(x, y, text, color=color, fontsize=size, ha=ha, va='center',
            family='monospace' if mono else None, weight=weight, zorder=6,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.9, 'pad': 2}
            if box else None)


def _title(fig: Figure, text: str) -> None:
    fig.suptitle(text, fontsize=13, weight='bold', y=0.98)


def _star(ax: Axes, point: Point, color: str = INK, size: float = 17) -> None:
    ax.plot([point[0]], [point[1]], marker='*', color=color, ms=size, zorder=5,
            markeredgecolor='white', markeredgewidth=0.8)


def _save(fig: Figure, folder: pathlib.Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / f'{name}.svg', bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{name}.png', bbox_inches='tight', pad_inches=0.3,
                    facecolor='white', dpi=110)
    plt.close(fig)


def _deg(values: tuple[float, ...]) -> list[float]:
    return [math.radians(v) for v in values]


# --------------------------------------------------------------------------
# forward kinematics
# --------------------------------------------------------------------------

POSES: dict[str, tuple[tuple[float, float], str]] = {
    'A': ((30.0, 60.0), LINK),
    'B': ((0.0, 90.0), GREEN),
    'C': ((90.0, -45.0), PURPLE),
}


def joint_vs_task_space() -> None:
    """Three poses, each shown as a dot among joint angles and as an arm on the table."""
    fig: Figure = plt.figure(figsize=(11.6, 5.2), facecolor='white')
    left: Axes = fig.add_axes((0.05, 0.1, 0.38, 0.75))
    right: Axes = fig.add_axes((0.52, 0.06, 0.46, 0.83))

    left.set_xlim(-30, 120)
    left.set_ylim(-75, 120)
    left.set_aspect('equal')
    left.set_xticks([0, 30, 60, 90])
    left.set_yticks([-45, 0, 45, 90])
    left.grid(color=GRID, lw=0.8)
    left.axhline(0, color=MUTED, lw=0.8)
    left.axvline(0, color=MUTED, lw=0.8)
    for spine in left.spines.values():
        spine.set_visible(False)
    left.tick_params(colors=MUTED, labelsize=9)
    left.set_xlabel('q1, joint 1 angle (degrees)', color=INK, fontsize=10)
    left.set_ylabel('q2, joint 2 angle (degrees)', color=INK, fontsize=10)
    left.set_title('Joint space: one dot per pose', color=INK, fontsize=11.5)
    for name, ((q1, q2), color) in POSES.items():
        left.plot([q1], [q2], 'o', color=color, ms=10, zorder=4)
        left.text(q1 + 6, q2 + 8, f'{name} ({q1:g}, {q2:g})', color=color, fontsize=10,
                  family='monospace', weight='bold')

    _axes(right, (-1.2, 6.2), (-0.6, 5.4))
    right.set_title('Task space: one arm per pose', color=INK, fontsize=11.5)
    _base(right)
    labels: dict[str, tuple[Point, str]] = {'A': ((0.25, 0.05), 'left'),
                                            'B': ((0.25, 0.0), 'left'),
                                            'C': ((-0.25, 0.1), 'right')}
    for name, ((q1, q2), color) in POSES.items():
        pts: list[Point] = points(_deg((q1, q2)), TWO_LINKS)
        _arm(right, pts, color=color, width=6)
        gx, gy = pts[-1]
        (dx, dy), ha = labels[name]
        _text(right, gx + dx, gy + dy, f'{name} ({gx:.3f}, {gy:.3f})', color=color,
              ha=ha, weight='bold', size=10)
    _title(fig, 'The same three poses, described two ways')
    _save(fig, FK_DIR, 'joint-vs-task-space')


def three_joint_pose() -> None:
    """Draw the three-joint arm, with the gripper's angle as the third number of its pose."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((7.0, 5.9))
    _axes(ax, (-1.0, 6.0), (-0.8, 5.2))
    _base(ax)
    q: list[float] = _deg((30.0, 60.0, -60.0))
    pts: list[Point] = points(q, THREE_LINKS)
    x, y, phi = forward(q, THREE_LINKS)
    _arm(ax, pts)

    # The gripper's angle, measured from a line parallel to the table.
    _dashed(ax, (x, y), (x + 1.4, y), color=MUTED)
    ax.annotate('', xy=(x + 1.1 * math.cos(phi), y + 1.1 * math.sin(phi)), xytext=(x, y),
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 2.0,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=5)
    _arc(ax, (x, y), 0.9, 0.0, phi, color=GRIP)
    _text(ax, x + 1.35, y + 0.28, 'φ = 30°', color=GRIP)

    # Each joint's own angle, measured from the link before it.
    _dashed(ax, (0, 0), (1.3, 0))
    _arc(ax, (0, 0), 1.0, 0.0, q[0])
    _text(ax, 1.55, 0.35, 'q1 = 30°')
    e1: Point = pts[1]
    _dashed(ax, e1, (e1[0] + 1.2 * math.cos(q[0]), e1[1] + 1.2 * math.sin(q[0])))
    _arc(ax, e1, 0.8, q[0], q[0] + q[1])
    _text(ax, e1[0] + 1.05, e1[1] + 0.95, 'q2 = 60°')
    e2: Point = pts[2]
    _dashed(ax, e2, (e2[0], e2[1] + 1.0))
    _arc(ax, e2, 0.6, q[0] + q[1] + q[2], q[0] + q[1])
    _text(ax, e2[0] - 0.95, e2[1] + 0.55, 'q3 = -60°')

    _text(ax, x + 0.2, y - 0.4, f'({x:.3f}, {y:.3f})', color=GRIP, ha='left')
    _text(ax, 2.5, -0.55, 'φ = q1 + q2 + q3 = 30° + 60° - 60° = 30°', color=INK)
    _title(fig, 'Three numbers for the gripper: x, y, and its angle φ')
    _save(fig, FK_DIR, 'three-joint-pose')


def _sweep(q1_range: tuple[float, float], q2_range: tuple[float, float],
           step: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    q1_deg: NDArray[np.float64] = np.arange(q1_range[0], q1_range[1] + 1e-9, step)
    q2_deg: NDArray[np.float64] = np.arange(q2_range[0], q2_range[1] + 1e-9, step)
    q1, q2 = np.meshgrid(np.radians(q1_deg), np.radians(q2_deg))
    x: NDArray[np.float64] = L1 * np.cos(q1) + L2 * np.cos(q1 + q2)
    y: NDArray[np.float64] = L1 * np.sin(q1) + L2 * np.sin(q1 + q2)
    return x.ravel(), y.ravel()


def workspace_ring() -> None:
    """Every place the gripper lands when both joints sweep all the way round."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((6.8, 6.6))
    _axes(ax, (-5.9, 5.9), (-6.3, 5.9))
    x, y = _sweep((-180.0, 179.0), (-180.0, 179.0), 3.0)
    ax.plot(x, y, '.', color=LINK, ms=1.3, alpha=0.35, zorder=1)
    for r in (L1 - L2, L1 + L2):
        ax.add_patch(Circle((0, 0), r, fill=False, color=INK, lw=1.2, ls=(0, (5, 3)), zorder=3))

    # At full stretch the gripper is L1 + L2 away. Fully folded, it is L1 - L2 away.
    stretched: list[Point] = points(_deg((40.0, 0.0)), TWO_LINKS)
    folded: list[Point] = points(_deg((200.0, 180.0)), TWO_LINKS)
    _arm(ax, stretched, width=6)
    _arm(ax, folded, color=GREEN, width=6)
    _text(ax, 3.35, 4.3, 'straight: 3 + 2 = 5 m', ha='left', color=LINK)
    _text(ax, -1.0, -2.2, 'folded: 3 - 2 = 1 m', color=GREEN, box=True)
    _text(ax, 0.0, -5.6, 'outer edge: 5 m from the base', color=INK)
    _text(ax, 0.2, -0.55, 'hole', color=MUTED, size=9)
    _title(fig, 'Sweep both joints all the way round: a ring')
    _save(fig, FK_DIR, 'workspace-ring')


def joint_limits() -> None:
    """Draw the ring in grey, and the part a limited arm can still reach in blue."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((6.8, 6.6))
    _axes(ax, (-5.9, 5.9), (-6.3, 5.9))
    x, y = _sweep((-180.0, 179.0), (-180.0, 179.0), 3.0)
    ax.plot(x, y, '.', color=GRID, ms=1.3, alpha=0.6, zorder=1)
    lx, ly = _sweep((-90.0, 90.0), (-150.0, 150.0), 2.0)
    ax.plot(lx, ly, '.', color=LINK, ms=1.4, alpha=0.45, zorder=2)
    reach: float = float(np.hypot(lx, ly).min())
    ax.add_patch(Circle((0, 0), reach, fill=False, color=INK, lw=1.2, ls=(0, (5, 3)), zorder=3))
    ax.plot([0], [0], 'o', color=JOINT, ms=10, zorder=4)
    _text(ax, 0.0, -2.4, f'new hole: {reach:.3f} m', color=INK, box=True)
    _text(ax, -4.0, 4.7, 'grey: lost to\nthe limits', color=MUTED, ha='left', mono=False)
    _text(ax, 2.6, 4.7, 'blue: still\nreachable', color=LINK, ha='left', mono=False)
    _text(ax, 0.0, -5.4, 'joint 1: -90° to +90°    joint 2: -150° to +150°', color=INK, size=10)
    _title(fig, 'Joint limits take a bite out of the ring')
    _save(fig, FK_DIR, 'joint-limits')


# --------------------------------------------------------------------------
# inverse kinematics
# --------------------------------------------------------------------------

def law_of_cosines() -> None:
    """Draw the triangle base, elbow, target, with each length and angle the solution uses."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((7.4, 6.4))
    _axes(ax, (-1.2, 5.6), (-0.9, 4.6))
    _base(ax)
    q1, q2 = two_joint_ik(TARGET[0], TARGET[1], L1, L2)[0]
    pts: list[Point] = points([q1, q2], TWO_LINKS)
    elbow: Point = pts[1]
    d: float = math.hypot(*TARGET)
    alpha: float = math.atan2(TARGET[1], TARGET[0])

    ax.fill([0, elbow[0], TARGET[0]], [0, elbow[1], TARGET[1]], color=REACH, zorder=0)
    _dashed(ax, (0, 0), TARGET, color=PURPLE, lw=1.6)
    _arm(ax, pts)
    _star(ax, TARGET, color=PURPLE, size=14)

    _text(ax, 2.1, 0.72, 'L1 = 3', color=LINK, ha='left')
    _text(ax, 3.05, 2.5, 'L2 = 2', color=LINK, ha='left')
    _text(ax, 0.75, 2.05, f'd = {d:.3f}', color=PURPLE)

    _dashed(ax, (0, 0), (1.7, 0))
    _arc(ax, (0, 0), 1.45, 0.0, alpha, color=PURPLE)
    _text(ax, 1.55, 0.2, f'α = {math.degrees(alpha):.2f}°', color=PURPLE, ha='left')
    _arc(ax, (0, 0), 0.75, q1, alpha, color=GREEN)
    _text(ax, 0.62, 0.72, 'β', color=GREEN)
    _arc(ax, (0, 0), 0.5, 0.0, q1)
    _text(ax, 0.72, 0.12, 'q1', size=9.5)

    ext: Point = (elbow[0] + 1.3 * math.cos(q1), elbow[1] + 1.3 * math.sin(q1))
    _dashed(ax, elbow, ext)
    _arc(ax, elbow, 0.55, q1, q1 + q2)
    _text(ax, elbow[0] + 0.8, elbow[1] + 0.5, 'q2 = 60°')
    _arc(ax, elbow, 0.35, q1 + q2, q1 + math.pi, color=GREEN)
    _text(ax, elbow[0] - 0.62, elbow[1] + 0.2, '120°', color=GREEN, size=9.5)

    _text(ax, 3.0, TARGET[1] + 0.35, f'target ({TARGET[0]:.3f}, {TARGET[1]:.3f})',
          color=PURPLE)
    _text(ax, 2.2, -0.65, 'q1 = α - β = 53.41° - 23.41° = 30°', color=INK)
    _title(fig, 'Three known lengths make one triangle')
    _save(fig, IK_DIR, 'law-of-cosines')


def two_answers() -> None:
    """Both joint-angle pairs that put the gripper on the same target."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((7.0, 5.9))
    _axes(ax, (-3.0, 5.2), (-0.8, 4.6))
    _base(ax)
    _dashed(ax, (0, 0), TARGET, color=MUTED, lw=1.2)
    answers = two_joint_ik(TARGET[0], TARGET[1], L1, L2)
    down, up = answers[0], answers[1]
    _arm(ax, points(list(down), TWO_LINKS), color=LINK)
    _arm(ax, points(list(up), TWO_LINKS), color=GREEN)
    _star(ax, TARGET, color=PURPLE, size=15)
    e_down: Point = points(list(down), TWO_LINKS)[1]
    e_up: Point = points(list(up), TWO_LINKS)[1]
    _text(ax, e_down[0] + 0.25, e_down[1] - 0.35,
          f'elbow down\nq1 = {math.degrees(down[0]):.2f}°, q2 = {math.degrees(down[1]):+.0f}°',
          color=LINK, ha='left', size=10)
    _text(ax, e_up[0] - 0.3, e_up[1] + 0.1,
          f'elbow up\nq1 = {math.degrees(up[0]):.2f}°, q2 = {math.degrees(up[1]):+.0f}°',
          color=GREEN, ha='right', size=10)
    _text(ax, TARGET[0] + 0.25, TARGET[1] + 0.35, f'({TARGET[0]:.3f}, {TARGET[1]:.1f})',
          color=PURPLE, ha='left')
    _title(fig, 'One target, two ways to reach it')
    _save(fig, IK_DIR, 'two-answers')


def reach_cases() -> None:
    """Targets outside, inside and on the edges of the ring, with their answer counts."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((7.4, 7.0))
    _axes(ax, (-6.6, 7.0), (-6.4, 6.9))
    ax.add_patch(Circle((0, 0), L1 + L2, color=REACH, zorder=0))
    ax.add_patch(Circle((0, 0), L1 - L2, color='white', zorder=0))
    for r in (L1 - L2, L1 + L2):
        ax.add_patch(Circle((0, 0), r, fill=False, color=MUTED, lw=1.0, zorder=1))
    ax.plot([0], [0], 'o', color=JOINT, ms=7, zorder=4)

    def at(r: float, deg: float) -> Point:
        return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))

    far: Point = at(6.0, 20.0)
    close: Point = at(0.6, 250.0)
    edge: Point = at(5.0, 70.0)
    inside: Point = at(4.0, 150.0)
    for answer in two_joint_ik(inside[0], inside[1], L1, L2):
        _arm(ax, points(list(answer), TWO_LINKS), color=GREEN, width=5, gripper=False)
    _arm(ax, points(_deg((70.0, 0.0)), TWO_LINKS), color=LINK, width=5, gripper=False)
    for point, color in ((far, GRIP), (close, GRIP), (edge, LINK), (inside, GREEN)):
        _star(ax, point, color=color, size=16)

    _text(ax, far[0] - 0.2, far[1] + 0.65, 'too far\n0 answers', color=GRIP, size=10)
    _text(ax, -1.2, -2.0, 'too close\n0 answers', color=GRIP, size=10)
    _dashed(ax, (-0.95, -1.55), (close[0] - 0.08, close[1] - 0.12), color=GRIP)
    _text(ax, edge[0] + 0.3, edge[1] + 0.5, 'at full stretch\n1 answer', color=LINK,
          ha='left', size=10)
    _text(ax, inside[0] - 0.3, inside[1] + 0.9, 'inside the ring\n2 answers', color=GREEN,
          size=10)
    _text(ax, 0.3, -5.8, 'only the distance from the base matters', color=MUTED, mono=False)
    _title(fig, 'How many answers a target has')
    _save(fig, IK_DIR, 'reach-cases')


def redundant() -> None:
    """Draw the three-joint arm reaching one point with the gripper at three angles."""
    fig: Figure
    axes: NDArray[np.object_]       # a NumPy array holding one Axes per panel
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.9), facecolor='white')
    x, y, _ = forward(_deg((30.0, 60.0, -60.0)), THREE_LINKS)
    for ax, phi in zip(axes, (0.0, 30.0, 90.0)):
        _axes(ax, (-0.8, 5.0), (-1.3, 5.2))
        _base(ax)
        q = three_joint_ik(x, y, math.radians(phi), THREE_LINKS)[0]
        _arm(ax, points(list(q), THREE_LINKS))
        a: float = math.radians(phi)
        ax.annotate('', xy=(x + 0.8 * math.cos(a), y + 0.8 * math.sin(a)), xytext=(x, y),
                    arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 2.0,
                                'shrinkA': 0, 'shrinkB': 0}, zorder=5)
        _star(ax, (x, y), color=PURPLE, size=12)
        ax.set_title(f'gripper angle φ = {phi:g}°', color=INK, fontsize=11.5)
        angles: str = ', '.join(f'{math.degrees(v):.1f}' for v in q)
        _text(ax, 2.1, -0.75, f'q = ({angles})', size=9.5)
    _title(fig, f'Three joints, one point ({x:.3f}, {y:.0f}), a different pose for every φ')
    fig.subplots_adjust(top=0.84)
    _save(fig, IK_DIR, 'three-joint-choices')


def numerical() -> None:
    """Draw the arm at each step of numerical inverse kinematics, from guess to target."""
    fig: Figure
    ax: Axes
    fig, ax = _figure((7.4, 6.0))
    _axes(ax, (-1.0, 6.4), (-1.9, 4.6))
    _base(ax)
    history = numerical_ik(TARGET[0], TARGET[1], _deg((0.0, 30.0)), TWO_LINKS)
    shown = history[:5]
    shades: list[str] = ['#d7e4f2', '#b0cbe6', '#86aed8', '#5b92ca', LINK]
    offsets: list[tuple[Point, str]] = [((0.15, -0.35), 'left'), ((0.2, 0.0), 'left'),
                                        ((0.3, 0.05), 'left'), ((-0.25, 0.0), 'right'),
                                        ((0.25, 0.2), 'left')]
    for i, ((joints, miss), shade) in enumerate(zip(shown, shades)):
        pts: list[Point] = points(joints, TWO_LINKS)
        _arm(ax, pts, color=shade, width=5, joints=(i == 0 or i == len(shown) - 1),
             gripper=False)
        ax.plot([pts[-1][0]], [pts[-1][1]], 'o', color=shade, ms=8, zorder=4,
                markeredgecolor=INK, markeredgewidth=0.6)
        (dx, dy), ha = offsets[i]
        if i < len(shown) - 1:
            _text(ax, pts[-1][0] + dx, pts[-1][1] + dy, f'step {i}: miss {miss:.3f} m',
                  color=INK, ha=ha, size=9.5)
    _star(ax, TARGET, color=PURPLE, size=15)
    _text(ax, TARGET[0] + 0.3, TARGET[1] + 0.3, 'target', color=PURPLE, ha='left', size=10)
    _text(ax, 2.6, -1.35, 'start: q1 = 0°, q2 = 30°. Each step turns both joints a little.',
          color=MUTED, mono=False)
    _title(fig, 'Guess, measure the miss, correct, repeat')
    _save(fig, IK_DIR, 'numerical-steps')


FIGURES: tuple[Callable[[], None], ...] = (
    joint_vs_task_space, three_joint_pose, workspace_ring, joint_limits,
    law_of_cosines, two_answers, reach_cases, redundant, numerical)

if __name__ == '__main__':
    if '--png' in sys.argv:
        PNG_DIR = pathlib.Path(sys.argv[sys.argv.index('--png') + 1])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    for figure in FIGURES:
        figure()
    print(f'wrote {len(FIGURES)} diagrams to {IMAGES}')
