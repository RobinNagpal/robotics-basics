"""Generate the diagrams for both pages of docs/06_neural-networks/13_using-a-model-for-real/.

    01_running-and-evaluating-a-model.md -> images/using-a-model-for-real/running-and-evaluating-a-model/
    02_the-map-of-models.md              -> images/using-a-model-for-real/the-map-of-models/

Run with:  pixi run python ../docs/diagrams/using_a_model_for_real.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints each one with a tag such as [p1-s5], so the two documents can quote the
same values.

What is real arithmetic here: the parameter counts, the file sizes, the
multiply-add counts, the launch-overhead sums, the batching curves, the latency
budget, the Clopper-Pearson confidence intervals, the exact probability that two
such intervals separate, the two-proportion sample-size formula, the compounding
of a per-step success rate, and the page counts of the book.

What is simulated, with a seeded numpy.random.default_rng so it is the same
every run: the four-colour object pictures used for the preprocessing and the
out-of-distribution experiments, the synthetic scene used for the resize
comparison, the episode simulator used for the loss-against-success scatter and
for the ablations, the workspace trials, and the three logged failure episodes.
The example machine (its multiply-add rate, its memory bandwidth and its launch
overhead) and the example timings of the camera and the bus are stated example
figures, not measurements of any named hardware.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'using-a-model-for-real')
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

RUN_DOC: str = 'running-and-evaluating-a-model'
MAP_DOC: str = 'the-map-of-models'

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
    for side in ax.spines:
        ax.spines[side].set_visible(False)


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str, edge: str = INK, size: float = 9.5,
         weight: str = 'normal', tcol: str = INK) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.02',
                                linewidth=1.2, edgecolor=edge, facecolor=face, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size,
            color=tcol, weight=weight, zorder=3)


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = MUTED, lw: float = 1.3) -> None:
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>',
                                 mutation_scale=11, linewidth=lw,
                                 color=colour, zorder=1,
                                 shrinkA=0.0, shrinkB=0.0))


def _wrap(text: str, width: int) -> str:
    """Break a title into lines of at most `width` characters."""
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if len(trial) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return '\n'.join(lines)


def _resize(img: Arr, out_h: int, out_w: int) -> Arr:
    """Plain bilinear resize of a height x width x 3 picture."""
    h, w = img.shape[0], img.shape[1]
    ys = np.clip((np.arange(out_h) + 0.5) * h / out_h - 0.5, 0, h - 1)
    xs = np.clip((np.arange(out_w) + 0.5) * w / out_w - 0.5, 0, w - 1)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    wy = (ys - y0)[:, None, None]
    wx = (xs - x0)[None, :, None]
    top = img[y0][:, x0] * (1 - wx) + img[y0][:, x1] * wx
    bot = img[y1][:, x0] * (1 - wx) + img[y1][:, x1] * wx
    return top * (1 - wy) + bot * wy


# --------------------------------------------------------------------------
# exact binomial arithmetic, used by the evaluation pictures
# --------------------------------------------------------------------------

_LOGFACT: Arr = np.concatenate([[0.0], np.cumsum(np.log(np.arange(1, 2001)))])


def _binom_pmf(n: int, p: float) -> Arr:
    k = np.arange(n + 1)
    out = np.zeros(n + 1)
    if p <= 0.0:
        out[0] = 1.0
        return out
    if p >= 1.0:
        out[n] = 1.0
        return out
    log_choose = _LOGFACT[n] - _LOGFACT[k] - _LOGFACT[n - k]
    return np.exp(log_choose + k * math.log(p) + (n - k) * math.log1p(-p))


def _bisect(f, lo: float, hi: float) -> float:
    """Root of an increasing function f on [lo, hi]."""
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


_CP_CACHE: dict[tuple[int, int], tuple[float, float]] = {}


def cp_interval(x: int, n: int) -> tuple[float, float]:
    """The exact (Clopper-Pearson) 95% confidence interval for x successes in n trials."""
    key = (x, n)
    if key in _CP_CACHE:
        return _CP_CACHE[key]
    a = 0.05
    lo = 0.0 if x == 0 else _bisect(lambda p: float(_binom_pmf(n, p)[x:].sum()) - a / 2, 0.0, 1.0)
    hi = 1.0 if x == n else _bisect(lambda p: a / 2 - float(_binom_pmf(n, p)[:x + 1].sum()), 0.0, 1.0)
    _CP_CACHE[key] = (lo, hi)
    return lo, hi


def separation_chance(n: int, p_bad: float, p_good: float) -> float:
    """Exact chance that the two 95% intervals do not overlap, with n trials each."""
    pb = _binom_pmf(n, p_bad)
    pg = _binom_pmf(n, p_good)
    hi_bad = np.array([cp_interval(x, n)[1] for x in range(n + 1)])
    lo_good = np.array([cp_interval(x, n)[0] for x in range(n + 1)])
    sep = (hi_bad[:, None] < lo_good[None, :]).astype(float)
    return float((pb[:, None] * pg[None, :] * sep).sum())


# ==========================================================================
# the example policy: one configuration, used by several pictures
# ==========================================================================

class Policy:
    """An example arm policy, stated as shapes, with its parameters and arithmetic.

    Two 224 x 224 colour cameras go through a shared picture encoder of 12
    transformer blocks at width 384 with 14-pixel patches. Sixty-four pooled
    tokens per camera, one joint-state token and sixteen action queries go
    through a trunk of 6 blocks at width 512. A table of 32,000 word pieces
    embeds the instruction. The head gives 16 future commands of 7 numbers.
    """

    def __init__(self) -> None:
        self.img = 224
        self.patch = 14
        self.vit_tokens = (self.img // self.patch) ** 2        # 256
        self.vit_d = 384
        self.vit_blocks = 12
        self.cameras = 2
        self.pooled = 64
        self.trunk_d = 512
        self.trunk_blocks = 6
        self.action_queries = 16
        self.action_dims = 7
        self.vocab = 32000
        self.text_tokens = 16
        self.trunk_tokens = self.cameras * self.pooled + 1 + self.text_tokens + self.action_queries

        def block_params(d: int) -> int:
            qkv = 3 * d * d + 3 * d
            proj = d * d + d
            mlp = d * (4 * d) + 4 * d + (4 * d) * d + d
            norms = 4 * d
            return qkv + proj + mlp + norms

        def block_macs(d: int, t: int) -> int:
            qkv = 3 * t * d * d
            scores = t * t * d
            mix = t * t * d
            proj = t * d * d
            mlp = 2 * t * d * (4 * d)
            return qkv + scores + mix + proj + mlp

        self.patch_params = 3 * self.patch * self.patch * self.vit_d + self.vit_d
        self.pos_params = self.vit_tokens * self.vit_d
        self.vit_params = (self.patch_params + self.pos_params
                           + self.vit_blocks * block_params(self.vit_d))
        self.proj_params = self.vit_d * self.trunk_d + self.trunk_d
        self.embed_params = self.vocab * self.trunk_d
        self.query_params = self.action_queries * self.trunk_d
        self.head_params = (self.trunk_d * self.trunk_d + self.trunk_d
                            + self.trunk_d * self.action_dims + self.action_dims)
        self.trunk_params = self.trunk_blocks * block_params(self.trunk_d)
        self.total_params = (self.vit_params + self.proj_params + self.embed_params
                             + self.query_params + self.head_params + self.trunk_params)

        self.patch_macs = self.vit_tokens * (3 * self.patch * self.patch) * self.vit_d
        self.vit_macs = self.cameras * (self.patch_macs
                                        + self.vit_blocks * block_macs(self.vit_d, self.vit_tokens))
        self.proj_macs = self.cameras * self.pooled * self.vit_d * self.trunk_d
        self.trunk_macs = self.trunk_blocks * block_macs(self.trunk_d, self.trunk_tokens)
        self.head_macs = self.action_queries * (self.trunk_d * self.trunk_d
                                                + self.trunk_d * self.action_dims)
        self.total_macs = self.vit_macs + self.proj_macs + self.trunk_macs + self.head_macs

        # Operations in the graph, counted as a plain framework would run them.
        self.ops_per_block = 13       # 2 norms, qkv, 2 matmuls, softmax, proj, 2 adds, fc1, act, fc2
        self.ops_plain = (self.cameras * (1 + self.vit_blocks * self.ops_per_block)
                          + 1 + self.trunk_blocks * self.ops_per_block + 3)
        self.ops_fused = (self.cameras * (1 + self.vit_blocks * 3)
                          + 1 + self.trunk_blocks * 3 + 3)

        # The example machine. These are stated example figures, not measurements.
        self.launch_us = 5.0                      # microseconds of overhead per operation
        self.bandwidth = 100e9                    # bytes a second to and from memory
        self.mac_rate = {'float32': 1.2e12, 'float16': 3.6e12, 'int8': 7.2e12}
        self.bytes_per_number = {'float32': 4, 'float16': 2, 'int8': 1}

    def weight_megabytes(self, precision: str) -> float:
        return self.total_params * self.bytes_per_number[precision] / 1e6

    def arithmetic_ms(self, precision: str) -> float:
        return 1000.0 * self.total_macs / self.mac_rate[precision]

    def memory_ms(self, precision: str) -> float:
        return 1000.0 * self.total_params * self.bytes_per_number[precision] / self.bandwidth

    def overhead_ms(self, fused: bool) -> float:
        ops = self.ops_fused if fused else self.ops_plain
        return ops * self.launch_us / 1000.0

    def forward_ms(self, precision: str, fused: bool = True) -> float:
        return max(self.arithmetic_ms(precision), self.memory_ms(precision)) + self.overhead_ms(fused)


POL = Policy()


def report_policy() -> None:
    p = POL
    print(f'[p1-s1] picture encoder parameters   {p.vit_params:,}')
    print(f'[p1-s1] trunk parameters             {p.trunk_params:,}')
    print(f'[p1-s1] word-piece table parameters  {p.embed_params:,}')
    print(f'[p1-s1] projector+queries+head       {p.proj_params + p.query_params + p.head_params:,}')
    print(f'[p1-s1] total parameters             {p.total_params:,}')
    print(f'[p1-s1] weights file  float32 {p.weight_megabytes("float32"):.1f} MB'
          f'   float16 {p.weight_megabytes("float16"):.1f} MB'
          f'   int8 {p.weight_megabytes("int8"):.1f} MB')
    print(f'[p1-s1] word-piece table share of the file '
          f'{100 * p.embed_params / p.total_params:.1f}%')
    print(f'[p1-s3] multiply-adds: cameras {p.vit_macs:,}  projector {p.proj_macs:,}'
          f'  trunk {p.trunk_macs:,}  head {p.head_macs:,}  total {p.total_macs:,}')
    print(f'[p1-s3] trunk tokens {p.trunk_tokens}')
    for prec in ('float32', 'float16', 'int8'):
        print(f'[p1-s3] {prec:8s} arithmetic {p.arithmetic_ms(prec):6.2f} ms   '
              f'memory {p.memory_ms(prec):5.2f} ms   '
              f'forward with fusion {p.forward_ms(prec):5.2f} ms')
    print(f'[p1-s3] operations plain {p.ops_plain}  fused {p.ops_fused}  '
          f'overhead plain {p.overhead_ms(False):.2f} ms  fused {p.overhead_ms(True):.2f} ms')


# ==========================================================================
# page 1, section 1: what a trained model is when it is a set of files
# ==========================================================================

def checkpoint_files() -> None:
    """The files of the example checkpoint, with the sizes worked out."""
    p = POL
    names = ['model.safetensors\nthe weights',
             'config.json\nthe shapes',
             'preprocessor.json\nthe picture settings',
             'action_stats.json\nthe command scaling',
             'tokenizer.json\nthe word pieces']
    counts = [p.total_params, 14, 9, 2 * (p.action_dims + 1), p.vocab]
    kinds = ['learned numbers', 'settings', 'settings', 'measured numbers', 'entries']
    colours = [LINK_PALE, '#fde9c8', '#fde9c8', '#d8f0d8', '#e6dff5']

    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.97, 'One trained policy on a disk: 57 million learned numbers, '
                       'and four small files they are useless without',
            ha='center', va='top', fontsize=12.5, weight='bold', color=INK)
    for i, (nm, c, kind, col) in enumerate(zip(names, counts, kinds, colours)):
        x = 0.02 + i * 0.196
        _box(ax, x, 0.46, 0.176, 0.30, nm, col)
        ax.text(x + 0.088, 0.40, f'{c:,}', ha='center', va='center',
                fontsize=12, weight='bold', color=INK)
        ax.text(x + 0.088, 0.345, kind, ha='center', va='center', fontsize=9, color=MUTED)
    mb32 = p.weight_megabytes('float32')
    mb16 = p.weight_megabytes('float16')
    ax.text(0.108, 0.80, f'{mb32:.0f} MB at four bytes a number\n{mb16:.0f} MB at two',
            ha='center', va='bottom', fontsize=9.5, color=LINK)
    ax.text(0.5, 0.22,
            'Lose any one of the four small files and the weights alone cannot be used:\n'
            'the shapes say how to rebuild the network, the picture settings say how to turn a photo\n'
            'into the numbers it was trained on, and the command scaling turns its output back into joint angles.',
            ha='center', va='center', fontsize=10, color=INK)
    _save(fig, RUN_DOC, 'checkpoint-files.svg')


def parameter_shares() -> None:
    """Where the 57 million parameters sit, and what each part costs in bytes."""
    p = POL
    parts = ['picture encoder\n(12 blocks, width 384)',
             'trunk\n(6 blocks, width 512)',
             'word-piece table\n(32,000 x 512)',
             'projector, queries, head']
    vals = [p.vit_params, p.trunk_params, p.embed_params,
            p.proj_params + p.query_params + p.head_params]
    for nm, v in zip(parts, vals):
        print(f'[p1-s1] share {nm.splitlines()[0]:24s} {v:12,}  {100 * v / p.total_params:5.1f}%')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.25, 1.0]})
    _plain(ax1)
    y = np.arange(len(parts))[::-1]
    cols = [LINK, TEAL, PURPLE, JOINT]
    ax1.barh(y, [v / 1e6 for v in vals], color=cols, height=0.58)
    for yy, v in zip(y, vals):
        ax1.text(v / 1e6 + 0.4, yy, f'{v / 1e6:.1f} M  ({100 * v / p.total_params:.0f}%)',
                 va='center', fontsize=9.5, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels(parts, fontsize=9)
    ax1.set_xlim(0, max(vals) / 1e6 * 1.38)
    ax1.set_xlabel('parameters, in millions', fontsize=10)
    ax1.set_title('More than a quarter of the file is the word-piece table',
                   fontsize=11.5, weight='bold')

    _plain(ax2)
    precs = ['float32', 'float16', 'int8']
    mbs = [p.weight_megabytes(q) for q in precs]
    ax2.bar(np.arange(3), mbs, color=[LINK, TEAL, SLIDE], width=0.55)
    for i, m in enumerate(mbs):
        ax2.text(i, m + 4, f'{m:.0f} MB', ha='center', fontsize=10, weight='bold', color=INK)
    ax2.set_xticks(np.arange(3))
    ax2.set_xticklabels(['4 bytes\na number', '2 bytes\na number', '1 byte\na number'], fontsize=9.5)
    ax2.set_ylim(0, max(mbs) * 1.22)
    ax2.set_ylabel('size of the weights file (MB)', fontsize=10)
    ax2.set_title('The same weights, written three ways', fontsize=11.5, weight='bold')
    _save(fig, RUN_DOC, 'parameter-shares.svg')


def _scene(rng: np.random.Generator) -> Arr:
    """A simulated 288 x 384 table scene: a shaded tabletop with three objects."""
    h, w = 288, 384
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3))
    table = np.stack([0.72 - 0.18 * yy / h, 0.62 - 0.16 * yy / h, 0.50 - 0.14 * yy / h], axis=-1)
    img += table
    for (cy, cx, r, col) in [(118, 96, 38, (0.74, 0.22, 0.18)),
                             (196, 232, 46, (0.22, 0.34, 0.66)),
                             (84, 308, 26, (0.88, 0.74, 0.22))]:
        m = ((yy - cy) ** 2 + (xx - cx) ** 2) < r * r
        for c in range(3):
            img[:, :, c] = np.where(m, col[c], img[:, :, c])
    img += rng.normal(0.0, 0.015, size=img.shape)
    return np.clip(img, 0.0, 1.0) * 255.0


def resize_mismatch() -> None:
    """Two picture settings on one scene, and the difference they leave behind."""
    rng = np.random.default_rng(11)
    scene = _scene(rng)
    squash = _resize(scene, 224, 224)
    short = _resize(scene, 256, int(round(384 * 256 / 288)))      # short side to 256
    top = (short.shape[0] - 224) // 2
    left = (short.shape[1] - 224) // 2
    crop = short[top:top + 224, left:left + 224]
    diff = np.abs(squash - crop).mean(axis=2)
    mad = float(diff.mean())
    frac = float((diff > 10.0).mean())
    print(f'[p1-s1] resize mismatch: mean absolute pixel difference {mad:.1f} of 255, '
          f'{100 * frac:.0f}% of pixels differ by more than 10')

    fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.9), facecolor='white')
    for ax in axes:
        _blank(ax)
    axes[0].imshow(scene.astype(np.uint8))
    axes[0].set_title('the camera picture\n288 rows by 384 columns', fontsize=10)
    axes[1].imshow(squash.astype(np.uint8))
    axes[1].set_title('setting A: squash the whole\npicture to 224 by 224', fontsize=10)
    axes[2].imshow(crop.astype(np.uint8))
    axes[2].set_title('setting B: short side to 256,\nthen cut out the middle 224', fontsize=10)
    im = axes[3].imshow(diff, cmap='inferno', vmin=0, vmax=120)
    axes[3].set_title(f'difference, A against B\nmean {mad:.1f} of 255', fontsize=10)
    cb = fig.colorbar(im, ax=axes[3], fraction=0.046, pad=0.04)
    cb.set_label('difference in brightness', fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    fig.suptitle('Two picture settings, one scene: the numbers the network sees are not the same',
                 fontsize=12.5, weight='bold', y=1.02)
    _save(fig, RUN_DOC, 'resize-mismatch.svg')


# ==========================================================================
# page 1, section 2: preprocessing has to match training
# ==========================================================================

CLASS_NAMES: list[str] = ['red mug', 'orange tin', 'brown block', 'grey plate']
CLASS_RGB: Arr = np.array([[0.72, 0.26, 0.22],
                           [0.80, 0.46, 0.18],
                           [0.55, 0.36, 0.24],
                           [0.52, 0.52, 0.54]])


def make_objects(n: int, rng: np.random.Generator, light: float = 1.0,
                 tint: Arr | None = None, noise: float = 0.045
                 ) -> tuple[Arr, NDArray[np.int64]]:
    """Simulated object patches: mean red, green and blue of each, plus its class."""
    labels = rng.integers(0, 4, size=n)
    base = CLASS_RGB[labels]
    shade = rng.uniform(0.74, 1.26, size=(n, 1))
    feats = base * shade * light
    if tint is not None:
        feats = feats + tint
    feats = feats + rng.normal(0.0, noise, size=feats.shape)
    return np.clip(feats, 0.0, 1.0), labels


def train_colour_model(x: Arr, y: NDArray[np.int64], steps: int = 900,
                       lr: float = 0.6) -> tuple[Arr, Arr]:
    """Plain multi-class logistic regression, trained by gradient descent in NumPy."""
    w = np.zeros((x.shape[1], 4))
    b = np.zeros(4)
    hot = np.eye(4)[y]
    for _ in range(steps):
        z = x @ w + b
        z = z - z.max(axis=1, keepdims=True)
        pr = np.exp(z)
        pr /= pr.sum(axis=1, keepdims=True)
        g = (pr - hot) / len(x)
        w -= lr * (x.T @ g)
        b -= lr * g.sum(axis=0)
    return w, b


def _accuracy(x: Arr, y: NDArray[np.int64], w: Arr, b: Arr) -> float:
    return float(((x @ w + b).argmax(axis=1) == y).mean())


class ColourModel:
    """One trained colour classifier, with the normalisation it was trained under."""

    def __init__(self) -> None:
        rng = np.random.default_rng(7)
        xtr, ytr = make_objects(4000, rng)
        self.mean = xtr.mean(axis=0)
        self.std = xtr.std(axis=0)
        self.w, self.b = train_colour_model((xtr - self.mean) / self.std, ytr)
        self.xte, self.yte = make_objects(2000, np.random.default_rng(8))
        self.base = _accuracy((self.xte - self.mean) / self.std, self.yte, self.w, self.b)

    def accuracy_with(self, mean: Arr, std: Arr, x: Arr | None = None,
                      y: NDArray[np.int64] | None = None) -> float:
        xx = self.xte if x is None else x
        yy = self.yte if y is None else y
        return _accuracy((xx - mean) / std, yy, self.w, self.b)


COL = ColourModel()


def wrong_normalisation() -> None:
    """Accuracy against the size of the mistake in the normalisation settings."""
    factors = np.linspace(0.4, 2.2, 37)
    acc_std = [COL.accuracy_with(COL.mean, COL.std * f) for f in factors]
    shifts = np.linspace(-0.3, 0.3, 37)
    acc_mean = [COL.accuracy_with(COL.mean + s, COL.std) for s in shifts]
    print(f'[p1-s2] colour model accuracy with the right settings {100 * COL.base:.1f}%')
    for f in (0.5, 0.8, 1.0, 1.25, 2.0):
        print(f'[p1-s2]   divide by {f:.2f} times the right spread -> '
              f'{100 * COL.accuracy_with(COL.mean, COL.std * f):.1f}%')
    for s in (-0.2, -0.1, 0.1, 0.2):
        print(f'[p1-s2]   subtract a mean that is {s:+.2f} out -> '
              f'{100 * COL.accuracy_with(COL.mean + s, COL.std):.1f}%')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    _plain(ax1)
    ax1.plot(factors, [100 * a for a in acc_std], color=LINK, lw=2.2)
    ax1.axvline(1.0, color=SLIDE, lw=1.4, ls='--')
    ax1.text(1.03, 32, 'the setting the\nmodel was trained with', fontsize=9, color=SLIDE)
    ax1.scatter([1.0], [100 * COL.base], color=SLIDE, zorder=4, s=36)
    ax1.set_xlabel('the spread used at run time, as a multiple of the trained one', fontsize=10)
    ax1.set_ylabel('accuracy on 2,000 test objects (%)', fontsize=10)
    ax1.set_ylim(15, 100)
    ax1.set_title('Dividing by the wrong spread', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.plot(shifts, [100 * a for a in acc_mean], color=PURPLE, lw=2.2)
    ax2.axvline(0.0, color=SLIDE, lw=1.4, ls='--')
    ax2.scatter([0.0], [100 * COL.base], color=SLIDE, zorder=4, s=36)
    ax2.set_xlabel('error in the mean that is subtracted (brightness units of 0 to 1)', fontsize=10)
    ax2.set_ylabel('accuracy (%)', fontsize=10)
    ax2.set_ylim(15, 100)
    ax2.set_title('Subtracting the wrong mean', fontsize=11.5, weight='bold')
    fig.suptitle('A settings file that is slightly wrong costs accuracy and raises no error',
                 fontsize=12.5, weight='bold', y=1.02)
    _save(fig, RUN_DOC, 'wrong-normalisation.svg')


def channel_swap() -> None:
    """Red and blue swapped: the single commonest silent preprocessing fault."""
    xte, yte = COL.xte, COL.yte
    swapped = xte[:, [2, 1, 0]]
    acc_ok = COL.base
    acc_bad = COL.accuracy_with(COL.mean, COL.std, swapped, yte)
    pred_bad = ((swapped - COL.mean) / COL.std @ COL.w + COL.b).argmax(axis=1)
    conf = np.zeros((4, 4))
    for t, p in zip(yte, pred_bad):
        conf[t, p] += 1
    conf = 100 * conf / conf.sum(axis=1, keepdims=True)
    print(f'[p1-s2] red and blue swapped: accuracy falls from {100 * acc_ok:.1f}% '
          f'to {100 * acc_bad:.1f}%')
    for i, nm in enumerate(CLASS_NAMES):
        print(f'[p1-s2]   {nm:12s} called {CLASS_NAMES[int(conf[i].argmax())]:12s} '
              f'{conf[i].max():.0f}% of the time')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.4), facecolor='white',
                                   gridspec_kw={'width_ratios': [0.8, 1.2]})
    _plain(ax1)
    ax1.bar([0, 1], [100 * acc_ok, 100 * acc_bad], color=[SLIDE, GRIP], width=0.5)
    for i, v in enumerate([100 * acc_ok, 100 * acc_bad]):
        ax1.text(i, v + 2, f'{v:.1f}%', ha='center', fontsize=11, weight='bold', color=INK)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['channels in the\ntrained order', 'red and blue\nswapped'], fontsize=9.5)
    ax1.set_ylim(0, 108)
    ax1.set_ylabel('accuracy (%)', fontsize=10)
    ax1.set_title('One line of loading code', fontsize=11.5, weight='bold')

    _blank(ax2)
    im = ax2.imshow(conf, cmap='Blues', vmin=0, vmax=100)
    ax2.set_xticks(range(4))
    ax2.set_yticks(range(4))
    ax2.set_xticklabels(CLASS_NAMES, fontsize=8.5, rotation=20, ha='right')
    ax2.set_yticklabels(CLASS_NAMES, fontsize=8.5)
    ax2.tick_params(length=0)
    for i in range(4):
        for j in range(4):
            ax2.text(j, i, f'{conf[i, j]:.0f}', ha='center', va='center', fontsize=9.5,
                     color='white' if conf[i, j] > 55 else INK)
    ax2.set_xlabel('what the model said', fontsize=10)
    ax2.set_ylabel('what it really was', fontsize=10)
    ax2.set_title('With the channels swapped, in per cent of each row', fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'channel-swap.svg')


JOINT_LOW: Arr = np.array([-170.0, -95.0, -140.0, -170.0, -110.0, -175.0, 0.0])
JOINT_HIGH: Arr = np.array([170.0, 95.0, 140.0, 170.0, 110.0, 175.0, 85.0])
OTHER_LOW: Arr = np.array([-150.0, -80.0, -120.0, -180.0, -120.0, -160.0, 0.0])
OTHER_HIGH: Arr = np.array([150.0, 110.0, 155.0, 180.0, 95.0, 190.0, 60.0])


def action_scaling() -> None:
    """Un-scaling a command with the wrong measured numbers, in degrees of error."""
    rng = np.random.default_rng(21)
    out = rng.uniform(-1.0, 1.0, size=(400, 7))

    def unscale(lo: Arr, hi: Arr) -> Arr:
        return lo + (out + 1.0) * 0.5 * (hi - lo)

    right = unscale(JOINT_LOW, JOINT_HIGH)
    wrong = unscale(OTHER_LOW, OTHER_HIGH)
    err = np.abs(right - wrong)
    per_joint = err.mean(axis=0)
    print(f'[p1-s2] wrong command scaling: mean error {err.mean():.1f} degrees, '
          f'worst joint {per_joint.max():.1f} degrees on joint {int(per_joint.argmax()) + 1}, '
          f'largest single error {err.max():.1f} degrees')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.4), facecolor='white')
    fig.subplots_adjust(wspace=0.3)
    _plain(ax1)
    x = np.arange(7)
    ax1.bar(x - 0.19, JOINT_HIGH - JOINT_LOW, width=0.36, color=LINK,
            label='range in the training data')
    ax1.bar(x + 0.19, OTHER_HIGH - OTHER_LOW, width=0.36, color=WRIST,
            label='range in the file that was loaded')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'J{i + 1}' for i in range(6)] + ['grip'], fontsize=9.5)
    ax1.set_ylabel('width of the range (degrees, or mm for the grip)', fontsize=9.5)
    ax1.legend(fontsize=9, frameon=False, loc='upper left')
    ax1.set_ylim(0, 420)
    ax1.set_title('Two command-scaling files that look alike', fontsize=11, weight='bold')

    _plain(ax2)
    ax2.bar(x, per_joint, color=GRIP, width=0.55)
    for i, v in enumerate(per_joint):
        ax2.text(i, v + 0.7, f'{v:.1f}', ha='center', fontsize=9, color=INK)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'J{i + 1}' for i in range(6)] + ['grip'], fontsize=9.5)
    ax2.set_ylabel('average error in the command sent (degrees)', fontsize=9.5)
    ax2.set_ylim(0, per_joint.max() * 1.25)
    ax2.set_title(f'The arm ends up {err.mean():.1f} degrees out, on average',
                  fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'action-scaling.svg')


# ==========================================================================
# page 1, section 3: export and runtimes
# ==========================================================================

def macs_by_stage() -> None:
    """Where the arithmetic of one forward pass goes, and how long it takes."""
    p = POL
    names = ['two camera encoders\n(2 x 12 blocks, 256 tokens)',
             'trunk\n(6 blocks, 161 tokens)',
             'projector',
             'action head']
    vals = [p.vit_macs, p.trunk_macs, p.proj_macs, p.head_macs]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.25, 1.0]})
    fig.subplots_adjust(wspace=0.35)
    _plain(ax1)
    y = np.arange(len(names))[::-1]
    ax1.barh(y, [v / 1e6 for v in vals], color=[LINK, TEAL, PURPLE, JOINT], height=0.55)
    ax1.set_xscale('log')
    for yy, v in zip(y, vals):
        ax1.text(v / 1e6 * 1.3, yy, f'{v / 1e6:,.0f} million  ({100 * v / p.total_macs:.1f}%)',
                 va='center', fontsize=9, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=9)
    ax1.set_xlim(1, 2e5)
    ax1.set_xlabel('multiply-adds in one forward pass, in millions (log scale)', fontsize=9.5)
    ax1.set_title(f'{p.total_macs / 1e9:.1f} thousand million multiply-adds, one decision',
                  fontsize=11, weight='bold')

    _plain(ax2)
    precs = ['float32', 'float16', 'int8']
    ar = [p.arithmetic_ms(q) for q in precs]
    me = [p.memory_ms(q) for q in precs]
    x = np.arange(3)
    ax2.bar(x - 0.18, ar, width=0.34, color=LINK, label='time the arithmetic needs')
    ax2.bar(x + 0.18, me, width=0.34, color=GRID, edgecolor=INK,
            label='time reading the weights needs')
    for i in range(3):
        ax2.text(i - 0.18, ar[i] + 0.25, f'{ar[i]:.1f}', ha='center', fontsize=9, color=INK)
        ax2.text(i + 0.18, me[i] + 0.25, f'{me[i]:.2f}', ha='center', fontsize=9, color=INK)
    ax2.set_xticks(x)
    ax2.set_xticklabels(precs, fontsize=10)
    ax2.set_ylabel('milliseconds', fontsize=10)
    ax2.set_ylim(0, max(ar) * 1.2)
    ax2.legend(fontsize=9, frameon=False)
    ax2.set_title('The arithmetic is what costs the time',
                  fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'macs-by-stage.svg')


def launch_overhead() -> None:
    """Counting the separate operations, before and after they are joined up."""
    p = POL
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.4), facecolor='white')
    fig.subplots_adjust(wspace=0.3)
    _plain(ax1)
    ax1.bar([0, 1], [p.ops_plain, p.ops_fused], color=[WRIST, SLIDE], width=0.5)
    for i, v in enumerate([p.ops_plain, p.ops_fused]):
        ax1.text(i, v + 8, f'{v} operations', ha='center', fontsize=10.5, weight='bold', color=INK)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['run layer by layer,\nas the training code does',
                         'exported and joined up\nby the runtime'], fontsize=9.5)
    ax1.set_ylim(0, p.ops_plain * 1.22)
    ax1.set_ylabel('separate pieces of work sent to the graphics processor', fontsize=9.5)
    ax1.set_title('Joining operations up removes the hand-offs',
                  fontsize=11, weight='bold')

    _plain(ax2)
    ar16 = p.arithmetic_ms('float16')
    bars = [[ar16, p.overhead_ms(False)], [ar16, p.overhead_ms(True)]]
    labels = ['layer by layer', 'exported and joined up']
    for i, (a, o) in enumerate(bars):
        ax2.bar(i, a, color=TEAL, width=0.5, label='arithmetic' if i == 0 else None)
        ax2.bar(i, o, bottom=a, color=GRIP, width=0.5,
                label='hand-off overhead' if i == 0 else None)
        ax2.text(i, a + o + 0.14, f'{a + o:.2f} ms', ha='center', fontsize=10.5,
                 weight='bold', color=INK)
        ax2.text(i, a / 2, f'{a:.2f}', ha='center', va='center', fontsize=9, color='white')
        ax2.text(i, a + o / 2, f'{o:.2f}', ha='center', va='center', fontsize=9, color='white')
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(labels, fontsize=9.5)
    ax2.set_ylim(0, (ar16 + p.overhead_ms(False)) * 1.22)
    ax2.set_ylabel('milliseconds for one forward pass', fontsize=10)
    ax2.legend(fontsize=9, frameon=False, loc='upper right')
    saved = p.overhead_ms(False) - p.overhead_ms(True)
    print(f'[p1-s3] joining operations up saves {saved:.2f} ms per forward pass, which is '
          f'{100 * saved / (ar16 + p.overhead_ms(False)):.0f}% of the layer-by-layer time')
    ax2.set_title(f'That is {saved:.2f} ms back on every decision',
                  fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'launch-overhead.svg')


def runtime_steps() -> None:
    """The four things export does to a model, each with the number it changes."""
    p = POL
    rows = [
        ('the training framework runs it',
         f'{p.arithmetic_ms("float32") + p.overhead_ms(False):.1f} ms',
         'float32, layer by layer, Python in the loop'),
        ('frozen into a graph of operations',
         f'{p.arithmetic_ms("float32") + p.overhead_ms(False):.1f} ms',
         'no Python left, so the timing stops wandering'),
        ('operations joined up by the runtime',
         f'{p.arithmetic_ms("float32") + p.overhead_ms(True):.1f} ms',
         f'{p.ops_plain} pieces of work become {p.ops_fused}'),
        ('weights rewritten at two bytes',
         f'{p.forward_ms("float16"):.1f} ms',
         f'the file drops from {p.weight_megabytes("float32"):.0f} MB '
         f'to {p.weight_megabytes("float16"):.0f} MB'),
        ('weights rewritten at one byte',
         f'{p.forward_ms("int8"):.1f} ms',
         'needs a calibration set, and accuracy has to be measured again'),
    ]
    for nm, t, note in rows:
        print(f'[p1-s3] step: {nm:40s} {t:>8s}   {note}')

    fig, ax = plt.subplots(figsize=(11.6, 5.2), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.985, 'Five steps from the training file to the file the robot runs',
            ha='center', va='top', fontsize=12.5, weight='bold', color=INK)
    cols = ['#eef3f9', '#eef3f9', '#e4f0e4', '#dff0ef', '#f6efe0']
    for i, ((nm, t, note), col) in enumerate(zip(rows, cols)):
        yy = 0.74 - i * 0.152
        _box(ax, 0.02, yy, 0.44, 0.118, nm, col, size=10)
        _box(ax, 0.48, yy, 0.12, 0.118, t, 'white', size=11.5, weight='bold')
        ax.text(0.625, yy + 0.059, note, ha='left', va='center', fontsize=9.3, color=MUTED)
    ax.text(0.54, 0.875, 'one forward pass takes', ha='center', va='bottom',
            fontsize=9.5, color=MUTED)
    _save(fig, RUN_DOC, 'runtime-steps.svg')


# ==========================================================================
# page 1, section 4: batching
# ==========================================================================

class Batching:
    """One stated example batching model, built from the numbers of section 3.

    Each call pays a fixed cost once: the joined-up hand-offs, reading the
    weights out of memory, and an example 1.2 ms of waking the graphics
    processor and waiting for it to answer. Each item in the batch then pays
    for its own arithmetic and for copying its two pictures across.
    """

    def __init__(self) -> None:
        p = POL
        self.fixed = p.overhead_ms(True) + p.memory_ms('float16') + 1.2
        self.copy_ms = 2 * 224 * 224 * 3 * 2 / 8e9 * 1000.0      # two pictures over an 8 GB/s link
        self.per_item = p.arithmetic_ms('float16') + self.copy_ms

    def time_ms(self, b: Arr | float) -> Arr | float:
        return self.fixed + self.per_item * b

    def throughput(self, b: Arr | float) -> Arr | float:
        return 1000.0 * b / self.time_ms(b)


BAT = Batching()


def throughput_vs_batch() -> None:
    """Throughput against batch size, and how little is left to win."""
    b = np.arange(1, 33)
    th = np.asarray(BAT.throughput(b))
    ceiling = 1000.0 / BAT.per_item
    print(f'[p1-s4] fixed cost {BAT.fixed:.2f} ms, per-item cost {BAT.per_item:.2f} ms '
          f'(copying two pictures takes {BAT.copy_ms:.2f} ms)')
    for bb in (1, 2, 4, 8, 16, 32):
        print(f'[p1-s4]   batch {bb:2d}: one call takes {BAT.time_ms(bb):6.1f} ms, '
              f'{BAT.throughput(bb):5.1f} decisions a second, '
              f'{BAT.throughput(bb) / BAT.throughput(1):.2f} times batch 1')
    print(f'[p1-s4] the ceiling, with the fixed cost spread over an endless batch, '
          f'is {ceiling:.1f} decisions a second')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.5), facecolor='white')
    fig.subplots_adjust(wspace=0.28)
    _plain(ax1)
    ax1.plot(b, th, color=LINK, lw=2.2, marker='o', ms=3.5)
    ax1.axhline(ceiling, color=MUTED, ls='--', lw=1.2)
    ax1.text(14, ceiling + 6, f'ceiling: {ceiling:.0f} decisions a second', fontsize=9, color=MUTED)
    for bb in (1, 4, 8, 32):
        ax1.annotate(f'{BAT.throughput(bb):.0f}', (bb, BAT.throughput(bb)),
                     textcoords='offset points', xytext=(2, -14), fontsize=9, color=INK)
    ax1.set_xlabel('batch size (decisions worked out in one call)', fontsize=10)
    ax1.set_ylabel('decisions a second', fontsize=10)
    ax1.set_ylim(0, ceiling * 1.12)
    ax1.set_title('Throughput rises and then stops', fontsize=11, weight='bold')

    _plain(ax2)
    ax2.plot(b, np.asarray(BAT.time_ms(b)), color=GRIP, lw=2.2)
    ax2.plot(b, np.asarray(BAT.time_ms(b)) / b, color=TEAL, lw=2.2)
    ax2.text(20, float(BAT.time_ms(20)) + 4, 'the whole call', fontsize=9.5, color=GRIP)
    ax2.text(14, float(BAT.time_ms(14)) / 14 + 7, 'the share of one decision',
             fontsize=9.5, color=TEAL)
    ax2.set_xlabel('batch size', fontsize=10)
    ax2.set_ylabel('milliseconds', fontsize=10)
    ax2.set_title('The work per decision barely falls', fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'throughput-vs-batch.svg')


def latency_vs_batch() -> None:
    """What waiting for the batch to fill does to one arm's deadline."""
    period_ms = 50.0
    b = np.arange(1, 17)
    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    arms_list = [1, 2, 6, 12]
    cols = [GRIP, WRIST, TEAL, LINK]
    best: dict[int, int] = {}
    for arms, col in zip(arms_list, cols):
        gap = period_ms / arms                           # ms between two requests arriving
        worst = (b - 1) * gap + np.asarray(BAT.time_ms(b))
        word = 'arm' if arms == 1 else 'arms'
        ax.plot(b, worst, color=col, lw=2.1, marker='o', ms=3.4,
                label=f'{arms} {word} at 20 Hz, sharing the machine')
        ok = b[worst <= period_ms]
        best[arms] = int(ok.max()) if len(ok) else 0
    ax.axhline(period_ms, color=INK, ls='--', lw=1.5)
    ax.text(12.2, period_ms + 3, 'the 50 ms deadline of a 20 Hz loop', fontsize=9.5, color=INK)
    ax.set_yscale('log')
    ax.set_xlabel('batch size', fontsize=10)
    ax.set_ylabel('worst time from picture to command (ms, log scale)', fontsize=10)
    ax.set_xticks(b)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Waiting for a batch to fill is paid by whichever arm asked first',
                 fontsize=12, weight='bold')
    for arms in arms_list:
        print(f'[p1-s4] {arms:2d} arms at 20 Hz: the largest batch that still meets the '
              f'50 ms deadline is {best[arms]}')
    _save(fig, RUN_DOC, 'latency-vs-batch.svg')


