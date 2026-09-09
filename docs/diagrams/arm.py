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

#: The pose most pictures use. Slanted, so no link lies flat on an axis and
#: every angle in the drawing is actually visible.
Q1 = math.radians(30.0)
Q2 = math.radians(60.0)

#: A second pose, used only where two poses need comparing.
R1 = math.radians(60.0)
R2 = math.radians(-60.0)

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


def _n(value, places=9):
    """Round away floating-point dust, so cos(90°) prints as 0 and not 1.8e-16."""
    return round(value, places) + 0.0


def _fmt(value):
    """Format a coordinate: whole numbers stay short, the rest get 3 decimals."""
    value = _n(value)
    if value == round(value):
        return f'{value:g}'
    return f'{value:.3f}'.rstrip('0').rstrip('.')


def _save(fig, name):
    fig.savefig(OUT_DIR / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)


# --------------------------------------------------------------------------
# the pictures
# --------------------------------------------------------------------------


def arm():
    """Draw the whole arm with its four frames. Used at the top of the doc."""
    fig, ax = _axes((-1.7, 5.5), (-1.5, 5.0), size=(6.6, 5.4))

    _dashed(ax, (0, 0), (1.7, 0))
    ext = (JOINT2[0] + 1.1 * math.cos(Q1), JOINT2[1] + 1.1 * math.sin(Q1))
    _dashed(ax, JOINT2, ext)

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, GRIPPER)
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _gripper(ax, GRIPPER)

    _arc(ax, (0, 0), 1.1, 0, Q1, 'q1 = 30°', (1.62, 0.34))
    _arc(ax, JOINT2, 0.95, Q1, Q1 + Q2, 'q2 = 60°', (JOINT2[0] + 0.72, JOINT2[1] + 1.18))

    ax.text(0.82, 1.55, f'L1 = {LINK1_M:g} m', color=MUTED, fontsize=10,
            family='monospace', ha='center')
    ax.text(2.30, 2.50, f'L2 = {LINK2_M:g} m', color=MUTED, fontsize=10,
            family='monospace', ha='right')

    _frame(ax, 0, 0, 0.0, 'base_link', length=1.0, offset=(-0.20, -0.55))
    _frame(ax, 0, 0, Q1, 'link1', length=0.75, offset=(1.15, -0.42))
    _frame(ax, JOINT2[0], JOINT2[1], Q1 + Q2, 'link2', length=0.8,
           offset=(-0.90, 0.42))
    _frame(ax, GRIPPER[0], GRIPPER[1], Q1 + Q2, 'gripper', length=0.8,
           offset=(0.95, 0.15))

    _title(ax, 1.9, 4.75, 'The arm and its frames')
    _caption(ax, 1.9, -1.35,
             'q1 turns joint 1 · q2 turns joint 2 · the gripper is bolted on')
    _save(fig, 'arm.svg')


def one_joint():
    """Draw the simplest arm at two angles, to show what cos and sin do."""
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6), facecolor='white')

    for ax, q1 in zip(axes, (math.radians(30.0), math.radians(60.0))):
        _axes((-1.7, 4.4), (-1.7, 4.2), ax=ax)
        tip = (LINK1_M * math.cos(q1), LINK1_M * math.sin(q1))

        ax.annotate('', xy=(3.9, 0), xytext=(0, 0),
                    arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})
        ax.annotate('', xy=(0, 3.8), xytext=(0, 0),
                    arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})

        _dashed(ax, tip, (tip[0], 0))
        _dashed(ax, tip, (0, tip[1]))
        _link(ax, (0, 0), tip)
        _joint(ax, (0, 0), size=11)
        _gripper(ax, tip, size=9)
        _arc(ax, (0, 0), 0.9, 0, q1, f'q1 = {math.degrees(q1):.0f}°',
             (1.45 * math.cos(q1 / 2), 1.45 * math.sin(q1 / 2)), size=10)

        ax.text(tip[0] / 2, -0.62, f'3·cos(q1) = {tip[0]:.3f}', color=AXIS_X,
                fontsize=10, family='monospace', ha='center')
        ax.text(-0.28, tip[1] / 2, '3·sin(q1)', color=AXIS_Y, fontsize=10,
                family='monospace', ha='right', va='bottom')
        ax.text(-0.28, tip[1] / 2 - 0.42, f'= {tip[1]:.3f}', color=AXIS_Y,
                fontsize=10, family='monospace', ha='right', va='bottom')
        ax.text(tip[0] + 0.22, tip[1] + 0.28, f'({_fmt(tip[0])}, {_fmt(tip[1])})',
                color=INK, fontsize=10, family='monospace', ha='left', va='bottom')

    fig.suptitle(f'One joint, one link  (L1 = {LINK1_M:g} m).  '
                 'Turn it from 30° to 60° and the two swap round.',
                 fontsize=12.5, weight='bold', y=1.0)
    _save(fig, 'one_joint.svg')


