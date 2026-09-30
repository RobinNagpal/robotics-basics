"""Generate the diagrams for one page of docs/06_learned-models/02_classical-machine-learning/.

    02_most-used/01_linear-and-logistic-regression.md
        -> images/classical-machine-learning/linear-and-logistic-regression/

Run with:  pixi run python ../docs/diagrams/classical_ml_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the page can quote the same values. The data is simulated, so the true
answer is known: a force sensor's reading against a known load, a depth
camera's error against distance, and whether a grasp held. The methods are
real (least squares, ridge regression with leave-one-out checking, weighted
least squares and logistic regression by gradient descent), written in NumPy.
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

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'classical-machine-learning'
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

REG_DOC: str = 'linear-and-logistic-regression'

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


def lstsq(X: Arr, y: Arr, w: Arr | None = None, lam: float = 0.0) -> Arr:
    """Least squares, optionally weighted and with a ridge penalty.

    Solves (X^T W X + lam I') b = X^T W y, where W holds the weights on its
    diagonal and I' is the identity with the constant's entry set to zero, so
    the constant is never shrunk.
    """
    if w is None:
        w = np.ones(len(y))
    XtW = X.T * w
    reg = lam * np.eye(X.shape[1])
    reg[0, 0] = 0.0
    return np.linalg.solve(XtW @ X + reg, XtW @ y)


# --------------------------------------------------------------------------
# 1. a line through five readings (the worked example, no picture)
# --------------------------------------------------------------------------

def worked_line() -> None:
    """Calibrate a gripper force sensor: raw counts against a known load."""
    load = np.array([0.0, 5.0, 10.0, 15.0, 20.0])            # newtons hung on it
    counts = np.array([102.0, 348.0, 611.0, 849.0, 1103.0])  # what it reported
    X = np.column_stack([np.ones(5), counts])
    b = lstsq(X, load)
    pred = X @ b
    xm, ym = counts.mean(), load.mean()
    slope = np.sum((counts - xm) * (load - ym)) / np.sum((counts - xm) ** 2)
    icpt = ym - slope * xm
    print(f'[worked] mean counts {xm:.1f}, mean load {ym:.1f}')
    print(f'[worked] sum (dx*dy) {np.sum((counts - xm) * (load - ym)):.1f}, '
          f'sum dx^2 {np.sum((counts - xm) ** 2):.1f}')
    print(f'[worked] slope {slope:.5f} N per count, intercept {icpt:.3f} N '
          f'(solver: {b[1]:.5f}, {b[0]:.3f})')
    print(f'[worked] predictions {np.round(pred, 2)}, residuals {np.round(load - pred, 2)}')
    print(f'[worked] reading of 700 counts -> {icpt + slope * 700:.2f} N')


# --------------------------------------------------------------------------
# 2. features by hand: a straight line cannot bend, powers of z can
# --------------------------------------------------------------------------

def _depth_error(z: Arr) -> Arr:
    """Made-up truth: a depth camera's error (mm) at distance z (m)."""
    return 4.0 * z ** 2 + 3.0 * np.sin(5.0 * z)


Z_LO, Z_HI = 0.3, 1.5


def _poly(z: Arr, deg: int) -> Arr:
    u = (z - 0.9) / 0.6            # centre and scale, so the powers stay near 1
    return np.vander(u, deg + 1, increasing=True)


def features_by_hand() -> None:
    rng = np.random.default_rng(3)
    z = rng.uniform(Z_LO, Z_HI, 30)
    y = _depth_error(z) + rng.normal(0, 1.0, 30)
    zt = np.linspace(Z_LO, Z_HI, 400)
    truth = _depth_error(zt)
    fits = {}
    for deg in (1, 2, 3):
        b = lstsq(_poly(z, deg), y)
        fits[deg] = _poly(zt, deg) @ b
        print(f'[features] degree {deg}: weights {np.round(b, 2)}, '
              f'error against the truth {_rmse(fits[deg], truth):.2f} mm')

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), facecolor='white', sharey=True)
    titles = ['Features: 1 and distance', 'Features: 1, distance, distance², distance³']
    for ax, deg, col, title in zip(axes, (1, 3), (JOINT, SLIDE), titles):
        _plain(ax)
        ax.plot(zt, truth, color=INK, ls='--', lw=1.3, label='the true error curve')
        ax.scatter(z, y, color=INK, s=20, zorder=5, label='30 measured examples')
        ax.plot(zt, fits[deg], color=col, lw=2.4,
                label=f'least-squares fit: off by {_rmse(fits[deg], truth):.1f} mm')
        ax.set_title(title, fontsize=11.5, weight='bold')
        ax.set_xlabel('distance from the camera (m)', fontsize=10)
        ax.legend(fontsize=9, frameon=False, loc='upper left')
        ax.set_ylim(-3, 13)
    axes[0].set_ylabel('depth reading error (mm)', fontsize=10)
    fig.suptitle('The same least-squares fit, given extra columns made by hand, can bend',
                 fontsize=12.5, weight='bold', y=1.02)
    _save(fig, REG_DOC, 'features-by-hand.svg')


