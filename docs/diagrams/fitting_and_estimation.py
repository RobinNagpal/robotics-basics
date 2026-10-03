"""Generate the diagrams for docs/06_programming-techniques/04_fitting-and-estimation/.

This covers 01_overview, 02_least-squares-fitting, 03_ransac and 04_kalman-filter.
Each document's pictures go to a folder named after it, under
docs/images/fitting-and-estimation/.

Run with:  pixi run python ../docs/diagrams/fitting_and_estimation.py
Add --png <dir> to also write PNG copies for checking.

Every result drawn here is computed for real. The points come from a seeded
random generator, the lines, planes and circles are real least-squares fits,
RANSAC really runs on the drawn points, and the Kalman filter really runs on the
drawn measurements. The script prints the numbers the documents quote.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Ellipse  # noqa: E402
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

TABLE: str = '#eadfcb'
TABLE_DARK: str = '#b89f74'
PURPLE: str = '#8e5bb5'

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small drawing helpers
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


def _style_3d(ax, xlabel: str = 'x (mm)', ylabel: str = 'y (mm)',
              zlabel: str = 'z (mm)') -> None:
    ax.set_facecolor('white')
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((1, 1, 1, 0))
        axis._axinfo['grid']['color'] = GRID
    ax.tick_params(labelsize=8, colors=MUTED)
    ax.set_xlabel(xlabel, fontsize=10, color=INK, labelpad=6)
    ax.set_ylabel(ylabel, fontsize=10, color=INK, labelpad=6)
    ax.set_zlabel(zlabel, fontsize=10, color=INK, labelpad=4)


# --------------------------------------------------------------------------
# the techniques themselves, written out so the pictures are true
# --------------------------------------------------------------------------

def fit_line(x: Arr, y: Arr) -> tuple[float, float]:
    """Least-squares line y = m x + c, from the normal equations."""
    a = np.column_stack([x, np.ones_like(x)])
    m, c = np.linalg.solve(a.T @ a, a.T @ y)
    return float(m), float(c)


def fit_plane_svd(pts: Arr) -> tuple[Arr, Arr, Arr]:
    """Plane through a point cloud: (centre, normal, singular values)."""
    centre = pts.mean(axis=0)
    _, s, vt = np.linalg.svd(pts - centre, full_matrices=False)
    normal = vt[2]
    if normal[2] < 0:
        normal = -normal
    return centre, normal, s


def fit_circle(x: Arr, y: Arr) -> tuple[float, float, float]:
    """Algebraic (Kasa) circle fit: x^2 + y^2 = 2 a x + 2 b y + k is linear in a, b, k."""
    a_mat = np.column_stack([2 * x, 2 * y, np.ones_like(x)])
    a, b, k = np.linalg.lstsq(a_mat, x**2 + y**2, rcond=None)[0]
    r = float(np.sqrt(k + a * a + b * b))
    return float(a), float(b), r


def ransac_line(x: Arr, y: Arr, tries: int, tol: float,
                rng: np.random.Generator) -> dict:
    """RANSAC for a line. Keeps a log of every try so the pictures can show them."""
    best_count, best = -1, None
    log = []
    for _ in range(tries):
        i, j = rng.choice(len(x), 2, replace=False)
        if x[i] == x[j]:
            continue
        m = (y[j] - y[i]) / (x[j] - x[i])
        c = y[i] - m * x[i]
        dist = np.abs(m * x - y + c) / np.sqrt(m * m + 1)
        inl = dist < tol
        log.append((i, j, m, c, int(inl.sum())))
        if inl.sum() > best_count:
            best_count, best = int(inl.sum()), (i, j, m, c, inl)
    i, j, m, c, inl = best
    m2, c2 = fit_line(x[inl], y[inl])            # refit on the inliers
    dist = np.abs(m2 * x - y + c2) / np.sqrt(m2 * m2 + 1)
    return {'sample': (i, j), 'm0': m, 'c0': c, 'm': m2, 'c': c2,
            'inliers': dist < tol, 'count0': best_count, 'log': log}


def ransac_plane(pts: Arr, tries: int, tol: float,
                 rng: np.random.Generator) -> tuple[Arr, Arr, Arr]:
    """RANSAC for a plane. Returns (centre, normal, inlier mask) after a refit."""
    best_count, best_inl = -1, None
    for _ in range(tries):
        p = pts[rng.choice(len(pts), 3, replace=False)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if np.linalg.norm(n) < 1e-9:
            continue
        n = n / np.linalg.norm(n)
        inl = np.abs((pts - p[0]) @ n) < tol
        if inl.sum() > best_count:
            best_count, best_inl = int(inl.sum()), inl
    centre, normal, _ = fit_plane_svd(pts[best_inl])
    inl = np.abs((pts - centre) @ normal) < tol
    return centre, normal, inl


def ransac_tries(p: float, w: float, s: int) -> float:
    """Tries needed to draw one all-inlier sample with probability p."""
    return float(np.log(1 - p) / np.log(1 - w**s))


def kalman_1d(z: Arr, x0: float, p0: float, q: float, r: float,
              u: float = 0.0) -> tuple[Arr, Arr, Arr, Arr, Arr]:
    """Scalar Kalman filter. Returns predicted mean and variance, gain, and updated
    mean and variance, one per measurement. u is a known change per step."""
    x, p = x0, p0
    xp, pp, ks, xs, ps = [], [], [], [], []
    for zk in z:
        x, p = x + u, p + q                     # predict
        xp.append(x)
        pp.append(p)
        if np.isnan(zk):                        # no measurement: keep the prediction
            ks.append(0.0)
        else:
            k = p / (p + r)                     # update
            x, p = x + k * (zk - x), (1 - k) * p
            ks.append(k)
        xs.append(x)
        ps.append(p)
    return tuple(np.array(v) for v in (xp, pp, ks, xs, ps))


def kalman_cv_2d(z: Arr, dt: float, q: float, r: float) -> tuple[Arr, Arr]:
    """Constant-velocity Kalman filter in the plane. State (x, y, vx, vy).
    Rows of z that are NaN are missed detections. Returns means and covariances."""
    f = np.eye(4)
    f[0, 2] = f[1, 3] = dt
    g = np.array([[dt**2 / 2, 0], [0, dt**2 / 2], [dt, 0], [0, dt]])
    qm = g @ g.T * q
    h = np.zeros((2, 4))
    h[0, 0] = h[1, 1] = 1
    rm = np.eye(2) * r
    x = np.array([z[0, 0], z[0, 1], 0.0, 0.0])
    p = np.diag([r, r, 100.0**2, 100.0**2])
    xs, ps = [x.copy()], [p.copy()]
    for zk in z[1:]:
        x = f @ x
        p = f @ p @ f.T + qm
        if not np.isnan(zk[0]):
            s = h @ p @ h.T + rm
            k = p @ h.T @ np.linalg.inv(s)
            x = x + k @ (zk - h @ x)
            p = (np.eye(4) - k @ h) @ p
        xs.append(x.copy())
        ps.append(p.copy())
    return np.array(xs), np.array(ps)


# --------------------------------------------------------------------------
# the data every picture uses, made once
# --------------------------------------------------------------------------

# Five points along the edge of a box, as a camera found them, in millimetres.
EDGE_X: Arr = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
EDGE_Y: Arr = np.array([1.0, 7.2, 11.9, 15.8, 19.4])


def ransac_points() -> tuple[Arr, Arr, Arr]:
    """40 points on a line (a table edge seen side-on) and 15 stray points."""
    rng = np.random.default_rng(7)
    xin = rng.uniform(0, 200, 40)
    yin = 0.25 * xin + 20 + rng.normal(0, 1.5, 40)
    xout = rng.uniform(0, 200, 15)
    yout = rng.uniform(40, 110, 15)
    x = np.concatenate([xin, xout])
    y = np.concatenate([yin, yout])
    truth = np.concatenate([np.ones(40, bool), np.zeros(15, bool)])
    return x, y, truth


def table_scene() -> Arr:
    """A depth camera's view of a table with a box and a cup on it, in millimetres."""
    rng = np.random.default_rng(3)
    gx, gy = np.meshgrid(np.arange(0, 400, 10.0), np.arange(0, 300, 10.0))
    table = np.column_stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)])
    # the objects hide the table under them
    under_box = (table[:, 0] > 80) & (table[:, 0] < 160) & (table[:, 1] > 60) & (table[:, 1] < 150)
    under_cup = (table[:, 0] - 280)**2 + (table[:, 1] - 180)**2 < 40**2
    table = table[~under_box & ~under_cup]
    # box 80 x 90 x 60: its top and its two faces toward the camera
    bx, by = np.meshgrid(np.arange(80, 161, 10.0), np.arange(60, 151, 10.0))
    top = np.column_stack([bx.ravel(), by.ravel(), np.full(bx.size, 60.0)])
    fz, fx = np.meshgrid(np.arange(10, 60, 10.0), np.arange(80, 161, 10.0))
    front = np.column_stack([fx.ravel(), np.full(fx.size, 60.0), fz.ravel()])
    fz, fy = np.meshgrid(np.arange(10, 60, 10.0), np.arange(60, 151, 10.0))
    side = np.column_stack([np.full(fy.size, 160.0), fy.ravel(), fz.ravel()])
    # cup of radius 40, 95 high: its wall
    th, hz = np.meshgrid(np.linspace(0, 2 * np.pi, 36, endpoint=False), np.arange(5, 96, 10.0))
    cup = np.column_stack([280 + 40 * np.cos(th.ravel()), 180 + 40 * np.sin(th.ravel()),
                           hz.ravel()])
    pts = np.vstack([table, top, front, side, cup])
    pts = pts + rng.normal(0, 1.5, pts.shape)
    # the table is not quite level in the camera's frame
    pts[:, 2] += 0.03 * pts[:, 0] - 0.02 * pts[:, 1]
    # stray readings, as a real depth camera gives at edges
    stray = np.column_stack([rng.uniform(0, 400, 25), rng.uniform(0, 300, 25),
                             rng.uniform(-30, 120, 25)])
    return np.vstack([pts, stray])


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

