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
# the simulated pictures
#
# Every picture is built the same way. Six smooth "content" basis pictures are
# added together with random amounts, and those amounts are what the class of
# the picture depends on. Three further smooth "nuisance" basis pictures, with a
# much larger amount, stand for the things that change between two photographs
# of the same object, such as the lighting and the background. Then independent
# noise is added to every pixel. Two views of one item share the content and get
# their own nuisance and their own noise.
# --------------------------------------------------------------------------

SIDE: int = 20
P: int = SIDE * SIDE
N_CONTENT: int = 6
N_NUISANCE: int = 3
CONTENT_SCALE: float = 10.0
NUISANCE_SCALE: float = 28.0
PIXEL_NOISE: float = 1.4
MARGIN: float = 0.55


def _smooth_basis(k: int, seed: int, width: float) -> Arr:
    """k smooth unit-length basis pictures, made by blurring noise and straightening up."""
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(k, SIDE, SIDE))
    half = int(round(2.5 * width))
    ker = np.exp(-0.5 * (np.arange(-half, half + 1) / width) ** 2)
    ker /= ker.sum()
    for _ in range(2):
        raw = np.apply_along_axis(lambda m: np.convolve(m, ker, mode='same'), 1, raw)
        raw = np.apply_along_axis(lambda m: np.convolve(m, ker, mode='same'), 2, raw)
    q, _ = np.linalg.qr(raw.reshape(k, P).T)
    return q.T[:k]


CONTENT_BASIS: Arr = _smooth_basis(N_CONTENT, seed=11, width=1.8)
NUISANCE_BASIS: Arr = _smooth_basis(N_NUISANCE, seed=12, width=3.0)


class Pics:
    """One batch of simulated pictures, with one or two views of each item."""

    def __init__(self, n: int, seed: int, views: int = 1) -> None:
        rng = np.random.default_rng(seed)
        keep: list[Arr] = []
        while len(keep) < n:
            z = rng.normal(size=(n, N_CONTENT))
            ok = ((np.abs(z[:, 0]) > MARGIN) & (np.abs(z[:, 1]) > MARGIN)
                  & (np.abs(np.abs(z[:, 0]) - np.abs(z[:, 1])) > MARGIN))
            keep.extend(list(z[ok]))
        self.z: Arr = np.array(keep[:n])
        self.content: Arr = CONTENT_SCALE * (self.z @ CONTENT_BASIS)
        self.clean: list[Arr] = []
        self.view: list[Arr] = []
        self.nuisance: list[Arr] = []
        for _ in range(views):
            coeff = rng.normal(size=(n, N_NUISANCE))
            self.nuisance.append(coeff)
            nuis = NUISANCE_SCALE * (coeff @ NUISANCE_BASIS)
            clean = self.content + nuis
            self.clean.append(clean)
            self.view.append(clean + PIXEL_NOISE * rng.normal(size=(n, P)))
        self.cls: NDArray[np.int64] = (
            2 * ((self.z[:, 0] * self.z[:, 1]) > 0).astype(np.int64)
            + (np.abs(self.z[:, 0]) > np.abs(self.z[:, 1])).astype(np.int64))

    @property
    def a(self) -> Arr:
        return self.view[0]

    @property
    def b(self) -> Arr:
        return self.view[1]


CLASS_NAMES: list[str] = ['class 1', 'class 2', 'class 3', 'class 4']


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
    ax1.set_title(f'{_si(n_sent)} sentences, two kinds of signal',
                  fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [hours, 0.0], color=[GRIP, SLIDE], width=0.55)
    ax2.text(0, hours * 1.03, f'{hours:.1f} hours', ha='center', fontsize=11, weight='bold')
    ax2.text(1, hours * 0.03, 'none', ha='center', fontsize=11, weight='bold', color=SLIDE)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['hand labels', 'next-word targets'], fontsize=9.5)
    ax2.set_ylim(0, hours * 1.25)
    ax2.set_ylabel(f'person-hours at {SECONDS_PER_LABEL:.0f} seconds a label', fontsize=10)
    ax2.set_title('What each one costs a person', fontsize=11.5, weight='bold')
    fig.subplots_adjust(wspace=0.32)
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
    ax2.set_title('One label, or hundreds of guesses', fontsize=11.5, weight='bold')
    fig.subplots_adjust(wspace=0.3)
    _save(fig, SSP_DOC, 'one-picture-many-targets.svg')


# --------------------------------------------------------------------------
# simulated matched pairs of picture and caption vectors (used by sections 1 and 4)
# --------------------------------------------------------------------------

def paired_vectors(n: int, dim: int = 8, noise: float = 0.75, seed: int = 5
                   ) -> tuple[Arr, Arr]:
    """Matched picture and caption vectors: one shared content vector plus separate noise."""
    rng = np.random.default_rng(seed)
    content = rng.normal(size=(n, dim))
    pic = content + noise * rng.normal(size=(n, dim))
    txt = content + noise * rng.normal(size=(n, dim))
    pic /= np.linalg.norm(pic, axis=1, keepdims=True)
    txt /= np.linalg.norm(txt, axis=1, keepdims=True)
    return pic, txt


def _patch_mask(rate: float, seed: int) -> NDArray[np.bool_]:
    """A pixel mask built from 2 by 2 patches: True means the pixel is hidden."""
    rng = np.random.default_rng(seed)
    per_side = SIDE // 2
    n_patch = per_side * per_side
    hide = np.zeros(n_patch, dtype=bool)
    hide[rng.permutation(n_patch)[:int(round(rate * n_patch))]] = True
    grid = np.repeat(np.repeat(hide.reshape(per_side, per_side), 2, axis=0), 2, axis=1)
    return grid.reshape(-1)


def four_recipes() -> None:
    sentence = CORPUS.sentences[3]
    pic = Pics(1, seed=31).a[0].reshape(SIDE, SIDE)
    mask = _patch_mask(0.5, seed=32)
    shown = pic.copy().reshape(-1)
    shown[mask] = np.nan
    pv, tv = paired_vectors(4, seed=33)
    sim = pv @ tv.T
    big_pic = Pics(1, seed=34).a[0].reshape(SIDE, SIDE)
    print(f'[recipes] sentence: {" ".join(sentence)}  (last word hidden: {sentence[-2]})')
    print(f'[recipes] picture mask hides {int(mask.sum())} of {SIDE * SIDE} pixels')
    print('[recipes] 4 by 4 similarity grid, diagonal: '
          + ', '.join(f'{sim[i, i]:+.2f}' for i in range(4)))
    print(f'[recipes] mean off-diagonal similarity {np.mean(sim[~np.eye(4, dtype=bool)]):+.2f}')

    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.2), facecolor='white')
    fig.suptitle('Four ways to make the answer out of the data itself',
                 fontsize=13, weight='bold', y=0.98)

    ax = axes[0, 0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    words = sentence[:-1]
    for i, w in enumerate(words):
        shown_word = i < len(words) - 1
        _box(ax, 0.2 + i * 1.32, 1.3, 1.24, 0.7, w if shown_word else '?',
             face=LINK_PALE if shown_word else '#fbdcdc',
             edge=LINK if shown_word else GRIP,
             weight='normal' if shown_word else 'bold', size=8.2)
    ax.text(0.2, 2.55, 'Next word: hide what comes next', fontsize=11, weight='bold')
    ax.text(0.2, 0.75, f'answer = "{words[-1]}", taken from the text', fontsize=9.5, color=MUTED)

    ax = axes[0, 1]
    _blank(ax)
    hidden_map = matplotlib.colormaps['Greys_r'].with_extremes(bad=GRIP)
    ax.imshow(shown.reshape(SIDE, SIDE), cmap=hidden_map, interpolation='nearest')
    ax.set_title('Masked patches: hide part of the picture', fontsize=11, weight='bold')
    ax.text(0.5, -0.09, f'answer = the {int(mask.sum())} hidden pixel values',
            transform=ax.transAxes, ha='center', fontsize=9.5, color=MUTED)

    ax = axes[1, 0]
    _blank(ax)
    ax.imshow(sim, cmap='RdYlGn', vmin=-1, vmax=1, interpolation='nearest')
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f'{sim[i, j]:+.2f}', ha='center', va='center', fontsize=9.5,
                    weight='bold' if i == j else 'normal')
    for i in range(4):
        ax.add_patch(Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=INK, lw=2.0))
    ax.set_title('Pairs: push the matching ones together', fontsize=11, weight='bold')
    ax.text(0.5, -0.09, 'answer = "the match is on the diagonal"',
            transform=ax.transAxes, ha='center', fontsize=9.5, color=MUTED)

    ax = axes[1, 1]
    _blank(ax)
    ax.imshow(big_pic, cmap='Greys_r', interpolation='nearest')
    ax.add_patch(Rectangle((-0.5, -0.5), 8, 8, fill=False, edgecolor=LINK, lw=2.4))
    ax.add_patch(Rectangle((3.5, 3.5), 8, 8, fill=False, edgecolor=GRIP, lw=2.4))
    ax.set_title('Two crops: make the two agree', fontsize=11, weight='bold')
    ax.text(0.5, -0.09, 'answer = whatever the slower copy said about the other crop',
            transform=ax.transAxes, ha='center', fontsize=9.5, color=MUTED)
    fig.subplots_adjust(hspace=0.33)
    _save(fig, SSP_DOC, 'four-recipes.svg')


# --------------------------------------------------------------------------
# page 1, section 2: next-token prediction
# --------------------------------------------------------------------------

class NextToken:
    """Four real models of the next word in the simulated corpus, fitted by gradient descent."""

    def __init__(self) -> None:
        c = CORPUS
        self.uniform = float(np.log(c.v))
        x0, y0 = c.no_context(c.train_ids)
        x0v, y0v = c.no_context(c.test_ids)
        w0, b0 = softmax_fit(x0, y0, c.v, steps=4000, lr=1.5, weight_decay=1e-6,
                             batch=512, seed=1)
        self.none = softmax_loss(x0v, y0v, w0, b0)
        x1, y1 = c.one_hot_pairs(c.train_ids, 1)
        x1v, y1v = c.one_hot_pairs(c.test_ids, 1)
        self.w1, self.b1, self.at1, self.hist1 = softmax_fit_history(
            x1, y1, x1v, y1v, c.v, steps=4000, lr=1.5, weight_decay=1e-6,
            batch=512, every=100, seed=2)
        self.one = softmax_loss(x1v, y1v, self.w1, self.b1)
        x2, y2 = c.one_hot_pairs(c.train_ids, 2)
        x2v, y2v = c.one_hot_pairs(c.test_ids, 2)
        self.w2, self.b2, self.at2, self.hist2 = softmax_fit_history(
            x2, y2, x2v, y2v, c.v, steps=4000, lr=1.5, weight_decay=1e-6,
            batch=512, every=100, seed=3)
        self.two = softmax_loss(x2v, y2v, self.w2, self.b2)
        self.n_train_pairs = len(y1)
        self.n_test_pairs = len(y1v)

    def after(self, word: str) -> Arr:
        x = np.zeros((1, CORPUS.v))
        x[0, CORPUS.index[word]] = 1.0
        return _softmax(x @ self.w1 + self.b1)[0]


NT: NextToken | None = None


def _nt() -> NextToken:
    global NT
    if NT is None:
        NT = NextToken()
    return NT


def next_token_pairs() -> None:
    s = CORPUS.sentences[1]
    print(f'[nt] sentence: {" ".join(s)}')
    print(f'[nt] {len(s)} words give {len(s) - 1} next-word jobs')
    fig, ax = plt.subplots(figsize=(11.0, 3.9), facecolor='white')
    _blank(ax)
    n = len(s)
    ax.set_xlim(0, n + 1.2)
    ax.set_ylim(0, 4.4)
    ax.text(0.1, 4.05, f'One sentence, read as {len(s) - 1} separate jobs at once',
            fontsize=12.5, weight='bold')
    ax.text(0.1, 2.72, 'the words', fontsize=10, weight='bold', color=LINK)
    ax.text(0.1, 1.42, 'what the model\nmust guess there', fontsize=10, weight='bold',
            color=GRIP)
    for i, w in enumerate(s):
        _box(ax, 1.25 + i * 1.0, 2.35, 0.92, 0.72, w, face=LINK_PALE, edge=LINK, size=8.8)
        ax.text(1.25 + i * 1.0 + 0.46, 3.3, f'{i + 1}', ha='center', fontsize=9, color=MUTED)
        if i < n - 1:
            _box(ax, 2.25 + i * 1.0, 1.15, 0.92, 0.72, s[i + 1], face='#fbdcdc',
                 edge=GRIP, size=8.8)
            _arrow(ax, 1.71 + i * 1.0, 2.3, 2.71 + i * 1.0, 1.92, colour=MUTED, lw=1.0)
    ax.text(0.1, 0.45, 'Each arrow is one training pair, and the answer was already in '
                       'the sentence, so nobody had to write it down.',
            fontsize=9.5, color=MUTED)
    _save(fig, SSP_DOC, 'next-token-pairs.svg')


def context_helps() -> None:
    nt = _nt()
    names = ['guess at random\n(no model)', 'no context\n(just word counts)',
             'the word before', 'the two words before']
    losses = [nt.uniform, nt.none, nt.one, nt.two]
    perp = [float(np.exp(v)) for v in losses]
    for nm, lo, pp in zip(names, losses, perp):
        print(f'[nt] {nm.replace(chr(10), " "):34s} held-out loss {lo:.3f}  '
              f'perplexity {pp:.1f}')
    print(f'[nt] fitted on {_si(nt.n_train_pairs)} training pairs, '
          f'measured on {_si(nt.n_test_pairs)} held-out pairs')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    cols = [MUTED, GRIP, WRIST, SLIDE]
    ax.bar(range(4), losses, color=cols, width=0.55)
    for i, (lo, pp) in enumerate(zip(losses, perp)):
        ax.text(i, lo + 0.06, f'{lo:.3f}\n(like a choice between {pp:.1f} words)',
                ha='center', fontsize=9.5, weight='bold')
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylim(0, max(losses) * 1.22)
    ax.set_ylabel('held-out loss (lower is better)', fontsize=10)
    ax.set_title('More of the sentence to look at, less surprise at the next word',
                 fontsize=12, weight='bold')
    _save(fig, SSP_DOC, 'context-helps.svg')


def one_position_probabilities() -> None:
    nt = _nt()
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    for ax, ctx, truth in zip(axes, ['red', 'gripper'], ['cube', 'closed']):
        p = nt.after(ctx)
        order = np.argsort(-p)[:8]
        words = [CORPUS.words[i] for i in order]
        vals = p[order]
        loss = float(-np.log(p[CORPUS.index[truth]]))
        print(f'[nt] after "{ctx}": ' + ', '.join(f'{w} {v:.3f}' for w, v in zip(words, vals)))
        print(f'[nt] true next word "{truth}" has chance {p[CORPUS.index[truth]]:.3f}, '
              f'loss {loss:.3f}')
        _plain(ax)
        cols = [GRIP if w == truth else LINK for w in words]
        ax.barh(range(len(words))[::-1], vals, color=cols, height=0.6)
        for k, (w, v) in enumerate(zip(words, vals)):
            ax.text(v + 0.012, len(words) - 1 - k, f'{v:.3f}', va='center', fontsize=9.5)
        ax.set_yticks(range(len(words))[::-1])
        ax.set_yticklabels(words, fontsize=9.5)
        ax.set_xlim(0, max(vals) * 1.3)
        ax.set_xlabel('chance the model gives the word', fontsize=10)
        ax.set_title(f'after "{ctx}": true word "{truth}", loss {loss:.3f}',
                     fontsize=11.5, weight='bold')
    _save(fig, SSP_DOC, 'one-position-probabilities.svg')


