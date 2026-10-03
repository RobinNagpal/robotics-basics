"""Generate the diagrams for the first two pages of docs/06_neural-networks/03_how-training-works/.

    01_the-score-of-being-wrong.md  -> images/how-training-works/the-score-of-being-wrong/
    02_gradient-descent.md          -> images/how-training-works/gradient-descent/

Run with:  python3 ../docs/diagrams/how_training_works_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints it so the two documents can quote the same values. Which data is made up
and which is measured:

  * The eight-row prediction table (three models guessing a travel distance),
    the five-row one-weight table, the eight grip-force readings and the
    seven-row hold-or-drop table are small tables chosen by hand so that a
    reader can redo the arithmetic. They are stated as made-up in the pages.
  * The two hundred examples used for the stochastic gradient descent pictures
    and the twenty-five examples used for the many-random-starts picture are
    drawn with numpy.random.default_rng(...) from a straight line plus noise,
    so they are simulated.
  * Everything else is measured from real arithmetic run here: the losses, the
    slopes by finite difference, every gradient descent path, the learning-rate
    sweep, the condition numbers, the spread of mini-batch gradients, the
    fraction of random symmetric matrices with every eigenvalue positive, and
    the final losses of twelve trained networks.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'how-training-works'
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

SCORE_DOC: str = 'the-score-of-being-wrong'
DESC_DOC: str = 'gradient-descent'

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


def _table(ax: Axes, headers: list[str], rows: list[list[str]],
           widths: list[float], colours: list[str] | None = None,
           fontsize: float = 10.0, row_h: float = 1.0,
           foot: list[str] | None = None) -> None:
    """Draw a small table of text. widths are relative column widths."""
    _blank(ax)
    n_row = len(rows) + (1 if foot else 0)
    total = float(sum(widths))
    edges = np.concatenate([[0.0], np.cumsum(np.array(widths, dtype=float) / total)])
    centres = (edges[:-1] + edges[1:]) / 2.0
    top = -0.3
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-(n_row + 1) * row_h - 0.55, 1.4)
    for c, (x, head) in enumerate(zip(centres, headers)):
        ax.text(x, 0.55, head, ha='center', va='center', fontsize=fontsize,
                weight='bold', color=INK, linespacing=1.4)
    ax.plot([0, 1], [-0.3, -0.3], color=INK, lw=1.2)
    for r, row in enumerate(rows):
        y = top - (r + 0.65) * row_h
        if r % 2 == 1:
            ax.add_patch(Rectangle((0, y - row_h / 2), 1, row_h, facecolor='#f4f4f4',
                                   edgecolor='none', zorder=0))
        for c, (x, cell) in enumerate(zip(centres, row)):
            col = colours[c] if colours else INK
            ax.text(x, y, cell, ha='center', va='center', fontsize=fontsize, color=col,
                    zorder=3)
    if foot:
        y = top - (len(rows) + 0.65) * row_h - 0.15
        ax.plot([0, 1], [y + row_h / 2, y + row_h / 2], color=INK, lw=1.2)
        for c, (x, cell) in enumerate(zip(centres, foot)):
            ax.text(x, y, cell, ha='center', va='center', fontsize=fontsize,
                    weight='bold', color=INK)


# --------------------------------------------------------------------------
# the made-up tables that both pages use
# --------------------------------------------------------------------------

# Eight parts on a tray. The job is to predict how far the gripper must travel
# downwards, in millimetres, before it touches the part.
TRUE8: Arr = np.array([24.0, 31.0, 18.0, 27.0, 35.0, 22.0, 29.0, 26.0])
ERR_A: Arr = np.array([2.0, -1.0, 3.0, 0.0, -2.0, 1.0, -4.0, 1.0])
ERR_B: Arr = np.array([2.0, 2.0, 2.0, 2.0, -2.0, -2.0, -2.0, -2.0])
ERR_C: Arr = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -12.0])
MODELS: list[tuple[str, Arr]] = [('model A', ERR_A), ('model B', ERR_B), ('model C', ERR_C)]

# Five parts, measured again. x is the height of the part in the camera picture
# in tens of pixels, y is the travel the arm really needed, in millimetres.
X1: Arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
Y1: Arr = np.array([3.1, 5.8, 9.2, 11.9, 15.1])
Y1_BAD: Arr = np.array([3.1, 5.8, 9.2, 11.9, 4.0])     # the last depth reading glitched

# Eight readings of the force needed to hold one particular part, in newtons.
# The last one is a sensor glitch.
FORCE7: Arr = np.array([4.8, 5.1, 4.9, 5.3, 5.0, 5.2, 4.7])
FORCE8: Arr = np.concatenate([FORCE7, [19.0]])

# Seven grips of the same part at different closing forces, and whether the
# part stayed in the gripper. The 4 N grip that held does not fit the pattern.
HOLD_F: Arr = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
HOLD_Y: Arr = np.array([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0])

CLASSES: list[str] = ['mug', 'cup', 'bowl', 'box']
CASES: list[tuple[str, Arr, int]] = [
    ('sure and right', np.array([4.0, 1.0, 0.5, 0.0]), 0),
    ('unsure and right', np.array([1.2, 1.0, 0.8, 0.5]), 0),
    ('sure and wrong', np.array([0.0, 4.0, 0.5, 1.0]), 0),
]


def mse_w(w: Arr | float, x: Arr = X1, y: Arr = Y1) -> Arr:
    """Mean squared error of the one-weight model prediction = w * x."""
    w = np.atleast_1d(np.asarray(w, dtype=float))
    return np.mean((w[:, None] * x[None, :] - y[None, :]) ** 2, axis=1)


def mae_w(w: Arr | float, x: Arr = X1, y: Arr = Y1) -> Arr:
    """Mean absolute error of the one-weight model prediction = w * x."""
    w = np.atleast_1d(np.asarray(w, dtype=float))
    return np.mean(np.abs(w[:, None] * x[None, :] - y[None, :]), axis=1)


def huber_w(w: Arr | float, delta: float = 1.0, x: Arr = X1, y: Arr = Y1) -> Arr:
    w = np.atleast_1d(np.asarray(w, dtype=float))
    e = np.abs(w[:, None] * x[None, :] - y[None, :])
    pen = np.where(e <= delta, 0.5 * e ** 2, delta * (e - 0.5 * delta))
    return np.mean(pen, axis=1)


def slope_mse(w: float, x: Arr = X1, y: Arr = Y1) -> float:
    """Exact slope of the mean squared error with respect to w."""
    return float(np.mean(2.0 * x * (w * x - y)))


def _softmax(z: Arr) -> Arr:
    e = np.exp(z - z.max())
    return e / e.sum()


def _sigmoid(z: Arr | float) -> Arr:
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


W_STAR: float = float(np.sum(X1 * Y1) / np.sum(X1 ** 2))
L_STAR: float = float(mse_w(W_STAR)[0])
A_COEF: float = float(np.mean(X1 ** 2))        # loss = A w^2 - 2 B w + C
B_COEF: float = float(np.mean(X1 * Y1))
C_COEF: float = float(np.mean(Y1 ** 2))
ETA_MAX: float = 1.0 / A_COEF                  # steps above this one diverge


# ==========================================================================
# 01_the-score-of-being-wrong.md
# ==========================================================================

# ---------------- section 1: why one number ----------------

def error_per_example() -> None:
    pred = TRUE8 + ERR_A
    print(f'[s1] true travel      {", ".join(f"{v:.0f}" for v in TRUE8)}')
    print(f'[s1] model A predicts {", ".join(f"{v:.0f}" for v in pred)}')
    print(f'[s1] model A errors   {", ".join(f"{v:+.0f}" for v in ERR_A)}')
    print(f'[s1] model A: total absolute {np.abs(ERR_A).sum():.0f} mm, '
          f'total squared {np.sum(ERR_A ** 2):.0f}, '
          f'mean absolute {np.abs(ERR_A).mean():.2f} mm, '
          f'mean squared {np.mean(ERR_A ** 2):.2f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    idx = np.arange(1, 9)
    for i, (t, p) in enumerate(zip(TRUE8, pred), start=1):
        ax.plot([i, i], [t, p], color=GRIP if abs(p - t) > 0 else MUTED, lw=2.0, zorder=1)
    ax.scatter(idx, TRUE8, s=90, color=INK, zorder=3, label='travel the arm really needed')
    ax.scatter(idx, pred, s=110, marker='X', color=LINK, zorder=3,
               label='travel the model predicted')
    for i, e in zip(idx, ERR_A):
        ax.text(i, max(TRUE8[i - 1], pred[i - 1]) + 1.0, f'{e:+.0f}', ha='center',
                fontsize=10.5, color=GRIP if e != 0 else MUTED, weight='bold')
    ax.set_xticks(idx)
    ax.set_xlabel('part on the tray', fontsize=10)
    ax.set_ylabel('downward travel (mm)', fontsize=10)
    ax.set_ylim(12, 40)
    ax.set_title('Eight predictions and eight separate mistakes, in millimetres',
                 fontsize=12.5, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.text(0.5, 0.97, 'the numbers above the lines are how wrong this model is',
            transform=ax.transAxes, fontsize=10, color=MUTED, ha='center', va='top')
    _save(fig, SCORE_DOC, 'error-per-example.svg')


def two_models_no_winner() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), facecolor='white', sharey=True)
    for ax, (name, err), colour in zip(axes, [MODELS[0], MODELS[2]], [LINK, PURPLE]):
        _plain(ax)
        idx = np.arange(1, 9)
        ax.bar(idx, err, color=colour, edgecolor=INK, lw=0.6, width=0.62)
        ax.axhline(0, color=INK, lw=1.0)
        for i, e in zip(idx, err):
            off = 0.9 if e >= 0 else -1.6
            ax.text(i, e + off, f'{e:+.0f}', ha='center', fontsize=10, color=INK)
        ax.set_xticks(idx)
        ax.set_xlabel('part on the tray', fontsize=10)
        ax.set_ylim(-13.8, 5.4)
        ax.set_title(f'{name}: errors in mm', fontsize=11.5, weight='bold', color=colour)
    axes[0].set_ylabel('error (mm)', fontsize=10)
    axes[0].text(0.6, -12.6, 'wrong by a little on seven parts', fontsize=10.5, color=INK)
    axes[1].text(0.6, -12.6, 'exactly right on seven parts, 12 mm out on one',
                 fontsize=10.5, color=INK)
    fig.suptitle('Two lists of eight mistakes that no eye can put in order',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'two-models-no-winner.svg')


def counting_versus_measuring() -> None:
    ws = np.linspace(2.0, 4.0, 1601)
    tol = 0.5
    hits = np.array([int(np.sum(np.abs(w * X1 - Y1) <= tol)) for w in ws])
    losses = mse_w(ws)
    best_count = float(ws[int(np.argmax(hits))])
    print(f'[s1] counting: the most parts inside {tol} mm is {hits.max()} of 5, '
          f'first reached at w = {best_count:.3f}')
    flat = float(np.mean(np.abs(np.diff(hits)) == 0))
    print(f'[s1] counting: the count is unchanged across {100 * flat:.1f}% of the '
          f'{len(ws) - 1} small moves in w that were tried')
    print(f'[s1] measuring: the squared-error loss changes at every one of those moves; '
          f'its lowest value is {losses.min():.4f} at w = {ws[int(np.argmin(losses))]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white')
    _plain(axes[0])
    axes[0].step(ws, hits, where='post', color=GRIP, lw=2.2)
    axes[0].set_ylim(-0.3, 5.6)
    axes[0].set_yticks(range(6))
    axes[0].set_xlabel('the one weight, w', fontsize=10)
    axes[0].set_ylabel('parts predicted within 0.5 mm', fontsize=10)
    axes[0].set_title('Counting the mistakes: flat ground with sudden jumps',
                      fontsize=11.5, weight='bold', color=GRIP)
    axes[0].annotate('from here, a small change in w\nchanges nothing to follow',
                     xy=(2.35, 0.04), xytext=(2.05, 3.3), fontsize=9.5, color=INK,
                     arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    _plain(axes[1])
    axes[1].plot(ws, losses, color=SLIDE, lw=2.4)
    axes[1].scatter([W_STAR], [L_STAR], s=80, color=INK, zorder=4)
    axes[1].text(W_STAR + 0.05, L_STAR + 1.2, f'lowest: w = {W_STAR:.3f},\n'
                 f'loss = {L_STAR:.4f}', fontsize=9.5, color=INK)
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[1].set_title('Measuring the mistakes: a slope at every value of w',
                      fontsize=11.5, weight='bold', color=SLIDE)
    fig.suptitle('The same five parts, scored two ways, as the single weight w is changed',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'counting-versus-measuring.svg')


# ---------------- section 2: squared error and absolute error ----------------

def the_error_table() -> None:
    pred = TRUE8 + ERR_A
    rows = [[f'{i}', f'{t:.0f}', f'{p:.0f}', f'{e:+.0f}', f'{e * e:.0f}', f'{abs(e):.0f}']
            for i, (t, p, e) in enumerate(zip(TRUE8, pred, ERR_A), start=1)]
    foot = ['total', '', '', f'{ERR_A.sum():+.0f}', f'{np.sum(ERR_A ** 2):.0f}',
            f'{np.abs(ERR_A).sum():.0f}']
    print(f'[s2] model A: signed errors add to {ERR_A.sum():+.0f}, '
          f'squared errors add to {np.sum(ERR_A ** 2):.0f}, '
          f'absolute errors add to {np.abs(ERR_A).sum():.0f}')
    print(f'[s2] model A: mean squared error {np.mean(ERR_A ** 2):.3f} mm^2, '
          f'root of it {np.sqrt(np.mean(ERR_A ** 2)):.3f} mm, '
          f'mean absolute error {np.abs(ERR_A).mean():.3f} mm')

    fig, ax = plt.subplots(figsize=(9.6, 5.6), facecolor='white')
    _table(ax,
           ['part', 'needed (mm)', 'predicted (mm)', 'error (mm)',
            'error squared', 'error size'],
           rows, [0.9, 1.5, 1.6, 1.3, 1.5, 1.3],
           colours=[INK, INK, LINK, GRIP, PURPLE, TEAL], fontsize=11.0, row_h=1.0,
           foot=foot)
    ax.set_title('Model A scored three ways: the signed errors cancel, '
                 'the other two columns do not',
                 fontsize=12.5, weight='bold', color=INK, pad=14)
    ax.text(0.5, -11.0, 'mean squared error = 36 / 8 = 4.50 mm$^2$        '
            'mean absolute error = 14 / 8 = 1.75 mm',
            ha='center', fontsize=11, color=INK)
    _save(fig, SCORE_DOC, 'the-error-table.svg')


def penalty_shapes() -> None:
    e = np.linspace(-5, 5, 801)
    for v in (1.0, 2.0, 4.0, 12.0):
        print(f'[s2] penalty at an error of {v:.0f} mm: squared {v * v:.0f}, '
              f'absolute {v:.0f}; squared is {v:.0f} times the absolute one')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white')
    _plain(axes[0])
    axes[0].plot(e, e ** 2, color=PURPLE, lw=2.6, label='squared error: penalty = error $\\times$ error')
    axes[0].plot(e, np.abs(e), color=TEAL, lw=2.6, label='absolute error: penalty = size of error')
    for v in (1.0, 2.0, 4.0):
        axes[0].scatter([v, v], [v * v, v], s=55, color=INK, zorder=4)
        axes[0].text(v + 0.12, v * v + 0.4, f'{v * v:.0f}', fontsize=9.5, color=PURPLE)
        axes[0].text(v + 0.12, v - 0.9, f'{v:.0f}', fontsize=9.5, color=TEAL)
    axes[0].set_xlabel('error on one part (mm)', fontsize=10)
    axes[0].set_ylabel('penalty the loss gives it', fontsize=10)
    axes[0].set_ylim(-0.6, 26)
    axes[0].set_title('The two penalty shapes', fontsize=11.5, weight='bold', color=INK)
    axes[0].legend(fontsize=9.5, frameon=False, loc='upper center')

    _plain(axes[1])
    idx = np.arange(1, 9)
    axes[1].bar(idx - 0.19, ERR_A ** 2, width=0.36, color=PURPLE, edgecolor=INK, lw=0.6,
                label='error squared')
    axes[1].bar(idx + 0.19, np.abs(ERR_A), width=0.36, color=TEAL, edgecolor=INK, lw=0.6,
                label='size of error')
    for i, v in zip(idx, ERR_A ** 2):
        axes[1].text(i - 0.19, v + 0.35, f'{v:.0f}', ha='center', fontsize=9.5, color=PURPLE)
    for i, v in zip(idx, np.abs(ERR_A)):
        axes[1].text(i + 0.19, v + 0.35, f'{v:.0f}', ha='center', fontsize=9.5, color=TEAL)
    axes[1].set_xticks(idx)
    axes[1].set_xlabel('part on the tray', fontsize=10)
    axes[1].set_ylabel('penalty', fontsize=10)
    axes[1].set_ylim(0, 24.5)
    axes[1].set_title("Model A's eight errors under both penalties", fontsize=11.5,
                      weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.suptitle('Squaring an error of 4 mm gives it four times the weight that its '
                 'size alone would\nPart 7, the one 4 mm miss, is 16 of the squared '
                 'total of 36 but only 4 of the absolute total of 14',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'penalty-shapes.svg')


def three_models_two_rankings() -> None:
    sq = {n: float(np.sum(e ** 2)) for n, e in MODELS}
    ab = {n: float(np.sum(np.abs(e))) for n, e in MODELS}
    order_sq = sorted(sq, key=lambda k: sq[k])
    order_ab = sorted(ab, key=lambda k: ab[k])
    for n, e in MODELS:
        print(f'[s2] {n}: absolute total {ab[n]:.0f} mm, squared total {sq[n]:.0f}, '
              f'mean absolute {ab[n] / 8:.2f} mm, mean squared {sq[n] / 8:.2f}')
    print('[s2] order by absolute error: ' + ' < '.join(f'{k} ({ab[k]:.0f})' for k in order_ab))
    print('[s2] order by squared error:  ' + ' < '.join(f'{k} ({sq[k]:.0f})' for k in order_sq))

    fig = plt.figure(figsize=(11.8, 6.4), facecolor='white')
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1.0], hspace=0.55, wspace=0.28)
    cols = [LINK, WRIST, PURPLE]
    for c, ((name, err), colour) in enumerate(zip(MODELS, cols)):
        ax = fig.add_subplot(gs[0, c])
        _plain(ax)
        ax.bar(np.arange(1, 9), err, color=colour, edgecolor=INK, lw=0.6, width=0.62)
        ax.axhline(0, color=INK, lw=1.0)
        ax.set_xticks(np.arange(1, 9))
        ax.tick_params(labelsize=8.5)
        ax.set_ylim(-13.6, 4.6)
        ax.set_xlabel('part', fontsize=9.5)
        if c == 0:
            ax.set_ylabel('error (mm)', fontsize=9.5)
        ax.set_title(f'{name}\nabsolute total {ab[name]:.0f}   squared total {sq[name]:.0f}',
                     fontsize=10.5, weight='bold', color=colour)
    for r, (label, table, order, colour) in enumerate([
            ('total of the error sizes', ab, order_ab, TEAL),
            ('total of the squared errors', sq, order_sq, PURPLE)]):
        ax = fig.add_subplot(gs[1, r])
        _plain(ax)
        names = [n for n, _ in MODELS]
        vals = [table[n] for n in names]
        ax.barh(names[::-1], vals[::-1], color=colour, edgecolor=INK, lw=0.6, height=0.55)
        for i, n in enumerate(names[::-1]):
            ax.text(table[n] + max(vals) * 0.02, i, f'{table[n]:.0f}', va='center',
                    fontsize=10, color=INK)
        ax.set_xlim(0, max(vals) * 1.22)
        ax.set_xlabel(label, fontsize=9.5)
        ax.set_title('best first: ' + ', '.join(k.replace('model ', '') for k in order),
                     fontsize=10.5, weight='bold', color=colour)
    ax = fig.add_subplot(gs[1, 2])
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.95, 'The two losses disagree', fontsize=11.5, weight='bold', color=INK,
            va='top')
    ax.text(0.0, 0.76, 'By error size:  C, then A, then B.', fontsize=10.5, color=TEAL,
            va='top')
    ax.text(0.0, 0.62, 'By squared error:  B, then A, then C.', fontsize=10.5,
            color=PURPLE, va='top')
    ax.text(0.0, 0.42, 'C is best on one and worst on the\nother, because its one 12 mm\n'
            'miss becomes 144 when squared.', fontsize=10, color=INK, va='top')
    fig.suptitle('Three models, eight parts each: picking the loss picks the winner',
                 fontsize=13, weight='bold', color=INK)
    _save(fig, SCORE_DOC, 'three-models-two-rankings.svg')


def _flat_bottom(grid: Arr, vals: Arr) -> tuple[float, float]:
    """The range of grid values whose loss is within rounding of the lowest."""
    keep = grid[vals <= vals.min() + 1e-9]
    return float(keep.min()), float(keep.max())


def one_wild_reading() -> None:
    grid = np.linspace(4.0, 8.0, 4001)
    panels = [('seven good readings', FORCE7), ('with one glitched reading', FORCE8)]
    out: dict[str, tuple[float, float, float]] = {}
    for label, data in panels:
        sq = np.array([np.mean((g - data) ** 2) for g in grid])
        ab = np.array([np.mean(np.abs(g - data)) for g in grid])
        best_sq = float(grid[int(np.argmin(sq))])
        lo_ab, hi_ab = _flat_bottom(grid, ab)
        out[label] = (best_sq, lo_ab, hi_ab)
        print(f'[s2] {label}: readings {", ".join(f"{v:.1f}" for v in data)}')
        print(f'[s2] {label}: squared error is lowest at {best_sq:.3f} N '
              f'(the average of the readings is {data.mean():.3f}); absolute error is '
              f'lowest anywhere from {lo_ab:.3f} to {hi_ab:.3f} N (the middle reading '
              f'is {np.median(data):.3f})')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    for ax, (label, data) in zip(axes, panels):
        _plain(ax)
        sq = np.array([np.mean((g - data) ** 2) for g in grid])
        ab = np.array([np.mean(np.abs(g - data)) for g in grid])
        bsq, lo_ab, hi_ab = out[label]
        ax.plot(grid, sq / sq.min(), color=PURPLE, lw=2.4)
        ax.plot(grid, ab / ab.min(), color=TEAL, lw=2.4)
        ax.axvline(bsq, color=PURPLE, ls='--', lw=1.4)
        ax.axvline(lo_ab, color=TEAL, ls=':', lw=1.8)
        ax.scatter(data, np.full(len(data), 0.97), s=90, marker='|', color=INK,
                   linewidths=2.2, clip_on=False)
        ax.text(0.03, 0.96, f'squared error, lowest at {bsq:.2f} N',
                transform=ax.transAxes, color=PURPLE, fontsize=11, weight='bold',
                va='top')
        ax.text(0.03, 0.87, f'absolute error, lowest at {lo_ab:.2f} N',
                transform=ax.transAxes, color=TEAL, fontsize=11, weight='bold',
                va='top')
        ax.set_xlim(4.0, 8.0)
        ax.set_ylim(0.95, 2.7)
        ax.set_xlabel('the one number the model gives, in newtons', fontsize=10)
        ax.set_ylabel('loss, divided by its own lowest value', fontsize=10)
        ax.set_title(f'{label}\nthe short marks along the bottom are the readings',
                     fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('One bad reading of 19 N moves the squared-error answer from 5.00 N to '
                 '6.75 N and leaves the absolute-error answer at 5.00 N',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'one-wild-reading.svg')


# ---------------- section 3: logits and softmax ----------------

def softmax_arithmetic() -> None:
    z = CASES[0][1]
    e = np.exp(z)
    tot = float(e.sum())
    p = e / tot
    for c, zi, ei, pi in zip(CLASSES, z, e, p):
        print(f'[s3] {c:5s} logit {zi:+.1f}  e^logit {ei:.4f}  '
              f'probability {ei:.4f}/{tot:.4f} = {pi:.4f}')
    print(f'[s3] the four e^logit values add to {tot:.4f}, '
          f'and the four probabilities add to {p.sum():.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.15, 1.0]})
    rows = [[c, f'{zi:+.1f}', f'{ei:.3f}', f'{ei:.3f} / {tot:.3f}', f'{pi:.4f}']
            for c, zi, ei, pi in zip(CLASSES, z, e, p)]
    foot = ['total', '', f'{tot:.3f}', '', f'{p.sum():.4f}']
    _table(axes[0], ['class', 'logit', 'e raised\nto the logit', 'divided by\nthe total',
                     'probability'],
           rows, [1.0, 0.9, 1.45, 1.75, 1.2],
           colours=[INK, LINK, WRIST, MUTED, SLIDE], fontsize=10.0, row_h=1.0, foot=foot)
    axes[0].set_title('Softmax, worked out in full', fontsize=12, weight='bold', color=INK,
                      pad=12)
    _plain(axes[1])
    xs = np.arange(4)
    axes[1].bar(xs - 0.2, z, width=0.38, color=LINK, edgecolor=INK, lw=0.6,
                label='logit (any size, either sign)')
    axes[1].bar(xs + 0.2, p * 4.0, width=0.38, color=SLIDE, edgecolor=INK, lw=0.6,
                label='probability (drawn at 4 times scale)')
    for x, zi in zip(xs, z):
        axes[1].text(x - 0.2, zi + 0.12, f'{zi:+.1f}', ha='center', fontsize=10, color=LINK)
    for x, pi in zip(xs, p):
        axes[1].text(x + 0.2, pi * 4.0 + 0.12, f'{pi:.3f}', ha='center', fontsize=10,
                     color=SLIDE)
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(CLASSES, fontsize=10.5)
    axes[1].axhline(0, color=INK, lw=1.0)
    axes[1].set_ylim(-0.4, 5.0)
    axes[1].set_ylabel('logit, and probability at 4 times scale', fontsize=9.5)
    axes[1].set_title('Four raw scores become four numbers that add to 1',
                      fontsize=12, weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, SCORE_DOC, 'softmax-arithmetic.svg')


def softmax_shift_and_spread() -> None:
    z = CASES[0][1]
    p = _softmax(z)
    p_shift = _softmax(z + 10.0)
    p_wide = _softmax(z * 2.0)
    p_flat = _softmax(z * 0.25)
    print(f'[s3] logits {z} give probabilities '
          f'{", ".join(f"{v:.4f}" for v in p)}')
    print(f'[s3] adding 10 to every logit gives '
          f'{", ".join(f"{v:.4f}" for v in p_shift)}, '
          f'largest change {np.abs(p_shift - p).max():.2e}')
    print(f'[s3] doubling every logit gives {", ".join(f"{v:.4f}" for v in p_wide)}')
    print(f'[s3] quartering every logit gives {", ".join(f"{v:.4f}" for v in p_flat)}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    xs = np.arange(4)
    _plain(axes[0])
    axes[0].bar(xs - 0.2, p, width=0.38, color=SLIDE, edgecolor=INK, lw=0.6,
                label='logits 4.0, 1.0, 0.5, 0.0')
    axes[0].bar(xs + 0.2, p_shift, width=0.38, color=LINK_PALE, edgecolor=INK, lw=0.6,
                label='the same logits plus 10')
    for x, a, b in zip(xs, p, p_shift):
        axes[0].text(x - 0.2, a + 0.02, f'{a:.3f}', ha='center', fontsize=9.5, color=INK)
        axes[0].text(x + 0.2, b + 0.02, f'{b:.3f}', ha='center', fontsize=9.5, color=INK)
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels(CLASSES, fontsize=10.5)
    axes[0].set_ylim(0, 1.12)
    axes[0].set_ylabel('probability', fontsize=10)
    axes[0].set_title('Only the gaps between logits matter', fontsize=11.5, weight='bold',
                      color=INK)
    axes[0].legend(fontsize=9.5, frameon=False, loc='upper center')
    _plain(axes[1])
    for off, vals, colour, lab in ((-0.26, p_flat, LINK, 'logits quartered'),
                                   (0.0, p, SLIDE, 'logits as they are'),
                                   (0.26, p_wide, PURPLE, 'logits doubled')):
        axes[1].bar(xs + off, vals, width=0.25, color=colour, edgecolor=INK, lw=0.6,
                    label=lab)
        for x, v in zip(xs, vals):
            axes[1].text(x + off, v + 0.02, f'{v:.2f}', ha='center', fontsize=9.0,
                         color=INK)
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(CLASSES, fontsize=10.5)
    axes[1].set_ylim(0, 1.32)
    axes[1].set_ylabel('probability', fontsize=10)
    axes[1].set_title('Stretching the logits sharpens the probabilities',
                      fontsize=11.5, weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='upper center')
    fig.suptitle('What softmax ignores, and what it reacts to',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'softmax-shift-and-spread.svg')


def three_cases_probabilities() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.4), facecolor='white', sharey=True)
    xs = np.arange(4)
    for ax, (label, z, truth) in zip(axes, CASES):
        _plain(ax)
        p = _softmax(z)
        print(f'[s4] {label:17s} logits {", ".join(f"{v:+.1f}" for v in z)}  ->  '
              f'probabilities {", ".join(f"{v:.4f}" for v in p)}  ->  '
              f'probability on the right class {p[truth]:.4f}')
        cols = [SLIDE if i == truth else LINK_PALE for i in range(4)]
        ax.bar(xs, p, color=cols, edgecolor=INK, lw=0.7, width=0.6)
        for x, v in zip(xs, p):
            ax.text(x, v + 0.025, f'{v:.3f}', ha='center', fontsize=10, color=INK)
        ax.set_xticks(xs)
        ax.set_xticklabels(CLASSES, fontsize=10.5)
        ax.set_ylim(0, 1.1)
        ax.set_title(f'{label}\nlogits ' + ', '.join(f'{v:+.1f}' for v in z),
                     fontsize=11, weight='bold', color=INK)
    axes[0].set_ylabel('probability', fontsize=10)
    fig.suptitle('The true class is mug (dark bar) in all three. '
                 'Only the probability it gets changes',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'three-cases-probabilities.svg')


# ---------------- section 4: cross-entropy ----------------

def minus_log_curve() -> None:
    p = np.linspace(0.005, 1.0, 1200)
    loss = -np.log(p)
    marks = []
    for label, z, truth in CASES:
        pr = float(_softmax(z)[truth])
        marks.append((label, pr, float(-np.log(pr))))
        print(f'[s4] {label:17s} probability {pr:.4f}  cross-entropy loss '
              f'{-np.log(pr):.4f}')
    guess = float(-np.log(0.25))
    print(f'[s4] a model that always gives every class the same 0.25 scores '
          f'{guess:.4f} on every picture')
    for pr in (0.5, 0.25, 0.1, 0.01, 0.001):
        print(f'[s4] loss at a true-class probability of {pr:g} is {-np.log(pr):.4f}')

    fig, ax = plt.subplots(figsize=(10.2, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(p, loss, color=GRIP, lw=2.6)
    ax.axhline(guess, color=MUTED, ls='--', lw=1.3)
    ax.text(0.73, guess + 0.14, f'always guessing 0.25 scores {guess:.3f}',
            fontsize=10, color=MUTED)
    cols = [SLIDE, JOINT, PURPLE]
    for (label, pr, lo), colour in zip(marks, cols):
        ax.scatter([pr], [lo], s=95, color=colour, zorder=5, edgecolor=INK, lw=0.7)
        ax.annotate(f'{label}\np = {pr:.3f}, loss = {lo:.3f}', xy=(pr, lo),
                    xytext=(pr + 0.07, lo + 0.65), fontsize=10, color=colour,
                    weight='bold',
                    arrowprops=dict(arrowstyle='->', color=colour, lw=1.2))
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 5.6)
    ax.set_xlabel('the probability the model gave to the class that was really there',
                  fontsize=10)
    ax.set_ylabel('cross-entropy loss for that one picture', fontsize=10)
    ax.set_title('Cross-entropy: the penalty grows without limit as the right answer '
                 'is given less probability',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, SCORE_DOC, 'minus-log-curve.svg')


def three_cases_loss() -> None:
    names = [c[0] for c in CASES]
    probs = [float(_softmax(z)[t]) for _, z, t in CASES]
    losses = [float(-np.log(q)) for q in probs]
    guess = float(-np.log(0.25))
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    cols = [SLIDE, JOINT, PURPLE]
    _plain(axes[0])
    axes[0].bar(names, probs, color=cols, edgecolor=INK, lw=0.7, width=0.55)
    for i, q in enumerate(probs):
        axes[0].text(i, q + 0.02, f'{q:.4f}', ha='center', fontsize=10.5, color=INK)
    axes[0].set_ylim(0, 1.08)
    axes[0].set_ylabel('probability given to the right class', fontsize=10)
    axes[0].tick_params(labelsize=10)
    axes[0].set_title('What the model said', fontsize=11.5, weight='bold', color=INK)
    _plain(axes[1])
    axes[1].bar(names, losses, color=cols, edgecolor=INK, lw=0.7, width=0.55)
    for i, lo in enumerate(losses):
        axes[1].text(i, lo + 0.08, f'{lo:.4f}', ha='center', fontsize=10.5, color=INK)
    axes[1].axhline(guess, color=MUTED, ls='--', lw=1.3)
    axes[1].text(-0.44, guess + 0.12, f'always guessing scores {guess:.3f}', fontsize=10,
                 color=MUTED, ha='left')
    axes[1].set_ylim(0, 4.8)
    axes[1].set_ylabel('cross-entropy loss', fontsize=10)
    axes[1].tick_params(labelsize=10)
    axes[1].set_title('What the loss charged for it', fontsize=11.5, weight='bold',
                      color=INK)
    fig.suptitle('An unsure right answer costs about 12 times a sure right answer, '
                 'and a sure wrong answer about 44 times',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    print(f'[s4] loss ratios: unsure-right / sure-right = {losses[1] / losses[0]:.1f}, '
          f'sure-wrong / sure-right = {losses[2] / losses[0]:.1f}')
    _save(fig, SCORE_DOC, 'three-cases-loss.svg')


BATCH_LOGITS: Arr = np.array([
    [3.5, 1.0, 0.5, 0.0],
    [2.0, 1.5, 0.5, 0.0],
    [1.0, 0.9, 0.5, 0.2],
    [2.5, 0.5, 1.0, 0.0],
    [0.0, 3.0, 0.5, 0.5],
    [3.0, 0.5, 0.0, 0.5],
])


def batch_average() -> None:
    probs = np.array([_softmax(row) for row in BATCH_LOGITS])
    ptrue = probs[:, 0]
    losses = -np.log(ptrue)
    right = probs.argmax(axis=1) == 0
    print(f'[s4] six pictures, true class mug every time; probabilities on mug: '
          f'{", ".join(f"{v:.3f}" for v in ptrue)}')
    print(f'[s4] their losses: {", ".join(f"{v:.3f}" for v in losses)}')
    print(f'[s4] right on {right.sum()} of 6 ({100 * right.mean():.1f}%); '
          f'average loss {losses.mean():.4f}; '
          f'picture 5 alone is {100 * losses[4] / losses.sum():.1f}% of the total')
    print(f'[s4] average loss over the five good pictures only: '
          f'{losses[right].mean():.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    idx = np.arange(1, 7)
    _plain(axes[0])
    cols = [SLIDE if r else PURPLE for r in right]
    axes[0].bar(idx, ptrue, color=cols, edgecolor=INK, lw=0.7, width=0.6)
    for i, v in zip(idx, ptrue):
        axes[0].text(i, v + 0.02, f'{v:.3f}', ha='center', fontsize=10, color=INK)
    axes[0].set_xticks(idx)
    axes[0].set_xlabel('picture in the batch', fontsize=10)
    axes[0].set_ylabel('probability given to mug, the right class', fontsize=10)
    axes[0].set_ylim(0, 0.95)
    axes[0].set_title('Five pictures named right, one named wrong', fontsize=11.5,
                      weight='bold', color=INK)
    _plain(axes[1])
    axes[1].bar(idx, losses, color=cols, edgecolor=INK, lw=0.7, width=0.6)
    for i, v in zip(idx, losses):
        axes[1].text(i, v + 0.06, f'{v:.3f}', ha='center', fontsize=10, color=INK)
    axes[1].axhline(losses.mean(), color=GRIP, lw=1.6, ls='--')
    axes[1].text(0.5, 0.97, f'average over the batch = {losses.mean():.3f}',
                 transform=axes[1].transAxes, fontsize=10.5, color=GRIP, weight='bold',
                 ha='center', va='top')
    axes[1].set_xticks(idx)
    axes[1].set_xlabel('picture in the batch', fontsize=10)
    axes[1].set_ylabel('cross-entropy loss', fontsize=10)
    axes[1].set_ylim(0, 4.1)
    axes[1].set_title('Picture 5 carries most of the average', fontsize=11.5,
                      weight='bold', color=INK)
    fig.suptitle('One batch of six pictures: 83% named right, '
                 'and 56% of the loss comes from the one failure',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'batch-average.svg')


# ---------------- section 5: the loss landscape of one weight ----------------

CAND_W: list[float] = [2.0, 2.5, 3.0, 3.5, 4.0]


def five_points_three_lines() -> None:
    print(f'[s5] five parts: x = {", ".join(f"{v:.0f}" for v in X1)} (tens of pixels), '
          f'y = {", ".join(f"{v:.1f}" for v in Y1)} mm')
    for w in CAND_W:
        print(f'[s5] w = {w:.1f}: predictions '
              f'{", ".join(f"{v:.1f}" for v in w * X1)}; '
              f'mean squared error {mse_w(w)[0]:.4f}')
    print(f'[s5] the lowest loss is {L_STAR:.4f} at w = {W_STAR:.4f}, '
          f'worked out as {np.sum(X1 * Y1):.1f} / {np.sum(X1 ** 2):.0f}')

    fig, ax = plt.subplots(figsize=(10.2, 5.4), facecolor='white')
    _plain(ax)
    xs = np.linspace(0, 5.6, 100)
    for w, colour, ls in ((2.0, LINK, '--'), (W_STAR, SLIDE, '-'), (4.0, GRIP, '--')):
        ax.plot(xs, w * xs, color=colour, lw=2.2, ls=ls,
                label=f'w = {w:.3f}, loss = {mse_w(w)[0]:.3f}')
    ax.scatter(X1, Y1, s=110, color=INK, zorder=5, label='the five measured parts')
    for w, colour in ((2.0, LINK), (4.0, GRIP)):
        for x, y in zip(X1, Y1):
            ax.plot([x, x], [y, w * x], color=colour, lw=1.0, alpha=0.55)
    for x, y in zip(X1, Y1):
        ax.text(x + 0.08, y - 0.9, f'{y:.1f}', fontsize=9.5, color=INK)
    ax.set_xlim(0, 5.6)
    ax.set_ylim(0, 23)
    ax.set_xlabel('height of the part in the camera picture (tens of pixels)', fontsize=10)
    ax.set_ylabel('downward travel the arm needed (mm)', fontsize=10)
    ax.set_title('One weight, three settings: the thin lines are the errors each '
                 'setting makes',
                 fontsize=12.5, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='upper left')
    _save(fig, SCORE_DOC, 'five-points-three-lines.svg')


def loss_against_weight() -> None:
    ws = np.linspace(1.0, 5.0, 801)
    losses = mse_w(ws)
    fig, ax = plt.subplots(figsize=(10.2, 5.6), facecolor='white')
    _plain(ax)
    ax.plot(ws, losses, color=SLIDE, lw=2.8)
    places = [(2.0, 2.14, 13.0, 'left'), (2.5, 2.66, 5.2, 'left'),
              (3.0, 2.90, 8.2, 'right'), (3.5, 3.34, 2.4, 'right'),
              (4.0, 3.86, 12.8, 'right')]
    for (w, tx, ty, align), colour in zip(places, [LINK, TEAL, SLIDE, JOINT, GRIP]):
        lo = float(mse_w(w)[0])
        ax.scatter([w], [lo], s=95, color=colour, edgecolor=INK, lw=0.7, zorder=5)
        ax.plot([w, w], [0, lo], color=colour, lw=1.0, ls=':')
        ax.annotate(f'w = {w:.1f}, loss {lo:.2f}', xy=(w, lo), xytext=(tx, ty),
                    fontsize=9.8, color=colour, weight='bold', ha=align,
                    arrowprops=dict(arrowstyle='-', color=colour, lw=0.9))
    ax.scatter([W_STAR], [L_STAR], s=130, marker='v', color=INK, zorder=6)
    ax.set_xlim(1.0, 5.0)
    ax.set_ylim(0, 48)
    ax.set_xlabel('the one weight, w', fontsize=10)
    ax.set_ylabel('mean squared error over the five parts (mm$^2$)', fontsize=10)
    ax.set_title('The loss landscape of a model with one weight, worked out at 801 '
                 f'settings of w\nThe triangle is the bottom, at w = {W_STAR:.3f}, '
                 f'where the loss is {L_STAR:.4f} mm$^2$',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, SCORE_DOC, 'loss-against-weight.svg')


def squared_and_absolute_landscape() -> None:
    ws = np.linspace(2.6, 3.4, 3201)
    sq = mse_w(ws)
    ab = mae_w(ws)
    best_ab = float(ws[int(np.argmin(ab))])
    ratios = Y1 / X1
    print(f'[s5] absolute error is lowest at w = {best_ab:.4f}, '
          f'value {ab.min():.4f} mm')
    print('[s5] the kinks sit where one part is predicted exactly: w = '
          + ', '.join(f'{r:.4f}' for r in sorted(ratios)))

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    _plain(axes[0])
    axes[0].plot(ws, sq, color=PURPLE, lw=2.6)
    axes[0].scatter([W_STAR], [L_STAR], s=100, color=INK, zorder=5)
    axes[0].text(W_STAR + 0.02, L_STAR + 0.35, f'smooth bottom\nw = {W_STAR:.3f}',
                 fontsize=10, color=INK)
    axes[0].set_xlabel('the one weight, w', fontsize=10)
    axes[0].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[0].set_title('Squared error: one smooth curve', fontsize=11.5, weight='bold',
                      color=PURPLE)
    _plain(axes[1])
    axes[1].set_ylim(0, 1.45)
    axes[1].plot(ws, ab, color=TEAL, lw=2.6)
    for r in ratios:
        axes[1].axvline(r, color=GRID, lw=1.0, zorder=0)
        axes[1].text(r, 1.42, f'{r:.3f}', rotation=90, fontsize=8.5, color=MUTED,
                     ha='center', va='top')
    axes[1].scatter([best_ab], [ab.min()], s=100, color=INK, zorder=5)
    axes[1].annotate(f'bottom at a kink, w = {best_ab:.3f}', xy=(best_ab, ab.min()),
                     xytext=(3.12, 0.62), fontsize=10, color=INK, ha='left',
                     arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean absolute error (mm)', fontsize=10)
    axes[1].set_title('Absolute error: five straight pieces joined at kinks',
                      fontsize=11.5, weight='bold', color=TEAL)
    fig.suptitle('The same five parts, the same one weight, two losses with two '
                 'different shapes',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'squared-and-absolute-landscape.svg')


def _ce_hold(w: Arr | float) -> Arr:
    """Mean cross-entropy of the one-weight hold-or-drop model, logit = w * (force - 5)."""
    w = np.atleast_1d(np.asarray(w, dtype=float))
    z = w[:, None] * (HOLD_F[None, :] - 5.0)
    p = _sigmoid(z)
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -np.mean(HOLD_Y[None, :] * np.log(p) + (1 - HOLD_Y[None, :]) * np.log(1 - p),
                    axis=1)


def cross_entropy_landscape() -> None:
    ws = np.linspace(-0.5, 4.0, 4501)
    ce = _ce_hold(ws)
    best = float(ws[int(np.argmin(ce))])
    print(f'[s5] hold-or-drop table: forces {", ".join(f"{v:.0f}" for v in HOLD_F)} N, '
          f'held = {", ".join(f"{int(v)}" for v in HOLD_Y)}')
    print(f'[s5] cross-entropy is lowest at w = {best:.4f}, value {ce.min():.4f}; '
          f'at w = 0 it is {_ce_hold(0.0)[0]:.4f} (which is ln 2 = {np.log(2):.4f})')
    for w in (0.0, 0.5, 1.0, 2.0, 3.0):
        print(f'[s5] w = {w:.1f}: cross-entropy {_ce_hold(w)[0]:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    _plain(axes[0])
    fs = np.linspace(1.5, 8.5, 400)
    for w, colour in ((0.5, LINK), (best, SLIDE), (3.0, GRIP)):
        axes[0].plot(fs, _sigmoid(w * (fs - 5.0)), color=colour, lw=2.2,
                     label=f'w = {w:.3f}, loss = {_ce_hold(w)[0]:.3f}')
    axes[0].scatter(HOLD_F, HOLD_Y, s=110, color=INK, zorder=5)
    for f, y in zip(HOLD_F, HOLD_Y):
        axes[0].text(f, y + (0.05 if y == 0 else -0.11), 'held' if y == 1 else 'dropped',
                     fontsize=9, color=INK, ha='center')
    axes[0].set_xlabel('closing force of the grip (newtons)', fontsize=10)
    axes[0].set_ylabel('probability the model gives to "held"', fontsize=10)
    axes[0].set_ylim(-0.18, 1.18)
    axes[0].set_title('Seven grips, and three settings of the one weight',
                      fontsize=11.5, weight='bold', color=INK)
    axes[0].legend(fontsize=9.5, frameon=False, loc='lower right')
    _plain(axes[1])
    axes[1].plot(ws, ce, color=GRIP, lw=2.6)
    axes[1].scatter([best], [ce.min()], s=110, marker='v', color=INK, zorder=5)
    axes[1].text(best + 0.12, ce.min() + 0.04, f'bottom: w = {best:.3f},\n'
                 f'loss = {ce.min():.4f}', fontsize=10, color=INK)
    axes[1].axhline(float(np.log(2)), color=MUTED, ls='--', lw=1.2)
    axes[1].text(2.05, np.log(2) + 0.025, f'w = 0 says 0.5 to everything: '
                 f'{np.log(2):.3f}', fontsize=9.5, color=MUTED, ha='left')
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean cross-entropy over the seven grips', fontsize=10)
    axes[1].set_ylim(0.3, 1.32)
    axes[1].set_title('A cross-entropy landscape has a bottom too',
                      fontsize=11.5, weight='bold', color=GRIP)
    fig.suptitle('Cross-entropy drawn against a weight: lopsided, but still a bowl',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'cross-entropy-landscape.svg')


# ---------------- section 6: choosing a loss ----------------

def huber_curve() -> None:
    e = np.linspace(-4, 4, 1601)
    delta = 1.0
    hub = np.where(np.abs(e) <= delta, 0.5 * e ** 2, delta * (np.abs(e) - 0.5 * delta))
    for v in (0.5, 1.0, 2.0, 4.0, 12.0):
        h = 0.5 * v ** 2 if v <= delta else delta * (v - 0.5 * delta)
        print(f'[s6] error {v:5.1f} mm: squared {v * v:7.2f}, absolute {v:6.2f}, '
              f'Huber (switch at 1 mm) {h:6.2f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(e, 0.5 * e ** 2, color=PURPLE, lw=2.4, label='half the squared error')
    ax.plot(e, np.abs(e), color=TEAL, lw=2.4, label='the error size')
    ax.plot(e, hub, color=WRIST, lw=3.0, ls='-', label='Huber, switching at 1 mm')
    for s in (-1.0, 1.0):
        ax.axvline(s, color=GRID, lw=1.2)
    ax.set_xlabel('error on one part (mm)', fontsize=10)
    ax.set_ylabel('penalty', fontsize=10)
    ax.set_ylim(-0.3, 5.4)
    ax.set_title('Inside 1 mm the Huber penalty follows the squared one,\n'
                 'and outside it follows the straight one',
                 fontsize=11, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper center')
    ax = axes[1]
    _plain(ax)
    sizes = [0.5, 1.0, 2.0, 4.0, 12.0]
    sq = [v * v for v in sizes]
    ab = list(sizes)
    hb = [0.5 * v ** 2 if v <= delta else delta * (v - 0.5 * delta) for v in sizes]
    xs = np.arange(len(sizes))
    for off, vals, colour, lab in ((-0.26, sq, PURPLE, 'squared error'),
                                   (0.0, ab, TEAL, 'the error size'),
                                   (0.26, hb, WRIST, 'Huber')):
        ax.bar(xs + off, vals, width=0.25, color=colour, edgecolor=INK, lw=0.6, label=lab)
        for x, v in zip(xs, vals):
            ax.text(x + off, v * 1.12, f'{v:g}', ha='center', fontsize=9.0, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(0.08, 600)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{v:g} mm' for v in sizes], fontsize=10)
    ax.set_xlabel('size of the error on one part', fontsize=10)
    ax.set_ylabel('penalty (log scale)', fontsize=10)
    ax.set_title('What each loss charges for five error sizes', fontsize=11,
                 weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.suptitle('A 12 mm miss costs 144 under squared error, 12 under the error size '
                 'and 11.5 under Huber',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'huber-curve.svg')


def fitted_under_three_losses() -> None:
    grid = np.linspace(0.5, 4.0, 7001)
    sq = np.array([float(np.mean((w * X1 - Y1_BAD) ** 2)) for w in grid])
    ab = np.array([float(np.mean(np.abs(w * X1 - Y1_BAD))) for w in grid])
    hub = np.array([float(huber_w(w, 1.0, X1, Y1_BAD)[0]) for w in grid])
    b_sq = float(grid[int(np.argmin(sq))])
    b_ab = float(grid[int(np.argmin(ab))])
    b_hub = float(grid[int(np.argmin(hub))])
    print(f'[s6] glitched table: y = {", ".join(f"{v:.1f}" for v in Y1_BAD)}')
    print(f'[s6] best w with good data: {W_STAR:.4f}')
    print(f'[s6] best w after the glitch: squared {b_sq:.4f}, absolute {b_ab:.4f}, '
          f'Huber {b_hub:.4f}')
    print(f'[s6] the glitch moves the squared-error answer by '
          f'{abs(b_sq - W_STAR):.4f}, the absolute-error answer by '
          f'{abs(b_ab - W_STAR):.4f} and the Huber answer by {abs(b_hub - W_STAR):.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.2), facecolor='white')
    _plain(axes[0])
    xs = np.linspace(0, 5.6, 100)
    axes[0].plot(xs, W_STAR * xs, color=GRID, lw=2.0, ls='--',
                 label=f'before the glitch: w = {W_STAR:.3f}')
    for w, colour, lab in ((b_sq, PURPLE, 'squared error'), (b_ab, TEAL, 'absolute error'),
                           (b_hub, WRIST, 'Huber')):
        axes[0].plot(xs, w * xs, color=colour, lw=2.3, label=f'{lab}: w = {w:.3f}')
    axes[0].scatter(X1[:4], Y1_BAD[:4], s=110, color=INK, zorder=5)
    axes[0].scatter([X1[4]], [Y1_BAD[4]], s=150, marker='X', color=GRIP, zorder=6)
    axes[0].annotate('the glitched reading:\n4.0 mm instead of 15.1 mm',
                     xy=(X1[4], Y1_BAD[4]), xytext=(2.6, 1.0), fontsize=9.5, color=GRIP,
                     arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    axes[0].set_xlim(0, 5.6)
    axes[0].set_ylim(0, 19)
    axes[0].set_xlabel('height of the part in the picture (tens of pixels)', fontsize=10)
    axes[0].set_ylabel('downward travel (mm)', fontsize=10)
    axes[0].set_title('One bad label, three answers', fontsize=11.5, weight='bold',
                      color=INK)
    axes[0].legend(fontsize=9.3, frameon=False, loc='upper left')
    _plain(axes[1])
    for vals, colour, lab, best in ((sq / sq.min(), PURPLE, 'squared error', b_sq),
                                    (ab / ab.min(), TEAL, 'absolute error', b_ab),
                                    (hub / hub.min(), WRIST, 'Huber', b_hub)):
        axes[1].plot(grid, vals, color=colour, lw=2.3, label=lab)
        axes[1].axvline(best, color=colour, ls=':', lw=1.4)
    axes[1].axvline(W_STAR, color=GRID, ls='--', lw=1.6)
    axes[1].text(W_STAR + 0.03, 5.6, f'the honest answer, {W_STAR:.3f}', fontsize=9.5,
                 color=MUTED, rotation=90, va='top')
    axes[1].set_xlim(1.2, 3.6)
    axes[1].set_ylim(0.9, 6.2)
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('loss, divided by its own lowest value', fontsize=10)
    axes[1].set_title('Each loss has its bottom in a different place', fontsize=11.5,
                      weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='upper right')
    fig.suptitle('With one glitched label in five, squared error gives up 1.01 of the '
                 'weight and absolute error gives up 0.03',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'fitted-under-three-losses.svg')


def why_not_squared_for_a_choice() -> None:
    p = np.linspace(0.002, 1.0, 2000)
    ce = -np.log(p)
    sq = (1.0 - p) ** 2
    zs = np.array([-4.6, -2.2, 0.0, 2.2, 4.6])
    ps = _sigmoid(zs)
    h = 1e-6
    ce_slope = []
    sq_slope = []
    for z in zs:
        f1 = -np.log(float(_sigmoid(z + h)))
        f0 = -np.log(float(_sigmoid(z - h)))
        ce_slope.append((f1 - f0) / (2 * h))
        g1 = (1.0 - float(_sigmoid(z + h))) ** 2
        g0 = (1.0 - float(_sigmoid(z - h))) ** 2
        sq_slope.append((g1 - g0) / (2 * h))
    for z, pr, a, b in zip(zs, ps, ce_slope, sq_slope):
        print(f'[s6] logit {z:+.1f} (probability {pr:.4f}): the loss changes by '
              f'{a:+.4f} for cross-entropy and {b:+.4f} for squared error, '
              f'per unit of logit')
    worst = int(np.argmin(ps))
    print(f'[s6] at a probability of {ps[worst]:.4f} cross-entropy pushes '
          f'{abs(ce_slope[worst] / sq_slope[worst]):.1f} times harder than squared error')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    _plain(axes[0])
    axes[0].plot(p, ce, color=GRIP, lw=2.6, label='cross-entropy: $-\\ln p$')
    axes[0].plot(p, sq, color=LINK, lw=2.6, label='squared error: $(1 - p)^2$')
    axes[0].axhline(1.0, color=GRID, lw=1.2)
    axes[0].text(0.97, 0.52, 'squared error can never charge more than 1',
                 transform=axes[0].transAxes, fontsize=9.5, color=LINK, ha='right')
    for pr in (0.01, 0.1):
        axes[0].scatter([pr, pr], [-np.log(pr), (1 - pr) ** 2], s=60, color=INK, zorder=5)
        axes[0].text(pr + 0.02, -np.log(pr) + 0.15, f'{-np.log(pr):.2f}', fontsize=9.5,
                     color=GRIP)
    axes[0].set_xlim(0, 1.02)
    axes[0].set_ylim(0, 5.4)
    axes[0].set_xlabel('probability given to the right class', fontsize=10)
    axes[0].set_ylabel('penalty', fontsize=10)
    axes[0].set_title('How much each loss charges', fontsize=11.5, weight='bold',
                      color=INK)
    axes[0].legend(fontsize=9.8, frameon=False, loc='upper center')
    _plain(axes[1])
    xpos = np.arange(len(zs))
    axes[1].bar(xpos - 0.19, np.abs(ce_slope), width=0.36, color=GRIP, edgecolor=INK,
                lw=0.6, label='cross-entropy')
    axes[1].bar(xpos + 0.19, np.abs(sq_slope), width=0.36, color=LINK, edgecolor=INK,
                lw=0.6, label='squared error')
    for x, a, b in zip(xpos, np.abs(ce_slope), np.abs(sq_slope)):
        axes[1].text(x - 0.19, a + 0.012, f'{a:.3f}', ha='center', fontsize=9.0,
                     color=INK)
        axes[1].text(x + 0.19, b + 0.012, f'{b:.3f}', ha='center', fontsize=9.0,
                     color=INK)
    axes[1].set_xticks(xpos)
    axes[1].set_xticklabels([f'{pr:.3f}' for pr in ps], fontsize=9.5)
    axes[1].set_xlabel('probability given to the right class', fontsize=10)
    axes[1].set_ylabel('size of the push on the logit', fontsize=10)
    axes[1].set_ylim(0, 1.12)
    axes[1].set_title('How hard each loss pushes the logit', fontsize=11.5,
                      weight='bold', color=INK)
    axes[1].legend(fontsize=9.8, frameon=False, loc='upper right')
    fig.suptitle('A sure wrong answer: cross-entropy still pushes hard, '
                 'squared error has almost given up',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'why-not-squared-for-a-choice.svg')


# ==========================================================================
# 02_gradient-descent.md
# ==========================================================================

def descent1(w0: float, eta: float, steps: int) -> tuple[Arr, Arr, Arr]:
    """Plain gradient descent on the one-weight squared-error loss."""
    w = float(w0)
    ws, losses, slopes = [w], [float(mse_w(w)[0])], []
    for _ in range(steps):
        g = slope_mse(w)
        slopes.append(g)
        w = w - eta * g
        ws.append(w)
        losses.append(float(mse_w(w)[0]))
    slopes.append(slope_mse(w))
    return np.array(ws), np.array(losses), np.array(slopes)


# ---------------- section 1: the slope of the loss curve ----------------

def tiny_nudge() -> None:
    w = 1.0
    h = 0.01
    l0 = float(mse_w(w)[0])
    l1 = float(mse_w(w + h)[0])
    ratio = (l1 - l0) / h
    print(f'[g1] at w = {w:.2f} the loss is {l0:.4f}')
    print(f'[g1] at w = {w + h:.2f} the loss is {l1:.4f}, a change of {l1 - l0:+.4f}')
    print(f'[g1] change in loss divided by change in w = {ratio:+.4f}; '
          f'the exact slope is {slope_mse(w):+.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    ws = np.linspace(0.0, 5.0, 801)
    _plain(axes[0])
    axes[0].plot(ws, mse_w(ws), color=SLIDE, lw=2.6)
    axes[0].scatter([w], [l0], s=100, color=GRIP, zorder=5)
    axes[0].add_patch(Rectangle((0.6, l0 - 8), 0.8, 16, facecolor='none',
                                edgecolor=INK, lw=1.2, ls='--'))
    axes[0].text(1.55, l0 + 14, 'the small box on the right', fontsize=10, color=INK)
    axes[0].set_xlabel('the one weight, w', fontsize=10)
    axes[0].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[0].set_ylim(0, 100)
    axes[0].set_title('The whole loss curve', fontsize=11.5, weight='bold', color=INK)
    _plain(axes[1])
    zw = np.linspace(0.955, 1.075, 400)
    axes[1].plot(zw, mse_w(zw), color=SLIDE, lw=2.8)
    axes[1].set_xlim(0.955, 1.075)
    axes[1].set_ylim(41.0, 46.4)
    axes[1].scatter([w, w + h], [l0, l1], s=100, color=[GRIP, LINK], zorder=5)
    axes[1].plot([w, w + h], [l0, l0], color=INK, lw=1.4)
    axes[1].plot([w + h, w + h], [l0, l1], color=INK, lw=1.4)
    axes[1].text(w + h / 2, l0 + 0.08, f'move w by {h:.2f}', ha='center', fontsize=10,
                 color=INK)
    axes[1].text(w + h + 0.003, (l0 + l1) / 2, f'the loss changes\nby {l1 - l0:+.4f}',
                 fontsize=10, color=INK, va='center', ha='left')
    axes[1].text(0.958, 41.3, f'{l1 - l0:+.4f} divided by {h:.2f} is {ratio:+.3f},\n'
                 'so the loss falls by about 44 mm$^2$\nfor every 1 that w rises',
                 fontsize=10, color=GRIP, weight='bold', va='bottom')
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[1].set_title(f'A nudge of {h:.2f} at w = {w:.2f}', fontsize=11.5,
                      weight='bold', color=INK)
    fig.suptitle('The slope is the change in the loss divided by the change in the '
                 'weight that caused it',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'tiny-nudge.svg')


def slope_at_three_places() -> None:
    picks = [0.5, 1.5, W_STAR, 4.5]
    cols = [LINK, TEAL, INK, GRIP]
    for w in picks:
        print(f'[g1] at w = {w:.3f}: loss {mse_w(w)[0]:.4f}, slope {slope_mse(w):+.4f}, '
              f'downhill means moving w '
              f'{"up" if slope_mse(w) < 0 else ("down" if slope_mse(w) > 0 else "nowhere")}')

    labels = [
        (0.5, (1.5, 86.0), 'w = 0.50, slope -55.16\nthe loss falls as w rises, so step w up'),
        (1.5, (2.35, 48.0), 'w = 1.50, slope -33.16\nstill falling, so still step w up'),
        (W_STAR, (3.05, 14.0), 'w = 3.01, slope 0.00\nthe bottom: nowhere to step'),
        (4.5, (3.75, 70.0), 'w = 4.50, slope +32.84\nthe loss rises as w rises, so step w down'),
    ]
    fig, ax = plt.subplots(figsize=(10.8, 6.0), facecolor='white')
    _plain(ax)
    ws = np.linspace(0.0, 5.2, 801)
    ax.plot(ws, mse_w(ws), color=SLIDE, lw=2.8, zorder=2)
    for (w, (tx, ty), text), colour in zip(labels, cols):
        lo = float(mse_w(w)[0])
        g = slope_mse(w)
        seg = np.linspace(w - 0.65, w + 0.65, 10)
        ax.plot(seg, lo + g * (seg - w), color=colour, lw=2.0, zorder=3)
        ax.scatter([w], [lo], s=100, color=colour, edgecolor=INK, lw=0.7, zorder=5)
        ax.annotate(text, xy=(w, lo), xytext=(tx, ty), fontsize=10, color=colour,
                    weight='bold', ha='center',
                    arrowprops=dict(arrowstyle='-', color=colour, lw=1.0))
    ax.set_xlim(0, 5.2)
    ax.set_ylim(0, 118)
    ax.set_xlabel('the one weight, w', fontsize=10)
    ax.set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    ax.set_title('The slope at four settings of w, with the straight line it describes',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, DESC_DOC, 'slope-at-three-places.svg')


def nudge_gets_smaller() -> None:
    w = 1.0
    hs = np.array([1.0, 0.5, 0.1, 0.01, 0.001, 0.0001])
    exact = slope_mse(w)
    rows = []
    for h in hs:
        l0 = float(mse_w(w)[0])
        l1 = float(mse_w(w + h)[0])
        r = (l1 - l0) / h
        rows.append([f'{h:g}', f'{l1:.6f}', f'{l1 - l0:+.6f}', f'{r:+.4f}',
                     f'{abs(r - exact):.4f}'])
        print(f'[g1] nudge {h:g}: ratio {r:+.6f}, which is {abs(r - exact):.6f} '
              f'away from the exact slope {exact:+.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1.0]})
    _table(axes[0], ['nudge\nin w', 'loss\nafter it', 'change\nin loss',
                     'change divided\nby the nudge', 'gap to the\nexact slope'],
           rows, [1.0, 1.3, 1.3, 1.5, 1.4],
           colours=[LINK, INK, GRIP, SLIDE, MUTED], fontsize=9.8, row_h=1.0)
    axes[0].set_title(f'Smaller nudges at w = 1.00, closing in on {exact:+.2f}',
                      fontsize=11.5, weight='bold', color=INK, pad=12)
    _plain(axes[1])
    ratios = [(float(mse_w(w + h)[0]) - float(mse_w(w)[0])) / h for h in hs]
    axes[1].plot(hs, ratios, marker='o', color=SLIDE, lw=2.2)
    axes[1].axhline(exact, color=GRIP, ls='--', lw=1.6)
    axes[1].text(0.0003, exact + 0.6, f'the exact slope, {exact:+.2f}', fontsize=10,
                 color=GRIP)
    axes[1].set_xscale('log')
    axes[1].set_xlabel('size of the nudge in w (log scale)', fontsize=10)
    axes[1].set_ylabel('change in loss divided by nudge', fontsize=10)
    axes[1].set_title('The ratio settles down as the nudge shrinks', fontsize=11.5,
                      weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'nudge-gets-smaller.svg')


# ---------------- section 2: one step downhill ----------------

ETA_GOOD: float = 0.03


def first_steps_table() -> None:
    ws, losses, slopes = descent1(0.0, ETA_GOOD, 8)
    rows = []
    for k in range(8):
        step = -ETA_GOOD * slopes[k]
        rows.append([f'{k}', f'{ws[k]:.4f}', f'{losses[k]:.4f}', f'{slopes[k]:+.4f}',
                     f'{step:+.4f}', f'{ws[k + 1]:.4f}'])
        print(f'[g2] step {k}: w {ws[k]:.4f}, loss {losses[k]:.4f}, '
              f'slope {slopes[k]:+.4f}, move {step:+.4f}, new w {ws[k + 1]:.4f}')
    print(f'[g2] after 8 steps at a learning rate of {ETA_GOOD}: w = {ws[8]:.4f}, '
          f'loss = {losses[8]:.4f}, against the bottom at w = {W_STAR:.4f}, '
          f'loss = {L_STAR:.4f}')

    fig, ax = plt.subplots(figsize=(10.8, 5.8), facecolor='white')
    _table(ax, ['step', 'w now', 'loss now', 'slope now',
                f'move =\n-{ETA_GOOD} x slope', 'w next'],
           rows, [0.8, 1.2, 1.2, 1.3, 1.9, 1.2],
           colours=[INK, LINK, SLIDE, GRIP, PURPLE, LINK], fontsize=10.5, row_h=1.0)
    ax.set_title(f'Eight steps downhill from w = 0, at a learning rate of {ETA_GOOD}',
                 fontsize=12.5, weight='bold', color=INK, pad=14)
    ax.text(0.5, -10.1, f'the bottom of this curve is at w = {W_STAR:.4f} with a loss of '
            f'{L_STAR:.4f} mm$^2$', ha='center', fontsize=11, color=INK)
    _save(fig, DESC_DOC, 'first-steps-table.svg')


def steps_on_the_curve() -> None:
    ws, losses, _ = descent1(0.0, ETA_GOOD, 12)
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.2), facecolor='white')
    _plain(axes[0])
    grid = np.linspace(-0.3, 5.0, 801)
    axes[0].plot(grid, mse_w(grid), color=SLIDE, lw=2.6, zorder=2)
    axes[0].plot(ws, losses, color=GRIP, lw=1.4, ls='--', zorder=3)
    axes[0].scatter(ws, losses, s=70, color=GRIP, edgecolor=INK, lw=0.6, zorder=4)
    for k in (0, 1):
        axes[0].text(ws[k] - 0.14, losses[k] + 4.5, f'step {k}', fontsize=10.5, color=INK,
                     weight='bold')
    axes[0].add_patch(Rectangle((2.55, -1.5), 0.6, 10, facecolor='none', edgecolor=INK,
                                lw=1.2, ls='--'))
    axes[0].annotate('steps 2 to 12 are all\ninside this small box',
                     xy=(3.15, 4.0), xytext=(3.45, 30.0), fontsize=10, color=INK,
                     ha='left', arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    axes[0].set_xlim(-0.3, 5.0)
    axes[0].set_ylim(0, 112)
    axes[0].set_xlabel('the one weight, w', fontsize=10)
    axes[0].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[0].set_title('The first three steps cover almost all the distance',
                      fontsize=11.5, weight='bold', color=INK)
    _plain(axes[1])
    zoom = np.linspace(2.55, 3.15, 600)
    axes[1].plot(zoom, mse_w(zoom), color=SLIDE, lw=2.6, zorder=2)
    axes[1].plot(ws[2:], losses[2:], color=GRIP, lw=1.4, ls='--', zorder=3)
    axes[1].scatter(ws[2:], losses[2:], s=70, color=GRIP, edgecolor=INK, lw=0.6, zorder=4)
    for k in (2, 3, 4):
        axes[1].text(ws[k], losses[k] + 0.09, f'step {k}', ha='center', fontsize=10.5,
                     color=INK, weight='bold')
    axes[1].scatter([W_STAR], [L_STAR], s=130, marker='v', color=INK, zorder=6)
    axes[1].annotate(f'the bottom: w = {W_STAR:.3f}\nsteps 5 to 12 are all here',
                     xy=(W_STAR, L_STAR), xytext=(3.02, 0.85), fontsize=10, color=INK,
                     ha='center', arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    axes[1].set_xlim(2.55, 3.15)
    axes[1].set_ylim(-0.1, 1.9)
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[1].set_title('Steps 2 to 12, close up: the dots crowd together',
                      fontsize=11.5, weight='bold', color=INK)
    fig.suptitle(f'Twelve steps at a learning rate of {ETA_GOOD}, from w = 0',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'steps-on-the-curve.svg')


def loss_against_step() -> None:
    ws, losses, _ = descent1(0.0, ETA_GOOD, 40)
    gap = losses - L_STAR
    print(f'[g2] loss at steps 0, 1, 2, 5, 10, 20, 40: '
          + ', '.join(f'{losses[k]:.4f}' for k in (0, 1, 2, 5, 10, 20, 40)))
    print(f'[g2] distance above the bottom at those steps: '
          + ', '.join(f'{gap[k]:.2e}' for k in (0, 1, 2, 5, 10, 20, 40)))
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(axes[0])
    axes[0].plot(np.arange(41), losses, marker='o', ms=4, color=SLIDE, lw=2.0)
    axes[0].axhline(L_STAR, color=INK, ls='--', lw=1.3)
    axes[0].text(18, L_STAR + 4, f'the lowest the loss can go: {L_STAR:.4f}',
                 fontsize=10, color=INK)
    axes[0].set_xlabel('step number', fontsize=10)
    axes[0].set_ylabel('mean squared error (mm$^2$)', fontsize=10)
    axes[0].set_title('The loss against the step number', fontsize=11.5, weight='bold',
                      color=INK)
    _plain(axes[1])
    axes[1].semilogy(np.arange(41), np.maximum(gap, 1e-16), marker='o', ms=4,
                     color=PURPLE, lw=2.0)
    axes[1].set_xlabel('step number', fontsize=10)
    axes[1].set_ylabel('how far the loss still is above the bottom', fontsize=10)
    axes[1].set_title('The same run, with the vertical axis in powers of ten',
                      fontsize=11.5, weight='bold', color=INK)
    axes[1].grid(True, which='both', color=GRID, lw=0.5)
    fig.suptitle('Forty steps at a learning rate of 0.03: the gap to the bottom is cut '
                 'by about a third every step',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'loss-against-step.svg')


def step_shrinks_as_it_arrives() -> None:
    ws, losses, slopes = descent1(0.0, ETA_GOOD, 14)
    moves = -ETA_GOOD * slopes[:14]
    print('[g2] the move made at steps 0 to 7: '
          + ', '.join(f'{v:+.4f}' for v in moves[:8]))
    print(f'[g2] the move at step 0 is {abs(moves[0] / moves[7]):.1f} times the move '
          f'at step 7, with the same learning rate throughout')
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    idx = np.arange(14)
    _plain(axes[0])
    axes[0].bar(idx, np.abs(slopes[:14]), color=GRIP, edgecolor=INK, lw=0.6, width=0.6)
    for k in (0, 3, 7, 13):
        axes[0].text(k, abs(slopes[k]) + 1.6, f'{abs(slopes[k]):.3f}', ha='center',
                     fontsize=9.5, color=INK)
    axes[0].set_ylim(0, 78)
    axes[0].set_xticks(idx)
    axes[0].set_xlabel('step number', fontsize=10)
    axes[0].set_ylabel('size of the slope', fontsize=10)
    axes[0].set_title('The slope shrinks as the bottom comes nearer', fontsize=11.5,
                      weight='bold', color=GRIP)
    _plain(axes[1])
    axes[1].bar(idx, np.abs(moves), color=PURPLE, edgecolor=INK, lw=0.6, width=0.6)
    for k in (0, 3, 7, 13):
        axes[1].text(k, abs(moves[k]) + 0.04, f'{abs(moves[k]):.3f}', ha='center',
                     fontsize=9.5, color=INK)
    axes[1].set_xticks(idx)
    axes[1].set_xlabel('step number', fontsize=10)
    axes[1].set_ylabel('how far w actually moved', fontsize=10)
    axes[1].set_ylim(0, 2.4)
    axes[1].set_title('So the step shrinks too, with no change to the learning rate',
                      fontsize=11.5, weight='bold', color=PURPLE)
    fig.suptitle('Gradient descent slows down on its own as it arrives, '
                 'because the move is the learning rate times the slope',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'step-shrinks-as-it-arrives.svg')


# ---------------- section 3: three learning rates ----------------

RATES: list[tuple[float, str, str]] = [
    (0.0005, 'too small', LINK),
    (0.03, 'about right', SLIDE),
    (0.1, 'too large', GRIP),
]


def three_rates_on_the_curve() -> None:
    shown = {0.0005: 40, 0.03: 12, 0.1: 6}
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.6), facecolor='white')
    for ax, (eta, label, colour) in zip(axes, RATES):
        n = shown[eta]
        ws, losses, _ = descent1(0.0, eta, n)
        print(f'[g3] learning rate {eta}: w after {n} steps = {ws[-1]:.4f}, '
              f'loss = {losses[-1]:.4f}')
        lo = min(ws.min(), 0.0) - 0.6
        hi = max(ws.max(), 5.0) + 0.6
        grid = np.linspace(lo, hi, 900)
        _plain(ax)
        ax.plot(grid, mse_w(grid), color=MUTED, lw=2.0, zorder=2)
        ax.plot(ws, losses, color=colour, lw=1.4, ls='--', zorder=3)
        ax.scatter(ws, losses, s=55, color=colour, edgecolor=INK, lw=0.5, zorder=4)
        ax.scatter([W_STAR], [L_STAR], s=110, marker='v', color=INK, zorder=5)
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, float(mse_w(np.array([lo, hi])).max()) * 1.08)
        ax.set_xlabel('the one weight, w', fontsize=9.5)
        ax.set_title(f'learning rate {eta}: {label}\n{n} steps end at w = {ws[-1]:.3f}',
                     fontsize=11, weight='bold', color=colour)
    axes[0].set_ylabel('mean squared error (mm$^2$)', fontsize=9.5)
    axes[0].text(0.52, 0.74, 'the steps are tiny, so after\n40 of them w has only\n'
                 'reached 1.075', transform=axes[0].transAxes, fontsize=9.5, color=INK,
                 ha='center', va='top')
    fig.suptitle('The same loss curve, the same start at w = 0, three learning rates',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'three-rates-on-the-curve.svg')


def three_rates_loss() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    for eta, label, colour in RATES:
        ws, losses, _ = descent1(0.0, eta, 40)
        ax.semilogy(np.arange(41), np.maximum(losses, 1e-12), marker='o', ms=4,
                    color=colour, lw=2.0, label=f'learning rate {eta} ({label})')
        print(f'[g3] learning rate {eta}: loss at steps 0, 10, 20, 40 = '
              + ', '.join(f'{losses[k]:.4g}' for k in (0, 10, 20, 40)))
    ax.axhline(L_STAR, color=INK, ls='--', lw=1.3)
    ax.text(21, L_STAR * 1.35, f'the lowest the loss can go: {L_STAR:.4f}', fontsize=10,
            color=INK)
    ax.set_xlabel('step number', fontsize=10)
    ax.set_ylabel('mean squared error, in powers of ten (mm$^2$)', fontsize=10)
    ax.set_ylim(1e-3, 1e9)
    ax.set_title('Forty steps at each learning rate: crawling, arriving, and running away',
                 fontsize=12.5, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='center left')
    ax.grid(True, which='major', color=GRID, lw=0.5)
    _save(fig, DESC_DOC, 'three-rates-loss.svg')


def rate_sweep() -> None:
    steps = 12
    etas = np.logspace(-4.2, -0.9, 331)
    perfect = 1.0 / (2.0 * A_COEF)
    etas = np.sort(np.concatenate([etas, [perfect]]))
    gaps = []
    for eta in etas:
        _, losses, _ = descent1(0.0, float(eta), steps)
        gaps.append(min(max(float(losses[-1]) - L_STAR, 1e-17), 1e12))
    gaps_arr = np.array(gaps)
    print(f'[g3] steps stay stable while the learning rate is below '
          f'1 / {A_COEF:.0f} = {ETA_MAX:.4f}')
    print(f'[g3] the perfect learning rate for this curve is 1 / {2 * A_COEF:.0f} = '
          f'{perfect:.4f}, and one step from w = 0 at that rate lands on '
          f'{descent1(0.0, perfect, 1)[0][1]:.4f}')
    for eta in (0.0005, 0.005, 0.03, perfect, 0.08, 0.0909, 0.1):
        _, losses, _ = descent1(0.0, float(eta), steps)
        print(f'[g3] learning rate {eta:.4f}: loss after {steps} steps {losses[-1]:.4g}, '
              f'which is {losses[-1] - L_STAR:.3e} above the bottom')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.loglog(etas, gaps_arr, color=PURPLE, lw=2.2)
    ax.axvline(ETA_MAX, color=GRIP, ls='--', lw=1.8)
    ax.text(ETA_MAX * 0.92, 5e11, f'above {ETA_MAX:.4f} every run runs away',
            rotation=90, fontsize=10, color=GRIP, ha='right', va='top')
    ax.axvline(perfect, color=SLIDE, ls=':', lw=1.8)
    ax.annotate(f'at exactly {perfect:.4f} the first\nstep lands on the bottom',
                xy=(perfect, 1e-14), xytext=(2.0e-3, 1e-13), fontsize=10, color=SLIDE,
                weight='bold', ha='left',
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.set_xlabel('learning rate (log scale)', fontsize=10)
    ax.set_ylabel('how far the loss is above the bottom after 12 steps (log scale)',
                  fontsize=10)
    ax.set_ylim(1e-18, 1e13)
    ax.set_title('Twelve steps at every learning rate from 0.00006 to 0.126: '
                 'a long slope down, then a cliff',
                 fontsize=12, weight='bold', color=INK)
    ax.grid(True, which='major', color=GRID, lw=0.5)
    _save(fig, DESC_DOC, 'rate-sweep.svg')


# ---------------- section 4: two weights ----------------

def _loss2(w1: Arr | float, w0: Arr | float, x: Arr, y: Arr) -> Arr:
    w1 = np.asarray(w1, dtype=float)
    w0 = np.asarray(w0, dtype=float)
    pred = w1[..., None] * x + w0[..., None]
    return np.mean((pred - y) ** 2, axis=-1)


def _grad2(w1: float, w0: float, x: Arr, y: Arr) -> tuple[float, float]:
    err = w1 * x + w0 - y
    return float(np.mean(2.0 * x * err)), float(np.mean(2.0 * err))


def _descent2(start: tuple[float, float], eta: float, steps: int, x: Arr,
              y: Arr) -> tuple[Arr, Arr]:
    w1, w0 = start
    path = [(w1, w0)]
    for _ in range(steps):
        g1, g0 = _grad2(w1, w0, x, y)
        w1 -= eta * g1
        w0 -= eta * g0
        path.append((w1, w0))
    p = np.array(path)
    return p, _loss2(p[:, 0], p[:, 1], x, y)


XS: Arr = (X1 - X1.mean()) / X1.std()


def _best2(x: Arr, y: Arr) -> tuple[float, float, float]:
    design = np.stack([x, np.ones_like(x)], axis=1)
    sol, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(sol[0]), float(sol[1]), float(_loss2(sol[0], sol[1], x, y))


def _hessian_eigs(x: Arr) -> tuple[float, float, float]:
    h = 2.0 * np.array([[np.mean(x ** 2), np.mean(x)], [np.mean(x), 1.0]])
    ev = np.linalg.eigvalsh(h)
    return float(ev[1]), float(ev[0]), float(ev[1] / ev[0])


def two_weight_contours() -> None:
    b1, b0, bl = _best2(X1, Y1)
    hi, lo, cond = _hessian_eigs(X1)
    print(f'[g4] two weights on the raw data: best slope {b1:.4f}, best offset '
          f'{b0:.4f}, lowest loss {bl:.4f}')
    print(f'[g4] raw data: the loss curves up {hi:.4f} in its steepest direction and '
          f'{lo:.4f} in its shallowest, a ratio of {cond:.1f}')
    path, losses = _descent2((0.0, 0.0), 0.08, 80, X1, Y1)
    print(f'[g4] 80 steps at a learning rate of 0.08 end at slope {path[-1, 0]:.4f}, '
          f'offset {path[-1, 1]:.4f}, loss {losses[-1]:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.4), facecolor='white')
    windows = [((-0.4, 5.6), (-4.6, 4.6), 'The whole path, 80 steps', 1),
               ((2.74, 3.30), (-0.30, 0.95), 'Steps 20 to 80, close up', 1)]
    for ax, ((x0, x1), (y0, y1), title, every) in zip(axes, windows):
        _plain(ax)
        g1 = np.linspace(x0, x1, 320)
        g0 = np.linspace(y0, y1, 320)
        M1, M0 = np.meshgrid(g1, g0)
        Z = np.mean((M1[..., None] * X1 + M0[..., None] - Y1) ** 2, axis=-1)
        levels = bl + np.array([0.004, 0.02, 0.08, 0.3, 1.0, 3.0, 10.0, 30.0])
        cs = ax.contour(M1, M0, Z, levels=levels, colors=LINK_PALE, linewidths=1.1)
        ax.clabel(cs, fmt='%.2f', fontsize=8, colors=MUTED)
        if title.startswith('The whole'):
            ax.plot(path[:, 0], path[:, 1], color=GRIP, lw=1.3, zorder=4)
            ax.scatter(path[::4, 0], path[::4, 1], s=20, color=GRIP, zorder=5)
            ax.scatter([0.0], [0.0], s=130, marker='s', color=INK, zorder=6)
            ax.text(0.08, -0.45, 'start at slope 0, offset 0', fontsize=9.5, color=INK)
        else:
            ax.plot(path[20:, 0], path[20:, 1], color=GRIP, lw=1.3, zorder=4)
            ax.scatter(path[20:, 0], path[20:, 1], s=26, color=GRIP, zorder=5)
            ax.text(2.76, 0.86, 'each step crosses the valley\nand lands on the other side',
                    fontsize=9.5, color=INK)
        ax.scatter([b1], [b0], s=170, marker='*', color=SLIDE, edgecolor=INK, lw=0.7,
                   zorder=6)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_xlabel('the slope weight, w$_1$', fontsize=10)
        ax.set_ylabel('the offset weight, w$_0$', fontsize=10)
        ax.set_title(title, fontsize=11.5, weight='bold', color=INK)
    fig.suptitle(f'Two weights, the loss as a contour map, and 80 real steps at a '
                 f'learning rate of 0.08. The star is the bottom, at slope {b1:.2f} '
                 f'and offset {b0:.2f}',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'two-weight-contours.svg')


def downhill_arrows() -> None:
    b1, b0, bl = _best2(X1, Y1)
    g1 = np.linspace(2.0, 4.0, 280)
    g0 = np.linspace(-3.0, 3.0, 280)
    M1, M0 = np.meshgrid(g1, g0)
    Z = np.mean((M1[..., None] * X1 + M0[..., None] - Y1) ** 2, axis=-1)
    q1 = np.linspace(2.2, 3.8, 7)
    q0 = np.linspace(-2.6, 2.6, 7)
    Q1, Q0 = np.meshgrid(q1, q0)
    U = np.zeros_like(Q1)
    V = np.zeros_like(Q0)
    for i in range(Q1.shape[0]):
        for j in range(Q1.shape[1]):
            a, b = _grad2(float(Q1[i, j]), float(Q0[i, j]), X1, Y1)
            U[i, j], V[i, j] = -a, -b
    sample = [(2.4, 2.0), (3.6, -2.0), (3.0, 1.5)]
    for s1, s0 in sample:
        a, b = _grad2(s1, s0, X1, Y1)
        print(f'[g4] at slope {s1:.1f}, offset {s0:.1f}: the loss changes by {a:+.3f} '
              f'per unit of slope and {b:+.3f} per unit of offset, so downhill is '
              f'{-a:+.3f}, {-b:+.3f}')
    fig, ax = plt.subplots(figsize=(10.4, 5.8), facecolor='white')
    _plain(ax)
    cs = ax.contour(M1, M0, Z, levels=bl + np.array([0.05, 0.3, 1.0, 3.0, 8.0, 18.0]),
                    colors=LINK, linewidths=1.1)
    ax.clabel(cs, fmt='%.1f', fontsize=8, colors=INK)
    ax.quiver(Q1, Q0, U, V, color=GRIP, angles='xy', width=0.004, scale=260)
    ax.scatter([b1], [b0], s=160, marker='*', color=SLIDE, edgecolor=INK, lw=0.7, zorder=6)
    ax.set_xlabel('the slope weight, w$_1$', fontsize=10)
    ax.set_ylabel('the offset weight, w$_0$', fontsize=10)
    ax.set_title('The downhill direction at 49 settings of the two weights\n'
                 'Each arrow is the pair of slopes, one for each weight, with the '
                 'sign turned round',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, DESC_DOC, 'downhill-arrows.svg')


def valley_shape() -> None:
    results = []
    for name, x in (('raw heights', X1), ('heights rescaled', XS)):
        b1, b0, bl = _best2(x, Y1)
        hi, lo, cond = _hessian_eigs(x)
        eta = 0.9 * 2.0 / hi
        path, losses = _descent2((0.0, 0.0), eta, 400, x, Y1)
        target = bl + 1e-6
        reach = int(np.argmax(losses <= target)) if np.any(losses <= target) else -1
        results.append((name, x, b1, b0, bl, hi, lo, cond, eta, path, losses, reach))
        print(f'[g4] {name}: steepest curvature {hi:.4f}, shallowest {lo:.4f}, '
              f'ratio {cond:.1f}; largest safe learning rate {2.0 / hi:.4f}; '
              f'at {eta:.4f} it takes {reach} steps to get the loss within one '
              f'millionth of the bottom')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.4), facecolor='white')
    for ax, r in zip(axes, results):
        name, x, b1, b0, bl, hi, lo, cond, eta, path, losses, reach = r
        _plain(ax)
        span1 = max(2.0, abs(path[:, 0]).max() * 0.6)
        g1 = np.linspace(b1 - span1, b1 + span1, 300)
        g0 = np.linspace(b0 - 1.1 * span1 * 3, b0 + 1.1 * span1 * 3, 300) \
            if name == 'raw heights' else np.linspace(b0 - span1 * 2, b0 + span1 * 2, 300)
        M1, M0 = np.meshgrid(g1, g0)
        Z = np.mean((M1[..., None] * x + M0[..., None] - Y1) ** 2, axis=-1)
        cs = ax.contour(M1, M0, Z, levels=bl + np.array([0.1, 0.5, 2.0, 8.0, 25.0, 60.0]),
                        colors=LINK, linewidths=1.1)
        ax.clabel(cs, fmt='%.0f', fontsize=8, colors=INK)
        ax.plot(path[:, 0], path[:, 1], color=GRIP, lw=1.6)
        ax.scatter(path[:60, 0], path[:60, 1], s=16, color=GRIP)
        ax.scatter([b1], [b0], s=160, marker='*', color=SLIDE, edgecolor=INK, lw=0.7,
                   zorder=6)
        ax.set_xlabel('the slope weight, w$_1$', fontsize=10)
        ax.set_ylabel('the offset weight, w$_0$', fontsize=10)
        ax.set_title(f'{name}: curvature ratio {cond:.1f}\n{reach} steps at a learning '
                     f'rate of {eta:.4f}',
                     fontsize=11, weight='bold', color=INK)
    fig.suptitle('The same five parts and the same two weights, with the camera heights '
                 'left raw and then rescaled.\nEach run uses nine tenths of its own '
                 'largest safe learning rate, and the step count is how many steps it '
                 'needs\nto bring the loss within one millionth of its lowest value',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'valley-shape.svg')


def two_weight_loss_curve() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    for name, x, colour in (('raw heights', X1, GRIP), ('heights rescaled', XS, SLIDE)):
        b1, b0, bl = _best2(x, Y1)
        hi, _, cond = _hessian_eigs(x)
        eta = 0.9 * 2.0 / hi
        _, losses = _descent2((0.0, 0.0), eta, 400, x, Y1)
        ax.semilogy(np.arange(401), np.maximum(losses - bl, 1e-16), color=colour, lw=2.2,
                    label=f'{name} (curvature ratio {cond:.1f})')
        print(f'[g4] {name}: gap above the bottom after 1, 10, 50, 200 and 400 steps = '
              + ', '.join(f'{losses[k] - bl:.3e}' for k in (1, 10, 50, 200, 400)))
    ax.set_xlabel('step number', fontsize=10)
    ax.set_ylabel('how far the loss still is above its lowest value', fontsize=10)
    ax.set_ylim(1e-16, 1e3)
    ax.set_title('Both runs use the largest safe learning rate for their own shape, '
                 'and one still takes far longer',
                 fontsize=12.5, weight='bold', color=INK)
    ax.legend(fontsize=10, frameon=False, loc='upper right')
    ax.grid(True, which='major', color=GRID, lw=0.5)
    _save(fig, DESC_DOC, 'two-weight-loss-curve.svg')


# ---------------- section 5: stochastic gradient descent ----------------

N_BIG: int = 200


def _big_data() -> tuple[Arr, Arr, Arr]:
    rng = np.random.default_rng(7)
    x_raw = rng.uniform(1.0, 5.0, N_BIG)
    y = 3.0 * x_raw + 1.0 + rng.normal(0.0, 1.2, N_BIG)
    xs = (x_raw - x_raw.mean()) / x_raw.std()
    return x_raw, xs, y


X_RAW, X_STD, Y_BIG = _big_data()
BEST1, BEST0, BEST_L = _best2(X_STD, Y_BIG)


def _sgd(batch: int, epochs: int, eta: float, seed: int,
         start: tuple[float, float] = (0.0, 0.0)) -> tuple[Arr, Arr, Arr]:
    """Mini-batch gradient descent. Returns the path, the full-data loss after each
    step, and how many examples had been used by then."""
    rng = np.random.default_rng(seed)
    w1, w0 = start
    path = [(w1, w0)]
    losses = [float(_loss2(w1, w0, X_STD, Y_BIG))]
    seen = [0]
    used = 0
    for _ in range(epochs):
        order = rng.permutation(N_BIG)
        for s in range(0, N_BIG, batch):
            idx = order[s:s + batch]
            g1, g0 = _grad2(w1, w0, X_STD[idx], Y_BIG[idx])
            w1 -= eta * g1
            w0 -= eta * g0
            used += len(idx)
            path.append((w1, w0))
            losses.append(float(_loss2(w1, w0, X_STD, Y_BIG)))
            seen.append(used)
    return np.array(path), np.array(losses), np.array(seen)


def one_epoch() -> None:
    sizes = [1, 8, 32, 200]
    steps = [N_BIG // b for b in sizes]
    print(f'[g5] {N_BIG} simulated examples; one epoch gives '
          + ', '.join(f'{s} steps at a batch of {b}' for b, s in zip(sizes, steps)))
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1.0]})
    ax = axes[0]
    _blank(ax)
    rng = np.random.default_rng(11)
    order = rng.permutation(N_BIG)
    cols = [LINK, SLIDE, WRIST, PURPLE, TEAL]
    for k, pos in enumerate(range(0, N_BIG, 8)):
        row, col = divmod(k, 5)
        for j in range(8):
            ax.add_patch(Rectangle((col * 1.9 + j * 0.2, -row * 1.0), 0.17, 0.6,
                                   facecolor=cols[k % 5], edgecolor='none'))
        ax.text(col * 1.9 + 0.8, -row * 1.0 + 0.72, f'batch {k + 1}', fontsize=7.5,
                ha='center', color=INK)
    ax.set_xlim(-0.3, 9.4)
    ax.set_ylim(-5.0, 1.3)
    ax.set_title('One epoch: 200 shuffled examples cut into 25 batches of 8,\n'
                 'which is 25 steps of gradient descent',
                 fontsize=11.5, weight='bold', color=INK)
    ax.text(0.0, -4.5, 'each small block is one example; each colour is one batch',
            fontsize=9.5, color=MUTED)
    _plain(axes[1])
    axes[1].bar([str(b) for b in sizes], steps, color=[LINK, SLIDE, WRIST, PURPLE],
                edgecolor=INK, lw=0.6, width=0.55)
    for i, s in enumerate(steps):
        axes[1].text(i, s + 4, f'{s}', ha='center', fontsize=10.5, color=INK)
    axes[1].set_yscale('log')
    axes[1].set_xlabel('batch size', fontsize=10)
    axes[1].set_ylabel('steps in one epoch (log scale)', fontsize=10)
    axes[1].set_ylim(0.6, 500)
    axes[1].set_title('Smaller batches buy more steps per epoch', fontsize=11.5,
                      weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'one-epoch.svg')


def full_batch_versus_mini_batch() -> None:
    eta = 0.08
    epochs = 6
    p_full, l_full, _ = _sgd(N_BIG, epochs, eta, 21)
    p_mini, l_mini, _ = _sgd(8, epochs, eta, 21)
    print(f'[g5] {epochs} epochs at a learning rate of {eta}: '
          f'full batch takes {len(p_full) - 1} steps and ends at slope '
          f'{p_full[-1, 0]:.4f}, offset {p_full[-1, 1]:.4f}, loss {l_full[-1]:.4f}')
    print(f'[g5] the same {epochs} epochs with batches of 8 take {len(p_mini) - 1} '
          f'steps and end at slope {p_mini[-1, 0]:.4f}, offset {p_mini[-1, 1]:.4f}, '
          f'loss {l_mini[-1]:.4f}')
    print(f'[g5] the lowest loss these two weights can reach is {BEST_L:.4f} at slope '
          f'{BEST1:.4f}, offset {BEST0:.4f}')

    g1 = np.linspace(-0.4, 4.4, 300)
    g0 = np.linspace(-0.4, 11.6, 300)
    M1, M0 = np.meshgrid(g1, g0)
    Z = np.mean((M1[..., None] * X_STD + M0[..., None] - Y_BIG) ** 2, axis=-1)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.4), facecolor='white')
    for ax, (path, lab, colour, nsteps) in zip(axes, (
            (p_full, 'all 200 examples per step', LINK, len(p_full) - 1),
            (p_mini, '8 examples per step', GRIP, len(p_mini) - 1))):
        _plain(ax)
        cs = ax.contour(M1, M0, Z, levels=BEST_L + np.array([0.2, 1.0, 4.0, 14.0, 40.0,
                                                             90.0, 170.0]),
                        colors=LINK_PALE, linewidths=1.1)
        ax.clabel(cs, fmt='%.0f', fontsize=8, colors=MUTED)
        ax.plot(path[:, 0], path[:, 1], color=colour, lw=1.5)
        ax.scatter(path[::max(1, len(path) // 60), 0], path[::max(1, len(path) // 60), 1],
                   s=18, color=colour)
        ax.scatter([BEST1], [BEST0], s=170, marker='*', color=SLIDE, edgecolor=INK,
                   lw=0.7, zorder=6)
        ax.set_xlabel('the slope weight, w$_1$', fontsize=10)
        ax.set_ylabel('the offset weight, w$_0$', fontsize=10)
        ax.set_title(f'{lab}\n{nsteps} steps in 6 epochs, ending at a loss of '
                     f'{float(_loss2(path[-1, 0], path[-1, 1], X_STD, Y_BIG)):.3f}',
                     fontsize=11, weight='bold', color=colour)
    fig.suptitle('Six passes over the same 200 examples: a smooth short path and a '
                 'noisy long one, going to the same place',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'full-batch-versus-mini-batch.svg')


def cost_in_examples() -> None:
    eta = 0.08
    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    for batch, colour in ((1, PURPLE), (8, GRIP), (32, WRIST), (200, LINK)):
        _, losses, seen = _sgd(batch, 10, eta, 31)
        ends = [int(np.argmax(seen >= k * N_BIG)) for k in range(11)]
        ax.semilogy(seen[ends], np.maximum(losses[ends] - BEST_L, 1e-6), color=colour,
                    lw=2.0, marker='o', ms=5, label=f'batch of {batch}')
        print(f'[g5] batch of {batch:3d}: gap above the bottom at the end of epochs '
              f'1, 3 and 10 = '
              + ', '.join(f'{losses[ends[k]] - BEST_L:.4f}' for k in (1, 3, 10)))
    ax.set_xlabel('examples used so far (10 epochs of 200 examples)', fontsize=10)
    ax.set_ylabel('how far the loss still is above its lowest value', fontsize=10)
    ax.set_title('Measured at the end of each epoch: the real cost of a step is the '
                 'examples it reads,\nand small batches get more done per example',
                 fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=10, frameon=False, loc='lower left')
    ax.grid(True, which='major', color=GRID, lw=0.5)
    _save(fig, DESC_DOC, 'cost-in-examples.svg')


def gradient_noise() -> None:
    rng = np.random.default_rng(13)
    w1, w0 = 1.5, 5.0
    full1, full0 = _grad2(w1, w0, X_STD, Y_BIG)
    sizes = [1, 2, 4, 8, 16, 32, 64, 128]
    spreads = []
    for b in sizes:
        samples = []
        for _ in range(4000):
            idx = rng.choice(N_BIG, size=b, replace=False)
            samples.append(_grad2(w1, w0, X_STD[idx], Y_BIG[idx])[0])
        spreads.append(float(np.std(samples)))
        print(f'[g5] batch of {b:3d}: the slope part of the gradient averages '
              f'{np.mean(samples):+.4f} against the all-200 value of {full1:+.4f}, '
              f'with a spread of {spreads[-1]:.4f}')
    spreads_arr = np.array(spreads)
    ref = spreads_arr[0] / np.sqrt(np.array(sizes, dtype=float))
    print(f'[g5] the spread falls from {spreads_arr[0]:.4f} at a batch of 1 to '
          f'{spreads_arr[-1]:.4f} at a batch of 128, and is exactly 0 at a batch of '
          f'200 because that batch is the whole dataset')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(axes[0])
    for b, colour in ((1, PURPLE), (8, GRIP), (64, LINK)):
        vals = [_grad2(w1, w0, X_STD[i], Y_BIG[i])[0]
                for i in [rng.choice(N_BIG, size=b, replace=False) for _ in range(1500)]]
        axes[0].hist(vals, bins=40, histtype='step', lw=2.0, color=colour,
                     label=f'batch of {b}')
    axes[0].axvline(full1, color=INK, ls='--', lw=1.6)
    axes[0].set_ylim(0, 185)
    axes[0].text(0.5, 0.98, f'all 200 examples give {full1:+.2f}',
                 transform=axes[0].transAxes, fontsize=10, color=INK, ha='center',
                 va='top')
    axes[0].set_xlabel('the slope part of the gradient, measured on one batch',
                       fontsize=10)
    axes[0].set_ylabel('how many batches gave that value', fontsize=10)
    axes[0].set_title('A small batch gives a noisy reading of the same gradient',
                      fontsize=11.5, weight='bold', color=INK)
    axes[0].legend(fontsize=9.5, frameon=False, loc='upper left')
    _plain(axes[1])
    axes[1].loglog(sizes, spreads_arr, marker='o', color=GRIP, lw=2.2,
                   label='measured spread')
    axes[1].loglog(sizes, ref, ls='--', color=MUTED, lw=1.8,
                   label='the batch-of-1 spread divided by\nthe square root of the batch size')
    for b, s in zip(sizes, spreads_arr):
        if b in (1, 8, 128):
            axes[1].text(b * 1.15, s * 1.15, f'{s:.3f}', fontsize=9.5, color=INK)
    axes[1].set_ylim(0.3, 20)
    axes[1].set_xlabel('batch size (log scale)', fontsize=10)
    axes[1].set_ylabel('spread of the measured gradient (log scale)', fontsize=10)
    axes[1].set_title('Four times the batch halves the noise', fontsize=11.5,
                      weight='bold', color=INK)
    axes[1].legend(fontsize=9.0, frameon=False, loc='lower left')
    axes[1].grid(True, which='major', color=GRID, lw=0.5)
    fig.suptitle('Measured at slope 1.50 and offset 5.00, over 4,000 random batches '
                 'of each size',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'gradient-noise.svg')


# ---------------- section 6: local minima and saddle points ----------------

XW: Arr = np.array([0.7, 1.1, 1.6, 2.2, 2.9])
YW: Arr = np.sin(1.3 * XW)


def _wavy(w: Arr | float) -> Arr:
    w = np.atleast_1d(np.asarray(w, dtype=float))
    return np.mean((np.sin(w[:, None] * XW[None, :]) - YW[None, :]) ** 2, axis=1)


def _wavy_slope(w: float) -> float:
    e = np.sin(w * XW) - YW
    return float(np.mean(2.0 * e * XW * np.cos(w * XW)))


def two_valleys() -> None:
    ws = np.linspace(0.0, 7.0, 7001)
    curve = _wavy(ws)
    mins = [i for i in range(1, len(ws) - 1)
            if curve[i] < curve[i - 1] and curve[i] <= curve[i + 1]]
    print('[g6] the wavy one-weight loss has bottoms at w = '
          + ', '.join(f'{ws[i]:.3f} (loss {curve[i]:.4f})' for i in mins))
    runs = []
    for start, colour in ((1.0, SLIDE), (4.6, GRIP)):
        w = start
        hist = [w]
        for _ in range(400):
            w = w - 0.25 * _wavy_slope(w)
            hist.append(w)
        runs.append((start, np.array(hist), colour))
        print(f'[g6] a run started at w = {start:.1f} settles at w = {w:.4f} with a '
              f'loss of {_wavy(w)[0]:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white')
    _plain(axes[0])
    print(f'[g6] the wavy loss rises to {curve.max():.4f} at w = '
          f'{ws[int(np.argmax(curve))]:.3f}')
    axes[0].plot(ws, curve, color=INK, lw=2.4)
    for start, hist, colour in runs:
        axes[0].plot(hist, _wavy(hist), color=colour, lw=1.3, ls='--')
        axes[0].scatter(hist[::6], _wavy(hist[::6]), s=28, color=colour, zorder=4)
        axes[0].scatter([start], [_wavy(start)[0]], s=130, marker='s', color=colour,
                        edgecolor=INK, lw=0.7, zorder=5)
        axes[0].text(start + 0.12, _wavy(start)[0], f'start at {start:.1f}', fontsize=9.5,
                     color=colour, ha='left', va='center')
    for i in mins:
        axes[0].text(ws[i], curve[i] - 0.04, f'{curve[i]:.3f}', fontsize=9.5, color=SLIDE,
                     ha='center', va='top', weight='bold')
    axes[0].set_xlabel('the one weight, w', fontsize=10)
    axes[0].set_ylabel('mean squared error', fontsize=10)
    axes[0].set_xlim(0, 7)
    axes[0].set_ylim(-0.16, float(curve.max()) * 1.12)
    axes[0].set_title('Four bottoms, with their losses, and two runs',
                      fontsize=11, weight='bold', color=INK)
    _plain(axes[1])
    for start, hist, colour in runs:
        axes[1].semilogy(np.maximum(_wavy(hist), 1e-7), color=colour, lw=2.0,
                         label=f'started at w = {start:.1f}, ends at w = {hist[-1]:.3f}')
    axes[1].set_xlim(0, 60)
    axes[1].set_ylim(1e-7, 3)
    axes[1].set_xlabel('step number', fontsize=10)
    axes[1].set_ylabel('mean squared error (log scale)', fontsize=10)
    axes[1].set_title('One run ends near zero, the other well above it',
                      fontsize=11, weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='center right')
    axes[1].grid(True, which='major', color=GRID, lw=0.5)
    fig.suptitle('A one-weight model whose prediction is sin(w x): '
                 'where you start decides where you stop',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'two-valleys.svg')


def _saddle(a: Arr | float, b: Arr | float) -> Arr:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return 0.5 * a ** 2 - 0.5 * b ** 2 + 0.25 * b ** 4


def a_saddle() -> None:
    eta = 0.1
    a, b = 1.0, 0.03
    path = [(a, b)]
    for _ in range(120):
        ga = a
        gb = -b + b ** 3
        a -= eta * ga
        b -= eta * gb
        path.append((a, b))
    p = np.array(path)
    vals = _saddle(p[:, 0], p[:, 1])
    flat = int(np.argmax(vals < vals[0] * 0.02))
    print(f'[g6] the saddle sits at a = 0, b = 0 with a loss of '
          f'{_saddle(0.0, 0.0):.4f}; the two bottoms are at b = -1 and b = +1 with a '
          f'loss of {_saddle(0.0, 1.0):.4f}')
    print(f'[g6] a run from a = 1.00, b = 0.03 reaches a loss of {vals[flat]:.4f} after '
          f'{flat} steps, then sits near the saddle, and ends at a = {p[-1, 0]:.4f}, '
          f'b = {p[-1, 1]:.4f} with a loss of {vals[-1]:.4f}')
    print('[g6] loss at steps 0, 10, 30, 50, 70, 90, 120: '
          + ', '.join(f'{vals[k]:.4f}' for k in (0, 10, 30, 50, 70, 90, 120)))

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    _plain(axes[0])
    ga = np.linspace(-1.2, 1.2, 300)
    gb = np.linspace(-1.5, 1.5, 300)
    A, B = np.meshgrid(ga, gb)
    Z = _saddle(A, B)
    cs = axes[0].contour(A, B, Z, levels=np.array([-0.24, -0.2, -0.1, 0.0, 0.1, 0.3, 0.6,
                                                   1.0]),
                         colors=LINK, linewidths=1.1)
    axes[0].clabel(cs, fmt='%.2f', fontsize=8, colors=INK)
    axes[0].plot(p[:, 0], p[:, 1], color=GRIP, lw=1.8)
    axes[0].scatter(p[::4, 0], p[::4, 1], s=20, color=GRIP, zorder=4)
    axes[0].scatter([0.0], [0.0], s=140, marker='X', color=INK, zorder=6)
    axes[0].text(-0.08, -0.1, 'the saddle', fontsize=9.5, color=INK, ha='right',
                 va='top')
    axes[0].scatter([0.0, 0.0], [1.0, -1.0], s=170, marker='*', color=SLIDE,
                    edgecolor=INK, lw=0.7, zorder=6)
    axes[0].text(0.10, 1.20, 'a real bottom', fontsize=9.5, color=SLIDE, ha='left')
    axes[0].set_xlabel('first weight, a', fontsize=10)
    axes[0].set_ylabel('second weight, b', fontsize=10)
    axes[0].set_title('A saddle point: uphill along a, downhill along b', fontsize=11.5,
                      weight='bold', color=INK)
    _plain(axes[1])
    axes[1].plot(vals, color=GRIP, lw=2.2)
    axes[1].axhline(float(_saddle(0.0, 0.0)), color=INK, ls='--', lw=1.3)
    axes[1].text(55, 0.03, 'the height of the saddle', fontsize=10, color=INK)
    axes[1].axhline(float(_saddle(0.0, 1.0)), color=SLIDE, ls='--', lw=1.3)
    axes[1].text(55, -0.22, 'the height of the bottom', fontsize=10, color=SLIDE)
    axes[1].set_xlabel('step number', fontsize=10)
    axes[1].set_ylabel('loss', fontsize=10)
    axes[1].set_title('The loss sits almost still for about 40 steps, then falls again',
                      fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('A made-up two-weight loss with a saddle at the origin, '
                 'and 120 real steps across it',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'a-saddle.svg')


def all_directions_up() -> None:
    rng = np.random.default_rng(17)
    dims = list(range(1, 9))
    trials = 200000
    frac = []
    for d in dims:
        m = rng.normal(size=(trials, d, d))
        m = (m + np.transpose(m, (0, 2, 1))) / np.sqrt(2.0)
        ev = np.linalg.eigvalsh(m)
        f = float(np.mean(np.all(ev > 0, axis=1)))
        frac.append(f)
        print(f'[g6] {d:2d} weights: {f * trials:.0f} of {trials} random flat points '
              f'curve upwards in every direction, a share of {f:.6f}; '
              f'the coin-flip estimate is {0.5 ** d:.6f}')
    frac_arr = np.array(frac)
    coin = 0.5 ** np.array(dims, dtype=float)

    shown = [(d, f) for d, f in zip(dims, frac_arr) if f > 0]
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(axes[0])
    axes[0].semilogy([d for d, _ in shown], [f for _, f in shown], marker='o', color=GRIP,
                     lw=2.2, label='measured on 200,000 random flat points')
    axes[0].semilogy(dims, coin, marker='s', ls='--', color=MUTED, lw=1.8,
                     label='one half, multiplied by itself once per weight')
    for d, f in shown:
        if d in (1, 2, 3, 4):
            axes[0].text(d + 0.12, f * 1.5, f'{f:.4f}', fontsize=9.5, color=INK)
    axes[0].text(0.97, 0.21, 'at 7 and 8 weights not one\nof the 200,000 was a bottom',
                 transform=axes[0].transAxes, fontsize=9.0, color=GRIP, ha='right',
                 va='top')
    axes[0].set_xlabel('number of weights', fontsize=10)
    axes[0].set_ylabel('share of flat points that are bottoms (log scale)', fontsize=10)
    axes[0].set_ylim(1e-7, 4.0)
    axes[0].set_title('A flat point is a bottom only if the loss\ncurves up in every '
                      'direction',
                      fontsize=11, weight='bold', color=INK)
    axes[0].legend(fontsize=9.0, frameon=False, loc='lower left')
    axes[0].grid(True, which='major', color=GRID, lw=0.5)
    _plain(axes[1])
    d_show = 8
    m = rng.normal(size=(1, d_show, d_show))
    m = (m + np.transpose(m, (0, 2, 1))) / np.sqrt(2.0)
    ev = np.linalg.eigvalsh(m)[0]
    cols = [SLIDE if v > 0 else GRIP for v in ev]
    axes[1].bar(np.arange(1, d_show + 1), ev, color=cols, edgecolor=INK, lw=0.6,
                width=0.6)
    axes[1].axhline(0, color=INK, lw=1.2)
    for i, v in enumerate(ev, start=1):
        axes[1].text(i, v + (0.12 if v > 0 else -0.28), f'{v:+.2f}', ha='center',
                     fontsize=9.0, color=INK)
    axes[1].set_xticks(np.arange(1, d_show + 1))
    axes[1].set_xlabel('direction through the eight-weight space', fontsize=10)
    axes[1].set_ylabel('how the loss curves in that direction', fontsize=10)
    axes[1].set_ylim(-7.0, 4.2)
    axes[1].set_title(f'One random flat point in eight weights:\n'
                      f'{int(np.sum(ev < 0))} of the 8 directions go downhill',
                      fontsize=11, weight='bold', color=INK)
    fig.suptitle('Why a network with millions of weights almost never gets stuck: '
                 'nearly every flat point still has a way down',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'all-directions-up.svg')


def _train_small_net(seed: int, steps: int = 3000, hidden: int = 8,
                     lr: float = 0.08) -> tuple[Arr, Arr]:
    """Train a one-hidden-layer tanh network by plain full-batch gradient descent."""
    rng = np.random.default_rng(seed)
    nx = np.random.default_rng(5)
    x = nx.uniform(-2.0, 2.0, 25)
    y = np.sin(1.6 * x) + 0.3 * x + nx.normal(0.0, 0.05, 25)
    X = x[:, None]
    Y = y[:, None]
    w1 = rng.normal(0.0, 1.0, (1, hidden))
    b1 = rng.normal(0.0, 0.5, hidden)
    w2 = rng.normal(0.0, 1.0 / np.sqrt(hidden), (hidden, 1))
    b2 = np.zeros(1)
    hist = []
    for _ in range(steps):
        h = np.tanh(X @ w1 + b1)
        out = h @ w2 + b2
        err = out - Y
        hist.append(float(np.mean(err ** 2)))
        gout = 2.0 * err / len(X)
        gw2 = h.T @ gout
        gb2 = gout.sum(0)
        gh = (gout @ w2.T) * (1 - h ** 2)
        gw1 = X.T @ gh
        gb1 = gh.sum(0)
        w1 -= lr * gw1
        b1 -= lr * gb1
        w2 -= lr * gw2
        b2 -= lr * gb2
    h = np.tanh(X @ w1 + b1)
    hist.append(float(np.mean((h @ w2 + b2 - Y) ** 2)))
    grid = np.linspace(-2.2, 2.2, 200)
    hg = np.tanh(grid[:, None] @ w1 + b1)
    return np.array(hist), (hg @ w2 + b2)[:, 0]


def many_starts_same_loss() -> None:
    runs = [_train_small_net(100 + k) for k in range(12)]
    finals = np.array([r[0][-1] for r in runs])
    print(f'[g6] twelve runs of the same small network from twelve random starting '
          f'points: final losses from {finals.min():.5f} to {finals.max():.5f}, '
          f'average {finals.mean():.5f}')
    print('[g6] all twelve final losses: ' + ', '.join(f'{v:.5f}' for v in finals))
    print(f'[g6] the worst run ends {finals.max() / finals.min():.2f} times the loss of '
          f'the best one, while the starting losses ranged from '
          f'{min(r[0][0] for r in runs):.4f} to {max(r[0][0] for r in runs):.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    _plain(axes[0])
    for hist, _ in runs:
        axes[0].semilogy(hist, color=LINK, lw=1.1, alpha=0.8)
    axes[0].set_xlabel('step number', fontsize=10)
    axes[0].set_ylabel('mean squared error (log scale)', fontsize=10)
    axes[0].set_title('Twelve runs, twelve random starts, 3,000 steps each',
                      fontsize=11.5, weight='bold', color=INK)
    axes[0].grid(True, which='major', color=GRID, lw=0.5)
    _plain(axes[1])
    axes[1].hist(finals, bins=np.linspace(finals.min() * 0.9, finals.max() * 1.1, 14),
                 color=SLIDE, edgecolor=INK, lw=0.6)
    axes[1].axvline(float(finals.mean()), color=GRIP, lw=1.8, ls='--')
    axes[1].text(finals.mean(), 3.4, f' average {finals.mean():.5f}', fontsize=10,
                 color=GRIP)
    axes[1].set_xlabel('loss at the end of the run', fontsize=10)
    axes[1].set_ylabel('how many of the twelve runs', fontsize=10)
    axes[1].set_title(f'All twelve end between {finals.min():.4f} and '
                      f'{finals.max():.4f}',
                      fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('A network with 25 weights, trained twelve times on the same 25 '
                 'simulated examples',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DESC_DOC, 'many-starts-same-loss.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    # 01_the-score-of-being-wrong.md
    error_per_example()
    two_models_no_winner()
    counting_versus_measuring()
    the_error_table()
    penalty_shapes()
    three_models_two_rankings()
    one_wild_reading()
    softmax_arithmetic()
    softmax_shift_and_spread()
    three_cases_probabilities()
    minus_log_curve()
    three_cases_loss()
    batch_average()
    five_points_three_lines()
    loss_against_weight()
    squared_and_absolute_landscape()
    cross_entropy_landscape()
    huber_curve()
    fitted_under_three_losses()
    why_not_squared_for_a_choice()
    # 02_gradient-descent.md
    tiny_nudge()
    slope_at_three_places()
    nudge_gets_smaller()
    first_steps_table()
    steps_on_the_curve()
    loss_against_step()
    step_shrinks_as_it_arrives()
    three_rates_on_the_curve()
    three_rates_loss()
    rate_sweep()
    two_weight_contours()
    downhill_arrows()
    valley_shape()
    two_weight_loss_curve()
    one_epoch()
    full_batch_versus_mini_batch()
    cost_in_examples()
    gradient_noise()
    two_valleys()
    a_saddle()
    all_directions_up()
    many_starts_same_loss()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