def overview_three_jobs() -> None:
    """One noisy input, three kinds of answer: a line, a line despite outliers, a steady number."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), facecolor='white')

    # 1. least squares through noisy points
    rng = np.random.default_rng(1)
    x = np.linspace(0, 100, 15)
    y = 0.4 * x + 10 + rng.normal(0, 2.5, x.size)
    m, c = fit_line(x, y)
    ax = axes[0]
    _plot_axes(ax, 'along the edge (mm)', 'height (mm)')
    ax.scatter(x, y, s=30, color=LINK, zorder=3, label='measured points')
    xx = np.array([0, 100])
    ax.plot(xx, m * xx + c, color=JOINT, lw=2.5, zorder=4, label='least-squares line')
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, '1. A clean shape from noisy points')

    # 2. the same with outliers: least squares is pulled, RANSAC is not
    x, y, _ = ransac_points()
    m_ls, c_ls = fit_line(x, y)
    res = ransac_line(x, y, 100, 4.0, np.random.default_rng(11))
    ax = axes[1]
    _plot_axes(ax, 'along the edge (mm)', 'height (mm)')
    ax.scatter(x[res['inliers']], y[res['inliers']], s=26, color=LINK, zorder=3,
               label='points on the edge')
    ax.scatter(x[~res['inliers']], y[~res['inliers']], s=26, color=GRIP, marker='x',
               zorder=3, label='stray points')
    xx = np.array([0, 200])
    ax.plot(xx, m_ls * xx + c_ls, color=MUTED, lw=2, ls='--', zorder=4,
            label='least squares (pulled up)')
    ax.plot(xx, res['m'] * xx + res['c'], color=JOINT, lw=2.5, zorder=4, label='RANSAC')
    ax.set_ylim(0, 125)
    ax.legend(fontsize=9.5, loc='upper left', frameon=False, ncol=2)
    _title(ax, '2. The right shape despite stray points')

    # 3. Kalman smoothing of a reading over time
    rng = np.random.default_rng(5)
    n = 60
    truth = 400.0
    z = truth + rng.normal(0, 4.0, n)
    _, _, _, xs, ps = kalman_1d(z, z[0], 16.0, 0.01, 16.0)
    t = np.arange(n) * 0.1
    ax = axes[2]
    _plot_axes(ax, 'time (s)', 'distance to table (mm)')
    ax.scatter(t, z, s=16, color=LINK, zorder=3, label='raw readings')
    ax.plot(t, xs, color=JOINT, lw=2.5, zorder=4, label='Kalman estimate')
    ax.axhline(truth, color=SLIDE, lw=1.2, ls=':', zorder=2, label='true distance')
    ax.set_ylim(385, 420)
    ax.legend(fontsize=10, loc='upper right', frameon=False, ncol=1)
    _title(ax, '3. A steady number from a noisy reading')

    fig.tight_layout(w_pad=2.5)
    _save(fig, 'overview', 'three-jobs.svg')


def overview_table_and_cup() -> None:
    """One arm task, two techniques: find the table plane, then fit the cup's rim."""
    pts = table_scene()
    centre, normal, inl = ransac_plane(pts, 200, 5.0, np.random.default_rng(2))
    fig = plt.figure(figsize=(13, 5.4), facecolor='white')

    ax = fig.add_subplot(1, 2, 1, projection='3d')
    _style_3d(ax)
    ax.scatter(*pts[inl].T, s=4, color=TABLE_DARK, alpha=0.6, depthshade=False)
    ax.scatter(*pts[~inl].T, s=6, color=LINK, depthshade=False)
    ax.view_init(elev=24, azim=-70)
    ax.set_box_aspect((400, 300, 190))
    ax.set_title('RANSAC finds the table plane (brown)\nand leaves the objects (blue)',
                 fontsize=12, color=INK, weight='bold')

    # the cup's points seen from above: the near half of its rim, fitted with a circle
    rest = pts[~inl]
    near_cup = (np.hypot(rest[:, 0] - 280, rest[:, 1] - 180) < 50) & (rest[:, 2] > 60)
    cup = rest[near_cup]
    # a camera in front of the table sees only the half of the wall facing it
    seen = cup[cup[:, 1] < 180]
    a, b, r = fit_circle(seen[:, 0], seen[:, 1])
    ax = fig.add_subplot(1, 2, 2)
    _plot_axes(ax, 'x (mm)', 'y (mm)')
    ax.set_aspect('equal')
    ax.scatter(seen[:, 0], seen[:, 1], s=18, color=LINK, zorder=3,
               label='cup wall points the camera sees')
    ax.add_patch(Circle((a, b), r, fill=False, color=JOINT, lw=2.5, zorder=4))
    ax.plot([], [], color=JOINT, lw=2.5, label=f'least-squares circle, r = {r:.1f} mm')
    ax.scatter([a], [b], s=90, marker='+', color=GRIP, lw=2.5, zorder=5,
               label=f'fitted centre ({a:.0f}, {b:.0f})')
    ax.set_xlim(215, 345)
    ax.set_ylim(120, 250)
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'Least squares turns half a rim\ninto a centre and a radius')
    fig.tight_layout(w_pad=3)
    _save(fig, 'overview', 'table-and-cup.svg')
    print(f'overview: table plane inliers {inl.sum()} of {len(pts)}; '
          f'cup circle centre ({a:.1f}, {b:.1f}) r {r:.1f} from {len(seen)} points')


