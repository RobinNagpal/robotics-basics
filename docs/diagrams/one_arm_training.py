"""Generate the diagrams used in docs/09_one-arm-training/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/one-arm-training/<doc-name>/.

Run with:  pixi run python docs/diagrams/one_arm_training.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Arc, Circle, FancyArrowPatch,  # noqa: E402
                                Polygon, Rectangle)
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


# --------------------------------------------------------------------------
# case-study/v1-place-glass.md
# --------------------------------------------------------------------------

def grip_from_profile() -> None:
    """Draw how a grip point is read off a measured width profile.

    Two stemmed glasses of very different proportions give the same answer,
    which is the whole argument for measuring instead of looking up.
    """
    fig: Figure
    axes: np.ndarray
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 6.2), facecolor='white')

    def profile(height: float, stem_at: float, stem_w: float,
                bowl_w: float, foot_w: float) -> tuple[np.ndarray, np.ndarray]:
        """Half-width against height for a stemmed glass."""
        h: np.ndarray = np.linspace(0, height, 260)
        w: np.ndarray = np.empty_like(h)
        foot_top: float = 0.06 * height
        bowl_bot: float = stem_at + 0.10 * height
        for i, y in enumerate(h):
            if y < foot_top:                       # the foot
                w[i] = foot_w * (1 - 0.35 * y / foot_top)
            elif y < bowl_bot:                     # the stem
                span = (y - foot_top) / (bowl_bot - foot_top)
                w[i] = foot_w * 0.35 + (stem_w - foot_w * 0.35) * min(1.0, span * 2.2)
            else:                                  # the bowl
                span = (y - bowl_bot) / (height - bowl_bot)
                w[i] = stem_w + (bowl_w - stem_w) * np.sqrt(max(0.0, span))
        return h, w

    tall = profile(200, 70, 5.5, 42, 32)
    squat = profile(120, 28, 9.0, 48, 36)

    # --- panel 1 and 3: the two glasses, with the found grip band -----------
    for ax, (h, w), name, height in ((axes[0], tall, 'a tall wine glass', 200),
                                     (axes[2], squat, 'a squat wine glass', 120)):
        ax.set_xlim(-72, 72)
        ax.set_ylim(-46, 232)
        ax.axis('off')
        ax.set_title(name, fontsize=10.5, color=INK, pad=10)
        ax.fill_betweenx(h, -w, w, facecolor=PALE_BLUE, edgecolor=BLUE, lw=1.6)
        ax.plot([-66, 66], [0, 0], color=MUTED, lw=1.2)

        widest: int = int(np.argmax(w))
        below: np.ndarray = w[:widest]
        stem: int = int(np.argmin(below))
        gh: float = float(h[stem])
        opening: float = float(2 * w[stem])

        ax.plot([-58, 58], [gh, gh], color=GREEN, lw=1.8, linestyle=(0, (5, 3)))
        for side in (-1, 1):
            ax.add_patch(Rectangle((side * (w[stem] + 4) - (0 if side > 0 else 11),
                                    gh - 9), 11, 18, facecolor=GREEN,
                                   edgecolor='none', alpha=0.85))
        # beside the stem, where the glass is narrow, so nothing overlaps
        ax.text(64, gh + 8, f'grip here\nopening {opening:.0f} mm',
                ha='right', va='bottom', fontsize=8.6, color=GREEN,
                linespacing=1.45)
        ax.text(0, h[widest] + 6, 'widest', ha='center', fontsize=8.0, color=MUTED)
        ax.text(0, -22, f'height {height} mm', ha='center', fontsize=8.8, color=INK)
        ax.text(0, -36, 'nobody measured this glass', ha='center', fontsize=8.2,
                color=MUTED)

    # --- panel 2: the rule, as a procedure over the list of widths ---------
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.2, 11.4)
    ax.axis('off')
    ax.set_title('the rule, applied to both', fontsize=10.5, color=INK, pad=10)
    steps: list[tuple[str, str]] = [
        ('1', 'take one side-on picture'),
        ('2', 'read the width at every height'),
        ('3', 'find the widest point'),
        ('4', 'below it, find the narrowest'),
        ('5', 'grip there'),
        ('6', 'the opening is the width you measured'),
    ]
    for index, (number, text) in enumerate(steps):
        y: float = 9.6 - index * 1.65
        ax.add_patch(Circle((0.7, y), 0.34, facecolor=PALE_GREEN, edgecolor=GREEN,
                            lw=1.3))
        ax.text(0.7, y, number, ha='center', va='center', fontsize=8.6, color=GREEN)
        ax.text(1.4, y, text, va='center', fontsize=9.2, color=INK)
        if index < len(steps) - 1:
            ax.plot([0.7, 0.7], [y - 0.42, y - 1.23], color=GREEN, lw=1.1)
    ax.text(0.2, -0.6, 'The same six steps. No number in them\nbelongs to a '
            'particular glass.', fontsize=8.8, color=MUTED, linespacing=1.5)

    fig.text(0.5, 0.015, 'Two wine glasses with nothing in common but their shape, '
             'and one rule that finds the stem on both.',
             ha='center', fontsize=9.8, color=INK)
    _save(fig, 'case-study/v1-place-glass', 'grip-from-profile.svg')


def add_a_glass_type() -> None:
    """Draw the loop for adding a new glass type, and what each stage gives you.

    The point of the picture is that only the first stage touches a real glass
    and only the last stage risks one, with simulation in between.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.4, 6.4), facecolor='white')
    ax.set_xlim(0, 34.5)
    ax.set_ylim(-3.2, 9.0)
    ax.axis('off')

    ax.text(0.2, 8.5, 'Adding a glass type: measure, model, prove, then trust',
            fontsize=12, color=INK)

    # (title, what you do, what it produces, colour, where it happens)
    stages: list[tuple[str, str, str, str, str]] = [
        ('1. Measure',
         'a ruler and a\nkitchen scale,\none afternoon',
         'a record in\nthe glass library', BLUE, 'real glass'),
        ('2. Model',
         'spin an outline,\nsimplify it for\ncontact, set the mass',
         'an SDF file the\nsimulator can load', PURPLE, 'desk'),
        ('3. Prove',
         '50 attempts, varying\nplace, rotation,\nneighbours and slot',
         'four numbers, each\nwith its own gate', GREEN, 'simulation'),
        ('4. Trust',
         'ten real picks at\nthe calculated force',
         'a type the cell\ncan be left with', ORANGE, 'real glass'),
    ]
    fills: dict[str, str] = {BLUE: PALE_BLUE, PURPLE: PALE_PURPLE,
                             GREEN: PALE_GREEN, ORANGE: PALE_ORANGE}
    width: float = 7.4
    gap: float = 1.2
    for index, (title, does, makes, colour, where) in enumerate(stages):
        x: float = 0.2 + index * (width + gap)
        ax.add_patch(Rectangle((x, 1.6), width, 5.6, facecolor=fills[colour],
                               edgecolor=colour, lw=1.6))
        ax.text(x + width / 2, 6.6, title, ha='center', fontsize=10.8, color=INK)
        ax.text(x + width / 2, 5.9, where, ha='center', fontsize=8.4, color=colour)
        ax.text(x + width / 2, 4.5, does, ha='center', va='center', fontsize=9.0,
                color=INK, linespacing=1.55)
        ax.plot([x + 0.8, x + width - 0.8], [3.2, 3.2], color=colour, lw=1.0)
        ax.text(x + width / 2, 2.5, makes, ha='center', va='center', fontsize=8.8,
                color=colour, linespacing=1.5)
        if index < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + width, 4.4), (x + width + gap, 4.4),
                                         arrowstyle='-|>', mutation_scale=13,
                                         color=INK, lw=1.4))

    # the loop back: a failed gate sends you to the field it blames. Routed
    # below the boxes so it crosses nothing.
    ax.add_patch(FancyArrowPatch((0.2 + 2 * (width + gap) + width / 2, 1.5),
                                 (0.2 + width / 2, 1.5),
                                 arrowstyle='-|>', mutation_scale=12, color=RED,
                                 lw=1.5, connectionstyle='arc3,rad=-0.28'))
    ax.text(0.2 + width + gap + width / 2, -1.25,
            'a failed gate names the field to change, so you go back and measure '
            'again', ha='center', fontsize=9.2, color=RED)

    ax.text(0.2, -2.45, 'No code is edited at any stage. If adding a type needs a '
            'code change, the record is missing a field.',
            fontsize=9.6, color=INK)
    _save(fig, 'case-study/v1-place-glass', 'add-a-glass-type.svg')


