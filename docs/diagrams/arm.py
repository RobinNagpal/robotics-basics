"""Generate the diagrams used in docs/arm/overview.md.

Images go to docs/images/<area>/, matching the docs/<area>/ folder that uses
them.

Run with:  pixi run python docs/diagrams/arm.py

There is one picture per idea in the doc, and they all draw the same arm, so a
reader can carry positions from one to the next. The link lengths come from
arm_math, so changing the arm changes every picture.
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
from arm_transforms.arm_math import (  # noqa: E402,I100,I202
    gripper_in_base, LINK1_M, LINK2_M, rotate_point, Transform2D)

AREA = 'arm'
OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / 'images' / AREA

GRID = '#d6d6d6'
AXIS_X = '#d1495b'
AXIS_Y = '#2a9d3f'
LINK = '#3b82c4'
LINK_PALE = '#b9d3ea'
JOINT = '#f0a500'
GRIP = '#e05555'
INK = '#222222'
MUTED = '#777777'

#: The pose every picture uses, so numbers carry from one to the next.
Q1 = math.radians(30.0)
Q2 = math.radians(60.0)

JOINT2 = (LINK1_M * math.cos(Q1), LINK1_M * math.sin(Q1))
GRIPPER = (JOINT2[0] + LINK2_M * math.cos(Q1 + Q2),
           JOINT2[1] + LINK2_M * math.sin(Q1 + Q2))


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(xlim, ylim, size=(6.4, 5.6), ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=size, facecolor='white')
    else:
        fig = ax.figure
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _frame(ax, x, y, theta, label, length=0.13, offset=(0.0, -0.075), size=9):
    """Draw a frame as a red +X arrow and a green +Y arrow."""
    for angle, color in ((theta, AXIS_X), (theta + math.pi / 2, AXIS_Y)):
        ax.annotate(
            '', xy=(x + length * math.cos(angle), y + length * math.sin(angle)),
            xytext=(x, y),
            arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.6,
                        'shrinkA': 0, 'shrinkB': 0},
            zorder=5)
    if label:
        ax.text(x + offset[0], y + offset[1], label, color=INK, fontsize=size,
                ha='center', va='center', family='monospace', zorder=6)


def _link(ax, start, end, color=LINK, width=7):
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=width,
            solid_capstyle='round', zorder=2)


def _joint(ax, point, size=13):
    ax.plot([point[0]], [point[1]], 'o', color=JOINT, ms=size, zorder=4)


def _gripper(ax, point, size=10):
    ax.plot([point[0]], [point[1]], 'o', color=GRIP, ms=size, zorder=4)


def _dashed(ax, start, end, color=GRID):
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=1.0,
            ls=(0, (4, 3)), zorder=1)


def _arc(ax, centre, radius, a1, a2, label, label_at, color=MUTED, size=11):
    ax.add_patch(Arc(centre, 2 * radius, 2 * radius, theta1=math.degrees(a1),
                     theta2=math.degrees(a2), color=color, lw=1.3, zorder=3))
    ax.text(label_at[0], label_at[1], label, color=INK, fontsize=size,
            family='monospace', ha='center', va='center', zorder=6)


def _title(ax, x, y, text):
    ax.text(x, y, text, fontsize=13, ha='center', color=INK, weight='bold')


def _caption(ax, x, y, text, size=10):
    ax.text(x, y, text, fontsize=size, ha='center', color=MUTED)


def _save(fig, name):
    fig.savefig(OUT_DIR / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)


# --------------------------------------------------------------------------
# the pictures
# --------------------------------------------------------------------------

def arm():
    """Draw the whole arm with its four frames. Used at the top of the doc."""
    fig, ax = _axes((-0.30, 0.92), (-0.22, 0.95))

    _dashed(ax, (0, 0), (0.34, 0))
    ext = (JOINT2[0] + 0.20 * math.cos(Q1), JOINT2[1] + 0.20 * math.sin(Q1))
    _dashed(ax, JOINT2, ext)

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, GRIPPER)
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _gripper(ax, GRIPPER)

    _arc(ax, (0, 0), 0.21, 0, Q1, 'q1', (0.245, 0.052))
    _arc(ax, JOINT2, 0.15, Q1, Q1 + Q2, 'q2', (JOINT2[0] + 0.115, JOINT2[1] + 0.105))

    mid1 = (JOINT2[0] / 2, JOINT2[1] / 2)
    ax.text(mid1[0] - 0.055, mid1[1] + 0.090, f'L1 = {LINK1_M} m', color=MUTED,
            fontsize=10, family='monospace', ha='center')
    mid2 = ((JOINT2[0] + GRIPPER[0]) / 2, (JOINT2[1] + GRIPPER[1]) / 2)
    ax.text(mid2[0] - 0.175, mid2[1], f'L2 = {LINK2_M} m', color=MUTED,
            fontsize=10, family='monospace', ha='center')

    _frame(ax, 0, 0, 0.0, 'base_link', length=0.17, offset=(-0.135, -0.095))
    _frame(ax, 0, 0, Q1, 'link1', length=0.10, offset=(0.125, -0.095))
    _frame(ax, JOINT2[0], JOINT2[1], Q1 + Q2, 'link2', offset=(0.145, -0.055))
    _frame(ax, GRIPPER[0], GRIPPER[1], Q1 + Q2, 'gripper', offset=(0.145, 0.055))

    _title(ax, 0.31, 0.90, 'The arm and its frames')
    _caption(ax, 0.31, -0.19,
             'q1 turns joint 1 · q2 turns joint 2 · the gripper is bolted on')
    _save(fig, 'arm.svg')


def one_joint():
    """Draw the simplest arm, and show cos and sin as the two sides of it."""
    fig, ax = _axes((-0.17, 0.76), (-0.22, 0.44), size=(6.2, 4.4))

    tip = (LINK1_M * math.cos(Q1), LINK1_M * math.sin(Q1))

    # Faint table axes to measure against.
    ax.annotate('', xy=(0.66, 0), xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})
    ax.annotate('', xy=(0, 0.38), xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})

    # The two sides of the right-angled triangle.
    _dashed(ax, tip, (tip[0], 0))
    _dashed(ax, tip, (0, tip[1]))

    _link(ax, (0, 0), tip)
    _joint(ax, (0, 0))
    _gripper(ax, tip)

    _arc(ax, (0, 0), 0.17, 0, Q1, 'q1', (0.205, 0.045))

    mid = (tip[0] / 2, tip[1] / 2)
    ax.text(mid[0] - 0.05, mid[1] + 0.075, f'L1 = {LINK1_M} m', color=MUTED,
            fontsize=10, family='monospace', ha='center')

    ax.text(tip[0] / 2, -0.075, f'L1·cos(q1) = {tip[0]:.3f}', color=AXIS_X,
            fontsize=10, family='monospace', ha='center')
    ax.text(-0.035, tip[1] / 2, f'L1·sin(q1)\n= {tip[1]:.3f}', color=AXIS_Y,
            fontsize=10, family='monospace', ha='right', va='center')

    ax.text(tip[0] + 0.035, tip[1] + 0.045, f'gripper\n({tip[0]:.3f}, {tip[1]:.3f})',
            color=INK, fontsize=9.5, family='monospace', ha='left', va='bottom')

    _frame(ax, 0, 0, 0.0, 'base_link', length=0.13, offset=(-0.02, -0.075))

    _title(ax, 0.30, 0.40, 'One joint, one link')
    _caption(ax, 0.30, -0.185, 'at q1 = 30°, the gripper is 0.5 m out along that angle')
    _save(fig, 'one_joint.svg')


def two_joints():
    """Draw the two-joint arm, showing that q2 is measured from link 1."""
    fig, ax = _axes((-0.22, 0.92), (-0.24, 0.86), size=(6.2, 5.2))

    _dashed(ax, (0, 0), (0.30, 0))
    ext = (JOINT2[0] + 0.26 * math.cos(Q1), JOINT2[1] + 0.26 * math.sin(Q1))
    _dashed(ax, JOINT2, ext)
    _dashed(ax, JOINT2, (JOINT2[0] + 0.26, JOINT2[1]))

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, GRIPPER)
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _gripper(ax, GRIPPER)

    _arc(ax, (0, 0), 0.18, 0, Q1, 'q1', (0.215, 0.045))
    # q2 is measured from link 1, not from the table.
    _arc(ax, JOINT2, 0.155, Q1, Q1 + Q2, 'q2',
         (JOINT2[0] + 0.135, JOINT2[1] + 0.105))
    # ...and the angle from the table is the two added together.
    _arc(ax, JOINT2, 0.235, 0, Q1 + Q2, 'q1 + q2',
         (JOINT2[0] + 0.245, JOINT2[1] + 0.205), color='#b06fc4')

    ax.text(JOINT2[0] + 0.045, JOINT2[1] - 0.075,
            f'joint 2\n({JOINT2[0]:.3f}, {JOINT2[1]:.3f})', color=INK,
            fontsize=9.5, family='monospace', ha='left', va='top')
    ax.text(GRIPPER[0] + 0.045, GRIPPER[1],
            f'gripper\n({GRIPPER[0]:.3f}, {GRIPPER[1]:.3f})', color=INK,
            fontsize=9.5, family='monospace', ha='left', va='center')

    _title(ax, 0.33, 0.82, 'Adding the second joint')
    _caption(ax, 0.33, -0.205,
             'q2 is measured from link 1 · from the table, link 2 points at q1 + q2')
    _save(fig, 'two_joints.svg')


def joining():
    """Show the chain being joined one link at a time, in three panels."""
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.9), facecolor='white')

    running = Transform2D()
    steps = [
        ('base_link → link1', 'link1', (0, 0)),
        ('base_link → link2', 'link2', JOINT2),
        ('base_link → gripper', 'gripper', GRIPPER),
    ]
    links = [Transform2D.rotation(Q1),
             Transform2D(LINK1_M, 0.0, Q2),
             Transform2D.translation(LINK2_M, 0.0)]

    for ax, (caption, name, point), link in zip(axes, steps, links):
        _axes((-0.26, 0.86), (-0.30, 0.90), ax=ax)
        running = running.then(link)

        # The whole arm, pale, so each panel sits in the same picture.
        _link(ax, (0, 0), JOINT2, color=LINK_PALE, width=5)
        _link(ax, JOINT2, GRIPPER, color=LINK_PALE, width=5)

        # The part reached so far, solid.
        if name == 'link1':
            _joint(ax, (0, 0), size=11)
        elif name == 'link2':
            _link(ax, (0, 0), JOINT2, width=6)
            _joint(ax, (0, 0), size=11)
            _joint(ax, JOINT2, size=11)
        else:
            _link(ax, (0, 0), JOINT2, width=6)
            _link(ax, JOINT2, GRIPPER, width=6)
            _joint(ax, (0, 0), size=11)
            _joint(ax, JOINT2, size=11)
            _gripper(ax, GRIPPER, size=9)

        # The transform reached so far, drawn as an arrow from the base.
        if point != (0, 0):
            ax.annotate('', xy=point, xytext=(0, 0),
                        arrowprops={'arrowstyle': '-|>', 'color': '#b06fc4',
                                    'lw': 1.8, 'shrinkA': 0, 'shrinkB': 0},
                        zorder=5)
        _frame(ax, point[0], point[1], running.theta, '', length=0.14)

        ax.text(0.30, 0.80, caption, fontsize=11, ha='center', color=INK,
                family='monospace', weight='bold')
        ax.text(0.30, -0.20,
                f'shift ({running.x:.3f}, {running.y:.3f})\n'
                f'turn {math.degrees(running.theta):.0f}°',
                fontsize=10, ha='center', color=MUTED, family='monospace')

    fig.suptitle('Joining the links, one at a time', fontsize=13, weight='bold', y=1.0)
    _save(fig, 'joining.svg')


def flipping():
    """Show the same relationship read in both directions."""
    fig, ax = _axes((-0.30, 0.98), (-0.26, 0.92), size=(6.4, 5.2))

    _link(ax, (0, 0), JOINT2, color=LINK_PALE, width=5)
    _link(ax, JOINT2, GRIPPER, color=LINK_PALE, width=5)
    _joint(ax, (0, 0), size=11)
    _joint(ax, JOINT2, size=11)
    _gripper(ax, GRIPPER, size=9)

    forward = gripper_in_base(Q1, Q2)
    back = forward.inverse()

    # Two arrows, bowed apart so both are readable.
    ax.annotate('', xy=GRIPPER, xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': '#b06fc4', 'lw': 2.0,
                            'connectionstyle': 'arc3,rad=-0.25'}, zorder=5)
    ax.annotate('', xy=(0, 0), xytext=GRIPPER,
                arrowprops={'arrowstyle': '-|>', 'color': '#3aa39a', 'lw': 2.0,
                            'connectionstyle': 'arc3,rad=-0.25'}, zorder=5)

    _frame(ax, 0, 0, 0.0, 'base_link', length=0.15, offset=(-0.005, -0.10))
    _frame(ax, GRIPPER[0], GRIPPER[1], Q1 + Q2, 'gripper',
           length=0.15, offset=(0.155, 0.045))

    ax.text(-0.28, 0.46,
            f'base_link → gripper\nshift ({forward.x:.3f}, {forward.y:.3f})\n'
            f'turn {math.degrees(forward.theta):.0f}°',
            color='#8b4fa5', fontsize=9.5, family='monospace', ha='left', va='center')
    ax.text(0.60, 0.20,
            f'gripper → base_link\nshift ({back.x:.3f}, {back.y:.3f})\n'
            f'turn {math.degrees(back.theta):.0f}°',
            color='#2b7d76', fontsize=9.5, family='monospace', ha='left', va='center')

    _title(ax, 0.34, 0.88, 'The same link, read both ways')
    _caption(ax, 0.34, -0.225, 'nothing new was measured — the turn and shift are undone')
    _save(fig, 'flipping.svg')


def carrying():
    """Show a point fixed in the gripper frame, at two different arm poses."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.4), facecolor='white')
    poses = [(Q1, Q2), (math.radians(-15.0), math.radians(50.0))]

    for ax, (q1, q2) in zip(axes, poses):
        _axes((-0.22, 1.02), (-0.56, 0.86), ax=ax)
        joint2 = (LINK1_M * math.cos(q1), LINK1_M * math.sin(q1))
        grip = (joint2[0] + LINK2_M * math.cos(q1 + q2),
                joint2[1] + LINK2_M * math.sin(q1 + q2))

        _link(ax, (0, 0), joint2)
        _link(ax, joint2, grip)
        _joint(ax, (0, 0), size=11)
        _joint(ax, joint2, size=11)
        _gripper(ax, grip, size=9)

        tip = gripper_in_base(q1, q2).apply(0.05, 0.0)
        _dashed(ax, grip, tip, color='#c9a227')
        ax.plot([tip[0]], [tip[1]], '*', color='#c9a227', ms=15, zorder=5)

        _frame(ax, grip[0], grip[1], q1 + q2, '', length=0.12)

        ax.text(tip[0] + 0.03, tip[1] + 0.03,
                f'tip on the table\n({tip[0]:.3f}, {tip[1]:.3f})', color=INK,
                fontsize=9, family='monospace', ha='left', va='bottom')
        ax.text(0.40, -0.34, f'q1 = {math.degrees(q1):.0f}°, q2 = {math.degrees(q2):.0f}°',
                fontsize=10.5, ha='center', color=INK, family='monospace')
        ax.text(0.40, -0.47, 'in the gripper frame: (0.05, 0)', color='#8a6d1f',
                fontsize=9.5, family='monospace', ha='center')

    fig.suptitle('The tip never moves in the gripper frame', fontsize=13,
                 weight='bold', y=1.0)
    _save(fig, 'carrying.svg')