# --------------------------------------------------------------------------
# 02_least-squares-fitting
# --------------------------------------------------------------------------

def ls_residuals() -> None:
    """The five edge points, a guessed line and the least-squares line, with residuals."""
    x, y = EDGE_X, EDGE_Y
    m, c = fit_line(x, y)
    mg = (y[-1] - y[0]) / (x[-1] - x[0])            # the line through the end points
    cg = y[0]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), facecolor='white', sharey=True)
    for ax, (mm, cc, name, col) in zip(axes, [(mg, cg, 'Line through the two end points', MUTED),
                                              (m, c, 'Least-squares line', JOINT)]):
        _plot_axes(ax, 'along the edge, x (mm)', 'across, y (mm)')
        xx = np.array([-3, 43])
        ax.plot(xx, mm * xx + cc, color=col, lw=2.5, zorder=3)
        pred = mm * x + cc
        for xi, yi, pi in zip(x, y, pred):
            ax.plot([xi, xi], [pi, yi], color=GRIP, lw=2, zorder=2)
            ax.text(xi + 0.9, (yi + pi) / 2, f'{yi - pi:+.2f}', fontsize=10, color=GRIP,
                    va='center', zorder=5)
        ax.scatter(x, y, s=50, color=LINK, zorder=4)
        sse = float(((y - pred)**2).sum())
        ax.text(0.03, 0.95, f'y = {mm:.3f} x + {cc:.2f}\nsum of squared errors = {sse:.2f}',
                transform=ax.transAxes, fontsize=11, va='top', color=INK,
                bbox={'boxstyle': 'round,pad=0.4', 'facecolor': 'white', 'edgecolor': GRID})
        _title(ax, name)
        ax.set_xlim(-4, 46)
        ax.set_ylim(-1, 24)
    fig.tight_layout(w_pad=2)
    _save(fig, 'least-squares-fitting', 'residuals.svg')
    print(f'least squares edge: m {m:.4f} c {c:.4f}; guess m {mg:.4f} c {cg:.4f}')