# --------------------------------------------------------------------------
# case-study/place-glass.md
# --------------------------------------------------------------------------

# The example rack and glass the case study assumes, in millimetres. The doc
# quotes the same numbers, so change them in both places or in neither.
GLASS_RIM_OUTER: float = 70.0
GLASS_RIM_INNER: float = 64.0
PEG_DIAMETER: float = 12.0
PEG_SPACING: float = 90.0


def _glass_glyph(ax: Axes, middle_x: float, base_y: float, width: float,
                 height: float, mouth_up: bool, colour: str = BLUE) -> None:
    """Draw a small tapered tumbler, open end up or open end down."""
    half: float = width / 2
    narrow: float = half * 0.80
    if mouth_up:
        outline = [(middle_x - half, base_y + height), (middle_x - narrow, base_y),
                   (middle_x + narrow, base_y), (middle_x + half, base_y + height)]
        closed_y: float = base_y
        closed_half: float = narrow
    else:
        outline = [(middle_x - narrow, base_y), (middle_x - half, base_y + height),
                   (middle_x + half, base_y + height), (middle_x + narrow, base_y)]
        closed_y = base_y + height
        closed_half = half
    ax.add_patch(Polygon(outline, closed=False, fill=False, edgecolor=colour,
                         lw=1.8, joinstyle='round'))
    ax.plot([middle_x - closed_half, middle_x + closed_half], [closed_y, closed_y],
            color=colour, lw=3.2, solid_capstyle='butt')


