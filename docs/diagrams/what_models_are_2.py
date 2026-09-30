"""Generate the diagrams for the second half of docs/05_neural-network-models/01_what-models-are/.

That is the three documents 04_where-the-data-comes-from.md,
05_running-a-model-on-a-robot.md and 06_the-map-of-models.md. Each document's
pictures go to a folder named after it, under docs/images/what-models-are/.

Run with:  pixi run python ../docs/diagrams/what_models_are_2.py
Add --png <folder> to also write PNG copies for checking by eye.

The pictures are drawings that explain ideas. The confidence numbers in the
"confidently wrong" picture are made-up examples, and the documents say so.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'what-models-are'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b6fd1'

# One colour per model category, used in both map pictures so they match.
CATEGORY_COLOURS: dict[str, str] = {
    'seeing': '#3b82c4',
    '3d': '#6a4fb3',
    'grasp': '#e05555',
    'movement': '#2a9d3f',
    'language': '#e07b39',
    'world': '#0f8b8d',
    'touch': '#b5487a',
}


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=7)


def _title(ax: Axes, x: float, y: float, text: str) -> None:
    ax.text(x, y, text, fontsize=13, ha='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, style: str = '-|>', rad: float = 0.0) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0,
                            'connectionstyle': f'arc3,rad={rad}'}, zorder=6)


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = 'white',
         edge: str = INK, lw: float = 1.2, z: int = 2) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.08',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=z))


def _mug(ax: Axes, x: float, y: float, w: float = 0.5, h: float = 0.55,
         color: str = GRIP, z: int = 4) -> None:
    """A mug standing on (x, y), where x is the middle of its body."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=0.8,
                           zorder=z))
    ax.add_patch(Arc((x + w / 2, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90, theta2=90,
                     color=INK, lw=2.2, zorder=z))


def _camera(ax: Axes, x: float, y: float, s: float = 0.3, angle: float = -90.0) -> None:
    """A small camera body with its lens pointing at `angle` degrees."""
    ax.add_patch(Rectangle((x - s, y - s * 0.6), 2 * s, 1.2 * s, facecolor=INK,
                           edgecolor=INK, zorder=5))
    c = math.cos(math.radians(angle))
    sn = math.sin(math.radians(angle))
    ax.add_patch(Circle((x + c * s * 0.9, y + sn * s * 0.9), s * 0.45, facecolor=MUTED,
                        edgecolor=INK, zorder=6))


def _link(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = LINK,
          width: float = 7, z: int = 2) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width, solid_capstyle='round',
            zorder=z)


def _hinge(ax: Axes, p: tuple[float, float], size: float = 11, color: str = JOINT) -> None:
    ax.plot([p[0]], [p[1]], 'o', color=color, ms=size, zorder=4)
    ax.plot([p[0]], [p[1]], 'o', color=INK, ms=size * 0.25, zorder=5)


def _gripper(ax: Axes, p: tuple[float, float], angle: float, size: float = 0.35,
             open_: float = 0.6) -> None:
    """Two short fingers opening in the direction the gripper points (angle in radians)."""
    c = math.cos(angle)
    s = math.sin(angle)
    nx, ny = -s, c
    for side in (1, -1):
        root = (p[0] + side * size * open_ * nx, p[1] + side * size * open_ * ny)
        tip = (root[0] + size * c, root[1] + size * s)
        ax.plot([p[0], root[0], tip[0]], [p[1], root[1], tip[1]], color=GRIP, lw=3,
                solid_capstyle='round', zorder=5)


def _arm(ax: Axes, base: tuple[float, float], lengths: list[float], angles_deg: list[float],
         scale: float = 1.0, color: str = LINK, grip: bool = True) -> tuple[float, float]:
    """Draw a flat arm from its base; angles add up along the chain. Returns the tip."""
    ax.add_patch(Rectangle((base[0] - 0.35 * scale, base[1] - 0.18 * scale), 0.7 * scale,
                           0.18 * scale, facecolor=MUTED, edgecolor=INK, lw=0.8, zorder=3))
    p = base
    total = 0.0
    for length, a in zip(lengths, angles_deg):
        total += a
        q = (p[0] + length * math.cos(math.radians(total)),
             p[1] + length * math.sin(math.radians(total)))
        _link(ax, p, q, color=color, width=7 * scale)
        _hinge(ax, p, size=11 * scale)
        p = q
    if grip:
        _gripper(ax, p, math.radians(total), size=0.3 * scale)
    return p


