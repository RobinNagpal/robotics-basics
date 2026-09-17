"""Generate the diagrams used in docs/stone-stacking.md.

The images go to docs/images/stone-stacking/.

Run with:  pixi run python docs/diagrams/stone_stacking.py
"""

import math
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'stone-stacking'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
GREY: str = '#9a9a9a'
STONE: str = '#c9c2b6'
STONE_EDGE: str = '#8c857a'
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
           dashed: bool = False) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=12,
                                 color=colour, lw=1.3, shrinkA=0, shrinkB=0,
                                 linestyle='dashed' if dashed else 'solid'))


def _stone(ax: Axes, middle: tuple[float, float], size: float, seed: int,
           squash: float = 0.7) -> NDArray[np.float64]:
    """Draw one irregular stone, and give back the corners it was drawn with."""
    rng: np.random.Generator = np.random.default_rng(seed)
    corners: int = int(rng.integers(6, 9))
    angles: NDArray[np.float64] = np.sort(rng.uniform(0, 2 * math.pi, corners))
    radii: NDArray[np.float64] = size * rng.uniform(0.7, 1.15, corners)
    points: NDArray[np.float64] = np.column_stack([
        middle[0] + radii * np.cos(angles),
        middle[1] + radii * np.sin(angles) * squash,
    ])
    ax.add_patch(Polygon(points, closed=True, facecolor=STONE, edgecolor=STONE_EDGE, lw=1.4))
    return points


def _arm(ax: Axes, base: tuple[float, float], reach: tuple[float, float], colour: str,
         lift: float = 1.1) -> None:
    """Draw one arm reaching from a base to a point."""
    elbow: tuple[float, float] = ((base[0] + reach[0]) / 2, max(base[1], reach[1]) + lift)
    ax.plot([base[0], elbow[0]], [base[1], elbow[1]], color=colour, lw=3.5,
            solid_capstyle='round', zorder=4)
    ax.plot([elbow[0], reach[0]], [elbow[1], reach[1]], color=colour, lw=3.5,
            solid_capstyle='round', zorder=4)
    ax.add_patch(Rectangle((base[0] - 0.3, base[1] - 0.25), 0.6, 0.25, facecolor=colour,
                           edgecolor='none', zorder=4))
    ax.plot([reach[0]], [reach[1]], marker='o', color=colour, markersize=5, zorder=5)


