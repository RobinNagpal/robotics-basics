"""Generate more diagrams for docs/06_programming-techniques/03_searching-and-matching/.

This script draws the pictures for two pieces of that chapter:

- 03_also-used/01_image-features-and-matching.md, into
  docs/images/searching-and-matching/image-features-and-matching/
- the section "Getting a first guess: 3D features and global registration" of
  02_most-used/02_iterative-closest-point.md, into
  docs/images/searching-and-matching/iterative-closest-point/

Run with:  pixi run python ../docs/diagrams/searching_and_matching_2.py
or, from the repo root:  python3 docs/diagrams/searching_and_matching_2.py --png <dir>
Add --numbers to print the worked-example numbers that the documents quote.

Every result drawn here is computed, not drawn by hand. The script makes a
picture of a flat printed label, warps it into a second picture, finds corners,
describes them with rotated binary tests (the idea inside ORB), matches them,
applies the ratio test and fits a homography with random sample consensus
(RANSAC). For the ICP section it computes normals and a small local shape
feature on a bracket outline, matches features, fits a rough pose with RANSAC and
finishes it with ICP. It needs only NumPy and Matplotlib.
"""

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

Array = NDArray[np.float64]

FEATURES: str = 'image-features-and-matching'
ICP_DIR: str = 'iterative-closest-point'


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


def _atitle(ax: Axes, text: str, y: float = 1.06, size: float = 12) -> None:
    ax.text(0.5, y, text, fontsize=size, ha='center', va='bottom', color=INK,
            weight='bold', transform=ax.transAxes)


def _acaption(ax: Axes, text: str, y: float = -0.03, size: float = 10) -> None:
    ax.text(0.5, y, text, fontsize=size, ha='center', va='top', color=MUTED,
            transform=ax.transAxes)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# part 1: image features, written out in NumPy
# --------------------------------------------------------------------------

def gauss_kernel(sigma: float) -> Array:
    r = int(math.ceil(3 * sigma))
    x = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-x * x / (2 * sigma * sigma))
    return k / k.sum()


def blur(img: Array, sigma: float) -> Array:
    """Separable Gaussian blur, with the edge pixels repeated outwards."""
    k = gauss_kernel(sigma)
    r = len(k) // 2
    p = np.pad(img, r, mode='edge')
    tmp = sum(k[i] * p[:, i:i + img.shape[1]] for i in range(len(k)))
    out = sum(k[i] * tmp[i:i + img.shape[0], :] for i in range(len(k)))
    return np.asarray(out)


def gradients(img: Array) -> tuple[Array, Array]:
    gy, gx = np.gradient(img)
    return gx, gy


def make_label(seed: int = 3, w: int = 200, h: int = 140, n_shapes: int = 34,
               stripe: bool = True) -> Array:
    """A flat printed label: a pale card with dark and grey shapes on it, and a
    strip of identical small squares, like the bars of a barcode."""
    rng = np.random.default_rng(seed)
    img = np.full((h, w), 0.85)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n_shapes):
        kind = rng.integers(0, 3)
        g = float(rng.choice([0.08, 0.3, 0.55]))
        cx, cy = rng.uniform(10, w - 10), rng.uniform(10, h - 10)
        s = rng.uniform(6, 22)
        if kind == 0:
            a = rng.uniform(0, math.pi)
            u = (xx - cx) * math.cos(a) + (yy - cy) * math.sin(a)
            v = -(xx - cx) * math.sin(a) + (yy - cy) * math.cos(a)
            m = (np.abs(u) < s) & (np.abs(v) < s * rng.uniform(0.3, 0.9))
        elif kind == 1:
            m = (xx - cx) ** 2 + (yy - cy) ** 2 < (s * 0.8) ** 2
        else:
            a = rng.uniform(0, 2 * math.pi)
            pts = [(cx + s * math.cos(a + k * 2.1), cy + s * math.sin(a + k * 2.1))
                   for k in range(3)]
            m = np.ones_like(img, bool)
            for i in range(3):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 3]
                (x3, y3) = pts[(i + 2) % 3]
                side = (x2 - x1) * (yy - y1) - (y2 - y1) * (xx - x1)
                ref = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
                m &= side * ref > 0
        img[m] = g
    if stripe:
        img[h - 26:h - 8, 12:w - 12] = 0.85
        for k in range(9):
            x0 = 18 + k * 19
            img[h - 22:h - 12, x0:x0 + 10] = 0.08
    img[:3, :] = img[-3:, :] = 0.2
    img[:, :3] = img[:, -3:] = 0.2
    return img


def homography_from(a: Array, b: Array) -> Array:
    """The 3 x 3 homography H with b ~ H a, from 4 or more point pairs (the direct linear
    transform, with the points first moved and scaled so the numbers are well sized)."""
    def norm(p: Array) -> tuple[Array, Array]:
        c = p.mean(0)
        s = math.sqrt(2) / max(1e-9, float(np.mean(np.linalg.norm(p - c, axis=1))))
        t = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
        return (p - c) * s, t
    an, ta = norm(a)
    bn, tb = norm(b)
    rows = []
    for (x, y), (u, v) in zip(an, bn):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _u, _s, vt = np.linalg.svd(np.array(rows))
    hn = vt[-1].reshape(3, 3)
    h = np.linalg.inv(tb) @ hn @ ta
    return h / h[2, 2]


def apply_h(h: Array, p: Array) -> Array:
    q = np.c_[p, np.ones(len(p))] @ h.T
    return q[:, :2] / q[:, 2:3]


