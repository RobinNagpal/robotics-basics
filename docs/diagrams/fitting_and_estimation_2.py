"""Generate the second set of diagrams for docs/05_programming-techniques/04_fitting-and-estimation/.

This covers:
  03_also-used/01_system-identification  -> docs/images/fitting-and-estimation/system-identification/
  02_most-used/03_kalman-filter, the section on bent relationships (EKF, UKF and the
  particle filter)                        -> docs/images/fitting-and-estimation/kalman-filter/

Run with:  pixi run python ../docs/diagrams/fitting_and_estimation_2.py
Add --png <dir> to also write PNG copies for checking.

Every result drawn here is computed for real with numpy. The friction fits are real
least-squares fits on simulated readings, recursive least squares really runs on the
drawn stream, the Monte Carlo check really draws 20 000 samples, and the extended
Kalman filter, the unscented Kalman filter and the particle filter really run on the
same turntable readings. The script prints the numbers the documents quote.
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
                        / 'fitting-and-estimation')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
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

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small drawing helpers (the same as fitting_and_estimation.py)
# --------------------------------------------------------------------------

def _plot_axes(ax: Axes, xlabel: str, ylabel: str) -> None:
    """A plain chart: light grid, no top or right frame, readable labels."""
    ax.set_facecolor('white')
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=10)
    ax.set_xlabel(xlabel, fontsize=11, color=INK)
    ax.set_ylabel(ylabel, fontsize=11, color=INK)


def _title(ax: Axes, text: str, size: float = 12) -> None:
    ax.set_title(text, fontsize=size, color=INK, weight='bold', pad=10)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _ellipse(ax: Axes, mean: Arr, cov: Arr, k: float, **kw) -> None:
    """Draw the k-spread ellipse of a 2 x 2 covariance."""
    vals, vecs = np.linalg.eigh(cov)
    ang = np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1]))
    ax.add_patch(Ellipse(mean, 2 * k * np.sqrt(vals[1]), 2 * k * np.sqrt(vals[0]),
                         angle=ang, fill=False, **kw))


# ==========================================================================
# 03_also-used/01_system-identification
# ==========================================================================

# A joint's friction: torque = b * speed + c * sign(speed).
# b is viscous friction (N m per rad/s), c is Coulomb friction (N m).
B_TRUE, C_TRUE, TAU_SD = 0.25, 0.40, 0.05


def friction_rows(speed: Arr) -> Arr:
    """One row per reading: [speed, sign(speed)]. Torque = row . [b, c]."""
    return np.column_stack([speed, np.sign(speed)])


def fit_ls(a: Arr, y: Arr) -> tuple[Arr, Arr, float]:
    """Least squares with error bars: returns (numbers, covariance, residual spread)."""
    theta, *_ = np.linalg.lstsq(a, y, rcond=None)
    res = y - a @ theta
    dof = len(y) - a.shape[1]
    s2 = float(res @ res / dof)
    cov = s2 * np.linalg.inv(a.T @ a)
    return theta, cov, float(np.sqrt(s2))


def rls(rows: Arr, y: Arr, lam: float, theta0: Arr, p0: float) -> tuple[Arr, Arr]:
    """Recursive least squares with forgetting factor lam. Returns every estimate
    and the diagonal of P after every reading."""
    theta = theta0.astype(float).copy()
    p = np.eye(len(theta)) * p0
    out, pd = [], []
    for phi, yk in zip(rows, y):
        k = p @ phi / (lam + phi @ p @ phi)
        theta = theta + k * (yk - phi @ theta)
        p = (p - np.outer(k, phi) @ p) / lam
        out.append(theta.copy())
        pd.append(np.diag(p).copy())
    return np.array(out), np.array(pd)


# The two probe moves: 40 steady-speed readings each.
GOOD_SPEEDS: Arr = np.repeat([-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0], 5)
POOR_SPEEDS: Arr = np.repeat([0.9, 0.95, 1.0, 1.05, 1.1], 8)


def sysid_probe_moves() -> None:
    """Two probe moves, and the (b, c) answers they give over 300 repeats."""
    rng = np.random.default_rng(11)
    runs = 300
    fits = {}
    for name, sp in (('good', GOOD_SPEEDS), ('poor', POOR_SPEEDS)):
        a = friction_rows(sp)
        est = []
        for _ in range(runs):
            y = a @ [B_TRUE, C_TRUE] + rng.normal(0, TAU_SD, len(sp))
            est.append(np.linalg.lstsq(a, y, rcond=None)[0])
        est = np.array(est)
        fits[name] = est
        _, cov, _ = fit_ls(a, a @ [B_TRUE, C_TRUE] + rng.normal(0, TAU_SD, len(sp)))
        formula_sd = TAU_SD * np.sqrt(np.diag(np.linalg.inv(a.T @ a)))
        print(f'probe {name}: cond {np.linalg.cond(a):.1f}; b sd {est[:, 0].std():.4f} '
              f'c sd {est[:, 1].std():.4f}; formula sd {np.round(formula_sd, 4)}; '
              f'b range {est[:, 0].min():.3f}..{est[:, 0].max():.3f}, '
              f'c range {est[:, 1].min():.3f}..{est[:, 1].max():.3f}; '
              f'corr {np.corrcoef(est.T)[0, 1]:.3f}')

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1, 1, 1.15]})
    t = np.arange(40) * 0.5
    for ax, sp, col, name in ((axes[0], GOOD_SPEEDS, SLIDE, 'Rich probe: 8 speeds, both ways'),
                              (axes[1], POOR_SPEEDS, GRIP, 'Poor probe: about 1 rad/s, one way')):
        _plot_axes(ax, 'time (s)', 'joint speed held (rad/s)')
        ax.step(t, sp, where='post', color=col, lw=2.2)
        ax.scatter(t + 0.25, sp, s=16, color=col, zorder=3)
        ax.axhline(0, color=MUTED, lw=1)
        ax.set_ylim(-2.4, 2.4)
        ax.set_xlim(0, 20)
        _title(ax, name, 11.5)
    ax = axes[2]
    _plot_axes(ax, 'fitted b, viscous friction (N m per rad/s)',
               'fitted c, Coulomb friction (N m)')
    ax.scatter(*fits['poor'].T, s=9, color=GRIP, alpha=0.55, label='poor probe, 300 repeats')
    ax.scatter(*fits['good'].T, s=9, color=SLIDE, alpha=0.7, label='rich probe, 300 repeats')
    ax.scatter([B_TRUE], [C_TRUE], marker='+', s=260, color=INK, lw=2.5, zorder=5,
               label='true values')
    ax.set_xlim(-0.05, 0.55)
    ax.set_ylim(0.05, 0.75)
    ax.legend(fontsize=9.5, loc='upper right', frameon=False)
    _title(ax, 'What each probe tells you', 11.5)
    fig.tight_layout(w_pad=2.5)
    _save(fig, 'system-identification', 'probe-moves.svg')


def sysid_friction_fit() -> None:
    """One real fit from the rich probe: data, fitted curve, error bars on the curve."""
    rng = np.random.default_rng(5)
    a = friction_rows(GOOD_SPEEDS)
    y = a @ [B_TRUE, C_TRUE] + rng.normal(0, TAU_SD, len(GOOD_SPEEDS))
    theta, cov, s = fit_ls(a, y)
    sd = np.sqrt(np.diag(cov))
    # the torque needed at 1.5 rad/s, with its spread (uses the covariance)
    g = np.array([1.5, 1.0])
    t15 = g @ theta
    t15_sd = float(np.sqrt(g @ cov @ g))
    t15_sd_naive = float(np.sqrt((1.5 * sd[0])**2 + sd[1]**2))
    print(f'fit: b {theta[0]:.4f} +- {sd[0]:.4f}, c {theta[1]:.4f} +- {sd[1]:.4f}, '
          f'residual sd {s:.4f}, corr {cov[0, 1] / sd[0] / sd[1]:.3f}; '
          f'torque at 1.5 rad/s {t15:.4f} +- {t15_sd:.4f} (naive {t15_sd_naive:.4f})')
    print(f'fit: first readings speed {GOOD_SPEEDS[[0, 5, 20, 35]]} torque '
          f'{np.round(y[[0, 5, 20, 35]], 3)}')

    fig, ax = plt.subplots(figsize=(10, 5.6), facecolor='white')
    _plot_axes(ax, 'joint speed (rad/s)', 'torque the motor needed (N m)')
    ax.axhline(0, color=MUTED, lw=1)
    ax.axvline(0, color=MUTED, lw=1)
    for side in (-1, 1):
        w = np.linspace(0.02, 2.2, 60) * side
        rows = friction_rows(w)
        fit = rows @ theta
        band = 2 * np.sqrt(np.einsum('ij,jk,ik->i', rows, cov, rows))
        ax.fill_between(w, fit - band, fit + band, color=JOINT, alpha=0.25, lw=0,
                        label='2-spread band of the fit' if side == 1 else None)
        ax.plot(w, fit, color=JOINT, lw=2.5,
                label=f'fit: b = {theta[0]:.3f}, c = {theta[1]:.3f}' if side == 1 else None)
    ax.scatter(GOOD_SPEEDS, y, s=26, color=LINK, zorder=3, label='40 readings')
    ax.annotate(f'c = {theta[1]:.3f} N m:\nthe jump at zero speed', xy=(0.0, theta[1]),
                xytext=(0.35, -0.55), fontsize=10.5, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.3})
    ax.annotate(f'b = {theta[0]:.3f}:\nthe slope', xy=(1.75, 1.75 * theta[0] + theta[1]),
                xytext=(1.85, 0.15), fontsize=10.5, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.3})
    ax.set_xlim(-2.3, 2.3)
    ax.set_ylim(-1.2, 1.3)
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'Fitting a joint\'s friction by least squares')
    _save(fig, 'system-identification', 'friction-fit.svg')


def sysid_rls_drift() -> None:
    """A friction number that drifts as the gearbox warms, and two RLS settings."""
    rng = np.random.default_rng(21)
    n = 600
    k = np.arange(n)
    b_true = np.where(k < 150, 0.30, np.where(k < 450, 0.30 - 0.10 * (k - 150) / 300, 0.20))
    speeds = rng.uniform(0.3, 2.0, n) * rng.choice([-1, 1], n)
    rows = friction_rows(speeds)
    y = b_true * speeds + C_TRUE * np.sign(speeds) + rng.normal(0, TAU_SD, n)
    th1, _ = rls(rows, y, 1.0, np.zeros(2), 100.0)
    th98, _ = rls(rows, y, 0.98, np.zeros(2), 100.0)
    th90, _ = rls(rows, y, 0.90, np.zeros(2), 100.0)
    print(f'rls: at reading 600 b true {b_true[-1]:.3f}; lam 1 {th1[-1, 0]:.4f}, '
          f'lam .98 {th98[-1, 0]:.4f}, lam .90 {th90[-1, 0]:.4f}')
    steady = slice(450, 600)
    for name, th in (('1', th1), ('0.98', th98), ('0.90', th90)):
        err = th[steady, 0] - b_true[steady]
        print(f'rls lam {name}: mean err last 150 {err.mean():+.4f}, sd {err.std():.4f}, '
              f'mean abs {np.abs(err).mean():.4f}')
    print(f'rls: at 150 lam1 {th1[149, 0]:.4f} lam98 {th98[149, 0]:.4f}')

    fig, ax = plt.subplots(figsize=(12, 5.4), facecolor='white')
    _plot_axes(ax, 'reading number (one reading every 2 s)',
               'b, viscous friction (N m per rad/s)')
    ax.plot(k, th90[:, 0], color=LINK_PALE, lw=1.2, label='forgetting factor 0.90')
    ax.plot(k, th1[:, 0], color=GRIP, lw=2.2, label='forgetting factor 1 (never forgets)')
    ax.plot(k, th98[:, 0], color=JOINT, lw=2.4, label='forgetting factor 0.98')
    ax.plot(k, b_true, color=INK, lw=1.6, ls='--', label='true b')
    ax.axvspan(150, 450, color=GRID, alpha=0.3, zorder=0)
    ax.text(300, 0.335, 'the gearbox warms up\nand its friction falls', ha='center',
            va='top', fontsize=10.5, color=MUTED)
    ax.set_ylim(0.14, 0.34)
    ax.set_xlim(0, 600)
    ax.legend(fontsize=10, loc='lower left', frameon=False)
    _title(ax, 'Recursive least squares following a friction number that drifts')
    _save(fig, 'system-identification', 'forgetting-factor.svg')


# The payload: the arm holds a part still with the forearm level. The extra torque
# at the elbow is tau = m * g * L, so m = tau / (g * L).
G = 9.81
TAU_M, TAU_S = 1.20, 0.04       # extra elbow torque (N m) and its spread
L_M, L_S = 0.150, 0.006         # distance to the part's centre (m) and its spread


def sysid_uncertainty() -> None:
    """Error propagation for m = tau / (g L), a Monte Carlo check, and the cautious end."""
    m = TAU_M / (G * L_M)
    rel = np.sqrt((TAU_S / TAU_M)**2 + (L_S / L_M)**2)
    m_sd = m * rel
    rng = np.random.default_rng(8)
    n = 20000
    samples = rng.normal(TAU_M, TAU_S, n) / (G * rng.normal(L_M, L_S, n))
    mc_mean, mc_sd = samples.mean(), samples.std()
    p975 = np.percentile(samples, 97.5)
    upper_formula = m + 2 * m_sd
    print(f'payload: m {m:.4f} kg, rel {rel:.4f}, sd {m_sd:.4f}; formula upper {upper_formula:.4f}; '
          f'MC mean {mc_mean:.4f} sd {mc_sd:.4f} 97.5% {p975:.4f} 2.5% '
          f'{np.percentile(samples, 2.5):.4f}; share above 0.9 {np.mean(samples > 0.9):.4f}')

    fig, ax = plt.subplots(figsize=(11, 5.4), facecolor='white')
    _plot_axes(ax, 'payload mass (kg)', 'how often (share of samples per 0.005 kg)')
    bins = np.arange(0.66, 0.99, 0.005)
    hist, edges = np.histogram(samples, bins=bins)
    ax.bar(edges[:-1], hist / n, width=0.005, align='edge', color=LINK_PALE,
           edgecolor=LINK, lw=0.5, label=f'Monte Carlo: {n} samples')
    xx = np.linspace(0.66, 0.98, 300)
    bell = np.exp(-0.5 * ((xx - m) / m_sd)**2) / (m_sd * np.sqrt(2 * np.pi)) * 0.005
    ax.plot(xx, bell, color=JOINT, lw=2.5, label='the formula\'s bell curve')
    top = bell.max()
    ax.axvline(m, color=INK, lw=1.4, ls=':')
    ax.text(m, top * 1.2, f'best value\n{m:.3f} kg', ha='center', va='bottom',
            fontsize=10.5, color=INK, bbox={'facecolor': 'white', 'edgecolor': 'none'})
    ax.axvline(upper_formula, color=GRIP, lw=2)
    ax.text(upper_formula + 0.004, top * 0.8,
            f'cautious end\n{upper_formula:.3f} kg\n(best + 2 spreads)',
            ha='left', va='top', fontsize=10.5, color=GRIP)
    ax.set_ylim(0, top * 1.55)
    ax.set_xlim(0.66, 0.98)
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'How sure is the payload mass?  m = torque / (g × distance)')
    _save(fig, 'system-identification', 'error-bars-and-cautious-end.svg')


# ==========================================================================
# 02_most-used/03_kalman-filter: EKF, UKF and the particle filter
# ==========================================================================

def sigma_points(mean: Arr, cov: Arr, kappa: float) -> tuple[Arr, Arr]:
    """The unscented transform's 2n + 1 sample points and their weights."""
    n = len(mean)
    s = np.linalg.cholesky((n + kappa) * cov)
    pts = [mean] + [mean + s[:, i] for i in range(n)] + [mean - s[:, i] for i in range(n)]
    w = np.full(2 * n + 1, 1 / (2 * (n + kappa)))
    w[0] = kappa / (n + kappa)
    return np.array(pts), w


