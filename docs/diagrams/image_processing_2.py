"""Generate the diagrams for the second half of
docs/06_programming-techniques/05_image-and-point-cloud-processing/.

This covers 04_edges-and-contours and 05_clustering. Each document's pictures go
to a folder named after it, under docs/images/image-and-point-cloud-processing/.

Run with:  pixi run python ../docs/diagrams/image_processing_2.py
Add --png <dir> to also write PNG copies for checking.

Every result drawn here is computed for real with NumPy: the gradients of the
small drawn picture, each Canny step, the traced outlines and their polygons,
connected components, Euclidean clustering, DBSCAN and voxel downsampling. The
numbers in the two documents come from these same functions (run
`python3 image_processing_2.py --numbers` to print them).
"""

import pathlib
import sys
from collections import deque

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from matplotlib.path import Path  # noqa: E402
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


def _image_axes(ax: Axes, title: str, subtitle: str = '') -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_title(title, fontsize=11, color=INK, weight='bold', pad=8)
    if subtitle:
        ax.text(0.5, -0.04, subtitle, transform=ax.transAxes, fontsize=9.5,
                ha='center', va='top', color=MUTED)


def _plot_axes(ax: Axes, title: str, subtitle: str = '') -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_title(title, fontsize=11, color=INK, weight='bold', pad=8)
    if subtitle:
        ax.text(0.5, -0.04, subtitle, transform=ax.transAxes, fontsize=9.5,
                ha='center', va='top', color=MUTED)


# --------------------------------------------------------------------------
# edges: the computations
# --------------------------------------------------------------------------

SOBEL_X: NDArray[np.float64] = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
SOBEL_Y: NDArray[np.float64] = SOBEL_X.T.copy()     # rows go down, so +y is down


def small_picture() -> NDArray[np.float64]:
    """An 8 x 8 grey picture: a bright 4 x 4 square (200) on a dark table (20)."""
    img = np.full((8, 8), 20.0)
    img[2:6, 2:6] = 200.0
    return img


def correlate3(img: NDArray[np.float64], k: NDArray[np.float64]) -> NDArray[np.float64]:
    """Slide a 3 x 3 kernel over the picture. Border pixels copy their neighbour."""
    p = np.pad(img, 1, mode='edge')
    out = np.zeros_like(img)
    for dr in range(3):
        for dc in range(3):
            out += k[dr, dc] * p[dr:dr + img.shape[0], dc:dc + img.shape[1]]
    return out


def gaussian_blur(img: NDArray[np.float64], sigma: float) -> NDArray[np.float64]:
    r = int(np.ceil(3 * sigma))
    x = np.arange(-r, r + 1)
    g = np.exp(-x ** 2 / (2 * sigma ** 2))
    g /= g.sum()
    p = np.pad(img, r, mode='edge')
    tmp = np.zeros((p.shape[0], img.shape[1]))
    for i, w in enumerate(g):
        tmp += w * p[:, i:i + img.shape[1]]
    out = np.zeros_like(img)
    for i, w in enumerate(g):
        out += w * tmp[i:i + img.shape[0], :]
    return out


def polygon_mask(shape: tuple[int, int], poly: NDArray[np.float64]) -> NDArray[np.bool_]:
    """True for every pixel whose centre lies inside the polygon (x, y) corners."""
    rows, cols = shape
    yy, xx = np.mgrid[0:rows, 0:cols]
    pts = np.column_stack([xx.ravel() + 0.5, yy.ravel() + 0.5])
    return Path(poly).contains_points(pts).reshape(shape)


def regular_polygon(cx: float, cy: float, r: float, n: int, turn: float) -> NDArray[np.float64]:
    a = turn + np.arange(n) * 2 * np.pi / n
    return np.column_stack([cx + r * np.cos(a), cy + r * np.sin(a)])


def canny_scene() -> NDArray[np.float64]:
    """A 64 x 96 grey picture: a triangle and a turned square on a table, with noise."""
    rng = np.random.default_rng(3)
    img = np.full((64, 96), 60.0)
    img[polygon_mask(img.shape, regular_polygon(26, 33, 20, 3, -np.pi / 2))] = 130.0
    img[polygon_mask(img.shape, regular_polygon(70, 32, 20, 4, np.pi / 7))] = 200.0
    img += rng.normal(0, 30, img.shape)
    return img


CANNY_SIGMA: float = 1.0
CANNY_LOW: float = 80.0
CANNY_HIGH: float = 200.0


