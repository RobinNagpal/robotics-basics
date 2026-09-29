"""Generate the diagrams used in docs/01_robotics-intro/05_arm-types/.

Each document's pictures go to a folder named after it, under
docs/images/arm-types/.

Run with:  pixi run python ../docs/diagrams/arm_types.py

The flat arms are drawn from code/src/arm_types/joints.py, and the UR5e is drawn
from the forward kinematics in code/src/arm_types/ur5e.py, so every position in
a picture is the same number the documents quote.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Polygon, Rectangle, Wedge  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d import proj3d  # noqa: E402
from mpl_toolkits.mplot3d.axes3d import Axes3D  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'code' / 'src' / 'arm_types'))
# Imported after the sys.path line above, which flake8's import rules cannot see.
from joints import chain_points, two_joint_solutions  # noqa: E402,I100,I202
from ur5e import forward, solve_many, tool, WORK_POSE_DEG  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'arm-types'
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


def _link(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = LINK,
          width: float = 7, z: int = 2) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width, solid_capstyle='round',
            zorder=z)


def _hinge(ax: Axes, p: tuple[float, float], size: float = 13, color: str = JOINT) -> None:
    """Draw a joint that turns about an axis pointing out of the page."""
    ax.plot([p[0]], [p[1]], 'o', color=color, ms=size, zorder=4)
    ax.plot([p[0]], [p[1]], 'o', color=INK, ms=size * 0.25, zorder=5)


def _twist(ax: Axes, p: tuple[float, float], angle: float, length: float = 0.5,
           width: float = 0.3, color: str = JOINT) -> None:
    """Draw a joint that turns about an axis lying in the page, along that axis."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    hl: float = length / 2
    hw: float = width / 2
    corners = [(p[0] + dx * c - dy * s, p[1] + dx * s + dy * c)
               for dx, dy in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
    ax.add_patch(Polygon(corners, closed=True, facecolor=color, edgecolor=INK, lw=0.8,
                         zorder=4))
    ext: float = hl + 0.25
    ax.plot([p[0] - ext * c, p[0] + ext * c], [p[1] - ext * s, p[1] + ext * s],
            color=INK, lw=0.8, ls=(0, (6, 2, 1, 2)), zorder=5)


def _slide(ax: Axes, p: tuple[float, float], angle: float, length: float = 0.6,
           width: float = 0.34) -> None:
    """Draw a joint that slides along the page, as a sleeve with a double arrow."""
    _twist(ax, p, angle, length, width, color=SLIDE)
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    d: float = length / 2 + 0.35
    ax.annotate('', xy=(p[0] + d * c, p[1] + d * s), xytext=(p[0] - d * c, p[1] - d * s),
                arrowprops={'arrowstyle': '<|-|>', 'color': SLIDE, 'lw': 1.6,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=6)


def _gripper(ax: Axes, p: tuple[float, float], angle: float, size: float = 0.35) -> None:
    """Two short fingers opening in the direction the gripper points."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    nx: float = -s
    ny: float = c
    for side in (1, -1):
        root = (p[0] + side * size * 0.6 * nx, p[1] + side * size * 0.6 * ny)
        tip = (root[0] + size * c, root[1] + size * s)
        ax.plot([p[0], root[0], tip[0]], [p[1], root[1], tip[1]], color=GRIP, lw=3,
                solid_capstyle='round', zorder=3)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=7)


def _title(ax: Axes, x: float, y: float, text: str) -> None:
    ax.text(x, y, text, fontsize=13, ha='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', color=MUTED)


def _floor(ax: Axes, x0: float, x1: float, y: float = 0.0) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.2, zorder=1)
    for x in np.arange(x0 + 0.1, x1, 0.3):
        ax.plot([x, x - 0.15], [y, y - 0.15], color=GRID, lw=1.0, zorder=1)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _pt(row: NDArray[np.float64]) -> tuple[float, float]:
    return (float(row[0]), float(row[1]))


# --------------------------------------------------------------------------
# 01_joints-and-degrees-of-freedom
# --------------------------------------------------------------------------

JOINTS_DOC: str = 'joints-and-degrees-of-freedom'


def joint_types() -> None:
    """Draw a turning joint and a sliding joint, each shown at two settings."""
    fig, (left, right) = _panels(2, (10.4, 4.4))

    _axes(left, (-1.6, 3.6), (-1.0, 3.4))
    _floor(left, -0.7, 1.3)
    _link(left, (0.3, 0.0), (0.3, 0.5), color=MUTED, width=10)
    for angle, color in ((math.radians(20), LINK_PALE), (math.radians(65), LINK)):
        end = (0.3 + 2.6 * math.cos(angle), 0.5 + 2.6 * math.sin(angle))
        _link(left, (0.3, 0.5), end, color=color)
    left.add_patch(Arc((0.3, 0.5), 2.4, 2.4, theta1=20, theta2=65, color=MUTED, lw=1.3,
                       zorder=3))
    _label(left, 1.75, 1.35, 'angle', color=MUTED)
    _hinge(left, (0.3, 0.5))
    _title(left, 1.0, 3.1, 'Revolute (turning) joint')
    _caption(left, 1.0, -0.65, 'The link swings round the pin.\nIts setting is an angle.')

    _axes(right, (-1.6, 3.6), (-1.0, 3.4))
    _floor(right, -1.0, 3.2)
    right.add_patch(Rectangle((-0.6, 0.0), 0.5, 1.0, facecolor=MUTED, zorder=2))
    _link(right, (-0.1, 0.56), (2.9, 0.56), color=LINK_PALE, z=2)
    _link(right, (-0.1, 0.56), (1.4, 0.56), color=LINK, z=3)
    right.add_patch(Rectangle((-0.35, 0.2), 0.7, 0.72, facecolor=SLIDE, edgecolor=INK,
                              lw=0.8, zorder=4))
    right.annotate('', xy=(2.9, 1.15), xytext=(1.4, 1.15),
                   arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.3})
    for x in (1.4, 2.9):
        right.plot([x, x], [0.75, 1.25], color=MUTED, lw=0.8, ls=':')
    _label(right, 2.15, 1.45, 'distance', color=MUTED)
    _title(right, 1.0, 3.1, 'Prismatic (sliding) joint')
    _caption(right, 1.0, -0.65, 'The link slides in and out of a sleeve.\n'
             'Its setting is a distance.')
    _save(fig, JOINTS_DOC, 'joint-types.svg')


def _draw_chain(ax: Axes, q: list[float], color: str = LINK, joints: bool = True,
                gripper: bool = True) -> None:
    pts: NDArray[np.float64] = chain_points(q)
    for a, b in zip(pts[:-1], pts[1:]):
        _link(ax, _pt(a), _pt(b), color=color, width=6)
    if joints:
        for p in pts[:-1]:
            _hinge(ax, _pt(p), size=11)
        if gripper:
            _gripper(ax, _pt(pts[-1]), math.radians(sum(q)), size=0.22)


def the_chain() -> None:
    """Show that joint 1 carries everything after it, and joint 3 moves only the end."""
    fig, axes = _panels(2, (11.0, 5.2))
    start: list[float] = [30.0, 60.0, -60.0]
    cases = (([50.0, 60.0, -60.0], 'Turn joint 1 by 20°', 0,
              'Everything after joint 1 moves.\nThe gripper moves 1.838 m.'),
             ([30.0, 60.0, -40.0], 'Turn joint 3 by 20°', 2,
              'Only the last link moves.\nThe gripper moves 0.347 m.'))
    for ax, (q, title, which, caption) in zip(axes, cases):
        _axes(ax, (-1.2, 5.0), (-1.4, 5.8))
        _floor(ax, -0.9, 1.0)
        _draw_chain(ax, start, color=LINK_PALE, joints=False)
        _draw_chain(ax, q)
        pts = chain_points(q)
        j = _pt(pts[which])
        ax.plot([j[0]], [j[1]], 'o', ms=22, mfc='none', mec=GRIP, mew=2, zorder=6)
        label_at = (j[0] + 0.95, j[1] - 0.25) if which == 0 else (j[0] + 1.05, j[1] - 0.2)
        _label(ax, *label_at, f'joint {which + 1}', color=GRIP)
        _title(ax, 1.9, 5.45, title)
        _caption(ax, 1.9, -1.2, caption)
    axes[0].plot([], [], color=LINK_PALE, lw=6, label='before')
    axes[0].plot([], [], color=LINK, lw=6, label='after')
    axes[0].legend(loc='center right', frameon=False, fontsize=10)
    _save(fig, JOINTS_DOC, 'the-chain.svg')


def angles_add() -> None:
    """Each joint's angle is measured from the link before it, so the directions add up."""
    fig, ax = plt.subplots(figsize=(7.0, 5.4), facecolor='white')
    _axes(ax, (-1.2, 5.6), (-1.2, 5.0))
    q: list[float] = [30.0, 60.0, -60.0]
    pts = chain_points(q)
    _floor(ax, -0.9, 1.2)
    _draw_chain(ax, q)
    # Dashed line carrying on the direction of the link before each joint.
    heading_deg = 0.0
    for i, (p, angle) in enumerate(zip(pts[:-1], q)):
        x, y = _pt(p)
        ext = 1.1
        ax.plot([x, x + ext * math.cos(math.radians(heading_deg))],
                [y, y + ext * math.sin(math.radians(heading_deg))],
                color=GRID, lw=1.2, ls=(0, (4, 3)), zorder=1)
        lo, hi = sorted((heading_deg, heading_deg + angle))
        r = 0.75 if i == 0 else 0.6
        ax.add_patch(Arc((x, y), 2 * r, 2 * r, theta1=lo, theta2=hi, color=MUTED, lw=1.3,
                         zorder=3))
        at = ((x + 1.35, y + 0.2), (x + 0.95, y + 0.75), (x - 0.85, y + 0.55))[i]
        _label(ax, at[0], at[1], f'q{i + 1} = {angle:+.0f}°', size=10, color=INK)
        heading_deg += angle
    notes = ('link 1 points at 30°', 'link 2 points at 30° + 60° = 90°',
             'link 3 points at 90° − 60° = 30°')
    for k, text in enumerate(notes):
        _label(ax, 5.5, 1.3 - 0.45 * k, text, size=10, ha='right', color=MUTED)
    _title(ax, 2.2, 4.75, 'Each angle is measured from the link before it')
    _save(fig, JOINTS_DOC, 'angles-add.svg')


def joint_limits() -> None:
    """Draw a joint that can turn from -150° to +150°, and where it stops."""
    fig, ax = plt.subplots(figsize=(6.0, 5.2), facecolor='white')
    _axes(ax, (-3.0, 3.0), (-2.9, 3.0))
    ax.add_patch(Wedge((0, 0), 2.2, -150, 150, facecolor='#e8f1e8', edgecolor='none',
                       zorder=1))
    ax.add_patch(Wedge((0, 0), 2.2, 150, 210, facecolor='#f6dede', edgecolor='none',
                       zorder=1))
    for a in (150, -150):
        ax.plot([0, 2.2 * math.cos(math.radians(a))], [0, 2.2 * math.sin(math.radians(a))],
                color=GRIP, lw=1.5, zorder=2)
    _link(ax, (0, 0), (2.0 * math.cos(math.radians(60)), 2.0 * math.sin(math.radians(60))))
    _link(ax, (0, 0), (2.0 * math.cos(math.radians(150)), 2.0 * math.sin(math.radians(150))),
          color=LINK_PALE)
    _hinge(ax, (0, 0), size=16)
    _label(ax, 1.55, 0.2, 'allowed:\n−150° to +150°', color=SLIDE)
    _label(ax, -2.55, 0.0, 'not\nallowed', color=GRIP)
    _label(ax, 1.45, 2.05, 'asked 60°: goes to 60°', size=9, ha='left')
    _label(ax, -1.75, 1.35, 'asked 170°:\nstops at 150°', size=9, ha='right')
    _title(ax, 0.0, 2.75, 'A joint has limits')
    _caption(ax, 0.0, -2.65, 'The red wedge is where the cables and the housing are.')
    _save(fig, JOINTS_DOC, 'joint-limits.svg')


def _pointing(ax: Axes, p: tuple[float, float], angle: float, color: str) -> None:
    """Draw an arrow from the tip in the direction the gripper points."""
    end = (p[0] + 0.8 * math.cos(angle), p[1] + 0.8 * math.sin(angle))
    ax.annotate('', xy=end, xytext=p, arrowprops={'arrowstyle': '-|>', 'color': color,
                                                  'lw': 2.0, 'shrinkA': 0, 'shrinkB': 0},
                zorder=6)


def two_vs_three() -> None:
    """Two joints can reach the handle but cannot choose the gripper's angle; three can."""
    fig, axes = _panels(2, (11.0, 5.4))
    handle = (3.0, 2.0)
    for ax in axes:
        _axes(ax, (-1.2, 5.2), (-1.2, 5.6))
        _floor(ax, -0.9, 4.8)
        ax.plot([handle[0]], [handle[1]], marker='*', ms=16, color=GRIP, zorder=8)
        ax.annotate('', xy=(3.9, 1.9), xytext=(3.9, 2.9),
                    arrowprops={'arrowstyle': '-|>', 'color': SLIDE, 'lw': 2.0}, zorder=7)
        _label(ax, 4.05, 2.4, 'must\npoint\ndown', size=9, ha='left', color=SLIDE)
    # Two joints: both answers.
    ax = axes[0]
    for (q1, q2), color in zip(two_joint_solutions(3.0, 2.0, 3.0, 2.0), (LINK, '#7a5cc0')):
        pts = chain_points([q1, q2], (3.0, 2.0))
        for a, b in zip(pts[:-1], pts[1:]):
            _link(ax, _pt(a), _pt(b), color=color, width=5)
        for p in pts[:-1]:
            _hinge(ax, _pt(p), size=10)
        _pointing(ax, _pt(pts[-1]), math.radians(q1 + q2), color)
    _label(ax, 3.35, 4.2, 'answer 1:\ngripper points at 90°', size=9, ha='left', color=LINK)
    _label(ax, 1.2, -0.6, 'answer 2: gripper points at −22.6°', size=9, color='#7a5cc0')
    _title(ax, 2.0, 5.3, 'Two joints: the tip gets there,')
    _label(ax, 2.0, 4.9, 'but the gripper points where it must', size=11, color=INK)
    # Three joints: one answer shown, gripper straight down.
    ax = axes[1]
    q1, q2 = two_joint_solutions(3.0, 3.0, 3.0, 2.0)[0]
    q = [q1, q2, -90.0 - q1 - q2]
    _draw_chain(ax, q, gripper=False)
    _pointing(ax, handle, math.radians(-90.0), LINK)
    _label(ax, 1.2, 3.9, 'gripper points\nstraight down (−90°)', size=9, color=SLIDE)
    _title(ax, 2.0, 5.3, 'Three joints: the tip gets there,')
    _label(ax, 2.0, 4.9, 'and the gripper points where you choose', size=11, color=INK)
    for ax in axes:
        _caption(ax, 2.0, -1.15,
                 'red star: the cup handle\narrow at the tip: where the gripper points')
    _save(fig, JOINTS_DOC, 'two-vs-three-joints.svg')


def six_numbers() -> None:
    """In 3D a gripper needs three numbers for where it is and three for which way it faces."""
    fig = plt.figure(figsize=(7.4, 6.2), facecolor='white')
    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_facecolor('white')
    p = np.array([0.6, 0.5, 0.45])
    # Floor axes.
    for d, color, name in ((np.array([1, 0, 0]), AXIS_X, 'x'), (np.array([0, 1, 0]), AXIS_Y, 'y'),
                           (np.array([0, 0, 1]), AXIS_Z, 'z')):
        end = 0.95 * d
        ax.plot([0, end[0]], [0, end[1]], [0, end[2]], color=color, lw=1.5)
        ax.text(*(1.02 * d), name, color=color, fontsize=11)
    # Dashed drop lines to show the three position numbers.
    ax.plot([p[0], p[0]], [p[1], p[1]], [0, p[2]], color=MUTED, lw=1, ls=':')
    ax.plot([0, p[0]], [p[1], p[1]], [0, 0], color=MUTED, lw=1, ls=':')
    ax.plot([p[0], p[0]], [0, p[1]], [0, 0], color=MUTED, lw=1, ls=':')
    ax.text(p[0] + 0.03, 0.0, 0.03, 'x', color=MUTED, fontsize=10)
    ax.text(-0.08, p[1], 0.03, 'y', color=MUTED, fontsize=10)
    ax.text(p[0] + 0.03, p[1], p[2] / 2, 'z', color=MUTED, fontsize=10)
    # The gripper's own axes, tilted, and a circle round each one for the turn about it.
    tilt = math.radians(30)
    rot = np.array([[math.cos(tilt), 0, math.sin(tilt)], [0, 1, 0],
                    [-math.sin(tilt), 0, math.cos(tilt)]])
    names = ('roll', 'pitch', 'yaw')
    for k, color in enumerate((AXIS_X, AXIS_Y, AXIS_Z)):
        d = rot[:, k]
        end = p + 0.32 * d
        ax.plot([p[0], end[0]], [p[1], end[1]], [p[2], end[2]], color=color, lw=2.5)
        u = rot[:, (k + 1) % 3]
        v = rot[:, (k + 2) % 3]
        t = np.linspace(0.2, 1.8 * math.pi, 50)
        centre = p + 0.22 * d
        ring = centre[:, None] + 0.06 * (np.outer(u, np.cos(t)) + np.outer(v, np.sin(t)))
        ax.plot(ring[0], ring[1], ring[2], color=color, lw=1.2)
        lab = p + 0.42 * d
        ax.text(lab[0], lab[1], lab[2], names[k], color=color, fontsize=10)
    ax.scatter([p[0]], [p[1]], [p[2]], color=GRIP, s=60, depthshade=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_zlim(0, 1)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    fig.text(0.5, 0.93, 'Six numbers place a gripper in 3D', ha='center', fontsize=13,
             weight='bold', color=INK)
    fig.text(0.5, 0.07, 'where it is: x, y, z (dotted)   ·   which way it faces: '
             'roll, pitch, yaw (rings)', ha='center', fontsize=10, color=MUTED)
    _save(fig, JOINTS_DOC, 'six-numbers.svg')


# --------------------------------------------------------------------------
# 02_five-common-arms
# --------------------------------------------------------------------------

ARMS_DOC: str = 'five-common-arms'


def _legend(ax: Axes, x: float, y: float) -> None:
    """Explain the three joint symbols, one per row."""
    _hinge(ax, (x, y), size=10)
    _label(ax, x + 0.55, y, 'turns about an axis out of the page', size=8, ha='left',
           color=MUTED)
    _twist(ax, (x, y - 0.4), 0.0, length=0.3, width=0.2)
    _label(ax, x + 0.55, y - 0.4, 'turns about the dashed line', size=8, ha='left',
           color=MUTED)
    _slide(ax, (x, y - 0.8), 0.0, length=0.2, width=0.18)
    _label(ax, x + 0.55, y - 0.8, 'slides along the arrow', size=8, ha='left', color=MUTED)


def six_joint_schematic() -> None:
    """Draw a six-joint arm from the side: three joints place the wrist, three point."""
    fig, ax = plt.subplots(figsize=(8.4, 5.6), facecolor='white')
    _axes(ax, (-1.6, 7.0), (-1.2, 5.2))
    _floor(ax, -1.2, 1.2)
    base = (0.0, 0.0)
    j1 = (0.0, 0.55)
    j2 = (0.0, 1.2)
    j3 = (1.9, 3.3)
    j4 = (3.3, 3.3)
    j5 = (4.4, 3.3)
    j6 = (4.4, 2.55)
    tip = (4.4, 1.95)
    _link(ax, base, j2, color=MUTED, width=12)
    _link(ax, j2, j3)
    _link(ax, j3, j5)
    _link(ax, j5, tip)
    _twist(ax, j1, math.pi / 2)
    _hinge(ax, j2)
    _hinge(ax, j3)
    _twist(ax, j4, 0.0)
    _hinge(ax, j5)
    _twist(ax, j6, math.pi / 2, length=0.4)
    _gripper(ax, tip, -math.pi / 2, size=0.3)
    labels = ((j1, (-0.95, 0.55), 'J1 base'), (j2, (-0.95, 1.35), 'J2 shoulder'),
              (j3, (1.1, 3.75), 'J3 elbow'), (j4, (3.3, 3.85), 'J4 wrist 1'),
              (j5, (5.35, 3.55), 'J5 wrist 2'), (j6, (5.35, 2.55), 'J6 wrist 3'))
    for _, at, text in labels:
        color = LINK if text[1] in '123' else WRIST
        _label(ax, at[0], at[1], text, size=10, color=color, weight='bold')
    _label(ax, 2.3, 1.5, 'J1, J2, J3: put the wrist\nin the right place', size=9, color=LINK)
    _label(ax, 5.85, 1.5, 'J4, J5, J6: point\nthe gripper', size=9, color=WRIST)
    _title(ax, 2.7, 4.85, 'Six-joint arm, industrial layout (FANUC, ABB, KUKA)')
    _legend(ax, 2.9, 0.6)
    _save(fig, ARMS_DOC, 'six-joint.svg')


def seven_joint_schematic() -> None:
    """Draw a seven-joint arm: the extra joint lets the elbow move, the hand stays still."""
    fig, ax = plt.subplots(figsize=(8.4, 5.8), facecolor='white')
    _axes(ax, (-1.6, 7.0), (-1.2, 5.4))
    _floor(ax, -1.2, 1.2)
    j1 = (0.0, 0.55)
    j2 = (0.0, 1.2)
    wrist = (3.6, 1.2)
    hand = (4.5, 1.2)
    for elbow, color in (((1.2, 3.55), LINK_PALE), ((2.3, 3.75), LINK)):
        _link(ax, j2, elbow, color=color)
        _link(ax, elbow, wrist, color=color)
    elbow = (2.3, 3.75)
    j3 = ((j2[0] + elbow[0]) / 2, (j2[1] + elbow[1]) / 2)
    j5 = ((elbow[0] + wrist[0]) / 2, (elbow[1] + wrist[1]) / 2)
    ang_up = math.atan2(elbow[1] - j2[1], elbow[0] - j2[0])
    ang_down = math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0])
    _link(ax, (0.0, 0.0), j2, color=MUTED, width=12)
    _link(ax, wrist, hand)
    _twist(ax, j1, math.pi / 2)
    _hinge(ax, j2)
    _twist(ax, j3, ang_up)
    _hinge(ax, elbow)
    _twist(ax, j5, ang_down)
    _hinge(ax, wrist)
    _twist(ax, (4.05, 1.2), 0.0, length=0.35)
    _gripper(ax, hand, 0.0, size=0.3)
    ax.add_patch(Arc((1.75, 3.65), 1.6, 0.7, theta1=0, theta2=180, color=GRIP, lw=1.5,
                     ls='--', zorder=3))
    _label(ax, 1.75, 4.3, 'the elbow can swing', size=9, color=GRIP)
    labels = (((-0.95, 0.55), 'J1'), ((-0.75, 1.3), 'J2'), ((j3[0] - 0.55, j3[1] + 0.1), 'J3'),
              ((elbow[0] + 0.6, elbow[1] + 0.05), 'J4'), ((j5[0] + 0.5, j5[1] + 0.25), 'J5'),
              ((wrist[0], wrist[1] - 0.5), 'J6'), ((4.05, 1.75), 'J7'))
    for at, text in labels:
        _label(ax, at[0], at[1], text, size=10, weight='bold',
               color=GRIP if text == 'J3' else INK)
    _label(ax, 5.1, 2.9, 'J3 is the extra joint.\nThe shoulder and the hand\n'
           'stay where they are,\nand the elbow moves.', size=9, ha='left', color=INK)
    _title(ax, 2.7, 5.05, 'Seven-joint arm (for example Franka Research 3, KUKA LBR iiwa)')
    _legend(ax, 5.1, 0.6)
    _save(fig, ARMS_DOC, 'seven-joint.svg')


def scara_schematic() -> None:
    """SCARA from the side and from above: two turns in a flat plane, then up and down."""
    fig, (side, top) = _panels(2, (11.2, 5.0))
    _axes(side, (-1.4, 5.0), (-1.3, 4.4))
    _floor(side, -1.0, 4.8)
    j1 = (0.0, 2.8)
    j2 = (2.2, 2.8)
    end = (3.9, 2.8)
    _link(side, (0.0, 0.0), (0.0, 2.6), color=MUTED, width=16)
    _link(side, j1, j2)
    _link(side, j2, end)
    _twist(side, j1, math.pi / 2)
    _twist(side, j2, math.pi / 2)
    _slide(side, (3.9, 2.3), math.pi / 2, length=0.5, width=0.28)
    _link(side, (3.9, 2.8), (3.9, 1.05), color=LINK, width=4)
    _twist(side, (3.9, 1.05), math.pi / 2, length=0.35, width=0.26)
    _gripper(side, (3.9, 0.75), -math.pi / 2, size=0.25)
    _label(side, -0.75, 3.1, 'J1', weight='bold')
    _label(side, 2.2, 3.55, 'J2', weight='bold')
    _label(side, 4.3, 2.3, 'J3 up/down', weight='bold', color=SLIDE, ha='left')
    _label(side, 4.55, 1.05, 'J4', weight='bold')
    _title(side, 1.8, 4.1, 'From the side')
    _caption(side, 1.8, -0.95, 'J1 and J2 turn about upright axes, so the arm\n'
             'always stays level. J3 lowers the tool. J4 spins it.')

    _axes(top, (-4.4, 4.4), (-4.9, 4.6))
    top.add_patch(Wedge((0, 0), 3.95, -132, 132, width=3.45, facecolor='#eef4fb',
                        edgecolor='none', zorder=1))
    for (a1, a2), color in (((20.0, 60.0), LINK), ((-60.0, 70.0), LINK_PALE)):
        p1 = (2.25 * math.cos(math.radians(a1)), 2.25 * math.sin(math.radians(a1)))
        p2 = (p1[0] + 1.75 * math.cos(math.radians(a1 + a2)),
              p1[1] + 1.75 * math.sin(math.radians(a1 + a2)))
        _link(top, (0, 0), p1, color=color)
        _link(top, p1, p2, color=color)
        _hinge(top, p1, size=10)
        top.plot([p2[0]], [p2[1]], 'o', color=GRIP, ms=8, zorder=5)
    _hinge(top, (0, 0), size=13)
    _label(top, 0.9, -4.25, 'shaded: where the tool can be', size=9, color=MUTED)
    _title(top, 0.0, 4.3, 'From above')
    _caption(top, 0.0, -4.95, 'J1 and J2 move the tool anywhere on the floor plan.')
    _save(fig, ARMS_DOC, 'scara.svg')


def _obl(x: float, y: float, z: float) -> tuple[float, float]:
    """Draw a 3D point on the page, with depth (y) going up and to the right."""
    return (x + 0.45 * y, z + 0.3 * y)


def cartesian_schematic() -> None:
    """Draw a gantry: three sliding joints, one along each of x, y and z."""
    fig, ax = plt.subplots(figsize=(8.0, 5.8), facecolor='white')
    _axes(ax, (-1.0, 7.6), (-1.5, 5.2))
    w, d, h = 5.0, 3.0, 3.2
    floor = [_obl(0, 0, 0), _obl(w, 0, 0), _obl(w, d, 0), _obl(0, d, 0)]
    ax.add_patch(Polygon(floor, closed=True, facecolor='#f3f3f3', edgecolor=GRID, zorder=0))
    for x, y in ((0, 0), (w, 0), (0, d), (w, d)):
        _link(ax, _obl(x, y, 0), _obl(x, y, h), color=MUTED, width=4, z=1)
    for y in (0, d):
        _link(ax, _obl(0, y, h), _obl(w, y, h), color=MUTED, width=4, z=1)
    # The bridge (moves along x), the carriage on it (moves along y), the quill (z).
    bx, cy, qz = 2.8, 1.4, 1.2
    _link(ax, _obl(bx, 0, h), _obl(bx, d, h), color=LINK, width=7, z=2)
    _slide(ax, _obl(bx, 0, h), 0.0, length=0.5, width=0.3)
    carriage = _obl(bx, cy, h)
    ang_y = math.atan2(0.3, 0.45)
    _slide(ax, carriage, ang_y, length=0.5, width=0.32)
    _link(ax, carriage, _obl(bx, cy, qz), color=LINK, width=5, z=2)
    _slide(ax, _obl(bx, cy, h - 0.9), math.pi / 2, length=0.45, width=0.28)
    _gripper(ax, _obl(bx, cy, qz), -math.pi / 2, size=0.28)
    _label(ax, _obl(bx, 0, h)[0] - 0.3, _obl(bx, 0, h)[1] - 0.45, 'J1: along x',
           weight='bold', color=SLIDE)
    _label(ax, carriage[0] + 0.75, carriage[1] + 0.05, 'J2: along y', weight='bold',
           color=SLIDE, ha='left')
    zl = _obl(bx, cy, h - 0.9)
    _label(ax, zl[0] + 1.2, zl[1], 'J3: along z', weight='bold', color=SLIDE)
    _title(ax, 3.3, 4.9, 'Cartesian (gantry) arm: three sliding joints')
    _caption(ax, 3.3, -0.9, 'Each joint moves the tool along one straight axis.\n'
             'It reaches every point inside the box, and nothing outside it.')
    _save(fig, ARMS_DOC, 'cartesian.svg')


def delta_schematic() -> None:
    """Draw a delta: three motors on a fixed plate, three light arms meeting at one plate."""
    fig, ax = plt.subplots(figsize=(8.0, 5.8), facecolor='white')
    _axes(ax, (-3.6, 4.4), (-2.4, 4.4))
    ax.add_patch(Rectangle((-2.2, 2.9), 4.4, 0.45, facecolor=MUTED, zorder=1))
    _label(ax, 0.0, 3.62, 'fixed top plate (on the frame or ceiling)', size=9, color=MUTED)
    plate_y = 0.0
    motors = ((-1.6, 2.7), (1.6, 2.7))
    elbows = ((-2.7, 1.5), (2.7, 1.5))
    joints_low = ((-0.45, plate_y), (0.45, plate_y))
    for m, e, lo in zip(motors, elbows, joints_low):
        _link(ax, m, e, color=LINK, width=7)
        for off in (-0.12, 0.12):
            ax.plot([e[0], lo[0]], [e[1] + off, lo[1] + off], color=LINK, lw=2, zorder=2)
        _hinge(ax, m, size=13)
    # The third arm, behind the other two, drawn paler.
    _link(ax, (0.0, 2.7), (0.35, 1.2), color=LINK_PALE, width=6, z=1)
    for off in (-0.12, 0.12):
        ax.plot([0.35, 0.0], [1.2 + off, plate_y + off], color=LINK_PALE, lw=2, zorder=1)
    ax.add_patch(Rectangle((-0.6, plate_y - 0.18), 1.2, 0.3, facecolor=JOINT, edgecolor=INK,
                           lw=0.8, zorder=4))
    _gripper(ax, (0.0, plate_y - 0.2), -math.pi / 2, size=0.3)
    _label(ax, -2.3, 2.6, 'motor 1', size=9, weight='bold')
    _label(ax, 2.35, 2.6, 'motor 2', size=9, weight='bold')
    _label(ax, 0.45, 2.2, 'motor 3\n(behind)', size=9, color=MUTED, ha='left')
    _label(ax, -3.0, 0.7, 'thin rods in\npairs', size=9, color=LINK)
    _label(ax, 1.5, -0.55, 'small plate: always\nstays level', size=9, ha='left')
    _title(ax, 0.4, 4.15, 'Delta (parallel) arm, for example ABB FlexPicker')
    _caption(ax, 0.4, -2.0, 'The three arms work side by side, not one after another.\n'
             'All three motors stay on the frame, so the moving parts are light.')
    _save(fig, ARMS_DOC, 'delta.svg')


# --------------------------------------------------------------------------
# 03_the-six-joint-arm
# --------------------------------------------------------------------------

SIX_DOC: str = 'the-six-joint-arm'
JOINT_LABELS: tuple[str, ...] = ('J1 base', 'J2 shoulder', 'J3 elbow', 'J4 wrist 1',
                                 'J5 wrist 2', 'J6 wrist 3')


def _ax3d(fig: Figure, pos: int | tuple[int, int, int], elev: float = 22,
          azim: float = -60,
          box: tuple[float, float, float, float] = (-0.9, 0.3, -0.6, 0.0),
          zoom: float = 1.0) -> Axes3D:
    """Make a 3D panel. box is (x min, x max, y min, z min); every side is equally long."""
    args = pos if isinstance(pos, tuple) else (pos,)
    ax: Axes3D = fig.add_subplot(*args, projection='3d')   # type: ignore[assignment]
    ax.set_facecolor('white')
    side: float = box[1] - box[0]
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[2] + side)
    ax.set_zlim(box[3], box[3] + side)
    ax.set_box_aspect((1, 1, 1), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    return ax


def _label3d(ax: Axes3D, p: NDArray[np.float64], text: str, dx: float, dy: float,
             ha: str = 'left', color: str = INK, weight: str = 'normal') -> None:
    """Put a label a fixed number of points away from a 3D point, on the page."""
    x2, y2, _ = proj3d.proj_transform(p[0], p[1], p[2], ax.get_proj())
    ax.annotate(text, xy=(x2, y2), xytext=(dx, dy), textcoords='offset points', ha=ha,
                va='center', fontsize=9, color=color, weight=weight)


def _floor3d(ax: Axes3D, x0: float, x1: float, y0: float, y1: float) -> None:
    for v in np.arange(x0, x1 + 1e-9, 0.1):
        ax.plot([v, v], [y0, y1], [0, 0], color=GRID, lw=0.6)
    for v in np.arange(y0, y1 + 1e-9, 0.1):
        ax.plot([x0, x1], [v, v], [0, 0], color=GRID, lw=0.6)


def _ur(ax: Axes3D, q: NDArray[np.float64], color: str = LINK, pale: bool = False,
        joints: bool = True, lw: float = 5.0) -> list[NDArray[np.float64]]:
    """Draw the UR5e as a stick figure through its joint frames."""
    frames = forward(q)
    pts = np.array([f[:3, 3] for f in frames])
    ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=color, lw=lw, solid_capstyle='round',
            alpha=0.35 if pale else 1.0)
    if joints:
        for i in range(6):
            c = JOINT if i < 3 else WRIST
            ax.scatter(*pts[i], color=c, s=55, depthshade=False, edgecolors=INK,
                       linewidths=0.6, alpha=0.35 if pale else 1.0)
        ax.scatter(*pts[6], color=GRIP, s=40, depthshade=False, alpha=0.35 if pale else 1.0)
    return frames


