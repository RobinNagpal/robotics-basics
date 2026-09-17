"""Generate the diagrams used in docs/two-arm-manipulation.md.

The images go to docs/images/two-arm-manipulation/.

Run with:  pixi run python docs/diagrams/two_arm.py
"""

import math
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402  (after use)
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'two-arm-manipulation'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
GREY: str = '#9a9a9a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'
PALE_GREY: str = '#eeeeee'


def _save(fig: Figure, name: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {IMAGES / name}')


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float], colour: str,
           style: str = '-|>', dashed: bool = False, width: float = 1.3) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=12,
                                 color=colour, lw=width, shrinkA=0, shrinkB=0,
                                 linestyle='dashed' if dashed else 'solid'))


def _arm(ax: Axes, base: tuple[float, float], reach: tuple[float, float], colour: str) -> None:
    """Draw one arm as a base, an upper link and a forearm ending at the reach point."""
    elbow: tuple[float, float] = ((base[0] + reach[0]) / 2, max(base[1], reach[1]) + 0.9)
    ax.plot([base[0], elbow[0]], [base[1], elbow[1]], color=colour, lw=4,
            solid_capstyle='round', zorder=2)
    ax.plot([elbow[0], reach[0]], [elbow[1], reach[1]], color=colour, lw=4,
            solid_capstyle='round', zorder=2)
    ax.add_patch(Rectangle((base[0] - 0.35, base[1] - 0.3), 0.7, 0.3, facecolor=colour,
                           edgecolor='none'))
    ax.plot([reach[0]], [reach[1]], marker='o', color=colour, markersize=6, zorder=3)


def coordination() -> None:
    """Draw the four kinds of two-arm work, from easiest to hardest."""
    titles: list[str] = ['1. side by side', '2. one holds, one works',
                         '3. hand over', '4. both hold one thing']
    notes: list[str] = ['two jobs at once,\nno coordination',
                        'one arm steadies,\nthe other acts',
                        'one arm passes it\nto the other',
                        'one object, two grips,\nevery moment']
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4), facecolor='white')
    for panel, ax in enumerate(axes):
        ax.set_xlim(-0.2, 6.2)
        ax.set_ylim(-0.6, 5.0)
        ax.set_aspect('equal')
        ax.axis('off')
        # The table.
        ax.plot([0.0, 6.0], [0.0, 0.0], color=GREY, lw=2)

        if panel == 0:                                   # two separate jobs
            _arm(ax, (1.0, 0.0), (1.6, 1.2), BLUE)
            _arm(ax, (5.0, 0.0), (4.4, 1.2), GREEN)
            ax.add_patch(Rectangle((1.3, 0.0), 0.6, 0.6, facecolor=PALE_ORANGE,
                                   edgecolor=ORANGE))
            ax.add_patch(Rectangle((4.1, 0.0), 0.6, 0.6, facecolor=PALE_ORANGE,
                                   edgecolor=ORANGE))
        elif panel == 1:                                 # one holds, one works
            _arm(ax, (1.0, 0.0), (2.4, 0.9), BLUE)
            _arm(ax, (5.0, 0.0), (3.4, 1.5), GREEN)
            ax.add_patch(Rectangle((2.2, 0.0), 1.6, 0.9, facecolor=PALE_ORANGE,
                                   edgecolor=ORANGE))
            ax.text(3.0, 2.2, 'held still', ha='center', fontsize=8.5, color=BLUE)
        elif panel == 2:                                 # hand over
            _arm(ax, (1.0, 0.0), (2.6, 1.6), BLUE)
            _arm(ax, (5.0, 0.0), (3.4, 1.6), GREEN)
            ax.add_patch(Rectangle((2.7, 1.4), 0.6, 0.45, facecolor=PALE_ORANGE,
                                   edgecolor=ORANGE))
            _arrow(ax, (2.6, 2.4), (3.4, 2.4), ORANGE)
        else:                                            # both hold one thing
            _arm(ax, (1.0, 0.0), (2.1, 1.5), BLUE)
            _arm(ax, (5.0, 0.0), (3.9, 1.5), GREEN)
            ax.add_patch(Rectangle((2.0, 1.3), 2.0, 0.5, facecolor=PALE_ORANGE,
                                   edgecolor=ORANGE))
            ax.text(3.0, 2.3, 'must not twist\nor drop', ha='center', fontsize=8.5,
                    color=ORANGE)

        ax.set_title(titles[panel], fontsize=10.5, color=INK)
        ax.text(3.0, -0.5, notes[panel], ha='center', va='top', fontsize=9, color=MUTED)
    fig.suptitle('The four kinds of two-arm work, in the order they get harder',
                 fontsize=11.5, color=INK, y=1.04)
    _save(fig, 'coordination.svg')