def two_joints():
    """Draw the two-joint arm, showing that q2 is measured from link 1."""
    fig, ax = _axes((-2.0, 6.0), (-1.6, 5.2), size=(6.8, 5.4))

    _dashed(ax, (0, 0), (1.8, 0))
    ext = (JOINT2[0] + 1.5 * math.cos(Q1), JOINT2[1] + 1.5 * math.sin(Q1))
    _dashed(ax, JOINT2, ext)
    _dashed(ax, JOINT2, (JOINT2[0] + 2.1, JOINT2[1]))

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, GRIPPER)
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _gripper(ax, GRIPPER)

    _arc(ax, (0, 0), 1.05, 0, Q1, 'q1 = 30°', (1.60, 0.32))
    _arc(ax, JOINT2, 0.95, Q1, Q1 + Q2, 'q2 = 60°',
         (JOINT2[0] + 0.95, JOINT2[1] + 0.50))
    _arc(ax, JOINT2, 1.85, 0, Q1 + Q2, 'q1 + q2 = 90°',
         (JOINT2[0] + 1.30, JOINT2[1] + 2.05), color='#b06fc4', size=10)

    ax.text(0.80, 1.58, f'L1 = {LINK1_M:g}', color=MUTED, fontsize=10,
            family='monospace', ha='center')
    ax.text(2.30, 2.50, f'L2 = {LINK2_M:g}', color=MUTED, fontsize=10,
            family='monospace', ha='right')

    ax.text(2.90, 1.10, 'joint 2 (2.598, 1.5)', color=INK, fontsize=9.5,
            family='monospace', ha='left', va='center')
    ax.text(2.36, 3.62, 'gripper (2.598, 3.5)', color=INK, fontsize=9.5,
            family='monospace', ha='right', va='center')

    _title(ax, 2.0, 4.95, 'Adding the second joint')
    _caption(ax, 2.0, -1.45,
             'q2 is measured from link 1 · from the table it comes to q1 + q2')
    _save(fig, 'two_joints.svg')


def joining():
    """Show the chain being joined one link at a time, in three panels."""
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 4.2), facecolor='white')

    running = Transform2D()
    steps = [
        ('base_link -> link1', 'link1', (0, 0)),
        ('base_link -> link2', 'link2', JOINT2),
        ('base_link -> gripper', 'gripper', GRIPPER),
    ]
    links = [Transform2D.rotation(Q1),
             Transform2D(LINK1_M, 0.0, Q2),
             Transform2D.translation(LINK2_M, 0.0)]

    for ax, (caption, name, point), link in zip(axes, steps, links):
        _axes((-1.4, 4.4), (-2.1, 5.0), ax=ax)
        running = running.then(link)

        _link(ax, (0, 0), JOINT2, color=LINK_PALE, width=5)
        _link(ax, JOINT2, GRIPPER, color=LINK_PALE, width=5)

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

        if point != (0, 0):
            ax.annotate('', xy=point, xytext=(0, 0),
                        arrowprops={'arrowstyle': '-|>', 'color': '#b06fc4',
                                    'lw': 1.8, 'shrinkA': 0, 'shrinkB': 0},
                        zorder=5)
        _frame(ax, point[0], point[1], running.theta, '', length=0.9)

        ax.text(1.5, 4.62, caption, fontsize=11, ha='center', color=INK,
                family='monospace', weight='bold')
        ax.text(1.5, -1.55, f'shift ({_fmt(running.x)}, {_fmt(running.y)})',
                fontsize=11, ha='center', color=MUTED, family='monospace')
        ax.text(1.5, -2.0, f'turn {math.degrees(running.theta):.0f}°',
                fontsize=11, ha='center', color=MUTED, family='monospace')

    fig.suptitle('Joining the links, one at a time', fontsize=13, weight='bold', y=1.0)
    _save(fig, 'joining.svg')