def _person(ax: Axes, x: float, y: float, s: float = 1.0) -> tuple[float, float]:
    """A stick figure standing on (x, y). Returns the position of the right hand."""
    ax.add_patch(Circle((x, y + 1.75 * s), 0.2 * s, facecolor='white', edgecolor=INK,
                        lw=1.5, zorder=4))
    ax.plot([x, x], [y + 1.55 * s, y + 0.8 * s], color=INK, lw=1.5, zorder=4)
    ax.plot([x, x - 0.25 * s], [y + 0.8 * s, y], color=INK, lw=1.5, zorder=4)
    ax.plot([x, x + 0.25 * s], [y + 0.8 * s, y], color=INK, lw=1.5, zorder=4)
    hand = (x + 0.55 * s, y + 1.05 * s)
    ax.plot([x, x + 0.3 * s, hand[0]], [y + 1.4 * s, y + 1.15 * s, hand[1]], color=INK,
            lw=1.5, zorder=4)
    ax.plot([x, x - 0.3 * s], [y + 1.4 * s, y + 1.0 * s], color=INK, lw=1.5, zorder=4)
    return hand


def _network(ax: Axes, x0: float, y0: float, w: float, h: float, layers: list[int],
             node: str = LINK, edge: str = GRID, highlight: set[tuple[int, int, int]] | None = None,
             hcolour: str = GRIP) -> None:
    """A small drawing of a neural network: columns of circles joined by lines."""
    xs = np.linspace(x0, x0 + w, len(layers))
    pos: list[list[tuple[float, float]]] = []
    gap = h / max(max(layers) - 1, 1)
    for x, n in zip(xs, layers):
        ys = y0 + h / 2 + gap * (np.arange(n) - (n - 1) / 2)
        pos.append([(float(x), float(y)) for y in ys[::-1]])
    for li in range(len(pos) - 1):
        for i, a in enumerate(pos[li]):
            for j, b in enumerate(pos[li + 1]):
                hit = highlight is not None and (li, i, j) in highlight
                ax.plot([a[0], b[0]], [a[1], b[1]], color=hcolour if hit else edge,
                        lw=1.8 if hit else 0.8, zorder=2 + (1 if hit else 0))
    r = min(w / (len(layers) * 5), h / (max(layers) * 3.2))
    for col in pos:
        for p in col:
            ax.add_patch(Circle(p, r, facecolor=node, edgecolor=INK, lw=0.6, zorder=4))


# --------------------------------------------------------------------------
# 04_where-the-data-comes-from
# --------------------------------------------------------------------------

DATA_DOC: str = 'where-the-data-comes-from'