def ur5e_joints() -> None:
    """Draw the UR5e at its working pose from forward kinematics, joints labelled."""
    fig = plt.figure(figsize=(8.2, 7.0), facecolor='white')
    ax = _ax3d(fig, 111, elev=25, azim=-40, box=(-0.75, 0.05, -0.45, 0.0), zoom=1.15)
    _floor3d(ax, -0.75, 0.05, -0.35, 0.25)
    q = np.radians(WORK_POSE_DEG)
    frames = _ur(ax, q, lw=7)
    offsets = ((0.04, 0.0, 0.0), (0.04, 0.0, 0.03), (0.0, 0.0, 0.05),
               (0.0, 0.0, 0.07), (0.02, 0.0, -0.06), (-0.03, 0.0, -0.03))
    aligns = ('left', 'left', 'left', 'left', 'left', 'right')
    for i, (label, off) in enumerate(zip(JOINT_LABELS, offsets)):
        p = frames[i][:3, 3]
        axis = frames[i][:3, 2]
        a0 = p - 0.06 * axis
        a1 = p + 0.06 * axis
        ax.plot([a0[0], a1[0]], [a0[1], a1[1]], [a0[2], a1[2]], color=INK, lw=1.0, ls='--')
        ax.text(p[0] + off[0], p[1] + off[1], p[2] + off[2], label, fontsize=9,
                color=LINK if i < 3 else WRIST, weight='bold', ha=aligns[i])
    tp = frames[6][:3, 3]
    ax.text(tp[0] - 0.03, tp[1], tp[2] - 0.03, 'tool', fontsize=9, color=GRIP, ha='right')
    fig.text(0.5, 0.9, 'The UR5e, drawn from its own chain', ha='center', fontsize=13,
             weight='bold', color=INK)
    fig.text(0.5, 0.03, 'blue labels: joints that place the wrist · orange labels: joints '
             'that point the tool\ndashed line through each joint: the axis it turns about',
             ha='center', fontsize=10, color=MUTED)
    _save(fig, SIX_DOC, 'ur5e-joints.svg')


