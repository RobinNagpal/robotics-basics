"""Generate the diagrams for the first two pages of docs/05_neural-networks/02_inside-a-network/.

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
repeatable. No picture here reports a measured time, because the parameter
counts, the multiply-add counts and the memory sizes are all counted exactly.
"""

import math
import pathlib
import sys

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
    _axes(ax, (0, 32), (0, 12.8))
    _label(ax, 16, 12.3, 'One neuron: multiply, add, add the bias, then apply the rule',
           size=13, weight='bold')
    ys = [9.0, 6.0, 3.0]
    names = ['distance to object (m)', 'gripper opening /100', 'patch brightness /255']
    cx, bx, sx = 6.9, 9.4, 19.2
    sy = 6.0
    _label(ax, 2.0, 11.0, 'reading', size=10.5, weight='bold', color=MUTED)
    _label(ax, 10.5, 11.0, 'weight', size=10.5, weight='bold', color=MUTED)
    _label(ax, 14.6, 11.0, 'product', size=10.5, weight='bold', color=MUTED)
    for y, nm, a, w, p in zip(ys, names, X, W, PROD):
        _label(ax, 0.1, y + 0.95, nm, size=9.5, ha='left', color=MUTED)
        ax.add_patch(plt.Circle((cx, y), 0.8, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                                zorder=4))
        _label(ax, cx, y, f'{a:.2f}', size=11.5, family=MONO)
        ax.plot([cx + 0.8, bx], [y, y], color=MUTED, lw=1.3, zorder=2)
        _box(ax, bx, y - 0.5, 2.2, 1.0, face='white', edge=JOINT)
        _label(ax, bx + 1.1, y, f'{w:+.2f}', size=11.5, family=MONO)
        _label(ax, bx + 2.5, y, f'= {p:+.3f}', size=11, family=MONO, ha='left')
        ax.plot([14.2, sx - 1.55], [y, sy + (y - sy) * 0.22], color=MUTED, lw=1.3, zorder=2)
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
    _axes(ax, (0, 27), (0.9, 15.1))
    _label(ax, 13.5, 14.5, 'The three readings, and how each one becomes a number near 1',
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
    _label(ax, 21.7, 13.8, 'the three inputs', size=10.5, weight='bold', color=LINK)
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
    _axes(ax, (0, 24), (1.2, 10.9), equal=False)
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
    ax.annotate(f'our reading -> {SUM:.3f}', xy=(DIST_M, X[1]), xytext=(0.07, 0.82),
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
    dd, gg = np.meshgrid(d, d)                  # both readings run from 0 to 1
    s_plus = 2.0 * dd + W[1] * gg + W[2] * BRIGHT + BIAS
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
    _label(ax, 0.03, 0.70, 'to the right of each line the sum\nis below 0, so the neuron gives 0', size=10, color=MUTED, ha='left')
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
    _box(ax, 4.8, y - 1.0, 5.2, 2.0, face='white', edge=JOINT)
    _label(ax, 7.4, y + 0.45, f'x {CH_W[0]:+.2f}, then {CH_B[0]:+.2f}', size=10.5, family=MONO)
    _label(ax, 7.4, y - 0.5, f'= {mid:+.3f}', size=11.5, family=MONO, weight='bold')
    _arrow(ax, (10.0, y), (11.3, y))
    _box(ax, 11.5, y - 1.0, 5.2, 2.0, face='white', edge=JOINT)
    _label(ax, 14.1, y + 0.45, f'x {CH_W[1]:+.2f}, then {CH_B[1]:+.2f}', size=10.5, family=MONO)
    _label(ax, 14.1, y - 0.5, f'= {out:+.3f}', size=11.5, family=MONO, weight='bold')
    _arrow(ax, (16.7, y), (17.6, y))
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
    _box(ax, 4.8, y2 - 1.0, 11.9, 2.0, face='white', edge=SLIDE)
    _label(ax, 10.75, y2 + 0.45, f'one neuron: x {cw:+.2f}, then {cb:+.2f}',
           size=10.5, family=MONO)
    _label(ax, 10.75, y2 - 0.5, f'= {DIST_M * cw + cb:+.3f}', size=11.5, family=MONO,
           weight='bold')
    _arrow(ax, (16.7, y2), (17.6, y2))
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
    _axes(ax, (0, 26), (0.3, 10.2), equal=False)
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
        ax.set_ylim(-0.1, 1.5)
    axes[0].plot(b, target, color=INK, lw=2.6, label='what we want')
    axes[0].plot(b, line, color=GRIP, lw=2.4, ls='--',
                 label=f'best straight line (average error {err_line:.3f})')
    axes[0].fill_between(b, target, line, color=GRIP, alpha=0.15)
    axes[0].set_ylabel('how good this brightness is for finding the object', fontsize=10)
    axes[0].set_title('One plain neuron cannot bend', fontsize=12.5, weight='bold')
    axes[0].legend(fontsize=9.6, frameon=False, loc='upper left')
    axes[1].plot(b, relu(b - 0.5), color=LINK, lw=2.0, label='neuron A: rule(brightness - 0.50)')
    axes[1].plot(b, relu(0.5 - b), color=SLIDE, lw=2.0, label='neuron B: rule(0.50 - brightness)')
    axes[1].plot(b, built, color=JOINT, lw=3.0, label='1.00 - 2 x A - 2 x B')
    axes[1].plot(b, target, color=INK, lw=1.2, ls=':', label='what we want')
    axes[1].set_title(f'Two neurons with the rule hit it exactly (gap {err_built:.0e})',
                      fontsize=12.5, weight='bold')
    axes[1].legend(fontsize=9.4, frameon=False, loc='upper center', ncol=2)
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
    _label(ax, -2.0, 1.5, 'this half is\nswitched off', size=10, color=MUTED)
    ax2 = axes[1]
    _axes(ax2, (0, 12), (0, 11), equal=False)
    rows = [['sum going in', 'output']]
    for c in CHECK:
        rows.append([f'{c:+.3f}', f'{float(relu(c)):.3f}'])
    _table(ax2, 1.4, 10.6, [5.0, 4.0], rows, row_h=1.0, size=11, mono_from=0)
    _label(ax2, 6.0, 0.7, 'our neuron\'s sum was +0.725', size=10.5, color=MUTED)
    _save(fig, ONE, 'relu-curve.svg')


def relu_pieces() -> None:
    """Six rule-neurons with elbows in different places follow a smooth curve."""
    b = np.linspace(0.0, 1.0, 1001)
    target = np.exp(-((b - 0.45) / 0.18) ** 2)
    def hinge_fit(n: int) -> tuple[Arr, Arr, float]:
        ks = np.linspace(0.08, 0.92, n)
        A = np.stack([np.ones_like(b), b] + [relu(b - k) for k in ks], axis=1)
        coef, *_ = np.linalg.lstsq(A, target, rcond=None)
        f = A @ coef
        return ks, f, float(np.max(np.abs(f - target)))

    knots, fit, gap = hinge_fit(6)
    knots12, fit12, gap12 = hinge_fit(12)
    print('--- elbows follow a curve ---------------------------------------')
    print('  6 elbows at ' + ', '.join(f'{k:.2f}' for k in knots))
    print(f'  biggest gap with 6 elbows: {gap:.4f}; with 12 elbows: {gap12:.4f}')
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(b, target, color=INK, lw=2.6, label='the smooth curve we want')
    ax.plot(b, fit, color=GRIP, lw=2.4, label=f'6 elbows added up (biggest gap {gap:.3f})')
    ax.plot(b, fit12, color=SLIDE, lw=2.0, ls='--',
            label=f'12 elbows added up (biggest gap {gap12:.3f})')
    for k in knots:
        ax.axvline(k, color=MUTED, lw=0.9, ls=':')
    ax.set_xlabel('patch brightness / 255', fontsize=10)
    ax.set_ylabel('how good this brightness is', fontsize=10)
    ax.set_title('Straight pieces with elbows can follow any curve you like',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    _label(ax, 0.03, 0.80, 'the dotted lines are the six elbows,\none per neuron',
           size=9.8, color=MUTED, ha='left')
    ax.set_ylim(-0.1, 1.2)
    _save(fig, ONE, 'relu-pieces.svg')


def relu_dead_units() -> None:
    """How often each of 64 simulated neurons fires, and how many never fire at all."""
    rng = np.random.default_rng(7)
    n_neu, n_read = 64, 200
    w = rng.normal(0.0, 1.0, size=(n_neu, 3))
    bias = rng.normal(0.0, 0.5, size=n_neu)
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
        face = '#eeeeee' if v == 0 else plt.get_cmap('YlGnBu')(0.15 + 0.75 * v)
        ax.add_patch(Rectangle((x, y), 0.92, 0.92, facecolor=face, edgecolor=GRID, lw=0.8,
                               zorder=3))
        if v == 0:
            ax.add_patch(Rectangle((x, y), 0.92, 0.92, facecolor='none', edgecolor=GRIP, lw=2.2,
                                   zorder=5))
        _label(ax, x + 0.46, y + 0.46, f'{v * 100:.0f}', size=9.2, family=MONO,
               color=GRIP if v == 0 else INK)
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
    fine = np.linspace(-6.0, 6.0, 24001)
    g_min, s_min = float(gelu(fine).min()), float(silu(fine).min())
    print(f'  the lowest GELU ever gives is {g_min:.4f} at {fine[int(np.argmin(gelu(fine)))]:+.3f}; '
          f'the lowest SiLU is {s_min:.4f} at {fine[int(np.argmin(silu(fine)))]:+.3f}')
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
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_ylim(-0.6, 4.3)
    axin = ax.inset_axes((0.07, 0.50, 0.38, 0.44))
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
    _table(ax2, 0.6, 10.6, [3.2, 2.9, 2.9, 2.9], rows, row_h=1.02, size=10.5, mono_from=0)
    _label(ax2, 6.4, 0.6, f'the lowest GELU ever gives is {g_min:.3f}, '
           f'and SiLU {s_min:.3f}', size=10, color=MUTED)
    _save(fig, ONE, 'three-rules.svg')


def three_slopes() -> None:
    """The slope of each rule, worked out by moving the input a tiny amount."""
    z = np.linspace(-4.0, 4.0, 1601)
    h = 1e-5
    print('--- the slopes of the three rules -------------------------------')
    def slope_of(nm: str, zz: Arr) -> Arr:
        if nm == 'ReLU':                       # the rule has no single slope at 0
            out = (zz > 0).astype(float)
            out[np.abs(zz) < 1e-9] = np.nan
            return out
        f = ACTS[nm]
        return (f(zz + h) - f(zz - h)) / (2 * h)       # type: ignore[operator]

    mins = {}
    for nm in ACTS:
        sl = slope_of(nm, z)
        mins[nm] = (float(np.nanmin(sl)), float(z[int(np.nanargmin(sl))]))
        print(f'  {nm:5s} slope at -2: {float(slope_of(nm, np.array([-2.0]))[0]):+.4f}, '
              f'at +2: {float(slope_of(nm, np.array([2.0]))[0]):+.4f}; '
              f'smallest slope {mins[nm][0]:+.4f} near {mins[nm][1]:+.2f}')
    print('  ReLU has no single slope at 0, so that one point is left out')
    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor='white')
    _plain(ax)
    for nm in ACTS:
        ax.plot(z, slope_of(nm, z), color=ACT_COLOUR[nm], lw=2.6, label=nm,
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
    check = np.linspace(-6.0, 6.0, 12001)
    approx_gap = float(np.max(np.abs(gelu(check) - gelu_fast(check))))
    costs = [1, 5, 10, 20]
    rises = [k * acts / mult_adds * 100.0 for k in costs]
    print('--- what the rule costs -----------------------------------------')
    print(f'a layer of {n_in} inputs and {n_out} neurons does {mult_adds:,} multiply-adds '
          f'and applies the rule {acts:,} times, which is one rule for every '
          f'{mult_adds // acts:,} multiply-adds')
    for k, r in zip(costs, rises):
        print(f'  if one use of the rule costs as much as {k:2d} multiply-adds, the layer '
              f'does {r:.2f}% more work')
    print(f'  the fast GELU never differs from the exact one by more than {approx_gap:.5f}')
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
    ax.bar([str(k) for k in costs], rises, color=PURPLE, edgecolor=INK, lw=0.8, width=0.5)
    for i, r in enumerate(rises):
        ax.text(i, r + 0.03, f'{r:.2f}%', ha='center', va='bottom', fontsize=11, family=MONO)
    ax.set_ylabel("extra work for the whole layer", fontsize=10)
    ax.set_xlabel('how many multiply-adds one use of the rule costs', fontsize=10)
    ax.set_ylim(0, max(rises) * 1.25)
    ax.set_title('Even a rule that costs 20 multiply-adds adds under 2%',
                 fontsize=11.5, weight='bold')
    _save(fig, ONE, 'activation-cost.svg')


def gelu_fast(z: Arr | float) -> Arr:
    """The approximate GELU that libraries offer, built from tanh instead of erf."""
    za = np.asarray(z, dtype=float)
    return 0.5 * za * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (za + 0.044715 * za ** 3)))




# ==========================================================================
# 02_layers-and-depth.md  --  the four-neuron layer both early sections use
# ==========================================================================

W1: Arr = np.array([[-2.0, 1.5, 0.8],
                    [2.0, -1.0, 0.0],
                    [0.0, 2.0, -1.5],
                    [-1.0, -1.0, 1.0]])
B1: Arr = np.array([0.5, 0.2, -0.4, 0.3])
SUMS1: Arr = W1 @ X + B1
OUT1: Arr = relu(SUMS1)
NEU_JOB: list[str] = ['near, open and bright', 'far and closed',
                      'open but not bright', 'far, closed and bright']


def report_layer() -> None:
    print('--- the four-neuron layer ---------------------------------------')
    for i in range(4):
        parts = ' '.join(f'{X[j]:.2f}x{W1[i, j]:+.2f}' for j in range(3))
        print(f'  neuron {i + 1}: {parts} {B1[i]:+.2f} = {SUMS1[i]:+.3f} '
              f'-> output {OUT1[i]:.3f}')
    print(f'  the layer owns {W1.size} weights and {B1.size} biases, '
          f'{W1.size + B1.size} parameters in all')


def one_layer_four_neurons() -> None:
    """Four neurons reading the same three readings, each with its own weights."""
    fig, ax = plt.subplots(figsize=(14.0, 7.2), facecolor='white')
    _axes(ax, (0, 31), (-0.6, 15.4))
    _label(ax, 15, 14.9, 'One layer: four neurons read the same three readings',
           size=13, weight='bold')
    in_y = [10.6, 7.4, 4.2]
    out_y = [12.6, 9.2, 5.8, 2.4]
    for y, nm, a in zip(in_y, SHORT, X):
        ax.add_patch(plt.Circle((2.6, y), 0.85, facecolor=LINK_PALE, edgecolor=LINK, lw=1.4,
                                zorder=4))
        _label(ax, 2.6, y, f'{a:.2f}', size=11.5, family=MONO)
        _label(ax, 2.6, y + 1.35, nm, size=10, color=MUTED)
    for k, y in enumerate(out_y):
        for j, yi in enumerate(in_y):
            w = W1[k, j]
            ax.plot([3.5, 10.0], [yi, y], color=GRIP if w < 0 else SLIDE,
                    lw=0.7 + 0.9 * abs(w) / 2.0, alpha=0.75, zorder=2)
        _box(ax, 10.0, y - 1.15, 8.2, 2.3, face='white', edge=JOINT)
        _label(ax, 14.1, y + 0.5, f'neuron {k + 1}: ' +
               ' '.join(f'{W1[k, j]:+.1f}' for j in range(3)) + f'  bias {B1[k]:+.1f}',
               size=9.2, family=MONO)
        _label(ax, 14.1, y - 0.5, f'sum {SUMS1[k]:+.3f}  ->  output {OUT1[k]:.3f}',
               size=9.8, family=MONO, weight='bold')
        ax.add_patch(plt.Circle((20.8, y), 0.9, facecolor=LINK_PALE if OUT1[k] > 0 else '#eeeeee',
                                edgecolor=LINK if OUT1[k] > 0 else GRIP, lw=1.4, zorder=4))
        _label(ax, 20.8, y, f'{OUT1[k]:.3f}', size=10.5, family=MONO)
        _arrow(ax, (18.4, y), (19.7, y))
        _label(ax, 22.1, y, NEU_JOB[k], size=10, ha='left', color=MUTED)
    _label(ax, 2.6, 1.4, 'the same three\nnumbers go to\nall four neurons', size=10,
           color=MUTED)
    _label(ax, 14.0, -0.3, 'green lines are plus weights and red lines are minus weights; '
           'a thicker line is a bigger weight', size=10, color=MUTED)
    _label(ax, 20.8, 0.9, 'four outputs', size=10.5, weight='bold')
    _save(fig, LAY, 'one-layer-four-neurons.svg')


def layer_arithmetic() -> None:
    """Every product in the layer, written out."""
    fig, ax = plt.subplots(figsize=(12.5, 5.6), facecolor='white')
    _axes(ax, (0, 25), (1.8, 11.4), equal=False)
    _label(ax, 12.5, 10.9, 'All twelve products, and the four answers they make',
           size=13, weight='bold')
    rows = [['', 'distance 0.42', 'opening 0.55', 'brightness 0.30', 'bias', 'sum', 'output']]
    for i in range(4):
        rows.append([f'neuron {i + 1}'] + [f'{X[j] * W1[i, j]:+.3f}' for j in range(3)] +
                    [f'{B1[i]:+.2f}', f'{SUMS1[i]:+.3f}', f'{OUT1[i]:.3f}'])
    _table(ax, 1.2, 10.0, [3.6, 3.8, 3.8, 4.0, 2.6, 3.0, 3.0], rows, row_h=1.25, size=10.5)
    _label(ax, 12.5, 3.3, 'each row is one neuron, and the row adds up left to right; '
           'the last column is the sum after the rule', size=10, color=MUTED)
    _label(ax, 12.5, 2.3, f'neuron 4 is the only one whose sum is below 0, so it is the only '
           f'one whose output is {OUT1[3]:.1f}', size=10.5)
    _save(fig, LAY, 'layer-arithmetic.svg')


def the_weight_grid() -> None:
    """The layer's weights as a grid of 4 rows and 3 columns, plus the bias column."""
    fig, ax = plt.subplots(figsize=(9.6, 5.8), facecolor='white')
    _axes(ax, (0, 16), (0.4, 11.6))
    _label(ax, 8, 11.2, 'The layer owns a grid of weights and one bias for each neuron',
           size=12.5, weight='bold')
    x0, y0, cell = 3.6, 3.0, 1.7
    for j, nm in enumerate(SHORT):
        _label(ax, x0 + j * cell + cell / 2, y0 + 4 * cell + 0.45, nm, size=10, color=MUTED)
    _label(ax, x0 + 3 * cell + 1.0 + cell / 2, y0 + 4 * cell + 0.45, 'bias', size=10,
           color=PURPLE, weight='bold')
    for i in range(4):
        _label(ax, x0 - 0.3, y0 + (3 - i) * cell + cell / 2, f'neuron {i + 1}', size=10.5,
               ha='right')
        for j in range(3):
            w = W1[i, j]
            shade = min(abs(w) / 2.0, 1.0)
            face = (1.0, 1.0 - 0.45 * shade, 1.0 - 0.45 * shade) if w < 0 else \
                   (1.0 - 0.45 * shade, 1.0, 1.0 - 0.45 * shade)
            ax.add_patch(Rectangle((x0 + j * cell, y0 + (3 - i) * cell), cell, cell,
                                   facecolor=face, edgecolor=GRID, lw=0.9, zorder=3))
            _label(ax, x0 + j * cell + cell / 2, y0 + (3 - i) * cell + cell / 2, f'{w:+.1f}',
                   size=11, family=MONO)
        ax.add_patch(Rectangle((x0 + 3 * cell + 1.0, y0 + (3 - i) * cell), cell, cell,
                               facecolor='#ece7f7', edgecolor=GRID, lw=0.9, zorder=3))
        _label(ax, x0 + 3 * cell + 1.0 + cell / 2, y0 + (3 - i) * cell + cell / 2,
               f'{B1[i]:+.1f}', size=11, family=MONO)
    _label(ax, 8, 1.9, f'{W1.shape[0]} neurons x {W1.shape[1]} readings = {W1.size} weights, '
           f'plus {B1.size} biases, so {W1.size + B1.size} parameters', size=11)
    _label(ax, 8, 1.0, 'red is a minus weight and green is a plus one', size=10, color=MUTED)
    _save(fig, LAY, 'the-weight-grid.svg')


def four_features() -> None:
    """The four outputs are four features: four different views of the same moment."""
    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor='white')
    _plain(ax)
    cols = [LINK if v > 0 else '#bbbbbb' for v in OUT1]
    ax.bar(range(4), OUT1, color=cols, edgecolor=INK, lw=0.8, width=0.5)
    for i, (s, o) in enumerate(zip(SUMS1, OUT1)):
        ax.text(i, o + 0.02, f'{o:.3f}', ha='center', va='bottom', fontsize=12, family=MONO)
        ax.text(i, -0.075, f'sum was {s:+.3f}', ha='center', va='top', fontsize=9.5,
                color=MUTED, family=MONO)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f'neuron {i + 1}\n{NEU_JOB[i]}' for i in range(4)], fontsize=9.8)
    ax.set_ylim(-0.2, 0.9)
    ax.axhline(0, color=INK, lw=1.1)
    ax.set_ylabel('the output of this neuron', fontsize=10)
    ax.set_title('Four features: one moment of the grasp described four ways',
                 fontsize=12.5, weight='bold')
    _save(fig, LAY, 'four-features.svg')


