"""Generate the diagrams for the first two pages of docs/06_neural-networks/09_models-that-see/.

    01_vision-backbones.md            -> images/models-that-see/vision-backbones/
    02_detection-and-segmentation.md  -> images/models-that-see/detection-and-segmentation/

Run with:  python3 models_that_see_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script prints
them so the documents can quote the same values.

What is real arithmetic here: the parameter counts and the multiply-add counts of
a vision transformer and of a 50-layer residual convolutional network, worked out
from the layer shapes; the patch arithmetic at 224 by 224 pixels; the
two-dimensional sine-and-cosine position vectors; the pinhole-camera arithmetic
for how many pixels wide a thing looks at a distance; the intersection over union
of boxes; non-maximum suppression; the precision and recall curve; the one-to-one
matching of query slots to true objects; and the mask arithmetic, including the
loss of accuracy when a mask is made at a low resolution and stretched back up.
The small convolutional network and the small fully connected network in
`tiny_nets` are really trained here, in NumPy, with Adam.

What is simulated: the camera scene itself is drawn with ellipses and rectangles
rather than photographed, the pictures the two small networks are trained on are
drawn shapes, the patch-embedding weights used to show the shapes of the numbers
are seeded random numbers because this script trains no vision transformer, and
the detector outputs used for the suppression, precision-recall and matching
pictures are made by jittering the true boxes with a seeded generator. Every such
number comes from numpy.random.default_rng with the seed written next to it.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402
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

BACK_DOC: str = 'vision-backbones'
SEG_DOC: str = 'detection-and-segmentation'

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


# --------------------------------------------------------------------------
# the simulated camera scene, used by both pages
# --------------------------------------------------------------------------

H: int = 480
W: int = 640


def _grid_yx() -> tuple[Arr, Arr]:
    yy, xx = np.meshgrid(np.arange(H, dtype=float), np.arange(W, dtype=float),
                         indexing='ij')
    return yy, xx


def _ellipse(yy: Arr, xx: Arr, cx: float, cy: float, rx: float, ry: float) -> Arr:
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0


def _rect(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)


def _glass(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    """A drinking glass: a body that tapers slightly, with an elliptical rim."""
    cx = (x1 + x2) / 2.0
    half_top = (x2 - x1) / 2.0
    half_bot = half_top * 0.78
    t = np.clip((yy - y1) / (y2 - y1), 0.0, 1.0)
    half = half_top + (half_bot - half_top) * t
    body = (np.abs(xx - cx) <= half) & (yy >= y1) & (yy <= y2)
    rim = _ellipse(yy, xx, cx, y1, half_top, 7.0)
    foot = _ellipse(yy, xx, cx, y2, half_bot, 5.0)
    return body | rim | foot


def _mug(yy: Arr, xx: Arr, x1: float, y1: float, x2: float, y2: float) -> Arr:
    body = _rect(yy, xx, x1, y1, x2, y2) | _ellipse(yy, xx, (x1 + x2) / 2, y1,
                                                    (x2 - x1) / 2, 8.0)
    cy = (y1 + y2) / 2.0
    outer = _ellipse(yy, xx, x2, cy, 26.0, 26.0)
    inner = _ellipse(yy, xx, x2, cy, 14.0, 14.0)
    handle = outer & ~inner & (xx >= x2)
    return body | handle


def scene() -> tuple[Arr, list[dict]]:
    """Draw the simulated table scene and return the picture and the objects.

    The picture is a float array of shape (480, 640, 3) with values from 0 to 1.
    Each object carries its own mask, its class name and the box of its visible
    pixels, worked out from that mask.
    """
    yy, xx = _grid_yx()
    rgb = np.zeros((H, W, 3))
    # wall above the table, then the table surface
    wall = 0.88 - 0.06 * (yy / H)
    table = 0.80 - 0.10 * (yy / H)
    horizon = 170.0
    base = np.where(yy < horizon, wall, table)
    rgb[..., 0] = base
    rgb[..., 1] = base
    rgb[..., 2] = base
    rgb[yy < horizon] *= np.array([0.95, 0.97, 1.00])
    rgb[yy >= horizon] *= np.array([1.00, 0.95, 0.86])
    # a few table markings so the background is not flat
    for x0 in (60, 300, 560):
        seam = _rect(yy, xx, x0, horizon + 6, x0 + 3, H - 1)
        rgb[seam] *= 0.96

    specs = [
        ('glass_back', 'glass', _glass(yy, xx, 170, 196, 220, 320), (0.62, 0.74, 0.80)),
        ('glass_front', 'glass', _glass(yy, xx, 150, 210, 200, 330), (0.70, 0.82, 0.88)),
        ('glass_right', 'glass', _glass(yy, xx, 240, 214, 290, 334), (0.66, 0.78, 0.85)),
        ('box', 'box', _rect(yy, xx, 520, 184, 616, 258), (0.78, 0.63, 0.42)),
        ('mug', 'mug', _mug(yy, xx, 370, 258, 446, 348), (0.80, 0.36, 0.30)),
        ('bolt', 'bolt', _ellipse(yy, xx, 344, 186, 9.0, 5.0), (0.34, 0.34, 0.36)),
    ]
    objects: list[dict] = []
    painted = np.zeros((H, W), dtype=bool)
    # painted later means painted in front, so earlier objects lose hidden pixels
    for name, cls, mask, colour in specs:
        rgb[mask] = colour
        objects.append({'name': name, 'cls': cls, 'raw': mask})
    for i, ob in enumerate(objects):
        later = np.zeros((H, W), dtype=bool)
        for other in objects[i + 1:]:
            later |= other['raw']
        vis = ob['raw'] & ~later
        ob['mask'] = vis
        ys, xs = np.nonzero(vis)
        ob['box'] = (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))
        ob['area'] = int(vis.sum())
    del painted
    # a little shading so the shapes are not flat, and faint noise
    shade = 1.0 - 0.00035 * (yy - 150.0)
    rgb *= np.clip(shade, 0.85, 1.05)[..., None]
    rng = np.random.default_rng(11)
    rgb += rng.normal(0.0, 0.006, rgb.shape)
    return np.clip(rgb, 0.0, 1.0), objects


SCENE: tuple[Arr, list[dict]] | None = None


def _scene() -> tuple[Arr, list[dict]]:
    global SCENE
    if SCENE is None:
        SCENE = scene()
    return SCENE


def crop224() -> Arr:
    """A 224 by 224 pixel crop of the scene, by nearest-pixel resizing of 336 by 336."""
    rgb, _ = _scene()
    side = 360
    y0, x0 = 120, 120
    patch = rgb[y0:y0 + side, x0:x0 + side]
    idx = (np.arange(224) * side / 224.0).astype(int)
    return patch[np.ix_(idx, idx)]


# --------------------------------------------------------------------------
# the cost of a vision transformer and of a convolutional backbone
# --------------------------------------------------------------------------

def vit_counts(img: int = 224, patch: int = 16, dim: int = 768, depth: int = 12,
               mlp: int = 3072, classes: int = 1000) -> dict[str, float]:
    """Parameters and multiply-adds of a plain vision transformer, from its shapes."""
    side = img // patch
    n_patch = side * side
    n_tok = n_patch + 1                       # the patches plus the class token
    pix = patch * patch * 3
    p_embed = pix * dim + dim
    p_pos = n_tok * dim
    p_cls = dim
    p_qkv = dim * 3 * dim + 3 * dim
    p_proj = dim * dim + dim
    p_mlp = dim * mlp + mlp + mlp * dim + dim
    p_norm = 4 * dim
    p_block = p_qkv + p_proj + p_mlp + p_norm
    p_back = p_embed + p_pos + p_cls + depth * p_block + 2 * dim
    p_head = dim * classes + classes
    m_embed = n_patch * dim * pix
    m_qkv = n_tok * dim * 3 * dim
    m_scores = n_tok * n_tok * dim
    m_mix = n_tok * n_tok * dim
    m_proj = n_tok * dim * dim
    m_mlp = 2 * n_tok * dim * mlp
    m_block = m_qkv + m_scores + m_mix + m_proj + m_mlp
    return {'side': side, 'n_patch': n_patch, 'n_tok': n_tok, 'pix': pix,
            'p_embed': p_embed, 'p_pos': p_pos, 'p_block': p_block,
            'p_qkv': p_qkv, 'p_proj': p_proj, 'p_mlp': p_mlp, 'p_norm': p_norm,
            'p_back': p_back, 'p_head': p_head,
            'm_embed': m_embed, 'm_block': m_block, 'm_qkv': m_qkv,
            'm_scores': m_scores, 'm_mix': m_mix, 'm_proj': m_proj, 'm_mlp': m_mlp,
            'm_quad': depth * (m_scores + m_mix),
            'm_lin': m_embed + depth * (m_qkv + m_proj + m_mlp),
            'm_total': m_embed + depth * m_block}


def resnet50_layers(img: int = 224) -> list[tuple[str, int, int, int, int]]:
    """The convolutions of a 50-layer residual network as (stage, k, cin, cout, out_side)."""
    layers: list[tuple[str, int, int, int, int]] = []
    s = img // 2
    layers.append(('stem', 7, 3, 64, s))
    s = s // 2                                 # the pooling layer halves it again
    cin = 64
    plan = [(64, 3, 1, s), (128, 4, 2, s // 2), (256, 6, 2, s // 4), (512, 3, 2, s // 8)]
    for stage, (width, blocks, _stride, out_s) in enumerate(plan, start=1):
        for b in range(blocks):
            first = b == 0
            mid_s = out_s
            layers.append((f'stage{stage}', 1, cin, width, out_s if not first else
                           (s if stage == 1 else out_s * 2)))
            layers.append((f'stage{stage}', 3, width, width, mid_s))
            layers.append((f'stage{stage}', 1, width, width * 4, mid_s))
            if first:
                layers.append((f'stage{stage}', 1, cin, width * 4, mid_s))
            cin = width * 4
    return layers


def resnet_counts(img: int = 224, classes: int = 1000) -> dict[str, float]:
    """Parameters and multiply-adds of the 50-layer residual network, from its shapes."""
    params = 9472 + 64 * 2                     # the 7x7 stem and its normalisation
    macs = 0.0
    by_stage: dict[str, float] = {}
    params = 0.0
    for stage, k, cin, cout, out_s in resnet50_layers(img):
        params += k * k * cin * cout + 2 * cout
        this = k * k * cin * cout * out_s * out_s
        macs += this
        by_stage[stage] = by_stage.get(stage, 0.0) + this
    params += 2048 * classes + classes
    macs += 2048 * classes
    return {'p_back': params - (2048 * classes + classes), 'p_head': 2048 * classes + classes,
            'm_total': macs, 'by_stage': by_stage}


# --------------------------------------------------------------------------
# 01_vision-backbones, section 1: the backbone and its heads
# --------------------------------------------------------------------------

HEADS: dict[str, dict] = {
    'classify': {'p': 768 * 1000 + 1000, 'out': '1,000 scores, one per class name'},
    'detect': {'p': 2 * (768 * 768 + 768) + (768 * 4 + 4) + (768 * 92 + 92) + 100 * 768,
               'out': '100 boxes, each 4 numbers plus 92 scores'},
    'segment': {'p': 9 * 768 * 256 + 256 + 2 * (9 * 256 * 256 + 256) + (256 + 1),
                'out': 'one number per pixel of a 28 by 28 grid'},
}


def backbone_and_heads() -> None:
    v = vit_counts()
    print(f"[backbone] vision transformer backbone {v['p_back']:,.0f} parameters, "
          f"one block {v['p_block']:,.0f}, patch embedding {v['p_embed']:,.0f}")
    for name, h in HEADS.items():
        print(f"[backbone] {name} head {h['p']:,.0f} parameters "
              f"({100 * h['p'] / v['p_back']:.2f}% of the backbone)")

    fig = plt.figure(figsize=(12.0, 5.4), facecolor='white')
    axp = fig.add_axes((0.02, 0.26, 0.21, 0.52))
    _show(axp, crop224(), 'the picture, 224 x 224')
    ax = fig.add_axes((0.27, 0.05, 0.71, 0.9))
    _blank(ax, (0, 10), (1.9, 9.8))
    _box(ax, 0.1, 2.2, 2.6, 5.6, LINK, '', alpha=0.10)
    ax.text(1.4, 7.5, 'the backbone', ha='center', fontsize=11.5, weight='bold',
            color=LINK)
    ax.text(1.4, 7.05, f"{v['p_back']:,.0f} parameters", ha='center', fontsize=9.5,
            color=INK)
    for i in range(6):
        _box(ax, 0.45, 2.55 + i * 0.72, 1.9, 0.55, LINK,
             'block 1' if i == 0 else ('block 12' if i == 5 else ''), fs=8.5)
    ax.text(1.4, 2.55 + 2.0 * 0.72 + 0.27, '...', ha='center', va='center',
            fontsize=13, color=INK)
    ax.text(1.4, 2.0, 'patch embedding', ha='center', fontsize=8.5, color=INK)
    _arrow(ax, (-0.35, 5.0), (0.1, 5.0), MUTED)

    rows = [('classify', SLIDE, 7.6), ('detect', LINK, 5.0), ('segment', PURPLE, 2.4)]
    for name, colour, y in rows:
        h = HEADS[name]
        _arrow(ax, (2.75, 5.0), (4.3, y + 0.6), MUTED)
        _box(ax, 4.35, y, 1.9, 1.2, colour, f'{name}\nhead', fs=10, alpha=0.3)
        ax.text(6.45, y + 0.82, h['out'], fontsize=9.5, color=INK, va='center')
        ax.text(6.45, y + 0.36, f"{h['p']:,.0f} parameters "
                                f"({100 * h['p'] / v['p_back']:.1f}% of the backbone)",
                fontsize=9, color=colour, va='center')
    ax.text(0.0, 9.3, 'One backbone, three small heads: the shared part does almost '
                      'all of the work',
            fontsize=13, weight='bold', color=INK)
    ax.text(0.0, 8.8, 'parameter counts worked out from the layer shapes of a '
                      'vision transformer with 12 blocks and 768 numbers per token',
            fontsize=9.5, color=MUTED)
    _save(fig, BACK_DOC, 'backbone-and-heads.svg')


def parameter_split() -> None:
    v = vit_counts()
    parts = [('patch embedding', v['p_embed'], TEAL),
             ('position vectors', v['p_pos'] + 768, MUTED),
             ('attention, 12 blocks', 12 * (v['p_qkv'] + v['p_proj']), LINK),
             ('feed-forward, 12 blocks', 12 * v['p_mlp'], PURPLE),
             ('normalisation, 12 blocks', 12 * v['p_norm'] + 1536, JOINT)]
    total = sum(p for _, p, _ in parts)
    print(f"[split] backbone total {total:,.0f} (check {v['p_back']:,.0f})")
    for name, p, _ in parts:
        print(f'[split] {name:26s} {p:12,.0f}  {100 * p / total:5.1f}%')

    fig, ax = plt.subplots(figsize=(10.6, 4.6), facecolor='white')
    _plain(ax)
    left = 0.0
    for name, p, colour in parts:
        ax.barh([0], [p / 1e6], left=left / 1e6, color=colour, alpha=0.85,
                edgecolor='white', height=0.5)
        left += p
    places = [(0.85, 'left'), (-0.85, 'left'), (0.40, 'center'), (-0.40, 'center'),
              (0.85, 'right')]
    left = 0.0
    for (name, p, colour), (y, ha) in zip(parts, places):
        mid = (left + p / 2) / 1e6
        tx = 0.0 if ha == 'left' else (total / 1e6 if ha == 'right' else mid)
        ax.annotate(f'{name}\n{p / 1e6:.2f} M ({100 * p / total:.1f}%)',
                    xy=(mid, 0.26 if y > 0 else -0.26), xytext=(tx, y),
                    ha=ha, va='bottom' if y > 0 else 'top', fontsize=9.5,
                    color=colour, weight='bold',
                    arrowprops=dict(arrowstyle='-', color=colour, lw=0.9))
        left += p
    ax.set_xlim(0, total / 1e6)
    ax.set_ylim(-1.5, 1.5)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xlabel('millions of parameters', fontsize=10)
    ax.set_title(f'Where the {total / 1e6:.1f} million parameters of the backbone sit',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'parameter-split.svg')


def shared_vs_separate() -> None:
    v = vit_counts()
    head_sum = sum(h['p'] for h in HEADS.values())
    shared = v['p_back'] + head_sum
    separate = 3 * v['p_back'] + head_sum
    print(f'[shared] three separate models {separate:,.0f} parameters, '
          f'one shared backbone {shared:,.0f}, saving {separate - shared:,.0f} '
          f'({100 * (separate - shared) / separate:.0f}%)')
    print(f'[shared] trainable when the backbone is frozen: {head_sum:,.0f} '
          f'({100 * head_sum / shared:.2f}% of the model)')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = ['three separate\nmodels', 'one shared backbone,\nthree heads']
    backs = np.array([3 * v['p_back'], v['p_back']]) / 1e6
    heads = np.array([head_sum, head_sum]) / 1e6
    ax.bar(names, backs, color=LINK, alpha=0.85, label='backbone', width=0.55)
    ax.bar(names, heads, bottom=backs, color=GRIP, alpha=0.9, label='heads', width=0.55)
    for i, (b, h) in enumerate(zip(backs, heads)):
        ax.text(i, b + h + 4, f'{b + h:.1f} M', ha='center', fontsize=11,
                weight='bold', color=INK)
        ax.text(i, b / 2, f'{b:.1f} M', ha='center', fontsize=9.5, color='white',
                weight='bold')
    ax.set_ylim(0, (backs + heads).max() * 1.18)
    ax.set_ylabel('millions of parameters', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('Doing three jobs: the cost of not sharing', fontsize=12,
                 weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    ax.bar(['fine-tune\neverything', 'freeze the backbone,\ntrain the heads'],
           [shared / 1e6, head_sum / 1e6], color=[WRIST, SLIDE], alpha=0.85, width=0.55)
    ax.set_yscale('log')
    for i, val in enumerate([shared, head_sum]):
        ax.text(i, val / 1e6 * 1.25, f'{val / 1e6:.2f} M', ha='center', fontsize=11,
                weight='bold', color=INK)
    ax.set_ylim(1, shared / 1e6 * 4)
    ax.set_ylabel('millions of parameters that change (log scale)', fontsize=10)
    ax.set_title(f'Training the heads alone changes '
                 f'{100 * head_sum / shared:.1f}% of the numbers',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'shared-vs-separate.svg')


def work_per_second() -> None:
    """How much arithmetic a live camera asks for, with and without a shared backbone."""
    v = vit_counts()
    rates = [10, 30]
    one = [v['m_total'] * r for r in rates]
    three = [3 * v['m_total'] * r for r in rates]
    for r, a, b in zip(rates, one, three):
        print(f'[rate] at {r} pictures a second: one backbone {a / 1e12:.2f} '
              f'tera multiply-adds a second, three backbones {b / 1e12:.2f}')

    fig, ax = plt.subplots(figsize=(8.6, 4.6), facecolor='white')
    _plain(ax)
    x = np.arange(len(rates))
    ax.bar(x - 0.18, np.array(one) / 1e12, width=0.34, color=SLIDE, alpha=0.85,
           label='one shared backbone')
    ax.bar(x + 0.18, np.array(three) / 1e12, width=0.34, color=GRIP, alpha=0.85,
           label='a separate backbone for each of the three jobs')
    for i, (a, b) in enumerate(zip(one, three)):
        ax.text(i - 0.18, a / 1e12 + 0.03, f'{a / 1e12:.2f}', ha='center', fontsize=10,
                color=INK, weight='bold')
        ax.text(i + 0.18, b / 1e12 + 0.03, f'{b / 1e12:.2f}', ha='center', fontsize=10,
                color=INK, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{r} pictures a second' for r in rates], fontsize=10)
    ax.set_ylabel('tera multiply-adds every second', fontsize=10)
    ax.set_ylim(0, max(three) / 1e12 * 1.2)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('The arithmetic a live camera asks for, at 224 by 224 pixels',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'work-per-second.svg')


# --------------------------------------------------------------------------
# 01_vision-backbones, section 2: the vision transformer, patch by patch
# --------------------------------------------------------------------------

PATCH: int = 16
SIDE: int = 14
DIM: int = 768


def _patches(img: Arr, patch: int = PATCH) -> Arr:
    """Cut a picture into patches and flatten each one: (n_patch, patch*patch*3)."""
    side = img.shape[0] // patch
    out = np.zeros((side * side, patch * patch * 3))
    for r in range(side):
        for c in range(side):
            out[r * side + c] = img[r * patch:(r + 1) * patch,
                                    c * patch:(c + 1) * patch].reshape(-1)
    return out


def _proj_weights() -> tuple[Arr, Arr]:
    """Seeded stand-in weights for the patch embedding, since nothing is trained here."""
    rng = np.random.default_rng(5)
    w = rng.normal(0.0, 1.0 / np.sqrt(PATCH * PATCH * 3), (DIM, PATCH * PATCH * 3))
    b = rng.normal(0.0, 0.02, DIM)
    return w, b


def _pos_vectors(side: int = SIDE, dim: int = DIM) -> Arr:
    """Two-dimensional sine-and-cosine position vectors, (side*side, dim)."""
    half = dim // 2
    k = np.arange(half // 2)
    omega = 1.0 / (10000.0 ** (2.0 * k / half))
    out = np.zeros((side * side, dim))
    for r in range(side):
        for c in range(side):
            i = r * side + c
            out[i, :half] = np.concatenate([np.sin(r * omega), np.cos(r * omega)])
            out[i, half:] = np.concatenate([np.sin(c * omega), np.cos(c * omega)])
    return out


def patch_grid() -> None:
    img = crop224()
    v = vit_counts()
    print(f"[patches] 224 / 16 = {v['side']:.0f} patches across, "
          f"{v['side']:.0f} x {v['side']:.0f} = {v['n_patch']:.0f} patches, "
          f"each {PATCH} x {PATCH} x 3 = {v['pix']:.0f} numbers")
    print(f"[patches] the picture holds 3 x 224 x 224 = {3 * 224 * 224:,} numbers, "
          f"and the patches hold {int(v['n_patch'] * v['pix']):,}")

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.8), facecolor='white')
    ax = axes[0]
    _show(ax, img, 'the picture, 224 rows of 224 pixels')
    for i in range(1, SIDE):
        ax.axhline(i * PATCH - 0.5, color=GRIP, lw=0.7, alpha=0.7)
        ax.axvline(i * PATCH - 0.5, color=GRIP, lw=0.7, alpha=0.7)
    ax.set_xlabel('each red square is one 16 by 16 patch', fontsize=9.5, color=INK)

    ax = axes[1]
    _show(ax, img * 0 + 1.0, 'the same picture counted as patches')
    for r in range(SIDE):
        for c in range(SIDE):
            n = r * SIDE + c
            ax.add_patch(Rectangle((c * PATCH - 0.5, r * PATCH - 0.5), PATCH, PATCH,
                                   facecolor=LINK_PALE, edgecolor=LINK, lw=0.6,
                                   alpha=0.55))
            if n < 3 or n in (SIDE * 6 + 3,) or n > 192:
                ax.text(c * PATCH + 7.5, r * PATCH + 7.5, str(n), fontsize=6.5,
                        ha='center', va='center', color=INK, weight='bold')
    ax.add_patch(Rectangle((3 * PATCH - 0.5, 6 * PATCH - 0.5), PATCH, PATCH,
                           fill=False, edgecolor=GRIP, lw=2.2))
    ax.set_xlabel(f'patches 0 to {SIDE * SIDE - 1}, in reading order; '
                  f'patch {SIDE * 6 + 3} is ringed in red', fontsize=9.5, color=INK)
    fig.suptitle('224 / 16 = 14 patches across, so one picture becomes 196 patches '
                 'of 16 x 16 x 3 = 768 numbers',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'patch-grid.svg')


def patch_to_vector() -> None:
    img = crop224()
    flat = _patches(img)
    w, b = _proj_weights()
    n = SIDE * 6 + 3
    x = flat[n]
    y = w @ x + b
    terms = w[0, :3] * x[:3]
    print(f'[embed] patch {n} holds {x.size} numbers, first six '
          f'{np.round(x[:6], 3).tolist()}')
    print(f'[embed] the first output number is '
          f'{terms[0]:.4f} + {terms[1]:.4f} + {terms[2]:.4f} + ... = {y[0]:.4f}')
    print(f'[embed] the embedded patch, first six: {np.round(y[:6], 3).tolist()}')
    print(f'[embed] in and out are both {x.size} and {y.size} numbers long')

    fig = plt.figure(figsize=(12.4, 5.0), facecolor='white')
    axp = fig.add_axes((0.03, 0.14, 0.2, 0.68))
    pix = img[6 * PATCH:7 * PATCH, 3 * PATCH:4 * PATCH]
    _show(axp, pix, f'patch {n}, 16 x 16 pixels')
    for i in range(1, PATCH):
        axp.axhline(i - 0.5, color=GRID, lw=0.4)
        axp.axvline(i - 0.5, color=GRID, lw=0.4)
    ax = fig.add_axes((0.27, 0.0, 0.71, 0.96))
    _blank(ax, (0, 10), (1.0, 9.8))
    ax.text(0.0, 9.3, 'One patch becomes one vector: flatten, then multiply by the '
                      'embedding weights', fontsize=12.5, weight='bold', color=INK)
    rows = [
        (7.6, 'the pixels, flattened in reading order, red then green then blue',
         ' '.join(f'{val:.2f}' for val in x[:9]) + '  ...  ' +
         f'({x.size} numbers in all)', TEAL),
        (5.6, 'the embedding weights of output number 0, one for each input number',
         ' '.join(f'{val:+.3f}' for val in w[0, :9]) + '  ...  ' +
         f'({w.shape[1]} weights)', MUTED),
        (3.6, 'multiply each pair and add them all up, then add the bias',
         f'{x[0]:.2f} x {w[0, 0]:+.3f} = {terms[0]:+.4f}, '
         f'{x[1]:.2f} x {w[0, 1]:+.3f} = {terms[1]:+.4f}, ... total {y[0]:+.4f}', JOINT),
        (1.6, 'the embedded patch: one vector of 768 numbers',
         ' '.join(f'{val:+.2f}' for val in y[:9]) + '  ...  ' +
         f'({y.size} numbers)', LINK),
    ]
    for y0, label, numbers, colour in rows:
        ax.text(0.0, y0 + 0.75, label, fontsize=10, color=colour, weight='bold')
        _box(ax, 0.0, y0 - 0.25, 9.9, 0.85, colour, numbers, fs=9.5, alpha=0.14)
        if y0 > 1.6:
            _arrow(ax, (4.9, y0 - 0.35), (4.9, y0 - 1.05), MUTED)
    _save(fig, BACK_DOC, 'patch-to-vector.svg')


def position_and_shuffle() -> None:
    img = crop224()
    pos = _pos_vectors()
    n = SIDE * 6 + 3
    unit = pos / np.linalg.norm(pos, axis=1, keepdims=True)
    sim = (unit @ unit[n]).reshape(SIDE, SIDE)
    rng = np.random.default_rng(7)
    order = rng.permutation(SIDE * SIDE)
    shuffled = np.zeros_like(img)
    for new, old in enumerate(order):
        r0, c0 = divmod(new, SIDE)
        r1, c1 = divmod(old, SIDE)
        shuffled[r0 * PATCH:(r0 + 1) * PATCH, c0 * PATCH:(c0 + 1) * PATCH] = \
            img[r1 * PATCH:(r1 + 1) * PATCH, c1 * PATCH:(c1 + 1) * PATCH]
    print(f'[pos] likeness of patch {n} to its right-hand neighbour '
          f'{sim[6, 4]:.3f}, to the patch two rows down {sim[8, 3]:.3f}, '
          f'to the far corner {sim[13, 13]:.3f}')
    print(f'[pos] the shuffled picture holds exactly the same 196 patches')

    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.9), facecolor='white')
    _show(axes[0], img, 'the picture')
    _show(axes[1], shuffled, 'the same 196 patches, shuffled')
    axes[1].set_xlabel('with no position information, the same bag of patches',
                       fontsize=9.5, color=INK)
    ax = axes[2]
    im = ax.imshow(sim, cmap='viridis', interpolation='nearest')
    ax.set_xticks(range(0, SIDE, 2))
    ax.set_yticks(range(0, SIDE, 2))
    ax.tick_params(labelsize=8)
    ax.add_patch(Rectangle((3 - 0.5, 6 - 0.5), 1, 1, fill=False, edgecolor=GRIP, lw=2))
    ax.set_title(f'likeness of every position vector\nto the one of patch {n}',
                 fontsize=10.5, weight='bold', color=INK)
    ax.set_xlabel('patch column', fontsize=9)
    ax.set_ylabel('patch row', fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle('Position has to be added, because the patches arrive as a bag',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'position-and-shuffle.svg')


def class_token() -> None:
    img_a = crop224()
    rgb, _ = _scene()
    side = 360
    patch_b = rgb[100:100 + side, 200:200 + side]
    idx = (np.arange(224) * side / 224.0).astype(int)
    img_b = patch_b[np.ix_(idx, idx)]
    w, b = _proj_weights()
    pos = _pos_vectors()
    rng = np.random.default_rng(9)
    cls_vec = rng.normal(0.0, 0.02, DIM)
    tok_a = np.vstack([cls_vec, (_patches(img_a) @ w.T + b) + pos])
    tok_b = np.vstack([cls_vec, (_patches(img_b) @ w.T + b) + pos])
    diff = np.abs(tok_a - tok_b).mean(axis=1)
    print(f'[cls] token 0 differs by {diff[0]:.4f} between two different pictures, '
          f'and the patch tokens differ by {diff[1:].mean():.3f} on average '
          f'(largest {diff[1:].max():.3f})')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), facecolor='white',
                             width_ratios=[1.0, 1.25])
    ax = axes[0]
    _blank(ax, (0, 10), (0, 10))
    ax.text(0.0, 9.2, 'The sequence that goes into the blocks', fontsize=12,
            weight='bold', color=INK)
    _box(ax, 0.2, 7.3, 1.5, 1.3, GRIP, 'class\ntoken', fs=9.5, alpha=0.3)
    for i in range(5):
        _box(ax, 2.0 + i * 1.55, 7.3, 1.45, 1.3, LINK,
             f'patch\n{i}' if i < 4 else '...', fs=9, alpha=0.25)
    ax.text(0.95, 6.85, 'token 0', ha='center', va='top', fontsize=9, color=GRIP)
    ax.text(5.5, 6.85, 'tokens 1 to 196', ha='center', va='top', fontsize=9, color=LINK)
    ax.text(0.0, 5.9, '197 tokens of 768 numbers go in, and 197 tokens of 768 numbers\n'
                      'come out of the last block', fontsize=10, color=INK, va='top')
    _box(ax, 0.2, 3.1, 1.5, 1.2, GRIP, 'token 0\nout', fs=9, alpha=0.3)
    _arrow(ax, (1.8, 3.7), (3.3, 3.7), MUTED)
    _box(ax, 3.4, 3.1, 2.6, 1.2, SLIDE, 'classify head', fs=9.5, alpha=0.3)
    _arrow(ax, (6.1, 3.7), (7.0, 3.7), MUTED)
    ax.text(7.1, 3.7, '1,000 scores', fontsize=9.5, va='center', color=INK)
    ax.text(0.0, 2.1, f'The classify head reads token 0 alone, which is\n'
                      f'768 / (197 x 768) = {100 / 197:.2f}% of what the backbone '
                      f'gives back.', fontsize=9.5, color=MUTED, va='top')

    ax = axes[1]
    _plain(ax)
    ax.bar(np.arange(197), diff, color=LINK, width=1.0)
    ax.plot([0], [0], marker='v', color=GRIP, markersize=11)
    ax.set_ylim(-0.012, diff[1:].max() * 1.42)
    ax.annotate(f'token 0 is the same learned vector for every\n'
                f'picture, so the difference here is exactly {diff[0]:.1f}',
                xy=(1, 0.004), xytext=(16, diff[1:].max() * 1.30), fontsize=9.5,
                color=GRIP, va='top',
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_xlabel('token number', fontsize=10)
    ax.set_ylabel('average size of the difference\nbetween two pictures', fontsize=10)
    ax.set_title('The class token is not read from the picture', fontsize=12,
                 weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'class-token.svg')


def shapes_ladder() -> None:
    v = vit_counts()
    steps = [
        ('the picture', '3 x 224 x 224', 3 * 224 * 224, TEAL),
        ('cut into patches', f"{v['n_patch']:.0f} x 16 x 16 x 3",
         int(v['n_patch'] * v['pix']), TEAL),
        ('each patch flattened', f"{v['n_patch']:.0f} x 768",
         int(v['n_patch'] * DIM), LINK),
        ('position vectors added', f"{v['n_patch']:.0f} x 768",
         int(v['n_patch'] * DIM), LINK),
        ('class token put in front', f"{v['n_tok']:.0f} x 768",
         int(v['n_tok'] * DIM), GRIP),
        ('after block 1 ... after block 12', f"{v['n_tok']:.0f} x 768",
         int(v['n_tok'] * DIM), PURPLE),
        ('token 0 taken out', '768', DIM, GRIP),
        ('the classify head', '1,000', 1000, SLIDE),
    ]
    for name, shape, count, _ in steps:
        print(f'[shapes] {name:34s} {shape:18s} {count:,} numbers')

    fig, ax = plt.subplots(figsize=(9.6, 7.4), facecolor='white')
    _blank(ax, (0, 10), (0, 10))
    top = 8.9
    gap = 1.02
    for i, (name, shape, count, colour) in enumerate(steps):
        y = top - i * gap
        _box(ax, 2.5, y - 0.62, 3.0, 0.72, colour, shape, fs=10.5, alpha=0.22,
             weight='bold')
        ax.text(2.35, y - 0.26, name, ha='right', va='center', fontsize=10, color=INK)
        ax.text(5.65, y - 0.26, f'{count:,} numbers', va='center', fontsize=9.5,
                color=colour)
        if i < len(steps) - 1:
            _arrow(ax, (4.0, y - 0.66), (4.0, y - gap + 0.14), MUTED)
    ax.text(0.0, 9.5, 'The shape of the numbers at every stage, for a 224 by 224 picture',
            fontsize=12.5, weight='bold', color=INK)
    ax.text(0.0, 0.35, 'The count does not change at the patch embedding, because '
                       '16 x 16 x 3 is 768 as well.', fontsize=10, color=MUTED)
    _save(fig, BACK_DOC, 'shapes-ladder.svg')


# --------------------------------------------------------------------------
# 01_vision-backbones, section 3: convolutional backbones
# --------------------------------------------------------------------------

def receptive_field() -> None:
    """How much of the picture one output number has seen, layer by layer."""
    depth = 14
    plain_rf, plain = [], 1
    for _ in range(depth):
        plain += 2
        plain_rf.append(plain)
    stage_rf, rf, jump = [], 1, 1
    strides = [2, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1]
    for st in strides:
        rf = rf + 2 * jump
        jump = jump * st
        stage_rf.append(rf)
    print(f'[field] 3 by 3 convolutions with no downsampling: after 1 layer '
          f'{plain_rf[0]} pixels, after 6 {plain_rf[5]}, after 14 {plain_rf[-1]}')
    print(f'[field] with the usual halving: after 1 layer {stage_rf[0]} pixels, '
          f'after 6 {stage_rf[5]}, after 14 {stage_rf[-1]}')
    print('[field] attention: 224 pixels after the first block')

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                             width_ratios=[1.05, 1.2])
    ax = axes[0]
    img = crop224()
    _show(ax, img, 'what one number in the middle has looked at')
    cx = cy = 112
    for rf, colour, name in ((plain_rf[0], SLIDE, f'1 conv layer: {plain_rf[0]} px'),
                             (plain_rf[5], LINK, f'6 conv layers: {plain_rf[5]} px'),
                             (stage_rf[5], PURPLE,
                              f'6 layers with halving: {stage_rf[5]} px'),
                             (224, GRIP, 'attention: all 224 px')):
        ax.add_patch(Rectangle((cx - rf / 2, cy - rf / 2), rf, rf, fill=False,
                               edgecolor=colour, lw=2.0, label=name))
    ax.legend(fontsize=8.5, frameon=True, loc='lower left', framealpha=0.9)

    ax = axes[1]
    _plain(ax)
    layers = np.arange(1, depth + 1)
    ax.plot(layers, plain_rf, marker='o', color=LINK, lw=2,
            label='3 by 3 convolutions, no downsampling')
    ax.plot(layers, stage_rf, marker='s', color=PURPLE, lw=2,
            label='3 by 3 convolutions, halving four times')
    ax.axhline(224, color=GRIP, lw=2, ls='--',
               label='attention: the whole picture from block 1')
    ax.set_yscale('log')
    ax.set_xlabel('layers passed', fontsize=10)
    ax.set_ylabel('pixels one output number has seen (log scale)', fontsize=10)
    ax.set_ylim(2, 700)
    ax.set_xticks(layers[::2])
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax.set_title('A convolution has to be stacked to see far; attention sees far at once',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'receptive-field.svg')


def _window(y0: int, x0: int, size: int = 224) -> Arr:
    rgb, _ = _scene()
    return rgb[y0:y0 + size, x0:x0 + size]


def _conv_feature(img: Arr, w: Arr) -> Arr:
    """Apply a small stack of fixed 3 by 3 filters, stride 1, and return the maps."""
    x = img.transpose(2, 0, 1)
    out = np.zeros((w.shape[0], x.shape[1] - 2, x.shape[2] - 2))
    for f in range(w.shape[0]):
        acc = np.zeros_like(out[0])
        for c in range(3):
            for i in range(3):
                for j in range(3):
                    acc += w[f, c, i, j] * x[c, i:i + acc.shape[0], j:j + acc.shape[1]]
        out[f] = np.maximum(acc, 0.0)
    return out


def shift_test() -> None:
    rng = np.random.default_rng(13)
    filters = rng.normal(0.0, 0.5, (8, 3, 3, 3))
    w, b = _proj_weights()
    y0, x0 = 150, 140
    base = _window(y0, x0)
    results: dict[int, tuple[float, float]] = {}
    for d in (5, 16):
        moved = _window(y0, x0 + d)
        fa, fb = _conv_feature(base, filters), _conv_feature(moved, filters)
        conv_gap = np.abs(fa[:, :, d:] - fb[:, :, :-d]).mean() / np.abs(fa).mean()
        ta = (_patches(base) @ w.T + b).reshape(SIDE, SIDE, DIM)
        tb = (_patches(moved) @ w.T + b).reshape(SIDE, SIDE, DIM)
        if d % PATCH == 0:
            k = d // PATCH
            tok_gap = np.abs(ta[:, k:] - tb[:, :SIDE - k]).mean() / np.abs(ta).mean()
        else:
            tok_gap = np.abs(ta[:, 1:] - tb[:, 1:]).mean() / np.abs(ta).mean()
        results[d] = (100 * conv_gap, 100 * tok_gap)
        print(f'[shift] moving the camera {d} pixels sideways changes the '
              f'convolution maps by {100 * conv_gap:.2f}% and the patch vectors by '
              f'{100 * tok_gap:.2f}%')

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.9), facecolor='white')
    for ax, d, name in ((axes[0], 0, 'the picture, with its patch grid'),
                        (axes[1], 5, 'the camera moved 5 pixels sideways')):
        _show(ax, _window(y0, x0 + d), name, fs=10)
        for i in range(1, SIDE):
            ax.axhline(i * PATCH - 0.5, color=GRIP, lw=0.6, alpha=0.8)
            ax.axvline(i * PATCH - 0.5, color=GRIP, lw=0.6, alpha=0.8)
        ax.add_patch(Rectangle((3 * PATCH - 0.5, 4 * PATCH - 0.5), PATCH, PATCH,
                               fill=False, edgecolor=JOINT, lw=2.4))
    axes[1].set_xlabel('every patch now holds different pixels', fontsize=9.5,
                       color=INK)
    ax = axes[2]
    _plain(ax)
    x = np.arange(2)
    conv = [results[5][0], results[16][0]]
    tok = [results[5][1], results[16][1]]
    ax.bar(x - 0.18, conv, width=0.34, color=SLIDE, alpha=0.9,
           label='convolution maps, shifted back')
    ax.bar(x + 0.18, tok, width=0.34, color=GRIP, alpha=0.9,
           label='patch vectors, shifted back')
    for i, (a, c) in enumerate(zip(conv, tok)):
        ax.text(i - 0.18, a + 0.6, f'{a:.2f}%', ha='center', fontsize=10, color=INK)
        ax.text(i + 0.18, c + 0.6, f'{c:.2f}%', ha='center', fontsize=10, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(['moved 5 pixels', 'moved 16 pixels\n(one whole patch)'],
                       fontsize=9.5)
    ax.set_ylabel('how much the numbers changed', fontsize=10)
    ax.set_ylim(0, max(tok) * 1.35)
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax.set_title('A small sideways move changes every patch vector',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'shift-test.svg')


# ---------------- two small networks, really trained here ----------------

SHAPES: list[str] = ['disc', 'square', 'triangle', 'ring', 'cross', 'bar', 'diamond']


def shape_pictures(n: int, classes: list[str], rng: np.random.Generator,
                   size: int = 24) -> tuple[Arr, NDArray[np.int64]]:
    """Simulated grey pictures of simple shapes, drawn at random places and sizes."""
    yy, xx = np.meshgrid(np.arange(size, dtype=float), np.arange(size, dtype=float),
                         indexing='ij')
    x = np.zeros((n, size, size))
    y = rng.integers(0, len(classes), n)
    for i in range(n):
        name = classes[y[i]]
        r = rng.uniform(4.0, 7.5)
        cy = rng.uniform(r + 1, size - r - 1)
        cx = rng.uniform(r + 1, size - r - 1)
        back = rng.uniform(0.15, 0.55)
        fore = back + rng.uniform(0.28, 0.48)
        dy, dx = yy - cy, xx - cx
        if name == 'disc':
            m = dy ** 2 + dx ** 2 <= r ** 2
        elif name == 'square':
            m = (np.abs(dy) <= r * 0.8) & (np.abs(dx) <= r * 0.8)
        elif name == 'triangle':
            m = (dy <= r * 0.8) & (dy >= -r * 0.8) & (np.abs(dx) <= (r * 0.9) *
                                                      (dy + r * 0.8) / (1.6 * r))
        elif name == 'ring':
            d2 = dy ** 2 + dx ** 2
            m = (d2 <= r ** 2) & (d2 >= (r * 0.55) ** 2)
        elif name == 'cross':
            m = ((np.abs(dy) <= r * 0.25) & (np.abs(dx) <= r)) | \
                ((np.abs(dx) <= r * 0.25) & (np.abs(dy) <= r))
        elif name == 'bar':
            m = (np.abs(dy) <= r * 0.28) & (np.abs(dx) <= r)
        else:
            m = np.abs(dy) + np.abs(dx) <= r
        pic = np.full((size, size), back)
        pic[m] = fore
        x[i] = np.clip(pic + rng.normal(0.0, 0.05, (size, size)), 0.0, 1.0)
    return x, y


def _im2col(x: Arr, k: int, s: int, p: int) -> tuple[Arr, int, int]:
    n, c, h, w = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)))
    ho = (h + 2 * p - k) // s + 1
    wo = (w + 2 * p - k) // s + 1
    cols = np.empty((n, k * k * c, ho * wo))
    t = 0
    for i in range(k):
        for j in range(k):
            cols[:, t * c:(t + 1) * c, :] = \
                xp[:, :, i:i + s * ho:s, j:j + s * wo:s].reshape(n, c, -1)
            t += 1
    return cols, ho, wo


def _col2im(cols: Arr, shape: tuple[int, int, int, int], k: int, s: int, p: int,
            ho: int, wo: int) -> Arr:
    n, c, h, w = shape
    xp = np.zeros((n, c, h + 2 * p, w + 2 * p))
    t = 0
    for i in range(k):
        for j in range(k):
            xp[:, :, i:i + s * ho:s, j:j + s * wo:s] += \
                cols[:, t * c:(t + 1) * c, :].reshape(n, c, ho, wo)
            t += 1
    return xp[:, :, p:p + h, p:p + w]


def _flat_w(w: Arr) -> Arr:
    return w.transpose(0, 2, 3, 1).reshape(w.shape[0], -1)


def _conv_forward(x: Arr, w: Arr, b: Arr, s: int, p: int) -> tuple[Arr, dict]:
    cols, ho, wo = _im2col(x, w.shape[2], s, p)
    out = np.matmul(_flat_w(w), cols) + b[None, :, None]
    return out.reshape(x.shape[0], w.shape[0], ho, wo), {
        'cols': cols, 'shape': x.shape, 'k': w.shape[2], 's': s, 'p': p,
        'ho': ho, 'wo': wo, 'w': w}


def _conv_backward(dout: Arr, cache: dict) -> tuple[Arr, Arr, Arr]:
    n = dout.shape[0]
    d = dout.reshape(n, dout.shape[1], -1)
    cols = cache['cols']
    o, c = d.shape[1], cols.shape[1]
    dw_flat = (d.transpose(1, 0, 2).reshape(o, -1) @
               cols.transpose(1, 0, 2).reshape(c, -1).T)
    db = d.sum(axis=(0, 2))
    dcols = np.matmul(_flat_w(cache['w']).T, d)
    dx = _col2im(dcols, cache['shape'], cache['k'], cache['s'], cache['p'],
                 cache['ho'], cache['wo'])
    w = cache['w']
    dw = dw_flat.reshape(w.shape[0], w.shape[2], w.shape[3], w.shape[1]).transpose(
        0, 3, 1, 2)
    return dx, dw, db


def _softmax_rows(z: Arr) -> Arr:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class Adam:
    def __init__(self, params: dict[str, Arr], lr: float = 0.01) -> None:
        self.p = params
        self.lr = lr
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(val) for k, val in params.items()}
        self.t = 0

    def step(self, g: dict[str, Arr]) -> None:
        self.t += 1
        for k in self.p:
            self.m[k] = 0.9 * self.m[k] + 0.1 * g[k]
            self.v[k] = 0.999 * self.v[k] + 0.001 * g[k] ** 2
            mh = self.m[k] / (1 - 0.9 ** self.t)
            vh = self.v[k] / (1 - 0.999 ** self.t)
            self.p[k] -= self.lr * mh / (np.sqrt(vh) + 1e-8)


def conv_net_forward(p: dict[str, Arr], x: Arr) -> tuple[Arr, dict]:
    a1, c1 = _conv_forward(x[:, None], p['w1'], p['b1'], 2, 2)
    r1 = np.maximum(a1, 0.0)
    a2, c2 = _conv_forward(r1, p['w2'], p['b2'], 2, 1)
    r2 = np.maximum(a2, 0.0)
    pooled = r2.mean(axis=(2, 3))
    logits = pooled @ p['w3'] + p['b3']
    return logits, {'c1': c1, 'a1': a1, 'r1': r1, 'c2': c2, 'a2': a2, 'r2': r2,
                    'pooled': pooled}


def conv_net_train(x: Arr, y: NDArray[np.int64], n_cls: int, seed: int,
                   steps: int = 900, batch: int = 64, lr: float = 0.02
                   ) -> dict[str, Arr]:
    rng = np.random.default_rng(seed)
    p = {'w1': rng.normal(0, 0.25, (8, 1, 5, 5)), 'b1': np.zeros(8),
         'w2': rng.normal(0, 0.18, (16, 8, 3, 3)), 'b2': np.zeros(16),
         'w3': rng.normal(0, 0.3, (16, n_cls)), 'b3': np.zeros(n_cls)}
    opt = Adam(p, lr=lr)
    for _ in range(steps):
        idx = rng.integers(0, len(x), min(batch, len(x)))
        xb, yb = x[idx], y[idx]
        logits, c = conv_net_forward(p, xb)
        probs = _softmax_rows(logits)
        dlog = probs.copy()
        dlog[np.arange(len(yb)), yb] -= 1.0
        dlog /= len(yb)
        g = {'w3': c['pooled'].T @ dlog, 'b3': dlog.sum(0)}
        dpool = dlog @ p['w3'].T
        dr2 = np.repeat(np.repeat(dpool[:, :, None, None], c['r2'].shape[2], 2),
                        c['r2'].shape[3], 3) / (c['r2'].shape[2] * c['r2'].shape[3])
        da2 = dr2 * (c['a2'] > 0)
        dr1, g['w2'], g['b2'] = _conv_backward(da2, c['c2'])
        da1 = dr1 * (c['a1'] > 0)
        _, g['w1'], g['b1'] = _conv_backward(da1, c['c1'])
        opt.step(g)
    return p


def fc_net_train(x: Arr, y: NDArray[np.int64], n_cls: int, seed: int,
                 steps: int = 900, batch: int = 64, hidden: int = 32
                 ) -> dict[str, Arr]:
    rng = np.random.default_rng(seed)
    d = x.shape[1] * x.shape[2]
    p = {'w1': rng.normal(0, 1.0 / np.sqrt(d), (d, hidden)), 'b1': np.zeros(hidden),
         'w2': rng.normal(0, 1.0 / np.sqrt(hidden), (hidden, n_cls)),
         'b2': np.zeros(n_cls)}
    opt = Adam(p, lr=0.01)
    flat = x.reshape(len(x), -1)
    for _ in range(steps):
        idx = rng.integers(0, len(x), min(batch, len(x)))
        xb, yb = flat[idx], y[idx]
        h = np.maximum(xb @ p['w1'] + p['b1'], 0.0)
        probs = _softmax_rows(h @ p['w2'] + p['b2'])
        dlog = probs.copy()
        dlog[np.arange(len(yb)), yb] -= 1.0
        dlog /= len(yb)
        g = {'w2': h.T @ dlog, 'b2': dlog.sum(0)}
        dh = (dlog @ p['w2'].T) * (h > 0)
        g['w1'] = xb.T @ dh
        g['b1'] = dh.sum(0)
        opt.step(g)
    return p


def _conv_accuracy(p: dict[str, Arr], x: Arr, y: NDArray[np.int64]) -> float:
    return float((conv_net_forward(p, x)[0].argmax(1) == y).mean())


def _fc_accuracy(p: dict[str, Arr], x: Arr, y: NDArray[np.int64]) -> float:
    h = np.maximum(x.reshape(len(x), -1) @ p['w1'] + p['b1'], 0.0)
    return float(((h @ p['w2'] + p['b2']).argmax(1) == y).mean())


DATA_CURVE: dict | None = None


def _data_curve() -> dict:
    global DATA_CURVE
    if DATA_CURVE is None:
        classes = SHAPES[:4]
        rng = np.random.default_rng(21)
        xte, yte = shape_pictures(800, classes, rng)
        sizes = [50, 100, 200, 400, 800, 1600, 3200]
        hidden = 128
        conv, fc = [], []
        for n in sizes:
            cs, fs = [], []
            for seed in (3, 7, 11):
                xtr, ytr = shape_pictures(n, classes,
                                          np.random.default_rng(100 + n + seed))
                cs.append(_conv_accuracy(conv_net_train(xtr, ytr, 4, seed=seed,
                                                        steps=1200, lr=0.005),
                                         xte, yte))
                fs.append(_fc_accuracy(fc_net_train(xtr, ytr, 4, seed=seed,
                                                    steps=2000, hidden=hidden),
                                       xte, yte))
            conv.append(float(np.mean(cs)))
            fc.append(float(np.mean(fs)))
            print(f'[data] {n} pictures: convolutional runs '
                  f'{[round(v, 3) for v in cs]}, fully connected runs '
                  f'{[round(v, 3) for v in fs]}')
        n_conv = 8 * 25 + 8 + 16 * 8 * 9 + 16 + 16 * 4 + 4
        n_fc = 576 * hidden + hidden + hidden * 4 + 4
        DATA_CURVE = {'sizes': sizes, 'conv': conv, 'fc': fc, 'n_conv': n_conv,
                      'n_fc': n_fc, 'classes': classes}
    return DATA_CURVE


def data_size_curve() -> None:
    d = _data_curve()
    print(f"[data] the small convolutional network has {d['n_conv']:,} parameters, "
          f"the fully connected one {d['n_fc']:,}")
    for n, c, f in zip(d['sizes'], d['conv'], d['fc']):
        print(f'[data] {n:5d} training pictures: convolutional {c:.3f}, '
              f'fully connected {f:.3f} (the average of three runs)')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), facecolor='white',
                             width_ratios=[1.0, 1.3])
    ax = axes[0]
    rng = np.random.default_rng(4)
    xs, ys = shape_pictures(12, d['classes'], rng)
    tile = np.ones((2 * 26 + 2, 6 * 26 + 2))
    for i in range(12):
        r, c = divmod(i, 6)
        tile[r * 26 + 2:r * 26 + 26, c * 26 + 2:c * 26 + 26] = xs[i]
    ax.imshow(tile, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('the simulated training pictures, 24 by 24 pixels',
                 fontsize=10.5, weight='bold', color=INK)
    ax.set_xlabel('four shapes, drawn at random places, sizes and brightnesses',
                  fontsize=9)

    ax = axes[1]
    _plain(ax)
    ax.plot(d['sizes'], d['conv'], marker='o', color=LINK, lw=2,
            label=f"convolutional network ({d['n_conv']:,} parameters)")
    ax.plot(d['sizes'], d['fc'], marker='s', color=WRIST, lw=2,
            label=f"fully connected network ({d['n_fc']:,} parameters)")
    ax.set_xscale('log')
    ax.set_xticks(d['sizes'])
    ax.set_xticklabels([str(s) for s in d['sizes']])
    ax.set_ylim(0.2, 1.02)
    ax.axhline(0.25, color=MUTED, ls=':', lw=1.2)
    ax.text(d['sizes'][0], 0.26, 'guessing', fontsize=9, color=MUTED)
    ax.set_xlabel('training pictures (log scale)', fontsize=10)
    ax.set_ylabel('share right on 800 held-out pictures', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax.set_title('With few pictures the sliding window wins, because it is given '
                 'what the other must learn', fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'data-size-curve.svg')


def conv_block_shapes() -> None:
    c, mlp, side = 96, 384, 56
    cells = side * side
    old = [('3 x 3 convolution, 96 to 96', 9 * c * c + c, 9 * c * c * cells),
           ('normalise, then ReLU', 2 * c, 0),
           ('3 x 3 convolution, 96 to 96', 9 * c * c + c, 9 * c * c * cells),
           ('normalise, then ReLU', 2 * c, 0)]
    new = [('7 x 7 convolution, one filter per channel', 49 * c + c, 49 * c * cells),
           ('normalise once', 2 * c, 0),
           ('1 x 1 convolution, 96 to 384', c * mlp + mlp, c * mlp * cells),
           ('GELU once', 0, 0),
           ('1 x 1 convolution, 384 to 96', mlp * c + c, mlp * c * cells)]
    po, mo = sum(p for _, p, _ in old), sum(m for _, _, m in old)
    pn, mn = sum(p for _, p, _ in new), sum(m for _, _, m in new)
    print(f'[block] older block {po:,} parameters and {mo / 1e6:.0f} million '
          f'multiply-adds on a {side} by {side} grid')
    print(f'[block] modern block {pn:,} parameters and {mn / 1e6:.0f} million '
          f'multiply-adds, which is {100 * mn / mo:.0f}% of the older one')

    fig, ax = plt.subplots(figsize=(11.8, 5.4), facecolor='white')
    _blank(ax, (0, 10), (0, 10))
    for x0, rows, colour, title, tot in ((0.2, old, MUTED, 'an older convolution block',
                                          (po, mo)),
                                         (5.2, new, LINK,
                                          'a modern convolution block, built the way '
                                          'a transformer block is', (pn, mn))):
        ax.text(x0, 9.2, title, fontsize=11.5, weight='bold', color=colour)
        y = 8.3
        for name, pr, mc in rows:
            _box(ax, x0, y - 0.72, 4.4, 0.72, colour, name, fs=9.5, alpha=0.16)
            ax.text(x0 + 4.5, y - 0.36, f'{pr:,}', fontsize=8.5, color=INK,
                    va='center')
            y -= 0.92
        ax.text(x0, y - 0.1, f'{tot[0]:,} parameters', fontsize=10.5, weight='bold',
                color=colour)
        ax.text(x0, y - 0.75, f'{tot[1] / 1e6:.0f} million multiply-adds on a '
                              f'{side} by {side} grid', fontsize=10, color=INK)
    ax.text(0.2, 0.9, 'The modern block keeps one normalisation and one activation, '
                      'widens the middle layer four times,', fontsize=10, color=INK)
    ax.text(0.2, 0.35, 'and spreads out the window, which are all habits taken from '
                       'the transformer block.', fontsize=10, color=INK)
    _save(fig, BACK_DOC, 'conv-block-shapes.svg')


# --------------------------------------------------------------------------
# 01_vision-backbones, section 4: how much work one picture costs
# --------------------------------------------------------------------------

def work_per_picture() -> None:
    v = vit_counts()
    r = resnet_counts()
    vit_parts = [('patch embedding', v['m_embed'], TEAL),
                 ('attention: making the\nqueries, keys and values', 12 * v['m_qkv'], LINK),
                 ('attention: the scores and\nthe weighted mix', 12 * (v['m_scores'] +
                                                                      v['m_mix']), GRIP),
                 ('attention: the output\nprojection', 12 * v['m_proj'], LINK_PALE),
                 ('the feed-forward part', 12 * v['m_mlp'], PURPLE)]
    res_parts = [('the 7 x 7 stem', r['by_stage']['stem'], TEAL)] + \
                [(f'stage {i}', r['by_stage'][f'stage{i}'],
                  [JOINT, WRIST, SLIDE, MUTED][i - 1]) for i in range(1, 5)]
    print(f"[work] vision transformer {v['m_total'] / 1e9:.2f} thousand million "
          f"multiply-adds for one 224 by 224 picture")
    for name, m, _ in vit_parts:
        print(f"[work]   {name.replace(chr(10), ' '):42s} {m / 1e9:6.2f} G "
              f"({100 * m / v['m_total']:4.1f}%)")
    print(f"[work] 50-layer convolutional network {r['m_total'] / 1e9:.2f} thousand "
          f"million, which is {v['m_total'] / r['m_total']:.1f} times less")
    for name, m, _ in res_parts:
        print(f'[work]   {name:42s} {m / 1e9:6.2f} G '
              f"({100 * m / r['m_total']:4.1f}%)")

    fig, ax = plt.subplots(figsize=(11.0, 4.9), facecolor='white')
    _plain(ax)
    ax.set_ylim(-0.55, 1.55)
    for i, (parts, label, total) in enumerate(
            ((vit_parts, 'vision transformer\n(12 blocks, 768 numbers per token)',
              v['m_total']),
             (res_parts, '50-layer convolutional network', r['m_total']))):
        left = 0.0
        for name, m, colour in parts:
            ax.barh([i], [m / 1e9], left=left / 1e9, color=colour, alpha=0.9,
                    edgecolor='white', height=0.45)
            if m / total > 0.07:
                ax.text((left + m / 2) / 1e9, i, f'{m / 1e9:.1f}', ha='center',
                        va='center', fontsize=9, color='white', weight='bold')
            left += m
        ax.text(left / 1e9 + 0.25, i, f'{total / 1e9:.1f} G', va='center',
                fontsize=11, weight='bold', color=INK)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['vision transformer\n12 blocks, 768 per token',
                        '50-layer convolutional\nnetwork'], fontsize=10)
    ax.set_xlim(0, v['m_total'] / 1e9 * 1.16)
    ax.set_xlabel('thousand million multiply-adds for one 224 by 224 picture',
                  fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.9)
               for _, _, c in vit_parts + res_parts[1:]]
    labels = [n.replace('\n', ' ') for n, _, _ in vit_parts] + \
             [f'convolutional {n}' for n, _, _ in res_parts[1:]]
    ax.legend(handles, labels, fontsize=8.5, frameon=False, ncol=2,
              loc='upper center', bbox_to_anchor=(0.5, -0.22))
    ax.set_title('The same picture, the same job, four times the arithmetic',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'work-per-picture.svg')


def cost_vs_resolution() -> None:
    sizes = [224, 320, 448, 640, 896, 1024]
    vit = [vit_counts(img=s)['m_total'] for s in sizes]
    quad = [vit_counts(img=s)['m_quad'] for s in sizes]
    res = [resnet_counts(img=s)['m_total'] for s in sizes]
    for s, a, q, b in zip(sizes, vit, quad, res):
        print(f'[res] {s:5d} px: transformer {a / 1e9:7.1f} G, of which the scores '
              f'are {100 * q / a:4.1f}%; convolutional {b / 1e9:6.1f} G')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(sizes, np.array(vit) / 1e9, marker='o', color=GRIP, lw=2,
            label='vision transformer, patch 16')
    ax.plot(sizes, np.array(res) / 1e9, marker='s', color=SLIDE, lw=2,
            label='50-layer convolutional network')
    for s, a, b in zip(sizes, vit, res):
        if s in (224, 1024):
            ax.annotate(f'{a / 1e9:.0f} G', (s, a / 1e9), textcoords='offset points',
                        xytext=(-6, 9), fontsize=9, color=GRIP, ha='right')
            ax.annotate(f'{b / 1e9:.0f} G', (s, b / 1e9), textcoords='offset points',
                        xytext=(-6, -14), fontsize=9, color=SLIDE, ha='right')
    ax.set_yscale('log')
    ax.set_xlabel('picture side, in pixels', fontsize=10)
    ax.set_ylabel('thousand million multiply-adds (log scale)', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('Work for one picture as the picture grows', fontsize=11.5,
                 weight='bold', color=INK)

    ax = axes[1]
    _plain(ax)
    share = [100 * q / a for q, a in zip(quad, vit)]
    ax.bar([str(s) for s in sizes], share, color=GRIP, alpha=0.85, width=0.6)
    for i, sh in enumerate(share):
        ax.text(i, sh + 0.8, f'{sh:.0f}%', ha='center', fontsize=10, color=INK,
                weight='bold')
    ax.set_ylim(0, max(share) * 1.25)
    ax.set_xlabel('picture side, in pixels', fontsize=10)
    ax.set_ylabel('share of the work spent comparing\nevery patch with every patch',
                  fontsize=10)
    ax.set_title('The part that grows with the square of the patch count',
                 fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'cost-vs-resolution.svg')


def patch_size_and_tokens() -> None:
    patches = [32, 16, 14, 8]
    rows = []
    for p in patches:
        v = vit_counts(img=224, patch=p)
        rows.append((p, int(v['n_patch']), v['m_total']))
        print(f"[patchsize] patch {p:2d}: {int(v['n_patch']):4d} patches, "
              f"{v['m_total'] / 1e9:6.2f} thousand million multiply-adds")

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = [f'{p} x {p}' for p, _, _ in rows]
    ax.bar(names, [n for _, n, _ in rows], color=LINK, alpha=0.85, width=0.6)
    for i, (_, n, _) in enumerate(rows):
        ax.text(i, n + 15, f'{n}', ha='center', fontsize=10, weight='bold', color=INK)
    ax.set_ylim(0, max(n for _, n, _ in rows) * 1.2)
    ax.set_xlabel('patch size, in pixels', fontsize=10)
    ax.set_ylabel('patches in a 224 by 224 picture', fontsize=10)
    ax.set_title('Smaller patches, more of them', fontsize=11.5, weight='bold',
                 color=INK)
    ax = axes[1]
    _plain(ax)
    ax.bar(names, [m / 1e9 for _, _, m in rows], color=GRIP, alpha=0.85, width=0.6)
    for i, (_, _, m) in enumerate(rows):
        ax.text(i, m / 1e9 + 2, f'{m / 1e9:.1f} G', ha='center', fontsize=10,
                weight='bold', color=INK)
    ax.set_ylim(0, max(m for _, _, m in rows) / 1e9 * 1.2)
    ax.set_xlabel('patch size, in pixels', fontsize=10)
    ax.set_ylabel('thousand million multiply-adds', fontsize=10)
    ax.set_title('and much more arithmetic', fontsize=11.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'patch-size-and-tokens.svg')


def attention_memory() -> None:
    sizes = [224, 448, 672, 1024]
    heads, depth, bytes_each = 12, 12, 2
    mb = []
    for s in sizes:
        n = int(vit_counts(img=s)['n_tok'])
        total = depth * heads * n * n * bytes_each
        mb.append(total / 1e6)
        print(f'[mem] {s} px: {n} tokens, one score table {n} x {n} = {n * n:,} '
              f'numbers, all heads and blocks together {total / 1e6:,.0f} megabytes')

    fig, ax = plt.subplots(figsize=(9.4, 4.8), facecolor='white')
    _plain(ax)
    ax.bar([str(s) for s in sizes], mb, color=PURPLE, alpha=0.85, width=0.55)
    for i, m in enumerate(mb):
        ax.text(i, m * 1.15, f'{m:,.0f} MB', ha='center', fontsize=10, weight='bold',
                color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, max(mb) * 6)
    ax.set_xlabel('picture side, in pixels', fontsize=10)
    ax.set_ylabel('megabytes of attention scores (log scale)', fontsize=10)
    ax.set_title('Room needed for the score tables alone, 12 blocks of 12 heads, '
                 'two bytes a number', fontsize=11.5, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'attention-memory.svg')


# --------------------------------------------------------------------------
# 01_vision-backbones, section 5: features at several scales
# --------------------------------------------------------------------------

def _shrink(img: Arr, factor: int) -> Arr:
    h = img.shape[0] // factor * factor
    w = img.shape[1] // factor * factor
    cut = img[:h, :w]
    return cut.reshape(h // factor, factor, w // factor, factor, 3).mean(axis=(1, 3))


def pyramid_grids() -> None:
    rgb, objects = _scene()
    bolt = next(o for o in objects if o['name'] == 'bolt')
    glass = next(o for o in objects if o['name'] == 'glass_front')
    fig, axes = plt.subplots(1, 4, figsize=(14.0, 4.4), facecolor='white')
    for ax, stride in zip(axes, (4, 8, 16, 32)):
        small = _shrink(rgb, stride)
        _show(ax, small, f'stride {stride}: a {small.shape[1]} by {small.shape[0]} grid')
        bw = (bolt['box'][2] - bolt['box'][0]) / stride
        bh = (bolt['box'][3] - bolt['box'][1]) / stride
        gw = (glass['box'][2] - glass['box'][0]) / stride
        ax.set_xlabel(f'{small.shape[0] * small.shape[1]:,} cells\n'
                      f'the bolt spans {bw:.1f} x {bh:.1f} cells\n'
                      f'the near glass spans {gw:.1f} cells across',
                      fontsize=9, color=INK)
        print(f'[pyramid] stride {stride:2d}: {small.shape[1]} by {small.shape[0]} '
              f'= {small.shape[0] * small.shape[1]:,} cells, bolt {bw:.2f} x {bh:.2f} '
              f'cells, near glass {gw:.2f} cells across')
    fig.suptitle('The same 640 by 480 picture at the four levels a detector uses',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'pyramid-grids.svg')


def apparent_size() -> None:
    width_px, fov_deg = 1280.0, 60.0
    f = (width_px / 2) / np.tan(np.radians(fov_deg / 2))
    things = [('a drinking glass, 70 mm across', 0.070, LINK),
              ('a bolt, 10 mm across', 0.010, GRIP)]
    d = np.linspace(0.3, 6.0, 200)
    print(f'[pinhole] a {width_px:.0f} pixel wide camera with a {fov_deg:.0f} degree '
          f'view has a focal length of {f:.0f} pixels')
    for name, size, _ in things:
        for dist in (0.5, 1.0, 2.0, 4.0):
            print(f'[pinhole] {name} at {dist:.1f} m looks {f * size / dist:.1f} '
                  f'pixels wide')
        print(f'[pinhole] {name} is narrower than one stride-32 cell beyond '
              f'{f * size / 32:.2f} m, and narrower than one stride-8 cell beyond '
              f'{f * size / 8:.2f} m')

    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    for name, size, colour in things:
        ax.plot(d, f * size / d, color=colour, lw=2, label=name)
    for stride, style in ((8, '--'), (16, '-.'), (32, ':')):
        ax.axhline(stride, color=MUTED, ls=style, lw=1.3)
        ax.text(5.95, stride * 1.06, f'one cell of the stride-{stride} grid',
                fontsize=9, color=MUTED, ha='right')
    for name, size, colour in things:
        dist = f * size / 32
        if 0.3 <= dist <= 6.0:
            ax.plot([dist], [32], marker='o', color=colour, markersize=8)
            ax.annotate(f'{dist:.2f} m', (dist, 32), textcoords='offset points',
                        xytext=(8, 10), fontsize=9.5, color=colour, weight='bold')
    ax.set_yscale('log')
    ax.set_ylim(1.5, 400)
    ax.set_xlim(0.3, 6.0)
    ax.set_xlabel('how far away the thing is, in metres', fontsize=10)
    ax.set_ylabel('how many pixels wide it looks (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title(f'Apparent width from the pinhole rule, for a camera {width_px:.0f} '
                 f'pixels wide with a {fov_deg:.0f} degree view',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'apparent-size.svg')


def small_object_cells() -> None:
    rgb, objects = _scene()
    bolt = next(o for o in objects if o['name'] == 'bolt')
    x1, y1, x2, y2 = bolt['box']
    w, h = x2 - x1, y2 - y1
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.6), facecolor='white')
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    half = 72
    view = rgb[int(cy - half):int(cy + half), int(cx - half):int(cx + half)]
    for ax, stride in zip(axes[:2], (8, 32)):
        _show(ax, view, f'the stride-{stride} grid over the small object')
        start_y = int(cy - half) % stride
        start_x = int(cx - half) % stride
        lo, hi = -0.5, 2 * half - 0.5
        for i in range(0, 2 * half + stride, stride):
            gy, gx = i - start_y + 0.5, i - start_x + 0.5
            if lo <= gy <= hi:
                ax.plot([lo, hi], [gy, gy], color=GRIP, lw=0.7, alpha=0.8)
            if lo <= gx <= hi:
                ax.plot([gx, gx], [lo, hi], color=GRIP, lw=0.7, alpha=0.8)
        ax.set_xlim(lo, hi)
        ax.set_ylim(hi, lo)
        _draw_box(ax, (x1 - (cx - half), y1 - (cy - half), x2 - (cx - half),
                       y2 - (cy - half)), SLIDE, None, lw=2.0)
        ax.set_xlabel(f'the object is {w:.0f} by {h:.0f} pixels, so it spans\n'
                      f'{w / stride:.2f} by {h / stride:.2f} cells of this grid',
                      fontsize=9.5, color=INK)
        print(f'[small] the bolt is {w:.0f} by {h:.0f} pixels and spans '
              f'{w / stride:.2f} by {h / stride:.2f} cells of the stride-{stride} grid')
    ax = axes[2]
    _plain(ax)
    strides = [4, 8, 16, 32]
    cover = [w * h / (s * s) for s in strides]
    ax.bar([f'stride {s}' for s in strides], cover, color=LINK, alpha=0.85, width=0.55)
    ax.axhline(1.0, color=GRIP, lw=1.6, ls='--')
    ax.text(-0.42, 1.25, 'one cell', fontsize=9.5, color=GRIP, ha='left')
    for i, c in enumerate(cover):
        ax.text(i, c * 0.55, f'{c:.2f}', ha='center', va='center', fontsize=10.5,
                weight='bold', color='white')
    ax.set_yscale('log')
    ax.set_ylim(0.05, max(cover) * 4)
    ax.set_ylabel('cells the object covers (log scale)', fontsize=10)
    ax.set_title('Below one cell, the object has no square of its own',
                 fontsize=11, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'small-object-cells.svg')


def top_down_pathway() -> None:
    levels = [(4, 160, 120, 256), (8, 80, 60, 512), (16, 40, 30, 1024),
              (32, 20, 15, 2048)]
    lateral = sum(c * 256 + 256 for _, _, _, c in levels)
    smooth = 4 * (9 * 256 * 256 + 256)
    print(f'[fpn] the 1 x 1 convolutions that bring every level to 256 channels '
          f'cost {lateral:,} parameters')
    print(f'[fpn] the four 3 x 3 convolutions that tidy the added levels cost '
          f'{smooth:,} parameters, so the whole pyramid costs {lateral + smooth:,}')

    fig, ax = plt.subplots(figsize=(11.6, 6.0), facecolor='white')
    _blank(ax, (0, 10), (0, 10))
    ax.text(0.0, 9.5, 'Building the pyramid: every level is brought to 256 channels, '
                      'then the coarse levels are added downwards',
            fontsize=12.5, weight='bold', color=INK)
    for i, (stride, gw, gh, ch) in enumerate(levels):
        y = 1.2 + i * 1.95
        _box(ax, 0.3, y, 2.5, 1.25, LINK, f'stride {stride}\n{gw} x {gh} x {ch}',
             fs=9.5, alpha=0.2)
        _box(ax, 4.3, y, 2.5, 1.25, SLIDE, f'1 x 1 convolution\n{gw} x {gh} x 256',
             fs=9.5, alpha=0.2)
        ax.text(7.0, y + 0.95, f'{ch * 256 + 256:,} parameters', fontsize=9,
                color=SLIDE)
        ax.text(7.0, y + 0.42, f'{gw * gh:,} cells of 256 numbers', fontsize=9,
                color=INK)
        _arrow(ax, (2.85, y + 0.62), (4.25, y + 0.62), MUTED)
        if i < len(levels) - 1:
            _arrow(ax, (5.55, y + 1.92), (5.55, y + 1.33), GRIP, lw=1.8)
            ax.text(5.75, y + 1.60, 'stretched to twice the size, then added',
                    fontsize=8.5, color=GRIP, va='center')
    ax.text(0.3, 0.4, f'The pyramid adds {lateral + smooth:,} parameters to the '
                      f'backbone, which is less than one block of the transformer.',
            fontsize=10, color=INK)
    _save(fig, BACK_DOC, 'top-down-pathway.svg')


# --------------------------------------------------------------------------
# 01_vision-backbones, section 6: what pretrained features look like
# --------------------------------------------------------------------------

TRAIN_CLASSES: list[str] = SHAPES[:4]
UNSEEN_CLASSES: list[str] = SHAPES[4:]


def conv_features(p: dict[str, Arr], x: Arr) -> Arr:
    """The numbers the backbone hands over: the 16 pooled outputs of the last layer."""
    a1, _ = _conv_forward(x[:, None], p['w1'], p['b1'], 2, 2)
    r1 = np.maximum(a1, 0.0)
    a2, _ = _conv_forward(r1, p['w2'], p['b2'], 2, 1)
    r2 = np.maximum(a2, 0.0)
    return r2.mean(axis=(2, 3))


FEATURES: dict | None = None


def _features() -> dict:
    global FEATURES
    if FEATURES is None:
        rng = np.random.default_rng(31)
        xtr, ytr = shape_pictures(1600, TRAIN_CLASSES, rng)
        p = conv_net_train(xtr, ytr, len(TRAIN_CLASSES), seed=77, steps=1500,
                           lr=0.005)
        xte, yte = shape_pictures(600, TRAIN_CLASSES, np.random.default_rng(32))
        acc = _conv_accuracy(p, xte, yte)
        xun, yun = shape_pictures(600, UNSEEN_CLASSES, np.random.default_rng(33))
        out = {}
        for tag, xs, ys in (('trained on', xte, yte), ('never seen', xun, yun)):
            feat = conv_features(p, xs)
            feat = (feat - feat.mean(0)) / (feat.std(0) + 1e-9)
            pix = xs.reshape(len(xs), -1)
            out[tag] = {'x': xs, 'y': ys, 'feat': feat, 'pix': pix}
        FEATURES = {'p': p, 'acc': acc, 'sets': out}
    return FEATURES


def _neighbours(space: Arr, k: int = 5) -> NDArray[np.int64]:
    d2 = ((space[:, None, :] - space[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d2, np.inf)
    return np.argsort(d2, axis=1)[:, :k]


def _agreement(space: Arr, labels: NDArray[np.int64], k: int = 5) -> float:
    nb = _neighbours(space, k)
    return float((labels[nb] == labels[:, None]).mean())


def neighbours_picture() -> None:
    f = _features()
    s = f['sets']['never seen']
    names = UNSEEN_CLASSES
    q = 7
    rows = []
    for tag, space in (('nearest in raw pixels', s['pix']),
                       ('nearest in the backbone features', s['feat'])):
        d2 = ((space - space[q]) ** 2).sum(1)
        d2[q] = np.inf
        rows.append((tag, np.argsort(d2)[:5], np.sort(d2)[:5]))
    print(f"[nn] the backbone was trained on {', '.join(TRAIN_CLASSES)} and reaches "
          f"{f['acc']:.3f} on held-out pictures of those four shapes")
    print(f'[nn] the query picture is a {names[s["y"][q]]}')
    for tag, idx, dist in rows:
        got = [names[s['y'][i]] for i in idx]
        print(f'[nn] {tag}: ' + ', '.join(got))

    fig, axes = plt.subplots(2, 6, figsize=(12.0, 4.9), facecolor='white')
    for r, (tag, idx, dist) in enumerate(rows):
        ax = axes[r][0]
        ax.imshow(s['x'][q], cmap='gray', vmin=0, vmax=1, interpolation='nearest')
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor(INK)
            sp.set_linewidth(2.0)
        ax.set_title(f'the query: a {names[s["y"][q]]}', fontsize=9.5, color=INK,
                     weight='bold')
        ax.set_ylabel(tag, fontsize=9.5, color=LINK if r else GRIP, weight='bold')
        for c in range(5):
            ax = axes[r][c + 1]
            i = idx[c]
            ax.imshow(s['x'][i], cmap='gray', vmin=0, vmax=1, interpolation='nearest')
            ax.set_xticks([])
            ax.set_yticks([])
            same = s['y'][i] == s['y'][q]
            for sp in ax.spines.values():
                sp.set_edgecolor(SLIDE if same else GRIP)
                sp.set_linewidth(2.0)
            ax.set_title(names[s['y'][i]], fontsize=9,
                         color=SLIDE if same else GRIP)
    fig.suptitle('The five closest pictures to the same query, counted two ways '
                 '(green means the same shape)', fontsize=12.5, weight='bold',
                 color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'neighbours-picture.svg')


def neighbour_agreement() -> None:
    f = _features()
    res = {}
    for tag, s in f['sets'].items():
        res[tag] = (_agreement(s['pix'], s['y']), _agreement(s['feat'], s['y']))
        print(f'[agree] shapes the backbone was {tag}: of the five nearest pictures, '
              f'{100 * res[tag][0]:.0f}% are the same shape in raw pixels and '
              f'{100 * res[tag][1]:.0f}% in the backbone features')
    chance = [1 / len(TRAIN_CLASSES), 1 / len(UNSEEN_CLASSES)]

    fig, ax = plt.subplots(figsize=(9.2, 4.8), facecolor='white')
    _plain(ax)
    tags = list(res)
    x = np.arange(len(tags))
    ax.bar(x - 0.19, [res[t][0] for t in tags], width=0.36, color=GRIP, alpha=0.88,
           label='raw pixels')
    ax.bar(x + 0.19, [res[t][1] for t in tags], width=0.36, color=LINK, alpha=0.88,
           label='the backbone features')
    for i, t in enumerate(tags):
        ax.text(i - 0.19, res[t][0] + 0.02, f'{100 * res[t][0]:.0f}%', ha='center',
                fontsize=10, weight='bold', color=INK)
        ax.text(i + 0.19, res[t][1] + 0.02, f'{100 * res[t][1]:.0f}%', ha='center',
                fontsize=10, weight='bold', color=INK)
        ax.plot([i - 0.42, i + 0.42], [chance[i], chance[i]], color=MUTED, ls='--',
                lw=1.3)
        ax.text(i + 0.42, chance[i] + 0.015, 'guessing', fontsize=8.5, color=MUTED,
                ha='right')
    ax.set_xticks(x)
    ax.set_xticklabels([f'the four shapes the backbone\nwas {tags[0]}',
                        f'three shapes it had\n{tags[1]}'], fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel('share of the five nearest pictures\nthat are the same shape',
                  fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Nearness in feature space means the same kind of thing; nearness '
                 'in pixels does not', fontsize=12, weight='bold', color=INK)
    _save(fig, BACK_DOC, 'neighbour-agreement.svg')


def _pca2(space: Arr) -> Arr:
    c = space - space.mean(0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    return c @ vt[:2].T


def feature_space_map() -> None:
    f = _features()
    s = f['sets']['never seen']
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.0), facecolor='white')
    for ax, space, tag in ((axes[0], s['pix'], 'raw pixels, 576 numbers a picture'),
                           (axes[1], s['feat'],
                            'backbone features, 48 numbers a picture')):
        _plain(ax)
        pts = _pca2(space)
        for cls, colour in zip(range(3), (LINK, GRIP, SLIDE)):
            m = s['y'] == cls
            ax.scatter(pts[m, 0], pts[m, 1], s=12, color=colour, alpha=0.75,
                       label=UNSEEN_CLASSES[cls])
        ax.set_xlabel('first direction of greatest spread', fontsize=9.5)
        ax.set_ylabel('second direction', fontsize=9.5)
        ax.set_title(tag, fontsize=11, weight='bold', color=INK)
        ax.legend(fontsize=9, frameon=False)
    fig.suptitle('600 pictures of three shapes the backbone never saw, flattened '
                 'onto two directions', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'feature-space-map.svg')


def why_pixels_fail() -> None:
    f = _features()
    s = f['sets']['never seen']
    n = 300
    rng = np.random.default_rng(44)
    a = rng.integers(0, len(s['x']), n)
    b = rng.integers(0, len(s['x']), n)
    bright = np.abs(s['x'][a].mean(axis=(1, 2)) - s['x'][b].mean(axis=(1, 2)))
    pix_d = np.sqrt(((s['pix'][a] - s['pix'][b]) ** 2).sum(1))
    fea_d = np.sqrt(((s['feat'][a] - s['feat'][b]) ** 2).sum(1))
    r_pix = float(np.corrcoef(bright, pix_d)[0, 1])
    r_fea = float(np.corrcoef(bright, fea_d)[0, 1])
    print(f'[why] over {n} random pairs, the link between the difference in overall '
          f'brightness and the distance is {r_pix:.2f} in raw pixels and '
          f'{r_fea:.2f} in the features')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white')
    for ax, d, r, tag, colour in ((axes[0], pix_d, r_pix, 'raw pixels', GRIP),
                                  (axes[1], fea_d, r_fea, 'backbone features', LINK)):
        _plain(ax)
        ax.scatter(bright, d, s=12, color=colour, alpha=0.6)
        fit = np.polyfit(bright, d, 1)
        xs = np.linspace(0, bright.max(), 50)
        ax.plot(xs, np.polyval(fit, xs), color=INK, lw=1.6, ls='--')
        ax.set_xlabel('difference in overall brightness between two pictures',
                      fontsize=9.5)
        ax.set_ylabel(f'distance between them in {tag}', fontsize=9.5)
        ax.set_title(f'{tag}: link = {r:.2f}', fontsize=11.5, weight='bold',
                     color=colour)
    fig.suptitle('Why raw pixels group pictures badly: the distance mostly measures '
                 'brightness', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, BACK_DOC, 'why-pixels-fail.svg')


# --------------------------------------------------------------------------
# 02_detection-and-segmentation, shared pieces
# --------------------------------------------------------------------------

CLASS_COLOUR: dict[str, str] = {'glass': LINK, 'mug': GRIP, 'box': JOINT,
                                'bolt': PURPLE}
INSTANCE_COLOUR: list[str] = [LINK, TEAL, SLIDE, JOINT, GRIP, PURPLE]


def _overlay(rgb: Arr, mask: Arr, colour: str, alpha: float = 0.65) -> Arr:
    out = rgb.copy()
    c = np.array(matplotlib.colors.to_rgb(colour))
    out[mask] = (1 - alpha) * out[mask] + alpha * c
    return out


def _iou(a: tuple[float, float, float, float],
         b: tuple[float, float, float, float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def simulated_detections() -> list[dict]:
    """Guesses a one-stage detector might make: several per object, plus mistakes.

    The jitter and the scores come from numpy.random.default_rng(101), and the
    score is tied to how well the guess covers the object, as a trained
    detector's score usually is.
    """
    _, objects = _scene()
    rng = np.random.default_rng(101)
    dets: list[dict] = []
    for ob in objects:
        x1, y1, x2, y2 = ob['box']
        for k in range(rng.integers(3, 6)):
            s = 4.0 + 9.0 * k
            box = (x1 + rng.normal(0, s), y1 + rng.normal(0, s),
                   x2 + rng.normal(0, s), y2 + rng.normal(0, s))
            box = (min(box[0], box[2]), min(box[1], box[3]),
                   max(box[0], box[2]), max(box[1], box[3]))
            ov = _iou(box, ob['box'])
            score = float(np.clip(0.97 - 0.85 * (1 - ov) + rng.normal(0, 0.05),
                                  0.05, 0.99))
            dets.append({'box': box, 'score': score, 'from': ob['name']})
    for _ in range(5):
        w, h = rng.uniform(40, 110), rng.uniform(40, 110)
        x = rng.uniform(20, W - w - 20)
        y = rng.uniform(180, H - h - 20)
        dets.append({'box': (x, y, x + w, y + h),
                     'score': float(rng.uniform(0.15, 0.55)), 'from': 'nothing'})
    dets.sort(key=lambda d: -d['score'])
    return dets


DETS: list[dict] | None = None


def _dets() -> list[dict]:
    global DETS
    if DETS is None:
        DETS = simulated_detections()
    return DETS


def nms(dets: list[dict], thresh: float) -> tuple[list[int], list[tuple[int, int, float]]]:
    """Keep the best-scoring box, drop everything that overlaps it too much, repeat."""
    order = list(range(len(dets)))
    keep: list[int] = []
    killed: list[tuple[int, int, float]] = []
    while order:
        i = order.pop(0)
        keep.append(i)
        rest = []
        for j in order:
            ov = _iou(dets[i]['box'], dets[j]['box'])
            if ov > thresh:
                killed.append((j, i, ov))
            else:
                rest.append(j)
        order = rest
    return keep, killed


def match_detections(dets: list[dict], truth: list[tuple[float, float, float, float]],
                     thresh: float = 0.5) -> list[dict]:
    """Walk the guesses from the best score down, matching each to an unused object."""
    used = set()
    rows = []
    for d in dets:
        best, best_ov = -1, 0.0
        any_ov = 0.0
        for k, t in enumerate(truth):
            ov = _iou(d['box'], t)
            any_ov = max(any_ov, ov)
            if k in used:
                continue
            if ov > best_ov:
                best, best_ov = k, ov
        hit = best >= 0 and best_ov >= thresh
        if hit:
            used.add(best)
        rows.append({'score': d['score'], 'iou': any_ov, 'free_iou': best_ov,
                     'hit': hit, 'again': (not hit) and any_ov >= thresh,
                     'box': d['box'], 'from': d['from']})
    return rows


def pr_curve(rows: list[dict], n_truth: int) -> tuple[Arr, Arr, float]:
    hits = np.array([1.0 if r['hit'] else 0.0 for r in rows])
    tp = np.cumsum(hits)
    fp = np.cumsum(1 - hits)
    precision = tp / (tp + fp)
    recall = tp / n_truth
    ap = 0.0
    prev_r = 0.0
    for p, r in zip(precision, recall):
        ap += (r - prev_r) * max(precision[recall >= r].max(), 0.0)
        prev_r = r
    return precision, recall, float(ap)


# --------------------------------------------------------------------------
# 02_detection-and-segmentation, section 1: four different jobs
# --------------------------------------------------------------------------

def four_jobs() -> None:
    rgb, objects = _scene()
    classes = sorted({o['cls'] for o in objects})
    per_class = {c: int(sum(o['area'] for o in objects if o['cls'] == c))
                 for c in classes}
    print(f'[jobs] the scene holds {len(objects)} objects of {len(classes)} kinds: '
          + ', '.join(f'{c} ({sum(1 for o in objects if o["cls"] == c)})'
                      for c in classes))
    for c in classes:
        print(f'[jobs] class {c:6s} covers {per_class[c]:,} pixels, which is '
              f'{100 * per_class[c] / (H * W):.1f}% of the picture')

    fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.0), facecolor='white')
    ax = axes[0][0]
    _show(ax, rgb, 'naming the picture: one answer for the whole picture')
    ax.text(12, 44, 'glasses  0.71\ntable     0.18\nmug       0.07', fontsize=11,
            color=INK, va='top', family='monospace',
            bbox=dict(facecolor='white', edgecolor=MUTED, alpha=0.9))
    ax.set_xlabel('the scores are simulated; the job gives no place and no count',
                  fontsize=9)

    ax = axes[0][1]
    _show(ax, rgb, 'putting a box round each object')
    for i, ob in enumerate(objects):
        _draw_box(ax, ob['box'], CLASS_COLOUR[ob['cls']], ob['cls'], lw=2.0,
                  above=i % 2 == 0)
    ax.set_xlabel(f'{len(objects)} boxes, each 4 numbers and a class name', fontsize=9)

    ax = axes[1][0]
    out = rgb.copy()
    for c in classes:
        m = np.zeros((H, W), dtype=bool)
        for ob in objects:
            if ob['cls'] == c:
                m |= ob['mask']
        out = _overlay(out, m, CLASS_COLOUR[c])
    _show(ax, out, 'labelling every pixel with a class')
    ax.set_xlabel('the three glasses share one colour, so they are one region',
                  fontsize=9)

    ax = axes[1][1]
    out = rgb.copy()
    for i, ob in enumerate(objects):
        out = _overlay(out, ob['mask'], INSTANCE_COLOUR[i % len(INSTANCE_COLOUR)])
    _show(ax, out, 'labelling every pixel with which object it belongs to')
    for i, ob in enumerate(objects):
        x1, y1, x2, y2 = ob['box']
        ax.text((x1 + x2) / 2, y1 - 6, str(i + 1), fontsize=10, weight='bold',
                color=INK, ha='center')
    ax.set_xlabel('each glass now has its own colour and its own pixel count',
                  fontsize=9)
    fig.suptitle('Four different jobs on one picture of a table',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'four-jobs.svg')


def class_versus_instance() -> None:
    rgb, objects = _scene()
    glasses = [o for o in objects if o['cls'] == 'glass']
    merged = np.zeros((H, W), dtype=bool)
    for g in glasses:
        merged |= g['mask']
    ys, xs = np.nonzero(merged)
    cx, cy = xs.mean(), ys.mean()
    box = (xs.min(), ys.min(), xs.max(), ys.max())
    on = [g['name'] for g in glasses if g['mask'][int(round(cy)), int(round(cx))]]
    one = glasses[1]
    oys, oxs = np.nonzero(one['mask'])
    ocx, ocy = oxs.mean(), oys.mean()
    width_ratio = (box[2] - box[0]) / (one['box'][2] - one['box'][0])
    print(f'[class] the glass region holds {int(merged.sum()):,} pixels and spans '
          f'{box[2] - box[0]:.0f} by {box[3] - box[1]:.0f} pixels')
    print(f'[class] its middle is at ({cx:.0f}, {cy:.0f}), which lands on '
          f'{on[0] if on else "no glass at all"}')
    print(f'[class] the whole region is {width_ratio:.1f} times as wide as one '
          f'glass, which is {one["box"][2] - one["box"][0]:.0f} pixels across')
    for g in glasses:
        gy, gx = np.nonzero(g['mask'])
        print(f'[class] {g["name"]:12s} {g["area"]:6,} pixels, middle at '
              f'({gx.mean():.0f}, {gy.mean():.0f})')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    ax = axes[0]
    _show(ax, _overlay(rgb, merged, LINK), 'one class: all the glass pixels together')
    _draw_box(ax, box, INK, None, lw=1.6)
    ax.plot([cx], [cy], marker='X', color=GRIP, markersize=14, markeredgecolor='white')
    ax.set_xlabel(f'{int(merged.sum()):,} pixels in one region, '
                  f'{box[2] - box[0]:.0f} pixels wide, middle marked with a cross',
                  fontsize=9.5)
    ax = axes[1]
    out = rgb.copy()
    for i, g in enumerate(glasses):
        out = _overlay(out, g['mask'], INSTANCE_COLOUR[i])
    _show(ax, out, 'three objects: each glass on its own')
    for i, g in enumerate(glasses):
        gy, gx = np.nonzero(g['mask'])
        ax.plot([gx.mean()], [gy.mean()], marker='X', color=INK, markersize=11,
                markeredgecolor='white')
        ax.text(gx.mean(), gy.mean() - 16, f'{g["area"]:,} px', fontsize=9,
                ha='center', color=INK, weight='bold')
    ax.set_xlabel('three regions with three middles, one of which the arm can reach',
                  fontsize=9.5)
    fig.suptitle('Why picking one glass out of several needs the fourth job, not '
                 'the third', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'class-versus-instance.svg')


def output_sizes() -> None:
    _, objects = _scene()
    n = len(objects)
    jobs = [('naming the picture', 4, 'four class scores'),
            ('a box for each object', n * 6, f'{n} boxes of 4 numbers, a class and '
                                             f'a score'),
            ('a class for every pixel', H * W, f'{H} rows of {W} numbers'),
            ('an object number for every pixel', H * W + n * 2,
             f'{H} by {W} numbers and a class and a score for each object')]
    for name, count, how in jobs:
        print(f'[sizes] {name:34s} {count:9,} numbers ({how})')

    fig, ax = plt.subplots(figsize=(10.2, 4.4), facecolor='white')
    _plain(ax)
    names = [j[0] for j in jobs]
    vals = [j[1] for j in jobs]
    bars = ax.barh(names[::-1], vals[::-1], color=[PURPLE, PURPLE, LINK, SLIDE][::-1],
                   alpha=0.88, height=0.55)
    for b, v in zip(bars, vals[::-1]):
        ax.text(v * 1.3, b.get_y() + b.get_height() / 2, f'{v:,}', va='center',
                fontsize=10, weight='bold', color=INK)
    ax.set_xscale('log')
    ax.set_xlim(1, max(vals) * 12)
    ax.set_xlabel('numbers in the answer, for one 640 by 480 picture (log scale)',
                  fontsize=10)
    ax.tick_params(axis='y', labelsize=9.5)
    ax.set_title('The four jobs give back answers of very different sizes',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, SEG_DOC, 'output-sizes.svg')


def grasp_point_from_each_job() -> None:
    rgb, objects = _scene()
    glasses = [o for o in objects if o['cls'] == 'glass']
    target = glasses[1]                      # the glass nearest the camera
    merged = np.zeros((H, W), dtype=bool)
    for g in glasses:
        merged |= g['mask']
    ys, xs = np.nonzero(merged)
    class_pt = (xs.mean(), ys.mean())
    x1, y1, x2, y2 = target['box']
    box_pt = ((x1 + x2) / 2, (y1 + y2) / 2)
    tys, txs = np.nonzero(target['mask'])
    inst_pt = (txs.mean(), tys.mean())
    on_target = {'box middle': target['mask'][int(round(box_pt[1])),
                                              int(round(box_pt[0]))],
                 'class middle': target['mask'][int(round(class_pt[1])),
                                                int(round(class_pt[0]))],
                 'object middle': target['mask'][int(round(inst_pt[1])),
                                                 int(round(inst_pt[0]))]}
    gap = np.hypot(class_pt[0] - inst_pt[0], class_pt[1] - inst_pt[1])
    print(f'[grasp] the box middle is at ({box_pt[0]:.0f}, {box_pt[1]:.0f}), the '
          f'class middle at ({class_pt[0]:.0f}, {class_pt[1]:.0f}) and the object '
          f'middle at ({inst_pt[0]:.0f}, {inst_pt[1]:.0f})')
    print(f'[grasp] the class middle is {gap:.0f} pixels from the object middle, '
          f'and the box middle is '
          f'{np.hypot(box_pt[0] - inst_pt[0], box_pt[1] - inst_pt[1]):.0f} pixels '
          f'from it')
    for name, hit in on_target.items():
        print(f'[grasp] the {name} lands on the chosen glass: {bool(hit)}')

    fig, ax = plt.subplots(figsize=(9.6, 6.4), facecolor='white')
    _show(ax, _overlay(rgb, target['mask'], TEAL, 0.45),
          'one job: pick up the glass nearest the camera')
    _draw_box(ax, target['box'], TEAL, None, lw=2.0)
    marks = [('naming the picture gives no point at all', None, MUTED),
             ('middle of the box', box_pt, JOINT),
             ('middle of the glass class region', class_pt, GRIP),
             ('middle of this object alone', inst_pt, SLIDE)]
    for size, (name, pt, colour) in zip((0, 22, 16, 11), marks):
        if pt is None:
            continue
        ax.plot([pt[0]], [pt[1]], marker='X', color=colour, markersize=size,
                markeredgecolor='white', markeredgewidth=1.2)
    ax.legend(handles=[plt.Line2D([], [], marker='X', ls='', color=c, markersize=11,
                                  label=n) for n, p, c in marks],
              fontsize=9.5, loc='lower left', framealpha=0.92)
    ax.set_xlabel(f'the class middle sits {gap:.0f} pixels away from the object '
                  f'middle, on a different glass', fontsize=10, color=INK)
    _save(fig, SEG_DOC, 'grasp-point-from-each-job.svg')


# --------------------------------------------------------------------------
# 02_detection-and-segmentation, section 2: boxes and how a guess is scored
# --------------------------------------------------------------------------

def box_as_numbers() -> None:
    rgb, objects = _scene()
    mug = next(o for o in objects if o['name'] == 'mug')
    x1, y1, x2, y2 = mug['box']
    cx, cy, bw, bh = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
    print(f'[box] the mug box by corners: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, '
          f'{y2:.0f})')
    print(f'[box] the same box by middle and size: ({cx:.0f}, {cy:.0f}) and '
          f'{bw:.0f} by {bh:.0f}')
    print(f'[box] the same box as fractions of the picture: {cx / W:.3f}, '
          f'{cy / H:.3f}, {bw / W:.3f}, {bh / H:.3f}')
    print(f'[box] the box holds {int(bw * bh):,} pixels and the mug itself '
          f'{mug["area"]:,}, so {100 * mug["area"] / (bw * bh):.0f}% of the box is '
          f'mug')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                             width_ratios=[1.15, 1.0])
    ax = axes[0]
    _show(ax, rgb[170:400, 330:520], 'the box around the mug')
    bx = (x1 - 330, y1 - 170, x2 - 330, y2 - 170)
    _draw_box(ax, bx, GRIP, None, lw=2.2)
    ax.plot([(bx[0] + bx[2]) / 2], [(bx[1] + bx[3]) / 2], marker='+', color=GRIP,
            markersize=12)
    ax.annotate(f'({x1:.0f}, {y1:.0f})', (bx[0], bx[1]), textcoords='offset points',
                xytext=(-6, 8), fontsize=9.5, color=GRIP, ha='left', weight='bold')
    ax.annotate(f'({x2:.0f}, {y2:.0f})', (bx[2], bx[3]), textcoords='offset points',
                xytext=(4, -12), fontsize=9.5, color=GRIP, ha='right', weight='bold')
    ax.set_xlabel('the corner numbers are counted in pixels from the top left of '
                  'the whole picture', fontsize=9)
    ax = axes[1]
    _blank(ax, (0, 10), (0, 10))
    rows = [('the two corners', f'x1 = {x1:.0f},  y1 = {y1:.0f}\n'
                                f'x2 = {x2:.0f},  y2 = {y2:.0f}', LINK),
            ('the middle and the size', f'middle ({cx:.0f}, {cy:.0f})\n'
                                        f'{bw:.0f} wide, {bh:.0f} tall', SLIDE),
            ('as fractions of the picture', f'{cx / W:.3f}, {cy / H:.3f}\n'
                                            f'{bw / W:.3f}, {bh / H:.3f}', PURPLE)]
    ax.text(0.0, 9.4, 'The same box written three ways', fontsize=12.5,
            weight='bold', color=INK)
    y = 7.6
    for name, body, colour in rows:
        ax.text(0.0, y + 1.0, name, fontsize=10.5, color=colour, weight='bold')
        _box(ax, 0.0, y - 0.6, 9.4, 1.5, colour, body, fs=11, alpha=0.14)
        y -= 2.6
    ax.text(0.0, 0.6, f'The box holds {int(bw * bh):,} pixels, and only '
                      f'{mug["area"]:,} of them, or '
                      f'{100 * mug["area"] / (bw * bh):.0f} in every hundred, are mug.',
            fontsize=10, color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'box-as-numbers.svg')


def iou_arithmetic() -> None:
    rgb, objects = _scene()
    truth = next(o for o in objects if o['name'] == 'glass_front')['box']
    pick = [d for d in _dets() if d['from'] == 'glass_front']
    guess = min(pick, key=lambda d: abs(_iou(d['box'], truth) - 0.6))['box']
    ix1, iy1 = max(truth[0], guess[0]), max(truth[1], guess[1])
    ix2, iy2 = min(truth[2], guess[2]), min(truth[3], guess[3])
    iw, ih = ix2 - ix1, iy2 - iy1
    inter = iw * ih
    a_t = (truth[2] - truth[0]) * (truth[3] - truth[1])
    a_g = (guess[2] - guess[0]) * (guess[3] - guess[1])
    union = a_t + a_g - inter
    print(f'[iou] true box ({truth[0]:.0f}, {truth[1]:.0f}, {truth[2]:.0f}, '
          f'{truth[3]:.0f}) covers {a_t:,.0f} pixels')
    print(f'[iou] guessed box ({guess[0]:.0f}, {guess[1]:.0f}, {guess[2]:.0f}, '
          f'{guess[3]:.0f}) covers {a_g:,.0f} pixels')
    print(f'[iou] the overlap is {iw:.0f} wide and {ih:.0f} tall, so {inter:,.0f} '
          f'pixels; the union is {a_t:,.0f} + {a_g:,.0f} - {inter:,.0f} = '
          f'{union:,.0f}')
    print(f'[iou] intersection over union = {inter:,.0f} / {union:,.0f} = '
          f'{inter / union:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.2), facecolor='white',
                             width_ratios=[1.0, 1.1])
    ax = axes[0]
    view = rgb[170:370, 110:260]
    _show(ax, view, 'one true box and one guess')
    shift = (110, 170, 110, 170)
    tb = tuple(t - s for t, s in zip(truth, shift))
    gb = tuple(g - s for g, s in zip(guess, shift))
    ax.add_patch(Rectangle((ix1 - 110, iy1 - 170), iw, ih, facecolor=JOINT,
                           alpha=0.45, edgecolor='none'))
    _draw_box(ax, tb, SLIDE, 'the true box', lw=2.2)
    _draw_box(ax, gb, GRIP, 'the guess', lw=2.2, above=False)
    ax.set_xlabel('the shaded rectangle is the overlap', fontsize=9.5)
    ax = axes[1]
    _blank(ax, (0, 10), (0, 10))
    lines = [
        ('the overlap, left and right',
         f'from max({truth[0]:.0f}, {guess[0]:.0f}) = {ix1:.0f} '
         f'to min({truth[2]:.0f}, {guess[2]:.0f}) = {ix2:.0f}, so {iw:.0f} wide'),
        ('the overlap, top and bottom',
         f'from max({truth[1]:.0f}, {guess[1]:.0f}) = {iy1:.0f} '
         f'to min({truth[3]:.0f}, {guess[3]:.0f}) = {iy2:.0f}, so {ih:.0f} tall'),
        ('the overlap in pixels',
         f'{iw:.0f} x {ih:.0f} = {inter:,.0f}'),
        ('the two boxes in pixels',
         f'{a_t:,.0f} and {a_g:,.0f}'),
        ('the union in pixels',
         f'{a_t:,.0f} + {a_g:,.0f} - {inter:,.0f} = {union:,.0f}'),
        ('overlap divided by union',
         f'{inter:,.0f} / {union:,.0f} = {inter / union:.3f}'),
    ]
    ax.text(0.0, 9.5, 'Intersection over union, worked out', fontsize=12.5,
            weight='bold', color=INK)
    y = 8.2
    for name, body in lines:
        colour = SLIDE if 'divided' in name else MUTED
        ax.text(0.0, y, name, fontsize=9.5, color=colour, weight='bold')
        ax.text(0.0, y - 0.55, body, fontsize=10.5, color=INK, family='monospace')
        y -= 1.42
    _save(fig, SEG_DOC, 'iou-arithmetic.svg')


def iou_ladder() -> None:
    rgb, objects = _scene()
    truth = next(o for o in objects if o['name'] == 'glass_front')['box']
    w = truth[2] - truth[0]
    h = truth[3] - truth[1]
    shifts = [0.0, 0.10, 0.25, 0.45, 0.75]
    fig, axes = plt.subplots(1, len(shifts), figsize=(14.0, 4.2), facecolor='white')
    print('[ladder] the same true box with five guesses, each moved further:')
    for ax, f in zip(axes, shifts):
        guess = (truth[0] + f * w, truth[1] + f * h * 0.4, truth[2] + f * w,
                 truth[3] + f * h * 0.4)
        ov = _iou(truth, guess)
        view = rgb[170:380, 120:300]
        _show(ax, view, f'moved {f * 100:.0f}% of a width')
        sh = (120, 170, 120, 170)
        _draw_box(ax, tuple(t - s for t, s in zip(truth, sh)), SLIDE, None, lw=2.0)
        _draw_box(ax, tuple(g - s for g, s in zip(guess, sh)), GRIP, None, lw=2.0)
        ax.set_xlabel(f'overlap over union = {ov:.2f}', fontsize=11,
                      color=GRIP if ov < 0.5 else SLIDE, weight='bold')
        print(f'[ladder] moved by {f:.2f} of a width: overlap over union {ov:.3f}')
    fig.suptitle('What different amounts of overlap look like, with the true box in '
                 'green and the guess in red', fontsize=12.5, weight='bold',
                 color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'iou-ladder.svg')


def iou_threshold_count() -> None:
    _, objects = _scene()
    truth = [o['box'] for o in objects]
    keep, _ = nms(_dets(), 0.5)
    kept = [_dets()[i] for i in keep]
    ths = [0.3, 0.5, 0.6, 0.7, 0.8, 0.9]
    counts = []
    for t in ths:
        rows = match_detections(kept, truth, t)
        counts.append(sum(1 for r in rows if r['hit']))
        print(f'[thresh] at an overlap of {t:.1f} or more, {counts[-1]} of the '
              f'{len(truth)} objects are counted as found, from {len(kept)} guesses')

    fig, ax = plt.subplots(figsize=(9.0, 4.6), facecolor='white')
    _plain(ax)
    ax.bar([f'{t:.1f}' for t in ths], counts, color=LINK, alpha=0.88, width=0.55)
    ax.axhline(len(truth), color=SLIDE, ls='--', lw=1.6)
    ax.text(5.45, len(truth) + 0.12, f'{len(truth)} objects are really there',
            fontsize=9.5, color=SLIDE, ha='right')
    for i, c in enumerate(counts):
        ax.text(i, c + 0.12, str(c), ha='center', fontsize=11, weight='bold',
                color=INK)
    ax.set_ylim(0, len(truth) + 1.2)
    ax.set_xlabel('the overlap a guess must reach to count as right', fontsize=10)
    ax.set_ylabel('objects counted as found', fontsize=10)
    ax.set_title('The same guesses, scored against different ideas of "right"',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, SEG_DOC, 'iou-threshold-count.svg')


# --------------------------------------------------------------------------
# 02_detection-and-segmentation, section 3: many guesses, and suppression
# --------------------------------------------------------------------------

ANCHORS: int = 3


def why_many_guesses() -> None:
    rgb, objects = _scene()
    mug = next(o for o in objects if o['name'] == 'mug')
    stride = 32
    gw, gh = W // stride, H // stride
    centres = [(stride / 2 + stride * i, stride / 2 + stride * j)
               for j in range(gh) for i in range(gw)]
    inside = [c for c in centres if mug['box'][0] <= c[0] <= mug['box'][2]
              and mug['box'][1] <= c[1] <= mug['box'][3]]
    print(f'[many] the stride-{stride} grid has {gw} by {gh} = {gw * gh} cells, and '
          f'with {ANCHORS} box shapes a cell that is {gw * gh * ANCHORS} guesses for '
          f'one picture')
    print(f'[many] {len(inside)} cell middles fall inside the mug, so {len(inside)} '
          f'cells can all see the mug and {len(inside) * ANCHORS} guesses are made '
          f'about it')

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.9), facecolor='white')
    ax = axes[0]
    _show(ax, rgb, f'the stride-{stride} grid over the whole picture')
    for i in range(1, gw):
        ax.plot([i * stride, i * stride], [0, H - 1], color=GRID, lw=0.6)
    for j in range(1, gh):
        ax.plot([0, W - 1], [j * stride, j * stride], color=GRID, lw=0.6)
    _draw_box(ax, mug['box'], GRIP, 'the mug', lw=2.0)
    for cxy in inside:
        ax.plot([cxy[0]], [cxy[1]], marker='o', color=SLIDE, markersize=5)
    ax.set_xlabel(f'{gw} x {gh} = {gw * gh} cells, each asked the same question',
                  fontsize=9.5)
    ax = axes[1]
    view = rgb[220:380, 340:500]
    _show(ax, view, 'the nine cells whose middles land on the mug')
    rng = np.random.default_rng(55)
    for cxy in inside:
        ax.plot([cxy[0] - 340], [cxy[1] - 220], marker='o', color=SLIDE,
                markersize=6)
        for _ in range(ANCHORS):
            w = (mug['box'][2] - mug['box'][0]) * rng.uniform(0.75, 1.25)
            h = (mug['box'][3] - mug['box'][1]) * rng.uniform(0.75, 1.25)
            _draw_box(ax, (cxy[0] - 340 - w / 2, cxy[1] - 220 - h / 2,
                           cxy[0] - 340 + w / 2, cxy[1] - 220 + h / 2), LINK, None,
                      lw=0.8)
    ax.set_xlabel(f'{len(inside)} cells x {ANCHORS} box shapes = '
                  f'{len(inside) * ANCHORS} guesses about one mug', fontsize=9.5)
    fig.suptitle('Why a detector guesses many times: every cell answers for itself',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'why-many-guesses.svg')


def nms_steps() -> None:
    rgb, _ = _scene()
    dets = [d for d in _dets() if d['score'] >= 0.4]
    thresh = 0.5
    order = list(range(len(dets)))
    steps: list[tuple[int, list[int]]] = []
    keep: list[int] = []
    while order:
        i = order.pop(0)
        keep.append(i)
        dropped = [j for j in order if _iou(dets[i]['box'], dets[j]['box']) > thresh]
        order = [j for j in order if j not in dropped]
        steps.append((i, dropped))
    print(f'[nms] {len(dets)} guesses score 0.40 or more, and suppression at an '
          f'overlap of {thresh} leaves {len(keep)}')
    for n, (i, dropped) in enumerate(steps[:4], start=1):
        drops = ', '.join(f"{dets[j]['score']:.2f} (overlap "
                          f"{_iou(dets[i]['box'], dets[j]['box']):.2f})"
                          for j in dropped)
        print(f'[nms] step {n}: keep the guess scoring {dets[i]["score"]:.2f}; '
              f'drop {len(dropped)} guesses' + (f': {drops}' if drops else ''))
    print('[nms] the boxes left standing, by score: '
          + ', '.join(f'{dets[i]["score"]:.2f}' for i in keep))

    fig, axes = plt.subplots(2, 3, figsize=(13.2, 7.4), facecolor='white')
    flat = axes.ravel()
    _show(flat[0], rgb, f'all {len(dets)} guesses scoring 0.40 or more')
    for d in dets:
        _draw_box(flat[0], d['box'], LINK, None, lw=1.1)
    flat[0].set_xlabel('every guess, before anything is removed', fontsize=9)
    shown = []
    for n in range(4):
        ax = flat[n + 1]
        i, dropped = steps[n]
        _show(ax, rgb, f'step {n + 1}: keep {dets[i]["score"]:.2f}, '
                       f'drop {len(dropped)}')
        for j in dropped:
            _draw_box(ax, dets[j]['box'], GRIP, f'{dets[j]["score"]:.2f}', lw=1.2,
                      fs=7.5)
        for k in shown:
            _draw_box(ax, dets[k]['box'], MUTED, None, lw=1.0)
        _draw_box(ax, dets[i]['box'], SLIDE, f'{dets[i]["score"]:.2f}', lw=2.2,
                  fs=8.5)
        shown.append(i)
        ax.set_xlabel('green is kept, red is dropped for overlapping it',
                      fontsize=8.5)
    ax = flat[5]
    _show(ax, rgb, f'what is left: {len(keep)} boxes')
    for i in keep:
        _draw_box(ax, dets[i]['box'], SLIDE, f'{dets[i]["score"]:.2f}', lw=1.8,
                  fs=8)
    ax.set_xlabel('one box an object, except where the guesses were poor',
                  fontsize=8.5)
    fig.suptitle(f'Non-maximum suppression, step by step, at an overlap of {thresh}',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'nms-steps.svg')


def nms_threshold() -> None:
    _, objects = _scene()
    dets = [d for d in _dets() if d['score'] >= 0.4]
    ths = np.arange(0.1, 0.95, 0.05)
    counts = []
    for t in ths:
        keep, _ = nms(dets, float(t))
        counts.append(len(keep))
    print('[nms-th] survivors at each suppression threshold: '
          + ', '.join(f'{t:.2f}->{c}' for t, c in zip(ths, counts)))

    fig, ax = plt.subplots(figsize=(9.6, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(ths, counts, marker='o', color=LINK, lw=2)
    ax.axhline(len(objects), color=SLIDE, ls='--', lw=1.6)
    ax.text(0.9, len(objects) + 0.35, f'{len(objects)} objects are really there',
            fontsize=9.5, color=SLIDE, ha='right')
    ax.annotate('too strict: real objects that stand close\ntogether are removed as '
                'duplicates', xy=(0.15, counts[1]), xytext=(0.22, 11.5),
                fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.annotate('too loose: the same object keeps\nseveral boxes', xy=(0.85,
                counts[-1]), xytext=(0.52, 14.5), fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.2))
    ax.set_xlabel('the overlap above which a lower-scoring box is dropped',
                  fontsize=10)
    ax.set_ylabel('boxes left standing', fontsize=10)
    ax.set_ylim(0, max(counts) + 3)
    ax.set_title('One number decides how many boxes come out', fontsize=12,
                 weight='bold', color=INK)
    _save(fig, SEG_DOC, 'nms-threshold.svg')


def nms_close_objects() -> None:
    rgb, objects = _scene()
    front = next(o for o in objects if o['name'] == 'glass_front')
    back = next(o for o in objects if o['name'] == 'glass_back')
    true_ov = _iou(front['box'], back['box'])
    dets = [d for d in _dets() if d['score'] >= 0.4]
    print(f'[close] the two glasses that stand together have boxes that overlap by '
          f'{true_ov:.3f} of their union')
    results = {}
    for t in (0.3, 0.5):
        keep, _ = nms(dets, t)
        found = set()
        for i in keep:
            for ob in (front, back):
                if _iou(dets[i]['box'], ob['box']) > 0.5:
                    found.add(ob['name'])
        results[t] = (len(keep), sorted(found))
        print(f'[close] suppressing at {t}: {len(keep)} boxes left, and the glasses '
              f'found are {sorted(found)}')

    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.6), facecolor='white')
    view = (120, 170, 260, 360)
    sub = rgb[view[1]:view[3], view[0]:view[2]]
    ax = axes[0]
    _show(ax, sub, 'two real objects, standing close')
    _draw_box(ax, (front['box'][0] - view[0], front['box'][1] - view[1],
                   front['box'][2] - view[0], front['box'][3] - view[1]), SLIDE,
              'glass in front', lw=2.0)
    _draw_box(ax, (back['box'][0] - view[0], back['box'][1] - view[1],
                   back['box'][2] - view[0], back['box'][3] - view[1]), LINK,
              'glass behind', lw=2.0, above=False)
    ax.set_xlabel(f'their true boxes already overlap by {true_ov:.2f}', fontsize=9.5)
    for ax, t in ((axes[1], 0.3), (axes[2], 0.5)):
        keep, _ = nms(dets, t)
        _show(ax, sub, f'suppressing at an overlap of {t}')
        for i in keep:
            b = dets[i]['box']
            if b[0] < view[2] and b[2] > view[0] and b[1] < view[3]:
                _draw_box(ax, (b[0] - view[0], b[1] - view[1], b[2] - view[0],
                               b[3] - view[1]), GRIP, f'{dets[i]["score"]:.2f}',
                          lw=1.8, fs=8.5)
        ax.set_xlabel(f'{len(results[t][1])} of the two glasses survive: '
                      + ', '.join(results[t][1]), fontsize=9.5)
    fig.suptitle('The price of suppression: a true object can be removed for looking '
                 'like a duplicate', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, SEG_DOC, 'nms-close-objects.svg')


# --------------------------------------------------------------------------
# 02_detection-and-segmentation, section 4: precision, recall and the curve
# --------------------------------------------------------------------------

def _kept_rows(thresh: float = 0.5) -> tuple[list[dict], list[tuple]]:
    _, objects = _scene()
    truth = [o['box'] for o in objects]
    keep, _ = nms(_dets(), 0.5)
    kept = [_dets()[i] for i in keep]
    return match_detections(kept, truth, thresh), truth


def ranked_detections() -> None:
    rows, truth = _kept_rows()
    n = len(truth)
    tp = fp = 0
    table = []
    for r in rows[:12]:
        if r['hit']:
            tp += 1
        else:
            fp += 1
        why = 'yes' if r['hit'] else ('already found' if r['again'] else 'no')
        table.append((r['score'], r['iou'], why, tp / (tp + fp), tp / n))
    print('[rank] score  best overlap  right  precision  recall')
    for s, ov, why, pr, rc in table:
        print(f'[rank] {s:.2f}   {ov:.2f}     {why:14s} {pr:.2f}       {rc:.2f}')

    fig, ax = plt.subplots(figsize=(10.6, 6.4), facecolor='white')
    _blank(ax, (0, 10), (0, 10))
    heads = ['score', 'best overlap', 'counts as right?', 'precision so far',
             'recall so far']
    xs = [0.6, 2.4, 4.4, 6.6, 8.6]
    ax.text(0.0, 9.6, f'The guesses in score order, after suppression, against the '
                      f'{n} real objects', fontsize=12.5, weight='bold', color=INK)
    for x, h in zip(xs, heads):
        ax.text(x, 8.9, h, fontsize=10, weight='bold', color=MUTED, ha='center')
    y = 8.3
    for s, ov, why, pr, rc in table:
        colour = SLIDE if why == 'yes' else GRIP
        ax.add_patch(Rectangle((0.0, y - 0.28), 9.7, 0.58, facecolor=colour,
                               alpha=0.10, edgecolor='none'))
        for x, val in zip(xs, [f'{s:.2f}', f'{ov:.2f}', why, f'{pr:.2f}',
                               f'{rc:.2f}']):
            ax.text(x, y - 0.06, val, fontsize=10.5, ha='center', color=INK)
        y -= 0.68
    ax.text(0.0, y - 0.1, 'A guess counts as right when it overlaps an object by 0.5 '
                          'or more and that object has not already been found by a '
                          'better-scoring guess.', fontsize=9.5, color=MUTED)
    _save(fig, SEG_DOC, 'ranked-detections.svg')


def precision_recall() -> None:
    rows, truth = _kept_rows()
    precision, recall, ap = pr_curve(rows, len(truth))
    print(f'[pr] with {len(rows)} guesses and {len(truth)} objects, the average '
          f'precision is {ap:.3f}')
    print(f'[pr] at the top guess precision is {precision[0]:.2f} and recall '
          f'{recall[0]:.2f}; at the end precision is {precision[-1]:.2f} and recall '
          f'{recall[-1]:.2f}')

    fig, ax = plt.subplots(figsize=(8.6, 5.2), facecolor='white')
    _plain(ax)
    ax.step(recall, precision, where='post', color=LINK, lw=2.2)
    ax.fill_between(recall, precision, step='post', color=LINK, alpha=0.15)
    ax.scatter(recall, precision, s=22, color=LINK)
    for i in (0, 2, 5, len(rows) - 1):
        ax.annotate(f'score {rows[i]["score"]:.2f}', (recall[i], precision[i]),
                    textcoords='offset points', xytext=(8, 8), fontsize=9,
                    color=MUTED)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.08)
    ax.set_xlabel('recall: the share of the real objects found', fontsize=10)
    ax.set_ylabel('precision: the share of the guesses that were right', fontsize=10)
    ax.set_title(f'Precision against recall, walking down the score order; the area '
                 f'under it is {ap:.3f}', fontsize=12, weight='bold', color=INK)
    _save(fig, SEG_DOC, 'precision-recall.svg')


def threshold_tradeoff() -> None:
    rows, truth = _kept_rows()
    ths = np.arange(0.05, 0.96, 0.05)
    prec, rec = [], []
    for t in ths:
        taken = [r for r in rows if r['score'] >= t]
        hits = sum(1 for r in taken if r['hit'])
        prec.append(hits / len(taken) if taken else 1.0)
        rec.append(hits / len(truth))
    for t, p, r in zip(ths, prec, rec):
        if abs(t - 0.3) < 0.01 or abs(t - 0.5) < 0.01 or abs(t - 0.7) < 0.01:
            print(f'[trade] keeping guesses that score {t:.2f} or more: precision '
                  f'{p:.2f}, recall {r:.2f}')

    fig, ax = plt.subplots(figsize=(9.4, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(ths, prec, marker='o', color=LINK, lw=2, label='precision')
    ax.plot(ths, rec, marker='s', color=GRIP, lw=2, label='recall')
    ax.axvline(0.5, color=MUTED, ls=':', lw=1.4)
    ax.text(0.51, 0.06, 'a common place to\nset the threshold', fontsize=9,
            color=MUTED)
    ax.set_ylim(0, 1.08)
    ax.set_xlabel('the lowest score a guess may have and still be kept', fontsize=10)
    ax.set_ylabel('share', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='center left')
    ax.set_title('Raising the score threshold buys precision with recall',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, SEG_DOC, 'threshold-tradeoff.svg')


def ap_at_thresholds() -> None:
    ths = [0.5, 0.6, 0.7, 0.8, 0.9]
    aps = []
    for t in ths:
        rows, truth = _kept_rows(t)
        aps.append(pr_curve(rows, len(truth))[2])
        print(f'[ap] demanding an overlap of {t:.1f}: average precision '
              f'{aps[-1]:.3f}')
    print(f'[ap] the mean of those five numbers is {np.mean(aps):.3f}')

    fig, ax = plt.subplots(figsize=(8.8, 4.6), facecolor='white')
    _plain(ax)
    ax.bar([f'{t:.1f}' for t in ths], aps, color=LINK, alpha=0.88, width=0.55)
    ax.axhline(float(np.mean(aps)), color=GRIP, ls='--', lw=1.6)
    ax.text(4.45, np.mean(aps) + 0.03, f'their mean, {np.mean(aps):.2f}',
            fontsize=9.5, color=GRIP, ha='right')
    for i, a in enumerate(aps):
        ax.text(i, a + 0.02, f'{a:.2f}', ha='center', fontsize=10.5, weight='bold',
                color=INK)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel('the overlap a guess must reach to count as right', fontsize=10)
    ax.set_ylabel('average precision', fontsize=10)
    ax.set_title('One detector, five scores, depending on how strict you are',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, SEG_DOC, 'ap-at-thresholds.svg')
