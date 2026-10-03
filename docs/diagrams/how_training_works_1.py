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
    top = 0.0
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-(n_row + 1) * row_h - 0.25, 0.9)
    for c, (x, head) in enumerate(zip(centres, headers)):
        ax.text(x, 0.25, head, ha='center', va='center', fontsize=fontsize,
                weight='bold', color=INK)
    ax.plot([0, 1], [-0.1, -0.1], color=INK, lw=1.2)
    for r, row in enumerate(rows):
        y = top - (r + 0.65) * row_h - 0.1
        if r % 2 == 1:
            ax.add_patch(Rectangle((0, y - row_h / 2), 1, row_h, facecolor='#f4f4f4',
                                   edgecolor='none', zorder=0))
        for c, (x, cell) in enumerate(zip(centres, row)):
            col = colours[c] if colours else INK
            ax.text(x, y, cell, ha='center', va='center', fontsize=fontsize, color=col,
                    zorder=3)
    if foot:
        y = top - (len(rows) + 0.65) * row_h - 0.25
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
    ax.text(0.6, 38.4, 'the eight numbers above the lines are the whole story of how wrong '
            'this model is', fontsize=10, color=MUTED)
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
                     xy=(2.4, 1.0), xytext=(2.08, 3.4), fontsize=9.5, color=INK,
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
    ax.text(0.5, -10.7, 'mean squared error = 36 / 8 = 4.50 mm$^2$        '
            'mean absolute error = 14 / 8 = 1.75 mm',
            ha='center', fontsize=11, color=INK)
    _save(fig, SCORE_DOC, 'the-error-table.svg')


def penalty_shapes() -> None:
    e = np.linspace(-5, 5, 801)
    print(f'[s2] penalty at an error of 1 mm: squared {1.0 ** 2:.0f}, absolute {1.0:.0f}')
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
    axes[1].set_ylim(0, 19.5)
    axes[1].set_title("Model A's eight errors under both penalties", fontsize=11.5,
                      weight='bold', color=INK)
    axes[1].legend(fontsize=9.5, frameon=False, loc='upper left')
    axes[1].text(2.2, 17.2, 'part 7, the 4 mm miss, is 16 of the 36 squared total\n'
                 'but only 4 of the 14 absolute total', fontsize=9.5, color=INK)
    fig.suptitle('Squaring an error of 4 mm gives it four times the weight that its '
                 'size alone would',
                 fontsize=13, weight='bold', color=INK)
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
    ax.text(0.0, 0.88, 'The two losses disagree', fontsize=11.5, weight='bold', color=INK)
    ax.text(0.0, 0.62, 'By error size:  C, then A, then B.', fontsize=10.5, color=TEAL)
    ax.text(0.0, 0.44, 'By squared error:  B, then A, then C.', fontsize=10.5, color=PURPLE)
    ax.text(0.0, 0.18, 'C is best on one and worst on the\nother, because its one 12 mm\n'
            'miss becomes 144 when squared.', fontsize=10, color=INK)
    fig.suptitle('Three models, eight parts each: picking the loss picks the winner',
                 fontsize=13, weight='bold', color=INK)
    _save(fig, SCORE_DOC, 'three-models-two-rankings.svg')


def one_wild_reading() -> None:
    grid = np.linspace(4.0, 8.0, 4001)
    out: dict[str, tuple[float, float]] = {}
    for label, data in (('seven good readings', FORCE7), ('with the glitch', FORCE8)):
        sq = np.array([np.mean((g - data) ** 2) for g in grid])
        ab = np.array([np.mean(np.abs(g - data)) for g in grid])
        best_sq = float(grid[int(np.argmin(sq))])
        best_ab = float(grid[int(np.argmin(ab))])
        out[label] = (best_sq, best_ab)
        print(f'[s2] {label}: readings {", ".join(f"{v:.1f}" for v in data)}')
        print(f'[s2] {label}: squared error is lowest at {best_sq:.3f} N '
              f'(the average is {data.mean():.3f}), absolute error is lowest at '
              f'{best_ab:.3f} N (the middle reading is {np.median(data):.3f})')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white')
    for ax, (label, data) in zip(axes, (('seven good readings', FORCE7),
                                        ('with one glitched reading', FORCE8))):
        _plain(ax)
        key = 'seven good readings' if len(data) == 7 else 'with the glitch'
        sq = np.array([np.mean((g - data) ** 2) for g in grid])
        ab = np.array([np.mean(np.abs(g - data)) for g in grid])
        ax.plot(grid, sq, color=PURPLE, lw=2.4, label='squared error')
        ax.plot(grid, ab, color=TEAL, lw=2.4, label='absolute error')
        bsq, bab = out[key]
        ax.axvline(bsq, color=PURPLE, ls='--', lw=1.3)
        ax.axvline(bab, color=TEAL, ls=':', lw=1.6)
        ax.scatter(data, np.full(len(data), -1.2), s=70, marker='|', color=INK,
                   linewidths=2.0, clip_on=False)
        ax.text(bsq, 21.5, f'{bsq:.2f} N', color=PURPLE, fontsize=10.5, ha='center',
                weight='bold')
        ax.text(bab, 18.0, f'{bab:.2f} N', color=TEAL, fontsize=10.5, ha='center',
                weight='bold')
        ax.set_xlim(4.0, 8.0)
        ax.set_ylim(0, 24)
        ax.set_xlabel('the one number the model gives, in newtons', fontsize=10)
        ax.set_ylabel('loss', fontsize=10)
        ax.set_title(label, fontsize=11.5, weight='bold', color=INK)
        ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    axes[1].text(4.08, 12.0, 'one bad reading of 19 N drags the\nsquared-error answer from 5.00 to 6.75,\n'
                 'while the absolute-error answer\nmoves from 5.00 to 5.05', fontsize=9.8,
                 color=INK)
    fig.suptitle('The best single guess for a grip force, before and after one sensor glitch',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SCORE_DOC, 'one-wild-reading.svg')
