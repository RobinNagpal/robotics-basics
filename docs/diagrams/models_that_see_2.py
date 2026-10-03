"""Generate the diagrams for the last two pages of docs/05_neural-networks/09_models-that-see/.

    03_open-vocabulary-vision.md -> images/models-that-see/open-vocabulary-vision/
    04_depth-and-3d.md           -> images/models-that-see/depth-and-3d/

Run with:  python3 models_that_see_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script prints
all of them so the two documents can quote the same values.

What is real and what is simulated:

* The shared picture-and-text space used by the open-vocabulary page is made up.
  It has thirteen named directions chosen so that a reader can follow the
  arithmetic by hand, and the word vectors and region vectors are written down in
  this file. The cosine similarities, the softmax over them and every score
  derived from them are then real arithmetic on those made-up vectors. A real
  model has hundreds of directions and none of them has a name.
* The counts of how many detector classes cover a workshop tray, and the
  labelling-time arithmetic, come from two lists written down in this file.
* The learning curve for few-shot learning, the spread of top scores when an
  object is present or absent, the stereo matching patches, the projected-dot
  visibility per surface and the simulated scene point cloud all come from
  numpy.random.default_rng with a fixed seed, and the pages say so.
* All the camera arithmetic is real: the pinhole projection, the scale
  ambiguity, the affine alignment of relative depth, the stereo disparity and
  its error, the pixel-to-point projection, the voxel counts and memory, the
  volume-rendering of the two-dimensional blob scene and the query counts.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, Ellipse, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'models-that-see'
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

OV_DOC: str = 'open-vocabulary-vision'
D3_DOC: str = 'depth-and-3d'

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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _cos(a: Arr, b: Arr) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def _mug(ax: Axes, x: float, y: float, w: float = 0.52, h: float = 0.62,
         colour: str = '#f4f4f4', handle: bool = True, lw: float = 1.3) -> None:
    ax.add_patch(Rectangle((x - w / 2, y), w, h, fc=colour, ec=INK, lw=lw, zorder=3))
    ax.add_patch(Ellipse((x, y + h), w, h * 0.22, fc='#ffffff', ec=INK, lw=lw, zorder=4))
    if handle:
        ax.add_patch(Arc((x + w / 2, y + h * 0.52), w * 0.62, h * 0.52,
                         theta1=-78, theta2=78, ec=INK, lw=2.2, zorder=3))


def _bowl(ax: Axes, x: float, y: float, w: float = 0.78, h: float = 0.34,
          colour: str = '#eceff4') -> None:
    th = np.linspace(np.pi, 2 * np.pi, 60)
    pts = np.column_stack([x + w / 2 * np.cos(th), y + h + h * np.sin(th)])
    ax.add_patch(Polygon(pts, closed=True, fc=colour, ec=INK, lw=1.3, zorder=3))
    ax.add_patch(Ellipse((x, y + h), w, h * 0.5, fc='#ffffff', ec=INK, lw=1.3, zorder=4))


def _tin(ax: Axes, x: float, y: float, w: float = 0.44, h: float = 0.50) -> None:
    ax.add_patch(Rectangle((x - w / 2, y), w, h, fc='#cfd6dd', ec=INK, lw=1.3, zorder=3))
    ax.add_patch(Ellipse((x, y + h), w, h * 0.22, fc='#e6ebf0', ec=INK, lw=1.3, zorder=4))


def _glass(ax: Axes, x: float, y: float, w: float = 0.42, h: float = 0.66) -> None:
    ax.add_patch(Polygon([[x - w / 2 * 0.82, y], [x + w / 2 * 0.82, y],
                          [x + w / 2, y + h], [x - w / 2, y + h]],
                         closed=True, fc='#dff0f4', ec=TEAL, lw=1.3, alpha=0.75, zorder=3))


# ==========================================================================
# PAGE 3: the made-up shared picture-and-text space
# ==========================================================================

AXES: list[str] = ['handle', 'round body', 'open top', 'ceramic', 'see-through',
                   'metal', 'holds drink', 'holds food', 'red',
                   'is a relation', 'order in depth', 'how many', 'is a denial']
APPEARANCE: int = 9      # the first nine directions are the ones a picture can show
NDIM: int = len(AXES)


def _vec(**kw: float) -> Arr:
    v = np.zeros(NDIM)
    for key, value in kw.items():
        name = key.replace('_', ' ')
        if name not in AXES:
            name = key.replace('_', '-')
        v[AXES.index(name)] = value
    return v


WORDS: dict[str, Arr] = {
    'mug': _vec(handle=0.90, round_body=0.70, open_top=0.80, ceramic=0.70,
                holds_drink=0.90, holds_food=0.10),
    'cup': _vec(handle=0.35, round_body=0.80, open_top=0.90, ceramic=0.60,
                see_through=0.10, holds_drink=1.00, holds_food=0.10),
    'bowl': _vec(round_body=0.90, open_top=1.00, ceramic=0.70,
                 holds_drink=0.20, holds_food=0.90),
    'glass': _vec(round_body=0.80, open_top=0.90, see_through=0.90,
                  holds_drink=0.95, holds_food=0.10),
    'tin can': _vec(round_body=0.90, open_top=0.10, metal=0.90,
                    holds_drink=0.30, holds_food=0.80),
    'jug': _vec(handle=0.80, round_body=0.60, open_top=0.70, ceramic=0.40,
                see_through=0.10, holds_drink=0.85, holds_food=0.10),
    'red': _vec(red=1.00),
    'behind': _vec(is_a_relation=0.90, order_in_depth=0.80),
    'in front of': _vec(is_a_relation=0.90, order_in_depth=-0.80),
    'two': _vec(how_many=0.90),
    'three': _vec(how_many=0.95),
    'not': _vec(is_a_denial=1.00),
}

REGIONS: dict[str, Arr] = {
    'white mug, handle hidden': _vec(handle=0.22, round_body=0.80, open_top=0.85,
                                     ceramic=0.75, see_through=0.05,
                                     holds_drink=0.90, holds_food=0.15),
    'white mug, handle in view': _vec(handle=0.85, round_body=0.78, open_top=0.84,
                                      ceramic=0.75, see_through=0.05,
                                      holds_drink=0.90, holds_food=0.15),
    'white bowl': _vec(handle=0.06, round_body=0.90, open_top=0.96, ceramic=0.68,
                       holds_drink=0.30, holds_food=0.82),
    'glass tumbler': _vec(round_body=0.75, open_top=0.86, ceramic=0.05,
                          see_through=0.72, holds_drink=0.90, holds_food=0.14),
    'tin of beans': _vec(round_body=0.84, open_top=0.12, see_through=0.04,
                         metal=0.80, holds_drink=0.28, holds_food=0.78),
    'red mug, handle in view': _vec(handle=0.85, round_body=0.78, open_top=0.84,
                                    ceramic=0.75, see_through=0.05,
                                    holds_drink=0.90, holds_food=0.15, red=0.95),
    'blue mug, handle in view': _vec(handle=0.85, round_body=0.78, open_top=0.84,
                                     ceramic=0.75, see_through=0.05,
                                     holds_drink=0.90, holds_food=0.15, red=0.02),
}

NAMES6: list[str] = ['mug', 'cup', 'bowl', 'glass', 'tin can', 'jug']


def _phrase(*words: str) -> Arr:
    return np.mean([WORDS[w] for w in words], axis=0)


# --------------------------------------------------------------------------
# section 1: a fixed list of names runs out
# --------------------------------------------------------------------------

DETECTOR_LIST: list[str] = [
    'person', 'bottle', 'cup', 'bowl', 'banana', 'apple', 'orange', 'knife',
    'spoon', 'fork', 'scissors', 'book', 'cell phone', 'remote', 'keyboard',
    'mouse', 'chair', 'dining table', 'vase', 'teddy bear']

TRAY: list[str] = [
    'cup', 'bowl', 'spoon', 'fork', 'bottle', 'book',
    'hex key', 'cable tie', 'zip-lock bag', 'calibration board',
    'spare gripper finger', 'pipette tip', 'tube of thermal paste', 'hex nut']


def closed_list() -> None:
    """How much of a workshop tray a fixed class list covers."""
    on = [t for t in TRAY if t in DETECTOR_LIST]
    off = [t for t in TRAY if t not in DETECTOR_LIST]
    frac = len(on) / len(TRAY)
    print(f'[closed-list] tray items {len(TRAY)}, on the list {len(on)}, '
          f'not on the list {len(off)}, covered {frac * 100:.1f}%')
    print(f'[closed-list] on  : {", ".join(on)}')
    print(f'[closed-list] off : {", ".join(off)}')

    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.0)
    for i, item in enumerate(TRAY):
        row, col = i % 7, i // 7
        x, y = 0.3 + col * 4.9, 6.4 - row * 0.86
        known = item in DETECTOR_LIST
        ax.add_patch(Rectangle((x, y), 4.3, 0.64, fc=LINK_PALE if known else '#fbe3e3',
                               ec=LINK if known else GRIP, lw=1.1))
        ax.text(x + 0.26, y + 0.32, 'yes' if known else 'no', fontsize=9.5,
                color=LINK if known else GRIP, va='center', weight='bold')
        ax.text(x + 0.95, y + 0.32, item, fontsize=10, color=INK, va='center')
    ax.text(5.0, 7.5, 'A tray of 14 things in a robot workshop, checked against a '
                      'detector trained on 20 names',
            fontsize=12, weight='bold', ha='center', color=INK)
    ax.text(5.0, 0.55, f'{len(on)} of {len(TRAY)} things have a name on the list, '
                       f'which is {frac * 100:.1f}%. The other {len(off)} cannot be '
                       'reported at all.',
            fontsize=11, ha='center', color=INK)
    ax.text(5.0, 0.05, 'The mug on the tray is counted here as "cup", because '
                       '"mug" is not one of the 20 names.',
            fontsize=9.5, ha='center', color=MUTED)
    _save(fig, OV_DOC, 'closed-list.svg')


def list_growth() -> None:
    """What it costs in labelling time to make the list longer."""
    boxes_per_class, seconds_per_box = 150, 18
    minutes_per_class = boxes_per_class * seconds_per_box / 60.0
    sizes = np.arange(80, 201, 20)
    hours = (sizes - 80) * minutes_per_class / 60.0
    print(f'[list-growth] {boxes_per_class} boxes a class x {seconds_per_box} s '
          f'= {minutes_per_class:.0f} minutes a class')
    for s, h in zip(sizes, hours):
        print(f'[list-growth] list of {s} names -> {h:.1f} labelling hours added')

    fig, ax = plt.subplots(figsize=(9.6, 4.8), facecolor='white')
    _plain(ax)
    ax.bar(sizes, hours, width=14, color=LINK, ec=INK, lw=0.8)
    for s, h in zip(sizes, hours):
        ax.text(s, h + 1.2, f'{h:.0f} h', ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(sizes)
    ax.set_xlabel('how many names the detector can report', fontsize=10)
    ax.set_ylabel('labelling hours added', fontsize=10)
    ax.set_ylim(0, hours.max() * 1.22)
    ax.set_title(f'Each new name costs {minutes_per_class:.0f} minutes of boxing '
                 f'({boxes_per_class} boxes at {seconds_per_box} s each), '
                 'plus a retrain',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'list-growth.svg')


def shots_curve() -> None:
    """Zero-shot, few-shot and the full training set, on a simulated curve."""
    rng = np.random.default_rng(11)
    n = np.array([1, 2, 5, 10, 20, 50, 100, 200])
    acc = 0.94 - 0.52 * np.exp(-n / 14.0) + rng.normal(0, 0.006, size=n.size)
    zero = 0.61
    crossing = int(n[np.argmax(acc > zero)])
    print(f'[shots] zero-shot (no examples at all) = {zero:.2f}')
    for k, a in zip(n, acc):
        print(f'[shots] {k:3d} examples a class -> {a:.3f} (simulated)')
    print(f'[shots] the curve first passes the zero-shot line at {crossing} examples '
          'a class')

    fig, ax = plt.subplots(figsize=(9.8, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(n, acc, marker='o', color=LINK, lw=2.2, label='trained on examples of the new name')
    ax.axhline(zero, color=GRIP, lw=2.2, ls='--',
               label='zero-shot: the name only, no examples')
    ax.annotate(f'five examples: {acc[2]:.2f}', xy=(5, acc[2]), xytext=(7.5, acc[2] - 0.10),
                fontsize=9.5, color=PURPLE,
                arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.3))
    ax.annotate(f'zero-shot: {zero:.2f}', xy=(1.6, zero), xytext=(1.3, zero + 0.09),
                fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.3))
    ax.set_xscale('log')
    ax.set_xticks(n)
    ax.set_xticklabels([str(k) for k in n])
    ax.set_ylim(0.45, 1.0)
    ax.set_xlabel('labelled examples of the new name (log scale)', fontsize=10)
    ax.set_ylabel('share of pictures named correctly', fontsize=10)
    ax.set_title(f'Simulated: zero-shot beats a handful of examples, and the curve '
                 f'only passes it at {crossing} examples a class',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, OV_DOC, 'shots-curve.svg')


# --------------------------------------------------------------------------
# section 2: one space for pictures and words
# --------------------------------------------------------------------------

def thirteen_directions() -> None:
    """The made-up table that every later number on the page comes from."""
    rows = NAMES6 + ['white mug, handle hidden', 'white mug, handle in view']
    mat = np.array([(WORDS[r] if r in WORDS else REGIONS[r])[:APPEARANCE - 1] for r in rows])
    print('[table] the first eight directions of the made-up space')
    for r, v in zip(rows, mat):
        print(f'[table] {r:28s} ' + ' '.join(f'{x:.2f}' for x in v))

    fig, ax = plt.subplots(figsize=(10.8, 4.9), facecolor='white')
    ax.imshow(mat, cmap='Blues', vmin=0, vmax=1.0, aspect='auto')
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f'{mat[i, j]:.2f}', ha='center', va='center', fontsize=9,
                    color='white' if mat[i, j] > 0.55 else INK)
    ax.set_xticks(range(APPEARANCE - 1))
    ax.set_xticklabels(AXES[:APPEARANCE - 1], fontsize=9.5, rotation=28, ha='right')
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f'word "{r}"' if r in WORDS else f'region: {r}' for r in rows],
                       fontsize=9.5)
    ax.axhline(5.5, color=GRIP, lw=2.4)
    ax.set_title('The made-up shared space: six words above the red line, two '
                 'picture regions below it',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'shared-space-table.svg')


def cosine_arithmetic() -> None:
    """The dot product, the two lengths and the cosine, written out."""
    pic = REGIONS['white mug, handle hidden']
    a, b = WORDS['mug'], WORDS['cup']
    pa, pb = pic[:8] * a[:8], pic[:8] * b[:8]
    cos_a, cos_b = _cos(pic, a), _cos(pic, b)
    print(f'[cosine] |picture| = {np.linalg.norm(pic):.4f}  '
          f'|mug| = {np.linalg.norm(a):.4f}  |cup| = {np.linalg.norm(b):.4f}')
    print(f'[cosine] dot with "mug" = {pic @ a:.4f}, dot with "cup" = {pic @ b:.4f}')
    print(f'[cosine] cosine with "mug" = {cos_a:.4f}, with "cup" = {cos_b:.4f}')

    fig, ax = plt.subplots(figsize=(10.6, 6.1), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    cols = [0.45, 3.55, 5.15, 6.55, 7.95, 9.35]
    heads = ['direction', 'picture', 'word "mug"', 'product', 'word "cup"', 'product']
    for x, h in zip(cols, heads):
        ax.text(x, 8.55, h, fontsize=10, weight='bold', color=INK,
                ha='left' if x < 1 else 'center')
    ax.plot([0.3, 9.7], [8.35, 8.35], color=INK, lw=1.2)
    for i in range(8):
        y = 7.85 - i * 0.62
        ax.text(cols[0], y, AXES[i], fontsize=9.8, color=INK, va='center')
        ax.text(cols[1], y, f'{pic[i]:.2f}', fontsize=9.8, ha='center', va='center')
        ax.text(cols[2], y, f'{a[i]:.2f}', fontsize=9.8, ha='center', va='center')
        ax.text(cols[3], y, f'{pa[i]:.3f}', fontsize=9.8, ha='center', va='center',
                color=LINK)
        ax.text(cols[4], y, f'{b[i]:.2f}', fontsize=9.8, ha='center', va='center')
        ax.text(cols[5], y, f'{pb[i]:.3f}', fontsize=9.8, ha='center', va='center',
                color=PURPLE)
    ax.plot([0.3, 9.7], [2.68, 2.68], color=INK, lw=1.2)
    ax.text(cols[0], 2.28, 'added up', fontsize=9.8, weight='bold', va='center')
    ax.text(cols[3], 2.28, f'{pa.sum():.3f}', fontsize=10.2, ha='center', va='center',
            weight='bold', color=LINK)
    ax.text(cols[5], 2.28, f'{pb.sum():.3f}', fontsize=10.2, ha='center', va='center',
            weight='bold', color=PURPLE)
    ax.text(cols[0], 1.62, 'divided by the two lengths', fontsize=9.8, va='center')
    ax.text(cols[3], 1.62, f'{np.linalg.norm(pic):.3f} x {np.linalg.norm(a):.3f}',
            fontsize=9.3, ha='center', va='center', color=LINK)
    ax.text(cols[5], 1.62, f'{np.linalg.norm(pic):.3f} x {np.linalg.norm(b):.3f}',
            fontsize=9.3, ha='center', va='center', color=PURPLE)
    ax.text(cols[0], 0.92, 'cosine similarity', fontsize=10, weight='bold', va='center')
    ax.text(cols[3], 0.92, f'{cos_a:.4f}', fontsize=11.5, ha='center', va='center',
            weight='bold', color=LINK)
    ax.text(cols[5], 0.92, f'{cos_b:.4f}', fontsize=11.5, ha='center', va='center',
            weight='bold', color=PURPLE)
    ax.text(5.0, 0.22, f'"cup" wins by {cos_b - cos_a:.4f}, because the one direction '
                       'that separates the two words is the handle, and the handle is '
                       'hidden in this view.',
            fontsize=10, ha='center', color=GRIP)
    ax.set_title('Scoring one region against two words, every product written out',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'cosine-arithmetic.svg')


def nearest_name() -> None:
    """The six candidate names ranked against the hidden-handle region."""
    pic = REGIONS['white mug, handle hidden']
    scores = np.array([_cos(pic, WORDS[n]) for n in NAMES6])
    order = np.argsort(-scores)
    for i in order:
        print(f'[nearest] "{NAMES6[i]}" -> {scores[i]:.4f}')

    fig, ax = plt.subplots(figsize=(9.8, 4.9), facecolor='white')
    _plain(ax)
    names = [NAMES6[i] for i in order]
    vals = scores[order]
    colours = [GRIP if n == 'cup' else (SLIDE if n == 'mug' else LINK) for n in names]
    ax.barh(range(len(names))[::-1], vals, color=colours, ec=INK, lw=0.8, height=0.6)
    for k, (n, v) in enumerate(zip(names, vals)):
        ax.text(v + 0.006, len(names) - 1 - k, f'{v:.4f}', va='center', fontsize=10)
    ax.set_yticks(range(len(names))[::-1])
    ax.set_yticklabels([f'"{n}"' for n in names], fontsize=11)
    ax.set_xlim(0, 1.06)
    ax.set_xlabel('cosine similarity with the picture region', fontsize=10)
    ax.set_title('The closest name to a mug with its handle hidden is "cup", '
                 'and the right answer is second',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'nearest-name.svg')


def handle_in_view() -> None:
    """The same six names against the same mug, handle hidden and handle visible."""
    hid = REGIONS['white mug, handle hidden']
    vis = REGIONS['white mug, handle in view']
    s_hid = np.array([_cos(hid, WORDS[n]) for n in NAMES6])
    s_vis = np.array([_cos(vis, WORDS[n]) for n in NAMES6])
    print('[handle] name      hidden   in view')
    for n, h, v in zip(NAMES6, s_hid, s_vis):
        print(f'[handle] {n:9s} {h:.4f}  {v:.4f}')
    print(f'[handle] hidden: best is "{NAMES6[int(np.argmax(s_hid))]}"; '
          f'in view: best is "{NAMES6[int(np.argmax(s_vis))]}"')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(NAMES6))
    ax.bar(x - 0.19, s_hid, width=0.36, color=GRIP, ec=INK, lw=0.8, label='handle hidden')
    ax.bar(x + 0.19, s_vis, width=0.36, color=SLIDE, ec=INK, lw=0.8, label='handle in view')
    for i in range(len(NAMES6)):
        ax.text(x[i] - 0.19, s_hid[i] + 0.008, f'{s_hid[i]:.3f}', ha='center', fontsize=8.6)
        ax.text(x[i] + 0.19, s_vis[i] + 0.008, f'{s_vis[i]:.3f}', ha='center', fontsize=8.6)
    ax.set_xticks(x)
    ax.set_xticklabels([f'"{n}"' for n in NAMES6], fontsize=10.5)
    ax.set_ylim(0, 1.28)
    ax.set_ylabel('cosine similarity', fontsize=10)
    ax.set_title('Turning the mug by 90 degrees moves "mug" from second place to first',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper center', ncol=2)
    _save(fig, OV_DOC, 'handle-in-view.svg')


def scaled_softmax() -> None:
    """A small gap in cosine becomes a large gap in reported confidence."""
    pic = REGIONS['white mug, handle hidden']
    scores = np.array([_cos(pic, WORDS[n]) for n in NAMES6])
    out = {}
    for scale in (1.0, 20.0, 100.0):
        z = scores * scale
        p = np.exp(z - z.max())
        out[scale] = p / p.sum()
        print(f'[softmax] scale {scale:5.0f} -> ' +
              '  '.join(f'{n}:{v * 100:.1f}%' for n, v in zip(NAMES6, out[scale])))
    gap = scores.max() - np.sort(scores)[-2]
    print(f'[softmax] cosine gap between the top two = {gap:.4f}; at scale 100 the '
          f'top name is reported as {out[100.0].max() * 100:.1f}%')

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.7), facecolor='white',
                             gridspec_kw={'wspace': 0.26})
    _plain(axes[0])
    axes[0].bar(NAMES6, scores, color=LINK, ec=INK, lw=0.8)
    for i, v in enumerate(scores):
        axes[0].text(i, v + 0.008, f'{v:.3f}', ha='center', fontsize=9)
    axes[0].set_ylim(0, 1.08)
    axes[0].set_ylabel('cosine similarity', fontsize=10)
    axes[0].set_title(f'The raw scores sit in a narrow band\n(top two differ by {gap:.4f})',
                      fontsize=11.5, weight='bold')
    axes[0].tick_params(axis='x', labelrotation=24)
    _plain(axes[1])
    p = out[100.0] * 100
    axes[1].bar(NAMES6, p, color=PURPLE, ec=INK, lw=0.8)
    for i, v in enumerate(p):
        axes[1].text(i, v + 2.0, f'{v:.1f}%', ha='center', fontsize=9)
    axes[1].set_ylim(0, 118)
    axes[1].set_ylabel('reported confidence', fontsize=10)
    axes[1].set_title('After multiplying by 100 and taking a softmax,\nthe same gap '
                      'looks like certainty',
                      fontsize=11.5, weight='bold')
    axes[1].tick_params(axis='x', labelrotation=24)
    _save(fig, OV_DOC, 'scaled-softmax.svg')


# --------------------------------------------------------------------------
# section 3: detection and segmentation without a list
# --------------------------------------------------------------------------

SCENE_REGIONS: list[str] = ['white mug, handle in view', 'white bowl',
                            'glass tumbler', 'tin of beans', 'red mug, handle in view']


def proposals_and_names() -> None:
    """Five proposed boxes on a tray, each given its closest name."""
    best = []
    for r in SCENE_REGIONS:
        s = np.array([_cos(REGIONS[r], WORDS[n]) for n in NAMES6])
        k = int(np.argmax(s))
        best.append((NAMES6[k], float(s[k])))
        print(f'[proposals] region "{r}" -> best name "{NAMES6[k]}" at {s[k]:.4f}')

    fig, ax = plt.subplots(figsize=(10.6, 3.9), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.9)
    ax.add_patch(Rectangle((0.2, 0.55), 9.6, 0.26, fc='#e8e2d8', ec=INK, lw=1.1))
    xs = [1.3, 3.2, 5.0, 6.7, 8.5]
    _mug(ax, xs[0], 0.81)
    _bowl(ax, xs[1], 0.81)
    _glass(ax, xs[2], 0.81)
    _tin(ax, xs[3], 0.81)
    _mug(ax, xs[4], 0.81, colour='#f0b1b1')
    widths = [0.95, 1.05, 0.72, 0.70, 0.95]
    heights = [0.90, 0.60, 0.76, 0.62, 0.90]
    for x, w, h, (name, score) in zip(xs, widths, heights, best):
        ax.add_patch(Rectangle((x - w / 2, 0.76), w, h, fill=False, ec=LINK, lw=1.8))
        ax.text(x, 0.76 + h + 0.16, f'"{name}"', ha='center', fontsize=10.5,
                color=LINK, weight='bold')
        ax.text(x, 0.76 + h + 0.46, f'{score:.3f}', ha='center', fontsize=9.5, color=INK)
    ax.text(5.0, 2.68, 'A region proposer draws five boxes, and each box is given '
                       'the closest of six names',
            fontsize=12, weight='bold', ha='center')
    ax.text(5.0, 0.18, 'Nothing in this picture was a training class. The names come '
                       'only from the six text vectors.',
            fontsize=10, ha='center', color=MUTED)
    _save(fig, OV_DOC, 'proposals-and-names.svg')


def score_matrix() -> None:
    """Every region against every name."""
    mat = np.array([[_cos(REGIONS[r], WORDS[n]) for n in NAMES6] for r in SCENE_REGIONS])
    print('[matrix] rows = regions, columns = names')
    for r, row in zip(SCENE_REGIONS, mat):
        print(f'[matrix] {r:26s} ' + ' '.join(f'{v:.3f}' for v in row))
    print(f'[matrix] lowest value in the whole table = {mat.min():.3f}, '
          f'highest = {mat.max():.3f}')

    fig, ax = plt.subplots(figsize=(10.2, 4.6), facecolor='white')
    ax.imshow(mat, cmap='Blues', vmin=0.4, vmax=1.0, aspect='auto')
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            top = j == int(np.argmax(mat[i]))
            ax.text(j, i, f'{mat[i, j]:.3f}', ha='center', va='center',
                    fontsize=9.6, weight='bold' if top else 'normal',
                    color='white' if mat[i, j] > 0.78 else INK)
            if top:
                ax.add_patch(Rectangle((j - 0.47, i - 0.44), 0.94, 0.88,
                                       fill=False, ec=GRIP, lw=2.2))
    ax.set_xticks(range(len(NAMES6)))
    ax.set_xticklabels([f'"{n}"' for n in NAMES6], fontsize=10)
    ax.set_yticks(range(len(SCENE_REGIONS)))
    ax.set_yticklabels(SCENE_REGIONS, fontsize=9.5)
    ax.set_title('The whole score table: the red ring marks each region\'s best name, '
                 'and no score is small',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'score-matrix.svg')


def threshold_sweep() -> None:
    """Raising the keep-it threshold trades missed objects against wrong ones."""
    rng = np.random.default_rng(5)
    present = rng.normal(0.935, 0.018, size=40)
    absent = rng.normal(0.893, 0.026, size=120)
    ths = np.arange(0.86, 0.981, 0.01)
    kept_right = np.array([(present >= t).sum() for t in ths])
    kept_wrong = np.array([(absent >= t).sum() for t in ths])
    for t, r, w in zip(ths, kept_right, kept_wrong):
        print(f'[sweep] threshold {t:.2f} -> kept {r:2d}/40 right, {w:3d}/120 wrong '
              '(simulated)')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white',
                             gridspec_kw={'wspace': 0.28})
    _plain(axes[0])
    bins = np.linspace(0.80, 1.00, 34)
    axes[0].hist(absent, bins=bins, color=GRIP, alpha=0.75, label='the named thing is absent')
    axes[0].hist(present, bins=bins, color=SLIDE, alpha=0.75, label='the named thing is there')
    axes[0].axvline(0.92, color=INK, lw=1.8, ls='--')
    axes[0].text(0.921, axes[0].get_ylim()[1] * 0.92, 'threshold 0.92', fontsize=9.5)
    axes[0].set_xlabel('best score in the picture', fontsize=10)
    axes[0].set_ylabel('how many pictures', fontsize=10)
    axes[0].set_title('Simulated: the two cases overlap', fontsize=11.5, weight='bold')
    axes[0].legend(fontsize=9, frameon=False, loc='upper left')
    _plain(axes[1])
    axes[1].plot(ths, kept_right / 40 * 100, marker='o', color=SLIDE, lw=2,
                 label='right boxes kept (% of 40)')
    axes[1].plot(ths, kept_wrong / 120 * 100, marker='s', color=GRIP, lw=2,
                 label='wrong boxes kept (% of 120)')
    axes[1].set_xlabel('keep-it threshold', fontsize=10)
    axes[1].set_ylabel('percentage kept', fontsize=10)
    axes[1].set_title('No threshold separates them', fontsize=11.5, weight='bold')
    axes[1].legend(fontsize=9, frameon=False)
    _save(fig, OV_DOC, 'threshold-sweep.svg')


def box_to_mask() -> None:
    """The box the matching gives is not the shape the gripper needs."""
    h, w = 100, 120
    yy, xx = np.mgrid[0:h, 0:w]
    body = ((xx - 46) / 30.0) ** 2 + ((yy - 50) / 42.0) ** 2 <= 1.0
    ring = ((xx - 86) / 22.0) ** 2 + ((yy - 50) / 24.0) ** 2
    handle = (ring <= 1.0) & (ring >= 0.42) & (xx >= 74)
    mask = body | handle
    c0, c1 = int(xx[mask].min()), int(xx[mask].max())
    r0, r1 = int(yy[mask].min()), int(yy[mask].max())
    bw, bh = c1 - c0 + 1, r1 - r0 + 1
    box_area, mask_area = bw * bh, int(mask.sum())
    cx_box, cy_box = (c0 + c1) / 2, (r0 + r1) / 2
    cx_mask, cy_mask = float(xx[mask].mean()), float(yy[mask].mean())
    shift = float(np.hypot(cx_box - cx_mask, cy_box - cy_mask))
    fx, z = 615.0, 0.42
    mm_per_pixel = z / fx * 1000.0
    print(f'[mask] the tight box is {bw} by {bh} = {box_area} pixels, '
          f'the mask is {mask_area} pixels '
          f'({mask_area / box_area * 100:.1f}% of the box)')
    print(f'[mask] box centre ({cx_box:.1f}, {cy_box:.1f}), '
          f'mask centre ({cx_mask:.1f}, {cy_mask:.1f}), shift {shift:.1f} pixels')
    print(f'[mask] at {z:.2f} m with fx = {fx:.0f} px, one pixel is '
          f'{mm_per_pixel:.3f} mm, so the shift is {shift * mm_per_pixel:.1f} mm')

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white',
                             gridspec_kw={'wspace': 0.18})
    for ax, show_mask in zip(axes, (False, True)):
        ax.set_facecolor('white')
        ax.imshow(mask if show_mask else np.zeros_like(mask), cmap='Blues',
                  vmin=0, vmax=1.6)
        ax.add_patch(Rectangle((c0 - 0.5, r0 - 0.5), bw, bh, fill=False, ec=LINK,
                               lw=2.4))
        if not show_mask:
            ax.contour(mask.astype(float), levels=[0.5], colors=[MUTED], linewidths=1.0)
        ax.plot([cx_box], [cy_box], marker='x', color=LINK, ms=12, mew=2.6)
        if show_mask:
            ax.plot([cx_mask], [cy_mask], marker='o', color=GRIP, ms=9)
            ax.plot([cx_box, cx_mask], [cy_box, cy_mask], color=GRIP, lw=1.6)
        ax.set_xticks([])
        ax.set_yticks([])
    axes[0].set_title(f'The box: {bw} x {bh} = {box_area} pixels,\ncentre marked with '
                      'a cross',
                      fontsize=11.5, weight='bold')
    axes[1].set_title(f'The mask: {mask_area} pixels, '
                      f'{mask_area / box_area * 100:.1f}% of the box,\ncentre '
                      f'{shift:.1f} px away = {shift * mm_per_pixel:.1f} mm on the table',
                      fontsize=11.5, weight='bold')
    _save(fig, OV_DOC, 'box-to-mask.svg')


# --------------------------------------------------------------------------
# section 4: grounding a phrase to a region
# --------------------------------------------------------------------------

MUG_A: tuple[float, float, float] = (0.055, 0.020, 0.760)    # x, y, z in metres
MUG_B: tuple[float, float, float] = (-0.070, 0.015, 0.455)
BOWL_C: tuple[float, float, float] = (-0.010, 0.000, 0.590)


def two_mugs_scene() -> None:
    """The scene the phrase has to pick from, in plan and in camera view."""
    print(f'[scene] mug A at z = {MUG_A[2]:.3f} m, bowl at z = {BOWL_C[2]:.3f} m, '
          f'mug B at z = {MUG_B[2]:.3f} m')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), facecolor='white',
                             gridspec_kw={'wspace': 0.24})
    ax = axes[0]
    _plain(ax)
    ax.plot([0], [0], marker='^', color=INK, ms=13)
    ax.text(0, -0.045, 'camera', fontsize=9.5, ha='center')
    for (x, _y, z), lab, col in ((MUG_A, 'mug A', LINK), (BOWL_C, 'bowl', JOINT),
                                 (MUG_B, 'mug B', PURPLE)):
        ax.add_patch(Circle((x, z), 0.035, fc=col, ec=INK, lw=1.1, alpha=0.85))
        ax.text(x + 0.055, z, f'{lab}\nz = {z:.3f} m', fontsize=9.5, va='center')
    ax.plot([0, 0.17], [0, 0.95], color=GRID, lw=1.2)
    ax.plot([0, -0.17], [0, 0.95], color=GRID, lw=1.2)
    ax.set_xlim(-0.26, 0.26)
    ax.set_ylim(-0.08, 0.95)
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('distance from the camera z (m)', fontsize=10)
    ax.set_title('Seen from above: mug A is further than the bowl,\nmug B is nearer',
                 fontsize=11.5, weight='bold')

    ax = axes[1]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.3)
    ax.add_patch(Polygon([[0.3, 0.55], [9.7, 0.55], [8.0, 2.45], [2.0, 2.45]],
                         closed=True, fc='#e8e2d8', ec=INK, lw=1.0))
    _mug(ax, 6.3, 2.05, w=0.34, h=0.40)
    ax.text(6.3, 2.60, 'mug A', fontsize=9.5, ha='center', color=LINK)
    _bowl(ax, 4.6, 1.30, w=1.20, h=0.50)
    ax.text(4.6, 2.00, 'bowl', fontsize=9.5, ha='center', color=JOINT)
    _mug(ax, 2.6, 0.70, w=0.72, h=0.86)
    ax.text(2.6, 1.72, 'mug B', fontsize=9.5, ha='center', color=PURPLE)
    ax.text(5.0, 4.05, 'The same scene from the camera: both mugs are whole mugs, '
                       'and both look alike',
            fontsize=11.5, weight='bold', ha='center')
    ax.text(5.0, 3.50, 'phrase to ground: "the mug behind the bowl"', fontsize=11,
            ha='center', color=GRIP, weight='bold')
    ax.text(5.0, 0.12, 'A mug that is further away is drawn smaller and higher up, '
                       'which is the only clue in the flat picture.',
            fontsize=9.5, ha='center', color=MUTED)
    _save(fig, OV_DOC, 'two-mugs-scene.svg')


def noun_cannot_choose() -> None:
    """The phrase scores the two identical-looking mugs identically."""
    reg = REGIONS['white mug, handle in view']
    p_behind = _phrase('mug', 'behind', 'bowl')
    p_front = _phrase('mug', 'in front of', 'bowl')
    just_mug = WORDS['mug']
    s_behind = _cos(reg, p_behind)
    s_front = _cos(reg, p_front)
    s_mug = _cos(reg, just_mug)
    print(f'[noun] "mug" alone against a mug region   = {s_mug:.4f}')
    print(f'[noun] "the mug behind the bowl"          = {s_behind:.4f}')
    print(f'[noun] "the mug in front of the bowl"     = {s_front:.4f}')
    print(f'[noun] the two phrases differ by {abs(s_behind - s_front):.6f}, '
          'and both mugs get the same score')

    fig, ax = plt.subplots(figsize=(10.0, 4.7), facecolor='white')
    _plain(ax)
    labels = ['mug A\n"behind the bowl"', 'mug B\n"behind the bowl"',
              'mug A\n"in front of the bowl"', 'mug B\n"in front of the bowl"']
    vals = [s_behind, s_behind, s_front, s_front]
    ax.bar(labels, vals, color=[LINK, PURPLE, LINK, PURPLE], ec=INK, lw=0.8)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.006, f'{v:.4f}', ha='center', fontsize=10)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('cosine similarity', fontsize=10)
    ax.set_title('Matching alone gives all four combinations the same score, '
                 'so it cannot ground the phrase',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'noun-cannot-choose.svg')


def relation_from_geometry() -> None:
    """Working the relation out from the measured distances instead."""
    za, zb, zc = MUG_A[2], MUG_B[2], BOWL_C[2]
    da, db = za - zc, zb - zc
    reg = REGIONS['white mug, handle in view']
    match = _cos(reg, _phrase('mug', 'behind', 'bowl'))
    rel_a = 1.0 if da > 0 else 0.0
    rel_b = 1.0 if db > 0 else 0.0
    comb_a = 0.6 * match + 0.4 * rel_a
    comb_b = 0.6 * match + 0.4 * rel_b
    print(f'[relation] mug A is {da * 1000:.0f} mm further than the bowl, '
          f'mug B is {db * 1000:.0f} mm further')
    print(f'[relation] match score {match:.4f} for both; '
          f'relation 1 for A and 0 for B')
    print(f'[relation] combined 0.6 x match + 0.4 x relation: '
          f'A = {comb_a:.4f}, B = {comb_b:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white',
                             gridspec_kw={'wspace': 0.3, 'width_ratios': [1.15, 1]})
    ax = axes[0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.0)
    rows = [('mug A', za, da, rel_a, comb_a, LINK), ('mug B', zb, db, rel_b, comb_b, PURPLE)]
    heads = ['', 'z (m)', 'z minus bowl z', 'behind?', 'combined']
    xs = [0.2, 2.2, 3.8, 6.9, 8.8]
    for x, hd in zip(xs, heads):
        ax.text(x, 5.3, hd, fontsize=10, weight='bold', ha='left')
    ax.plot([0.2, 9.8], [5.05, 5.05], color=INK, lw=1.1)
    ax.text(xs[0], 4.55, f'bowl', fontsize=10, color=JOINT, weight='bold')
    ax.text(xs[1], 4.55, f'{zc:.3f}', fontsize=10)
    for k, (lab, z, d, rel, comb, col) in enumerate(rows):
        y = 3.75 - k * 0.85
        ax.text(xs[0], y, lab, fontsize=10, color=col, weight='bold')
        ax.text(xs[1], y, f'{z:.3f}', fontsize=10)
        ax.text(xs[2], y, f'{d * 1000:+.0f} mm', fontsize=10,
                color=SLIDE if d > 0 else GRIP)
        ax.text(xs[3], y, 'yes' if rel > 0 else 'no', fontsize=10,
                color=SLIDE if rel > 0 else GRIP, weight='bold')
        ax.text(xs[4], y, f'{comb:.3f}', fontsize=10.5, weight='bold', color=col)
    ax.text(0.3, 1.7, 'The relation is decided by subtracting two measured distances,\n'
                      'not by matching the phrase to the picture.',
            fontsize=10, color=INK)
    ax.text(0.3, 0.6, f'combined score = 0.6 x {match:.3f} + 0.4 x (1 or 0)',
            fontsize=10, color=MUTED)
    ax.set_title('Grounding "the mug behind the bowl" with geometry',
                 fontsize=11.5, weight='bold')

    ax = axes[1]
    _plain(ax)
    ax.bar(['mug A', 'mug B'], [comb_a, comb_b], color=[LINK, PURPLE], ec=INK, lw=0.9)
    for i, v in enumerate([comb_a, comb_b]):
        ax.text(i, v + 0.012, f'{v:.3f}', ha='center', fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('combined score', fontsize=10)
    ax.set_title(f'Now the two differ by {comb_a - comb_b:.3f}', fontsize=11.5,
                 weight='bold')
    _save(fig, OV_DOC, 'relation-from-geometry.svg')


def opposite_phrases() -> None:
    """Why two phrases that mean opposite things look nearly the same."""
    p_behind = _phrase('mug', 'behind', 'bowl')
    p_front = _phrase('mug', 'in front of', 'bowl')
    c = _cos(p_behind, p_front)
    print(f'[opposites] cosine between "the mug behind the bowl" and '
          f'"the mug in front of the bowl" = {c:.4f}')
    print('[opposites] the two phrase vectors, direction by direction:')
    for i, nm in enumerate(AXES):
        print(f'[opposites] {nm:16s} behind {p_behind[i]:+.3f}   front {p_front[i]:+.3f}')
    share = float(np.abs(p_behind[APPEARANCE:]).sum() / np.abs(p_behind).sum())
    print(f'[opposites] of the whole phrase vector, '
          f'{share * 100:.1f}% sits on directions no picture can show')

    fig, ax = plt.subplots(figsize=(11.0, 4.9), facecolor='white')
    _plain(ax)
    x = np.arange(NDIM)
    ax.bar(x - 0.2, p_behind, width=0.38, color=LINK, ec=INK, lw=0.7,
           label='"the mug behind the bowl"')
    ax.bar(x + 0.2, p_front, width=0.38, color=GRIP, ec=INK, lw=0.7,
           label='"the mug in front of the bowl"')
    ax.axvspan(APPEARANCE - 0.5, NDIM - 0.5, color='#f6ead6', zorder=0)
    ax.text((APPEARANCE + NDIM - 1) / 2, -0.44,
            'no picture region has any value on these four',
            fontsize=9.5, ha='center', color=WRIST)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(AXES, fontsize=9, rotation=30, ha='right')
    ax.set_ylim(-0.55, 0.78)
    ax.set_ylabel('value on each direction', fontsize=10)
    ax.set_title(f'The two opposite phrases agree everywhere a picture can be compared, '
                 f'so their cosine is {c:.3f}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, OV_DOC, 'opposite-phrases.svg')


# --------------------------------------------------------------------------
# section 5: the failure modes, and what they cost an arm
# --------------------------------------------------------------------------

def counting_and_denial() -> None:
    """Counting words and the word "not" barely move the score."""
    white = REGIONS['white mug, handle in view']
    reg = REGIONS['red mug, handle in view']
    blue = REGIONS['blue mug, handle in view']
    counts = {'just "mug"': _cos(white, _phrase('mug')),
              '"two mugs"': _cos(white, _phrase('two', 'mug')),
              '"three mugs"': _cos(white, _phrase('three', 'mug'))}
    for k, v in counts.items():
        print(f'[counting] {k:24s} -> {v:.4f}')
    gap = abs(counts['"two mugs"'] - counts['"three mugs"'])
    cost = counts['just "mug"'] - counts['"two mugs"']
    print(f'[counting] "two mugs" and "three mugs" differ by {gap:.4f}, '
          f'while adding any count word at all costs {cost:.4f}')

    red_p = _phrase('red', 'mug')
    not_red_p = _phrase('not', 'red', 'mug')
    print(f'[denial] "the red mug" vs "the mug that is not red": '
          f'cosine between the phrases = {_cos(red_p, not_red_p):.4f}')
    print(f'[denial] "not red mug" scores {_cos(reg, not_red_p):.4f} on the RED mug '
          f'and {_cos(blue, not_red_p):.4f} on the blue mug')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.7), facecolor='white',
                             gridspec_kw={'wspace': 0.3})
    ax = axes[0]
    _plain(ax)
    ax.bar(list(counts.keys()), list(counts.values()), color=LINK, ec=INK, lw=0.8)
    for i, v in enumerate(counts.values()):
        ax.text(i, v + 0.006, f'{v:.4f}', ha='center', fontsize=9.6)
    ax.set_ylim(0, max(counts.values()) * 1.2)
    ax.set_ylabel('cosine similarity', fontsize=10)
    ax.tick_params(axis='x', labelrotation=14)
    ax.set_title(f'"Two" and "three" are {gap:.4f} apart, and the picture\nhas three '
                 'mugs in it either way',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    labels = ['red mug\n"the red mug"', 'red mug\n"the mug that is not red"',
              'blue mug\n"the mug that is not red"']
    vals = [_cos(reg, red_p), _cos(reg, not_red_p), _cos(blue, not_red_p)]
    ax.bar(labels, vals, color=[GRIP, GRIP, LINK], ec=INK, lw=0.8)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.006, f'{v:.4f}', ha='center', fontsize=9.6)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_ylabel('cosine similarity', fontsize=10)
    ax.tick_params(axis='x', labelrotation=10, labelsize=8.6)
    ax.set_title('"Not red" still prefers the red mug', fontsize=11.5, weight='bold')
    _save(fig, OV_DOC, 'counting-and-denial.svg')


def near_synonyms() -> None:
    """Names that mean different objects to a robot sit almost on top of each other."""
    pairs = [('mug', 'cup'), ('cup', 'glass'), ('bowl', 'cup'), ('jug', 'mug'),
             ('tin can', 'bowl'), ('mug', 'tin can')]
    vals = [_cos(WORDS[a], WORDS[b]) for a, b in pairs]
    for (a, b), v in zip(pairs, vals):
        print(f'[synonyms] "{a}" vs "{b}" -> {v:.4f}')

    fig, ax = plt.subplots(figsize=(10.0, 4.6), facecolor='white')
    _plain(ax)
    labels = [f'"{a}"\nvs "{b}"' for a, b in pairs]
    colours = [GRIP if v > 0.9 else (WRIST if v > 0.75 else LINK) for v in vals]
    ax.bar(labels, vals, color=colours, ec=INK, lw=0.8)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.008, f'{v:.3f}', ha='center', fontsize=10)
    ax.axhline(0.90, color=INK, ls='--', lw=1.4)
    ax.text(5.45, 0.925, 'above this line the two names\nare hard to tell apart',
            fontsize=9, ha='right', color=INK)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel('cosine similarity between the two text vectors', fontsize=10)
    top = int(np.argmax(vals))
    print(f'[synonyms] the closest pair is "{pairs[top][0]}" and "{pairs[top][1]}" '
          f'at {vals[top]:.4f}, which is {1 - vals[top]:.4f} from being the same word')
    ax.set_title(f'"{pairs[top][0]}" and "{pairs[top][1]}" are only '
                 f'{1 - vals[top]:.3f} from being the same direction, and a grasp '
                 'plan needs them apart',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'near-synonyms.svg')


def absent_object() -> None:
    """A thing that is not in the picture still gets a box."""
    rng = np.random.default_rng(23)
    absent_top = rng.normal(0.901, 0.021, size=300)
    present_top = rng.normal(0.938, 0.016, size=300)
    th = 0.92
    f_abs = float((absent_top >= th).mean())
    f_pre = float((present_top >= th).mean())
    print(f'[absent] simulated: with the threshold at {th:.2f}, '
          f'{f_abs * 100:.1f}% of pictures without the thing still return a box, '
          f'and {f_pre * 100:.1f}% of pictures with it do')
    print(f'[absent] mean top score absent {absent_top.mean():.4f}, '
          f'present {present_top.mean():.4f}, difference '
          f'{present_top.mean() - absent_top.mean():.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.7), facecolor='white',
                             gridspec_kw={'wspace': 0.26, 'width_ratios': [1, 1.1]})
    ax = axes[0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.4)
    ax.add_patch(Rectangle((0.3, 0.9), 9.4, 0.24, fc='#e8e2d8', ec=INK, lw=1.0))
    _bowl(ax, 2.6, 1.14, w=1.5, h=0.62)
    _mug(ax, 5.4, 1.14, w=0.7, h=0.84)
    _tin(ax, 7.8, 1.14, w=0.6, h=0.68)
    ax.add_patch(Rectangle((7.3, 1.10), 1.0, 0.80, fill=False, ec=GRIP, lw=2.4))
    ax.text(7.8, 2.14, '"a screwdriver"\n0.934', ha='center', fontsize=10,
            color=GRIP, weight='bold')
    ax.text(5.0, 4.05, 'Asked for a screwdriver in a picture\nthat holds no screwdriver',
            fontsize=11.5, weight='bold', ha='center')
    ax.text(5.0, 3.15, 'the model returns the tin, above the threshold',
            fontsize=10.5, ha='center', color=GRIP)
    ax.text(5.0, 0.28, 'There is no "nothing here" answer, because every\nregion gets '
                       'a score and one of them is highest.',
            fontsize=9.5, ha='center', color=MUTED)
    ax = axes[1]
    _plain(ax)
    bins = np.linspace(0.83, 1.00, 36)
    ax.hist(absent_top, bins=bins, color=GRIP, alpha=0.75, label='no such thing in the picture')
    ax.hist(present_top, bins=bins, color=SLIDE, alpha=0.75, label='the thing is in the picture')
    ax.axvline(th, color=INK, lw=1.8, ls='--')
    ax.set_ylim(0, 58)
    ax.text(th + 0.003, 44, f'threshold {th:.2f}', fontsize=9.5)
    ax.set_xlabel('best score anywhere in the picture', fontsize=10)
    ax.set_ylabel('how many pictures (of 300 each)', fontsize=10)
    ax.set_title(f'Simulated: {f_abs * 100:.0f}% of the absent cases clear the threshold',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    _save(fig, OV_DOC, 'absent-object.svg')


def cost_on_an_arm() -> None:
    """What a wrong region costs when a gripper acts on it."""
    true_c = np.array([0.055, 0.020])       # metres, the mug the words meant
    wrong_c = np.array([-0.070, 0.015])     # the other mug the model returned
    miss = float(np.linalg.norm(true_c - wrong_c) * 1000)
    opening, width = 85.0, 72.0
    margin = (opening - width) / 2
    print(f'[arm] the returned box centre is {miss:.1f} mm from the one the words meant')
    print(f'[arm] gripper opening {opening:.0f} mm, object {width:.0f} mm wide, '
          f'so the margin each side is {margin:.1f} mm')
    print(f'[arm] the miss is {miss / margin:.1f} times the margin')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    ax.add_patch(Rectangle((-0.16, -0.05), 0.32, 0.12, fc='#f1ece2', ec=GRID, lw=1.0))
    for c, lab, col in ((true_c, 'the mug the words meant', SLIDE),
                        (wrong_c, 'the mug the model returned', GRIP)):
        ax.add_patch(Circle(c, 0.036, fc=col, ec=INK, lw=1.1, alpha=0.35))
        ax.plot([c[0]], [c[1]], marker='o', color=col, ms=9)
        ax.text(c[0], c[1] + 0.050, lab, fontsize=9.8, ha='center', color=col)
    ax.annotate('', xy=tuple(true_c), xytext=tuple(wrong_c),
                arrowprops=dict(arrowstyle='<->', color=INK, lw=1.8))
    ax.text((true_c[0] + wrong_c[0]) / 2, (true_c[1] + wrong_c[1]) / 2 - 0.016,
            f'{miss:.0f} mm', fontsize=11.5, ha='center', weight='bold')
    for side in (-1, 1):
        ax.add_patch(Rectangle((wrong_c[0] + side * opening / 2000 - 0.004, -0.012),
                               0.008, 0.055, fc='#888888', ec=INK, lw=0.9))
    ax.text(wrong_c[0], -0.030, f'gripper opens {opening:.0f} mm,\nmargin '
                                f'{margin:.1f} mm each side',
            fontsize=9.5, ha='center', color=INK)
    ax.set_xlim(-0.17, 0.17)
    ax.set_ylim(-0.055, 0.105)
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('height y (m)', fontsize=10)
    ax.set_title(f'A {miss:.0f} mm miss is {miss / margin:.0f} times the gripper\'s '
                 f'{margin:.1f} mm margin, so the fingers close on the wrong thing',
                 fontsize=12, weight='bold')
    _save(fig, OV_DOC, 'cost-on-an-arm.svg')


# ==========================================================================
# PAGE 4: depth and 3D
# ==========================================================================

FX: float = 615.0
FY: float = 615.0
CX: float = 320.5
CY: float = 240.5


def flat_picture_is_a_ray() -> None:
    """One pixel fixes a direction, not a place."""
    u, v = 412.0, 178.0
    zs = [0.30, 0.60, 0.90]
    pts = [((u - CX) * z / FX, (v - CY) * z / FY, z) for z in zs]
    print(f'[ray] pixel ({u:.0f}, {v:.0f}) with fx = {FX:.0f}, cx = {CX:.1f}, '
          f'cy = {CY:.1f}')
    for (x, y, z) in pts:
        print(f'[ray] at z = {z:.2f} m the pixel means the point '
              f'({x:+.4f}, {y:+.4f}, {z:.2f}) m')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    ax.plot([0], [0], marker='^', color=INK, ms=14)
    ax.text(0, -0.055, 'camera', fontsize=9.5, ha='center')
    ax.plot([0, 1.05], [0, 1.05 * (u - CX) / FX], color=GRIP, lw=2.2)
    for (x, _y, z) in pts:
        ax.plot([z], [x], marker='o', color=LINK, ms=10)
        ax.text(z, x + 0.020, f'z = {z:.2f} m, x = {x:+.3f} m', fontsize=9.3,
                ha='center', color=LINK)
    ax.add_patch(Rectangle((0.05, -0.09), 0.012, 0.18, fc='#dddddd', ec=INK, lw=1.0))
    ax.text(0.085, 0.092, 'sensor', fontsize=9, color=MUTED)
    ax.set_xlim(-0.04, 1.08)
    ax.set_ylim(-0.10, 0.22)
    ax.set_xlabel('distance from the camera z (m)', fontsize=10)
    ax.set_ylabel('sideways position x (m)', fontsize=10)
    ax.set_title(f'Pixel ({u:.0f}, {v:.0f}) names a whole line of places, and the '
                 'picture does not say which one',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'flat-picture-is-a-ray.svg')


def _toy_scene_depth(cols: int = 12, rows: int = 8) -> Arr:
    """A small made-up depth map in millimetres: a sloping table with a mug on it."""
    yy, xx = np.mgrid[0:rows, 0:cols]
    table = 900.0 - 42.0 * (rows - 1 - yy)
    mug = ((xx >= 6) & (xx <= 8) & (yy >= 3) & (yy <= 5))
    d = np.where(mug, 468.0, table)
    return d


def depth_map_grid() -> None:
    """A depth map is a grid of distances."""
    d = _toy_scene_depth()
    print(f'[depth-map] grid {d.shape[1]} wide by {d.shape[0]} tall, '
          f'nearest {d.min():.0f} mm, furthest {d.max():.0f} mm')
    print('[depth-map] the rows, in millimetres:')
    for r in range(d.shape[0]):
        print('[depth-map] ' + ' '.join(f'{x:4.0f}' for x in d[r]))

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    im = ax.imshow(d, cmap='viridis_r')
    for i in range(d.shape[0]):
        for j in range(d.shape[1]):
            ax.text(j, i, f'{d[i, j]:.0f}', ha='center', va='center', fontsize=8.6,
                    color='white' if d[i, j] > 640 else INK)
    ax.add_patch(Rectangle((5.5, 2.5), 3, 3, fill=False, ec=GRIP, lw=2.6))
    ax.set_ylim(7.5, -1.6)
    ax.annotate('the mug: 468 mm', xy=(7.0, 2.45), xytext=(7.0, -1.2),
                ha='center', fontsize=10.5, color=GRIP, weight='bold',
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.6))
    ax.set_xticks(range(d.shape[1]))
    ax.set_yticks(range(d.shape[0]))
    ax.set_xlabel('pixel column', fontsize=10)
    ax.set_ylabel('pixel row', fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.82, label='distance (mm)')
    ax.set_title('A depth map holds one distance in each pixel, in millimetres',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'depth-map-grid.svg')


def brightness_edge_depth_edge() -> None:
    """Brightness edges and depth edges are not in the same places."""
    rng = np.random.default_rng(7)
    n = 160
    col = np.arange(n)
    bright = np.full(n, 0.62) + rng.normal(0, 0.012, n)
    bright[40:70] = 0.24 + rng.normal(0, 0.012, 30)     # a painted stripe, flat table
    bright[96:128] = 0.88 + rng.normal(0, 0.012, 32)    # the white mug
    depth = np.full(n, 0.760)
    depth[96:128] = 0.468
    depth += rng.normal(0, 0.0015, n)
    b_edges = col[:-1][np.abs(np.diff(bright)) > 0.2]
    d_edges = col[:-1][np.abs(np.diff(depth)) > 0.05]
    print(f'[edges] brightness jumps at columns {[int(c) for c in b_edges]}')
    print(f'[edges] depth jumps at columns {[int(c) for c in d_edges]}')
    print(f'[edges] of {len(b_edges)} brightness jumps, {len(d_edges)} are also '
          'depth jumps, which is the painted stripe giving two false ones')

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 5.8), facecolor='white', sharex=True,
                             gridspec_kw={'hspace': 0.34})
    _plain(axes[0])
    axes[0].plot(col, bright, color=INK, lw=1.6)
    for c in b_edges:
        axes[0].axvline(c, color=WRIST, lw=1.4, ls='--')
    axes[0].set_ylabel('brightness (0 to 1)', fontsize=10)
    axes[0].set_title('One row of the picture: four brightness jumps, two of them '
                      'only paint',
                      fontsize=12, weight='bold')
    _plain(axes[1])
    axes[1].plot(col, depth, color=TEAL, lw=1.6)
    for c in d_edges:
        axes[1].axvline(c, color=GRIP, lw=1.4, ls='--')
    axes[1].set_ylim(0.40, 0.84)
    axes[1].set_ylabel('distance (m)', fontsize=10)
    axes[1].set_xlabel('pixel column along the row', fontsize=10)
    axes[1].set_title('The same row in depth: only the mug makes a jump',
                      fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'brightness-edge-depth-edge.svg')


def same_picture_two_sizes() -> None:
    """The real scale ambiguity, worked out."""
    f = 600.0
    small_h, small_z = 0.095, 0.40
    big_h, big_z = 0.285, 1.20
    px_small = f * small_h / small_z
    px_big = f * big_h / big_z
    print(f'[scale] a {small_h * 1000:.0f} mm mug at {small_z:.2f} m with f = {f:.0f} px '
          f'is {px_small:.1f} px tall')
    print(f'[scale] a {big_h * 1000:.0f} mm bin at {big_z:.2f} m with f = {f:.0f} px '
          f'is {px_big:.1f} px tall')
    print(f'[scale] the two differ by {abs(px_small - px_big):.1f} px, and the '
          f'distance ratio {big_z / small_z:.1f} matches the size ratio '
          f'{big_h / small_h:.1f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    ax.plot([0], [0], marker='^', color=INK, ms=14)
    ax.text(0, -0.09, 'camera', fontsize=9.5, ha='center')
    ax.add_patch(Rectangle((0.04, -0.13), 0.012, 0.26, fc='#dddddd', ec=INK, lw=1.0))
    for z, hgt, lab, col in ((small_z, small_h, f'mug, {small_h * 1000:.0f} mm tall', LINK),
                             (big_z, big_h, f'bin, {big_h * 1000:.0f} mm tall', PURPLE)):
        ax.add_patch(Rectangle((z - 0.025, -hgt / 2), 0.05, hgt, fc=col, ec=INK,
                               lw=1.1, alpha=0.5))
        ax.text(z, hgt / 2 + 0.022, lab, fontsize=9.8, ha='center', color=col)
        ax.text(z, -hgt / 2 - 0.045, f'z = {z:.2f} m', fontsize=9.5, ha='center',
                color=col)
    ax.plot([0, big_z + 0.1], [0, (big_z + 0.1) * (big_h / 2) / big_z], color=GRIP, lw=1.8)
    ax.plot([0, big_z + 0.1], [0, -(big_z + 0.1) * (big_h / 2) / big_z], color=GRIP, lw=1.8)
    ax.text(0.70, -0.185, 'both objects fill exactly the same cone of view',
            fontsize=10.5, color=GRIP, ha='center')
    ax.set_xlim(-0.05, 1.42)
    ax.set_ylim(-0.23, 0.22)
    ax.set_xlabel('distance from the camera z (m)', fontsize=10)
    ax.set_ylabel('height above the lens axis (m)', fontsize=10)
    ax.set_title(f'Both come out {px_small:.1f} pixels tall, so the flat picture '
                 'cannot tell them apart',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'same-picture-two-sizes.svg')


def size_assumption() -> None:
    """A guessed size turns straight into a guessed distance."""
    f = 600.0
    h_px = 142.5
    sizes = np.array([0.076, 0.085, 0.095, 0.105, 0.114])
    zs = f * sizes / h_px
    print(f'[assumption] an object {h_px:.1f} px tall, f = {f:.0f} px:')
    for s, z in zip(sizes, zs):
        print(f'[assumption]   if it is {s * 1000:.0f} mm tall it is at {z:.3f} m')
    err = (zs[-1] - zs[0]) * 1000
    print(f'[assumption] a 20% spread of assumed heights (76 mm to 114 mm) moves the '
          f'answer by {err:.0f} mm')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white',
                             gridspec_kw={'wspace': 0.3})
    ax = axes[0]
    _plain(ax)
    z_grid = np.linspace(0.2, 1.5, 200)
    ax.plot(z_grid, f * 0.095 / z_grid, color=LINK, lw=2.2, label='a 95 mm object')
    ax.plot(z_grid, f * 0.285 / z_grid, color=PURPLE, lw=2.2, label='a 285 mm object')
    ax.axhline(h_px, color=GRIP, lw=1.6, ls='--')
    ax.text(1.15, h_px + 18, f'{h_px:.1f} px tall', fontsize=9.5, color=GRIP)
    ax.plot([0.40, 1.20], [h_px, h_px], marker='o', color=GRIP, ls='none', ms=8)
    ax.set_xlabel('distance z (m)', fontsize=10)
    ax.set_ylabel('height in the picture (pixels)', fontsize=10)
    ax.set_ylim(0, 600)
    ax.set_title('Height in pixels falls as one over the distance',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False)
    ax = axes[1]
    _plain(ax)
    ax.bar([f'{s * 1000:.0f}' for s in sizes], zs, color=TEAL, ec=INK, lw=0.8)
    for i, z in enumerate(zs):
        ax.text(i, z + 0.012, f'{z:.3f} m', ha='center', fontsize=9.6)
    ax.set_xlabel('assumed real height of the object (mm)', fontsize=10)
    ax.set_ylabel('distance that follows (m)', fontsize=10)
    ax.set_ylim(0, zs.max() * 1.2)
    ax.set_title(f'The same {h_px:.1f} px, five size guesses, '
                 f'{err:.0f} mm of spread',
                 fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'size-assumption.svg')


def _relative_row() -> tuple[Arr, Arr, Arr]:
    """True distances along one row, and a simulated relative-depth prediction."""
    rng = np.random.default_rng(31)
    n = 120
    col = np.arange(n)
    true = np.full(n, 0.780)
    true[20:46] = 0.512            # a bowl
    true[70:100] = 0.436           # a mug, nearer
    true += np.linspace(0, 0.03, n) + rng.normal(0, 0.002, n)
    pred = 0.62 * true + 0.09 + rng.normal(0, 0.004, n)
    return col.astype(float), true, pred


def monocular_shape_right_scale_wrong() -> None:
    """One-picture depth gets the shape right and the scale wrong."""
    col, true, pred = _relative_row()
    a, b = np.polyfit(true, pred, 1)
    print(f'[relative] the simulated prediction is {a:.3f} x true + {b:.3f}')
    print(f'[relative] at the mug: true {true[70:100].mean():.3f} m, '
          f'predicted {pred[70:100].mean():.3f} m, '
          f'error {abs(pred[70:100].mean() - true[70:100].mean()) * 1000:.0f} mm')
    print(f'[relative] at the far table: true {true[100:].mean():.3f} m, '
          f'predicted {pred[100:].mean():.3f} m, '
          f'error {abs(pred[100:].mean() - true[100:].mean()) * 1000:.0f} mm')
    order_true = np.argsort([true[20:46].mean(), true[70:100].mean(), true[100:].mean()])
    order_pred = np.argsort([pred[20:46].mean(), pred[70:100].mean(), pred[100:].mean()])
    print(f'[relative] the nearest-to-furthest order of bowl, mug and far table is '
          f'{[int(i) for i in order_true]} from the true depths and '
          f'{[int(i) for i in order_pred]} from the prediction, so the order is kept')

    fig, ax = plt.subplots(figsize=(10.4, 4.9), facecolor='white')
    _plain(ax)
    ax.plot(col, true, color=TEAL, lw=2.0, label='true distance')
    ax.plot(col, pred, color=GRIP, lw=2.0, label='one-picture prediction (simulated)')
    for lo, hi, lab in ((20, 46, 'bowl'), (70, 100, 'mug')):
        ax.axvspan(lo, hi, color='#f3f0e6', zorder=0)
        ax.text((lo + hi) / 2, 0.88, lab, ha='center', fontsize=9.8, color=MUTED)
    ax.set_xlabel('pixel column along the row', fontsize=10)
    ax.set_ylabel('distance (m)', fontsize=10)
    ax.set_ylim(0.32, 0.94)
    ax.set_title(f'The shape of the row is right, but every value is '
                 f'{a:.2f} x true + {b:.2f}, so no distance is usable',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, D3_DOC, 'monocular-shape-right-scale-wrong.svg')


def affine_freedom() -> None:
    """Three scalings of the same relative prediction, all equally consistent."""
    col, true, pred = _relative_row()
    rel = (pred - pred.min()) / (pred.max() - pred.min())      # 0 to 1, nothing more
    settings = [(0.30, 0.55), (0.42, 0.78), (0.58, 1.05)]
    print('[freedom] the same 0-to-1 relative map, read with three different scalings:')
    for near, far in settings:
        z = near + rel * (far - near)
        print(f'[freedom]   near {near:.2f} m, far {far:.2f} m -> the mug sits at '
              f'{z[70:100].mean():.3f} m')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(col, true, color=TEAL, lw=2.4, label='true distance')
    for (near, far), colour in zip(settings, (LINK, PURPLE, WRIST)):
        z = near + rel * (far - near)
        ax.plot(col, z, lw=1.8, color=colour,
                label=f'read as {near:.2f} m to {far:.2f} m '
                      f'(mug at {z[70:100].mean():.3f} m)')
    ax.set_xlabel('pixel column along the row', fontsize=10)
    ax.set_ylabel('distance (m)', fontsize=10)
    ax.set_title('A relative depth map is the same picture under every scaling, '
                 'and the mug lands anywhere',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper center',
              bbox_to_anchor=(0.5, -0.17), ncol=2)
    _save(fig, D3_DOC, 'affine-freedom.svg')


def align_then_measure() -> None:
    """Two known distances fix the scale, and the error that is left."""
    col, true, pred = _relative_row()
    opening, width = 85.0, 72.0
    margin = (opening - width) / 2
    runs = {}
    for lab, (i1, i2) in (('far apart in depth', (85, 110)),
                          ('close together in depth', (5, 110))):
        a = (true[i2] - true[i1]) / (pred[i2] - pred[i1])
        b = true[i1] - a * pred[i1]
        fixed = a * pred + b
        resid = np.abs(fixed - true) * 1000
        runs[lab] = (i1, i2, a, b, fixed, resid)
        print(f'[align] anchors {lab} (columns {i1} and {i2}, '
              f'{abs(true[i2] - true[i1]) * 1000:.0f} mm apart): '
              f'scale a = {a:.4f}, shift b = {b:+.4f}')
        print(f'[align]   left over: mean {resid.mean():.1f} mm, '
              f'worst {resid.max():.1f} mm, on the mug '
              f'{np.abs(fixed[70:100] - true[70:100]).mean() * 1000:.1f} mm, '
              f'which is {resid.max() / margin:.1f} times the '
              f'{margin:.1f} mm gripper margin')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.8), facecolor='white',
                             gridspec_kw={'wspace': 0.3})
    ax = axes[0]
    _plain(ax)
    ax.plot(col, true, color=TEAL, lw=2.4, label='true distance')
    for (lab, (i1, i2, a, b, fixed, _r)), colour in zip(runs.items(), (LINK, GRIP)):
        ax.plot(col, fixed, color=colour, lw=1.7,
                label=f'fitted with anchors {lab}')
        ax.plot([col[i1], col[i2]], [true[i1], true[i2]], marker='o', color=colour,
                ls='none', ms=8)
    ax.set_xlabel('pixel column', fontsize=10)
    ax.set_ylabel('distance (m)', fontsize=10)
    ax.set_ylim(0.30, 0.95)
    ax.set_title('Two measured anchors turn a relative map into metres',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=8.6, frameon=False, loc='upper left')
    ax = axes[1]
    _plain(ax)
    for (lab, (_i1, _i2, _a, _b, _f, resid)), colour in zip(runs.items(), (LINK, GRIP)):
        ax.plot(col, resid, color=colour, lw=1.8,
                label=f'{lab}: worst {resid.max():.1f} mm')
    ax.axhline(margin, color=INK, ls='--', lw=1.6)
    ax.text(50, 34, f'gripper margin {margin:.1f} mm', fontsize=9.5, ha='center')
    ax.annotate('', xy=(50, margin), xytext=(50, 31),
                arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))
    ax.set_xlabel('pixel column', fontsize=10)
    ax.set_ylabel('distance error left over (mm)', fontsize=10)
    ax.set_ylim(0, 215)
    ax.set_title('Anchors at nearly the same distance leave\nan error far above the '
                 'gripper margin',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper center')
    _save(fig, D3_DOC, 'align-then-measure.svg')


def relative_versus_metric() -> None:
    """What each kind of depth lets an arm do, with the mug's distance each way."""
    col, true, pred = _relative_row()
    rel = (pred - pred.min()) / (pred.max() - pred.min())
    truth = float(true[70:100].mean())
    reads = [(0.30, 0.55), (0.42, 0.78), (0.58, 1.05)]
    guesses = [float((near + rel * (far - near))[70:100].mean()) for near, far in reads]
    i1, i2 = 85, 110
    a = (true[i2] - true[i1]) / (pred[i2] - pred[i1])
    b = true[i1] - a * pred[i1]
    aligned = float((a * pred + b)[70:100].mean())
    margin = (85.0 - 72.0) / 2
    print(f'[kinds] the mug really is at {truth:.3f} m')
    for (near, far), g in zip(reads, guesses):
        print(f'[kinds]   relative map read as {near:.2f} to {far:.2f} m -> '
              f'{g:.3f} m, which is {abs(g - truth) * 1000:.0f} mm out')
    print(f'[kinds]   after two measured anchors -> {aligned:.3f} m, '
          f'{abs(aligned - truth) * 1000:.1f} mm out')
    print(f'[kinds] the three relative readings spread over '
          f'{(max(guesses) - min(guesses)) * 1000:.0f} mm, against a gripper margin '
          f'of {margin:.1f} mm')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white',
                             gridspec_kw={'wspace': 0.28, 'width_ratios': [1, 1.1]})
    ax = axes[0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    rows = [('Which object is nearest?', 'yes', 'yes'),
            ('Is the mug in front?', 'yes', 'yes'),
            ('How far must the arm reach?', 'no', 'yes'),
            ('Will the fingers clear the rim?', 'no', 'yes')]
    ax.text(0.2, 5.9, 'question', fontsize=10.5, weight='bold')
    ax.text(7.4, 5.9, 'relative', fontsize=10.5, weight='bold', ha='center')
    ax.text(9.3, 5.9, 'metric', fontsize=10.5, weight='bold', ha='center')
    ax.plot([0.15, 10.0], [5.6, 5.6], color=INK, lw=1.1)
    for k, (q, r, m) in enumerate(rows):
        y = 4.9 - k * 0.95
        ax.text(0.2, y, q, fontsize=9.6, va='center')
        for x, v in ((7.4, r), (9.3, m)):
            ax.text(x, y, v, fontsize=10.5, ha='center', va='center', weight='bold',
                    color=SLIDE if v == 'yes' else GRIP)
    ax.text(0.2, 0.55, 'Relative depth answers questions about order.\n'
                       'Only metric depth answers questions in millimetres.',
            fontsize=10, color=INK, va='center')
    ax.set_title('What each kind of depth can be asked', fontsize=11.5, weight='bold')

    ax = axes[1]
    _plain(ax)
    labels = ['truth'] + [f'relative,\nread as\n{n:.2f}-{f:.2f} m' for n, f in reads] \
        + ['after two\nmeasured\nanchors']
    vals = [truth] + guesses + [aligned]
    colours = [TEAL, LINK, PURPLE, WRIST, SLIDE]
    ax.bar(labels, vals, color=colours, ec=INK, lw=0.8)
    ax.axhspan(truth - margin / 1000, truth + margin / 1000, color='#d8f0dc', zorder=0)
    ax.text(0.5, truth + 0.10, f'the {margin:.1f} mm the gripper allows',
            fontsize=9, ha='center', color=SLIDE)
    ax.annotate('', xy=(0.5, truth + 0.012), xytext=(0.5, truth + 0.092),
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    for i, v in enumerate(vals):
        ax.text(i, v + 0.012, f'{v:.3f} m', ha='center', fontsize=9.4)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel('distance the arm would reach to (m)', fontsize=10)
    ax.tick_params(axis='x', labelsize=8.4)
    ax.set_title(f'The same relative map puts the mug anywhere over '
                 f'{(max(guesses) - min(guesses)) * 1000:.0f} mm',
                 fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'relative-versus-metric.svg')


def stereo_geometry() -> None:
    """The disparity arithmetic for one baseline and one focal length."""
    f, base = 700.0, 0.060
    zs = np.array([0.30, 0.40, 0.60, 1.00, 2.00, 4.00])
    disp = f * base / zs
    print(f'[stereo] f = {f:.0f} px, baseline = {base * 1000:.0f} mm, '
          f'so disparity = {f * base:.1f} / z')
    for z, d in zip(zs, disp):
        print(f'[stereo]   z = {z:.2f} m -> disparity {d:.2f} px')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.8), facecolor='white',
                             gridspec_kw={'wspace': 0.3})
    ax = axes[0]
    _plain(ax)
    z0 = 0.40
    ax.plot([-base / 2, base / 2], [0, 0], marker='^', color=INK, ms=13, ls='none')
    ax.text(-base / 2, -0.072, 'left camera', fontsize=9.3, ha='center')
    ax.text(base / 2, -0.072, 'right camera', fontsize=9.3, ha='center')
    ax.annotate('', xy=(-base / 2, -0.026), xytext=(base / 2, -0.026),
                arrowprops=dict(arrowstyle='<->', color=GRIP, lw=1.6))
    ax.text(0, -0.050, f'baseline {base * 1000:.0f} mm', fontsize=9.5, ha='center',
            color=GRIP)
    ax.plot([0.012], [z0], marker='o', color=LINK, ms=11)
    ax.text(0.020, z0, f'point at z = {z0:.2f} m', fontsize=9.8, va='center', color=LINK)
    ax.plot([-base / 2, 0.012], [0, z0], color=MUTED, lw=1.4)
    ax.plot([base / 2, 0.012], [0, z0], color=MUTED, lw=1.4)
    ax.set_xlim(-0.09, 0.13)
    ax.set_ylim(-0.095, 0.50)
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('distance z (m)', fontsize=10)
    ax.set_title(f'disparity = f x baseline / z\n= {f:.0f} x {base:.3f} / {z0:.2f} '
                 f'= {f * base / z0:.1f} pixels',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    z_grid = np.linspace(0.25, 4.2, 300)
    ax.plot(z_grid, f * base / z_grid, color=LINK, lw=2.2)
    ax.plot(zs, disp, marker='o', color=GRIP, ls='none', ms=8)
    for z, d in zip(zs, disp):
        ax.text(z + 0.06, d + 2.5, f'{d:.1f} px', fontsize=9.2, color=GRIP)
    ax.set_xlabel('distance z (m)', fontsize=10)
    ax.set_ylabel('disparity (pixels)', fontsize=10)
    ax.set_xlim(0.1, 4.7)
    ax.set_title('Far things shift by almost nothing', fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'stereo-geometry.svg')


def stereo_error() -> None:
    """Half a pixel of matching error, turned into millimetres at each distance."""
    f, base = 700.0, 0.060
    dd = 0.25
    zs = np.array([0.30, 0.40, 0.60, 1.00, 2.00, 4.00])
    err = zs ** 2 / (f * base) * dd * 1000
    print(f'[stereo-error] a matching error of {dd:.2f} px costs:')
    for z, e in zip(zs, err):
        print(f'[stereo-error]   at z = {z:.2f} m -> {e:.1f} mm')
    print(f'[stereo-error] going from 0.40 m to 4.00 m is 10 times the distance and '
          f'{err[-1] / err[1]:.0f} times the error')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plain(ax)
    z_grid = np.linspace(0.25, 4.2, 300)
    ax.plot(z_grid, z_grid ** 2 / (f * base) * dd * 1000, color=GRIP, lw=2.4)
    ax.plot(zs, err, marker='o', color=INK, ls='none', ms=8)
    for z, e in zip(zs, err):
        ax.text(z, e * 1.35, f'{e:.1f} mm', ha='center', fontsize=9.4)
    ax.axhline(6.5, color=SLIDE, lw=1.6, ls='--')
    ax.text(2.4, 7.6, 'a gripper\'s 6.5 mm margin', fontsize=9.5, color=SLIDE)
    ax.set_yscale('log')
    ax.set_ylim(0.25, 400)
    ax.set_xlim(0.1, 4.5)
    ax.set_xlabel('distance z (m)', fontsize=10)
    ax.set_ylabel('distance error (mm, log scale)', fontsize=10)
    ax.set_title(f'Depth error grows with the square of the distance: '
                 f'{err[1]:.1f} mm at 0.40 m, {err[-1]:.0f} mm at 4.00 m',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'stereo-error.svg')


def texture_is_needed() -> None:
    """Matching only works where the surface has something to match."""
    rng = np.random.default_rng(13)
    n, true_d, win = 200, 12, 24
    textured = np.clip(0.5 + np.cumsum(rng.normal(0, 0.09, n)) * 0.25, 0.02, 0.98)
    plain = np.full(n, 0.82) + rng.normal(0, 0.006, n)
    out = {}
    for name, row, has_features in (('textured wood', textured, True),
                                    ('plain white wall', plain, False)):
        # The right camera sees the same surface shifted by true_d pixels. On the
        # wall there is nothing to shift, so all the right camera has is its own
        # sensor noise, which the left camera never saw.
        if has_features:
            right = np.roll(row, -true_d) + rng.normal(0, 0.006, n)
        else:
            right = np.full(n, 0.82) + rng.normal(0, 0.006, n)
        left = row[90:90 + win]
        sad = np.array([np.abs(left - right[90 - d:90 - d + win]).sum()
                        for d in range(0, 31)])
        out[name] = sad
        best = int(np.argmin(sad))
        rest = np.argsort(sad)
        second = int([k for k in rest if abs(k - best) > 2][0])
        print(f'[texture] {name:17s} best shift {best} px (score {sad[best]:.3f}), '
              f'next best away from it {second} px (score {sad[second]:.3f}), '
              f'gap {sad[second] - sad[best]:.3f}, whole curve spans '
              f'{sad.max() - sad.min():.3f}')
    print(f'[texture] the true shift in this made-up pair is {true_d} px')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), facecolor='white',
                             gridspec_kw={'wspace': 0.28})
    _plain(axes[0])
    axes[0].plot(textured, color=WRIST, lw=1.5, label='textured wood')
    axes[0].plot(plain, color=LINK, lw=1.5, label='plain white wall')
    axes[0].set_xlabel('pixel along the row', fontsize=10)
    axes[0].set_ylabel('brightness', fontsize=10)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_title('Simulated: two rows from the left picture', fontsize=11.5,
                      weight='bold')
    axes[0].legend(fontsize=9, frameon=False, loc='lower left')
    _plain(axes[1])
    for name, colour in (('textured wood', WRIST), ('plain white wall', LINK)):
        axes[1].plot(out[name], color=colour, lw=2.0, marker='o', ms=3.4, label=name)
    axes[1].axvline(true_d, color=GRIP, ls='--', lw=1.5)
    axes[1].text(true_d + 0.5, max(out['textured wood']) * 0.92,
                 f'true shift {true_d} px', fontsize=9.5, color=GRIP)
    axes[1].set_xlabel('shift tried (pixels)', fontsize=10)
    axes[1].set_ylabel('how badly the two windows differ', fontsize=10)
    axes[1].set_title('A sharp dip on wood, no dip at all on the wall',
                      fontsize=11.5, weight='bold')
    axes[1].legend(fontsize=9, frameon=False)
    _save(fig, D3_DOC, 'texture-is-needed.svg')