def canny(img: NDArray[np.float64], sigma: float, low: float, high: float
          ) -> dict[str, NDArray]:
    """The four Canny steps, each kept so it can be drawn."""
    blur = gaussian_blur(img, sigma)
    gx = correlate3(blur, SOBEL_X)
    gy = correlate3(blur, SOBEL_Y)
    mag = np.hypot(gx, gy)
    ang = (np.degrees(np.arctan2(gy, gx)) + 180.0) % 180.0
    # thin: keep a pixel only if it is at least as strong as both neighbours
    # across the edge (the gradient direction, rounded to 0, 45, 90 or 135 deg).
    thin = np.zeros_like(mag)
    rows, cols = mag.shape
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            a = ang[r, c]
            if a < 22.5 or a >= 157.5:
                n1, n2 = mag[r, c - 1], mag[r, c + 1]
            elif a < 67.5:
                n1, n2 = mag[r - 1, c - 1], mag[r + 1, c + 1]
            elif a < 112.5:
                n1, n2 = mag[r - 1, c], mag[r + 1, c]
            else:
                n1, n2 = mag[r - 1, c + 1], mag[r + 1, c - 1]
            if mag[r, c] >= n1 and mag[r, c] >= n2:
                thin[r, c] = mag[r, c]
    strong = thin >= high
    weak = (thin >= low) & ~strong
    # hysteresis: a weak pixel survives only if it touches a strong chain
    keep = strong.copy()
    q = deque(zip(*np.nonzero(strong)))
    while q:
        r, c = q.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols and weak[rr, cc] and not keep[rr, cc]:
                    keep[rr, cc] = True
                    q.append((rr, cc))
    return {'blur': blur, 'mag': mag, 'thin': thin, 'strong': strong, 'weak': weak,
            'edges': keep}


# 8 neighbours in clockwise order on screen (rows go down): E, SE, S, SW, W, NW, N, NE
NEIGH: list[tuple[int, int]] = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1),
                                (-1, 0), (-1, 1)]


def trace_outline(mask: NDArray[np.bool_]) -> NDArray[np.int64]:
    """Moore-neighbour tracing: walk round the outside pixels of one blob, clockwise.

    Returns (row, col) of each outline pixel in walking order.
    """
    rows, cols = mask.shape
    fg = np.argwhere(mask)
    start = tuple(fg[0])                         # top-most, then left-most pixel
    back = 4                                     # we "arrived" from the west
    path = [start]
    cur = start
    first_move: tuple[tuple[int, int], int] | None = None
    while True:
        found = False
        for k in range(1, 9):
            d = (back + k) % 8
            r, c = cur[0] + NEIGH[d][0], cur[1] + NEIGH[d][1]
            if 0 <= r < rows and 0 <= c < cols and mask[r, c]:
                nxt = (r, c)
                back = (d + 4) % 8               # direction pointing back to cur
                found = True
                break
        if not found:                            # a single lone pixel
            break
        if first_move is None:
            first_move = (nxt, back)
        elif cur == start and (nxt, back) == first_move:
            break
        cur = nxt
        path.append(cur)
    return np.array(path[:-1])


def _rdp_open(pts: NDArray[np.float64], eps: float) -> list[int]:
    a, b = pts[0], pts[-1]
    d = b - a
    n = np.hypot(*d)
    if n == 0:
        dist = np.hypot(*(pts - a).T)
    else:
        dist = np.abs(d[0] * (pts[:, 1] - a[1]) - d[1] * (pts[:, 0] - a[0])) / n
    i = int(np.argmax(dist))
    if dist[i] > eps:
        left = _rdp_open(pts[:i + 1], eps)
        right = _rdp_open(pts[i:], eps)
        return left[:-1] + [j + i for j in right]
    return [0, len(pts) - 1]


def simplify_closed(pts: NDArray[np.float64], eps: float) -> NDArray[np.float64]:
    """Ramer-Douglas-Peucker on a closed outline.

    Start the loop at the point farthest from the middle (almost always a corner),
    split it again at the point farthest from that, simplify both halves, and
    join them.
    """
    pts = np.roll(pts, -int(np.argmax(np.hypot(*(pts - pts.mean(axis=0)).T))), axis=0)
    far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
    loop = np.vstack([pts, pts[:1]])
    first = _rdp_open(loop[:far + 1], eps)
    second = _rdp_open(loop[far:], eps)
    idx = first[:-1] + [j + far for j in second][:-1]
    return pts[idx]


def perimeter(poly: NDArray[np.float64]) -> float:
    return float(np.hypot(*(np.roll(poly, -1, axis=0) - poly).T).sum())


