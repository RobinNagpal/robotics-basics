"""Generate the diagrams used in docs/05_programming-techniques/03_searching-and-matching/.

Each document's pictures go to a folder named after it, under
docs/images/searching-and-matching/.

Run with:  pixi run python ../docs/diagrams/searching_and_matching.py
or, from the repo root:  python3 docs/diagrams/searching_and_matching.py --png <dir>
Add --numbers to print the worked-example numbers that the documents quote.

Every result drawn here is computed, not drawn by hand. The script builds a real
k-d tree and searches it, runs real iterative closest point (ICP) iterations,
and solves each assignment by trying every possible pairing. It needs only NumPy
and Matplotlib.

All scenes are a table seen from above, measured in millimetres.
"""

import itertools
import math
import pathlib
import sys
from typing import Any

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'searching-and-matching')
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

# The table top seen from above: 600 mm wide and 400 mm deep.
TW: float = 600.0
TD: float = 400.0

Node = dict[str, Any]
Array = NDArray[np.float64]


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
           ha: str = 'center', va: str = 'center', weight: str = 'normal',
           box: bool = False) -> None:
    kw: dict[str, Any] = {}
    if box:
        kw['bbox'] = {'boxstyle': 'round,pad=0.2', 'facecolor': 'white',
                      'edgecolor': 'none', 'alpha': 0.9}
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            zorder=12, **kw)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='top', color=MUTED)


def _atitle(ax: Axes, text: str, y: float = 1.1, size: float = 12) -> None:
    """A title placed in the panel's own 0-to-1 coordinates, so panels of any scale line up."""
    ax.text(0.5, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold',
            transform=ax.transAxes)


def _acaption(ax: Axes, text: str, y: float = -0.04, size: float = 10) -> None:
    ax.text(0.5, y, text, fontsize=size, ha='center', va='top', color=MUTED,
            transform=ax.transAxes)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>') -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': style, 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=8)


def _table(ax: Axes, pad: float = 30.0) -> None:
    """The table top seen from above, with a little white round it."""
    _axes(ax, (-pad, TW + pad), (-pad, TD + pad))
    ax.add_patch(Rectangle((0, 0), TW, TD, facecolor=TABLE, edgecolor=INK, lw=1.0,
                           zorder=1))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# the techniques themselves, written out in NumPy
# --------------------------------------------------------------------------

# Eleven objects on the table, and the gripper tip that asks "which is nearest?".
OBJECTS: dict[str, tuple[float, float]] = {
    'A': (60, 300), 'B': (120, 80), 'C': (180, 220), 'D': (250, 350), 'E': (300, 150),
    'F': (360, 60), 'G': (400, 270), 'H': (460, 340), 'I': (500, 130), 'J': (540, 240),
    'K': (220, 40)}
QUERY: tuple[float, float] = (430, 300)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def kd_build(items: list[tuple[str, tuple[float, float]]], depth: int = 0) -> Node | None:
    """Build a k-d tree: split at the middle point, across x then y then x ..."""
    if not items:
        return None
    axis: int = depth % 2
    items = sorted(items, key=lambda it: it[1][axis])
    m: int = len(items) // 2
    return {'name': items[m][0], 'p': items[m][1], 'axis': axis, 'depth': depth,
            'left': kd_build(items[:m], depth + 1),
            'right': kd_build(items[m + 1:], depth + 1)}


def kd_nearest(node: Node | None, q: tuple[float, float], best: tuple[str, float] | None,
               log: list[tuple[str, str, float]]) -> tuple[str, float] | None:
    """Search the tree. log gets ('check', name, distance) and ('skip', name, gap)."""
    if node is None:
        return best
    d: float = _dist(node['p'], q)
    log.append(('check', node['name'], d))
    if best is None or d < best[1]:
        best = (node['name'], d)
    diff: float = q[node['axis']] - node['p'][node['axis']]
    near, far = (node['left'], node['right']) if diff < 0 else (node['right'], node['left'])
    best = kd_nearest(near, q, best, log)
    assert best is not None
    if far is not None:
        if abs(diff) < best[1]:
            best = kd_nearest(far, q, best, log)
        else:
            log.append(('skip', far['name'], abs(diff)))
    return best


def _subtree_names(node: Node | None) -> list[str]:
    if node is None:
        return []
    return [node['name']] + _subtree_names(node['left']) + _subtree_names(node['right'])


def _find(node: Node | None, name: str) -> Node | None:
    if node is None:
        return None
    if node['name'] == name:
        return node
    return _find(node['left'], name) or _find(node['right'], name)


def kd_count_checks(points: Array, queries: Array) -> int:
    """How many distance checks a k-d tree needs to answer every query."""
    tree = kd_build([(str(i), (float(p[0]), float(p[1]))) for i, p in enumerate(points)])
    total: int = 0
    for q in queries:
        log: list[tuple[str, str, float]] = []
        kd_nearest(tree, (float(q[0]), float(q[1])), None, log)
        total += sum(1 for e in log if e[0] == 'check')
    return total


def outline(corners: list[tuple[float, float]], step: float) -> Array:
    """Points every `step` mm round a closed outline."""
    pts: list[Array] = []
    for a, b in zip(corners, corners[1:] + corners[:1]):
        pa, pb = np.array(a, float), np.array(b, float)
        n: int = max(1, int(round(float(np.linalg.norm(pb - pa)) / step)))
        for i in range(n):
            pts.append(pa + (pb - pa) * i / n)
    return np.array(pts)


def rot(deg: float) -> Array:
    t: float = math.radians(deg)
    return np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])


def best_fit(a: Array, b: Array) -> tuple[Array, Array]:
    """The rotation R and shift t that move points a closest to their partners b."""
    ca, cb = a.mean(0), b.mean(0)
    h = (a - ca).T @ (b - cb)
    u, _s, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:             # a mirror image is not a real movement
        vt[1] *= -1
        r = vt.T @ u.T
    return r, cb - r @ ca