# Where the label's four corners land in the scene picture: turned, shrunk a
# little, and tilted, as a label on a box seen from an angle.
SCENE_W, SCENE_H = 320, 230
LABEL_W, LABEL_H = 200, 140


def true_h() -> Array:
    src = np.array([[0, 0], [LABEL_W, 0], [LABEL_W, LABEL_H], [0, LABEL_H]], float)
    dst = np.array([[92, 28], [268, 62], [236, 196], [58, 158]], float)
    return homography_from(src, dst)


def bilinear(img: Array, x: Array, y: Array, fill: float = np.nan) -> Array:
    h, w = img.shape
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < w - 1) & (y0 < h - 1)
    x0c, y0c = np.clip(x0, 0, w - 2), np.clip(y0, 0, h - 2)
    v = (img[y0c, x0c] * (1 - fx) * (1 - fy) + img[y0c, x0c + 1] * fx * (1 - fy)
         + img[y0c + 1, x0c] * (1 - fx) * fy + img[y0c + 1, x0c + 1] * fx * fy)
    return np.where(ok, v, fill)


def make_scene(label: Array, h: Array, seed: int = 11) -> Array:
    """The label warped into a cluttered scene, with camera noise."""
    bg = make_label(seed=seed, w=SCENE_W, h=SCENE_H, n_shapes=40, stripe=False) * 0.6 + 0.3
    # a second, smaller sticker with part of the same print on it, on another box
    bg[160:215, 4:84] = label[10:65, 20:100]
    yy, xx = np.mgrid[0:SCENE_H, 0:SCENE_W]
    back = apply_h(np.linalg.inv(h), np.c_[xx.ravel(), yy.ravel()].astype(float))
    v = bilinear(label, back[:, 0], back[:, 1]).reshape(SCENE_H, SCENE_W)
    img = np.where(np.isnan(v), bg, v)
    rng = np.random.default_rng(seed)
    return np.clip(img + rng.normal(0, 0.02, img.shape), 0, 1)


def harris(img: Array, sigma: float = 1.5) -> Array:
    """The corner score of every pixel: large only where the brightness changes
    in two directions at once."""
    gx, gy = gradients(blur(img, 1.0))
    sxx, syy, sxy = blur(gx * gx, sigma), blur(gy * gy, sigma), blur(gx * gy, sigma)
    return sxx * syy - sxy * sxy - 0.05 * (sxx + syy) ** 2


def corners(img: Array, n: int, margin: int = 22, win: int = 4) -> Array:
    """The n strongest corners, each the best in its own (2 win + 1) square."""
    r = harris(img)
    h, w = r.shape
    best = np.full_like(r, -np.inf)
    p = np.pad(r, win, mode='constant', constant_values=-np.inf)
    for dy in range(2 * win + 1):
        for dx in range(2 * win + 1):
            best = np.maximum(best, p[dy:dy + h, dx:dx + w])
    peak = (r >= best) & (r > 2e-7)
    peak[:margin, :] = peak[-margin:, :] = False
    peak[:, :margin] = peak[:, -margin:] = False
    ys, xs = np.nonzero(peak)
    order = np.argsort(-r[ys, xs])[:n]
    return np.c_[xs[order], ys[order]].astype(float)


# The test pattern: 256 pairs of pixel positions inside a circle of radius 15
# around the corner. The same pattern is used for every corner in both pictures.
PATCH_R: float = 15.0


def test_pairs(n: int = 256, seed: int = 5) -> Array:
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < n:
        a = rng.normal(0, PATCH_R / 2.2, 4)
        if np.hypot(a[0], a[1]) < PATCH_R and np.hypot(a[2], a[3]) < PATCH_R:
            out.append(a)
    return np.array(out)


PAIRS: Array = test_pairs()


def orientation(img: Array, p: Array) -> float:
    """The direction from the corner to the 'centre of brightness' of its patch."""
    r = int(PATCH_R)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    m = xx ** 2 + yy ** 2 <= r * r
    patch = img[int(p[1]) - r:int(p[1]) + r + 1, int(p[0]) - r:int(p[0]) + r + 1]
    return math.atan2(float((patch * yy)[m].sum()), float((patch * xx)[m].sum()))


def describe(img: Array, pts: Array) -> tuple[NDArray[np.bool_], Array]:
    """Rotated binary tests (the idea inside ORB): for each pair of positions, turned
    to the corner's own direction, is the first pixel darker than the second?"""
    smooth = blur(img, 2.0)
    bits = np.zeros((len(pts), len(PAIRS)), bool)
    angles = np.zeros(len(pts))
    for i, p in enumerate(pts):
        a = orientation(smooth, p)
        angles[i] = a
        c, s = math.cos(a), math.sin(a)
        x1 = p[0] + c * PAIRS[:, 0] - s * PAIRS[:, 1]
        y1 = p[1] + s * PAIRS[:, 0] + c * PAIRS[:, 1]
        x2 = p[0] + c * PAIRS[:, 2] - s * PAIRS[:, 3]
        y2 = p[1] + s * PAIRS[:, 2] + c * PAIRS[:, 3]
        bits[i] = bilinear(smooth, x1, y1, 0.0) < bilinear(smooth, x2, y2, 0.0)
    return bits, angles


def hamming(a: NDArray[np.bool_], b: NDArray[np.bool_]) -> NDArray[np.int64]:
    return (a[:, None, :] != b[None, :, :]).sum(2)