SURFACES: list[tuple[str, float]] = [('matte paper', 0.97), ('black rubber', 0.52),
                                     ('brushed steel', 0.34), ('clear glass', 0.07)]


def pattern_on_surfaces() -> None:
    """The projected dots, and how many of them come back from each surface."""
    rng = np.random.default_rng(3)
    fig, axes = plt.subplots(1, 4, figsize=(12.0, 3.6), facecolor='white',
                             gridspec_kw={'wspace': 0.14})
    for ax, (name, prob) in zip(axes, SURFACES):
        _blank(ax)
        ax.add_patch(Rectangle((0, 0), 1, 1, fc='#f7f7f7', ec=INK, lw=1.1))
        pts = rng.random((200, 2)) * 0.9 + 0.05
        seen = rng.random(200) < prob
        ax.plot(pts[seen, 0], pts[seen, 1], marker='o', ls='none', ms=3.2, color=GRIP)
        ax.plot(pts[~seen, 0], pts[~seen, 1], marker='o', ls='none', ms=3.2,
                mfc='none', mec=GRID)
        found = int(seen.sum())
        print(f'[pattern] {name:14s} {found:3d} of 200 dots found '
              f'({found / 200 * 100:.0f}%, simulated at p = {prob:.2f})')
        ax.set_title(f'{name}\n{found} of 200 dots found', fontsize=10.5, weight='bold')
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
    fig.suptitle('Simulated: the projected dots a depth camera gets back from four '
                 'surfaces (solid = found, hollow = lost)',
                 fontsize=12, weight='bold', y=1.08)
    _save(fig, D3_DOC, 'pattern-on-surfaces.svg')


