"""Generate the diagrams for both pages of docs/06_neural-networks/08_models-that-generate/.

    01_diffusion.md                            -> images/models-that-generate/diffusion/
    02_flow-matching-and-other-generators.md   -> images/models-that-generate/flow-matching-and-other-generators/

Run with:  python3 models_that_generate.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints them so the documents can quote the same values.

The data is simulated. It stands for a set of recorded demonstrations in which
a robot arm moves its gripper from left to right past a round obstacle at the
origin, passing either above it or below it, so the two-dimensional points are
gripper waypoints in metres. The trajectory dataset used for the autoencoder
section is built the same way, as sixteen sideways readings along one path.

The methods run on that data are real and written in NumPy: a squared-error
regression network, a denoising diffusion model with a cosine noise schedule
trained to predict the added noise, ancestral and deterministic samplers,
classifier-free guidance, a conditional flow-matching model with Euler
sampling, a two-stage histogram autoregressive model, and an autoencoder with
a flow-matching model trained in its code space. All timings are measured with
time.perf_counter on the machine that drew the pictures.
"""

import os

# One thread per matrix multiply. On the machine that drew these pictures the
# threaded BLAS spends far longer starting threads than doing the arithmetic,
# so this has to be set before numpy is imported.
for _var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_var, '1')

import pathlib  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrow, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'models-that-generate')
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

DIFF_DOC: str = 'diffusion'
FLOW_DOC: str = 'flow-matching-and-other-generators'

OBST_R: float = 0.5          # radius of the round obstacle, in metres

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


def _arena(ax: Axes, lim: float = 3.4, obstacle: bool = True,
           labels: bool = True) -> None:
    """Square axes for the waypoint plots, with the round obstacle drawn."""
    _plain(ax)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    if obstacle:
        ax.add_patch(Circle((0.0, 0.0), OBST_R, facecolor='#f3d6d6',
                            edgecolor=GRIP, lw=1.4, zorder=1))
    if labels:
        ax.set_xlabel('forward position x (m)', fontsize=9)
        ax.set_ylabel('sideways position y (m)', fontsize=9)


def _pair_dist(a: Arr, b: Arr) -> Arr:
    """Every distance between the rows of a and the rows of b."""
    return np.sqrt(np.maximum(
        ((a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None, :] - 2.0 * a @ b.T), 0.0))


def _mismatch(a: Arr, b: Arr) -> float:
    """Energy distance between two clouds of points.

    It is 0 when the two clouds look like draws from the same place, and it
    grows when they do not, so the page calls it the mismatch score.
    """
    dab = _pair_dist(a, b).mean()
    daa = _pair_dist(a, a).mean()
    dbb = _pair_dist(b, b).mean()
    return float(2.0 * dab - daa - dbb)


def _nearest(a: Arr, b: Arr) -> float:
    """Mean distance from each row of a to the closest row of b."""
    return float(_pair_dist(a, b).min(1).mean())


def _in_obstacle(p: Arr) -> float:
    return float((np.hypot(p[:, 0], p[:, 1]) < OBST_R).mean())


def _show(p: Arr, n: int = 900, seed: int = 0) -> Arr:
    """A fixed subsample, so a scatter plot stays a small file."""
    if len(p) <= n:
        return p
    idx = np.random.default_rng(seed).choice(len(p), n, replace=False)
    return p[idx]


# --------------------------------------------------------------------------
# the simulated demonstrations
# --------------------------------------------------------------------------

AMP: float = 1.43       # how far the swerve takes the gripper from the centre line
WID: float = 0.85       # how wide the swerve is


def _waypoints(n: int, rng: np.random.Generator) -> tuple[Arr, NDArray[np.int64]]:
    """n recorded gripper waypoints, half above the obstacle and half below.

    Returns the points and a side label, 0 for above and 1 for below.
    """
    x = rng.uniform(-1.7, 1.7, n)
    side = rng.integers(0, 2, n)
    sign = 1.0 - 2.0 * side
    y = sign * AMP * np.exp(-(x / WID) ** 2) + rng.normal(0.0, 0.07, n)
    return np.stack([x, y], axis=1), side


class Data:
    """The demonstration data, made once and shared by every picture."""

    def __init__(self) -> None:
        rng = np.random.default_rng(7)
        self.train, self.train_side = _waypoints(6000, rng)
        self.test, self.test_side = _waypoints(2000, rng)
        self.ref, self.ref_side = _waypoints(2000, rng)
        self.floor = _mismatch(self.test, self.ref)
        self.near_floor = _nearest(self.test, self.ref)


DATA: Data | None = None


def _data() -> Data:
    global DATA
    if DATA is None:
        DATA = Data()
    return DATA


# --------------------------------------------------------------------------
# a small network in NumPy, with Adam
# --------------------------------------------------------------------------

class MLP:
    """A fully connected network with tanh in the middle and a plain output."""

    def __init__(self, dims: list[int], seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        self.n = len(dims) - 1
        self.p: list[Arr] = []
        for i in range(self.n):
            self.p.append(rng.normal(0.0, np.sqrt(1.6 / dims[i]), (dims[i], dims[i + 1])))
            self.p.append(np.zeros(dims[i + 1]))

    def acts(self, X: Arr) -> list[Arr]:
        out = [X]
        a = X
        for i in range(self.n):
            z = a @ self.p[2 * i] + self.p[2 * i + 1]
            a = np.tanh(z) if i < self.n - 1 else z
            out.append(a)
        return out

    def run(self, X: Arr) -> Arr:
        return self.acts(X)[-1]

    def grads(self, X: Arr, target: Arr) -> tuple[float, list[Arr]]:
        acts = self.acts(X)
        diff = acts[-1] - target
        loss = float(np.mean(diff ** 2))
        d = 2.0 * diff / (diff.shape[0] * diff.shape[1])
        g: list[Arr] = [np.zeros(0)] * (2 * self.n)
        for i in reversed(range(self.n)):
            g[2 * i] = acts[i].T @ d
            g[2 * i + 1] = d.sum(0)
            if i > 0:
                d = (d @ self.p[2 * i].T) * (1.0 - acts[i] ** 2)
        return loss, g


CACHE: pathlib.Path | None = (pathlib.Path(os.environ['MTG_CACHE'])
                              if os.environ.get('MTG_CACHE') else None)


def _cached(name: str, net: MLP, make) -> tuple[bool, list[float], float]:
    """Load a trained network from the cache folder if MTG_CACHE is set."""
    if CACHE is not None:
        CACHE.mkdir(parents=True, exist_ok=True)
        f = CACHE / f'{name}.npz'
        if f.exists():
            z = np.load(f)
            for i in range(len(net.p)):
                net.p[i] = z[f'p{i}']
            return True, list(z['hist']), float(z['secs'])
    start = time.perf_counter()
    hist = make()
    secs = time.perf_counter() - start
    if CACHE is not None:
        np.savez(CACHE / f'{name}.npz', hist=np.array(hist), secs=secs,
                 **{f'p{i}': v for i, v in enumerate(net.p)})
    return False, hist, secs


def _adam(net: MLP, batches, steps: int, lr: float) -> list[float]:
    """Train with Adam and a cosine fall in the learning rate. Returns the losses."""
    m = [np.zeros_like(v) for v in net.p]
    v = [np.zeros_like(q) for q in net.p]
    hist: list[float] = []
    for it in range(1, steps + 1):
        X, target = batches(it)
        loss, g = net.grads(X, target)
        hist.append(loss)
        step = lr * 0.5 * (1.0 + np.cos(np.pi * it / steps))
        for k in range(len(net.p)):
            m[k] = 0.9 * m[k] + 0.1 * g[k]
            v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            mh = m[k] / (1.0 - 0.9 ** it)
            vh = v[k] / (1.0 - 0.999 ** it)
            net.p[k] = net.p[k] - step * mh / (np.sqrt(vh) + 1e-8)
    return hist


def _tfeat(t: Arr) -> Arr:
    """Eight numbers worked out from a step counter scaled to run from 0 to 1."""
    k = np.arange(4)
    ang = t[:, None] * np.pi * (2.0 ** k)[None, :]
    return np.concatenate([np.sin(ang), np.cos(ang)], axis=1)


def _cfeat(c: NDArray[np.int64]) -> Arr:
    """Three numbers saying what to produce: above, below, or not told."""
    out = np.zeros((len(c), 3))
    out[np.arange(len(c)), c] = 1.0
    return out


# --------------------------------------------------------------------------
# 01_diffusion.md, section 1: why the average of two right answers is wrong
# --------------------------------------------------------------------------

def two_ways_round() -> None:
    d = _data()
    above = d.train[d.train_side == 0]
    below = d.train[d.train_side == 1]
    print(f'[s1] {len(above)} waypoints above the obstacle, {len(below)} below')
    print(f'[s1] spread of the training points: x {d.train[:, 0].std():.3f} m, '
          f'y {d.train[:, 1].std():.3f} m')

    fig, ax = plt.subplots(figsize=(7.4, 7.0), facecolor='white')
    _arena(ax, lim=2.4)
    sa, sb = _show(above, 800, 1), _show(below, 800, 2)
    ax.scatter(sa[:, 0], sa[:, 1], s=8, color=LINK, alpha=0.6,
               label=f'passed above ({len(above)} waypoints)')
    ax.scatter(sb[:, 0], sb[:, 1], s=8, color=SLIDE, alpha=0.6,
               label=f'passed below ({len(below)} waypoints)')
    ax.text(0.0, 0.0, 'obstacle', ha='center', va='center', fontsize=9,
            color=GRIP, zorder=3)
    ax.plot([-2.1], [0.0], marker='s', ms=9, color=INK)
    ax.text(-2.1, -0.25, 'start', ha='center', fontsize=9.5, color=INK)
    ax.plot([2.1], [0.0], marker='*', ms=15, color=INK)
    ax.text(2.1, -0.25, 'goal', ha='center', fontsize=9.5, color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower center')
    ax.set_title('6,000 recorded gripper waypoints, 800 of each side drawn: every\n'
                 'demonstration goes round the obstacle, half of them each way',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'two-ways-round.svg')


def average_is_wrong() -> None:
    d = _data()
    band = np.abs(d.train[:, 0]) < 0.15
    pts = d.train[band]
    up = pts[pts[:, 1] > 0]
    dn = pts[pts[:, 1] < 0]
    mu_up = float(up[:, 1].mean())
    mu_dn = float(dn[:, 1].mean())
    mu_all = float(pts[:, 1].mean())
    print(f'[s1] in the band |x| < 0.15 m there are {len(up)} points above '
          f'(mean y {mu_up:+.3f} m) and {len(dn)} below (mean y {mu_dn:+.3f} m)')
    print(f'[s1] the average of all {len(pts)} of them is y = {mu_all:+.4f} m, '
          f'which is {abs(mu_all):.4f} m from the middle of an obstacle of '
          f'radius {OBST_R} m')

    fig, ax = plt.subplots(figsize=(7.2, 6.8), facecolor='white')
    _arena(ax, lim=2.0)
    ax.scatter(up[:, 0], up[:, 1], s=16, color=LINK, alpha=0.7)
    ax.scatter(dn[:, 0], dn[:, 1], s=16, color=SLIDE, alpha=0.7)
    ax.axhline(mu_up, color=LINK, lw=1.4, ls='--')
    ax.axhline(mu_dn, color=SLIDE, lw=1.4, ls='--')
    ax.text(-1.92, mu_up + 0.09, f'average above: y = {mu_up:+.3f} m',
            fontsize=9.5, color=LINK)
    ax.text(-1.92, mu_dn - 0.22, f'average below: y = {mu_dn:+.3f} m',
            fontsize=9.5, color=SLIDE)
    ax.plot([0.0], [mu_all], marker='X', ms=16, color=PURPLE, zorder=5)
    ax.annotate(f'average of both answers:\ny = {mu_all:+.3f} m,\ninside the obstacle',
                xy=(0.0, mu_all), xytext=(0.85, 0.95), fontsize=10, color=PURPLE,
                weight='bold',
                arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.6))
    ax.set_title('The two right answers at x = 0, and their average,\n'
                 'which is the one place the gripper must not be',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'average-is-wrong.svg')


class Predictor:
    """A plain squared-error network that predicts y from x."""

    def __init__(self) -> None:
        d = _data()
        rng = np.random.default_rng(21)
        X = d.train[:, :1]
        Y = d.train[:, 1:]
        self.net = MLP([1, 64, 64, 1], seed=5)

        def batches(_it: int) -> tuple[Arr, Arr]:
            idx = rng.integers(0, len(X), 512)
            return X[idx], Y[idx]

        self.hist = _adam(self.net, batches, 4000, 3e-3)
        self.loss = float(np.mean((self.net.run(X) - Y) ** 2))
        sign = 1.0 - 2.0 * d.train_side
        arc = (sign * AMP * np.exp(-(d.train[:, 0] / WID) ** 2))[:, None]
        self.loss_arc = float(np.mean((np.abs(arc) - Y) ** 2))
        self.grid = np.linspace(-1.7, 1.7, 201)
        self.curve = self.net.run(self.grid[:, None])[:, 0]


PRED: Predictor | None = None


def _pred() -> Predictor:
    global PRED
    if PRED is None:
        PRED = Predictor()
    return PRED


def what_a_predictor_gives() -> None:
    d = _data()
    p = _pred()
    inside = float((np.hypot(p.grid, p.curve) < OBST_R).mean())
    mid = np.abs(p.grid) < 0.3
    print(f'[s1] the squared-error network ends with training error '
          f'{p.loss:.4f} m^2; always answering the upper arc would give '
          f'{p.loss_arc:.4f} m^2')
    print(f'[s1] its answer in |x| < 0.3 m runs from {p.curve[mid].min():+.3f} to '
          f'{p.curve[mid].max():+.3f} m, and {inside * 100:.1f}% of its path '
          f'lies inside the obstacle')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 6.2), facecolor='white')
    ax = axes[0]
    _arena(ax, lim=2.0)
    sh = _show(d.train, 1000, 3)
    ax.scatter(sh[:, 0], sh[:, 1], s=6, color=MUTED, alpha=0.4,
               label='the demonstrations')
    ax.plot(p.grid, p.curve, color=PURPLE, lw=3.0,
            label='what the predictor answers')
    ax.legend(fontsize=9.5, frameon=False, loc='lower center')
    ax.set_title('A network trained on squared error answers\n'
                 'with the average, straight through the obstacle',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    names = ['answer the average\n(what training finds)',
             'always answer\nthe upper arc']
    vals = [p.loss, p.loss_arc]
    bars = ax.bar(names, vals, color=[PURPLE, LINK], width=0.55, edgecolor=INK, lw=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f'{v:.3f}', ha='center',
                fontsize=11, weight='bold', color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel('average squared error on the training data (m$^2$)', fontsize=9.5)
    ax.set_title('Squared error prefers the useless answer,\n'
                 'because it scores lower than either real answer',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'what-a-predictor-gives.svg')


def many_right_answers() -> None:
    d = _data()
    p = _pred()
    band = np.abs(d.train[:, 0]) < 0.15
    ys = d.train[band][:, 1]
    guesses = np.linspace(-2.0, 2.0, 401)
    curve = np.array([float(np.mean((ys - g) ** 2)) for g in guesses])
    best = float(guesses[int(np.argmin(curve))])
    at_arc = float(np.mean((ys - AMP) ** 2))
    print(f'[s1] over the {len(ys)} points in the band, the single answer with '
          f'the lowest squared error is y = {best:+.3f} m, scoring '
          f'{curve.min():.4f} m^2, while answering y = {AMP:+.2f} m scores '
          f'{at_arc:.4f} m^2')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.hist(ys, bins=40, color=LINK, alpha=0.75, edgecolor=INK, lw=0.4)
    ax.axvline(float(p.net.run(np.zeros((1, 1)))[0, 0]), color=PURPLE, lw=2.5)
    ax.text(0.06, ax.get_ylim()[1] * 0.80, 'the predictor\'s\nsingle answer',
            fontsize=9.5, color=PURPLE, weight='bold')
    ax.set_xlabel('sideways position y of the real waypoints at x = 0 (m)', fontsize=9.5)
    ax.set_ylabel('how many waypoints', fontsize=9.5)
    ax.set_title(f'The {len(ys)} real answers at x = 0 have two peaks',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ax.plot(guesses, curve, color=GRIP, lw=2.4)
    ax.plot([best], [curve.min()], marker='o', ms=9, color=PURPLE)
    ax.annotate(f'lowest at y = {best:+.3f} m', xy=(best, curve.min()),
                xytext=(-1.95, curve.max() * 0.45), fontsize=10, color=PURPLE,
                arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.4))
    for g, lab in ((AMP, 'the upper arc'), (-AMP, 'the lower arc')):
        ax.plot([g], [float(np.mean((ys - g) ** 2))], marker='o', ms=8, color=LINK)
        ax.text(g, float(np.mean((ys - g) ** 2)) + 0.12, lab, ha='center',
                fontsize=9.5, color=LINK)
    ax.set_xlabel('the one number the predictor could answer at x = 0 (m)', fontsize=9.5)
    ax.set_ylabel('its average squared error (m$^2$)', fontsize=9.5)
    ax.set_title('The score is lowest exactly between the two\n'
                 'right answers, so that is the answer training picks',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'many-right-answers.svg')


# --------------------------------------------------------------------------
# 01_diffusion.md, section 2: adding the noise, step by step
# --------------------------------------------------------------------------

T_STEPS: int = 100


def _schedule(T: int = T_STEPS, s: float = 0.008) -> dict[str, Arr]:
    """The cosine noise schedule: how much data is left after each step."""
    tt = np.arange(T + 1) / T
    f = np.cos((tt + s) / (1.0 + s) * np.pi / 2.0) ** 2
    ab = np.clip(f / f[0], 1e-5, 1.0)
    beta = np.concatenate([[0.0], np.clip(1.0 - ab[1:] / ab[:-1], 0.0, 0.999)])
    return {'ab': ab, 'beta': beta, 'alpha': 1.0 - beta}


SCHED: dict[str, Arr] = _schedule()


def _noisy(x0: Arr, t: int, rng: np.random.Generator) -> tuple[Arr, Arr]:
    ab = SCHED['ab'][t]
    eps = rng.normal(size=x0.shape)
    return np.sqrt(ab) * x0 + np.sqrt(1.0 - ab) * eps, eps


def forward_noise_steps() -> None:
    d = _data()
    rng = np.random.default_rng(31)
    base = _show(d.train, 900, 4)
    shots = [0, 20, 40, 60, 80, 100]
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 9.0), facecolor='white')
    for ax, t in zip(axes.ravel(), shots):
        xt, _ = _noisy(base, t, np.random.default_rng(31))
        _arena(ax, lim=3.6, obstacle=(t == 0), labels=False)
        ax.scatter(xt[:, 0], xt[:, 1], s=6, color=LINK if t < 100 else PURPLE,
                   alpha=0.55)
        ab = float(SCHED['ab'][t])
        ax.set_title(f'step t = {t}\ndata kept {np.sqrt(ab):.3f}, '
                     f'noise added {np.sqrt(1 - ab):.3f}',
                     fontsize=10.5, weight='bold', color=INK)
        print(f'[s2] t = {t:3d}: sqrt(kept) {np.sqrt(ab):.4f}, '
              f'sqrt(noise) {np.sqrt(1 - ab):.4f}, spread of the cloud '
              f'x {xt[:, 0].std():.3f}, y {xt[:, 1].std():.3f}')
    for ax in axes.ravel():
        ax.set_xlabel('x', fontsize=9)
        ax.set_ylabel('y', fontsize=9)
    fig.suptitle('Adding noise in 100 steps turns the two arcs into a plain round blob',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'forward-noise-steps.svg')


