"""Generate the diagrams for the first half of docs/06_programming-techniques/05_image-and-point-cloud-processing/.

This covers 01_overview, 02_thresholding-and-colour-masks and
03_morphology-and-distance-transform. Each document's pictures go to a folder
named after it, under docs/images/image-and-point-cloud-processing/.

Run with:  pixi run python ../docs/diagrams/image_processing_1.py
Add --png <dir> to also write PNG copies for checking.

Every picture here is computed, not drawn by hand. The small images are real
NumPy arrays, and the masks, erosions, dilations, distance transforms, Otsu
thresholds and groups shown on them are worked out by the functions below. The
functions use NumPy only, so the script runs without OpenCV or SciPy.
"""

import pathlib
import sys
from collections import deque

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.colors import to_hex  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
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

WALL: str = '#f3f3f3'
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'

OFF: str = '#f4f4f4'       # a "no" pixel in a mask
ON: str = LINK             # a "yes" pixel in a mask


# --------------------------------------------------------------------------
# the techniques themselves, in plain NumPy
# --------------------------------------------------------------------------

def rgb_to_hsv(rgb: NDArray[np.uint8]) -> NDArray[np.int32]:
    """Hue 0-179, saturation 0-255 and value 0-255, on the same scale as OpenCV."""
    f = rgb.astype(float) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(axis=-1)
    mn = f.min(axis=-1)
    d = mx - mn
    safe = np.where(d == 0, 1.0, d)
    h = np.where(mx == r, (60 * (g - b) / safe) % 360,
                 np.where(mx == g, 60 * (b - r) / safe + 120, 60 * (r - g) / safe + 240))
    h = np.where(d == 0, 0.0, h)
    s = np.where(mx == 0, 0.0, d / np.where(mx == 0, 1.0, mx))
    out = np.stack([np.round(h / 2) % 180, np.round(s * 255), np.round(mx * 255)], axis=-1)
    return out.astype(np.int32)


def otsu(values: NDArray[np.int_]) -> tuple[int, NDArray[np.float64]]:
    """Otsu's threshold: the cut that best separates dark from bright.

    Returns the threshold t (a pixel is bright when value >= t) and the score
    for every t from 0 to 255. The score is w_dark * w_bright * (mean gap)^2.
    """
    v = np.asarray(values).ravel()
    scores = np.zeros(256)
    for t in range(1, 256):
        dark = v[v < t]
        bright = v[v >= t]
        if len(dark) == 0 or len(bright) == 0:
            continue
        wd = len(dark) / len(v)
        scores[t] = wd * (1 - wd) * (dark.mean() - bright.mean()) ** 2
    return int(np.argmax(scores)), scores


def _shifts(mask: NDArray[np.bool_], size: int, fill: bool) -> list[NDArray[np.bool_]]:
    """Every copy of the mask moved by up to size // 2 pixels in each direction."""
    k = size // 2
    padded = np.pad(mask, k, constant_values=fill)
    h, w = mask.shape
    return [padded[k + dy:k + dy + h, k + dx:k + dx + w]
            for dy in range(-k, k + 1) for dx in range(-k, k + 1)]


def erode(mask: NDArray[np.bool_], size: int = 3) -> NDArray[np.bool_]:
    """A pixel stays yes only if every pixel under the square brush is yes."""
    return np.logical_and.reduce(_shifts(mask, size, fill=False))


def dilate(mask: NDArray[np.bool_], size: int = 3) -> NDArray[np.bool_]:
    """A pixel becomes yes if any pixel under the square brush is yes."""
    return np.logical_or.reduce(_shifts(mask, size, fill=False))


def opening(mask: NDArray[np.bool_], size: int = 3) -> NDArray[np.bool_]:
    return dilate(erode(mask, size), size)


def closing(mask: NDArray[np.bool_], size: int = 3) -> NDArray[np.bool_]:
    return erode(dilate(mask, size), size)


