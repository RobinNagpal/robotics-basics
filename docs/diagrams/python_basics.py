"""Generate the diagrams used in docs/01_robotics-intro/01_python-and-numpy/01_python-basics.md.

Images go to docs/images/python-and-numpy/python-basics/.

Run with:  pixi run python ../docs/diagrams/python_basics.py

There is one picture per idea in the doc. They draw the same arm as the frames
and transforms doc: link 1 is 3 m long, link 2 is 2 m long.

Set PNG_DIR to a folder to also write PNG copies, for checking by eye.
"""

import math
import os
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, FancyBboxPatch, Wedge  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

OUT_DIR: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                         / 'python-and-numpy' / 'python-basics')
PNG_DIR: str = os.environ.get('PNG_DIR', '')

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#b9d3ea'
JOINT: str = '#f0a500'
GRIP: str = '#e05555'
INK: str = '#222222'
MUTED: str = '#777777'
GOOD: str = '#2a9d3f'
BAD: str = '#d1495b'

L1: float = 3.0
L2: float = 2.0


def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _link(ax: Axes, start: tuple[float, float], end: tuple[float, float],
          color: str = LINK) -> None:
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=7,
            solid_capstyle='round', zorder=2)


def _dot(ax: Axes, point: tuple[float, float], color: str, size: float = 13) -> None:
    ax.plot([point[0]], [point[1]], 'o', color=color, ms=size, zorder=4)


def _dashed(ax: Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.plot([start[0], end[0]], [start[1], end[1]], color=GRID, lw=1.0,
            ls=(0, (4, 3)), zorder=1)


def _save(fig: Figure, name: str) -> None:
    fig.savefig(OUT_DIR / f'{name}.svg', bbox_inches='tight', pad_inches=0.3,
                facecolor='white')
    if PNG_DIR:
        fig.savefig(pathlib.Path(PNG_DIR) / f'{name}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def list_to_arm() -> None:
    """Show that q[0] turns the joint at the base and q[1] the joint after it."""
    fig, ax = plt.subplots(figsize=(8.4, 5.0), facecolor='white')
    _axes(ax, (-3.6, 5.2), (-1.3, 4.6))

    q1: float = math.radians(30.0)
    q2: float = math.radians(60.0)
    joint2: tuple[float, float] = (L1 * math.cos(q1), L1 * math.sin(q1))
    grip: tuple[float, float] = (joint2[0] + L2 * math.cos(q1 + q2),
                                 joint2[1] + L2 * math.sin(q1 + q2))

    ax.plot([-0.6, 0.6], [-0.18, -0.18], color=INK, lw=2, zorder=1)
    _dashed(ax, (0, 0), (1.6, 0))
    _dashed(ax, joint2, (joint2[0] + 1.2 * math.cos(q1), joint2[1] + 1.2 * math.sin(q1)))
    _link(ax, (0, 0), joint2)
    _link(ax, joint2, grip)
    _dot(ax, (0, 0), JOINT)
    _dot(ax, joint2, JOINT)
    _dot(ax, grip, GRIP, 10)
    ax.add_patch(Arc((0, 0), 2.2, 2.2, theta1=0, theta2=30, color=MUTED, lw=1.3))
    ax.add_patch(Arc(joint2, 1.6, 1.6, theta1=30, theta2=90, color=MUTED, lw=1.3))
    ax.text(1.35, 0.32, '30°', fontsize=10, color=INK, family='monospace')
    ax.text(joint2[0] + 0.55, joint2[1] + 0.68, '60°', fontsize=10, color=INK,
            family='monospace')
    ax.text(grip[0] + 0.25, grip[1], 'gripper', fontsize=10, color=INK, va='center')

    # The list, drawn as two boxes with their indexes underneath.
    ax.text(-3.4, 3.9, 'q =', fontsize=14, family='monospace', color=INK, va='center')
    boxes: list[tuple[float, str, str]] = [(-2.55, '30.0', '0'), (-1.35, '60.0', '1')]
    for left, value, index in boxes:
        ax.add_patch(FancyBboxPatch((left, 3.55), 1.1, 0.7, boxstyle='round,pad=0.02',
                                    fc='#fff4d6', ec=JOINT, lw=1.5))
        ax.text(left + 0.55, 3.9, value, fontsize=13, family='monospace', ha='center',
                va='center', color=INK)
        ax.text(left + 0.55, 3.28, f'q[{index}]', fontsize=10, family='monospace',
                ha='center', va='center', color=MUTED)

    arrow: dict[str, object] = {'arrowstyle': '-|>', 'color': JOINT, 'lw': 1.4,
                                'connectionstyle': 'arc3,rad=0.25'}
    ax.annotate('', xy=(-0.18, 0.2), xytext=(-2.0, 3.05), arrowprops=arrow)
    ax.annotate('', xy=(joint2[0] - 0.25, joint2[1] + 0.12), xytext=(-0.8, 3.05),
                arrowprops={**arrow, 'connectionstyle': 'arc3,rad=-0.2'})
    ax.text(-1.95, 1.2, 'joint 1,\nat the base', fontsize=10, color=INK, ha='center')
    ax.text(joint2[0] + 0.3, joint2[1] - 0.5, 'joint 2', fontsize=10, color=INK, ha='left')

    ax.text(0.8, -1.05, 'Index 0 is the joint nearest the base. Each index after it is one '
            'joint further out.', fontsize=10, color=MUTED, ha='center')
    _save(fig, 'list-to-arm')


def radians_mistake() -> None:
    """Show where a link points when 60 is passed to cos as radians by mistake."""
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.0), facecolor='white')
    wrong_deg: float = math.degrees(60.0) % 360.0
    panels: list[tuple[str, float, str, str]] = [
        ('math.cos(math.radians(60))', 60.0, GOOD, 'the link points at 60°, as meant'),
        ('math.cos(60)', wrong_deg, BAD,
         f'60 is read as 60 radians, which is {math.degrees(60.0):.1f}°:\n'
         f'{int(math.degrees(60.0) // 360)} full turns and then {wrong_deg:.1f}°'),
    ]
    for ax, (code, angle_deg, color, caption) in zip(axes, panels):
        _axes(ax, (-3.8, 3.8), (-3.2, 3.9))
        _dashed(ax, (-3.3, 0), (3.3, 0))
        _dashed(ax, (0, -3.0), (0, 3.2))
        angle: float = math.radians(angle_deg)
        tip: tuple[float, float] = (L1 * math.cos(angle), L1 * math.sin(angle))
        _link(ax, (0, 0), tip, color=LINK if color == GOOD else LINK_PALE)
        _dot(ax, (0, 0), JOINT)
        _dot(ax, tip, color, 10)
        ax.add_patch(Arc((0, 0), 1.4, 1.4, theta1=0, theta2=angle_deg, color=MUTED, lw=1.3))
        mid: float = math.radians(min(angle_deg / 2, 20.0))
        ax.text(1.35 * math.cos(mid), 1.35 * math.sin(mid), f'{angle_deg:.1f}°',
                fontsize=10, color=INK, family='monospace', ha='center', va='center')
        ax.text(tip[0], tip[1] + (0.4 if tip[1] >= 0 else -0.45),
                f'x = {tip[0]:.3f}', fontsize=10, color=color, family='monospace',
                ha='center', va='center')
        ax.text(0, 3.65, code, fontsize=12, family='monospace', ha='center', color=INK,
                weight='bold')
        ax.text(0, -3.05, caption, fontsize=10, color=MUTED, ha='center', va='top')
    _save(fig, 'radians-mistake')


