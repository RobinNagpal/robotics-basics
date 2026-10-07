"""Generate the diagrams for one page of docs/05_neural-networks/13_starting-your-own-model/.

    02_the-order-of-the-work.md -> images/starting-your-own-model/the-order-of-the-work/

Run with:  python3 starting_your_own_model_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so the document can quote the same values. No wall-clock
time is measured or drawn anywhere, because the machine this runs on is shared.

What is simulated, and what is real:

* The data is simulated. One example is a vector of 16 readings standing in for
  features already pulled out of a camera frame, and its label is one of ten
  classes. The readings are a class centre drawn from a seeded generator plus
  noise large enough that the ten classes overlap, so the job is learnable but
  not trivially so. One pool of 2,200 examples is drawn once, the first 600 are
  the held-back set for every run in this file, and the training examples are
  taken from the rest, so the split is fixed before any training happens. The
  regression figure reuses the same inputs with one number as the target.
* Everything done to that data is real. Every loss, accuracy, first-batch
  reading, plateau, learning curve, seed spread, probability matrix and
  sensitivity number comes from a real PyTorch model trained on the CPU with
  AdamW, and the planted bugs are planted in the real training loop: the input
  zeroed, the labels re-paired with the inputs on every step, the labels
  shuffled once and then left alone, every parameter frozen but the final bias,
  a hidden layer one unit wide, a learning rate of zero and a learning rate far
  too large.
* The shape chain is read off a real forward pass of a small convolutional
  network with hooks, and the weight counts are counted from its tensors.
* The run-folder sizes are the real byte sizes of a run folder this script
  writes into a temporary directory and then measures.
"""

import os

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import json  # noqa: E402
import pathlib  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
import torch  # noqa: E402
from torch import nn  # noqa: E402
import torch.nn.functional as F  # noqa: E402

torch.set_num_threads(1)

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'starting-your-own-model')
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

DOC: str = 'the-order-of-the-work'

Arr = NDArray[np.float64]

D_IN: int = 16
K: int = 10
NOISE: float = 2.0

# The sizes of the runs the page describes. The ladder picture in section 1 and
# the experiments further down read the same constants, so the two cannot
# disagree about what a rung costs.
RUNG1_BATCH: int = 64
RUNG2_N: int = 10
RUNG2_STEPS: int = 400
RUNG3_N: int = 960
RUNG3_BATCH: int = 32
RUNG3_PASSES: int = 25
RUNG4_RUNS: int = 9

N_HELD_BACK: int = 600


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
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _box(ax: Axes, x: float, y: float, w: float, h: float, colour: str,
         alpha: float = 0.18, lw: float = 1.4) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, edgecolor=colour,
                           alpha=alpha, lw=0))
    ax.add_patch(Rectangle((x, y), w, h, facecolor='none', edgecolor=colour, lw=lw))


# --------------------------------------------------------------------------
# the simulated data, drawn once, and split once
# --------------------------------------------------------------------------

def make_data(n: int, seed: int, k: int = K, d: int = D_IN,
              noise: float = NOISE) -> tuple[torch.Tensor, torch.Tensor]:
    """n simulated examples: d readings each, one of k classes."""
    rng = np.random.default_rng(1000 + seed)
    centres = np.random.default_rng(7).normal(0.0, 1.0, (k, d)) * 1.5
    y = rng.integers(0, k, n)
    x = centres[y] + rng.normal(0.0, noise, (n, d))
    return (torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.long))


POOL_X, POOL_Y = make_data(2200, seed=40)
VAL_X, VAL_Y = POOL_X[:N_HELD_BACK], POOL_Y[:N_HELD_BACK]
TRAIN_X, TRAIN_Y = POOL_X[N_HELD_BACK:], POOL_Y[N_HELD_BACK:]


def mlp(width: int, seed: int, d: int = D_IN, k: int = K) -> nn.Sequential:
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(d, width), nn.ReLU(), nn.Linear(width, k))


def balanced_ten() -> tuple[torch.Tensor, torch.Tensor]:
    """One training example of each of the ten classes, which is the batch to
    memorise at rung 2: every class has to be in it or the test proves less."""
    pick: list[int] = []
    for c in range(K):
        pick.append(int((TRAIN_Y == c).nonzero()[0]))
    idx = torch.tensor(pick)
    return TRAIN_X[idx], TRAIN_Y[idx]


# --------------------------------------------------------------------------
# section 1: the ladder and what each rung costs
# --------------------------------------------------------------------------

RUNGS: list[tuple[str, str]] = [
    ('1  one batch through an untrained model', 'the data, the shapes and the loss'),
    ('2  memorise ten examples on purpose', 'the loop, the gradients and the labels'),
    ('3  one small honest run with a split', 'that the job is learnable at all'),
    ('4  scale, one change at a time', 'which change is worth paying for'),
]

CAUSES: list[tuple[str, int]] = [
    ('the loader hands back the wrong file', 1),
    ('the pictures arrive in the wrong shape', 1),
    ('a label falls outside the list of classes', 1),
    ('the last layer has the wrong number of outputs', 1),
    ('the loss does not match the job', 1),
    ('the input never reaches the output', 2),
    ('the labels are not lined up with the inputs', 2),
    ('the optimiser was never given the weights', 2),
    ('the learning rate is far too small or too large', 2),
    ('the model is too small for the job', 3),
    ('there are far too few examples', 3),
    ('the split leaks, so the held-back loss lies', 3),
    ('the recipe stops improving with more of anything', 4),
]


def rung_costs() -> list[int]:
    """Example-views spent at each rung, from the run sizes used in this file."""
    r1 = RUNG1_BATCH
    r2 = RUNG2_STEPS * RUNG2_N
    r3 = RUNG3_PASSES * RUNG3_N
    r4 = RUNG4_RUNS * RUNG3_PASSES * RUNG3_N
    return [r1, r2, r3, r4]


def fig_ladder() -> None:
    costs = rung_costs()
    cum = np.cumsum(costs)
    print('[1.1] rung costs in example-views: ' + '  '.join(
        f'{i + 1}:{c:,}' for i, c in enumerate(costs)))
    print('[1.1] cumulative: ' + '  '.join(f'{i + 1}:{c:,}' for i, c in enumerate(cum)))

    fig, ax = plt.subplots(figsize=(11.8, 5.6), facecolor='white')
    _bare(ax)
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 4.9)
    colours = [TEAL, SLIDE, LINK, PURPLE]
    for i, ((name, proves), colour) in enumerate(zip(RUNGS, colours)):
        y = 0.35 + i * 1.08
        _box(ax, 0.3, y, 5.6, 0.86, colour, alpha=0.16)
        ax.text(0.55, y + 0.56, name, fontsize=12, weight='bold', color=INK)
        ax.text(0.55, y + 0.21, f'proves: {proves}', fontsize=10, color=INK)
        ax.text(6.15, y + 0.58, f'{costs[i]:,} example-views',
                fontsize=10.5, color=colour, weight='bold')
        ax.text(6.15, y + 0.22, f'{cum[i]:,} spent in all by the end of this rung',
                fontsize=9.5, color=MUTED)
        if i < len(RUNGS) - 1:
            ax.add_patch(FancyArrow(3.0, y + 0.88, 0.0, 0.16, width=0.03,
                                    head_width=0.16, head_length=0.06,
                                    color=MUTED, length_includes_head=True))
    ax.text(0.3, 4.62, 'Four rungs, climbed in this order because each one costs more '
                       'than the one below it',
            fontsize=12.5, weight='bold', color=INK)
    ax.text(0.3, 0.05, 'one example-view is one example put through the model once; '
                       'rung 4 is nine runs the size of rung 3',
            fontsize=9.5, color=MUTED, style='italic')
    _save(fig, DOC, 'the-ladder.svg')