def distance_steps(mask: NDArray[np.bool_]) -> NDArray[np.int32]:
    """City-block distance transform by the classic two passes.

    Each yes pixel gets the number of up, down, left or right steps to the
    nearest no pixel. Everything outside the picture counts as no.
    """
    h, w = mask.shape
    big = h + w
    d = np.where(mask, big, 0).astype(np.int32)
    for y in range(h):                       # pass 1: top-left to bottom-right
        for x in range(w):
            if d[y, x]:
                up = d[y - 1, x] if y > 0 else 0
                left = d[y, x - 1] if x > 0 else 0
                d[y, x] = min(d[y, x], up + 1, left + 1)
    for y in range(h - 1, -1, -1):           # pass 2: bottom-right to top-left
        for x in range(w - 1, -1, -1):
            if d[y, x]:
                down = d[y + 1, x] if y < h - 1 else 0
                right = d[y, x + 1] if x < w - 1 else 0
                d[y, x] = min(d[y, x], down + 1, right + 1)
    return d


def distance_straight(mask: NDArray[np.bool_]) -> NDArray[np.float64]:
    """Exact straight-line distance from each yes pixel to the nearest no pixel.

    Brute force, which is fine for the small pictures here. The picture is
    padded with one ring of no pixels, so the outside counts as no.
    """
    padded = np.pad(mask, 1, constant_values=False)
    ys, xs = np.nonzero(~padded)
    out = np.zeros(mask.shape)
    for y, x in zip(*np.nonzero(mask)):
        out[y, x] = np.sqrt(((ys - (y + 1)) ** 2 + (xs - (x + 1)) ** 2).min())
    return out


