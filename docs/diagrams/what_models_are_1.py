"""Generate the diagrams for the first half of docs/06_learned-models/01_what-models-are/.

Each document's pictures go to a folder named after it, under
docs/images/what-models-are/:

    01_what-a-model-is.md         -> what-a-model-is/
    02_how-a-model-learns.md      -> how-a-model-learns/
    03_inside-a-neural-network.md -> inside-a-neural-network/

Run with:  pixi run python ../docs/diagrams/what_models_are_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file (the loss of a guess,
the steps downhill, the sum inside a neuron, the output of a sliding filter,
the errors of the three fitted curves), and the script prints them so the
documents can quote the same values.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (  # noqa: E402
    Arc, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle,
)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

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

MUG: str = LINK          # mugs are drawn blue
BOWL: str = WRIST        # bowls are drawn orange
GOOD: str = SLIDE
BAD: str = GRIP
MONO: str = 'DejaVu Sans Mono'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', family: str | None = None,
           va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            family=family, zorder=7)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 13) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.8, rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=16, color=color,
                                 lw=lw, connectionstyle=f'arc3,rad={rad}', zorder=6))


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = LINK_PALE,
         edge: str = LINK, lw: float = 1.5) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.15',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=3))


def _mug(ax: Axes, x: float, y: float, w: float, h: float, color: str = MUG) -> None:
    """A mug seen from the side: a body with a handle on the right. (x, y) is the bottom left."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=INK, lw=1.0, zorder=4))
    ax.add_patch(Arc((x + w, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90, theta2=90,
                     color=INK, lw=3.2, zorder=3))
    ax.add_patch(Arc((x + w, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90, theta2=90,
                     color=color, lw=1.8, zorder=3))


def _bowl(ax: Axes, x: float, y: float, w: float, h: float, color: str = BOWL) -> None:
    """A bowl seen from the side: the lower half of an ellipse. (x, y) is the bottom left."""
    t = np.linspace(math.pi, 2 * math.pi, 40)
    xs = x + w / 2 + (w / 2) * np.cos(t)
    ys = y + h + h * np.sin(t)
    ax.add_patch(Polygon(np.column_stack([xs, ys]), closed=True, facecolor=color,
                         edgecolor=INK, lw=1.0, zorder=4))


def _table(ax: Axes, x0: float, x1: float, y: float) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.4, zorder=2)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 01_what-a-model-is.md
# --------------------------------------------------------------------------

def rules_vs_learned() -> None:
    """A hand-written rule fails on a short, wide mug; a model learned from examples does not."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), facecolor='white')
    left, right = axes
    for ax in axes:
        _axes(ax, (0, 10), (0, 10))

    # left: the rule a person writes
    _title(left, 5, 9.5, 'A rule written by hand')
    left.add_patch(FancyBboxPatch((1.0, 5.6), 8.0, 3.0, boxstyle='round,pad=0.1',
                                  facecolor='#f4f4f4', edgecolor=MUTED, lw=1.0, zorder=2))
    code = ('if height > width:\n'
            '    answer = "mug"\n'
            'else:\n'
            '    answer = "bowl"')
    _label(left, 1.4, 7.1, code, size=12, ha='left', family=MONO)

    _table(left, 0.3, 9.7, 1.6)
    _mug(left, 1.0, 1.6, 1.3, 2.0)
    _label(left, 1.85, 4.2, 'tall mug', size=10)
    _label(left, 1.85, 0.9, '"mug"', size=11, color=GOOD, weight='bold')
    _bowl(left, 4.0, 1.6, 2.2, 1.0)
    _label(left, 5.1, 4.2, 'bowl', size=10)
    _label(left, 5.1, 0.9, '"bowl"', size=11, color=GOOD, weight='bold')
    _mug(left, 7.3, 1.6, 1.7, 1.1)
    _label(left, 8.3, 4.2, 'short, wide mug', size=10)
    _label(left, 8.3, 0.9, '"bowl"  (wrong)', size=11, color=BAD, weight='bold')

    # right: examples, training, a model
    _title(right, 5, 9.5, 'A model learned from examples')
    shapes = [('mug', 1.2, 1.8), ('bowl', 2.0, 0.9), ('mug', 1.7, 1.1),
              ('bowl', 1.6, 1.0), ('mug', 1.0, 1.5), ('bowl', 2.2, 1.1)]
    for i, (kind, w, h) in enumerate(shapes):
        cx = 0.9 + (i % 3) * 1.55
        cy = 7.2 if i < 3 else 5.2
        s = 0.55
        if kind == 'mug':
            _mug(right, cx - w * s / 2 - 0.1, cy, w * s, h * s)
        else:
            _bowl(right, cx - w * s / 2, cy, w * s, h * s)
        _label(right, cx, cy - 0.35, kind, size=9, color=MUTED)
    _label(right, 2.45, 4.35, 'many photos, each with its answer', size=10, color=MUTED)

    _arrow(right, (5.0, 6.5), (6.2, 6.5))
    _label(right, 5.6, 7.0, 'training', size=10, color=MUTED)
    _box(right, 6.4, 5.7, 3.0, 1.6)
    _label(right, 7.9, 6.5, 'model', size=13, weight='bold')

    _table(right, 0.3, 9.7, 1.6)
    _mug(right, 1.3, 1.6, 1.7, 1.1)
    _label(right, 2.3, 3.2, 'short, wide mug', size=10)
    _arrow(right, (3.6, 2.1), (6.3, 2.1))
    _arrow(right, (7.9, 5.6), (7.9, 2.8), color=MUTED, lw=1.2)
    _label(right, 7.9, 2.1, '"mug"', size=13, color=GOOD, weight='bold')
    _label(right, 7.9, 0.9, 'it has seen short mugs before', size=10, color=MUTED)
    _save(fig, 'what-a-model-is', 'rules-vs-learned.svg')


def mug_picture() -> NDArray[np.int64]:
    """An 8 x 8 grey picture of a dark mug on a light background, as brightness 0..255."""
    img = np.full((8, 8), 230, dtype=np.int64)
    img[2:7, 1:5] = 40            # the mug's body
    img[3, 5] = 60                # the handle, top
    img[4, 6] = 60                # the handle, side
    img[5, 5] = 60                # the handle, bottom
    img[7, :] = 150               # the table
    return img


def picture_to_numbers() -> None:
    """A tiny picture, the same picture as numbers, the model, and the numbers that come out."""
    img = mug_picture()
    fig, ax = plt.subplots(figsize=(15, 5.4), facecolor='white')
    _axes(ax, (0, 32), (0, 10.5))

    cell = 0.85
    # panel 1: the picture as a grid of grey squares
    x0, y0 = 0.4, 1.4
    for r in range(8):
        for c in range(8):
            g = img[r, c] / 255
            ax.add_patch(Rectangle((x0 + c * cell, y0 + (7 - r) * cell), cell, cell,
                                   facecolor=(g, g, g), edgecolor=GRID, lw=0.6, zorder=3))
    _title(ax, x0 + 4 * cell, 9.6, 'The picture', size=12)
    _caption(ax, x0 + 4 * cell, 0.7, '8 x 8 = 64 small squares (pixels)')

    _arrow(ax, (7.5, 4.8), (8.6, 4.8))

    # panel 2: the same picture as numbers
    x1 = 8.9
    for r in range(8):
        for c in range(8):
            ax.add_patch(Rectangle((x1 + c * cell, y0 + (7 - r) * cell), cell, cell,
                                   facecolor='white', edgecolor=GRID, lw=0.6, zorder=3))
            _label(ax, x1 + c * cell + cell / 2, y0 + (7 - r) * cell + cell / 2,
                   str(img[r, c]), size=8, family=MONO)
    _title(ax, x1 + 4 * cell, 9.6, 'The same picture as numbers', size=12)
    _caption(ax, x1 + 4 * cell, 0.7, '0 is black, 255 is white')

    _arrow(ax, (16.0, 4.8), (18.2, 4.8))
    _label(ax, 17.1, 5.4, '64 numbers', size=9, color=MUTED)

    # panel 3: the model
    _box(ax, 18.4, 3.6, 3.6, 2.4)
    _label(ax, 20.2, 4.8, 'model', size=14, weight='bold')
    _title(ax, 20.2, 9.6, 'The model', size=12)
    _caption(ax, 20.2, 2.7, 'does arithmetic\non the numbers')

    _arrow(ax, (22.2, 4.8), (24.4, 4.8))
    _label(ax, 23.3, 5.4, '2 numbers', size=9, color=MUTED)

    # panel 4: the answer as numbers
    _title(ax, 28.0, 9.6, 'What comes out', size=12)
    for i, (name, value, color) in enumerate((('mug', 0.93, MUG), ('bowl', 0.07, BOWL))):
        y = 6.3 - i * 2.4
        _label(ax, 24.8, y, name, size=12, ha='left')
        ax.add_patch(Rectangle((26.2, y - 0.4), 4.0, 0.8, facecolor='white',
                               edgecolor=GRID, lw=0.8, zorder=3))
        ax.add_patch(Rectangle((26.2, y - 0.4), 4.0 * value, 0.8, facecolor=color,
                               edgecolor='none', zorder=4))
        _label(ax, 30.5, y, f'{value:.2f}', size=12, ha='left', family=MONO)
    _caption(ax, 28.0, 2.2, 'the bigger number wins:\nthe answer is "mug"')
    _save(fig, 'what-a-model-is', 'picture-to-numbers.svg')


def _network(ax: Axes, sizes: list[int], xs: list[float], y_mid: float, gap: float,
             colors: list[str], radius: float = 0.32) -> list[list[tuple[float, float]]]:
    layers: list[list[tuple[float, float]]] = []
    for n, x in zip(sizes, xs):
        top = y_mid + gap * (n - 1) / 2
        layers.append([(x, top - i * gap) for i in range(n)])
    for a, b in zip(layers[:-1], layers[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRID, lw=0.9, zorder=2)
    for layer, color in zip(layers, colors):
        for p in layer:
            ax.add_patch(plt.Circle(p, radius, facecolor=color, edgecolor=INK, lw=1.0,
                                    zorder=4))
    return layers


def small_network() -> None:
    """A small neural network: numbers in on the left, layers of neurons, two answers out."""
    fig, ax = plt.subplots(figsize=(12.5, 6.4), facecolor='white')
    _axes(ax, (0, 20), (0, 10.5))
    layers = _network(ax, [5, 6, 6, 2], [4.0, 8.0, 12.0, 16.0], 5.0, 1.25,
                      [LINK_PALE, JOINT, JOINT, LINK_PALE])

    ins = ['230', '40', '40', '...', '150']
    for (x, y), t in zip(layers[0], ins):
        _label(ax, x - 0.7, y, t, size=10, ha='right', family=MONO)
    for (x, y), t in zip(layers[-1], ['mug  0.93', 'bowl  0.07']):
        _label(ax, x + 0.6, y, t, size=11, ha='left', family=MONO)

    _label(ax, 4.0, 9.3, 'input layer', size=11, weight='bold')
    _label(ax, 4.0, 0.6, "the picture's\nnumbers go in", size=10, color=MUTED)
    _label(ax, 10.0, 9.3, 'hidden layers', size=11, weight='bold')
    _label(ax, 10.0, 0.6, 'each circle is a neuron:\nit adds up what reaches it', size=10,
           color=MUTED)
    _label(ax, 16.0, 9.3, 'output layer', size=11, weight='bold')
    _label(ax, 16.0, 0.6, 'one number\nfor each answer', size=10, color=MUTED)

    # point at one line and say what it is
    p, q = layers[1][0], layers[2][1]
    ax.plot([p[0], q[0]], [p[1], q[1]], color=GRIP, lw=2.2, zorder=3)
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    _arrow(ax, (mid[0] - 0.4, 9.9), (mid[0] - 0.05, mid[1] + 0.12), color=GRIP, lw=1.2)
    _label(ax, mid[0] - 0.5, 10.25, 'each line has a weight: a number the model learns',
           size=10, color=GRIP)
    _save(fig, 'what-a-model-is', 'a-small-network.svg')


# --------------------------------------------------------------------------
# 02_how-a-model-learns.md
# --------------------------------------------------------------------------

def training_step() -> None:
    """One step of training: an example, a guess, how wrong it is, a small nudge."""
    p_mug = 0.40
    loss_before = -math.log(p_mug)
    p_after = 0.46
    loss_after = -math.log(p_after)
    print(f'training step: guess mug={p_mug:.2f} -> loss {loss_before:.2f}; '
          f'after nudge mug={p_after:.2f} -> loss {loss_after:.2f}')

    fig, ax = plt.subplots(figsize=(15, 5.6), facecolor='white')
    _axes(ax, (0, 32), (-1.2, 11))
    centres = [3.5, 11.5, 19.5, 27.5]
    titles = ['1. Show an example', '2. The model guesses', '3. Measure how wrong',
              '4. Nudge the weights']
    for cx, t in zip(centres, titles):
        ax.add_patch(FancyBboxPatch((cx - 3.4, 1.6), 6.8, 7.4, boxstyle='round,pad=0.1',
                                    facecolor='#fafafa', edgecolor=GRID, lw=1.0, zorder=1))
        _title(ax, cx, 8.4, t, size=12)
    for a, b in zip(centres[:-1], centres[1:]):
        _arrow(ax, (a + 3.55, 5.2), (b - 3.55, 5.2))

    # 1. the example and its label
    _table(ax, 1.0, 6.0, 3.8)
    _mug(ax, 2.5, 3.8, 1.6, 2.2)
    _label(ax, 3.5, 2.6, 'label: "mug"', size=11, weight='bold', color=GOOD)

    # 2. the guess
    for i, (name, v, color) in enumerate((('mug', p_mug, MUG), ('bowl', 1 - p_mug, BOWL))):
        y = 6.4 - i * 1.6
        _label(ax, 8.6, y, name, size=11, ha='left')
        ax.add_patch(Rectangle((10.0, y - 0.35), 3.6, 0.7, facecolor='white',
                               edgecolor=GRID, lw=0.8, zorder=3))
        ax.add_patch(Rectangle((10.0, y - 0.35), 3.6 * v, 0.7, facecolor=color,
                               edgecolor='none', zorder=4))
        _label(ax, 13.8, y, f'{v:.2f}', size=11, ha='left', family=MONO)
    _label(ax, 11.5, 2.6, 'it leans towards "bowl"', size=10, color=MUTED)

    # 3. the loss
    _label(ax, 19.5, 6.6, 'the right answer was "mug"', size=10, color=MUTED)
    _label(ax, 19.5, 5.5, f'it gave "mug" only {p_mug:.2f}', size=10, color=MUTED)
    _label(ax, 19.5, 4.2, f'loss = {loss_before:.2f}', size=16, weight='bold', color=BAD,
           family=MONO)
    _label(ax, 19.5, 2.6, 'a big loss means very wrong', size=10, color=MUTED)

    # 4. the nudge
    rows = [('0.52', '0.55'), ('-0.31', '-0.33'), ('0.08', '0.10')]
    _label(ax, 25.2, 7.3, 'weight', size=10, color=MUTED)
    _label(ax, 29.2, 7.3, 'after', size=10, color=MUTED)
    for i, (a, b) in enumerate(rows):
        y = 6.5 - i * 0.9
        _label(ax, 25.2, y, a, size=11, family=MONO)
        _arrow(ax, (26.3, y), (28.1, y), color=MUTED, lw=1.2)
        _label(ax, 29.2, y, b, size=11, family=MONO)
    _label(ax, 27.5, 3.5, f'next time: mug {p_after:.2f},\nloss {loss_after:.2f}', size=10,
           color=GOOD)
    _label(ax, 27.5, 2.3, '(thousands of weights\nchange, not three)', size=9, color=MUTED)

    # repeat
    ax.add_patch(FancyArrowPatch((27.5, 1.3), (3.5, 1.3), arrowstyle='-|>', mutation_scale=16,
                                 color=MUTED, lw=1.4, connectionstyle='arc3,rad=-0.08',
                                 zorder=6))
    _label(ax, 15.5, -0.9, 'repeat with the next example, many thousands of times', size=11,
           color=MUTED)
    _save(fig, 'how-a-model-learns', 'one-training-step.svg')


def downhill() -> None:
    """Gradient descent on one weight: each step moves the weight a little way downhill."""
    def loss(w: float) -> float:
        return 0.6 * (w - 2.0) ** 2 + 0.3

    def slope(w: float) -> float:
        return 1.2 * (w - 2.0)

    rate = 0.35
    w = -1.5
    steps = [w]
    for _ in range(6):
        w = w - rate * slope(w)
        steps.append(w)
    print('downhill steps (weight, loss):',
          ', '.join(f'({s:.2f}, {loss(s):.2f})' for s in steps))

    fig, ax = plt.subplots(figsize=(11, 6.2), facecolor='white')
    ax.set_facecolor('white')
    ws = np.linspace(-2.0, 5.0, 300)
    ax.plot(ws, [loss(v) for v in ws], color=LINK, lw=2.5, zorder=2)
    for i, s in enumerate(steps):
        ax.plot([s], [loss(s)], 'o', color=JOINT if i else GRIP, ms=13, mec=INK, zorder=5)
        _label(ax, s, loss(s) + 0.55, str(i), size=10, weight='bold')
    for a, b in zip(steps[:-1], steps[1:]):
        ax.add_patch(FancyArrowPatch((a, loss(a) - 0.15), (b, loss(b) - 0.15),
                                     arrowstyle='-|>', mutation_scale=12, color=INK, lw=1.2,
                                     connectionstyle='arc3,rad=0.35', zorder=4))
    ax.plot([2.0], [0.3], marker='*', color=GOOD, ms=18, mec=INK, zorder=4)

    ax.text(-1.25, loss(-1.5) + 0.4, 'start: a random weight,\na big loss', fontsize=10,
            color=GRIP, ha='left', va='center')
    ax.text(2.0, -0.55, 'the lowest loss:\nthe best value for this weight', fontsize=10,
            color=GOOD, ha='center', va='top')
    ax.text(0.9, 6.6, 'each step goes a little\nway downhill, and the\nsteps get smaller near\n'
            'the bottom', fontsize=10, color=MUTED, ha='left', va='center')

    ax.set_xlim(-2.0, 5.5)
    ax.set_ylim(-1.8, 8.8)
    ax.set_xlabel('the value of one weight', fontsize=11, color=INK)
    ax.set_ylabel('loss (how wrong the model is)', fontsize=11, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    _save(fig, 'how-a-model-learns', 'steps-down-the-curve.svg')


def three_fits() -> None:
    """Underfitting, a good fit and overfitting, with training dots and held-back test dots."""
    rng = np.random.default_rng(2)

    def truth(x: NDArray[np.float64]) -> NDArray[np.float64]:
        return 1.5 + 2.2 * x - 0.28 * x ** 2

    x_train = np.linspace(0.5, 7.5, 10) + rng.uniform(-0.2, 0.2, 10)
    y_train = truth(x_train) + rng.normal(0, 0.5, x_train.size)
    x_test = np.linspace(0.9, 7.1, 8) + rng.uniform(-0.2, 0.2, 8)
    y_test = truth(x_test) + rng.normal(0, 0.5, x_test.size)

    panels = [(1, 'Too simple', 'underfitting'), (2, 'About right', 'a good fit'),
              (9, 'Too closely fitted', 'overfitting')]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), facecolor='white')
    xs = np.linspace(0.5, 7.5, 400)
    for ax, (deg, title, sub) in zip(axes, panels):
        fit = np.polynomial.Polynomial.fit(x_train, y_train, deg)
        train_err = float(np.mean(np.abs(fit(x_train) - y_train)))
        test_err = float(np.mean(np.abs(fit(x_test) - y_test)))
        print(f'fit degree {deg:2d}: training error {train_err:.2f}, test error {test_err:.2f}')
        ax.set_facecolor('white')
        ax.plot(xs, fit(xs), color=LINK, lw=2.2, zorder=2)
        ax.plot(x_train, y_train, 'o', color=JOINT, mec=INK, ms=8, zorder=4,
                label='training examples')
        ax.plot(x_test, y_test, 'o', mfc='white', mec=GRIP, mew=2, ms=8, zorder=4,
                label='test examples (kept back)')
        ax.set_xlim(0, 8)
        ax.set_ylim(-2.5, 11)
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        ax.set_title(f'{title}\n({sub})', fontsize=12, color=INK, weight='bold')
        ax.set_xlabel(f'error on training: {train_err:.2f}\nerror on test: {test_err:.2f}',
                      fontsize=11, color=INK)
    axes[0].set_ylabel('output', fontsize=11, color=INK)
    axes[0].legend(loc='lower left', fontsize=9, frameon=False)
    fig.text(0.5, -0.08, 'the input goes along the bottom of each panel, the output up the side',
             ha='center', fontsize=10, color=MUTED)
    _save(fig, 'how-a-model-learns', 'too-simple-and-too-close.svg')


# --------------------------------------------------------------------------
# 03_inside-a-neural-network.md
# --------------------------------------------------------------------------

def one_neuron() -> None:
    """One neuron: multiply each input by its weight, add them up, then a simple rule."""
    inputs = [0.8, 0.2, 0.5]
    weights = [0.9, -0.4, 0.3]
    products = [a * b for a, b in zip(inputs, weights)]
    total = sum(products)
    out = max(0.0, total)
    neg_total = inputs[0] * -weights[0] + products[1] + products[2]   # first weight flipped
    print('neuron products:', ', '.join(f'{p:.2f}' for p in products),
          f'sum {total:.2f} -> output {out:.2f}; with the first weight -0.9 the sum is '
          f'{neg_total:.2f} -> output 0')

    fig, ax = plt.subplots(figsize=(14, 5.6), facecolor='white')
    _axes(ax, (0, 26), (0, 10))
    ys = [7.6, 5.0, 2.4]
    nx, ny = 13.5, 5.0
    _label(ax, 1.5, 9.4, 'inputs', size=11, weight='bold')
    _label(ax, 7.0, 9.4, 'x weight', size=11, weight='bold')
    for y, a, w, p in zip(ys, inputs, weights, products):
        ax.add_patch(plt.Circle((1.5, y), 0.6, facecolor=LINK_PALE, edgecolor=INK, zorder=4))
        _label(ax, 1.5, y, f'{a:.1f}', size=11, family=MONO)
        ax.plot([2.1, 6.2], [y, y], color=MUTED, lw=1.4, zorder=2)
        end_y = ny + (y - ny) * 0.3
        ax.plot([7.8, nx - 1.25], [y, end_y], color=MUTED, lw=1.4, zorder=2)
        ax.add_patch(FancyBboxPatch((6.2, y - 0.35), 1.6, 0.7, boxstyle='round,pad=0.05',
                                    facecolor='white', edgecolor=JOINT, lw=1.4, zorder=5))
        _label(ax, 7.0, y, f'{w:+.1f}', size=11, family=MONO)
        off = -0.5 if y < ny else 0.5
        _label(ax, 8.1, y + off, f'= {p:+.2f}', size=10, family=MONO, color=MUTED, ha='left')

    ax.add_patch(plt.Circle((nx, ny), 1.3, facecolor=JOINT, edgecolor=INK, lw=1.2, zorder=4))
    _label(ax, nx, ny + 0.35, 'add up', size=10, weight='bold')
    _label(ax, nx, ny - 0.4, f'{total:.2f}', size=12, family=MONO)
    _label(ax, nx, 2.8, 'the neuron', size=10, color=MUTED)

    _arrow(ax, (nx + 1.35, ny), (17.2, ny))
    _box(ax, 17.4, 3.6, 3.6, 2.8)
    _label(ax, 19.2, 5.8, 'the rule', size=11, weight='bold')
    _label(ax, 19.2, 4.7, 'below 0: give 0\notherwise: keep it', size=9)
    _arrow(ax, (21.2, ny), (22.8, ny))
    ax.add_patch(plt.Circle((23.9, ny), 0.8, facecolor=LINK_PALE, edgecolor=INK, zorder=4))
    _label(ax, 23.9, ny, f'{out:.2f}', size=12, family=MONO)
    _label(ax, 23.9, 3.6, 'output', size=11, weight='bold')

    _label(ax, 13, 0.6, f'{products[0]:.2f} + ({products[1]:.2f}) + {products[2]:.2f} = '
           f'{total:.2f};  {total:.2f} is not below 0, so the output is {out:.2f}',
           size=10, color=MUTED)
    _save(fig, 'inside-a-neural-network', 'one-neuron.svg')


def sliding_filter() -> None:
    """A 3 x 3 pattern detector slides over a picture and lights up where dark meets light."""
    img = np.zeros((7, 7), dtype=np.int64)
    img[:, 4:] = 1          # the right part of the picture is bright
    kern = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.int64)
    out = np.zeros((5, 5), dtype=np.int64)
    for r in range(5):
        for c in range(5):
            out[r, c] = int(np.sum(img[r:r + 3, c:c + 3] * kern))
    print('sliding filter output:\n', out)
    wr, wc = 1, 2                               # the window drawn highlighted

    fig, ax = plt.subplots(figsize=(15, 6.0), facecolor='white')
    _axes(ax, (0, 30), (-0.8, 11))
    cell = 1.0

    def grid(x0: float, y0: float, a: NDArray[np.int64], shade: bool,
             hl: tuple[int, int, int] | None, out_colors: bool = False) -> None:
        n_r, n_c = a.shape
        for r in range(n_r):
            for c in range(n_c):
                v = int(a[r, c])
                if shade:
                    face = '#ffffff' if v else '#555555'
                    txt = INK if v else 'white'
                elif out_colors:
                    face = JOINT if v > 0 else 'white'
                    txt = INK
                else:
                    face = '#fdf1d6' if v > 0 else ('#dbe8f5' if v < 0 else 'white')
                    txt = INK
                ax.add_patch(Rectangle((x0 + c * cell, y0 + (n_r - 1 - r) * cell), cell, cell,
                                       facecolor=face, edgecolor=GRID, lw=0.8, zorder=3))
                _label(ax, x0 + c * cell + 0.5, y0 + (n_r - 1 - r) * cell + 0.5, str(v),
                       size=11, color=txt, family=MONO)
        if hl is not None:
            r0, c0, size = hl
            ax.add_patch(Rectangle((x0 + c0 * cell, y0 + (n_r - r0 - size) * cell), size * cell,
                                   size * cell, facecolor='none', edgecolor=GRIP, lw=3,
                                   zorder=6))

    # the picture
    gx, gy = 0.5, 1.5
    grid(gx, gy, img, True, (wr, wc, 3))
    _title(ax, gx + 3.5, 9.9, 'The picture', size=12)
    _caption(ax, gx + 3.5, 0.6, '0 is dark, 1 is bright')

    # the filter
    kx, ky = 11.0, 4.5
    grid(kx, ky, kern, False, None)
    _title(ax, kx + 1.5, 9.9, 'The pattern detector', size=12)
    _caption(ax, kx + 1.5, 3.4, '3 x 3 weights that\nthe model learned')
    _label(ax, kx + 1.5, 8.3, 'multiply square by square\nwith the red window, add up',
           size=10, color=GRIP)
    _arrow(ax, (8.2, 6.0), (10.6, 6.0), color=GRIP)

    # the output
    ox, oy = 20.0, 2.5
    grid(ox, oy, out, False, (wr, wc, 1), out_colors=True)
    _title(ax, ox + 2.5, 9.9, 'What comes out', size=12)
    _caption(ax, ox + 2.5, 1.6, 'big numbers where dark meets bright')
    _arrow(ax, (kx + 3.4, 6.0), (ox - 0.4, 6.0), color=GRIP)
    _label(ax, 17.2, 6.6, 'one number', size=10, color=GRIP)
    _caption(ax, 15, -0.4, 'Slide the red window one square at a time and repeat, '
             'to fill in every square on the right.')
    _save(fig, 'inside-a-neural-network', 'sliding-pattern-detector.svg')


def attention_lines() -> None:
    """Attention: the word "it" looks at every other word, and looks hardest at "mug"."""
    words = ['pick', 'up', 'the', 'mug', 'and', 'put', 'it', 'in', 'the', 'bowl']
    # made-up attention weights for the word "it", chosen to show the idea; they add up to 1
    weights = [0.02, 0.01, 0.03, 0.62, 0.02, 0.05, 0.08, 0.02, 0.03, 0.12]
    assert abs(sum(weights) - 1.0) < 1e-9
    src = words.index('it')

    fig, ax = plt.subplots(figsize=(14, 5.4), facecolor='white')
    _axes(ax, (-0.5, 20.5), (0, 10))
    xs = [1.0 + 2.0 * i for i in range(len(words))]
    top, bottom = 7.6, 2.4
    for x, w in zip(xs, words):
        face = LINK_PALE if w == 'mug' else ('#fdf1d6' if w == 'bowl' else 'white')
        ax.add_patch(FancyBboxPatch((x - 0.8, top - 0.45), 1.6, 0.9, boxstyle='round,pad=0.05',
                                    facecolor=face, edgecolor=MUTED, lw=1.0, zorder=4))
        _label(ax, x, top, w, size=12)
    sx = xs[src]
    ax.add_patch(FancyBboxPatch((sx - 0.8, bottom - 0.45), 1.6, 0.9, boxstyle='round,pad=0.05',
                                facecolor=JOINT, edgecolor=INK, lw=1.2, zorder=4))
    _label(ax, sx, bottom, 'it', size=12, weight='bold')
    for x, wgt in zip(xs, weights):
        ax.plot([sx, x], [bottom + 0.5, top - 0.5], color=GRIP, lw=0.6 + 14 * wgt,
                alpha=0.35 + 0.65 * min(1.0, wgt * 3), solid_capstyle='round', zorder=2)
        _label(ax, x, top + 0.9, f'{wgt:.2f}', size=9, color=MUTED, family=MONO)
    _label(ax, 10.0, 9.5, 'how much "it" looks at each word (the numbers add up to 1)', size=10,
           color=MUTED)
    _label(ax, sx + 1.3, bottom, 'the word being worked on', size=10, color=MUTED, ha='left')
    _label(ax, 10.0, 0.7, 'thick line = looks hard.  "it" looks hardest at "mug", '
           'so the model can work out that "it" means the mug.', size=10, color=INK)
    _save(fig, 'inside-a-neural-network', 'attention-lines.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    rules_vs_learned()
    picture_to_numbers()
    small_network()
    training_step()
    downhill()
    three_fits()
    one_neuron()
    sliding_filter()
    attention_lines()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
