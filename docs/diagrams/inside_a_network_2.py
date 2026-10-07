"""Generate the diagrams for the last two pages of docs/05_neural-networks/02_inside-a-network/.

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
stand for small, middling and large models, as are the four model shapes whose
parameters section 2 counts.
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


def _table(ax: Axes, heads: tuple[str, ...], rows: list[tuple[str, ...]],
           widths: tuple[float, ...], highlight: int = -1, size: float = 9.0,
           head_size: float = 9.0) -> None:
    """Draw a table in an axes whose coordinates run 0 to 1 both ways."""
    ax.set_facecolor('white')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    total = sum(widths)
    xs, x = [], 0.0
    for w in widths:
        xs.append(x)
        x += w / total
    ws = [w / total for w in widths]
    n = len(rows) + 1
    h = 1.0 / n
    for x, w, head in zip(xs, ws, heads):
        ax.add_patch(Rectangle((x, 1 - h), w, h, facecolor='#e8eff7', edgecolor=INK,
                               lw=0.8))
        ax.text(x + w / 2, 1 - h / 2, head, fontsize=head_size, ha='center',
                va='center', color=INK, weight='bold')
    for i, row in enumerate(rows):
        y = 1 - (i + 2) * h
        face = PALE if i % 2 else 'white'
        for x, w, cell in zip(xs, ws, row):
            ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=GRID,
                                   lw=0.8))
            ax.text(x + w / 2, y + h / 2, cell, fontsize=size, ha='center',
                    va='center', color=GRIP if i == highlight else INK,
                    weight='bold' if i == highlight else 'normal')


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

    fig, ax = plt.subplots(figsize=(13.2, 5.6), facecolor='white')
    _blank(ax, (-1.4, 24.6), (-5.6, 5.0))
    faces = _faces(g, vmin=0, vmax=23)
    _grid_at(ax, g, 0.0, 4.2, cell=1.05, faces=faces, size=8.5)
    for r in range(4):
        ax.text(-0.35, 4.2 - (r + 0.5) * 1.05, f'row {r}', fontsize=8.5, ha='right',
                va='center', color=MUTED)
    for c in range(6):
        ax.text((c + 0.5) * 1.05, 4.45, f'col {c}', fontsize=8.5, ha='center',
                va='bottom', color=MUTED)
    ax.text(3.15, -0.3, 'the grid, shape (4, 6)', fontsize=10, ha='center', va='top',
            color=INK, weight='bold')

    # the one line of memory
    cell = 0.76
    x0 = 0.6
    _grid_at(ax, v.reshape(1, 24), x0, -2.4, cell=cell, faces=_faces(v.reshape(1, 24),
                                                                    vmin=0, vmax=23),
             size=7.0)
    for i in range(0, 24, 6):
        ax.text(x0 + (i + 0.5) * cell, -3.3, f'place {i}', fontsize=7.5, ha='center',
                va='top', color=MUTED)
    ax.text(x0 + 9.1, -4.2, 'memory: one line of 24 places, counted from 0',
            fontsize=10, ha='center', va='top', color=INK, weight='bold')
    _arrow(ax, (9.0, -0.4), (9.0, -2.3), colour=MUTED, lw=1.4)
    ax.text(9.3, -1.4, 'the rows are laid down one after another,\nrow 0 first',
            fontsize=9.5, ha='left', va='center', color=MUTED)

    colours = (GRIP, SLIDE, PURPLE)
    for (r, c), colour in zip(picks, colours):
        _frame(ax, c * 1.05, 4.2 - r * 1.05, 1.05, 1.05, colour=colour, lw=2.4)
        place = r * 6 + c
        _frame(ax, x0 + place * cell, -2.4, cell, cell, colour=colour, lw=2.4)
        ax.text(9.6, 3.0 - colours.index(colour) * 1.1,
                f'(row {r}, col {c})  ->  {r} x 6 + {c} = place {place}', fontsize=10.5,
                ha='left', va='center', color=colour)
    ax.text(9.6, 4.2, 'where a position lands in the line', fontsize=10.5, ha='left',
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

    x0 = 7.6
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
    ax.text(5.9, 2.2, 'x', fontsize=13, ha='center', va='center', color=MUTED)
    ax.text(12.1, 2.2, '+ bias', fontsize=11, ha='center', va='center', color=WRIST)
    _arrow(ax, (16.9, 2.2), (18.0, 2.2))

    _frame(ax, 0.0, 3.4 - cell, 4 * cell, cell, colour=GRIP)
    _frame(ax, 7.6 + 2 * cell, 3.4, cell, 4 * cell, colour=GRIP)
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


# --------------------------------------------------------------------------
# 03, section 2 continued: counting the parameters of a whole model
# --------------------------------------------------------------------------

# The four models that section 2 counts and section 6 prices. Each one is a
# round made-up size chosen to stand for a scale of model, not a real model.
# A fully connected layer of n inputs into m neurons holds n x m weights and
# m biases, so a stack of such layers is a sum of (n x m + m).
LINE_SIZES: tuple[int, ...] = (1, 1)             # a fitted straight line
TINY_SIZES: tuple[int, ...] = (3, 8, 1)          # 3 inputs, 8 neurons, 1 output
PICTURE_SIZES: tuple[int, ...] = (64 * 64, 256, 256, 1)   # a 64 by 64 grey picture
STACK_BLOCKS: int = 48
STACK_WIDTH: int = 2048
# One block holds twelve square grids of its own width: four in the attention
# part, and two in the middle layer, whose middle is four times the width, so
# those two cover eight times the area of one square grid.
BLOCK_GRIDS: int = 12


def _layers_of(sizes: tuple[int, ...]) -> list[tuple[int, int]]:
    """The (inputs, neurons) pair of every layer in a stack of sizes."""
    return list(zip(sizes, sizes[1:]))


def _mlp_params(sizes: tuple[int, ...]) -> int:
    """Parameters of a stack of fully connected layers: sum of n x m + m."""
    return sum(n * m + m for n, m in _layers_of(sizes))


def _mlp_macs(sizes: tuple[int, ...]) -> int:
    """Multiply-adds for one example: one for every input-and-neuron pair."""
    return sum(n * m for n, m in _layers_of(sizes))


def _stack_params() -> int:
    """Parameters of a stack of blocks, counting its square grids only."""
    return STACK_BLOCKS * BLOCK_GRIDS * STACK_WIDTH * STACK_WIDTH


def _print_stack(sizes: tuple[int, ...], name: str) -> int:
    total = 0
    for i, (n, m) in enumerate(_layers_of(sizes), start=1):
        total += n * m + m
        print(f'[count] {name}, layer {i}: {_commas(n)} x {_commas(m)} = '
              f'{_commas(n * m)} weights, + {_commas(m)} biases = '
              f'{_commas(n * m + m)} parameters')
    print(f'[count] {name}: {_commas(total)} parameters in all')
    return total


def count_the_tiny_network() -> None:
    """Every parameter of a 3 -> 8 -> 1 network, drawn small enough to count."""
    _print_stack(LINE_SIZES, 'a fitted straight line')
    total = _print_stack(TINY_SIZES, 'the tiny network 3 -> 8 -> 1')

    (n1, m1), (n2, m2) = _layers_of(TINY_SIZES)
    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _blank(ax, (-2.8, 19.4), (-3.6, 9.6))
    cell, top = 1.0, 8.0
    blue = [_shade(0.55, 0.0, 1.0)]
    amber = [_shade(0.55, 0.0, 1.0, cmap='Oranges')]

    # first layer: an 8 by 3 weight grid beside a column of 8 biases
    _grid_at(ax, np.zeros((m1, n1)), 0.0, top, cell=cell,
             faces=[blue * n1 for _ in range(m1)], show_text=False, edge='white')
    _grid_at(ax, np.zeros((m1, 1)), n1 + 1.2, top, cell=cell,
             faces=[amber for _ in range(m1)], show_text=False, edge='white')
    ax.text(n1 / 2, top + 0.35, 'weights', fontsize=10.5, ha='center', va='bottom',
            color=LINK, weight='bold')
    ax.text(n1 + 1.7, top + 0.35, 'biases', fontsize=10.5, ha='center', va='bottom',
            color=WRIST, weight='bold')
    mid1 = (n1 + 2.2) / 2
    ax.text(mid1, -0.5, f'first layer: {n1} inputs into {m1} neurons', fontsize=11,
            ha='center', va='top', color=MUTED)
    ax.text(mid1, -1.5, f'{n1} x {m1} + {m1} = {n1 * m1 + m1}', fontsize=12,
            ha='center', va='top', color=INK, weight='bold')

    # second layer: a column of 8 weights beside its single bias
    x2 = 11.6
    _grid_at(ax, np.zeros((n2, m2)), x2, top, cell=cell,
             faces=[blue for _ in range(n2)], show_text=False, edge='white')
    _grid_at(ax, np.zeros((1, 1)), x2 + 2.2, top, cell=cell, faces=[amber],
             show_text=False, edge='white')
    ax.text(x2 + 0.5, top + 0.35, 'weights', fontsize=10.5, ha='center', va='bottom',
            color=LINK, weight='bold')
    ax.text(x2 + 2.7, top + 0.35, 'bias', fontsize=10.5, ha='center', va='bottom',
            color=WRIST, weight='bold')
    mid2 = x2 + 1.6
    ax.text(mid2, -0.5, f'second layer: {n2} inputs into {m2} output', fontsize=11,
            ha='center', va='top', color=MUTED)
    ax.text(mid2, -1.5, f'{n2} x {m2} + {m2} = {n2 * m2 + m2}', fontsize=12,
            ha='center', va='top', color=INK, weight='bold')

    ax.text((mid1 + mid2) / 2, -2.9,
            f'{n1 * m1 + m1} + {n2 * m2 + m2} = {total} parameters in all',
            fontsize=13, ha='center', va='top', color=INK, weight='bold')
    _title(fig, 'Every parameter of a network with 3 inputs, 8 neurons and 1 output',
           size=12.5)
    _save(fig, DOC3, 'count-the-tiny-network.svg')


def parameters_layer_by_layer() -> None:
    """Where the parameters of the 64 by 64 picture network sit, layer by layer."""
    total = _print_stack(PICTURE_SIZES, 'the 64 by 64 picture network')
    layers = _layers_of(PICTURE_SIZES)
    counts = [n * m + m for n, m in layers]
    for (n, m), c in zip(layers, counts):
        print(f'[count] the {_commas(n)} -> {_commas(m)} layer is '
              f'{100 * c / total:.2f} per cent of the {_commas(total)}')

    names = [f'layer {i}\n{_commas(n)} -> {_commas(m)}'
             for i, (n, m) in enumerate(layers, start=1)]
    fig, ax = plt.subplots(figsize=(11.2, 4.6), facecolor='white')
    _plain(ax)
    pos = np.arange(len(counts), dtype=float)[::-1]
    ax.barh(pos, counts, height=0.55, color=LINK, edgecolor=INK, lw=0.6)
    for p, (n, m), c in zip(pos, layers, counts):
        ax.text(c + total * 0.015, p, f'{_commas(n)} x {_commas(m)} + {_commas(m)} '
                f'= {_commas(c)}', fontsize=10.5, va='center', ha='left', color=INK)
    ax.set_yticks(pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlim(0, total * 1.62)
    ax.set_xticks([0, 250_000, 500_000, 750_000, 1_000_000])
    ax.set_xticklabels(['0', '250,000', '500,000', '750,000', '1,000,000'],
                       fontsize=9.5)
    ax.set_xlabel('parameters the layer holds', fontsize=10)
    ax.set_title(f'The first layer holds {100 * counts[0] / total:.0f} of every 100 '
                 f'parameters, because it reads all 4,096 pixels', fontsize=12,
                 weight='bold')
    ax.text(0.5, -0.30, f'{_commas(counts[0])} + {_commas(counts[1])} + '
            f'{_commas(counts[2])} = {_commas(total)} parameters in all',
            transform=ax.transAxes, fontsize=11.5, ha='center', va='top',
            color=INK, weight='bold')
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    _save(fig, DOC3, 'parameters-layer-by-layer.svg')


def block_of_twelve_grids() -> None:
    """One block of the 48-block stack is twelve square grids of its width."""
    per_grid = STACK_WIDTH * STACK_WIDTH
    per_block = BLOCK_GRIDS * per_grid
    total = _stack_params()
    print(f'[count] one grid of the stack: {STACK_WIDTH} x {STACK_WIDTH} = '
          f'{_commas(per_grid)} weights')
    print(f'[count] one block: {BLOCK_GRIDS} x {_commas(per_grid)} = '
          f'{_commas(per_block)} weights')
    print(f'[count] {STACK_BLOCKS} blocks: {STACK_BLOCKS} x {_commas(per_block)} = '
          f'{_commas(total)} parameters')
    norms = STACK_BLOCKS * 2 * STACK_WIDTH
    print(f'[count] the two normalisations in each block, which this count leaves '
          f'out, hold {STACK_BLOCKS} x 2 x {STACK_WIDTH} = {_commas(norms)}, '
          f'which is 1 part in {total / norms:,.0f}')

    fig, ax = plt.subplots(figsize=(11.6, 4.8), facecolor='white')
    _blank(ax, (-1.2, 20.0), (-4.2, 7.2))
    side, gap = 2.1, 0.32
    for r in range(2):
        for c in range(2):
            _box(ax, c * (side + gap), 4.7 - r * (side + gap) - side, side, side,
                 face=_shade(0.5, 0.0, 1.0), edge=INK, lw=0.8)
    left_w = 2 * side + gap
    x0 = left_w + 2.6
    for r in range(2):
        for c in range(4):
            _box(ax, x0 + c * (side + gap), 4.7 - r * (side + gap) - side, side, side,
                 face=_shade(0.5, 0.0, 1.0, cmap='Oranges'), edge=INK, lw=0.8)
    right_w = 4 * side + 3 * gap
    ax.text(left_w / 2, -0.1, 'the attention part\n4 grids', fontsize=10.5,
            ha='center', va='top', color=LINK, weight='bold')
    ax.text(x0 + right_w / 2, -0.1, 'the middle layer, four times wider\n'
            '8 grids of the same area', fontsize=10.5, ha='center', va='top',
            color=WRIST, weight='bold')
    ax.text((x0 + right_w) / 2, 6.0, f'every grid is {STACK_WIDTH:,} by '
            f'{STACK_WIDTH:,} = {_commas(per_grid)} numbers', fontsize=11,
            ha='center', va='bottom', color=INK)
    ax.text((x0 + right_w) / 2, -2.4, f'one block: {BLOCK_GRIDS} x '
            f'{_commas(per_grid)} = {_commas(per_block)}', fontsize=11.5,
            ha='center', va='top', color=INK)
    ax.text((x0 + right_w) / 2, -3.3, f'{STACK_BLOCKS} blocks: {STACK_BLOCKS} x '
            f'{_commas(per_block)} = {_commas(total)} parameters', fontsize=12.5,
            ha='center', va='top', color=INK, weight='bold')
    _title(fig, f'One block of a stack {STACK_WIDTH:,} numbers wide is twelve '
                'square grids', size=12.5)
    _save(fig, DOC3, 'block-of-twelve-grids.svg')


def answer_cost_counts() -> None:
    """Multiplications and additions for one answer, printed for the prose."""
    for label, sizes in (('a fitted straight line', LINE_SIZES),
                         ('a three-weight model', (3, 1)),
                         ('the tiny network 3 -> 8 -> 1', TINY_SIZES),
                         ('the 64 by 64 picture network', PICTURE_SIZES)):
        macs = _mlp_macs(sizes)
        print(f'[answer] {label}: {_commas(macs)} multiply-adds for one answer, '
              f'which is {_commas(macs)} multiplications and {_commas(macs)} '
              f'additions, so {_commas(2 * macs)} operations')
    passes, examples = 400, 800
    one = _mlp_macs((3, 1)) * 2
    forward = passes * examples * one
    print(f'[answer] {passes} passes x {examples} examples x {one} operations = '
          f'{_commas(forward)} operations in the forward passes of training, '
          f'which is {_commas(passes * examples)} times one answer')


# --------------------------------------------------------------------------
# 03, section 3: why the hardware is built for this one operation
# --------------------------------------------------------------------------

MATMUL_SIZES: list[int] = [16, 64, 256, 1024, 4096]


def work_per_number() -> None:
    """Multiply-adds done for every number moved, for a square multiply and for adding."""
    for n in MATMUL_SIZES:
        macs = n ** 3
        moved = 3 * n * n
        print(f'[intensity] {n} by {n}: {_commas(macs)} multiply-adds, '
              f'{_commas(moved)} numbers moved, {macs / moved:.1f} multiply-adds '
              f'per number moved')
    print('[intensity] adding two grids together: 1 add per 3 numbers moved = 0.33, '
          'whatever the size')

    ns = np.array(MATMUL_SIZES, dtype=float)
    fine = np.logspace(np.log10(8), np.log10(8192), 200)
    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(fine, fine / 3.0, color=LINK, lw=2.2, label='matrix multiply')
    ax.plot(fine, np.full_like(fine, 1 / 3), color=GRIP, lw=2.2,
            label='adding two grids together')
    ax.scatter(ns, ns / 3.0, color=LINK, zorder=5, s=36)
    for n in MATMUL_SIZES:
        ax.annotate(f'{n} by {n}\n{n / 3:.0f} per number', (n, n / 3),
                    textcoords='offset points', xytext=(8, -4), fontsize=9,
                    color=LINK, ha='left', va='top')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(8, 20000)
    ax.set_ylim(0.1, 5000)
    ax.set_xlabel('size of the square grids being multiplied (log scale)', fontsize=10)
    ax.set_ylabel('multiply-adds done for each number moved (log scale)', fontsize=10)
    ax.set_title('The bigger the multiply, the more arithmetic the machine gets out of '
                 'each number it fetches', fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, DOC3, 'work-per-number.svg')


BLOCK_SIZES: tuple[int, ...] = (1, 2, 4, 8, 16)
INNER_LENGTH: int = 512


def _block_rows() -> list[tuple[int, int, int, float]]:
    """Numbers loaded and multiply-adds done for one square block of the answer."""
    rows = []
    for t in BLOCK_SIZES:
        loads = 2 * t * INNER_LENGTH
        products = t * t * INNER_LENGTH
        rows.append((t, loads, products, products / loads))
    return rows


def squares_are_independent() -> None:
    """Every square of the answer can be worked out at the same moment as the rest."""
    side = 8
    print(f'[independent] an {side} by {side} answer has {side * side} squares, and '
          f'each one needs only its own row and its own column')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax, (-10.8, 19.2), (-3.2, 10.0))
    cell = 1.0
    units = np.arange(side * side).reshape(side, side)
    faces = [[to_hex(plt.get_cmap('Blues')(0.10 + 0.32 * ((r + c) % 2)))
              for c in range(side)] for r in range(side)]
    _grid_at(ax, units.astype(float), 0.0, 8.6, cell=cell, fmt='{:.0f}', faces=faces,
             size=7.5)
    ax.text(side * cell / 2, 8.8, f'the answer: {side * side} squares', fontsize=11,
            ha='center', va='bottom', color=INK, weight='bold')
    ax.text(side * cell / 2, -0.4, 'the number in each square is the multiply-add unit '
            'that takes it,\nso all 64 squares are worked out at the same moment',
            fontsize=10.5, ha='center', va='top', color=INK)

    # one square on the right edge and one on the left edge, each labelled outwards
    _frame(ax, 7 * cell, 8.6 - 1 * cell, cell, cell, colour=GRIP, lw=2.6)
    _arrow(ax, (8.1, 8.1), (9.4, 8.1), colour=GRIP, lw=1.4)
    ax.text(9.7, 8.1, 'square 15 reads row 1 of the left grid\n'
            'and column 7 of the right grid', fontsize=10, ha='left', va='center',
            color=GRIP)
    _frame(ax, 0.0, 8.6 - 6 * cell, cell, cell, colour=PURPLE, lw=2.6)
    _arrow(ax, (-0.1, 2.1), (-1.4, 2.1), colour=PURPLE, lw=1.4)
    ax.text(-1.7, 2.1, 'square 48 reads row 6 of the left grid\n'
            'and column 0 of the right grid', fontsize=10, ha='right', va='center',
            color=PURPLE)
    _title(fig, 'Why thousands of units can share the work: no square of the answer '
                'reads another square')
    _save(fig, DOC3, 'squares-are-independent.svg')


def tiles_reuse() -> None:
    """One block of the answer reuses the rows and columns it loads."""
    for t, loads, products, ratio in _block_rows():
        print(f'[tile] a {t} by {t} block with inner length {INNER_LENGTH}: loads '
              f'{_commas(loads)} numbers, does {_commas(products)} multiply-adds, '
              f'{ratio:.1f} per number loaded')

    fig, ax = plt.subplots(figsize=(11.8, 5.0), facecolor='white')
    _blank(ax, (-0.6, 19.0), (-2.4, 7.2))
    cell = 0.62
    _grid_at(ax, np.zeros((8, 8)), 0.0, 6.4, cell=cell,
             faces=[['#eef4fa'] * 8 for _ in range(8)], show_text=False)
    ax.text(2.48, 6.6, 'the answer, 8 by 8', fontsize=10, ha='center', va='bottom',
            color=INK, weight='bold')
    _frame(ax, 2 * cell, 6.4 - 2 * cell, 4 * cell, 4 * cell, colour=GRIP, lw=2.4)
    ax.text(2.48, 1.1, 'one 4 by 4 block', fontsize=9.5, ha='center', va='top',
            color=GRIP)

    _grid_at(ax, np.zeros((4, 10)), 6.6, 5.16, cell=cell,
             faces=[['#f7e3e3'] * 10 for _ in range(4)], show_text=False)
    ax.text(6.6 + 3.1, 5.36, '4 rows of the left grid', fontsize=9.5, ha='center',
            va='bottom', color=GRIP)

    _grid_at(ax, np.zeros((10, 4)), 14.6, 6.4, cell=cell,
             faces=[['#f7e3e3'] * 4 for _ in range(10)], show_text=False)
    ax.text(14.6 + 1.24, 6.6, '4 columns of the right grid', fontsize=9.5, ha='center',
            va='bottom', color=GRIP)

    ax.text(9.2, -1.5, 'fetched once, used for all 16 answers in the block',
            fontsize=11, ha='center', va='center', color=INK)
    _title(fig, 'A block of the answer shares the rows and columns it loads')
    _save(fig, DOC3, 'tiles-reuse.svg')


def block_size_table() -> None:
    """How much arithmetic each loaded number earns, against the size of the block."""
    rows = _block_rows()
    fig, ax = plt.subplots(figsize=(8.8, 3.6), facecolor='white')
    _table(ax, ('block of the answer', 'numbers loaded', 'multiply-adds',
                'work per number loaded'),
           [(f'{t} by {t}', _commas(loads), _commas(products), f'{ratio:.1f}')
            for t, loads, products, ratio in rows],
           (2.3, 2.2, 2.2, 2.6), highlight=4, size=10.0, head_size=9.5)
    ax.text(0.5, -0.08, f'inner length {INNER_LENGTH} in every row', fontsize=9.5,
            ha='center', va='top', color=MUTED, transform=ax.transAxes)
    _title(fig, 'The bigger the block, the more arithmetic each loaded number earns',
           size=12.0)
    fig.tight_layout(rect=(0, 0.04, 1, 0.88))
    _save(fig, DOC3, 'block-size-table.svg')


def almost_all_matmul() -> None:
    """Nearly every piece of arithmetic in a layer pair is part of a matrix multiply."""
    d_in, d_mid, d_out = 768, 3072, 768
    mac1 = d_in * d_mid
    mac2 = d_mid * d_out
    bias = d_mid + d_out
    relu = d_mid
    total = mac1 + mac2 + bias + relu
    share = (mac1 + mac2) / total
    print(f'[share] 768 -> 3072 -> 768 for one example: multiply-adds '
          f'{_commas(mac1 + mac2)}, bias adds {_commas(bias)}, ReLU comparisons '
          f'{_commas(relu)}')
    print(f'[share] the two matrix multiplies are {100 * share:.2f} per cent of all '
          f'the arithmetic ({_commas(total)} pieces in all)')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    labels = ['first matrix\nmultiply\n768 x 3072', 'second matrix\nmultiply\n3072 x 768',
              'bias adds', 'ReLU\ncomparisons']
    vals = [mac1, mac2, bias, relu]
    colours = [LINK, LINK, WRIST, SLIDE]
    pos = np.arange(4, dtype=float)
    ax.bar(pos, vals, color=colours, edgecolor=INK, lw=0.6, width=0.62)
    ax.set_yscale('log')
    ax.set_ylim(1, 1e8)
    for p, v in zip(pos, vals):
        ax.text(p, v * 1.4, _commas(v), fontsize=9.5, ha='center', color=INK)
    ax.set_xticks(pos)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel('pieces of arithmetic for one example (log scale)', fontsize=10)
    ax.set_title(f'In a 768 to 3072 to 768 block, the two multiplies are\n'
                 f'{100 * share:.2f} per cent of all the arithmetic', fontsize=12.5,
                 weight='bold')
    _save(fig, DOC3, 'almost-all-matmul.svg')


BLOCK_WIDTHS: list[int] = [64, 128, 256, 512, 768, 1536, 3072]


def matmul_share_vs_width() -> None:
    """The wider the block, the larger the matrix multiply's share of the arithmetic."""
    shares = []
    for d in BLOCK_WIDTHS:
        macs = 2 * 4 * d * d
        other = 4 * d + d + 4 * d
        shares.append(100 * macs / (macs + other))
        print(f'[share] a {d} -> {4 * d} -> {d} block: matrix multiplies are '
              f'{100 * macs / (macs + other):.3f} per cent of the arithmetic')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(BLOCK_WIDTHS, shares, marker='o', color=LINK, lw=2.2)
    for d, s in zip(BLOCK_WIDTHS, shares):
        if d in (64, 256, 768, 3072):
            ax.annotate(f'{s:.2f}%', (d, s), textcoords='offset points',
                        xytext=(0, -18), fontsize=10, color=LINK, ha='center')
    ax.set_xscale('log')
    ax.set_xticks(BLOCK_WIDTHS)
    ax.set_xticklabels([str(d) for d in BLOCK_WIDTHS], fontsize=9.5)
    ax.minorticks_off()
    ax.set_ylim(97.5, 100.1)
    ax.set_xlabel('width of the block, with the middle layer four times as wide '
                  '(log scale)', fontsize=10)
    ax.set_ylabel('share of the arithmetic that is\nthe matrix multiply, per cent',
                  fontsize=10)
    ax.set_title('Making the block wider makes the matrix multiply\'s share larger',
                 fontsize=12, weight='bold')
    _save(fig, DOC3, 'matmul-share-vs-width.svg')