def shoelace(poly: NDArray[np.float64]) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def fit_circle(pts: NDArray[np.float64]) -> tuple[float, float, float]:
    """Least-squares circle: solve x^2 + y^2 + D x + E y + F = 0 for D, E, F."""
    x, y = pts[:, 0], pts[:, 1]
    a = np.column_stack([x, y, np.ones_like(x)])
    b = -(x ** 2 + y ** 2)
    d, e, f = np.linalg.lstsq(a, b, rcond=None)[0]
    cx, cy = -d / 2, -e / 2
    return float(cx), float(cy), float(np.sqrt(cx ** 2 + cy ** 2 - f))


SHAPE_SIZE: int = 60


def four_shapes() -> list[tuple[str, NDArray[np.bool_]]]:
    s = (SHAPE_SIZE, SHAPE_SIZE)
    c = SHAPE_SIZE / 2
    tri = polygon_mask(s, regular_polygon(c, c + 4, 26, 3, -np.pi / 2))
    sq = polygon_mask(s, regular_polygon(c, c, 25, 4, np.pi / 9))
    hexa = polygon_mask(s, regular_polygon(c, c, 25, 6, 0.3))
    yy, xx = np.mgrid[0:SHAPE_SIZE, 0:SHAPE_SIZE]
    circ = (xx + 0.5 - c) ** 2 + (yy + 0.5 - c) ** 2 <= 23 ** 2
    return [('triangle', tri), ('square', sq), ('hexagon', hexa), ('circle', circ)]


def describe_shape(mask: NDArray[np.bool_], frac: float = 0.02) -> dict:
    outline = trace_outline(mask)
    pts = outline[:, ::-1].astype(float) + 0.5      # (x, y) pixel centres
    eps = frac * perimeter(pts)
    poly = simplify_closed(pts, eps)
    area = float(mask.sum())
    circ = 4 * np.pi * shoelace(pts) / perimeter(pts) ** 2
    return {'outline': pts, 'poly': poly, 'eps': eps, 'corners': len(poly),
            'area': area, 'perimeter': perimeter(pts), 'circularity': circ}


# --------------------------------------------------------------------------
# clustering: the computations
# --------------------------------------------------------------------------

def small_mask() -> NDArray[np.int64]:
    """A 7 x 10 mask with blobs; two of them touch only at one corner."""
    rows = [
        '1100000000',
        '1100001110',
        '0000001110',
        '0011000000',
        '0011100011',
        '0000010011',
        '0000001000',
    ]
    return np.array([[int(ch) for ch in r] for r in rows])


def label_components(mask: NDArray, eight: bool) -> NDArray[np.int64]:
    """Flood fill each unlabelled foreground pixel. Labels start at 1."""
    steps = NEIGH if eight else [(0, 1), (1, 0), (0, -1), (-1, 0)]
    labels = np.zeros(mask.shape, int)
    nxt = 0
    for r, c in np.argwhere(mask):
        if labels[r, c]:
            continue
        nxt += 1
        labels[r, c] = nxt
        q = deque([(r, c)])
        while q:
            a, b = q.popleft()
            for dr, dc in steps:
                aa, bb = a + dr, b + dc
                if (0 <= aa < mask.shape[0] and 0 <= bb < mask.shape[1]
                        and mask[aa, bb] and not labels[aa, bb]):
                    labels[aa, bb] = nxt
                    q.append((aa, bb))
    return labels


def neighbours_within(pts: NDArray[np.float64], radius: float) -> list[NDArray[np.int64]]:
    """Brute-force radius search: for each point, the indices within `radius`."""
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    return [np.nonzero(row <= radius)[0] for row in d]


def euclidean_clusters(pts: NDArray[np.float64], tol: float, min_size: int
                       ) -> NDArray[np.int64]:
    """Grow each cluster through every point within `tol`. Small ones become -1."""
    nb = neighbours_within(pts, tol)
    labels = np.full(len(pts), -2)
    nxt = 0
    for i in range(len(pts)):
        if labels[i] != -2:
            continue
        labels[i] = nxt
        q = deque([i])
        while q:
            j = q.popleft()
            for k in nb[j]:
                if labels[k] == -2:
                    labels[k] = nxt
                    q.append(k)
        nxt += 1
    # throw away clusters below the minimum size, then renumber by size
    out = np.full(len(pts), -1)
    sizes = [(np.sum(labels == c), c) for c in range(nxt)]
    kept = [c for n, c in sorted(sizes, reverse=True) if n >= min_size]
    for new, c in enumerate(kept):
        out[labels == c] = new
    return out


