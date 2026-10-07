"""Generate the diagrams for the first two pages of docs/05_neural-networks/06_the-transformer/.

    01_attention.md            -> images/the-transformer/attention/
    02_a-transformer-block.md  -> images/the-transformer/a-transformer-block/

Run with:  python3 the_transformer_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so the two documents can quote the same values.

What is simulated: the small four-token example is made of numbers drawn by
numpy.random.default_rng(28) and rounded to one decimal place, so the weight
matrices are random rather than trained, and the attention pattern they give
carries no meaning; only the arithmetic is real. The head-size experiment, the
deep-stack experiment that compares pre-norm with post-norm, the per-block
contribution sizes and the expert load counts are also simulated with seeded
generators. Everything about parameter counts, multiply-add counts and memory
sizes is exact arithmetic on the stated model shapes, not simulation.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle  # noqa: E402
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

ATT_DOC: str = 'attention'
BLK_DOC: str = 'a-transformer-block'

Arr = NDArray[np.float64]

TOKENS: list[str] = ['pick', 'up', 'the', 'cube']


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
    ax.set_axis_off()
    ax.set_aspect('equal')


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


_ERF = np.vectorize(math.erf)


def _gelu(x: Arr) -> Arr:
    return 0.5 * x * (1.0 + _ERF(x / math.sqrt(2.0)))


def _mix(colour: str, v: float) -> tuple[float, float, float]:
    """Blend a colour towards white; v = 0 is white, v = 1 is the colour itself."""
    r, g, b = matplotlib.colors.to_rgb(colour)
    v = float(np.clip(v, 0.0, 1.0))
    return (1 - v + v * r, 1 - v + v * g, 1 - v + v * b)


def _signed(v: float, vmax: float) -> tuple[float, float, float]:
    """Pale blue for a positive number, pale orange for a negative one."""
    if vmax <= 0:
        return (1.0, 1.0, 1.0)
    return _mix(LINK if v >= 0 else WRIST, 0.75 * abs(v) / vmax)


def _grid(ax: Axes, M: Arr, x0: float = 0.0, y0: float = 0.0,
          cw: float = 1.0, ch: float = 0.62, fmt: str = '{:+.2f}',
          rows: list[str] | None = None, cols: list[str] | None = None,
          title: str | None = None, colour: str | None = None,
          vmax: float | None = None, fontsize: float = 9.5,
          rowsize: float = 9.5, box: str | None = None,
          mask: NDArray[np.bool_] | None = None) -> tuple[float, float]:
    """Draw a matrix of numbers as a grid of shaded cells.

    The top-left cell sits at (x0, y0) and the grid grows right and down.
    Returns the (width, height) the grid takes up. With colour=None the cells
    are shaded blue for positive numbers and orange for negative ones; with a
    colour given they are shaded from white to that colour by size.
    """
    M = np.atleast_2d(np.asarray(M, dtype=float))
    nr, nc = M.shape
    big = float(np.abs(M).max()) if vmax is None else vmax
    for i in range(nr):
        for j in range(nc):
            if mask is not None and mask[i, j]:
                face = _mix(MUTED, 0.30)
                txt = '-inf'
            else:
                face = _signed(M[i, j], big) if colour is None else _mix(colour, M[i, j] / big if big else 0)
                txt = fmt.format(M[i, j])
            ax.add_patch(Rectangle((x0 + j * cw, y0 - (i + 1) * ch), cw, ch,
                                   facecolor=face, edgecolor=GRID, lw=0.8))
            ax.text(x0 + (j + 0.5) * cw, y0 - (i + 0.5) * ch, txt, ha='center',
                    va='center', fontsize=fontsize, color=INK)
    if rows is not None:
        for i, lab in enumerate(rows):
            ax.text(x0 - 0.12, y0 - (i + 0.5) * ch, lab, ha='right', va='center',
                    fontsize=rowsize, color=INK)
    if cols is not None:
        for j, lab in enumerate(cols):
            ax.text(x0 + (j + 0.5) * cw, y0 + 0.10, lab, ha='center', va='bottom',
                    fontsize=rowsize, color=MUTED)
    if title is not None:
        ax.text(x0 + nc * cw / 2, y0 + (0.46 if cols is not None else 0.14), title,
                ha='center', va='bottom', fontsize=10.5, color=INK, weight='bold')
    if box is not None:
        ax.add_patch(Rectangle((x0, y0 - nr * ch), nc * cw, nr * ch, facecolor='none',
                               edgecolor=box, lw=1.8))
    return nc * cw, nr * ch


def _lines(ax: Axes, x: float, y: float, text: list[str], size: float = 9.5,
           colour: str = INK, dy: float = 0.30, ha: str = 'left') -> float:
    """Write monospace lines downwards from (x, y); returns the y it stopped at."""
    for k, line in enumerate(text):
        ax.text(x, y - k * dy, line, ha=ha, va='center', fontsize=size,
                color=colour, family='monospace')
    return y - (len(text) - 1) * dy


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = MUTED, lw: float = 1.4, label: str | None = None,
           size: float = 9.0, labelpos: float = 0.5, dy: float = 0.16) -> None:
    ax.add_patch(FancyArrow(x0, y0, x1 - x0, y1 - y0, width=0.004 * lw,
                            head_width=0.11, head_length=0.14, length_includes_head=True,
                            facecolor=colour, edgecolor=colour))
    if label is not None:
        ax.text(x0 + labelpos * (x1 - x0), y0 + labelpos * (y1 - y0) + dy, label,
                ha='center', va='bottom', fontsize=size, color=colour)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, size: float = 10.0,
         weight: str = 'normal', lw: float = 1.3) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                                facecolor=face, edgecolor=edge, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size,
            color=INK, weight=weight)


def _title(fig: Figure, text: str) -> None:
    fig.suptitle(text, fontsize=12, weight='bold', color=INK, y=0.99)


def _fit(fig: Figure, ax: Axes, room: float = 0.42) -> None:
    """Shrink a drawing figure to the shape of what was drawn, leaving room above.

    The drawings use an equal aspect ratio, so a figure whose height does not
    match the data leaves a band of white between the title and the picture.
    """
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    w = fig.get_size_inches()[0]
    h = max(w * (y1 - y0) / (x1 - x0) + room, 1.4)
    fig.set_size_inches(w, h)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0 - room / h)


# --------------------------------------------------------------------------
# the small four-token example, worked out once
# --------------------------------------------------------------------------

class Toy:
    """The four-token, four-number attention example used by both pages.

    X holds one row per token. The three projection matrices are random, so
    the pattern they produce means nothing; the arithmetic is what matters.
    All of X and the matrices are rounded to one decimal place, which makes Q,
    K and V land exactly on two decimal places so a reader can check them.
    """

    def __init__(self) -> None:
        rng = np.random.default_rng(28)
        self.X: Arr = np.round(rng.normal(0.0, 0.9, (4, 4)), 1)
        self.WQ: Arr = np.round(rng.normal(0.0, 0.6, (4, 4)), 1)
        self.WK: Arr = np.round(rng.normal(0.0, 0.6, (4, 4)), 1)
        self.WV: Arr = np.round(rng.normal(0.0, 0.6, (4, 4)), 1)
        self.WO: Arr = np.round(rng.normal(0.0, 0.6, (4, 4)), 1)
        self.W1: Arr = np.round(rng.normal(0.0, 0.5, (4, 16)), 1)
        self.W2: Arr = np.round(rng.normal(0.0, 0.5, (16, 4)), 1)

        self.Q: Arr = self.X @ self.WQ
        self.K: Arr = self.X @ self.WK
        self.V: Arr = self.X @ self.WV
        self.raw: Arr = self.Q @ self.K.T
        self.dk: int = 4
        self.scaled: Arr = self.raw / math.sqrt(self.dk)
        self.A: Arr = _softmax(self.scaled)
        self.O: Arr = self.A @ self.V
        self.OW: Arr = self.O @ self.WO

        # two heads of size two, cut out of the same three matrices
        self.heads: list[dict[str, Arr]] = []
        for h in range(2):
            sl = slice(2 * h, 2 * h + 2)
            q, k, v = self.Q[:, sl], self.K[:, sl], self.V[:, sl]
            s = q @ k.T / math.sqrt(2)
            a = _softmax(s)
            self.heads.append({'q': q, 'k': k, 'v': v, 's': s, 'a': a, 'o': a @ v})
        self.cat: Arr = np.concatenate([h['o'] for h in self.heads], axis=1)
        self.two_head_out: Arr = self.cat @ self.WO

        # one row with the last key forbidden by a mask
        row = self.scaled[1].copy()
        row[3] = -np.inf
        self.masked_row: Arr = _softmax(row)


TOY = Toy()


def report_toy() -> None:
    np.set_printoptions(suppress=True, linewidth=150)
    t = TOY
    print('[toy] tokens          ', TOKENS)
    print('[toy] X\n', t.X)
    print('[toy] WQ\n', t.WQ)
    print('[toy] WK\n', t.WK)
    print('[toy] WV\n', t.WV)
    print('[toy] WO\n', t.WO)
    print('[toy] Q (= X @ WQ)\n', np.round(t.Q, 2))
    print('[toy] K\n', np.round(t.K, 2))
    print('[toy] V\n', np.round(t.V, 2))
    print('[toy] raw scores (exact)\n', np.round(t.raw, 4))
    print('[toy] raw scores (2dp)\n', np.round(t.raw, 2))
    print('[toy] scaled = raw / sqrt(4) = raw / 2\n', np.round(t.scaled, 2))
    print('[toy] weights (3dp)\n', np.round(t.A, 3))
    print('[toy] weight row sums', np.round(t.A.sum(axis=1), 6))
    print('[toy] output O = A @ V\n', np.round(t.O, 2))
    print('[toy] O @ WO\n', np.round(t.OW, 2))
    for h, d in enumerate(TOY.heads):
        print(f'[toy] head {h + 1} scaled scores\n', np.round(d['s'], 2))
        print(f'[toy] head {h + 1} weights\n', np.round(d['a'], 3))
        print(f'[toy] head {h + 1} output\n', np.round(d['o'], 2))
    print('[toy] joined head outputs\n', np.round(TOY.cat, 2))
    print('[toy] two-head result after WO\n', np.round(TOY.two_head_out, 2))
    print('[toy] row 2 with key 4 forbidden ->', np.round(TOY.masked_row, 3))
    r4 = TOY.scaled[3]
    print('[toy] row 4 scaled', np.round(r4, 2), 'exp', np.round(np.exp(r4), 3),
          'sum', round(float(np.exp(r4).sum()), 3))
    r2 = TOY.scaled[1]
    print('[toy] row 2 scaled', np.round(r2, 2), 'exp', np.round(np.exp(r2), 3),
          'sum', round(float(np.exp(r2).sum()), 3))


def _thick_arrow(ax: Axes, p0: tuple[float, float], p1: tuple[float, float],
                 lw: float, colour: str = LINK, alpha: float = 1.0) -> None:
    ax.annotate('', xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle='-|>', lw=lw, color=colour,
                                alpha=alpha, shrinkA=2, shrinkB=2))


# --------------------------------------------------------------------------
# 01_attention.md, section 1: what one token needs from the others
# --------------------------------------------------------------------------

def token_vectors() -> None:
    cols = ['number 1', 'number 2', 'number 3', 'number 4']
    fig, ax = plt.subplots(figsize=(8.2, 2.9), facecolor='white')
    _blank(ax)
    w, h = _grid(ax, TOY.X, cw=1.55, ch=0.72, rows=[f'"{t}"' for t in TOKENS], cols=cols)
    ax.set_xlim(-1.6, w + 0.3)
    ax.set_ylim(-h - 0.35, 0.55)
    _fit(fig, ax)
    _title(fig, 'Four tokens, each one a list of four numbers')
    _save(fig, ATT_DOC, 'token-vectors.svg')


def one_token_draws_from_four() -> None:
    wts = TOY.A[3]
    fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor='white')
    _blank(ax)
    ys = [2.4, 1.6, 0.8, 0.0]
    for i, (tok, y) in enumerate(zip(TOKENS, ys)):
        _box(ax, 0.0, y - 0.22, 1.5, 0.52, f'"{tok}"', face=_mix(LINK, 0.14), size=10.5)
        _thick_arrow(ax, (1.55, y + 0.04), (5.45, 1.26), lw=0.6 + 9.0 * wts[i],
                     colour=TEAL, alpha=0.85)
        f = 0.38
        ax.text(1.55 + f * 3.9, y + 0.04 + f * (1.26 - y - 0.04) + 0.07,
                f'{wts[i]:.3f}', ha='center', va='bottom', fontsize=10.5, color=INK)
    _box(ax, 5.5, 1.0, 2.9, 0.56, 'new vector for "cube"', face=_mix(JOINT, 0.18), size=10.5)
    ax.text(2.2, -0.65, 'the four numbers add up to '
            f'{wts.sum():.3f}, so the new vector is an average of the four value vectors',
            ha='center', va='center', fontsize=10, color=MUTED)
    ax.set_xlim(-0.3, 8.7)
    ax.set_ylim(-1.0, 3.1)
    _fit(fig, ax)
    _title(fig, 'One token mixes the other three in fixed proportions')
    _save(fig, ATT_DOC, 'one-token-draws-from-four.svg')


def before_and_after() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 3.4), facecolor='white')
    _blank(ax)
    rows = [f'"{t}"' for t in TOKENS]
    w1, h1 = _grid(ax, TOY.X, x0=0.0, cw=1.05, ch=0.66, rows=rows,
                   title='before: each token on its own')
    diff = np.abs(TOY.O - TOY.X).mean(axis=1, keepdims=True)
    w2, _ = _grid(ax, TOY.O, x0=w1 + 1.3, cw=1.05, ch=0.66,
                  title='after: the mixed vectors')
    _grid(ax, diff, x0=w1 + 1.3 + w2 + 0.7, cw=1.4, ch=0.66, colour=PURPLE,
          fmt='{:.2f}', cols=['size of change'],
          title=None)
    ax.text(w1 + 0.65, -h1 / 2, 'attention', ha='center', va='center', fontsize=10,
            color=MUTED, rotation=90)
    print('[toy] size of the change per token', np.round(diff.ravel(), 3))
    ax.set_xlim(-1.5, w1 + 1.3 + w2 + 0.7 + 1.5)
    ax.set_ylim(-h1 - 0.5, 0.85)
    _fit(fig, ax)
    _title(fig, 'What attention changes: every token is replaced by a mix')
    _save(fig, ATT_DOC, 'before-and-after.svg')


def same_token_two_sentences() -> None:
    """The embedding table gives one token the same numbers in any sentence."""
    vec = TOY.X[3]
    left = ['a', 'cube', 'of', 'ice']
    right = ['a', 'wooden', 'cube']
    fig, ax = plt.subplots(figsize=(10.2, 3.6), facecolor='white')
    _blank(ax)
    for row, (words, y) in enumerate(((left, 0.0), (right, -2.1))):
        x = 0.0
        for word in words:
            hit = word == 'cube'
            _box(ax, x, y - 0.5, 1.5, 0.55, word,
                 face=_mix(LINK, 0.22) if hit else 'white',
                 edge=LINK if hit else GRID, size=10.5,
                 weight='bold' if hit else 'normal')
            if hit:
                _arrow(ax, x + 0.75, y - 0.58, x + 0.75, y - 1.0, colour=LINK, lw=1.2)
                _grid(ax, vec.reshape(1, 4), x0=x + 0.75 - 2.0, y0=y - 1.05,
                      cw=1.0, ch=0.58, fmt='{:+.1f}')
            x += 1.7
        ax.text(-0.25, y - 0.22, f'sentence {row + 1}', ha='right', va='center',
                fontsize=10, color=MUTED)
    ax.text(3.6, -3.95, 'the same four numbers both times',
            ha='center', va='top', fontsize=10.5, color=INK)
    ax.set_xlim(-2.4, 7.3)
    ax.set_ylim(-4.45, 0.4)
    _fit(fig, ax)
    _title(fig, 'The embedding table cannot tell the two sentences apart')
    _save(fig, ATT_DOC, 'same-token-two-sentences.svg')


def _conv_weights() -> Arr:
    """Fixed three-wide mixing weights, the same pattern on every row."""
    base = np.array([0.25, 0.50, 0.25])
    W = np.zeros((4, 4))
    for i in range(4):
        for k, off in enumerate((-1, 0, 1)):
            j = i + off
            if 0 <= j < 4:
                W[i, j] = base[k]
    return W / W.sum(axis=1, keepdims=True)


def convolution_weight_grid() -> None:
    """The rejected alternative: weights fixed by position, not by content."""
    W = _conv_weights()
    print('[conv] fixed three-wide mixing weights\n', np.round(W, 3))
    fig, ax = plt.subplots(figsize=(8.6, 3.5), facecolor='white')
    _blank(ax)
    rows = [f'new "{t}"' for t in TOKENS]
    cols = [f'old "{t}"' for t in TOKENS]
    w, h = _grid(ax, W, cw=1.3, ch=0.72, fmt='{:.3f}', rows=rows, cols=cols,
                 colour=WRIST, vmax=1.0)
    ax.text(w / 2, -h - 0.25, 'the same pattern on every row, moved one place along',
            ha='center', va='top', fontsize=10, color=INK)
    ax.set_xlim(-2.0, w + 0.3)
    ax.set_ylim(-h - 0.72, 0.62)
    _fit(fig, ax)
    _title(fig, 'A convolution fixes its weights by position before it sees the words')
    _save(fig, ATT_DOC, 'convolution-weight-grid.svg')


# --------------------------------------------------------------------------
# section 2: query, key and value
# --------------------------------------------------------------------------

def projection_matrices() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 3.1), facecolor='white')
    _blank(ax)
    x = 0.0
    for name, M, col in (('W_query', TOY.WQ, 'query'), ('W_key', TOY.WK, 'key'),
                         ('W_value', TOY.WV, 'value')):
        w, h = _grid(ax, M, x0=x, cw=1.0, ch=0.62, fmt='{:+.1f}',
                     title=f'{name}  (4 rows, 4 columns)')
        ax.text(x + w / 2, -h - 0.25, f'turns a token into its {col} vector',
                ha='center', va='top', fontsize=9.5, color=MUTED)
        x += w + 1.0
    ax.set_xlim(-0.4, x - 0.6)
    ax.set_ylim(-h - 0.9, 0.85)
    _fit(fig, ax)
    _title(fig, 'Three learned matrices, 16 numbers each, shared by every token')
    _save(fig, ATT_DOC, 'projection-matrices.svg')


def one_query_worked_out() -> None:
    x4 = TOY.X[3]
    fig, ax = plt.subplots(figsize=(11.0, 4.3), facecolor='white')
    _blank(ax)
    w, h = _grid(ax, x4.reshape(1, 4), x0=0.0, cw=1.0, ch=0.62, fmt='{:+.1f}',
                 rows=['"cube"'], title='the token')
    x = 0.0
    for j in range(4):
        col = TOY.WQ[:, j]
        terms = [f'{a:+.1f} x {b:+.1f} = {a * b:+.2f}' for a, b in zip(x4, col)]
        total = float(x4 @ col)
        _lines(ax, x, -1.55, [f'query number {j + 1}'] + terms +
               ['-' * 19, f'            = {total:+.2f}'], size=9.0)
        x += 2.85
    _grid(ax, TOY.Q[3].reshape(1, 4), x0=0.0, y0=-3.95, cw=2.85, ch=0.7,
          fmt='{:+.2f}', rows=['query for "cube"'], rowsize=10.0)
    ax.set_xlim(-2.6, 11.5)
    ax.set_ylim(-4.9, 0.9)
    _fit(fig, ax)
    _title(fig, 'One token times one matrix: four multiply-and-add sums')
    _save(fig, ATT_DOC, 'one-query-worked-out.svg')


def qkv_grids() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 3.2), facecolor='white')
    _blank(ax)
    rows = [f'"{t}"' for t in TOKENS]
    x = 0.0
    for name, M in (('Q: the queries', TOY.Q), ('K: the keys', TOY.K),
                    ('V: the values', TOY.V)):
        w, h = _grid(ax, M, x0=x, cw=1.08, ch=0.64, rows=rows if x == 0 else None,
                     title=name)
        x += w + 1.1
    ax.set_xlim(-1.5, x - 0.8)
    ax.set_ylim(-h - 0.4, 0.85)
    _fit(fig, ax)
    _title(fig, 'Every token gets three vectors of its own')
    _save(fig, ATT_DOC, 'qkv-grids.svg')


def query_meets_key() -> None:
    """The three jobs for one pair: "cube" asks, "pick" offers, "pick" gives."""
    ask, give = 3, 0
    score = float(TOY.raw[ask, give])
    weight = float(TOY.A[ask, give])
    print(f'[pair] query of "{TOKENS[ask]}" against key of "{TOKENS[give]}": '
          f'raw {score:.4f}, divided {score / 2:.4f}, weight {weight:.3f}')
    fig, ax = plt.subplots(figsize=(10.8, 4.2), facecolor='white')
    _blank(ax)
    ax.text(1.1, 0.34, f'"{TOKENS[ask]}" is asking', ha='center', va='bottom',
            fontsize=10.5, color=LINK, weight='bold')
    _grid(ax, TOY.Q[ask].reshape(1, 4), x0=0.0, y0=0.0, cw=0.55, ch=0.55,
          fmt='{:+.2f}', fontsize=8.0, rows=['query'], rowsize=9.5)
    ax.text(6.9, 0.34, f'"{TOKENS[give]}" is offering', ha='center', va='bottom',
            fontsize=10.5, color=TEAL, weight='bold')
    _grid(ax, TOY.K[give].reshape(1, 4), x0=5.8, y0=0.0, cw=0.55, ch=0.55,
          fmt='{:+.2f}', fontsize=8.0, rows=['key'], rowsize=9.5)
    _arrow(ax, 2.3, -0.28, 3.3, -0.28, colour=MUTED, lw=1.2)
    _arrow(ax, 5.0, -0.28, 4.1, -0.28, colour=MUTED, lw=1.2)
    ax.text(3.7, -0.12, 'dot product', ha='center', va='bottom', fontsize=9.5, color=MUTED)
    ax.text(3.7, -0.75, f'raw score {score:+.2f}', ha='center', va='center',
            fontsize=10.5, color=INK)
    ax.text(3.7, -1.2, f'divide by 2:  {score / 2:+.2f}', ha='center', va='center',
            fontsize=10.5, color=INK)
    _arrow(ax, 3.7, -1.5, 3.7, -2.0, colour=MUTED, lw=1.2)
    ax.text(3.95, -1.75, 'softmax, with the other three scores', ha='left', va='center',
            fontsize=9.5, color=MUTED)
    ax.text(3.7, -2.35, f'weight {weight:.3f}', ha='center', va='center',
            fontsize=11.5, color=GRIP, weight='bold')
    ax.text(6.9, -2.1, f'"{TOKENS[give]}" is giving', ha='center', va='bottom',
            fontsize=10.5, color=PURPLE, weight='bold')
    _grid(ax, TOY.V[give].reshape(1, 4), x0=5.8, y0=-2.2, cw=0.55, ch=0.55,
          fmt='{:+.2f}', fontsize=8.0, rows=['value'], rowsize=9.5)
    _arrow(ax, 5.6, -2.48, 4.55, -2.48, colour=PURPLE, lw=1.4)
    ax.text(1.4, -3.25, f'{weight:.3f} of that value vector goes into the new "{TOKENS[ask]}"',
            ha='center', va='center', fontsize=10, color=INK)
    _arrow(ax, 3.4, -2.65, 2.7, -3.05, colour=PURPLE, lw=1.4)
    ax.set_xlim(-1.3, 9.1)
    ax.set_ylim(-3.7, 0.8)
    _fit(fig, ax)
    _title(fig, 'One pair of tokens: the query asks, the key answers, the value travels')
    _save(fig, ATT_DOC, 'query-meets-key.svg')


# --------------------------------------------------------------------------
# section 3: the score, and why it is divided
# --------------------------------------------------------------------------

def dot_product_worked_out() -> None:
    q4 = TOY.Q[3]
    fig, ax = plt.subplots(figsize=(11.4, 4.6), facecolor='white')
    _blank(ax)
    _grid(ax, q4.reshape(1, 4), x0=0.0, cw=1.1, ch=0.64, fmt='{:+.2f}',
          rows=['query of "cube"'], rowsize=10.0)
    x = 0.0
    for i in range(4):
        k = TOY.K[i]
        terms = [f'{a:+.2f} x {b:+.2f} = {a * b:+.4f}' for a, b in zip(q4, k)]
        total = float(q4 @ k)
        _lines(ax, x, -1.5, [f'against key of "{TOKENS[i]}"'] + terms +
               ['-' * 24, f'      raw score = {total:+.4f}'], size=8.8)
        x += 3.3
    ax.set_xlim(-2.9, 13.2)
    ax.set_ylim(-3.5, 0.25)
    _fit(fig, ax)
    _title(fig, 'One query against four keys: four dot products')
    _save(fig, ATT_DOC, 'dot-product-worked-out.svg')


def dot_product_vs_angle() -> None:
    """Why a dot product measures fit: it follows the angle between the vectors."""
    length = 2.0
    deg = np.linspace(0.0, 180.0, 361)
    dot = length * length * np.cos(np.deg2rad(deg))
    marks = [0, 60, 90, 120, 180]
    print(f'[angle] two vectors of length {length:.0f} each:')
    for a in marks:
        print(f'[angle] {a:3d} degrees apart -> dot product '
              f'{length * length * math.cos(math.radians(a)):+.2f}')
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(deg, dot, color=LINK, lw=2.4)
    ax.axhline(0.0, color=MUTED, ls=':', lw=1.0)
    for a in marks:
        v = length * length * math.cos(math.radians(a))
        ax.plot([a], [v], marker='o', color=GRIP, ms=7)
        ax.text(a, v + (0.22 if a <= 90 else -0.22), f'{v:+.2f}', ha='center',
                va='bottom' if a <= 90 else 'top', fontsize=10, color=INK)
    ax.text(4, -3.2, 'pointing the same way:\nlarge and positive', ha='left', va='bottom',
            fontsize=9.5, color=MUTED)
    ax.text(90, -3.2, 'at right angles:\nzero', ha='center', va='bottom',
            fontsize=9.5, color=MUTED)
    ax.text(176, -3.2, 'pointing opposite ways:\nlarge and negative', ha='right',
            va='bottom', fontsize=9.5, color=MUTED)
    ax.set_xticks(marks)
    ax.set_xticklabels([f'{a}' for a in marks])
    ax.set_xlabel('angle between the query and the key, in degrees', fontsize=10)
    ax.set_ylabel('their dot product', fontsize=10)
    ax.set_ylim(-5.4, 5.0)
    ax.set_title(f'Two vectors of length {length:.0f}, turned away from each other',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'dot-product-vs-angle.svg')


def raw_score_grid() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 3.4), facecolor='white')
    _blank(ax)
    rows = [f'query "{t}"' for t in TOKENS]
    cols = [f'key "{t}"' for t in TOKENS]
    w, h = _grid(ax, TOY.raw, cw=1.3, ch=0.72, rows=rows, cols=cols)
    ax.text(w / 2, -h - 0.3, 'row 4, column 1 is the -0.28 worked out above',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-1.9, w + 0.3)
    ax.set_ylim(-h - 0.9, 1.0)
    _fit(fig, ax)
    _title(fig, 'Sixteen raw scores: every query against every key')
    _save(fig, ATT_DOC, 'raw-score-grid.svg')


def scaled_score_grid() -> None:
    fig, ax = plt.subplots(figsize=(10.8, 3.4), facecolor='white')
    _blank(ax)
    rows = [f'query "{t}"' for t in TOKENS]
    w1, h = _grid(ax, TOY.raw, cw=1.2, ch=0.72, rows=rows, title='raw scores')
    w2, _ = _grid(ax, TOY.scaled, x0=w1 + 1.9, cw=1.2, ch=0.72,
                  title='after dividing by 2')
    ax.text(w1 + 0.95, -h / 2 + 0.06, 'divide by 2,', ha='center', va='bottom',
            fontsize=10, color=MUTED)
    ax.text(w1 + 0.95, -h / 2 - 0.06, 'the square root of 4', ha='center', va='top',
            fontsize=10, color=MUTED)
    ax.text(w1 + 1.85, -h - 0.3,
            'the biggest score drops from '
            f'{TOY.raw.max():.2f} to {TOY.scaled.max():.2f}, and every gap halves',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-2.0, w1 + 1.9 + w2 + 0.3)
    ax.set_ylim(-h - 1.1, 0.95)
    _fit(fig, ax)
    _title(fig, 'Dividing by the square root of the head size')
    _save(fig, ATT_DOC, 'why-divide-by-two.svg')


_HEAD_SIZES: list[int] = [4, 16, 64, 256, 1024]
_N_KEYS: int = 64


def head_size_experiment() -> tuple[list[float], list[float], list[float], list[float]]:
    """Random queries and keys at five head sizes, measured twice over."""
    spread_raw, spread_scaled, top_raw, top_scaled = [], [], [], []
    for d in _HEAD_SIZES:
        rng = np.random.default_rng(100 + d)
        q = rng.normal(0.0, 1.0, (400, d))
        k = rng.normal(0.0, 1.0, (400, _N_KEYS, d))
        s = np.einsum('bd,bkd->bk', q, k)
        spread_raw.append(float(s.std()))
        spread_scaled.append(float((s / math.sqrt(d)).std()))
        top_raw.append(float(_softmax(s).max(axis=1).mean()))
        top_scaled.append(float(_softmax(s / math.sqrt(d)).max(axis=1).mean()))
    print('[scale] head sizes            ', _HEAD_SIZES)
    print('[scale] spread of raw scores  ', [round(v, 2) for v in spread_raw])
    print('[scale] spread after dividing ', [round(v, 2) for v in spread_scaled])
    print('[scale] biggest weight, raw   ', [round(v, 3) for v in top_raw])
    print('[scale] biggest weight, scaled', [round(v, 3) for v in top_scaled])
    return spread_raw, spread_scaled, top_raw, top_scaled


def score_spread_vs_head_size() -> None:
    """Idea one: the raw scores grow with the head size, and the division undoes it."""
    spread_raw, spread_scaled, _, _ = head_size_experiment()
    fig, ax = plt.subplots(figsize=(9.0, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(_HEAD_SIZES, spread_raw, marker='o', color=GRIP, lw=2,
            label='raw dot product')
    ax.plot(_HEAD_SIZES, spread_scaled, marker='o', color=TEAL, lw=2,
            label='after dividing by the square root')
    ax.plot(_HEAD_SIZES, [math.sqrt(d) for d in _HEAD_SIZES], ls='--', color=MUTED,
            lw=1.2, label='the square root of the head size')
    for d, v in zip(_HEAD_SIZES, spread_raw):
        ax.text(d, v * 1.1, f'{v:.2f}', ha='center', va='bottom', fontsize=9.5, color=INK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(_HEAD_SIZES)
    ax.set_xticklabels([str(s) for s in _HEAD_SIZES])
    ax.set_xlabel('head size (how many numbers in one query)', fontsize=10)
    ax.set_ylabel('typical spread of the scores', fontsize=10)
    ax.set_title('Raw scores grow with the head size; the division takes that back out',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'score-spread-vs-head-size.svg')


def sharpness_vs_head_size() -> None:
    """Idea two: without the division, one key alone takes nearly all the weight."""
    _, _, top_raw, top_scaled = head_size_experiment()
    fig, ax = plt.subplots(figsize=(9.0, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(_HEAD_SIZES, top_raw, marker='o', color=GRIP, lw=2, label='raw dot product')
    ax.plot(_HEAD_SIZES, top_scaled, marker='o', color=TEAL, lw=2,
            label='after dividing by the square root')
    for d, v in zip(_HEAD_SIZES, top_raw):
        ax.text(d, v + 0.035, f'{v:.3f}', ha='center', va='bottom', fontsize=9.5, color=INK)
    for d, v in zip(_HEAD_SIZES, top_scaled):
        ax.text(d, v + 0.035, f'{v:.3f}', ha='center', va='bottom', fontsize=9.5, color=INK)
    ax.axhline(1.0, color=MUTED, ls=':', lw=1.0)
    ax.set_xscale('log')
    ax.set_xticks(_HEAD_SIZES)
    ax.set_xticklabels([str(s) for s in _HEAD_SIZES])
    ax.set_ylim(0, 1.12)
    ax.set_xlabel('head size (how many numbers in one query)', fontsize=10)
    ax.set_ylabel(f'biggest of the {_N_KEYS} weights, on average', fontsize=10)
    ax.set_title(f'Choosing between {_N_KEYS} keys: without the division one key takes '
                 'everything', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center left')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'sharpness-vs-head-size.svg')


# --------------------------------------------------------------------------
# section 4: softmax, the mix, and the matrix form
# --------------------------------------------------------------------------

def softmax_steps() -> None:
    row = TOY.scaled[3]
    ex = np.exp(row)
    wts = ex / ex.sum()
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1.0]})
    ax = axes[0]
    _blank(ax)
    table = np.vstack([row, ex, wts])
    w, h = _grid(ax, table, cw=1.45, ch=0.66,
                 rows=['scaled score', 'raised to a power', 'weight'],
                 cols=[f'key "{t}"' for t in TOKENS], rowsize=9.5, fmt='{:.3f}')
    ax.text(w / 2, -h - 0.25,
            f'the four raised values add up to {ex.sum():.3f}',
            ha='center', va='top', fontsize=10, color=MUTED)
    ax.set_xlim(-2.4, w + 0.3)
    ax.set_ylim(-h - 0.9, 0.95)
    ax.set_title('The query of "cube", step by step', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.bar(range(4), wts, color=[_mix(TEAL, 0.35 + 0.6 * v) for v in wts],
           edgecolor=TEAL)
    for i, v in enumerate(wts):
        ax.text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom', fontsize=10, color=INK)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f'"{t}"' for t in TOKENS], fontsize=10)
    ax.set_ylim(0, max(wts) * 1.2)
    ax.set_ylabel('share of the mix', fontsize=10)
    ax.set_title('The same four weights as shares', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'softmax-steps.svg')


def softmax_sharpness() -> None:
    """Two keys only: how much weight a lead in the score is worth."""
    lead = np.linspace(0.0, 6.0, 241)
    share = 1.0 / (1.0 + np.exp(-lead))
    marks = [0.0, 0.5, 1.0, 2.0, 4.0]
    print('[sharp] two keys, one ahead of the other:')
    for g in marks:
        print(f'[sharp] lead of {g:.1f} in the score -> '
              f'{1 / (1 + math.exp(-g)):.3f} of the mix')
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(lead, share, color=TEAL, lw=2.4)
    ax.axhline(0.5, color=MUTED, ls=':', lw=1.0)
    for g in marks:
        v = 1 / (1 + math.exp(-g))
        ax.plot([g], [v], marker='o', color=GRIP, ms=7)
        ax.text(g + 0.07, v - 0.015, f'{v:.3f}', ha='left', va='top', fontsize=10,
                color=INK)
    ax.set_xlabel('how far the leading score is ahead of the other one', fontsize=10)
    ax.set_ylabel("the leader's share of the mix", fontsize=10)
    ax.set_ylim(0.4, 1.04)
    ax.set_xlim(-0.2, 6.3)
    ax.set_title('A lead of 1 in the score is already 0.731 of the mix',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'softmax-sharpness.svg')


def weight_grid() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 3.5), facecolor='white')
    _blank(ax)
    rows = [f'query "{t}"' for t in TOKENS]
    cols = [f'key "{t}"' for t in TOKENS]
    w, h = _grid(ax, TOY.A, cw=1.3, ch=0.72, fmt='{:.3f}', rows=rows, cols=cols,
                 colour=TEAL, vmax=1.0)
    _grid(ax, TOY.A.sum(axis=1).reshape(4, 1), x0=w + 0.45, cw=1.3, ch=0.72,
          fmt='{:.3f}', cols=['row total'], colour=MUTED, vmax=1.0)
    ax.set_xlim(-2.0, w + 2.1)
    ax.set_ylim(-h - 0.35, 1.0)
    _fit(fig, ax)
    _title(fig, 'The weight grid: each row is a recipe that adds up to 1')
    _save(fig, ATT_DOC, 'weight-grid.svg')


def output_mix_worked_out() -> None:
    wts = np.round(TOY.A[3], 3)
    fig, ax = plt.subplots(figsize=(11.4, 4.4), facecolor='white')
    _blank(ax)
    _grid(ax, wts.reshape(1, 4), x0=0.0, cw=1.15, ch=0.64, fmt='{:.3f}',
          rows=['weights for "cube"'], rowsize=10.0, colour=TEAL, vmax=1.0)
    x = 0.0
    sums = []
    for j in range(4):
        col = TOY.V[:, j]
        terms = [f'{a:.3f} x {b:+.2f} = {a * b:+.4f}' for a, b in zip(wts, col)]
        total = float(wts @ col)
        sums.append(total)
        _lines(ax, x, -1.5, [f'output number {j + 1}'] + terms +
               ['-' * 23, f'            = {total:+.4f}'], size=8.8)
        x += 3.25
    _grid(ax, np.array(sums).reshape(1, 4), x0=0.0, y0=-4.0, cw=3.25, ch=0.7,
          fmt='{:+.2f}', rows=['new vector for "cube"'], rowsize=10.0)
    print('[toy] o_4 from 3dp weights', np.round(sums, 4),
          'exact', np.round(TOY.O[3], 4))
    ax.set_xlim(-3.0, 13.1)
    ax.set_ylim(-4.9, 0.6)
    _fit(fig, ax)
    _title(fig, 'The output is the value vectors added up in those proportions')
    _save(fig, ATT_DOC, 'output-mix-worked-out.svg')


def attention_as_matrices() -> None:
    fig, ax = plt.subplots(figsize=(13.4, 3.4), facecolor='white')
    _blank(ax)
    x = 0.0
    pieces = [('X\n4 x 4', TOY.X, '{:+.1f}'), ('Q\n4 x 4', TOY.Q, '{:+.2f}'),
              ('scores\n4 x 4', TOY.scaled, '{:+.2f}'), ('weights\n4 x 4', TOY.A, '{:.2f}'),
              ('output\n4 x 4', TOY.O, '{:+.2f}')]
    steps = ['times W_query,\nW_key and W_value', 'Q times K sideways,\nthen divided by 2',
             'softmax along\neach row', 'times V']
    gap = 2.9
    h = 2.0
    for n, (name, M, fmt) in enumerate(pieces):
        colour = TEAL if 'weights' in name else None
        w, h = _grid(ax, M, x0=x, cw=0.82, ch=0.52, fmt=fmt, fontsize=7.8,
                     colour=colour, vmax=1.0 if colour else None)
        ax.text(x + w / 2, -h - 0.18, name, ha='center', va='top', fontsize=10,
                color=INK, weight='bold')
        if n < 4:
            _arrow(ax, x + w + 0.35, -h / 2, x + w + gap - 0.35, -h / 2, colour=MUTED, lw=1.2)
            ax.text(x + w + gap / 2, 0.18, steps[n], ha='center', va='bottom',
                    fontsize=9, color=MUTED)
        x += w + gap
    ax.set_xlim(-0.3, x - gap + 0.3)
    ax.set_ylim(-h - 1.3, 1.1)
    _fit(fig, ax)
    _title(fig, 'The whole of attention for four tokens: four matrix multiplies and one softmax')
    _save(fig, ATT_DOC, 'attention-as-matrices.svg')


def shape_chain() -> None:
    n, d, h = 512, 768, 12
    head = d // h
    counts = [('X', n, d), ('Q, K and V', n, d), ('score grid, one head', n, n),
              ('weight grid, one head', n, n), ('output', n, d)]
    print(f'[shapes] n={n} d={d} heads={h} head size={head}')
    for name, a, b in counts:
        print(f'[shapes] {name:24s} {a} x {b} = {a * b:,} numbers')
    print(f'[shapes] all {h} score grids together: {h * n * n:,} numbers')
    fig, ax = plt.subplots(figsize=(11.0, 3.9), facecolor='white')
    _blank(ax)
    x = 0.0
    for name, a, b in counts:
        wd = 1.6 * b / d
        ht = 1.6
        ax.add_patch(Rectangle((x, -ht), wd, ht, facecolor=_mix(LINK, 0.18),
                               edgecolor=LINK, lw=1.3))
        ax.text(x + wd / 2, -ht - 0.18, f'{a} x {b}', ha='center', va='top',
                fontsize=10, color=INK, weight='bold')
        ax.text(x + wd / 2, -ht - 0.52, f'{a * b:,}\nnumbers', ha='center', va='top',
                fontsize=9, color=MUTED)
        ax.text(x + wd / 2, 0.12, name, ha='center', va='bottom', fontsize=9.5, color=INK)
        x += wd + 1.0
    ax.text(x - 1.0, -2.95,
            f'with {h} heads the {n} by {n} score grid happens {h} times over, which is '
            f'{h * n * n:,} numbers in one layer',
            ha='right', va='top', fontsize=10, color=MUTED)
    ax.set_xlim(-0.3, x - 0.7)
    ax.set_ylim(-3.5, 0.55)
    _fit(fig, ax)
    _title(fig, f'The real shapes for {n} tokens and a width of {d}')
    _save(fig, ATT_DOC, 'shape-chain.svg')


# --------------------------------------------------------------------------
# section 5: several small heads instead of one big one
# --------------------------------------------------------------------------

def split_into_heads() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 3.8), facecolor='white')
    _blank(ax)
    w1, h1 = _grid(ax, TOY.WQ, cw=1.0, ch=0.62, fmt='{:+.1f}',
                   title='W_query, the same 16 numbers')
    for g, colour in ((0, LINK), (1, PURPLE)):
        ax.add_patch(Rectangle((g * 2.0, -h1), 2.0, h1, facecolor='none',
                               edgecolor=colour, lw=2.2))
        ax.text(g * 2.0 + 1.0, -h1 - 0.16, f'head {g + 1}', ha='center', va='top',
                fontsize=10, color=colour, weight='bold')
    x = w1 + 1.4
    for g, colour in ((0, LINK), (1, PURPLE)):
        w2, h2 = _grid(ax, TOY.Q[:, 2 * g:2 * g + 2], x0=x, cw=1.1, ch=0.62,
                       rows=[f'"{t}"' for t in TOKENS] if g == 0 else None,
                       title=f'queries, head {g + 1}', box=colour)
        x += w2 + 1.3
    ax.text(w1 + 2.9, -h1 - 0.65,
            'each token now has a query of two numbers in each head, not one of four',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-1.6, x - 0.9)
    ax.set_ylim(-h1 - 1.5, 0.9)
    _fit(fig, ax)
    _title(fig, 'Two heads are two halves of the same matrices')
    _save(fig, ATT_DOC, 'split-into-heads.svg')


def two_heads_two_patterns() -> None:
    fig, ax = plt.subplots(figsize=(10.6, 3.6), facecolor='white')
    _blank(ax)
    x = 0.0
    for g, colour in ((0, LINK), (1, PURPLE)):
        a = TOY.heads[g]['a']
        w, h = _grid(ax, a, x0=x, cw=1.25, ch=0.7, fmt='{:.3f}', colour=TEAL, vmax=1.0,
                     rows=[f'query "{t}"' for t in TOKENS] if g == 0 else None,
                     cols=[f'"{t}"' for t in TOKENS], box=colour,
                     title=f'head {g + 1} weights')
        spread = float(a.max(axis=1).mean())
        ax.text(x + w / 2, -h - 0.25,
                f'biggest weight in a row, on average: {spread:.3f}',
                ha='center', va='top', fontsize=9.5, color=MUTED)
        x += w + 1.9
    ax.set_xlim(-2.4, x - 1.6)
    ax.set_ylim(-h - 0.95, 1.0)
    _fit(fig, ax)
    _title(fig, 'The same four tokens, two different mixing patterns')
    _save(fig, ATT_DOC, 'two-heads-two-patterns.svg')


def join_the_heads() -> None:
    fig, ax = plt.subplots(figsize=(11.6, 3.5), facecolor='white')
    _blank(ax)
    w1, h = _grid(ax, TOY.cat, cw=1.1, ch=0.66, rows=[f'"{t}"' for t in TOKENS],
                  title='the two head outputs written side by side')
    for g, colour in ((0, LINK), (1, PURPLE)):
        ax.add_patch(Rectangle((g * 2.2, -h), 2.2, h, facecolor='none',
                               edgecolor=colour, lw=2.2))
        ax.text(g * 2.2 + 1.1, -h - 0.16, f'head {g + 1}', ha='center', va='top',
                fontsize=10, color=colour, weight='bold')
    x = w1 + 1.3
    w2, _ = _grid(ax, TOY.WO, x0=x, cw=1.0, ch=0.66, fmt='{:+.1f}',
                  title='W_out, 4 by 4')
    ax.text(x - 0.65, -h / 2, 'x', ha='center', va='center', fontsize=13, color=MUTED)
    x += w2 + 1.3
    w3, _ = _grid(ax, TOY.two_head_out, x0=x, cw=1.1, ch=0.66,
                  title='what the two heads give together')
    ax.text(x - 0.65, -h / 2, '=', ha='center', va='center', fontsize=13, color=MUTED)
    ax.set_xlim(-1.5, x + w3 + 0.3)
    ax.set_ylim(-h - 0.9, 1.0)
    _fit(fig, ax)
    _title(fig, 'The heads are joined back together and passed through one more matrix')
    _save(fig, ATT_DOC, 'join-the-heads.svg')


def head_count_shapes() -> None:
    d = 768
    options = [1, 4, 12, 24, 48]
    per_matrix = d * d
    print(f'[heads] width {d}: one matrix holds {per_matrix:,} numbers, '
          f'four of them hold {4 * per_matrix:,}')
    for h in options:
        print(f'[heads] {h:2d} heads -> head size {d // h:3d}, '
              f'score grids per layer {h}, numbers in all four matrices {4 * per_matrix:,}')
    fig, ax = plt.subplots(figsize=(10.8, 3.4), facecolor='white')
    _blank(ax)
    y = 0.0
    for h in options:
        head = d // h
        ax.text(-0.25, y - 0.3, f'{h} head' + ('s' if h > 1 else ''), ha='right',
                va='center', fontsize=10, color=INK)
        for g in range(h):
            frac = g / max(h - 1, 1)
            ax.add_patch(Rectangle((8.0 * g / h, y - 0.55), 8.0 / h - 0.03, 0.5,
                                   facecolor=_mix(LINK, 0.25 + 0.5 * frac),
                                   edgecolor='white', lw=0.8))
        ax.text(8.2, y - 0.3, f'head size {head}', ha='left', va='center',
                fontsize=10, color=MUTED)
        y -= 0.8
    ax.text(4.0, y - 0.1, f'the width is always {d} numbers, cut up in different ways;\n'
            f'the four matrices hold {4 * per_matrix:,} numbers whichever cut is chosen',
            ha='center', va='top', fontsize=10, color=INK)
    ax.set_xlim(-2.6, 11.4)
    ax.set_ylim(y - 1.1, 0.3)
    _fit(fig, ax)
    _title(fig, 'Cutting a width of 768 into heads costs nothing extra')
    _save(fig, ATT_DOC, 'head-count-shapes.svg')


# --------------------------------------------------------------------------
# section 6: self-attention, cross-attention and the mask
# --------------------------------------------------------------------------

def self_and_cross() -> None:
    rng = np.random.default_rng(55)
    Z = np.round(rng.normal(0.0, 0.9, (2, 4)), 1)
    QZ = Z @ TOY.WQ
    cross = QZ @ TOY.K.T / 2.0
    AC = _softmax(cross)
    print('[cross] two extra tokens\n', Z)
    print('[cross] their queries\n', np.round(QZ, 2))
    print('[cross] scaled scores against the four word keys\n', np.round(cross, 2))
    print('[cross] weights\n', np.round(AC, 3))
    print('[cross] output\n', np.round(AC @ TOY.V, 2))

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 3.8), facecolor='white')
    ax = axes[0]
    _blank(ax)
    w, h = _grid(ax, TOY.A, cw=1.1, ch=0.62, fmt='{:.2f}', colour=TEAL, vmax=1.0,
                 rows=[f'"{t}"' for t in TOKENS], cols=[f'"{t}"' for t in TOKENS])
    ax.text(w / 2, -h - 0.3, 'queries: the four words\nkeys and values: the same four words\n'
            'grid shape: 4 by 4', ha='center', va='top', fontsize=9.5, color=INK)
    ax.set_xlim(-1.4, w + 0.3)
    ax.set_ylim(-h - 1.6, 0.9)
    ax.set_title('Self-attention', fontsize=11.5, weight='bold')
    ax = axes[1]
    _blank(ax)
    w, h = _grid(ax, AC, cw=1.1, ch=0.62, fmt='{:.2f}', colour=JOINT, vmax=1.0,
                 rows=['arm state', 'gripper'], cols=[f'"{t}"' for t in TOKENS])
    ax.text(w / 2, -h - 0.3, 'queries: two robot tokens\nkeys and values: the four words\n'
            'grid shape: 2 by 4', ha='center', va='top', fontsize=9.5, color=INK)
    ax.set_xlim(-1.6, w + 0.3)
    ax.set_ylim(-h - 1.6, 0.9)
    ax.set_title('Cross-attention', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'self-and-cross.svg')


def mask_grid() -> None:
    forbid = np.zeros((4, 4), dtype=bool)
    forbid[:, 3] = True          # the last token is padding: nobody may look at it
    forbid[3, :] = True          # and it asks nothing of anybody
    forbid[3, 3] = False
    scores = TOY.scaled.copy()
    masked = np.where(forbid, -np.inf, scores)
    A = _softmax(masked)
    print('[mask] weights with the last token forbidden\n', np.round(A, 3))
    print('[mask] row sums', np.round(A.sum(axis=1), 6))
    fig, ax = plt.subplots(figsize=(11.0, 3.6), facecolor='white')
    _blank(ax)
    w1, h = _grid(ax, scores, cw=1.2, ch=0.68, rows=[f'query "{t}"' for t in TOKENS],
                  mask=forbid, title='scores, with the forbidden pairs replaced')
    w2, _ = _grid(ax, A, x0=w1 + 1.6, cw=1.2, ch=0.68, fmt='{:.3f}', colour=TEAL,
                  vmax=1.0, title='the weights that come out')
    _arrow(ax, w1 + 0.3, -h / 2, w1 + 1.4, -h / 2, colour=MUTED, lw=1.2)
    ax.text(w1 + 0.85, -h / 2 + 0.2, 'softmax', ha='center', va='bottom',
            fontsize=9.5, color=MUTED)
    ax.text(w1 + 1.6 + w2 / 2, -h - 0.3,
            'a forbidden pair gets weight 0.000 exactly, and the weights that are left\n'
            'still add up to 1 in every row', ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-2.1, w1 + 1.6 + w2 + 0.3)
    ax.set_ylim(-h - 1.4, 0.9)
    _fit(fig, ax)
    _title(fig, 'A mask forbids pairs by setting their score to minus infinity')
    _save(fig, ATT_DOC, 'mask-grid.svg')


def mask_arithmetic() -> None:
    row = TOY.scaled[1]
    ex = np.exp(row)
    kept = ex.copy()
    kept[3] = 0.0
    wts = kept / kept.sum()
    print('[mask] row 2 before', np.round(_softmax(row), 3))
    print('[mask] row 2 after forbidding key 4', np.round(wts, 3),
          'sum of the three raised values', round(float(kept.sum()), 3))
    fig, ax = plt.subplots(figsize=(10.4, 3.6), facecolor='white')
    _blank(ax)
    lines = ['row 2 of the scaled scores, with the last key forbidden:',
             '',
             f'  key 1   {row[0]:+.2f}   raised to a power = {ex[0]:7.3f}',
             f'  key 2   {row[1]:+.2f}   raised to a power = {ex[1]:7.3f}',
             f'  key 3   {row[2]:+.2f}   raised to a power = {ex[2]:7.3f}',
             '  key 4    -inf   raised to a power =   0.000',
             '                                     -------',
             f'                               total = {kept.sum():7.3f}',
             '',
             f'  weights = {wts[0]:.3f}  {wts[1]:.3f}  {wts[2]:.3f}  {wts[3]:.3f}'
             f'   (total {wts.sum():.3f})']
    _lines(ax, 0.0, 0.0, lines, size=10.0, dy=0.34)
    ax.set_xlim(-0.2, 7.4)
    ax.set_ylim(-3.3, 0.4)
    _fit(fig, ax)
    _title(fig, 'Minus infinity becomes a weight of exactly zero')
    _save(fig, ATT_DOC, 'mask-arithmetic.svg')


def robot_model_attention() -> None:
    groups = [('picture\ntokens', 256, LINK), ('words of\nthe order', 12, TEAL),
              ('joint\nreadings', 1, JOINT), ('action\ntokens', 8, GRIP)]
    total = sum(g[1] for g in groups)
    allowed = np.array([[1, 1, 0, 0],
                        [1, 1, 0, 0],
                        [1, 1, 1, 0],
                        [1, 1, 1, 1]], dtype=float)
    sizes = np.array([g[1] for g in groups], dtype=float)
    pairs = float((allowed * np.outer(sizes, sizes)).sum())
    print('[robot] token groups: ' + ', '.join(f'{n} {nm}'.replace(chr(10), ' ')
                                               for nm, n, _ in groups))
    print(f'[robot] tokens in all: {total}, pairs in the full grid: {total * total:,}, '
          f'pairs the mask allows: {int(pairs):,} '
          f'({100 * pairs / (total * total):.1f} per cent)')
    fig, ax = plt.subplots(figsize=(9.2, 4.6), facecolor='white')
    _blank(ax)
    cw, ch = 1.6, 0.9
    for i in range(4):
        for j in range(4):
            yes = allowed[i, j] > 0
            ax.add_patch(Rectangle((j * cw, -(i + 1) * ch), cw, ch,
                                   facecolor=_mix(TEAL, 0.32) if yes else _mix(MUTED, 0.18),
                                   edgecolor='white', lw=1.4))
            ax.text((j + 0.5) * cw, -(i + 0.5) * ch, 'allowed' if yes else 'forbidden',
                    ha='center', va='center', fontsize=9.5,
                    color=INK if yes else MUTED)
    for i, (nm, n, colour) in enumerate(groups):
        ax.text(-0.18, -(i + 0.5) * ch, f'{nm} ({n})', ha='right', va='center',
                fontsize=9.5, color=colour)
        ax.text((i + 0.5) * cw, 0.12, f'{nm} ({n})', ha='center', va='bottom',
                fontsize=9.5, color=colour)
    ax.text(2 * cw, 1.25, 'keys and values: what may be looked at', ha='center',
            va='bottom', fontsize=10, color=MUTED)
    ax.text(-1.95, -2 * ch, 'queries: who is looking', ha='center', va='center',
            fontsize=10, color=MUTED, rotation=90)
    ax.text(2 * cw, -4 * ch - 0.3,
            f'{total} tokens in all, so the full grid holds {total * total:,} pairs; '
            f'this mask allows {int(pairs):,} of them, which is '
            f'{100 * pairs / (total * total):.1f} per cent',
            ha='center', va='top', fontsize=9.5, color=INK)
    ax.set_xlim(-2.6, 4 * cw + 0.3)
    ax.set_ylim(-4 * ch - 1.0, 1.65)
    _fit(fig, ax)
    _title(fig, 'One arrangement for a robot model: who is allowed to look at whom')
    _save(fig, ATT_DOC, 'robot-model-attention.svg')


# --------------------------------------------------------------------------
# section 7: what it costs
# --------------------------------------------------------------------------

def score_grid_grows() -> None:
    fig, ax = plt.subplots(figsize=(10.6, 3.6), facecolor='white')
    _blank(ax)
    x = 0.0
    for n in (4, 8, 16):
        cell = 2.4 / n
        for i in range(n):
            for j in range(n):
                ax.add_patch(Rectangle((x + j * cell, -(i + 1) * cell), cell, cell,
                                       facecolor=_mix(LINK, 0.45), edgecolor='white',
                                       lw=0.6 if n < 16 else 0.3))
        ax.text(x + 1.2, -2.55, f'{n} tokens', ha='center', va='top', fontsize=10.5,
                color=INK, weight='bold')
        ax.text(x + 1.2, -2.95, f'{n} x {n} = {n * n} scores', ha='center', va='top',
                fontsize=10, color=MUTED)
        x += 3.4
    ax.text((x - 1.0) / 2, -3.8, 'twice the tokens, four times the scores',
            ha='center', va='top', fontsize=10.5, color=INK)
    ax.set_xlim(-0.3, x - 0.7)
    ax.set_ylim(-4.2, 0.1)
    _fit(fig, ax)
    _fit(fig, ax)
    _title(fig, 'The score grid is every token against every token')
    _save(fig, ATT_DOC, 'score-grid-grows.svg')


def cost_vs_length() -> None:
    d = 768
    lengths = np.array([128, 512, 1536, 2048, 8192, 32768, 131072], dtype=float)
    proj = 4 * lengths * d * d
    sc = 2 * lengths * lengths * d
    print(f'[cost] width {d}, one layer, one set of heads:')
    for n, p, s in zip(lengths, proj, sc):
        print(f'[cost] {int(n):7d} tokens: projections {p / 1e9:10.2f} billion, '
              f'scores and mixing {s / 1e9:10.2f} billion, '
              f'share from the grid {100 * s / (p + s):5.1f} per cent')
    print(f'[cost] the two parts are equal at {2 * d} tokens')
    fig, ax = plt.subplots(figsize=(9.6, 4.6), facecolor='white')
    _plain(ax)
    ax.plot(lengths, proj / 1e9, marker='o', color=LINK, lw=2,
            label='the four projections: 4 x n x 768 x 768')
    ax.plot(lengths, sc / 1e9, marker='o', color=GRIP, lw=2,
            label='scores and mixing: 2 x n x n x 768')
    ax.plot(lengths, (proj + sc) / 1e9, color=INK, lw=1.2, ls='--', label='the two together')
    ax.axvline(2 * d, color=MUTED, ls=':', lw=1.2)
    ax.text(2 * d * 1.08, 2e-2, f'equal at {2 * d} tokens', fontsize=9.5, color=MUTED,
            rotation=90, va='bottom')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(lengths)
    ax.set_xticklabels([f'{int(n):,}' for n in lengths], rotation=45, ha='right')
    ax.set_xlabel('number of tokens in the window', fontsize=10)
    ax.set_ylabel('billions of multiply-and-add steps, one layer', fontsize=10)
    ax.set_title('Below 1,536 tokens the matrices cost more; above it the grid does',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'cost-vs-length.svg')


def score_memory() -> None:
    h, byte = 12, 2
    lengths = [512, 2048, 8192, 32768]
    sizes = [n * n * h * byte for n in lengths]
    for n, s in zip(lengths, sizes):
        print(f'[memory] {n:6d} tokens: {h} score grids at {byte} bytes each = '
              f'{s:,} bytes = {s / 2**20:,.1f} MiB')
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    bars = ax.bar([str(f'{n:,}') for n in lengths], [s / 2**20 for s in sizes],
                  color=_mix(GRIP, 0.55), edgecolor=GRIP, width=0.6)
    for b, s in zip(bars, sizes):
        txt = f'{s / 2**20:,.0f} MiB' if s < 2**30 else f'{s / 2**30:,.1f} GiB'
        ax.text(b.get_x() + b.get_width() / 2, s / 2**20 * 1.08, txt, ha='center',
                va='bottom', fontsize=10, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, 1e5)
    ax.set_xlabel('number of tokens in the window', fontsize=10)
    ax.set_ylabel('memory for one layer of score grids (MiB)', fontsize=10)
    ax.set_title(f'All {h} score grids of one layer, held as two-byte numbers',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'score-memory.svg')


# --------------------------------------------------------------------------
# 02_a-transformer-block.md: the same four tokens through one whole block
# --------------------------------------------------------------------------

def _rms_norm(X: Arr) -> Arr:
    """Divide every row by the square root of the mean of its squares."""
    return X / np.sqrt((X ** 2).mean(axis=1, keepdims=True))


class Block:
    """One pre-norm transformer block run on the four-token example."""

    def __init__(self) -> None:
        t = TOY
        self.x: Arr = t.X
        self.n1: Arr = _rms_norm(self.x)
        q, k, v = self.n1 @ t.WQ, self.n1 @ t.WK, self.n1 @ t.WV
        self.a: Arr = _softmax(q @ k.T / 2.0)
        self.attn: Arr = (self.a @ v) @ t.WO
        self.s1: Arr = self.x + self.attn
        self.n2: Arr = _rms_norm(self.s1)
        self.hidden: Arr = self.n2 @ t.W1
        self.hidden_gelu: Arr = _gelu(self.hidden)
        self.ff: Arr = self.hidden_gelu @ t.W2
        self.s2: Arr = self.s1 + self.ff

    @staticmethod
    def rms(M: Arr) -> float:
        return float(np.sqrt((np.asarray(M) ** 2).mean()))


BLOCK = Block()


def report_block() -> None:
    b = BLOCK
    print('[block] x\n', np.round(b.x, 2))
    print('[block] after the first normalisation\n', np.round(b.n1, 2))
    print('[block] what attention gives\n', np.round(b.attn, 2))
    print('[block] stream after the first add\n', np.round(b.s1, 2))
    print('[block] after the second normalisation\n', np.round(b.n2, 2))
    print('[block] what the feed-forward part gives\n', np.round(b.ff, 2))
    print('[block] stream after the second add\n', np.round(b.s2, 2))
    print(f'[block] typical size: x {b.rms(b.x):.3f}, attention output {b.rms(b.attn):.3f}, '
          f'stream after one add {b.rms(b.s1):.3f}, feed-forward output {b.rms(b.ff):.3f}, '
          f'stream at the end {b.rms(b.s2):.3f}')
    sq = BLOCK.x[0] ** 2
    print(f'[block] token 1 squares {np.round(sq, 2)}, mean {sq.mean():.4f}, '
          f'root {math.sqrt(sq.mean()):.4f}, normalised {np.round(BLOCK.n1[0], 3)}')


def six_steps() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _blank(ax)
    steps = [('1. normalise', 'put every token on the same scale', TEAL),
             ('2. attention', 'every token mixes the others', LINK),
             ('3. add it back on', 'the stream keeps what it had', JOINT),
             ('4. normalise again', 'the same rule, a second scale', TEAL),
             ('5. feed-forward part', 'each token on its own, widened then narrowed', PURPLE),
             ('6. add it back on', 'the stream keeps what it had', JOINT)]
    y = 0.0
    ax.text(3.9, 0.35, 'in: 4 tokens, 4 numbers each', ha='center', va='bottom',
            fontsize=10, color=INK)
    for name, what, colour in steps:
        _box(ax, 2.1, y - 0.52, 3.6, 0.56, name, face=_mix(colour, 0.18), edge=colour,
             size=10.5, weight='bold')
        ax.text(5.95, y - 0.24, what, ha='left', va='center', fontsize=9.5, color=MUTED)
        y -= 0.95
    ax.text(3.9, y + 0.1, 'out: 4 tokens, 4 numbers each', ha='center', va='top',
            fontsize=10, color=INK)
    ax.annotate('', xy=(1.55, y + 0.33), xytext=(1.55, 0.05),
                arrowprops=dict(arrowstyle='-|>', lw=2.4, color=JOINT))
    ax.text(1.3, y / 2, 'the stream runs down here', ha='center', va='center',
            fontsize=10, color=JOINT, rotation=90)
    ax.set_xlim(0.3, 12.4)
    ax.set_ylim(y - 0.55, 0.85)
    _fit(fig, ax)
    _title(fig, 'One transformer block, in the order the steps happen')
    _save(fig, BLK_DOC, 'six-steps.svg')


def numbers_through_a_block() -> None:
    b = BLOCK
    stages = [('in', b.x, '{:+.1f}'), ('normalised', b.n1, '{:+.2f}'),
              ('attention gives', b.attn, '{:+.2f}'), ('add: stream', b.s1, '{:+.2f}'),
              ('normalised again', b.n2, '{:+.2f}'), ('feed-forward gives', b.ff, '{:+.2f}'),
              ('add: stream out', b.s2, '{:+.2f}')]
    fig, ax = plt.subplots(figsize=(13.2, 3.4), facecolor='white')
    _blank(ax)
    x = 0.0
    for n, (name, M, fmt) in enumerate(stages):
        colour = JOINT if 'stream' in name else None
        w, h = _grid(ax, M, x0=x, cw=0.76, ch=0.5, fmt=fmt, fontsize=7.5,
                     rows=[f'"{t}"' for t in TOKENS] if n == 0 else None,
                     rowsize=9.0, box=colour)
        ax.text(x + w / 2, 0.12, name, ha='center', va='bottom', fontsize=9.5,
                color=JOINT if colour else INK,
                weight='bold' if colour else 'normal')
        ax.text(x + w / 2, -h - 0.18, f'size {BLOCK.rms(M):.2f}', ha='center', va='top',
                fontsize=9, color=MUTED)
        x += w + 0.55
    ax.set_xlim(-1.3, x - 0.3)
    ax.set_ylim(-h - 0.8, 0.8)
    _fit(fig, ax)
    _title(fig, 'The four tokens at every stage of one block, with their typical size')
    _save(fig, BLK_DOC, 'numbers-through-a-block.svg')


def size_of_each_change() -> None:
    b = BLOCK
    names = ['the stream\ncoming in', 'what attention\nadds', 'the stream\nafter one add',
             'what feed-forward\nadds', 'the stream\ngoing out']
    vals = [b.rms(b.x), b.rms(b.attn), b.rms(b.s1), b.rms(b.ff), b.rms(b.s2)]
    colours = [JOINT, LINK, JOINT, PURPLE, JOINT]
    fig, ax = plt.subplots(figsize=(9.4, 4.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(5), vals, color=[_mix(c, 0.45) for c in colours],
                  edgecolor=colours, width=0.62)
    for bb, v in zip(bars, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, v + 0.015, f'{v:.2f}', ha='center',
                va='bottom', fontsize=10.5, color=INK)
    ax.set_xticks(range(5))
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_ylabel('typical size of the numbers', fontsize=10)
    ax.set_title('Each part adds something of its own size to the stream it was given',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'size-of-each-change.svg')


# --------------------------------------------------------------------------
# page 2, section 2: normalisation, and why it goes first
# --------------------------------------------------------------------------

def rms_norm_worked_out() -> None:
    x = BLOCK.x[0]
    sq = x ** 2
    mean = float(sq.mean())
    root = math.sqrt(mean)
    out = x / root
    fig, ax = plt.subplots(figsize=(10.0, 3.8), facecolor='white')
    _blank(ax)
    lines = [f'the vector of "{TOKENS[0]}":   ' +
             '  '.join(f'{v:+.1f}' for v in x),
             '',
             '  squares:            ' + '  '.join(f'{v:.2f}' for v in sq),
             f'  their mean:         ({" + ".join(f"{v:.2f}" for v in sq)}) / 4 = {mean:.4f}',
             f'  square root:        {mean:.4f} -> {root:.4f}',
             '',
             '  divide each number by ' + f'{root:.4f}:',
             '     ' + '  '.join(f'{v:+.1f} / {root:.4f} = {o:+.3f}' for v, o in
                                 zip(x[:2], out[:2])),
             '     ' + '  '.join(f'{v:+.1f} / {root:.4f} = {o:+.3f}' for v, o in
                                 zip(x[2:], out[2:])),
             '',
             '  the result:         ' + '  '.join(f'{v:+.3f}' for v in out) +
             f'   (its own typical size is {math.sqrt((out ** 2).mean()):.3f})']
    _lines(ax, 0.0, 0.0, lines, size=9.8, dy=0.33)
    ax.set_xlim(-0.2, 9.6)
    ax.set_ylim(-3.8, 0.4)
    _fit(fig, ax)
    _title(fig, 'Root-mean-square normalisation on one token, in full')
    _save(fig, BLK_DOC, 'rms-norm-worked-out.svg')


def token_sizes_before_and_after() -> None:
    """Normalisation pulls four tokens of different sizes onto one scale."""
    b = BLOCK
    before = [float(np.sqrt((row ** 2).mean())) for row in b.x]
    after = [float(np.sqrt((row ** 2).mean())) for row in b.n1]
    print('[norm] typical size of each token before', [round(v, 3) for v in before])
    print('[norm] typical size of each token after ', [round(v, 3) for v in after])
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    xs = np.arange(4)
    b1 = ax.bar(xs - 0.19, before, width=0.38, color=_mix(MUTED, 0.5), edgecolor=MUTED,
                label='before normalising')
    b2 = ax.bar(xs + 0.19, after, width=0.38, color=_mix(TEAL, 0.5), edgecolor=TEAL,
                label='after normalising')
    for bars, vals in ((b1, before), (b2, after)):
        for bb, v in zip(bars, vals):
            ax.text(bb.get_x() + bb.get_width() / 2, v + 0.02, f'{v:.2f}', ha='center',
                    va='bottom', fontsize=10, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'"{t}"' for t in TOKENS], fontsize=10.5)
    ax.set_ylim(0, 1.35)
    ax.set_ylabel('typical size of that token\'s four numbers', fontsize=10)
    ax.set_title('Four tokens of four different sizes all come out at exactly 1.00',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'token-sizes-before-and-after.svg')


def _norm_order_drawing(mode: str, name: str, title: str) -> None:
    """Draw one of the two orders on its own, because a drawing is a whole argument."""
    fig, ax = plt.subplots(figsize=(6.6, 5.2), facecolor='white')
    _blank(ax)
    if mode == 'pre':
        _box(ax, 1.4, 1.0, 2.4, 0.6, 'normalise', face=_mix(TEAL, 0.18), edge=TEAL)
        _box(ax, 1.4, 2.1, 2.4, 0.6, 'attention', face=_mix(LINK, 0.18), edge=LINK)
        ax.add_patch(plt.Circle((2.6, 3.6), 0.22, facecolor='white', edgecolor=JOINT, lw=1.8))
        ax.text(2.6, 3.6, '+', ha='center', va='center', fontsize=13, color=JOINT)
        _arrow(ax, 2.6, 0.3, 2.6, 0.95, colour=INK)
        _arrow(ax, 2.6, 1.62, 2.6, 2.05, colour=INK)
        _arrow(ax, 2.6, 2.72, 2.6, 3.35, colour=INK)
        _arrow(ax, 2.6, 3.84, 2.6, 4.6, colour=INK)
        ax.plot([0.6, 0.6], [0.5, 3.6], color=JOINT, lw=2.6)
        _arrow(ax, 0.6, 3.6, 2.35, 3.6, colour=JOINT, lw=2.0)
        ax.plot([2.6, 0.6], [0.5, 0.5], color=JOINT, lw=2.6)
        ax.text(0.45, 2.0, 'nothing rescales this path', rotation=90, ha='right',
                va='center', fontsize=10, color=JOINT)
    else:
        _box(ax, 1.4, 1.6, 2.4, 0.6, 'attention', face=_mix(LINK, 0.18), edge=LINK)
        ax.add_patch(plt.Circle((2.6, 3.0), 0.22, facecolor='white', edgecolor=JOINT, lw=1.8))
        ax.text(2.6, 3.0, '+', ha='center', va='center', fontsize=13, color=JOINT)
        _box(ax, 1.4, 3.8, 2.4, 0.6, 'normalise', face=_mix(TEAL, 0.18), edge=TEAL)
        _arrow(ax, 2.6, 0.3, 2.6, 1.55, colour=INK)
        _arrow(ax, 2.6, 2.22, 2.6, 2.75, colour=INK)
        _arrow(ax, 2.6, 3.24, 2.6, 3.75, colour=INK)
        _arrow(ax, 2.6, 4.42, 2.6, 4.9, colour=INK)
        ax.plot([0.6, 0.6], [0.5, 3.0], color=JOINT, lw=2.6)
        _arrow(ax, 0.6, 3.0, 2.35, 3.0, colour=JOINT, lw=2.0)
        ax.plot([2.6, 0.6], [0.5, 0.5], color=JOINT, lw=2.6)
        ax.text(0.45, 1.75, 'this path is rescaled\nat every block', rotation=90,
                ha='right', va='center', fontsize=10, color=GRIP)
    ax.text(2.6, 0.08, 'the stream arrives', ha='center', va='top', fontsize=9.5,
            color=MUTED)
    ax.text(2.6, 5.0, 'the stream leaves', ha='center', va='bottom', fontsize=9.5,
            color=MUTED)
    ax.set_xlim(-1.3, 4.4)
    ax.set_ylim(-0.5, 5.5)
    _fit(fig, ax)
    _title(fig, title)
    _save(fig, BLK_DOC, name)


def pre_norm_order() -> None:
    _norm_order_drawing('pre', 'pre-norm-order.svg',
                        'Pre-norm: normalise the branch, then add it on')


def post_norm_order() -> None:
    _norm_order_drawing('post', 'post-norm-order.svg',
                        'Post-norm: add the branch on, then normalise everything')


def depth_experiment() -> tuple[list[float], list[float], list[float], list[float]]:
    """Run a chain of random blocks both ways and watch the sizes change."""
    depth, width = 48, 64
    rng = np.random.default_rng(7)
    Ws = [rng.normal(0.0, 1.0, (width, width)) / math.sqrt(width) for _ in range(depth)]
    x0 = rng.normal(0.0, 1.0, width)
    eps = 1e-6
    dirn = rng.normal(0.0, 1.0, width)
    dirn /= np.linalg.norm(dirn)

    def run(mode: str, start: Arr) -> list[Arr]:
        x = start.copy()
        out = [x.copy()]
        for W in Ws:
            if mode == 'pre':
                x = x + W @ (x / math.sqrt((x ** 2).mean()))
            else:
                y = x + W @ x
                x = y / math.sqrt((y ** 2).mean())
            out.append(x.copy())
        return out

    pre = run('pre', x0)
    post = run('post', x0)
    pre_p = run('pre', x0 + eps * dirn)
    post_p = run('post', x0 + eps * dirn)
    pre_size = [float(np.sqrt((v ** 2).mean())) for v in pre]
    post_size = [float(np.sqrt((v ** 2).mean())) for v in post]
    pre_sens = [float(np.linalg.norm(a - b) / eps) for a, b in zip(pre_p, pre)]
    post_sens = [float(np.linalg.norm(a - b) / eps) for a, b in zip(post_p, post)]
    print(f'[depth] simulated chain of {depth} random blocks, width {width}')
    for lab, arr in (('pre-norm stream size', pre_size), ('post-norm stream size', post_size),
                     ('pre-norm sensitivity', pre_sens), ('post-norm sensitivity', post_sens)):
        picks = [0, 1, 4, 12, 24, 48]
        print(f'[depth] {lab:22s} ' + '  '.join(f'block {p}: {arr[p]:.3g}' for p in picks))
    return pre_size, post_size, pre_sens, post_sens


def stream_size_through_depth() -> None:
    """Idea one: what the two orders do to the size of the stream."""
    pre_size, post_size, _, _ = depth_experiment()
    depth = len(pre_size) - 1
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(range(depth + 1), pre_size, color=TEAL, lw=2.2, label='pre-norm')
    ax.plot(range(depth + 1), post_size, color=GRIP, lw=2.2, label='post-norm')
    ax.plot(range(depth + 1), [math.sqrt(1 + i) for i in range(depth + 1)], ls='--',
            color=MUTED, lw=1.2, label='the square root of the depth')
    ax.text(depth + 0.8, pre_size[-1], f'{pre_size[-1]:.2f}', ha='left', va='center',
            fontsize=10, color=TEAL)
    ax.text(depth + 0.8, post_size[-1], f'{post_size[-1]:.2f}', ha='left', va='center',
            fontsize=10, color=GRIP)
    ax.set_xlim(-1.5, depth + 5.0)
    ax.set_xlabel('blocks passed', fontsize=10)
    ax.set_ylabel('typical size of the numbers in the stream', fontsize=10)
    ax.set_ylim(0, max(pre_size) * 1.2)
    ax.set_title(f'{depth} simulated blocks: pre-norm lets the stream grow, post-norm '
                 'pins it', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'stream-size-through-depth.svg')


def nudge_through_depth() -> None:
    """Idea two: how far a small change at the bottom travels in each order."""
    _, _, pre_sens, post_sens = depth_experiment()
    depth = len(pre_sens) - 1
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(range(depth + 1), pre_sens, color=TEAL, lw=2.2, label='pre-norm')
    ax.plot(range(depth + 1), post_sens, color=GRIP, lw=2.2, label='post-norm')
    ax.axhline(1.0, color=MUTED, ls=':', lw=1.0)
    ax.text(depth, pre_sens[-1] * 1.1, f'{pre_sens[-1]:.2f} times', ha='right',
            va='bottom', fontsize=10, color=TEAL)
    ax.text(depth, post_sens[-1] * 0.88, f'{post_sens[-1]:.2f} times', ha='right',
            va='top', fontsize=10, color=GRIP)
    ax.set_yscale('log')
    ax.set_xlabel('blocks passed', fontsize=10)
    ax.set_ylabel('how much the same small nudge has moved things', fontsize=10)
    ax.set_title(f'One nudge at the bottom, carried up through {depth} blocks',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'nudge-through-depth.svg')


# --------------------------------------------------------------------------
# page 2, section 3: the residual add
# --------------------------------------------------------------------------

def residual_add_arithmetic() -> None:
    b = BLOCK
    fig, ax = plt.subplots(figsize=(10.6, 3.3), facecolor='white')
    _blank(ax)
    rows = [f'"{t}"' for t in TOKENS]
    w1, h = _grid(ax, b.x, cw=1.05, ch=0.64, fmt='{:+.1f}', rows=rows,
                  title='the stream going in', box=JOINT)
    w2, _ = _grid(ax, b.attn, x0=w1 + 1.0, cw=1.05, ch=0.64, title='what attention gives')
    w3, _ = _grid(ax, b.s1, x0=w1 + w2 + 2.0, cw=1.05, ch=0.64,
                  title='the stream coming out', box=JOINT)
    ax.text(w1 + 0.5, -h / 2, '+', ha='center', va='center', fontsize=15, color=JOINT)
    ax.text(w1 + w2 + 1.5, -h / 2, '=', ha='center', va='center', fontsize=15, color=JOINT)
    ax.text((w1 + w2 + w3 + 3.0) / 2, -h - 0.3,
            f'the first row reads {b.x[0, 0]:+.1f} {b.attn[0, 0]:+.2f} = {b.s1[0, 0]:+.2f}, '
            'and so on for all sixteen numbers',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-1.3, w1 + w2 + w3 + 2.3)
    ax.set_ylim(-h - 1.0, 0.9)
    _fit(fig, ax)
    _title(fig, 'The residual add: the block is added to the stream, not put in its place')
    _save(fig, BLK_DOC, 'residual-add-arithmetic.svg')


def stream_experiment() -> tuple[list[float], list[float]]:
    depth, width = 12, 64
    rng = np.random.default_rng(11)
    Ws = [rng.normal(0.0, 1.0, (width, width)) / math.sqrt(width) for _ in range(depth)]
    x = rng.normal(0.0, 1.0, width)
    adds: list[float] = []
    sizes: list[float] = [float(np.sqrt((x ** 2).mean()))]
    for W in Ws:
        add = W @ (x / math.sqrt((x ** 2).mean()))
        adds.append(float(np.sqrt((add ** 2).mean())))
        x = x + add
        sizes.append(float(np.sqrt((x ** 2).mean())))
    print(f'[stream] simulated {depth} pre-norm blocks, width {width}')
    print('[stream] what each block adds ', [round(v, 3) for v in adds])
    print('[stream] stream size after each', [round(v, 3) for v in sizes])
    print('[stream] share of the stream each block adds',
          [round(a / s, 3) for a, s in zip(adds, sizes[1:])])
    return adds, sizes


def stream_is_a_sum() -> None:
    adds, sizes = stream_experiment()
    depth = len(adds)
    fig, ax = plt.subplots(figsize=(9.8, 4.2), facecolor='white')
    _plain(ax)
    ax.bar(range(1, depth + 1), adds, color=_mix(PURPLE, 0.45), edgecolor=PURPLE,
           width=0.6, label='what that block adds')
    ax.plot(range(depth + 1), sizes, color=JOINT, lw=2.4, marker='o',
            label='size of the stream')
    for i, s in enumerate(sizes):
        if i % 3 == 0:
            ax.text(i, s + 0.06, f'{s:.2f}', ha='center', va='bottom', fontsize=9, color=INK)
    ax.set_xticks(range(depth + 1))
    ax.set_xlabel('block number', fontsize=10)
    ax.set_ylabel('typical size of the numbers', fontsize=10)
    ax.set_ylim(0, max(sizes) * 1.25)
    ax.set_title('Twelve simulated blocks: the stream is the start plus every addition',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'stream-is-a-sum.svg')


def how_much_each_block_changes() -> None:
    adds, sizes = stream_experiment()
    share = [a / s for a, s in zip(adds, sizes[1:])]
    fig, ax = plt.subplots(figsize=(9.8, 4.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(1, len(share) + 1), [100 * v for v in share],
                  color=_mix(LINK, 0.45), edgecolor=LINK, width=0.6)
    for b, v in zip(bars, share):
        ax.text(b.get_x() + b.get_width() / 2, 100 * v + 0.6, f'{100 * v:.0f}%',
                ha='center', va='bottom', fontsize=9.5, color=INK)
    ax.set_xticks(range(1, len(share) + 1))
    ax.set_xlabel('block number', fontsize=10)
    ax.set_ylabel('its addition as a share of the stream', fontsize=10)
    ax.set_ylim(0, max(100 * v for v in share) * 1.25)
    ax.set_title('Each block nudges the stream; none of them replaces it',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'how-much-each-block-changes.svg')


def additions_partly_cancel() -> None:
    """Why twelve additions of size 1 do not give a stream of size 12."""
    adds, sizes = stream_experiment()
    depth = len(adds)
    aligned = [sizes[0]]
    for a in adds:
        aligned.append(aligned[-1] + a)
    root = [sizes[0] * math.sqrt(1 + i) for i in range(depth + 1)]
    print(f'[cancel] if every addition pointed the same way the stream would reach '
          f'{aligned[-1]:.2f}; it actually reaches {sizes[-1]:.2f}')
    fig, ax = plt.subplots(figsize=(9.4, 4.2), facecolor='white')
    _plain(ax)
    ax.plot(range(depth + 1), aligned, color=GRIP, lw=2.2, marker='o',
            label='if every addition pointed the same way')
    ax.plot(range(depth + 1), sizes, color=JOINT, lw=2.4, marker='o',
            label='what the simulated stream actually does')
    ax.plot(range(depth + 1), root, ls='--', color=MUTED, lw=1.2,
            label='the start times the square root of the count')
    ax.text(depth, aligned[-1] + 0.3, f'{aligned[-1]:.2f}', ha='right', va='bottom',
            fontsize=10.5, color=GRIP)
    ax.text(depth, sizes[-1] + 0.4, f'{sizes[-1]:.2f}', ha='right', va='bottom',
            fontsize=10.5, color=JOINT)
    ax.set_xticks(range(depth + 1))
    ax.set_xlabel('blocks passed', fontsize=10)
    ax.set_ylabel('typical size of the numbers in the stream', fontsize=10)
    ax.set_ylim(0, aligned[-1] * 1.18)
    ax.set_title(f'{depth} additions of size about 1 give a stream of {sizes[-1]:.2f}, '
                 f'not of {aligned[-1]:.2f}', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'additions-partly-cancel.svg')


# --------------------------------------------------------------------------
# page 2, section 4: the feed-forward part
# --------------------------------------------------------------------------

def feed_forward_middle_numbers() -> None:
    b = BLOCK
    row = 0
    hid, out = b.hidden[row], b.hidden_gelu[row]
    print(f'[ff] token "{TOKENS[row]}" in ', np.round(b.n2[row], 2))
    print('[ff] 16 hidden numbers       ', np.round(hid, 2))
    print('[ff] after the smooth rule   ', np.round(out, 2))
    print(f'[ff] how many of the 16 went to almost nothing: '
          f'{int((out < 0.01).sum())} of 16')
    print('[ff] back down to four       ', np.round(b.ff[row], 2))
    fig, ax = plt.subplots(figsize=(10.4, 4.0), facecolor='white')
    _plain(ax)
    ax.bar(np.arange(16) - 0.19, hid, width=0.38, color=_mix(MUTED, 0.5),
           edgecolor=MUTED, label='the 16 widened numbers')
    ax.bar(np.arange(16) + 0.19, out, width=0.38, color=_mix(PURPLE, 0.5),
           edgecolor=PURPLE, label='after the smooth rule')
    ax.axhline(0, color=INK, lw=0.8)
    quiet = int((out < 0.01).sum())
    ax.set_xticks(range(16))
    ax.set_xticklabels([str(i + 1) for i in range(16)], fontsize=9)
    ax.set_xlabel('which of the 16 middle numbers', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title(f'The smooth rule leaves {quiet} of the 16 detectors at almost nothing, '
                 f'for "{TOKENS[row]}"', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'feed-forward-middle-numbers.svg')


def feed_forward_shape() -> None:
    """The same token as four numbers, then sixteen, then four again."""
    b = BLOCK
    row = 0
    out = b.hidden_gelu[row]
    fig, ax = plt.subplots(figsize=(11.0, 2.8), facecolor='white')
    _blank(ax)
    w1, h = _grid(ax, b.n2[row].reshape(1, 4), cw=1.0, ch=0.62, rows=['4 numbers in'],
                  rowsize=9.5)
    x = w1 + 2.2
    w2, _ = _grid(ax, out.reshape(1, 16), x0=x, cw=0.62, ch=0.62, fmt='{:+.1f}',
                  fontsize=7.5, colour=PURPLE)
    ax.text(x + w2 / 2, 0.12, '16 numbers in the middle', ha='center', va='bottom',
            fontsize=9.5, color=PURPLE)
    _arrow(ax, w1 + 0.3, -h / 2, x - 0.3, -h / 2, colour=MUTED, lw=1.2,
           label='widen', dy=0.12)
    x2 = x + w2 + 2.2
    _grid(ax, b.ff[row].reshape(1, 4), x0=x2, cw=1.0, ch=0.62, title='4 numbers out')
    _arrow(ax, x + w2 + 0.3, -h / 2, x2 - 0.3, -h / 2, colour=MUTED, lw=1.2,
           label='narrow', dy=0.12)
    ax.set_xlim(-2.4, x2 + 4.3)
    ax.set_ylim(-h - 0.35, 0.6)
    _fit(fig, ax)
    _title(fig, f'The token "{TOKENS[0]}" goes in as four numbers and comes out as four')
    _save(fig, BLK_DOC, 'feed-forward-shape.svg')


def two_matrices_collapse() -> None:
    """With nothing between them, the two matrices are one matrix."""
    b, t = BLOCK, TOY
    prod = t.W1 @ t.W2
    row = b.n2[0]
    two_steps = (row @ t.W1) @ t.W2
    one_step = row @ prod
    print('[collapse] W1 @ W2 (4 by 4)\n', np.round(prod, 3))
    print('[collapse] widen then narrow with no rule in between', np.round(two_steps, 3))
    print('[collapse] the one matrix, straight                 ', np.round(one_step, 3))
    fig, ax = plt.subplots(figsize=(10.6, 3.6), facecolor='white')
    _blank(ax)
    w1, h = _grid(ax, prod, cw=1.15, ch=0.68, fmt='{:+.2f}',
                  title='W_1 times W_2, worked out once: one 4 by 4 matrix')
    ax.text(w1 / 2, -h - 0.25, 'the smooth rule is what stops this happening',
            ha='center', va='top', fontsize=10, color=INK)
    x = w1 + 1.4
    _grid(ax, two_steps.reshape(1, 4), x0=x, y0=-0.3, cw=1.15, ch=0.62, fmt='{:+.3f}',
          title='widen, then narrow, with no rule between')
    _grid(ax, one_step.reshape(1, 4), x0=x, y0=-1.7, cw=1.15, ch=0.62, fmt='{:+.3f}',
          title='the one matrix on its own')
    ax.text(x + 2.3, -2.6, f'the same four numbers out, for the token "{TOKENS[0]}"',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-0.4, x + 4.9)
    ax.set_ylim(-h - 0.85, 0.85)
    _fit(fig, ax)
    _title(fig, 'Two matrices with nothing between them collapse into one')
    _save(fig, BLK_DOC, 'two-matrices-collapse.svg')


def model_counts(d: int = 768, L: int = 12, h: int = 12, dff: int = 3072,
                 vocab: int = 32000, quiet: bool = False) -> dict[str, int]:
    attn = 4 * d * d
    ff = 2 * d * dff
    norms = 2 * d
    block = attn + ff + norms
    emb = vocab * d
    total = L * block + emb + d
    c = {'attn': attn, 'ff': ff, 'norms': norms, 'block': block, 'blocks': L * block,
         'emb': emb, 'final': d, 'total': total}
    if not quiet:
        print(f'[count] width {d}, {L} blocks, {h} heads of {d // h}, '
              f'feed-forward width {dff}, vocabulary {vocab:,}')
        print(f'[count] attention in one block   4 x {d} x {d} = {attn:,}')
        print(f'[count] feed-forward in one block 2 x {d} x {dff} = {ff:,}')
        print(f'[count] two normalisations        2 x {d} = {norms:,}')
        print(f'[count] one block                 {block:,} '
              f'(feed-forward is {100 * ff / block:.1f} per cent)')
        print(f'[count] {L} blocks                {L * block:,}')
        print(f'[count] embedding table           {vocab:,} x {d} = {emb:,}')
        print(f'[count] final normalisation       {d:,}')
        print(f'[count] whole model               {total:,} = {total / 1e6:.2f} million')
        print(f'[count] at two bytes each         {2 * total:,} bytes = '
              f'{2 * total / 2**20:.1f} MiB')
    return c


def widen_then_narrow() -> None:
    d, dff = 768, 3072
    c = model_counts(quiet=True)
    fig, ax = plt.subplots(figsize=(11.4, 4.2), facecolor='white')
    _blank(ax)
    ax.add_patch(Rectangle((0.0, -0.5), 0.8, 1.0, facecolor=_mix(JOINT, 0.3),
                           edgecolor=JOINT, lw=1.3))
    ax.text(0.4, -0.75, f'{d} numbers', ha='center', va='top', fontsize=10, color=INK)
    ax.add_patch(Rectangle((4.6, -2.0), 0.8, 4.0, facecolor=_mix(PURPLE, 0.3),
                           edgecolor=PURPLE, lw=1.3))
    ax.text(5.0, -2.25, f'{dff} numbers', ha='center', va='top', fontsize=10, color=INK)
    ax.add_patch(Rectangle((10.0, -0.5), 0.8, 1.0, facecolor=_mix(JOINT, 0.3),
                           edgecolor=JOINT, lw=1.3))
    ax.text(10.4, -0.75, f'{d} numbers', ha='center', va='top', fontsize=10, color=INK)
    _arrow(ax, 1.0, 0.0, 4.4, 0.0, colour=MUTED, lw=1.6)
    ax.text(2.7, 0.25, f'first matrix, {d} x {dff}\n{d * dff:,} numbers', ha='center',
            va='bottom', fontsize=10, color=INK)
    _arrow(ax, 5.6, 0.0, 9.8, 0.0, colour=MUTED, lw=1.6)
    ax.text(7.7, 0.25, f'second matrix, {dff} x {d}\n{dff * d:,} numbers', ha='center',
            va='bottom', fontsize=10, color=INK)
    ax.text(5.4, -3.1, f'the two matrices together hold {c["ff"]:,} numbers, which is '
            f'{100 * c["ff"] / c["block"]:.1f} per cent of the {c["block"]:,} in one block',
            ha='center', va='top', fontsize=10, color=INK)
    ax.text(5.0, 2.25, 'the smooth rule is applied here, to each of the 3,072 on its own',
            ha='center', va='bottom', fontsize=9.5, color=PURPLE)
    ax.set_xlim(-0.4, 11.4)
    ax.set_ylim(-3.9, 2.9)
    _fit(fig, ax)
    _title(fig, 'The feed-forward part widens by four, then narrows back')
    _save(fig, BLK_DOC, 'widen-then-narrow.svg')


def where_the_parameters_sit() -> None:
    c = model_counts(quiet=True)
    names = ['attention\n(4 matrices)', 'feed-forward\n(2 matrices)', 'the two\nnormalisations']
    vals = [c['attn'], c['ff'], c['norms']]
    fig, ax = plt.subplots(figsize=(9.2, 4.2), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(3), vals, color=[_mix(LINK, 0.45), _mix(PURPLE, 0.45),
                                         _mix(TEAL, 0.45)],
                  edgecolor=[LINK, PURPLE, TEAL], width=0.6)
    for b, v in zip(bars, vals):
        share = 100 * v / c['block']
        ax.text(b.get_x() + b.get_width() / 2, v * 1.02, f'{v:,}\n'
                f'{share:.1f}%' if share >= 1 else f'{v:,}\n{share:.2f}%',
                ha='center', va='bottom', fontsize=10, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_yscale('log')
    ax.set_ylim(300, c['ff'] * 6)
    ax.set_ylabel('numbers held (log scale)', fontsize=10)
    ax.set_title(f'Where the {c["block"]:,} numbers of one block sit, at width 768',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'where-the-parameters-sit.svg')


def gated_feed_forward() -> None:
    d = 768
    plain_dff, gated_dff = 3072, 2048
    plain = 2 * d * plain_dff
    gated = 3 * d * gated_dff
    print(f'[gated] plain: 2 x {d} x {plain_dff} = {plain:,}')
    print(f'[gated] gated: 3 x {d} x {gated_dff} = {gated:,}')
    print(f'[gated] difference: {gated - plain:,}')
    fig, ax = plt.subplots(figsize=(11.6, 3.9), facecolor='white')
    _blank(ax)
    for x0, title, mats, dff, total in (
            (0.0, 'the plain kind', ['widen', 'narrow'], plain_dff, plain),
            (7.0, 'the gated kind', ['widen', 'gate', 'narrow'], gated_dff, gated)):
        step = 2.1
        for k, m in enumerate(mats):
            ax.add_patch(Rectangle((x0 + k * step, -1.1), 1.2, 2.2,
                                   facecolor=_mix(PURPLE, 0.3), edgecolor=PURPLE, lw=1.2))
            ax.text(x0 + k * step + 0.6, 0.0, m, ha='center', va='center', fontsize=9.5,
                    color=INK, rotation=90)
            ax.text(x0 + k * step + 0.6, -1.3, f'{d} x {dff}\n{d * dff:,}', ha='center',
                    va='top', fontsize=9, color=MUTED)
        mid = x0 + (len(mats) - 1) * step / 2 + 0.6
        ax.text(mid, 1.35, title, ha='center', va='bottom', fontsize=11, color=INK,
                weight='bold')
        ax.text(mid, -2.4, f'{len(mats)} x {d} x {dff}\n= {total:,} numbers',
                ha='center', va='top', fontsize=10, color=INK)
    ax.text(6.3, -3.6, 'the middle width drops from 3,072 to 2,048 so that three matrices '
            'hold what two held', ha='center', va='top', fontsize=10, color=MUTED)
    ax.set_xlim(-0.4, 13.0)
    ax.set_ylim(-4.4, 2.0)
    _fit(fig, ax)
    _title(fig, 'A third matrix, and a narrower middle, for the same number of parameters')
    _save(fig, BLK_DOC, 'gated-feed-forward.svg')


# --------------------------------------------------------------------------
# page 2, section 5: a stack of blocks, and the whole count
# --------------------------------------------------------------------------

def stack_of_blocks() -> None:
    c = model_counts(quiet=True)
    L = 12
    fig, ax = plt.subplots(figsize=(9.6, 7.0), facecolor='white')
    _blank(ax)
    y = 0.0
    _box(ax, 2.0, y, 4.2, 0.52, 'the embedding table', face=_mix(TEAL, 0.18), edge=TEAL,
         size=10)
    ax.text(6.45, y + 0.26, f'{c["emb"]:,} numbers', ha='left', va='center', fontsize=9.5,
            color=MUTED)
    y += 0.78
    for i in range(L):
        _box(ax, 2.0, y, 4.2, 0.40, f'block {i + 1}', face=_mix(LINK, 0.14), edge=LINK,
             size=9.5)
        if i == 0:
            ax.text(6.45, y + 0.20, f'{c["block"]:,} numbers in each block', ha='left',
                    va='center', fontsize=9.5, color=MUTED)
        y += 0.56
    _box(ax, 2.0, y, 4.2, 0.46, 'one last normalisation', face=_mix(TEAL, 0.18), edge=TEAL,
         size=10)
    ax.text(6.45, y + 0.23, f'{c["final"]:,} numbers', ha='left', va='center', fontsize=9.5,
            color=MUTED)
    y += 0.74
    _box(ax, 2.0, y, 4.2, 0.46, 'the embedding table, used backwards',
         face=_mix(TEAL, 0.10), edge=TEAL, size=9.5)
    ax.text(6.45, y + 0.23, 'no new numbers', ha='left', va='center', fontsize=9.5,
            color=MUTED)
    ax.annotate('', xy=(1.6, y + 0.34), xytext=(1.6, 0.1),
                arrowprops=dict(arrowstyle='-|>', lw=2.4, color=JOINT))
    ax.text(1.35, y / 2, 'one stream, 768 numbers wide, all the way up', rotation=90,
            ha='center', va='center', fontsize=9.5, color=JOINT)
    ax.set_xlim(0.6, 11.6)
    ax.set_ylim(-0.35, y + 0.9)
    _fit(fig, ax)
    _title(fig, f'Twelve blocks on one stream: {c["total"]:,} numbers in all')
    _save(fig, BLK_DOC, 'stack-of-blocks.svg')


def whole_model_count() -> None:
    c = model_counts()
    L = 12
    parts = [('the embedding table', c['emb'], TEAL),
             ('attention, all 12 blocks', L * c['attn'], LINK),
             ('feed-forward, all 12 blocks', L * c['ff'], PURPLE),
             ('every normalisation', L * c['norms'] + c['final'], JOINT)]
    total = sum(p[1] for p in parts)
    print(f'[count] check: the four parts add to {total:,}')
    fig, ax = plt.subplots(figsize=(10.4, 3.0), facecolor='white')
    _plain(ax)
    left = 0.0
    for name, v, colour in parts:
        ax.barh([0], [v], left=[left], color=_mix(colour, 0.5), edgecolor=colour,
                height=0.55)
        if v / total > 0.05:
            ax.text(left + v / 2, 0, f'{v / 1e6:.1f}M\n{100 * v / total:.1f}%',
                    ha='center', va='center', fontsize=10, color=INK)
        left += v
    left = 0.0
    for name, v, colour in parts:
        if v / total > 0.05:
            ax.text(left + v / 2, 0.38, name, ha='center', va='bottom', fontsize=9.5,
                    color=colour)
        else:
            ax.text(total, -0.42, f'{name}: {v:,}', ha='right', va='top', fontsize=9.5,
                    color=colour)
        left += v
    ax.set_yticks([])
    ax.set_ylim(-0.75, 0.75)
    ax.set_xlim(0, total * 1.02)
    ax.set_xticks([0, 2.5e7, 5e7, 7.5e7, 1e8])
    ax.set_xticklabels(['0', '25M', '50M', '75M', '100M'])
    ax.set_xlabel('numbers held', fontsize=10)
    ax.spines['left'].set_visible(False)
    ax.set_title(f'The whole {total / 1e6:.1f} million, split four ways',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'whole-model-count.svg')


def width_and_depth() -> None:
    widths = [256, 512, 768, 1024, 1536, 2048, 4096]
    depths = [6, 12, 24, 48]
    fig, ax = plt.subplots(figsize=(9.8, 4.6), facecolor='white')
    _plain(ax)
    for L, colour in zip(depths, (TEAL, LINK, PURPLE, GRIP)):
        tot = [model_counts(d=w, L=L, h=max(w // 64, 1), dff=4 * w, quiet=True)['total']
               for w in widths]
        ax.plot(widths, [v / 1e6 for v in tot], marker='o', color=colour, lw=2,
                label=f'{L} blocks')
        print(f'[grow] {L:2d} blocks: ' +
              '  '.join(f'width {w}: {v / 1e6:.0f}M' for w, v in zip(widths, tot)))
    c = model_counts(quiet=True)
    ax.plot([768], [c['total'] / 1e6], marker='*', ms=18, color=INK)
    ax.annotate(f'the model counted above:\n768 wide, 12 blocks, {c["total"] / 1e6:.1f}M',
                xy=(790, c['total'] / 1e6), xytext=(1100, 28), fontsize=9.5, color=INK,
                ha='left', arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths])
    ax.set_xticks([], minor=True)
    ax.set_ylim(8, 2e4)
    ax.set_xlabel('width of the stream', fontsize=10)
    ax.set_ylabel('millions of numbers in the whole model', fontsize=10)
    ax.set_title('Doubling the depth doubles the count; doubling the width nearly '
                 'quadruples it', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'width-and-depth.svg')


# --------------------------------------------------------------------------
# page 2, section 6: mixture of experts
# --------------------------------------------------------------------------

def moe_counts(d: int = 768, L: int = 12, dff: int = 3072, experts: int = 8,
               k: int = 2, vocab: int = 32000, quiet: bool = False) -> dict[str, int]:
    dense = model_counts(d=d, L=L, dff=dff, vocab=vocab, quiet=True)
    one_ff = 2 * d * dff
    router = d * experts
    held_block = 4 * d * d + experts * one_ff + router + 2 * d
    used_block = 4 * d * d + k * one_ff + router + 2 * d
    held = L * held_block + vocab * d + d
    used = L * used_block + vocab * d + d
    c = {'dense_total': dense['total'], 'one_ff': one_ff, 'router': router,
         'held_block': held_block, 'used_block': used_block, 'held': held, 'used': used}
    if not quiet:
        print(f'[moe] {experts} experts per block, {k} of them used per token')
        print(f'[moe] one expert: {one_ff:,}; the router: {d} x {experts} = {router:,}')
        print(f'[moe] one block holds {held_block:,} and uses {used_block:,} per token')
        print(f'[moe] whole model holds {held:,} = {held / 1e6:.1f} million')
        print(f'[moe] whole model uses  {used:,} = {used / 1e6:.1f} million per token')
        print(f'[moe] the dense model of the same shape: {dense["total"]:,} = '
              f'{dense["total"] / 1e6:.1f} million')
        print(f'[moe] held / dense = {held / dense["total"]:.2f}, '
              f'used / dense = {used / dense["total"]:.2f}')
        print(f'[moe] memory at two bytes: dense {2 * dense["total"] / 2**20:.0f} MiB, '
              f'mixture {2 * held / 2**20:.0f} MiB')
    return c


def router_picks_two() -> None:
    rng = np.random.default_rng(3)
    scores = np.round(rng.normal(0.0, 1.2, 8), 2)
    order = np.argsort(scores)[::-1]
    top = order[:2]
    pair = scores[top]
    e = np.exp(pair - pair.max())
    wts = e / e.sum()
    print('[router] the eight router scores for one token', scores)
    print(f'[router] the two biggest are expert {top[0] + 1} ({pair[0]:+.2f}) and '
          f'expert {top[1] + 1} ({pair[1]:+.2f})')
    print(f'[router] their shares are {wts[0]:.3f} and {wts[1]:.3f}')
    fig, ax = plt.subplots(figsize=(9.8, 4.4), facecolor='white')
    _plain(ax)
    colours = [GRIP if i in top else _mix(MUTED, 0.6) for i in range(8)]
    bars = ax.bar(range(8), scores, color=[_mix(c, 0.55) for c in colours],
                  edgecolor=colours, width=0.62)
    for i, (b, v) in enumerate(zip(bars, scores)):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.06 if v >= 0 else -0.06),
                f'{v:+.2f}', ha='center', va='bottom' if v >= 0 else 'top',
                fontsize=10, color=INK)
    for rank, i in enumerate(top):
        ax.text(i, scores[i] + 0.55, f'picked\nshare {wts[rank]:.3f}', ha='center',
                va='bottom', fontsize=9.5, color=GRIP)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(8))
    ax.set_xticklabels([f'expert {i + 1}' for i in range(8)], fontsize=9.5)
    ax.set_ylim(min(scores) - 0.7, max(scores) + 1.5)
    ax.set_ylabel('router score for this one token', fontsize=10)
    ax.set_title('The router scores eight experts and keeps the best two',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'router-picks-two.svg')


def held_versus_used() -> None:
    c = moe_counts()
    names = ['the plain model', 'the mixture model:\nnumbers held',
             'the mixture model:\nnumbers used per token']
    vals = [c['dense_total'], c['held'], c['used']]
    colours = [LINK, GRIP, PURPLE]
    fig, ax = plt.subplots(figsize=(9.4, 4.4), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(3), [v / 1e6 for v in vals],
                  color=[_mix(col, 0.5) for col in colours], edgecolor=colours, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v / 1e6 + 8, f'{v / 1e6:.0f} million',
                ha='center', va='bottom', fontsize=10.5, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, c['held'] / 1e6 * 1.18)
    ax.set_ylabel('millions of numbers', fontsize=10)
    ax.set_title(f'Eight experts per block: {c["held"] / c["dense_total"]:.1f} times the '
                 f'parameters, {c["used"] / c["dense_total"]:.1f} times the work per token',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'held-versus-used.svg')


def memory_cost() -> None:
    c = moe_counts(quiet=True)
    opts = [('plain model,\n2 bytes each', 2 * c['dense_total'], LINK),
            ('mixture model,\n2 bytes each', 2 * c['held'], GRIP),
            ('mixture model,\n1 byte each', 1 * c['held'], WRIST)]
    for name, v, _ in opts:
        print(f'[memory] {name.replace(chr(10), " ")}: {v:,} bytes = {v / 2**20:.0f} MiB')
    fig, ax = plt.subplots(figsize=(9.0, 4.2), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(3), [v / 2**20 for v in opts and [o[1] for o in opts]],
                  color=[_mix(o[2], 0.5) for o in opts],
                  edgecolor=[o[2] for o in opts], width=0.6)
    for b, (name, v, _) in zip(bars, opts):
        ax.text(b.get_x() + b.get_width() / 2, v / 2**20 + 20, f'{v / 2**20:.0f} MiB',
                ha='center', va='bottom', fontsize=10.5, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels([o[0] for o in opts], fontsize=10)
    ax.set_ylim(0, max(o[1] for o in opts) / 2**20 * 1.2)
    ax.set_ylabel('memory the weights take up (MiB)', fontsize=10)
    ax.set_title('Every expert has to be in memory, whether a token uses it or not',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'memory-cost.svg')


def expert_load() -> None:
    rng = np.random.default_rng(19)
    n_tok, experts, k = 4096, 8, 2
    bias = rng.normal(0.0, 0.55, experts)
    scores = rng.normal(0.0, 1.0, (n_tok, experts)) + bias
    picks = np.argsort(-scores, axis=1)[:, :k]
    counts = np.bincount(picks.reshape(-1), minlength=experts)
    fair = n_tok * k / experts
    print(f'[load] {n_tok} tokens, {k} experts each, so a fair share is {fair:.0f} tokens')
    print('[load] tokens per expert', counts.tolist())
    print(f'[load] busiest expert {counts.max()} = {counts.max() / fair:.2f} times a fair '
          f'share, quietest {counts.min()} = {counts.min() / fair:.2f} times')
    fig, ax = plt.subplots(figsize=(9.6, 4.2), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(experts), counts, color=_mix(TEAL, 0.5), edgecolor=TEAL, width=0.62)
    for b, v in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, v + 30, f'{v}', ha='center', va='bottom',
                fontsize=10, color=INK)
    ax.axhline(fair, color=GRIP, ls='--', lw=1.4)
    ax.text(experts - 0.4, fair + 40, f'a fair share: {fair:.0f}', ha='right', va='bottom',
            fontsize=9.5, color=GRIP)
    ax.set_xticks(range(experts))
    ax.set_xticklabels([f'{i + 1}' for i in range(experts)], fontsize=10)
    ax.set_xlabel('expert', fontsize=10)
    ax.set_ylabel(f'tokens sent to it, out of {n_tok}', fontsize=10)
    ax.set_ylim(0, counts.max() * 1.25)
    ax.set_title('A simulated router left to itself: some experts get far more work',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BLK_DOC, 'expert-load.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)

    report_toy()
    token_vectors()
    same_token_two_sentences()
    one_token_draws_from_four()
    before_and_after()
    convolution_weight_grid()
    projection_matrices()
    one_query_worked_out()
    qkv_grids()
    query_meets_key()
    dot_product_worked_out()
    dot_product_vs_angle()
    raw_score_grid()
    scaled_score_grid()
    score_spread_vs_head_size()
    sharpness_vs_head_size()
    softmax_steps()
    softmax_sharpness()
    weight_grid()
    output_mix_worked_out()
    attention_as_matrices()
    shape_chain()
    split_into_heads()
    two_heads_two_patterns()
    join_the_heads()
    head_count_shapes()
    self_and_cross()
    mask_grid()
    mask_arithmetic()
    robot_model_attention()
    score_grid_grows()
    cost_vs_length()
    score_memory()

    report_block()
    six_steps()
    numbers_through_a_block()
    size_of_each_change()
    rms_norm_worked_out()
    token_sizes_before_and_after()
    pre_norm_order()
    post_norm_order()
    stream_size_through_depth()
    nudge_through_depth()
    residual_add_arithmetic()
    stream_is_a_sum()
    how_much_each_block_changes()
    additions_partly_cancel()
    feed_forward_middle_numbers()
    feed_forward_shape()
    two_matrices_collapse()
    model_counts()
    widen_then_narrow()
    where_the_parameters_sit()
    gated_feed_forward()
    stack_of_blocks()
    whole_model_count()
    width_and_depth()
    moe_counts()
    router_picks_two()
    held_versus_used()
    memory_cost()
    expert_load()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