# --------------------------------------------------------------------------
# 03, section 4: the batch dimension
# --------------------------------------------------------------------------

def batch_of_four() -> None:
    """Four arm readings through the same small layer in one multiply."""
    rng = np.random.default_rng(11)
    readings = np.round(rng.uniform(-90, 90, (4, 7)), 0) + 0.0
    readings[readings == 0] = 0.0
    weights = np.round(rng.normal(0, 0.5, (7, 3)), 1) + 0.0
    out = (readings / 90.0) @ weights
    print(f'[batch4] four readings, shape {readings.shape}, times weights, shape '
          f'{weights.shape}, gives shape {out.shape}')
    print(f'[batch4] readings (degrees) =\n{readings}')
    print(f'[batch4] weights =\n{weights}')
    print(f'[batch4] answer (readings divided by 90, then multiplied) =\n'
          f'{np.round(out, 2)}')

    fig, ax = plt.subplots(figsize=(13.0, 5.4), facecolor='white')
    _blank(ax, (-2.6, 23.0), (-6.6, 4.6))
    cell = 1.1
    _grid_at(ax, readings, 0.0, 3.2, cell=cell, fmt='{:.0f}',
             faces=_faces(readings, vmin=-90, vmax=90), size=8.5)
    ax.text(3.85, 3.5, 'four arm readings, shape (4, 7)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')
    for r in range(4):
        ax.text(-0.25, 3.2 - (r + 0.5) * cell, f'reading {r}', fontsize=8.5, ha='right',
                va='center', color=MUTED)
    ax.text(3.85, -1.5, 'one row per example, seven joint angles in degrees',
            fontsize=9.5, ha='center', va='top', color=MUTED)

    ax.text(8.6, 1.0, 'x', fontsize=13, ha='center', va='center', color=MUTED)

    x0 = 10.0
    _grid_at(ax, weights, x0, 3.2, cell=cell, fmt='{:+.1f}',
             faces=_faces(weights, cmap='RdBu', vmin=-1.2, vmax=1.2), size=8.5)
    ax.text(x0 + 1.65, 3.5, 'weights, shape (7, 3)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')
    ax.text(x0 + 1.65, -5.0, 'the same weights for every example', fontsize=9.5,
            ha='center', va='top', color=MUTED)

    _arrow(ax, (14.2, 1.0), (15.4, 1.0))
    x0 = 15.8
    _grid_at(ax, out, x0, 3.2, cell=cell, fmt='{:+.2f}',
             faces=_faces(out, cmap='RdBu', vmin=-2, vmax=2), size=8.5)
    ax.text(x0 + 1.65, 3.5, 'answer, shape (4, 3)', fontsize=10, ha='center',
            va='bottom', color=INK, weight='bold')
    ax.text(x0 + 1.65, -1.5, 'one row per example, still four examples',
            fontsize=9.5, ha='center', va='top', color=MUTED)
    _title(fig, 'The batch is the first number of the shape: four examples go through '
                'the layer in one multiply')
    _save(fig, DOC3, 'batch-of-four.svg')


BATCHES: list[int] = [1, 2, 4, 8, 16, 32, 64, 128, 256]