def polar_to_xy(rt: Arr) -> Arr:
    """(range, bearing) to (x, y). Works on one point or on rows of points."""
    rt = np.atleast_2d(rt)
    return np.column_stack([rt[:, 0] * np.cos(rt[:, 1]), rt[:, 0] * np.sin(rt[:, 1])])


def kalman_bent_measurement() -> None:
    """A range of 400 +- 5 mm and a bearing of 90 +- 25 degrees, turned into x and y."""
    mean = np.array([400.0, np.pi / 2])
    cov = np.diag([5.0**2, np.radians(25)**2])
    rng = np.random.default_rng(4)
    samples = rng.multivariate_normal(mean, cov, 5000)
    xy = polar_to_xy(samples)
    true_mean, true_cov = xy.mean(axis=0), np.cov(xy.T)
    # EKF: straight-line version at the mean
    r, t = mean
    jac = np.array([[np.cos(t), -r * np.sin(t)], [np.sin(t), r * np.cos(t)]])
    ekf_mean = polar_to_xy(mean)[0]
    ekf_cov = jac @ cov @ jac.T
    # UKF: five sample points pushed through the real conversion
    sp, w = sigma_points(mean, cov, kappa=1.0)
    spxy = polar_to_xy(sp)
    ukf_mean = w @ spxy
    d = spxy - ukf_mean
    ukf_cov = (w[:, None] * d).T @ d
    print(f'bent: sample mean {np.round(true_mean, 1)}, EKF mean {np.round(ekf_mean, 1)}, '
          f'UKF mean {np.round(ukf_mean, 1)}; sd y sample {np.sqrt(true_cov[1, 1]):.1f} '
          f'EKF {np.sqrt(ekf_cov[1, 1]):.1f} UKF {np.sqrt(ukf_cov[1, 1]):.1f}; sd x sample '
          f'{np.sqrt(true_cov[0, 0]):.1f} EKF {np.sqrt(ekf_cov[0, 0]):.1f} '
          f'UKF {np.sqrt(ukf_cov[0, 0]):.1f}')

    fig, ax = plt.subplots(figsize=(11, 6.2), facecolor='white')
    _plot_axes(ax, 'x, sideways from the sensor (mm)', 'y, forward from the sensor (mm)')
    ax.set_aspect('equal')
    ax.scatter(*xy.T, s=3, color=LINK_PALE, alpha=0.8, zorder=1)
    ax.scatter([], [], s=20, color=LINK_PALE, label='5000 possible positions')
    _ellipse(ax, ekf_mean, ekf_cov, 2, color=GRIP, lw=2.2, zorder=3)
    _ellipse(ax, ukf_mean, ukf_cov, 2, color=JOINT, lw=2.2, ls='--', zorder=3)
    ax.scatter(*true_mean, s=90, marker='x', color=LINK, lw=2.8, zorder=5,
               label=f'real average: y = {true_mean[1]:.0f} mm')
    ax.scatter(*ekf_mean, s=60, color=GRIP, zorder=5, edgecolor=INK,
               label=f'EKF average: y = {ekf_mean[1]:.0f} mm (2-spread ellipse, red)')
    ax.scatter(*ukf_mean, s=60, marker='D', color=JOINT, zorder=5, edgecolor=INK,
               label=f'UKF average: y = {ukf_mean[1]:.0f} mm (2-spread ellipse, dashed)')
    ax.scatter(*spxy.T, s=110, facecolor='none', edgecolor=PURPLE, lw=2, zorder=6,
               label='the UKF\'s 5 sample points')
    ax.scatter([0], [0], marker='^', s=140, color=INK, zorder=6)
    ax.text(0, -18, 'sensor', ha='center', va='top', fontsize=10.5, color=INK)
    ax.set_xlim(-420, 420)
    ax.set_ylim(-60, 480)
    ax.legend(fontsize=10, loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False)
    _title(ax, 'A bell curve pushed through a bend: range 400 ± 5 mm, angle ± 25°')
    _save(fig, 'kalman-filter', 'bent-measurement.svg')


