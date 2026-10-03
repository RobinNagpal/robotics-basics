"""Generate the diagrams for the first two pages of docs/06_neural-networks/02_inside-a-network/.

Each document's pictures go to a folder named after it, under
docs/images/inside-a-network/:

    01_one-neuron.md        -> one-neuron/
    02_layers-and-depth.md  -> layers-and-depth/

Run with:  python3 inside_a_network_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file and printed, so the
two documents quote the same values. The worked neuron reads three made-up
sensor values for one moment of one grasp: a distance of 0.42 m from a depth
camera, a gripper opening of 55 mm, and the average brightness of a 4 by 4
patch of pixels, which is set out in the file. The weights and biases of that
neuron, and of the four-neuron layer on the second page, were chosen by hand so
that the arithmetic is small enough to follow; they were not trained. Where a
picture needs many weights at once (the counts of straight pieces, the dead
units, the thirty-layer stacks) the weights are drawn from
numpy.random.default_rng with a fixed seed, so the numbers are simulated but
repeatable. The timing picture is one measurement of NumPy on the computer that
drew it, so the shape of the curve is the point rather than the exact seconds.
"""

import math
import pathlib
import sys
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (  # noqa: E402
    FancyArrowPatch, FancyBboxPatch, Rectangle,
)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'inside-a-network'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
PURPLE: str = '#6a4fb3'
TEAL: str = '#0f8b8d'
INK: str = '#222222'
MUTED: str = '#777777'
MONO: str = 'DejaVu Sans Mono'

ONE: str = 'one-neuron'
LAY: str = 'layers-and-depth'

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float],
          equal: bool = True) -> None:
    ax.set_facecolor('white')
    if equal:
        ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)
    ax.grid(True, color=GRID, lw=0.7, alpha=0.7)
    ax.set_axisbelow(True)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', family: str | None = None,
           va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            family=family, zorder=7)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.8, rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=15, color=color,
                                 lw=lw, connectionstyle=f'arc3,rad={rad}', zorder=6))


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = LINK_PALE,
         edge: str = LINK, lw: float = 1.4) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.15',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=3))


def _table(ax: Axes, x0: float, y0: float, widths: list[float], rows: list[list[str]],
           row_h: float = 0.9, head: bool = True, face: str = 'white',
           head_face: str = LINK_PALE, mono_from: int = 1, size: float = 10.5) -> float:
    """Draw a table of text. Returns the y of the bottom edge."""
    n = len(rows)
    for r, row in enumerate(rows):
        y = y0 - r * row_h
        x = x0
        is_head = head and r == 0
        for c, cell in enumerate(row):
            ax.add_patch(Rectangle((x, y - row_h), widths[c], row_h,
                                   facecolor=head_face if is_head else face,
                                   edgecolor=GRID, lw=0.9, zorder=3))
            fam = None if (is_head or c < mono_from) else MONO
            _label(ax, x + widths[c] / 2.0, y - row_h / 2.0, cell, size=size,
                   weight='bold' if is_head else 'normal', family=fam)
            x += widths[c]
    return y0 - n * row_h


# --------------------------------------------------------------------------
# activation functions
# --------------------------------------------------------------------------

_ERF = np.vectorize(math.erf)


def relu(z: Arr | float) -> Arr:
    return np.maximum(0.0, np.asarray(z, dtype=float))


def gelu(z: Arr | float) -> Arr:
    za = np.asarray(z, dtype=float)
    return 0.5 * za * (1.0 + _ERF(za / math.sqrt(2.0)))


def silu(z: Arr | float) -> Arr:
    za = np.asarray(z, dtype=float)
    return za / (1.0 + np.exp(-za))


ACTS: dict[str, object] = {'ReLU': relu, 'GELU': gelu, 'SiLU': silu}
ACT_COLOUR: dict[str, str] = {'ReLU': LINK, 'GELU': GRIP, 'SiLU': SLIDE}


# --------------------------------------------------------------------------
# the one neuron that both pages are built on
# --------------------------------------------------------------------------

PATCH: NDArray[np.int64] = np.array([[71, 80, 69, 88],
                                     [64, 93, 77, 70],
                                     [83, 61, 90, 74],
                                     [79, 72, 86, 67]], dtype=np.int64)

DIST_M: float = 0.42        # metres, straight from the depth camera
OPEN_MM: float = 55.0       # millimetres, the gripper's own reading
PATCH_MEAN: float = float(PATCH.mean())
BRIGHT: float = round(PATCH_MEAN / 255.0, 3)

X: Arr = np.array([DIST_M, OPEN_MM / 100.0, BRIGHT])
W: Arr = np.array([-2.0, 1.5, 0.8])
BIAS: float = 0.5

SHORT: list[str] = ['distance', 'opening', 'brightness']
LONG: list[str] = ['distance to the object (m)',
                   'gripper opening / 100',
                   'patch brightness / 255']

PROD: Arr = X * W
SUM: float = float(PROD.sum() + BIAS)
OUT: float = float(relu(SUM))
OTHER_TWO: float = float(PROD[1] + PROD[2])          # the part that does not move with distance
ZERO_D: float = (OTHER_TWO + BIAS) / 2.0             # distance where the sum crosses 0


def neuron_sum(d: Arr | float, wd: float = W[0], b: float = BIAS) -> Arr:
    """The neuron's weighted sum as the distance changes, with the other two readings fixed."""
    return np.asarray(d, dtype=float) * wd + OTHER_TWO + b


def report_core() -> None:
    print('--- the worked neuron -------------------------------------------')
    print(f'patch mean {PATCH_MEAN:.1f} of 255 -> brightness input {BRIGHT:.3f}')
    print(f'inputs      {X}')
    print(f'weights     {W}   bias {BIAS:+.2f}')
    for nm, a, w, p in zip(SHORT, X, W, PROD):
        print(f'  {nm:11s} {a:5.2f} x {w:+.2f} = {p:+.3f}')
    print(f'sum of the three products {PROD.sum():+.3f}; plus bias -> {SUM:.3f}')
    print(f'ReLU output {OUT:.3f}; GELU {float(gelu(SUM)):.4f}; SiLU {float(silu(SUM)):.4f}')
    print(f'the two fixed products add to {OTHER_TWO:.3f}, '
          f'so the sum is 0 at a distance of {ZERO_D:.4f} m')


# ==========================================================================
# 01_one-neuron.md  --  section 1: what one neuron holds
# ==========================================================================