def per_example_traffic() -> None:
    """Numbers moved for each example as the batch grows, for a 768 -> 3072 layer."""
    d_in, d_out = 768, 3072
    weights = d_in * d_out
    per_example, intensity = [], []
    for b in BATCHES:
        moved = b * d_in + weights + b * d_out
        per_example.append(moved / b)
        intensity.append(b * d_in * d_out / moved)
        print(f'[traffic] batch {b:>4}: {_commas(moved)} numbers moved in all, '
              f'{moved / b:,.0f} per example, {b * d_in * d_out / moved:.1f} '
              f'multiply-adds per number moved')
    one_at_a_time = 1024 * (d_in + weights + d_out)
    all_together = 1024 * d_in + weights + 1024 * d_out
    print(f'[traffic] 1,024 examples one at a time move {_commas(one_at_a_time)} '
          f'numbers; all together they move {_commas(all_together)}, which is '
          f'{one_at_a_time / all_together:.0f} times fewer')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(BATCHES, per_example, marker='o', color=LINK, lw=2.2)
    for b, v in zip(BATCHES, per_example):
        if b in (1, 8, 64, 256):
            ax.annotate(f'{v:,.0f}', (b, v), textcoords='offset points',
                        xytext=(6, 6), fontsize=9.5, color=LINK)
    ax.axhline(d_in + d_out, color=SLIDE, ls='--', lw=1.4)
    ax.text(1.1, d_in + d_out * 1.6, f'the floor: {d_in + d_out:,} numbers,\n'
            'the example going in and the answer coming out', fontsize=9.5,
            color=SLIDE, va='bottom')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(BATCHES)
    ax.set_xticklabels([str(b) for b in BATCHES], fontsize=9)
    ax.minorticks_off()
    ax.set_xlabel('how many examples go through together (log scale)', fontsize=10)
    ax.set_ylabel('numbers moved for each example (log scale)', fontsize=10)
    ax.set_title('A layer of 768 inputs and 3,072 neurons: the weights are read once '
                 'for the whole group', fontsize=12, weight='bold')
    _save(fig, DOC3, 'per-example-traffic.svg')


def traffic_one_at_a_time() -> None:
    """The same 1,024 examples, sent singly and sent together."""
    d_in, d_out = 768, 3072
    weights = d_in * d_out
    one_at_a_time = 1024 * (d_in + weights + d_out)
    all_together = 1024 * d_in + weights + 1024 * d_out
    print(f'[traffic] 1,024 examples one at a time move {_commas(one_at_a_time)} '
          f'numbers; all together they move {_commas(all_together)}, which is '
          f'{one_at_a_time / all_together:.0f} times fewer')

    fig, ax = plt.subplots(figsize=(8.8, 5.0), facecolor='white')
    _plain(ax)
    ax.bar([0, 1], [one_at_a_time, all_together], color=[GRIP, SLIDE], width=0.5,
           edgecolor=INK, lw=0.6)
    ax.set_yscale('log')
    ax.set_ylim(1e5, 1e11)
    ax.set_xlim(-0.7, 1.7)
    for p, v in zip((0, 1), (one_at_a_time, all_together)):
        ax.text(p, v * 1.6, _commas(v), fontsize=11, ha='center', color=INK,
                weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['1,024 examples,\none at a time', '1,024 examples,\nall at once'],
                       fontsize=10.5)
    ax.set_ylabel('numbers moved in all (log scale)', fontsize=10)
    ax.set_title(f'The same arithmetic either way, and '
                 f'{one_at_a_time / all_together:.0f} times less traffic one way',
                 fontsize=12, weight='bold')
    _save(fig, DOC3, 'traffic-one-at-a-time.svg')


def weights_share_of_traffic() -> None:
    """How much of the traffic is weights rather than examples, at two batch sizes."""
    d_in, d_out = 768, 3072
    weights = d_in * d_out
    fig, ax = plt.subplots(figsize=(9.0, 5.0), facecolor='white')
    _plain(ax)
    for i, b in enumerate((1, 256)):
        carried = b * (d_in + d_out)
        moved = carried + weights
        print(f'[dominate] batch {b}: {_commas(weights)} of the {_commas(moved)} '
              f'numbers moved are weights, which is {100 * weights / moved:.1f} '
              f'per cent')
        ax.bar(i, weights, color=PURPLE, edgecolor=INK, lw=0.6, width=0.5)
        ax.bar(i, carried, bottom=weights, color=TEAL, edgecolor=INK, lw=0.6,
               width=0.5)
        ax.text(i, weights / 2, f'the weights\n{_commas(weights)}\n'
                f'{100 * weights / moved:.1f}%', fontsize=10, ha='center',
                va='center', color='white', weight='bold')
        ax.text(i, weights + carried / 2 + 60000,
                f'the examples and\ntheir answers\n{_commas(carried)}', fontsize=9.5,
                ha='center', va='center', color=INK)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['batch 1: one example', 'batch 256: 256 examples'],
                       fontsize=10.5)
    ax.set_xlim(-0.7, 1.7)
    ax.set_ylabel('numbers moved for one pass through the layer', fontsize=10)
    ax.set_title('At batch 1 the machine is almost entirely fetching weights',
                 fontsize=12, weight='bold')
    _save(fig, DOC3, 'weights-share-of-traffic.svg')


VISION_STAGES: list[tuple[str, tuple[int, int, int]]] = [
    ('the photo', (3, 224, 224)),
    ('after stage 1', (32, 112, 112)),
    ('after stage 2', (64, 56, 56)),
    ('after stage 3', (128, 28, 28)),
    ('after stage 4', (256, 14, 14)),
]
VISION_CONVS: list[tuple[int, int]] = [(3, 32), (32, 64), (64, 128), (128, 256)]


def batch_memory() -> None:
    """Weights stay the same size; the numbers passing through grow with the batch."""
    per_example = sum(int(np.prod(s)) for _, s in VISION_STAGES)
    weights = sum(c_in * c_out * 9 + c_out for c_in, c_out in VISION_CONVS)
    print(f'[memory] the five stages hold {_commas(per_example)} numbers for one '
          f'photo, which is {per_example * 4 / 1e6:.2f} MB at float32')
    print(f'[memory] the four sets of filters hold {_commas(weights)} numbers, '
          f'{weights * 4 / 1e6:.2f} MB at float32')
    for b in (1, 8, 32, 128, 256):
        print(f'[memory] batch {b:>3}: {per_example * b * 4 / 1e6:,.0f} MB of numbers '
              f'passing through, against {weights * 4 / 1e6:.2f} MB of weights')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    bs = np.array(BATCHES, dtype=float)
    act_mb = per_example * bs * 4 / 1e6
    ax.plot(bs, act_mb, marker='o', color=TEAL, lw=2.2,
            label='the numbers passing through')
    ax.axhline(weights * 4 / 1e6, color=PURPLE, ls='--', lw=1.8,
               label=f'the weights: {weights * 4 / 1e6:.2f} MB, whatever the batch')
    for b, v in zip(BATCHES, act_mb):
        if b in (1, 16, 256):
            off, align = ((10, -6), 'left') if b == 1 else ((-6, 9), 'right')
            ax.annotate(f'{v:,.1f} MB' if v < 10 else f'{v:,.0f} MB', (b, v),
                        textcoords='offset points', xytext=off, fontsize=9.5,
                        color=TEAL, ha=align)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(BATCHES)
    ax.set_xticklabels([str(b) for b in BATCHES], fontsize=9)
    ax.minorticks_off()
    ax.set_xlabel('how many photos go through together (log scale)', fontsize=10)
    ax.set_ylabel('memory at float32, MB (log scale)', fontsize=10)
    ax.set_title('A bigger batch costs memory, and the model does not grow at all',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC3, 'batch-memory.svg')


