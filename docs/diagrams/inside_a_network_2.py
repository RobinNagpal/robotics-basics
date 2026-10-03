"""Generate the diagrams for the last two pages of docs/06_neural-networks/02_inside-a-network/.

    03_the-shape-of-the-numbers.md  -> images/inside-a-network/the-shape-of-the-numbers/
    04_what-a-network-can-learn.md  -> images/inside-a-network/what-a-network-can-learn/

Run with:  python3 ../docs/diagrams/inside_a_network_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so the two documents can quote the same values.

What is real and what is made up. The arithmetic is all real: the matrix
multiplies, the counts of multiply-adds and of numbers moved, the byte and
gigabyte totals, the floating-point spacings and rounding errors (measured
with NumPy, with bfloat16 worked out by cutting a float32 down to 7 fraction
bits), the convolutions, the parameter counts and the least-squares fits. The
*data* is made up where a worked example needs small numbers a reader can
follow: the weights and inputs of the small layers, the small brightness
grids, and the curve that the rectified-linear fits on the second page chase.
Made-up data that needs to be random comes from numpy.random.default_rng with
a fixed seed, and the pages say so where the picture is used. No benchmark
score, no real model's parameter count and no measured running time appears
anywhere; the model sizes in the memory bill are round numbers chosen to
stand for small, middling and large models.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize, to_hex  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'inside-a-network')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
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
PALE: str = '#f4f4f4'

DOC3: str = 'the-shape-of-the-numbers'
DOC4: str = 'what-a-network-can-learn'

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


def _blank(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    """A plain white drawing surface with equal aspect and no axes."""
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _plain(ax: Axes) -> None:
    """A normal plot with the top and right frame lines removed."""
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = 'white',
         edge: str = INK, lw: float = 1.0, text: str = '', size: float = 9.0,
         colour: str = INK, weight: str = 'normal', zorder: float = 2.0) -> None:
    """One rectangle with its lower-left corner at (x, y), optionally labelled."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, lw=lw,
                           zorder=zorder))
    if text:
        ax.text(x + w / 2, y + h / 2, text, fontsize=size, ha='center', va='center',
                color=colour, weight=weight, zorder=zorder + 0.5)


def _grid_at(ax: Axes, values: Arr, x0: float, y0: float, cell: float = 1.0,
             fmt: str = '{:.0f}', faces: list[list[str]] | None = None,
             size: float = 8.5, edge: str = 'white', frame: str = INK,
             text_colours: list[list[str]] | None = None,
             show_text: bool = True) -> tuple[float, float]:
    """Draw a 2-D array of numbers as a grid whose TOP-left corner is (x0, y0).

    Returns the width and height drawn, so callers can place the next thing.
    """
    h, w = values.shape
    for r in range(h):
        for c in range(w):
            face = faces[r][c] if faces is not None else 'white'
            ax.add_patch(Rectangle((x0 + c * cell, y0 - (r + 1) * cell), cell, cell,
                                   facecolor=face, edgecolor=edge, lw=0.8, zorder=2))
            if show_text:
                tc = text_colours[r][c] if text_colours is not None else INK
                ax.text(x0 + (c + 0.5) * cell, y0 - (r + 0.5) * cell,
                        fmt.format(values[r, c]), fontsize=size, ha='center',
                        va='center', color=tc, zorder=3)
    ax.add_patch(Rectangle((x0, y0 - h * cell), w * cell, h * cell, facecolor='none',
                           edgecolor=frame, lw=1.2, zorder=4))
    return w * cell, h * cell


def _frame(ax: Axes, x0: float, y0: float, w: float, h: float, colour: str = GRIP,
           lw: float = 2.2) -> None:
    """A coloured outline, used to mark a window or a chosen row."""
    ax.add_patch(Rectangle((x0, y0 - h), w, h, facecolor='none', edgecolor=colour,
                           lw=lw, zorder=6))


def _arrow(ax: Axes, p0: tuple[float, float], p1: tuple[float, float],
           colour: str = MUTED, lw: float = 1.6, scale: float = 14.0,
           style: str = '-|>') -> None:
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=scale,
                                 color=colour, lw=lw, zorder=5,
                                 shrinkA=0.0, shrinkB=0.0))