def wrist_budget() -> None:
    """Why the 180 degree turn has to be planned backwards from the joint limits.

    The turn itself is free. What is not free is where in the wrist's range it
    starts, and that is settled at the moment of the grasp, long before the turn.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.6, 4.8), facecolor='white')
    ax.set_xlim(-285, 365)
    ax.set_ylim(-1.55, 3.55)
    ax.axis('off')

    limit: float = 175.0

    def lane(y: float, start: float, title: str, colour: str, verdict: str,
             ok: bool) -> None:
        ax.text(-283, y + 0.84, title, fontsize=9.8, color=INK, ha='left')
        ax.add_patch(Rectangle((-200, y - 0.09), 400, 0.18, facecolor=PALE_GREY,
                               edgecolor='none'))
        ax.add_patch(Rectangle((-200, y - 0.19), 200 - limit, 0.38,
                               facecolor=PALE_RED, edgecolor='none'))
        ax.add_patch(Rectangle((limit, y - 0.19), 200 - limit, 0.38,
                               facecolor=PALE_RED, edgecolor='none'))
        ax.plot([-limit, -limit], [y - 0.21, y + 0.21], color=RED, lw=1.4)
        ax.plot([limit, limit], [y - 0.21, y + 0.21], color=RED, lw=1.4)

        end: float = start + 180.0
        tip: float = min(end, limit)
        ax.add_patch(FancyArrowPatch((start, y + 0.42), (tip, y + 0.42),
                                     arrowstyle='-|>', mutation_scale=13,
                                     color=colour, lw=2.0))
        ax.text((start + tip) / 2, y + 0.54, 'turn 180°', fontsize=8.8,
                color=colour, ha='center')
        ax.plot([start], [y], marker='o', markersize=7, color=colour, zorder=5)
        ax.text(start, y - 0.32, f'grasp at {start:+.0f}°', fontsize=9,
                color=colour, ha='center', va='top')
        if ok:
            ax.plot([end], [y], marker='o', markersize=7, color=colour, zorder=5)
            ax.text(end, y - 0.32, f'let go at {end:+.0f}°', fontsize=9,
                    color=colour, ha='center', va='top')
        else:
            ax.plot([limit], [y], marker='X', markersize=11, color=RED, zorder=6)
        ax.text(208, y + 0.02, verdict, fontsize=9.2, color=colour, ha='left',
                va='center', linespacing=1.5)

    lane(2.00, 0.0, 'Plan A: grasp with the wrist where it happens to be', RED,
         'the wrist stops 5° short,\nholding the glass on its side', False)
    lane(0.45, -90.0, 'Plan B: turn the wrist back before closing the fingers',
         GREEN, 'the same turn, with\n85° still to spare', True)

    for edge in (-limit, limit):
        ax.text(edge, -0.42, 'joint limit', fontsize=8.6, color=RED, ha='center',
                va='top')

    # A key on the right: what the turn is for.
    _glass_glyph(ax, 265, 2.72, 46, 0.48, mouth_up=True, colour=MUTED)
    _glass_glyph(ax, 340, 2.72, 46, 0.48, mouth_up=False, colour=MUTED)
    ax.add_patch(FancyArrowPatch((293, 2.96), (312, 2.96), arrowstyle='-|>',
                                 mutation_scale=11, color=MUTED, lw=1.4))
    ax.text(302, 2.54, 'what the turn is for', fontsize=8.6, color=MUTED,
            ha='center', va='top')

    ax.text(-285, -1.46, 'The turn itself is free. Where in the range it starts is '
            'not, and that is settled at the grasp, not at the turn.',
            fontsize=9.5, color=INK)
    _save(fig, 'case-study/place-glass', 'wrist-budget.svg')


def why_depth_fails() -> None:
    """What a depth camera gives back when it is pointed at a drinking glass."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.6, 4.9), facecolor='white')
    ax.set_xlim(-0.3, 15.1)
    ax.set_ylim(-1.55, 5.35)
    ax.axis('off')

    # The camera, and the table it is looking at.
    ax.add_patch(Rectangle((0.0, 3.55), 1.15, 0.72, facecolor=PALE_GREY,
                           edgecolor=INK, lw=1.2))
    ax.add_patch(Circle((1.15, 3.91), 0.16, facecolor=INK, edgecolor='none'))
    ax.text(0.57, 4.44, 'depth camera', fontsize=9.2, color=INK, ha='center')
    ax.plot([0.5, 8.9], [0.7, 0.7], color=INK, lw=1.6)
    ax.text(0.55, 0.44, 'table', fontsize=8.8, color=MUTED)

    # An opaque mug: the light comes back, so the distance is measured.
    ax.add_patch(Rectangle((3.05, 0.7), 0.85, 1.20, facecolor=PALE_ORANGE,
                           edgecolor=ORANGE, lw=1.8))
    ax.text(3.48, 2.24, 'a mug', fontsize=9.0, color=ORANGE, ha='center')
    ax.add_patch(FancyArrowPatch((1.42, 3.74), (3.12, 1.98), arrowstyle='-|>',
                                 mutation_scale=12, color=ORANGE, lw=1.6))
    ax.add_patch(FancyArrowPatch((3.30, 1.98), (1.56, 3.58), arrowstyle='-|>',
                                 mutation_scale=12, color=ORANGE, lw=1.6))
    ax.text(0.0, 2.58, 'the light comes straight\nback, so the distance\nis '
            'measured', fontsize=8.8, color=ORANGE, ha='left', va='top',
            linespacing=1.5)

    # The glass: the light goes through, bends, and lands somewhere else.
    _glass_glyph(ax, 6.35, 0.7, 0.90, 1.20, mouth_up=True, colour=BLUE)
    ax.text(6.35, 2.06, 'a glass', fontsize=9.0, color=BLUE, ha='center')
    ax.plot([1.42, 6.06], [3.68, 1.52], color=BLUE, lw=1.6)
    ax.plot([6.06, 6.72], [1.52, 0.98], color=BLUE, lw=1.6, linestyle=(0, (5, 3)))
    ax.add_patch(FancyArrowPatch((6.72, 0.98), (8.62, 0.73), arrowstyle='-|>',
                                 mutation_scale=12, color=BLUE, lw=1.6,
                                 linestyle=(0, (5, 3))))
    ax.text(7.05, 1.72, 'it passes through and bends,\nso what comes back is the '
            'table\nbehind — or nothing at all', fontsize=8.8, color=BLUE,
            ha='left', va='center', linespacing=1.5)

    # What the two pictures of that scene look like.
    def panel(bottom: float, title: str) -> None:
        ax.add_patch(Rectangle((10.6, bottom), 3.6, 1.75, facecolor='white',
                               edgecolor=MUTED, lw=1.2))
        ax.text(10.6, bottom + 1.88, title, fontsize=9.4, color=INK, ha='left')

    panel(3.25, 'what the ordinary picture shows')
    ax.add_patch(Rectangle((11.30, 3.74), 0.60, 0.92, facecolor=PALE_ORANGE,
                           edgecolor=ORANGE, lw=1.4))
    _glass_glyph(ax, 13.15, 3.74, 0.66, 0.92, mouth_up=True, colour=BLUE)
    ax.text(12.40, 3.36, 'both of them', fontsize=8.5, color=MUTED, ha='center')

    panel(0.55, 'what the depth picture shows')
    ax.add_patch(Rectangle((11.30, 1.04), 0.60, 0.92, facecolor=ORANGE,
                           edgecolor='none', alpha=0.8))
    ax.add_patch(Rectangle((12.82, 1.04), 0.66, 0.92, facecolor='white',
                           edgecolor=RED, lw=1.4, linestyle=(0, (4, 3)),
                           hatch='///'))
    ax.text(11.60, 0.66, 'a solid block', fontsize=8.5, color=MUTED, ha='center')
    ax.text(13.15, 0.66, 'a hole', fontsize=8.5, color=RED, ha='center')

    ax.text(-0.3, -1.42, 'The ordinary picture still shows the glass. So the '
            'outline has to come from a model run on that picture, and depth is '
            'demoted to confirming it.', fontsize=9.5, color=INK)
    _save(fig, 'case-study/place-glass', 'why-depth-fails.svg')