def numbers_through_the_stack() -> None:
    """How many numbers one photo and the four stage answers come to."""
    per_example = sum(int(np.prod(s)) for _, s in VISION_STAGES)
    fig, ax = plt.subplots(figsize=(10.2, 4.6), facecolor='white')
    _plain(ax)
    names = [n for n, _ in VISION_STAGES]
    counts = [int(np.prod(s)) for _, s in VISION_STAGES]
    ax.barh(np.arange(len(names)), counts, color=TEAL, edgecolor=INK, lw=0.6,
            height=0.6)
    for i, (c, (_, s)) in enumerate(zip(counts, VISION_STAGES)):
        ax.text(c + 9000, i, f'{s[0]} x {s[1]} x {s[2]} = {c:,}', fontsize=9.5,
                va='center', color=INK)
    ax.set_yticks(np.arange(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlim(0, 640000)
    ax.invert_yaxis()
    ax.set_xlabel('numbers held for one photo', fontsize=10)
    ax.set_title(f'One photo and the four stage answers come to {per_example:,} '
                 f'numbers', fontsize=12, weight='bold')
    _save(fig, DOC3, 'numbers-through-the-stack.svg')


def weights_are_not_the_bill() -> None:
    """At a useful batch the numbers passing through dwarf the weights."""
    per_example = sum(int(np.prod(s)) for _, s in VISION_STAGES)
    weights = sum(c_in * c_out * 9 + c_out for c_in, c_out in VISION_CONVS)
    batch = 32
    w_mb = weights * 4 / 1e6
    a_mb = per_example * batch * 4 / 1e6
    print(f'[bill] the small picture network at batch {batch}: {w_mb:.2f} MB of '
          f'weights and {a_mb:.1f} MB of numbers passing through, so the weights '
          f'are {100 * w_mb / (w_mb + a_mb):.1f} per cent of the bill')

    fig, ax = plt.subplots(figsize=(9.0, 5.2), facecolor='white')
    _plain(ax)
    ax.bar(0, w_mb, color=PURPLE, edgecolor=INK, lw=0.6, width=0.5)
    ax.bar(0, a_mb, bottom=w_mb, color=TEAL, edgecolor=INK, lw=0.6, width=0.5)
    ax.annotate(f'the weights: {w_mb:.2f} MB, which is\nonly '
                f'{100 * w_mb / (w_mb + a_mb):.1f} per cent of the bill',
                (0.27, w_mb / 2), xytext=(1.0, 22), fontsize=11, color=PURPLE,
                ha='left', va='center',
                arrowprops={'arrowstyle': '-|>', 'color': PURPLE, 'lw': 1.4})
    ax.annotate(f'the numbers passing through:\n{a_mb:.1f} MB',
                (0.27, w_mb + a_mb / 2), xytext=(1.0, w_mb + a_mb / 2), fontsize=11,
                color=TEAL, ha='left', va='center',
                arrowprops={'arrowstyle': '-|>', 'color': TEAL, 'lw': 1.4})
    ax.set_xticks([0])
    ax.set_xticklabels([f'the small picture network,\n{batch} photos at once'],
                       fontsize=10.5)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(0, 130)
    ax.set_ylabel('memory at float32, MB', fontsize=10)
    ax.set_title('The weights are the floor of the bill, not the bill', fontsize=12.5,
                 weight='bold')
    _save(fig, DOC3, 'weights-are-not-the-bill.svg')


# --------------------------------------------------------------------------
# 03, sections 5 and 6: floating point and the memory bill
# --------------------------------------------------------------------------

def _to_bf16(x: Arr) -> Arr:
    """Round a float32 array to bfloat16 and back, keeping 7 fraction bits."""
    a = np.asarray(x, dtype=np.float32)
    u = a.view(np.uint32).astype(np.uint64)
    lsb = (u >> np.uint64(16)) & np.uint64(1)
    rounded = (u + np.uint64(0x7FFF) + lsb) & np.uint64(0xFFFF0000)
    return rounded.astype(np.uint32).view(np.float32).astype(np.float64)


def _to_f16(x: Arr) -> Arr:
    return np.asarray(x, dtype=np.float16).astype(np.float64)


def _to_f32(x: Arr) -> Arr:
    return np.asarray(x, dtype=np.float32).astype(np.float64)


def _quantise_int8(x: Arr) -> tuple[NDArray[np.int8], float]:
    """Symmetric 8-bit quantisation: one scale for the whole array."""
    scale = float(np.abs(x).max()) / 127.0
    q = np.clip(np.rint(x / scale), -127, 127).astype(np.int8)
    return q, scale


FORMATS: list[tuple[str, int, int, int, int]] = [
    # name, sign bits, exponent bits, fraction bits, bytes
    ('float32', 1, 8, 23, 4),
    ('bfloat16', 1, 8, 7, 2),
    ('float16', 1, 5, 10, 2),
    ('int8', 1, 0, 7, 1),
]


def number_formats() -> None:
    """How the bits of each format are split, and what each one can hold."""
    f32 = np.finfo(np.float32)
    f16 = np.finfo(np.float16)
    print(f'[format] float32: 4 bytes, biggest {float(f32.max):.6e}, smallest normal '
          f'{float(f32.tiny):.6e}, steps of about {2 ** -23:.3e} of the number')
    print(f'[format] float16: 2 bytes, biggest {float(f16.max):.0f}, smallest normal '
          f'{float(f16.tiny):.6e}, steps of about {2 ** -10:.3e} of the number')
    bf_max = float(np.ldexp(2.0 - 2.0 ** -7, 127))   # the largest bfloat16
    print(f'[format] bfloat16: 2 bytes, biggest {bf_max:.6e}, smallest normal '
          f'{float(f32.tiny):.6e}, steps of about {2 ** -7:.3e} of the number')
    print('[format] int8: 1 byte, whole numbers from -127 to 127 only, with one '
          'scale shared by the whole tensor')

    fig, ax = plt.subplots(figsize=(12.4, 5.6), facecolor='white')
    _blank(ax, (-5.0, 34.0), (-2.6, 7.6))
    unit = 0.86
    notes = {
        'float32': f'biggest {float(f32.max):.3e}; steps of 1 part in 8,388,608',
        'bfloat16': f'biggest {bf_max:.3e}; steps of 1 part in 128',
        'float16': f'biggest {float(f16.max):,.0f}; steps of 1 part in 1,024',
        'int8': 'whole numbers -127 to 127, times one shared scale',
    }
    for i, (name, nsign, nexp, nfrac, nbytes) in enumerate(FORMATS):
        y = 6.2 - i * 2.1
        ax.text(-0.4, y + 0.4, name, fontsize=11, ha='right', va='center', color=INK,
                weight='bold')
        x = 0.0
        if name == 'int8':
            _box(ax, x, y, nsign * unit, 0.8, face=GRIP, edge=INK, text='s', size=8,
                 colour='white')
            x += nsign * unit
            _box(ax, x, y, nfrac * unit, 0.8, face=LINK, edge=INK,
                 text=f'{nfrac} bits: the number', size=9, colour='white')
            x += nfrac * unit
        else:
            _box(ax, x, y, nsign * unit, 0.8, face=GRIP, edge=INK, text='s', size=8,
                 colour='white')
            x += nsign * unit
            _box(ax, x, y, nexp * unit, 0.8, face=WRIST, edge=INK,
                 text=f'{nexp} bits: how big', size=9, colour='white')
            x += nexp * unit
            _box(ax, x, y, nfrac * unit, 0.8, face=LINK, edge=INK,
                 text=f'{nfrac} bits: the digits', size=9, colour='white')
            x += nfrac * unit
        ax.text(x + 0.5, y + 0.4, f'{nbytes * 8} bits = {nbytes} '
                f'byte{"s" if nbytes > 1 else ""} for one number', fontsize=10,
                ha='left', va='center', color=INK, weight='bold')
        ax.text(0.0, y - 0.35, notes[name], fontsize=9.5, ha='left', va='top',
                color=MUTED)
    ax.text(0.0, -1.8, 's is the sign bit, which says whether the number is above or '
            'below 0', fontsize=9.5, ha='left', va='top', color=GRIP)
    _title(fig, 'Four ways to spend the bits: how big the number can be, and how many '
                'digits it keeps')
    _save(fig, DOC3, 'number-formats.svg')


def spacing_of_numbers() -> None:
    """The gap to the next number each format can hold, against the size of the number."""
    mags = np.logspace(-3, np.log10(6e4), 71)
    gap32 = np.array([float(np.nextafter(np.float32(m), np.float32(np.inf)) - np.float32(m))
                      for m in mags])
    gap16 = np.array([float(np.nextafter(np.float16(m), np.float16(np.inf)) - np.float16(m))
                      for m in mags])
    gapbf = np.array([float(np.ldexp(1.0, int(np.floor(np.log2(m))) - 7)) for m in mags])
    for m in (0.001, 1.0, 100.0, 1000.0):
        g32 = float(np.nextafter(np.float32(m), np.float32(np.inf)) - np.float32(m))
        g16 = float(np.nextafter(np.float16(m), np.float16(np.inf)) - np.float16(m))
        gbf = float(np.ldexp(1.0, int(np.floor(np.log2(m))) - 7))
        print(f'[spacing] at {m:g}: float32 can tell numbers {g32:.3e} apart, '
              f'bfloat16 {gbf:.3e}, float16 {g16:.3e}')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(mags, gap32, color=LINK, lw=2.2, label='float32 (4 bytes)')
    ax.plot(mags, gapbf, color=PURPLE, lw=2.2, label='bfloat16 (2 bytes)')
    ax.plot(mags, gap16, color=WRIST, lw=2.2, label='float16 (2 bytes)')
    ax.axvline(65504, color=GRIP, ls='--', lw=1.4)
    ax.text(65504 * 0.9, 1e-7, 'float16 stops here,\nat 65,504', fontsize=9,
            color=GRIP, ha='right')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(1e-3, 2e5)
    ax.set_xlabel('the size of the number (log scale)', fontsize=10)
    ax.set_ylabel('gap to the next number the format can hold (log scale)', fontsize=10)
    ax.set_title('Floating point keeps the same number of digits at every size, so the '
                 'gap grows with the number', fontsize=11.5, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, DOC3, 'spacing-of-numbers.svg')


def rounding_error() -> None:
    """What rounding the weights to each format does to a real matrix multiply."""
    rng = np.random.default_rng(21)
    w = rng.normal(0.0, 0.05, 200_000)
    a = rng.normal(0.0, 1.0, (256, 512))
    b = rng.normal(0.0, 0.05, (512, 256))
    ref = a @ b
    denom = float(np.mean(np.abs(ref)))

    names, w_err, m_err = [], [], []
    for name, fn in (('float32', _to_f32), ('bfloat16', _to_bf16), ('float16', _to_f16)):
        rw = fn(w)
        we = float(np.mean(np.abs(rw - w)) / np.mean(np.abs(w)))
        out = fn(a) @ fn(b)
        me = float(np.mean(np.abs(out - ref)) / denom)
        names.append(name)
        w_err.append(100 * we)
        m_err.append(100 * me)
        print(f'[rounding] {name}: the stored weights are out by {100 * we:.4g} per '
              f'cent on average, and the answer of a 256x512 by 512x256 multiply is '
              f'out by {100 * me:.4g} per cent')
    qa, sa = _quantise_int8(a)
    qb, sb = _quantise_int8(b)
    out8 = (qa.astype(np.int32) @ qb.astype(np.int32)).astype(float) * sa * sb
    qw, sw = _quantise_int8(w)
    we8 = float(np.mean(np.abs(qw.astype(float) * sw - w)) / np.mean(np.abs(w)))
    me8 = float(np.mean(np.abs(out8 - ref)) / denom)
    names.append('int8')
    w_err.append(100 * we8)
    m_err.append(100 * me8)
    print(f'[rounding] int8: the stored weights are out by {100 * we8:.4g} per cent '
          f'on average, and the answer is out by {100 * me8:.4g} per cent '
          f'(one scale for the whole tensor)')

    fig, ax = plt.subplots(figsize=(10.8, 5.0), facecolor='white')
    _plain(ax)
    pos = np.arange(len(names), dtype=float)
    ax.bar(pos - 0.2, w_err, width=0.4, color=LINK, edgecolor=INK, lw=0.6,
           label='error in each stored number')
    ax.bar(pos + 0.2, m_err, width=0.4, color=WRIST, edgecolor=INK, lw=0.6,
           label='error in the answer of the multiply')
    ax.set_yscale('log')
    ax.set_ylim(1e-7, 1000)
    for p, v in zip(pos - 0.2, w_err):
        ax.text(p, v * 1.6, f'{v:.4g}%', fontsize=9, ha='center', color=LINK)
    for p, v in zip(pos + 0.2, m_err):
        ax.text(p, v * 1.6, f'{v:.4g}%', fontsize=9, ha='center', color=WRIST)
    ax.set_xticks(pos)
    ax.set_xticklabels(names, fontsize=10.5)
    ax.set_ylabel('how far out, per cent (log scale)', fontsize=10)
    ax.set_title('Rounding 200,000 made-up weights, and one real 256 by 512 multiply, '
                 'in each format', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC3, 'rounding-error.svg')


def running_total() -> None:
    """Adding up 4,096 made-up squares in each format: one overflows, one stalls."""
    rng = np.random.default_rng(7)
    vals = (rng.normal(0.0, 1.0, 4096) * 50.0) ** 2
    exact = np.cumsum(vals)

    total16 = np.float16(0.0)
    total_bf = 0.0
    run16, runbf = [], []
    first_inf = None
    with np.errstate(over='ignore', invalid='ignore'):
        for i, v in enumerate(vals):
            total16 = np.float16(total16 + np.float16(v))
            total_bf = float(_to_bf16(np.array(
                [total_bf + float(_to_bf16(np.array([v]))[0])]))[0])
            run16.append(float(total16))
            runbf.append(total_bf)
            if first_inf is None and not np.isfinite(float(total16)):
                first_inf = i + 1
    run16 = np.array(run16)
    runbf = np.array(runbf)
    print(f'[total] the exact total of the 4,096 squares is {exact[-1]:,.0f}')
    print(f'[total] float16 runs past its biggest number, 65,504, after '
          f'{first_inf} of them, and from there it holds infinity')
    print(f'[total] bfloat16 reaches {runbf[-1]:,.0f}, which is '
          f'{100 * abs(runbf[-1] - exact[-1]) / exact[-1]:.2f} per cent out')
    print(f'[total] float32 reaches {float(np.float32(np.cumsum(np.float32(vals))[-1])):,.0f}')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    steps = np.arange(1, len(vals) + 1)
    ax.plot(steps, exact, color=LINK, lw=2.4, label='exact total (float32 keeps up)')
    ax.plot(steps, runbf, color=PURPLE, lw=2.0, ls='-',
            label='bfloat16: never overflows, but loses the small additions')
    safe = np.where(np.isfinite(run16), run16, np.nan)
    ax.plot(steps, safe, color=WRIST, lw=2.0, label='float16: stops at 65,504')
    ax.axhline(65504, color=GRIP, ls='--', lw=1.3)
    ax.text(5500, 65504 * 1.35, 'the biggest number float16 holds: 65,504',
            fontsize=9, color=GRIP, ha='right')
    if first_inf is not None:
        ax.axvline(first_inf, color=GRIP, ls=':', lw=1.2)
        ax.annotate(f'after {first_inf} numbers\nfloat16 gives up',
                    (first_inf, 4e3), textcoords='offset points', xytext=(10, 0),
                    fontsize=9, color=GRIP, va='center')
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_ylim(1e3, 3e7)
    ax.set_xlim(1, 6000)
    ax.set_xlabel('how many of the 4,096 squares have been added so far (log scale)',
                  fontsize=10)
    ax.set_ylabel('the running total (log scale)', fontsize=10)
    ax.set_title('Adding up 4,096 simulated squares: the range matters more than the '
                 'digits', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC3, 'running-total.svg')


def mixed_precision() -> None:
    """Small numbers going in, a large running total inside, small numbers coming out."""
    print('[mixed] the stored weights and inputs are 2 bytes each, the running total '
          'inside the multiplier is 4 bytes, and the answer is written back as '
          '2 bytes')

    fig, ax = plt.subplots(figsize=(12.0, 4.0), facecolor='white')
    _blank(ax, (-0.8, 28.0), (-1.6, 6.4))

    _box(ax, 0.0, 1.4, 5.6, 2.2, face='#e9e4f5', edge=PURPLE, lw=1.6,
         text='the weights and\nthe inputs\n2 bytes each', size=10, colour=INK)
    ax.text(2.8, 1.1, 'bfloat16: wide range,\nfew digits', fontsize=9.5, ha='center',
            va='top', color=PURPLE)

    _arrow(ax, (5.9, 2.5), (8.3, 2.5), colour=MUTED, lw=1.8)

    _box(ax, 8.6, 0.6, 9.4, 3.8, face='#e3f1f1', edge=TEAL, lw=1.8,
         text='multiply, then add into\na running total kept in\nfloat32: 4 bytes',
         size=10.5, colour=INK)
    ax.text(13.3, 0.3, 'the total can grow large without overflowing,\n'
            'and small products still change it', fontsize=9.5, ha='center',
            va='top', color=TEAL)

    _arrow(ax, (18.3, 2.5), (20.7, 2.5), colour=MUTED, lw=1.8)

    _box(ax, 21.0, 1.4, 5.6, 2.2, face='#e9e4f5', edge=PURPLE, lw=1.6,
         text='the answer, rounded\nback to 2 bytes', size=10, colour=INK)
    ax.text(23.8, 1.1, 'so the next layer\nreads 2 bytes too', fontsize=9.5,
            ha='center', va='top', color=PURPLE)

    ax.text(13.3, 5.2, 'stored small, added up large', fontsize=13, ha='center',
            va='bottom', color=INK, weight='bold')
    _save(fig, DOC3, 'mixed-precision.svg')


MODEL_SIZES: list[tuple[str, int]] = [
    ('a small robot model\n25 million parameters', 25_000_000),
    ('a middling model\n350 million parameters', 350_000_000),
    ('a large model\n7 billion parameters', 7_000_000_000),
]
PRECISIONS: list[tuple[str, int]] = [('float32', 4), ('bfloat16', 2), ('float16', 2),
                                     ('int8', 1)]


def memory_bill() -> None:
    """A 7 billion parameter model's weights, in gigabytes, at each precision."""
    n = 7_000_000_000
    vals = []
    for name, nbytes in PRECISIONS:
        gb = _gb(n, nbytes)
        vals.append(gb)
        print(f'[bill] 7,000,000,000 parameters at {name}: {n} x {nbytes} = '
              f'{_commas(n * nbytes)} bytes = {gb:.1f} GB '
              f'({n * nbytes / 2 ** 30:.2f} GiB)')
    print(f'[bill] four bits a parameter would be {_gb(n, 1) / 2:.1f} GB')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    labels = [f'{nm}\n{nb} byte{"s" if nb > 1 else ""} each' for nm, nb in PRECISIONS]
    pos = np.arange(len(vals), dtype=float)
    ax.bar(pos, vals, color=[LINK, PURPLE, WRIST, SLIDE], edgecolor=INK, lw=0.6,
           width=0.6)
    for p, v in zip(pos, vals):
        ax.text(p, v + 0.6, f'{v:.0f} GB', fontsize=11.5, ha='center', color=INK,
                weight='bold')
    ax.set_xticks(pos)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 33)
    ax.set_ylabel('memory for the weights alone, GB', fontsize=10)
    ax.set_title('A model with 7 billion parameters: the same model, four times the '
                 'memory from one end to the other', fontsize=11.5, weight='bold')
    _save(fig, DOC3, 'memory-bill.svg')


def three_sizes() -> None:
    """The same sum for three model sizes, as a grid of gigabytes."""
    rows = []
    for label, n in MODEL_SIZES:
        cells = []
        for name, nbytes in PRECISIONS:
            gb = _gb(n, nbytes)
            cells.append(f'{gb * 1000:,.0f} MB' if gb < 1 else f'{gb:.1f} GB')
            print(f'[sizes] {label.replace(chr(10), ", ")} at {name}: {gb:.3f} GB')
        rows.append((label.split('\n')[1], *cells))

    fig, ax = plt.subplots(figsize=(10.6, 3.4), facecolor='white')
    _table(ax, ('model size', *[nm for nm, _ in PRECISIONS]), rows,
           (3.4, 2.0, 2.0, 2.0, 2.0), size=10.5, head_size=10.5)
    _title(fig, 'The weights alone, in gigabytes: parameter count times bytes '
                'per number', size=12.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.86))
    _save(fig, DOC3, 'three-sizes.svg')


def _bytes_text(nbytes: int) -> str:
    """A byte count, with the same count in MB or GB under it where that helps."""
    if nbytes < 1_000_000:
        return f'{_commas(nbytes)} bytes'
    if nbytes < 1_000_000_000:
        return f'{_commas(nbytes)} bytes\n{nbytes / 1e6:.2f} MB'
    return f'{_commas(nbytes)} bytes\n{nbytes / 1e9:.2f} GB'


def four_models_in_bytes() -> None:
    """The same sum, count times bytes, for the four models of section 2."""
    models = [('a fitted straight line', _mlp_params(LINE_SIZES)),
              ('a tiny network, 3 -> 8 -> 1', _mlp_params(TINY_SIZES)),
              ('a 64 by 64 picture network', _mlp_params(PICTURE_SIZES)),
              ('a stack of 48 blocks, 2,048 wide', _stack_params())]
    rows = []
    for label, n in models:
        cells = [label, _commas(n)]
        for _, nbytes in (('four bytes', 4), ('two bytes', 2), ('one byte', 1)):
            total = n * nbytes
            cells.append(_bytes_text(total))
            print(f'[store] {label}: {_commas(n)} x {nbytes} = {_commas(total)} '
                  f'bytes = {total / 1e6:,.3f} MB = {total / 1e9:,.3f} GB '
                  f'({total / 2 ** 20:,.3f} MiB, {total / 2 ** 30:,.3f} GiB)')
        rows.append(tuple(cells))

    fig, ax = plt.subplots(figsize=(13.2, 4.2), facecolor='white')
    _table(ax, ('the model', 'parameters', 'at four bytes each',
                'at two bytes each', 'at one byte each'), rows,
           (4.0, 2.8, 3.1, 3.1, 3.1), size=10.0, head_size=10.0)
    _title(fig, 'The weights of four models: the parameter count multiplied by the '
                'bytes each parameter takes', size=12.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.86))
    _save(fig, DOC3, 'four-models-in-bytes.svg')


def does_it_fit() -> None:
    """Which precisions let a 7 billion parameter model sit on a given computer."""
    n = 7_000_000_000
    limits = [(8, 'a small robot computer, 8 GB'),
              (16, 'a laptop graphics card, 16 GB'),
              (24, 'a desktop graphics card, 24 GB'),
              (48, 'a big card, 48 GB')]
    vals = [_gb(n, nb) for _, nb in PRECISIONS]
    for (name, nb), gb in zip(PRECISIONS, vals):
        fits = [text for lim, text in limits if gb <= lim]
        print(f'[fit] at {name} the weights need {gb:.0f} GB and fit on: '
              f'{", ".join(fits) if fits else "none of the four"}')

    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _plain(ax)
    pos = np.arange(len(vals), dtype=float)
    ax.bar(pos, vals, color=[LINK, PURPLE, WRIST, SLIDE], edgecolor=INK, lw=0.6,
           width=0.55)
    for p, v in zip(pos, vals):
        ax.text(p, v - 2.6, f'{v:.0f} GB', fontsize=11, ha='center', color='white',
                weight='bold')
    for lim, text in limits:
        ax.plot([-0.6, 3.5], [lim, lim], color=MUTED, ls='--', lw=1.2)
        ax.text(3.6, lim, text, fontsize=9.5, color=MUTED, va='center', ha='left')
    ax.set_xticks(pos)
    ax.set_xticklabels([nm for nm, _ in PRECISIONS], fontsize=10.5)
    ax.set_xlim(-0.6, 6.4)
    ax.set_ylim(0, 54)
    ax.set_ylabel('memory for the weights alone, GB', fontsize=10)
    ax.set_title('Where a 7 billion parameter model fits: the precision decides which '
                 'machines can hold it', fontsize=11.5, weight='bold')
    _save(fig, DOC3, 'does-it-fit.svg')