def steps() -> None:
    """Draw the five steps as a staircase, with what each one adds."""
    names: list[str] = [
        '1. drive two arms',
        '2. copy demonstrations',
        '3. make your own data',
        '4. measure generalisation',
        '5. the whole pipeline',
    ]
    adds: list[str] = [
        'a simulator, two arms,\na scripted policy',
        'a dataset and a policy:\ntrain, then evaluate',
        'generate many episodes\nfrom a few demonstrations',
        'many tasks, changed scenes,\none evaluation protocol',
        'long tasks end to end,\nand the road to a real robot',
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13, 5.6), facecolor='white')
    ax.set_xlim(0, 31)
    ax.set_ylim(0, 12.8)
    ax.axis('off')
    fills: list[str] = [PALE_GREEN, PALE_GREEN, PALE_BLUE, PALE_BLUE, PALE_ORANGE]
    edges: list[str] = [GREEN, GREEN, BLUE, BLUE, ORANGE]
    for step in range(5):
        x: float = 0.4 + step * 6.0
        y: float = 0.6 + step * 2.2
        ax.add_patch(Rectangle((x, y), 5.6, 1.9, facecolor=fills[step],
                               edgecolor=edges[step], lw=1.5))
        ax.text(x + 2.8, y + 1.35, names[step], ha='center', va='center', fontsize=10,
                color=INK)
        ax.text(x + 2.8, y + 0.6, adds[step], ha='center', va='center', fontsize=8,
                color=MUTED)
        if step < 4:
            _arrow(ax, (x + 5.6, y + 0.95), (x + 6.0, y + 2.2), INK)
    ax.text(15.5, 12.2, 'Each step keeps everything from the one below, and adds one thing',
            ha='center', fontsize=10.5, color=INK)
    _save(fig, 'steps.svg')


def loop() -> None:
    """Draw the loop each step is worked through."""
    stages: list[tuple[str, str]] = [
        ('pick one\ntask', 'the smallest task that\nstill needs two arms'),
        ('run the\nbaseline', 'their code, their data,\ntheir settings'),
        ('measure', 'success over many\nepisodes and seeds'),
        ('change\none thing', 'one only: the policy,\nthe data, the camera'),
        ('compare', 'same episodes, same seeds,\nkeep it or drop it'),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(10.5, 6.4), facecolor='white')
    ax.set_xlim(-9.0, 9.0)
    ax.set_ylim(-6.6, 6.2)
    ax.set_aspect('equal')
    ax.axis('off')

    radius: float = 3.5
    positions: list[tuple[float, float]] = []
    for index in range(5):
        angle: float = math.pi / 2 - index * 2 * math.pi / 5
        positions.append((radius * math.cos(angle) * 1.35, radius * math.sin(angle)))

    for index, ((title, note), (x, y)) in enumerate(zip(stages, positions)):
        ax.add_patch(Circle((x, y), 1.3, facecolor=PALE_BLUE, edgecolor=BLUE, lw=1.4))
        ax.text(x, y, title, ha='center', va='center', fontsize=9.5, color=INK)
        # The note sits outside the ring, on the line from the middle through the circle,
        # so that it never lands on top of another stage.
        away: float = math.hypot(x, y)
        ax.text(x + x / away * 2.9, y + y / away * 2.6, note, ha='center', va='center',
                fontsize=8.5, color=MUTED)

    for index in range(5):
        start: tuple[float, float] = positions[index]
        end: tuple[float, float] = positions[(index + 1) % 5]
        dx: float = end[0] - start[0]
        dy: float = end[1] - start[1]
        length: float = math.hypot(dx, dy)
        gap: float = 1.5
        _arrow(ax, (start[0] + dx / length * gap, start[1] + dy / length * gap),
               (end[0] - dx / length * gap, end[1] - dy / length * gap), GREEN)

    ax.text(0, 0, 'one change\nper lap', ha='center', va='center', fontsize=10.5,
            color=GREEN)
    _save(fig, 'loop.svg')


if __name__ == '__main__':
    coordination()
    steps()
    loop()