def ransac_h(a: Array, b: Array, tries: int = 1000, limit: float = 3.0,
             seed: int = 2) -> tuple[Array, NDArray[np.bool_], int]:
    rng = np.random.default_rng(seed)
    best = np.zeros(len(a), bool)
    best_try = 0
    for t in range(tries):
        idx = rng.choice(len(a), 4, replace=False)
        try:
            h = homography_from(a[idx], b[idx])
        except np.linalg.LinAlgError:
            continue
        if not np.all(np.isfinite(h)):
            continue
        err = np.linalg.norm(apply_h(h, a) - b, axis=1)
        inl = err < limit
        if inl.sum() > best.sum():
            best, best_try = inl, t + 1
    h = homography_from(a[best], b[best])
    return h, best, best_try


class FeatureRun:
    """The whole image-feature pipeline, run once and kept for the pictures."""

    def __init__(self) -> None:
        self.label = make_label()
        self.h_true = true_h()
        self.scene = make_scene(self.label, self.h_true)
        self.kp_a = corners(self.label, 150)
        self.kp_b = corners(self.scene, 250)
        self.da, self.ang_a = describe(self.label, self.kp_a)
        self.db, self.ang_b = describe(self.scene, self.kp_b)
        d = hamming(self.da, self.db)
        self.dist = d
        order = np.argsort(d, axis=1)
        self.nn = order[:, 0]
        self.d1 = d[np.arange(len(d)), order[:, 0]].astype(float)
        self.d2 = d[np.arange(len(d)), order[:, 1]].astype(float)
        self.ratio = self.d1 / self.d2
        where = apply_h(self.h_true, self.kp_a)
        self.truth_err = np.linalg.norm(where - self.kp_b[self.nn], axis=1)
        self.correct = self.truth_err < 3.0
        self.keep = self.ratio < 0.8
        a = self.kp_a[self.keep]
        b = self.kp_b[self.nn[self.keep]]
        self.h_fit, self.inl, self.found_at = ransac_h(a, b)
        box = np.array([[0, 0], [LABEL_W, 0], [LABEL_W, LABEL_H], [0, LABEL_H]], float)
        self.box_true = apply_h(self.h_true, box)
        self.box_fit = apply_h(self.h_fit, box)


_RUN: FeatureRun | None = None


def run() -> FeatureRun:
    global _RUN
    if _RUN is None:
        _RUN = FeatureRun()
    return _RUN


def shift_cost(img: Array, p: tuple[int, int], r: int = 6, s: int = 5) -> Array:
    """How much a small square patch changes when it is shifted by (dx, dy)."""
    x, y = p
    base = img[y - r:y + r + 1, x - r:x + r + 1]
    out = np.zeros((2 * s + 1, 2 * s + 1))
    for dy in range(-s, s + 1):
        for dx in range(-s, s + 1):
            moved = img[y + dy - r:y + dy + r + 1, x + dx - r:x + dx + r + 1]
            out[dy + s, dx + s] = float(((moved - base) ** 2).mean())
    return out


# --------------------------------------------------------------------------
# 03_also-used/01_image-features-and-matching
# --------------------------------------------------------------------------