def dbscan(pts: NDArray[np.float64], eps: float, min_pts: int
           ) -> tuple[NDArray[np.int64], NDArray[np.bool_]]:
    """DBSCAN. Returns labels (-1 is noise) and which points are core points.

    A point is core when at least `min_pts` points (itself included) lie within
    `eps`. Clusters grow only through core points.
    """
    nb = neighbours_within(pts, eps)
    core = np.array([len(n) >= min_pts for n in nb])
    labels = np.full(len(pts), -1)
    nxt = 0
    for i in range(len(pts)):
        if not core[i] or labels[i] != -1:
            continue
        labels[i] = nxt
        q = deque([i])
        while q:
            j = q.popleft()
            for k in nb[j]:
                if labels[k] == -1:
                    labels[k] = nxt
                    if core[k]:
                        q.append(k)
        nxt += 1
    return labels, core


def table_points() -> NDArray[np.float64]:
    """Top-down points (mm) left on a table after the table plane was removed.

    A round cup, a box, a small block, and some scattered speckle.
    """
    rng = np.random.default_rng(7)
    step = 6.0

    def fill(inside, x0, x1, y0, y1) -> NDArray[np.float64]:
        xs, ys = np.meshgrid(np.arange(x0, x1, step), np.arange(y0, y1, step))
        p = np.column_stack([xs.ravel(), ys.ravel()])
        p = p[[inside(x, y) for x, y in p]]
        return p + rng.normal(0, 1.2, p.shape)

    cup = fill(lambda x, y: (x - 70) ** 2 + (y - 150) ** 2 <= 38 ** 2, 30, 110, 110, 190)
    box = fill(lambda x, y: True, 150, 240, 120, 175)
    block = fill(lambda x, y: True, 110, 145, 30, 65)
    speckle = rng.uniform([10, 10], [260, 200], (14, 2))
    return np.vstack([cup, box, block, speckle])


def bridge_points() -> NDArray[np.float64]:
    """Two blocks 30 mm apart with a thin line of stray points between them."""
    rng = np.random.default_rng(11)
    step = 6.0
    xs, ys = np.meshgrid(np.arange(0, 48, step), np.arange(0, 48, step))
    a = np.column_stack([xs.ravel(), ys.ravel()]) + rng.normal(0, 1.0, (xs.size, 2))
    b = a + np.array([48 + 30, 0])
    line = np.column_stack([np.linspace(52, 74, 4), np.full(4, 22.0)])
    return np.vstack([a, b, line])


def dense_cloud() -> NDArray[np.float64]:
    """A dense top-down scan of a mug and a box, in mm, for voxel downsampling."""
    rng = np.random.default_rng(5)
    n = 1400
    ang = rng.uniform(0, 2 * np.pi, n)
    rad = 30 * np.sqrt(rng.uniform(0, 1, n))
    mug = np.column_stack([40 + rad * np.cos(ang), 45 + rad * np.sin(ang)])
    box = rng.uniform([90, 20], [150, 70], (1600, 2))
    return np.vstack([mug, box])


def voxel_downsample(pts: NDArray[np.float64], size: float
                     ) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """One point per occupied cell: the average of the points that fell in it."""
    cells = np.floor(pts / size).astype(int)
    keys, inv = np.unique(cells, axis=0, return_inverse=True)
    inv = inv.ravel()
    out = np.zeros((len(keys), pts.shape[1]))
    np.add.at(out, inv, pts)
    counts = np.bincount(inv)
    return out / counts[:, None], keys


# --------------------------------------------------------------------------
# diagrams for 04_edges-and-contours
# --------------------------------------------------------------------------

def gradient_arrows() -> None:
    """The 8 x 8 picture, with the Sobel gradient drawn as an arrow at each pixel."""
    img = small_picture()
    gx = correlate3(img, SOBEL_X)
    gy = correlate3(img, SOBEL_Y)
    mag = np.hypot(gx, gy)
    fig, (a1, a2) = _panels(2, (11.5, 5.6))
    for ax in (a1, a2):
        ax.imshow(img, cmap='gray', vmin=0, vmax=255)
        ax.set_xticks(np.arange(8))
        ax.set_yticks(np.arange(8))
        ax.tick_params(labelsize=8, colors=MUTED, length=0)
        for s in ax.spines.values():
            s.set_color(GRID)
    for r in range(8):
        for c in range(8):
            v = int(img[r, c])
            a1.text(c, r, str(v), ha='center', va='center', fontsize=10,
                    color='white' if v < 100 else INK)
    a1.add_patch(Rectangle((0.5, 2.5), 3, 1, fill=False, edgecolor=JOINT, lw=2.4))
    a1.set_title('The picture: brightness of each pixel', fontsize=11, color=INK,
                 weight='bold', pad=8)
    a1.text(3.5, 8.3, 'orange: the 3 x 3 patch used for pixel (row 3, column 1)',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    scale = 0.45 / mag.max()
    for r in range(8):
        for c in range(8):
            if mag[r, c] < 1:
                continue
            dx, dy = gx[r, c] * scale, gy[r, c] * scale
            a2.annotate('', xy=(c + dx, r + dy), xytext=(c - dx, r - dy),
                        arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.8,
                                    'shrinkA': 0, 'shrinkB': 0})
    a2.set_title('The gradient: arrows point from dark to bright', fontsize=11,
                 color=INK, weight='bold', pad=8)
    a2.text(3.5, 8.3, 'longer arrow = sharper change; flat areas get no arrow',
            ha='center', va='top', fontsize=9.5, color=MUTED)
    fig.tight_layout()
    _save(fig, EDGES, 'gradient-arrows.svg')


