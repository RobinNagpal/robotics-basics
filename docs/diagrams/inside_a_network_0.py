"""Generate the diagrams for the first pages of docs/05_neural-networks/02_inside-a-network/.

Each document's pictures go to a folder named after it, under
docs/images/inside-a-network/:

    01_networks-and-neurons.md     -> networks-and-neurons/
    02_the-grasp-example.md        -> the-grasp-example/
    04_the-smallest-network.md     -> the-smallest-network/
    05_a-network-on-a-robot.md     -> a-network-on-a-robot/
    06_one-neuron-of-that-network.md -> one-neuron-of-that-network/

Run with:  python3 ../docs/diagrams/inside_a_network_0.py
Add --png <folder> to also write PNG copies for checking by eye.

The worked example is the same one the rest of the chapter uses, so the three
readings, the four-neuron layer and its weights are imported from
inside_a_network_1.py rather than written out again here. What this file adds is
the drawings of the arm, the gripper and the cup at three moments, and the output
neuron that turns the layer's four features into one answer. That neuron's four
weights and its bias were chosen by hand, like every other weight in the chapter,
so that the three moments get the answers a person watching the arm would give.
Nothing here was trained. Every number drawn is printed when the script runs, so
the documents can quote the same values.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from inside_a_network_1 import (  # noqa: E402
    B1, BIAS, BRIGHT, DIST_MM, GRID, GRIP, INK, JOINT, LINK, LINK_PALE, MONO, MUTED,
    NEU_JOB, OPEN_MM, OUT1, PATCH, PATCH_MEAN, PURPLE, SHORT, SLIDE, SUM, SUMS1, TEAL,
    W, W1, X, Arr,
    _arrow, _axes, _box, _label, _plain, _table, relu,
)
from matplotlib.patches import Circle, Rectangle  # noqa: E402
import inside_a_network_1 as one  # noqa: E402


def sigmoid(z: Arr | float) -> Arr:
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


# --------------------------------------------------------------------------
# the three moments of the grasp
# --------------------------------------------------------------------------
# Seen from above. The fingers are 80 mm long and the cup is 45 mm across, so the
# cup sits between the fingertips when its near side is less than about 60 mm from
# the palm. The distance is the gap from the palm to the near side of the cup,
# divided by 100 mm; the opening is the gap between the fingers, divided by 100 mm;
# the brightness is the patch between the fingertips, worked out in
# inside_a_network_1.py. The dark patch of the third moment is set to 0.05.
FINGER_MM: float = 80.0
CUP_MM: float = 45.0
# name, picture, palm-to-cup distance (mm), opening (mm), cup off to the side (mm),
# patch brightness
MOMENTS: list[tuple[str, str, float, float, float, float]] = [
    ('ready to close', 'ready-to-close', DIST_MM, OPEN_MM, 0.0, BRIGHT),
    ('too far away', 'too-far-away', 85.0, OPEN_MM, 0.0, BRIGHT),
    ('aimed beside the cup', 'aimed-beside-the-cup', DIST_MM, OPEN_MM, 60.0, 0.05),
]


def _readings(m) -> Arr:
    return np.array([m[2] / 100.0, m[3] / 100.0, m[5]])


# --------------------------------------------------------------------------
# the output neuron that finishes the network
# --------------------------------------------------------------------------
# It reads the four features of the layer and gives one number between 0 and 1,
# read as how likely this grasp is to hold. Its weights say which features count
# for the grasp and which count against it. Chosen by hand, not trained, so that
# the three moments come out the way a person watching the arm would judge them.
W2: Arr = np.array([5.00, -2.00, -8.00, -1.00])
B2: float = 1.00


def run(x: Arr) -> tuple[Arr, Arr, float, float]:
    """The whole network on one set of readings: sums, features, total, answer."""
    sums = W1 @ x + B1
    feats = relu(sums)
    total = float(feats @ W2 + B2)
    return sums, feats, total, float(sigmoid(total))


PROD2: Arr = OUT1 * W2
SUM2: float = float(PROD2.sum() + B2)
P_HOLD: float = float(sigmoid(SUM2))
RUNS: list[tuple[Arr, Arr, float, float]] = [run(_readings(m)) for m in MOMENTS]

# The two bigger networks of 04_the-smallest-network.md, counted but not run.
SHAPES: list[tuple[str, list[int]]] = [('one layer of four', [3, 4, 1]),
                                       ('one layer of eight', [3, 8, 1]),
                                       ('two layers of four', [3, 4, 4, 1])]


def owned(sizes: list[int]) -> list[tuple[int, int]]:
    """Weights and biases of each layer that does arithmetic."""
    return [(a * b, b) for a, b in zip(sizes, sizes[1:])]


IMAGES: pathlib.Path = one.IMAGES
NET: str = 'networks-and-neurons'
GRA: str = 'the-grasp-example'
SML: str = 'the-smallest-network'
ROB: str = 'a-network-on-a-robot'
ONEN: str = 'one-neuron-of-that-network'


def _save(fig, folder: str, name: str) -> None:
    one._save(fig, folder, name)


def report() -> None:
    print('--- the three moments -------------------------------------------')
    for m, (sums, feats, total, p) in zip(MOMENTS, RUNS):
        x = _readings(m)
        print(f'  {m[0]:22s} readings {x[0]:.2f} {x[1]:.2f} {x[2]:.2f}')
        print(f'      layer sums {" ".join(f"{v:+.3f}" for v in sums)}')
        print(f'      features   {" ".join(f"{v:.3f}" for v in feats)}')
        print(f'      products   {" ".join(f"{v:+.3f}" for v in feats * W2)} '
              f'bias {B2:+.2f} -> total {total:+.3f} -> sigmoid {p:.3f}')
    print('--- the layer at the first moment -------------------------------')
    for i in range(4):
        print(f'  neuron {i + 1} ({NEU_JOB[i]:22s}) weights {W1[i]} bias {B1[i]:+.2f} '
              f'sum {SUMS1[i]:+.3f} -> {OUT1[i]:.3f}')
    print('--- what each network owns --------------------------------------')
    for name, sizes in SHAPES:
        parts = owned(sizes)
        print(f'  {name:20s} ' + ' + '.join(f'({w} + {b})' for w, b in parts) +
              f' = {sum(w + b for w, b in parts)}')


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
# 02_the-grasp-example.md
# ==========================================================================

def _scene(ax, m, notes: bool) -> None:
    """The gripper and the cup seen from above, at one moment, sizes in millimetres."""
    _name, _pic, dist, opening, dy, bright = m
    half = opening / 2.0
    ax.add_patch(Rectangle((-150, -95), 300, 190, facecolor='#5b5148', zorder=0))
    ax.add_patch(Rectangle((-140, -14), 120, 28, facecolor='#b9b9b9', edgecolor=INK,
                           lw=1.0, zorder=2))
    ax.add_patch(Rectangle((-20, -50), 20, 100, facecolor='#d0d0d0', edgecolor=INK,
                           lw=1.0, zorder=3))
    ax.add_patch(Rectangle((-7, -7), 7, 14, facecolor=INK, zorder=4))
    for y0 in (half, -half - 8):
        ax.add_patch(Rectangle((0, y0), FINGER_MM, 8, facecolor='#d0d0d0', edgecolor=INK,
                               lw=1.0, zorder=3))
    # the camera's line of sight: the centre of its picture is what lies straight ahead
    ax.plot([0, 148], [0, 0], color=JOINT, lw=1.4, ls='--', zorder=4)
    cx = dist + CUP_MM / 2.0
    ax.add_patch(Circle((cx, dy), CUP_MM / 2.0, facecolor='#f4f1ea', edgecolor=INK,
                        lw=1.2, zorder=5))
    ax.add_patch(Circle((cx, dy), CUP_MM / 2.0 - 4, facecolor='#e2ddd2', edgecolor='none',
                        zorder=5))
    # the distance, from the palm to the near side of the cup, drawn below the fingers
    yd = -half - 24
    ax.annotate('', xy=(dist, yd), xytext=(0, yd),
                arrowprops=dict(arrowstyle='<->', color='white', lw=1.4), zorder=7)
    ax.plot([dist, dist], [yd - 4, dy], color='white', lw=0.8, ls=':', zorder=2)
    _label(ax, dist / 2.0, yd - 9, f'distance {dist:.0f} mm', size=9.5, color='white')
    # the opening, between the inside faces of the fingers
    ax.annotate('', xy=(8, half), xytext=(8, -half),
                arrowprops=dict(arrowstyle='<->', color='white', lw=1.4), zorder=7)
    ax.text(16, 0, f'{opening:.0f} mm', rotation=90, ha='center', va='center',
            fontsize=9.5, color='white', zorder=7)
    _label(ax, 146, -84, f'centre of the picture: brightness {bright:.2f}', size=9.5,
           color=JOINT, ha='right')
    if notes:
        ax.annotate('camera in the palm', xy=(-4, 6), xytext=(-80, 40), fontsize=9.5,
                    color='white', ha='center',
                    arrowprops=dict(arrowstyle='-', color='white', lw=0.9), zorder=7)
        _label(ax, -80, -26, 'arm', size=9.5, color='white')
        _label(ax, -80, -46, 'opening', size=9.5, color='white')
        ax.annotate('', xy=(10, -20), xytext=(-55, -46),
                    arrowprops=dict(arrowstyle='-', color='white', lw=0.9), zorder=7)
        ax.annotate('cup, 45 mm across', xy=(cx + 8, dy + CUP_MM / 2.0 - 1), xytext=(cx + 30, 70),
                    fontsize=9.5, color='white', ha='center',
                    arrowprops=dict(arrowstyle='-', color='white', lw=0.9), zorder=7)
        _label(ax, 40, half + 18, 'fingers 80 mm long', size=9.5, color='white')


def the_arm_the_gripper_and_the_cup() -> None:
    """The first moment, with every part named."""
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    _axes(ax, (-150, 150), (-95, 95))
    _scene(ax, MOMENTS[0], notes=True)
    _save(fig, GRA, 'the-arm-the-gripper-and-the-cup.svg')


def one_moment(i: int) -> None:
    """One of the three moments, with only its three readings marked."""
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    _axes(ax, (-150, 150), (-95, 95))
    _scene(ax, MOMENTS[i], notes=False)
    _save(fig, GRA, f'{MOMENTS[i][1]}.svg')


def scaling_the_readings() -> None:
    """Where the three input numbers come from, including the 4 by 4 patch of pixels."""
    print('--- the three readings ------------------------------------------')
    print(f'distance {DIST_MM:.0f} mm / 100 = {DIST_MM / 100:.2f}; opening {OPEN_MM:.0f} mm '
          f'/ 100 = {OPEN_MM / 100:.2f}; patch sum {PATCH.sum()} over 16 pixels = '
          f'{PATCH_MEAN:.1f}, /255 = {PATCH_MEAN / 255:.4f} -> {BRIGHT:.3f}')
    fig, ax = plt.subplots(figsize=(13.5, 7.4), facecolor='white')
    _axes(ax, (0, 27), (0.9, 15.1))
    _label(ax, 13.5, 14.5, 'The three readings, and how each one becomes a number from 0 to 1',
           size=13, weight='bold')
    rows = [(12.6, 'wrist camera', f'{DIST_MM:.0f} mm',
             'only the last 100 mm matter,\nso divide by 100', f'{X[0]:.2f}', LINK),
            (9.6, 'gripper', f'{OPEN_MM:.0f} mm', 'the jaws open to 100 mm,\nso divide by 100',
             f'{X[1]:.2f}', JOINT)]
    for y, src, raw, how, val, col in rows:
        _label(ax, 0.1, y, src, size=10.5, ha='left', weight='bold', color=MUTED)
        _box(ax, 5.0, y - 0.6, 3.0, 1.2, face='white', edge=col)
        _label(ax, 6.5, y, raw, size=11.5, family=MONO)
        _arrow(ax, (8.2, y), (10.0, y), color=MUTED, lw=1.4)
        _label(ax, 10.3, y, how, size=9.8, ha='left')
        _arrow(ax, (18.4, y), (20.2, y), color=MUTED, lw=1.4)
        _box(ax, 20.4, y - 0.6, 2.6, 1.2, face=LINK_PALE, edge=LINK)
        _label(ax, 21.7, y, val, size=11.5, family=MONO)
    _label(ax, 0.1, 6.4, 'camera patch', size=10.5, ha='left', weight='bold', color=MUTED)
    x0, y0 = 4.0, 2.0
    for r in range(4):
        for c in range(4):
            v = int(PATCH[r, c])
            shade = v / 255.0
            ax.add_patch(Rectangle((x0 + c, y0 + (3 - r)), 1, 1,
                                   facecolor=(shade, shade, shade), edgecolor=GRID, lw=0.8,
                                   zorder=3))
            _label(ax, x0 + c + 0.5, y0 + (3 - r) + 0.5, str(v), size=10, color='white',
                   family=MONO)
    _label(ax, x0 + 2, y0 - 0.7, '16 pixels, 0 is black and 255 is white', size=9.5, color=MUTED)
    _arrow(ax, (x0 + 4.2, y0 + 2), (10.0, y0 + 2), color=MUTED, lw=1.4)
    _label(ax, 10.3, y0 + 2.3, f'add the 16 values: {PATCH.sum()}', size=9.8, ha='left')
    _label(ax, 10.3, y0 + 1.3, f'divide by 16: {PATCH_MEAN:.1f}, then by 255',
           size=9.8, ha='left')
    _arrow(ax, (18.4, y0 + 2), (20.2, y0 + 2), color=MUTED, lw=1.4)
    _box(ax, 20.4, y0 + 1.4, 2.6, 1.2, face=LINK_PALE, edge=LINK)
    _label(ax, 21.7, y0 + 2, f'{BRIGHT:.2f}', size=11.5, family=MONO)
    _label(ax, 21.7, 13.8, 'the three inputs', size=10.5, weight='bold', color=LINK)
    _save(fig, GRA, 'scaling-the-readings.svg')


# ==========================================================================
# 04_the-smallest-network.md
# ==========================================================================

def _sketch(ax, sizes: list[int], x0: float, gap: float, y_mid: float, step: float,
            first: list[str] | None = None, last: str | None = None) -> None:
    """Circles for each layer, every circle joined to every circle in the next layer."""
    xs = [x0 + i * gap for i in range(len(sizes))]
    ys = [[y_mid + (n - 1) / 2.0 * step - k * step for k in range(n)] for n in sizes]
    r = min(0.26, step * 0.42)
    for i in range(len(sizes) - 1):
        for ya in ys[i]:
            for yb in ys[i + 1]:
                ax.plot([xs[i] + r, xs[i + 1] - r], [ya, yb], color=LINK_PALE, lw=0.8,
                        zorder=1)
    for i, col in enumerate(ys):
        face, edge = (('#fdf1dc', JOINT) if i == 0 else
                      ('#dff0df', SLIDE) if i == len(sizes) - 1 else (LINK_PALE, LINK))
        for k, y in enumerate(col):
            ax.add_patch(Circle((xs[i], y), r, facecolor=face, edgecolor=edge, lw=1.4,
                                zorder=3))
            if i == 0 and first:
                _label(ax, xs[i], y, first[k], size=8.5, family=MONO)
    if last:
        _label(ax, xs[-1], ys[-1][0], last, size=8.5, family=MONO)


def one_layer_of_four() -> None:
    """The three readings, one layer of four neurons, and one answer."""
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    _axes(ax, (0, 9.0), (0.6, 4.9), equal=False)
    _sketch(ax, [3, 4, 1], 1.4, 2.5, 2.75, 0.9, [f'{v:.2f}' for v in X], f'{P_HOLD:.2f}')
    _label(ax, 1.4, 4.55, 'three readings', size=10.5, color=JOINT, weight='bold')
    _label(ax, 3.9, 4.55, 'four neurons', size=10.5, color=LINK, weight='bold')
    _label(ax, 6.4, 3.4, 'one answer', size=10.5, color=SLIDE, weight='bold')
    _save(fig, SML, 'one-layer-of-four.svg')


def the_layer_worked_out() -> None:
    """Each of the four neurons: its weights, its bias, its sum and what the rule leaves."""
    rows = [['neuron', 'distance', 'opening', 'brightness', 'bias', 'sum', 'after rule'],
            *[[f'{i + 1}', f'{W1[i, 0]:+.2f}', f'{W1[i, 1]:+.2f}', f'{W1[i, 2]:+.2f}',
               f'{B1[i]:+.2f}', f'{SUMS1[i]:+.3f}', f'{OUT1[i]:.3f}'] for i in range(4)]]
    fig, ax = plt.subplots(figsize=(9.4, 2.5))
    _axes(ax, (0, 10.8), (0.1, 4.2), equal=False)
    _table(ax, 0.15, 4.1, [1.2, 1.55, 1.55, 1.65, 1.3, 1.5, 1.6], rows, row_h=0.8,
           mono_from=1, size=10)
    _save(fig, SML, 'the-layer-worked-out.svg')


def the_output_neuron_worked_out() -> None:
    """The output neuron's row of arithmetic, feature by feature."""
    rows = [['feature', 'value', 'weight', 'product'],
            *[[f'{i + 1}', f'{OUT1[i]:.3f}', f'{W2[i]:+.2f}', f'{PROD2[i]:+.3f}']
              for i in range(4)],
            ['bias', '', f'{B2:+.2f}', f'{B2:+.3f}'],
            ['sum', '', '', f'{SUM2:+.3f}'],
            ['sigmoid', '', '', f'{P_HOLD:.3f}']]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    _axes(ax, (0, 7.0), (0.1, 7.3), equal=False)
    _table(ax, 0.15, 7.2, [1.6, 1.6, 1.6, 1.8], rows, row_h=0.8, mono_from=1, size=10)
    _save(fig, SML, 'the-output-neuron-worked-out.svg')