# ==========================================================================
# 02_layers-and-depth.md  --  section 2: fully connected, and what it costs
# ==========================================================================

def fully_connected_count() -> None:
    """Every input joined to every neuron: count the lines."""
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4), facecolor='white')
    for ax, (n_in, n_out) in zip(axes, ((3, 4), (6, 8))):
        _axes(ax, (0, 10), (0, 11))
        in_y = np.linspace(2.0, 9.0, n_in)[::-1]
        out_y = np.linspace(1.4, 9.6, n_out)[::-1]
        for yi in in_y:
            for yo in out_y:
                ax.plot([2.6, 7.4], [yi, yo], color=LINK, lw=0.7, alpha=0.45, zorder=2)
        for yi in in_y:
            ax.add_patch(plt.Circle((2.3, yi), 0.42, facecolor=LINK_PALE, edgecolor=LINK,
                                    lw=1.2, zorder=4))
        for yo in out_y:
            ax.add_patch(plt.Circle((7.7, yo), 0.42, facecolor=JOINT, edgecolor=INK, lw=1.0,
                                    zorder=4))
        _label(ax, 2.3, 10.4, f'{n_in} inputs', size=11, weight='bold')
        _label(ax, 7.7, 10.4, f'{n_out} neurons', size=11, weight='bold')
        _label(ax, 5.0, 0.5, f'{n_in} x {n_out} = {n_in * n_out} weights, '
               f'plus {n_out} biases = {n_in * n_out + n_out} parameters', size=11)
    axes[0].set_title('our layer', fontsize=12.5, weight='bold')
    axes[1].set_title('the same idea, a little wider', fontsize=12.5, weight='bold')
    print('--- fully connected counts --------------------------------------')
    for n_in, n_out in ((3, 4), (6, 8), (1024, 1024)):
        print(f'  {n_in} inputs into {n_out} neurons: {n_in * n_out:,} weights + '
              f'{n_out:,} biases = {n_in * n_out + n_out:,} parameters')
    _save(fig, LAY, 'fully-connected-count.svg')