def flipping():
    """Show the same relationship read in both directions."""
    fig, ax = _axes((-2.4, 6.6), (-2.4, 4.9), size=(7.0, 5.0))

    _link(ax, (0, 0), JOINT2, color=LINK_PALE, width=5)
    _link(ax, JOINT2, GRIPPER, color=LINK_PALE, width=5)
    _joint(ax, (0, 0), size=11)
    _joint(ax, JOINT2, size=11)
    _gripper(ax, GRIPPER, size=9)

    forward = gripper_in_base(Q1, Q2)
    back = forward.inverse()

    ax.annotate('', xy=GRIPPER, xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': '#b06fc4', 'lw': 2.0,
                            'connectionstyle': 'arc3,rad=-0.3'}, zorder=5)
    ax.annotate('', xy=(0, 0), xytext=GRIPPER,
                arrowprops={'arrowstyle': '-|>', 'color': '#3aa39a', 'lw': 2.0,
                            'connectionstyle': 'arc3,rad=-0.3'}, zorder=5)

    _frame(ax, 0, 0, 0.0, 'base_link', length=0.9, offset=(-0.15, -0.55))
    _frame(ax, GRIPPER[0], GRIPPER[1], Q1 + Q2, 'gripper', length=0.9,
           offset=(1.05, 0.15))

    ax.text(-2.2, 3.6, 'base_link -> gripper', color='#8b4fa5', fontsize=10,
            family='monospace', ha='left')
    ax.text(-2.2, 3.15, f'shift ({_fmt(forward.x)}, {_fmt(forward.y)})',
            color='#8b4fa5', fontsize=10, family='monospace', ha='left')
    ax.text(-2.2, 2.70, f'turn {math.degrees(forward.theta):.0f}°', color='#8b4fa5',
            fontsize=10, family='monospace', ha='left')

    ax.text(3.5, 0.55, 'gripper -> base_link', color='#2b7d76', fontsize=10,
            family='monospace', ha='left')
    ax.text(3.5, 0.10, f'shift ({_fmt(back.x)}, {_fmt(back.y)})', color='#2b7d76',
            fontsize=10, family='monospace', ha='left')
    ax.text(3.5, -0.35, f'turn {math.degrees(back.theta):.0f}°', color='#2b7d76',
            fontsize=10, family='monospace', ha='left')

    _title(ax, 2.1, 4.65, 'The same link, read both ways')
    _caption(ax, 2.1, -2.1, 'the same two numbers come back, swapped and turned')
    _save(fig, 'flipping.svg')


def carrying():
    """Show a point fixed in the gripper frame, at two different arm poses."""
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.8), facecolor='white')

    for ax, (q1, q2) in zip(axes, [(Q1, Q2), (R1, R2)]):
        _axes((-1.6, 6.4), (-2.6, 5.6), ax=ax)
        joint2 = (LINK1_M * math.cos(q1), LINK1_M * math.sin(q1))
        grip = (joint2[0] + LINK2_M * math.cos(q1 + q2),
                joint2[1] + LINK2_M * math.sin(q1 + q2))

        _link(ax, (0, 0), joint2)
        _link(ax, joint2, grip)
        _joint(ax, (0, 0), size=11)
        _joint(ax, joint2, size=11)
        _gripper(ax, grip, size=9)

        tip = gripper_in_base(q1, q2).apply(1.0, 0.0)
        _dashed(ax, grip, tip, color='#c9a227')
        ax.plot([tip[0]], [tip[1]], '*', color='#c9a227', ms=17, zorder=5)
        _frame(ax, grip[0], grip[1], q1 + q2, '', length=0.75)

        ax.text(tip[0] + 0.45, tip[1] + 0.95, 'tip on the table', color=INK,
                fontsize=10, family='monospace', ha='center', va='bottom')
        ax.text(tip[0] + 0.45, tip[1] + 0.5, f'({_fmt(tip[0])}, {_fmt(tip[1])})',
                color=INK, fontsize=10, family='monospace', ha='center', va='bottom')
        ax.text(2.4, -1.7, f'q1 = {math.degrees(q1):.0f}°, q2 = {math.degrees(q2):.0f}°',
                fontsize=11, ha='center', color=INK, family='monospace')
        ax.text(2.4, -2.4, 'in the gripper frame: (1, 0)', color='#8a6d1f',
                fontsize=10, family='monospace', ha='center')

    fig.suptitle('The tip never moves in the gripper frame', fontsize=13,
                 weight='bold', y=1.0)
    _save(fig, 'carrying.svg')


