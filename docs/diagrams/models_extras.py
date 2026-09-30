"""Generate the diagrams for three additions to Book 6 (neural network models).

Each document's pictures go to a folder named after it, under docs/images/:

    01_what-models-are/07_fine-tuning.md
        -> what-models-are/fine-tuning/
    01_what-models-are/03_inside-a-neural-network.md, section "Layers that remember"
        -> what-models-are/inside-a-neural-network/
    02_seeing-models/02_most-used/04_keypoints-and-object-pose.md, section on 6D pose tracking
        -> seeing-models/keypoints-and-object-pose/

Run with:  pixi run python ../docs/diagrams/models_extras.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file and printed, so the
documents can quote the same values: the parameter counts of LoRA against a full
layer, a small fine-tuning run in numpy with its errors and its forgetting, the
memory of a tiny recurrent network, a sliding filter along time, a fixed and a
selective running memory, the 252 starting guesses of FoundationPose's first frame,
and a simulated pose track with and without re-detection.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
GRIP_PALE: str = '#f7d0d0'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
FROZEN: str = '#e6e6e6'
PURPLE: str = '#8e5ec9'
MONO: str = 'DejaVu Sans Mono'

FT_DOC: str = 'what-models-are/fine-tuning'
NN_DOC: str = 'what-models-are/inside-a-neural-network'
POSE_DOC: str = 'seeing-models/keypoints-and-object-pose'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', family: str | None = None,
           va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            family=family, zorder=7)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=14, color=color,
                                 lw=lw, connectionstyle=f'arc3,rad={rad}', zorder=6))


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = LINK_PALE,
         edge: str = LINK, lw: float = 1.4) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=3))


def _plot_style(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9.5)
    ax.grid(True, color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        flat = folder.replace('/', '__')
        fig.savefig(PNG_DIR / f'{flat}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 07_fine-tuning.md
# --------------------------------------------------------------------------

def _relu(z: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.maximum(z, 0.0)


class FineTuneRun:
    """A small, real fine-tuning experiment in numpy.

    A "pretrained" network has a backbone (16 inputs -> 32 neurons) and a head that
    gives 4 outputs for the old job. We pretend pretraining already worked by using
    the very weights that make the old job's answers. The new job is made by a
    slightly changed backbone (a rank-1 change) and a new 1-output head. We have only
    50 examples of the new job. We then train four ways: head only, LoRA (rank 1) on
    the backbone plus the head, full fine-tuning, and from scratch.
    """

    D, H, KA = 16, 32, 4
    N_NEW = 50
    STEPS = 3000
    LR = 0.01

    def __init__(self) -> None:
        rng = np.random.default_rng(0)
        d, h = self.D, self.H
        self.w1 = rng.normal(0, 1 / np.sqrt(d), (h, d))
        self.b1 = rng.normal(0, 0.1, h)
        self.head_old = rng.normal(0, 1 / np.sqrt(h), (self.KA, h))
        u = rng.normal(0, 1, (h, 1))
        v = rng.normal(0, 1, (1, d))
        self.w1_new = self.w1 + 0.35 * (u @ v) / np.sqrt(d)
        self.head_new_true = rng.normal(0, 1 / np.sqrt(h), (1, h))
        self.x_old = rng.normal(size=(2000, d))
        self.y_old = self._old(self.w1, self.b1, self.x_old)
        self.x_new = rng.normal(size=(self.N_NEW, d))
        self.y_new = self._new_true(self.x_new) + rng.normal(0, 0.02, (self.N_NEW, 1))
        self.x_test = rng.normal(size=(2000, d))
        self.y_test = self._new_true(self.x_test)
        self.guess_mean_error = float(np.var(self.y_test))

    def _old(self, w: NDArray[np.float64], b: NDArray[np.float64],
             x: NDArray[np.float64]) -> NDArray[np.float64]:
        return _relu(x @ w.T + b) @ self.head_old.T

    def _new_true(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        return _relu(x @ self.w1_new.T + self.b1) @ self.head_new_true.T

    @staticmethod
    def _mse(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
        return float(np.mean((a - b) ** 2))

    def train(self, mode: str, rank: int = 1) -> dict[str, object]:
        g = np.random.default_rng(1)
        d, h = self.D, self.H
        w, b = self.w1.copy(), self.b1.copy()
        head = np.zeros((1, h))
        if mode == 'scratch':
            w = g.normal(0, 1 / np.sqrt(d), (h, d))
            b = np.zeros(h)
            head = g.normal(0, 1 / np.sqrt(h), (1, h))
        la = g.normal(0, 0.01, (rank, d))       # LoRA's two thin matrices
        lb = np.zeros((h, rank))
        m1: dict[str, NDArray[np.float64]] = {}
        m2: dict[str, NDArray[np.float64]] = {}

        def adam(name: str, p: NDArray[np.float64], gr: NDArray[np.float64],
                 t: int) -> NDArray[np.float64]:
            m1[name] = 0.9 * m1.get(name, 0 * gr) + 0.1 * gr
            m2[name] = 0.999 * m2.get(name, 0 * gr) + 0.001 * gr ** 2
            mh = m1[name] / (1 - 0.9 ** t)
            vh = m2[name] / (1 - 0.999 ** t)
            return p - self.LR * mh / (np.sqrt(vh) + 1e-8)

        def eff(w_: NDArray[np.float64]) -> NDArray[np.float64]:
            return w_ + lb @ la if mode == 'lora' else w_

        hist: list[tuple[int, float, float]] = []
        for t in range(1, self.STEPS + 1):
            we = eff(w)
            z = self.x_new @ we.T + b
            hid = _relu(z)
            e = (hid @ head.T - self.y_new) * 2 / self.N_NEW
            g_head = e.T @ hid
            g_z = (e @ head) * (z > 0)
            g_w = g_z.T @ self.x_new
            g_b = g_z.sum(0)
            head = adam('head', head, g_head, t)
            if mode in ('full', 'scratch'):
                w = adam('w', w, g_w, t)
                b = adam('b', b, g_b, t)
            if mode == 'lora':
                g_lb = g_w @ la.T
                g_la = lb.T @ g_w
                lb = adam('lb', lb, g_lb, t)
                la = adam('la', la, g_la, t)
            if t == 1 or t % 50 == 0:
                we = eff(w)
                hist.append((t, self._mse(_relu(self.x_test @ we.T + b) @ head.T, self.y_test),
                             self._mse(self._old(we, b, self.x_old), self.y_old)))
        we = eff(w)
        trained = {'head': h, 'lora': h + rank * (d + h), 'full': h * d + h + h,
                   'scratch': h * d + h + h}[mode]
        return {
            'new_test': self._mse(_relu(self.x_test @ we.T + b) @ head.T, self.y_test),
            'new_train': self._mse(_relu(self.x_new @ we.T + b) @ head.T, self.y_new),
            'old_on': self._mse(self._old(we, b, self.x_old), self.y_old),
            'old_off': self._mse(self._old(w, b, self.x_old), self.y_old),
            'trained': trained,
            'hist': hist,
        }


_FT_CACHE: dict[str, dict[str, object]] = {}


def fine_tune_results() -> dict[str, dict[str, object]]:
    if not _FT_CACHE:
        run = FineTuneRun()
        for mode in ('head', 'lora', 'full', 'scratch'):
            _FT_CACHE[mode] = run.train(mode)
        _FT_CACHE['_meta'] = {'guess_mean_error': run.guess_mean_error,
                              'backbone': run.H * run.D + run.H, 'head': run.H}
        print('fine-tuning run (mean squared error; guessing the average gives '
              f'{run.guess_mean_error:.3f}):')
        for mode in ('head', 'lora', 'full', 'scratch'):
            r = _FT_CACHE[mode]
            print(f'  {mode:8s} trained={r["trained"]:4d}  new job test={r["new_test"]:.3f} '
                  f'(train {r["new_train"]:.4f})  old job with change on={r["old_on"]:.3f} '
                  f'old job with change off={r["old_off"]:.3f}')
    return _FT_CACHE


def _net(ax: Axes, x0: float, y0: float, trained: str, title: str, note: str) -> None:
    """A small picture of a network: input, three backbone layers, a head.

    trained is one of 'head', 'lora', 'full'.
    """
    layer_x = [x0 + 0.6, x0 + 1.9, x0 + 3.2, x0 + 4.5]
    sizes = [4, 5, 5, 2]
    ys: list[list[float]] = []
    for n in sizes:
        ys.append([y0 + 1.9 + (i - (n - 1) / 2) * 0.62 for i in range(n)])
    # backbone box and head box
    back_face = FROZEN if trained in ('head', 'lora') else GRIP_PALE
    back_edge = MUTED if trained in ('head', 'lora') else GRIP
    ax.add_patch(Rectangle((x0 + 0.25, y0 + 0.1), 3.3, 3.6, facecolor=back_face,
                           edgecolor=back_edge, lw=1.2, zorder=1))
    ax.add_patch(Rectangle((x0 + 3.95, y0 + 0.1), 1.1, 3.6, facecolor=GRIP_PALE,
                           edgecolor=GRIP, lw=1.2, zorder=1))
    for li in range(3):
        is_head = li == 2
        for ya in ys[li]:
            for yb in ys[li + 1]:
                if is_head or trained == 'full':
                    col, lw = GRIP, 0.9
                else:
                    col, lw = '#a8a8a8', 0.7
                ax.plot([layer_x[li], layer_x[li + 1]], [ya, yb], color=col, lw=lw, zorder=2)
    for lx, col_ys in zip(layer_x, ys):
        for yy in col_ys:
            ax.add_patch(plt.Circle((lx, yy), 0.16, facecolor='white', edgecolor=INK,
                                    lw=1.0, zorder=4))
    if trained == 'lora':
        # a thin side path around the middle layer: two small matrices
        xa, xb = layer_x[1], layer_x[2]
        mid = (xa + xb) / 2
        ax.add_patch(Rectangle((mid - 0.32, y0 + 3.9), 0.64, 0.42, facecolor=GRIP_PALE,
                               edgecolor=GRIP, lw=1.3, zorder=5))
        _label(ax, mid, y0 + 4.11, 'A,B', size=9, color=GRIP, weight='bold')
        ax.plot([xa, mid - 0.32], [ys[1][-1] + 0.2, y0 + 4.11], color=GRIP, lw=1.3, zorder=5)
        ax.plot([mid + 0.32, xb], [y0 + 4.11, ys[2][-1] + 0.2], color=GRIP, lw=1.3, zorder=5)
    _label(ax, x0 + 1.9, y0 - 0.2, 'backbone', size=9.5, color=MUTED)
    _label(ax, x0 + 4.5, y0 - 0.2, 'head', size=9.5, color=MUTED)
    _title(ax, x0 + 2.65, y0 + 5.0, title, size=12)
    _label(ax, x0 + 2.65, y0 - 0.95, note, size=9.8, color=INK)


def three_ways() -> None:
    """The same network three times: which parts change in each way of fine-tuning."""
    res = fine_tune_results()
    meta = res['_meta']
    fig, ax = plt.subplots(figsize=(14.5, 5.4), facecolor='white')
    _axes(ax, (-0.2, 18.4), (-2.3, 5.6))
    notes = {
        'head': f'trains {res["head"]["trained"]} numbers',
        'lora': f'trains {res["lora"]["trained"]} numbers',
        'full': f'trains {res["full"]["trained"]} numbers',
    }
    _net(ax, 0.0, 0.0, 'head', '1. Freeze the backbone,\nnew head', notes['head'])
    _net(ax, 6.2, 0.0, 'lora', '2. LoRA: small side path\n+ new head', notes['lora'])
    _net(ax, 12.4, 0.0, 'full', '3. Full fine-tuning', notes['full'])
    _label(ax, 9.2, -1.85, f'Grey = frozen (kept as it was).  Red = trained on your data.  '
           f'The example network has a backbone of {meta["backbone"]} numbers '
           f'and a head of {meta["head"]}.', size=10, color=MUTED)
    _save(fig, FT_DOC, 'three-ways-to-fine-tune.svg')


def lora_counts() -> None:
    """One 4096 x 4096 weight grid, against LoRA's two thin grids, with real counts."""
    n = 4096
    full = n * n
    ranks = [4, 8, 16, 32, 64]
    counts = [r * (n + n) for r in ranks]
    print(f'LoRA counts for a {n} x {n} layer: full = {full:,}')
    for r, c in zip(ranks, counts):
        print(f'  rank {r:3d}: {c:,} = {100 * c / full:.2f} % of the full layer')

    fig = plt.figure(figsize=(13.5, 5.6), facecolor='white')
    ax = fig.add_axes((0.0, 0.0, 0.56, 1.0))
    _axes(ax, (-0.5, 12.5), (-1.6, 6.4))
    # the full grid
    ax.add_patch(Rectangle((0.0, 0.0), 5.0, 5.0, facecolor=LINK_PALE, edgecolor=LINK, lw=1.5))
    _label(ax, 2.5, 2.9, 'W', size=20, weight='bold', color=LINK)
    _label(ax, 2.5, 2.0, f'{n} x {n}', size=11, family=MONO)
    _label(ax, 2.5, 1.35, f'= {full:,} numbers', size=10.5)
    _label(ax, 2.5, 5.6, 'the frozen layer', size=11, weight='bold')
    _label(ax, 6.0, 2.5, '+', size=22)
    # B (tall thin) x A (short wide), drawn for rank 32 with exaggerated thickness
    ax.add_patch(Rectangle((7.0, 0.0), 0.45, 5.0, facecolor=GRIP_PALE, edgecolor=GRIP, lw=1.5))
    _label(ax, 7.22, 2.5, 'B', size=13, weight='bold', color=GRIP)
    _label(ax, 7.22, -0.5, f'{n} x 32', size=9.5, family=MONO)
    _label(ax, 8.0, 2.5, 'x', size=16)
    ax.add_patch(Rectangle((8.5, 2.28), 3.6, 0.45, facecolor=GRIP_PALE, edgecolor=GRIP, lw=1.5))
    _label(ax, 10.3, 2.5, 'A', size=13, weight='bold', color=GRIP)
    _label(ax, 10.3, 1.85, f'32 x {n}', size=9.5, family=MONO)
    _label(ax, 9.6, 5.6, 'LoRA, rank 32: the trained part', size=11, weight='bold')
    _label(ax, 9.6, 4.6, f'32 x ({n} + {n})\n= {counts[3]:,} numbers', size=10.5)
    _label(ax, 6.0, -1.3, 'The two thin grids are drawn thicker than true scale so that '
           'you can see them.', size=9.5, color=MUTED)

    bx = fig.add_axes((0.63, 0.16, 0.35, 0.7))
    _plot_style(bx)
    pct = [100 * c / full for c in counts]
    bars = bx.bar([str(r) for r in ranks], pct, color=GRIP, width=0.6)
    for rect, p, c in zip(bars, pct, counts):
        bx.text(rect.get_x() + rect.get_width() / 2, p + 0.08, f'{p:.2f} %\n({c:,})',
                ha='center', va='bottom', fontsize=8.8, color=INK)
    bx.set_ylim(0, 4.2)
    bx.set_xlabel('rank (how thin the two grids are)', fontsize=10, color=INK)
    bx.set_ylabel('trained numbers, as % of the full layer', fontsize=10, color=INK)
    bx.set_title(f'Same {n} x {n} layer, five ranks', fontsize=11.5, color=INK,
                 weight='bold')
    _save(fig, FT_DOC, 'lora-in-numbers.svg')