def ls_error_bowl() -> None:
    """The sum of squared errors for every slope and offset: one lowest point."""
    x, y = EDGE_X, EDGE_Y
    m, c = fit_line(x, y)
    ms = np.linspace(0.30, 0.62, 241)
    cs = np.linspace(-4, 8, 241)
    mm, cc = np.meshgrid(ms, cs)
    sse = ((mm[..., None] * x + cc[..., None] - y)**2).sum(axis=-1)
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')
    _plot_axes(ax, 'slope m', 'offset c (mm)')
    levels = [3, 4, 6, 10, 20, 40, 80, 160]
    cs_ = ax.contour(mm, cc, sse, levels=levels, colors=LINK, linewidths=1.3)
    ax.clabel(cs_, fontsize=9, fmt='%g')
    ax.scatter([m], [c], s=120, color=JOINT, zorder=5, edgecolor=INK)
    ax.annotate(f'lowest point\nm = {m:.3f}, c = {c:.2f}\nsum = {((m * x + c - y)**2).sum():.2f}',
                xy=(m, c), xytext=(0.50, 5.6), fontsize=11, color=INK,
                bbox={'boxstyle': 'round,pad=0.3', 'facecolor': 'white', 'edgecolor': GRID},
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.4})
    mg = (y[-1] - y[0]) / (x[-1] - x[0])
    ax.scatter([mg], [y[0]], s=80, color=MUTED, zorder=5, edgecolor=INK)
    sse_g = float(((mg * x + y[0] - y)**2).sum())
    ax.annotate(f'line through the\ntwo end points\nsum = {sse_g:.2f}', xy=(mg, y[0]), xytext=(0.33, -2.8),
                fontsize=10.5, color=INK,
                bbox={'boxstyle': 'round,pad=0.3', 'facecolor': 'white', 'edgecolor': GRID},
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.2})
    _title(ax, 'Sum of squared errors for every line (contours)')
    _save(fig, 'least-squares-fitting', 'error-bowl.svg')


def ls_svd_plane() -> None:
    """Points on the tilted face of a board, its plane and its three directions from the SVD."""
    rng = np.random.default_rng(4)
    n = 150
    xy = rng.uniform([0, 0], [300, 200], (n, 2))
    z = 0.25 * xy[:, 0] - 0.35 * xy[:, 1] + rng.normal(0, 1.0, n)
    pts = np.column_stack([xy, z])
    centre, normal, s = fit_plane_svd(pts)
    _, _, vt = np.linalg.svd(pts - centre, full_matrices=False)
    dist = (pts - centre) @ normal
    rms = float(np.sqrt((dist**2).mean()))
    spread = s / np.sqrt(n)

    fig = plt.figure(figsize=(13.5, 5.8), facecolor='white')
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    _style_3d(ax)
    gx, gy = np.meshgrid(np.linspace(0, 300, 7), np.linspace(0, 200, 5))
    gz = centre[2] - (normal[0] * (gx - centre[0]) + normal[1] * (gy - centre[1])) / normal[2]
    ax.plot_surface(gx, gy, gz, color=LINK_PALE, alpha=0.35, edgecolor=LINK, lw=0.3)
    ax.scatter(*pts.T, s=9, color=LINK, depthshade=False)
    for d, length, col, name in [(vt[0], 2 * spread[0], PURPLE, 'longest'),
                                 (vt[1], 2 * spread[1], PURPLE, 'middle'),
                                 (normal, 70, GRIP, 'normal')]:
        ax.quiver(*centre, *(d * length), color=col, lw=2.5, arrow_length_ratio=0.15)
        ax.text(*(centre + d * (length + 14)), name, color=col, fontsize=11, weight='bold',
                zorder=10, bbox={'boxstyle': 'round,pad=0.15', 'facecolor': 'white',
                                 'edgecolor': 'none', 'alpha': 0.85})
    ax.view_init(elev=38, azim=-115)
    ax.set_box_aspect((300, 200, 170))
    ax.set_title('Points on a tilted face, the fitted plane\nand its three directions',
                 fontsize=12, color=INK, weight='bold', pad=14)

    ax = fig.add_subplot(1, 2, 2)
    _plot_axes(ax, '', 'spread of the points (mm)')
    names = ['longest', 'middle', 'thinnest\n= the normal']
    ax.bar(names, spread, color=[PURPLE, PURPLE, GRIP], width=0.6, zorder=3)
    for i, v in enumerate(spread):
        ax.text(i, v + 2, f'{v:.1f} mm', ha='center', fontsize=11, color=INK)
    ax.set_ylim(0, spread[0] * 1.2)
    ax.tick_params(axis='x', labelsize=11)
    _title(ax, 'How far the points spread in each direction')
    fig.tight_layout(w_pad=2)
    _save(fig, 'least-squares-fitting', 'svd-plane.svg')
    print(f'svd plane: normal {np.round(normal, 4)} spreads {np.round(spread, 2)} rms {rms:.3f}')