def next_token_training_curve() -> None:
    nt = _nt()
    print(f'[nt] curve start {nt.hist1[0]:.3f}, the-word-before ends {nt.hist1[-1]:.3f}, '
          f'two-words-before ends {nt.hist2[-1]:.3f}')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    ax.axhline(nt.uniform, color=MUTED, ls='--', lw=1.4)
    ax.text(nt.at1[-1] * 0.98, nt.uniform + 0.03,
            f'guessing at random: {nt.uniform:.3f}', ha='right', fontsize=9.5, color=MUTED)
    ax.plot(nt.at1, nt.hist1, color=WRIST, lw=2.0, label='the word before')
    ax.plot(nt.at2, nt.hist2, color=SLIDE, lw=2.0, label='the two words before')
    ax.set_xlabel('gradient steps taken', fontsize=10)
    ax.set_ylabel('held-out loss', fontsize=10)
    ax.set_ylim(0, nt.uniform * 1.12)
    ax.set_title('Learning to guess the next word, with no labels anywhere',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    _save(fig, SSP_DOC, 'next-token-training-curve.svg')


# --------------------------------------------------------------------------
# page 1, section 3: masked prediction
# --------------------------------------------------------------------------

def fit_fill(mask: NDArray[np.bool_], n_train: int = 12000, seed: int = 42,
             ridge: float = 1.0) -> dict[str, object]:
    """Learn to fill the hidden pixels from the visible ones, by least squares.

    The thing the model is asked for is the picture without its pixel noise,
    because nobody can predict noise. The error is measured against that clean
    picture, and the comparison is a model that always answers with the average
    picture of the training set.
    """
    tr = Pics(n_train, seed=seed)
    te = Pics(3000, seed=seed + 1)
    vis, hid = tr.a[:, ~mask], tr.clean[0][:, mask]
    a = np.hstack([vis, np.ones((len(vis), 1))])
    gram = a.T @ a + ridge * np.eye(a.shape[1])
    w = np.linalg.solve(gram, a.T @ hid)
    base = hid.mean(axis=0)
    tv = np.hstack([te.a[:, ~mask], np.ones((len(te.a), 1))])
    pred = tv @ w
    truth = te.clean[0][:, mask]
    filled = te.a.copy()
    filled[:, mask] = pred
    return {
        'mae': float(np.mean(np.abs(pred - truth))),
        'mae_base': float(np.mean(np.abs(base[None, :] - truth))),
        'mae_noisy': float(np.mean(np.abs(pred - te.a[:, mask]))),
        'test': te,
        'filled': filled,
        'n_train': n_train,
    }


class Masked:
    """The masked-prediction run at one mask rate, plus the sweep over rates."""

    def __init__(self) -> None:
        self.rate = 0.5
        self.mask = _patch_mask(self.rate, seed=41)
        r = fit_fill(self.mask)
        self.mae = float(r['mae'])
        self.mae_base = float(r['mae_base'])
        self.mae_noisy = float(r['mae_noisy'])
        self.test: Pics = r['test']            # type: ignore[assignment]
        self.filled: Arr = r['filled']         # type: ignore[assignment]
        self.n_train = int(r['n_train'])
        self.rates = [0.2, 0.35, 0.5, 0.65, 0.8, 0.9]
        self.sweep: list[tuple[int, float, float]] = []
        for rate in self.rates:
            m = _patch_mask(rate, seed=50 + int(rate * 100))
            out = fit_fill(m, n_train=8000, seed=60)
            self.sweep.append((int(m.sum()), float(out['mae']), float(out['mae_base'])))


MK: Masked | None = None


def _mk() -> Masked:
    global MK
    if MK is None:
        MK = Masked()
    return MK


def masked_patches() -> None:
    mk = _mk()
    n_hidden_pixels = int(mk.mask.sum())
    per_side = SIDE // 2
    grid = mk.mask.reshape(SIDE, SIDE)
    n_patch_hidden = int(grid[::2, ::2].sum())
    pic = Pics(1, seed=71).a[0].reshape(SIDE, SIDE)
    shown = pic.copy()
    shown[grid] = np.nan
    print(f'[mask] {SIDE} by {SIDE} picture = {P} pixels, cut into '
          f'{per_side} by {per_side} = {per_side * per_side} patches of 2 by 2')
    print(f'[mask] mask rate {mk.rate:.0%} hides {n_patch_hidden} patches '
          f'= {n_hidden_pixels} pixels, leaving {P - n_hidden_pixels} visible')

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4.2), facecolor='white')
    for ax in axes:
        _blank(ax)
    vmin, vmax = float(pic.min()), float(pic.max())
    axes[0].imshow(pic, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
    axes[0].set_title(f'the simulated picture\n{P} pixels', fontsize=10.5, weight='bold')
    axes[1].imshow(pic, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
    for i in range(per_side):
        for j in range(per_side):
            hid = grid[2 * i, 2 * j]
            axes[1].add_patch(Rectangle((2 * j - 0.5, 2 * i - 0.5), 2, 2,
                                        facecolor=GRIP if hid else 'none',
                                        alpha=0.45 if hid else 1.0,
                                        edgecolor=LINK, lw=0.9))
    axes[1].set_title(f'{per_side * per_side} patches, {n_patch_hidden} of them\n'
                      f'picked to be hidden (red)', fontsize=10.5, weight='bold')
    axes[2].imshow(shown, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
    axes[2].set_title(f'what the model is shown\n{P - n_hidden_pixels} pixels',
                      fontsize=10.5, weight='bold')
    fig.suptitle('Masked prediction: the picture hides part of itself, '
                 'and the hidden part is the answer', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, SSP_DOC, 'masked-patches.svg')


def fill_the_gaps() -> None:
    mk = _mk()
    grid = mk.mask.reshape(SIDE, SIDE)
    print(f'[mask] learned fill: average error {mk.mae:.3f} per pixel against the '
          f'noise-free picture')
    print(f'[mask] always answering with the average picture: {mk.mae_base:.3f} per pixel')
    print(f'[mask] the learned fill is {100 * (1 - mk.mae / mk.mae_base):.0f} per cent better')
    print(f'[mask] measured against the noisy pixels instead it is {mk.mae_noisy:.3f}, '
          f'and the pixel noise alone is {PIXEL_NOISE:.1f}')

    fig, axes = plt.subplots(2, 3, figsize=(10.4, 7.2), facecolor='white')
    for row, k in enumerate([0, 1]):
        truth = mk.test.clean[0][k].reshape(SIDE, SIDE)
        shown = mk.test.a[k].reshape(SIDE, SIDE).copy()
        shown[grid] = np.nan
        guess = mk.filled[k].reshape(SIDE, SIDE)
        err = float(np.mean(np.abs(mk.filled[k][mk.mask] - mk.test.clean[0][k][mk.mask])))
        print(f'[mask] test picture {k + 1}: error of the filled part {err:.3f}')
        vmin, vmax = float(truth.min()), float(truth.max())
        for col, (img, name) in enumerate([(shown, 'shown to the model'),
                                           (guess, f'filled in (error {err:.2f})'),
                                           (truth, 'what was really there')]):
            ax = axes[row, col]
            _blank(ax)
            ax.imshow(img, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
            ax.set_title(f'picture {k + 1}: {name}', fontsize=10.5, weight='bold')
    fig.suptitle(f'Fitted on {_si(mk.n_train)} unlabelled pictures, the fill is '
                 f'{mk.mae:.2f} per pixel out, against {mk.mae_base:.2f} for answering '
                 f'with the average picture', fontsize=11.5, weight='bold', y=1.0)
    fig.subplots_adjust(hspace=0.28)
    _save(fig, SSP_DOC, 'fill-the-gaps.svg')


def mask_rate_curve() -> None:
    mk = _mk()
    for r, (n_hid, mae, base) in zip(mk.rates, mk.sweep):
        print(f'[mask] rate {r:.0%}: {n_hid} pixels hidden, learned error {mae:.3f}, '
              f'average-picture error {base:.3f}')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    xs = [r * 100 for r in mk.rates]
    ax.plot(xs, [s[1] for s in mk.sweep], marker='o', color=SLIDE, lw=2.0,
            label='the learned fill')
    ax.plot(xs, [s[2] for s in mk.sweep], marker='s', color=MUTED, lw=2.0, ls='--',
            label='always answering with the average picture')
    for x, s in zip(xs, mk.sweep):
        ax.text(x, s[1] + 0.07, f'{s[1]:.2f}', ha='center', fontsize=9, color=SLIDE)
    ax.set_xlabel('percentage of the patches hidden', fontsize=10)
    ax.set_ylabel('average error per hidden pixel', fontsize=10)
    ax.set_ylim(0, max(s[2] for s in mk.sweep) * 1.2)
    ax.set_title('Hide more of the picture, and filling it in gets harder',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center left')
    _save(fig, SSP_DOC, 'mask-rate-curve.svg')


class WordFill:
    """Filling in a hidden word from one side only, and from both sides."""

    def __init__(self) -> None:
        c = CORPUS
        xl, yl = c.both_sides_pairs(c.train_ids, left_only=True)
        xlv, ylv = c.both_sides_pairs(c.test_ids, left_only=True)
        self.wl, self.bl = softmax_fit(xl, yl, c.v, steps=4000, lr=1.5,
                                       weight_decay=1e-6, batch=512, seed=4)
        self.loss_left = softmax_loss(xlv, ylv, self.wl, self.bl)
        xb, yb = c.both_sides_pairs(c.train_ids, left_only=False)
        xbv, ybv = c.both_sides_pairs(c.test_ids, left_only=False)
        self.wb, self.bb = softmax_fit(xb, yb, c.v, steps=4000, lr=1.5,
                                       weight_decay=1e-6, batch=512, seed=5)
        self.loss_both = softmax_loss(xbv, ybv, self.wb, self.bb)
        self.n_jobs = len(yb)

    def left(self, before: str) -> Arr:
        x = np.zeros((1, CORPUS.v))
        x[0, CORPUS.index[before]] = 1.0
        return _softmax(x @ self.wl + self.bl)[0]

    def both(self, before: str, after: str) -> Arr:
        x = np.zeros((1, 2 * CORPUS.v))
        x[0, CORPUS.index[before]] = 1.0
        x[0, CORPUS.v + CORPUS.index[after]] = 1.0
        return _softmax(x @ self.wb + self.bb)[0]


def masked_word_fill() -> None:
    wf = WordFill()
    before, hidden, after = 'arm', 'moved', 'to'
    pl = wf.left(before)
    pb = wf.both(before, after)
    print(f'[wordfill] held-out loss from the word before only: {wf.loss_left:.3f}')
    print(f'[wordfill] held-out loss from both neighbours:      {wf.loss_both:.3f}')
    print(f'[wordfill] hidden word "{hidden}" between "{before}" and "{after}": '
          f'left only gives it {pl[CORPUS.index[hidden]]:.3f}, '
          f'both sides give it {pb[CORPUS.index[hidden]]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    for ax, p, name in zip(axes, [pl, pb],
                           [f'only the word before ("{before}")',
                            f'both neighbours ("{before}" ... "{after}")']):
        order = np.argsort(-p)[:6]
        words = [CORPUS.words[i] for i in order]
        vals = p[order]
        print(f'[wordfill] {name}: ' + ', '.join(f'{w} {v:.3f}' for w, v in zip(words, vals)))
        _plain(ax)
        cols = [GRIP if w == hidden else LINK for w in words]
        ax.barh(range(len(words))[::-1], vals, color=cols, height=0.6)
        for k, v in enumerate(vals):
            ax.text(v + 0.015, len(words) - 1 - k, f'{v:.3f}', va='center', fontsize=9.5)
        ax.set_yticks(range(len(words))[::-1])
        ax.set_yticklabels(words, fontsize=9.5)
        ax.set_xlim(0, 1.18)
        ax.set_xlabel(f'chance given to each word for the gap', fontsize=10)
        ax.set_title(f'guessing from {name}', fontsize=11, weight='bold')
    fig.suptitle(f'"the {before} ___ {after} the red cube": the word after the gap decides it',
                 fontsize=12.5, weight='bold', y=1.0)
    _save(fig, SSP_DOC, 'masked-word-fill.svg')


# --------------------------------------------------------------------------
# page 1, section 4: contrastive learning, worked out with real numbers
# --------------------------------------------------------------------------

class Contrastive:
    """A real CLIP-style run: two linear encoders trained on the batch-matching loss.

    The data is simulated. Each item has a hidden content vector; the picture
    vector and the caption vector are two different noisy linear views of it, so
    the only thing the two share is the content. The encoders are trained with
    the usual loss, which asks each picture to pick its own caption out of the
    batch and each caption to pick its own picture.
    """

    def __init__(self, n: int = 6000, dim_pic: int = 24, dim_txt: int = 20,
                 dim_out: int = 16, content: int = 5, noise: float = 2.2,
                 tau: float = 0.1, batch: int = 32, steps: int = 1500,
                 lr: float = 0.08, seed: int = 9) -> None:
        rng = np.random.default_rng(seed)
        c = rng.normal(size=(n, content))
        a_pic = rng.normal(size=(content, dim_pic))
        a_txt = rng.normal(size=(content, dim_txt))
        self.pic_raw = c @ a_pic + noise * rng.normal(size=(n, dim_pic))
        self.txt_raw = c @ a_txt + noise * rng.normal(size=(n, dim_txt))
        cut = int(0.8 * n)
        self.tau = tau
        self.batch = batch
        self.wp0 = rng.normal(0.0, dim_pic ** -0.5, size=(dim_pic, dim_out))
        self.wt0 = rng.normal(0.0, dim_txt ** -0.5, size=(dim_txt, dim_out))
        wp, wt = self.wp0.copy(), self.wt0.copy()
        self.train = (self.pic_raw[:cut], self.txt_raw[:cut])
        self.test = (self.pic_raw[cut:], self.txt_raw[cut:])
        self.at: list[int] = [0]
        self.hist: list[float] = [self.loss(wp, wt, tau, batch, seed=500)]
        for step in range(1, steps + 1):
            idx = rng.integers(0, cut, size=batch)
            p, t = self.train[0][idx], self.train[1][idx]
            gp, gt = self._grad(p, t, wp, wt, tau)
            wp -= lr * gp
            wt -= lr * gt
            if step % 25 == 0:
                self.at.append(step)
                self.hist.append(self.loss(wp, wt, tau, batch, seed=500))
        self.wp, self.wt = wp, wt

    @staticmethod
    def _unit(x: Arr) -> tuple[Arr, Arr]:
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        return x / norm, norm

    def embed(self, p: Arr, t: Arr, wp: Arr, wt: Arr) -> tuple[Arr, Arr]:
        u, _ = self._unit(p @ wp)
        v, _ = self._unit(t @ wt)
        return u, v

    def _grad(self, p: Arr, t: Arr, wp: Arr, wt: Arr, tau: float) -> tuple[Arr, Arr]:
        ap, np_ = p @ wp, None
        at = t @ wt
        u, nu = self._unit(ap)
        v, nv = self._unit(at)
        b = len(p)
        s = u @ v.T / tau
        pr = _softmax(s)
        pc = _softmax(s.T).T
        eye = np.eye(b)
        g = ((pr - eye) + (pc - eye)) / (2.0 * b)
        du = g @ v / tau
        dv = g.T @ u / tau
        da = (du - (np.sum(du * u, axis=1, keepdims=True)) * u) / nu
        db = (dv - (np.sum(dv * v, axis=1, keepdims=True)) * v) / nv
        return p.T @ da, t.T @ db

    def loss(self, wp: Arr, wt: Arr, tau: float, batch: int, seed: int = 500,
             n_batch: int = 40) -> float:
        rng = np.random.default_rng(seed)
        out = []
        for _ in range(n_batch):
            idx = rng.integers(0, len(self.test[0]), size=batch)
            u, v = self.embed(self.test[0][idx], self.test[1][idx], wp, wt)
            s = u @ v.T / tau
            pr = _softmax(s)
            pc = _softmax(s.T).T
            d = np.arange(batch)
            out.append(float(-0.5 * (np.mean(np.log(pr[d, d] + 1e-12))
                                     + np.mean(np.log(pc[d, d] + 1e-12)))))
        return float(np.mean(out))

    def grid(self, k: int, trained: bool = True, seed: int = 77) -> Arr:
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(self.test[0]), size=k)
        wp, wt = (self.wp, self.wt) if trained else (self.wp0, self.wt0)
        u, v = self.embed(self.test[0][idx], self.test[1][idx], wp, wt)
        return u @ v.T


CL: Contrastive | None = None


def _cl() -> Contrastive:
    global CL
    if CL is None:
        CL = Contrastive()
    return CL


def _draw_grid(ax: Axes, sim: Arr, title: str) -> None:
    k = len(sim)
    ax.imshow(sim, cmap='RdYlGn', vmin=-1, vmax=1, interpolation='nearest')
    for i in range(k):
        for j in range(k):
            ax.text(j, i, f'{sim[i, j]:+.2f}', ha='center', va='center', fontsize=9,
                    weight='bold' if i == j else 'normal')
    for i in range(k):
        ax.add_patch(Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=INK, lw=2.2))
    ax.set_xticks(range(k))
    ax.set_xticklabels([f'caption {j + 1}' for j in range(k)], fontsize=8.5, rotation=35,
                       ha='right')
    ax.set_yticks(range(k))
    ax.set_yticklabels([f'picture {i + 1}' for i in range(k)], fontsize=8.5)
    ax.set_title(title, fontsize=11, weight='bold')


def similarity_grid() -> None:
    cl = _cl()
    k = 6
    sim = cl.grid(k)
    diag = float(np.mean(np.diag(sim)))
    off = float(np.mean(sim[~np.eye(k, dtype=bool)]))
    print('[clip] similarity grid (trained), rows are pictures, columns captions:')
    for i in range(k):
        print('[clip]   ' + '  '.join(f'{sim[i, j]:+.2f}' for j in range(k)))
    print(f'[clip] mean matching pair {diag:+.3f}, mean non-matching pair {off:+.3f}')
    print(f'[clip] the biggest number in each row is on the diagonal: '
          f'{all(np.argmax(sim[i]) == i for i in range(k))}')
    fig, ax = plt.subplots(figsize=(7.2, 6.0), facecolor='white')
    ax.set_facecolor('white')
    _draw_grid(ax, sim, f'Every picture against every caption in a batch of {k}\n'
                        f'matching pairs average {diag:+.2f}, the rest {off:+.2f}')
    _save(fig, SSP_DOC, 'similarity-grid.svg')


def softmax_of_one_row() -> None:
    cl = _cl()
    k = 6
    r = 2                      # the row worked through: picture 3
    sim = cl.grid(k)
    row = sim[r]
    scaled = row / cl.tau
    p = _softmax(scaled[None, :])[0]
    loss = float(-np.log(p[r]))
    all_rows = _softmax(sim / cl.tau)
    mean_loss = float(-np.mean(np.log(np.diag(all_rows))))
    print(f'[clip] row {r + 1} similarities: ' + ', '.join(f'{v:+.3f}' for v in row))
    print(f'[clip] divided by the temperature {cl.tau}: '
          + ', '.join(f'{v:+.2f}' for v in scaled))
    print(f'[clip] after softmax: ' + ', '.join(f'{v:.3f}' for v in p))
    print(f'[clip] loss for row {r + 1} = -log({p[r]:.3f}) = {loss:.3f}; '
          f'guessing would give -log(1/{k}) = {np.log(k):.3f}')
    print(f'[clip] mean loss over the {k} rows of this batch: {mean_loss:.3f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    _plain(ax1)
    cols = [MUTED] * k
    cols[r] = SLIDE
    ax1.bar(range(k), row, color=cols, width=0.6)
    span = float(row.max() - min(row.min(), 0.0))
    for j, v in enumerate(row):
        ax1.text(j, v + (0.04 * span if v >= 0 else -0.13 * span), f'{v:+.2f}',
                 ha='center', fontsize=9.5)
    ax1.axhline(0, color=INK, lw=0.8)
    ax1.set_ylim(min(row.min() * 1.45, -0.05), row.max() * 1.25)
    ax1.set_xticks(range(k))
    ax1.set_xticklabels([f'cap {j + 1}' for j in range(k)], fontsize=9)
    ax1.set_ylabel(f'similarity to picture {r + 1}', fontsize=10)
    ax1.set_title(f'Picture {r + 1} against all six captions', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.bar(range(k), p, color=cols, width=0.6)
    for j, v in enumerate(p):
        ax2.text(j, v + 0.02, f'{v:.3f}', ha='center', fontsize=9.5)
    ax2.set_xticks(range(k))
    ax2.set_xticklabels([f'cap {j + 1}' for j in range(k)], fontsize=9)
    ax2.set_ylim(0, 1.12)
    ax2.set_ylabel('chance after dividing by 0.1 and softmax', fontsize=10)
    ax2.set_title(f'The right caption gets {p[r]:.3f}, so the loss is {loss:.3f}',
                  fontsize=11.5, weight='bold')
    fig.suptitle('The other five captions in the batch are the wrong answers, '
                 'and nobody had to write them', fontsize=12.5, weight='bold', y=1.0)
    _save(fig, SSP_DOC, 'softmax-of-one-row.svg')


def contrastive_training() -> None:
    cl = _cl()
    k = 6
    before = cl.grid(k, trained=False)
    after = cl.grid(k, trained=True)
    chance = float(np.log(cl.batch))
    print(f'[clip] held-out loss before training {cl.hist[0]:.3f}, '
          f'after {cl.hist[-1]:.3f}, guessing at random {chance:.3f}')
    print(f'[clip] before: matching {np.mean(np.diag(before)):+.3f}, '
          f'rest {np.mean(before[~np.eye(k, dtype=bool)]):+.3f}')
    print(f'[clip] after:  matching {np.mean(np.diag(after)):+.3f}, '
          f'rest {np.mean(after[~np.eye(k, dtype=bool)]):+.3f}')
    fig = plt.figure(figsize=(13.0, 4.8), facecolor='white')
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.set_facecolor('white')
    _draw_grid(ax1, before, 'before training')
    ax2 = fig.add_subplot(1, 3, 2)
    ax2.set_facecolor('white')
    _draw_grid(ax2, after, 'after training')
    ax3 = fig.add_subplot(1, 3, 3)
    _plain(ax3)
    ax3.plot(cl.at, cl.hist, color=LINK, lw=2.0)
    ax3.axhline(chance, color=MUTED, ls='--', lw=1.3)
    ax3.text(cl.at[-1], chance + 0.06, f'guessing: {chance:.2f}', ha='right', fontsize=9,
             color=MUTED)
    ax3.set_xlabel('gradient steps', fontsize=10)
    ax3.set_ylabel(f'held-out loss, batch of {cl.batch}', fontsize=10)
    ax3.set_ylim(0, chance * 1.15)
    ax3.set_title('the loss falling', fontsize=11, weight='bold')
    fig.suptitle('Pulling matching pairs together and pushing the rest apart',
                 fontsize=12.5, weight='bold', y=1.02)
    fig.subplots_adjust(wspace=0.55)
    _save(fig, SSP_DOC, 'contrastive-training.svg')


def batch_size_and_temperature() -> None:
    cl = _cl()
    sizes = [2, 4, 8, 16, 32, 64, 128]
    got = [cl.loss(cl.wp, cl.wt, cl.tau, b, seed=900) for b in sizes]
    chance = [float(np.log(b)) for b in sizes]
    taus = [0.02, 0.04, 0.07, 0.1, 0.15, 0.25, 0.4, 0.7, 1.0]
    by_tau = [cl.loss(cl.wp, cl.wt, t, 32, seed=901) for t in taus]
    best = taus[int(np.argmin(by_tau))]
    for b, g, c in zip(sizes, got, chance):
        print(f'[clip] batch {b:4d}: {b - 1:3d} wrong answers, trained loss {g:.3f}, '
              f'guessing {c:.3f}')
    for t, v in zip(taus, by_tau):
        print(f'[clip] temperature {t:.2f}: held-out loss {v:.3f}')
    print(f'[clip] the lowest loss is at temperature {best:.2f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    _plain(ax1)
    ax1.plot(sizes, chance, marker='s', ls='--', color=MUTED, lw=1.8,
             label='guessing at random')
    ax1.plot(sizes, got, marker='o', color=SLIDE, lw=2.0, label='the trained encoders')
    for b, g in zip(sizes, got):
        ax1.text(b, g - 0.18, f'{g:.2f}', ha='center', fontsize=9, color=SLIDE)
    ax1.set_xscale('log')
    ax1.set_xticks(sizes)
    ax1.set_xticklabels([str(s) for s in sizes])
    ax1.set_xlabel('pictures in the batch', fontsize=10)
    ax1.set_ylabel('held-out loss', fontsize=10)
    ax1.set_title('A bigger batch is a harder question', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper left')
    _plain(ax2)
    ax2.plot(taus, by_tau, marker='o', color=PURPLE, lw=2.0)
    ax2.axvline(best, color=GRIP, ls='--', lw=1.3)
    ax2.text(best * 1.08, max(by_tau) * 0.9, f'lowest at {best:.2f}', fontsize=9.5, color=GRIP)
    ax2.set_xscale('log')
    ax2.set_xlabel('temperature the similarities are divided by', fontsize=10)
    ax2.set_ylabel('held-out loss, batch of 32', fontsize=10)
    ax2.set_title('Too sharp or too flat, and the loss rises', fontsize=11.5, weight='bold')
    _save(fig, SSP_DOC, 'batch-size-and-temperature.svg')


# --------------------------------------------------------------------------
# page 1, section 5: self-distillation, the two-crops idea
# --------------------------------------------------------------------------

def _entropy(p: Arr) -> float:
    return float(-np.sum(p * np.log(p + 1e-12)))


def _unit_rows(x: Arr) -> Arr:
    return x / np.linalg.norm(x, axis=1, keepdims=True)


class Distill:
    """A real self-distillation run on two crops of the same simulated picture.

    The student turns a crop into sixteen numbers, makes their length one, and
    scores them against K prototype directions. The teacher is the same thing
    with weights that are a moving average of the student's, it looks at the
    other crop, and its scores are sharpened and have a running average taken
    off them. The student is trained to say what the teacher said. No label is
    used anywhere, and the only thing the two crops have in common is the item
    they were cut from.
    """

    def __init__(self, k: int = 8, dh: int = 16, n: int = 6000, steps: int = 2000,
                 batch: int = 64, lr: float = 0.5, momentum: float = 0.99,
                 t_student: float = 0.1, t_teacher: float = 0.04,
                 centre_momentum: float = 0.9, seed: int = 13) -> None:
        self.k, self.dh, self.steps = k, dh, steps
        self.momentum, self.t_student, self.t_teacher = momentum, t_student, t_teacher
        self.rows = SIDE * 3 // 5
        self.overlap = 2 * self.rows - SIDE
        self.pics = Pics(n, seed=seed, views=2)
        self.crop_a = self._crop(self.pics.a, top=True)
        self.crop_b = self._crop(self.pics.b, top=False)
        self.mu = self.crop_a.mean(axis=0)
        self.sd = float(self.crop_a.std())
        self.crop_a = (self.crop_a - self.mu) / self.sd
        self.crop_b = (self.crop_b - self.mu) / self.sd
        held = Pics(2000, seed=seed + 40, views=2)
        self.test_a = (self._crop(held.a, top=True) - self.mu) / self.sd
        self.test_b = (self._crop(held.b, top=False) - self.mu) / self.sd
        rng = np.random.default_rng(seed + 1)
        d = self.crop_a.shape[1]
        w = rng.normal(0.0, d ** -0.5, size=(d, dh))
        c = _unit_rows((rng.normal(0.0, dh ** -0.5, size=(dh, k))).T).T
        self.w0, self.c0 = w.copy(), c.copy()
        w_t, c_t = w.copy(), c.copy()
        centre = np.zeros(k)
        self.at: list[int] = []
        self.loss: list[float] = []
        self.spread: list[float] = []
        self.same: list[float] = []
        self.diff: list[float] = []
        self.agree: list[float] = []
        for step in range(steps + 1):
            idx = rng.integers(0, n, size=batch)
            xs = np.vstack([self.crop_a[idx], self.crop_b[idx]])
            xo = np.vstack([self.crop_b[idx], self.crop_a[idx]])
            h = xs @ w
            nh = np.linalg.norm(h, axis=1, keepdims=True)
            u = h / nh
            ps = _softmax(u @ c / t_student)
            ut = _unit_rows(xo @ w_t)
            lt = ut @ c_t
            pt = _softmax((lt - centre) / t_teacher)
            g = (ps - pt) / (t_student * len(ps))
            dh_ = (g @ c.T - np.sum((g @ c.T) * u, axis=1, keepdims=True) * u) / nh
            w -= lr * (xs.T @ dh_)
            c -= lr * (u.T @ g)
            c /= np.linalg.norm(c, axis=0, keepdims=True)
            w_t = momentum * w_t + (1.0 - momentum) * w
            c_t = momentum * c_t + (1.0 - momentum) * c
            c_t /= np.linalg.norm(c_t, axis=0, keepdims=True)
            centre = centre_momentum * centre + (1.0 - centre_momentum) * lt.mean(axis=0)
            if step % 20 == 0:
                self.at.append(step)
                self.loss.append(float(-np.mean(np.sum(pt * np.log(ps + 1e-12), axis=1))))
                self.spread.append(_entropy(ps.mean(axis=0)))
                sm_, df_, ag_ = self._measure(w, c)
                self.same.append(sm_)
                self.diff.append(df_)
                self.agree.append(ag_)
        self.w, self.c, self.c_t, self.w_t, self.centre = w, c, c_t, w_t, centre

    def _crop(self, pic: Arr, top: bool) -> Arr:
        sq = pic.reshape(len(pic), SIDE, SIDE)
        return (sq[:, :self.rows, :] if top else sq[:, SIDE - self.rows:, :]
                ).reshape(len(pic), -1)

    def _measure(self, w: Arr, c: Arr) -> tuple[float, float, float]:
        ua = _unit_rows(self.test_a @ w)
        ub = _unit_rows(self.test_b @ w)
        same = float(np.mean(np.sum(ua * ub, axis=1)))
        rolled = np.roll(ub, 1, axis=0)
        diff = float(np.mean(np.sum(ua * rolled, axis=1)))
        pa = np.argmax(ua @ c, axis=1)
        pb = np.argmax(ub @ c, axis=1)
        return same, diff, float(np.mean(pa == pb))

    def pairs(self, trained: bool) -> tuple[Arr, Arr]:
        w = self.w if trained else self.w0
        ua = _unit_rows(self.test_a @ w)
        ub = _unit_rows(self.test_b @ w)
        same = np.sum(ua * ub, axis=1)
        diff = np.sum(ua * np.roll(ub, 1, axis=0), axis=1)
        return same, diff


DS: Distill | None = None


def _ds() -> Distill:
    global DS
    if DS is None:
        DS = Distill()
    return DS


def two_crops() -> None:
    ds = _ds()
    pic_a = ds.pics.a[0].reshape(SIDE, SIDE)
    pic_b = ds.pics.b[0].reshape(SIDE, SIDE)
    shared = ds.pics.content[0].reshape(SIDE, SIDE)
    print(f'[dino] picture {SIDE} by {SIDE}; each crop is {ds.rows} rows by {SIDE} '
          f'columns = {ds.rows * SIDE} pixels')
    print(f'[dino] the two crops share {ds.overlap} rows, and they come from two views '
          f'of the same item, so the lighting part of the picture differs as well')
    content_sd = float(ds.pics.content.std())
    light_sd = float((ds.pics.clean[0] - ds.pics.content).std())
    print(f'[dino] across the batch the shared part has a spread of {content_sd:.2f} per '
          f'pixel, the lighting part {light_sd:.2f}, and the noise {PIXEL_NOISE:.2f}')
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 4.0), facecolor='white')
    for ax in axes:
        _blank(ax)
    vmin = float(min(pic_a.min(), pic_b.min()))
    vmax = float(max(pic_a.max(), pic_b.max()))
    axes[0].imshow(pic_a, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
    axes[0].add_patch(Rectangle((-0.5, -0.5), SIDE, ds.rows, fill=False, edgecolor=LINK,
                                lw=2.6))
    axes[0].set_title(f'view one,\ntop {ds.rows} rows taken', fontsize=10.5, weight='bold')
    axes[1].imshow(pic_b, cmap='Greys_r', vmin=vmin, vmax=vmax, interpolation='nearest')
    axes[1].add_patch(Rectangle((-0.5, SIDE - ds.rows - 0.5), SIDE, ds.rows, fill=False,
                                edgecolor=GRIP, lw=2.6))
    axes[1].set_title(f'view two,\nbottom {ds.rows} rows taken', fontsize=10.5,
                      weight='bold')
    gap = np.full((2, SIDE), np.nan)
    crop_map = matplotlib.colormaps['Greys_r'].with_extremes(bad='white')
    axes[2].imshow(np.vstack([pic_a[:ds.rows], gap, pic_b[SIDE - ds.rows:]]),
                   cmap=crop_map, vmin=vmin, vmax=vmax, interpolation='nearest')
    axes[2].set_title(f'the two crops,\neach {ds.rows * SIDE} pixels', fontsize=10.5,
                      weight='bold')
    axes[3].imshow(shared, cmap='Greys_r', interpolation='nearest')
    axes[3].set_title('the part the two views share,\nwhich decides the class',
                      fontsize=10.5, weight='bold')
    fig.suptitle('Two crops of one item: the object is the same, '
                 'and the lighting and the noise are not',
                 fontsize=12.5, weight='bold', y=1.04)
    _save(fig, SSP_DOC, 'two-crops.svg')


def teacher_and_student() -> None:
    ds = _ds()
    i = 0
    ps = _softmax(_unit_rows(ds.crop_a[i:i + 1] @ ds.w) @ ds.c / ds.t_student)[0]
    lt = _unit_rows(ds.crop_b[i:i + 1] @ ds.w_t) @ ds.c_t
    pt = _softmax((lt - ds.centre) / ds.t_teacher)[0]
    loss = float(-np.sum(pt * np.log(ps + 1e-12)))
    print('[dino] student on crop one: ' + ', '.join(f'{v:.3f}' for v in ps))
    print('[dino] teacher on crop two: ' + ', '.join(f'{v:.3f}' for v in pt))
    print(f'[dino] both pick prototype {int(np.argmax(ps)) + 1}, and the loss for this '
          f'item is {loss:.3f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    for ax, p, name, col in [(ax1, ps, f'student on crop one, divided by {ds.t_student}',
                              LINK),
                             (ax2, pt, f'teacher on crop two, divided by {ds.t_teacher}',
                              PURPLE)]:
        _plain(ax)
        ax.bar(range(1, ds.k + 1), p, color=col, width=0.6)
        for j, v in enumerate(p):
            if v > 0.005:
                ax.text(j + 1, v + 0.02, f'{v:.3f}', ha='center', fontsize=9)
        ax.set_ylim(0, 1.14)
        ax.set_xticks(range(1, ds.k + 1))
        ax.set_xlabel('prototype', fontsize=10)
        ax.set_ylabel('share given to the prototype', fontsize=10)
        ax.set_title(name, fontsize=11, weight='bold')
    fig.suptitle(f'The teacher is sharper, and the student is trained to repeat it: '
                 f'loss {loss:.3f}', fontsize=12.5, weight='bold', y=1.0)
    _save(fig, SSP_DOC, 'teacher-and-student.svg')


def agreement_rises() -> None:
    ds = _ds()
    best = float(np.log(ds.k))
    print(f'[dino] loss between teacher and student: {ds.loss[0]:.3f} at the start, '
          f'{ds.loss[-1]:.3f} at the end')
    print(f'[dino] the two crops are given the same prototype '
          f'{ds.agree[0]:.1%} of the time at the start and {ds.agree[-1]:.1%} at the end, '
          f'where guessing gives {1 / ds.k:.1%}')
    print(f'[dino] spread of the answers over the {ds.k} prototypes: {ds.spread[0]:.3f} '
          f'at the start, {ds.spread[-1]:.3f} at the end, and {best:.3f} would be '
          f'all prototypes used equally')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white')
    _plain(ax1)
    ax1.plot(ds.at, ds.loss, color=LINK, lw=2.0)
    ax1.set_xlabel('gradient steps', fontsize=10)
    ax1.set_ylabel("loss against the teacher's answer", fontsize=10)
    ax1.set_ylim(0, max(ds.loss) * 1.08)
    ax1.set_title(f'the student learns to agree: {ds.loss[0]:.2f} down to '
                  f'{ds.loss[-1]:.2f}', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.plot(ds.at, [100 * a for a in ds.agree], color=SLIDE, lw=2.0,
             label='both crops given the same prototype')
    ax2.axhline(100 / ds.k, color=MUTED, ls='--', lw=1.3,
                label=f'guessing: {100 / ds.k:.0f} per cent')
    ax2.set_xlabel('gradient steps', fontsize=10)
    ax2.set_ylabel('per cent of held-out items', fontsize=10)
    ax2.set_ylim(0, 105)
    ax2.set_title('two crops, one answer, on items never trained on',
                  fontsize=11.5, weight='bold')
    ax2.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.subplots_adjust(wspace=0.3)
    _save(fig, SSP_DOC, 'agreement-rises.svg')


def same_item_closer() -> None:
    ds = _ds()
    before_same, before_diff = ds.pairs(trained=False)
    after_same, after_diff = ds.pairs(trained=True)
    print(f'[dino] before training: two crops of the same item {before_same.mean():+.3f}, '
          f'crops of different items {before_diff.mean():+.3f}')
    print(f'[dino] after training:  two crops of the same item {after_same.mean():+.3f}, '
          f'crops of different items {after_diff.mean():+.3f}')
    print(f'[dino] the gap went from {before_same.mean() - before_diff.mean():.3f} to '
          f'{after_same.mean() - after_diff.mean():.3f}')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white')
    bins = np.linspace(-1, 1, 41)
    for ax, (sm_, df_, name) in zip(axes, [(before_same, before_diff, 'before training'),
                                           (after_same, after_diff, 'after training')]):
        _plain(ax)
        ax.hist(df_, bins=bins, color=MUTED, alpha=0.75, label='two different items')
        ax.hist(sm_, bins=bins, color=SLIDE, alpha=0.75, label='two crops of one item')
        ax.axvline(float(sm_.mean()), color=SLIDE, lw=1.6)
        ax.axvline(float(df_.mean()), color=INK, lw=1.6, ls='--')
        ax.set_xlim(-1, 1)
        ax.set_xlabel('similarity of the two sets of sixteen numbers', fontsize=10)
        ax.set_ylabel('held-out pairs', fontsize=10)
        ax.set_title(f'{name}: same item {sm_.mean():+.2f}, different '
                     f'{df_.mean():+.2f}', fontsize=11, weight='bold')
        ax.legend(fontsize=9, frameon=False, loc='upper left')
    fig.suptitle('What the two-crops rule buys: the same object in two views lands in '
                 'the same place', fontsize=12.5, weight='bold', y=1.0)
    _save(fig, SSP_DOC, 'same-item-closer.svg')




# --------------------------------------------------------------------------
# page 1, section 6: what a pretrained representation is, and what it buys
#
# The backbone here is fitted on unlabelled pairs of views by the plainest
# method of the two-crops kind that can be worked out exactly: it keeps the
# directions of the picture on which the two views of one item agree, and throws
# away the directions where they disagree. No label is used to fit it. It is
# then frozen, and only a small head is trained on labelled examples.
# --------------------------------------------------------------------------

def mlp_fit(x: Arr, y: NDArray[np.int64], n_class: int, hidden: int = 32,
            steps: int = 4000, lr: float = 0.1, weight_decay: float = 1e-3,
            batch: int = 64, seed: int = 0) -> tuple[Arr, Arr, Arr, Arr]:
    """A small network with one hidden layer and a ReLU, fitted by mini-batch descent."""
    rng = np.random.default_rng(seed)
    n, d = x.shape
    w1 = rng.normal(0.0, np.sqrt(2.0 / d), size=(d, hidden))
    b1 = np.zeros(hidden)
    w2 = rng.normal(0.0, np.sqrt(2.0 / hidden), size=(hidden, n_class))
    b2 = np.zeros(n_class)
    for _ in range(steps):
        idx = rng.integers(0, n, size=min(batch, n))
        xb, yb = x[idx], y[idx]
        pre = xb @ w1 + b1
        hid = np.maximum(pre, 0.0)
        p = _softmax(hid @ w2 + b2)
        g = p.copy()
        g[np.arange(len(yb)), yb] -= 1.0
        g /= len(yb)
        gw2 = hid.T @ g + weight_decay * w2
        gb2 = g.sum(axis=0)
        gh = g @ w2.T
        gh[pre <= 0.0] = 0.0
        w1 -= lr * (xb.T @ gh + weight_decay * w1)
        b1 -= lr * gh.sum(axis=0)
        w2 -= lr * gw2
        b2 -= lr * gb2
    return w1, b1, w2, b2


def mlp_acc(x: Arr, y: NDArray[np.int64], par: tuple[Arr, Arr, Arr, Arr]) -> float:
    w1, b1, w2, b2 = par
    return float(np.mean(np.argmax(np.maximum(x @ w1 + b1, 0.0) @ w2 + b2, axis=1) == y))


def mlp_params(d: int, hidden: int, n_class: int) -> int:
    return d * hidden + hidden + hidden * n_class + n_class


class Backbone:
    """A frozen representation fitted on unlabelled pairs, and what it buys."""

    def __init__(self, n_unlabelled: int = 20000, k: int = 8, hidden_head: int = 16,
                 hidden_scratch: int = 32, ridge: float = 1e-3, seed: int = 301) -> None:
        self.k = k
        self.hidden_head = hidden_head
        self.hidden_scratch = hidden_scratch
        self.n_unlabelled = n_unlabelled
        un = Pics(n_unlabelled, seed=seed, views=2)
        xa, xb = un.a, un.b
        self.mu = xa.mean(axis=0)
        ca = (xa - self.mu)
        cb = (xb - xb.mean(axis=0))
        caa = ca.T @ ca / n_unlabelled
        cbb = cb.T @ cb / n_unlabelled
        cab = ca.T @ cb / n_unlabelled
        eps = ridge * float(np.trace(caa)) / P

        def inv_sqrt(c: Arr) -> Arr:
            val, vec = np.linalg.eigh(c + eps * np.eye(P))
            return vec @ np.diag(val ** -0.5) @ vec.T

        ia, ib = inv_sqrt(caa), inv_sqrt(cbb)
        u, sing, _ = np.linalg.svd(ia @ cab @ ib)
        self.correlations = sing[:12]
        self.w_two_view = ia @ u[:, :k]
        f = (xa - self.mu) @ self.w_two_view
        self.scale_two_view = f.std(axis=0)
        val, vec = np.linalg.eigh(caa)
        order = np.argsort(-val)
        self.pca_val = val[order]
        self.w_pca = vec[:, order[:k]]
        g = (xa - self.mu) @ self.w_pca
        self.scale_pca = g.std(axis=0)
        self.un = un
        self.test = Pics(4000, seed=seed + 1)
        self.sizes = [50, 100, 200, 400, 800, 1600, 3200]
        self.curves: dict[str, list[float]] = {'frozen backbone': [], 'top 8 directions': [],
                                               'from scratch': []}
        for n in self.sizes:
            got: dict[str, list[float]] = {key: [] for key in self.curves}
            for rep in range(2):
                tr = Pics(n, seed=900 + n + 7 * rep)
                got['frozen backbone'].append(mlp_acc(
                    self.features(self.test.a), self.test.cls,
                    mlp_fit(self.features(tr.a), tr.cls, 4, hidden=hidden_head,
                            steps=3000, lr=0.15, seed=rep)))
                got['top 8 directions'].append(mlp_acc(
                    self.pca_features(self.test.a), self.test.cls,
                    mlp_fit(self.pca_features(tr.a), tr.cls, 4, hidden=hidden_head,
                            steps=3000, lr=0.15, seed=rep)))
                got['from scratch'].append(mlp_acc(
                    self.test.a / 10.0, self.test.cls,
                    mlp_fit(tr.a / 10.0, tr.cls, 4, hidden=hidden_scratch,
                            steps=5000, lr=0.1, seed=rep)))
            for key in self.curves:
                self.curves[key].append(float(np.mean(got[key])))

    def features(self, x: Arr) -> Arr:
        return ((x - self.mu) @ self.w_two_view) / self.scale_two_view

    def pca_features(self, x: Arr) -> Arr:
        return ((x - self.mu) @ self.w_pca) / self.scale_pca

    def labels_to_reach(self, key: str, target: float) -> float | None:
        """How many labels this curve needs to reach the target, read off the curve."""
        xs, ys = self.sizes, self.curves[key]
        for i in range(1, len(xs)):
            if ys[i] >= target >= ys[i - 1]:
                t = (target - ys[i - 1]) / (ys[i] - ys[i - 1] + 1e-12)
                return float(np.exp(np.log(xs[i - 1]) + t * (np.log(xs[i] / xs[i - 1]))))
        return None


BB: Backbone | None = None


def _bb() -> Backbone:
    global BB
    if BB is None:
        BB = Backbone()
    return BB


def backbone_and_head() -> None:
    bb = _bb()
    back_numbers = P * bb.k
    head = mlp_params(bb.k, bb.hidden_head, 4)
    scratch = mlp_params(P, bb.hidden_scratch, 4)
    print(f'[frozen] this demonstration: backbone {_si(back_numbers)} numbers, fitted on '
          f'{_si(bb.n_unlabelled)} unlabelled pairs and then frozen')
    print(f'[frozen] head trained on the labels: {head} parameters')
    print(f'[frozen] the same job from scratch: {scratch} parameters, all of them trained')
    print(f'[frozen] so the head trains {head / scratch:.3%} as many parameters')
    layers, width, classes = 24, 1024, 20
    big_back = 12 * width * width * layers
    big_head = width * classes + classes
    print(f'[frozen] an example full-size backbone of {layers} blocks and width {width}: '
          f'{big_back / 1e6:.0f} million parameters')
    print(f'[frozen] a head of {classes} classes on top of it: {_si(big_head)} parameters, '
          f'which is {big_head / big_back:.5%} of the backbone')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8), facecolor='white')
    _plain(ax1)
    ax1.bar([0, 1, 2], [back_numbers, head, scratch], color=[MUTED, SLIDE, GRIP], width=0.55)
    for i, v in enumerate([back_numbers, head, scratch]):
        ax1.text(i, v * 1.35, _si(v), ha='center', fontsize=10.5, weight='bold')
    ax1.set_yscale('log')
    ax1.set_ylim(50, back_numbers * 40)
    ax1.set_xticks([0, 1, 2])
    ax1.set_xticklabels(['the frozen\nbackbone', 'the head\n(trained)',
                         'the whole network,\nfrom scratch'], fontsize=9)
    ax1.set_ylabel('numbers in the model (log scale)', fontsize=10)
    ax1.set_title('This page\'s demonstration', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.bar([0, 1], [big_back, big_head], color=[MUTED, SLIDE], width=0.5)
    ax2.text(0, big_back * 1.4, f'{big_back / 1e6:.0f} million', ha='center',
             fontsize=10.5, weight='bold')
    ax2.text(1, big_head * 1.4, _si(big_head), ha='center', fontsize=10.5, weight='bold')
    ax2.set_yscale('log')
    ax2.set_ylim(1e3, big_back * 60)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels([f'example backbone:\n{layers} blocks, width {width}',
                         f'head for {classes} classes'], fontsize=9.5)
    ax2.set_ylabel('parameters (log scale)', fontsize=10)
    ax2.set_title(f'An example full-size pair: the head is '
                  f'{big_head / big_back:.4%} of it', fontsize=11.5, weight='bold')
    _save(fig, SSP_DOC, 'backbone-and-head.svg')


def what_the_features_track() -> None:
    bb = _bb()
    pics = Pics(4000, seed=777)
    factors = np.hstack([pics.z, pics.nuisance[0]])
    names = [f'content {i + 1}' for i in range(N_CONTENT)] + \
            [f'lighting {i + 1}' for i in range(N_NUISANCE)]
    grids = {}
    for key, fn in [('fitted on two views', bb.features),
                    ('top 8 directions of the pictures', bb.pca_features)]:
        feats = fn(pics.a)
        g = np.zeros((bb.k, factors.shape[1]))
        for i in range(bb.k):
            for j in range(factors.shape[1]):
                g[i, j] = abs(np.corrcoef(feats[:, i], factors[:, j])[0, 1])
        grids[key] = g
        content = float(g[:, :N_CONTENT].max(axis=1).mean())
        nuis = float(g[:, N_CONTENT:].max(axis=1).mean())
        print(f'[frozen] {key}: average best match with a content factor {content:.3f}, '
              f'with a lighting factor {nuis:.3f}')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white')
    for ax, (key, g) in zip(axes, grids.items()):
        ax.set_facecolor('white')
        im = ax.imshow(g, cmap='Blues', vmin=0, vmax=1, interpolation='nearest')
        for i in range(g.shape[0]):
            for j in range(g.shape[1]):
                ax.text(j, i, f'{g[i, j]:.2f}', ha='center', va='center', fontsize=7.5,
                        color='white' if g[i, j] > 0.55 else INK)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, fontsize=8, rotation=40, ha='right')
        ax.set_yticks(range(bb.k))
        ax.set_yticklabels([f'feature {i + 1}' for i in range(bb.k)], fontsize=8)
        ax.axvline(N_CONTENT - 0.5, color=GRIP, lw=2.0)
        ax.set_title(key, fontsize=11, weight='bold')
        fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    fig.suptitle('What each learned feature follows: the two-view backbone keeps the '
                 'content and drops the lighting', fontsize=12.5, weight='bold', y=1.02)
    fig.subplots_adjust(wspace=0.5)
    _save(fig, SSP_DOC, 'what-the-features-track.svg')


def few_labels_beat_many() -> None:
    bb = _bb()
    print('[frozen] canonical correlations of the two views: '
          + ', '.join(f'{v:.3f}' for v in bb.correlations[:9]))
    for key, ys in bb.curves.items():
        print(f'[frozen] {key:18s} ' + '  '.join(f'n={n}:{v:.3f}'
                                                 for n, v in zip(bb.sizes, ys)))
    fig, ax = plt.subplots(figsize=(10.2, 5.4), facecolor='white')
    _plain(ax)
    style = {'frozen backbone': (SLIDE, 'o', 'a small head on the frozen backbone'),
             'top 8 directions': (WRIST, '^', 'a small head on the 8 biggest directions'),
             'from scratch': (GRIP, 's', 'the same size of network, from scratch on pixels')}
    for key, ys in bb.curves.items():
        col, mark, label = style[key]
        ax.plot(bb.sizes, [100 * v for v in ys], marker=mark, color=col, lw=2.0, label=label)
    ax.axhline(25, color=MUTED, ls=':', lw=1.2)
    ax.text(bb.sizes[0], 26.5, 'guessing one of four: 25 per cent', ha='left',
            fontsize=9, color=MUTED)
    ax.set_xscale('log')
    ax.set_xticks(bb.sizes)
    ax.set_xticklabels([str(s) for s in bb.sizes])
    ax.set_xlabel('labelled examples used (log scale)', fontsize=10)
    ax.set_ylabel('accuracy on 4,000 held-out pictures (per cent)', fontsize=10)
    ax.set_ylim(20, 103)
    ax.set_title('200 labels on a frozen backbone beat 800 labels from scratch',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, SSP_DOC, 'few-labels-beat-many.svg')


def labels_needed() -> None:
    bb = _bb()
    targets = [0.80, 0.90, 0.95]
    rows: dict[str, list[float | None]] = {}
    for key in bb.curves:
        rows[key] = [bb.labels_to_reach(key, t) for t in targets]
        for t, v in zip(targets, rows[key]):
            got = f'{v:.0f}' if v is not None else 'never, up to 3,200'
            print(f'[frozen] {key:18s} needs {got} labels to reach {t:.0%}')
    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    width = 0.26
    cols = {'frozen backbone': SLIDE, 'top 8 directions': WRIST, 'from scratch': GRIP}
    for off, (key, vals) in zip([-width, 0.0, width], rows.items()):
        xs = np.arange(len(targets)) + off
        heights = [v if v is not None else 6000.0 for v in vals]
        alphas = [1.0 if v is not None else 0.3 for v in vals]
        for x, h, al in zip(xs, heights, alphas):
            ax.bar([x], [h], width=width, color=cols[key], alpha=al,
                   hatch='' if al == 1.0 else '//')
        ax.bar([xs[0]], [0.0], width=width, color=cols[key], label=key)
        for x, v in zip(xs, vals):
            if v is None:
                ax.text(x, 300, 'never, even\nwith 3,200', ha='center', fontsize=8.5,
                        rotation=90, color=INK)
            else:
                ax.text(x, v * 1.08, f'{v:.0f}', ha='center', fontsize=9.5, weight='bold')
    ax.set_yscale('log')
    ax.set_ylim(30, 40000)
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels([f'{t:.0%} accuracy' for t in targets], fontsize=10)
    ax.set_ylabel('labelled examples needed (log scale)', fontsize=10)
    ax.set_title('How many labels each way of working needs to reach the same accuracy',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SSP_DOC, 'labels-needed.svg')


# ==========================================================================
# page 2: 02_scale-data-and-compute.md
#
# Everything below is arithmetic on example configurations that are stated in
# full. The example model, the example accelerator and the scaling formula are
# written for this page; none of them is a measurement of a real product.
# ==========================================================================

# the example model: a transformer of 32 blocks, width 4096, vocabulary 128,000
EX_LAYERS: int = 32
EX_WIDTH: int = 4096
EX_VOCAB: int = 128_000
EX_SEQ: int = 4096

# the example accelerator
EX_FLOPS: float = 4.0e14          # floating-point operations a second, at full stretch
EX_BAND: float = 2.0e12           # bytes a second between its memory and its arithmetic
EX_MEM: float = 80e9              # bytes of memory on the card
EX_USE: float = 0.40              # share of the arithmetic a real run keeps busy

BYTES: dict[str, float] = {'float32': 4.0, 'bfloat16': 2.0, 'float16': 2.0,
                           'int8': 1.0, 'int4': 0.5}


def transformer_params(layers: int = EX_LAYERS, width: int = EX_WIDTH,
                       vocab: int = EX_VOCAB) -> dict[str, float]:
    """Parameters of the example transformer, split into the three places they sit."""
    attention = 4.0 * width * width * layers
    feed_forward = 8.0 * width * width * layers
    embedding = float(vocab) * width
    return {'attention': attention, 'feed-forward': feed_forward,
            'embedding table': embedding,
            'total': attention + feed_forward + embedding}


# --------------------------------------------------------------------------
# page 2, section 1: what a graphics processing unit does
# --------------------------------------------------------------------------

def one_matrix_multiply() -> None:
    rng = np.random.default_rng(21)
    a = rng.integers(-3, 4, size=(4, 3)).astype(float)
    b = rng.integers(-3, 4, size=(3, 5)).astype(float)
    c = a @ b
    row, col = 1, 2
    terms = [f'({a[row, k]:.0f} x {b[k, col]:.0f})' for k in range(3)]
    print(f'[gpu] a {a.shape[0]} by {a.shape[1]} grid times a {b.shape[0]} by '
          f'{b.shape[1]} grid gives a {c.shape[0]} by {c.shape[1]} grid')
    print(f'[gpu] cell (row {row + 1}, column {col + 1}) = '
          + ' + '.join(terms) + f' = {c[row, col]:.0f}')
    print(f'[gpu] the whole thing is {c.shape[0]} x {c.shape[1]} x {a.shape[1]} = '
          f'{c.size * a.shape[1]} multiply-and-add pairs, and no cell needs any other cell')

    fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.0), facecolor='white',
                             gridspec_kw={'width_ratios': [0.9, 1.1, 1.1]})
    for ax, grid, name, mark in [(axes[0], a, 'the first grid', ('row', row)),
                                 (axes[1], b, 'the second grid', ('col', col)),
                                 (axes[2], c, 'the answer', ('cell', (row, col)))]:
        _blank(ax)
        n_r, n_c = grid.shape
        ax.set_xlim(-0.6, n_c - 0.4)
        ax.set_ylim(n_r - 0.4, -0.6)
        for i in range(n_r):
            for j in range(n_c):
                hot = ((mark[0] == 'row' and i == mark[1])
                       or (mark[0] == 'col' and j == mark[1])
                       or (mark[0] == 'cell' and (i, j) == mark[1]))
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1,
                                       facecolor=LINK_PALE if hot else 'white',
                                       edgecolor=GRID, lw=1.0))
                ax.text(j, i, f'{grid[i, j]:.0f}', ha='center', va='center',
                        fontsize=10.5 if n_c < 6 else 9.5,
                        weight='bold' if hot else 'normal')
        ax.set_title(f'{name}, {n_r} by {n_c}', fontsize=11, weight='bold')
    fig.suptitle(f'One cell of the answer is {" + ".join(terms)} = {c[row, col]:.0f}, '
                 f'and all {c.size} cells can be worked out at the same time',
                 fontsize=12, weight='bold', y=1.02)
    fig.subplots_adjust(wspace=0.3)
    _save(fig, SDC_DOC, 'one-matrix-multiply.svg')