def empty_or_full() -> None:
    """Both checks for water sit before the turn, because the turn cannot be undone."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.4, 5.0), facecolor='white')
    ax.set_xlim(-0.35, 14.9)
    ax.set_ylim(-2.35, 3.25)
    ax.axis('off')

    steps: list[tuple[float, str, str]] = [
        (0.30, 'look at it', 'is there a\nwater line?'),
        (3.30, 'pick it up', ''),
        (6.30, 'weigh it', 'more than\n260 g?'),
        (10.60, 'turn it over', ''),
    ]
    for x, title, question in steps:
        pale: str = PALE_RED if title == 'turn it over' else PALE_BLUE
        edge: str = RED if title == 'turn it over' else BLUE
        ax.add_patch(Rectangle((x, 0.55), 2.35, 0.95, facecolor=pale,
                               edgecolor=edge, lw=1.6))
        ax.text(x + 1.175, 1.02, title, fontsize=10, color=INK, ha='center',
                va='center')
        if question:
            ax.text(x + 1.175, 1.70, question, fontsize=8.8, color=MUTED,
                    ha='center', va='bottom', linespacing=1.45)

    for start, end in ((2.65, 3.30), (5.65, 6.30), (8.65, 10.60)):
        ax.add_patch(FancyArrowPatch((start, 1.02), (end, 1.02), arrowstyle='-|>',
                                     mutation_scale=12, color=INK, lw=1.3))

    # The two ways out, both of them before the turn.
    for x, answer in ((1.48, 'leave it\nwhere it is'), (7.48, 'put it back\ndown')):
        ax.add_patch(FancyArrowPatch((x, 0.50), (x, -0.55), arrowstyle='-|>',
                                     mutation_scale=12, color=ORANGE, lw=1.6))
        ax.text(x + 0.16, 0.00, 'yes', fontsize=8.6, color=ORANGE, ha='left',
                va='center')
        ax.add_patch(Rectangle((x - 1.05, -1.42), 2.10, 0.82,
                               facecolor=PALE_ORANGE, edgecolor=ORANGE, lw=1.4))
        ax.text(x, -1.01, answer, fontsize=9.0, color=INK, ha='center',
                va='center', linespacing=1.45)

    ax.plot([9.70, 9.70], [-1.60, 2.55], color=RED, lw=1.4, linestyle=(0, (5, 4)))
    ax.text(9.88, 2.50, 'the point of no return: after this,\nwater from a full '
            'glass is on the floor', fontsize=9.0, color=RED, ha='left', va='top',
            linespacing=1.5)

    ax.text(0.30, -1.92, 'This glass weighs 220 g empty and 564 g full, so a full '
            'one is not a close call — but the scales are the arm itself, and '
            'it only reads them once the glass is off the table.',
            fontsize=9.5, color=INK, va='top', linespacing=1.6)
    _save(fig, 'case-study/place-glass', 'empty-or-full.svg')


def grip_window() -> None:
    """Grip force has a window, and the fingers decide how wide that window is."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.2, 4.6), facecolor='white')
    ax.set_xlim(-0.2, 14.6)
    ax.set_ylim(-1.35, 3.60)
    ax.axis('off')

    lo: float = 3.6
    hi: float = 10.4

    def bar(y: float, slip: float, crack: float, label: str, note: str) -> None:
        ax.add_patch(Rectangle((lo, y), slip - lo, 0.50, facecolor=PALE_RED,
                               edgecolor='none'))
        ax.add_patch(Rectangle((slip, y), crack - slip, 0.50, facecolor=PALE_GREEN,
                               edgecolor='none'))
        ax.add_patch(Rectangle((crack, y), hi - crack, 0.50, facecolor=PALE_RED,
                               edgecolor='none'))
        ax.plot([slip, slip], [y - 0.05, y + 0.55], color=RED, lw=1.4)
        ax.plot([crack, crack], [y - 0.05, y + 0.55], color=RED, lw=1.4)
        ax.text((slip + crack) / 2, y + 0.25, 'it holds', fontsize=9.0, color=GREEN,
                ha='center', va='center')
        ax.text(lo - 0.15, y + 0.25, label, fontsize=9.2, color=INK, ha='right',
                va='center')
        ax.text(hi + 0.20, y + 0.25, note, fontsize=9.0, color=MUTED, ha='left',
                va='center')

    bar(2.20, 5.00, 6.55, 'hard plastic fingers', 'a window you can miss')
    bar(1.25, 4.05, 9.30, 'soft pads, dry glass', 'the pads widened it')
    bar(0.30, 5.55, 9.30, 'soft pads, wet glass', 'water moved the near edge')

    ax.add_patch(FancyArrowPatch((lo, -0.22), (hi, -0.22), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.2))
    ax.text(lo, -0.52, 'less squeeze', fontsize=9.0, color=INK, ha='left')
    ax.text(hi, -0.52, 'more squeeze', fontsize=9.0, color=INK, ha='right')

    ax.text(4.30, 3.10, 'it slides out of the fingers', fontsize=9.2, color=RED,
            ha='center')
    ax.text(9.30, 3.38, 'the rim cracks', fontsize=9.2, color=RED, ha='center')
    ax.plot([9.30, 9.30], [0.85, 3.28], color=RED, lw=1.0, linestyle=(0, (3, 3)))
    ax.text(9.48, 3.06, 'set by the glass, not by you', fontsize=8.6, color=MUTED,
            va='top', ha='left')

    ax.text(-0.2, -1.22, 'You do not pick a force. You pick fingers that widen the '
            'window, then measure where its two edges are for the glass you have.',
            fontsize=9.5, color=INK)
    _save(fig, 'case-study/place-glass', 'grip-window.svg')


