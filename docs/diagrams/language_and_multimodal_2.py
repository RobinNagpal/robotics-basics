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