# ==========================================================================
# 04_what-a-network-can-learn
# ==========================================================================

# A made-up target curve, chosen because it bends in several places.
X_LO, X_HI = 0.0, 4.0
X_FINE: Arr = np.linspace(X_LO, X_HI, 401)


def _target(x: Arr) -> Arr:
    return 1.2 + 0.8 * x - 0.35 * x ** 2 + 0.9 * np.sin(2.2 * x)


Y_FINE: Arr = _target(X_FINE)


def _features(x: Arr, knots: Arr | list[float]) -> Arr:
    """A straight line plus one rectified-linear bend at each knot."""
    cols = [np.ones_like(x), x] + [np.maximum(0.0, x - k) for k in knots]
    return np.stack(cols, axis=1)


def _even_knots(width: int) -> Arr:
    return np.linspace(X_LO, X_HI, width + 2)[1:-1] if width > 0 else np.array([])


def _fit(knots: Arr | list[float], xs: Arr, ys: Arr) -> Arr:
    """The output weights that put the bent line as close to the points as it goes."""
    coef, *_ = np.linalg.lstsq(_features(xs, knots), ys, rcond=None)
    return coef


def _predict(knots: Arr | list[float], coef: Arr, xs: Arr) -> Arr:
    return _features(xs, knots) @ coef


def _fit_width(width: int) -> tuple[Arr, Arr, Arr, float]:
    """Fit the target curve itself with `width` bends, evenly spread."""
    knots = _even_knots(width)
    coef = _fit(knots, X_FINE, Y_FINE)
    pred = _predict(knots, coef, X_FINE)
    return knots, coef, pred, float(np.mean(np.abs(pred - Y_FINE)))


def straight_line_fails() -> None:
    """The best straight line through a bending curve, and how far out it is."""
    knots, coef, pred, gap = _fit_width(0)
    worst = int(np.argmax(np.abs(pred - Y_FINE)))
    sign = '-' if coef[1] < 0 else '+'
    print(f'[line] the best straight line is y = {coef[0]:.2f} {sign} '
          f'{abs(coef[1]):.2f} x')
    print(f'[line] it is {gap:.3f} away from the curve on average and '
          f'{abs(pred[worst] - Y_FINE[worst]):.3f} away at its worst, at x = '
          f'{X_FINE[worst]:.2f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(X_FINE, Y_FINE, color=LINK, lw=2.6, label='the curve to be matched')
    ax.plot(X_FINE, pred, color=GRIP, lw=2.2,
            label=f'the best straight line: y = {coef[0]:.2f} {sign} '
                  f'{abs(coef[1]):.2f} x')
    ax.fill_between(X_FINE, Y_FINE, pred, color=GRIP, alpha=0.12)
    ax.plot([X_FINE[worst], X_FINE[worst]], [Y_FINE[worst], pred[worst]], color=INK,
            lw=1.4, ls=':')
    ax.annotate(f'the worst gap: {abs(pred[worst] - Y_FINE[worst]):.2f}',
                (X_FINE[worst], (Y_FINE[worst] + pred[worst]) / 2),
                textcoords='offset points', xytext=(12, 0), fontsize=9.5, color=INK,
                va='center')
    ax.set_xlabel('the number going in', fontsize=10)
    ax.set_ylabel('the number wanted out', fontsize=10)
    ax.set_title(f'A straight line has nothing to bend with, so it is {gap:.2f} out on '
                 'average', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, DOC4, 'straight-line-fails.svg')


def two_multiplies_collapse() -> None:
    """Two matrix multiplies in a row do the same thing as one, so depth alone is free."""
    a = np.array([[0.5, -0.2, 0.8], [-0.3, 0.6, 0.2]])
    b = np.array([[1.0, -0.5], [0.4, 0.2], [-0.6, 0.9]])
    x = np.array([2.0, 1.0])
    first = x @ a                 # shape (3,)
    second = first @ b            # shape (2,)
    joined = a @ b                # shape (2, 2)
    direct = x @ joined
    print(f'[collapse] first multiply: {x.tolist()} times a (2, 3) grid = '
          f'{np.round(first, 2).tolist()}')
    print(f'[collapse] second multiply: that times a (3, 2) grid = '
          f'{np.round(second, 2).tolist()}')
    print(f'[collapse] the two grids multiplied together =\n{np.round(joined, 2)}')
    print(f'[collapse] one multiply by that single grid gives '
          f'{np.round(direct, 2).tolist()}, the same answer')

    fig, ax = plt.subplots(figsize=(12.4, 5.2), facecolor='white')
    _blank(ax, (-1.2, 25.2), (-6.7, 3.6))
    cell = 1.15

    def label(cx: float, cy: float, text: str, colour: str = INK,
              size: float = 9.5, weight: str = 'normal') -> None:
        ax.text(cx, cy, text, fontsize=size, ha='center', va='top', color=colour,
                weight=weight)

    # top row: two multiplies, one after the other
    _grid_at(ax, x.reshape(1, 2), 0.0, 2.6, cell=cell, fmt='{:.0f}',
             faces=_faces(x.reshape(1, 2), vmin=-2, vmax=2), size=9.5)
    label(cell, 1.25, 'the input\n(1, 2)', MUTED)
    ax.text(2.9, 2.0, 'x', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, a, 3.6, 2.6, cell=cell, fmt='{:+.1f}',
             faces=_faces(a, cmap='RdBu', vmin=-1, vmax=1), size=9.0)
    label(3.6 + 1.5 * cell, 2.6 - 2 * cell - 0.15, 'first grid\n(2, 3)', MUTED)
    ax.text(8.0, 2.0, '=', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, first.reshape(1, 3), 8.7, 2.6, cell=cell, fmt='{:+.2f}',
             faces=_faces(first.reshape(1, 3), cmap='RdBu', vmin=-2, vmax=2), size=8.5)
    label(8.7 + 1.5 * cell, 1.25, 'in between\n(1, 3)', MUTED)
    ax.text(12.9, 2.0, 'x', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, b, 13.6, 2.6, cell=cell, fmt='{:+.1f}',
             faces=_faces(b, cmap='RdBu', vmin=-1, vmax=1), size=9.0)
    label(13.6 + cell, 2.6 - 3 * cell - 0.15, 'second grid\n(3, 2)', MUTED)
    ax.text(17.2, 2.0, '=', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, second.reshape(1, 2), 17.9, 2.6, cell=cell, fmt='{:+.2f}',
             faces=_faces(second.reshape(1, 2), cmap='RdBu', vmin=-2, vmax=2),
             size=8.5)
    _frame(ax, 17.9, 2.6, 2 * cell, cell, colour=SLIDE, lw=2.4)
    label(17.9 + cell, 1.25, 'the answer\n(1, 2)', SLIDE, weight='bold')

    ax.text(-0.9, 2.0, 'two\nmultiplies', fontsize=10.5, ha='right', va='center',
            color=INK, weight='bold')

    # bottom row: the two grids multiplied together first
    y = -2.6
    _grid_at(ax, x.reshape(1, 2), 0.0, y, cell=cell, fmt='{:.0f}',
             faces=_faces(x.reshape(1, 2), vmin=-2, vmax=2), size=9.5)
    label(cell, y - cell - 0.15, 'the same input', MUTED)
    ax.text(2.9, y - cell / 2, 'x', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, joined, 3.6, y, cell=cell, fmt='{:+.2f}',
             faces=_faces(joined, cmap='RdBu', vmin=-1, vmax=1), size=8.5)
    _frame(ax, 3.6, y, 2 * cell, 2 * cell, colour=PURPLE, lw=2.4)
    label(3.6 + cell, y - 2 * cell - 0.15, 'the two grids multiplied\ntogether, '
          'worked out once\n(2, 2)', PURPLE, weight='bold')
    ax.text(6.9, y - cell / 2, '=', fontsize=12, ha='center', va='center', color=MUTED)
    _grid_at(ax, direct.reshape(1, 2), 7.6, y, cell=cell, fmt='{:+.2f}',
             faces=_faces(direct.reshape(1, 2), cmap='RdBu', vmin=-2, vmax=2),
             size=8.5)
    _frame(ax, 7.6, y, 2 * cell, cell, colour=SLIDE, lw=2.4)
    label(7.6 + cell, y - cell - 0.15, 'the same answer', SLIDE, weight='bold')

    ax.text(-0.9, y - cell / 2, 'one\nmultiply', fontsize=10.5, ha='right',
            va='center', color=INK, weight='bold')
    ax.text(13.0, y - cell, 'So a second layer with nothing between it and the\n'
            'first adds no new shapes, only arithmetic.', fontsize=10.5,
            ha='left', va='center', color=INK)
    _title(fig, 'Two matrix multiplies with nothing between them are one matrix '
                'multiply')
    _save(fig, DOC4, 'two-multiplies-collapse.svg')


def one_hinge() -> None:
    """What one rectified-linear neuron gives: a flat part and then a slope."""
    x = X_FINE
    plain = np.maximum(0.0, x - 1.5)
    print(f'[hinge] max(0, x - 1.5) is 0 up to x = 1.5 and rises with slope 1 after it; '
          f'at x = 4 it is {plain[-1]:.2f}')

    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor='white')
    _plain(ax)
    ax.set_xlim(X_LO, X_HI)
    ax.axhline(0, color=GRID, lw=1.0)
    ax.plot(x, plain, color=LINK, lw=3.0)
    ax.axvline(1.5, color=MUTED, ls=':', lw=1.3)
    ax.annotate('flat: the total inside the\nneuron is below 0, so the\nReLU gives 0',
                (0.7, 0.35), fontsize=10, color=MUTED, ha='center', va='bottom')
    ax.annotate('rising with slope 1: the ReLU\npasses the total through',
                (3.1, 0.35), fontsize=10, color=LINK, ha='center', va='bottom')
    ax.annotate('the bend, at x = 1.5', (1.5, 2.72), textcoords='offset points',
                xytext=(8, 0), fontsize=10.5, color=INK, ha='left', va='center',
                weight='bold')
    ax.set_ylim(-0.4, 3.0)
    ax.set_xlabel('the number going in', fontsize=10)
    ax.set_ylabel('what comes out', fontsize=10)
    ax.set_title('One rectified-linear neuron: flat, then one bend, then a straight '
                 'rise', fontsize=12, weight='bold')
    _save(fig, DOC4, 'one-hinge.svg')


def hinge_weight() -> None:
    """The same hinge, scaled by three different weights in the layer after it."""
    x = X_FINE
    plain = np.maximum(0.0, x - 1.5)
    for w in (1.0, 2.5, -1.8):
        print(f'[hinge] weight {w:+.1f} on the same hinge: slope {w:+.1f} after the '
              f'bend, reaching {w * plain[-1]:+.2f} at x = 4')

    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor='white')
    _plain(ax)
    ax.set_xlim(X_LO, X_HI)
    ax.axhline(0, color=GRID, lw=1.0)
    ax.axvline(1.5, color=MUTED, ls=':', lw=1.3)
    for w, colour, style in ((1.0, GRID, '-'), (2.5, LINK, '-'), (-1.8, GRIP, '-')):
        ax.plot(x, w * plain, color=colour, lw=2.8, ls=style,
                label=f'weight {w:+.1f}: slope {w:+.1f}')
    ax.text(1.56, 5.6, 'the bend never moves', fontsize=10, color=MUTED, ha='left')
    ax.set_ylim(-5.2, 6.8)
    ax.set_xlabel('the number going in', fontsize=10)
    ax.set_ylabel('what the next layer receives', fontsize=10)
    ax.set_title('The weight after the neuron sets the slope, and its sign sets the '
                 'direction', fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='lower left')
    _save(fig, DOC4, 'hinge-weight.svg')


def three_piece_line() -> None:
    """A straight line plus two rectified-linear neurons: a line in three pieces."""
    x = X_FINE
    steep = 2.5 * np.maximum(0.0, x - 1.5)
    down = -1.8 * np.maximum(0.0, x - 2.6)
    line = 0.4 + 0.5 * x
    joined = line + steep + down
    print(f'[hinge] the line 0.4 + 0.5x plus 2.5 hinge(x - 1.5) minus 1.8 '
          f'hinge(x - 2.6) has slopes 0.50, then 3.00, then 1.20')

    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor='white')
    _plain(ax)
    ax.set_xlim(X_LO, X_HI)
    ax.axhline(0, color=GRID, lw=1.0)
    ax.plot(x, line, color=GRID, lw=2.2, ls='--', label='the line 0.4 + 0.5 x alone')
    ax.plot(x, joined, color=PURPLE, lw=3.0, label='the line plus both neurons')
    for k, slope in ((0.7, '0.50'), (2.0, '3.00'), (3.35, '1.20')):
        i = int(np.argmin(np.abs(x - k)))
        ax.annotate(f'slope {slope}', (k, joined[i]), textcoords='offset points',
                    xytext=(-22, 16), fontsize=10.5, color=PURPLE, ha='center')
    for k in (1.5, 2.6):
        ax.axvline(k, color=MUTED, ls=':', lw=1.3)
        ax.annotate(f'bend at {k}', (k, -0.35), textcoords='offset points',
                    xytext=(4, 0), fontsize=9.5, color=MUTED, ha='left')
    ax.set_ylim(-0.8, 9.2)
    ax.set_xlabel('the number going in', fontsize=10)
    ax.set_ylabel('what comes out', fontsize=10)
    ax.set_title('Two neurons added to a straight line make a line in three pieces',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, DOC4, 'three-piece-line.svg')


def building_with_hinges() -> None:
    """Add the bends one at a time and watch the fit close in on the curve."""
    fig, axes = plt.subplots(1, 4, figsize=(14.0, 4.2), facecolor='white')
    for w, ax in zip((0, 1, 2, 3), axes):
        knots, coef, pred, gap = _fit_width(w)
        slopes = [coef[1]]
        for i in range(len(knots)):
            slopes.append(slopes[-1] + coef[2 + i])
        print(f'[build] {w} bend(s) at {[round(float(k), 2) for k in knots]}: '
              f'average gap {gap:.4f}, piece slopes '
              f'{[round(float(s), 2) for s in slopes]}')
        _plain(ax)
        ax.plot(X_FINE, Y_FINE, color=LINK, lw=2.4)
        ax.plot(X_FINE, pred, color=GRIP, lw=2.2)
        for k in knots:
            ax.axvline(float(k), color=MUTED, ls=':', lw=1.1)
        ax.set_xlim(X_LO, X_HI)
        ax.set_ylim(-1.4, 3.1)
        ax.set_title(f'{w} bend{"" if w == 1 else "s"}: {w + 2} numbers,\n'
                     f'average gap {gap:.3f}', fontsize=10.5, weight='bold')
        ax.set_xlabel('the number going in', fontsize=9)
    axes[0].set_ylabel('the number wanted out', fontsize=9)
    _title(fig, 'Bends added one at a time: the blue curve is the target, the red line '
                'is what the neurons make')
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    _save(fig, DOC4, 'building-with-hinges.svg')