def fig_cost_of_finding_late() -> None:
    costs = rung_costs()
    cum = np.cumsum(costs)
    labels = ['found at\nrung 1', 'found at\nrung 2', 'found at\nrung 3',
              'found at\nrung 4']
    print('[1.2] example-views spent before the same fault shows: ' + '  '.join(
        f'rung {i + 1}:{c:,}' for i, c in enumerate(cum)))
    print(f'[1.2] rung 4 costs {cum[3] / cum[0]:,.0f} times rung 1 '
          f'and {cum[3] / cum[1]:.1f} times rung 2')

    fig, ax = plt.subplots(figsize=(10.0, 5.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(labels, cum, color=[TEAL, SLIDE, LINK, PURPLE], width=0.62)
    ax.set_yscale('log')
    ax.set_ylim(10, cum[3] * 9)
    for b, c in zip(bars, cum):
        ax.text(b.get_x() + b.get_width() / 2, c * 1.3, f'{c:,}',
                ha='center', fontsize=11, weight='bold', color=INK)
    ax.set_ylabel('example-views spent before the fault shows (log scale)', fontsize=10)
    ax.set_title('One fault, four places it could be caught: the bill for finding it '
                 'late', fontsize=12, weight='bold')
    _save(fig, DOC, 'cost-of-finding-late.svg')


def fig_causes_ruled_out() -> None:
    open_after = [len(CAUSES)]
    for rung in (1, 2, 3, 4):
        open_after.append(sum(1 for _c, r in CAUSES if r > rung))
    print('[1.3] causes still open after each rung: ' + '  '.join(
        f'{i}:{v}' for i, v in enumerate(open_after)))

    fig, axl = plt.subplots(figsize=(10.4, 5.8), facecolor='white')
    _plain(axl)
    colours = {1: TEAL, 2: SLIDE, 3: LINK, 4: PURPLE}
    ys = np.arange(len(CAUSES))[::-1]
    for y, (cause, rung) in zip(ys, CAUSES):
        axl.plot([0.4, rung], [y, y], color=GRID, lw=1.2, zorder=1)
        axl.scatter([rung], [y], s=150, color=colours[rung], zorder=3)
        axl.text(rung + 0.1, y, cause, fontsize=10, va='center', color=INK)
    axl.set_xlim(0.4, 7.4)
    axl.set_ylim(-0.8, len(CAUSES) - 0.2)
    axl.set_yticks([])
    axl.spines['left'].set_visible(False)
    axl.set_xticks([1, 2, 3, 4])
    axl.set_xlabel('the rung that first rules this cause out', fontsize=10)
    axl.set_title('Thirteen things that go wrong, and where each one is caught',
                  fontsize=12, weight='bold')
    _save(fig, DOC, 'causes-ruled-out.svg')

    fig, axr = plt.subplots(figsize=(8.8, 5.0), facecolor='white')
    _plain(axr)
    axr.step(range(5), open_after, where='post', color=GRIP, lw=2.4)
    axr.scatter(range(5), open_after, s=55, color=GRIP, zorder=3)
    for i, v in enumerate(open_after):
        last = i == len(open_after) - 1
        axr.text(i + (0.16 if last else 0.0), v + (0.0 if last else 0.45), str(v),
                 ha='left' if last else 'center', va='center' if last else 'baseline',
                 fontsize=11, weight='bold', color=INK)
    axr.set_xticks(range(5))
    axr.set_xticklabels(['start', '1', '2', '3', '4'])
    axr.set_ylim(-0.6, len(CAUSES) + 1.6)
    axr.set_xlabel('rungs finished', fontsize=10)
    axr.set_ylabel('causes still open', fontsize=10)
    axr.set_title('How short the list of suspects gets, rung by rung',
                  fontsize=12, weight='bold')
    _save(fig, DOC, 'causes-still-open.svg')


# --------------------------------------------------------------------------
# section 2: the first batch through an untrained model
# --------------------------------------------------------------------------

def fig_first_loss_by_classes() -> None:
    ks = [2, 10, 80, 1000]
    lows: list[float] = []
    highs: list[float] = []
    mids: list[float] = []
    for k in ks:
        x, y = make_data(RUNG1_BATCH, seed=3, k=k)
        vals: list[float] = []
        for s in range(20):
            net = mlp(64, seed=100 + s, k=k)
            with torch.no_grad():
                vals.append(float(F.cross_entropy(net(x), y)))
        lows.append(min(vals))
        highs.append(max(vals))
        mids.append(float(np.mean(vals)))
        print(f'[2.1] classes={k:4d}  ln(classes)={np.log(k):.3f}  '
              f'20 untrained models give {min(vals):.3f} to {max(vals):.3f}, '
              f'average {np.mean(vals):.3f}')

    grid = np.arange(2, 1001)
    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(grid, np.log(grid), color=LINK, lw=2.2,
            label='the loss to expect from an untrained model: ln(classes)')
    ax.errorbar(ks, mids, yerr=[np.array(mids) - np.array(lows),
                                np.array(highs) - np.array(mids)],
                fmt='o', color=GRIP, ms=9, capsize=6, lw=1.8, zorder=4,
                label='20 untrained models, one batch of 64 each: average and range')
    for k, m, lo, hi in zip(ks, mids, lows, highs):
        offset = (14, 14) if k == 2 else (14, -40)
        ax.annotate(f'{k} classes\nln = {np.log(k):.3f}\nmeasured {lo:.3f} to {hi:.3f}',
                    (k, m), textcoords='offset points', xytext=offset,
                    fontsize=9.5, color=INK)
    ax.set_xscale('log')
    ax.set_xlim(1.7, 3200)
    ax.set_ylim(0, 8.4)
    ax.set_xlabel('number of classes (log scale)', fontsize=10)
    ax.set_ylabel('cross-entropy loss on the first batch', fontsize=10)
    ax.set_title('The first loss of an untrained classifier is ln(classes), and '
                 'checking it costs one forward pass', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, DOC, 'first-loss-by-classes.svg')


def fig_shape_chain() -> None:
    cnn = nn.Sequential(
        nn.Conv2d(3, 16, 3, stride=2, padding=1), nn.ReLU(),
        nn.Conv2d(16, 32, 3, stride=2, padding=1), nn.ReLU(),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(32, K))
    torch.manual_seed(11)
    picture = torch.randn(8, 3, 64, 64)
    chain: list[tuple[str, tuple[int, ...], int]] = [('the batch going in',
                                                      tuple(picture.shape),
                                                      int(picture.numel()))]
    names = {0: 'conv 3 to 16,\nstride 2', 2: 'conv 16 to 32,\nstride 2',
             4: 'average over\nthe picture', 5: 'flatten', 6: 'linear\n32 to 10'}
    out = picture
    with torch.no_grad():
        for i, layer in enumerate(cnn):
            out = layer(out)
            if i in names:
                chain.append((names[i], tuple(out.shape), int(out.numel())))
    params = sum(int(p.numel()) for p in cnn.parameters())
    for name, shape, n in chain:
        flat = name.replace('\n', ' ')
        print(f'[2.2] {flat:26s} shape={shape}  numbers={n:,}')
    print(f'[2.2] weights in the whole model: {params:,}')

    fig, ax = plt.subplots(figsize=(13.4, 4.6), facecolor='white')
    _bare(ax)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 3.9)
    colours = [MUTED, LINK, LINK, TEAL, TEAL, PURPLE]
    w = 1.8
    for i, ((name, shape, n), colour) in enumerate(zip(chain, colours)):
        x = 0.18 + i * 2.16
        _box(ax, x, 1.3, w, 1.72, colour, alpha=0.15)
        ax.text(x + w / 2, 2.62, name, ha='center', va='center', fontsize=9.5,
                color=INK, weight='bold', linespacing=1.3)
        ax.text(x + w / 2, 1.98, str(shape), ha='center', fontsize=11, color=colour,
                weight='bold')
        ax.text(x + w / 2, 1.52, f'{n:,} numbers', ha='center', fontsize=9.5,
                color=MUTED)
        if i < len(chain) - 1:
            ax.add_patch(FancyArrow(x + w + 0.04, 2.0, 0.28, 0.0, width=0.02,
                                    head_width=0.13, head_length=0.1, color=MUTED,
                                    length_includes_head=True))
    ax.plot([0.18, 0.18 + w], [1.14, 1.14], color=SLIDE, lw=2.6)
    ax.plot([0.18 + 5 * 2.16, 0.18 + 5 * 2.16 + w], [1.14, 1.14], color=SLIDE, lw=2.6)
    ax.text(0.18 + w / 2, 0.74, 'the 8 is the batch,\nand it must survive to the end',
            ha='center', fontsize=9.5, color=SLIDE)
    ax.text(0.18 + 5 * 2.16 + w / 2, 0.74,
            'the 10 is the classes,\nand it must match your labels',
            ha='center', fontsize=9.5, color=SLIDE)
    ax.text(0.18, 3.46, 'The shapes of one real forward pass, read off with hooks: '
                        f'this model holds {params:,} weights',
            fontsize=12.5, weight='bold', color=INK)
    _save(fig, DOC, 'shape-chain.svg')


def fig_planted_first_losses() -> None:
    x, y = make_data(RUNG1_BATCH, seed=3)
    rows: list[tuple[str, float]] = []

    net = mlp(64, seed=5)
    with torch.no_grad():
        rows.append(('a correct untrained model', float(F.cross_entropy(net(x), y))))

    big = mlp(64, seed=5)
    with torch.no_grad():
        big[2].weight *= 12.0
        rows.append(('the last layer started 12 times too large',
                     float(F.cross_entropy(big(x), y))))

    biased = mlp(64, seed=5)
    with torch.no_grad():
        biased[2].bias[3] += 9.0
        rows.append(('a bias left over, favouring one class',
                     float(F.cross_entropy(biased(x), y))))

    wrong_loss = mlp(64, seed=5)
    with torch.no_grad():
        onehot = F.one_hot(y, K).double()
        rows.append(('the wrong loss: squared error on the ten outputs',
                     float(((wrong_loss(x).double() - onehot) ** 2).mean())))

    double = mlp(64, seed=5)
    with torch.no_grad():
        rows.append(('softmax applied before the loss as well',
                     float(F.cross_entropy(F.softmax(double(x), dim=1), y))))

    for name, v in rows:
        print(f'[2.3] {name:54s} first loss = {v:.3f}')
    print(f'[2.3] ln(10) = {np.log(10):.3f}')

    names = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]
    colours = [MUTED, GRIP, GRIP, WRIST, JOINT][::-1]
    fig, ax = plt.subplots(figsize=(11.8, 5.0), facecolor='white')
    _plain(ax)
    bars = ax.barh(names, vals, color=colours, height=0.58)
    ax.set_xscale('log')
    ax.set_xlim(0.03, max(vals) * 9)
    ax.axvline(float(np.log(10)), color=INK, ls='--', lw=1.5)
    ax.set_ylim(-0.6, len(vals) - 0.1)
    ax.text(float(np.log(10)) * 1.08, len(vals) - 0.45,
            'ln(10) = 2.303, the number to expect', fontsize=9.5, color=INK)
    for b, v in zip(bars, vals):
        ax.text(v * 1.16, b.get_y() + b.get_height() / 2, f'{v:.3f}', va='center',
                fontsize=10.5, weight='bold', color=INK)
    ax.tick_params(labelsize=10)
    ax.set_xlabel('loss on the first batch, before any training (log scale)',
                  fontsize=10)
    ax.set_title('Five first losses from the same untrained model: three are visibly '
                 'wrong, one is right, and one bug hides', fontsize=12, weight='bold')
    _save(fig, DOC, 'planted-first-losses.svg')