def label(mask: NDArray[np.bool_]) -> tuple[NDArray[np.int32], int]:
    """Connected components, joining pixels that touch on a side (4 neighbours)."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    h, w = mask.shape
    for sy, sx in zip(*np.nonzero(mask)):
        if lab[sy, sx]:
            continue
        n += 1
        lab[sy, sx] = n
        todo = deque([(sy, sx)])
        while todo:
            y, x = todo.popleft()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    todo.append((ny, nx))
    return lab, n


def cluster_points(pts: NDArray[np.float64], radius: float) -> NDArray[np.int32]:
    """Euclidean clustering: points closer than radius end up in the same group."""
    lab = np.zeros(len(pts), dtype=np.int32)
    n = 0
    for i in range(len(pts)):
        if lab[i]:
            continue
        n += 1
        lab[i] = n
        todo = deque([i])
        while todo:
            j = todo.popleft()
            near = np.nonzero((np.linalg.norm(pts - pts[j], axis=1) < radius) & (lab == 0))[0]
            lab[near] = n
            todo.extend(near.tolist())
    return lab


# --------------------------------------------------------------------------
# the small pictures the pages share
# --------------------------------------------------------------------------

GREY_6X8: NDArray[np.int32] = np.array([
    [52, 48, 55, 60, 58, 50, 47, 53],
    [50, 56, 182, 190, 188, 61, 49, 51],
    [47, 59, 185, 203, 196, 178, 55, 46],
    [53, 62, 176, 199, 207, 184, 58, 50],
    [49, 57, 64, 171, 180, 66, 52, 48],
    [51, 46, 50, 57, 62, 54, 49, 45]])

DEPTH_ROW: NDArray[np.int32] = np.array([601, 600, 602, 538, 531, 529, 0, 533, 600, 599,
                                         521, 520, 601, 600])


def table_scene() -> NDArray[np.uint8]:
    """A 22 by 30 top-down picture: grey table, two red parts, one green part.

    The left red part has a white highlight (a hole in its mask), a few table
    pixels are slightly red (specks), and the two red parts are separate.
    """
    rng = np.random.default_rng(3)
    img = np.full((22, 30, 3), 125, dtype=np.int32)
    img += rng.integers(-6, 7, size=(22, 30, 1))
    img[3:11, 3:11] = (196, 44, 40)                 # red part 1
    img[6:8, 6:8] = (240, 205, 200)                 # highlight on it
    img[12:19, 16:26] = (190, 42, 46)               # red part 2
    img[3:9, 17:25] = (46, 150, 64)                 # green part
    for y, x in ((15, 4), (1, 14), (19, 11), (10, 27)):
        img[y, x] = (175, 70, 66)                   # reddish specks on the table
    return np.clip(img, 0, 255).astype(np.uint8)


def red_mask(img: NDArray[np.uint8]) -> NDArray[np.bool_]:
    """Hue near red (both ends of the circle), strong colour, not too dark."""
    hsv = rgb_to_hsv(img)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return ((h <= 10) | (h >= 170)) & (s >= 100) & (v >= 50)


def shadow_scene() -> NDArray[np.uint8]:
    """A 14 by 20 picture: a red block half in shadow, a green block, grey table."""
    img = np.full((14, 20, 3), 120, dtype=np.uint8)
    img[:, 9:] = (70, 70, 70)                       # the shadow falls on the right
    img[3:11, 4:14] = (200, 40, 40)                 # red block, lit part
    img[3:11, 9:14] = (100, 20, 20)                 # red block, shadowed part
    img[4:9, 15:19] = (20, 80, 30)                  # green block, in shadow
    return img


def open_close_mask() -> NDArray[np.bool_]:
    """A 15 by 21 mask as a colour threshold gives it: four specks, two holes, a bump."""
    m = np.zeros((15, 21), dtype=bool)
    m[3:12, 4:16] = True             # the part: 9 rows by 12 columns
    m[6, 8] = False                  # a one-pixel hole
    m[7:9, 12] = False               # a two-pixel hole
    m[2, 10] = True                  # a one-pixel bump on the top edge
    for y, x in ((1, 1), (13, 18), (6, 19), (12, 2)):
        m[y, x] = True               # specks
    return m


def erode_dilate_mask() -> NDArray[np.bool_]:
    """A 9 by 11 mask: a block with a thin arm and a speck."""
    m = np.zeros((9, 11), dtype=bool)
    m[2:7, 2:7] = True               # a 5 by 5 block
    m[4, 7:10] = True                # a one-pixel-wide arm
    m[1, 9] = True                   # a speck
    return m


def u_bracket() -> NDArray[np.bool_]:
    """A 13 by 14 U-shaped bracket, seen from above."""
    m = np.zeros((13, 14), dtype=bool)
    m[1:12, 1:4] = True              # left wall, 3 wide
    m[1:12, 10:13] = True            # right wall, 3 wide
    m[8:12, 1:13] = True             # the base joining them, 4 high
    return m


def two_discs() -> NDArray[np.bool_]:
    """Two touching discs, radius 8, centres 14 apart: two coins seen as one blob."""
    yy, xx = np.mgrid[0:22, 0:36]
    return (((yy - 10.5) ** 2 + (xx - 10.5) ** 2 <= 64)
            | ((yy - 10.5) ** 2 + (xx - 24.5) ** 2 <= 64))


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _title(ax: Axes, text: str, size: float = 11) -> None:
    ax.set_title(text, fontsize=size, color=INK, weight='bold', pad=8)


def _caption(ax: Axes, text: str, size: float = 9.5, y: float = -0.04) -> None:
    ax.text(0.5, y, text, transform=ax.transAxes, fontsize=size, ha='center', va='top',
            color=MUTED)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _cells(ax: Axes, colours: list[list[str]], text: list[list[str]] | None = None,
           text_colours: list[list[str]] | None = None, size: float = 8.5,
           edge: str = 'white', lw: float = 1.0) -> None:
    """Draw a grid of coloured squares, row 0 at the top, with optional text."""
    h = len(colours)
    w = len(colours[0])
    for y in range(h):
        for x in range(w):
            ax.add_patch(Rectangle((x, h - 1 - y), 1, 1, facecolor=colours[y][x],
                                   edgecolor=edge, lw=lw, zorder=2))
            if text is not None and text[y][x]:
                tc = text_colours[y][x] if text_colours else INK
                ax.text(x + 0.5, h - 0.5 - y, text[y][x], fontsize=size, ha='center',
                        va='center', color=tc, zorder=3)
    ax.add_patch(Rectangle((0, 0), w, h, facecolor='none', edgecolor=INK, lw=1.0, zorder=4))
    _axes(ax, (-0.2, w + 0.2), (-0.2, h + 0.2))


def _mask_colours(mask: NDArray[np.bool_], on: str = ON, off: str = OFF) -> list[list[str]]:
    return [[on if v else off for v in row] for row in mask]


def _show_rgb(ax: Axes, img: NDArray[np.uint8]) -> None:
    h, w = img.shape[:2]
    ax.imshow(img, interpolation='nearest', extent=(0, w, 0, h))
    ax.add_patch(Rectangle((0, 0), w, h, facecolor='none', edgecolor=INK, lw=1.0))
    _axes(ax, (-0.2, w + 0.2), (-0.2, h + 0.2))


def _grey_hex(v: float) -> str:
    g = int(round(v))
    return f'#{g:02x}{g:02x}{g:02x}'


def _arrow(fig: Figure, x0: float, x1: float, y: float) -> None:
    fig.patches.append(FancyArrowPatch(
        (x0, y), (x1, y), transform=fig.transFigure, arrowstyle='-|>', mutation_scale=16,
        color=MUTED, lw=1.6))


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'


def picture_to_objects() -> None:
    """One small picture taken through threshold, clean-up, outline and grouping."""
    img = table_scene()
    raw = red_mask(img)
    clean = closing(opening(raw))
    outline = clean & ~erode(clean)
    lab, n = label(clean)

    fig, axes = _panels(5, (15.5, 3.9))
    _show_rgb(axes[0], img)
    _title(axes[0], '1. The picture')
    _caption(axes[0], 'two red parts, one green\npart, on a grey table')

    _cells(axes[1], _mask_colours(raw), edge=OFF, lw=0.4)
    _title(axes[1], '2. Threshold')
    _caption(axes[1], f'"is it red?" gives a mask\nwith specks and a hole')

    _cells(axes[2], _mask_colours(clean), edge=OFF, lw=0.4)
    _title(axes[2], '3. Morphology')
    _caption(axes[2], 'opening removes specks,\nclosing fills the hole')

    _cells(axes[3], _mask_colours(outline, on=INK), edge=OFF, lw=0.4)
    _title(axes[3], '4. Edges and contours')
    _caption(axes[3], 'the outline of each part,\nready to measure')

    palette = {1: GRIP, 2: JOINT}
    cols = [[palette.get(int(v), OFF) for v in row] for row in lab]
    _cells(axes[4], cols, edge=OFF, lw=0.4)
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        axes[4].text(xs.mean() + 0.5, lab.shape[0] - 0.5 - ys.mean(), str(k),
                     fontsize=14, ha='center', va='center', color='white', weight='bold',
                     zorder=5)
    _title(axes[4], '5. Clustering')
    _caption(axes[4], f'{n} separate groups:\none per red part')
    fig.subplots_adjust(wspace=0.12)
    _save(fig, OVERVIEW, 'picture-to-objects.svg')


def point_cloud_side_view() -> None:
    """The same two ideas on a point cloud: a height threshold, then grouping."""
    rng = np.random.default_rng(7)
    table_x = rng.uniform(0, 420, 170)
    table = np.column_stack([table_x, rng.normal(0, 1.5, 170)])
    box_top = np.column_stack([rng.uniform(70, 150, 30), rng.normal(60, 1.5, 30)])
    box_side = np.column_stack([rng.normal(70, 1.2, 20), np.linspace(3, 58, 20)])
    cyl_top = np.column_stack([rng.uniform(250, 300, 20), rng.normal(95, 1.5, 20)])
    cyl_side = np.column_stack([rng.normal(250, 1.2, 32), np.linspace(3, 93, 32)])
    # the table under the objects is hidden from the camera
    keep = ~(((table_x > 72) & (table_x < 150)) | ((table_x > 252) & (table_x < 300)))
    pts = np.vstack([table[keep], box_top, box_side, cyl_top, cyl_side])

    above = pts[:, 1] > 10.0
    groups = cluster_points(pts[above], radius=15.0)
    assert groups.max() == 2, groups.max()

    fig, axes = plt.subplots(1, 2, figsize=(13, 3.6), facecolor='white')
    for ax in axes:
        ax.set_xlim(-10, 430)
        ax.set_ylim(-15, 125)
        ax.set_xlabel('across the table (mm)', fontsize=9.5, color=INK)
        ax.set_ylabel('height above table (mm)', fontsize=9.5, color=INK)
        ax.tick_params(labelsize=8.5, colors=MUTED)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axes[0].scatter(pts[:, 0], pts[:, 1], s=9, color=MUTED)
    axes[0].set_title('1. The point cloud, seen from the side', fontsize=11, color=INK,
                      weight='bold')

    axes[1].scatter(pts[~above, 0], pts[~above, 1], s=9, color=GRID)
    for k, c in ((1, GRIP), (2, JOINT)):
        sel = pts[above][groups == k]
        axes[1].scatter(sel[:, 0], sel[:, 1], s=11, color=c)
        axes[1].text(sel[:, 0].mean(), sel[:, 1].max() + 12, f'group {k}: {len(sel)} points',
                     fontsize=9.5, ha='center', color=c, weight='bold')
    axes[1].axhline(10, color=LINK, lw=1.4, ls='--')
    axes[1].text(425, 14, 'keep points higher than 10 mm', fontsize=9, color=LINK,
                 ha='right', va='bottom')
    axes[1].set_title('2. Height threshold, then group nearby points', fontsize=11,
                      color=INK, weight='bold')
    fig.subplots_adjust(wspace=0.25)
    _save(fig, OVERVIEW, 'point-cloud-side-view.svg')


# --------------------------------------------------------------------------
# 02_thresholding-and-colour-masks
# --------------------------------------------------------------------------

THRESH: str = 'thresholding-and-colour-masks'


def grey_threshold() -> None:
    """A 6 by 8 grey picture with its numbers, and the mask for value >= 120."""
    g = GREY_6X8
    m = g >= 120
    fig, axes = _panels(2, (11.5, 3.7))
    cols = [[_grey_hex(v) for v in row] for row in g]
    txt = [[str(v) for v in row] for row in g]
    tcol = [['white' if v < 120 else INK for v in row] for row in g]
    _cells(axes[0], cols, txt, tcol, size=9.5)
    _title(axes[0], 'The picture: one brightness number per pixel')
    _cells(axes[1], _mask_colours(m), [['1' if v else '0' for v in row] for row in m],
           [['white' if v else MUTED for v in row] for row in m], size=9.5)
    _title(axes[1], f'The mask: 1 where the number is 120 or more')
    _caption(axes[1], f'{int(m.sum())} of {m.size} pixels are 1', y=-0.05)
    _arrow(fig, 0.485, 0.525, 0.5)
    fig.subplots_adjust(wspace=0.2)
    _save(fig, THRESH, 'grey-threshold.svg')


def otsu_image() -> NDArray[np.int32]:
    """A 60 by 80 grey picture: a table around 70, a part around 165, and noise."""
    rng = np.random.default_rng(11)
    img = rng.normal(70, 14, size=(60, 80))
    yy, xx = np.mgrid[0:60, 0:80]
    part = (yy - 30) ** 2 / 17 ** 2 + (xx - 38) ** 2 / 24 ** 2 <= 1
    img[part] = rng.normal(165, 18, size=int(part.sum()))
    return np.clip(np.round(img), 0, 255).astype(np.int32)


def otsu_histogram() -> None:
    """The histogram of a real picture, Otsu's score for every cut, and the best cut."""
    img = otsu_image()
    t, scores = otsu(img)
    fig, (top, bot) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True, facecolor='white',
                                   gridspec_kw={'height_ratios': [1.3, 1]})
    counts = np.bincount(img.ravel(), minlength=256)
    top.bar(np.arange(256), counts, width=1.0,
            color=[GRID if i < t else LINK for i in range(256)])
    top.axvline(t, color=GRIP, lw=1.8)
    top.text(t + 3, counts.max() * 0.92, f"Otsu's cut: {t}", color=GRIP, fontsize=10,
             weight='bold')
    top.text(70, counts.max() * 1.02, 'the table', ha='center', fontsize=9.5, color=MUTED)
    top.text(165, counts.max() * 0.45, 'the part', ha='center', fontsize=9.5, color=LINK)
    top.set_ylabel('number of pixels', fontsize=9.5, color=INK)
    top.set_title('How many pixels have each brightness (a 60 by 80 picture)',
                  fontsize=11, color=INK, weight='bold')
    bot.plot(np.arange(256), scores, color=INK, lw=1.6)
    bot.axvline(t, color=GRIP, lw=1.8)
    bot.plot([t], [scores[t]], 'o', color=GRIP)
    bot.set_ylabel('separation score', fontsize=9.5, color=INK)
    bot.set_xlabel('brightness (0 is black, 255 is white)', fontsize=9.5, color=INK)
    bot.set_title('The score for cutting at each brightness: Otsu picks the highest',
                  fontsize=11, color=INK, weight='bold')
    for ax in (top, bot):
        ax.tick_params(labelsize=8.5, colors=MUTED)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    bot.set_xlim(0, 255)
    top.set_ylim(0, counts.max() * 1.12)
    fig.subplots_adjust(hspace=0.35)
    _save(fig, THRESH, 'otsu-histogram.svg')