def batch_timeline() -> None:
    """A timeline of two arms sharing a batch of eight, which misses four deadlines."""
    arms, batch = 2, 8
    gap = 50.0 / arms
    wait = (batch - 1) * gap
    total = wait + float(BAT.time_ms(batch))
    missed = int(math.floor(total / 50.0))
    print(f'[p1-s4] two arms, batch of 8: the first arm waits {wait:.0f} ms for the batch '
          f'to fill, the call takes {BAT.time_ms(batch):.1f} ms, so its command is '
          f'{total:.1f} ms late and it has missed {missed} deadlines')

    fig, ax = plt.subplots(figsize=(11.6, 4.0), facecolor='white')
    _blank(ax)
    ax.set_xlim(-10, total + 40)
    ax.set_ylim(0, 1)
    for k in range(batch):
        t = k * gap
        ax.plot([t, t], [0.60, 0.74], color=LINK if k % 2 == 0 else TEAL, lw=2.0)
        ax.text(t, 0.76, f'{t:.0f} ms', ha='center', fontsize=8, color=MUTED)
    ax.text(-8, 0.63, 'requests\narriving', ha='right', va='center', fontsize=9.5, color=INK)
    ax.add_patch(Rectangle((0, 0.36), wait, 0.16, facecolor='#f3dede',
                           edgecolor=GRIP, lw=1.2))
    ax.text(wait / 2, 0.44, f'the first arm waits {wait:.0f} ms', ha='center', va='center',
            fontsize=10, color=INK)
    ax.add_patch(Rectangle((wait, 0.36), float(BAT.time_ms(batch)), 0.16,
                           facecolor='#dfeaf6', edgecolor=LINK, lw=1.2))
    ax.text(wait + float(BAT.time_ms(batch)) / 2, 0.44, f'{BAT.time_ms(batch):.0f} ms',
            ha='center', va='center', fontsize=9.5, color=INK)
    for k in range(1, missed + 1):
        ax.plot([50 * k, 50 * k], [0.18, 0.56], color=GRIP, ls='--', lw=1.1)
        ax.text(50 * k, 0.14, f'deadline {k}\nmissed', ha='center', va='top',
                fontsize=8.5, color=GRIP)
    ax.plot([total, total], [0.18, 0.56], color=SLIDE, lw=2.0)
    ax.text(total + 4, 0.37, f'command finally\nready at {total:.0f} ms',
            ha='left', va='center', fontsize=9.5, color=SLIDE)
    ax.text(0.5, 0.97, 'Two arms, a batch of eight, and a 20 Hz loop: four commands never arrive in time',
            transform=ax.transAxes, ha='center', va='top', fontsize=12, weight='bold', color=INK)
    _save(fig, RUN_DOC, 'batch-timeline.svg')