def three_joints():
    """Sketch a third joint, to show the pattern does not change."""
    fig, ax = _axes((-0.26, 1.06), (-0.28, 0.98), size=(6.4, 5.2))

    link3_m = 0.25
    q3 = math.radians(-50.0)
    joint3 = GRIPPER
    tip = (joint3[0] + link3_m * math.cos(Q1 + Q2 + q3),
           joint3[1] + link3_m * math.sin(Q1 + Q2 + q3))

    _dashed(ax, (0, 0), (0.28, 0))
    _dashed(ax, JOINT2, (JOINT2[0] + 0.22 * math.cos(Q1), JOINT2[1] + 0.22 * math.sin(Q1)))
    _dashed(ax, joint3, (joint3[0] + 0.22 * math.cos(Q1 + Q2),
                         joint3[1] + 0.22 * math.sin(Q1 + Q2)))

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, joint3)
    _link(ax, joint3, tip, color='#7ab8e8')
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _joint(ax, joint3)
    _gripper(ax, tip)

    _arc(ax, (0, 0), 0.17, 0, Q1, 'q1', (0.205, 0.042))
    _arc(ax, JOINT2, 0.14, Q1, Q1 + Q2, 'q2', (JOINT2[0] + 0.125, JOINT2[1] + 0.09))
    _arc(ax, joint3, 0.14, Q1 + Q2 + q3, Q1 + Q2, 'q3',
         (joint3[0] + 0.085, joint3[1] + 0.175))

    ax.text(0.86, 0.79, 'link 3 is new', color=MUTED, fontsize=10,
            family='monospace', ha='center')
    ax.annotate('', xy=((joint3[0] + tip[0]) / 2, (joint3[1] + tip[1]) / 2),
                xytext=(0.86, 0.755),
                arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})

    _title(ax, 0.38, 0.94, 'A third joint changes nothing')
    _caption(ax, 0.38, -0.245,
             'one more row in the list · joining produces q1 + q2 + q3 on its own')
    _save(fig, 'three_joints.svg')


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

    _title(ax, 0.65, 1.38, 'Turning a point about the origin')
    ax.text(0.65, -0.50, "x' = x·cos(theta) − y·sin(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')
    ax.text(0.65, -0.68, "y' = x·sin(theta) + y·cos(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')
    _save(fig, 'rotation.svg')


FIGURES = (arm, one_joint, two_joints, rotation, joining, flipping, carrying,
           three_joints)

if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for figure in FIGURES:
        figure()
    print(f'wrote {len(FIGURES)} diagrams to {OUT_DIR}')