def ls_circle_rim() -> None:
    """The near side of a glass's rim seen from above: the mean is not the centre, the fit is."""
    rng = np.random.default_rng(6)
    true_c, true_r = np.array([120.0, 80.0]), 40.0
    th = np.linspace(np.deg2rad(200), np.deg2rad(340), 18)
    x = true_c[0] + true_r * np.cos(th) + rng.normal(0, 0.6, th.size)
    y = true_c[1] + true_r * np.sin(th) + rng.normal(0, 0.6, th.size)
    a, b, r = fit_circle(x, y)
    fig, ax = plt.subplots(figsize=(7.5, 7), facecolor='white')
    _plot_axes(ax, 'x (mm)', 'y (mm)')
    ax.set_aspect('equal')
    ax.add_patch(Circle((a, b), r, fill=False, color=JOINT, lw=2.5, zorder=3))
    ax.scatter(x, y, s=40, color=LINK, zorder=4, label='rim points the camera sees')
    ax.plot([], [], color=JOINT, lw=2.5, label=f'fitted circle, r = {r:.1f} mm')
    ax.scatter([a], [b], s=160, marker='+', color=SLIDE, lw=3, zorder=5,
               label=f'fitted centre ({a:.1f}, {b:.1f})')
    ax.scatter([x.mean()], [y.mean()], s=80, marker='x', color=GRIP, lw=2.5, zorder=5,
               label=f'mean of the points ({x.mean():.1f}, {y.mean():.1f})')
    ax.annotate('', xy=(120, 4), xytext=(120, 22),
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.6})
    ax.text(123, 13, 'the camera is this way', fontsize=10, color=MUTED, va='center')
    ax.set_xlim(60, 180)
    ax.set_ylim(0, 150)
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'A circle fitted to the near half of a rim')
    _save(fig, 'least-squares-fitting', 'circle-from-half-a-rim.svg')
    print(f'circle: true (120,80) r40; fit ({a:.2f},{b:.2f}) r {r:.2f}; '
          f'mean ({x.mean():.2f},{y.mean():.2f})')


# --------------------------------------------------------------------------
# 03_ransac
# --------------------------------------------------------------------------

def ransac_best_line() -> None:
    x, y, truth = ransac_points()
    m_ls, c_ls = fit_line(x, y)
    res = ransac_line(x, y, 100, 4.0, np.random.default_rng(11))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor='white', sharey=True)
    xx = np.array([0, 200])
    for k, ax in enumerate(axes):
        _plot_axes(ax, 'along the edge, x (mm)', 'height, y (mm)')
        ax.set_xlim(-5, 205)
        ax.set_ylim(0, 165)
        ax.plot(xx, 0.25 * xx + 20, color=SLIDE, lw=1.3, ls=':', zorder=2, label='true edge')
    ax = axes[0]
    ax.scatter(x, y, s=28, color=LINK, zorder=3, label='all 55 points')
    ax.plot(xx, m_ls * xx + c_ls, color=MUTED, lw=2.5, ls='--', zorder=4,
            label=f'least squares: y = {m_ls:.3f} x + {c_ls:.1f}')
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'Least squares on everything')
    ax = axes[1]
    band = 4.0 * np.sqrt(res['m']**2 + 1)
    ax.fill_between(xx, res['m'] * xx + res['c'] - band, res['m'] * xx + res['c'] + band,
                    color=JOINT, alpha=0.18, zorder=1, label='within 4 mm of the line')
    inl = res['inliers']
    ax.scatter(x[inl], y[inl], s=28, color=LINK, zorder=3, label=f'{inl.sum()} inliers')
    ax.scatter(x[~inl], y[~inl], s=34, color=GRIP, marker='x', zorder=3,
               label=f'{(~inl).sum()} outliers, ignored')
    ax.plot(xx, res['m'] * xx + res['c'], color=JOINT, lw=2.5, zorder=4,
            label=f'RANSAC: y = {res["m"]:.3f} x + {res["c"]:.1f}')
    ax.legend(fontsize=10, loc='upper left', frameon=False)
    _title(ax, 'RANSAC: the best line ignores the outliers')
    fig.tight_layout(w_pad=2)
    _save(fig, 'ransac', 'best-line.svg')
    agree = int((inl == truth).sum())
    print(f'ransac line: LS m {m_ls:.4f} c {c_ls:.3f}; RANSAC m {res["m"]:.4f} c {res["c"]:.3f} '
          f'inliers {inl.sum()} (first-pass {res["count0"]}); labels agree on {agree}/55')