def fig_first_loss_regression() -> None:
    x = TRAIN_X[:512]
    torch.manual_seed(21)
    direction = torch.randn(D_IN)
    raw = (x @ direction) * 48.0 + 310.0           # a target in millimetres
    std = (raw - raw.mean()) / raw.std()
    net = mlp(64, seed=5, k=1)
    with torch.no_grad():
        pred = net(x)[:, 0]
    mse_raw = float(((pred - raw) ** 2).mean())
    mse_std = float(((pred - std) ** 2).mean())
    var_raw = float(raw.var(unbiased=False))
    var_std = float(std.var(unbiased=False))
    mean_raw = float(((raw.mean() - raw) ** 2).mean())
    mean_std = float(((std.mean() - std) ** 2).mean())
    print(f'[2.4] raw target: average {float(raw.mean()):.1f} mm, '
          f'spread {float(raw.std()):.1f} mm, variance {var_raw:,.0f}, '
          f'untrained loss {mse_raw:,.0f}, always-the-average loss {mean_raw:,.0f}')
    print(f'[2.4] standardised target: variance {var_std:.3f}, '
          f'untrained loss {mse_std:.3f}, always-the-average loss {mean_std:.3f}')
    print(f'[2.4] the untrained model starts {float(pred.mean()):.3f} on average, '
          f'which is {float(raw.mean() - pred.mean()):.1f} mm from the target average, '
          f'and that gap squared is {float((raw.mean() - pred.mean()) ** 2):,.0f}')

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white')
    for ax, vals, ttl, fmt in (
            (axl, [mse_raw, mean_raw, var_raw], 'Target left in millimetres',
             '{:,.0f}'),
            (axr, [mse_std, mean_std, var_std], 'The same target, standardised',
             '{:.3f}')):
        _plain(ax)
        labs = ['untrained\nmodel', 'always the\naverage', 'the variance\nof the target']
        bars = ax.bar(labs, vals, color=[GRIP, LINK, MUTED], width=0.6)
        ax.set_ylim(0, max(vals) * 1.3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.04, fmt.format(v),
                    ha='center', fontsize=11, weight='bold', color=INK)
        ax.set_ylabel('mean squared error on the first batch', fontsize=10)
        if 'millimetres' in ttl:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda v, _p: f'{int(v):,}'))
        ax.set_title(ttl, fontsize=12, weight='bold')
    fig.suptitle('For a job that predicts a number, the first loss should be about the '
                 'variance of the target, and it only is once the target is centred',
                 fontsize=12.5, weight='bold')
    _save(fig, DOC, 'first-loss-regression.svg')


# --------------------------------------------------------------------------
# section 3: memorise ten examples on purpose
# --------------------------------------------------------------------------

def overfit(x: torch.Tensor, y: torch.Tensor, *, mode: str = 'correct',
            width: int = 64, lr: float = 0.05, steps: int = RUNG2_STEPS,
            seed: int = 0) -> tuple[list[float], list[float], torch.Tensor]:
    """Train on one fixed batch. mode plants a bug. Returns the losses, the share
    of the batch got right at each step, and the final probabilities."""
    net = mlp(width, seed)
    if mode == 'only-bias':
        for p in net.parameters():
            p.requires_grad_(False)
        net[2].bias.requires_grad_(True)
    params = [p for p in net.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr)
    gen = torch.Generator().manual_seed(seed + 101)
    target = y
    if mode == 'shuffle-once':
        target = y[torch.randperm(len(y), generator=torch.Generator().manual_seed(9))]
    losses: list[float] = []
    accs: list[float] = []
    for _s in range(steps):
        xb = torch.zeros_like(x) if mode == 'zero-input' else x
        yb = target
        if mode == 'repair':
            yb = target[torch.randperm(len(target), generator=gen)]
        out = net(xb)
        loss = F.cross_entropy(out, yb)
        accs.append(float((out.detach().argmax(1) == target).double().mean()))
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    with torch.no_grad():
        xb = torch.zeros_like(x) if mode == 'zero-input' else x
        probs = F.softmax(net(xb), dim=1)
    return losses, accs, probs


