"""Generate the diagrams for two pages of
docs/06_learned-models/02_classical-machine-learning/02_most-used/:

    03_gaussian-processes-and-bayesian-optimisation.md
        -> images/classical-machine-learning/gaussian-processes-and-bayesian-optimisation/
    04_nearest-neighbours-and-locally-weighted-regression.md
        -> images/classical-machine-learning/nearest-neighbours-and-locally-weighted-regression/

Run with:  pixi run python ../docs/diagrams/classical_ml_3.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the documents can quote the same values. The data is simulated: a joint
with made-up friction, a made-up grasp rule, and a made-up correction torque, so
that the true answer is known. The methods are real and written in NumPy: a
Gaussian process with its settings chosen by the marginal likelihood, Bayesian
optimisation with expected improvement and an upper confidence bound,
k-nearest neighbours, distance-weighted
neighbours and locally weighted regression.

The PID trials simulate the same joint as Book 5's PID page: inertia 0.05 kg m^2,
friction 0.5 N m per rad/s, a gravity pull of 1.0 N m and a 1,000 Hz loop.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'classical-machine-learning')
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

GP_DOC: str = 'gaussian-processes-and-bayesian-optimisation'
NN_DOC: str = 'nearest-neighbours-and-locally-weighted-regression'

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


def _rmse(a: Arr, b: Arr) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


# --------------------------------------------------------------------------
# a Gaussian process in NumPy
# --------------------------------------------------------------------------

def _rbf(a: Arr, b: Arr, ell: float, sf: float) -> Arr:
    """Squared-exponential kernel. a is (n, d), b is (m, d)."""
    d2 = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    return sf ** 2 * np.exp(-0.5 * d2 / ell ** 2)


def _col(x: Arr) -> Arr:
    return x.reshape(len(x), -1)


class GP:
    """An exact Gaussian process with a constant mean equal to the data mean."""

    def __init__(self, x: Arr, y: Arr, ell: float, sf: float, sn: float) -> None:
        self.x, self.ell, self.sf, self.sn = _col(x), ell, sf, sn
        self.ym = float(y.mean())
        K = _rbf(self.x, self.x, ell, sf) + sn ** 2 * np.eye(len(y))
        self.L = np.linalg.cholesky(K)
        self.a = np.linalg.solve(self.L.T, np.linalg.solve(self.L, y - self.ym))
        self.loglik = float(-0.5 * (y - self.ym) @ self.a - np.log(np.diag(self.L)).sum()
                            - 0.5 * len(y) * np.log(2 * np.pi))

    def predict(self, xs: Arr, with_noise: bool = False) -> tuple[Arr, Arr]:
        """Mean and standard deviation of the curve (or of a new measurement)."""
        Ks = _rbf(_col(xs), self.x, self.ell, self.sf)
        mean = Ks @ self.a + self.ym
        v = np.linalg.solve(self.L, Ks.T)
        var = np.maximum(self.sf ** 2 - (v ** 2).sum(0), 1e-12)
        if with_noise:
            var = var + self.sn ** 2
        return mean, np.sqrt(var)


def gp_fit(x: Arr, y: Arr, ells: tuple[float, ...], sfs: tuple[float, ...],
           sns: tuple[float, ...]) -> GP:
    """Try every combination of settings; keep the one with the best marginal likelihood."""
    best: GP | None = None
    for ell in ells:
        for sf in sfs:
            for sn in sns:
                g = GP(x, y, ell, sf, sn)
                if best is None or g.loglik > best.loglik:
                    best = g
    assert best is not None
    return best


def _norm_pdf(z: Arr) -> Arr:
    return np.exp(-0.5 * z ** 2) / np.sqrt(2 * np.pi)


def _norm_cdf(z: Arr) -> Arr:
    # Abramowitz and Stegun 7.1.26 for erf, accurate to about 1e-7
    s = np.sign(z)
    x = np.abs(z) / np.sqrt(2)
    t = 1 / (1 + 0.3275911 * x)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027
                                                                          + t * 1.061405429))))
    erf = 1 - poly * np.exp(-x * x)
    return 0.5 * (1 + s * erf)


def expected_improvement(mean: Arr, sd: Arr, best: float) -> Arr:
    """For minimising: the average amount by which a trial here would beat `best`."""
    z = (best - mean) / sd
    return (best - mean) * _norm_cdf(z) + sd * _norm_pdf(z)


# --------------------------------------------------------------------------
# 03 page, data 1: a correction to the joint's friction model
# --------------------------------------------------------------------------

def _friction_residual(v: Arr) -> Arr:
    """Made-up truth: the torque (N m) the plain friction model misses, at speed v (rad/s)."""
    return 0.3 * np.tanh(4.0 * v) - 0.12 * v


def kernel_and_samples() -> None:
    d = np.linspace(0, 1.5, 300)
    xs = np.linspace(0, 2, 300)
    rng = np.random.default_rng(3)
    for ell in (0.1, 0.3, 1.0):
        k = np.exp(-0.5 * np.array([0.1, 0.3, 1.0]) ** 2 / ell ** 2)
        print(f'[kernel] length scale {ell}: similarity at distance 0.1, 0.3, 1.0 = '
              + ', '.join(f'{v:.2f}' for v in k))

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for ell, colour in ((0.1, GRIP), (0.3, PURPLE), (1.0, TEAL)):
        ax.plot(d, np.exp(-0.5 * d ** 2 / ell ** 2), color=colour, lw=2.2,
                label=f'length scale {ell}')
    ax.set_xlabel('distance between two inputs', fontsize=10)
    ax.set_ylabel('how alike their answers are (kernel)', fontsize=10)
    ax.set_title('The kernel: close inputs, similar answers', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax.set_ylim(0, 1.05)

    for ax, ell, colour in ((axes[1], 0.1, GRIP), (axes[2], 1.0, TEAL)):
        _plain(ax)
        K = _rbf(_col(xs), _col(xs), ell, 1.0) + 1e-8 * np.eye(len(xs))
        L = np.linalg.cholesky(K)
        for i in range(3):
            ax.plot(xs, L @ rng.standard_normal(len(xs)), color=colour, lw=1.6,
                    alpha=[1.0, 0.7, 0.45][i])
        ax.set_ylim(-3.2, 3.2)
        ax.axhline(0, color=GRID, lw=1, zorder=0)
        ax.set_xlabel('input', fontsize=10)
        ax.set_title(f'Curves the kernel allows, length scale {ell}', fontsize=11.5,
                     weight='bold')
    axes[1].set_ylabel('answer', fontsize=10)
    fig.tight_layout()
    _save(fig, GP_DOC, 'kernel-and-samples.svg')


def prediction_and_noise() -> None:
    rng = np.random.default_rng(8)
    v = np.concatenate([rng.uniform(-1.0, 0.45, 20), rng.uniform(1.15, 1.4, 4)])
    y = _friction_residual(v) + rng.normal(0, 0.04, len(v))
    vt = np.linspace(-1.2, 2.0, 400)
    truth = _friction_residual(vt)
    grid = dict(ells=(0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2),
                sfs=(0.1, 0.2, 0.3, 0.5, 0.8))
    tiny = gp_fit(v, y, sns=(0.001,), **grid)
    fitted = gp_fit(v, y, sns=(0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.1), **grid)
    print(f'[gp-noise] {len(v)} measurements, true noise 0.04 N m')
    for name, g in (('noise forced to 0.001', tiny), ('noise chosen by the data', fitted)):
        m, s = g.predict(vt)
        inside = (vt > -1.0) & (vt < 0.45)
        print(f'[gp-noise] {name}: length scale {g.ell}, signal {g.sf}, noise {g.sn}; '
              f'error vs truth on -1..0.45 = {_rmse(m[inside], truth[inside]):.3f} N m')
    for vq in (0.0, 0.8, 1.3, 1.9):
        m, s = fitted.predict(np.array([vq]))
        print(f'[gp-noise] at {vq:.1f} rad/s: {m[0]:.3f} +- {2 * s[0]:.3f} N m (2 sd), '
              f'truth {_friction_residual(np.array([vq]))[0]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8), facecolor='white', sharey=True)
    for ax, g, title in ((axes[0], tiny, 'Noise set to almost zero: it chases every dot'),
                         (axes[1], fitted, f'Noise learned from the data ({fitted.sn} N m)')):
        _plain(ax)
        m, s = g.predict(vt)
        ax.fill_between(vt, m - 2 * s, m + 2 * s, color=PURPLE, alpha=0.18,
                        label='error bar (2 standard deviations)')
        ax.plot(vt, m, color=PURPLE, lw=2, label='GP prediction')
        ax.plot(vt, truth, color=INK, ls='--', lw=1.2, label='true correction')
        ax.scatter(v, y, color=INK, s=22, zorder=5, label=f'{len(v)} measurements')
        ax.set_ylim(-0.75, 0.75)
        ax.set_xlabel('joint speed (rad/s)', fontsize=10)
        ax.set_title(title, fontsize=11.5, weight='bold')
    axes[0].set_ylabel('missing friction torque (N m)', fontsize=10)
    axes[1].legend(fontsize=9, frameon=False, loc='lower right')
    axes[1].annotate('no data here:\nthe band opens', xy=(0.85, 0.37), xytext=(0.5, 0.6),
                     fontsize=9, color=MUTED, ha='center',
                     arrowprops=dict(arrowstyle='->', color=MUTED))
    fig.tight_layout()
    _save(fig, GP_DOC, 'prediction-and-noise.svg')


def gp_cost() -> None:
    """How the work and memory of an exact GP grow with the number of examples.

    Solving with the n x n table (a Cholesky factorisation) takes about n^3 / 3
    multiply-adds, and the table holds n^2 numbers of 8 bytes each.
    """
    for n in (100, 1_000, 10_000, 100_000):
        print(f'[gp-cost] n = {n:>7,}: about {n ** 3 / 3:.1e} multiply-adds, '
              f'table {n * n * 8 / 1e6:,.0f} MB')


# --------------------------------------------------------------------------
# 03 page, data 2: tuning PID gains on the Book 5 joint
# --------------------------------------------------------------------------

KD_RANGE = (0.0, 2.0)          # for the one-gain example, on an even scale
KP_LOG = (2.0, 200.0)          # for the two-gain example, on a log scale
KD_LOG = (0.02, 5.0)
KI: float = 5.0


def pid_trial(kp: Arr, kd: Arr, seed: int | None, T: float = 1.0) -> Arr:
    """Run step trials (one per gain pair, all at once) and return their scores.

    The joint goes from 0 to 0.5 rad. The score adds the average error (mrad / 10),
    the overshoot (mrad / 10) and five times the torque jitter (N m per tick).
    A seed gives one real-like trial: sensor noise, and a load that changes a little
    from trial to trial. seed=None gives the "true" score: the average of 8 trials.
    """
    kp = np.atleast_1d(np.asarray(kp, float))
    kd = np.atleast_1d(np.asarray(kd, float))
    if seed is None:
        return np.mean([pid_trial(kp, kd, 10_000 + s, T) for s in range(8)], axis=0)
    dt, J, b = 0.001, 0.05, 0.5
    n = int(T / dt)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.0005, (n, len(kp)))
    g = 1.0 + 0.05 * rng.standard_normal(len(kp))
    th = np.zeros(len(kp))
    w = np.zeros(len(kp))
    integ = np.zeros(len(kp))
    prev = np.full(len(kp), 0.5)
    ths = np.empty((n, len(kp)))
    us = np.empty((n, len(kp)))
    for k in range(n):
        e = 0.5 - (th + noise[k])
        integ += e * dt
        de = (e - prev) / dt
        prev = e
        u = np.clip(kp * e + KI * integ + kd * de, -10, 10)
        w = w + (u - b * w - g) / J * dt
        th = th + w * dt
        ths[k] = th
        us[k] = u
    err = np.mean(np.abs(0.5 - ths), axis=0) * 1000
    over = np.maximum(0, ths.max(0) - 0.5) * 1000
    jit = np.std(np.diff(us[200:], axis=0), axis=0)
    return err / 10 + over / 10 + 5 * jit


def _to_gains(u: Arr) -> tuple[Arr, Arr]:
    """Map the unit square to (Kp, Kd), each on a log scale."""
    return (KP_LOG[0] * (KP_LOG[1] / KP_LOG[0]) ** u[:, 0],
            KD_LOG[0] * (KD_LOG[1] / KD_LOG[0]) ** u[:, 1])


GP_GRID = dict(ells=(0.08, 0.12, 0.18, 0.25, 0.35, 0.5, 0.8),
               sfs=(0.5, 1.0, 1.5, 2.5),
               sns=(0.02, 0.05, 0.1, 0.2, 0.4))


def bo_run(cand: Arr, n_start: int, n_total: int, seed: int, trial_fn,
           acq: str) -> tuple[Arr, Arr]:
    """Bayesian optimisation over a fixed set of candidate inputs (rows of cand).

    Starts with n_start random trials. Then each new trial goes where the
    acquisition is best: 'ei' is expected improvement, 'ucb' is the optimistic
    bound mean - 1 sd (for a score to minimise). The GP sees log(score), standardised.
    """
    rng = np.random.default_rng(seed)
    idx = list(rng.choice(len(cand), n_start, replace=False))
    ys = [float(trial_fn(cand[i:i + 1], seed * 100 + j)[0]) for j, i in enumerate(idx)]
    while len(idx) < n_total:
        y = np.log(np.array(ys))
        mu, sd = y.mean(), y.std() + 1e-9
        g = gp_fit(cand[idx], (y - mu) / sd, **GP_GRID)
        m, s = g.predict(cand)
        if acq == 'ei':
            a = expected_improvement(m, s, float(((y - mu) / sd).min()))
        else:
            a = -(m - 1.0 * s)
        a[idx] = -np.inf
        nxt = int(np.argmax(a))
        idx.append(nxt)
        ys.append(float(trial_fn(cand[nxt:nxt + 1], seed * 100 + len(idx))[0]))
    return np.array(idx), np.array(ys)


def bo_one_gain() -> None:
    """Tune Kd alone, with Kp fixed at 20, and draw three steps of the loop."""
    kd_c = np.linspace(0, 2, 201)
    cand = ((kd_c - KD_RANGE[0]) / (KD_RANGE[1] - KD_RANGE[0]))[:, None]

    def trial(u: Arr, seed: int) -> Arr:
        kd = KD_RANGE[0] + u[:, 0] * (KD_RANGE[1] - KD_RANGE[0])
        return pid_trial(np.full(len(kd), 20.0), kd, seed)

    truth = pid_trial(np.full(len(kd_c), 20.0), kd_c, None)
    i_best = int(np.argmin(truth))
    print(f'[bo-1d] Kp = 20: best Kd on a fine sweep {kd_c[i_best]:.2f}, '
          f'score {truth[i_best]:.2f}; Kd = 0 scores {truth[0]:.2f}, Kd = 2 scores {truth[-1]:.2f}')
    # start from three fixed trials so the picture is easy to follow
    idx = [int(np.argmin(np.abs(kd_c - k))) for k in (0.1, 1.0, 1.9)]
    ys = [float(trial(cand[i:i + 1], 7 + j)[0]) for j, i in enumerate(idx)]
    snaps = []
    for step in range(5):
        y = np.array(ys)
        mu, sd = y.mean(), y.std() + 1e-9
        g = gp_fit(cand[idx], (y - mu) / sd, **GP_GRID)
        m, s = g.predict(cand)
        best = float(((y - mu) / sd).min())
        ei = expected_improvement(m, s, best) * sd
        ucb_pick = kd_c[int(np.argmin(m - 2 * s))]
        ei[idx] = 0
        nxt = int(np.argmax(ei))
        snaps.append((list(idx), list(ys), m * sd + mu, s * sd, ei, nxt))
        print(f'[bo-1d] after {len(idx)} trials: best score so far {min(ys):.2f} at Kd '
              f'{kd_c[idx[int(np.argmin(ys))]]:.2f}; expected improvement picks Kd '
              f'{kd_c[nxt]:.2f}; lower confidence bound (mean - 2 sd) would pick {ucb_pick:.2f}')
        idx.append(nxt)
        ys.append(float(trial(cand[nxt:nxt + 1], 7 + len(idx))[0]))
    print(f'[bo-1d] after {len(idx)} trials: best {min(ys):.2f} at Kd '
          f'{kd_c[idx[int(np.argmin(ys))]]:.2f}; tried Kd = '
          + ', '.join(f'{kd_c[i]:.2f}' for i in idx))

    show = (0, 2, 4)
    fig, axes = plt.subplots(2, 3, figsize=(14.0, 7.2), facecolor='white',
                             gridspec_kw=dict(height_ratios=(2.2, 1.0)), sharex=True)
    for col, k in enumerate(show):
        tried, scores, m, s, ei, nxt = snaps[k]
        ax = axes[0, col]
        _plain(ax)
        ax.fill_between(kd_c, m - 2 * s, m + 2 * s, color=PURPLE, alpha=0.18)
        ax.plot(kd_c, m, color=PURPLE, lw=2, label='GP guess of the score')
        ax.plot(kd_c, truth, color=INK, ls='--', lw=1.1, label='true score (unknown)')
        ax.scatter(kd_c[tried], scores, color=INK, s=34, zorder=5, label='trials run')
        ax.axvline(kd_c[nxt], color=SLIDE, lw=1.4, ls=':')
        ax.set_ylim(5, 37)
        ax.set_title(f'After {len(tried)} trials', fontsize=12, weight='bold')
        ax2 = axes[1, col]
        _plain(ax2)
        ax2.fill_between(kd_c, 0, ei, color=SLIDE, alpha=0.3)
        ax2.plot(kd_c, ei, color=SLIDE, lw=1.8)
        ax2.axvline(kd_c[nxt], color=SLIDE, lw=1.4, ls=':')
        ax2.text(kd_c[nxt], ei.max() * 1.05, f' next: Kd = {kd_c[nxt]:.2f}',
                 fontsize=9.5, color=SLIDE, va='bottom',
                 ha='left' if kd_c[nxt] < 1.3 else 'right')
        ax2.set_ylim(0, ei.max() * 1.45)
        ax2.set_xlabel('derivative gain Kd (Kp fixed at 20)', fontsize=10)
    axes[0, 0].set_ylabel('score of one step trial\n(lower is better)', fontsize=10)
    axes[1, 0].set_ylabel('expected\nimprovement', fontsize=10)
    axes[0, 0].legend(fontsize=9, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, GP_DOC, 'bo-one-gain.svg')


def bo_two_gains() -> None:
    """Tune Kp and Kd together in 15 trials; compare with 15 random trials."""
    n1 = 41
    u1 = np.linspace(0, 1, n1)
    U = np.array([(a, b) for b in u1 for a in u1])
    kp, kd = _to_gains(U)
    truth = pid_trial(kp, kd, None)
    best_true = float(truth.min())
    ib = int(np.argmin(truth))
    print(f'[bo-2d] best on a {n1} x {n1} sweep (1,681 settings): Kp {kp[ib]:.1f}, '
          f'Kd {kd[ib]:.2f}, score {best_true:.2f}; worst {truth.max():.1f}; '
          f'{np.mean(truth < best_true + 1) * 100:.1f}% of settings within 1 of the best')

    def trial(u: Arr, seed: int) -> Arr:
        a, b = _to_gains(u)
        return pid_trial(a, b, seed)

    runs, n_total = 20, 15
    names = ('Bayesian optimisation, UCB', 'Bayesian optimisation, EI', 'random trials')
    curves: dict[str, list[list[float]]] = {nm: [] for nm in names}
    ucb_runs: list[tuple[Arr, Arr]] = []
    for r in range(runs):
        for nm, acq in ((names[0], 'ucb'), (names[1], 'ei')):
            idx, ys = bo_run(U, 4, n_total, r, trial, acq)
            # the robot keeps its best measured trial; judge that choice by its true score
            curves[nm].append([float(truth[idx[:j + 1]][int(np.argmin(ys[:j + 1]))])
                               for j in range(n_total)])
            if acq == 'ucb':
                ucb_runs.append((idx, ys))
        rng = np.random.default_rng(500 + r)
        ridx = rng.choice(len(U), n_total, replace=False)
        rys = trial(U[ridx], 900 + r)
        curves[names[2]].append([float(truth[ridx[:j + 1]][int(np.argmin(rys[:j + 1]))])
                                 for j in range(n_total)])
    for nm in names:
        c = np.array(curves[nm])
        print(f'[bo-2d] {nm:27s} after 15 trials: true score of the kept gains, mean '
              f'{c[:, -1].mean():.2f}, worst of 20 runs {c[:, -1].max():.2f}; '
              f'by trial: ' + ' '.join(f'{v:.2f}' for v in c.mean(0)))
    # draw the run whose final result is the median of the 20 UCB runs
    finals = np.array(curves[names[0]])[:, -1]
    r_med = int(np.argsort(finals)[runs // 2])
    eidx, eys = ucb_runs[r_med]
    ek = int(np.argmin(eys))
    print(f'[bo-2d] run {r_med} (UCB, the median run) keeps Kp {kp[eidx[ek]]:.1f}, Kd {kd[eidx[ek]]:.2f}, measured '
          f'{eys[ek]:.2f}, true {truth[eidx[ek]]:.2f}; trial order: '
          + '; '.join(f'{kp[i]:.0f}/{kd[i]:.2f}' for i in eidx))

    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.4), facecolor='white',
                             gridspec_kw=dict(width_ratios=(1.05, 1.0)))
    ax = axes[0]
    ax.set_facecolor('white')
    Z = truth.reshape(n1, n1)
    top = 30.0
    cs = ax.contourf(kp.reshape(n1, n1), kd.reshape(n1, n1), np.minimum(Z, top),
                     levels=np.linspace(best_true, top, 14), cmap='Blues_r')
    cb = fig.colorbar(cs, ax=ax, shrink=0.9, ticks=[11, 15, 20, 25, 30])
    cb.set_label('true score (lower is better; 30 or more\nshown as 30)', fontsize=9.5)
    cb.ax.tick_params(labelsize=9)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.scatter(kp[eidx[:4]], kd[eidx[:4]], s=60, facecolor='white', edgecolor=INK,
               lw=1.4, zorder=5, label='first 4 trials, at random')
    ax.scatter(kp[eidx[4:]], kd[eidx[4:]], s=60, color=JOINT, edgecolor=INK, lw=0.8,
               zorder=5, label='next 11, chosen by the GP')
    placed: list[tuple[float, float]] = []
    for j, i in enumerate(eidx):
        pos = (float(np.log10(kp[i])), float(np.log10(kd[i])))
        if any(abs(pos[0] - a) < 0.12 and abs(pos[1] - b) < 0.12 for a, b in placed):
            continue    # too close to a number already written; the cluster speaks for itself
        placed.append(pos)
        ax.annotate(str(j + 1), (kp[i], kd[i]), xytext=(5, 4), textcoords='offset points',
                    fontsize=8.5, color=INK, zorder=6,
                    bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
    ax.scatter([kp[eidx[ek]]], [kd[eidx[ek]]], s=240, facecolor='none', edgecolor=GRIP,
               lw=2, zorder=6, label='gains kept')
    ax.set_xlabel('proportional gain Kp (log scale)', fontsize=10)
    ax.set_ylabel('derivative gain Kd (log scale)', fontsize=10)
    ax.set_title('One run: 15 trials on the joint', fontsize=12, weight='bold')
    ax.legend(fontsize=8.8, loc='upper left', framealpha=0.92)
    ax.tick_params(labelsize=9.5)

    ax = axes[1]
    _plain(ax)
    t = np.arange(1, n_total + 1)
    for nm, colour in zip(names, (JOINT, PURPLE, LINK)):
        ax.plot(t, np.mean(curves[nm], axis=0), marker='o', color=colour, lw=2.2, label=nm)
    ax.axhline(best_true, color=INK, ls='--', lw=1.2)
    ax.text(15.3, best_true - 0.3, 'best possible', fontsize=9, color=INK, ha='right',
            va='top')
    ax.axvline(4.5, color=GRID, lw=1)
    ax.text(4.65, 25.5, 'the GP starts\nchoosing', fontsize=9, color=MUTED, va='top')
    ax.set_xticks(t)
    ax.set_ylim(best_true - 1.5, 26)
    ax.set_xlabel('trials run so far', fontsize=10)
    ax.set_ylabel('true score of the best gains so far\n(average of 20 runs)', fontsize=10)
    ax.set_title('Fewer trials to reach good gains', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, GP_DOC, 'bo-two-gains.svg')


# --------------------------------------------------------------------------
# 04 page: nearest neighbours and locally weighted regression
# --------------------------------------------------------------------------

def _grasp_truth(width: Arr, offset: Arr) -> Arr:
    """Made-up rule: a grasp works if the sideways offset is small enough for the width."""
    allowed = (85.0 - width) / 2.0 + 8.0 + 4.0 * np.sin(width / 9.0)
    return (np.abs(offset) < allowed).astype(int)


def _grasp_data(n: int, rng: np.random.Generator, flip: float) -> tuple[Arr, NDArray[np.int64]]:
    x = np.column_stack([rng.uniform(20, 80, n), rng.uniform(-35, 35, n)])
    y = _grasp_truth(x[:, 0], x[:, 1])
    f = rng.uniform(0, 1, n) < flip
    y[f] = 1 - y[f]
    return x, y


def knn_classify(x: Arr, y: NDArray[np.int64], q: Arr, k: int,
                 weighted: bool = False) -> Arr:
    """Share of 'success' votes among the k nearest (optionally weighted by 1/distance)."""
    d = np.sqrt(((q[:, None, :] - x[None, :, :]) ** 2).sum(-1))
    idx = np.argsort(d, axis=1)[:, :k]
    lab = y[idx].astype(float)
    if not weighted:
        return lab.mean(1)
    w = 1.0 / (np.take_along_axis(d, idx, 1) + 1e-6)
    return (w * lab).sum(1) / w.sum(1)


def knn_classification() -> None:
    rng = np.random.default_rng(4)
    x, y = _grasp_data(150, rng, 0.08)
    xt, _ = _grasp_data(4000, np.random.default_rng(99), 0.0)
    yt = _grasp_truth(xt[:, 0], xt[:, 1])
    res = {}
    for k in (1, 5, 15, 45):
        acc = float(np.mean((knn_classify(x, y, xt, k) > 0.5) == yt))
        accw = float(np.mean((knn_classify(x, y, xt, k, True) > 0.5) == yt))
        res[k] = acc
        print(f'[knn-class] 150 grasps, k = {k}: test accuracy {acc:.3f}, '
              f'distance-weighted {accw:.3f}')
    # the same data with width in metres: offset dominates the distance
    xm = x.copy()
    xm[:, 0] /= 1000
    xtm = xt.copy()
    xtm[:, 0] /= 1000
    acc_m = float(np.mean((knn_classify(xm, y, xtm, 5) > 0.5) == yt))
    xs = (x - x.mean(0)) / x.std(0)
    xts = (xt - x.mean(0)) / x.std(0)
    acc_s = float(np.mean((knn_classify(xs, y, xts, 5) > 0.5) == yt))
    print(f'[knn-class] k = 5 with width in metres and offset in mm: {acc_m:.3f}; '
          f'with both columns standardised: {acc_s:.3f}')
    q = np.array([[60.0, 12.0]])
    d = np.sqrt(((q - x) ** 2).sum(1))
    nn = np.argsort(d)[:5]
    print(f'[knn-class] query width 60 mm, offset 12 mm: 5 nearest labels {list(y[nn])}, '
          f'distances ' + ', '.join(f'{v:.1f}' for v in d[nn]) +
          f'; truth {int(_grasp_truth(q[:, 0], q[:, 1])[0])}')

    g1, g2 = np.meshgrid(np.linspace(20, 80, 240), np.linspace(-35, 35, 240))
    G = np.column_stack([g1.ravel(), g2.ravel()])
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), facecolor='white', sharey=True)
    for ax, k in zip(axes, (1, 15)):
        ax.set_facecolor('white')
        p = knn_classify(x, y, G, k).reshape(g1.shape)
        ax.contourf(g1, g2, (p > 0.5).astype(float), levels=[-0.5, 0.5, 1.5],
                    colors=[GRIP, SLIDE], alpha=0.16)
        tg = _grasp_truth(g1.ravel(), g2.ravel()).reshape(g1.shape)
        ax.contour(g1, g2, tg, levels=[0.5], colors=INK, linestyles='--', linewidths=1.2)
        ax.scatter(x[y == 1, 0], x[y == 1, 1], color=SLIDE, s=22, edgecolor='white', lw=0.4,
                   label='grasp held', zorder=4)
        ax.scatter(x[y == 0, 0], x[y == 0, 1], color=GRIP, marker='x', s=24, lw=1.4,
                   label='grasp slipped', zorder=4)
        ax.set_xlabel('object width (mm)', fontsize=10)
        ax.set_title(f'k = {k}: {res[k] * 100:.0f}% right on new grasps', fontsize=12,
                     weight='bold')
        ax.tick_params(labelsize=9.5)
    axes[0].set_ylabel('sideways offset of the grasp (mm)', fontsize=10)
    axes[1].plot([], [], color=INK, ls='--', lw=1.2, label='true boundary')
    axes[1].legend(fontsize=9.5, loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False)
    fig.tight_layout()
    _save(fig, NN_DOC, 'knn-classification.svg')


def _torque_truth(v: Arr) -> Arr:
    """Made-up truth: friction torque (N m) at joint speed v (rad/s)."""
    return 0.3 * np.tanh(4.0 * v) + 0.4 * v


def knn_reg(x: Arr, y: Arr, q: Arr, k: int, weighted: bool = False) -> Arr:
    d = np.abs(q[:, None] - x[None, :])
    idx = np.argsort(d, axis=1)[:, :k]
    if not weighted:
        return y[idx].mean(1)
    w = 1.0 / (np.take_along_axis(d, idx, 1) + 1e-3)
    return (w * y[idx]).sum(1) / w.sum(1)


def lwr(x: Arr, y: Arr, q: Arr, h: float) -> tuple[Arr, Arr, Arr]:
    """Locally weighted regression: a weighted straight line around every query.

    Returns the predictions and, for each query, the line's constant and slope.
    """
    out = np.empty(len(q))
    c0 = np.empty(len(q))
    c1 = np.empty(len(q))
    for i, qi in enumerate(q):
        w = np.exp(-0.5 * ((x - qi) / h) ** 2)
        X = np.column_stack([np.ones_like(x), x - qi])
        A = X.T @ (w[:, None] * X) + 1e-6 * np.eye(2)
        beta = np.linalg.solve(A, X.T @ (w * y))
        out[i], c0[i], c1[i] = beta[0], beta[0], beta[1]
    return out, c0, c1


def weighted_and_local() -> None:
    rng = np.random.default_rng(12)
    v = rng.uniform(-1.0, 1.0, 40)
    y = _torque_truth(v) + rng.normal(0, 0.04, len(v))
    vt = np.linspace(-1.0, 1.0, 401)
    truth = _torque_truth(vt)
    k, h = 6, 0.12
    p_knn = knn_reg(v, y, vt, k)
    p_w = knn_reg(v, y, vt, k, True)
    p_l, _, _ = lwr(v, y, vt, h)
    print(f'[local] 40 samples, k = {k}, LWR width {h} rad/s')
    for nm, p in (('kNN', p_knn), ('weighted kNN', p_w), ('LWR', p_l)):
        edge = np.abs(vt) > 0.85
        print(f'[local] {nm:13s} error overall {_rmse(p, truth):.3f} N m, '
              f'near the two ends (|v| > 0.85) {_rmse(p[edge], truth[edge]):.3f}')
    q = 0.97
    d = np.abs(v - q)
    nn = np.argsort(d)[:k]
    wq = np.exp(-0.5 * ((v - q) / h) ** 2)
    pk = knn_reg(v, y, np.array([q]), k)[0]
    pw = knn_reg(v, y, np.array([q]), k, True)[0]
    pl, c0, c1 = lwr(v, y, np.array([q]), h)
    print(f'[local] query {q} rad/s: truth {_torque_truth(np.array([q]))[0]:.3f}, kNN {pk:.3f}, '
          f'weighted {pw:.3f}, LWR {pl[0]:.3f} (local slope {c1[0]:.2f} N m per rad/s); '
          f'neighbours at ' + ', '.join(f'{v[i]:.2f}' for i in sorted(nn, key=lambda i: v[i])))

    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.2), facecolor='white')
    ax = axes[0]
    _plain(ax)
    sz = 12 + 110 * wq
    ax.scatter(v, y, s=sz, color=TEAL, alpha=0.85, edgecolor='white', lw=0.5, zorder=4,
               label='samples, sized by their LWR weight')
    ax.scatter(v[nn], y[nn], s=150, facecolor='none', edgecolor=JOINT, lw=1.8, zorder=5,
               label=f'the {k} nearest neighbours')
    ll = np.linspace(q - 0.35, q + 0.06, 20)
    ax.plot(ll, c0[0] + c1[0] * (ll - q), color=TEAL, lw=2.2, label='LWR: small line fitted here')
    ax.plot(vt, truth, color=INK, ls='--', lw=1.1, label='true torque')
    ax.axvline(q, color=GRID, lw=1)
    ax.scatter([q], [pk], marker='s', s=70, color=JOINT, zorder=6, label=f'kNN average {pk:.2f}')
    ax.scatter([q], [pl[0]], marker='D', s=60, color=TEAL, edgecolor=INK, zorder=6,
               label=f'LWR answer {pl[0]:.2f}')
    ax.set_xlim(0.45, 1.05)
    ax.set_ylim(0.3, 0.8)
    ax.set_xlabel('joint speed (rad/s)', fontsize=10)
    ax.set_ylabel('friction torque (N m)', fontsize=10)
    ax.set_title(f'One query at {q} rad/s, near the end of the data', fontsize=12,
                 weight='bold')
    ax.legend(fontsize=8.8, frameon=False, loc='upper left')

    ax = axes[1]
    _plain(ax)
    ax.scatter(v, y, s=14, color=MUTED, zorder=3, label='40 samples')
    ax.plot(vt, truth, color=INK, ls='--', lw=1.1, label='true torque')
    ax.plot(vt, p_knn, color=JOINT, lw=1.8, label=f'kNN, k = {k}: off by {_rmse(p_knn, truth):.3f}')
    ax.plot(vt, p_w, color=PURPLE, lw=1.5,
            label=f'weighted kNN: off by {_rmse(p_w, truth):.3f}')
    ax.plot(vt, p_l, color=TEAL, lw=2.2, label=f'LWR: off by {_rmse(p_l, truth):.3f}')
    ax.set_xlabel('joint speed (rad/s)', fontsize=10)
    ax.set_title('Across all speeds (errors in N m)', fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, NN_DOC, 'weighted-and-local.svg')


def curse_of_dimensionality() -> None:
    rng = np.random.default_rng(1)
    dims = [1, 2, 3, 5, 7, 10, 15, 20, 30]
    ratio = []
    for dd in dims:
        x = rng.uniform(0, 1, (2000, dd))
        q = rng.uniform(0, 1, (200, dd))
        d = np.sqrt(((q[:, None, :] - x[None, :, :]) ** 2).sum(-1))
        ratio.append(float(np.mean(d.min(1) / d.mean(1))))
    print('[curse] 2,000 random points: nearest distance / average distance = '
          + ', '.join(f'{dd}D {r:.2f}' for dd, r in zip(dims, ratio)))
    side = [0.01 ** (1 / dd) for dd in dims]
    print('[curse] side of a box holding 1% of the data = '
          + ', '.join(f'{dd}D {s:.2f}' for dd, s in zip(dims, side)))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(dims, ratio, marker='o', color=GRIP, lw=2.2)
    for dd, r in zip(dims, ratio):
        if dd in (3, 10, 30):
            ax.annotate(f'{r:.2f}', (dd, r), xytext=(6, -12), textcoords='offset points',
                        fontsize=9.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([1, 5, 10, 15, 20, 30])
    ax.set_xlabel('number of input numbers (dimensions)', fontsize=10)
    ax.set_ylabel('nearest distance / average distance', fontsize=10)
    ax.set_title('The nearest point is barely nearer than the rest', fontsize=12,
                 weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.bar([str(dd) for dd in dims], side, color=LINK)
    for i, s in enumerate(side):
        ax.text(i, s + 0.02, f'{s:.2f}', ha='center', fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel('number of input numbers (dimensions)', fontsize=10)
    ax.set_ylabel('side of the box, as a share of the full range', fontsize=10)
    ax.set_title('Box needed to hold the nearest 1% of the data', fontsize=12,
                 weight='bold')
    fig.tight_layout()
    _save(fig, NN_DOC, 'curse-of-dimensionality.svg')


def _correction(q: Arr) -> Arr:
    """Made-up truth: a correction torque (N m) over two joint angles (rad)."""
    return 0.6 * np.sin(1.5 * q[:, 0]) * np.cos(1.2 * q[:, 1]) + 0.3 * q[:, 1]


def distance_check() -> None:
    rng = np.random.default_rng(6)
    # training poses: the arm only worked in a curved band of the two joint angles
    t = rng.uniform(0, 1, 300)
    q = np.column_stack([-1.5 + 2.4 * t + rng.normal(0, 0.12, 300),
                         0.8 * np.sin(3.0 * t) - 0.4 + rng.normal(0, 0.12, 300)])
    y = _correction(q) + rng.normal(0, 0.02, len(q))
    # leave-one-out nearest distance on the training data sets the threshold
    D = np.sqrt(((q[:, None, :] - q[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    loo = D.min(1)
    thr = float(np.quantile(loo, 0.99))
    print(f'[ood] 300 training poses; nearest-neighbour distance inside the data: median '
          f'{np.median(loo):.3f} rad, 99th percentile {thr:.3f} rad (the threshold)')
    qt = rng.uniform(-2, 2, (3000, 2))
    dt = np.sqrt(((qt[:, None, :] - q[None, :, :]) ** 2).sum(-1))
    idx = np.argsort(dt, axis=1)[:, :5]
    pred = y[idx].mean(1)
    err = np.abs(pred - _correction(qt))
    near = dt.min(1)
    ok = near <= thr
    print(f'[ood] 3,000 test poses: {ok.mean() * 100:.0f}% pass the check. Mean error passed '
          f'{err[ok].mean():.3f} N m, flagged {err[~ok].mean():.3f} N m; errors above 0.1 N m: '
          f'{np.mean(err[ok] > 0.1) * 100:.1f}% of passed, {np.mean(err[~ok] > 0.1) * 100:.0f}% of flagged')

    g1, g2 = np.meshgrid(np.linspace(-2, 2, 200), np.linspace(-2, 2, 200))
    G = np.column_stack([g1.ravel(), g2.ravel()])
    dg = np.sqrt(((G[:, None, :] - q[None, :, :]) ** 2).sum(-1)).min(1).reshape(g1.shape)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), facecolor='white')
    ax = axes[0]
    ax.set_facecolor('white')
    cs = ax.contourf(g1, g2, dg, levels=np.linspace(0, dg.max(), 12), cmap='Greys')
    cb = fig.colorbar(cs, ax=ax, shrink=0.9, ticks=[0, 0.5, 1.0, 1.5, 2.0])
    cb.set_label('distance to the nearest training pose (rad)', fontsize=9.5)
    cb.ax.tick_params(labelsize=9)
    ax.contour(g1, g2, dg, levels=[thr], colors=GRIP, linewidths=2)
    ax.scatter(q[:, 0], q[:, 1], s=8, color=LINK, label='training poses')
    ax.plot([], [], color=GRIP, lw=2, label=f'check limit: {thr:.2f} rad')
    ax.set_xlabel('joint 1 angle (rad)', fontsize=10)
    ax.set_ylabel('joint 2 angle (rad)', fontsize=10)
    ax.set_title('Where the model has seen data', fontsize=12, weight='bold')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.92)
    ax.tick_params(labelsize=9.5)
    ax = axes[1]
    _plain(ax)
    ax.scatter(near[ok], err[ok], s=7, color=SLIDE, alpha=0.5, label='passed the check')
    ax.scatter(near[~ok], err[~ok], s=7, color=GRIP, alpha=0.35, label='flagged as unfamiliar')
    ax.axvline(thr, color=GRIP, lw=1.5, ls='--')
    ax.set_xlabel('distance to the nearest training pose (rad)', fontsize=10)
    ax.set_ylabel('error of the kNN prediction (N m)', fontsize=10)
    ax.set_title('Far from the data, the answers go wrong', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left', markerscale=2.5)
    fig.tight_layout()
    _save(fig, NN_DOC, 'distance-check.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    kernel_and_samples()
    prediction_and_noise()
    gp_cost()
    bo_one_gain()
    bo_two_gains()
    knn_classification()
    weighted_and_local()
    curse_of_dimensionality()
    distance_check()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
