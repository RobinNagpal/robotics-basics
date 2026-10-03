"""Generate the diagrams for two pages of docs/05_neural-networks/10_language-and-multimodal-models/.

    03_vision-language-models.md   -> images/language-and-multimodal-models/vision-language-models/
    04_reasoning-and-tool-use.md   -> images/language-and-multimodal-models/reasoning-and-tool-use/

Run with:  python3 docs/diagrams/language_and_multimodal_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so that the two documents can quote the same values.

What is real arithmetic and what is simulated:

* The token counts, the patch counts, the tiling counts, the context shares,
  the projector shapes, the parameter counts and the memory figures on the
  vision-language page are all plain arithmetic on the sizes stated at the top
  of this file. Those sizes are a worked illustrative model, not a measurement
  of any named model: a square input of 224 pixels cut into patches of 14, a
  vision backbone of 24 blocks of width 1024 and a language model of 32 blocks
  of width 4096.
* The scene pictures on the vision-language page are drawn here as arrays with
  numpy.random.default_rng(7) for the speckle, and the squeezing is a real
  block average of that array, so the loss of detail in the small version is
  the real result of averaging.
* The vector clouds and vector lengths that show why the two halves do not fit
  together are simulated with numpy.random.default_rng(3), and the lengths and
  distances drawn from them are real arithmetic on those simulated vectors.
* The two training-order curves come from a real gradient descent run written
  out in NumPy on a made-up task with numpy.random.default_rng(21), so the
  curves are measured rather than drawn.
* The accuracy-against-working-out curves, the vote curves, the beam search
  curves, the argument validation counts and the episode turn and time counts
  on the reasoning page are Monte Carlo simulations with the seeds given in
  each class, run on the simple made-up tasks those classes describe. They are
  drawn to show the shape of a trade and are labelled illustrative in the
  figures and in the pages. They are not benchmark scores for any model.
"""

import pathlib
import re
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'language-and-multimodal-models')
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

VLM_DOC: str = 'vision-language-models'
RTU_DOC: str = 'reasoning-and-tool-use'

Arr = NDArray[np.float64]

# --------------------------------------------------------------------------
# the one illustrative model whose sizes every number on page 3 comes from
# --------------------------------------------------------------------------

PATCH: int = 14                     # pixels on a side of one picture patch
SIDE: int = 224                     # pixels on a side of the backbone's input square
GRID_N: int = SIDE // PATCH         # patches across the input square
PIC_TOKENS: int = GRID_N * GRID_N   # picture tokens for one square crop
V_WIDTH: int = 1024                 # numbers in one backbone output vector
L_WIDTH: int = 4096                 # numbers in one language model token embedding
V_BLOCKS: int = 24
L_BLOCKS: int = 32
CONTEXT: int = 8192                 # tokens the language model can hold at once
BIG_CONTEXT: int = 131072
HI: int = 672                       # pixels on a side of the high resolution picture
CAM_W: int = 1280                   # camera frame width in pixels
CAM_H: int = 720                    # camera frame height in pixels
MM_PER_PIXEL: float = 0.5           # the camera sees 640 mm across its 1280 pixels


def block_params(width: int, blocks: int) -> int:
    """Parameters in a stack of transformer blocks of this width.

    One block holds four square attention matrices and two feed-forward
    matrices of four times the width, so 4 * w * w + 2 * 4 * w * w = 12 * w * w.
    """
    return blocks * 12 * width * width


V_PARAMS: int = block_params(V_WIDTH, V_BLOCKS) + PATCH * PATCH * 3 * V_WIDTH
L_PARAMS: int = block_params(L_WIDTH, L_BLOCKS)
PROJ_1: int = V_WIDTH * L_WIDTH + L_WIDTH                       # one linear layer
PROJ_2: int = PROJ_1 + L_WIDTH * L_WIDTH + L_WIDTH              # two layers with GELU
RESAMPLE_OUT: int = 64                                          # a resampler's fixed count
PROJ_R: int = (RESAMPLE_OUT * L_WIDTH + 4 * L_WIDTH * L_WIDTH
               + 2 * L_WIDTH * V_WIDTH)                         # queries + one attention

TILES_HI: int = (HI // SIDE) * (HI // SIDE)                     # crops over the 672 picture
TOK_HI: int = (TILES_HI + 1) * PIC_TOKENS                       # crops plus one thumbnail
TILES_CAM: int = -(-CAM_W // SIDE) * -(-CAM_H // SIDE)          # crops over a camera frame
TOK_CAM: int = (TILES_CAM + 1) * PIC_TOKENS

SQUEEZE: int = HI // SIDE                                       # how much 672 shrinks by
PX_PER_PATCH_SQ: int = PATCH * SQUEEZE                          # original pixels per patch
PX_PER_PATCH_TILE: int = PATCH


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


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, size: float = 10.0,
         colour: str = INK, weight: str = 'normal', lw: float = 1.1,
         family: str | None = None) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.012,rounding_size=0.03',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size,
            color=colour, weight=weight, zorder=3,
            family=family if family else 'DejaVu Sans')


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.3, style: str = '-|>') -> None:
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=colour, lw=lw,
                                shrinkA=0, shrinkB=0))


def _thousands(n: int) -> str:
    return f'{n:,}'


# ==========================================================================
# 03_vision-language-models.md
# ==========================================================================

# -- section 1: the two halves, and the gap between them -------------------

def vlm_two_halves() -> None:
    """The backbone's output shape beside the language model's embedding shape."""
    fig: Figure = plt.figure(figsize=(11.0, 5.1))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5.1)

    ax.text(2.6, 4.85, 'The seeing half', ha='center', fontsize=12.5, weight='bold',
            color=TEAL)
    ax.text(8.4, 4.85, 'The reading half', ha='center', fontsize=12.5, weight='bold',
            color=PURPLE)

    _box(ax, 0.7, 3.75, 3.8, 0.72,
         f'camera picture, {SIDE} x {SIDE} pixels', face='#eef7f7', edge=TEAL)
    _box(ax, 0.7, 2.75, 3.8, 0.72,
         f'cut into patches of {PATCH} x {PATCH}\n'
         f'{GRID_N} x {GRID_N} = {PIC_TOKENS} patches', face='#eef7f7', edge=TEAL)
    _box(ax, 0.7, 1.55, 3.8, 0.92,
         f'{V_BLOCKS} transformer blocks\nof width {V_WIDTH}', face='#eef7f7', edge=TEAL)
    _box(ax, 0.7, 0.55, 3.8, 0.72,
         f'out: {PIC_TOKENS} vectors\nof {V_WIDTH} numbers each',
         face='#d9ecec', edge=TEAL, weight='bold')
    for y0, y1 in ((3.75, 3.47), (2.75, 2.47), (1.55, 1.27)):
        _arrow(ax, 2.6, y0, 2.6, y1, colour=TEAL)

    _box(ax, 6.5, 3.75, 3.8, 0.72, 'the words of the question', face='#f2eefa',
         edge=PURPLE)
    _box(ax, 6.5, 2.75, 3.8, 0.72, 'split into tokens,\neach looked up in a table',
         face='#f2eefa', edge=PURPLE)
    _box(ax, 6.5, 1.55, 3.8, 0.92,
         f'{L_BLOCKS} transformer blocks\nof width {L_WIDTH}', face='#f2eefa',
         edge=PURPLE)
    _box(ax, 6.5, 0.55, 3.8, 0.72,
         f'each token is a vector\nof {L_WIDTH} numbers', face='#e6dcf7', edge=PURPLE,
         weight='bold')
    for y0, y1 in ((3.75, 3.47), (2.75, 2.47), (1.55, 1.27)):
        _arrow(ax, 8.4, y0, 8.4, y1, colour=PURPLE)

    ax.annotate('', xy=(6.4, 0.91), xytext=(4.6, 0.91),
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=2.0,
                                connectionstyle='arc3,rad=0.0'))
    ax.text(5.5, 1.42, f'{V_WIDTH}\ndoes not fit\ninto {L_WIDTH}', ha='center',
            va='center', fontsize=10.5, color=GRIP, weight='bold')
    ax.text(5.5, 0.28, 'nothing lines these two up on its own', ha='center',
            fontsize=10, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'two-halves.svg')
    print(f'[1a] backbone out {PIC_TOKENS} x {V_WIDTH}; '
          f'language model tokens are {L_WIDTH} numbers wide')


def vlm_vector_lengths() -> None:
    """Simulated: the backbone's vectors are far longer than token embeddings."""
    rng = np.random.default_rng(3)
    width = 64
    patch = rng.normal(0.0, 1.0, size=(PIC_TOKENS, width)) * 2.9 + 0.8
    tokens = rng.normal(0.0, 1.0, size=(400, width)) * 0.42
    lp = np.linalg.norm(patch, axis=1)
    lt = np.linalg.norm(tokens, axis=1)
    ratio = float(lp.mean() / lt.mean())

    # a toy first block of the language model, made once and used on both sets
    w1 = rng.normal(0.0, 1.0 / np.sqrt(width), size=(width, width))
    w2 = rng.normal(0.0, 1.0 / np.sqrt(width), size=(width, width))

    def block(x: Arr) -> Arr:
        h = np.maximum(x @ w1, 0.0)
        return h @ w2

    out_t = np.linalg.norm(block(tokens), axis=1)
    out_p = np.linalg.norm(block(patch), axis=1)

    fig: Figure = plt.figure(figsize=(11.0, 3.9))
    ax1: Axes = fig.add_axes((0.07, 0.17, 0.38, 0.64))
    ax2: Axes = fig.add_axes((0.58, 0.17, 0.38, 0.64))
    _plain(ax1)
    _plain(ax2)

    ax1.hist(lt, bins=28, color=PURPLE, alpha=0.85, label='token embeddings')
    ax1.hist(lp, bins=28, color=TEAL, alpha=0.85, label='backbone patch vectors')
    ax1.set_xlabel('length of the vector', fontsize=10)
    ax1.set_ylabel('how many vectors', fontsize=10)
    ax1.set_title(f'Lengths differ by about {ratio:.0f} times', fontsize=11.5,
                  weight='bold')
    ax1.legend(fontsize=9, frameon=False)

    ax2.hist(out_t, bins=28, color=PURPLE, alpha=0.85,
             label='from token embeddings')
    ax2.hist(out_p, bins=28, color=TEAL, alpha=0.85,
             label='from raw patch vectors')
    ax2.set_xlabel('length of what the first block gives back', fontsize=10)
    ax2.set_ylabel('how many vectors', fontsize=10)
    ax2.set_title(f'So the first block answers about {out_p.mean() / out_t.mean():.0f} '
                  'times too loudly', fontsize=11.5, weight='bold')
    ax2.legend(fontsize=9, frameon=False)
    fig.text(0.5, 0.005, 'simulated vectors and a simulated first block, seed 3',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'vector-lengths.svg')
    print(f'[1b] simulated mean length: patch vectors {lp.mean():.2f}, token '
          f'embeddings {lt.mean():.2f}, ratio {ratio:.1f}; after one block the '
          f'answers are {out_p.mean() / out_t.mean():.1f} times as long')


def vlm_parameter_shares() -> None:
    """How small the trained joining part is next to the two halves."""
    names = ['vision backbone\n'
             f'{V_BLOCKS} blocks of {V_WIDTH}',
             'language model\n'
             f'{L_BLOCKS} blocks of {L_WIDTH}',
             'projector\n'
             f'one {V_WIDTH} x {L_WIDTH} layer']
    vals = [V_PARAMS, L_PARAMS, PROJ_1]
    total = sum(vals)
    fig: Figure = plt.figure(figsize=(9.2, 4.2))
    ax: Axes = fig.add_axes((0.08, 0.20, 0.88, 0.62))
    _plain(ax)
    bars = ax.bar(names, vals, color=[TEAL, PURPLE, JOINT], width=0.56)
    ax.set_yscale('log')
    ax.set_ylabel('parameters (log scale)', fontsize=10)
    ax.set_ylim(1e6, 2e10)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.35,
                f'{_thousands(v)}\n{100 * v / total:.3f}% of the whole',
                ha='center', fontsize=9.5, color=INK)
    ax.set_title('The part that is trained first holds '
                 f'{100 * PROJ_1 / total:.3f}% of the parameters',
                 fontsize=12, weight='bold')
    ax.tick_params(axis='x', labelsize=9.5)
    _save(fig, VLM_DOC, 'parameter-shares.svg')
    print(f'[1c] backbone {_thousands(V_PARAMS)}, language model {_thousands(L_PARAMS)}, '
          f'projector {_thousands(PROJ_1)}, whole {_thousands(total)}, '
          f'projector share {100 * PROJ_1 / total:.4f}%')


# -- section 2: the projector ----------------------------------------------

def _toy_projection() -> tuple[Arr, Arr, Arr, Arr]:
    """A 5-number patch vector through a 5 -> 4 matrix, worked out in full."""
    v = np.array([0.40, -0.90, 1.30, 0.20, -0.50])
    w = np.array([
        [0.5, -0.2, 0.9, 0.1, -0.4],
        [-0.7, 0.6, 0.2, -0.3, 0.8],
        [0.2, 0.4, -0.6, 0.7, 0.1],
        [0.9, -0.1, 0.3, -0.8, 0.2],
    ])
    b = np.array([0.10, -0.20, 0.05, 0.00])
    out = w @ v + b
    return v, w, b, out


def vlm_projector_arithmetic() -> None:
    """One patch vector multiplied by the projector matrix, every number shown."""
    v, w, b, out = _toy_projection()
    fig: Figure = plt.figure(figsize=(10.4, 5.4))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 5.4)
    ax.text(5.2, 5.08, 'The projector is one matrix multiply and one add',
            ha='center', fontsize=12.5, weight='bold')

    cw, ch = 0.62, 0.46
    x0, y0 = 0.45, 3.95
    for j, val in enumerate(v):
        ax.add_patch(Rectangle((x0 + j * cw, y0), cw, ch, facecolor='#d9ecec',
                               edgecolor='white', lw=1.0))
        ax.text(x0 + (j + 0.5) * cw, y0 + ch / 2, f'{val:+.2f}', ha='center',
                va='center', fontsize=9.5, color=INK)
    ax.text(x0 + 2.5 * cw, y0 + ch + 0.18, f'one patch vector, {len(v)} numbers',
            ha='center', fontsize=10.2, color=TEAL, weight='bold')

    mx, my = 0.45, 1.85
    for i in range(w.shape[0]):
        for j in range(w.shape[1]):
            ax.add_patch(Rectangle((mx + j * cw, my + (3 - i) * ch), cw, ch,
                                   facecolor='#fdf0d5', edgecolor='white', lw=1.0))
            ax.text(mx + (j + 0.5) * cw, my + (3 - i + 0.5) * ch, f'{w[i, j]:+.1f}',
                    ha='center', va='center', fontsize=9, color=INK)
    ax.text(mx + 2.5 * cw, my - 0.26,
            f'the projector matrix, {w.shape[0]} rows of {w.shape[1]}',
            ha='center', fontsize=10.2, color=JOINT, weight='bold')

    ox = 5.1
    for i, val in enumerate(out):
        ax.add_patch(Rectangle((ox, my + (3 - i) * ch), 0.95, ch,
                               facecolor='#e6dcf7', edgecolor='white', lw=1.0))
        ax.text(ox + 0.47, my + (3 - i + 0.5) * ch, f'{val:+.3f}', ha='center',
                va='center', fontsize=9.5, color=INK)
    _arrow(ax, 4.0, my + 2 * ch, 5.0, my + 2 * ch, colour=MUTED)
    ax.text(ox + 0.47, my - 0.26, 'out: 4 numbers', ha='center', fontsize=10.2,
            color=PURPLE, weight='bold')
    ax.text(6.4, my + 2.6 * ch,
            'the language model now takes\nthose 4 numbers as a token,\n'
            'exactly as it takes a word', ha='left', va='center', fontsize=10,
            color=PURPLE)

    lines = []
    for i in range(w.shape[0]):
        parts = ' + '.join(f'({w[i, j]:+.1f} x {v[j]:+.2f})' for j in range(len(v)))
        lines.append(f'row {i + 1}:  {parts}  = {float(w[i] @ v):+.3f}'
                     f'   then {b[i]:+.2f}  = {out[i]:+.3f}')
    ax.text(0.45, 1.25, 'each row of the matrix gives one output number',
            ha='left', fontsize=10.2, color=MUTED)
    ax.text(0.45, 0.95, chr(10).join(lines), ha='left', va='top', fontsize=8.6,
            family='DejaVu Sans Mono', color=INK)
    _save(fig, VLM_DOC, 'projector-arithmetic.svg')
    print('[2a] toy projector: a vector of '
          + ', '.join(f'{x:+.2f}' for x in v) + ' becomes '
          + ', '.join(f'{x:+.3f}' for x in out))


def vlm_projector_shapes() -> None:
    """The real shapes the projector works on, and what it weighs."""
    fig: Figure = plt.figure(figsize=(10.6, 3.5))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 3.5)
    ax.text(5.3, 3.18, 'The same multiply, at the real sizes', ha='center',
            fontsize=12.5, weight='bold')
    _box(ax, 0.35, 1.25, 2.6, 1.3,
         f'{PIC_TOKENS} patch vectors\nof {V_WIDTH} numbers\n\n'
         f'{_thousands(PIC_TOKENS * V_WIDTH)} numbers',
         face='#d9ecec', edge=TEAL)
    _box(ax, 3.9, 1.25, 2.8, 1.3,
         f'projector matrix\n{V_WIDTH} in, {L_WIDTH} out\n\n'
         f'{_thousands(V_WIDTH * L_WIDTH)} weights\n+ {_thousands(L_WIDTH)} biases',
         face='#fdf0d5', edge=JOINT)
    _box(ax, 7.65, 1.25, 2.6, 1.3,
         f'{PIC_TOKENS} picture tokens\nof {L_WIDTH} numbers\n\n'
         f'{_thousands(PIC_TOKENS * L_WIDTH)} numbers',
         face='#e6dcf7', edge=PURPLE)
    _arrow(ax, 3.0, 1.9, 3.82, 1.9)
    _arrow(ax, 6.76, 1.9, 7.57, 1.9)
    ax.text(5.3, 0.78, f'{_thousands(PROJ_1)} parameters in all, and every one of the '
            f'{PIC_TOKENS} patches goes through the same matrix',
            ha='center', fontsize=10.5, color=INK)
    ax.text(5.3, 0.38, f'the multiply costs {PIC_TOKENS} x {V_WIDTH} x {L_WIDTH} = '
            f'{_thousands(PIC_TOKENS * V_WIDTH * L_WIDTH)} multiply-and-adds per picture',
            ha='center', fontsize=10, color=MUTED)
    _save(fig, VLM_DOC, 'projector-shapes.svg')
    print(f'[2b] projector {V_WIDTH}->{L_WIDTH}: {_thousands(PROJ_1)} parameters, '
          f'{_thousands(PIC_TOKENS * V_WIDTH * L_WIDTH)} multiply-and-adds per picture')


