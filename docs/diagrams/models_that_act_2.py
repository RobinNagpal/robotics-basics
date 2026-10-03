"""Generate the diagrams for the last two pages of docs/06_neural-networks/12_models-that-act/.

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
  percentile normalisation, the uniform and quantile binning, the measured
  quantisation error, the integrated drift, the discrete cosine transform
  compression, and the flow-matching action head, which is a small network
  trained in NumPy by gradient descent.
* The catastrophic-forgetting and cross-embodiment experiments are small
  networks trained in NumPy on simulated data, with the two-link arm geometry
  and its Jacobian worked out exactly.
* The world-model page uses one simulated system: a one-joint arm (a pendulum)
  with viscous damping, a torque input and a hard stop at 0.9 radians. The
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