# ==========================================================================
# page 1, section 5: a latency budget for one arm
# ==========================================================================

BUDGET: list[tuple[str, float]] = [
    ('camera exposure', 8.0),
    ('readout and transfer', 11.0),
    ('preprocessing', 3.2),
    ('forward pass', POL.forward_ms('float16')),
    ('postprocessing', 1.1),
    ('command onto the bus', 2.0),
]
BUDGET_COLOURS: list[str] = [JOINT, WRIST, PURPLE, LINK, TEAL, SLIDE]


def latency_budget() -> None:
    """The whole budget as one bar, against the period of three control rates."""
    names = [n for n, _ in BUDGET]
    vals = [v for _, v in BUDGET]
    total = sum(vals)
    print(f'[p1-s5] budget total {total:.2f} ms')
    for n, v in BUDGET:
        print(f'[p1-s5]   {n:22s} {v:5.2f} ms  {100 * v / total:5.1f}%')
    for hz in (10, 20, 30, 50, 100):
        per = 1000.0 / hz
        print(f'[p1-s5] at {hz:3d} Hz the period is {per:6.2f} ms, which leaves '
              f'{per - total:+7.2f} ms')

    fig, ax = plt.subplots(figsize=(12.0, 4.6), facecolor='white')
    _plain(ax)
    left = 0.0
    for (n, v), c in zip(BUDGET, BUDGET_COLOURS):
        ax.barh([0], [v], left=[left], color=c, height=0.42, edgecolor='white')
        if v > 2.5:
            ax.text(left + v / 2, 0, f'{v:.1f}', ha='center', va='center', fontsize=9.5,
                    color='white', weight='bold')
        left += v
    ax.text(total + 1.5, 0, f'total {total:.1f} ms', va='center', fontsize=10.5,
            weight='bold', color=INK)
    for hz, y in ((20, 0.55), (30, 0.85), (50, 1.15)):
        per = 1000.0 / hz
        ax.plot([per, per], [-0.3, y], color=INK, ls='--', lw=1.3)
        room = per - total
        word = f'{room:+.1f} ms spare' if room > 0 else f'{-room:.1f} ms short'
        ax.text(per, y + 0.03, f'{hz} Hz: {per:.1f} ms  ({word})', ha='center', va='bottom',
                fontsize=9.5, color=SLIDE if room > 0 else GRIP)
    ax.set_yticks([])
    ax.set_ylim(-0.45, 1.5)
    ax.set_xlim(0, 56)
    ax.set_xlabel('milliseconds from the light hitting the sensor to the command leaving', fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in BUDGET_COLOURS]
    ax.legend(handles, [f'{n} ({v:.1f} ms)' for n, v in BUDGET], fontsize=9,
              frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(0.5, -0.55))
    ax.set_title('One 20 Hz loop, end to end, on the example machine',
                 fontsize=12.5, weight='bold')
    _save(fig, RUN_DOC, 'latency-budget.svg')


def where_the_time_goes() -> None:
    """The share of the loop each stage takes, with the camera and the model grouped."""
    names = [n for n, _ in BUDGET]
    vals = np.array([v for _, v in BUDGET])
    total = float(vals.sum())
    camera = vals[0] + vals[1]
    software = total - camera
    print(f'[p1-s5] the camera takes {camera:.1f} ms, {100 * camera / total:.1f}% of the loop; '
          f'the model takes {vals[3]:.2f} ms, {100 * vals[3] / total:.1f}%')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.5), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.3, 1.0]})
    _plain(ax1)
    y = np.arange(len(names))[::-1]
    ax1.barh(y, 100 * vals / total, color=BUDGET_COLOURS, height=0.55)
    for yy, v in zip(y, vals):
        ax1.text(100 * v / total + 0.9, yy, f'{100 * v / total:.1f}%  ({v:.1f} ms)',
                 va='center', fontsize=9.5, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=9.5)
    ax1.set_xlim(0, 48)
    ax1.set_xlabel('share of the 30 ms loop (%)', fontsize=10)
    ax1.set_title('The network is the fourth biggest cost', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [camera, software], color=[JOINT, LINK], width=0.5)
    for i, v in enumerate([camera, software]):
        ax2.text(i, v + 0.5, f'{v:.1f} ms\n{100 * v / total:.0f}%', ha='center',
                 fontsize=10.5, weight='bold', color=INK)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['getting the picture\nout of the camera',
                         'everything your code does\nwith it'], fontsize=9.5)
    ax2.set_ylim(0, camera * 1.3)
    ax2.set_ylabel('milliseconds', fontsize=10)
    ax2.set_title('Where to look first for time', fontsize=11.5, weight='bold')
    _save(fig, RUN_DOC, 'where-the-time-goes.svg')


