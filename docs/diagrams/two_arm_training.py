"""Generate the diagrams used in docs/10_two-arm-training/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/two-arm-training/<doc-name>/.

Run with:  pixi run python docs/diagrams/two_arm_training.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'two-arm-training'

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


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def _arm(ax: Axes, base: tuple[float, float], elbow: tuple[float, float],
         hand: tuple[float, float], colour: str, alpha: float = 1.0) -> None:
    """Draw one arm as a base, two links and a gripper."""
    ax.add_patch(Rectangle((base[0] - 0.42, base[1] - 0.22), 0.84, 0.44,
                           facecolor=colour, edgecolor='none', alpha=0.75 * alpha))
    ax.plot([base[0], elbow[0], hand[0]], [base[1], elbow[1], hand[1]],
            color=colour, lw=2.6, solid_capstyle='round', zorder=3, alpha=alpha)
    ax.plot([hand[0]], [hand[1]], marker='o', markersize=6, color=colour, zorder=4,
            alpha=alpha)


# --------------------------------------------------------------------------
# when-two-arms-help.md
# --------------------------------------------------------------------------

def fixture_or_arm() -> None:
    """Show why a fixture is cheap per product and expensive per variant.

    The point of the picture is that the decision turns on variety, not on
    capability, which is the argument the document makes in words.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.2, 6.4), facecolor='white')
    ax.set_xlim(-1.5, 15.6)
    ax.set_ylim(-2.6, 12.6)
    ax.axis('off')

    ax.add_patch(FancyArrowPatch((0, 0), (11.4, 0), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.add_patch(FancyArrowPatch((0, 0), (0, 11.4), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.text(5.6, -1.1, 'how many product variants the cell must handle  →',
            ha='center', fontsize=10, color=INK)
    ax.text(-0.75, 5.7, 'total cost  →', rotation=90, ha='center', va='center',
            fontsize=10, color=INK)

    # A fixture is cheap to start and costs another fixture for every variant.
    variants: np.ndarray = np.arange(0, 11)
    fixture: np.ndarray = 0.7 + 0.95 * variants
    ax.step(variants, fixture, where='post', color=BLUE, lw=2.4, zorder=3)
    ax.text(10.4, 10.4, 'one arm and a fixture\na new fixture for every variant,\n'
            'plus somewhere to store it', fontsize=9.2, color=BLUE, ha='left',
            va='center', linespacing=1.55)

    # A second arm costs a lot once, and then nothing per variant.
    ax.plot([0, 10.6], [6.2, 6.9], color=ORANGE, lw=2.4, zorder=3)
    ax.text(10.8, 6.6, 'two arms\nexpensive once, then\nalmost free per variant',
            fontsize=9.2, color=ORANGE, ha='left', va='center', linespacing=1.55)

    crossing: float = 5.8
    ax.plot([crossing, crossing], [0, 6.55], color=MUTED, lw=1.1,
            linestyle=(0, (4, 4)), zorder=1)
    ax.plot([crossing], [6.55], marker='o', markersize=8, color=RED, zorder=5)
    ax.annotate('the crossing point is the whole\nargument — and nobody can tell\n'
                'you where it is for your task',
                xy=(crossing + 0.12, 6.3), xytext=(7.0, 2.9), fontsize=9.0,
                color=RED, ha='left', va='center', linespacing=1.55,
                arrowprops={'arrowstyle': '->', 'color': RED, 'lw': 1.1,
                            'connectionstyle': 'arc3,rad=-0.25'})

    ax.add_patch(Rectangle((0.05, 0.05), crossing - 0.05, 6.4, facecolor=PALE_BLUE,
                           edgecolor='none', alpha=0.5, zorder=0))
    ax.add_patch(Rectangle((crossing, 0.05), 10.55 - crossing, 6.85,
                           facecolor=PALE_ORANGE, edgecolor='none', alpha=0.5,
                           zorder=0))

    ax.text(-1.5, 12.2, 'The trade-off turns on variety, not on capability',
            fontsize=11.5, color=INK)
    ax.text(-1.5, -2.2, 'Both lines are shapes, not measurements: no published '
            'figures compare the two this way. What is published is that '
            'fixtureless assembly pays off\n"especially for a multi-style '
            'production line" — which is this picture, stated by engineers who '
            'build the cells.', fontsize=9.3, color=MUTED, va='top',
            linespacing=1.6)
    _save(fig, 'when-two-arms-help', 'fixture-or-arm.svg')


# --------------------------------------------------------------------------
# overview.md
# --------------------------------------------------------------------------

def coordination() -> None:
    """Draw the two kinds of coupling, and the handover that passes through both."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.2, 5.4), facecolor='white')
    ax.set_xlim(-0.6, 26.4)
    ax.set_ylim(-3.4, 7.6)
    ax.axis('off')

    ax.text(-0.6, 7.2, 'Out of scope: two arms doing unrelated things in one cell. '
            'That is two single-arm problems and a collision check.',
            fontsize=9.3, color=MUTED)

    panels: list[tuple[str, str, str, str]] = [
        ('loosely coupled', 'one holds, one works',
         'the arms have different roles, and\nthe coupling is mild: the working arm\n'
         'needs to know where the part is',
         'the common case, and the one\nworth designing for on purpose'),
        ('tightly coupled', 'both hold one thing',
         'the arms, the object and the table\nform a loop, so neither arm is\n'
         'free to be commanded on its own',
         'position control alone will squeeze\nor fight: control the pair together'),
        ('the transition', 'the handover',
         'loosely coupled, then tightly coupled\nfor an instant, then loosely\n'
         'coupled again',
         'all the difficulty is in the release,\nand the release is a force problem'),
    ]
    for index, (kind, title, what, why) in enumerate(panels):
        x0: float = index * 9.0
        colour: str = [GREEN, ORANGE, PURPLE][index]
        fill: str = [PALE_GREEN, PALE_ORANGE, PALE_PURPLE][index]
        ax.add_patch(Rectangle((x0, 0.4), 7.8, 5.5, facecolor=fill,
                               edgecolor=colour, lw=1.4))
        ax.text(x0 + 3.9, 6.5, title, ha='center', fontsize=11.5, color=INK)
        ax.text(x0 + 3.9, 5.65, kind, ha='center', fontsize=9.0, color=colour)
        ax.plot([x0 + 0.5, x0 + 7.3], [0.9, 0.9], color=MUTED, lw=1.0)

        left_base: tuple[float, float] = (x0 + 1.6, 1.25)
        right_base: tuple[float, float] = (x0 + 6.2, 1.25)
        if index == 0:
            _arm(ax, left_base, (x0 + 1.6, 3.1), (x0 + 3.0, 3.6), colour)
            _arm(ax, right_base, (x0 + 6.2, 4.0), (x0 + 4.6, 4.5), colour)
            ax.add_patch(Rectangle((x0 + 3.0, 2.9), 2.0, 1.3, facecolor=INK,
                                   edgecolor='none', alpha=0.55))
            ax.text(x0 + 2.3, 2.3, 'holds', ha='center', fontsize=8.5, color=colour)
            ax.text(x0 + 5.0, 4.9, 'works', ha='center', fontsize=8.5, color=colour)
        elif index == 1:
            _arm(ax, left_base, (x0 + 1.6, 3.1), (x0 + 2.7, 3.6), colour)
            _arm(ax, right_base, (x0 + 6.2, 3.1), (x0 + 5.1, 3.6), colour)
            ax.add_patch(Rectangle((x0 + 2.7, 3.2), 2.4, 0.9, facecolor=INK,
                                   edgecolor='none', alpha=0.55))
            for sign, tip in ((1, x0 + 3.5), (-1, x0 + 4.3)):
                ax.add_patch(FancyArrowPatch((tip - 0.5 * sign, 3.65), (tip, 3.65),
                                             arrowstyle='-|>', mutation_scale=9,
                                             color='white', lw=1.4))
            ax.text(x0 + 3.9, 2.4, 'forces that go nowhere', ha='center',
                    fontsize=8.5, color=colour)
        else:
            _arm(ax, left_base, (x0 + 1.6, 3.1), (x0 + 3.2, 3.8), colour)
            _arm(ax, right_base, (x0 + 6.2, 3.1), (x0 + 4.6, 3.8), colour)
            ax.add_patch(Rectangle((x0 + 3.2, 3.4), 1.4, 0.8, facecolor=INK,
                                   edgecolor='none', alpha=0.55))
            ax.add_patch(FancyArrowPatch((x0 + 3.3, 4.6), (x0 + 4.5, 4.6),
                                         arrowstyle='-|>', mutation_scale=11,
                                         color=colour, lw=1.6))
            ax.text(x0 + 3.9, 4.82, 'passes across', ha='center', fontsize=8.5,
                    color=colour)
            ax.text(x0 + 3.9, 2.4, 'let go too early: it drops\ntoo late: they fight',
                    ha='center', fontsize=8.5, color=colour, linespacing=1.4)

        ax.text(x0 + 3.9, -0.1, what, ha='center', va='top', fontsize=8.8,
                color=INK, linespacing=1.5)
        ax.text(x0 + 3.9, -2.3, why, ha='center', va='top', fontsize=8.5,
                color=colour, linespacing=1.45)

    _save(fig, 'overview', 'coordination.svg')


def layers() -> None:
    """Draw the five layers, with the one a second arm adds picked out.

    Traced through one concrete job — screwdriving and packing — so that the
    new layer is a real decision rather than an abstract box.
    """
    rows: list[tuple[str, str, str, str, bool]] = [
        ('what to do next', 'fetch the housing, fit the board, drive four\n'
         'screws, clip the lid, put it in the tray',
         'behaviour tree  ·  state machine', PURPLE, False),
        ('which arm does what', 'the left holds the housing and re-angles it;\n'
         'the right picks and drives; they swap only at the end',
         'almost always written by hand', RED, True),
        ('which skill, and where', '"drive a screw" becomes: this screw, from\n'
         'that feeder, into that hole',
         'learned perception feeding a planner  ·  a VLA', BLUE, False),
        ('how to move', 'two paths that must miss the fixture, the\n'
         'workpiece, and each other, and arrive on time',
         'plan the pair as one robot  ·  learned by the policy', GREEN, False),
        ('how to touch', 'engage the thread without cross-threading, and\n'
         'hold firm against the push without shifting the part',
         'force control, with two different stiffnesses', ORANGE, False),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.4, 6.8), facecolor='white')
    ax.set_xlim(0, 30)
    ax.set_ylim(-1.8, 4.5 * len(rows) + 1.0)
    ax.axis('off')
    fills: dict[str, str] = {PURPLE: PALE_PURPLE, BLUE: PALE_BLUE, GREEN: PALE_GREEN,
                             ORANGE: PALE_ORANGE, RED: PALE_RED}

    ax.text(0.2, 4.5 * len(rows) + 0.3,
            'One job — screwdriving and packing — through the five layers. '
            'The second layer is the one a second arm adds.',
            fontsize=11, color=INK)

    for index, (title, doing, methods, colour, is_new) in enumerate(rows):
        y: float = (len(rows) - 1 - index) * 4.3
        ax.add_patch(Rectangle((0.2, y), 5.8, 3.3, facecolor=fills[colour],
                               edgecolor=colour, lw=2.8 if is_new else 1.5))
        ax.text(3.1, y + 1.7, title, ha='center', fontsize=10.5, color=INK)
        if is_new:
            ax.text(3.1, y + 0.55, 'NEW WITH TWO ARMS', ha='center', fontsize=7.6,
                    color=RED)
        ax.text(6.8, y + 1.7, doing, ha='left', va='center', fontsize=9.0,
                color=INK, linespacing=1.5)
        ax.text(19.6, y + 1.7, methods, ha='left', va='center', fontsize=8.8,
                color=colour)
        if index < len(rows) - 1:
            ax.add_patch(FancyArrowPatch((3.1, y), (3.1, y - 1.0), arrowstyle='-|>',
                                         mutation_scale=12, color=INK, lw=1.2))

    ax.text(0.2, -1.4, 'Only the top layer is unchanged by the second arm. '
            'Every other layer gains a question it did not have before.',
            fontsize=9.5, color=INK)
    _save(fig, 'overview', 'layers.svg')


# --------------------------------------------------------------------------
# programmed-methods.md
# --------------------------------------------------------------------------

def separate_plans_collide() -> None:
    """Draw the classic two-arm bug, in two pictures.

    Each plan is collision-free against the other arm WHERE IT IS NOW, and the
    two together collide, because neither plan knew the other was moving.
    """
    fig: Figure
    axes: np.ndarray
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4), facecolor='white')

    # Each path is the gripper's trajectory, starting from where that hand is.
    left_path: list[tuple[float, float]] = [(2.6, 3.5), (3.8, 4.15), (5.0, 4.4)]
    right_path: list[tuple[float, float]] = [(8.4, 3.5), (6.8, 4.2), (5.2, 4.4)]

    for index, ax in enumerate(axes):
        ax.set_xlim(-0.4, 12.6)
        ax.set_ylim(-0.6, 7.6)
        ax.axis('off')
        ax.plot([0.4, 9.6], [0.9, 0.9], color=MUTED, lw=1.0)

        if index == 0:
            ax.set_title('how the left arm was planned', fontsize=10.5, color=BLUE,
                         pad=10)
            # The right arm is an obstacle at the pose it happens to be in now.
            _arm(ax, (8.4, 1.25), (8.4, 2.6), (8.4, 3.5), GREY)
            ax.text(8.9, 2.3, 'the right arm, treated\nas an obstacle where\n'
                    'it is standing now', ha='left', va='center', fontsize=8.4,
                    color=MUTED, linespacing=1.45)
            xs: list[float] = [p[0] for p in right_path]
            ys: list[float] = [p[1] for p in right_path]
            ax.plot(xs, ys, color=GREY, lw=1.6, linestyle=(0, (4, 4)), zorder=2)
            ax.text(6.4, 5.5, 'where it is about to go —\nnot considered at all',
                    ha='center', fontsize=8.4, color=MUTED, linespacing=1.45)

            _arm(ax, (1.6, 1.25), (1.6, 2.9), (2.6, 3.5), BLUE)
            xs = [p[0] for p in left_path]
            ys = [p[1] for p in left_path]
            ax.plot(xs, ys, color=BLUE, lw=2.2, zorder=3,
                    linestyle=(0, (1, 1.6)), dash_capstyle='round')
            ax.plot([5.0], [4.4], marker='o', markersize=7, color=BLUE, zorder=4)
            ax.text(3.9, 2.2, 'the path planned\nfor its gripper', ha='center',
                    fontsize=8.4, color=BLUE, linespacing=1.45)
            ax.text(5.0, 6.6, "the plan is collision-free.\nSo is the right arm's, "
                    'planned the same way.', ha='center', fontsize=9.0, color=BLUE,
                    linespacing=1.5)
        else:
            ax.set_title('what happens when both run', fontsize=10.5, color=RED,
                         pad=10)
            _arm(ax, (1.6, 1.25), (2.6, 3.0), (4.2, 4.1), BLUE)
            _arm(ax, (8.4, 1.25), (7.4, 3.0), (5.8, 4.1), ORANGE)
            ax.add_patch(Circle((5.0, 4.3), 1.05, facecolor=PALE_RED,
                                edgecolor=RED, lw=2.0, zorder=5))
            ax.text(5.0, 4.3, 'CRASH', ha='center', va='center', fontsize=9.5,
                    color=RED, zorder=6)
            ax.text(1.6, 0.35, 'left arm', ha='center', fontsize=8.4, color=BLUE)
            ax.text(8.4, 0.35, 'right arm', ha='center', fontsize=8.4, color=ORANGE)
            ax.text(5.0, 6.6, 'both arms arrive in the same place\nat the same '
                    'moment', ha='center', fontsize=9.0, color=RED, linespacing=1.5)

    fig.text(0.5, 0.055, 'The fix is to plan the two arms as one robot over all '
             'twelve joints — which is correct, and expensive.',
             ha='center', fontsize=9.8, color=INK)
    fig.text(0.5, 0.005, 'MoveIt 2 ships no configuration that does this: its '
             'dual-arm example defines two planning groups and plans one at a time.',
             ha='center', fontsize=9.3, color=MUTED)
    _save(fig, 'programmed-methods', 'separate-plans-collide.svg')


def internal_force() -> None:
    """Where the six leftover degrees of freedom go: into squeeze."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.8, 6.2), facecolor='white')
    ax.set_xlim(-0.6, 27.0)
    ax.set_ylim(-2.8, 9.4)
    ax.axis('off')

    ax.text(-0.6, 9.0, 'Twelve joints driving a six-degree-of-freedom object. '
            'The other six do not disappear.', fontsize=11.5, color=INK)

    # The arithmetic, as one bar splitting into two.
    ax.add_patch(Rectangle((0.2, 5.4), 11.4, 1.5, facecolor=PALE_BLUE,
                           edgecolor=BLUE, lw=1.6))
    ax.text(5.9, 6.15, '12 joint degrees of freedom   (two six-joint arms)',
            ha='center', va='center', fontsize=10, color=BLUE)

    ax.add_patch(Rectangle((0.2, 2.6), 5.5, 1.5, facecolor=PALE_GREEN,
                           edgecolor=GREEN, lw=1.6))
    ax.text(2.95, 3.35, "6  the object's motion", ha='center', va='center',
            fontsize=10, color=GREEN)
    ax.text(2.95, 1.9, 'where the thing you are\nholding actually goes',
            ha='center', va='top', fontsize=8.8, color=GREEN, linespacing=1.45)

    ax.add_patch(Rectangle((6.1, 2.6), 5.5, 1.5, facecolor=PALE_RED,
                           edgecolor=RED, lw=1.6))
    ax.text(8.85, 3.35, '6  internal force', ha='center', va='center',
            fontsize=10, color=RED)
    ax.text(8.85, 1.9, 'squeeze and stretch that\nproduce no motion at all',
            ha='center', va='top', fontsize=8.8, color=RED, linespacing=1.45)

    for x_from, x_to, colour in ((5.0, 2.95, GREEN), (6.8, 8.85, RED)):
        ax.add_patch(FancyArrowPatch((x_from, 5.3), (x_to, 4.2), arrowstyle='-|>',
                                     mutation_scale=12, color=colour, lw=1.5))

    # The same thing as a picture: two arms squeezing one object.
    ax.plot([13.6, 25.8], [1.0, 1.0], color=MUTED, lw=1.0)
    _arm(ax, (15.2, 1.35), (15.2, 3.4), (16.8, 4.2), ORANGE)
    _arm(ax, (24.2, 1.35), (24.2, 3.4), (22.6, 4.2), ORANGE)
    ax.add_patch(Rectangle((16.8, 3.6), 5.8, 1.2, facecolor=INK, edgecolor='none',
                           alpha=0.55))
    for tip, sign in ((18.6, 1), (20.8, -1)):
        ax.add_patch(FancyArrowPatch((tip - 1.0 * sign, 4.2), (tip, 4.2),
                                     arrowstyle='-|>', mutation_scale=11,
                                     color='white', lw=1.8))
    ax.text(19.7, 5.6, 'a millimetre of disagreement between\n'
            'the two position commands becomes\nan enormous force in here',
            ha='center', va='bottom', fontsize=9.0, color=RED, linespacing=1.55)
    ax.text(19.7, 0.3, 'and no camera will show it to you', ha='center',
            fontsize=8.8, color=MUTED)

    ax.text(-0.6, -1.1, 'You cannot choose not to have the internal force. You can '
            'only choose whether you command it deliberately — by telling the\n'
            'controller where the object should go AND how hard to squeeze it — '
            'or discover it when something is crushed.',
            fontsize=9.6, color=INK, va='top', linespacing=1.7)
    _save(fig, 'programmed-methods', 'internal-force.svg')


# --------------------------------------------------------------------------
# learned-methods.md
# --------------------------------------------------------------------------

def one_policy_or_two() -> None:
    """Draw both architectures, with the one measurement anyone has published."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.0, 6.4), facecolor='white')
    ax.set_xlim(-0.6, 27.0)
    ax.set_ylim(-4.6, 10.2)
    ax.axis('off')

    ax.text(-0.6, 9.8, 'Two ways to drive two arms with a network, and what '
            'happened when somebody compared them', fontsize=11.5, color=INK)

    # Left: one joint policy.
    ax.add_patch(Rectangle((0.2, 4.4), 10.4, 4.4, facecolor=PALE_GREEN,
                           edgecolor=GREEN, lw=1.5))
    ax.text(5.4, 8.3, 'one policy for both arms', ha='center', fontsize=10.5,
            color=INK)
    ax.add_patch(Rectangle((3.4, 6.2), 4.0, 1.4, facecolor='white',
                           edgecolor=GREEN, lw=1.6))
    ax.text(5.4, 6.9, 'one network', ha='center', va='center', fontsize=9.5,
            color=GREEN)
    ax.text(5.4, 6.0, '14 numbers out: 6 joints and a gripper, twice over',
            ha='center', va='top', fontsize=8.6, color=INK)
    for x in (3.9, 6.9):
        ax.add_patch(FancyArrowPatch((x, 5.7), (x, 5.1), arrowstyle='-|>',
                                     mutation_scale=10, color=GREEN, lw=1.3))
    ax.text(3.9, 4.85, 'left arm', ha='center', fontsize=8.6, color=GREEN)
    ax.text(6.9, 4.85, 'right arm', ha='center', fontsize=8.6, color=GREEN)

    # Right: two policies with a link.
    ax.add_patch(Rectangle((13.0, 4.4), 10.4, 4.4, facecolor=PALE_BLUE,
                           edgecolor=BLUE, lw=1.5))
    ax.text(18.2, 8.3, 'two policies, one feeding the other', ha='center',
            fontsize=10.5, color=INK)
    for x, label in ((15.3, 'leader net'), (21.1, 'follower net')):
        ax.add_patch(Rectangle((x - 1.7, 6.2), 3.4, 1.4, facecolor='white',
                               edgecolor=BLUE, lw=1.6))
        ax.text(x, 6.9, label, ha='center', va='center', fontsize=9.5, color=BLUE)
    ax.add_patch(FancyArrowPatch((17.0, 6.9), (19.4, 6.9), arrowstyle='-|>',
                                 mutation_scale=11, color=BLUE, lw=1.5))
    ax.text(18.2, 7.2, 'its prediction', ha='center', fontsize=8.2, color=BLUE)
    for x in (15.3, 21.1):
        ax.add_patch(FancyArrowPatch((x, 6.2), (x, 5.2), arrowstyle='-|>',
                                     mutation_scale=10, color=BLUE, lw=1.3))
    ax.text(15.3, 4.85, 'left arm', ha='center', fontsize=8.6, color=BLUE)
    ax.text(21.1, 4.85, 'right arm', ha='center', fontsize=8.6, color=BLUE)

    # The measurement.
    ax.text(5.4, 3.3, '16.8%', ha='center', fontsize=17, color=GREEN)
    ax.text(18.2, 3.3, '17.5%', ha='center', fontsize=17, color=BLUE)
    ax.text(11.8, 3.3, 'vs', ha='center', va='center', fontsize=11, color=MUTED)
    ax.text(11.8, 1.9, 'PerAct2: 13 tasks, 100 evaluations each. A tie.',
            ha='center', fontsize=9.8, color=INK)
    ax.text(11.8, 0.9, 'The joint policy won 9 of the 13 and trained about 40% '
            'faster, so it is the simpler design — not the proven one.',
            ha='center', fontsize=9.2, color=MUTED)

    # The thing that IS measured.
    ax.add_patch(Rectangle((0.2, -3.9), 23.2, 3.6, facecolor=PALE_ORANGE,
                           edgecolor=ORANGE, lw=1.5))
    ax.text(11.8, -0.9, 'What the evidence does settle, whichever you pick',
            ha='center', fontsize=10.5, color=INK)
    ax.text(11.8, -2.0, "each gripper's position RELATIVE TO THE OTHER has to be "
            "in the network's input", ha='center', fontsize=10, color=ORANGE)
    ax.text(11.8, -3.2, 'Remove that term and two-arm cloth folding falls from '
            '70% to 30%.', ha='center', fontsize=9.2, color=MUTED)
    _save(fig, 'learned-methods', 'one-policy-or-two.svg')


def teleop_rigs() -> None:
    """How a person drives two arms, and how much the choice is worth."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.2, 5.0), facecolor='white')
    ax.set_xlim(-0.5, 128)
    ax.set_ylim(-1.9, 3.5)
    ax.axis('off')

    ax.text(-0.5, 3.2, 'Three ways for one person to drive fourteen joints at '
            'once, measured on five two-arm tasks', fontsize=11.5, color=INK)

    rigs: list[tuple[str, float, str, str]] = [
        ('a pair of small leader arms\nheld one in each hand', 92.0, GREEN,
         'your hands are already doing the task;\nthe robot just copies the pose'),
        ('virtual-reality controllers', 72.0, ORANGE,
         'no force to feel, and the mapping from\nyour hand to the gripper is learned'),
        ('a 3D mouse', 63.0, RED,
         'one device, two arms — so you drive\nthem one at a time'),
    ]
    for index, (label, score, colour, why) in enumerate(rigs):
        y: float = 2.0 - index * 1.25
        ax.add_patch(Rectangle((0, y - 0.28), score, 0.56, facecolor=colour,
                               edgecolor='none', alpha=0.85))
        ax.text(score + 1.5, y, f'{score:.0f}%', va='center', fontsize=12,
                color=colour)
        ax.text(0, y + 0.42, label, va='bottom', fontsize=9.4, color=INK,
                linespacing=1.4)
        ax.text(score + 7.5, y, why, va='center', fontsize=8.8, color=MUTED,
                linespacing=1.45)

    ax.text(-0.5, -1.5, 'Task success across twelve participants. The rig is a '
            'bigger determinant of your data quality than most modelling choices, '
            'which is why\nthe standard setup is leader arms.',
            fontsize=9.5, color=INK, va='top', linespacing=1.7)
    _save(fig, 'learned-methods', 'teleop-rigs.svg')


if __name__ == '__main__':
    fixture_or_arm()
    coordination()
    layers()
    separate_plans_collide()
    internal_force()
    one_policy_or_two()
    teleop_rigs()