def parameters_against_width() -> None:
    """How the parameter count of one fully connected layer grows with its width."""
    widths = np.array([16, 32, 64, 128, 256, 512, 1024, 2048, 4096])
    n_in = 1024
    params = widths * n_in + widths
    print('--- one layer with 1024 inputs ----------------------------------')
    for w, p in zip(widths, params):
        print(f'  width {w:5d}: {p:,} parameters, {p * 4 / 1e6:.2f} MB at 4 bytes each')
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(widths, params, marker='o', color=LINK, lw=2.4, ms=7)
    for w, p in zip(widths, params):
        if w in (16, 256, 4096):
            ax.annotate(f'{p:,}', xy=(w, p), xytext=(16, -20), textcoords='offset points',
                        fontsize=10, ha='center',
                        arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths], fontsize=9.5)
    ax.set_xlabel('how many neurons the layer has (its width)', fontsize=10)
    ax.set_ylabel('parameters in that one layer', fontsize=10)
    ax.set_title('One layer reading 1,024 numbers: doubling the width doubles its parameters',
                 fontsize=12, weight='bold')
    _save(fig, LAY, 'parameters-against-width.svg')


def local_versus_full() -> None:
    """Joining every input to every neuron is not the only choice."""
    n = 16
    full = n * n + n
    local = n * 3 + n
    print('--- joining everything, or only neighbours ----------------------')
    print(f'  {n} inputs into {n} neurons, all joined: {full:,} parameters')
    print(f'  the same, each neuron reading only its 3 neighbours: {local:,} parameters, '
          f'which is {full / local:.1f} times fewer')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.6), facecolor='white')
    for ax, mode in zip(axes, ('full', 'local')):
        _axes(ax, (0, 18), (0, 11))
        in_x = np.linspace(1.0, 17.0, n)
        for i, xi in enumerate(in_x):
            ax.add_patch(plt.Circle((xi, 8.4), 0.42, facecolor=LINK_PALE, edgecolor=LINK,
                                    lw=1.1, zorder=4))
            ax.add_patch(plt.Circle((xi, 3.0), 0.42, facecolor=JOINT, edgecolor=INK,
                                    lw=1.0, zorder=4))
        for k in range(n):
            reads = range(n) if mode == 'full' else [j for j in (k - 1, k, k + 1)
                                                     if 0 <= j < n]
            for j in reads:
                ax.plot([in_x[j], in_x[k]], [8.0, 3.4], color=LINK,
                        lw=0.5 if mode == 'full' else 1.2,
                        alpha=0.25 if mode == 'full' else 0.9, zorder=2)
        _label(ax, 9.0, 9.8, '16 numbers going in', size=11, weight='bold')
        _label(ax, 9.0, 1.6, '16 neurons', size=11, weight='bold')
        count = full if mode == 'full' else local
        _label(ax, 9.0, 0.5, f'{count:,} parameters', size=12, weight='bold',
               color=LINK if mode == 'full' else SLIDE)
        ax.set_title('every neuron reads every input' if mode == 'full'
                     else 'every neuron reads only its three neighbours',
                     fontsize=12, weight='bold')
    _save(fig, LAY, 'local-versus-full.svg')