def bends_and_gap() -> None:
    """Where the bends sit matters as much as how many there are."""
    even_knots = _even_knots(3)
    even_gap = _fit_width(3)[3]
    cands = np.linspace(0.1, 3.9, 39)
    best_gap, best_knots = None, None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            for k in range(j + 1, len(cands)):
                kn = [float(cands[i]), float(cands[j]), float(cands[k])]
                coef = _fit(kn, X_FINE, Y_FINE)
                g = float(np.mean(np.abs(_predict(kn, coef, X_FINE) - Y_FINE)))
                if best_gap is None or g < best_gap:
                    best_gap, best_knots = g, kn
    assert best_knots is not None and best_gap is not None
    print(f'[place] three bends spread evenly, at '
          f'{[round(float(k), 2) for k in even_knots]}: average gap {even_gap:.4f}')
    print(f'[place] the best three places, at {[round(k, 2) for k in best_knots]}: '
          f'average gap {best_gap:.4f}, which is '
          f'{even_gap / best_gap:.1f} times closer')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6), facecolor='white')
    for ax, knots, gap, head in (
            (axes[0], list(even_knots), even_gap, 'three bends spread evenly'),
            (axes[1], best_knots, best_gap, 'three bends in the best places')):
        _plain(ax)
        coef = _fit(knots, X_FINE, Y_FINE)
        pred = _predict(knots, coef, X_FINE)
        ax.plot(X_FINE, Y_FINE, color=LINK, lw=2.4, label='the curve to be matched')
        ax.plot(X_FINE, pred, color=GRIP, lw=2.2, label='what three neurons make')
        for k in knots:
            ax.axvline(float(k), color=MUTED, ls=':', lw=1.2)
            ax.annotate(f'bend at {float(k):.1f}', (float(k) + 0.06, -1.25),
                        fontsize=9, color=MUTED, ha='left')
        ax.set_xlim(X_LO, X_HI)
        ax.set_ylim(-1.4, 3.1)
        ax.set_xlabel('the number going in', fontsize=9.5)
        ax.set_title(f'{head}: average gap {gap:.3f}', fontsize=11, weight='bold')
    axes[0].set_ylabel('the number wanted out', fontsize=9.5)
    axes[0].legend(fontsize=9, frameon=False, loc='upper right')
    _title(fig, 'The same three neurons, moved: finding where the bends go is what '
                'training is for')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    _save(fig, DOC4, 'bends-and-gap.svg')


WIDTHS: list[int] = [2, 4, 8, 16, 32, 64]


def wider_fits() -> None:
    """The same curve matched by 4, 16 and 64 bends."""
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), facecolor='white')
    for w, ax in zip((4, 16, 64), axes):
        _, _, pred, gap = _fit_width(w)
        print(f'[wider] {w} bends: average gap {gap:.4f}, worst gap '
              f'{float(np.max(np.abs(pred - Y_FINE))):.4f}')
        _plain(ax)
        ax.plot(X_FINE, Y_FINE, color=LINK, lw=3.0, label='the curve to be matched')
        ax.plot(X_FINE, pred, color=GRIP, lw=1.8, label='what the neurons make')
        ax.set_xlim(X_LO, X_HI)
        ax.set_ylim(-1.1, 3.0)
        ax.set_xlabel('the number going in', fontsize=9.5)
        ax.set_title(f'{w} neurons, {w} bends\naverage gap {gap:.4f}', fontsize=11,
                     weight='bold')
    axes[0].set_ylabel('the number wanted out', fontsize=9.5)
    axes[0].legend(fontsize=9, frameon=False, loc='lower left')
    _title(fig, 'More bends, less gap: with enough of them the two lines cannot be '
                'told apart')
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    _save(fig, DOC4, 'wider-fits.svg')


def gap_vs_width() -> None:
    """How fast the gap closes as neurons are added."""
    gaps = []
    for w in WIDTHS:
        gap = _fit_width(w)[3]
        gaps.append(gap)
        print(f'[gapwidth] {w:>3} neurons: average gap {gap:.5f}')
    ratios = [gaps[i] / gaps[i + 1] for i in range(len(gaps) - 1)]
    print(f'[gapwidth] doubling the neurons divides the gap by about '
          f'{np.mean(ratios):.1f}')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(WIDTHS, gaps, marker='o', color=LINK, lw=2.2)
    for w, g in zip(WIDTHS, gaps):
        ax.annotate(f'{g:.4f}', (w, g), textcoords='offset points', xytext=(8, 6),
                    fontsize=9.5, color=LINK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(WIDTHS)
    ax.set_xticklabels([str(w) for w in WIDTHS], fontsize=9.5)
    ax.minorticks_off()
    ax.set_xlabel('how many rectified-linear neurons the layer has (log scale)',
                  fontsize=10)
    ax.set_ylabel('average gap to the curve (log scale)', fontsize=10)
    ax.set_title(f'Each doubling of the layer divides the gap by about '
                 f'{np.mean(ratios):.1f}', fontsize=12, weight='bold')
    _save(fig, DOC4, 'gap-vs-width.svg')


# --------------------------------------------------------------------------
# 04, section 3: capacity and parameter count
# --------------------------------------------------------------------------

def _dense_params(n_in: int, width: int, depth: int, n_out: int) -> int:
    """Parameters of a network with `depth` hidden layers, all of the same width."""
    total = n_in * width + width
    total += (depth - 1) * (width * width + width)
    total += width * n_out + n_out
    return total


def parameter_count() -> None:
    """How the parameter count follows from width and depth, with a real sum."""
    widths = (32, 128, 512)
    depths = (1, 3, 8)
    rows = []
    for w in widths:
        cells = [f'{w}']
        for d in depths:
            p = _dense_params(7, w, d, 2)
            cells.append(_commas(p))
            print(f'[params] 7 inputs, {d} hidden layer(s) of {w}, 2 outputs: '
                  f'{_commas(p)} parameters')
        rows.append(tuple(cells))

    fig, ax = plt.subplots(figsize=(9.6, 3.6), facecolor='white')
    _table(ax, ('width of each\nhidden layer', *[f'{d} hidden\nlayer'
                                                 f'{"" if d == 1 else "s"}'
                                                 for d in depths]),
           rows, (2.4, 2.1, 2.1, 2.1), size=10.5, head_size=10.0)
    _title(fig, 'Parameters of a network with 7 inputs and 2 outputs, counted exactly',
           size=12.0)
    fig.tight_layout(rect=(0, 0.02, 1, 0.88))
    _save(fig, DOC4, 'parameter-count.svg')


def params_and_bends() -> None:
    """Cost and capacity of a one-input network, side by side on one scale."""
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    small_widths = [2, 4, 8, 16, 32, 64]
    params = [_dense_params(1, w, 1, 1) for w in small_widths]
    ax.plot(small_widths, params, marker='o', color=LINK, lw=2.4,
            label='parameters it holds')
    ax.plot(small_widths, small_widths, marker='s', color=GRIP, lw=2.4,
            label='bends it can make')
    for w, p in zip(small_widths, params):
        ax.annotate(_commas(p), (w, p), textcoords='offset points', xytext=(7, 6),
                    fontsize=9.5, color=LINK)
        print(f'[params] one input, one hidden layer of {w}, one output: '
              f'{p} parameters and {w} bends')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(small_widths)
    ax.set_xticklabels([str(w) for w in small_widths], fontsize=9.5)
    ax.minorticks_off()
    ax.set_xlim(1.7, 110)
    ax.set_xlabel('neurons in the hidden layer (log scale)', fontsize=10)
    ax.set_ylabel('count (log scale)', fontsize=10)
    ax.set_title('For one input, the parameters are about three times the bends, '
                 'at every width', fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, DOC4, 'params-and-bends.svg')


def _noisy_points() -> tuple[Arr, Arr]:
    """Twenty simulated readings of the target curve, taken at even steps."""
    rng = np.random.default_rng(5)
    xs = np.linspace(X_LO + 0.05, X_HI - 0.05, 20)
    ys = _target(xs) + rng.normal(0.0, 0.22, 20)
    return xs, ys


def _fit_points(width: int) -> tuple[Arr, Arr, float, float]:
    xs, ys = _noisy_points()
    knots = _even_knots(width)
    coef = _fit(knots, xs, ys)
    at_points = float(np.mean(np.abs(_predict(knots, coef, xs) - ys)))
    pred = _predict(knots, coef, X_FINE)
    to_truth = float(np.mean(np.abs(pred - Y_FINE)))
    return knots, pred, at_points, to_truth


def too_little_too_much() -> None:
    """Twelve noisy readings fitted by 2, 5 and 14 bends."""
    xs, ys = _noisy_points()
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.6), facecolor='white')
    heads = ('2 neurons: too few',
             '5 neurons: about right',
             '18 neurons: too many')
    for w, ax, head in zip((2, 5, 18), axes, heads):
        _, pred, at_points, to_truth = _fit_points(w)
        print(f'[capacity] {w} neurons: {_dense_params(1, w, 1, 1)} parameters, '
              f'gap at the 20 readings {at_points:.4f}, gap to the true curve '
              f'{to_truth:.4f}')
        _plain(ax)
        ax.plot(X_FINE, Y_FINE, color=LINK, lw=2.4, label='the true curve')
        ax.plot(X_FINE, pred, color=GRIP, lw=2.0, label='what the neurons make')
        ax.scatter(xs, ys, color=INK, s=30, zorder=5, label='the 20 noisy readings')
        ax.set_xlim(X_LO, X_HI)
        ax.set_ylim(-1.8, 3.4)
        ax.set_xlabel('the number going in', fontsize=9.5)
        ax.set_title(f'{head}\ngap at the readings {at_points:.3f}, '
                     f'to the curve {to_truth:.3f}', fontsize=10.5, weight='bold')
    axes[0].set_ylabel('the number wanted out', fontsize=9.5)
    axes[0].legend(fontsize=8.5, frameon=False, loc='lower left')
    _title(fig, 'Twenty simulated readings of a curve, matched by three networks of '
                'different sizes')
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    _save(fig, DOC4, 'too-little-too-much.svg')


def points_versus_truth() -> None:
    """The gap at the readings keeps falling while the gap to the truth turns round."""
    widths = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18]
    at_points, to_truth = [], []
    for w in widths:
        _, _, ap, tt = _fit_points(w)
        at_points.append(ap)
        to_truth.append(tt)
        print(f'[turn] {w:>2} neurons: gap at the 20 readings {ap:.4f}, gap to the '
              f'true curve {tt:.4f}')
    best = widths[int(np.argmin(to_truth))]
    print(f'[turn] the gap to the true curve is smallest at {best} neurons')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(widths, at_points, marker='o', color=GRIP, lw=2.2,
            label='gap at the 20 readings it was given')
    ax.plot(widths, to_truth, marker='s', color=LINK, lw=2.2,
            label='gap to the true curve everywhere else')
    ax.axvline(best, color=MUTED, ls=':', lw=1.4)
    ax.annotate(f'{best} neurons: as close to the\ntruth as this fit gets',
                (best, min(to_truth)), textcoords='offset points', xytext=(14, -28),
                fontsize=9.5, color=LINK)
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths], fontsize=9)
    ax.set_ylim(-0.02, 0.48)
    ax.set_xlabel('neurons in the hidden layer', fontsize=10)
    ax.set_ylabel('average gap', fontsize=10)
    ax.set_title('Past a point, matching the readings better means matching the truth '
                 'worse', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, DOC4, 'points-versus-truth.svg')


# --------------------------------------------------------------------------
# 04, section 4: why a fully connected layer is wrong for a photo
# --------------------------------------------------------------------------

def flatten_a_photo() -> None:
    """Counting the weights a fully connected layer needs for one colour photo."""
    n_in = 3 * 224 * 224
    neurons = 1000
    dense = n_in * neurons
    conv = 3 * 3 * 3 * 64
    print(f'[flatten] a colour photo of 224 by 224 is 3 x 224 x 224 = {_commas(n_in)} '
          f'numbers')
    print(f'[flatten] a fully connected layer of {neurons} neurons needs '
          f'{_commas(n_in)} x {neurons} = {_commas(dense)} weights, which is '
          f'{dense * 4 / 1e9:.3f} GB at float32')
    print(f'[flatten] a convolutional layer with 64 filters of 3 by 3 needs '
          f'3 x 3 x 3 x 64 = {_commas(conv)} weights, {conv * 4 / 1e3:.2f} kB')
    print(f'[flatten] the fully connected layer has {dense / conv:,.0f} times as many '
          f'weights')

    fig, ax = plt.subplots(figsize=(13.2, 5.0), facecolor='white')
    _blank(ax, (-1.0, 27.0), (-4.6, 5.0))
    # the photo as three stacked grids
    for k, colour in enumerate(('#e05555', '#2a9d3f', '#3b82c4')):
        ax.add_patch(Rectangle((0.3 + k * 0.45, 1.6 - k * 0.45), 3.4, 3.4,
                               facecolor='#f2f2f2', edgecolor=colour, lw=1.6,
                               zorder=2 + k))
    ax.text(2.2, 0.6, '3 x 224 x 224', fontsize=10.5, ha='center', va='top',
            color=INK, weight='bold')
    ax.text(2.2, -0.2, 'one colour photo', fontsize=9.5, ha='center', va='top',
            color=MUTED)

    _arrow(ax, (5.4, 2.6), (6.6, 2.6))
    ax.text(6.0, 3.0, 'flatten', fontsize=9.5, ha='center', va='bottom', color=MUTED)
    _grid_at(ax, np.zeros((1, 24)), 7.0, 3.0, cell=0.4,
             faces=[['#dbe8f5'] * 24], show_text=False)
    ax.text(11.8, 2.2, f'{_commas(n_in)} numbers in one long list', fontsize=10.5,
            ha='center', va='top', color=INK, weight='bold')

    _arrow(ax, (17.2, 2.8), (18.4, 2.8))
    _box(ax, 18.8, 1.4, 2.6, 2.8, face='#e8eff7', edge=INK,
         text='1,000\nneurons', size=10.5)
    ax.text(22.0, 3.6, f'{_commas(n_in)} x 1,000', fontsize=11, ha='left',
            va='center', color=GRIP)
    ax.text(22.0, 2.8, f'= {_commas(dense)} weights', fontsize=11, ha='left',
            va='center', color=GRIP, weight='bold')
    ax.text(22.0, 2.0, f'= {dense * 4 / 1e9:.2f} GB at float32', fontsize=10.5,
            ha='left', va='center', color=GRIP)
    ax.text(22.0, 1.2, 'for one layer', fontsize=9.5, ha='left', va='center',
            color=MUTED)

    ax.text(0.0, -1.6, f'A convolutional layer with 64 filters of 3 by 3 does the same '
            f'job with 3 x 3 x 3 x 64 = {_commas(conv)} weights,\nwhich is '
            f'{dense / conv:,.0f} times fewer, and it is the same {_commas(conv)} '
            f'weights whatever the size of the photo.', fontsize=10.5, ha='left',
            va='top', color=SLIDE)
    _title(fig, 'Flattening a photo into a fully connected layer: 150 million weights '
                'for one layer')
    _save(fig, DOC4, 'flatten-a-photo.svg')