def work_and_independence() -> None:
    sizes = [64, 256, 1024, 4096, 16384]
    work = [2.0 * n ** 3 for n in sizes]
    cells = [float(n * n) for n in sizes]
    for n, w, c in zip(sizes, work, cells):
        print(f'[gpu] {n} by {n}: {w:.3e} operations, spread over {c:.3e} cells, '
              f'{w / c:.0f} operations each')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(sizes, work, marker='o', color=GRIP, lw=2.0,
            label='operations in the multiply (2 x n x n x n)')
    ax.plot(sizes, cells, marker='s', color=SLIDE, lw=2.0,
            label='cells that can be worked out at the same time (n x n)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('side of the square grid, n', fontsize=10)
    ax.set_ylabel('count (log scale)', fontsize=10)
    ax.set_title('A matrix multiply is a huge amount of work cut into independent pieces',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'work-and-independence.svg')


def arithmetic_per_byte() -> None:
    sizes = [64, 256, 1024, 4096, 16384]
    mm = [(2.0 * n ** 3) / (3.0 * n * n * 2.0) for n in sizes]
    add = [(float(n * n)) / (3.0 * n * n * 2.0) for n in sizes]
    for n, m, a in zip(sizes, mm, add):
        print(f'[gpu] {n} by {n}: matrix multiply does {m:.1f} operations per byte moved, '
              f'adding two grids does {a:.2f}')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(sizes, mm, marker='o', color=LINK, lw=2.0, label='a matrix multiply')
    ax.plot(sizes, add, marker='s', color=WRIST, lw=2.0, label='adding two grids together')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    for n, m in zip(sizes, mm):
        ax.text(n, m * 1.25, f'{m:.0f}', ha='center', fontsize=9, color=LINK)
    ax.set_xlabel('side of the square grid, n', fontsize=10)
    ax.set_ylabel('operations done for each byte fetched (log scale)', fontsize=10)
    ax.set_title('The bigger the multiply, the more work each fetched number pays for',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'arithmetic-per-byte.svg')


def batch_fills_the_chip() -> None:
    d = EX_WIDTH
    batches = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    weights_bytes = d * d * 2.0
    times, arith, memory = [], [], []
    for b in batches:
        flops = 2.0 * b * d * d
        bytes_moved = weights_bytes + 2.0 * b * d * 2.0
        t_a = flops / EX_FLOPS
        t_m = bytes_moved / EX_BAND
        arith.append(t_a * 1e6)
        memory.append(t_m * 1e6)
        times.append(max(t_a, t_m) * 1e6)
    knee = next(b for b, a, m in zip(batches, arith, memory) if a >= m)
    print(f'[gpu] example layer: {d} by {d} weights, {weights_bytes / 1e6:.1f} megabytes '
          f'at two bytes each')
    for b, a, m in zip(batches, arith, memory):
        print(f'[gpu] batch {b:5d}: arithmetic {a:8.1f} microseconds, '
              f'fetching the weights {m:8.1f} microseconds')
    print(f'[gpu] the arithmetic only catches up with the fetching at a batch of {knee}')
    fig, ax = plt.subplots(figsize=(9.8, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(batches, arith, marker='o', color=LINK, lw=2.0, label='time to do the arithmetic')
    ax.plot(batches, memory, marker='s', color=GRIP, lw=2.0,
            label='time to fetch the weights from memory')
    ax.plot(batches, times, color=INK, lw=1.2, ls=':', label='what you actually wait for')
    ax.axvline(knee, color=SLIDE, ls='--', lw=1.4)
    ax.text(knee * 1.15, min(arith) * 1.6, f'batch {knee}: the chip is\nfinally busy',
            fontsize=9.5, color=SLIDE)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(batches)
    ax.set_xticklabels([str(b) for b in batches], fontsize=8.5)
    ax.set_xlabel('rows of input put through the layer at once', fontsize=10)
    ax.set_ylabel('microseconds (log scale)', fontsize=10)
    ax.set_title('With one row at a time the chip spends its life waiting for memory',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'batch-fills-the-chip.svg')


# --------------------------------------------------------------------------
# page 2, section 2: what one parameter costs
# --------------------------------------------------------------------------

def bytes_per_parameter() -> None:
    par = transformer_params()
    n = par['total']
    names = ['float32', 'bfloat16', 'int8', 'int4']
    gb = [n * BYTES[k] / 1e9 for k in names]
    print(f'[mem] the example model: {EX_LAYERS} blocks, width {EX_WIDTH}, vocabulary '
          f'{_si(EX_VOCAB)}')
    print(f'[mem] attention {par["attention"] / 1e9:.2f} billion, feed-forward '
          f'{par["feed-forward"] / 1e9:.2f} billion, embedding table '
          f'{par["embedding table"] / 1e9:.2f} billion')
    print(f'[mem] total {n / 1e9:.2f} billion parameters')
    for k, v in zip(names, gb):
        print(f'[mem] at {k:9s} ({BYTES[k]} bytes each): {v:.1f} gigabytes just to hold them')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    cols = [GRIP, LINK, SLIDE, PURPLE]
    ax.bar(range(len(names)), gb, color=cols, width=0.55)
    for i, (k, v) in enumerate(zip(names, gb)):
        ax.text(i, v + max(gb) * 0.02, f'{v:.1f} GB', ha='center', fontsize=11,
                weight='bold')
        ax.text(i, max(gb) * 0.04, f'{BYTES[k]} bytes\nper parameter', ha='center',
                fontsize=9, color='white')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, max(gb) * 1.15)
    ax.set_ylabel('memory to hold the parameters (gigabytes)', fontsize=10)
    ax.set_title(f'The same {n / 1e9:.2f} billion parameters, stored four ways',
                 fontsize=12, weight='bold')
    _save(fig, SDC_DOC, 'bytes-per-parameter.svg')


def rounding_at_each_precision() -> None:
    values = np.array([9.5, 3.14159265, 1.0, 0.3, 0.1])
    rows: dict[str, list[float]] = {}
    f32 = values.astype(np.float32).astype(np.float64)
    f16 = values.astype(np.float16).astype(np.float64)
    bf = (values.astype(np.float32).view(np.uint32) >> 16 << 16).astype(np.uint32)
    bf16 = bf.view(np.float32).astype(np.float64)
    scale = float(np.max(np.abs(values))) / 127.0
    i8 = np.round(values / scale) * scale
    for name, got in [('float32', f32), ('bfloat16', bf16), ('float16', f16),
                      ('int8 with one shared scale', i8)]:
        err = np.abs(got - values) / np.abs(values)
        rows[name] = list(err)
        print(f'[mem] {name:28s} ' + '  '.join(f'{v:.2e}' for v in err))
    print(f'[mem] stored value of 0.1: float32 {f32[4]:.10f}, bfloat16 {bf16[4]:.10f}, '
          f'float16 {f16[4]:.10f}, int8 {i8[4]:.10f}')
    print(f'[mem] the one shared int8 scale is {scale:.6f}, which is the largest number '
          f'in the set divided by 127')
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    labels = ['9.5', '3.14159265', '1.0', '0.3', '0.1']
    width = 0.2
    cols = [GRIP, LINK, SLIDE, PURPLE]
    for off, (name, errs), col in zip([-1.5 * width, -0.5 * width, 0.5 * width,
                                       1.5 * width], rows.items(), cols):
        ax.bar(np.arange(len(values)) + off, [max(e, 3e-9) for e in errs], width=width,
               color=col, label=name)
    ax.set_yscale('log')
    ax.set_ylim(1e-9, 1e-1)
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel('how far the stored number is out, as a share of it (log scale)',
                  fontsize=10)
    ax.set_title('Fewer bits, bigger rounding: the same five numbers stored four ways',
                 fontsize=12, weight='bold')
    ax.text(0.0, 6e-9, 'a bar this short means the number is kept exactly', fontsize=8.5,
            color=MUTED)
    ax.legend(fontsize=9, frameon=False, loc='lower left', ncol=2)
    _save(fig, SDC_DOC, 'rounding-at-each-precision.svg')


def where_the_parameters_are() -> None:
    configs = [('small: 12 blocks, width 768', 12, 768),
               ('medium: 24 blocks, width 2048', 24, 2048),
               ('the example model: 32 blocks, width 4096', EX_LAYERS, EX_WIDTH)]
    parts = ['attention', 'feed-forward', 'embedding table']
    cols = {'attention': LINK, 'feed-forward': SLIDE, 'embedding table': WRIST}
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    bottoms = np.zeros(len(configs))
    for part in parts:
        vals = np.array([transformer_params(l, w)[part] / 1e9 for _, l, w in configs])
        ax.bar(range(len(configs)), vals, bottom=bottoms, color=cols[part], width=0.5,
               label=part)
        bottoms += vals
    for i, (name, l, w) in enumerate(configs):
        par = transformer_params(l, w)
        print(f'[mem] {name}: attention {par["attention"] / 1e9:.3f} billion, '
              f'feed-forward {par["feed-forward"] / 1e9:.3f}, embedding '
              f'{par["embedding table"] / 1e9:.3f}, total {par["total"] / 1e9:.3f}')
        ax.text(i, bottoms[i] + 0.15, f'{par["total"] / 1e9:.2f} billion', ha='center',
                fontsize=10.5, weight='bold')
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels([c[0].replace(': ', ':\n') for c in configs], fontsize=9.5)
    ax.set_ylim(0, bottoms.max() * 1.15)
    ax.set_ylabel('parameters (billions)', fontsize=10)
    ax.set_title('Where the parameters sit: the feed-forward part is twice the attention',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'where-the-parameters-are.svg')


def model_size_versus_card() -> None:
    counts = np.array([1e9, 3e9, 7e9, 13e9, 34e9, 70e9, 180e9])
    cards = [16, 24, 80]
    fig, ax = plt.subplots(figsize=(10.2, 5.2), facecolor='white')
    _plain(ax)
    for name, col in [('float32', GRIP), ('bfloat16', LINK), ('int8', SLIDE),
                      ('int4', PURPLE)]:
        gb = counts * BYTES[name] / 1e9
        ax.plot(counts / 1e9, gb, marker='o', color=col, lw=2.0, label=name)
        print(f'[mem] {name:9s}: ' + ', '.join(f'{c / 1e9:.0f}B->{g:.0f}GB'
                                               for c, g in zip(counts, gb)))
    for c in cards:
        ax.axhline(c, color=MUTED, ls=':', lw=1.2)
        ax.text(1.0, c * 1.06, f'an example card with {c} GB', fontsize=8.5, color=MUTED)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks([1, 3, 7, 13, 34, 70, 180])
    ax.set_xticklabels(['1', '3', '7', '13', '34', '70', '180'])
    ax.set_xlabel('parameters (billions, log scale)', fontsize=10)
    ax.set_ylabel('memory to hold them (gigabytes, log scale)', fontsize=10)
    ax.set_title('What fits on one card, before anything else is counted',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'model-size-versus-card.svg')


# --------------------------------------------------------------------------
# page 2, section 3: what training needs on top of the parameters
# --------------------------------------------------------------------------

ACT_PER_BLOCK: int = 16     # tensors the size of one block's input kept for the backward pass


def training_budget(batch: int = 4, seq: int = EX_SEQ, checkpointing: bool = False
                    ) -> dict[str, float]:
    n = transformer_params()['total']
    per_block = EX_LAYERS * batch * seq * EX_WIDTH * 2.0
    acts = per_block * (1 if checkpointing else ACT_PER_BLOCK)
    return {'parameters (bfloat16)': n * 2.0,
            'gradients (bfloat16)': n * 2.0,
            'master copy (float32)': n * 4.0,
            'two optimiser averages (float32)': n * 8.0,
            'activations kept for the backward pass': acts}


def training_memory_budget() -> None:
    budget = training_budget()
    total = sum(budget.values())
    n = transformer_params()['total']
    run_only = n * 2.0 + 2.0 * EX_LAYERS * EX_SEQ * EX_WIDTH * 2.0
    for k, v in budget.items():
        print(f'[train] {k:42s} {v / 1e9:7.1f} GB')
    print(f'[train] {"total to train":42s} {total / 1e9:7.1f} GB')
    print(f'[train] {"to run it on one sequence":42s} {run_only / 1e9:7.1f} GB')
    print(f'[train] training needs {total / run_only:.1f} times as much memory as running')
    print(f'[train] that is {total / EX_MEM:.1f} cards of {EX_MEM / 1e9:.0f} GB')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 5.2), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.35, 1.0]})
    _plain(ax1)
    bottom = 0.0
    cols = [LINK, WRIST, PURPLE, TEAL, SLIDE]
    for (k, v), col in zip(budget.items(), cols):
        ax1.bar([0], [v / 1e9], bottom=[bottom / 1e9], color=col, width=0.5)
        ax1.text(0.0, (bottom + v / 2) / 1e9, f'{v / 1e9:.0f} GB', fontsize=9.5,
                 va='center', ha='center', color='white', weight='bold')
        bottom += v
    ax1.bar([1], [run_only / 1e9], color=MUTED, width=0.5)
    ax1.text(1, run_only / 1e9 + total / 1e9 * 0.02, f'{run_only / 1e9:.0f} GB',
             ha='center', fontsize=10.5, weight='bold')
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['training it', 'just running it'], fontsize=10)
    ax1.set_xlim(-0.5, 1.6)
    ax1.set_ylim(0, total / 1e9 * 1.1)
    ax1.set_ylabel('gigabytes', fontsize=10)
    ax1.set_title(f'{total / 1e9:.0f} GB against {run_only / 1e9:.0f} GB: '
                  f'{total / run_only:.0f} times as much', fontsize=11.5, weight='bold')
    _plain(ax2)
    share = [v / total * 100 for v in budget.values()]
    ax2.barh(range(len(share))[::-1], share, color=cols, height=0.6)
    for i, v in enumerate(share):
        ax2.text(v + 1, len(share) - 1 - i, f'{v:.0f}%', va='center', fontsize=9.5)
    ax2.set_yticks(range(len(share))[::-1])
    ax2.set_yticklabels(['parameters', 'gradients', 'master copy',
                         'optimiser averages', 'activations'], fontsize=9)
    ax2.set_xlim(0, max(share) * 1.25)
    ax2.set_xlabel('share of the training memory (per cent)', fontsize=10)
    ax2.set_title('the parameters are the small part', fontsize=11.5, weight='bold')
    fig.suptitle(f'Training the example model: batch of 4 sequences of {_si(EX_SEQ)} '
                 f'words', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.5)
    _save(fig, SDC_DOC, 'training-memory-budget.svg')