def noise_schedule() -> None:
    ab = SCHED['ab']
    ts = np.arange(len(ab))
    marks = [0, 10, 25, 50, 75, 90, 100]
    print('[s2] schedule: ' + '; '.join(
        f't={m} kept {np.sqrt(ab[m]):.3f} noise {np.sqrt(1 - ab[m]):.3f}'
        for m in marks))
    half = int(np.argmin(np.abs(np.sqrt(ab) - np.sqrt(1 - ab))))
    print(f'[s2] the two halves are equal at t = {half}, where each is '
          f'{np.sqrt(ab[half]):.3f}')
    print(f'[s2] the biggest single-step beta is {SCHED["beta"].max():.4f} at '
          f't = {int(np.argmax(SCHED["beta"]))}')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(ts, np.sqrt(ab), color=LINK, lw=2.6, label='how much data is kept')
    ax.plot(ts, np.sqrt(1.0 - ab), color=GRIP, lw=2.6, label='how much noise is added')
    ax.axvline(half, color=MUTED, ls='--', lw=1.2)
    ax.text(half + 3, 0.18, f'equal at t = {half}', fontsize=9.5, color=MUTED)
    for m in (25, 75):
        ax.plot([m], [np.sqrt(ab[m])], marker='o', ms=6, color=LINK)
        ax.text(m, np.sqrt(ab[m]) + 0.04, f'{np.sqrt(ab[m]):.2f}', ha='center',
                fontsize=9, color=LINK)
    ax.set_xlabel('step t', fontsize=9.5)
    ax.set_ylabel('multiplier used at that step', fontsize=9.5)
    ax.set_ylim(0, 1.08)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax.set_title('The cosine schedule: the two multipliers at every step',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ax.plot(ts[1:], SCHED['beta'][1:], color=PURPLE, lw=2.6)
    ax.set_xlabel('step t', fontsize=9.5)
    ax.set_ylabel('share of the point replaced at step t', fontsize=9.5)
    ax.set_title('How much one single step changes:\nalmost nothing early, almost'
                 ' everything late', fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'noise-schedule.svg')


def one_point_walk() -> None:
    rng = np.random.default_rng(44)
    x0 = np.array([0.0, AMP])
    ts = np.arange(T_STEPS + 1)
    paths = []
    for k in range(6):
        r = np.random.default_rng(100 + k)
        eps = r.normal(size=(2,))
        paths.append(np.sqrt(SCHED['ab'])[:, None] * x0[None, :]
                     + np.sqrt(1.0 - SCHED['ab'])[:, None] * eps[None, :])
    cloud = np.stack([np.sqrt(SCHED['ab'])[:, None] * x0[None, :]
                      + np.sqrt(1.0 - SCHED['ab'])[:, None] * e[None, :]
                      for e in rng.normal(size=(600, 2))])
    print(f'[s2] one waypoint at ({x0[0]:.2f}, {x0[1]:.2f}) m: at t = 25 its noisy '
          f'copies have mean y {cloud[:, 25, 1].mean():+.3f} and spread '
          f'{cloud[:, 25, 1].std():.3f}')
    print(f'[s2] at t = 100 they have mean y {cloud[:, 100, 1].mean():+.3f} and '
          f'spread {cloud[:, 100, 1].std():.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for k, p in enumerate(paths):
        ax.plot(ts, p[:, 1], lw=1.8, alpha=0.9,
                color=[LINK, SLIDE, GRIP, PURPLE, TEAL, WRIST][k])
    ax.plot(ts, np.sqrt(SCHED['ab']) * x0[1], color=INK, lw=2.8, ls='--',
            label='where the waypoint itself has got to')
    ax.axhline(0, color=MUTED, lw=1.0)
    ax.set_xlabel('step t', fontsize=9.5)
    ax.set_ylabel('sideways position y (m)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax.set_title(f'Six noisy copies of the single waypoint (0.00, {x0[1]:.2f}),\n'
                 'each with its own fixed noise', fontsize=11.5, weight='bold',
                 color=INK)
    ax = axes[1]
    _plain(ax)
    edges = np.linspace(-3.4, 3.8, 50)
    for t, col in ((25, LINK), (50, SLIDE), (100, PURPLE)):
        ax.hist(cloud[:, t, 1], bins=edges, color=col, alpha=0.55,
                label=f't = {t} (spread {cloud[:, t, 1].std():.2f} m)')
    ax.axvline(x0[1], color=INK, lw=2.0, ls='--')
    ax.text(x0[1] + 0.12, 5, 'where the waypoint\nstarted, at t = 0',
            fontsize=9, color=INK)
    ax.set_xlabel('sideways position y of the noisy copy (m)', fontsize=9.5)
    ax.set_ylabel('how many of the 600 copies', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('The same waypoint, spread wider at every step',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'one-point-walk.svg')


def blob_is_round() -> None:
    d = _data()
    rng = np.random.default_rng(55)
    xT, _ = _noisy(d.test, T_STEPS, rng)
    pure = rng.normal(size=(len(d.test), 2))
    spreads = np.array([_noisy(d.test, t, np.random.default_rng(9))[0].std(0)
                        for t in range(T_STEPS + 1)])
    print(f'[s2] at t = 100 the noisy data has mean ({xT[:, 0].mean():+.3f}, '
          f'{xT[:, 1].mean():+.3f}) and spread ({xT[:, 0].std():.3f}, '
          f'{xT[:, 1].std():.3f})')
    print(f'[s2] plain round noise has mean ({pure[:, 0].mean():+.3f}, '
          f'{pure[:, 1].mean():+.3f}) and spread ({pure[:, 0].std():.3f}, '
          f'{pure[:, 1].std():.3f})')
    print(f'[s2] mismatch score between the two {_mismatch(xT, pure):.4f}, '
          f'against a floor of {d.floor:.4f}')

    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.0), facecolor='white')
    for ax, pts, name in ((axes[0], xT, 'the data after 100 noise steps'),
                          (axes[1], pure, 'plain round noise, drawn from scratch')):
        _arena(ax, lim=3.6, obstacle=False, labels=False)
        s = _show(pts, 900, 6)
        ax.scatter(s[:, 0], s[:, 1], s=6, color=PURPLE if pts is xT else TEAL,
                   alpha=0.5)
        ax.set_xlabel('x', fontsize=9)
        ax.set_ylabel('y', fontsize=9)
        ax.set_title(f'{name}\nspread {pts[:, 0].std():.2f} across, '
                     f'{pts[:, 1].std():.2f} up', fontsize=10.5, weight='bold',
                     color=INK)
    ax = axes[2]
    _plain(ax)
    ax.plot(spreads[:, 0], color=LINK, lw=2.4, label='spread across (x)')
    ax.plot(spreads[:, 1], color=SLIDE, lw=2.4, label='spread up (y)')
    ax.axhline(1.0, color=MUTED, ls='--', lw=1.2)
    ax.text(5, 1.04, 'spread of plain round noise', fontsize=9, color=MUTED)
    ax.set_xlabel('step t', fontsize=9.5)
    ax.set_ylabel('spread of the cloud (m)', fontsize=9.5)
    ax.set_ylim(0, 1.25)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('Both directions end at the same spread,\n'
                 'which is why the end is a round blob', fontsize=10.5,
                 weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'blob-is-round.svg')


# --------------------------------------------------------------------------
# the denoiser itself, trained in NumPy
# --------------------------------------------------------------------------

HIDDEN: int = 128
DIFF_STEPS: int = 12000
ABOVE, BELOW, UNTOLD = 0, 1, 2
CLIP: float = 3.0   # the guess of the clean waypoint is kept in this range


def _dinput(x: Arr, t: Arr, c: NDArray[np.int64]) -> Arr:
    return np.concatenate([x, _tfeat(t), _cfeat(c)], axis=1)


class Denoiser:
    """A network trained to name the noise that was added at one step."""

    def __init__(self) -> None:
        d = _data()
        rng = np.random.default_rng(101)
        self.net = MLP([2 + 8 + 3, HIDDEN, HIDDEN, 2], seed=12)

        def batches(_it: int) -> tuple[Arr, Arr]:
            idx = rng.integers(0, len(d.train), 512)
            x0 = d.train[idx]
            c = d.train_side[idx].copy()
            c[rng.uniform(size=len(c)) < 0.2] = UNTOLD
            t = rng.integers(1, T_STEPS + 1, len(idx))
            ab = SCHED['ab'][t][:, None]
            eps = rng.normal(size=x0.shape)
            xt = np.sqrt(ab) * x0 + np.sqrt(1.0 - ab) * eps
            return _dinput(xt, t / T_STEPS, c), eps

        _, self.hist, self.train_seconds = _cached(
            'denoiser', self.net, lambda: _adam(self.net, batches, DIFF_STEPS, 2e-3))

    def eps(self, x: Arr, t: int, c: int) -> Arr:
        n = len(x)
        return self.net.run(_dinput(x, np.full(n, t / T_STEPS),
                                    np.full(n, c, dtype=np.int64)))

    def guided(self, x: Arr, t: int, c: int, w: float) -> Arr:
        if c == UNTOLD or w == 1.0:
            return self.eps(x, t, c)
        e_u = self.eps(x, t, UNTOLD)
        return e_u + w * (self.eps(x, t, c) - e_u)


DEN: Denoiser | None = None


def _den() -> Denoiser:
    global DEN
    if DEN is None:
        DEN = Denoiser()
    return DEN


def _ddpm(n: int, c: int, seed: int, w: float = 1.0,
          snaps: tuple[int, ...] = ()) -> tuple[Arr, dict[int, Arr]]:
    """The reverse walk, one step at a time, with fresh noise added back.

    The guess of the clean waypoint is kept inside the range the data occupies,
    which is what every standard sampler does and what stops a strong guidance
    setting running away.
    """
    den = _den()
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    kept: dict[int, Arr] = {T_STEPS: x.copy()} if T_STEPS in snaps else {}
    for t in range(T_STEPS, 0, -1):
        eps = den.guided(x, t, c, w)
        beta = float(SCHED['beta'][t])
        ab = float(SCHED['ab'][t])
        abp = float(SCHED['ab'][t - 1])
        x0h = np.clip((x - np.sqrt(1.0 - ab) * eps) / np.sqrt(ab), -CLIP, CLIP)
        mean = (np.sqrt(abp) * beta / (1.0 - ab) * x0h
                + np.sqrt(1.0 - beta) * (1.0 - abp) / (1.0 - ab) * x)
        if t > 1:
            sig = np.sqrt(beta * (1.0 - abp) / (1.0 - ab))
            x = mean + sig * rng.normal(size=x.shape)
        else:
            x = mean
        if t - 1 in snaps:
            kept[t - 1] = x.copy()
    return x, kept


def _ddim(n: int, c: int, seed: int, steps: int, w: float = 1.0) -> tuple[Arr, Arr]:
    """The reverse walk with no noise added back, so it can skip steps."""
    den = _den()
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    order = np.unique(np.linspace(1, T_STEPS, steps).round().astype(int))[::-1]
    path = [x.copy()]
    for i, t in enumerate(order):
        eps = den.guided(x, int(t), c, w)
        ab = float(SCHED['ab'][t])
        x0h = np.clip((x - np.sqrt(1.0 - ab) * eps) / np.sqrt(ab), -CLIP, CLIP)
        prev = int(order[i + 1]) if i + 1 < len(order) else 0
        abp = float(SCHED['ab'][prev])
        x = np.sqrt(abp) * x0h + np.sqrt(1.0 - abp) * eps
        path.append(x.copy())
    return x, np.array(path)


# --------------------------------------------------------------------------
# 01_diffusion.md, section 3: training the network to name the noise
# --------------------------------------------------------------------------

def noise_prediction_target() -> None:
    d = _data()
    den = _den()
    x0 = np.array([[0.0, AMP]])
    eps = np.array([[1.1, -1.6]])
    t = 50
    ab = float(SCHED['ab'][t])
    xt = np.sqrt(ab) * x0 + np.sqrt(1.0 - ab) * eps
    hat = den.eps(xt, t, UNTOLD)
    hat_c = den.eps(xt, t, ABOVE)
    print(f'[s3] one training example at t = {t}: x0 = ({x0[0, 0]:.2f}, '
          f'{x0[0, 1]:.2f}), noise = ({eps[0, 0]:.2f}, {eps[0, 1]:.2f}), '
          f'kept {np.sqrt(ab):.3f} so xt = ({xt[0, 0]:.3f}, {xt[0, 1]:.3f})')
    print(f'[s3] the trained network answers ({hat[0, 0]:.3f}, {hat[0, 1]:.3f}) '
          f'when it is not told the side, and ({hat_c[0, 0]:.3f}, '
          f'{hat_c[0, 1]:.3f}) when it is told "above"')

    fig, ax = plt.subplots(figsize=(9.0, 8.2), facecolor='white')
    _arena(ax, lim=3.2)
    sh = _show(d.train, 700, 8)
    ax.scatter(sh[:, 0], sh[:, 1], s=5, color=GRID, alpha=0.8)
    scaled = np.sqrt(ab) * x0
    ax.plot(x0[0, 0], x0[0, 1], marker='o', ms=11, color=LINK, zorder=4)
    ax.text(x0[0, 0] + 0.1, x0[0, 1] + 0.12,
            f'the real waypoint\n({x0[0, 0]:.2f}, {x0[0, 1]:.2f})',
            fontsize=9.5, color=LINK)
    ax.plot(scaled[0, 0], scaled[0, 1], marker='o', ms=9, color=TEAL, zorder=4)
    ax.text(scaled[0, 0] - 1.55, scaled[0, 1],
            f'shrunk by {np.sqrt(ab):.3f}:\n({scaled[0, 0]:.2f}, {scaled[0, 1]:.2f})',
            fontsize=9.5, color=TEAL)
    ax.annotate('', xy=(xt[0, 0], xt[0, 1]), xytext=(scaled[0, 0], scaled[0, 1]),
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=2.4))
    ax.text(0.45, 0.72, f'the noise, times {np.sqrt(1 - ab):.3f}\n'
            f'({eps[0, 0]:.2f}, {eps[0, 1]:.2f})', fontsize=9.5, color=GRIP)
    ax.plot(xt[0, 0], xt[0, 1], marker='X', ms=14, color=PURPLE, zorder=5)
    ax.text(xt[0, 0] + 0.15, xt[0, 1] - 0.45,
            f'what the network is shown:\n({xt[0, 0]:.2f}, {xt[0, 1]:.2f}), '
            f'at t = {t}', fontsize=9.5, color=PURPLE)
    guess = (xt - np.sqrt(1 - ab) * hat) / np.sqrt(ab)
    ax.annotate('', xy=(guess[0, 0], guess[0, 1]), xytext=(xt[0, 0], xt[0, 1]),
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=2.4, ls='--'))
    ax.plot(guess[0, 0], guess[0, 1], marker='o', ms=9, color=SLIDE, zorder=5)
    ax.text(guess[0, 0] + 0.12, guess[0, 1] + 0.05,
            f'taking out the noise it named,\n({hat[0, 0]:.2f}, {hat[0, 1]:.2f}), '
            f'puts the clean\nwaypoint at ({guess[0, 0]:.2f}, {guess[0, 1]:.2f}),'
            f'\nwhich is nowhere a waypoint sits',
            fontsize=9.5, color=SLIDE)
    print(f'[s3] taking the named noise back out puts the clean waypoint at '
          f'({guess[0, 0]:.3f}, {guess[0, 1]:.3f}), which is between the two arcs '
          f'rather than on either of them')
    ax.set_title('One training example: the waypoint is shrunk, noise is added,\n'
                 'and the network has to name the noise from the result alone',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'noise-prediction-target.svg')