# The turntable run. A part sits 150 mm from the centre of a turntable that turns at a
# known 0.5 rad/s. A camera looking along the table sees only the part's sideways
# position x = R cos(angle). Angles a and -a give the same x, so one reading has two
# answers; only the direction of the change tells them apart.
TT_R, TT_W, TT_DT, TT_Q, TT_SD, TT_N = 150.0, 0.5, 0.1, 0.02**2, 5.0, 45
TT_START, TT_GUESS, TT_GUESS_SD = 0.6, -0.6, 0.5


def wrap(a: Arr | float) -> Arr | float:
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


def turntable_data() -> tuple[Arr, Arr]:
    rng = np.random.default_rng(12)
    ang = TT_START + TT_W * TT_DT * np.arange(1, TT_N + 1) + np.cumsum(
        rng.normal(0, np.sqrt(TT_Q), TT_N))
    z = TT_R * np.cos(ang) + rng.normal(0, TT_SD, TT_N)
    return ang, z


def run_ekf(z: Arr, x0: float, p0: float) -> tuple[Arr, Arr]:
    x, p = x0, p0
    xs, ps = [], []
    r = TT_SD**2
    for zk in z:
        x, p = x + TT_W * TT_DT, p + TT_Q                     # predict (straight already)
        hdash = -TT_R * np.sin(x)                            # slope of R cos(x) here
        s = hdash * p * hdash + r
        k = p * hdash / s
        x = x + k * (zk - TT_R * np.cos(x))
        p = (1 - k * hdash) * p
        xs.append(x)
        ps.append(p)
    return np.array(xs), np.array(ps)