def neuron_parts() -> None:
    """The whole neuron: three named readings, three weights, a bias, a rule, one output."""
    fig, ax = plt.subplots(figsize=(15.0, 5.8), facecolor='white')
    _axes(ax, (0, 32), (0, 12.4))
    _label(ax, 16, 11.8, 'One neuron: multiply, add, add the bias, then apply the rule',
           size=13, weight='bold')
    ys = [9.0, 6.0, 3.0]
    names = ['distance to object (m)', 'gripper opening /100', 'patch brightness /255']
    cx, bx, sx = 6.9, 9.4, 19.2
    sy = 6.0
    _label(ax, 2.0, 10.1, 'reading', size=10.5, weight='bold', color=MUTED)
    _label(ax, 10.5, 10.1, 'weight', size=10.5, weight='bold', color=MUTED)
    _label(ax, 14.6, 10.1, 'product', size=10.5, weight='bold', color=MUTED)
    for y, nm, a, w, p in zip(ys, names, X, W, PROD):
        _label(ax, 0.1, y + 0.95, nm, size=9.5, ha='left', color=MUTED)
        ax.add_patch(plt.Circle((cx, y), 0.8, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                                zorder=4))
        _label(ax, cx, y, f'{a:.2f}', size=11.5, family=MONO)
        ax.plot([cx + 0.8, bx], [y, y], color=MUTED, lw=1.3, zorder=2)
        _box(ax, bx, y - 0.5, 2.2, 1.0, face='white', edge=JOINT)
        _label(ax, bx + 1.1, y, f'{w:+.2f}', size=11.5, family=MONO)
        _label(ax, bx + 2.5, y, f'= {p:+.3f}', size=11, family=MONO, ha='left')
        ax.plot([15.9, sx - 1.55], [y, sy + (y - sy) * 0.22], color=MUTED, lw=1.3, zorder=2)
    ax.add_patch(plt.Circle((sx, sy), 1.55, facecolor=JOINT, edgecolor=INK, lw=1.2, zorder=4))
    _label(ax, sx, sy + 0.45, 'add up', size=10.5, weight='bold')
    _label(ax, sx, sy - 0.35, f'{SUM:.3f}', size=12, family=MONO)
    _box(ax, sx - 1.3, 0.6, 2.6, 1.1, face='white', edge=SLIDE)
    _label(ax, sx, 1.15, f'{BIAS:+.2f}', size=11.5, family=MONO)
    _label(ax, sx, 2.05, 'bias', size=10.5, weight='bold', color=SLIDE)
    _arrow(ax, (sx, 1.75), (sx, sy - 1.6), color=SLIDE, lw=1.6)
    _arrow(ax, (sx + 1.6, sy), (22.3, sy))
    _box(ax, 22.5, 4.4, 5.3, 3.2, face='white', edge=PURPLE)
    _label(ax, 25.15, 7.0, 'the rule', size=11, weight='bold', color=PURPLE)
    _label(ax, 25.15, 5.8, 'below 0: give 0\notherwise: keep it', size=9.8)
    _label(ax, 25.15, 4.0, '(the activation function)', size=9.3, color=MUTED)
    _arrow(ax, (27.9, sy), (29.3, sy))
    ax.add_patch(plt.Circle((30.4, sy), 0.95, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                            zorder=4))
    _label(ax, 30.4, sy, f'{OUT:.3f}', size=11.5, family=MONO)
    _label(ax, 30.4, 4.5, 'output', size=10.5, weight='bold')
    _label(ax, 16, 0.1, f'{PROD[0]:+.3f} {PROD[1]:+.3f} {PROD[2]:+.3f} {BIAS:+.2f} '
           f'= {SUM:.3f}, which is above 0, so the output is {OUT:.3f}',
           size=10.5, color=MUTED, family=MONO)
    _save(fig, ONE, 'neuron-parts.svg')