def activations_grow_with_batch() -> None:
    batches = [1, 2, 4, 8, 16, 32]
    fixed = sum(v for k, v in training_budget().items() if 'activations' not in k)
    acts = [EX_LAYERS * b * EX_SEQ * EX_WIDTH * 2.0 * ACT_PER_BLOCK for b in batches]
    acts_cp = [EX_LAYERS * b * EX_SEQ * EX_WIDTH * 2.0 for b in batches]
    for b, a, c in zip(batches, acts, acts_cp):
        print(f'[train] batch {b:3d}: activations {a / 1e9:7.1f} GB, with recomputing '
              f'{c / 1e9:6.1f} GB, plus {fixed / 1e9:.0f} GB that never changes')
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(batches, [(fixed + a) / 1e9 for a in acts], marker='o', color=GRIP, lw=2.0,
            label='keeping every activation')
    ax.plot(batches, [(fixed + a) / 1e9 for a in acts_cp], marker='s', color=SLIDE, lw=2.0,
            label='keeping one per block and recomputing the rest')
    ax.axhline(fixed / 1e9, color=MUTED, ls='--', lw=1.3)
    ax.text(batches[-1], fixed / 1e9 * 0.93,
            f'parameters, gradients and optimiser state: {fixed / 1e9:.0f} GB',
            fontsize=9, color=MUTED, ha='right', va='top')
    ax.set_xscale('log')
    ax.set_xticks(batches)
    ax.set_xticklabels([str(b) for b in batches])
    ax.set_xlabel(f'sequences of {_si(EX_SEQ)} words put through at once', fontsize=10)
    ax.set_ylabel('memory for the whole training step (gigabytes)', fontsize=10)
    ax.set_title('The fixed cost is flat; what grows with the batch is the activations',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'activations-grow-with-batch.svg')