def rack_clearance() -> None:
    """The peg is easy to hit. The glasses already on the rack are not.

    Both halves are drawn to scale in millimetres, from the numbers in the doc.
    """
    fig: Figure
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white')
    radius_outer: float = GLASS_RIM_OUTER / 2
    radius_inner: float = GLASS_RIM_INNER / 2

    left: Axes = axes[0]
    left.set_aspect('equal')
    left.set_xlim(-112, 112)
    left.set_ylim(-78, 62)
    left.axis('off')
    left.add_patch(Circle((0, 0), radius_outer, facecolor=PALE_BLUE,
                          edgecolor=BLUE, lw=2.0))
    left.add_patch(Circle((0, 0), radius_inner, facecolor='white',
                          edgecolor=BLUE, lw=1.1, linestyle=(0, (4, 3))))
    left.add_patch(Circle((0, 0), PEG_DIAMETER / 2, facecolor=GREY,
                          edgecolor=INK, lw=1.1))
    left.add_patch(FancyArrowPatch((PEG_DIAMETER / 2, 0), (radius_inner, 0),
                                   arrowstyle='<|-|>', mutation_scale=10,
                                   color=GREEN, lw=1.5))
    left.text(16, 8.0, '26 mm', fontsize=9.6, color=GREEN, ha='center')
    left.text(0, 50, 'against the peg', fontsize=10.6, color=GREEN, ha='center')
    left.text(0, -42, 'The peg is 12 mm across, the glass 64 mm across\n'
              'inside. You can be 26 mm out sideways and the\nglass still drops '
              'over it.', fontsize=9.2, color=INK, ha='center', va='top',
              linespacing=1.6)

    right: Axes = axes[1]
    right.set_aspect('equal')
    right.set_xlim(-112, 112)
    right.set_ylim(-78, 62)
    right.axis('off')
    for offset in (-PEG_SPACING, 0.0, PEG_SPACING):
        placing: bool = offset == 0.0
        right.add_patch(Circle((offset, 0), radius_outer,
                               facecolor=PALE_BLUE if placing else PALE_GREY,
                               edgecolor=BLUE if placing else GREY, lw=2.0))
        right.add_patch(Circle((offset, 0), PEG_DIAMETER / 2, facecolor=GREY,
                               edgecolor=INK, lw=1.0))
    for offset in (-PEG_SPACING, PEG_SPACING):
        right.text(offset, -14, 'already\nthere', fontsize=8.4, color=MUTED,
                   ha='center', va='center', linespacing=1.4)
    right.text(0, -14, 'going\nin', fontsize=8.4, color=BLUE, ha='center',
               va='center', linespacing=1.4)
    gap_left: float = -PEG_SPACING + radius_outer
    right.add_patch(FancyArrowPatch((gap_left, 22), (-radius_outer, 22),
                                    arrowstyle='<|-|>', mutation_scale=10,
                                    color=RED, lw=1.5))
    right.text((gap_left - radius_outer) / 2, 27, '10 mm', fontsize=9.6, color=RED,
               ha='center')
    right.text(0, 50, 'against the neighbours', fontsize=10.6, color=RED,
               ha='center')
    right.text(0, -42, 'The rims sit 20 mm apart, so 10 mm each side is all\n'
               'there is — and tilting a 120 mm glass by 5° swings its\n'
               'rim 10.5 mm, which uses every bit of it.', fontsize=9.2, color=INK,
               ha='center', va='top', linespacing=1.6)

    fig.text(0.5, 0.02, 'Both halves are drawn to the same scale. Landing on the '
             'peg is the easy part; getting down past the glasses already on the '
             'rack is the tolerance that decides the design.',
             fontsize=9.5, color=INK, ha='center')
    _save(fig, 'case-study/place-glass', 'rack-clearance.svg')