# --------------------------------------------------------------------------
# 3. ridge: choose lambda by leaving one example out at a time
# --------------------------------------------------------------------------

def _loo_error(z: Arr, y: Arr, deg: int, lam: float) -> float:
    """Leave-one-out error: fit without each example, predict it, average."""
    errs = []
    for i in range(len(z)):
        keep = np.arange(len(z)) != i
        b = lstsq(_poly(z[keep], deg), y[keep], lam=lam)
        errs.append((_poly(z[i:i + 1], deg) @ b)[0] - y[i])
    return float(np.sqrt(np.mean(np.square(errs))))


def ridge_choose_lambda() -> None:
    rng = np.random.default_rng(21)
    z = rng.uniform(Z_LO, Z_HI, 12)
    y = _depth_error(z) + rng.normal(0, 1.0, 12)
    zt = np.linspace(Z_LO, Z_HI, 400)
    truth = _depth_error(zt)
    deg = 9
    lams = 10.0 ** np.arange(-6, 2.01, 0.25)
    loo = np.array([_loo_error(z, y, deg, lam) for lam in lams])
    test = np.array([_rmse(_poly(zt, deg) @ lstsq(_poly(z, deg), y, lam=lam), truth) for lam in lams])
    best = lams[int(np.argmin(loo))]
    print(f'[ridge] leave-one-out picks lambda = {best:.4g} '
          f'(LOO error {loo.min():.2f} mm, error against truth {test[int(np.argmin(loo))]:.2f} mm)')
    show = {1e-6: GRIP, best: SLIDE, 100.0: JOINT}
    for lam in (0.0, 1e-6, best, 1.0, 100.0):
        b = lstsq(_poly(z, deg), y, lam=lam)
        print(f'[ridge] lambda {lam:g}: largest weight {np.abs(b[1:]).max():.1f}, '
              f'error against truth {_rmse(_poly(zt, deg) @ b, truth):.2f} mm, '
              f'LOO {_loo_error(z, y, deg, lam):.2f} mm')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.9), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.15, 1.0]})
    _plain(ax1)
    ax1.plot(zt, truth, color=INK, ls='--', lw=1.3, label='the true error curve')
    names = {1e-6: 'λ = 0.000001 (almost no penalty)', best: f'λ = {best:.2g} (chosen)',
             100.0: 'λ = 100 (too much penalty)'}
    for lam, col in show.items():
        b = lstsq(_poly(z, deg), y, lam=lam)
        ax1.plot(zt, _poly(zt, deg) @ b, color=col, lw=2.0, label=names[lam])
    ax1.scatter(z, y, color=INK, s=26, zorder=5, label='12 examples')
    ax1.set_ylim(-6, 16)
    ax1.set_xlabel('distance from the camera (m)', fontsize=10)
    ax1.set_ylabel('depth reading error (mm)', fontsize=10)
    ax1.set_title('Ten weights, twelve examples, three penalties', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=8.8, frameon=False, loc='upper left')

    _plain(ax2)
    ax2.plot(lams, loo, color=LINK, lw=2.2, marker='o', ms=3.5,
             label='leave-one-out error (what you can measure)')
    ax2.plot(lams, test, color=MUTED, lw=1.6, ls=':',
             label='error against the true curve (hidden in real life)')
    ax2.plot([best, best], [0, 7.0], color=SLIDE, lw=1.3)
    ax2.text(best * 1.4, 0.35, f'lowest here: λ = {best:.2g}', color=SLIDE, fontsize=9.5)
    ax2.set_xscale('log')
    ax2.set_ylim(0, 9)
    ax2.set_xlabel('penalty size λ (log scale)', fontsize=10)
    ax2.set_ylabel('error (mm)', fontsize=10)
    ax2.set_title('Pick λ by leaving each example out in turn', fontsize=11.5, weight='bold')
    ax2.legend(fontsize=8.8, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, REG_DOC, 'ridge-choosing-lambda.svg')