HOLE_REGIONS: list[tuple[str, float, slice, slice]] = [
    ('clear glass', 0.07, slice(6, 26), slice(6, 22)),
    ('brushed steel', 0.34, slice(8, 30), slice(30, 44)),
    ('black rubber', 0.52, slice(30, 44), slice(14, 36)),
    ('matte paper', 0.97, slice(28, 44), slice(44, 60))]


def _hole_map() -> NDArray[np.bool_]:
    """A simulated 64 by 48 map of which pixels got a distance back."""
    rng = np.random.default_rng(4)
    valid = np.ones((48, 64), dtype=bool)
    for _name, prob, rs, cs in HOLE_REGIONS:
        block = valid[rs, cs]
        valid[rs, cs] = rng.random(block.shape) < prob
    return valid


def holes_in_the_depth_map() -> None:
    """The holes those lost dots leave in the depth map."""
    valid = _hole_map()
    regions = HOLE_REGIONS
    print(f'[holes] the whole depth map is {valid.mean() * 100:.1f}% filled')
    bars = []
    for name, _prob, rs, cs in regions:
        pct = valid[rs, cs].mean() * 100
        bars.append((name, pct))
        print(f'[holes] over the {name} patch, {pct:.1f}% of pixels have a distance')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white',
                             gridspec_kw={'wspace': 0.26, 'width_ratios': [1.15, 1]})
    ax = axes[0]
    ax.imshow(valid.astype(float), cmap='Greys_r', vmin=0, vmax=1)
    for name, _prob, rs, cs in regions:
        ax.add_patch(Rectangle((cs.start - 0.5, rs.start - 0.5),
                               cs.stop - cs.start, rs.stop - rs.start,
                               fill=False, ec=GRIP, lw=1.8))
        below = name == 'black rubber'
        ax.text((cs.start + cs.stop) / 2,
                rs.stop + 3.4 if below else rs.start - 2.0, name, ha='center',
                fontsize=9, color=GRIP,
                bbox=dict(facecolor='white', edgecolor='none', pad=1.2))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f'Simulated depth map: black means no distance\n'
                 f'({valid.mean() * 100:.1f}% of pixels are filled)',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.barh([b[0] for b in bars][::-1], [b[1] for b in bars][::-1],
            color=[LINK, WRIST, GRIP, SLIDE][::-1], ec=INK, lw=0.8, height=0.55)
    for i, (_n, p) in enumerate(bars[::-1]):
        ax.text(p + 1.5, i, f'{p:.0f}%', va='center', fontsize=10)
    ax.set_xlim(0, 112)
    ax.set_xlabel('pixels with a distance (%)', fontsize=10)
    ax.set_title('The glass patch is almost empty', fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'holes-in-the-depth-map.svg')