def three_joints():
    """Sketch a third joint, to show the pattern does not change."""
    fig, ax = _axes((-2.0, 6.6), (-1.7, 5.4), size=(6.8, 5.2))

    link3_m = 1.0
    q3 = math.radians(-60.0)
    joint3 = GRIPPER
    tip = (joint3[0] + link3_m * math.cos(Q1 + Q2 + q3),
           joint3[1] + link3_m * math.sin(Q1 + Q2 + q3))

    _dashed(ax, (0, 0), (1.6, 0))
    _dashed(ax, JOINT2, (JOINT2[0] + 1.2 * math.cos(Q1), JOINT2[1] + 1.2 * math.sin(Q1)))
    _dashed(ax, joint3, (joint3[0], joint3[1] + 1.2))

    _link(ax, (0, 0), JOINT2)
    _link(ax, JOINT2, joint3)
    _link(ax, joint3, tip, color='#7ab8e8')
    _joint(ax, (0, 0))
    _joint(ax, JOINT2)
    _joint(ax, joint3)
    _gripper(ax, tip)

    _arc(ax, (0, 0), 1.0, 0, Q1, 'q1', (1.35, 0.30))
    _arc(ax, JOINT2, 0.9, Q1, Q1 + Q2, 'q2', (JOINT2[0] + 0.48, JOINT2[1] + 1.12))
    _arc(ax, joint3, 0.85, Q1 + Q2 + q3, Q1 + Q2, 'q3',
         (joint3[0] + 0.72, joint3[1] + 0.82))

    ax.text(4.6, 3.1, f'link 3 is new (L3 = {link3_m:g})', color=MUTED,
            fontsize=10, family='monospace', ha='center', va='center')
    ax.annotate('', xy=((joint3[0] + tip[0]) / 2 + 0.12, (joint3[1] + tip[1]) / 2),
                xytext=(4.6, 3.3),
                arrowprops={'arrowstyle': '-|>', 'color': GRID, 'lw': 1.2})
    ax.text(tip[0] + 0.25, tip[1] - 0.05, f'({_fmt(tip[0])}, {_fmt(tip[1])})',
            color=INK, fontsize=9.5, family='monospace', ha='left', va='center')

    _title(ax, 2.2, 5.15, 'A third joint changes nothing')
    _caption(ax, 2.2, -1.55,
             'one more row in the list · joining produces q1 + q2 + q3 on its own')
    _save(fig, 'three_joints.svg')


def rotation():
    """Draw a point being turned about the origin, with the formula."""
    fig, ax = _axes((-3.0, 5.6), (-2.9, 4.7), size=(6.4, 5.4))

    theta = math.radians(45.0)
    px, py = 3.0, 1.0
    qx, qy = rotate_point(px, py, theta)

    for angle, color, name in ((0.0, AXIS_X, 'X'), (math.pi / 2, AXIS_Y, 'Y')):
        ax.annotate('', xy=(3.9 * math.cos(angle), 3.9 * math.sin(angle)), xytext=(0, 0),
                    arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.6})
        ax.text(4.3 * math.cos(angle), 4.3 * math.sin(angle), name, color=color,
                fontsize=11, ha='center', va='center', family='monospace')

    radius = math.hypot(px, py)
    ax.add_patch(Arc((0, 0), 2 * radius, 2 * radius,
                     theta1=math.degrees(math.atan2(py, px)),
                     theta2=math.degrees(math.atan2(qy, qx)),
                     color=GRID, lw=1.4, ls=(0, (5, 4))))

    for x, y, label, color in ((px, py, 'the point', '#888888'),
                               (qx, qy, 'turned by 45°', LINK)):
        ax.plot([0, x], [0, y], color=color, lw=1.8, zorder=2)
        ax.plot([x], [y], 'o', color=color, ms=11, zorder=3)
        ax.text(x + 0.2, y + 0.5, label, color=INK, fontsize=10,
                family='monospace', ha='left', va='bottom')
        ax.text(x + 0.2, y + 0.12, f'({_fmt(x)}, {_fmt(y)})', color=INK,
                fontsize=10, family='monospace', ha='left', va='bottom')

    ax.add_patch(Arc((0, 0), 2.2, 2.2, theta1=math.degrees(math.atan2(py, px)),
                     theta2=math.degrees(math.atan2(qy, qx)), color=MUTED, lw=1.3))
    ax.text(1.30, 0.95, 'theta', color=INK, fontsize=10, family='monospace')

    _title(ax, 1.4, 4.55, 'Turning a point about the origin')
    ax.text(1.2, -1.95, "x' = x·cos(theta) − y·sin(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')
    ax.text(1.2, -2.5, "y' = x·sin(theta) + y·cos(theta)", fontsize=10.5,
            ha='center', color=INK, family='monospace')
    _save(fig, 'rotation.svg')


FIGURES = (arm, one_joint, two_joints, rotation, joining, flipping, carrying,
           three_joints)

if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for figure in FIGURES:
        figure()
    print(f'wrote {len(FIGURES)} diagrams to {OUT_DIR}')
