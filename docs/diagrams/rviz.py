"""Generate the diagrams used in docs/rviz/overview.md.

Images go to docs/images/<area>/, matching the docs/<area>/ folder that uses
them.

Run with:  pixi run python docs/diagrams/rviz.py

The figures read their numbers from the node's defaults, so if you change the
orbit radius or period in marker_publisher.py, regenerate rather than editing
the SVGs by hand.
"""

import math
import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Circle  # noqa: E402  (must follow matplotlib.use)
import matplotlib.pyplot as plt  # noqa: E402

# Defaults declared by MarkerPublisher.
RADIUS_M = 2.0
PERIOD_S = 6.0
DIAMETER_M = 0.4

AREA = 'rviz'
OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / 'images' / AREA

GRID = '#d6d6d6'
AXIS_X = '#d1495b'
AXIS_Y = '#2a9d3f'
SPHERE = '#1a99ff'
INK = '#222222'
MUTED = '#777777'


def _new_axes(size=(6.0, 6.0), xlim=(-3.2, 3.2), ylim=(-3.2, 3.2)):
    fig, ax = plt.subplots(figsize=size, facecolor='white')
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _draw_grid(ax):
    """Draw the RViz Grid display: 1 m cells on the XY plane."""
    for i in range(-3, 4):
        ax.plot([-3, 3], [i, i], color=GRID, lw=0.8, zorder=0)
        ax.plot([i, i], [-3, 3], color=GRID, lw=0.8, zorder=0)


def _draw_frame(ax, x, y, yaw, label, length=0.6, label_offset=(0.0, -0.42)):
    """Draw a coordinate frame: red +X, green +Y, like RViz's TF display."""
    for angle, color in ((yaw, AXIS_X), (yaw + math.pi / 2, AXIS_Y)):
        ax.annotate(
            '', xy=(x + length * math.cos(angle), y + length * math.sin(angle)),
            xytext=(x, y),
            arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 2.0,
                        'shrinkA': 0, 'shrinkB': 0},
            zorder=4,
        )
    ax.text(x + label_offset[0], y + label_offset[1], label, color=INK,
            fontsize=10, ha='center', va='center', family='monospace', zorder=5)


def scene():
    """Draw what the RViz window shows."""
    # Extra room on the right so the marker_frame label does not touch the edge.
    fig, ax = _new_axes(xlim=(-3.2, 4.0))
    _draw_grid(ax)

    ax.add_patch(Circle((0, 0), RADIUS_M, fill=False, ls=(0, (5, 4)),
                        color=MUTED, lw=1.2, zorder=1))

    angle = math.radians(35.0)
    mx, my = RADIUS_M * math.cos(angle), RADIUS_M * math.sin(angle)

    ax.add_patch(Circle((mx, my), DIAMETER_M / 2, color=SPHERE, zorder=3))
    _draw_frame(ax, 0, 0, 0.0, 'world', label_offset=(-0.45, -0.3))
    _draw_frame(ax, mx, my, angle + math.pi / 2, 'marker_frame',
                label_offset=(0.78, -0.46))

    ax.annotate('', xy=(mx, my), xytext=(0, 0),
                arrowprops={'arrowstyle': '-', 'color': MUTED, 'lw': 1.0, 'ls': ':'})
    ax.text(mx / 2 - 0.28, my / 2 + 0.22, f'{RADIUS_M:g} m', color=MUTED,
            fontsize=10, family='monospace', rotation=35)

    ax.text(0, 3.0, 'What you see in RViz', fontsize=13, ha='center',
            color=INK, weight='bold')
    ax.text(0, -3.05, f'{DIAMETER_M:g} m sphere, one lap every {PERIOD_S:g} s',
            fontsize=10, ha='center', color=MUTED)

    fig.savefig(OUT_DIR / 'scene.svg', bbox_inches='tight', pad_inches=0.35, facecolor='white')
    plt.close(fig)


def motion():
    """Where the frame is at each quarter of a revolution."""
    fig, ax = _new_axes(ylim=(-3.6, 3.6))

    ax.add_patch(Circle((0, 0), RADIUS_M, fill=False, ls=(0, (5, 4)),
                        color=GRID, lw=1.4, zorder=1))
    _draw_frame(ax, 0, 0, 0.0, 'world', length=0.5, label_offset=(-0.4, -0.28))

    for quarter in range(4):
        t = quarter * PERIOD_S / 4.0
        angle = 2 * math.pi * t / PERIOD_S
        x, y = RADIUS_M * math.cos(angle), RADIUS_M * math.sin(angle)

        ax.add_patch(Circle((x, y), DIAMETER_M / 2, color=SPHERE,
                            alpha=0.35 + 0.65 * (quarter == 0), zorder=3))
        # Heading is tangent to the circle: yaw = angle + pi/2.
        heading = angle + math.pi / 2
        ax.annotate(
            '', xy=(x + 0.75 * math.cos(heading), y + 0.75 * math.sin(heading)),
            xytext=(x, y),
            arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.8},
            zorder=4,
        )
        ax.text(x * 1.34, y * 1.34, f't = {t:g} s', fontsize=10, ha='center',
                va='center', color=INK, family='monospace')

    ax.text(0, 3.35, 'One revolution', fontsize=13, ha='center', color=INK,
            weight='bold')
    ax.text(0, -3.45, 'red arrow = +X of marker_frame, tangent to the path',
            fontsize=10, ha='center', color=MUTED)

    fig.savefig(OUT_DIR / 'motion.svg', bbox_inches='tight', pad_inches=0.35, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scene()
    motion()
    print(f'wrote {OUT_DIR}/scene.svg and {OUT_DIR}/motion.svg')
