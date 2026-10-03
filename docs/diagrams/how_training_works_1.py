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
    _table(axes[0], ['class', 'logit', 'e raised to it', 'divided by the total',
                     'probability'],
           rows, [1.0, 0.9, 1.45, 1.75, 1.2],
           colours=[INK, LINK, WRIST, MUTED, SLIDE], fontsize=10.5, row_h=1.0, foot=foot)
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
    axes[1].set_ylim(0, 1.18)
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
    axes[1].text(1.55, guess + 0.1, f'guessing = {guess:.3f}', fontsize=10, color=MUTED)
    axes[1].set_ylim(0, 4.8)
    axes[1].set_ylabel('cross-entropy loss', fontsize=10)
    axes[1].tick_params(labelsize=10)
    axes[1].set_title('What the loss charged for it', fontsize=11.5, weight='bold',
                      color=INK)
    fig.suptitle('An unsure right answer costs about 11 times a sure right answer, '
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
    axes[1].text(1.0, losses.mean() + 0.1, f'average over the batch = {losses.mean():.3f}',
                 fontsize=10.5, color=GRIP, weight='bold')
    axes[1].set_xticks(idx)
    axes[1].set_xlabel('picture in the batch', fontsize=10)
    axes[1].set_ylabel('cross-entropy loss', fontsize=10)
    axes[1].set_ylim(0, 3.9)
    axes[1].set_title('Picture 5 carries most of the average', fontsize=11.5,
                      weight='bold', color=INK)
    fig.suptitle('One batch of six pictures: 83% named right, '
                 'and 71% of the loss comes from the one failure',
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
    for w, colour in zip(CAND_W, [LINK, TEAL, SLIDE, JOINT, GRIP]):
        lo = float(mse_w(w)[0])
        ax.scatter([w], [lo], s=95, color=colour, edgecolor=INK, lw=0.7, zorder=5)
        ax.plot([w, w], [0, lo], color=colour, lw=1.0, ls=':')
        ax.text(w, lo + 1.6, f'w={w:.1f}\n{lo:.2f}', ha='center', fontsize=9.5,
                color=colour, weight='bold')
    ax.scatter([W_STAR], [L_STAR], s=130, marker='v', color=INK, zorder=6)
    ax.annotate(f'the bottom: w = {W_STAR:.3f}, loss = {L_STAR:.4f} mm$^2$',
                xy=(W_STAR, L_STAR), xytext=(3.3, 12.0), fontsize=10.5, color=INK,
                weight='bold', arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))
    ax.set_xlim(1.0, 5.0)
    ax.set_ylim(0, 48)
    ax.set_xlabel('the one weight, w', fontsize=10)
    ax.set_ylabel('mean squared error over the five parts (mm$^2$)', fontsize=10)
    ax.set_title('The loss landscape of a model with one weight, worked out at 801 '
                 'settings of w',
                 fontsize=12.5, weight='bold', color=INK)
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
    axes[1].plot(ws, ab, color=TEAL, lw=2.6)
    for r in ratios:
        axes[1].axvline(r, color=GRID, lw=1.0, zorder=0)
        axes[1].text(r, 0.02, f'{r:.3f}', rotation=90, fontsize=8.5, color=MUTED,
                     ha='right', va='bottom')
    axes[1].scatter([best_ab], [ab.min()], s=100, color=INK, zorder=5)
    axes[1].text(best_ab + 0.02, ab.min() + 0.12, f'bottom at a kink\nw = {best_ab:.3f}',
                 fontsize=10, color=INK)
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
    ws = np.linspace(-1.0, 4.0, 5001)
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
    axes[0].legend(fontsize=9.5, frameon=False, loc='center right')
    _plain(axes[1])
    axes[1].plot(ws, ce, color=GRIP, lw=2.6)
    axes[1].scatter([best], [ce.min()], s=110, marker='v', color=INK, zorder=5)
    axes[1].text(best + 0.1, ce.min() + 0.08, f'bottom: w = {best:.3f},\n'
                 f'loss = {ce.min():.4f}', fontsize=10, color=INK)
    axes[1].axhline(float(np.log(2)), color=MUTED, ls='--', lw=1.2)
    axes[1].text(2.2, np.log(2) + 0.02, f'w = 0 says 0.5 to everything: {np.log(2):.3f}',
                 fontsize=9.5, color=MUTED)
    axes[1].set_xlabel('the one weight, w', fontsize=10)
    axes[1].set_ylabel('mean cross-entropy over the seven grips', fontsize=10)
    axes[1].set_ylim(0.3, 1.3)
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

    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(e, 0.5 * e ** 2, color=PURPLE, lw=2.4, label='half the squared error')
    ax.plot(e, np.abs(e), color=TEAL, lw=2.4, label='the error size')
    ax.plot(e, hub, color=WRIST, lw=3.0, ls='-', label='Huber, switching at 1 mm')
    for s in (-1.0, 1.0):
        ax.axvline(s, color=GRID, lw=1.2)
    ax.text(0.0, 6.2, 'inside 1 mm the Huber penalty is the squared one',
            ha='center', fontsize=9.5, color=INK)
    ax.annotate('outside 1 mm it becomes a straight line,\n'
                'so one wild reading cannot dominate',
                xy=(2.8, 2.3), xytext=(1.35, 5.0), fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    ax.set_xlabel('error on one part (mm)', fontsize=10)
    ax.set_ylabel('penalty', fontsize=10)
    ax.set_ylim(-0.3, 7.4)
    ax.set_title('Three penalty shapes: the Huber loss is squared near zero and '
                 'straight far out',
                 fontsize=12.5, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    _save(fig, SCORE_DOC, 'huber-curve.svg')


def fitted_under_three_losses() -> None:
    grid = np.linspace(0.5, 4.0, 7001)
    sq = mse_w(grid, Y1_BAD * 0 + X1 * 0 + X1, Y1_BAD) if False else \
        np.array([float(np.mean((w * X1 - Y1_BAD) ** 2)) for w in grid])
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
    axes[0].text(0.3, 1.08, 'squared error can never charge more than 1', fontsize=9.5,
                 color=LINK)
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