def forgetting_curves() -> None:
    """The real run: error on the new job and on the old job, step by step, three ways."""
    res = fine_tune_results()
    meta = res['_meta']
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white')
    styles = {'head': (SLIDE, 'freeze backbone, new head'),
              'lora': (WRIST, 'LoRA, rank 1 (side path switched on)'),
              'full': (GRIP, 'full fine-tuning'),
              'scratch': (MUTED, 'from scratch, no pretraining')}
    for mode, (col, name) in styles.items():
        hist = np.array(res[mode]['hist'])
        ls = '--' if mode == 'scratch' else '-'
        a1.plot(hist[:, 0], hist[:, 1], color=col, lw=2.0, ls=ls, label=name)
        if mode != 'scratch':
            a2.plot(hist[:, 0], hist[:, 2], color=col, lw=2.0, label=name)
    for a in (a1, a2):
        _plot_style(a)
        a.set_xlabel('training step', fontsize=10, color=INK)
        a.set_ylabel('error (mean squared)', fontsize=10, color=INK)
    a1.set_ylim(0, 0.6)
    a1.axhline(meta['guess_mean_error'], color=INK, lw=0.8, ls=':')
    a1.text(3000, meta['guess_mean_error'] - 0.012, 'always guessing the average',
            ha='right', va='top', fontsize=9, color=MUTED)
    a1.set_title('New job: 50 examples to learn from', fontsize=11.5, color=INK,
                 weight='bold')
    a2.set_title('Old job: has the model forgotten it?', fontsize=11.5, color=INK,
                 weight='bold')
    a2.set_ylim(-0.005, 0.12)
    a1.legend(fontsize=9, frameon=False, loc='center right', bbox_to_anchor=(1.0, 0.52))
    a2.text(3000, 0.004, 'head only: the backbone never changes, so the error stays 0',
            ha='right', va='bottom', fontsize=9, color=SLIDE)
    fig.tight_layout(w_pad=3.0)
    _save(fig, FT_DOC, 'forgetting-in-a-real-run.svg')