def run_ukf(z: Arr, x0: float, p0: float) -> tuple[Arr, Arr]:
    x, p = x0, p0
    xs, ps = [], []
    r = TT_SD**2
    kappa = 2.0
    for zk in z:
        x, p = x + TT_W * TT_DT, p + TT_Q
        sp, w = sigma_points(np.array([x]), np.array([[p]]), kappa)
        sp = sp[:, 0]
        zs = TT_R * np.cos(sp)
        zbar = w @ zs
        s = w @ (zs - zbar)**2 + r
        c = w @ ((sp - x) * (zs - zbar))
        k = c / s
        x = x + k * (zk - zbar)
        p = p - k * s * k
        xs.append(x)
        ps.append(p)
    return np.array(xs), np.array(ps)


def systematic_resample(w: Arr, rng: np.random.Generator) -> Arr:
    n = len(w)
    pos = (rng.uniform() + np.arange(n)) / n
    return np.minimum(np.searchsorted(np.cumsum(w), pos), n - 1)


def run_pf(z: Arr, n: int, rng: np.random.Generator) -> tuple[Arr, list[Arr], list[Arr]]:
    """Particle filter. Starts knowing nothing: guesses spread all round the table."""
    parts = rng.uniform(-np.pi, np.pi, n)
    est, snaps, wsnaps = [], [parts.copy()], [np.full(n, 1 / n)]
    for zk in z:
        parts = parts + TT_W * TT_DT + rng.normal(0, np.sqrt(TT_Q), n)  # move every guess
        w = np.exp(-0.5 * ((zk - TT_R * np.cos(parts)) / TT_SD)**2)      # weigh it
        w = w / w.sum()
        est.append(np.angle(np.sum(w * np.exp(1j * parts))))            # weighted average
        snaps.append(parts.copy())
        wsnaps.append(w.copy())
        parts = parts[systematic_resample(w, rng)]                        # resample
    return np.array(est), snaps, wsnaps


