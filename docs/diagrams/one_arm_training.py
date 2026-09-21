"""Generate the diagrams used in docs/07_one-arm-training/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/one-arm-training/<doc-name>/.

Run with:  pixi run python docs/diagrams/one_arm_training.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'one-arm-training'

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

# One branch of the tree: a label and the children below it.
Node = tuple[str, list['Node']]

PROGRAMMED: list[Node] = [
    ('teach and replay\nlead the arm through, it repeats', []),
    ('offline programming\nwrite the path against a CAD model', []),
    ('scripted logic\nstate machines, behaviour trees', []),
    ('motion planning', [
        ('sampling-based: RRT, PRM', []),
        ('optimisation-based: CHOMP, TrajOpt', []),
        ('point-to-point, linear, circular', []),
    ]),
    ('task and motion planning\nwhat to do and how to move, at once', []),
    ('feedback control', [
        ('inverse kinematics, trajectory tracking', []),
        ('force: impedance and admittance', []),
        ('visual servoing: steer by the picture', []),
        ('model predictive control', []),
    ]),
]

LEARNED: list[Node] = [
    ('from demonstrations', [
        ('behaviour cloning: ACT, diffusion policy', []),
        ('interactive: DAgger, human take-over', []),
        ('learn the reward: inverse RL, preferences', []),
    ]),
    ('from trial and error', [
        ('model-free RL: PPO, SAC', []),
        ('model-based RL: Dreamer, TD-MPC', []),
        ('offline RL: learn from logs (IQL, CQL)', []),
    ]),
    ('from large pretraining', [
        ('vision-language-action models (VLAs)', []),
        ('fine-tune one on your task', []),
    ]),
    ('learned pieces in a\nprogrammed stack', [
        ('grasp points, object pose, segmentation', []),
        ('learned stability and cost models', []),
    ]),
]


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


# --------------------------------------------------------------------------
# overview.md
# --------------------------------------------------------------------------

def task_map() -> None:
    """Place real tasks on the two axes that decide which method you need.

    The point of the picture is that the four corners want different methods,
    and that the task groups A-D are not an arbitrary ordering.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.6, 8.0), facecolor='white')
    ax.set_xlim(-0.06, 1.18)
    ax.set_ylim(-0.16, 1.12)
    ax.axis('off')

    # The four quadrants, each labelled with what it actually needs. The "needs"
    # text sits in whichever corner the task points leave free.
    corners: list[tuple[float, float, str, str, str, str, float, str]] = [
        (0.0, 0.0, PALE_PURPLE, PURPLE, 'little known  ·  little contact',
         'learned perception,\nthen an ordinary planner', 0.02, 'left'),
        (0.5, 0.0, PALE_BLUE, BLUE, 'known  ·  little contact',
         'teach it, or generate it\nfrom the CAD model', 0.48, 'right'),
        (0.5, 0.5, PALE_ORANGE, ORANGE, 'known  ·  contact decides',
         'force control, and\nlearning is arriving here', 0.48, 'right'),
        (0.0, 0.5, PALE_GREEN, GREEN, 'little known  ·  contact decides',
         'learning, or\nnobody has solved it', 0.48, 'right'),
    ]
    for x0, y0, fill, edge, corner, need, offset, align in corners:
        ax.add_patch(Rectangle((x0, y0), 0.5, 0.5, facecolor=fill, edgecolor=edge,
                               lw=1.2, alpha=0.65, zorder=0))
        ax.text(x0 + 0.02, y0 + 0.48, corner, fontsize=8.2, color=edge, va='top')
        ax.text(x0 + offset, y0 + 0.02, need, fontsize=9.0, color=edge, ha=align,
                va='bottom', linespacing=1.4)

    # (x, y, label, group letter, colour, text alignment). 'right' puts the label
    # to the LEFT of its dot. Set by hand so no label crosses a boundary.
    tasks: list[tuple[float, float, str, str, str, str]] = [
        (0.92, 0.40, 'palletising', '', BLUE, 'right'),
        (0.82, 0.22, 'spot welding', '', BLUE, 'right'),
        (0.72, 0.30, 'arc welding', '', BLUE, 'right'),
        (0.86, 0.66, 'screwdriving', 'A', ORANGE, 'right'),
        (0.90, 0.78, 'connector insertion', 'A', ORANGE, 'right'),
        (0.72, 0.90, 'press and snap fits', 'A', ORANGE, 'right'),
        (0.60, 0.60, 'polishing, deburring', 'A', ORANGE, 'left'),
        (0.40, 0.14, 'kitting and packing', 'B', PURPLE, 'left'),
        (0.30, 0.24, 'bin picking, mixed', 'B', PURPLE, 'left'),
        (0.22, 0.34, 'order picking', 'B', PURPLE, 'left'),
        (0.46, 0.44, 'machine tending, unfixtured', 'B', PURPLE, 'right'),
        (0.28, 0.66, 'cable routing', 'C', GREEN, 'left'),
        (0.34, 0.83, 'food handling', 'C', GREEN, 'left'),
        (0.10, 0.74, 'fabric handling', 'C', GREEN, 'left'),
        (0.06, 0.58, 'fruit harvesting', 'D', GREEN, 'left'),
        (0.12, 0.92, 'rubble, natural material', 'D', GREEN, 'left'),
    ]
    for x, y, label, group, colour, align in tasks:
        ax.plot([x], [y], marker='o', markersize=7.5, color=colour, zorder=4,
                markeredgecolor='white', markeredgewidth=1.2)
        text: str = f'{group}. {label}' if group else label
        nudge: float = -0.022 if align == 'right' else 0.022
        ax.text(x + nudge, y, text, fontsize=8.4, color=INK, ha=align,
                va='center', zorder=5, linespacing=1.3)

    ax.add_patch(FancyArrowPatch((0.0, -0.05), (1.0, -0.05), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.text(0.5, -0.095, 'how much is known in advance  →', ha='center',
            fontsize=10, color=INK)
    ax.text(0.0, -0.095, 'nothing', ha='left', fontsize=8.5, color=MUTED)
    ax.text(1.0, -0.095, 'drawings, feeders, a jig', ha='right', fontsize=8.5,
            color=MUTED)

    ax.add_patch(FancyArrowPatch((-0.03, 0.0), (-0.03, 1.0), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.text(-0.052, 0.5, 'how much of the job is contact  →', rotation=90,
            ha='center', va='center', fontsize=10, color=INK)

    ax.text(0.0, 1.08, 'The two properties that predict which method you need. '
            'The letters are the task groups.', fontsize=10, color=INK)
    _save(fig, 'overview', 'task-map.svg')


def layers() -> None:
    """Trace one concrete task down the four layers.

    Generic layer diagrams say nothing; this one follows "put this connector in
    that socket" the whole way down, which is what makes the layers legible.
    """
    rows: list[tuple[str, str, str, str]] = [
        ('what to do next',
         'fetch the board, seat the connector,\ntest it, put the board in the tray',
         'behaviour tree  ·  state machine  ·  a language model', PURPLE),
        ('which skill, and where',
         '"seat the connector" becomes:\nthis one, from the feeder, into that socket',
         'learned perception feeding a planner  ·  a VLA', BLUE),
        ('how to move',
         'a path from the feeder to 2 cm above\nthe socket that hits nothing',
         'motion planning  ·  or point-to-point, if nothing moves', GREEN),
        ('how to touch',
         'the last 2 cm: press, feel for the hole,\nseat it without bending a pin',
         'force control  ·  learned from demonstrations  ·  RL', ORANGE),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.0, 5.4), facecolor='white')
    ax.set_xlim(0, 28)
    ax.set_ylim(-1.6, 4.5 * len(rows) + 0.8)
    ax.axis('off')
    fills: dict[str, str] = {PURPLE: PALE_PURPLE, BLUE: PALE_BLUE, GREEN: PALE_GREEN,
                             ORANGE: PALE_ORANGE}

    ax.text(0.2, 4.5 * len(rows) + 0.2,
            'One task — "put this connector in that socket" — through the four layers',
            fontsize=11, color=INK)

    for index, (title, doing, methods, colour) in enumerate(rows):
        y: float = (len(rows) - 1 - index) * 4.3
        ax.add_patch(Rectangle((0.2, y), 5.6, 3.3, facecolor=fills[colour],
                               edgecolor=colour, lw=1.5))
        ax.text(3.0, y + 1.7, title, ha='center', fontsize=10.5, color=INK)
        ax.text(6.6, y + 1.7, doing, ha='left', va='center', fontsize=9.2,
                color=INK, linespacing=1.5)
        ax.text(17.2, y + 1.7, methods, ha='left', va='center', fontsize=9.0,
                color=colour)
        if index < len(rows) - 1:
            ax.add_patch(FancyArrowPatch((3.0, y), (3.0, y - 1.0), arrowstyle='-|>',
                                         mutation_scale=12, color=INK, lw=1.2))

    ax.text(0.2, -1.2, 'The top layer is nearly always programmed and the bottom '
            'is increasingly learned. The middle two are where the argument is.',
            fontsize=9.5, color=INK)
    _save(fig, 'overview', 'layers.svg')


def _count_leaves(nodes: list[Node]) -> int:
    """How many rows a branch needs: one per leaf."""
    return sum(max(1, _count_leaves(children)) for _, children in nodes)


def _draw_branch(ax: Axes, nodes: list[Node], depth: int, top: float, colour: str,
                 fill: str, parent: tuple[float, float] | None) -> float:
    """Draw one level of the tree downwards from `top`, and say where it ended."""
    row: float = top
    widths: dict[int, float] = {0: 7.2, 1: 8.2, 2: 11.0}
    x: float = {0: 0.0, 1: 8.0, 2: 17.0}[depth]
    width: float = widths[depth]
    for label, children in nodes:
        if children:
            start: float = row
            row = _draw_branch(ax, children, depth + 1, row, colour, fill, None)
            middle: float = (start + row) / 2 - 0.5
        else:
            middle = row
            row += 1.0
        ax.add_patch(Rectangle((x, middle - 0.4), width, 0.8, facecolor=fill,
                               edgecolor=colour, lw=1.2))
        ax.text(x + 0.25, middle, label, ha='left', va='center', fontsize=8.2, color=INK)
        if parent is not None:
            ax.add_patch(FancyArrowPatch((parent[0], parent[1]), (x, middle),
                                         arrowstyle='-', color=colour, lw=1.0,
                                         connectionstyle='angle,angleA=0,angleB=90,rad=4'))
        if children:
            ax.add_patch(FancyArrowPatch((x + width, middle), (x + width + 0.8, middle),
                                         arrowstyle='-', color=colour, lw=1.0))
    return row


def taxonomy() -> None:
    """Draw the family tree of ways to make an arm do something."""
    programmed_rows: int = _count_leaves(PROGRAMMED)
    learned_rows: int = _count_leaves(LEARNED)
    total: float = programmed_rows + learned_rows + 3
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.5, 0.62 * total + 2.0), facecolor='white')
    ax.set_xlim(-5.8, 28.6)
    ax.set_ylim(total + 1.0, -1.6)
    ax.axis('off')

    ax.text(-5.7, -1.0, 'Ways to make one robot arm do a complex task', fontsize=12.5,
            color=INK)

    end_programmed: float = _draw_branch(ax, PROGRAMMED, 0, 0.6, BLUE, PALE_BLUE, None)
    ax.add_patch(Rectangle((-5.6, 0.2), 5.0, end_programmed - 0.8, facecolor=PALE_GREY,
                           edgecolor=BLUE, lw=1.6))
    ax.text(-3.1, (0.2 + end_programmed - 0.6) / 2,
            'PROGRAMMED\n\na person writes\nthe behaviour',
            ha='center', va='center', fontsize=9.5, color=BLUE)

    start_learned: float = end_programmed + 1.4
    end_learned: float = _draw_branch(ax, LEARNED, 0, start_learned, GREEN, PALE_GREEN, None)
    ax.add_patch(Rectangle((-5.6, start_learned - 0.4), 5.0, end_learned - start_learned,
                           facecolor=PALE_GREY, edgecolor=GREEN, lw=1.6))
    ax.text(-3.1, (start_learned + end_learned - 0.4) / 2,
            'LEARNED\n\nthe behaviour comes\nfrom examples\nor from practice',
            ha='center', va='center', fontsize=9.5, color=GREEN)

    ax.text(-5.7, end_learned + 0.6,
            'On top of either: a language model can choose the order of the steps '
            '(see "directed by language").',
            fontsize=9, color=PURPLE)
    _save(fig, 'overview', 'taxonomy.svg')


def timeline() -> None:
    """Draw roughly when each method became common, and which are fading."""
    # (label, first widely used, still common until, status colour, note)
    bars: list[tuple[str, int, int, str, str]] = [
        ('teach and replay', 1975, 2026, BLUE, 'not declining; now hand-guided'),
        ('offline programming from CAD', 1990, 2026, BLUE, 'standard for high-mix lines'),
        ('behaviour trees and state machines', 2005, 2026, BLUE, 'standard for sequencing'),
        ('sampling-based motion planning', 2000, 2026, BLUE, 'standard; now often GPU-solved'),
        ('CAD model matching for known parts', 2004, 2026, BLUE, 'still standard for known parts'),
        ('hand-designed visual features', 2000, 2016, GREY, 'replaced by learned perception'),
        ('learned grasp proposal', 2017, 2026, GREEN, 'deployed; for unknown objects'),
        ('learned pose and segmentation', 2018, 2026, GREEN, 'deployed widely'),
        ('reinforcement learning in simulation', 2017, 2026, GREEN, 'for contact and dexterity'),
        ('inverse RL and adversarial imitation', 2016, 2022, GREY, 'now a minority approach'),
        ('behaviour cloning with action chunking', 2023, 2026, GREEN, 'the default first try'),
        ('diffusion and flow-matching policies', 2023, 2026, GREEN, 'default when demos vary'),
        ('language models as task planners', 2022, 2026, PURPLE, 'for sequencing and code'),
        ('vision-language-action models', 2023, 2026, PURPLE, 'the current frontier'),
        ('RL fine-tuning of pretrained policies', 2025, 2026, PURPLE, 'the 2026 precision recipe'),
        ('world-model policies', 2025, 2026, PURPLE, 'new, and unproven on real arms'),
        ('learning from human video at scale', 2026, 2026, PURPLE, 'newest; little released'),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13, 6.4), facecolor='white')
    first: int = 1975
    last: int = 2027
    ax.set_xlim(first - 1, last + 9)
    ax.set_ylim(len(bars) + 0.4, -1.8)
    ax.axis('off')

    for year in range(1980, 2027, 10):
        ax.plot([year, year], [-0.8, len(bars) - 0.4], color=PALE_GREY, lw=1.0, zorder=0)
        ax.text(year, -1.1, str(year), ha='center', fontsize=8.5, color=MUTED)
    ax.text(2026, -1.1, 'now', ha='center', fontsize=8.5, color=INK)

    for index, (label, start, end, colour, note) in enumerate(bars):
        fading: bool = end < 2026
        ax.add_patch(Rectangle((start, index - 0.28), end - start, 0.56,
                               facecolor=colour, edgecolor='none',
                               alpha=0.35 if fading else 0.85, zorder=2))
        ax.text(start - 0.6, index, label, ha='right', va='center', fontsize=8.6,
                color=MUTED if fading else INK)
        ax.text(end + 0.6, index, note, ha='left', va='center', fontsize=8.2,
                color=MUTED if fading else colour)

    ax.text(first - 1, len(bars) + 0.2,
            'Faded bars are methods that were largely replaced; the year they end is '
            'roughly when that happened.', fontsize=9, color=MUTED)
    _save(fig, 'what-is-changing', 'timeline.svg')