def glass_reads_the_table() -> None:
    """A clear object does not just go missing, it reports the wrong distance."""
    glass_z, table_z = 0.460, 0.710
    err = (table_z - glass_z) * 1000
    print(f'[glass] the glass front is at {glass_z:.3f} m, the table behind it at '
          f'{table_z:.3f} m')
    print(f'[glass] the camera reports the table, so the error is {err:.0f} mm, '
          'and it points away from the arm')
    print(f'[glass] a gripper sent to {table_z:.3f} m travels {err:.0f} mm past the '
          'glass before it closes')

    fig, ax = plt.subplots(figsize=(10.4, 4.8), facecolor='white')
    _plain(ax)
    ax.plot([0], [0], marker='^', color=INK, ms=14)
    ax.text(0.012, 0.062, 'depth\ncamera', fontsize=9.5, ha='left', va='center')
    ax.add_patch(Rectangle((table_z, -0.09), 0.012, 0.18, fc='#c9b89a', ec=INK, lw=1.1))
    ax.text(table_z + 0.022, 0.075, 'table behind', fontsize=9.8, color=INK)
    ax.add_patch(Rectangle((glass_z, -0.055), 0.010, 0.11, fc='#dff0f4', ec=TEAL,
                           lw=1.4, alpha=0.8))
    ax.text(glass_z, 0.072, 'glass front', fontsize=9.8, ha='center', color=TEAL)
    for y, colour, lab in ((0.030, TEAL, 'the dots pass straight through'),
                           (-0.030, GRIP, 'and come back off the table')):
        ax.annotate('', xy=(table_z, y), xytext=(0.02, y),
                    arrowprops=dict(arrowstyle='->', color=colour, lw=1.7))
        ax.text(0.10, y + 0.009, lab, fontsize=9.5, color=colour)
    ax.annotate('', xy=(glass_z, -0.072), xytext=(table_z, -0.072),
                arrowprops=dict(arrowstyle='<->', color=GRIP, lw=2.0))
    ax.text((glass_z + table_z) / 2, -0.086, f'{err:.0f} mm of error', fontsize=11,
            ha='center', weight='bold', color=GRIP)
    ax.set_xlim(-0.03, 0.86)
    ax.set_ylim(-0.105, 0.125)
    ax.set_xlabel('distance from the camera z (m)', fontsize=10)
    ax.set_ylabel('height y (m)', fontsize=10)
    ax.set_title(f'Clear glass reports the table behind it, which is {err:.0f} mm too '
                 'far, and the gripper closes there',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'glass-reads-the-table.svg')