def rgb_versus_hsv() -> None:
    """A red block half in shadow: a red-channel rule misses the shadow, an HSV rule does not."""
    img = shadow_scene()
    rgb_rule = img[..., 0].astype(int) > 150
    hsv = rgb_to_hsv(img)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    hsv_rule = ((h <= 10) | (h >= 170)) & (s >= 100) & (v >= 50)

    fig, axes = _panels(3, (14, 4.3))
    _show_rgb(axes[0], img)
    H = img.shape[0]
    lit = hsv[5, 6]
    dark = hsv[5, 11]
    axes[0].text(6.5, -1.6, f'lit: RGB (200, 40, 40)\nH {lit[0]}, S {lit[1]}, V {lit[2]}',
                 fontsize=8.5, ha='center', va='center', color=INK)
    axes[0].text(12.8, H + 1.6, f'shadow: RGB (100, 20, 20)\nH {dark[0]}, S {dark[1]}, V {dark[2]}',
                 fontsize=8.5, ha='center', va='center', color=INK)
    axes[0].plot([6.5], [H - 6.5], 'o', color='white', ms=5, mec=INK)
    axes[0].plot([11.5], [H - 6.5], 'o', color='white', ms=5, mec=INK)
    axes[0].set_ylim(-3.4, H + 3.2)
    _caption(axes[0], 'a red block, half in shadow', y=-0.02)

    _cells(axes[1], _mask_colours(rgb_rule), edge=OFF, lw=0.4)
    axes[1].set_ylim(-3.4, H + 3.2)
    axes[1].text(10, H + 1.8, 'rule: red channel above 150', fontsize=10.5, ha='center',
                 color=INK, weight='bold')
    _caption(axes[1], f'{int(rgb_rule.sum())} pixels: the shadowed half is lost', y=0.1)

    _cells(axes[2], _mask_colours(hsv_rule), edge=OFF, lw=0.4)
    axes[2].set_ylim(-3.4, H + 3.2)
    axes[2].text(10, H + 1.8, 'rule: hue 0-10 or 170-179,\nS 100+, V 50+', fontsize=10.5,
                 ha='center', color=INK, weight='bold')
    _caption(axes[2], f'{int(hsv_rule.sum())} pixels: the whole block', y=0.1)
    fig.subplots_adjust(wspace=0.12)
    _save(fig, THRESH, 'rgb-versus-hsv.svg')