def fig_overfit_ten() -> None:
    x, y = balanced_ten()
    runs = {
        'everything correct': ('correct', SLIDE),
        'the input never reaches the output': ('zero-input', GRIP),
        'the labels re-paired with the inputs every step': ('repair', PURPLE),
    }
    out: dict[str, list[float]] = {}
    for label, (mode, _c) in runs.items():
        losses, _a, _p = overfit(x, y, mode=mode)
        out[label] = losses
        first_tiny = next((i for i, v in enumerate(losses) if v < 1e-4), None)
        print(f'[3.1] {label:48s} first {losses[0]:.3f}  '
              f'step 50 {losses[50]:.3e}  last {losses[-1]:.3e}  '
              f'first step under 1e-4: {first_tiny}')
    print(f'[3.1] ln(10) = {np.log(10):.4f}, and the ten labels are one of each class, '
          f'so guessing by how often each appears also gives {np.log(10):.4f}')

    fig, ax = plt.subplots(figsize=(11.0, 5.6), facecolor='white')
    _plain(ax)
    for label, (_m, colour) in runs.items():
        vals = np.maximum(np.array(out[label]), 1e-7)
        ax.plot(vals, color=colour, lw=2.0, label=label)
    ax.axhline(float(np.log(10)), color=INK, ls='--', lw=1.4)
    ax.text(RUNG2_STEPS * 0.30, 7.5,
            f'ln(10) = {np.log(10):.3f}: exactly where an untrained model starts',
            fontsize=9.5, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(5e-8, 30)
    ax.set_xlim(0, RUNG2_STEPS)
    ax.set_xlabel('step (every step is the same ten examples again)', fontsize=10)
    ax.set_ylabel('loss on those ten examples (log scale)', fontsize=10)
    ax.set_title('Ten examples, 400 steps: the healthy run reaches a millionth of '
                 'where it started and both planted bugs sit on ln(10)',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center left')
    _save(fig, DOC, 'overfit-ten.svg')


def fig_overfit_accuracy() -> None:
    x, y = balanced_ten()
    runs = [('everything correct', 'correct', SLIDE),
            ('the labels shuffled once, then left alone', 'shuffle-once', LINK),
            ('the labels re-paired every step', 'repair', PURPLE),
            ('the input never reaches the output', 'zero-input', GRIP)]
    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _plain(ax)
    for label, mode, colour in runs:
        _l, accs, _p = overfit(x, y, mode=mode)
        reached = next((i for i, a in enumerate(accs) if a >= 1.0), None)
        wide = mode == 'correct'
        ax.plot(np.array(accs) * 100, color=colour, lw=4.0 if wide else 2.0,
                ls='-' if mode != 'shuffle-once' else '--', label=label)
        print(f'[3.2] {label:44s} untrained {accs[0] * 100:5.1f}% right, '
              f'final {accs[-1] * 100:5.1f}% right, first step at 100%: {reached}')
    ax.set_ylim(-4, 112)
    ax.set_xlim(0, RUNG2_STEPS)
    ax.axhline(100, color=GRID, lw=1.2)
    ax.axhline(10, color=GRID, lw=1.2, ls=':')
    ax.text(RUNG2_STEPS * 0.55, 13.5, '10%: one of the ten, by luck', fontsize=9.5,
            color=MUTED)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('share of the ten examples it gets right (%)', fontsize=10)
    ax.set_title('Labels shuffled once are memorised just as easily, which is why this '
                 'test proves the machinery and not the meaning',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    _save(fig, DOC, 'overfit-accuracy.svg')


def fig_ten_at_random() -> None:
    """Why the ten examples are chosen one of each class rather than at random."""
    rng = np.random.default_rng(17)
    y = TRAIN_Y.numpy()
    draws = 4000
    present = np.array([len(np.unique(y[rng.choice(len(y), RUNG2_N, replace=False)]))
                        for _ in range(draws)])
    counts = np.bincount(present, minlength=K + 1)[1:K + 1]
    share = counts / draws * 100
    print(f'[3.2b] {draws} batches of {RUNG2_N} drawn at random hold '
          f'{present.mean():.1f} of the {K} classes on average, '
          f'and all {K} in {share[K - 1]:.1f}% of them')
    print('[3.2b] classes present: ' + '  '.join(
        f'{n}:{s:.1f}%' for n, s in zip(range(1, K + 1), share) if s > 0))

    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(1, K + 1), share, color=LINK, width=0.64)
    for b, s in zip(bars, share):
        if s >= 0.2:
            ax.text(b.get_x() + b.get_width() / 2, s + 0.8, f'{s:.1f}%', ha='center',
                    fontsize=10, weight='bold', color=INK)
    ax.axvline(K, color=SLIDE, lw=2.2)
    ax.text(K - 0.2, max(share) * 1.3, 'the batch you pick by hand sits here:\n'
            'one example of each class, all ten', fontsize=10, color=SLIDE,
            ha='right', va='top')
    ax.set_xticks(range(1, K + 1))
    ax.set_xlim(0.4, K + 0.9)
    ax.set_ylim(0, max(share) * 1.36)
    ax.set_xlabel(f'different classes present in a batch of {RUNG2_N}', fontsize=10)
    ax.set_ylabel(f'share of {draws:,} random batches (%)', fontsize=10)
    ax.set_title(f'Ten examples drawn at random hold {present.mean():.1f} of the ten '
                 'classes, so the test would prove less', fontsize=12, weight='bold')
    _save(fig, DOC, 'ten-at-random.svg')


def fig_rung_two_predicts_rung_three() -> None:
    """The claim the second rung rests on, measured: what fails ten also fails 240."""
    x, y = balanced_ten()
    widths = [1, 2, 4, 8, 16, 64]
    rung2: list[float] = []
    rung3: list[float] = []
    for w in widths:
        losses, _a, _p = overfit(x, y, mode='correct', width=w)
        rung2.append(max(losses[-1], 1e-7))
        rung3.append(final_val(width=w))
        print(f'[3.5] hidden layer {w:3d} units: ten examples end at {rung2[-1]:.4g}, '
              f'the real run ends at a held-back loss of {rung3[-1]:.3f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(rung2, rung3, color=MUTED, lw=1.4, ls='--', zorder=1)
    ax.scatter(rung2, rung3, s=110, color=[SLIDE if v < 1e-4 else GRIP for v in rung2],
               zorder=3)
    for w, a, b in zip(widths, rung2, rung3):
        ax.annotate(f'{w} unit' + ('' if w == 1 else 's'), (a, b),
                    textcoords='offset points',
                    xytext=(10, -4) if w != 64 else (12, 2), fontsize=10, color=INK)
    ax.axvline(1e-4, color=INK, ls=':', lw=1.5)
    ax.text(6e-5, max(rung3) * 0.99, 'green passed the second rung:\nunder 0.0001 on '
            'the ten examples', fontsize=9.5, color=INK, ha='right', va='top')
    ax.set_xscale('log')
    ax.set_xlim(2e-7, 20)
    ax.set_xlabel('loss on the ten examples after 400 steps, the second rung '
                  '(log scale)', fontsize=10)
    ax.set_ylabel('held-back loss after a real run on 240 examples,\nthe third rung',
                  fontsize=10)
    ax.set_title('Every model that cannot memorise the ten also loses the real run',
                 fontsize=12, weight='bold')
    _save(fig, DOC, 'rung-two-predicts-rung-three.svg')


def fig_plateau_fingerprints() -> None:
    x, y = balanced_ten()
    panels = [('everything correct', 'correct'),
              ('the input never reaches the output', 'zero-input'),
              ('the hidden layer is one unit wide', 'correct')]
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.8), facecolor='white')
    for ax, (title, mode) in zip(axes, panels):
        kw = {'width': 1} if 'one unit' in title else {}
        losses, accs, probs = overfit(x, y, mode=mode, **kw)   # type: ignore[arg-type]
        p = probs.numpy()
        row_spread = float(np.abs(p - p.mean(axis=0, keepdims=True)).max())
        print(f'[3.3] {title:38s} loss {losses[-1]:.4g}, {accs[-1] * 100:.0f}% right, '
              f'largest difference between two rows {row_spread:.4f}, '
              f'largest probability {p.max():.4f}')
        im = ax.imshow(p, cmap='Blues', vmin=0.0, vmax=1.0, aspect='auto')
        ax.set_xticks(range(K))
        ax.set_yticks(range(K))
        ax.set_xticklabels([str(c) for c in range(K)], fontsize=8.5)
        ax.set_yticklabels([str(c) for c in range(K)], fontsize=8.5)
        ax.set_xlabel('class the model gives weight to', fontsize=9.5)
        ax.set_ylabel('example (and its true class)', fontsize=9.5)
        ax.set_title(f'{title}\nloss {losses[-1]:.4g}, rows differ by at most '
                     f'{row_spread:.3f}', fontsize=10.5, weight='bold')
        for i in range(K):
            for j in range(K):
                if p[i, j] > 0.08:
                    ax.text(j, i, f'{p[i, j]:.2f}', ha='center', va='center',
                            fontsize=6.6,
                            color='white' if p[i, j] > 0.55 else INK)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    fig.suptitle('What each plateau is made of: the probabilities the three runs end up '
                 'giving the same ten examples', fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, DOC, 'plateau-fingerprints.svg')


def fig_bug_catalogue() -> None:
    x, y = balanced_ten()
    cases: list[tuple[str, dict[str, object]]] = [
        ('everything correct', {'mode': 'correct'}),
        ('the learning rate left at zero', {'mode': 'correct', 'lr': 0.0}),
        ('the learning rate 2000 times too large', {'mode': 'correct', 'lr': 100.0}),
        ('the hidden layer one unit wide', {'mode': 'correct', 'width': 1}),
        ('only the final bias allowed to move', {'mode': 'only-bias'}),
        ('the input never reaching the output', {'mode': 'zero-input'}),
        ('the labels re-paired every step', {'mode': 'repair'}),
    ]
    rows: list[tuple[str, float, float]] = []
    for label, kw in cases:
        losses, accs, _p = overfit(x, y, **kw)  # type: ignore[arg-type]
        rows.append((label, losses[-1], accs[-1]))
        print(f'[3.4] {label:42s} final loss {losses[-1]:.4g}  '
              f'{accs[-1] * 100:5.1f}% right')

    names = [r[0] for r in rows][::-1]
    vals = [max(r[1], 1e-7) for r in rows][::-1]
    accs = [r[2] for r in rows][::-1]
    colours = [SLIDE if a >= 1.0 else GRIP for a in accs]
    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _plain(ax)
    bars = ax.barh(names, vals, color=colours, height=0.6)
    ax.set_xscale('log')
    ax.set_xlim(5e-8, max(vals) * 90)
    ax.axvline(float(np.log(10)), color=INK, ls='--', lw=1.4)
    ax.set_ylim(-0.6, len(vals) - 0.1)
    ax.text(float(np.log(10)) * 1.12, len(vals) - 0.45, 'ln(10) = 2.303',
            fontsize=9.5, color=INK)
    note_x = max(vals) * 4.0
    for b, v, a in zip(bars, vals, accs):
        ax.text(note_x, b.get_y() + b.get_height() / 2,
                f'loss {v:.4g}, {a * 100:.0f}% right', va='center', fontsize=10,
                color=INK)
    ax.tick_params(labelsize=10)
    ax.set_xlabel('loss on the same ten examples after 400 steps (log scale)',
                  fontsize=10)
    ax.set_title('Seven single-batch runs: green memorised all ten, red could not, and '
                 'each red one leaves its own mark', fontsize=12, weight='bold')
    _save(fig, DOC, 'bug-catalogue.svg')


# --------------------------------------------------------------------------
# section 4: one small honest run
# --------------------------------------------------------------------------

def honest_run(n_train: int = RUNG3_N, *, width: int = 64, lr: float = 0.002,
               passes: int = RUNG3_PASSES, batch: int = RUNG3_BATCH, seed: int = 0,
               wd: float = 0.05, leak: int = 0) -> dict[str, object]:
    """Train on n_train examples from the fixed training pool and measure both
    losses after every pass. leak > 0 copies that many training rows into the
    held-back set, which is the mistake section 4 demonstrates."""
    xtr, ytr = TRAIN_X[:n_train], TRAIN_Y[:n_train]
    xva, yva = VAL_X, VAL_Y
    if leak > 0:
        xva = torch.cat([xtr[:leak], VAL_X[leak:]])
        yva = torch.cat([ytr[:leak], VAL_Y[leak:]])
    net = mlp(width, seed)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
    gen = torch.Generator().manual_seed(seed + 7)
    tr_loss: list[float] = []
    va_loss: list[float] = []
    tr_err: list[float] = []
    va_err: list[float] = []
    steps = 0
    for _p in range(passes):
        order = torch.randperm(n_train, generator=gen)
        for i in range(0, n_train, batch):
            sel = order[i:i + batch]
            loss = F.cross_entropy(net(xtr[sel]), ytr[sel])
            opt.zero_grad()
            loss.backward()
            opt.step()
            steps += 1
        with torch.no_grad():
            o_tr, o_va = net(xtr), net(xva)
            tr_loss.append(float(F.cross_entropy(o_tr, ytr)))
            va_loss.append(float(F.cross_entropy(o_va, yva)))
            tr_err.append(float((o_tr.argmax(1) != ytr).double().mean()))
            va_err.append(float((o_va.argmax(1) != yva).double().mean()))
    return {'tr_loss': tr_loss, 'va_loss': va_loss, 'tr_err': tr_err,
            'va_err': va_err, 'steps': steps, 'n_train': n_train}


def nearest_neighbour_error(n_train: int) -> float:
    xtr, ytr = TRAIN_X[:n_train], TRAIN_Y[:n_train]
    d = ((VAL_X[:, None, :] - xtr[None, :, :]) ** 2).sum(-1)
    return float((ytr[d.argmin(1)] != VAL_Y).double().mean())


def fig_first_honest_curve() -> None:
    r = honest_run()
    tr_loss: list[float] = r['tr_loss']        # type: ignore[assignment]
    va_loss: list[float] = r['va_loss']        # type: ignore[assignment]
    tr_err: list[float] = r['tr_err']          # type: ignore[assignment]
    va_err: list[float] = r['va_err']          # type: ignore[assignment]
    nn_err = nearest_neighbour_error(RUNG3_N)
    counts = torch.bincount(TRAIN_Y[:RUNG3_N], minlength=K)
    major = float((VAL_Y != int(counts.argmax())).double().mean())
    best = int(np.argmin(va_loss))
    print(f'[4.1] {r["steps"]} steps: {RUNG3_N} examples in batches of {RUNG3_BATCH} '
          f'over {RUNG3_PASSES} passes, {N_HELD_BACK} examples held back')
    print(f'[4.1] training loss {tr_loss[0]:.3f} -> {tr_loss[-1]:.3f}; '
          f'held-back loss {va_loss[0]:.3f} -> {va_loss[-1]:.3f}, '
          f'lowest {va_loss[best]:.3f} at pass {best + 1}')
    print(f'[4.1] wrong answers: training {tr_err[-1] * 100:.1f}%, '
          f'held back {va_err[-1] * 100:.1f}%; nearest neighbour {nn_err * 100:.1f}%, '
          f'always the commonest class {major * 100:.1f}%')

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.8, 5.2), facecolor='white')
    _plain(axl)
    axl.plot(range(1, len(tr_loss) + 1), tr_loss, color=LINK, lw=2.0,
             label='training loss')
    axl.plot(range(1, len(va_loss) + 1), va_loss, color=GRIP, lw=2.0,
             label='held-back loss')
    axl.fill_between(range(1, len(tr_loss) + 1), tr_loss, va_loss, color=GRIP,
                     alpha=0.1)
    axl.scatter([best + 1], [va_loss[best]], s=80, color=GRIP, zorder=4)
    axl.annotate(f'lowest held-back loss\n{va_loss[best]:.3f} at pass {best + 1}',
                 (best + 1, va_loss[best]), textcoords='offset points',
                 xytext=(4, -70), fontsize=9.5, color=INK,
                 arrowprops={'arrowstyle': '->', 'color': MUTED})
    axl.text(len(tr_loss) * 0.52, (tr_loss[-1] + va_loss[-1]) / 2,
             f'the gap at the end is\n{va_loss[-1] - tr_loss[-1]:.3f}', fontsize=9.5,
             color=GRIP)
    axl.set_xlabel('pass through the training examples', fontsize=10)
    axl.set_ylabel('cross-entropy loss', fontsize=10)
    axl.set_ylim(0, max(va_loss) * 1.3)
    axl.set_title('The first honest curve', fontsize=12, weight='bold')
    axl.legend(fontsize=9.5, frameon=False, loc='upper right')

    _plain(axr)
    axr.plot(range(1, len(tr_err) + 1), np.array(tr_err) * 100, color=LINK, lw=2.0,
             label='training error')
    axr.plot(range(1, len(va_err) + 1), np.array(va_err) * 100, color=GRIP, lw=2.0,
             label='held-back error')
    axr.axhline(nn_err * 100, color=PURPLE, ls='--', lw=1.6)
    axr.text(1.5, nn_err * 100 + 2.2, f'nearest neighbour: {nn_err * 100:.1f}% wrong',
             fontsize=9.5, color=PURPLE)
    axr.axhline(major * 100, color=MUTED, ls=':', lw=1.6)
    axr.text(1.5, major * 100 - 6.0,
             f'always the commonest class: {major * 100:.1f}% wrong', fontsize=9.5,
             color=MUTED)
    axr.set_ylim(0, 100)
    axr.set_xlabel('pass through the training examples', fontsize=10)
    axr.set_ylabel('share of answers that are wrong (%)', fontsize=10)
    axr.set_title('The same run against the two baselines', fontsize=12, weight='bold')
    axr.legend(fontsize=9.5, frameon=False, loc='center right')
    fig.suptitle('One small honest run: the curve says it is training, and the baseline '
                 'lines say whether that is worth anything',
                 fontsize=12.5, weight='bold')
    _save(fig, DOC, 'first-honest-curve.svg')


