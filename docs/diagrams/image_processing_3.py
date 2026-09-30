"""Generate the diagrams for the additions to
docs/05_programming-techniques/05_image-and-point-cloud-processing/.

This covers three things:

- the Hough transform section of 03_also-used/01_edges-and-contours.md
  (pictures go to images/image-and-point-cloud-processing/edges-and-contours/),
- the k-means and mean shift section of 02_most-used/03_clustering.md
  (pictures go to images/image-and-point-cloud-processing/clustering/),
- the page 03_also-used/02_volumetric-maps.md
  (pictures go to images/image-and-point-cloud-processing/volumetric-maps/).

Run with:  pixi run python ../docs/diagrams/image_processing_3.py
Add --png <dir> to also write PNG copies for checking.
Run with --numbers to print every number the documents quote.

Every result drawn here is computed for real with NumPy: the Hough vote
tables, k-means, mean shift, the log-odds occupancy map built by casting rays,
the quadtree that stores it, the truncated signed distance function and the
Euclidean signed distance field.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'image-and-point-cloud-processing')
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
TABLE: str = '#eadfcb'

CLUSTER_COLOURS: list[str] = [LINK, SLIDE, WRIST, PURPLE, GRIP, JOINT]

EDGES: str = 'edges-and-contours'
CLUSTER: str = 'clustering'
VOLUME: str = 'volumetric-maps'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _plot_axes(ax: Axes, title: str, subtitle: str = '', equal: bool = True,
               ticks: bool = False) -> None:
    ax.set_facecolor('white')
    if equal:
        ax.set_aspect('equal')
    if not ticks:
        ax.set_xticks([])
        ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_title(title, fontsize=11, color=INK, weight='bold', pad=8)
    if subtitle:
        ax.text(0.5, -0.04 if not ticks else -0.16, subtitle, transform=ax.transAxes,
                fontsize=9.5, ha='center', va='top', color=MUTED)


# ==========================================================================
# PART 1: the Hough transform (edges-and-contours)
# ==========================================================================

THETAS: NDArray[np.float64] = np.deg2rad(np.arange(0.0, 180.0, 1.0))   # 180 angles


def hough_lines(pts: NDArray[np.float64], rho_max: float
                ) -> tuple[NDArray[np.int64], NDArray[np.float64]]:
    """Vote table for lines rho = x cos(theta) + y sin(theta), 1 degree by 1 pixel."""
    rhos = np.arange(-rho_max, rho_max + 1.0, 1.0)
    acc = np.zeros((len(rhos), len(THETAS)), dtype=np.int64)
    cols = np.arange(len(THETAS))
    for x, y in pts:
        r = x * np.cos(THETAS) + y * np.sin(THETAS)
        rows = np.round(r + rho_max).astype(int)
        acc[rows, cols] += 1
    return acc, rhos


def hough_peaks(acc: NDArray[np.int64], n: int, gap: int = 6) -> list[tuple[int, int, int]]:
    """The n highest cells, each at least `gap` cells from the ones already taken."""
    a = acc.copy()
    out: list[tuple[int, int, int]] = []
    for _ in range(n):
        r, c = np.unravel_index(np.argmax(a), a.shape)
        out.append((int(r), int(c), int(a[r, c])))
        a[max(0, r - gap):r + gap + 1, max(0, c - gap):c + gap + 1] = 0
        # the angle axis wraps round: theta near 180 is theta near 0 with -rho
    return out


def three_points() -> NDArray[np.float64]:
    """Three points on one line and one point off it, in pixels."""
    return np.array([[10.0, 40.0], [30.0, 30.0], [50.0, 20.0], [22.0, 12.0]])


def table_edge_points() -> NDArray[np.float64]:
    """Canny edge pixels of a table's front edge and a box side, both broken, plus specks."""
    rng = np.random.default_rng(7)
    pts: list[list[float]] = []
    # the table edge: y = 70 - 0.25 x, x from 0 to 119, with two gaps (a cable and a shadow)
    for x in range(0, 120):
        if 30 <= x < 42 or 78 <= x < 86:
            continue
        pts.append([x, round(70 - 0.25 * x)])
    # one vertical side of a box: x = 88, y from 12 to 44, with a gap
    for y in range(12, 45):
        if 24 <= y < 30:
            continue
        pts.append([88, y])
    # scattered specks from texture on the table
    specks = rng.uniform([0, 0], [120, 80], size=(40, 2)).round()
    return np.vstack([np.array(pts, float), specks])


def hough_circle_votes(pts: NDArray[np.float64], r: float, shape: tuple[int, int],
                       n_angles: int = 90) -> NDArray[np.int64]:
    """Each edge point votes for every centre at distance r from it (one vote per cell)."""
    acc = np.zeros(shape, dtype=np.int64)
    a = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
    for x, y in pts:
        cx = np.round(x + r * np.cos(a)).astype(int)
        cy = np.round(y + r * np.sin(a)).astype(int)
        ok = (cx >= 0) & (cx < shape[1]) & (cy >= 0) & (cy < shape[0])
        cells = np.unique(cy[ok] * shape[1] + cx[ok])
        np.add.at(acc.reshape(-1), cells, 1)
    return acc


def cup_rim_points() -> NDArray[np.float64]:
    """Edge pixels of a cup rim seen from above: radius 20 px, centre (40, 38).
    A gripper finger hides the part from 200 to 290 degrees. Some specks are added."""
    rng = np.random.default_rng(3)
    pts: set[tuple[int, int]] = set()
    for deg in np.arange(0, 360, 1.0):
        if 200 <= deg < 290:
            continue
        t = np.deg2rad(deg)
        pts.add((int(round(40 + 20 * np.cos(t))), int(round(38 + 20 * np.sin(t)))))
    rim = np.array(sorted(pts), float)
    specks = rng.uniform([0, 0], [80, 76], size=(25, 2)).round()
    return np.vstack([rim, specks])