def one_layer_of_eight() -> None:
    """The same readings and answer with a layer twice as wide."""
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    _axes(ax, (0, 9.0), (0.1, 5.6), equal=False)
    _sketch(ax, [3, 8, 1], 1.4, 2.5, 2.7, 0.62)
    _label(ax, 1.4, 5.35, 'three readings', size=10.5, color=JOINT, weight='bold')
    _label(ax, 3.9, 5.35, 'eight neurons', size=10.5, color=LINK, weight='bold')
    _label(ax, 6.4, 3.4, 'one answer', size=10.5, color=SLIDE, weight='bold')
    _save(fig, SML, 'one-layer-of-eight.svg')


def two_layers_of_four() -> None:
    """The same readings and answer with a second layer of four after the first."""
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    _axes(ax, (0, 10.6), (0.6, 4.9), equal=False)
    _sketch(ax, [3, 4, 4, 1], 1.4, 2.5, 2.75, 0.9)
    _label(ax, 1.4, 4.55, 'three readings', size=10.5, color=JOINT, weight='bold')
    _label(ax, 3.9, 4.55, 'four neurons', size=10.5, color=LINK, weight='bold')
    _label(ax, 6.4, 4.55, 'four more', size=10.5, color=LINK, weight='bold')
    _label(ax, 8.9, 3.4, 'one answer', size=10.5, color=SLIDE, weight='bold')
    _save(fig, SML, 'two-layers-of-four.svg')