def fig_three_dataset_sizes() -> None:
    sizes = [60, 240, 960]
    fig, ax = plt.subplots(figsize=(11.2, 5.4), facecolor='white')
    _plain(ax)
    colours = [GRIP, WRIST, LINK]
    runs = {n: honest_run(n) for n in sizes}
    top = max(max(max(r['tr_loss']), max(r['va_loss']))      # type: ignore[arg-type]
              for r in runs.values())
    for n, colour in zip(sizes, colours):
        r = runs[n]
        tr: list[float] = r['tr_loss']         # type: ignore[assignment]
        va: list[float] = r['va_loss']         # type: ignore[assignment]
        ve: list[float] = r['va_err']          # type: ignore[assignment]
        ax.plot(range(1, len(tr) + 1), tr, color=colour, lw=1.5, ls='--')
        ax.plot(range(1, len(va) + 1), va, color=colour, lw=2.2,
                label=f'{n} training examples')
        gap = va[-1] - tr[-1]
        print(f'[4.2] {n:4d} examples: training {tr[-1]:.3f}, held back {va[-1]:.3f}, '
              f'gap {gap:.3f}, held-back error {ve[-1] * 100:.1f}%, '
              f'nearest neighbour {nearest_neighbour_error(n) * 100:.1f}%')
        ax.annotate(f'gap {gap:.2f}', (len(va), va[-1]), textcoords='offset points',
                    xytext=(8, -4), fontsize=9.5, color=colour, weight='bold')
    ax.set_xlim(1, RUNG3_PASSES + 5)
    ax.set_ylim(0, top * 1.06)
    ax.set_xlabel('pass through the training examples', fontsize=10)
    ax.set_ylabel('cross-entropy loss', fontsize=10)
    ax.set_title('Dashed is training, solid is held back: the gap between them measures '
                 'how short of examples you are', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, DOC, 'three-dataset-sizes.svg')


def fig_leaky_split() -> None:
    honest = honest_run(240)
    leaky = honest_run(240, leak=300)
    h_tr: list[float] = honest['tr_loss']      # type: ignore[assignment]
    h_va: list[float] = honest['va_loss']      # type: ignore[assignment]
    l_va: list[float] = leaky['va_loss']       # type: ignore[assignment]
    h_ve: list[float] = honest['va_err']       # type: ignore[assignment]
    l_ve: list[float] = leaky['va_err']        # type: ignore[assignment]
    print(f'[4.3] honest held-back loss {h_va[-1]:.3f} (error {h_ve[-1] * 100:.1f}%), '
          f'leaky held-back loss {l_va[-1]:.3f} (error {l_ve[-1] * 100:.1f}%)')
    print(f'[4.3] 300 of the {N_HELD_BACK} held-back examples were copies of training '
          f'examples, and the lie is {h_va[-1] - l_va[-1]:.3f} of loss and '
          f'{(h_ve[-1] - l_ve[-1]) * 100:.1f} points of error')

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.5, 1.0]})
    _plain(axl)
    axl.plot(range(1, len(h_tr) + 1), h_tr, color=MUTED, lw=1.5, ls='--',
             label='training loss, the same in both runs')
    axl.plot(range(1, len(h_va) + 1), h_va, color=LINK, lw=2.2,
             label='held-back loss, a clean split')
    axl.plot(range(1, len(l_va) + 1), l_va, color=GRIP, lw=2.2,
             label='held-back loss, half the rows copied from training')
    axl.set_xlabel('pass through the training examples', fontsize=10)
    axl.set_ylabel('cross-entropy loss', fontsize=10)
    axl.set_ylim(0, max(max(h_tr), max(h_va), max(l_va)) * 1.06)
    axl.set_title('A leak makes the run look better than it is',
                  fontsize=12, weight='bold')
    axl.legend(fontsize=9.5, frameon=False, loc='upper right')

    _plain(axr)
    vals = [h_va[-1], l_va[-1]]
    bars = axr.bar(['clean split', 'leaky split'], vals, color=[LINK, GRIP], width=0.55)
    for b, v, e in zip(bars, vals, [h_ve[-1], l_ve[-1]]):
        axr.text(b.get_x() + b.get_width() / 2, v + 0.02,
                 f'{v:.3f}\n{e * 100:.1f}% wrong', ha='center', fontsize=10.5,
                 weight='bold', color=INK)
    axr.set_ylim(0, max(vals) * 1.45)
    axr.set_ylabel('held-back loss after the last pass', fontsize=10)
    axr.set_title('The size of the lie', fontsize=12, weight='bold')
    _save(fig, DOC, 'leaky-split.svg')


