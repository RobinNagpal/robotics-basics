"""Generate the diagrams for docs/06_learned-models/10_making-models-work-on-an-arm/.

It also draws the two pictures for the section "A learned model inside MPC" of
docs/05_programming-techniques/06_planning-and-search/03_also-used/
02_sampling-based-optimisation-and-mpc.md, because that section is about a
learned model and uses the same kind of code.

The pictures go to folders named after their documents, under docs/images/:

    03_evaluation-and-failure.md        -> making-models-work-on-an-arm/evaluation-and-failure/
    02_sampling-based-optimisation-...  -> planning-and-search/sampling-based-optimisation-and-mpc/

Run with:  pixi run python ../docs/diagrams/making_models_work.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file (the confidence
intervals, the chance of a clean trial, the counts in the example failure log,
the learned push model and the MPC runs), and the script prints them so the
documents can quote the same values. It needs only numpy and matplotlib.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
PURPLE: str = '#8e5bb5'
PALE_GREY: str = '#eeeeee'

EVAL: str = 'making-models-work-on-an-arm/evaluation-and-failure'
SOM: str = 'planning-and-search/sampling-based-optimisation-and-mpc'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _plain_axes(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK, labelsize=10)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str, face: str = LINK_PALE,
         edge: str = LINK, size: float = 10.5, weight: str = 'normal') -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                facecolor=face, edgecolor=edge, lw=1.5, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, fontsize=size, ha='center', va='center', color=INK,
            weight=weight, zorder=4)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, text: str = '', tx: float = 0.0, ty: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=14, color=color, lw=lw,
                                 zorder=2))
    if text:
        ax.text((a[0] + b[0]) / 2 + tx, (a[1] + b[1]) / 2 + ty, text, fontsize=9.5, color=MUTED,
                ha='center', va='center', zorder=5,
                bbox=dict(facecolor='white', edgecolor='none', pad=1.0))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder.split("/")[-1]}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# ==========================================================================
# 03_evaluation-and-failure.md
# ==========================================================================

def _binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p), summed in log space so large n does not overflow."""
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    total = 0.0
    for i in range(k + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                          + i * lp + (n - i) * lq)
    return min(total, 1.0)