def scaling_the_readings() -> None:
    """Where the three input numbers come from, including the 4 by 4 patch of pixels."""
    print('--- the three readings ------------------------------------------')
    print(f'distance {DIST_M} m goes in unchanged; opening {OPEN_MM:.0f} mm / 100 = '
          f'{OPEN_MM / 100:.2f}; patch sum {PATCH.sum()} over 16 pixels = {PATCH_MEAN:.1f}, '
          f'/255 = {PATCH_MEAN / 255:.4f} -> {BRIGHT:.3f}')
    fig, ax = plt.subplots(figsize=(13.5, 7.4), facecolor='white')
    _axes(ax, (0, 27), (0, 15))
    _label(ax, 13.5, 14.4, 'The three readings, and how each one becomes a number near 1',
           size=13, weight='bold')
    rows = [(12.6, 'depth camera', f'{DIST_M} m', 'already between 0 and 1,\nso it goes in as it is',
             f'{X[0]:.2f}', LINK),
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
    _label(ax, 24.6, 11.1, 'the three\ninputs', size=10.5, weight='bold', color=LINK)
    _save(fig, ONE, 'scaling-the-readings.svg')


def the_four_parameters() -> None:
    """The four numbers this neuron owns: three weights and one bias."""
    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _plain(ax)
    names = ['weight on\ndistance', 'weight on\nopening', 'weight on\nbrightness', 'bias']
    vals = [W[0], W[1], W[2], BIAS]
    cols = [GRIP, SLIDE, SLIDE, PURPLE]
    bars = ax.bar(range(4), vals, color=cols, edgecolor=INK, lw=0.8, width=0.56)
    for i, (b, v) in enumerate(zip(bars, vals)):
        off = 0.12 if v > 0 else -0.12
        ax.text(i, v + off, f'{v:+.2f}', ha='center',
                va='bottom' if v > 0 else 'top', fontsize=12, family=MONO)
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(-2.6, 2.0)
    ax.set_ylabel('value of the number', fontsize=10)
    ax.set_title('This one neuron owns four numbers: 3 weights + 1 bias = 4 parameters',
                 fontsize=12.5, weight='bold')
    ax.text(2.65, -2.2, 'a minus weight pushes the output down\nas that reading grows',
            fontsize=9.5, color=MUTED, ha='center')
    _save(fig, ONE, 'the-four-parameters.svg')


# ==========================================================================
# 01_one-neuron.md  --  section 2: the weighted sum
# ==========================================================================

def weighted_sum_lines() -> None:
    """The weighted sum as four lines of arithmetic with a running total."""
    run = np.cumsum(np.append(PROD, BIAS))
    print('--- the weighted sum, line by line ------------------------------')
    for nm, a, w, p, r in zip(SHORT + ['bias'], list(X) + [1.0], list(W) + [BIAS],
                              list(PROD) + [BIAS], run):
        print(f'  {nm:11s} {a:5.2f} x {w:+.2f} = {p:+.3f}   running total {r:+.3f}')
    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _axes(ax, (0, 24), (0, 11), equal=False)
    _label(ax, 12, 10.4, 'The weighted sum written out, one line at a time',
           size=13, weight='bold')
    rows = [['what it is', 'reading', 'weight', 'product', 'running total']]
    for nm, a, w, p, r in zip(SHORT, X, W, PROD, run):
        rows.append([nm, f'{a:.2f}', f'{w:+.2f}', f'{p:+.3f}', f'{r:+.3f}'])
    rows.append(['bias', '-', f'{BIAS:+.2f}', f'{BIAS:+.3f}', f'{run[-1]:+.3f}'])
    widths = [5.0, 3.0, 3.0, 3.4, 4.6]
    bottom = _table(ax, 2.0, 9.4, widths, rows, row_h = 1.15, size=11)
    _label(ax, 2.0 + sum(widths) / 2, bottom - 0.9,
           f'the weighted sum is {SUM:.3f}, and the rule keeps it, so the output is {OUT:.3f}',
           size=11, color=INK)
    _label(ax, 2.0 + sum(widths) / 2, bottom - 1.8,
           'the running total is what the neuron would have if it stopped at that line',
           size=9.5, color=MUTED)
    _save(fig, ONE, 'weighted-sum-lines.svg')


def contribution_bars() -> None:
    """Which reading pushed the answer up and which pushed it down."""
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    labels = ['distance\n0.42 x -2.00', 'opening\n0.55 x +1.50',
              'brightness\n0.30 x +0.80', 'bias\n+0.50']
    vals = list(PROD) + [BIAS]
    cols = [GRIP if v < 0 else SLIDE for v in vals[:3]] + [PURPLE]
    ax.bar(range(4), vals, color=cols, edgecolor=INK, lw=0.8, width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v + (0.05 if v > 0 else -0.05), f'{v:+.3f}', ha='center',
                va='bottom' if v > 0 else 'top', fontsize=11.5, family=MONO)
    ax.bar([4], [SUM], color=JOINT, edgecolor=INK, lw=1.0, width=0.55)
    ax.text(4, SUM + 0.05, f'{SUM:+.3f}', ha='center', va='bottom', fontsize=12,
            family=MONO, weight='bold')
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_xticks(range(5))
    ax.set_xticklabels(labels + ['the sum'], fontsize=9.8)
    ax.set_ylim(-1.1, 1.15)
    ax.set_ylabel('how much this line adds to the sum', fontsize=10)
    ax.set_title('Only the distance pulls this sum down; the other three push it up',
                 fontsize=12.5, weight='bold')
    _save(fig, ONE, 'contribution-bars.svg')


def sum_against_distance() -> None:
    """Hold two readings still, move the distance: the sum is a straight line."""
    d = np.linspace(0.0, 1.0, 201)
    s = neuron_sum(d)
    print('--- the sum as the distance changes -----------------------------')
    for dd in (0.0, 0.2, 0.42, 0.6, ZERO_D, 0.9):
        print(f'  distance {dd:6.4f} m -> sum {float(neuron_sum(dd)):+.4f} '
              f'-> output {float(relu(neuron_sum(dd))):.4f}')
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(d, s, color=LINK, lw=2.4, label='weighted sum (before the rule)')
    ax.plot(d, relu(s), color=GRIP, lw=2.4, ls='--', label='output (after the rule)')
    ax.axhline(0, color=INK, lw=1.1)
    ax.plot([DIST_M], [SUM], 'o', color=JOINT, ms=11, mec=INK, zorder=6)
    ax.annotate(f'our reading: {DIST_M} m -> {SUM:.3f}', xy=(DIST_M, SUM),
                xytext=(DIST_M + 0.07, SUM + 0.45), fontsize=10.5,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.3))
    ax.plot([ZERO_D], [0.0], 'o', color=PURPLE, ms=10, mec=INK, zorder=6)
    ax.annotate(f'the sum reaches 0 at {ZERO_D:.4f} m', xy=(ZERO_D, 0.0),
                xytext=(0.40, -0.52), fontsize=10.5,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.3))
    ax.set_xlabel('distance to the object (m), with the opening at 0.55 and the brightness at 0.30',
                  fontsize=10)
    ax.set_ylabel('the neuron', fontsize=10)
    ax.set_title('With only the distance moving, the sum falls by 2.00 for every extra metre',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    ax.set_ylim(-0.7, 1.9)
    _save(fig, ONE, 'sum-against-distance.svg')


def sum_over_two_readings() -> None:
    """The sum over distance and opening together: the dividing line is straight."""
    d = np.linspace(0.0, 1.0, 241)
    g = np.linspace(0.0, 1.0, 241)
    dd, gg = np.meshgrid(d, g)
    s = W[0] * dd + W[1] * gg + W[2] * BRIGHT + BIAS
    g_at = lambda dv: (-W[0] * dv - W[2] * BRIGHT - BIAS) / W[1]
    print('--- the sum over two readings -----------------------------------')
    print(f'the dividing line runs from opening {g_at(0.0):+.4f} at 0 m to '
          f'{g_at(1.0):+.4f} at 1 m; sum range {s.min():+.3f} to {s.max():+.3f}')
    fig, ax = plt.subplots(figsize=(8.6, 6.4), facecolor='white')
    im = ax.pcolormesh(dd, gg, s, cmap='RdYlBu', shading='auto', vmin=-2.0, vmax=2.0)
    cs = ax.contour(dd, gg, s, levels=[0.0], colors=[INK], linewidths=2.6)
    ax.clabel(cs, fmt={0.0: 'sum = 0'}, fontsize=10)
    ax.plot([DIST_M], [X[1]], 'o', color='white', ms=12, mec=INK, mew=1.6, zorder=6)
    ax.annotate(f'our reading -> {SUM:.3f}', xy=(DIST_M, X[1]), xytext=(0.52, 0.30),
                fontsize=10.5, arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.3))
    ax.set_xlabel('distance to the object (m)', fontsize=10)
    ax.set_ylabel('gripper opening / 100', fontsize=10)
    ax.set_title('One neuron splits the readings with a straight line, never a curve',
                 fontsize=12.5, weight='bold')
    ax.tick_params(labelsize=9.5)
    fig.colorbar(im, ax=ax, label='the weighted sum', shrink=0.88)
    _save(fig, ONE, 'sum-over-two-readings.svg')


# ==========================================================================
# 01_one-neuron.md  --  section 3: changing a weight, changing the bias
# ==========================================================================

