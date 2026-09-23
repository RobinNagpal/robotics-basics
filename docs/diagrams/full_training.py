"""Generate the diagrams used in the docs/13_full-training/ docs.

Each doc's images go to docs/images/full-training/<doc-name>/.

Run with:  pixi run python docs/diagrams/full_training.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'full-training'

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


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def _box(ax: Axes, x: float, y: float, width: float, height: float, title: str, note: str,
         fill: str, edge: str, title_size: float = 10.5) -> None:
    ax.add_patch(Rectangle((x, y), width, height, facecolor=fill, edgecolor=edge, lw=1.5))
    ax.text(x + width / 2, y + height * 0.66, title, ha='center', va='center',
            fontsize=title_size, color=INK)
    ax.text(x + width / 2, y + height * 0.28, note, ha='center', va='center', fontsize=8.5,
            color=MUTED)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float], colour: str,
           curve: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=12,
                                 color=colour, lw=1.3, shrinkA=0, shrinkB=0,
                                 connectionstyle=f'arc3,rad={curve}'))


def phases() -> None:
    """Draw the five phases of training the whole thing, and the loop back."""
    stages: list[tuple[str, str]] = [
        ('1. build the rig', 'two arms, cameras,\na way to drive them by hand'),
        ('2. demonstrate', 'a few hundred times,\nrecorded frame by frame'),
        ('3. make the dataset', 'one folder: pictures,\nstates, actions, labels'),
        ('4. train', 'one model, pictures in,\narm commands out'),
        ('5. evaluate', 'many attempts,\nfixed seeds, one number'),
    ]
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(13.5, 4.4), facecolor='white')
    ax.set_xlim(0, 30)
    ax.set_ylim(-1.0, 7.6)
    ax.axis('off')
    fills: list[str] = [PALE_GREY, PALE_BLUE, PALE_BLUE, PALE_GREEN, PALE_ORANGE]
    edges: list[str] = [MUTED, BLUE, BLUE, GREEN, ORANGE]
    for index, ((title, note), fill, edge) in enumerate(zip(stages, fills, edges)):
        x: float = 0.4 + index * 5.9
        _box(ax, x, 2.0, 5.1, 2.0, title, note, fill, edge)
        if index < 4:
            _arrow(ax, (x + 5.1, 3.0), (x + 5.9, 3.0), INK)

    # Back to demonstrating, not to the rig: the fix is almost always more data.
    ax.add_patch(FancyArrowPatch((26.0, 4.2), (8.9, 4.2), arrowstyle='-|>',
                                 mutation_scale=13, color=RED, lw=1.4,
                                 connectionstyle='arc3,rad=0.2'))
    ax.text(15.0, 7.2, 'it failed at the third stone — so go and demonstrate '
            'the third stone', ha='center', fontsize=9.5, color=RED)
    ax.text(15.0, 1.2, 'the only thing you change between laps is the data',
            ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'overview', 'phases.svg')


def two_designs() -> None:
    """Draw the modular system beside the trained one, to show what is replaced."""
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(2, 1, figsize=(11, 5.6), facecolor='white')
    for ax in axes:
        ax.set_xlim(0, 26)
        ax.set_ylim(0, 4.2)
        ax.axis('off')

    # Modular: every stage is a program you wrote.
    ax = axes[0]
    ax.text(0.2, 3.9, 'programmed: five stages you can inspect', fontsize=10.5, color=INK)
    stages: list[tuple[str, str]] = [
        ('see', 'mesh per stone'), ('choose', 'pose search'), ('plan', 'both arms'),
        ('place', 'force control'), ('check', 'did it stand'),
    ]
    for index, (title, note) in enumerate(stages):
        x: float = 0.2 + index * 5.2
        _box(ax, x, 1.1, 4.3, 1.9, title, note, PALE_GREY, MUTED, title_size=10)
        if index < 4:
            _arrow(ax, (x + 4.3, 2.05), (x + 5.2, 2.05), INK)
    ax.text(13.0, 0.4, 'each arrow is data you can look at: a mesh, a pose, a path',
            ha='center', fontsize=9, color=MUTED)

    # Trained: one model replaces the middle.
    ax = axes[1]
    ax.text(0.2, 3.9, 'trained: one model, and you see only what goes in and out',
            fontsize=10.5, color=INK)
    _box(ax, 0.2, 1.1, 5.6, 1.9, 'what it sees',
         "camera pictures\n+ both arms' joints", PALE_BLUE, BLUE, title_size=10)
    _box(ax, 8.6, 1.1, 8.4, 1.9, 'one trained policy',
         'learned from demonstrations', PALE_GREEN, GREEN, title_size=10)
    _box(ax, 19.8, 1.1, 6.0, 1.9, 'what it does',
         'the next 100 commands\nfor both arms', PALE_ORANGE, ORANGE, title_size=10)
    _arrow(ax, (5.8, 2.05), (8.6, 2.05), INK)
    _arrow(ax, (17.0, 2.05), (19.8, 2.05), INK)
    ax.text(13.0, 0.4, 'no mesh, no chosen pose, no path: nothing in the middle to check',
            ha='center', fontsize=9, color=RED)
    _save(fig, 'overview', 'two-designs.svg')


def episode() -> None:
    """Draw one demonstration: the phases of adding a stone, and what is recorded."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12.5, 4.6), facecolor='white')
    ax.set_xlim(-0.5, 26)
    ax.set_ylim(-2.6, 5.0)
    ax.axis('off')

    phases_in_episode: list[tuple[str, float, str]] = [
        ('reach', 3.2, PALE_GREY), ('grasp', 2.4, PALE_GREY), ('lift and turn', 4.0, PALE_BLUE),
        ('bring it over', 3.6, PALE_BLUE), ('touch down', 3.4, PALE_ORANGE),
        ('let go slowly', 3.4, PALE_ORANGE), ('watch it settle', 3.4, PALE_GREEN),
    ]
    x: float = 0.0
    for title, width, fill in phases_in_episode:
        ax.add_patch(Rectangle((x, 2.2), width, 1.2, facecolor=fill, edgecolor=GREY, lw=1.2))
        ax.text(x + width / 2, 2.8, title, ha='center', va='center', fontsize=9, color=INK)
        x += width

    ax.annotate('', xy=(x, 1.9), xytext=(0, 1.9),
                arrowprops={'arrowstyle': '<|-|>', 'color': INK, 'lw': 1.1})
    ax.text(x / 2, 1.4, 'one episode: about 20 seconds, one stone added',
            ha='center', fontsize=9.5, color=INK)

    # What is written down on every frame.
    ax.text(0, 0.6, 'recorded 30 to 50 times a second, all the way through:',
            fontsize=9.5, color=INK)
    rows: list[tuple[str, str]] = [
        ('observation.images.*', 'one picture per camera: overhead, and one on each wrist'),
        ('observation.state', 'where both arms actually are'),
        ('action', 'where the demonstrator told both arms to go'),
    ]
    for index, (key, note) in enumerate(rows):
        y: float = -0.2 - index * 0.6
        ax.text(0.3, y, key, fontsize=9, color=BLUE, family='monospace')
        ax.text(7.4, y, note, fontsize=9, color=MUTED)
    ax.text(0.3, -2.1, 'and once, at the end:', fontsize=9, color=INK)
    ax.text(5.2, -2.1, 'did the tower still stand ten seconds later?', fontsize=9, color=RED)

    # The last three phases are the contact-rich part, and the reason to train at all.
    ax.add_patch(Rectangle((x - 10.2, 2.2), 10.2, 1.2, facecolor='none', edgecolor=RED,
                           lw=1.8))
    ax.text(x - 5.1, 4.2, 'the part no one can write by hand', ha='center', fontsize=9,
            color=RED)
    ax.annotate('', xy=(x - 5.1, 3.5), xytext=(x - 5.1, 4.0),
                arrowprops={'arrowstyle': '-|>', 'color': RED, 'lw': 1.2})
    _save(fig, 'collecting-data', 'episode.svg')