def action_chunk_timeline() -> None:
    """How a chunk of commands buys the model time, and what it costs in freshness."""
    chunk, replan, hz = 16, 8, 20
    step_ms = 1000.0 / hz
    chunk_ms = chunk * step_ms
    replan_ms = replan * step_ms
    loop = sum(v for _, v in BUDGET)
    calls = 1000.0 / replan_ms
    share = 100 * loop / replan_ms
    staleness = loop + replan_ms
    print(f'[p1-s5] a chunk of {chunk} commands at {hz} Hz covers {chunk_ms:.0f} ms of motion; '
          f're-planning every {replan} commands means {calls:.1f} model calls a second, '
          f'{share:.1f}% of the time, and the oldest command acted on was worked out '
          f'from a picture {staleness:.0f} ms before it is used')

    fig, ax = plt.subplots(figsize=(12.0, 4.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(-120, 1760)
    ax.set_ylim(0, 1)
    for k in range(33):
        t = k * step_ms
        ax.plot([t, t], [0.20, 0.30], color=GRID, lw=1.0)
    ax.text(-20, 0.25, '20 Hz\ncommands', ha='right', va='center', fontsize=9, color=MUTED)
    for i, start in enumerate((0.0, replan_ms, 2 * replan_ms)):
        col = [LINK_PALE, '#dff0ef', '#f6efe0'][i]
        edge = [LINK, TEAL, WRIST][i]
        ax.add_patch(Rectangle((start, 0.36 + i * 0.17), chunk_ms, 0.13,
                               facecolor=col, edgecolor=edge, lw=1.2))
        ax.text(start + chunk_ms / 2, 0.425 + i * 0.17,
                f'chunk {i + 1}: {chunk} commands, {chunk_ms:.0f} ms of motion',
                ha='center', va='center', fontsize=9.5, color=INK)
        ax.add_patch(Rectangle((start - loop, 0.36 + i * 0.17), loop, 0.13,
                               facecolor=GRIP, edgecolor=GRIP))
        if i == 0:
            ax.text(start - loop - 10, 0.425, f'{loop:.0f} ms\nof work', ha='right',
                    va='center', fontsize=9, color=GRIP)
        ax.plot([start + replan_ms, start + replan_ms], [0.33, 0.36 + i * 0.17],
                color=edge, ls='--', lw=1.0)
    ax.text(0.5, 0.98,
            f'Re-planning every {replan} commands: the model runs {calls:.1f} times a second '
            f'and uses {share:.0f}% of the machine',
            transform=ax.transAxes, ha='center', va='top', fontsize=12, weight='bold', color=INK)
    ax.text(0.5, 0.06, f'Only the first {replan} commands of each chunk are ever sent, '
                       f'so the arm never acts on a command older than {staleness:.0f} ms.',
            transform=ax.transAxes, ha='center', va='bottom', fontsize=10, color=MUTED)
    _save(fig, RUN_DOC, 'action-chunk-timeline.svg')


# ==========================================================================
# page 1, section 6: evaluating honestly
# ==========================================================================

EP_STEPS: int = 40
EP_TOL: float = 11.0        # millimetres the gripper may stray before the grasp misses
EP_JUMP: float = 20.0       # size of a rare large mistake, in millimetres
EP_DECAY: float = 0.6       # how much of last step's position error the arm carries over


def run_episodes(rng: np.random.Generator, n: int, sigma: float, tail: float,
                 bias: float = 0.0, rho: float = 0.0) -> tuple[int, float]:
    """Simulate n episodes of a policy and return the successes and the training loss.

    Each step the policy makes a position mistake. The arm corrects part of the
    error it already has and keeps the rest, so the error follows the mistakes
    with a lag, and the grasp succeeds only if the error never leaves the
    tolerance. The loss the trainer sees is the average squared mistake.
    """
    noise = rng.normal(0.0, sigma, size=(n, EP_STEPS))
    if rho > 0.0:
        for t in range(1, EP_STEPS):
            noise[:, t] += rho * noise[:, t - 1]
    jumps = (rng.random((n, EP_STEPS)) < tail) * rng.normal(0.0, EP_JUMP, size=(n, EP_STEPS))
    err = noise + jumps + bias
    pos = np.empty_like(err)
    pos[:, 0] = err[:, 0]
    for t in range(1, EP_STEPS):
        pos[:, t] = EP_DECAY * pos[:, t - 1] + err[:, t]
    ok = int((np.abs(pos).max(axis=1) < EP_TOL).sum())
    return ok, float((err ** 2).mean())


def loss_not_success() -> None:
    """Many policies, their training loss and their measured success rate."""
    rng = np.random.default_rng(31)
    n_pol, n_ep = 180, 600
    loss, rate, sig, tl = [], [], [], []
    for _ in range(n_pol):
        s = rng.uniform(0.3, 3.2)
        t = rng.uniform(0.0, 0.022)
        ok, ls = run_episodes(rng, n_ep, s, t)
        loss.append(ls)
        rate.append(ok / n_ep)
        sig.append(s)
        tl.append(t)
    loss = np.array(loss)
    rate = np.array(rate)
    corr = float(np.corrcoef(loss, rate)[0, 1])
    gap, pair = 0.0, (0, 0)
    for i in range(n_pol):
        for j in range(i + 1, n_pol):
            if abs(loss[i] - loss[j]) <= 0.02 * max(loss[i], loss[j]):
                d = abs(rate[i] - rate[j])
                if d > gap:
                    gap, pair = d, (i, j)
    a, b = pair
    if rate[a] > rate[b]:
        a, b = b, a
    print(f'[p1-s6] {n_pol} simulated policies: the straight-line agreement between loss '
          f'and success rate is {corr:.2f}')
    print(f'[p1-s6] two policies with the same loss: {loss[a]:.2f} and {loss[b]:.2f} '
          f'square millimetres, succeeding {100 * rate[a]:.0f}% and {100 * rate[b]:.0f}% '
          f'of the time (the worse one makes a big mistake on '
          f'{100 * tl[a]:.1f}% of steps, the better one on {100 * tl[b]:.1f}%)')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    sc = ax.scatter(loss, 100 * rate, c=100 * np.array(tl), cmap='viridis', s=34,
                    edgecolor='white', linewidth=0.4)
    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label('how often the policy makes one big mistake (% of steps)', fontsize=9)
    cb.ax.tick_params(labelsize=8.5)
    for idx, mark in ((a, 'o'), (b, 'o')):
        ax.scatter([loss[idx]], [100 * rate[idx]], facecolor='none', edgecolor=GRIP,
                   s=190, linewidth=2.0, marker=mark, zorder=5)
    ax.plot([loss[a], loss[b]], [100 * rate[a], 100 * rate[b]], color=GRIP, lw=1.4, ls='--')
    ax.annotate(f'same loss ({loss[a]:.1f}), {100 * rate[a]:.0f}% success',
                (loss[a], 100 * rate[a]), textcoords='offset points', xytext=(17, -4),
                fontsize=9.5, color=GRIP)
    ax.annotate(f'same loss ({loss[b]:.1f}), {100 * rate[b]:.0f}% success',
                (loss[b], 100 * rate[b]), textcoords='offset points', xytext=(17, 2),
                fontsize=9.5, color=GRIP)
    ax.set_xlabel('training loss: average squared mistake per step (square millimetres)', fontsize=10)
    ax.set_ylabel('success rate over 600 simulated episodes (%)', fontsize=10)
    ax.set_title('A loss number does not fix a success rate: these two agree only loosely',
                 fontsize=12, weight='bold')
    _save(fig, RUN_DOC, 'loss-not-success.svg')


def trial_positions() -> None:
    """Where the training examples were, and where the trials should be."""
    rng = np.random.default_rng(41)
    train = np.stack([rng.uniform(-12, 12, 140), rng.uniform(16, 34, 140)], axis=1)
    xs = np.linspace(-17.5, 17.5, 8)
    ys = np.linspace(12.5, 37.5, 6)
    per_cell = 12
    grid = np.zeros((len(ys), len(xs)))
    inside_ok = inside_n = outside_ok = outside_n = 0
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            d = float(np.min(np.hypot(train[:, 0] - x, train[:, 1] - y)))
            p = 0.93 * math.exp(-(d / 5.5) ** 2) + 0.02
            ok = int((rng.random(per_cell) < p).sum())
            grid[i, j] = ok / per_cell
            if -12 <= x <= 12 and 16 <= y <= 34:
                inside_ok += ok
                inside_n += per_cell
            else:
                outside_ok += ok
                outside_n += per_cell
    lo_i, hi_i = cp_interval(inside_ok, inside_n)
    lo_o, hi_o = cp_interval(outside_ok, outside_n)
    print(f'[p1-s6] trials inside the training box: {inside_ok} of {inside_n} = '
          f'{100 * inside_ok / inside_n:.0f}% (95% interval {100 * lo_i:.0f}% to {100 * hi_i:.0f}%)')
    print(f'[p1-s6] trials outside it: {outside_ok} of {outside_n} = '
          f'{100 * outside_ok / outside_n:.0f}% (95% interval {100 * lo_o:.0f}% to '
          f'{100 * hi_o:.0f}%)')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.2), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.3, 0.75]})
    fig.subplots_adjust(wspace=0.55)
    im = ax1.imshow(100 * grid, origin='lower', extent=(-20, 20, 10, 40), cmap='RdYlGn',
                    vmin=0, vmax=100, aspect='auto')
    ax1.scatter(train[:, 0], train[:, 1], s=9, color=INK, alpha=0.65,
                label='where the 140 demonstrations put the object')
    ax1.add_patch(Rectangle((-12, 16), 24, 18, facecolor='none', edgecolor=INK,
                            lw=1.8, ls='--'))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            ax1.text(x, y, f'{100 * grid[i, j]:.0f}', ha='center', va='center', fontsize=8,
                     color=INK)
    ax1.set_xlabel('across the table (cm from the middle)', fontsize=10)
    ax1.set_ylabel('away from the arm (cm)', fontsize=10)
    ax1.tick_params(labelsize=9)
    ax1.legend(fontsize=8.5, frameon=False, loc='upper center',
               bbox_to_anchor=(0.5, -0.14))
    cb = fig.colorbar(im, ax=ax1, fraction=0.045, pad=0.02)
    cb.set_label('successes out of 12 trials, as a percentage', fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    ax1.set_title('48 cells, 12 trials each, on simulated data', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [100 * inside_ok / inside_n, 100 * outside_ok / outside_n],
            color=[SLIDE, GRIP], width=0.5)
    ax2.errorbar([0, 1], [100 * inside_ok / inside_n, 100 * outside_ok / outside_n],
                 yerr=[[100 * (inside_ok / inside_n - lo_i), 100 * (outside_ok / outside_n - lo_o)],
                       [100 * (hi_i - inside_ok / inside_n), 100 * (hi_o - outside_ok / outside_n)]],
                 fmt='none', ecolor=INK, capsize=6, lw=1.4)
    for i, v in enumerate([100 * inside_ok / inside_n, 100 * outside_ok / outside_n]):
        ax2.text(i, v + 7, f'{v:.0f}%', ha='center', fontsize=12, weight='bold', color=INK)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels([f'inside the dashed box\n({inside_n} trials)',
                         f'outside it\n({outside_n} trials)'], fontsize=9.5)
    ax2.set_ylim(0, 108)
    ax2.set_ylabel('success rate (%)', fontsize=10)
    ax2.set_title('A trial list that stays inside the box\nflatters the policy',
                  fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'trial-positions.svg')


def trials_and_intervals() -> None:
    """How wide a success rate really is, and how many trials it takes to tell two apart."""
    counts = [10, 20, 50, 100, 200, 500]
    rows = []
    for n in counts:
        for p, col in ((0.70, WRIST), (0.90, LINK)):
            x = int(round(p * n))
            lo, hi = cp_interval(x, n)
            rows.append((n, p, x, lo, hi, col))
            print(f'[p1-s6] {x:3d} of {n:3d} = {100 * x / n:.0f}%  '
                  f'95% interval {100 * lo:.1f}% to {100 * hi:.1f}%  '
                  f'(width {100 * (hi - lo):.1f} points)')

    ns = [10, 20, 30, 40, 50, 60, 80, 100, 120, 160, 200]
    sep = [separation_chance(n, 0.70, 0.90) for n in ns]
    for n, s in zip(ns, sep):
        print(f'[p1-s6] with {n:3d} trials each, two 95% intervals separate '
              f'{100 * s:.0f} times in 100')
    first = next((n for n, s in zip(ns, sep) if s >= 0.80), None)
    print(f'[p1-s6] the first trial count in that list with an 80% chance of separating '
          f'is {first}')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.15, 1.0]})
    _plain(ax1)
    for i, n in enumerate(counts):
        for k, (p, col) in enumerate(((0.70, WRIST), (0.90, LINK))):
            x = int(round(p * n))
            lo, hi = cp_interval(x, n)
            y = i * 2 + (0.34 if k else -0.34)
            ax1.plot([100 * lo, 100 * hi], [y, y], color=col, lw=4.0, solid_capstyle='butt')
            ax1.scatter([100 * x / n], [y], color=INK, s=16, zorder=4)
            ax1.text(101, y, f'{100 * (hi - lo):.0f} pts wide', va='center', fontsize=8.5,
                     color=col)
    ax1.set_yticks([i * 2 for i in range(len(counts))])
    ax1.set_yticklabels([f'{n} trials' for n in counts], fontsize=9.5)
    ax1.set_xlim(30, 118)
    ax1.set_xticks([40, 50, 60, 70, 80, 90, 100])
    ax1.set_xlabel('true success rate the trials are consistent with (%)', fontsize=10)
    ax1.plot([], [], color=WRIST, lw=4, label='a policy that scored 70%')
    ax1.plot([], [], color=LINK, lw=4, label='a policy that scored 90%')
    ax1.legend(fontsize=9, frameon=False, loc='upper center', ncol=2,
               bbox_to_anchor=(0.5, -0.17))
    ax1.set_title('Exact 95% intervals for the same two scores', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.plot(ns, [100 * s for s in sep], color=PURPLE, lw=2.3, marker='o', ms=4)
    ax2.axhline(80, color=MUTED, ls='--', lw=1.2)
    ax2.text(14, 83, 'eight times in ten', fontsize=9, color=MUTED)
    for n in (20, 60, 120):
        s = sep[ns.index(n)]
        ax2.annotate(f'{100 * s:.0f}%', (n, 100 * s), textcoords='offset points',
                     xytext=(6, -16), fontsize=9.5, color=INK)
    ax2.set_xlabel('trials run on each of the two policies', fontsize=10)
    ax2.set_ylabel('chance the two intervals do not overlap (%)', fontsize=10)
    ax2.set_ylim(0, 105)
    ax2.set_title('A policy that is truly 70% against one that is truly 90%',
                  fontsize=11.5, weight='bold')
    _save(fig, RUN_DOC, 'trials-and-intervals.svg')


ABLATIONS: list[tuple[str, dict[str, float]]] = [
    ('everything on', {'sigma': 1.40, 'tail': 0.004}),
    ('wrist camera removed', {'sigma': 3.10, 'tail': 0.008}),
    ('joint readings removed', {'sigma': 1.40, 'tail': 0.004, 'bias': 2.6}),
    ('one command at a time', {'sigma': 1.40, 'tail': 0.004, 'rho': 0.80}),
]


def ablation_bars() -> None:
    """Four versions of the same policy, 80 trials each, with their intervals."""
    rng = np.random.default_rng(53)
    n = 80
    res = []
    for name, kw in ABLATIONS:
        ok, loss = run_episodes(rng, n, **kw)   # type: ignore[arg-type]
        lo, hi = cp_interval(ok, n)
        res.append((name, ok, lo, hi, loss))
        print(f'[p1-s6] ablation {name:24s} {ok:2d} of {n} = {100 * ok / n:.0f}%  '
              f'95% interval {100 * lo:.0f}% to {100 * hi:.0f}%  '
              f'loss {loss:.2f} square mm')

    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(res))
    rates = [100 * r[1] / n for r in res]
    ax.bar(x, rates, color=[SLIDE, GRIP, WRIST, PURPLE], width=0.55)
    ax.errorbar(x, rates,
                yerr=[[r - 100 * res[i][2] for i, r in enumerate(rates)],
                      [100 * res[i][3] - r for i, r in enumerate(rates)]],
                fmt='none', ecolor=INK, capsize=7, lw=1.5)
    for i, r in enumerate(rates):
        ax.text(i, 100 * res[i][3] + 2.5, f'{r:.0f}%', ha='center', fontsize=11.5,
                weight='bold', color=INK)
        ax.text(i, 7, f'training loss {res[i][4]:.1f}', ha='center', fontsize=9,
                color='white')
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in res], fontsize=9.5)
    ax.set_ylim(0, 112)
    ax.set_ylabel(f'successes in {n} simulated trials (%), with the 95% interval', fontsize=10)
    ax.set_title('Taking one part away at a time, on simulated episodes',
                 fontsize=12, weight='bold')
    ax.text(0.5, -0.17, 'The last three intervals all overlap, so 80 trials cannot order '
                        'them, and the training loss does not order them either.',
            transform=ax.transAxes, ha='center', fontsize=9.5, color=MUTED)
    _save(fig, RUN_DOC, 'ablation-bars.svg')