CUP_SHAPE: tuple[int, int] = (76, 80)


def hough_one_point_picture() -> None:
    pts = three_points()
    fig, (a1, a2) = _panels(2, (12.5, 4.8))
    _plot_axes(a1, 'In the picture: lines through one point',
               'every line through the orange point is one vote it casts')
    a1.set_xlim(0, 60)
    a1.set_ylim(50, 0)
    x0, y0 = pts[1]
    for deg in range(0, 180, 20):
        t = np.deg2rad(deg)
        d = np.array([-np.sin(t), np.cos(t)])
        p = np.array([x0, y0]) + np.outer([-80, 80], d)
        a1.plot(p[:, 0], p[:, 1], color=LINK_PALE, lw=1.0, zorder=1)
    a1.plot([0, 60], [45, 15], color=SLIDE, lw=2, zorder=2)
    for i, (x, y) in enumerate(pts):
        col = WRIST if i == 1 else (SLIDE if i < 3 else PURPLE)
        a1.plot(x, y, 'o', color=col, ms=10, zorder=3, mec='white')
        a1.text(x + 1.6, y - 1.6, f'({x:.0f}, {y:.0f})', fontsize=9, color=INK, zorder=4)
    a1.text(58, 47, 'the green line holds\nthree of the points', fontsize=9, color=SLIDE,
            ha='right', va='bottom')

    acc, rhos = hough_lines(pts, 80)
    _plot_axes(a2, 'In the vote table: one curve per point',
               '', equal=False, ticks=True)
    deg = np.rad2deg(THETAS)
    for i, (x, y) in enumerate(pts):
        col = WRIST if i == 1 else (SLIDE if i < 3 else PURPLE)
        a2.plot(deg, x * np.cos(THETAS) + y * np.sin(THETAS), color=col, lw=2)
    r, c, v = hough_peaks(acc, 1)[0]
    a2.plot(deg[c], rhos[r], 'o', ms=16, mfc='none', mec=GRIP, mew=2)
    a2.annotate(f'3 curves cross here:\nangle {deg[c]:.0f}°, distance {rhos[r]:.0f} px',
                (deg[c], rhos[r]), (4, -40), fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP))
    a2.set_xlabel('angle of the line (degrees)', fontsize=9.5, color=INK)
    a2.set_ylabel('distance of the line from the corner (px)', fontsize=9.5, color=INK)
    a2.set_xlim(0, 180)
    a2.axhline(0, color=GRID, lw=0.8)
    a2.tick_params(labelsize=8.5, colors=MUTED)
    fig.tight_layout(w_pad=3)
    _save(fig, EDGES, 'hough-one-point-votes.svg')


def hough_accumulator_picture() -> None:
    pts = table_edge_points()
    acc, rhos = hough_lines(pts, 150)
    peaks = hough_peaks(acc, 2)
    fig, axes = _panels(3, (15.5, 4.6))
    a1, a2, a3 = axes
    _plot_axes(a1, 'Edge pixels from Canny',
               f'{len(pts)} pixels: two broken edges and 40 specks')
    a1.scatter(pts[:, 0], pts[:, 1], s=6, color=INK)
    a1.set_xlim(-2, 122)
    a1.set_ylim(82, -2)

    _plot_axes(a2, 'The vote table', 'brighter = more votes; circles = the two peaks',
               equal=False, ticks=True)
    a2.imshow(np.sqrt(acc), aspect='auto', cmap='magma', origin='lower',
              extent=[0, 180, rhos[0], rhos[-1]])
    for r, c, v in peaks:
        a2.plot(np.rad2deg(THETAS[c]), rhos[r], 'o', ms=15, mfc='none', mec='white', mew=2)
        a2.text(np.rad2deg(THETAS[c]) + 7, rhos[r] + 6, f'{v} votes', color='white', fontsize=9.5,
                weight='bold')
    a2.set_xlabel('angle (degrees)', fontsize=9.5, color=INK)
    a2.set_ylabel('distance (px)', fontsize=9.5, color=INK)
    a2.set_ylim(-60, 110)
    a2.tick_params(labelsize=8.5, colors=MUTED)

    _plot_axes(a3, 'The two lines it reports', 'each line runs straight across the gaps')
    a3.scatter(pts[:, 0], pts[:, 1], s=6, color=MUTED)
    for (r, c, v), col in zip(peaks, [GRIP, LINK]):
        t, rho = THETAS[c], rhos[r]
        if abs(np.sin(t)) > 0.5:
            xs = np.array([0, 120.0])
            ys = (rho - xs * np.cos(t)) / np.sin(t)
        else:
            ys = np.array([0, 80.0])
            xs = (rho - ys * np.sin(t)) / np.cos(t)
        a3.plot(xs, ys, color=col, lw=2.2)
    a3.set_xlim(-2, 122)
    a3.set_ylim(82, -2)
    fig.tight_layout(w_pad=2.5)
    _save(fig, EDGES, 'hough-line-accumulator.svg')