def fig_first_curve_shapes() -> None:
    shapes = [
        ('still falling: let it run longer', {'lr': 0.0004}),
        ('flat from the first pass: nothing is learning', {'lr': 1e-7}),
        ('the held-back loss climbing: too few examples',
         {'n_train': 60, 'width': 256}),
        ('jumping about: the learning rate is too large', {'lr': 0.5}),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.6), facecolor='white')
    for ax, (title, kw) in zip(axes.ravel(), shapes):
        r = honest_run(**kw)             # type: ignore[arg-type]
        tr: list[float] = r['tr_loss']   # type: ignore[assignment]
        va: list[float] = r['va_loss']   # type: ignore[assignment]
        _plain(ax)
        ax.plot(range(1, len(tr) + 1), tr, color=LINK, lw=2.0, label='training')
        ax.plot(range(1, len(va) + 1), va, color=GRIP, lw=2.0, label='held back')
        ax.set_title(title, fontsize=11, weight='bold')
        ax.set_xlabel('pass', fontsize=9.5)
        ax.set_ylabel('loss', fontsize=9.5)
        ax.legend(fontsize=9, frameon=False)
        ax.set_ylim(0, max(max(tr), max(va)) * 1.22)
        print(f'[4.4] {title:54s} training {tr[-1]:.3f}, held back {va[-1]:.3f}, '
              f'highest training {max(tr):.3f}, highest held back {max(va):.3f}')
    fig.suptitle('Four first curves from four real runs on the same job, and what each '
                 'shape is telling you', fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, DOC, 'first-curve-shapes.svg')


# --------------------------------------------------------------------------
# section 5: scaling one change at a time
# --------------------------------------------------------------------------

BASE: dict[str, object] = {'n_train': 240, 'width': 64, 'lr': 0.002,
                           'passes': RUNG3_PASSES, 'wd': 0.05, 'batch': RUNG3_BATCH,
                           'seed': 0}

CHANGES: list[tuple[str, dict[str, object]]] = [
    ('four times the examples', {'n_train': 960}),
    ('four times as wide', {'width': 256}),
    ('three times as many passes', {'passes': 75}),
    ('four times the batch', {'batch': 128}),
]


def final_val(**over: object) -> float:
    kw = dict(BASE)
    kw.update(over)
    r = honest_run(**kw)                               # type: ignore[arg-type]
    return float(r['va_loss'][-1])                     # type: ignore[index]


_SPREAD: tuple[float, float, float, list[float]] | None = None


def seed_spread() -> tuple[float, float, float, list[float]]:
    global _SPREAD
    if _SPREAD is None:
        vals = [final_val(seed=s) for s in range(6)]
        _SPREAD = (float(np.mean(vals)), float(np.std(vals)),
                   float(max(vals) - min(vals)), vals)
    return _SPREAD


def fig_one_at_a_time() -> None:
    base = final_val()
    _m, sd, _rng, _v = seed_spread()
    rows: list[tuple[str, float, float]] = []
    for label, over in CHANGES:
        v = final_val(**over)
        rows.append((label, v, v - base))
        print(f'[5.1] {label:30s} held-back loss {v:.3f}, change {v - base:+.3f}, '
              f'which is {abs(v - base) / sd:.1f} times the seed spread')
    print(f'[5.1] the run they are all compared with ends at {base:.3f}, '
          f'and the spread over six seeds is {sd:.3f}')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    names = ['the run you\nstarted from'] + [
        r[0].replace('four times as wide', 'four times\nas wide')
            .replace('four times the ', 'four times\nthe ')
            .replace('three times as many ', 'three times\nas many ') for r in rows]
    vals = [base] + [r[1] for r in rows]
    colours = [MUTED] + [SLIDE if r[2] < 0 else GRIP for r in rows]
    bars = ax.bar(names, vals, color=colours, width=0.58)
    ax.axhline(base, color=MUTED, ls='--', lw=1.4)
    ax.axhspan(base - sd, base + sd, color=GRID, alpha=0.55, zorder=0)
    ax.text(-0.42, max(vals) * 1.22,
            f'the grey band is one seed spread either side of the starting run '
            f'(plus or minus {sd:.3f})', fontsize=9.5, color=MUTED)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f'{v:.3f}', ha='center',
                fontsize=10.5, weight='bold', color=INK)
    for b, r in zip(bars[1:], rows):
        ax.text(b.get_x() + b.get_width() / 2, 0.04, f'{r[2]:+.3f}', ha='center',
                fontsize=10.5, weight='bold', color='white')
    ax.set_ylim(0, max(vals) * 1.34)
    ax.set_ylabel('held-back loss at the end of the run', fontsize=10)
    ax.set_title('Four runs, each changing exactly one thing from the same starting '
                 'run, so every number means something', fontsize=12, weight='bold')
    _save(fig, DOC, 'one-at-a-time.svg')


def fig_two_at_once() -> None:
    base = final_val()
    a = final_val(n_train=960)
    b = final_val(width=8)
    both = final_val(n_train=960, width=8)
    _m, sd, _r, _v = seed_spread()
    print(f'[5.2] starting run {base:.3f}; four times the examples {a:.3f} '
          f'({a - base:+.3f}); the hidden layer cut from 64 to 8 {b:.3f} '
          f'({b - base:+.3f}); both at once {both:.3f} ({both - base:+.3f})')
    print(f'[5.2] both at once is {abs(both - base) / sd:.1f} seed spreads from the '
          f'start, and the two changes on their own are {abs(a - base) / sd:.1f} and '
          f'{abs(b - base) / sd:.1f}')

    r0 = honest_run(**BASE)                                 # type: ignore[arg-type]
    ra = honest_run(**{**BASE, 'n_train': 960})             # type: ignore[arg-type]
    rb = honest_run(**{**BASE, 'width': 8})                 # type: ignore[arg-type]
    rc = honest_run(**{**BASE, 'n_train': 960, 'width': 8})  # type: ignore[arg-type]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    _plain(axl)
    labels = ['the run you\nstarted from', 'four times\nthe examples',
              'hidden layer\n64 down to 8', 'both changes\nat once']
    vals = [base, a, b, both]
    bars = axl.bar(labels, vals, color=[MUTED, SLIDE, GRIP, PURPLE], width=0.58)
    for bar, v in zip(bars, vals):
        axl.text(bar.get_x() + bar.get_width() / 2, v + 0.025, f'{v:.3f}', ha='center',
                 fontsize=10.5, weight='bold', color=INK)
    axl.axhline(base, color=MUTED, ls='--', lw=1.4)
    axl.axhspan(base - sd, base + sd, color=GRID, alpha=0.55, zorder=0)
    axl.set_ylim(0, max(vals) * 1.22)
    axl.tick_params(axis='x', labelsize=9.5)
    axl.set_ylabel('held-back loss at the end of the run', fontsize=10)
    axl.set_title('One change helps, one hurts, and together they hide each other',
                  fontsize=11.5, weight='bold')

    _plain(axr)
    for r, colour, label in ((r0, MUTED, 'the run you started from'),
                             (ra, SLIDE, 'four times the examples'),
                             (rb, GRIP, 'the hidden layer cut to 8 units'),
                             (rc, PURPLE, 'both changes at once')):
        axr.plot(range(1, RUNG3_PASSES + 1), r['va_loss'],   # type: ignore[index]
                 color=colour, lw=2.0, label=label)
    axr.set_xlabel('pass through the training examples', fontsize=10)
    axr.set_ylabel('held-back loss', fontsize=10)
    axr.set_ylim(0, max(max(r['va_loss']) for r in (r0, ra, rb, rc)) * 1.1)  # type: ignore[index]
    axr.set_title('The held-back curves of the same four runs',
                  fontsize=11.5, weight='bold')
    axr.legend(fontsize=9.5, frameon=False, loc='upper right')
    fig.suptitle('Change two things at once and the answer is unreadable: both-at-once '
                 f'lands {abs(both - base):.3f} from the start, which looks like '
                 'nothing happened', fontsize=12.5, weight='bold')
    _save(fig, DOC, 'two-at-once.svg')


