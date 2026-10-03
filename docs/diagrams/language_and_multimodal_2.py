"""Generate the diagrams for two pages of docs/06_neural-networks/10_language-and-multimodal-models/.

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
* The vector clouds that show the projector pulling picture vectors into the
  token embedding space are simulated with numpy.random.default_rng(3), and the
  cosine similarities and lengths drawn from them are real arithmetic on those
  simulated vectors.
* The training curves, the accuracy-against-working-out curves, the vote
  curves, the beam search curves, the argument validation counts and the turn
  counts on the reasoning page are all Monte Carlo simulations with the seeds
  given in each function, run on the simple made-up task described in the
  function. They are drawn to show the shape of a trade and are labelled
  illustrative in the figures and in the pages. They are not benchmark scores.
"""

import pathlib
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
    """Simulated: the two kinds of vector sit at different lengths and angles."""
    rng = np.random.default_rng(3)
    patch = rng.normal(0.0, 1.0, size=(PIC_TOKENS, 64)) * 2.9 + 0.8
    tokens = rng.normal(0.0, 1.0, size=(400, 64)) * 0.42
    lp = np.linalg.norm(patch, axis=1)
    lt = np.linalg.norm(tokens, axis=1)

    def cos_to(a: Arr, b: Arr) -> Arr:
        an = a / np.linalg.norm(a, axis=1, keepdims=True)
        bn = b / np.linalg.norm(b, axis=1, keepdims=True)
        return (an @ bn.T).ravel()

    cross = cos_to(patch, tokens)
    within = cos_to(tokens[:200], tokens[200:])

    fig: Figure = plt.figure(figsize=(11.0, 3.9))
    ax1: Axes = fig.add_axes((0.06, 0.17, 0.40, 0.66))
    ax2: Axes = fig.add_axes((0.57, 0.17, 0.40, 0.66))
    _plain(ax1)
    _plain(ax2)

    ax1.hist(lt, bins=28, color=PURPLE, alpha=0.85, label='token embeddings')
    ax1.hist(lp, bins=28, color=TEAL, alpha=0.85, label='backbone patch vectors')
    ax1.set_xlabel('length of the vector', fontsize=10)
    ax1.set_ylabel('how many vectors', fontsize=10)
    ax1.set_title(f'Lengths differ by about {lp.mean() / lt.mean():.0f} times',
                  fontsize=11.5, weight='bold')
    ax1.legend(fontsize=9, frameon=False)

    ax2.hist(cross, bins=40, color=GRIP, alpha=0.8, density=True,
             label='patch vector against token embedding')
    ax2.hist(within, bins=40, color=PURPLE, alpha=0.6, density=True,
             label='token embedding against token embedding')
    ax2.axvline(0.0, color=INK, lw=0.9, ls=':')
    ax2.set_xlabel('cosine similarity', fontsize=10)
    ax2.set_ylabel('share of pairs', fontsize=10)
    ax2.set_title('Neither set points the same way as the other',
                  fontsize=11.5, weight='bold')
    ax2.legend(fontsize=8.5, frameon=False, loc='upper left')
    fig.text(0.5, 0.005, 'simulated vectors, seed 3', ha='center', fontsize=9,
             color=MUTED, style='italic')
    _save(fig, VLM_DOC, 'vector-lengths.svg')
    print(f'[1b] simulated mean length: patch vectors {lp.mean():.2f}, '
          f'token embeddings {lt.mean():.2f}, ratio {lp.mean() / lt.mean():.1f}; '
          f'mean cross cosine {cross.mean():+.3f}')


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
                 f'{100 * PROJ_1 / total:.2f}% of the parameters',
                 fontsize=12, weight='bold')
    ax.tick_params(axis='x', labelsize=9.5)
    _save(fig, VLM_DOC, 'parameter-shares.svg')
    print(f'[1c] backbone {_thousands(V_PARAMS)}, language model {_thousands(L_PARAMS)}, '
          f'projector {_thousands(PROJ_1)}, whole {_thousands(total)}, '
          f'projector share {100 * PROJ_1 / total:.4f}%')


# -- section 2: the projector ----------------------------------------------

def _toy_projection() -> tuple[Arr, Arr, Arr, Arr]:
    """A 6-number patch vector through a 6 -> 4 matrix, worked out in full."""
    v = np.array([0.40, -0.90, 1.30, 0.20, -0.50, 0.70])
    w = np.array([
        [0.5, -0.2, 0.9, 0.1, -0.4, 0.3],
        [-0.7, 0.6, 0.2, -0.3, 0.8, 0.1],
        [0.2, 0.4, -0.6, 0.7, 0.1, -0.5],
        [0.9, -0.1, 0.3, -0.8, 0.2, 0.6],
    ])
    b = np.array([0.10, -0.20, 0.05, 0.00])
    out = w @ v + b
    return v, w, b, out