def closest(src: Array, dst: Array) -> tuple[NDArray[np.int64], Array]:
    """Brute-force nearest neighbour: for each src point, the index of the nearest dst point."""
    d = np.linalg.norm(src[:, None, :] - dst[None, :, :], axis=2)
    j = d.argmin(1)
    return j, d[np.arange(len(src)), j]


def icp(src: Array, dst: Array, max_iters: int = 80,
        stop: float = 0.001) -> list[tuple[Array, NDArray[np.int64], float]]:
    """Point-to-point ICP. Returns, for each round, the moved model, its pairs and mean gap."""
    cur = src.copy()
    hist: list[tuple[Array, NDArray[np.int64], float]] = []
    for _ in range(max_iters):
        j, gaps = closest(cur, dst)
        hist.append((cur.copy(), j, float(gaps.mean())))
        if len(hist) > 1 and hist[-2][2] - hist[-1][2] < stop:
            break
        r, t = best_fit(cur, dst[j])
        cur = cur @ r.T + t
    return hist


def angle_of(r: Array) -> float:
    return math.degrees(math.atan2(r[1, 0], r[0, 0]))


# An L-shaped bracket seen from above, 120 by 80 mm. The model has a point every
# 10 mm round its outline. The scan has a point every 6 mm and 0.8 mm of noise.
BRACKET: list[tuple[float, float]] = [(0, 0), (120, 0), (120, 30), (30, 30), (30, 80), (0, 80)]
MODEL: Array = outline(BRACKET, 10.0)
MODEL_C: Array = MODEL.mean(0)
PLACE: Array = np.array([230.0, 150.0])          # where the model sits on the table


def scan_of(deg: float, shift: tuple[float, float], seed: int = 1) -> Array:
    fine = outline(BRACKET, 6.0)
    rng = np.random.default_rng(seed)
    return ((fine - MODEL_C) @ rot(deg).T + MODEL_C + np.array(shift)
            + rng.normal(0.0, 0.8, fine.shape))


GOOD_TURN, GOOD_SHIFT = 20.0, (30.0, 20.0)
BAD_TURN = 120.0


# Three mugs on a moving belt. Where they were one frame ago, and what the
# detector reports now.
TRACKS: Array = np.array([(100, 200), (180, 200), (400, 150)], float)
DETS: Array = np.array([(150, 200), (235, 200), (450, 150)], float)
# The next frame: mug 3 is hidden by the arm, and a new mug has been put down.
DETS_2: Array = np.array([(150, 200), (235, 200), (560, 300)], float)
GATE: float = 80.0


def cost_table(a: Array, b: Array) -> Array:
    return np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)


def best_assignment(cost: Array, gate: float = math.inf) -> tuple[list[tuple[int, int]], float]:
    """Try every pairing (fine for a handful of objects). A pair over the gate is not allowed;
    leaving a row unmatched costs `gate`."""
    n, m = cost.shape
    best: tuple[list[tuple[int, int]], float] = ([], math.inf)
    for perm in itertools.permutations(range(m + n), n):
        total, pairs, ok = 0.0, [], True
        for i, j in enumerate(perm):
            if j < m:
                if cost[i, j] > gate:
                    ok = False
                    break
                total += cost[i, j]
                pairs.append((i, j))
            else:
                total += gate
        if ok and total < best[1] - 1e-9:
            best = (pairs, total)
    return best


def greedy_assignment(cost: Array) -> tuple[list[tuple[int, int]], float]:
    """Take the cheapest pair left, again and again."""
    c = cost.copy()
    pairs: list[tuple[int, int]] = []
    while np.isfinite(c).any():
        i, j = np.unravel_index(int(np.argmin(c)), c.shape)
        pairs.append((int(i), int(j)))
        c[i, :] = np.inf
        c[:, j] = np.inf
    return pairs, float(sum(cost[i, j] for i, j in pairs))


# --------------------------------------------------------------------------
# drawing pieces shared by several pictures
# --------------------------------------------------------------------------

# Where each object's name goes, relative to the object. G sits next to the
# gripper, so its name goes below and to the left.
NAME_OFFSET: dict[str, tuple[float, float]] = {'G': (-18.0, -20.0)}


def _objects(ax: Axes, highlight: dict[str, str] | None = None, names: bool = True,
             faded: set[str] | None = None) -> None:
    highlight = highlight or {}
    faded = faded or set()
    for name, p in OBJECTS.items():
        color = highlight.get(name, LINK)
        alpha = 0.3 if name in faded else 1.0
        ax.plot([p[0]], [p[1]], 'o', ms=10, color=color, mec=INK, mew=0.8, alpha=alpha,
                zorder=6)
        if names:
            dx, dy = NAME_OFFSET.get(name, (14.0, 14.0))
            _label(ax, p[0] + dx, p[1] + dy, name, size=10, weight='bold',
                   color=INK if name not in faded else MUTED)


def _gripper_name(ax: Axes) -> None:
    """The word 'gripper' above the table edge, with a pointer to the cross."""
    ax.annotate('gripper', xy=(QUERY[0] + 6, QUERY[1] + 8), xytext=(QUERY[0] + 95, TD - 22),
                fontsize=10, color=GRIP, ha='left', va='center', zorder=12,
                arrowprops={'arrowstyle': '-', 'color': GRIP, 'lw': 1.0},
                bbox={'boxstyle': 'round,pad=0.2', 'facecolor': 'white', 'edgecolor': 'none'})


def _gripper(ax: Axes, q: tuple[float, float] = QUERY, size: float = 13) -> None:
    ax.plot([q[0]], [q[1]], marker='X', ms=size, color=GRIP, mec=INK, mew=0.8, zorder=9)


