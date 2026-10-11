"""Generate the diagrams for the first pages of docs/05_neural-networks/02_inside-a-network/.

Each document's pictures go to a folder named after it, under
docs/images/inside-a-network/:

    01_networks-and-neurons.md     -> networks-and-neurons/
    02_the-smallest-network.md     -> the-smallest-network/
    04_a-network-on-a-robot.md     -> a-network-on-a-robot/
    05_one-neuron-of-that-network.md -> one-neuron-of-that-network/

Run with:  python3 ../docs/diagrams/inside_a_network_0.py
Add --png <folder> to also write PNG copies for checking by eye.

The worked example is the same one the rest of the chapter uses, so the three
readings, the four-neuron layer and its weights are imported from
inside_a_network_1.py rather than written out again here. What this file adds is
the output neuron that turns the layer's four features into one answer, and that
neuron's four weights and its bias were chosen by hand, like every other weight
in the chapter. Nothing here was trained. Every number drawn is printed when the
script runs, so the documents can quote the same values.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from inside_a_network_1 import (  # noqa: E402
    B1, BIAS, GRID, GRIP, INK, JOINT, LINK, LINK_PALE, MONO, MUTED, NEU_JOB,
    OUT1, PURPLE, SHORT, SLIDE, SUM, SUMS1, TEAL, W, W1, X, Arr,
    _arrow, _axes, _box, _label, _plain, _table, relu,
)
import inside_a_network_1 as one  # noqa: E402


def sigmoid(z: Arr | float) -> Arr:
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


# --------------------------------------------------------------------------
# the output neuron that finishes the network
# --------------------------------------------------------------------------
# It reads the four features of the layer and gives one number between 0 and 1,
# read as how likely this grasp is to hold. Its weights say which features count
# for the grasp and which count against it. Chosen by hand, not trained.
W2: Arr = np.array([2.40, -1.20, -0.50, -0.80])
B2: float = 0.10
PROD2: Arr = OUT1 * W2
SUM2: float = float(PROD2.sum() + B2)
P_HOLD: float = float(sigmoid(SUM2))

# A second moment, further away, to show the same network answering differently.
FAR: Arr = np.array([0.85, 0.55, 0.30])
SUMS1_FAR: Arr = W1 @ FAR + B1
OUT1_FAR: Arr = relu(SUMS1_FAR)
SUM2_FAR: float = float((OUT1_FAR * W2).sum() + B2)
P_HOLD_FAR: float = float(sigmoid(SUM2_FAR))

# The smallest network of all: the three readings joined straight to one answer,
# with no layer in between. Same weights as the single neuron of 03_one-neuron.md.
SUM_FLAT: float = SUM
P_FLAT: float = float(sigmoid(SUM_FLAT))

IMAGES: pathlib.Path = one.IMAGES
NET: str = 'networks-and-neurons'
SML: str = 'the-smallest-network'
ROB: str = 'a-network-on-a-robot'
ONEN: str = 'one-neuron-of-that-network'


def _save(fig, folder: str, name: str) -> None:
    one._save(fig, folder, name)


def report() -> None:
    print('--- the readings and the four-neuron layer ----------------------')
    for nm, a in zip(SHORT, X):
        print(f'  {nm:11s} {a:.2f}')
    for i in range(4):
        print(f'  neuron {i + 1} ({NEU_JOB[i]:22s}) sum {SUMS1[i]:+.3f} -> {OUT1[i]:.3f}')
    print('--- the output neuron -------------------------------------------')
    for i in range(4):
        print(f'  feature {i + 1} {OUT1[i]:.3f} x {W2[i]:+.2f} = {PROD2[i]:+.3f}')
    print(f'  bias {B2:+.2f}; sum {SUM2:+.3f}; sigmoid -> {P_HOLD:.3f}')
    print('--- the same network at 0.85 m ----------------------------------')
    print(f'  features {np.round(OUT1_FAR, 3)}')
    print(f'  sum {SUM2_FAR:+.3f}; sigmoid -> {P_HOLD_FAR:.3f}')
    print('--- no middle at all --------------------------------------------')
    print(f'  the three readings straight to one answer: sum {SUM_FLAT:+.3f} '
          f'-> sigmoid {P_FLAT:.3f}')
    print('--- what each of the two networks owns --------------------------')
    flat = len(W) + 1
    layer = W1.size + B1.size
    out = W2.size + 1
    print(f'  no middle:      {len(W)} weights + 1 bias = {flat}')
    print(f'  one layer:      {W1.size} weights + {B1.size} biases = {layer}, '
          f'then {W2.size} weights + 1 bias = {out}, so {layer + out} in all')


# ==========================================================================
# 01_networks-and-neurons.md
# ==========================================================================

RAW: np.ndarray = np.array([[18, 24, 31, 27],
                            [22, 251, 249, 30],
                            [25, 250, 252, 26],
                            [19, 23, 28, 21]])


def a_number_on_its_own_says_nothing() -> None:
    """One bright blue reading, and three different things it could be."""
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    _axes(ax, (0, 10.6), (0, 4.6), equal=False)
    _label(ax, 2.0, 4.35, 'how much blue light, at each place', size=10, color=MUTED)
    for r in range(4):
        for c in range(4):
            v = int(RAW[r, c])
            hot = v > 200
            x, y = 0.5 + c * 0.75, 3.55 - r * 0.75
            ax.add_patch(plt.Rectangle((x, y - 0.7), 0.7, 0.7,
                                       facecolor='#cfe0f5' if hot else 'white',
                                       edgecolor=LINK if hot else GRID,
                                       lw=1.6 if hot else 0.9))
            _label(ax, x + 0.35, y - 0.35, str(v), size=10, family=MONO,
                   color=LINK if hot else MUTED, weight='bold' if hot else 'normal')
    _arrow(ax, (4.1, 2.3), (5.3, 2.3), color=MUTED, lw=1.6)
    _label(ax, 5.5, 2.3, '251', size=15, family=MONO, weight='bold', color=LINK, ha='left')
    _label(ax, 5.5, 1.75, 'the reading does not say which', size=9.5, color=MUTED, ha='left')
    for i, what in enumerate(['a piece of sky', 'water', 'blue paint']):
        _label(ax, 7.6, 3.5 - i * 0.6, f'could be {what}', size=10.5, ha='left')
    _save(fig, NET, 'a-number-on-its-own-says-nothing.svg')


def the_shape_of_a_network() -> None:
    """Raw readings, several stages that rewrite them, then one small answer."""
    fig, ax = plt.subplots(figsize=(9.4, 2.9))
    _axes(ax, (0, 11.2), (0, 3.4), equal=False)
    _box(ax, 0.2, 1.1, 1.5, 1.3, face='#fdf1dc', edge=JOINT)
    _label(ax, 0.95, 1.95, 'readings', size=10.5)
    _label(ax, 0.95, 1.55, 'as they come', size=9.5, color=MUTED)
    x = 2.1
    for i in range(3):
        _box(ax, x, 1.1, 1.5, 1.3)
        _label(ax, x + 0.75, 1.95, 'a layer', size=10.5)
        _label(ax, x + 0.75, 1.55, 'rewrites them', size=9.5, color=MUTED)
        _arrow(ax, (x - 0.3, 1.75), (x - 0.02, 1.75), color=MUTED, lw=1.5)
        x += 1.8
    _arrow(ax, (x - 0.3, 1.75), (x - 0.02, 1.75), color=MUTED, lw=1.5)
    _box(ax, x, 1.1, 1.9, 1.3, face='#dff0df', edge=SLIDE)
    _label(ax, x + 0.95, 1.95, 'one small model', size=10.5)
    _label(ax, x + 0.95, 1.55, 'gives the answer', size=9.5, color=MUTED)
    ax.plot([2.1, 2.1, 7.2, 7.2], [0.85, 0.5, 0.5, 0.85], color=MUTED, lw=1.1)
    _label(ax, 4.65, 0.2, 'training decides what these do', size=10, color=MUTED)
    _save(fig, NET, 'the-shape-of-a-network.svg')


def the_words_on_one_network() -> None:
    """Every word this chapter uses, marked on one small network."""
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    _axes(ax, (0, 10.0), (0.4, 5.4), equal=False)
    xs = [1.3, 4.3, 7.6]
    ys_in = [3.9, 3.0, 2.1]
    ys_h = [4.3, 3.4, 2.5, 1.6]
    for y in ys_in:
        for yh in ys_h:
            ax.plot([xs[0] + 0.3, xs[1] - 0.3], [y, yh], color=LINK_PALE, lw=0.9, zorder=1)
    for yh in ys_h:
        ax.plot([xs[1] + 0.3, xs[2] - 0.3], [yh, 3.0], color=LINK_PALE, lw=0.9, zorder=1)
    for i, y in enumerate(ys_in):
        ax.add_patch(plt.Circle((xs[0], y), 0.28, facecolor='#fdf1dc', edgecolor=JOINT,
                                lw=1.4, zorder=3))
        _label(ax, xs[0] - 0.55, y, SHORT[i], size=9.5, ha='right', color=MUTED)
    for y in ys_h:
        ax.add_patch(plt.Circle((xs[1], y), 0.28, facecolor=LINK_PALE, edgecolor=LINK,
                                lw=1.4, zorder=3))
    ax.add_patch(plt.Circle((xs[2], 3.0), 0.28, facecolor='#dff0df', edgecolor=SLIDE,
                            lw=1.4, zorder=3))
    _label(ax, xs[0], 4.8, 'input layer', size=10.5, weight='bold', color=JOINT)
    _label(ax, xs[1], 4.95, 'hidden layer', size=10.5, weight='bold', color=LINK)
    _label(ax, xs[2], 4.8, 'output layer', size=10.5, weight='bold', color=SLIDE)
    _arrow(ax, (xs[1] + 1.1, 1.0), (xs[1] + 0.25, 1.45), color=MUTED, lw=1.2)
    _label(ax, xs[1] + 1.2, 0.85, 'one circle is a neuron', size=9.5, color=MUTED, ha='left')
    _arrow(ax, (2.3, 0.85), (2.75, 2.35), color=MUTED, lw=1.2)
    _label(ax, 2.2, 0.7, 'one line is a weight', size=9.5, color=MUTED, ha='center')
    _save(fig, NET, 'the-words-on-one-network.svg')


def given_and_chosen() -> None:
    """What the problem hands you, and what is left for you to decide."""
    rows = [['what the problem hands you', 'what you choose'],
            ['how many numbers go in', 'how many layers'],
            ['what the answer has to be', 'how many neurons in each layer'],
            ['the examples to learn from', 'which rule follows each layer'],
            ['', 'and the output rule has to match the answer']]
    fig, ax = plt.subplots(figsize=(8.8, 2.6))
    _axes(ax, (0, 10.0), (0.1, 4.6), equal=False)
    _table(ax, 0.2, 4.5, [4.6, 5.0], rows, row_h=0.84, mono_from=9, size=10.5)
    _save(fig, NET, 'given-and-chosen.svg')


# ==========================================================================
# 02_the-smallest-network.md
# ==========================================================================

def _net_sketch(ax, xs, ys_in, ys_h, y_out, show_hidden: bool) -> None:
    if show_hidden:
        for y in ys_in:
            for yh in ys_h:
                ax.plot([xs[0] + 0.26, xs[1] - 0.26], [y, yh], color=LINK_PALE, lw=0.9, zorder=1)
        for yh in ys_h:
            ax.plot([xs[1] + 0.26, xs[2] - 0.26], [yh, y_out], color=LINK_PALE, lw=0.9, zorder=1)
        for yh in ys_h:
            ax.add_patch(plt.Circle((xs[1], yh), 0.26, facecolor=LINK_PALE, edgecolor=LINK,
                                    lw=1.4, zorder=3))
    else:
        for y in ys_in:
            ax.plot([xs[0] + 0.26, xs[2] - 0.26], [y, y_out], color=LINK_PALE, lw=0.9, zorder=1)
    for i, y in enumerate(ys_in):
        ax.add_patch(plt.Circle((xs[0], y), 0.26, facecolor='#fdf1dc', edgecolor=JOINT,
                                lw=1.4, zorder=3))
        _label(ax, xs[0], y, f'{X[i]:.2f}', size=9, family=MONO)
    ax.add_patch(plt.Circle((xs[2], y_out), 0.26, facecolor='#dff0df', edgecolor=SLIDE,
                            lw=1.4, zorder=3))


def no_middle_at_all() -> None:
    """Three readings joined straight to one answer: the smallest network there is."""
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    _axes(ax, (0, 9.0), (0.3, 4.3), equal=False)
    _net_sketch(ax, [1.4, 0, 6.2], [3.4, 2.5, 1.6], [], 2.5, show_hidden=False)
    _label(ax, 6.2, 2.5, f'{P_FLAT:.2f}', size=9, family=MONO)
    _label(ax, 1.4, 4.0, 'three readings', size=10.5, color=JOINT, weight='bold')
    _label(ax, 6.2, 3.3, 'one answer', size=10.5, color=SLIDE, weight='bold')
    _label(ax, 3.8, 3.75, 'three weights and one bias', size=10, color=MUTED)
    _label(ax, 4.6, 0.75, 'nothing in the middle at all', size=10.5, color=MUTED)
    _save(fig, SML, 'no-middle-at-all.svg')


def one_layer_in_the_middle() -> None:
    """The same three readings, with one layer of four neurons put in between."""
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    _axes(ax, (0, 9.0), (0.3, 4.9), equal=False)
    _net_sketch(ax, [1.4, 3.8, 6.4], [3.4, 2.5, 1.6], [4.1, 3.2, 2.3, 1.4], 2.5,
                show_hidden=True)
    _label(ax, 6.4, 2.5, f'{P_HOLD:.2f}', size=9, family=MONO)
    _label(ax, 1.4, 4.6, 'the same readings', size=10.5, color=JOINT, weight='bold')
    _label(ax, 3.8, 4.7, 'four neurons', size=10.5, color=LINK, weight='bold')
    _label(ax, 6.4, 3.3, 'one answer', size=10.5, color=SLIDE, weight='bold')
    _label(ax, 3.8, 0.75, 'the readings are rewritten once before the answer is worked out',
           size=10, color=MUTED)
    _save(fig, SML, 'one-layer-in-the-middle.svg')


def the_same_reading_through_both() -> None:
    """The same moment put through both networks, number by number."""
    rows = [['', 'no middle', 'one layer of four'],
            ['what the answer is worked out from', '3 readings', '4 features'],
            ['the numbers it is worked out from',
             '0.42 0.55 0.30',
             ' '.join(f'{v:.2f}' for v in OUT1)],
            ['the sum before the rule', f'{SUM_FLAT:+.3f}', f'{SUM2:+.3f}'],
            ['the answer', f'{P_FLAT:.3f}', f'{P_HOLD:.3f}'],
            ['numbers it owns', '4', '16 + 5 = 21']]
    fig, ax = plt.subplots(figsize=(9.0, 3.0))
    _axes(ax, (0, 10.4), (0.1, 5.5), equal=False)
    _table(ax, 0.15, 5.4, [4.3, 2.6, 3.3], rows, row_h=0.84, mono_from=1, size=10)
    _save(fig, SML, 'the-same-reading-through-both.svg')


# ==========================================================================
# 04_a-network-on-a-robot.md
# ==========================================================================

def the_whole_network() -> None:
    """The three readings, the four features and the one answer, with every number."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    _axes(ax, (0, 11.4), (0.5, 6.4), equal=False)
    ys_in = [4.2, 3.2, 2.2]
    ys_h = [4.9, 3.7, 2.5, 1.3]
    for y in ys_in:
        for yh in ys_h:
            ax.plot([1.9, 4.3], [y, yh], color=LINK_PALE, lw=0.8, zorder=1)
    for yh in ys_h:
        ax.plot([5.9, 8.5], [yh, 3.1], color=LINK_PALE, lw=0.8, zorder=1)
    for i, y in enumerate(ys_in):
        _box(ax, 0.2, y - 0.3, 1.6, 0.6, face='#fdf1dc', edge=JOINT)
        _label(ax, 1.0, y, f'{SHORT[i]} {X[i]:.2f}', size=9.5)
    for i, yh in enumerate(ys_h):
        _box(ax, 4.35, yh - 0.36, 1.5, 0.72)
        _label(ax, 5.1, yh + 0.14, f'sum {SUMS1[i]:+.3f}', size=9, family=MONO)
        _label(ax, 5.1, yh - 0.16, f'out {OUT1[i]:.3f}', size=9, family=MONO,
               color=MUTED if OUT1[i] == 0 else INK)
        _label(ax, 5.1, yh + 0.55, NEU_JOB[i], size=9, color=MUTED)
    _box(ax, 8.55, 2.74, 1.9, 0.72, face='#dff0df', edge=SLIDE)
    _label(ax, 9.5, 3.26, f'sum {SUM2:+.3f}', size=9, family=MONO)
    _label(ax, 9.5, 2.96, f'answer {P_HOLD:.3f}', size=9, family=MONO, weight='bold')
    _label(ax, 1.0, 5.1, 'what the arm reports', size=10.5, color=JOINT, weight='bold')
    _label(ax, 5.1, 6.1, 'what the layer makes of it', size=10.5, color=LINK, weight='bold')
    _label(ax, 9.5, 4.1, 'how likely the grasp holds', size=10.5, color=SLIDE, weight='bold')
    _save(fig, ROB, 'the-whole-network.svg')