def memory_by_mode() -> None:
    """Published memory figures (openpi README, OpenVLA README) against card sizes."""
    fig, ax = plt.subplots(figsize=(11.5, 4.8), facecolor='white')
    _plot_style(ax)
    rows = [('openpi: run the model', 8.0, SLIDE),
            ('openpi: LoRA fine-tuning', 22.5, WRIST),
            ('OpenVLA: LoRA, small batch', 27.0, WRIST),
            ('openpi: full fine-tuning', 70.0, GRIP),
            ('OpenVLA: LoRA, batch of 16', 72.0, WRIST)]
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    cols = [r[2] for r in rows]
    y = np.arange(len(rows))[::-1]
    ax.barh(y, vals, color=cols, height=0.55)
    for yy, v in zip(y, vals):
        ax.text(v + 1.0, yy, f'more than {v:g} GB' if v != 27.0 and v != 72.0
                else f'about {v:g} GB', va='center', fontsize=9.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    for gb, name in ((24, '24 GB card\n(RTX 4090)'), (80, '80 GB card\n(A100, H100)')):
        ax.axvline(gb, color=INK, lw=1.0, ls=':')
        ax.text(gb + 0.6, len(rows) - 0.35, name, fontsize=9, color=MUTED, va='top')
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xlabel('graphics card memory the project states (GB)', fontsize=10, color=INK)
    ax.set_title('Memory needed, as each project\'s own README states it', fontsize=11.5,
                 color=INK, weight='bold')
    ax.text(100, -1.75, 'OpenVLA full fine-tuning is not a bar: its README asks for a node '
            'of 8 A100 cards.', ha='right', fontsize=9, color=MUTED)
    _save(fig, FT_DOC, 'memory-by-way-of-fine-tuning.svg')


# --------------------------------------------------------------------------
# 03_inside-a-neural-network.md: layers that remember
# --------------------------------------------------------------------------

READ_A = [1.0, 2.0, 3.0]        # squeezing harder
READ_B = [5.0, 4.0, 3.0]        # letting go
KEEP, TAKE = 0.6, 0.4           # the small recurrent rule: memory = 0.6 x memory + 0.4 x reading


def _run_memory(reads: list[float]) -> list[float]:
    mem = [reads[0]]
    for r in reads[1:]:
        mem.append(KEEP * mem[-1] + TAKE * r)
    return mem


def same_reading_two_stories() -> None:
    """Two force histories that end on the same reading."""
    fig, ax = plt.subplots(figsize=(9.5, 4.4), facecolor='white')
    _plot_style(ax)
    t = [0, 1, 2]
    ax.plot(t, READ_A, color=LINK, lw=2.4, marker='o', ms=8, label='A: squeezing harder')
    ax.plot(t, READ_B, color=WRIST, lw=2.4, marker='s', ms=8, label='B: letting go')
    for x, (ya, yb) in enumerate(zip(READ_A, READ_B)):
        if x < 2:
            ax.text(x - 0.07, ya, f'{ya:g} N', ha='right', va='center', fontsize=9.5,
                    color=LINK)
            ax.text(x + 0.07, yb + 0.15, f'{yb:g} N', ha='left', va='bottom', fontsize=9.5,
                    color=WRIST)
    ax.text(2.0, 3.6, '3 N', ha='center', va='bottom', fontsize=9.5, color=GRIP)
    ax.add_patch(Rectangle((1.8, 2.5), 0.4, 1.0, facecolor='none', edgecolor=GRIP, lw=1.6,
                           ls='--'))
    ax.text(2.25, 3.0, 'now: both read 3 N.\nA network that sees only\nthis reading gives\n'
            'the same answer for both.', fontsize=9.5, color=GRIP, va='center')
    ax.set_xticks(t)
    ax.set_xticklabels(['2 readings ago', '1 reading ago', 'now'])
    ax.set_xlim(-0.4, 3.2)
    ax.set_ylim(0, 6)
    ax.set_ylabel('gripper force (newtons)', fontsize=10, color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('Same reading now, two different stories', fontsize=11.5, color=INK,
                 weight='bold')
    _save(fig, NN_DOC, 'same-reading-two-stories.svg')


def recurrent_memory() -> None:
    """The tiny recurrent rule, unrolled over the three readings, for both stories."""
    mem_a = _run_memory(READ_A)
    mem_b = _run_memory(READ_B)
    out_a = READ_A[-1] - mem_a[-1]
    out_b = READ_B[-1] - mem_b[-1]
    print('recurrent memory: rule memory = '
          f'{KEEP} x memory + {TAKE} x reading, starting at the first reading')
    print(f'  A readings {READ_A} -> memory {[round(m, 2) for m in mem_a]}; '
          f'reading now - memory = {out_a:+.2f}')
    print(f'  B readings {READ_B} -> memory {[round(m, 2) for m in mem_b]}; '
          f'reading now - memory = {out_b:+.2f}')

    fig, ax = plt.subplots(figsize=(13.0, 5.6), facecolor='white')
    _axes(ax, (-1.6, 14.2), (-0.6, 6.4))
    for row, (reads, mem, col, name, out) in enumerate(
            [(READ_A, mem_a, LINK, 'A', out_a), (READ_B, mem_b, WRIST, 'B', out_b)]):
        y = 4.3 - row * 3.0
        _label(ax, -1.1, y + 0.2, name, size=15, weight='bold', color=col)
        for k, (r, m) in enumerate(zip(reads, mem)):
            x = 0.6 + k * 3.6
            _label(ax, x, y + 1.25, f'reading {r:g} N', size=10, color=col)
            _arrow(ax, (x, y + 1.0), (x, y + 0.5), color=col, lw=1.3)
            _box(ax, x - 0.85, y - 0.35, 1.7, 0.8, face='white', edge=col)
            _label(ax, x, y + 0.05, f'memory\n{m:.2f}', size=9.5, family=MONO)
            if k > 0:
                _label(ax, x - 1.8, y - 0.75, f'0.6 x {mem[k - 1]:.2f} + 0.4 x {r:g}',
                       size=8.8, family=MONO, color=MUTED)
                _arrow(ax, (x - 2.75, y + 0.05), (x - 0.9, y + 0.05), color=MUTED, lw=1.3)
        xo = 0.6 + 3 * 3.6
        _arrow(ax, (xo - 2.75, y + 0.05), (xo - 1.2, y + 0.05), color=MUTED, lw=1.3)
        verdict = 'rising: squeezing' if out > 0 else 'falling: letting go'
        _box(ax, xo - 1.1, y - 0.5, 3.2, 1.1, face=LINK_PALE if out > 0 else '#fbe0cc',
             edge=col)
        _label(ax, xo + 0.5, y + 0.05, f'3 - {mem[-1]:.2f} = {out:+.2f}\n{verdict}',
               size=9.5, family=MONO)
    _label(ax, 6.3, 6.15, 'The same small rule runs at every step and passes its memory on',
           size=11.5, weight='bold')
    _save(fig, NN_DOC, 'a-recurrent-memory.svg')


def temporal_filter() -> None:
    """A size-3 filter sliding along time over force readings, and how stacking widens it."""
    force = np.array([0.0, 0.0, 0.0, 0.1, 0.2, 2.0, 4.0, 4.1, 4.0, 4.0, 3.9, 4.0])
    filt = np.array([-1.0, 0.0, 1.0])
    out = np.array([float(np.dot(force[i:i + 3], filt)) for i in range(len(force) - 2)])
    print('temporal filter [-1, 0, +1] over force', force.tolist(), '->',
          [round(v, 2) for v in out.tolist()])
    # receptive field growth with and without halving between layers (kernel 3 each)
    rf_plain, rf_half, jump = [], [], 1
    rp, rh = 1, 1
    for layer in range(4):
        rp += 2
        rf_plain.append(rp)
        rh += 2 * jump
        rf_half.append(rh)
        jump *= 2
    print('readings seen by one output after 1..4 layers of size-3 filters:',
          rf_plain, '; with halving the length between layers:', rf_half)

    fig = plt.figure(figsize=(13.0, 6.2), facecolor='white')
    ax = fig.add_axes((0.0, 0.34, 1.0, 0.66))
    _axes(ax, (-1.9, 12.6), (-0.4, 4.2))
    peak = int(np.argmax(out))
    for i, v in enumerate(force):
        face = LINK_PALE if peak <= i <= peak + 2 else 'white'
        ax.add_patch(Rectangle((i - 0.45, 2.6), 0.9, 0.8, facecolor=face, edgecolor=MUTED,
                               lw=1.0))
        _label(ax, i, 3.0, f'{v:g}', size=10, family=MONO)
    _label(ax, -1.2, 3.0, 'force', size=10, color=MUTED)
    for i, v in enumerate(out):
        x = i + 1
        face = GRIP_PALE if i == peak else 'white'
        ax.add_patch(Rectangle((x - 0.45, 0.2), 0.9, 0.8, facecolor=face, edgecolor=MUTED,
                               lw=1.0))
        _label(ax, x, 0.6, f'{v:.1f}', size=10, family=MONO)
    _label(ax, -1.2, 0.6, 'output', size=10, color=MUTED)
    for dx in (-1, 0, 1):
        ax.plot([peak + 1 + dx, peak + 1], [2.6, 1.0], color=GRIP, lw=1.2)
    _label(ax, peak + 3.4, 1.8, f'-1 x {force[peak]:g} + 0 x {force[peak + 1]:g} + 1 x '
           f'{force[peak + 2]:g} = {out[peak]:.1f}', size=9.5, family=MONO, color=GRIP,
           ha='left')
    _label(ax, 5.5, 3.95, 'time  ->   (one box = one reading)', size=10, color=MUTED)

    bx = fig.add_axes((0.2, 0.06, 0.6, 0.26))
    _plot_style(bx)
    layers = np.arange(1, 5)
    bx.plot(layers, rf_plain, color=LINK, marker='o', lw=2, label='stacked filters of size 3')
    bx.plot(layers, rf_half, color=WRIST, marker='s', lw=2,
            label='same, halving the length between layers (as a U-Net does)')
    for x, a, b in zip(layers, rf_plain, rf_half):
        bx.text(x + 0.06, a - 1.0, str(a), ha='left', va='top', fontsize=9, color=LINK)
        bx.text(x - 0.06, b + 1.0, str(b), ha='right', va='bottom', fontsize=9, color=WRIST)
    bx.set_xticks(layers)
    bx.set_xlabel('number of layers', fontsize=9.5)
    bx.set_ylabel('readings seen', fontsize=9.5)
    bx.set_ylim(-2, 40)
    bx.legend(fontsize=8.8, frameon=False, loc='upper left')
    _save(fig, NN_DOC, 'a-filter-along-time.svg')


def selective_memory() -> None:
    """A fixed running memory against one that chooses when to forget."""
    n = 40
    t = np.arange(n)
    force = np.where(t < 15, 1.0, 4.0) + 0.25 * np.sin(t * 1.7)
    fixed = np.zeros(n)
    sel = np.zeros(n)
    keep_used = np.zeros(n)
    fixed[0] = sel[0] = force[0]
    for k in range(1, n):
        fixed[k] = 0.9 * fixed[k - 1] + 0.1 * force[k]
        # the "selective" keep factor depends on the new reading: a big jump means forget
        jump = abs(force[k] - sel[k - 1])
        keep = 0.9 if jump < 1.0 else 0.1
        keep_used[k] = keep
        sel[k] = keep * sel[k - 1] + (1 - keep) * force[k]
    lag_fixed = int(np.argmax(fixed >= 3.5))
    lag_sel = int(np.argmax(sel >= 3.5))
    print(f'running memory after a jump at step 15: fixed keep 0.9 reaches 3.5 at step '
          f'{lag_fixed}; selective memory reaches it at step {lag_sel}')

    fig, ax = plt.subplots(figsize=(10.5, 4.6), facecolor='white')
    _plot_style(ax)
    ax.plot(t, force, color=MUTED, lw=1.2, marker='.', label='force readings')
    ax.plot(t, fixed, color=LINK, lw=2.2, label='fixed memory: always keep 0.9 of the old')
    ax.plot(t, sel, color=GRIP, lw=2.2,
            label='selective memory: keep 0.9, but only 0.1 after a big jump')
    ax.axvline(15, color=INK, lw=0.8, ls=':')
    ax.text(15.3, 0.25, 'the gripper touches\nthe part here', fontsize=9, color=INK)
    ax.annotate(f'reaches 3.5 N at step {lag_fixed}', (lag_fixed, fixed[lag_fixed]),
                (lag_fixed + 3, 2.2), fontsize=9, color=LINK,
                arrowprops=dict(arrowstyle='->', color=LINK))
    ax.annotate(f'reaches 3.5 N at step {lag_sel}', (lag_sel, sel[lag_sel]),
                (27.0, 5.2), fontsize=9, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP))
    ax.set_ylim(0, 6.2)
    ax.set_xlabel('reading number', fontsize=10)
    ax.set_ylabel('newtons', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('A state-space memory, fixed and selective', fontsize=11.5, color=INK,
                 weight='bold')
    _save(fig, NN_DOC, 'fixed-and-selective-memory.svg')


# --------------------------------------------------------------------------
# 04_keypoints-and-object-pose.md: 6D pose tracking
# --------------------------------------------------------------------------

def _icosphere_one_split() -> NDArray[np.float64]:
    """The 42 corners of an icosahedron split once: FoundationPose's first-frame viewpoints."""
    p = (1 + 5 ** 0.5) / 2
    v = np.array([[-1, p, 0], [1, p, 0], [-1, -p, 0], [1, -p, 0], [0, -1, p], [0, 1, p],
                  [0, -1, -p], [0, 1, -p], [p, 0, -1], [p, 0, 1], [-p, 0, -1], [-p, 0, 1]],
                 dtype=float)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    # every edge of the icosahedron has length 1.0515 on the unit sphere
    mids = []
    for i in range(12):
        for j in range(i + 1, 12):
            if np.linalg.norm(v[i] - v[j]) < 1.1:
                m = (v[i] + v[j]) / 2
                mids.append(m / np.linalg.norm(m))
    return np.vstack([v, np.array(mids)])


def first_frame_vs_next() -> None:
    """252 starting guesses on the first frame; one guess on every frame after."""
    views = _icosphere_one_split()
    n_views = len(views)
    turns = len(range(0, 360, 60))
    guesses = n_views * turns
    est_rounds, track_rounds = 5, 2
    print(f'FoundationPose first frame: {n_views} viewpoints x {turns} turns = {guesses} '
          f'starting guesses, each refined {est_rounds} rounds = {guesses * est_rounds} '
          f'refinement passes; tracking: 1 guess x {track_rounds} rounds = {track_rounds}')

    fig = plt.figure(figsize=(13.0, 5.6), facecolor='white')
    ax = fig.add_axes((0.02, 0.1, 0.42, 0.8), projection='3d')
    ax.set_box_aspect((1, 1, 1))
    uu, vv = np.mgrid[0:2 * np.pi:30j, 0:np.pi:16j]
    ax.plot_wireframe(np.cos(uu) * np.sin(vv), np.sin(uu) * np.sin(vv), np.cos(vv),
                      color=GRID, lw=0.4)
    ax.scatter(views[:, 0], views[:, 1], views[:, 2], color=LINK, s=26, depthshade=True)
    ax.set_axis_off()
    ax.view_init(elev=18, azim=35)
    ax.set_title(f'First frame: {n_views} viewpoints x {turns} turns\n= {guesses} starting '
                 f'guesses, each refined {est_rounds} rounds', fontsize=11.5, color=INK,
                 weight='bold')

    bx = fig.add_axes((0.5, 0.1, 0.48, 0.8))
    _axes(bx, (0, 10), (0, 7))
    _title(bx, 5.0, 6.55, f'Every later frame: 1 guess, refined {track_rounds} rounds',
           size=11.5)
    # a turned box: last frame's answer (dashed) and this frame's object (filled)
    def rect(cx: float, cy: float, ang: float) -> NDArray[np.float64]:
        c, s = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        pts = np.array([[-1.2, -0.8], [1.2, -0.8], [1.2, 0.8], [-1.2, 0.8], [-1.2, -0.8]])
        return pts @ np.array([[c, s], [-s, c]]) + np.array([cx, cy])
    now = rect(5.3, 3.4, 24)
    before = rect(4.95, 3.25, 17)
    bx.fill(now[:, 0], now[:, 1], color='#f6c89c', zorder=2)
    bx.plot(now[:, 0], now[:, 1], color=MUTED, lw=1.0, zorder=2)
    bx.plot(before[:, 0], before[:, 1], color=LINK, lw=2.0, ls=(0, (4, 2)), zorder=3)
    _label(bx, 5.0, 1.35, 'dashed: last frame\'s answer, used as this frame\'s only guess.\n'
           'Filled: where the part is now. They are close, because 1/30 s has passed.',
           size=9.8, color=INK)
    _label(bx, 5.0, 0.35, f'{guesses * est_rounds} refinement passes against '
           f'{track_rounds}', size=11, weight='bold', color=GRIP)
    _save(fig, POSE_DOC, 'first-frame-and-later-frames.svg')


def _pose_sim() -> dict[str, NDArray[np.float64]]:
    """A simulated turntable: the true turn, per-frame estimates, and a tracker."""
    rng = np.random.default_rng(3)
    n = 120
    t = np.arange(n)
    truth = 30.0 + 0.6 * t
    # per-frame estimation: small noise, and now and then the wrong one of two
    # look-alike answers (the part looks almost the same turned 180 degrees)
    est = truth + rng.normal(0, 2.5, n)
    flips = rng.random(n) < 0.06
    est[flips] += 180.0
    # tracking: start from the last answer, refine towards the truth, small noise
    trk = np.zeros(n)
    trk[0] = est[0] if not flips[0] else truth[0]
    for k in range(1, n):
        guess = trk[k - 1]
        for _ in range(2):      # two refinement rounds
            guess = guess + 0.6 * (truth[k] - guess) + rng.normal(0, 0.6)
        trk[k] = guess
    return {'t': t, 'truth': truth, 'est': est, 'trk': trk, 'flips': flips.astype(float)}


def smoother_track() -> None:
    """Estimating afresh every frame against tracking, on a simulated turntable."""
    s = _pose_sim()
    est_jump = np.abs(np.diff(s['est']))
    trk_jump = np.abs(np.diff(s['trk']))
    est_err = np.abs(s['est'] - s['truth'])
    trk_err = np.abs(s['trk'] - s['truth'])
    print(f'turntable simulation, {len(s["t"])} frames: estimate every frame -> '
          f'{int(s["flips"].sum())} flips of 180 deg, median frame-to-frame change '
          f'{np.median(est_jump):.2f} deg, median error {np.median(est_err):.2f} deg; '
          f'track -> median change {np.median(trk_jump):.2f} deg (true change 0.60), '
          f'median error {np.median(trk_err):.2f} deg, largest error {trk_err.max():.2f} deg')

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.0, 6.4), facecolor='white',
                                 sharex=True, gridspec_kw={'height_ratios': [1.6, 1.0]})
    for a in (a1, a2):
        _plot_style(a)
    a1.plot(s['t'], s['est'], '.', color=WRIST, ms=5, label='estimate afresh every frame')
    a1.plot(s['t'], s['trk'], color=LINK, lw=2.0, label='estimate once, then track')
    a1.plot(s['t'], s['truth'], color=INK, lw=0.8, ls=':', label='true turn')
    a1.set_ylabel('turn of the part (degrees)', fontsize=10)
    a1.legend(fontsize=9, frameon=False, loc='center right')
    a1.set_title('A part on a turntable, 120 frames (simulated)', fontsize=11.5, color=INK,
                 weight='bold')
    a2.plot(s['t'][1:], np.minimum(est_jump, 12), color=WRIST, lw=1.2,
            label='estimate afresh')
    a2.plot(s['t'][1:], trk_jump, color=LINK, lw=1.8, label='track')
    a2.set_ylim(0, 12.5)
    a2.set_ylabel('change from the\nframe before (deg,\ncut off at 12)', fontsize=10)
    a2.set_xlabel('frame', fontsize=10)
    a2.legend(fontsize=9, frameon=False, loc='center right')
    fig.tight_layout()
    _save(fig, POSE_DOC, 'estimate-every-frame-or-track.svg')