def hough_circle_picture() -> None:
    pts = cup_rim_points()
    acc = hough_circle_votes(pts, 20.0, CUP_SHAPE)
    cy, cx = np.unravel_index(np.argmax(acc), acc.shape)
    fig, (a1, a2) = _panels(2, (11.5, 5.0))
    _plot_axes(a1, 'Each edge pixel votes on a circle',
               'three pixels shown; the finger hides a quarter of the rim')
    a1.add_patch(Rectangle((0, 0), 80, 76, color=TABLE, zorder=0))
    a1.add_patch(Rectangle((14, 9), 31, 22, color=MUTED, alpha=0.55, zorder=1))
    a1.text(29, 19, 'gripper\nfinger', ha='center', va='center', fontsize=9, color='white')
    a1.scatter(pts[:, 0], pts[:, 1], s=9, color=INK, zorder=2)
    for (x, y), col in zip([(60, 38), (40, 58), (54, 52)], [LINK, SLIDE, PURPLE]):
        a1.add_patch(Circle((x, y), 20, fill=False, ec=col, lw=1.6, zorder=3))
        a1.plot(x, y, 'o', color=col, ms=8, zorder=4, mec='white')
    a1.plot(cx, cy, '+', color=GRIP, ms=16, mew=2.5, zorder=5)
    a1.annotate('the three circles\nmeet at the centre', (cx, cy), (2, 66), fontsize=9,
                color=GRIP, zorder=5, arrowprops=dict(arrowstyle='->', color=GRIP))
    a1.set_xlim(0, 80)
    a1.set_ylim(76, 0)

    _plot_axes(a2, 'Votes for each possible centre (radius 20)',
               f'the peak is at ({cx}, {cy}) with {acc.max()} votes')
    im = a2.imshow(acc, cmap='magma', origin='upper')
    a2.plot(cx, cy, 'o', ms=16, mfc='none', mec='white', mew=2)
    cb = fig.colorbar(im, ax=a2, fraction=0.045, pad=0.03)
    cb.ax.tick_params(labelsize=8.5)
    cb.set_label('votes', fontsize=9.5)
    fig.tight_layout(w_pad=3)
    _save(fig, EDGES, 'hough-circle-votes.svg')


def circle_radius_scan() -> list[tuple[int, int]]:
    pts = cup_rim_points()
    return [(r, int(hough_circle_votes(pts, float(r), CUP_SHAPE).max())) for r in range(10, 31)]


def hough_radius_picture() -> None:
    scan = circle_radius_scan()
    fig, ax = plt.subplots(figsize=(7.5, 4.0), facecolor='white')
    _plot_axes(ax, 'Trying each radius: the highest peak picks the size', '',
               equal=False, ticks=True)
    rs = [r for r, _ in scan]
    vs = [v for _, v in scan]
    cols = [GRIP if r == 20 else LINK for r in rs]
    ax.bar(rs, vs, color=cols, width=0.75)
    best = max(scan, key=lambda t: t[1])
    ax.text(best[0], best[1] + 3, f'{best[1]} votes\nat radius {best[0]}', ha='center',
            va='bottom', fontsize=9.5, color=GRIP)
    ax.set_xlabel('radius tried (pixels)', fontsize=9.5, color=INK)
    ax.set_ylabel('votes at the best centre', fontsize=9.5, color=INK)
    ax.set_ylim(0, best[1] * 1.3)
    ax.set_xticks(rs[::2])
    ax.tick_params(labelsize=8.5, colors=MUTED)
    fig.tight_layout()
    _save(fig, EDGES, 'hough-circle-radius.svg')


# ==========================================================================
# PART 2: k-means and mean shift (clustering)
# ==========================================================================

def colour_points() -> NDArray[np.float64]:
    """Pixel colours of a picture of red and blue parts on a grey table:
    the (red, blue) values of 300 table, 120 red-part and 80 blue-part pixels."""
    rng = np.random.default_rng(11)
    table = rng.normal([125, 120], [10, 10], size=(300, 2))
    red = rng.normal([205, 55], [12, 10], size=(120, 2))
    blue = rng.normal([60, 185], [10, 12], size=(80, 2))
    return np.clip(np.vstack([table, red, blue]), 0, 255)


