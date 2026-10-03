"""Generate the diagrams for the first two pages of docs/06_neural-networks/06_the-transformer/.

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
    fig, ax = plt.subplots(figsize=(7.4, 2.9), facecolor='white')
    _blank(ax)
    w, h = _grid(ax, TOY.X, cw=1.25, ch=0.7, rows=[f'"{t}"' for t in TOKENS], cols=cols)
    ax.set_xlim(-1.6, w + 0.3)
    ax.set_ylim(-h - 0.35, 0.95)
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
        ax.text(3.3, y + 0.04 + 0.52 * (1.26 - y - 0.04) / 1.0 + 0.02,
                f'{wts[i]:.3f}', ha='center', va='bottom', fontsize=10.5, color=INK)
    _box(ax, 5.5, 1.0, 2.9, 0.56, 'new vector for "cube"', face=_mix(JOINT, 0.18), size=10.5)
    ax.text(2.2, -0.65, 'the four numbers add up to '
            f'{wts.sum():.3f}, so the new vector is an average of the four value vectors',
            ha='center', va='center', fontsize=10, color=MUTED)
    ax.set_xlim(-0.3, 8.7)
    ax.set_ylim(-1.0, 3.1)
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
    ax.text(w1 + 1.3 + w2 / 2, -h1 - 0.45,
            'rows 1 and 2 come out close together, because both tokens drew most of their\n'
            'mix from the same place; rows 3 and 4 stay different', ha='center',
            va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-1.5, w1 + 1.3 + w2 + 0.7 + 1.5)
    ax.set_ylim(-h1 - 1.5, 0.85)
    _title(fig, 'What attention changes: every token is replaced by a mix')
    _save(fig, ATT_DOC, 'before-and-after.svg')


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
    _title(fig, 'Every token gets three vectors of its own')
    _save(fig, ATT_DOC, 'qkv-grids.svg')


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
    ax.set_ylim(-3.6, 0.6)
    _title(fig, 'One query against four keys: four dot products')
    _save(fig, ATT_DOC, 'dot-product-worked-out.svg')


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
    _title(fig, 'Sixteen raw scores: every query against every key')
    _save(fig, ATT_DOC, 'raw-score-grid.svg')


def scaled_score_grid() -> None:
    fig, ax = plt.subplots(figsize=(10.8, 3.4), facecolor='white')
    _blank(ax)
    rows = [f'query "{t}"' for t in TOKENS]
    w1, h = _grid(ax, TOY.raw, cw=1.2, ch=0.72, rows=rows, title='raw scores')
    w2, _ = _grid(ax, TOY.scaled, x0=w1 + 1.9, cw=1.2, ch=0.72,
                  title='after dividing by 2')
    ax.text(w1 + 0.95, -h / 2 + 0.1, 'divide', ha='center', va='bottom',
            fontsize=10, color=MUTED)
    ax.text(w1 + 0.95, -h / 2 - 0.1, 'by  4 = 2', ha='center', va='top',
            fontsize=10, color=MUTED)
    ax.plot([w1 + 0.55, w1 + 0.74], [-h / 2 - 0.30, -h / 2 - 0.30], color=MUTED, lw=1.0)
    ax.text(w1 + 1.85, -h - 0.3,
            'the biggest score drops from '
            f'{TOY.raw.max():.2f} to {TOY.scaled.max():.2f}, and every gap halves',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-2.0, w1 + 1.9 + w2 + 0.3)
    ax.set_ylim(-h - 1.1, 0.95)
    _title(fig, 'Dividing by the square root of the head size')
    _save(fig, ATT_DOC, 'why-divide-by-two.svg')


def why_divide() -> None:
    sizes = [4, 16, 64, 256, 1024]
    n_keys = 64
    spread_raw, spread_scaled, top_raw, top_scaled = [], [], [], []
    for d in sizes:
        rng = np.random.default_rng(100 + d)
        q = rng.normal(0.0, 1.0, (400, d))
        k = rng.normal(0.0, 1.0, (400, n_keys, d))
        s = np.einsum('bd,bkd->bk', q, k)
        spread_raw.append(float(s.std()))
        spread_scaled.append(float((s / math.sqrt(d)).std()))
        top_raw.append(float(_softmax(s).max(axis=1).mean()))
        top_scaled.append(float(_softmax(s / math.sqrt(d)).max(axis=1).mean()))
    print('[scale] head sizes            ', sizes)
    print('[scale] spread of raw scores  ', [round(v, 2) for v in spread_raw])
    print('[scale] spread after dividing ', [round(v, 2) for v in spread_scaled])
    print('[scale] biggest weight, raw   ', [round(v, 3) for v in top_raw])
    print('[scale] biggest weight, scaled', [round(v, 3) for v in top_scaled])

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(sizes, spread_raw, marker='o', color=GRIP, lw=2, label='raw dot product')
    ax.plot(sizes, spread_scaled, marker='o', color=TEAL, lw=2, label='after dividing by  d')
    ax.plot(sizes, [math.sqrt(d) for d in sizes], ls='--', color=MUTED, lw=1.2,
            label='the square root of the head size')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('head size (how many numbers in a query)', fontsize=10)
    ax.set_ylabel('typical spread of the scores', fontsize=10)
    ax.set_title('Raw scores grow with head size', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax = axes[1]
    _plain(ax)
    ax.plot(sizes, top_raw, marker='o', color=GRIP, lw=2, label='raw dot product')
    ax.plot(sizes, top_scaled, marker='o', color=TEAL, lw=2, label='after dividing by  d')
    ax.axhline(1.0, color=MUTED, ls=':', lw=1.0)
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_ylim(0, 1.08)
    ax.set_xlabel('head size (how many numbers in a query)', fontsize=10)
    ax.set_ylabel(f'biggest of the {n_keys} weights', fontsize=10)
    ax.set_title('Without the division, one key takes everything', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='center left')
    fig.tight_layout()
    _save(fig, ATT_DOC, 'why-divide.svg')


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
                 cols=[f'key "{t}"' for t in TOKENS], rowsize=9.5, fmt='{:+.3f}')
    ax.text(w / 2, -h - 0.25,
            f'the four raised values add up to {ex.sum():.3f}, and each weight is one of\n'
            f'them divided by that total, so the weights add up to {wts.sum():.3f}',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    ax.set_xlim(-2.4, w + 0.3)
    ax.set_ylim(-h - 1.3, 0.95)
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
    _title(fig, 'The output is the value vectors added up in those proportions')
    _save(fig, ATT_DOC, 'output-mix-worked-out.svg')


def attention_as_matrices() -> None:
    fig, ax = plt.subplots(figsize=(12.0, 3.6), facecolor='white')
    _blank(ax)
    x = 0.0
    pieces = [('X\n4 x 4', TOY.X, '{:+.1f}'), ('Q\n4 x 4', TOY.Q, '{:+.2f}'),
              ('scores\n4 x 4', TOY.scaled, '{:+.2f}'), ('weights\n4 x 4', TOY.A, '{:.2f}'),
              ('output\n4 x 4', TOY.O, '{:+.2f}')]
    steps = ['times W_query,\nW_key, W_value', 'Q times K\nturned on its side,\ndivided by 2',
             'softmax\nalong each row', 'times V']
    for n, (name, M, fmt) in enumerate(pieces):
        colour = TEAL if 'weights' in name else None
        w, h = _grid(ax, M, x0=x, cw=0.78, ch=0.5, fmt=fmt, fontsize=7.5,
                     colour=colour, vmax=1.0 if colour else None)
        ax.text(x + w / 2, -h - 0.18, name, ha='center', va='top', fontsize=10,
                color=INK, weight='bold')
        if n < 4:
            _arrow(ax, x + w + 0.18, -h / 2, x + w + 1.55, -h / 2, colour=MUTED, lw=1.2)
            ax.text(x + w + 0.87, -h / 2 + 0.22, steps[n], ha='center', va='bottom',
                    fontsize=8.5, color=MUTED)
        x += w + 1.75
    ax.set_xlim(-0.3, x - 0.9)
    ax.set_ylim(-h - 1.6, 1.2)
    _title(fig, 'The whole of attention for all four tokens: four matrix multiplies and one softmax')
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
        wd = 1.0 if b == d else 1.6
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
    ax.set_ylim(-3.6, 0.9)
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
    _title(fig, 'Minus infinity becomes a weight of exactly zero')
    _save(fig, ATT_DOC, 'mask-arithmetic.svg')


def robot_model_attention() -> None:
    groups = [('picture tokens', 256, LINK), ('words of the order', 12, TEAL),
              ('joint readings', 1, JOINT), ('action tokens', 8, GRIP)]
    total = sum(g[1] for g in groups)
    allowed = np.array([[1, 1, 0, 0],
                        [1, 1, 0, 0],
                        [1, 1, 1, 0],
                        [1, 1, 1, 1]], dtype=float)
    sizes = np.array([g[1] for g in groups], dtype=float)
    pairs = float((allowed * np.outer(sizes, sizes)).sum())
    print(f'[robot] token groups: ' + ', '.join(f'{n} {nm}' for nm, n, _ in groups))
    print(f'[robot] tokens in all: {total}, pairs in the full grid: {total * total:,}, '
          f'pairs the mask allows: {int(pairs):,} '
          f'({100 * pairs / (total * total):.1f} per cent)')
    fig, ax = plt.subplots(figsize=(8.6, 4.4), facecolor='white')
    _blank(ax)
    span = np.cumsum(np.concatenate([[0.0], sizes / total * 6.0]))
    for i in range(4):
        for j in range(4):
            face = _mix(TEAL, 0.35) if allowed[i, j] else _mix(MUTED, 0.22)
            ax.add_patch(Rectangle((span[j], -span[i + 1]), span[j + 1] - span[j],
                                   span[i + 1] - span[i], facecolor=face,
                                   edgecolor='white', lw=1.0))
    for i, (nm, n, colour) in enumerate(groups):
        ax.text(-0.15, -(span[i] + span[i + 1]) / 2, f'{nm} ({n})', ha='right',
                va='center', fontsize=9.5, color=colour)
        ax.text((span[i] + span[i + 1]) / 2, 0.12, f'{n}', ha='center', va='bottom',
                fontsize=9, color=colour)
    ax.text(3.0, 0.55, 'keys, grouped by what they are', ha='center', va='bottom',
            fontsize=10, color=MUTED)
    ax.text(3.0, -6.35, f'{total} tokens in all, so the full grid holds {total * total:,} pairs;\n'
            f'this mask allows {int(pairs):,} of them, which is '
            f'{100 * pairs / (total * total):.1f} per cent',
            ha='center', va='top', fontsize=9.5, color=INK)
    ax.text(-1.85, -3.0, 'queries', ha='center', va='center', fontsize=10,
            color=MUTED, rotation=90)
    ax.set_xlim(-2.1, 6.4)
    ax.set_ylim(-7.6, 1.0)
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
    ax.text(x - 1.2, -3.8, 'twice the tokens, four times the scores',
            ha='center', va='top', fontsize=10.5, color=INK)
    ax.set_xlim(-0.3, x - 0.7)
    ax.set_ylim(-4.4, 0.3)
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