def _shade(value: float, vmin: float, vmax: float, cmap: str = 'Blues',
           lo: float = 0.04, hi: float = 0.62) -> str:
    """A pale-to-strong colour for one number, used to fill grid cells."""
    if vmax <= vmin:
        return 'white'
    t = (float(value) - vmin) / (vmax - vmin)
    t = min(max(t, 0.0), 1.0)
    return to_hex(plt.get_cmap(cmap)(lo + t * (hi - lo)))


def _faces(values: Arr, cmap: str = 'Blues', vmin: float | None = None,
           vmax: float | None = None, lo: float = 0.04,
           hi: float = 0.62) -> list[list[str]]:
    a = float(values.min()) if vmin is None else vmin
    b = float(values.max()) if vmax is None else vmax
    return [[_shade(v, a, b, cmap, lo, hi) for v in row] for row in values]


def _grey_faces(values: Arr, top: float = 255.0) -> list[list[str]]:
    """Brightness 0 to top drawn as black to white, the way a picture looks."""
    out = []
    for row in values:
        cells = []
        for v in row:
            g = int(round(255 * min(max(float(v) / top, 0.0), 1.0)))
            cells.append(f'#{g:02x}{g:02x}{g:02x}')
        out.append(cells)
    return out


def _title(fig: Figure, text: str, size: float = 13.0) -> None:
    fig.suptitle(text, fontsize=size, weight='bold', color=INK)


def _gb(n_numbers: float, bytes_each: int) -> float:
    """Gigabytes, counting a gigabyte as 1,000,000,000 bytes."""
    return n_numbers * bytes_each / 1e9


def _commas(n: float) -> str:
    return f'{int(round(n)):,}'


# --------------------------------------------------------------------------
# 03_the-shape-of-the-numbers, section 1: what a tensor is
# --------------------------------------------------------------------------

JOINT_ANGLES: Arr = np.array([0.0, -45.0, 90.0, 0.0, 60.0, 0.0, 15.0])

# A made-up 8 by 8 brightness grid: a dark table with a bright upright bar on it.
def _small_picture() -> Arr:
    pic = np.full((8, 8), 30.0)
    pic[1:7, 3:5] = 210.0
    pic[2, 2] = 90.0
    pic[5, 5] = 90.0
    pic[0, :] = 45.0
    pic[7, :] = 20.0
    return pic