def out_of_distribution() -> None:
    """The colour model of section 2, measured under four conditions it did not train on."""
    conds = [
        ('as trained', dict(light=1.0, tint=None, noise=0.045)),
        ('light 45% brighter', dict(light=1.45, tint=None, noise=0.045)),
        ('a warmer tablecloth', dict(light=1.0, tint=np.array([0.10, 0.05, -0.05]),
                                     noise=0.045)),
        ('a noisier camera', dict(light=1.0, tint=None, noise=0.11)),
    ]
    n = 2000
    res = []
    for i, (name, kw) in enumerate(conds):
        x, y = make_objects(n, np.random.default_rng(90 + i), **kw)  # type: ignore[arg-type]
        acc = COL.accuracy_with(COL.mean, COL.std, x, y)
        ok = int(round(acc * n))
        lo, hi = cp_interval(ok, n)
        res.append((name, acc, lo, hi))
        print(f'[p1-s6] out of distribution: {name:22s} {100 * acc:.1f}%  '
              f'95% interval {100 * lo:.1f}% to {100 * hi:.1f}%')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.0]})
    _plain(ax1)
    x = np.arange(len(res))
    rates = [100 * r[1] for r in res]
    ax1.bar(x, rates, color=[SLIDE, WRIST, GRIP, PURPLE], width=0.55)
    ax1.errorbar(x, rates,
                 yerr=[[r - 100 * res[i][2] for i, r in enumerate(rates)],
                       [100 * res[i][3] - r for i, r in enumerate(rates)]],
                 fmt='none', ecolor=INK, capsize=6, lw=1.3)
    for i, r in enumerate(rates):
        ax1.text(i, r + 3.5, f'{r:.1f}%', ha='center', fontsize=10.5, weight='bold', color=INK)
    ax1.set_xticks(x)
    ax1.set_xticklabels([r[0] for r in res], fontsize=9, rotation=12, ha='right')
    ax1.set_ylim(0, 112)
    ax1.set_ylabel('accuracy on 2,000 objects (%)', fontsize=10)
    ax1.set_title('The same weights, four conditions', fontsize=11.5, weight='bold')

    _plain(ax2)
    lights = np.linspace(0.6, 1.8, 25)
    accs = []
    for i, lg in enumerate(lights):
        xx, yy = make_objects(1500, np.random.default_rng(300 + i), light=float(lg))
        accs.append(100 * COL.accuracy_with(COL.mean, COL.std, xx, yy))
    ax2.plot(lights, accs, color=LINK, lw=2.2)
    ax2.axvspan(0.95, 1.05, color=LINK_PALE, alpha=0.7)
    ax2.text(1.0, 20, 'the light the model\nwas trained under', ha='center', fontsize=9,
             color=LINK)
    ax2.set_xlabel('brightness of the light, as a multiple of the trained one', fontsize=10)
    ax2.set_ylabel('accuracy (%)', fontsize=10)
    ax2.set_ylim(10, 102)
    ax2.set_title('Accuracy falls away on both sides', fontsize=11.5, weight='bold')
    print('[p1-s6] accuracy against brightness: '
          + '  '.join(f'{lg:.2f}x:{a:.0f}%' for lg, a in zip(lights, accs) if
                      abs(lg - round(lg * 5) / 5) < 1e-9))
    _save(fig, RUN_DOC, 'out-of-distribution.svg')


# ==========================================================================
# page 1, section 7: reading a failure, and the safety layer
# ==========================================================================

def failure_triage() -> None:
    """Three logged episodes, each with a different kind of fault in the numbers."""
    rng = np.random.default_rng(61)
    hz = 20.0
    t = np.arange(48) / hz
    conf = np.where(t < 1.0, 0.91, 0.18) + rng.normal(0, 0.02, len(t))
    target = np.where(t < 1.0, 18.0 + 2 * t, 18.0 + 2 * 1.0 + rng.normal(0, 9.0, len(t)))
    cmd_a = np.clip(np.cumsum(np.where(t < 1.0, 0.5, 0.0)), 0, None)

    base = 20.0 * np.sin(2 * np.pi * 0.35 * t)
    chatter = np.where(t < 0.8, 0.0, 11.0 * np.sin(2 * np.pi * 4.0 * t) * (t - 0.8) / 1.6)
    cmd_b = base + chatter

    cmd_c = 24.0 * t
    meas_c = cmd_c.copy()
    stall = t >= 1.2
    meas_c[stall] = cmd_c[np.argmax(stall)]
    meas_c += rng.normal(0, 0.12, len(t))
    track = np.abs(cmd_c - meas_c)
    thresh = 3.0
    crossed = t[np.argmax(track > thresh)]

    print(f'[p1-s7] perception failure: the detector score falls from '
          f'{conf[:20].mean():.2f} to {conf[25:].mean():.2f} at 1.0 s, and the target '
          f'the policy was given then jumps by up to {np.abs(np.diff(target[20:])).max():.0f} mm')
    print(f'[p1-s7] policy failure: the command shakes at 4.0 Hz, growing to '
          f'{np.abs(chatter).max():.1f} degrees, while nothing else in the log changes')
    print(f'[p1-s7] hardware failure: the measured joint stops at '
          f'{meas_c[-1]:.1f} degrees while the command reaches {cmd_c[-1]:.1f}, so the '
          f'tracking error passes {thresh:.0f} degrees at {crossed:.2f} s and peaks at '
          f'{track.max():.1f}')

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.3), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(t, conf, color=PURPLE, lw=2.0, label='detector score')
    ax.plot(t, target / 40.0, color=WRIST, lw=2.0, label='target position / 40')
    ax.axvline(1.0, color=GRIP, ls='--', lw=1.3)
    ax.text(1.05, 1.26, 'the box is lost', fontsize=9, color=GRIP)
    ax.set_ylim(-0.1, 1.38)
    ax.set_xlabel('seconds into the episode', fontsize=9.5)
    ax.set_ylabel('score, and scaled target', fontsize=9.5)
    ax.legend(fontsize=8.5, frameon=False, loc='lower left')
    ax.set_title('Perception failed:\nthe score collapsed first', fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    ax.plot(t, cmd_b, color=LINK, lw=2.0, label='commanded joint 2')
    ax.plot(t, base, color=GRID, lw=1.6, ls='--', label='what a steady policy would send')
    ax.set_xlabel('seconds into the episode', fontsize=9.5)
    ax.set_ylabel('degrees', fontsize=9.5)
    ax.legend(fontsize=8.5, frameon=False, loc='lower left')
    ax.set_title('The policy failed:\nthe command shook, the score did not',
                 fontsize=11, weight='bold')

    ax = axes[2]
    _plain(ax)
    ax.plot(t, cmd_c, color=LINK, lw=2.0, label='commanded joint 4')
    ax.plot(t, meas_c, color=GRIP, lw=2.0, label='measured joint 4')
    ax.fill_between(t, cmd_c, meas_c, color='#f3dede', alpha=0.8)
    ax.axvline(crossed, color=INK, ls='--', lw=1.2)
    ax.text(0.06, 48, f'{thresh:.0f} degrees of error\nat {crossed:.2f} s',
            ha='left', va='top', fontsize=9, color=INK)
    ax.set_xlabel('seconds into the episode', fontsize=9.5)
    ax.set_ylabel('degrees', fontsize=9.5)
    ax.legend(fontsize=8.5, frameon=False, loc='lower right')
    ax.set_title('The hardware failed:\nthe joint stopped following',
                 fontsize=11, weight='bold')
    fig.suptitle('Three simulated episodes that all look the same from outside the robot',
                 fontsize=12.5, weight='bold', y=1.04)
    _save(fig, RUN_DOC, 'failure-triage.svg')


LOG_STREAMS: list[tuple[str, float, int, bool]] = [
    # name, samples a second, bytes a sample, kept on every trial
    ('joint positions, speeds and torques', 500.0, 21 * 4, True),
    ('commands sent to the arm', 20.0, 7 * 4, True),
    ('what the model gave back', 20.0, 16 * 7 * 4, True),
    ('the detector score and box', 20.0, 5 * 4, True),
    ('wrist camera, compressed', 30.0, 60_000, True),
    ('scene camera, compressed', 30.0, 60_000, True),
    ('the exact numbers fed to the network', 20.0, 2 * 224 * 224 * 3 * 2, False),
]


def what_to_log() -> None:
    """What one twelve-second trial costs to record, stream by stream."""
    secs = 12.0
    trials = 100
    rows = [(nm, rate, size, keep, rate * size * secs / 1e6) for nm, rate, size, keep in LOG_STREAMS]
    always = sum(r[4] for r in rows if r[3])
    extra = sum(r[4] for r in rows if not r[3])
    print(f'[p1-s7] a {secs:.0f} second trial: the streams kept every time come to '
          f'{always:.1f} MB, and {trials} trials come to {always * trials / 1000:.2f} GB')
    print(f'[p1-s7] the preprocessed network input alone would add {extra:.1f} MB a trial, '
          f'which is {extra / always:.1f} times everything else')
    for nm, rate, size, keep, mb in rows:
        print(f'[p1-s7]   {nm:38s} {rate:5.0f} Hz x {size:7,} bytes = {mb:7.2f} MB')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.45, 0.75]})
    _plain(ax1)
    y = np.arange(len(rows))[::-1]
    cols = [SLIDE if r[3] else GRIP for r in rows]
    ax1.barh(y, [r[4] for r in rows], color=cols, height=0.55)
    ax1.set_xscale('log')
    for yy, r in zip(y, rows):
        txt = f'{r[4]:.3f} MB' if r[4] < 0.01 else f'{r[4]:.2f} MB'
        ax1.text(r[4] * 1.25, yy, f'{txt}   ({r[1]:.0f} Hz)', va='center',
                 fontsize=9, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax1.set_xlim(1e-3, 1e4)
    ax1.set_xlabel('megabytes written in one 12 second trial (log scale)', fontsize=10)
    ax1.set_title('What one trial costs to record', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [always, always + extra], color=[SLIDE, GRIP], width=0.5)
    for i, v in enumerate([always, always + extra]):
        ax2.text(i, v + 12, f'{v:.0f} MB', ha='center', fontsize=11, weight='bold', color=INK)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['everything except the\nnetwork input',
                         'with the network\ninput as well'], fontsize=9.5)
    ax2.set_ylim(0, (always + extra) * 1.22)
    ax2.set_ylabel('megabytes per trial', fontsize=10)
    ax2.set_title(f'{trials} trials: {always * trials / 1000:.1f} GB '
                  f'against {(always + extra) * trials / 1000:.1f} GB',
                  fontsize=11, weight='bold')
    _save(fig, RUN_DOC, 'what-to-log.svg')


def safety_layer() -> None:
    """The clamp and the watchdog, both outside the model, on simulated commands."""
    rng = np.random.default_rng(71)
    hz = 20.0
    n = 60
    t = np.arange(n) / hz
    want = 120.0 + 40.0 * np.sin(2 * np.pi * 0.25 * t) + rng.normal(0, 0.8, n)
    want[28:33] += 55.0                     # the policy asks for a jump
    limit_hi, limit_lo = 170.0, -170.0
    vel_limit = 90.0                        # degrees a second
    step_limit = vel_limit / hz
    safe = np.empty(n)
    safe[0] = want[0]
    for k in range(1, n):
        step = np.clip(want[k] - safe[k - 1], -step_limit, step_limit)
        safe[k] = np.clip(safe[k - 1] + step, limit_lo, limit_hi)
    v_want = np.abs(np.diff(want)) * hz
    v_safe = np.abs(np.diff(safe)) * hz
    breaks = int((v_want > vel_limit).sum())
    print(f'[p1-s7] the policy asked for a speed above {vel_limit:.0f} degrees a second on '
          f'{breaks} of {n - 1} steps, peaking at {v_want.max():.0f}; after the clamp the '
          f'peak is {v_safe.max():.0f} and the largest command change is '
          f'{step_limit:.1f} degrees')
    period, timeout, stall = 50.0, 120.0, 300.0
    fires = timeout
    print(f'[p1-s7] commands every {period:.0f} ms, a watchdog that waits {timeout:.0f} ms: '
          f'a {stall:.0f} ms gap is caught after {fires:.0f} ms, which is '
          f'{fires / period:.1f} missed commands, and the brake goes on '
          f'{stall - fires:.0f} ms before the model recovers')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.7), facecolor='white')
    _plain(ax1)
    ax1.plot(t, want, color=GRIP, lw=1.9, label='what the model asked for')
    ax1.plot(t, safe, color=SLIDE, lw=2.2, label='what the clamp let through')
    ax1.axhline(limit_hi, color=INK, ls='--', lw=1.2)
    ax1.text(0.05, limit_hi + 3, f'joint limit {limit_hi:.0f} degrees', fontsize=9, color=INK)
    ax1.set_xlabel('seconds', fontsize=10)
    ax1.set_ylabel('joint 2 command (degrees)', fontsize=10)
    ax1.set_ylim(60, 235)
    ax1.legend(fontsize=9, frameon=False, loc='lower left')
    ax1.set_title(f'The clamp caught {breaks} commands that were too fast',
                  fontsize=11.5, weight='bold')

    _blank(ax2)
    ax2.set_xlim(-130, 760)
    ax2.set_ylim(0, 1)
    for k in range(5):
        x = k * period
        ax2.plot([x, x], [0.70, 0.86], color=LINK, lw=2.6)
        ax2.text(x, 0.88, f'{x:.0f}', ha='center', va='bottom', fontsize=8, color=MUTED)
    ax2.text(-16, 0.78, 'commands\narriving every\n50 ms', ha='right', va='center',
             fontsize=9, color=INK)
    gap_start = 4 * period
    ax2.add_patch(Rectangle((gap_start, 0.44), stall, 0.16, facecolor='#f3dede',
                            edgecolor=GRIP, lw=1.2))
    ax2.text(gap_start + stall - 12, 0.62, f'nothing arrives for {stall:.0f} ms',
             ha='right', va='bottom', fontsize=10, color=INK)
    ax2.plot([gap_start + timeout, gap_start + timeout], [0.20, 0.45], color=INK, lw=1.8)
    ax2.text(gap_start + timeout, 0.17,
             f'the watchdog fires\n{timeout:.0f} ms into the gap\nand the arm brakes',
             ha='center', va='top', fontsize=9.5, color=INK)
    ax2.plot([gap_start + stall, gap_start + stall], [0.40, 0.90], color=SLIDE, lw=2.6)
    ax2.text(gap_start + stall + 14, 0.52, 'the model\ncatches up', ha='left', va='center',
             fontsize=9.5, color=SLIDE)
    ax2.set_title('The watchdog does not know why the command is late',
                  fontsize=11.5, weight='bold')
    _save(fig, RUN_DOC, 'safety-layer.svg')




# ==========================================================================
# page 2, section 1: one map of the whole book
# ==========================================================================

CHAPTERS: list[tuple[int, str, int]] = [
    (1, 'What learning from data means', 2),
    (2, 'Inside a neural network', 4),
    (3, 'How training works', 4),
    (4, 'Making training work', 2),
    (5, 'Turning the world into numbers', 2),
    (6, 'The transformer', 4),
    (7, 'Pretraining and adapting', 4),
    (8, 'Models that generate', 2),
    (9, 'Models that see', 4),
    (10, 'Language and multimodal models', 4),
    (11, 'Learning from outcomes', 2),
    (12, 'Models that act', 4),
    (13, 'Using a model for real', 2),
]