def _mug_top(ax: Axes, p: Array | tuple[float, float], color: str, hollow: bool = False,
             r: float = 13.0, label: str = '') -> None:
    """Where a mug's centre was one frame ago: a dashed ring (or a filled one if not hollow)."""
    if hollow:
        ax.add_patch(Circle((p[0], p[1]), r, facecolor='white', edgecolor=color, lw=2.0,
                            ls='--', zorder=5))
    else:
        ax.add_patch(Circle((p[0], p[1]), r, facecolor=color, edgecolor=INK, lw=1.0,
                            zorder=5))
        ax.add_patch(Circle((p[0], p[1]), r * 0.6, facecolor='white', edgecolor=INK,
                            lw=0.8, zorder=6))
    if label:
        _label(ax, p[0], p[1] + r + 16, label, size=10, weight='bold', color=color)


def _bracket(ax: Axes, pts: Array, color: str, size: float = 4.5, alpha: float = 1.0,
             z: int = 6) -> None:
    ax.plot(pts[:, 0], pts[:, 1], 'o', ms=size, color=color, alpha=alpha, mew=0, zorder=z)


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'


def three_questions() -> None:
    """One table, the three questions this chapter answers, each answered for real."""
    fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.9), facecolor='white')

    # 1. nearest neighbour
    ax = axes[0]
    _table(ax)
    tree = kd_build(list(OBJECTS.items()))
    best = kd_nearest(tree, QUERY, None, [])
    assert best is not None
    _objects(ax, highlight={best[0]: JOINT})
    bp = OBJECTS[best[0]]
    ax.plot([QUERY[0], bp[0]], [QUERY[1], bp[1]], color=GRIP, lw=2.2, zorder=7)
    _gripper(ax)
    _gripper_name(ax)
    _atitle(ax, '1. Which one is nearest?')
    _acaption(ax, f'Nearest-neighbour search: object {best[0]}\n'
                  f'is {best[1]:.1f} mm from the gripper.')

    # 2. ICP, drawn closer in: the bracket is small on the table
    ax = axes[1]
    lim = (-50.0, 230.0, -40.0, 156.0)
    _axes(ax, (lim[0], lim[1]), (lim[2], lim[3]))
    ax.add_patch(Rectangle((lim[0], lim[2]), lim[1] - lim[0], lim[3] - lim[2],
                           facecolor=TABLE, edgecolor=INK, lw=1.0, zorder=1))
    scan = scan_of(GOOD_TURN, GOOD_SHIFT)
    hist = icp(MODEL, scan)
    _bracket(ax, scan, MUTED, size=3.5)
    _bracket(ax, MODEL, LINK_PALE, size=5.0, z=5)
    _bracket(ax, hist[-1][0], LINK, size=5.0, z=7)
    _label(ax, -42, 146, 'grey: the scan', color=MUTED, ha='left', size=10)
    _label(ax, -42, 134, 'pale blue: the model at its first guess', color=LINK, ha='left',
           size=10)
    _label(ax, -42, 122, 'blue: the model after ICP', color=LINK, ha='left', size=10,
           weight='bold')
    _atitle(ax, '2. Where exactly is the part?')
    _acaption(ax, 'Iterative closest point: the model outline\n'
                  f'is moved onto the scan in {len(hist) - 1} rounds.')

    # 3. assignment, drawn closer in
    ax = axes[2]
    pairs, total = best_assignment(cost_table(TRACKS, DETS))
    _belt(ax, 50, 500, 60, 374, edge=True)
    _pairs(ax, TRACKS, DETS, pairs, costs=None)
    _label(ax, 275, 350, 'dashed ring: a mug one frame ago\nsquare: a detection now',
           color=MUTED, size=10)
    _atitle(ax, '3. Which one is which?')
    _acaption(ax, 'Assignment: each detection now is paired\n'
                  f'with one mug seen before (total {total:.1f} mm).')
    fig.subplots_adjust(wspace=0.08)
    _save(fig, OVERVIEW, 'three-questions.svg')


def work_grows() -> None:
    """How the obvious method's work grows, next to the clever method's."""
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white')
    rng = np.random.default_rng(7)

    ax = axes[0]
    ns = [10, 30, 100, 300, 1000, 3000]
    brute = [n * n for n in ns]
    kd = []
    for n in ns:
        pts = rng.uniform(0, 600, (n, 2))
        qs = pts + rng.normal(0, 2.0, pts.shape)        # a second scan of the same points
        kd.append(kd_count_checks(pts, qs))
    ax.loglog(ns, brute, 'o-', color=GRIP, lw=2, label='check every pair (brute force)')
    ax.loglog(ns, kd, 's-', color=LINK, lw=2, label='k-d tree, counted in this script')
    for n, b, k in zip(ns, brute, kd):
        if n in (100, 3000):
            _label(ax, n, b * 2.6, f'{b:,}', color=GRIP, size=9)
            _label(ax, n, k / 2.6, f'{k:,}', color=LINK, size=9)
    ax.set_xlabel('points in each scan')
    ax.set_ylabel('distance checks to match every point')
    ax.set_title('Matching one scan to another', fontsize=12, weight='bold')
    ax.legend(frameon=False, loc='upper left', fontsize=9.5)
    ax.grid(True, which='major', color=GRID, lw=0.6)
    ax.set_ylim(10, 5e8)

    ax = axes[1]
    ns2 = list(range(2, 13))
    perms = [math.factorial(n) for n in ns2]
    cubes = [n ** 3 for n in ns2]
    ax.semilogy(ns2, perms, 'o-', color=GRIP, lw=2, label='try every pairing (n!)')
    ax.semilogy(ns2, cubes, 's-', color=LINK, lw=2, label='Hungarian algorithm (about n³ steps)')
    _label(ax, 12, perms[-1] * 3.5, f'{perms[-1]:,}', color=GRIP, size=9, ha='right')
    _label(ax, 12, cubes[-1] / 4.0, f'{cubes[-1]:,}', color=LINK, size=9, ha='right')
    ax.set_xlabel('objects to pair up')
    ax.set_ylabel('pairings or steps')
    ax.set_title('Deciding which object is which', fontsize=12, weight='bold')
    ax.legend(frameon=False, loc='upper left', fontsize=9.5)
    ax.grid(True, which='major', color=GRID, lw=0.6)
    ax.set_ylim(1, 5e10)
    for a in axes:
        for s in ('top', 'right'):
            a.spines[s].set_visible(False)
    fig.subplots_adjust(wspace=0.3)
    _save(fig, OVERVIEW, 'work-grows.svg')


