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
    ax.text(s.mean_loss + 0.05, len(s.targets) - 0.45, f'average {s.mean_loss:.2f}',
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
        ax.set_ylim(0, 0.95)
        ax.text(tgt, p[tgt] + 0.03, f'{p[tgt]:.3f}', ha='center', fontsize=10, color=SLIDE,
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
    _matrix(axes[0], a.scores, labels, labels, fmt='{:+.2f}', cmap='PuOr',
            vmin=-float(np.abs(a.scores).max()), vmax=float(np.abs(a.scores).max()),
            text_cut=2.0)
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
        ax.text(x + w / 2, 1.40, 'scored against', ha='center', va='center', fontsize=7.5,
                color=MUTED)
        if i < len(s.targets) - 1:
            _arrow(ax, x + w + 0.03, 3.4, x + 1.72, 3.4, colour=LINK, head=0.1)
    ax.text(0.1, 3.4, 'fed in: the true token,\nalways', ha='right', va='center',
            fontsize=10, color=LINK, weight='bold')
    ax.text(0.1, 2.05, "the model's own best\nguess", ha='right', va='center', fontsize=10,
            color=INK, weight='bold')
    ax.text(0.1, 0.7, 'the true next token', ha='right', va='center', fontsize=10,
            color=INK, weight='bold')
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