def flipping_one_weight() -> None:
    """The same readings with the distance weight flipped from -2.00 to +2.00."""
    w2 = W.copy()
    w2[0] = -W[0]
    prod2 = X * w2
    sum2 = float(prod2.sum() + BIAS)
    print('--- flipping the distance weight --------------------------------')
    print(f'with {W[0]:+.2f} the sum is {SUM:+.3f} and the output {OUT:.3f}')
    print(f'with {w2[0]:+.2f} the sum is {sum2:+.3f} and the output {float(relu(sum2)):.3f}')
    fig, ax = plt.subplots(figsize=(13.5, 5.8), facecolor='white')
    _axes(ax, (0, 27), (0, 11.4), equal=False)
    _label(ax, 13.5, 10.8, 'Flipping one weight from minus to plus: the same readings, '
           'a different answer', size=13, weight='bold')
    for x0, ws, ps, tot, col, head in ((0.8, W, PROD, SUM, GRIP, 'weight on distance -2.00'),
                                       (14.2, w2, prod2, sum2, SLIDE,
                                        'weight on distance +2.00')):
        _label(ax, x0 + 5.8, 9.8, head, size=11.5, weight='bold', color=col)
        rows = [['reading', 'value', 'weight', 'product']]
        for nm, a, w, p in zip(SHORT, X, ws, ps):
            rows.append([nm, f'{a:.2f}', f'{w:+.2f}', f'{p:+.3f}'])
        rows.append(['bias', '-', f'{BIAS:+.2f}', f'{BIAS:+.3f}'])
        rows.append(['sum', '', '', f'{tot:+.3f}'])
        bottom = _table(ax, x0, 9.0, [3.6, 2.6, 2.6, 2.8], rows, row_h=1.1, size=10.8,
                        head_face=LINK_PALE)
        _label(ax, x0 + 5.8, bottom - 0.75, f'the rule gives {float(relu(tot)):.3f}',
               size=11.5, color=col, weight='bold')
    _label(ax, 13.5, 0.35, 'the first neuron answers "near, open and bright"; the second one '
           'answers "far, open and bright"', size=10, color=MUTED)
    _save(fig, ONE, 'flipping-one-weight.svg')


