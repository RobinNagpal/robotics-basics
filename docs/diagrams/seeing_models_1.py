"""Generate the diagrams for the first half of docs/06_learned-models/03_seeing-models/.

This covers 01_overview, 02_image-classification, 03_object-detection and
04_segmentation. Each document's pictures go to a folder named after it, under
docs/images/seeing-models/.

Run with:  pixi run python ../docs/diagrams/seeing_models_1.py
Add --png <dir> to also write PNG copies for checking.

The pictures are drawings, not real model output. The confidence numbers on them
are example values, and the documents say so.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Ellipse, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'seeing-models'
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

# The scene every picture shares: a photo 10 wide and 7 high, with a blue mug,
# a green bottle and a red mug standing on a table.
W: float = 10.0
H: float = 7.0
TABLE_TOP: float = 2.0
MUG_1: tuple[float, float, float, float] = (1.2, 1.2, 1.6, 2.0)
BOTTLE: tuple[float, float, float, float] = (4.3, 1.0, 1.0, 2.8)
MUG_2: tuple[float, float, float, float] = (6.8, 1.3, 1.6, 2.0)


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


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='top', color=MUTED)


def _tag(ax: Axes, x: float, y: float, text: str, color: str, size: float = 9,
         ha: str = 'left') -> None:
    """A small filled label, as detectors print on top of a box."""
    ax.text(x, y, text, fontsize=size, ha=ha, va='bottom', color='white', weight='bold',
            zorder=9, bbox={'boxstyle': 'square,pad=0.2', 'facecolor': color,
                            'edgecolor': color})


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>') -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': style, 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=8)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# the objects and the scene
# --------------------------------------------------------------------------

def _mug(ax: Axes, box: tuple[float, float, float, float], color: str, alpha: float = 1.0,
         lw: float = 5.0, rim: bool = True, z: int = 3) -> None:
    """A mug seen from the side, with its handle on the right."""
    x, y, w, h = box
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor='none', alpha=alpha,
                           zorder=z))
    ax.add_patch(Arc((x + w, y + h * 0.5), w * 0.6, h * 0.55, theta1=-90, theta2=90,
                     color=color, lw=lw, alpha=alpha, zorder=z))
    if rim:
        ax.add_patch(Ellipse((x + w / 2, y + h), w, 0.28, facecolor='white',
                             edgecolor=color, lw=1.5, alpha=alpha, zorder=z + 1))


def _bottle(ax: Axes, box: tuple[float, float, float, float], color: str,
            alpha: float = 1.0, cap: str = INK, z: int = 3) -> None:
    x, y, w, h = box
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor='none', alpha=alpha,
                           zorder=z))
    ax.add_patch(Polygon([(x, y + h), (x + w, y + h), (x + 0.7 * w, y + h + 0.5),
                          (x + 0.3 * w, y + h + 0.5)], closed=True, facecolor=color,
                         edgecolor='none', alpha=alpha, zorder=z))
    ax.add_patch(Rectangle((x + 0.3 * w, y + h + 0.5), 0.4 * w, 0.25, facecolor=color,
                           edgecolor='none', alpha=alpha, zorder=z))
    ax.add_patch(Rectangle((x + 0.27 * w, y + h + 0.75), 0.46 * w, 0.2, facecolor=cap,
                           edgecolor='none', alpha=alpha, zorder=z))


def _mug_box(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """The tight rectangle round a mug and its handle, as (x0, y0, x1, y1)."""
    x, y, w, h = box
    return (x - 0.08, y - 0.08, x + w * 1.36, y + h + 0.2)


def _bottle_box(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x, y, w, h = box
    return (x - 0.08, y - 0.08, x + w + 0.08, y + h + 1.02)


def _frame(ax: Axes, x0: float = 0.0, y0: float = 0.0, w: float = W, h: float = H) -> None:
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor='none', edgecolor=INK, lw=1.2,
                           zorder=10))


def _background(ax: Axes, x0: float = 0.0, y0: float = 0.0, w: float = W, h: float = H,
                table_top: float = TABLE_TOP) -> None:
    ax.add_patch(Rectangle((x0, y0 + table_top), w, h - table_top, facecolor=WALL,
                           edgecolor='none', zorder=1))
    ax.add_patch(Rectangle((x0, y0), w, table_top, facecolor=TABLE, edgecolor='none',
                           zorder=1))


def _scene(ax: Axes, objects: bool = True) -> None:
    """The shared photo: wall, table, blue mug, green bottle, red mug."""
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
    _background(ax)
    if objects:
        _mug(ax, MUG_1, LINK)
        _bottle(ax, BOTTLE, SLIDE)
        _mug(ax, MUG_2, GRIP)
    _frame(ax)


def _box(ax: Axes, b: tuple[float, float, float, float], color: str, lw: float = 2.2,
         ls: str = '-', z: int = 8) -> None:
    ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], facecolor='none',
                           edgecolor=color, lw=lw, ls=ls, zorder=z))


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'


def seven_answers() -> None:
    """One photo, and the kind of answer each of the seven subcategories gives."""
    fig, axes = plt.subplots(2, 4, figsize=(15.0, 7.6), facecolor='white')
    flat: list[Axes] = list(axes.ravel())

    ax = flat[0]
    _scene(ax)
    _title(ax, W / 2, H + 0.9, 'The photo')
    _caption(ax, W / 2, -0.6, 'What the camera gives.')

    # 1. image classification: one name for a picture of one thing
    ax = flat[1]
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
    _background(ax)
    _mug(ax, (3.2, 1.2, 2.6, 3.4), LINK, lw=8)
    _frame(ax)
    _tag(ax, 0.3, 5.9, 'mug', INK, size=11)
    _title(ax, W / 2, H + 0.9, 'Classification')
    _caption(ax, W / 2, -0.6, 'One name for the whole picture.')

    # 2. object detection: a box and a name for each thing
    ax = flat[2]
    _scene(ax)
    for b, name, c in ((_mug_box(MUG_1), 'mug', LINK), (_bottle_box(BOTTLE), 'bottle', SLIDE),
                       (_mug_box(MUG_2), 'mug', GRIP)):
        _box(ax, b, INK)
        _tag(ax, b[0], b[3], name, INK)
    _title(ax, W / 2, H + 0.9, 'Detection')
    _caption(ax, W / 2, -0.6, 'A box and a name for each thing.')

    # 3. segmentation: the exact pixels of each thing
    ax = flat[3]
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
    ax.add_patch(Rectangle((0, 0), W, H, facecolor='white', edgecolor='none', zorder=1))
    _mug(ax, MUG_1, LINK, rim=False)
    _bottle(ax, BOTTLE, SLIDE, cap=SLIDE)
    _mug(ax, MUG_2, JOINT, rim=False)
    _frame(ax)
    _title(ax, W / 2, H + 0.9, 'Segmentation')
    _caption(ax, W / 2, -0.6, 'The exact pixels of each thing.')

    # 4. keypoints and pose
    ax = flat[4]
    _scene(ax)
    x, y, w, h = MUG_2
    pts = [(x, y + h), (x + w, y + h), (x, y), (x + w, y), (x + w * 1.3, y + h * 0.5)]
    for p in pts:
        ax.plot([p[0]], [p[1]], 'o', color=JOINT, mec=INK, ms=8, zorder=9)
    cx, cy = x + w / 2, y + h / 2
    _arrow(ax, (cx, cy), (cx + 1.6, cy + 0.9), color=INK, lw=2.0)
    _arrow(ax, (cx, cy), (cx, cy + 2.6), color=INK, lw=2.0)
    _title(ax, W / 2, H + 0.9, 'Keypoints and pose')
    _caption(ax, W / 2, -0.6, 'Named points, and which way\nthe object faces.')

    # 5. depth
    ax = flat[5]
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
    grad = np.linspace(0.25, 0.6, 50).reshape(-1, 1)
    ax.imshow(grad, extent=(0, W, 0, TABLE_TOP), cmap='Greys_r', vmin=0, vmax=1,
              origin='lower', aspect='auto', zorder=1)
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))    # imshow resets the limits and aspect
    ax.add_patch(Rectangle((0, TABLE_TOP), W, H - TABLE_TOP, facecolor='#e6e6e6',
                           edgecolor='none', zorder=1))
    _mug(ax, MUG_1, '#555555', rim=False)
    _bottle(ax, BOTTLE, '#6a6a6a', cap='#6a6a6a')
    _mug(ax, MUG_2, '#444444', rim=False)
    _frame(ax)
    _label(ax, 8.9, 6.4, 'far', color=MUTED)
    _label(ax, 8.9, 0.5, 'near', color='white')
    _title(ax, W / 2, H + 0.9, 'Depth')
    _caption(ax, W / 2, -0.6, 'How far away each pixel is.\nDarker is nearer.')

    # 6. open vocabulary: found from words
    ax = flat[6]
    _scene(ax)
    _box(ax, _mug_box(MUG_2), INK)
    _label(ax, W / 2, 5.9, 'asked for: "the red mug"', size=11, color=INK)
    _title(ax, W / 2, H + 0.9, 'Open vocabulary')
    _caption(ax, W / 2, -0.6, 'Finds what you ask for in words,\neven names it never trained on.')

    # 7. tracking and motion
    ax = flat[7]
    _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
    _background(ax)
    for i, (dx, a) in enumerate(((0.0, 0.25), (2.3, 0.5), (4.6, 1.0))):
        _mug(ax, (1.2 + dx, 1.3, 1.6, 2.0), GRIP, alpha=a, rim=(i == 2))
        _label(ax, 2.0 + dx, 0.7, f'frame {i + 1}', size=9, color=MUTED)
    _arrow(ax, (2.0, 4.1), (7.4, 4.1), color=INK, lw=2.0)
    _frame(ax)
    _title(ax, W / 2, H + 0.9, 'Tracking and motion')
    _caption(ax, W / 2, -0.6, 'The same object followed\nfrom picture to picture.')

    fig.subplots_adjust(wspace=0.12, hspace=0.45)
    _save(fig, OVERVIEW, 'seven-answers.svg')


def detail_levels() -> None:
    """A name, a box and an outline of the same mug, and what each lets the arm do."""
    fig, axes = _panels(3, (13.5, 4.9))
    mug = (3.2, 1.2, 2.6, 3.4)
    texts = (('A name', 'The arm learns a mug is there.\nIt does not learn where.'),
             ('A box', 'The arm learns roughly where.\nThe box also holds table and wall.'),
             ('An outline', 'The arm learns exactly which\npixels are mug, handle included.'))
    for i, (ax, (title, caption)) in enumerate(zip(axes, texts)):
        _axes(ax, (-0.3, W + 0.3), (-0.3, H + 0.3))
        _background(ax)
        _mug(ax, mug, LINK, lw=8)
        _frame(ax)
        if i == 0:
            _tag(ax, 0.3, 5.9, 'mug', INK, size=12)
        elif i == 1:
            b = (mug[0] - 0.1, mug[1] - 0.1, mug[0] + mug[2] * 1.38, mug[1] + mug[3] + 0.25)
            _box(ax, b, INK, lw=2.5)
            _tag(ax, b[0], b[3], 'mug', INK, size=11)
        else:
            _mug(ax, mug, JOINT, lw=10, rim=False, z=6)
            _tag(ax, mug[0], mug[1] + mug[3] + 0.3, 'mug', INK, size=11)
        _title(ax, W / 2, H + 0.8, title)
        _caption(ax, W / 2, -0.6, caption)
    _save(fig, OVERVIEW, 'name-box-outline.svg')


# --------------------------------------------------------------------------
# 02_image-classification
# --------------------------------------------------------------------------

CLASSIFY: str = 'image-classification'


def _tiny_mug_picture() -> np.ndarray:
    """A 12 x 12 grey picture of a mug on a table: one brightness number per pixel."""
    img = np.full((12, 12), 236, dtype=int)
    img[8:, :] = 186                                   # the table
    img[3:10, 2:7] = 64                                # the body of the mug
    for r, c in ((4, 7), (4, 8), (5, 8), (6, 8), (7, 8), (7, 7)):
        img[r, c] = 64                                 # the handle
    for r in range(12):
        for c in range(12):
            img[r, c] += (r * 7 + c * 13) % 7 - 3      # small differences, as in a photo
    return img


def pixels_to_numbers() -> None:
    """A tiny picture, a zoomed corner with its brightness numbers, and the flat list."""
    img = _tiny_mug_picture()
    fig, ax = plt.subplots(figsize=(13.5, 5.6), facecolor='white')
    _axes(ax, (-0.5, 31.5), (-0.4, 13.4))
    for r in range(12):
        for c in range(12):
            v = img[r, c] / 255
            ax.add_patch(Rectangle((c, 11 - r), 1, 1, facecolor=(v, v, v), edgecolor=GRID,
                                   lw=0.5, zorder=2))
    ax.add_patch(Rectangle((5, 6), 4, 4, facecolor='none', edgecolor=GRIP, lw=2.5, zorder=5))
    _label(ax, 6, 12.7, 'The picture: 12 × 12 pixels', size=11, weight='bold')

    x0, y0, s = 14.0, 2.6, 1.7
    for i in range(4):
        for j in range(4):
            v = int(img[2 + i, 5 + j])
            g = v / 255
            ax.add_patch(Rectangle((x0 + j * s, y0 + (3 - i) * s), s, s, facecolor=(g, g, g),
                                   edgecolor=GRID, lw=0.8, zorder=2))
            _label(ax, x0 + j * s + s / 2, y0 + (3 - i) * s + s / 2, str(v), size=11,
                   color='white' if g < 0.5 else INK)
    ax.add_patch(Rectangle((x0, y0), 4 * s, 4 * s, facecolor='none', edgecolor=GRIP, lw=2.5,
                           zorder=5))
    for a, b in (((9, 10), (x0, y0 + 4 * s)), ((9, 6), (x0, y0))):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=GRIP, lw=1, ls=':', zorder=4)
    _label(ax, x0 + 2 * s, 12.7, 'The red square, close up', size=11, weight='bold')
    _label(ax, x0 + 2 * s, 1.4, 'Each pixel is one number:\n0 is black, 255 is white.',
           size=10, color=MUTED)

    patch = [int(v) for v in img[2:6, 5:9].ravel()]
    lines = [', '.join(str(v) for v in patch[k:k + 4]) + ',' for k in range(0, 16, 4)]
    _arrow(ax, (21.4, 6.0), (23.4, 6.0), color=INK, lw=2)
    _label(ax, 27.4, 12.7, 'What the model is given', size=11, weight='bold')
    _label(ax, 27.4, 11.2, 'the numbers, one row after another', size=10, color=MUTED)
    for k, line in enumerate(lines):
        ax.text(24.0, 9.6 - k * 1.1, line, fontsize=10.5, family='monospace', color=INK,
                va='center')
    ax.text(24.0, 9.6 - 4 * 1.1, '... and so on,', fontsize=10.5, family='monospace',
            color=MUTED, va='center')
    ax.text(24.0, 9.6 - 5 * 1.1, '144 numbers in all', fontsize=10.5, family='monospace',
            color=MUTED, va='center')
    _label(ax, 27.4, 1.4, 'A real colour camera picture of\n640 × 480 pixels, with red, '
           'green\nand blue for each, is 921,600 numbers.', size=10, color=MUTED)
    _save(fig, CLASSIFY, 'pixels-become-numbers.svg')


def scores_for_names() -> None:
    """One picture in, one score per name out, and the highest score is the answer."""
    fig = plt.figure(figsize=(12.0, 4.6), facecolor='white')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.35], wspace=0.35)
    left = fig.add_subplot(gs[0])
    _axes(left, (-0.3, W + 0.3), (-0.3, H + 0.3))
    _background(left)
    _mug(left, (3.2, 1.2, 2.6, 3.4), LINK, lw=8)
    _frame(left)
    _title(left, W / 2, H + 0.9, 'The picture that goes in')

    right = fig.add_subplot(gs[1])
    names = ['mug', 'cup', 'bowl', 'bottle', 'vase']
    scores = [0.81, 0.12, 0.04, 0.02, 0.01]
    colors = [LINK] + [LINK_PALE] * 4
    ys = np.arange(len(names))[::-1]
    right.barh(ys, scores, color=colors, height=0.6)
    for y, s in zip(ys, scores):
        right.text(s + 0.015, y, f'{s:.2f}', va='center', fontsize=11, color=INK)
    right.set_yticks(ys)
    right.set_yticklabels(names, fontsize=12)
    right.set_xlim(0, 1.0)
    right.set_xlabel('score (example numbers; the five add up to 1)', fontsize=10,
                     color=MUTED)
    for side in ('top', 'right'):
        right.spines[side].set_visible(False)
    right.tick_params(colors=INK)
    right.set_title('The scores that come out', fontsize=12, weight='bold', color=INK,
                    pad=14)
    right.annotate('the answer: the name\nwith the highest score', xy=(0.7, ys[0] - 0.32),
                   xytext=(0.55, 2.2), fontsize=10, color=INK,
                   arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.3})
    _save(fig, CLASSIFY, 'one-score-per-name.svg')


def _tile(ax: Axes, x: float, y: float, s: float) -> None:
    ax.add_patch(Rectangle((x, y), s, s, facecolor='white', edgecolor=MUTED, lw=1.2,
                           zorder=2))


def layers_build_up() -> None:
    """Early layers react to edges, middle ones to parts, the last ones to whole objects."""
    fig, ax = plt.subplots(figsize=(12.5, 6.2), facecolor='white')
    _axes(ax, (-0.5, 23.5), (-0.6, 11.2))
    s = 2.6
    cols = (1.0, 10.0, 19.0)
    rows = (6.6, 3.6, 0.6)
    titles = ('Early layers\nreact to edges', 'Middle layers\nreact to parts',
              'Last layers\nreact to whole objects')
    for x, t in zip(cols, titles):
        _label(ax, x + s / 2, 10.3, t, size=11, weight='bold')
        for y in rows:
            _tile(ax, x, y, s)

    # edges
    x, lw = cols[0], 3
    y = rows[0]
    ax.plot([x + 0.4, x + s - 0.4], [y + s / 2, y + s / 2], color=INK, lw=lw, zorder=3)
    y = rows[1]
    ax.plot([x + s / 2, x + s / 2], [y + 0.4, y + s - 0.4], color=INK, lw=lw, zorder=3)
    y = rows[2]
    ax.add_patch(Arc((x + s / 2, y + 0.5), s - 0.8, s - 0.6, theta1=0, theta2=180, color=INK,
                     lw=lw, zorder=3))
    for y, t in zip(rows, ('flat edge', 'upright edge', 'curve')):
        _label(ax, x + s + 0.3, y + s / 2, t, size=10, color=MUTED, ha='left')

    # parts
    x = cols[1]
    y = rows[0]
    ax.add_patch(Ellipse((x + s / 2, y + s / 2), s - 0.6, 0.7, facecolor='white',
                         edgecolor=LINK, lw=3, zorder=3))
    y = rows[1]
    ax.add_patch(Arc((x + 0.9, y + s / 2), 1.8, 1.6, theta1=-90, theta2=90, color=LINK, lw=5,
                     zorder=3))
    y = rows[2]
    ax.add_patch(Polygon([(x + 0.6, y + 0.3), (x + s - 0.6, y + 0.3), (x + s - 0.9, y + 1.3),
                          (x + 0.9, y + 1.3)], closed=True, facecolor=SLIDE, edgecolor='none',
                         zorder=3))
    ax.add_patch(Rectangle((x + 1.0, y + 1.3), s - 2.0, 0.9, facecolor=SLIDE, zorder=3))
    for y, t in zip(rows, ('round rim', 'handle loop', 'bottle neck')):
        _label(ax, x + s + 0.3, y + s / 2, t, size=10, color=MUTED, ha='left')

    # whole objects
    x = cols[2]
    _mug(ax, (x + 0.5, rows[0] + 0.4, 1.2, 1.6), LINK, lw=4)
    _bottle(ax, (x + 0.95, rows[1] + 0.3, 0.7, 1.3), SLIDE)
    ax.add_patch(Arc((x + s / 2, rows[2] + 1.7), s - 0.6, 2.4, theta1=180, theta2=360,
                     color=WRIST, lw=4, zorder=3))
    ax.plot([x + 0.3, x + s - 0.3], [rows[2] + 1.7, rows[2] + 1.7], color=WRIST, lw=4,
            zorder=3)
    for y, t in zip(rows, ('mug', 'bottle', 'bowl')):
        _label(ax, x + s + 0.3, y + s / 2, t, size=10, color=MUTED, ha='left')

    for a, b in ((7.2, 9.6), (16.2, 18.6)):
        _arrow(ax, (a, 5.0), (b, 5.0), color=INK, lw=2)
    _save(fig, CLASSIFY, 'edges-parts-objects.svg')


# --------------------------------------------------------------------------
# 03_object-detection
# --------------------------------------------------------------------------

DETECT: str = 'object-detection'


def boxes_on_table() -> None:
    """The detector's answer: a box, a name and a confidence for each object."""
    fig, ax = plt.subplots(figsize=(8.0, 6.0), facecolor='white')
    _scene(ax)
    for b, text, c in ((_mug_box(MUG_1), 'mug 0.94', LINK),
                       (_bottle_box(BOTTLE), 'bottle 0.88', SLIDE),
                       (_mug_box(MUG_2), 'mug 0.91', GRIP)):
        _box(ax, b, c, lw=2.6)
        _tag(ax, b[0], b[3], text, c, size=10)
    _save(fig, DETECT, 'boxes-on-a-table.svg')