def ur5e_frames() -> None:
    """Draw the zero pose with each joint's frame: one 4 x 4 transform per joint."""
    fig = plt.figure(figsize=(8.2, 6.8), facecolor='white')
    ax = _ax3d(fig, 111, elev=25, azim=-140, box=(-0.95, 0.05, -0.6, -0.35), zoom=1.6)
    q = np.zeros(6)
    frames = _ur(ax, q, color=LINK_PALE, joints=False, lw=6)
    # Where each label goes on the page, in points from its frame's origin.
    places = ((12, -8, 'left'), (14, 4, 'left'), (0, 22, 'center'), (-12, 8, 'right'),
              (12, 6, 'left'), (-12, -4, 'right'), (10, -12, 'left'))
    for i, f in enumerate(frames):
        p = f[:3, 3]
        for k, color in enumerate((AXIS_X, AXIS_Y, AXIS_Z)):
            e = p + 0.06 * f[:3, k]
            ax.plot([p[0], e[0]], [p[1], e[1]], [p[2], e[2]], color=color, lw=2)
        dx, dy, ha = places[i]
        _label3d(ax, p, f'frame {i}', dx, dy, ha=ha)
    fig.text(0.5, 0.9, 'Every pose is seven frames, each one built on the last',
             ha='center', fontsize=13, weight='bold', color=INK)
    fig.text(0.5, 0.08, 'all joints at 0 · red = x, green = y, blue = z of each frame\n'
             "frame i = frame i−1 moved by joint i's 4 × 4 transform",
             ha='center', fontsize=10, color=MUTED)
    _save(fig, SIX_DOC, 'frames-along-the-chain.svg')