def ransac_three_tries() -> None:
    """Three of the tries RANSAC made on the same points, and how many points agreed."""
    x, y, _ = ransac_points()
    res = ransac_line(x, y, 100, 4.0, np.random.default_rng(11))
    log = res['log']
    counts = [t[4] for t in log]
    best_k = int(np.argmax(counts))
    middling = next(k for k, t in enumerate(log) if 12 <= t[4] <= 30)
    picks = [0, middling, best_k]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), facecolor='white', sharey=True)
    xx = np.array([0, 200])
    for ax, k in zip(axes, picks):
        i, j, m, c, n = log[k]
        _plot_axes(ax, 'x (mm)', 'y (mm)' if k == 0 else '')
        band = 4.0 * np.sqrt(m * m + 1)
        ax.fill_between(xx, m * xx + c - band, m * xx + c + band, color=JOINT, alpha=0.18,
                        zorder=1)
        dist = np.abs(m * x - y + c) / np.sqrt(m * m + 1)
        near = dist < 4.0
        ax.scatter(x[~near], y[~near], s=22, color=GRID, edgecolor=MUTED, lw=0.5, zorder=3)
        ax.scatter(x[near], y[near], s=26, color=LINK, zorder=3)
        ax.plot(xx, m * xx + c, color=JOINT, lw=2, zorder=4)
        ax.scatter(x[[i, j]], y[[i, j]], s=130, facecolor='none', edgecolor=GRIP, lw=2.5,
                   zorder=5)
        ax.set_xlim(-5, 205)
        ax.set_ylim(0, 125)
        label = 'best try' if k == best_k else 'try'
        _title(ax, f'{label} {k + 1}: {n} points agree')
    fig.text(0.5, -0.02, 'Red rings: the two points picked at random.  '
             'Blue: points within 4 mm of their line.  Grey: the rest.',
             ha='center', fontsize=11, color=MUTED)
    fig.tight_layout(w_pad=1.5)
    _save(fig, 'ransac', 'three-tries.svg')
    print(f'ransac tries: shown {[p + 1 for p in picks]} counts {[log[p][4] for p in picks]} '
          f'of {len(log)} tries')


def ransac_how_many_tries() -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor='white')
    _plot_axes(ax, 'share of points that are outliers', 'tries needed for 99% success')
    out = np.linspace(0.01, 0.8, 159)
    w = 1 - out
    for s, name, col in [(2, 'line (2 points per try)', LINK),
                         (3, 'plane (3 points per try)', JOINT),
                         (6, 'a 6-point model', GRIP)]:
        ax.plot(out, [ransac_tries(0.99, wi, s) for wi in w], color=col, lw=2.5, label=name)
    ax.set_yscale('log')
    ax.set_xlim(0, 0.8)
    ax.set_ylim(1, 1e5)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    for frac in (0.5,):
        n3 = ransac_tries(0.99, 1 - frac, 3)
        ax.scatter([frac], [n3], s=60, color=JOINT, zorder=5, edgecolor=INK)
        ax.annotate(f'half the points are outliers:\na plane needs {np.ceil(n3):.0f} tries',
                    xy=(frac, n3), xytext=(0.12, 700), fontsize=10.5, color=INK,
                    arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.3})
    ax.legend(fontsize=10.5, loc='upper left', frameon=False)
    _title(ax, 'How many tries RANSAC needs')
    _save(fig, 'ransac', 'how-many-tries.svg')


def ransac_table_plane() -> None:
    pts = table_scene()
    centre, normal, inl = ransac_plane(pts, 200, 5.0, np.random.default_rng(2))
    fig = plt.figure(figsize=(14, 5.6), facecolor='white')
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    _style_3d(ax)
    ax.scatter(*pts.T, s=4, color=LINK, depthshade=False)
    ax.view_init(elev=24, azim=-70)
    ax.set_box_aspect((400, 300, 190))
    ax.set_title(f'The depth camera\'s {len(pts)} points', fontsize=12, color=INK,
                 weight='bold')
    ax = fig.add_subplot(1, 2, 2, projection='3d')
    _style_3d(ax)
    ax.scatter(*pts[inl].T, s=3, color=TABLE_DARK, alpha=0.35, depthshade=False)
    ax.scatter(*pts[~inl].T, s=7, color=LINK, depthshade=False)
    ax.view_init(elev=24, azim=-70)
    ax.set_box_aspect((400, 300, 190))
    ax.set_title(f'{inl.sum()} on the table plane (brown), {(~inl).sum()} left over',
                 fontsize=12, color=INK, weight='bold')
    fig.tight_layout(w_pad=1)
    _save(fig, 'ransac', 'table-plane.svg')
    print(f'ransac plane: normal {np.round(normal, 4)} centre z {centre[2]:.2f} '
          f'inliers {inl.sum()} of {len(pts)}')


# --------------------------------------------------------------------------
# 04_kalman-filter
# --------------------------------------------------------------------------

