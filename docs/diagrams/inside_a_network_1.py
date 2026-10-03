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