def weight_size_lines() -> None:
    """How the size of one weight tilts the line where the neuron switches on."""
    d = np.linspace(0.0, 1.0, 201)
    print('--- the size of the distance weight -----------------------------')
    fig, ax = plt.subplots(figsize=(8.8, 6.2), facecolor='white')
    _plain(ax)
    for wd, col in ((-1.0, SLIDE), (-2.0, LINK), (-4.0, GRIP)):
        g = (-wd * d - W[2] * BRIGHT - BIAS) / W[1]
        ax.plot(d, g, color=col, lw=2.4, label=f'weight on distance {wd:+.2f}')
        inside = (g >= 0) & (g <= 1)
        print(f'  weight {wd:+.2f}: the line crosses the square from opening '
              f'{g[inside][0]:.3f} to {g[inside][-1]:.3f}')
    s_plus = 2.0 * d[:, None] + W[1] * d[None, :] + W[2] * BRIGHT + BIAS
    print(f'  weight +2.00: the smallest sum anywhere in the square is '
          f'{float(s_plus.min()):+.3f}, so the neuron is never off')
    ax.plot([DIST_M], [X[1]], 'o', color=JOINT, ms=12, mec=INK, zorder=6)
    _label(ax, DIST_M + 0.04, X[1] + 0.05, 'our reading', size=10, ha='left')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('distance to the object (m)', fontsize=10)
    ax.set_ylabel('gripper opening / 100', fontsize=10)
    ax.set_title('A bigger weight on the distance tilts the switch-on line towards upright',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper left')
    _label(ax, 0.62, 0.12, 'below each line the neuron gives 0', size=10, color=MUTED)
    _save(fig, ONE, 'weight-size-lines.svg')


def moving_the_bias() -> None:
    """The bias slides the whole line up and down, so the elbow moves."""
    d = np.linspace(0.0, 1.0, 401)
    fig, ax = plt.subplots(figsize=(10.5, 5.6), facecolor='white')
    _plain(ax)
    print('--- moving the bias ---------------------------------------------')
    for b, col in ((0.5, LINK), (0.0, JOINT), (-1.0, GRIP)):
        out = relu(neuron_sum(d, b=b))
        cross = (OTHER_TWO + b) / 2.0
        ax.plot(d, out, color=col, lw=2.4, label=f'bias {b:+.2f}')
        ax.plot([cross], [0.0], 'o', color=col, ms=9, mec=INK, zorder=6)
        print(f'  bias {b:+.2f}: output at 0.42 m is {float(relu(neuron_sum(0.42, b=b))):.3f}, '
              f'and the output reaches 0 at {cross:.4f} m')
    ax.set_xlabel('distance to the object (m)', fontsize=10)
    ax.set_ylabel("the neuron's output after the rule", fontsize=10)
    ax.set_title('The bias moves the elbow: where the neuron falls silent, in metres',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    ax.set_ylim(-0.12, 1.75)
    _label(ax, 0.55, 1.45, 'the dots mark the elbow, where the output first reaches 0',
           size=9.8, color=MUTED, ha='center')
    _save(fig, ONE, 'moving-the-bias.svg')


# ==========================================================================
# 01_one-neuron.md  --  section 4: why a weighted sum is not enough
# ==========================================================================

CH_W: list[float] = [-2.0, 3.0, 0.5]
CH_B: list[float] = [0.5, -0.4, 1.2]


def _chain(d: Arr | float, depth: int, with_rule: bool = False) -> Arr:
    v = np.asarray(d, dtype=float)
    for i in range(depth):
        v = v * CH_W[i] + CH_B[i]
        if with_rule and i < depth - 1:
            v = relu(v)
    return v


def two_plain_layers() -> None:
    """Two neurons in a row with no rule between them are one neuron."""
    mid = DIST_M * CH_W[0] + CH_B[0]
    out = mid * CH_W[1] + CH_B[1]
    cw = CH_W[0] * CH_W[1]
    cb = CH_B[0] * CH_W[1] + CH_B[1]
    print('--- two plain layers collapse -----------------------------------')
    print(f'first neuron: {DIST_M} x {CH_W[0]:+.2f} {CH_B[0]:+.2f} = {mid:+.3f}')
    print(f'second neuron: {mid:+.3f} x {CH_W[1]:+.2f} {CH_B[1]:+.2f} = {out:+.3f}')
    print(f'the pair equals one neuron with weight {cw:+.2f} and bias {cb:+.2f}: '
          f'{DIST_M} x {cw:+.2f} {cb:+.2f} = {DIST_M * cw + cb:+.3f}')
    fig, ax = plt.subplots(figsize=(14.0, 5.6), facecolor='white')
    _axes(ax, (0, 30), (0, 12))
    _label(ax, 15, 11.4, 'Two neurons in a row, with nothing between them, are one neuron',
           size=13, weight='bold')
    y = 8.0
    ax.add_patch(plt.Circle((2.0, y), 0.85, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                            zorder=4))
    _label(ax, 2.0, y, f'{DIST_M}', size=11.5, family=MONO)
    _label(ax, 2.0, y + 1.5, 'distance', size=10, color=MUTED)
    _arrow(ax, (2.9, y), (4.6, y))
    _box(ax, 4.8, y - 1.0, 4.4, 2.0, face='white', edge=JOINT)
    _label(ax, 7.0, y + 0.45, f'x {CH_W[0]:+.2f}, then {CH_B[0]:+.2f}', size=10.5, family=MONO)
    _label(ax, 7.0, y - 0.5, f'= {mid:+.3f}', size=11.5, family=MONO, weight='bold')
    _arrow(ax, (9.4, y), (11.1, y))
    _box(ax, 11.3, y - 1.0, 4.4, 2.0, face='white', edge=JOINT)
    _label(ax, 13.5, y + 0.45, f'x {CH_W[1]:+.2f}, then {CH_B[1]:+.2f}', size=10.5, family=MONO)
    _label(ax, 13.5, y - 0.5, f'= {out:+.3f}', size=11.5, family=MONO, weight='bold')
    _arrow(ax, (15.9, y), (17.6, y))
    ax.add_patch(plt.Circle((18.6, y), 0.95, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                            zorder=4))
    _label(ax, 18.6, y, f'{out:+.2f}', size=11, family=MONO)
    _label(ax, 24.5, y + 1.1, 'the two weights multiply\nand the first bias is scaled',
           size=10, color=MUTED)
    _label(ax, 24.5, y - 0.9, f'{CH_W[1]:+.2f} x ({CH_W[0]:+.2f} d {CH_B[0]:+.2f}) '
           f'{CH_B[1]:+.2f}', size=10.5, family=MONO)
    y2 = 3.2
    ax.add_patch(plt.Circle((2.0, y2), 0.85, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                            zorder=4))
    _label(ax, 2.0, y2, f'{DIST_M}', size=11.5, family=MONO)
    _arrow(ax, (2.9, y2), (4.6, y2))
    _box(ax, 4.8, y2 - 1.0, 10.9, 2.0, face='white', edge=SLIDE)
    _label(ax, 10.25, y2 + 0.45, f'one neuron: x {cw:+.2f}, then {cb:+.2f}',
           size=10.5, family=MONO)
    _label(ax, 10.25, y2 - 0.5, f'= {DIST_M * cw + cb:+.3f}', size=11.5, family=MONO,
           weight='bold')
    _arrow(ax, (15.9, y2), (17.6, y2))
    ax.add_patch(plt.Circle((18.6, y2), 0.95, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                            zorder=4))
    _label(ax, 18.6, y2, f'{DIST_M * cw + cb:+.2f}', size=11, family=MONO)
    _label(ax, 24.5, y2, 'the same answer, from\nhalf the arithmetic', size=10, color=MUTED)
    _save(fig, ONE, 'two-plain-layers.svg')


def collapse_curves() -> None:
    """The collapse drawn: two plain layers and the one equivalent neuron are the same line."""
    d = np.linspace(0.0, 1.0, 401)
    pair = _chain(d, 2)
    cw = CH_W[0] * CH_W[1]
    cb = CH_B[0] * CH_W[1] + CH_B[1]
    single = d * cw + cb
    bent = _chain(d, 2, with_rule=True)
    gap = float(np.max(np.abs(pair - single)))
    print('--- the collapse drawn ------------------------------------------')
    print(f'biggest gap between the two plain layers and the single neuron: {gap:.2e}')
    print(f'with the rule in the middle the output is {float(_chain(0.0, 2, True)):+.3f} '
          f'at 0 m and {float(_chain(0.42, 2, True)):+.3f} at 0.42 m, and it bends at '
          f'{CH_B[0] / -CH_W[0]:.3f} m')
    fig, ax = plt.subplots(figsize=(10.5, 5.6), facecolor='white')
    _plain(ax)
    ax.plot(d, pair, color=LINK, lw=5.0, alpha=0.4, label='two plain layers, one after the other')
    ax.plot(d, single, color=GRIP, lw=2.0, ls='--',
            label=f'one neuron, weight {cw:+.2f}, bias {cb:+.2f}')
    ax.plot(d, bent, color=SLIDE, lw=2.4,
            label='the same two layers with the rule between them')
    ax.axhline(0, color=INK, lw=1.0)
    ax.axvline(CH_B[0] / -CH_W[0], color=MUTED, lw=1.0, ls=':')
    ax.set_xlabel('distance to the object (m)', fontsize=10)
    ax.set_ylabel('what comes out of the second layer', fontsize=10)
    ax.set_title(f'Without the rule the two layers lie exactly on one straight line '
                 f'(biggest gap {gap:.0e})', fontsize=12, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='lower left')
    _label(ax, CH_B[0] / -CH_W[0] + 0.02, 1.0, 'the bend the rule makes,\nat 0.25 m',
           size=9.8, color=MUTED, ha='left')
    _save(fig, ONE, 'collapse-curves.svg')


def three_plain_layers() -> None:
    """Three plain layers collapse in the same way, to one weight and one bias."""
    vals = [DIST_M]
    for i in range(3):
        vals.append(vals[-1] * CH_W[i] + CH_B[i])
    cw = CH_W[0] * CH_W[1] * CH_W[2]
    cb = (CH_B[0] * CH_W[1] + CH_B[1]) * CH_W[2] + CH_B[2]
    print('--- three plain layers collapse ---------------------------------')
    print('  values along the chain: ' + ' -> '.join(f'{v:+.3f}' for v in vals))
    print(f'  one neuron with weight {cw:+.2f} and bias {cb:+.2f} gives '
          f'{DIST_M * cw + cb:+.3f}')
    fig, ax = plt.subplots(figsize=(12.5, 5.2), facecolor='white')
    _axes(ax, (0, 26), (0, 10.4), equal=False)
    _label(ax, 13, 9.8, 'Three plain layers: still one weight and one bias in the end',
           size=13, weight='bold')
    rows = [['layer', 'weight', 'bias', 'what comes out']]
    for i in range(3):
        rows.append([f'layer {i + 1}', f'{CH_W[i]:+.2f}', f'{CH_B[i]:+.2f}', f'{vals[i + 1]:+.3f}'])
    rows.append(['all three at once', f'{cw:+.2f}', f'{cb:+.2f}', f'{DIST_M * cw + cb:+.3f}'])
    bottom = _table(ax, 3.0, 8.6, [6.4, 3.4, 3.4, 5.2], rows, row_h=1.2, size=11)
    _label(ax, 12.2, bottom - 0.8, f'the reading going in is {DIST_M} m, and both roads '
           f'end at {DIST_M * cw + cb:+.3f}', size=11)
    _label(ax, 12.2, bottom - 1.7, f'the three weights multiply: {CH_W[0]:+.2f} x '
           f'{CH_W[1]:+.2f} x {CH_W[2]:+.2f} = {cw:+.2f}', size=10, color=MUTED)
    _save(fig, ONE, 'three-plain-layers.svg')


def a_bend_is_needed() -> None:
    """A job no straight line can do: brightness that is best in the middle."""
    b = np.linspace(0.0, 1.0, 501)
    target = 1.0 - 2.0 * np.abs(b - 0.5)
    A = np.stack([b, np.ones_like(b)], axis=1)
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    line = A @ coef
    built = 1.0 - 2.0 * relu(b - 0.5) - 2.0 * relu(0.5 - b)
    err_line = float(np.mean(np.abs(line - target)))
    err_built = float(np.max(np.abs(built - target)))
    print('--- a bend is needed --------------------------------------------')
    print(f'the best straight line is {coef[0]:+.4f} x brightness {coef[1]:+.4f}, '
          f'and its average error is {err_line:.4f}')
    print(f'two rule-neurons rebuild the target exactly: biggest gap {err_built:.2e}')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    for ax in axes:
        _plain(ax)
        ax.set_xlabel('patch brightness / 255', fontsize=10)
        ax.set_ylim(-0.1, 1.15)
    axes[0].plot(b, target, color=INK, lw=2.6, label='what we want')
    axes[0].plot(b, line, color=GRIP, lw=2.4, ls='--',
                 label=f'best straight line (average error {err_line:.3f})')
    axes[0].fill_between(b, target, line, color=GRIP, alpha=0.15)
    axes[0].set_ylabel('how good this brightness is for finding the object', fontsize=10)
    axes[0].set_title('One plain neuron cannot bend', fontsize=12.5, weight='bold')
    axes[0].legend(fontsize=9.6, frameon=False, loc='lower center')
    axes[1].plot(b, relu(b - 0.5), color=LINK, lw=2.0, label='neuron A: rule(brightness - 0.50)')
    axes[1].plot(b, relu(0.5 - b), color=SLIDE, lw=2.0, label='neuron B: rule(0.50 - brightness)')
    axes[1].plot(b, built, color=JOINT, lw=3.0, label='1.00 - 2 x A - 2 x B')
    axes[1].plot(b, target, color=INK, lw=1.2, ls=':', label='what we want')
    axes[1].set_title(f'Two neurons with the rule hit it exactly (gap {err_built:.0e})',
                      fontsize=12.5, weight='bold')
    axes[1].legend(fontsize=9.4, frameon=False, loc='lower center')
    _save(fig, ONE, 'a-bend-is-needed.svg')


# ==========================================================================
# 01_one-neuron.md  --  section 5: the rectified linear unit
# ==========================================================================

CHECK: list[float] = [-2.0, -1.0, -0.5, 0.0, 0.5, 0.725, 1.0, 2.0]


def relu_curve() -> None:
    """The rule drawn on real axes, with the numbers it gives beside it."""
    z = np.linspace(-3.0, 3.0, 601)
    print('--- the rectified linear unit -----------------------------------')
    for c in CHECK:
        print(f'  in {c:+.3f} -> out {float(relu(c)):.3f}')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1.0]})
    ax = axes[0]
    _plain(ax)
    ax.plot(z, relu(z), color=LINK, lw=2.8)
    ax.axhline(0, color=INK, lw=1.0)
    ax.axvline(0, color=INK, lw=1.0)
    for c in (-1.0, 0.725, 2.0):
        ax.plot([c], [float(relu(c))], 'o', color=JOINT, ms=10, mec=INK, zorder=6)
        ax.annotate(f'{c:+.3f} -> {float(relu(c)):.3f}', xy=(c, float(relu(c))),
                    xytext=(c - 0.1, float(relu(c)) + 0.55), fontsize=10, ha='center',
                    arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.1))
    ax.set_xlabel('the weighted sum going in', fontsize=10)
    ax.set_ylabel('the output coming out', fontsize=10)
    ax.set_title('The rectified linear unit: flat at 0, then a straight 45 degree climb',
                 fontsize=12, weight='bold')
    ax.set_ylim(-0.4, 3.3)
    _label(ax, -1.7, 0.45, 'this half is\nswitched off', size=10, color=MUTED)
    ax2 = axes[1]
    _axes(ax2, (0, 12), (0, 11), equal=False)
    rows = [['sum going in', 'output']]
    for c in CHECK:
        rows.append([f'{c:+.3f}', f'{float(relu(c)):.3f}'])
    _table(ax2, 1.4, 10.2, [5.0, 4.0], rows, row_h=1.08, size=11, mono_from=0)
    _label(ax2, 6.0, 0.5, 'our neuron\'s sum was +0.725', size=10.5, color=MUTED)
    _save(fig, ONE, 'relu-curve.svg')


