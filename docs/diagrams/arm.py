"""Generate the diagrams used in docs/arm/overview.md.

Images go to docs/images/<area>/, matching the docs/<area>/ folder that uses
them.

Run with:  pixi run python docs/diagrams/arm.py

The link lengths come from arm_math, so changing the arm changes the pictures.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Arc  # noqa: E402  (must follow matplotlib.use)
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'src' / 'arm_transforms'))
# Imported after the sys.path line above, which flake8's import rules cannot see.
from arm_transforms.arm_math import LINK1_M, LINK2_M, rotate_point  # noqa: E402,I100,I202

AREA = 'arm'
OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / 'images' / AREA

GRID = '#d6d6d6'
AXIS_X = '#d1495b'
AXIS_Y = '#2a9d3f'
LINK = '#3b82c4'
JOINT = '#f0a500'
INK = '#222222'
MUTED = '#777777'

Q1 = math.radians(30.0)
Q2 = math.radians(60.0)


def _axes(xlim, ylim, size=(6.4, 5.6)):
    fig, ax = plt.subplots(figsize=size, facecolor='white')
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _frame(ax, x, y, theta, label, length=0.13, offset=(0.0, -0.075)):
    """Draw a frame as a red +X arrow and a green +Y arrow."""
    for angle, color in ((theta, AXIS_X), (theta + math.pi / 2, AXIS_Y)):
        ax.annotate(
            '', xy=(x + length * math.cos(angle), y + length * math.sin(angle)),
            xytext=(x, y),
            arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.6,
                        'shrinkA': 0, 'shrinkB': 0},
            zorder=5)
    ax.text(x + offset[0], y + offset[1], label, color=INK, fontsize=9,
            ha='center', va='center', family='monospace', zorder=6)


def arm():
    """Draw the two-link arm with its joints, links and frames labelled."""
    fig, ax = _axes((-0.30, 0.92), (-0.22, 0.95))

    elbow = (LINK1_M * math.cos(Q1), LINK1_M * math.sin(Q1))
    grip = (elbow[0] + LINK2_M * math.cos(Q1 + Q2), elbow[1] + LINK2_M * math.sin(Q1 + Q2))

    # Reference lines the joint angles are measured from.
    ax.plot([0, 0.34], [0, 0], color=GRID, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ext = (elbow[0] + 0.20 * math.cos(Q1), elbow[1] + 0.20 * math.sin(Q1))
    ax.plot([elbow[0], ext[0]], [elbow[1], ext[1]], color=GRID, lw=1.0,
            ls=(0, (4, 3)), zorder=1)

    # The two links.
    ax.plot([0, elbow[0]], [0, elbow[1]], color=LINK, lw=7, solid_capstyle='round', zorder=2)
    ax.plot([elbow[0], grip[0]], [elbow[1], grip[1]], color=LINK, lw=7,
            solid_capstyle='round', zorder=2)

    # Joints and the gripper.
    ax.plot([0], [0], 'o', color=JOINT, ms=13, zorder=4)
    ax.plot([elbow[0]], [elbow[1]], 'o', color=JOINT, ms=13, zorder=4)
    ax.plot([grip[0]], [grip[1]], 'o', color='#e05555', ms=10, zorder=4)

    # Joint angle arcs.
    ax.add_patch(Arc((0, 0), 0.42, 0.42, theta1=0, theta2=math.degrees(Q1),
                     color=MUTED, lw=1.3, zorder=3))
    ax.text(0.245, 0.052, 'q1', color=INK, fontsize=11, family='monospace')
    ax.add_patch(Arc(elbow, 0.30, 0.30, theta1=math.degrees(Q1),
                     theta2=math.degrees(Q1 + Q2), color=MUTED, lw=1.3, zorder=3))
    ax.text(elbow[0] + 0.115, elbow[1] + 0.105, 'q2', color=INK, fontsize=11,
            family='monospace')

    # Link length labels, pushed off the link so they stay readable.
    mid1 = (elbow[0] / 2, elbow[1] / 2)
    ax.text(mid1[0] - 0.055, mid1[1] + 0.090, f'L1 = {LINK1_M} m', color=MUTED,
            fontsize=10, family='monospace', ha='center')
    mid2 = ((elbow[0] + grip[0]) / 2, (elbow[1] + grip[1]) / 2)
    ax.text(mid2[0] - 0.175, mid2[1], f'L2 = {LINK2_M} m', color=MUTED,
            fontsize=10, family='monospace', ha='center')

    _frame(ax, 0, 0, 0.0, 'base_link', length=0.17, offset=(-0.135, -0.095))
    _frame(ax, 0, 0, Q1, 'upper_arm', length=0.10, offset=(0.155, -0.095))
    _frame(ax, elbow[0], elbow[1], Q1 + Q2, 'forearm', offset=(0.17, -0.055))
    _frame(ax, grip[0], grip[1], Q1 + Q2, 'gripper', offset=(0.135, 0.055))

    ax.text(0.31, 0.90, 'The arm, and its four frames', fontsize=13, ha='center',
            color=INK, weight='bold')
    ax.text(0.31, -0.19, 'q1 turns the shoulder · q2 turns the elbow',
            fontsize=10, ha='center', color=MUTED)

    fig.savefig(OUT_DIR / 'arm.svg', bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)


def rotation():
    """Draw a point being turned about the origin, with the formula."""
    fig, ax = _axes((-0.40, 1.70), (-0.80, 1.45), size=(6.0, 5.4))

    theta = math.radians(55.0)
    px, py = 1.0, 0.25
    qx, qy = rotate_point(px, py, theta)

    for angle, color, name in ((0.0, AXIS_X, 'X'), (math.pi / 2, AXIS_Y, 'Y')):
        ax.annotate('', xy=(1.2 * math.cos(angle), 1.2 * math.sin(angle)), xytext=(0, 0),
                    arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.6})
        ax.text(1.30 * math.cos(angle), 1.30 * math.sin(angle), name, color=color,
                fontsize=11, ha='center', va='center', family='monospace')

    radius = math.hypot(px, py)
    ax.add_patch(Arc((0, 0), 2 * radius, 2 * radius,
                     theta1=math.degrees(math.atan2(py, px)),
                     theta2=math.degrees(math.atan2(qy, qx)),
                     color=GRID, lw=1.4, ls=(0, (5, 4))))

    for x, y, label, color in ((px, py, 'the point', '#888888'), (qx, qy, 'turned', LINK)):
        ax.plot([0, x], [0, y], color=color, lw=1.6, zorder=2)
        ax.plot([x], [y], 'o', color=color, ms=10, zorder=3)
        ax.text(x + 0.06, y + 0.09, f'{label}\n({x:.2f}, {y:.2f})', color=INK,
                fontsize=9.5, family='monospace', ha='left', va='bottom')

    ax.add_patch(Arc((0, 0), 0.55, 0.55, theta1=math.degrees(math.atan2(py, px)),
                     theta2=math.degrees(math.atan2(qy, qx)), color=MUTED, lw=1.3))
    ax.text(0.30, 0.30, 'theta', color=INK, fontsize=10, family='monospace')

    ax.text(0.65, 1.38, 'Turning a point about the origin', fontsize=13, ha='center',
            color=INK, weight='bold')
    ax.text(0.65, -0.50, "x' = x·cos(theta) − y·sin(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')
    ax.text(0.65, -0.68, "y' = x·sin(theta) + y·cos(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')

    fig.savefig(OUT_DIR / 'rotation.svg', bbox_inches='tight', pad_inches=0.3,
                facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    arm()
    rotation()
    print(f'wrote {OUT_DIR}/arm.svg and {OUT_DIR}/rotation.svg')