def four_features_into_one_answer() -> None:
    """The output neuron's row of arithmetic, feature by feature."""
    rows = [['feature', 'what it answers', 'value', 'weight', 'product'],
            *[[f'{i + 1}', NEU_JOB[i], f'{OUT1[i]:.3f}', f'{W2[i]:+.2f}', f'{PROD2[i]:+.3f}']
              for i in range(4)],
            ['bias', 'added whatever the readings are', '', f'{B2:+.2f}', f'{B2:+.3f}'],
            ['sum', '', '', '', f'{SUM2:+.3f}']]
    fig, ax = plt.subplots(figsize=(9.4, 3.2))
    _axes(ax, (0, 10.8), (0.1, 6.4), equal=False)
    _table(ax, 0.15, 6.3, [1.1, 4.6, 1.3, 1.3, 1.5], rows, row_h=0.8, mono_from=2, size=10)
    _save(fig, ROB, 'four-features-into-one-answer.svg')


def features_at_two_moments() -> None:
    """What the four neurons give at 0.42 m and at 0.85 m."""
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    idx = np.arange(4)
    ax.bar(idx - 0.18, OUT1, width=0.36, color=LINK, label='at 0.42 m')
    ax.bar(idx + 0.18, OUT1_FAR, width=0.36, color=GRIP, label='at 0.85 m')
    ax.set_xticks(idx, [f'feature {i + 1}' for i in idx], fontsize=9.5)
    ax.set_ylabel('what the neuron gives', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    _plain(ax)
    fig.tight_layout()
    _save(fig, ROB, 'features-at-two-moments.svg')


def the_answer_at_two_moments() -> None:
    """The one number the whole network gives, at the same two moments."""
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    ax.bar([0, 1], [P_HOLD, P_HOLD_FAR], width=0.5, color=[LINK, GRIP])
    ax.set_xticks([0, 1], ['at 0.42 m', 'at 0.85 m'], fontsize=9.5)
    ax.set_ylim(0, 1)
    ax.set_ylabel('how likely the grasp holds', fontsize=9.5)
    for i, v in enumerate([P_HOLD, P_HOLD_FAR]):
        ax.text(i, v + 0.03, f'{v:.3f}', ha='center', fontsize=10, family=MONO)
    _plain(ax)
    fig.tight_layout()
    _save(fig, ROB, 'the-answer-at-two-moments.svg')


# ==========================================================================
# 05_one-neuron-of-that-network.md
# ==========================================================================

PICK: int = 1       # the second neuron of the layer: 'far and closed'


def the_second_neuron() -> None:
    """One neuron of the four, worked out line by line."""
    prod = X * W1[PICK]
    run = np.cumsum(prod)
    rows = [['reading', 'value', 'weight', 'product', 'running total'],
            *[[SHORT[i], f'{X[i]:.2f}', f'{W1[PICK, i]:+.2f}', f'{prod[i]:+.3f}',
               f'{run[i]:+.3f}'] for i in range(3)],
            ['bias', '', f'{B1[PICK]:+.2f}', f'{B1[PICK]:+.3f}', f'{SUMS1[PICK]:+.3f}']]
    fig, ax = plt.subplots(figsize=(8.8, 2.7))
    _axes(ax, (0, 10.2), (0.1, 4.6), equal=False)
    _table(ax, 0.2, 4.5, [2.1, 1.3, 1.4, 1.6, 2.0], rows, row_h=0.82, mono_from=1, size=10)
    _save(fig, ONEN, 'the-second-neuron.svg')


def two_neurons_two_questions() -> None:
    """The same three readings, two neurons, two different weights and two answers."""
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    _axes(ax, (0, 10.4), (0.2, 4.6), equal=False)
    for row, n in enumerate([0, PICK]):
        y = 3.3 - row * 1.8
        _label(ax, 0.15, y + 0.92, f'neuron {n + 1}: {NEU_JOB[n]}', size=10.5, ha='left',
               weight='bold', color=LINK if row == 0 else PURPLE)
        for i in range(3):
            x = 0.4 + i * 2.4
            w = W1[n, i]
            colour = SLIDE if w > 0 else (GRIP if w < 0 else MUTED)
            if w == 0:
                ax.plot([x, x], [y - 0.17, y + 0.17], color=MUTED, lw=1.4, zorder=3)
                _label(ax, x + 0.12, y, 'nothing', size=8.5, ha='left', color=MUTED)
            else:
                ax.barh(y, abs(w) * 0.9, left=x, height=0.34, color=colour, zorder=3)
            _label(ax, x, y + 0.4, f'{SHORT[i]} {w:+.2f}', size=9, ha='left', color=MUTED)
        _label(ax, 8.4, y, f'sum {SUMS1[n]:+.3f}', size=10, family=MONO, ha='left')
        _label(ax, 8.4, y - 0.38, f'out {OUT1[n]:.3f}', size=10, family=MONO, ha='left',
               color=MUTED if OUT1[n] == 0 else INK)
    _label(ax, 5.2, 0.45, 'green counts in favour, red counts against, '
                          'and the bar is how much', size=10, color=MUTED)
    _save(fig, ONEN, 'two-neurons-two-questions.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        one.PNG_DIR = pathlib.Path(sys.argv[2])
        one.PNG_DIR.mkdir(parents=True, exist_ok=True)
    report()
    a_number_on_its_own_says_nothing()
    the_shape_of_a_network()
    the_words_on_one_network()
    given_and_chosen()
    no_middle_at_all()
    one_layer_in_the_middle()
    the_same_reading_through_both()
    the_whole_network()
    four_features_into_one_answer()
    features_at_two_moments()
    the_answer_at_two_moments()
    the_second_neuron()
    two_neurons_two_questions()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