def vlm_projector_kinds() -> None:
    """Three projector shapes: what each costs and how many tokens each gives."""
    names = ['one linear\nlayer', 'two layers\nwith GELU',
             f'resampler to\n{RESAMPLE_OUT} tokens']
    params = [PROJ_1, PROJ_2, PROJ_R]
    toks = [PIC_TOKENS, PIC_TOKENS, RESAMPLE_OUT]
    fig: Figure = plt.figure(figsize=(10.2, 3.9))
    ax1: Axes = fig.add_axes((0.07, 0.19, 0.38, 0.62))
    ax2: Axes = fig.add_axes((0.58, 0.19, 0.38, 0.62))
    _plain(ax1)
    _plain(ax2)
    b1 = ax1.bar(names, params, color=[JOINT, WRIST, TEAL], width=0.55)
    ax1.set_ylabel('parameters', fontsize=10)
    ax1.set_title('What the joining part weighs', fontsize=11.5, weight='bold')
    for b, v in zip(b1, params):
        ax1.text(b.get_x() + b.get_width() / 2, v + max(params) * 0.03,
                 _thousands(v), ha='center', fontsize=9)
    ax1.set_ylim(0, max(params) * 1.25)
    b2 = ax2.bar(names, toks, color=[JOINT, WRIST, TEAL], width=0.55)
    ax2.set_ylabel('picture tokens per crop', fontsize=10)
    ax2.set_title('What it costs in context', fontsize=11.5, weight='bold')
    for b, v in zip(b2, toks):
        ax2.text(b.get_x() + b.get_width() / 2, v + max(toks) * 0.03, str(v),
                 ha='center', fontsize=9.5)
    ax2.set_ylim(0, max(toks) * 1.25)
    ax1.tick_params(axis='x', labelsize=9)
    ax2.tick_params(axis='x', labelsize=9)
    _save(fig, VLM_DOC, 'projector-kinds.svg')
    print(f'[2c] projector kinds: linear {_thousands(PROJ_1)} params / {PIC_TOKENS} '
          f'tokens; two layers {_thousands(PROJ_2)} / {PIC_TOKENS}; '
          f'resampler {_thousands(PROJ_R)} / {RESAMPLE_OUT}')


def vlm_projector_pulls_in() -> None:
    """Simulated: before training the picture vectors sit apart, after they do not."""
    rng = np.random.default_rng(3)
    tok = rng.normal(0.0, 1.0, size=(300, 2)) @ np.array([[1.0, 0.25], [0.25, 0.9]])
    raw = rng.normal(0.0, 1.0, size=(PIC_TOKENS, 2)) * 2.6 + np.array([5.4, 4.1])
    centre = tok.mean(axis=0)
    scale = tok.std() / raw.std()
    fitted = (raw - raw.mean(axis=0)) * scale + centre
    fitted += rng.normal(0.0, 0.22, size=fitted.shape)

    def far(a: Arr) -> float:
        return float(np.mean(np.linalg.norm(a - centre, axis=1)))

    fig: Figure = plt.figure(figsize=(10.2, 4.3))
    ax1: Axes = fig.add_axes((0.07, 0.15, 0.39, 0.68))
    ax2: Axes = fig.add_axes((0.57, 0.15, 0.39, 0.68))
    for ax, pts, title in ((ax1, raw, 'Before the projector is trained'),
                           (ax2, fitted, 'After the projector is trained')):
        _plain(ax)
        ax.scatter(tok[:, 0], tok[:, 1], s=11, color=PURPLE, alpha=0.6,
                   label='word token embeddings')
        ax.scatter(pts[:, 0], pts[:, 1], s=13, color=TEAL, alpha=0.75,
                   label='projected picture tokens')
        ax.set_xlim(-5.5, 10.5)
        ax.set_ylim(-5.0, 9.0)
        ax.set_xlabel('first of two drawn directions', fontsize=9.5)
        ax.set_ylabel('second drawn direction', fontsize=9.5)
        ax.set_title(f'{title}\nmean distance from the word cloud '
                     f'{far(pts):.2f}', fontsize=11, weight='bold')
        ax.legend(fontsize=8.5, frameon=False, loc='lower right')
    fig.text(0.5, 0.005, 'simulated vectors, seed 3, drawn in two directions',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'projector-pulls-in.svg')
    print(f'[2d] simulated mean distance from the word cloud: before {far(raw):.2f}, '
          f'after {far(fitted):.2f}')


# -- section 3: a picture inside the token stream ---------------------------

SYS_TOKENS: int = 38
Q_TOKENS: int = 17
A_TOKENS: int = 24


def vlm_token_stream() -> None:
    """The real stream of tokens with a picture block sitting inside it."""
    blocks = [('system prompt', SYS_TOKENS, '#e8e8e8', INK),
              ('picture tokens', PIC_TOKENS, '#d9ecec', TEAL),
              ('the question in words', Q_TOKENS, '#f2eefa', PURPLE),
              ('the answer, written one token at a time', A_TOKENS, '#fdf0d5', JOINT)]
    total = sum(n for _, n, _, _ in blocks)
    fig: Figure = plt.figure(figsize=(11.4, 3.6))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.4)
    ax.set_ylim(0, 3.6)
    ax.text(5.7, 3.3, f'One question about one picture is {total} tokens long',
            ha='center', fontsize=12.5, weight='bold')
    x = 0.4
    span = 10.6
    for name, n, face, edge in blocks:
        w = span * n / total
        ax.add_patch(Rectangle((x, 1.55), w, 0.72, facecolor=face, edgecolor=edge,
                               lw=1.2))
        ax.text(x + w / 2, 1.91, str(n), ha='center', va='center', fontsize=10.5,
                weight='bold', color=edge)
        x += w
    x = 0.4
    offs = [(0.0, 1.22), (0.0, 0.88), (0.0, 1.22), (0.0, 0.88)]
    for (name, n, face, edge), (_, yy) in zip(blocks, offs):
        w = span * n / total
        ax.plot([x + w / 2, x + w / 2], [1.52, yy + 0.16], color=edge, lw=0.9)
        ax.text(x + w / 2, yy, f'{name}\n{n} tokens', ha='center', va='top',
                fontsize=9.5, color=edge)
        x += w
    ax.text(0.4, 2.58, 'the model sees one flat row of tokens and cannot tell '
            'from the row alone which ones came from a picture',
            ha='left', fontsize=10, color=MUTED)
    ax.annotate('', xy=(11.0, 2.42), xytext=(0.4, 2.42),
                arrowprops=dict(arrowstyle='-|>', color=MUTED, lw=1.0))
    _save(fig, VLM_DOC, 'token-stream.svg')
    print(f'[3a] stream: {SYS_TOKENS} system + {PIC_TOKENS} picture + {Q_TOKENS} '
          f'question + {A_TOKENS} answer = {total} tokens; the picture is '
          f'{100 * PIC_TOKENS / total:.0f}% of it')


def vlm_context_share() -> None:
    """How much of the context each way of sending a picture eats."""
    schemes = [f'one squeezed crop\n{PIC_TOKENS} tokens',
               f'{HI} x {HI} in {TILES_HI} crops\nplus a thumbnail\n'
               f'{_thousands(TOK_HI)} tokens',
               f'{CAM_W} x {CAM_H} frame in {TILES_CAM} crops\nplus a thumbnail\n'
               f'{_thousands(TOK_CAM)} tokens']
    toks = [PIC_TOKENS, TOK_HI, TOK_CAM]
    fig: Figure = plt.figure(figsize=(10.4, 4.0))
    ax: Axes = fig.add_axes((0.08, 0.26, 0.88, 0.56))
    _plain(ax)
    y = np.arange(3)
    ax.barh(y, [CONTEXT] * 3, color='#eeeeee', height=0.52)
    bars = ax.barh(y, toks, color=[TEAL, WRIST, GRIP], height=0.52)
    ax.set_yticks(y)
    ax.set_yticklabels(schemes, fontsize=9.3)
    ax.set_xlim(0, CONTEXT * 1.04)
    ax.set_xlabel(f'tokens, against a context window of {_thousands(CONTEXT)}',
                  fontsize=10)
    ax.invert_yaxis()
    for b, v in zip(bars, toks):
        ax.text(v + CONTEXT * 0.012, b.get_y() + b.get_height() / 2,
                f'{100 * v / CONTEXT:.1f}% of the window', va='center', fontsize=9.5,
                color=INK)
    ax.set_title('One high resolution camera frame can fill most of the window',
                 fontsize=12, weight='bold')
    _save(fig, VLM_DOC, 'context-share.svg')
    print(f'[3b] context share of {_thousands(CONTEXT)}: one crop '
          f'{100 * PIC_TOKENS / CONTEXT:.2f}%, tiled {HI} '
          f'{100 * TOK_HI / CONTEXT:.2f}%, tiled camera frame '
          f'{100 * TOK_CAM / CONTEXT:.2f}%')