# ==========================================================================
# 02_layers-and-depth.md  --  section 3: what each extra layer buys you
# ==========================================================================

def _corners(x: Arr, y: Arr) -> Arr:
    """Where the line changes direction, counting each corner once."""
    sl = np.diff(y) / np.diff(x)
    tol = 1e-6 * (float(np.max(np.abs(sl))) + 1.0)
    idx = np.where(np.abs(np.diff(sl)) > tol)[0]
    keep = [i for n, i in enumerate(idx) if n == 0 or i - idx[n - 1] > 2]
    return x[np.array(keep, dtype=int) + 1] if keep else np.array([])


def _bends(x: Arr, y: Arr) -> int:
    """How many places the line changes direction."""
    return len(_corners(x, y))


def one_layer_two_bends() -> None:
    """One layer of two neurons: two elbows, so three straight pieces."""
    b = np.linspace(0.0, 1.0, 4001)
    a1, a2 = relu(3.0 * b - 0.9), relu(3.0 * b - 2.1)
    out = 2.5 * a1 - 5.0 * a2
    n = _bends(b, out)
    print('--- one layer of two neurons ------------------------------------')
    print(f'  elbows at 0.300 and 0.700, so the line has {n} bends and {n + 1} '
          f'straight pieces; the top is {float(out.max()):.3f}')
    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(b, a1, color=LINK, lw=1.8, ls=':', label='neuron A: rule(3.0 x brightness - 0.9)')
    ax.plot(b, a2, color=SLIDE, lw=1.8, ls=':', label='neuron B: rule(3.0 x brightness - 2.1)')
    ax.plot(b, out, color=GRIP, lw=2.8, label='2.5 x A - 5.0 x B')
    for k in (0.3, 0.7):
        ax.axvline(k, color=MUTED, lw=0.9, ls='--')
    ax.set_xlabel('patch brightness / 255', fontsize=10)
    ax.set_ylabel('what the layer gives', fontsize=10)
    ax.set_title(f'One layer, two neurons: {n} bends and {n + 1} straight pieces',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.6, frameon=False, loc='upper left')
    ax.set_ylim(-0.3, 3.4)
    _save(fig, LAY, 'one-layer-two-bends.svg')


def two_layers_more_bends() -> None:
    """A second layer bends the bends: four elbows out of the same two neurons."""
    b = np.linspace(0.0, 1.0, 8001)
    a1, a2 = relu(3.0 * b - 0.9), relu(3.0 * b - 2.1)
    one = 2.5 * a1 - 5.0 * a2
    c1 = relu(0.8 * a1 - 1.6 * a2 - 0.4)
    c2 = relu(0.5 * a2 - 0.1)
    two = c1 + c2
    n1, n2 = _bends(b, one), _bends(b, two)
    corners = _corners(b, two)
    print('--- a second layer ----------------------------------------------')
    print(f'  one layer: {n1} bends; two layers of the same two neurons: {n2} bends')
    print('  the two-layer bends sit at ' + ', '.join(f'{c:.3f}' for c in corners))
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    for ax in axes:
        _plain(ax)
        ax.set_xlabel('patch brightness / 255', fontsize=10)
        ax.set_ylim(-0.15, 1.5)
    axes[0].plot(b, c1, color=LINK, lw=2.2, label='second-layer neuron C')
    axes[0].plot(b, c2, color=SLIDE, lw=2.2, label='second-layer neuron D')
    axes[0].set_ylabel('what each second-layer neuron gives', fontsize=10)
    axes[0].set_title('the second layer reads A and B, not the brightness',
                      fontsize=12, weight='bold')
    axes[0].legend(fontsize=9.8, frameon=False, loc='upper left')
    axes[1].plot(b, two, color=GRIP, lw=2.8, label=f'two layers: {n2} bends')
    axes[1].plot(b, one / 3.0, color=MUTED, lw=1.6, ls='--',
                 label=f'one layer: {n1} bends (scaled to fit)')
    for c in corners:
        axes[1].axvline(c, color=MUTED, lw=0.8, ls=':')
    axes[1].set_ylabel('what the whole network gives', fontsize=10)
    axes[1].set_title(f'the same two neurons, used twice, make {n2} bends',
                      fontsize=12, weight='bold')
    axes[1].legend(fontsize=9.8, frameon=False, loc='upper left')
    _save(fig, LAY, 'two-layers-more-bends.svg')


