"""Generate the diagrams for both pages of docs/06_neural-networks/04_making-training-work/.

    01_overfitting-and-generalisation.md -> images/making-training-work/overfitting-and-generalisation/
    02_normalisation-and-stability.md    -> images/making-training-work/normalisation-and-stability/

Run with:  python3 making_training_work.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints them so the two documents can quote the same values.

All the data is simulated, and the methods run on it are real. The first page
uses a made-up one-input measurement curve with noise added by a seeded
generator, a seeded set of synthetic camera frames grouped into episodes and
scenes, and a seeded random-feature model; the polynomial fits, the small
network trained with Adam, the nearest-neighbour scores, the dropout masks,
the weight decay and the double-descent sweep are all computed here. The
second page uses a made-up two-feature regression in millimetres and metres, a
seeded deep stack of residual blocks, seeded gradient values, and a seeded
quadratic training run with one bad batch injected; the gradient-descent
convergence, the normalisation arithmetic, the batch-statistics spread, the
float16 and bfloat16 rounding and the loss spike are all computed here.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'making-training-work'
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

OVF_DOC: str = 'overfitting-and-generalisation'
NRM_DOC: str = 'normalisation-and-stability'

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


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, size: float = 9.5,
         weight: str = 'normal', tcol: str = INK, lw: float = 1.2) -> None:
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.02',
        facecolor=face, edgecolor=edge, linewidth=lw))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=size, color=tcol, weight=weight)


def _title(ax: Axes, text: str, size: float = 11.5) -> None:
    ax.set_title(text, fontsize=size, weight='bold', color=INK, pad=10)


# ==========================================================================
# PAGE 1: shared simulated data and experiments
# ==========================================================================

NOISE_SD: float = 0.35


def truth(x: Arr) -> Arr:
    """The made-up true relation: a sensor reading against slide position."""
    return 1.8 + 2.6 * np.sin(1.9 * x) - 0.45 * x


class Curve:
    """The small noisy measurement set, and the polynomial fits to it."""

    def __init__(self) -> None:
        rng = np.random.default_rng(7)
        self.x_tr: Arr = np.sort(rng.uniform(0.0, 3.0, 12))
        self.y_tr: Arr = truth(self.x_tr) + rng.normal(0.0, NOISE_SD, 12)
        self.x_ho: Arr = np.sort(rng.uniform(0.0, 3.0, 50))
        self.y_ho: Arr = truth(self.x_ho) + rng.normal(0.0, NOISE_SD, 50)
        self.grid: Arr = np.linspace(0.0, 3.0, 400)
        self.degrees: list[int] = list(range(0, 12))
        self.e_tr: Arr = np.zeros(len(self.degrees))
        self.e_ho: Arr = np.zeros(len(self.degrees))
        self.coefs: dict[int, Arr] = {}
        for i, d in enumerate(self.degrees):
            c = self.fit(d)
            self.coefs[d] = c
            self.e_tr[i] = self.rmse(c, self.x_tr, self.y_tr)
            self.e_ho[i] = self.rmse(c, self.x_ho, self.y_ho)
        self.best: int = int(self.degrees[int(np.argmin(self.e_ho))])

    @staticmethod
    def _design(x: Arr, n: int) -> Arr:
        return np.vander((x - 1.5) / 1.5, n, increasing=True)

    def fit(self, deg: int) -> Arr:
        v = self._design(self.x_tr, deg + 1)
        c, *_ = np.linalg.lstsq(v, self.y_tr, rcond=None)
        return c

    def predict(self, c: Arr, x: Arr) -> Arr:
        return self._design(x, len(c)) @ c

    def rmse(self, c: Arr, x: Arr, y: Arr) -> float:
        return float(np.sqrt(np.mean((self.predict(c, x) - y) ** 2)))


CV = Curve()


def _net_init(width: int, seed: int) -> list[Arr]:
    r = np.random.default_rng(seed)
    return [r.normal(0.0, 1.0, (1, width)), np.zeros(width),
            r.normal(0.0, 1.0 / np.sqrt(width), (width, width)), np.zeros(width),
            r.normal(0.0, 1.0 / np.sqrt(width), (width, 1)), np.zeros(1)]


def _net_fwd(p: list[Arr], x: Arr) -> tuple[Arr, tuple[Arr, Arr]]:
    w1, b1, w2, b2, w3, b3 = p
    h1 = np.tanh(x[:, None] @ w1 + b1)
    h2 = np.tanh(h1 @ w2 + b2)
    return (h2 @ w3 + b3)[:, 0], (h1, h2)


def _net_grads(p: list[Arr], x: Arr, t: Arr) -> list[Arr]:
    w1, b1, w2, b2, w3, b3 = p
    out, (h1, h2) = _net_fwd(p, x)
    n = len(x)
    d = 2.0 * (out - t) / n
    g_w3 = h2.T @ d[:, None]
    g_b3 = d.sum(keepdims=True)
    da2 = (d[:, None] @ w3.T) * (1 - h2 ** 2)
    g_w2 = h1.T @ da2
    g_b2 = da2.sum(0)
    da1 = (da2 @ w2.T) * (1 - h1 ** 2)
    g_w1 = x[:, None].T @ da1
    g_b1 = da1.sum(0)
    return [g_w1, g_b1, g_w2, g_b2, g_w3, g_b3]


def train_net(width: int = 96, steps: int = 8000, lr: float = 0.002,
              wd: float = 0.0, jitter: float = 0.0, seed: int = 4
              ) -> tuple[list[Arr], Arr, Arr]:
    """Train the small network on the 12 noisy points, tracking both errors."""
    p = _net_init(width, seed)
    m = [np.zeros_like(q) for q in p]
    v = [np.zeros_like(q) for q in p]
    jr = np.random.default_rng(99)
    tr = np.zeros(steps)
    ho = np.zeros(steps)
    for s in range(1, steps + 1):
        x_in = CV.x_tr + (jr.normal(0.0, jitter, CV.x_tr.size) if jitter > 0 else 0.0)
        g = _net_grads(p, x_in, CV.y_tr)
        for i in range(len(p)):
            m[i] = 0.9 * m[i] + 0.1 * g[i]
            v[i] = 0.999 * v[i] + 0.001 * g[i] ** 2
            mh = m[i] / (1 - 0.9 ** s)
            vh = v[i] / (1 - 0.999 ** s)
            p[i] -= lr * (mh / (np.sqrt(vh) + 1e-8) + wd * p[i])
        tr[s - 1] = np.mean((_net_fwd(p, CV.x_tr)[0] - CV.y_tr) ** 2)
        ho[s - 1] = np.mean((_net_fwd(p, CV.x_ho)[0] - CV.y_ho) ** 2)
    return p, tr, ho


class NetRun:
    """The plain run of the small network, used by sections 1 and 4."""

    def __init__(self) -> None:
        self.p, self.tr, self.ho = train_net()
        self.best: int = int(np.argmin(self.ho)) + 1
        self.best_ho: float = float(self.ho[self.best - 1])
        self.best_tr: float = float(self.tr[self.best - 1])
        self.final_tr: float = float(self.tr[-1])
        self.final_ho: float = float(self.ho[-1])
        self.curve: Arr = _net_fwd(self.p, CV.grid)[0]


# ==========================================================================
# PAGE 1, SECTION 1: the loss went down, but did it learn?
# ==========================================================================

def fig_poly_fits(net: NetRun) -> None:
    shown = [1, 5, 11]
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.9))
    for ax, d in zip(axes, shown):
        _plain(ax)
        c = CV.coefs[d]
        ax.plot(CV.grid, truth(CV.grid), color=MUTED, lw=1.3, ls='--',
                label='true relation')
        ax.plot(CV.grid, CV.predict(c, CV.grid), color=LINK, lw=2.2,
                label=f'polynomial of degree {d}')
        ax.scatter(CV.x_tr, CV.y_tr, s=46, color=GRIP, zorder=5,
                   edgecolor='white', linewidth=0.8, label='12 training points')
        ax.scatter(CV.x_ho, CV.y_ho, s=14, color=TEAL, alpha=0.75, zorder=4,
                   label='50 held-out points')
        ax.set_xlim(-0.08, 3.08)
        ax.set_ylim(-2.4, 5.4)
        ax.set_xlabel('slide position (metres)', fontsize=9.5)
        ax.grid(True, color=GRID, lw=0.6)
        i = CV.degrees.index(d)
        ax.set_title(f'degree {d}\ntraining {CV.e_tr[i]:.2f}   held-out {CV.e_ho[i]:.2f}',
                     fontsize=10.5, color=INK)
    axes[0].set_ylabel('sensor reading', fontsize=9.5)
    axes[0].legend(fontsize=8.0, loc='lower left', framealpha=0.95)
    fig.suptitle('A straighter line is too simple, degree 5 is right, degree 11 '
                 'goes through every training point and is useless',
                 fontsize=11.5, weight='bold', color=INK, y=1.04)
    _save(fig, OVF_DOC, 'poly-fits.svg')


def fig_error_vs_degree() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    _plain(ax)
    ax.plot(CV.degrees, CV.e_tr, 'o-', color=LINK, lw=2.0, ms=6,
            label='error on the 12 training points')
    ax.plot(CV.degrees, CV.e_ho, 's-', color=GRIP, lw=2.0, ms=6,
            label='error on the 50 held-out points')
    ax.axhline(NOISE_SD, color=MUTED, ls=':', lw=1.3)
    ax.text(0.1, NOISE_SD * 1.12, f'noise in the measurements: {NOISE_SD}',
            fontsize=9, color=MUTED)
    i = CV.degrees.index(CV.best)
    ax.scatter([CV.best], [CV.e_ho[i]], s=200, facecolor='none',
               edgecolor=SLIDE, linewidth=2.2, zorder=6)
    ax.annotate(f'best held-out error\n{CV.e_ho[i]:.3f} at degree {CV.best}',
                xy=(CV.best, CV.e_ho[i]), xytext=(CV.best + 0.7, 0.055),
                fontsize=9.5, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.3))
    ax.set_yscale('log')
    ax.set_xticks(CV.degrees)
    ax.set_xlabel('degree of the polynomial, which is how flexible the model is',
                  fontsize=10)
    ax.set_ylabel('root-mean-square error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='upper left')
    _title(ax, 'Training error only ever falls; held-out error bottoms out at degree '
               f'{CV.best} and then climbs to {CV.e_ho[-1]:.0f}')
    _save(fig, OVF_DOC, 'error-vs-degree.svg')


def fig_net_curves(net: NetRun) -> None:
    steps = np.arange(1, len(net.tr) + 1)
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    _plain(ax)
    ax.plot(steps, net.tr, color=LINK, lw=1.8, label='training loss (12 points)')
    ax.plot(steps, net.ho, color=GRIP, lw=1.8, label='held-out loss (50 points)')
    ax.axvline(net.best, color=SLIDE, ls='--', lw=1.4)
    ax.text(net.best * 1.12, 2.4,
            f'held-out loss is lowest\nat step {net.best}: {net.best_ho:.3f}',
            fontsize=9.5, color=SLIDE)
    ax.annotate(f'training loss {net.final_tr:.3f}',
                xy=(steps[-1], net.final_tr), xytext=(1100, 0.0035),
                fontsize=9.5, color=LINK,
                arrowprops=dict(arrowstyle='->', color=LINK, lw=1.1))
    ax.annotate(f'held-out loss {net.final_ho:.2f}',
                xy=(steps[-1], net.final_ho), xytext=(900, 8.0),
                fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('training step (log scale)', fontsize=10)
    ax.set_ylabel('mean squared error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='lower left')
    n_par = sum(q.size for q in net.p)
    _title(ax, f'A network with {n_par:,} weights and biases on 12 points: '
               f'the two losses part company after step {net.best}')
    _save(fig, OVF_DOC, 'network-train-and-held-out.svg')


def fig_net_curve_shape(net: NetRun) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    _plain(ax)
    ax.plot(CV.grid, truth(CV.grid), color=MUTED, lw=1.5, ls='--',
            label='true relation')
    ax.plot(CV.grid, net.curve, color=GRIP, lw=2.2,
            label='network after 8,000 steps')
    ax.scatter(CV.x_tr, CV.y_tr, s=52, color=LINK, zorder=5,
               edgecolor='white', linewidth=0.8, label='12 training points')
    ax.scatter(CV.x_ho, CV.y_ho, s=14, color=TEAL, alpha=0.7, zorder=4,
               label='50 held-out points')
    ax.set_xlabel('slide position (metres)', fontsize=10)
    ax.set_ylabel('sensor reading', fontsize=10)
    ax.set_xlim(-0.05, 3.05)
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(fontsize=9, loc='lower left')
    _title(ax, f'The trained network passes through the 12 points '
               f'(loss {net.final_tr:.3f}) by swinging far away between them')
    _save(fig, OVF_DOC, 'network-fitted-curve.svg')


# ==========================================================================
# PAGE 1, SECTION 2: three sets of data
# ==========================================================================

class Split:
    """One run of the three-way split, with the degree chosen on validation."""

    def __init__(self) -> None:
        rng = np.random.default_rng(101)
        n = 120
        x = np.sort(rng.uniform(0.0, 3.0, n))
        y = truth(x) + rng.normal(0.0, NOISE_SD, n)
        order = rng.permutation(n)
        self.n = n
        self.n_tr, self.n_va, self.n_te = 84, 18, 18
        self.i_tr = np.sort(order[:self.n_tr])
        self.i_va = np.sort(order[self.n_tr:self.n_tr + self.n_va])
        self.i_te = np.sort(order[self.n_tr + self.n_va:])
        self.x, self.y = x, y
        self.where = np.zeros(n, dtype=int)
        self.where[self.i_va] = 1
        self.where[self.i_te] = 2
        self.degrees = list(range(0, 12))
        self.e_tr = np.zeros(len(self.degrees))
        self.e_va = np.zeros(len(self.degrees))
        self.e_te = np.zeros(len(self.degrees))
        for i, d in enumerate(self.degrees):
            v = np.vander((x[self.i_tr] - 1.5) / 1.5, d + 1, increasing=True)
            c, *_ = np.linalg.lstsq(v, y[self.i_tr], rcond=None)
            for idx, store in ((self.i_tr, self.e_tr), (self.i_va, self.e_va),
                               (self.i_te, self.e_te)):
                vv = np.vander((x[idx] - 1.5) / 1.5, d + 1, increasing=True)
                store[i] = float(np.sqrt(np.mean((vv @ c - y[idx]) ** 2)))
        self.chosen = int(self.degrees[int(np.argmin(self.e_va))])
        k = self.degrees.index(self.chosen)
        self.chosen_va = float(self.e_va[k])
        self.chosen_te = float(self.e_te[k])


SP = Split()


def fig_three_way_split() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 3.5))
    _blank(ax)
    cols = {0: LINK_PALE, 1: JOINT, 2: GRIP}
    names = {0: 'training', 1: 'validation', 2: 'test'}
    per_row = 24
    for i in range(SP.n):
        r, c = divmod(i, per_row)
        ax.add_patch(mpatches.Rectangle((c * 1.0, -r * 1.0), 0.86, 0.86,
                                        facecolor=cols[SP.where[i]],
                                        edgecolor='white', linewidth=1.0))
    ax.set_xlim(-0.6, per_row + 7.4)
    ax.set_ylim(-5.0, 1.6)
    counts = {0: SP.n_tr, 1: SP.n_va, 2: SP.n_te}
    uses = {0: 'the weights are changed with these',
            1: 'the settings are chosen with these',
            2: 'touched once, at the very end'}
    for j in range(3):
        ax.add_patch(mpatches.Rectangle((per_row + 0.8, -j * 1.1 + 0.0), 0.8, 0.8,
                                        facecolor=cols[j], edgecolor='white'))
        ax.text(per_row + 1.85, -j * 1.1 + 0.42,
                f'{names[j]}: {counts[j]} of {SP.n} examples '
                f'({counts[j] / SP.n * 100:.0f}%)', fontsize=10, va='center',
                color=INK, weight='bold')
        ax.text(per_row + 1.85, -j * 1.1 - 0.02, uses[j], fontsize=8.8,
                va='center', color=MUTED)
    ax.text(-0.3, -4.5, 'each square is one measurement, and the colour says '
                        'which set it was put in',
            fontsize=9.5, color=MUTED)
    _title(ax, f'{SP.n} examples split three ways: '
               f'{SP.n_tr} training, {SP.n_va} validation, {SP.n_te} test')
    _save(fig, OVF_DOC, 'three-way-split.svg')


def fig_choosing_on_validation() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    _plain(ax)
    ax.plot(SP.degrees, SP.e_tr, 'o-', color=LINK_PALE, lw=1.8, ms=5,
            label=f'training error ({SP.n_tr} points)')
    ax.plot(SP.degrees, SP.e_va, 'o-', color=JOINT, lw=2.2, ms=6,
            label=f'validation error ({SP.n_va} points)')
    ax.plot(SP.degrees, SP.e_te, 's--', color=GRIP, lw=1.8, ms=5,
            label=f'test error ({SP.n_te} points)')
    ax.axvline(SP.chosen, color=SLIDE, ls='--', lw=1.5)
    ax.text(SP.chosen + 0.2, max(SP.e_va) * 0.55,
            f'degree {SP.chosen} wins on validation\n'
            f'validation {SP.chosen_va:.3f}\ntest {SP.chosen_te:.3f}',
            fontsize=9.5, color=SLIDE)
    ax.set_yscale('log')
    ax.set_xticks(SP.degrees)
    ax.set_xlabel('degree of the polynomial', fontsize=10)
    ax.set_ylabel('root-mean-square error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='upper left')
    _title(ax, 'The validation set picks the degree, and only then is the '
               'test set read once')
    _save(fig, OVF_DOC, 'choosing-on-validation.svg')


class TestReuse:
    """Best-of-k on a 20-trial test set, when every candidate is equally good."""

    def __init__(self) -> None:
        self.p_true = 0.70
        self.trials = 20
        self.ks = [1, 2, 3, 5, 8, 12, 20, 30, 50]
        self.reps = 20000
        rng = np.random.default_rng(2024)
        draws = rng.binomial(self.trials, self.p_true,
                             size=(self.reps, max(self.ks))) / self.trials
        self.measured = np.array([draws[:, :k].max(1).mean() for k in self.ks])
        fresh = rng.binomial(self.trials, self.p_true,
                             size=(self.reps, max(self.ks))) / self.trials
        self.honest = np.array([
            fresh[np.arange(self.reps), draws[:, :k].argmax(1)].mean()
            for k in self.ks])


TR = TestReuse()


def fig_reusing_the_test_set() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.5))
    _plain(ax)
    ax.plot(TR.ks, TR.measured * 100, 'o-', color=GRIP, lw=2.2, ms=6,
            label='score the best candidate shows on that test set')
    ax.plot(TR.ks, TR.honest * 100, 's-', color=LINK, lw=2.2, ms=6,
            label='score the same candidate gets on fresh trials')
    ax.axhline(TR.p_true * 100, color=MUTED, ls=':', lw=1.4)
    ax.text(1.1, TR.p_true * 100 - 3.0,
            f'every candidate really succeeds {TR.p_true * 100:.0f}% of the time',
            fontsize=9.2, color=MUTED)
    for k, m, h in zip(TR.ks, TR.measured, TR.honest):
        if k in (1, 12, 50):
            ax.annotate(f'{m * 100:.1f}%', xy=(k, m * 100), xytext=(0, 9),
                        textcoords='offset points', ha='center',
                        fontsize=9.2, color=GRIP)
    ax.set_xscale('log')
    ax.set_xticks(TR.ks)
    ax.set_xticklabels([str(k) for k in TR.ks])
    ax.set_xlabel('how many candidates were compared on the same test set',
                  fontsize=10)
    ax.set_ylabel('success rate (%)', fontsize=10)
    ax.set_ylim(60, 92)
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(fontsize=9.3, loc='upper left')
    _title(ax, 'Picking the winner on the test set makes the test set lie: '
               f'{TR.measured[0] * 100:.0f}% becomes '
               f'{TR.measured[-1] * 100:.0f}% while nothing improved')
    _save(fig, OVF_DOC, 'reusing-the-test-set.svg')


# ==========================================================================
# PAGE 1, SECTION 3: leakage
# ==========================================================================

class Frames:
    """Simulated camera frames: 3 scenes, 9 episodes each, 40 frames each."""

    def __init__(self) -> None:
        rng = np.random.default_rng(23)
        self.d = 8
        self.n_scene, self.n_ep, self.n_fr = 3, 9, 40
        centre = rng.normal(0.0, 1.0, (3, self.d))
        scene_off = rng.normal(0.0, 1.0, (self.n_scene, self.d))
        rows: list[tuple[int, int, int, int]] = []
        feats: list[Arr] = []
        labels_per_ep = np.repeat([0, 1, 2], 3)
        for s in range(self.n_scene):
            for e in range(self.n_ep):
                lab = int(labels_per_ep[e])
                ep_off = rng.normal(0.0, 0.8, self.d)
                phase = rng.uniform(0.0, 2 * np.pi, self.d)
                freq = rng.uniform(0.5, 1.5, self.d)
                for t in range(self.n_fr):
                    drift = 0.30 * np.sin(freq * (t / self.n_fr * 2 * np.pi) + phase)
                    feats.append(centre[lab] + scene_off[s] + ep_off + drift
                                 + rng.normal(0.0, 0.04, self.d))
                    rows.append((s, s * self.n_ep + e, t, lab))
        meta = np.array(rows)
        self.scene = meta[:, 0]
        self.ep = meta[:, 1]
        self.frame = meta[:, 2]
        self.lab = meta[:, 3]
        self.x: Arr = np.array(feats)
        self.n = len(self.x)
        self.labels_per_ep = labels_per_ep
        self.ho_eps = [s * self.n_ep + e for s in range(self.n_scene)
                       for e in (0, 3, 6)]
        idx = np.arange(self.n)
        perm = np.random.default_rng(77).permutation(self.n)
        cut = int(0.7 * self.n)
        self.acc_frame = self._knn(perm[:cut], perm[cut:])
        m = np.isin(self.ep, self.ho_eps)
        self.acc_episode = self._knn(idx[~m], idx[m])
        m2 = self.scene == 2
        self.acc_scene = self._knn(idx[~m2], idx[m2])
        self.chance = 1.0 / 3.0
        self.nn_gap = float(np.linalg.norm(self.x[1] - self.x[0]))
        other = self.x[self.ep != self.ep[0]]
        self.cross_gap = float(np.min(np.linalg.norm(other - self.x[0], axis=1)))

    def _knn(self, tr: NDArray[np.int64], te: NDArray[np.int64]) -> float:
        d = ((self.x[te][:, None, :] - self.x[tr][None, :, :]) ** 2).sum(-1)
        return float((self.lab[tr][d.argmin(1)] == self.lab[te]).mean())


FR = Frames()


def fig_frame_split_strip() -> None:
    rng = np.random.default_rng(5)
    n_show = 26
    pick = rng.random(n_show) < 0.3
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 4.3))
    for ax, mode in zip(axes, ('random frame', 'whole episode')):
        _blank(ax)
        ax.set_xlim(-3.4, n_show + 0.6)
        ax.set_ylim(-1.2, 1.5)
        for i in range(n_show):
            if mode == 'random frame':
                held = bool(pick[i])
            else:
                held = i >= 18
            ax.add_patch(mpatches.Rectangle((i, 0.0), 0.86, 0.86,
                                            facecolor=GRIP if held else LINK_PALE,
                                            edgecolor='white', linewidth=1.0))
            ax.text(i + 0.43, 0.43, str(i + 1), ha='center', va='center',
                    fontsize=7.0, color=INK if not held else 'white')
        ax.text(-0.5, 0.43, mode, ha='right', va='center', fontsize=10.5,
                color=INK, weight='bold')
        if mode == 'random frame':
            ax.text(-0.5, -0.6, 'frames 7 and 8 are 1/30 of a second apart and\n'
                                'land on opposite sides of the split',
                    ha='right', va='center', fontsize=8.6, color=GRIP)
        else:
            ax.text(-0.5, -0.6, 'every held-out frame comes from an episode\n'
                                'the model never trained on',
                    ha='right', va='center', fontsize=8.6, color=SLIDE)
    axes[0].text(n_show * 0.42, 1.15, 'one continuous recording, frame by frame',
                 fontsize=9.5, color=MUTED)
    fig.suptitle('Splitting frames at random puts near-identical pictures on both '
                 'sides; splitting by episode does not',
                 fontsize=11.5, weight='bold', color=INK, y=1.03)
    _save(fig, OVF_DOC, 'frame-split-strip.svg')


def fig_split_kinds_score() -> None:
    names = ['random frame\nsplit', 'episode\nsplit', 'new scene\nsplit']
    vals = [FR.acc_frame, FR.acc_episode, FR.acc_scene]
    cols = [GRIP, JOINT, LINK]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    _plain(ax)
    bars = ax.bar(names, [v * 100 for v in vals], color=cols, width=0.55,
                  edgecolor='white')
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 100 + 1.6,
                f'{v * 100:.1f}%', ha='center', fontsize=11, color=INK,
                weight='bold')
    ax.axhline(FR.chance * 100, color=MUTED, ls=':', lw=1.4)
    ax.text(2.42, FR.chance * 100 + 1.4,
            f'guessing: {FR.chance * 100:.1f}%', fontsize=9.2, color=MUTED,
            ha='right')
    ax.set_ylim(0, 112)
    ax.set_ylabel('accuracy of the same model on held-out frames (%)', fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.6)
    _title(ax, 'The same model and the same data, scored three ways: '
               f'{FR.acc_frame * 100:.0f}%, {FR.acc_episode * 100:.0f}% '
               f'and {FR.acc_scene * 100:.0f}%')
    _save(fig, OVF_DOC, 'split-kinds-score.svg')


def fig_episodes_by_scene() -> None:
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    _blank(ax)
    for s in range(FR.n_scene):
        for e in range(FR.n_ep):
            ep_id = s * FR.n_ep + e
            held = ep_id in FR.ho_eps
            lab = int(FR.labels_per_ep[e])
            ax.add_patch(mpatches.Rectangle((e * 1.1, -s * 1.1), 1.0, 1.0,
                                            facecolor=GRIP if held else LINK_PALE,
                                            edgecolor='white', linewidth=1.4))
            ax.text(e * 1.1 + 0.5, -s * 1.1 + 0.62, f'ep {e + 1}',
                    ha='center', va='center', fontsize=8.2,
                    color='white' if held else INK)
            ax.text(e * 1.1 + 0.5, -s * 1.1 + 0.3, f'object {lab + 1}',
                    ha='center', va='center', fontsize=7.4,
                    color='white' if held else MUTED)
        ax.text(-0.35, -s * 1.1 + 0.5, f'scene {s + 1}', ha='right', va='center',
                fontsize=10.5, color=INK, weight='bold')
    ax.set_xlim(-2.6, FR.n_ep * 1.1 + 0.4)
    ax.set_ylim(-FR.n_scene * 1.1 - 0.8, 1.0)
    ax.text(0.0, -FR.n_scene * 1.1 - 0.35,
            f'{len(FR.ho_eps)} whole episodes held out, {FR.n_fr} frames each, '
            f'one of each object from each scene', fontsize=9.3, color=MUTED)
    _title(ax, f'{FR.n_scene * FR.n_ep} episodes of {FR.n_fr} frames, '
               'split by episode and balanced across objects and scenes')
    _save(fig, OVF_DOC, 'episodes-by-scene.svg')


# ==========================================================================
# PAGE 1, SECTION 4: early stopping, dropout, weight decay
# ==========================================================================

def fig_early_stopping(net: NetRun) -> None:
    steps = np.arange(1, len(net.ho) + 1)
    top = 2500
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    _plain(ax)
    ax.plot(steps[:top], net.tr[:top], color=LINK, lw=1.8, label='training loss')
    ax.plot(steps[:top], net.ho[:top], color=GRIP, lw=1.8, label='validation loss')
    ax.scatter([net.best], [net.best_ho], s=150, facecolor='none',
               edgecolor=SLIDE, linewidth=2.2, zorder=6)
    ax.axvline(net.best, color=SLIDE, ls='--', lw=1.3)
    ax.annotate(f'stop here: step {net.best}\nvalidation {net.best_ho:.4f}',
                xy=(net.best, net.best_ho), xytext=(net.best + 420, 0.52),
                fontsize=9.6, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.annotate(f'carry on to step 8,000 and\nvalidation reaches '
                f'{net.final_ho:.2f}',
                xy=(top, net.ho[top - 1]), xytext=(900, 1.15),
                fontsize=9.6, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('mean squared error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='lower left')
    _title(ax, 'Early stopping keeps the weights from the best validation step, '
               f'not the last one')
    _save(fig, OVF_DOC, 'early-stopping-point.svg')


class Dropout:
    """One real small layer, with one real dropout mask worked out on it."""

    def __init__(self) -> None:
        rng = np.random.default_rng(314)
        self.p = 0.25
        self.x = np.round(rng.uniform(-1.0, 1.0, 6), 2)
        self.w = np.round(rng.normal(0.0, 0.8, (8, 6)), 2)
        self.b = np.round(rng.normal(0.0, 0.3, 8), 2)
        self.h = np.maximum(0.0, self.w @ self.x + self.b)
        mrng = np.random.default_rng(2718)
        self.keep = (mrng.random(8) >= self.p)
        self.dropped = self.h * self.keep
        self.scale = 1.0 / (1.0 - self.p)
        self.scaled = self.dropped * self.scale
        self.sum_h = float(self.h.sum())
        self.sum_dropped = float(self.dropped.sum())
        self.sum_scaled = float(self.scaled.sum())
        many = np.random.default_rng(99991).random((40000, 8)) >= self.p
        self.mean_raw = float((many * self.h).sum(1).mean())
        self.mean_scaled = float((many * self.h).sum(1).mean() * self.scale)
        self.n_zero_before = int((self.h == 0).sum())
        self.n_dropped = int((~self.keep).sum())


DP = Dropout()


def fig_dropout_one_layer() -> None:
    rows = [('weighted sum then ReLU', DP.h, LINK_PALE),
            ('mask: 1 keeps, 0 drops', DP.keep.astype(float), None),
            ('after the mask', DP.dropped, LINK_PALE),
            (f'divided by 1 - {DP.p} = multiplied by {DP.scale:.4f}',
             DP.scaled, JOINT)]
    fig, ax = plt.subplots(figsize=(10.6, 4.3))
    _blank(ax)
    for r, (name, vals, face) in enumerate(rows):
        y = -r * 1.0
        ax.text(-0.3, y + 0.35, name, ha='right', va='center', fontsize=9.6,
                color=INK)
        for i, v in enumerate(vals):
            if name.startswith('mask'):
                col = SLIDE if DP.keep[i] else GRIP
                txt = '1' if DP.keep[i] else '0'
                tcol = 'white'
            else:
                col = 'white' if v == 0 else face
                txt = f'{v:.2f}'
                tcol = MUTED if v == 0 else INK
            ax.add_patch(mpatches.Rectangle((i * 1.15, y), 1.02, 0.7,
                                            facecolor=col, edgecolor=INK,
                                            linewidth=1.0))
            ax.text(i * 1.15 + 0.51, y + 0.35, txt, ha='center', va='center',
                    fontsize=9.4, color=tcol)
        total = vals.sum() if not name.startswith('mask') else DP.keep.sum()
        label = f'sum {total:.3f}' if not name.startswith('mask') \
            else f'{int(total)} of 8 kept'
        ax.text(8 * 1.15 + 0.25, y + 0.35, label, fontsize=9.6, va='center',
                color=INK, weight='bold')
    for i in range(8):
        ax.text(i * 1.15 + 0.51, 0.95, f'unit {i + 1}', ha='center',
                fontsize=8.4, color=MUTED)
    ax.set_xlim(-6.4, 8 * 1.15 + 2.6)
    ax.set_ylim(-3.5, 1.4)
    _title(ax, f'Dropout with p = {DP.p} on one layer of 8 units: '
               f'{DP.n_dropped} units are set to 0 and the rest grow by '
               f'{DP.scale:.4f} times')
    _save(fig, OVF_DOC, 'dropout-one-layer.svg')


def fig_dropout_average() -> None:
    names = ['layer sum with\nno dropout', 'average layer sum\nafter the mask,\n'
             'no scaling', 'average layer sum\nafter the mask\nand the scaling']
    vals = [DP.sum_h, DP.mean_raw, DP.mean_scaled]
    cols = [LINK, GRIP, SLIDE]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    _plain(ax)
    bars = ax.bar(names, vals, color=cols, width=0.5, edgecolor='white')
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f'{v:.4f}',
                ha='center', fontsize=11, color=INK, weight='bold')
    ax.axhline(DP.sum_h, color=MUTED, ls=':', lw=1.3)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('sum of the 8 activations', fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.6)
    _title(ax, 'Averaged over 40,000 random masks, the scaling puts the layer '
               'sum back where it was')
    _save(fig, OVF_DOC, 'dropout-keeps-the-average.svg')


class Decay:
    """The same network trained with a range of weight decay strengths."""

    def __init__(self) -> None:
        self.wds = [0.0, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]
        self.final_tr: list[float] = []
        self.final_ho: list[float] = []
        self.rms_w: list[float] = []
        self.max_w: list[float] = []
        self.weights: dict[float, Arr] = {}
        for wd in self.wds:
            p, tr, ho = train_net(wd=wd)
            allw = np.concatenate([q.ravel() for q in (p[0], p[2], p[4])])
            self.weights[wd] = allw
            self.final_tr.append(float(tr[-1]))
            self.final_ho.append(float(ho[-1]))
            self.rms_w.append(float(np.sqrt(np.mean(allw ** 2))))
            self.max_w.append(float(np.abs(allw).max()))
        self.best_i = int(np.argmin(self.final_ho))
        self.best_wd = self.wds[self.best_i]
        self.n_params = sum(q.size for q in train_net(steps=1)[0])


def fig_weight_sizes(dec: Decay) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    _plain(ax)
    bins = np.linspace(-3.0, 3.0, 61)
    a = dec.weights[0.0]
    b = dec.weights[dec.best_wd]
    ax.hist(a, bins=bins, color=GRIP, alpha=0.6, label=f'no weight decay, '
            f'root-mean-square {dec.rms_w[0]:.4f}, largest '
            f'{dec.max_w[0]:.2f}')
    ax.hist(b, bins=bins, color=LINK, alpha=0.6,
            label=f'weight decay {dec.best_wd}, root-mean-square '
                  f'{dec.rms_w[dec.best_i]:.4f}, largest '
                  f'{dec.max_w[dec.best_i]:.2f}')
    ax.set_xlabel('value of one weight at the end of training', fontsize=10)
    ax.set_ylabel(f'how many of the {dec.n_params:,} numbers', fontsize=10)
    ax.set_yscale('log')
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(fontsize=9.0, loc='upper right')
    _title(ax, 'Weight decay pulls every weight towards zero, so the long tails '
               'of big weights disappear')
    _save(fig, OVF_DOC, 'weight-sizes.svg')


def fig_weight_decay_sweep(dec: Decay) -> None:
    xs = [max(w, 0.003) for w in dec.wds]
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    _plain(ax)
    ax.plot(xs, dec.final_ho, 'o-', color=GRIP, lw=2.2, ms=6,
            label='validation loss at step 8,000')
    ax.plot(xs, dec.final_tr, 'o-', color=LINK, lw=2.0, ms=6,
            label='training loss at step 8,000')
    ax.scatter([xs[dec.best_i]], [dec.final_ho[dec.best_i]], s=200,
               facecolor='none', edgecolor=SLIDE, linewidth=2.2, zorder=6)
    ax.annotate(f'best: decay {dec.best_wd},\nvalidation '
                f'{dec.final_ho[dec.best_i]:.4f}',
                xy=(xs[dec.best_i], dec.final_ho[dec.best_i]),
                xytext=(0.012, 0.9), fontsize=9.6, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.annotate(f'no decay:\n{dec.final_ho[0]:.2f}', xy=(xs[0], dec.final_ho[0]),
                xytext=(0.0045, 1.4), fontsize=9.6, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(xs)
    ax.set_xticklabels(['0'] + [str(w) for w in dec.wds[1:]])
    ax.set_xlabel('weight decay strength (log scale, left-hand point is zero)',
                  fontsize=10)
    ax.set_ylabel('mean squared error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.3, loc='lower left')
    _title(ax, f'Validation loss falls from {dec.final_ho[0]:.2f} to '
               f'{dec.final_ho[dec.best_i]:.3f} and then rises again, '
               'so decay has a best size')
    _save(fig, OVF_DOC, 'weight-decay-sweep.svg')


# ==========================================================================
# PAGE 1, SECTION 5: augmentation
# ==========================================================================

class Pictures:
    """Two made-up 16 by 16 pictures: a mug and a left-handed spanner."""

    size = 16

    def __init__(self) -> None:
        self.mug = self._mug()
        self.tool = self._tool()
        self.mug_flip = self.mug[:, ::-1]
        self.tool_flip = self.tool[:, ::-1]
        self.mug_shift = np.roll(self.mug, 2, axis=1)
        self.mug_dim = self.mug * 0.6
        self.vals = {
            'mug': self._stats(self.mug),
            'mug flipped': self._stats(self.mug_flip),
            'mug shifted': self._stats(self.mug_shift),
            'mug dimmed': self._stats(self.mug_dim),
            'spanner': self._stats(self.tool),
            'spanner flipped': self._stats(self.tool_flip),
        }

    def _blank(self) -> Arr:
        return np.zeros((self.size, self.size))

    def _mug(self) -> Arr:
        a = self._blank()
        a[4:13, 4:10] = 0.85          # body
        a[4:6, 4:10] = 0.55           # rim
        a[6:10, 10:12] = 0.85         # handle on the right
        a[7:9, 11:13] = 0.85
        return a

    def _tool(self) -> Arr:
        a = self._blank()
        a[3:13, 7:9] = 0.8            # shaft
        a[3:5, 4:9] = 0.8             # head bent to the left
        a[11:13, 7:11] = 0.8          # foot bent to the right
        return a

    def _stats(self, a: Arr) -> dict[str, float]:
        cols = np.arange(self.size)
        mass = a.sum()
        centre = float((a.sum(0) * cols).sum() / mass)
        left = float(a[:, :self.size // 2].sum())
        right = float(a[:, self.size // 2:].sum())
        return {'mean': float(a.mean()), 'centre': centre,
                'lean': right - left, 'mass': float(mass)}


PIC = Pictures()


def _show_grid(ax: Axes, a: Arr, title: str, sub: str) -> None:
    ax.imshow(a, cmap='Greys', vmin=0.0, vmax=1.0, interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_color(GRID)
    ax.set_title(title, fontsize=10.2, color=INK)
    ax.set_xlabel(sub, fontsize=8.6, color=MUTED)


def fig_safe_augmentations() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.6))
    items = [('original mug', PIC.mug, 'mug'),
             ('shifted 2 columns right', PIC.mug_shift, 'mug shifted'),
             ('brightness x 0.6', PIC.mug_dim, 'mug dimmed'),
             ('flipped left to right', PIC.mug_flip, 'mug flipped')]
    for ax, (name, arr, key) in zip(axes, items):
        v = PIC.vals[key]
        _show_grid(ax, arr, name,
                   f'mean brightness {v["mean"]:.4f}\n'
                   f'centre column {v["centre"]:.2f}')
    fig.suptitle('Three changes to a picture of a mug that all leave the answer '
                 '"mug" true', fontsize=11.5, weight='bold', color=INK, y=1.04)
    _save(fig, OVF_DOC, 'safe-augmentations.svg')


def fig_flip_handed_tool() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.7))
    pairs = [('mug', PIC.mug, 'mug', 'still a mug'),
             ('mug flipped', PIC.mug_flip, 'mug flipped', 'still a mug'),
             ('left-handed spanner', PIC.tool, 'spanner', 'the part you have'),
             ('spanner flipped', PIC.tool_flip, 'spanner flipped',
              'a right-handed spanner,\nwhich is a different part')]
    for ax, (name, arr, key, verdict) in zip(axes, pairs):
        v = PIC.vals[key]
        _show_grid(ax, arr, name,
                   f'lean {v["lean"]:+.2f}\n{verdict}')
    for ax in axes[2:]:
        for side in ('top', 'right', 'bottom', 'left'):
            ax.spines[side].set_color(GRIP)
            ax.spines[side].set_linewidth(1.8)
    fig.suptitle('The lean of the picture, which is the brightness on the right '
                 'minus the brightness on the left, changes sign under a flip',
                 fontsize=11.5, weight='bold', color=INK, y=1.05)
    _save(fig, OVF_DOC, 'flipping-a-handed-tool.svg')


class Jitter:
    """The same network trained with a range of input-jitter strengths."""

    def __init__(self) -> None:
        self.js = [0.0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8]
        self.final_ho: list[float] = []
        self.final_tr: list[float] = []
        for j in self.js:
            _, tr, ho = train_net(jitter=j)
            self.final_tr.append(float(tr[-1]))
            self.final_ho.append(float(ho[-1]))
        self.best_i = int(np.argmin(self.final_ho))
        self.best_j = self.js[self.best_i]


def fig_jitter_sweep(ji: Jitter) -> None:
    xs = [max(j, 0.006) for j in ji.js]
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    _plain(ax)
    ax.plot(xs, ji.final_ho, 'o-', color=GRIP, lw=2.2, ms=6,
            label='held-out loss at step 8,000')
    ax.plot(xs, ji.final_tr, 'o-', color=LINK, lw=2.0, ms=6,
            label='training loss at step 8,000')
    ax.scatter([xs[ji.best_i]], [ji.final_ho[ji.best_i]], s=200,
               facecolor='none', edgecolor=SLIDE, linewidth=2.2, zorder=6)
    ax.annotate(f'best jitter {ji.best_j} metres,\nheld-out '
                f'{ji.final_ho[ji.best_i]:.4f}',
                xy=(xs[ji.best_i], ji.final_ho[ji.best_i]), xytext=(0.03, 0.9),
                fontsize=9.6, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.annotate(f'no jitter: {ji.final_ho[0]:.2f}',
                xy=(xs[0], ji.final_ho[0]), xytext=(0.008, 1.3),
                fontsize=9.6, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(xs)
    ax.set_xticklabels(['0'] + [str(j) for j in ji.js[1:]])
    ax.set_xlabel('size of the random shift added to the slide position, in metres',
                  fontsize=10)
    ax.set_ylabel('mean squared error (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.3, loc='lower left')
    _title(ax, 'Shifting each training input a little every step cuts the '
               f'held-out loss from {ji.final_ho[0]:.2f} to '
               f'{ji.final_ho[ji.best_i]:.3f}')
    _save(fig, OVF_DOC, 'jitter-sweep.svg')


# ==========================================================================
# PAGE 1, SECTION 6: where the classical picture runs out
# ==========================================================================

class DoubleDescent:
    """Random-feature models of rising width on 60 training examples."""

    def __init__(self) -> None:
        rng = np.random.default_rng(5)
        self.d_in, self.n, self.n_te = 20, 60, 3000
        beta = rng.normal(0.0, 1.0, self.d_in) / np.sqrt(self.d_in)
        x_tr = rng.normal(0.0, 1.0, (self.n, self.d_in))
        x_te = rng.normal(0.0, 1.0, (self.n_te, self.d_in))
        def f(x: Arr) -> Arr:
            return x @ beta + 0.4 * np.tanh(x[:, 0] * x[:, 1])
        y_tr = f(x_tr) + rng.normal(0.0, 0.25, self.n)
        y_te = f(x_te)
        self.max_p = 1200
        w = rng.normal(0.0, 1.0, (self.d_in, self.max_p)) / np.sqrt(self.d_in)
        b = rng.normal(0.0, 0.5, self.max_p)
        self.ps = [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 58, 60, 62, 64, 72, 88,
                   120, 160, 240, 360, 520, 800, 1200]
        self.e_tr: list[float] = []
        self.e_te: list[float] = []
        for p in self.ps:
            f_tr = np.maximum(0.0, x_tr @ w[:, :p] + b[:p])
            f_te = np.maximum(0.0, x_te @ w[:, :p] + b[:p])
            c = np.linalg.pinv(f_tr) @ y_tr
            self.e_tr.append(float(np.sqrt(np.mean((f_tr @ c - y_tr) ** 2))))
            self.e_te.append(float(np.sqrt(np.mean((f_te @ c - y_te) ** 2))))
        under = [i for i, p in enumerate(self.ps) if p < self.n - 4]
        self.classic_i = int(min(under, key=lambda i: self.e_te[i]))
        self.peak_i = int(max(range(len(self.ps)), key=lambda i: self.e_te[i]))
        self.final_i = len(self.ps) - 1
        self.zero_i = int(min(i for i in range(len(self.ps))
                              if self.e_tr[i] < 1e-9))


DD = DoubleDescent()


def fig_classical_picture() -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    _plain(ax)
    keep = [i for i, d in enumerate(CV.degrees) if d <= 8]
    ax.plot([CV.degrees[i] for i in keep], [CV.e_tr[i] for i in keep], 'o-',
            color=LINK, lw=2.2, ms=6, label='training error')
    ax.plot([CV.degrees[i] for i in keep], [CV.e_ho[i] for i in keep], 's-',
            color=GRIP, lw=2.2, ms=6, label='held-out error')
    i = CV.degrees.index(CV.best)
    ax.axvline(CV.best, color=SLIDE, ls='--', lw=1.4)
    ax.text(CV.best + 0.15, 3.2, f'the sweet spot\nat degree {CV.best}',
            fontsize=9.6, color=SLIDE)
    ax.text(0.2, 0.25, 'too simple', fontsize=9.6, color=MUTED)
    ax.text(6.6, 0.25, 'too flexible', fontsize=9.6, color=MUTED)
    ax.set_xticks([CV.degrees[i] for i in keep])
    ax.set_xlabel('how flexible the model is', fontsize=10)
    ax.set_ylabel('root-mean-square error', fontsize=10)
    ax.set_ylim(0, 4.2)
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(fontsize=9.5, loc='upper center')
    _title(ax, 'The classical picture: held-out error falls, bottoms out, '
               'then rises for good')
    _save(fig, OVF_DOC, 'the-classical-picture.svg')


def fig_double_descent() -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    _plain(ax)
    ax.plot(DD.ps, DD.e_te, 'o-', color=GRIP, lw=2.2, ms=5,
            label=f'error on {DD.n_te:,} held-out examples')
    ax.axvline(DD.n, color=MUTED, ls='--', lw=1.4)
    ax.text(DD.n * 1.08, 1.86,
            f'width = number of\ntraining examples ({DD.n})',
            fontsize=9.3, color=MUTED)
    for i, note, dx, dy in ((DD.classic_i, 'best narrow model\n', 0.35, 0.42),
                            (DD.peak_i, 'worst of all\n', 1.6, 0.06),
                            (DD.final_i, 'widest model\n', 0.14, 0.42)):
        ax.annotate(f'{note}width {DD.ps[i]}, error {DD.e_te[i]:.3f}',
                    xy=(DD.ps[i], DD.e_te[i]),
                    xytext=(DD.ps[i] * dx, DD.e_te[i] + dy),
                    fontsize=9.3, color=INK, ha='center',
                    arrowprops=dict(arrowstyle='->', color=INK, lw=1.0))
    ax.set_xscale('log')
    ax.set_xlabel('width of the model, which is how many features it has '
                  '(log scale)', fontsize=10)
    ax.set_ylabel('root-mean-square error', fontsize=10)
    ax.set_ylim(0, 2.4)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='lower left')
    _title(ax, 'Held-out error falls, then peaks where the model just fits the '
               'data, then falls past its old best')
    _save(fig, OVF_DOC, 'double-descent.svg')


def fig_interpolation_threshold() -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    _plain(ax)
    ax.plot(DD.ps, DD.e_tr, 'o-', color=LINK, lw=2.2, ms=5,
            label=f'error on the {DD.n} training examples')
    ax.plot(DD.ps, DD.e_te, 's-', color=GRIP, lw=1.6, ms=4, alpha=0.55,
            label='error on held-out examples, for comparison')
    ax.axvline(DD.n, color=MUTED, ls='--', lw=1.4)
    ax.annotate(f'training error first reaches 0 at width '
                f'{DD.ps[DD.zero_i]}, which is exactly the number of\n'
                f'training examples, and the held-out error peaks at '
                f'{DD.e_te[DD.peak_i]:.2f} right there',
                xy=(DD.n, 0.02), xytext=(2.2, 1.45), fontsize=9.3, color=INK,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.0))
    ax.set_xscale('log')
    ax.set_xlabel('width of the model (log scale)', fontsize=10)
    ax.set_ylabel('root-mean-square error', fontsize=10)
    ax.set_ylim(-0.08, 2.3)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='upper right')
    _title(ax, 'The peak sits exactly where the model gains just enough room to '
               'pass through every training point')
    _save(fig, OVF_DOC, 'interpolation-threshold.svg')


# ==========================================================================
# PAGE 2, SECTION 1: scaling the inputs
# ==========================================================================

class Scaling:
    """A two-feature regression, once in raw units and once standardised.

    Gradient descent on a squared-error loss is exact in the eigenbasis of the
    curvature matrix, so the loss at any step is worked out in closed form and
    checked against a real loop.
    """

    def __init__(self) -> None:
        rng = np.random.default_rng(31)
        self.n = 200
        self.reach_mm: Arr = rng.uniform(220.0, 640.0, self.n)
        self.height_m: Arr = rng.uniform(0.08, 0.62, self.n)
        self.y: Arr = (0.004 * self.reach_mm + 1.9 * self.height_m + 0.35
                       + rng.normal(0.0, 0.05, self.n))
        self.x_raw: Arr = np.column_stack([self.reach_mm, self.height_m,
                                          np.ones(self.n)])
        self.mu: Arr = self.x_raw[:, :2].mean(0)
        self.sd: Arr = self.x_raw[:, :2].std(0)
        self.x_std: Arr = np.column_stack([(self.x_raw[:, :2] - self.mu) / self.sd,
                                           np.ones(self.n)])
        self.raw = self._analyse(self.x_raw)
        self.std = self._analyse(self.x_std)
        self.target = 0.001
        self.raw_steps = self._steps_to(self.raw, self.target)
        self.std_steps = self._steps_to(self.std, self.target)
        self.check_raw_loop, self.check_raw_formula = self._check(self.x_raw,
                                                                 self.raw, 2000)

    def _analyse(self, m: Arr) -> dict[str, object]:
        hess = 2.0 / self.n * m.T @ m
        lam, vec = np.linalg.eigh(hess)
        w_opt, *_ = np.linalg.lstsq(m, self.y, rcond=None)
        loss_opt = float(np.mean((m @ w_opt - self.y) ** 2))
        e0 = vec.T @ (np.zeros(3) - w_opt)
        return {'lam': lam, 'vec': vec, 'w_opt': w_opt, 'loss_opt': loss_opt,
                'e0': e0, 'lr_max': float(2.0 / lam[-1]),
                'lr': float(1.9 / lam[-1]),
                'cond': float(lam[-1] / lam[0])}

    @staticmethod
    def excess(info: dict[str, object], t: Arr) -> Arr:
        lam = np.asarray(info['lam'])
        e0 = np.asarray(info['e0'])
        lr = float(info['lr'])
        decay = (1.0 - lr * lam) ** (2.0 * np.asarray(t, dtype=float)[:, None])
        return 0.5 * (decay * (lam * e0 ** 2)).sum(1)

    def _steps_to(self, info: dict[str, object], target: float) -> int:
        ts = np.unique(np.round(np.logspace(0, 9, 2000)).astype(np.int64))
        ex = self.excess(info, ts)
        return int(ts[int(np.argmax(ex < target))])

    def _check(self, m: Arr, info: dict[str, object], steps: int
               ) -> tuple[float, float]:
        w = np.zeros(3)
        lr = float(info['lr'])
        for _ in range(steps):
            r = m @ w - self.y
            w -= lr * (2.0 / self.n) * (m.T @ r)
        loop = float(np.mean((m @ w - self.y) ** 2) - float(info['loss_opt']))
        return loop, float(self.excess(info, np.array([steps]))[0])

    def weight_path(self, info: dict[str, object], ts: Arr) -> Arr:
        lam = np.asarray(info['lam'])
        vec = np.asarray(info['vec'])
        e0 = np.asarray(info['e0'])
        lr = float(info['lr'])
        w_opt = np.asarray(info['w_opt'])
        decay = (1.0 - lr * lam) ** np.asarray(ts, dtype=float)[:, None]
        return w_opt + (decay * e0) @ vec.T


SC = Scaling()


def fig_feature_ranges() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))
    sets = [('as measured', SC.x_raw[:, :2],
             ['reach (millimetres)', 'height (metres)']),
            ('after standardising', SC.x_std[:, :2],
             ['reach, standardised', 'height, standardised'])]
    for ax, (name, data, labels) in zip(axes, sets):
        _plain(ax)
        for i, lab in enumerate(labels):
            col = LINK if i == 0 else JOINT
            ax.scatter(data[:, i], np.full(SC.n, 1 - i) + np.random.default_rng(i)
                       .normal(0, 0.045, SC.n), s=9, color=col, alpha=0.55)
            ax.text(data[:, i].mean(), 1 - i + 0.26,
                    f'{lab}\nfrom {data[:, i].min():.3g} to '
                    f'{data[:, i].max():.3g}, spread '
                    f'{data[:, i].std():.3g}',
                    ha='center', fontsize=9.0, color=INK)
        ax.set_yticks([])
        ax.set_ylim(-0.75, 1.75)
        ax.set_xlabel('value of the feature', fontsize=10)
        ax.set_title(name, fontsize=11, color=INK)
        ax.grid(True, axis='x', color=GRID, lw=0.6)
        if name == 'as measured':
            ax.set_xscale('symlog', linthresh=0.1)
    fig.suptitle('Two features of the same reaching move, one about '
                 f'{SC.mu[0] / SC.mu[1]:,.0f} times bigger than the other '
                 'until both are standardised',
                 fontsize=11.5, weight='bold', color=INK, y=1.05)
    _save(fig, NRM_DOC, 'feature-ranges.svg')


def fig_steps_to_train() -> None:
    ts = np.unique(np.round(np.logspace(0, 8, 500)).astype(np.int64))
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    _plain(ax)
    ax.plot(ts, SC.excess(SC.raw, ts), color=GRIP, lw=2.2,
            label=f'as measured, learning rate {SC.raw["lr"]:.2g}')
    ax.plot(ts, SC.excess(SC.std, ts), color=LINK, lw=2.2,
            label=f'standardised, learning rate {SC.std["lr"]:.3g}')
    ax.axhline(SC.target, color=MUTED, ls=':', lw=1.4)
    ax.text(1.4, SC.target * 1.25,
            f'close enough: loss within {SC.target} of the best possible',
            fontsize=9.2, color=MUTED)
    for info, steps, col in ((SC.std, SC.std_steps, LINK),
                             (SC.raw, SC.raw_steps, GRIP)):
        ax.scatter([steps], [SC.target], s=130, facecolor='none',
                   edgecolor=col, linewidth=2.0, zorder=6)
        ax.annotate(f'{steps:,} steps', xy=(steps, SC.target),
                    xytext=(steps, SC.target * 40), fontsize=10, color=col,
                    ha='center',
                    arrowprops=dict(arrowstyle='->', color=col, lw=1.2))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('gradient descent step (log scale)', fontsize=10)
    ax.set_ylabel('loss above the best possible loss (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='upper right')
    _title(ax, f'Standardising the two features turns {SC.raw_steps:,} steps '
               f'into {SC.std_steps}')
    _save(fig, NRM_DOC, 'steps-to-train.svg')


def fig_weight_paths() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.1))
    sets = [('as measured', SC.raw, np.unique(np.round(
        np.logspace(0, 8, 400)).astype(np.int64)), GRIP),
            ('standardised', SC.std, np.arange(0, 41), LINK)]
    for ax, (name, info, ts, col) in zip(axes, sets):
        _plain(ax)
        path = SC.weight_path(info, ts)
        w_opt = np.asarray(info['w_opt'])
        for j, (lab, c) in enumerate((('weight on reach', LINK),
                                      ('weight on height', JOINT))):
            ax.plot(np.maximum(ts, 1), path[:, j] / w_opt[j], lw=2.2, color=c,
                    label=lab)
        ax.axhline(1.0, color=MUTED, ls='--', lw=1.3)
        ax.text(1.3, 1.06, 'the value that fits best', fontsize=9.0, color=MUTED)
        if name == 'as measured':
            ax.set_xscale('log')
            ax.set_xlabel('step (log scale)', fontsize=10)
        else:
            ax.set_xlabel('step', fontsize=10)
        ax.set_ylim(-0.12, 1.35)
        ax.set_ylabel('weight, as a fraction of its best value', fontsize=10)
        ax.set_title(name, fontsize=11, color=INK)
        ax.grid(True, color=GRID, lw=0.6, which='both')
        ax.legend(fontsize=9.2, loc='lower right')
    fig.suptitle('In raw units the weight on reach is right after a few hundred '
                 'steps while the weight on height is still near zero a million '
                 'steps later', fontsize=11.5, weight='bold', color=INK, y=1.04)
    _save(fig, NRM_DOC, 'weight-paths.svg')


def fig_largest_learning_rate() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    _plain(ax)
    names = ['as measured\n(millimetres and metres)', 'standardised\n(both)']
    vals = [SC.raw['lr_max'], SC.std['lr_max']]
    conds = [SC.raw['cond'], SC.std['cond']]
    bars = ax.bar(names, vals, color=[GRIP, LINK], width=0.45, edgecolor='white')
    for b, v, c in zip(bars, vals, conds):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.7,
                f'largest safe\nlearning rate\n{v:.3g}', ha='center',
                fontsize=10, color=INK, weight='bold')
        ax.text(b.get_x() + b.get_width() / 2, v * 0.33,
                f'curvature ratio\n{c:,.0f} to 1', ha='center',
                fontsize=9.3, color='white')
    ax.set_yscale('log')
    ax.set_ylim(1e-7, 20.0)
    ax.set_ylabel('learning rate (log scale)', fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.6, which='both')
    _title(ax, 'Raw units force a learning rate '
               f'{float(SC.std["lr_max"]) / float(SC.raw["lr_max"]):,.0f} times '
               'smaller than standardised units allow')
    _save(fig, NRM_DOC, 'largest-learning-rate.svg')


# ==========================================================================
# PAGE 2, SECTION 2: layer normalisation and RMS normalisation
# ==========================================================================

class Norms:
    """Layer normalisation and RMS normalisation on one real six-number vector."""

    def __init__(self) -> None:
        rng = np.random.default_rng(404)
        self.x: Arr = np.round(rng.normal(0.4, 1.6, 6), 2)
        self.eps = 1e-5
        self.gamma: Arr = np.array([1.20, 0.90, 1.00, 1.40, 0.80, 1.10])
        self.beta: Arr = np.array([0.10, 0.00, -0.20, 0.00, 0.30, 0.00])
        self.mean = float(self.x.mean())
        self.dev: Arr = self.x - self.mean
        self.sq: Arr = self.dev ** 2
        self.var = float(self.sq.mean())
        self.sd = float(np.sqrt(self.var + self.eps))
        self.ln: Arr = self.dev / self.sd
        self.ln_out: Arr = self.ln * self.gamma + self.beta
        self.ln_mean = float(self.ln.mean())
        self.ln_sd = float(self.ln.std())
        self.sq_raw: Arr = self.x ** 2
        self.ms = float(self.sq_raw.mean())
        self.rms = float(np.sqrt(self.ms + self.eps))
        self.rn: Arr = self.x / self.rms
        self.rn_out: Arr = self.rn * self.gamma
        self.rn_mean = float(self.rn.mean())
        self.rn_rms = float(np.sqrt(np.mean(self.rn ** 2)))
        self.diff: Arr = self.ln_out - self.rn_out
        self.max_diff = float(np.abs(self.diff).max())


NM = Norms()


def _number_rows(ax: Axes, rows: list[tuple[str, Arr, str]], note: str) -> None:
    _blank(ax)
    n = len(rows[0][1])
    for r, (name, vals, face) in enumerate(rows):
        y = -r * 0.95
        ax.text(-0.3, y + 0.33, name, ha='right', va='center', fontsize=9.6,
                color=INK)
        for i, v in enumerate(vals):
            ax.add_patch(mpatches.Rectangle((i * 1.3, y), 1.18, 0.66,
                                            facecolor=face, edgecolor=INK,
                                            linewidth=1.0))
            ax.text(i * 1.3 + 0.59, y + 0.33, f'{v:.3f}', ha='center',
                    va='center', fontsize=9.3, color=INK)
    for i in range(n):
        ax.text(i * 1.3 + 0.59, 0.88, f'no. {i + 1}', ha='center',
                fontsize=8.4, color=MUTED)
    ax.set_xlim(-7.6, n * 1.3 + 0.4)
    ax.set_ylim(-len(rows) * 0.95 - 0.7, 1.3)
    ax.text(-7.4, -len(rows) * 0.95 - 0.3, note, fontsize=9.5, color=MUTED,
            ha='left')


def fig_layer_norm_steps() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    _number_rows(ax, [
        ('the six numbers coming in', NM.x, 'white'),
        (f'take off the average, which is {NM.mean:.4f}', NM.dev, LINK_PALE),
        ('square each one', NM.sq, LINK_PALE),
        (f'divide by the spread, which is {NM.sd:.4f}', NM.ln, JOINT),
        ('multiply by the learned scale and add the learned shift',
         NM.ln_out, SLIDE)],
        f'average of the squares is {NM.var:.4f}, and the spread is the square '
        f'root of {NM.var:.4f} + {NM.eps:g}, which is {NM.sd:.4f}.  '
        f'The normalised numbers have average {NM.ln_mean:.4f} and spread '
        f'{NM.ln_sd:.4f}.')
    _title(ax, 'Layer normalisation, every step shown on one real vector of six '
               'numbers')
    _save(fig, NRM_DOC, 'layer-norm-steps.svg')


def fig_rms_norm_steps() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.3))
    _number_rows(ax, [
        ('the same six numbers coming in', NM.x, 'white'),
        ('square each one, with no average taken off first', NM.sq_raw,
         LINK_PALE),
        (f'divide by the root-mean-square, which is {NM.rms:.4f}', NM.rn, JOINT),
        ('multiply by the learned scale, with no shift', NM.rn_out, SLIDE)],
        f'average of the squares is {NM.ms:.4f}, and its square root, after '
        f'adding {NM.eps:g}, is {NM.rms:.4f}.  The result has '
        f'root-mean-square {NM.rn_rms:.4f} but average {NM.rn_mean:.4f}, which '
        f'is not zero.')
    _title(ax, 'Root-mean-square normalisation: the same vector, two steps fewer')
    _save(fig, NRM_DOC, 'rms-norm-steps.svg')


def fig_layer_vs_rms() -> None:
    idx = np.arange(6)
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    _plain(ax)
    ax.bar(idx - 0.19, NM.ln_out, width=0.36, color=LINK,
           label='layer normalisation')
    ax.bar(idx + 0.19, NM.rn_out, width=0.36, color=JOINT,
           label='root-mean-square normalisation')
    for i in idx:
        ax.text(i, max(NM.ln_out[i], NM.rn_out[i]) + 0.1,
                f'{NM.diff[i]:+.3f}', ha='center', fontsize=9.0, color=MUTED)
    ax.axhline(0.0, color=INK, lw=0.9)
    ax.set_xticks(idx)
    ax.set_xticklabels([f'no. {i + 1}' for i in idx])
    ax.set_ylabel('value after the normalisation', fontsize=10)
    ax.set_xlabel('the six numbers, with the difference printed above each pair',
                  fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.6)
    ax.legend(fontsize=9.5, loc='lower right')
    _title(ax, 'The two rules give answers that differ by at most '
               f'{NM.max_diff:.3f} on this vector')
    _save(fig, NRM_DOC, 'layer-norm-vs-rms-norm.svg')


class Batch:
    """A real 4 by 6 batch of activations, used for the batch-norm pictures."""

    def __init__(self) -> None:
        rng = np.random.default_rng(808)
        self.a: Arr = np.round(rng.normal(0.3, 1.2, (4, 6)), 2)
        self.row_mean = float(self.a[0].mean())
        self.row_sd = float(self.a[0].std())
        self.col_mean = float(self.a[:, 0].mean())
        self.col_sd = float(self.a[:, 0].std())
        self.eps = 1e-5
        rng2 = np.random.default_rng(909)
        self.other: Arr = np.round(rng2.normal(1.6, 1.2, (3, 6)), 2)
        self.batch_a: Arr = self.a
        self.batch_b: Arr = np.vstack([self.a[0:1], self.other])
        self.out_a = float((self.a[0, 0] - self.batch_a[:, 0].mean())
                           / np.sqrt(self.batch_a[:, 0].var() + self.eps))
        self.out_b = float((self.a[0, 0] - self.batch_b[:, 0].mean())
                           / np.sqrt(self.batch_b[:, 0].var() + self.eps))
        self.gap = self.out_a - self.out_b
        self.sizes = [2, 4, 8, 16, 32, 64, 128, 256]
        self.spread: list[float] = []
        pool_rng = np.random.default_rng(1212)
        for m in self.sizes:
            outs = []
            for _ in range(600):
                pool = pool_rng.normal(0.3, 1.2, m - 1)
                full = np.concatenate([[self.a[0, 0]], pool])
                outs.append((self.a[0, 0] - full.mean())
                            / np.sqrt(full.var() + self.eps))
            self.spread.append(float(np.std(outs)))
        run_mean, run_var = 0.0, 1.0
        shift_rng = np.random.default_rng(1313)
        for _ in range(400):
            b = shift_rng.normal(0.3, 1.2, 32)
            run_mean = 0.9 * run_mean + 0.1 * b.mean()
            run_var = 0.9 * run_var + 0.1 * b.var()
        self.run_mean, self.run_var = float(run_mean), float(run_var)
        self.shift = 1.4
        darker = shift_rng.normal(0.3 + self.shift, 1.2, 32)
        self.one = float(darker[0])
        self.with_running = float((self.one - self.run_mean)
                                  / np.sqrt(self.run_var + self.eps))
        self.with_batch = float((self.one - darker.mean())
                                / np.sqrt(darker.var() + self.eps))


BT = Batch()


def fig_which_numbers_averaged() -> None:
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    _blank(ax)
    for r in range(4):
        for c in range(6):
            face = 'white'
            if r == 0:
                face = LINK_PALE
            if c == 0:
                face = JOINT if r != 0 else SLIDE
            ax.add_patch(mpatches.Rectangle((c * 1.25, -r * 0.9), 1.14, 0.78,
                                            facecolor=face, edgecolor=INK,
                                            linewidth=1.0))
            ax.text(c * 1.25 + 0.57, -r * 0.9 + 0.39, f'{BT.a[r, c]:.2f}',
                    ha='center', va='center', fontsize=9.4, color=INK)
        ax.text(-0.25, -r * 0.9 + 0.39, f'example {r + 1}', ha='right',
                va='center', fontsize=9.4, color=INK)
    for c in range(6):
        ax.text(c * 1.25 + 0.57, 0.6, f'feature {c + 1}', ha='center',
                fontsize=8.6, color=MUTED, rotation=0)
    ax.annotate('', xy=(6 * 1.25 - 0.1, 0.39), xytext=(-0.05, 0.39),
                arrowprops=dict(arrowstyle='-', color=LINK, lw=3.0, alpha=0.35))
    ax.text(6 * 1.25 + 0.15, 0.39,
            f'layer normalisation averages\nacross one example: '
            f'average {BT.row_mean:.4f}, spread {BT.row_sd:.4f}',
            fontsize=9.4, color=LINK, va='center')
    ax.annotate('', xy=(0.57, -3 * 0.9), xytext=(0.57, 0.78),
                arrowprops=dict(arrowstyle='-', color=JOINT, lw=3.0, alpha=0.45))
    ax.text(0.57, -3 * 0.9 - 0.55,
            f'batch normalisation averages down one feature, across the other '
            f'examples:\naverage {BT.col_mean:.4f}, spread {BT.col_sd:.4f}',
            fontsize=9.4, color=INK, ha='left', va='top')
    ax.set_xlim(-2.6, 6 * 1.25 + 7.6)
    ax.set_ylim(-4.7, 1.1)
    _title(ax, 'The same batch of 4 examples and 6 features, averaged two '
               'different ways')
    _save(fig, NRM_DOC, 'which-numbers-averaged.svg')


# ==========================================================================
# PAGE 2, SECTION 3: why batch normalisation lost ground
# ==========================================================================

def fig_batch_depends_on_batch() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0))
    for ax, (name, batch, out) in zip(axes, (
            ('in a batch of quiet pictures', BT.batch_a, BT.out_a),
            ('in a batch of bright pictures', BT.batch_b, BT.out_b))):
        _blank(ax)
        col = batch[:, 0]
        for r, v in enumerate(col):
            face = SLIDE if r == 0 else LINK_PALE
            ax.add_patch(mpatches.Rectangle((0.0, -r * 0.9), 1.2, 0.78,
                                            facecolor=face, edgecolor=INK,
                                            linewidth=1.0))
            ax.text(0.6, -r * 0.9 + 0.39, f'{v:.2f}', ha='center', va='center',
                    fontsize=9.6, color='white' if r == 0 else INK)
            ax.text(1.35, -r * 0.9 + 0.39,
                    'our example' if r == 0 else f'other example {r}',
                    fontsize=9.0, va='center', color=INK if r == 0 else MUTED)
        ax.text(0.0, -len(col) * 0.9 - 0.1,
                f'average of this column {col.mean():.4f}\n'
                f'spread {col.std():.4f}\n'
                f'our example comes out as {out:+.4f}',
                fontsize=10, va='top', color=INK)
        ax.set_xlim(-0.3, 5.4)
        ax.set_ylim(-len(col) * 0.9 - 1.5, 1.0)
        ax.set_title(name, fontsize=11, color=INK)
    fig.suptitle('Batch normalisation gives the same example two different '
                 f'answers, {BT.out_a:+.4f} and {BT.out_b:+.4f}, a gap of '
                 f'{abs(BT.gap):.4f}',
                 fontsize=11.5, weight='bold', color=INK, y=1.04)
    _save(fig, NRM_DOC, 'batch-norm-depends-on-batch.svg')


def fig_batch_size_noise() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    _plain(ax)
    ax.plot(BT.sizes, BT.spread, 'o-', color=GRIP, lw=2.2, ms=6)
    for m, s in zip(BT.sizes, BT.spread):
        if m in (2, 8, 32, 256):
            ax.annotate(f'{s:.4f}', xy=(m, s), xytext=(0, 10),
                        textcoords='offset points', ha='center', fontsize=9.2,
                        color=INK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(BT.sizes)
    ax.set_xticklabels([str(m) for m in BT.sizes])
    ax.set_xlabel('how many examples are in the batch (log scale)', fontsize=10)
    ax.set_ylabel('spread of the answer for one fixed example (log scale)',
                  fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    _title(ax, 'With a batch of 2 the answer for one example wobbles by '
               f'{BT.spread[0]:.3f}; with 256 it wobbles by '
               f'{BT.spread[-1]:.3f}')
    _save(fig, NRM_DOC, 'batch-size-noise.svg')


def fig_train_and_predict_gap() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    _plain(ax)
    names = ['during training,\nusing this batch', 'at prediction time,\n'
             'using the stored averages']
    vals = [BT.with_batch, BT.with_running]
    bars = ax.bar(names, vals, color=[LINK, GRIP], width=0.45,
                  edgecolor='white')
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2,
                v + (0.07 if v >= 0 else -0.16), f'{v:+.4f}', ha='center',
                fontsize=12, color=INK, weight='bold')
    ax.axhline(0.0, color=INK, lw=0.9)
    ax.set_ylabel('the answer for the same single number', fontsize=10)
    ax.set_ylim(min(0, min(vals)) - 0.5, max(vals) + 0.55)
    ax.grid(True, axis='y', color=GRID, lw=0.6)
    ax.text(0.5, max(vals) + 0.33,
            f'stored average {BT.run_mean:.4f} and stored spread '
            f'{np.sqrt(BT.run_var):.4f} were learned on quiet pictures;\n'
            f'the room has got brighter by {BT.shift}, so the two routes now '
            f'disagree by {abs(BT.with_batch - BT.with_running):.4f}',
            ha='center', fontsize=9.2, color=MUTED)
    _title(ax, 'Batch normalisation changes rule between training and '
               'prediction, and the two answers part company')
    _save(fig, NRM_DOC, 'train-and-predict-gap.svg')


# ==========================================================================
# PAGE 2, SECTION 4: the residual stream, and where the normalisation sits
# ==========================================================================

def _rmsnorm(x: Arr, eps: float = 1e-6) -> tuple[Arr, Arr]:
    r = np.sqrt(np.mean(x ** 2, axis=-1, keepdims=True) + eps)
    return x / r, r


def _rmsnorm_back(x: Arr, r: Arr, g: Arr) -> Arr:
    d = x.shape[-1]
    return g / r - x * np.sum(g * x, axis=-1, keepdims=True) / (d * r ** 3)


class Stack:
    """A stack of residual blocks, with the normalisation before or after."""

    def __init__(self, d_in: int, d: int, hid: int, blocks: int,
                 pre: bool = True, seed: int = 0) -> None:
        r = np.random.default_rng(seed)
        self.pre, self.blocks, self.d = pre, blocks, d
        self.w_in = r.normal(0.0, 1.0 / np.sqrt(d_in), (d_in, d))
        self.w1 = [r.normal(0.0, 1.0 / np.sqrt(d), (d, hid)) for _ in range(blocks)]
        self.w2 = [r.normal(0.0, 1.0 / np.sqrt(hid), (hid, d)) for _ in range(blocks)]
        self.w_out = r.normal(0.0, 1.0 / np.sqrt(d), (d, 1))

    def params(self) -> list[Arr]:
        return [self.w_in] + self.w1 + self.w2 + [self.w_out]

    def forward(self, x_in: Arr) -> tuple[Arr, dict[str, object]]:
        x = x_in @ self.w_in
        cache: list[tuple[Arr, Arr, Arr, Arr]] = []
        stream: list[Arr] = [x.copy()]
        adds: list[Arr] = []
        for l in range(self.blocks):
            if self.pre:
                nx, r = _rmsnorm(x)
                h = np.maximum(0.0, nx @ self.w1[l])
                o = h @ self.w2[l]
                cache.append((x, nx, r, h))
                x = x + o
            else:
                h = np.maximum(0.0, x @ self.w1[l])
                o = h @ self.w2[l]
                u = x + o
                y, r = _rmsnorm(u)
                cache.append((x, u, r, h))
                x = y
            adds.append(o)
            stream.append(x.copy())
        out = (x @ self.w_out)[:, 0]
        return out, {'cache': cache, 'last': x, 'in': x_in,
                     'stream': stream, 'adds': adds}

    def backward(self, c: dict[str, object], d_out: Arr) -> list[Arr]:
        cache = c['cache']            # type: ignore[assignment]
        g_out = np.asarray(c['last']).T @ d_out[:, None]
        g = d_out[:, None] @ self.w_out.T
        g1: list[Arr] = [np.zeros(0)] * self.blocks
        g2: list[Arr] = [np.zeros(0)] * self.blocks
        self.grad_norms: list[float] = [float(np.sqrt(np.mean(g ** 2)))]
        for l in range(self.blocks - 1, -1, -1):
            x_in, mid, r, h = cache[l]          # type: ignore[index]
            if self.pre:
                g2[l] = h.T @ g
                ga = (g @ self.w2[l].T) * (h > 0)
                g1[l] = mid.T @ ga
                g = g + _rmsnorm_back(x_in, r, ga @ self.w1[l].T)
            else:
                gu = _rmsnorm_back(mid, r, g)
                g2[l] = h.T @ gu
                ga = (gu @ self.w2[l].T) * (h > 0)
                g1[l] = x_in.T @ ga
                g = gu + ga @ self.w1[l].T
            self.grad_norms.append(float(np.sqrt(np.mean(g ** 2))))
        g_in = np.asarray(c['in']).T @ g
        return [g_in] + g1 + g2 + [g_out]


class Residual:
    """Forward sizes, gradient sizes and a stability sweep for both placements."""

    d_in, d, hid, blocks = 8, 24, 48, 24
    deep = 48

    def __init__(self) -> None:
        rng = np.random.default_rng(3)
        self.n = 120
        self.x = rng.normal(0.0, 1.0, (self.n, self.d_in))
        beta = rng.normal(0.0, 1.0, self.d_in) / np.sqrt(self.d_in)
        self.y = np.tanh(self.x @ beta * 2.0) + 0.3 * self.x[:, 0] * self.x[:, 1]
        self.var_y = float(np.var(self.y))
        self.small_x = np.round(rng.normal(0.0, 1.0, (1, 4)), 2)
        self._one_block()
        self._through_depth()
        self._sweep()

    def _one_block(self) -> None:
        r = np.random.default_rng(55)
        w = np.round(r.normal(0.0, 0.7, (4, 4)), 2)
        x = self.small_x[0]
        self.ob_x = x
        self.ob_w = w
        nx, rr = _rmsnorm(x)
        self.ob_norm = nx
        self.ob_rms_in = float(np.ravel(rr)[0])
        self.ob_f_pre = np.maximum(0.0, nx) @ w
        self.ob_pre = x + self.ob_f_pre
        self.ob_f_post = np.maximum(0.0, x) @ w
        self.ob_sum_post = x + self.ob_f_post
        post, rp = _rmsnorm(self.ob_sum_post)
        self.ob_post = post
        self.ob_rms_sum = float(np.ravel(rp)[0])
        self.ob_gap = float(np.abs(self.ob_pre - self.ob_post).max())

    def _through_depth(self) -> None:
        xs = self.x[:64]
        self.fwd: dict[str, list[float]] = {}
        self.bwd: dict[str, list[float]] = {}
        for name, pre in (('pre-norm', True), ('post-norm', False)):
            s = Stack(self.d_in, self.d, self.hid, self.deep, pre=pre, seed=17)
            out, c = s.forward(xs)
            self.fwd[name] = [float(np.sqrt(np.mean(v ** 2)))
                              for v in c['stream']]          # type: ignore[index]
            if name == 'pre-norm':
                self.adds = [float(np.sqrt(np.mean(v ** 2)))
                             for v in c['adds']]             # type: ignore[index]
            s.backward(c, np.ones(len(xs)) / len(xs))
            self.bwd[name] = list(reversed(s.grad_norms))
        self.depths = [4, 8, 16, 24, 32, 48, 64]
        self.share: dict[str, list[float]] = {}
        for name, pre in (('pre-norm', True), ('post-norm', False)):
            out = []
            for blocks in self.depths:
                s = Stack(self.d_in, self.d, self.hid, blocks, pre=pre, seed=17)
                _, c = s.forward(xs)
                s.backward(c, np.ones(len(xs)) / len(xs))
                out.append(float(s.grad_norms[-1] / s.grad_norms[0]))
            self.share[name] = out

    def _train(self, pre: bool, lr: float, steps: int = 220,
               warmup: int = 0) -> Arr:
        s = Stack(self.d_in, self.d, self.hid, self.blocks, pre=pre, seed=0)
        p = s.params()
        m = [np.zeros_like(q) for q in p]
        v = [np.zeros_like(q) for q in p]
        loss = np.full(steps, np.nan)
        for step in range(1, steps + 1):
            out, c = s.forward(self.x)
            cur_loss = float(np.mean((out - self.y) ** 2))
            if not np.isfinite(cur_loss):
                break
            loss[step - 1] = cur_loss
            g = s.backward(c, 2.0 * (out - self.y) / self.n)
            rate = lr * min(1.0, step / warmup) if warmup else lr
            for i in range(len(p)):
                m[i] = 0.9 * m[i] + 0.1 * g[i]
                v[i] = 0.999 * v[i] + 0.001 * g[i] ** 2
                p[i] -= rate * (m[i] / (1 - 0.9 ** step)) / (
                    np.sqrt(v[i] / (1 - 0.999 ** step)) + 1e-8)
        return loss

    def _sweep(self) -> None:
        self.lrs = [0.001, 0.003, 0.01, 0.03]
        self.final: dict[str, list[float]] = {'pre-norm': [], 'post-norm': []}
        self.curves: dict[tuple[str, float], Arr] = {}
        for name, pre in (('pre-norm', True), ('post-norm', False)):
            for lr in self.lrs:
                curve = self._train(pre, lr)
                self.curves[(name, lr)] = curve
                self.final[name].append(float(np.nanmin(curve[-20:])))
        self.warm = self._train(False, 0.01, warmup=50)
        self.warm_final = float(np.nanmin(self.warm[-20:]))


RS = Residual()


def fig_residual_stream() -> None:
    show = 6
    fig, ax = plt.subplots(figsize=(11.2, 3.6))
    _blank(ax)
    for i in range(show + 1):
        _box(ax, i * 1.62, 0.0, 1.0, 0.62,
             f'{RS.fwd["pre-norm"][i]:.3f}', face=LINK_PALE)
        ax.text(i * 1.62 + 0.5, -0.3, f'after block {i}' if i else 'start',
                ha='center', fontsize=8.6, color=MUTED)
        if i < show:
            ax.annotate('', xy=(i * 1.62 + 1.56, 0.31),
                        xytext=(i * 1.62 + 1.02, 0.31),
                        arrowprops=dict(arrowstyle='->', color=INK, lw=1.3))
            ax.text(i * 1.62 + 1.29, 0.78, f'+ {RS.adds[i]:.3f}', ha='center',
                    fontsize=8.8, color=SLIDE)
    ax.text(0.0, 1.35, 'each block reads the stream, works out a small change, '
                       'and adds it back; nothing is ever overwritten',
            fontsize=9.6, color=MUTED)
    ax.set_xlim(-0.3, show * 1.62 + 1.4)
    ax.set_ylim(-0.9, 1.9)
    _title(ax, 'The residual stream as a running total: the size of the stream '
               'and the size of what each block adds')
    _save(fig, NRM_DOC, 'residual-stream.svg')


def fig_pre_and_post_order() -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 5.4))
    rows_pre = [('the stream coming in', RS.ob_x, 'white'),
                (f'normalised first (its size was {RS.ob_rms_in:.4f})',
                 RS.ob_norm, JOINT),
                ('what the block works out from the normalised copy',
                 RS.ob_f_pre, LINK_PALE),
                ('added back to the untouched stream', RS.ob_pre, SLIDE)]
    rows_post = [('the same stream coming in', RS.ob_x, 'white'),
                 ('what the block works out from the raw stream',
                  RS.ob_f_post, LINK_PALE),
                 (f'added, giving a stream of size {RS.ob_rms_sum:.4f}',
                  RS.ob_sum_post, LINK_PALE),
                 ('and then normalised, which rewrites the stream itself',
                  RS.ob_post, GRIP)]
    for ax, rows, name in zip(axes, (rows_pre, rows_post),
                              ('normalisation before the block (pre-norm)',
                               'normalisation after the add (post-norm)')):
        _number_rows(ax, rows, '')
        ax.set_title(name, fontsize=10.8, color=INK, weight='bold', pad=6)
    fig.suptitle('One block, one four-number stream, two placements: the '
                 f'outputs differ by up to {RS.ob_gap:.3f}',
                 fontsize=11.5, weight='bold', color=INK, y=1.02)
    _save(fig, NRM_DOC, 'pre-and-post-norm-order.svg')


def fig_stream_size_through_depth() -> None:
    depth = np.arange(RS.deep + 1)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    _plain(axes[0])
    axes[0].plot(depth, RS.fwd['pre-norm'], color=LINK, lw=2.2,
                 label='pre-norm')
    axes[0].plot(depth, RS.fwd['post-norm'], color=GRIP, lw=2.2,
                 label='post-norm')
    axes[0].annotate(f'{RS.fwd["pre-norm"][-1]:.3f} after {RS.deep} blocks',
                     xy=(RS.deep, RS.fwd['pre-norm'][-1]), xytext=(9, 5.4),
                     fontsize=9.4, color=LINK,
                     arrowprops=dict(arrowstyle='->', color=LINK, lw=1.1))
    axes[0].annotate(f'pinned at {RS.fwd["post-norm"][-1]:.3f}',
                     xy=(RS.deep * 0.6, RS.fwd['post-norm'][-1]),
                     xytext=(14, 2.1), fontsize=9.4, color=GRIP,
                     arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    axes[0].set_xlabel('block number', fontsize=10)
    axes[0].set_ylabel('size of the stream (root-mean-square)', fontsize=10)
    axes[0].grid(True, color=GRID, lw=0.6)
    axes[0].legend(fontsize=9.5, loc='upper left')
    axes[0].set_title('going forwards', fontsize=11, color=INK)
    _plain(axes[1])
    axes[1].plot(RS.depths, RS.share['pre-norm'], 'o-', color=LINK, lw=2.2,
                 ms=6, label='pre-norm')
    axes[1].plot(RS.depths, RS.share['post-norm'], 's-', color=GRIP, lw=2.2,
                 ms=6, label='post-norm')
    axes[1].axhline(1.0, color=MUTED, ls=':', lw=1.3)
    axes[1].annotate(f'{RS.share["pre-norm"][-1]:.2f} through '
                     f'{RS.depths[-1]} blocks',
                     xy=(RS.depths[-1], RS.share['pre-norm'][-1]),
                     xytext=(14, RS.share['pre-norm'][-1] * 0.8),
                     fontsize=9.4, color=LINK,
                     arrowprops=dict(arrowstyle='->', color=LINK, lw=1.1))
    axes[1].annotate(f'{RS.share["post-norm"][-1]:.3f}',
                     xy=(RS.depths[-1], RS.share['post-norm'][-1]),
                     xytext=(34, RS.share['post-norm'][-1] * 4.5),
                     fontsize=9.4, color=GRIP,
                     arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    axes[1].set_yscale('log')
    axes[1].set_xlabel('how many blocks the gradient has to travel through',
                       fontsize=10)
    axes[1].set_ylabel('gradient at the first block, divided by\n'
                       'the gradient at the last (log scale)', fontsize=10)
    axes[1].grid(True, color=GRID, lw=0.6, which='both')
    axes[1].legend(fontsize=9.5, loc='lower left')
    axes[1].set_title('coming backwards', fontsize=11, color=INK)
    fig.suptitle(f'A stack of {RS.deep} blocks at the start of training: '
                 'pre-norm lets the stream grow, post-norm holds it at 1',
                 fontsize=11.5, weight='bold', color=INK, y=1.03)
    _save(fig, NRM_DOC, 'stream-size-through-depth.svg')


def fig_learning_rate_stability() -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    _plain(ax)
    floor = 1e-6
    pre_v = [max(v, floor) for v in RS.final['pre-norm']]
    post_v = [max(v, floor) for v in RS.final['post-norm']]
    ax.plot(RS.lrs, pre_v, 'o-', color=LINK, lw=2.2, ms=7, label='pre-norm')
    ax.plot(RS.lrs, post_v, 's-', color=GRIP, lw=2.2, ms=7, label='post-norm')
    ax.set_ylim(floor * 0.5, 4.0)
    ax.axhline(RS.var_y, color=MUTED, ls=':', lw=1.4)
    ax.text(0.00105, RS.var_y * 1.25,
            f'predicting the average every time would score {RS.var_y:.4f}',
            fontsize=9.2, color=MUTED)
    warm_y = max(RS.warm_final, floor)
    ax.scatter([0.01], [warm_y], s=150, facecolor='none',
               edgecolor=SLIDE, linewidth=2.2, zorder=6)
    ax.annotate('post-norm with 50 steps of warmup,\nwhich lands back below '
                f'{max(RS.warm_final, 1e-6):.0e}',
                xy=(0.01, warm_y), xytext=(0.0012, 0.0009),
                fontsize=9.4, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(RS.lrs)
    ax.set_xticklabels([str(v) for v in RS.lrs])
    ax.set_xlabel('learning rate (log scale)', fontsize=10)
    ax.set_ylabel('loss after 300 steps (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.5, loc='center left')
    _title(ax, f'{RS.blocks} blocks trained at four learning rates: post-norm '
               'stops learning at 0.01, pre-norm does not')
    _save(fig, NRM_DOC, 'learning-rate-stability.svg')


# ==========================================================================
# PAGE 2, SECTION 5: mixed precision
# ==========================================================================

def to_bf16(x: Arr | np.float32) -> NDArray[np.float32]:
    """Round a float32 to bfloat16 by keeping its top 16 bits, to nearest even.

    NumPy has no bfloat16 type, so the rounding is done on the bit pattern,
    which gives exactly the numbers a bfloat16 register would hold.
    """
    a = np.asarray(x, dtype=np.float32).view(np.uint32).astype(np.uint64)
    b = ((a + 0x7FFF + ((a >> 16) & 1)) & 0xFFFF0000).astype(np.uint32)
    return b.view(np.float32)


class Precision:
    """Real facts about the three number formats, and real rounding of them."""

    def __init__(self) -> None:
        f32 = np.finfo(np.float32)
        f16 = np.finfo(np.float16)
        self.formats = [
            ('float32', 1, 8, 23, float(f32.max), float(f32.smallest_subnormal),
             float(f32.eps), 4),
            ('bfloat16', 1, 8, 7, float(to_bf16(np.float32(3.3895314e38))),
             2.0 ** -133, 2.0 ** -7, 2),
            ('float16', 1, 5, 10, float(f16.max), float(f16.smallest_subnormal),
             float(f16.eps), 2),
        ]
        rng = np.random.default_rng(42)
        self.grads = np.exp(rng.normal(np.log(2e-7), 2.1, 400000)).astype(np.float32)
        self.scale = 1024.0
        with np.errstate(over='ignore', under='ignore'):
            g16 = self.grads.astype(np.float16)
            gs16 = (self.grads * np.float32(self.scale)).astype(np.float16)
            gbf = to_bf16(self.grads)
        self.lost_f16 = float((g16 == 0).mean() * 100)
        self.lost_f16_scaled = float((gs16 == 0).mean() * 100)
        self.lost_bf16 = float((gbf == 0).mean() * 100)
        self.over_scaled = float(np.isinf(gs16).mean() * 100)
        self.median = float(np.median(self.grads))
        self.f16_floor = float(np.finfo(np.float16).smallest_subnormal)
        self.f16_tiny = float(np.finfo(np.float16).tiny)
        self.over_vals = [1e2, 1e3, 1e4, 6.55e4, 1e5, 1e6, 1e10, 1e38]
        self.over_f16: list[float] = []
        self.over_bf16: list[float] = []
        with np.errstate(over='ignore'):
            for v in self.over_vals:
                self.over_f16.append(float(np.float32(v).astype(np.float16)))
                self.over_bf16.append(float(to_bf16(np.float32(v))))
        self.f16_max = float(np.finfo(np.float16).max)
        self.bf16_max = float(to_bf16(np.float32(3.3895314e38)))
        # bytes held for every weight in the model, for one AdamW step
        self.pieces = [('the weights the arithmetic uses', 2, 4),
                       ('the master copy of the weights', 4, 0),
                       ('the gradients', 2, 4),
                       ('Adam\'s running average of the gradient', 4, 4),
                       ('Adam\'s running average of the squared gradient', 4, 4)]
        self.mixed_bytes = sum(p[1] for p in self.pieces)
        self.plain_bytes = sum(p[2] for p in self.pieces)
        self.act_tokens = 2048
        self.act_width = 4096
        self.act_f32 = self.act_tokens * self.act_width * 4 / 2 ** 20
        self.act_bf16 = self.act_tokens * self.act_width * 2 / 2 ** 20


PR = Precision()


def fig_number_formats() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.0))
    _blank(ax)
    unit = 0.26
    for r, (name, s, e, m, big, small, eps, by) in enumerate(PR.formats):
        y = -r * 1.15
        ax.text(-0.3, y + 0.3, f'{name}\n{by} bytes', ha='right', va='center',
                fontsize=9.8, color=INK, weight='bold')
        x = 0.0
        for width, col, lab in ((s, GRIP, 'sign'), (e, JOINT, f'{e} exponent bits'),
                                (m, LINK_PALE, f'{m} mantissa bits')):
            ax.add_patch(mpatches.Rectangle((x, y), width * unit, 0.6,
                                            facecolor=col, edgecolor=INK,
                                            linewidth=0.9))
            if width * unit > 0.5:
                ax.text(x + width * unit / 2, y + 0.3, lab, ha='center',
                        va='center', fontsize=8.6,
                        color='white' if col in (GRIP, JOINT) else INK)
            x += width * unit
        ax.text(24 * unit + 0.35, y + 0.3,
                f'largest {big:.3g}      smallest above zero {small:.2g}      '
                f'step above 1 is {eps:.3g}', fontsize=9.2, va='center',
                color=INK)
    ax.set_xlim(-3.4, 24 * unit + 7.6)
    ax.set_ylim(-3.0, 1.0)
    ax.text(0.0, 0.78, 'exponent bits set how far the format reaches; mantissa '
                       'bits set how fine its steps are',
            fontsize=9.5, color=MUTED)
    _title(ax, 'bfloat16 keeps float32\'s 8 exponent bits and spends the saving '
               'on precision, while float16 does the opposite')
    _save(fig, NRM_DOC, 'number-formats.svg')


def fig_what_stays_float32() -> None:
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    _plain(ax)
    names = [p[0] for p in PR.pieces]
    mixed = [p[1] for p in PR.pieces]
    plain = [p[2] if p[2] else p[1] for p in PR.pieces]
    ypos = np.arange(len(names))
    ax.barh(ypos + 0.18, plain, height=0.34, color=MUTED,
            label=f'everything in float32: {PR.plain_bytes} bytes a weight')
    ax.barh(ypos - 0.18, mixed, height=0.34, color=LINK,
            label=f'mixed precision: {PR.mixed_bytes} bytes a weight')
    for i, (m, p) in enumerate(zip(mixed, plain)):
        ax.text(m + 0.12, i - 0.18, f'{m}', va='center', fontsize=9.4,
                color=LINK, weight='bold')
        ax.text(p + 0.12, i + 0.18, f'{p}', va='center', fontsize=9.4,
                color=MUTED)
    ax.set_yticks(ypos)
    ax.set_yticklabels(names, fontsize=9.4)
    ax.invert_yaxis()
    ax.set_xlim(0, 5.6)
    ax.set_xlabel('bytes held for every weight in the model', fontsize=10)
    ax.grid(True, axis='x', color=GRID, lw=0.6)
    ax.legend(fontsize=9.4, loc='lower right')
    ax.text(5.5, 4.35,
            f'the saving is not here but in the activations: one layer\'s\n'
            f'{PR.act_tokens:,} rows of {PR.act_width:,} numbers take '
            f'{PR.act_f32:.0f} MB in float32\nand {PR.act_bf16:.0f} MB in '
            f'bfloat16, and the matrix multiplies run faster',
            fontsize=9.2, color=MUTED, ha='right', va='bottom')
    _title(ax, 'Mixed precision halves two pieces and adds a new one, so every '
               f'weight still costs {PR.mixed_bytes} bytes')
    _save(fig, NRM_DOC, 'what-stays-float32.svg')


def fig_loss_scale_underflow() -> None:
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    _plain(ax)
    bins = np.logspace(-11, -1, 70)
    ax.hist(PR.grads, bins=bins, color=LINK_PALE, edgecolor=LINK, lw=0.6,
            label='the gradient values')
    ax.hist(PR.grads * PR.scale, bins=bins, color=SLIDE, alpha=0.35,
            label=f'the same values multiplied by {PR.scale:.0f}')
    ax.axvline(PR.f16_floor, color=GRIP, lw=2.0)
    ax.text(PR.f16_floor * 1.4, 1.0e4,
            f'below {PR.f16_floor:.0g} a float16\nholds nothing but zero',
            fontsize=9.3, color=GRIP)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('size of one gradient value (log scale)', fontsize=10)
    ax.set_ylabel('how many of the 400,000 values (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.4, loc='upper left')
    _title(ax, f'In float16 {PR.lost_f16:.1f}% of these gradients round to zero; '
               f'after the loss scale {PR.lost_f16_scaled:.1f}% do, and in '
               f'bfloat16 {PR.lost_bf16:.1f}% do')
    _save(fig, NRM_DOC, 'loss-scale-underflow.svg')


def fig_overflow() -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    _plain(ax)
    xs = np.arange(len(PR.over_vals))
    ax.plot(xs, PR.over_vals, 'o--', color=MUTED, lw=1.4, ms=6,
            label='the value being stored')
    f16 = [v if np.isfinite(v) else np.nan for v in PR.over_f16]
    ax.plot(xs, f16, 's-', color=GRIP, lw=2.2, ms=7,
            label='what a float16 holds')
    ax.plot(xs, PR.over_bf16, '^-', color=LINK, lw=2.2, ms=7,
            label='what a bfloat16 holds')
    first = next(i for i, v in enumerate(PR.over_f16) if not np.isfinite(v))
    ax.axvline(first - 0.5, color=GRIP, ls=':', lw=1.5)
    ax.text(first - 0.4, 3e6,
            f'float16 runs out at {PR.f16_max:,.0f};\nevery bigger value '
            'becomes infinity,\nand one infinity makes every weight\nit touches '
            'not a number',
            fontsize=9.3, color=GRIP)
    ax.set_yscale('log')
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{v:.0e}' for v in PR.over_vals], fontsize=8.8)
    ax.set_xlabel('the value being stored', fontsize=10)
    ax.set_ylabel('the value actually held (log scale)', fontsize=10)
    ax.set_ylim(50, 1e40)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    ax.legend(fontsize=9.4, loc='lower right')
    _title(ax, f'bfloat16 reaches to {PR.bf16_max:.2g}, so a big activation '
               'never overflows it')
    _save(fig, NRM_DOC, 'overflow.svg')


# ==========================================================================
# PAGE 2, SECTION 6: loss spikes
# ==========================================================================

class Spike:
    """A simulated training run with one bad batch, and three responses."""

    floor = 1.60
    bad_step = 1400
    steps = 2600
    mult = 200.0

    def __init__(self) -> None:
        rng0 = np.random.default_rng(5)
        self.dim = 24
        self.lam = np.exp(np.linspace(np.log(0.02), np.log(2.0), self.dim))
        self.w0 = rng0.normal(0.0, 1.2, self.dim)
        self.base, self.base_g = self._run()
        self.clipped, self.clipped_g = self._run(clip=2.0)
        self.skipped, self.skipped_g = self._run(skip=True)
        self.before = float(self.base[self.bad_step - 5])
        win = self.base[self.bad_step - 1:]
        self.peak = float(win.max())
        self.peak_step = int(np.argmax(win)) + self.bad_step
        self.spike_grad = float(self.base_g[self.bad_step - 1])
        self.usual_grad = float(np.median(self.base_g[self.bad_step - 300:
                                                      self.bad_step - 1]))
        after = np.arange(self.peak_step, self.steps)
        back = after[self.base[after] < self.before]
        self.recover = int(back[0]) + 1 - self.peak_step if len(back) else None
        self.end_base = float(self.base[-1])
        self.end_clipped = float(self.clipped[-1])
        self.end_skipped = float(self.skipped[-1])
        self.clip_at = 2.0

    def _run(self, clip: float | None = None, skip: bool = False
             ) -> tuple[Arr, Arr]:
        rng = np.random.default_rng(5)
        w = self.w0.copy()
        m = np.zeros(self.dim)
        v = np.zeros(self.dim)
        loss = np.zeros(self.steps)
        gnorm = np.zeros(self.steps)
        for s in range(1, self.steps + 1):
            g = self.lam * w + rng.normal(0.0, 0.03, self.dim)
            if s == self.bad_step and not skip:
                g = g + rng.normal(0.0, 1.0, self.dim) * self.mult
            gnorm[s - 1] = float(np.linalg.norm(g))
            if clip is not None and gnorm[s - 1] > clip:
                g = g * (clip / gnorm[s - 1])
            m = 0.9 * m + 0.1 * g
            v = 0.999 * v + 0.001 * g ** 2
            w = w - 0.01 * (m / (1 - 0.9 ** s)) / (
                np.sqrt(v / (1 - 0.999 ** s)) + 1e-8)
            loss[s - 1] = self.floor + 0.5 * float(np.sum(self.lam * w ** 2))
        return loss, gnorm


SK = Spike()


def fig_loss_spike() -> None:
    steps = np.arange(1, SK.steps + 1)
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    _plain(ax)
    ax.plot(steps, SK.base, color=LINK, lw=1.8)
    ax.scatter([SK.peak_step], [SK.peak], s=140, facecolor='none',
               edgecolor=GRIP, linewidth=2.2, zorder=6)
    ax.annotate(f'peak {SK.peak:.4f} at step {SK.peak_step}',
                xy=(SK.peak_step, SK.peak), xytext=(1720, 2.5),
                fontsize=9.6, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.annotate(f'just before: {SK.before:.4f}',
                xy=(SK.bad_step - 5, SK.before), xytext=(420, 1.75),
                fontsize=9.6, color=INK,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    ax.annotate(f'still {SK.end_base:.4f} at step {SK.steps}, which the run had '
                f'already passed\nbefore the spike',
                xy=(SK.steps, SK.end_base), xytext=(560, 2.7),
                fontsize=9.6, color=INK,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.1))
    ax.axvline(SK.bad_step, color=MUTED, ls=':', lw=1.3)
    ax.text(SK.bad_step - 30, 3.4, 'one bad batch arrives here', fontsize=9.3,
            color=MUTED, ha='right')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('training loss', fontsize=10)
    ax.set_ylim(1.55, 3.9)
    ax.grid(True, color=GRID, lw=0.6)
    _title(ax, 'A loss spike: one batch out of 2,600 sends the loss from '
               f'{SK.before:.3f} up to {SK.peak:.3f}')
    _save(fig, NRM_DOC, 'loss-spike.svg')


def fig_gradient_norm_spike() -> None:
    steps = np.arange(1, SK.steps + 1)
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    _plain(ax)
    ax.plot(steps, SK.base_g, color=PURPLE, lw=1.2)
    ax.axhline(SK.clip_at, color=SLIDE, ls='--', lw=1.6)
    ax.text(60, SK.clip_at * 1.35,
            f'a clipping threshold of {SK.clip_at}, which is '
            f'{SK.clip_at / SK.usual_grad:.0f} times the usual size',
            fontsize=9.3, color=SLIDE)
    ax.annotate(f'{SK.spike_grad:,.0f}, which is '
                f'{SK.spike_grad / SK.usual_grad:,.0f} times the usual '
                f'{SK.usual_grad:.3f}',
                xy=(SK.bad_step, SK.spike_grad), xytext=(380, 300),
                fontsize=9.6, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('size of the whole gradient (log scale)', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6, which='both')
    _title(ax, 'The gradient size shows the trouble on the exact step it '
               'happens, one step before the loss does')
    _save(fig, NRM_DOC, 'gradient-norm-spike.svg')


def fig_what_to_do() -> None:
    steps = np.arange(1, SK.steps + 1)
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    _plain(ax)
    ax.plot(steps, SK.base, color=GRIP, lw=1.8,
            label=f'nothing done: {SK.end_base:.4f} at the end')
    ax.plot(steps, SK.clipped, color=LINK, lw=1.8,
            label=f'gradient clipped at {SK.clip_at}: '
                  f'{SK.end_clipped:.4f} at the end')
    ax.plot(steps, SK.skipped, color=SLIDE, lw=1.8, ls='--',
            label=f'go back to the last saved copy and skip that batch: '
                  f'{SK.end_skipped:.4f} at the end')
    ax.axvline(SK.bad_step, color=MUTED, ls=':', lw=1.3)
    ax.set_xlim(1200, SK.steps)
    ax.set_ylim(1.595, 2.05)
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('training loss', fontsize=10)
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(fontsize=9.3, loc='upper right')
    _title(ax, 'Two cheap responses remove the spike entirely; doing nothing '
               'costs real progress')
    _save(fig, NRM_DOC, 'what-to-do-about-a-spike.svg')


# ==========================================================================
# printing and running
# ==========================================================================

def report(net: NetRun, dec: Decay, ji: Jitter) -> None:
    p = '{:<46}{}'.format
    print('=' * 78)
    print('PAGE 1  overfitting-and-generalisation')
    print('=' * 78)
    print('--- section 1: polynomial fits to 12 noisy points')
    print(p('noise in the measurements', NOISE_SD))
    for i, d in enumerate(CV.degrees):
        print(f'  degree {d:2d}   training rmse {CV.e_tr[i]:8.4f}'
              f'   held-out rmse {CV.e_ho[i]:12.4f}')
    print(p('best held-out degree', f'{CV.best} '
            f'({CV.e_ho[CV.degrees.index(CV.best)]:.4f})'))
    print('--- section 1: the small network')
    print(p('weights and biases in the network', f'{dec.n_params:,}'))
    print(p('best held-out step', net.best))
    print(p('loss there (training, held-out)',
            f'{net.best_tr:.4f}, {net.best_ho:.4f}'))
    print(p('loss at step 8,000 (training, held-out)',
            f'{net.final_tr:.4f}, {net.final_ho:.4f}'))
    print(p('held-out loss got worse by a factor of',
            f'{net.final_ho / net.best_ho:.1f}'))
    print('--- section 2: the three-way split')
    print(p('examples', SP.n))
    print(p('training / validation / test',
            f'{SP.n_tr} / {SP.n_va} / {SP.n_te}'))
    print(p('degree chosen on validation', SP.chosen))
    print(p('its validation error', f'{SP.chosen_va:.4f}'))
    print(p('its test error', f'{SP.chosen_te:.4f}'))
    print('--- section 2: reusing the test set (20 trials each)')
    for k, m, h in zip(TR.ks, TR.measured, TR.honest):
        print(f'  best of {k:3d}:  shows {m * 100:5.1f}%   really '
              f'{h * 100:5.1f}%   (true rate {TR.p_true * 100:.0f}%)')
    print('--- section 3: leakage')
    print(p('frames', f'{FR.n} = {FR.n_scene} scenes x {FR.n_ep} episodes '
            f'x {FR.n_fr} frames'))
    print(p('distance to the next frame of the same episode',
            f'{FR.nn_gap:.4f}'))
    print(p('distance to the nearest frame of another episode',
            f'{FR.cross_gap:.4f}'))
    print(p('accuracy, random frame split', f'{FR.acc_frame * 100:.1f}%'))
    print(p('accuracy, episode split', f'{FR.acc_episode * 100:.1f}%'))
    print(p('accuracy, new scene split', f'{FR.acc_scene * 100:.1f}%'))
    print(p('accuracy of guessing', f'{FR.chance * 100:.1f}%'))
    print('--- section 4: dropout on one layer of 8 units')
    print(p('p', DP.p))
    print(p('activations', ' '.join(f'{v:.2f}' for v in DP.h)))
    print(p('mask', ' '.join('1' if k else '0' for k in DP.keep)))
    print(p('units dropped', DP.n_dropped))
    print(p('scale 1/(1-p)', f'{DP.scale:.4f}'))
    print(p('sum before / after mask / after scaling',
            f'{DP.sum_h:.4f} / {DP.sum_dropped:.4f} / {DP.sum_scaled:.4f}'))
    print(p('average sum over 40,000 masks, no scaling',
            f'{DP.mean_raw:.4f}'))
    print(p('average sum over 40,000 masks, with scaling',
            f'{DP.mean_scaled:.4f}'))
    print('--- section 4: weight decay')
    for wd, tr, ho, rw, mw in zip(dec.wds, dec.final_tr, dec.final_ho,
                                  dec.rms_w, dec.max_w):
        print(f'  decay {wd:6g}:  training {tr:7.4f}  held-out {ho:8.4f}'
              f'  weight rms {rw:.4f}  largest weight {mw:.3f}')
    print(p('best decay', f'{dec.best_wd} ({dec.final_ho[dec.best_i]:.4f})'))
    print('--- section 5: augmentation')
    for name, v in PIC.vals.items():
        print(f'  {name:<18} mean brightness {v["mean"]:.4f}   '
              f'centre column {v["centre"]:.2f}   lean {v["lean"]:+.2f}')
    for j, tr, ho in zip(ji.js, ji.final_tr, ji.final_ho):
        print(f'  jitter {j:4g}:  training {tr:7.4f}  held-out {ho:8.4f}')
    print(p('best jitter', f'{ji.best_j} ({ji.final_ho[ji.best_i]:.4f})'))
    print('--- section 6: double descent')
    for pp, a, b in zip(DD.ps, DD.e_tr, DD.e_te):
        print(f'  width {pp:5d}:  training {a:8.5f}  held-out {b:8.4f}')
    print(p('training examples', DD.n))
    print(p('best narrow width',
            f'{DD.ps[DD.classic_i]} ({DD.e_te[DD.classic_i]:.4f})'))
    print(p('worst width', f'{DD.ps[DD.peak_i]} ({DD.e_te[DD.peak_i]:.4f})'))
    print(p('first width with zero training error', DD.ps[DD.zero_i]))
    print(p('widest width', f'{DD.ps[-1]} ({DD.e_te[-1]:.4f})'))
    print()
    print('=' * 78)
    print('PAGE 2  normalisation-and-stability')
    print('=' * 78)
    print('--- section 1: scaling the inputs')
    print(p('reach, in millimetres',
            f'{SC.reach_mm.min():.1f} to {SC.reach_mm.max():.1f}, '
            f'spread {SC.reach_mm.std():.2f}'))
    print(p('height, in metres',
            f'{SC.height_m.min():.4f} to {SC.height_m.max():.4f}, '
            f'spread {SC.height_m.std():.4f}'))
    print(p('ratio of the two spreads',
            f'{SC.reach_mm.std() / SC.height_m.std():,.0f}'))
    for name, info in (('as measured', SC.raw), ('standardised', SC.std)):
        print(f'  {name}:')
        print('    ' + p('curvature, smallest to largest',
                         ' '.join(f'{v:.5g}' for v in np.asarray(info['lam']))))
        print('    ' + p('ratio of largest to smallest',
                         f'{float(info["cond"]):,.0f}'))
        print('    ' + p('largest safe learning rate',
                         f'{float(info["lr_max"]):.5g}'))
        print('    ' + p('best possible loss', f'{float(info["loss_opt"]):.6f}'))
    print(p('steps to get within 0.001, as measured', f'{SC.raw_steps:,}'))
    print(p('steps to get within 0.001, standardised', f'{SC.std_steps:,}'))
    print(p('check: loop at 2,000 steps gives',
            f'{SC.check_raw_loop:.6f}'))
    print(p('check: closed form at 2,000 steps gives',
            f'{SC.check_raw_formula:.6f}'))
    print('--- section 2: layer norm and RMS norm on one vector')
    print(p('the six numbers', ' '.join(f'{v:.2f}' for v in NM.x)))
    print(p('average', f'{NM.mean:.4f}'))
    print(p('average of the squared deviations', f'{NM.var:.4f}'))
    print(p('spread used to divide', f'{NM.sd:.4f}'))
    print(p('layer norm, before scale and shift',
            ' '.join(f'{v:.4f}' for v in NM.ln)))
    print(p('its average and spread', f'{NM.ln_mean:.4f}, {NM.ln_sd:.4f}'))
    print(p('layer norm output', ' '.join(f'{v:.4f}' for v in NM.ln_out)))
    print(p('average of the raw squares', f'{NM.ms:.4f}'))
    print(p('root-mean-square used to divide', f'{NM.rms:.4f}'))
    print(p('rms norm, before scale', ' '.join(f'{v:.4f}' for v in NM.rn)))
    print(p('its average and root-mean-square',
            f'{NM.rn_mean:.4f}, {NM.rn_rms:.4f}'))
    print(p('rms norm output', ' '.join(f'{v:.4f}' for v in NM.rn_out)))
    print(p('largest difference between the two', f'{NM.max_diff:.4f}'))
    print('--- section 3: batch normalisation')
    print(p('average along one example (layer norm)',
            f'{BT.row_mean:.4f}, spread {BT.row_sd:.4f}'))
    print(p('average down one feature (batch norm)',
            f'{BT.col_mean:.4f}, spread {BT.col_sd:.4f}'))
    print(p('the same number in batch A', f'{BT.out_a:+.4f}'))
    print(p('the same number in batch B', f'{BT.out_b:+.4f}'))
    print(p('gap', f'{abs(BT.gap):.4f}'))
    for m, s in zip(BT.sizes, BT.spread):
        print(f'  batch of {m:4d}: the answer for one example wobbles by {s:.4f}')
    print(p('stored average and spread',
            f'{BT.run_mean:.4f}, {np.sqrt(BT.run_var):.4f}'))
    print(p('brightness shift at prediction time', BT.shift))
    print(p('answer using the batch', f'{BT.with_batch:+.4f}'))
    print(p('answer using the stored averages', f'{BT.with_running:+.4f}'))
    print('--- section 4: the residual stream')
    print(p('stream size at blocks 0, 12, 24, 36, 48, pre-norm',
            ' '.join(f'{RS.fwd["pre-norm"][i]:.3f}' for i in (0, 12, 24, 36, 48))))
    print(p('stream size at the same blocks, post-norm',
            ' '.join(f'{RS.fwd["post-norm"][i]:.3f}' for i in (0, 12, 24, 36, 48))))
    print(p('what the first six blocks add, pre-norm',
            ' '.join(f'{v:.3f}' for v in RS.adds[:6])))
    print(p('gradient size at blocks 0 and 48, pre-norm',
            f'{RS.bwd["pre-norm"][0]:.5f} and {RS.bwd["pre-norm"][-1]:.5f}'))
    print(p('gradient size at blocks 0 and 48, post-norm',
            f'{RS.bwd["post-norm"][0]:.5f} and {RS.bwd["post-norm"][-1]:.5f}'))
    print(p('one block, stream in', ' '.join(f'{v:.2f}' for v in RS.ob_x)))
    print(p('pre-norm output', ' '.join(f'{v:.3f}' for v in RS.ob_pre)))
    print(p('post-norm output', ' '.join(f'{v:.3f}' for v in RS.ob_post)))
    print(p('largest difference', f'{RS.ob_gap:.4f}'))
    print(p('predicting the average would score', f'{RS.var_y:.4f}'))
    for name in ('pre-norm', 'post-norm'):
        for lr, v in zip(RS.lrs, RS.final[name]):
            print(f'  {name} at learning rate {lr:6g}: loss {v:.5f}')
    print(p('post-norm at 0.01 with 50 warmup steps', f'{RS.warm_final:.5f}'))
    print('--- section 5: mixed precision')
    for name, s, e, m, big, small, eps, by in PR.formats:
        print(f'  {name:<9} {by} bytes  {e} exponent bits  {m} mantissa bits  '
              f'largest {big:.4g}  smallest above zero {small:.3g}  '
              f'step above 1 {eps:.4g}')
    print(p('median gradient value', f'{PR.median:.3g}'))
    print(p('rounded to zero in float16', f'{PR.lost_f16:.2f}%'))
    print(p(f'rounded to zero after multiplying by {PR.scale:.0f}',
            f'{PR.lost_f16_scaled:.2f}%'))
    print(p('and overflowed after the multiply',
            f'{PR.over_scaled:.3f}%'))
    print(p('rounded to zero in bfloat16', f'{PR.lost_bf16:.2f}%'))
    for v, a, b in zip(PR.over_vals, PR.over_f16, PR.over_bf16):
        print(f'  storing {v:9.3g}:  float16 gives {a:<12.6g} '
              f'bfloat16 gives {b:.6g}')
    print(p('bytes a weight, all float32', PR.plain_bytes))
    print(p('bytes a weight, mixed precision', PR.mixed_bytes))
    print(p(f'activations for {PR.act_tokens:,} tokens of width '
            f'{PR.act_width:,}, float32', f'{PR.act_f32:.1f} MB'))
    print(p('the same in bfloat16', f'{PR.act_bf16:.1f} MB'))
    print('--- section 6: the loss spike')
    print(p('loss just before the bad batch', f'{SK.before:.4f}'))
    print(p('peak loss and the step it happened',
            f'{SK.peak:.4f} at {SK.peak_step}'))
    print(p('usual gradient size', f'{SK.usual_grad:.4f}'))
    print(p('gradient size on the bad step', f'{SK.spike_grad:,.1f}'))
    print(p('that is bigger by a factor of',
            f'{SK.spike_grad / SK.usual_grad:,.0f}'))
    print(p('steps to get back below where it was', SK.recover))
    print(p('loss at step 2,600, nothing done', f'{SK.end_base:.4f}'))
    print(p('loss at step 2,600, gradient clipped', f'{SK.end_clipped:.4f}'))
    print(p('loss at step 2,600, batch skipped', f'{SK.end_skipped:.4f}'))


def main() -> None:
    net = NetRun()
    dec = Decay()
    ji = Jitter()

    fig_poly_fits(net)
    fig_error_vs_degree()
    fig_net_curves(net)
    fig_net_curve_shape(net)
    fig_three_way_split()
    fig_choosing_on_validation()
    fig_reusing_the_test_set()
    fig_frame_split_strip()
    fig_split_kinds_score()
    fig_episodes_by_scene()
    fig_early_stopping(net)
    fig_dropout_one_layer()
    fig_dropout_average()
    fig_weight_sizes(dec)
    fig_weight_decay_sweep(dec)
    fig_safe_augmentations()
    fig_flip_handed_tool()
    fig_jitter_sweep(ji)
    fig_classical_picture()
    fig_double_descent()
    fig_interpolation_threshold()

    fig_feature_ranges()
    fig_steps_to_train()
    fig_weight_paths()
    fig_largest_learning_rate()
    fig_layer_norm_steps()
    fig_rms_norm_steps()
    fig_layer_vs_rms()
    fig_which_numbers_averaged()
    fig_batch_depends_on_batch()
    fig_batch_size_noise()
    fig_train_and_predict_gap()
    fig_residual_stream()
    fig_pre_and_post_order()
    fig_stream_size_through_depth()
    fig_learning_rate_stability()
    fig_number_formats()
    fig_what_stays_float32()
    fig_loss_scale_underflow()
    fig_overflow()
    fig_loss_spike()
    fig_gradient_norm_spike()
    fig_what_to_do()

    report(net, dec, ji)


if __name__ == '__main__':
    if '--png' in sys.argv:
        PNG_DIR = pathlib.Path(sys.argv[sys.argv.index('--png') + 1])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    main()
