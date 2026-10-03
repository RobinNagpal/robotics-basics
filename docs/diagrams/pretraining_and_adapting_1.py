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


def softmax_fit_history(x: Arr, y: NDArray[np.int64], xv: Arr, yv: NDArray[np.int64],
                        n_class: int, steps: int = 400, lr: float = 0.5,
                        weight_decay: float = 1e-4, batch: int = 256,
                        every: int = 20, seed: int = 0
                        ) -> tuple[Arr, Arr, list[int], list[float]]:
    """Like softmax_fit, but also record the held-out loss as the fit goes on."""
    rng = np.random.default_rng(seed)
    n, d = x.shape
    w = np.zeros((d, n_class))
    b = np.zeros(n_class)
    at: list[int] = [0]
    hist: list[float] = [softmax_loss(xv, yv, w, b)]
    for step in range(1, steps + 1):
        idx = rng.integers(0, n, size=min(batch, n))
        xb, yb = x[idx], y[idx]
        p = _softmax(xb @ w + b)
        p[np.arange(len(yb)), yb] -= 1.0
        w -= lr * (xb.T @ p / len(yb) + weight_decay * w)
        b -= lr * p.mean(axis=0)
        if step % every == 0:
            at.append(step)
            hist.append(softmax_loss(xv, yv, w, b))
    return w, b, at, hist


# --------------------------------------------------------------------------
# the simulated toy corpus: a tiny grammar of sentences about an arm
# --------------------------------------------------------------------------

TEMPLATES: list[list[str]] = [
    'the arm moved to the COL OBJ .'.split(),
    'the gripper closed around the COL OBJ .'.split(),
    'the camera saw a COL OBJ on the table .'.split(),
    'the arm lifted the COL OBJ slowly .'.split(),
    'the gripper opened above the COL OBJ .'.split(),
    'the controller held the COL OBJ still .'.split(),
]
COLOURS: list[str] = ['red', 'blue', 'green', 'grey']
OBJECTS: list[str] = ['cube', 'mug', 'bowl', 'tray']


class Corpus:
    """A simulated corpus of simple sentences, with every next-token pair in it."""

    def __init__(self, n_sentences: int = 4000, seed: int = 7) -> None:
        rng = np.random.default_rng(seed)
        self.sentences: list[list[str]] = []
        for _ in range(n_sentences):
            t = TEMPLATES[int(rng.integers(0, len(TEMPLATES)))]
            col = COLOURS[int(rng.integers(0, len(COLOURS)))]
            obj = OBJECTS[int(rng.integers(0, len(OBJECTS)))]
            self.sentences.append([col if w == 'COL' else obj if w == 'OBJ' else w
                                   for w in t])
        self.words: list[str] = sorted({w for s in self.sentences for w in s})
        self.index: dict[str, int] = {w: i for i, w in enumerate(self.words)}
        self.v: int = len(self.words)
        self.ids: list[NDArray[np.int64]] = [
            np.array([self.index[w] for w in s], dtype=np.int64) for s in self.sentences]
        self.n_tokens: int = int(sum(len(s) for s in self.ids))
        self.n_next_pairs: int = int(sum(len(s) - 1 for s in self.ids))
        cut = int(0.8 * len(self.ids))
        self.train_ids = self.ids[:cut]
        self.test_ids = self.ids[cut:]

    def one_hot_pairs(self, ids: list[NDArray[np.int64]], context: int
                      ) -> tuple[Arr, NDArray[np.int64]]:
        """Inputs are the one-hot codes of the last `context` words, target is the next word."""
        rows: list[Arr] = []
        targets: list[int] = []
        for s in ids:
            for i in range(context, len(s)):
                x = np.zeros(max(context, 1) * self.v)
                for k in range(context):
                    x[k * self.v + s[i - context + k]] = 1.0
                rows.append(x)
                targets.append(int(s[i]))
        return np.array(rows), np.array(targets, dtype=np.int64)

    def no_context(self, ids: list[NDArray[np.int64]]) -> tuple[Arr, NDArray[np.int64]]:
        targets = np.array([int(t) for s in ids for t in s[1:]], dtype=np.int64)
        return np.ones((len(targets), 1)), targets

    def both_sides_pairs(self, ids: list[NDArray[np.int64]], left_only: bool
                         ) -> tuple[Arr, NDArray[np.int64]]:
        """Inputs code the word before and (unless left_only) the word after the hidden one."""
        rows: list[Arr] = []
        targets: list[int] = []
        width = self.v if left_only else 2 * self.v
        for s in ids:
            for i in range(1, len(s) - 1):
                x = np.zeros(width)
                x[s[i - 1]] = 1.0
                if not left_only:
                    x[self.v + s[i + 1]] = 1.0
                rows.append(x)
                targets.append(int(s[i]))
        return np.array(rows), np.array(targets, dtype=np.int64)