def fig_seed_spread() -> None:
    mean, sd, rng_, vals = seed_spread()
    base = vals[0]
    deltas = [(label, final_val(**over) - base) for label, over in CHANGES]
    print('[5.3] six seeds of the same settings: ' + '  '.join(f'{v:.3f}' for v in vals))
    print(f'[5.3] average {mean:.3f}, spread {sd:.3f}, '
          f'highest minus lowest {rng_:.3f}, and twice the spread is {2 * sd:.3f}')
    for label, d in deltas:
        print(f'[5.3] {label:30s} {d:+.3f}, '
              f'{"outside" if abs(d) > 2 * sd else "inside"} twice the spread')

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(14.0, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [0.95, 1.3],
                                                'wspace': 0.55})
    _plain(axl)
    axl.scatter(range(6), vals, s=90, color=LINK, zorder=3)
    axl.axhline(mean, color=INK, ls='--', lw=1.4)
    axl.axhspan(mean - sd, mean + sd, color=LINK_PALE, alpha=0.75, zorder=0)
    for i, v in enumerate(vals):
        axl.text(i, v + 0.006, f'{v:.3f}', ha='center', fontsize=9.5, color=INK)
    axl.set_xticks(range(6))
    axl.set_xlim(-0.6, 5.6)
    axl.set_xlabel('seed, with every other setting the same', fontsize=10)
    axl.set_ylabel('held-back loss at the end', fontsize=10)
    axl.set_ylim(min(vals) - 0.04, max(vals) + 0.04)
    axl.set_title(f'Six runs of one recipe: spread {sd:.3f}',
                  fontsize=11.5, weight='bold')

    _plain(axr)
    names = [d[0].replace('three times as many ', 'three times\nas many ')
             .replace('four times as wide', 'four times\nas wide')
             .replace('four times the ', 'four times\nthe ') for d in deltas][::-1]
    ds = [d[1] for d in deltas][::-1]
    colours = [(SLIDE if d < 0 else GRIP) if abs(d) > 2 * sd else MUTED for d in ds]
    bars = axr.barh(names, ds, color=colours, height=0.55)
    axr.axvspan(-2 * sd, 2 * sd, color=GRID, alpha=0.75, zorder=0)
    axr.axvline(0, color=INK, lw=1.2)
    axr.set_ylim(-1.15, 3.6)
    axr.text(0.0, -0.95, f'inside the grey band, which is twice the spread '
                         f'(plus or minus {2 * sd:.3f}),\na change is smaller than '
                         'the luck of the seed',
             fontsize=9.5, color=MUTED, ha='center')
    for bar, d in zip(bars, ds):
        axr.text(d + (0.006 if d > 0 else -0.006), bar.get_y() + bar.get_height() / 2,
                 f'{d:+.3f}', va='center', ha='left' if d > 0 else 'right',
                 fontsize=10, weight='bold', color=INK)
    axr.tick_params(labelsize=10)
    axr.set_xlim(min(ds) - 0.09, max(ds) + 0.07)
    axr.set_xlabel('change in held-back loss against the run it came from', fontsize=10)
    axr.set_title('Which of the four changes is larger than the noise',
                  fontsize=11.5, weight='bold')
    _save(fig, DOC, 'seed-spread.svg')


def fig_runs_needed() -> None:
    ks = np.arange(1, 9)
    one_at_a_time = ks + 1
    every_mix = 2 ** ks
    views = int(RUNG3_PASSES * int(BASE['n_train']))   # type: ignore[arg-type]
    print(f'[5.4] telling 8 changes apart: {one_at_a_time[-1]} runs one at a time '
          f'against {every_mix[-1]} runs for every mixture')
    print(f'[5.4] one run of the starting recipe is {views:,} example-views, so those '
          f'are {views * int(one_at_a_time[-1]):,} and '
          f'{views * int(every_mix[-1]):,} example-views')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(ks, one_at_a_time, marker='o', color=SLIDE, lw=2.2,
            label='one change at a time: changes + 1 runs')
    ax.plot(ks, every_mix, marker='s', color=GRIP, lw=2.2,
            label='every mixture of the changes: 2 to the power of changes')
    for k, a, b in zip(ks, one_at_a_time, every_mix):
        if k in (4, 8):
            ax.annotate(f'{a} runs', (k, a), textcoords='offset points',
                        xytext=(8, -14), fontsize=10, color=SLIDE, weight='bold')
            ax.annotate(f'{b} runs', (k, b), textcoords='offset points',
                        xytext=(-42, 2), fontsize=10, color=GRIP, weight='bold')
    ax.set_yscale('log')
    ax.set_xlabel('number of things you want to change', fontsize=10)
    ax.set_ylabel('runs needed to know which one did it (log scale)', fontsize=10)
    ax.set_title('One change at a time costs one run per change, and the alternative '
                 'doubles every time you add one', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, DOC, 'runs-needed.svg')


# --------------------------------------------------------------------------
# section 6: the run folder
# --------------------------------------------------------------------------