def vlm_projector_arithmetic() -> None:
    """One patch vector multiplied by the projector matrix, every number shown."""
    v, w, b, out = _toy_projection()
    fig: Figure = plt.figure(figsize=(11.2, 4.4))
    ax: Axes = fig.add_axes((0, 0, 1, 1))
    _blank(ax)
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.4)
    ax.text(5.6, 4.12, 'The projector is one matrix multiply and one add',
            ha='center', fontsize=12.5, weight='bold')

    cw, ch = 0.52, 0.42
    x0, y0 = 0.45, 2.25
    for j, val in enumerate(v):
        ax.add_patch(Rectangle((x0 + j * cw, y0), cw, ch, facecolor='#d9ecec',
                               edgecolor='white', lw=1.0))
        ax.text(x0 + (j + 0.5) * cw, y0 + ch / 2, f'{val:+.2f}', ha='center',
                va='center', fontsize=9, color=INK)
    ax.text(x0 + 3 * cw, y0 + ch + 0.22, f'one patch vector, {len(v)} numbers',
            ha='center', fontsize=10, color=TEAL, weight='bold')

    mx, my = 0.45, 0.25
    for i in range(w.shape[0]):
        for j in range(w.shape[1]):
            ax.add_patch(Rectangle((mx + j * cw, my + (3 - i) * ch), cw, ch,
                                   facecolor='#fdf0d5', edgecolor='white', lw=1.0))
            ax.text(mx + (j + 0.5) * cw, my + (3 - i + 0.5) * ch, f'{w[i, j]:+.1f}',
                    ha='center', va='center', fontsize=8.5, color=INK)
    ax.text(mx + 3 * cw, my - 0.22, f'the projector matrix, {w.shape[0]} rows '
            f'of {w.shape[1]}', ha='center', fontsize=10, color=JOINT, weight='bold')

    lines = []
    for i in range(w.shape[0]):
        parts = ' + '.join(f'({w[i, j]:+.1f} x {v[j]:+.2f})' for j in range(len(v)))
        lines.append(f'row {i + 1}:  {parts}  = {float(w[i] @ v):+.3f}'
                     f'   then {b[i]:+.2f}  = {out[i]:+.3f}')
    ax.text(4.25, 2.05, '\n'.join(lines), ha='left', va='center', fontsize=8.6,
            family='DejaVu Sans Mono', color=INK)
    ax.text(4.25, 3.08, 'each row of the matrix gives one output number',
            ha='left', fontsize=10, color=MUTED)

    ox = 4.25
    for i, val in enumerate(out):
        ax.add_patch(Rectangle((ox + i * 0.78, 0.45), 0.78, ch, facecolor='#e6dcf7',
                               edgecolor='white', lw=1.0))
        ax.text(ox + (i + 0.5) * 0.78, 0.45 + ch / 2, f'{val:+.3f}', ha='center',
                va='center', fontsize=9.5, color=INK)
    ax.text(ox + 2 * 0.78, 0.18, f'out: {len(out)} numbers, which the language model '
            'now treats as a token', ha='center', fontsize=10, color=PURPLE,
            weight='bold')
    _save(fig, VLM_DOC, 'projector-arithmetic.svg')
    print('[2a] toy projector output: '
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
        ax.legend(fontsize=8.5, frameon=False, loc='upper left')
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
    for k in (2, 5, 8):
        ax.annotate(f'{tiled[k] ** 2 / 1e6:.1f}M', xy=(k, tiled[k] ** 2 / 1e6),
                    xytext=(k - 0.45, tiled[k] ** 2 / 1e6 + 18), fontsize=9,
                    color=GRIP)
    ax.annotate(f'{one[8] ** 2 / 1e6:.2f}M', xy=(8, one[8] ** 2 / 1e6),
                xytext=(6.6, 40), fontsize=9, color=TEAL,
                arrowprops=dict(arrowstyle='-', color=TEAL, lw=0.8))
    _save(fig, VLM_DOC, 'attention-cost.svg')
    print(f'[3d] attention pairs with 8 pictures: squeezed {one[8] ** 2:,}, '
          f'tiled {tiled[8] ** 2:,}, which is '
          f'{(tiled[8] ** 2) / (one[8] ** 2):.0f} times as much work')