def weight_per_type() -> None:
    """Why the water gate needs one threshold per glass type, not one number.

    The three types overlap: any single threshold high enough to let an empty
    tall glass through is also high enough to let a full tea glass through.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.4, 5.0), facecolor='white')
    ax.set_xlim(-235, 980)
    ax.set_ylim(-1.95, 3.35)
    ax.axis('off')

    # grams -> nothing to convert; the x axis is grams directly.
    types: list[tuple[float, str, float, float, float]] = [
        (2.35, 'tea glass', 128, 273, 146),
        (1.35, 'tumbler', 218, 563, 261),
        (0.35, 'tall glass', 305, 854, 373),
    ]
    for y, name, empty, full, gate in types:
        ax.plot([empty, full], [y, y], color=PALE_BLUE, lw=11,
                solid_capstyle='butt', zorder=1)
        ax.plot([empty], [y], marker='o', markersize=8, color=GREY, zorder=4)
        ax.plot([full], [y], marker='o', markersize=8, color=BLUE, zorder=4)
        ax.text(-18, y, name, fontsize=9.6, color=INK, ha='right', va='center')
        # The tall glass's empty label would otherwise sit on the red line.
        side: str = 'right' if name == 'tall glass' else 'center'
        nudge: float = -14 if name == 'tall glass' else 0
        ax.text(empty + nudge, y + 0.26, f'{empty:.0f} g', fontsize=8.6,
                color=MUTED, ha=side)
        ax.text(full, y + 0.26, f'{full:.0f} g', fontsize=8.6, color=BLUE,
                ha='center')
        ax.plot([gate, gate], [y - 0.24, y + 0.24], color=GREEN, lw=2.0, zorder=5)
        ax.text(gate - 7, y - 0.34, f'gate {gate:.0f} g', fontsize=8.4,
                color=GREEN, ha='right', va='top')

    ax.add_patch(FancyArrowPatch((0, -0.62), (930, -0.62), arrowstyle='-|>',
                                 mutation_scale=13, color=INK, lw=1.2))
    for tick in (0, 200, 400, 600, 800):
        ax.plot([tick, tick], [-0.70, -0.62], color=INK, lw=1.0)
        ax.text(tick, -0.82, f'{tick}', fontsize=8.4, color=MUTED, ha='center',
                va='top')
    ax.text(930, -0.46, 'grams on the wrist', fontsize=9.0, color=INK, ha='right',
            va='bottom')

    # The overlap that kills a single global threshold: these two dots, and the
    # line between them, are the whole argument.
    ax.plot([273, 305], [2.24, 0.46], color=RED, lw=1.3, linestyle=(0, (4, 3)),
            zorder=3)
    for mass, y in ((273, 2.35), (305, 0.35)):
        ax.plot([mass], [y], marker='o', markersize=13, markerfacecolor='none',
                markeredgecolor=RED, markeredgewidth=1.6, zorder=6)
    ax.plot([430, 300], [2.94, 2.52], color=RED, lw=0.9)
    ax.text(430, 3.02, 'a full tea glass (273 g) is lighter than an empty tall '
            'glass (305 g)', fontsize=9.2, color=RED, ha='center')

    ax.text(-235, -1.20, 'Grey is empty, blue is full, and the pale bar between '
            'them is the water. Every glass needs its own gate, because no single '
            'number\nseparates full from empty across all three \u2014 and the '
            'numbers live in the glass library, not in the code.',
            fontsize=9.5, color=INK, va='top', linespacing=1.7)
    _save(fig, 'case-study/place-glass', 'weight-per-type.svg')


def what_language_decides() -> None:
    """A language model changes the goal of the run. It never changes the motion."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.4, 5.6), facecolor='white')
    ax.set_xlim(-0.35, 13.9)
    ax.set_ylim(-1.05, 7.35)
    ax.axis('off')

    ax.add_patch(Rectangle((0.0, 6.15), 8.4, 0.85, facecolor=PALE_PURPLE,
                           edgecolor=PURPLE, lw=1.6))
    ax.text(4.2, 6.57, '"put the tea glasses on the front row and leave the '
            'tall ones out"', fontsize=10, color=PURPLE, ha='center', va='center')
    ax.text(8.6, 6.57, 'what a person says,\nwhich changes every day',
            fontsize=8.8, color=MUTED, ha='left', va='center', linespacing=1.45)

    def block(bottom: float, height: float, title: str, body: str, pale: str,
              edge: str, side: str) -> None:
        ax.add_patch(Rectangle((0.0, bottom), 8.4, height, facecolor=pale,
                               edgecolor=edge, lw=1.6))
        ax.text(0.28, bottom + height - 0.32, title, fontsize=10, color=INK,
                ha='left', va='center')
        ax.text(0.28, bottom + height - 0.72, body, fontsize=9.0, color=MUTED,
                ha='left', va='top', linespacing=1.55)
        ax.text(8.6, bottom + height / 2, side, fontsize=8.8, color=edge,
                ha='left', va='center', linespacing=1.45)

    block(4.55, 1.25, 'the planner works out the goal',
          'which glasses, in what order, to which destination',
          PALE_PURPLE, PURPLE, 'this part is the\nlanguage model')
    block(3.05, 1.20, 'the checker refuses what cannot be done',
          'is that glass in the library? is that peg free? does it fit?',
          PALE_ORANGE, ORANGE, 'ordinary code, and\nnothing moves\nuntil it passes')
    block(0.30, 2.40, 'the recipes carry it out',
          'find it \u00b7 look for a water line \u00b7 grasp with the wrist '
          'pre-turned\nlift \u00b7 weigh it against this type\'s gate \u00b7 '
          'turn 180\u00b0\ndescend on force \u00b7 let go slowly \u00b7 check '
          'it is standing',
          PALE_GREEN, GREEN, 'unchanged from\nversion 3, and the\nonly thing that\n'
          'touches the glass')

    for top, bottom in ((6.15, 5.80), (4.55, 4.25), (3.05, 2.70)):
        ax.add_patch(FancyArrowPatch((4.2, top), (4.2, bottom), arrowstyle='-|>',
                                     mutation_scale=13, color=INK, lw=1.4))

    ax.text(-0.35, -0.42, 'The instruction decides which glass goes where. It never '
            'decides how the arm holds one, how hard it squeezes, or whether it '
            'may skip the water gate.', fontsize=9.5, color=INK)
    _save(fig, 'case-study/place-glass', 'what-language-decides.svg')


