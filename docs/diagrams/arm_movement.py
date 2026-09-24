"""Generate the diagrams used in docs/08_arm-movement/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/arm-movement/<doc-name>/.

Three of the five are computed on the repo's own arm, the two-link planar arm of
docs/03_arm/01_overview.md: L1 = 3 m, L2 = 2 m, both joints revolute. That arm
was chosen there because every number in it can be checked by hand, and the same
property is what makes it useful here. Its reachable set is the annulus between
1 m and 5 m, its Jacobian determinant is exactly L1 * L2 * sin(q2), and its two
inverse-kinematics solutions differ only in the sign of q2. Nothing below is a
sketch of a shape; every curve is the arithmetic.

The joint speed limit drawn on the singularity picture is 180 degrees per second,
which is the value the official Universal Robots description package gives for
every joint of a UR5e, in config/ur5e/joint_limits.yaml.

Run with:  pixi run python docs/diagrams/arm_movement.py
"""

import math
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,  # noqa: E402
                                Polygon, Rectangle, Wedge)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'arm-movement'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PURPLE: str = '#7b5aa6'
GREY: str = '#9a9a9a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'
PALE_PURPLE: str = '#ece4f5'
PALE_GREY: str = '#eeeeee'
PALE_RED: str = '#fbe4e8'

L1: float = 3.0
L2: float = 2.0


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def _fk(q1: float, q2: float) -> tuple[float, float]:
    """Where the gripper is, for the repo's two-link arm, in metres."""
    return (L1 * math.cos(q1) + L2 * math.cos(q1 + q2),
            L1 * math.sin(q1) + L2 * math.sin(q1 + q2))