def what_each_network_owns() -> None:
    """Weights and biases, layer by layer, for the three networks."""
    rows = [['network', 'first layer', 'second layer', 'output neuron', 'in all']]
    for name, sizes in SHAPES:
        parts = [f'{w} + {b}' for w, b in owned(sizes)]
        mid = parts[1] if len(parts) == 3 else ''
        rows.append([name, parts[0], mid, parts[-1], f'{sum(w + b for w, b in owned(sizes))}'])
    fig, ax = plt.subplots(figsize=(9.2, 2.2))
    _axes(ax, (0, 10.6), (0.1, 3.5), equal=False)
    _table(ax, 0.15, 3.4, [3.0, 1.9, 1.9, 2.0, 1.4], rows, row_h=0.8, mono_from=1, size=10)
    _save(fig, SML, 'what-each-network-owns.svg')


# ==========================================================================
# 05_a-network-on-a-robot.md
# ==========================================================================

def the_network_at(i: int) -> None:
    """The three readings, the four features and the one answer at one moment."""
    m = MOMENTS[i]
    x = _readings(m)
    sums, feats, total, p = RUNS[i]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    _axes(ax, (0, 11.4), (0.5, 6.4), equal=False)
    ys_in = [4.2, 3.2, 2.2]
    ys_h = [4.9, 3.7, 2.5, 1.3]
    for y in ys_in:
        for yh in ys_h:
            ax.plot([1.9, 4.3], [y, yh], color=LINK_PALE, lw=0.8, zorder=1)
    for yh in ys_h:
        ax.plot([5.9, 8.5], [yh, 3.1], color=LINK_PALE, lw=0.8, zorder=1)
    for k, y in enumerate(ys_in):
        _box(ax, 0.05, y - 0.3, 1.8, 0.6, face='#fdf1dc', edge=JOINT)
        _label(ax, 0.95, y, f'{SHORT[k]} {x[k]:.2f}', size=9.5)
    for k, yh in enumerate(ys_h):
        _box(ax, 4.35, yh - 0.36, 1.5, 0.72)
        _label(ax, 5.1, yh + 0.14, f'sum {sums[k]:+.3f}', size=9, family=MONO)
        _label(ax, 5.1, yh - 0.16, f'out {feats[k]:.3f}', size=9, family=MONO,
               color=MUTED if feats[k] == 0 else INK)
        _label(ax, 5.1, yh + 0.55, NEU_JOB[k], size=9, color=MUTED)
    _box(ax, 8.55, 2.74, 1.9, 0.72, face='#dff0df', edge=SLIDE)
    _label(ax, 9.5, 3.26, f'sum {total:+.3f}', size=9, family=MONO)
    _label(ax, 9.5, 2.96, f'answer {p:.3f}', size=9, family=MONO, weight='bold')
    _label(ax, 1.0, 5.1, 'what the arm reports', size=10.5, color=JOINT, weight='bold')
    _label(ax, 5.1, 6.1, 'what the layer makes of it', size=10.5, color=LINK, weight='bold')
    _label(ax, 9.5, 4.1, 'how likely the grasp holds', size=10.5, color=SLIDE, weight='bold')
    _save(fig, ROB, f'network-{m[1]}.svg')


