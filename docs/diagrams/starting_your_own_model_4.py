"""Generate the diagrams for one page of docs/05_neural-networks/13_starting-your-own-model/.

    04_recipes-for-models-that-see-and-understand.md
        -> images/starting-your-own-model/recipes-for-models-that-see-and-understand/

Run with:  python3 starting_your_own_model_4.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints them so the document can quote the same values.

What is real arithmetic or a real measurement here: the two learning curves in
`examples_per_class_curve`, which really train a multinomial logistic
regression by gradient descent in NumPy on drawn pictures and score it on a
held-out set it never saw; the coverage calculation, which counts how often a
random collection of pictures leaves one of the twenty-four conditions short;
the box arithmetic of the drawn scene; the labelling-hour arithmetic; the
binomial chance that a rare class lands badly in a split; the average precision
of jittered detections; the overlap of a polygon of k corners with the true
outline; the mask overlap at a coarse resolution, including the handle on its
own; the pinhole-camera arithmetic for millimetres per pixel; the stereo error
formula; the error budget added in quadrature; the depth regression in
`cue_ambiguity_floor`, which is really fitted and really scored against the
clean truth; the word-counting retriever over the written notes; the Wilson interval
for a test set of n questions; the low-rank adapter parameter counts; and the
token and time arithmetic for a tiled picture.

What is simulated: the camera scene is drawn with ellipses and rectangles
rather than photographed; the pictures the classifier is trained on are drawn
shapes with a seeded random orientation, size, brightness and clutter blob; the
detector outputs are the true boxes moved by seeded random amounts, so the
per-class average precisions are a property of that jitter and not a published
result; the operator requests, the cell notes, the written scene questions
and the free-text answers are lists written in this file; and the depth cue in
the noise-floor measurement is a made-up formula plus seeded noise. Every such
number comes from numpy.random.default_rng with the seed written next to it.
No published model, dataset or benchmark figure appears anywhere in this file.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'starting-your-own-model')
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

DOC: str = 'recipes-for-models-that-see-and-understand'

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


def _blank(ax: Axes, xlim: tuple[float, float] = (0, 10),
           ylim: tuple[float, float] = (0, 10)) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _box(ax: Axes, x: float, y: float, w: float, h: float, colour: str,
         label: str, fs: float = 9.5, alpha: float = 0.25,
         text_colour: str = INK, weight: str = 'normal') -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=alpha,
                           edgecolor=colour, lw=1.4))
    ax.text(x + w / 2, y + h / 2, label, ha='center', va='center', fontsize=fs,
            color=text_colour, weight=weight)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
           colour: str = INK, lw: float = 1.4) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=13,
                                 color=colour, lw=lw, shrinkA=0, shrinkB=0))


def _show(ax: Axes, rgb: Arr, title: str | None = None, fs: float = 10.5) -> None:
    ax.imshow(np.clip(rgb, 0, 1), interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_edgecolor(MUTED)
        side.set_linewidth(0.8)
    if title is not None:
        ax.set_title(title, fontsize=fs, color=INK, weight='bold')


def _draw_box(ax: Axes, box: tuple[float, float, float, float], colour: str,
              label: str | None = None, lw: float = 1.8, fs: float = 8.5,
              above: bool = True) -> None:
    x1, y1, x2, y2 = box
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor=colour,
                           lw=lw))
    if label:
        ty = y1 - 4 if above else y2 + 11
        ax.text(x1, ty, label, fontsize=fs, color=colour, weight='bold',
                va='bottom' if above else 'top')


def _softmax_rows(z: Arr) -> Arr:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


# --------------------------------------------------------------------------
# the simulated camera scene, used by sections 1 to 4
# --------------------------------------------------------------------------

H: int = 480
W: int = 640
F_PX: float = 700.0        # focal length in pixels
Z_TABLE: float = 0.80      # distance to the objects on the table, in metres
GRIP_MARGIN_MM: float = 6.5   # how far out a grasp may be before the fingers miss


def _grid_yx() -> tuple[Arr, Arr]:
    yy, xx = np.meshgrid(np.arange(H, dtype=float), np.arange(W, dtype=float),
                         indexing='ij')
    return yy, xx


def _ellipse(yy: Arr, xx: Arr, cx: float, cy: float, rx: float, ry: float) -> Arr:
    return (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0


def _rect(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)


def _glass(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    """A tumbler: a slightly tapered body with a rounded bottom."""
    cx = (x1 + x2) / 2.0
    half_top = (x2 - x1) / 2.0
    half_bot = half_top * 0.86
    t = np.clip((yy - y1) / max(y2 - y1, 1.0), 0.0, 1.0)
    half = half_top + (half_bot - half_top) * t
    body = (np.abs(xx - cx) <= half) & (yy >= y1) & (yy <= y2)
    foot = _ellipse(yy, xx, cx, y2, half_bot, 7.0) & (yy >= y2)
    return body | foot


def _mug(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    """A mug: a slightly tapered body with a rounded base and a ring handle."""
    cx = (x1 + x2) / 2.0
    half_top = (x2 - x1) / 2.0
    half_bot = half_top * 0.90
    t = np.clip((yy - y1) / max(y2 - y1, 1.0), 0.0, 1.0)
    half = half_top + (half_bot - half_top) * t
    body = (np.abs(xx - cx) <= half) & (yy >= y1) & (yy <= y2 - 6)
    base = _ellipse(yy, xx, cx, y2 - 6, half_bot, 7.0) & (yy >= y2 - 6)
    cy = (y1 + y2) / 2.0
    r_out = (y2 - y1) * 0.30
    r_in = r_out * 0.52
    d = np.sqrt((xx - (cx + half_top)) ** 2 + (yy - cy) ** 2)
    handle = (d <= r_out) & (d >= r_in) & (xx >= cx + half_top - 2)
    return body | base | handle


def _lying_glass(yy: Arr, xx: Arr, cx: float, cy: float, length: float,
                 width: float, deg: float) -> Arr:
    """A glass lying on its side: a rectangle turned by `deg` degrees."""
    a = np.deg2rad(deg)
    u = (xx - cx) * np.cos(a) + (yy - cy) * np.sin(a)
    v = -(xx - cx) * np.sin(a) + (yy - cy) * np.cos(a)
    body = (np.abs(u) <= length / 2.0) & (np.abs(v) <= width / 2.0)
    rim = ((u - length / 2.0) ** 2 / 8.0 ** 2 + v ** 2 / (width / 2.0) ** 2) <= 1.0
    return body | rim


def _scene() -> tuple[Arr, list[dict]]:
    """Draw the table scene and return the colour picture and the object list."""
    yy, xx = _grid_yx()
    rgb = np.zeros((H, W, 3))
    rgb[:] = np.array([0.80, 0.72, 0.60])                     # the table top
    grain = 0.03 * np.sin(xx / 11.0) * np.cos(yy / 37.0)      # a little wood grain
    rgb += grain[:, :, None]
    rgb[:170] = np.array([0.56, 0.58, 0.62])                  # the wall behind

    objects: list[dict] = []

    def _fix(o: dict) -> None:
        ys, xs = np.nonzero(o['mask'])
        o['box'] = (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))
        o['pixels'] = int(o['mask'].sum())

    def add(name: str, mask: NDArray[np.bool_], colour: tuple[float, float, float],
            rare: bool = False) -> None:
        rgb[mask] = np.array(colour)
        for prev in objects:                 # whatever is drawn later is in front
            prev['mask'] = prev['mask'] & ~mask
            _fix(prev)
        o = {'name': name, 'mask': mask, 'rare': rare}
        _fix(o)
        objects.append(o)

    add('mug', _mug(yy, xx, 370, 250, 472, 348), (0.93, 0.93, 0.95))
    add('glass_a', _glass(yy, xx, 120, 252, 172, 372), (0.72, 0.80, 0.86))
    add('glass_c', _glass(yy, xx, 232, 248, 284, 368), (0.74, 0.81, 0.87))
    add('glass_b', _lying_glass(yy, xx, 203, 352, 122, 50, 7.0), (0.62, 0.72, 0.81))
    add('tray', _rect(yy, xx, 508, 300, 624, 362), (0.35, 0.40, 0.46))
    add('bolt', _ellipse(yy, xx, 322, 416, 13, 10), (0.52, 0.50, 0.48), rare=True)
    objects.sort(key=lambda o: ['mug', 'glass_a', 'glass_b', 'glass_c', 'tray',
                                'bolt'].index(o['name']))
    return np.clip(rgb, 0, 1), objects


SCENE_RGB, SCENE_OBJ = _scene()
MM_PER_PX: float = Z_TABLE * 1000.0 / F_PX


# ==========================================================================
# section 1: naming a picture or a region, the classifier
# ==========================================================================

COV_ORIENT: int = 6          # six ways the thing can be lying
COV_LIGHT: int = 4           # four lightings
COV_CELLS: int = COV_ORIENT * COV_LIGHT
COV_NEED: int = 3            # how many examples of each condition we want

CLS_NAMES: list[str] = ['mug', 'glass', 'box', 'tray', 'bolt', 'cable']
N_CLS: int = len(CLS_NAMES)
SIDE: int = 16


def _render(cls: int, rng: np.random.Generator, side: int = SIDE) -> Arr:
    """Draw one grey training picture of class `cls`, with seeded nuisance variation."""
    g = np.linspace(-1.0, 1.0, side)
    xx, yy = np.meshgrid(g, g)
    ang = float(rng.choice(np.arange(COV_ORIENT) * (np.pi / COV_ORIENT)))
    ca, sa = np.cos(ang), np.sin(ang)
    ox, oy = rng.uniform(-0.18, 0.18, 2)
    s = rng.uniform(0.85, 1.15)
    u = ((xx - ox) * ca + (yy - oy) * sa) / s
    v = (-(xx - ox) * sa + (yy - oy) * ca) / s

    if cls == 0:                                   # mug: body plus a handle blob
        m = (np.abs(u) < 0.40) & (np.abs(v) < 0.50)
        m |= ((u - 0.52) ** 2 + v ** 2) < 0.17 ** 2
    elif cls == 1:                                 # glass: narrow and tall
        m = (np.abs(u) < 0.21) & (np.abs(v) < 0.62)
    elif cls == 2:                                 # box: square
        m = (np.abs(u) < 0.46) & (np.abs(v) < 0.46)
    elif cls == 3:                                 # tray: wide and flat
        m = (np.abs(u) < 0.74) & (np.abs(v) < 0.19)
    elif cls == 4:                                 # bolt head: a disc
        m = (u ** 2 + v ** 2) < 0.33 ** 2
    else:                                          # cable: a thin wavy line
        m = np.abs(v - 0.34 * np.sin(3.1 * u)) < 0.075

    level = int(rng.integers(0, COV_LIGHT))        # one of four lightings
    bright = 0.52 + 0.14 * level
    back = 0.06 + 0.07 * level
    img = np.where(m, bright, back)
    if rng.random() < 0.35:                        # a clutter blob somewhere
        cx, cy = rng.uniform(-1.0, 1.0, 2)
        r = rng.uniform(0.06, 0.15)
        img = np.where(((xx - cx) ** 2 + (yy - cy) ** 2) < r ** 2,
                       rng.uniform(0.2, 0.9), img)
    img = img + rng.normal(0.0, 0.07, img.shape)
    return np.clip(img, 0.0, 1.0)


def _summaries(img: Arr) -> Arr:
    """Eight numbers about the object in the picture, instead of its 256 pixels."""
    on = img > 0.5 * (img.max() + img.min())
    if on.sum() < 3:
        return np.zeros(8)
    ys, xs = np.nonzero(on)
    h = (ys.max() - ys.min() + 1) / img.shape[0]
    w = (xs.max() - xs.min() + 1) / img.shape[1]
    area = on.mean()
    fill = on.sum() / max((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1), 1)
    inner = on[1:-1, 1:-1]
    edge = (inner & ~(on[:-2, 1:-1] & on[2:, 1:-1] & on[1:-1, :-2] & on[1:-1, 2:]))
    rim = edge.sum() / max(on.sum(), 1)
    pts = np.stack([ys - ys.mean(), xs - xs.mean()])
    ev = np.linalg.eigvalsh(np.cov(pts) + 1e-9 * np.eye(2))
    elong = float(np.sqrt(max(ev[1], 1e-9) / max(ev[0], 1e-9)))
    return np.array([area, max(w, h), min(w, h), fill, rim, elong,
                     float(img[on].mean()), float(img[~on].mean() if (~on).any() else 0.0)])


def _batch(n_per_class: int, seed: int) -> tuple[Arr, Arr, NDArray[np.int64]]:
    """Return raw pixels, the eight summaries, and the labels, for n pictures a class."""
    rng = np.random.default_rng(seed)
    pix, sm, lab = [], [], []
    for c in range(N_CLS):
        for _ in range(n_per_class):
            img = _render(c, rng)
            pix.append(img.ravel())
            sm.append(_summaries(img))
            lab.append(c)
    return np.array(pix), np.array(sm), np.array(lab, dtype=np.int64)


def _logreg(xtr: Arr, ytr: NDArray[np.int64], xte: Arr, yte: NDArray[np.int64],
            steps: int = 700, lr: float = 1.2, wd: float = 3e-3) -> float:
    """Train a multinomial logistic regression by gradient descent, return accuracy."""
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-8
    a = np.hstack([(xtr - mu) / sd, np.ones((len(xtr), 1))])
    b = np.hstack([(xte - mu) / sd, np.ones((len(xte), 1))])
    wt = np.zeros((a.shape[1], N_CLS))
    target = np.eye(N_CLS)[ytr]
    for _ in range(steps):
        p = _softmax_rows(a @ wt)
        wt -= lr * (a.T @ (p - target) / len(a) + wd * wt)
    return float(np.mean(np.argmax(b @ wt, axis=1) == yte))


CURVE_N: list[int] = [2, 4, 8, 16, 32, 64, 128, 256]
CURVE: dict[str, list[float]] = {}


def examples_per_class_curve() -> None:
    """How a real held-out score climbs with the number of examples a class."""
    pix_te, sm_te, y_te = _batch(120, seed=99)          # 720 held-out pictures
    raw, summ = [], []
    for n in CURVE_N:
        r_acc, s_acc = [], []
        for rep in range(4):
            pix_tr, sm_tr, y_tr = _batch(n, seed=1000 + 37 * rep + n)
            r_acc.append(_logreg(pix_tr, y_tr, pix_te, y_te))
            s_acc.append(_logreg(sm_tr, y_tr, sm_te, y_te))
        raw.append(float(np.mean(r_acc)))
        summ.append(float(np.mean(s_acc)))
    CURVE['raw'] = raw
    CURVE['summ'] = summ
    print('[1b] held-out accuracy of a really trained classifier, 6 classes, '
          f'{len(y_te)} held-out pictures, mean of 4 runs')
    for n, r, s in zip(CURVE_N, raw, summ):
        print(f'      n={n:4d} per class   raw 256 pixels {r:.3f}   eight summaries {s:.3f}')
    chance = 1.0 / N_CLS
    print(f'      chance level {chance:.3f}')
    for name, vals in (('raw', raw), ('summaries', summ)):
        best = vals[-1]
        reach = next((n for n, v in zip(CURVE_N, vals) if v >= 0.9 * best), None)
        print(f'      {name}: best {best:.3f}, within a tenth of it from n={reach}')

    fig, ax = plt.subplots(figsize=(10.2, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(CURVE_N, summ, marker='o', color=TEAL, lw=2.2,
            label='a head on eight summary numbers (stands in for reused features)')
    ax.plot(CURVE_N, raw, marker='s', color=PURPLE, lw=2.2,
            label='the same head on all 256 raw pixels (stands in for from scratch)')
    ax.axhline(chance, color=MUTED, ls=':', lw=1.4)
    ax.text(CURVE_N[0], chance + 0.015, 'guessing (1 in 6)', fontsize=9, color=MUTED)
    ax.set_xscale('log')
    ax.set_xticks(CURVE_N)
    ax.set_xticklabels([str(n) for n in CURVE_N])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel('training pictures per class (log scale)', fontsize=10)
    ax.set_ylabel('accuracy on 720 held-out pictures', fontsize=10)
    ax.set_title('Simulated data: reused features reach their own ceiling by about 32 a class,\n'
                 'raw pixels still climb at 256', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.grid(axis='y', color=GRID, lw=0.7)
    _save(fig, DOC, 'examples-per-class-curve.svg')


def classifier_example_files() -> None:
    """What one training example is: one picture file and one word."""
    rng = np.random.default_rng(7)
    fig = plt.figure(figsize=(11.0, 5.0), facecolor='white')
    gs = fig.add_gridspec(2, N_CLS, height_ratios=[1.3, 1.0], hspace=0.08, wspace=0.25)
    for c in range(N_CLS):
        ax = fig.add_subplot(gs[0, c])
        _show(ax, np.repeat(_render(c, rng)[:, :, None], 3, axis=2))
        ax.set_title(CLS_NAMES[c], fontsize=10.5, weight='bold', color=TEAL)
        ax.set_xlabel(f'{CLS_NAMES[c]}/img_{c:02d}1.png', fontsize=8.5, color=MUTED)
    ax = fig.add_subplot(gs[1, :])
    _blank(ax, (0, 10), (0, 10))
    lines = ['train/', '  mug/     img_001.png  img_002.png  ...',
             '  glass/   img_011.png  ...', '  box/     ...', '  tray/    ...',
             '  bolt/    ...', '  cable/   ...', 'val/     the same six folders']
    ax.text(0.2, 9.4, 'one example = one picture file in a folder named after its one label',
            fontsize=10.5, weight='bold', color=INK, va='top')
    for i, ln in enumerate(lines):
        ax.text(0.4, 8.2 - 1.03 * i, ln, fontsize=9.5, family='monospace', color=INK,
                va='top')
    ax.text(5.6, 8.2, 'The label is a single word for the whole picture.\n'
                      'There is no position, no size and no outline in it,\n'
                      'so the training needs nobody to draw anything.\n\n'
                      'One person can take and sort a few hundred\n'
                      'pictures in an afternoon, which is why this is\n'
                      'the cheapest labelled data of any seeing job.',
            fontsize=10, color=INK, va='top')
    fig.suptitle('A classifier\'s training example: a file and a word, and nothing else',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'one-example-classifier.svg')
    print('[1a] six simulated classes drawn: ' + ', '.join(CLS_NAMES))


def covering_the_conditions() -> None:
    """How many pictures a random collection needs before every condition is covered."""
    rng = np.random.default_rng(4242)
    sizes = [24, 48, 96, 144, 192, 288, 384, 480]
    trials = 4000
    probs = []
    for n in sizes:
        draws = rng.integers(0, COV_CELLS, size=(trials, n))
        ok = 0
        for row in draws:
            counts = np.bincount(row, minlength=COV_CELLS)
            ok += int(counts.min() >= COV_NEED)
        probs.append(ok / trials)
    print(f'[1c] {COV_CELLS} conditions ({COV_ORIENT} ways of lying x {COV_LIGHT} lightings), '
          f'each wanted at least {COV_NEED} times, {trials} simulated collections each')
    for n, p in zip(sizes, probs):
        print(f'      n={n:4d} pictures   chance every condition is covered {p:.3f}')
    first = next((n for n, p in zip(sizes, probs) if p >= 0.9), None)
    print(f'      first size in this list with a 9 in 10 chance: {first}')

    one = rng.integers(0, COV_CELLS, size=96)
    counts = np.bincount(one, minlength=COV_CELLS).reshape(COV_ORIENT, COV_LIGHT)
    short = int((counts < COV_NEED).sum())
    empty = int((counts == 0).sum())
    print(f'      one collection of 96: {short} of {COV_CELLS} conditions short of '
          f'{COV_NEED}, {empty} of them with nothing at all')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    ax1.imshow(counts, cmap='Blues', vmin=0, vmax=counts.max(), aspect='auto')
    for i in range(COV_ORIENT):
        for j in range(COV_LIGHT):
            v = int(counts[i, j])
            if v < COV_NEED:
                tc = GRIP
            else:
                tc = 'white' if v >= 0.7 * counts.max() else INK
            ax1.text(j, i, str(v), ha='center', va='center', fontsize=11,
                     weight='bold', color=tc)
    ax1.set_xticks(range(COV_LIGHT))
    ax1.set_xticklabels(['dim', 'room', 'bright', 'window'], fontsize=9.5)
    ax1.set_yticks(range(COV_ORIENT))
    ax1.set_yticklabels(['upright', 'tipped', 'on side', 'upside\ndown', 'half\nhidden',
                         'at an\nangle'], fontsize=9.5)
    ax1.set_title(f'96 pictures taken at random:\n{short} of {COV_CELLS} conditions are '
                  f'short of {COV_NEED} (red)', fontsize=11, weight='bold')
    _plain(ax2)
    ax2.plot(sizes, probs, marker='o', color=TEAL, lw=2.2)
    ax2.axhline(0.9, color=GRIP, ls='--', lw=1.4)
    ax2.text(sizes[0], 0.915, 'a 9 in 10 chance', fontsize=9, color=GRIP)
    ax2.set_xlabel('pictures taken at random', fontsize=10)
    ax2.set_ylabel(f'chance all {COV_CELLS} conditions got {COV_NEED} or more', fontsize=10)
    ax2.set_ylim(0, 1.03)
    ax2.set_title('The number of examples is set by the conditions,\nnot by the number of '
                  'classes', fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    _save(fig, DOC, 'covering-the-conditions.svg')


def one_name_is_not_a_place() -> None:
    """A whole-picture label gives the arm nothing to reach for."""
    mug = next(o for o in SCENE_OBJ if o['name'] == 'mug')
    x1, y1, x2, y2 = mug['box']
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    cx, cy = W / 2.0, H / 2.0
    d_px = float(np.hypot(mx - cx, my - cy))
    d_mm = d_px * MM_PER_PX
    glasses = [o for o in SCENE_OBJ if o['name'].startswith('glass')]
    gx = [(o['box'][0] + o['box'][2]) / 2.0 for o in glasses]
    spread_px = max(gx) - min(gx)
    spread_mm = spread_px * MM_PER_PX
    print(f'[1d] millimetres per pixel at {Z_TABLE:.2f} m with a focal length of '
          f'{F_PX:.0f} pixels: {MM_PER_PX:.3f}')
    print(f'      the mug\'s middle is {d_px:.0f} pixels from the middle of the picture, '
          f'which is {d_mm:.0f} mm')
    print(f'      the three glasses\' middles span {spread_px:.0f} pixels, '
          f'which is {spread_mm:.0f} mm, against a gripper margin of {GRIP_MARGIN_MM} mm')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.3, 1.0]})
    _show(ax1, SCENE_RGB)
    ax1.plot([cx], [cy], marker='+', ms=16, mew=2.4, color=GRIP)
    ax1.plot([mx], [my], marker='o', ms=9, color=TEAL)
    ax1.annotate('', xy=(mx, my), xytext=(cx, cy),
                 arrowprops=dict(arrowstyle='<->', color=PURPLE, lw=1.8))
    ax1.text((cx + mx) / 2 + 48, (cy + my) / 2 - 32, f'{d_px:.0f} px = {d_mm:.0f} mm',
             fontsize=10.5, color=PURPLE, weight='bold', ha='center')
    ax1.text(cx - 10, cy + 34, 'middle of the picture', fontsize=9, color=GRIP,
             ha='right')
    ax1.text(mx, my + 72, 'middle of the mug', fontsize=9, color=TEAL, ha='center')
    for o in glasses:
        _draw_box(ax1, o['box'], LINK, lw=1.2)
    ax1.set_title('The classifier\'s whole answer: "mug"', fontsize=11.5, weight='bold')
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.2, 9.6, 'what the classifier gives', fontsize=10.5, weight='bold', color=INK,
             va='top')
    ax2.text(0.4, 8.7, 'one word: mug', fontsize=10, family='monospace', color=TEAL, va='top')
    ax2.text(0.2, 7.6, 'what the arm needs before it moves', fontsize=10.5, weight='bold',
             color=INK, va='top')
    for i, ln in enumerate(['where the mug is, to about 6.5 mm',
                            'which of the three glasses was meant',
                            'how wide to open the fingers']):
        ax2.text(0.4, 6.7 - 0.95 * i, '- ' + ln, fontsize=10, color=INK, va='top')
    ax2.text(0.2, 3.3, f'Reaching for the middle of the picture instead\n'
                       f'of the mug misses by {d_mm:.0f} mm, and the gripper\n'
                       f'tolerates about {GRIP_MARGIN_MM:.1f} mm, so the answer is\n'
                       f'{d_mm / GRIP_MARGIN_MM:.0f} times too coarse to act on.',
             fontsize=10.5, color=GRIP, va='top')
    fig.suptitle('A name for the whole picture is not a place on the table',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'one-name-is-not-a-place.svg')


# ==========================================================================
# section 2: finding a thing, the detector
# ==========================================================================

DET_CLASSES: list[str] = ['mug', 'glass', 'tray', 'bolt']


def _yolo_lines() -> list[tuple[str, float, float, float, float]]:
    """The scene's boxes written the way a detector's label file writes them."""
    rows = []
    for o in SCENE_OBJ:
        x1, y1, x2, y2 = o['box']
        name = 'glass' if o['name'].startswith('glass') else o['name']
        rows.append((name, ((x1 + x2) / 2) / W, ((y1 + y2) / 2) / H,
                     (x2 - x1) / W, (y2 - y1) / H))
    return rows


def detector_label_file() -> None:
    """2a: one training example is a picture and one line per object."""
    rows = _yolo_lines()
    print('[2a] the scene as a detector label file, '
          f'{len(rows)} lines for {len(rows)} objects')
    for name, cx, cy, bw, bh in rows:
        print(f'      {name:6s} {cx:.4f} {cy:.4f} {bw:.4f} {bh:.4f}')
    areas = {}
    for o in SCENE_OBJ:
        x1, y1, x2, y2 = o['box']
        name = 'glass' if o['name'].startswith('glass') else o['name']
        areas.setdefault(name, []).append((x2 - x1) * (y2 - y1))
    for name in DET_CLASSES:
        a = float(np.mean(areas[name]))
        print(f'      {name:6s} box area {a:8.0f} px, '
              f'side {np.sqrt(a):5.1f} px, {np.sqrt(a) * MM_PER_PX:5.1f} mm')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.25, 1.0]})
    _show(ax1, SCENE_RGB)
    cols = {'mug': TEAL, 'glass': LINK, 'tray': PURPLE, 'bolt': GRIP}
    for o in SCENE_OBJ:
        name = 'glass' if o['name'].startswith('glass') else o['name']
        _draw_box(ax1, o['box'], cols[name], name, lw=1.8,
                  above=o['name'] not in ('bolt', 'tray'))
    ax1.set_title('frame_0417.png: six objects, so six lines', fontsize=11.5,
                  weight='bold')
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.8, 'frame_0417.txt', fontsize=10.5, weight='bold',
             family='monospace', color=INK, va='top')
    ax2.text(0.1, 9.0, 'class   middle x  middle y    width   height',
             fontsize=9, color=MUTED, va='top', family='monospace')
    for i, (name, cx, cy, bw, bh) in enumerate(rows):
        ax2.text(0.1, 8.3 - 0.78 * i,
                 f'{name:6s}  {cx:.4f}    {cy:.4f}    {bw:.4f}   {bh:.4f}',
                 fontsize=9, family='monospace', color=cols[name], va='top')
    ax2.text(0.1, 3.0, 'The four numbers are fractions of the picture, so the\n'
                       'same line means the same box at any picture size.\n'
                       'Somebody had to draw all six boxes by hand, and a\n'
                       'missed object is not a gap in the file but a positive\n'
                       'statement that there is nothing there.',
             fontsize=10, color=INK, va='top')
    fig.suptitle("A detector's training example: one picture file and one line an object",
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'one-example-detector.svg')


def boxes_and_hours() -> None:
    """2b: what drawing the boxes actually costs, in hours."""
    per_pic = len(SCENE_OBJ)
    secs = np.arange(4, 31, 1, dtype=float)
    sizes = [300, 800, 2000]
    print(f'[2b] {per_pic} boxes a picture; hours = pictures x {per_pic} x seconds / 3600')
    rows = {}
    for n in sizes:
        hours = n * per_pic * secs / 3600.0
        rows[n] = hours
        for sv in (6.0, 12.0, 20.0):
            h = n * per_pic * sv / 3600.0
            print(f'      {n:5d} pictures at {sv:4.0f} s a box: '
                  f'{n * per_pic:6d} boxes, {h:6.1f} hours, {h / 7.5:4.1f} working days')

    fig, ax = plt.subplots(figsize=(10.2, 5.2), facecolor='white')
    _plain(ax)
    for n, colour in zip(sizes, (TEAL, LINK, PURPLE)):
        ax.plot(secs, rows[n], color=colour, lw=2.2,
                label=f'{n} pictures ({n * per_pic} boxes)')
    for h, lab in ((7.5, 'one working day'), (37.5, 'one working week')):
        ax.axhline(h, color=GRIP, ls='--', lw=1.3)
        ax.text(secs[-1] - 0.3, h + 1.6, lab, fontsize=9, color=GRIP, ha='right')
    ax.set_xlabel('seconds to draw and name one box', fontsize=10)
    ax.set_ylabel('hours of somebody drawing boxes', fontsize=10)
    ax.set_title('Six boxes a picture: the labelling bill is a straight line through '
                 'your own speed', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.grid(axis='y', color=GRID, lw=0.7)
    _save(fig, DOC, 'boxes-and-hours.svg')


RARE_PICS: int = 14          # pictures in which the rare class happens to appear
HOLD_FRAC: float = 0.2       # the share of pictures kept back


def _binom_le(k: int, n: int, p: float) -> float:
    """The chance of at most k successes out of n, worked out term by term."""
    tot = 0.0
    for i in range(k + 1):
        tot += float(np.exp(
            np.sum(np.log(np.arange(n - i + 1, n + 1))) - np.sum(np.log(np.arange(1, i + 1)))
            + i * np.log(p) + (n - i) * np.log(1 - p)))
    return tot


def rare_class_split() -> None:
    """2c: a class that appears in a few pictures cannot be measured at all."""
    ks = np.arange(4, 81, 2)
    p_one = np.array([_binom_le(1, int(k), HOLD_FRAC) for k in ks])
    p_four = np.array([_binom_le(4, int(k), HOLD_FRAC) for k in ks])
    at14 = _binom_le(1, RARE_PICS, HOLD_FRAC)
    need = next(int(k) for k in ks if _binom_le(4, int(k), HOLD_FRAC) <= 0.1)
    print(f'[2c] a {HOLD_FRAC:.0%} held-out split taken picture by picture')
    print(f'      a class in {RARE_PICS} pictures: chance the held-out side gets 0 or 1 '
          f'of them is {at14:.3f}')
    for k in (10, 20, 40, 60, 80):
        print(f'      a class in {k:3d} pictures: chance of 0 or 1 held out '
              f'{_binom_le(1, k, HOLD_FRAC):.3f}, of 4 or fewer '
              f'{_binom_le(4, k, HOLD_FRAC):.3f}')
    print(f'      first count with a 9 in 10 chance of at least 5 held-out examples: {need}')

    counts = {'glass': 300 * 3, 'mug': 300, 'tray': 300, 'bolt': 300,
              'cracked cup': RARE_PICS}
    print('      instances in 300 pictures of the scene: ' +
          ', '.join(f'{k} {v}' for k, v in counts.items()))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    _plain(ax1)
    names = list(counts)
    vals = [counts[n] for n in names]
    colours = [LINK, TEAL, PURPLE, WRIST, GRIP]
    ax1.barh(names, vals, color=colours, alpha=0.85)
    for i, v in enumerate(vals):
        ax1.text(v + 18, i, str(v), va='center', fontsize=10, weight='bold',
                 color=colours[i])
    ax1.set_xlim(0, 1050)
    ax1.set_xlabel('labelled instances in 300 pictures', fontsize=10)
    ax1.set_title('Five classes in one set of 300 pictures,\nand one of them is barely there',
                  fontsize=11, weight='bold')
    _plain(ax2)
    ax2.plot(ks, p_one, marker='o', ms=4, color=GRIP, lw=2.0,
             label='held-out side gets 0 or 1 of them')
    ax2.plot(ks, p_four, marker='s', ms=4, color=LINK, lw=2.0,
             label='held-out side gets 4 or fewer')
    ax2.axvline(RARE_PICS, color=MUTED, ls=':', lw=1.4)
    ax2.text(RARE_PICS + 0.9, 0.025, f'{RARE_PICS} instances', fontsize=9,
             color=MUTED)
    ax2.axhline(0.1, color=SLIDE, ls='--', lw=1.3)
    ax2.text(62, 0.125, 'a 1 in 10 risk', fontsize=9, color=SLIDE)
    ax2.set_xlabel('labelled instances of that one class', fontsize=10)
    ax2.set_ylabel('chance of too few in the held-out set', fontsize=10)
    ax2.set_ylim(0, 1.0)
    ax2.set_title(f'At {RARE_PICS} instances there is a {at14:.0%} chance the held-out set\n'
                  'cannot say anything about that class', fontsize=11, weight='bold')
    ax2.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    _save(fig, DOC, 'rare-class-split.svg')


def _iou(a: tuple[float, float, float, float],
         b: tuple[float, float, float, float]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _ap(scores: Arr, hits: NDArray[np.bool_], n_true: int) -> float:
    """Average precision: the area under the precision and recall curve."""
    order = np.argsort(-scores)
    h = hits[order]
    tp = np.cumsum(h)
    fp = np.cumsum(~h)
    rec = tp / max(n_true, 1)
    prec = tp / np.maximum(tp + fp, 1)
    mrec = np.concatenate([[0.0], rec, [1.0]])
    mpre = np.concatenate([[0.0], prec, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.nonzero(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


DET_JITTER: float = 6.0      # pixels of error on each edge of every guessed box
DET_PICS: int = 60


def _simulate_detections(seed: int = 606) -> dict:
    """Move every true box by the same number of pixels and score the result."""
    rng = np.random.default_rng(seed)
    out: dict[str, dict] = {c: {'scores': [], 'hits50': [], 'hits75': [], 'n': 0}
                            for c in DET_CLASSES}
    for _ in range(DET_PICS):
        dx, dy = rng.normal(0, 14, 2)
        for o in SCENE_OBJ:
            cls = 'glass' if o['name'].startswith('glass') else o['name']
            x1, y1, x2, y2 = o['box']
            true = (x1 + dx, y1 + dy, x2 + dx, y2 + dy)
            guess = tuple(float(v + e) for v, e in
                          zip(true, rng.normal(0, DET_JITTER, 4)))
            v = _iou(true, guess)
            out[cls]['n'] += 1
            out[cls]['scores'].append(float(np.clip(rng.normal(0.85, 0.08), 0.02, 0.999)))
            out[cls]['hits50'].append(v >= 0.5)
            out[cls]['hits75'].append(v >= 0.75)
        for cls in DET_CLASSES:          # one wrong guess a picture a class
            out[cls]['scores'].append(float(np.clip(rng.normal(0.40, 0.16), 0.02, 0.999)))
            out[cls]['hits50'].append(False)
            out[cls]['hits75'].append(False)
    res = {}
    for cls in DET_CLASSES:
        sc = np.array(out[cls]['scores'])
        res[cls] = {
            'ap50': _ap(sc, np.array(out[cls]['hits50']), out[cls]['n']),
            'ap75': _ap(sc, np.array(out[cls]['hits75']), out[cls]['n']),
            'scores': sc, 'hits50': np.array(out[cls]['hits50']), 'n': out[cls]['n']}
    return res


def average_precision() -> None:
    """2d: the mean hides the class you care about."""
    res = _simulate_detections()
    m50 = float(np.mean([res[c]['ap50'] for c in DET_CLASSES]))
    m75 = float(np.mean([res[c]['ap75'] for c in DET_CLASSES]))
    print(f'[2d] simulated detections: every guessed box moved by {DET_JITTER:.0f} pixels '
          f'of error on each edge, {DET_PICS} pictures')
    for c in DET_CLASSES:
        side = np.sqrt(np.mean([(o['box'][2] - o['box'][0]) * (o['box'][3] - o['box'][1])
                                for o in SCENE_OBJ
                                if ('glass' if o['name'].startswith('glass')
                                    else o['name']) == c]))
        print(f'      {c:6s} box side {side:5.1f} px   '
              f'AP at 0.5 {res[c]["ap50"]:.3f}   AP at 0.75 {res[c]["ap75"]:.3f}')
    print(f'      mean over the four classes: {m50:.3f} at 0.5 and {m75:.3f} at 0.75')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    cls = 'bolt'
    sc, hits, n = res[cls]['scores'], res[cls]['hits50'], res[cls]['n']
    order = np.argsort(-sc)
    tp = np.cumsum(hits[order])
    fp = np.cumsum(~hits[order])
    _plain(ax1)
    ax1.plot(tp / n, tp / np.maximum(tp + fp, 1), color=GRIP, lw=2.2, label='bolt')
    sc2, hits2, n2 = res['mug']['scores'], res['mug']['hits50'], res['mug']['n']
    o2 = np.argsort(-sc2)
    tp2, fp2 = np.cumsum(hits2[o2]), np.cumsum(~hits2[o2])
    ax1.plot(tp2 / n2, tp2 / np.maximum(tp2 + fp2, 1), color=TEAL, lw=2.2, label='mug')
    ax1.set_xlabel('share of the real objects found (recall)', fontsize=10)
    ax1.set_ylabel('share of the guesses that were right (precision)', fontsize=10)
    ax1.set_xlim(0, 1.02)
    ax1.set_ylim(0, 1.05)
    ax1.set_title(f'The same box error: mug {res["mug"]["ap50"]:.2f}, '
                  f'bolt {res["bolt"]["ap50"]:.2f}', fontsize=11, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax1.grid(color=GRID, lw=0.7)
    _plain(ax2)
    xs = np.arange(len(DET_CLASSES))
    ax2.bar(xs - 0.19, [res[c]['ap50'] for c in DET_CLASSES], 0.36, color=LINK,
            alpha=0.9, label='AP at an overlap of 0.5')
    ax2.bar(xs + 0.19, [res[c]['ap75'] for c in DET_CLASSES], 0.36, color=PURPLE,
            alpha=0.9, label='AP at an overlap of 0.75')
    for i, c in enumerate(DET_CLASSES):
        ax2.text(i - 0.19, res[c]['ap50'] + 0.02, f'{res[c]["ap50"]:.2f}', ha='center',
                 fontsize=9, color=LINK, weight='bold')
        ax2.text(i + 0.19, res[c]['ap75'] + 0.02, f'{res[c]["ap75"]:.2f}', ha='center',
                 fontsize=9, color=PURPLE, weight='bold')
    ax2.axhline(m50, color=GRIP, ls='--', lw=1.4)
    ax2.text(2.6, m50 + 0.03, f'the mean, {m50:.2f}', fontsize=9.5, color=GRIP)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(DET_CLASSES, fontsize=10)
    ax2.set_ylim(0, 1.42)
    ax2.set_ylabel('average precision', fontsize=10)
    ax2.set_title('The small object is the worst, and the mean does not say so',
                  fontsize=11, weight='bold')
    ax2.legend(fontsize=9, frameon=False, loc='upper right')
    _save(fig, DOC, 'average-precision.svg')


# ==========================================================================
# section 3: which pixels, the segmenter
# ==========================================================================

PART_R0: float = 62.0        # the irregular part's mean radius, in pixels
PART_CX: float = 150.0
PART_CY: float = 150.0
GRID_N: int = 300


def _part_radius(theta: Arr) -> Arr:
    """The outline of a simulated irregular part, as a radius at each angle."""
    return PART_R0 * (1.0 + 0.22 * np.sin(3.0 * theta) + 0.10 * np.cos(7.0 * theta)
                      - 0.07 * np.sin(5.0 * theta + 0.6))


def _part_mask() -> NDArray[np.bool_]:
    yy, xx = np.meshgrid(np.arange(GRID_N, dtype=float),
                         np.arange(GRID_N, dtype=float), indexing='ij')
    th = np.arctan2(yy - PART_CY, xx - PART_CX)
    r = np.sqrt((xx - PART_CX) ** 2 + (yy - PART_CY) ** 2)
    return r <= _part_radius(th)


def _poly_mask(k: int) -> tuple[NDArray[np.bool_], Arr]:
    """The mask a person gets by clicking k corners evenly round the outline."""
    from matplotlib.path import Path as MplPath
    th = np.linspace(0.0, 2.0 * np.pi, k, endpoint=False)
    pts = np.stack([PART_CX + _part_radius(th) * np.cos(th),
                    PART_CY + _part_radius(th) * np.sin(th)], axis=1)
    yy, xx = np.meshgrid(np.arange(GRID_N, dtype=float),
                         np.arange(GRID_N, dtype=float), indexing='ij')
    inside = MplPath(pts).contains_points(np.stack([xx.ravel(), yy.ravel()], axis=1))
    return inside.reshape(GRID_N, GRID_N), pts


POLY_K: list[int] = [3, 4, 6, 8, 12, 16, 24, 32, 48]
POLY_IOU: dict[int, float] = {}
BOX_IOU_PART: float = 0.0


def polygon_clicks() -> None:
    """3a: how many clicks an outline really takes, measured on a drawn part."""
    global BOX_IOU_PART
    true = _part_mask()
    ys, xs = np.nonzero(true)
    box = (xs.min(), ys.min(), xs.max(), ys.max())
    box_area = (box[2] - box[0] + 1) * (box[3] - box[1] + 1)
    BOX_IOU_PART = float(true.sum() / box_area)
    for k in POLY_K:
        pm, _ = _poly_mask(k)
        POLY_IOU[k] = float((pm & true).sum() / (pm | true).sum())
    print(f'[3a] a simulated irregular part of {int(true.sum())} pixels; its box holds '
          f'{int(box_area)} pixels, so the box alone overlaps the part by '
          f'{BOX_IOU_PART:.3f}')
    for k in POLY_K:
        print(f'      {k:3d} clicks round the outline: overlap {POLY_IOU[k]:.3f}')
    first95 = next(k for k in POLY_K if POLY_IOU[k] >= 0.95)
    first98 = next(k for k in POLY_K if POLY_IOU[k] >= 0.98)
    print(f'      {first95} clicks reach an overlap of 0.95 and {first98} reach 0.98, '
          f'against 2 clicks for a box')

    fig = plt.figure(figsize=(11.8, 5.0), facecolor='white')
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.6], wspace=0.3)
    for i, k in enumerate((4, 8, 16)):
        ax = fig.add_subplot(gs[0, i])
        pm, pts = _poly_mask(k)
        rgb = np.ones((GRID_N, GRID_N, 3))
        rgb[true] = np.array([0.80, 0.88, 0.92])
        rgb[pm & ~true] = np.array([0.95, 0.72, 0.72])
        rgb[true & ~pm] = np.array([0.98, 0.88, 0.60])
        lo, hi = int(PART_CX - PART_R0 * 1.55), int(PART_CX + PART_R0 * 1.55)
        _show(ax, rgb[lo:hi, lo:hi])
        ax.add_patch(Polygon(pts - lo, closed=True, fill=False, edgecolor=PURPLE,
                             lw=1.6))
        ax.plot(pts[:, 0] - lo, pts[:, 1] - lo, 'o', ms=4.5, color=PURPLE)
        ax.set_title(f'{k} clicks\noverlap {POLY_IOU[k]:.3f}', fontsize=10.5,
                     weight='bold')
    ax = fig.add_subplot(gs[0, 3])
    _plain(ax)
    ax.plot(POLY_K, [POLY_IOU[k] for k in POLY_K], marker='o', color=TEAL, lw=2.2)
    ax.axhline(BOX_IOU_PART, color=GRIP, ls='--', lw=1.4)
    ax.text(POLY_K[-1], BOX_IOU_PART - 0.045,
            f'a box, 2 clicks: {BOX_IOU_PART:.2f}', fontsize=9, color=GRIP, ha='right')
    ax.axhline(0.95, color=SLIDE, ls=':', lw=1.3)
    ax.text(3, 0.96, 'overlap 0.95', fontsize=9, color=SLIDE)
    ax.set_xlabel('clicks round the outline', fontsize=10)
    ax.set_ylabel('overlap with the true outline', fontsize=10)
    ax.set_ylim(0.3, 1.02)
    ax.set_title(f'{first95} clicks for 0.95, against 2 for a box',
                 fontsize=11, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('What an outline costs: the overlap climbs with every click, and so '
                 'does the bill', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'polygon-clicks.svg')


def prompt_or_train() -> None:
    """3b: the far cheaper route is to prompt a promptable model."""
    k95 = next(k for k in POLY_K if POLY_IOU[k] >= 0.95)
    n_masks = 300
    per_pic = len(SCENE_OBJ)
    sec_click = 1.5
    overhead = 6.0
    poly_h = n_masks * per_pic * (k95 * sec_click + overhead) / 3600.0
    box_h = n_masks * per_pic * (2 * sec_click + overhead) / 3600.0
    check_h = n_masks * per_pic * 4.0 / 3600.0      # looking at what came back
    print(f'[3b] {n_masks} pictures, {per_pic} objects each, {sec_click} s a click '
          f'and {overhead} s of overhead an object')
    print(f'      outlining every object with {k95} clicks: {poly_h:.1f} hours')
    print(f'      drawing a box round every object: {box_h:.1f} hours')
    print(f'      prompting a promptable model with those boxes and checking the masks: '
          f'{check_h:.1f} hours and no masks drawn at all')
    print(f'      the outlining route costs {poly_h / check_h:.1f} times the checking '
          f'route and {poly_h - check_h:.1f} hours more')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.3]})
    _plain(ax1)
    labels = [f'train a segmenter:\noutline {n_masks * per_pic} objects',
              f'train a detector:\nbox {n_masks * per_pic} objects',
              'prompt a promptable model:\ncheck what it returns']
    vals = [poly_h, box_h, check_h]
    cols = [GRIP, WRIST, TEAL]
    ax1.barh(labels, vals, color=cols, alpha=0.9)
    for i, v in enumerate(vals):
        ax1.text(v + 1.2, i, f'{v:.1f} h', va='center', fontsize=10.5, weight='bold',
                 color=cols[i])
    ax1.set_xlim(0, max(vals) * 1.25)
    ax1.set_xlabel('hours of somebody labelling', fontsize=10)
    ax1.set_title('The same 1800 objects, three ways', fontsize=11, weight='bold')
    ax1.invert_yaxis()
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.8, 'the prompting route, at run time', fontsize=11, weight='bold',
             color=INK, va='top')
    steps = [('camera frame', LINK_PALE), ('a detector or a phrase\ngives one box',
              LINK), ('promptable segmenter\nreturns the pixels in it', TEAL),
             ('grasp width across\nthe mask, in mm', SLIDE)]
    for i, (txt, col) in enumerate(steps):
        _box(ax2, 0.3, 7.6 - 2.0 * i, 4.4, 1.5, col, txt, fs=9.5, alpha=0.3)
        if i < len(steps) - 1:
            _arrow(ax2, (2.5, 7.6 - 2.0 * i), (2.5, 7.25 - 2.0 * i))
    ax2.text(5.3, 9.0, 'What it costs instead of labelling:\n\n'
                       '- two models in the loop rather than one,\n'
                       '  so two things to load and two to time;\n'
                       '- the masks carry no class name, so the\n'
                       '  box has to come from somewhere;\n'
                       '- a point prompt is genuinely ambiguous,\n'
                       '  so a box prompt is the safer one;\n'
                       '- you cannot improve it by labelling more,\n'
                       '  because you are not training it.',
             fontsize=10, color=INK, va='top')
    fig.suptitle('Prompting a promptable segmenter needs no masks drawn at all',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'prompt-or-train.svg')


def where_the_overlap_goes() -> None:
    """3c: a coarse mask is fine on the body and poor on the thin part."""
    mug = next(o for o in SCENE_OBJ if o['name'] == 'mug')
    mask = mug['mask']
    x1, y1, x2, y2 = (int(v) for v in mug['box'])
    crop = mask[y1:y2 + 1, x1:x2 + 1]
    hh, ww = crop.shape
    body_cols = int(0.72 * ww)
    handle = np.zeros_like(crop)
    handle[:, body_cols:] = crop[:, body_cols:]
    rows = []
    for g in (7, 14, 28, 56):
        ys = (np.arange(hh) * g // hh).clip(0, g - 1)
        xs = (np.arange(ww) * g // ww).clip(0, g - 1)
        small = np.zeros((g, g))
        cnt = np.zeros((g, g))
        np.add.at(small, (ys[:, None], xs[None, :]), crop.astype(float))
        np.add.at(cnt, (ys[:, None], xs[None, :]), 1.0)
        coarse = (small / np.maximum(cnt, 1)) >= 0.5
        back = coarse[ys[:, None], xs[None, :]]
        all_iou = float((back & crop).sum() / (back | crop).sum())
        hs = (back & (np.arange(ww) >= body_cols)[None, :])
        h_iou = float((hs & handle).sum() / max((hs | handle).sum(), 1))
        wrong = int((back != crop).sum())
        wrong_handle = int(((back != crop) & (np.arange(ww) >= body_cols)[None, :]).sum())
        rows.append((g, all_iou, h_iou, wrong, wrong_handle))
    print('[3c] the mug\'s mask drawn on a coarse grid and stretched back to its box of '
          f'{ww} by {hh} pixels')
    for g, a, h, wr, wh in rows:
        print(f'      {g:3d} by {g:3d}: overlap on the whole mug {a:.3f}, on the handle '
              f'{h:.3f}, {wr} wrong pixels of which {wh} are in the handle '
              f'({100.0 * wh / max(wr, 1):.0f} per cent)')

    fig = plt.figure(figsize=(12.0, 4.6), facecolor='white')
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 1.9], wspace=0.3)
    for i, g in enumerate((7, 14, 28, 56)):
        ax = fig.add_subplot(gs[0, i])
        ys = (np.arange(hh) * g // hh).clip(0, g - 1)
        xs = (np.arange(ww) * g // ww).clip(0, g - 1)
        small = np.zeros((g, g)); cnt = np.zeros((g, g))
        np.add.at(small, (ys[:, None], xs[None, :]), crop.astype(float))
        np.add.at(cnt, (ys[:, None], xs[None, :]), 1.0)
        back = ((small / np.maximum(cnt, 1)) >= 0.5)[ys[:, None], xs[None, :]]
        rgb = np.ones((hh, ww, 3))
        rgb[crop] = np.array([0.80, 0.88, 0.92])
        rgb[back & ~crop] = np.array([0.95, 0.72, 0.72])
        rgb[crop & ~back] = np.array([0.98, 0.88, 0.60])
        _show(ax, rgb)
        ax.set_title(f'{g} by {g}\nall {rows[i][1]:.3f}\nhandle {rows[i][2]:.3f}',
                     fontsize=10, weight='bold')
    ax = fig.add_subplot(gs[0, 4])
    _plain(ax)
    gsz = [r[0] for r in rows]
    ax.plot(gsz, [r[1] for r in rows], marker='o', color=TEAL, lw=2.2,
            label='the whole mug')
    ax.plot(gsz, [r[2] for r in rows], marker='s', color=GRIP, lw=2.2,
            label='the handle on its own')
    ax.set_xscale('log')
    ax.set_xticks(gsz)
    ax.set_xticklabels([str(g) for g in gsz])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_ylim(0, 1.05)
    ax.set_xlabel('the grid the mask is drawn on', fontsize=10)
    ax.set_ylabel('overlap with the true mask', fontsize=10)
    ax.set_title('The handle stays wrong long after the\nwhole-mug number looks fine',
                 fontsize=11, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('Where a mask\'s error actually sits: in the thin part the arm has to '
                 'take hold of', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'where-the-overlap-goes.svg')


def _narrow_width_px(mask: NDArray[np.bool_]) -> float:
    """The narrowest row across the object, ignoring rows where little of it shows."""
    widths = []
    for row in mask:
        xs = np.nonzero(row)[0]
        if len(xs) > 2:
            widths.append(float(xs.max() - xs.min() + 1))
    if not widths:
        return 0.0
    w = np.array(widths)
    return float(w[w >= 0.5 * w.max()].min())


def do_you_need_pixels() -> None:
    """3d: the two tests that say whether a box will do."""
    fills, narrow = {}, {}
    for o in SCENE_OBJ:
        x1, y1, x2, y2 = (int(v) for v in o['box'])
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        fills[o['name']] = o['pixels'] / area
        narrow[o['name']] = _narrow_width_px(o['mask']) * MM_PER_PX
    gb = next(o for o in SCENE_OBJ if o['name'] == 'glass_b')
    x1, y1, x2, y2 = (int(v) for v in gb['box'])
    inside = np.zeros_like(gb['mask'])
    inside[y1:y2 + 1, x1:x2 + 1] = True
    others = np.zeros_like(gb['mask'])
    for o in SCENE_OBJ:
        if o['name'] in ('glass_a', 'glass_c'):
            others |= o['mask']
    stray = int((inside & others).sum())
    box_area = (x2 - x1 + 1) * (y2 - y1 + 1)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    on_target = bool(gb['mask'][cy, cx])
    print('[3d] how much of each box is the object, and how narrow the object is')
    for o in SCENE_OBJ:
        print(f'      {o["name"]:8s} box fill {fills[o["name"]]:.3f}   '
              f'narrow way {narrow[o["name"]]:5.1f} mm')
    print(f'      the middle glass\'s box holds {stray} pixels of the other two glasses, '
          f'{100.0 * stray / box_area:.1f} per cent of the box')
    print(f'      the middle of that box lands on the middle glass: {on_target}')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    pad = 78
    sub = SCENE_RGB[max(y1 - pad, 0):y2 + 40, max(x1 - 60, 0):x2 + 60].copy()
    oy, ox = max(y1 - pad, 0), max(x1 - 60, 0)
    sm = others[max(y1 - pad, 0):y2 + 40, max(x1 - 60, 0):x2 + 60]
    im = inside[max(y1 - pad, 0):y2 + 40, max(x1 - 60, 0):x2 + 60]
    sub[sm & im] = np.array([0.95, 0.55, 0.55])
    _show(ax1, sub)
    _draw_box(ax1, (x1 - ox, y1 - oy, x2 - ox, y2 - oy), PURPLE, 'box of the middle glass')
    ax1.plot([cx - ox], [cy - oy], marker='+', ms=14, mew=2.2, color=INK)
    ax1.text(cx - ox + 6, cy - oy + 16, 'middle of the box', fontsize=9, color=INK)
    ax1.set_title(f'{stray} pixels inside this box belong to the\nglasses either side of it',
                  fontsize=11, weight='bold')
    _plain(ax2)
    names = [o['name'] for o in SCENE_OBJ]
    xs = np.arange(len(names))
    ax2.bar(xs, [fills[n] for n in names], 0.6, color=LINK, alpha=0.9)
    for i, n in enumerate(names):
        ax2.text(i, fills[n] + 0.015, f'{fills[n]:.2f}', ha='center', fontsize=9.5,
                 weight='bold', color=LINK)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([f'{n}\n{narrow[n]:.0f} mm' for n in names], fontsize=9.5)
    ax2.set_ylim(0, 1.12)
    ax2.set_ylabel('share of the box that is really the object', fontsize=10)
    ax2.set_title('The bar is how much of the box is really the object;\nunder each name '
                  'is the narrow way across its pixels', fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('Two tests that say whether you need pixels or a box will do',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'do-you-need-pixels.svg')


# ==========================================================================
# section 4: depth and the third dimension
# ==========================================================================

STEREO_BASE_MM: float = 60.0     # how far apart two cameras sit
MATCH_PX: float = 0.25           # how well a stereo pair can match one pixel


def _stereo_error_mm(z_m: Arr | float) -> Arr | float:
    """Depth error from a quarter of a pixel of matching error, in millimetres."""
    z_mm = np.asarray(z_m, dtype=float) * 1000.0
    return z_mm ** 2 * MATCH_PX / (F_PX * STEREO_BASE_MM)


def calibrate_before_training() -> None:
    """4a: a degree of calibration error costs more than most depth models do."""
    degs = np.linspace(0.0, 2.0, 81)
    dists = [0.4, 0.8, 1.6]
    print('[4a] position error from a turned camera, worked out as distance x tan(angle)')
    for d in dists:
        for deg in (0.2, 0.5, 1.0, 2.0):
            e = d * 1000.0 * np.tan(np.deg2rad(deg))
            print(f'      at {d:.1f} m a {deg:.1f} degree error moves the point by '
                  f'{e:5.1f} mm')
    cross = {d: np.rad2deg(np.arctan(GRIP_MARGIN_MM / (d * 1000.0))) for d in dists}
    for d in dists:
        print(f'      at {d:.1f} m the whole {GRIP_MARGIN_MM} mm margin is used up by '
              f'{cross[d]:.3f} of a degree')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(ax1)
    for d, colour in zip(dists, (TEAL, LINK, PURPLE)):
        ax1.plot(degs, d * 1000.0 * np.tan(np.deg2rad(degs)), color=colour, lw=2.2,
                 label=f'object at {d:.1f} m')
    ax1.axhline(GRIP_MARGIN_MM, color=GRIP, ls='--', lw=1.5)
    ax1.text(1.95, 2.6, f'the whole gripper margin, {GRIP_MARGIN_MM} mm',
             fontsize=9.5, color=GRIP, ha='right')
    ax1.set_xlabel('error in the camera-to-arm angle (degrees)', fontsize=10)
    ax1.set_ylabel('how far out the point lands (mm)', fontsize=10)
    ax1.set_ylim(0, 60)
    ax1.set_title('Half a degree of calibration error is already\nmost of the margin',
                  fontsize=11, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax1.grid(color=GRID, lw=0.7)
    _plain(ax2)
    zs = np.linspace(0.25, 2.0, 120)
    ax2.plot(zs, _stereo_error_mm(zs), color=TEAL, lw=2.2,
             label=f'two cameras {STEREO_BASE_MM:.0f} mm apart, {MATCH_PX} px of matching error')
    ax2.plot(zs, 1000.0 * zs * np.tan(np.deg2rad(0.5)), color=GRIP, lw=2.2, ls='--',
             label='half a degree of calibration error')
    ax2.axhline(GRIP_MARGIN_MM, color=MUTED, ls=':', lw=1.4)
    ax2.text(0.27, GRIP_MARGIN_MM + 1.0, f'{GRIP_MARGIN_MM} mm margin', fontsize=9,
             color=MUTED)
    ax2.set_xlabel('distance to the object (m)', fontsize=10)
    ax2.set_ylabel('error contributed (mm)', fontsize=10)
    ax2.set_ylim(0, 40)
    ax2.set_title('Out to about a metre the calibration is the\nbigger of the two errors',
                  fontsize=11, weight='bold')
    ax2.legend(fontsize=9, frameon=False, loc='upper left')
    ax2.grid(color=GRID, lw=0.7)
    fig.suptitle('Before training any depth model, find out what the calibration is '
                 'already costing', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'calibrate-before-training.svg')


def where_depth_labels_come_from() -> None:
    """4b: a depth label is only as good as whatever measured it."""
    mug = next(o for o in SCENE_OBJ if o['name'] == 'mug')
    x1, y1, x2, y2 = mug['box']
    mug_px = y2 - y1
    real_h_mm = mug_px * MM_PER_PX
    size_err = Z_TABLE * 1000.0 / mug_px          # one pixel of size error, in mm
    sources = [('two cameras, 0.25 px matched', float(_stereo_error_mm(Z_TABLE)), TEAL),
               ('a known object 1 px bigger\nor smaller than measured', size_err, LINK),
               ('a steel rule held up by hand', 1.0, SLIDE)]
    print(f'[4b] the mug stands {mug_px:.0f} pixels tall, which at {Z_TABLE:.2f} m is '
          f'{real_h_mm:.0f} mm')
    for name, err, _ in sources:
        print(f'      {name.replace(chr(10), " "):48s} {err:6.1f} mm of error in the label')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.2, 1.0]})
    _plain(ax1)
    names = [s[0] for s in sources[:3]]
    vals = [s[1] for s in sources[:3]]
    cols = [s[2] for s in sources[:3]]
    ax1.barh(names, vals, color=cols, alpha=0.9)
    for i, v in enumerate(vals):
        ax1.text(v + 0.25, i, f'{v:.1f} mm', va='center', fontsize=10.5, weight='bold',
                 color=cols[i])
    ax1.axvline(GRIP_MARGIN_MM, color=GRIP, ls='--', lw=1.5)
    ax1.text(GRIP_MARGIN_MM + 0.2, 2.68, f'gripper margin, {GRIP_MARGIN_MM} mm',
             fontsize=9, color=GRIP, va='center')
    ax1.set_xlim(0, 12)
    ax1.set_xlabel(f'error the label carries at {Z_TABLE:.2f} m (mm)', fontsize=10)
    ax1.set_title('Three honest ways to get a metric depth label',
                  fontsize=11, weight='bold')
    ax1.invert_yaxis()
    ax1.set_ylim(2.95, -0.65)
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.8, 'one training example for a metric depth model', fontsize=10.5,
             weight='bold', color=INK, va='top')
    rows = ['frame_0417.png        the colour picture',
            'frame_0417_depth.png  one distance a pixel,',
            '                      in millimetres',
            'frame_0417.json       the camera\'s focal length,',
            '                      centre, and the pose it',
            '                      was at when the frame',
            '                      was taken']
    for i, r in enumerate(rows):
        ax2.text(0.3, 8.9 - 0.80 * i, r, fontsize=9.5, family='monospace', color=INK,
                 va='top')
    ax2.text(0.1, 2.6, 'A missing camera file makes the pair useless, because\n'
                       'a distance in millimetres means nothing without the\n'
                       'focal length that turns a pixel into a direction.',
             fontsize=10, color=GRIP, va='top')
    fig.suptitle('A depth model cannot be better than the thing that measured its labels',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'where-depth-labels-come-from.svg')


AMBIG_MM: list[float] = [0.0, 0.4, 1.0, 2.0]   # how much the real object's height varies
AMBIG_N: list[int] = [20, 50, 120, 300, 800, 2000]
AMBIG_RES: dict[float, list[float]] = {}
OBJ_H_MM: float = 80.0                        # the nominal height of the thing measured


def _depth_cue(n: int, spread: float, rng: np.random.Generator,
               bias: float = 0.0) -> tuple[Arr, Arr, Arr]:
    """A made-up cue. Apparent size pins the distance only if the height is known.

    Returns the model's inputs, the labels it is trained on, and the clean truth.
    """
    z = rng.uniform(300.0, 1200.0, n)                       # true distance in mm
    h = OBJ_H_MM + rng.normal(0.0, spread, n)               # this one's real height
    size = F_PX * h / z + rng.normal(0.0, 0.3, n)           # apparent height in pixels,
                                                            # measured to a third of one
    blur = 0.0040 * (z - 650.0) + rng.normal(0.0, 1.2, n)   # a weak second cue
    x = np.stack([F_PX * OBJ_H_MM / size, blur, np.ones(n)], axis=1)
    return x, z + bias, z


def cue_ambiguity_floor() -> None:
    """4c: a really fitted depth model stops where its cue stops saying anything."""
    print('[4c] a depth model really fitted by least squares on a simulated cue, scored '
          'against the clean truth on 6000 held-out examples')
    for spread in AMBIG_MM:
        errs = []
        for n in AMBIG_N:
            reps = []
            for rep in range(6):
                r = np.random.default_rng(31337 + 101 * rep + n)
                x_tr, y_tr, _ = _depth_cue(n, spread, r)
                beta, *_ = np.linalg.lstsq(x_tr, y_tr, rcond=None)
                te = np.random.default_rng(555 + rep)
                x_te, _, z_te = _depth_cue(6000, spread, te)
                reps.append(float(np.mean(np.abs(x_te @ beta - z_te))))
            errs.append(float(np.mean(reps)))
        AMBIG_RES[spread] = errs
        pct = 100.0 * spread / OBJ_H_MM
        print(f'      height varies by {spread:4.1f} mm ({pct:4.1f} per cent of '
              f'{OBJ_H_MM:.0f} mm): ' +
              '  '.join(f'n={n}:{e:5.1f}' for n, e in zip(AMBIG_N, errs)))
    for spread in AMBIG_MM:
        v = AMBIG_RES[spread]
        print(f'      height varies by {spread:4.1f} mm: from {v[0]:.1f} mm at 20 examples '
              f'to {v[-1]:.1f} mm at 2000, a gain of {v[0] - v[-1]:.1f} mm')

    bias_rows = []
    for n in (50, 300, 2000):
        reps = []
        for rep in range(6):
            r = np.random.default_rng(900 + 17 * rep + n)
            x_tr, y_tr, _ = _depth_cue(n, 1.0, r, bias=5.0)
            beta, *_ = np.linalg.lstsq(x_tr, y_tr, rcond=None)
            te = np.random.default_rng(777 + rep)
            x_te, _, z_te = _depth_cue(6000, 1.0, te)
            reps.append(float(np.mean(x_te @ beta - z_te)))
        bias_rows.append((n, float(np.mean(reps))))
    print('      with every label measured 5.0 mm too far away:')
    for n, b in bias_rows:
        print(f'      n={n:5d}  the model is {b:+.2f} mm out on average, and more '
              f'examples do not help')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.3, 1.0]})
    _plain(ax1)
    for spread, colour in zip(AMBIG_MM, (SLIDE, TEAL, LINK, GRIP)):
        ax1.plot(AMBIG_N, AMBIG_RES[spread], marker='o', color=colour, lw=2.2,
                 label=f'real height varies by {spread:.1f} mm of {OBJ_H_MM:.0f}')
    ax1.axhline(GRIP_MARGIN_MM, color=MUTED, ls='--', lw=1.4)
    ax1.text(AMBIG_N[0], GRIP_MARGIN_MM + 0.6, f'{GRIP_MARGIN_MM} mm gripper margin',
             fontsize=9.5, color=MUTED)
    ax1.set_xscale('log')
    ax1.set_xticks(AMBIG_N)
    ax1.set_xticklabels([str(n) for n in AMBIG_N])
    ax1.xaxis.set_minor_formatter(plt.NullFormatter())
    ax1.set_xlabel('training examples (log scale)', fontsize=10)
    ax1.set_ylabel('average error against the clean truth (mm)', fontsize=10)
    ax1.set_ylim(0, 22)
    ax1.set_title('Each curve flattens where its cue runs out,\nand more examples '
                  'never go below that', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax1.grid(axis='y', color=GRID, lw=0.7)
    _plain(ax2)
    ax2.bar([str(n) for n, _ in bias_rows], [b for _, b in bias_rows], 0.5, color=GRIP,
            alpha=0.9)
    for i, (n, b) in enumerate(bias_rows):
        ax2.text(i, b + 0.12, f'{b:+.2f} mm', ha='center', fontsize=10.5, weight='bold',
                 color=GRIP)
    ax2.axhline(5.0, color=INK, ls='--', lw=1.5)
    ax2.text(-0.44, 5.15, 'the ruler was 5 mm out', fontsize=9.5, color=INK)
    ax2.set_ylim(0, 7.6)
    ax2.set_xlabel('training examples', fontsize=10)
    ax2.set_ylabel('average error left in the model (mm)', fontsize=10)
    ax2.set_title('A measuring mistake that never varies\ngoes into the model and '
                  'stays', fontsize=11.5, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('Two floors a depth model cannot get under: an ambiguous cue and a '
                 'biased ruler', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'cue-ambiguity-floor.svg')


def depth_error_budget() -> None:
    """4d: add the millimetres up and fix the biggest one."""
    terms = [('depth reading', 4.0, 4.0, TEAL),
             ('camera-to-arm angle', 0.5, 0.2, GRIP),
             ('camera-to-arm offset', 2.0, 2.0, LINK),
             ('middle of the mask, 3 px', 3.0, 3.0, PURPLE)]
    def mm(name: str, v: float) -> float:
        if name == 'camera-to-arm angle':
            return float(Z_TABLE * 1000.0 * np.tan(np.deg2rad(v)))
        if name == 'middle of the mask, 3 px':
            return float(v * MM_PER_PX)
        return float(v)
    before = [mm(n, a) for n, a, _, _ in terms]
    after = [mm(n, b) for n, _, b, _ in terms]
    tot_b = float(np.sqrt(np.sum(np.square(before))))
    tot_a = float(np.sqrt(np.sum(np.square(after))))
    print('[4d] an error budget, added in quadrature, for a grasp at '
          f'{Z_TABLE:.2f} m')
    for (n, a, b, _), eb, ea in zip(terms, before, after):
        print(f'      {n:26s} {eb:5.2f} mm  ->  {ea:5.2f} mm')
    print(f'      total {tot_b:.2f} mm against a margin of {GRIP_MARGIN_MM} mm: '
          f'{"fails" if tot_b > GRIP_MARGIN_MM else "passes"}')
    print(f'      after turning the angle error from 0.5 to 0.2 degrees: {tot_a:.2f} mm, '
          f'{"fails" if tot_a > GRIP_MARGIN_MM else "passes"}')
    print(f'      the angle alone is {100.0 * before[1] ** 2 / tot_b ** 2:.0f} per cent '
          f'of the squared total before the fix')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(ax1)
    names = [t[0] for t in terms]
    xs = np.arange(len(names))
    ax1.bar(xs - 0.19, before, 0.36, color=LINK, alpha=0.9, label='as found')
    ax1.bar(xs + 0.19, after, 0.36, color=SLIDE, alpha=0.9,
            label='after calibrating the angle')
    for i in range(len(names)):
        ax1.text(i - 0.19, before[i] + 0.15, f'{before[i]:.1f}', ha='center', fontsize=9,
                 color=LINK, weight='bold')
        ax1.text(i + 0.19, after[i] + 0.15, f'{after[i]:.1f}', ha='center', fontsize=9,
                 color=SLIDE, weight='bold')
    ax1.set_xticks(xs)
    ax1.set_xticklabels(['depth\nreading', 'camera\nangle', 'camera\noffset',
                         'middle of\nthe mask'], fontsize=9.5)
    ax1.set_ylabel('error contributed (mm)', fontsize=10)
    ax1.set_ylim(0, 9)
    ax1.set_title('Four things that each add millimetres', fontsize=11, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax1.grid(axis='y', color=GRID, lw=0.7)
    _plain(ax2)
    ax2.bar(['as found', 'after calibrating'], [tot_b, tot_a], 0.5,
            color=[GRIP, SLIDE], alpha=0.9)
    for i, v in enumerate([tot_b, tot_a]):
        ax2.text(i, v + 0.60, f'{v:.2f} mm', ha='center', fontsize=11, weight='bold',
                 color=[GRIP, SLIDE][i])
    ax2.axhline(GRIP_MARGIN_MM, color=INK, ls='--', lw=1.6)
    ax2.text(-0.56, GRIP_MARGIN_MM + 0.24, f'{GRIP_MARGIN_MM} mm margin', fontsize=10,
             color=INK)
    ax2.set_xlim(-0.65, 1.6)
    ax2.set_ylim(0, 11)
    ax2.set_ylabel('all four added in quadrature (mm)', fontsize=10)
    ax2.set_title('Calibrating the angle fixed the grasp;\ntraining a depth model would '
                  'not have', fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('The error budget tells you what to work on, and it is usually not '
                 'the model', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'depth-error-budget.svg')


# ==========================================================================
# section 5: a language model job
# ==========================================================================

COMMANDS: dict[str, str] = {
    'open_gripper': 'open the gripper fingers release let go',
    'close_gripper': 'close the gripper fingers grip hold shut',
    'home': 'go home return to the home position start',
    'stop': 'stop halt everything now at once',
    'pick_from_tray': 'pick take a part from off the tray lift out',
    'place_on_tray': 'place put the part on the tray down set',
    'move_up': 'move up raise the tool higher millimetres',
    'move_down': 'move down lower the tool a little millimetres',
    'slower': 'slow down slower gently easy',
    'faster': 'speed up faster quicker',
    'take_photo': 'take a photo picture image frame of the tray',
    'run_inspection': 'run the inspection inspect check the part for cracks',
}

REQUESTS: list[tuple[str, str]] = [
    ('open the gripper', 'open_gripper'),
    ('let go of it', 'open_gripper'),
    ('release the part', 'open_gripper'),
    ('open it', 'open_gripper'),
    ('close the gripper', 'close_gripper'),
    ('grip it', 'close_gripper'),
    ('hold on to the part', 'close_gripper'),
    ('shut the fingers', 'close_gripper'),
    ('go home', 'home'),
    ('return to the home position', 'home'),
    ('back to the start', 'home'),
    ('stop', 'stop'),
    ('stop now please', 'stop'),
    ('freeze', 'stop'),
    ('stop everything at once', 'stop'),
    ('pick the part from the tray', 'pick_from_tray'),
    ('take a part off the tray', 'pick_from_tray'),
    ('lift one out of the tray', 'pick_from_tray'),
    ('fetch me a part', 'pick_from_tray'),
    ('put it on the tray', 'place_on_tray'),
    ('place the part on the tray', 'place_on_tray'),
    ('set it down on the tray', 'place_on_tray'),
    ('give the part back', 'place_on_tray'),
    ('move up', 'move_up'),
    ('lift the tool up a bit', 'move_up'),
    ('raise it', 'move_up'),
    ('move the tool up by ten millimetres', 'move_up'),
    ('move down', 'move_down'),
    ('lower the tool', 'move_down'),
    ('go down a little', 'move_down'),
    ('slow down', 'slower'),
    ('go slower', 'slower'),
    ('take it easy', 'slower'),
    ('speed up', 'faster'),
    ('go faster', 'faster'),
    ('quicker please', 'faster'),
    ('take a photo', 'take_photo'),
    ('take a picture of the tray', 'take_photo'),
    ('grab a frame', 'take_photo'),
    ('run the inspection', 'run_inspection'),
    ('inspect the part', 'run_inspection'),
    ('check the part for cracks', 'run_inspection'),
]

STOP_WORDS: set[str] = {'the', 'a', 'an', 'to', 'of', 'it', 'is', 'in', 'on', 'at',
                        'for', 'me', 'please', 'and', 'by', 'off', 'out', 'one',
                        'bit', 'little', 'now', 'be', 'that', 'this'}


def _words(text: str) -> list[str]:
    return [w for w in text.lower().replace('?', ' ').replace('.', ' ').split()
            if w not in STOP_WORDS]


def _tfidf_match(queries: list[str], docs: list[str]) -> NDArray[np.int64]:
    """Rank the documents for each query by shared rare words, and return the order."""
    vocab = sorted({w for d in docs for w in _words(d)} |
                   {w for q in queries for w in _words(q)})
    idx = {w: i for i, w in enumerate(vocab)}
    dm = np.zeros((len(docs), len(vocab)))
    for i, d in enumerate(docs):
        for w in _words(d):
            dm[i, idx[w]] += 1.0
    df = (dm > 0).sum(axis=0)
    weight = np.log((1.0 + len(docs)) / (1.0 + df)) + 1.0
    dm = dm * weight
    dm /= np.maximum(np.linalg.norm(dm, axis=1, keepdims=True), 1e-9)
    qm = np.zeros((len(queries), len(vocab)))
    for i, q in enumerate(queries):
        for w in _words(q):
            qm[i, idx[w]] += 1.0
    qm = qm * weight
    qm /= np.maximum(np.linalg.norm(qm, axis=1, keepdims=True), 1e-9)
    return np.argsort(-(qm @ dm.T), axis=1)


def word_list_baseline() -> None:
    """5a: the baseline a language model has to beat is a list of words."""
    names = list(COMMANDS)
    order = _tfidf_match([r for r, _ in REQUESTS], [COMMANDS[n] for n in names])
    right, wrong = [], []
    for (req, want), row in zip(REQUESTS, order):
        got = names[int(row[0])]
        (right if got == want else wrong).append((req, want, got))
    n = len(REQUESTS)
    print(f'[5a] matching {n} written requests against {len(names)} commands by '
          f'shared rare words, with no model at all')
    print(f'      right {len(right)} of {n} ({len(right) / n:.1%}), wrong {len(wrong)}')
    for req, want, got in wrong:
        print(f'      wrong: "{req}" wanted {want}, matched {got}')
    per = {}
    for nm in names:
        tot = sum(1 for _, w in REQUESTS if w == nm)
        ok = sum(1 for _, w, g in [(r, w, g) for r, w, g in right] if w == nm)
        per[nm] = (ok, tot)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 5.2), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.25]})
    _plain(ax1)
    ys = np.arange(len(names))
    ax1.barh(ys, [per[nm][1] for nm in names], 0.62, color=LINK_PALE,
             label='requests written')
    ax1.barh(ys, [per[nm][0] for nm in names], 0.62, color=TEAL,
             label='matched by words alone')
    ax1.set_yticks(ys)
    ax1.set_yticklabels(names, fontsize=9.5, family='monospace')
    ax1.invert_yaxis()
    ax1.set_xlabel('requests', fontsize=10)
    ax1.set_xlim(0, 6.6)
    ax1.set_xticks(range(0, 6))
    ax1.set_title(f'{len(right)} of {n} requests need no model at all',
                  fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='lower right')
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.9, f'the {len(wrong)} the word list got wrong, and why',
             fontsize=11, weight='bold', color=INK, va='top')
    for i, (req, want, got) in enumerate(wrong[:9]):
        ax2.text(0.3, 9.0 - 0.92 * i, f'"{req}"', fontsize=9.5, color=GRIP, va='top')
        ax2.text(5.0, 9.0 - 0.92 * i, f'{want}  not  {got}', fontsize=9,
                 family='monospace', color=MUTED, va='top')
    ax2.text(0.1, 1.5, 'Every one of them is a different way of saying a command\n'
                       'that is already on the list, which is the one thing a\n'
                       'language model is reliably good at.',
             fontsize=10, color=INK, va='top')
    fig.suptitle('Write the word list first: it is the baseline the model has to beat',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'word-list-baseline.svg')


NOTES: list[str] = [
    'The scalpel is kept in drawer 8.', 'The spare grippers are in drawer 3.',
    'The calibration plate lives in drawer 1.', 'The hex keys are in drawer 2.',
    'The feeler gauges are in drawer 4.', 'The spare fuses are in drawer 5.',
    'The torque wrench is in drawer 6.', 'The cable ties are in drawer 7.',
    'The gripper pads are in drawer 9.', 'The camera lens cloths are in drawer 10.',
    'Cell 2 runs the inspection station.', 'Cell 1 runs the packing station.',
    'Cell 3 is out of service until the new controller arrives.',
    'The emergency stop for cell 1 is on the left post.',
    'The emergency stop for cell 2 is beside the door.',
    'The air supply valve is behind the cell 1 cabinet.',
    'The main breaker is in the corridor cupboard.',
    'The arm in cell 1 is a six joint arm with a parallel gripper.',
    'The arm in cell 2 has a suction cup rather than fingers.',
    'The tray feeder holds twenty four parts.',
    'A full tray weighs about three kilograms.',
    'The conveyor runs at one hundred and twenty millimetres a second.',
    'The inspection camera is mounted two hundred millimetres above the tray.',
    'The inspection light must be switched on before any photo is taken.',
    'Parts with a chipped rim go in the red bin.',
    'Parts with a scratched base go in the amber bin.',
    'Good parts go on the outfeed conveyor.',
    'The red bin is emptied every Friday afternoon.',
    'The gripper pads are replaced every two thousand cycles.',
    'The arm is greased every six months.',
    'The controller firmware was last updated in March.',
    'The cell log is written to the share called cellone.',
    'A cycle takes about four seconds when nothing goes wrong.',
    'The safety fence gate must be shut before the arm will move.',
    'The teach pendant is kept on the hook by the door.',
    'The pendant passcode is held by the shift supervisor.',
    'Only trained operators may jog the arm by hand.',
    'The arm must be sent home before the power is switched off.',
    'A dropped part counts as a failed cycle in the log.',
    'The log keeps the last ninety days of cycles.',
    'Spare suction cups are ordered from the maintenance office.',
    'The tray feeder jams if a part is loaded upside down.',
    'A jammed feeder is cleared with the arm stopped and the gate open.',
    'The barcode reader is on the outfeed side of the conveyor.',
    'The barcode must be read before a part is packed.',
    'Packing boxes are stacked beside the outfeed conveyor.',
    'The box label printer is on the bench behind cell 1.',
    'The printer takes forty by twenty millimetre labels.',
]

FACT_QUESTIONS: list[tuple[str, int]] = [
    ('which drawer holds the scalpel ?', 0),
    ('where are the spare grippers kept ?', 1),
    ('where is the calibration plate ?', 2),
    ('which drawer has the hex keys ?', 3),
    ('where would I find a torque wrench ?', 6),
    ('which drawer has the cable ties ?', 7),
    ('which cell does the inspection ?', 10),
    ('which cell is out of service ?', 12),
    ('where is the emergency stop for cell 2 ?', 14),
    ('where is the air supply valve ?', 15),
    ('does cell 2 have fingers or a suction cup ?', 18),
    ('how many parts does the tray feeder hold ?', 19),
    ('how fast does the conveyor run ?', 21),
    ('how high above the tray is the inspection camera ?', 22),
    ('what has to be on before a photo is taken ?', 23),
    ('which bin takes a part with a chipped rim ?', 24),
    ('which bin takes a scratched base ?', 25),
    ('when is the red bin emptied ?', 27),
    ('how often are the gripper pads replaced ?', 28),
    ('how long does one cycle take ?', 32),
    ('what must be shut before the arm will move ?', 33),
    ('who holds the pendant passcode ?', 35),
    ('how many days of cycles does the log keep ?', 39),
    ('what size labels does the printer take ?', 47),
]


def retriever_first() -> None:
    """5b: test the finding of the text before any model reads it."""
    qs = [q for q, _ in FACT_QUESTIONS]
    order = _tfidf_match(qs, NOTES)
    at1 = at3 = at5 = 0
    misses = []
    for (q, want), row in zip(FACT_QUESTIONS, order):
        rank = int(np.nonzero(row == want)[0][0]) + 1
        at1 += rank == 1
        at3 += rank <= 3
        at5 += rank <= 5
        if rank > 3:
            misses.append((q, rank, NOTES[int(row[0])]))
    n = len(FACT_QUESTIONS)
    print(f'[5b] finding the right note for {n} written questions among {len(NOTES)} '
          f'notes, by shared rare words and no model')
    print(f'      right note first {at1}/{n} ({at1 / n:.1%}), in the top three {at3}/{n} '
          f'({at3 / n:.1%}), in the top five {at5}/{n} ({at5 / n:.1%})')
    for q, rank, got in misses:
        print(f'      outside the top three: "{q}" came back {rank}th, '
              f'first was "{got}"')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.3]})
    _plain(ax1)
    vals = [at1, at3, at5]
    labs = ['first', 'in the\ntop three', 'in the\ntop five']
    ax1.bar(labs, vals, 0.55, color=[LINK, TEAL, SLIDE], alpha=0.9)
    for i, v in enumerate(vals):
        ax1.text(i, v + 0.3, f'{v} of {n}\n{v / n:.0%}', ha='center', fontsize=10,
                 weight='bold', color=[LINK, TEAL, SLIDE][i])
    ax1.set_ylim(0, n * 1.22)
    ax1.set_ylabel('questions whose note was found', fontsize=10)
    ax1.set_title('The retrieving step on its own,\nbefore any model reads anything',
                  fontsize=11, weight='bold')
    ax1.grid(axis='y', color=GRID, lw=0.7)
    rowq, want = FACT_QUESTIONS[0]
    scores_order = _tfidf_match([rowq], NOTES)[0]
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.8, f'"{rowq}"', fontsize=11, weight='bold', color=INK, va='top')
    ax2.text(0.1, 8.9, 'the five notes it brings back, in order', fontsize=10,
             color=MUTED, va='top')
    for i in range(5):
        ni = int(scores_order[i])
        col = SLIDE if ni == want else MUTED
        ax2.text(0.3, 8.1 - 1.0 * i, f'{i + 1}. {NOTES[ni]}', fontsize=9.5, color=col,
                 va='top')
    ax2.text(0.1, 2.6, 'If the right note is not in this list, no model can\n'
                       'answer from it, so this is the number to fix first,\n'
                       'and fixing it means editing notes rather than\n'
                       'training anything.',
             fontsize=10, color=INK, va='top')
    fig.suptitle('Retrieval is tested without a model, because a model cannot read a '
                 'note it was not given', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'retriever-first.svg')


LORA_RANKS: list[int] = [2, 4, 8, 16, 32, 64]
LORA_DIM: int = 4096


def adapter_and_pairs() -> None:
    """5c: what one fine-tuning example is, and what an adapter costs."""
    full = LORA_DIM * LORA_DIM
    counts = [2 * LORA_DIM * r for r in LORA_RANKS]
    n_cmd = len(COMMANDS)
    phrasings = 5
    pairs = n_cmd * phrasings
    print(f'[5c] a weight matrix of {LORA_DIM} by {LORA_DIM} holds {full:,} numbers')
    for r, c in zip(LORA_RANKS, counts):
        print(f'      a rank {r:2d} adapter adds 2 x {LORA_DIM} x {r} = {c:,} numbers, '
              f'{100.0 * c / full:.2f} per cent of the matrix')
    print(f'      {n_cmd} commands x {phrasings} ways of saying each = {pairs} written '
          f'pairs as a floor, and the {len(REQUESTS)} requests above average '
          f'{len(REQUESTS) / n_cmd:.1f} a command')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.15, 1.0]})
    _blank(ax1, (0, 10), (0, 10))
    ax1.text(0.1, 9.9, 'one fine-tuning example: a pair of written strings',
             fontsize=11, weight='bold', color=INK, va='top')
    pair = ['{', '  "prompt":  "operator: take it easy",', '  "answer":  "slower"', '}']
    for i, ln in enumerate(pair):
        ax1.text(0.3, 9.0 - 0.72 * i, ln, fontsize=10, family='monospace', color=TEAL,
                 va='top')
    ax1.text(0.1, 5.7, 'how many pairs the job needs', fontsize=11, weight='bold',
             color=INK, va='top')
    ax1.text(0.3, 4.9, f'{n_cmd} commands, and a person can say each of\n'
                       f'them about {phrasings} different ways, so {pairs} pairs\n'
                       f'is the floor and not the target. Every pair is\n'
                       f'a sentence somebody wrote, so the data is\n'
                       f'written rather than collected, and a day of\n'
                       f'writing gets you several hundred.',
             fontsize=10, color=INK, va='top')
    _plain(ax2)
    ax2.bar([str(r) for r in LORA_RANKS], counts, 0.55, color=PURPLE, alpha=0.9)
    for i, c in enumerate(counts):
        ax2.text(i, c * 1.12, f'{100.0 * c / full:.2f}%', ha='center', fontsize=9.5,
                 weight='bold', color=PURPLE)
    ax2.axhline(full, color=GRIP, ls='--', lw=1.5)
    ax2.text(5.45, full * 1.18, f'the whole matrix, {full:,}', fontsize=9.5, color=GRIP,
             ha='right')
    ax2.set_yscale('log')
    ax2.set_ylim(5e3, full * 6)
    ax2.set_xlabel('rank of the adapter', fontsize=10)
    ax2.set_ylabel('numbers trained (log scale)', fontsize=10)
    ax2.set_title(f'A rank 8 adapter trains {100.0 * counts[2] / full:.2f} per cent of '
                  'one matrix', fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('A fine-tune for this job is written sentences and a very small number '
                 'of new weights', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'adapter-and-pairs.svg')


TEST_N: list[int] = [10, 20, 40, 100, 200, 400]


def _wilson(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """The usual 95 per cent interval for a share, worked out Wilson's way."""
    ph = k / n
    d = 1.0 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return float(c - h), float(c + h)