def chunking() -> None:
    """Draw why a policy predicts a chunk of actions instead of one."""
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(2, 1, figsize=(11, 5.0), facecolor='white')
    for ax in axes:
        ax.set_xlim(-1.0, 22)
        ax.set_ylim(-1.4, 3.0)
        ax.axis('off')
        ax.plot([0, 20.5], [0, 0], color=GREY, lw=1.2)
        for step in range(21):
            ax.plot([step], [0], marker='|', color=GREY, markersize=6)

    ax = axes[0]
    ax.text(-0.9, 2.6, 'one action per picture', fontsize=10.5, color=INK)
    for step in range(0, 21, 2):
        ax.add_patch(Rectangle((step - 0.35, 0.25), 0.7, 0.7, facecolor=PALE_BLUE,
                               edgecolor=BLUE, lw=1.0))
    ax.text(10, 1.5, 'the policy is asked again every step; small mistakes pile up '
            'and the motion jitters', ha='center', fontsize=9, color=MUTED)
    ax.text(10, -1.0, 'time, at 50 steps a second', ha='center', fontsize=9, color=MUTED)

    ax = axes[1]
    ax.text(-0.9, 2.6, 'a chunk of 100 actions per picture', fontsize=10.5, color=INK)
    ax.add_patch(Rectangle((-0.4, 0.25), 10.8, 0.7, facecolor=PALE_GREEN, edgecolor=GREEN,
                           lw=1.4))
    ax.text(5.0, 0.6, 'one look, then 100 commands played out in order', ha='center',
            fontsize=9, color=INK)
    ax.add_patch(Rectangle((10.6, 0.25), 9.8, 0.7, facecolor=PALE_GREEN, edgecolor=GREEN,
                           lw=1.4, alpha=0.55))
    ax.text(15.5, 0.6, 'look again, next chunk', ha='center', fontsize=9, color=INK)
    ax.text(10, 1.6, 'two seconds of motion decided at once: steadier, and the arms stay '
            'in step with each other', ha='center', fontsize=9, color=MUTED)
    ax.text(10, -1.0, 'ACT does this; the chunk length is a setting (100 by default)',
            ha='center', fontsize=9, color=MUTED)
    _save(fig, 'training-and-evaluating', 'chunking.svg')


if __name__ == '__main__':
    phases()
    two_designs()
    episode()
    chunking()