def canny_steps() -> None:
    img = canny_scene()
    res = canny(img, sigma=CANNY_SIGMA, low=CANNY_LOW, high=CANNY_HIGH)
    naive = res['mag'] >= CANNY_LOW
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.9), facecolor='white')
    axes[0].imshow(img, cmap='gray', vmin=0, vmax=255)
    _image_axes(axes[0], '1. Noisy picture', 'a triangle and a square on a table')
    axes[1].imshow(res['mag'], cmap='magma')
    _image_axes(axes[1], '2. Blur, then gradient size',
                f'one threshold of {CANNY_LOW:.0f} keeps {int(naive.sum())} px')
    axes[2].imshow(res['thin'] >= CANNY_LOW, cmap='gray_r')
    _image_axes(axes[2], '3. Thin to the ridge',
                f'{int((res["thin"] >= CANNY_LOW).sum())} px above {CANNY_LOW:.0f} remain')
    rgb = np.ones(img.shape + (3,))
    weak_dropped = res['weak'] & ~res['edges']
    rgb[weak_dropped] = matplotlib.colors.to_rgb(GRID)
    rgb[res['edges'] & ~res['strong']] = matplotlib.colors.to_rgb(LINK)
    rgb[res['strong']] = matplotlib.colors.to_rgb(INK)
    axes[3].imshow(rgb)
    _image_axes(axes[3], '4. Keep strong + connected weak',
                f'{int(res["edges"].sum())} px; blue = weak kept, grey = dropped')
    fig.tight_layout()
    _save(fig, EDGES, 'canny-steps.svg')


def outline_to_polygon() -> None:
    shapes = dict(four_shapes())
    mask = shapes['hexagon']
    d = describe_shape(mask)
    fig, (a1, a2, a3) = _panels(3, (13.5, 5.0))
    a1.imshow(mask, cmap='Greys', vmin=0, vmax=2.2, extent=(0, SHAPE_SIZE, SHAPE_SIZE, 0))
    _image_axes(a1, '1. The mask', f'{int(d["area"])} pixels are "object"')
    a2.imshow(mask, cmap='Greys', vmin=0, vmax=4, extent=(0, SHAPE_SIZE, SHAPE_SIZE, 0))
    o = d['outline']
    a2.plot(np.r_[o[:, 0], o[:1, 0]], np.r_[o[:, 1], o[:1, 1]], color=LINK, lw=1.4)
    a2.plot(o[0, 0], o[0, 1], 'o', color=GRIP, ms=7, zorder=5)
    a2.text(o[0, 0] + 1.5, o[0, 1] - 2.0, 'start', color=GRIP, fontsize=9.5, va='bottom')
    _image_axes(a2, '2. The traced outline (contour)',
                f'{len(o)} outline points, walked clockwise')
    a3.imshow(mask, cmap='Greys', vmin=0, vmax=4, extent=(0, SHAPE_SIZE, SHAPE_SIZE, 0))
    a3.plot(np.r_[o[:, 0], o[:1, 0]], np.r_[o[:, 1], o[:1, 1]], color=LINK_PALE, lw=1.2)
    p = d['poly']
    a3.plot(np.r_[p[:, 0], p[:1, 0]], np.r_[p[:, 1], p[:1, 1]], color=WRIST, lw=2.2)
    a3.plot(p[:, 0], p[:, 1], 'o', color=WRIST, ms=7)
    _image_axes(a3, '3. The simplified polygon',
                f'{d["corners"]} corners kept (tolerance {d["eps"]:.1f} px)')
    fig.tight_layout()
    _save(fig, EDGES, 'outline-to-polygon.svg')