# --------------------------------------------------------------------------
# learning-path.md
# --------------------------------------------------------------------------

def learning_path() -> None:
    """Five whole projects, each climbing the same four layers.

    The point of the picture is that every project is done four times, getting
    less hand-written each round, and that the Mac runs everything except the
    last column.
    """
    layers: list[tuple[str, str]] = [
        ('layer 1', 'written by hand'),
        ('layer 2', 'one learned piece'),
        ('layer 3', 'a learned skill'),
        ('layer 4', 'the 2026 frontier'),
    ]
    # (project, [four cells], colour)
    rows: list[tuple[str, list[str], str]] = [
        ('1. Tidy the desk',
         ['find by colour,\nplan, place', 'segment anything,\nnot just colour',
          'learn where\nto grasp', 'ask for it\nin words'], BLUE),
        ('2. Fit the connector',
         ['position control\njams the pin', 'force control\nand a search',
          'copy the search\nfrom demos', 'practise until\nit is reliable'], ORANGE),
        ('3. Empty the bin',
         ['geometric grasps\non a point cloud', 'segment, then\nrank candidates',
          'train your own\ngrasp scorer', 'a pretrained\npolicy'], GREEN),
        ('4. Copy from video',
         ['track a hand\nin your own video', 'retarget hand\nto gripper',
          'train on the\nretargeted data', 'video plus a few\nreal demos'], PURPLE),
        ('5. Build the kit',
         ['behaviour tree\nover skills', 'learned steps\ninside the tree',
          'one policy,\nend to end', 'a model picks\nthe branch'], RED),
    ]
    fills: dict[str, str] = {BLUE: PALE_BLUE, ORANGE: PALE_ORANGE, GREEN: PALE_GREEN,
                             PURPLE: PALE_PURPLE, RED: PALE_RED}
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.6, 7.6), facecolor='white')
    col_w: float = 6.2
    left: float = 7.0
    ax.set_xlim(0, left + 4 * col_w + 0.6)
    ax.set_ylim(-2.4, 4.0 * len(rows) + 3.0)
    ax.axis('off')

    ax.text(0.2, 4.0 * len(rows) + 2.3,
            'Five whole projects, each built four times — every round replaces '
            'more hand-written code with something learned', fontsize=11.5, color=INK)

    for index, (tag, note) in enumerate(layers):
        x: float = left + index * col_w
        ax.text(x + col_w / 2 - 0.3, 4.0 * len(rows) + 1.1, tag, ha='center',
                fontsize=9.0, color=MUTED)
        ax.text(x + col_w / 2 - 0.3, 4.0 * len(rows) + 0.35, note, ha='center',
                fontsize=9.6, color=INK)

    for r, (project, cells, colour) in enumerate(rows):
        y: float = (len(rows) - 1 - r) * 4.0
        ax.add_patch(Rectangle((0.2, y), 6.2, 3.1, facecolor=fills[colour],
                               edgecolor=colour, lw=1.6))
        ax.text(3.3, y + 1.55, project, ha='center', va='center', fontsize=10.2,
                color=INK)
        for c, cell in enumerate(cells):
            x = left + c * col_w
            ax.add_patch(Rectangle((x, y), col_w - 0.6, 3.1, facecolor='white',
                                   edgecolor=GREY, lw=1.0))
            ax.text(x + (col_w - 0.6) / 2, y + 1.55, cell, ha='center',
                    va='center', fontsize=8.6, color=INK, linespacing=1.5)

    # Where the Mac stops.
    boundary: float = left + 3 * col_w - 0.3
    ax.plot([boundary, boundary], [-0.5, 4.0 * len(rows) - 0.4], color=ORANGE,
            lw=2.0, linestyle=(0, (6, 4)))
    ax.text(boundary - 0.3, -1.1, 'everything left of this line runs on the Mac',
            ha='right', fontsize=9.2, color=GREEN)
    ax.text(boundary + 0.3, -1.1, 'rent a GPU for most of this column',
            ha='left', fontsize=9.2, color=ORANGE)

    ax.text(0.2, -2.1, 'Each project is worth doing on its own, and each layer is '
            'a version you could show somebody.', fontsize=9.5, color=INK)
    _save(fig, 'learning-path', 'learning-path.svg')


