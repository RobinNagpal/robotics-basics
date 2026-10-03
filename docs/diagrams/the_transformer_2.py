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
        rng = np.random.default_rng(45)
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


# ==========================================================================
# 03_training-and-running-a-transformer.md
# section 1: next-token prediction as the training job
# ==========================================================================

def signals_per_sentence() -> None:
    s = sim()
    n = len(s.targets)
    print(f'[signals] the sentence has {n} tokens and gives {n} training signals')

    fig, ax = plt.subplots(figsize=(11.5, 5.0), facecolor='white')
    _bare(ax)
    w, h = 1.35, 0.62
    for i in range(n):
        x = 0.4 + i * 1.6
        _box(ax, x, 2.35, w, h, s.inputs[i], face='#eef3f9', edge=LINK, fontsize=11)
        _box(ax, x, 0.55, w, h, s.targets[i], face='#eaf4ec', edge=SLIDE, fontsize=11,
             weight='bold')
        _arrow(ax, x + w / 2, 2.30, x + w / 2, 1.25, colour=MUTED, lw=1.1, head=0.12)
        ax.text(x + w / 2, 1.78, f'signal {i + 1}', ha='center', va='center', fontsize=8.5,
                color=MUTED)
        ax.text(x + w / 2, 3.18, f'position {i + 1}', ha='center', va='center', fontsize=9,
                color=INK)
    ax.text(0.1, 2.66, 'what goes in', ha='right', va='center', fontsize=10.5, color=LINK,
            weight='bold')
    ax.text(0.1, 0.86, 'what must come out', ha='right', va='center', fontsize=10.5,
            color=SLIDE, weight='bold')
    ax.text(5.1, 0.02, f'one sentence of {n} tokens gives {n} scored predictions in one pass, '
                       'and no human wrote any of them',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.set_xlim(-2.6, 10.2)
    ax.set_ylim(-0.3, 3.6)
    ax.set_title('Next-token prediction: every position is asked for the token that follows it',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'signals-per-sentence.svg')


def per_position_loss() -> None:
    s = sim()
    for i in range(len(s.targets)):
        print(f'[loss] position {i + 1}: in "{s.inputs[i]}" -> target "{s.targets[i]}", '
              f'p(target) = {s.p_target[i]:.3f}, loss = {s.loss[i]:.2f}, '
              f'best guess "{s.guess[i]}"')
    print(f'[loss] mean loss over the sentence = {s.mean_loss:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1.0]})
    ax = axes[0]
    _bare(ax)
    cols = [0.0, 1.1, 3.1, 5.1, 7.0]
    heads = ['position', 'goes in', 'must come out', 'chance it gave', 'loss there']
    for x, head in zip(cols, heads):
        ax.text(x, 6.35, head, fontsize=10.5, weight='bold', color=INK)
    ax.plot([-0.2, 8.4], [6.15, 6.15], color=INK, lw=1.0)
    for i in range(len(s.targets)):
        y = 5.3 - i * 0.85
        ax.text(cols[0] + 0.25, y, str(i + 1), fontsize=10.5, color=INK)
        ax.text(cols[1], y, s.inputs[i], fontsize=10.5, color=LINK)
        ax.text(cols[2], y, s.targets[i], fontsize=10.5, color=SLIDE, weight='bold')
        ax.text(cols[3] + 0.3, y, f'{s.p_target[i]:.3f}', fontsize=10.5, color=INK)
        ax.text(cols[4] + 0.2, y, f'{s.loss[i]:.2f}', fontsize=10.5, color=GRIP)
    ax.plot([-0.2, 8.4], [0.05, 0.05], color=INK, lw=1.0)
    ax.text(cols[3] - 0.9, -0.55, f'average of the six losses = {s.mean_loss:.2f}',
            fontsize=10.5, weight='bold', color=INK)
    ax.set_xlim(-0.6, 8.6)
    ax.set_ylim(-1.1, 6.9)
    ax.set_title('Six predictions, six losses, one average', fontsize=12, weight='bold',
                 color=INK)

    ax = axes[1]
    _plain(ax)
    ypos = np.arange(len(s.targets))[::-1]
    ax.barh(ypos, s.loss, color=[GRIP if v > s.mean_loss else SLIDE for v in s.loss],
            height=0.62)
    for y, v, t in zip(ypos, s.loss, s.targets):
        ax.text(v + 0.06, y, f'{v:.2f}  ("{t}")', va='center', fontsize=9.5, color=INK)
    ax.axvline(s.mean_loss, color=INK, ls='--', lw=1.2)
    ax.text(s.mean_loss + 0.07, len(s.targets) - 0.75, f'average {s.mean_loss:.2f}',
            fontsize=9.5, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f'position {i + 1}' for i in range(len(s.targets))], fontsize=9.5)
    ax.set_xlim(0, max(s.loss) * 1.55)
    ax.set_xlabel('loss at that position (cross-entropy, in nats)', fontsize=10)
    ax.set_title('A confident right answer costs almost nothing', fontsize=12,
                 weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'per-position-loss.svg')


def one_position_distribution() -> None:
    s = sim()
    picks = [3, 5]
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white', sharey=True)
    for ax, i in zip(axes, picks):
        _plain(ax)
        p = s.probs[i]
        tgt = int(s.target_idx[i])
        colours = [SLIDE if k == tgt else LINK_PALE for k in range(len(WORDS))]
        ax.bar(np.arange(len(WORDS)), p, color=colours, edgecolor=LINK, lw=0.6)
        ax.set_xticks(np.arange(len(WORDS)))
        ax.set_xticklabels(WORDS, rotation=45, ha='right', fontsize=9.5)
        ax.set_ylim(0, 1.16)
        ax.text(tgt, p[tgt] + 0.04, f'{p[tgt]:.3f}', ha='center', fontsize=10, color=SLIDE,
                weight='bold')
        ax.set_title(f'Position {i + 1}: "{s.inputs[i]}" goes in, "{s.targets[i]}" must come out\n'
                     f'loss = -log({s.p_target[i]:.3f}) = {s.loss[i]:.2f}',
                     fontsize=11.5, weight='bold', color=INK)
        print(f'[dist] position {i + 1}: ' +
              ', '.join(f'{w} {v:.3f}' for w, v in zip(WORDS, p)))
    axes[0].set_ylabel('chance the model gave that word', fontsize=10)
    fig.suptitle('The same arithmetic at every position: pick out the chance given to the '
                 'right word, take minus its logarithm', fontsize=12.5, weight='bold',
                 color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'one-position-distribution.svg')


def signals_per_thousand_tokens() -> None:
    sentence_len = 20
    corpus = np.array([1_000, 10_000, 100_000, 1_000_000, 10_000_000], dtype=float)
    by_sentence = corpus / sentence_len
    by_token = corpus
    print(f'[scale] with sentences of {sentence_len} tokens: 1,000 tokens give '
          f'{by_sentence[0]:.0f} sentence labels and {by_token[0]:.0f} next-token signals, '
          f'which is {by_token[0] / by_sentence[0]:.0f} times as many')
    for c, a, b in zip(corpus, by_sentence, by_token):
        print(f'[scale] {c:,.0f} tokens -> {a:,.0f} sentence labels, {b:,.0f} next-token signals')

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['one label a person writes\nfor each sentence', 'one signal for each token,\ntaken from the text itself'],
                  [by_sentence[0], by_token[0]], color=[WRIST, SLIDE], width=0.55)
    for b, v in zip(bars, [by_sentence[0], by_token[0]]):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.06, f'{v:,.0f}', ha='center',
                fontsize=11, weight='bold', color=INK)
    ax.set_yscale('log')
    ax.set_ylim(10, 3000)
    ax.set_ylabel('training signals from 1,000 tokens (log scale)', fontsize=10)
    ax.set_title(f'{by_token[0] / by_sentence[0]:.0f} times more signals from the same text',
                 fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.plot(corpus, by_token, marker='o', color=SLIDE, lw=2, label='one signal per token')
    ax.plot(corpus, by_sentence, marker='s', color=WRIST, lw=2,
            label=f'one label per {sentence_len}-token sentence')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens of text available', fontsize=10)
    ax.set_ylabel('training signals (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('The gap stays the same factor however much text there is',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'signals-per-thousand-tokens.svg')


# ==========================================================================
# section 2: the causal mask
# ==========================================================================

class Att:
    """One head's scores over the six input positions, with and without the mask."""

    def __init__(self) -> None:
        rng = np.random.default_rng(11)
        self.n = len(SENTENCE)
        self.q: Arr = rng.normal(0.0, 1.0, size=(self.n, HEAD_DIM // 8))
        self.k: Arr = rng.normal(0.0, 1.0, size=(self.n, HEAD_DIM // 8))
        self.scores: Arr = self.q @ self.k.T / np.sqrt(self.q.shape[1])
        self.allowed: NDArray[np.bool_] = np.tril(np.ones((self.n, self.n), dtype=bool))
        masked = np.where(self.allowed, self.scores, -np.inf)
        self.weights: Arr = _softmax(masked)
        self.weights_open: Arr = _softmax(self.scores)
        self.shown: Arr = np.where(self.allowed, self.weights, np.nan)
        self.n_allowed: int = int(self.allowed.sum())


_ATT: Att | None = None


def att() -> Att:
    global _ATT
    if _ATT is None:
        _ATT = Att()
    return _ATT


def causal_mask_grid() -> None:
    a = att()
    s = sim()
    print(f'[mask] {a.n} positions: {a.n_allowed} pairs allowed of {a.n * a.n}, '
          f'which is {a.n_allowed / (a.n * a.n) * 100:.1f} per cent')

    fig, ax = plt.subplots(figsize=(10.4, 6.6), facecolor='white')
    _bare(ax)
    cell = 1.0
    for i in range(a.n):
        for j in range(a.n):
            x, y = j * cell, (a.n - 1 - i) * cell
            ok = bool(a.allowed[i, j])
            _box(ax, x, y, cell * 0.94, cell * 0.94,
                 'allowed' if ok else 'blocked',
                 face='#e3f1e6' if ok else '#ececec',
                 edge=SLIDE if ok else '#bbbbbb',
                 fontsize=8.5, colour=SLIDE if ok else '#999999')
        ax.text(-0.25, (a.n - 1 - i) * cell + 0.47,
                f'{i + 1}. "{s.inputs[i]}"', ha='right', va='center', fontsize=10, color=LINK)
    for j in range(a.n):
        ax.text(j * cell + 0.47, a.n * cell + 0.12, f'{j + 1}\n"{s.inputs[j]}"', ha='center',
                va='bottom', fontsize=9.5, color=INK)
    ax.text(-2.55, a.n / 2, 'the position doing\nthe looking', ha='center', va='center',
            fontsize=10.5, weight='bold', color=LINK, rotation=90)
    ax.text(a.n / 2, a.n * cell + 1.15, 'the position being looked at', ha='center',
            va='center', fontsize=10.5, weight='bold', color=INK)
    ax.text(a.n / 2, -0.75, f'{a.n_allowed} of the {a.n * a.n} pairs are allowed, and the '
                            'blocked ones are exactly the positions that hold the answer',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.set_xlim(-3.4, a.n * cell + 0.3)
    ax.set_ylim(-1.3, a.n * cell + 1.6)
    ax.set_title('The causal mask: a position may look at itself and at everything before it, '
                 'and at nothing after it', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'causal-mask-grid.svg')


def scores_before_after_mask() -> None:
    a = att()
    s = sim()
    labels = [f'{i + 1} "{w}"' for i, w in enumerate(s.inputs)]
    print('[scores] raw scores, row by row:')
    for i in range(a.n):
        print('[scores] row ' + str(i + 1) + ': ' +
              '  '.join(f'{v:+.2f}' for v in a.scores[i]))
    print('[weights] masked attention weights, row by row:')
    for i in range(a.n):
        print('[weights] row ' + str(i + 1) + ': ' +
              '  '.join(f'{v:.2f}' if a.allowed[i, j] else '  - '
                        for j, v in enumerate(a.weights[i])))

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.6), facecolor='white')
    span = 1.7 * float(np.abs(a.scores).max())
    _matrix(axes[0], a.scores, labels, labels, fmt='{:+.2f}', cmap='PuOr',
            vmin=-span, vmax=span, text_cut=2.0)
    axes[0].set_title('Step 1: the raw scores, every position against every position',
                      fontsize=11.5, weight='bold', color=INK)
    _matrix(axes[1], a.shown, labels, labels, fmt='{:.2f}', cmap='Greens', vmin=0.0, vmax=1.0)
    axes[1].set_title('Step 2: block the later positions, then soften each row to add up to 1',
                      fontsize=11.5, weight='bold', color=INK)
    for ax in axes:
        ax.set_xlabel('position being looked at', fontsize=10)
    axes[0].set_ylabel('position doing the looking', fontsize=10)
    fig.suptitle('Masking happens between the scores and the softening, so the blocked '
                 'weights are 0 and the allowed ones still add up to 1',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'scores-before-after-mask.svg')


def what_the_mask_stops() -> None:
    a = att()
    s = sim()
    row = 2                       # the position whose input is "arm" and whose target is "lifts"
    answer = row + 1              # the position that holds that target as its input
    open_w = a.weights_open[row]
    leak = float(open_w[answer])
    later = float(open_w[answer:].sum())
    print(f'[leak] without the mask, position {row + 1} ("{s.inputs[row]}") puts '
          f'{leak:.3f} of its weight on position {answer + 1} ("{s.inputs[answer]}"), '
          f'which is the answer it is being asked for, and {later:.3f} on that position '
          'and everything after it')
    print('[leak] masked weights:   ' + '  '.join(f'{v:.3f}' for v in a.weights[row]))
    print('[leak] unmasked weights: ' + '  '.join(f'{v:.3f}' for v in open_w))

    fig, ax = plt.subplots(figsize=(11.6, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(a.n)
    ax.bar(x - 0.2, a.weights[row], width=0.38, color=SLIDE, label='with the causal mask')
    ax.bar(x + 0.2, open_w, width=0.38, color=GRIP, label='with no mask at all')
    ax.annotate(f'{leak:.3f} of the weight lands on\nthe very word it must guess',
                xy=(answer + 0.2, open_w[answer]), xytext=(answer + 0.75, open_w[answer] + 0.16),
                fontsize=10, color=GRIP,
                arrowprops={'arrowstyle': '->', 'color': GRIP, 'lw': 1.2})
    ax.set_xticks(x)
    ax.set_xticklabels([f'{i + 1}\n"{w}"' for i, w in enumerate(s.inputs)], fontsize=10)
    ax.set_ylim(0, max(open_w.max(), a.weights[row].max()) + 0.3)
    ax.set_xlabel('position being looked at', fontsize=10)
    ax.set_ylabel('share of the mix taken from that position', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title(f'Position {row + 1} has to predict "{s.targets[row]}", and position '
                 f'{answer + 1} already holds it', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'what-the-mask-stops.svg')


# ==========================================================================
# section 3: teacher forcing and what one training step costs
# ==========================================================================

def teacher_forcing() -> None:
    s = sim()
    n_right = sum(s.right)
    print(f'[forcing] the model guessed right at {n_right} of {len(s.targets)} positions: ' +
          ', '.join(f'{i + 1}:"{g}"{"" if r else " (wrong)"}'
                    for i, (g, r) in enumerate(zip(s.guess, s.right))))

    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _bare(ax)
    w, h = 1.45, 0.6
    for i in range(len(s.targets)):
        x = 0.4 + i * 1.75
        _box(ax, x, 3.1, w, h, s.inputs[i], face='#eef3f9', edge=LINK, fontsize=10.5)
        ok = s.right[i]
        _box(ax, x, 1.75, w, h, s.guess[i], face='#fdecec' if not ok else '#eaf4ec',
             edge=GRIP if not ok else SLIDE, fontsize=10.5,
             colour=GRIP if not ok else SLIDE)
        _box(ax, x, 0.4, w, h, s.targets[i], face='white', edge=INK, fontsize=10.5,
             weight='bold')
        _arrow(ax, x + w / 2, 3.05, x + w / 2, 2.45, colour=MUTED, head=0.1)
        _arrow(ax, x + w / 2, 1.70, x + w / 2, 1.08, colour=MUTED, head=0.1)
        if i < len(s.targets) - 1:
            _arrow(ax, x + w + 0.03, 3.4, x + 1.72, 3.4, colour=LINK, head=0.1)
    ax.text(0.1, 3.4, 'fed in: the true token,\nalways', ha='right', va='center',
            fontsize=10, color=LINK, weight='bold')
    ax.text(0.1, 2.05, "the model's own best\nguess", ha='right', va='center', fontsize=10,
            color=INK, weight='bold')
    ax.text(0.1, 0.7, 'the true next token', ha='right', va='center', fontsize=10,
            color=INK, weight='bold')
    ax.text(0.1, 1.39, 'scored against', ha='right', va='center', fontsize=9, color=MUTED)
    ax.text(5.6, -0.35, f'the model was right at {n_right} of {len(s.targets)} positions, and a '
                        'wrong guess still never changes what the next position is fed',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.set_xlim(-4.0, 11.0)
    ax.set_ylim(-0.8, 4.2)
    ax.set_title('Teacher forcing: the true tokens go in, the guesses only go to the loss',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'teacher-forcing.svg')


def errors_compound() -> None:
    lengths = np.arange(1, 61)
    rates = [0.90, 0.95, 0.99]
    colours = [GRIP, WRIST, SLIDE]
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    for p, colour in zip(rates, colours):
        whole = p ** lengths
        ax.plot(lengths, whole, color=colour, lw=2,
                label=f'{p * 100:.0f} per cent right on each token')
        at20 = p ** 20
        print(f'[compound] {p * 100:.0f} per cent per token: a run of 20 tokens is all right '
              f'{at20 * 100:.1f} per cent of the time, a run of 60 tokens '
              f'{p ** 60 * 100:.2f} per cent')
        ax.scatter([20], [at20], color=colour, zorder=5, s=35)
        ax.text(21, at20 + 0.02, f'{at20 * 100:.0f}%', fontsize=9.5, color=colour)
    ax.axvline(20, color=MUTED, ls=':', lw=1.0)
    ax.text(20.4, 0.95, 'a 20-token answer', fontsize=9.5, color=MUTED)
    ax.set_xlim(1, 60)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('length of the answer, in tokens', fontsize=10)
    ax.set_ylabel('chance every token in it is right', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('Why training on true tokens and running on its own tokens are different jobs',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'errors-compound.svg')


def training_memory() -> None:
    batch, seq, saved_per_layer = 8, 512, 10
    weights = P_TOTAL * NBYTES
    grads = P_TOTAL * NBYTES
    adam = P_TOTAL * 8                       # two running numbers, four bytes each
    master = P_TOTAL * 4                     # the careful copy of the weights
    acts = batch * seq * WIDTH * NBYTES * saved_per_layer * LAYERS
    parts = [('the weights', weights, LINK),
             ('the gradients', grads, WRIST),
             ('the optimiser\'s two\nrunning numbers', adam, PURPLE),
             ('the careful copy\nof the weights', master, TEAL),
             (f'activations saved for\n{batch} x {seq} tokens', acts, GRIP)]
    total = sum(v for _, v, _ in parts)
    print(f'[train-mem] weights {weights / GIB:.3f} GiB, gradients {grads / GIB:.3f} GiB, '
          f'optimiser {adam / GIB:.3f} GiB, master copy {master / GIB:.3f} GiB, '
          f'activations {acts / GIB:.3f} GiB')
    print(f'[train-mem] training total {total / GIB:.2f} GiB against {weights / GIB:.3f} GiB '
          f'to only run it, which is {total / weights:.1f} times as much')

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.5, 1.0]})
    ax = axes[0]
    _plain(ax)
    names = [p[0] for p in parts]
    vals = [p[1] / GIB for p in parts]
    ax.bar(names, vals, color=[p[2] for p in parts], width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.06, f'{v:.2f} GiB', ha='center', fontsize=10, color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel('memory held during training (GiB)', fontsize=10)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_title('What a training step has to keep in memory', fontsize=12, weight='bold',
                 color=INK)

    ax = axes[1]
    _plain(ax)
    bottom = 0.0
    for name, v, colour in parts:
        ax.bar(['training'], [v / GIB], bottom=[bottom], color=colour, width=0.45)
        bottom += v / GIB
    ax.bar(['running'], [weights / GIB], color=LINK, width=0.45)
    ax.text(0, total / GIB + 0.15, f'{total / GIB:.2f} GiB', ha='center', fontsize=11,
            weight='bold', color=INK)
    ax.text(1, weights / GIB + 0.15, f'{weights / GIB:.2f} GiB', ha='center', fontsize=11,
            weight='bold', color=INK)
    ax.set_ylim(0, total / GIB * 1.2)
    ax.set_ylabel('memory (GiB)', fontsize=10)
    ax.set_title(f'Training the same model needs {total / weights:.1f} times the memory',
                 fontsize=12, weight='bold', color=INK)
    fig.suptitle(f'The example model has {P_TOTAL / 1e6:.0f} million parameters, and that '
                 'number sets every bar here', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'training-memory.svg')


# ==========================================================================
# section 4: running the model one token at a time, and the key-value cache
# ==========================================================================

def generation_steps() -> None:
    prompt = ['the', 'arm', 'lifts']
    made = ['the', 'red', 'block']
    reads = [len(prompt) + i for i in range(len(made))]
    print(f'[steps] prompt of {len(prompt)} tokens, then steps that read '
          f'{reads} positions and write one token each: {made}')

    fig, ax = plt.subplots(figsize=(12.2, 5.8), facecolor='white')
    _bare(ax)
    w, h = 1.25, 0.58
    rows = [('the prompt goes in', prompt, -1)]
    for i, token in enumerate(made):
        rows.append((f'step {i + 1}', prompt + made[:i] + [token], len(prompt) + i))
    for r, (name, tokens, new_at) in enumerate(rows):
        y = (len(rows) - 1 - r) * 1.02
        for j, token in enumerate(tokens):
            x = 2.0 + j * 1.4
            fresh = (j == new_at)
            _box(ax, x, y, w, h, token,
                 face='#fdf0d8' if fresh else '#eef3f9',
                 edge=JOINT if fresh else LINK,
                 fontsize=10, colour=INK, weight='bold' if fresh else 'normal')
        ax.text(1.85, y + h / 2, name, ha='right', va='center', fontsize=10.5, color=INK,
                weight='bold')
        if new_at >= 0:
            ax.text(2.0 + len(tokens) * 1.4 + 0.1, y + h / 2,
                    f'reads {new_at} earlier positions, writes 1 token', ha='left',
                    va='center', fontsize=9.5, color=MUTED)
        else:
            ax.text(2.0 + len(tokens) * 1.4 + 0.1, y + h / 2,
                    f'all {len(tokens)} positions at once', ha='left', va='center',
                    fontsize=9.5, color=MUTED)
    ax.text(6.0, -0.75, 'training read the whole sentence in one pass; generation adds one '
                        'token at a time and each step reads everything before it',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.set_xlim(-2.6, 16.0)
    ax.set_ylim(-1.15, len(rows) * 1.02 + 0.2)
    ax.set_title('Generation is a loop: one token out, then that token goes back in',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'generation-steps.svg')


def cache_saves_work() -> None:
    n = np.arange(1, 1025)
    without = n * (n + 1) / 2.0
    with_cache = n.astype(float)
    for k in (8, 128, 512, 1024):
        print(f'[cache-work] {k} tokens: without a cache {int(k * (k + 1) / 2):,} '
              f'position passes, with a cache {k:,}, which is '
              f'{(k + 1) / 2:.1f} times less work')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(n, without, color=GRIP, lw=2, label='no cache: every step redoes every position')
    ax.plot(n, with_cache, color=SLIDE, lw=2, label='with a cache: every step does one position')
    for k in (128, 512, 1024):
        ax.scatter([k], [k * (k + 1) / 2], color=GRIP, s=30, zorder=5)
        ax.text(k * 0.95, k * (k + 1) / 2 * 1.5, f'{int(k * (k + 1) / 2):,}', fontsize=9,
                color=GRIP, ha='right')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens generated', fontsize=10)
    ax.set_ylabel('position passes through the stack (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('The work the cache removes', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ks = [8, 64, 512, 4096]
    ratios = [(k + 1) / 2 for k in ks]
    ax.bar([str(k) for k in ks], ratios, color=PURPLE, width=0.55)
    for i, (k, r) in enumerate(zip(ks, ratios)):
        ax.text(i, r * 1.05, f'{r:.0f}x', ha='center', fontsize=10.5, weight='bold', color=INK)
        print(f'[cache-work] saving factor at {k} tokens: {r:.1f} times')
    ax.set_yscale('log')
    ax.set_ylim(1, max(ratios) * 3)
    ax.set_xlabel('tokens generated', fontsize=10)
    ax.set_ylabel('times less work than redoing everything (log scale)', fontsize=10)
    ax.set_title('The longer the answer, the more the cache saves', fontsize=12,
                 weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'cache-saves-work.svg')


def cache_size_arithmetic() -> None:
    lengths = [512, 2048, 8192, 32768]
    sizes = [CACHE_PER_TOKEN * n for n in lengths]
    for n, b in zip(lengths, sizes):
        print(f'[cache-size] {n:,} tokens: {b:,} bytes = {b / MIB:.0f} MiB '
              f'({b / WEIGHT_BYTES:.2f} times the weights)')

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.15, 1.0]})
    ax = axes[0]
    _bare(ax)
    lines = [
        ('keys and values, so two of them', '2'),
        (f'one pair for each of {LAYERS} layers', f'x {LAYERS}'),
        (f'{HEADS} heads in each layer', f'x {HEADS}'),
        (f'{HEAD_DIM} numbers in each head', f'x {HEAD_DIM}'),
        (f'{NBYTES} bytes for each number', f'x {NBYTES}'),
    ]
    for i, (text, factor) in enumerate(lines):
        y = 5.2 - i * 0.78
        ax.text(0.0, y, text, fontsize=11, color=INK)
        ax.text(6.3, y, factor, fontsize=11, color=LINK, weight='bold', ha='right')
    ax.plot([-0.1, 6.4], [1.05, 1.05], color=INK, lw=1.0)
    ax.text(0.0, 0.5, 'bytes of cache for one token', fontsize=11.5, weight='bold', color=INK)
    ax.text(6.3, 0.5, f'{CACHE_PER_TOKEN:,}', fontsize=11.5, weight='bold', color=SLIDE,
            ha='right')
    ax.text(0.0, -0.15, f'which is {CACHE_PER_TOKEN / 1024:.0f} KiB a token, so a sequence of '
                        f'{TRAINED_LEN:,} tokens holds\n'
                        f'{CACHE_PER_TOKEN * TRAINED_LEN / MIB:.0f} MiB and the weights '
                        f'hold {WEIGHT_BYTES / MIB:.0f} MiB',
            fontsize=10.5, color=INK, va='top')
    ax.set_xlim(-0.4, 6.8)
    ax.set_ylim(-1.6, 5.9)
    ax.set_title('The cache for one token, worked out factor by factor', fontsize=12,
                 weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    vals = [b / MIB for b in sizes]
    ax.bar([f'{n:,}' for n in lengths], vals, color=TEAL, width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.05, f'{v:,.0f} MiB', ha='center', fontsize=10, color=INK)
    ax.axhline(WEIGHT_BYTES / MIB, color=GRIP, ls='--', lw=1.4)
    ax.text(-0.42, WEIGHT_BYTES / MIB * 1.12, f'all the weights: {WEIGHT_BYTES / MIB:.0f} MiB',
            fontsize=9.5, color=GRIP)
    ax.set_yscale('log')
    ax.set_ylim(20, max(vals) * 3)
    ax.set_xlabel('tokens held in the cache', fontsize=10)
    ax.set_ylabel('cache for one sequence (MiB, log scale)', fontsize=10)
    ax.set_title('Past a few thousand tokens the cache is the bigger thing in memory',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'cache-size-arithmetic.svg')


def cache_versus_weights() -> None:
    batches = [1, 4, 16, 64]
    length = 2048
    per_seq = CACHE_PER_TOKEN * length
    totals = [(WEIGHT_BYTES + b * per_seq) / GIB for b in batches]
    for b, t in zip(batches, totals):
        print(f'[cache-vs-weights] {length:,} tokens, {b} sequences at once: '
              f'weights {WEIGHT_BYTES / GIB:.2f} GiB + cache {b * per_seq / GIB:.2f} GiB '
              f'= {t:.2f} GiB')

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    labels = [str(b) for b in batches]
    ax.bar(labels, [WEIGHT_BYTES / GIB] * len(batches), color=LINK, width=0.5,
           label='the weights, shared by every sequence')
    ax.bar(labels, [b * per_seq / GIB for b in batches], bottom=[WEIGHT_BYTES / GIB] * len(batches),
           color=TEAL, width=0.5, label=f'the caches, one for each sequence of {length:,} tokens')
    for i, t in enumerate(totals):
        ax.text(i, t + 0.15, f'{t:.2f} GiB', ha='center', fontsize=10.5, color=INK)
    ax.set_xlabel('sequences being answered at the same time', fontsize=10)
    ax.set_ylabel('memory held (GiB)', fontsize=10)
    ax.set_ylim(0, max(totals) * 1.18)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('The weights are paid for once; the cache is paid for again for every '
                 'conversation', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'cache-versus-weights.svg')


# ==========================================================================
# section 5: choosing the next token
# ==========================================================================

SAMPLE_POS: int = 3        # the position where the model is least sure


def logits_to_probabilities() -> None:
    s = sim()
    i = SAMPLE_POS
    z, p = s.logits[i], s.probs[i]
    order = np.argsort(-p)
    print(f'[sampling] position {i + 1} ("{s.inputs[i]}" goes in, "{s.targets[i]}" is right)')
    print('[sampling] raw outputs: ' + ', '.join(f'{WORDS[k]} {z[k]:+.2f}' for k in order))
    print('[sampling] after softening: ' + ', '.join(f'{WORDS[k]} {p[k]:.3f}' for k in order))
    print(f'[sampling] they add up to {p.sum():.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = [WORDS[k] for k in order]
    ax.bar(names, z[order], color=[LINK if v >= 0 else WRIST for v in z[order]], width=0.6)
    for j, v in enumerate(z[order]):
        ax.text(j, (v + 0.12) if v >= 0 else 0.12, f'{v:+.2f}', ha='center', fontsize=9,
                color=INK)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9.5)
    ax.set_ylabel('raw output for that word', fontsize=10)
    ax.set_title('What comes out of the last layer: one plain number for each word',
                 fontsize=11.5, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(names, p[order], color=SLIDE, width=0.6)
    for j, v in enumerate(p[order]):
        ax.text(j, v + 0.006, f'{v:.3f}', ha='center', fontsize=9, color=INK)
    ax.set_xticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9.5)
    ax.set_ylim(0, max(p) * 1.25)
    ax.set_ylabel('chance of that word', fontsize=10)
    ax.set_title(f'After softening: {len(WORDS)} chances that add up to {p.sum():.2f}',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'logits-to-probabilities.svg')


def three_temperatures() -> None:
    s = sim()
    z = s.logits[SAMPLE_POS]
    temps = [0.5, 1.0, 1.5]
    colours = [PURPLE, SLIDE, WRIST]
    order = np.argsort(-_softmax(z))
    names = [WORDS[k] for k in order]
    dists = []
    for t in temps:
        p = _softmax(z / t)
        dists.append(p)
        ent = float(-np.sum(p * np.log(p)))
        print(f'[temperature] T = {t}: top word "{WORDS[int(p.argmax())]}" at {p.max():.3f}, '
              f'spread (entropy) {ent:.2f} nats, two least likely words '
              f'{p[order[-1]]:.4f} and {p[order[-2]]:.4f}')
        print(f'[temperature] T = {t}: ' + ', '.join(f'{WORDS[k]} {p[k]:.3f}' for k in order))

    fig, ax = plt.subplots(figsize=(12.4, 5.4), facecolor='white')
    _plain(ax)
    x = np.arange(len(WORDS))
    for j, (t, p, colour) in enumerate(zip(temps, dists, colours)):
        ent = float(-np.sum(p * np.log(p)))
        ax.bar(x + (j - 1) * 0.27, p[order], width=0.25, color=colour,
               label=f'temperature {t}  (spread {ent:.2f} nats)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=10)
    ax.set_ylabel('chance of that word', fontsize=10)
    ax.set_xlabel('the twelve words, most likely first', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper right')
    ax.set_title('One set of raw outputs divided by three temperatures: below 1 sharpens, '
                 'above 1 flattens', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'three-temperatures.svg')


def top_p_cut() -> None:
    s = sim()
    p = s.probs[SAMPLE_POS]
    order = np.argsort(-p)
    sp = p[order]
    cum = np.cumsum(sp)
    cutoff = 0.9
    keep = int(np.searchsorted(cum, cutoff) + 1)
    kept = sp[:keep]
    renorm = kept / kept.sum()
    print(f'[top-p] cutting at {cutoff}: the running total reaches '
          f'{cum[keep - 1]:.3f} after {keep} words, so {keep} of {len(WORDS)} words are kept '
          f'and {len(WORDS) - keep} are thrown away')
    print('[top-p] running total: ' +
          ', '.join(f'{WORDS[k]} {c:.3f}' for k, c in zip(order, cum)))
    print('[top-p] kept and shared out again: ' +
          ', '.join(f'{WORDS[k]} {v:.3f}' for k, v in zip(order[:keep], renorm)))

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = [WORDS[k] for k in order]
    ax.bar(names, sp, color=[SLIDE if j < keep else '#dddddd' for j in range(len(sp))],
           width=0.6)
    ax2 = ax.twinx()
    ax2.plot(names, cum, color=GRIP, marker='o', lw=1.6, label='running total')
    ax2.axhline(cutoff, color=GRIP, ls='--', lw=1.2)
    ax2.text(len(names) - 0.4, cutoff + 0.02, f'cut at {cutoff}', ha='right', fontsize=9.5,
             color=GRIP)
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel('running total of the chances', fontsize=10, color=GRIP)
    ax2.tick_params(axis='y', colors=GRIP, labelsize=9.5)
    ax.axvline(keep - 0.5, color=INK, ls=':', lw=1.4)
    ax.set_xticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9.5)
    ax.set_ylabel('chance of that word', fontsize=10)
    ax.set_title(f'The running total passes {cutoff} after {keep} words', fontsize=11.5,
                 weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(names[:keep], renorm, color=TEAL, width=0.5)
    for j, v in enumerate(renorm):
        ax.text(j, v + 0.008, f'{v:.3f}', ha='center', fontsize=10, color=INK)
    ax.set_xticks(np.arange(keep))
    ax.set_xticklabels(names[:keep], rotation=45, ha='right', fontsize=10)
    ax.set_ylim(0, max(renorm) * 1.25)
    ax.set_ylabel('chance after sharing out again', fontsize=10)
    ax.set_title(f'The {keep} survivors, shared out so they add up to {renorm.sum():.2f}',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'top-p-cut.svg')


def greedy_loses() -> None:
    s = sim()
    first = s.probs[SAMPLE_POS]
    order = np.argsort(-first)[:2]
    branch: dict[int, Arr] = {}
    seed_used = -1
    for seed in range(20, 400):
        rng = np.random.default_rng(seed)
        cand = {int(k): _softmax(rng.normal(0.0, 1.6, size=len(WORDS))) for k in order}
        joints = {(int(k), int(c)): float(first[k] * cand[int(k)][c])
                  for k in order for c in np.argsort(-cand[int(k)])[:3]}
        greedy_first = int(order[0])
        greedy_second = int(np.argmax(cand[greedy_first]))
        best = max(joints, key=lambda key: joints[key])
        if (best[0] != greedy_first and best[1] != best[0]
                and int(np.argmax(cand[greedy_first])) != greedy_first
                and joints[best] > joints[(greedy_first, greedy_second)] * 1.3):
            branch = cand
            seed_used = seed
            break
    greedy_first = int(order[0])
    greedy_second = int(np.argmax(branch[greedy_first]))
    greedy_joint = float(first[greedy_first] * branch[greedy_first][greedy_second])
    pairs = {(int(k), int(c)): float(first[k] * branch[int(k)][c])
             for k in order for c in np.argsort(-branch[int(k)])[:3]}
    best = max(pairs, key=lambda key: pairs[key])
    print(f'[greedy] second-step numbers from seed {seed_used}')
    print(f'[greedy] greedy takes "{WORDS[greedy_first]}" ({first[greedy_first]:.3f}) then '
          f'"{WORDS[greedy_second]}" ({branch[greedy_first][greedy_second]:.3f}), '
          f'so the pair has chance {greedy_joint:.4f}')
    print(f'[greedy] the best pair is "{WORDS[best[0]]}" ({first[best[0]]:.3f}) then '
          f'"{WORDS[best[1]]}" ({branch[best[0]][best[1]]:.3f}), '
          f'chance {pairs[best]:.4f}, which is {pairs[best] / greedy_joint:.2f} times better')

    fig, ax = plt.subplots(figsize=(12.0, 6.0), facecolor='white')
    _bare(ax)
    _box(ax, 0.0, 2.95, 2.0, 0.7, f'"{s.inputs[SAMPLE_POS]}"', face='#eef3f9', edge=LINK,
         fontsize=11)
    ys = [4.8, 1.5]
    for bi, k in enumerate(order):
        k = int(k)
        ax.add_patch(Rectangle((3.4, ys[bi] - 0.35), 2.1, 0.7, facecolor='white',
                               edgecolor=SLIDE if k == best[0] else INK, lw=1.4, zorder=2))
        ax.text(4.45, ys[bi], f'"{WORDS[k]}"  {first[k]:.3f}', ha='center', va='center',
                fontsize=11, color=INK, zorder=3)
        _arrow(ax, 2.05, 3.30, 3.35, ys[bi], colour=MUTED, head=0.11)
        tops = np.argsort(-branch[k])[:3]
        for ci, c in enumerate(tops):
            c = int(c)
            yy = ys[bi] + 1.1 - ci * 1.1
            joint = float(first[k] * branch[k][c])
            winner = (k, c) == best
            greedy = (k == greedy_first and c == greedy_second)
            face = '#eaf4ec' if winner else ('#fdecec' if greedy else 'white')
            edge = SLIDE if winner else (GRIP if greedy else '#bbbbbb')
            ax.add_patch(Rectangle((6.9, yy - 0.34), 4.6, 0.68, facecolor=face,
                                   edgecolor=edge, lw=1.4, zorder=2))
            ax.text(7.1, yy, f'"{WORDS[c]}"  {branch[k][c]:.3f}', ha='left', va='center',
                    fontsize=10.5, color=INK, zorder=3)
            ax.text(11.3, yy, f'pair: {joint:.4f}', ha='right', va='center', fontsize=10.5,
                    color=SLIDE if winner else (GRIP if greedy else MUTED), zorder=3,
                    weight='bold' if winner or greedy else 'normal')
            _arrow(ax, 5.55, ys[bi], 6.85, yy, colour='#cccccc', head=0.09)
    ax.text(4.45, 6.65, 'first token', ha='center', fontsize=10.5, weight='bold', color=INK)
    ax.text(9.2, 6.65, 'second token, and the chance of the pair', ha='center', fontsize=10.5,
            weight='bold', color=INK)
    ax.text(5.9, -0.55, f'taking the best first token gives a pair worth {greedy_joint:.4f}, '
                        f'while the best pair is worth {pairs[best]:.4f}',
            ha='center', fontsize=11, color=INK)
    ax.set_xlim(-0.3, 11.9)
    ax.set_ylim(-1.0, 7.1)
    ax.set_title('Why always taking the most likely token is not the same as finding the '
                 'most likely answer', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'greedy-loses.svg')


# ==========================================================================
# section 6: the context window, and what makes generation slow
# ==========================================================================

def context_cost() -> None:
    lengths = np.array([1024, 4096, 8192, 32768, 131072])
    pairs = lengths.astype(float) * (lengths + 1) / 2.0
    cache = lengths.astype(float) * CACHE_PER_TOKEN
    for n, pr, cb in zip(lengths, pairs, cache):
        print(f'[context] {n:,} tokens: {pr:,.0f} allowed pairs in every head of every layer, '
              f'cache {cb / GIB:.2f} GiB for one sequence')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    nn = np.arange(256, 131073, 256, dtype=float)
    ax.plot(nn, nn * (nn + 1) / 2, color=GRIP, lw=2, label='pairs of positions to score')
    ax.plot(nn, nn, color=SLIDE, lw=2, label='positions, for comparison')
    for n, pr in zip(lengths, pairs):
        ax.scatter([n], [pr], color=GRIP, s=28, zorder=5)
        ax.text(n * 0.9, pr * 2.0, f'{pr / 1e6:,.1f} million', fontsize=9, color=GRIP,
                ha='right')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens in the context', fontsize=10)
    ax.set_ylabel('things to work out, per head per layer (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Doubling the context quadruples the pairs', fontsize=12, weight='bold',
                 color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar([f'{n:,}' for n in lengths], cache / GIB, color=TEAL, width=0.55)
    for i, v in enumerate(cache / GIB):
        ax.text(i, v * 1.06, f'{v:.2f} GiB', ha='center', fontsize=10, color=INK)
    ax.axhline(WEIGHT_BYTES / GIB, color=GRIP, ls='--', lw=1.3)
    ax.text(-0.45, WEIGHT_BYTES / GIB * 1.15, f'the weights: {WEIGHT_BYTES / GIB:.2f} GiB',
            fontsize=9.5, color=GRIP)
    ax.set_yscale('log')
    ax.set_ylim(0.03, max(cache / GIB) * 4)
    ax.set_xlabel('tokens in the context', fontsize=10)
    ax.set_ylabel('cache for one sequence (GiB, log scale)', fontsize=10)
    ax.set_title('And it doubles the memory one conversation holds', fontsize=12,
                 weight='bold', color=INK)
    fig.suptitle(f'The example model, trained on {TRAINED_LEN:,} tokens of context',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'context-cost.svg')


def past_the_window() -> None:
    window = 2048
    talk = 3000
    dropped = talk - window
    print(f'[window] a conversation of {talk:,} tokens in a window of {window:,}: '
          f'the oldest {dropped:,} tokens fall out, which is '
          f'{dropped / talk * 100:.1f} per cent of what was said')

    fig, ax = plt.subplots(figsize=(11.8, 4.6), facecolor='white')
    _bare(ax)
    scale = 10.0 / talk
    ax.add_patch(Rectangle((0, 2.0), dropped * scale, 0.8, facecolor='#ececec',
                           edgecolor='#aaaaaa', lw=1.2))
    ax.add_patch(Rectangle((dropped * scale, 2.0), window * scale, 0.8, facecolor='#e3f1e6',
                           edgecolor=SLIDE, lw=1.4))
    ax.text(dropped * scale / 2, 2.4, f'{dropped:,} tokens\nfallen out', ha='center',
            va='center', fontsize=10, color='#777777')
    ax.text(dropped * scale + window * scale / 2, 2.4,
            f'the {window:,} tokens the model can still see', ha='center', va='center',
            fontsize=11, color=SLIDE, weight='bold')
    ax.text(0, 3.15, 'the start of the conversation', fontsize=10, color=INK)
    ax.text(10.0, 3.15, 'the newest token', fontsize=10, color=INK, ha='right')
    ax.add_patch(Rectangle((0, 0.7), 10.0, 0.75, facecolor='#eef3f9', edgecolor=LINK, lw=1.2))
    ax.text(5.0, 1.07, f'everything that was said: {talk:,} tokens', ha='center', va='center',
            fontsize=11, color=LINK)
    _arrow(ax, 1.2, 1.5, 1.2, 1.95, colour=MUTED, head=0.1)
    _arrow(ax, 7.0, 1.5, 7.0, 1.95, colour=MUTED, head=0.1)
    ax.text(5.0, 0.15, f'{dropped / talk * 100:.0f} per cent of the conversation is gone, and '
                       'nothing in the answer says so',
            ha='center', fontsize=10.5, color=INK)
    ax.set_xlim(-0.4, 10.4)
    ax.set_ylim(-0.2, 3.6)
    ax.set_title(f'Past the window: a {talk:,}-token conversation inside a '
                 f'{window:,}-token window', fontsize=12.5, weight='bold', color=INK)
    _save(fig, TRAIN_DOC, 'past-the-window.svg')


def memory_bound() -> None:
    length, batch = 2048, 1
    bytes_read = _bytes_per_step(length, batch)
    flops = batch * _flops_per_token(length)
    t_mem = bytes_read / BANDWIDTH
    t_ar = flops / PEAK_FLOPS
    print(f'[bound] at {length:,} tokens and one sequence: {bytes_read:,.0f} bytes read '
          f'({WEIGHT_BYTES:,} of weights plus {batch * CACHE_PER_TOKEN * length:,} of cache) '
          f'and {flops:,.0f} arithmetic operations')
    print(f'[bound] reading takes {t_mem * 1e6:,.0f} microseconds, the arithmetic takes '
          f'{t_ar * 1e6:,.1f} microseconds, so reading takes {t_mem / t_ar:.0f} times longer')
    print(f'[bound] that is {1 / t_mem:,.0f} tokens a second at best')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.1]})
    ax = axes[0]
    _plain(ax)
    ax.bar(['waiting for memory', 'doing the arithmetic'], [t_mem * 1e6, t_ar * 1e6],
           color=[GRIP, SLIDE], width=0.5)
    ax.text(0, t_mem * 1e6 * 1.03, f'{t_mem * 1e6:,.0f} microseconds', ha='center',
            fontsize=10.5, color=INK)
    ax.text(1, t_ar * 1e6 * 1.3, f'{t_ar * 1e6:,.1f} microseconds', ha='center', fontsize=10.5,
            color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, t_mem * 1e6 * 4)
    ax.set_ylabel('time for one token (microseconds, log scale)', fontsize=10)
    ax.set_title(f'One token, one sequence: reading takes {t_mem / t_ar:.0f} times as long '
                 'as the sums', fontsize=11.5, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(['bytes that must be read for one token'], [WEIGHT_BYTES / MIB], color=LINK,
           width=0.4, label=f'every weight, once: {WEIGHT_BYTES / MIB:.0f} MiB')
    ax.bar(['bytes that must be read for one token'], [CACHE_PER_TOKEN * length / MIB],
           bottom=[WEIGHT_BYTES / MIB], color=TEAL, width=0.4,
           label=f'the whole cache, once: {CACHE_PER_TOKEN * length / MIB:.0f} MiB')
    ax.text(0, bytes_read / MIB + 25, f'{bytes_read / MIB:.0f} MiB for a single token',
            ha='center', fontsize=11, weight='bold', color=INK)
    ax.set_ylim(0, bytes_read / MIB * 1.3)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylabel('memory read (MiB)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title('Where the reading goes', fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('Generation is held up by memory reading, not by arithmetic',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'memory-bound.svg')


def batch_helps() -> None:
    length = 2048
    batches = np.arange(1, 65)
    times = np.array([max(_bytes_per_step(length, int(b)) / BANDWIDTH,
                          b * _flops_per_token(length) / PEAK_FLOPS) for b in batches])
    per_token = times / batches
    throughput = batches / times
    for b in (1, 2, 8, 32, 64):
        i = b - 1
        print(f'[batch] {b:2d} sequences: {times[i] * 1e3:.2f} ms a step, '
              f'{per_token[i] * 1e6:,.0f} microseconds a token, '
              f'{throughput[i]:,.0f} tokens a second in all')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(batches, throughput, color=LINK, lw=2)
    for b in (1, 8, 32, 64):
        ax.scatter([b], [throughput[b - 1]], color=LINK, s=30, zorder=5)
        ax.text(b, throughput[b - 1] * 1.04, f'{throughput[b - 1]:,.0f}', fontsize=9.5,
                color=INK, ha='center')
    ax.set_xlabel('sequences answered at the same time', fontsize=10)
    ax.set_ylabel('tokens a second, all sequences together', fontsize=10)
    ax.set_ylim(0, throughput.max() * 1.2)
    ax.set_title('Answering several at once gets more out of the same reading',
                 fontsize=11.5, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.plot(batches, per_token * 1e6, color=GRIP, lw=2)
    ax.axhline(per_token[0] * 1e6, color=MUTED, ls=':', lw=1.0)
    ax.text(32, per_token[0] * 1e6 * 0.93, f'one sequence: {per_token[0] * 1e6:,.0f} '
                                           'microseconds a token', fontsize=9.5, color=MUTED)
    ax.set_xlabel('sequences answered at the same time', fontsize=10)
    ax.set_ylabel('microseconds for each token', fontsize=10)
    ax.set_ylim(0, per_token[0] * 1e6 * 1.2)
    ax.set_title('But each conversation does not get faster than a floor',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle(f'The example model at {length:,} tokens of context, on the example '
                 'accelerator', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TRAIN_DOC, 'batch-helps.svg')


# ==========================================================================
# 04_why-the-transformer-won.md
# section 1: what a convolution cannot do that attention can
# ==========================================================================

def layers_to_reach() -> None:
    dist = np.arange(2, 1025)
    kernels = [3, 5, 7]
    colours = [GRIP, WRIST, PURPLE]
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    for k, colour in zip(kernels, colours):
        need = np.ceil(dist / (k - 1))
        ax.plot(dist, need, color=colour, lw=2, label=f'convolution over {k} positions')
        at512 = int(np.ceil(512 / (k - 1)))
        print(f'[reach] a convolution over {k} positions needs {at512} layers to join two '
              f'positions 512 apart, and {int(np.ceil(64 / (k - 1)))} to join two 64 apart')
    ax.plot(dist, np.ones_like(dist), color=SLIDE, lw=2.5, label='attention, any distance')
    ax.annotate('attention: 1 layer, whatever the distance', xy=(300, 1), xytext=(60, 4),
                fontsize=10.5, color=SLIDE,
                arrowprops={'arrowstyle': '->', 'color': SLIDE, 'lw': 1.2})
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('distance between the two positions, in tokens', fontsize=10)
    ax.set_ylabel('layers needed before they can affect each other (log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title('How many layers it takes for one position to reach another',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'layers-to-reach.svg')


def receptive_cone() -> None:
    n, layers, k = 17, 5, 3
    centre = 8
    half = (k - 1) // 2
    counts = [1 + 2 * half * lay for lay in range(layers + 1)]
    print(f'[cone] a stack of {k}-wide convolutions: after '
          + ', '.join(f'{lay} layers it sees {c} positions' for lay, c in enumerate(counts)))
    print(f'[cone] to see all {n} positions from the middle it needs '
          f'{int(np.ceil((n - 1) / 2 / half))} layers')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _bare(ax)
    for lay in range(layers + 1):
        seen = range(max(0, centre - half * lay), min(n, centre + half * lay + 1))
        for j in range(n):
            inside = j in seen
            ax.add_patch(Rectangle((j, lay), 0.92, 0.82,
                                   facecolor='#d9ead9' if inside else '#f2f2f2',
                                   edgecolor=SLIDE if inside else '#dddddd', lw=1.0))
        word = 'layer' if lay == 1 else 'layers'
        cnt = len(list(seen))
        ax.text(-0.3, lay + 0.41, f'after {lay} {word}', ha='right', va='center', fontsize=10,
                color=INK)
        ax.text(n + 0.2, lay + 0.41, f'{cnt} position' + ('' if cnt == 1 else 's'),
                ha='left', va='center', fontsize=10, color=SLIDE)
    ax.add_patch(Rectangle((centre, 0), 0.92, 0.82, facecolor=JOINT, edgecolor=INK, lw=1.2))
    ax.text(centre + 0.46, 0.41, 'here', ha='center', va='center', fontsize=9, color=INK)
    for j in range(n):
        ax.text(j + 0.46, -0.45, str(j), ha='center', fontsize=9, color=MUTED)
    ax.text(n / 2, -1.1, 'position along the sentence', ha='center', fontsize=10.5, color=INK)
    ax.set_xlim(-4.2, n + 3.4)
    ax.set_ylim(-1.5, layers + 1.2)
    ax.set_title('A convolution three wide: the view grows by one position each side per layer',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'receptive-cone.svg')


def dilation_helps() -> None:
    layers = np.arange(1, 13)
    plain = 2 * layers + 1
    dilated = 2 ** (layers + 1) - 1
    context = 8192
    print(f'[dilation] after 12 layers: plain sees {plain[-1]} positions, '
          f'doubled gaps see {dilated[-1]:,} positions')
    need = int(np.ceil(np.log2(context + 1) - 1))
    print(f'[dilation] to cover {context:,} positions, doubling the gaps needs {need} layers '
          f'and plain layers need {int(np.ceil((context - 1) / 2)):,}')

    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(layers, plain, marker='o', color=GRIP, lw=2, label='plain convolution, 3 wide')
    ax.plot(layers, dilated, marker='s', color=WRIST, lw=2,
            label='same convolution with the gaps doubled each layer')
    ax.axhline(context, color=SLIDE, ls='--', lw=1.6)
    ax.text(1.1, context * 1.25, f'attention sees all {context:,} positions in its first layer',
            fontsize=10, color=SLIDE)
    ax.set_yscale('log')
    ax.set_ylim(1, context * 6)
    ax.set_xlabel('layers stacked', fontsize=10)
    ax.set_ylabel('positions one position can see (log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('Spreading the filter out helps, but the view is still a shape chosen '
                 'in advance', fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'dilation-helps.svg')


# ==========================================================================
# section 2: what a recurrent network cannot do
# ==========================================================================

def sequential_steps() -> None:
    lengths = [128, 512, 2048, 8192]
    step_us = 20.0              # a stated example: 20 microseconds for one small step
    rec = [n for n in lengths]
    tra = [LAYERS for _ in lengths]
    for n in lengths:
        print(f'[sequence] {n:,} positions: one after another {n:,} steps '
              f'= {n * step_us / 1000:.1f} ms at {step_us:.0f} microseconds a step; '
              f'all at once {LAYERS} layer steps = {LAYERS * step_us / 1000:.2f} ms')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    x = np.arange(len(lengths))
    ax.bar(x - 0.19, rec, width=0.36, color=GRIP, label='one position after another')
    ax.bar(x + 0.19, tra, width=0.36, color=SLIDE,
           label=f'all positions together, {LAYERS} layers deep')
    for i, (r, t) in enumerate(zip(rec, tra)):
        ax.text(i - 0.19, r * 1.1, f'{r:,}', ha='center', fontsize=9.5, color=INK)
        ax.text(i + 0.19, t * 1.1, f'{t}', ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{n:,}' for n in lengths])
    ax.set_yscale('log')
    ax.set_ylim(1, max(rec) * 4)
    ax.set_xlabel('positions in the sentence', fontsize=10)
    ax.set_ylabel('steps that must wait for the one before (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Steps that cannot be done at the same time', fontsize=12, weight='bold',
                 color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(x - 0.19, [n * step_us / 1000 for n in lengths], width=0.36, color=GRIP)
    ax.bar(x + 0.19, [LAYERS * step_us / 1000 for _ in lengths], width=0.36, color=SLIDE)
    for i, n in enumerate(lengths):
        ax.text(i - 0.19, n * step_us / 1000 * 1.1, f'{n * step_us / 1000:.1f} ms', ha='center',
                fontsize=9.5, color=INK)
        ax.text(i + 0.19, LAYERS * step_us / 1000 * 1.1, f'{LAYERS * step_us / 1000:.2f} ms',
                ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{n:,}' for n in lengths])
    ax.set_yscale('log')
    ax.set_ylim(0.1, max(lengths) * step_us / 1000 * 5)
    ax.set_xlabel('positions in the sentence', fontsize=10)
    ax.set_ylabel('time for one pass (milliseconds, log scale)', fontsize=10)
    ax.set_title(f'At a stated {step_us:.0f} microseconds a step', fontsize=12,
                 weight='bold', color=INK)
    fig.suptitle('Why order-bound layers waste parallel hardware', fontsize=12.5,
                 weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'sequential-steps.svg')


def hardware_busy() -> None:
    n = 12
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    for ax, kind in zip(axes, ('one after another', 'all at once')):
        _bare(ax)
        busy = 0
        for t in range(n):
            for j in range(n):
                if kind == 'one after another':
                    on = (j == t)
                else:
                    on = (t == 0)
                busy += int(on)
                ax.add_patch(Rectangle((j, n - 1 - t), 0.9, 0.9,
                                       facecolor=SLIDE if on else '#f0f0f0',
                                       edgecolor='#dddddd', lw=0.8))
        for j in range(n):
            ax.text(j + 0.45, -0.45, str(j + 1), ha='center', fontsize=8, color=MUTED)
            ax.text(-0.25, n - 1 - j + 0.45, str(j + 1), ha='right', va='center', fontsize=8,
                    color=MUTED)
        ax.text(n / 2, -1.1, 'position', ha='center', fontsize=10, color=INK)
        ax.text(-1.15, n / 2, 'time slot', ha='center', va='center', fontsize=10, color=INK,
                rotation=90)
        slots = n if kind == 'one after another' else 1
        title = ('A layer that must run in order' if kind == 'one after another'
                 else 'Attention over the same positions')
        ax.set_title(f'{title}\n{slots} time slot' + ('' if slots == 1 else 's')
                     + f' used, {busy // slots} position'
                     + ('' if busy // slots == 1 else 's') + ' worked on in each',
                     fontsize=11.5, weight='bold', color=INK)
        ax.set_xlim(-1.6, n + 0.3)
        ax.set_ylim(-1.5, n + 0.3)
        print(f'[busy] {kind}: {slots} time slots used, {busy // slots} positions in each, '
              f'{busy} positions in all')
    fig.suptitle('The same twelve positions, worked on by hardware that can do twelve things '
                 'at once', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'hardware-busy.svg')


def signal_decay() -> None:
    dist = np.arange(1, 513)
    factors = [0.90, 0.95, 0.98]
    colours = [GRIP, WRIST, PURPLE]
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    for f, colour in zip(factors, colours):
        ax.plot(dist, f ** dist, color=colour, lw=2,
                label=f'each step keeps {f * 100:.0f} per cent of what came in')
        print(f'[decay] keeping {f * 100:.0f} per cent a step: after 100 steps '
              f'{f ** 100:.2e} is left, after 511 steps {f ** 511:.2e}')
    ax.axhline(1.0, color=SLIDE, lw=2.5)
    ax.text(5, 1.4, 'attention: one layer, so nothing is passed along and nothing shrinks',
            fontsize=10.5, color=SLIDE)
    ax.set_yscale('log')
    ax.set_ylim(1e-12, 12)
    ax.set_xlabel('how many positions back the information started', fontsize=10)
    ax.set_ylabel('how much of it survives (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax.set_title('Passing a summary along one step at a time shrinks it every step',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'signal-decay.svg')


# ==========================================================================
# section 3: what the transformer costs
# ==========================================================================

def _weight_work(n: float) -> float:
    """Arithmetic in one layer that uses the weights, for a sequence of n tokens."""
    return 8.0 * n * WIDTH * WIDTH + 2.0 * 2.0 * n * WIDTH * FFN


def _pair_work(n: float) -> float:
    """Arithmetic in one layer spent on pairs of positions, counting the allowed half only."""
    return 2.0 * n * n * WIDTH


def attention_overtakes() -> None:
    n = np.logspace(np.log10(256), np.log10(262144), 400)
    cross = 12.0 * WIDTH          # where 2 n^2 d equals 24 n d^2
    print(f'[crossover] the pair work passes the weight work at {cross:,.0f} tokens, '
          f'which is 12 times the width of {WIDTH}')
    for k in (1024, 8192, 32768, 131072):
        w, p = _weight_work(k), _pair_work(k)
        print(f'[crossover] {k:,} tokens: weight work {w / 1e12:.2f} teraoperations a layer, '
              f'pair work {p / 1e12:.2f}, pair share {p / (w + p) * 100:.0f} per cent')

    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(n, _weight_work(n) / 1e12, color=LINK, lw=2,
            label='work with the weights (grows with the length)')
    ax.plot(n, _pair_work(n) / 1e12, color=GRIP, lw=2,
            label='work on pairs of positions (grows with the length squared)')
    ax.axvline(cross, color=INK, ls=':', lw=1.4)
    ax.text(cross * 1.1, 0.02, f'they are equal at\n{cross:,.0f} tokens', fontsize=10,
            color=INK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens in the sequence', fontsize=10)
    ax.set_ylabel('arithmetic in one layer (trillions of operations, log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title(f'For the example model, pairs overtake weights at about '
                 f'{cross:,.0f} tokens', fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'attention-overtakes.svg')


def fraction_in_attention() -> None:
    n = np.logspace(np.log10(256), np.log10(262144), 400)
    share = _pair_work(n) / (_pair_work(n) + _weight_work(n)) * 100
    marks = [1024, 8192, 32768, 131072]
    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(n, share, color=GRIP, lw=2.2)
    for k in marks:
        v = _pair_work(k) / (_pair_work(k) + _weight_work(k)) * 100
        ax.scatter([k], [v], color=GRIP, s=32, zorder=5)
        ax.text(k, v + 4, f'{v:.0f}%', ha='center', fontsize=10, color=INK)
        print(f'[share] {k:,} tokens: {v:.1f} per cent of a layer\'s arithmetic is on pairs')
    ax.set_xscale('log')
    ax.set_ylim(0, 105)
    ax.set_xlabel('tokens in the sequence (log scale)', fontsize=10)
    ax.set_ylabel('share of a layer\'s arithmetic spent on pairs (per cent)', fontsize=10)
    ax.set_title('Short sequences hardly notice attention; long ones are almost nothing else',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'fraction-in-attention.svg')


BUDGET_GIB: float = 24.0        # a stated example: 24 GiB of memory on the accelerator


def cache_fills_memory() -> None:
    free = BUDGET_GIB * GIB - WEIGHT_BYTES
    max_tokens = free / CACHE_PER_TOKEN
    lengths = np.array([1024, 8192, 32768, 131072, 262144], dtype=float)
    held = (WEIGHT_BYTES + lengths * CACHE_PER_TOKEN) / GIB
    print(f'[budget] a stated {BUDGET_GIB:.0f} GiB of memory, weights take '
          f'{WEIGHT_BYTES / GIB:.2f} GiB, so {free / GIB:.2f} GiB is left and one sequence '
          f'can hold at most {max_tokens:,.0f} tokens')
    for n, h in zip(lengths, held):
        print(f'[budget] {n:,.0f} tokens: {h:.2f} GiB held in all')

    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    labels = [f'{int(n):,}' for n in lengths]
    ax.bar(labels, [WEIGHT_BYTES / GIB] * len(lengths), color=LINK, width=0.5,
           label='the weights')
    ax.bar(labels, lengths * CACHE_PER_TOKEN / GIB, bottom=[WEIGHT_BYTES / GIB] * len(lengths),
           color=TEAL, width=0.5, label='the cache for one sequence')
    ax.axhline(BUDGET_GIB, color=GRIP, ls='--', lw=1.6)
    ax.text(-0.45, BUDGET_GIB + 0.8, f'all the memory there is: {BUDGET_GIB:.0f} GiB',
            fontsize=10, color=GRIP)
    for i, h in enumerate(held):
        ax.text(i, h + 0.6, f'{h:.1f}', ha='center', fontsize=9.5, color=INK)
    ax.set_ylim(0, BUDGET_GIB * 1.35)
    ax.set_xlabel('tokens in the one conversation', fontsize=10)
    ax.set_ylabel('memory held (GiB)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title(f'One conversation can hold at most {max_tokens / 1000:,.0f} thousand tokens '
                 'before the memory is gone', fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'cache-fills-memory.svg')


def slower_with_length() -> None:
    lengths = np.arange(0, 131073, 512, dtype=float)
    times = (WEIGHT_BYTES + lengths * CACHE_PER_TOKEN) / BANDWIDTH * 1e3
    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(lengths, times, color=GRIP, lw=2.2)
    for k in (0, 8192, 32768, 131072):
        t = (WEIGHT_BYTES + k * CACHE_PER_TOKEN) / BANDWIDTH * 1e3
        ax.scatter([k], [t], color=GRIP, s=32, zorder=5)
        ax.text(k + 2500, t, f'{t:.2f} ms', fontsize=10, color=INK, va='center')
        print(f'[slower] at {k:,} tokens already said, one more token takes {t:.2f} ms '
              f'({1000 / t:,.0f} tokens a second)')
    ax.set_xticks([0, 32768, 65536, 98304, 131072])
    ax.set_xticklabels(['0', '32,768', '65,536', '98,304', '131,072'])
    ax.set_xlabel('tokens already in the conversation', fontsize=10)
    ax.set_ylabel('time to produce one more token (milliseconds)', fontsize=10)
    ax.set_ylim(0, times.max() * 1.15)
    ax.set_title('Every token the model writes costs more than the one before it',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'slower-with-length.svg')


# ==========================================================================
# section 4: cutting the cost of attention
# ==========================================================================

def _draw_mask(ax: Axes, allowed: NDArray[np.bool_], title: str, colour: str) -> int:
    n = allowed.shape[0]
    for i in range(n):
        for j in range(n):
            on = bool(allowed[i, j])
            ax.add_patch(Rectangle((j, n - 1 - i), 0.92, 0.92,
                                   facecolor=colour if on else '#f1f1f1',
                                   edgecolor='#dddddd', lw=0.7))
    _bare(ax)
    ax.text(-0.9, n / 2, 'position doing the looking', ha='center', va='center',
            fontsize=9.5, color=MUTED, rotation=90)
    ax.set_xlim(-1.6, n + 0.4)
    ax.set_ylim(-1.6, n + 0.4)
    count = int(allowed.sum())
    ax.text(n / 2, -0.75, f'{count} pairs allowed of {n * n}', ha='center', fontsize=10.5,
            color=INK)
    ax.text(n / 2, -1.35, 'position being looked at', ha='center', fontsize=9.5, color=MUTED)
    ax.set_title(title, fontsize=11.5, weight='bold', color=INK)
    return count


def window_mask() -> None:
    n, w = 16, 4
    rows = np.arange(n)[:, None]
    cols = np.arange(n)[None, :]
    full = cols <= rows
    window = full & (rows - cols < w)
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6), facecolor='white')
    a = _draw_mask(axes[0], full, 'Every earlier position', SLIDE)
    b = _draw_mask(axes[1], window, f'Only the last {w} positions', TEAL)
    print(f'[window] {n} positions: full causal {a} pairs, window of {w} {b} pairs, '
          f'which is {b / a * 100:.0f} per cent of them')
    big = 8192
    full_big = big * (big + 1) / 2
    win_big = sum(min(i + 1, 1024) for i in range(big))
    print(f'[window] {big:,} positions with a window of 1,024: {win_big:,} pairs against '
          f'{full_big:,.0f}, which is {win_big / full_big * 100:.1f} per cent')
    fig.suptitle(f'A sliding window keeps {b / a * 100:.0f} per cent of the pairs here, and '
                 f'{win_big / full_big * 100:.0f} per cent at {big:,} tokens',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'window-mask.svg')


def window_reach() -> None:
    layers = np.arange(1, LAYERS + 1)
    windows = [4, 128, 1024]
    colours = [GRIP, WRIST, TEAL]
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    for w, colour in zip(windows, colours):
        reach = 1 + layers * (w - 1)
        ax.plot(layers, reach, marker='o', ms=3.5, color=colour, lw=2,
                label=f'window of {w:,} positions')
        print(f'[window-reach] a window of {w:,} over {LAYERS} layers reaches '
              f'{int(reach[-1]):,} positions back')
    ax.axhline(TRAINED_LEN, color=SLIDE, ls='--', lw=1.6)
    ax.text(1.2, TRAINED_LEN * 1.3, f'the whole {TRAINED_LEN:,}-token context', fontsize=10,
            color=SLIDE)
    ax.set_yscale('log')
    ax.set_ylim(1, 100000)
    ax.set_xlabel('layers stacked', fontsize=10)
    ax.set_ylabel('positions the top layer can be touched by (log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('Stacking windowed layers gets the reach back, one window at a time',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'window-reach.svg')


def sparse_mask() -> None:
    n, w, keep = 16, 3, 2
    rows = np.arange(n)[:, None]
    cols = np.arange(n)[None, :]
    full = cols <= rows
    window = full & (rows - cols < w)
    sparse = window | (full & (cols < keep))
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6), facecolor='white')
    b = _draw_mask(axes[0], window, f'A window of {w}, and nothing else', TEAL)
    c = _draw_mask(axes[1], sparse, f'The same window, plus the first {keep} positions '
                                    'kept for everyone', PURPLE)
    a = int(full.sum())
    print(f'[sparse] {n} positions: full {a}, window of {w} {b}, '
          f'window plus {keep} shared positions {c}')
    fig.suptitle('A sparse pattern: a window for what is near, plus a few positions everyone '
                 'may look at', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'sparse-mask.svg')


def fewer_kv_heads() -> None:
    groups = [16, 4, 1]
    names = ['one key and value\nfor each of the 16 heads', 'four shared groups',
             'one shared pair for\nall 16 heads']
    per_token = [2 * LAYERS * g * HEAD_DIM * NBYTES for g in groups]
    length = 8192
    totals = [p * length / MIB for p in per_token]
    for g, p, t in zip(groups, per_token, totals):
        print(f'[kv-heads] {g} key-value heads: {p:,} bytes a token ({p / 1024:.0f} KiB), '
              f'{t:,.0f} MiB for {length:,} tokens, '
              f'{per_token[0] / p:.0f} times smaller than the full cache')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar(names, [p / 1024 for p in per_token], color=[GRIP, WRIST, SLIDE], width=0.55)
    for i, p in enumerate(per_token):
        ax.text(i, p / 1024 + 2.5, f'{p / 1024:.0f} KiB', ha='center', fontsize=10.5, color=INK)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_ylabel('cache for one token (KiB)', fontsize=10)
    ax.set_ylim(0, per_token[0] / 1024 * 1.2)
    ax.set_title('What one token costs in the cache', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(names, totals, color=[GRIP, WRIST, SLIDE], width=0.55)
    for i, t in enumerate(totals):
        ax.text(i, t * 1.08, f'{t:,.0f} MiB', ha='center', fontsize=10.5, color=INK)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_yscale('log')
    ax.set_ylim(10, totals[0] * 4)
    ax.set_ylabel(f'cache for one {length:,}-token conversation (MiB, log scale)', fontsize=10)
    ax.set_title('And what a whole conversation costs', fontsize=12, weight='bold', color=INK)
    fig.suptitle('Sharing keys and values between heads cuts the cache without changing the '
                 'number of heads that ask', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'fewer-kv-heads.svg')


# ==========================================================================
# section 5: carrying a running summary instead
# ==========================================================================

STATE_SIZE: int = 16        # a stated example: 16 running numbers for each of the 1024 channels


def running_summary() -> None:
    keep = 0.9
    x = np.zeros(18)
    x[2] = 1.0
    x[3] = 0.6
    x[9] = 1.0
    x[14] = 0.4
    h = np.zeros_like(x)
    for t in range(1, len(x)):
        h[t] = keep * h[t - 1] + x[t]
    print(f'[summary] keeping {keep} of the running total and adding the new token: ' +
          ', '.join(f't{t}:{v:.3f}' for t, v in enumerate(h)))
    print(f'[summary] the token at step 2 still counts {keep ** 7:.3f} at step 9 and '
          f'{keep ** 15:.3f} at step 17')

    fig, ax = plt.subplots(figsize=(11.4, 5.0), facecolor='white')
    _plain(ax)
    ax.bar(np.arange(len(x)), x, color=LINK_PALE, edgecolor=LINK, width=0.5,
           label='what arrives at this position')
    ax.plot(np.arange(len(x)), h, color=PURPLE, marker='o', lw=2,
            label='the running summary carried forward')
    for t in (2, 9, 14):
        ax.annotate('', xy=(t, h[t]), xytext=(t, x[t] + 0.12),
                    arrowprops={'arrowstyle': '->', 'color': MUTED, 'lw': 1.0})
    ax.text(9.6, 0.42, f'the summary keeps {keep * 100:.0f} per cent of itself each step,\n'
                       'then adds whatever the new token brings', fontsize=10, color=PURPLE)
    ax.set_xticks(np.arange(len(x)))
    ax.set_xlabel('position in the sentence', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper right')
    ax.set_title('A state-space layer: one running summary, updated once per token',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'running-summary.svg')


def cost_per_token_flat() -> None:
    pos = np.arange(1, 32769)
    attn = 4.0 * LAYERS * WIDTH * pos                 # reading every earlier key and value
    ssm = np.full_like(pos, 4.0 * LAYERS * WIDTH * STATE_SIZE, dtype=float)
    cache = pos * CACHE_PER_TOKEN / MIB
    state = np.full_like(pos, LAYERS * WIDTH * STATE_SIZE * NBYTES / MIB, dtype=float)
    print(f'[flat] state-space work for one token: {ssm[0]:,.0f} operations at every position')
    for k in (1024, 8192, 32768):
        print(f'[flat] at position {k:,}: attention does {attn[k - 1]:,.0f} operations and '
              f'holds {cache[k - 1]:,.1f} MiB; the state-space layer does {ssm[0]:,.0f} and '
              f'holds {state[0]:.2f} MiB')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(pos, attn / 1e6, color=GRIP, lw=2, label='attention: reads every earlier position')
    ax.plot(pos, ssm / 1e6, color=PURPLE, lw=2, label='state-space: reads one running summary')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('how many tokens have gone before (log scale)', fontsize=10)
    ax.set_ylabel('millions of operations for the next token (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Work for one more token', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.plot(pos, cache, color=GRIP, lw=2, label='the key-value cache')
    ax.plot(pos, state, color=PURPLE, lw=2,
            label=f'the running summary ({STATE_SIZE} numbers a channel)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('tokens in the conversation (log scale)', fontsize=10)
    ax.set_ylabel('memory for one conversation (MiB, log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Memory for the conversation so far', fontsize=12, weight='bold', color=INK)
    fig.suptitle('The whole trade: the state-space layer pays the same for its ten thousandth '
                 'token as for its first', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'what-the-summary-buys.svg')


def what_it_gives_up() -> None:
    k = np.arange(1, 1001)
    factors = [0.90, 0.98, 0.999]
    colours = [GRIP, WRIST, PURPLE]
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for f, colour in zip(factors, colours):
        ax.plot(k, f ** k, color=colour, lw=2, label=f'keeps {f} of the summary each step')
        print(f'[gives-up] keeping {f} a step: the token 200 back counts {f ** 200:.2e}, '
              f'the token 1,000 back counts {f ** 1000:.2e}')
    ax.axhline(1.0, color=SLIDE, lw=2.5)
    ax.text(30, 1.5, 'attention can give any one earlier token any weight it likes',
            fontsize=10, color=SLIDE)
    ax.set_yscale('log')
    ax.set_ylim(1e-12, 30)
    ax.set_xlabel('how many tokens back', fontsize=10)
    ax.set_ylabel('weight that token still has (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('How much of an old token is left', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    far = [f ** 1000 for f in factors]
    sep = [1.0 - f for f in factors]
    floor = 1e-10
    x = np.arange(len(factors))
    ax.bar(x - 0.19, [max(v, floor) for v in far], width=0.36, color=TEAL,
           label='weight left on the token 1,000 back')
    ax.bar(x + 0.19, sep, width=0.36, color=WRIST,
           label='difference in weight between two next-door tokens')
    for i, (a, b) in enumerate(zip(far, sep)):
        shown = f'{a:.1e}' if a >= floor else 'below 1e-10'
        ax.text(i - 0.19, max(a, floor) * 2.2, shown, ha='center', fontsize=9, color=INK)
        ax.text(i + 0.19, b * 2.2, f'{b:.3f}', ha='center', fontsize=9, color=INK)
        print(f'[gives-up] keeping {factors[i]} a step: weight on the token 1,000 back '
              f'{a:.2e}, and two next-door tokens differ by only {b:.3f}')
    ax.set_xticks(x)
    ax.set_xticklabels([f'keeps {f}' for f in factors])
    ax.set_yscale('log')
    ax.set_ylim(floor, 200)
    ax.set_ylabel('log scale', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Forget slowly and two tokens look alike; forget fast and the old ones go',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('What the running summary gives up: it cannot reach back and pick out one '
                 'token', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'what-it-gives-up.svg')


def hybrid_memory() -> None:
    attn_layers = 3
    lengths = np.array([1024, 8192, 32768, 131072], dtype=float)
    full = lengths * CACHE_PER_TOKEN / MIB
    hybrid_cache = lengths * (2 * attn_layers * HEADS * HEAD_DIM * NBYTES) / MIB
    state_bytes = (LAYERS - attn_layers) * WIDTH * STATE_SIZE * NBYTES / MIB
    hybrid = hybrid_cache + state_bytes
    print(f'[hybrid] {attn_layers} attention layers of {LAYERS}: cache '
          f'{2 * attn_layers * HEADS * HEAD_DIM * NBYTES:,} bytes a token, plus a fixed '
          f'{state_bytes:.2f} MiB of running summaries')
    for n, f, h in zip(lengths, full, hybrid):
        print(f'[hybrid] {n:,.0f} tokens: every layer attention {f:,.0f} MiB, '
              f'hybrid {h:,.1f} MiB, which is {f / h:.1f} times smaller')

    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(len(lengths))
    ax.bar(x - 0.19, full, width=0.36, color=GRIP, label=f'attention in all {LAYERS} layers')
    ax.bar(x + 0.19, hybrid, width=0.36, color=PURPLE,
           label=f'attention in {attn_layers} layers, running summaries in the other '
                 f'{LAYERS - attn_layers}')
    for i, (f, h) in enumerate(zip(full, hybrid)):
        ax.text(i - 0.19, f * 1.12, f'{f:,.0f}', ha='center', fontsize=9.5, color=INK)
        ax.text(i + 0.19, h * 1.12, f'{h:,.0f}', ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(n):,}' for n in lengths])
    ax.set_yscale('log')
    ax.set_ylim(10, full[-1] * 4)
    ax.set_xlabel('tokens in the conversation', fontsize=10)
    ax.set_ylabel('memory for one conversation (MiB, log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    ax.set_title(f'A hybrid stack holds {full[-1] / hybrid[-1]:.0f} times less at '
                 f'{int(lengths[-1]):,} tokens, and can still reach back exactly '
                 f'{attn_layers} times', fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'hybrid-memory.svg')


# ==========================================================================
# section 6: what is still open
# ==========================================================================

def where_the_time_goes() -> None:
    prompt, answer = 8192, 256
    prefill_flops = 2.0 * P_MATMUL * prompt + LAYERS * _pair_work(float(prompt))
    prefill_bytes = WEIGHT_BYTES + prompt * CACHE_PER_TOKEN
    t_prefill = max(prefill_flops / PEAK_FLOPS, prefill_bytes / BANDWIDTH)
    gen_times = [(WEIGHT_BYTES + (prompt + t) * CACHE_PER_TOKEN) / BANDWIDTH
                 for t in range(answer)]
    t_gen = float(np.sum(gen_times))
    print(f'[time] reading a {prompt:,}-token prompt: {prefill_flops:,.0f} operations and '
          f'{prefill_bytes:,.0f} bytes, so {t_prefill * 1e3:.0f} ms, which is '
          f'{t_prefill / prompt * 1e6:.1f} microseconds a token')
    print(f'[time] writing {answer} tokens of answer: {t_gen * 1e3:.0f} ms, which is '
          f'{t_gen / answer * 1e6:,.0f} microseconds a token')
    print(f'[time] a token of answer costs {(t_gen / answer) / (t_prefill / prompt):.0f} times '
          'as much as a token of prompt')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar([f'reading the\n{prompt:,}-token prompt', f'writing the\n{answer}-token answer'],
           [t_prefill * 1e3, t_gen * 1e3], color=[LINK, GRIP], width=0.5)
    ax.text(0, t_prefill * 1e3 + 10, f'{t_prefill * 1e3:.0f} ms', ha='center', fontsize=11,
            color=INK)
    ax.text(1, t_gen * 1e3 + 10, f'{t_gen * 1e3:.0f} ms', ha='center', fontsize=11, color=INK)
    ax.set_ylim(0, t_gen * 1e3 * 1.25)
    ax.set_ylabel('time (milliseconds)', fontsize=10)
    ax.set_title('Where the waiting happens', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    per = [t_prefill / prompt * 1e6, t_gen / answer * 1e6]
    ax.bar(['a token of prompt', 'a token of answer'], per, color=[LINK, GRIP], width=0.5)
    for i, v in enumerate(per):
        ax.text(i, v * 1.3, f'{v:,.1f} microseconds', ha='center', fontsize=11, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, per[1] * 6)
    ax.set_ylabel('time for one token (microseconds, log scale)', fontsize=10)
    ax.set_title(f'A token of answer costs {per[1] / per[0]:.0f} times as much as a token '
                 'of prompt', fontsize=12, weight='bold', color=INK)
    fig.suptitle('The prompt is read in one wide pass; the answer is written one narrow token '
                 'at a time', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'where-the-time-goes.svg')


def how_many_conversations_fit() -> None:
    free = BUDGET_GIB * GIB - WEIGHT_BYTES
    lengths = [2048, 8192, 32768, 131072]
    full = [max(int(free // (CACHE_PER_TOKEN * n)), 0) for n in lengths]
    grouped = [max(int(free // (CACHE_PER_TOKEN // 4 * n)), 0) for n in lengths]
    for n, a, b in zip(lengths, full, grouped):
        print(f'[fit] {n:,} tokens each: {a} conversations fit in {BUDGET_GIB:.0f} GiB with a '
              f'full cache, and {b} with four shared key-value groups')

    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(len(lengths))
    ax.bar(x - 0.19, full, width=0.36, color=GRIP, label='one key and value for each head')
    ax.bar(x + 0.19, grouped, width=0.36, color=SLIDE, label='four shared key-value groups')
    for i, (a, b) in enumerate(zip(full, grouped)):
        ax.text(i - 0.19, a * 1.15 + 0.3, str(a), ha='center', fontsize=10, color=INK)
        ax.text(i + 0.19, b * 1.15 + 0.3, str(b), ha='center', fontsize=10, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{n:,}' for n in lengths])
    ax.set_yscale('log')
    ax.set_ylim(0.7, max(grouped) * 4)
    ax.set_xlabel('tokens in each conversation', fontsize=10)
    ax.set_ylabel('conversations that fit at once (log scale)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper right')
    ax.set_title(f'How many conversations fit beside the weights in {BUDGET_GIB:.0f} GiB',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, WHY_DOC, 'how-many-conversations-fit.svg')


def three_designs() -> None:
    length, window, keep = 32768, 1024, 0.98
    full_mem = length * CACHE_PER_TOKEN / MIB
    win_mem = window * CACHE_PER_TOKEN / MIB
    ssm_mem = LAYERS * WIDTH * STATE_SIZE * NBYTES / MIB
    names = ['attention over\neverything', f'attention over the\nlast {window:,}',
             'a running summary']
    mems = [full_mem, win_mem, ssm_mem]
    for nm, m in zip(names, mems):
        print(f'[designs] {nm.replace(chr(10), " ")}: {m:,.2f} MiB for a '
              f'{length:,}-token conversation')
    far = keep ** 4000
    print(f'[designs] weight one layer can put on the token 4,000 back: attention up to 1, '
          f'a window of {window:,} exactly 0, a summary keeping {keep} a step {far:.1e}')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar(names, mems, color=[GRIP, WRIST, PURPLE], width=0.55)
    for i, m in enumerate(mems):
        ax.text(i, m * 1.4, f'{m:,.2f} MiB', ha='center', fontsize=10.5, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(0.2, full_mem * 8)
    ax.tick_params(axis='x', labelsize=9.5)
    ax.set_ylabel(f'memory for a {length:,}-token conversation (MiB, log scale)', fontsize=10)
    ax.set_title('What each design holds', fontsize=12, weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    k = np.arange(1, 4001)
    ax.plot(k, np.ones_like(k, dtype=float), color=GRIP, lw=2.5,
            label='attention over everything')
    win_curve = np.where(k <= window, 1.0, np.nan)
    ax.plot(k, win_curve, color=WRIST, lw=2.5, ls='--',
            label=f'attention over the last {window:,}')
    ax.plot(k, keep ** k, color=PURPLE, lw=2, label=f'a running summary keeping {keep}')
    ax.axvline(window, color=WRIST, ls=':', lw=1.2)
    ax.text(window * 1.1, 1e-6, f'past {window:,} tokens this layer\nsees nothing at all',
            fontsize=9.5, color=WRIST)
    ax.set_yscale('log')
    ax.set_ylim(1e-12, 30)
    ax.set_xlabel('how many tokens back', fontsize=10)
    ax.set_ylabel('weight one layer can put on that token (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('What each design can still reach', fontsize=12, weight='bold', color=INK)
    fig.suptitle('Nobody has a design that is cheap in memory and can still pick out one '
                 'token from far back', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WHY_DOC, 'three-designs.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    print_config()
    # 03_training-and-running-a-transformer.md
    signals_per_sentence()
    per_position_loss()
    one_position_distribution()
    signals_per_thousand_tokens()
    causal_mask_grid()
    scores_before_after_mask()
    what_the_mask_stops()
    teacher_forcing()
    errors_compound()
    training_memory()
    generation_steps()
    cache_saves_work()
    cache_size_arithmetic()
    cache_versus_weights()
    logits_to_probabilities()
    three_temperatures()
    top_p_cut()
    greedy_loses()
    context_cost()
    past_the_window()
    memory_bound()
    batch_helps()
    # 04_why-the-transformer-won.md
    layers_to_reach()
    receptive_cone()
    dilation_helps()
    sequential_steps()
    hardware_busy()
    signal_decay()
    attention_overtakes()
    fraction_in_attention()
    cache_fills_memory()
    slower_with_length()
    window_mask()
    window_reach()
    sparse_mask()
    fewer_kv_heads()
    running_summary()
    cost_per_token_flat()
    what_it_gives_up()
    hybrid_memory()
    where_the_time_goes()
    how_many_conversations_fit()
    three_designs()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