def test_set_width() -> None:
    """5d: a short written test set cannot tell two models apart."""
    p_true = 0.80
    print(f'[5d] the 95 per cent interval round a score of {p_true:.0%}, Wilson\'s way')
    los, his = [], []
    for n in TEST_N:
        lo, hi = _wilson(p_true * n, n)
        los.append(lo); his.append(hi)
        print(f'      {n:4d} questions: {lo:.3f} to {hi:.3f}, a width of '
              f'{100 * (hi - lo):.1f} points')
    small = next(i for i, n in enumerate(TEST_N) if n == 20)
    big = next(i for i, n in enumerate(TEST_N) if n == 200)
    print(f'      at 20 questions the interval is {100 * (his[small] - los[small]):.0f} '
          f'points wide, at 200 it is {100 * (his[big] - los[big]):.0f}')

    fig, ax = plt.subplots(figsize=(10.0, 5.0), facecolor='white')
    _plain(ax)
    xs = np.arange(len(TEST_N))
    ax.errorbar(xs, [p_true] * len(TEST_N),
                yerr=[[p_true - lo for lo in los], [hi - p_true for hi in his]],
                fmt='o', color=TEAL, ecolor=LINK, elinewidth=3, capsize=9, ms=8)
    for i, n in enumerate(TEST_N):
        ax.text(i + 0.12, his[i] + 0.012,
                f'{100 * (his[i] - los[i]):.0f} points wide', fontsize=9.5, color=LINK)
    ax.axhline(p_true, color=MUTED, ls=':', lw=1.3)
    ax.axhline(0.70, color=GRIP, ls='--', lw=1.4)
    ax.text(len(TEST_N) - 1, 0.672, 'a model that is really 10 points worse',
            fontsize=9.5, color=GRIP, ha='right')
    ax.set_xticks(xs)
    ax.set_xticklabels([str(n) for n in TEST_N])
    ax.set_xlabel('written questions in the test set', fontsize=10)
    ax.set_ylabel('measured share answered right', fontsize=10)
    ax.set_ylim(0.45, 1.02)
    ax.set_title('A score of 80 per cent on 20 questions cannot be told apart from '
                 '70 per cent,\nand on 200 questions it can', fontsize=12,
                 weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.7)
    _save(fig, DOC, 'test-set-width.svg')