def depth_band() -> None:
    """One row of a depth picture: keep what is nearer than the table, skip missing readings."""
    d = DEPTH_ROW
    keep = (d > 0) & (d < 590)
    x = np.arange(len(d))
    fig, (top, bot) = plt.subplots(2, 1, figsize=(10, 5.2), facecolor='white',
                                   gridspec_kw={'height_ratios': [3.2, 0.8]})
    top.axhspan(590, 640, color=TABLE, alpha=0.7, lw=0)
    top.axhline(590, color=GRIP, lw=1.6, ls='--')
    top.text(-0.4, 588, 'cut: 590 mm', color=GRIP, fontsize=9.5, ha='left', va='bottom')
    top.text(13.6, 628, 'the table: about 600 mm away', color=MUTED, fontsize=9.5,
             ha='right', va='center')
    for i, v in enumerate(d):
        if v == 0:
            top.plot([i], [575], 'x', color=GRIP, ms=10, mew=2)
            top.text(i, 568, 'reading 0:\nno depth here', ha='center', va='bottom',
                     fontsize=8.5, color=GRIP)
        else:
            top.plot([i], [v], 'o', color=LINK if keep[i] else MUTED, ms=7)
            top.text(i, v - 4 if keep[i] else v + 4, str(v), ha='center',
                     va='bottom' if keep[i] else 'top', fontsize=8.5, color=INK)
    top.set_ylim(645, 505)       # nearer is higher on the page, as the camera sees it
    top.set_xlim(-0.6, len(d) - 0.4)
    top.set_ylabel('distance from camera (mm)', fontsize=9.5, color=INK)
    top.set_xticks(x)
    top.tick_params(labelsize=8.5, colors=MUTED)
    top.set_xlabel('pixel column in one row of the depth picture', fontsize=9.5, color=INK)
    for s in ('top', 'right'):
        top.spines[s].set_visible(False)
    top.set_title('Keep a pixel when its reading is above 0 and below 590 mm',
                  fontsize=11, color=INK, weight='bold')
    for i, k in enumerate(keep):
        bot.add_patch(Rectangle((i - 0.5, 0), 1, 1, facecolor=ON if k else OFF,
                                edgecolor='white', lw=1.2))
        bot.text(i, 0.5, '1' if k else '0', ha='center', va='center', fontsize=9,
                 color='white' if k else MUTED)
    bot.set_xlim(-0.6, len(d) - 0.4)
    bot.set_ylim(-0.1, 1.1)
    bot.axis('off')
    bot.text(-0.6, 1.35, f'The mask for this row: {int(keep.sum())} of {len(d)} pixels kept',
             fontsize=10, color=INK, weight='bold')
    fig.subplots_adjust(hspace=0.55)
    _save(fig, THRESH, 'depth-band.svg')