# --------------------------------------------------------------------------
# 02_nearest-neighbour-search
# --------------------------------------------------------------------------

NN: str = 'nearest-neighbour-search'


def brute_force() -> None:
    """The gripper measures its distance to every object and keeps the smallest."""
    fig, ax = plt.subplots(figsize=(8.6, 6.2), facecolor='white')
    _table(ax)
    dists = {n: _dist(p, QUERY) for n, p in OBJECTS.items()}
    best = min(dists, key=lambda n: dists[n])
    for n, p in OBJECTS.items():
        is_best = n == best
        ax.plot([QUERY[0], p[0]], [QUERY[1], p[1]], color=GRIP if is_best else GRID,
                lw=2.4 if is_best else 1.2, zorder=3 if not is_best else 4)
        f = {'K': 0.8, 'G': 0.35}.get(n, 0.62)
        mx, my = f * p[0] + (1 - f) * QUERY[0], f * p[1] + (1 - f) * QUERY[1]
        if n == 'G':
            mx, my = mx - 22, my + 10
        _label(ax, mx, my, f'{dists[n]:.0f}', size=8.5, color=GRIP if is_best else MUTED,
               box=True, weight='bold' if is_best else 'normal')
    _objects(ax, highlight={best: JOINT})
    _gripper(ax)
    _gripper_name(ax)
    _title(ax, TW / 2, TD + 60, 'Brute force: measure all 11, keep the smallest')
    _caption(ax, TW / 2, -40, f'Object {best} is nearest, {dists[best]:.1f} mm away. '
                              'Numbers are distances in mm.')
    _save(fig, NN, 'brute-force.svg')


def _draw_splits(ax: Axes, node: Node | None, box: tuple[float, float, float, float],
                 greyed: set[str], lw: float = 1.8) -> None:
    """Draw each split line inside the box its node owns."""
    if node is None:
        return
    x0, y0, x1, y1 = box
    px, py = node['p']
    color = [GRIP, SLIDE, WRIST, MUTED][min(node['depth'], 3)]
    if node['axis'] == 0:
        ax.plot([px, px], [y0, y1], color=color, lw=lw, zorder=4)
        lbox, rbox = (x0, y0, px, y1), (px, y0, x1, y1)
    else:
        ax.plot([x0, x1], [py, py], color=color, lw=lw, zorder=4)
        lbox, rbox = (x0, y0, x1, py), (x0, py, x1, y1)
    for child, cbox in ((node['left'], lbox), (node['right'], rbox)):
        if child is not None and child['name'] in greyed:
            ax.add_patch(Rectangle((cbox[0], cbox[1]), cbox[2] - cbox[0], cbox[3] - cbox[1],
                                   facecolor='#bdbdbd', edgecolor='none', alpha=0.55,
                                   zorder=2))
        _draw_splits(ax, child, cbox, greyed, lw)


def _tree_layout(node: Node | None, x: float, y: float, dx: float,
                 out: dict[str, tuple[float, float]]) -> None:
    if node is None:
        return
    out[node['name']] = (x, y)
    _tree_layout(node['left'], x - dx, y - 1.0, dx / 2, out)
    _tree_layout(node['right'], x + dx, y - 1.0, dx / 2, out)


def kd_tree_boxes() -> None:
    """The k-d tree cuts the table into boxes; the same cuts drawn as a tree."""
    tree = kd_build(list(OBJECTS.items()))
    fig, axes = plt.subplots(1, 2, figsize=(15.0, 5.6), facecolor='white',
                             gridspec_kw={'width_ratios': [1.15, 1.0]})
    ax = axes[0]
    _table(ax)
    _draw_splits(ax, tree, (0, 0, TW, TD), set())
    _objects(ax)
    _title(ax, TW / 2, TD + 60, 'The table cut into boxes')
    _caption(ax, TW / 2, -40, 'Red: first cut (x = 300, through E). Green: second cuts.\n'
                              'Orange and grey: third and fourth cuts.')

    ax = axes[1]
    pos: dict[str, tuple[float, float]] = {}
    _tree_layout(tree, 0.0, 0.0, 2.0, pos)
    _axes(ax, (-4.2, 4.2), (-3.9, 0.9))

    def edges(node: Node | None) -> None:
        if node is None:
            return
        for c in (node['left'], node['right']):
            if c is not None:
                a, b = pos[node['name']], pos[c['name']]
                ax.plot([a[0], b[0]], [a[1], b[1]], color=GRID, lw=1.6, zorder=2)
                edges(c)
    edges(tree)

    def nodes(node: Node | None) -> None:
        if node is None:
            return
        x, y = pos[node['name']]
        color = [GRIP, SLIDE, WRIST, MUTED][min(node['depth'], 3)]
        ax.add_patch(Circle((x, y), 0.28, facecolor='white', edgecolor=color, lw=2.2,
                            zorder=5))
        _label(ax, x, y, node['name'], weight='bold', size=11)
        axis = 'x' if node['axis'] == 0 else 'y'
        if node['left'] is not None or node['right'] is not None:
            _label(ax, x, y - 0.45, f'{axis} = {node["p"][node["axis"]]:.0f}', size=8.5,
                   color=color, box=True)
        nodes(node['left'])
        nodes(node['right'])
    nodes(tree)
    _label(ax, -2.9, 0.35, 'smaller:\ngo left', size=9, color=MUTED)
    _label(ax, 2.9, 0.35, 'larger:\ngo right', size=9, color=MUTED)
    _title(ax, 0, 1.05, 'The same cuts as a tree')
    _caption(ax, 0, -3.55, 'Each point splits its box in two. Under each point: the cut it makes.')
    fig.subplots_adjust(wspace=0.05)
    _save(fig, NN, 'kd-tree-boxes.svg')


