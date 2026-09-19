"""Generate the diagrams used in docs/arms-training-methods/overview.md.

The images go to docs/images/arms-training-methods/overview/.

Run with:  pixi run python docs/diagrams/arms_training_methods.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'arms-training-methods' / 'overview'

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

# One branch of the tree: a label, its colour, and the children below it.
Node = tuple[str, list['Node']]

PROGRAMMED: list[Node] = [
    ('teach and replay\nlead the arm through, it repeats', []),
    ('offline programming\nwrite the path against a CAD model', []),
    ('scripted logic\nstate machines, behaviour trees', []),
    ('motion planning', [
        ('sampling-based: RRT, PRM', []),
        ('optimisation-based: CHOMP, TrajOpt', []),
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


def _save(fig: Figure, name: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {IMAGES / name}')


def _count_leaves(nodes: list[Node]) -> int:
    """How many rows a branch needs: one per leaf."""
    return sum(max(1, _count_leaves(children)) for _, children in nodes)


def _draw_branch(ax: Axes, nodes: list[Node], depth: int, top: float, colour: str,
                 fill: str, parent: tuple[float, float] | None) -> float:
    """Draw one level of the tree downwards from `top`, and say where it ended.

    Every node is placed on its own row unless it has children, in which case it
    is centred on them. The x position comes from the depth, so the whole tree
    reads left to right.
    """
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
            # Join this node to the children drawn just above.
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

    ax.text(-5.7, -1.0, 'Ways to make a robot arm do a complex task', fontsize=12.5,
            color=INK)

    # The two families, each a box on the left with its branch to the right.
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
    _save(fig, 'taxonomy.svg')


def layers() -> None:
    """Draw the four layers of a system, and which method usually fills each one."""
    rows: list[tuple[str, str, str, str]] = [
        ('what to do next', 'the order of the steps',
         'scripted logic  ·  behaviour tree  ·  task planner  ·  a language model', PURPLE),
        ('which skill, and where', 'pick the object, place it there',
         'a planner with learned perception  ·  a trained policy  ·  a VLA', BLUE),
        ('how to move', 'a path that misses everything',
         'motion planning  ·  learned directly by the policy', GREEN),
        ('how to touch', 'the last centimetre, and the forces',
         'force control  ·  learned from demonstrations  ·  RL', ORANGE),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.5, 4.6), facecolor='white')
    ax.set_xlim(0, 26)
    ax.set_ylim(-1.2, 4.6 * len(rows) + 0.4)
    ax.axis('off')
    fills: dict[str, str] = {PURPLE: PALE_PURPLE, BLUE: PALE_BLUE, GREEN: PALE_GREEN,
                             ORANGE: PALE_ORANGE}
    for index, (title, note, methods, colour) in enumerate(rows):
        y: float = (len(rows) - 1 - index) * 4.4
        ax.add_patch(Rectangle((0.2, y), 7.2, 3.4, facecolor=fills[colour],
                               edgecolor=colour, lw=1.5))
        ax.text(3.8, y + 2.2, title, ha='center', fontsize=10.5, color=INK)
        ax.text(3.8, y + 1.0, note, ha='center', fontsize=8.5, color=MUTED)
        ax.text(8.4, y + 1.7, methods, ha='left', va='center', fontsize=9.5, color=colour)
        if index < len(rows) - 1:
            ax.add_patch(FancyArrowPatch((3.8, y), (3.8, y - 1.0), arrowstyle='-|>',
                                         mutation_scale=12, color=INK, lw=1.2))
    ax.text(0.2, -0.9, 'Almost every working system mixes families down this stack: '
            'the top is usually programmed, the bottom is usually learned.',
            fontsize=9.5, color=INK)
    _save(fig, 'layers.svg')


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
    _save(fig, 'timeline.svg')


if __name__ == '__main__':
    taxonomy()
    layers()
    timeline()