def _shift_spots(img: Array) -> list[tuple[str, tuple[int, int]]]:
    """A flat spot, a spot on a straight edge and a corner, found in the label."""
    gx, gy = gradients(blur(img, 1.0))
    g = np.hypot(gx, gy)
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inner = (xs > 20) & (xs < img.shape[1] - 20) & (ys > 20) & (ys < img.shape[0] - 20)
    # flat: the lowest gradient in a 13 x 13 window
    flat_score = np.where(inner, blur(g, 4.0), np.inf)
    fy, fx = np.unravel_index(int(np.argmin(flat_score)), g.shape)
    # edge and corner: try many spots with a strong gradient, and keep the one whose
    # patch changes least for its easiest shift (an edge) and most (a corner)
    cand = [(int(x), int(y)) for y, x in zip(*np.nonzero(inner & (g > 0.08)))][::3]
    lows = []
    for (x, y) in cand:
        c = shift_cost(img, (x, y))
        lows.append((float(np.sort(np.delete(c.ravel(), c.size // 2))[0]), float(c.max())))
    e = int(np.argmin([lo / hi for lo, hi in lows]))
    k = int(np.argmax([lo for lo, _hi in lows]))
    ex, ey = cand[e]
    cx, cy = cand[k]
    return [('on a flat area', (int(fx), int(fy))), ('on an edge', (int(ex), int(ey))),
            ('on a corner', (int(cx), int(cy)))]


def shift_test() -> None:
    rr = run()
    img = rr.label
    spots = _shift_spots(img)
    fig, axes = plt.subplots(2, 3, figsize=(12.0, 8.2), facecolor='white',
                             gridspec_kw={'height_ratios': [1.0, 1.0], 'hspace': 0.45})
    for k, (name, (x, y)) in enumerate(spots):
        ax = axes[0, k]
        r = 14
        ax.imshow(img[y - r:y + r + 1, x - r:x + r + 1], cmap='gray', vmin=0, vmax=1,
                  extent=(-r - 0.5, r + 0.5, r + 0.5, -r - 0.5))
        ax.add_patch(Rectangle((-6.5, -6.5), 13, 13, fill=False, edgecolor=GRIP, lw=2.2))
        ax.set_xticks([])
        ax.set_yticks([])
        _atitle(ax, f'{k + 1}. A patch {name}', y=1.03)
        cost = shift_cost(img, (x, y))
        ax2 = axes[1, k]
        ax2.imshow(cost, cmap='viridis', vmin=0, vmax=0.08,
                   extent=(-5.5, 5.5, 5.5, -5.5))
        ax2.set_xticks([-5, 0, 5])
        ax2.set_yticks([-5, 0, 5])
        ax2.tick_params(labelsize=9, colors=MUTED)
        ax2.set_xlabel('shift left-right (pixels)', fontsize=9, color=MUTED)
        if k == 0:
            ax2.set_ylabel('shift up-down (pixels)', fontsize=9, color=MUTED)
        low = float(np.sort(np.delete(cost.ravel(), cost.size // 2))[0])
        worst = {0: 'every shift looks the same',
                 1: 'shifting along the edge\nlooks the same',
                 2: 'every shift looks different'}[k]
        _acaption(ax2, f'{worst}\nsmallest change for any shift: {low:.4f}', y=-0.22)
    fig.text(0.5, 0.505, 'How much the red square changes when it is shifted '
             '(dark = no change, yellow = a big change)', ha='center', fontsize=11,
             color=INK)
    _save(fig, FEATURES, 'shift-test.svg')


def patch_to_bits() -> None:
    rr = run()
    # a correct, confident match that is well away from the picture edge
    good = [i for i in range(len(rr.kp_a)) if rr.correct[i] and rr.keep[i]]
    i = good[0]
    j = int(rr.nn[i])
    other = int(np.argsort(rr.dist[i])[len(rr.kp_b) // 2])     # a typical wrong corner
    fig = plt.figure(figsize=(13.0, 5.7), facecolor='white')
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.36], hspace=0.08, wspace=0.12)
    shown = [(rr.label, rr.kp_a[i], rr.ang_a[i], rr.da[i], '1. A corner in the label'),
             (rr.scene, rr.kp_b[j], rr.ang_b[j], rr.db[j],
              '2. The same corner in the scene'),
             (rr.scene, rr.kp_b[other], rr.ang_b[other], rr.db[other],
              '3. A different corner in the scene')]
    for k, (img, p, a, bits, title) in enumerate(shown):
        ax = fig.add_subplot(gs[0, k])
        r = 20
        x, y = int(round(p[0])), int(round(p[1]))
        ax.imshow(img[y - r:y + r + 1, x - r:x + r + 1], cmap='gray', vmin=0, vmax=1,
                  extent=(x - r - 0.5, x + r + 0.5, y + r + 0.5, y - r - 0.5))
        ax.add_patch(Circle((p[0], p[1]), PATCH_R, fill=False, edgecolor=LINK, lw=1.5,
                            ls='--'))
        c, s = math.cos(a), math.sin(a)
        for q in PAIRS[:14]:
            x1, y1 = p[0] + c * q[0] - s * q[1], p[1] + s * q[0] + c * q[1]
            x2, y2 = p[0] + c * q[2] - s * q[3], p[1] + s * q[2] + c * q[3]
            ax.plot([x1, x2], [y1, y2], color=JOINT, lw=1.2, alpha=0.95)
            ax.plot([x1], [y1], 'o', ms=3.5, color=JOINT)
        ax.annotate('', xy=(p[0] + 13 * c, p[1] + 13 * s), xytext=(p[0], p[1]),
                    arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 2.2})
        ax.plot([p[0]], [p[1]], '+', ms=12, mew=2, color=GRIP)
        ax.set_xticks([])
        ax.set_yticks([])
        _atitle(ax, title, y=1.03)
        axb = fig.add_subplot(gs[1, k])
        n = 64
        axb.imshow(bits[:n].reshape(4, 16), cmap='gray_r', vmin=-0.4, vmax=1.3,
                   aspect='equal')
        axb.set_xticks([])
        axb.set_yticks([])
        if k == 0:
            txt = 'the first 64 of its 256 answers\n(black = "first pixel is darker")'
        else:
            dd = int((rr.da[i] != bits).sum())
            txt = f'differs from 1. in {dd} of 256 answers'
        _acaption(axb, txt, y=-0.12)
    fig.text(0.5, 0.955, 'Red arrow: the patch\'s own direction.  Orange: some of the '
             'pixel pairs compared, turned to that direction.', ha='center', fontsize=10.5,
             color=MUTED)
    _save(fig, FEATURES, 'patch-to-bits.svg')


def ratio_test() -> None:
    rr = run()
    fig, ax = plt.subplots(figsize=(8.6, 6.4), facecolor='white')
    ok, bad = rr.correct, ~rr.correct
    ax.scatter(rr.d2[bad], rr.d1[bad], s=26, color=GRIP, alpha=0.75,
               label=f'wrong match ({int(bad.sum())})', zorder=4)
    ax.scatter(rr.d2[ok], rr.d1[ok], s=30, color=SLIDE, alpha=0.85, marker='s',
               label=f'right match ({int(ok.sum())})', zorder=5)
    xs = np.array([0, 62])
    ax.plot(xs, 0.8 * xs, color=INK, lw=1.6, ls='--', label='best = 0.8 × second best')
    ax.plot(xs, xs, color=GRID, lw=1.4, label='best = second best')
    ax.fill_between(xs, 0, 0.8 * xs, color=SLIDE, alpha=0.07)
    _label(ax, 54, 33, 'kept by the\nratio test', size=11, color=SLIDE, weight='bold')
    _label(ax, 18, 38, 'thrown away', size=11, color=GRIP, weight='bold')
    ax.set_xlim(0, 60)
    ax.set_ylim(-1, 56)
    ax.set_xlabel('distance to the second-best match (bits that differ)', fontsize=10)
    ax.set_ylabel('distance to the best match (bits that differ)', fontsize=10)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper left', fontsize=10, frameon=False)
    ax.set_title('Each dot is one label corner and its best match in the scene',
                 fontsize=12, weight='bold', color=INK, pad=12)
    _save(fig, FEATURES, 'ratio-test.svg')


def ransac_homography() -> None:
    rr = run()
    fig = plt.figure(figsize=(14.0, 5.6), facecolor='white')
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    gap = 30
    ox = LABEL_W + gap
    oy = (SCENE_H - LABEL_H) / 2
    ax.imshow(rr.label, cmap='gray', vmin=0, vmax=1.25,
              extent=(-0.5, LABEL_W - 0.5, oy + LABEL_H - 0.5, oy - 0.5))
    ax.imshow(rr.scene, cmap='gray', vmin=0, vmax=1.25,
              extent=(ox - 0.5, ox + SCENE_W - 0.5, SCENE_H - 0.5, -0.5))
    a = rr.kp_a[rr.keep]
    b = rr.kp_b[rr.nn[rr.keep]]
    for k in range(len(a)):
        col, lw, al = (SLIDE, 1.1, 0.9) if rr.inl[k] else (GRIP, 1.6, 1.0)
        ax.plot([a[k, 0], b[k, 0] + ox], [a[k, 1] + oy, b[k, 1]], color=col, lw=lw,
                alpha=al, zorder=5)
    box = np.vstack([rr.box_fit, rr.box_fit[:1]])
    ax.plot(box[:, 0] + ox, box[:, 1], color=LINK, lw=3.0, zorder=6)
    ax.set_xlim(-5, ox + SCENE_W + 5)
    ax.set_ylim(SCENE_H + 40, -30)
    ax.set_aspect('equal')
    ax.axis('off')
    _label(ax, LABEL_W / 2, oy - 14, 'the label, as stored', size=11, weight='bold')
    _label(ax, ox + SCENE_W / 2, -16, 'the camera picture', size=11, weight='bold')
    n_in, n_out = int(rr.inl.sum()), int((~rr.inl).sum())
    ax.text(ox + SCENE_W / 2, SCENE_H + 12,
            f'green: {n_in} matches that agree with one homography   '
            f'red: {n_out} that do not   blue: the label\'s outline, moved by that homography',
            ha='center', va='top', fontsize=10, color=MUTED)
    _save(fig, FEATURES, 'ransac-homography.svg')


# --------------------------------------------------------------------------
# part 2: normals, local shape features and a rough pose for ICP
# --------------------------------------------------------------------------

BRACKET: list[tuple[float, float]] = [(0, 0), (120, 0), (120, 30), (30, 30), (30, 80), (0, 80)]


def outline(corners_: list[tuple[float, float]], step: float) -> Array:
    pts: list[Array] = []
    for a, b in zip(corners_, corners_[1:] + corners_[:1]):
        pa, pb = np.array(a, float), np.array(b, float)
        n = max(1, int(round(float(np.linalg.norm(pb - pa)) / step)))
        for i in range(n):
            pts.append(pa + (pb - pa) * i / n)
    return np.array(pts)


def rot(deg: float) -> Array:
    t = math.radians(deg)
    return np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])


# The same bracket, model and scans as in searching_and_matching.py, so that the
# numbers agree with the rest of the ICP page.
MODEL: Array = outline(BRACKET, 10.0)
MODEL_C: Array = MODEL.mean(0)
BAD_TURN: float = 120.0
SHIFT: tuple[float, float] = (30.0, 20.0)


def scan_of(deg: float, shift: tuple[float, float], seed: int = 1) -> Array:
    fine = outline(BRACKET, 6.0)
    rng = np.random.default_rng(seed)
    return ((fine - MODEL_C) @ rot(deg).T + MODEL_C + np.array(shift)
            + rng.normal(0.0, 0.8, fine.shape))


def best_fit(a: Array, b: Array) -> tuple[Array, Array]:
    ca, cb = a.mean(0), b.mean(0)
    h = (a - ca).T @ (b - cb)
    u, _s, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[1] *= -1
        r = vt.T @ u.T
    return r, cb - r @ ca


def closest(src: Array, dst: Array) -> tuple[NDArray[np.int64], Array]:
    d = np.linalg.norm(src[:, None, :] - dst[None, :, :], axis=2)
    j = d.argmin(1)
    return j, d[np.arange(len(src)), j]


def icp(src: Array, dst: Array, max_iters: int = 80,
        stop: float = 0.001) -> list[tuple[Array, float]]:
    cur = src.copy()
    hist: list[tuple[Array, float]] = []
    for _ in range(max_iters):
        j, gaps = closest(cur, dst)
        hist.append((cur.copy(), float(gaps.mean())))
        if len(hist) > 1 and hist[-2][1] - hist[-1][1] < stop:
            break
        r, t = best_fit(cur, dst[j])
        cur = cur @ r.T + t
    return hist


def normals(pts: Array, k: int = 6) -> Array:
    """For each point, fit a line to its k nearest neighbours (principal component
    analysis) and take the direction at right angles to it."""
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    out = np.zeros_like(pts)
    for i in range(len(pts)):
        nb = pts[np.argsort(d[i])[:k]]
        c = nb - nb.mean(0)
        _w, v = np.linalg.eigh(c.T @ c)
        out[i] = v[:, 0]                       # the direction of least spread
    return out


FEAT_R: float = 45.0          # how far round each point the feature looks, in mm
DIST_BINS: int = 3
ANGLE_BINS: int = 3


def shape_feature(pts: Array, nrm: Array) -> Array:
    """A small local shape feature in the spirit of FPFH: for each point, a
    histogram of (how far away, how differently turned) over its neighbours
    within FEAT_R. The angle is between the two normals, ignoring their sign."""
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    feats = np.zeros((len(pts), DIST_BINS * ANGLE_BINS))
    for i in range(len(pts)):
        nb = np.nonzero((d[i] > 1e-9) & (d[i] < FEAT_R))[0]
        cosang = np.abs(nrm[nb] @ nrm[i]).clip(0, 1)
        ang = np.degrees(np.arccos(cosang))                 # 0 .. 90 degrees
        db = np.minimum((d[i, nb] / FEAT_R * DIST_BINS).astype(int), DIST_BINS - 1)
        ab = np.minimum((ang / 90.0 * ANGLE_BINS).astype(int), ANGLE_BINS - 1)
        hist = np.zeros(DIST_BINS * ANGLE_BINS)
        np.add.at(hist, db * ANGLE_BINS + ab, 1.0)
        feats[i] = hist / max(1.0, hist.sum())
    return feats


def ransac_rigid(a: Array, b: Array, tries: int = 500, limit: float = 5.0,
                 seed: int = 4) -> tuple[Array, Array, NDArray[np.bool_], int]:
    """RANSAC for a rigid move in the plane: two pairs fix a turn and a shift."""
    rng = np.random.default_rng(seed)
    best = np.zeros(len(a), bool)
    best_try = 0
    for t in range(tries):
        i, j = rng.choice(len(a), 2, replace=False)
        # the two pairs must be about the same distance apart in both sets
        la, lb = np.linalg.norm(a[i] - a[j]), np.linalg.norm(b[i] - b[j])
        if la < 20 or abs(la - lb) > 0.1 * la:
            continue
        r, sh = best_fit(a[[i, j]], b[[i, j]])
        inl = np.linalg.norm(a @ r.T + sh - b, axis=1) < limit
        if inl.sum() > best.sum():
            best, best_try = inl, t + 1
    r, sh = best_fit(a[best], b[best])
    return r, sh, best, best_try


class GlobalRun:
    """Normals, features, matches, RANSAC and ICP for the 120-degree bracket."""

    def __init__(self) -> None:
        self.model = MODEL
        self.scan = scan_of(BAD_TURN, SHIFT)
        self.n_model = normals(self.model)
        self.n_scan = normals(self.scan)
        self.f_model = shape_feature(self.model, self.n_model)
        self.f_scan = shape_feature(self.scan, self.n_scan)
        fd = np.linalg.norm(self.f_model[:, None, :] - self.f_scan[None, :, :], axis=2)
        self.match = fd.argmin(1)
        a, b = self.model, self.scan[self.match]
        self.r, self.t, self.inl, self.found_at = ransac_rigid(a, b)
        self.coarse = self.model @ self.r.T + self.t
        self.coarse_turn = math.degrees(math.atan2(self.r[1, 0], self.r[0, 0]))
        self.coarse_gap = float(closest(self.coarse, self.scan)[1].mean())
        self.fine = icp(self.coarse, self.scan)
        rf, tf = best_fit(self.model, self.fine[-1][0])
        self.fine_turn = math.degrees(math.atan2(rf[1, 0], rf[0, 0]))
        self.fine_shift = self.fine[-1][0].mean(0) - self.model.mean(0)
        self.alone = icp(self.model, self.scan)
        ra, _ta = best_fit(self.model, self.alone[-1][0])
        self.alone_turn = math.degrees(math.atan2(ra[1, 0], ra[0, 0]))
        # where each model point really is in the scan, to mark right and wrong matches
        truth = (self.model - MODEL_C) @ rot(BAD_TURN).T + MODEL_C + np.array(SHIFT)
        self.match_err = np.linalg.norm(truth - self.scan[self.match], axis=1)


_GRUN: GlobalRun | None = None


def grun() -> GlobalRun:
    global _GRUN
    if _GRUN is None:
        _GRUN = GlobalRun()
    return _GRUN


def _pts(ax: Axes, p: Array, color: str, size: float = 4.5, z: int = 6,
         alpha: float = 1.0) -> None:
    ax.plot(p[:, 0], p[:, 1], 'o', ms=size, color=color, mew=0, zorder=z, alpha=alpha)


def normals_picture() -> None:
    g = grun()
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 6.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1.0], 'wspace': 0.08})
    ax = axes[0]
    s, n = g.scan, g.n_scan
    lo, hi = s.min(0) - 20, s.max(0) + 20
    _axes(ax, (lo[0], hi[0]), (lo[1], hi[1]))
    _pts(ax, s, MUTED, size=4.0)
    for p, v in zip(s, n):
        ax.plot([p[0], p[0] + 9 * v[0]], [p[1], p[1] + 9 * v[1]], color=LINK, lw=1.3,
                zorder=5)
    _atitle(ax, '1. The scan, with a normal at every point')
    _acaption(ax, 'Each blue stick sits at right angles to the surface near its point.')
    # zoom on one point: its neighbours and the line fitted through them
    ax = axes[1]
    d = np.linalg.norm(s[:, None, :] - s[None, :, :], axis=2)
    # pick a point in the middle of the longest straight edge instead of a corner
    mid = (np.array([60.0, 0.0]) - MODEL_C) @ rot(BAD_TURN).T + MODEL_C + np.array(SHIFT)
    edge_pt = int(np.argmin(np.linalg.norm(s - mid, axis=1)))
    p = s[edge_pt]
    nb = np.argsort(d[edge_pt])[:6]
    _axes(ax, (p[0] - 26, p[0] + 26), (p[1] - 22, p[1] + 22))
    near = np.linalg.norm(s - p, axis=1) < 40
    _pts(ax, s[near], MUTED, size=8.0)
    _pts(ax, s[nb], JOINT, size=11.0, z=7)
    c = s[nb] - s[nb].mean(0)
    _w, v = np.linalg.eigh(c.T @ c)
    along = v[:, 1]
    m = s[nb].mean(0)
    ax.plot([m[0] - 22 * along[0], m[0] + 22 * along[0]],
            [m[1] - 22 * along[1], m[1] + 22 * along[1]], color=INK, lw=1.4, ls='--',
            zorder=5)
    nv = n[edge_pt]
    ax.annotate('', xy=(p[0] + 15 * nv[0], p[1] + 15 * nv[1]), xytext=(p[0], p[1]),
                arrowprops={'arrowstyle': '-|>', 'color': LINK, 'lw': 2.6}, zorder=9)
    ax.plot([p[0]], [p[1]], 'o', ms=13, color=GRIP, mec=INK, zorder=8)
    _atitle(ax, '2. How one normal is found, close up')
    _acaption(ax, 'Red: the point.  Orange: its 5 nearest neighbours.\n'
                  'Dashed: the line that fits them best.  Blue: the normal,\n'
                  'at right angles to that line.')
    _save(fig, ICP_DIR, 'normals.svg')


def local_features_picture() -> None:
    g = grun()
    # three model points: the outer corner, the tip of the long arm, a point on an edge
    picks = [('A: the outer corner', np.array([0.0, 0.0])),
             ('B: the tip of the long arm', np.array([120.0, 30.0])),
             ('C: the middle of the long edge', np.array([60.0, 0.0]))]
    idx = [int(np.argmin(np.linalg.norm(g.model - q, axis=1))) for _n, q in picks]
    fig = plt.figure(figsize=(14.0, 6.2), facecolor='white')
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.8], hspace=0.45, wspace=0.18)
    cols = [JOINT, GRIP, LINK]
    labels = [f'{a}, {b}' for a in ('near', 'middle', 'far')
              for b in ('same way', 'tilted', 'across')]
    for k, ((name, _q), i) in enumerate(zip(picks, idx)):
        ax = fig.add_subplot(gs[0, k])
        _axes(ax, (-50, 170), (-50, 125))
        _pts(ax, g.model, MUTED, size=4.0)
        p = g.model[i]
        ax.add_patch(Circle((p[0], p[1]), FEAT_R, facecolor=cols[k], alpha=0.12,
                            edgecolor=cols[k], lw=1.4))
        ax.plot([p[0]], [p[1]], 'o', ms=11, color=cols[k], mec=INK, zorder=8)
        _atitle(ax, name, y=1.0, size=11)
        axh = fig.add_subplot(gs[1, k])
        axh.bar(range(len(labels)), g.f_model[i], color=cols[k], edgecolor=INK, lw=0.6)
        axh.set_ylim(0, 0.75)
        axh.set_xticks(range(len(labels)))
        axh.set_xticklabels(labels, rotation=55, fontsize=8.5, ha='right', rotation_mode='anchor')
        axh.tick_params(axis='y', labelsize=8)
        for s_ in ('top', 'right'):
            axh.spines[s_].set_visible(False)
        if k == 0:
            axh.set_ylabel('share of neighbours', fontsize=9)
    fig.text(0.5, 0.955, 'The feature of a point counts its neighbours inside the circle '
             '(45 mm) by how far away they are and how their normal is turned',
             ha='center', fontsize=10.5, color=MUTED)
    _save(fig, ICP_DIR, 'local-features.svg')