def kd_tree_search() -> None:
    """The search for the gripper's nearest object checks 4 points and skips two boxes."""
    tree = kd_build(list(OBJECTS.items()))
    assert tree is not None
    log: list[tuple[str, str, float]] = []
    best = kd_nearest(tree, QUERY, None, log)
    assert best is not None
    checked = [e[1] for e in log if e[0] == 'check']
    skipped: set[str] = set()
    for e in log:
        if e[0] == 'skip':
            skipped |= set(_subtree_names(_find(tree, e[1])))

    fig, ax = plt.subplots(figsize=(9.0, 6.6), facecolor='white')
    _table(ax)
    _draw_splits(ax, tree, (0, 0, TW, TD), {e[1] for e in log if e[0] == 'skip'}, lw=1.4)
    ax.add_patch(Circle(QUERY, best[1], facecolor='none', edgecolor=GRIP, lw=1.6, ls='--',
                        zorder=5))
    _objects(ax, highlight={n: JOINT for n in checked}, faded=skipped)
    for k, n in enumerate(checked):
        p = OBJECTS[n]
        ax.text(p[0] - 16, p[1] - 20, f'{k + 1}', fontsize=9, ha='center', va='center',
                color='white', weight='bold', zorder=13,
                bbox={'boxstyle': 'circle,pad=0.2', 'facecolor': INK, 'edgecolor': INK})
    bp = OBJECTS[best[0]]
    ax.plot([QUERY[0], bp[0]], [QUERY[1], bp[1]], color=GRIP, lw=2.4, zorder=7)
    _gripper(ax)
    _label(ax, 150, 110, 'skipped:\nthe whole left half\nis at least 130 mm away', size=9.5,
           color=INK, box=True)
    _label(ax, 470, 30, 'skipped: I and F\nare at least 60 mm away', size=9.5, color=INK,
           box=True, va='bottom')
    _title(ax, TW / 2, TD + 60, f'The tree search checks {len(checked)} of 11 objects')
    _caption(ax, TW / 2, -40, f'Numbered: the order the search checks them. Dashed circle: '
                              f'the best distance found, {best[1]:.1f} mm.\n'
                              'A grey box that lies wholly outside the circle cannot hold '
                              'anything nearer.')
    _save(fig, NN, 'kd-tree-search.svg')


def _uneven_cloud() -> Array:
    rng = np.random.default_rng(11)
    dense = rng.normal((170, 220), (38, 32), (160, 2))
    sparse = rng.uniform((330, 40), (570, 360), (26, 2))
    return np.vstack([dense, sparse])


def radius_vs_k() -> None:
    """A radius search returns more points where the cloud is dense; k nearest always k."""
    pts = _uneven_cloud()
    queries = [np.array([175.0, 215.0]), np.array([450.0, 200.0])]
    radius, k = 40.0, 8
    fig, axes = plt.subplots(1, 2, figsize=(15.0, 5.4), facecolor='white')
    for ax, mode in zip(axes, ('radius', 'k')):
        _table(ax)
        ax.plot(pts[:, 0], pts[:, 1], 'o', ms=3.5, color=MUTED, mew=0, zorder=4)
        for q, qc in zip(queries, (GRIP, WRIST)):
            d = np.linalg.norm(pts - q, axis=1)
            if mode == 'radius':
                sel = np.where(d <= radius)[0]
                ax.add_patch(Circle((q[0], q[1]), radius, facecolor='none', edgecolor=qc,
                                    lw=1.8, zorder=5))
                reach = radius
            else:
                sel = np.argsort(d)[:k]
                reach = float(d[sel].max())
                ax.add_patch(Circle((q[0], q[1]), reach, facecolor='none', edgecolor=qc,
                                    lw=1.8, ls='--', zorder=5))
            ax.plot(pts[sel, 0], pts[sel, 1], 'o', ms=5.5, color=qc, mec=INK, mew=0.5,
                    zorder=6)
            ax.plot([q[0]], [q[1]], marker='X', ms=11, color=qc, mec=INK, zorder=8)
            text = (f'{len(sel)} points' if mode == 'radius'
                    else f'reaches {reach:.0f} mm')
            ty = q[1] + max(reach, radius) + 22 if q[0] > 300 else 40
            _label(ax, q[0], ty, text, size=10, color=qc, weight='bold', box=True)
        if mode == 'radius':
            _title(ax, TW / 2, TD + 60, f'Radius search: everything within {radius:.0f} mm')
            _caption(ax, TW / 2, -40, 'The same circle holds many points in the crowded\n'
                                      'patch and none at all in the thin patch.')
        else:
            _title(ax, TW / 2, TD + 60, f'k nearest: always the {k} closest')
            _caption(ax, TW / 2, -40, 'Always 8 points, but in the thin patch the\n'
                                      '8th one can be far away.')
    fig.subplots_adjust(wspace=0.08)
    _save(fig, NN, 'radius-vs-k-nearest.svg')


# --------------------------------------------------------------------------
# 03_iterative-closest-point
# --------------------------------------------------------------------------

ICP: str = 'iterative-closest-point'


def _icp_view(ax: Axes, scan: Array, model_now: Array, pairs: NDArray[np.int64] | None,
              lim: tuple[float, float, float, float]) -> None:
    _axes(ax, (lim[0], lim[1]), (lim[2], lim[3]))
    ax.add_patch(Rectangle((lim[0], lim[2]), lim[1] - lim[0], lim[3] - lim[2],
                           facecolor=TABLE, edgecolor='none', zorder=1))
    _bracket(ax, scan, MUTED, size=3.5, z=4)
    if pairs is not None:
        for p, j in zip(model_now, pairs):
            ax.plot([p[0], scan[j, 0]], [p[1], scan[j, 1]], color=GRIP, lw=1.0, zorder=5)
    _bracket(ax, model_now, LINK, size=5.5, z=6)