def vlm_pictures_that_fit() -> None:
    """How many pictures fit in a small and a large context window."""
    labels = ['one squeezed crop', f'{HI} x {HI} tiled',
              f'{CAM_W} x {CAM_H} tiled']
    toks = [PIC_TOKENS, TOK_HI, TOK_CAM]
    small = [CONTEXT // t for t in toks]
    big = [BIG_CONTEXT // t for t in toks]
    fig: Figure = plt.figure(figsize=(9.6, 4.0))
    ax: Axes = fig.add_axes((0.08, 0.17, 0.88, 0.64))
    _plain(ax)
    x = np.arange(3)
    b1 = ax.bar(x - 0.19, small, width=0.36, color=TEAL,
                label=f'{_thousands(CONTEXT)} token window')
    b2 = ax.bar(x + 0.19, big, width=0.36, color=PURPLE,
                label=f'{_thousands(BIG_CONTEXT)} token window')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel('pictures that fit (log scale)', fontsize=10)
    ax.set_ylim(0.6, 1500)
    for bars, vals in ((b1, small), (b2, big)):
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.2, str(v), ha='center',
                    fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('A tiled camera frame leaves almost no room for a second picture',
                 fontsize=12, weight='bold')
    _save(fig, VLM_DOC, 'pictures-that-fit.svg')
    print(f'[3c] pictures that fit in {_thousands(CONTEXT)}: {small}; '
          f'in {_thousands(BIG_CONTEXT)}: {big}')


def vlm_attention_cost() -> None:
    """Attention work grows with the square of the stream, so pictures hurt twice."""
    n_pics = np.arange(0, 9)
    base = SYS_TOKENS + Q_TOKENS
    one = base + n_pics * PIC_TOKENS
    tiled = base + n_pics * TOK_HI
    fig: Figure = plt.figure(figsize=(9.8, 4.0))
    ax: Axes = fig.add_axes((0.10, 0.17, 0.86, 0.64))
    _plain(ax)
    ax.plot(n_pics, one.astype(float) ** 2 / 1e6, 'o-', color=TEAL, lw=1.8,
            label=f'squeezed crops, {PIC_TOKENS} tokens each')
    ax.plot(n_pics, tiled.astype(float) ** 2 / 1e6, 's-', color=GRIP, lw=1.8,
            label=f'tiled {HI} pictures, {_thousands(TOK_HI)} tokens each')
    ax.set_xlabel('pictures in the conversation', fontsize=10)
    ax.set_ylabel('attention pairs, in millions', fontsize=10)
    ax.set_title('Attention compares every token with every other, '
                 'so the cost is the square of the length',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_ylim(-20, float(tiled[8] ** 2 / 1e6) * 1.18)
    for k in (2, 5):
        ax.annotate(f'{tiled[k] ** 2 / 1e6:.1f}M', xy=(k, tiled[k] ** 2 / 1e6),
                    xytext=(k - 0.45, tiled[k] ** 2 / 1e6 + 22), fontsize=9,
                    color=GRIP)
    ax.annotate(f'{tiled[8] ** 2 / 1e6:.0f}M', xy=(8, tiled[8] ** 2 / 1e6),
                xytext=(6.9, tiled[8] ** 2 / 1e6 * 0.86), fontsize=9, color=GRIP)
    ax.annotate(f'{one[8] ** 2 / 1e6:.2f}M', xy=(8, one[8] ** 2 / 1e6),
                xytext=(6.6, 40), fontsize=9, color=TEAL,
                arrowprops=dict(arrowstyle='-', color=TEAL, lw=0.8))
    _save(fig, VLM_DOC, 'attention-cost.svg')
    print(f'[3d] attention pairs with 8 pictures: squeezed {one[8] ** 2:,}, '
          f'tiled {tiled[8] ** 2:,}, which is '
          f'{(tiled[8] ** 2) / (one[8] ** 2):.0f} times as much work')


# -- section 4: the training order -----------------------------------------

BYTES_WEIGHT: int = 2       # one parameter kept in bfloat16
BYTES_TRAINED: int = 14     # gradient in bfloat16 plus two Adam moments and a
                            # float32 copy, for each parameter that is trained


def vlm_freeze_stages() -> None:
    """The two stages, with the parameters that move in each one."""
    fig: Figure = plt.figure(figsize=(11.2, 4.6))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.6)
    stages = [
        (0.4, 'Stage 1: train the projector only',
         [('backbone', V_PARAMS, False), ('projector', PROJ_1, True),
          ('language model', L_PARAMS, False)]),
        (5.9, 'Stage 2: unfreeze the language model',
         [('backbone', V_PARAMS, False), ('projector', PROJ_1, True),
          ('language model', L_PARAMS, True)]),
    ]
    for x0, title, parts in stages:
        ax.text(x0 + 2.4, 4.2, title, ha='center', fontsize=12, weight='bold')
        y = 3.3
        for name, n, trained in parts:
            face = '#fdf0d5' if trained else '#eeeeee'
            edge = JOINT if trained else MUTED
            word = 'trained' if trained else 'frozen'
            _box(ax, x0, y, 4.8, 0.78,
                 f'{name}:  {_thousands(n)} parameters,  {word}',
                 face=face, edge=edge, size=10.2,
                 weight='bold' if trained else 'normal')
            y -= 0.95
        moved = sum(n for _, n, t in parts if t)
        total = sum(n for _, n, _ in parts)
        ax.text(x0 + 2.4, 0.95, f'{_thousands(moved)} parameters move,\n'
                f'which is {100 * moved / total:.3f}% of the model',
                ha='center', fontsize=10.5, color=GRIP)
    ax.text(5.65, 2.3, '→', ha='center', va='center', fontsize=26, color=MUTED)
    ax.text(5.6, 0.25, 'the backbone usually stays frozen through both stages, and '
            'its last few blocks are unfrozen only if the pictures are unusual',
            ha='center', fontsize=9.8, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'freeze-stages.svg')
    print(f'[4a] stage 1 moves {_thousands(PROJ_1)} parameters '
          f'({100 * PROJ_1 / (V_PARAMS + L_PARAMS + PROJ_1):.3f}%), stage 2 moves '
          f'{_thousands(PROJ_1 + L_PARAMS)} '
          f'({100 * (PROJ_1 + L_PARAMS) / (V_PARAMS + L_PARAMS + PROJ_1):.2f}%)')


def vlm_stage_memory() -> None:
    """What each stage needs in memory, worked out from the parameter counts."""
    total = V_PARAMS + L_PARAMS + PROJ_1
    held = total * BYTES_WEIGHT
    trained = [PROJ_1, PROJ_1 + L_PARAMS, total]
    names = ['stage 1\nprojector only', 'stage 2\nprojector and\nlanguage model',
             'everything at once\nincluding the backbone']
    extra = [t * BYTES_TRAINED for t in trained]
    gb = 1024 ** 3
    fig: Figure = plt.figure(figsize=(9.6, 4.2))
    ax: Axes = fig.add_axes((0.09, 0.22, 0.87, 0.60))
    _plain(ax)
    ax.bar(names, [held / gb] * 3, color='#cccccc', width=0.5,
           label='the weights themselves, 2 bytes each')
    ax.bar(names, [e / gb for e in extra], bottom=[held / gb] * 3, color=GRIP,
           width=0.5, label='gradients and optimiser state, 14 bytes per trained parameter')
    ax.set_ylabel('memory needed, in gibibytes', fontsize=10)
    for i, e in enumerate(extra):
        ax.text(i, (held + e) / gb + 2.0, f'{(held + e) / gb:.1f} GiB', ha='center',
                fontsize=10, weight='bold')
    ax.set_ylim(0, max((held + e) / gb for e in extra) * 1.45)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.tick_params(axis='x', labelsize=9)
    ax.set_title('Freezing the big parts is what makes the first stage fit on '
                 'one graphics card', fontsize=11.5, weight='bold')
    _save(fig, VLM_DOC, 'stage-memory.svg')
    print(f'[4b] memory: weights {held / gb:.2f} GiB; stage 1 total '
          f'{(held + extra[0]) / gb:.2f} GiB; stage 2 total '
          f'{(held + extra[1]) / gb:.1f} GiB; everything at once '
          f'{(held + extra[2]) / gb:.1f} GiB')


class OrderRun:
    """A real small training run that shows why the projector is trained first.

    The simulated set-up mirrors the real one. A 'language model body' is a two
    layer network that has already been trained on a made-up text task, so it
    starts out good at that task. A 'projector' is a matrix that must learn to
    turn made-up picture vectors into something the body can read. The picture
    vectors, the text vectors and the two tasks are drawn with
    numpy.random.default_rng(21). Everything else is real gradient descent
    written out in NumPy, so the curves are the real result of the two orders.
    """

    D_V: int = 16
    D_L: int = 24
    D_H: int = 32
    D_OUT: int = 8
    STEPS: int = 260
    SWITCH: int = 130

    def __init__(self) -> None:
        rng = np.random.default_rng(21)
        self.rng = rng
        self.text = rng.normal(0, 1, size=(self.D_L, 256))
        self.pics = rng.normal(0, 1, size=(self.D_V, 256))
        self.a_text = rng.normal(0, 0.6, size=(self.D_OUT, self.D_L))
        self.a_pic = rng.normal(0, 0.6, size=(self.D_OUT, self.D_V))
        self.t_text = self.a_text @ self.text
        self.t_pic = self.a_pic @ self.pics
        self.w1 = rng.normal(0, 0.25, size=(self.D_H, self.D_L))
        self.b1 = np.zeros((self.D_H, 1))
        self.w2 = rng.normal(0, 0.25, size=(self.D_OUT, self.D_H))
        self.b2 = np.zeros((self.D_OUT, 1))
        self._pretrain_on_text(1400, 0.05)
        self.body0 = (self.w1.copy(), self.b1.copy(), self.w2.copy(), self.b2.copy())
        self.proj0 = rng.normal(0, 0.25, size=(self.D_L, self.D_V))

    def _forward(self, z: Arr, body: tuple[Arr, Arr, Arr, Arr]
                 ) -> tuple[Arr, Arr, Arr]:
        w1, b1, w2, b2 = body
        a = w1 @ z + b1
        h = np.maximum(a, 0.0)
        return w2 @ h + b2, a, h

    def _pretrain_on_text(self, steps: int, lr: float) -> None:
        body = (self.w1, self.b1, self.w2, self.b2)
        for _ in range(steps):
            y, a, h = self._forward(self.text, body)
            d = (y - self.t_text) / self.text.shape[1]
            g_w2 = d @ h.T
            g_b2 = d.sum(axis=1, keepdims=True)
            da = (self.w2.T @ d) * (a > 0)
            self.w2 -= lr * g_w2
            self.b2 -= lr * g_b2
            self.w1 -= lr * (da @ self.text.T)
            self.b1 -= lr * da.sum(axis=1, keepdims=True)

    def _loss(self, y: Arr, t: Arr) -> float:
        return float(0.5 * np.mean(np.sum((y - t) ** 2, axis=0)))

    def run(self, freeze_first: bool, lr: float = 0.03
            ) -> tuple[Arr, Arr]:
        body = tuple(m.copy() for m in self.body0)
        proj = self.proj0.copy()
        pic_loss, text_loss = [], []
        for step in range(self.STEPS):
            w1, b1, w2, b2 = body
            z = proj @ self.pics
            y, a, h = self._forward(z, body)
            pic_loss.append(self._loss(y, self.t_pic))
            yt, _, _ = self._forward(self.text, body)
            text_loss.append(self._loss(yt, self.t_text))
            d = (y - self.t_pic) / self.pics.shape[1]
            g_w2 = d @ h.T
            g_b2 = d.sum(axis=1, keepdims=True)
            da = (w2.T @ d) * (a > 0)
            g_w1 = da @ z.T
            g_b1 = da.sum(axis=1, keepdims=True)
            g_proj = (w1.T @ da) @ self.pics.T
            proj -= lr * g_proj
            unfrozen = (not freeze_first) or step >= self.SWITCH
            if unfrozen:
                mix = 0.5
                dt = (yt - self.t_text) / self.text.shape[1]
                _, at, ht = self._forward(self.text, body)
                t_w2 = dt @ ht.T
                t_b2 = dt.sum(axis=1, keepdims=True)
                dat = (w2.T @ dt) * (at > 0)
                keep = mix
                w2 -= lr * (g_w2 + keep * t_w2)
                b2 -= lr * (g_b2 + keep * t_b2)
                w1 -= lr * (g_w1 + keep * (dat @ self.text.T))
                b1 -= lr * (g_b1 + keep * dat.sum(axis=1, keepdims=True))
        return np.array(pic_loss), np.array(text_loss)


ORDER: OrderRun | None = None


def _order() -> OrderRun:
    global ORDER
    if ORDER is None:
        ORDER = OrderRun()
    return ORDER


def vlm_order_curves() -> None:
    """The real curves from the small run: the wrong order damages the reading half."""
    run = _order()
    p_good, t_good = run.run(freeze_first=True)
    p_bad, t_bad = run.run(freeze_first=False)
    steps = np.arange(run.STEPS)
    fig: Figure = plt.figure(figsize=(10.6, 4.3))
    ax1: Axes = fig.add_axes((0.08, 0.18, 0.38, 0.62))
    ax2: Axes = fig.add_axes((0.58, 0.18, 0.38, 0.62))
    _plain(ax1)
    _plain(ax2)
    ax1.plot(steps, p_good, color=TEAL, lw=1.9, label='freeze first, then unfreeze')
    ax1.plot(steps, p_bad, color=GRIP, lw=1.9, ls='--', label='train everything at once')
    ax1.axvline(run.SWITCH, color=MUTED, lw=0.9, ls=':')
    ax1.text(run.SWITCH + 5, max(p_good.max(), p_bad.max()) * 0.85,
             'unfreeze', fontsize=9, color=MUTED)
    ax1.set_xlabel('training step', fontsize=10)
    ax1.set_ylabel('loss on the picture task', fontsize=10)
    ax1.set_yscale('log')
    ax1.set_title('Both orders end up reading the pictures', fontsize=11.5,
                  weight='bold')
    ax1.legend(fontsize=8.8, frameon=False)
    ax2.plot(steps, t_good, color=TEAL, lw=1.9, label='freeze first, then unfreeze')
    ax2.plot(steps, t_bad, color=GRIP, lw=1.9, ls='--', label='train everything at once')
    ax2.axvline(run.SWITCH, color=MUTED, lw=0.9, ls=':')
    ax2.set_xlabel('training step', fontsize=10)
    ax2.set_ylabel('loss on the old text task', fontsize=10)
    ax2.set_yscale('log')
    ax2.set_title('Only one of them keeps what the model already knew',
                  fontsize=11.5, weight='bold')
    ax2.annotate(f'rises to {t_bad.max():.2f}', xy=(float(np.argmax(t_bad)), t_bad.max()),
                 xytext=(60, t_bad.max() * 1.05), fontsize=9, color=GRIP)
    ax2.legend(fontsize=8.8, frameon=False)
    fig.text(0.5, 0.005, 'a real small NumPy training run on a simulated task, seed 21',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'order-curves.svg')
    print(f'[4c] simulated run: text loss starts at {t_good[0]:.4f}; '
          f'freeze-first never rises above {t_good.max():.4f} and ends at '
          f'{t_good[-1]:.4f}; all-at-once rises to {t_bad.max():.3f}, which is '
          f'{t_bad.max() / t_good[0]:.0f} times its starting value, and ends at '
          f'{t_bad[-1]:.4f}. picture loss starts at {p_good[0]:.1f} and ends at '
          f'{p_good[-1]:.4f} and {p_bad[-1]:.4f}')


# -- section 5: resolution and tiling --------------------------------------

LABEL_X0: int = 300
LABEL_Y0: int = 250
LABEL_W: int = 80
LABEL_H: int = 32
CHAR_H: int = 10            # a character on the label is 5 mm tall
STROKE_W: int = 2           # a stroke of that character is 1 mm wide
SCREW_D: int = 12           # a 6 mm screw head


def _scene() -> Arr:
    """A simulated workbench picture of HI x HI pixels, drawn as an array.

    The speckle is numpy.random.default_rng(7). Everything else is drawn from
    the sizes above, so the bottle, the printed label and the screw head are
    exactly the number of pixels across that MM_PER_PIXEL makes them.
    """
    rng = np.random.default_rng(7)
    img = np.full((HI, HI), 0.74) + rng.normal(0, 0.016, size=(HI, HI))
    img[int(HI * 0.62):, :] *= 0.86                     # the darker table front
    img[150:470, 266:406] = 0.34                        # the bottle body
    img[120:150, 310:362] = 0.28                        # the bottle neck
    img[LABEL_Y0:LABEL_Y0 + LABEL_H, LABEL_X0:LABEL_X0 + LABEL_W] = 0.95
    x = LABEL_X0 + 4
    while x < LABEL_X0 + LABEL_W - 6:
        for s in (0, 3):
            img[LABEL_Y0 + 8:LABEL_Y0 + 8 + CHAR_H, x + s:x + s + STROKE_W] = 0.10
        img[LABEL_Y0 + 8 + CHAR_H // 2:LABEL_Y0 + 10 + CHAR_H // 2,
            x:x + 5] = 0.10
        x += 7
    yy, xx = np.mgrid[0:HI, 0:HI]
    screw = ((yy - 500) ** 2 + (xx - 180) ** 2) < (SCREW_D / 2) ** 2
    img[screw] = 0.18
    return np.clip(img, 0.0, 1.0)


def _block_mean(img: Arr, k: int) -> Arr:
    """Shrink a picture by averaging every k by k block, which is what resizing does."""
    n = img.shape[0] // k
    return img[:n * k, :n * k].reshape(n, k, n, k).mean(axis=(1, 3))


def _text_band(full: Arr, small: Arr) -> tuple[float, float]:
    """Brightness spread across the printed line, before and after squeezing.

    A line of print is a run of dark strokes and light gaps, so the standard
    deviation of the brightness across that band says how much of the print has
    survived. It falls when the strokes are averaged together with the gaps.
    """
    y0, x0 = LABEL_Y0 + 8, LABEL_X0 + 4
    band_f = full[y0:y0 + CHAR_H, x0:x0 + LABEL_W - 10]
    band_s = small[y0 // SQUEEZE:(y0 + CHAR_H) // SQUEEZE,
                   x0 // SQUEEZE:(x0 + LABEL_W - 10) // SQUEEZE]
    return float(band_f.std()), float(band_s.std())


def vlm_squeezed_picture() -> None:
    """The same label at full size and after being squeezed to the model's square."""
    full = _scene()
    small = _block_mean(full, SQUEEZE)
    c_full, c_small = _text_band(full, small)
    lab_full = full[LABEL_Y0 - 4:LABEL_Y0 + LABEL_H + 4,
                    LABEL_X0 - 4:LABEL_X0 + LABEL_W + 4]
    lab_small = small[(LABEL_Y0 - 4) // SQUEEZE:(LABEL_Y0 + LABEL_H + 4) // SQUEEZE,
                      (LABEL_X0 - 4) // SQUEEZE:(LABEL_X0 + LABEL_W + 4) // SQUEEZE]
    fig: Figure = plt.figure(figsize=(11.2, 4.6))
    ax1: Axes = fig.add_axes((0.02, 0.09, 0.27, 0.74))
    ax2: Axes = fig.add_axes((0.31, 0.09, 0.27, 0.74))
    ax3: Axes = fig.add_axes((0.63, 0.52, 0.34, 0.31))
    ax4: Axes = fig.add_axes((0.63, 0.11, 0.34, 0.31))
    for ax in (ax1, ax2, ax3, ax4):
        _blank(ax)
    ax1.imshow(full, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax1.add_patch(Rectangle((LABEL_X0 - 4, LABEL_Y0 - 4), LABEL_W + 8, LABEL_H + 8,
                            facecolor='none', edgecolor=GRIP, lw=1.6))
    ax1.set_title(f'{HI} x {HI} camera picture', fontsize=11, weight='bold')
    ax2.imshow(small, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax2.add_patch(Rectangle(((LABEL_X0 - 4) / SQUEEZE, (LABEL_Y0 - 4) / SQUEEZE),
                            (LABEL_W + 8) / SQUEEZE, (LABEL_H + 8) / SQUEEZE,
                            facecolor='none', edgecolor=GRIP, lw=1.6))
    ax2.set_title(f'squeezed to {SIDE} x {SIDE}', fontsize=11, weight='bold')
    ax3.imshow(lab_full, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax3.set_title(f'the label at full size: strokes {STROKE_W} pixels wide,\n'
                  f'spread across the printed line {c_full:.3f}',
                  fontsize=10, weight='bold')
    ax4.imshow(lab_small, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    ax4.set_title(f'the same label squeezed: strokes {STROKE_W / SQUEEZE:.2f} pixels '
                  f'wide,\nspread across the printed line {c_small:.3f}',
                  fontsize=10, weight='bold')
    fig.text(0.5, 0.005, f'simulated picture, seed 7; squeezing is a real {SQUEEZE} '
             f'by {SQUEEZE} block average',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'squeezed-picture.svg')
    print(f'[5a] spread across the printed line {c_full:.3f} at {HI} pixels and '
          f'{c_small:.3f} after squeezing to {SIDE}, a fall of '
          f'{100 * (1 - c_small / c_full):.0f}%; a {CHAR_H}-pixel character becomes '
          f'{CHAR_H / SQUEEZE:.1f} pixels tall')


def vlm_tiling_layout() -> None:
    """The crops a tiled picture is cut into, and what each one costs in tokens."""
    full = _scene()
    fig: Figure = plt.figure(figsize=(11.0, 4.6))
    ax1: Axes = fig.add_axes((0.03, 0.08, 0.36, 0.78))
    ax2: Axes = fig.add_axes((0.44, 0.08, 0.17, 0.78))
    ax3: Axes = fig.add_axes((0.655, 0.10, 0.33, 0.74))
    for ax in (ax1, ax2):
        _blank(ax)
    _blank(ax3)
    ax1.imshow(full, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    n = HI // SIDE
    for i in range(n):
        for j in range(n):
            ax1.add_patch(Rectangle((j * SIDE, i * SIDE), SIDE, SIDE, facecolor='none',
                                    edgecolor=JOINT, lw=1.6))
            ax1.text(j * SIDE + SIDE / 2, i * SIDE + SIDE / 2, f'{PIC_TOKENS}',
                     ha='center', va='center', fontsize=12, color=JOINT,
                     weight='bold')
    ax1.set_title(f'{TILES_HI} crops of {SIDE} x {SIDE}, each {PIC_TOKENS} tokens',
                  fontsize=11, weight='bold')
    ax2.imshow(_block_mean(full, SQUEEZE), cmap='gray', vmin=0, vmax=1,
               interpolation='nearest')
    ax2.set_title(f'one whole-picture\nthumbnail,\n{PIC_TOKENS} tokens',
                  fontsize=10.5, weight='bold')
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    rows = [(f'{TILES_HI} crops x {PIC_TOKENS} tokens', TILES_HI * PIC_TOKENS),
            (f'1 thumbnail x {PIC_TOKENS} tokens', PIC_TOKENS),
            ('total for one picture', TOK_HI)]
    y = 8.0
    for name, val in rows:
        bold = name.startswith('total')
        ax3.text(0.2, y, name, fontsize=11, color=INK,
                 weight='bold' if bold else 'normal')
        ax3.text(9.8, y, _thousands(val), fontsize=11, ha='right', color=GRIP if bold else INK,
                 weight='bold' if bold else 'normal')
        if bold:
            ax3.plot([0.2, 9.8], [y + 0.85, y + 0.85], color=INK, lw=0.9)
        y -= 1.7
    ax3.text(0.2, 2.4, f'that is {TOK_HI // PIC_TOKENS} times the tokens of the\n'
             f'squeezed picture, and it buys\n{SQUEEZE} times the detail in each '
             'direction', fontsize=10.5, color=MUTED, va='top')
    ax3.set_title('The bill for one tiled picture', fontsize=11.5, weight='bold')
    _save(fig, VLM_DOC, 'tiling-layout.svg')
    print(f'[5b] tiling {HI}: {TILES_HI} crops + 1 thumbnail = '
          f'{TILES_HI + 1} crops = {_thousands(TOK_HI)} tokens, '
          f'{TOK_HI // PIC_TOKENS} times one squeezed crop')


def vlm_token_bill() -> None:
    """Tokens spent against detail kept, for the three ways of sending a picture."""
    names = [f'squeeze {HI} to {SIDE}', f'tile {HI} into {TILES_HI} + 1',
             f'tile the {CAM_W} x {CAM_H} frame\ninto {TILES_CAM} + 1']
    toks = [PIC_TOKENS, TOK_HI, TOK_CAM]
    px = [PX_PER_PATCH_SQ, PX_PER_PATCH_TILE, PX_PER_PATCH_TILE]
    fig: Figure = plt.figure(figsize=(10.4, 4.1))
    ax1: Axes = fig.add_axes((0.07, 0.24, 0.38, 0.58))
    ax2: Axes = fig.add_axes((0.58, 0.24, 0.38, 0.58))
    _plain(ax1)
    _plain(ax2)
    b1 = ax1.bar(names, toks, color=[TEAL, WRIST, GRIP], width=0.55)
    ax1.set_ylabel('tokens for one picture', fontsize=10)
    ax1.set_title('What it costs', fontsize=11.5, weight='bold')
    for b, v in zip(b1, toks):
        ax1.text(b.get_x() + b.get_width() / 2, v + max(toks) * 0.03, _thousands(v),
                 ha='center', fontsize=10)
    ax1.set_ylim(0, max(toks) * 1.2)
    b2 = ax2.bar(names, [p * MM_PER_PIXEL for p in px],
                 color=[TEAL, WRIST, GRIP], width=0.55)
    ax2.set_ylabel('millimetres of table under one patch', fontsize=10)
    ax2.set_title('What it buys', fontsize=11.5, weight='bold')
    for b, p in zip(b2, px):
        ax2.text(b.get_x() + b.get_width() / 2, p * MM_PER_PIXEL + 0.8,
                 f'{p} pixels\n{p * MM_PER_PIXEL:.0f} mm', ha='center', fontsize=9.5)
    ax2.set_ylim(0, max(px) * MM_PER_PIXEL * 1.35)
    ax1.tick_params(axis='x', labelsize=8.6)
    ax2.tick_params(axis='x', labelsize=8.6)
    _save(fig, VLM_DOC, 'token-bill.svg')
    print(f'[5c] one patch covers {PX_PER_PATCH_SQ} original pixels '
          f'({PX_PER_PATCH_SQ * MM_PER_PIXEL:.0f} mm of table) when the picture is '
          f'squeezed, and {PX_PER_PATCH_TILE} pixels '
          f'({PX_PER_PATCH_TILE * MM_PER_PIXEL:.0f} mm) when it is tiled')


def vlm_detail_curve() -> None:
    """Tokens against detail as a camera frame is cut into more and more crops."""
    across = np.arange(1, 7)
    down = np.ceil(across * CAM_H / CAM_W).astype(int)
    crops = across * down
    toks = (crops + 1) * PIC_TOKENS
    covered = across * SIDE
    scale = np.maximum(CAM_W / covered, 1.0)
    mm = PATCH * MM_PER_PIXEL * scale
    fig: Figure = plt.figure(figsize=(10.0, 4.3))
    ax: Axes = fig.add_axes((0.10, 0.17, 0.78, 0.64))
    _plain(ax)
    ax.plot(toks, mm, 'o-', color=GRIP, lw=1.9)
    for a, d, t, m in zip(across, down, toks, mm):
        dy = 1.6 if a < 5 else 5.0
        ax.annotate(f'{a} x {d} crops\n{_thousands(int(t))} tokens',
                    xy=(t, m), xytext=(t + 180, m + dy), fontsize=8.8, color=INK)
    ax.set_xlabel(f'tokens spent on one {CAM_W} x {CAM_H} camera frame', fontsize=10)
    ax.set_ylabel('millimetres of table under one patch', fontsize=10)
    ax.set_xlim(0, toks.max() * 1.30)
    ax.set_ylim(0, mm.max() * 1.28)
    ax.axhline(PATCH * MM_PER_PIXEL, color=MUTED, lw=0.9, ls=':')
    ax.text(toks.max() * 0.03, PATCH * MM_PER_PIXEL - 2.6,
            f'{PATCH * MM_PER_PIXEL:.0f} mm, the limit the camera itself sets',
            fontsize=9, color=MUTED, ha='left')
    ax.set_title('Detail improves with the square root of the tokens spent, and '
                 f'stops at the camera\'s own {PATCH * MM_PER_PIXEL:.0f} mm',
                 fontsize=11.5, weight='bold')
    _save(fig, VLM_DOC, 'detail-curve.svg')
    print('[5d] crops, tokens, mm under one patch: '
          + '; '.join(f'{a}x{d}={_thousands(int(t))} tok, {m:.1f} mm'
                      for a, d, t, m in zip(across, down, toks, mm)))


# -- section 6: what it is weak at -----------------------------------------

def vlm_position_grain() -> None:
    """The finest position the token stream can name, drawn as the patch grid."""
    full = _scene()
    fig: Figure = plt.figure(figsize=(11.0, 4.7))
    ax1: Axes = fig.add_axes((0.02, 0.11, 0.28, 0.72))
    ax2: Axes = fig.add_axes((0.33, 0.11, 0.28, 0.72))
    ax3: Axes = fig.add_axes((0.66, 0.10, 0.33, 0.74))
    for ax in (ax1, ax2, ax3):
        _blank(ax)
    for ax, step, name in ((ax1, PX_PER_PATCH_SQ, 'squeezed'),
                           (ax2, PX_PER_PATCH_TILE * 2, 'tiled')):
        ax.imshow(full, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
        for k in range(0, HI + 1, step):
            ax.axvline(k, color=LINK, lw=0.35, alpha=0.8)
            ax.axhline(k, color=LINK, lw=0.35, alpha=0.8)
        ax.set_xlim(0, HI)
        ax.set_ylim(HI, 0)
    ax1.set_title(f'squeezed: one patch is {PX_PER_PATCH_SQ} pixels, '
                  f'{PX_PER_PATCH_SQ * MM_PER_PIXEL:.0f} mm', fontsize=10.2,
                  weight='bold')
    ax2.set_title(f'tiled: one patch is {PX_PER_PATCH_TILE} pixels, '
                  f'{PX_PER_PATCH_TILE * MM_PER_PIXEL:.0f} mm', fontsize=10.2,
                  weight='bold')
    fig.text(0.47, 0.045, 'on the right only every second patch line is drawn, so '
             'that the grid stays visible', ha='center', fontsize=9, color=MUTED,
             style='italic')
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    ax3.set_title('Out comes words, not pixels', fontsize=11.5, weight='bold')
    ax3.text(0.2, 8.9, 'asked "where is the bottle?" the model\nwrites one of these:',
             fontsize=10.3, va='top', color=INK)
    for i, s in enumerate(['"in the middle of the bench"',
                           '"just left of centre, standing up"',
                           '"about a third of the way across"']):
        ax3.text(0.6, 7.1 - i * 0.85, s, fontsize=10, color=PURPLE)
    ax3.text(0.2, 4.0, f'a detector writes this instead:', fontsize=10.3, color=INK)
    ax3.text(0.6, 3.1, 'box = (266, 150, 406, 470)\nin pixels, to the pixel',
             fontsize=10, color=TEAL, family='DejaVu Sans Mono')
    ax3.text(0.2, 1.5, f'the words can be turned into a number no\n'
             f'finer than one patch, which is '
             f'{PX_PER_PATCH_SQ * MM_PER_PIXEL:.0f} mm when\nthe picture is squeezed',
             fontsize=9.8, color=GRIP, va='top')
    _save(fig, VLM_DOC, 'position-grain.svg')
    print(f'[6a] finest position a patch-level answer can name: '
          f'{PX_PER_PATCH_SQ} pixels / {PX_PER_PATCH_SQ * MM_PER_PIXEL:.0f} mm '
          f'squeezed, {PX_PER_PATCH_TILE} pixels / '
          f'{PX_PER_PATCH_TILE * MM_PER_PIXEL:.0f} mm tiled')


def vlm_object_size() -> None:
    """How many patches an object of a given size covers, and when text survives."""
    mm = np.linspace(2, 160, 300)
    px = mm / MM_PER_PIXEL
    sq = (px / PX_PER_PATCH_SQ) ** 2
    ti = (px / PX_PER_PATCH_TILE) ** 2
    marks = [('screw head, 6 mm', 6.0), ('bolt, 16 mm', 16.0),
             ('mug, 90 mm', 90.0)]
    fig: Figure = plt.figure(figsize=(10.6, 4.3))
    ax1: Axes = fig.add_axes((0.08, 0.18, 0.37, 0.62))
    ax2: Axes = fig.add_axes((0.58, 0.18, 0.37, 0.62))
    _plain(ax1)
    _plain(ax2)
    ax1.plot(mm, sq, color=TEAL, lw=1.9, label='squeezed picture')
    ax1.plot(mm, ti, color=GRIP, lw=1.9, label='tiled picture')
    ax1.axhline(1.0, color=MUTED, lw=1.0, ls=':')
    ax1.text(150, 1.4, 'one patch', fontsize=9, color=MUTED, ha='right')
    ax1.set_yscale('log')
    ax1.set_xlabel('size of the object on the table, in millimetres', fontsize=10)
    ax1.set_ylabel('patches it covers (log scale)', fontsize=10)
    ax1.set_title('An object smaller than one patch gets no token of its own',
                  fontsize=11, weight='bold')
    ax1.legend(fontsize=9, frameon=False, loc='lower right')
    for (name, v), ytext in zip(marks, (0.013, 2.2, 0.013)):
        ax1.axvline(v, color=INK, lw=0.6, ls='--', alpha=0.5)
        ax1.text(v + 2.5, ytext, name, rotation=90, fontsize=8.5, color=INK,
                 va='bottom',
                 bbox=dict(facecolor='white', edgecolor='none', pad=0.6))
    ax1.set_ylim(0.01, 500)

    # a stroke has to survive the shrink: it needs at least 3 pixels after it
    strokes_needed = 3
    min_stroke_sq = strokes_needed * SQUEEZE
    min_stroke_ti = strokes_needed
    min_char_sq = 5 * min_stroke_sq * MM_PER_PIXEL
    min_char_ti = 5 * min_stroke_ti * MM_PER_PIXEL
    actual = CHAR_H * MM_PER_PIXEL
    names = ['squeezed\npicture', 'tiled\npicture']
    vals = [min_char_sq, min_char_ti]
    bars = ax2.bar(names, vals, color=[TEAL, GRIP], width=0.45)
    ax2.axhline(actual, color=JOINT, lw=1.6)
    ax2.text(-0.42, actual - 1.0, f'the label on the bottle is only {actual:.1f} mm',
             fontsize=9.5, color=JOINT, ha='left', va='top')
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.6, f'{v:.1f} mm', ha='center',
                 fontsize=10)
    ax2.set_ylabel('smallest character the picture can carry, in mm', fontsize=10)
    ax2.set_ylim(0, max(vals) * 1.3)
    ax2.set_title('Printed text has to be this tall to survive', fontsize=11,
                  weight='bold')
    _save(fig, VLM_DOC, 'object-size.svg')
    print(f'[6b] patches covered: screw head {(6 / MM_PER_PIXEL / PX_PER_PATCH_SQ) ** 2:.3f} '
          f'squeezed and {(6 / MM_PER_PIXEL / PX_PER_PATCH_TILE) ** 2:.2f} tiled; '
          f'smallest character {min_char_sq:.1f} mm squeezed and {min_char_ti:.1f} mm '
          f'tiled, against the {actual:.1f} mm label')


def vlm_counting_grid() -> None:
    """Simulated tray of screws: how many share a patch under each scheme."""
    rng = np.random.default_rng(13)
    n = 26
    xs = rng.uniform(70, 230, size=n)
    ys = rng.uniform(470, 580, size=n)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(i):
            if keep[j] and (xs[i] - xs[j]) ** 2 + (ys[i] - ys[j]) ** 2 < 17 ** 2:
                keep[i] = False
    xs, ys = xs[keep], ys[keep]
    n = len(xs)

    def shared(step: int) -> tuple[int, int, list[tuple[int, int]]]:
        cells: dict[tuple[int, int], int] = {}
        for x, y in zip(xs, ys):
            k = (int(x // step), int(y // step))
            cells[k] = cells.get(k, 0) + 1
        crowded = [k for k, v in cells.items() if v > 1]
        return len(cells), len(crowded), crowded

    cells_sq, multi_sq, crowd_sq = shared(PX_PER_PATCH_SQ)
    cells_ti, multi_ti, crowd_ti = shared(PX_PER_PATCH_TILE)
    fig: Figure = plt.figure(figsize=(10.8, 4.5))
    ax1: Axes = fig.add_axes((0.04, 0.08, 0.30, 0.78))
    ax2: Axes = fig.add_axes((0.37, 0.08, 0.30, 0.78))
    ax3: Axes = fig.add_axes((0.72, 0.14, 0.26, 0.66))
    for ax in (ax1, ax2):
        _blank(ax)
        ax.set_xlim(56, 244)
        ax.set_ylim(592, 458)
        ax.scatter(xs, ys, s=38, color=GRIP, zorder=3)
    _plain(ax3)
    for ax, step, crowd, title in (
            (ax1, PX_PER_PATCH_SQ, crowd_sq,
             f'squeezed: {PX_PER_PATCH_SQ}-pixel patches,\n{cells_sq} patches hold the '
             f'{n} screws'),
            (ax2, PX_PER_PATCH_TILE, crowd_ti,
             f'tiled: {PX_PER_PATCH_TILE}-pixel patches,\n{cells_ti} patches hold the '
             f'{n} screws')):
        for cx, cy in crowd:
            ax.add_patch(Rectangle((cx * step, cy * step), step, step,
                                   facecolor='#f6cdcd', edgecolor='none', zorder=1))
        for k in range(0, 700, step):
            ax.axvline(k, color=LINK, lw=0.5, zorder=2)
            ax.axhline(k, color=LINK, lw=0.5, zorder=2)
        ax.set_title(title, fontsize=10.3, weight='bold')
    bars = ax3.bar(['squeezed', 'tiled'], [multi_sq, multi_ti], color=[TEAL, GRIP],
                   width=0.45)
    ax3.set_yticks(range(0, max(multi_sq, multi_ti) + 2))
    for b, v in zip(bars, (multi_sq, multi_ti)):
        ax3.text(b.get_x() + b.get_width() / 2, v + 0.08, str(v), ha='center',
                 fontsize=11, weight='bold')
    ax3.set_ylabel('patches holding more than one screw\n(shaded pink on the left)',
                   fontsize=9.2)
    ax3.set_ylim(0, max(multi_sq, multi_ti) + 1.2)
    ax3.set_title(f'Counting {n} screws', fontsize=11, weight='bold')
    fig.text(0.5, 0.005, 'simulated screw positions, seed 13', ha='center',
             fontsize=9, color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'counting-grid.svg')
    print(f'[6c] {n} simulated screws: squeezed they fall in {cells_sq} patches with '
          f'{multi_sq} patches holding more than one; tiled they fall in {cells_ti} '
          f'patches with {multi_ti} holding more than one')


def vlm_box_grain() -> None:
    """The detector's box against the coarsest box the patch grid can express."""
    full = _scene()
    box = (266, 150, 406, 470)          # the bottle, to the pixel
    step = PX_PER_PATCH_SQ
    coarse = (box[0] // step * step, box[1] // step * step,
              -(-box[2] // step) * step, -(-box[3] // step) * step)
    errs = [box[0] - coarse[0], box[1] - coarse[1],
            coarse[2] - box[2], coarse[3] - box[3]]
    sides = ['left', 'top', 'right', 'bottom']
    fig: Figure = plt.figure(figsize=(11.0, 4.5))
    ax1: Axes = fig.add_axes((0.02, 0.10, 0.28, 0.72))
    ax2: Axes = fig.add_axes((0.32, 0.10, 0.28, 0.72))
    ax3: Axes = fig.add_axes((0.68, 0.17, 0.30, 0.62))
    for ax in (ax1, ax2):
        _blank(ax)
        ax.imshow(full, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
        ax.set_xlim(180, 500)
        ax.set_ylim(560, 80)
    _plain(ax3)
    ax1.add_patch(Rectangle((box[0], box[1]), box[2] - box[0], box[3] - box[1],
                            facecolor='none', edgecolor=TEAL, lw=2.2))
    ax1.set_title('the detector returns\n'
                  f'({box[0]}, {box[1]}, {box[2]}, {box[3]}) in pixels',
                  fontsize=10.2, weight='bold')
    for k in range(0, HI + 1, step):
        ax2.axvline(k, color=LINK, lw=0.5)
        ax2.axhline(k, color=LINK, lw=0.5)
    ax2.add_patch(Rectangle((coarse[0], coarse[1]), coarse[2] - coarse[0],
                            coarse[3] - coarse[1], facecolor='none', edgecolor=GRIP,
                            lw=2.2))
    ax2.set_title('the finest box the patch grid can hold\n'
                  f'({coarse[0]}, {coarse[1]}, {coarse[2]}, {coarse[3]})',
                  fontsize=10.2, weight='bold')
    bars = ax3.bar(sides, [e * MM_PER_PIXEL for e in errs], color=GRIP, width=0.55)
    for b, e in zip(bars, errs):
        ax3.text(b.get_x() + b.get_width() / 2, e * MM_PER_PIXEL + 0.4,
                 f'{e} px\n{e * MM_PER_PIXEL:.0f} mm', ha='center', fontsize=9.3)
    ax3.axhline(5.0, color=SLIDE, lw=1.5)
    ax3.text(-0.45, 5.5, 'a 5 mm gripper tolerance', fontsize=9, color=SLIDE,
             ha='left')
    ax3.set_ylabel('how far the coarse box is out, in mm', fontsize=9.5)
    ax3.set_ylim(0, max(errs) * MM_PER_PIXEL * 1.45)
    ax3.set_title('Every side is outside what the gripper allows',
                  fontsize=11, weight='bold')
    _save(fig, VLM_DOC, 'box-grain.svg')
    print(f'[6d] detector box {box}; patch-aligned box {coarse}; errors in mm: '
          + ', '.join(f'{s} {e * MM_PER_PIXEL:.0f}' for s, e in zip(sides, errs)))


# -- section 7: what it gives a robot that a detector cannot ---------------

CLASS_LIST: list[str] = ['person', 'bottle', 'cup', 'bowl', 'knife', 'spoon',
                         'book', 'laptop', 'chair', 'scissors', 'banana', 'clock']

BENCH: list[str] = [
    'bottle', 'cup', 'cup', 'bowl', 'spoon', 'scissors', 'book',
    'hex key', 'torque wrench', 'cable tie', 'anti-static bag', 'solder reel',
    'calibration target', 'spare gripper pad', 'the lid of the cup',
    'a cup with a chip in its rim', 'a cup lying on its side',
    'a bottle with no label', 'a half-full bottle', 'the bottle nearest the edge',
    'a screw on the floor', 'a puddle of water', 'a cardboard offcut',
    'the tray the cups came in', 'a sticky note', 'a dropped cable',
    'the bin', 'a glove', 'a label peeled off a bottle', 'a chipped tile',
]


def vlm_class_list() -> None:
    """How much of a real bench falls outside a fixed class list."""
    inside = [b for b in BENCH if b in CLASS_LIST]
    outside = [b for b in BENCH if b not in CLASS_LIST]
    fig: Figure = plt.figure(figsize=(9.2, 5.5))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 5.5)
    ax.text(4.6, 5.22, f'{len(BENCH)} things listed on one workbench, against a '
            f'detector trained on {len(CLASS_LIST)} class names', ha='center',
            fontsize=12.3, weight='bold')
    ax.text(0.3, 4.72, f'{len(inside)} the detector has a name for '
            f'({100 * len(inside) / len(BENCH):.0f}%)', fontsize=11, color=TEAL,
            weight='bold')
    ax.text(0.5, 4.36, ', '.join(inside), fontsize=10, color=TEAL)
    ax.text(0.3, 3.90, f'{len(outside)} it does not '
            f'({100 * len(outside) / len(BENCH):.0f}%)', fontsize=11, color=GRIP,
            weight='bold')
    txt = ', '.join(outside)
    wrapped, line = [], ''
    for word in txt.split(', '):
        if len(line) + len(word) > 74:
            wrapped.append(line.rstrip(', '))
            line = ''
        line += word + ', '
    wrapped.append(line.rstrip(', '))
    for i, ln in enumerate(wrapped):
        ax.text(0.5, 3.55 - i * 0.355, ln, fontsize=10, color=GRIP)
    ax.text(0.3, 0.85, 'the ones in the second group are not rare objects, they are '
            'ordinary ones described by their\nstate, their place or their part, and '
            'a class list has no way to hold a description like that',
            fontsize=10.3, color=INK, va='top')
    _save(fig, VLM_DOC, 'class-list.svg')
    print(f'[7a] of {len(BENCH)} listed bench items, {len(inside)} are in the '
          f'{len(CLASS_LIST)}-name class list and {len(outside)} are not '
          f'({100 * len(outside) / len(BENCH):.0f}%)')


def vlm_questions() -> None:
    """Six questions a robot actually needs answered, and which part can answer them."""
    rows = [('"how many cups are on the tray?"', 'yes, it lists them', 'not reliably'),
            ('"which pixel is the cup rim at?"', 'yes, to the pixel', 'no, only to a patch'),
            ('"is this cup clean enough to put away?"', 'no such class', 'yes, in words'),
            ('"has somebody left a tool in the cell?"', 'only tools in its list', 'yes, in words'),
            ('"is the bottle upright or on its side?"', 'only if pose was trained',
             'yes, in words'),
            ('"why can the gripper not reach it?"', 'no', 'yes, with a reason')]
    fig: Figure = plt.figure(figsize=(11.2, 4.7))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.7)
    ax.text(5.6, 4.45, 'Six questions from one cell, and what each part can do with them',
            ha='center', fontsize=12.3, weight='bold')
    ax.text(0.3, 3.95, 'the question', fontsize=10.5, weight='bold')
    ax.text(6.6, 3.95, 'detector', fontsize=10.5, weight='bold', color=TEAL,
            ha='center')
    ax.text(9.6, 3.95, 'vision-language model', fontsize=10.5, weight='bold',
            color=PURPLE, ha='center')
    y = 3.58
    for q, d, v in rows:
        ax.plot([0.25, 11.0], [y + 0.2, y + 0.2], color=GRID, lw=0.8)
        ax.text(0.3, y, q, fontsize=10, color=INK, va='center')
        ok_d = d.startswith('yes')
        ok_v = v.startswith('yes')
        ax.text(6.6, y, d, fontsize=9.6, ha='center', va='center',
                color=TEAL if ok_d else GRIP)
        ax.text(9.6, y, v, fontsize=9.6, ha='center', va='center',
                color=PURPLE if ok_v else GRIP)
        y -= 0.49
    ax.plot([0.25, 11.0], [y + 0.2, y + 0.2], color=GRID, lw=0.8)
    ax.text(0.3, 0.26, 'the first two rows are why the detector stays, and the last '
            'four are why the vision-language model is added', fontsize=10,
            color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'questions.svg')
    print(f'[7b] drawn {len(rows)} questions: the detector answers '
          f'{sum(1 for _, d, _ in rows if d.startswith("yes"))} of them and the '
          f'vision-language model answers '
          f'{sum(1 for _, _, v in rows if v.startswith("yes"))}')


def vlm_handover() -> None:
    """The real pipeline: words choose the target, a detector turns it into pixels."""
    fig: Figure = plt.figure(figsize=(11.2, 4.4))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.4)
    ax.text(5.6, 4.12, 'The two joined up: a question in words becomes a grasp in '
            'millimetres', ha='center', fontsize=12.3, weight='bold')
    steps = [
        (0.35, '#f2eefa', PURPLE, 'the operator asks',
         '"put away the cup\nthat somebody has\nleft on its side"'),
        (2.55, '#e6dcf7', PURPLE, 'vision-language model',
         f'reads the {PIC_TOKENS}-token\npicture and writes\n'
         '"the white cup, front\nleft, lying down"'),
        (4.95, '#d9ecec', TEAL, 'open-vocabulary detector',
         'takes that phrase and\nreturns one box\n(312, 487, 408, 549)'),
        (7.35, '#eef7f7', TEAL, 'grasp model',
         'takes the box and the\ndepth frame and returns\n'
         'a gripper pose in mm'),
        (9.55, '#fdf0d5', JOINT, 'the arm',
         'moves, at its own\nrate, with no model\nin the control loop'),
    ]
    for x, face, edge, title, body in steps:
        w = 1.95 if x < 9.4 else 1.5
        _box(ax, x, 1.55, w, 1.75, '', face=face, edge=edge)
        ax.text(x + w / 2, 3.05, title, ha='center', fontsize=10.2, weight='bold',
                color=edge)
        ax.text(x + w / 2, 2.25, body, ha='center', va='center', fontsize=9.3,
                color=INK)
    for x0, x1 in ((2.30, 2.52), (4.50, 4.92), (6.90, 7.32), (9.30, 9.52)):
        _arrow(ax, x0, 2.42, x1, 2.42, colour=MUTED)
    ax.text(0.35, 1.15, 'words → words → pixels → millimetres: each part hands the '
            'next one the only thing it is good at producing',
            fontsize=10.5, color=INK)
    ax.text(0.35, 0.65, 'the two middle steps are the ones this page explains, and '
            'the one model that does all of this at once is the subject of the\n'
            'vision-language-action page', fontsize=10, color=MUTED, va='top')
    _save(fig, VLM_DOC, 'handover.svg')
    print('[7c] drawn the five-step handover from words to millimetres')


# ==========================================================================
# 04_reasoning-and-tool-use.md
# ==========================================================================

FIRST_TOKEN: float = 0.35      # seconds before the first token appears
TOKENS_PER_SEC: float = 40.0   # tokens the model writes each second


def _toks(text: str) -> int:
    """Count tokens the simple way: a run of letters or digits, or one mark.

    A real tokeniser splits some long words into two or three pieces, so this
    count is a little low, but it is close enough to show the shape of a
    conversation and it is worked out from the text rather than guessed.
    """
    return len(re.findall(r'[A-Za-z0-9_.]+|[^\sA-Za-z0-9_]', text))


QUESTION: str = ('The tray holds 3 rows of 7 cups. 4 of them are cracked. '
                 'How many good cups are there, and what do they weigh if one '
                 'cup is 180 grams?')
WORKING: str = ('First work out how many cups the tray holds: 3 rows times 7 cups '
                'is 21 cups.\n'
                'Then take away the cracked ones: 21 minus 4 is 17 good cups.\n'
                'Then work out the weight: 17 times 180 grams.\n'
                '17 times 180 is 17 times 18 tens, and 17 times 18 is 306, '
                'so the answer is 3060 grams.\n'
                'That is 3.06 kilograms.')
ANSWER: str = 'There are 17 good cups and they weigh 3060 grams, or 3.06 kilograms.'


# -- section 1: the working out is tokens ----------------------------------

def rtu_working_out_stream() -> None:
    """The real stream: question, working out, answer, counted token by token."""
    q, w, a = _toks(QUESTION), _toks(WORKING), _toks(ANSWER)
    total = q + w + a
    fig: Figure = plt.figure(figsize=(11.2, 4.6))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.6)
    ax.text(5.6, 4.32, f'The working out is {w} of the {total} tokens, and the '
            f'answer is only {a}', ha='center', fontsize=12.3, weight='bold')
    x = 0.4
    span = 10.4
    for name, n, face, edge in (('the question', q, '#f2eefa', PURPLE),
                                ('the working out', w, '#fdf0d5', JOINT),
                                ('the answer', a, '#d9ecec', TEAL)):
        width = span * n / total
        ax.add_patch(Rectangle((x, 3.35), width, 0.55, facecolor=face,
                               edgecolor=edge, lw=1.2))
        ax.text(x + width / 2, 3.62, f'{name}: {n}', ha='center', va='center',
                fontsize=10, color=edge, weight='bold')
        x += width
    ax.text(0.4, 2.98, 'what the model is actually made to write, one token after '
            'another:', fontsize=10.3, color=MUTED)
    ax.text(0.45, 2.70, QUESTION, fontsize=9.6, color=PURPLE, va='top', wrap=True)
    y = 2.24
    for line in WORKING.split('\n'):
        ax.text(0.45, y, line, fontsize=9.6, color=INK, va='top')
        y -= 0.30
    ax.text(0.45, y - 0.05, ANSWER, fontsize=9.6, color=TEAL, va='top',
            weight='bold')
    ax.text(0.45, 0.30, 'none of those lines is a separate kind of thought: every '
            'one is a token drawn from the same vocabulary\nas the answer, in the '
            'same way, by the same model', fontsize=10, color=GRIP, va='top')
    _save(fig, RTU_DOC, 'working-out-stream.svg')
    print(f'[1a] question {q} tokens, working out {w} tokens, answer {a} tokens, '
          f'{total} in all; the working out is {100 * w / total:.0f}% of it')


def rtu_one_token_at_a_time() -> None:
    """The working out is produced by the same next-token step as everything else."""
    piece = '3 rows times 7 cups is 21'
    words = piece.split()
    fig: Figure = plt.figure(figsize=(11.2, 4.3))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.3)
    ax.text(5.6, 4.05, 'Each piece of the working out is one next-token step',
            ha='center', fontsize=12.3, weight='bold')
    rows = [3, 5, 7]
    y = 3.35
    for k in rows:
        x = 0.4
        for j, wd in enumerate(words[:k]):
            w = 0.26 + 0.135 * len(wd)
            face = '#fdf0d5' if j < k - 1 else '#f6cdcd'
            ax.add_patch(Rectangle((x, y), w, 0.42, facecolor=face,
                                   edgecolor=JOINT if j < k - 1 else GRIP, lw=1.0))
            ax.text(x + w / 2, y + 0.21, wd, ha='center', va='center', fontsize=9.6)
            x += w + 0.06
        ax.add_patch(Rectangle((x, y), 0.9, 0.42, facecolor='white',
                               edgecolor=MUTED, lw=1.0, ls='--'))
        ax.text(x + 0.45, y + 0.21, 'next?', ha='center', va='center', fontsize=9.3,
                color=MUTED)
        ax.text(x + 1.15, y + 0.21, f'the model reads {k} tokens and picks the one '
                f'that comes next', fontsize=9.6, color=INK, va='center')
        y -= 0.72
    ax.text(0.4, 1.35, 'the step that writes "21" is the same step that writes "the" '
            'in an ordinary sentence:\nthe model turns the tokens so far into one '
            'guess at the next token, and nothing in it knows\nthat these particular '
            'tokens are working out rather than prose',
            fontsize=10.2, color=INK, va='top')
    ax.text(0.4, 0.30, 'so the only way to spend more effort on a question is to '
            'write more tokens before the answer', fontsize=10.2, color=GRIP,
            va='top', weight='bold')
    _save(fig, RTU_DOC, 'one-token-at-a-time.svg')
    print(f'[1b] drawn three next-token steps over the piece "{piece}"')


class Chain:
    """A simulated six-step task, used to show what written working out buys.

    The task is a chain of six small steps that all have to be right. A step the
    model writes out is got wrong with probability 0.03, and a step it does in
    one jump without writing anything is got wrong with probability 0.22. After
    writing all six, the model may read its own working back; each reading pass
    catches each mistake already made with probability 0.30 and introduces a new
    one with probability 0.02. Those four numbers are the made-up part. The
    accuracies below are measured by running the task 8,000 times with
    numpy.random.default_rng(5), so the curve is a real Monte Carlo result.
    """

    K: int = 6
    Q_WRITTEN: float = 0.03
    Q_SILENT: float = 0.22
    P_CATCH: float = 0.30
    P_NEW: float = 0.02
    N: int = 8000
    BASE_TOKENS: int = 40
    STEP_TOKENS: int = 14
    PASS_TOKENS: int = 70

    def __init__(self) -> None:
        self.rng = np.random.default_rng(5)
        self.settings: list[tuple[int, int]] = (
            [(m, 0) for m in range(self.K + 1)] + [(self.K, p) for p in (1, 2, 3)])
        self.acc = np.array([self._accuracy(m, p) for m, p in self.settings])
        self.tokens = np.array([self.BASE_TOKENS + self.STEP_TOKENS * m
                                + self.PASS_TOKENS * p for m, p in self.settings])
        self.seconds = FIRST_TOKEN + self.tokens / TOKENS_PER_SEC

    def _accuracy(self, m: int, passes: int) -> float:
        rng = self.rng
        wrong = (rng.random((self.N, m)) < self.Q_WRITTEN).sum(axis=1)
        wrong = wrong + (rng.random((self.N, self.K - m))
                         < self.Q_SILENT).sum(axis=1)
        for _ in range(passes):
            caught = rng.binomial(wrong, self.P_CATCH)
            wrong = wrong - caught + (rng.random(self.N) < self.P_NEW)
        return float(np.mean(wrong == 0))


CHAIN: Chain | None = None


def _chain() -> Chain:
    global CHAIN
    if CHAIN is None:
        CHAIN = Chain()
    return CHAIN


def rtu_written_vs_silent() -> None:
    """Simulated: how often the whole chain comes out right, written or silent."""
    c = _chain()
    silent = c.acc[0]
    written = c.acc[c.K]
    fig: Figure = plt.figure(figsize=(10.0, 4.1))
    ax1: Axes = fig.add_axes((0.08, 0.20, 0.36, 0.60))
    ax2: Axes = fig.add_axes((0.57, 0.20, 0.38, 0.60))
    _plain(ax1)
    _plain(ax2)
    bars = ax1.bar(['all six steps\nin one jump', 'all six steps\nwritten out'],
                   [silent, written], color=[GRIP, TEAL], width=0.5)
    for b, v in zip(bars, (silent, written)):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.025, f'{100 * v:.0f}%',
                 ha='center', fontsize=11, weight='bold')
    ax1.set_ylim(0, 1.0)
    ax1.set_ylabel('share of tasks got right', fontsize=10)
    ax1.set_title('Writing the steps out', fontsize=11.5, weight='bold')
    steps = np.arange(c.K + 1)
    ax2.plot(steps, c.acc[:c.K + 1], 'o-', color=TEAL, lw=1.9)
    ax2.set_xlabel('steps written out, of six', fontsize=10)
    ax2.set_ylabel('share of tasks got right', fontsize=10)
    ax2.set_ylim(0, 1.0)
    ax2.set_title('Each step written is one less step guessed', fontsize=11.5,
                  weight='bold')
    for k in (0, 3, 6):
        ax2.annotate(f'{100 * c.acc[k]:.0f}%', xy=(k, c.acc[k]),
                     xytext=(k - 0.1, c.acc[k] + 0.07), fontsize=9.5, color=INK)
    fig.text(0.5, 0.005, 'illustrative: a simulated six-step task, 8,000 runs, seed 5',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'written-vs-silent.svg')
    print(f'[1c] simulated chain: {100 * silent:.0f}% right with nothing written, '
          f'{100 * written:.0f}% with all six steps written')


# -- section 2: what more tokens at answering time buy ---------------------

def rtu_accuracy_vs_tokens() -> None:
    """The simulated trade: accuracy against the number of working-out tokens."""
    c = _chain()
    fig: Figure = plt.figure(figsize=(9.8, 4.2))
    ax: Axes = fig.add_axes((0.10, 0.18, 0.80, 0.63))
    _plain(ax)
    n_write = c.K + 1
    ax.plot(c.tokens[:n_write], c.acc[:n_write], 'o-', color=TEAL, lw=2.0,
            label='writing more of the six steps')
    ax.plot(c.tokens[n_write - 1:], c.acc[n_write - 1:], 's--', color=PURPLE,
            lw=2.0, label='then reading the working back, pass by pass')
    ax.set_xlabel('tokens the model writes before the answer', fontsize=10)
    ax.set_ylabel('share of tasks got right', fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_title('More working out helps, and then it almost stops helping',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    for i in (0, c.K, len(c.acc) - 1):
        ax.annotate(f'{int(c.tokens[i])} tokens\n{100 * c.acc[i]:.0f}%',
                    xy=(c.tokens[i], c.acc[i]),
                    xytext=(c.tokens[i] + 8, c.acc[i] - 0.17), fontsize=9,
                    color=INK)
    ax.set_xlim(20, c.tokens.max() * 1.12)
    fig.text(0.5, 0.005, 'illustrative: a simulated six-step task, 8,000 runs each, '
             'seed 5', ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'accuracy-vs-tokens.svg')
    print('[2a] simulated tokens and accuracy: '
          + '; '.join(f'{int(t)} tok {100 * a:.0f}%'
                      for t, a in zip(c.tokens, c.acc)))


def rtu_time_vs_tokens() -> None:
    """The other half of the trade: what those tokens cost in seconds."""
    c = _chain()
    fig: Figure = plt.figure(figsize=(9.8, 4.2))
    ax: Axes = fig.add_axes((0.10, 0.18, 0.80, 0.63))
    _plain(ax)
    ax.plot(c.tokens, c.seconds, 'o-', color=GRIP, lw=2.0)
    ax.set_xlabel('tokens the model writes before the answer', fontsize=10)
    ax.set_ylabel('seconds before the answer appears', fontsize=10)
    ax.set_title(f'At {TOKENS_PER_SEC:.0f} tokens a second, with '
                 f'{FIRST_TOKEN:.2f} s before the first one',
                 fontsize=12, weight='bold')
    for i in (0, c.K, len(c.acc) - 1):
        ax.annotate(f'{c.seconds[i]:.2f} s', xy=(c.tokens[i], c.seconds[i]),
                    xytext=(c.tokens[i] - 4, c.seconds[i] + 0.55), fontsize=9.5,
                    color=INK)
    ax.set_ylim(0, c.seconds.max() * 1.3)
    ax.set_xlim(20, c.tokens.max() * 1.12)
    ax.axhline(c.seconds[0], color=MUTED, ls=':', lw=0.9)
    ax.text(c.tokens.max() * 1.10, c.seconds[0] + 0.12,
            'the shortest answer', fontsize=9, color=MUTED, ha='right')
    fig.text(0.5, 0.005, 'illustrative: the writing rate is a stated assumption, '
             'not a measurement', ha='center', fontsize=9, color=MUTED,
             style='italic')
    _save(fig, RTU_DOC, 'time-vs-tokens.svg')
    print(f'[2b] simulated seconds: shortest {c.seconds[0]:.2f} s at '
          f'{int(c.tokens[0])} tokens, longest {c.seconds[-1]:.2f} s at '
          f'{int(c.tokens[-1])} tokens, which is '
          f'{c.seconds[-1] / c.seconds[0]:.1f} times as long')


def rtu_accuracy_per_second() -> None:
    """The two put together, so the point where more time stops paying is visible."""
    c = _chain()
    gain = np.diff(c.acc) / np.diff(c.seconds)
    fig: Figure = plt.figure(figsize=(10.4, 4.2))
    ax1: Axes = fig.add_axes((0.08, 0.19, 0.37, 0.61))
    ax2: Axes = fig.add_axes((0.58, 0.27, 0.37, 0.53))
    _plain(ax1)
    _plain(ax2)
    ax1.plot(c.seconds, c.acc, 'o-', color=PURPLE, lw=2.0)
    ax1.set_xlabel('seconds spent', fontsize=10)
    ax1.set_ylabel('share of tasks got right', fontsize=10)
    ax1.set_ylim(0, 1.0)
    ax1.set_title('What a second of thinking buys', fontsize=11.5, weight='bold')
    best = int(np.argmax(gain))
    ax1.annotate('the steepest stretch',
                 xy=(c.seconds[best + 1], c.acc[best + 1]),
                 xytext=(c.seconds[best + 1] + 0.3, c.acc[best + 1] - 0.30),
                 fontsize=9.3, color=GRIP,
                 arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.0))
    ax2.bar(range(len(gain)), gain * 100, color=TEAL, width=0.62)
    ax2.set_xticks(range(len(gain)))
    ax2.set_xticklabels([f'{int(c.tokens[i])}\nto\n{int(c.tokens[i + 1])}'
                         for i in range(len(gain))], fontsize=7.6)
    ax2.set_xlabel('tokens, from one setting to the next', fontsize=10)
    ax2.set_ylabel('extra tasks got right per second spent, %', fontsize=9.5)
    ax2.set_title('And what the next second buys', fontsize=11.5, weight='bold')
    ax2.axhline(0, color=INK, lw=0.8)
    fig.text(0.5, 0.005, 'illustrative: simulated task, 8,000 runs each, seed 5',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'accuracy-per-second.svg')
    print(f'[2c] simulated gain per second is largest between '
          f'{int(c.tokens[best])} and {int(c.tokens[best + 1])} tokens at '
          f'{100 * gain[best]:.0f} percentage points a second, and falls to '
          f'{100 * gain[-1]:.1f} at the end')


# -- section 3: the three shapes of test-time compute ----------------------

class Vote:
    """Several attempts at the same question, with the commonest answer kept.

    Each attempt is right with the probability the simulated task gives when
    three of its six steps are written out. A wrong attempt lands on one of six
    wrong answers, and one of those six is the easy mistake, which takes 35 out
    of every 100 wrong attempts. The vote keeps the answer that came up most
    often, and a tie is broken at random. 6,000 episodes with
    numpy.random.default_rng(17).
    """

    N: int = 6000
    N_WRONG: int = 6
    EASY_SHARE: float = 0.35

    def __init__(self, p_right: float, tokens_each: int) -> None:
        self.p_right = p_right
        self.tokens_each = tokens_each
        self.rng = np.random.default_rng(17)
        self.counts = np.arange(1, 16, 2)
        self.acc = np.array([self._vote(n) for n in self.counts])
        self.tokens = self.counts * tokens_each
        self.seconds = self.counts * (FIRST_TOKEN + tokens_each / TOKENS_PER_SEC)

    def _draw(self, size: tuple[int, int]) -> NDArray[np.int64]:
        rng = self.rng
        right = rng.random(size) < self.p_right
        easy = rng.random(size) < self.EASY_SHARE
        other = rng.integers(1, self.N_WRONG, size=size)
        ans = np.where(right, 0, np.where(easy, 1, other + 1))
        return ans.astype(np.int64)

    def _vote(self, n: int) -> float:
        ans = self._draw((self.N, n))
        wins = 0
        for row in ans:
            vals, cnt = np.unique(row, return_counts=True)
            best = vals[cnt == cnt.max()]
            wins += int(self.rng.choice(best) == 0)
        return wins / self.N


VOTE: Vote | None = None


def _vote_run() -> Vote:
    global VOTE
    if VOTE is None:
        c = _chain()
        VOTE = Vote(float(c.acc[3]), int(c.tokens[3]))
    return VOTE


def rtu_vote_curve() -> None:
    """Simulated: taking several goes and keeping the commonest answer."""
    v = _vote_run()
    fig: Figure = plt.figure(figsize=(9.8, 4.2))
    ax: Axes = fig.add_axes((0.10, 0.18, 0.80, 0.62))
    _plain(ax)
    ax.plot(v.counts, v.acc, 'o-', color=PURPLE, lw=2.0)
    ax.axhline(v.p_right, color=MUTED, ls=':', lw=1.0)
    ax.text(15, v.p_right - 0.055, 'one attempt on its own', fontsize=9.3,
            color=MUTED, ha='right')
    ax.set_xlabel('attempts at the same question', fontsize=10)
    ax.set_ylabel('share of tasks got right after the vote', fontsize=10)
    ax.set_xticks(v.counts)
    ax.set_ylim(0, 1.0)
    ax.set_title('The vote climbs quickly and then flattens, because the attempts '
                 'share the same easy mistake', fontsize=11.5, weight='bold')
    for i in (0, 2, 7):
        ax.annotate(f'{100 * v.acc[i]:.0f}%', xy=(v.counts[i], v.acc[i]),
                    xytext=(v.counts[i] - 0.3, v.acc[i] + 0.06), fontsize=9.5)
    fig.text(0.5, 0.005, 'illustrative: 6,000 simulated episodes, seed 17',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'vote-curve.svg')
    print(f'[3a] simulated vote: one attempt {100 * v.acc[0]:.0f}%, '
          f'3 attempts {100 * v.acc[1]:.0f}%, 5 attempts {100 * v.acc[2]:.0f}%, '
          f'15 attempts {100 * v.acc[7]:.0f}%')


def rtu_vote_cost() -> None:
    """What the vote costs: every attempt is paid for in full."""
    v = _vote_run()
    fig: Figure = plt.figure(figsize=(10.2, 4.1))
    ax1: Axes = fig.add_axes((0.08, 0.19, 0.37, 0.61))
    ax2: Axes = fig.add_axes((0.58, 0.19, 0.37, 0.61))
    _plain(ax1)
    _plain(ax2)
    ax1.bar(v.counts, v.tokens, color=GRIP, width=1.3)
    ax1.set_xlabel('attempts', fontsize=10)
    ax1.set_ylabel('tokens written in all', fontsize=10)
    ax1.set_xticks(v.counts)
    ax1.set_title('The bill rises in a straight line', fontsize=11.5, weight='bold')
    for n, t in zip(v.counts[::3], v.tokens[::3]):
        ax1.text(n, t + v.tokens.max() * 0.03, str(int(t)), ha='center', fontsize=9)
    ax1.set_ylim(0, v.tokens.max() * 1.18)
    ax2.plot(v.tokens, v.acc, 'o-', color=PURPLE, lw=2.0)
    ax2.set_xlabel('tokens written in all', fontsize=10)
    ax2.set_ylabel('share of tasks got right', fontsize=10)
    ax2.set_ylim(0, 1.0)
    ax2.set_title('The answer does not', fontsize=11.5, weight='bold')
    fig.text(0.5, 0.005, 'illustrative: 6,000 simulated episodes, seed 17; the '
             'attempts can be written at the same time, so the seconds need not '
             'rise with the tokens', ha='center', fontsize=9, color=MUTED,
             style='italic')
    _save(fig, RTU_DOC, 'vote-cost.svg')
    print(f'[3b] simulated vote cost: 1 attempt {int(v.tokens[0])} tokens, '
          f'15 attempts {int(v.tokens[7])} tokens, for '
          f'{100 * (v.acc[7] - v.p_right):.0f} more tasks right in every hundred')


class Beam:
    """A search over partial answers, scored by a noisy judge.

    The question is answered in four steps and there are three ways to take each
    step, so there are 81 whole answers and exactly one of them is right. A
    judge gives each partial answer a score: 1 if the partial answer is still on
    the right path and 0 if it is not, plus noise drawn from a normal
    distribution with a spread of 0.7, which is what makes the judge imperfect.
    Beam search keeps the b best partial answers at each step. 4,000 runs with
    numpy.random.default_rng(23).
    """

    DEPTH: int = 4
    BRANCH: int = 3
    NOISE: float = 0.7
    N: int = 4000
    TOKENS_PER_NODE: int = 30

    def __init__(self) -> None:
        self.rng = np.random.default_rng(23)
        self.widths = np.arange(1, 10)
        self.acc = np.array([self._run(b) for b in self.widths])
        self.nodes = np.array([self._nodes(b) for b in self.widths])
        self.tokens = self.nodes * self.TOKENS_PER_NODE

    def _nodes(self, b: int) -> int:
        kept, total = 1, 0
        for _ in range(self.DEPTH):
            made = kept * self.BRANCH
            total += made
            kept = min(b, made)
        return total

    def _run(self, b: int) -> float:
        rng = self.rng
        wins = 0
        for _ in range(self.N):
            beam = [True]                      # one partial answer, on the path
            for _ in range(self.DEPTH):
                made: list[bool] = []
                for on_path in beam:
                    for k in range(self.BRANCH):
                        made.append(on_path and k == 0)
                scores = np.array(made, dtype=float) + rng.normal(
                    0.0, self.NOISE, size=len(made))
                order = np.argsort(-scores)[:b]
                beam = [made[i] for i in order]
            wins += int(any(beam))
        return wins / self.N


BEAM: Beam | None = None


def _beam() -> Beam:
    global BEAM
    if BEAM is None:
        BEAM = Beam()
    return BEAM


def rtu_search_tree() -> None:
    """One run of the search drawn out, with the scores the judge gave."""
    rng = np.random.default_rng(23)
    b = Beam()
    fig: Figure = plt.figure(figsize=(11.0, 5.6))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.0)
    ax.set_ylim(0, 5.6)
    ax.text(5.5, 5.32, 'One run of the search, with a beam of 2 and the judge\'s '
            'scores written on each partial answer', ha='center', fontsize=11.8,
            weight='bold')
    width = 2
    beam: list[tuple[bool, float, float]] = [(True, 5.5, 4.85)]
    kept_text = []
    for d in range(3):
        made = []
        for on_path, px, py in beam:
            for k in range(3):
                made.append((on_path and k == 0, px, py, k))
        xs = np.linspace(1.0, 10.0, len(made))
        scores = rng.normal(0.0, b.NOISE, size=len(made)) + np.array(
            [1.0 if m[0] else 0.0 for m in made])
        order = np.argsort(-scores)[:width]
        y = 4.85 - (d + 1) * 1.12
        new_beam = []
        for i, ((on_path, px, py, k), x, sc) in enumerate(zip(made, xs, scores)):
            keep = i in order
            face = '#d9ecec' if keep else '#f3f3f3'
            edge = GRIP if on_path else (TEAL if keep else '#bbbbbb')
            ax.plot([px, x], [py - 0.19, y + 0.22],
                    color=TEAL if keep else '#dddddd', lw=1.4 if keep else 0.7,
                    zorder=1)
            ax.add_patch(FancyBboxPatch((x - 0.40, y - 0.22), 0.80, 0.44,
                                        boxstyle='round,pad=0.01,rounding_size=0.04',
                                        facecolor=face, edgecolor=edge,
                                        lw=2.0 if on_path else (1.4 if keep else 0.8),
                                        zorder=2))
            ax.text(x, y, f'{sc:+.2f}', ha='center', va='center', fontsize=8.8,
                    color=INK if keep else MUTED, zorder=3,
                    weight='bold' if keep else 'normal')
            if keep:
                new_beam.append((on_path, x, y))
        kept_text.append(f'step {d + 1}: {len(made)} partial answers made, '
                         f'{width} kept')
        beam = new_beam
    ax.text(0.35, 0.85, '   |   '.join(kept_text), fontsize=9.8, color=INK)
    ax.text(0.35, 0.52, 'a red outline marks a partial answer that is still on the '
            'right path, and a shaded box one the judge kept', fontsize=9.6,
            color=GRIP)
    ax.text(0.35, 0.19, 'the judge is noisy, so a partial answer on the right path '
            'is sometimes thrown away, which is why a wider beam helps',
            fontsize=9.6, color=MUTED)
    _save(fig, RTU_DOC, 'search-tree.svg')
    print('[3c] drawn one search run with a beam of 2 over three steps of three '
          'branches')


def rtu_search_curve() -> None:
    """Simulated: a wider beam finds the answer more often, and costs more."""
    b = _beam()
    fig: Figure = plt.figure(figsize=(10.2, 4.1))
    ax1: Axes = fig.add_axes((0.08, 0.19, 0.37, 0.61))
    ax2: Axes = fig.add_axes((0.58, 0.19, 0.37, 0.61))
    _plain(ax1)
    _plain(ax2)
    ax1.plot(b.widths, b.acc, 'o-', color=TEAL, lw=2.0)
    ax1.set_xlabel('how many partial answers are kept at each step', fontsize=10)
    ax1.set_ylabel('share of runs that find the answer', fontsize=10)
    ax1.set_xticks(b.widths)
    ax1.set_ylim(0, 1.0)
    ax1.set_title('A wider beam survives the noisy judge', fontsize=11.5,
                  weight='bold')
    for i in (0, 2, 8):
        ax1.annotate(f'{100 * b.acc[i]:.0f}%', xy=(b.widths[i], b.acc[i]),
                     xytext=(b.widths[i] - 0.25, b.acc[i] + 0.06), fontsize=9.5)
    ax2.plot(b.widths, b.tokens, 's-', color=GRIP, lw=2.0)
    ax2.set_xlabel('how many partial answers are kept at each step', fontsize=10)
    ax2.set_ylabel('tokens written in all', fontsize=10)
    ax2.set_xticks(b.widths)
    ax2.set_title('And costs a straight line of tokens', fontsize=11.5,
                  weight='bold')
    for i in (0, 8):
        ax2.annotate(f'{int(b.nodes[i])} partial answers\n{int(b.tokens[i])} tokens',
                     xy=(b.widths[i], b.tokens[i]),
                     xytext=(b.widths[i] + 0.2, b.tokens[i] - 350), fontsize=8.8)
    ax2.set_ylim(0, b.tokens.max() * 1.15)
    fig.text(0.5, 0.005, 'illustrative: 4,000 simulated runs for each width, seed 23',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'search-curve.svg')
    print('[3d] simulated beam search: '
          + '; '.join(f'width {w}: {100 * a:.0f}% right, {int(n)} partial answers'
                      for w, a, n in zip(b.widths, b.acc, b.nodes)))


# -- section 4: calling a tool ---------------------------------------------

CALLS: list[tuple[str, str]] = [
    ('{"tool": "count_objects", "arguments": {"class": "cup"}}',
     '{"count": 21}'),
    ('{"tool": "count_objects", "arguments": {"class": "cup", '
     '"condition": "cracked"}}', '{"count": 4}'),
    ('{"tool": "calculator", "arguments": {"expression": "(21 - 4) * 180"}}',
     '{"value": %d}' % ((21 - 4) * 180)),
]
TOOL_PROMPT: str = ('You may call count_objects(class, condition) and '
                    'calculator(expression). Write one call at a time and wait '
                    'for its result.')
TOOL_QUESTION: str = ('How many good cups are on the tray, and what do they weigh '
                      'if one cup is 180 grams?')
TOOL_ANSWER: str = ('There are 17 good cups on the tray and they weigh %d grams, '
                    'which is 3.06 kilograms.' % ((21 - 4) * 180))


def rtu_tool_loop() -> None:
    """The loop drawn with the worked example on it."""
    fig: Figure = plt.figure(figsize=(11.2, 5.5))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 5.5)
    ax.text(5.6, 5.22, 'One turn of the tool loop, and the three turns the question '
            'actually took', ha='center', fontsize=12.3, weight='bold')
    stations = [
        (0.35, 3.15, '#e6dcf7', PURPLE, '1. the model writes a call',
         'it writes tokens that happen\nto spell a call, and stops'),
        (0.35, 1.55, '#fdf0d5', JOINT, '2. the program checks it',
         'is the tool real, are the\narguments allowed'),
        (2.95, 1.55, '#d9ecec', TEAL, '3. the program runs it',
         'the detector counts, or the\ncalculator multiplies'),
        (2.95, 3.15, '#eef7f7', TEAL, '4. the result goes back in',
         'as plain tokens, appended\nto the same stream'),
    ]
    for x, y, face, edge, title, body in stations:
        _box(ax, x, y, 2.35, 1.15, '', face=face, edge=edge)
        ax.text(x + 1.175, y + 0.92, title, ha='center', fontsize=10.2,
                weight='bold', color=edge)
        ax.text(x + 1.175, y + 0.42, body, ha='center', va='center', fontsize=9.1,
                color=INK)
    _arrow(ax, 1.525, 3.13, 1.525, 2.74, colour=MUTED)
    _arrow(ax, 2.72, 2.12, 2.93, 2.12, colour=MUTED)
    _arrow(ax, 4.125, 2.72, 4.125, 3.13, colour=MUTED)
    ax.annotate('', xy=(1.525, 4.36), xytext=(4.125, 4.36),
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.5,
                                connectionstyle='arc3,rad=0.45'))
    ax.text(2.82, 5.00, 'then round again', ha='center', fontsize=9.6, color=GRIP)
    x0 = 6.0
    ax.text(x0, 4.84, 'the three turns, written out', fontsize=11, weight='bold')
    y = 4.52
    ax.text(x0, y, f'asked: {TOOL_QUESTION}', fontsize=8.8, color=PURPLE,
            va='top', wrap=True)
    y -= 0.52
    for i, (call, result) in enumerate(CALLS, start=1):
        shown = call if len(call) < 86 else call[:84] + ' ...'
        ax.text(x0, y, f'turn {i} out:  {shown}', fontsize=7.5, color=INK,
                family='DejaVu Sans Mono', va='top')
        ax.text(x0, y - 0.26, f'turn {i} back: {result}', fontsize=7.5, color=TEAL,
                family='DejaVu Sans Mono', va='top')
        y -= 0.70
    ax.text(x0, y, f'answer: {TOOL_ANSWER}', fontsize=8.8, color=JOINT, va='top',
            weight='bold')
    ax.text(x0, 0.75, 'the model never did the multiplying itself, and it never '
            'counted\nthe cups itself, so neither of those could come out wrong',
            fontsize=9.4, color=MUTED, va='top')
    _save(fig, RTU_DOC, 'tool-loop.svg')
    print(f'[4a] worked example: {len(CALLS)} calls, the last of which returns '
          f'{(21 - 4) * 180}')


def rtu_tool_transcript() -> None:
    """How the stream grows turn by turn, counted token by token."""
    base = _toks(TOOL_PROMPT) + _toks(TOOL_QUESTION)
    marks: list[tuple[str, int, str]] = [('system prompt\nand question', base, MUTED)]
    running = base
    for i, (call, result) in enumerate(CALLS, start=1):
        running += _toks(call)
        marks.append((f'call {i}', _toks(call), PURPLE))
        running += _toks(result)
        marks.append((f'result {i}', _toks(result), TEAL))
    running += _toks(TOOL_ANSWER)
    marks.append(('the answer', _toks(TOOL_ANSWER), JOINT))
    totals = np.cumsum([m[1] for m in marks])
    fig: Figure = plt.figure(figsize=(10.6, 4.3))
    ax1: Axes = fig.add_axes((0.07, 0.30, 0.42, 0.52))
    ax2: Axes = fig.add_axes((0.59, 0.19, 0.38, 0.63))
    _plain(ax1)
    _plain(ax2)
    ax1.bar(range(len(marks)), [m[1] for m in marks],
            color=[m[2] for m in marks], width=0.62)
    ax1.set_xticks(range(len(marks)))
    ax1.set_xticklabels([m[0] for m in marks], fontsize=8, rotation=35, ha='right')
    ax1.set_ylabel('tokens added', fontsize=10)
    ax1.set_title('What each part of the loop adds', fontsize=11.5, weight='bold')
    for i, m in enumerate(marks):
        ax1.text(i, m[1] + 1.2, str(m[1]), ha='center', fontsize=8.8)
    ax1.set_ylim(0, max(m[1] for m in marks) * 1.2)
    ax2.step(range(len(totals)), totals, where='post', color=GRIP, lw=2.0)
    ax2.plot(range(len(totals)), totals, 'o', color=GRIP, ms=5)
    ax2.set_xticks(range(len(marks)))
    ax2.set_xticklabels(['start', 'c1', 'r1', 'c2', 'r2', 'c3', 'r3', 'end'],
                        fontsize=9)
    ax2.set_ylabel('tokens in the stream', fontsize=10)
    ax2.set_xlabel('the loop, step by step', fontsize=10)
    ax2.set_title(f'The stream reaches {int(totals[-1])} tokens, and the model '
                  f'reads all of it\non every turn', fontsize=11, weight='bold')
    ax2.set_ylim(0, totals[-1] * 1.2)
    ax2.annotate(f'{int(totals[-1])}', xy=(len(totals) - 1, totals[-1]),
                 xytext=(len(totals) - 2.0, totals[-1] * 1.07), fontsize=10,
                 color=GRIP, weight='bold')
    _save(fig, RTU_DOC, 'tool-transcript.svg')
    print('[4b] token counts: '
          + ', '.join(f'{m[0].replace(chr(10), " ")} {m[1]}' for m in marks)
          + f'; {int(totals[-1])} in all')


def rtu_tool_vs_no_tool() -> None:
    """Simulated: multiplying by hand against handing it to a calculator.

    The model works a multiplication out digit by digit, and each digit it
    writes is wrong with probability 0.06, which is the made-up part. A d-digit
    number times a d-digit number needs about 2 d squared digit steps, so the
    chance of getting the whole thing right falls fast. The calculator is
    always right. 4,000 problems for each size with seed 41.
    """
    rng = np.random.default_rng(41)
    q = 0.06
    digits = np.arange(1, 8)
    n = 4000
    by_hand = []
    for d in digits:
        steps = 2 * d * d
        wrong = (rng.random((n, steps)) < q).sum(axis=1)
        by_hand.append(float(np.mean(wrong == 0)))
    by_hand = np.array(by_hand)
    fig: Figure = plt.figure(figsize=(10.0, 4.2))
    ax: Axes = fig.add_axes((0.10, 0.18, 0.80, 0.62))
    _plain(ax)
    ax.plot(digits, by_hand, 'o-', color=GRIP, lw=2.0,
            label='the model multiplies it out in tokens')
    ax.plot(digits, np.ones_like(digits, dtype=float), 's-', color=TEAL, lw=2.0,
            label='the model calls a calculator')
    ax.set_xlabel('digits in each of the two numbers', fontsize=10)
    ax.set_ylabel('share of multiplications got right', fontsize=10)
    ax.set_ylim(0, 1.08)
    ax.set_xticks(digits)
    ax.set_title('A tool does not make the model cleverer, it removes a job the '
                 'model is bad at', fontsize=11.8, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center left')
    for i in (0, 2, 6):
        ax.annotate(f'{100 * by_hand[i]:.0f}%', xy=(digits[i], by_hand[i]),
                    xytext=(digits[i] - 0.1, by_hand[i] + 0.06), fontsize=9.5,
                    color=GRIP)
    fig.text(0.5, 0.005, 'illustrative: 4,000 simulated problems at each size, seed 41',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'tool-vs-no-tool.svg')
    print('[4c] simulated multiplication by hand: '
          + ', '.join(f'{d} digits {100 * a:.0f}%' for d, a in zip(digits, by_hand)))


def rtu_tool_cost() -> None:
    """Where the seconds go in one turn of the loop."""
    call_tokens = _toks(CALLS[0][0])
    parts = [('waiting for the first token', FIRST_TOKEN),
             ('writing the call', call_tokens / TOKENS_PER_SEC),
             ('running the tool', 0.22),
             ('reading the result back in', 0.06)]
    turn = sum(v for _, v in parts)
    fig: Figure = plt.figure(figsize=(10.4, 4.1))
    ax1: Axes = fig.add_axes((0.08, 0.40, 0.42, 0.42))
    ax2: Axes = fig.add_axes((0.62, 0.22, 0.34, 0.60))
    _plain(ax1)
    _plain(ax2)
    left = 0.0
    colours = [MUTED, PURPLE, TEAL, JOINT]
    for (name, v), col in zip(parts, colours):
        ax1.barh([0], [v], left=[left], color=col, height=0.5, label=name)
        left += v
    ax1.set_yticks([])
    ax1.set_xlabel('seconds in one turn', fontsize=10)
    ax1.set_xlim(0, turn * 1.02)
    ax1.set_title(f'One turn takes {turn:.2f} seconds', fontsize=11.5, weight='bold')
    ax1.legend(fontsize=8.6, frameon=False, loc='upper center',
               bbox_to_anchor=(0.5, -0.42), ncol=2)
    turns = np.arange(1, 7)
    ax2.bar(turns, turns * turn, color=GRIP, width=0.6)
    ax2.set_xlabel('turns of the loop', fontsize=10)
    ax2.set_ylabel('seconds in all', fontsize=10)
    ax2.set_xticks(turns)
    ax2.set_title('And they add up', fontsize=11.5, weight='bold')
    for t in (3, 6):
        ax2.text(t, t * turn + 0.12, f'{t * turn:.1f} s', ha='center', fontsize=9.3)
    ax2.set_ylim(0, 6 * turn * 1.2)
    fig.text(0.98, 0.02, 'illustrative: the writing rate and the tool time are '
             'stated assumptions', ha='right', fontsize=9, color=MUTED,
             style='italic')
    _save(fig, RTU_DOC, 'tool-cost.svg')
    print(f'[4d] one turn of the loop takes {turn:.2f} s '
          + ', '.join(f'{n} {v:.2f}' for n, v in parts)
          + f'; three turns take {3 * turn:.2f} s and six take {6 * turn:.2f} s')


# -- section 5: what goes wrong in the loop --------------------------------

class Episodes:
    """Simulated agent episodes, used by sections 5, 6 and 7.

    One episode is a run of turns. On each turn the agent finishes the job with
    probability 0.35, unless it has fallen into a state where it keeps asking
    the same thing, which happens on any turn with probability 0.06 and drops
    the chance of finishing to 0.10. A turn costs 0.35 seconds before its first
    token, then the tokens of the call at 40 a second, where the call is
    between 45 and 110 tokens, and then the tool's own time, which is 0.05
    seconds plus a draw from an exponential distribution with a mean of 0.35
    seconds, cut off at 3 seconds. Those numbers are the made-up part; the
    counts and the times below are measured over 3,000 episodes run with
    numpy.random.default_rng(31).
    """

    N: int = 3000
    P_DONE: float = 0.35
    P_STUCK: float = 0.06
    P_DONE_STUCK: float = 0.10
    HARD_LIMIT: int = 40
    CAP: int = 8
    TIMEOUT: float = 30.0

    def __init__(self) -> None:
        rng = np.random.default_rng(31)
        self.rng = rng
        turns: list[int] = []
        secs: list[float] = []
        self.example: list[tuple[float, float, float]] = []
        for e in range(self.N):
            stuck = False
            t, total = 0, 0.0
            parts: list[tuple[float, float, float]] = []
            while t < self.HARD_LIMIT:
                t += 1
                call = int(rng.integers(45, 111))
                tool = 0.05 + min(float(rng.exponential(0.35)), 3.0)
                parts.append((FIRST_TOKEN, call / TOKENS_PER_SEC, tool))
                total += FIRST_TOKEN + call / TOKENS_PER_SEC + tool
                if not stuck and rng.random() < self.P_STUCK:
                    stuck = True
                p = self.P_DONE_STUCK if stuck else self.P_DONE
                if rng.random() < p:
                    break
            turns.append(t)
            secs.append(total)
            if not self.example and t == 5:
                self.example = parts
        self.turns = np.array(turns)
        self.secs = np.array(secs)
        self.capped = np.minimum(self.turns, self.CAP)

    @property
    def hit_cap(self) -> float:
        return float(np.mean(self.turns > self.CAP))

    @property
    def over_timeout(self) -> float:
        return float(np.mean(self.secs > self.TIMEOUT))


EPISODES: Episodes | None = None


def _episodes() -> Episodes:
    global EPISODES
    if EPISODES is None:
        EPISODES = Episodes()
    return EPISODES


def rtu_argument_check() -> None:
    """Simulated: how many calls a plain check on the arguments throws out.

    400 calls are drawn with numpy.random.default_rng(29). A call names a real
    tool 93 times in 100, uses a class name from the allowed list 88 times in
    100, keeps a numeric argument inside its range 95 times in 100, and
    includes every required argument 97 times in 100. Those four rates are the
    made-up part; the counts are what the draw gave.
    """
    rng = np.random.default_rng(29)
    n = 400
    ok_name = rng.random(n) < 0.93
    ok_class = rng.random(n) < 0.88
    ok_range = rng.random(n) < 0.95
    ok_required = rng.random(n) < 0.97
    bad_name = int((~ok_name).sum())
    bad_class = int((ok_name & ~ok_class).sum())
    bad_range = int((ok_name & ok_class & ~ok_range).sum())
    bad_req = int((ok_name & ok_class & ok_range & ~ok_required).sum())
    passed = n - bad_name - bad_class - bad_range - bad_req
    stages = [('calls the model wrote', n, MUTED),
              ('the tool name is not one of ours', bad_name, GRIP),
              ('the class is not in the allowed list', bad_class, GRIP),
              ('a number is outside its range', bad_range, GRIP),
              ('a required argument is missing', bad_req, GRIP),
              ('calls that are run', passed, TEAL)]
    fig: Figure = plt.figure(figsize=(10.2, 4.3))
    ax: Axes = fig.add_axes((0.40, 0.16, 0.56, 0.66))
    _plain(ax)
    y = np.arange(len(stages))
    ax.barh(y, [s[1] for s in stages], color=[s[2] for s in stages], height=0.58)
    ax.set_yticks(y)
    ax.set_yticklabels([s[0] for s in stages], fontsize=9.6)
    ax.invert_yaxis()
    ax.set_xlabel('calls out of 400', fontsize=10)
    for i, s in enumerate(stages):
        ax.text(s[1] + 5, i, str(s[1]), va='center', fontsize=9.8, weight='bold')
    ax.set_xlim(0, n * 1.12)
    ax.set_title(f'A check written in a few lines catches '
                 f'{n - passed} of 400 bad calls before anything moves',
                 fontsize=11.5, weight='bold')
    fig.text(0.5, 0.005, 'illustrative: 400 simulated calls, seed 29', ha='center',
             fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'argument-check.svg')
    print(f'[5a] of 400 simulated calls: {bad_name} named a tool that does not '
          f'exist, {bad_class} used a class outside the list, {bad_range} had a '
          f'number out of range, {bad_req} missed a required argument, and '
          f'{passed} were run')


def rtu_turn_cap() -> None:
    """Simulated: how many turns an episode takes, and what a cap does."""
    e = _episodes()
    fig: Figure = plt.figure(figsize=(10.2, 4.2))
    ax1: Axes = fig.add_axes((0.08, 0.19, 0.38, 0.62))
    ax2: Axes = fig.add_axes((0.58, 0.19, 0.38, 0.62))
    _plain(ax1)
    _plain(ax2)
    bins = np.arange(0.5, 25.5, 1.0)
    ax1.hist(e.turns, bins=bins, color=PURPLE, alpha=0.9)
    ax1.axvline(e.CAP + 0.5, color=GRIP, lw=1.8)
    ax1.text(e.CAP + 1.0, ax1.get_ylim()[1] * 0.75, f'a cap of {e.CAP} turns',
             fontsize=9.5, color=GRIP)
    ax1.set_xlabel('turns the episode took', fontsize=10)
    ax1.set_ylabel('episodes', fontsize=10)
    ax1.set_title(f'Most finish quickly, {100 * e.hit_cap:.0f} in every 100 do not',
                  fontsize=11.3, weight='bold')
    longest = int(e.turns.max())
    ax2.bar(['no cap', f'cap of {e.CAP}'],
            [float(e.turns.mean()), float(e.capped.mean())],
            color=[PURPLE, TEAL], width=0.45)
    ax2.set_ylabel('average turns per episode', fontsize=10)
    ax2.set_title('What the cap saves on average', fontsize=11.3, weight='bold')
    for i, v in enumerate((float(e.turns.mean()), float(e.capped.mean()))):
        ax2.text(i, v + 0.07, f'{v:.2f}', ha='center', fontsize=10.5, weight='bold')
    ax2.set_ylim(0, max(e.turns.mean(), e.capped.mean()) * 1.3)
    ax2.text(0.5, max(e.turns.mean(), e.capped.mean()) * 1.16,
             f'the longest run without a cap took {longest} turns', ha='center',
             fontsize=9.3, color=GRIP)
    fig.text(0.5, 0.005, 'illustrative: 3,000 simulated episodes, seed 31',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'turn-cap.svg')
    print(f'[5b] simulated episodes: mean {e.turns.mean():.2f} turns, longest '
          f'{longest}, {100 * e.hit_cap:.1f}% go past {e.CAP} turns; with the cap '
          f'the mean is {e.capped.mean():.2f}')


def rtu_wall_clock() -> None:
    """Simulated: the time an episode takes, and where a timeout cuts it off."""
    e = _episodes()
    med = float(np.median(e.secs))
    p95 = float(np.percentile(e.secs, 95))
    fig: Figure = plt.figure(figsize=(10.2, 4.2))
    ax: Axes = fig.add_axes((0.09, 0.18, 0.86, 0.62))
    _plain(ax)
    ax.hist(e.secs, bins=60, color=TEAL, alpha=0.9)
    ax.axvline(med, color=INK, lw=1.6)
    ax.axvline(p95, color=JOINT, lw=1.6)
    ax.axvline(e.TIMEOUT, color=GRIP, lw=1.8, ls='--')
    top = ax.get_ylim()[1]
    ax.text(med + 0.5, top * 0.88, f'half finish inside {med:.1f} s', fontsize=9.5,
            color=INK)
    ax.text(p95 + 0.5, top * 0.68, f'one in twenty takes more than {p95:.1f} s',
            fontsize=9.5, color=JOINT)
    ax.text(e.TIMEOUT + 0.5, top * 0.48,
            f'a {e.TIMEOUT:.0f} s timeout cuts off {100 * e.over_timeout:.1f}%',
            fontsize=9.5, color=GRIP)
    ax.set_xlabel('seconds the whole episode took', fontsize=10)
    ax.set_ylabel('episodes', fontsize=10)
    ax.set_title('The time an agent loop takes is not one number but a long tail',
                 fontsize=12, weight='bold')
    fig.text(0.5, 0.005, 'illustrative: 3,000 simulated episodes, seed 31',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'wall-clock.svg')
    print(f'[5c] simulated episode time: median {med:.1f} s, mean '
          f'{e.secs.mean():.1f} s, 95th percentile {p95:.1f} s, longest '
          f'{e.secs.max():.1f} s, {100 * e.over_timeout:.1f}% past '
          f'{e.TIMEOUT:.0f} s')


def rtu_three_guards() -> None:
    """The three guards drawn on the loop, with the numbers they are set to."""
    e = _episodes()
    fig: Figure = plt.figure(figsize=(11.0, 4.3))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.0)
    ax.set_ylim(0, 4.3)
    ax.text(5.5, 4.05, 'Three guards, each on a different failure', ha='center',
            fontsize=12.3, weight='bold')
    rows = [
        ('a wrong argument', GRIP,
         'the model names a tool that\ndoes not exist, or a class that\n'
         'is not in the list',
         'check the call against the tool\'s\nwritten shape before running it,\n'
         'and hand the error back as text'),
        ('a tool that fails', WRIST,
         'the camera is busy, the arm is\nin a fault state, the network\nis down',
         'return the failure as an ordinary\nresult, so the model can try\n'
         'something else rather than stop'),
        ('a loop that never ends', PURPLE,
         'the model asks the same thing\nagain and again because the\n'
         'answer never satisfies it',
         f'stop after {e.CAP} turns, and stop\nthe whole thing after '
         f'{e.TIMEOUT:.0f} seconds\nwhatever state it is in'),
    ]
    ax.text(0.35, 3.62, 'what goes wrong', fontsize=10.5, weight='bold')
    ax.text(3.55, 3.62, 'what it looks like', fontsize=10.5, weight='bold')
    ax.text(7.30, 3.62, 'the plain answer', fontsize=10.5, weight='bold')
    y = 3.30
    for name, col, looks, fix in rows:
        ax.plot([0.3, 10.8], [y + 0.18, y + 0.18], color=GRID, lw=0.8)
        ax.text(0.35, y - 0.08, name, fontsize=10.2, color=col, weight='bold',
                va='top')
        ax.text(3.55, y - 0.08, looks, fontsize=9.3, color=INK, va='top')
        ax.text(7.30, y - 0.08, fix, fontsize=9.3, color=INK, va='top')
        y -= 1.05
    ax.plot([0.3, 10.8], [y + 0.18, y + 0.18], color=GRID, lw=0.8)
    ax.text(0.35, 0.28, 'none of these three is clever, and that is the point: '
            'they are the ordinary guards any program gets\nwhen it calls out to '
            'something it does not control', fontsize=9.8, color=MUTED, va='top')
    _save(fig, RTU_DOC, 'three-guards.svg')
    print(f'[5d] guards drawn: argument check, failure as a result, cap of {e.CAP} '
          f'turns and a {e.TIMEOUT:.0f} second timeout')


# -- section 6: the agent loop ---------------------------------------------

def rtu_agent_loop() -> None:
    """The same loop with a goal instead of a question, on a real cell job."""
    fig: Figure = plt.figure(figsize=(11.2, 4.8))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.8)
    ax.text(5.6, 4.52, 'An agent loop is the tool loop with a goal that outlives '
            'one turn', ha='center', fontsize=12.3, weight='bold')
    _box(ax, 0.35, 3.45, 3.0, 0.75, 'the goal, written once\n'
         '"clear the tray and put\nthe cracked cups in the bin"',
         face='#f2eefa', edge=PURPLE, size=9.3)
    ring = [(4.30, 3.20, '#fdf0d5', JOINT, 'look',
             'call the camera tools,\nread what came back'),
            (7.60, 3.20, '#d9ecec', TEAL, 'decide',
             'write the next step\nas one tool call'),
            (7.60, 1.45, '#eef7f7', TEAL, 'act',
             'the program runs it:\nthe arm moves'),
            (4.30, 1.45, '#f6e2e2', GRIP, 'check',
             'is the goal met yet,\nand did anything fail')]
    for x, y, face, edge, title, body in ring:
        _box(ax, x, y, 2.6, 1.05, '', face=face, edge=edge)
        ax.text(x + 1.3, y + 0.82, title, ha='center', fontsize=10.6, weight='bold',
                color=edge)
        ax.text(x + 1.3, y + 0.40, body, ha='center', va='center', fontsize=9.2)
    _arrow(ax, 6.94, 3.72, 7.56, 3.72, colour=MUTED)
    _arrow(ax, 8.90, 3.18, 8.90, 2.54, colour=MUTED)
    _arrow(ax, 7.56, 1.97, 6.94, 1.97, colour=MUTED)
    _arrow(ax, 5.60, 2.54, 5.60, 3.18, colour=MUTED)
    _arrow(ax, 3.37, 3.72, 4.26, 3.72, colour=PURPLE)
    ax.text(5.76, 2.72, 'not yet', ha='left', fontsize=9, color=MUTED)
    _box(ax, 0.35, 1.45, 3.0, 0.75, 'done, or out of turns,\nor out of time',
         face='#eeeeee', edge=MUTED, size=9.6)
    _arrow(ax, 4.26, 1.97, 3.39, 1.97, colour=GRIP)
    ax.text(0.35, 0.90, 'the model holds no memory between turns except the stream '
            'itself, so the goal, every call and every\nresult stay in the stream, '
            'and the stream is read again from the beginning on every turn',
            fontsize=9.8, color=INK, va='top')
    ax.text(0.35, 0.22, 'that is what makes the loop both simple to write and '
            'expensive to run', fontsize=9.8, color=GRIP)
    _save(fig, RTU_DOC, 'agent-loop.svg')
    print('[6a] drawn the four-station agent loop with a tray-clearing goal')


def rtu_latency_stack() -> None:
    """One simulated episode, turn by turn, with the seconds broken up."""
    e = _episodes()
    parts = e.example
    names = ['waiting for the first token', 'writing the call', 'running the tool']
    cols = [MUTED, PURPLE, TEAL]
    fig: Figure = plt.figure(figsize=(10.0, 4.2))
    ax: Axes = fig.add_axes((0.09, 0.26, 0.87, 0.56))
    _plain(ax)
    x = np.arange(1, len(parts) + 1)
    bottom = np.zeros(len(parts))
    for k, (name, col) in enumerate(zip(names, cols)):
        vals = np.array([p[k] for p in parts])
        ax.bar(x, vals, bottom=bottom, color=col, width=0.55, label=name)
        bottom = bottom + vals
    for xi, tot in zip(x, bottom):
        ax.text(xi, tot + 0.04, f'{tot:.2f} s', ha='center', fontsize=9.3)
    ax.set_xticks(x)
    ax.set_xlabel('turn of the loop', fontsize=10)
    ax.set_ylabel('seconds', fontsize=10)
    ax.set_ylim(0, bottom.max() * 1.25)
    ax.set_title(f'One simulated episode: {len(parts)} turns and '
                 f'{bottom.sum():.1f} seconds in all', fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper center',
              bbox_to_anchor=(0.5, -0.20), ncol=3)
    fig.text(0.5, 0.005, 'illustrative: one episode from the simulation, seed 31',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'latency-stack.svg')
    print(f'[6b] the drawn episode takes {len(parts)} turns and '
          f'{bottom.sum():.2f} s, with the longest turn at {bottom.max():.2f} s')


def rtu_time_spread() -> None:
    """How unpredictable the loop is: the spread of episode times and turns."""
    e = _episodes()
    med = float(np.median(e.secs))
    p95 = float(np.percentile(e.secs, 95))
    fig: Figure = plt.figure(figsize=(10.2, 4.2))
    ax1: Axes = fig.add_axes((0.08, 0.20, 0.36, 0.60))
    ax2: Axes = fig.add_axes((0.57, 0.20, 0.38, 0.60))
    _plain(ax1)
    _plain(ax2)
    ax1.boxplot([e.secs], widths=0.4, showfliers=True,
                flierprops=dict(marker='.', markersize=2.5, markerfacecolor=MUTED,
                                markeredgecolor='none', alpha=0.45),
                medianprops=dict(color=GRIP, lw=2.0))
    ax1.set_yscale('log')
    ax1.set_xticklabels(['one agent loop'], fontsize=10)
    ax1.set_ylabel('seconds to finish', fontsize=10)
    ax1.set_title(f'Half inside {med:.1f} s, but the\nslowest took '
                  f'{e.secs.max():.1f} s', fontsize=11.3, weight='bold')
    qs = np.arange(5, 100, 5)
    ax2.plot(qs, np.percentile(e.secs, qs), 'o-', color=PURPLE, lw=1.9)
    ax2.set_xlabel('share of episodes finished, %', fontsize=10)
    ax2.set_ylabel('seconds', fontsize=10)
    ax2.set_title('The last few are the expensive ones', fontsize=11.3,
                  weight='bold')
    ax2.annotate(f'{p95:.1f} s', xy=(95, p95), xytext=(76, p95 + 1.0), fontsize=9.5,
                 color=JOINT)
    ax2.annotate(f'{med:.1f} s', xy=(50, med), xytext=(34, med + 1.4), fontsize=9.5,
                 color=INK)
    fig.text(0.5, 0.005, 'illustrative: 3,000 simulated episodes, seed 31',
             ha='center', fontsize=9, color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'time-spread.svg')
    print(f'[6c] simulated spread: median {med:.1f} s, 95th percentile {p95:.1f} s, '
          f'slowest {e.secs.max():.1f} s, so the slow end is '
          f'{e.secs.max() / med:.1f} times the middle')


# -- section 7: where this belongs on a robot ------------------------------

CONTROL_HZ: float = 500.0
POLICY_HZ: float = 10.0
DETECTOR_HZ: float = 30.0
TOKEN_MS: float = 1000.0 / TOKENS_PER_SEC


def rtu_two_rates() -> None:
    """One agent loop against the control loop, on the same time axis."""
    e = _episodes()
    med = float(np.median(e.secs))
    cycles = int(med * CONTROL_HZ)
    fig: Figure = plt.figure(figsize=(11.0, 4.3))
    ax: Axes = fig.add_axes((0.06, 0.20, 0.90, 0.58))
    _plain(ax)
    ax.set_xlim(0, med)
    ax.set_ylim(0, 3)
    for k in range(0, cycles, 10):
        ax.plot([k / CONTROL_HZ, k / CONTROL_HZ], [0.35, 0.95], color=TEAL, lw=0.35)
    ax.text(med / 2, 1.15, f'the joint controller: {CONTROL_HZ:.0f} steps a second, '
            f'{cycles:,} of them in this one agent loop\n'
            '(every tenth one drawn, or the lines would touch)',
            ha='center', fontsize=10, color=TEAL)
    for k in range(int(med * POLICY_HZ) + 1):
        ax.plot([k / POLICY_HZ, k / POLICY_HZ], [1.75, 2.15], color=JOINT, lw=1.0)
    ax.text(med / 2, 2.30, f'the movement policy: {POLICY_HZ:.0f} a second, '
            f'{int(med * POLICY_HZ)} of them', ha='center', fontsize=10, color=JOINT)
    ax.add_patch(Rectangle((0.0, 2.55), med, 0.30, facecolor='#e6dcf7',
                           edgecolor=PURPLE, lw=1.3))
    ax.text(med / 2, 2.70, f'one turn of the agent loop, {med:.1f} seconds',
            ha='center', va='center', fontsize=10.5, color=PURPLE, weight='bold')
    ax.set_yticks([])
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_title('In the time the agent takes one decision, the controller has '
                 f'taken {cycles:,}', fontsize=12, weight='bold')
    fig.text(0.5, 0.005, 'the agent time is the median of the simulated episodes; '
             'the two rates are stated assumptions', ha='center', fontsize=9,
             color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'two-rates.svg')
    print(f'[7a] in the median simulated episode of {med:.1f} s the '
          f'{CONTROL_HZ:.0f} Hz controller runs {cycles:,} times and the '
          f'{POLICY_HZ:.0f} Hz policy runs {int(med * POLICY_HZ)} times')


def rtu_rate_ladder() -> None:
    """Every part of the stack on one scale of how often it runs."""
    e = _episodes()
    med = float(np.median(e.secs))
    rows = [('joint controller', 1000.0 / CONTROL_HZ, TEAL,
             'reads the encoders, works out a current, writes it'),
            ('movement policy', 1000.0 / POLICY_HZ, SLIDE,
             'turns a picture and a state into the next arm positions'),
            ('detector and segmenter', 1000.0 / DETECTOR_HZ, WRIST,
             'turns a frame into boxes and masks'),
            ('one language model token', TOKEN_MS, JOINT,
             'one step of writing, and an answer needs hundreds'),
            ('one vision-language answer', 1000.0 * (FIRST_TOKEN + 60 / TOKENS_PER_SEC),
             PURPLE, 'a sentence about the scene, 60 tokens long'),
            ('one agent loop', 1000.0 * med, GRIP,
             'several turns, each with a tool call in it')]
    rows = sorted(rows, key=lambda r: r[1])
    fig: Figure = plt.figure(figsize=(10.8, 4.4))
    ax: Axes = fig.add_axes((0.26, 0.17, 0.71, 0.64))
    _plain(ax)
    y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.56)
    ax.set_xscale('log')
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('how long one run takes, in milliseconds (log scale)', fontsize=10)
    ax.set_xlim(1, 2e5)
    for i, r in enumerate(rows):
        label = f'{r[1]:,.0f} ms' if r[1] >= 10 else f'{r[1]:.0f} ms'
        ax.text(r[1] * 1.3, i, f'{label}   {r[3]}', va='center', fontsize=9)
    ax.set_title('Four orders of magnitude separate the control loop from the '
                 'agent loop', fontsize=12, weight='bold')
    _save(fig, RTU_DOC, 'rate-ladder.svg')
    print('[7b] rate ladder, milliseconds per run: '
          + '; '.join(f'{r[0]} {r[1]:,.1f}' for r in rows))


def rtu_cycle_budget() -> None:
    """One control cycle against one token, so the gap is on the same picture."""
    cycle_ms = 1000.0 / CONTROL_HZ
    parts = [('read the encoders', 0.20, TEAL),
             ('work out the next current', 0.55, SLIDE),
             ('write it to the drivers', 0.25, WRIST),
             ('spare, for safety checks', cycle_ms - 1.00, MUTED)]
    fig: Figure = plt.figure(figsize=(10.4, 4.2))
    ax1: Axes = fig.add_axes((0.07, 0.42, 0.40, 0.40))
    ax2: Axes = fig.add_axes((0.58, 0.22, 0.38, 0.60))
    _plain(ax1)
    _plain(ax2)
    left = 0.0
    for name, v, col in parts:
        ax1.barh([0], [v], left=[left], color=col, height=0.45, label=name)
        left += v
    ax1.set_yticks([])
    ax1.set_xlim(0, cycle_ms)
    ax1.set_xlabel('milliseconds', fontsize=10)
    ax1.set_title(f'One control cycle is {cycle_ms:.0f} ms', fontsize=11.5,
                  weight='bold')
    ax1.legend(fontsize=8.4, frameon=False, loc='upper center',
               bbox_to_anchor=(0.5, -0.50), ncol=2)
    bars = ax2.bar(['one control\ncycle', 'one model\ntoken',
                    'one short\nmodel answer'],
                   [cycle_ms, TOKEN_MS,
                    1000.0 * (FIRST_TOKEN + 60 / TOKENS_PER_SEC)],
                   color=[TEAL, JOINT, PURPLE], width=0.5)
    ax2.set_yscale('log')
    ax2.set_ylabel('milliseconds (log scale)', fontsize=10)
    ax2.set_ylim(1, 1e4)
    for b, v in zip(bars, (cycle_ms, TOKEN_MS,
                           1000.0 * (FIRST_TOKEN + 60 / TOKENS_PER_SEC))):
        ax2.text(b.get_x() + b.get_width() / 2, v * 1.3, f'{v:,.0f} ms',
                 ha='center', fontsize=9.8)
    ax2.set_title(f'One token alone is {TOKEN_MS / cycle_ms:.0f} cycles long',
                  fontsize=11.5, weight='bold')
    fig.text(0.98, 0.02, 'illustrative: the parts of the cycle are stated '
             'assumptions, the ratios follow from them', ha='right', fontsize=9,
             color=MUTED, style='italic')
    _save(fig, RTU_DOC, 'cycle-budget.svg')
    print(f'[7c] one control cycle is {cycle_ms:.0f} ms and one token is '
          f'{TOKEN_MS:.0f} ms, which is {TOKEN_MS / cycle_ms:.0f} cycles; a '
          f'60-token answer is '
          f'{1000.0 * (FIRST_TOKEN + 60 / TOKENS_PER_SEC) / cycle_ms:.0f} cycles')


def rtu_boundary() -> None:
    """Exactly where the line sits, and what crosses it in each direction."""
    e = _episodes()
    med = float(np.median(e.secs))
    fig: Figure = plt.figure(figsize=(11.2, 4.8))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.8)
    ax.text(5.6, 4.52, 'The line, and the only two things that cross it',
            ha='center', fontsize=12.3, weight='bold')
    ax.plot([0.3, 10.9], [2.42, 2.42], color=GRIP, lw=2.2)
    ax.text(10.85, 2.52, 'the line', fontsize=10, color=GRIP, ha='right')
    above = [(0.4, 'the agent loop', f'about {med:.0f} s a turn'),
             (3.1, 'the vision-language model', 'about 2 s an answer'),
             (6.2, 'a planner or a behaviour tree', 'tens of milliseconds'),
             (8.9, 'the operator', 'whenever they ask')]
    for x, name, rate in above:
        _box(ax, x, 3.30, 2.45 if x < 8.5 else 2.0, 0.78, '', face='#e6dcf7',
             edge=PURPLE)
        ax.text(x + (1.22 if x < 8.5 else 1.0), 3.88, name, ha='center',
                fontsize=9.8, weight='bold', color=PURPLE)
        ax.text(x + (1.22 if x < 8.5 else 1.0), 3.55, rate, ha='center',
                fontsize=9.2, color=INK)
    below = [(0.4, 'the movement policy', f'{POLICY_HZ:.0f} a second'),
             (3.1, 'the detector and segmenter', f'{DETECTOR_HZ:.0f} a second'),
             (6.2, 'the joint controller', f'{CONTROL_HZ:.0f} a second'),
             (8.9, 'the safety stop', 'hardware, always')]
    for x, name, rate in below:
        _box(ax, x, 1.25, 2.45 if x < 8.5 else 2.0, 0.78, '', face='#d9ecec',
             edge=TEAL)
        ax.text(x + (1.22 if x < 8.5 else 1.0), 1.83, name, ha='center',
                fontsize=9.8, weight='bold', color=TEAL)
        ax.text(x + (1.22 if x < 8.5 else 1.0), 1.50, rate, ha='center',
                fontsize=9.2, color=INK)
    ax.annotate('', xy=(3.3, 2.15), xytext=(3.3, 3.25),
                arrowprops=dict(arrowstyle='-|>', color=PURPLE, lw=2.0))
    ax.text(3.45, 3.02, 'down: a goal in words, and nothing else', fontsize=10,
            color=PURPLE, va='center')
    ax.annotate('', xy=(8.3, 3.25), xytext=(8.3, 2.15),
                arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=2.0))
    ax.text(8.15, 2.22, 'up: did it work, and what was seen', fontsize=10,
            color=TEAL, va='center', ha='right')
    ax.text(0.4, 0.82, 'above the line nothing has a deadline, and a slow answer '
            'only makes the robot wait', fontsize=10.2, color=PURPLE, va='top')
    ax.text(0.4, 0.46, 'below the line everything has a deadline, and a missed one '
            'is a dropped cup or a fault', fontsize=10.2, color=TEAL, va='top')
    ax.text(0.4, 0.10, 'so no model that writes tokens may ever sit inside the '
            'control loop, however good its answers are', fontsize=10.2,
            color=GRIP, va='top', weight='bold')
    _save(fig, RTU_DOC, 'boundary.svg')
    print(f'[7d] drawn the boundary: four parts above it and four below, with a '
          f'{med:.0f} s agent turn on top and a {1000 / CONTROL_HZ:.0f} ms control '
          f'cycle below')


# ==========================================================================
# the runner
# ==========================================================================

VLM_FIGURES = [
    vlm_two_halves, vlm_vector_lengths, vlm_parameter_shares,
    vlm_projector_arithmetic, vlm_projector_shapes, vlm_projector_kinds,
    vlm_projector_pulls_in,
    vlm_token_stream, vlm_context_share, vlm_pictures_that_fit, vlm_attention_cost,
    vlm_freeze_stages, vlm_stage_memory, vlm_order_curves,
    vlm_squeezed_picture, vlm_tiling_layout, vlm_token_bill, vlm_detail_curve,
    vlm_position_grain, vlm_object_size, vlm_counting_grid, vlm_box_grain,
    vlm_class_list, vlm_questions, vlm_handover,
]

RTU_FIGURES = [
    rtu_working_out_stream, rtu_one_token_at_a_time, rtu_written_vs_silent,
    rtu_accuracy_vs_tokens, rtu_time_vs_tokens, rtu_accuracy_per_second,
    rtu_vote_curve, rtu_vote_cost, rtu_search_tree, rtu_search_curve,
    rtu_tool_loop, rtu_tool_transcript, rtu_tool_vs_no_tool, rtu_tool_cost,
    rtu_argument_check, rtu_turn_cap, rtu_wall_clock, rtu_three_guards,
    rtu_agent_loop, rtu_latency_stack, rtu_time_spread,
    rtu_two_rates, rtu_rate_ladder, rtu_cycle_budget, rtu_boundary,
]


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    for fn in VLM_FIGURES + RTU_FIGURES:
        fn()
    print(f'wrote {len(VLM_FIGURES) + len(RTU_FIGURES)} diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