def feature_matches_picture() -> None:
    g = grun()
    fig, ax = plt.subplots(figsize=(11.0, 7.0), facecolor='white')
    lo = np.minimum(g.model.min(0), g.scan.min(0)) - 15
    hi = np.maximum(g.model.max(0), g.scan.max(0)) + 15
    _axes(ax, (lo[0], hi[0]), (lo[1], hi[1]))
    _pts(ax, g.scan, MUTED, size=4.0)
    _pts(ax, g.model, LINK, size=5.5, z=7)
    b = g.scan[g.match]
    for k in range(len(g.model)):
        if g.inl[k]:
            ax.plot([g.model[k, 0], b[k, 0]], [g.model[k, 1], b[k, 1]], color=SLIDE, lw=1.6,
                    zorder=5)
        else:
            ax.plot([g.model[k, 0], b[k, 0]], [g.model[k, 1], b[k, 1]], color=GRIP, lw=0.8,
                    alpha=0.55, zorder=4)
    _label(ax, g.model[:, 0].mean() - 10, lo[1] + 8, 'blue: the model, where it was drawn',
           color=LINK, size=10)
    ax.set_title(f'Feature matches: green = the {int(g.inl.sum())} that RANSAC keeps, '
                 f'red = the {int((~g.inl).sum())} it throws away', fontsize=12,
                 weight='bold', color=INK)
    _acaption(ax, 'Grey: the scan of the bracket, turned 120 degrees. Every model point '
                  'is joined to the scan point with the most similar feature.', y=0.0)
    _save(fig, ICP_DIR, 'feature-matches.svg')