def recompute_tradeoff() -> None:
    keep = sum(training_budget(checkpointing=False).values())
    cheap = sum(training_budget(checkpointing=True).values())
    n = transformer_params()['total']
    d_tokens = 4 * EX_SEQ
    flops_normal = 6.0 * n * d_tokens
    flops_recompute = 8.0 * n * d_tokens
    print(f'[train] memory with every activation kept {keep / 1e9:.0f} GB, '
          f'with recomputing {cheap / 1e9:.0f} GB, a saving of '
          f'{100 * (1 - cheap / keep):.0f} per cent')
    print(f'[train] arithmetic per step rises from 6 x N x D to 8 x N x D, which is '
          f'{100 * (flops_recompute / flops_normal - 1):.0f} per cent more')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.8), facecolor='white')
    _plain(ax1)
    ax1.bar([0, 1], [keep / 1e9, cheap / 1e9], color=[GRIP, SLIDE], width=0.5)
    for i, v in enumerate([keep / 1e9, cheap / 1e9]):
        ax1.text(i, v + keep / 1e9 * 0.02, f'{v:.0f} GB', ha='center', fontsize=11,
                 weight='bold')
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['keep every activation', 'recompute them'], fontsize=9.5)
    ax1.set_ylim(0, keep / 1e9 * 1.15)
    ax1.set_ylabel('memory for one training step (gigabytes)', fontsize=10)
    ax1.set_title(f'memory falls by {100 * (1 - cheap / keep):.0f} per cent',
                  fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.bar([0, 1], [flops_normal / 1e12, flops_recompute / 1e12], color=[GRIP, SLIDE],
            width=0.5)
    for i, v in enumerate([flops_normal / 1e12, flops_recompute / 1e12]):
        ax2.text(i, v + flops_recompute / 1e12 * 0.02, f'{v:.0f}', ha='center',
                 fontsize=11, weight='bold')
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['6 x N x D', '8 x N x D'], fontsize=10)
    ax2.set_ylim(0, flops_recompute / 1e12 * 1.15)
    ax2.set_ylabel('million million operations for one step', fontsize=10)
    ax2.set_title(f'and the arithmetic rises by '
                  f'{100 * (flops_recompute / flops_normal - 1):.0f} per cent',
                  fontsize=11.5, weight='bold')
    fig.suptitle('Trading arithmetic for memory: throw the activations away and work '
                 'them out again', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.35)
    _save(fig, SDC_DOC, 'recompute-tradeoff.svg')