def _corr3(img: Arr, k: Arr) -> Arr:
    """Slide a 3 by 3 group of weights over a picture, keeping the same size."""
    pad = np.pad(img, 1)
    out = np.zeros_like(img)
    for r in range(img.shape[0]):
        for c in range(img.shape[1]):
            out[r, c] = float(np.sum(pad[r:r + 3, c:c + 3] * k))
    return out


def _mug() -> Arr:
    pic = np.zeros((14, 14))
    pic[3:11, 2:8] = 1.0      # the body, six columns wide
    pic[5:8, 9:12] = 1.0      # the handle, three columns wide
    return pic


VERT: Arr = np.array([[-1.0, 0.0, 1.0]] * 3)
HORZ: Arr = VERT.T


def _draw_map(ax: Axes, a: Arr, title: str, cmap: str, vmin: float, vmax: float,
              marks: list[tuple[int, int]] | None = None, numbers: bool = True) -> None:
    n_r, n_c = a.shape
    _axes(ax, (-0.5, n_c + 0.5), (-0.5, n_r + 0.5))
    for r in range(n_r):
        for c in range(n_c):
            v = float(a[r, c])
            face = plt.get_cmap(cmap)((v - vmin) / (vmax - vmin))
            ax.add_patch(Rectangle((c, n_r - 1 - r), 1, 1, facecolor=face, edgecolor=GRID,
                                   lw=0.5, zorder=3))
            if numbers and v != 0:
                ax.text(c + 0.5, n_r - 1 - r + 0.5, f'{v:.0f}', ha='center', va='center',
                        fontsize=7.5, color=INK, zorder=5)
    if marks:
        for r, c in marks:
            ax.add_patch(Rectangle((c, n_r - 1 - r), 1, 1, facecolor='none', edgecolor=GRIP,
                                   lw=2.4, zorder=6))
    ax.set_title(title, fontsize=11.5, weight='bold')


def edges_first() -> None:
    """Stage one: small groups of weights that answer where an edge is."""
    pic = _mug()
    v = _corr3(pic, VERT)
    h = _corr3(pic, HORZ)
    print('--- stage one: edges --------------------------------------------')
    print(f'  the picture is {pic.shape[0]} by {pic.shape[1]}, with a six-wide body and a '
          f'three-wide handle')
    print(f'  the up-and-down edge filter runs from {float(v.min()):+.0f} to '
          f'{float(v.max()):+.0f}; it is positive in columns '
          f'{sorted(set(np.where(v > 0)[1].tolist()))} (dark then bright) and negative in '
          f'{sorted(set(np.where(v < 0)[1].tolist()))} (bright then dark)')
    print(f'  the side-to-side edge filter runs from {float(h.min()):+.0f} to '
          f'{float(h.max()):+.0f}, and it answers on rows '
          f'{sorted(set(np.where(h != 0)[0].tolist()))}')
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 5.2), facecolor='white')
    _draw_map(axes[0], pic, 'the picture: a cup with a handle', 'Greys', 0.0, 1.3,
              numbers=False)
    _draw_map(axes[1], v, 'filter 1: up-and-down edges', 'RdYlBu', -3.5, 3.5)
    _draw_map(axes[2], h, 'filter 2: side-to-side edges', 'RdYlBu', -3.5, 3.5)
    fig.suptitle('Stage one: nine weights slid over the picture answer "is there an edge here"',
                 fontsize=13, weight='bold')
    _save(fig, LAY, 'edges-first.svg')


def shapes_then_parts() -> None:
    """Stage two and three: corners out of edges, then a handle out of corners."""
    pic = _mug()
    v, h = _corr3(pic, VERT), _corr3(pic, HORZ)
    corner = np.minimum(np.abs(v), np.abs(h))
    bar = np.zeros_like(v)
    vpos, vneg = np.maximum(v, 0.0), np.maximum(-v, 0.0)
    gap = 2
    bar[:, :-gap] = np.minimum(vpos[:, :-gap], vneg[:, gap:])
    corner_spots = [(int(r), int(c)) for r, c in zip(*np.where(corner >= 2))]
    bar_spots = [(int(r), int(c)) for r, c in zip(*np.where(bar > 0))]
    print('--- stage two and three: shapes and parts -----------------------')
    print(f'  the corner answer is above 2 at {len(corner_spots)} places, all of them at the '
          f'ends of the two shapes: {corner_spots}')
    print(f'  the "bright bar three wide" answer fires at {len(bar_spots)} places, '
          f'all in the handle: {bar_spots}')
    print(f'  it never fires on the body, because the body is six wide')
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 5.2), facecolor='white')
    _draw_map(axes[0], pic, 'the picture again', 'Greys', 0.0, 1.3, numbers=False)
    _draw_map(axes[1], corner, 'stage two: a corner', 'YlOrRd', 0.0, 4.0,
              marks=corner_spots)
    _draw_map(axes[2], bar, 'stage three: a bar three wide', 'YlGnBu',
              0.0, 4.0, marks=bar_spots)
    fig.suptitle('Stages two and three are built out of stage one, not out of the picture',
                 fontsize=13, weight='bold')
    _save(fig, LAY, 'shapes-then-parts.svg')


# ==========================================================================
# 02_layers-and-depth.md  --  section 4: depth and width
# ==========================================================================

def _pieces(depth: int, width: int, seed: int, n: int = 6001) -> tuple[int, Arr, Arr, int]:
    """Count the straight pieces a random network of this shape makes on one sweep."""
    rng = np.random.default_rng(seed)
    x = np.linspace(-1.0, 1.0, n)
    h = x[:, None]
    breaks = 0
    params = 0
    for _ in range(depth):
        fan_in = h.shape[1]
        w = rng.normal(0.0, math.sqrt(2.0 / fan_in), size=(fan_in, width))
        bb = rng.normal(0.0, 0.5, size=width)
        z = h @ w + bb
        breaks += int(np.sum(np.diff(np.sign(z), axis=0) != 0))
        params += fan_in * width + width
        h = relu(z)
    w_out = rng.normal(0.0, math.sqrt(2.0 / width), size=(width, 1))
    params += width + 1
    y = (h @ w_out)[:, 0]
    return breaks + 1, x, y, params


def _mean_pieces(depth: int, width: int, seeds: int = 5) -> float:
    return float(np.mean([_pieces(depth, width, 100 + s)[0] for s in range(seeds)]))


def pieces_by_depth() -> None:
    """More layers of the same width make many more straight pieces."""
    depths = [1, 2, 3, 4, 5]
    vals = [_mean_pieces(d, 8) for d in depths]
    print('--- straight pieces against depth (width 8, 5 seeds) ------------')
    for d, v in zip(depths, vals):
        print(f'  depth {d}: {v:.1f} pieces on average')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar([str(d) for d in depths], vals, color=LINK, edgecolor=INK, lw=0.8, width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.6, f'{v:.1f}', ha='center', fontsize=11, family=MONO)
    ax.set_xlabel('how many layers (the depth)', fontsize=10)
    ax.set_ylabel('straight pieces in the answer', fontsize=10)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title('Width 8, counted on a sweep of 6,001 points', fontsize=12, weight='bold')
    ax = axes[1]
    _plain(ax)
    for d, col in zip((1, 3), (SLIDE, GRIP)):
        n_p, x, y, params = _pieces(d, 8, 100)
        ax.plot(x, y / np.max(np.abs(y)), color=col, lw=2.2,
                label=f'{d} layer{"s" if d > 1 else ""}: {n_p} pieces, {params} parameters')
    ax.set_xlabel('one reading, swept from -1 to +1', fontsize=10)
    ax.set_ylabel('the answer, scaled to fit', fontsize=10)
    ax.set_ylim(-1.2, 0.35)
    ax.set_title('The same width, one layer and three layers', fontsize=12, weight='bold')
    ax.legend(fontsize=9.6, frameon=False, loc='upper left')
    _save(fig, LAY, 'pieces-by-depth.svg')