SHORT: dict[int, str] = {
    1: 'What learning means', 2: 'Inside a network', 3: 'How training works',
    4: 'Making training work', 5: 'The world as numbers', 6: 'The transformer',
    7: 'Pretraining and adapting', 8: 'Models that generate', 9: 'Models that see',
    10: 'Language and multimodal', 11: 'Learning from outcomes', 12: 'Models that act',
    13: 'Using a model for real',
}

NEEDS: list[tuple[int, int]] = [
    (1, 2), (2, 3), (3, 4), (2, 5), (5, 6), (4, 6), (6, 7), (3, 8),
    (6, 9), (5, 9), (6, 10), (9, 10), (3, 11), (7, 12), (8, 12),
    (9, 12), (10, 12), (11, 12), (12, 13), (7, 13),
]


def _depths() -> dict[int, int]:
    depth = {c: 1 for c, _, _ in CHAPTERS}
    for _ in range(len(CHAPTERS)):
        for a, b in NEEDS:
            depth[b] = max(depth[b], depth[a] + 1)
    return depth


def book_map() -> None:
    """Every chapter of the book, with the chapters each one needs first."""
    depth = _depths()
    pages = {c: p for c, _, p in CHAPTERS}
    names = {c: n for c, n, _ in CHAPTERS}
    total = sum(pages.values())
    levels: dict[int, list[int]] = {}
    for c in sorted(depth, key=lambda k: (depth[k], k)):
        levels.setdefault(depth[c], []).append(c)
    print(f'[p2-s1] {len(CHAPTERS)} chapters and {total} pages, in '
          f'{max(depth.values())} levels of the reading order')
    for lv in sorted(levels):
        print(f'[p2-s1]   level {lv}: ' + ', '.join(f'{c} {names[c]}' for c in levels[lv]))

    pos: dict[int, tuple[float, float]] = {}
    for lv, members in levels.items():
        for k, c in enumerate(members):
            y = 0.5 if len(members) == 1 else 0.5 + (k - (len(members) - 1) / 2) * 0.295
            pos[c] = ((lv - 0.5) / max(levels), y)

    fig, ax = plt.subplots(figsize=(15.0, 7.0), facecolor='white')
    _blank(ax)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(0.02, 0.98)
    bw, bh = 0.098, 0.215
    for a, b in NEEDS:
        xa, ya = pos[a]
        xb, yb = pos[b]
        _arrow(ax, xa + bw / 2, ya, xb - bw / 2, yb, '#8fb8dd', 1.3)
    groups = {1: '#eef3f9', 2: '#eef3f9', 3: '#eef3f9', 4: '#eef3f9',
              5: '#e4f0e4', 6: '#e4f0e4', 7: '#e4f0e4',
              8: '#f6efe0', 9: '#f6efe0', 10: '#f6efe0', 11: '#f6efe0', 12: '#f6efe0',
              13: '#f3dede'}
    for c, (x, y) in pos.items():
        _box(ax, x - bw / 2, y - bh / 2, bw, bh, '', groups[c])
        ax.text(x, y + 0.062, f'{c}', ha='center', va='center', fontsize=12.5,
                weight='bold', color=INK)
        ax.text(x, y - 0.005, _wrap(SHORT[c], 13), ha='center', va='center', fontsize=7.6,
                color=INK, linespacing=1.35)
        ax.text(x, y - 0.078, f'{pages[c]} pages', ha='center', va='center',
                fontsize=7.4, color=MUTED)
    ax.text(0.5, 0.975, f'The whole book: {len(CHAPTERS)} chapters, {total} pages, '
                        f'and what each one needs before it',
            ha='center', va='top', fontsize=13, weight='bold', color=INK)
    ax.text(0.01, 0.045, 'blue: the machinery      green: how it is built and adapted      '
                        'orange: the families      red: putting one to work',
            ha='left', va='center', fontsize=9.5, color=MUTED)
    _save(fig, MAP_DOC, 'book-map.svg')


def pages_per_chapter() -> None:
    """How the forty pages are shared out, chapter by chapter."""
    nums = [c for c, _, _ in CHAPTERS]
    pages = [p for _, _, p in CHAPTERS]
    cum = np.cumsum(pages)
    print(f'[p2-s1] pages per chapter: ' + ', '.join(f'{c}:{p}' for c, p in zip(nums, pages)))
    print(f'[p2-s1] the first four chapters are {cum[3]} of the {cum[-1]} pages '
          f'({100 * cum[3] / cum[-1]:.0f}%), and chapters 8 to 12 are '
          f'{cum[11] - cum[6]} pages ({100 * (cum[11] - cum[6]) / cum[-1]:.0f}%)')

    fig, ax = plt.subplots(figsize=(12.4, 4.8), facecolor='white')
    _plain(ax)
    cols = [LINK if c <= 4 else SLIDE if c <= 7 else WRIST if c <= 12 else GRIP for c in nums]
    ax.bar(nums, pages, color=cols, width=0.62)
    for c, p in zip(nums, pages):
        ax.text(c, p + 0.12, str(p), ha='center', fontsize=10, color=INK)
    ax.set_xticks(nums)
    ax.set_xticklabels([f'{c}. {n}' for c, n, _ in CHAPTERS], fontsize=8.4,
                       rotation=32, ha='right')
    ax.set_ylim(0, 5.6)
    ax.set_ylabel('pages in the chapter', fontsize=10)
    ax2 = ax.twinx()
    ax2.plot(nums, cum, color=INK, lw=1.8, marker='o', ms=4)
    ax2.set_ylabel('pages read so far', fontsize=10)
    ax2.set_ylim(0, 44)
    ax2.tick_params(labelsize=9.5)
    for c, v in zip(nums, cum):
        if c in (4, 7, 12, 13):
            ax2.annotate(str(v), (c, v), textcoords='offset points', xytext=(-16, 5),
                         fontsize=9, color=INK)
    ax.set_title('Forty pages, and where you are after each chapter',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'pages-per-chapter.svg')


def dependency_depth() -> None:
    """How many chapters stand behind each one, worked out from the map."""
    depth = _depths()
    names = {c: n for c, n, _ in CHAPTERS}
    order = sorted(depth, key=lambda c: (depth[c], c))
    for c in order:
        print(f'[p2-s1] chapter {c:2d} sits at level {depth[c]} of the reading order')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _plain(ax)
    y = np.arange(len(order))[::-1]
    vals = [depth[c] for c in order]
    cols = [LINK if v <= 3 else SLIDE if v <= 5 else WRIST if v <= 7 else GRIP for v in vals]
    ax.barh(y, vals, color=cols, height=0.6)
    for yy, c in zip(y, order):
        ax.text(depth[c] + 0.08, yy, f'{depth[c]}', va='center', fontsize=9.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f'{c}. {names[c]}' for c in order], fontsize=9)
    ax.set_xlim(0, max(vals) + 1.0)
    ax.set_xticks(range(1, max(vals) + 1))
    ax.set_xlabel('the longest chain of chapters that has to be read first, '
                  'counting this one', fontsize=10)
    ax.set_title('Nine chapters deep: why this page is the last one',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'dependency-depth.svg')


# ==========================================================================
# page 2, section 2: the families, side by side
# ==========================================================================

def _tx_macs(tokens: int, d: int, blocks: int) -> int:
    per = 3 * tokens * d * d + 2 * tokens * tokens * d + tokens * d * d + 2 * tokens * d * (4 * d)
    return blocks * per


def _tx_params(d: int, blocks: int) -> int:
    per = (3 * d * d + 3 * d) + (d * d + d) + (2 * 4 * d * d + 5 * d) + 4 * d
    return blocks * per


class Family:
    def __init__(self, name: str, shape: str, n_in: int, n_out: int, macs: int,
                 examples: float, example_note: str) -> None:
        self.name = name
        self.shape = shape
        self.n_in = n_in
        self.n_out = n_out
        self.macs = macs
        self.examples = examples
        self.note = example_note


FAMILIES: list[Family] = [
    Family('picture classifier', '12 blocks, width 384, 196 patches',
           3 * 224 * 224, 1000,
           _tx_macs(196, 384, 12) + 196 * 3 * 16 * 16 * 384, 1e6,
           'labelled pictures'),
    Family('object detector', '12 blocks, width 384, 1,200 patches',
           3 * 640 * 480, 300 * (4 + 1 + 80),
           _tx_macs(1200, 384, 12) + 1200 * 3 * 16 * 16 * 384, 1e5,
           'pictures with boxes drawn on them'),
    Family('promptable segmenter', '12 blocks, width 768, 4,096 patches',
           3 * 1024 * 1024, 1024 * 1024,
           _tx_macs(4096, 768, 12) + 4096 * 3 * 16 * 16 * 768, 1e7,
           'masks, most of them made by the model itself'),
    Family('depth model', '12 blocks, width 384, 1,369 patches',
           3 * 518 * 518, 518 * 518,
           _tx_macs(1369, 384, 12) + 1369 * 3 * 14 * 14 * 384, 1e7,
           'pictures with a depth reading for each pixel'),
    Family('language model, one new word', '24 blocks, width 2,048, cached',
           2048, 32000,
           2 * _tx_params(2048, 24) + 2 * 2048 * 2048 * 24, 1e12,
           'words of text'),
    Family('vision-language model, one new word', '24 blocks, width 2,048, 320 tokens cached',
           320, 32000,
           2 * _tx_params(2048, 24) + 2 * 320 * 2048 * 24, 1e9,
           'picture and caption pairs'),
    Family('behaviour-cloning policy', 'the example policy of the page before',
           2 * 3 * 224 * 224 + 7, 16 * 7, POL.total_macs, 5e2,
           'demonstrations driven by a person'),
    Family('diffusion policy, 10 steps', 'the same, with the trunk run 10 times',
           2 * 3 * 224 * 224 + 7, 16 * 7,
           POL.vit_macs + POL.proj_macs + 10 * (POL.trunk_macs + POL.head_macs), 5e2,
           'demonstrations driven by a person'),
    Family('world model, 20 steps ahead', 'a 512-number state, 6 blocks, width 512',
           512 + 7, 20 * 512, 20 * _tx_macs(20, 512, 6), 1e4,
           'recorded episodes, no labels needed'),
]