def many_guesses() -> None:
    """Before cleanup the detector gives many boxes for one mug; afterwards, one."""
    fig, axes = _panels(2, (13.5, 5.4))
    mug = (3.5, 1.3, 2.2, 3.0)
    kept = _mug_box(mug)
    guesses = ((kept, 0.91, INK), ((3.0, 0.9, 6.3, 4.9), 0.84, LINK),
               ((3.8, 1.5, 7.0, 5.0), 0.77, PURPLE), ((3.2, 1.0, 6.7, 4.2), 0.63, SLIDE),
               ((3.7, 0.7, 7.3, 4.6), 0.48, JOINT))
    for i, ax in enumerate(axes):
        _axes(ax, (-0.3, 15.0), (-1.2, H + 1.2))
        _background(ax)
        _mug(ax, mug, GRIP, lw=7)
        _frame(ax)
    left, right = axes
    for k, (b, score, c) in enumerate(guesses):
        _box(left, b, c, lw=2.0)
        left.plot([10.6, 11.4], [6.0 - k * 0.9] * 2, color=c, lw=2.5)
        _label(left, 11.7, 6.0 - k * 0.9, f'box {k + 1}: {score:.2f}', size=10.5, ha='left')
    _title(left, W / 2, H + 0.7, 'What the network gives: five boxes for one mug')
    _caption(left, W / 2, -0.35, 'All five overlap a lot. They are guesses at the same mug.')

    _box(right, kept, INK, lw=2.6)
    _tag(right, kept[0], kept[3], 'mug 0.91', INK, size=10)
    _label(right, 10.6, 6.0, 'Keep box 1: the highest score.', size=10.5, ha='left')
    _label(right, 10.6, 5.1, 'Drop boxes 2 to 5: each one', size=10.5, ha='left')
    _label(right, 10.6, 4.5, 'overlaps box 1 too much.', size=10.5, ha='left')
    _title(right, W / 2, H + 0.7, 'After the cleanup step: one box')
    _caption(right, W / 2, -0.35, 'This step is called non-maximum suppression.')
    _save(fig, DETECT, 'many-guesses-one-box.svg')