def teleoperation() -> None:
    """A person moves a small arm by hand; the robot copies it; both are recorded."""
    fig, ax = plt.subplots(figsize=(11.5, 6.4), facecolor='white')
    _axes(ax, (-0.6, 13.0), (-3.6, 4.4))

    _title(ax, 6.2, 4.05, 'Teleoperation: a person drives the robot, and everything is recorded')

    # the person and the leader arm on a small table
    ax.plot([-0.4, 3.6], [0, 0], color=MUTED, lw=1.2)
    _person(ax, 0.2, 0.0, s=1.25)
    tip_l = _arm(ax, (2.2, 0.9), [0.8, 0.7], [70, -95], scale=0.7, color=LINK_PALE,
                 grip=False)
    ax.add_patch(Rectangle((1.6, 0.0), 1.2, 0.72, facecolor='#eeeeee', edgecolor=MUTED,
                           lw=0.8, zorder=1))
    ax.plot([0.2 + 0.55 * 1.25, tip_l[0]], [1.05 * 1.25, tip_l[1]], color=INK, lw=1.2,
            ls=':', zorder=3)
    _label(ax, 1.6, -0.45, 'a person moves a small\n"leader" arm by hand', size=10)

    # the arrow that copies joint angles
    _arrow(ax, (3.9, 2.0), (6.1, 2.0), color=JOINT, lw=2.2)
    _label(ax, 5.0, 2.55, 'the same joint angles,', size=9.5, color=INK)
    _label(ax, 5.0, 1.45, 'many times a second', size=9.5, color=INK)

    # the robot arm and the mug
    ax.plot([6.3, 12.6], [0, 0], color=MUTED, lw=1.2)
    tip_r = _arm(ax, (7.3, 0.0), [2.0, 1.75], [70, -95], scale=1.0)
    _mug(ax, tip_r[0] + 0.55, 0.0, w=0.55, h=0.6)
    _camera(ax, 10.9, 3.3, s=0.28, angle=-120)
    ax.plot([10.75, 9.9], [3.05, 0.9], color=GRID, lw=1, ls='--', zorder=1)
    ax.plot([10.75, 11.6], [3.05, 0.9], color=GRID, lw=1, ls='--', zorder=1)
    _label(ax, 11.6, 3.35, 'camera', size=9.5, ha='left')
    _label(ax, 9.3, -0.45, 'the real robot arm copies it', size=10)

    # the recording strip
    _label(ax, 6.2, -1.15, 'What gets saved: one pair of "what the camera saw" and '
           '"what the arm did" at each moment', size=10.5, weight='bold')
    for i, t in enumerate(['0.0 s', '0.1 s', '0.2 s', '0.3 s']):
        x = 0.4 + i * 3.1
        _box(ax, x, -3.3, 2.7, 1.7, face='#fafafa', edge=MUTED)
        # tiny picture
        ax.add_patch(Rectangle((x + 0.15, -2.95), 1.05, 1.05, facecolor='#f3efe6',
                               edgecolor=INK, lw=0.6, zorder=3))
        _mug(ax, x + 0.62 + 0.04 * i, -2.8, w=0.3, h=0.33, z=4)
        # gripper coming down in the picture
        _gripper(ax, (x + 0.62 + 0.04 * i, -2.0 - 0.13 * i), -math.pi / 2, size=0.2,
                 open_=0.8)
        # angles
        a1 = 70 - 3 * i
        a2 = -95 + 4 * i
        _label(ax, x + 1.95, -2.2, f'{a1}°\n{a2}°\ngrip open', size=8.5, color=INK)
        _label(ax, x + 1.35, -3.12, t, size=8.5, color=MUTED)
    _save(fig, DATA_DOC, 'teleoperation.svg')


def domain_randomisation() -> None:
    """Many simulated pictures with random colours and light, and one real picture."""
    rng = np.random.default_rng(4)
    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _axes(ax, (-0.3, 15.6), (-1.2, 6.2))
    _title(ax, 5.6, 5.75, 'Simulated pictures: colours, light and positions chosen at random')
    _title(ax, 13.6, 5.75, 'A real picture')

    tables = ['#c8a27a', '#8fb3d9', '#d9d9d9', '#9bc59d', '#e6c3c3', '#6d6d6d', '#e0d38a',
              '#b39ddb']
    for k in range(8):
        col = k % 4
        row = k // 4
        x = col * 2.85
        y = 2.9 - row * 2.95
        light = rng.uniform(0.55, 1.0)
        bg = (light, light, light * rng.uniform(0.85, 1.0))
        ax.add_patch(Rectangle((x, y), 2.6, 2.4, facecolor=bg, edgecolor=INK, lw=0.8,
                               zorder=1))
        ax.add_patch(Rectangle((x, y), 2.6, 0.9, facecolor=tables[k], edgecolor='none',
                               zorder=2))
        mug_colour = matplotlib.colors.hsv_to_rgb((rng.uniform(0, 1), 0.7, 0.85))
        mx = x + rng.uniform(0.6, 1.8)
        _mug(ax, mx, y + rng.uniform(0.25, 0.55), w=0.42, h=0.5, color=mug_colour)
        # one or two random shapes that are not mugs
        for _ in range(rng.integers(1, 3)):
            sx = x + rng.uniform(0.25, 2.3)
            if abs(sx - mx) < 0.55:
                sx = x + (0.3 if mx > x + 1.3 else 2.25)
            c = matplotlib.colors.hsv_to_rgb((rng.uniform(0, 1), 0.5, 0.7))
            ax.add_patch(Rectangle((sx - 0.15, y + 0.2), 0.3, rng.uniform(0.2, 0.45),
                                   facecolor=c, edgecolor=INK, lw=0.5, zorder=3))
        # a lamp: a small yellow sun at a random spot along the top
        ax.add_patch(Circle((x + rng.uniform(0.3, 2.3), y + 2.1), 0.12, facecolor=JOINT,
                            edgecolor='none', zorder=3))

    # the real picture, drawn with a thicker frame
    x, y = 12.3, 1.6
    ax.add_patch(Rectangle((x, y), 2.6, 2.4, facecolor='#e9e4da', edgecolor=SLIDE, lw=2.5,
                           zorder=1))
    ax.add_patch(Rectangle((x, y), 2.6, 0.9, facecolor='#b08d66', edgecolor='none',
                           zorder=2))
    _mug(ax, x + 1.2, y + 0.4, w=0.42, h=0.5, color='#d9d4c7')
    _label(ax, x + 1.3, y - 0.45, 'different again from\nevery simulated picture',
           size=9.5, color=MUTED)
    _arrow(ax, (11.4, 2.8), (12.15, 2.8), color=SLIDE, lw=2)

    _label(ax, 5.6, -0.85, 'Because no two training pictures look alike, the model '
           'learns to find the mug by its shape, not by its colour.', size=10.5)
    _save(fig, DATA_DOC, 'domain-randomisation.svg')