def inputs_and_outputs() -> None:
    """How many numbers go into each family, and how many come out."""
    for f in FAMILIES:
        print(f'[p2-s2] {f.name:36s} in {f.n_in:10,}  out {f.n_out:10,}  '
              f'multiply-adds {f.macs:16,}')

    fig, ax = plt.subplots(figsize=(12.6, 5.6), facecolor='white')
    _plain(ax)
    y = np.arange(len(FAMILIES))[::-1]
    ax.barh(y + 0.19, [f.n_in for f in FAMILIES], height=0.34, color=LINK,
            label='numbers going in')
    ax.barh(y - 0.19, [f.n_out for f in FAMILIES], height=0.34, color=WRIST,
            label='numbers coming out')
    ax.set_xscale('log')
    for yy, f in zip(y, FAMILIES):
        ax.text(f.n_in * 1.3, yy + 0.19, f'{f.n_in:,}', va='center', fontsize=8.5, color=INK)
        ax.text(f.n_out * 1.3, yy - 0.19, f'{f.n_out:,}', va='center', fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f.name for f in FAMILIES], fontsize=9)
    ax.set_xlim(10, 3e8)
    ax.set_xlabel('count of numbers (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('Every family takes a pile of numbers and gives back a smaller one',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'inputs-and-outputs.svg')


def data_and_run_cost() -> None:
    """Training data against the arithmetic of one decision, for every family."""
    fig, ax = plt.subplots(figsize=(12.0, 6.0), facecolor='white')
    _plain(ax)
    cols = [LINK, LINK, LINK, LINK, PURPLE, PURPLE, SLIDE, SLIDE, TEAL]
    for f, c in zip(FAMILIES, cols):
        ax.scatter([f.examples], [f.macs / 1e9], s=90, color=c, zorder=4,
                   edgecolor='white', linewidth=0.8)
    offsets = [(11, -4), (11, 5), (11, 4), (11, -5), (-12, 6), (11, -6),
               (12, -14), (12, 6), (11, 5)]
    for f, (dx, dy) in zip(FAMILIES, offsets):
        ax.annotate(f.name, (f.examples, f.macs / 1e9), textcoords='offset points',
                    xytext=(dx, dy), fontsize=8.8, color=INK,
                    ha='left' if dx > 0 else 'right')
    period = 1000.0 / 20
    budget = POL.mac_rate['float16'] * period / 1000.0 / 1e9
    ax.axhline(budget, color=GRIP, ls='--', lw=1.5)
    ax.text(1.6e2, budget * 1.12, f'all the arithmetic one 20 Hz loop has room for '
                                f'on the example machine ({budget:.0f} thousand million)',
            fontsize=9, color=GRIP)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(1e2, 1e14)
    ax.set_ylim(1, 3e3)
    ax.set_xlabel('rough order of magnitude of training examples (example figures, '
                  'not measurements)', fontsize=10)
    ax.set_ylabel('multiply-adds for one decision, in thousand millions (log scale)',
                  fontsize=10)
    ax.set_title('What each family costs to train and what it costs to run',
                 fontsize=12.5, weight='bold')
    print(f'[p2-s2] one 20 Hz loop on the example machine has room for '
          f'{budget:.1f} thousand million multiply-adds')
    _save(fig, MAP_DOC, 'data-and-run-cost.svg')


EPISODE: list[tuple[str, float, float, float]] = [
    # name, calls a second, seconds it runs for, multiply-adds per call in thousand millions
    ('language model, planning the steps', 0.0, 0.0, 0.0),
]


def calls_per_episode() -> None:
    """One six-second pick-and-place, and how often each family is asked."""
    secs = 6.0
    rows = [
        ('language model: the steps, once', 1.0 / secs, FAMILIES[4].macs / 1e9 * 60, PURPLE),
        ('vision-language model: check the scene', 0.5, FAMILIES[5].macs / 1e9 * 20, PURPLE),
        ('open-vocabulary detector', 5.0, FAMILIES[1].macs / 1e9, LINK),
        ('depth model', 5.0, FAMILIES[3].macs / 1e9, LINK),
        ('the policy, with chunks of 16', 2.5, FAMILIES[6].macs / 1e9, SLIDE),
        ('written safety checks', 500.0, 1e-6, GRIP),
    ]
    total_calls = 0.0
    total_work = 0.0
    for nm, rate, macs, _ in rows:
        calls = rate * secs
        total_calls += calls
        total_work += calls * macs
        print(f'[p2-s2] {nm:38s} {rate:7.2f} a second, {calls:6.1f} calls in {secs:.0f} s, '
              f'{calls * macs:9.1f} thousand million multiply-adds')
    seeing = rows[2][1] * secs * rows[2][2] + rows[3][1] * secs * rows[3][2]
    print(f'[p2-s2] the whole episode: {total_calls:.0f} calls and '
          f'{total_work:,.0f} thousand million multiply-adds')
    print(f'[p2-s2] the detector and the depth model together cost {seeing:,.0f} of those '
          f'{total_work:,.0f}, which is {100 * seeing / total_work:.0f}%')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.0, 1.0]})
    fig.subplots_adjust(wspace=0.45)
    _plain(ax1)
    y = np.arange(len(rows))[::-1]
    ax1.barh(y, [r[1] * secs for r in rows], color=[r[3] for r in rows], height=0.55)
    ax1.set_xscale('log')
    for yy, r in zip(y, rows):
        ax1.text(r[1] * secs * 1.3, yy, f'{r[1] * secs:.0f} calls', va='center',
                 fontsize=9, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels([r[0] for r in rows], fontsize=8.8)
    ax1.set_xlim(0.5, 2e4)
    ax1.set_xlabel('calls in one 6 second pick-and-place (log scale)', fontsize=9.5)
    ax1.set_title('How often each one is asked', fontsize=11.5, weight='bold')

    _plain(ax2)
    work = [r[1] * secs * r[2] for r in rows]
    ax2.barh(y, work, color=[r[3] for r in rows], height=0.55)
    ax2.set_xscale('log')
    for yy, w in zip(y, work):
        ax2.text(max(w, 1e-3) * 1.4, yy, f'{w:,.0f}' if w >= 1 else f'{w:.3f}',
                 va='center', fontsize=9, color=INK)
    ax2.set_yticks(y)
    ax2.set_yticklabels([])
    ax2.set_xlim(1e-3, 1e7)
    ax2.set_xlabel('thousand million multiply-adds in the episode (log scale)', fontsize=9.5)
    ax2.set_title('How much of the machine each one takes', fontsize=11.5, weight='bold')
    _save(fig, MAP_DOC, 'calls-per-episode.svg')


# ==========================================================================
# page 2, section 3: what to reach for, given a job
# ==========================================================================

JOBS: list[tuple[str, str, float, float, float, str]] = [
    # job, what to reach for, control rate (Hz), operations per decision,
    # training examples needed, what those examples are
    ('find a bright part on a plain belt', 'a written colour threshold', 30.0,
     3 * 640 * 480, 0, 'none'),
    ('hold 5 newtons against a surface', 'a written force controller', 500.0,
     40, 0, 'none'),
    ('move from A to B without hitting anything', 'a written planner', 2.0,
     2e6, 0, 'none'),
    ('stop the arm when something is wrong', 'written limits and a watchdog', 500.0,
     12, 0, 'none'),
    ('name which of twenty known parts is in the bin', 'a picture classifier', 10.0,
     float(FAMILIES[0].macs), 2e4, 'labelled pictures'),
    ('find an object nobody labelled', 'an open-vocabulary detector', 5.0,
     float(FAMILIES[1].macs), 1e5, 'pictures with boxes, already trained'),
    ('measure how far away each pixel is', 'a depth model', 5.0,
     float(FAMILIES[3].macs), 1e7, 'pictures with depth, already trained'),
    ('pick a cloth out of a pile', 'a diffusion policy', 20.0,
     float(FAMILIES[7].macs), 5e2, 'demonstrations you record'),
    ('follow a spoken instruction on a new table',
     'a vision-language-action model', 10.0, float(FAMILIES[5].macs) * 56, 2e3,
     'demonstrations, on top of web pretraining'),
    ('work out the order of the steps', 'a language model, once a task', 0.2,
     float(FAMILIES[4].macs) * 300, 1e12, 'words of text, already trained'),
]


def cost_against_budget() -> None:
    """What each answer costs to run, against the room its control rate leaves."""
    rate = POL.mac_rate['float16']
    fig, ax = plt.subplots(figsize=(12.6, 6.0), facecolor='white')
    _plain(ax)
    y = np.arange(len(JOBS))[::-1]
    cols = [SLIDE if j[4] == 0 else LINK for j in JOBS]
    ax.barh(y, [j[3] for j in JOBS], color=cols, height=0.5)
    for yy, j in zip(y, JOBS):
        budget = rate / j[2]
        ax.plot([budget, budget], [yy - 0.34, yy + 0.34], color=GRIP, lw=2.2)
        share = 100 * j[3] / budget
        label = (f'one part in {budget / j[3]:,.0f} of the budget' if share < 0.5
                 else f'{share:.1f}% of the budget')
        ax.text(max(j[3], budget) * 1.8, yy, label, va='center', fontsize=8.6, color=INK)
        print(f'[p2-s3] {j[0]:44s} {j[1]:34s} {j[2]:6.1f} Hz  '
              f'{j[3]:18,.0f} operations  {share:9.4f}% of the budget')
    ax.set_xscale('log')
    ax.set_yticks(y)
    ax.set_yticklabels([f'{j[0]}\n{j[1]}' for j in JOBS], fontsize=8.4)
    ax.set_xlim(1, 1e17)
    ax.set_xlabel('arithmetic operations for one decision (log scale)', fontsize=10)
    ax.plot([], [], color=GRIP, lw=2.2, label='all the machine can do in one period at that rate')
    ax.plot([], [], color=SLIDE, lw=6, label='written, not learned')
    ax.plot([], [], color=LINK, lw=6, label='learned')
    ax.legend(fontsize=9, frameon=False, loc='upper center', ncol=3,
              bbox_to_anchor=(0.5, -0.12))
    ax.set_title('Ten jobs, what to reach for, and whether it fits in the time',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'cost-against-budget.svg')


def data_needed() -> None:
    """What each answer costs in examples, and in a person's time where it is demonstrations."""
    learned = [j for j in JOBS if j[4] > 0]
    secs_each = 20.0
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.3, 0.85]})
    fig.subplots_adjust(wspace=0.6)
    _plain(ax1)
    y = np.arange(len(learned))[::-1]
    ax1.barh(y, [j[4] for j in learned], color=LINK, height=0.55)
    ax1.set_xscale('log')
    for yy, j in zip(y, learned):
        ax1.text(j[4] * 1.6, yy, f'{j[4]:,.0f}  {j[5]}', va='center', fontsize=8.6, color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels([j[1] for j in learned], fontsize=9)
    ax1.set_xlim(1e2, 1e18)
    ax1.set_xlabel('training examples, as a rough order of magnitude (log scale)', fontsize=9.5)
    ax1.set_title('Most of these have been trained already', fontsize=11.5, weight='bold')

    _plain(ax2)
    counts = [200, 500, 1000, 2000, 5000]
    hours = [c * secs_each / 3600 for c in counts]
    ax2.bar(np.arange(len(counts)), hours, color=WRIST, width=0.55)
    for i, (c, h) in enumerate(zip(counts, hours)):
        ax2.text(i, h + 0.6, f'{h:.1f} h', ha='center', fontsize=9.5, color=INK)
    ax2.set_xticks(np.arange(len(counts)))
    ax2.set_xticklabels([f'{c:,}' for c in counts], fontsize=9.5)
    ax2.set_xlabel('demonstrations recorded', fontsize=9.5)
    ax2.set_ylabel(f'hours of a person driving the arm, at {secs_each:.0f} s each', fontsize=9.5)
    ax2.set_ylim(0, max(hours) * 1.22)
    ax2.set_title('The one cost you pay yourself', fontsize=11.5, weight='bold')
    for j in learned:
        print(f'[p2-s3] {j[1]:34s} needs about {j[4]:,.0f} {j[5]}')
    for c, h in zip(counts, hours):
        print(f'[p2-s3] {c:,} demonstrations at {secs_each:.0f} seconds each is '
              f'{h:.1f} hours of a person driving the arm')
    _save(fig, MAP_DOC, 'data-needed.svg')


def choosing_a_family() -> None:
    """The questions that pick a family, in the order worth asking them."""
    fig, ax = plt.subplots(figsize=(14.2, 6.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.985, 'Four questions, asked in this order, and where each answer leads',
            ha='center', va='top', fontsize=13, weight='bold', color=INK)
    qs = [
        ('Can a person write down\nthe rule that decides it?', 0.095),
        ('Is the answer a name, a box,\na mask or a depth reading?', 0.295),
        ('Does it need words,\nor an object nobody listed?', 0.495),
        ('Does it have to move the arm\nmoment by moment?', 0.695),
    ]
    for text, x in qs:
        _box(ax, x - 0.085, 0.60, 0.17, 0.17, text, '#eef3f9', size=9.0)
    for i in range(3):
        _arrow(ax, qs[i][1] + 0.085, 0.685, qs[i + 1][1] - 0.085, 0.685, MUTED, 1.6)
        ax.text((qs[i][1] + qs[i + 1][1]) / 2, 0.705, 'no', ha='center', fontsize=9,
                color=MUTED)
    leaves = [
        ('write it:\nthresholds, geometry,\nplanners, controllers', 0.095, '#e4f0e4',
         'no training data at all'),
        ('a classifier, a detector,\na segmenter or\na depth model', 0.295, '#dfeaf6',
         'already trained;\nfine-tune on hundreds'),
        ('a vision-language model,\nor an open-vocabulary\ndetector', 0.495, '#e6dff5',
         'already trained;\nprompt it in words'),
        ('a behaviour-cloning,\ndiffusion or\nflow policy', 0.695, '#f6efe0',
         '200 to 2,000\ndemonstrations'),
    ]
    for text, x, col, note in leaves:
        _box(ax, x - 0.09, 0.21, 0.18, 0.17, text, col, size=9.0)
        ax.text(x, 0.145, note, ha='center', va='center', fontsize=8.4, color=MUTED)
        _arrow(ax, x, 0.60, x, 0.385, MUTED, 1.6)
        ax.text(x + 0.012, 0.49, 'yes', ha='left', fontsize=9, color=MUTED)
    _box(ax, 0.835, 0.21, 0.155, 0.17,
         'a vision-language-\naction model,\nor break the job up', '#f3dede', size=9.0)
    ax.text(0.9125, 0.145, 'co-trained on web\nand robot data', ha='center', va='center',
            fontsize=8.4, color=MUTED)
    _arrow(ax, qs[3][1] + 0.085, 0.685, 0.9125, 0.685, MUTED, 1.6)
    _arrow(ax, 0.9125, 0.60, 0.9125, 0.385, MUTED, 1.6)
    ax.text(0.845, 0.705, 'no', ha='center', fontsize=9, color=MUTED)
    ax.text(0.5, 0.06, 'Ask the first question honestly. Three of the ten jobs on this page '
                       'are answered without any model at all, and those three run in '
                       'microseconds and never surprise you.',
            ha='center', va='center', fontsize=10, color=INK)
    _save(fig, MAP_DOC, 'choosing-a-family.svg')


# ==========================================================================
# page 2, section 4: when the answer is not a neural network
# ==========================================================================

def _written_rule(x: Arr) -> NDArray[np.int64]:
    """The method a person writes: pick the nominal colour that is nearest."""
    d = ((x[:, None, :] - CLASS_RGB[None, :, :]) ** 2).sum(axis=2)
    return d.argmin(axis=1)


def rule_vs_learned() -> None:
    """How many examples the learned method needs before it beats the written one."""
    xte, yte = COL.xte, COL.yte
    written = float((_written_rule(xte) == yte).mean())
    sizes = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    means, spread = [], []
    for n in sizes:
        got = []
        for seed in range(9):
            rng = np.random.default_rng(500 + seed)
            xtr, ytr = make_objects(n, rng)
            mu, sd = xtr.mean(axis=0), xtr.std(axis=0) + 1e-6
            w, b = train_colour_model((xtr - mu) / sd, ytr)
            got.append(_accuracy((xte - mu) / sd, yte, w, b))
        means.append(float(np.mean(got)))
        spread.append(float(np.std(got)))
    cross = next((n for n, m in zip(sizes, means) if m > written), None)
    print(f'[p2-s4] the written nearest-colour rule scores {100 * written:.1f}% with no '
          f'training data at all')
    for n, m, s in zip(sizes, means, spread):
        print(f'[p2-s4]   the learned classifier with {n:5d} examples: {100 * m:.1f}% '
              f'(spread {100 * s:.1f} points over 9 runs)')
    print(f'[p2-s4] the learned one first beats the written one at {cross} examples')

    fig, ax = plt.subplots(figsize=(11.2, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(sizes, [100 * m for m in means], color=LINK, lw=2.2, marker='o', ms=4.5,
            label='learned: a classifier trained on that many examples')
    ax.fill_between(sizes, [100 * (m - s) for m, s in zip(means, spread)],
                    [100 * (m + s) for m, s in zip(means, spread)], color=LINK_PALE, alpha=0.8)
    ax.axhline(100 * written, color=SLIDE, lw=2.2,
               label='written: pick the nearest nominal colour, no data at all')
    if cross is not None:
        ax.axvline(cross, color=MUTED, ls='--', lw=1.2)
        ax.text(cross * 1.1, 42, f'the learned one pulls ahead\nat about {cross} examples',
                fontsize=9.5, color=INK)
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes], fontsize=9)
    ax.set_ylim(20, 100)
    ax.set_xlabel('training examples given to the learned method (log scale)', fontsize=10)
    ax.set_ylabel('accuracy on the same 2,000 test objects (%)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('With few examples, the rule a person wrote is the better answer',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'rule-vs-learned.svg')


def cost_comparison() -> None:
    """What the two answers cost for one decision, and what they cost to change."""
    pixels = 3 * 224 * 224
    written_ops = pixels + 4 * 3 * 3           # average the pixels, then four distances
    learned_ops = FAMILIES[0].macs
    ratio = learned_ops / written_ops
    print(f'[p2-s4] the written rule does {written_ops:,} operations for one decision, '
          f'the classifier does {learned_ops:,}, which is {ratio:,.0f} times as many')
    ms_written = 1000 * written_ops / POL.mac_rate['float16']
    ms_learned = 1000 * learned_ops / POL.mac_rate['float16']
    print(f'[p2-s4] on the example machine that is {ms_written * 1000:.2f} microseconds '
          f'against {ms_learned:.2f} milliseconds')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), facecolor='white')
    fig.subplots_adjust(wspace=0.35)
    _plain(ax1)
    ax1.bar([0, 1], [written_ops, learned_ops], color=[SLIDE, LINK], width=0.5)
    ax1.set_yscale('log')
    for i, v in enumerate([written_ops, learned_ops]):
        ax1.text(i, v * 1.6, f'{v:,}', ha='center', fontsize=10.5, weight='bold', color=INK)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['the written rule', 'the picture classifier'], fontsize=9.5)
    ax1.set_ylim(1e4, 1e13)
    ax1.set_ylabel('operations for one decision (log scale)', fontsize=10)
    ax1.set_title(f'{ratio:,.0f} times the arithmetic', fontsize=11.5, weight='bold')

    _plain(ax2)
    ax2.bar([0, 1], [ms_written, ms_learned], color=[SLIDE, LINK], width=0.5)
    ax2.set_yscale('log')
    for i, v in enumerate([ms_written, ms_learned]):
        txt = f'{v * 1000:.2f} microseconds' if v < 0.01 else f'{v:.2f} ms'
        ax2.text(i, v * 1.8, txt, ha='center', fontsize=10.5, weight='bold', color=INK)
    ax2.axhline(1000 / 500, color=GRIP, ls='--', lw=1.4)
    ax2.text(-0.46, 1000 / 500 * 2.2, 'the 2 ms period of a 500 Hz loop', ha='left',
             fontsize=9, color=GRIP)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['the written rule', 'the picture classifier'], fontsize=9.5)
    ax2.set_ylim(1e-5, 1e2)
    ax2.set_ylabel('milliseconds on the example machine (log scale)', fontsize=10)
    ax2.set_title('Only one of them fits in a fast loop', fontsize=11.5, weight='bold')
    _save(fig, MAP_DOC, 'cost-comparison.svg')