def four_shapes() -> None:
    """A number, a list, a grid and a stack of grids, with the shape of each."""
    pic = _small_picture()
    rgb = np.stack([pic * 0.95, pic * 0.70, pic * 0.45]) / 255.0
    print('[shapes] one number: shape (), 1 number')
    print(f'[shapes] joint angles: shape (7,), 7 numbers -> {JOINT_ANGLES.tolist()}')
    print(f'[shapes] grey picture: shape (8, 8), {pic.size} numbers, '
          f'values {pic.min():.0f} to {pic.max():.0f}')
    print(f'[shapes] colour picture: shape (3, 8, 8), {rgb.size} numbers')

    fig, ax = plt.subplots(figsize=(13.4, 5.2), facecolor='white')
    _blank(ax, (-0.6, 33.4), (-4.6, 8.4))

    # a single number
    _box(ax, 0.0, 6.0, 1.6, 1.6, face=_shade(0.63, 0.0, 1.0), text='0.63', size=10)
    ax.text(0.8, 5.5, 'one number', fontsize=10, ha='center', va='top', color=INK,
            weight='bold')
    ax.text(0.8, 4.8, 'shape ()\n1 number', fontsize=9.5, ha='center', va='top',
            color=MUTED)

    # a list of seven numbers
    x0 = 4.0
    _grid_at(ax, JOINT_ANGLES.reshape(1, 7), x0, 7.6, cell=1.1, fmt='{:.0f}',
             faces=_faces(JOINT_ANGLES.reshape(1, 7), vmin=-60, vmax=100), size=8.5)
    ax.text(x0 + 3.85, 5.5, 'a list of numbers', fontsize=10, ha='center', va='top',
            color=INK, weight='bold')
    ax.text(x0 + 3.85, 4.8, 'shape (7,)\n7 numbers: one angle per joint, in degrees',
            fontsize=9.5, ha='center', va='top', color=MUTED)

    # a grid of numbers
    x0 = 13.6
    _grid_at(ax, pic, x0, 8.0, cell=0.95, fmt='{:.0f}', faces=_grey_faces(pic),
             size=7.0,
             text_colours=[['white' if v < 120 else INK for v in row] for row in pic])
    ax.text(x0 + 3.8, 0.0, 'a grid of numbers', fontsize=10, ha='center', va='top',
            color=INK, weight='bold')
    ax.text(x0 + 3.8, -0.7, 'shape (8, 8)\n64 numbers: the brightness of each pixel',
            fontsize=9.5, ha='center', va='top', color=MUTED)

    # a stack of three grids
    x0 = 23.2
    tints = ((2, '#e05555', 'red'), (1, '#2a9d3f', 'green'), (0, '#3b82c4', 'blue'))
    for k, (rgb_k, colour, name) in enumerate(tints):
        dx, dy = k * 1.8, -k * 1.8
        for r in range(8):
            for c in range(8):
                v = float(rgb[2 - rgb_k, r, c])
                base = np.array([0.88, 0.88, 0.88])
                pure = np.array(plt.matplotlib.colors.to_rgb(colour))
                mix = base * (1 - v) + pure * v
                ax.add_patch(Rectangle((x0 + dx + c * 0.55, 6.6 + dy - (r + 1) * 0.55),
                                       0.55, 0.55, facecolor=to_hex(mix),
                                       edgecolor='white', lw=0.25, zorder=2 + k))
        ax.add_patch(Rectangle((x0 + dx, 6.6 + dy - 4.4), 4.4, 4.4, facecolor='none',
                               edgecolor=colour, lw=1.6, zorder=5 + k))
        ax.text(x0 + dx + 4.5, 6.6 + dy - 0.3, name, fontsize=9, color=colour,
                ha='left', va='center', zorder=8)
    ax.text(x0 + 3.8, -2.3, 'a stack of grids', fontsize=10, ha='center', va='top',
            color=INK, weight='bold')
    ax.text(x0 + 3.8, -3.0, 'shape (3, 8, 8)\n192 numbers: one grid per colour',
            fontsize=9.5, ha='center', va='top', color=MUTED)

    _title(fig, 'One word, tensor, covers all four: the shape says how the numbers '
                'are arranged')
    _save(fig, DOC3, 'four-shapes.svg')


REAL_SHAPES: list[tuple[str, tuple[int, ...], str]] = [
    ('(7,)', (7,), 'one reading of a seven-joint arm'),
    ('(32, 7)', (32, 7), '32 readings of that arm, one per row'),
    ('(3, 224, 224)', (3, 224, 224), 'one colour photo, 224 rows by 224 columns'),
    ('(8, 3, 224, 224)', (8, 3, 224, 224), 'eight colour photos at once'),
    ('(8, 128, 768)', (8, 128, 768), 'eight sentences of 128 words, 768 numbers a word'),
]


def real_shapes() -> None:
    """A table of shapes a robot model really uses, with counts and byte sizes."""
    rows = []
    for text, shape, meaning in REAL_SHAPES:
        n = int(np.prod(shape))
        rows.append((text, meaning, n, n * 4))
        print(f'[real] {text:18s} {n:>12,} numbers  {n * 4:>13,} bytes at float32 '
              f'({n * 4 / 1e6:.3f} MB)  -- {meaning}')

    fig, ax = plt.subplots(figsize=(13.0, 4.4), facecolor='white')
    _blank(ax, (-0.3, 26.3), (-0.4, 7.0))
    heads = ('shape, as code writes it', 'what it holds', 'how many numbers',
             'bytes at float32')
    widths = (5.4, 10.4, 4.6, 5.4)
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    for x, w, head in zip(xs, widths, heads):
        _box(ax, x, 5.9, w, 1.0, face='#e8eff7', edge=INK, text=head, size=10,
             weight='bold')
    for i, (text, meaning, n, nbytes) in enumerate(rows):
        y = 4.8 - i * 1.1
        face = PALE if i % 2 else 'white'
        bytes_text = (_commas(nbytes) if nbytes < 100_000
                      else f'{_commas(nbytes)}  ({nbytes / 1e6:.2f} MB)')
        cells = (text, meaning, _commas(n), bytes_text)
        for x, w, cell in zip(xs, widths, cells):
            _box(ax, x, y, w, 1.1, face=face, edge=GRID, text=cell,
                 size=9.5 if cell is not text else 10,
                 weight='bold' if cell is text else 'normal',
                 colour=LINK if cell is text else INK)
    _title(fig, 'Real shapes: the first number is nearly always how many examples '
                'are being handled at once')
    _save(fig, DOC3, 'real-shapes.svg')