def pretrain_then_fine_tune() -> None:
    """A big pile of general data, then a small pile of robot data, into the same network."""
    fig, ax = plt.subplots(figsize=(12.2, 5.4), facecolor='white')
    _axes(ax, (-0.4, 15.4), (-1.6, 5.4))

    _title(ax, 3.7, 5.0, 'Step 1: pretraining')
    _title(ax, 11.6, 5.0, 'Step 2: fine-tuning')

    # step 1: a big pile of pictures with captions
    rng = np.random.default_rng(1)
    for i in range(14):
        for j in range(10):
            c = matplotlib.colors.hsv_to_rgb((rng.uniform(0, 1), 0.35, 0.9))
            ax.add_patch(Rectangle((i * 0.2, 0.4 + j * 0.32), 0.18, 0.28, facecolor=c,
                                   edgecolor='none', zorder=2))
    _label(ax, 1.4, -0.05, 'a very large pile of general data:', size=9.5)
    _label(ax, 1.4, -0.5, 'pictures, captions, videos', size=9.5)
    _label(ax, 1.4, -0.95, '(millions of examples or more)', size=9.5, color=MUTED)
    _arrow(ax, (3.0, 2.0), (3.9, 2.0))
    _network(ax, 4.2, 0.6, 2.4, 2.8, [4, 5, 5, 3])
    _label(ax, 5.4, -0.05, 'a general model:', size=9.5)
    _label(ax, 5.4, -0.5, 'knows what mugs, tables', size=9.5)
    _label(ax, 5.4, -0.95, 'and sinks look like', size=9.5)

    # the carry-over arrow
    _arrow(ax, (6.9, 2.0), (9.0, 2.0), color=JOINT, lw=2.4)
    _label(ax, 7.95, 2.5, 'keep every', size=9.5)
    _label(ax, 7.95, 1.5, 'number it learned', size=9.5)

    # step 2: a small pile of robot recordings
    for i in range(3):
        for j in range(3):
            ax.add_patch(Rectangle((9.3 + i * 0.3, 1.2 + j * 0.42), 0.26, 0.36,
                                   facecolor=LINK_PALE, edgecolor=LINK, lw=0.6, zorder=2))
    _label(ax, 9.75, 0.75, 'a small pile of', size=9.5)
    _label(ax, 9.75, 0.3, 'recordings from', size=9.5)
    _label(ax, 9.75, -0.15, 'this robot', size=9.5)
    _label(ax, 9.75, -0.6, '(hundreds or thousands)', size=9.5, color=MUTED)
    _arrow(ax, (10.5, 2.0), (11.3, 2.0))
    hl = {(1, 1, 2), (1, 2, 2), (2, 2, 1), (2, 3, 1), (0, 0, 1), (2, 1, 0)}
    _network(ax, 11.6, 0.6, 2.4, 2.8, [4, 5, 5, 3], highlight=hl)
    _label(ax, 12.8, -0.05, 'the same model, adjusted:', size=9.5)
    _label(ax, 12.8, -0.5, 'now also knows how this', size=9.5)
    _label(ax, 12.8, -0.95, 'arm picks up a mug', size=9.5)
    _label(ax, 12.8, 3.85, 'red lines: numbers that changed a little', size=9, color=GRIP)
    _save(fig, DATA_DOC, 'pretrain-then-fine-tune.svg')


# --------------------------------------------------------------------------
# 05_running-a-model-on-a-robot
# --------------------------------------------------------------------------

RUN_DOC: str = 'running-a-model-on-a-robot'