def counting_corners() -> None:
    fig, axes = _panels(4, (14, 4.4))
    for ax, (name, mask) in zip(axes, four_shapes()):
        d = describe_shape(mask)
        ax.imshow(mask, cmap='Greys', vmin=0, vmax=4, extent=(0, SHAPE_SIZE, SHAPE_SIZE, 0))
        p = d['poly']
        ax.plot(np.r_[p[:, 0], p[:1, 0]], np.r_[p[:, 1], p[:1, 1]], color=WRIST, lw=2)
        ax.plot(p[:, 0], p[:, 1], 'o', color=WRIST, ms=6)
        if name == 'circle':
            cx, cy, r = fit_circle(d['outline'])
            ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor=LINK, lw=1.6, ls='--'))
        sub = f'roundness {d["circularity"]:.2f}'
        if name == 'circle':
            sub += f'; dashed: fitted circle, r = {r:.1f} px'
        _image_axes(ax, f'{name}: {d["corners"]} corners', sub)
    fig.tight_layout()
    _save(fig, EDGES, 'counting-corners.svg')


# --------------------------------------------------------------------------
# diagrams for 05_clustering
# --------------------------------------------------------------------------

def _draw_labels(ax: Axes, mask: NDArray, labels: NDArray, title: str, sub: str) -> None:
    rows, cols = mask.shape
    for r in range(rows):
        for c in range(cols):
            lab = labels[r, c]
            face = 'white' if lab == 0 else CLUSTER_COLOURS[(lab - 1) % len(CLUSTER_COLOURS)]
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=face, edgecolor=GRID, lw=1))
            if lab:
                ax.text(c + 0.5, r + 0.5, str(lab), ha='center', va='center',
                        color='white', fontsize=11, weight='bold')
    ax.set_xlim(0, cols)
    ax.set_ylim(rows, 0)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=11, color=INK, weight='bold', pad=8)
    ax.text(cols / 2, rows + 0.4, sub, ha='center', va='top', fontsize=9.5, color=MUTED)


def connected_components_picture() -> None:
    m = small_mask()
    l4 = label_components(m, eight=False)
    l8 = label_components(m, eight=True)
    fig, (a1, a2) = _panels(2, (12, 4.6))
    _draw_labels(a1, m, l4, 'Four neighbours (up, down, left, right)',
                 f'{l4.max()} objects: corner touches do not join')
    _draw_labels(a2, m, l8, 'Eight neighbours (diagonals too)',
                 f'{l8.max()} objects: corner touches join')
    fig.tight_layout()
    _save(fig, CLUSTER, 'connected-components.svg')


def _table_background(ax: Axes, w: float, h: float) -> None:
    ax.add_patch(Rectangle((0, 0), w, h, facecolor=TABLE, edgecolor='none', alpha=0.45,
                           zorder=0))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)