# --------------------------------------------------------------------------
# 4. weighted least squares: trust the still readings more
# --------------------------------------------------------------------------

TRUE_GAIN: float = 0.0200      # newtons per count
TRUE_OFFSET: float = -2.0      # newtons
SD_STILL: float = 0.2
SD_MOVING: float = 1.0


def _force_data(rng: np.random.Generator) -> tuple[Arr, Arr, Arr]:
    # the still readings were taken with light loads only; the moving ones cover the whole range
    counts = np.concatenate([rng.uniform(100, 600, 20), rng.uniform(100, 1100, 10)])
    sd = np.where(np.arange(30) < 20, SD_STILL, SD_MOVING)
    load = TRUE_OFFSET + TRUE_GAIN * counts + rng.normal(0, 1, 30) * sd
    return counts, load, sd


def weighted_least_squares() -> None:
    rng = np.random.default_rng(8)
    counts, load, sd = _force_data(rng)
    X = np.column_stack([np.ones(30), counts])
    b_plain = lstsq(X, load)
    b_w = lstsq(X, load, w=1.0 / sd ** 2)
    print(f'[wls] one run: plain gain {b_plain[1]:.5f}, offset {b_plain[0]:.3f}; '
          f'weighted gain {b_w[1]:.5f}, offset {b_w[0]:.3f}; true {TRUE_GAIN}, {TRUE_OFFSET}')
    xs = np.linspace(0, 1200, 50)
    tl = TRUE_OFFSET + TRUE_GAIN * xs
    e_plain = _rmse(b_plain[0] + b_plain[1] * xs, tl)
    e_w = _rmse(b_w[0] + b_w[1] * xs, tl)
    print(f'[wls] one run: error of the line against the true line, 0..1200 counts: '
          f'plain {e_plain:.3f} N, weighted {e_w:.3f} N')
    # many repeats
    rng2 = np.random.default_rng(100)
    ep, ew, eo = [], [], []
    for _ in range(2000):
        c, l, s = _force_data(rng2)
        Xr = np.column_stack([np.ones(30), c])
        bp = lstsq(Xr, l)
        bw = lstsq(Xr, l, w=1.0 / s ** 2)
        bo = lstsq(Xr[:20], l[:20])
        ep.append(_rmse(bp[0] + bp[1] * xs, tl))
        ew.append(_rmse(bw[0] + bw[1] * xs, tl))
        eo.append(_rmse(bo[0] + bo[1] * xs, tl))
    print(f'[wls] 2000 repeats, average error of the line: plain {np.mean(ep):.3f} N, '
          f'weighted {np.mean(ew):.3f} N, still readings only {np.mean(eo):.3f} N')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.0), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.25, 1.0]})
    _plain(ax)
    still = sd == SD_STILL
    ax.plot(xs, tl, color=INK, ls='--', lw=1.3, label='the true line')
    ax.plot(xs, b_plain[0] + b_plain[1] * xs, color=GRIP, lw=2.0, label='plain least squares')
    ax.plot(xs, b_w[0] + b_w[1] * xs, color=SLIDE, lw=2.2, label='weighted least squares')
    ax.errorbar(counts[still], load[still], yerr=2 * sd[still], fmt='o', color=LINK, ms=5,
                capsize=2, zorder=5,
                label=f'20 readings, arm still, light loads (± {2 * SD_STILL:.1f} N): weight {1 / SD_STILL ** 2:.0f}')
    ax.errorbar(counts[~still], load[~still], yerr=2 * sd[~still], fmt='s', color=WRIST, ms=5,
                capsize=2, zorder=5, alpha=0.9,
                label=f'10 readings, arm moving, all loads (± {2 * SD_MOVING:.0f} N): weight {1 / SD_MOVING ** 2:.0f}')
    ax.set_xlabel('raw sensor reading (counts)', fontsize=10)
    ax.set_ylabel('known load (N)', fontsize=10)
    ax.set_xlim(0, 1200)
    ax.set_ylim(-6, 30)
    ax.set_title('Thirty calibration readings, two kinds', fontsize=11.5, weight='bold')
    ax.legend(fontsize=8.8, frameon=False, loc='upper left')

    _plain(ax2)
    ax2.axhline(0, color=INK, ls='--', lw=1.2)
    ax2.plot(xs, b_plain[0] + b_plain[1] * xs - tl, color=GRIP, lw=2.2,
             label=f'plain: off by {e_plain:.2f} N on average')
    ax2.plot(xs, b_w[0] + b_w[1] * xs - tl, color=SLIDE, lw=2.2,
             label=f'weighted: off by {e_w:.2f} N on average')
    ax2.set_xlim(0, 1200)
    ax2.set_ylim(-0.8, 0.8)
    ax2.set_xlabel('raw sensor reading (counts)', fontsize=10)
    ax2.set_ylabel('fitted line minus true line (N)', fontsize=10)
    ax2.set_title('How far each fitted line is from the truth', fontsize=11.5, weight='bold')
    ax2.legend(fontsize=9, frameon=False, loc='upper right')
    fig.suptitle('Weighting each reading by 1 / (its noise)² lets the good readings lead',
                 fontsize=12.5, weight='bold', y=1.02)
    fig.tight_layout()
    _save(fig, REG_DOC, 'weighted-least-squares.svg')