def grid_of_cells() -> None:
    """A one-look detector splits the picture into cells; the cell holding an object's middle
    reports that object's box."""
    fig, ax = plt.subplots(figsize=(8.6, 6.6), facecolor='white')
    _scene(ax)
    ax.set_ylim(-1.3, H + 0.3)
    nx, ny = 7, 4
    cw, ch = W / nx, H / ny
    for k in range(1, nx):
        ax.plot([k * cw, k * cw], [0, H], color=INK, lw=0.9, ls='--', zorder=7)
    for k in range(1, ny):
        ax.plot([0, W], [k * ch, k * ch], color=INK, lw=0.9, ls='--', zorder=7)
    for b, c in ((_mug_box(MUG_1), LINK), (_bottle_box(BOTTLE), SLIDE),
                 (_mug_box(MUG_2), GRIP)):
        mx, my = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        col, row = int(mx // cw), int(my // ch)
        ax.add_patch(Rectangle((col * cw, row * ch), cw, ch, facecolor='#fbe3a6',
                               edgecolor='none', zorder=2))
        ax.add_patch(Rectangle((col * cw, row * ch), cw, ch, facecolor='none',
                               edgecolor=JOINT, lw=2.5, zorder=7))
        _box(ax, b, c, lw=2.4)
        ax.plot([mx], [my], 'o', color='white', mec=INK, mew=1.5, ms=10, zorder=9)
    _caption(ax, W / 2, -0.35, 'The picture is split into a grid of cells. The yellow cells hold '
             'the middle (white dot)\nof an object, so each of them reports that object\'s '
             'box and name.')
    _save(fig, DETECT, 'grid-of-cells.svg')


# --------------------------------------------------------------------------
# 04_segmentation
# --------------------------------------------------------------------------

SEGMENT: str = 'segmentation'


def _swatch(ax: Axes, x: float, y: float, color: str, text: str) -> None:
    ax.add_patch(Rectangle((x, y - 0.25), 0.5, 0.5, facecolor=color, edgecolor=INK, lw=0.6))
    _label(ax, x + 0.7, y, text, size=10, ha='left')


def semantic_vs_instance() -> None:
    """Semantic segmentation gives a kind per pixel; instance gives each object its own mask."""
    fig, axes = _panels(3, (15.0, 5.6))
    for ax in axes:
        _axes(ax, (-0.3, W + 0.3), (-2.6, H + 1.2))

    ax = axes[0]
    _background(ax)
    _mug(ax, MUG_1, LINK)
    _bottle(ax, BOTTLE, SLIDE)
    _mug(ax, MUG_2, GRIP)
    _frame(ax)
    _title(ax, W / 2, H + 0.7, 'The photo')

    ax = axes[1]
    ax.add_patch(Rectangle((0, TABLE_TOP), W, H - TABLE_TOP, facecolor='#cfcfcf', zorder=1))
    ax.add_patch(Rectangle((0, 0), W, TABLE_TOP, facecolor='#c9a877', zorder=1))
    _mug(ax, MUG_1, LINK, rim=False)
    _bottle(ax, BOTTLE, SLIDE, cap=SLIDE)
    _mug(ax, MUG_2, LINK, rim=False)
    _frame(ax)
    _title(ax, W / 2, H + 0.7, 'Semantic segmentation')
    _swatch(ax, 0.2, -0.8, '#cfcfcf', 'wall')
    _swatch(ax, 2.6, -0.8, '#c9a877', 'table')
    _swatch(ax, 5.0, -0.8, LINK, 'mug')
    _swatch(ax, 7.2, -0.8, SLIDE, 'bottle')
    _caption(ax, W / 2, -1.4, 'Every pixel gets a kind. Both mugs\nare the same colour: '
             'one "mug" area.')

    ax = axes[2]
    ax.add_patch(Rectangle((0, 0), W, H, facecolor='white', zorder=1))
    _mug(ax, MUG_1, LINK, rim=False)
    _bottle(ax, BOTTLE, SLIDE, cap=SLIDE)
    _mug(ax, MUG_2, JOINT, rim=False)
    _frame(ax)
    _title(ax, W / 2, H + 0.7, 'Instance segmentation')
    _swatch(ax, 0.2, -0.8, LINK, 'mug 1')
    _swatch(ax, 3.3, -0.8, SLIDE, 'bottle 1')
    _swatch(ax, 6.7, -0.8, JOINT, 'mug 2')
    _caption(ax, W / 2, -1.4, 'Each object gets its own mask.\nWall and table are left out.')
    fig.subplots_adjust(wspace=0.08)
    _save(fig, SEGMENT, 'semantic-and-instance.svg')


def box_vs_mask() -> None:
    """A box holds background as well as the mug; a mask holds only the mug."""
    fig, axes = _panels(2, (12.5, 5.8))
    mug = (3.0, 1.0, 3.0, 4.0)
    x, y, w, h = mug
    b = (x - 0.1, y - 0.1, x + w * 1.36, y + h + 0.25)
    for ax in axes:
        _axes(ax, (-0.3, W + 0.3), (-1.8, H + 1.0))
        _background(ax)
    left, right = axes
    left.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], facecolor='none',
                             edgecolor=MUTED, hatch='//', lw=0, zorder=2))
    _mug(left, mug, GRIP, lw=12)
    _box(left, b, INK, lw=2.5)
    _frame(left)
    _title(left, W / 2, H + 0.6, 'A box')
    _caption(left, W / 2, -0.35, 'The striped pixels are inside the box but are not mug:\n'
             'the wall, the table and the gap inside the handle.')

    _mug(right, mug, GRIP, lw=12, rim=False)
    _mug(right, mug, JOINT, lw=14, rim=False, z=6)
    _frame(right)
    hole = (x + w + 0.35, y + h / 2)
    _arrow(right, (8.6, 5.6), (hole[0] + 0.15, hole[1] + 0.2), color=INK, lw=1.5)
    _label(right, 8.6, 5.95, 'gap inside\nthe handle', size=10)
    _title(right, W / 2, H + 0.6, 'A mask')
    _caption(right, W / 2, -0.35, 'The yellow pixels are exactly the mug. The gap inside\n'
             'the handle is left out, so a finger could go there.')
    _save(fig, SEGMENT, 'box-and-mask.svg')