def euclidean_picture() -> None:
    pts = table_points()
    tol, min_size = 10.0, 10
    labels = euclidean_clusters(pts, tol, min_size)
    fig, (a1, a2) = _panels(2, (13, 5.2))
    for ax in (a1, a2):
        _table_background(ax, 270, 210)
    a1.scatter(pts[:, 0], pts[:, 1], s=9, color=MUTED, zorder=2)
    # show the tolerance circle round a few points of the block
    blk = np.nonzero((pts[:, 0] > 108) & (pts[:, 0] < 147) & (pts[:, 1] < 70))[0][:3]
    for i in blk:
        a1.add_patch(Circle(pts[i], tol, fill=False, edgecolor=GRIP, lw=1.2, zorder=3))
    a1.annotate(f'circle of radius {tol:.0f} mm:\nevery point inside joins',
                xy=(pts[blk[0], 0] - 4, pts[blk[0], 1] + 4), xytext=(20, 75),
                fontsize=9.5, color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    _plot_axes(a1, 'Before: one cloud of points', f'{len(pts)} points seen from above')
    for c in range(labels.max() + 1):
        sel = labels == c
        a2.scatter(pts[sel, 0], pts[sel, 1], s=9, color=CLUSTER_COLOURS[c], zorder=2)
        cx, cy = pts[sel].mean(axis=0)
        a2.text(cx, cy, f'{sel.sum()}', fontsize=10, weight='bold', color='white',
                ha='center', va='center', zorder=4,
                bbox={'boxstyle': 'round,pad=0.25', 'facecolor': CLUSTER_COLOURS[c],
                      'edgecolor': 'none'})
    noise = labels == -1
    a2.scatter(pts[noise, 0], pts[noise, 1], s=22, marker='x', color=INK, zorder=3,
               lw=1.3)
    _plot_axes(a2, f'After: {labels.max() + 1} clusters',
               f'{noise.sum()} stray points in clusters smaller than {min_size} are dropped (x)')
    fig.tight_layout()
    _save(fig, CLUSTER, 'euclidean-clusters.svg')


def dbscan_picture() -> None:
    pts = table_points()
    eps, min_pts = 10.0, 5
    labels, core = dbscan(pts, eps, min_pts)
    # number the clusters largest first, so the colours match the Euclidean picture
    order = sorted(range(labels.max() + 1), key=lambda c: -np.sum(labels == c))
    labels = np.array([order.index(v) if v >= 0 else -1 for v in labels])
    fig, ax = plt.subplots(figsize=(8.5, 6.4), facecolor='white')
    _table_background(ax, 270, 210)
    for c in range(labels.max() + 1):
        sel = (labels == c) & core
        ax.scatter(pts[sel, 0], pts[sel, 1], s=12, color=CLUSTER_COLOURS[c], zorder=2)
        sel = (labels == c) & ~core
        ax.scatter(pts[sel, 0], pts[sel, 1], s=26, facecolor='white',
                   edgecolor=CLUSTER_COLOURS[c], lw=1.4, zorder=3)
    noise = labels == -1
    ax.scatter(pts[noise, 0], pts[noise, 1], s=28, marker='x', color=INK, lw=1.4, zorder=3)
    # one core point with its eps circle
    i = int(np.nonzero(core & (labels == 0))[0][0])
    ax.add_patch(Circle(pts[i], eps, fill=False, edgecolor=GRIP, lw=1.3, zorder=4))
    ax.annotate(f'radius {eps:.0f} mm holds at least {min_pts} points:\na core point',
                xy=(pts[i, 0] + 2, pts[i, 1] - 7), xytext=(160, 60), fontsize=9.5,
                color=GRIP, arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    ax.scatter([], [], s=12, color=MUTED, label=f'core point ({core.sum()})')
    ax.scatter([], [], s=26, facecolor='white', edgecolor=MUTED, lw=1.4,
               label=f'border point ({int(((labels >= 0) & ~core).sum())})')
    ax.scatter([], [], s=28, marker='x', color=INK, label=f'noise ({noise.sum()})')
    ax.legend(loc='upper right', fontsize=9.5, frameon=True, framealpha=0.95)
    _plot_axes(ax, f'DBSCAN finds {labels.max() + 1} clusters and marks noise', '')
    fig.tight_layout()
    _save(fig, CLUSTER, 'dbscan-core-border-noise.svg')


def bridge_picture() -> None:
    pts = bridge_points()
    tol = 10.0
    eu = euclidean_clusters(pts, tol, 1)
    db, core = dbscan(pts, tol, 5)
    fig, (a1, a2) = _panels(2, (13, 3.9))
    for ax, labels, title in ((a1, eu, 'Euclidean clustering'), (a2, db, 'DBSCAN')):
        for c in range(labels.max() + 1):
            sel = labels == c
            ax.scatter(pts[sel, 0], pts[sel, 1], s=18, color=CLUSTER_COLOURS[c], zorder=2)
        noise = labels == -1
        ax.scatter(pts[noise, 0], pts[noise, 1], s=34, marker='x', color=INK, lw=1.4,
                   zorder=3)
        ax.set_xlim(-8, 134)
        ax.set_ylim(-16, 54)
        n = labels.max() + 1
        _plot_axes(ax, f'{title}: {n} cluster{"s" if n > 1 else ""}', '')
    a1.text(63, -8, 'the stray line chains the two blocks together', ha='center',
            va='top', fontsize=9.5, color=MUTED)
    a2.text(63, -8, 'the stray points have too few neighbours to carry the chain', ha='center',
            va='top', fontsize=9.5, color=MUTED)
    fig.tight_layout()
    _save(fig, CLUSTER, 'stray-points-bridge.svg')


def voxel_picture() -> None:
    pts = dense_cloud()
    size = 10.0
    down, keys = voxel_downsample(pts, size)
    fig, (a1, a2) = _panels(2, (13, 3.9))
    for ax in (a1, a2):
        ax.set_xlim(0, 160)
        ax.set_ylim(10, 80)
    a1.scatter(pts[:, 0], pts[:, 1], s=2, color=LINK, zorder=2)
    _plot_axes(a1, f'Before: {len(pts)} points', 'a dense scan of a mug and a box')
    for x in np.arange(0, 161, size):
        a2.plot([x, x], [10, 80], color=GRID, lw=0.8, zorder=1)
    for y in np.arange(10, 81, size):
        a2.plot([0, 160], [y, y], color=GRID, lw=0.8, zorder=1)
    for kx, ky in keys:
        a2.add_patch(Rectangle((kx * size, ky * size), size, size, facecolor=LINK_PALE,
                               edgecolor='none', zorder=0))
    a2.scatter(down[:, 0], down[:, 1], s=16, color=LINK, zorder=3)
    _plot_axes(a2, f'After: {len(down)} points',
               f'one average point per occupied {size:.0f} mm cell')
    fig.tight_layout()
    _save(fig, CLUSTER, 'voxel-downsampling.svg')


# --------------------------------------------------------------------------
# the numbers the documents quote
# --------------------------------------------------------------------------

def print_numbers() -> None:
    np.set_printoptions(linewidth=140)
    img = small_picture()
    gx, gy = correlate3(img, SOBEL_X), correlate3(img, SOBEL_Y)
    print('small picture\n', img.astype(int))
    for rc in [(3, 1), (3, 2), (3, 3), (2, 2), (0, 0), (1, 1)]:
        g = np.hypot(gx[rc], gy[rc])
        ang = np.degrees(np.arctan2(gy[rc], gx[rc]))
        print(f'pixel {rc}: gx={gx[rc]:.0f} gy={gy[rc]:.0f} mag={g:.1f} angle={ang:.1f}')
    res = canny(canny_scene(), CANNY_SIGMA, CANNY_LOW, CANNY_HIGH)
    print('canny: naive>=low', int((res['mag'] >= CANNY_LOW).sum()), 'thin>=low', int((res['thin'] >= CANNY_LOW).sum()),
          'strong', int(res['strong'].sum()), 'weak', int(res['weak'].sum()),
          'final', int(res['edges'].sum()),
          'weak kept', int((res['edges'] & ~res['strong']).sum()),
          'mag max', round(float(res['mag'].max()), 1))
    for name, mask in four_shapes():
        d = describe_shape(mask)
        extra = ''
        if name == 'circle':
            extra = ' circle fit (cx, cy, r) = ' + str(tuple(round(v, 2) for v in fit_circle(d['outline'])))
        print(f'{name}: area={d["area"]:.0f} outline pts={len(d["outline"])} '
              f'perimeter={d["perimeter"]:.1f} eps={d["eps"]:.2f} corners={d["corners"]} '
              f'roundness={d["circularity"]:.3f}{extra}')
    for frac in (0.005, 0.01, 0.02, 0.05, 0.1):
        print('hexagon frac', frac, 'corners', describe_shape(dict(four_shapes())['hexagon'], frac)['corners'],
              ' circle corners', describe_shape(dict(four_shapes())['circle'], frac)['corners'])
    m = small_mask()
    print('mask\n', m)
    print('4-conn\n', label_components(m, False))
    print('8-conn\n', label_components(m, True))
    pts = table_points()
    eu = euclidean_clusters(pts, 10.0, 10)
    print('table points', len(pts), 'euclid sizes', [int((eu == c).sum()) for c in range(eu.max() + 1)],
          'dropped', int((eu == -1).sum()))
    raw = euclidean_clusters(pts, 10.0, 1)
    print('euclid before size filter: clusters', raw.max() + 1)
    db, core = dbscan(pts, 10.0, 5)
    print('dbscan sizes', [int((db == c).sum()) for c in range(db.max() + 1)],
          'noise', int((db == -1).sum()), 'core', int(core.sum()),
          'border', int(((db >= 0) & ~core).sum()))
    b = bridge_points()
    eb = euclidean_clusters(b, 10.0, 1)
    dbb, cb = dbscan(b, 10.0, 5)
    print('bridge pts', len(b), 'euclid clusters', eb.max() + 1,
          'dbscan clusters', dbb.max() + 1, 'dbscan sizes',
          [int((dbb == c).sum()) for c in range(dbb.max() + 1)], 'noise', int((dbb == -1).sum()),
          'neighbour counts of bridge pts', [len(n) for n in neighbours_within(b, 10.0)[-4:]])
    d = dense_cloud()
    for s in (5.0, 10.0, 20.0):
        down, _ = voxel_downsample(d, s)
        print('voxel', s, len(d), '->', len(down))


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    gradient_arrows()
    canny_steps()
    outline_to_polygon()
    counting_corners()
    connected_components_picture()
    euclidean_picture()
    dbscan_picture()
    bridge_picture()
    voxel_picture()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