def weights_vs_picture_size() -> None:
    """How the two kinds of layer grow as the photo gets bigger."""
    sides = [32, 64, 128, 224, 512]
    dense = [3 * s * s * 1000 for s in sides]
    conv = [3 * 3 * 3 * 64] * len(sides)
    for s, d in zip(sides, dense):
        print(f'[grow] a {s} by {s} colour photo into 1,000 neurons: {_commas(d)} '
              f'weights; the 64 filters stay at {conv[0]:,}')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(sides, dense, marker='o', color=GRIP, lw=2.4,
            label='fully connected, 1,000 neurons')
    ax.plot(sides, conv, marker='s', color=SLIDE, lw=2.4,
            label='convolutional, 64 filters of 3 by 3')
    for s, d in zip(sides, dense):
        off, align = ((8, 6), 'left') if s == sides[0] else ((-6, 10), 'right')
        ax.annotate(_commas(d), (s, d), textcoords='offset points', xytext=off,
                    fontsize=9, color=GRIP, ha=align)
    ax.annotate(f'{conv[0]:,} weights, whatever the size', (sides[2], conv[0]),
                textcoords='offset points', xytext=(0, 12), fontsize=9.5, color=SLIDE,
                ha='center')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sides)
    ax.set_xticklabels([f'{s} x {s}' for s in sides], fontsize=9.5)
    ax.minorticks_off()
    ax.set_xlim(26, 640)
    ax.set_ylim(1e2, 1e10)
    ax.set_xlabel('size of the colour photo (log scale)', fontsize=10)
    ax.set_ylabel('weights in the first layer (log scale)', fontsize=10)
    ax.set_title('Four times the pixels, four times the weights, for the fully '
                 'connected layer only', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC4, 'weights-vs-picture-size.svg')


EDGE_V: Arr = np.array([[1.0, 0.0, -1.0]] * 3)
EDGE_H: Arr = np.array([[1.0, 1.0, 1.0], [0.0, 0.0, 0.0], [-1.0, -1.0, -1.0]])


def _convolve(grid: Arr, filt: Arr) -> Arr:
    h, w = grid.shape
    kh, kw = filt.shape
    out = np.zeros((h - kh + 1, w - kw + 1))
    for r in range(out.shape[0]):
        for c in range(out.shape[1]):
            out[r, c] = float(np.sum(grid[r:r + kh, c:c + kw] * filt))
    return out


def _block_picture(top: int, left: int, size: int = 3, side: int = 8,
                   back: float = 1.0, bright: float = 9.0) -> Arr:
    pic = np.full((side, side), back)
    pic[top:top + size, left:left + size] = bright
    return pic


def position_blindness() -> None:
    """The same block in two places: a flat list shares nothing, a filter shares all."""
    a = _block_picture(1, 1)
    b = _block_picture(4, 4)
    fa = a.reshape(-1)
    fb = b.reshape(-1)
    bright_a = set(np.flatnonzero(fa > 5).tolist())
    bright_b = set(np.flatnonzero(fb > 5).tolist())
    overlap = sorted(bright_a & bright_b)
    out_a = _convolve(a, EDGE_V)
    out_b = _convolve(b, EDGE_V)
    print(f'[blind] block at rows 1-3: bright places in the flat list {sorted(bright_a)}')
    print(f'[blind] block at rows 4-6: bright places in the flat list {sorted(bright_b)}')
    print(f'[blind] places they share: {overlap if overlap else "none"}')
    print(f'[blind] the filter gives the same numbers, moved: '
          f'{sorted(set(np.round(out_a[out_a != 0], 0).tolist()))} appear in both '
          f'answers; row sums of the first answer '
          f'{np.round(out_a.sum(axis=1), 0).tolist()}')

    fig, ax = plt.subplots(figsize=(13.2, 7.0), facecolor='white')
    _blank(ax, (-0.8, 24.6), (-8.4, 7.0))
    cell = 0.62
    flat_cell = 0.2
    for i, (pic, flat, colour, label) in enumerate(
            ((a, fa, LINK, 'the block near the top left'),
             (b, fb, PURPLE, 'the same block moved down and right'))):
        top = 6.0 - i * 6.6
        _grid_at(ax, pic, 0.0, top, cell=cell, fmt='{:.0f}',
                 faces=_grey_faces(pic, top=10.0), size=7.0,
                 text_colours=[['white' if v < 5 else INK for v in row] for row in pic])
        ax.text(2.48, top + 0.15, label, fontsize=9.5, ha='center', va='bottom',
                color=colour, weight='bold')
        _grid_at(ax, flat.reshape(1, 64), 6.2, top - 2.3, cell=flat_cell,
                 faces=_grey_faces(flat.reshape(1, 64), top=10.0), show_text=False)
        for start in np.flatnonzero(flat > 5)[::3]:
            _frame(ax, 6.2 + float(start) * flat_cell, top - 2.3, 3 * flat_cell,
                   flat_cell, colour=colour, lw=1.6)
        places = sorted(np.flatnonzero(flat > 5).tolist())
        ax.text(6.2 + 6.4, top - 2.8, 'the same 64 numbers in one flat list\n'
                'bright at places ' + ', '.join(str(v) for v in places),
                fontsize=9.5, ha='center', va='top', color=MUTED)
        out = out_a if i == 0 else out_b
        _grid_at(ax, out, 20.0, top - 0.62, cell=cell, fmt='{:.0f}',
                 faces=_faces(out, cmap='RdBu', vmin=-27, vmax=27), size=7.0)
        ax.text(20.0 + 1.86, top + 0.15, 'what one 3 by 3 filter gives', fontsize=9.5,
                ha='center', va='bottom', color=colour, weight='bold')
    ax.text(0.0, -6.0, 'The two flat lists share no bright place at all, so a weight '
            'that learned the block in the first place does nothing in the\nsecond. '
            'The filter gives exactly the same six numbers, moved to the same new '
            'place, because it is the same filter everywhere.',
            fontsize=10.5, ha='left', va='top', color=INK)
    _title(fig, 'A flat list forgets where a thing was; a filter does not')
    _save(fig, DOC4, 'position-blindness.svg')


# --------------------------------------------------------------------------
# 04, section 5: the convolution worked out
# --------------------------------------------------------------------------

def _conv_grid() -> Arr:
    """A made-up 7 by 7 brightness grid: a bright block on a dark table."""
    pic = np.full((7, 7), 2.0)
    pic[1:5, 2:6] = 8.0
    return pic


def filter_over_grid() -> None:
    """One filter slid over a 7 by 7 grid, with every output number shown."""
    pic = _conv_grid()
    out = _convolve(pic, EDGE_V)
    print(f'[conv] the 7 by 7 grid =\n{pic.astype(int)}')
    print(f'[conv] the filter =\n{EDGE_V.astype(int)}')
    print(f'[conv] the 5 by 5 answer =\n{out.astype(int)}')
    print(f'[conv] the answer runs from {out.min():.0f} to {out.max():.0f}')

    fig, ax = plt.subplots(figsize=(13.2, 5.2), facecolor='white')
    _blank(ax, (-0.8, 25.4), (-2.8, 6.0))
    cell = 0.78
    _grid_at(ax, pic, 0.0, 5.4, cell=cell, fmt='{:.0f}',
             faces=_grey_faces(pic, top=10.0), size=8.5,
             text_colours=[['white' if v < 5 else INK for v in row] for row in pic])
    ax.text(2.73, 5.6, 'the picture, 7 by 7', fontsize=10.5, ha='center', va='bottom',
            color=INK, weight='bold')
    _frame(ax, 1 * cell, 5.4 - 1 * cell, 3 * cell, 3 * cell, colour=GRIP, lw=2.4)
    ax.text(2.73, -0.4, 'the red window sits at row 1, column 1', fontsize=9.5,
            ha='center', va='top', color=GRIP)

    x0 = 7.4
    _grid_at(ax, EDGE_V, x0, 4.2, cell=cell, fmt='{:+.0f}',
             faces=_faces(EDGE_V, cmap='RdBu', vmin=-1.5, vmax=1.5), size=9.5)
    ax.text(x0 + 1.17, 4.4, 'the filter, 3 by 3', fontsize=10.5, ha='center',
            va='bottom', color=INK, weight='bold')
    ax.text(x0 + 1.17, 1.6, 'left column plus,\nright column minus', fontsize=9.5,
            ha='center', va='top', color=MUTED)

    _arrow(ax, (11.6, 3.0), (12.8, 3.0))
    x0 = 13.4
    _grid_at(ax, out, x0, 5.4, cell=cell, fmt='{:+.0f}',
             faces=_faces(out, cmap='RdBu', vmin=-27, vmax=27), size=8.5)
    ax.text(x0 + 1.95, 5.6, 'the answer, 5 by 5', fontsize=10.5, ha='center',
            va='bottom', color=INK, weight='bold')
    _frame(ax, x0 + 1 * cell, 5.4 - 1 * cell, cell, cell, colour=GRIP, lw=2.4)
    ax.text(x0 + 1.95, -0.4, f'that window gives {out[1, 1]:+.0f}', fontsize=9.5,
            ha='center', va='top', color=GRIP)
    ax.text(19.6, 3.0, 'negative down the block\'s\nleft edge, positive down its\n'
            'right edge, 0 between them',
            fontsize=10.5, ha='left', va='center', color=INK)
    _title(fig, 'A 3 by 3 filter slid over a 7 by 7 picture gives a 5 by 5 answer')
    _save(fig, DOC4, 'filter-over-grid.svg')


def three_window_positions() -> None:
    """Three positions of the window, with all nine products written out."""
    pic = _conv_grid()
    out = _convolve(pic, EDGE_V)
    picks = [(0, 0), (1, 1), (1, 4)]
    fig, ax = plt.subplots(figsize=(13.4, 5.6), facecolor='white')
    _blank(ax, (-0.8, 27.2), (-3.4, 5.2))
    cell = 0.82
    for i, (r, c) in enumerate(picks):
        x0 = i * 9.0
        window = pic[r:r + 3, c:c + 3]
        prod = window * EDGE_V
        total = float(prod.sum())
        terms = ' + '.join(f'{int(window[a, b])}x{int(EDGE_V[a, b]):+d}'
                           for a in range(3) for b in range(3))
        print(f'[window] row {r}, column {c}: {terms} = {total:+.0f} '
              f'(the answer grid holds {out[r, c]:+.0f} there)')
        _grid_at(ax, window, x0, 4.4, cell=cell, fmt='{:.0f}',
                 faces=_grey_faces(window, top=10.0), size=9,
                 text_colours=[['white' if v < 5 else INK for v in row]
                               for row in window])
        ax.text(x0 + 1.23, 4.6, f'window at row {r}, column {c}', fontsize=10,
                ha='center', va='bottom', color=INK, weight='bold')
        ax.text(x0 + 2.9, 3.0, 'x', fontsize=12, ha='center', va='center', color=MUTED)
        _grid_at(ax, EDGE_V, x0 + 3.5, 4.4, cell=cell, fmt='{:+.0f}',
                 faces=_faces(EDGE_V, cmap='RdBu', vmin=-1.5, vmax=1.5), size=9)
        _grid_at(ax, prod, x0 + 3.5, 0.8, cell=cell, fmt='{:+.0f}',
                 faces=_faces(prod, cmap='RdBu', vmin=-9, vmax=9), size=9)
        ax.text(x0 + 4.73, 1.0, 'the nine products', fontsize=9.5, ha='center',
                va='bottom', color=MUTED)
        ax.text(x0 + 2.5, -2.0, f'they add up to {total:+.0f}', fontsize=11.5,
                ha='center', va='center', color=GRIP, weight='bold')
    _title(fig, 'Three positions of the same filter: nine multiplies and one total '
                'at each')
    _save(fig, DOC4, 'three-window-positions.svg')


def two_filters() -> None:
    """The same picture through two different filters."""
    pic = _conv_grid()
    out_v = _convolve(pic, EDGE_V)
    out_h = _convolve(pic, EDGE_H)
    print(f'[two] the up-and-down edge filter gives numbers from {out_v.min():.0f} to '
          f'{out_v.max():.0f}; the left-and-right one from {out_h.min():.0f} to '
          f'{out_h.max():.0f}')
    print(f'[two] left-and-right answer =\n{out_h.astype(int)}')

    fig, ax = plt.subplots(figsize=(13.0, 5.6), facecolor='white')
    _blank(ax, (-0.8, 25.0), (-3.6, 5.6))
    cell = 0.78
    _grid_at(ax, pic, 0.0, 5.0, cell=cell, fmt='{:.0f}',
             faces=_grey_faces(pic, top=10.0), size=8.5,
             text_colours=[['white' if v < 5 else INK for v in row] for row in pic])
    ax.text(2.73, 5.2, 'the same picture', fontsize=10.5, ha='center', va='bottom',
            color=INK, weight='bold')

    for i, (filt, out, name) in enumerate(
            ((EDGE_V, out_v, 'left column plus, right column minus:\n'
                              'it finds the up-and-down edges'),
             (EDGE_H, out_h, 'top row plus, bottom row minus:\n'
                              'it finds the left-and-right edges'))):
        y = 5.0 - i * 3.2
        _grid_at(ax, filt, 7.2, y, cell=0.62, fmt='{:+.0f}',
                 faces=_faces(filt, cmap='RdBu', vmin=-1.5, vmax=1.5), size=8.5)
        _arrow(ax, (9.4, y - 0.95), (10.4, y - 0.95))
        _grid_at(ax, out, 11.0, y, cell=0.62, fmt='{:+.0f}',
                 faces=_faces(out, cmap='RdBu', vmin=-27, vmax=27), size=7.5)
        ax.text(14.4, y - 0.95, name, fontsize=10, ha='left', va='center', color=INK)
    ax.text(0.0, -2.2, 'Nine weights each, nine pixels each: only the nine numbers '
            'differ.', fontsize=11, ha='left', va='top', color=INK)
    _title(fig, 'Two filters, one picture: a filter is a detector for one small pattern')
    _save(fig, DOC4, 'two-filters.svg')


def output_size() -> None:
    """How the answer's size follows from the picture, the filter, the padding, stride."""
    pic = _conv_grid()
    plain = _convolve(pic, EDGE_V)
    padded = _convolve(np.pad(pic, 1, mode='constant', constant_values=2.0), EDGE_V)
    strided = plain[::2, ::2]
    print(f'[size] 7 - 3 + 1 = {plain.shape[0]}, so the plain answer is '
          f'{plain.shape[0]} by {plain.shape[1]}')
    print(f'[size] with one ring of padding, 9 - 3 + 1 = {padded.shape[0]}, so the '
          f'answer is {padded.shape[0]} by {padded.shape[1]}, the same size as the '
          f'picture')
    print(f'[size] taking every second window, the answer is {strided.shape[0]} by '
          f'{strided.shape[1]}')

    fig, ax = plt.subplots(figsize=(13.2, 4.8), facecolor='white')
    _blank(ax, (-0.8, 26.4), (-3.0, 5.2))
    cell = 0.62
    for i, (out, head, note) in enumerate(
            ((plain, 'slide it everywhere it fits',
              '7 - 3 + 1 = 5, so the answer is 5 by 5\nand the picture has shrunk'),
             (padded, 'add a ring of table first',
              '9 - 3 + 1 = 7, so the answer is 7 by 7\nand nothing has shrunk'),
             (strided, 'step two, not one',
              'the answer is 3 by 3, so 9 squares\nare worked out instead of 25'))):
        x0 = i * 8.8
        _grid_at(ax, out, x0, 4.6, cell=cell, fmt='{:+.0f}',
                 faces=_faces(out, cmap='RdBu', vmin=-27, vmax=27), size=7.0)
        ax.text(x0, 4.8, head, fontsize=10.5, ha='left',
                va='bottom', color=INK, weight='bold')
        ax.text(x0, 0.0, note, fontsize=9.5, ha='left', va='top', color=MUTED)
    _title(fig, 'What decides the size of the answer: the filter, the padding and how '
                'far the window steps')
    _save(fig, DOC4, 'output-size.svg')