def coarse_then_fine_picture() -> None:
    g = grun()
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.4), facecolor='white')
    lo = np.minimum(g.model.min(0), g.scan.min(0)) - 12
    hi = np.maximum(g.model.max(0), g.scan.max(0)) + 12
    views = [(g.alone[-1][0], GRIP, '1. ICP alone, from the drawn pose',
              f'stuck after {len(g.alone) - 1} rounds: turned {g.alone_turn:.1f}°,\n'
              f'mean gap {g.alone[-1][1]:.1f} mm'),
             (g.coarse, JOINT, '2. The rough pose from features',
              f'turned {g.coarse_turn:.1f}°, mean gap {g.coarse_gap:.1f} mm'),
             (g.fine[-1][0], SLIDE, '3. ICP started from the rough pose',
              f'{len(g.fine) - 1} rounds: turned {g.fine_turn:.1f}°,\n'
              f'mean gap {g.fine[-1][1]:.1f} mm')]
    for ax, (pts, col, title, cap) in zip(axes, views):
        _axes(ax, (lo[0], hi[0]), (lo[1], hi[1]))
        _pts(ax, g.scan, MUTED, size=3.5)
        _pts(ax, pts, col, size=5.0, z=7)
        _atitle(ax, title, y=1.02)
        _acaption(ax, cap, y=0.0)
    fig.text(0.5, 0.97, 'Grey: the scan, turned 120° from the model. The true answer is '
             'a turn of 120°.', ha='center', fontsize=10.5, color=MUTED)
    _save(fig, ICP_DIR, 'coarse-then-fine.svg')