# ==========================================================================
# section 6: a vision-language job
# ==========================================================================

VQA_QUESTIONS: list[tuple[str, str, str]] = [
    ('Is anything lying on its side ?', 'yes, one glass', 'state'),
    ('How many glasses are on the table ?', 'three', 'counting'),
    ('Is the mug empty ?', 'cannot tell from here', 'state'),
    ('Which object is nearest the front edge ?', 'the bolt', 'relation'),
    ('Has somebody left a tool in the cell ?', 'yes, a bolt', 'state'),
    ('Is the tray clear ?', 'yes', 'state'),
    ('Is the lying glass touching another glass ?', 'yes', 'relation'),
    ('Which object would the arm have to move first ?', 'the lying glass', 'relation'),
]

TILE: int = 224
PATCH: int = 14
VQA_RES: list[int] = [224, 448, 672, 896]
Q_TOKENS: int = 20
A_TOKENS: int = 12
DECODE_SHARE: float = 0.1     # writing a token is far slower than reading the prompt
CYCLE_S: float = 4.0          # the arm's cycle, from the written notes


def _tiles_and_tokens(res: int) -> tuple[int, int]:
    """How many crops a picture of this width becomes, and how many tokens that is."""
    if res <= TILE:
        tiles = 1
    else:
        tiles = (res // TILE) ** 2 + 1          # the crops, plus one whole-picture copy
    return tiles, tiles * (TILE // PATCH) ** 2


def one_example_vqa() -> None:
    """6a: the example is a question and an answer, and it is a test set."""
    print('[6a] the written questions for one scene, by kind')
    kinds: dict[str, int] = {}
    for q, a, k in VQA_QUESTIONS:
        kinds[k] = kinds.get(k, 0) + 1
        print(f'      [{k:8s}] {q:46s} -> {a}')
    print('      ' + ', '.join(f'{k}: {v}' for k, v in kinds.items()))

    fig = plt.figure(figsize=(12.0, 5.0), facecolor='white')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.35], wspace=0.14)
    ax1 = fig.add_subplot(gs[0, 0])
    _show(ax1, SCENE_RGB)
    ax1.set_title('frame_0417.png, and nothing drawn on it', fontsize=11, weight='bold')
    ax2 = fig.add_subplot(gs[0, 1])
    _blank(ax2, (0, 10), (0, 10))
    ax2.text(0.1, 9.9, 'frame_0417_questions.jsonl', fontsize=10.5, weight='bold',
             family='monospace', color=INK, va='top')
    cols = {'state': TEAL, 'counting': LINK, 'relation': PURPLE}
    for i, (q, a, k) in enumerate(VQA_QUESTIONS):
        ax2.text(0.25, 9.1 - 1.03 * i, q, fontsize=9.5, color=INK, va='top')
        ax2.text(0.55, 8.73 - 1.03 * i, f'-> {a}', fontsize=9.5, color=cols[k], va='top')
        ax2.text(9.8, 9.1 - 1.03 * i, k, fontsize=8.5, color=cols[k], va='top',
                 ha='right')
    ax2.text(0.1, 0.8, 'No box, no mask and no number of millimetres: the label is '
                       'the sentence a\nperson would have said.',
             fontsize=10, color=MUTED, va='top')
    fig.suptitle('A vision-language example is a picture, a question and the answer you '
                 'wanted', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'one-example-vqa.svg')