def pieces_by_width() -> None:
    """More neurons in one layer also make more pieces, but one at a time."""
    widths = [2, 4, 8, 16, 32, 64]
    one = [_mean_pieces(1, w) for w in widths]
    two = [_mean_pieces(2, w) for w in widths]
    print('--- straight pieces against width (5 seeds) ---------------------')
    for w, a, b in zip(widths, one, two):
        print(f'  width {w:3d}: one layer {a:6.1f} pieces, two layers {b:6.1f} pieces')
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(widths, one, marker='o', color=SLIDE, lw=2.2, ms=7, label='one layer')
    ax.plot(widths, two, marker='s', color=GRIP, lw=2.2, ms=7, label='two layers')
    for w, a in zip(widths, one):
        ax.annotate(f'{a:.0f}', xy=(w, a), xytext=(0, -16), textcoords='offset points',
                    fontsize=9.5, ha='center', color=SLIDE)
    for w, b in zip(widths, two):
        ax.annotate(f'{b:.0f}', xy=(w, b), xytext=(0, 10), textcoords='offset points',
                    fontsize=9.5, ha='center', color=GRIP)
    ax.set_xscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths])
    ax.minorticks_off()
    ax.set_xlabel('neurons in each layer (the width)', fontsize=10)
    ax.set_ylabel('straight pieces in the answer', fontsize=10)
    ax.set_title('Pieces climb with the width, and a second layer of the same width adds more',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, LAY, 'pieces-by-width.svg')


def depth_width_grid() -> None:
    """Pieces for every mixture of depth and width."""
    depths, widths = [1, 2, 3, 4], [4, 8, 16, 32]
    grid = np.array([[_mean_pieces(d, w) for w in widths] for d in depths])
    print('--- pieces for every depth and width ----------------------------')
    for i, d in enumerate(depths):
        print(f'  depth {d}: ' + '  '.join(f'w{w}={grid[i, j]:7.1f}'
                                           for j, w in enumerate(widths)))
    neurons = np.array([[d * w for w in widths] for d in depths], dtype=float)
    slope = float(np.sum(neurons * grid) / np.sum(neurons * neurons))
    print(f'  pieces against total neurons: one straight line through 0 with slope '
          f'{slope:.3f} fits all sixteen shapes')
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), facecolor='white')
    ax = axes[0]
    im = ax.imshow(np.log10(grid), cmap='YlGnBu', aspect='auto')
    for i in range(len(depths)):
        for j in range(len(widths)):
            ax.text(j, i, f'{grid[i, j]:.0f}', ha='center', va='center', fontsize=12,
                    color='white' if np.log10(grid[i, j]) > 1.6 else INK, family=MONO)
    ax.set_xticks(range(len(widths)))
    ax.set_xticklabels([str(w) for w in widths], fontsize=10)
    ax.set_yticks(range(len(depths)))
    ax.set_yticklabels([str(d) for d in depths], fontsize=10)
    ax.set_xlabel('width: neurons in each layer', fontsize=10)
    ax.set_ylabel('depth: how many layers', fontsize=10)
    ax.set_title('Pieces made, averaged over five random networks',
                 fontsize=12, weight='bold')
    fig.colorbar(im, ax=ax, label='pieces (log scale)', shrink=0.85)
    ax = axes[1]
    _plain(ax)
    for i, d in enumerate(depths):
        ax.plot(neurons[i], grid[i], 'o', ms=8, color=[LINK, SLIDE, JOINT, GRIP][i],
                label=f'depth {d}')
    line_x = np.array([0.0, float(neurons.max()) * 1.05])
    ax.plot(line_x, slope * line_x, color=MUTED, lw=1.6, ls='--',
            label=f'one line through 0, slope {slope:.2f}')
    ax.set_xlabel('neurons in the whole network (depth x width)', fontsize=10)
    ax.set_ylabel('straight pieces in the answer', fontsize=10)
    ax.set_title('Pieces follow the total number of neurons, however they are arranged',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.6, frameon=False, loc='upper left')
    _save(fig, LAY, 'depth-width-grid.svg')


def deep_narrow_wide_shallow() -> None:
    """Two networks with similar parameter counts: one deep and thin, one wide and flat."""
    deep_n, x, deep_y, deep_p = _pieces(4, 8, 202)
    wide_n, _, wide_y, wide_p = _pieces(1, 64, 202)
    print('--- deep and thin against wide and flat -------------------------')
    print(f'  4 layers of 8: {deep_p} parameters, {deep_n} pieces')
    print(f'  1 layer of 64: {wide_p} parameters, {wide_n} pieces')
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(x, deep_y / np.max(np.abs(deep_y)), color=GRIP, lw=2.2,
            label=f'4 layers of 8 neurons: {deep_p} parameters, {deep_n} pieces')
    ax.plot(x, wide_y / np.max(np.abs(wide_y)), color=LINK, lw=2.2,
            label=f'1 layer of 64 neurons: {wide_p} parameters, {wide_n} pieces')
    ax.set_xlabel('one reading, swept from -1 to +1', fontsize=10)
    ax.set_ylabel('the answer, scaled to fit', fontsize=10)
    ax.set_ylim(-1.5, 1.15)
    ax.set_title('Similar numbers of parameters, different amounts of detail',
                 fontsize=12.5, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='lower center')
    _save(fig, LAY, 'deep-narrow-wide-shallow.svg')


# ==========================================================================
# 02_layers-and-depth.md  --  section 5: what depth and width cost
# ==========================================================================

def _stack_params(depth: int, width: int) -> int:
    return depth * (width * width + width)


def _stack_mults(depth: int, width: int) -> int:
    return depth * width * width


def parameters_and_memory() -> None:
    """Parameter counts for a stack of equal layers, and what they weigh in memory."""
    depths, widths = [2, 4, 8, 16], [256, 512, 1024, 2048]
    grid = np.array([[_stack_params(d, w) for w in widths] for d in depths], dtype=float)
    print('--- parameters in a stack of equal layers -----------------------')
    for i, d in enumerate(depths):
        print(f'  depth {d:2d}: ' + '  '.join(
            f'w{w}={int(grid[i, j]):,} ({grid[i, j] * 4 / 1e6:.1f} MB)'
            for j, w in enumerate(widths)))
    fig, ax = plt.subplots(figsize=(10.5, 5.6), facecolor='white')
    im = ax.imshow(np.log10(grid), cmap='YlOrRd', aspect='auto')
    for i in range(len(depths)):
        for j in range(len(widths)):
            ax.text(j, i + 0.12, f'{grid[i, j] / 1e6:.1f}M', ha='center', va='center',
                    fontsize=12.5, family=MONO,
                    color='white' if np.log10(grid[i, j]) > 6.6 else INK)
            mb = grid[i, j] * 4 / 1e6
            ax.text(j, i - 0.22, f'{mb:.1f} MB' if mb < 10 else f'{mb:.0f} MB',
                    ha='center', va='center',
                    fontsize=9.5, color='white' if np.log10(grid[i, j]) > 6.6 else MUTED)
    ax.set_xticks(range(len(widths)))
    ax.set_xticklabels([str(w) for w in widths], fontsize=10)
    ax.set_yticks(range(len(depths)))
    ax.set_yticklabels([str(d) for d in depths], fontsize=10)
    ax.set_xlabel('width: neurons in each layer', fontsize=10)
    ax.set_ylabel('depth: how many layers', fontsize=10)
    ax.set_title('Parameters in the stack, and what they weigh at 4 bytes each',
                 fontsize=12.5, weight='bold')
    fig.colorbar(im, ax=ax, label='parameters (log scale)', shrink=0.85)
    _save(fig, LAY, 'parameters-and-memory.svg')