def one_joint_at_a_time() -> None:
    """Six small pictures: the working pose, and the same pose with one joint turned 30°."""
    fig = plt.figure(figsize=(12.0, 8.2), facecolor='white')
    base = np.radians(WORK_POSE_DEG)
    for i, label in enumerate(JOINT_LABELS):
        ax = _ax3d(fig, (2, 3, i + 1), elev=22, azim=-115, box=(-0.8, 0.05, -0.5, -0.1),
                   zoom=1.5)
        _floor3d(ax, -0.8, 0.0, -0.4, 0.2)
        _ur(ax, base, color=LINK, pale=True, joints=False, lw=4)
        q = base.copy()
        q[i] += math.radians(30.0)
        frames = _ur(ax, q, color=LINK, lw=4)
        p = frames[i][:3, 3]
        ax.scatter(*p, s=260, facecolors='none', edgecolors=GRIP, linewidths=2,
                   depthshade=False)
        ax.set_title(f'{label} + 30°', fontsize=11, color=LINK if i < 3 else WRIST,
                     weight='bold', y=0.92)
    fig.text(0.5, 0.95, 'Turn one joint at a time: pale is before, dark is after',
             ha='center', fontsize=13, weight='bold', color=INK)
    fig.text(0.5, 0.04, 'The first three joints carry the tool a long way. The last three '
             'mostly turn it where it is.', ha='center', fontsize=10, color=MUTED)
    _save(fig, SIX_DOC, 'one-joint-at-a-time.svg')


