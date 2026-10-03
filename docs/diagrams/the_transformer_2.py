"""Generate the diagrams for the last two pages of docs/06_neural-networks/06_the-transformer/.

    03_training-and-running-a-transformer.md -> images/the-transformer/training-and-running-a-transformer/
    04_why-the-transformer-won.md            -> images/the-transformer/why-the-transformer-won/

Run with:  python3 the_transformer_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints all of them so the two documents can quote the same values.

What is simulated and what is real arithmetic:

  * The six-token sentence "the arm lifts the red block", the twelve-word
    vocabulary and the raw outputs a "model" gives for that sentence are
    simulated: the raw numbers are drawn with numpy.random.default_rng(7) and
    then a stated boost is added to the right answer at each position.
    Everything done with those numbers is the real arithmetic: softmax,
    cross-entropy, temperature, top-p and the two-step tree.
  * The attention scores in the causal-mask pictures come from query and key
    vectors drawn with numpy.random.default_rng(11). The scaling by the square
    root of the head size, the masking and the softmax are real.
  * Every memory figure, work figure and time figure is worked out from one
    stated example configuration (24 layers, 16 heads of 64 numbers each,
    width 1024, feed-forward width 4096, vocabulary 32768, every number held
    in two bytes) and one stated example accelerator (1,000 gigabytes a second
    of memory reading and 100 trillion arithmetic operations a second). No real
    product and no published model is described anywhere in this file.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'the-transformer'
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

TRAIN_DOC: str = 'training-and-running-a-transformer'
WHY_DOC: str = 'why-the-transformer-won'

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)


def _bare(ax: Axes) -> None:
    """No axes at all: for the pictures drawn out of boxes and arrows."""
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _softmax(z: Arr, axis: int = -1) -> Arr:
    z = z - np.max(z, axis=axis, keepdims=True)
    e = np.exp(z)
    return e / np.sum(e, axis=axis, keepdims=True)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, fontsize: float = 10.0,
         colour: str = INK, weight: str = 'normal', lw: float = 1.2) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fontsize,
            color=colour, weight=weight, zorder=3)


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.1, head: float = 0.09) -> None:
    ax.add_patch(FancyArrow(x0, y0, x1 - x0, y1 - y0, width=0.0, head_width=head,
                            head_length=head * 1.4, length_includes_head=True,
                            color=colour, lw=lw, zorder=4))


def _matrix(ax: Axes, m: Arr, col_labels: list[str], row_labels: list[str], *,
            fmt: str = '{:.2f}', cmap: str = 'Blues', vmin: float | None = None,
            vmax: float | None = None, fontsize: float = 8.5,
            text_cut: float = 0.6) -> None:
    """Draw a matrix as coloured cells with the number written in each cell.

    Cells holding not-a-number are drawn grey and left empty.
    """
    cm = matplotlib.colormaps[cmap].copy()
    cm.set_bad('#e8e8e8')
    lo = float(np.nanmin(m)) if vmin is None else vmin
    hi = float(np.nanmax(m)) if vmax is None else vmax
    ax.imshow(np.ma.masked_invalid(m), cmap=cm, vmin=lo, vmax=hi)
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=fontsize + 0.5)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=fontsize + 0.5)
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which='minor', color='white', lw=1.4)
    ax.tick_params(which='minor', length=0)
    ax.tick_params(length=0, labelsize=fontsize + 0.5, colors=INK)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            if not np.isfinite(v):
                continue
            shade = (v - lo) / (hi - lo) if hi > lo else 0.0
            ax.text(j, i, fmt.format(v), ha='center', va='center', fontsize=fontsize,
                    color='white' if shade > text_cut else INK)


# --------------------------------------------------------------------------
# the one stated example configuration, used by every memory and time picture
# --------------------------------------------------------------------------

LAYERS: int = 24
HEADS: int = 16
HEAD_DIM: int = 64
WIDTH: int = HEADS * HEAD_DIM            # 1024
FFN: int = 4 * WIDTH                     # 4096
VOCAB: int = 32768
TRAINED_LEN: int = 8192
NBYTES: int = 2                          # every number held in two bytes

P_PER_LAYER: int = 4 * WIDTH * WIDTH + 2 * WIDTH * FFN + 2 * WIDTH
P_LAYERS: int = LAYERS * P_PER_LAYER
P_EMBED: int = VOCAB * WIDTH
P_TOTAL: int = P_EMBED + P_LAYERS + WIDTH     # the output layer shares the embedding table
P_MATMUL: int = P_LAYERS + P_EMBED            # the parameters that take part in a matrix multiply

WEIGHT_BYTES: int = P_TOTAL * NBYTES
CACHE_PER_TOKEN: int = 2 * LAYERS * HEADS * HEAD_DIM * NBYTES   # keys and values

BANDWIDTH: float = 1.0e12       # bytes a second the example accelerator can read
PEAK_FLOPS: float = 1.0e14      # useful arithmetic operations a second

MIB: float = 1024.0 ** 2
GIB: float = 1024.0 ** 3


def _flops_per_token(length: int) -> float:
    """Arithmetic for one more token: the weight multiplies plus the attention pairs."""
    return 2.0 * P_MATMUL + 4.0 * LAYERS * WIDTH * length


def _bytes_per_step(length: int, batch: int) -> float:
    """Memory read for one generation step: the weights once, each cache once."""
    return WEIGHT_BYTES + batch * CACHE_PER_TOKEN * length


def print_config() -> None:
    print(f'[config] {LAYERS} layers, {HEADS} heads of {HEAD_DIM}, width {WIDTH}, '
          f'feed-forward {FFN}, vocabulary {VOCAB}, trained length {TRAINED_LEN}')
    print(f'[config] parameters per layer {P_PER_LAYER:,}; all layers {P_LAYERS:,}; '
          f'embedding table {P_EMBED:,}; total {P_TOTAL:,}')
    print(f'[config] weights at {NBYTES} bytes each: {WEIGHT_BYTES:,} bytes '
          f'= {WEIGHT_BYTES / MIB:.0f} MiB')
    print(f'[config] cache per token: 2 x {LAYERS} x {HEADS} x {HEAD_DIM} x {NBYTES} '
          f'= {CACHE_PER_TOKEN:,} bytes = {CACHE_PER_TOKEN / 1024:.0f} KiB')
    print(f'[config] cache for one sequence of {TRAINED_LEN}: '
          f'{CACHE_PER_TOKEN * TRAINED_LEN:,} bytes = {CACHE_PER_TOKEN * TRAINED_LEN / MIB:.0f} MiB')


# --------------------------------------------------------------------------
# the simulated sentence and the simulated model that predicts it
# --------------------------------------------------------------------------

WORDS: list[str] = ['the', 'arm', 'lifts', 'red', 'block', 'gripper',
                    'drops', 'blue', 'table', 'cube', 'and', 'slowly']
SENTENCE: list[str] = ['the', 'arm', 'lifts', 'the', 'red', 'block']
BOOSTS: list[float] = [1.2, 3.4, 2.2, 0.9, 2.6, 4.4]    # how sure the model is at each position


class Sim:
    """The simulated raw outputs for the sentence, and everything real taken from them."""

    def __init__(self) -> None:
        rng = np.random.default_rng(7)
        self.inputs: list[str] = ['<start>'] + SENTENCE[:-1]
        self.targets: list[str] = list(SENTENCE)
        n = len(self.targets)
        self.logits: Arr = rng.normal(0.0, 1.4, size=(n, len(WORDS)))
        for i, word in enumerate(self.targets):
            self.logits[i, WORDS.index(word)] += BOOSTS[i]
        self.probs: Arr = _softmax(self.logits)
        self.target_idx: NDArray[np.int64] = np.array([WORDS.index(w) for w in self.targets])
        self.p_target: Arr = self.probs[np.arange(n), self.target_idx]
        self.loss: Arr = -np.log(self.p_target)
        self.mean_loss: float = float(self.loss.mean())
        self.guess: list[str] = [WORDS[int(i)] for i in self.probs.argmax(1)]
        self.right: list[bool] = [g == t for g, t in zip(self.guess, self.targets)]


_SIM: Sim | None = None


def sim() -> Sim:
    global _SIM
    if _SIM is None:
        _SIM = Sim()
    return _SIM