def training_curve() -> None:
    den = _den()
    h = np.array(den.hist)
    smooth = np.convolve(h, np.ones(200) / 200, mode='valid')
    print(f'[s3] training ran {DIFF_STEPS} steps in {den.train_seconds:.1f} s; '
          f'the squared error fell from {smooth[0]:.4f} to {smooth[-1]:.4f}')
    marks = [0, 1000, 3000, 6000, len(smooth) - 1]
    print('[s3] smoothed error: ' + '; '.join(
        f'step {m}: {smooth[m]:.4f}' for m in marks))

    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(h, color=LINK_PALE, lw=0.6, label='each batch of 512 examples')
    ax.plot(np.arange(len(smooth)) + 100, smooth, color=LINK, lw=2.4,
            label='average over 200 batches')
    for m in marks:
        ax.plot([m + 100], [smooth[m]], marker='o', ms=6, color=PURPLE)
        ax.text(m + 220, smooth[m] + 0.03, f'{smooth[m]:.3f}', fontsize=9,
                color=PURPLE)
    ax.set_xlabel('training step', fontsize=9.5)
    ax.set_ylabel('average squared error of the named noise', fontsize=9.5)
    ax.set_ylim(0, 1.3)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title(f'Training the denoiser: {DIFF_STEPS:,} steps, '
                 f'{den.train_seconds:.0f} seconds on one processor core',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'training-curve.svg')


def predicted_vs_true_noise() -> None:
    d = _data()
    den = _den()
    rng = np.random.default_rng(66)
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.0), facecolor='white')
    for ax, t in zip(axes, (10, 50, 90)):
        idx = rng.integers(0, len(d.test), 600)
        x0 = d.test[idx]
        ab = float(SCHED['ab'][t])
        eps = rng.normal(size=x0.shape)
        xt = np.sqrt(ab) * x0 + np.sqrt(1.0 - ab) * eps
        hat = den.eps(xt, t, UNTOLD)
        err = float(np.mean((hat - eps) ** 2))
        corr = float(np.corrcoef(hat.ravel(), eps.ravel())[0, 1])
        print(f'[s3] at t = {t:3d}: squared error {err:.3f}, agreement '
              f'{corr:.3f}, spread of the answers {hat.std():.3f} against '
              f'{eps.std():.3f} for the real noise')
        _plain(ax)
        ax.plot([-3.2, 3.2], [-3.2, 3.2], color=MUTED, ls='--', lw=1.2)
        ax.scatter(eps[:, 1], hat[:, 1], s=8, color=LINK, alpha=0.5)
        ax.set_xlim(-3.4, 3.4)
        ax.set_ylim(-3.4, 3.4)
        ax.set_aspect('equal')
        ax.set_xlabel('the noise that was really added (y part)', fontsize=9)
        ax.set_ylabel('the noise the network names', fontsize=9)
        ax.set_title(f't = {t}: squared error {err:.2f},\nagreement {corr:.2f}',
                     fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    fig.subplots_adjust(top=0.80)
    fig.suptitle('The network is almost exactly right late on and badly wrong '
                 'early on', fontsize=12.5, weight='bold', color=INK, y=0.99)
    _save(fig, DIFF_DOC, 'predicted-vs-true-noise.svg')


def error_by_time() -> None:
    d = _data()
    den = _den()
    rng = np.random.default_rng(77)
    ts = np.arange(1, T_STEPS + 1)
    errs = []
    for t in ts:
        idx = rng.integers(0, len(d.test), 500)
        x0 = d.test[idx]
        ab = float(SCHED['ab'][t])
        eps = rng.normal(size=x0.shape)
        xt = np.sqrt(ab) * x0 + np.sqrt(1.0 - ab) * eps
        errs.append(float(np.mean((den.eps(xt, int(t), UNTOLD) - eps) ** 2)))
    errs = np.array(errs)
    print(f'[s3] squared error by step: t=1 {errs[0]:.3f}, t=25 {errs[24]:.3f}, '
          f't=50 {errs[49]:.3f}, t=75 {errs[74]:.3f}, t=100 {errs[99]:.3f}')
    print(f'[s3] the worst step is t = {int(ts[np.argmax(errs)])} with '
          f'{errs.max():.3f}, the best is t = {int(ts[np.argmin(errs)])} with '
          f'{errs.min():.3f}')

    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(ts, errs, color=GRIP, lw=2.4)
    ax.axhline(1.0, color=MUTED, ls='--', lw=1.2)
    ax.text(3, 1.03, 'what guessing zero would score', fontsize=9, color=MUTED)
    for t in (1, 25, 50, 75, 100):
        ax.plot([t], [errs[t - 1]], marker='o', ms=6, color=PURPLE)
        ax.text(t + (4 if t == 1 else 0), errs[t - 1] + 0.035,
                f'{errs[t - 1]:.2f}', ha='center', fontsize=9, color=PURPLE)
    ax.set_xlabel('step t the network is asked about', fontsize=9.5)
    ax.set_ylabel('average squared error of the named noise', fontsize=9.5)
    ax.set_ylim(0, 1.2)
    ax.set_title('The same network is good at the late steps and poor at the early\n'
                 'ones, because early on the noise cannot be worked out from the point',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'error-by-time.svg')


# --------------------------------------------------------------------------
# 01_diffusion.md, section 4: the reverse walk
# --------------------------------------------------------------------------

def reverse_walk_panels() -> None:
    shots = (100, 80, 60, 40, 20, 0)
    pts, kept = _ddpm(900, UNTOLD, seed=201, snaps=shots)
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 9.0), facecolor='white')
    for ax, t in zip(axes.ravel(), shots):
        p = kept[t]
        _arena(ax, lim=3.6, obstacle=(t == 0), labels=False)
        ax.scatter(p[:, 0], p[:, 1], s=6, color=PURPLE if t > 0 else SLIDE,
                   alpha=0.55)
        ax.set_xlabel('x', fontsize=9)
        ax.set_ylabel('y', fontsize=9)
        ax.set_title(f'after walking back to t = {t}\n'
                     f'spread {p[:, 0].std():.2f} across, {p[:, 1].std():.2f} up',
                     fontsize=10.5, weight='bold', color=INK)
        print(f'[s4] t = {t:3d}: spread ({p[:, 0].std():.3f}, {p[:, 1].std():.3f}), '
              f'inside the obstacle {_in_obstacle(p) * 100:.1f}%')
    fig.suptitle('The reverse walk: 900 points of plain noise, carried back one step '
                 'at a time\nby the trained denoiser, until they lie on the two arcs',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'reverse-walk-panels.svg')