# --------------------------------------------------------------------------
# the simulated pictures: six smooth basis pictures, random amounts, pixel noise
# --------------------------------------------------------------------------

SIDE: int = 12
N_FACTOR: int = 6
NOISE: float = 0.45
MARGIN: float = 0.5


def _basis(seed: int = 11) -> Arr:
    """Six smooth unit-length basis pictures, made by blurring noise and orthonormalising."""
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(N_FACTOR, SIDE, SIDE))
    k = np.exp(-0.5 * (np.arange(-3, 4) / 1.3) ** 2)
    k /= k.sum()
    for _ in range(2):
        raw = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 1, raw)
        raw = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 2, raw)
    flat = raw.reshape(N_FACTOR, SIDE * SIDE)
    q, _ = np.linalg.qr(flat.T)
    return q.T[:N_FACTOR]


BASIS: Arr = _basis()


def make_pictures(n: int, seed: int) -> tuple[Arr, NDArray[np.int64], Arr]:
    """Return n flattened pictures, their class (the quadrant of the first two factors),
    and the hidden factors themselves."""
    rng = np.random.default_rng(seed)
    keep_z: list[Arr] = []
    while len(keep_z) < n:
        z = rng.normal(size=(n, N_FACTOR))
        ok = (np.abs(z[:, 0]) > MARGIN) & (np.abs(z[:, 1]) > MARGIN)
        keep_z.extend(list(z[ok]))
    z = np.array(keep_z[:n])
    pics = z @ BASIS + NOISE * rng.normal(size=(n, SIDE * SIDE))
    cls = ((z[:, 0] > 0).astype(np.int64) * 2 + (z[:, 1] > 0).astype(np.int64))
    return pics, cls, z


# --------------------------------------------------------------------------
# page 1, section 1: where the training signal comes from
# --------------------------------------------------------------------------

CORPUS: Corpus = Corpus()
SECONDS_PER_LABEL: float = 20.0


def labels_versus_free_signal() -> None:
    n_sent = len(CORPUS.sentences)
    hand = n_sent
    free = CORPUS.n_next_pairs
    hours = hand * SECONDS_PER_LABEL / 3600.0
    print(f'[sig] corpus: {_si(n_sent)} sentences, {_si(CORPUS.n_tokens)} words, '
          f'vocabulary {CORPUS.v}')
    print(f'[sig] one hand label per sentence: {_si(hand)} training signals, '
          f'{hours:.1f} person-hours at {SECONDS_PER_LABEL:.0f} s each')
    print(f'[sig] next-word targets in the same text: {_si(free)} signals, 0 person-hours')
    print(f'[sig] ratio {free / hand:.1f} times as many signals')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.4), facecolor='white')
    _plain(ax1)
    ax1.bar([0, 1], [hand, free], color=[GRIP, SLIDE], width=0.55)
    for i, v in enumerate([hand, free]):
        ax1.text(i, v + free * 0.02, _si(v), ha='center', fontsize=11, weight='bold')
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['one hand label\nper sentence', 'every next word\nin the same text'],
                        fontsize=9.5)
    ax1.set_ylim(0, free * 1.16)
    ax1.set_ylabel('training signals', fontsize=10)
    ax1.set_title(f'The same {_si(n_sent)} sentences, two ways of getting a signal',
                  fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [hours, 0.0], color=[GRIP, SLIDE], width=0.55)
    ax2.text(0, hours * 1.03, f'{hours:.1f} hours', ha='center', fontsize=11, weight='bold')
    ax2.text(1, hours * 0.03, 'none', ha='center', fontsize=11, weight='bold', color=SLIDE)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['hand labels', 'next-word targets'], fontsize=9.5)
    ax2.set_ylim(0, hours * 1.25)
    ax2.set_ylabel(f'person-hours at {SECONDS_PER_LABEL:.0f} seconds a label', fontsize=10)
    ax2.set_title('What each column of signal costs a person', fontsize=11.5, weight='bold')
    _save(fig, SSP_DOC, 'labels-versus-free-signal.svg')