def _grid(ax: Axes, x0: float, y0: float, size: float, cells: np.ndarray,
          colors: dict[int, str]) -> None:
    n = cells.shape[0]
    s = size / n
    for r in range(n):
        for c in range(n):
            ax.add_patch(Rectangle((x0 + c * s, y0 + (n - 1 - r) * s), s, s,
                                   facecolor=colors[int(cells[r, c])], edgecolor=GRID,
                                   lw=0.6, zorder=2))
    ax.add_patch(Rectangle((x0, y0), size, size, facecolor='none', edgecolor=INK, lw=1.2,
                           zorder=3))


def u_shape() -> None:
    """A segmentation network shrinks the picture to find what is there, then grows it back to
    full size to say which pixels are which, copying detail across as it goes."""
    mug = np.zeros((8, 8), dtype=int)
    mug[2:7, 1:5] = 1
    for r, c in ((3, 5), (3, 6), (4, 6), (5, 6), (5, 5)):
        mug[r, c] = 1
    greys = {k: g for k, g in enumerate(('#f2f2f2', '#d9d9d9', '#bdbdbd', '#9e9e9e',
                                         '#7f7f7f'))}
    mid4 = np.array([[0, 1, 1, 0], [2, 4, 3, 1], [1, 3, 4, 2], [0, 2, 1, 0]])
    mid2 = np.array([[3, 2], [4, 3]])
    mid4b = np.array([[0, 2, 1, 0], [1, 4, 4, 2], [1, 4, 3, 1], [0, 1, 1, 0]])

    fig, ax = plt.subplots(figsize=(13.5, 6.4), facecolor='white')
    _axes(ax, (-0.6, 19.6), (-1.4, 10.4))
    _grid(ax, 0.0, 4.4, 3.6, mug, {0: WALL, 1: LINK})
    _grid(ax, 4.8, 2.2, 2.4, mid4, greys)
    _grid(ax, 8.7, 0.3, 1.6, mid2, greys)
    _grid(ax, 11.8, 2.2, 2.4, mid4b, greys)
    _grid(ax, 15.4, 4.4, 3.6, mug, {0: 'white', 1: JOINT})

    _label(ax, 1.8, 3.8, 'the photo\n8 × 8 pixels', size=10)
    _label(ax, 6.0, 1.5, '4 × 4', size=10)
    _label(ax, 9.5, -0.5, '2 × 2', size=10)
    _label(ax, 13.0, 1.5, '4 × 4', size=10)
    _label(ax, 17.2, 3.8, 'the mask\n8 × 8: mug or not', size=10)

    _arrow(ax, (3.0, 4.2), (4.6, 3.6), color=INK, lw=1.8)
    _arrow(ax, (7.0, 2.0), (8.5, 1.4), color=INK, lw=1.8)
    _arrow(ax, (10.5, 1.4), (11.6, 2.0), color=INK, lw=1.8)
    _arrow(ax, (14.4, 3.6), (15.9, 4.2), color=INK, lw=1.8)

    _arrow(ax, (3.8, 7.6), (15.2, 7.6), color=WRIST, lw=1.6)
    _label(ax, 9.5, 8.0, 'copy the fine detail across', size=10, color=WRIST)
    _arrow(ax, (7.4, 3.4), (11.6, 3.4), color=WRIST, lw=1.6)
    _label(ax, 9.5, 3.8, 'copy detail', size=10, color=WRIST)

    _label(ax, 4.6, 9.6, 'Shrink: work out what is in the picture', size=11, weight='bold')
    _label(ax, 14.6, 9.6, 'Grow back: say which pixel is which', size=11, weight='bold')
    _save(fig, SEGMENT, 'shrink-then-grow.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    seven_answers()
    detail_levels()
    pixels_to_numbers()
    scores_for_names()
    layers_build_up()
    boxes_on_table()
    many_guesses()
    grid_of_cells()
    semantic_vs_instance()
    box_vs_mask()
    u_shape()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