def one_sample_path() -> None:
    d = _data()
    shots = tuple(range(0, 101))
    _, kept = _ddpm(3, UNTOLD, seed=303, snaps=shots)
    track = np.stack([kept[t] for t in range(100, -1, -1)])      # (101, 3, 2)
    _, dpath = _ddim(3, UNTOLD, seed=303, steps=100)
    lengths = np.sqrt(((track[1:] - track[:-1]) ** 2).sum(-1)).sum(0)
    direct = np.sqrt(((track[-1] - track[0]) ** 2).sum(-1))
    dl = np.sqrt(((dpath[1:] - dpath[:-1]) ** 2).sum(-1)).sum(0)
    dd = np.sqrt(((dpath[-1] - dpath[0]) ** 2).sum(-1))
    print(f'[s4] with the noise put back, three walks travel on average '
          f'{lengths.mean():.1f} m to cover {direct.mean():.1f} m of ground, a '
          f'ratio of {(lengths / direct).mean():.1f}')
    print(f'[s4] with the noise left out, the same three travel '
          f'{dl.mean():.2f} m to cover {dd.mean():.2f} m, a ratio of '
          f'{(dl / dd).mean():.2f}')

    cols = [LINK, SLIDE, GRIP]
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 6.6), facecolor='white')
    for ax, path, name, ratio in (
            (axes[0], track, 'noise put back at every step',
             float((lengths / direct).mean())),
            (axes[1], dpath, 'the same three, with the noise left out',
             float((dl / dd).mean()))):
        _arena(ax, lim=3.2, labels=False)
        sh = _show(d.train, 500, 9)
        ax.scatter(sh[:, 0], sh[:, 1], s=4, color=GRID, alpha=0.9)
        for k in range(3):
            ax.plot(path[:, k, 0], path[:, k, 1], color=cols[k], lw=1.2, alpha=0.9)
            ax.plot(path[0, k, 0], path[0, k, 1], marker='o', ms=7, color=cols[k])
            ax.plot(path[-1, k, 0], path[-1, k, 1], marker='*', ms=15, color=cols[k])
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(f'{name}\npath is {ratio:.1f} times the straight line',
                     fontsize=11, weight='bold', color=INK)
    axes[0].text(-3.1, 2.85, 'circle: where the point started, in pure noise\n'
                 'star: where it finished, on the data', fontsize=9.5, color=INK)
    fig.suptitle('Three single points walked back from the same noise to the arcs',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'one-sample-path.svg')