def pixel_to_point() -> None:
    """The projection arithmetic for one pixel, written out."""
    u, v, z = 412.0, 178.0, 0.624
    x = (u - CX) * z / FX
    y = (v - CY) * z / FY
    print(f'[project] fx = {FX:.1f}, fy = {FY:.1f}, cx = {CX:.1f}, cy = {CY:.1f}')
    print(f'[project] pixel ({u:.0f}, {v:.0f}) with depth {z:.3f} m')
    print(f'[project] X = ({u:.0f} - {CX:.1f}) x {z:.3f} / {FX:.0f} = {x:.5f} m')
    print(f'[project] Y = ({v:.0f} - {CY:.1f}) x {z:.3f} / {FY:.0f} = {y:.5f} m')
    print(f'[project] Z = {z:.3f} m, so the point is '
          f'({x * 1000:.1f}, {y * 1000:.1f}, {z * 1000:.0f}) mm')

    fig, ax = plt.subplots(figsize=(10.6, 4.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    lines = [
        ('what the camera gives', f'pixel column u = {u:.0f},   pixel row v = {v:.0f},'
                                  f'   depth Z = {z:.3f} m', INK),
        ('what calibration gives', f'fx = {FX:.0f} px,   fy = {FY:.0f} px,   '
                                   f'cx = {CX:.1f} px,   cy = {CY:.1f} px', MUTED),
        ('sideways', f'X = (u - cx) x Z / fx = ({u:.0f} - {CX:.1f}) x {z:.3f} / '
                     f'{FX:.0f} = {x:+.5f} m', LINK),
        ('up and down', f'Y = (v - cy) x Z / fy = ({v:.0f} - {CY:.1f}) x {z:.3f} / '
                        f'{FY:.0f} = {y:+.5f} m', PURPLE),
        ('forwards', f'Z = {z:.3f} m, straight from the depth map', TEAL),
    ]
    for k, (lab, body, colour) in enumerate(lines):
        y0 = 5.1 - k * 0.92
        ax.text(0.2, y0, lab, fontsize=10.5, weight='bold', color=colour, va='center')
        ax.text(3.0, y0, body, fontsize=10.5, color=INK, va='center', family='monospace')
    ax.add_patch(Rectangle((0.15, 0.18), 9.7, 0.78, fc='#eef4fb', ec=LINK, lw=1.3))
    ax.text(5.0, 0.57, f'one point in the arm\'s own units: '
                       f'({x * 1000:+.1f}, {y * 1000:+.1f}, {z * 1000:.0f}) mm',
            fontsize=12, ha='center', va='center', weight='bold', color=LINK)
    ax.set_title('Turning one depth pixel into one point, with the real arithmetic',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'pixel-to-point.svg')


def _simulated_cloud(rng: np.random.Generator) -> Arr:
    """A made-up table scene as a point cloud, in metres, in the camera's frame."""
    table = np.column_stack([rng.uniform(-0.30, 0.30, 9000),
                             rng.uniform(-0.02, 0.02, 9000),
                             rng.uniform(0.38, 0.92, 9000)])
    table[:, 1] = 0.0 + rng.normal(0, 0.0015, 9000)
    ang = rng.uniform(0, 2 * np.pi, 2600)
    mug = np.column_stack([0.055 + 0.040 * np.cos(ang),
                           rng.uniform(0.0, 0.095, 2600),
                           0.560 + 0.040 * np.sin(ang)])
    ang2 = rng.uniform(0, 2 * np.pi, 2200)
    bowl = np.column_stack([-0.075 + 0.075 * np.cos(ang2),
                            rng.uniform(0.0, 0.045, 2200),
                            0.480 + 0.075 * np.sin(ang2)])
    box = np.column_stack([rng.uniform(-0.26, -0.14, 2000),
                           rng.uniform(0.0, 0.130, 2000),
                           rng.uniform(0.72, 0.86, 2000)])
    cloud = np.vstack([table, mug, bowl, box])
    return cloud


def _cloud_parts(rng: np.random.Generator) -> tuple[Arr, NDArray[np.bool_]]:
    """The simulated cloud, and a flag saying which points are the flat table."""
    cloud = _simulated_cloud(rng)
    is_table = np.zeros(len(cloud), dtype=bool)
    is_table[:9000] = True
    return cloud, is_table


def cloud_from_map() -> None:
    """How many points a depth map gives, and what they look like."""
    rng = np.random.default_rng(17)
    cloud, is_table = _cloud_parts(rng)
    w, h = 640, 480
    pixels = w * h
    valid_fraction = float(_hole_map().mean())
    valid = int(round(pixels * valid_fraction))
    print(f'[cloud] a {w} by {h} depth map has {pixels} pixels, and at '
          f'{valid_fraction * 100:.1f}% filled, the fill of the simulated map above, '
          f'that is {valid} points')
    print(f'[cloud] the simulated scene drawn here holds {len(cloud)} points')
    print(f'[cloud] three floats a point at 4 bytes each is '
          f'{valid * 12 / 1e6:.1f} MB for one frame, and at 30 frames a second '
          f'{valid * 12 * 30 / 1e6:.0f} MB a second')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.7), facecolor='white',
                             gridspec_kw={'wspace': 0.26})
    ax = axes[0]
    _plain(ax)
    ax.scatter(cloud[is_table, 2], cloud[is_table, 0], s=0.5, color='#d2d2d2')
    ax.scatter(cloud[~is_table, 2], cloud[~is_table, 0], s=2.2,
               c=cloud[~is_table, 1], cmap='viridis')
    ax.set_xlabel('distance from the camera z (m)', fontsize=10)
    ax.set_ylabel('sideways position x (m)', fontsize=10)
    ax.set_title(f'Seen from above: {len(cloud)} simulated points, the flat\ntable in '
                 'grey and the three objects coloured by height',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.scatter(cloud[is_table, 0], cloud[is_table, 1], s=0.5, color='#d2d2d2')
    ax.scatter(cloud[~is_table, 0], cloud[~is_table, 1], s=2.2,
               c=cloud[~is_table, 2], cmap='plasma')
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('height above the table y (m)', fontsize=10)
    ax.set_title('Seen from the front: the mug, the bowl and the box\nstand up out '
                 'of the table',
                 fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'cloud-from-map.svg')


def order_does_not_matter() -> None:
    """Max over points survives a reshuffle; a flattened layer does not."""
    pts = np.array([[0.05, 0.02, 0.56],
                    [-0.07, 0.00, 0.48],
                    [0.09, 0.09, 0.57],
                    [-0.22, 0.13, 0.79],
                    [0.00, 0.00, 0.78]])
    w = np.array([[2.0, -1.0, 0.5, 0.0],
                  [0.0, 3.0, -2.0, 1.5],
                  [1.0, 0.5, 1.0, -1.0]])
    b = np.array([-0.4, -0.1, -0.3, 0.2])
    feats = np.maximum(pts @ w + b, 0.0)
    pooled = feats.max(axis=0)
    perm = np.array([3, 0, 4, 2, 1])
    feats2 = np.maximum(pts[perm] @ w + b, 0.0)
    pooled2 = feats2.max(axis=0)
    flat_w = np.linspace(-1.0, 1.0, 15 * 4).reshape(15, 4)
    flat1 = pts.reshape(-1) @ flat_w
    flat2 = pts[perm].reshape(-1) @ flat_w
    print('[order] per-point features, original order:')
    for p, f in zip(pts, feats):
        print(f'[order]   point {p} -> {np.round(f, 4)}')
    print(f'[order] max over points, original order  = {np.round(pooled, 4)}')
    print(f'[order] max over points, reshuffled      = {np.round(pooled2, 4)}')
    print(f'[order] the two agree: {np.allclose(pooled, pooled2)}')
    print(f'[order] flattened layer, original order  = {np.round(flat1, 4)}')
    print(f'[order] flattened layer, reshuffled      = {np.round(flat2, 4)}')
    print(f'[order] biggest change from the reshuffle = '
          f'{np.abs(flat1 - flat2).max():.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), facecolor='white',
                             gridspec_kw={'wspace': 0.2, 'width_ratios': [1.3, 1]})
    ax = axes[0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.8)
    ax.text(0.2, 8.3, 'every point goes through the same small network,',
            fontsize=10.2, weight='bold', color=INK)
    ax.text(0.2, 7.75, 'and we keep the largest value in each column',
            fontsize=10.2, weight='bold', color=INK)
    for k, (p, f) in enumerate(zip(pts, feats)):
        y = 6.8 - k * 0.78
        ax.text(0.2, y, f'({p[0]:+.2f}, {p[1]:+.2f}, {p[2]:.2f})', fontsize=9.4,
                family='monospace', va='center')
        ax.text(3.9, y, '->', fontsize=9.4, va='center', color=MUTED)
        ax.text(4.6, y, '  '.join(f'{x:5.2f}' for x in f), fontsize=9.4,
                family='monospace', va='center', color=LINK)
    ax.plot([4.5, 9.4], [2.55, 2.55], color=INK, lw=1.2)
    ax.text(0.2, 2.10, 'largest in each column', fontsize=9.8, weight='bold',
            va='center')
    ax.text(4.6, 2.10, '  '.join(f'{x:5.2f}' for x in pooled), fontsize=9.8,
            family='monospace', va='center', weight='bold', color=SLIDE)
    ax.text(0.2, 1.40, 'the same points, reshuffled', fontsize=9.8, va='center')
    ax.text(4.6, 1.40, '  '.join(f'{x:5.2f}' for x in pooled2), fontsize=9.8,
            family='monospace', va='center', weight='bold', color=SLIDE)
    ax.text(0.2, 0.55, 'identical, because the largest of a set\ndoes not depend on '
                       'the order',
            fontsize=9.8, color=SLIDE, va='center')
    ax = axes[1]
    _plain(ax)
    x = np.arange(4)
    ax.bar(x - 0.2, flat1, width=0.38, color=LINK, ec=INK, lw=0.8,
           label='original order')
    ax.bar(x + 0.2, flat2, width=0.38, color=GRIP, ec=INK, lw=0.8, label='reshuffled')
    for i in range(4):
        ax.text(x[i] - 0.2, flat1[i] + 0.012 * np.sign(flat1[i]), f'{flat1[i]:.3f}',
                ha='center', fontsize=9, va='bottom' if flat1[i] >= 0 else 'top')
        ax.text(x[i] + 0.2, flat2[i] + 0.012 * np.sign(flat2[i]), f'{flat2[i]:.3f}',
                ha='center', fontsize=9, va='bottom' if flat2[i] >= 0 else 'top')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([f'output {i + 1}' for i in x], fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title('A layer that reads all 15 numbers in a row gives\na different '
                 f'answer, up to {np.abs(flat1 - flat2).max():.2f} different',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False)
    _save(fig, D3_DOC, 'order-does-not-matter.svg')


def voxels_and_occupancy() -> None:
    """Chopping the space into cubes, and what that costs."""
    rng = np.random.default_rng(17)
    cloud = _simulated_cloud(rng)
    lo = np.array([-0.30, -0.02, 0.38])
    side = 1.0
    out = {}
    for mm in (20.0, 5.0, 2.0):
        step = mm / 1000.0
        n = int(round(side / step))
        idx = np.floor((cloud - lo) / step).astype(int)
        keep = np.all((idx >= 0) & (idx < n), axis=1)
        occupied = {tuple(r) for r in idx[keep]}
        dense = n ** 3
        out[mm] = (n, dense, len(occupied))
        print(f'[voxel] {mm:.0f} mm cubes over a 1 m box: {n} x {n} x {n} = {dense} '
              f'cubes, {len(occupied)} of them touched by a point '
              f'({len(occupied) / dense * 100:.3f}%)')
        print(f'[voxel]   one byte a cube is {dense / 1e6:.1f} MB dense, '
              f'against {len(occupied) * 12 / 1e3:.1f} kB for a list of the '
              'occupied ones')

    step = 0.020
    n = int(round(side / step))
    layer = int((0.020 - lo[1]) / step)
    idx = np.floor((cloud - lo) / step).astype(int)
    keep = np.all((idx >= 0) & (idx < n), axis=1) & (idx[:, 1] == layer)
    cells = {(int(a), int(c)) for a, _bb, c in idx[keep]}
    print(f'[voxel] the slice drawn is the 20 mm layer from '
          f'{(layer * 20 + lo[1] * 1000):.0f} mm to '
          f'{(layer * 20 + 20 + lo[1] * 1000):.0f} mm above the table, and '
          f'{len(cells)} of its {n * n} cells hold a point')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9), facecolor='white',
                             gridspec_kw={'wspace': 0.32, 'width_ratios': [1, 1.05]})
    ax = axes[0]
    _plain(ax)
    for a in range(n):
        for c in range(n):
            x0 = lo[0] + a * step
            z0 = lo[2] + c * step
            full = (a, c) in cells
            ax.add_patch(Rectangle((x0, z0), step, step,
                                   fc=LINK if full else 'white',
                                   ec=GRID if not full else INK, lw=0.5))
    ax.set_xlim(lo[0], lo[0] + side)
    ax.set_ylim(lo[2], lo[2] + side)
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('distance z (m)', fontsize=10)
    ax.set_title(f'One 20 mm layer of the grid seen from above:\n{len(cells)} of '
                 f'{n * n} cells in this layer hold a point',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    labels, vals, colours = [], [], []
    for mm in (20.0, 5.0, 2.0):
        _nn, dense, occ = out[mm]
        labels += [f'{mm:.0f} mm\nall cubes', f'{mm:.0f} mm\nfull only']
        vals += [dense / 1e6, occ * 12 / 1e6]
        colours += [GRIP, SLIDE]
    ax.bar(labels, vals, color=colours, ec=INK, lw=0.8)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.7, f'{v:.1f} MB' if v > 1 else f'{v * 1000:.0f} kB',
                ha='center', fontsize=9.6)
    ax.set_yscale('log')
    ax.set_ylim(1e-3, 1e4)
    ax.set_ylabel('memory for one scene (MB, log scale)', fontsize=10)
    ax.tick_params(axis='x', labelsize=8.6)
    ax.set_title('Every cube against only the full ones,\nat three cube sizes',
                 fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'voxels-and-occupancy.svg')