def tokens_and_time() -> None:
    """6b: what one question costs in time while the arm waits."""
    print(f'[6b] a picture cut into crops of {TILE} pixels, each crop {TILE // PATCH} by '
          f'{TILE // PATCH} patches of {PATCH} pixels')
    rows = []
    for res in VQA_RES:
        tiles, toks = _tiles_and_tokens(res)
        prompt = toks + Q_TOKENS
        work = prompt + A_TOKENS / DECODE_SHARE
        rows.append((res, tiles, toks, prompt, work))
        print(f'      {res:4d} px: {tiles:2d} crops, {toks:5d} picture tokens, '
              f'{prompt:5d} tokens of prompt, {work:7.0f} tokens of work in all')
    rates = np.linspace(500.0, 20000.0, 400)
    print(f'      with the answer\'s {A_TOKENS} tokens written at a tenth of the '
          f'reading speed, the rate needed to answer inside one second is:')
    for res, _, _, _, work in rows:
        print(f'      {res:4d} px: {work:.0f} tokens a second')
    budget = CYCLE_S
    for res, _, _, _, work in rows:
        print(f'      {res:4d} px at 4000 tokens a second: {work / 4000.0:.2f} s, which '
              f'is {100 * work / 4000.0 / budget:.0f} per cent of a {budget:.0f} s cycle')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white')
    _plain(ax1)
    for (res, _, _, _, work), colour in zip(rows, (SLIDE, TEAL, LINK, PURPLE)):
        ax1.plot(rates, work / rates, color=colour, lw=2.2, label=f'{res} px picture')
    ax1.axhline(1.0, color=GRIP, ls='--', lw=1.4)
    ax1.text(6200, 1.11, 'one second', fontsize=9.5, color=GRIP)
    ax1.axhline(CYCLE_S, color=INK, ls=':', lw=1.4)
    ax1.text(6200, CYCLE_S + 0.11, f'a whole {CYCLE_S:.0f} s cycle', fontsize=9.5,
             color=INK)
    ax1.set_xlabel('tokens a second your machine really manages', fontsize=10)
    ax1.set_ylabel('time to answer one question (s)', fontsize=10)
    ax1.set_ylim(0, 5.2)
    ax1.set_title('One question, four picture sizes: the time is the\ntoken count '
                  'divided by your own speed', fontsize=11, weight='bold')
    ax1.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax1.grid(color=GRID, lw=0.7)
    _plain(ax2)
    xs = np.arange(len(rows))
    toks = [r[2] for r in rows]
    ax2.bar(xs, toks, 0.55, color=LINK, alpha=0.9)
    for i, (res, tiles, tk, _, _) in enumerate(rows):
        ax2.text(i, tk + 110, f'{tk}\n{tiles} crop' + ('s' if tiles > 1 else ''),
                 ha='center', fontsize=9.5, weight='bold', color=LINK)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([f'{r[0]} px' for r in rows], fontsize=10)
    ax2.set_ylim(0, max(toks) * 1.3)
    ax2.set_ylabel('tokens the picture alone becomes', fontsize=10)
    ax2.set_title('Doubling the picture\'s width roughly quadruples\nwhat the model has '
                  'to read', fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('Asking about a picture costs time, and the picture is nearly all of it',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'tokens-and-time.svg')


FREE_ANSWERS: list[tuple[str, bool]] = [
    ('yes', True), ('Yes.', True), ('yes, it is upright', True),
    ('It is upright.', True), ('upright', True), ('The bottle is upright.', True),
    ('Yes, the bottle is standing up.', True), ('standing', True),
    ('no', False), ('No.', False), ('no, it is on its side', False),
    ('It is lying down.', False), ('on its side', False),
    ('The bottle has fallen over.', False), ('not upright', False), ('lying', False),
]


def fixed_answer_list() -> None:
    """6c: score the answer against a short list, not against a string."""
    raw = [a for a, _ in FREE_ANSWERS]
    norm = [a.lower().strip().rstrip('.').strip() for a in raw]
    distinct_raw = len(set(raw))
    distinct_norm = len(set(norm))
    exact_yes = sum(1 for a, t in zip(norm, [t for _, t in FREE_ANSWERS])
                    if t and a == 'yes')
    exact_no = sum(1 for a, t in zip(norm, [t for _, t in FREE_ANSWERS])
                   if (not t) and a == 'no')
    exact = exact_yes + exact_no
    up_words = ('yes', 'upright', 'standing', 'stand')
    down_words = ('no', 'side', 'lying', 'fallen', 'down', 'not upright')
    mapped = 0
    for a, t in zip(norm, [t for _, t in FREE_ANSWERS]):
        said_down = any(w in a for w in down_words)
        said_up = any(w in a for w in up_words) and not said_down
        got = True if said_up else (False if said_down else None)
        mapped += int(got is t)
    n = len(FREE_ANSWERS)
    print(f'[6c] {n} answers to the one question "is the bottle upright ?", '
          f'every one of them correct')
    print(f'      {distinct_raw} different strings, {distinct_norm} after lower-casing '
          f'and dropping the full stop')
    print(f'      scored by matching the string "yes" or "no" exactly: {exact} of {n} '
          f'({exact / n:.1%}) counted as right')
    print(f'      scored by mapping each answer onto the two allowed replies: '
          f'{mapped} of {n} ({mapped / n:.1%})')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.35, 1.0]})
    _blank(ax1, (0, 10), (0, 10))
    ax1.text(0.1, 9.9, 'sixteen answers to one question, every one of them correct',
             fontsize=11, weight='bold', color=INK, va='top')
    for i, (a, t) in enumerate(FREE_ANSWERS):
        col = SLIDE if t else WRIST
        row, col_i = i % 8, i // 8
        ax1.text(0.3 + 5.0 * col_i, 8.9 - 1.03 * row, f'"{a}"', fontsize=9.5, color=col,
                 va='top')
    ax1.text(0.1, 0.5, f'{distinct_raw} different strings; '
                       f'{distinct_norm} once the capitals and full stops go.',
             fontsize=10, color=MUTED, va='top')
    _plain(ax2)
    ax2.bar(['matching the\nstring exactly', 'mapping onto\ntwo allowed replies'],
            [exact / n, mapped / n], 0.5, color=[GRIP, SLIDE], alpha=0.9)
    for i, v in enumerate([exact / n, mapped / n]):
        ax2.text(i, v + 0.02, f'{v:.0%}', ha='center', fontsize=13, weight='bold',
                 color=[GRIP, SLIDE][i])
    ax2.set_ylim(0, 1.12)
    ax2.set_ylabel('share the scoring program counted as right', fontsize=10)
    ax2.set_title('The same sixteen correct answers,\nscored two ways',
                  fontsize=11, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.7)
    fig.suptitle('The commonest mistake is letting the model answer in free text and '
                 'then scoring the text', fontsize=12.5, weight='bold', y=1.03)
    _save(fig, DOC, 'fixed-answer-list.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    classifier_example_files()
    examples_per_class_curve()
    covering_the_conditions()
    one_name_is_not_a_place()
    detector_label_file()
    boxes_and_hours()
    rare_class_split()
    average_precision()
    polygon_clicks()
    prompt_or_train()
    where_the_overlap_goes()
    do_you_need_pixels()
    calibrate_before_training()
    where_depth_labels_come_from()
    cue_ambiguity_floor()
    depth_error_budget()
    word_list_baseline()
    retriever_first()
    adapter_and_pairs()
    test_set_width()
    one_example_vqa()
    tokens_and_time()
    fixed_answer_list()
    print(f'wrote the diagrams under {IMAGES / DOC}')


if __name__ == '__main__':
    main()