def time_budgets() -> None:
    """One tenth of a second: camera frames, control-loop ticks, and three model speeds."""
    fig, ax = plt.subplots(figsize=(12.0, 5.2), facecolor='white')
    ax.set_facecolor('white')
    ax.set_xlim(-38, 108)
    ax.set_ylim(-1.2, 6.0)
    ax.axis('off')

    ax.text(33, 5.55, 'What happens in one tenth of a second (100 milliseconds)',
            fontsize=13, ha='center', color=INK, weight='bold')

    # time axis
    ax.plot([0, 100], [0, 0], color=INK, lw=1.2)
    for t in range(0, 101, 10):
        ax.plot([t, t], [0, -0.15], color=INK, lw=1)
        ax.text(t, -0.45, f'{t}', fontsize=9, ha='center', va='center', color=INK)
    ax.text(50, -0.95, 'time in milliseconds (ms)', fontsize=9.5, ha='center', color=MUTED)

    # row 1: control loop ticks every 2 ms (500 per second)
    y = 4.4
    ax.text(-2, y, 'control loop, 500 times\na second: one tick every 2 ms', fontsize=9.5,
            ha='right', va='center', color=INK)
    for t in range(0, 101, 2):
        ax.plot([t, t], [y - 0.3, y + 0.3], color=SLIDE, lw=1.2)

    # row 2: camera frames every 33.3 ms (30 per second)
    y = 3.3
    ax.text(-2, y, 'camera, 30 pictures a second:\none new picture every 33 ms', fontsize=9.5,
            ha='right', va='center', color=INK)
    for k in range(4):
        t = k * 100 / 3
        ax.add_patch(Rectangle((t - 1.6, y - 0.35), 3.2, 0.7, facecolor=LINK_PALE,
                               edgecolor=LINK, lw=1, zorder=3))

    # rows 3-5: model run times, as bars
    rows = [(2.2, 'a small model: 10 ms\n(keeps up with every picture)', 10, SLIDE),
            (1.3, 'a medium model: 30 ms\n(only just keeps up)', 30, JOINT),
            (0.4, 'a large model: 200 ms\n(does not finish in this window)', 200, GRIP)]
    for yy, text, dur, colour in rows:
        ax.text(-2, yy, text, fontsize=9.5, ha='right', va='center', color=INK)
        k = 0
        while k * 100 / 3 < 100:
            start = k * 100 / 3
            end = min(start + dur, 100)
            ax.add_patch(Rectangle((start, yy - 0.25), end - start, 0.5, facecolor=colour,
                                   edgecolor=INK, lw=0.6, alpha=0.85, zorder=3))
            if dur > 100 / 3:
                break
            k += 1
        if dur > 100:
            ax.annotate('', xy=(107, yy), xytext=(100.5, yy),
                        arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.8})
    _save(fig, RUN_DOC, 'time-budgets.svg')


def confidently_wrong() -> None:
    """Three pictures, and the scores a mug/bottle/box model gives each one."""
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.4), facecolor='white',
                             gridspec_kw={'height_ratios': [1.0, 1.0]})
    classes = ['mug', 'bottle', 'box']
    scores = [[0.96, 0.03, 0.01], [0.88, 0.02, 0.10], [0.91, 0.06, 0.03]]
    titles = ['A mug\n(seen in training)', 'A bowl\n(never seen)', 'A shoe\n(never seen)']
    verdicts = ['right', 'wrong', 'wrong']

    for k in range(3):
        pic = axes[0][k]
        _axes(pic, (0, 3), (0, 2.4))
        pic.add_patch(Rectangle((0.05, 0.05), 2.9, 2.3, facecolor='#f3efe6', edgecolor=INK,
                                lw=0.8))
        pic.add_patch(Rectangle((0.05, 0.05), 2.9, 0.7, facecolor='#c8a27a',
                                edgecolor='none'))
        if k == 0:
            _mug(pic, 1.4, 0.55, w=0.8, h=0.95)
        elif k == 1:
            pic.add_patch(Polygon([(0.85, 1.35), (2.15, 1.35), (1.85, 0.6), (1.15, 0.6)],
                                  closed=True, facecolor=AXIS_Z, edgecolor=INK, lw=0.8))
        else:
            pic.add_patch(Polygon([(0.6, 0.6), (2.4, 0.6), (2.4, 0.85), (1.6, 1.0),
                                   (1.3, 1.45), (0.9, 1.45), (0.9, 0.95), (0.6, 0.85)],
                                  closed=True, facecolor=WRIST, edgecolor=INK, lw=0.8))
        pic.set_title(titles[k], fontsize=11, color=INK)

        bars = axes[1][k]
        bars.set_facecolor('white')
        colours = [GRIP if verdicts[k] == 'wrong' else SLIDE, GRID, GRID]
        bars.barh(classes[::-1], scores[k][::-1], color=colours[::-1], edgecolor=INK, lw=0.6)
        bars.set_xlim(0, 1.25)
        for i, v in enumerate(scores[k][::-1]):
            bars.text(v + 0.03, i, f'{v:.2f}', va='center', fontsize=10, color=INK)
        for side in ('top', 'right'):
            bars.spines[side].set_visible(False)
        bars.set_xticks([0, 0.5, 1.0])
        bars.tick_params(labelsize=9.5)
        word = 'right' if verdicts[k] == 'right' else 'wrong, but still sure'
        bars.set_title(f'the model says "mug": {word}', fontsize=10.5,
                       color=SLIDE if verdicts[k] == 'right' else GRIP)
        bars.set_xlabel('score', fontsize=9.5, color=MUTED)
    fig.suptitle('A model that only knows "mug", "bottle" and "box" must pick one of them',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RUN_DOC, 'confidently-wrong.svg')