# --------------------------------------------------------------------------
# section 7: learned scenes
# --------------------------------------------------------------------------

BLOBS: list[tuple[float, float, float, float, float, str]] = [
    # x, z, size, opacity, (unused slot kept for clarity), colour
    (-0.26, 0.80, 0.055, 0.95, 0.0, '#8c6239'),   # box, back left
    (-0.20, 0.82, 0.050, 0.95, 0.0, '#9a6d41'),
    (-0.14, 0.80, 0.050, 0.95, 0.0, '#8c6239'),
    (0.055, 0.56, 0.040, 0.95, 0.0, '#dddddd'),   # the mug
    (0.075, 0.58, 0.032, 0.90, 0.0, '#cccccc'),
    (-0.075, 0.48, 0.060, 0.95, 0.0, '#9fb6c4'),  # the bowl
    (-0.09, 0.50, 0.045, 0.90, 0.0, '#8fa8b8'),
    (0.22, 0.70, 0.048, 0.95, 0.0, '#4f7f4f'),    # a plant
    (0.26, 0.74, 0.040, 0.90, 0.0, '#5d8f5d'),
]


def _render_strip(cam: tuple[float, float], look: float, rays: int = 160,
                  samples: int = 48) -> tuple[Arr, Arr, int]:
    """Volume-render the blob scene from one camera, in two dimensions.

    Returns the strip of colours, which blob dominates each ray, and the number of
    density look-ups the render needed.
    """
    cx, cz = cam
    half = np.deg2rad(27.0)
    angles = np.linspace(look - half, look + half, rays)
    t = np.linspace(0.05, 1.10, samples)
    dt = float(t[1] - t[0])
    strip = np.zeros((rays, 3))
    owner = np.full(rays, -1)
    lookups = 0
    for r, a in enumerate(angles):
        px = cx + np.cos(a) * t
        pz = cz + np.sin(a) * t
        dens = np.zeros((len(BLOBS), samples))
        for k, (bx, bz, s, op, _u, _c) in enumerate(BLOBS):
            d2 = (px - bx) ** 2 + (pz - bz) ** 2
            dens[k] = op * np.exp(-d2 / (2 * s ** 2)) * 40.0
            lookups += samples
        total = dens.sum(axis=0)
        alpha = 1.0 - np.exp(-total * dt)
        trans = np.concatenate([[1.0], np.cumprod(1.0 - alpha)[:-1]])
        weight = alpha * trans
        cols = np.array([matplotlib.colors.to_rgb(b[5]) for b in BLOBS])
        share = np.where(total > 1e-9, dens / np.maximum(total, 1e-9), 0.0)
        strip[r] = (weight[None, :] * share * 1.0).sum(axis=1) @ cols
        strip[r] += (1.0 - weight.sum()) * np.array([0.96, 0.96, 0.94])
        contrib = (weight[None, :] * share).sum(axis=1)
        if contrib.max() > 0.08:
            owner[r] = int(np.argmax(contrib))
    return np.clip(strip, 0, 1), owner, lookups