# --------------------------------------------------------------------------
# 04, section 6: the convolutional neural network
# --------------------------------------------------------------------------

def receptive_field() -> None:
    """How far back into the picture one late number can see."""
    print('[field] with 3 by 3 filters and a step of 1, the window on the picture '
          'grows by 2 each layer:')
    for layers in range(1, 6):
        print(f'[field]   after {layers} layer(s): {2 * layers + 1} by '
              f'{2 * layers + 1} pixels')
    need = -(-(224 - 1) // 2)
    print(f'[field] to cover 224 pixels that way would take {need} layers')
    rf, jump, rows = 1, 1, []
    for i in range(12):
        stride = 1 if i % 2 == 0 else 2
        rf += (3 - 1) * jump
        jump *= stride
        rows.append((i + 1, stride, rf, jump))
        print(f'[field] with every second layer stepping 2: after layer {i + 1} '
              f'(step {stride}) the window is {rf} by {rf} pixels')

    fig, ax = plt.subplots(figsize=(8.2, 6.4), facecolor='white')
    _blank(ax, (-1.0, 18.6), (-2.6, 14.4))
    side = 13
    _grid_at(ax, np.zeros((side, side)), 0.0, 13.0, cell=1.0,
             faces=[['#f4f7fb'] * side for _ in range(side)], show_text=False,
             edge='#e3e9f0')
    colours = [LINK, SLIDE, WRIST, PURPLE, GRIP]
    for layers in range(1, 6):
        w = 2 * layers + 1
        off = (side - w) / 2
        _frame(ax, off, 13.0 - off, w, w, colour=colours[layers - 1], lw=2.0)
        ax.text(13.4, 13.0 - off, f'after {layers} layer'
                f'{"" if layers == 1 else "s"}: {w} by {w}', fontsize=10,
                ha='left', va='center', color=colours[layers - 1], weight='bold')
    ax.text(6.5, -0.6, 'each 3 by 3 filter adds one pixel on every side,\n'
            'so the window grows by 2 for every layer', fontsize=10.5, ha='center',
            va='top', color=INK)
    _title(fig, 'What one number five layers deep has seen of the picture', size=12.0)
    _save(fig, DOC4, 'receptive-field.svg')


def reach_vs_layers() -> None:
    """How many layers it takes for one number to see the whole picture."""
    rf, jump, rows = 1, 1, []
    for i in range(12):
        stride = 1 if i % 2 == 0 else 2
        rf += (3 - 1) * jump
        jump *= stride
        rows.append((i + 1, stride, rf, jump))

    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    layers = [r[0] for r in rows]
    plain_rf = [2 * n + 1 for n in layers]
    step_rf = [r[2] for r in rows]
    ax.plot(layers, plain_rf, marker='o', color=LINK, lw=2.4,
            label='every layer steps one place')
    ax.plot(layers, step_rf, marker='s', color=GRIP, lw=2.4,
            label='every second layer steps two places')
    for n, v in zip(layers, step_rf):
        if n in (4, 8, 12):
            ax.annotate(f'{v} by {v}', (n, v), textcoords='offset points',
                        xytext=(-6, 9), fontsize=9.5, color=GRIP, ha='right')
    for n, v in zip(layers, plain_rf):
        if n == 12:
            ax.annotate(f'{v} by {v}', (n, v), textcoords='offset points',
                        xytext=(-6, -14), fontsize=9.5, color=LINK, ha='right')
    ax.axhline(224, color=MUTED, ls='--', lw=1.3)
    ax.text(1.1, 248, 'the whole 224 pixel picture', fontsize=10, color=MUTED)
    ax.set_yscale('log')
    ax.set_ylim(2.5, 700)
    ax.set_xticks(layers)
    ax.set_xlabel('how many convolutional layers deep', fontsize=10)
    ax.set_ylabel('pixels of the picture one number sees (log scale)', fontsize=10)
    reach = next(r[0] for r in rows if r[2] >= 224)
    print(f'[field] stepping two every other layer covers the whole 224 pixel '
          f'picture after {reach} layers')
    ax.set_title(f'Stepping two every other layer reaches the whole picture in '
                 f'{reach} layers', fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    _save(fig, DOC4, 'reach-vs-layers.svg')


def cnn_stage_shapes() -> None:
    """A small convolutional network: the shape and the weight count at every stage."""
    rows = []
    total = 0
    shape = (3, 224, 224)
    for c_in, c_out in VISION_CONVS:
        params = c_in * c_out * 9 + c_out
        total += params
        out_shape = (c_out, shape[1] // 2, shape[2] // 2)
        macs = c_out * out_shape[1] * out_shape[2] * c_in * 9
        rows.append((f'{c_in} -> {c_out}', f'{out_shape[0]} x {out_shape[1]} x '
                     f'{out_shape[2]}', _commas(params), f'{macs / 1e6:,.1f} million'))
        print(f'[cnn] 3 by 3 filters, {c_in} in, {c_out} out, step 2: answer '
              f'{out_shape}, {_commas(params)} weights, {macs / 1e6:,.1f} million '
              f'multiply-adds')
        shape = out_shape
    print(f'[cnn] the four stages together hold {_commas(total)} parameters, '
          f'{total * 4 / 1e6:.2f} MB at float32')
    dense = 3 * 224 * 224 * 1000 + 1000
    print(f'[cnn] one fully connected layer on the same photo holds '
          f'{_commas(dense)} parameters, {dense / total:,.0f} times as many')

    fig, ax = plt.subplots(figsize=(11.6, 3.8), facecolor='white')
    _table(ax, ('stage', 'what comes out', 'weights', 'multiply-adds for one photo'),
           rows, (2.2, 3.0, 2.2, 3.6), size=10.0, head_size=9.5)
    ax.text(0.5, -0.1, f'the four stages together: {_commas(total)} parameters, '
            f'{total * 4 / 1e6:.2f} MB at float32', fontsize=10.5, ha='center',
            va='top', transform=ax.transAxes, color=INK, weight='bold')
    _title(fig, 'A four-stage convolutional network on a 3 x 224 x 224 photo',
           size=12.5)
    fig.tight_layout(rect=(0, 0.04, 1, 0.86))
    _save(fig, DOC4, 'cnn-stage-shapes.svg')


def stages_shrink_and_deepen() -> None:
    """The grid gets smaller stage by stage while the number of grids grows."""
    fig, ax = plt.subplots(figsize=(12.8, 5.2), facecolor='white')
    _blank(ax, (-3.2, 27.2), (-5.4, 7.2))
    shapes = [(3, 224), (32, 112), (64, 56), (128, 28), (256, 14)]
    names = ['the photo', 'after stage 1', 'after stage 2', 'after stage 3',
             'after stage 4']
    scale = 4.4 / 224.0
    pitch, shown, step, mid = 5.6, 6, 0.17, 2.4
    for i, ((channels, side), name) in enumerate(zip(shapes, names)):
        w = side * scale
        cx = i * pitch
        x0 = cx - (w + (shown - 1) * step) / 2
        top = mid + (w + (shown - 1) * step) / 2
        for k in range(shown - 1, -1, -1):
            face = to_hex(plt.get_cmap('Blues')(0.10 + 0.06 * k))
            ax.add_patch(Rectangle((x0 + k * step, top - k * step - w), w, w,
                                   facecolor=face, edgecolor=LINK, lw=0.7,
                                   zorder=10 - k))
        ax.text(cx, 5.6, f'{channels} grids', fontsize=11, ha='center', va='bottom',
                color=INK, weight='bold')
        ax.text(cx, -1.4, f'{side} by {side}\neach', fontsize=10.5, ha='center',
                va='top', color=INK)
        ax.text(cx, -3.4, name, fontsize=10, ha='center', va='top', color=MUTED)
        if i < len(shapes) - 1:
            _arrow(ax, (cx + pitch / 2 - 0.5, mid), (cx + pitch / 2 + 0.5, mid),
                   colour=MUTED, lw=1.6)
    ax.text(11.2, -4.9, 'half the width and half the height each time, twice as many '
            'grids', fontsize=11.5, ha='center', va='center', color=INK)
    _title(fig, 'Stage by stage the grids get smaller and there are more of them',
           size=12.5)
    _save(fig, DOC4, 'stages-shrink-and-deepen.svg')


def patches_are_a_convolution() -> None:
    """Cutting a picture into patches is a convolution with a filter the patch's size."""
    side, patch = 224, 16
    per_side = side // patch
    print(f'[patches] a {side} by {side} picture cut into {patch} by {patch} patches '
          f'gives {per_side} by {per_side} = {per_side * per_side} patches, which is '
          f'one convolution with a {patch} by {patch} filter stepping {patch}')

    fig, ax = plt.subplots(figsize=(9.6, 5.6), facecolor='white')
    _blank(ax, (-1.0, 23.0), (-2.8, 15.6))
    cell = 1.0
    shown = 14
    rng = np.random.default_rng(31)
    faces = [[to_hex(plt.get_cmap('Blues')(0.05 + 0.30 * float(v)))
              for v in row] for row in rng.random((shown, shown))]
    _grid_at(ax, np.zeros((shown, shown)), 0.0, 14.0, cell=cell, faces=faces,
             show_text=False, edge=INK)
    _frame(ax, 0.0, 14.0, cell, cell, colour=GRIP, lw=2.6)
    _frame(ax, cell, 14.0, cell, cell, colour=JOINT, lw=2.6)
    ax.text(15.0, 13.5, 'one patch: 16 by 16 pixels\nof the photo, with 3 colours,\n'
            'so 768 numbers', fontsize=10, ha='left', va='center', color=GRIP)
    ax.text(15.0, 10.0, 'the next patch starts 16\npixels along, so no patch\n'
            'overlaps another', fontsize=10, ha='left', va='center', color=JOINT)
    ax.text(7.0, -0.5, f'{per_side} by {per_side} = {per_side * per_side} patches '
            f'from one 224 by 224 photo', fontsize=11, ha='center', va='top',
            color=INK, weight='bold')
    ax.text(7.0, -1.7, 'a filter 16 wide stepping 16 places at a time',
            fontsize=10.5, ha='center', va='top', color=MUTED)
    _title(fig, 'A vision transformer starts with a convolution: one 16 by 16 filter, '
                'stepping 16', size=12.0)
    _save(fig, DOC4, 'patches-are-a-convolution.svg')


def _conv_versus_dense() -> tuple[int, int, int, int]:
    """Parameters and multiply-adds of the stack and of one fully connected layer."""
    conv_params = sum(c_in * c_out * 9 + c_out for c_in, c_out in VISION_CONVS)
    conv_macs = 0
    shape = (3, 224, 224)
    for c_in, c_out in VISION_CONVS:
        out_shape = (c_out, shape[1] // 2, shape[2] // 2)
        conv_macs += c_out * out_shape[1] * out_shape[2] * c_in * 9
        shape = out_shape
    dense_params = 3 * 224 * 224 * 1000 + 1000
    dense_macs = 3 * 224 * 224 * 1000
    return conv_params, conv_macs, dense_params, dense_macs


CONV_LABELS: tuple[str, str] = (
    'four convolutional stages\n3 -> 32 -> 64 -> 128 -> 256',
    'one fully connected layer\n150,528 -> 1,000',
)


def conv_versus_dense_weights() -> None:
    """How many weights each of the two choices of first picture layer holds."""
    conv_params, conv_macs, dense_params, dense_macs = _conv_versus_dense()
    print(f'[compare] the four convolutional stages: {_commas(conv_params)} '
          f'parameters and {_commas(conv_macs)} multiply-adds for one photo')
    print(f'[compare] one fully connected layer of 1,000 neurons: '
          f'{_commas(dense_params)} parameters and {_commas(dense_macs)} '
          f'multiply-adds')
    print(f'[compare] the fully connected layer has {dense_params / conv_params:,.0f} '
          f'times the parameters and {dense_macs / conv_macs:.2f} times the '
          f'multiply-adds')

    fig, ax = plt.subplots(figsize=(9.2, 5.0), facecolor='white')
    _plain(ax)
    ax.bar([0, 1], [conv_params, dense_params], width=0.5, color=SLIDE,
           edgecolor=INK, lw=0.6)
    ax.set_yscale('log')
    ax.set_ylim(1e4, 1e10)
    ax.set_xlim(-0.7, 1.7)
    for p, v in zip((0, 1), (conv_params, dense_params)):
        ax.text(p, v * 1.7, _commas(v), fontsize=11, ha='center', color=INK,
                weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(list(CONV_LABELS), fontsize=10)
    ax.set_ylabel('weights and biases it holds (log scale)', fontsize=10)
    ax.set_title(f'The convolutional stack holds {dense_params / conv_params:,.0f} '
                 f'times fewer weights', fontsize=12, weight='bold')
    _save(fig, DOC4, 'conv-versus-dense-weights.svg')


def conv_versus_dense_arithmetic() -> None:
    """How much arithmetic each of the two choices of first picture layer does."""
    _, conv_macs, _, dense_macs = _conv_versus_dense()

    fig, ax = plt.subplots(figsize=(9.2, 5.0), facecolor='white')
    _plain(ax)
    ax.bar([0, 1], [conv_macs, dense_macs], width=0.5, color=WRIST,
           edgecolor=INK, lw=0.6)
    ax.set_ylim(0, 2.3e8)
    ax.set_xlim(-0.7, 1.7)
    for p, v in zip((0, 1), (conv_macs, dense_macs)):
        ax.text(p, v + 7e6, _commas(v), fontsize=11, ha='center', color=INK,
                weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(list(CONV_LABELS), fontsize=10)
    ax.set_ylabel('multiply-adds for one photo', fontsize=10)
    ax.set_title(f'The arithmetic barely changes: the stack does '
                 f'{conv_macs / dense_macs:.2f} times as much', fontsize=12,
                 weight='bold')
    _save(fig, DOC4, 'conv-versus-dense-arithmetic.svg')


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
    count_the_tiny_network()
    parameters_layer_by_layer()
    block_of_twelve_grids()
    answer_cost_counts()
    work_per_number()
    squares_are_independent()
    tiles_reuse()
    block_size_table()
    almost_all_matmul()
    matmul_share_vs_width()
    batch_of_four()
    per_example_traffic()
    traffic_one_at_a_time()
    weights_share_of_traffic()
    numbers_through_the_stack()
    batch_memory()
    number_formats()
    spacing_of_numbers()
    rounding_error()
    running_total()
    mixed_precision()
    memory_bill()
    three_sizes()
    four_models_in_bytes()
    does_it_fit()
    weights_are_not_the_bill()
    straight_line_fails()
    two_multiplies_collapse()
    one_hinge()
    hinge_weight()
    three_piece_line()
    building_with_hinges()
    bends_and_gap()
    wider_fits()
    gap_vs_width()
    parameter_count()
    params_and_bends()
    too_little_too_much()
    points_versus_truth()
    flatten_a_photo()
    weights_vs_picture_size()
    position_blindness()
    filter_over_grid()
    three_window_positions()
    two_filters()
    output_size()
    receptive_field()
    reach_vs_layers()
    cnn_stage_shapes()
    stages_shrink_and_deepen()
    patches_are_a_convolution()
    conv_versus_dense_weights()
    conv_versus_dense_arithmetic()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