def make_the_label_from_the_data() -> None:
    sentence = CORPUS.sentences[0]
    print(f'[pairs] sentence: {" ".join(sentence)}')
    pairs = [(sentence[:i], sentence[i]) for i in range(1, len(sentence))]
    for ctx, tgt in pairs:
        print(f'[pairs]   "{" ".join(ctx)}" -> "{tgt}"')
    print(f'[pairs] {len(pairs)} pairs from one sentence of {len(sentence)} words')

    fig, ax = plt.subplots(figsize=(10.6, 4.9), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, len(pairs) + 1.9)
    ax.text(0.1, len(pairs) + 1.3,
            f'One simulated sentence of {len(sentence)} words gives {len(pairs)} '
            f'training pairs, and nobody wrote a label',
            fontsize=12, weight='bold', va='center')
    ax.text(0.7, len(pairs) + 0.55, 'words the model is shown', fontsize=10,
            weight='bold', color=LINK)
    ax.text(7.5, len(pairs) + 0.55, 'word it must guess', fontsize=10,
            weight='bold', color=GRIP)
    for row, (ctx, tgt) in enumerate(pairs):
        y = len(pairs) - row - 0.5
        _box(ax, 0.7, y - 0.33, 6.3, 0.66, ' '.join(ctx), face=LINK_PALE, edge=LINK)
        _arrow(ax, 7.05, y, 7.45, y, colour=MUTED)
        _box(ax, 7.5, y - 0.33, 1.6, 0.66, tgt, face='#fbdcdc', edge=GRIP, weight='bold')
    _save(fig, SSP_DOC, 'make-the-label-from-the-data.svg')


def one_picture_many_targets() -> None:
    px = 224
    patch = 16
    per_side = px // patch
    n_patch = per_side * per_side
    mask_rate = 0.75
    n_masked = int(round(mask_rate * n_patch))
    numbers = px * px * 3
    print(f'[targets] a {px} by {px} colour picture is {_si(numbers)} numbers')
    print(f'[targets] cut into {patch} by {patch} patches: {per_side} by {per_side} '
          f'= {n_patch} patches')
    print(f'[targets] hiding {mask_rate:.0%} of them gives {n_masked} things to predict, '
          f'against 1 hand label')

    rng = np.random.default_rng(3)
    hidden = np.zeros(n_patch, dtype=bool)
    hidden[rng.permutation(n_patch)[:n_masked]] = True
    grid = hidden.reshape(per_side, per_side)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    _blank(ax1)
    ax1.set_xlim(-0.5, per_side - 0.5)
    ax1.set_ylim(per_side - 0.5, -0.5)
    for i in range(per_side):
        for j in range(per_side):
            face = MUTED if grid[i, j] else LINK_PALE
            ax1.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=face,
                                    edgecolor='white', lw=1.0))
    ax1.set_title(f'{per_side} by {per_side} = {n_patch} patches, '
                  f'{n_masked} of them hidden (grey)', fontsize=11, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1, 2], [1, n_masked, numbers], color=[GRIP, SLIDE, TEAL], width=0.55)
    ax2.set_yscale('log')
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(['one hand label\n("a mug")', f'{n_masked} hidden\npatches to fill in',
                         'all its numbers,\nif you predict pixels'], fontsize=9.5)
    for i, v in enumerate([1, n_masked, numbers]):
        ax2.text(i, v * 1.5, _si(v), ha='center', fontsize=11, weight='bold')
    ax2.set_ylim(0.5, numbers * 12)
    ax2.set_ylabel('training signals from one picture (log scale)', fontsize=10)
    ax2.set_title('One picture, one label, or hundreds of guesses', fontsize=11.5, weight='bold')
    _save(fig, SSP_DOC, 'one-picture-many-targets.svg')