def closest_pairs() -> None:
    """Round one: every model point is paired with the closest scan point."""
    scan = scan_of(GOOD_TURN, GOOD_SHIFT)
    hist = icp(MODEL, scan)
    cur, j, gap = hist[0]
    fig, ax = plt.subplots(figsize=(8.4, 6.6), facecolor='white')
    _icp_view(ax, scan, cur, j, (-40, 190, -30, 150))
    _label(ax, -30, 140, 'grey dots: the scan (where the bracket really is)', color=MUTED,
           ha='left', size=10, box=True)
    _label(ax, -30, 130, 'blue dots: the model at its first guess', color=LINK, ha='left',
           size=10, box=True)
    _label(ax, -30, 120, 'red lines: each model point to its closest scan point', color=GRIP,
           ha='left', size=10, box=True)
    _title(ax, 75, 160, 'Round 1: pair every model point with its closest scan point')
    _caption(ax, 75, -35, f'The mean length of the red lines is {gap:.1f} mm. Many pairs are '
                          'wrong:\nseveral model points share one scan point, but the pairs '
                          'still pull the model the right way.')
    _save(fig, ICP, 'closest-pairs.svg')


def rounds() -> None:
    """The model after rounds 0, 1, 4 and the last one."""
    scan = scan_of(GOOD_TURN, GOOD_SHIFT)
    hist = icp(MODEL, scan)
    last = len(hist) - 1
    picks = [0, 1, 4, last]
    fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.8), facecolor='white')
    for ax, k in zip(axes, picks):
        cur, j, gap = hist[k]
        _icp_view(ax, scan, cur, j if k < last else None, (-40, 190, -30, 150))
        r, t = best_fit(MODEL, cur)
        name = 'start' if k == 0 else f'after round {k}'
        _title(ax, 75, 165, name)
        _caption(ax, 75, -35, f'turned {angle_of(r):.1f}°\nmean gap {gap:.1f} mm', size=10.5)
    fig.subplots_adjust(wspace=0.05)
    _save(fig, ICP, 'rounds.svg')


def gap_per_round() -> None:
    """The mean gap falls quickly, then flattens; the loop stops when it stops falling."""
    scan = scan_of(GOOD_TURN, GOOD_SHIFT)
    hist = icp(MODEL, scan)
    gaps = [h[2] for h in hist]
    fig, ax = plt.subplots(figsize=(8.6, 4.6), facecolor='white')
    ax.plot(range(len(gaps)), gaps, 'o-', color=LINK, lw=2)
    ax.axhline(0.8, color=MUTED, lw=1.0, ls='--')
    _label(ax, 0.3, 0.8 + 0.45, 'the noise added to the scan: 0.8 mm', color=MUTED, size=9.5,
           ha='left')
    _label(ax, 0.4, gaps[0], f'{gaps[0]:.1f} mm at the start', ha='left', size=9.5,
           color=LINK)
    _label(ax, len(gaps) - 1, gaps[-1] + 1.4, f'{gaps[-1]:.2f} mm\nat the end', ha='right',
           size=9.5, color=LINK)
    ax.set_xlabel('round')
    ax.set_ylabel('mean gap from each model point\nto its closest scan point (mm)')
    ax.set_ylim(0, gaps[0] * 1.12)
    ax.set_xticks(range(0, len(gaps), 2))
    ax.grid(True, color=GRID, lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.set_title('The gap after each round', fontsize=12, weight='bold')
    _save(fig, ICP, 'gap-per-round.svg')


def wrong_start() -> None:
    """A start 20 degrees off ends right; a start 120 degrees off ends stuck and wrong."""
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.6), facecolor='white')
    for ax, turn in zip(axes, (GOOD_TURN, BAD_TURN)):
        scan = scan_of(turn, GOOD_SHIFT)
        hist = icp(MODEL, scan)
        cur, _j, gap = hist[-1]
        r, _t = best_fit(MODEL, cur)
        lim = (-60, 210, -60, 170)
        _axes(ax, (lim[0], lim[1]), (lim[2], lim[3]))
        ax.add_patch(Rectangle((lim[0], lim[2]), lim[1] - lim[0], lim[3] - lim[2],
                               facecolor=TABLE, edgecolor='none', zorder=1))
        _bracket(ax, scan, MUTED, size=3.5, z=4)
        _bracket(ax, MODEL, LINK_PALE, size=4.5, z=5)
        _bracket(ax, cur, LINK if turn == GOOD_TURN else GRIP, size=5.5, z=6)
        ok = turn == GOOD_TURN
        _title(ax, 75, 185, f'Real turn {turn:.0f}°: ' + ('found' if ok else 'stuck'))
        _caption(ax, 75, -65, f'ICP stops after {len(hist) - 1} rounds, turned '
                              f'{angle_of(r):.1f}°,\nmean gap {gap:.1f} mm. '
                              + ('The model sits on the scan.' if ok
                                 else 'The model lies across the scan.'))
    _label(axes[0], -50, 160, 'grey: the scan.  pale blue: the first guess.', color=MUTED,
           ha='left', size=9.5, box=True)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, ICP, 'wrong-start.svg')


# --------------------------------------------------------------------------
# 04_assignment-and-matching
# --------------------------------------------------------------------------

ASSIGN: str = 'assignment-and-matching'
MUG_COLORS: list[str] = [LINK, SLIDE, WRIST]


def _belt(ax: Axes, x0: float = 40, x1: float = 500, y0: float = 90, y1: float = 290,
          edge: bool = False) -> None:
    _axes(ax, (x0, x1), (y0, y1))
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=TABLE,
                           edgecolor=INK if edge else 'none', lw=1.0, zorder=1))


