"""Generate the diagrams used in docs/ros/ros-basics.md.

The images go to docs/images/ros/ros-basics/.

Run with:  pixi run python docs/diagrams/ros_basics.py
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
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'ros' / 'ros-basics'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'
PALE_GREY: str = '#eeeeee'


def _save(fig: Figure, name: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {IMAGES / name}')


def _node(ax: Axes, x: float, y: float, width: float, height: float, text: str,
          fill: str, edge: str) -> None:
    ax.add_patch(Rectangle((x, y), width, height, facecolor=fill, edgecolor=edge, lw=1.4))
    ax.text(x + width / 2, y + height / 2, text, ha='center', va='center', fontsize=9.5,
            color=INK)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float], colour: str,
           style: str = '-|>', dashed: bool = False) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=12,
                                 color=colour, lw=1.2, shrinkA=0, shrinkB=0,
                                 linestyle='dashed' if dashed else 'solid'))


def talking() -> None:
    """Draw the three ways nodes talk: a topic, a service and an action."""
    fig: Figure
    axes: list[Axes]
    fig, axes = plt.subplots(3, 1, figsize=(10, 7.5), facecolor='white')
    for ax in axes:
        ax.set_xlim(0, 24)
        ax.set_ylim(0, 6)
        ax.axis('off')

    # A topic: one sender, any number of receivers, no answer.
    ax = axes[0]
    _node(ax, 0.5, 2.0, 5.2, 2.0, 'publisher\nbasics_publisher', PALE_GREEN, GREEN)
    ax.add_patch(Rectangle((8.4, 2.4), 5.0, 1.2, facecolor=PALE_GREY, edgecolor=MUTED, lw=1.2))
    ax.text(10.9, 3.0, '/countdown', ha='center', va='center', fontsize=9.5, color=INK,
            family='monospace')
    _node(ax, 16.2, 3.6, 6.0, 1.7, 'subscriber', PALE_BLUE, BLUE)
    _node(ax, 16.2, 0.8, 6.0, 1.7, 'another subscriber', PALE_BLUE, BLUE)
    _arrow(ax, (5.7, 3.0), (8.4, 3.0), GREEN)
    _arrow(ax, (13.4, 3.0), (16.2, 4.4), BLUE)
    _arrow(ax, (13.4, 3.0), (16.2, 1.7), BLUE)
    ax.text(12, 5.2, 'a topic: messages flow one way, to anyone listening, and the\n'
            'sender neither knows nor waits for them', ha='center', fontsize=9.5, color=MUTED)

    # A service: one asks, one answers, the asker waits.
    ax = axes[1]
    _node(ax, 0.5, 2.0, 6.0, 2.0, 'client\nbasics_service_client', PALE_BLUE, BLUE)
    _node(ax, 16.2, 2.0, 6.0, 2.0, 'server\nbasics_service_server', PALE_GREEN, GREEN)
    _arrow(ax, (6.5, 3.4), (16.2, 3.4), BLUE)
    _arrow(ax, (16.2, 2.6), (6.5, 2.6), GREEN)
    ax.text(11.35, 4.0, 'request: a = 7, b = 5', ha='center', fontsize=9, color=BLUE,
            family='monospace')
    ax.text(11.35, 1.5, 'response: sum = 12', ha='center', fontsize=9, color=GREEN,
            family='monospace')
    ax.text(11.35, 5.2, 'a service: one question, one answer, and the asker waits for it',
            ha='center', fontsize=9.5, color=MUTED)

    # An action: a goal, progress while it runs, and a result.
    ax = axes[2]
    _node(ax, 0.5, 2.0, 6.0, 2.0, 'client\nbasics_action_client', PALE_BLUE, BLUE)
    _node(ax, 16.2, 2.0, 6.0, 2.0, 'server\nbasics_action_server', PALE_ORANGE, ORANGE)
    _arrow(ax, (6.5, 3.7), (16.2, 3.7), BLUE)
    ax.text(11.35, 4.1, 'goal: count to 5', ha='center', fontsize=9, color=BLUE,
            family='monospace')
    for step in range(4):
        _arrow(ax, (16.2, 3.0 - step * 0.35), (6.5, 3.0 - step * 0.35), ORANGE, dashed=True)
    ax.text(11.35, 3.3, 'feedback, again and again while it runs', ha='center', fontsize=9,
            color=ORANGE)
    _arrow(ax, (16.2, 1.2), (6.5, 1.2), GREEN)
    ax.text(11.35, 0.6, 'result: [1, 2, 3, 4, 5]', ha='center', fontsize=9, color=GREEN,
            family='monospace')
    ax.text(11.35, 5.2, 'an action: a long job, watched while it runs, and cancellable',
            ha='center', fontsize=9.5, color=MUTED)

    _save(fig, 'talking.svg')


def frames() -> None:
    """Draw the two frames the frames.py node publishes, and the circle the tool travels."""
    fig: Figure
    left: Axes
    right: Axes
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.8), facecolor='white',
                                      gridspec_kw={'width_ratios': (1, 1.1)})
    left.set_xlim(0, 10)
    left.set_ylim(0, 6)
    left.axis('off')
    _node(left, 2.6, 4.0, 4.8, 1.4, 'base_link', PALE_BLUE, BLUE)
    _node(left, 2.6, 0.6, 4.8, 1.4, 'tool', PALE_GREEN, GREEN)
    _arrow(left, (5.0, 4.0), (5.0, 2.0), INK)
    left.text(5.3, 3.0, 'a transform:\nwhere tool is\ninside base_link', fontsize=9,
              color=INK, va='center')
    left.text(5.0, 5.8, 'the tree of frames', ha='center', fontsize=10, color=MUTED)

    # The circle the tool goes round, as the node publishes it.
    radius: float = 0.30
    right.add_patch(Circle((0.0, 0.0), radius, fill=False, edgecolor=MUTED, lw=1.0,
                           linestyle='dashed'))
    right.plot([0], [0], marker='o', color=BLUE, markersize=8)
    right.text(0.02, -0.05, 'base_link', fontsize=9.5, color=BLUE)
    for seconds, colour in ((0.0, GREEN), (2.0, ORANGE), (4.0, RED)):
        angle: float = 2 * math.pi * seconds / 8.0
        x: float = radius * math.cos(angle)
        y: float = radius * math.sin(angle)
        right.plot([x], [y], marker='o', color=colour, markersize=7)
        right.text(x + 0.02, y + 0.02, f'tool at {seconds:.0f} s', fontsize=9, color=colour)
    right.set_xlim(-0.45, 0.62)
    right.set_ylim(-0.45, 0.45)
    right.set_aspect('equal')
    right.grid(color=PALE_GREY)
    right.set_axisbelow(True)
    right.tick_params(labelsize=8, colors=MUTED)
    right.set_title('where the node says the tool is, in metres', fontsize=10, color=MUTED)
    _save(fig, 'frames.svg')


if __name__ == '__main__':
    talking()
    frames()