def lose_and_recover() -> None:
    """A hand hides the part; the tracker drifts, its score drops, and it re-detects."""
    rng = np.random.default_rng(5)
    n = 100
    t = np.arange(n)
    truth = 30.0 + 0.6 * t
    hidden = (t >= 40) & (t < 58)
    visible = np.where(hidden, 0.25, 1.0)
    threshold, patience = 0.5, 3

    def run(redetect: bool) -> tuple[NDArray[np.float64], NDArray[np.float64], list[int]]:
        trk = np.zeros(n)
        score = np.zeros(n)
        trk[0] = truth[0]
        low = 0
        redetects: list[int] = []
        for k in range(1, n):
            guess = trk[k - 1]
            if hidden[k]:
                # nothing to lock onto, so the guess wanders off
                guess = trk[k - 1] - 2.0 + rng.normal(0, 0.4)
            else:
                for _ in range(2):
                    # refinement only works when the guess is near: within 15 degrees
                    pull = 0.6 if abs(truth[k] - guess) < 15 else 0.0
                    guess = guess + pull * (truth[k] - guess) + rng.normal(0, 0.6)
            trk[k] = guess
            score[k] = visible[k] * np.exp(-abs(guess - truth[k]) / 15.0)
            low = low + 1 if score[k] < threshold else 0
            if redetect and low >= patience and not hidden[k]:
                trk[k] = truth[k] + rng.normal(0, 1.0)     # full first-frame estimate again
                score[k] = np.exp(-abs(trk[k] - truth[k]) / 15.0)
                redetects.append(k)
                low = 0
        score[0] = 1.0
        return trk, score, redetects

    trk_no, score_no, _ = run(False)
    trk_yes, score_yes, redo = run(True)
    print(f'hidden from frame 40 to 57; without re-detection the error at frame 99 is '
          f'{abs(trk_no[-1] - truth[-1]):.1f} deg; with re-detection (score below '
          f'{threshold} for {patience} frames in a row) it re-detects at frames {redo} '
          f'and the error at frame 99 is {abs(trk_yes[-1] - truth[-1]):.1f} deg')

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.0, 6.4), facecolor='white', sharex=True,
                                 gridspec_kw={'height_ratios': [1.5, 1.0]})
    for a in (a1, a2):
        _plot_style(a)
        a.axvspan(40, 57.5, color=GRIP_PALE, alpha=0.6, lw=0)
    a1.plot(t, truth, color=INK, lw=0.8, ls=':', label='true turn')
    a1.plot(t, trk_no, color=WRIST, lw=2.0, label='track only')
    a1.plot(t, trk_yes, color=LINK, lw=2.0, label='track, and re-detect when the score stays low')
    for k in redo:
        a1.plot(k, trk_yes[k], 'o', color=LINK, ms=8)
        a1.annotate('re-detect', (k, trk_yes[k]), (k + 4, trk_yes[k] - 25), fontsize=9,
                    color=LINK, arrowprops=dict(arrowstyle='->', color=LINK))
    a1.text(48.7, 84, 'a hand hides\nthe part', ha='center', fontsize=9, color=GRIP)
    a1.set_ylabel('turn of the part (degrees)', fontsize=10)
    a1.legend(fontsize=9, frameon=False, loc='upper left')
    a1.set_title('Losing track and finding it again (simulated)', fontsize=11.5, color=INK,
                 weight='bold')
    a2.plot(t, score_no, color=WRIST, lw=1.6, label='track only')
    a2.plot(t, score_yes, color=LINK, lw=1.6, label='with re-detection')
    a2.axhline(threshold, color=INK, lw=0.9, ls='--')
    a2.text(99, threshold + 0.03, f'threshold {threshold}', ha='right', va='bottom',
            fontsize=9, color=INK)
    a2.set_ylim(0, 1.1)
    a2.set_ylabel('match score\n(1 = perfect)', fontsize=10)
    a2.set_xlabel('frame', fontsize=10)
    a2.legend(fontsize=9, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, POSE_DOC, 'losing-track-and-re-detecting.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    three_ways()
    lora_counts()
    forgetting_curves()
    memory_by_mode()
    same_reading_two_stories()
    recurrent_memory()
    temporal_filter()
    selective_memory()
    first_frame_vs_next()
    smoother_track()
    lose_and_recover()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