def multiply_adds() -> None:
    """The multiply-adds one example costs, as the width and the depth change."""
    widths = np.array([128, 256, 512, 1024, 2048, 4096])
    depths = np.array([1, 2, 4, 8, 16, 32])
    by_width = np.array([_stack_mults(8, int(w)) for w in widths], dtype=float)
    by_depth = np.array([_stack_mults(int(d), 1024) for d in depths], dtype=float)
    print('--- multiply-adds for one example -------------------------------')
    for w, m in zip(widths, by_width):
        print(f'  depth 8, width {w:5d}: {int(m):,} multiply-adds')
    for d, m in zip(depths, by_depth):
        print(f'  width 1024, depth {d:2d}: {int(m):,} multiply-adds')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(widths, by_width, marker='o', color=LINK, lw=2.4, ms=7)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths], fontsize=9)
    ax.minorticks_off()
    ax.set_xlabel('width, with the depth held at 8', fontsize=10)
    ax.set_ylabel('multiply-adds for one example', fontsize=10)
    ax.set_title('Doubling the width multiplies the work by 4', fontsize=12, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(depths, by_depth, marker='s', color=GRIP, lw=2.4, ms=7)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(depths)
    ax.set_xticklabels([str(d) for d in depths], fontsize=9)
    ax.minorticks_off()
    ax.set_xlabel('depth, with the width held at 1024', fontsize=10)
    ax.set_ylabel('multiply-adds for one example', fontsize=10)
    ax.set_title('Doubling the depth multiplies the work by 2', fontsize=12, weight='bold')
    _save(fig, LAY, 'multiply-adds.svg')


def what_doubling_costs() -> None:
    """The same stack, then twice as wide, then twice as deep."""
    rows_in = [('8 layers of 1024', 8, 1024), ('8 layers of 2048', 8, 2048),
               ('16 layers of 1024', 16, 1024)]
    base_p = _stack_params(8, 1024)
    base_m = _stack_mults(8, 1024)
    print('--- what doubling costs -----------------------------------------')
    for nm, d, w in rows_in:
        p, m = _stack_params(d, w), _stack_mults(d, w)
        print(f'  {nm:18s} {p:>12,} parameters ({p / base_p:.1f}x), '
              f'{m:>12,} multiply-adds ({m / base_m:.1f}x), {p * 4 / 1e6:.1f} MB')
    fig, ax = plt.subplots(figsize=(12.5, 4.8), facecolor='white')
    _axes(ax, (0, 25), (0.4, 9.6), equal=False)
    _label(ax, 12.5, 9.1, 'Doubling the width costs four times as much; doubling the depth, '
           'twice', size=13, weight='bold')
    rows = [['the stack', 'parameters', 'times the first', 'multiply-adds', 'memory']]
    for nm, d, w in rows_in:
        p, m = _stack_params(d, w), _stack_mults(d, w)
        rows.append([nm, f'{p:,}', f'{p / base_p:.1f}x', f'{m:,}', f'{p * 4 / 1e6:.1f} MB'])
    _table(ax, 1.0, 8.2, [5.0, 5.2, 4.2, 5.4, 3.6], rows, row_h=1.3, size=10.5)
    _label(ax, 12.0, 1.9, 'each layer here takes its own width in and gives its own width out, '
           'and the memory is at 4 bytes for each number', size=10, color=MUTED)
    _save(fig, LAY, 'what-doubling-costs.svg')


def work_for_many_examples() -> None:
    """The same stack, used on one reading, on a batch, and on a whole set of examples."""
    per_example = _stack_mults(8, 1024)
    jobs = [('one moment of one grasp', 1), ('32 moments at once', 32),
            ('10,000 moments', 10_000)]
    print('--- the work for more than one example --------------------------')
    for nm, k in jobs:
        print(f'  {nm:24s} {per_example * k:>18,} multiply-adds')
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    vals = [per_example * k for _, k in jobs]
    ax.bar([nm for nm, _ in jobs], vals, color=[LINK, JOINT, PURPLE], edgecolor=INK,
           lw=0.8, width=0.5)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.4, f'{v:,}', ha='center', fontsize=11, family=MONO)
    ax.set_yscale('log')
    ax.set_ylim(1e6, 1e12)
    ax.set_ylabel('multiply-adds through 8 layers of 1024', fontsize=10)
    ax.set_title('The work grows with the examples as well as with the shape',
                 fontsize=12.5, weight='bold')
    ax.set_xlabel('how many readings go through the stack', fontsize=10)
    _save(fig, LAY, 'work-for-many-examples.svg')


# ==========================================================================
# 02_layers-and-depth.md  --  section 6: residual connections
# ==========================================================================

W2: Arr = np.array([[0.2, -0.3, 0.1, 0.0],
                    [0.0, 0.4, -0.2, 0.1],
                    [-0.1, 0.1, 0.3, 0.2],
                    [0.3, 0.0, -0.1, 0.1]])
B2: Arr = np.array([0.05, -0.10, 0.00, 0.02])


def residual_block_numbers() -> None:
    """One residual block worked out on the four numbers the first layer gave."""
    x = OUT1
    inner = W2 @ x + B2
    f = relu(inner)
    out = x + f
    print('--- one residual block ------------------------------------------')
    print('  going in:      ' + '  '.join(f'{v:6.3f}' for v in x))
    print('  the block says:' + '  '.join(f'{v:6.3f}' for v in f))
    print('  added back:    ' + '  '.join(f'{v:6.3f}' for v in out))
    fig, ax = plt.subplots(figsize=(13.5, 5.4), facecolor='white')
    _axes(ax, (0, 28), (0, 12.0))
    _label(ax, 14, 11.6, 'A residual block: work something out, then add it to what came in',
           size=13, weight='bold')
    ys = [8.4, 6.6, 4.8, 3.0]
    for k, y in enumerate(ys):
        ax.add_patch(plt.Circle((2.0, y), 0.62, facecolor=LINK_PALE, edgecolor=LINK, lw=1.2,
                                zorder=4))
        _label(ax, 2.0, y, f'{x[k]:.3f}', size=9.5, family=MONO)
        ax.add_patch(plt.Circle((13.2, y), 0.62, facecolor='#ede8f8', edgecolor=PURPLE, lw=1.2,
                                zorder=4))
        _label(ax, 13.2, y, f'{f[k]:.3f}', size=9.5, family=MONO)
        ax.add_patch(plt.Circle((21.0, y), 0.72, facecolor=JOINT, edgecolor=INK, lw=1.2,
                                zorder=4))
        _label(ax, 21.0, y, f'{out[k]:.3f}', size=9.5, family=MONO)
        ax.plot([2.7, 5.4], [y, y], color=MUTED, lw=1.1, zorder=2)
        _arrow(ax, (13.9, y), (20.2, y), color=PURPLE, lw=1.4)
        _label(ax, 17.0, y + 0.42, f'{x[k]:.3f} + {f[k]:.3f}', size=9, color=MUTED, family=MONO)
    _box(ax, 5.6, 2.2, 7.0, 7.0, face='white', edge=PURPLE)
    _label(ax, 9.1, 8.6, 'the block', size=11, weight='bold', color=PURPLE)
    _label(ax, 9.1, 7.4, 'a layer of four neurons:\nmultiply by its weights,\nadd its bias,\n'
           'then the rule', size=10)
    _label(ax, 9.1, 4.3, 'it gives four numbers,\nnone of them below 0', size=9.6, color=MUTED)
    _arrow(ax, (2.0, 9.2), (2.0, 10.0), color=LINK, lw=1.6)
    ax.plot([2.0, 21.0], [10.0, 10.0], color=LINK, lw=1.6, zorder=2)
    _arrow(ax, (21.0, 10.0), (21.0, 9.4), color=LINK, lw=1.6)
    _label(ax, 11.5, 10.5, 'the short way round: the four numbers go straight to the end',
           size=10.5, color=LINK)
    _label(ax, 21.0, 1.8, 'what comes out', size=10.5, weight='bold')
    _label(ax, 2.0, 1.8, 'what went in', size=10.5, weight='bold')
    _label(ax, 14, 0.6, 'the block never replaces the four numbers; it only adds to them',
           size=10.5, color=MUTED)
    _save(fig, LAY, 'residual-block-numbers.svg')