# --------------------------------------------------------------------------
# numbers quoted in the documents
# --------------------------------------------------------------------------

def ppf_example() -> None:
    """A point pair feature between two points on a box, in 3D."""
    p1, n1 = np.array([0.0, 0.0, 0.05]), np.array([0.0, 0.0, 1.0])     # top face, metres
    p2, n2 = np.array([0.04, 0.0, 0.02]), np.array([1.0, 0.0, 0.0])    # side face
    d = p2 - p1
    dist = float(np.linalg.norm(d))
    du = d / dist

    def ang(a: Array, b: Array) -> float:
        return math.degrees(math.acos(float(np.clip(a @ b, -1, 1))))
    print(f'  PPF: distance {dist * 1000:.1f} mm, angle(n1,d) {ang(n1, du):.1f}, '
          f'angle(n2,d) {ang(n2, du):.1f}, angle(n1,n2) {ang(n1, n2):.1f}')


def print_numbers() -> None:
    rr = run()
    print('image features')
    print(f'  corners: label {len(rr.kp_a)}, scene {len(rr.kp_b)}')
    print(f'  best matches right: {int(rr.correct.sum())} of {len(rr.correct)}')
    print(f'  after ratio 0.8: kept {int(rr.keep.sum())}, of which right '
          f'{int((rr.keep & rr.correct).sum())}, wrong {int((rr.keep & ~rr.correct).sum())}')
    print(f'  thrown away: right {int((~rr.keep & rr.correct).sum())}, '
          f'wrong {int((~rr.keep & ~rr.correct).sum())}')
    print(f'  RANSAC inliers {int(rr.inl.sum())} of {len(rr.inl)}, best found at try '
          f'{rr.found_at}')
    err = np.linalg.norm(rr.box_fit - rr.box_true, axis=1)
    print(f'  label corner error (px): {np.round(err, 2)}  max {err.max():.2f}')
    w = rr.inl.mean()
    if w < 1:
        print(f'  inlier share {w:.2f}; tries for 99% with 4 points: '
              f'{math.log(0.01) / math.log(1 - w ** 4):.1f}')
    for name, (x, y) in _shift_spots(rr.label):
        c = shift_cost(rr.label, (x, y))
        low = float(np.sort(np.delete(c.ravel(), c.size // 2))[0])
        print(f'  shift test {name} at ({x},{y}): smallest {low:.4f}, largest {c.max():.4f}')
    good = [i for i in range(len(rr.kp_a)) if rr.correct[i] and rr.keep[i]]
    i = good[0]
    j = int(rr.nn[i])
    other = int(np.argsort(rr.dist[i])[len(rr.kp_b) // 2])
    print(f'  bits example: corner {i} at {rr.kp_a[i]}, match {rr.kp_b[j]}, '
          f'd1 {rr.d1[i]:.0f}, d2 {rr.d2[i]:.0f}, ratio {rr.ratio[i]:.2f}, '
          f'other {int(rr.dist[i, other])}')
    print(f'  angles: label {math.degrees(rr.ang_a[i]):.1f}, scene '
          f'{math.degrees(rr.ang_b[j]):.1f}')
    ht = rr.h_true
    print('  true H\n', np.round(ht, 4))
    print('  fitted H\n', np.round(rr.h_fit, 4))
    ppf_example()
    g = grun()
    print('global registration')
    print(f'  model {len(g.model)} pts, scan {len(g.scan)} pts')
    print(f'  feature matches within 5 mm of true: {int((g.match_err < 5).sum())} of '
          f'{len(g.match_err)}')
    print(f'  RANSAC inliers {int(g.inl.sum())}, found at try {g.found_at}')
    print(f'  coarse turn {g.coarse_turn:.2f}, gap {g.coarse_gap:.2f}')
    print(f'  fine: rounds {len(g.fine) - 1}, turn {g.fine_turn:.2f}, gap '
          f'{g.fine[-1][1]:.2f}, centre shift {np.round(g.fine_shift, 1)}')
    print(f'  alone: rounds {len(g.alone) - 1}, turn {g.alone_turn:.2f}, gap '
          f'{g.alone[-1][1]:.2f}')
    for nm, q in (('A', (0, 0)), ('B', (120, 30)), ('C', (60, 0))):
        i = int(np.argmin(np.linalg.norm(g.model - np.array(q, float), axis=1)))
        print(f'  feature {nm}: {np.round(g.f_model[i], 2)}')


def main() -> None:
    global PNG_DIR
    if '--numbers' in sys.argv:
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    shift_test()
    patch_to_bits()
    ratio_test()
    ransac_homography()
    normals_picture()
    local_features_picture()
    feature_matches_picture()
    coarse_then_fine_picture()


if __name__ == '__main__':
    main()