def _ik(x: float, y: float, elbow: int = 1) -> tuple[float, float]:
    """The two joint angles that put the gripper at (x, y). elbow is +1 or -1."""
    c2: float = (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q2: float = elbow * math.acos(max(-1.0, min(1.0, c2)))
    q1: float = math.atan2(y, x) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
    return q1, q2


def _draw_arm(ax, q1: float, q2: float, colour: str = BLUE, lw: float = 3.4,
              alpha: float = 1.0, zorder: int = 5) -> None:
    """The two links and the three joints, drawn from the base at the origin."""
    ex, ey = L1 * math.cos(q1), L1 * math.sin(q1)
    tx, ty = _fk(q1, q2)
    ax.plot([0, ex, tx], [0, ey, ty], color=colour, lw=lw, alpha=alpha,
            solid_capstyle='round', zorder=zorder)
    for px, py in ((0.0, 0.0), (ex, ey)):
        ax.add_patch(Circle((px, py), 0.13, facecolor='white', edgecolor=colour,
                            lw=1.8, alpha=alpha, zorder=zorder + 1))
    ax.add_patch(Circle((tx, ty), 0.10, facecolor=colour, edgecolor=colour,
                        lw=1.0, alpha=alpha, zorder=zorder + 1))


# --------------------------------------------------------------------------
# 01_overview.md
# --------------------------------------------------------------------------

def kinds_of_move() -> None:
    """One peg-into-hole task, cut into the five kinds of move it really contains.

    The idea this picture carries is that the kind of move is a property of the
    segment and not of the task. People pick one planner and use it from the
    home position to the bottom of the hole, and the segments at the two ends
    want opposite things: the long segment wants freedom to detour, and the last
    twenty millimetres want no freedom at all.
    """
    fig = plt.figure(figsize=(15.2, 7.9))
    grid = fig.add_gridspec(2, 5, height_ratios=[1.45, 1.0], hspace=0.05,
                            wspace=0.50, bottom=0.17)

    ax = fig.add_subplot(grid[0, :])
    ax.set_xlim(-0.4, 13.2)
    ax.set_ylim(-0.9, 8.4)
    ax.axis('off')
    ax.set_aspect('equal')

    ax.add_patch(Rectangle((-0.2, -0.55), 13.2, 0.55, facecolor=PALE_GREY,
                           edgecolor=GREY, lw=1.0, zorder=1))
    ax.add_patch(Rectangle((9.6, 0.0), 2.6, 1.5, facecolor=PALE_GREY,
                           edgecolor=GREY, lw=1.2, zorder=2))
    ax.add_patch(Rectangle((10.72, 0.55), 0.36, 0.95, facecolor='white',
                           edgecolor=INK, lw=1.2, zorder=3))
    ax.text(9.35, 0.75, 'the hole', fontsize=10.0, color=INK, ha='right',
            va='center')
    ax.annotate('', xy=(10.68, 0.9), xytext=(9.45, 0.78),
                arrowprops=dict(arrowstyle='->', color=GREY, lw=1.0))

    ax.add_patch(Rectangle((4.3, 0.0), 1.5, 3.4, facecolor=PALE_RED,
                           edgecolor=RED, lw=1.3, zorder=2))
    ax.text(5.05, 3.68, 'a clamp in the way', fontsize=10.0, color=RED,
            ha='center')

    free = np.array([[0.6, 5.6], [2.0, 6.9], [3.8, 7.3], [5.6, 6.9], [7.2, 6.0],
                     [8.3, 5.0], [8.9, 4.2]])
    ax.plot(free[:, 0], free[:, 1], color=BLUE, lw=3.2, zorder=4)
    ax.plot([8.9, 10.9], [4.2, 2.9], color=PURPLE, lw=3.2, zorder=4)
    ax.plot([10.9, 10.9], [2.9, 1.62], color=ORANGE, lw=3.2, zorder=4)
    ax.plot([10.9, 10.9], [1.62, 1.05], color=GREEN, lw=4.2, zorder=4)
    ax.plot([10.9, 10.9], [1.05, 0.62], color=RED, lw=4.2, zorder=4)

    ax.add_patch(Rectangle((10.74, 0.62), 0.32, 1.9, facecolor=PALE_BLUE,
                           edgecolor=BLUE, lw=1.4, zorder=5))

    ax.add_patch(Circle((0.6, 5.6), 0.15, facecolor='white', edgecolor=INK,
                        lw=1.5, zorder=6))
    ax.text(0.28, 5.25, 'home', fontsize=10.0, color=INK, ha='center', va='top')

    # One numbered badge per segment, placed clear of the route.
    badges = [(3.8, 7.3, '1', BLUE, 0.0, 0.75),
              (9.9, 3.55, '2', PURPLE, 0.55, 0.35),
              (10.9, 2.26, '3', ORANGE, 0.62, 0.0),
              (10.9, 1.33, '4', GREEN, 0.62, 0.0),
              (10.9, 0.84, '5', RED, 0.62, 0.0)]
    for bx, by, label, colour, dx, dy in badges:
        ax.add_patch(Circle((bx + dx, by + dy), 0.30, facecolor='white',
                            edgecolor=colour, lw=2.0, zorder=7))
        ax.text(bx + dx, by + dy, label, fontsize=11.5, color=colour,
                ha='center', va='center', weight='bold', zorder=8)

    ax.set_title('One peg into one hole, and the five different moves it takes',
                 fontsize=13.2, color=INK, pad=10)

    cards = [
        ('1', BLUE, 'free move',
         'Anywhere that is not a collision.\nThe path\'s shape does not matter,\n'
         'so this is the only segment a\nsampling planner is right for.'),
        ('2', PURPLE, 'straight line',
         'The tool travels in a line a person\ncan predict, above the fixture\n'
         'rather than through it. Wanted\nbecause somebody signs it off.'),
        ('3', ORANGE, 'servoed',
         'The camera watches the hole and\ncorrects sideways as the tool comes\n'
         'down. Covers a fixture that has\nmoved since it was taught.'),
        ('4', GREEN, 'guarded',
         'Move down until the force sensor\nsays something is there, then stop.\n'
         'Finds the surface without needing\nto know where it is.'),
        ('5', RED, 'compliant',
         'Push with a chosen force rather\nthan to a chosen position. The only\n'
         'kind that survives the hole being\n0.3 mm from where you thought.'),
    ]

    for i, (num, colour, name, body) in enumerate(cards):
        cax = fig.add_subplot(grid[1, i])
        cax.set_xlim(0, 1)
        cax.set_ylim(0, 1)
        cax.axis('off')
        cax.add_patch(Rectangle((0.0, 0.86), 1.0, 0.035, facecolor=colour,
                                edgecolor='none'))
        cax.text(0.0, 0.76, f'{num}.  {name}', fontsize=12.0, color=colour,
                 ha='left', va='top', weight='bold')
        cax.text(0.0, 0.60, body, fontsize=9.3, color=INK, ha='left', va='top',
                 linespacing=1.8)

    fig.text(0.075, 0.115,
             'Segment 1 covers about 95 per cent of the distance and almost none of the '
             'difficulty. Segments 3 to 5 cover roughly the last 20 mm and\nalmost all of '
             'it. Choosing one kind of move for the whole task is the mistake, and it '
             'shows up either as a path nobody will sign off or\nas a controller that '
             'pushes until the peg breaks.',
             fontsize=10.6, color=INK, va='top', linespacing=1.9)

    _save(fig, 'overview', 'kinds-of-move.svg')


# --------------------------------------------------------------------------
# 02_reaching-and-reachability.md
# --------------------------------------------------------------------------

def workspace_hole() -> None:
    """Two poses the arm can reach, and a straight line between them that it cannot.

    Computed on the repo's own arm. Both ends sit at radius 4.9 m, well inside
    the 5 m outer limit. The straight line between them passes 0.851 m from the
    base, and the inner limit of the reachable set is 1.0 m, so 1.051 m of the
    path is outside the workspace while neither end is.
    """
    fig, ax = plt.subplots(figsize=(11.4, 7.4))
    ax.set_xlim(-7.4, 7.4)
    ax.set_ylim(-1.35, 6.35)
    ax.axis('off')
    ax.set_aspect('equal')

    ax.add_patch(Wedge((0, 0), L1 + L2, 0, 180, width=(L1 + L2) - (L1 - L2),
                       facecolor=PALE_GREEN, edgecolor=GREEN, lw=1.4, zorder=1))
    ax.add_patch(Wedge((0, 0), L1 - L2, 0, 180, facecolor=PALE_RED,
                       edgecolor=RED, lw=1.6, zorder=2))
    ax.plot([-(L1 + L2), L1 + L2], [0, 0], color=GREY, lw=1.0, zorder=3)

    ax.text(-3.35, 3.30, 'reachable:\n1.0 m to 5.0 m\nfrom the base',
            fontsize=10.8, color=GREEN, ha='center', va='center',
            linespacing=1.7, zorder=4)

    ang = math.radians(80.0)
    start = (4.9 * math.cos(ang), 4.9 * math.sin(ang))
    goal = (4.9 * math.cos(math.pi - ang), 4.9 * math.sin(math.pi - ang))

    # Only the start pose is drawn. At 4.9 m the elbow is almost straight, so
    # the goal pose is the same shape mirrored and drawing it adds no information.
    _draw_arm(ax, *_ik(*start, elbow=-1), colour=BLUE, lw=3.0, alpha=0.95)

    ax.plot([start[0], goal[0]], [start[1], goal[1]], color=ORANGE, lw=3.0,
            zorder=9)

    closest = 4.9 * math.cos(ang)
    half = math.sqrt((L1 - L2) ** 2 - closest ** 2)
    ax.plot([-half, half], [closest, closest], color=RED, lw=5.5, zorder=10)

    ax.plot([0, 0], [0, closest], color=INK, lw=1.1, ls=':', zorder=11)
    ax.plot([-0.14, 0.14], [closest, closest], color=INK, lw=1.4, zorder=11)
    ax.text(0.28, closest * 0.45, '0.851 m', fontsize=10.4, color=INK,
            ha='left', va='center', zorder=11)

    ax.annotate('1051 mm of this move\nis outside the workspace',
                xy=(-half * 0.7, closest), xytext=(-3.85, 0.62),
                fontsize=10.6, color=RED, ha='center', va='center',
                linespacing=1.7, zorder=13,
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))

    ax.text(5.55, 3.05, 'turning the base does not\nhelp: the hole is there in\n'
            'every direction at once',
            fontsize=10.2, color=INK, ha='center', va='center', linespacing=1.7)

    for point, name, ha in ((start, 'start', 'left'), (goal, 'goal', 'right')):
        ax.add_patch(Circle(point, 0.17, facecolor=ORANGE, edgecolor=INK,
                            lw=1.5, zorder=12))
        ax.text(point[0] + (0.34 if ha == 'left' else -0.34), point[1] + 0.30,
                name, fontsize=11.0, color=INK, ha=ha, zorder=12)

    ax.add_patch(Rectangle((-0.5, -0.62), 1.0, 0.5, facecolor=PALE_GREY,
                           edgecolor=GREY, lw=1.2, zorder=6))
    ax.text(0.0, -0.9, 'base', fontsize=9.6, color=MUTED, ha='center', va='top')

    ax.set_title('A move whose two ends are reachable and whose middle is not',
                 fontsize=13.0, color=INK, pad=10)

    fig.text(0.035, 0.045,
             'The repo\'s own two-link arm: L1 = 3 m, L2 = 2 m, so it can reach anything '
             'between 1 m and 5 m from the base and nothing else.\nBoth ends of this move '
             'are 4.9 m out, comfortably inside the outer limit, and a joint-space plan '
             'between them succeeds at once.\nAsk instead for a straight line and it fails '
             'in the middle, because the line passes 0.851 m from the base. Nothing about '
             'the two\ngoal poses tells you this, and checking each pose for reachability '
             'does not catch it.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'reaching-and-reachability', 'workspace-hole.svg')


def singularity_cost() -> None:
    """What holding a constant tool speed costs in joint speed, near full extension.

    For the repo's arm the tool's distance from the base is
    r = sqrt(L1^2 + L2^2 + 2*L1*L2*cos(q2)), so moving the tool outward at
    v metres per second needs the elbow to turn at v*r / (L1*L2*sin(q2)). The
    numerator is bounded and sin(q2) goes to zero, so the required joint speed
    goes to infinity while the tool speed asked for stays the same.
    """
    fig, ax = plt.subplots(figsize=(11.2, 6.6))

    gaps_mm = np.geomspace(0.05, 200.0, 400)
    v = 0.05  # 50 mm/s of tool speed, straight out along the radius
    speeds = []
    for gap in gaps_mm:
        r = (L1 + L2) - gap / 1000.0
        c2 = (r * r - L1 * L1 - L2 * L2) / (2 * L1 * L2)
        q2 = math.acos(max(-1.0, min(1.0, c2)))
        speeds.append(math.degrees(v * r / (L1 * L2 * math.sin(q2))))
    speeds = np.array(speeds)

    ax.plot(gaps_mm, speeds, color=BLUE, lw=2.6, zorder=5)
    ax.axhline(180.0, color=RED, lw=1.8, ls='--', zorder=4)
    ax.text(190.0, 200.0, 'a UR5e joint stops here: 180 °/s',
            fontsize=10.4, color=RED, ha='left', va='bottom')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(200.0, 0.05)
    ax.set_ylim(3.0, 900.0)
    ax.set_xlabel('how far the tool still is from full extension, in millimetres',
                  fontsize=10.6, color=INK)
    ax.set_ylabel('elbow speed needed, in degrees per second',
                  fontsize=10.6, color=INK)
    ax.set_xticks([200, 100, 50, 10, 5, 1, 0.5, 0.1])
    ax.set_xticklabels(['200', '100', '50', '10', '5', '1', '0.5', '0.1'])
    ax.set_yticks([3, 10, 30, 100, 180, 300, 900])
    ax.set_yticklabels(['3', '10', '30', '100', '180', '300', '900'])
    ax.tick_params(labelsize=9.6, colors=INK)
    ax.grid(True, which='major', color=PALE_GREY, lw=0.8, zorder=1)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)

    for gap, note in ((10.0, '10 mm out:\n18.5 °/s'), (1.0, '1 mm out:\n58.5 °/s'),
                      (0.1, '0.1 mm out:\n184.9 °/s')):
        r = (L1 + L2) - gap / 1000.0
        c2 = (r * r - L1 * L1 - L2 * L2) / (2 * L1 * L2)
        q2 = math.acos(max(-1.0, min(1.0, c2)))
        s = math.degrees(v * r / (L1 * L2 * math.sin(q2)))
        ax.plot([gap], [s], marker='o', color=INK, ms=6.0, zorder=6)
        ax.annotate(note, xy=(gap, s), xytext=(gap * 3.4, s * 0.40),
                    fontsize=10.0, color=INK, ha='center', va='top',
                    linespacing=1.6, zorder=6,
                    arrowprops=dict(arrowstyle='-', color=GREY, lw=0.9))

    ax.set_title('Holding the tool at 50 mm/s while the arm straightens',
                 fontsize=12.6, color=INK, pad=14)

    fig.text(0.055, -0.03,
             'Nothing has gone wrong here and nothing has hit anything. The tool speed '
             'asked for is the same all the way across;\nonly the arm\'s shape changed. The '
             'last tenth of a millimetre of reach costs more joint speed than the whole '
             'first 190 mm,\nand a UR5e runs out at 180 °/s. This is why "it is inside the '
             'workspace" is not the same as "the arm can do it".',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'reaching-and-reachability', 'singularity-cost.svg')