def kalman_turntable() -> None:
    ang, z = turntable_data()
    ekf, ekf_p = run_ekf(z, TT_GUESS, TT_GUESS_SD**2)
    ukf, ukf_p = run_ukf(z, TT_GUESS, TT_GUESS_SD**2)
    ekf_ok, _ = run_ekf(z, TT_START, TT_GUESS_SD**2)
    pf, snaps, wsnaps = run_pf(z, 1000, np.random.default_rng(3))
    t = np.arange(1, TT_N + 1) * TT_DT
    e = lambda est: np.degrees(np.abs(wrap(est - ang)))  # noqa: E731
    print(f'turntable: first reading {z[0]:.1f} mm, true angle {np.degrees(ang[0]):.1f} deg')
    for name, est in (('EKF bad start', ekf), ('UKF bad start', ukf), ('EKF good start', ekf_ok),
                      ('PF', pf)):
        err = e(est)
        print(f'  {name}: err at steps 1,2,3,5,10,20,45 {np.round(err[[0, 1, 2, 4, 9, 19, 44]], 1)} '
              f'deg; mean err last 30 {err[-30:].mean():.2f} deg; '
              f'final angle {np.degrees(est[-1]):.1f} true {np.degrees(ang[-1]):.1f}')
    print(f'  EKF bad start final sd {np.degrees(np.sqrt(ekf_p[-1])):.2f} deg, '
          f'UKF {np.degrees(np.sqrt(ukf_p[-1])):.2f} deg')

    # figure 1: the angle over time for the three filters
    fig, ax = plt.subplots(figsize=(12, 5.4), facecolor='white')
    _plot_axes(ax, 'time (s)', 'angle of the part on the turntable (degrees)')
    ax.plot(t, np.degrees(ang), color=INK, lw=1.8, ls='--', label='true angle', zorder=5)
    ax.plot(t, np.degrees(ekf), color=GRIP, lw=2.4, label='EKF, started at −34°')
    ax.plot(t, np.degrees(ukf), color=JOINT, lw=2.4, ls=(0, (5, 2)),
            label='UKF, started at −34°')
    ax.plot(t, np.degrees(np.unwrap(pf)), color=SLIDE, lw=2.4, label='particle filter, started anywhere')
    ax.plot(t, -np.degrees(ang), color=MUTED, lw=1.2, ls=':',
            label='the mirror answer: same x, opposite angle')
    ax.set_xlim(0, TT_N * TT_DT)
    ax.legend(fontsize=10, loc='lower left', frameon=False)
    _title(ax, 'Three filters on the same turntable readings')
    _save(fig, 'kalman-filter', 'three-filters-on-a-turntable.svg')

    # figure 2: the particles at a few steps, on the turntable circle
    show = [0, 1, 4, 12]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.6), facecolor='white')
    for ax, s in zip(axes, show):
        ax.set_aspect('equal')
        ax.axis('off')
        circ = np.linspace(0, 2 * np.pi, 200)
        ax.plot(TT_R * np.cos(circ), TT_R * np.sin(circ), color=GRID, lw=6, zorder=0)
        p, w = snaps[s], wsnaps[s]
        rad = TT_R + np.random.default_rng(s).uniform(-12, 12, len(p))
        size = 4 + 900 * w if s > 0 else np.full(len(p), 4.0)
        ax.scatter(rad * np.cos(p), rad * np.sin(p), s=size, color=SLIDE, alpha=0.55,
                   lw=0, zorder=2)
        if s > 0:
            ta = ang[s - 1]
            ax.scatter([TT_R * np.cos(ta)], [TT_R * np.sin(ta)], marker='*', s=260,
                       color=GRIP, edgecolor=INK, lw=0.8, zorder=4)
            ax.axvline(z[s - 1], color=LINK, lw=1.6, ls='--', zorder=1)
            ax.text(z[s - 1] + 6, -TT_R - 32, f'x read: {z[s - 1]:.0f} mm', ha='left',
                    va='top', fontsize=10, color=LINK)
            label = f'after reading {s}'
        else:
            label = 'start: 1000 guesses'
            ax.text(0, -TT_R - 32, 'spread all round', ha='center', va='top',
                    fontsize=10, color=MUTED)
        ax.set_xlim(-TT_R - 40, TT_R + 40)
        ax.set_ylim(-TT_R - 60, TT_R + 30)
        _title(ax, label, 11.5)
    fig.text(0.5, 0.0, 'Green dots: guesses, drawn larger when their weight is larger.  '
             'Red star: the true part.  Blue dashed line: the x the camera read.',
             ha='center', fontsize=10.5, color=MUTED)
    fig.tight_layout(w_pad=1)
    _save(fig, 'kalman-filter', 'particles-on-a-turntable.svg')
    for s in show[1:]:
        p = snaps[s]
        print(f'  particles after reading {s}: share with angle > 0: '
              f'{np.sum(wsnaps[s][wrap(p) > 0]):.3f} (weight)')

    # figure 3: weigh and resample, 12 guesses, one step
    guesses = np.radians(np.linspace(-77, 77, 12))
    zk = z[0]
    w = np.exp(-0.5 * ((zk - TT_R * np.cos(guesses)) / 15.0)**2)
    w = w / w.sum()
    idx = systematic_resample(w, np.random.default_rng(2))
    counts = np.bincount(idx, minlength=12)
    print(f'  resample demo: guesses {np.round(np.degrees(guesses), 1)} reading {zk:.1f}, weights {np.round(w, 3)}, copies {counts}')
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), facecolor='white')
    ax = axes[0]
    _plot_axes(ax, 'guess of the angle (degrees)', 'weight')
    ax.bar(np.degrees(guesses), w, width=7, color=SLIDE)
    for gdeg, wi in zip(np.degrees(guesses), w):
        ax.text(gdeg, wi + 0.008, f'{wi:.2f}', ha='center', va='bottom', fontsize=9,
                color=INK)
    ax.set_ylim(0, w.max() * 1.25)
    _title(ax, f'Weigh: how well does each guess explain x = {zk:.0f} mm?', 11.5)
    ax = axes[1]
    _plot_axes(ax, 'guess of the angle (degrees)', 'copies kept')
    ax.bar(np.degrees(guesses), counts, width=7, color=LINK)
    ax.set_ylim(0, counts.max() + 1)
    ax.set_yticks(range(counts.max() + 2))
    _title(ax, 'Resample: 12 new guesses, copied in proportion to weight', 11.5)
    for a in axes:
        a.set_xlim(-85, 85)
    fig.tight_layout(w_pad=2.5)
    _save(fig, 'kalman-filter', 'weigh-and-resample.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    sysid_probe_moves()
    sysid_friction_fit()
    sysid_rls_drift()
    sysid_uncertainty()
    kalman_bent_measurement()
    kalman_turntable()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