def the_loop() -> None:
    """Camera -> model -> safety check -> planner -> controller -> arm -> world -> camera."""
    fig, ax = plt.subplots(figsize=(12.0, 6.2), facecolor='white')
    _axes(ax, (-0.5, 16.0), (-1.2, 7.4))
    _title(ax, 7.75, 7.0, 'The model is one part of a loop that runs again and again')

    def station(x: float, y: float, w: float, h: float, head: str, body: str,
                edge: str = INK, face: str = 'white') -> None:
        _box(ax, x, y, w, h, face=face, edge=edge, lw=1.6)
        _label(ax, x + w / 2, y + h - 0.35, head, size=11, weight='bold')
        _label(ax, x + w / 2, y + h / 2 - 0.3, body, size=9.5)

    # top row, left to right
    station(0.0, 4.2, 3.0, 2.2, 'camera', '')
    _camera(ax, 1.5, 5.25, s=0.35, angle=0)
    _label(ax, 1.5, 4.55, 'takes a picture', size=9.5)

    station(4.0, 4.2, 3.0, 2.2, 'model', '')
    _network(ax, 4.55, 4.55, 1.9, 1.2, [3, 4, 2], node=LINK)

    station(8.0, 4.2, 3.4, 2.2, 'safety checks', 'Is the answer sure\nenough? Is the point\n'
            'inside the table?', edge=GRIP, face='#fdf0f0')

    station(12.4, 4.2, 3.2, 2.2, 'planner', 'works out a path\nthat does not hit\nanything')

    # bottom row, right to left
    station(12.4, 0.0, 3.2, 2.2, 'controller', 'turns the path into\nmotor commands,\n'
            'hundreds a second')

    # the arm and the world
    _box(ax, 4.0, 0.0, 7.4, 2.2, face='white', edge=INK, lw=1.6)
    _label(ax, 7.7, 1.85, 'the arm moves, and the world changes', size=11, weight='bold')
    ax.plot([4.3, 11.1], [0.3, 0.3], color=MUTED, lw=1)
    _arm(ax, (5.3, 0.3), [0.9, 0.8], [60, -80], scale=0.8)
    _mug(ax, 8.4, 0.3, w=0.45, h=0.5)

    # arrows
    _arrow(ax, (3.0, 5.3), (4.0, 5.3))
    _label(ax, 3.5, 5.7, 'picture', size=9)
    _arrow(ax, (7.0, 5.3), (8.0, 5.3))
    _label(ax, 7.5, 5.7, 'answer', size=9)
    _arrow(ax, (11.4, 5.3), (12.4, 5.3))
    _label(ax, 11.9, 5.7, 'OK', size=9, color=SLIDE)
    _arrow(ax, (14.0, 4.2), (14.0, 2.2))
    _arrow(ax, (12.4, 1.1), (11.4, 1.1))
    _arrow(ax, (4.0, 1.1), (1.5, 1.1))
    _arrow(ax, (1.5, 1.1), (1.5, 4.2))
    _label(ax, 1.5, 0.7, 'the camera sees the new scene', size=9.5, color=MUTED)

    # rejected answers
    _arrow(ax, (9.7, 4.2), (9.7, 3.3), color=GRIP)
    _label(ax, 9.7, 2.85, 'not OK: stop the arm,\nor try again', size=9.5, color=GRIP)
    _save(fig, RUN_DOC, 'the-loop.svg')