def reshape_24() -> None:
    """The same 24 numbers seen as a list, a grid and a stack of grids."""
    v = np.arange(24, dtype=float)
    print(f'[reshape] 24 numbers 0..23 as (24,), (4, 6) and (2, 3, 4); '
          f'row 1 of the (4, 6) view is {v.reshape(4, 6)[1].tolist()}')
    print(f'[reshape] in the (2, 3, 4) view the number at (1, 2, 3) is '
          f'{v.reshape(2, 3, 4)[1, 2, 3]:.0f}')

    fig, ax = plt.subplots(figsize=(13.2, 5.0), facecolor='white')
    _blank(ax, (-0.5, 27.5), (-3.2, 4.2))
    faces1 = _faces(v.reshape(1, 24), vmin=0, vmax=23)
    _grid_at(ax, v.reshape(1, 24), 0.0, 3.4, cell=0.84, faces=faces1, size=7.5)
    ax.text(10.1, 2.2, 'shape (24,): one long list', fontsize=10, ha='center',
            va='top', color=INK, weight='bold')

    g = v.reshape(4, 6)
    _grid_at(ax, g, 0.0, 0.6, cell=1.0, faces=_faces(g, vmin=0, vmax=23), size=8.5)
    ax.text(3.0, -4.0 + 0.1, 'shape (4, 6): four rows of six', fontsize=10,
            ha='center', va='top', color=INK, weight='bold')
    ax.text(3.0, -4.7 + 0.1, 'the numbers are in the same order,\nread left to right '
            'then down', fontsize=9.5, ha='center', va='top', color=MUTED)

    s = v.reshape(2, 3, 4)
    for k in range(2):
        x0 = 9.6 + k * 6.4
        _grid_at(ax, s[k], x0, 0.6, cell=1.0, faces=_faces(s[k], vmin=0, vmax=23),
                 size=8.5)
        ax.text(x0 + 2.0, 0.95, f'slice {k}', fontsize=9.5, ha='center', va='bottom',
                color=MUTED)
    ax.text(14.8, -3.9, 'shape (2, 3, 4): two grids of three rows by four',
            fontsize=10, ha='center', va='top', color=INK, weight='bold')
    ax.text(14.8, -4.6, 'nothing moved in memory; only the way of counting changed',
            fontsize=9.5, ha='center', va='top', color=MUTED)

    _arrow(ax, (20.7, 2.0), (22.6, 2.0))
    ax.text(23.0, 2.0, 'reshaping is free:\nthe numbers stay\nwhere they are',
            fontsize=9.5, ha='left', va='center', color=LINK)
    _arrow(ax, (8.6, -1.4), (9.3, -1.4))
    _title(fig, 'One shape, three ways of counting: 24 numbers as (24,), (4, 6) and '
                '(2, 3, 4)')
    _save(fig, DOC3, 'reshape-24.svg')