def clopper_pearson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """The exact (Clopper-Pearson) confidence interval for k successes in n trials.

    The lower end is the success rate at which seeing k or more successes would
    happen only (1 - level) / 2 of the time; the upper end is the rate at which
    seeing k or fewer would happen only that often. Both are found by halving.
    """
    a = (1.0 - level) / 2.0

    def solve(f, lo: float, hi: float) -> float:
        for _ in range(80):
            mid = (lo + hi) / 2
            if f(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2

    lower = 0.0 if k == 0 else solve(lambda p: 1.0 - _binom_cdf(k - 1, n, p) >= a, 0.0, 1.0)
    upper = 1.0 if k == n else solve(lambda p: _binom_cdf(k, n, p) <= a, 0.0, 1.0)
    return lower, upper


# The trial counts the page uses. All show a 90% success rate, except the
# comparison pairs and the no-failure case.
SAME_RATE: list[tuple[int, int]] = [(9, 10), (18, 20), (45, 50), (90, 100), (180, 200), (450, 500)]
PAIRS: list[tuple[tuple[int, int], tuple[int, int]]] = [((18, 20), (15, 20)), ((90, 100), (75, 100))]


def intervals_picture() -> None:
    """Left: one 90% rate, measured with more and more trials. Right: two methods, 20 and 100 trials."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    _plain_axes(ax)
    for i, (k, n) in enumerate(SAME_RATE):
        lo, hi = clopper_pearson(k, n)
        y = len(SAME_RATE) - 1 - i
        ax.plot([lo * 100, hi * 100], [y, y], color=LINK, lw=5, solid_capstyle='butt', zorder=2)
        ax.plot([k / n * 100], [y], 'o', color=INK, ms=7, zorder=3)
        ax.text(hi * 100 + 1.0, y, f'{lo * 100:.1f}% to {hi * 100:.1f}%', fontsize=10, color=INK,
                va='center')
    ax.set_yticks(range(len(SAME_RATE)))
    ax.set_yticklabels([f'{k} of {n}' for k, n in reversed(SAME_RATE)], fontsize=10.5)
    ax.set_xlim(50, 112)
    ax.set_xticks([50, 60, 70, 80, 90, 100])
    ax.set_xticklabels(['50%', '60%', '70%', '80%', '90%', '100%'])
    ax.axvline(90, color=GRID, lw=1, zorder=1)
    ax.set_xlabel('true success rate (95% confidence interval)', fontsize=11, color=INK)
    ax.set_title('Every row scored 90%.\nMore trials, a narrower range', fontsize=12, color=INK,
                 weight='bold')

    ax = axes[1]
    _plain_axes(ax)
    cols = [SLIDE, WRIST]
    names = ['new model', 'old method']
    ys = [3.2, 2.6, 0.8, 0.2]
    j = 0
    for (a, b) in PAIRS:
        for c, (k, n) in enumerate((a, b)):
            lo, hi = clopper_pearson(k, n)
            y = ys[j]
            ax.plot([lo * 100, hi * 100], [y, y], color=cols[c], lw=5, solid_capstyle='butt')
            ax.plot([k / n * 100], [y], 'o', color=INK, ms=7, zorder=3)
            ax.text(21, y, f'{names[c]}: {k} of {n}', fontsize=10, color=cols[c], va='center',
                    weight='bold')
            j += 1
    ax.text(60, 3.75, 'the two ranges overlap a lot:\n20 trials each cannot tell them apart',
            fontsize=10, color=INK, ha='center', va='bottom')
    ax.text(60, 1.35, 'the two ranges only just overlap:\n100 trials each nearly separate them',
            fontsize=10, color=INK, ha='center', va='bottom')
    ax.set_xlim(20, 100)
    ax.set_ylim(-0.3, 4.6)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xticks([50, 60, 70, 80, 90, 100])
    ax.set_xticklabels(['50%', '60%', '70%', '80%', '90%', '100%'])
    ax.set_xlabel('true success rate (95% confidence interval)', fontsize=11, color=INK)
    ax.set_title('Is the new model better?\nThe same gap, with 20 and 100 trials', fontsize=12,
                 color=INK, weight='bold')
    fig.tight_layout(w_pad=3)
    _save(fig, EVAL, 'trials-and-intervals.svg')


STEP_RIGHT: list[float] = [0.99, 0.995, 0.999]
STEPS_SHOWN: list[int] = [10, 50, 100, 200]


def compounding_picture() -> None:
    """If each step is right with chance p and any one wrong step spoils the trial,
    a whole trial of N steps is clean with chance p ** N."""
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain_axes(ax)
    n = np.arange(1, 301)
    cols = [GRIP, JOINT, SLIDE]
    for p, c in zip(STEP_RIGHT, cols):
        ax.plot(n, 100 * p ** n, color=c, lw=2.6)
        ax.text(302, 100 * p ** 300, f'each step right\n{p * 100:.1f}% of the time', fontsize=10,
                color=c, va='center', weight='bold')
    for N in (50, 200):
        ax.axvline(N, color=GRID, lw=1, zorder=0)
    ax.plot([50], [100 * 0.99 ** 50], 'o', color=INK, ms=6, zorder=4)
    ax.text(54, 100 * 0.99 ** 50 + 2, f'{100 * 0.99 ** 50:.0f}% of trials clean', fontsize=10,
            color=INK, va='bottom')
    ax.plot([200], [100 * 0.999 ** 200], 'o', color=INK, ms=6, zorder=4)
    ax.text(204, 100 * 0.999 ** 200 + 2, f'{100 * 0.999 ** 200:.0f}%', fontsize=10, color=INK,
            va='bottom')
    ax.text(53, 3, '50 steps:\n5 s at 10 a second', fontsize=9.5, color=MUTED, ha='left',
            va='bottom')
    ax.text(203, 52, '200 steps:\n20 s at 10 a second', fontsize=9.5, color=MUTED, ha='left',
            va='bottom')
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 102)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
    ax.set_xlabel('steps in one trial', fontsize=11, color=INK)
    ax.set_ylabel('trials with no wrong step', fontsize=11, color=INK)
    ax.set_title('A small mistake rate per step becomes a large one per trial',
                 fontsize=12, color=INK, weight='bold')
    fig.tight_layout()
    _save(fig, EVAL, 'steps-and-trials.svg')


# A made-up log of 100 real trials of a mug-picking model, sorted into kinds.
# The counts are an example, chosen to be typical in shape, not measured.
FAILURE_LOG: list[tuple[str, int, str]] = [
    ('mug slipped out while lifting', 5, 'grasp'),
    ('reached for the wrong spot', 2, 'seeing'),
    ('stopped moving, ran out of time', 1, 'policy'),
    ('touched the rack, safety stop', 1, 'safety'),
    ('person had to step in', 1, 'other'),
]
TRIALS: int = 100


def failure_kinds_picture() -> None:
    """The failures from 100 example trials, largest kind first, with a running total."""
    names = [f[0] for f in FAILURE_LOG]
    counts = np.array([f[1] for f in FAILURE_LOG])
    total_fail = int(counts.sum())
    run = np.cumsum(counts) / total_fail * 100
    fig, ax = plt.subplots(figsize=(11, 5.0), facecolor='white')
    _plain_axes(ax)
    y = np.arange(len(names))[::-1]
    cols = [GRIP, WRIST, JOINT, PURPLE, MUTED]
    ax.barh(y, counts, color=cols, height=0.6, zorder=2)
    for yi, c, r in zip(y, counts, run):
        ax.text(c + 0.15, yi, f'{c}      running total: {r:.0f}% of the failures', fontsize=10,
                color=INK, va='center')
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10.5)
    ax.set_xlim(0, 9)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_xlabel('trials that ended this way', fontsize=11, color=INK)
    ax.set_title(f'{TRIALS} trials, {TRIALS - total_fail} successes, {total_fail} failures, '
                 'sorted by kind (an example log)', fontsize=12, color=INK, weight='bold')
    fig.tight_layout()
    _save(fig, EVAL, 'failure-kinds.svg')


def on_failure_picture() -> None:
    """What the arm does when a trial goes wrong: stop first, then look again, retry,
    hand the job to a written method, or ask a person."""
    fig, ax = plt.subplots(figsize=(13.5, 6.8), facecolor='white')
    _axes(ax, (0, 13.5), (0, 6.8))
    red_face, green_face, amber_face = '#f7d4d4', '#d5ecd9', '#fbe8c2'
    _box(ax, 0.2, 2.95, 2.2, 0.9, 'a check says\nsomething is wrong', PALE_GREY, MUTED)
    _box(ax, 3.0, 2.95, 2.2, 0.9, 'is anyone or\nanything at risk?', PALE_GREY, MUTED)
    _box(ax, 2.7, 0.55, 2.8, 0.9, 'STOP\nand wait for a person', red_face, GRIP)
    _box(ax, 5.9, 2.95, 2.2, 0.9, 'which kind of\nfailure is it?', PALE_GREY, MUTED)
    rows = [(5.25, 'if it is unsure what it sees:', 'LOOK AGAIN', 'from a new angle, then ask again',
             green_face, SLIDE),
            (3.85, 'if the grasp slipped or missed:', 'RETRY', 'the same step, at most twice',
             green_face, SLIDE),
            (2.45, 'if the same step failed twice:', 'HAND BACK', 'to the written method',
             amber_face, JOINT),
            (1.05, 'if it is none of these:', 'ASK A PERSON', 'and log it for retraining',
             amber_face, JOINT)]
    for y, cond, act, how, face, edge in rows:
        ax.add_patch(FancyBboxPatch((9.0, y), 4.3, 1.05,
                                    boxstyle='round,pad=0.02,rounding_size=0.12',
                                    facecolor=face, edgecolor=edge, lw=1.5, zorder=3))
        ax.text(11.15, y + 0.8, cond, fontsize=9.5, color=MUTED, ha='center', va='center', zorder=4)
        ax.text(11.15, y + 0.5, act, fontsize=10.5, color=INK, ha='center', va='center',
                weight='bold', zorder=4)
        ax.text(11.15, y + 0.22, how, fontsize=10, color=INK, ha='center', va='center', zorder=4)
        _arrow(ax, (8.1, 3.4), (9.0, y + 0.52))
    _arrow(ax, (2.4, 3.4), (3.0, 3.4))
    _arrow(ax, (4.1, 2.95), (4.1, 1.45), GRIP, text='yes', tx=0.3)
    _arrow(ax, (5.2, 3.4), (5.9, 3.4), text='no', ty=0.25)
    ax.text(6.75, 6.6, 'What the arm does when something goes wrong', fontsize=13, color=INK,
            weight='bold', ha='center')
    ax.text(0.2, 0.15, 'Red comes first, always. Green: the model tries again. '
            'Amber: the model is taken off this job.', fontsize=10, color=MUTED)
    _save(fig, EVAL, 'what-to-do-on-failure.svg')


def print_eval_numbers() -> None:
    print('--- evaluation and failure')
    for k, n in SAME_RATE + [(20, 25), (19, 25), (15, 20), (75, 100), (85, 100), (0, 20), (20, 20),
                             (0, 100), (100, 100), (0, 300)]:
        lo, hi = clopper_pearson(k, n)
        print(f'{k:3d} of {n:3d} = {k / n * 100:5.1f}%   95% interval {lo * 100:5.1f}% to {hi * 100:5.1f}%')
    for n in (20, 100, 300):
        print(f'rule of three, 0 failures in {n}: failure rate up to about {300 / n:.1f}%')
    for p in STEP_RIGHT:
        print(f'step right {p}: ' + ', '.join(f'{N} steps -> {100 * p ** N:.1f}%' for N in STEPS_SHOWN))
    counts = [f[1] for f in FAILURE_LOG]
    print('failure log:', FAILURE_LOG, 'total failures', sum(counts),
          'successes', TRIALS - sum(counts))


# ==========================================================================
# 02_sampling-based-optimisation-and-mpc.md: a learned model inside MPC
# ==========================================================================

# The same pushing task as planning_and_search_4.py, in centimetres, seen from above.
P_START: np.ndarray = np.array([0.0, 0.0])
P_TARGET: np.ndarray = np.array([20.0, 4.0])
MUG: tuple[float, float, float] = (10.0, 2.0, 5.0)     # centre x, y, and the block's keep-out radius
MAX_PUSH: float = 5.0
MODEL: tuple[float, float] = (0.8, 0.15)      # the hand-written push model: slide, drift
REAL: tuple[float, float] = (0.65, 0.30)      # the real block
REAL_NOISE: float = 0.15                      # cm of random scatter on every real push
RECORD_MAX: float = 3.0                       # the recorded random pushes are at most 3 cm long
N_RECORDS: int = 200
N_MEMBERS: int = 5
HIDDEN: int = 16
EXTRA_DRIFT: float = 0.3                      # extra drift per cm of push beyond 3 cm
UNSURE_WEIGHT: float = 0.5                    # cost per cm of disagreement between members


def clip_push(u: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(u, axis=-1, keepdims=True)
    return u * np.minimum(1.0, MAX_PUSH / np.maximum(n, 1e-12))


def real_move(u: np.ndarray) -> np.ndarray:
    """How far the real block moves for push u, without the random scatter. The planner
    never sees this. The block slides 0.65 times as far as the pusher and drifts 0.30
    times the push length to the left. A push longer than 3 cm also starts to turn it,
    so it drifts a further 0.3 cm per cm of push beyond 3 cm. The recorded pushes are
    all 3 cm or shorter, so the records never show this part."""
    u = clip_push(u)
    L = np.linalg.norm(u, axis=-1, keepdims=True)
    left = np.stack([-u[..., 1], u[..., 0]], -1)
    return REAL[0] * u + (REAL[1] + EXTRA_DRIFT * np.clip(L - RECORD_MAX, 0, None)) * left


def real_push(p: np.ndarray, u: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One push of the real block: the move above plus a little random scatter."""
    return p + real_move(u) + rng.normal(0, REAL_NOISE, p.shape)


def written_push(p: np.ndarray, u: np.ndarray) -> np.ndarray:
    u = clip_push(u)
    left = np.stack([-u[..., 1], u[..., 0]], -1)
    return p + MODEL[0] * u + MODEL[1] * left


class Ensemble:
    """Five small neural networks. Each takes a push (2 numbers) and predicts how far
    the block moves (2 numbers). Each is trained on its own resampled copy of the
    records, from its own random starting numbers, so they agree where the records are
    dense and disagree where there are none."""

    def __init__(self, X: np.ndarray, Y: np.ndarray, seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        self.members = []
        self.train_err = []
        for _ in range(N_MEMBERS):
            idx = rng.integers(0, len(X), len(X))
            W = self._train(X[idx], Y[idx], rng)
            self.members.append(W)
            self.train_err.append(float(np.mean(np.linalg.norm(self._one(W, X) - Y, axis=1))))

    @staticmethod
    def _one(W: tuple, X: np.ndarray) -> np.ndarray:
        W1, b1, W2, b2 = W
        return np.tanh(X / 3.0 @ W1 + b1) @ W2 + b2

    @staticmethod
    def _train(X: np.ndarray, Y: np.ndarray, rng: np.random.Generator, steps: int = 3000,
               lr: float = 0.01) -> tuple:
        W = [rng.normal(0, 1.0, (2, HIDDEN)), np.zeros(HIDDEN), rng.normal(0, 0.3, (HIDDEN, 2)),
             np.zeros(2)]
        m = [np.zeros_like(w) for w in W]
        v = [np.zeros_like(w) for w in W]
        Xs = X / 3.0
        for t in range(1, steps + 1):
            H = np.tanh(Xs @ W[0] + W[1])
            out = H @ W[2] + W[3]
            g_out = 2 * (out - Y) / len(X)
            g = [None, None, H.T @ g_out, g_out.sum(0)]
            gH = g_out @ W[2].T * (1 - H ** 2)
            g[0] = Xs.T @ gH
            g[1] = gH.sum(0)
            for i in range(4):          # the Adam update
                m[i] = 0.9 * m[i] + 0.1 * g[i]
                v[i] = 0.999 * v[i] + 0.001 * g[i] ** 2
                W[i] = W[i] - lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
        return tuple(W)

    def predict_all(self, U: np.ndarray) -> np.ndarray:
        """Each member's predicted move, shape (members, ..., 2)."""
        flat = clip_push(U).reshape(-1, 2)
        return np.stack([self._one(W, flat).reshape(U.shape) for W in self.members])


def record_pushes(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Random play: 200 random pushes, each at most 3 cm long, and how far the block moved."""
    ang = rng.uniform(0, 2 * np.pi, N_RECORDS)
    length = RECORD_MAX * np.sqrt(rng.uniform(0, 1, N_RECORDS))
    U = np.stack([length * np.cos(ang), length * np.sin(ang)], 1)
    moved = real_push(np.zeros((N_RECORDS, 2)), U, rng)
    return U, moved


def _seg_hits_mug(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    c = np.array(MUG[:2])
    ab = b - a
    denom = np.maximum((ab * ab).sum(-1), 1e-12)
    t = np.clip(((c - a) * ab).sum(-1) / denom, 0, 1)
    closest = a + t[..., None] * ab
    return np.linalg.norm(closest - c, axis=-1) < MUG[2]


def mpc_cost(P: np.ndarray, spread: np.ndarray | None) -> np.ndarray:
    """The same score as the Book 5 page's MPC: the average distance to the target, plus
    100 for touching the mug, plus 20 per cm inside a 1.5 cm margin. With a learned
    model it also adds a cost for every cm the ensemble members disagree."""
    hit = _seg_hits_mug(P[..., :-1, :], P[..., 1:, :]).any(-1)
    gap = np.linalg.norm(P[..., 1:, :] - np.array(MUG[:2]), axis=-1) - MUG[2]
    inside = np.clip(1.5 - gap, 0, None).sum(-1)
    c = np.linalg.norm(P[..., 1:, :] - P_TARGET, axis=-1).mean(-1) + 100.0 * hit + 20.0 * inside
    if spread is not None:
        c = c + UNSURE_WEIGHT * spread
    return c


def rollout(p0: np.ndarray, U: np.ndarray, model, unsure: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """Roll a batch of plans (pop, H, 2) forward. With the ensemble, the block position
    is the members' average and the spread is how far apart the members end up."""
    if model == 'written':
        ps = [np.broadcast_to(p0, U.shape[:-2] + (2,))]
        for k in range(U.shape[-2]):
            ps.append(written_push(ps[-1], U[..., k, :]))
        return np.stack(ps, -2), None
    moves = model.predict_all(U)                       # (members, pop, H, 2)
    ends = p0 + np.cumsum(moves, axis=-2)              # each member's own rollout
    mean = ends.mean(0)
    P = np.concatenate([np.broadcast_to(p0, mean.shape[:-2] + (1, 2)), mean], -2)
    spread = np.linalg.norm(ends - mean, axis=-1).mean(0).sum(-1) if unsure else None
    return P, spread


def cem(p0: np.ndarray, H: int, rng: np.random.Generator, model, unsure: bool,
        mean: np.ndarray | None, pop: int = 60, elites: int = 6, iters: int = 6,
        std: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """The same CEM as the Book 5 page. Only the rollout inside it changes."""
    mu = np.zeros((H, 2)) if mean is None else mean.copy()
    sd = np.full((H, 2), std)
    best_U, best_s = None, np.inf
    for _ in range(iters):
        U = clip_push(mu + sd * rng.standard_normal((pop, H, 2)))
        P, spread = rollout(p0, U, model, unsure)
        s = mpc_cost(P, spread)
        order = np.argsort(s)
        if s[order[0]] < best_s:
            best_s, best_U = float(s[order[0]]), U[order[0]]
        E = U[order[:elites]]
        mu = E.mean(0)
        sd = E.std(0) + 0.05
    return best_U, mu


def run_mpc(model, unsure: bool, seed: int, steps: int = 12) -> dict:
    """Plan 5 pushes, do the first on the real block, look again, plan again."""
    rng_plan = np.random.default_rng(seed)
    rng_real = np.random.default_rng(1000 + seed)
    p = P_START.copy()
    real = [p.copy()]
    lengths = []
    mean = None
    hits = False
    for _ in range(steps):
        U, mu = cem(p, 5, rng_plan, model, unsure, mean)
        u = clip_push(U[0])
        lengths.append(float(np.linalg.norm(u)))
        p_new = real_push(p, u, rng_real)
        hits = hits or bool(_seg_hits_mug(p, p_new))
        p = p_new
        real.append(p.copy())
        mean = np.concatenate([mu[1:], np.zeros((1, 2))])
    real_arr = np.array(real)
    d = np.linalg.norm(real_arr - P_TARGET, axis=1)
    return {'real': real_arr, 'hits': hits, 'final': float(d[-1]), 'lengths': np.array(lengths),
            'd': d}


N_SEEDS: int = 60
_CACHE: dict = {}


def learned_setup() -> dict:
    if 'ens' not in _CACHE:
        U, moved = record_pushes(np.random.default_rng(7))
        _CACHE['U'], _CACHE['moved'] = U, moved
        _CACHE['ens'] = Ensemble(U, moved, seed=1)
        runs = {}
        for name, model, unsure in (('written', 'written', False),
                                    ('learned', _CACHE['ens'], False),
                                    ('learned+unsure', _CACHE['ens'], True)):
            runs[name] = [run_mpc(model, unsure, s) for s in range(N_SEEDS)]
        _CACHE['runs'] = runs
    return _CACHE


def ensemble_picture() -> None:
    """How far the block moves along the push, for pushes straight forwards, 0 to 5 cm:
    the real block, the written model and the five learned members."""
    S = learned_setup()
    ens = S['ens']
    L = np.linspace(0, MAX_PUSH, 101)
    U = np.stack([L, np.zeros_like(L)], 1)
    member = ens.predict_all(U)                          # (members, 101, 2)
    real_mean = real_move(U)
    written = written_push(np.zeros_like(U), U)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), facecolor='white')
    for ax, dim, title in ((axes[0], 0, 'Forwards: how far the block slides'),
                           (axes[1], 1, 'Sideways: how far it drifts to the left')):
        _plain_axes(ax)
        ax.axvspan(0, RECORD_MAX, color=PALE_GREY, zorder=0)
        for m in member:
            ax.plot(L, m[:, dim], color=LINK, lw=1.4, alpha=0.8)
        ax.plot(L, real_mean[:, dim], color=INK, lw=2.4, ls='-')
        ax.plot(L, written[:, dim], color=WRIST, lw=2.0, ls='--')
        ax.set_xlim(0, MAX_PUSH)
        ax.set_xlabel('length of a straight push forwards (cm)', fontsize=11, color=INK)
        ax.set_ylabel('block moves (cm)', fontsize=11, color=INK)
        ax.set_title(title, fontsize=12, color=INK, weight='bold')
    axes[0].text(RECORD_MAX / 2, 3.6, f'the {N_RECORDS} recorded\npushes were all\nin this range',
                 fontsize=10, color=MUTED, ha='center', va='center')
    axes[0].plot([], [], color=INK, lw=2.4, label='the real block')
    axes[0].plot([], [], color=WRIST, lw=2.0, ls='--', label='the written model (0.8, 0.15)')
    axes[0].plot([], [], color=LINK, lw=1.4, label=f'the {N_MEMBERS} learned members')
    axes[0].legend(loc='lower right', fontsize=10, frameon=False)
    axes[1].text(4.0, 0.25, 'past 3 cm the members\ndisagree: none of them\nhas seen such a push',
                 fontsize=10, color=LINK, ha='center', va='center')
    fig.tight_layout(w_pad=3)
    _save(fig, SOM, 'learned-push-model.svg')


def learned_mpc_picture() -> None:
    """The same MPC loop on the real block, with three prediction steps."""
    S = learned_setup()
    runs = S['runs']
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), facecolor='white')
    titles = {'written': 'Written push model',
              'learned': 'Learned ensemble, average only',
              'learned+unsure': 'Learned ensemble, plus a cost\nfor disagreement'}
    cols = {'written': WRIST, 'learned': PURPLE, 'learned+unsure': SLIDE}
    for ax, name in zip(axes, ('written', 'learned', 'learned+unsure')):
        _axes(ax, (-4, 26), (-8, 17))
        ax.add_patch(Circle(MUG[:2], MUG[2] - 1.5, facecolor=MUTED, edgecolor='none', zorder=2))
        ax.add_patch(Circle(MUG[:2], MUG[2], facecolor='none', edgecolor=MUTED, lw=1, ls='--',
                            zorder=2))
        ax.text(MUG[0], MUG[1], 'mug', fontsize=10, color='white', ha='center', va='center',
                zorder=3)
        ax.add_patch(Rectangle(P_START - 1.5, 3, 3, facecolor=WRIST, edgecolor='none', zorder=6))
        ax.plot(*P_TARGET, marker='x', color=INK, ms=12, mew=2.5, zorder=7)
        for r in runs[name]:
            ax.plot(r['real'][:, 0], r['real'][:, 1], '-', color=cols[name], lw=0.9, alpha=0.4,
                    zorder=4)
        finals = np.array([r['final'] for r in runs[name]])
        hits = sum(r['hits'] for r in runs[name])
        long_pushes = np.mean([np.mean(r['lengths'] > RECORD_MAX) for r in runs[name]]) * 100
        ax.text(0.02, -0.02, f'{N_SEEDS} runs of 12 real pushes\n'
                f'median end: {np.median(finals):.1f} cm from target\n'
                f'pushes longer than 3 cm: {long_pushes:.0f}%\n'
                f'runs that touched the mug: {hits}', fontsize=10.5, color=INK, va='top',
                transform=ax.transAxes)
        ax.set_title(titles[name], fontsize=12, color=INK, weight='bold')
    fig.tight_layout(w_pad=1.5)
    _save(fig, SOM, 'learned-model-in-mpc.svg')