def how_many_cards() -> None:
    counts = np.array([1e9, 3e9, 7e9, 13e9, 34e9, 70e9, 180e9])
    run = counts * 2.0
    train = counts * 16.0
    cards_run = np.ceil(run / EX_MEM)
    cards_train = np.ceil(train / EX_MEM)
    for c, r, t in zip(counts, cards_run, cards_train):
        print(f'[train] {c / 1e9:5.0f} billion parameters: {r:3.0f} card(s) to run, '
              f'{t:3.0f} to train, on {EX_MEM / 1e9:.0f} GB cards')
    fig, ax = plt.subplots(figsize=(10.0, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(counts))
    ax.bar(x - 0.2, cards_run, width=0.4, color=LINK, label='to run it (two bytes each)')
    ax.bar(x + 0.2, cards_train, width=0.4, color=GRIP,
           label='to train it (sixteen bytes each, before activations)')
    for i, (r, t) in enumerate(zip(cards_run, cards_train)):
        ax.text(i - 0.2, r * 1.1, f'{r:.0f}', ha='center', fontsize=9.5)
        ax.text(i + 0.2, t * 1.1, f'{t:.0f}', ha='center', fontsize=9.5, weight='bold')
    ax.set_yscale('log')
    ax.set_ylim(0.6, max(cards_train) * 3)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{c / 1e9:.0f}B' for c in counts], fontsize=9.5)
    ax.set_xlabel('parameters', fontsize=10)
    ax.set_ylabel(f'cards of {EX_MEM / 1e9:.0f} GB needed (log scale)', fontsize=10)
    ax.set_title('Sixteen bytes a parameter is why training needs a room full of cards',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, SDC_DOC, 'how-many-cards.svg')


# --------------------------------------------------------------------------
# page 2, section 4: measuring a run in floating-point operations
# --------------------------------------------------------------------------

EX_TOKENS: float = 1.4e12       # the example training run reads this many tokens


def six_n_d() -> None:
    n = transformer_params()['total']
    d = EX_TOKENS
    forward = 2.0 * n * d
    backward = 4.0 * n * d
    total = forward + backward
    print(f'[flop] N = {n / 1e9:.2f} billion parameters, D = {d / 1e12:.1f} million '
          f'million tokens')
    print(f'[flop] forward pass 2 x N x D = {forward:.3e} operations')
    print(f'[flop] backward pass 4 x N x D = {backward:.3e} operations')
    print(f'[flop] whole run 6 x N x D = {total:.3e} operations')
    days = total / (EX_FLOPS * EX_USE)
    print(f'[flop] on one example accelerator at {EX_USE:.0%} of '
          f'{EX_FLOPS / 1e12:.0f} million million operations a second: '
          f'{days / 86400 / 365:.0f} years')
    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    ax.bar([0], [forward / 1e21], color=LINK, width=0.5, label='forward pass, 2 x N x D')
    ax.bar([0], [backward / 1e21], bottom=[forward / 1e21], color=GRIP, width=0.5,
           label='backward pass, 4 x N x D')
    ax.text(0.33, forward / 2e21, f'{forward:.2e}', fontsize=10, va='center')
    ax.text(0.33, (forward + backward / 2) / 1e21, f'{backward:.2e}', fontsize=10,
            va='center')
    ax.text(0, total / 1e21 * 1.03, f'{total:.2e} operations in all', ha='center',
            fontsize=11.5, weight='bold')
    ax.set_xlim(-0.6, 1.4)
    ax.set_xticks([0])
    ax.set_xticklabels([f'the example run:\nN = {n / 1e9:.2f} billion, '
                        f'D = {d / 1e12:.1f} million million'], fontsize=10)
    ax.set_ylim(0, total / 1e21 * 1.18)
    ax.set_ylabel('thousand million million million operations', fontsize=10)
    ax.set_title('The rule of thumb: one token through one parameter costs about '
                 'six operations', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, SDC_DOC, 'six-n-d.svg')


def flops_and_days() -> None:
    configs = [('1 billion, 20 billion tokens', 1e9, 2e10),
               ('7 billion, 1.4 million million', 7e9, 1.4e12),
               ('70 billion, 10 million million', 7e10, 1e13)]
    counts = [8, 64, 512]
    print(f'[flop] sustained rate per accelerator: {EX_FLOPS * EX_USE / 1e12:.0f} million '
          f'million operations a second')
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    width = 0.2
    cols = [LINK, SLIDE, WRIST, PURPLE]
    for off, k, col in zip([-width, 0.0, width], counts, cols):
        days = []
        for name, n, d in configs:
            total = 6.0 * n * d
            days.append(total / (EX_FLOPS * EX_USE * k) / 86400)
        ax.bar(np.arange(len(configs)) + off, days, width=width, color=col,
               label=f'{k} accelerators')
        for i, v in enumerate(days):
            ax.text(i + off, v * 1.2, f'{v:.2g}', ha='center', fontsize=8.5,
                    rotation=90)
    for name, n, d in configs:
        print(f'[flop] {name}: 6 x N x D = {6.0 * n * d:.2e} operations; '
              + ', '.join(f'{k} cards: {6.0 * n * d / (EX_FLOPS * EX_USE * k) / 86400:.2f} '
                          f'days' for k in counts))
    ax.set_yscale('log')
    ax.set_ylim(0.01, 3e5)
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels([c[0].replace(', ', ',\n') for c in configs], fontsize=9.5)
    ax.set_ylabel('days of training (log scale)', fontsize=10)
    ax.set_title('Three example runs, and how long each takes on a given pile of cards',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left', ncol=2)
    _save(fig, SDC_DOC, 'flops-and-days.svg')


def iso_compute_grid() -> None:
    ns = np.logspace(8, 11.5, 60)
    ds = np.logspace(10, 13.5, 60)
    nn, dd = np.meshgrid(ns, ds, indexing='ij')
    cost = 6.0 * nn * dd
    fig, ax = plt.subplots(figsize=(9.8, 5.4), facecolor='white')
    _plain(ax)
    im = ax.pcolormesh(ns / 1e9, ds / 1e12, np.log10(cost).T, cmap='YlGnBu', shading='auto')
    levels = [1e20, 1e21, 1e22, 1e23, 1e24]
    cs = ax.contour(ns / 1e9, ds / 1e12, cost.T, levels=levels, colors=INK,
                    linewidths=1.2)
    ax.clabel(cs, fmt={lv: f'{lv:.0e}' for lv in levels}, fontsize=8.5)
    ax.plot([7.0], [1.4], marker='*', color=GRIP, markersize=18)
    ax.text(7.0, 0.45, 'the example run', fontsize=9.5, color=GRIP, weight='bold',
            ha='center', bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2.0})
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('parameters (billions, log scale)', fontsize=10)
    ax.set_ylabel('training tokens (million millions, log scale)', fontsize=10)
    ax.set_title('Every line is one budget of arithmetic: 6 x N x D held fixed',
                 fontsize=12, weight='bold')
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02,
                 label='log of the operations in the run')
    print('[flop] iso-compute lines drawn at ' + ', '.join(f'{lv:.0e}' for lv in levels))
    print('[flop] the example run sits at N = 7 billion, D = 1.4 million million, '
          f'6ND = {6 * 7e9 * 1.4e12:.2e}')
    _save(fig, SDC_DOC, 'iso-compute-grid.svg')