# --------------------------------------------------------------------------
# 03_morphology-and-distance-transform
# --------------------------------------------------------------------------

MORPH: str = 'morphology-and-distance-transform'


def erode_and_dilate() -> None:
    """A mask, its erosion and its dilation with a 3 by 3 square brush."""
    m = erode_dilate_mask()
    e = erode(m)
    d = dilate(m)
    fig, axes = _panels(3, (13.5, 4.2))
    _cells(axes[0], _mask_colours(m))
    # the brush, drawn once on the original
    axes[0].add_patch(Rectangle((1, m.shape[0] - 1 - 5), 3, 3, facecolor='none',
                                edgecolor=JOINT, lw=2.6, zorder=6))
    _title(axes[0], f'The mask: {int(m.sum())} pixels')
    _caption(axes[0], 'orange square: the 3 by 3 brush')

    cols = [[ON if e[y, x] else (LINK_PALE if m[y, x] else OFF) for x in range(m.shape[1])]
            for y in range(m.shape[0])]
    _cells(axes[1], cols)
    _title(axes[1], f'Erosion: {int(e.sum())} pixels left')
    _caption(axes[1], 'pale: removed, because the brush\ncentred there touched a 0')

    cols = [[ON if m[y, x] else (JOINT if d[y, x] else OFF) for x in range(m.shape[1])]
            for y in range(m.shape[0])]
    _cells(axes[2], cols)
    _title(axes[2], f'Dilation: {int(d.sum())} pixels')
    _caption(axes[2], 'orange: added, because the brush\ncentred there touched a 1')
    fig.subplots_adjust(wspace=0.12)
    _save(fig, MORPH, 'erode-and-dilate.svg')