def balance() -> None:
    """Draw what makes a stack stand up: the middle of mass over the contact patch."""
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.0), facecolor='white')
    titles: list[str] = ['it stands', 'it topples', 'a wider contact patch forgives more']
    notes: list[str] = [
        'the middle of mass falls\ninside the contact patch',
        'the same stone, moved 2 cm:\nthe line falls outside',
        'three contact points instead of one\nleave room for error',
    ]
    for panel, ax in enumerate(axes):
        ax.set_xlim(-3.2, 3.2)
        ax.set_ylim(-0.8, 5.2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.plot([-3.0, 3.0], [0, 0], color=GREY, lw=2)

        _stone(ax, (0.0, 0.8), 1.5, seed=1)
        offset: float = {0: 0.15, 1: 1.05, 2: 0.15}[panel]
        _stone(ax, (offset, 2.5), 1.2 if panel < 2 else 1.6, seed=4 if panel < 2 else 7)

        # The contact patch: where the upper stone actually touches the lower one.
        patch: tuple[float, float] = {0: (-0.4, 0.6), 1: (0.35, 0.95), 2: (-1.0, 1.3)}[panel]
        ax.plot(list(patch), [1.75, 1.75], color=ORANGE, lw=4, solid_capstyle='butt', zorder=6)
        contact_points: list[float] = ([patch[0], patch[1]] if panel < 2
                                       else [patch[0], (patch[0] + patch[1]) / 2, patch[1]])
        for x in contact_points:
            ax.plot([x], [1.75], marker='o', color=ORANGE, markersize=6, zorder=7)

        # The middle of mass of the upper stone, and the line straight down from it.
        middle_of_mass: float = offset
        ax.plot([middle_of_mass], [2.5], marker='o', color=RED, markersize=8, zorder=8)
        inside: bool = patch[0] <= middle_of_mass <= patch[1]
        ax.plot([middle_of_mass, middle_of_mass], [2.5, 1.55], color=RED, lw=1.4,
                linestyle='dashed', zorder=6)
        ax.text(middle_of_mass, 4.3, 'middle of mass', fontsize=8.5, color=RED, ha='center')
        ax.plot([middle_of_mass, middle_of_mass], [4.1, 3.3], color=RED, lw=0.8, alpha=0.6)
        if not inside:
            ax.text(2.0, 1.4, 'it tips', fontsize=9, color=RED, ha='center')
            ax.add_patch(FancyArrowPatch((1.6, 2.6), (2.3, 1.8), arrowstyle='-|>',
                                         mutation_scale=12, color=RED, lw=1.3))

        if panel == 0:
            ax.annotate('where it touches', xy=(0.1, 1.75), xytext=(-3.0, 0.6),
                        fontsize=8.5, color=ORANGE,
                        arrowprops={'arrowstyle': '-', 'color': ORANGE, 'lw': 0.9})
        ax.set_title(titles[panel], fontsize=10.5, color=INK)
        ax.text(0, -0.35, notes[panel], ha='center', va='top', fontsize=9, color=MUTED)
    fig.suptitle('Whether a stone stays where you put it', fontsize=11.5, color=INK, y=1.03)
    _save(fig, 'balance.svg')


def roles() -> None:
    """Draw what the second arm is for."""
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), facecolor='white')
    titles: list[str] = ['1. hold, then place', '2. turn it over to see it',
                         '3. hold on while it settles']
    notes: list[str] = [
        'one arm steadies the stack,\nthe other adds a stone',
        'pass it between grippers to scan\nevery side, and to grip a better face',
        'let go slowly, feel whether it moves,\nand catch it if it does',
    ]
    for panel, ax in enumerate(axes):
        ax.set_xlim(-0.4, 8.4)
        ax.set_ylim(-1.0, 6.6)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.plot([0.0, 8.0], [0, 0], color=GREY, lw=2)

        if panel == 0:
            _stone(ax, (4.0, 0.55), 1.3, seed=2)
            _stone(ax, (4.0, 1.65), 1.1, seed=3)
            _arm(ax, (1.2, 0.0), (2.9, 1.65), BLUE)         # steadying arm
            _stone(ax, (4.1, 3.2), 0.9, seed=5)
            _arm(ax, (6.8, 0.0), (5.0, 3.3), GREEN)         # placing arm
            ax.text(1.9, 3.5, 'holds', fontsize=9, color=BLUE)
            ax.text(6.1, 4.6, 'places', fontsize=9, color=GREEN)
        elif panel == 1:
            _stone(ax, (4.0, 2.6), 1.1, seed=6)
            _arm(ax, (1.2, 0.0), (3.0, 2.6), BLUE)
            _arm(ax, (6.8, 0.0), (5.0, 2.6), GREEN)
            _arrow(ax, (3.4, 4.3), (4.6, 4.3), ORANGE)
            ax.text(4.0, 4.6, 'hand over', fontsize=9, color=ORANGE, ha='center')
            ax.text(4.0, 1.2, 'the face it sat on\nis now visible', fontsize=8.5,
                    color=MUTED, ha='center', va='top')
        else:
            _stone(ax, (4.0, 0.55), 1.2, seed=2)
            _stone(ax, (4.1, 1.75), 1.0, seed=8)
            _arm(ax, (1.2, 0.0), (3.2, 1.8), BLUE)
            _arm(ax, (6.8, 0.0), (5.0, 1.9), GREEN)
            ax.add_patch(Circle((4.1, 1.75), 1.55, fill=False, edgecolor=RED, lw=1.2,
                                linestyle='dashed'))
            ax.text(4.1, 3.9, 'force sensors watch\nfor it slipping', fontsize=8.5,
                    color=RED, ha='center')

        ax.set_title(titles[panel], fontsize=10.5, color=INK)
        ax.text(4.0, -0.55, notes[panel], ha='center', va='top', fontsize=9, color=MUTED)
    fig.suptitle('What the second arm is for', fontsize=11.5, color=INK, y=1.04)
    _save(fig, 'roles.svg')


def pipeline() -> None:
    """Draw the loop the robot runs once per stone."""
    stages: list[tuple[str, str]] = [
        ('see', 'depth camera, segment\nthe stones, build a mesh'),
        ('choose', 'search poses in a physics\nengine: which stone, which way up'),
        ('plan', 'a path for both arms\nthat avoids the stack'),
        ('place', 'move slowly, feel the contact,\nrelease gradually'),
        ('check', 'did it stay? measure,\nlog it, and go again'),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13, 4.2), facecolor='white')
    ax.set_xlim(0, 27)
    ax.set_ylim(-1.6, 7.4)
    ax.axis('off')
    fills: list[str] = [PALE_BLUE, PALE_GREEN, PALE_GREEN, PALE_ORANGE, PALE_GREY]
    edges: list[str] = [BLUE, GREEN, GREEN, ORANGE, MUTED]
    for index, ((title, note), fill, edge) in enumerate(zip(stages, fills, edges)):
        x: float = 0.4 + index * 5.3
        ax.add_patch(Rectangle((x, 2.0), 4.3, 1.7, facecolor=fill, edgecolor=edge, lw=1.5))
        ax.text(x + 2.15, 2.85, title, ha='center', va='center', fontsize=11, color=INK)
        ax.text(x + 2.15, 1.5, note, ha='center', va='top', fontsize=8.5, color=MUTED)
        if index < 4:
            _arrow(ax, (x + 4.3, 2.85), (x + 5.3, 2.85), INK)

    # The loop back: one stone at a time, and a failure just starts the loop again.
    ax.add_patch(FancyArrowPatch((23.0, 3.9), (2.5, 3.9), arrowstyle='-|>',
                                 mutation_scale=13, color=BLUE, lw=1.3,
                                 connectionstyle='arc3,rad=0.22'))
    ax.text(12.8, 7.0, 'once per stone — and a collapse is just the next lap',
            ha='center', fontsize=9.5, color=BLUE)
    _save(fig, 'pipeline.svg')


if __name__ == '__main__':
    balance()
    roles()
    pipeline()