# --------------------------------------------------------------------------
# 06_the-map-of-models
# --------------------------------------------------------------------------

MAP_DOC: str = 'the-map-of-models'


def one_task_seven_models() -> None:
    """One arm putting the red mug in the sink, with each model category where it acts."""
    fig, ax = plt.subplots(figsize=(12.5, 7.6), facecolor='white')
    _axes(ax, (-1.0, 17.0), (-2.2, 9.2))
    _title(ax, 8.0, 8.8, '"Put the red mug in the sink": where each kind of model does its job')
    cc = CATEGORY_COLOURS

    # counter and sink
    ax.add_patch(Rectangle((2.0, -0.4), 13.0, 0.4, facecolor='#e6e0d4', edgecolor=INK,
                           lw=0.8, zorder=1))
    ax.add_patch(Polygon([(11.2, 0.0), (14.4, 0.0), (14.0, -1.3), (11.6, -1.3)], closed=True,
                         facecolor='#dfe8ef', edgecolor=INK, lw=1.0, zorder=2))
    _label(ax, 12.8, -1.75, 'sink', size=10, color=MUTED)

    # the arm reaching the mug
    tip = _arm(ax, (4.9, 0.0), [2.4, 2.1], [72, -100], scale=1.0, grip=False)
    _gripper(ax, tip, math.radians(-90), size=0.38, open_=1.15)
    _mug(ax, 7.49, 0.0, w=0.7, h=0.8)
    _mug(ax, 9.3, 0.0, w=0.55, h=0.6, color=AXIS_Z)   # a blue mug that is not the target

    # wrist camera
    _camera(ax, 5.7, 4.6, s=0.25, angle=-45)

    def tag(x: float, y: float, num: int, name: str, text: str, key: str,
            ha: str = 'left') -> None:
        colour = cc[key]
        ax.add_patch(Circle((x, y), 0.3, facecolor=colour, edgecolor='none', zorder=8))
        ax.text(x, y, str(num), fontsize=10, ha='center', va='center', color='white',
                weight='bold', zorder=9)
        dx = 0.45 if ha == 'left' else -0.45
        ax.text(x + dx, y + 0.12, name, fontsize=10.5, ha=ha, va='center', color=colour,
                weight='bold', zorder=9)
        ax.text(x + dx, y - 0.12, text, fontsize=9, ha=ha, va='top', color=INK, zorder=9)

    # 5. language: a person says the words
    _person(ax, 0.0, 0.0, s=1.4)
    _box(ax, -1.0, 3.0, 4.5, 0.9, face='#fff4ea', edge=cc['language'])
    _label(ax, 1.25, 3.45, '"Put the red mug in the sink"', size=9.5)
    tag(-0.5, 5.2, 5, 'Language', 'turns the words into\nsteps: find, pick, place', 'language')

    # 1. seeing: the camera view with a box on the red mug
    ax.plot([5.7, 7.1], [4.4, 1.9], color=cc['seeing'], lw=1, ls='--', zorder=1)
    vx, vy = 7.8, 5.3
    ax.add_patch(Rectangle((vx, vy), 2.8, 2.1, facecolor='#f3efe6', edgecolor=cc['seeing'],
                           lw=1.6, zorder=3))
    _mug(ax, vx + 1.0, vy + 0.4, w=0.5, h=0.55, z=4)
    _mug(ax, vx + 2.1, vy + 0.4, w=0.4, h=0.45, color=AXIS_Z, z=4)
    ax.add_patch(Rectangle((vx + 0.6, vy + 0.3), 1.0, 0.8, facecolor='none',
                           edgecolor=cc['seeing'], lw=1.8, zorder=5))
    _label(ax, vx + 1.1, vy + 1.35, 'red mug', size=8.5, color=cc['seeing'])
    _label(ax, vx + 1.4, vy + 1.85, 'what the camera sees', size=8.5, color=MUTED)
    tag(11.2, 7.3, 1, 'Seeing', 'finds the red mug\nin the picture', 'seeing')

    # 2. 3D: dots on the mug
    rng = np.random.default_rng(3)
    for _ in range(40):
        px = 7.49 + rng.uniform(-0.33, 0.33)
        py = rng.uniform(0.05, 0.78)
        ax.plot(px, py, 'o', color=cc['3d'], ms=2.2, zorder=6)
    tag(11.2, 5.9, 2, '3D', 'the mug\'s exact shape\nand place in space', '3d')

    # 3. grasp: a marker at the handle
    for gx in (7.49 - 0.45, 7.49 + 0.45):
        ax.plot([gx], [0.6], marker='x', color=cc['grasp'], ms=10, mew=2.5, zorder=7)
    tag(11.2, 4.5, 3, 'Grasp', 'the two red crosses:\none finger each side', 'grasp')

    # 4. movement: a dotted path from the mug to the sink
    path_x = np.linspace(7.49, 12.8, 30)
    path_y = 1.4 + 2.0 * np.sin(np.linspace(0, math.pi, 30)) - 0.8 * np.linspace(0, 1, 30)
    ax.plot(path_x, path_y, color=cc['movement'], lw=2.2, ls=(0, (3, 2)), zorder=5)
    _arrow(ax, (path_x[-2], path_y[-2]), (path_x[-1], path_y[-1] - 0.25),
           color=cc['movement'], lw=2)
    tag(14.3, 2.5, 4, 'Movement', 'the path the arm\nfollows, step by step', 'movement')

    # 6. world model: a faded mug predicted in the sink
    ax.add_patch(Rectangle((12.55, -0.95), 0.5, 0.55, facecolor='none',
                           edgecolor=cc['world'], lw=1.4, ls='--', zorder=4))
    tag(14.3, 0.9, 6, 'World model', 'predicts: "if I let go\nhere, the mug lands\nupright"',
        'world')

    # 7. touch: the fingertips
    tag(2.2, -1.25, 7, 'Touch and body', 'feels the grip; notices\nif the mug slips',
        'touch')
    ax.plot([4.3, 7.0], [-1.1, 0.75], color=cc['touch'], lw=0.8, ls=':', zorder=1)
    _save(fig, MAP_DOC, 'one-task-seven-models.svg')