def the_answer_at_three_moments() -> None:
    """The one number the whole network gives, at the three moments."""
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ps = [r[3] for r in RUNS]
    ax.bar(range(3), ps, width=0.5, color=[SLIDE, GRIP, GRIP])
    ax.set_xticks(range(3), [m[0] for m in MOMENTS], fontsize=9.5)
    ax.set_ylim(0, 1)
    ax.set_ylabel('how likely the grasp holds', fontsize=9.5)
    for k, v in enumerate(ps):
        ax.text(k, v + 0.03, f'{v:.3f}', ha='center', fontsize=10, family=MONO)
    _plain(ax)
    fig.tight_layout()
    _save(fig, ROB, 'the-answer-at-three-moments.svg')


# ==========================================================================
# 06_one-neuron-of-that-network.md
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
    the_arm_the_gripper_and_the_cup()
    for i in range(len(MOMENTS)):
        one_moment(i)
    scaling_the_readings()
    one_layer_of_four()
    the_layer_worked_out()
    the_output_neuron_worked_out()
    one_layer_of_eight()
    two_layers_of_four()
    what_each_network_owns()
    for i in range(len(MOMENTS)):
        the_network_at(i)
    the_answer_at_three_moments()
    the_second_neuron()
    two_neurons_two_questions()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