# --------------------------------------------------------------------------
# what-is-changing.md
# --------------------------------------------------------------------------

def what_is_expensive() -> None:
    """Show the mechanism: the winner is whatever needs less of the scarce thing.

    The fourth panel is the same rule producing the opposite answer, which is
    the part that explains why industry has not adopted the learned methods.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.4, 6.2), facecolor='white')
    ax.set_xlim(-0.5, 35.5)
    ax.set_ylim(-1.2, 12.0)
    ax.axis('off')

    ax.text(-0.5, 11.5, 'Methods are displaced by whatever needs less of the '
            'currently expensive thing', fontsize=12, color=INK)

    # (era, what is scarce, what won, what it displaced, colour, fill)
    panels: list[tuple[str, str, str, str, str, str]] = [
        ('1970s onwards', 'COMPUTE', 'teach and replay',
         'stores joint angles and\nplays them back: no model,\n'
         'no search, no arithmetic\nworth the name', BLUE, PALE_BLUE),
        ('2010s onwards', "A SPECIALIST'S TIME", 'learned perception',
         'displaced hand-tuned visual\nfeatures, which needed a\n'
         'specialist per object and\nper factory', GREEN, PALE_GREEN),
        ('2020s onwards', 'SPECIFICATION EFFORT', 'imitation learning',
         'beat reinforcement learning:\nwriting a reward is\n'
         'specification, doing the\ntask 50 times is not', PURPLE, PALE_PURPLE),
        ('wherever it applies', 'VERIFICATION', 'the classical stack',
         'a factory must say why a\nmachine stopped, and an\n'
         'inspectable system is\ncheaper to certify', RED, PALE_RED),
    ]
    for index, (era, scarce, winner, why, colour, fill) in enumerate(panels):
        x0: float = index * 8.8
        ax.add_patch(Rectangle((x0, 0.2), 7.7, 10.2, facecolor=fill,
                               edgecolor=colour, lw=2.4 if index == 3 else 1.4))
        ax.text(x0 + 3.85, 9.6, era, ha='center', fontsize=9.0, color=MUTED)
        ax.text(x0 + 3.85, 8.5, 'what is expensive', ha='center', fontsize=8.4,
                color=MUTED)
        ax.text(x0 + 3.85, 7.6, scarce, ha='center', fontsize=10.5, color=colour)
        ax.add_patch(FancyArrowPatch((x0 + 3.85, 7.0), (x0 + 3.85, 5.9),
                                     arrowstyle='-|>', mutation_scale=12,
                                     color=INK, lw=1.2))
        ax.text(x0 + 3.85, 5.4, 'so the winner is', ha='center', fontsize=8.4,
                color=MUTED)
        ax.text(x0 + 3.85, 4.5, winner, ha='center', fontsize=11, color=INK)
        ax.text(x0 + 3.85, 3.3, why, ha='center', va='top', fontsize=8.5,
                color=colour, linespacing=1.55)
        if index == 3:
            ax.text(x0 + 3.85, 10.8, 'the same rule, opposite answer',
                    ha='center', fontsize=9.0, color=RED)

    ax.text(-0.5, -0.9, 'Nothing here got worse. What changed is which resource '
            'was scarce — which is why a displaced method can come back, and why '
            'the fourth panel is not nostalgia.', fontsize=9.5, color=INK)
    _save(fig, 'what-is-changing', 'what-is-expensive.svg')


def consolidation() -> None:
    """Show that most "dead" repositories were consolidated, not superseded."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.0, 6.6), facecolor='white')
    ax.set_xlim(-0.5, 32.0)
    ax.set_ylim(-2.2, 15.4)
    ax.axis('off')

    ax.text(-0.5, 14.9, 'Three organisations, one pattern: the work moved house '
            'rather than stopping', fontsize=12, color=INK)

    # (sources, destination, who did it, colour, fill)
    bands: list[tuple[list[str], str, str, str, str]] = [
        (['ACT  ·  last commit 2024',
          'diffusion_policy  ·  late 2024',
          'Octo  ·  mid-2024',
          'OpenVLA  ·  March 2025'],
         'LeRobot\nmaintained, one shared\ndataset format',
         'consolidated by Hugging Face', GREEN, PALE_GREEN),
        (['OpenAI Gym  ·  archived',
          'D4RL  ·  deprecated'],
         'Gymnasium\nand Minari',
         'adopted by the Farama Foundation', BLUE, PALE_BLUE),
        (['Isaac Gym  ·  no longer supported',
          'IsaacGymEnvs  ·  archived'],
         'Isaac Lab\non the Isaac Sim platform',
         'consolidated by NVIDIA', ORANGE, PALE_ORANGE),
    ]
    top: float = 13.4
    for sources, destination, who, colour, fill in bands:
        height: float = 1.05 * len(sources) + 0.9
        centre: float = top - height / 2
        for index, source in enumerate(sources):
            y: float = top - 1.0 - index * 1.05
            ax.add_patch(Rectangle((0.2, y - 0.38), 11.0, 0.76,
                                   facecolor=PALE_GREY, edgecolor=GREY, lw=1.0))
            ax.text(0.5, y, source, va='center', fontsize=8.6, color=MUTED)
            ax.add_patch(FancyArrowPatch((11.4, y), (15.4, centre),
                                         arrowstyle='-|>', mutation_scale=10,
                                         color=colour, lw=1.1,
                                         connectionstyle='arc3,rad=0.12'))
        ax.add_patch(Rectangle((15.7, centre - height / 2 + 0.3), 9.4,
                               height - 0.6, facecolor=fill, edgecolor=colour,
                               lw=1.6))
        ax.text(20.4, centre, destination, ha='center', va='center',
                fontsize=9.8, color=INK, linespacing=1.5)
        ax.text(25.6, centre, who, ha='left', va='center', fontsize=8.8,
                color=colour)
        top -= height + 0.9

    ax.text(-0.5, -1.4, 'A dormant repository is not a verdict on the technique. '
            'Check whether the method moved into a maintained home before '
            'concluding it died.', fontsize=9.5, color=INK)
    _save(fig, 'what-is-changing', 'consolidation.svg')


