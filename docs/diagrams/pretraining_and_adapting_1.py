"""Generate the diagrams for the first two pages of docs/06_neural-networks/07_pretraining-and-adapting/.

    01_self-supervised-pretraining.md -> images/pretraining-and-adapting/self-supervised-pretraining/
    02_scale-data-and-compute.md      -> images/pretraining-and-adapting/scale-data-and-compute/

Run with:  cd docs/diagrams && python3 pretraining_and_adapting_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints all of them so the two documents can quote the same values.

What is simulated, and what is real:

* The sentences of the toy corpus come from a small hand-written grammar with a
  seeded generator, so the corpus is simulated. The next-token models trained on
  it are real softmax regressions fitted by gradient descent in NumPy, and the
  losses printed are measured on a held-out part of that corpus.
* The pictures are simulated: each one is six smooth basis pictures added
  together with random amounts, plus pixel noise, from a seeded generator. The
  masked-prediction model, the principal-component representation, the linear
  head, the from-scratch network, the contrastive (CLIP-style) training and the
  self-distillation (DINO-style) run are all real fitted models written in
  NumPy, run on that simulated data.
* The memory budgets, floating-point operation counts and timings on page two
  are arithmetic on clearly stated example configurations and an example
  accelerator. They are not measurements of any real product, and no real
  model's parameter count, token count or benchmark score appears anywhere.
* The scaling-law curves come from one stated formula in this file. They are
  illustrative arithmetic, not a measurement.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'pretraining-and-adapting')
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

SSP_DOC: str = 'self-supervised-pretraining'
SDC_DOC: str = 'scale-data-and-compute'

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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, size: float = 9.5,
         weight: str = 'normal', colour: str = INK) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=size, weight=weight, color=colour)


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.4) -> None:
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>',
                                 mutation_scale=12, color=colour, lw=lw,
                                 shrinkA=0, shrinkB=0))


def _si(n: float) -> str:
    """A whole number with thousands separators."""
    return f'{n:,.0f}'


# --------------------------------------------------------------------------
# a real softmax regression, fitted by gradient descent, used several times
# --------------------------------------------------------------------------

def softmax_fit(x: Arr, y: NDArray[np.int64], n_class: int, steps: int = 400,
                lr: float = 0.5, weight_decay: float = 1e-4,
                batch: int = 256, seed: int = 0) -> tuple[Arr, Arr]:
    """Fit logits = x @ w + b by mini-batch gradient descent on cross-entropy."""
    rng = np.random.default_rng(seed)
    n, d = x.shape
    w = np.zeros((d, n_class))
    b = np.zeros(n_class)
    for step in range(steps):
        idx = rng.integers(0, n, size=min(batch, n))
        xb, yb = x[idx], y[idx]
        p = _softmax(xb @ w + b)
        p[np.arange(len(yb)), yb] -= 1.0
        g = xb.T @ p / len(yb) + weight_decay * w
        w -= lr * g
        b -= lr * p.mean(axis=0)
    return w, b


def softmax_loss(x: Arr, y: NDArray[np.int64], w: Arr, b: Arr) -> float:
    p = _softmax(x @ w + b)
    return float(-np.mean(np.log(p[np.arange(len(y)), y] + 1e-12)))


def softmax_acc(x: Arr, y: NDArray[np.int64], w: Arr, b: Arr) -> float:
    return float(np.mean(np.argmax(x @ w + b, axis=1) == y))