# The worked example: a block on a conveyor that moves 5 mm per step (50 mm/s,
# 10 pictures a second). The camera measures its position with noise.
CONV_Z: Arr = np.array([107.0, 109.0, 118.0, 121.0])
CONV_X0, CONV_P0, CONV_Q, CONV_R, CONV_U = 100.0, 25.0, 1.0, 16.0, 5.0


def _gauss(x: Arr, mu: float, var: float) -> Arr:
    return np.exp(-(x - mu)**2 / (2 * var)) / np.sqrt(2 * np.pi * var)


def kalman_predict_update() -> None:
    """Step 1 of the worked example as three bell curves."""
    xp, pp, ks, xs, ps = kalman_1d(CONV_Z, CONV_X0, CONV_P0, CONV_Q, CONV_R, CONV_U)
    grid = np.linspace(80, 130, 600)
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='white')
    _plot_axes(ax, 'position along the belt (mm)', 'how likely')
    ax.set_yticks([])
    curves = [(CONV_X0, CONV_P0, MUTED, 'last estimate', ':'),
              (xp[0], pp[0], LINK, 'prediction', '-'),
              (CONV_Z[0], CONV_R, GRIP, 'measurement', '-'),
              (xs[0], ps[0], JOINT, 'updated estimate', '-')]
    for mu, var, col, name, ls in curves:
        g = _gauss(grid, mu, var)
        ax.plot(grid, g, color=col, lw=2.5 if name == 'updated estimate' else 2, ls=ls,
                label=f'{name}: {mu:.1f} mm, spread {np.sqrt(var):.1f} mm')
        if name != 'last estimate':
            ax.fill_between(grid, g, color=col, alpha=0.08)
    ax.annotate('', xy=(xp[0], 0.092), xytext=(CONV_X0, 0.092),
                arrowprops={'arrowstyle': '-|>', 'color': LINK, 'lw': 1.6})
    ax.text(CONV_X0 - 0.5, 0.092, 'predict: +5 mm', ha='right', va='center', fontsize=10.5,
            color=LINK)
    ax.set_ylim(0, 0.175)
    ax.set_xlim(80, 130)
    ax.legend(fontsize=10.5, loc='upper left', frameon=False)
    _title(ax, 'One predict and update step')
    _save(fig, 'kalman-filter', 'predict-and-update.svg')
    print('kalman worked example:')
    for k in range(len(CONV_Z)):
        print(f'  step {k + 1}: predict {xp[k]:.2f} var {pp[k]:.2f} | z {CONV_Z[k]:.0f} '
              f'K {ks[k]:.3f} | update {xs[k]:.2f} var {ps[k]:.2f} sd {np.sqrt(ps[k]):.2f}')


def kalman_smoothing() -> None:
    """A noisy distance reading, a slow filter and a quick filter, and a 20 mm step."""
    rng = np.random.default_rng(5)
    n = 60
    truth = np.full(n, 400.0)
    truth[35:] = 380.0
    z = truth + rng.normal(0, 4.0, n)
    t = np.arange(n) * 0.1
    _, _, _, xs_slow, ps_slow = kalman_1d(z, z[0], 16.0, 0.01, 16.0)
    _, _, _, xs_fast, _ = kalman_1d(z, z[0], 16.0, 4.0, 16.0)
    fig, ax = plt.subplots(figsize=(11, 5), facecolor='white')
    _plot_axes(ax, 'time (s)', 'distance to the table (mm)')
    ax.plot(t, truth, color=SLIDE, lw=1.5, ls=':', zorder=2, label='true distance')
    ax.scatter(t, z, s=20, color=LINK, zorder=3, label='raw readings (spread 4 mm)')
    sd = np.sqrt(ps_slow)
    ax.fill_between(t, xs_slow - sd, xs_slow + sd, color=JOINT, alpha=0.2, zorder=1)
    ax.plot(t, xs_slow, color=JOINT, lw=2.5, zorder=4,
            label='Kalman, small process noise q = 0.01 (band: its own spread)')
    ax.plot(t, xs_fast, color=PURPLE, lw=2, zorder=4, label='Kalman, larger process noise q = 4')
    ax.annotate('the arm lowers\nthe camera 20 mm', xy=(3.5, 381), xytext=(1.6, 374),
                fontsize=10.5, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.3})
    ax.set_ylim(368, 428)
    ax.legend(fontsize=10, loc='upper right', frameon=False)
    _title(ax, 'Smoothing a noisy depth reading')
    _save(fig, 'kalman-filter', 'smoothing-a-reading.svg')
    err_raw = np.abs(z[10:35] - truth[10:35]).mean()
    err_slow = np.abs(xs_slow[10:35] - truth[10:35]).mean()
    err_fast = np.abs(xs_fast[10:35] - truth[10:35]).mean()
    lag_slow = next((k - 35 for k in range(35, n) if xs_slow[k] < 385), None)
    lag_fast = next((k - 35 for k in range(35, n) if xs_fast[k] < 385), None)
    print(f'smoothing: mean abs error steps 11-35 raw {err_raw:.2f} slow {err_slow:.2f} '
          f'fast {err_fast:.2f}; steps to get within 5 mm after the drop slow {lag_slow} '
          f'fast {lag_fast}; slow at end {xs_slow[-1]:.1f}')