# --------------------------------------------------------------------------
# programmed-methods.md
# --------------------------------------------------------------------------

def planner_families() -> None:
    """Solve the same start and goal three ways, so the trade-off is visible."""
    fig: Figure
    axes: np.ndarray
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.6), facecolor='white')

    # (title, colour, path, what you get, what it costs)
    start: tuple[float, float] = (0.6, 0.8)
    goal: tuple[float, float] = (9.4, 5.2)
    sampled: list[tuple[float, float]] = [
        (0.6, 0.8), (1.5, 2.2), (0.9, 3.6), (1.8, 5.2), (3.0, 6.3), (4.7, 5.6),
        (4.8, 3.2), (5.6, 2.9), (6.9, 3.0), (8.4, 2.6), (9.1, 4.0), (9.4, 5.2),
    ]
    optimised: list[tuple[float, float]] = [
        (0.6, 0.8), (1.6, 1.6), (2.6, 2.4), (3.8, 2.7), (4.8, 2.9), (5.8, 3.0),
        (6.9, 3.2), (8.0, 3.4), (8.8, 4.3), (9.4, 5.2),
    ]
    point_to_point: list[tuple[float, float]] = [
        (0.6, 0.8), (0.6, 6.8), (9.4, 6.8), (9.4, 5.2),
    ]
    panels: list[tuple[str, str, list[tuple[float, float]], str, str]] = [
        ('sampling-based\nRRT, PRM', GREEN, sampled,
         'finds a way through\nawkward spaces',
         'ugly, and different\nevery single run'),
        ('optimisation-based\nCHOMP, TrajOpt, cuRobo', BLUE, optimised,
         'short, smooth,\nand repeatable',
         'can get stuck where\na sampler would not'),
        ('point-to-point\nwhat industrial controllers do', ORANGE, point_to_point,
         'identical every time,\nand you can prove it',
         'you place the via\npoints yourself'),
    ]

    for ax, (title, colour, path, gives, costs) in zip(axes, panels):
        ax.set_xlim(-0.3, 10.3)
        ax.set_ylim(-2.8, 7.6)
        ax.axis('off')
        ax.set_title(title, fontsize=10, color=INK, pad=8)

        for x0, y0, width, height in ((2.2, 3.0, 2.0, 2.4), (5.4, 0.4, 2.2, 2.0),
                                      (6.4, 3.6, 1.6, 1.8)):
            ax.add_patch(Rectangle((x0, y0), width, height, facecolor=PALE_GREY,
                                   edgecolor=GREY, lw=1.0, zorder=1))

        xs: list[float] = [p[0] for p in path]
        ys: list[float] = [p[1] for p in path]
        ax.plot(xs, ys, color=colour, lw=2.2, zorder=3, solid_capstyle='round')
        ax.plot(xs[1:-1], ys[1:-1], marker='o', markersize=3.4, color=colour,
                linestyle='none', zorder=4)
        ax.plot([start[0]], [start[1]], marker='o', markersize=9, color=INK, zorder=5)
        ax.plot([goal[0]], [goal[1]], marker='*', markersize=15, color=RED, zorder=5)
        ax.text(start[0] + 0.25, start[1] - 0.55, 'start', fontsize=8.5, color=INK)
        ax.text(goal[0] - 0.25, goal[1] + 0.45, 'goal', fontsize=8.5, color=RED,
                ha='right')

        ax.text(-0.3, -0.9, gives, fontsize=8.8, color=colour, va='top',
                linespacing=1.4)
        ax.text(-0.3, -1.9, costs, fontsize=8.8, color=MUTED, va='top',
                linespacing=1.4)

    fig.text(0.5, 0.02, 'The grey boxes are obstacles and the dots are the points '
             'each method actually decides. Same problem, three shapes of answer.',
             ha='center', fontsize=9.5, color=INK)
    _save(fig, 'programmed-methods', 'planner-families.svg')