def query_counting() -> None:
    """How many network look-ups one rendered picture needs."""
    w, h = 640, 480
    rays = w * h
    for samples in (32, 64, 128):
        print(f'[queries] {samples} samples a ray x {rays} rays = '
              f'{samples * rays} network look-ups for one picture')
    samples = 64
    print(f'[queries] a detector runs the network once over the whole picture, '
          f'which is {samples * rays:,} times fewer calls')

    fig, ax = plt.subplots(figsize=(10.0, 4.7), facecolor='white')
    _plain(ax)
    labels = ['a detector:\none pass over\nthe picture',
              'radiance field:\n32 samples a ray', 'radiance field:\n64 samples a ray',
              'radiance field:\n128 samples a ray']
    vals = [1, 32 * rays, 64 * rays, 128 * rays]
    ax.bar(labels, vals, color=[SLIDE, LINK, LINK, LINK], ec=INK, lw=0.8)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.6, f'{v:,}', ha='center', fontsize=10)
    ax.set_yscale('log')
    ax.set_ylim(0.5, 1e9)
    ax.set_ylabel('network look-ups for one 640 by 480 picture (log scale)', fontsize=10)
    ax.set_title('A radiance field asks the network once for every sample on every ray',
                 fontsize=12, weight='bold')
    _save(fig, D3_DOC, 'query-counting.svg')


