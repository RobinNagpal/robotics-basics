"""Generate the diagrams for the last two pages of docs/05_neural-networks/12_models-that-act/.

    03_vision-language-action-models.md -> images/models-that-act/vision-language-action-models/
    04_world-models.md                  -> images/models-that-act/world-models/

Run with:  python3 models_that_act_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so the two documents can quote the same values.

What is simulated, and what is real:

* The robot episodes on the vision-language-action page are simulated. Each
  episode is a smooth six-joint trajectory built from three sine waves per
  joint with amplitudes, frequencies and phases drawn from a seeded generator,
  plus a gripper command that closes once. The joint position deltas are the
  differences of that trajectory at 20 readings a second.
* Everything done to those episodes is real arithmetic: the per-dimension
  percentile normalisation, the binning, the measured
  quantisation error, the integrated drift, the discrete cosine transform
  compression, and the flow-matching action head, which is a small network
  trained in NumPy by gradient descent.
* The catastrophic-forgetting and cross-embodiment experiments are small
  networks trained in NumPy on simulated data, with the two-link arm geometry
  and its Jacobian worked out exactly.
* The world-model page uses one simulated system: a one-joint arm (a pendulum)
  with viscous damping, a torque input and a hard stop at 0.45 radians. The
  step function is exact for that system, and it stands in for "the truth".
  The learned dynamics model is a real least-squares fit of degree-two
  polynomial features to noisy transitions from that system, and the pictures
  of the camera images, the principal-component latent space, the planner and
  the energy drift are all measured from that fit.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'models-that-act'
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

VLA_DOC: str = 'vision-language-action-models'
WM_DOC: str = 'world-models'

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


def _blank(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)
    ax.set_facecolor('white')


def _box(ax: Axes, x: float, y: float, w: float, h: float, label: str,
         fc: str = 'white', ec: str = INK, fs: float = 9.5,
         tc: str = INK, weight: str = 'normal') -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.02',
                                linewidth=1.3, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, label, ha='center', va='center', fontsize=fs,
            color=tc, zorder=3, weight=weight, linespacing=1.45)


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.3) -> None:
    ax.add_patch(FancyArrow(x0, y0, x1 - x0, y1 - y0, width=0.0014,
                            head_width=0.016, head_length=0.022,
                            length_includes_head=True, color=colour,
                            linewidth=lw, zorder=4))


def _rmse(a: Arr, b: Arr) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


# ==========================================================================
# PART A -- the simulated robot episodes used by the whole of page 3
# ==========================================================================

CONTROL_HZ: float = 20.0
N_JOINTS: int = 6
ACTION_DIM: int = 7           # six joint deltas and one gripper command
CHUNK: int = 10               # actions per chunk
LEVER_M: float = 0.60         # distance from a joint to the fingertip, in metres

JOINT_NAMES: list[str] = ['joint 1', 'joint 2', 'joint 3',
                          'joint 4', 'joint 5', 'joint 6']


def make_episodes(n_ep: int, horizon: int, seed: int) -> tuple[Arr, Arr]:
    """Simulated teleoperation episodes.

    Returns the joint angles (n_ep, horizon + 1, 6) in radians and the actions
    (n_ep, horizon, 7), where the first six action numbers are joint position
    deltas for one control step and the seventh is the gripper command.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(horizon + 1) / CONTROL_HZ
    q = np.zeros((n_ep, horizon + 1, N_JOINTS))
    for e in range(n_ep):
        for j in range(N_JOINTS):
            curve = np.zeros_like(t)
            for _k in range(3):
                amp = rng.uniform(0.05, 0.45)
                freq = rng.uniform(0.05, 0.35)
                phase = rng.uniform(0.0, 2 * np.pi)
                curve += amp * np.sin(2 * np.pi * freq * t + phase)
            q[e, :, j] = curve
    dq = np.diff(q, axis=1)
    grip = np.zeros((n_ep, horizon, 1))
    for e in range(n_ep):
        close_at = int(rng.uniform(0.35, 0.75) * horizon)
        grip[e, close_at:, 0] = 1.0
    actions = np.concatenate([dq, grip], axis=2)
    return q, actions


class Episodes:
    """The simulated episodes and the numbers every later section needs."""

    def __init__(self) -> None:
        self.horizon = 300
        self.n_train = 240
        self.n_test = 60
        self.q_train, self.a_train = make_episodes(self.n_train, self.horizon, seed=11)
        self.q_test, self.a_test = make_episodes(self.n_test, self.horizon, seed=12)
        flat = self.a_train.reshape(-1, ACTION_DIM)
        self.lo = np.percentile(flat, 1.0, axis=0)
        self.hi = np.percentile(flat, 99.0, axis=0)
        self.span = self.hi - self.lo
        self.flat_test = self.a_test.reshape(-1, ACTION_DIM)

    def normalise(self, a: Arr) -> Arr:
        """Map each action number to the range -1 to 1 using the 1st and 99th percentile."""
        z = 2.0 * (a - self.lo) / self.span - 1.0
        return np.clip(z, -1.0, 1.0)

    def denormalise(self, z: Arr) -> Arr:
        return (z + 1.0) / 2.0 * self.span + self.lo


EP: Episodes = Episodes()


def bin_uniform(z: Arr, n_bins: int) -> Arr:
    """Round each number in -1..1 to the middle of one of n_bins equal bins."""
    idx = np.clip(((z + 1.0) / 2.0 * n_bins).astype(int), 0, n_bins - 1)
    return (idx + 0.5) / n_bins * 2.0 - 1.0


def bin_quantile(z: Arr, n_bins: int, ref: Arr) -> Arr:
    """Round each number to the middle of a bin whose edges are the data's own quantiles."""
    out = np.empty_like(z)
    for d in range(z.shape[1]):
        edges = np.quantile(ref[:, d], np.linspace(0.0, 1.0, n_bins + 1))
        edges[0], edges[-1] = -1.0000001, 1.0000001
        centres = 0.5 * (edges[:-1] + edges[1:])
        idx = np.clip(np.searchsorted(edges, z[:, d], side='right') - 1, 0, n_bins - 1)
        out[:, d] = centres[idx]
    return out


def dct_matrix(n: int) -> Arr:
    """The orthonormal discrete cosine transform matrix of size n."""
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    m = np.cos(np.pi * (i + 0.5) * k / n)
    m[0, :] *= np.sqrt(1.0 / n)
    m[1:, :] *= np.sqrt(2.0 / n)
    return m


# ==========================================================================
# PART B -- page 3, section 1: what a vision-language-action model is
# ==========================================================================

IMG_SIDE: int = 224
PATCH: int = 14
WIDTH: int = 1024             # the width of one token inside the model
VOCAB: int = 32000
N_CAMERAS: int = 2
INSTRUCTION: str = 'pick up the red block and put it in the bowl'

PATCHES_PER_SIDE: int = IMG_SIDE // PATCH
PATCHES: int = PATCHES_PER_SIDE ** 2
TEXT_TOKENS: int = len(INSTRUCTION.split()) + 1       # one per short word, plus an end marker
STATE_TOKENS: int = 1
PREFIX_TOKENS: int = N_CAMERAS * PATCHES + TEXT_TOKENS + STATE_TOKENS
ACTION_TOKENS: int = CHUNK * ACTION_DIM


def vla_input_output() -> None:
    """The real input and the real output of one call, with the counts worked out."""
    obs_q = EP.q_test[0, 100, :]
    chunk = EP.a_test[0, 100:100 + CHUNK, :]
    print('[vla-io] picture numbers per camera =', IMG_SIDE * IMG_SIDE * 3)
    print('[vla-io] patches per camera =', PATCHES, f'({PATCHES_PER_SIDE} by {PATCHES_PER_SIDE})')
    print('[vla-io] text tokens =', TEXT_TOKENS, 'state tokens =', STATE_TOKENS)
    print('[vla-io] prefix tokens =', PREFIX_TOKENS, 'action numbers out =', ACTION_TOKENS)
    print('[vla-io] joint state (rad) =', np.round(obs_q, 3))
    print('[vla-io] first action of the chunk (rad) =', np.round(chunk[0], 4))

    fig, ax = plt.subplots(figsize=(11.8, 5.8), facecolor='white')
    _blank(ax, (0, 1), (0.065, 1.0))
    ax.text(0.5, 0.975, 'One call of a vision-language-action model: '
            f'{PREFIX_TOKENS} tokens in, {ACTION_TOKENS} numbers out',
            ha='center', va='center', fontsize=12.5, weight='bold', color=INK)

    # the two camera pictures, drawn as real patch grids
    side = 0.175
    for y0, name in [(0.730, 'wrist camera'), (0.460, 'scene camera')]:
        x0 = 0.03
        for r in range(PATCHES_PER_SIDE):
            for k in range(PATCHES_PER_SIDE):
                ax.add_patch(Rectangle((x0 + k * side / PATCHES_PER_SIDE,
                                        y0 + r * side / PATCHES_PER_SIDE),
                                       side / PATCHES_PER_SIDE, side / PATCHES_PER_SIDE,
                                       facecolor=LINK_PALE if (r + k) % 2 else 'white',
                                       edgecolor=GRID, linewidth=0.4))
        ax.add_patch(Rectangle((x0, y0), side, side, facecolor='none',
                               edgecolor=LINK, linewidth=1.6))
        ax.text(x0 + side / 2, y0 - 0.014,
                f'{name}\n{IMG_SIDE} by {IMG_SIDE} pixels, {PATCHES} patches',
                ha='center', va='top', fontsize=8.6, color=INK)

    _box(ax, 0.022, 0.250, 0.268, 0.105,
         f'instruction, {TEXT_TOKENS} tokens\n"{INSTRUCTION}"',
         fc='#eee9f7', ec=PURPLE, fs=7.9)
    _box(ax, 0.022, 0.105, 0.268, 0.095,
         f'joint state, {N_JOINTS} numbers, 1 token\n'
         + ', '.join(f'{v:.2f}' for v in obs_q[:4]) + ', ...',
         fc='#fff6e0', ec=JOINT, fs=8.6)

    _box(ax, 0.345, 0.125, 0.165, 0.76,
         'one model\n\nvision\nbackbone\n+\nlanguage\nmodel\n+\naction\noutput\n\n'
         f'{PREFIX_TOKENS} tokens\nin the\nsequence',
         fc='#eaf3fb', ec=LINK, fs=9.6)
    _arrow(ax, 0.212, 0.8175, 0.34, 0.520, colour=MUTED)
    _arrow(ax, 0.212, 0.5475, 0.34, 0.510, colour=MUTED)
    _arrow(ax, 0.298, 0.3025, 0.34, 0.490, colour=MUTED)
    _arrow(ax, 0.298, 0.1525, 0.34, 0.480, colour=MUTED)

    # the action chunk as the real table of numbers
    tx, ty, cw, ch = 0.620, 0.185, 0.051, 0.059
    heads = ['j1', 'j2', 'j3', 'j4', 'j5', 'j6', 'grip']
    for d, h in enumerate(heads):
        ax.text(tx + d * cw + cw / 2, ty + CHUNK * ch + 0.018, h,
                ha='center', va='bottom', fontsize=8.8, weight='bold', color=INK)
    for s_i in range(CHUNK):
        yy = ty + (CHUNK - 1 - s_i) * ch
        ax.text(tx - 0.008, yy + ch / 2, f'step {s_i}', ha='right', va='center',
                fontsize=8, color=MUTED)
        for d in range(ACTION_DIM):
            v = chunk[s_i, d]
            ax.add_patch(Rectangle((tx + d * cw, yy), cw, ch, facecolor='white',
                                   edgecolor=GRID, linewidth=0.5))
            txt = f'{v:+.3f}' if d < N_JOINTS else f'{v:.0f}'
            ax.text(tx + d * cw + cw / 2, yy + ch / 2, txt, ha='center', va='center',
                    fontsize=7.4, color=INK if d < N_JOINTS else GRIP)
    ax.add_patch(Rectangle((tx, ty), ACTION_DIM * cw, CHUNK * ch, facecolor='none',
                           edgecolor=SLIDE, linewidth=1.8))
    ax.text(tx + ACTION_DIM * cw / 2, ty - 0.025,
            f'the action chunk: {CHUNK} steps by {ACTION_DIM} numbers = {ACTION_TOKENS} numbers,\n'
            f'joint deltas in radians, covering {CHUNK / CONTROL_HZ:.2f} s at '
            f'{CONTROL_HZ:.0f} commands a second',
            ha='center', va='top', fontsize=9, color=INK)
    _arrow(ax, 0.516, 0.505, 0.548, 0.505, colour=SLIDE, lw=1.6)
    _save(fig, VLA_DOC, 'vla-input-output.svg')