def open_and_close() -> None:
    """A messy threshold mask, then opening, then closing."""
    m = open_close_mask()
    o = opening(m)
    c = closing(o)
    fig, axes = _panels(3, (14, 3.9))
    _cells(axes[0], _mask_colours(m), edge=GRID, lw=0.4)
    _title(axes[0], f'From the threshold: {int(m.sum())} pixels')
    _caption(axes[0], '4 specks, 2 holes and a bump')

    cols = [[ON if o[y, x] else (GRIP if m[y, x] else OFF) for x in range(m.shape[1])]
            for y in range(m.shape[0])]
    _cells(axes[1], cols, edge=GRID, lw=0.4)
    _title(axes[1], f'After opening: {int(o.sum())} pixels')
    _caption(axes[1], 'red: removed (specks and the bump)')

    cols = [[ON if c[y, x] and o[y, x] else (SLIDE if c[y, x] else OFF)
             for x in range(m.shape[1])] for y in range(m.shape[0])]
    _cells(axes[2], cols, edge=GRID, lw=0.4)
    _title(axes[2], f'Then closing: {int(c.sum())} pixels')
    _caption(axes[2], 'green: filled in (the two holes)')
    fig.subplots_adjust(wspace=0.12)
    _save(fig, MORPH, 'open-and-close.svg')