def relu_pieces() -> None:
    """Six rule-neurons with elbows in different places follow a smooth curve."""
    b = np.linspace(0.0, 1.0, 1001)
    target = np.exp(-((b - 0.45) / 0.18) ** 2)
    knots = np.array([0.10, 0.25, 0.40, 0.55, 0.70, 0.85])
    feats = [np.ones_like(b), b] + [relu(b - k) for k in knots]
    A = np.stack(feats, axis=1)
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    fit = A @ coef
    gap = float(np.max(np.abs(fit - target)))
    print('--- six elbows follow a curve -----------------------------------')
    print('  elbows at ' + ', '.join(f'{k:.2f}' for k in knots))
    print(f'  biggest gap between the six-elbow line and the smooth curve: {gap:.4f}')
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(b, target, color=INK, lw=2.6, label='the smooth curve we want')
    ax.plot(b, fit, color=GRIP, lw=2.4, label=f'six elbows added up (biggest gap {gap:.3f})')
    for k in knots:
        ax.axvline(k, color=MUTED, lw=0.9, ls=':')
    ax.set_xlabel('patch brightness / 255', fontsize=10)
    ax.set_ylabel('how good this brightness is', fontsize=10)
    ax.set_title('Straight pieces with elbows can follow any curve you like',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    _label(ax, 0.5, -0.17, 'the dotted lines are the six elbows, one per neuron',
           size=9.8, color=MUTED)
    ax.set_ylim(-0.1, 1.2)
    _save(fig, ONE, 'relu-pieces.svg')


def relu_dead_units() -> None:
    """How often each of 64 simulated neurons fires, and how many never fire at all."""
    rng = np.random.default_rng(7)
    n_neu, n_read = 64, 200
    w = rng.normal(0.0, 1.0, size=(n_neu, 3))
    bias = rng.normal(-1.0, 0.6, size=n_neu)
    reads = np.stack([rng.uniform(0.10, 0.90, n_read),
                      rng.uniform(0.00, 1.00, n_read),
                      rng.uniform(0.10, 0.90, n_read)], axis=1)
    sums = reads @ w.T + bias
    fires = (sums > 0).mean(axis=0)
    dead = int((fires == 0).sum())
    print('--- dead neurons ------------------------------------------------')
    print(f'of {n_neu} simulated neurons reading {n_read} simulated moments, {dead} never '
          f'fire at all, and the average neuron fires on {fires.mean() * 100:.1f}% of them')
    fig, ax = plt.subplots(figsize=(9.6, 5.6), facecolor='white')
    _axes(ax, (0, 8.6), (0, 10.4))
    _label(ax, 4.3, 9.9, 'Each square is one neuron: how often it gives something above 0',
           size=12.5, weight='bold')
    for i in range(n_neu):
        r, c = divmod(i, 8)
        x, y = 0.3 + c, 8.3 - r
        v = fires[i]
        ax.add_patch(Rectangle((x, y), 0.92, 0.92, facecolor=plt.get_cmap('YlGnBu')(0.15 + 0.8 * v),
                               edgecolor=GRID, lw=0.8, zorder=3))
        if v == 0:
            ax.add_patch(Rectangle((x, y), 0.92, 0.92, facecolor='none', edgecolor=GRIP, lw=2.2,
                                   zorder=5))
            _label(ax, x + 0.46, y + 0.46, '0', size=10.5, color=GRIP, family=MONO)
        else:
            _label(ax, x + 0.46, y + 0.46, f'{v * 100:.0f}', size=9.2, family=MONO)
    _label(ax, 4.3, 0.55, f'the number in each square is the percentage of the 200 moments '
           f'that neuron fired on', size=10, color=MUTED)
    _label(ax, 4.3, -0.1, f'{dead} of the 64 never fired, so the rule had switched them off '
           f'for every reading', size=10.5, color=GRIP)
    _save(fig, ONE, 'relu-dead-units.svg')


def relu_slope() -> None:
    """The slope of the rule: 0 on the left, 1 on the right, and a jump at 0."""
    z = np.linspace(-3.0, 3.0, 1201)
    h = 1e-5
    slope = (relu(z + h) - relu(z - h)) / (2 * h)
    print('--- the slope of the rule ---------------------------------------')
    for c in (-1.0, -0.001, 0.001, 1.0):
        print(f'  slope at {c:+.4f}: {float((relu(c + h) - relu(c - h)) / (2 * h)):.3f}')
    fig, ax = plt.subplots(figsize=(10.0, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(z[z < -0.002], slope[z < -0.002], color=LINK, lw=2.8)
    ax.plot(z[z > 0.002], slope[z > 0.002], color=LINK, lw=2.8)
    ax.plot([0], [0], 'o', mfc='white', mec=LINK, ms=9, mew=2)
    ax.plot([0], [1], 'o', mfc='white', mec=LINK, ms=9, mew=2)
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_xlabel('the weighted sum going in', fontsize=10)
    ax.set_ylabel('how much the output moves\nwhen the sum moves a little', fontsize=10)
    ax.set_title('The slope of the rule jumps from 0 to 1 at a single point',
                 fontsize=12.5, weight='bold')
    ax.set_ylim(-0.15, 1.3)
    _label(ax, -1.6, 0.18, 'nothing comes out, so\nnothing changes', size=10, color=MUTED)
    _label(ax, 1.6, 0.82, 'the output follows\nthe sum exactly', size=10, color=MUTED)
    _save(fig, ONE, 'relu-slope.svg')


# ==========================================================================
# 01_one-neuron.md  --  section 6: GELU and SiLU
# ==========================================================================

def three_rules() -> None:
    """ReLU, GELU and SiLU on the same axes, with the numbers they give."""
    z = np.linspace(-4.0, 4.0, 801)
    print('--- the three rules ---------------------------------------------')
    hdr = '  in        ' + '  '.join(f'{nm:>8s}' for nm in ACTS)
    print(hdr)
    for c in CHECK:
        line = f'  {c:+7.3f}   ' + '  '.join(f'{float(f(c)):8.4f}' for f in ACTS.values())
        print(line)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1.3, 1.0]})
    ax = axes[0]
    _plain(ax)
    for nm, f in ACTS.items():
        ax.plot(z, f(z), color=ACT_COLOUR[nm], lw=2.6, label=nm,
                ls='-' if nm != 'SiLU' else '--')
    ax.axhline(0, color=INK, lw=1.0)
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_xlabel('the weighted sum going in', fontsize=10)
    ax.set_ylabel('the output coming out', fontsize=10)
    ax.set_title('All three climb on the right; only two dip below 0 on the left',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_ylim(-0.6, 4.3)
    axin = ax.inset_axes((0.56, 0.12, 0.42, 0.42))
    zz = np.linspace(-3.0, 0.5, 401)
    for nm, f in ACTS.items():
        axin.plot(zz, f(zz), color=ACT_COLOUR[nm], lw=2.0, ls='-' if nm != 'SiLU' else '--')
    axin.axhline(0, color=INK, lw=0.8)
    axin.set_title('the left half, close up', fontsize=9)
    axin.tick_params(labelsize=8)
    axin.grid(True, color=GRID, lw=0.6)
    ax2 = axes[1]
    _axes(ax2, (0, 13), (0, 11), equal=False)
    rows = [['sum in'] + list(ACTS)]
    for c in CHECK:
        rows.append([f'{c:+.3f}'] + [f'{float(f(c)):+.4f}' for f in ACTS.values()])
    _table(ax2, 0.6, 10.4, [3.2, 2.9, 2.9, 2.9], rows, row_h=1.1, size=10.5, mono_from=0)
    _label(ax2, 6.4, 0.5, 'the smallest GELU ever gives is about -0.17', size=10, color=MUTED)
    _save(fig, ONE, 'three-rules.svg')


def three_slopes() -> None:
    """The slope of each rule, worked out by moving the input a tiny amount."""
    z = np.linspace(-4.0, 4.0, 1601)
    h = 1e-5
    print('--- the slopes of the three rules -------------------------------')
    mins = {}
    for nm, f in ACTS.items():
        sl = (f(z + h) - f(z - h)) / (2 * h)
        mins[nm] = (float(sl.min()), float(z[int(np.argmin(sl))]))
        print(f'  {nm:5s} slope at -2: {float((f(-2 + h) - f(-2 - h)) / (2 * h)):+.4f}, '
              f'at 0: {float((f(h) - f(-h)) / (2 * h)):+.4f}, '
              f'at +2: {float((f(2 + h) - f(2 - h)) / (2 * h)):+.4f}; '
              f'smallest slope {mins[nm][0]:+.4f} near {mins[nm][1]:+.2f}')
    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor='white')
    _plain(ax)
    for nm, f in ACTS.items():
        sl = (f(z + h) - f(z - h)) / (2 * h)
        ax.plot(z, sl, color=ACT_COLOUR[nm], lw=2.6, label=nm,
                ls='-' if nm != 'SiLU' else '--')
    ax.axhline(0, color=INK, lw=1.0)
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_xlabel('the weighted sum going in', fontsize=10)
    ax.set_ylabel('how much the output moves\nwhen the sum moves a little', fontsize=10)
    ax.set_title('GELU and SiLU change their slope smoothly, and ReLU jumps',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_ylim(-0.25, 1.35)
    _label(ax, 1.9, 0.25, f"SiLU's slope dips to {mins['SiLU'][0]:+.3f} "
           f"near {mins['SiLU'][1]:+.2f}", size=9.8, color=MUTED)
    _save(fig, ONE, 'three-slopes.svg')


def neuron_three_rules() -> None:
    """Our neuron under all three rules, as the distance changes."""
    d = np.linspace(0.0, 1.0, 801)
    s = neuron_sum(d)
    print('--- our neuron under the three rules ----------------------------')
    for dd in (0.42, ZERO_D, 0.85, 0.95):
        sv = float(neuron_sum(dd))
        print(f'  at {dd:.4f} m the sum is {sv:+.4f} -> ' +
              ', '.join(f'{nm} {float(f(sv)):+.4f}' for nm, f in ACTS.items()))
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    for ax in axes:
        _plain(ax)
        ax.set_xlabel('distance to the object (m)', fontsize=10)
    for nm, f in ACTS.items():
        axes[0].plot(d, f(s), color=ACT_COLOUR[nm], lw=2.4, label=nm,
                     ls='-' if nm != 'SiLU' else '--')
        axes[1].plot(d, f(s), color=ACT_COLOUR[nm], lw=2.4, label=nm,
                     ls='-' if nm != 'SiLU' else '--')
    axes[0].axhline(0, color=INK, lw=1.0)
    axes[0].set_ylabel("the neuron's output", fontsize=10)
    axes[0].set_title('The same neuron, the same readings, three rules',
                      fontsize=12, weight='bold')
    axes[0].legend(fontsize=10, frameon=False, loc='upper right')
    axes[1].set_xlim(0.62, 1.0)
    axes[1].set_ylim(-0.12, 0.30)
    axes[1].axhline(0, color=INK, lw=1.0)
    axes[1].axvline(ZERO_D, color=MUTED, lw=1.0, ls=':')
    axes[1].set_title(f'close up on the elbow at {ZERO_D:.4f} m', fontsize=12, weight='bold')
    axes[1].set_ylabel('the output, close up', fontsize=10)
    _label(axes[1], 0.90, -0.075, 'GELU and SiLU go a little\nbelow 0 here', size=9.8,
           color=MUTED)
    _save(fig, ONE, 'neuron-three-rules.svg')


def activation_cost() -> None:
    """What the rule costs next to the multiplying and adding in the same layer."""
    n_in, n_out = 1024, 1024
    mult_adds = n_in * n_out
    acts = n_out
    rng = np.random.default_rng(3)
    big = rng.normal(0.0, 1.0, size=2_000_000)
    times: dict[str, float] = {}
    for nm, f in ACTS.items():
        best = min(_time_once(f, big) for _ in range(3))
        times[nm] = best
    print('--- what the rule costs -----------------------------------------')
    print(f'a layer of {n_in} inputs and {n_out} neurons does {mult_adds:,} multiply-adds '
          f'and applies the rule {acts:,} times, which is one rule for every '
          f'{mult_adds // acts:,} multiply-adds')
    for nm, t in times.items():
        print(f'  {nm:5s} on 2,000,000 numbers took {t * 1000:.1f} ms '
              f'({t / times["ReLU"]:.1f} times ReLU) on the computer that drew this')
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar(['multiply-adds', 'uses of the rule'], [mult_adds, acts],
           color=[LINK, PURPLE], edgecolor=INK, lw=0.8, width=0.5)
    ax.set_yscale('log')
    ax.set_ylabel('how many times, for one layer', fontsize=10)
    for i, v in enumerate([mult_adds, acts]):
        ax.text(i, v * 1.3, f'{v:,}', ha='center', fontsize=11.5, family=MONO)
    ax.set_ylim(100, 1e7)
    ax.set_title(f'A 1024 into 1024 layer: one rule per {mult_adds // acts:,} multiply-adds',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    names = list(times)
    ax.bar(names, [times[n] * 1000 for n in names],
           color=[ACT_COLOUR[n] for n in names], edgecolor=INK, lw=0.8, width=0.5)
    for i, n in enumerate(names):
        ax.text(i, times[n] * 1000 * 1.02, f'{times[n] * 1000:.1f} ms', ha='center',
                va='bottom', fontsize=11, family=MONO)
    ax.set_ylabel('time for 2,000,000 numbers (ms)', fontsize=10)
    ax.set_ylim(0, max(times.values()) * 1000 * 1.25)
    ax.set_title('One measurement, on the computer that drew this picture',
                 fontsize=11.5, weight='bold')
    _save(fig, ONE, 'activation-cost.svg')


def _time_once(f: object, arr: Arr) -> float:
    t0 = time.perf_counter()
    f(arr)                                        # type: ignore[operator]
    return time.perf_counter() - t0