# Where the names and costs go, so that none of them sit on a ring, a square or a line.
MUG_NAME_OFFSET: list[tuple[float, float]] = [(0, 30), (0, 30), (0, -30)]
DET_NAME_OFFSET: list[tuple[float, float]] = [(0, -30), (0, -30), (0, -30)]
COST_OFFSET: list[tuple[float, float]] = [(0, -58), (0, 58), (0, 34)]


def _pairs(ax: Axes, tracks: Array, dets: Array, pairs: list[tuple[int, int]],
           costs: Array | None, order: bool = False) -> None:
    """Dashed rings where the mugs were, squares for the detections, a line for each pair."""
    for i, t in enumerate(tracks):
        _mug_top(ax, t, MUG_COLORS[i], hollow=True)
        dx, dy = MUG_NAME_OFFSET[i]
        _label(ax, t[0] + dx, t[1] + dy, f'mug {i + 1}', weight='bold', color=MUG_COLORS[i])
    for j, d in enumerate(dets):
        ax.plot([d[0]], [d[1]], 's', ms=11, color=INK, zorder=7)
        dx, dy = DET_NAME_OFFSET[j]
        _label(ax, d[0] + dx, d[1] + dy, f'd{j + 1}', weight='bold', size=10.5)
    for step, (i, j) in enumerate(pairs):
        a, b = tracks[i], dets[j]
        # an earlier pair is drawn on top of a later one where the two lines overlap
        ax.plot([a[0], b[0]], [a[1], b[1]], color=MUG_COLORS[i], lw=3.0,
                zorder=6 + 0.1 * (len(pairs) - step))
        if costs is not None:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = COST_OFFSET[i]
            tag = f'{costs[i, j]:.1f}' if not order else f'{step + 1}st: {costs[i, j]:.1f}'
            if order:
                tag = tag.replace('2st', '2nd').replace('3st', '3rd')
            _label(ax, mx + dx, my + dy, tag, size=10, color=MUG_COLORS[i], weight='bold',
                   box=True)


def cost_table_picture() -> None:
    """Three mugs one frame ago, three detections now, and the table of distances."""
    cost = cost_table(TRACKS, DETS)
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1.0]})
    ax = axes[0]
    _belt(ax)
    _pairs(ax, TRACKS, DETS, [], None)
    _arrow(ax, (60, 110), (160, 110), color=MUTED, lw=2)
    _label(ax, 170, 110, 'the belt moves this way', color=MUTED, ha='left', size=10)
    _atitle(ax, 'One frame ago (dashed rings) and now (squares)', y=1.08)

    ax = axes[1]
    _axes(ax, (0, 4.2), (0, 4.4))
    _title(ax, 2.1, 4.25, 'Cost: distance in mm')
    for j in range(3):
        _label(ax, 1.6 + j, 3.55, f'd{j + 1}', weight='bold')
    for i in range(3):
        _label(ax, 0.55, 2.8 - i, f'mug {i + 1}', weight='bold', color=MUG_COLORS[i])
        for j in range(3):
            ax.add_patch(Rectangle((1.1 + j, 2.3 - i), 1.0, 1.0, facecolor='white',
                                   edgecolor=GRID, lw=1.2))
            _label(ax, 1.6 + j, 2.8 - i, f'{cost[i, j]:.1f}', size=11)
    _caption(ax, 2.1, -0.05, 'One row per mug, one column per detection.')
    fig.subplots_adjust(wspace=0.05)
    _save(fig, ASSIGN, 'cost-table.svg')


def greedy_vs_best() -> None:
    """Greedy takes the cheapest pair first and pays for it later."""
    cost = cost_table(TRACKS, DETS)
    g_pairs, g_total = greedy_assignment(cost)
    b_pairs, b_total = best_assignment(cost)
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 4.6), facecolor='white')
    for ax, pairs, total, name in ((axes[0], g_pairs, g_total, 'Greedy'),
                                   (axes[1], b_pairs, b_total, 'Best total (Hungarian)')):
        _belt(ax)
        _pairs(ax, TRACKS, DETS, pairs, cost, order=name == 'Greedy')
        _atitle(ax, f'{name}: total {total:.1f} mm', y=1.08)
    _acaption(axes[0], 'Greedy took the cheapest pair first, then the cheapest left, and so on.')
    _acaption(axes[1], 'Every mug moved about 50 mm with the belt.')
    fig.subplots_adjust(wspace=0.06)
    _save(fig, ASSIGN, 'greedy-vs-best.svg')


def hungarian_steps() -> None:
    """Subtract each row's smallest number, then each column's; a zero in each row and column."""
    cost = np.round(cost_table(TRACKS, DETS)).astype(int)
    rows = cost - cost.min(1, keepdims=True)
    cols = rows - rows.min(0, keepdims=True)
    b_pairs, _t = best_assignment(cost_table(TRACKS, DETS))
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6), facecolor='white')
    stages = [(cost, 'Costs, rounded to whole mm', 'Row minima: '
               + ', '.join(str(v) for v in cost.min(1))),
              (rows, 'Step 1: subtract each row\'s smallest', 'Column minima: '
               + ', '.join(str(v) for v in rows.min(0))),
              (cols, 'Step 2: subtract each column\'s smallest',
               'Pick one zero in every row and column.')]
    for k, (ax, (m, title, note)) in enumerate(zip(axes, stages)):
        _axes(ax, (0, 4.3), (-0.5, 4.4))
        _title(ax, 2.2, 4.2, title, size=11.5)
        for j in range(3):
            _label(ax, 1.7 + j, 3.55, f'd{j + 1}', weight='bold')
        for i in range(3):
            _label(ax, 0.6, 2.8 - i, f'mug {i + 1}', weight='bold', color=MUG_COLORS[i])
            for j in range(3):
                chosen = k == 2 and (i, j) in b_pairs
                zero = m[i, j] == 0 and k > 0
                face = JOINT if chosen else ('#fff3d6' if zero else 'white')
                ax.add_patch(Rectangle((1.2 + j, 2.3 - i), 1.0, 1.0, facecolor=face,
                                       edgecolor=GRID, lw=1.2))
                _label(ax, 1.7 + j, 2.8 - i, str(m[i, j]), size=11,
                       weight='bold' if chosen else 'normal')
        _caption(ax, 2.2, -0.1, note, size=10)
    fig.subplots_adjust(wspace=0.05)
    _save(fig, ASSIGN, 'hungarian-steps.svg')