def splat_parameters() -> None:
    """What one blob stores, and what a whole scene of them costs."""
    parts = [('where it is', 3), ('how wide in each direction', 3),
             ('how it is turned', 4), ('how solid it is', 1),
             ('its colour from every side', 48)]
    total = sum(p[1] for p in parts)
    bytes_each = total * 4
    counts = np.array([200_000, 600_000, 1_200_000, 3_000_000])
    mb = counts * bytes_each / 1e6
    print(f'[splat] one blob keeps ' +
          ', '.join(f'{n} for {lab}' for lab, n in parts) +
          f' = {total} numbers')
    print(f'[splat] at 4 bytes a number that is {bytes_each} bytes a blob')
    for c, m in zip(counts, mb):
        print(f'[splat] {c:,} blobs -> {m:.0f} MB')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.7), facecolor='white',
                             gridspec_kw={'wspace': 0.3})
    ax = axes[0]
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.4)
    for k, (lab, n) in enumerate(parts):
        y = 6.2 - k * 0.86
        ax.add_patch(Rectangle((0.3, y - 0.26), 6.2, 0.56, fc=LINK_PALE, ec=LINK, lw=1.0))
        ax.text(0.5, y, lab, fontsize=10.2, va='center', color=INK)
        ax.text(7.0, y, f'{n} number' + ('' if n == 1 else 's'), fontsize=10.2,
                va='center', weight='bold', color=LINK)
    ax.plot([0.3, 9.4], [1.55, 1.55], color=INK, lw=1.2)
    ax.text(0.5, 1.05, 'one blob', fontsize=11, weight='bold', va='center')
    ax.text(7.0, 1.05, f'{total} numbers = {bytes_each} bytes', fontsize=11,
            weight='bold', va='center', color=GRIP)
    ax.set_title('What one Gaussian blob stores', fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.bar([f'{c // 1000:,}k' for c in counts], mb, color=PURPLE, ec=INK, lw=0.8)
    for i, m in enumerate(mb):
        ax.text(i, m + 25, f'{m:.0f} MB', ha='center', fontsize=10)
    ax.set_xlabel('number of blobs in the scene', fontsize=10)
    ax.set_ylabel('memory for the scene (MB)', fontsize=10)
    ax.set_ylim(0, mb.max() * 1.2)
    ax.set_title(f'At {bytes_each} bytes a blob, a scene is '
                 'hundreds of megabytes',
                 fontsize=11.5, weight='bold')
    _save(fig, D3_DOC, 'splat-parameters.svg')


def new_viewpoints() -> None:
    """What a fitted scene gives a robot: a view it never photographed."""
    cam_a = (0.00, 0.02)
    cam_b = (0.52, 0.42)
    look_a = np.deg2rad(90.0)
    look_b = np.deg2rad(150.0)
    strip_a, own_a, look_ups_a = _render_strip(cam_a, look_a)
    strip_b, own_b, look_ups_b = _render_strip(cam_b, look_b)
    mug_blobs = {3, 4}
    seen_a = int(sum(1 for o in own_a if o in mug_blobs))
    seen_b = int(sum(1 for o in own_b if o in mug_blobs))
    rays, samples = 160, 48
    print(f'[views] one strip is {rays} rays x {samples} samples = '
          f'{rays * samples} sample points, which is one network call each in a '
          f'radiance field, and {look_ups_a} blob look-ups with {len(BLOBS)} blobs')
    print(f'[views] from the first camera the mug owns {seen_a} of 160 rays')
    print(f'[views] from the second camera the mug owns {seen_b} of 160 rays')
    set_a = sorted(set(own_a.tolist()) - {-1})
    set_b = sorted(set(own_b.tolist()) - {-1})
    print(f'[views] blobs that own at least one ray: first camera {len(set_a)} '
          f'{set_a}, second camera {len(set_b)} {set_b}, of {len(BLOBS)} in the scene')

    fig = plt.figure(figsize=(11.6, 5.4), facecolor='white')
    gs = fig.add_gridspec(2, 2, height_ratios=[3.2, 1.0], hspace=0.42, wspace=0.26)
    ax = fig.add_subplot(gs[0, :])
    _plain(ax)
    for bx, bz, s, op, _u, c in BLOBS:
        ax.add_patch(Circle((bx, bz), s * 1.9, fc=c, ec='none', alpha=0.55 * op))
    for cam, look, lab, colour, pos in (
            (cam_a, look_a, 'camera 1:\na real photo', LINK, (0.0, -0.105)),
            (cam_b, look_b, 'camera 2:\na view nobody stood at', GRIP, (0.655, 0.26))):
        ax.plot([cam[0]], [cam[1]], marker='^', color=colour, ms=13)
        for sign in (-1, 1):
            a = look + sign * np.deg2rad(27.0)
            ax.plot([cam[0], cam[0] + np.cos(a) * 1.05],
                    [cam[1], cam[1] + np.sin(a) * 1.05], color=colour, lw=1.3, ls='--')
        ax.text(pos[0], pos[1], lab, fontsize=9.6,
                ha='center' if cam is cam_a else 'right', va='center', color=colour)
    ax.text(0.055, 0.63, 'mug', fontsize=9.6, ha='center')
    ax.text(-0.075, 0.41, 'bowl', fontsize=9.6, ha='center')
    ax.text(-0.20, 0.90, 'box', fontsize=9.6, ha='center')
    ax.text(0.24, 0.80, 'plant', fontsize=9.6, ha='center')
    ax.set_xlim(-0.42, 0.68)
    ax.set_ylim(-0.18, 1.00)
    ax.set_xlabel('sideways position x (m)', fontsize=10)
    ax.set_ylabel('distance z (m)', fontsize=10)
    ax.set_title('Nine blobs standing for a table scene, seen from above, '
                 'with two camera positions',
                 fontsize=12, weight='bold')
    for k, (strip, seen, lab, colour) in enumerate(
            ((strip_a, seen_a, 'rendered from camera 1', LINK),
             (strip_b, seen_b, 'rendered from camera 2', GRIP))):
        axs = fig.add_subplot(gs[1, k])
        axs.imshow(strip[None, :, :], aspect='auto')
        axs.set_yticks([])
        axs.set_xticks([0, 80, 159])
        axs.set_xticklabels(['left', 'middle', 'right'], fontsize=9)
        axs.set_title(f'{lab}: the mug fills {seen} of 160 rays', fontsize=10.5,
                      weight='bold', color=colour)
    _save(fig, D3_DOC, 'new-viewpoints.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)

    # 03_open-vocabulary-vision.md
    closed_list()
    list_growth()
    shots_curve()
    thirteen_directions()
    cosine_arithmetic()
    nearest_name()
    handle_in_view()
    scaled_softmax()
    proposals_and_names()
    score_matrix()
    threshold_sweep()
    box_to_mask()
    two_mugs_scene()
    noun_cannot_choose()
    relation_from_geometry()
    opposite_phrases()
    counting_and_denial()
    near_synonyms()
    absent_object()
    cost_on_an_arm()

    # 04_depth-and-3d.md
    flat_picture_is_a_ray()
    depth_map_grid()
    brightness_edge_depth_edge()
    same_picture_two_sizes()
    size_assumption()
    monocular_shape_right_scale_wrong()
    affine_freedom()
    align_then_measure()
    relative_versus_metric()
    stereo_geometry()
    stereo_error()
    texture_is_needed()
    pattern_on_surfaces()
    holes_in_the_depth_map()
    glass_reads_the_table()
    pixel_to_point()
    cloud_from_map()
    order_does_not_matter()
    voxels_and_occupancy()
    query_counting()
    splat_parameters()
    new_viewpoints()

    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