def joint_limits() -> None:
    """Show set_angle refusing 170° and set_angle_clamped stopping at 150°."""
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.0), facecolor='white')
    panels: list[tuple[str, str]] = [
        ('elbow.set_angle(170.0)', 'ValueError: the joint stays at 0°'),
        ('elbow.set_angle_clamped(170.0)', 'the joint stops at its limit, 150°'),
    ]
    for i, (ax, (code, caption)) in enumerate(zip(axes, panels)):
        _axes(ax, (-3.4, 3.4), (-3.2, 3.6))
        ax.add_patch(Wedge((0, 0), 2.6, -150, 150, fc='#e3f3e6', ec='none', zorder=0))
        ax.add_patch(Wedge((0, 0), 2.6, 150, 210, fc='#f8dfe2', ec='none', zorder=0))
        ax.text(-2.2, 0, 'not\nallowed', fontsize=9, color=BAD, ha='center', va='center')
        ax.text(1.35, -0.55, 'allowed: -150° to 150°', fontsize=9, color=GOOD, ha='center')
        asked: float = math.radians(170.0)
        ax.plot([0, 2.9 * math.cos(asked)], [0, 2.9 * math.sin(asked)], color=BAD, lw=1.5,
                ls=(0, (4, 3)), zorder=1)
        ax.text(2.9 * math.cos(asked) + 0.1, 2.9 * math.sin(asked) + 0.3, 'asked: 170°',
                fontsize=10, color=BAD, ha='center')
        final_deg: float = 0.0 if i == 0 else 150.0
        final: float = math.radians(final_deg)
        tip: tuple[float, float] = (2.4 * math.cos(final), 2.4 * math.sin(final))
        _link(ax, (0, 0), tip)
        _dot(ax, (0, 0), JOINT)
        _dot(ax, tip, GRIP, 10)
        label_at: tuple[float, float] = ((tip[0], tip[1] + 0.35) if i == 0
                                         else (tip[0] + 0.2, tip[1] + 0.45))
        ax.text(*label_at, f'now {final_deg:.0f}°', fontsize=10, color=INK, ha='center')
        ax.text(0, 3.3, code, fontsize=12, family='monospace', ha='center', color=INK,
                weight='bold')
        ax.text(0, -3.05, caption, fontsize=10, color=MUTED, ha='center', va='top')
    _save(fig, 'joint-limits')


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    list_to_arm()
    radians_mistake()
    joint_limits()
    print(f'wrote 3 diagrams to {OUT_DIR}')