# --------------------------------------------------------------------------
# 5. logistic regression: will this grasp hold?
# --------------------------------------------------------------------------

def _sigmoid(s: Arr) -> Arr:
    return 1.0 / (1.0 + np.exp(-s))


def _grasps(n: int, rng: np.random.Generator) -> tuple[Arr, Arr]:
    """Simulated logged grasps: grip force (N), object width (mm) -> held (1) or dropped (0)."""
    force = rng.uniform(5, 40, n)
    width = rng.uniform(20, 90, n)
    true_score = 0.30 * force - 0.10 * width + 1.0
    held = (rng.uniform(0, 1, n) < _sigmoid(true_score)).astype(float)
    return np.column_stack([force, width]), held


def logistic_fit(F: Arr, y: Arr, steps: int = 20000, rate: float = 0.5) -> tuple[Arr, Arr, Arr]:
    """Gradient descent on the log loss. Features are scaled first; returns
    weights in the original units, plus the mean and spread used."""
    mu, sdv = F.mean(axis=0), F.std(axis=0)
    X = np.column_stack([np.ones(len(y)), (F - mu) / sdv])
    b = np.zeros(X.shape[1])
    for _ in range(steps):
        p = _sigmoid(X @ b)
        b -= rate * X.T @ (p - y) / len(y)
    w = b[1:] / sdv
    b0 = b[0] - np.sum(b[1:] * mu / sdv)
    return np.concatenate([[b0], w]), mu, sdv