def eight_answers() -> None:
    """Draw the eight different joint settings that put the tool on the same target."""
    target = tool(np.radians(WORK_POSE_DEG))
    answers = solve_many(target, tries=200, seed=1)
    answers.sort(key=lambda a: (-round(float(a[0]), 3), round(float(a[1]), 3)))
    fig = plt.figure(figsize=(13.0, 7.4), facecolor='white')
    for i, q in enumerate(answers):
        ax = _ax3d(fig, (2, 4, i + 1), elev=15, azim=-110, box=(-0.8, 0.05, -0.55, -0.1),
                   zoom=1.5)
        _floor3d(ax, -0.8, 0.0, -0.4, 0.2)
        _ur(ax, q, lw=4)
        t = target[:3, 3]
        ax.scatter(*t, marker='*', s=160, color=GRIP, depthshade=False)
        degs = ', '.join(f'{round(float(v)) + 0:d}' for v in np.degrees(q))
        ax.set_title(f'{i + 1}: ({degs})', fontsize=8, color=INK, y=0.95)
    fig.text(0.5, 0.95, 'One target (red star), eight ways to reach it',
             ha='center', fontsize=13, weight='bold', color=INK)
    fig.text(0.5, 0.04, 'Top row: the base faces the target. Bottom row: the base faces '
             'away and the arm reaches back over itself.\nIn each row: elbow up or down, '
             'and the wrist one way round or flipped.', ha='center', fontsize=10,
             color=MUTED)
    _save(fig, SIX_DOC, 'eight-answers.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    joint_types()
    the_chain()
    angles_add()
    joint_limits()
    two_vs_three()
    six_numbers()
    six_joint_schematic()
    seven_joint_schematic()
    scara_schematic()
    cartesian_schematic()
    delta_schematic()
    ur5e_joints()
    ur5e_frames()
    one_joint_at_a_time()
    eight_answers()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