def generated_vs_real() -> None:
    d = _data()
    gen, _ = _ddpm(2000, UNTOLD, seed=404)
    mis = _mismatch(gen, d.ref)
    near = _nearest(gen, d.ref)
    print(f'[s4] 2,000 generated waypoints: mismatch score {mis:.4f} against a '
          f'floor of {d.floor:.4f}; nearest real point {near:.4f} m against a '
          f'floor of {d.near_floor:.4f} m')
    print(f'[s4] generated above {float((gen[:, 1] > 0).mean()) * 100:.1f}%, '
          f'inside the obstacle {_in_obstacle(gen) * 100:.2f}%, real data '
          f'{_in_obstacle(d.ref) * 100:.2f}%')

    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.4), facecolor='white')
    for ax, pts, name, col in (
            (axes[0], d.ref, 'real demonstrations', LINK),
            (axes[1], gen, 'generated by the reverse walk', SLIDE)):
        _arena(ax, lim=2.4, labels=False)
        s = _show(pts, 900, 11)
        ax.scatter(s[:, 0], s[:, 1], s=6, color=col, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(f'{name}\ninside the obstacle: '
                     f'{_in_obstacle(pts) * 100:.2f}%',
                     fontsize=10.5, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    names = ['real against real\n(the best possible)', 'generated against real']
    vals = [d.floor, mis]
    bars = ax.bar(names, vals, color=[MUTED, SLIDE], width=0.5, edgecolor=INK, lw=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, f'{v:.4f}',
                ha='center', fontsize=11, weight='bold', color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel('mismatch score (0 is a perfect match)', fontsize=9.5)
    ax.set_title('How far the generated cloud is\nfrom the real one',
                 fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'generated-vs-real.svg')


def the_step_rule() -> None:
    den = _den()
    rng = np.random.default_rng(505)
    t = 40
    x = np.array([[0.62, 1.05]])
    eps = den.eps(x, t, UNTOLD)
    beta = float(SCHED['beta'][t])
    ab = float(SCHED['ab'][t])
    mean = (x - beta / np.sqrt(1.0 - ab) * eps) / np.sqrt(1.0 - beta)
    sig = float(np.sqrt(beta * (1.0 - SCHED['ab'][t - 1]) / (1.0 - ab)))
    draws = mean + sig * rng.normal(size=(200, 2))
    print(f'[s4] one reverse step from t = {t}: the point ({x[0, 0]:.2f}, '
          f'{x[0, 1]:.2f}), the named noise ({eps[0, 0]:.3f}, {eps[0, 1]:.3f}), '
          f'beta {beta:.4f}, the new middle ({mean[0, 0]:.3f}, {mean[0, 1]:.3f}), '
          f'and the noise put back has spread {sig:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.set_xlim(0.3, 1.0)
    ax.set_ylim(0.75, 1.3)
    ax.set_aspect('equal')
    ax.scatter(draws[:, 0], draws[:, 1], s=9, color=LINK_PALE, alpha=0.9,
               label=f'200 draws of the new point, spread {sig:.3f}')
    ax.plot(x[0, 0], x[0, 1], marker='X', ms=14, color=PURPLE, zorder=5)
    ax.text(x[0, 0] + 0.02, x[0, 1] + 0.055, f'the point at t = {t}',
            fontsize=9.5, color=PURPLE)
    ax.plot(mean[0, 0], mean[0, 1], marker='o', ms=11, color=GRIP, zorder=5)
    ax.text(mean[0, 0] - 0.025, mean[0, 1] - 0.085,
            f'the middle of the next point\n({mean[0, 0]:.3f}, {mean[0, 1]:.3f})',
            fontsize=9.5, color=GRIP, ha='right')
    ax.annotate('', xy=(mean[0, 0], mean[0, 1]), xytext=(x[0, 0], x[0, 1]),
                arrowprops=dict(arrowstyle='->', color=INK, lw=2.0))
    ax.set_xlabel('x (m)', fontsize=9.5)
    ax.set_ylabel('y (m)', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title(f'One step back, from t = {t} to t = {t - 1}',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    ax.axis('off')
    lines = [
        f'the point now        x = ({x[0, 0]:.3f}, {x[0, 1]:.3f}),  t = {t}',
        f'the named noise      e = ({eps[0, 0]:.3f}, {eps[0, 1]:.3f})',
        '',
        f'share removed        beta = {beta:.4f}',
        f'noise still in       sqrt(1 - kept) = {np.sqrt(1 - ab):.4f}',
        f'take out             beta / {np.sqrt(1 - ab):.4f} = {beta / np.sqrt(1 - ab):.4f}',
        '',
        f'x - {beta / np.sqrt(1 - ab):.4f} e = '
        f'({x[0, 0] - beta / np.sqrt(1 - ab) * eps[0, 0]:.3f}, '
        f'{x[0, 1] - beta / np.sqrt(1 - ab) * eps[0, 1]:.3f})',
        f'divide by {np.sqrt(1 - beta):.4f} = ({mean[0, 0]:.3f}, {mean[0, 1]:.3f})',
        '',
        f'put noise back       spread {sig:.4f}',
        f'so the new point is  ({mean[0, 0]:.3f}, {mean[0, 1]:.3f}) '
        f'+ {sig:.3f} x noise',
    ]
    ax.text(0.0, 0.97, '\n'.join(lines), fontsize=11.0, family='monospace',
            va='top', color=INK)
    ax.set_title('The same step written out', fontsize=11.5, weight='bold',
                 color=INK, loc='left')
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'the-step-rule.svg')


# --------------------------------------------------------------------------
# 01_diffusion.md, sections 5 and 6: conditioning and guidance
# --------------------------------------------------------------------------

def _arc_offset(p: Arr) -> Arr:
    """How far each point sits from the upper arc, measured sideways."""
    return p[:, 1] - AMP * np.exp(-(p[:, 0] / WID) ** 2)


def conditioning_input() -> None:
    den = _den()
    x = np.array([[0.62, 1.05]])
    t = 40
    rows = [(ABOVE, 'told to go above'), (BELOW, 'told to go below'),
            (UNTOLD, 'not told at all')]
    fig, ax = plt.subplots(figsize=(13.4, 5.6), facecolor='white')
    ax.axis('off')
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 5.6)
    groups = [(0, 2, 'where the point is\nnow (2 numbers)', LINK),
              (2, 10, 'which step it is, worked out from t = 40 (8 numbers)', TEAL),
              (10, 13, 'what to produce\n(3 numbers)', JOINT)]
    cell = 0.84
    left = 0.6
    for k, (c, label) in enumerate(rows):
        y = 4.0 - k * 1.15
        vec = _dinput(x, np.array([t / T_STEPS]), np.array([c], dtype=np.int64))[0]
        out = den.eps(x, t, c)[0]
        for i, v in enumerate(vec):
            col = next(g[3] for g in groups if g[0] <= i < g[1])
            ax.add_patch(Rectangle((left + i * cell, y), cell * 0.94, 0.62,
                                   facecolor=col, alpha=0.18, edgecolor=col, lw=1.0))
            ax.text(left + i * cell + cell * 0.47, y + 0.31, f'{v:+.2f}',
                    ha='center', va='center', fontsize=8.6, color=INK)
        ax.text(left - 0.15, y + 0.31, label, ha='right', va='center',
                fontsize=10, color=INK)
        ax.annotate('', xy=(left + 13 * cell + 1.0, y + 0.31),
                    xytext=(left + 13 * cell + 0.1, y + 0.31),
                    arrowprops=dict(arrowstyle='->', color=INK, lw=1.6))
        ax.text(left + 13 * cell + 1.1, y + 0.31,
                f'noise named: ({out[0]:+.2f}, {out[1]:+.2f})', va='center',
                fontsize=10, color=GRIP, weight='bold')
        print(f'[s5] input with the condition "{label}": the network names '
              f'({out[0]:+.3f}, {out[1]:+.3f})')
    for a, b, label, col in groups:
        ax.plot([left + a * cell, left + b * cell - cell * 0.06], [4.78, 4.78],
                color=col, lw=2.4)
        ax.text(left + (a + b) / 2 * cell, 4.88, label, ha='center', va='bottom',
                fontsize=9.5, color=col)
    ax.text(0.2, 0.55, f'The same point ({x[0, 0]:.2f}, {x[0, 1]:.2f}) at the same '
            f'step t = {t}. Only the last three numbers change, and the answer '
            'changes with them.', fontsize=10.5, color=INK)
    ax.set_title('What the conditioned denoiser is actually handed: one row of '
                 '13 numbers', fontsize=12.5, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'conditioning-input.svg')


def conditional_samples() -> None:
    d = _data()
    out = {}
    for name, c in (('not told', UNTOLD), ('told above', ABOVE), ('told below', BELOW)):
        pts, _ = _ddpm(1200, c, seed=606)
        frac = float((pts[:, 1] > 0).mean())
        out[name] = (pts, frac)
        print(f'[s5] {name}: {frac * 100:.1f}% of the 1,200 generated waypoints '
              f'went above, inside the obstacle {_in_obstacle(pts) * 100:.2f}%')
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.4), facecolor='white')
    for ax, (name, (pts, frac)) in zip(axes, out.items()):
        _arena(ax, lim=2.4, labels=False)
        s = _show(pts, 900, 12)
        ax.scatter(s[:, 0], s[:, 1], s=6, color=LINK, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(f'{name}\n{frac * 100:.1f}% went above',
                     fontsize=11, weight='bold', color=INK)
    fig.suptitle('The same denoiser, run three times with a different condition '
                 'and nothing else changed', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'conditional-samples.svg')


def guidance_arrows() -> None:
    den = _den()
    x = np.array([[0.0, 0.25]])
    t = 55
    e_u = den.eps(x, t, UNTOLD)[0]
    e_c = den.eps(x, t, ABOVE)[0]
    diff = e_c - e_u
    print(f'[s6] at ({x[0, 0]:.2f}, {x[0, 1]:.2f}) and t = {t}: not told '
          f'({e_u[0]:+.3f}, {e_u[1]:+.3f}), told above ({e_c[0]:+.3f}, '
          f'{e_c[1]:+.3f}), the part the condition adds ({diff[0]:+.3f}, '
          f'{diff[1]:+.3f})')
    fig, ax = plt.subplots(figsize=(8.6, 7.4), facecolor='white')
    _plain(ax)
    lim = max(2.2, float(np.abs(e_u + 4 * diff).max()) * 1.15)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    ax.axhline(0, color=GRID, lw=1.0)
    ax.axvline(0, color=GRID, lw=1.0)
    specs = [(e_u, MUTED, 'not told: the noise it names', 2.6),
             (e_c, LINK, 'told "above": the noise it names', 2.6)]
    for w, col in ((2.0, WRIST), (4.0, GRIP)):
        g = e_u + w * diff
        specs.append((g, col, f'guided with strength {w:.0f}', 2.6))
        print(f'[s6] strength {w:.0f} gives ({g[0]:+.3f}, {g[1]:+.3f}), which is '
              f'{np.hypot(*g):.3f} long against {np.hypot(*e_u):.3f} for the '
              'untold answer')
    for v, col, label, lw in specs:
        ax.annotate('', xy=(v[0], v[1]), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color=col, lw=lw))
        ax.text(v[0] * 1.06, v[1] * 1.06, label, fontsize=9.5, color=col,
                ha='left' if v[0] >= 0 else 'right')
    ax.annotate('', xy=(e_c[0], e_c[1]), xytext=(e_u[0], e_u[1]),
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=2.2, ls='--'))
    ax.text((e_u[0] + e_c[0]) / 2 - 0.1, (e_u[1] + e_c[1]) / 2 + 0.12,
            f'what the condition adds:\n({diff[0]:+.2f}, {diff[1]:+.2f})',
            fontsize=9.5, color=SLIDE, ha='right')
    ax.set_xlabel('x part of the named noise', fontsize=9.5)
    ax.set_ylabel('y part of the named noise', fontsize=9.5)
    ax.set_title(f'Guidance at the single point ({x[0, 0]:.2f}, {x[0, 1]:.2f}), '
                 f'step t = {t}:\nthe gap between the two answers, taken further',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, DIFF_DOC, 'guidance-arrows.svg')


def guidance_sweep() -> None:
    d = _data()
    above_real = d.ref[d.ref_side == ABOVE]
    real_off = float(_arc_offset(above_real).std())
    real_x = float(above_real[:, 0].std())
    ws = (0.0, 0.5, 1.0, 2.0, 4.0)
    fig, axes = plt.subplots(1, 5, figsize=(17.5, 4.6), facecolor='white')
    for ax, w in zip(axes, ws):
        pts, _ = _ddpm(1000, ABOVE, seed=707, w=w)
        frac = float((pts[:, 1] > 0).mean())
        off = float(_arc_offset(pts[pts[:, 1] > 0]).std())
        along = float(pts[:, 0].std())
        mis = _mismatch(pts, above_real)
        print(f'[s6] strength {w:.1f}: {frac * 100:.1f}% above, spread around the '
              f'arc {off:.4f} m, spread along it {along:.3f} m, mismatch against '
              f'the real upper arc {mis:.4f}')
        _arena(ax, lim=2.4, labels=False)
        sh = _show(pts, 700, 13)
        ax.scatter(sh[:, 0], sh[:, 1], s=5, color=LINK, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=8.5)
        ax.set_ylabel('y (m)', fontsize=8.5)
        ax.set_title(f'strength {w:.1f}\n{frac * 100:.0f}% above, spread along '
                     f'{along:.2f} m', fontsize=10, weight='bold', color=INK)
    print(f'[s6] the real upper arc has spread {real_off:.4f} m around itself and '
          f'{real_x:.3f} m along itself')
    fig.suptitle('Turning the guidance strength up: the condition is obeyed sooner, '
                 'and then the variety goes',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'guidance-sweep.svg')


def guidance_tradeoff() -> None:
    d = _data()
    above_real = d.ref[d.ref_side == ABOVE]
    real_off = float(_arc_offset(above_real).std())
    real_x = float(above_real[:, 0].std())
    ws = np.arange(0.0, 4.01, 0.5)
    fracs, offs, alongs, miss = [], [], [], []
    for w in ws:
        pts, _ = _ddpm(600, ABOVE, seed=808, w=float(w))
        fracs.append(float((pts[:, 1] > 0).mean()))
        offs.append(float(_arc_offset(pts[pts[:, 1] > 0]).std()))
        alongs.append(float(pts[:, 0].std()))
        miss.append(_mismatch(pts, above_real))
    fracs = np.array(fracs)
    offs = np.array(offs)
    alongs = np.array(alongs)
    miss = np.array(miss)
    best = float(ws[int(np.argmin(miss))])
    print('[s6] sweep: ' + '; '.join(
        f'w {w:.1f} obeyed {f * 100:.0f}% across {a:.3f} m mismatch {m:.4f}'
        for w, f, a, m in zip(ws, fracs, alongs, miss)))
    print(f'[s6] the lowest mismatch is {miss.min():.4f} at strength {best:.1f}; '
          f'at strength 0 it is {miss[0]:.4f} and at strength 4 it is {miss[-1]:.4f}')
    print(f'[s6] spread along the arc falls from {alongs[ws == 1.0][0]:.3f} m at '
          f'strength 1 to {alongs[-1]:.3f} m at strength 4, while the real data '
          f'has {real_x:.3f} m')

    fig, axes = plt.subplots(1, 3, figsize=(15.4, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(ws, fracs * 100, color=LINK, lw=2.6, marker='o', ms=5)
    ax.axhline(50, color=MUTED, ls='--', lw=1.2)
    ax.text(1.4, 52, 'what no condition at all gives', fontsize=9, color=MUTED)
    ax.set_xlabel('guidance strength', fontsize=9.5)
    ax.set_ylabel('waypoints that went above (%)', fontsize=9.5)
    ax.set_ylim(40, 105)
    ax.set_title('The condition is obeyed more',
                 fontsize=11, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ax.plot(ws, alongs, color=GRIP, lw=2.6, marker='o', ms=5,
            label='spread along the arc')
    ax.plot(ws, offs * 10, color=PURPLE, lw=2.6, marker='s', ms=5,
            label='spread across it, times 10')
    ax.axhline(real_x, color=GRIP, ls='--', lw=1.3)
    ax.axhline(real_off * 10, color=PURPLE, ls='--', lw=1.3)
    ax.text(0.05, real_x + 0.03, f'real: {real_x:.3f} m', fontsize=9, color=GRIP)
    ax.text(0.05, real_off * 10 + 0.03, f'real: {real_off:.3f} m', fontsize=9,
            color=PURPLE)
    ax.set_xlabel('guidance strength', fontsize=9.5)
    ax.set_ylabel('spread of the generated waypoints (m)', fontsize=9.5)
    ax.set_ylim(0, max(alongs.max(), real_x) * 1.3)
    ax.legend(fontsize=9, frameon=False, loc='lower left')
    ax.set_title('But the variety goes with it',
                 fontsize=11, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    ax.plot(ws, miss, color=SLIDE, lw=2.6, marker='o', ms=5)
    ax.plot([best], [miss.min()], marker='o', ms=11, color=INK)
    ax.text(best + 0.12, miss.min() * 1.6,
            f'best at strength {best:.1f}\nmismatch {miss.min():.4f}',
            fontsize=9.5, color=INK)
    ax.set_yscale('log')
    ax.set_xlabel('guidance strength', fontsize=9.5)
    ax.set_ylabel('mismatch against the real upper arc', fontsize=9.5)
    ax.set_title('So there is one best setting,\nand it is not the largest one',
                 fontsize=11, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'guidance-tradeoff.svg')


# --------------------------------------------------------------------------
# 01_diffusion.md, section 7: the cost
# --------------------------------------------------------------------------

STEP_COUNTS: tuple[int, ...] = (2, 5, 10, 25, 50, 100)


def _ddim_quality() -> dict[int, tuple[float, float, float]]:
    d = _data()
    out = {}
    for n in STEP_COUNTS:
        pts, _ = _ddim(1500, UNTOLD, seed=909, steps=n)
        out[n] = (_mismatch(pts, d.ref), _nearest(pts, d.ref), _in_obstacle(pts))
    return out


DQ: dict[int, tuple[float, float, float]] | None = None


def _dq() -> dict[int, tuple[float, float, float]]:
    global DQ
    if DQ is None:
        DQ = _ddim_quality()
    return DQ


def _pass_time(batch: int, repeats: int = 40) -> float:
    """Measured seconds for one pass of the denoiser over a batch of points."""
    den = _den()
    x = np.zeros((batch, 2))
    den.eps(x, 50, UNTOLD)
    best = []
    for _ in range(repeats):
        start = time.perf_counter()
        den.eps(x, 50, UNTOLD)
        best.append(time.perf_counter() - start)
    return float(np.median(best))


def steps_vs_error() -> None:
    d = _data()
    q = _dq()
    for n in STEP_COUNTS:
        print(f'[s7] {n:3d} steps: mismatch {q[n][0]:.4f}, nearest real point '
              f'{q[n][1]:.4f} m, inside the obstacle {q[n][2] * 100:.2f}%')
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(STEP_COUNTS, [q[n][0] for n in STEP_COUNTS], color=LINK, lw=2.6,
            marker='o', ms=6)
    ax.axhline(d.floor, color=MUTED, ls='--', lw=1.3)
    ax.text(30, d.floor * 1.6, f'real against real: {d.floor:.4f}', fontsize=9.5,
            color=MUTED)
    for n in STEP_COUNTS:
        ax.text(n, q[n][0] * 1.12, f'{q[n][0]:.3f}', ha='center', fontsize=9,
                color=LINK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(STEP_COUNTS)
    ax.set_xticklabels([str(n) for n in STEP_COUNTS])
    ax.set_xlabel('number of steps used to generate', fontsize=9.5)
    ax.set_ylabel('mismatch score (lower is better)', fontsize=9.5)
    ax.set_title('Fewer steps, worse points', fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    vals = [q[n][2] * 100 for n in STEP_COUNTS]
    bars = ax.bar([str(n) for n in STEP_COUNTS], vals, color=GRIP, width=0.6,
                  edgecolor=INK, lw=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, f'{v:.2f}%',
                ha='center', fontsize=10, color=INK)
    ax.set_ylim(0, max(vals) * 1.25 + 0.01)
    ax.set_xlabel('number of steps used to generate', fontsize=9.5)
    ax.set_ylabel('generated waypoints inside the obstacle (%)', fontsize=9.5)
    ax.set_title('And the mistakes land where they matter',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'steps-vs-error.svg')


def samples_at_few_steps() -> None:
    q = _dq()
    shown = (2, 5, 10, 25, 100)
    fig, axes = plt.subplots(1, 5, figsize=(17.5, 4.4), facecolor='white')
    for ax, n in zip(axes, shown):
        pts, _ = _ddim(900, UNTOLD, seed=909, steps=n)
        _arena(ax, lim=2.6, labels=False)
        ax.scatter(pts[:, 0], pts[:, 1], s=5, color=SLIDE, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=8.5)
        ax.set_ylabel('y (m)', fontsize=8.5)
        ax.set_title(f'{n} steps\nmismatch {q[n][0]:.3f}', fontsize=10.5,
                     weight='bold', color=INK)
    fig.suptitle('The same model, asked for its answer in fewer and fewer steps',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'samples-at-few-steps.svg')


def steps_vs_time() -> None:
    one = _pass_time(1)
    many = _pass_time(64)
    print(f'[s7] one pass of this denoiser over a single point takes '
          f'{one * 1e6:.1f} microseconds, and over 64 points at once '
          f'{many * 1e6:.1f} microseconds')
    rows = []
    for n in STEP_COUNTS:
        rows.append((n, n * one * 1e3, n * many * 1e3))
        print(f'[s7] {n:3d} steps: {n * one * 1e3:.3f} ms for one point, '
              f'{n * many * 1e3:.3f} ms for 64 points')

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot([r[0] for r in rows], [r[1] for r in rows], color=LINK, lw=2.4,
            marker='o', ms=6, label='one point at a time')
    ax.plot([r[0] for r in rows], [r[2] for r in rows], color=SLIDE, lw=2.4,
            marker='s', ms=6, label='64 points at once')
    ax.set_xlabel('number of steps', fontsize=9.5)
    ax.set_ylabel('measured time to generate (ms)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('Time grows in a straight line with the number of steps,\n'
                 'because each step is one full pass of the network',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    steps = np.arange(1, 101)
    for per, col in ((0.5, TEAL), (1.0, LINK), (2.0, WRIST), (5.0, GRIP)):
        ax.plot(steps, steps * per, color=col, lw=2.2,
                label=f'{per:.1f} ms for one pass')
    ax.axhline(100.0, color=INK, ls='--', lw=1.6)
    ax.text(2, 106, 'the whole budget at 10 commands a second (100 ms)',
            fontsize=9.5, color=INK)
    ax.axhline(33.3, color=MUTED, ls='--', lw=1.6)
    ax.text(2, 36, 'the whole budget at 30 commands a second (33 ms)',
            fontsize=9.5, color=MUTED)
    ax.set_ylim(0, 160)
    ax.set_xlabel('number of steps', fontsize=9.5)
    ax.set_ylabel('time to generate one action (ms)', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('The same arithmetic for networks of four different speeds',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, DIFF_DOC, 'steps-vs-time.svg')


# ==========================================================================
# 02_flow-matching-and-other-generators.md
# ==========================================================================

FLOW_STEPS: int = 12000


class Flow:
    """A network trained to name the direction to move at a point and a time."""

    def __init__(self) -> None:
        d = _data()
        rng = np.random.default_rng(111)
        self.net = MLP([2 + 8 + 3, HIDDEN, HIDDEN, 2], seed=22)

        def batches(_it: int) -> tuple[Arr, Arr]:
            idx = rng.integers(0, len(d.train), 512)
            x1 = d.train[idx]
            c = d.train_side[idx].copy()
            c[rng.uniform(size=len(c)) < 0.2] = UNTOLD
            x0 = rng.normal(size=x1.shape)
            t = rng.uniform(size=len(idx))
            xt = (1.0 - t)[:, None] * x0 + t[:, None] * x1
            return _dinput(xt, t, c), x1 - x0

        _, self.hist, self.train_seconds = _cached(
            'flow', self.net, lambda: _adam(self.net, batches, FLOW_STEPS, 2e-3))

    def vel(self, x: Arr, t: float, c: int) -> Arr:
        n = len(x)
        return self.net.run(_dinput(x, np.full(n, t),
                                    np.full(n, c, dtype=np.int64)))


FLOW: Flow | None = None


def _flow() -> Flow:
    global FLOW
    if FLOW is None:
        FLOW = Flow()
    return FLOW


def _flow_sample(n: int, c: int, seed: int, steps: int) -> tuple[Arr, Arr]:
    f = _flow()
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    path = [x.copy()]
    dt = 1.0 / steps
    for i in range(steps):
        x = x + dt * f.vel(x, i * dt, c)
        path.append(x.copy())
    return x, np.array(path)


def _straightness(path: Arr) -> float:
    lengths = np.sqrt(((path[1:] - path[:-1]) ** 2).sum(-1)).sum(0)
    direct = np.sqrt(((path[-1] - path[0]) ** 2).sum(-1))
    return float(np.mean(lengths / np.maximum(direct, 1e-9)))


def flow_pairing() -> None:
    d = _data()
    rng = np.random.default_rng(1212)
    f = _flow()
    x1 = np.array([[0.30, 1.40]])
    x0 = np.array([[-1.20, -0.90]])
    t = 0.5
    xt = (1 - t) * x0 + t * x1
    target = x1 - x0
    named = f.vel(xt, t, UNTOLD)
    print(f'[p2s1] the pair: noise point ({x0[0, 0]:.2f}, {x0[0, 1]:.2f}) and '
          f'data point ({x1[0, 0]:.2f}, {x1[0, 1]:.2f}); halfway is '
          f'({xt[0, 0]:.2f}, {xt[0, 1]:.2f}) and the direction asked for is '
          f'({target[0, 0]:+.2f}, {target[0, 1]:+.2f})')
    print(f'[p2s1] the trained network names ({named[0, 0]:+.3f}, '
          f'{named[0, 1]:+.3f}) there')

    fig, ax = plt.subplots(figsize=(8.2, 7.4), facecolor='white')
    _arena(ax, lim=2.6)
    sh = _show(d.train, 600, 14)
    ax.scatter(sh[:, 0], sh[:, 1], s=5, color=GRID, alpha=0.9)
    extra = rng.normal(size=(5, 2))
    picks = d.train[rng.integers(0, len(d.train), 5)]
    for a, b in zip(extra, picks):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=LINK_PALE, lw=1.2, zorder=1)
        ax.plot(a[0], a[1], marker='o', ms=4, color=LINK_PALE)
    ax.plot([x0[0, 0], x1[0, 0]], [x0[0, 1], x1[0, 1]], color=INK, lw=2.0, zorder=2)
    ax.plot(x0[0, 0], x0[0, 1], marker='o', ms=10, color=PURPLE, zorder=4)
    ax.text(x0[0, 0] - 0.1, x0[0, 1] - 0.3, 'a point of plain noise\n(where t = 0)',
            fontsize=9.5, color=PURPLE, ha='center')
    ax.plot(x1[0, 0], x1[0, 1], marker='*', ms=17, color=LINK, zorder=4)
    ax.text(x1[0, 0] + 0.12, x1[0, 1] + 0.1, 'a real waypoint\n(where t = 1)',
            fontsize=9.5, color=LINK)
    ax.plot(xt[0, 0], xt[0, 1], marker='X', ms=13, color=GRIP, zorder=5)
    ax.text(xt[0, 0] - 1.45, xt[0, 1] + 0.05,
            f'halfway, t = {t:.1f}\n({xt[0, 0]:.2f}, {xt[0, 1]:.2f})',
            fontsize=9.5, color=GRIP)
    ax.annotate('', xy=(xt[0, 0] + target[0, 0] * 0.45,
                        xt[0, 1] + target[0, 1] * 0.45),
                xytext=(xt[0, 0], xt[0, 1]),
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=2.6))
    ax.text(xt[0, 0] + 0.25, xt[0, 1] - 0.45,
            f'the direction it must name:\n({target[0, 0]:+.2f}, {target[0, 1]:+.2f})',
            fontsize=9.5, color=SLIDE)
    ax.set_title('One training example for flow matching: join a noise point to a\n'
                 'real waypoint, stand somewhere on the line, name the direction',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'flow-pairing.svg')


def vector_field_arrows() -> None:
    d = _data()
    f = _flow()
    grid = np.linspace(-2.4, 2.4, 13)
    gx, gy = np.meshgrid(grid, grid)
    pts = np.stack([gx.ravel(), gy.ravel()], axis=1)
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.4), facecolor='white')
    for ax, t in zip(axes, (0.15, 0.50, 0.85)):
        v = f.vel(pts, t, UNTOLD)
        _arena(ax, lim=2.7, obstacle=False, labels=False)
        sh = _show(d.train, 500, 15)
        ax.scatter(sh[:, 0], sh[:, 1], s=4, color=GRID, alpha=0.9)
        ax.quiver(pts[:, 0], pts[:, 1], v[:, 0], v[:, 1], color=LINK,
                  angles='xy', scale_units='xy', scale=3.0, width=0.005)
        print(f'[p2s1] at t = {t:.2f} the arrows are on average '
              f'{np.hypot(v[:, 0], v[:, 1]).mean():.3f} long, '
              f'longest {np.hypot(v[:, 0], v[:, 1]).max():.3f}')
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(f't = {t:.2f}: average arrow '
                     f'{np.hypot(v[:, 0], v[:, 1]).mean():.2f} m long',
                     fontsize=10.5, weight='bold', color=INK)
    fig.suptitle('The vector field the model learned: at every place, at three '
                 'different times,\none arrow saying which way to move',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'vector-field-arrows.svg')


def flow_paths() -> None:
    d = _data()
    _, path = _flow_sample(10, UNTOLD, seed=1313, steps=50)
    straight = _straightness(path)
    print(f'[p2s1] ten flow paths travel on average {straight:.3f} times the '
          'straight-line distance from start to finish')
    fig, ax = plt.subplots(figsize=(8.0, 7.4), facecolor='white')
    _arena(ax, lim=3.0)
    sh = _show(d.train, 600, 16)
    ax.scatter(sh[:, 0], sh[:, 1], s=5, color=GRID, alpha=0.9)
    cols = [LINK, SLIDE, GRIP, PURPLE, TEAL, WRIST, JOINT, '#9c3fb3', '#3f7fb3',
            '#b3863f']
    for k in range(path.shape[1]):
        ax.plot(path[:, k, 0], path[:, k, 1], color=cols[k], lw=1.4)
        ax.plot(path[0, k, 0], path[0, k, 1], marker='o', ms=5, color=cols[k])
        ax.plot(path[-1, k, 0], path[-1, k, 1], marker='*', ms=13, color=cols[k])
    ax.text(-2.85, 2.6, 'circle: the noise point it started from\n'
                        'star: the waypoint it ended on', fontsize=9.5, color=INK)
    ax.set_title('Ten points carried from noise to the arcs by following the arrows,\n'
                 f'each travelling {straight:.2f} times the straight-line distance',
                 fontsize=11.5, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'flow-paths.svg')


def straightness_compare() -> None:
    d = _data()
    _, fpath = _flow_sample(300, UNTOLD, seed=1414, steps=50)
    _, dpath = _ddim(300, UNTOLD, seed=1414, steps=50)
    fs, ds = _straightness(fpath), _straightness(dpath)
    print(f'[p2s1] over 300 paths: flow matching {fs:.3f}, diffusion {ds:.3f} '
          'times the straight-line distance')
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.4), facecolor='white')
    for ax, path, name, col, val in (
            (axes[0], dpath, 'diffusion, walking the noise back', PURPLE, ds),
            (axes[1], fpath, 'flow matching, following the arrows', SLIDE, fs)):
        _arena(ax, lim=3.0, labels=False)
        sh = _show(d.train, 400, 17)
        ax.scatter(sh[:, 0], sh[:, 1], s=4, color=GRID, alpha=0.9)
        for k in range(12):
            ax.plot(path[:, k, 0], path[:, k, 1], color=col, lw=1.2, alpha=0.8)
            ax.plot(path[0, k, 0], path[0, k, 1], marker='o', ms=4, color=col)
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(f'{name}\npath is {val:.2f} times the straight line',
                     fontsize=10.5, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    bars = ax.bar(['diffusion', 'flow matching'], [ds, fs], color=[PURPLE, SLIDE],
                  width=0.5, edgecolor=INK, lw=0.6)
    ax.axhline(1.0, color=MUTED, ls='--', lw=1.4)
    ax.text(-0.45, 1.02, 'a perfectly straight path', fontsize=9.5, color=MUTED)
    for b, v in zip(bars, [ds, fs]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f'{v:.2f}', ha='center',
                fontsize=12, weight='bold', color=INK)
    ax.set_ylim(0.9, max(ds, fs) * 1.18)
    ax.set_ylabel('distance travelled, divided by the straight line', fontsize=9.5)
    ax.set_title('How bent each path is', fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'straightness-compare.svg')


# --------------------------------------------------------------------------
# page 2, section 2: straight paths need fewer steps
# --------------------------------------------------------------------------

FEW: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)


class StepSweep:
    """The measured error of both generators at each number of steps."""

    def __init__(self) -> None:
        d = _data()
        self.flow: dict[int, float] = {}
        self.diff: dict[int, float] = {}
        self.flow_pts: dict[int, Arr] = {}
        self.diff_pts: dict[int, Arr] = {}
        for n in FEW:
            fp, _ = _flow_sample(1500, UNTOLD, seed=1515, steps=n)
            dp, _ = _ddim(1500, UNTOLD, seed=1515, steps=n)
            self.flow[n] = _mismatch(fp, d.ref)
            self.diff[n] = _mismatch(dp, d.ref)
            self.flow_pts[n] = fp
            self.diff_pts[n] = dp


SWEEP: StepSweep | None = None


def _sweep() -> StepSweep:
    global SWEEP
    if SWEEP is None:
        SWEEP = StepSweep()
    return SWEEP


def steps_vs_error_both() -> None:
    d = _data()
    s = _sweep()
    for n in FEW:
        print(f'[p2s2] {n:3d} steps: flow {s.flow[n]:.4f}, diffusion '
              f'{s.diff[n]:.4f}')
    target = 0.01
    f_need = min((n for n in FEW if s.flow[n] <= target), default=None)
    d_need = min((n for n in FEW if s.diff[n] <= target), default=None)
    print(f'[p2s2] to get the mismatch under {target}, flow needs {f_need} steps '
          f'and diffusion needs {d_need}')

    fig, ax = plt.subplots(figsize=(10.2, 5.6), facecolor='white')
    _plain(ax)
    ax.plot(FEW, [s.diff[n] for n in FEW], color=PURPLE, lw=2.6, marker='o', ms=6,
            label='diffusion, walking the noise back')
    ax.plot(FEW, [s.flow[n] for n in FEW], color=SLIDE, lw=2.6, marker='s', ms=6,
            label='flow matching, following the arrows')
    ax.axhline(d.floor, color=MUTED, ls='--', lw=1.3)
    ax.text(1.1, d.floor * 1.5, f'real against real: {d.floor:.4f}', fontsize=9.5,
            color=MUTED)
    for n in FEW:
        ax.text(n, s.flow[n] * 0.62, f'{s.flow[n]:.3f}', ha='center', fontsize=8.5,
                color=SLIDE)
        ax.text(n, s.diff[n] * 1.3, f'{s.diff[n]:.3f}', ha='center', fontsize=8.5,
                color=PURPLE)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(FEW)
    ax.set_xticklabels([str(n) for n in FEW])
    ax.set_xlabel('number of steps used to generate', fontsize=9.5)
    ax.set_ylabel('mismatch score (lower is better)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('The same job, the same network size, the same data:\n'
                 'flow matching gets there in far fewer steps',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'steps-vs-error-both.svg')


def few_step_panels() -> None:
    s = _sweep()
    shown = (1, 2, 4, 8)
    fig, axes = plt.subplots(2, 4, figsize=(15.0, 8.0), facecolor='white')
    for col, n in enumerate(shown):
        for row, (pts, name, colour) in enumerate((
                (s.diff_pts[n], 'diffusion', PURPLE),
                (s.flow_pts[n], 'flow matching', SLIDE))):
            ax = axes[row, col]
            _arena(ax, lim=2.8, labels=False)
            ax.scatter(pts[:900, 0], pts[:900, 1], s=5, color=colour, alpha=0.55)
            ax.set_xlabel('x (m)', fontsize=8.5)
            ax.set_ylabel('y (m)', fontsize=8.5)
            score = s.diff[n] if row == 0 else s.flow[n]
            ax.set_title(f'{name}, {n} step{"s" if n > 1 else ""}\n'
                         f'mismatch {score:.3f}', fontsize=10, weight='bold',
                         color=INK)
    fig.suptitle('One, two, four and eight steps, drawn from the same starting noise',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'few-step-panels.svg')


def error_at_fixed_steps() -> None:
    s = _sweep()
    pairs = [(2, s.diff[2], s.flow[2]), (4, s.diff[4], s.flow[4]),
             (16, s.diff[16], s.flow[16]), (64, s.diff[64], s.flow[64])]
    print('[p2s2] side by side: ' + '; '.join(
        f'{n} steps diffusion {a:.4f} flow {b:.4f} '
        f'({a / b:.1f} times worse)' for n, a, b in pairs))
    fig, ax = plt.subplots(figsize=(10.0, 5.4), facecolor='white')
    _plain(ax)
    idx = np.arange(len(pairs))
    ax.bar(idx - 0.19, [p[1] for p in pairs], width=0.36, color=PURPLE,
           edgecolor=INK, lw=0.6, label='diffusion')
    ax.bar(idx + 0.19, [p[2] for p in pairs], width=0.36, color=SLIDE,
           edgecolor=INK, lw=0.6, label='flow matching')
    for i, (_n, a, b) in enumerate(pairs):
        ax.text(i - 0.19, a * 1.15, f'{a:.3f}', ha='center', fontsize=9, color=INK)
        ax.text(i + 0.19, b * 1.15, f'{b:.3f}', ha='center', fontsize=9, color=INK)
    ax.set_yscale('log')
    ax.set_xticks(idx)
    ax.set_xticklabels([f'{p[0]} steps' for p in pairs])
    ax.set_ylabel('mismatch score (lower is better)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('The gap is largest where it matters most, at the smallest '
                 'step counts', fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'error-at-fixed-steps.svg')


def time_to_quality() -> None:
    s = _sweep()
    one = _pass_time(1)
    print(f'[p2s2] one pass over a single point takes {one * 1e6:.1f} microseconds, '
          'and both models are the same size')
    for n in FEW:
        print(f'[p2s2] {n:3d} steps costs {n * one * 1e3:.3f} ms: flow '
              f'{s.flow[n]:.4f}, diffusion {s.diff[n]:.4f}')
    fig, ax = plt.subplots(figsize=(10.2, 5.6), facecolor='white')
    _plain(ax)
    times = np.array(FEW) * one * 1e3
    ax.plot(times, [s.diff[n] for n in FEW], color=PURPLE, lw=2.6, marker='o',
            ms=6, label='diffusion')
    ax.plot(times, [s.flow[n] for n in FEW], color=SLIDE, lw=2.6, marker='s',
            ms=6, label='flow matching')
    for n, tm in zip(FEW, times):
        ax.text(tm, s.flow[n] * 0.62, f'{n}', ha='center', fontsize=9, color=SLIDE)
        ax.text(tm, s.diff[n] * 1.3, f'{n}', ha='center', fontsize=9, color=PURPLE)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('measured time to generate one waypoint (ms)', fontsize=9.5)
    ax.set_ylabel('mismatch score (lower is better)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('The same picture read as a budget: the number beside each point\n'
                 'is the step count that bought that time',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'time-to-quality.svg')


# --------------------------------------------------------------------------
# page 2, section 3: generating one piece at a time
# --------------------------------------------------------------------------

NBIN: int = 20
XLO, XHI, YLO, YHI = -1.9, 1.9, -2.0, 2.0


class AutoReg:
    """A two-stage model: first the x of the waypoint, then its y given that x."""

    def __init__(self) -> None:
        d = _data()
        self.xe = np.linspace(XLO, XHI, NBIN + 1)
        self.ye = np.linspace(YLO, YHI, NBIN + 1)
        xi = np.clip(np.digitize(d.train[:, 0], self.xe) - 1, 0, NBIN - 1)
        yi = np.clip(np.digitize(d.train[:, 1], self.ye) - 1, 0, NBIN - 1)
        self.px = np.bincount(xi, minlength=NBIN).astype(float)
        self.px /= self.px.sum()
        self.pyx = np.zeros((NBIN, NBIN))
        for a, b in zip(xi, yi):
            self.pyx[a, b] += 1.0
        self.counts = self.pyx.sum(1)
        self.pyx = self.pyx / np.maximum(self.counts[:, None], 1.0)

    def draw(self, n: int, seed: int) -> Arr:
        rng = np.random.default_rng(seed)
        a = rng.choice(NBIN, size=n, p=self.px)
        b = np.array([rng.choice(NBIN, p=self.pyx[k]) for k in a])
        x = self.xe[a] + rng.uniform(size=n) * (self.xe[1] - self.xe[0])
        y = self.ye[b] + rng.uniform(size=n) * (self.ye[1] - self.ye[0])
        return np.stack([x, y], axis=1)


AR: AutoReg | None = None


def _ar() -> AutoReg:
    global AR
    if AR is None:
        AR = AutoReg()
    return AR


def autoregressive_pieces() -> None:
    a = _ar()
    mids = (a.xe[:-1] + a.xe[1:]) / 2
    print(f'[p2s3] the first piece is a list of {NBIN} chances; the busiest '
          f'band is x around {mids[int(np.argmax(a.px))]:+.2f} m with '
          f'{a.px.max() * 100:.1f}% of the waypoints')
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.bar(mids, a.px * 100, width=(a.xe[1] - a.xe[0]) * 0.9, color=LINK,
           edgecolor=INK, lw=0.5)
    ax.set_xlabel('forward position x of the waypoint (m)', fontsize=9.5)
    ax.set_ylabel('chance of landing in this band (%)', fontsize=9.5)
    ax.set_title('Piece one: the chance of each band of x,\n'
                 'counted from the 6,000 training waypoints',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ymids = (a.ye[:-1] + a.ye[1:]) / 2
    for k, col in ((NBIN // 2, LINK), (NBIN // 2 + 5, SLIDE), (1, GRIP)):
        ax.plot(ymids, a.pyx[k] * 100, color=col, lw=2.4, marker='o', ms=4,
                label=f'x near {mids[k]:+.2f} m ({int(a.counts[k])} waypoints)')
        peaks = ymids[a.pyx[k] > 0.08]
        print(f'[p2s3] with x near {mids[k]:+.2f} m, the chances for y peak at '
              + ', '.join(f'{p:+.2f}' for p in peaks) + ' m')
    ax.set_xlabel('sideways position y of the waypoint (m)', fontsize=9.5)
    ax.set_ylabel('chance given the x already chosen (%)', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('Piece two: the chance of each band of y,\n'
                 'once the x has been chosen',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'autoregressive-pieces.svg')


def autoregressive_samples() -> None:
    d = _data()
    a = _ar()
    gen = a.draw(1500, seed=1616)
    mis = _mismatch(gen, d.ref)
    s = _sweep()
    print(f'[p2s3] the two-stage model scores {mis:.4f}, against {s.flow[8]:.4f} '
          f'for flow matching with 8 steps and a floor of {d.floor:.4f}')
    print(f'[p2s3] it puts {_in_obstacle(gen) * 100:.2f}% of its waypoints inside '
          'the obstacle')
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.2), facecolor='white')
    for ax, pts, name, col in ((axes[0], d.ref, 'real demonstrations', LINK),
                               (axes[1], gen, 'one piece at a time', WRIST)):
        _arena(ax, lim=2.4, labels=False)
        sh = _show(pts, 900, 18)
        ax.scatter(sh[:, 0], sh[:, 1], s=6, color=col, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=9)
        ax.set_ylabel('y (m)', fontsize=9)
        ax.set_title(name, fontsize=10.5, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    names = ['real against\nreal', 'one piece\nat a time', 'flow matching,\n8 steps']
    vals = [d.floor, mis, s.flow[8]]
    bars = ax.bar(names, vals, color=[MUTED, WRIST, SLIDE], width=0.55,
                  edgecolor=INK, lw=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, f'{v:.4f}',
                ha='center', fontsize=10, weight='bold', color=INK)
    ax.set_ylim(0, max(vals) * 1.3)
    ax.set_ylabel('mismatch score', fontsize=9.5)
    ax.set_title('Good enough here, because the\nwaypoint has only two pieces',
                 fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'autoregressive-samples.svg')


def autoregressive_cost() -> None:
    one = _pass_time(1)
    pieces = np.arange(1, 65)
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(pieces, pieces * one * 1e3, color=WRIST, lw=2.6,
            label='one piece at a time: one pass per piece')
    for n, col, ls in ((4, SLIDE, '-'), (50, PURPLE, '--')):
        ax.axhline(n * one * 1e3, color=col, lw=2.0, ls=ls,
                   label=f'{n} steps of a flow or diffusion model')
    ax.set_xlabel('how many pieces the answer has', fontsize=9.5)
    ax.set_ylabel('measured time to generate one answer (ms)', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('Cost one piece at a time grows with the answer,\n'
                 'while a flow model pays the same whatever its size',
                 fontsize=11.5, weight='bold', color=INK)
    print(f'[p2s3] a 2-piece answer costs {2 * one * 1e3:.3f} ms one piece at a '
          f'time, a 16-piece answer {16 * one * 1e3:.3f} ms and a 64-piece answer '
          f'{64 * one * 1e3:.3f} ms, while 4 flow steps cost '
          f'{4 * one * 1e3:.3f} ms whatever the size')
    ax = axes[1]
    _plain(ax)
    ax.axis('off')
    order = ['choose x from the 20 chances', 'now fix x, and look up the 20',
             'chances for y that go with it', 'choose y from those',
             '', 'two pieces, so two passes', '',
             'a 16-number arm trajectory would', 'need 16 passes, in order,',
             'and none of them can be started', 'before the one before it is done']
    ax.text(0.02, 0.95, '\n'.join(order), fontsize=12, va='top', color=INK,
            family='monospace')
    ax.set_title('Why the pieces cannot be done at the same time',
                 fontsize=11.5, weight='bold', color=INK, loc='left')
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'autoregressive-cost.svg')


# --------------------------------------------------------------------------
# page 2, section 4: generating in a small space
# --------------------------------------------------------------------------

NT: int = 16            # how many sideways readings make up one trajectory
XS: Arr = np.linspace(-1.7, 1.7, NT)


def _traj(n: int, rng: np.random.Generator) -> tuple[Arr, NDArray[np.int64]]:
    """n whole demonstrations, each one 16 sideways readings along the path."""
    side = rng.integers(0, 2, n)
    sign = 1.0 - 2.0 * side
    amp = rng.uniform(1.0, 1.8, n)
    wide = rng.uniform(0.6, 1.1, n)
    y = (sign * amp)[:, None] * np.exp(-(XS[None, :] / wide[:, None]) ** 2)
    return y + rng.normal(0.0, 0.03, (n, NT)), side


class Squeeze:
    """An autoencoder: 16 numbers in, a code of k numbers, 16 numbers out."""

    def __init__(self, k: int, steps: int = 7000, seed: int = 30) -> None:
        rng = np.random.default_rng(seed)
        self.k = k
        self.train, self.side = _traj(4000, rng)
        self.test, self.test_side = _traj(1000, rng)
        self.net = MLP([NT, 64, k, 64, NT], seed=seed)

        def batches(_it: int) -> tuple[Arr, Arr]:
            idx = rng.integers(0, len(self.train), 256)
            return self.train[idx], self.train[idx]

        _, self.hist, self.secs = _cached(
            f'squeeze{k}', self.net, lambda: _adam(self.net, batches, steps, 3e-3))
        self.error = float(np.mean((self.net.run(self.test) - self.test) ** 2))

    def code(self, x: Arr) -> Arr:
        return self.net.acts(x)[2]

    def decode(self, z: Arr) -> Arr:
        a = z
        for i in (2, 3):
            za = a @ self.net.p[2 * i] + self.net.p[2 * i + 1]
            a = np.tanh(za) if i < self.net.n - 1 else za
        return a


SQ: dict[int, Squeeze] = {}


def _sq(k: int) -> Squeeze:
    if k not in SQ:
        SQ[k] = Squeeze(k)
    return SQ[k]


def trajectory_dataset() -> None:
    s = _sq(2)
    print(f'[p2s4] the trajectory set holds {len(s.train)} demonstrations, each '
          f'{NT} numbers long, so one demonstration is a point in {NT} dimensions')
    print(f'[p2s4] each one is really made from 3 choices: which side, how far '
          f'out, how wide')
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for k in range(40):
        ax.plot(XS, s.train[k], color=LINK if s.side[k] == 0 else SLIDE, lw=1.0,
                alpha=0.8)
    ax.axhline(0, color=MUTED, lw=1.0)
    ax.set_xlabel('forward position x (m)', fontsize=9.5)
    ax.set_ylabel('sideways position y (m)', fontsize=9.5)
    ax.set_title(f'40 whole demonstrations, each {NT} numbers long',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    one = s.train[0]
    ax.bar(np.arange(NT), one, color=LINK, edgecolor=INK, lw=0.5)
    for i in (0, 7, 8, 15):
        ax.text(i, one[i] + 0.06 * np.sign(one[i] + 1e-9), f'{one[i]:+.2f}',
                ha='center', fontsize=8.5, color=INK)
    ax.set_xticks(np.arange(NT))
    ax.set_xticklabels([f'{i + 1}' for i in range(NT)], fontsize=8)
    ax.set_xlabel('which of the 16 readings', fontsize=9.5)
    ax.set_ylabel('sideways position y (m)', fontsize=9.5)
    ax.set_title('One of them written out as its 16 numbers',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'trajectory-dataset.svg')


def autoencoder_reconstruction() -> None:
    s = _sq(2)
    out = s.net.run(s.test)
    worst = int(np.argmax(((out - s.test) ** 2).mean(1)))
    print(f'[p2s4] with a code of 2 numbers the average squared error on held-out '
          f'demonstrations is {s.error:.5f} m^2, which is {np.sqrt(s.error):.4f} m '
          'of typical error on each reading')
    print(f'[p2s4] the worst of the 1,000 held-out demonstrations is out by '
          f'{np.sqrt(((out[worst] - s.test[worst]) ** 2).mean()):.4f} m')
    fig, axes = plt.subplots(1, 3, figsize=(14.6, 5.0), facecolor='white')
    for ax, idx in zip(axes, (0, 1, worst)):
        _plain(ax)
        z = s.code(s.test[idx:idx + 1])[0]
        ax.plot(XS, s.test[idx], color=LINK, lw=2.4, marker='o', ms=4,
                label='the real demonstration')
        ax.plot(XS, out[idx], color=GRIP, lw=2.0, ls='--', marker='s', ms=4,
                label='rebuilt from its 2-number code')
        err = float(np.sqrt(np.mean((out[idx] - s.test[idx]) ** 2)))
        ax.set_xlabel('forward position x (m)', fontsize=9)
        ax.set_ylabel('sideways position y (m)', fontsize=9)
        ax.legend(fontsize=8.5, frameon=False, loc='lower center')
        ax.set_title(f'code ({z[0]:+.2f}, {z[1]:+.2f})\ntypical error {err:.3f} m',
                     fontsize=10.5, weight='bold', color=INK)
    fig.suptitle('16 numbers squeezed into 2 and built back up, '
                 'for two ordinary demonstrations and the worst one',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'autoencoder-reconstruction.svg')


def code_size_vs_error() -> None:
    ks = (1, 2, 3, 4, 8)
    errs = []
    for k in ks:
        e = _sq(k).error
        errs.append(e)
        print(f'[p2s4] a code of {k} number{"s" if k > 1 else ""}: average squared '
              f'error {e:.5f} m^2, typical error {np.sqrt(e):.4f} m')
    fig, ax = plt.subplots(figsize=(9.8, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(ks, np.sqrt(errs), color=PURPLE, lw=2.6, marker='o', ms=7)
    for k, e in zip(ks, errs):
        ax.text(k, np.sqrt(e) * 1.1, f'{np.sqrt(e):.3f} m', ha='center',
                fontsize=9.5, color=PURPLE)
    ax.axvline(3, color=MUTED, ls='--', lw=1.4)
    ax.text(3.1, max(np.sqrt(errs)) * 0.6,
            'three real choices went into\neach demonstration', fontsize=9.5,
            color=MUTED)
    ax.set_yscale('log')
    ax.set_xticks(ks)
    ax.set_xlabel('how many numbers the code has', fontsize=9.5)
    ax.set_ylabel('typical error of the rebuilt demonstration (m)', fontsize=9.5)
    ax.set_title('The code only has to be as big as the data really is:\n'
                 'past three numbers almost nothing is gained',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'code-size-vs-error.svg')


class LatentFlow:
    """A flow-matching model trained on the 2-number codes, not on the 16 numbers."""

    def __init__(self) -> None:
        s = _sq(2)
        self.codes = s.code(s.train)
        self.mean = self.codes.mean(0)
        self.sd = self.codes.std(0)
        z = (self.codes - self.mean) / self.sd
        rng = np.random.default_rng(141)
        self.net = MLP([2 + 8, 64, 64, 2], seed=41)

        def batches(_it: int) -> tuple[Arr, Arr]:
            idx = rng.integers(0, len(z), 256)
            z1 = z[idx]
            z0 = rng.normal(size=z1.shape)
            t = rng.uniform(size=len(idx))
            zt = (1.0 - t)[:, None] * z0 + t[:, None] * z1
            return np.concatenate([zt, _tfeat(t)], axis=1), z1 - z0

        _, self.hist, self.secs = _cached(
            'latentflow', self.net, lambda: _adam(self.net, batches, 8000, 3e-3))

    def draw(self, n: int, seed: int, steps: int = 8) -> Arr:
        rng = np.random.default_rng(seed)
        z = rng.normal(size=(n, 2))
        dt = 1.0 / steps
        for i in range(steps):
            v = self.net.run(np.concatenate(
                [z, _tfeat(np.full(n, i * dt))], axis=1))
            z = z + dt * v
        return z * self.sd + self.mean


LF: LatentFlow | None = None


def _lf() -> LatentFlow:
    global LF
    if LF is None:
        LF = LatentFlow()
    return LF


def latent_codes() -> None:
    s = _sq(2)
    lf = _lf()
    made = lf.draw(600, seed=1717)
    built = s.decode(made)
    print(f'[p2s4] the 4,000 real codes fill a patch from '
          f'({lf.codes[:, 0].min():+.2f}, {lf.codes[:, 1].min():+.2f}) to '
          f'({lf.codes[:, 0].max():+.2f}, {lf.codes[:, 1].max():+.2f})')
    frac = float((built[:, NT // 2] > 0).mean())
    print(f'[p2s4] 600 demonstrations generated in the code space and built back '
          f'up: {frac * 100:.1f}% swerve above')
    print(f'[p2s4] their middle reading has spread {built[:, NT // 2].std():.3f} m '
          f'against {s.test[:, NT // 2].std():.3f} m for real ones')

    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    up = s.side == 0
    ax.scatter(lf.codes[up, 0], lf.codes[up, 1], s=6, color=LINK, alpha=0.5,
               label='swerves above')
    ax.scatter(lf.codes[~up, 0], lf.codes[~up, 1], s=6, color=SLIDE, alpha=0.5,
               label='swerves below')
    ax.set_xlabel('first number of the code', fontsize=9.5)
    ax.set_ylabel('second number of the code', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('Where the 4,000 real demonstrations\nland in the 2-number space',
                 fontsize=10.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ax.scatter(lf.codes[:, 0], lf.codes[:, 1], s=5, color=GRID, alpha=0.9)
    ax.scatter(made[:, 0], made[:, 1], s=7, color=GRIP, alpha=0.6)
    ax.set_xlabel('first number of the code', fontsize=9.5)
    ax.set_ylabel('second number of the code', fontsize=9.5)
    ax.set_title('600 new codes made by a flow model\nthat never saw the 16 numbers',
                 fontsize=10.5, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    for k in range(40):
        ax.plot(XS, built[k], color=GRIP, lw=1.0, alpha=0.8)
    ax.axhline(0, color=MUTED, lw=1.0)
    ax.set_xlabel('forward position x (m)', fontsize=9.5)
    ax.set_ylabel('sideways position y (m)', fontsize=9.5)
    ax.set_title('40 of those codes built back up into\nwhole demonstrations',
                 fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'latent-codes.svg')


def pixels_vs_latent_cost() -> None:
    pic = 512 * 512 * 3
    small = 64 * 64 * 4
    print(f'[p2s4] a 512 by 512 colour picture is {pic:,} numbers; shrunk by 8 on '
          f'each side with 4 channels it is {small:,}, which is {pic / small:.0f} '
          'times fewer')
    traj = NT
    code = 2
    print(f'[p2s4] the demonstration here goes from {traj} numbers to {code}, '
          f'which is {traj / code:.0f} times fewer')
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['every pixel\n512 x 512 x 3', 'the small code\n64 x 64 x 4'],
                  [pic, small], color=[GRIP, SLIDE], width=0.5, edgecolor=INK,
                  lw=0.6)
    for b, v in zip(bars, [pic, small]):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f'{v:,}', ha='center',
                fontsize=11, weight='bold', color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1e3, pic * 4)
    ax.set_ylabel('numbers the generator has to work on', fontsize=9.5)
    ax.set_title(f'A picture generator: {pic / small:.0f} times fewer numbers\n'
                 'once the picture is squeezed first',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    steps = np.arange(1, 51)
    ax.plot(steps, steps * pic / 1e6, color=GRIP, lw=2.6,
            label='working on every pixel')
    ax.plot(steps, steps * small / 1e6, color=SLIDE, lw=2.6,
            label='working on the small code')
    ax.set_xlabel('number of generating steps', fontsize=9.5)
    ax.set_ylabel('millions of numbers touched in all', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('And every step pays the saving again,\n'
                 'which is what makes 50 steps affordable',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'pixels-vs-latent-cost.svg')


# --------------------------------------------------------------------------
# page 2, section 5: which generator suits which job
# --------------------------------------------------------------------------

def all_generators_samples() -> None:
    d = _data()
    s = _sweep()
    a = _ar()
    one = _pass_time(1)
    rows = [
        ('diffusion, 50 steps', _ddim(1500, UNTOLD, seed=1818, steps=50)[0], 50,
         PURPLE),
        ('flow matching, 4 steps', _flow_sample(1500, UNTOLD, seed=1818, steps=4)[0],
         4, SLIDE),
        ('one piece at a time', a.draw(1500, seed=1818), 2, WRIST),
    ]
    print('[p2s5] side by side at the settings a robot would use:')
    for name, pts, passes, _col in rows:
        print(f'[p2s5]   {name}: mismatch {_mismatch(pts, d.ref):.4f}, inside the '
              f'obstacle {_in_obstacle(pts) * 100:.2f}%, {passes} passes, '
              f'{passes * one * 1e3:.3f} ms')
    fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.8), facecolor='white')
    _arena(axes[0], lim=2.4, labels=False)
    sh = _show(d.ref, 800, 20)
    axes[0].scatter(sh[:, 0], sh[:, 1], s=5, color=LINK, alpha=0.55)
    axes[0].set_xlabel('x (m)', fontsize=8.5)
    axes[0].set_ylabel('y (m)', fontsize=8.5)
    axes[0].set_title('real demonstrations\nmismatch 0 by definition', fontsize=10.5,
                      weight='bold', color=INK)
    for ax, (name, pts, passes, col) in zip(axes[1:], rows):
        _arena(ax, lim=2.4, labels=False)
        ax.scatter(pts[:800, 0], pts[:800, 1], s=5, color=col, alpha=0.55)
        ax.set_xlabel('x (m)', fontsize=8.5)
        ax.set_ylabel('y (m)', fontsize=8.5)
        ax.set_title(f'{name}\nmismatch {_mismatch(pts, d.ref):.4f}, '
                     f'{passes} passes', fontsize=10.5, weight='bold', color=INK)
    fig.suptitle('The three generators of this chapter, at the settings a robot '
                 'would actually use', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'all-generators-samples.svg')


def control_rate_budget() -> None:
    rates = [(10, 100.0), (30, 33.3), (50, 20.0)]
    pers = [0.5, 1.0, 2.0, 5.0]
    print('[p2s5] how many passes fit inside one control period:')
    table = []
    for hz, ms in rates:
        row = [int(ms // per) for per in pers]
        table.append(row)
        print(f'[p2s5]   {hz} commands a second ({ms:.0f} ms): ' + ', '.join(
            f'{n} passes at {per:.1f} ms each' for n, per in zip(row, pers)))
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    idx = np.arange(len(pers))
    for k, (hz, _ms) in enumerate(rates):
        ax.bar(idx + (k - 1) * 0.27, table[k], width=0.25,
               color=[LINK, SLIDE, GRIP][k], edgecolor=INK, lw=0.5,
               label=f'{hz} commands a second')
        for i, v in enumerate(table[k]):
            ax.text(i + (k - 1) * 0.27, v * 1.1, str(v), ha='center', fontsize=8.5,
                    color=INK)
    ax.set_yscale('log')
    ax.set_xticks(idx)
    ax.set_xticklabels([f'{p:.1f} ms\nper pass' for p in pers])
    ax.set_ylabel('passes that fit in one period', fontsize=9.5)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('How many passes a control rate pays for',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    ax.axis('off')
    lines = ['at 2.0 ms for one pass:', '',
             '  50 denoising steps  = 100.0 ms  -> 10 Hz at best, nothing to spare',
             '  10 denoising steps  =  20.0 ms  -> fits 30 Hz',
             '   4 flow steps       =   8.0 ms  -> fits 50 Hz',
             '   1 flow step        =   2.0 ms  -> fits anything',
             '',
             'and a 16-piece answer made one piece',
             'at a time needs 16 passes = 32.0 ms,',
             'which already misses 50 Hz']
    ax.text(0.0, 0.95, '\n'.join(lines), fontsize=11.5, family='monospace',
            va='top', color=INK)
    ax.set_title('The same arithmetic written out', fontsize=11.5, weight='bold',
                 color=INK, loc='left')
    fig.tight_layout()
    _save(fig, FLOW_DOC, 'control-rate-budget.svg')


def passes_needed() -> None:
    s = _sweep()
    target = 0.01
    f_need = min((n for n in FEW if s.flow[n] <= target), default=max(FEW))
    d_need = min((n for n in FEW if s.diff[n] <= target), default=max(FEW))
    names = ['flow matching', 'diffusion', 'one piece at a time\n(2-piece answer)',
             'one piece at a time\n(16-piece answer)']
    vals = [f_need, d_need, 2, 16]
    print(f'[p2s5] passes needed to reach a mismatch of {target}: flow {f_need}, '
          f'diffusion {d_need}; one piece at a time always needs one pass per piece')
    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    bars = ax.bar(names, vals, color=[SLIDE, PURPLE, WRIST, WRIST], width=0.55,
                  edgecolor=INK, lw=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha='center',
                fontsize=12, weight='bold', color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel('passes through the network for one answer', fontsize=9.5)
    ax.set_title(f'What each generator costs for one answer, where the first two\n'
                 f'are measured at the same quality (mismatch {target})',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'passes-needed.svg')


def error_vs_time_frontier() -> None:
    d = _data()
    s = _sweep()
    a = _ar()
    one = _pass_time(1)
    ar_mis = _mismatch(a.draw(1500, seed=1919), d.ref)
    print(f'[p2s5] the two-stage model scores {ar_mis:.4f} for 2 passes '
          f'({2 * one * 1e3:.3f} ms)')
    fig, ax = plt.subplots(figsize=(10.4, 5.6), facecolor='white')
    _plain(ax)
    times = np.array(FEW) * one * 1e3
    ax.plot(times, [s.diff[n] for n in FEW], color=PURPLE, lw=2.4, marker='o',
            ms=6, label='diffusion')
    ax.plot(times, [s.flow[n] for n in FEW], color=SLIDE, lw=2.4, marker='s',
            ms=6, label='flow matching')
    ax.plot([2 * one * 1e3], [ar_mis], marker='D', ms=10, color=WRIST,
            label='one piece at a time')
    ax.axhline(d.floor, color=MUTED, ls='--', lw=1.3)
    ax.text(times[0], d.floor * 1.35, f'real against real: {d.floor:.4f}',
            fontsize=9.5, color=MUTED)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('measured time to make one waypoint (ms)', fontsize=9.5)
    ax.set_ylabel('mismatch score (lower is better)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('Everything on one pair of axes: what each generator buys\n'
                 'for the time it takes', fontsize=12, weight='bold', color=INK)
    _save(fig, FLOW_DOC, 'error-vs-time-frontier.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    d = _data()
    print(f'[data] {len(d.train)} training waypoints, {len(d.test)} held-out, '
          f'{len(d.ref)} reference')
    print(f'[data] mismatch score between two held-out halves (the floor) '
          f'{d.floor:.4f}; nearest-point distance {d.near_floor:.4f} m')
    print(f'[data] obstacle radius {OBST_R} m, '
          f'real waypoints inside it {_in_obstacle(d.test):.4f}')
    two_ways_round()
    average_is_wrong()
    what_a_predictor_gives()
    many_right_answers()
    forward_noise_steps()
    noise_schedule()
    one_point_walk()
    blob_is_round()
    noise_prediction_target()
    training_curve()
    predicted_vs_true_noise()
    error_by_time()
    reverse_walk_panels()
    one_sample_path()
    generated_vs_real()
    the_step_rule()
    conditioning_input()
    conditional_samples()
    guidance_arrows()
    guidance_sweep()
    guidance_tradeoff()
    steps_vs_error()
    samples_at_few_steps()
    steps_vs_time()
    flow_pairing()
    vector_field_arrows()
    flow_paths()
    straightness_compare()
    steps_vs_error_both()
    few_step_panels()
    error_at_fixed_steps()
    time_to_quality()
    autoregressive_pieces()
    autoregressive_samples()
    autoregressive_cost()
    trajectory_dataset()
    autoencoder_reconstruction()
    code_size_vs_error()
    latent_codes()
    pixels_vs_latent_cost()
    all_generators_samples()
    control_rate_budget()
    passes_needed()
    error_vs_time_frontier()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