# --------------------------------------------------------------------------
# 03_planning-a-path.md
# --------------------------------------------------------------------------

def joint_vs_cartesian() -> None:
    """The same two poses, joined in joint space and joined in a straight line.

    Both ends sit at radius sqrt(17) = 4.123 m, so both have the same elbow angle
    of 70.53 degrees, and interpolating the joints linearly holds that angle the
    whole way. The tool therefore travels along an arc of radius 4.123 m while
    the straight line between the ends passes 3.536 m from the base. The gap
    between them is 0.588 m, at the midpoint, and it is where the obstacle lives.
    """
    fig, ax = plt.subplots(figsize=(10.0, 7.4))
    ax.set_xlim(-0.5, 6.6)
    ax.set_ylim(-0.75, 5.75)
    ax.axis('off')
    ax.set_aspect('equal')

    a = (4.0, 1.0)
    b = (1.0, 4.0)
    qa = _ik(*a, elbow=1)
    qb = _ik(*b, elbow=1)

    ts = np.linspace(0.0, 1.0, 400)
    arc = np.array([_fk(qa[0] + t * (qb[0] - qa[0]),
                        qa[1] + t * (qb[1] - qa[1])) for t in ts])

    mid_line = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    mid_arc = tuple(arc[len(arc) // 2])

    # The fixture sits on the straight line a quarter of the way along, where the
    # arc has already pulled 430 mm clear of it. Putting it at the midpoint would
    # cover the dimension arrow.
    fixture = (3.25, 1.75)
    ax.add_patch(Rectangle((fixture[0] - 0.20, fixture[1] - 0.20), 0.40, 0.40,
                           facecolor=PALE_RED, edgecolor=RED, lw=1.6, zorder=6))

    ax.plot([a[0], b[0]], [a[1], b[1]], color=PURPLE, lw=2.8, zorder=5)
    ax.plot(arc[:, 0], arc[:, 1], color=ORANGE, lw=2.8, zorder=5)

    ax.annotate('', xy=mid_arc, xytext=mid_line,
                arrowprops=dict(arrowstyle='<->', color=INK, lw=1.8,
                                shrinkA=0, shrinkB=0), zorder=10)
    ax.annotate('588 mm apart\nat the midpoint', xy=(2.70, 2.70),
                xytext=(1.30, 2.35), fontsize=10.6, color=INK, ha='center',
                va='center', linespacing=1.7, zorder=11,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))

    ax.annotate('a fixture 400 mm across,\nsitting on the straight line\n'
                'and 430 mm clear of the arc',
                xy=(fixture[0] + 0.19, fixture[1] + 0.13), xytext=(4.55, 2.35),
                fontsize=10.2, color=RED, ha='left', va='center',
                linespacing=1.7, zorder=11,
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

    ax.text(1.55, 0.62, 'straight line: 3.536 m\nfrom the base at its closest',
            fontsize=10.4, color=PURPLE, ha='left', va='center', linespacing=1.7)
    ax.text(3.15, 4.75, 'joints interpolated:\nan arc at 4.123 m, because\n'
            'the elbow angle never\nchanges between these two',
            fontsize=10.4, color=ORANGE, ha='left', va='center', linespacing=1.7)

    for point, name, dy in ((a, 'start', -0.36), (b, 'goal', 0.34)):
        ax.add_patch(Circle(point, 0.13, facecolor='white', edgecolor=INK,
                            lw=1.7, zorder=8))
        ax.text(point[0] + 0.26, point[1] + dy, name, fontsize=10.8, color=INK,
                ha='left', zorder=8)

    ax.add_patch(Circle((0, 0), 0.14, facecolor=PALE_GREY, edgecolor=GREY,
                        lw=1.4, zorder=3))
    ax.text(-0.22, -0.30, 'base', fontsize=9.8, color=MUTED, ha='center',
            va='top')

    ax.set_title('Two ways to get the tool from (4, 1) to (1, 4)',
                 fontsize=13.0, color=INK, pad=10)

    fig.text(0.03, 0.055,
             'Both ends are 4.123 m from the base, so both need the same elbow angle, and '
             'interpolating the joints holds that angle all the way:\nthe tool sweeps an '
             'arc rather than travelling in a line. The two paths are 588 mm apart at the '
             'midpoint. A planning scene holding this\nfixture accepts the arc and rejects '
             'the line, and the arm has not moved yet either time.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'planning-a-path', 'joint-vs-cartesian.svg')


# --------------------------------------------------------------------------
# 04_controlling-the-move.md
# --------------------------------------------------------------------------

def tolerance_not_enforced() -> None:
    """What joint_trajectory_controller checks by default, which is nothing.

    The commanded profile is a trapezoidal move of 60 degrees in 2 seconds. The
    achieved profile is that command through a first-order lag of 150 ms, which
    is an illustrative arm rather than a measured one; the shape is the point.
    The three numbers marked on the picture are not illustrative. They are the
    defaults in ros2_controllers' joint_trajectory_controller: constraints
    trajectory 0.0, constraints goal 0.0, and the header of tolerances.hpp says
    a tolerance of zero means no tolerance is applied.
    """
    fig, ax = plt.subplots(figsize=(11.8, 6.4))

    dt = 0.002
    t = np.arange(0.0, 3.0 + dt, dt)
    total, move_time, accel_time = 60.0, 2.0, 0.5
    peak = total / (move_time - accel_time)

    def commanded(tt: float) -> float:
        if tt <= 0:
            return 0.0
        if tt < accel_time:
            return 0.5 * (peak / accel_time) * tt * tt
        if tt < move_time - accel_time:
            return 0.5 * peak * accel_time + peak * (tt - accel_time)
        if tt < move_time:
            s = tt - (move_time - accel_time)
            return (0.5 * peak * accel_time + peak * (move_time - 2 * accel_time)
                    + peak * s - 0.5 * (peak / accel_time) * s * s)
        return total

    cmd = np.array([commanded(tt) for tt in t])
    tau = 0.15
    act = np.zeros_like(cmd)
    for i in range(1, len(t)):
        act[i] = act[i - 1] + (dt / tau) * (cmd[i - 1] - act[i - 1])

    ax.plot(t, cmd, color=BLUE, lw=2.6, label='commanded by the trajectory', zorder=5)
    ax.plot(t, act, color=ORANGE, lw=2.6, label='where the joint actually is', zorder=5)

    # The worst following error during the move, and where it happens.
    during = (t > 0.05) & (t < move_time)
    k = int(np.argmax(np.abs(cmd - act) * during))
    ax.annotate('', xy=(t[k], act[k]), xytext=(t[k], cmd[k]),
                arrowprops=dict(arrowstyle='<->', color=RED, lw=1.6))
    ax.annotate(f'{cmd[k] - act[k]:.1f}° behind the\ncommand, mid-move',
                xy=(t[k], (cmd[k] + act[k]) / 2), xytext=(0.78, 45.0),
                fontsize=10.2, color=RED, ha='center', va='center',
                linespacing=1.7,
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

    ax.axvline(move_time, color=GREY, lw=1.1, ls=':', zorder=3)
    ax.text(move_time - 0.04, 31.5, 'trajectory ends here', fontsize=9.8,
            color=MUTED, rotation=90, ha='right', va='bottom')

    end = np.argmin(np.abs(t - move_time))
    ax.plot([move_time], [act[end]], marker='o', color=INK, ms=6.5, zorder=6)
    ax.annotate(f'{total - act[end]:.1f}° short at the moment\nthe trajectory finishes',
                xy=(move_time, act[end]), xytext=(2.34, 44.0), fontsize=10.2,
                color=INK, ha='left', va='center', linespacing=1.6,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.3))

    ax.add_patch(Rectangle((2.06, 5.0), 0.90, 26.0, facecolor=PALE_RED,
                           edgecolor=RED, lw=1.3, zorder=7))
    ax.text(2.13, 29.2,
            'what the controller checks,\nwith the shipped defaults:\n\n'
            'constraints.trajectory = 0.0\nconstraints.goal = 0.0\n\n'
            'and zero means the tolerance\nis not applied. Both of the\n'
            'errors marked here pass.',
            fontsize=9.8, color=INK, ha='left', va='top', linespacing=1.7,
            zorder=8)

    ax.set_xlim(0.0, 3.0)
    ax.set_ylim(0.0, 68.0)
    ax.set_xlabel('seconds', fontsize=10.6, color=INK)
    ax.set_ylabel('joint angle, in degrees', fontsize=10.6, color=INK)
    ax.tick_params(labelsize=9.6, colors=INK)
    ax.legend(loc='lower right', fontsize=10.0, frameon=False,
              bbox_to_anchor=(1.0, 0.02))
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)

    ax.set_title('A move that is late, short, and reported as a success',
                 fontsize=12.8, color=INK, pad=14)

    fig.text(0.055, -0.02,
             'The arm here is an illustration: a 60° move in 2 s, followed through a 150 ms '
             'first-order lag. The defaults in the box are not.\nThey are what '
             'joint_trajectory_controller ships with, and they mean the controller never '
             'compares where the joint is with where\nthe trajectory said it should be. '
             'The goal is accepted once the trajectory runs out and the joint is slower '
             'than 0.01 rad/s.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'controlling-the-move', 'tolerance-not-enforced.svg')


def cycle_time_breakdown() -> None:
    """Where the seconds actually go in one pick and place.

    Every figure is the one computed in 09_the-cost-of-a-move.md, which sources
    the speeds from vendor manuals and says plainly which it had to assume.
    """
    fig, (bar, saving) = plt.subplots(1, 2, figsize=(13.4, 5.0),
                                      gridspec_kw={'width_ratios': [1.3, 1]})

    parts = [('motion', 6.16, BLUE), ('settling', 0.90, ORANGE),
             ('perception', 0.50, GREEN), ('gripper', 0.49, PURPLE),
             ('planning', 0.17, GREY)]
    left = 0.0
    for name, secs, colour in parts:
        bar.barh([0], [secs], left=left, height=0.5, color=colour, label=name)
        # only the wide segments can carry a label inside them; the narrow ones
        # are named by the legend and called out beneath instead.
        if secs > 0.8:
            bar.text(left + secs / 2, 0, f'{secs:.2f} s', ha='center', va='center',
                     fontsize=9.5, color='white')
        left += secs
    bar.set_xlim(0, 8.6)
    bar.set_ylim(-1.3, 1.1)
    bar.set_yticks([])
    bar.set_xlabel('seconds in one pick-and-place cycle', fontsize=9.5)
    bar.legend(fontsize=8.8, frameon=False, ncol=5, loc='upper center')
    bar.set_title('8.216 s, or 438 picks an hour', fontsize=11.5, color=INK, pad=12)
    for side in ('top', 'right', 'left'):
        bar.spines[side].set_visible(False)
    bar.spines['bottom'].set_color(GREY)
    bar.text(0, -0.72, 'perception 0.50 s   ·   gripper 0.49 s   ·   planning 0.17 s',
             fontsize=9.0, color=MUTED)
    bar.text(0, -1.05, 'Settling alone costs 1.8x what the model costs.',
             fontsize=9.6, color=INK)

    moves = [('make the model\nten times faster', 0.450, GREY),
             ('overlap computing\nwith motion', 0.672, GREEN),
             ('drop the second\nviewpoint', 1.057, GREEN)]
    y = np.arange(len(moves))
    saving.barh(y, [m[1] for m in moves], height=0.55, color=[m[2] for m in moves])
    for yi, (_, secs, _) in zip(y, moves):
        saving.text(secs + 0.03, yi, f'{secs:.3f} s', va='center', fontsize=9.6, color=INK)
    saving.set_yticks(y)
    saving.set_yticklabels([m[0] for m in moves], fontsize=9.4, linespacing=1.5)
    saving.set_xlim(0, 1.45)
    saving.set_xlabel('seconds saved', fontsize=9.5)
    saving.set_title('What each change is worth', fontsize=11.5, color=INK, pad=12)
    for side in ('top', 'right'):
        saving.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        saving.spines[side].set_color(GREY)

    fig.text(0.5, -0.06,
             'Dropping one viewpoint is worth 2.35 times a tenfold model speed-up. And '
             "MoveIt's shipped 0.1 velocity scaling, one line of\nconfiguration, turns "
             '2.887 s of joint moves into 22.387 s — costing 43 times what the model '
             'choice is worth.',
             fontsize=10.2, color=INK, ha='center', va='top', linespacing=1.8)
    _save(fig, 'the-cost-of-a-move', 'where-the-seconds-go.svg')


def the_cost_ladder() -> None:
    """Why you order feasibility tests cheapest first.

    Timings measured over two million candidates in C on an Apple M4, against
    twenty obstacle footprints; the last two rungs are MoveIt's own defaults.
    """
    fig, ax = plt.subplots(figsize=(11.8, 5.6))

    rungs = [('approach direction\nagainst a cone', 0.2e-9, 83.4, GREEN),
             ('distance against the\nreach envelope', 0.4e-9, 30.1, GREEN),
             ('clearance against the\nnearest obstacle', 10e-9, 13.1, BLUE),
             ('line of sight, a ray\nagainst 20 footprints', 49e-9, 41.7, BLUE),
             ('inverse kinematics', 50e-3, None, ORANGE),
             ('a full motion plan', 5.0, None, RED)]

    y = np.arange(len(rungs))[::-1]
    ax.barh(y, [r[1] for r in rungs], height=0.55, color=[r[3] for r in rungs])
    for yi, (_, cost, rejected, colour) in zip(y, rungs):
        label = f'{cost * 1e9:.1f} ns' if cost < 1e-6 else f'{cost * 1e3:.0f} ms' if cost < 1 else f'{cost:.0f} s'
        ax.text(cost * 1.6, yi, label, va='center', fontsize=9.8, color=INK)
        if rejected is not None:
            ax.text(cost * 1.6, yi - 0.30, f'rejects {rejected:.1f}%', va='center',
                    fontsize=8.6, color=MUTED)

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rungs], fontsize=9.6, linespacing=1.5)
    ax.set_xscale('log')
    ax.set_xlim(1e-10, 2e3)
    ax.set_xlabel('seconds per candidate, log scale', fontsize=9.5)
    ax.set_title('Ten orders of magnitude between the cheapest test and the dearest',
                 fontsize=11.5, color=INK, pad=12)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)

    fig.text(0.06, -0.09,
             'A motion plan costs twenty-five thousand million times what an approach-'
             'direction test costs. In the measured run the four cheap tests\nremoved '
             '69.2% of candidates before a single ray was cast, and casting rays at '
             'everything would have cost 1.14 ms against 0.46 ms\nfor the whole cascade.',
             fontsize=10.2, color=INK, va='top', linespacing=1.8)
    _save(fig, 'reaching-and-reachability', 'the-cost-ladder.svg')


if __name__ == '__main__':
    kinds_of_move()
    workspace_hole()
    singularity_cost()
    joint_vs_cartesian()
    tolerance_not_enforced()
    cycle_time_breakdown()
    the_cost_ladder()