def gate_new_and_lost() -> None:
    """Mug 3 is hidden and a new mug appears. Without a gate the solver pairs them anyway."""
    cost = cost_table(TRACKS, DETS_2)
    plain, plain_total = best_assignment(cost)
    gated, _g_total = best_assignment(cost, gate=GATE)
    fig, axes = plt.subplots(1, 2, figsize=(15.0, 5.0), facecolor='white')
    for ax, pairs, name in ((axes[0], plain, 'No gate: every mug gets a detection'),
                            (axes[1], gated, f'Gate of {GATE:.0f} mm: one lost, one new')):
        _belt(ax, 0, 640, 60, 360)
        _pairs(ax, TRACKS, DETS_2, pairs, None)
        for i, j in pairs:
            a, b = TRACKS[i], DETS_2[j]
            if cost[i, j] > GATE:
                _label(ax, (a[0] + b[0]) / 2 - 40, (a[1] + b[1]) / 2 + 20,
                       f'{cost[i, j]:.0f} mm: wrong', color=GRIP, weight='bold', box=True)
        if ax is axes[1]:
            for t in TRACKS:
                ax.add_patch(Circle((t[0], t[1]), GATE, facecolor='none', edgecolor=MUTED,
                                    lw=1.0, ls=':', zorder=3))
            matched_tracks = {i for i, _ in pairs}
            matched_dets = {j for _, j in pairs}
            for i in range(3):
                if i not in matched_tracks:
                    _label(ax, TRACKS[i][0] + 110, TRACKS[i][1] - 10,
                           'not seen:\nkeep it,\nmark it lost', size=9.5, color=GRIP, box=True)
            for j in range(3):
                if j not in matched_dets:
                    _label(ax, DETS_2[j][0], DETS_2[j][1] + 32, 'new mug', size=9.5,
                           color=GRIP, weight='bold', box=True)
        _atitle(ax, name, y=1.07)
    _acaption(axes[0], f'Total {plain_total:.1f} mm. Mug 3 is paired with a mug that was '
                       'never mug 3.')
    _acaption(axes[1], 'Dotted circles: the gate round each mug. A pair outside it is not '
                       'allowed.')
    fig.subplots_adjust(wspace=0.05)
    _save(fig, ASSIGN, 'gate-new-and-lost.svg')


# --------------------------------------------------------------------------
# the numbers the documents quote
# --------------------------------------------------------------------------

def print_numbers() -> None:
    tree = kd_build(list(OBJECTS.items()))
    log: list[tuple[str, str, float]] = []
    best = kd_nearest(tree, QUERY, None, log)
    print('k-d tree search from', QUERY, '->', best)
    for e in log:
        print('   ', e[0], e[1], f'{e[2]:.1f}')
    print('brute force distances:',
          {n: round(_dist(p, QUERY), 1) for n, p in OBJECTS.items()})
    pts = _uneven_cloud()
    for q in ([175.0, 215.0], [450.0, 200.0]):
        d = np.linalg.norm(pts - np.array(q), axis=1)
        print('radius 40 around', q, '->', int((d <= 40).sum()), ' 8th nearest at',
              round(float(np.sort(d)[7]), 1))

    print('model points', len(MODEL), 'scan points', len(scan_of(0, (0, 0))))
    for turn in (GOOD_TURN, BAD_TURN):
        scan = scan_of(turn, GOOD_SHIFT)
        hist = icp(MODEL, scan)
        print(f'ICP real turn {turn}, shift {GOOD_SHIFT}: rounds {len(hist) - 1}')
        for k, (cur, _j, gap) in enumerate(hist):
            r, _t = best_fit(MODEL, cur)
            sh = cur.mean(0) - MODEL_C
            print(f'   round {k:2d}: gap {gap:6.2f} mm  turned {angle_of(r):7.2f}  '
                  f'centre moved ({sh[0]:.1f}, {sh[1]:.1f})')
    tri = np.array([[0, 0], [40, 0], [0, 20]], float)
    moved = tri @ rot(30).T + np.array([10.0, 5.0])
    r, t = best_fit(tri, moved)
    print('3-point best fit: turn', round(angle_of(r), 3), 'shift', np.round(t, 3),
          'centres', np.round(tri.mean(0), 2), np.round(moved.mean(0), 2))
    print('moved triangle', np.round(moved, 2))

    cost = cost_table(TRACKS, DETS)
    print('cost\n', np.round(cost, 1))
    print('greedy', greedy_assignment(cost))
    print('best', best_assignment(cost))
    for perm in itertools.permutations(range(3)):
        print('   ', perm, round(float(sum(cost[i, perm[i]] for i in range(3))), 1))
    c2 = cost_table(TRACKS, DETS_2)
    print('cost 2\n', np.round(c2, 1))
    print('no gate', best_assignment(c2), 'gate', best_assignment(c2, GATE))
    rng = np.random.default_rng(7)
    for n in (10, 30, 100, 300, 1000, 3000):
        p = rng.uniform(0, 600, (n, 2))
        print('n', n, 'brute', n * n, 'kd', kd_count_checks(p, p + rng.normal(0, 2.0, p.shape)))


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if '--numbers' in sys.argv:
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    three_questions()
    work_grows()
    brute_force()
    kd_tree_boxes()
    kd_tree_search()
    radius_vs_k()
    closest_pairs()
    rounds()
    gap_per_round()
    wrong_start()
    cost_table_picture()
    greedy_vs_best()
    hungarian_steps()
    gate_new_and_lost()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