def same_picture_two_sentences() -> None:
    """The same scene with two instructions gives two different chunks of joint deltas."""
    a = EP.a_test[3, 40:40 + CHUNK, :]
    b = EP.a_test[17, 160:160 + CHUNK, :]
    sep = float(np.sqrt(np.mean((a[:, :N_JOINTS] - b[:, :N_JOINTS]) ** 2)))
    print(f'[two-sentences] the two chunks differ by {np.degrees(sep):.2f} deg per joint per step '
          f'({sep:.4f} rad), while one chunk moves {np.degrees(np.abs(a[:, :N_JOINTS]).mean()):.2f} '
          'deg per joint per step on average')
    steps = np.arange(CHUNK)
    lim = float(np.degrees(np.abs(np.concatenate([a, b])[:, :N_JOINTS]).max())) * 1.18
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5), facecolor='white')
    titles = [f'"{INSTRUCTION}"', '"put the block on the shelf"']
    lines = []
    for ax, chunk, title in zip(axes, [a, b], titles):
        _plain(ax)
        for j, colour in enumerate([LINK, SLIDE, JOINT, PURPLE, TEAL, WRIST]):
            ln, = ax.plot(steps, np.degrees(chunk[:, j]), marker='o', ms=3.5, lw=1.6,
                          color=colour, label=JOINT_NAMES[j])
            if ax is axes[0]:
                lines.append(ln)
        ax.axhline(0, color=GRID, lw=1)
        ax.set_xlabel('step inside the chunk', fontsize=10)
        ax.set_ylabel('commanded joint movement (degrees)', fontsize=10)
        ax.set_ylim(-lim, lim)
        ax.set_title(title, fontsize=11, weight='bold')
    fig.legend(lines, JOINT_NAMES, fontsize=9.5, frameon=False, ncol=6,
               loc='lower center', bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('Same cameras, same joint state, two instructions: the chunk the model '
                 'returns is not the same', fontsize=12, weight='bold')
    fig.tight_layout(rect=(0, 0.06, 1, 0.93))
    _save(fig, VLA_DOC, 'same-picture-two-sentences.svg')


N_TASKS: int = 12
DEMOS_PER_TASK: int = 150


def one_model_many_tasks() -> None:
    """How many episodes each trained model gets to learn from."""
    total = N_TASKS * DEMOS_PER_TASK
    frames_single = DEMOS_PER_TASK * EP.horizon
    frames_shared = total * EP.horizon
    print(f'[many-tasks] {N_TASKS} tasks at {DEMOS_PER_TASK} demonstrations each = {total} episodes')
    print(f'[many-tasks] one single-task policy sees {DEMOS_PER_TASK} episodes = '
          f'{frames_single} frames; one shared policy sees {total} episodes = {frames_shared} frames')
    print(f'[many-tasks] the shared policy sees {frames_shared / frames_single:.0f} times as many frames')

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['one policy\nper task', 'one shared\npolicy'], [1, N_TASKS],
                  color=[GRIP, SLIDE], width=0.55)
    ax.bar_label(bars, labels=[f'{DEMOS_PER_TASK} episodes', f'{total} episodes'],
                 fontsize=10, padding=4)
    ax.set_ylabel(f'episodes one trained model learns from\n(as multiples of {DEMOS_PER_TASK})',
                  fontsize=10)
    ax.set_ylim(0, N_TASKS * 1.25)
    ax.set_title(f'With {N_TASKS} tasks and {DEMOS_PER_TASK} demonstrations each',
                 fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    tasks = np.arange(1, N_TASKS + 1)
    ax.plot(tasks, tasks, marker='o', color=GRIP, lw=2, label='separate policies to train and keep')
    ax.plot(tasks, np.ones_like(tasks), marker='s', color=SLIDE, lw=2,
            label='one instruction-conditioned policy')
    ax.set_xlabel('number of tasks the arm must do', fontsize=10)
    ax.set_ylabel('number of trained models to keep working', fontsize=10)
    ax.set_xticks(tasks)
    ax.set_yticks(range(0, N_TASKS + 1, 2))
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Every new task adds a model, or it adds a sentence',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'one-model-many-tasks.svg')


# ==========================================================================
# PART C -- page 3, section 2: the body of the model, with real shapes
# ==========================================================================

HEAD_WIDTH: int = 256
HEAD_LAYERS: int = 3


def vla_body_shapes() -> None:
    """Every shape inside one call, worked out from the picture size and the model width."""
    px = IMG_SIDE * IMG_SIDE * 3
    per_patch = PATCH * PATCH * 3
    proj_weights = per_patch * WIDTH
    embed_table = VOCAB * WIDTH
    state_proj = N_JOINTS * WIDTH
    seq_numbers = PREFIX_TOKENS * WIDTH
    pairs = PREFIX_TOKENS ** 2
    print(f'[body] one picture = {px} numbers; one patch = {per_patch} numbers')
    print(f'[body] patch projection = {per_patch} x {WIDTH} = {proj_weights} weights')
    print(f'[body] word embedding table = {VOCAB} x {WIDTH} = {embed_table} numbers')
    print(f'[body] state projection = {N_JOINTS} x {WIDTH} = {state_proj} weights')
    print(f'[body] sequence = {PREFIX_TOKENS} tokens x {WIDTH} = {seq_numbers} numbers')
    print(f'[body] attention compares {PREFIX_TOKENS} x {PREFIX_TOKENS} = {pairs} pairs of tokens')

    stages = [
        ('two camera pictures',
         f'2 x {IMG_SIDE} x {IMG_SIDE} x 3 = {2 * px:,} numbers go in', LINK),
        ('cut into patches',
         f'{PATCHES_PER_SIDE} x {PATCHES_PER_SIDE} = {PATCHES} patches a camera, '
         f'each patch {PATCH} x {PATCH} x 3 = {per_patch} numbers', LINK),
        ('patch projection',
         f'one layer of {per_patch} x {WIDTH} = {proj_weights:,} weights turns each patch\n'
         f'into one token of {WIDTH} numbers, giving {N_CAMERAS * PATCHES} picture tokens', TEAL),
        ('instruction and state',
         f'{TEXT_TOKENS} word tokens looked up in a table of {VOCAB:,} x {WIDTH} = '
         f'{embed_table:,} numbers,\nand the {N_JOINTS} joint readings through a '
         f'{N_JOINTS} x {WIDTH} layer, which is {STATE_TOKENS} more token', PURPLE),
        ('one sequence',
         f'{N_CAMERAS * PATCHES} + {TEXT_TOKENS} + {STATE_TOKENS} = {PREFIX_TOKENS} tokens, '
         f'so {PREFIX_TOKENS} x {WIDTH} = {seq_numbers:,} numbers in all', JOINT),
        ('transformer blocks',
         f'attention compares every token with every token:\n{PREFIX_TOKENS} x '
         f'{PREFIX_TOKENS} = {pairs:,} pairs, in every head of every block', GRIP),
        ('action output',
         f'{CHUNK} steps x {ACTION_DIM} numbers = {ACTION_TOKENS} numbers, which is the chunk '
         'the arm runs', SLIDE),
    ]
    fig, ax = plt.subplots(figsize=(11.6, 7.0), facecolor='white')
    _blank(ax, (0, 1), (0, 1))
    ax.text(0.5, 0.975, 'The real shapes inside one call, for a model whose token width is '
            f'{WIDTH}', ha='center', va='center', fontsize=12.5, weight='bold', color=INK)
    n = len(stages)
    top, bottom = 0.915, 0.115
    h = (top - bottom) / n - 0.018
    for i, (title, body, colour) in enumerate(stages):
        y = top - (i + 1) * (h + 0.018) + 0.018
        _box(ax, 0.015, y, 0.215, h, title, fc='white', ec=colour, fs=9.4,
             tc=colour, weight='bold')
        _box(ax, 0.245, y, 0.74, h, body, fc='white', ec=GRID, fs=9.0)
        if i < n - 1:
            _arrow(ax, 0.1225, y - 0.001, 0.1225, y - 0.017, colour=MUTED)
    ax.text(0.5, 0.055, 'Every number here follows from three choices only: the picture size '
            f'({IMG_SIDE} pixels), the patch size ({PATCH} pixels) and the token width '
            f'({WIDTH}).', ha='center', va='center', fontsize=9.8, color=INK)
    _save(fig, VLA_DOC, 'vla-body-shapes.svg')


def resolution_and_tokens() -> None:
    """What a sharper camera picture costs the model."""
    sides = [224, 336, 448, 672]
    patches = [(s // PATCH) ** 2 for s in sides]
    seqs = [N_CAMERAS * p + TEXT_TOKENS + STATE_TOKENS for p in patches]
    pairs = [s ** 2 for s in seqs]
    base = pairs[0]
    for s, p, q, pr in zip(sides, patches, seqs, pairs):
        print(f'[resolution] {s}px -> {p} patches a camera -> sequence {q} -> {pr:,} token pairs '
              f'({pr / base:.1f} times the {sides[0]}px cost)')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar([str(s) for s in sides], seqs, color=[LINK, TEAL, JOINT, GRIP], width=0.6)
    ax.bar_label(bars, fmt='%d', fontsize=10, padding=3)
    ax.set_xlabel('picture size in pixels along one side', fontsize=10)
    ax.set_ylabel('tokens in the sequence (two cameras)', fontsize=10)
    ax.set_ylim(0, max(seqs) * 1.18)
    ax.set_title('A sharper picture is more tokens', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    rel = [p / base for p in pairs]
    bars = ax.bar([str(s) for s in sides], rel, color=[LINK, TEAL, JOINT, GRIP], width=0.6)
    ax.bar_label(bars, labels=[f'{r:.1f}x' for r in rel], fontsize=10, padding=3)
    ax.set_xlabel('picture size in pixels along one side', fontsize=10)
    ax.set_ylabel(f'attention work, as a multiple of the {sides[0]}-pixel case', fontsize=10)
    ax.set_ylim(0, max(rel) * 1.18)
    ax.set_title('Attention compares every pair, so the cost grows faster still',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'resolution-and-tokens.svg')


def two_ways_to_get_an_action() -> None:
    """The two action outputs, drawn with the weights each one needs."""
    token_head = WIDTH * VOCAB
    noise_in = ACTION_TOKENS
    sizes = [WIDTH + noise_in + 1, HEAD_WIDTH, HEAD_WIDTH, ACTION_TOKENS]
    cont_head = sum(sizes[i] * sizes[i + 1] + sizes[i + 1] for i in range(len(sizes) - 1))
    print(f'[two-ways] token head: {WIDTH} x {VOCAB:,} = {token_head:,} weights, '
          f'{ACTION_TOKENS} tokens decoded one after another')
    print(f'[two-ways] continuous head: {HEAD_LAYERS} layers of width {HEAD_WIDTH} = '
          f'{cont_head:,} weights, one chunk of {ACTION_TOKENS} numbers per flow step')
    print(f'[two-ways] the token head is {token_head / cont_head:.0f} times as many weights')

    fig, ax = plt.subplots(figsize=(11.4, 6.2), facecolor='white')
    _blank(ax, (0, 1), (0.02, 1))
    ax.text(0.5, 0.965, 'Two ways to turn the last token into a chunk of actions',
            ha='center', va='center', fontsize=12.5, weight='bold', color=INK)
    _box(ax, 0.36, 0.785, 0.28, 0.125,
         f'the model\'s last token\n{WIDTH} numbers', fc='#eaf3fb', ec=LINK, fs=10)
    _arrow(ax, 0.44, 0.780, 0.24, 0.690, colour=MUTED)
    _arrow(ax, 0.56, 0.780, 0.76, 0.690, colour=MUTED)

    _box(ax, 0.045, 0.165, 0.39, 0.515,
         'Way one: discrete action tokens\n\n'
         f'one output layer of {WIDTH} x {VOCAB:,}\n= {token_head:,} weights,\n'
         'the same layer the model uses for words\n\n'
         f'{ACTION_TOKENS} action tokens come out one\nafter another, each chosen from 256 bins\n\n'
         f'{ACTION_TOKENS} passes through the whole model',
         fc='#fdeeee', ec=GRIP, fs=9.2)
    _box(ax, 0.565, 0.165, 0.39, 0.515,
         'Way two: a small continuous head\n\n'
         f'{HEAD_LAYERS} layers of width {HEAD_WIDTH}\n= {cont_head:,} weights\n\n'
         f'in: {WIDTH} numbers from the model,\n{ACTION_TOKENS} noise numbers, 1 time number\n'
         f'out: all {ACTION_TOKENS} action numbers at once\n\n'
         'a handful of passes through the small head only',
         fc='#eaf7ee', ec=SLIDE, fs=9.2)
    ax.text(0.5, 0.085, f'The big output layer holds {token_head / cont_head:.0f} times as many '
            'weights as the small head, but the small head has to be trained to generate, '
            'which is what the next section is about.',
            ha='center', va='center', fontsize=9.6, color=INK)
    _save(fig, VLA_DOC, 'two-ways-to-get-an-action.svg')


# ==========================================================================
# PART D -- page 3, section 3: actions written as discrete tokens
# ==========================================================================

BINS: int = 256
BIN_LIST: list[int] = [32, 64, 128, 256, 512, 1024]
LONG_CHUNK: int = 50


def binning_one_dimension() -> None:
    """What binning does to one joint's commanded movement."""
    d = 0
    raw = EP.a_train.reshape(-1, ACTION_DIM)[:, d]
    lo, hi = EP.lo[d], EP.hi[d]
    width = (hi - lo) / BINS
    outside = float(np.mean((raw < lo) | (raw > hi)))
    print(f'[binning] joint 1: 1st percentile {lo:+.4f} rad, 99th percentile {hi:+.4f} rad, '
          f'range {hi - lo:.4f} rad = {np.degrees(hi - lo):.2f} deg')
    print(f'[binning] with {BINS} bins one bin is {width:.6f} rad = {np.degrees(width):.4f} deg '
          f'= {width * LEVER_M * 1000:.3f} mm at a {LEVER_M:.2f} m lever')
    print(f'[binning] {outside * 100:.1f}% of this joint\'s numbers fall outside the range '
          'and are pushed back to the end bins')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.hist(np.degrees(raw), bins=120, color=LINK_PALE, edgecolor=LINK, linewidth=0.5)
    ax.axvline(np.degrees(lo), color=GRIP, lw=1.8)
    ax.axvline(np.degrees(hi), color=GRIP, lw=1.8)
    ax.set_xlabel('commanded movement of joint 1 in one step (degrees)', fontsize=10)
    ax.set_ylabel('number of steps in the training episodes', fontsize=10)
    ax.set_title(f'The 1st and 99th percentile cut at {np.degrees(lo):+.2f} and '
                 f'{np.degrees(hi):+.2f} degrees', fontsize=11, weight='bold')
    ax.text(0.015, 0.97, f'{outside * 100:.1f}% of the\nnumbers fall\noutside and are\n'
            'pushed back\nto the ends', transform=ax.transAxes, fontsize=8.4,
            va='top', ha='left', color=GRIP)

    ax = axes[1]
    _plain(ax)
    centre = 0.0
    half = 6 * width
    sel = raw[(raw > centre - half) & (raw < centre + half)]
    ax.hist(np.degrees(sel), bins=60, color='#f2f2f2', edgecolor=GRID, linewidth=0.5)
    edges = lo + np.arange(BINS + 1) * width
    near = edges[(edges > centre - half) & (edges < centre + half)]
    for e in near:
        ax.axvline(np.degrees(e), color=TEAL, lw=0.9)
    ax.set_xlabel('commanded movement of joint 1 (degrees), a close-up on 12 bins',
                  fontsize=10)
    ax.set_ylabel('number of steps', fontsize=10)
    ax.set_title(f'One of {BINS} bins is {np.degrees(width):.4f} degrees wide',
                 fontsize=11, weight='bold')
    fig.suptitle('Every action number is replaced by the middle of the bin it lands in',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, VLA_DOC, 'binning-one-dimension.svg')


def _error_split(n_bins: int) -> tuple[float, float, float]:
    """Rounding RMS, rounding worst case and total RMS, all in degrees, for n_bins bins."""
    raw = EP.flat_test[:, :N_JOINTS]
    z = EP.normalise(EP.flat_test)
    back = EP.denormalise(bin_uniform(z, n_bins))[:, :N_JOINTS]
    err = back - raw
    inside = (raw >= EP.lo[:N_JOINTS]) & (raw <= EP.hi[:N_JOINTS])
    rnd = err[inside]
    return (float(np.degrees(np.sqrt(np.mean(rnd ** 2)))),
            float(np.degrees(np.abs(rnd).max())),
            float(np.degrees(np.sqrt(np.mean(err ** 2)))))


def quantisation_error_vs_bins() -> None:
    """The measured error of writing an action as a whole number of bins."""
    rows = [(b, *_error_split(b)) for b in BIN_LIST]
    for b, r, m, t in rows:
        print(f'[quant] {b:5d} bins: rounding RMS {r:.4f} deg ({r / 180 * np.pi * LEVER_M * 1000:.3f} mm), '
              f'worst rounding {m:.4f} deg, total RMS including clipping {t:.4f} deg')
    rnd = [r[1] for r in rows]
    tot = [r[3] for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(BIN_LIST, rnd, marker='o', color=SLIDE, lw=2,
            label='rounding only, for numbers inside the range')
    ax.plot(BIN_LIST, tot, marker='s', color=GRIP, lw=2,
            label='everything, including the numbers pushed back')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(BIN_LIST)
    ax.set_xticklabels([str(b) for b in BIN_LIST])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('number of bins each action number is written in', fontsize=10)
    ax.set_ylabel('error of one joint in one step (degrees)', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='lower left')
    ax.set_title('Rounding keeps getting smaller; the total stops',
                 fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    mm = [np.radians(r) * LEVER_M * 1000 for r in rnd]
    bars = ax.bar([str(b) for b in BIN_LIST], mm, color=TEAL, width=0.6)
    ax.bar_label(bars, labels=[f'{v:.3f}' for v in mm], fontsize=9, padding=3)
    ax.set_xlabel('number of bins', fontsize=10)
    ax.set_ylabel(f'rounding error at the fingertip (mm, {LEVER_M:.2f} m lever)', fontsize=10)
    ax.set_ylim(0, max(mm) * 1.2)
    ax.set_title(f'At {BINS} bins the rounding is {mm[BIN_LIST.index(BINS)]:.3f} mm, '
                 'far below what an arm can repeat', fontsize=10.5, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'quantisation-error-vs-bins.svg')


def percentile_range_matters() -> None:
    """The range the bins cover costs more than the number of bins, and deltas add up."""
    flat_tr = EP.a_train.reshape(-1, ACTION_DIM)
    ranges = [
        ('1st and 99th\npercentile',
         np.percentile(flat_tr, 1.0, axis=0), np.percentile(flat_tr, 99.0, axis=0), GRIP),
        ('0.1st and 99.9th\npercentile',
         np.percentile(flat_tr, 0.1, axis=0), np.percentile(flat_tr, 99.9, axis=0), WRIST),
        ('smallest and largest\nseen in training',
         flat_tr.min(axis=0), flat_tr.max(axis=0), JOINT),
        ('a third wider than\nanything seen',
         flat_tr.min(axis=0) * 1.3, flat_tr.max(axis=0) * 1.3, SLIDE),
    ]
    totals, drifts, clipped = [], [], []
    for name, lo, hi, _c in ranges:
        span = hi - lo
        frac = float(np.mean((EP.a_test[:, :, :N_JOINTS] < lo[:N_JOINTS])
                             | (EP.a_test[:, :, :N_JOINTS] > hi[:N_JOINTS])))
        ze = np.clip(2.0 * (EP.a_test - lo) / span - 1.0, -1.0, 1.0)
        be = ((bin_uniform(ze.reshape(-1, ACTION_DIM), BINS) + 1.0) / 2.0 * span
              + lo).reshape(EP.a_test.shape)[:, :, :N_JOINTS]
        diff = be - EP.a_test[:, :, :N_JOINTS]
        t = float(np.degrees(np.sqrt(np.mean(diff ** 2))))
        d10 = float(np.sqrt(np.mean(np.cumsum(diff, axis=1)[:, CHUNK - 1, :] ** 2)))
        d_all = float(np.sqrt(np.mean(np.cumsum(diff, axis=1)[:, -1, :] ** 2)))
        totals.append(t)
        clipped.append(frac * 100)
        drifts.append((d10 * LEVER_M * 1000, d_all * LEVER_M * 1000))
        print(f'[range] {name.replace(chr(10), " ")}: {frac * 100:.2f}% of numbers pushed back, '
              f'step error {t:.4f} deg, fingertip out by {d10 * LEVER_M * 1000:.2f} mm after '
              f'{CHUNK} steps and {d_all * LEVER_M * 1000:.2f} mm after {EP.horizon} steps')

    labels = [r[0] for r in ranges]
    colours = [r[3] for r in ranges]
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(labels, totals, color=colours, width=0.6)
    ax.bar_label(bars, labels=[f'{t:.3f} deg\n({c:.2f}% cut)' for t, c in zip(totals, clipped)],
                 fontsize=9, padding=3)
    ax.tick_params(axis='x', labelsize=8.8)
    ax.set_ylabel('error of one joint in one step (degrees)', fontsize=10)
    ax.set_ylim(0, max(totals) * 1.32)
    ax.set_title(f'All four use {BINS} bins. What changes is the range\nthe bins cover',
                 fontsize=10.8, weight='bold')

    ax = axes[1]
    _plain(ax)
    x = np.arange(len(ranges))
    b1 = ax.bar(x - 0.19, [d[0] for d in drifts], width=0.36, color=TEAL,
                label=f'after one chunk of {CHUNK} steps')
    b2 = ax.bar(x + 0.19, [d[1] for d in drifts], width=0.36, color=PURPLE,
                label=f'after a whole episode of {EP.horizon} steps')
    ax.bar_label(b1, fmt='%.1f', fontsize=8.5, padding=2)
    ax.bar_label(b2, fmt='%.1f', fontsize=8.5, padding=2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.8)
    ax.set_ylabel('how far the fingertip has drifted (mm)', fontsize=10)
    ax.set_ylim(0, max(d[1] for d in drifts) * 1.3)
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax.set_title('The movements are deltas, so the error adds up\nover the steps of a chunk',
                 fontsize=10.8, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'percentile-range-matters.svg')


def tokens_per_chunk() -> None:
    """How many tokens a chunk costs, and how a frequency transform cuts the count."""
    long_chunks = EP.a_test[:, :LONG_CHUNK, :N_JOINTS]
    n = LONG_CHUNK
    dmat = dct_matrix(n)
    coeffs = np.einsum('kt,etj->ekj', dmat, long_chunks)
    keeps = [2, 4, 6, 8, 12, 16, 25]
    errs = []
    for k in keeps:
        cut = np.zeros_like(coeffs)
        cut[:, :k, :] = coeffs[:, :k, :]
        back = np.einsum('kt,ekj->etj', dmat, cut)
        e = float(np.degrees(np.sqrt(np.mean((back - long_chunks) ** 2))))
        errs.append(e)
        print(f'[dct] keeping {k:2d} of {n} frequencies: {k * N_JOINTS:3d} tokens a chunk, '
              f'error {e:.4f} deg a joint a step')
    plain_tokens = LONG_CHUNK * N_JOINTS
    print(f'[dct] writing the {N_JOINTS} joint rows of the long chunk straight out costs '
          f'{plain_tokens} tokens')
    best = keeps[int(np.argmin([abs(e - 0.05) for e in errs]))]
    print(f'[dct] {best * N_JOINTS} tokens already gets the error near '
          f'{errs[keeps.index(best)]:.3f} deg')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    labels = [f'chunk of {CHUNK} steps\nwritten straight out',
              f'chunk of {LONG_CHUNK} steps\nwritten straight out',
              f'chunk of {LONG_CHUNK} steps\nkeeping {best} frequencies']
    vals = [CHUNK * N_JOINTS, plain_tokens, best * N_JOINTS]
    bars = ax.bar(labels, vals, color=[LINK, GRIP, SLIDE], width=0.55)
    ax.bar_label(bars, fmt='%d tokens', fontsize=10, padding=3)
    ax.set_ylabel('action tokens the model must produce one by one', fontsize=10)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title(f'Tokens for the {N_JOINTS} joint rows: every one is\na separate pass through the model',
                 fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    ax.plot([k * N_JOINTS for k in keeps], errs, marker='o', color=TEAL, lw=2)
    ax.axhline(0.0, color=GRID, lw=1)
    ax.set_xlabel(f'tokens used for a {LONG_CHUNK}-step chunk of {N_JOINTS} joints', fontsize=10)
    ax.set_ylabel('error of the rebuilt chunk (degrees a joint a step)', fontsize=10)
    ax.set_yscale('log')
    ax.set_title('A smooth movement needs few frequencies to describe it',
                 fontsize=11, weight='bold')
    for k, dx, dy in ((4, 14, 16), (16, -8, 20)):
        e = errs[keeps.index(k)]
        ax.annotate(f'{k * N_JOINTS} tokens, {e:.3f} deg', (k * N_JOINTS, e),
                    textcoords='offset points', xytext=(dx, dy), fontsize=9, color=INK,
                    arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.9))
    ax.set_ylim(min(errs) * 0.45, max(errs) * 3.0)
    fig.tight_layout()
    _save(fig, VLA_DOC, 'tokens-per-chunk.svg')


# ==========================================================================
# PART E -- page 3, section 4: a small continuous action head, trained here
# ==========================================================================

class MLP:
    """A plain network of fully connected layers with a ReLU rule, trained by Adam."""

    def __init__(self, sizes: list[int], seed: int) -> None:
        rng = np.random.default_rng(seed)
        self.w = [rng.normal(0.0, np.sqrt(2.0 / sizes[i]), (sizes[i], sizes[i + 1]))
                  for i in range(len(sizes) - 1)]
        self.b = [np.zeros(sizes[i + 1]) for i in range(len(sizes) - 1)]
        self.mw = [np.zeros_like(w) for w in self.w]
        self.vw = [np.zeros_like(w) for w in self.w]
        self.mb = [np.zeros_like(b) for b in self.b]
        self.vb = [np.zeros_like(b) for b in self.b]
        self.t = 0

    def forward(self, x: Arr) -> tuple[Arr, list[Arr]]:
        acts = [x]
        h = x
        for i, (w, b) in enumerate(zip(self.w, self.b)):
            h = h @ w + b
            if i < len(self.w) - 1:
                h = np.maximum(h, 0.0)
            acts.append(h)
        return h, acts

    def step(self, x: Arr, target: Arr, lr: float, mask: Arr | None = None) -> float:
        out, acts = self.forward(x)
        n = x.shape[0]
        diff = out - target
        if mask is not None:
            diff = diff * mask
        g = 2.0 * diff / n
        loss = float(np.mean(diff ** 2))
        gw: list[Arr] = [np.zeros(0)] * len(self.w)
        gb: list[Arr] = [np.zeros(0)] * len(self.b)
        for i in range(len(self.w) - 1, -1, -1):
            gw[i] = acts[i].T @ g
            gb[i] = g.sum(axis=0)
            if i > 0:
                g = (g @ self.w[i].T) * (acts[i] > 0)
        self.t += 1
        b1, b2, eps = 0.9, 0.999, 1e-8
        for i in range(len(self.w)):
            self.mw[i] = b1 * self.mw[i] + (1 - b1) * gw[i]
            self.vw[i] = b2 * self.vw[i] + (1 - b2) * gw[i] ** 2
            self.mb[i] = b1 * self.mb[i] + (1 - b1) * gb[i]
            self.vb[i] = b2 * self.vb[i] + (1 - b2) * gb[i] ** 2
            mw = self.mw[i] / (1 - b1 ** self.t)
            vw = self.vw[i] / (1 - b2 ** self.t)
            mb = self.mb[i] / (1 - b1 ** self.t)
            vb = self.vb[i] / (1 - b2 ** self.t)
            self.w[i] -= lr * mw / (np.sqrt(vw) + eps)
            self.b[i] -= lr * mb / (np.sqrt(vb) + eps)
        return loss

    def predict(self, x: Arr) -> Arr:
        return self.forward(x)[0]


class FlowHead:
    """A flow-matching action head: it learns to walk from noise to a chunk of actions.

    What it is told about the situation, standing in for the pictures and the
    instruction a real model would have, is the ten actions just before the chunk.
    """

    def __init__(self) -> None:
        a = EP.a_train
        n_ep, horizon, _ = a.shape
        starts = np.arange(CHUNK, horizon - CHUNK, 4)
        ctx = np.stack([a[:, s - CHUNK:s, :].reshape(n_ep, -1) for s in starts], axis=1)
        tgt = np.stack([a[:, s:s + CHUNK, :] for s in starts], axis=1)
        self.ctx = ctx.reshape(-1, CHUNK * ACTION_DIM)
        self.tgt = tgt.reshape(-1, CHUNK * ACTION_DIM)
        self.scale = self.tgt.std(axis=0) + 1e-9
        self.mean = self.tgt.mean(axis=0)
        self.x1 = (self.tgt - self.mean) / self.scale
        self.cs = (self.ctx - self.ctx.mean(axis=0)) / (self.ctx.std(axis=0) + 1e-9)
        self.net = MLP([CHUNK * ACTION_DIM + 1 + CHUNK * ACTION_DIM, 160, 160,
                        CHUNK * ACTION_DIM], seed=5)
        self.losses: list[float] = []

    def train(self, steps: int = 4000, batch: int = 128, lr: float = 3e-3) -> None:
        rng = np.random.default_rng(7)
        n = self.x1.shape[0]
        for i in range(steps):
            idx = rng.integers(0, n, batch)
            x1 = self.x1[idx]
            c = self.cs[idx]
            x0 = rng.normal(0.0, 1.0, x1.shape)
            t = rng.uniform(0.0, 1.0, (batch, 1))
            xt = (1.0 - t) * x0 + t * x1
            inp = np.concatenate([xt, t, c], axis=1)
            self.losses.append(self.net.step(inp, x1 - x0, lr))
        print(f'[flow] trained the head for {steps} steps; the loss fell from '
              f'{np.mean(self.losses[:50]):.4f} to {np.mean(self.losses[-50:]):.4f}')

    def sample(self, c: Arr, x0: Arr, n_steps: int) -> Arr:
        """Walk from the noise x0 to an action chunk in n_steps equal steps."""
        x = x0.copy()
        dt = 1.0 / n_steps
        for k in range(n_steps):
            t = np.full((x.shape[0], 1), k * dt)
            v = self.net.predict(np.concatenate([x, t, c], axis=1))
            x = x + dt * v
        return x

    def path(self, c: Arr, x0: Arr, n_steps: int) -> Arr:
        x = x0.copy()
        out = [x.copy()]
        dt = 1.0 / n_steps
        for k in range(n_steps):
            t = np.full((x.shape[0], 1), k * dt)
            x = x + dt * self.net.predict(np.concatenate([x, t, c], axis=1))
            out.append(x.copy())
        return np.stack(out)

    def to_actions(self, x: Arr) -> Arr:
        return (x * self.scale + self.mean).reshape(-1, CHUNK, ACTION_DIM)


FLOW: FlowHead | None = None
STEP_LIST: list[int] = [1, 2, 4, 8, 16, 32]


def _flow() -> FlowHead:
    global FLOW
    if FLOW is None:
        FLOW = FlowHead()
        FLOW.train()
    return FLOW


def flow_head_path() -> None:
    """The walk from noise to a chunk, drawn for a coarse and a fine number of steps."""
    f = _flow()
    rng = np.random.default_rng(21)
    c = f.cs[500:501]
    x0 = rng.normal(0.0, 1.0, (1, CHUNK * ACTION_DIM))
    shown = [1, 2, 4, 32]
    paths = {k: f.path(c, x0, k) for k in shown}
    d = 0                      # joint 1 at the first step of the chunk
    ends = {k: float(np.degrees(paths[k][-1, 0, d] * f.scale[d] + f.mean[d])) for k in shown}
    for k in shown:
        print(f'[flow-path] with {k:2d} steps joint 1 lands on {ends[k]:+.3f} deg, '
              f'{abs(ends[k] - ends[32]):.3f} deg from where 32 steps land it')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for k, colour, style in zip(shown, [GRIP, WRIST, TEAL, SLIDE], ['-', '-', '-', '-']):
        v = np.degrees(paths[k][:, 0, d] * f.scale[d] + f.mean[d])
        ax.plot(np.linspace(0, 1, k + 1), v, color=colour, lw=1.9, ls=style,
                marker='o', ms=4.5, label=f'{k} step' + ('' if k == 1 else 's'))
    ax.set_xlabel('how far along the walk, from pure noise (0) to an action (1)', fontsize=10)
    ax.set_ylabel('the value of joint 1 at the first step\nof the chunk (degrees)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('One noise sample, walked in different step counts',
                 fontsize=10.8, weight='bold')

    ax = axes[1]
    _plain(ax)
    many = rng.normal(0.0, 1.0, (24, CHUNK * ACTION_DIM))
    cc = np.repeat(c, 24, axis=0)
    paths = f.path(cc, many, 32)
    vals = np.degrees(paths[:, :, d] * f.scale[d] + f.mean[d])
    for i in range(24):
        ax.plot(np.linspace(0, 1, 33), vals[:, i], color=LINK, lw=1.0, alpha=0.6)
    ax.set_xlabel('how far along the walk', fontsize=10)
    ax.set_ylabel('the value of joint 1 (degrees)', fontsize=10)
    ax.set_title('24 noise samples, one instruction and picture',
                 fontsize=10.8, weight='bold')
    fig.suptitle('A flow head turns noise into a chunk by following a learned direction',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, VLA_DOC, 'flow-head-path.svg')


def flow_steps_vs_error() -> None:
    """How wrong a few big steps are, measured against a very fine walk."""
    f = _flow()
    rng = np.random.default_rng(31)
    n = 250
    idx = rng.integers(0, f.cs.shape[0], n)
    c = f.cs[idx]
    x0 = rng.normal(0.0, 1.0, (n, CHUNK * ACTION_DIM))
    ref = f.to_actions(f.sample(c, x0, 128))
    errs = []
    for k in STEP_LIST:
        got = f.to_actions(f.sample(c, x0, k))
        e = float(np.degrees(np.sqrt(np.mean((got[:, :, :N_JOINTS]
                                              - ref[:, :, :N_JOINTS]) ** 2))))
        errs.append(e)
        print(f'[flow-steps] {k:3d} steps: {e:.4f} deg a joint a step away from the '
              f'128-step answer ({np.radians(e) * LEVER_M * 1000:.3f} mm at the fingertip)')
    fig, ax = plt.subplots(figsize=(7.6, 4.5), facecolor='white')
    _plain(ax)
    ax.plot(STEP_LIST, errs, marker='o', color=SLIDE, lw=2)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(STEP_LIST)
    ax.set_xticklabels([str(k) for k in STEP_LIST])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('number of steps the head takes to produce one chunk', fontsize=10)
    ax.set_ylabel('distance from the 128-step answer\n(degrees a joint a step)', fontsize=10)
    ax.set_title('Fewer steps is faster and less exact, and the fall is steep at first',
                 fontsize=11.5, weight='bold')
    for k, e in zip(STEP_LIST, errs):
        ax.annotate(f'{e:.3f}', (k, e), textcoords='offset points', xytext=(6, 7),
                    fontsize=8.8, color=INK)
    fig.tight_layout()
    _save(fig, VLA_DOC, 'flow-steps-vs-error.svg')


def head_vs_tokens_latency() -> None:
    """How often each way of getting a chunk lets the model look at a fresh picture."""
    prefill_ms = 30.0        # reading the 525 tokens of pictures, words and joint state
    per_token_ms = 4.0       # one more action token, with the earlier work kept in a cache
    head_ms = 0.4            # one pass through the small head
    tok_time = prefill_ms + ACTION_TOKENS * per_token_ms
    head_times = [prefill_ms + k * head_ms for k in STEP_LIST]
    chunk_ms = CHUNK / CONTROL_HZ * 1000.0
    print(f'[latency] reading the {PREFIX_TOKENS} tokens in costs {prefill_ms:.0f} ms, and one '
          f'more action token costs {per_token_ms:.0f} ms')
    print(f'[latency] {ACTION_TOKENS} action tokens: {tok_time:.0f} ms a chunk, so the model '
          f'sees a fresh picture {1000.0 / tok_time:.1f} times a second')
    for k, t in zip(STEP_LIST, head_times):
        print(f'[latency] head at {k:2d} steps: {t:.1f} ms a chunk, so a fresh picture '
              f'{1000.0 / t:.1f} times a second')
    print(f'[latency] one chunk lasts {chunk_ms:.0f} ms on the arm at {CONTROL_HZ:.0f} Hz')
    open_tok = tok_time / 1000.0 * CONTROL_HZ
    open_head = head_times[STEP_LIST.index(8)] / 1000.0 * CONTROL_HZ
    print(f'[latency] the arm runs {open_tok:.1f} commands blind with tokens, and '
          f'{open_head:.1f} with the head at 8 steps')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = [f'{ACTION_TOKENS} action tokens'] + [f'head, {k} steps' for k in STEP_LIST]
    vals = [tok_time] + head_times
    cols = [GRIP] + [SLIDE] * len(head_times)
    bars = ax.barh(names[::-1], vals[::-1], color=cols[::-1])
    ax.bar_label(bars, labels=[f'{v:.0f} ms' for v in vals[::-1]], fontsize=9, padding=3)
    ax.axvline(prefill_ms, color=LINK, lw=1.6, ls='--')
    ax.annotate(f'{prefill_ms:.0f} ms of every bar is\njust reading the pictures in',
                xy=(prefill_ms, len(vals) - 2.0), xytext=(prefill_ms * 2.6, len(vals) - 3.1),
                fontsize=8.8, color=LINK, va='center',
                arrowprops=dict(arrowstyle='->', color=LINK, lw=0.9))
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_ylim(-0.7, len(vals) - 0.3)
    ax.set_xlabel(f'time to produce one chunk, if reading the input costs {prefill_ms:.0f} ms,\n'
                  f'one action token costs {per_token_ms:.0f} ms and one head step costs '
                  f'{head_ms:.1f} ms', fontsize=9.6)
    ax.tick_params(axis='y', labelsize=9)
    ax.set_title('Action tokens are produced one at a time', fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    ax.plot(STEP_LIST, [1000.0 / t for t in head_times], marker='o', color=SLIDE, lw=2,
            label='small continuous head')
    ax.axhline(1000.0 / tok_time, color=GRIP, lw=2, label=f'{ACTION_TOKENS} action tokens')
    ax.axhline(CONTROL_HZ, color=PURPLE, lw=1.8, ls='--',
               label=f'the arm\'s {CONTROL_HZ:.0f} commands a second')
    ax.set_xscale('log', base=2)
    ax.set_xticks(STEP_LIST)
    ax.set_xticklabels([str(k) for k in STEP_LIST])
    ax.set_ylim(0, 38)
    ax.set_xlabel('steps the head takes', fontsize=10)
    ax.set_ylabel('times a second the model can look at a fresh picture', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='center left')
    ax.set_title(f'With tokens the arm runs {open_tok:.0f} commands between looks,\n'
                 f'with the head at 8 steps only {open_head:.1f}',
                 fontsize=10.5, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'head-vs-tokens-latency.svg')


def continuous_vs_binned() -> None:
    """One real chunk, written four ways."""
    f = _flow()
    rng = np.random.default_rng(41)
    look = f.tgt[:3000].reshape(-1, CHUNK, ACTION_DIM)[:, :, 1]
    i = int(np.argmax(look.max(axis=1) - look.min(axis=1)))
    c = f.cs[i:i + 1]
    true_chunk = f.tgt[i].reshape(CHUNK, ACTION_DIM)
    x0 = rng.normal(0.0, 1.0, (1, CHUNK * ACTION_DIM))
    got4 = f.to_actions(f.sample(c, x0, 4))[0]
    got16 = f.to_actions(f.sample(c, x0, 16))[0]
    binned = EP.denormalise(bin_uniform(EP.normalise(true_chunk), BINS))
    e_bin = float(np.degrees(_rmse(binned[:, :N_JOINTS], true_chunk[:, :N_JOINTS])))
    e_head = float(np.degrees(_rmse(got16[:, :N_JOINTS], true_chunk[:, :N_JOINTS])))
    idx = rng.integers(0, f.cs.shape[0], 200)
    many = f.to_actions(f.sample(f.cs[idx], rng.normal(0.0, 1.0, (200, CHUNK * ACTION_DIM)),
                                 16))[:, :, :N_JOINTS]
    real = f.tgt[idx].reshape(-1, CHUNK, ACTION_DIM)[:, :, :N_JOINTS]
    e_many = float(np.degrees(_rmse(many, real)))
    print(f'[compare] writing this chunk through {BINS} bins moves it by {e_bin:.4f} degrees; '
          f'the head\'s own chunk sits {e_head:.3f} degrees from the demonstrated one')
    print(f'[compare] over 200 situations the head lands {e_many:.3f} degrees a joint a step '
          'from the demonstrated continuation')

    d = 1
    steps = np.arange(CHUNK)
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(steps, np.degrees(true_chunk[:, d]), color=INK, lw=2.6, marker='o', ms=5,
            label='the demonstrated chunk')
    ax.plot(steps, np.degrees(binned[:, d]), color=GRIP, lw=1.6, ls='--', marker='s', ms=4,
            label=f'written through {BINS} bins')
    ax.plot(steps, np.degrees(got16[:, d]), color=SLIDE, lw=1.8, marker='^', ms=5,
            label='the head, 16 walking steps')
    ax.plot(steps, np.degrees(got4[:, d]), color=TEAL, lw=1.6, ls=':', marker='v', ms=5,
            label='the head, 4 walking steps')
    ax.set_xlabel('step inside the chunk', fontsize=10)
    ax.set_ylabel('movement of joint 2 (degrees)', fontsize=10)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('Binning reproduces the demonstration almost exactly;\n'
                 'the head draws its own version of the same movement',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'continuous-vs-binned.svg')


# ==========================================================================
# PART F -- page 3, section 5: co-training, and what forgetting looks like
# ==========================================================================

GEN_CLASSES: int = 4          # the four answers of the simulated general task
ROB_CLASSES: int = 3          # the three answers of the simulated robot task
IN_DIM: int = 12


def _two_task_data(seed: int) -> tuple[Arr, Arr, Arr, Arr, Arr, Arr, Arr, Arr]:
    """Two simulated jobs: a general one and a robot one, with different rules and inputs."""
    rng = np.random.default_rng(seed)
    a = rng.normal(0.0, 1.0, (GEN_CLASSES, IN_DIM))
    b = rng.normal(0.0, 1.0, (ROB_CLASSES, IN_DIM))
    shift = rng.normal(0.0, 1.2, IN_DIM)

    def gen(n: int) -> tuple[Arr, Arr]:
        x = rng.normal(0.0, 1.0, (n, IN_DIM))
        y = np.argmax(x @ a.T, axis=1)
        t = np.zeros((n, GEN_CLASSES + ROB_CLASSES))
        t[np.arange(n), y] = 1.0
        return x, t

    def rob(n: int) -> tuple[Arr, Arr]:
        x = rng.normal(0.0, 0.7, (n, IN_DIM)) + shift
        y = np.argmax(x @ b.T, axis=1)
        t = np.zeros((n, GEN_CLASSES + ROB_CLASSES))
        t[np.arange(n), GEN_CLASSES + y] = 1.0
        return x, t

    xg, tg = gen(6000)
    xgt, tgt = gen(2000)
    xr, tr = rob(3000)
    xrt, trt = rob(1000)
    return xg, tg, xgt, tgt, xr, tr, xrt, trt


def _acc(net: MLP, x: Arr, t: Arr, lo: int, hi: int) -> float:
    out = net.predict(x)[:, lo:hi]
    return float(np.mean(np.argmax(out, axis=1) == np.argmax(t[:, lo:hi], axis=1)))


class CoTrain:
    """Pretrain on the general job, then learn the robot job with a mixture of both."""

    def __init__(self) -> None:
        (self.xg, self.tg, self.xgt, self.tgt,
         self.xr, self.tr, self.xrt, self.trt) = _two_task_data(3)
        self.gen_mask = np.zeros(GEN_CLASSES + ROB_CLASSES)
        self.gen_mask[:GEN_CLASSES] = 1.0
        self.rob_mask = np.zeros(GEN_CLASSES + ROB_CLASSES)
        self.rob_mask[GEN_CLASSES:] = 1.0
        self.base = MLP([IN_DIM, 64, 64, GEN_CLASSES + ROB_CLASSES], seed=9)
        rng = np.random.default_rng(13)
        for _ in range(1200):
            idx = rng.integers(0, self.xg.shape[0], 128)
            self.base.step(self.xg[idx], self.tg[idx], 3e-3,
                           np.broadcast_to(self.gen_mask, (128, GEN_CLASSES + ROB_CLASSES)))
        self.start_gen = _acc(self.base, self.xgt, self.tgt, 0, GEN_CLASSES)
        print(f'[cotrain] after pretraining, the general job is right '
              f'{self.start_gen * 100:.1f}% of the time')

    def _copy(self) -> MLP:
        net = MLP([IN_DIM, 64, 64, GEN_CLASSES + ROB_CLASSES], seed=9)
        net.w = [w.copy() for w in self.base.w]
        net.b = [b.copy() for b in self.base.b]
        return net

    def run(self, p_general: float, steps: int = 1200, every: int = 40
            ) -> tuple[list[int], list[float], list[float]]:
        net = self._copy()
        rng = np.random.default_rng(23)
        xs, gs, rs = [0], [self.start_gen], [_acc(net, self.xrt, self.trt,
                                                  GEN_CLASSES, GEN_CLASSES + ROB_CLASSES)]
        batch = 128
        n_gen = int(round(batch * p_general))
        n_rob = batch - n_gen
        full = np.broadcast_to(self.gen_mask, (max(n_gen, 1), GEN_CLASSES + ROB_CLASSES))
        rmask = np.broadcast_to(self.rob_mask, (n_rob, GEN_CLASSES + ROB_CLASSES))
        for i in range(1, steps + 1):
            ri = rng.integers(0, self.xr.shape[0], n_rob)
            net.step(self.xr[ri], self.tr[ri], 1e-3, rmask)
            if n_gen > 0:
                gi = rng.integers(0, self.xg.shape[0], n_gen)
                net.step(self.xg[gi], self.tg[gi], 1e-3, full)
            if i % every == 0:
                xs.append(i)
                gs.append(_acc(net, self.xgt, self.tgt, 0, GEN_CLASSES))
                rs.append(_acc(net, self.xrt, self.trt, GEN_CLASSES,
                               GEN_CLASSES + ROB_CLASSES))
        return xs, gs, rs


CO: CoTrain | None = None


def _co() -> CoTrain:
    global CO
    if CO is None:
        CO = CoTrain()
    return CO


def forgetting_curve() -> None:
    """What happens to the general job while the model learns the robot job."""
    co = _co()
    xs0, g0, r0 = co.run(0.0)
    xs1, g1, r1 = co.run(0.25)
    print(f'[forget] robot data only: the general job falls from {g0[0] * 100:.1f}% to '
          f'{g0[-1] * 100:.1f}%, and the robot job reaches {r0[-1] * 100:.1f}%')
    print(f'[forget] one quarter general data: the general job stays at '
          f'{g1[-1] * 100:.1f}%, and the robot job reaches {r1[-1] * 100:.1f}%')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    for ax, (gs, rs, title) in zip(axes, [(g0, r0, 'trained on robot data only'),
                                          (g1, r1, 'one batch in four is general data')]):
        _plain(ax)
        ax.plot(xs0, [v * 100 for v in gs], color=PURPLE, lw=2, marker='o', ms=3,
                label='the general job it already knew')
        ax.plot(xs0, [v * 100 for v in rs], color=SLIDE, lw=2, marker='s', ms=3,
                label='the new robot job')
        ax.axhline(co.start_gen * 100, color=GRID, lw=1.2, ls='--')
        ax.set_ylim(0, 100)
        ax.set_xlabel('training steps on the robot job', fontsize=10)
        ax.set_ylabel('answers right, out of a hundred', fontsize=10)
        ax.legend(fontsize=9, frameon=False, loc='lower right')
        ax.set_title(title, fontsize=11, weight='bold')
    fig.suptitle('Learning the new job wipes out the old one, unless the old data keeps coming',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, VLA_DOC, 'forgetting-curve.svg')


MIX: list[float] = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75]


def mixture_sweep() -> None:
    """How much of the old data has to keep coming."""
    co = _co()
    gen_end, rob_end = [], []
    for p in MIX:
        _xs, g, r = co.run(p)
        gen_end.append(g[-1] * 100)
        rob_end.append(r[-1] * 100)
        print(f'[mixture] {p * 100:.0f}% general data in the mixture: general job '
              f'{g[-1] * 100:.1f}%, robot job {r[-1] * 100:.1f}%')
    fig, ax = plt.subplots(figsize=(8.0, 4.6), facecolor='white')
    _plain(ax)
    x = [p * 100 for p in MIX]
    ax.plot(x, gen_end, marker='o', color=PURPLE, lw=2, label='the general job')
    ax.plot(x, rob_end, marker='s', color=SLIDE, lw=2, label='the robot job')
    ax.set_xlabel('share of the training batches that are general data (per cent)', fontsize=10)
    ax.set_ylabel('answers right at the end, out of a hundred', fontsize=10)
    ax.set_ylim(0, 103)
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    ax.set_title('A small share of the old data keeps most of the old skill',
                 fontsize=11.5, weight='bold')
    for i, (xx, gg) in enumerate(zip(x, gen_end)):
        off = (10, -4) if i == 0 else (0, 9)
        ax.annotate(f'{gg:.0f}', (xx, gg), textcoords='offset points', xytext=off,
                    ha='center', fontsize=8.8, color=PURPLE)
    fig.tight_layout()
    _save(fig, VLA_DOC, 'mixture-sweep.svg')


WEB_PAIRS: int = 400_000_000


def data_sizes() -> None:
    """Why the mixture has to be chosen rather than left to the natural sizes."""
    robot_frames = N_TASKS * DEMOS_PER_TASK * EP.horizon
    ratio = WEB_PAIRS / robot_frames
    share_natural = robot_frames / (robot_frames + WEB_PAIRS) * 100
    p = 0.25
    repeats = (1 - p) / p * WEB_PAIRS / robot_frames
    print(f'[sizes] robot frames {robot_frames:,}; web picture-and-text pairs {WEB_PAIRS:,}; '
          f'the web set is {ratio:,.0f} times larger')
    print(f'[sizes] poured together, robot data would be {share_natural:.4f}% of the batches')
    print(f'[sizes] to make robot data {(1 - p) * 100:.0f}% of the batches, every robot frame '
          f'is seen about {repeats:,.0f} times for each pass through the web set')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['robot frames\nfrom demonstrations', 'picture-and-text pairs\nfrom the web'],
                  [robot_frames, WEB_PAIRS], color=[SLIDE, PURPLE], width=0.55)
    ax.bar_label(bars, labels=[f'{robot_frames:,}', f'{WEB_PAIRS:,}'], fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylabel('number of training examples', fontsize=10)
    ax.set_ylim(1e4, WEB_PAIRS * 12)
    ax.set_title(f'The web set is about {ratio:,.0f} times larger', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    shares = [share_natural, 25.0, 75.0]
    bars = ax.bar(['poured together\nas they are', 'one quarter\nrobot data',
                   'three quarters\nrobot data'], shares, color=[GRIP, WRIST, SLIDE], width=0.55)
    ax.bar_label(bars, labels=[f'{share_natural:.4f}%', '25%', '75%'], fontsize=10, padding=3)
    ax.set_ylabel('share of the batches that are robot frames (per cent)', fontsize=10)
    ax.set_ylim(0, 92)
    ax.set_title('So the share has to be chosen on purpose', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'data-sizes.svg')


# ==========================================================================
# PART G -- page 3, section 6: episodes from many different robots
# ==========================================================================

ARM_A: tuple[float, float] = (0.40, 0.30)      # link lengths of the first simulated arm, metres
ARM_B: tuple[float, float] = (0.25, 0.45)      # link lengths of the second
POSE_A: tuple[float, float] = (0.55, 0.95)     # joint angles the arms are holding, radians
POSE_B: tuple[float, float] = (0.75, 1.25)


def _tip(links: tuple[float, float], th: tuple[float, float]) -> Arr:
    l1, l2 = links
    t1, t2 = th
    return np.array([l1 * np.cos(t1) + l2 * np.cos(t1 + t2),
                     l1 * np.sin(t1) + l2 * np.sin(t1 + t2)])


def _jac(links: tuple[float, float], th: tuple[float, float]) -> Arr:
    l1, l2 = links
    t1, t2 = th
    return np.array([
        [-l1 * np.sin(t1) - l2 * np.sin(t1 + t2), -l2 * np.sin(t1 + t2)],
        [l1 * np.cos(t1) + l2 * np.cos(t1 + t2), l2 * np.cos(t1 + t2)],
    ])


def _joint_delta(links: tuple[float, float], th: tuple[float, float], move: Arr) -> Arr:
    return np.linalg.solve(_jac(links, th), move)


def action_spaces_do_not_match() -> None:
    """The same fingertip movement needs different joint movements on different arms."""
    move = np.array([0.02, 0.01])          # 20 mm across and 10 mm up
    da = _joint_delta(ARM_A, POSE_A, move)
    db = _joint_delta(ARM_B, POSE_B, move)
    print(f'[embodiment] to move the fingertip {move[0] * 1000:.0f} mm across and '
          f'{move[1] * 1000:.0f} mm up:')
    print(f'[embodiment] arm A (links {ARM_A[0]:.2f} m and {ARM_A[1]:.2f} m) needs '
          f'{np.degrees(da[0]):+.3f} and {np.degrees(da[1]):+.3f} degrees')
    print(f'[embodiment] arm B (links {ARM_B[0]:.2f} m and {ARM_B[1]:.2f} m) needs '
          f'{np.degrees(db[0]):+.3f} and {np.degrees(db[1]):+.3f} degrees')
    print(f'[embodiment] the two joint-one numbers differ by a factor of '
          f'{abs(db[0] / da[0]):.2f}, and joint two even changes sign' if da[1] * db[1] < 0 else
          f'[embodiment] the two joint-one numbers differ by a factor of {abs(db[0] / da[0]):.2f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), facecolor='white')
    for ax, links, pose, delta, name, colour in [
            (axes[0], ARM_A, POSE_A, da, 'arm A', LINK),
            (axes[1], ARM_B, POSE_B, db, 'arm B', SLIDE)]:
        _plain(ax)
        l1, l2 = links
        t1, t2 = pose
        elbow = np.array([l1 * np.cos(t1), l1 * np.sin(t1)])
        tip = _tip(links, pose)
        ax.plot([0, elbow[0], tip[0]], [0, elbow[1], tip[1]], color=colour, lw=5,
                solid_capstyle='round')
        ax.plot([0, elbow[0]], [0, elbow[1]], 'o', color=JOINT, ms=11)
        ax.plot(tip[0], tip[1], 'o', color=GRIP, ms=9)
        new_pose = (t1 + delta[0], t2 + delta[1])
        new_elbow = np.array([l1 * np.cos(new_pose[0]), l1 * np.sin(new_pose[0])])
        new_tip = _tip(links, new_pose)
        ax.plot([0, new_elbow[0], new_tip[0]], [0, new_elbow[1], new_tip[1]],
                color=colour, lw=2, ls='--', alpha=0.8)
        ax.annotate('', xy=(tip[0] + move[0] * 6, tip[1] + move[1] * 6), xytext=(tip[0], tip[1]),
                    arrowprops=dict(arrowstyle='->', color=GRIP, lw=2.2))
        ax.text(tip[0] + move[0] * 6.4, tip[1] + move[1] * 6.4,
                f'move {move[0] * 1000:.0f} mm across\nand {move[1] * 1000:.0f} mm up\n'
                '(arrow drawn 6 times longer)', fontsize=8.6, color=GRIP, va='center')
        ax.set_aspect('equal')
        ax.set_xlim(-0.12, 0.62)
        ax.set_ylim(-0.05, 0.72)
        ax.set_xlabel('metres across', fontsize=10)
        ax.set_ylabel('metres up', fontsize=10)
        ax.set_title(f'{name}: links {l1:.2f} m and {l2:.2f} m\n'
                     f'joint 1 turns {np.degrees(delta[0]):+.3f}, '
                     f'joint 2 turns {np.degrees(delta[1]):+.3f} degrees',
                     fontsize=10.5, weight='bold')
    fig.suptitle('The same job at the fingertip is a different pair of numbers on each arm',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, VLA_DOC, 'action-spaces-do-not-match.svg')


def normalising_per_robot() -> None:
    """Each robot's own range maps onto the same -1 to 1, which is what lets the data pool."""
    rng = np.random.default_rng(55)
    fast = EP.a_train[:, :, 0].reshape(-1)
    slow = fast[rng.permutation(fast.size)[:fast.size // 2]] * 0.35
    ranges = {}
    for name, data in (('arm A', fast), ('arm B', slow)):
        lo, hi = np.percentile(data, 1.0), np.percentile(data, 99.0)
        ranges[name] = (lo, hi)
        print(f'[normalise] {name}: joint 1 runs from {np.degrees(lo):+.2f} to '
              f'{np.degrees(hi):+.2f} degrees a step')
    print('[normalise] after each arm is scaled by its own range, both fill -1 to 1')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.hist(np.degrees(fast), bins=90, color=LINK_PALE, edgecolor=LINK, linewidth=0.5,
            alpha=0.85, label='arm A', density=True)
    ax.hist(np.degrees(slow), bins=90, color='#cfe9d6', edgecolor=SLIDE, linewidth=0.5,
            alpha=0.75, label='arm B', density=True)
    ax.set_xlabel('movement of joint 1 in one step (degrees)', fontsize=10)
    ax.set_ylabel('how often, as a share', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('Raw numbers: arm B moves in much smaller steps', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    for data, name, face, edge in ((fast, 'arm A', LINK_PALE, LINK),
                                   (slow, 'arm B', '#cfe9d6', SLIDE)):
        lo, hi = ranges[name]
        z = np.clip(2.0 * (data - lo) / (hi - lo) - 1.0, -1.0, 1.0)
        ax.hist(z, bins=90, color=face, edgecolor=edge, linewidth=0.5, alpha=0.8,
                label=name, density=True)
    ax.set_xlabel('the same movement after each arm is scaled by its own range', fontsize=10)
    ax.set_ylabel('how often, as a share', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('Scaled: the two arms now speak in the same numbers',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'normalising-per-robot.svg')


def _reach_data(arm: tuple[float, float], pose: tuple[float, float], n: int,
                tag: int, seed: int) -> tuple[Arr, Arr]:
    """Where the camera sees a thing, and the joint movement that arm needs to reach it.

    The camera map from picture position to table position is the same for both arms and
    is deliberately wiggly, so that it takes many examples to learn. Turning a table
    position into joint movement is different for each arm and is simple once the camera
    map is known.
    """
    rng = np.random.default_rng(seed)
    uv = rng.uniform(-1.0, 1.0, (n, 2))
    u, v = uv[:, 0], uv[:, 1]
    world = np.stack([0.30 + 0.16 * (u + 0.45 * np.sin(5.5 * u) + 0.35 * np.sin(4.0 * v)),
                      0.34 + 0.16 * (v + 0.45 * np.sin(5.5 * v) - 0.35 * np.sin(4.0 * u))],
                     axis=1)
    here = _tip(arm, pose)
    jinv = np.linalg.inv(_jac(arm, pose))
    dq = (world - here) @ jinv.T + rng.normal(0.0, np.radians(0.25), (n, 2))
    onehot = np.zeros((n, 2))
    onehot[:, tag] = 1.0
    return np.concatenate([uv, onehot], axis=1), dq


def _fit_reach(x: Arr, y: Arr, steps: int = 2500, seed: int = 4) -> MLP:
    net = MLP([4, 64, 64, 2], seed=seed)
    rng = np.random.default_rng(seed + 1)
    for _ in range(steps):
        idx = rng.integers(0, x.shape[0], 96)
        net.step(x[idx], y[idx], 3e-3)
    return net


def _reach_error(xb: Arr, yb: Arr, xa: Arr | None, ya: Arr | None,
                 xt: Arr, yt: Arr, tags: bool = True, seeds: int = 3) -> float:
    """Average error in degrees over a few training runs, each arm scaled by its own range."""
    sb = yb.std(axis=0)
    out = []
    for s in range(seeds):
        if xa is None or ya is None:
            x, y = xb, yb / sb
            xe = xt
        else:
            sa = ya.std(axis=0)
            x = np.vstack([xa, xb])
            y = np.vstack([ya / sa, yb / sb])
            xe = xt
            if not tags:
                x = x.copy()
                x[:, 2:] = 0.0
                xe = xt.copy()
                xe[:, 2:] = 0.0
        net = _fit_reach(x, y, seed=4 + 7 * s)
        out.append(float(np.degrees(_rmse(net.predict(xe) * sb, yt))))
    return float(np.mean(out))


def pooling_helps() -> None:
    """Pooling another arm's episodes helps a thin dataset, if the model is told which arm."""
    xa, ya = _reach_data(ARM_A, POSE_A, 2000, 0, 101)
    xb, yb = _reach_data(ARM_B, POSE_B, 50, 1, 202)
    xt, yt = _reach_data(ARM_B, POSE_B, 1000, 1, 303)
    scores = [
        ('arm B\'s 50 episodes\non their own', _reach_error(xb, yb, None, None, xt, yt), WRIST),
        ('plus arm A\'s 2,000,\nwith a tag saying which arm',
         _reach_error(xb, yb, xa, ya, xt, yt, tags=True), SLIDE),
        ('plus arm A\'s 2,000,\nwith no tag',
         _reach_error(xb, yb, xa, ya, xt, yt, tags=False), GRIP),
    ]
    for name, v, _c in scores:
        print(f'[pool] {name.replace(chr(10), " ")}: error {v:.3f} degrees a joint')
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor='white')
    _plain(ax)
    bars = ax.bar([s[0] for s in scores], [s[1] for s in scores],
                  color=[s[2] for s in scores], width=0.55)
    ax.bar_label(bars, labels=[f'{s[1]:.2f} deg' for s in scores], fontsize=10, padding=3)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_ylabel('error in the joint movement it asks for (degrees)', fontsize=10)
    ax.set_ylim(0, max(s[1] for s in scores) * 1.2)
    ax.set_title('Another arm\'s episodes help a thin dataset, but only when\n'
                 'the model knows which arm it is driving', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'pooling-helps.svg')


def pooling_vs_data() -> None:
    """Pooling helps where the new arm's own data is thinnest, and stops helping later."""
    xa, ya = _reach_data(ARM_A, POSE_A, 2000, 0, 101)
    xt, yt = _reach_data(ARM_B, POSE_B, 1000, 1, 303)
    sizes = [25, 50, 100, 200, 400, 800]
    alone, with_a = [], []
    for n in sizes:
        xb, yb = _reach_data(ARM_B, POSE_B, n, 1, 400 + n)
        e1 = _reach_error(xb, yb, None, None, xt, yt)
        e2 = _reach_error(xb, yb, xa, ya, xt, yt, tags=True)
        alone.append(e1)
        with_a.append(e2)
        print(f'[pool-size] arm B with {n:4d} examples: alone {e1:.3f} deg, '
              f'pooled with arm A {e2:.3f} deg')
    fig, ax = plt.subplots(figsize=(8.2, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(sizes, alone, marker='o', color=GRIP, lw=2, label='arm B\'s own episodes only')
    ax.plot(sizes, with_a, marker='s', color=SLIDE, lw=2, label='pooled with arm A\'s 2,000')
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(n) for n in sizes])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('training examples recorded on arm B', fontsize=10)
    ax.set_ylabel('error in the joint movement it asks for (degrees)', fontsize=10)
    ax.set_ylim(0, max(max(alone), max(with_a)) * 1.15)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('The pool is worth most when the new arm has least,\n'
                 'and stops paying once the new arm has its own few hundred',
                 fontsize=11.2, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'pooling-vs-data.svg')


# ==========================================================================
# PART H -- page 3, section 7: what generalisation looks like, and what it costs
# ==========================================================================

TRAIN_HALF: float = 0.6       # the objects in training sat in the middle of the camera view


COVERAGE: dict[str, float] = {}


def position_coverage() -> None:
    """The same task with the object moved: inside the seen area it works, outside it does not."""
    rng = np.random.default_rng(77)
    seen = rng.uniform(-TRAIN_HALF, TRAIN_HALF, (400, 2))
    covered = (2 * TRAIN_HALF) ** 2 / 4.0 * 100
    print(f'[coverage] training objects sat inside a square {2 * TRAIN_HALF:.1f} wide out of '
          f'2, which is {covered:.0f}% of the camera view')

    xa, ya = _reach_data(ARM_A, POSE_A, 2400, 0, 101)
    keep = np.all(np.abs(xa[:, :2]) <= TRAIN_HALF, axis=1)
    xtr, ytr = xa[keep], ya[keep]
    net = _fit_reach(xtr, ytr / ytr.std(axis=0), seed=4)
    xte, yte = _reach_data(ARM_A, POSE_A, 4000, 0, 909)
    pred = net.predict(xte) * ytr.std(axis=0)
    err = np.degrees(np.sqrt(np.mean((pred - yte) ** 2, axis=1)))
    dist = np.maximum(np.abs(xte[:, 0]), np.abs(xte[:, 1]))
    edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    mids, vals = [], []
    for i in range(len(edges) - 1):
        m = (dist >= edges[i]) & (dist < edges[i + 1])
        mids.append((edges[i] + edges[i + 1]) / 2)
        vals.append(float(np.mean(err[m])))
        print(f'[coverage] objects {edges[i]:.1f} to {edges[i + 1]:.1f} from the middle: '
              f'error {vals[-1]:.2f} degrees ({int(m.sum())} test objects)')
    COVERAGE['inside'] = float(np.mean(vals[:3]))
    COVERAGE['edge'] = float(vals[-1])
    print(f'[coverage] {len(xtr)} of 2400 training objects were kept; the average error '
          f'inside the seen area is {COVERAGE["inside"]:.2f} degrees and at the edge of the '
          f'view it is {COVERAGE["edge"]:.2f} degrees')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.7), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.scatter(seen[:, 0], seen[:, 1], s=9, color=LINK, alpha=0.55, label='seen in training')
    ax.add_patch(Rectangle((-TRAIN_HALF, -TRAIN_HALF), 2 * TRAIN_HALF, 2 * TRAIN_HALF,
                           facecolor='none', edgecolor=LINK, lw=2))
    ax.add_patch(Rectangle((-1, -1), 2, 2, facecolor='none', edgecolor=GRIP, lw=2, ls='--',
                           label='the whole camera view'))
    ax.set_xlim(-1.14, 1.14)
    ax.set_ylim(-1.14, 1.3)
    ax.set_aspect('equal')
    ax.set_xlabel('across the camera view', fontsize=10)
    ax.set_ylabel('up the camera view', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper center', ncol=2,
              bbox_to_anchor=(0.5, 1.02))
    ax.set_title(f'The objects in training covered {covered:.0f}% of the view',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    cols = [SLIDE if m < TRAIN_HALF else GRIP for m in mids]
    bars = ax.bar([f'{edges[i]:.1f}-{edges[i + 1]:.1f}' for i in range(len(edges) - 1)],
                  vals, color=cols, width=0.62)
    ax.bar_label(bars, labels=[f'{v:.2f}' for v in vals], fontsize=9, padding=3)
    ax.axvline(2.5, color=INK, lw=1.2, ls=':')
    ax.text(2.55, max(vals) * 0.9, 'edge of what\nwas seen', fontsize=9, color=INK)
    ax.set_xlabel('how far the object is from the middle of the view', fontsize=10)
    ax.set_ylabel('error in the movement asked for (degrees)', fontsize=10)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title('Moving the object inside the seen area is fine;\noutside it is not',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'position-coverage.svg')


def _grasp_height(w: Arr, h: Arr) -> Arr:
    """Where to close the fingers on an object, as a smooth rule of its width and height."""
    return 0.52 * h + 0.9 * np.sin(w / 3.4) + 0.012 * (w - 11.0) ** 2


def _poly2(w: Arr, h: Arr) -> Arr:
    return np.stack([np.ones_like(w), w, h, w ** 2, h ** 2, w * h], axis=1)


def new_object_kind() -> None:
    """A new object of a kind the model saw, against an object of a kind it never saw."""
    rng = np.random.default_rng(88)
    mw = rng.uniform(6.0, 9.0, 300)
    mh = rng.uniform(8.0, 11.0, 300)
    bw = rng.uniform(13.0, 18.0, 300)
    bh = rng.uniform(4.5, 7.0, 300)
    noise = 0.08
    y_m = _grasp_height(mw, mh) + rng.normal(0, noise, 300)
    y_b = _grasp_height(bw, bh) + rng.normal(0, noise, 300)
    coef, *_ = np.linalg.lstsq(_poly2(mw[:200], mh[:200]), y_m[:200], rcond=None)
    e_same = _rmse(_poly2(mw[200:], mh[200:]) @ coef, y_m[200:])
    e_new = _rmse(_poly2(bw, bh) @ coef, y_b)
    both = np.concatenate([np.arange(200), 300 + np.arange(150)])
    aw = np.concatenate([mw[:200], bw[:150]])
    ah = np.concatenate([mh[:200], bh[:150]])
    ay = np.concatenate([y_m[:200], y_b[:150]])
    coef2, *_ = np.linalg.lstsq(_poly2(aw, ah), ay, rcond=None)
    e_both = _rmse(_poly2(bw[150:], bh[150:]) @ coef2, y_b[150:])
    print(f'[kinds] trained on 200 tall narrow objects: error {e_same:.3f} cm on new tall '
          f'narrow ones, {e_new:.3f} cm on wide flat ones it never saw')
    print(f'[kinds] after 150 wide flat ones are added to training, the error on wide flat '
          f'ones falls to {e_both:.3f} cm')
    print(f'[kinds] the second number is {e_new / e_same:.0f} times the first, and '
          f'{len(both)} objects were used in the mixed fit')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.7), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.scatter(mw, mh, s=12, color=LINK, alpha=0.6, label='tall narrow objects (trained on)')
    ax.scatter(bw, bh, s=12, color=GRIP, alpha=0.6, label='wide flat objects (never seen)')
    ax.set_xlabel('width of the object (cm)', fontsize=10)
    ax.set_ylabel('height of the object (cm)', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax.set_title('The two kinds sit in different parts of the picture',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    bars = ax.bar(['a new object of\nthe kind it saw', 'an object of a\nkind it never saw',
                   'the new kind, after\n150 of them are added'],
                  [e_same, e_new, e_both], color=[SLIDE, GRIP, WRIST], width=0.55)
    ax.bar_label(bars, labels=[f'{v:.2f} cm' for v in [e_same, e_new, e_both]],
                 fontsize=10, padding=3)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_ylabel('error in where to close the fingers (cm)', fontsize=10)
    ax.set_ylim(0, e_new * 1.2)
    ax.set_title('The rule it learned does not reach the other kind',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'new-object-kind.svg')


TRAIN_INSTRUCTIONS: list[str] = [
    'pick up the red block and put it in the bowl',
    'put the red block in the bowl',
    'pick up the blue block and put it in the tray',
    'move the mug to the left of the plate',
    'place the cup on the saucer',
    'put the spoon in the mug',
    'pick up the yellow block',
    'push the plate towards the edge',
]
TEST_INSTRUCTIONS: list[tuple[str, str]] = [
    ('place the red block into the bowl', 'the same task, said differently'),
    ('put the red block inside the bowl please', 'the same task, said differently'),
    ('drop the red block in the bowl', 'the same task, said differently'),
    ('fold the cloth in half', 'a task it never learned'),
    ('unscrew the lid of the jar', 'a task it never learned'),
]


def instruction_overlap() -> None:
    """A crude check of how much of a new sentence the model has already met."""
    known: set[str] = set()
    for line in TRAIN_INSTRUCTIONS:
        known.update(line.split())
    shares, labels, kinds = [], [], []
    for line, kind in TEST_INSTRUCTIONS:
        words = line.split()
        share = sum(w in known for w in words) / len(words) * 100
        shares.append(share)
        labels.append(line)
        kinds.append(kind)
        print(f'[words] "{line}": {share:.0f}% of its words appear in the training '
              f'instructions ({kind})')
    print(f'[words] the training instructions use {len(known)} different words in all')
    fig, ax = plt.subplots(figsize=(9.4, 4.4), facecolor='white')
    _plain(ax)
    cols = [SLIDE if k.startswith('the same') else GRIP for k in kinds]
    bars = ax.barh(labels[::-1], shares[::-1], color=cols[::-1])
    ax.bar_label(bars, labels=[f'{v:.0f}%' for v in shares[::-1]], fontsize=9.5, padding=3)
    ax.set_xlim(0, 118)
    ax.set_xlabel('share of the sentence\'s words that appear in the training instructions',
                  fontsize=10)
    ax.tick_params(axis='y', labelsize=9)
    ax.set_title('Rewording a known task reuses the words; a new task brings new ones',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, VLA_DOC, 'instruction-overlap.svg')


def four_cases() -> None:
    """The four kinds of change, and what each one costs, using the numbers measured above."""
    rng = np.random.default_rng(88)
    mw, mh = rng.uniform(6, 9, 300), rng.uniform(8, 11, 300)
    bw, bh = rng.uniform(13, 18, 300), rng.uniform(4.5, 7, 300)
    y_m = _grasp_height(mw, mh) + rng.normal(0, 0.08, 300)
    y_b = _grasp_height(bw, bh) + rng.normal(0, 0.08, 300)
    coef, *_ = np.linalg.lstsq(_poly2(mw[:200], mh[:200]), y_m[:200], rcond=None)
    e_same = _rmse(_poly2(mw[200:], mh[200:]) @ coef, y_m[200:])
    e_new = _rmse(_poly2(bw, bh) @ coef, y_b)

    if not COVERAGE:
        position_coverage()
    known: set[str] = set()
    for line in TRAIN_INSTRUCTIONS:
        known.update(line.split())
    same = [sum(w in known for w in t.split()) / len(t.split()) * 100
            for t, k in TEST_INSTRUCTIONS if k.startswith('the same')]
    lo_w, hi_w = min(same), max(same)
    rows = [
        ('the same task, object moved\ninside the area seen before',
         'works', f'the error stays near {COVERAGE["inside"]:.1f} degrees everywhere\n'
         'inside the area the training objects covered', SLIDE),
        ('the same task, said in\ndifferent words',
         'usually works', f'{lo_w:.0f} to {hi_w:.0f} per cent of the words in the reworded '
         'sentences\nalready appear in the training instructions', SLIDE),
        ('the same task, object moved\noutside the area seen before',
         'does not work', f'the error grows to about {COVERAGE["edge"]:.0f} degrees at the '
         'edge of the camera view', GRIP),
        ('a new object of a kind\nthe model never saw',
         'does not work', f'the error on the unseen kind is {e_new / e_same:.0f} times\n'
         'the error on a new object of a seen kind', GRIP),
        ('a task the model was\nnever shown',
         'does not work', 'nothing in the training data says what the new words mean '
         'for the arm', GRIP),
    ]
    print(f'[cases] unseen-kind error {e_new:.3f} cm against seen-kind error {e_same:.3f} cm, '
          f'a factor of {e_new / e_same:.0f}')
    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax, (0, 1), (0, 1))
    ax.text(0.5, 0.965, 'What a vision-language-action model actually carries over, '
            'measured on this page',
            ha='center', va='center', fontsize=12.5, weight='bold', color=INK)
    top, h, gap = 0.875, 0.145, 0.022
    for i, (change, verdict, why, colour) in enumerate(rows):
        y = top - (i + 1) * (h + gap) + gap
        _box(ax, 0.015, y, 0.28, h, change, fc='white', ec=colour, fs=9.0)
        _box(ax, 0.305, y, 0.155, h, verdict, fc='white', ec=colour, fs=9.6,
             tc=colour, weight='bold')
        _box(ax, 0.47, y, 0.515, h, why, fc='#fafafa', ec=GRID, fs=8.8)
    _save(fig, VLA_DOC, 'four-cases.svg')


def cost_of_running() -> None:
    """How a slow model still drives a fast arm."""
    prefill_ms, per_token_ms, head_ms = 30.0, 4.0, 0.4
    tok_ms = prefill_ms + ACTION_TOKENS * per_token_ms
    head8_ms = prefill_ms + 8 * head_ms
    small_ms = head8_ms / 10.0
    rates = [20, 50, 100, 200, 500]
    need_tok = [r * tok_ms / 1000.0 for r in rates]
    need_head = [r * head8_ms / 1000.0 for r in rates]
    need_small = [r * small_ms / 1000.0 for r in rates]
    print(f'[cost] one chunk takes {tok_ms:.0f} ms with action tokens, {head8_ms:.1f} ms with '
          f'the head at 8 steps, and {small_ms:.1f} ms for a distilled model ten times smaller')
    for r, a, b, c in zip(rates, need_tok, need_head, need_small):
        print(f'[cost] at {r:3d} commands a second the chunk must cover at least '
              f'{a:.1f} steps (tokens), {b:.1f} (head) or {c:.1f} (distilled)')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(rates, need_tok, marker='o', color=GRIP, lw=2, label=f'{ACTION_TOKENS} action tokens')
    ax.plot(rates, need_head, marker='s', color=SLIDE, lw=2, label='continuous head, 8 steps')
    ax.plot(rates, need_small, marker='^', color=TEAL, lw=2, label='a distilled model, ten times faster')
    ax.axhline(CHUNK, color=PURPLE, lw=1.6, ls='--', label=f'the {CHUNK}-step chunk on this page')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(rates)
    ax.set_xticklabels([str(r) for r in rates])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('commands the arm wants each second', fontsize=10)
    ax.set_ylabel('shortest chunk that still covers\none call of the model (steps)', fontsize=10)
    ax.legend(fontsize=8.8, frameon=False, loc='upper left')
    ax.set_title('A faster arm needs a longer chunk, or a faster model',
                 fontsize=11, weight='bold')

    ax = axes[1]
    _blank(ax, (0, 1), (0, 1))
    ax.text(0.5, 0.95, 'The third way: two models, at two speeds',
            ha='center', va='center', fontsize=11.5, weight='bold', color=INK)
    span = tok_ms
    ax.text(0.02, 0.80, f'the big model, every {span:.0f} ms', fontsize=9.5, color=GRIP)
    for i in range(3):
        _box(ax, 0.03 + i * 0.32, 0.62, 0.30, 0.13, 'looks, then sets\nthe next goal',
             fc='#fdeeee', ec=GRIP, fs=8.6)
    ax.text(0.02, 0.45, f'a small fast policy, every {1000 / 100:.0f} ms', fontsize=9.5,
            color=SLIDE)
    n_fast = int(round(span / 10.0))
    for i in range(3 * 10):
        ax.add_patch(Rectangle((0.03 + i * 0.0315, 0.28), 0.026, 0.13,
                               facecolor='#eaf7ee', edgecolor=SLIDE, linewidth=0.9))
    print(f'[cost] the big model fires once for about every {n_fast} steps of the fast policy')
    ax.text(0.5, 0.13, f'the big model looks {1000 / span:.1f} times a second, while the small '
            'one\nkeeps the arm moving 100 times a second towards its goal',
            ha='center', va='center', fontsize=9.6, color=INK)
    fig.tight_layout()
    _save(fig, VLA_DOC, 'cost-of-running.svg')


# ==========================================================================
# PART I -- page 4: one simulated system, a learned model of it, and a planner
# ==========================================================================

G: float = 9.81
LINK_L: float = 1.0
MASS: float = 1.0
DAMP: float = 0.25
DT: float = 0.05
STOP: float = 0.45            # the hard stop the joint cannot turn past, in radians
TORQUE: float = 1.1           # the torque the recorded episodes used
TORQUE_PLAN: float = 1.6      # the torque the planner is allowed to ask for
GOAL: float = 0.70            # the angle the planner is told to reach, which is past the stop


def true_step(state: Arr, u: Arr) -> Arr:
    """One step of the real system: a one-joint arm with damping and a hard stop."""
    th, om = state[..., 0], state[..., 1]
    om_n = om + DT * (-(G / LINK_L) * np.sin(th) - DAMP * om + u / (MASS * LINK_L ** 2))
    th_n = th + DT * om_n
    hit = th_n > STOP
    th_n = np.where(hit, STOP, th_n)
    om_n = np.where(hit, 0.0, om_n)
    return np.stack([th_n, om_n], axis=-1)


def _smooth_torque(n: int, horizon: int, rng: np.random.Generator, hold: int = 5,
                   tmax: float = TORQUE) -> Arr:
    segs = int(np.ceil(horizon / hold))
    vals = rng.uniform(-tmax, tmax, (n, segs))
    return np.repeat(vals, hold, axis=1)[:, :horizon]


def make_transitions(n_ep: int, horizon: int, seed: int, noise: float = 0.002
                     ) -> tuple[Arr, Arr, Arr, NDArray[np.bool_]]:
    """Collect (state, torque, next state) from the real system, as a recording would."""
    rng = np.random.default_rng(seed)
    s = np.stack([rng.uniform(-1.0, -0.15, n_ep), rng.uniform(-0.8, 0.8, n_ep)], axis=1)
    us = _smooth_torque(n_ep, horizon, rng)
    states, acts, nexts, hits = [], [], [], []
    for k in range(horizon):
        u = us[:, k]
        s2 = true_step(s, u)
        hits.append((s2[:, 0] >= STOP - 1e-9) | (s[:, 0] >= STOP - 1e-9))
        states.append(s.copy())
        acts.append(u.copy())
        nexts.append(s2.copy())
        s = s2
    st = np.concatenate(states)
    ac = np.concatenate(acts)
    nx = np.concatenate(nexts)
    hit = np.concatenate(hits)
    st = st + rng.normal(0.0, noise, st.shape)
    nx = nx + rng.normal(0.0, noise, nx.shape)
    return st, ac, nx, hit


def poly_features(st: Arr, u: Arr) -> Arr:
    """Degree-two features of the angle, the speed and the torque."""
    th, om = st[..., 0], st[..., 1]
    one = np.ones_like(th)
    return np.stack([one, th, om, u, th ** 2, om ** 2, u ** 2,
                     th * om, th * u, om * u], axis=-1)


class LearnedModel:
    """A learned dynamics model: least squares from the features to the change in state."""

    def __init__(self, st: Arr, ac: Arr, nx: Arr, lam: float = 1e-6) -> None:
        phi = poly_features(st, ac)
        target = nx - st
        a = phi.T @ phi + lam * np.eye(phi.shape[1])
        self.w = np.linalg.solve(a, phi.T @ target)

    def step(self, state: Arr, u: Arr) -> Arr:
        return state + poly_features(state, u) @ self.w


class World:
    """Everything the world-model page measures, worked out once."""

    def __init__(self) -> None:
        self.st, self.ac, self.nx, self.hit = make_transitions(400, 30, seed=2)
        self.n = self.st.shape[0]
        self.clean = ~self.hit
        self.model = LearnedModel(self.st[self.clean], self.ac[self.clean], self.nx[self.clean])
        self.vst, self.vac, self.vnx, vhit = make_transitions(80, 30, seed=3, noise=0.0)
        keep = ~vhit
        self.vst, self.vac, self.vnx = self.vst[keep], self.vac[keep], self.vnx[keep]
        pred = self.model.step(self.vst, self.vac)
        self.one_step_angle = float(np.degrees(_rmse(pred[:, 0], self.vnx[:, 0])))
        self.one_step_speed = float(_rmse(pred[:, 1], self.vnx[:, 1]))
        print(f'[world] {self.n} recorded transitions, of which {int(self.hit.sum())} touched '
              f'the hard stop ({self.hit.mean() * 100:.2f}%) and were left out of the fit')
        print(f'[world] one-step error on fresh data: {self.one_step_angle:.4f} degrees of '
              f'angle and {self.one_step_speed:.4f} radians a second of speed')


WORLD: World | None = None


def _w() -> World:
    global WORLD
    if WORLD is None:
        WORLD = World()
    return WORLD


def rollout(stepper, state: Arr, us: Arr) -> Arr:
    """Run a sequence of torques through a stepper and return every state along the way."""
    out = [state]
    s = state
    for k in range(us.shape[-1]):
        s = stepper(s, us[..., k])
        out.append(s)
    return np.stack(out, axis=-2)


def one_step_job() -> None:
    """What a learned dynamics model is asked to do, with real numbers from the simulation."""
    w = _w()
    s0 = np.array([-0.45, 0.60])
    u0 = 1.2
    s1 = true_step(s0, np.array(u0))
    p1 = w.model.step(s0, np.array(u0))
    print(f'[one-step] from angle {np.degrees(s0[0]):+.2f} deg and speed {s0[1]:+.2f} rad/s '
          f'with torque {u0:+.1f} Nm')
    print(f'[one-step] the real system goes to {np.degrees(s1[0]):+.3f} deg and '
          f'{s1[1]:+.3f} rad/s; the learned model says {np.degrees(p1[0]):+.3f} deg and '
          f'{p1[1]:+.3f} rad/s')
    fig, ax = plt.subplots(figsize=(10.8, 4.6), facecolor='white')
    _blank(ax, (0, 1), (0.02, 1))
    ax.text(0.5, 0.955, 'One step of a learned dynamics model, worked out on the simulated arm',
            ha='center', va='center', fontsize=12.5, weight='bold', color=INK)
    _box(ax, 0.02, 0.56, 0.24, 0.26,
         'what it sees now\n\n'
         f'angle {np.degrees(s0[0]):+.2f} degrees\nspeed {s0[1]:+.2f} radians a second',
         fc='#eaf3fb', ec=LINK, fs=9.4)
    _box(ax, 0.02, 0.17, 0.24, 0.26,
         'what it is about to do\n\n'
         f'torque {u0:+.1f} newton metres\nfor one step of {DT * 1000:.0f} ms',
         fc='#fff6e0', ec=JOINT, fs=9.4)
    _box(ax, 0.33, 0.30, 0.22, 0.42,
         'the learned model\n\nten features of the\nangle, the speed and\nthe torque, times\n'
         f'{w.model.w.size} learned numbers',
         fc='#eee9f7', ec=PURPLE, fs=9.2)
    _arrow(ax, 0.265, 0.69, 0.325, 0.56, colour=MUTED)
    _arrow(ax, 0.265, 0.30, 0.325, 0.44, colour=MUTED)
    _arrow(ax, 0.555, 0.69, 0.625, 0.69, colour=MUTED)
    _box(ax, 0.63, 0.56, 0.345, 0.26,
         'what the model says comes next\n\n'
         f'angle {np.degrees(p1[0]):+.3f} degrees, '
         f'speed {p1[1]:+.3f} radians a second',
         fc='#eaf7ee', ec=SLIDE, fs=9.4)
    _box(ax, 0.63, 0.17, 0.345, 0.26,
         'what really comes next\n\n'
         f'angle {np.degrees(s1[0]):+.3f} degrees, '
         f'speed {s1[1]:+.3f} radians a second',
         fc='white', ec=INK, fs=9.4)
    ax.plot([0.60, 0.60], [0.30, 0.82], color=MUTED, lw=1.1, ls=':')
    ax.plot([0.60, 0.625], [0.69, 0.69], color=MUTED, lw=1.1, ls=':')
    ax.plot([0.60, 0.625], [0.30, 0.30], color=MUTED, lw=1.1, ls=':')
    ax.text(0.592, 0.49, 'compare', ha='right', va='center', fontsize=9, color=MUTED,
            rotation=90)
    ax.text(0.80, 0.09, f'over fresh data the gap is {w.one_step_angle:.4f} degrees of angle',
            ha='center', va='center', fontsize=9.6, color=INK)
    _save(fig, WM_DOC, 'one-step-job.svg')


def training_transitions() -> None:
    """Where in the state space the recorded transitions sit."""
    w = _w()
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    sub = slice(None, None, 7)
    ax.scatter(np.degrees(w.st[sub, 0]), w.st[sub, 1], s=5, c=w.ac[sub], cmap='coolwarm',
               alpha=0.6)
    ax.axvline(np.degrees(STOP), color=GRIP, lw=2)
    ax.text(np.degrees(STOP) - 1.5, 2.6, 'the hard stop', color=GRIP, fontsize=9.5,
            ha='right')
    ax.set_xlabel('joint angle (degrees)', fontsize=10)
    ax.set_ylabel('joint speed (radians a second)', fontsize=10)
    ax.set_title(f'{w.n:,} recorded transitions, coloured by the torque used',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    bars = ax.bar(['away from\nthe stop', 'touching\nthe stop'],
                  [int((~w.hit).sum()), int(w.hit.sum())], color=[LINK, GRIP], width=0.5)
    ax.bar_label(bars, fmt='%d', fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(1, w.n * 4)
    ax.set_ylabel('number of recorded transitions', fontsize=10)
    ax.set_title(f'Only {w.hit.mean() * 100:.2f}% of the recording touches the stop,\n'
                 'so the model barely learns it exists', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'training-transitions.svg')


def one_step_error() -> None:
    """How close the learned one-step prediction is on data it did not see."""
    w = _w()
    pred = w.model.step(w.vst, w.vac)
    err = np.degrees(pred[:, 0] - w.vnx[:, 0])
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    sub = slice(None, None, 5)
    ax.scatter(np.degrees(w.vnx[sub, 0]), np.degrees(pred[sub, 0]), s=5, color=LINK, alpha=0.4)
    lim = [np.degrees(w.vnx[:, 0]).min() - 2, np.degrees(w.vnx[:, 0]).max() + 2]
    ax.plot(lim, lim, color=INK, lw=1.2, ls='--')
    ax.set_xlabel('the angle the real system reaches (degrees)', fontsize=10)
    ax.set_ylabel('the angle the model predicts (degrees)', fontsize=10)
    ax.set_title(f'One step ahead the model is right to {w.one_step_angle:.3f} degrees',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.hist(err, bins=70, color=LINK_PALE, edgecolor=LINK, linewidth=0.5)
    ax.axvline(0, color=INK, lw=1.2)
    ax.set_xlabel('prediction minus truth, for one step (degrees)', fontsize=10)
    ax.set_ylabel('number of transitions', fontsize=10)
    ax.set_title('The one-step mistakes are small and sit around zero',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'one-step-error.svg')


def learned_against_true_physics() -> None:
    """What the model learned about gravity, against what gravity really does."""
    w = _w()
    th = np.linspace(-1.4, 1.0, 200)
    zero = np.zeros_like(th)
    state = np.stack([th, zero], axis=1)
    pred = w.model.step(state, zero)
    dom_model = (pred[:, 1] - zero) / DT
    dom_true = -(G / LINK_L) * np.sin(th)
    seen_lo = float(np.percentile(w.st[:, 0], 1.0))
    seen_hi = float(np.percentile(w.st[:, 0], 99.0))
    inside = (th >= seen_lo) & (th <= seen_hi)
    e_in = float(np.sqrt(np.mean((dom_model - dom_true)[inside] ** 2)))
    e_out = float(np.sqrt(np.mean((dom_model - dom_true)[~inside] ** 2)))
    print(f'[physics] the recording covered angles from {np.degrees(seen_lo):.1f} to '
          f'{np.degrees(seen_hi):.1f} degrees')
    print(f'[physics] the learned pull is wrong by {e_in:.4f} rad/s^2 inside those angles '
          f'and by {e_out:.4f} rad/s^2 outside them')
    fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor='white')
    _plain(ax)
    ax.plot(np.degrees(th), dom_true, color=INK, lw=2.4, label='what gravity really does')
    ax.plot(np.degrees(th), dom_model, color=PURPLE, lw=2, ls='--',
            label='what the learned model does')
    ax.axvspan(np.degrees(seen_lo), np.degrees(seen_hi), color='#eaf3fb',
               label='the middle 98% of the angles the recording covered')
    ax.axvline(np.degrees(STOP), color=GRIP, lw=2)
    ax.text(np.degrees(STOP) + 0.6, 6, 'the hard stop', color=GRIP, fontsize=9.5)
    ax.set_xlabel('joint angle (degrees)', fontsize=10)
    ax.set_ylabel('the pull on the joint (radians a second, each second)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title('The model copies the real pull where it has seen it, and guesses elsewhere',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'learned-against-true-physics.svg')


# ==========================================================================
# PART J -- page 4, section 2: predicting in a squeezed-down space
# ==========================================================================

IMG: int = 32
ROD_LEN: float = 20.0
GRIP_OPEN: float = 5.0
GRIP_SHUT: float = 2.0


def render(theta: float, grip: float) -> Arr:
    """A small grey camera picture of the simulated arm, as a 32 by 32 grid of brightness."""
    yy, xx = np.meshgrid(np.arange(IMG), np.arange(IMG), indexing='ij')
    px, py = IMG / 2.0, 2.0
    tipx = px + ROD_LEN * np.sin(theta)
    tipy = py + ROD_LEN * np.cos(theta)
    vx, vy = tipx - px, tipy - py
    ln = vx * vx + vy * vy
    t = np.clip(((xx - px) * vx + (yy - py) * vy) / ln, 0.0, 1.0)
    d = np.hypot(xx - (px + t * vx), yy - (py + t * vy))
    img = np.clip(1.0 - (d - 1.1) / 0.9, 0.0, 1.0)
    nx, ny = -vy / np.sqrt(ln), vx / np.sqrt(ln)
    for sign in (-1.0, 1.0):
        fx = tipx + sign * grip / 2.0 * nx
        fy = tipy + sign * grip / 2.0 * ny
        df = np.hypot(xx - fx, yy - fy)
        img = np.maximum(img, np.clip(1.0 - (df - 0.7) / 0.7, 0.0, 1.0))
    return img


class Latent:
    """A squeezed-down space for the pictures, found by principal components."""

    def __init__(self, n: int = 1200) -> None:
        rng = np.random.default_rng(17)
        self.theta = rng.uniform(-1.0, STOP, n)
        self.open = rng.integers(0, 2, n).astype(float)
        grips = np.where(self.open > 0.5, GRIP_OPEN, GRIP_SHUT)
        self.imgs = np.stack([render(t, g) for t, g in zip(self.theta, grips)])
        self.flat = self.imgs.reshape(n, -1)
        self.mean = self.flat.mean(axis=0)
        centred = self.flat - self.mean
        _u, sv, vt = np.linalg.svd(centred, full_matrices=False)
        self.sv = sv
        self.vt = vt
        self.scores = centred @ vt.T
        total = float((sv ** 2).sum())
        self.explained = np.cumsum(sv ** 2) / total * 100.0

    def rebuild(self, k: int) -> Arr:
        return (self.scores[:, :k] @ self.vt[:k] + self.mean).reshape(-1, IMG, IMG)

    def read_grip(self, k: int) -> float:
        x = np.concatenate([self.scores[:, :k], np.ones((self.scores.shape[0], 1))], axis=1)
        tr, te = slice(None, 900), slice(900, None)
        coef, *_ = np.linalg.lstsq(x[tr], self.open[tr], rcond=None)
        got = (x[te] @ coef) > 0.5
        return float(np.mean(got == (self.open[te] > 0.5)) * 100.0)


LAT: Latent | None = None
K_LIST: list[int] = [2, 4, 8, 16, 32, 64]


def _lat() -> Latent:
    global LAT
    if LAT is None:
        LAT = Latent()
    return LAT


def pixels_to_latent() -> None:
    """How many numbers a picture is, and how many are kept."""
    lat = _lat()
    big = 256 * 256 * 3
    print(f'[latent] one small picture here is {IMG} x {IMG} = {IMG * IMG} numbers')
    print(f'[latent] a real camera frame of 256 by 256 in colour is {big:,} numbers')
    for k in (8, 32):
        print(f'[latent] the first {k} components hold {lat.explained[k - 1]:.2f}% of what '
              f'moves in the pictures')
    fig, axes = plt.subplots(1, 4, figsize=(11.2, 3.6), facecolor='white')
    for ax, th in zip(axes, [-0.9, -0.3, 0.3, 0.85]):
        ax.imshow(render(th, GRIP_OPEN), cmap='gray_r', origin='lower',
                  vmin=0, vmax=1, interpolation='nearest')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f'angle {np.degrees(th):+.0f} degrees', fontsize=10)
    fig.suptitle(f'Four of the {len(lat.theta)} simulated camera pictures, each one '
                 f'{IMG} by {IMG} = {IMG * IMG} numbers',
                 fontsize=12, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    _save(fig, WM_DOC, 'pixels-to-latent.svg')


def variance_vs_latent_size() -> None:
    """How much of the picture a handful of numbers can hold."""
    lat = _lat()
    vals = [lat.explained[k - 1] for k in K_LIST]
    for k, v in zip(K_LIST, vals):
        print(f'[latent] {k:3d} numbers hold {v:.2f}% of what changes between pictures')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(K_LIST, vals, marker='o', color=TEAL, lw=2)
    ax.set_xscale('log', base=2)
    ax.set_xticks(K_LIST)
    ax.set_xticklabels([str(k) for k in K_LIST])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_ylim(0, 103)
    ax.set_xlabel('numbers kept for each picture', fontsize=10)
    ax.set_ylabel('share of what changes between pictures\nthat is kept (per cent)',
                  fontsize=10)
    ax.set_title(f'{K_LIST[2]} numbers already hold {vals[2]:.1f}% of it',
                 fontsize=11, weight='bold')
    for k, v in zip(K_LIST, vals):
        ax.annotate(f'{v:.1f}', (k, v), textcoords='offset points', xytext=(0, -16),
                    ha='center', fontsize=8.6, color=INK)
    ax = axes[1]
    _plain(ax)
    sizes = [IMG * IMG, 64, 32, 8]
    names = [f'the picture\n({IMG * IMG} numbers)', '64 numbers', '32 numbers', '8 numbers']
    weights = [n ** 2 for n in sizes]
    bars = ax.bar(names, weights, color=[GRIP, WRIST, JOINT, SLIDE], width=0.55)
    ax.bar_label(bars, labels=[f'{v:,}' for v in weights], fontsize=9, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(10, max(weights) * 40)
    ax.set_ylabel('weights in a one-layer model that maps\none state to the next', fontsize=10)
    ax.tick_params(axis='x', labelsize=9)
    ax.set_title('Predicting in the squeezed space is far less work',
                 fontsize=11, weight='bold')
    print(f'[latent] a one-layer predictor over raw pixels needs {(IMG * IMG) ** 2:,} weights, '
          f'and over 8 numbers it needs {8 ** 2}')
    fig.tight_layout()
    _save(fig, WM_DOC, 'variance-vs-latent-size.svg')


def what_is_lost() -> None:
    """What the squeezing throws away: the small detail that matters for grasping."""
    lat = _lat()
    opens = np.flatnonzero(lat.open > 0.5)
    shuts = np.flatnonzero(lat.open <= 0.5)
    j = int(np.argmin(np.abs(lat.theta[shuts] - lat.theta[opens[0]])))
    pick = [int(opens[0]), int(shuts[j])]
    print(f'[lost] the two pictures shown sit at {np.degrees(lat.theta[pick[0]]):.1f} and '
          f'{np.degrees(lat.theta[pick[1]]):.1f} degrees, one with the fingers open and one '
          'with them shut')
    r8 = lat.rebuild(8)
    r64 = lat.rebuild(64)
    fig, axes = plt.subplots(2, 3, figsize=(8.4, 5.8), facecolor='white')
    for row, i in enumerate(pick):
        for col, (img, name) in enumerate([(lat.imgs[i], 'the real picture'),
                                           (r8[i], 'rebuilt from 8 numbers'),
                                           (r64[i], 'rebuilt from 64 numbers')]):
            ax = axes[row, col]
            ax.imshow(img, cmap='gray_r', origin='lower', vmin=0, vmax=1,
                      interpolation='nearest')
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(name, fontsize=10.5, weight='bold')
            if col == 0:
                ax.set_ylabel('fingers '
                              + ('open' if lat.open[i] > 0.5 else 'shut'), fontsize=10)
    e8 = float(np.sqrt(np.mean((r8 - lat.imgs) ** 2)))
    e64 = float(np.sqrt(np.mean((r64 - lat.imgs) ** 2)))
    print(f'[lost] rebuilding from 8 numbers is {e8:.4f} off per pixel of brightness, '
          f'and from 64 numbers {e64:.4f}')
    fig.suptitle('The rod survives the squeeze; whether the fingers are open does not',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, WM_DOC, 'what-is-lost.svg')


def reading_the_gripper() -> None:
    """How well the open or shut fingers can be read back out of the squeezed numbers."""
    lat = _lat()
    accs = [lat.read_grip(k) for k in K_LIST]
    for k, a in zip(K_LIST, accs):
        print(f'[gripper] from {k:3d} numbers, whether the fingers are open is read right '
              f'{a:.1f}% of the time')
    fig, ax = plt.subplots(figsize=(8.0, 4.5), facecolor='white')
    _plain(ax)
    bars = ax.bar([str(k) for k in K_LIST], accs, color=TEAL, width=0.55)
    ax.bar_label(bars, labels=[f'{a:.0f}%' for a in accs], fontsize=10, padding=3)
    ax.axhline(50, color=GRIP, lw=1.6, ls='--')
    ax.text(0.985, 0.47, 'guessing', color=GRIP, fontsize=9.5, ha='right',
            va='bottom', transform=ax.transAxes)
    ax.set_ylim(0, 112)
    ax.set_xlabel('numbers kept for each picture', fontsize=10)
    ax.set_ylabel('how often the fingers are read right (per cent)', fontsize=10)
    ax.set_title('A squeeze that keeps most of the picture can still lose\n'
                 'the one detail a grasp depends on', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'reading-the-gripper.svg')


# ==========================================================================
# PART K -- page 4, section 3: error that piles up over a rollout
# ==========================================================================

ROLL: int = 60
THRESH_DEG: float = 0.25


def test_rollouts(n: int, seed: int, free_only: bool = True) -> tuple[Arr, Arr, Arr, float]:
    """Fresh starts and torque sequences, run through the real system and the learned model.

    With free_only, only the runs whose real path never touches the hard stop are kept, so
    that the growth of the error is the model's own drift and not the unmodelled contact.
    """
    w = _w()
    rng = np.random.default_rng(seed)
    s0 = np.stack([rng.uniform(-1.0, -0.15, n), rng.uniform(-0.8, 0.8, n)], axis=1)
    us = _smooth_torque(n, ROLL, rng)
    tru = rollout(true_step, s0, us)
    pre = rollout(w.model.step, s0, us)
    free = ~np.any(tru[:, :, 0] >= STOP - 1e-9, axis=1)
    share = float(free.mean())
    if free_only:
        return tru[free], pre[free], us[free], share
    return tru, pre, us, share


def rollout_vs_truth() -> None:
    """One run of the real system beside the same run inside the learned model."""
    tr, pr, _us, _share = test_rollouts(200, 5)
    tru, pre = tr[0], pr[0]
    gap = np.degrees(np.abs(pre[:, 0] - tru[:, 0]))
    first = int(np.argmax(gap > THRESH_DEG)) if np.any(gap > THRESH_DEG) else ROLL
    print(f'[rollout] on this run the two paths part by more than {THRESH_DEG:.2f} degrees '
          f'after {first} steps, which is {first * DT:.2f} seconds')
    print(f'[rollout] by step {ROLL} the gap is {gap[-1]:.2f} degrees')
    t = np.arange(ROLL + 1) * DT
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(t, np.degrees(tru[:, 0]), color=INK, lw=2.4, label='the real system')
    ax.plot(t, np.degrees(pre[:, 0]), color=PURPLE, lw=2, ls='--',
            label='the learned model, run on its own output')
    ax.axvline(first * DT, color=GRIP, lw=1.4, ls=':')
    ax.text(first * DT + 0.08, np.degrees(tru[:, 0]).max(),
            f'{THRESH_DEG:.2f} degrees apart\nafter {first * DT:.2f} s', fontsize=9,
            color=GRIP, va='top')
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('joint angle (degrees)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False, loc='lower center')
    ax.set_title('Same starting point, same torques, two paths',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(t, gap, color=GRIP, lw=2)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('how far apart the two angles are (degrees)', fontsize=10)
    ax.set_title('The gap opens and closes as the arm swings,\nand each swing opens it wider',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'rollout-vs-truth.svg')


def error_vs_horizon() -> None:
    """Averaged over many starts, how far ahead the model stays useful."""
    w = _w()
    tru, pre, _us, share = test_rollouts(600, 31)
    n = tru.shape[0]
    print(f'[horizon] {n} of 600 runs never touch the hard stop ({share * 100:.0f}%), and '
          'only those are measured here')
    gap = np.degrees(np.mean(np.abs(pre[:, :, 0] - tru[:, :, 0]), axis=0))
    cross = int(np.argmax(gap > THRESH_DEG)) if np.any(gap > THRESH_DEG) else ROLL
    for k in (1, 5, 10, 20, 40, 60):
        print(f'[horizon] {k:2d} steps ahead ({k * DT:.2f} s): average gap {gap[k]:.3f} degrees')
    print(f'[horizon] the average gap passes {THRESH_DEG:.2f} degrees at step {cross} '
          f'({cross * DT:.2f} s)')
    fig, ax = plt.subplots(figsize=(8.2, 4.6), facecolor='white')
    _plain(ax)
    ax.plot(np.arange(ROLL + 1), gap, color=PURPLE, lw=2.4)
    ax.axhline(THRESH_DEG, color=GRIP, lw=1.5, ls='--')
    ax.axvline(cross, color=GRIP, lw=1.5, ls=':')
    ax.text(cross + 2.0, THRESH_DEG * 0.35,
            f'past {cross} steps the model is wrong\nby more than {THRESH_DEG:.2f} degrees',
            fontsize=9.4, color=GRIP)
    ax.set_ylim(0, gap.max() * 1.15)
    ax.set_xlabel('steps predicted ahead', fontsize=10)
    ax.set_ylabel('average gap in the angle (degrees)', fontsize=10)
    ax.set_title(f'Averaged over {n} starts: a one-step error of '
                 f'{w.one_step_angle:.3f} degrees\nbecomes {gap[-1]:.1f} degrees by step {ROLL}',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'error-vs-horizon.svg')


def phase_path() -> None:
    """The same divergence seen as a path through angle and speed together."""
    tr, pr, _us, _share = test_rollouts(200, 12)
    tru, pre = tr[1], pr[1]
    print(f'[phase] the real path ends at angle {np.degrees(tru[-1, 0]):.2f} degrees and speed '
          f'{tru[-1, 1]:.2f} rad/s; the model ends at {np.degrees(pre[-1, 0]):.2f} degrees and '
          f'{pre[-1, 1]:.2f} rad/s')
    fig, ax = plt.subplots(figsize=(7.8, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(np.degrees(tru[:, 0]), tru[:, 1], color=INK, lw=2.2, label='the real system')
    ax.plot(np.degrees(pre[:, 0]), pre[:, 1], color=PURPLE, lw=2, ls='--',
            label='the learned model')
    for k, off in ((0, (8, -10)), (10, (6, 8)), (20, (8, 4)), (40, (-6, 10)), (60, (8, -8))):
        ax.plot(np.degrees(tru[k, 0]), tru[k, 1], 'o', color=INK, ms=7)
        ax.plot(np.degrees(pre[k, 0]), pre[k, 1], 'o', color=PURPLE, ms=4)
        ax.annotate(f'step {k}', (np.degrees(tru[k, 0]), tru[k, 1]),
                    textcoords='offset points', xytext=off, fontsize=8.6, color=MUTED)
    ax.set_xlabel('joint angle (degrees)', fontsize=10)
    ax.set_ylabel('joint speed (radians a second)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    gap_end = float(np.degrees(abs(pre[-1, 0] - tru[-1, 0])))
    ax.set_title('Two turns round the same loop, and by step 60 the two\n'
                 f'paths are {gap_end:.2f} degrees apart', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'phase-path.svg')


def more_data_does_not_fix_it() -> None:
    """More recorded transitions make the one-step prediction better and the rollout no better."""
    rng = np.random.default_rng(44)
    n = 400
    s0 = np.stack([rng.uniform(-1.0, -0.15, n), rng.uniform(-0.8, 0.8, n)], axis=1)
    us = _smooth_torque(n, ROLL, rng)
    tru = rollout(true_step, s0, us)
    free = ~np.any(tru[:, :, 0] >= STOP - 1e-9, axis=1)
    s0, us, tru = s0[free], us[free], tru[free]
    vst, vac, vnx, vhit = make_transitions(80, 30, seed=3, noise=0.0)
    keepv = ~vhit
    vst, vac, vnx = vst[keepv], vac[keepv], vnx[keepv]
    eps = [10, 25, 50, 100, 200, 400]
    ones, finals = [], []
    for e in eps:
        st, ac, nx, hit = make_transitions(e, 30, seed=1000 + e)
        keep = ~hit
        m = LearnedModel(st[keep], ac[keep], nx[keep])
        one = float(np.degrees(_rmse(m.step(vst, vac)[:, 0], vnx[:, 0])))
        pre = rollout(m.step, s0, us)
        gap = float(np.degrees(np.mean(np.abs(pre[:, -1, 0] - tru[:, -1, 0]))))
        ones.append(one)
        finals.append(gap)
        print(f'[data] {e * 30:6,} recorded transitions: one step off by {one:.4f} degrees, '
              f'{ROLL} steps off by {gap:.2f} degrees')
    print(f'[data] from the smallest to the largest set the one-step error falls '
          f'{ones[0] / ones[-1]:.0f} times over, while the {ROLL}-step gap changes by a factor '
          f'of only {max(finals) / min(finals):.2f}')
    xs = [e * 30 for e in eps]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(xs, ones, marker='o', color=TEAL, lw=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('recorded transitions used to fit the model', fontsize=10)
    ax.set_ylabel('error one step ahead (degrees)', fontsize=10)
    ax.set_title('One step ahead, more data helps a lot', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(xs, finals, marker='s', color=GRIP, lw=2)
    ax.set_xscale('log')
    ax.set_xlabel('recorded transitions used to fit the model', fontsize=10)
    ax.set_ylabel(f'gap after {ROLL} steps (degrees)', fontsize=10)
    ax.set_ylim(0, max(finals) * 1.3)
    ax.set_title(f'{ROLL} steps ahead, more data does not help at all',
                 fontsize=11, weight='bold')
    fig.suptitle('The far-off error comes from the shape of the model, not from a shortage '
                 'of data', fontsize=12.5, weight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    _save(fig, WM_DOC, 'more-data-does-not-fix-it.svg')


# ==========================================================================
# PART L -- page 4, section 4: planning inside the model
# ==========================================================================

def step_cost(state: Arr, u: Arr) -> Arr:
    return (state[..., 0] - GOAL) ** 2 + 0.05 * state[..., 1] ** 2 + 0.01 * u ** 2


def plan_and_run(stepper, n_cand: int, horizon: int, steps: int = 50, seed: int = 0
                 ) -> tuple[float, float, Arr]:
    """Try n_cand torque sequences inside `stepper`, run the first torque of the best one."""
    rng = np.random.default_rng(seed)
    s = np.array([-0.80, 0.0])
    traj = [s.copy()]
    real_cost = 0.0
    believed = 0.0
    for _t in range(steps):
        cands = _smooth_torque(n_cand, horizon, rng, tmax=TORQUE_PLAN)
        batch = np.repeat(s[None, :], n_cand, axis=0)
        cost = np.zeros(n_cand)
        for k in range(horizon):
            batch = stepper(batch, cands[:, k])
            cost += step_cost(batch, cands[:, k])
        best = int(np.argmin(cost))
        believed += float(cost[best]) / horizon
        u = cands[best, 0]
        s = true_step(s, np.array(u))
        real_cost += float(step_cost(s, np.array(u)))
        traj.append(s.copy())
    return real_cost, believed, np.array(traj)


def candidate_sequences() -> None:
    """The fan of candidate futures the planner looks at, and the one it picks."""
    w = _w()
    rng = np.random.default_rng(99)
    s = np.array([-0.80, 0.0])
    n_cand, horizon = 40, 20
    cands = _smooth_torque(n_cand, horizon, rng, tmax=TORQUE_PLAN)
    batch = np.repeat(s[None, :], n_cand, axis=0)
    paths = [batch.copy()]
    cost = np.zeros(n_cand)
    for k in range(horizon):
        batch = w.model.step(batch, cands[:, k])
        cost += step_cost(batch, cands[:, k])
        paths.append(batch.copy())
    paths = np.stack(paths, axis=1)
    best = int(np.argmin(cost))
    real = rollout(true_step, s, cands[best])
    print(f'[plan] {n_cand} candidate torque sequences of {horizon} steps were tried inside '
          f'the model, which is {n_cand * horizon} model steps for one decision')
    print(f'[plan] the best candidate scores {cost[best] / horizon:.4f} inside the model; '
          f'run on the real system the same torques end at '
          f'{np.degrees(real[-1, 0]):.2f} degrees against the model\'s '
          f'{np.degrees(paths[best, -1, 0]):.2f} degrees')
    t = np.arange(horizon + 1) * DT
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor='white')
    _plain(ax)
    for i in range(n_cand):
        ax.plot(t, np.degrees(paths[i, :, 0]), color=LINK, lw=0.9, alpha=0.35)
    ax.plot(t, np.degrees(paths[best, :, 0]), color=SLIDE, lw=2.6,
            label='the candidate the planner picks')
    ax.plot(t, np.degrees(real[:, 0]), color=INK, lw=2.2, ls='--',
            label='what those torques really do')
    ax.axhline(np.degrees(GOAL), color=JOINT, lw=1.6, ls=':', label='the angle it is aiming for')
    ax.set_xlabel('seconds ahead', fontsize=10)
    ax.set_ylabel('joint angle (degrees)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False, loc='lower right')
    ax.set_title(f'{n_cand} futures tried inside the model, {horizon} steps each',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'candidate-sequences.svg')


def arithmetic_of_planning() -> None:
    """How many futures fit inside one control period."""
    period_ms = DT * 1000.0
    per_call_us = [0.5, 5.0, 50.0, 500.0]
    names = ['a handful of\nsums (0.5 us)', 'a small network\n(5 us)',
             'a latent network\n(50 us)', 'a video model\n(500 us)']
    budget = period_ms * 1000.0
    allowed = [budget / c for c in per_call_us]
    for nm, c, a in zip(names, per_call_us, allowed):
        print(f'[arith] at {c} microseconds a step, {a:,.0f} model steps fit in the '
              f'{period_ms:.0f} ms between commands, which is {a / 20:,.0f} candidates '
              '20 steps long')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(names, [a / 20 for a in allowed],
                  color=[SLIDE, TEAL, JOINT, GRIP], width=0.55)
    ax.bar_label(bars, labels=[f'{a / 20:,.0f}' for a in allowed], fontsize=9.5, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(0.1, max(allowed) / 20 * 40)
    ax.tick_params(axis='x', labelsize=8.4)
    ax.set_ylabel('candidate futures of 20 steps that fit\nin one control period', fontsize=10)
    ax.set_title(f'{period_ms:.0f} ms between commands at {1 / DT:.0f} Hz',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    cands = np.array([16, 64, 256, 1024])
    for h, colour in zip([5, 10, 20, 40], [SLIDE, TEAL, JOINT, GRIP]):
        ax.plot(cands, cands * h, marker='o', color=colour, lw=2, label=f'{h} steps ahead')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(cands)
    ax.set_xticklabels([str(c) for c in cands])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('candidate torque sequences tried', fontsize=10)
    ax.set_ylabel('model steps for one decision', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('Candidates times horizon is the whole bill',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'arithmetic-of-planning.svg')


CAND_LIST: list[int] = [4, 16, 64, 256]
HORIZON_LIST: list[int] = [5, 10, 20, 40]


def more_candidates() -> None:
    """More candidates give a better plan, up to a point set by the model's own error."""
    w = _w()
    learned, perfect = [], []
    for k in CAND_LIST:
        a = float(np.mean([plan_and_run(w.model.step, k, 15, seed=s)[0] for s in range(3)]))
        b = float(np.mean([plan_and_run(true_step, k, 15, seed=s)[0] for s in range(3)]))
        learned.append(a)
        perfect.append(b)
        print(f'[cands] {k:4d} candidates: cost {a:.3f} planning in the learned model, '
              f'{b:.3f} planning in the real one')
    fig, ax = plt.subplots(figsize=(8.0, 4.6), facecolor='white')
    _plain(ax)
    ax.plot(CAND_LIST, learned, marker='o', color=PURPLE, lw=2, label='planned in the learned model')
    ax.plot(CAND_LIST, perfect, marker='s', color=SLIDE, lw=2, label='planned in the real system')
    ax.set_xscale('log', base=2)
    ax.set_xticks(CAND_LIST)
    ax.set_xticklabels([str(c) for c in CAND_LIST])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('candidate torque sequences tried for each decision', fontsize=10)
    ax.set_ylabel('cost actually paid on the real system', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('With the plan remade at every step, the learned model\n'
                 'very nearly matches a perfect one', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'more-candidates.svg')


HOLD_GOAL: float = 0.20       # a reachable angle to hold, for the re-planning experiment
EXTRA_PULL: float = -0.45     # a steady pull the model knows nothing about, in newton metres


def _hold_cost(state: Arr, u: Arr) -> Arr:
    return (state[..., 0] - HOLD_GOAL) ** 2 + 0.05 * state[..., 1] ** 2 + 0.01 * u ** 2


def replanning_rate() -> None:
    """How often the plan has to be remade when the real arm is not quite the modelled one."""
    w = _w()
    total, horizon, k = 40, 25, 256
    every = [1, 2, 5, 10, 20]
    offs = []
    for e in every:
        runs = []
        for seed in range(6):
            rng = np.random.default_rng(3000 + seed)
            s = np.array([-0.80, 0.0])
            plan = np.zeros(horizon)
            errs = []
            for t in range(total):
                if t % e == 0:
                    cands = _smooth_torque(k, horizon, rng, tmax=TORQUE_PLAN)
                    batch = np.repeat(s[None, :], k, axis=0)
                    cost = np.zeros(k)
                    for j in range(horizon):
                        batch = w.model.step(batch, cands[:, j])
                        cost += _hold_cost(batch, cands[:, j])
                    plan = cands[int(np.argmin(cost))]
                u = plan[t % e]
                s = true_step(s, np.array(u + EXTRA_PULL))
                if t >= 20:
                    errs.append(abs(float(s[0]) - HOLD_GOAL))
            runs.append(float(np.mean(errs)))
        offs.append(float(np.degrees(np.mean(runs))))
        print(f'[replan] the plan remade every {e:2d} steps ({e * DT:.2f} s): the arm settles '
              f'{offs[-1]:.2f} degrees away from the angle it was asked to hold')
    print(f'[replan] remaking the plan at every step leaves {offs[0]:.2f} degrees of error '
          f'against {offs[-1]:.2f} degrees when it is remade once a second')
    fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor='white')
    _plain(ax)
    ax.plot([e * DT for e in every], offs, marker='o', color=PURPLE, lw=2)
    ax.set_xscale('log')
    ax.set_xticks([e * DT for e in every])
    ax.set_xticklabels([f'{e * DT:.2f}' for e in every])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('seconds between one plan and the next', fontsize=10)
    ax.set_ylabel('how far from the asked-for angle the arm settles\n(degrees)', fontsize=10)
    ax.set_ylim(0, max(offs) * 1.2)
    ax.set_title(f'With a steady pull of {abs(EXTRA_PULL):.2f} newton metres the model knows '
                 f'nothing about,\nremaking the plan every step takes {offs[-1] - offs[0]:.1f} '
                 'degrees off the error', fontsize=11.2, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'replanning-rate.svg')


# ==========================================================================
# PART M -- page 4, sections 5 and 6: video, simulators and wrong physics
# ==========================================================================

VIDEO_HOURS: int = 10_000
VIDEO_FPS: int = 30


def labelled_against_unlabelled() -> None:
    """Why video is tempting: nobody has to record what the robot did."""
    robot_frames = N_TASKS * DEMOS_PER_TASK * EP.horizon
    video_frames = VIDEO_HOURS * 3600 * VIDEO_FPS
    print(f'[video] {N_TASKS} tasks x {DEMOS_PER_TASK} demonstrations x {EP.horizon} steps = '
          f'{robot_frames:,} frames with a recorded action beside them')
    print(f'[video] {VIDEO_HOURS:,} hours of ordinary video at {VIDEO_FPS} frames a second is '
          f'{video_frames:,} frames with no action at all')
    print(f'[video] that is {video_frames / robot_frames:,.0f} times as many frames')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['frames with a\nrecorded action', 'frames of ordinary\nvideo'],
                  [robot_frames, video_frames], color=[SLIDE, PURPLE], width=0.5)
    ax.bar_label(bars, labels=[f'{robot_frames:,}', f'{video_frames:,}'], fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(1e4, video_frames * 25)
    ax.set_ylabel('number of frames', fontsize=10)
    ax.set_title(f'About {video_frames / robot_frames:,.0f} times as much video exists',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _blank(ax, (0, 1), (0, 1))
    ax.text(0.5, 0.93, 'What each kind of frame can teach', ha='center', va='center',
            fontsize=11.5, weight='bold', color=INK)
    _box(ax, 0.03, 0.52, 0.44, 0.33,
         'a frame with its action\n\nwhat I see, what I did,\nwhat happened next\n\n'
         'enough to plan with', fc='#eaf7ee', ec=SLIDE, fs=9.4)
    _box(ax, 0.53, 0.52, 0.44, 0.33,
         'a frame of ordinary video\n\nwhat I see and what\nhappened next\n\n'
         'no record of what caused it', fc='#eee9f7', ec=PURPLE, fs=9.4)
    ax.text(0.5, 0.30, 'A world model trained on video learns how the world usually carries on.\n'
            'To plan with it, the model still has to be told what the arm did, which is why\n'
            'video pretraining is almost always followed by training on recorded episodes.',
            ha='center', va='center', fontsize=9.6, color=INK)
    fig.tight_layout()
    _save(fig, WM_DOC, 'labelled-against-unlabelled.svg')


def cost_of_predicting_pixels() -> None:
    """What it costs to predict a picture instead of a short list of numbers."""
    frame = 256 * 256 * 3
    diffusion_steps = 20
    latent = 32
    k, h = 64, 20
    per_frame = frame * diffusion_steps
    plan_pixels = k * h * per_frame
    plan_latent = k * h * latent
    print(f'[pixels] one predicted frame at 256 by 256 in colour is {frame:,} numbers, and a '
          f'generator that takes {diffusion_steps} steps writes {per_frame:,} of them')
    print(f'[pixels] one planning decision with {k} candidates {h} steps long writes '
          f'{plan_pixels:,} numbers in pixels and {plan_latent:,} in a {latent}-number '
          'squeezed space')
    print(f'[pixels] the pixel version is {plan_pixels / plan_latent:,.0f} times the work')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = [f'{latent} squeezed\nnumbers', f'one frame\n({frame:,} numbers)',
             f'one frame through a\n{diffusion_steps}-step generator']
    vals = [latent, frame, per_frame]
    bars = ax.bar(names, vals, color=[SLIDE, JOINT, GRIP], width=0.55)
    ax.bar_label(bars, labels=[f'{v:,}' for v in vals], fontsize=9.5, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(1, per_frame * 60)
    ax.tick_params(axis='x', labelsize=8.6)
    ax.set_ylabel('numbers written for one predicted step', fontsize=10)
    ax.set_title('One step ahead', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    bars = ax.bar(['in the squeezed space', 'in pixels'], [plan_latent, plan_pixels],
                  color=[SLIDE, GRIP], width=0.45)
    ax.bar_label(bars, labels=[f'{plan_latent:,}', f'{plan_pixels:,}'], fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(1e3, plan_pixels * 60)
    ax.set_ylabel('numbers written for one planning decision', fontsize=10)
    ax.set_title(f'{k} candidates, {h} steps each, in the {DT * 1000:.0f} ms '
                 'between commands', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'cost-of-predicting-pixels.svg')


def simulator_against_learned() -> None:
    """Where a learned stand-in for the physics is right, and where it is not."""
    w = _w()
    rng = np.random.default_rng(66)
    n = 4000
    st = np.stack([rng.uniform(-1.0, STOP + 0.25, n), rng.uniform(-2.0, 2.0, n)], axis=1)
    ac = rng.uniform(-TORQUE_PLAN, TORQUE_PLAN, n)
    nxt = true_step(st, ac)
    pred = w.model.step(st, ac)
    hit = nxt[:, 0] >= STOP - 1e-9
    e_free = float(np.degrees(_rmse(pred[~hit, 0], nxt[~hit, 0])))
    e_hit = float(np.degrees(_rmse(pred[hit, 0], nxt[hit, 0])))
    e_free_sp = float(_rmse(pred[~hit, 1], nxt[~hit, 1]))
    e_hit_sp = float(_rmse(pred[hit, 1], nxt[hit, 1]))
    print(f'[sim] away from the stop the learned step is off by {e_free:.4f} degrees and '
          f'{e_free_sp:.4f} rad/s; at the stop it is off by {e_hit:.3f} degrees and '
          f'{e_hit_sp:.3f} rad/s')
    print(f'[sim] that is {e_hit / e_free:,.0f} times worse in the angle and '
          f'{e_hit_sp / e_free_sp:,.0f} times worse in the speed')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bars = ax.bar(['steps away from\nthe stop', 'steps that touch\nthe stop'],
                  [e_free, e_hit], color=[SLIDE, GRIP], width=0.5)
    ax.bar_label(bars, labels=[f'{e_free:.4f} deg', f'{e_hit:.2f} deg'], fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(e_free / 4, e_hit * 12)
    ax.set_ylabel('one-step error in the angle (degrees)', fontsize=10)
    ax.set_title(f'The same model, {e_hit / e_free:,.0f} times worse where it never looked',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    bars = ax.bar(['steps away from\nthe stop', 'steps that touch\nthe stop'],
                  [e_free_sp, e_hit_sp], color=[SLIDE, GRIP], width=0.5)
    ax.bar_label(bars, labels=[f'{e_free_sp:.4f}', f'{e_hit_sp:.3f}'], fontsize=10, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(e_free_sp / 4, e_hit_sp * 12)
    ax.set_ylabel('one-step error in the speed (radians a second)', fontsize=10)
    ax.set_title('And the speed is where the contact really shows',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'simulator-against-learned.svg')


def through_the_stop() -> None:
    """What the model does when the arm reaches the one thing it never saw."""
    w = _w()
    rng = np.random.default_rng(404)
    found = None
    for _try in range(200):
        s0 = np.array([rng.uniform(-0.6, -0.2), rng.uniform(0.4, 0.8)])
        us = _smooth_torque(1, ROLL, rng, tmax=TORQUE_PLAN)[0]
        tru = rollout(true_step, s0, us)
        if np.any(tru[:, 0] >= STOP - 1e-9):
            found = (s0, us, tru)
            break
    assert found is not None
    s0, us, tru = found
    pre = rollout(w.model.step, s0, us)
    first = int(np.argmax(tru[:, 0] >= STOP - 1e-9))
    over = float(np.degrees(pre[:, 0].max() - STOP))
    print(f'[stop] the real arm reaches the stop at step {first} ({first * DT:.2f} s); the '
          f'model sails {over:.1f} degrees past it, up to '
          f'{np.degrees(pre[:, 0].max()):.1f} degrees')
    tru_all, pre_all, _u, share = test_rollouts(600, 31, free_only=False)
    free = ~np.any(tru_all[:, :, 0] >= STOP - 1e-9, axis=1)
    gap_free = np.degrees(np.mean(np.abs(pre_all[free, :, 0] - tru_all[free, :, 0]), axis=0))
    gap_hit = np.degrees(np.mean(np.abs(pre_all[~free, :, 0] - tru_all[~free, :, 0]), axis=0))
    print(f'[stop] averaged over runs that touch the stop the gap reaches {gap_hit[-1]:.1f} '
          f'degrees by step {ROLL}, against {gap_free[-1]:.2f} degrees for runs that do not')
    t = np.arange(ROLL + 1) * DT
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(t, np.degrees(tru[:, 0]), color=INK, lw=2.4, label='the real arm')
    ax.plot(t, np.degrees(pre[:, 0]), color=PURPLE, lw=2, ls='--', label='the learned model')
    ax.axhline(np.degrees(STOP), color=GRIP, lw=1.8)
    ax.text(t[-1], np.degrees(STOP) + 2.2, 'the hard stop', color=GRIP, fontsize=9.5,
            ha='right')
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('joint angle (degrees)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title(f'The model takes the arm {over:.0f} degrees through solid metal',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(np.arange(ROLL + 1), gap_free, color=SLIDE, lw=2.2,
            label='runs that never touch the stop')
    ax.plot(np.arange(ROLL + 1), gap_hit, color=GRIP, lw=2.2, label='runs that touch it')
    ax.set_yscale('log')
    ax.set_xlabel('steps predicted ahead', fontsize=10)
    ax.set_ylabel('average gap in the angle (degrees)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False, loc='lower right')
    ax.set_title('One rare event the model never learned costs more\n'
                 'than all the ordinary drift put together', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'through-the-stop.svg')


def energy_drift() -> None:
    """A model that is almost right still makes or destroys energy as it runs."""
    w = _w()
    s0 = np.array([-0.40, 0.0])
    us = np.zeros(ROLL)
    tru = rollout(true_step, s0, us)
    pre = rollout(w.model.step, s0, us)

    def energy(path: Arr) -> Arr:
        return (0.5 * MASS * LINK_L ** 2 * path[:, 1] ** 2
                + MASS * G * LINK_L * (1.0 - np.cos(path[:, 0])))

    et, ep = energy(tru), energy(pre)
    reached = float(np.degrees(np.max(tru[:, 0])))
    print(f'[energy] the real arm swings up to {reached:.1f} degrees, which stays clear of '
          f'the stop at {np.degrees(STOP):.1f} degrees, so nothing but friction is at work')
    print(f'[energy] with no torque at all, the real arm goes from {et[0]:.4f} to {et[-1]:.4f} '
          f'joules as friction takes the energy away')
    print(f'[energy] the learned model goes from {ep[0]:.4f} to {ep[-1]:.4f} joules, which is '
          f'{(ep[-1] - et[-1]) / et[0] * 100:+.1f}% of the starting energy out of nowhere')
    t = np.arange(ROLL + 1) * DT
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(t, np.degrees(tru[:, 0]), color=INK, lw=2.4, label='the real arm')
    ax.plot(t, np.degrees(pre[:, 0]), color=PURPLE, lw=2, ls='--', label='the learned model')
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('joint angle (degrees)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False)
    ax.set_title('Let go from rest with no torque at all', fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(t, et, color=INK, lw=2.4, label='the real arm')
    ax.plot(t, ep, color=PURPLE, lw=2, ls='--', label='the learned model')
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('energy held by the arm (joules)', fontsize=10)
    ax.legend(fontsize=9.2, frameon=False)
    ax.set_title('The model lets the energy go a little more slowly\nthan the arm does',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'energy-drift.svg')


OPEN_K: list[int] = [4, 16, 64, 256, 1024, 4096]


def plan_that_exploits_the_error() -> None:
    """The planner finds the sequences the model is most wrong about."""
    w = _w()
    h = 40
    believed, really, best = [], [], []
    for k in OPEN_K:
        bs, rs, gs = [], [], []
        for seed in range(5):
            rng = np.random.default_rng(1000 + seed)
            s0 = np.array([-0.80, 0.0])
            cands = _smooth_torque(k, h, rng, tmax=TORQUE_PLAN)
            bm = np.repeat(s0[None, :], k, axis=0)
            mc = np.zeros(k)
            for j in range(h):
                bm = w.model.step(bm, cands[:, j])
                mc += step_cost(bm, cands[:, j])
            bt = np.repeat(s0[None, :], k, axis=0)
            tc = np.zeros(k)
            for j in range(h):
                bt = true_step(bt, cands[:, j])
                tc += step_cost(bt, cands[:, j])
            i = int(np.argmin(mc))
            bs.append(mc[i] / h)
            rs.append(tc[i] / h)
            gs.append(tc.min() / h)
        believed.append(float(np.mean(bs)))
        really.append(float(np.mean(rs)))
        best.append(float(np.mean(gs)))
        print(f'[exploit] {k:5d} candidates: the model expects {believed[-1]:.4f}, the real '
              f'system charges {really[-1]:.4f}, and the best of those candidates would have '
              f'cost {best[-1]:.4f}')
    flat = [r - b for r, b in zip(really, believed)]
    lost = [r - g for r, g in zip(really, best)]
    print(f'[exploit] the model flatters itself by between {min(flat):.4f} and {max(flat):.4f} '
          'a step, however many candidates are tried')
    print(f'[exploit] choosing by the model rather than by the truth costs between '
          f'{min(lost):.4f} and {max(lost):.4f} a step, and that never goes away')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(OPEN_K, believed, marker='o', color=PURPLE, lw=2, label='what the model expects to pay')
    ax.plot(OPEN_K, really, marker='s', color=GRIP, lw=2, label='what the real system charges')
    ax.plot(OPEN_K, best, marker='^', color=SLIDE, lw=2,
            label='the best of the same candidates')
    ax.set_xscale('log', base=2)
    ax.set_xticks(OPEN_K)
    ax.set_xticklabels([str(k) for k in OPEN_K])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('candidate torque sequences tried', fontsize=10)
    ax.set_ylabel('average cost of one step', fontsize=10)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title(f'Planning {h} steps ahead, towards an angle past the stop',
                 fontsize=11, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(OPEN_K, flat, marker='o', color=GRIP, lw=2,
            label='how much the model flatters itself')
    ax.plot(OPEN_K, lost, marker='^', color=WRIST, lw=2,
            label='how much is lost by choosing with the model')
    ax.set_ylim(0, max(flat) * 1.35)
    ax.set_xscale('log', base=2)
    ax.set_xticks(OPEN_K)
    ax.set_xticklabels([str(k) for k in OPEN_K])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('candidate torque sequences tried', fontsize=10)
    ax.set_ylabel('cost per step', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_title('Trying more candidates improves the plan but never\ncloses either gap',
                 fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, WM_DOC, 'plan-that-exploits-the-error.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)

    # 03_vision-language-action-models.md
    vla_input_output()
    same_picture_two_sentences()
    one_model_many_tasks()
    vla_body_shapes()
    resolution_and_tokens()
    two_ways_to_get_an_action()
    binning_one_dimension()
    quantisation_error_vs_bins()
    percentile_range_matters()
    tokens_per_chunk()
    flow_head_path()
    flow_steps_vs_error()
    head_vs_tokens_latency()
    continuous_vs_binned()
    forgetting_curve()
    mixture_sweep()
    data_sizes()
    action_spaces_do_not_match()
    normalising_per_robot()
    pooling_helps()
    pooling_vs_data()
    position_coverage()
    new_object_kind()
    instruction_overlap()
    four_cases()
    cost_of_running()

    # 04_world-models.md
    one_step_job()
    training_transitions()
    one_step_error()
    learned_against_true_physics()
    pixels_to_latent()
    variance_vs_latent_size()
    what_is_lost()
    reading_the_gripper()
    rollout_vs_truth()
    error_vs_horizon()
    phase_path()
    more_data_does_not_fix_it()
    candidate_sequences()
    arithmetic_of_planning()
    more_candidates()
    replanning_rate()
    labelled_against_unlabelled()
    cost_of_predicting_pixels()
    simulator_against_learned()
    through_the_stop()
    energy_drift()
    plan_that_exploits_the_error()

    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