def force_signal_chain() -> None:
    """Where every force decision in the task gets its number from.

    The point is that it is one topic feeding three decisions, published by a
    stock controller, and that the fourth decision comes from somewhere else.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.6, 5.4), facecolor='white')
    ax.set_xlim(-0.35, 15.0)
    ax.set_ylim(-1.30, 5.85)
    ax.axis('off')

    def box(x: float, bottom: float, width: float, title: str, detail: str,
            pale: str, edge: str) -> None:
        ax.add_patch(Rectangle((x, bottom), width, 0.95, facecolor=pale,
                               edgecolor=edge, lw=1.5))
        ax.text(x + 0.20, bottom + 0.63, title, fontsize=9.4, color=INK,
                ha='left', va='center')
        ax.text(x + 0.20, bottom + 0.30, detail, fontsize=8.5, color=MUTED,
                ha='left', va='center')

    for x, heading in ((0.0, 'where the number comes from'),
                       (4.35, 'what publishes it'),
                       (8.85, 'what decides with it')):
        ax.text(x, 5.45, heading, fontsize=9.6, color=INK, ha='left')

    box(0.0, 2.70, 3.95, 'wrist force\u2013torque sensor',
        'or an estimate from the joint currents', PALE_BLUE, BLUE)
    box(0.0, 0.30, 3.95, 'gripper finger position',
        'which every gripper already reports', PALE_ORANGE, ORANGE)

    box(4.35, 2.70, 4.05, 'force_torque_sensor_broadcaster',
        'publishes the /wrench topic', PALE_BLUE, BLUE)
    box(4.35, 0.30, 4.05, 'gripper_controllers',
        'publishes the actual finger width', PALE_ORANGE, ORANGE)

    uses: list[tuple[float, str, str, str, str]] = [
        (3.90, 'is it empty?', 'lift 20 mm, read the payload, take off the tool weight',
         PALE_BLUE, BLUE),
        (2.70, 'has the rim met the base?', 'admittance_controller stops on contact',
         PALE_BLUE, BLUE),
        (1.50, 'is the rack carrying it?', 'only then open the fingers',
         PALE_BLUE, BLUE),
        (0.30, 'is it slipping?', 'the fingers are still closing',
         PALE_ORANGE, ORANGE),
    ]
    for bottom, title, detail, pale, edge in uses:
        box(8.85, bottom, 5.95, title, detail, pale, edge)

    ax.add_patch(FancyArrowPatch((3.95, 3.18), (4.35, 3.18), arrowstyle='-|>',
                                 mutation_scale=12, color=BLUE, lw=1.4))
    ax.add_patch(FancyArrowPatch((3.95, 0.78), (4.35, 0.78), arrowstyle='-|>',
                                 mutation_scale=12, color=ORANGE, lw=1.4))
    for target in (4.38, 3.18, 1.98):
        ax.add_patch(FancyArrowPatch((8.40, 3.18), (8.85, target),
                                     arrowstyle='-|>', mutation_scale=12,
                                     color=BLUE, lw=1.4,
                                     connectionstyle='arc3,rad=0.0'))
    ax.add_patch(FancyArrowPatch((8.40, 0.78), (8.85, 0.78), arrowstyle='-|>',
                                 mutation_scale=12, color=ORANGE, lw=1.4))

    ax.text(-0.35, -0.55, 'Three of the four decisions read one topic, published by '
            'a controller that ships with ros2_controllers. The fourth needs no '
            'force sensor\nat all, which is worth knowing before you buy one.',
            fontsize=9.5, color=INK, va='top', linespacing=1.7)
    _save(fig, 'case-study/place-glass', 'force-signal-chain.svg')


def where_to_hold() -> None:
    """Four criteria run up the height of a glass, and three of them agree.

    Drawn to scale in millimetres for the example tumbler, whose centre of
    mass works out at 53.4 mm, or 44.5 per cent of its height.
    """
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.4, 4.7), facecolor='white')
    ax.set_aspect('equal')
    ax.set_xlim(-40, 470)
    ax.set_ylim(-42, 152)
    ax.axis('off')

    outer, inner, height, wall = 35.0, 32.0, 120.0, 3.0

    # The two zones that decide the answer, drawn behind the glass.
    ax.add_patch(Rectangle((-42, 90), 84, 30, facecolor=PALE_RED,
                           edgecolor='none', zorder=0))
    ax.add_patch(Rectangle((-42, 22), 84, 26, facecolor=PALE_GREEN,
                           edgecolor='none', zorder=0))

    # The glass in section: a U of wall thickness, open at the top.
    section = [(-outer, height), (-outer, 0), (outer, 0), (outer, height),
               (inner, height), (inner, wall), (-inner, wall), (-inner, height)]
    ax.add_patch(Polygon(section, closed=True, facecolor=PALE_BLUE,
                         edgecolor=BLUE, lw=1.8, zorder=2))

    # Where gravity acts.
    com: float = 53.4
    ax.plot([0], [com], marker='o', markersize=9, color=INK, zorder=5)
    ax.plot([-inner, inner], [com, com], color=INK, lw=0.9,
            linestyle=(0, (3, 3)), zorder=4)

    # The offset a low grip leaves, measured on the right of the glass.
    quarter: float = 30.0
    ax.add_patch(FancyArrowPatch((54, quarter), (54, com), arrowstyle='<|-|>',
                                 mutation_scale=10, color=ORANGE, lw=1.5))
    ax.text(58, (quarter + com) / 2, '23 mm', fontsize=8.8, color=ORANGE,
            ha='left', va='center')

    notes: list[tuple[float, float, str, str]] = [
        (108, 103, 'the worst place to squeeze it\nan open edge with nothing to stop '
         'it going oval,\nand the part people put their mouths on', RED),
        (62, 56, 'where gravity acts\na low grip leaves a moment for the pads to '
         'take,\nwhich is a reason for taller pads, not a harder squeeze', INK),
        (20, 33, 'hold here, about a quarter of the way up\nthe base stiffens the '
         'shell against going oval, and after\nthe turn these fingers are on top, '
         'clear of the rack', GREEN),
    ]
    for y_text, y_point, body, colour in notes:
        ax.plot([76, 100], [y_point, y_text], color=MUTED, lw=0.8, zorder=1)
        ax.text(104, y_text, body, fontsize=8.8, color=colour, ha='left',
                va='center', linespacing=1.6)

    ax.text(0, 132, 'the example tumbler', fontsize=9.0, color=MUTED, ha='center')
    ax.text(-40, -26, 'Three of the four criteria want a low grip and only the '
            'centre of mass wants a middle one. That is why the answer is a low '
            'grip with tall pads,\nrather than a compromise height.', fontsize=9.5,
            color=INK, va='top', linespacing=1.7)
    _save(fig, 'case-study/place-glass', 'where-to-hold.svg')


if __name__ == '__main__':
    task_map()
    layers()
    taxonomy()
    timeline()
    add_a_glass_type()
    grip_from_profile()
    learning_path()
    what_is_expensive()
    consolidation()
    planner_families()
    position_vs_force()
    compounding_error()
    what_is_learned()
    wrist_budget()
    why_depth_fails()
    grip_window()
    rack_clearance()
    empty_or_full()
    weight_per_type()
    what_language_decides()
    force_signal_chain()
    where_to_hold()