def training_versus_serving() -> None:
    n = transformer_params()['total']
    d = EX_TOKENS
    train = 6.0 * n * d
    per_token = 2.0 * n
    tokens_equal = train / per_token
    print(f'[flop] answering costs about 2 x N = {per_token:.2e} operations a token')
    print(f'[flop] the training run costs the same as answering '
          f'{tokens_equal:.3e} tokens, which is three times the {d:.1e} tokens it '
          f'was trained on')
    served = np.logspace(9, 14, 60)
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(served, served * per_token, color=LINK, lw=2.2,
            label='operations spent answering, added up')
    ax.axhline(train, color=GRIP, lw=2.0, ls='--',
               label=f'the whole training run: {train:.2e} operations')
    ax.plot([tokens_equal], [train], marker='o', color=INK, markersize=9, zorder=5)
    ax.annotate(f'{tokens_equal:.2e} tokens answered\ncosts as much as training it once',
                xy=(tokens_equal, train), xytext=(1.2e9, train * 2.2), fontsize=9.5,
                arrowprops={'arrowstyle': '->', 'color': INK})
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens the finished model has answered with (log scale)', fontsize=10)
    ax.set_ylabel('operations (log scale)', fontsize=10)
    ax.set_ylim(1e19, train * 20)
    ax.set_title('Training is paid once; answering is paid every time, and it catches up',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, SDC_DOC, 'training-versus-serving.svg')


# --------------------------------------------------------------------------
# page 2, section 5: scaling laws
#
# The formula below is written for this page. It has the shape that measured
# ones have, and the numbers in it are chosen so the curves look like the real
# ones, but it is arithmetic and not a measurement.
# --------------------------------------------------------------------------

LAW_FLOOR: float = 1.60
LAW_A: float = 500.0
LAW_B: float = 500.0
LAW_AN: float = 0.35
LAW_BD: float = 0.30


def law(n: Arr | float, d: Arr | float) -> Arr | float:
    return LAW_FLOOR + LAW_A / np.power(n, LAW_AN) + LAW_B / np.power(d, LAW_BD)


def best_split(c: float, grid: int = 4000) -> tuple[float, float, float]:
    """The model size and token count that give the lowest loss for a budget of arithmetic."""
    ns = np.logspace(6, 13, grid)
    ds = c / (6.0 * ns)
    losses = law(ns, ds)
    i = int(np.argmin(losses))
    return float(ns[i]), float(ds[i]), float(losses[i])


