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