def build_run_folder() -> tuple[pathlib.Path, dict[str, int], dict[str, object]]:
    """Write a real run folder, then measure the real size of every file in it."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='run-folder-'))
    r = honest_run(**BASE)                                   # type: ignore[arg-type]
    config: dict[str, object] = {
        'run': '2027-01-14-003', 'job': 'ten classes from 16 readings',
        'data': 'simulated-pool-v3', 'train_examples': BASE['n_train'],
        'held_back_examples': N_HELD_BACK,
        'split': 'fixed list of example ids, written before the first run',
        'model': 'mlp', 'width': BASE['width'], 'classes': K, 'inputs': D_IN,
        'optimiser': 'adamw', 'learning_rate': BASE['lr'],
        'weight_decay': BASE['wd'], 'batch': BASE['batch'], 'passes': BASE['passes'],
        'seed': BASE['seed'], 'loss': 'cross_entropy',
        'baseline_to_beat': 'nearest neighbour', 'torch': torch.__version__,
        'numpy': np.__version__, 'commit': '0' * 40,
    }
    (tmp / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    lines = ['pass,train_loss,held_back_loss,train_error,held_back_error']
    for i in range(int(BASE['passes'])):                     # type: ignore[arg-type]
        lines.append(
            f'{i + 1},{r["tr_loss"][i]:.6f},{r["va_loss"][i]:.6f},'  # type: ignore[index]
            f'{r["tr_err"][i]:.6f},{r["va_err"][i]:.6f}')            # type: ignore[index]
    (tmp / 'metrics.csv').write_text('\n'.join(lines) + '\n')
    n_ids = int(BASE['n_train']) + N_HELD_BACK               # type: ignore[arg-type]
    (tmp / 'split-ids.txt').write_text('\n'.join(f'example-{i:05d}'
                                                 for i in range(n_ids)) + '\n')
    (tmp / 'stdout.log').write_text(''.join(
        f'pass {i + 1:3d}  train {r["tr_loss"][i]:.4f}  '    # type: ignore[index]
        f'held back {r["va_loss"][i]:.4f}\n'                 # type: ignore[index]
        for i in range(int(BASE['passes']))))                # type: ignore[arg-type]
    net = mlp(int(BASE['width']), 0)                         # type: ignore[arg-type]
    opt = torch.optim.AdamW(net.parameters(), lr=0.002)
    F.cross_entropy(net(TRAIN_X[:8]), TRAIN_Y[:8]).backward()
    opt.step()
    torch.save(net.state_dict(), tmp / 'weights.pt')
    torch.save({'model': net.state_dict(), 'opt': opt.state_dict()},
               tmp / 'checkpoint.pt')
    sizes = {p.name: p.stat().st_size for p in sorted(tmp.iterdir())}
    return tmp, sizes, config


FOLDER_ORDER: list[str] = ['config.json', 'metrics.csv', 'split-ids.txt', 'stdout.log',
                           'weights.pt', 'checkpoint.pt']
FOLDER_NOTES: dict[str, str] = {
    'config.json': 'every setting, so the run can be run again',
    'metrics.csv': 'one row a pass: both losses and both error rates',
    'split-ids.txt': 'which example went into which half of the split',
    'stdout.log': 'everything the run printed, kept as it printed it',
    'weights.pt': 'the weights on their own, for using the model',
    'checkpoint.pt': 'weights and optimiser state, for carrying the run on',
}


def fig_run_folder() -> None:
    tmp, sizes, config = build_run_folder()
    total = sum(sizes[n] for n in FOLDER_ORDER)
    written = sizes['config.json'] + sizes['metrics.csv'] + sizes['stdout.log']
    for n in FOLDER_ORDER:
        print(f'[6.1] {n:16s} {sizes[n]:9,d} bytes   {FOLDER_NOTES[n]}')
    print(f'[6.1] the whole folder is {total:,} bytes, config.json holds '
          f'{len(config)} settings, and the three files that describe the run are '
          f'{written:,} bytes')

    fig, ax = plt.subplots(figsize=(12.8, 5.4), facecolor='white')
    _bare(ax)
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 7.4)
    ax.text(0.2, 6.95, f'runs/2027-01-14-003/      {total:,} bytes in all, and '
                       f'{len(config)} settings written down',
            fontsize=12.5, weight='bold', color=INK)
    for i, n in enumerate(FOLDER_ORDER):
        y = 5.9 - i * 0.92
        colour = PURPLE if n.endswith('.pt') else TEAL
        _box(ax, 0.5, y, 3.1, 0.7, colour, alpha=0.16)
        ax.text(0.68, y + 0.26, n, fontsize=11, weight='bold', color=INK,
                family='monospace')
        ax.text(3.85, y + 0.26, f'{sizes[n]:>9,d} bytes', fontsize=10.5, color=colour,
                weight='bold', family='monospace')
        ax.text(6.1, y + 0.26, FOLDER_NOTES[n], fontsize=10, color=INK)
    ax.plot([0.3, 0.3], [0.45, 6.6], color=GRID, lw=1.4)
    ax.text(0.2, 0.08, f'the three files that describe the run come to {written:,} '
                       f'bytes, which is {written / total * 100:.1f} per cent of the '
                       'folder', fontsize=10, color=MUTED, style='italic')
    _save(fig, DOC, 'run-folder.svg')
    shutil.rmtree(tmp, ignore_errors=True)


def fig_reproduce_or_not() -> None:
    a = honest_run(**BASE)                                  # type: ignore[arg-type]
    b = honest_run(**BASE)                                  # type: ignore[arg-type]
    c = honest_run(**{**BASE, 'seed': 3})                   # type: ignore[arg-type]
    av: list[float] = a['va_loss']                          # type: ignore[assignment]
    bv: list[float] = b['va_loss']                          # type: ignore[assignment]
    cv: list[float] = c['va_loss']                          # type: ignore[assignment]
    same = max(abs(x - y) for x, y in zip(av, bv))
    diff = max(abs(x - y) for x, y in zip(av, cv))
    print(f'[6.2] same settings and same seed: the largest difference between the two '
          f'curves is {same:.2e}')
    print(f'[6.2] same settings, seed 0 against seed 3: the largest difference is '
          f'{diff:.3f}, and the two runs end at {av[-1]:.3f} and {cv[-1]:.3f}')

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white')
    _plain(axl)
    axl.plot(range(1, len(av) + 1), av, color=LINK, lw=3.6, label='the first run')
    axl.plot(range(1, len(bv) + 1), bv, color=JOINT, lw=1.6, ls='--',
             label='the same config.json run again')
    axl.set_title(f'Same settings, same seed: largest gap {same:.1e}',
                  fontsize=11.5, weight='bold')
    axl.set_xlabel('pass', fontsize=10)
    axl.set_ylabel('held-back loss', fontsize=10)
    axl.legend(fontsize=9.5, frameon=False)
    axl.set_ylim(0, 2.4)

    _plain(axr)
    axr.plot(range(1, len(av) + 1), av, color=LINK, lw=2.4, label='seed 0')
    axr.plot(range(1, len(cv) + 1), cv, color=GRIP, lw=2.4, label='seed 3')
    axr.set_title(f'Same settings, a different seed: largest gap {diff:.3f}',
                  fontsize=11.5, weight='bold')
    axr.set_xlabel('pass', fontsize=10)
    axr.set_ylabel('held-back loss', fontsize=10)
    axr.legend(fontsize=9.5, frameon=False)
    axr.set_ylim(0, 2.4)
    fig.suptitle('The run you keep is the one you can run again, which is why the seed '
                 'is a setting and not an accident', fontsize=12.5, weight='bold')
    _save(fig, DOC, 'reproduce-or-not.svg')


def fig_which_settings_matter() -> None:
    base = final_val()
    _m, sd, _r, _v = seed_spread()
    tests = [('learning rate, 0.002 to 0.0004', {'lr': 0.0004}),
             ('width, 64 to 8', {'width': 8}),
             ('passes, 25 to 75', {'passes': 75}),
             ('batch, 32 to 128', {'batch': 128}),
             ('training examples, 240 to 960', {'n_train': 960}),
             ('weight decay, 0.05 to 0.5', {'wd': 0.5}),
             ('seed, 0 to 3', {'seed': 3})]
    rows: list[tuple[str, float]] = []
    for label, over in tests:
        v = final_val(**over)
        rows.append((label, v - base))
        print(f'[6.3] {label:32s} held-back loss {v:.3f}, change {v - base:+.3f}')
    print(f'[6.3] the run they are all compared with ends at {base:.3f}, and twice the '
          f'seed spread is {2 * sd:.3f}')

    rows.sort(key=lambda r: abs(r[1]))
    fig, ax = plt.subplots(figsize=(11.8, 5.4), facecolor='white')
    _plain(ax)
    names = [r[0] for r in rows]
    deltas = [r[1] for r in rows]
    colours = [(GRIP if d > 0 else SLIDE) if abs(d) > 2 * sd else MUTED
               for d in deltas]
    bars = ax.barh(names, deltas, color=colours, height=0.6)
    ax.axvspan(-2 * sd, 2 * sd, color=GRID, alpha=0.75, zorder=0)
    ax.axvline(0, color=INK, lw=1.2)
    for bar, d in zip(bars, deltas):
        ax.text(d + (0.012 if d > 0 else -0.012), bar.get_y() + bar.get_height() / 2,
                f'{d:+.3f}', va='center', ha='left' if d > 0 else 'right',
                fontsize=10, weight='bold', color=INK)
    ax.set_xlim(min(deltas) - 0.12, max(deltas) + 0.12)
    ax.tick_params(labelsize=10)
    ax.set_xlabel('change in the final held-back loss when that one setting is changed',
                  fontsize=10)
    ax.set_title('Every setting in config.json, sorted by how far changing it moves the '
                 'answer; grey is inside the seed noise',
                 fontsize=12, weight='bold')
    _save(fig, DOC, 'which-settings-matter.svg')


def fig_log_cost() -> None:
    tmp, sizes, _c = build_run_folder()
    written = sizes['config.json'] + sizes['metrics.csv'] + sizes['stdout.log']
    big = mlp(2048, 0)
    opt = torch.optim.AdamW(big.parameters(), lr=0.002)
    F.cross_entropy(big(TRAIN_X[:8]), TRAIN_Y[:8]).backward()
    opt.step()
    torch.save({'model': big.state_dict(), 'opt': opt.state_dict()},
               tmp / 'big-checkpoint.pt')
    big_bytes = (tmp / 'big-checkpoint.pt').stat().st_size
    n_weights = sum(int(p.numel()) for p in big.parameters())
    print(f'[6.4] bytes: ' + '  '.join(f'{n}={sizes[n]:,}' for n in FOLDER_ORDER))
    print(f'[6.4] the three files that describe the run are {written:,} bytes; '
          f'the small checkpoint is {sizes["checkpoint.pt"] / written:.1f} times that')
    print(f'[6.4] a width-2048 model has {n_weights:,} weights and its checkpoint is '
          f'{big_bytes:,} bytes, which is {big_bytes / written:,.0f} times the three '
          f'files')

    names = ['config.json', 'metrics.csv', 'stdout.log', 'split-ids.txt',
             'checkpoint.pt', 'the same for a\nwidth-2048 model']
    vals = [sizes['config.json'], sizes['metrics.csv'], sizes['stdout.log'],
            sizes['split-ids.txt'], sizes['checkpoint.pt'], big_bytes]
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    bars = ax.bar(names, vals, color=[TEAL, TEAL, TEAL, TEAL, PURPLE, PURPLE],
                  width=0.6)
    ax.set_yscale('log')
    ax.set_ylim(100, max(vals) * 10)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.35, f'{v:,}', ha='center',
                fontsize=10, weight='bold', color=INK)
    ax.tick_params(axis='x', labelsize=9.5)
    ax.set_ylabel('bytes (log scale)', fontsize=10)
    ax.set_title('What writing the run down costs: the three files that describe it are '
                 f'{written:,} bytes, and one checkpoint is '
                 f'{big_bytes / written:,.0f} times that', fontsize=12, weight='bold')
    _save(fig, DOC, 'log-cost.svg')
    shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    fig_ladder()
    fig_cost_of_finding_late()
    fig_causes_ruled_out()
    fig_first_loss_by_classes()
    fig_shape_chain()
    fig_planted_first_losses()
    fig_first_loss_regression()
    fig_ten_at_random()
    fig_overfit_ten()
    fig_overfit_accuracy()
    fig_plateau_fingerprints()
    fig_bug_catalogue()
    fig_rung_two_predicts_rung_three()
    fig_first_honest_curve()
    fig_three_dataset_sizes()
    fig_leaky_split()
    fig_first_curve_shapes()
    fig_one_at_a_time()
    fig_two_at_once()
    fig_seed_spread()
    fig_runs_needed()
    fig_run_folder()
    fig_reproduce_or_not()
    fig_which_settings_matter()
    fig_log_cost()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