def where_each_breaks() -> None:
    """The same four conditions, put to both answers."""
    conds = [
        ('as expected', dict(light=1.0, tint=None, noise=0.045)),
        ('light 45% brighter', dict(light=1.45, tint=None, noise=0.045)),
        ('a warmer tablecloth', dict(light=1.0, tint=np.array([0.10, 0.05, -0.05]),
                                     noise=0.045)),
        ('a noisier camera', dict(light=1.0, tint=None, noise=0.11)),
    ]
    wr, ln = [], []
    for i, (name, kw) in enumerate(conds):
        seed = 8 if i == 0 else 700 + i      # i == 0 is the very test set COL was measured on
        x, y = make_objects(2000, np.random.default_rng(seed), **kw)  # type: ignore[arg-type]
        a_w = float((_written_rule(x) == y).mean())
        a_l = COL.accuracy_with(COL.mean, COL.std, x, y)
        wr.append(a_w)
        ln.append(a_l)
        print(f'[p2-s4] {name:22s} written {100 * a_w:5.1f}%   learned {100 * a_l:5.1f}%')

    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(conds))
    ax.bar(x - 0.19, [100 * v for v in wr], width=0.36, color=SLIDE,
           label='the written nearest-colour rule')
    ax.bar(x + 0.19, [100 * v for v in ln], width=0.36, color=LINK,
           label='the learned classifier')
    for i in range(len(conds)):
        ax.text(i - 0.19, 100 * wr[i] + 1.8, f'{100 * wr[i]:.0f}', ha='center', fontsize=9.5)
        ax.text(i + 0.19, 100 * ln[i] + 1.8, f'{100 * ln[i]:.0f}', ha='center', fontsize=9.5)
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in conds], fontsize=9.5)
    ax.set_ylim(0, 112)
    ax.set_ylabel('accuracy on 2,000 objects (%)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax.set_title('Neither one survives a change it was not built for',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'where-each-breaks.svg')


# ==========================================================================
# page 2, section 5: what is not solved
# ==========================================================================

def data_cost_curve() -> None:
    """An example curve for the hours of demonstration a success rate costs."""
    def failure(h: Arr | float) -> Arr | float:
        return 0.5 * (np.asarray(h) / 10.0) ** -0.4

    def hours_for(target: float) -> float:
        return 10.0 * (0.5 / (1.0 - target)) ** 2.5

    hrs = np.logspace(1, 5.6, 140)
    succ = 100 * (1 - failure(hrs))
    marks = [0.80, 0.90, 0.95, 0.99]
    for t in marks:
        h = hours_for(t)
        print(f'[p2-s5] reaching {100 * t:.0f}% on this example curve takes {h:,.0f} hours '
              f'of demonstration, which is {h * 180:,.0f} demonstrations at 20 seconds each, '
              f'or {h / (6 * 250):,.1f} years for one person working six hours a day')

    fig, ax = plt.subplots(figsize=(11.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(hrs, succ, color=LINK, lw=2.4)
    for t, col in zip(marks, [SLIDE, TEAL, WRIST, GRIP]):
        h = hours_for(t)
        ax.plot([h, h], [40, 100 * t], color=col, ls='--', lw=1.3)
        ax.scatter([h], [100 * t], color=col, s=42, zorder=4)
        right = h < 1e4
        ax.text(h * (1.14 if right else 0.86), 100 * t - (1.6 if right else 6.5),
                f'{100 * t:.0f}%: {h:,.0f} hours', fontsize=9.5, color=col,
                ha='left' if right else 'right')
    ax.set_xscale('log')
    ax.set_xlim(10, 4e5)
    ax.set_ylim(40, 102)
    ax.set_xlabel('hours of demonstration collected (log scale)', fontsize=10)
    ax.set_ylabel('whole-task success rate (%)', fontsize=10)
    ax.set_title('An example curve, not a measurement: each step up costs far more '
                 'than the one before', fontsize=12, weight='bold')
    _save(fig, MAP_DOC, 'data-cost-curve.svg')


def reliability_compounding() -> None:
    """One step going right is not one task going right."""
    steps = np.arange(1, 41)
    rates = [0.95, 0.98, 0.99, 0.999]
    cols = [GRIP, WRIST, TEAL, SLIDE]
    bar = 0.95
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.15, 0.9]})
    fig.subplots_adjust(wspace=0.32)
    _plain(ax1)
    for p, c in zip(rates, cols):
        ax1.plot(steps, 100 * p ** steps, color=c, lw=2.2, label=f'{100 * p:g}% a step')
        n = math.log(bar) / math.log(p)
        print(f'[p2-s5] at {100 * p:g}% a step, a task of {n:.1f} steps still succeeds '
              f'{100 * bar:.0f}% of the time; 20 steps gives {100 * p ** 20:.1f}%')
    ax1.axhline(100 * bar, color=INK, ls='--', lw=1.3)
    ax1.text(22, 100 * bar - 7, 'a task that works 95 times in 100', fontsize=9, color=INK)
    ax1.set_xlabel('steps in the task', fontsize=10)
    ax1.set_ylabel('chance the whole task works (%)', fontsize=10)
    ax1.set_ylim(0, 104)
    ax1.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax1.set_title('A good step rate is not a good task rate', fontsize=11.5, weight='bold')

    _plain(ax2)
    task_rates = [0.90, 0.95, 0.99, 0.999]
    per_hour = 3600 / 40.0
    gaps = [1.0 / ((1 - r) * per_hour) for r in task_rates]
    ax2.bar(np.arange(4), gaps, color=[GRIP, WRIST, TEAL, SLIDE], width=0.55)
    ax2.set_yscale('log')
    for i, (r, g) in enumerate(zip(task_rates, gaps)):
        txt = f'{g * 60:.0f} min' if g < 1 else f'{g:.1f} h'
        ax2.text(i, g * 1.5, txt, ha='center', fontsize=10, weight='bold', color=INK)
        print(f'[p2-s5] a whole-task success of {100 * r:g}% at one task every 40 seconds '
              f'means a person is called over every {g:.2f} hours')
    need = 1 - 1.0 / (per_hour * 8)
    print(f'[p2-s5] one call-out per eight-hour shift needs a whole-task success of '
          f'{100 * need:.2f}%')
    ax2.set_xticks(np.arange(4))
    ax2.set_xticklabels([f'{100 * r:g}%' for r in task_rates], fontsize=10)
    ax2.set_xlabel('whole-task success rate', fontsize=10)
    ax2.set_ylabel('hours between call-outs (log scale)', fontsize=10)
    ax2.set_ylim(0.01, 100)
    ax2.set_title(f'One shift without a call-out needs {100 * need:.2f}%',
                  fontsize=11.5, weight='bold')
    _save(fig, MAP_DOC, 'reliability-compounding.svg')


def evaluation_cost() -> None:
    """How many trials it takes to prove a small improvement, and how long that is."""
    z_a, z_b = 1.959964, 0.841621
    p1 = 0.80
    gains = np.arange(1, 16) / 100.0
    per_arm = []
    for g in gains:
        p2 = p1 + g
        pbar = (p1 + p2) / 2
        num = (z_a * math.sqrt(2 * pbar * (1 - pbar))
               + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        per_arm.append(math.ceil(num / g ** 2))
    secs = 90.0
    for g, n in zip(gains, per_arm):
        if round(g * 100) in (2, 5, 10, 15):
            hrs = 2 * n * secs / 3600
            print(f'[p2-s5] proving {100 * p1:.0f}% has become {100 * (p1 + g):.0f}% needs '
                  f'{n:,} trials of each, which is {2 * n:,} trials and {hrs:.1f} hours '
                  f'at 90 seconds a trial')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(100 * gains, per_arm, color=PURPLE, lw=2.4, marker='o', ms=4.5)
    ax.set_yscale('log')
    for g, n in zip(gains, per_arm):
        if round(g * 100) in (2, 5, 10):
            ax.annotate(f'{n:,} each', (100 * g, n), textcoords='offset points',
                        xytext=(8, 6), fontsize=9.5, color=INK)
    ax.set_xlabel('the improvement you are trying to prove, in percentage points', fontsize=10)
    ax.set_ylabel('trials needed on each of the two policies (log scale)', fontsize=10)
    ax2 = ax.twinx()
    ax2.set_yscale('log')
    ax2.set_ylim(*[v * 2 * secs / 3600 for v in ax.get_ylim()])
    ax2.set_ylabel('hours of arm time for both, at 90 seconds a trial', fontsize=10)
    ax2.tick_params(labelsize=9.5)
    ax.set_title('Starting from 80%: what it costs to show you have improved it',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'evaluation-cost.svg')


def outside_the_training_set() -> None:
    """Measured success against how far the object was from anything in the training data."""
    rng = np.random.default_rng(41)
    train = np.stack([rng.uniform(-12, 12, 140), rng.uniform(16, 34, 140)], axis=1)
    pts, dists, oks = [], [], []
    for x in np.linspace(-19, 19, 20):
        for y in np.linspace(11, 39, 15):
            d = float(np.min(np.hypot(train[:, 0] - x, train[:, 1] - y)))
            p = 0.93 * math.exp(-(d / 5.5) ** 2) + 0.02
            ok = int((rng.random(10) < p).sum())
            pts.append((x, y))
            dists.append(d)
            oks.append(ok)
    dists = np.array(dists)
    oks = np.array(oks)
    edges = [0, 1, 2, 3, 4, 6, 8, 12]
    mids, rate, lo, hi = [], [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (dists >= a) & (dists < b)
        if m.sum() == 0:
            continue
        s = int(oks[m].sum())
        n = int(10 * m.sum())
        l, h = cp_interval(s, n)
        mids.append((a + b) / 2)
        rate.append(s / n)
        lo.append(l)
        hi.append(h)
        print(f'[p2-s5] objects {a}-{b} cm from the nearest training example: '
              f'{s} of {n} = {100 * s / n:.0f}% '
              f'(95% interval {100 * l:.0f}% to {100 * h:.0f}%)')

    fig, ax = plt.subplots(figsize=(11.2, 5.2), facecolor='white')
    _plain(ax)
    ax.errorbar(mids, [100 * r for r in rate],
                yerr=[[100 * (r - l) for r, l in zip(rate, lo)],
                      [100 * (h - r) for r, h in zip(rate, hi)]],
                fmt='o-', color=LINK, ecolor=INK, capsize=5, lw=2.2, ms=6)
    ax.axhline(100 * rate[0], color=SLIDE, ls='--', lw=1.3)
    ax.text(8.5, 100 * rate[0] + 2, 'what the policy scores where it was trained',
            ha='right', fontsize=9.5, color=SLIDE)
    ax.set_xlabel('distance from the nearest training example (cm)', fontsize=10)
    ax.set_ylabel('measured success rate, with its 95% interval (%)', fontsize=10)
    ax.set_ylim(0, 105)
    ax.set_title('Nothing in the training promises anything about the right-hand side',
                 fontsize=12.5, weight='bold')
    _save(fig, MAP_DOC, 'outside-the-training-set.svg')


# ==========================================================================
# page 2, section 6: what this book left out
# ==========================================================================

BOOKS: list[tuple[str, str]] = [
    ('01_robotics-intro', 'Robot Arm Basics'),
    ('02_perception', 'Perception'),
    ('03_frameworks', 'Frameworks and Manipulation'),
    ('04_ros-and-rviz', 'ROS and RViz'),
    ('05_programming-techniques', 'Programming Techniques'),
    ('06_neural-networks', 'Neural Networks and AI Models'),
    ('07_learned-models', 'Learned Models'),
    ('08_robotics-by-example', 'Robotics by Example'),
]


def _chapter_count(folder: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[1] / folder
    dirs = sum(1 for p in root.iterdir() if p.is_dir())
    files = sum(1 for p in root.iterdir() if p.suffix == '.md')
    return dirs + files


def library_shelf() -> None:
    """The eight books of the library and how many chapters each one holds."""
    counts = [_chapter_count(f) for f, _ in BOOKS]
    for (f, t), c in zip(BOOKS, counts):
        print(f'[p2-s6] {t:32s} {c:2d} chapters')
    print(f'[p2-s6] the library holds {sum(counts)} chapters in {len(BOOKS)} books')

    fig, ax = plt.subplots(figsize=(13.0, 5.2), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.985, f'The library: {len(BOOKS)} books and {sum(counts)} chapters, '
                        f'and where this book sits among them',
            ha='center', va='top', fontsize=13, weight='bold', color=INK)
    w = 0.108
    for i, ((f, t), c) in enumerate(zip(BOOKS, counts)):
        x = 0.018 + i * (w + 0.0125)
        here = f.endswith('neural-networks')
        col = '#f3dede' if here else '#eef3f9'
        h = 0.17 + 0.028 * c
        _box(ax, x, 0.30, w, h, '', col, edge=GRIP if here else INK)
        ax.text(x + w / 2, 0.30 + h - 0.075, _wrap(t, 14), ha='center', va='center',
                fontsize=8.4, color=INK, weight='bold' if here else 'normal',
                linespacing=1.35)
        ax.text(x + w / 2, 0.345, f'{c} chapters', ha='center', va='center', fontsize=8.6,
                color=MUTED)
    ax.text(0.5, 0.15, 'This book explains the machinery. The one on its right lists the '
                       'models built out of it, and the one on its left holds the methods '
                       'that were written rather than learned.',
            ha='center', va='center', fontsize=10, color=INK)
    _save(fig, MAP_DOC, 'library-shelf.svg')


HANDOFFS: list[tuple[str, str]] = [
    ('what a camera measures, and how to calibrate it', 'Perception'),
    ('frames, transforms and inverse kinematics', 'Robot Arm Basics'),
    ('planning a path that misses the obstacles', 'Programming Techniques'),
    ('PID, force control and safety monitoring', 'Programming Techniques'),
    ('simulators, and training an arm in one', 'Frameworks and Manipulation'),
    ('the software the parts talk through', 'ROS and RViz'),
    ('which models exist, what they cost, their licences', 'Learned Models'),
    ('one problem followed the whole way down', 'Robotics by Example'),
]


def handoff_map() -> None:
    """Everything this book left out, and the book that holds it."""
    titles = [t for _, t in BOOKS]
    colours = {t: c for t, c in zip(titles, [TEAL, PURPLE, JOINT, LINK, SLIDE, GRIP,
                                             WRIST, '#8a6d3b'])}
    for topic, book in HANDOFFS:
        print(f'[p2-s6] left out: {topic:52s} -> {book}')

    fig, ax = plt.subplots(figsize=(12.6, 5.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.985, 'Eight things this book does not cover, and the book that does',
            ha='center', va='top', fontsize=13, weight='bold', color=INK)
    for i, (topic, book) in enumerate(HANDOFFS):
        y = 0.86 - i * 0.104
        _box(ax, 0.02, y - 0.042, 0.50, 0.084, topic, '#f4f4f4', size=9.4)
        _arrow(ax, 0.53, y, 0.60, y, MUTED, 1.4)
        _box(ax, 0.61, y - 0.042, 0.36, 0.084, book, '#eef3f9',
             edge=colours.get(book, INK), size=9.4)
    _save(fig, MAP_DOC, 'handoff-map.svg')


def reading_order() -> None:
    """One suggested path through the rest of the library after this book."""
    counts = {f: _chapter_count(f) for f, _ in BOOKS}
    steps = [
        ('you are here', '06_neural-networks', 'the machinery, from one neuron up'),
        ('next', '07_learned-models', 'which models exist for an arm, and what each costs'),
        ('then', '05_programming-techniques', 'the methods nobody had to train'),
        ('then', '02_perception', 'what the camera really measures'),
        ('then', '03_frameworks', 'simulators, and training an arm in one'),
        ('last', '08_robotics-by-example', 'one problem solved ten ways, written and learned'),
    ]
    total = sum(counts[f] for _, f, _ in steps)
    print(f'[p2-s6] the suggested onward path covers {total} chapters in {len(steps)} books')
    titles = dict(BOOKS)

    fig, ax = plt.subplots(figsize=(13.2, 4.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.97, f'Where to go after this page: {total} chapters, in this order',
            ha='center', va='top', fontsize=13, weight='bold', color=INK)
    w = 0.148
    for i, (word, folder, note) in enumerate(steps):
        x = 0.015 + i * (w + 0.015)
        here = i == 0
        _box(ax, x, 0.40, w, 0.33, '', '#f3dede' if here else '#eef3f9',
             edge=GRIP if here else INK)
        ax.text(x + w / 2, 0.695, word, ha='center', va='center', fontsize=8.4, color=MUTED)
        ax.text(x + w / 2, 0.585, _wrap(titles[folder], 15), ha='center', va='center',
                fontsize=8.8, weight='bold', color=INK, linespacing=1.35)
        ax.text(x + w / 2, 0.445, f'{counts[folder]} chapters', ha='center', va='center',
                fontsize=8.6, color=MUTED)
        ax.text(x + w / 2, 0.365, _wrap(note, 24), ha='center', va='top', fontsize=7.8,
                color=MUTED, linespacing=1.4)
        if i:
            _arrow(ax, x - 0.014, 0.565, x - 0.002, 0.565, MUTED, 1.5)
    _save(fig, MAP_DOC, 'reading-order.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    report_policy()
    checkpoint_files()
    parameter_shares()
    resize_mismatch()
    wrong_normalisation()
    channel_swap()
    action_scaling()
    macs_by_stage()
    launch_overhead()
    runtime_steps()
    throughput_vs_batch()
    latency_vs_batch()
    batch_timeline()
    latency_budget()
    where_the_time_goes()
    action_chunk_timeline()
    loss_not_success()
    trial_positions()
    trials_and_intervals()
    ablation_bars()
    out_of_distribution()
    failure_triage()
    what_to_log()
    safety_layer()
    book_map()
    pages_per_chapter()
    dependency_depth()
    inputs_and_outputs()
    data_and_run_cost()
    calls_per_episode()
    cost_against_budget()
    data_needed()
    choosing_a_family()
    rule_vs_learned()
    cost_comparison()
    where_each_breaks()
    data_cost_curve()
    reliability_compounding()
    evaluation_cost()
    outside_the_training_set()
    library_shelf()
    handoff_map()
    reading_order()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