def kalman_gain_settles() -> None:
    """The gain and the spread for the steady reading: both settle within a few steps."""
    rng = np.random.default_rng(5)
    z = 400 + rng.normal(0, 4.0, 60)
    _, pp, ks, _, ps = kalman_1d(z, z[0], 16.0, 0.01, 16.0)
    _, _, ks4, _, ps4 = kalman_1d(z, z[0], 16.0, 4.0, 16.0)
    steps = np.arange(1, 61)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor='white')
    ax = axes[0]
    _plot_axes(ax, 'step', 'Kalman gain K')
    ax.plot(steps, ks, color=JOINT, lw=2.5, marker='o', ms=3, label='q = 0.01')
    ax.plot(steps, ks4, color=PURPLE, lw=2, marker='o', ms=3, label='q = 4')
    ax.set_ylim(0, 0.6)
    ax.legend(fontsize=10.5, frameon=False)
    _title(ax, 'How much each new reading counts')
    ax = axes[1]
    _plot_axes(ax, 'step', 'spread of the estimate (mm)')
    ax.plot(steps, np.sqrt(ps), color=JOINT, lw=2.5, marker='o', ms=3, label='q = 0.01')
    ax.plot(steps, np.sqrt(ps4), color=PURPLE, lw=2, marker='o', ms=3, label='q = 4')
    ax.axhline(4.0, color=LINK, lw=1.3, ls='--')
    ax.text(60, 4.15, 'spread of one raw reading', ha='right', va='bottom', fontsize=10,
            color=LINK)
    ax.set_ylim(0, 5.6)
    ax.legend(fontsize=10.5, frameon=False, loc='upper left')
    _title(ax, 'How sure the filter is')
    fig.tight_layout(w_pad=2.5)
    _save(fig, 'kalman-filter', 'gain-settles.svg')
    print(f'gain: q=0.01 K at steps 1,2,5,10,60 {np.round(ks[[0, 1, 4, 9, 59]], 3)} '
          f'sd end {np.sqrt(ps[-1]):.2f}; q=4 K end {ks4[-1]:.3f} sd end {np.sqrt(ps4[-1]):.2f}')


def kalman_tracking() -> None:
    """A part on a belt, seen by a camera 10 times a second, hidden by the arm for 0.8 s."""
    rng = np.random.default_rng(9)
    dt, n = 0.1, 40
    t = np.arange(n) * dt
    true = np.column_stack([50 + 60 * t, 100 + 15 * t + 10 * np.sin(0.8 * t)])
    z = true + rng.normal(0, 4.0, true.shape)
    hidden = (np.arange(n) >= 18) & (np.arange(n) < 26)
    z[hidden] = np.nan
    xs, ps = kalman_cv_2d(z, dt, q=200.0, r=16.0)
    fig, ax = plt.subplots(figsize=(12, 5.4), facecolor='white')
    _plot_axes(ax, 'x along the belt (mm)', 'y across the belt (mm)')
    ax.set_aspect('equal')
    ax.axvspan(true[18, 0] - 3, true[25, 0] + 3, color=GRID, alpha=0.35, zorder=0)
    ax.text((true[18, 0] + true[25, 0]) / 2, 177, 'the arm hides\nthe part here',
            ha='center', va='top', fontsize=10.5, color=MUTED)
    ax.plot(*true.T, color=SLIDE, lw=1.5, ls=':', zorder=2, label='true path')
    ax.scatter(*z[~hidden].T, s=24, color=LINK, zorder=3, label='camera detections')
    ax.plot(xs[:, 0], xs[:, 1], color=JOINT, lw=2.5, zorder=4, label='Kalman estimate')
    for k in list(range(2, n, 4)) + [25]:
        vals, vecs = np.linalg.eigh(ps[k][:2, :2])
        ang = np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1]))
        w, h = 2 * 2 * np.sqrt(vals[1]), 2 * 2 * np.sqrt(vals[0])
        ax.add_patch(Ellipse(xs[k, :2], w, h, angle=ang, fill=False, color=GRIP, lw=1.4,
                             zorder=5))
    ax.plot([], [], color=GRIP, lw=1.4, label='where the filter thinks it could be (2 spreads)')
    ax.set_ylim(80, 180)
    ax.set_xlim(40, 300)
    ax.legend(fontsize=10, loc='lower right', frameon=False)
    _title(ax, 'Tracking a part on a belt, through a gap in the detections')
    _save(fig, 'kalman-filter', 'tracking-through-a-gap.svg')
    sd_before = np.sqrt(ps[17][0, 0])
    sd_gap = np.sqrt(ps[25][0, 0])
    err_gap = np.linalg.norm(xs[25, :2] - true[25])
    vel = xs[17, 2:]
    raw_err = np.nanmean(np.linalg.norm(z - true, axis=1))
    est_err = np.mean(np.linalg.norm(xs[5:18, :2] - true[5:18], axis=1))
    print(f'tracking: sd x before gap {sd_before:.2f}, at end of gap {sd_gap:.2f}; '
          f'error at end of gap {err_gap:.2f}; velocity before gap {np.round(vel, 1)}; '
          f'mean raw err {raw_err:.2f}, filter err steps 6-18 {est_err:.2f}')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    overview_three_jobs()
    overview_table_and_cup()
    ls_residuals()
    ls_error_bowl()
    ls_svd_plane()
    ls_circle_rim()
    ransac_best_line()
    ransac_three_tries()
    ransac_how_many_tries()
    ransac_table_plane()
    kalman_predict_update()
    kalman_smoothing()
    kalman_gain_settles()
    kalman_tracking()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