def when_each_model_acts() -> None:
    """A timeline of the same task: which category is busy during which step."""
    fig, ax = plt.subplots(figsize=(12.0, 5.4), facecolor='white')
    ax.set_facecolor('white')
    ax.set_xlim(-2.4, 6.3)
    ax.set_ylim(-1.3, 8.2)
    ax.axis('off')
    ax.text(1.9, 7.85, 'The same task over time: which kind of model is busy in each step',
            fontsize=13, ha='center', color=INK, weight='bold')

    steps = ['hear the\nwords', 'find the\nmug', 'choose\nthe grip', 'reach and\nclose',
             'carry to\nthe sink', 'let go']
    rows = [('Language', 'language', [(0, 1)]),
            ('Seeing', 'seeing', [(1, 4)]),
            ('3D', '3d', [(1, 3)]),
            ('Grasp', 'grasp', [(2, 3)]),
            ('Movement', 'movement', [(3, 6)]),
            ('World model', 'world', [(4, 6)]),
            ('Touch and body', 'touch', [(3, 6)])]
    for i, s in enumerate(steps):
        ax.text(i + 0.5, -0.65, s, fontsize=9.5, ha='center', va='center', color=INK)
        ax.plot([i, i], [0, 7.2], color=GRID, lw=0.8, zorder=1)
    ax.plot([6, 6], [0, 7.2], color=GRID, lw=0.8, zorder=1)
    for r, (name, key, spans) in enumerate(rows):
        y = 6.6 - r
        ax.text(-0.2, y, name, fontsize=10.5, ha='right', va='center', color=CATEGORY_COLOURS[key],
                weight='bold')
        for a, b in spans:
            ax.add_patch(FancyBboxPatch((a + 0.06, y - 0.3), b - a - 0.12, 0.6,
                                        boxstyle='round,pad=0,rounding_size=0.12',
                                        facecolor=CATEGORY_COLOURS[key], edgecolor='none',
                                        zorder=3))
    _save(fig, MAP_DOC, 'when-each-model-acts.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    teleoperation()
    domain_randomisation()
    pretrain_then_fine_tune()
    time_budgets()
    confidently_wrong()
    the_loop()
    one_task_seven_models()
    when_each_model_acts()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