def memory_line() -> None:
    """How a (4, 6) grid sits in one line of memory, and the index arithmetic."""
    v = np.arange(24, dtype=float)
    g = v.reshape(4, 6)
    picks = [(0, 0), (1, 2), (3, 5)]
    for r, c in picks:
        print(f'[memory] grid position (row {r}, column {c}) is at place '
              f'{r} x 6 + {c} = {r * 6 + c} in the line, holding '
              f'{g[r, c]:.0f}')

    fig, ax = plt.subplots(figsize=(13.2, 5.4), facecolor='white')
    _blank(ax, (-0.6, 25.6), (-4.6, 4.6))
    faces = _faces(g, vmin=0, vmax=23)
    _grid_at(ax, g, 0.0, 4.2, cell=1.05, faces=faces, size=8.5)
    for r in range(4):
        ax.text(-0.35, 4.2 - (r + 0.5) * 1.05, f'row {r}', fontsize=8.5, ha='right',
                va='center', color=MUTED)
    for c in range(6):
        ax.text((c + 0.5) * 1.05, 4.45, f'col {c}', fontsize=8.5, ha='center',
                va='bottom', color=MUTED)
    ax.text(3.15, -0.5, 'the grid, shape (4, 6)', fontsize=10, ha='center', va='top',
            color=INK, weight='bold')

    # the one line of memory
    cell = 0.84
    x0 = 8.6
    _grid_at(ax, v.reshape(1, 24), x0, -1.9, cell=cell, faces=_faces(v.reshape(1, 24),
                                                                    vmin=0, vmax=23),
             size=7.0)
    for i in range(0, 24, 6):
        ax.text(x0 + (i + 0.5) * cell, -2.95, str(i), fontsize=7.5, ha='center',
                va='top', color=MUTED)
    ax.text(x0 + 10.1, -3.7, 'memory: one line of 24 places, counted from 0',
            fontsize=10, ha='center', va='top', color=INK, weight='bold')

    colours = (GRIP, SLIDE, PURPLE)
    for (r, c), colour in zip(picks, colours):
        _frame(ax, c * 1.05, 4.2 - r * 1.05, 1.05, 1.05, colour=colour, lw=2.4)
        place = r * 6 + c
        _frame(ax, x0 + place * cell, -1.9, cell, cell, colour=colour, lw=2.4)
        _arrow(ax, ((c + 0.5) * 1.05, 4.2 - (r + 1) * 1.05 - 0.05),
               (x0 + (place + 0.5) * cell, -1.85), colour=colour, lw=1.3)
        ax.text(16.0, 3.4 - colours.index(colour) * 1.0,
                f'(row {r}, col {c})  ->  {r} x 6 + {c} = {place}', fontsize=10.5,
                ha='left', va='center', color=colour)
    ax.text(16.0, 4.3, 'where a position lands in the line', fontsize=10.5, ha='left',
            va='center', color=INK, weight='bold')
    _title(fig, 'A grid is a line of numbers plus a rule: step 6 to change row, '
                'step 1 to change column')
    _save(fig, DOC3, 'memory-line.svg')


# --------------------------------------------------------------------------
# 03, section 2: a fully connected layer is a matrix multiply
# --------------------------------------------------------------------------

# A made-up small layer: four inputs into three neurons.
W_SMALL: Arr = np.array([[0.5, -0.2, 0.8, 0.1],
                         [-0.3, 0.6, 0.2, -0.5],
                         [0.7, 0.4, -0.6, 0.3]])
B_SMALL: Arr = np.array([0.1, -0.2, 0.05])
X_SMALL: Arr = np.array([2.0, 1.0, -1.0, 3.0])
X_BATCH: Arr = np.array([[2.0, 1.0, -1.0, 3.0],
                         [0.0, 2.0, 1.0, -1.0]])