def most_central_point() -> None:
    """The distance transform of a U-shaped bracket: its peak versus its centroid."""
    m = u_bracket()
    d = distance_steps(m)
    ys, xs = np.nonzero(m)
    cy, cx = ys.mean(), xs.mean()
    peak = np.argwhere(d == d.max())
    cmap = plt.get_cmap('Blues')
    cols = [[to_hex(cmap(0.25 + 0.7 * v / d.max())) if v else OFF
             for v in row] for row in d]
    txt = [[str(v) if v else '' for v in row] for row in d]
    tcol = [['white' if v >= 3 else INK for v in row] for row in d]
    fig, ax = plt.subplots(figsize=(7.2, 6.4), facecolor='white')
    _cells(ax, cols, txt, tcol, size=10)
    H = m.shape[0]
    for py, px in peak:
        ax.add_patch(Rectangle((px, H - 1 - py), 1, 1, facecolor='none', edgecolor=JOINT,
                               lw=3, zorder=6))
    ax.plot([cx + 0.5], [H - 0.5 - cy], marker='x', color=GRIP, ms=14, mew=3, zorder=7)
    ax.text(cx + 0.5, H - 0.5 - cy + 0.75, 'centroid\n(average position)', color=GRIP,
            fontsize=9.5, ha='center', va='bottom', weight='bold', zorder=7)
    ax.text(m.shape[1] / 2, -0.6,
            f'orange squares: the two pixels furthest inside, {d.max()} steps from the nearest edge',
            color=INK, fontsize=10, ha='center', va='top')
    ax.set_ylim(-1.4, H + 0.2)
    _title(ax, 'Each number: steps to the nearest pixel outside the bracket')
    _save(fig, MORPH, 'most-central-point.svg')


def split_touching() -> None:
    """Two touching coins: one blob, its distance transform, and the two cores inside it."""
    m = two_discs()
    d = distance_straight(m)
    cores = d >= 0.7 * d.max()
    lab_blob, n_blob = label(m)
    lab_core, n_core = label(cores)
    fig, axes = _panels(3, (14.5, 3.9))
    _cells(axes[0], _mask_colours(m), edge=OFF, lw=0.3)
    _title(axes[0], f'The mask: {n_blob} blob')
    _caption(axes[0], 'two coins that touch look like one')

    h, w = m.shape
    axes[1].imshow(np.where(m, d, np.nan), cmap='Blues', interpolation='nearest',
                   extent=(0, w, 0, h), vmin=-2, vmax=d.max())
    axes[1].add_patch(Rectangle((0, 0), w, h, facecolor='none', edgecolor=INK, lw=1.0))
    _axes(axes[1], (-0.2, w + 0.2), (-0.2, h + 0.2))
    _title(axes[1], 'The distance transform')
    _caption(axes[1], f'darker is further from the edge;\nlargest {d.max():.1f} pixels')

    palette = {1: GRIP, 2: JOINT}
    cols = [[palette.get(int(lab_core[y, x]), LINK_PALE if m[y, x] else OFF)
             for x in range(w)] for y in range(h)]
    _cells(axes[2], cols, edge=OFF, lw=0.3)
    _title(axes[2], f'Keep 70 % of the largest distance or more')
    _caption(axes[2], f'{n_core} separate cores: one seed per coin')
    fig.subplots_adjust(wspace=0.12)
    _save(fig, MORPH, 'split-touching.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    picture_to_objects()
    point_cloud_side_view()
    grey_threshold()
    otsu_histogram()
    rgb_versus_hsv()
    depth_band()
    erode_and_dilate()
    open_and_close()
    most_central_point()
    split_touching()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