def position_vs_force() -> None:
    """Why commanding a position into a rigid surface breaks things."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.0, 5.8), facecolor='white')
    ax.set_xlim(-0.4, 4.9)
    ax.set_ylim(-110, 730)
    ax.axis('off')

    # Axes drawn by hand so the picture stays diagrammatic rather than a plot.
    ax.add_patch(FancyArrowPatch((0, 0), (3.3, 0), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.add_patch(FancyArrowPatch((0, 0), (0, 700), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.3))
    ax.text(3.34, -45, 'how far past the surface you commanded  (mm)', fontsize=9.5,
            color=INK, ha='left')
    ax.text(-0.22, 700, 'contact force  (N)', fontsize=9.5, color=INK, rotation=90,
            va='top')

    ax.plot([0, 0], [-70, 720], color=MUTED, lw=1.0, linestyle=(0, (4, 4)))
    ax.text(0.04, -48, 'the surface', fontsize=8.5, color=MUTED)

    # The band sits above where either line reaches, so nothing overlaps.
    ax.add_patch(Rectangle((-0.02, 565), 3.3, 150, facecolor=PALE_RED,
                           edgecolor='none', alpha=0.6, zorder=0))
    ax.text(1.64, 628, 'where parts get broken', fontsize=10, color=RED,
            ha='center', va='center', zorder=1)

    stiff: np.ndarray = np.linspace(0, 2.6, 60)
    ax.plot(stiff, 200.0 * stiff, color=RED, lw=2.6)
    ax.text(2.72, 520, 'position control\nstiff by construction: the controller\n'
            'sees an error it cannot remove,\nso it pushes harder',
            fontsize=9.2, color=RED, ha='left', va='center', linespacing=1.55)

    soft: np.ndarray = np.linspace(0, 3.0, 60)
    ax.plot(soft, 22.0 * soft, color=GREEN, lw=2.6)
    ax.text(3.16, 66, 'impedance control\nbehaves like a spring of a\nstiffness you '
            'chose', fontsize=9.2, color=GREEN, ha='left', va='center',
            linespacing=1.55)

    ax.plot([0.55], [110], marker='o', markersize=8, color=RED, zorder=5)
    ax.text(0.80, 185, 'half a millimetre of model error\nis already a large force',
            fontsize=8.8, color=INK, va='bottom', linespacing=1.45)

    ax.text(-0.4, -105, 'The whole idea of force control is to choose the slope of '
            'that line rather than inherit it from the mechanics.',
            fontsize=9.5, color=INK)
    _save(fig, 'programmed-methods', 'position-vs-force.svg')


# --------------------------------------------------------------------------
# learned-methods.md
# --------------------------------------------------------------------------

def compounding_error() -> None:
    """Why copying drifts, and what the two standard fixes actually do."""
    fig: Figure
    axes: np.ndarray
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), facecolor='white')

    steps: np.ndarray = np.linspace(0, 10, 200)
    centre: np.ndarray = 2.0 + 1.5 * np.sin(steps / 3.4)

    titles: list[tuple[str, str, str]] = [
        ('one command per frame', RED,
         'every frame is a fresh chance to be\nslightly wrong, and the errors add up'),
        ('predict 100 commands at once', GREEN,
         'the same drift per decision, but\n100x fewer decisions in the task'),
        ('correct it while it runs', BLUE,
         'a person pulls it back, and that\ncorrection becomes training data'),
    ]
    for index, (ax, (title, colour, note)) in enumerate(zip(axes, titles)):
        ax.set_xlim(-0.5, 10.8)
        ax.set_ylim(-3.4, 7.6)
        ax.axis('off')
        ax.set_title(title, fontsize=10, color=colour, pad=10)

        ax.fill_between(steps, centre - 0.65, centre + 0.65, color=PALE_GREY,
                        edgecolor=GREY, lw=1.0, zorder=0)
        ax.plot(steps, centre, color=GREY, lw=1.4, linestyle=(0, (5, 4)), zorder=1)
        if index == 0:
            ax.text(0.0, 0.55, 'the grey band is what the\ndemonstrations covered',
                    fontsize=8.4, color=MUTED, linespacing=1.4)

        if index == 0:
            # Error grows with the square of the number of decisions taken.
            drift: np.ndarray = centre + 0.040 * steps ** 2
            decisions: np.ndarray = np.linspace(0, 10, 26)
        elif index == 1:
            drift = centre + 0.16 * steps
            decisions = np.linspace(0, 10, 4)
        else:
            drift = centre + 0.16 * steps
            drift[steps > 5.2] = centre[steps > 5.2] + 0.22
            decisions = np.linspace(0, 10, 4)

        ax.plot(steps, drift, color=colour, lw=2.4, zorder=3)
        picked: np.ndarray = np.interp(decisions, steps, drift)
        ax.plot(decisions, picked, marker='o', markersize=4.2, color=colour,
                linestyle='none', zorder=4)

        if index == 0:
            ax.annotate('nothing in the data\nlooks like this',
                        xy=(9.5, float(np.interp(9.5, steps, drift)) + 0.15),
                        xytext=(5.3, 7.0), fontsize=8.6, color=RED,
                        ha='center', va='top', linespacing=1.4,
                        arrowprops={'arrowstyle': '->', 'color': RED, 'lw': 1.1})
        if index == 2:
            ax.add_patch(FancyArrowPatch((5.2, 6.1), (5.2, 4.5),
                                         arrowstyle='-|>', mutation_scale=12,
                                         color=BLUE, lw=1.6))
            ax.text(5.5, 6.6, 'a person takes over', fontsize=8.6, color=BLUE,
                    va='center')

        ax.text(-0.5, -1.1, note, fontsize=8.8, color=INK, va='top', linespacing=1.6)
        ax.text(-0.5, -3.1, f'{len(decisions)} decisions in this picture',
                fontsize=8.2, color=MUTED)

    fig.text(0.5, 0.015, 'The dots are decisions. Compounding error grows with how '
             'many there are, which is the whole argument for action chunking.',
             ha='center', fontsize=9.5, color=INK)
    _save(fig, 'learned-methods', 'compounding-error.svg')


def what_is_learned() -> None:
    """Show which stages of a deployed system are networks and which are code.

    Drawn from Amazon's published account of its item-stowing system, because it
    is the one large deployment that says plainly which parts are which.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.0, 5.2), facecolor='white')
    ax.set_xlim(-0.5, 33.0)
    ax.set_ylim(-3.4, 6.6)
    ax.axis('off')

    # (label, learned?)
    stages: list[tuple[str, bool]] = [
        ('depth\nestimation', True),
        ('segmentation', True),
        ('product\nidentity', True),
        ('risk and\nfree space', True),
        ('grasp\nplanning', False),
        ('motion\nplanning', False),
        ('force\ncontrol', False),
        ('named\nprimitives', False),
    ]
    width: float = 3.5
    gap: float = 0.55
    for index, (label, learned) in enumerate(stages):
        x: float = index * (width + gap)
        colour: str = GREEN if learned else BLUE
        fill: str = PALE_GREEN if learned else PALE_BLUE
        ax.add_patch(Rectangle((x, 1.4), width, 2.6, facecolor=fill,
                               edgecolor=colour, lw=1.5))
        ax.text(x + width / 2, 2.7, label, ha='center', va='center', fontsize=9.0,
                color=INK, linespacing=1.4)
        if index < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + width, 2.7), (x + width + gap, 2.7),
                                         arrowstyle='-|>', mutation_scale=10,
                                         color=MUTED, lw=1.2))

    learned_span: float = 4 * width + 3 * gap
    ax.add_patch(Rectangle((0, 4.3), learned_span, 0.5, facecolor=GREEN,
                           edgecolor='none', alpha=0.8))
    ax.text(learned_span / 2, 5.3, 'LEARNED  —  recognising things',
            ha='center', fontsize=10, color=GREEN)

    classical_start: float = 4 * (width + gap)
    classical_span: float = 4 * width + 3 * gap
    ax.add_patch(Rectangle((classical_start, 4.3), classical_span, 0.5,
                           facecolor=BLUE, edgecolor='none', alpha=0.8))
    ax.text(classical_start + classical_span / 2, 5.3,
            'CLASSICAL  —  moving and touching', ha='center', fontsize=10, color=BLUE)

    ax.text(-0.5, 6.3, 'One deployed system, stage by stage: what is a network and '
            'what is ordinary code', fontsize=11, color=INK)

    numbers: list[tuple[str, str]] = [
        ('85.86%', 'success, over 100,000 attempts'),
        ('9.31%', 'unproductive cycles'),
        ('3.77%', 'items dropped'),
        ('0.24%', 'items damaged'),
        ('224/hr', 'against 243/hr for the people on the same floor'),
    ]
    for index, (value, meaning) in enumerate(numbers):
        y: float = -0.4 - index * 0.62
        ax.text(0.0, y, value, fontsize=9.4, color=INK, ha='left')
        ax.text(4.2, y, meaning, fontsize=9.0, color=MUTED, ha='left')

    ax.text(18.0, -0.4, 'The shape to remember: learning is applied to the parts that\n'
            'require recognising something, and everything else stays\n'
            'classical, because everything else can be checked.',
            fontsize=9.5, color=INK, va='top', linespacing=1.6)
    _save(fig, 'learned-methods', 'what-is-learned.svg')


if __name__ == '__main__':
    task_map()
    layers()
    taxonomy()
    timeline()
    learning_path()
    what_is_expensive()
    consolidation()
    planner_families()
    position_vs_force()
    compounding_error()
    what_is_learned()