def kmeans(pts: NDArray[np.float64], starts: NDArray[np.float64], max_iter: int = 50
           ) -> tuple[NDArray[np.int64], NDArray[np.float64], list[NDArray[np.float64]], float]:
    """Plain k-means from the given starting centres. Returns labels, centres,
    the centres after every round, and the total squared distance."""
    c = starts.copy()
    history = [c.copy()]
    for _ in range(max_iter):
        d = ((pts[:, None, :] - c[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        new = np.array([pts[lab == k].mean(0) if (lab == k).any() else c[k] for k in range(len(c))])
        history.append(new.copy())
        if np.allclose(new, c):
            break
        c = new
    d = ((pts[:, None, :] - c[None, :, :]) ** 2).sum(-1)
    lab = d.argmin(1)
    return lab, c, history, float(d.min(1).sum())


def kmeans_starts(pts: NDArray[np.float64], k: int, seed: int) -> NDArray[np.float64]:
    """Pick k different pixels at random as the starting centres."""
    rng = np.random.default_rng(seed)
    return pts[rng.choice(len(pts), size=k, replace=False)]


KMEANS_SEED: int = 4


def _colour_axes(ax: Axes, title: str, sub: str) -> None:
    _plot_axes(ax, title, sub, equal=True, ticks=True)
    ax.set_xlim(20, 250)
    ax.set_ylim(20, 230)
    ax.set_xlabel('red amount (0 to 255)', fontsize=9, color=INK)
    ax.set_ylabel('blue amount (0 to 255)', fontsize=9, color=INK)
    ax.tick_params(labelsize=8, colors=MUTED)


def kmeans_steps_picture() -> None:
    pts = colour_points()
    starts = kmeans_starts(pts, 3, KMEANS_SEED)
    lab, c, hist, sse = kmeans(pts, starts)
    fig, axes = _panels(3, (15.5, 5.2))

    def draw(ax: Axes, centres: NDArray[np.float64], title: str, sub: str) -> None:
        _colour_axes(ax, title, sub)
        d = ((pts[:, None, :] - centres[None, :, :]) ** 2).sum(-1)
        la = d.argmin(1)
        for k in range(3):
            ax.scatter(pts[la == k, 0], pts[la == k, 1], s=7, color=CLUSTER_COLOURS[k], alpha=0.6)
            ax.plot(centres[k, 0], centres[k, 1], 'X', ms=14, color=CLUSTER_COLOURS[k], mec=INK, mew=1.2)

    draw(axes[0], hist[0], 'Start: 3 centres at random pixels',
         'each pixel joins its nearest centre')
    draw(axes[1], hist[1], 'Round 1: centres move to the average',
         'then every pixel is sorted again')
    for k in range(3):
        axes[1].annotate('', hist[1][k], hist[0][k],
                         arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))
    draw(axes[2], c, f'Done after {len(hist) - 2} rounds',
         'table grey, red parts, blue parts')
    fig.tight_layout(w_pad=2.5)
    _save(fig, CLUSTER, 'k-means-steps.svg')


def kmeans_k_results() -> list[tuple[int, NDArray[np.int64], NDArray[np.float64], float]]:
    pts = colour_points()
    out = []
    for k in (2, 3, 4):
        best = None
        for seed in range(10):                      # 10 restarts, keep the best
            lab, c, _, sse = kmeans(pts, kmeans_starts(pts, k, seed))
            if best is None or sse < best[3]:
                best = (k, lab, c, sse)
        out.append(best)
    return out


def kmeans_wrong_k_picture() -> None:
    pts = colour_points()
    fig, axes = _panels(3, (15.5, 5.2))
    notes = {2: 'the blue parts are lumped in with the table',
             3: 'one group per real colour',
             4: 'the grey table is cut in two'}
    for ax, (k, lab, c, sse) in zip(axes, kmeans_k_results()):
        _colour_axes(ax, f'k = {k}   (spread {sse / 1000:.0f} thousand)', notes[k])
        for j in range(k):
            ax.scatter(pts[lab == j, 0], pts[lab == j, 1], s=7, color=CLUSTER_COLOURS[j], alpha=0.6)
            ax.plot(c[j, 0], c[j, 1], 'X', ms=14, color=CLUSTER_COLOURS[j], mec=INK, mew=1.2)
    fig.tight_layout(w_pad=2.5)
    _save(fig, CLUSTER, 'k-means-wrong-k.svg')


def grasp_points() -> NDArray[np.float64]:
    """Grasp centres proposed by a grasp model, seen from above, in mm:
    many round a mug, fewer round a box, a few round a small block, and 15 scattered."""
    rng = np.random.default_rng(21)
    mug = rng.normal([80, 90], [9, 9], size=(70, 2))
    box = rng.normal([200, 110], [14, 8], size=(45, 2))
    block = rng.normal([150, 30], [6, 6], size=(20, 2))
    loose = rng.uniform([20, 0], [260, 160], size=(15, 2))
    return np.vstack([mug, box, block, loose])


def mean_shift_path(pts: NDArray[np.float64], start: NDArray[np.float64], h: float,
                    tol: float = 0.1, max_iter: int = 100) -> list[NDArray[np.float64]]:
    """Flat-window mean shift: move to the average of the points within h, until it stops."""
    p = start.copy()
    path = [p.copy()]
    for _ in range(max_iter):
        near = pts[np.linalg.norm(pts - p, axis=1) <= h]
        if len(near) == 0:
            break
        new = near.mean(0)
        path.append(new.copy())
        if np.linalg.norm(new - p) < tol:
            break
        p = new
    return path


def mean_shift(pts: NDArray[np.float64], h: float, min_support: int = 1
               ) -> tuple[NDArray[np.float64], NDArray[np.int64], list[int]]:
    """Start a climb from every point; merge end points closer than h / 2.
    Returns the peaks, a label for every point, and how many points reached each peak."""
    ends = np.array([mean_shift_path(pts, p, h)[-1] for p in pts])
    peaks: list[NDArray[np.float64]] = []
    lab = np.zeros(len(pts), dtype=np.int64)
    for i, e in enumerate(ends):
        for j, q in enumerate(peaks):
            if np.linalg.norm(e - q) < h / 2:
                lab[i] = j
                break
        else:
            peaks.append(e)
            lab[i] = len(peaks) - 1
    counts = [int((lab == j).sum()) for j in range(len(peaks))]
    order = np.argsort(counts)[::-1]
    remap = np.empty(len(order), dtype=np.int64)
    remap[order] = np.arange(len(order))
    return np.array(peaks)[order], remap[lab], [counts[o] for o in order]


MS_START: NDArray[np.float64] = np.array([112.0, 60.0])
MS_H: float = 30.0


def _grasp_axes(ax: Axes, title: str, sub: str) -> None:
    _plot_axes(ax, title, sub)
    ax.add_patch(Rectangle((0, -10), 280, 180, color=TABLE, zorder=0))
    ax.set_xlim(0, 280)
    ax.set_ylim(-10, 170)


def mean_shift_climb_picture() -> None:
    pts = grasp_points()
    path = np.array(mean_shift_path(pts, MS_START, MS_H))
    fig, ax = plt.subplots(figsize=(8.5, 5.8), facecolor='white')
    _grasp_axes(ax, 'One mean shift climb: move to the average of the window',
                f'window radius {MS_H:.0f} mm; the window stops moving after {len(path) - 1} steps')
    ax.scatter(pts[:, 0], pts[:, 1], s=11, color=INK, zorder=2)
    for i, p in enumerate(path[:-1]):
        ax.add_patch(Circle(p, MS_H, fill=False, ec=LINK, lw=1.0, alpha=0.35 + 0.1 * min(i, 6),
                            zorder=3))
    ax.plot(path[:, 0], path[:, 1], '-o', color=WRIST, ms=5, lw=2, zorder=4)
    ax.plot(*path[0], 'o', color=WRIST, ms=10, mec='white', zorder=5)
    ax.text(path[0, 0] + 4, path[0, 1] - 10, 'start', color=WRIST, fontsize=10)
    ax.plot(*path[-1], '*', color=GRIP, ms=18, mec='white', zorder=5)
    ax.annotate('peak: the crowded middle', path[-1], (105, 138), color=GRIP, fontsize=10,
                va='bottom', arrowprops=dict(arrowstyle='->', color=GRIP))
    ax.text(200, 145, 'box', ha='center', fontsize=10, color=MUTED)
    ax.text(150, 55, 'block', ha='center', fontsize=10, color=MUTED)
    ax.text(58, 125, 'mug', ha='center', fontsize=10, color=MUTED)
    fig.tight_layout()
    _save(fig, CLUSTER, 'mean-shift-climb.svg')


def mean_shift_bandwidth_picture() -> None:
    pts = grasp_points()
    fig, axes = _panels(3, (16.0, 4.6))
    for ax, h in zip(axes, (10.0, 30.0, 90.0)):
        peaks, lab, counts = mean_shift(pts, h)
        big = [j for j, n in enumerate(counts) if n >= 10]
        _grasp_axes(ax, f'window {h:.0f} mm: {len(peaks)} peak' + ('s' if len(peaks) > 1 else ''),
                    f'{len(big)} of them reached by 10 or more points')
        for j in range(len(peaks)):
            col = CLUSTER_COLOURS[j] if j in big else MUTED
            m = lab == j
            ax.scatter(pts[m, 0], pts[m, 1], s=9, color=col, zorder=2)
        for j in big:
            ax.plot(*peaks[j], '*', ms=17, color=CLUSTER_COLOURS[j], mec=INK, zorder=4)
    fig.tight_layout(w_pad=2)
    _save(fig, CLUSTER, 'mean-shift-bandwidth.svg')


# ==========================================================================
# PART 3: volumetric maps
# ==========================================================================

N: int = 64                       # the map is 64 x 64 cells of 1 cm, seen from above
CAM_A: NDArray[np.float64] = np.array([32.0, 0.5])
CAM_B: NDArray[np.float64] = np.array([63.5, 40.0])

L_HIT: float = float(np.log(0.7 / 0.3))       # OctoMap's default hit probability 0.7
L_MISS: float = float(np.log(0.4 / 0.6))      # and miss probability 0.4
L_MIN: float = float(np.log(0.1192 / 0.8808))   # clamping limits 0.1192 and 0.971
L_MAX: float = float(np.log(0.971 / 0.029))


def truth_occupied(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.bool_]:
    """The real scene, seen from above: a box, a round tin and a back wall (cm)."""
    box = (x >= 12) & (x < 24) & (y >= 26) & (y < 36)
    tin = (x - 42) ** 2 + (y - 30) ** 2 < 6.0 ** 2
    wall = y >= 58
    return box | tin | wall


def truth_grid() -> NDArray[np.bool_]:
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    return truth_occupied(xx, yy)


def cast(cam: NDArray[np.float64], angle: float, max_range: float = 90.0
         ) -> tuple[float, NDArray[np.float64]]:
    """March from the camera until the ray meets the scene. Returns the range and the direction."""
    d = np.array([np.cos(angle), np.sin(angle)])
    s = np.arange(0.0, max_range, 0.02)
    p = cam + np.outer(s, d)
    inside = (p[:, 0] >= 0) & (p[:, 0] < N) & (p[:, 1] >= 0) & (p[:, 1] < N)
    hit = truth_occupied(p[:, 0], p[:, 1]) & inside
    idx = np.argmax(hit) if hit.any() else None
    return (float(s[idx]) if idx is not None else np.inf), d


def ray_cells(cam: NDArray[np.float64], d: NDArray[np.float64], length: float
              ) -> list[tuple[int, int]]:
    """The grid cells the ray passes through, in order, up to `length` (small steps)."""
    out: list[tuple[int, int]] = []
    for s in np.arange(0.0, length, 0.1):
        p = cam + s * d
        c = (int(p[1]), int(p[0]))
        if not (0 <= c[0] < N and 0 <= c[1] < N):
            break
        if not out or out[-1] != c:
            out.append(c)
    return out


def camera_angles(cam: NDArray[np.float64]) -> NDArray[np.float64]:
    """A depth camera with a 70 degree view and 141 rays, aimed at the middle of the table."""
    aim = np.arctan2(32.0 - cam[1], 32.0 - cam[0])
    return aim + np.deg2rad(np.linspace(-35, 35, 141))


def build_map(cams: list[NDArray[np.float64]], frames: int = 3, noise: float = 0.3
              ) -> NDArray[np.float64]:
    """Log-odds occupancy: for each frame and ray, cells before the hit get a miss,
    the hit cell gets a hit. Values are clamped like OctoMap."""
    rng = np.random.default_rng(5)
    L = np.zeros((N, N))
    for cam in cams:
        for _ in range(frames):
            for a in camera_angles(cam):
                r, d = cast(cam, a)
                if not np.isfinite(r):
                    continue
                r = r + rng.normal(0, noise)
                cells = ray_cells(cam, d, r + 0.05)
                end = (int((cam + r * d)[1]), int((cam + r * d)[0]))
                for c in cells:
                    if c != end:
                        L[c] = max(L_MIN, L[c] + L_MISS)
                if 0 <= end[0] < N and 0 <= end[1] < N:
                    L[end] = min(L_MAX, L[end] + L_HIT)
    return L


def classify(L: NDArray[np.float64]) -> NDArray[np.int64]:
    """0 unknown, 1 free, 2 occupied."""
    out = np.zeros(L.shape, dtype=np.int64)
    out[L < 0] = 1
    out[L > 0] = 2
    return out


MAP_CMAP = ListedColormap(['#bdbdbd', '#ffffff', INK])


def _map_axes(ax: Axes, title: str, sub: str) -> None:
    _plot_axes(ax, title, sub)
    ax.set_xlim(0, N)
    ax.set_ylim(N, 0)


def occupancy_rays_picture() -> None:
    truth = truth_grid()
    one = classify(build_map([CAM_A]))
    two = classify(build_map([CAM_A, CAM_B]))
    fig, axes = _panels(3, (15.5, 5.6))
    _map_axes(axes[0], 'The table from above, and the rays', 'box, round tin and back wall')
    axes[0].imshow(np.where(truth, 1.0, 0.0), cmap=ListedColormap([TABLE, INK]),
                   extent=[0, N, N, 0])
    for a in camera_angles(CAM_A)[::10]:
        r, d = cast(CAM_A, a)
        e = CAM_A + r * d
        axes[0].plot([CAM_A[0], e[0]], [CAM_A[1], e[1]], color=LINK, lw=0.9)
        axes[0].plot(*e, 'o', color=GRIP, ms=3.5)
    axes[0].plot(*CAM_A, 's', color=LINK, ms=11, mec='white')
    axes[0].text(CAM_A[0] + 3, CAM_A[1] + 3.5, 'camera', color=LINK, fontsize=9.5, va='top')

    for ax, m, title in [(axes[1], one, 'After one camera'), (axes[2], two, 'After a second view')]:
        n_u, n_f, n_o = (int((m == k).sum()) for k in range(3))
        _map_axes(ax, title, f'free {n_f}, occupied {n_o}, unknown {n_u} cells')
        ax.imshow(m, cmap=MAP_CMAP, vmin=0, vmax=2, extent=[0, N, N, 0])
        ax.plot(*CAM_A, 's', color=LINK, ms=11, mec='white')
    axes[2].plot(*CAM_B, 's', color=LINK, ms=11, mec='white', clip_on=False)
    axes[1].text(20, 46, 'unknown:\nhidden behind\nthe box', fontsize=9, color=INK, ha='center')
    for ax in axes[1:]:
        for x in range(0, N + 1, 8):
            ax.axvline(x, color=GRID, lw=0.3)
            ax.axhline(x, color=GRID, lw=0.3)
    handles = [Rectangle((0, 0), 1, 1, fc=c, ec=GRID) for c in ['#ffffff', INK, '#bdbdbd']]
    axes[2].legend(handles, ['free', 'occupied', 'unknown'], loc='upper center',
                   bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=9, frameon=False)
    fig.tight_layout(w_pad=2)
    _save(fig, VOLUME, 'rays-free-occupied-unknown.svg')


def cell_history(hits: int, misses: int, clamp: bool) -> list[float]:
    L = 0.0
    out = [L]
    for i in range(hits + misses):
        L += L_HIT if i < hits else L_MISS
        if clamp:
            L = min(L_MAX, max(L_MIN, L))
        out.append(L)
    return out


def first_free(hist: list[float], hits: int) -> int:
    """How many misses after the hits until the cell reads free (log-odds below 0)."""
    for i, v in enumerate(hist[hits + 1:], start=1):
        if v < 0:
            return i
    return -1


def log_odds_picture() -> None:
    hits, misses = 10, 25
    fig, (a1, a2) = _panels(2, (13.0, 4.4))
    for ax, clamp, title in [(a1, False, 'Without a cap'), (a2, True, 'With OctoMap\'s cap')]:
        h = np.array(cell_history(hits, misses, clamp))
        p = 1 / (1 + np.exp(-h))
        _plot_axes(ax, title, '', equal=False, ticks=True)
        ax.axvspan(0, hits, color=LINK_PALE, alpha=0.6)
        ax.text(hits / 2, 1.04, 'cup is there:\n10 hits', ha='center', va='bottom',
                fontsize=9, color=LINK)
        ax.text(hits + misses / 2, 1.04, 'cup lifted away: misses', ha='center', va='bottom',
                fontsize=9, color=MUTED)
        ax.plot(np.arange(len(p)), p, '-o', ms=3.5, color=INK, lw=1.6)
        ax.axhline(0.5, color=GRIP, lw=1, ls='--')
        ax.text(len(p) - 1, 0.52, 'occupied above this line', ha='right', fontsize=8.5,
                color=GRIP)
        n = first_free(list(h), hits)
        ax.plot(hits + n, p[hits + n], 'o', ms=12, mfc='none', mec=GRIP, mew=2)
        ax.annotate(f'reads free after {n} misses', (hits + n, p[hits + n]),
                    (hits + n + (3 if n < 15 else -14), 0.2), fontsize=9.5, color=GRIP,
                    arrowprops=dict(arrowstyle='->', color=GRIP))
        ax.set_ylim(0, 1.2)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xlim(0, hits + misses)
        ax.set_xlabel('depth readings of this cell', fontsize=9.5, color=INK)
        ax.set_ylabel('chance the cell is occupied', fontsize=9.5, color=INK)
        ax.tick_params(labelsize=8.5, colors=MUTED)
    fig.tight_layout(w_pad=3)
    _save(fig, VOLUME, 'log-odds-over-time.svg')


def quadtree(m: NDArray[np.int64], x: int, y: int, size: int,
             out: list[tuple[int, int, int, int]]) -> None:
    """Split a square into four until each square holds only one state."""
    block = m[y:y + size, x:x + size]
    if size == 1 or (block == block.flat[0]).all():
        out.append((x, y, size, int(block.flat[0])))
        return
    h = size // 2
    for dx, dy in ((0, 0), (h, 0), (0, h), (h, h)):
        quadtree(m, x + dx, y + dy, h, out)


def octree_picture() -> None:
    m = classify(build_map([CAM_A, CAM_B]))
    leaves: list[tuple[int, int, int, int]] = []
    quadtree(m, 0, 0, N, leaves)
    fig, (a1, a2) = _panels(2, (12.0, 6.0))
    _map_axes(a1, 'A plain grid', f'{N * N:,} cells, all the same size')
    a1.imshow(m, cmap=MAP_CMAP, vmin=0, vmax=2, extent=[0, N, N, 0])
    for x in range(0, N + 1):
        a1.axvline(x, color=GRID, lw=0.25)
        a1.axhline(x, color=GRID, lw=0.25)
    _map_axes(a2, 'The same map as a tree of squares',
              f'{len(leaves):,} squares: big ones in open space, small at the edges')
    cols = ['#bdbdbd', '#ffffff', INK]
    for x, y, s, v in leaves:
        a2.add_patch(Rectangle((x, y), s, s, fc=cols[v], ec=LINK, lw=0.5))
    fig.tight_layout(w_pad=3)
    _save(fig, VOLUME, 'octree-cells.svg')


TRUNC: float = 3.0        # truncation distance, cm
READINGS: list[float] = [50.4, 49.7, 50.2]   # three depth readings of a surface at 50.0 cm
VOXELS: NDArray[np.float64] = np.arange(45.5, 55.0, 1.0)   # voxel centres along the ray


def tsdf_1d() -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    """Each reading gives every voxel a signed distance (reading - voxel), cut at +-TRUNC.
    Voxels farther behind the surface than TRUNC are not updated. Fused = the average."""
    per = []
    for z in READINGS:
        sd = z - VOXELS
        v = np.clip(sd, -TRUNC, TRUNC)
        v[sd < -TRUNC] = np.nan
        per.append(v)
    per_a = np.array(per)
    seen = ~np.isnan(per_a).all(0)
    fused = np.full(len(VOXELS), np.nan)
    fused[seen] = np.nanmean(per_a[:, seen], axis=0)
    i = int(np.where((fused[:-1] > 0) & (fused[1:] <= 0))[0][0])
    zero = VOXELS[i] + fused[i] / (fused[i] - fused[i + 1]) * 1.0
    return per_a, fused, float(zero)


def esdf(occupied: NDArray[np.bool_]) -> NDArray[np.float64]:
    """Distance from every cell centre to the nearest occupied cell centre (brute force);
    negative inside obstacles (distance to the nearest free cell)."""
    yy, xx = np.mgrid[0:N, 0:N]
    cells = np.stack([xx.ravel(), yy.ravel()], 1).astype(float)
    occ = cells[occupied.ravel()]
    free = cells[~occupied.ravel()]
    out = np.empty(N * N)
    for i, c in enumerate(cells):
        if occupied.ravel()[i]:
            out[i] = -np.sqrt(((free - c) ** 2).sum(1).min())
        else:
            out[i] = np.sqrt(((occ - c) ** 2).sum(1).min())
    return out.reshape(N, N)


# two balls that stand for parts of the gripper: (x, y, radius) in cm
ARM_SPHERES: list[tuple[float, float, float]] = [(50.0, 13.0, 4.0), (21.0, 21.5, 5.0)]


def tsdf_esdf_picture() -> None:
    per, fused, zero = tsdf_1d()
    occ = classify(build_map([CAM_A, CAM_B])) == 2
    dist = esdf(occ)
    fig, (a1, a2) = _panels(2, (13.5, 5.4))
    _plot_axes(a1, 'TSDF along one camera ray', '', equal=False, ticks=True)
    for row, z, col in zip(per, READINGS, [LINK, SLIDE, PURPLE]):
        a1.plot(VOXELS, row, 'o--', color=col, ms=5, lw=1, alpha=0.8, label=f'reading {z} cm')
    a1.plot(VOXELS, fused, 's-', color=INK, ms=7, lw=2, label='average of the three')
    a1.axhline(0, color=MUTED, lw=0.8)
    a1.axvline(zero, color=GRIP, lw=1.5)
    a1.text(zero + 0.25, 1.6, f'surface where the\naverage crosses 0:\n{zero:.2f} cm',
            color=GRIP, fontsize=9.5)
    a1.text(45.6, 2.4, 'in front: free space', fontsize=9, color=MUTED)
    a1.set_xlabel('distance from the camera along the ray (cm)', fontsize=9.5, color=INK)
    a1.set_ylabel('stored value (cm), cut at ±3', fontsize=9.5, color=INK)
    a1.set_ylim(-3.6, 3.6)
    a1.legend(fontsize=8.5, loc='lower left', frameon=False)
    a1.tick_params(labelsize=8.5, colors=MUTED)

    _plot_axes(a2, 'ESDF: distance to the nearest obstacle',
               'each gripper ball is safe if the distance at its centre is bigger than its radius')
    im = a2.imshow(np.clip(dist, 0, 20), cmap='viridis', extent=[0, N, N, 0])
    cs = a2.contour(np.arange(N) + 0.5, np.arange(N) + 0.5, dist, levels=[5, 10, 15],
                    colors='white', linewidths=0.8)
    a2.clabel(cs, fmt='%d cm', fontsize=8)
    a2.contour(np.arange(N) + 0.5, np.arange(N) + 0.5, occ.astype(float), levels=[0.5],
               colors=GRIP, linewidths=1.2)
    for x, y, r in ARM_SPHERES:
        d = esdf_at(dist, x, y)
        col = 'white' if d > r else GRIP
        a2.add_patch(Circle((x, y), r, fill=False, ec=col, lw=2.2))
        a2.plot(x, y, '+', color=col, ms=8, mew=1.5)
        a2.text(x, y - r - 1.2, f'{d:.1f} cm away, radius {r:.0f}: '
                + ('safe' if d > r else 'too close'), ha='center', va='bottom', fontsize=8.5,
                color=INK if d > r else GRIP, weight='bold',
                bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1.5))
    a2.set_xlim(0, N)
    a2.set_ylim(N, 0)
    cb = fig.colorbar(im, ax=a2, fraction=0.045, pad=0.03)
    cb.set_label('distance (cm)', fontsize=9.5)
    cb.ax.tick_params(labelsize=8.5)
    fig.tight_layout(w_pad=3)
    _save(fig, VOLUME, 'tsdf-and-esdf.svg')


def esdf_at(dist: NDArray[np.float64], x: float, y: float) -> float:
    """Bilinear read of the distance field at a point (cell centres at +0.5)."""
    gx, gy = x - 0.5, y - 0.5
    x0, y0 = int(np.floor(gx)), int(np.floor(gy))
    fx, fy = gx - x0, gy - y0
    d = dist
    return float((1 - fx) * (1 - fy) * d[y0, x0] + fx * (1 - fy) * d[y0, x0 + 1]
                 + (1 - fx) * fy * d[y0 + 1, x0] + fx * fy * d[y0 + 1, x0 + 1])


# ==========================================================================
# numbers quoted in the documents
# ==========================================================================

def print_numbers() -> None:
    print('--- Hough lines ---')
    pts = three_points()
    acc, rhos = hough_lines(pts, 80)
    r, c, v = hough_peaks(acc, 1)[0]
    print('three points peak: theta', np.rad2deg(THETAS[c]), 'rho', rhos[r], 'votes', v)
    for x, y in pts:
        print('  point', (x, y), 'rho at that theta', round(x * np.cos(THETAS[c]) + y * np.sin(THETAS[c]), 2))
    te = table_edge_points()
    acc, rhos = hough_lines(te, 150)
    print('table edge pts', len(te), 'acc shape', acc.shape, 'cells', acc.size)
    for r, c, v in hough_peaks(acc, 4):
        print('  peak theta', np.rad2deg(THETAS[c]), 'rho', rhos[r], 'votes', v)
    print('  line pixels on table edge', 120 - 12 - 8, 'box side', 33 - 6)
    print('--- Hough circles ---')
    cp = cup_rim_points()
    acc = hough_circle_votes(cp, 20.0, CUP_SHAPE)
    cy, cx = np.unravel_index(np.argmax(acc), acc.shape)
    print('cup pts', len(cp), 'rim pts', len(cp) - 25, 'peak', (cx, cy), 'votes', acc.max(),
          'second best away from peak',
          int(np.max(np.where((np.abs(np.arange(80)[None] - cx) > 2) | (np.abs(np.arange(76)[:, None] - cy) > 2), acc, 0))))
    print('radius scan', circle_radius_scan())
    print('--- k-means ---')
    cpts = colour_points()
    starts = kmeans_starts(cpts, 3, KMEANS_SEED)
    lab, cen, hist, sse = kmeans(cpts, starts)
    print('starts', starts.round(1).tolist())
    print('after round 1', hist[1].round(1).tolist())
    print('final', cen.round(1).tolist(), 'rounds', len(hist) - 2, 'sizes',
          [int((lab == k).sum()) for k in range(3)], 'sse', round(sse))
    for k, lab, c, sse in kmeans_k_results():
        print('k', k, 'sizes', [int((lab == j).sum()) for j in range(k)], 'centres',
              c.round(0).tolist(), 'sse', round(sse))
    # does a bad start give a bad answer?
    for seed in range(10):
        _, c, h, s = kmeans(cpts, kmeans_starts(cpts, 3, seed))
        print('  k=3 seed', seed, 'sse', round(s), 'rounds', len(h) - 2)
    print('--- mean shift ---')
    g = grasp_points()
    path = mean_shift_path(g, MS_START, MS_H)
    print('grasp pts', len(g), 'path', [p.round(1).tolist() for p in path])
    for h in (10.0, 20.0, 30.0, 45.0, 60.0, 90.0):
        peaks, lab, counts = mean_shift(g, h)
        print('h', h, 'peaks', len(peaks), 'counts', counts[:8],
              'big (>=10)', sum(1 for n in counts if n >= 10),
              'top peaks', peaks[:3].round(1).tolist())
    print('--- volumetric maps ---')
    print('L_HIT', round(L_HIT, 3), 'L_MISS', round(L_MISS, 3), 'L_MIN', round(L_MIN, 3),
          'L_MAX', round(L_MAX, 3))
    for clamp in (False, True):
        h = cell_history(10, 25, clamp)
        print('clamp', clamp, 'after 10 hits', round(h[10], 3), 'p',
              round(1 / (1 + np.exp(-h[10])), 4), 'misses to free', first_free(h, 10))
    h1 = cell_history(1, 0, True)
    print('one hit p', round(1 / (1 + np.exp(-h1[1])), 3), 'two hits', round(1 / (1 + np.exp(-2 * L_HIT)), 3),
          'hit then miss', round(1 / (1 + np.exp(-(L_HIT + L_MISS))), 3))
    for cams, name in [([CAM_A], 'one'), ([CAM_A, CAM_B], 'two')]:
        m = classify(build_map(cams))
        print(name, 'camera: unknown', int((m == 0).sum()), 'free', int((m == 1).sum()),
              'occupied', int((m == 2).sum()))
    m = classify(build_map([CAM_A, CAM_B]))
    leaves: list[tuple[int, int, int, int]] = []
    quadtree(m, 0, 0, N, leaves)
    sizes = {}
    for *_, s, v in [(0, 0, l[2], l[3]) for l in leaves]:
        sizes[s] = sizes.get(s, 0) + 1
    print('quadtree leaves', len(leaves), 'by size', dict(sorted(sizes.items())))
    print('dense cells', N * N, 'dense 3D 1 m cube at 1 cm', 100 ** 3)
    per, fused, zero = tsdf_1d()
    print('tsdf voxels', VOXELS.tolist())
    for z, row in zip(READINGS, per):
        print('  reading', z, [None if np.isnan(v) else round(v, 2) for v in row])
    print('  fused', [None if np.isnan(v) else round(v, 3) for v in fused], 'zero', round(zero, 3),
          'mean of readings', round(float(np.mean(READINGS)), 3))
    occ = m == 2
    dist = esdf(occ)
    for x, y, r in ARM_SPHERES:
        d = esdf_at(dist, x, y)
        print('  sphere', (x, y, r), 'esdf', round(d, 2), 'clearance', round(d - r, 2),
              'safe' if d > r else 'COLLIDES')
    print('  esdf max', round(dist.max(), 2), 'min', round(dist.min(), 2))


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    hough_one_point_picture()
    hough_accumulator_picture()
    hough_circle_picture()
    hough_radius_picture()
    kmeans_steps_picture()
    kmeans_wrong_k_picture()
    mean_shift_climb_picture()
    mean_shift_bandwidth_picture()
    occupancy_rays_picture()
    log_odds_picture()
    octree_picture()
    tsdf_esdf_picture()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