def _logloss(p: Arr, y: Arr) -> float:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def logistic_grasp() -> None:
    rng = np.random.default_rng(12)
    F, y = _grasps(200, rng)
    Ft, yt = _grasps(2000, np.random.default_rng(99))
    b, _, _ = logistic_fit(F, y)
    pt = _sigmoid(b[0] + Ft @ b[1:])
    acc = float(np.mean((pt > 0.5) == (yt == 1)))
    print(f'[logistic] 200 grasps, {int(y.sum())} held. weights: constant {b[0]:.2f}, '
          f'force {b[1]:.3f} per N, width {b[2]:.3f} per mm')
    print(f'[logistic] test accuracy on 2000 new grasps {acc:.3f}, log loss {_logloss(pt, yt):.3f}')
    # force only
    b1, _, _ = logistic_fit(F[:, :1], y)
    p1 = _sigmoid(b1[0] + Ft[:, :1] @ b1[1:])
    acc1 = float(np.mean((p1 > 0.5) == (yt == 1)))
    print(f'[logistic] force only: weights {np.round(b1, 3)}, test accuracy {acc1:.3f}')
    # hand-made feature: force minus what the width needs
    for f, w in ((20, 40), (20, 70), (30, 70)):
        s = b[0] + b[1] * f + b[2] * w
        print(f'[logistic] force {f} N, width {w} mm: score {s:.2f}, chance it holds {_sigmoid(np.array(s)):.2f}')
    # force needed for 90 % at 70 mm
    need = (np.log(9) - b[0] - b[2] * 70) / b[1]
    print(f'[logistic] force for a 90% chance at 70 mm: {need:.1f} N')
    # plain linear regression on 0/1 labels, for comparison
    X = np.column_stack([np.ones(200), F])
    bl = lstsq(X, y)
    pl = X @ bl
    print(f'[logistic] straight line on the 0/1 labels gives values from {pl.min():.2f} to {pl.max():.2f}')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.15]})
    _plain(ax1)
    s = np.linspace(-8, 8, 300)
    ax1.plot(s, _sigmoid(s), color=PURPLE, lw=2.4)
    ax1.axhline(0.5, color=GRID, lw=1)
    ax1.axvline(0, color=GRID, lw=1)
    for sv in (-3.0, 0.0, 2.2):
        ax1.plot([sv], [_sigmoid(np.array(sv))], 'o', color=INK, ms=6)
        ax1.annotate(f'score {sv:g} → {_sigmoid(np.array(sv)):.2f}', (sv, _sigmoid(np.array(sv))),
                     xytext=(10, -14 if sv > 0 else 8), textcoords='offset points', fontsize=9.5)
    ax1.set_xlabel('score = constant + w₁ × force + w₂ × width', fontsize=10)
    ax1.set_ylabel('chance the grasp holds', fontsize=10)
    ax1.set_ylim(-0.03, 1.05)
    ax1.set_title('The S-curve turns any score into a chance', fontsize=11.5, weight='bold')

    _plain(ax2)
    held = y == 1
    ax2.scatter(F[held, 0], F[held, 1], color=SLIDE, s=22, marker='o', label='held')
    ax2.scatter(F[~held, 0], F[~held, 1], color=GRIP, s=26, marker='x', label='dropped')
    fg = np.linspace(5, 40, 50)
    for pv, ls in ((0.1, ':'), (0.5, '-'), (0.9, '--')):
        sv = np.log(pv / (1 - pv))
        wg = (sv - b[0] - b[1] * fg) / b[2]
        ax2.plot(fg, wg, color=INK, ls=ls, lw=1.6, label=f'chance {pv:.0%} line')
    ax2.set_xlim(5, 40)
    ax2.set_ylim(15, 95)
    ax2.set_xlabel('grip force (N)', fontsize=10)
    ax2.set_ylabel('object width (mm)', fontsize=10)
    ax2.set_title(f'200 logged grasps: {acc:.0%} right on 2,000 new ones', fontsize=11.5, weight='bold')
    ax2.legend(fontsize=9, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=5,
               handletextpad=0.4, columnspacing=1.0)
    fig.tight_layout()
    _save(fig, REG_DOC, 'logistic-grasp.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    worked_line()
    features_by_hand()
    ridge_choose_lambda()
    weighted_least_squares()
    logistic_grasp()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