def _stacks(n_layers: int = 30, n: int = 64, scale: float = 0.8,
            seed: int = 11) -> tuple[float, Arr, Arr]:
    """Push one set of numbers through a plain stack and a residual stack of the same layers.

    Returns the size of the numbers that went in, and their typical size after every
    layer of each stack.
    """
    rng = np.random.default_rng(seed)
    mats = [rng.normal(0.0, scale * math.sqrt(2.0 / n), size=(n, n)) for _ in range(n_layers)]
    start = np.abs(rng.normal(0.0, 1.0, size=n))
    plain, res = start.copy(), start.copy()
    size_p, size_r = [], []
    for mat in mats:
        plain = relu(mat @ plain)
        res = res + relu(mat @ res)
        size_p.append(float(np.sqrt(np.mean(plain ** 2))))
        size_r.append(float(np.sqrt(np.mean(res ** 2))))
    return float(np.sqrt(np.mean(start ** 2))), np.array(size_p), np.array(size_r)


def signal_through_30_layers() -> None:
    """Thirty layers at two weight sizes: the plain stack fades, the residual stack does not."""
    print('--- thirty layers -----------------------------------------------')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    layers = np.arange(1, 31)
    for ax, scale in zip(axes, (0.6, 0.9)):
        start, sp, sr = _stacks(scale=scale)
        print(f'  weights {scale:.1f} of the size that would hold steady: the numbers go in '
              f'at {start:.3f}; after 30 plain layers they are {sp[-1]:.2e}, and after 30 '
              f'residual layers {sr[-1]:.2e}')
        _plain(ax)
        ax.axhline(start, color=MUTED, lw=1.2, ls=':')
        ax.plot(layers, sp, color=GRIP, lw=2.4, label='plain stack')
        ax.plot(layers, sr, color=SLIDE, lw=2.4, label='residual stack')
        ax.set_yscale('log')
        ax.set_ylim(1e-9, 1e7)
        ax.set_xlabel('layer number', fontsize=10)
        ax.set_ylabel('typical size of the numbers', fontsize=10)
        ax.set_title(f'block weights {scale:.1f} times the steady size', fontsize=12,
                     weight='bold')
        ax.legend(fontsize=10, frameon=False, loc='lower left')
        _label(ax, 15, start * 2.2, 'the size that went in', size=9.5, color=MUTED)
    fig.suptitle('Thirty layers: the plain stack fades to nothing, and the residual stack '
                 'never does', fontsize=13, weight='bold')
    _save(fig, LAY, 'signal-through-30-layers.svg')


def residual_numbers_table() -> None:
    """The same two stacks, as numbers at five depths."""
    start, sp6, sr6 = _stacks(scale=0.6)
    _, sp9, sr9 = _stacks(scale=0.9)
    picks = [1, 5, 10, 20, 30]
    print('--- the two stacks at five depths -------------------------------')
    for p in picks:
        print(f'  after layer {p:2d}: plain {sp6[p - 1]:.2e} / {sp9[p - 1]:.2e}, '
              f'residual {sr6[p - 1]:.2e} / {sr9[p - 1]:.2e}')
    fig, ax = plt.subplots(figsize=(12.5, 5.0), facecolor='white')
    _axes(ax, (0, 25), (0.2, 10.0), equal=False)
    _label(ax, 12.5, 9.5, 'The typical size of the numbers, read off at five depths',
           size=13, weight='bold')
    rows = [['after layer', 'plain,\nweights 0.6', 'residual,\nweights 0.6',
             'plain,\nweights 0.9', 'residual,\nweights 0.9']]
    for p in picks:
        rows.append([str(p), f'{sp6[p - 1]:.2e}', f'{sr6[p - 1]:.2e}',
                     f'{sp9[p - 1]:.2e}', f'{sr9[p - 1]:.2e}'])
    _table(ax, 2.0, 8.6, [4.0, 4.6, 4.8, 4.6, 4.8], rows, row_h=1.2, size=10.5)
    _label(ax, 12.5, 0.8, f'the numbers going in had a typical size of {start:.3f}, and '
           f'2.0e-03 means 0.002', size=10, color=MUTED)
    _save(fig, LAY, 'residual-numbers-table.svg')


def quiet_block_does_nothing() -> None:
    """A block with tiny weights changes almost nothing, which is why adding one is safe."""
    rng = np.random.default_rng(23)
    n = 64
    x = np.abs(rng.normal(0.0, 1.0, size=n))
    tiny = rng.normal(0.0, 0.01 * math.sqrt(2.0 / n), size=(n, n))
    res_out = x + relu(tiny @ x)
    plain_out = relu(tiny @ x)
    res_gap = float(np.max(np.abs(res_out - x)))
    plain_size = float(np.sqrt(np.mean(plain_out ** 2)))
    x_size = float(np.sqrt(np.mean(x ** 2)))
    print('--- a quiet block -----------------------------------------------')
    print(f'  with weights a hundred times smaller than usual, the residual block changes '
          f'no number by more than {res_gap:.5f}')
    print(f'  the same weights in a plain layer shrink the typical size from {x_size:.3f} '
          f'to {plain_size:.5f}')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    idx = np.arange(12)
    ax = axes[0]
    _plain(ax)
    ax.bar(idx - 0.2, x[:12], width=0.4, color=LINK, edgecolor=INK, lw=0.6,
           label='what went in')
    ax.bar(idx + 0.2, res_out[:12], width=0.4, color=SLIDE, edgecolor=INK, lw=0.6,
           label='after a quiet residual block')
    ax.set_xlabel('the first twelve of the 64 numbers', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title(f'Nothing moves by more than {res_gap:.5f}', fontsize=12, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    ax = axes[1]
    _plain(ax)
    ax.bar(idx - 0.2, x[:12], width=0.4, color=LINK, edgecolor=INK, lw=0.6,
           label='what went in')
    ax.bar(idx + 0.2, plain_out[:12], width=0.4, color=GRIP, edgecolor=INK, lw=0.6,
           label='after a quiet plain layer')
    ax.set_xlabel('the first twelve of the 64 numbers', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title(f'The same weights without the add: {x_size:.2f} becomes {plain_size:.5f}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    _save(fig, LAY, 'quiet-block-does-nothing.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    report_core()
    neuron_parts()
    scaling_the_readings()
    the_four_parameters()
    weighted_sum_lines()
    contribution_bars()
    sum_against_distance()
    sum_over_two_readings()
    flipping_one_weight()
    weight_size_lines()
    moving_the_bias()
    two_plain_layers()
    collapse_curves()
    three_plain_layers()
    a_bend_is_needed()
    relu_curve()
    relu_pieces()
    relu_dead_units()
    relu_slope()
    three_rules()
    three_slopes()
    neuron_three_rules()
    activation_cost()
    report_layer()
    one_layer_four_neurons()
    layer_arithmetic()
    the_weight_grid()
    four_features()
    fully_connected_count()
    parameters_against_width()
    local_versus_full()
    one_layer_two_bends()
    two_layers_more_bends()
    edges_first()
    shapes_then_parts()
    pieces_by_depth()
    pieces_by_width()
    depth_width_grid()
    deep_narrow_wide_shallow()
    parameters_and_memory()
    multiply_adds()
    what_doubling_costs()
    work_for_many_examples()
    residual_block_numbers()
    signal_through_30_layers()
    residual_numbers_table()
    quiet_block_does_nothing()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
