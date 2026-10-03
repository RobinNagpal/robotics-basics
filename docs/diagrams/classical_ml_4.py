"""Generate the diagrams for two pages of
docs/07_learned-models/02_classical-machine-learning/03_also-used/.

    01_mixture-models-and-hidden-markov-models.md
        -> images/classical-machine-learning/mixture-models-and-hidden-markov-models/
    02_movement-primitives.md
        -> images/classical-machine-learning/movement-primitives/

Run with:  pixi run python ../docs/diagrams/classical_ml_4.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the documents can quote the same values. The data is simulated: the box
weights, the tray points, the demonstrations and the force trace come from
made-up formulas plus random noise. The methods run on that data are real
(expectation-maximisation for a Gaussian mixture, Gaussian mixture regression,
the forward algorithm and Viterbi for a hidden Markov model, a dynamic movement
primitive and a probabilistic movement primitive), written in NumPy.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Ellipse  # noqa: E402
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

MIX_DOC: str = 'mixture-models-and-hidden-markov-models'
MP_DOC: str = 'movement-primitives'

COLOURS: list[str] = [LINK, WRIST, SLIDE, PURPLE]

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


def _gauss_pdf(x: Arr, mean: Arr, cov: Arr) -> Arr:
    """Density of a Gaussian with the given mean and covariance at each row of x."""
    d: int = mean.shape[0]
    diff: Arr = x - mean
    inv: Arr = np.linalg.inv(cov)
    quad: Arr = np.einsum('ni,ij,nj->n', diff, inv, diff)
    norm: float = float(np.sqrt((2 * np.pi) ** d * np.linalg.det(cov)))
    return np.exp(-0.5 * quad) / norm


def _ellipse(ax: Axes, mean: Arr, cov: Arr, colour: str, n_std: float = 2.0,
             lw: float = 2.0, fill: bool = False) -> None:
    vals, vecs = np.linalg.eigh(cov)
    angle: float = float(np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1])))
    w, h = 2 * n_std * np.sqrt(vals[1]), 2 * n_std * np.sqrt(vals[0])
    ax.add_patch(Ellipse((float(mean[0]), float(mean[1])), float(w), float(h),
                         angle=angle, fill=fill, lw=lw, ec=colour,
                         fc=colour if fill else 'none', alpha=0.25 if fill else 1.0))


# --------------------------------------------------------------------------
# Gaussian mixture model fitted by expectation-maximisation
# --------------------------------------------------------------------------

def em_gmm(x: Arr, means: Arr, covs: Arr, weights: Arr, n_iter: int,
           tol: float = 1e-6) -> tuple[Arr, Arr, Arr, list[float], list[tuple[Arr, Arr, Arr]]]:
    """Run EM. Returns the final parameters, the log-likelihood per step and a
    copy of the parameters after every step."""
    n, d = x.shape
    k: int = means.shape[0]
    history: list[tuple[Arr, Arr, Arr]] = [(means.copy(), covs.copy(), weights.copy())]
    loglik: list[float] = []
    for _ in range(n_iter):
        # E step: how much each bell claims each point
        dens: Arr = np.stack([weights[j] * _gauss_pdf(x, means[j], covs[j])
                              for j in range(k)], axis=1)
        total: Arr = dens.sum(axis=1, keepdims=True)
        loglik.append(float(np.log(total).sum()))
        resp: Arr = dens / total
        # M step: refit every bell from the points it claims
        nk: Arr = resp.sum(axis=0)
        weights = nk / n
        means = (resp.T @ x) / nk[:, None]
        covs = np.stack([((resp[:, j, None] * (x - means[j])).T @ (x - means[j])) / nk[j]
                         + 1e-6 * np.eye(d) for j in range(k)])
        history.append((means.copy(), covs.copy(), weights.copy()))
        if len(loglik) > 1 and abs(loglik[-1] - loglik[-2]) < tol:
            break
    return means, covs, weights, loglik, history


def two_bells() -> None:
    """1D mixture of two bells: the weight read when the arm lifts a box."""
    rng = np.random.default_rng(3)
    empty: Arr = rng.normal(410.0, 25.0, 70)      # grams
    full: Arr = rng.normal(505.0, 30.0, 50)
    x: Arr = np.concatenate([empty, full])[:, None]
    means0: Arr = np.array([[380.0], [560.0]])
    covs0: Arr = np.array([[[60.0 ** 2]], [[60.0 ** 2]]])
    w0: Arr = np.array([0.5, 0.5])
    m, c, w, ll, hist = em_gmm(x, means0, covs0, w0, 300)
    order = np.argsort(m[:, 0])
    m, c, w = m[order], c[order], w[order]
    sd: Arr = np.sqrt(c[:, 0, 0])
    print('two bells: steps', len(ll), 'means', m[:, 0].round(1), 'sd', sd.round(1),
          'weights', w.round(2))
    grid: Arr = np.linspace(300, 640, 400)
    p0: Arr = w[0] * _gauss_pdf(grid[:, None], m[0], c[0])
    p1: Arr = w[1] * _gauss_pdf(grid[:, None], m[1], c[1])
    r1: Arr = p1 / (p0 + p1)
    for g in (440.0, 455.0, 470.0, 500.0):
        i = int(np.argmin(abs(grid - g)))
        print(f'  chance "full" at {g:.0f} g: {r1[i]:.2f}')
    cross = grid[np.argmin(abs(r1 - 0.5))]
    print(f'  50/50 point: {cross:.0f} g')

    fig, (ax, bx) = plt.subplots(2, 1, figsize=(8.4, 6.2), sharex=True,
                                 gridspec_kw={'height_ratios': [2.2, 1]})
    _plain(ax)
    _plain(bx)
    ax.hist(x[:, 0], bins=np.arange(300, 650, 12), density=True, color=GRID,
            ec='white', label='120 lifted boxes')
    ax.plot(grid, p0, color=LINK, lw=2.2,
            label=f'bell 1: mean {m[0, 0]:.0f} g, share {w[0]:.2f}')
    ax.plot(grid, p1, color=WRIST, lw=2.2,
            label=f'bell 2: mean {m[1, 0]:.0f} g, share {w[1]:.2f}')
    ax.plot(grid, p0 + p1, color=INK, lw=1.4, ls='--', label='the two added')
    ax.set_ylabel('how common', fontsize=10.5, color=INK)
    ax.set_yticks([])
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('Two overlapping bells fitted to the weights of lifted boxes',
                 fontsize=12, color=INK)
    bx.plot(grid, r1, color=WRIST, lw=2.2)
    bx.plot(grid, 1 - r1, color=LINK, lw=2.2)
    bx.axvline(cross, color=MUTED, lw=1, ls=':')
    bx.text(cross + 5, 0.5, f'50/50 at {cross:.0f} g', fontsize=9.5, color=MUTED,
            va='center')
    bx.text(318, 0.58, 'chance it came\nfrom bell 1', color=LINK, fontsize=9.5)
    bx.text(565, 0.58, 'chance it came\nfrom bell 2', color=WRIST, fontsize=9.5)
    bx.set_ylim(-0.05, 1.12)
    bx.set_ylabel('chance', fontsize=10.5, color=INK)
    bx.set_xlabel('weight read by the arm (g)', fontsize=10.5, color=INK)
    fig.tight_layout()
    _save(fig, MIX_DOC, 'two-bells.svg')


def em_steps() -> None:
    """2D EM on where a person dropped parts on a tray, shown at three moments."""
    rng = np.random.default_rng(7)
    true_means: Arr = np.array([[0.10, 0.12], [0.22, 0.10], [0.17, 0.24]])
    true_covs: Arr = np.array([[[0.0010, 0.0006], [0.0006, 0.0012]],
                               [[0.0009, -0.0003], [-0.0003, 0.0006]],
                               [[0.0016, 0.0], [0.0, 0.0006]]])
    counts = [80, 60, 60]
    x: Arr = np.concatenate([rng.multivariate_normal(true_means[j], true_covs[j], counts[j])
                             for j in range(3)])
    means0: Arr = np.array([[0.12, 0.20], [0.15, 0.17], [0.19, 0.14]])
    covs0: Arr = np.stack([np.eye(2) * 0.004] * 3)
    w0: Arr = np.ones(3) / 3
    m, c, w, ll, hist = em_gmm(x, means0, covs0, w0, 500)
    print('EM 2D: steps', len(ll), 'log-lik first', round(ll[0], 1), 'last', round(ll[-1], 1))
    for j in range(3):
        print('  bell', j, 'mean', (m[j] * 100).round(1), 'cm, share', round(float(w[j]), 2))
    print('  true means (cm):', (true_means * 100).round(1).tolist())

    shown = [0, 3, len(hist) - 1]
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.3),
                             gridspec_kw={'width_ratios': [1, 1, 1, 1.05]})
    for ax, s in zip(axes[:3], shown):
        _plain(ax)
        mm, cc, ww = hist[s]
        dens = np.stack([ww[j] * _gauss_pdf(x, mm[j], cc[j]) for j in range(3)], axis=1)
        resp = dens / dens.sum(axis=1, keepdims=True)
        cols = resp @ np.array([matplotlib.colors.to_rgb(col) for col in COLOURS[:3]])
        ax.scatter(x[:, 0] * 100, x[:, 1] * 100, s=12, c=np.clip(cols, 0, 1), alpha=0.8,
                   lw=0)
        for j in range(3):
            _ellipse(ax, mm[j] * 100, cc[j] * 1e4, COLOURS[j])
            ax.plot(mm[j, 0] * 100, mm[j, 1] * 100, marker='+', ms=12, mew=2.2,
                    color=COLOURS[j])
        ax.set_xlim(0, 32)
        ax.set_ylim(0, 33)
        ax.set_aspect('equal')
        ax.set_xlabel('x on the tray (cm)', fontsize=10, color=INK)
        title = 'start: a guess' if s == 0 else (f'after {s} steps' if s != shown[-1]
                                                  else f'after {s} steps: settled')
        ax.set_title(title, fontsize=11.5, color=INK)
    axes[0].set_ylabel('y on the tray (cm)', fontsize=10, color=INK)
    ax = axes[3]
    _plain(ax)
    ax.plot(np.arange(len(ll)), ll, color=INK, lw=2)
    for s in shown[:2]:
        ax.plot(s, ll[min(s, len(ll) - 1)], 'o', color=GRIP, ms=6)
    ax.set_xlabel('EM step', fontsize=10, color=INK)
    ax.set_ylabel('how well the bells explain\nthe points (log-likelihood)', fontsize=10,
                  color=INK)
    ax.set_title('the score only goes up', fontsize=11.5, color=INK)
    fig.tight_layout()
    _save(fig, MIX_DOC, 'em-steps.svg')


# --------------------------------------------------------------------------
# Gaussian mixture regression on toy demonstrations
# --------------------------------------------------------------------------

def _demo_heights(rng: np.random.Generator, t: Arr, n: int) -> Arr:
    """Cup height (m) during a lift-and-set-down, one row per demonstration."""
    out = []
    for _ in range(n):
        peak = 0.25 + rng.normal(0, 0.015)
        shift = rng.normal(0, 0.03)
        tt = np.clip(t + shift, 0, 1)
        z = 0.05 + (peak - 0.05) * np.sin(np.pi * tt) ** 2 + 0.03 * tt
        out.append(z + rng.normal(0, 0.004, t.size))
    return np.array(out)


def gmr_demos() -> None:
    rng = np.random.default_rng(11)
    t: Arr = np.linspace(0, 1, 60)
    demos: Arr = _demo_heights(rng, t, 5)
    data: Arr = np.column_stack([np.tile(t, 5), demos.ravel()])
    k = 5
    means0: Arr = np.column_stack([np.linspace(0.1, 0.9, k),
                                   np.interp(np.linspace(0.1, 0.9, k), t, demos.mean(0))])
    covs0: Arr = np.stack([np.diag([0.02, 0.002])] * k)
    m, c, w, ll, _ = em_gmm(data, means0, covs0, np.ones(k) / k, 300)
    print('GMR: EM steps', len(ll))
    # regression: z given t
    tq: Arr = np.linspace(0, 1, 200)
    h = np.stack([w[j] * _gauss_pdf(tq[:, None], m[j, :1], c[j, :1, :1]) for j in range(k)],
                 axis=1)
    h = h / h.sum(axis=1, keepdims=True)
    mu_j = np.stack([m[j, 1] + c[j, 1, 0] / c[j, 0, 0] * (tq - m[j, 0]) for j in range(k)],
                    axis=1)
    var_j = np.array([c[j, 1, 1] - c[j, 1, 0] ** 2 / c[j, 0, 0] for j in range(k)])
    mu: Arr = (h * mu_j).sum(axis=1)
    var: Arr = (h * (var_j[None, :] + mu_j ** 2)).sum(axis=1) - mu ** 2
    sd: Arr = np.sqrt(var)
    mean_demo = np.interp(tq, t, demos.mean(0))
    print(f'  GMR vs average of demos: largest gap {np.abs(mu - mean_demo).max() * 1000:.1f} mm')
    print(f'  GMR peak height {mu.max() * 100:.1f} cm at t={tq[mu.argmax()]:.2f}')
    for q in (0.0, 0.5, 1.0):
        i = int(np.argmin(abs(tq - q)))
        print(f'  spread (1 sd) at t={q}: {sd[i] * 1000:.1f} mm')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.6))
    for a in (ax, bx):
        _plain(a)
        a.set_xlabel('time through the motion (0 = start, 1 = end)', fontsize=10, color=INK)
        a.set_ylim(0, 0.36)
        a.set_xlim(-0.02, 1.02)
    for d in demos:
        ax.plot(t, d, color=MUTED, lw=1.2, alpha=0.8)
    ax.plot([], [], color=MUTED, lw=1.2, label='5 demonstrations')
    for j in range(k):
        _ellipse(ax, m[j], c[j], COLOURS[j % 4], lw=2.0)
    ax.plot([], [], color=LINK, lw=2, label=f'{k} bells fitted to (time, height)')
    ax.set_ylabel('cup height above the table (m)', fontsize=10, color=INK)
    ax.set_title('1. Fit a mixture to all the recorded points', fontsize=11.5, color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    for d in demos:
        bx.plot(t, d, color=GRID, lw=1.2)
    bx.fill_between(tq, mu - 2 * sd, mu + 2 * sd, color=LINK_PALE, label='2 sd either side')
    bx.plot(tq, mu, color=LINK, lw=2.5, label='GMR: the height to follow')
    bx.set_title('2. Read off the height for each moment', fontsize=11.5, color=INK)
    bx.legend(fontsize=9.5, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, MIX_DOC, 'gmr-from-demos.svg')


# --------------------------------------------------------------------------
# hidden Markov model on a toy force trace
# --------------------------------------------------------------------------

STATE_NAMES: list[str] = ['approaching', 'in contact', 'sliding']
STATE_COLS: list[str] = [LINK, WRIST, SLIDE]


def _force_trace(rng: np.random.Generator, segments: list[tuple[int, int]],
                 dt: float) -> tuple[Arr, Arr]:
    """Make a two-channel reading (normal force N, sideways speed mm/s) for a
    list of (state, number of samples)."""
    states = np.concatenate([np.full(n, s) for s, n in segments]).astype(int)
    force_mean = np.array([0.3, 5.0, 4.4])
    speed_mean = np.array([0.0, 0.0, 15.0])
    force = force_mean[states] + rng.normal(0, 1.4, states.size)
    speed = speed_mean[states] + rng.normal(0, 7.0, states.size)
    return states, np.column_stack([force, speed])


def _fit_hmm(states: Arr, obs: Arr, k: int) -> tuple[Arr, Arr, Arr, Arr]:
    """Fit the HMM from a labelled recording by counting and averaging."""
    trans = np.full((k, k), 0.5)              # a small starting count avoids zeros
    for a, b in zip(states[:-1], states[1:]):
        trans[a, b] += 1
    trans /= trans.sum(axis=1, keepdims=True)
    means = np.array([obs[states == s].mean(0) for s in range(k)])
    sds = np.array([obs[states == s].std(0) for s in range(k)])
    start = np.array([0.98, 0.01, 0.01])
    return start, trans, means, sds


def _emission(obs: Arr, means: Arr, sds: Arr) -> Arr:
    """Chance of each reading under each state (independent Gaussians per channel)."""
    z = (obs[:, None, :] - means[None]) / sds[None]
    return np.exp(-0.5 * (z ** 2).sum(-1)) / np.prod(np.sqrt(2 * np.pi) * sds, axis=1)[None]


def forward(start: Arr, trans: Arr, e: Arr) -> Arr:
    """Forward algorithm, rescaled at each step: chance of each state given the
    readings so far."""
    n, k = e.shape
    alpha = np.zeros((n, k))
    a = start * e[0]
    alpha[0] = a / a.sum()
    for i in range(1, n):
        a = (alpha[i - 1] @ trans) * e[i]
        alpha[i] = a / a.sum()
    return alpha


def viterbi(start: Arr, trans: Arr, e: Arr) -> Arr:
    """Most likely sequence of states, in log space."""
    n, k = e.shape
    lt = np.log(trans)
    le = np.log(e + 1e-300)
    score = np.log(start) + le[0]
    back = np.zeros((n, k), dtype=int)
    for i in range(1, n):
        cand = score[:, None] + lt
        back[i] = cand.argmax(axis=0)
        score = cand.max(axis=0) + le[i]
    path = np.zeros(n, dtype=int)
    path[-1] = int(score.argmax())
    for i in range(n - 1, 0, -1):
        path[i - 1] = back[i, path[i]]
    return path


def _switches(s: Arr) -> int:
    return int((s[1:] != s[:-1]).sum())


def viterbi_contact() -> None:
    rng = np.random.default_rng(5)
    dt = 0.02                                  # 50 readings a second
    train_s, train_o = _force_trace(rng, [(0, 120), (1, 60), (2, 150), (1, 40), (2, 90),
                                          (1, 50)], dt)
    start, trans, means, sds = _fit_hmm(train_s, train_o, 3)
    print('HMM fitted from', train_s.size, 'labelled readings')
    print('  stay chances:', np.diag(trans).round(3))
    print('  means (N, mm/s):', means.round(1).tolist())
    test_s, test_o = _force_trace(rng, [(0, 75), (1, 40), (2, 80), (1, 25), (2, 55),
                                        (1, 35)], dt)
    e = _emission(test_o, means, sds)
    naive = e.argmax(axis=1)
    alpha = forward(start, trans, e)
    filt = alpha.argmax(axis=1)
    vit = viterbi(start, trans, e)
    n = test_s.size
    print(f'  test trace: {n} readings, {n * dt:.1f} s, true switches {_switches(test_s)}')
    for name, s in (('each reading alone', naive), ('forward', filt), ('Viterbi', vit)):
        print(f'  {name}: wrong {100 * (s != test_s).mean():.1f} %, switches {_switches(s)}')

    tt = np.arange(n) * dt
    fig, axes = plt.subplots(4, 1, figsize=(11, 8.2), sharex=True,
                             gridspec_kw={'height_ratios': [1.2, 1.2, 1.1, 1.4]})
    for a in axes:
        _plain(a)

    def shade(a: Axes, s: Arr) -> None:
        i0 = 0
        for i in range(1, n + 1):
            if i == n or s[i] != s[i0]:
                a.axvspan(tt[i0], tt[i - 1] + dt, color=STATE_COLS[s[i0]], alpha=0.12, lw=0)
                i0 = i

    shade(axes[0], test_s)
    shade(axes[1], test_s)
    axes[0].plot(tt, test_o[:, 0], color=INK, lw=1)
    axes[0].set_ylabel('pressing\nforce (N)', fontsize=10, color=INK)
    axes[0].set_title('A wiping tool meets the table, presses, and slides: '
                      'readings shaded by the true state', fontsize=11.5, color=INK)
    axes[1].plot(tt, test_o[:, 1], color=INK, lw=1)
    axes[1].set_ylabel('sideways\nspeed (mm/s)', fontsize=10, color=INK)
    ax = axes[2]
    for s in range(3):
        ax.plot(tt, alpha[:, s], color=STATE_COLS[s], lw=1.8, label=STATE_NAMES[s])
    ax.set_ylabel('forward:\nchance of\neach state', fontsize=10, color=INK)
    ax.set_ylim(-0.05, 1.08)
    ax.legend(fontsize=9, frameon=False, ncol=3, loc='upper center',
              bbox_to_anchor=(0.5, 1.28))
    ax = axes[3]
    rows = [('true', test_s), ('each reading\nalone', naive), ('Viterbi', vit)]
    for r, (label, s) in enumerate(rows):
        y = 2 - r
        for i in range(n):
            ax.add_patch(plt.Rectangle((tt[i], y - 0.35), dt, 0.7, color=STATE_COLS[s[i]],
                                       lw=0))
        extra = '' if r == 0 else (f'  {100 * (s != test_s).mean():.0f} % wrong, '
                                   f'{_switches(s)} switches')
        ax.text(tt[-1] + dt + 0.05, y, extra.strip(), fontsize=9.5, va='center', color=INK)
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xlim(0, tt[-1] + dt)
    ax.set_xlabel('time (s)', fontsize=10, color=INK)
    for a in axes:
        a.set_xlim(0, tt[-1] + dt)
    fig.tight_layout()
    _save(fig, MIX_DOC, 'viterbi-contact.svg')


# --------------------------------------------------------------------------
# dynamic movement primitive
# --------------------------------------------------------------------------

ALPHA_Z: float = 25.0
BETA_Z: float = ALPHA_Z / 4
ALPHA_X: float = 4.0
N_BASIS: int = 30


def _basis(x: Arr) -> Arr:
    """Bells spread along the phase x (which falls from 1 to near 0)."""
    centres = np.exp(-ALPHA_X * np.linspace(0, 1, N_BASIS))
    widths = 8 * N_BASIS ** 1.5 / centres / ALPHA_X
    return np.exp(-widths[None] * (x[:, None] - centres[None]) ** 2)


def dmp_learn(y: Arr, dt: float) -> tuple[Arr, Arr, Arr, float]:
    """Learn DMP weights for each column of y (samples x dims), duration tau=T."""
    tau = (y.shape[0] - 1) * dt
    yd = np.gradient(y, dt, axis=0)
    ydd = np.gradient(yd, dt, axis=0)
    t = np.arange(y.shape[0]) * dt
    x = np.exp(-ALPHA_X * t / tau)
    y0, g = y[0], y[-1]
    k = ALPHA_Z * BETA_Z
    # the spring's anchor slides from the start to the goal as the phase runs out
    # (the form of Hoffmann et al., 2009); the shape is what the spring leaves over
    f_target = (tau ** 2 * ydd + ALPHA_Z * tau * yd) / k - (g - y) + (g - y0) * x[:, None]
    psi = _basis(x)
    # locally weighted regression: one small weighted fit per bell
    w = np.zeros((N_BASIS, y.shape[1]))
    for i in range(N_BASIS):
        p = psi[:, i]
        w[i] = (p * x) @ f_target / ((p * x * x).sum() + 1e-10)
    return w, y0, g, tau


def dmp_run(w: Arr, y0: Arr, g: Arr, tau: float, dt: float, n_steps: int,
            use_force: bool = True) -> tuple[Arr, Arr]:
    y = y0.astype(float).copy()
    z = np.zeros_like(y)
    x = 1.0
    ys, fs = [y.copy()], []
    for _ in range(n_steps):
        psi = _basis(np.array([x]))[0]
        f = (psi @ w) / psi.sum() * x if use_force else np.zeros_like(y)
        fs.append(f)
        k = ALPHA_Z * BETA_Z
        zd = (k * (g - y) - ALPHA_Z * z - k * (g - y0) * x + k * f) / tau
        y = y + z / tau * dt
        z = z + zd * dt
        x = x + (-ALPHA_X * x / tau) * dt
        ys.append(y.copy())
    return np.array(ys), np.array(fs)


def _pour_demo(n: int) -> Arr:
    """A hand-guided move that lifts a jug up and over to a bowl (x, z in metres)."""
    s = np.linspace(0, 1, n)
    s = 3 * s ** 2 - 2 * s ** 3                           # starts and ends gently
    x = 0.40 * s
    z = 0.08 + 0.10 * s + 0.16 * np.sin(np.pi * s) ** 1.5
    return np.column_stack([x, z])


def dmp_figures() -> None:
    dt = 0.01
    demo = _pour_demo(201)                               # 2 s at 100 Hz
    w, y0, g, tau = dmp_learn(demo, dt)
    n = demo.shape[0] - 1
    n_run = int(n * 1.3)                                 # let the spring settle
    rep, f = dmp_run(w, y0, g, tau, dt, n_run)
    spring, _ = dmp_run(w, y0, g, tau, dt, n_run, use_force=False)
    err = np.linalg.norm(rep[:n + 1] - demo, axis=1).max()
    print(f'  distance from goal at {tau:.1f} s: {np.linalg.norm(rep[n] - g) * 1000:.1f} mm, '
          f'at {n_run * dt:.1f} s: {np.linalg.norm(rep[-1] - g) * 1000:.2f} mm')
    print(f'DMP: {N_BASIS} bells per axis, demo {tau:.1f} s')
    print(f'  largest gap between replay and demo: {err * 1000:.1f} mm')
    print(f'  spring alone, highest point: {spring[:, 1].max() * 100:.1f} cm; '
          f'demo highest {demo[:, 1].max() * 100:.1f} cm')

    # figure 1: spring alone, the shape, spring plus shape
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.6),
                                 gridspec_kw={'width_ratios': [1.25, 1]})
    for a in (ax, bx):
        _plain(a)
    ax.plot(demo[:, 0] * 100, demo[:, 1] * 100, color=GRID, lw=7, label='hand-guided demonstration')
    ax.plot(spring[:, 0] * 100, spring[:, 1] * 100, color=MUTED, lw=2, ls='--',
            label='spring alone: straight to the goal')
    ax.plot(rep[:, 0] * 100, rep[:, 1] * 100, color=LINK, lw=2.2,
            label='spring + learned shape')
    ax.plot(*(y0 * 100), 'o', color=INK, ms=7)
    ax.plot(*(g * 100), marker='*', color=GRIP, ms=15)
    ax.text(y0[0] * 100 + 0.8, y0[1] * 100 - 1.8, 'start', fontsize=9.5, color=INK)
    ax.text(g[0] * 100 - 5, g[1] * 100 - 2.5, 'goal: over the bowl', fontsize=9.5,
            color=GRIP)
    ax.set_xlabel('forward (cm)', fontsize=10, color=INK)
    ax.set_ylabel('height (cm)', fontsize=10, color=INK)
    ax.set_xlim(-2, 46)
    ax.set_ylim(4, 40)
    ax.set_aspect('equal')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('The spring pulls to the goal; the shape adds the arc', fontsize=11.5,
                 color=INK)
    tt = np.arange(n_run) * dt
    bx.plot(tt, f[:, 1] * 100, color=LINK, lw=2, label='shape on height')
    bx.plot(tt, f[:, 0] * 100, color=WRIST, lw=2, label='shape on forward')
    bx.axhline(0, color=GRID, lw=1)
    bx.set_xlabel('time (s)', fontsize=10, color=INK)
    bx.set_ylabel('learned shape term (cm)', fontsize=10, color=INK)
    bx.set_title('The learned shape fades out as the move ends', fontsize=11.5, color=INK)
    bx.legend(fontsize=9.5, frameon=False)
    fig.tight_layout()
    _save(fig, MP_DOC, 'dmp-spring-and-shape.svg')

    # figure 2: new goals and a slower replay
    goals = [np.array([0.40, 0.18]), np.array([0.30, 0.14]), np.array([0.48, 0.24]),
             np.array([0.36, 0.26])]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.7),
                                 gridspec_kw={'width_ratios': [1.25, 1]})
    for a in (ax, bx):
        _plain(a)
    ax.plot(demo[:, 0] * 100, demo[:, 1] * 100, color=GRID, lw=7, label='demonstration')
    for j, gg in enumerate(goals):
        r, _ = dmp_run(w, y0, gg, tau, dt, n_run)
        miss = np.linalg.norm(r[-1] - gg)
        print(f'  new goal {gg * 100} cm: ends {miss * 1000:.2f} mm from it, '
              f'top {r[:, 1].max() * 100:.1f} cm')
        col = COLOURS[j % 4]
        ax.plot(r[:, 0] * 100, r[:, 1] * 100, color=col, lw=2)
        ax.plot(*(gg * 100), marker='*', color=col, ms=14)
    ax.plot(*(y0 * 100), 'o', color=INK, ms=7)
    ax.set_xlabel('forward (cm)', fontsize=10, color=INK)
    ax.set_ylabel('height (cm)', fontsize=10, color=INK)
    ax.set_xlim(-2, 52)
    ax.set_ylim(4, 46)
    ax.set_aspect('equal')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Move the bowl: one learned shape, four goals', fontsize=11.5, color=INK)
    slow, _ = dmp_run(w, y0, g, tau * 1.5, dt, int(n_run * 1.5))
    print(f'  slow replay (tau x1.5): largest path gap from normal replay '
          f'{np.min(np.linalg.norm(slow[:, None] - rep[None], axis=2), axis=1).max() * 1000:.1f} mm')
    bx.plot(np.arange(rep.shape[0]) * dt, rep[:, 0] * 100, color=LINK, lw=2.2,
            label=f'normal: {tau:.1f} s')
    bx.plot(np.arange(slow.shape[0]) * dt, slow[:, 0] * 100, color=WRIST, lw=2.2,
            label=f'time scale 1.5: {tau * 1.5:.1f} s')
    bx.set_xlabel('time (s)', fontsize=10, color=INK)
    bx.set_ylabel('forward (cm)', fontsize=10, color=INK)
    bx.set_title('Change one number to slow it down', fontsize=11.5, color=INK)
    bx.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, MP_DOC, 'dmp-new-goal-and-time.svg')


# --------------------------------------------------------------------------
# probabilistic movement primitive
# --------------------------------------------------------------------------

def _promp_basis(t: Arr, n: int = 10) -> Arr:
    c = np.linspace(-0.1, 1.1, n)
    h = 0.1 ** 2
    b = np.exp(-(t[:, None] - c[None]) ** 2 / (2 * h))
    return b / b.sum(axis=1, keepdims=True)


def _wipe_demos(rng: np.random.Generator, t: Arr, n: int) -> Arr:
    """Sideways position (m) of a wiping tool over one stroke, one row per demo."""
    out = []
    for _ in range(n):
        a = 0.12 + rng.normal(0, 0.025)             # how far it swings out
        b = rng.normal(0, 0.012)                    # where it ends
        y = a * np.sin(np.pi * t) + b * t + 0.02 * np.sin(2 * np.pi * t) * rng.normal(1, 0.5)
        out.append(y + rng.normal(0, 0.002, t.size))
    return np.array(out)


def promp_figures() -> None:
    rng = np.random.default_rng(21)
    t = np.linspace(0, 1, 100)
    demos = _wipe_demos(rng, t, 8)
    phi = _promp_basis(t)
    lam = 1e-6
    ws = np.array([np.linalg.solve(phi.T @ phi + lam * np.eye(phi.shape[1]), phi.T @ d)
                   for d in demos])
    w_mu = ws.mean(0)
    w_cov = np.cov(ws.T) + 1e-8 * np.eye(ws.shape[1])
    fit_err = max(np.abs(phi @ wi - d).max() for wi, d in zip(ws, demos))
    print(f'ProMP: {len(demos)} demos, {phi.shape[1]} weights each; '
          f'largest fit error {fit_err * 1000:.1f} mm')
    noise = 1e-6
    mu = phi @ w_mu
    sd = np.sqrt(np.einsum('ti,ij,tj->t', phi, w_cov, phi) + noise)
    for q in (0.0, 0.5, 1.0):
        i = int(np.argmin(abs(t - q)))
        print(f'  mean {mu[i] * 100:.1f} cm, spread (1 sd) {sd[i] * 1000:.1f} mm at t={q}')

    fig, ax = plt.subplots(figsize=(9, 4.6))
    _plain(ax)
    for d in demos:
        ax.plot(t, d * 100, color=MUTED, lw=1, alpha=0.8)
    ax.plot([], [], color=MUTED, lw=1, label='8 hand-guided strokes')
    ax.fill_between(t, (mu - 2 * sd) * 100, (mu + 2 * sd) * 100, color=LINK_PALE,
                    label='2 sd either side')
    ax.plot(t, mu * 100, color=LINK, lw=2.5, label='mean path')
    ax.set_xlabel('time through the stroke (0 = start, 1 = end)', fontsize=10, color=INK)
    ax.set_ylabel('sideways position of the cloth (cm)', fontsize=10, color=INK)
    ax.set_title('A ProMP: the mean stroke and how much the strokes vary', fontsize=11.5,
                 color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower center')
    fig.tight_layout()
    _save(fig, MP_DOC, 'promp-mean-and-spread.svg')

    # condition on a via-point
    t_star, y_star, s_star = 0.5, 0.155, 1e-6
    p = _promp_basis(np.array([t_star]))[0]
    gain = w_cov @ p / (s_star + p @ w_cov @ p)
    w_mu2 = w_mu + gain * (y_star - p @ w_mu)
    w_cov2 = w_cov - np.outer(gain, p @ w_cov)
    w_cov2 = 0.5 * (w_cov2 + w_cov2.T) + 1e-10 * np.eye(len(w_mu))
    mu2 = phi @ w_mu2
    sd2 = np.sqrt(np.maximum(np.einsum('ti,ij,tj->t', phi, w_cov2, phi), 0) + noise)
    i_star = int(np.argmin(abs(t - t_star)))
    print(f'  via-point {y_star * 100:.1f} cm at t={t_star}: prior mean there '
          f'{mu[i_star] * 100:.1f} cm; conditioned mean {mu2[i_star] * 100:.2f} cm, '
          f'sd {sd2[i_star] * 1000:.2f} mm')
    print(f'  conditioned spread at start {sd2[0] * 1000:.1f} mm, end {sd2[-1] * 1000:.1f} mm')
    samples = rng.multivariate_normal(w_mu2, w_cov2, 6)

    fig, ax = plt.subplots(figsize=(9, 4.6))
    _plain(ax)
    ax.fill_between(t, (mu - 2 * sd) * 100, (mu + 2 * sd) * 100, color=GRID, alpha=0.6,
                    label='before: what the demos allow')
    ax.fill_between(t, (mu2 - 2 * sd2) * 100, (mu2 + 2 * sd2) * 100, color=LINK_PALE,
                    label='after: paths through the via-point')
    for smp in samples:
        ax.plot(t, phi @ smp * 100, color=LINK, lw=0.9, alpha=0.7)
    ax.plot(t, mu2 * 100, color=LINK, lw=2.5, label='new mean path')
    ax.plot(t, mu * 100, color=MUTED, lw=1.6, ls='--', label='old mean path')
    ax.plot(t_star, y_star * 100, marker='*', color=GRIP, ms=17, zorder=5)
    ax.annotate('via-point: reach 15.5 cm\nhalf-way through', (t_star, y_star * 100),
                xytext=(0.62, 21.5), fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP))
    ax.set_xlabel('time through the stroke (0 = start, 1 = end)', fontsize=10, color=INK)
    ax.set_ylabel('sideways position of the cloth (cm)', fontsize=10, color=INK)
    ax.set_title('Ask for a via-point: every likely path now passes through it',
                 fontsize=11.5, color=INK)
    ax.set_ylim(-4, 27)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, MP_DOC, 'promp-via-point.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    two_bells()
    em_steps()
    gmr_demos()
    viterbi_contact()
    dmp_figures()
    promp_figures()


if __name__ == '__main__':
    main()