def print_mpc_numbers() -> None:
    S = learned_setup()
    ens = S['ens']
    print('--- a learned model inside MPC')
    print('records', N_RECORDS, 'max push', RECORD_MAX, 'members', N_MEMBERS, 'hidden', HIDDEN)
    print('mean training error per member (cm):', [round(e, 3) for e in ens.train_err])
    for L in (1.0, 2.0, 3.0, 4.0, 5.0):
        m = ens.predict_all(np.array([[L, 0.0]]))[:, 0, :]
        print(f'push {L} cm forwards: members forwards {np.round(m[:, 0], 2)}, left {np.round(m[:, 1], 2)}, '
              f'spread {np.linalg.norm(m - m.mean(0), axis=1).mean():.3f} cm')
    for name, rs in S['runs'].items():
        finals = np.array([r['final'] for r in rs])
        long_p = np.mean([np.mean(r['lengths'] > RECORD_MAX) for r in rs]) * 100
        within = sum(f <= 1.0 for f in finals)
        print(f'{name:15s} median final {np.median(finals):.2f} cm, worst {finals.max():.2f}, '
              f'within 1 cm {within}/{len(rs)}, hits {sum(r["hits"] for r in rs)}, '
              f'pushes > 3 cm {long_p:.0f}%, mean push {np.mean([r["lengths"].mean() for r in rs]):.2f} cm')
    global UNSURE_WEIGHT
    keep = UNSURE_WEIGHT
    UNSURE_WEIGHT = 2.0         # a heavier cost for disagreement, to show what too much does
    rs = [run_mpc(ens, True, sd) for sd in range(N_SEEDS)]
    UNSURE_WEIGHT = keep
    finals = np.array([r['final'] for r in rs])
    print(f'with weight 2.0: median final {np.median(finals):.2f} cm, within 1 cm '
          f'{sum(f <= 1.0 for f in finals)}/{len(rs)}, hits {sum(r["hits"] for r in rs)}')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    print_eval_numbers()
    intervals_picture()
    compounding_picture()
    failure_kinds_picture()
    on_failure_picture()
    print_mpc_numbers()
    ensemble_picture()
    learned_mpc_picture()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