def one_layer_by_hand() -> None:
    """Every product of a 3-by-4 weight grid times a 4-long input, then ReLU."""
    prod = W_SMALL * X_SMALL[None, :]
    sums = prod.sum(axis=1)
    pre = sums + B_SMALL
    out = np.maximum(pre, 0.0)
    for r in range(3):
        terms = ' + '.join(f'({W_SMALL[r, c]:.1f} x {X_SMALL[c]:.0f})' for c in range(4))
        print(f'[layer] neuron {r}: {terms} = {sums[r]:.2f}; '
              f'+ bias {B_SMALL[r]:.2f} = {pre[r]:.2f}; ReLU -> {out[r]:.2f}')
    print(f'[layer] products grid =\n{np.round(prod, 2)}')
    print(f'[layer] output = {np.round(out, 2).tolist()}')

    fig, ax = plt.subplots(figsize=(13.6, 5.6), facecolor='white')
    _blank(ax, (-2.2, 24.6), (-2.6, 6.4))
    cell = 1.15

    # the weight grid
    _grid_at(ax, W_SMALL, 0.0, 4.6, cell=cell, fmt='{:+.1f}',
             faces=_faces(W_SMALL, cmap='RdBu', vmin=-1.0, vmax=1.0), size=9)
    ax.text(2.07, 5.0, 'weights, shape (3, 4)', fontsize=10, ha='center', va='bottom',
            color=INK, weight='bold')
    for r in range(3):
        ax.text(-0.25, 4.6 - (r + 0.5) * cell, f'neuron {r}', fontsize=9, ha='right',
                va='center', color=MUTED)

    # the input
    x0 = 6.2
    _grid_at(ax, X_SMALL.reshape(4, 1), x0, 4.6, cell=cell, fmt='{:+.0f}',
             faces=_faces(X_SMALL.reshape(4, 1), vmin=-3, vmax=3), size=9)
    ax.text(x0 + 0.58, 5.0, 'input,\nshape (4,)', fontsize=10, ha='center', va='bottom',
            color=INK, weight='bold')

    # the products
    x0 = 9.6
    _grid_at(ax, prod, x0, 4.6, cell=cell, fmt='{:+.1f}',
             faces=_faces(prod, cmap='RdBu', vmin=-2.4, vmax=2.4), size=9)
    ax.text(x0 + 2.3, 5.0, 'the 12 products, one per pair', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')

    # the row sums, bias, ReLU, output
    x0 = 15.2
    for r in range(3):
        y = 4.6 - (r + 1) * cell
        _box(ax, x0, y, 1.5, cell, face='white', edge=INK, text=f'{sums[r]:+.2f}',
             size=9.5)
        _box(ax, x0 + 2.2, y, 1.5, cell, face='white', edge=GRID,
             text=f'{B_SMALL[r]:+.2f}', size=9.5, colour=WRIST)
        _box(ax, x0 + 4.4, y, 1.5, cell, face='white', edge=INK,
             text=f'{pre[r]:+.2f}', size=9.5)
        _box(ax, x0 + 6.6, y, 1.5, cell, face=_shade(out[r], 0, 2.5), edge=INK,
             text=f'{out[r]:.2f}', size=10, weight='bold')
        ax.text(x0 + 1.95, y + cell / 2, '+', fontsize=11, ha='center', va='center',
                color=MUTED)
        ax.text(x0 + 4.15, y + cell / 2, '=', fontsize=11, ha='center', va='center',
                color=MUTED)
        _arrow(ax, (x0 + 5.95, y + cell / 2), (x0 + 6.5, y + cell / 2))
    for dx, label, colour in ((0.75, 'sum of\nthe row', INK),
                              (2.95, 'bias', WRIST),
                              (5.15, 'total', INK),
                              (7.35, 'ReLU:\nbelow 0 -> 0', SLIDE)):
        ax.text(x0 + dx, 5.0, label, fontsize=9.5, ha='center', va='bottom',
                color=colour, weight='bold')
    ax.text(11.0, -1.6, 'The three neurons do the same arithmetic on the same four '
            'inputs with different weights, which is exactly what a matrix multiply is.',
            fontsize=10, ha='center', va='center', color=MUTED)
    _title(fig, 'One fully connected layer worked out in full: 12 multiplies, '
                '3 row totals, 3 biases, 3 ReLUs')
    _save(fig, DOC3, 'one-layer-by-hand.svg')


def shapes_must_match() -> None:
    """The inner numbers of the two shapes have to agree, with a worked failure."""
    good = X_BATCH @ W_SMALL.T
    print(f'[match] (2, 4) times (4, 3) gives (2, 3): \n{np.round(good, 2)}')
    print('[match] (2, 4) times (3, 3) is refused, because 4 does not equal 3')

    fig, ax = plt.subplots(figsize=(12.6, 4.6), facecolor='white')
    _blank(ax, (-0.8, 25.0), (-3.4, 3.2))

    def shape_pair(x0: float, a: tuple[int, int], b: tuple[int, int], ok: bool) -> None:
        colour = SLIDE if ok else GRIP
        _box(ax, x0, 0.4, 3.0, 1.4, face='white', edge=INK,
             text=f'({a[0]}, {a[1]})', size=12)
        ax.text(x0 + 3.5, 1.1, 'x', fontsize=12, ha='center', va='center', color=MUTED)
        _box(ax, x0 + 4.0, 0.4, 3.0, 1.4, face='white', edge=INK,
             text=f'({b[0]}, {b[1]})', size=12)
        ax.plot([x0 + 2.3, x0 + 4.7], [0.1, 0.1], color=colour, lw=2.0)
        ax.text(x0 + 3.5, -0.25, f'{a[1]} and {b[0]}', fontsize=10, ha='center',
                va='top', color=colour, weight='bold')
        if ok:
            _arrow(ax, (x0 + 7.4, 1.1), (x0 + 8.4, 1.1), colour=SLIDE)
            _box(ax, x0 + 8.6, 0.4, 3.0, 1.4, face='#e6f3e8', edge=SLIDE,
                 text=f'({a[0]}, {b[1]})', size=12, colour=SLIDE)
            ax.text(x0 + 5.8, 2.1, 'the inner numbers agree, so this works',
                    fontsize=10.5, ha='center', va='bottom', color=SLIDE, weight='bold')
            ax.text(x0 + 5.8, -1.1, 'the two outer numbers become the answer\'s shape',
                    fontsize=9.5, ha='center', va='top', color=MUTED)
        else:
            ax.text(x0 + 7.9, 1.1, 'refused', fontsize=11.5, ha='left', va='center',
                    color=GRIP, weight='bold')
            ax.text(x0 + 5.2, 2.1, 'the inner numbers differ, so there is nothing to add',
                    fontsize=10.5, ha='center', va='bottom', color=GRIP, weight='bold')
            ax.text(x0 + 5.2, -1.1, 'each of the 4 numbers in a row needs a partner,\n'
                    'and only 3 are offered', fontsize=9.5, ha='center', va='top',
                    color=MUTED)

    shape_pair(0.0, (2, 4), (4, 3), True)
    ax.plot([12.6, 12.6], [-2.2, 2.6], color=GRID, lw=1.2)
    shape_pair(13.6, (2, 4), (3, 3), False)
    _title(fig, 'The shape rule: (rows, inner) times (inner, columns) gives '
                '(rows, columns)')
    _save(fig, DOC3, 'shapes-must-match.svg')


def batch_matmul() -> None:
    """Two examples through the same layer in one multiply, with one cell opened up."""
    pre = X_BATCH @ W_SMALL.T + B_SMALL[None, :]
    out = np.maximum(pre, 0.0)
    terms = [f'({X_BATCH[1, c]:+.0f} x {W_SMALL[2, c]:+.1f})' for c in range(4)]
    cell_val = float(X_BATCH[1] @ W_SMALL[2])
    print(f'[batch2] pre-ReLU totals =\n{np.round(pre, 2)}')
    print(f'[batch2] after ReLU =\n{np.round(out, 2)}')
    print(f'[batch2] example 1, neuron 2: {" + ".join(terms)} = {cell_val:.2f}, '
          f'+ bias {B_SMALL[2]:.2f} = {pre[1, 2]:.2f}')

    fig, ax = plt.subplots(figsize=(13.4, 5.4), facecolor='white')
    _blank(ax, (-2.4, 24.0), (-3.6, 5.0))
    cell = 1.2

    _grid_at(ax, X_BATCH, 0.0, 3.4, cell=cell, fmt='{:+.0f}',
             faces=_faces(X_BATCH, vmin=-3, vmax=3), size=9.5)
    ax.text(2.4, 3.8, 'two examples, shape (2, 4)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')
    for r in range(2):
        ax.text(-0.25, 3.4 - (r + 0.5) * cell, f'example {r}', fontsize=9, ha='right',
                va='center', color=MUTED)

    x0 = 6.4
    _grid_at(ax, W_SMALL.T, x0, 3.4, cell=cell, fmt='{:+.1f}',
             faces=_faces(W_SMALL.T, cmap='RdBu', vmin=-1.0, vmax=1.0), size=9.5)
    ax.text(x0 + 1.8, 3.8, 'the same weights, shape (4, 3)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')

    x0 = 13.0
    _grid_at(ax, pre, x0, 3.4, cell=cell, fmt='{:+.2f}',
             faces=_faces(pre, cmap='RdBu', vmin=-3, vmax=3), size=9)
    ax.text(x0 + 1.8, 3.8, 'totals, shape (2, 3)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')

    x0 = 18.2
    _grid_at(ax, out, x0, 3.4, cell=cell, fmt='{:.2f}',
             faces=_faces(out, vmin=0, vmax=3), size=9)
    ax.text(x0 + 1.8, 3.8, 'after ReLU', fontsize=10, ha='center', va='bottom',
            color=INK, weight='bold')
    ax.text(4.0, 1.3, 'x', fontsize=13, ha='center', va='center', color=MUTED)
    ax.text(11.5, 1.3, '+ bias', fontsize=11, ha='center', va='center', color=WRIST)
    _arrow(ax, (16.9, 1.3), (18.0, 1.3))

    _frame(ax, 0.0, 3.4 - cell, 4 * cell, cell, colour=GRIP)
    _frame(ax, 6.4 + 2 * cell, 3.4, cell, 4 * cell, colour=GRIP)
    _frame(ax, 13.0 + 2 * cell, 3.4 - cell, cell, cell, colour=GRIP)
    ax.text(10.6, -1.9, f'the marked cell: {" + ".join(terms)} = {cell_val:.2f}, '
            f'then + {B_SMALL[2]:.2f} = {pre[1, 2]:.2f}', fontsize=11, ha='center',
            va='center', color=GRIP)
    ax.text(10.6, -2.9, 'each of the six totals is one row of inputs paired with one '
            'column of weights, so the two examples never mix', fontsize=10,
            ha='center', va='center', color=MUTED)
    _title(fig, 'A batch of two examples through one layer: one multiply, '
                'six row-and-column pairings')
    _save(fig, DOC3, 'batch-matmul.svg')


LAYER_SIZES: list[tuple[str, int, int]] = [
    ('joint angles\n7 -> 64', 7, 64),
    ('hidden layer\n64 -> 64', 64, 64),
    ('transformer part\n768 -> 3072', 768, 3072),
    ('flattened photo\n150,528 -> 1,000', 150528, 1000),
]


def layer_cost() -> None:
    """How the weight count and the multiply-add count grow with the layer's size."""
    names, params, macs = [], [], []
    for label, n_in, n_out in LAYER_SIZES:
        p = n_in * n_out + n_out
        names.append(label)
        params.append(p)
        macs.append(n_in * n_out)
        print(f'[cost] {label.replace(chr(10), " ")}: {n_in} x {n_out} = '
              f'{_commas(n_in * n_out)} weights, + {n_out} biases = {_commas(p)} '
              f'parameters; {_commas(n_in * n_out)} multiply-adds per example')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    pos = np.arange(len(names), dtype=float)
    ax.bar(pos - 0.2, params, width=0.4, color=LINK, edgecolor=INK, lw=0.6,
           label='parameters (weights + biases)')
    ax.bar(pos + 0.2, macs, width=0.4, color=WRIST, edgecolor=INK, lw=0.6,
           label='multiply-adds for one example')
    ax.set_yscale('log')
    ax.set_ylim(1, 1e10)
    for p, v in zip(pos - 0.2, params):
        ax.text(p, v * 1.5, _commas(v), fontsize=8.5, ha='center', color=LINK,
                rotation=90, va='bottom')
    for p, v in zip(pos + 0.2, macs):
        ax.text(p, v * 1.5, _commas(v), fontsize=8.5, ha='center', color=WRIST,
                rotation=90, va='bottom')
    ax.set_xticks(pos)
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylabel('count (log scale)', fontsize=10)
    ax.set_title('A fully connected layer costs one weight and one multiply-add for '
                 'every input-and-neuron pair', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC3, 'layer-cost.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    four_shapes()
    real_shapes()
    reshape_24()
    memory_line()
    one_layer_by_hand()
    shapes_must_match()
    batch_matmul()
    layer_cost()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