def power_law_curve() -> None:
    budgets = np.logspace(17, 26, 40)
    best = [best_split(c) for c in budgets]
    losses = np.array([b[2] for b in best])
    for c, (n, d, l) in list(zip(budgets, best))[::8]:
        print(f'[law] budget {c:.1e} operations: best size {n / 1e9:.3f} billion, '
              f'{d / 1e9:.1f} billion tokens, loss {l:.3f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.8), facecolor='white')
    _plain(ax1)
    ax1.plot(budgets, losses, color=LINK, lw=2.4)
    ax1.axhline(LAW_FLOOR, color=MUTED, ls='--', lw=1.3)
    ax1.text(budgets[0], LAW_FLOOR + 0.05, f'the floor this formula has: {LAW_FLOOR}',
             fontsize=9, color=MUTED)
    ax1.set_xscale('log')
    ax1.set_xlabel('operations in the training run (log scale)', fontsize=10)
    ax1.set_ylabel('loss', fontsize=10)
    ax1.set_title('loss against arithmetic', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.plot(budgets, losses - LAW_FLOOR, color=SLIDE, lw=2.4)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel('operations in the training run (log scale)', fontsize=10)
    ax2.set_ylabel('loss above the floor (log scale)', fontsize=10)
    ax2.set_title('the same curve, both axes squashed: a straight line',
                  fontsize=11.5, weight='bold')
    fig.suptitle('An illustrative scaling curve, worked out from one formula written '
                 'for this page', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.3)
    _save(fig, SDC_DOC, 'power-law-curve.svg')


def bigger_model_alone() -> None:
    ns = np.logspace(7.5, 12, 80)
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    for d, col in zip([1e10, 1e11, 1e12, 1e13], [GRIP, WRIST, LINK, SLIDE]):
        losses = law(ns, d)
        ax.plot(ns / 1e9, losses, color=col, lw=2.0,
                label=f'{d / 1e9:.0f} billion tokens')
        floor = LAW_FLOOR + LAW_B / d ** LAW_BD
        ax.axhline(floor, color=col, ls=':', lw=1.0)
        print(f'[law] with {d / 1e9:.0f} billion tokens the loss cannot go below '
              f'{floor:.3f} however big the model is; at 1 billion parameters it is '
              f'{law(1e9, d):.3f} and at 100 billion {law(1e11, d):.3f}')
    ax.set_xscale('log')
    ax.set_xlabel('parameters (billions, log scale)', fontsize=10)
    ax.set_ylabel('loss', fontsize=10)
    ax.set_title('Growing the model with the data held still runs into a floor',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, SDC_DOC, 'bigger-model-alone.svg')


def grow_together() -> None:
    budgets = np.logspace(18, 26, 30)
    best = [best_split(c) for c in budgets]
    ns = np.array([b[0] for b in best])
    ds = np.array([b[1] for b in best])
    slope_n = float(np.polyfit(np.log(budgets), np.log(ns), 1)[0])
    slope_d = float(np.polyfit(np.log(budgets), np.log(ds), 1)[0])
    print(f'[law] when the budget is multiplied by ten, the best model size is multiplied '
          f'by {10 ** slope_n:.2f} and the best token count by {10 ** slope_d:.2f}')
    print(f'[law] tokens per parameter at the small end '
          f'{ds[0] / ns[0]:.0f}, at the large end {ds[-1] / ns[-1]:.0f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.8), facecolor='white')
    _plain(ax1)
    ax1.plot(budgets, ns, color=LINK, lw=2.4, label='best number of parameters')
    ax1.plot(budgets, ds, color=SLIDE, lw=2.4, label='best number of training tokens')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xlabel('operations in the run (log scale)', fontsize=10)
    ax1.set_ylabel('count (log scale)', fontsize=10)
    ax1.set_title('both grow, and at almost the same rate', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper left')
    _plain(ax2)
    ax2.plot(budgets, ds / ns, color=PURPLE, lw=2.4)
    ax2.set_xscale('log')
    ax2.set_xlabel('operations in the run (log scale)', fontsize=10)
    ax2.set_ylabel('training tokens for each parameter', fontsize=10)
    ax2.set_ylim(0, float(np.max(ds / ns)) * 1.2)
    ax2.set_title('so the tokens for each parameter move slowly',
                  fontsize=11.5, weight='bold')
    fig.suptitle('Spend a budget of arithmetic well: make the model and the data grow '
                 'together', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.32)
    _save(fig, SDC_DOC, 'grow-together.svg')


def predict_the_big_run() -> None:
    rng = np.random.default_rng(31)
    small = np.logspace(18, 21, 7)
    truth_small = np.array([best_split(c)[2] for c in small])
    measured = truth_small * (1.0 + 0.01 * rng.normal(size=len(small)))
    coef = np.polyfit(np.log(small), np.log(measured - LAW_FLOOR), 1)
    big = 1e24
    predicted = LAW_FLOOR + float(np.exp(np.polyval(coef, np.log(big))))
    actual = best_split(big)[2]
    print(f'[law] fitted on runs from {small[0]:.0e} to {small[-1]:.0e} operations')
    print(f'[law] predicted loss at {big:.0e}: {predicted:.4f}; the formula gives '
          f'{actual:.4f}; out by {100 * abs(predicted - actual) / actual:.2f} per cent')
    curve = np.logspace(18, 24.3, 60)
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(curve, [best_split(c)[2] for c in curve], color=MUTED, lw=1.6, ls='--',
            label='what the formula says')
    ax.plot(curve, LAW_FLOOR + np.exp(np.polyval(coef, np.log(curve))), color=LINK,
            lw=2.0, label='the straight line fitted to the small runs only')
    ax.scatter(small, measured, color=SLIDE, zorder=5, s=42,
               label='the small runs, with a little noise added')
    ax.scatter([big], [actual], color=GRIP, zorder=5, s=90, marker='*',
               label='the big run nobody has done yet')
    ax.annotate(f'predicted {predicted:.3f}\nformula says {actual:.3f}',
                xy=(big, actual), xytext=(big / 300, actual + 0.35), fontsize=9.5,
                arrowprops={'arrowstyle': '->', 'color': INK})
    ax.set_xscale('log')
    ax.set_xlabel('operations in the run (log scale)', fontsize=10)
    ax.set_ylabel('loss', fontsize=10)
    ax.set_title('Why anyone plans with these curves: the small runs tell you where the '
                 'big one lands', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    _save(fig, SDC_DOC, 'predict-the-big-run.svg')


# --------------------------------------------------------------------------
# page 2, section 6: the data
# --------------------------------------------------------------------------

def quality_beats_volume() -> None:
    bb = _bb()
    sizes = [100, 200, 400, 800, 1600, 3200]
    wrong = [0.0, 0.2, 0.4]
    test_f = bb.features(bb.test.a)
    curves: dict[float, list[float]] = {w: [] for w in wrong}
    for n in sizes:
        for w in wrong:
            acc = []
            for rep in range(2):
                tr = Pics(n, seed=5000 + n + 11 * rep)
                y = tr.cls.copy()
                rng = np.random.default_rng(77 + rep)
                spoil = rng.random(n) < w
                y[spoil] = rng.integers(0, 4, size=int(spoil.sum()))
                acc.append(mlp_acc(test_f, bb.test.cls,
                                   mlp_fit(bb.features(tr.a), y, 4, hidden=16,
                                           steps=3000, lr=0.15, seed=rep)))
            curves[w].append(float(np.mean(acc)))
    for w in wrong:
        print(f'[data] {w:.0%} of the labels wrong: '
              + '  '.join(f'n={n}:{v:.3f}' for n, v in zip(sizes, curves[w])))
    clean_200 = curves[0.0][sizes.index(200)]
    dirty_3200 = curves[0.4][sizes.index(3200)]
    print(f'[data] 200 clean examples give {clean_200:.3f}, and 3,200 examples with '
          f'40 per cent of the labels wrong give {dirty_3200:.3f}')
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    for w, col in zip(wrong, [SLIDE, WRIST, GRIP]):
        ax.plot(sizes, [100 * v for v in curves[w]], marker='o', color=col, lw=2.0,
                label=f'{w:.0%} of the labels wrong')
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('examples in the training set (log scale)', fontsize=10)
    ax.set_ylabel('accuracy on held-out pictures (per cent)', fontsize=10)
    ax.set_ylim(20, 103)
    ax.set_title(f'200 clean examples are worth 3,200 with two labels in five wrong: '
                 f'{100 * clean_200:.1f} against {100 * dirty_3200:.1f} per cent',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, SDC_DOC, 'quality-beats-volume.svg')


def duplicates_waste_the_budget() -> None:
    bb = _bb()
    budget = 1600
    fractions = [0.0, 0.5, 0.75, 0.9, 0.95, 0.98]
    test_f = bb.features(bb.test.a)
    accs, uniques = [], []
    for f in fractions:
        u = max(int(round(budget * (1.0 - f))), 4)
        acc = []
        for rep in range(3):
            tr = Pics(u, seed=6000 + u + 13 * rep)
            reps = int(np.ceil(budget / u))
            x = np.tile(bb.features(tr.a), (reps, 1))[:budget]
            y = np.tile(tr.cls, reps)[:budget]
            acc.append(mlp_acc(test_f, bb.test.cls,
                               mlp_fit(x, y, 4, hidden=16, steps=3000, lr=0.15, seed=rep)))
        accs.append(float(np.mean(acc)))
        uniques.append(u)
        print(f'[data] {f:.0%} of the {budget} examples are copies: {u} different '
              f'examples, accuracy {accs[-1]:.3f}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8), facecolor='white')
    _plain(ax1)
    ax1.bar([f * 100 for f in fractions], uniques, width=4, color=LINK)
    for f, u in zip(fractions, uniques):
        ax1.text(f * 100, u + budget * 0.02, str(u), ha='center', fontsize=9.5)
    ax1.set_xlabel('percentage of the set that is copies', fontsize=10)
    ax1.set_ylabel('different examples in it', fontsize=10)
    ax1.set_ylim(0, budget * 1.15)
    ax1.set_title(f'the set is always {_si(budget)} examples', fontsize=11.5,
                  weight='bold')
    _plain(ax2)
    ax2.plot([f * 100 for f in fractions], [100 * a for a in accs], marker='o',
             color=GRIP, lw=2.2)
    for f, a in zip(fractions, accs):
        ax2.text(f * 100, 100 * a + 1.2, f'{100 * a:.1f}', ha='center', fontsize=9.5)
    ax2.set_xlabel('percentage of the set that is copies', fontsize=10)
    ax2.set_ylabel('accuracy on held-out pictures (per cent)', fontsize=10)
    ax2.set_ylim(20, 108)
    ax2.set_title('and the accuracy falls with every copy', fontsize=11.5, weight='bold')
    fig.suptitle('Copies cost the same to train on and teach nothing, which is why '
                 'duplicates are taken out first', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.3)
    _save(fig, SDC_DOC, 'duplicates-waste-the-budget.svg')


MIXTURE: list[tuple[str, float, float]] = [
    # name, tokens available (in millions of millions), share of the run
    ('general web pages', 9.0, 0.50),
    ('books and articles', 0.6, 0.12),
    ('program code', 1.2, 0.20),
    ('maths and reasoning', 0.1, 0.10),
    ('robot logs and manuals', 0.02, 0.08),
]


def a_data_mixture() -> None:
    total = EX_TOKENS
    names = [m[0] for m in MIXTURE]
    have = np.array([m[1] for m in MIXTURE]) * 1e12
    share = np.array([m[2] for m in MIXTURE])
    drawn = share * total
    times = drawn / have
    for nm, h, s, dr, t in zip(names, have, share, drawn, times):
        print(f'[data] {nm:24s} have {h / 1e12:5.2f} million million, take {s:.0%} of the '
              f'run = {dr / 1e12:5.3f}, so each token is read {t:.2f} times')
    print(f'[data] the shares add to {share.sum():.2f} and the run is '
          f'{total / 1e12:.1f} million million tokens')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.8), facecolor='white')
    _plain(ax1)
    y = np.arange(len(names))[::-1]
    ax1.barh(y + 0.18, have / 1e12, height=0.34, color=MUTED, label='tokens there are')
    ax1.barh(y - 0.18, drawn / 1e12, height=0.34, color=LINK, label='tokens the run reads')
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=9)
    ax1.set_xscale('log')
    ax1.set_xlabel('million million tokens (log scale)', fontsize=10)
    ax1.set_title('what there is, and what is read', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9, frameon=False, loc='lower right')
    _plain(ax2)
    cols = [SLIDE if t <= 1.0 else GRIP for t in times]
    ax2.barh(y, times, height=0.5, color=cols)
    for yy, t in zip(y, times):
        ax2.text(t * 1.1, yy, f'{t:.1f} times', va='center', fontsize=9.5)
    ax2.axvline(1.0, color=INK, lw=1.2, ls='--')
    ax2.set_yticks(y)
    ax2.set_yticklabels(names, fontsize=9)
    ax2.set_xscale('log')
    ax2.set_xlim(0.05, max(times) * 3)
    ax2.set_xlabel('times each token of that source is read (log scale)', fontsize=10)
    ax2.set_title('a small source read many times over', fontsize=11.5, weight='bold')
    fig.suptitle(f'An example mixture for a run of {total / 1e12:.1f} million million '
                 f'tokens', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.6)
    _save(fig, SDC_DOC, 'a-data-mixture.svg')


DEMO_SECONDS: float = 25.0
RESET_SECONDS: float = 12.0


def robot_data_costs_time() -> None:
    per_demo = DEMO_SECONDS + RESET_SECONDS
    per_hour = 3600.0 / per_demo
    targets = [10_000, 100_000, 1_000_000]
    hours = [t / per_hour for t in targets]
    years = [h / (8 * 220) for h in hours]
    print(f'[robot] {DEMO_SECONDS:.0f} seconds a demonstration plus '
          f'{RESET_SECONDS:.0f} seconds to put the scene back is {per_demo:.0f} seconds, '
          f'so one person-hour gives {per_hour:.1f} demonstrations')
    for t, h, y in zip(targets, hours, years):
        print(f'[robot] {_si(t)} demonstrations: {_si(h)} person-hours, '
              f'{y:.1f} person-years of 8-hour days')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8), facecolor='white')
    _plain(ax1)
    ax1.bar([0], [per_hour], color=SLIDE, width=0.4)
    ax1.text(0, per_hour * 1.03, f'{per_hour:.0f} demonstrations', ha='center',
             fontsize=11.5, weight='bold')
    ax1.set_xlim(-0.6, 0.6)
    ax1.set_xticks([0])
    ax1.set_xticklabels([f'{DEMO_SECONDS:.0f} s of moving\n+ {RESET_SECONDS:.0f} s of '
                         f'resetting'], fontsize=10)
    ax1.set_ylim(0, per_hour * 1.2)
    ax1.set_ylabel('demonstrations in one person-hour', fontsize=10)
    ax1.set_title('one person, one hour, one arm', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.bar(range(len(targets)), hours, color=[LINK, WRIST, GRIP], width=0.5)
    for i, (h, y) in enumerate(zip(hours, years)):
        ax2.text(i, h * 1.3, f'{_si(h)} hours\n{y:.1f} person-years', ha='center',
                 fontsize=9.5, weight='bold')
    ax2.set_yscale('log')
    ax2.set_ylim(50, max(hours) * 12)
    ax2.set_xticks(range(len(targets)))
    ax2.set_xticklabels([f'{_si(t)}\ndemonstrations' for t in targets], fontsize=9.5)
    ax2.set_ylabel('person-hours (log scale)', fontsize=10)
    ax2.set_title('what a dataset of that size costs in people', fontsize=11.5,
                  weight='bold')
    fig.suptitle('Robot data is scarce because every example is somebody sitting at an arm',
                 fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.35)
    _save(fig, SDC_DOC, 'robot-data-costs-time.svg')


# example costings written for this page: person-hours of work, and examples got for it
WAYS: list[tuple[str, float, float]] = [
    ('teleoperating a real arm', 1.0, 3600.0 / (DEMO_SECONDS + RESET_SECONDS)),
    ('taking in somebody else\'s robot data', 40.0, 50_000.0),
    ('simulation with randomised scenes', 60.0, 300_000.0),
    ('examples generated by a model', 20.0, 10_000.0),
    ('learning from video of people', 10.0, 20_000.0),
]


def four_ways_to_get_more_data() -> None:
    names = [w[0] for w in WAYS]
    rate = [w[2] / w[1] for w in WAYS]
    need = [100_000.0 / r for r in rate]
    for nm, (_, h, got), r, n in zip(names, WAYS, rate, need):
        print(f'[robot] {nm:38s} {h:5.0f} person-hours gives {_si(got):>9s} examples '
              f'= {r:9.1f} an hour; {_si(n):>7s} hours for 100,000')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white')
    cols = [GRIP, LINK, SLIDE, PURPLE, WRIST]
    _plain(ax1)
    y = np.arange(len(names))[::-1]
    ax1.barh(y, rate, color=cols, height=0.55)
    for yy, r in zip(y, rate):
        ax1.text(r * 1.15, yy, f'{r:,.0f}', va='center', fontsize=9.5)
    ax1.set_xscale('log')
    ax1.set_xlim(50, max(rate) * 6)
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=9)
    ax1.set_xlabel('examples for each person-hour (log scale)', fontsize=10)
    ax1.set_title('what an hour of a person buys', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.barh(y, need, color=cols, height=0.55)
    for yy, n in zip(y, need):
        ax2.text(n * 1.15, yy, f'{n:,.0f} h', va='center', fontsize=9.5)
    ax2.set_xscale('log')
    ax2.set_xlim(5, max(need) * 8)
    ax2.set_yticks(y)
    ax2.set_yticklabels([])
    ax2.set_xlabel('person-hours for 100,000 examples (log scale)', fontsize=10)
    ax2.set_title('and what 100,000 examples cost', fontsize=11.5, weight='bold')
    fig.suptitle('Example costings for five ways of getting robot data, written for this '
                 'page', fontsize=12.5, weight='bold', y=1.0)
    fig.subplots_adjust(wspace=0.12)
    _save(fig, SDC_DOC, 'four-ways-to-get-more-data.svg')


# --------------------------------------------------------------------------

PAGE_ONE = [labels_versus_free_signal, make_the_label_from_the_data,
            one_picture_many_targets, four_recipes,
            next_token_pairs, context_helps, one_position_probabilities,
            next_token_training_curve,
            masked_patches, fill_the_gaps, mask_rate_curve, masked_word_fill,
            similarity_grid, softmax_of_one_row, contrastive_training,
            batch_size_and_temperature,
            two_crops, teacher_and_student, agreement_rises, same_item_closer,
            backbone_and_head, what_the_features_track, few_labels_beat_many,
            labels_needed]

PAGE_TWO = [one_matrix_multiply, work_and_independence, arithmetic_per_byte,
            batch_fills_the_chip,
            bytes_per_parameter, rounding_at_each_precision, where_the_parameters_are,
            model_size_versus_card,
            training_memory_budget, activations_grow_with_batch, recompute_tradeoff,
            how_many_cards,
            six_n_d, flops_and_days, iso_compute_grid, training_versus_serving,
            power_law_curve, bigger_model_alone, grow_together, predict_the_big_run,
            quality_beats_volume, duplicates_waste_the_budget, a_data_mixture,
            robot_data_costs_time, four_ways_to_get_more_data]


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    for fn in PAGE_ONE + PAGE_TWO:
        fn()
    print(f'wrote {len(PAGE_ONE) + len(PAGE_TWO)} diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
