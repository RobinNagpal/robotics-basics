"""Generate the diagrams for the first two pages of docs/06_neural-networks/12_models-that-act/.

    01_behaviour-cloning-and-action-chunks.md
        -> images/models-that-act/behaviour-cloning-and-action-chunks/
    02_diffusion-and-flow-policies.md
        -> images/models-that-act/diffusion-and-flow-policies/

Run with:  pixi run python ../docs/diagrams/models_that_act_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script prints
them so that the two documents can quote the same values.

The data is simulated. A made-up teleoperated reach is generated with a seeded
random generator: the demonstrator starts near one place, aims at a goal that
moves a little from take to take, swings the gripper out on an arc of varying
size, varies the speed, and shakes slightly. A second simulated task puts a box
between the start and the goal, and half the demonstrations go above it while
half go below. The arm itself is simulated as a point that moves by the commanded
step plus a small servo error.

The methods run on that simulated data are real and written in NumPy: a
nearest-neighbour chunk policy, a squared-error multilayer network trained with
Adam, a denoising diffusion policy with a cosine noise schedule and DDIM
sampling, and a flow-matching policy integrated with Euler steps. The timing
tables are arithmetic on stated per-pass costs, which the script states and
prints rather than measuring on any particular machine.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'models-that-act'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies
CACHE: pathlib.Path | None = None       # set by --cache <file> to keep trained weights

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

BC_DOC: str = 'behaviour-cloning-and-action-chunks'
DF_DOC: str = 'diffusion-and-flow-policies'

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


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str, colour: str,
         fontsize: float = 9.5, alpha: float = 0.20, weight: str = 'normal') -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=colour, alpha=alpha,
                               edgecolor=colour, lw=1.5, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fontsize,
            color=INK, zorder=3, weight=weight, linespacing=1.45)


def _arrow(ax: Axes, xy_from: tuple[float, float], xy_to: tuple[float, float],
           colour: str = INK, lw: float = 1.6) -> None:
    ax.annotate('', xy=xy_to, xytext=xy_from,
                arrowprops=dict(arrowstyle='-|>', color=colour, lw=lw,
                                shrinkA=2, shrinkB=2))


def _sigmoid(x: Arr) -> Arr:
    out = np.empty_like(x)
    pos = x >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    e = np.exp(x[~pos])
    out[~pos] = e / (1.0 + e)
    return out


def _silu(x: Arr) -> Arr:
    return x * _sigmoid(x)


def _dsilu(x: Arr) -> Arr:
    s = _sigmoid(x)
    return s * (1.0 + x * (1.0 - s))


# ==========================================================================
# PAGE 1 --- the simulated teleoperated arm
# ==========================================================================

RATE: float = 30.0                 # recording rate in hertz
DT: float = 1.0 / RATE
EP_SECONDS: float = 12.0           # one teleoperated episode
EP_STEPS: int = int(EP_SECONDS * RATE)
N_EPISODES: int = 50
CAM_H, CAM_W, CAM_C = 480, 640, 3
N_CAMS: int = 2

JOINT_NAMES: list[str] = ['base', 'shoulder', 'elbow', 'wrist 1', 'wrist 2', 'wrist 3']
JOINT_LO: Arr = np.array([-170.0, -120.0, -170.0, -120.0, -170.0, -175.0])
JOINT_HI: Arr = np.array([170.0, 120.0, 170.0, 120.0, 170.0, 175.0])

REACH_STEPS: int = 120             # four seconds of reaching at 30 hertz
HORIZON: int = 48                  # how many future steps the policy works out


def _tremor(rng: np.random.Generator, n: int, amp: float) -> Arr:
    """A slow shake, the kind a person's hand puts into a demonstration."""
    t = np.arange(n) / max(n - 1, 1)
    out = np.zeros((n, 2))
    for j in range(2):
        for f, a in ((1.7, 1.0), (4.3, 0.45)):
            out[:, j] += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return out * amp


def _profile(n: int, g: float) -> Arr:
    tau = (np.arange(n + 1) / n) ** g
    return 3 * tau ** 2 - 2 * tau ** 3


def reach_path(start: Arr, goal: Arr, arc: float, g: float, n: int = REACH_STEPS) -> Arr:
    """The path a demonstrator draws: a smooth swing from start to goal."""
    u = _profile(n, g)
    d = goal - start
    perp = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    return start + u[:, None] * d + arc * np.sin(np.pi * u)[:, None] * perp


def reach_demo(rng: np.random.Generator, n: int = REACH_STEPS
               ) -> tuple[Arr, Arr, Arr, Arr]:
    """One simulated demonstration: path, steps, what the policy sees, the goal."""
    start = np.array([0.0, 0.0]) + rng.normal(0, 0.6, 2)
    goal = np.array([40.0 + rng.normal(0, 1.5), rng.normal(0, 4.0)])
    pos = reach_path(start, goal, rng.normal(6.0, 1.2), rng.normal(1.0, 0.09), n)
    pos = pos + _tremor(rng, n + 1, 0.30)
    acts = np.diff(pos, axis=0)
    obs = np.concatenate([pos[:-1], np.tile(goal, (n, 1))], axis=1)
    return pos, acts, obs, goal


class ChunkStore:
    """Every recorded moment of a demonstration set, with the block that follows it."""

    def __init__(self, n_demos: int, seed: int, horizon: int = HORIZON) -> None:
        rng = np.random.default_rng(seed)
        obs_all, chunk_all = [], []
        for _ in range(n_demos):
            _pos, acts, obs, _goal = reach_demo(rng)
            keep = len(acts) - horizon
            idx = np.arange(keep)
            obs_all.append(obs[:keep])
            chunk_all.append(np.stack([acts[i:i + horizon] for i in idx]))
        self.obs: Arr = np.concatenate(obs_all)
        self.chunks: Arr = np.concatenate(chunk_all)
        self.horizon = horizon
        self.n_demos = n_demos


class KnnChunkPolicy:
    """The policy: find the most similar recorded moments and copy what happened next."""

    def __init__(self, store: ChunkStore, k: int = 5) -> None:
        self.obs = store.obs
        self.chunks = store.chunks
        self.k = k
        self._sq = (self.obs ** 2).sum(1)

    def _d2(self, q: Arr) -> Arr:
        return self._sq[None, :] - 2.0 * q @ self.obs.T + (q ** 2).sum(1)[:, None]

    def __call__(self, q: Arr) -> Arr:
        out = np.zeros((len(q), self.chunks.shape[1], 2))
        for a in range(0, len(q), 256):
            b = q[a:a + 256]
            d2 = self._d2(b)
            idx = np.argpartition(d2, self.k, axis=1)[:, :self.k]
            dd = np.sqrt(np.maximum(np.take_along_axis(d2, idx, 1), 0.0))
            w = 1.0 / (dd + 0.08)
            w = w / w.sum(1, keepdims=True)
            out[a:a + 256] = (self.chunks[idx] * w[:, :, None, None]).sum(1)
        return out

    def nearest_distance(self, q: Arr) -> Arr:
        out = np.zeros(len(q))
        for a in range(0, len(q), 256):
            out[a:a + 256] = np.sqrt(np.maximum(self._d2(q[a:a + 256]).min(1), 0.0))
        return out


def one_step_error(policy: KnnChunkPolicy, seed: int = 777, n_demos: int = 25) -> float:
    """The policy's error on demonstrations it was not fitted to, in cm for one step."""
    rng = np.random.default_rng(seed)
    qs, ys = [], []
    for _ in range(n_demos):
        _pos, acts, obs, _goal = reach_demo(rng)
        keep = len(acts) - HORIZON
        qs.append(obs[:keep])
        ys.append(acts[:keep])
    q = np.concatenate(qs)
    y = np.concatenate(ys)
    pred = policy(q)[:, 0]
    return float(np.linalg.norm(pred - y, axis=1).mean())


def heldout_gap(policy: KnnChunkPolicy, seed: int = 778, n_demos: int = 10) -> float:
    """How far a fresh demonstration's own moments are from the recorded ones."""
    rng = np.random.default_rng(seed)
    qs = []
    for _ in range(n_demos):
        _pos, acts, obs, _goal = reach_demo(rng)
        qs.append(obs[:len(acts) - HORIZON])
    return float(policy.nearest_distance(np.concatenate(qs)).mean())


OBS_SIGMA: float = 0.15            # the camera's error in reading a position, in cm


def rollout(policy: KnnChunkPolicy, starts: Arr, goals: Arr, execute: int,
            rng: np.random.Generator, steps: int = REACH_STEPS, sigma: float = 0.02,
            shift_at: int | None = None, new_goals: Arr | None = None,
            obs_sigma: float = OBS_SIGMA) -> tuple[Arr, Arr, Arr]:
    """Run the policy on the simulated arm. Returns the path, the commands and
    the distance from each visited state to the nearest recorded one."""
    b = len(starts)
    pos = starts.copy()
    goal = goals.copy()
    path = np.zeros((steps + 1, b, 2))
    cmds = np.zeros((steps, b, 2))
    gap = np.zeros((steps, b))
    path[0] = pos
    t = 0
    while t < steps:
        q = np.concatenate([pos, goal], axis=1) + rng.normal(0, obs_sigma, (b, 4))
        block = policy(q)
        gap[t] = policy.nearest_distance(q)
        for i in range(min(execute, steps - t)):
            cmds[t] = block[:, min(i, block.shape[1] - 1)]
            pos = pos + cmds[t] + rng.normal(0, sigma, (b, 2))
            t += 1
            path[t] = pos
            if shift_at is not None and t == shift_at and new_goals is not None:
                goal = new_goals.copy()
    return path, cmds, gap


def reference_paths(starts: Arr, goals: Arr, steps: int = REACH_STEPS) -> Arr:
    """The path an average demonstrator would draw from the same start to the same goal."""
    return np.stack([reach_path(s, g, 6.0, 1.0, steps) for s, g in zip(starts, goals)], axis=1)


def test_starts(n: int, seed: int) -> tuple[Arr, Arr]:
    rng = np.random.default_rng(seed)
    starts = np.array([0.0, 0.0]) + rng.normal(0, 0.6, (n, 2))
    goals = np.column_stack([40.0 + rng.normal(0, 1.5, n), rng.normal(0, 4.0, n)])
    return starts, goals


class ReachSim:
    """Everything page one measures on the simulated reach, worked out once."""

    def __init__(self) -> None:
        self.store = ChunkStore(100, seed=11)
        self.policy = KnnChunkPolicy(self.store)
        self.starts, self.goals = test_starts(40, seed=303)
        self.ref = reference_paths(self.starts, self.goals)
        self.runs: dict[int, tuple[Arr, Arr, Arr]] = {}
        for c in (1, 2, 4, 8, 16, 32, 48):
            self.runs[c] = rollout(self.policy, self.starts, self.goals, c,
                                   np.random.default_rng(900 + c))

    def error(self, c: int) -> Arr:
        path = self.runs[c][0]
        return np.linalg.norm(path - self.ref, axis=2).mean(1)


SIM: ReachSim | None = None


def _sim() -> ReachSim:
    global SIM
    if SIM is None:
        SIM = ReachSim()
    return SIM


# --------------------------------------------------------------------------
# section 1 --- what the output is
# --------------------------------------------------------------------------

def teleop_episode(seed: int = 7) -> tuple[Arr, Arr]:
    """A simulated 12-second episode: six joint angles in degrees and a gripper."""
    rng = np.random.default_rng(seed)
    t = np.arange(EP_STEPS) * DT
    ang = np.zeros((EP_STEPS, 6))
    for j in range(6):
        span = 0.22 * (JOINT_HI[j] - JOINT_LO[j]) / 2.0
        for f, a in ((0.11, 1.0), (0.27, 0.45), (0.6, 0.15)):
            ang[:, j] += a * span * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    grip = np.where(t < 5.0, 1.0, np.where(t < 5.6, 1.0 - (t - 5.0) / 0.6, 0.0))
    return ang, grip


def action_vector() -> None:
    ang, grip = teleop_episode()
    k = 150
    raw = ang[k]
    norm = 2.0 * (raw - JOINT_LO) / (JOINT_HI - JOINT_LO) - 1.0
    print('[bc] action vector at step %d (t = %.1f s):' % (k, k * DT))
    for nm, lo, hi, r, nv in zip(JOINT_NAMES, JOINT_LO, JOINT_HI, raw, norm):
        print(f'[bc]   {nm:9s} limits {lo:+.0f} to {hi:+.0f} deg, reading {r:+7.2f} deg'
              f' -> {nv:+.3f}')
    print(f'[bc]   gripper   0 closed to 1 open, reading {grip[k]:.2f} -> '
          f'{2 * grip[k] - 1:+.3f}')
    print(f'[bc] so one action is {len(JOINT_NAMES) + 1} numbers, each between -1 and +1')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.15, 1]})
    ax = axes[0]
    _plain(ax)
    y = np.arange(6)[::-1]
    ax.barh(y, JOINT_HI - JOINT_LO, left=JOINT_LO, height=0.45, color=LINK_PALE,
            edgecolor=LINK, lw=1.0)
    ax.plot(raw, y, 'o', color=GRIP, ms=9, zorder=4)
    for yy, r in zip(y, raw):
        ax.text(r, yy + 0.32, f'{r:+.1f}', ha='center', fontsize=9, color=GRIP)
    ax.set_yticks(y)
    ax.set_yticklabels(JOINT_NAMES, fontsize=9.5)
    ax.set_xlabel('joint angle in degrees, with the bar showing the joint\'s whole range',
                  fontsize=9.5)
    ax.set_xlim(-190, 190)
    ax.set_ylim(-0.7, 5.8)
    ax.set_title('What the arm reads: six angles inside their limits', fontsize=11.5,
                 weight='bold')

    ax = axes[1]
    _plain(ax)
    vals = np.append(norm, 2 * grip[k] - 1)
    names = JOINT_NAMES + ['gripper']
    y2 = np.arange(7)[::-1]
    cols = [LINK] * 6 + [SLIDE]
    ax.barh(y2, vals, height=0.5, color=cols, alpha=0.85)
    for yy, v in zip(y2, vals):
        off = 0.06 if v >= 0 else -0.06
        ax.text(v + off, yy, f'{v:+.3f}', va='center', fontsize=9.2, color=INK,
                ha='left' if v >= 0 else 'right')
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_yticks(y2)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.7, 6.8)
    ax.set_xlabel('the same reading rescaled to run from -1 to +1', fontsize=9.5)
    ax.set_title('What the policy puts out: seven numbers', fontsize=11.5, weight='bold')
    fig.suptitle(f'One action, at t = {k * DT:.1f} s of a simulated episode',
                 fontsize=13, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'action-vector.svg')


def control_loop() -> None:
    period = 1000.0 / RATE
    parts = [('camera picture ready', 8.0, WRIST),
             ('run the network', 12.0, PURPLE),
             ('send to the joints', 1.0, SLIDE)]
    used = sum(p[1] for p in parts)
    slack = period - used
    print(f'[bc] control loop at {RATE:.0f} Hz: period {period:.2f} ms, '
          f'work {used:.1f} ms, slack {slack:.2f} ms')
    print(f'[bc] a loop at 10 Hz would have {100.0 - used:.1f} ms of slack, '
          f'and one at 50 Hz would be short by {used - 20.0:.1f} ms')

    fig, ax = plt.subplots(figsize=(11.6, 3.9), facecolor='white')
    ax.axis('off')
    ax.set_xlim(-2, 104)
    ax.set_ylim(-2.3, 3.4)
    for row, (rate, label) in enumerate(((50.0, 'a loop at 50 Hz'), (RATE, 'a loop at 30 Hz'),
                                         (10.0, 'a loop at 10 Hz'))):
        p = 1000.0 / rate
        yb = 2.0 - row * 1.25
        x = 0.0
        for nm, ms, col in parts:
            _box(ax, x, yb, ms, 0.62, '', col, alpha=0.75)
            x += ms
        if p > used:
            _box(ax, used, yb, p - used, 0.62, f'waiting {p - used:.1f} ms', GRID,
                 fontsize=9, alpha=0.6)
        else:
            ax.plot([p, p], [yb - 0.12, yb + 0.74], color=GRIP, lw=2.2)
            ax.text(used + 1.5, yb + 0.31, f'{used - p:.1f} ms too late', fontsize=9.2,
                    color=GRIP, va='center')
        ax.text(-1.0, yb + 0.31, label, ha='right', va='center', fontsize=10)
        ax.plot([p, p], [yb - 0.1, yb + 0.72], color=INK, lw=1.4, ls='--')
        ax.text(p, yb + 0.82, f'next command due at {p:.1f} ms', fontsize=8.6,
                ha='center', color=INK)
    x = 0.0
    for i, (nm, ms, col) in enumerate(parts):
        ty = -0.72 - 0.42 * i
        ax.plot([x + ms / 2, x + ms / 2], [-0.1, ty + 0.1], color=col, lw=0.9)
        ax.text(x + ms / 2, ty, f'{nm}, {ms:.0f} ms', ha='center', va='top',
                fontsize=9.2, color=col)
        x += ms
    ax.set_title('The same 21 ms of work inside three control periods',
                 fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'the-control-loop.svg')


def absolute_versus_delta() -> None:
    ang, _grip = teleop_episode()
    el = ang[:, 2]
    d = np.diff(el)
    t = np.arange(EP_STEPS) * DT
    print(f'[bc] elbow over 12 s: lowest {el.min():+.2f} deg, highest {el.max():+.2f} deg, '
          f'range {el.max() - el.min():.2f} deg')
    print(f'[bc] step to step change: largest {np.abs(d).max():.3f} deg, '
          f'average size {np.abs(d).mean():.3f} deg, '
          f'ratio of ranges {(el.max() - el.min()) / (d.max() - d.min()):.1f}')

    fig, axes = plt.subplots(2, 1, figsize=(11.2, 6.0), facecolor='white', sharex=True)
    ax = axes[0]
    _plain(ax)
    ax.plot(t, el, color=LINK, lw=2.0)
    ax.axhline(el.max(), color=MUTED, ls=':', lw=1.0)
    ax.axhline(el.min(), color=MUTED, ls=':', lw=1.0)
    ax.set_ylabel('elbow angle (degrees)', fontsize=9.5)
    ax.set_title(f'Writing the action as a place to go to: the range is '
                 f'{el.max() - el.min():.1f} degrees', fontsize=11.5, weight='bold')
    ax.text(0.99, 0.05, f'highest {el.max():+.1f}, lowest {el.min():+.1f}',
            fontsize=9.2, color=MUTED, transform=ax.transAxes, ha='right')
    ax = axes[1]
    _plain(ax)
    ax.plot(t[1:], d, color=WRIST, lw=1.4)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_ylabel('change since the last step (degrees)', fontsize=9.5)
    ax.set_xlabel('time through the episode (seconds)', fontsize=9.5)
    ax.set_title(f'Writing it as a change instead: the range is only '
                 f'{d.max() - d.min():.2f} degrees, so the numbers have to be rescaled harder',
                 fontsize=11.5, weight='bold')
    ax.text(0.99, 0.05, f'largest single step {np.abs(d).max():.3f} degrees',
            fontsize=9.2, color=MUTED, transform=ax.transAxes, ha='right')
    fig.tight_layout()
    _save(fig, BC_DOC, 'absolute-versus-delta.svg')


# --------------------------------------------------------------------------
# section 2 --- the shape of the data
# --------------------------------------------------------------------------

def one_example() -> None:
    per_cam = CAM_H * CAM_W * CAM_C
    cams = per_cam * N_CAMS
    state = 7
    action = 7
    total = cams + state + action
    print(f'[bc] one camera frame is {CAM_H} x {CAM_W} x {CAM_C} = {per_cam:,} numbers')
    print(f'[bc] one example: {N_CAMS} frames = {cams:,} numbers, state {state}, '
          f'label {action}, total {total:,}')
    print(f'[bc] the pictures are {100.0 * cams / total:.3f} per cent of the numbers')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.7), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    _box(ax, 0.2, 4.0, 3.2, 1.6,
         f'overhead camera\n{CAM_H} x {CAM_W} x {CAM_C}\n= {per_cam:,} numbers', WRIST,
         fontsize=9.2)
    _box(ax, 0.2, 2.1, 3.2, 1.6,
         f'wrist camera\n{CAM_H} x {CAM_W} x {CAM_C}\n= {per_cam:,} numbers', WRIST,
         fontsize=9.2)
    _box(ax, 0.2, 0.5, 3.2, 1.3, f'joint angles and gripper\n{state} numbers', TEAL,
         fontsize=9.2)
    _box(ax, 4.3, 2.0, 2.2, 2.0, f'the question\n{cams + state:,}\nnumbers', LINK,
         fontsize=9.6, weight='bold')
    _box(ax, 7.3, 2.4, 2.5, 1.2, f'the answer\n{action} numbers', SLIDE, fontsize=9.6,
         weight='bold')
    for y0 in (4.8, 2.9, 1.15):
        _arrow(ax, (3.45, y0), (4.25, 3.0), MUTED)
    _arrow(ax, (6.55, 3.0), (7.25, 3.0), INK)
    ax.text(6.9, 4.5, 'what the person\ndid next', ha='center', fontsize=8.8, color=SLIDE)
    ax.plot([6.9, 6.9], [3.15, 4.1], color=SLIDE, lw=0.9)
    ax.set_title('One training example from a teleoperated arm', fontsize=11.5,
                 weight='bold')

    ax = axes[1]
    _plain(ax)
    names = ['two camera\nframes', 'joint angles\nand gripper', 'the label\n(one action)']
    vals = [cams, state, action]
    ax.bar(np.arange(3), vals, color=[WRIST, TEAL, SLIDE], width=0.6)
    ax.set_yscale('log')
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(names, fontsize=9.2)
    ax.set_ylim(1, cams * 9)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.5, f'{v:,}', ha='center', fontsize=9.5, color=INK)
    ax.set_ylabel('numbers in one example (log scale)', fontsize=9.5)
    ax.set_title(f'The pictures are {100.0 * cams / total:.4f} per cent of it',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'one-example.svg')


def one_episode() -> None:
    ang, grip = teleop_episode()
    t = np.arange(EP_STEPS) * DT
    print(f'[bc] one episode: {EP_SECONDS:.0f} s at {RATE:.0f} Hz = {EP_STEPS} steps, '
          f'so {EP_STEPS} examples from one episode')
    print(f'[bc] {N_EPISODES} episodes = {N_EPISODES * EP_STEPS:,} examples and '
          f'{N_EPISODES * EP_SECONDS / 60.0:.0f} minutes of arm movement')

    fig, axes = plt.subplots(2, 1, figsize=(11.4, 6.4), facecolor='white',
                             gridspec_kw={'height_ratios': [1.5, 1]})
    ax = axes[0]
    _plain(ax)
    for j in range(6):
        ax.plot(t, ang[:, j], lw=1.6, label=JOINT_NAMES[j])
    ax.set_ylabel('joint angle (degrees)', fontsize=9.5)
    ax.set_xlim(0, EP_SECONDS)
    ax.legend(fontsize=8.4, frameon=False, ncol=6, loc='upper center',
              bbox_to_anchor=(0.5, 1.16))
    ax.set_title(f'One simulated episode: {EP_SECONDS:.0f} seconds recorded at '
                 f'{RATE:.0f} readings a second', fontsize=11.5, weight='bold', pad=26)
    ax = axes[1]
    _plain(ax)
    ax.plot(t, grip, color=SLIDE, lw=2.0)
    ax.fill_between(t, 0, grip, color=SLIDE, alpha=0.15)
    ax.set_ylim(-0.12, 1.2)
    ax.set_ylabel('gripper (1 open, 0 shut)', fontsize=9.5)
    ax.set_xlabel('time through the episode (seconds)', fontsize=9.5)
    ax.set_xlim(0, EP_SECONDS)
    for s in (0, 3, 6, 9, 12):
        ax.axvline(s, color=GRID, lw=0.8)
    ax.text(0.15, 1.05, f'every one of the {EP_STEPS} readings is one example, and its '
                        f'label is the reading the person made next',
            fontsize=9.2, color=MUTED)
    fig.tight_layout()
    _save(fig, BC_DOC, 'one-episode.svg')


def dataset_size() -> None:
    per_cam = CAM_H * CAM_W * CAM_C
    raw_step = per_cam * N_CAMS
    raw_ep = raw_step * EP_STEPS
    raw_set = raw_ep * N_EPISODES
    ratio = 40.0
    print(f'[bc] raw bytes: one step {raw_step:,}, one episode {raw_ep / 1e6:.1f} MB, '
          f'{N_EPISODES} episodes {raw_set / 1e9:.2f} GB')
    print(f'[bc] stored as video at {ratio:.0f} to 1: {raw_set / 1e9 / ratio:.3f} GB, '
          f'and the {N_EPISODES * EP_STEPS * 14:,} action and state numbers are '
          f'{N_EPISODES * EP_STEPS * 14 * 4 / 1e6:.2f} MB as 4-byte numbers')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5), facecolor='white')
    ax = axes[0]
    _plain(ax)
    eps = np.array([1, 10, 50, 200, 1000])
    ax.plot(eps, eps * EP_STEPS, 'o-', color=LINK, lw=2.0, ms=7)
    for e in eps:
        ax.text(e, e * EP_STEPS * 1.5, f'{e * EP_STEPS:,}', ha='center', fontsize=9,
                color=LINK)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(eps)
    ax.set_xticklabels([str(e) for e in eps])
    ax.set_ylim(200, 1000 * EP_STEPS * 6)
    ax.set_xlabel('episodes recorded (log scale)', fontsize=9.5)
    ax.set_ylabel('training examples (log scale)', fontsize=9.5)
    ax.set_title(f'Each episode gives {EP_STEPS} examples', fontsize=11.5, weight='bold')

    ax = axes[1]
    _plain(ax)
    labels = ['camera frames\nkept raw', 'camera frames\nas video',
              'joint and action\nnumbers']
    vals = [raw_set / 1e9, raw_set / 1e9 / ratio, N_EPISODES * EP_STEPS * 14 * 4 / 1e9]
    ax.bar(np.arange(3), vals, color=[GRIP, WRIST, TEAL], width=0.6)
    ax.set_yscale('log')
    for i, v in enumerate(vals):
        txt = f'{v:.2f} GB' if v >= 0.01 else f'{v * 1000:.1f} MB'
        ax.text(i, v * 1.6, txt, ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(labels, fontsize=9.2)
    ax.set_ylim(2e-4, vals[0] * 12)
    ax.set_ylabel('gigabytes for 50 episodes (log scale)', fontsize=9.5)
    ax.set_title(f'Where the {raw_set / 1e9:.1f} GB sits, with video at '
                 f'{ratio:.0f} to 1', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'dataset-size.svg')


def hours_of_a_day() -> None:
    motion, reset, check = EP_SECONDS, 20.0, 8.0
    per_take = motion + reset + check
    keep = 5.0 / 6.0
    takes = N_EPISODES / keep
    setup = 10.0 * 60.0
    total = takes * per_take + setup
    examples = N_EPISODES * EP_STEPS
    print(f'[bc] one take is {per_take:.0f} s ({motion:.0f} moving, {reset:.0f} resetting, '
          f'{check:.0f} checking)')
    print(f'[bc] keeping 5 takes in 6 means {takes:.0f} takes for {N_EPISODES} episodes, '
          f'which is {takes * per_take / 60.0:.0f} min plus {setup / 60.0:.0f} min of setup '
          f'= {total / 60.0:.0f} min')
    print(f'[bc] that is {examples:,} examples per {total / 3600.0:.2f} human hours = '
          f'{examples / (total / 3600.0):,.0f} examples an hour')
    for n in (50, 200, 1000, 5000):
        tk = n / keep
        tt = tk * per_take + setup
        print(f'[bc]   {n} episodes -> {tt / 3600.0:.1f} human hours, {n * EP_STEPS:,} examples')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    parts = [('moving the arm', motion * takes / 60.0, LINK),
             ('resetting the scene', reset * takes / 60.0, WRIST),
             ('checking and saving', check * takes / 60.0, TEAL),
             ('setting up', setup / 60.0, MUTED)]
    left = 0.0
    for i, (nm, v, col) in enumerate(parts):
        ax.barh([0], [v], left=[left], color=col, height=0.5, alpha=0.85)
        ty = 0.42 + 0.30 * (i % 2)
        ax.plot([left + v / 2, left + v / 2], [0.26, ty - 0.03], color=col, lw=0.9)
        ax.text(left + v / 2, ty, f'{nm}, {v:.0f} min', ha='center', fontsize=9.2,
                color=col, va='bottom')
        left += v
    ax.set_xlim(0, total / 60.0 * 1.04)
    ax.set_ylim(-0.6, 1.25)
    ax.set_yticks([])
    ax.set_xlabel('minutes of one person\'s day', fontsize=9.5)
    ax.set_title(f'{N_EPISODES} usable episodes cost {total / 60.0:.0f} minutes, and only '
                 f'{motion * takes / 60.0:.0f} of them are arm movement',
                 fontsize=11.2, weight='bold')

    ax = axes[1]
    _plain(ax)
    ns = np.array([50, 200, 1000, 5000])
    hrs = (ns / keep * per_take + setup) / 3600.0
    ax.plot(ns * EP_STEPS, hrs, 'o-', color=GRIP, lw=2.0, ms=7)
    for i, (n, h) in enumerate(zip(ns, hrs)):
        ha = 'right' if i == len(ns) - 1 else 'left'
        off = 0.82 if i == len(ns) - 1 else 1.22
        ax.text(n * EP_STEPS * off, h + hrs[-1] * 0.07,
                f'{n} episodes\n{h:.1f} hours', fontsize=9, color=INK, va='bottom',
                ha=ha)
    ax.set_xscale('log')
    ax.set_xlim(1.2e4, 4e6)
    ax.set_ylim(0, hrs[-1] * 1.3)
    ax.set_xlabel('training examples (log scale)', fontsize=9.5)
    ax.set_ylabel('hours of a person\'s time', fontsize=9.5)
    ax.set_title('Robot data is bought in hours, not downloads', fontsize=11.5,
                 weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'hours-of-a-day.svg')


# --------------------------------------------------------------------------
# section 3 --- drift and covariate shift
# --------------------------------------------------------------------------

def drift_paths() -> None:
    s = _sim()
    rng = np.random.default_rng(5)
    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _plain(ax)
    demo_rng = np.random.default_rng(11)
    for i in range(14):
        pos, _a, _o, _g = reach_demo(demo_rng)
        ax.plot(pos[:, 0], pos[:, 1], color=LINK, lw=1.0, alpha=0.5,
                label='demonstrations' if i == 0 else None)
    path = s.runs[1][0]
    err = np.linalg.norm(path - s.ref, axis=2)
    worst = int(np.argsort(err[-1])[-1])
    typ = int(np.argsort(err[-1])[len(err[-1]) // 2])
    for idx, col, nm in ((typ, WRIST, 'a typical run of the policy'),
                         (worst, GRIP, 'the worst of 40 runs')):
        ax.plot(path[:, idx, 0], path[:, idx, 1], color=col, lw=2.4, label=nm)
        ax.plot(s.ref[:, idx, 0], s.ref[:, idx, 1], color=col, lw=1.2, ls='--')
        ax.plot(s.goals[idx, 0], s.goals[idx, 1], '*', color=col, ms=15)
        ax.annotate(f'{err[-1, idx]:.1f} cm out',
                    xy=(path[-1, idx, 0], path[-1, idx, 1]),
                    xytext=(path[-1, idx, 0] - 11, path[-1, idx, 1] + np.sign(
                        path[-1, idx, 1] - s.goals[idx, 1]) * 3.0),
                    fontsize=9.5, color=col,
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=1.2))
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title('Deciding one step at a time: the dashed line is where the run should '
                 'have gone, the star is the goal', fontsize=11.8, weight='bold')
    print(f'[bc] one-step policy on 40 runs: average final miss '
          f'{err[-1].mean():.2f} cm, worst {err[-1].max():.2f} cm, '
          f'best {err[-1].min():.2f} cm')
    fig.tight_layout()
    _save(fig, BC_DOC, 'drift-paths.svg')


def error_over_time() -> None:
    s = _sim()
    t = np.arange(REACH_STEPS + 1) * DT
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), facecolor='white',
                             gridspec_kw={'width_ratios': [1.4, 1]})
    ax = axes[0]
    _plain(ax)
    err = s.error(1)
    ax.plot(t, err, color=GRIP, lw=2.4, label='the policy, deciding one step at a time')
    walk = err[30] * np.sqrt(np.maximum(np.arange(REACH_STEPS + 1), 0) / 30.0)
    ax.plot(t, walk, color=MUTED, ls=':', lw=1.8,
            label='how far it would be if the mistakes were unrelated wobble')
    ax.fill_between(t, walk, err, color=GRIP, alpha=0.12)
    ax.annotate(f'{err[-1] - walk[-1]:.2f} cm more than wobble explains',
                xy=(t[-1], (err[-1] + walk[-1]) / 2),
                xytext=(1.5, err[-1] * 0.72), fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.2))
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, err[-1] * 1.2)
    ax.set_xlabel('time through the reach (seconds)', fontsize=9.5)
    ax.set_ylabel('average distance from where it should be (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper left')
    ax.set_title('The error never comes back, and it grows faster than chance',
                 fontsize=11.5, weight='bold')
    print(f'[bc] one-step drift: 1 s {err[30]:.2f} cm, 2 s {err[60]:.2f} cm, '
          f'3 s {err[90]:.2f} cm, 4 s {err[-1]:.2f} cm; unrelated wobble would give '
          f'{walk[-1]:.2f} cm')

    ax = axes[1]
    _plain(ax)
    vals, names = [], []
    for sigma in (0.0, 0.02, 0.06):
        path, _c, _g = rollout(s.policy, s.starts, s.goals, 1,
                               np.random.default_rng(42), sigma=sigma)
        v = np.linalg.norm(path - s.ref, axis=2).mean(1)[-1]
        vals.append(v)
        names.append(f'{sigma:.2f}')
        print(f'[bc] servo error {sigma:.2f} cm a step -> final drift {v:.2f} cm')
    ax.bar(np.arange(3), vals, color=[LINK, WRIST, GRIP], width=0.55, alpha=0.9)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.02, f'{v:.2f} cm', ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(['perfect\njoints', '0.02 cm\na step', '0.06 cm\na step'],
                       fontsize=9.2)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_xlabel('how much the joints themselves get wrong', fontsize=9.5)
    ax.set_ylabel('distance from where it should be after 4 s (cm)', fontsize=9.5)
    ax.set_title('Perfect joints barely help: the drift is the model\'s',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'error-over-time.svg')


def more_demos() -> None:
    t = np.arange(REACH_STEPS + 1) * DT
    starts, goals = test_starts(150, seed=303)
    ref = reference_paths(starts, goals)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), facecolor='white')
    finals, steps_err = [], []
    sizes = (5, 25, 100, 400)
    for n, col in zip(sizes, (GRIP, WRIST, LINK, PURPLE)):
        store = ChunkStore(n, seed=11)
        pol = KnnChunkPolicy(store)
        errs = []
        for sd in (42, 43, 44):
            path, _c, _g = rollout(pol, starts, goals, 1, np.random.default_rng(sd))
            errs.append(np.linalg.norm(path - ref, axis=2).mean(1))
        err = np.mean(errs, axis=0)
        axes[0].plot(t, err, color=col, lw=2.2, label=f'{n} demonstrations')
        finals.append(err[-1])
        se = one_step_error(pol)
        steps_err.append(se)
        print(f'[bc] {n:4d} demonstrations ({store.obs.shape[0]:,} recorded moments): '
              f'one-step error on fresh demonstrations {se * 10:.3f} mm, '
              f'drift after 1 s {err[30]:.2f} cm, after 4 s {err[-1]:.2f} cm')
    _plain(axes[0])
    axes[0].set_xlabel('time through the reach (seconds)', fontsize=9.5)
    axes[0].set_ylabel('average distance from where it should be (cm)', fontsize=9.5)
    axes[0].legend(fontsize=9.2, frameon=False, loc='upper left')
    axes[0].set_xlim(0, t[-1])
    axes[0].set_ylim(0, max(finals) * 1.2)
    axes[0].set_title('Eighty times the data, and the same climbing shape',
                      fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(sizes, [v * 10 for v in steps_err], 'o-', color=LINK, lw=2.2, ms=7)
    for n, v in zip(sizes, steps_err):
        ax.text(n, v * 10 * 1.06, f'{v * 10:.3f} mm', ha='center', fontsize=9,
                color=LINK, va='bottom')
    ax.set_xscale('log')
    ax.set_xticks(list(sizes))
    ax.set_xticklabels([str(n) for n in sizes])
    ax.set_ylim(0, max(steps_err) * 10 * 1.3)
    ax.set_xlabel('demonstrations in the training set (log scale)', fontsize=9.5)
    ax.set_ylabel('error of one predicted step (mm)', fontsize=9.5, color=LINK)
    ax2 = ax.twinx()
    ax2.plot(sizes, finals, 's--', color=GRIP, lw=2.0, ms=7)
    for n, v in zip(sizes, finals):
        ax2.text(n, v * 0.90, f'{v:.2f} cm', ha='center', fontsize=9, color=GRIP,
                 va='top')
    ax2.set_ylim(0, max(finals) * 1.3)
    ax2.set_ylabel('distance from where it should be after 4 s (cm)', fontsize=9.5,
                   color=GRIP)
    ax2.tick_params(labelsize=9.5, colors=GRIP)
    ax.set_title(f'One step\'s error falls by {100 * (1 - steps_err[-1] / steps_err[0]):.0f} '
                 f'per cent, the drift by {100 * (1 - finals[-1] / finals[0]):.0f} per cent',
                 fontsize=11.0, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'more-demos.svg')


def unseen_inputs() -> None:
    s = _sim()
    t = np.arange(REACH_STEPS) * DT
    path, _c, gap = s.runs[1]
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    keep = s.store.obs
    sub = np.random.default_rng(1).choice(len(keep), 2500, replace=False)
    ax.plot(keep[sub, 0], keep[sub, 1], '.', color=LINK_PALE, ms=2.6,
            label='where the demonstrations went')
    worst = int(np.argmax(gap[-1]))
    sc = ax.scatter(path[:-1, worst, 0], path[:-1, worst, 1], c=gap[:, worst],
                    cmap='YlOrRd', s=22, vmin=0, zorder=4, edgecolors='none')
    cb = fig.colorbar(sc, ax=ax, fraction=0.04)
    cb.set_label('distance to the nearest\nrecorded moment (cm)', fontsize=8.6)
    cb.ax.tick_params(labelsize=8.4)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title('One run, coloured by how new its input was', fontsize=11.5,
                 weight='bold')
    ax = axes[1]
    _plain(ax)
    mean_gap = gap.mean(1)
    lo = np.percentile(gap, 10, axis=1)
    hi = np.percentile(gap, 90, axis=1)
    ax.fill_between(t, lo, hi, color=PURPLE, alpha=0.15)
    ax.plot(t, mean_gap, color=PURPLE, lw=2.4, label='average over 40 runs')
    held = heldout_gap(s.policy)
    ax.axhline(held, color=SLIDE, ls=':', lw=1.8,
               label=f'a fresh demonstration sits {held:.2f} cm from the nearest')
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, hi.max() * 1.15)
    ax.set_xlabel('time through the reach (seconds)', fontsize=9.5)
    ax.set_ylabel('distance to the nearest recorded moment (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper left')
    ax.set_title('Each question is less like anything the policy was fitted to',
                 fontsize=11.5, weight='bold')
    print(f'[bc] gap to the nearest recorded moment: at the start '
          f'{mean_gap[0]:.2f} cm, after 1 s {mean_gap[30]:.2f} cm, '
          f'after 4 s {mean_gap[-1]:.2f} cm, against {held:.2f} cm along a fresh '
          f'demonstration, so {mean_gap[-1] / held:.0f} times further out')
    fig.tight_layout()
    _save(fig, BC_DOC, 'unseen-inputs.svg')


# --------------------------------------------------------------------------
# section 4 --- action chunks
# --------------------------------------------------------------------------

def chunk_timeline() -> None:
    cs = (1, 4, 16, 48)
    print('[bc] decisions in a 4-second reach at 30 Hz:')
    for c in cs:
        print(f'[bc]   chunk of {c:2d} steps ({c * DT * 1000:6.1f} ms of motion): '
              f'{int(np.ceil(REACH_STEPS / c)):3d} decisions')
    fig, ax = plt.subplots(figsize=(11.6, 4.4), facecolor='white')
    ax.axis('off')
    ax.set_xlim(-0.6, REACH_STEPS * DT + 0.5)
    ax.set_ylim(-0.4, len(cs) * 1.0 + 0.3)
    for row, c in enumerate(cs):
        yb = (len(cs) - 1 - row) * 1.0
        n_dec = int(np.ceil(REACH_STEPS / c))
        t0 = 0.0
        for d in range(n_dec):
            width = min(c, REACH_STEPS - d * c) * DT
            col = LINK if d % 2 == 0 else TEAL
            ax.add_patch(plt.Rectangle((t0, yb), width, 0.46, facecolor=col, alpha=0.35,
                                       edgecolor=col, lw=0.8))
            if n_dec <= 8:
                ax.plot([t0], [yb + 0.6], 'v', color=INK, ms=6)
            t0 += width
        if n_dec > 8:
            ax.text(REACH_STEPS * DT / 2, yb + 0.62,
                    f'{n_dec} decisions, too many to draw', fontsize=9, color=INK,
                    ha='center')
        ax.text(-0.15, yb + 0.23, f'chunk of {c}', ha='right', va='center', fontsize=10)
        ax.text(REACH_STEPS * DT + 0.1, yb + 0.23, f'{n_dec} decisions', fontsize=9.5,
                color=INK, va='center')
    ax.plot([0, REACH_STEPS * DT], [-0.25, -0.25], color=INK, lw=1.2)
    for sec in range(5):
        ax.plot([sec, sec], [-0.32, -0.18], color=INK, lw=1.2)
        ax.text(sec, -0.42, f'{sec} s', ha='center', fontsize=9, color=INK)
    ax.set_title('One four-second reach, cut into decisions: a longer chunk means fewer '
                 'chances to be wrong', fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'chunk-timeline.svg')


def chunk_drift() -> None:
    s = _sim()
    t = np.arange(REACH_STEPS + 1) * DT
    fig, ax = plt.subplots(figsize=(11.0, 5.2), facecolor='white')
    _plain(ax)
    for c, col in zip((1, 4, 16, 48), (GRIP, WRIST, LINK, SLIDE)):
        err = s.error(c)
        ax.plot(t, err, color=col, lw=2.2,
                label=f'chunk of {c} ({int(np.ceil(REACH_STEPS / c))} decisions)')
        print(f'[bc] chunk of {c:2d}: error after 1 s {err[30]:.2f} cm, '
              f'after 4 s {err[-1]:.2f} cm')
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, s.error(1)[-1] * 1.12)
    ax.set_xlabel('time through the reach (seconds)', fontsize=9.5)
    ax.set_ylabel('average distance from where it should be (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper left')
    ax.set_title('The same policy, the same data, only the number of steps played per '
                 'decision changed', fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'chunk-drift.svg')


def chunk_smoothness() -> None:
    s = _sim()
    t = np.arange(1, REACH_STEPS) * DT
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1]})
    ax = axes[0]
    _plain(ax)
    jerks = {}
    for c, col in zip((1, 16), (GRIP, LINK)):
        cmds = s.runs[c][1]
        d = np.linalg.norm(np.diff(cmds, axis=0), axis=2).mean(1)
        jerks[c] = d
        ax.plot(t, d * 10.0, color=col, lw=1.6, label=f'chunk of {c}')
    ax.set_xlim(0, t[-1])
    ax.set_xlabel('time through the reach (seconds)', fontsize=9.5)
    ax.set_ylabel('change in the command from one step to the next (mm)', fontsize=9.5)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('One step at a time jitters all the way; a chunk only jumps at the '
                 'joins', fontsize=11.2, weight='bold')
    ax = axes[1]
    _plain(ax)
    cs = (1, 2, 4, 8, 16, 32, 48)
    vals = [np.linalg.norm(np.diff(s.runs[c][1], axis=0), axis=2).mean() * 10.0
            for c in cs]
    ax.bar(np.arange(len(cs)), vals, color=TEAL, width=0.6, alpha=0.85)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.03, f'{v:.3f}', ha='center', fontsize=8.8, color=INK)
    ax.set_xticks(np.arange(len(cs)))
    ax.set_xticklabels([str(c) for c in cs], fontsize=9.5)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_xlabel('steps played per decision', fontsize=9.5)
    ax.set_ylabel('average change per step (mm)', fontsize=9.5)
    ax.set_title(f'From {vals[0]:.3f} mm a step down to {min(vals):.3f} mm',
                 fontsize=11.5, weight='bold')
    print('[bc] average change in the command from step to step (mm): ' +
          ', '.join(f'chunk {c}: {v:.3f}' for c, v in zip(cs, vals)))
    fig.tight_layout()
    _save(fig, BC_DOC, 'chunk-smoothness.svg')


# --------------------------------------------------------------------------
# section 5 --- the action-chunking transformer
# --------------------------------------------------------------------------

ACT_H, ACT_W = 480, 640
ACT_CAMS = 4
ACT_STRIDE = 32
ACT_WIDTH = 512
ACT_CHUNK = 100
ACT_JOINTS = 14
ACT_HEADS = 8
ACT_ENC, ACT_DEC = 4, 7
ACT_FFN = 3200
ACT_RATE = 50.0                    # the two-armed rig this arrangement was built for
ACT_DT = 1.0 / ACT_RATE


def _act_counts() -> dict[str, int]:
    gh, gw = ACT_H // ACT_STRIDE, ACT_W // ACT_STRIDE
    cells = gh * gw
    vis = cells * ACT_CAMS
    tokens = vis + 2
    enc_pairs = tokens * tokens
    dec_pairs = ACT_CHUNK * tokens + ACT_CHUNK * ACT_CHUNK
    att = 4 * ACT_WIDTH * ACT_WIDTH + 4 * ACT_WIDTH
    ffn = ACT_WIDTH * ACT_FFN + ACT_FFN + ACT_FFN * ACT_WIDTH + ACT_WIDTH
    enc_layer = att + ffn + 4 * ACT_WIDTH
    dec_layer = 2 * att + ffn + 6 * ACT_WIDTH
    head = ACT_WIDTH * ACT_JOINTS + ACT_JOINTS
    total = ACT_ENC * enc_layer + ACT_DEC * dec_layer + head
    return dict(gh=gh, gw=gw, cells=cells, vis=vis, tokens=tokens, enc_pairs=enc_pairs,
                dec_pairs=dec_pairs, enc_layer=enc_layer, dec_layer=dec_layer,
                head=head, total=total, out=ACT_CHUNK * ACT_JOINTS)


def act_shapes() -> None:
    c = _act_counts()
    print(f'[bc] ACT: each {ACT_H} x {ACT_W} picture becomes a {c["gh"]} x {c["gw"]} = '
          f'{c["cells"]} cell grid at stride {ACT_STRIDE}')
    print(f'[bc] {ACT_CAMS} cameras give {c["vis"]} picture tokens, plus one for the joints '
          f'and one for the style, so {c["tokens"]} tokens of {ACT_WIDTH} numbers '
          f'= {c["tokens"] * ACT_WIDTH:,} numbers')
    print(f'[bc] the decoder has {ACT_CHUNK} slots and gives {ACT_CHUNK} x {ACT_JOINTS} = '
          f'{c["out"]:,} numbers, which is {ACT_CHUNK * ACT_DT:.2f} s of movement at '
          f'{ACT_RATE:.0f} Hz')
    print(f'[bc] weights: {ACT_ENC} encoder layers of {c["enc_layer"]:,} + {ACT_DEC} '
          f'decoder layers of {c["dec_layer"]:,} + a head of {c["head"]:,} '
          f'= {c["total"]:,} in the transformer alone')

    fig, ax = plt.subplots(figsize=(13.0, 5.6), facecolor='white')
    ax.axis('off')
    ax.set_xlim(0, 14.2)
    ax.set_ylim(0, 6.4)
    for i in range(ACT_CAMS):
        _box(ax, 0.1, 4.6 - i * 0.78, 2.3, 0.62,
             f'camera {i + 1}: {ACT_H} x {ACT_W}', WRIST, fontsize=8.8)
    _box(ax, 0.1, 1.0, 2.3, 0.62, f'{ACT_JOINTS} joint readings', TEAL, fontsize=8.8)
    _box(ax, 0.1, 0.2, 2.3, 0.62, 'style numbers (0 when running)', PURPLE, fontsize=8.4)
    _box(ax, 3.0, 2.4, 2.3, 2.6,
         f'ResNet-18\non each picture\n\n{c["gh"]} x {c["gw"]} = {c["cells"]} cells\n'
         f'per camera', LINK, fontsize=9.0)
    _box(ax, 6.0, 1.9, 2.5, 3.2,
         f'encoder\n{ACT_ENC} layers\n\n{c["tokens"]} tokens\nof {ACT_WIDTH} numbers\n\n'
         f'{c["tokens"] * ACT_WIDTH:,}\nnumbers in all', PURPLE, fontsize=9.0)
    _box(ax, 9.2, 1.9, 2.4, 3.2,
         f'decoder\n{ACT_DEC} layers\n\n{ACT_CHUNK} slots,\none per future step',
         TEAL, fontsize=9.0)
    _box(ax, 9.2, 0.4, 2.4, 1.1,
         f'{ACT_CHUNK} x {ACT_JOINTS} = {c["out"]:,} numbers\n'
         f'= {ACT_CHUNK * ACT_DT:.2f} s of movement', SLIDE, fontsize=9.0, weight='bold')
    for i in range(ACT_CAMS):
        _arrow(ax, (2.45, 4.9 - i * 0.78), (2.95, 3.9), MUTED)
    _arrow(ax, (2.45, 1.3), (5.95, 2.3), MUTED)
    _arrow(ax, (2.45, 0.5), (5.95, 2.1), MUTED)
    _arrow(ax, (5.35, 3.7), (5.95, 3.7), INK)
    _arrow(ax, (8.55, 3.5), (9.15, 3.5), INK)
    _arrow(ax, (10.4, 1.85), (10.4, 1.55), INK)
    ax.text(12.9, 3.5, f'{c["total"]:,}\nweights in the\nencoder and\ndecoder together',
            fontsize=9.5, color=INK, ha='center', va='center')
    ax.set_title('The action-chunking transformer, with every shape counted',
                 fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'act-shapes.svg')


def act_attention_cost() -> None:
    c = _act_counts()
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.7), facecolor='white')
    ax = axes[0]
    _plain(ax)
    cams = np.arange(1, 5)
    toks = cams * c['cells'] + 2
    pairs = toks ** 2
    ax.bar(cams, pairs / 1e6, color=PURPLE, width=0.55, alpha=0.85)
    for n, tk, p in zip(cams, toks, pairs):
        ax.text(n, p / 1e6 * 1.03, f'{tk} tokens\n{p / 1e6:.2f}M pairs', ha='center',
                fontsize=9, color=INK)
    ax.set_xticks(cams)
    ax.set_xlabel('cameras feeding the encoder', fontsize=9.5)
    ax.set_ylabel('token pairs per head per layer (millions)', fontsize=9.5)
    ax.set_ylim(0, pairs[-1] / 1e6 * 1.3)
    ax.set_title(f'Two cameras instead of one: {pairs[1] / pairs[0]:.1f} times the pairs',
                 fontsize=11.2, weight='bold')
    print('[bc] attention pairs per head per layer: ' +
          ', '.join(f'{n} cameras ({tk} tokens): {p:,}'
                    for n, tk, p in zip(cams, toks, pairs)))
    ax = axes[1]
    _plain(ax)
    chunks = np.array([25, 50, 100, 200])
    dec = chunks * c['tokens'] + chunks ** 2
    ax.bar(np.arange(len(chunks)), dec / 1e6, color=TEAL, width=0.55, alpha=0.85)
    for i, (ch, d) in enumerate(zip(chunks, dec)):
        ax.text(i, d / 1e6 * 1.02, f'{d / 1e6:.2f}M pairs\n{ch * ACT_JOINTS:,} numbers out\n'
                                   f'{ch * ACT_DT:.1f} s of movement', ha='center',
                fontsize=8.6, color=INK)
    ax.set_xticks(np.arange(len(chunks)))
    ax.set_xticklabels([str(ch) for ch in chunks], fontsize=9.5)
    ax.set_xlabel(f'steps in the chunk, at {ACT_RATE:.0f} Hz', fontsize=9.5)
    ax.set_ylabel('pairs in the decoder (millions)', fontsize=9.5)
    ax.set_ylim(0, dec[-1] / 1e6 * 1.45)
    ax.set_title(f'A {chunks[-1]}-step chunk: {dec[-1] / c["enc_pairs"]:.2f} of an '
                 f'encoder layer', fontsize=11.2, weight='bold')
    print('[bc] decoder pairs by chunk length: ' +
          ', '.join(f'{ch}: {d:,}' for ch, d in zip(chunks, dec)))
    fig.tight_layout()
    _save(fig, BC_DOC, 'act-attention-cost.svg')


def act_output_block() -> None:
    c = _act_counts()
    rng = np.random.default_rng(21)
    t = np.arange(ACT_CHUNK)
    block = np.zeros((ACT_CHUNK, ACT_JOINTS))
    for j in range(ACT_JOINTS):
        amp = rng.uniform(0.25, 1.0) * (1 if j % 2 == 0 else -1)
        ph = rng.uniform(0, 2 * np.pi)
        block[:, j] = amp * np.sin(np.pi * t / ACT_CHUNK * rng.uniform(0.7, 1.3) + ph)
    block[:, 6] = np.where(t < 60, 1.0, np.where(t < 72, 1.0 - (t - 60) / 12.0, 0.0))
    block[:, 13] = block[:, 6]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    im = ax.imshow(block.T, aspect='auto', cmap='RdBu_r', vmin=-1.1, vmax=1.1)
    ax.set_yticks(np.arange(ACT_JOINTS))
    ax.set_yticklabels([f'left j{i + 1}' for i in range(6)] + ['left grip'] +
                       [f'right j{i + 1}' for i in range(6)] + ['right grip'],
                       fontsize=7.6)
    ax.set_xlabel(f'step in the chunk, 1 to {ACT_CHUNK} '
                  f'(= {ACT_CHUNK * ACT_DT:.2f} s at {ACT_RATE:.0f} Hz)', fontsize=9.5)
    ax.set_title(f'The whole answer: a {ACT_CHUNK} by {ACT_JOINTS} block of '
                 f'{c["out"]:,} numbers', fontsize=11.2, weight='bold')
    cb = fig.colorbar(im, ax=ax, fraction=0.035)
    cb.set_label('rescaled joint target', fontsize=9)
    cb.ax.tick_params(labelsize=8.5)
    ax = axes[1]
    _plain(ax)
    ax.plot(t * ACT_DT, block[:, 2], color=LINK, lw=2.2, label='left elbow')
    ax.plot(t * ACT_DT, block[:, 6], color=SLIDE, lw=2.2, label='left gripper')
    ax.axvline(60 * ACT_DT, color=MUTED, ls=':', lw=1.3)
    ax.text(60 * ACT_DT + 0.04, -0.75, f'the gripper shuts at step 60,\n'
                                       f'{60 * ACT_DT:.1f} s ahead', fontsize=9,
            color=MUTED)
    ax.set_xlabel('seconds ahead of now', fontsize=9.5)
    ax.set_ylabel('rescaled joint target', fontsize=9.5)
    ax.set_ylim(-1.3, 1.3)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title('Two rows of that block, read as movement', fontsize=11.2, weight='bold')
    print(f'[bc] the drawn chunk is simulated; it holds {c["out"]:,} numbers covering '
          f'{ACT_CHUNK * ACT_DT:.2f} s, and the gripper shuts '
          f'{60 * ACT_DT:.1f} s ahead')
    fig.tight_layout()
    _save(fig, BC_DOC, 'act-output-block.svg')


# --------------------------------------------------------------------------
# section 6 --- temporal ensembling and the length of a chunk
# --------------------------------------------------------------------------

def ensembling_weights(m: int, k: float = 0.01) -> Arr:
    w = np.exp(-k * np.arange(m))
    return w / w.sum()


def temporal_ensembling() -> None:
    s = _sim()
    m = 8
    w = ensembling_weights(m)
    rng = np.random.default_rng(77)
    starts, goals = test_starts(1, seed=303)
    pos = starts.copy()
    hist: list[Arr] = []
    raw, ens, gaps = [], [], []
    store_blocks = []
    for t in range(60):
        block = s.policy(np.concatenate([pos, goals], axis=1))[0]
        hist.insert(0, block)
        hist = hist[:m]
        picks = np.array([hist[i][i] for i in range(len(hist))])
        ww = w[:len(hist)] / w[:len(hist)].sum()
        a = (picks * ww[:, None]).sum(0)
        raw.append(block[0].copy())
        ens.append(a.copy())
        store_blocks.append(picks.copy())
        gaps.append(len(hist))
        pos = pos + a[None] + rng.normal(0, 0.02, (1, 2))
    raw_a = np.array(raw)
    ens_a = np.array(ens)
    print(f'[bc] temporal ensembling weights for m = 0.01 and {m} chunks: ' +
          ', '.join(f'{x:.4f}' for x in w))
    print(f'[bc] newest chunk gets {w[0]:.4f} and the oldest {w[-1]:.4f}, '
          f'a difference of {100 * (w[0] / w[-1] - 1):.1f} per cent')
    jr = np.linalg.norm(np.diff(raw_a, axis=0), axis=1).mean() * 10
    je = np.linalg.norm(np.diff(ens_a, axis=0), axis=1).mean() * 10
    print(f'[bc] average step-to-step change: newest chunk only {jr:.3f} mm, '
          f'weighted average of {m} chunks {je:.3f} mm, a drop of '
          f'{100 * (1 - je / jr):.1f} per cent')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    k = 40
    picks = store_blocks[k]
    vs = picks[:, 1] * 10
    span = max(vs.max() - vs.min(), 1e-3)
    for i, v in enumerate(vs):
        ax.plot([i], [v], 'o', color=LINK, ms=7, alpha=0.9)
        ax.text(i, v - span * 0.09, f'{v:.3f}', ha='center', fontsize=8.4,
                color=LINK, va='top')
    ax.axhline(ens_a[k][1] * 10, color=GRIP, lw=2.0,
               label=f'weighted average {ens_a[k][1] * 10:.3f} mm')
    ax.set_ylim(vs.min() - span * 0.3, vs.max() + span * 0.22)
    ax.set_xlim(-0.6, len(vs) - 0.4)
    ax.set_xticks(np.arange(len(picks)))
    ax.set_xticklabels([f'{i} steps\nold' for i in range(len(picks))], fontsize=8.4)
    ax.set_xlabel(f'which chunk the guess came from, at step {k} of the run',
                  fontsize=9.5)
    ax.set_ylabel('guess for this step, sideways part (mm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper right')
    ax.set_title(f'{len(picks)} chunks all hold a guess for step {k}', fontsize=11.2,
                 weight='bold')
    ax = axes[1]
    _plain(ax)
    tt = np.arange(len(raw_a)) * DT
    ax.plot(tt, raw_a[:, 1] * 10, color=GRIP, lw=1.5, label='newest chunk only')
    ax.plot(tt, ens_a[:, 1] * 10, color=LINK, lw=2.4,
            label=f'weighted average of up to {m}')
    ax.set_xlabel('time through the run (seconds)', fontsize=9.5)
    ax.set_ylabel('command, sideways part (mm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='lower right')
    ax.set_title(f'The averaged command changes {100 * (1 - je / jr):.0f} per cent less '
                 f'from step to step', fontsize=11.2, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'temporal-ensembling.svg')


def ensembling_weights_picture() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.6), facecolor='white')
    _plain(ax)
    m = 8
    for kk, col, nm in ((0.01, LINK, 'm = 0.01 (the usual setting)'),
                        (0.2, WRIST, 'm = 0.2'),
                        (0.8, GRIP, 'm = 0.8')):
        w = ensembling_weights(m, kk)
        ax.plot(np.arange(m), w, 'o-', color=col, lw=2.0, ms=7, label=nm)
        print(f'[bc] weights at m = {kk}: ' + ', '.join(f'{x:.3f}' for x in w))
        for i in (0, m - 1):
            ax.text(i, w[i] + 0.012, f'{w[i]:.3f}', ha='center', fontsize=8.6, color=col)
    ax.set_xticks(np.arange(m))
    ax.set_xticklabels([f'{i}' for i in range(m)])
    ax.set_xlabel('how many steps ago the chunk was worked out', fontsize=9.5)
    ax.set_ylabel('its share of the command', fontsize=9.5)
    ax.set_ylim(0, 0.75)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('The weights in temporal ensembling: at m = 0.01 the eight chunks count '
                 'almost equally', fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'ensembling-weights.svg')


def chunk_length_trade() -> None:
    s = _sim()
    cs = (1, 2, 4, 8, 16, 32, 48)
    starts, goals = test_starts(40, seed=303)
    new_goals = goals + np.array([0.0, 8.0])
    drift, react = [], []
    for c in cs:
        drift.append(s.error(c)[-1])
        path, _cmd, _g = rollout(s.policy, starts, goals, c,
                                 np.random.default_rng(900 + c), shift_at=50,
                                 new_goals=new_goals)
        miss = np.linalg.norm(path[-1] - new_goals, axis=1).mean()
        react.append(miss)
        print(f'[bc] chunk of {c:2d}: drift at the end {drift[-1]:.2f} cm, '
              f'miss after the goal jumps 8 cm at step 50: {miss:.2f} cm, '
              f'longest wait before it notices {c * DT * 1000:.0f} ms')
    best = int(np.argmin(np.array(drift) + np.array(react)))
    print(f'[bc] adding the two costs, the chunk of {cs[best]} is lowest at '
          f'{drift[best] + react[best]:.2f} cm')
    fig, ax = plt.subplots(figsize=(11.2, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(len(cs))
    ax.plot(x, drift, 'o-', color=LINK, lw=2.2, ms=7,
            label='drift: how far off it ends with nothing changing')
    ax.plot(x, react, 's-', color=GRIP, lw=2.2, ms=7,
            label='slowness: how far off it ends when the goal jumps 8 cm')
    tot = np.array(drift) + np.array(react)
    ax.plot(x, tot, '^:', color=PURPLE, lw=1.8, ms=7, label='the two added together')
    ax.plot([x[best]], [tot[best]], 'o', color=PURPLE, ms=14, mfc='none', mew=2.2)
    ax.annotate(f'best here: chunk of {cs[best]}\n({cs[best] * DT * 1000:.0f} ms of motion)',
                xy=(x[best], tot[best]), xytext=(x[best] - 1.6, tot[best] + 2.0),
                fontsize=9.5, color=PURPLE,
                arrowprops=dict(arrowstyle='-|>', color=PURPLE, lw=1.3))
    ax.set_xticks(x)
    ax.set_xticklabels([f'{c}\n{c * DT * 1000:.0f} ms' for c in cs], fontsize=9.2)
    ax.set_xlabel('steps played per decision, and how long they last', fontsize=9.5)
    ax.set_ylabel('distance from where it should be at the end (cm)', fontsize=9.5)
    ax.set_ylim(0, max(tot) * 1.35)
    ax.legend(fontsize=9.2, frameon=False, loc='upper center')
    ax.set_title('The trade: short chunks drift, long chunks react late',
                 fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'chunk-length-trade.svg')


# ==========================================================================
# PAGE 2 --- the two-way obstacle task, and the generators
# ==========================================================================

BOX: tuple[float, float, float, float] = (16.0, 24.0, -5.0, 5.0)
GOAL2: Arr = np.array([40.0, 0.0])
OBST_STEPS: int = 120
CHUNK2: int = 32                  # steps the policy works out at once
SPLIT: float = 10.0               # how far along the reach the two ways part
EXEC2: int = 8                    # steps it plays before working out the next
ADIM: int = CHUNK2 * 2            # numbers in one chunk


def _obst_profile(n: int, g: float, hesitate: bool = True) -> Arr:
    tau = np.linspace(0.0, 1.0, n + 1)
    sp = np.sin(np.pi * tau) ** g + 0.02
    if hesitate:
        sp = sp * (1.0 - 0.80 * np.exp(-((tau - 0.72) / 0.05) ** 2))
    u = np.cumsum(sp)
    return (u - u[0]) / (u[-1] - u[0])


def _bump(u: Arr) -> Arr:
    """Zero for the first quarter of the reach, then a swing out and back."""
    return np.exp(-((u - 0.5) / 0.17) ** 2)


def obstacle_demo(rng: np.random.Generator, side: float | None = None,
                  n: int = OBST_STEPS) -> tuple[Arr, Arr, float]:
    start = np.array([0.0, 0.0]) + rng.normal(0, 0.5, 2)
    goal = GOAL2 + rng.normal(0, 0.4, 2)
    s = float(rng.choice([-1.0, 1.0])) if side is None else side
    arc = s * rng.normal(9.0, 0.8)
    u = _obst_profile(n, rng.normal(1.0, 0.08))
    d = goal - start
    perp = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    pos = start + u[:, None] * d + arc * _bump(u)[:, None] * perp
    pos = pos + _tremor(rng, n + 1, 0.22)
    return pos, np.diff(pos, axis=0), s


def hits_box(path: Arr) -> Arr:
    """True for each run whose path goes through the box. path is (steps, runs, 2)."""
    x0, x1, y0, y1 = BOX
    inside = ((path[..., 0] > x0) & (path[..., 0] < x1) &
              (path[..., 1] > y0) & (path[..., 1] < y1))
    return inside.any(axis=0)


class ObstacleData:
    """Every recorded moment of the obstacle demonstrations, ready for training."""

    def __init__(self, n_demos: int = 400, seed: int = 5) -> None:
        rng = np.random.default_rng(seed)
        obs, chunks, paths, sides = [], [], [], []
        for _ in range(n_demos):
            pos, acts, s = obstacle_demo(rng)
            keep = len(acts) - CHUNK2
            obs.append(pos[:keep])
            chunks.append(np.stack([acts[i:i + CHUNK2] for i in range(keep)]))
            paths.append(pos)
            sides.append(s)
        self.paths = np.stack(paths, axis=1)
        self.sides = np.array(sides)
        self.obs_raw = np.concatenate(obs)
        ch = np.concatenate(chunks)
        # each of the two action numbers gets its own scale, because a step along
        # the reach and a step sideways are nothing like the same size
        self.act_mean = ch.reshape(-1, 2).mean(0)
        self.act_std = ch.reshape(-1, 2).std(0)
        self.chunks_raw = ch
        self.x = self.norm_obs(self.obs_raw).astype(np.float32)
        self.y = self.to_norm(ch)
        self.n_demos = n_demos

    def to_norm(self, ch: Arr) -> Arr:
        return ((ch - self.act_mean) / self.act_std).reshape(len(ch), -1).astype(np.float32)

    @staticmethod
    def norm_obs(p: Arr) -> Arr:
        return np.column_stack([p[:, 0] / 20.0 - 1.0, p[:, 1] / 10.0]).astype(np.float32)

    def to_cm(self, y: Arr) -> Arr:
        return y.reshape(len(y), CHUNK2, 2) * self.act_std + self.act_mean


class Mlp:
    """A small network of fully connected layers, trained with Adam in NumPy."""

    def __init__(self, sizes: list[int], seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        self.n = len(sizes) - 1
        self.W = [rng.normal(0, np.sqrt(2.0 / sizes[i]),
                             (sizes[i], sizes[i + 1])).astype(np.float32)
                  for i in range(self.n)]
        self.B = [np.zeros(sizes[i + 1], dtype=np.float32) for i in range(self.n)]
        self.mW = [np.zeros_like(w) for w in self.W]
        self.vW = [np.zeros_like(w) for w in self.W]
        self.mB = [np.zeros_like(b) for b in self.B]
        self.vB = [np.zeros_like(b) for b in self.B]
        self.t = 0
        self.sizes = sizes

    @property
    def n_weights(self) -> int:
        return sum(w.size for w in self.W) + sum(b.size for b in self.B)

    def __call__(self, x: Arr) -> Arr:
        h = x
        for i in range(self.n):
            z = h @ self.W[i] + self.B[i]
            h = _silu(z) if i < self.n - 1 else z
        return h

    def step(self, x: Arr, target: Arr, lr: float) -> float:
        zs, hs = [], [x]
        h = x
        for i in range(self.n):
            z = h @ self.W[i] + self.B[i]
            zs.append(z)
            h = _silu(z) if i < self.n - 1 else z
            hs.append(h)
        loss = float(np.mean((h - target) ** 2))
        d = 2.0 * (h - target) / (x.shape[0] * target.shape[1])
        gW: list[Arr] = [np.zeros(0)] * self.n
        gB: list[Arr] = [np.zeros(0)] * self.n
        for i in reversed(range(self.n)):
            gW[i] = hs[i].T @ d
            gB[i] = d.sum(0)
            if i > 0:
                d = (d @ self.W[i].T) * _dsilu(zs[i - 1])
        self.t += 1
        b1, b2, eps = 0.9, 0.999, 1e-8
        c1 = 1 - b1 ** self.t
        c2 = 1 - b2 ** self.t
        for i in range(self.n):
            self.mW[i] = b1 * self.mW[i] + (1 - b1) * gW[i]
            self.vW[i] = b2 * self.vW[i] + (1 - b2) * gW[i] ** 2
            self.W[i] -= lr * (self.mW[i] / c1) / (np.sqrt(self.vW[i] / c2) + eps)
            self.mB[i] = b1 * self.mB[i] + (1 - b1) * gB[i]
            self.vB[i] = b2 * self.vB[i] + (1 - b2) * gB[i] ** 2
            self.B[i] -= lr * (self.mB[i] / c1) / (np.sqrt(self.vB[i] / c2) + eps)
        return loss


TEMB: int = 16
K_STEPS: int = 100


def _temb(u: Arr) -> Arr:
    """Turn the noise level into a few smooth numbers the network can read."""
    freqs = np.arange(1, TEMB // 2 + 1)
    ang = u[:, None] * np.pi * freqs[None, :]
    return np.concatenate([np.sin(ang), np.cos(ang)], axis=1).astype(np.float32)


def _abar() -> Arr:
    s = 0.008
    t = np.arange(K_STEPS + 1) / K_STEPS
    f = np.cos((t + s) / (1 + s) * np.pi / 2) ** 2
    return f / f[0]


AB: Arr = np.clip(_abar(), 0.01, 1.0).astype(np.float32)


class Policies:
    """Three policies trained on the same obstacle demonstrations."""

    def __init__(self) -> None:
        self.data = ObstacleData()
        d = self.data
        n = len(d.x)
        rng = np.random.default_rng(3)
        hid = 224
        self.diff = Mlp([ADIM + 2 + TEMB, hid, hid, ADIM], seed=1)
        self.flow = Mlp([ADIM + 2 + TEMB, hid, hid, ADIM], seed=2)
        self.mean = Mlp([2, hid, hid, ADIM], seed=4)
        steps, batch = 10000, 256
        self.losses: dict[str, list[float]] = {'diffusion': [], 'flow': [], 'averaging': []}
        if CACHE is not None and CACHE.exists():
            z = np.load(CACHE)
            for nm, net in (('d', self.diff), ('f', self.flow), ('m', self.mean)):
                for i in range(net.n):
                    net.W[i] = z[f'{nm}W{i}']
                    net.B[i] = z[f'{nm}B{i}']
            print(f'[df] loaded the trained weights from {CACHE}')
            self.losses = {k: [float(z[f'loss_{k}'])] for k in self.losses}
            return
        for it in range(steps):
            lr = 1.5e-3 * (0.5 * (1 + np.cos(np.pi * it / steps)) * 0.9 + 0.1)
            j = rng.integers(0, n, batch)
            x0, obs = d.y[j], d.x[j]
            ti = rng.integers(1, K_STEPS + 1, batch)
            ab = AB[ti][:, None]
            eps = rng.normal(size=x0.shape).astype(np.float32)
            xt = np.sqrt(ab) * x0 + np.sqrt(1 - ab) * eps
            la = self.diff.step(np.concatenate([xt, obs, _temb(ti / K_STEPS)], 1), x0, lr)
            tf = rng.uniform(0, 1, batch)
            z = rng.normal(size=x0.shape).astype(np.float32)
            xf = (1 - tf)[:, None] * z + tf[:, None] * x0
            lb = self.flow.step(np.concatenate([xf, obs, _temb(tf)], 1), x0 - z, lr)
            lc = self.mean.step(obs, x0, lr)
            if it % 50 == 0:
                self.losses['diffusion'].append(la)
                self.losses['flow'].append(lb)
                self.losses['averaging'].append(lc)
        print(f'[df] trained on {n:,} recorded moments from {d.n_demos} demonstrations; '
              f'each network holds {self.diff.n_weights:,} weights '
              f'(the averaging one {self.mean.n_weights:,})')
        print(f'[df] final training loss: diffusion {self.losses["diffusion"][-1]:.4f}, '
              f'flow {self.losses["flow"][-1]:.4f}, '
              f'averaging {self.losses["averaging"][-1]:.4f}')
        if CACHE is not None:
            out = {}
            for nm, net in (('d', self.diff), ('f', self.flow), ('m', self.mean)):
                for i in range(net.n):
                    out[f'{nm}W{i}'] = net.W[i]
                    out[f'{nm}B{i}'] = net.B[i]
            for k, v in self.losses.items():
                out[f'loss_{k}'] = np.array(v[-1])
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            np.savez(CACHE, **out)

    # ---- samplers, all returning chunks in centimetres ----

    def ddim(self, obs: Arr, n_steps: int, rng: np.random.Generator,
             trace: bool = False) -> Arr | tuple[Arr, Arr]:
        x = rng.normal(size=(len(obs), ADIM)).astype(np.float32)
        ts = np.linspace(K_STEPS, 0, n_steps + 1).round().astype(int)
        path = [x.copy()]
        for i in range(n_steps):
            ti, tp = int(ts[i]), int(ts[i + 1])
            ab_t, ab_p = AB[ti], AB[tp]
            u = np.full(len(obs), ti / K_STEPS, dtype=np.float32)
            x0 = np.clip(self.diff(np.concatenate([x, obs, _temb(u)], 1)), -4.0, 4.0)
            eps = (x - np.sqrt(ab_t) * x0) / np.sqrt(1 - ab_t)
            x = np.sqrt(ab_p) * x0 + np.sqrt(1 - ab_p) * eps
            path.append(x.copy())
        if trace:
            return self.data.to_cm(x), np.stack(path)
        return self.data.to_cm(x)

    def euler(self, obs: Arr, n_steps: int, rng: np.random.Generator,
              trace: bool = False) -> Arr | tuple[Arr, Arr]:
        x = rng.normal(size=(len(obs), ADIM)).astype(np.float32)
        path = [x.copy()]
        for i in range(n_steps):
            u = np.full(len(obs), i / n_steps, dtype=np.float32)
            v = self.flow(np.concatenate([x, obs, _temb(u)], 1))
            x = x + v / n_steps
            path.append(x.copy())
        if trace:
            return self.data.to_cm(x), np.stack(path)
        return self.data.to_cm(x)

    def average(self, obs: Arr) -> Arr:
        return self.data.to_cm(self.mean(obs))


POL: Policies | None = None


def _pol() -> Policies:
    global POL
    if POL is None:
        POL = Policies()
    return POL


def obst_rollout(kind: str, n_runs: int, rng: np.random.Generator, n_steps: int = 20,
                 start_offset: float = 0.0, steps: int = OBST_STEPS,
                 execute: int = EXEC2) -> Arr:
    p = _pol()
    pos = np.column_stack([rng.normal(0, 0.5, n_runs),
                           rng.normal(0, 0.5, n_runs) + start_offset])
    path = np.zeros((steps + 1, n_runs, 2))
    path[0] = pos
    t = 0
    while t < steps:
        o = ObstacleData.norm_obs(pos)
        if kind == 'average':
            ch = p.average(o)
        elif kind == 'diffusion':
            ch = p.ddim(o, n_steps, rng)
        else:
            ch = p.euler(o, n_steps, rng)
        for i in range(min(execute, steps - t)):
            pos = pos + ch[:, i] + rng.normal(0, 0.02, (n_runs, 2))
            t += 1
            path[t] = pos
    return path


def _draw_box(ax: Axes, label: bool = True) -> None:
    x0, x1, y0, y1 = BOX
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=MUTED, alpha=0.35,
                               edgecolor=INK, lw=1.4, zorder=5))
    if label:
        ax.text((x0 + x1) / 2, 0, 'box', ha='center', va='center', fontsize=10,
                color='white', zorder=6, weight='bold')


# --------------------------------------------------------------------------
# page 2, section 1 --- the averaging problem
# --------------------------------------------------------------------------

def two_ways_one_average() -> None:
    d = _pol().data
    up = d.paths[:, d.sides > 0]
    dn = d.paths[:, d.sides < 0]
    mean_path = d.paths.mean(axis=1)
    print(f'[df] {d.n_demos} demonstrations: {up.shape[1]} go one side, '
          f'{dn.shape[1]} the other')
    print(f'[df] the average of all of them passes the box at y = '
          f'{mean_path[OBST_STEPS // 2, 1]:+.2f} cm, which is inside it')
    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    for i in range(0, up.shape[1], 8):
        ax.plot(up[:, i, 0], up[:, i, 1], color=LINK, lw=0.9, alpha=0.5,
                label='demonstrations going one way' if i == 0 else None)
    for i in range(0, dn.shape[1], 8):
        ax.plot(dn[:, i, 0], dn[:, i, 1], color=TEAL, lw=0.9, alpha=0.5,
                label='demonstrations going the other way' if i == 0 else None)
    ax.plot(mean_path[:, 0], mean_path[:, 1], color=GRIP, lw=3.0,
            label='the average of all of them')
    _draw_box(ax)
    ax.plot(*GOAL2, '*', color=INK, ms=16, zorder=7)
    ax.text(GOAL2[0], GOAL2[1] + 1.4, 'goal', ha='center', fontsize=9.5)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left')
    ax.set_title('Both ways round the box are right, and the average of them is not',
                 fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'two-ways-one-average.svg')


def label_spread() -> None:
    d = _pol().data
    near = np.abs(d.obs_raw[:, 0] - SPLIT) < 0.6
    lab = d.chunks_raw[near].sum(axis=1)[:, 1]
    print(f'[df] at {SPLIT:.0f} cm along the reach there are {near.sum()} recorded '
          f'moments; '
          f'over the next {CHUNK2} steps they move sideways by '
          f'{lab[lab > 0].mean():+.2f} cm one way and {lab[lab < 0].mean():+.2f} cm the '
          f'other, and the average of all of them is {lab.mean():+.3f} cm')
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.hist(lab, bins=40, color=LINK, alpha=0.8)
    ax.axvline(lab.mean(), color=GRIP, lw=2.4,
               label=f'the average label, {lab.mean():+.3f} cm')
    ax.axvline(lab[lab > 0].mean(), color=TEAL, lw=1.6, ls='--')
    ax.axvline(lab[lab < 0].mean(), color=TEAL, lw=1.6, ls='--',
               label='the two things people actually did')
    ax.set_xlabel(f'sideways movement over the next {CHUNK2} steps (cm)', fontsize=9.5)
    ax.set_ylabel('recorded moments', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper center')
    ax.set_title('One question, two very different labels', fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    qs = np.linspace(lab.min() * 1.1, lab.max() * 1.1, 400)
    se = ((lab[None, :] - qs[:, None]) ** 2).mean(1)
    ax.plot(qs, se, color=PURPLE, lw=2.4)
    ax.plot([lab.mean()], [se.min()], 'o', color=GRIP, ms=10)
    ax.annotate(f'lowest at {lab.mean():+.3f} cm,\nthe average of the labels',
                xy=(lab.mean(), se.min()), xytext=(lab.mean() + 1.0, se.min() * 1.5),
                fontsize=9.5, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.3))
    for v, nm in ((lab[lab > 0].mean(), 'one way'), (lab[lab < 0].mean(), 'the other')):
        k = int(np.argmin(np.abs(qs - v)))
        ax.plot([v], [se[k]], 's', color=TEAL, ms=8)
        ax.text(v, se[k] * 1.04, nm, ha='center', fontsize=9, color=TEAL)
    ax.set_xlabel('the one number the policy could put out (cm)', fontsize=9.5)
    ax.set_ylabel('average squared error against the labels', fontsize=9.5)
    ax.set_title('Squared error is lowest exactly at the average', fontsize=11.5,
                 weight='bold')
    print(f'[df] squared error: {se.min():.2f} at the average, '
          f'{se[int(np.argmin(np.abs(qs - lab[lab > 0].mean())))]:.2f} at the one way')
    fig.tight_layout()
    _save(fig, DF_DOC, 'label-spread.svg')


def averaging_rollouts() -> None:
    rng = np.random.default_rng(31)
    path = obst_rollout('average', 200, rng)
    hit = hits_box(path)
    end = np.linalg.norm(path[-1] - GOAL2, axis=1)
    print(f'[df] the averaging policy: {hit.mean() * 100:.1f} per cent of 200 runs go '
          f'through the box, and the average end point is {end.mean():.2f} cm from the goal')
    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    for i in range(0, 200, 2):
        ax.plot(path[:, i, 0], path[:, i, 1], color=GRIP if hit[i] else SLIDE,
                lw=0.8, alpha=0.5)
    _draw_box(ax)
    ax.plot(*GOAL2, '*', color=INK, ms=16, zorder=7)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.set_ylim(-12, 12)
    ax.text(1, 10.2, f'{hit.sum()} of 200 runs go through the box', fontsize=10,
            color=GRIP, weight='bold')
    ax.set_title('A policy trained with squared error drives into the thing it was '
                 'shown going round', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'averaging-rollouts.svg')


# --------------------------------------------------------------------------
# page 2, section 2 --- the diffusion policy
# --------------------------------------------------------------------------

def noising_a_chunk() -> None:
    d = _pol().data
    rng = np.random.default_rng(9)
    j = int(np.argmin(np.abs(d.obs_raw[:, 0] - SPLIT)))
    x0 = d.y[j]
    levels = [0, 20, 40, 60, 100]
    fig, axes = plt.subplots(1, len(levels), figsize=(13.2, 3.4), facecolor='white')
    print('[df] noising one real chunk, 32 steps long:')
    for ax, lv in zip(axes, levels):
        ab = AB[lv]
        xt = np.sqrt(ab) * x0 + np.sqrt(1 - ab) * rng.normal(size=ADIM)
        ch = xt.reshape(CHUNK2, 2) * d.act_std + d.act_mean
        pt = d.obs_raw[j] + np.cumsum(ch, axis=0)
        ax.plot(pt[:, 0], pt[:, 1], 'o-', color=LINK if lv == 0 else PURPLE, ms=3, lw=1.4)
        ax.plot(d.obs_raw[j, 0], d.obs_raw[j, 1], 'o', color=GRIP, ms=6)
        ax.set_title(f'step {lv}\nkeep {np.sqrt(ab):.2f} of it', fontsize=10,
                     weight='bold')
        ax.set_xlim(-10, 24)
        ax.set_ylim(-12, 22)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(GRID)
        print(f'[df]   step {lv:3d}: keeps {np.sqrt(ab):.3f} of the chunk and adds '
              f'{np.sqrt(1 - ab):.3f} of noise')
    axes[0].set_ylabel('the real chunk, drawn as a path', fontsize=9.5)
    fig.suptitle('Noise added to one chunk of 32 future steps, in the shape the training '
                 'uses', fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'noising-a-chunk.svg')


def denoiser_shapes() -> None:
    p = _pol()
    fig, ax = plt.subplots(figsize=(12.4, 4.6), facecolor='white')
    ax.axis('off')
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5.2)
    _box(ax, 0.1, 3.4, 2.9, 1.2, f'the noisy chunk\n{CHUNK2} steps x 2 = {ADIM} numbers',
         PURPLE, fontsize=9.2)
    _box(ax, 0.1, 1.9, 2.9, 1.1, 'where the gripper is\n2 numbers', TEAL, fontsize=9.2)
    _box(ax, 0.1, 0.5, 2.9, 1.1, f'which noise step\n{TEMB} numbers', WRIST, fontsize=9.2)
    _box(ax, 3.9, 1.6, 2.6, 2.6,
         f'{ADIM} + 2 + {TEMB}\n= {ADIM + 2 + TEMB} numbers in', LINK, fontsize=9.6,
         weight='bold')
    _box(ax, 7.2, 1.6, 2.4, 2.6, f'two hidden layers\nof {p.diff.sizes[1]}\n\n'
                                 f'{p.diff.n_weights:,} weights', GRIP, fontsize=9.4)
    _box(ax, 10.3, 2.0, 2.5, 1.8, f'the chunk it thinks\nwas spoiled\n{ADIM} numbers',
         SLIDE, fontsize=9.4, weight='bold')
    for y in (4.0, 2.45, 1.05):
        _arrow(ax, (3.05, y), (3.85, 2.9), MUTED)
    _arrow(ax, (6.55, 2.9), (7.15, 2.9), INK)
    _arrow(ax, (9.65, 2.9), (10.25, 2.9), INK)
    ax.set_title('The denoiser: it never sees a picture of noise, it sees a spoiled '
                 'piece of movement', fontsize=12.2, weight='bold')
    print(f'[df] the denoiser takes {ADIM + 2 + TEMB} numbers and gives {ADIM}; '
          f'it holds {p.diff.n_weights:,} weights in two hidden layers of '
          f'{p.diff.sizes[1]}, and the averaging network holds {p.mean.n_weights:,}')
    fig.tight_layout()
    _save(fig, DF_DOC, 'denoiser-shapes.svg')


def reverse_walk() -> None:
    p = _pol()
    d = p.data
    rng = np.random.default_rng(12)
    obs = ObstacleData.norm_obs(np.array([[SPLIT, 0.0]]))
    _final, trace = p.ddim(obs, 20, rng, trace=True)
    fig, axes = plt.subplots(1, 5, figsize=(13.2, 3.4), facecolor='white')
    picks = [0, 5, 10, 15, 20]
    for ax, k in zip(axes, picks):
        ch = trace[k][0].reshape(CHUNK2, 2) * d.act_std + d.act_mean
        pt = np.array([SPLIT, 0.0]) + np.cumsum(ch, axis=0)
        ax.plot(pt[:, 0], pt[:, 1], 'o-', color=PURPLE if k < 20 else SLIDE, ms=3, lw=1.5)
        ax.plot([SPLIT], [0.0], 'o', color=GRIP, ms=6)
        ax.set_title(f'after {k} of 20 steps', fontsize=10, weight='bold')
        ax.set_xlim(SPLIT - 10, SPLIT + 18)
        ax.set_ylim(-14, 16)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(GRID)
    axes[0].set_ylabel('the chunk, drawn as a path', fontsize=9.5)
    lens = [float(np.linalg.norm(trace[k][0])) for k in picks]
    print('[df] reverse walk: the size of the chunk numbers goes ' +
          ', '.join(f'{v:.1f}' for v in lens) + ' as the noise comes out')
    fig.suptitle('The reverse walk turns noise into one whole movement, not an average '
                 'of two', fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'reverse-walk.svg')


def conditioning() -> None:
    p = _pol()
    rng = np.random.default_rng(4)
    places = [np.array([SPLIT, 0.0]), np.array([18.0, 6.5]), np.array([18.0, -6.5])]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), facecolor='white')
    for ax, pl in zip(axes, places):
        obs = np.repeat(ObstacleData.norm_obs(pl[None, :]), 40, axis=0)
        ch = p.ddim(obs, 20, rng)
        ups = 0
        for i in range(40):
            pt = pl + np.cumsum(ch[i], axis=0)
            ups += int(pt[:, 1].mean() > 0)
            ax.plot(pt[:, 0], pt[:, 1], color=LINK, lw=0.9, alpha=0.6)
        ax.plot(*pl, 'o', color=GRIP, ms=9, zorder=6)
        _draw_box(ax, label=False)
        ax.set_xlim(-2, 36)
        ax.set_ylim(-14, 14)
        _plain(ax)
        ax.set_xlabel('distance along the reach (cm)', fontsize=9)
        ax.set_title(f'from ({pl[0]:.0f}, {pl[1]:+.0f}) cm:\n{ups} of 40 chunks stay '
                     f'above the box', fontsize=10.5, weight='bold')
        print(f'[df] conditioned on ({pl[0]:.0f}, {pl[1]:+.0f}) cm: {ups} of 40 chunks '
              f'stay above the box and {40 - ups} below')
    axes[0].set_ylabel('sideways (cm)', fontsize=9.5)
    fig.suptitle('The same denoiser, three different places: what it generates follows '
                 'what it is told', fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'conditioning.svg')


# --------------------------------------------------------------------------
# page 2, section 3 --- the two policies side by side
# --------------------------------------------------------------------------

def diffusion_rollouts() -> None:
    rng = np.random.default_rng(31)
    path = obst_rollout('diffusion', 200, rng)
    hit = hits_box(path)
    end = np.linalg.norm(path[-1] - GOAL2, axis=1)
    up = (path[OBST_STEPS // 2, :, 1] > 0)
    print(f'[df] the diffusion policy: {hit.sum()} of 200 runs go through the box, '
          f'{up.sum()} pass above and {200 - up.sum()} below, and the average end point '
          f'is {end.mean():.2f} cm from the goal')
    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    for i in range(0, 200, 2):
        ax.plot(path[:, i, 0], path[:, i, 1], color=GRIP if hit[i] else SLIDE,
                lw=0.8, alpha=0.5)
    _draw_box(ax)
    ax.plot(*GOAL2, '*', color=INK, ms=16, zorder=7)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.set_ylim(-12, 12)
    ax.text(1, 10.2, f'{hit.sum()} of 200 runs go through the box', fontsize=10,
            color=SLIDE, weight='bold')
    ax.set_title('The same data, generated instead of averaged: each run picks a side '
                 'and keeps it', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'diffusion-rollouts.svg')


def side_counts() -> None:
    rng = np.random.default_rng(31)
    out = {}
    for kind in ('average', 'diffusion', 'flow'):
        path = obst_rollout(kind, 200, rng)
        hit = hits_box(path)
        mid = path[OBST_STEPS // 2, :, 1]
        end = np.linalg.norm(path[-1] - GOAL2, axis=1)
        out[kind] = (hit.mean() * 100, (mid > 2).sum(), (mid < -2).sum(),
                     int(((mid >= -2) & (mid <= 2)).sum()), end.mean())
        print(f'[df] {kind:10s}: {hit.mean() * 100:5.1f} per cent hit the box, '
              f'{out[kind][1]:3d} go up, {out[kind][2]:3d} go down, '
              f'{out[kind][3]:3d} go straight at it, end {end.mean():.2f} cm from the goal')
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = ['averaging\n(squared error)', 'diffusion\n(20 steps)', 'flow\n(20 steps)']
    vals = [out[k][0] for k in ('average', 'diffusion', 'flow')]
    ax.bar(np.arange(3), vals, color=[GRIP, LINK, TEAL], width=0.55, alpha=0.9)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, f'{v:.1f}%', ha='center', fontsize=10, color=INK)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(names, fontsize=9.2)
    ax.set_ylim(0, max(max(vals) * 1.25, 10))
    ax.set_ylabel('runs that go through the box (per cent)', fontsize=9.5)
    ax.set_title('The same training data, three ways of giving an answer',
                 fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    w = 0.27
    for i, k in enumerate(('average', 'diffusion', 'flow')):
        ax.bar([i - w, i, i + w], [out[k][1], out[k][3], out[k][2]], width=w * 0.92,
               color=[TEAL, GRIP, LINK], alpha=0.9)
        for dx, v in zip((-w, 0, w), (out[k][1], out[k][3], out[k][2])):
            ax.text(i + dx, v + 3, str(v), ha='center', fontsize=8.8, color=INK)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(names, fontsize=9.2)
    ax.set_ylim(0, 230)
    ax.set_ylabel('runs out of 200', fontsize=9.5)
    ax.set_title('Left bar: passes above. Middle: straight at the box. Right: below',
                 fontsize=10.8, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'side-counts.svg')


# --------------------------------------------------------------------------
# page 2, section 4 --- flow matching and the step count
# --------------------------------------------------------------------------

def straight_versus_curved() -> None:
    p = _pol()
    rng = np.random.default_rng(77)
    obs = np.repeat(ObstacleData.norm_obs(np.array([[SPLIT, 0.0]])), 6, axis=0)
    _a, td = p.ddim(obs, 20, rng, trace=True)
    _b, tf = p.euler(obs, 20, rng, trace=True)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white')
    for ax, tr, nm, col in ((axes[0], td, 'diffusion, 20 steps', PURPLE),
                            (axes[1], tf, 'flow matching, 20 steps', TEAL)):
        _plain(ax)
        for i in range(6):
            ax.plot(tr[:, i, 0], tr[:, i, 1], '-o', color=col, ms=3, lw=1.2, alpha=0.8)
            ax.plot(tr[0, i, 0], tr[0, i, 1], 'o', color=GRIP, ms=7)
            ax.plot(tr[-1, i, 0], tr[-1, i, 1], '*', color=SLIDE, ms=13)
        ax.set_xlabel('first number of the chunk', fontsize=9.5)
        ax.set_ylabel('second number of the chunk', fontsize=9.5)
        ln = np.abs(np.diff(tr[:, :, :2], axis=0)).sum(0).sum(1).mean()
        direct = np.abs(tr[-1, :, :2] - tr[0, :, :2]).sum(1).mean()
        ax.set_title(f'{nm}\npath length {ln:.2f} against {direct:.2f} straight',
                     fontsize=11.0, weight='bold')
        print(f'[df] {nm}: the walk covers {ln:.2f} in the first two numbers, '
              f'and the straight line between its ends is {direct:.2f}')
    fig.suptitle('Where the two generators travel, drawn in the first two of the '
                 f'{ADIM} numbers (red dot: the noise it starts from)',
                 fontsize=12.0, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'straight-versus-curved.svg')


def steps_versus_quality() -> None:
    p = _pol()
    d = p.data
    rng = np.random.default_rng(55)
    obs = np.repeat(ObstacleData.norm_obs(np.array([[SPLIT, 0.0]])), 300, axis=0)
    counts = [1, 2, 4, 8, 16, 32, 50]
    res: dict[str, list[float]] = {'diffusion': [], 'flow': []}
    fence: dict[str, list[float]] = {'diffusion': [], 'flow': []}
    near = (np.abs(d.obs_raw[:, 0] - SPLIT) < 0.8) & (np.abs(d.obs_raw[:, 1]) < 1.2)
    real = d.to_norm(d.chunks_raw[near])[::3]
    others = d.to_norm(d.chunks_raw[near])[1::7]
    dd = np.sqrt(((others[:, None, :] - real[None, :, :]) ** 2).sum(2))
    dd[dd < 1e-6] = 1e9
    base = float(dd.min(1).mean())
    sides_real = np.abs(d.chunks_raw[near][1::7].cumsum(1)[:, :, 1]).max(1)
    cut = float(np.percentile(sides_real, 20))
    print(f'[df] a real chunk sits {base:.2f} from the nearest other real chunk, and '
          f'four real chunks in five swing more than {cut:.2f} cm sideways')
    for n in counts:
        for kind in ('diffusion', 'flow'):
            ch = p.ddim(obs, n, rng) if kind == 'diffusion' else p.euler(obs, n, rng)
            flat = d.to_norm(ch)
            dist = np.sqrt(((flat[:, None, :] - real[None, :, :]) ** 2).sum(2)).min(1)
            res[kind].append(float(dist.mean()))
            swing = np.abs(ch.cumsum(1)[:, :, 1]).max(1)
            fence[kind].append(float((swing < cut).mean() * 100))
        print(f'[df] {n:3d} passes: distance to the nearest real chunk, diffusion '
              f'{res["diffusion"][-1]:.2f}, flow {res["flow"][-1]:.2f}; chunks that sit '
              f'on the fence, diffusion {fence["diffusion"][-1]:.1f}%, flow '
              f'{fence["flow"][-1]:.1f}%')
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), facecolor='white')
    x = np.arange(len(counts))
    ax = axes[0]
    _plain(ax)
    ax.plot(x, res['diffusion'], 'o-', color=PURPLE, lw=2.2, ms=7, label='diffusion')
    ax.plot(x, res['flow'], 's-', color=TEAL, lw=2.2, ms=7, label='flow matching')
    ax.axhline(base, color=MUTED, ls=':', lw=1.6,
               label=f'a real chunk sits {base:.2f} away')
    for i in (0, 1, 2, len(counts) - 1):
        ax.text(x[i], res['diffusion'][i] * 1.04, f'{res["diffusion"][i]:.2f}',
                ha='center', fontsize=9, color=PURPLE)
        ax.text(x[i], res['flow'][i] * 0.96, f'{res["flow"][i]:.2f}', ha='center',
                fontsize=9, color=TEAL, va='top')
    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('passes through the network to make one chunk', fontsize=9.5)
    ax.set_ylabel('distance from the chunk made to the nearest real one', fontsize=9.5)
    ax.set_ylim(0, max(res['diffusion'] + res['flow']) * 1.12)
    ax.legend(fontsize=9.2, frameon=False)
    ax.set_title('How real the chunk is against how many passes it took',
                 fontsize=11.2, weight='bold')
    ax = axes[1]
    _plain(ax)
    w = 0.38
    ax.bar(x - w / 2, fence['diffusion'], width=w, color=PURPLE, alpha=0.85,
           label='diffusion')
    ax.bar(x + w / 2, fence['flow'], width=w, color=TEAL, alpha=0.85,
           label='flow matching')
    for i in range(len(counts)):
        ax.text(x[i] - w / 2, fence['diffusion'][i] + 1.5, f'{fence["diffusion"][i]:.0f}',
                ha='center', fontsize=8.4, color=PURPLE)
        ax.text(x[i] + w / 2, fence['flow'][i] + 1.5, f'{fence["flow"][i]:.0f}',
                ha='center', fontsize=8.4, color=TEAL)
    ax.axhline(20, color=MUTED, ls=':', lw=1.6)
    ax.text(len(counts) - 0.6, 22, 'one real chunk in five is this straight',
            fontsize=8.8, color=MUTED, ha='right')
    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('passes through the network to make one chunk', fontsize=9.5)
    ax.set_ylabel('chunks that sit on the fence (per cent)', fontsize=9.5)
    ax.set_ylim(0, max(fence['diffusion'] + fence['flow'] + [25]) * 1.25)
    ax.legend(fontsize=9.2, frameon=False, loc='upper right')
    ax.set_title('With too few passes the answer slides back to the middle',
                 fontsize=11.2, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'steps-versus-quality.svg')


ENCODE_MS: float = 11.0
PASS_MS: float = 6.0
SEND_MS: float = 2.0


def timing_table() -> None:
    counts = [1, 2, 4, 8, 16, 32, 50, 100]
    budget = EXEC2 / RATE * 1000.0
    tight = 3 / RATE * 1000.0
    print(f'[df] stated costs: {ENCODE_MS:.0f} ms to turn the pictures into numbers, '
          f'{PASS_MS:.0f} ms a pass, {SEND_MS:.0f} ms to send')
    print(f'[df] playing {EXEC2} steps at {RATE:.0f} Hz gives {budget:.1f} ms; '
          f'playing 3 gives {tight:.1f} ms')
    totals = []
    for n in counts:
        tot = ENCODE_MS + PASS_MS * n + SEND_MS
        totals.append(tot)
        print(f'[df]   {n:3d} passes: {tot:6.1f} ms  '
              f'{"fits" if tot <= budget else "too slow"} in {budget:.0f} ms, '
              f'{"fits" if tot <= tight else "too slow"} in {tight:.0f} ms')
    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(len(counts))
    cols = [SLIDE if t <= tight else (LINK if t <= budget else GRIP) for t in totals]
    ax.bar(x, totals, color=cols, width=0.6, alpha=0.9)
    for i, t in enumerate(totals):
        ax.text(i, t + 8, f'{t:.0f}', ha='center', fontsize=9.2, color=INK)
    ax.axhline(budget, color=INK, lw=1.6, ls='--')
    ax.text(len(counts) - 0.4, budget + 10, f'{budget:.0f} ms: the time {EXEC2} steps '
                                            f'of the last chunk last', fontsize=9.2,
            ha='right', color=INK)
    ax.axhline(tight, color=GRIP, lw=1.6, ls=':')
    ax.text(len(counts) - 0.4, tight + 10, f'{tight:.0f} ms: the time 3 steps last',
            fontsize=9.2, ha='right', color=GRIP)
    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('passes through the network to make one chunk', fontsize=9.5)
    ax.set_ylabel('time to make one chunk (milliseconds)', fontsize=9.5)
    ax.set_ylim(0, max(totals) * 1.12)
    ax.set_title(f'At {PASS_MS:.0f} ms a pass, {ENCODE_MS:.0f} ms for the pictures and '
                 f'{SEND_MS:.0f} ms to send', fontsize=11.8, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'timing-table.svg')


# --------------------------------------------------------------------------
# page 2, section 5 --- receding horizon
# --------------------------------------------------------------------------

def receding_horizon() -> None:
    gen = ENCODE_MS + PASS_MS * 4 + SEND_MS
    play = EXEC2 / RATE * 1000.0
    chunk_ms = CHUNK2 / RATE * 1000.0
    print(f'[df] receding horizon: a chunk covers {chunk_ms:.0f} ms, '
          f'{EXEC2} steps of it are played in {play:.1f} ms, and making the next one '
          f'takes {gen:.0f} ms, which leaves {play - gen:.1f} ms of slack')
    fig, ax = plt.subplots(figsize=(12.0, 4.6), facecolor='white')
    ax.axis('off')
    ax.set_xlim(-90, 1150)
    ax.set_ylim(-0.8, 4.2)
    cols = [LINK, TEAL, PURPLE, WRIST]
    for c in range(4):
        t0 = c * play
        ax.add_patch(plt.Rectangle((t0, 3.0), chunk_ms, 0.34, facecolor=cols[c],
                                   alpha=0.16, edgecolor=cols[c], lw=1.0))
        ax.add_patch(plt.Rectangle((t0, 3.0), play, 0.34, facecolor=cols[c], alpha=0.65,
                                   edgecolor=cols[c], lw=1.0))
        ax.add_patch(plt.Rectangle((t0 - gen, 2.0), gen, 0.34, facecolor=cols[c],
                                   alpha=0.85, edgecolor=cols[c], lw=1.0))
        ax.text(t0 - gen / 2, 1.85, f'{gen:.0f} ms', ha='center', va='top', fontsize=8.4,
                color=cols[c])
        _arrow(ax, (t0 - gen / 2, 2.38), (t0 + play / 2, 2.96), cols[c], lw=1.1)
        ax.text(t0 + play / 2, 3.17, f'chunk {c + 1}', ha='center', va='center',
                fontsize=9, color='white' if c < 3 else INK, weight='bold')
    ax.text(-85, 3.17, 'what the arm plays', fontsize=9.8, va='center')
    ax.text(-85, 2.17, 'what the computer does', fontsize=9.8, va='center')
    ax.plot([-gen, 1100], [1.3, 1.3], color=INK, lw=1.2)
    for ms in range(0, 1101, 200):
        ax.plot([ms, ms], [1.22, 1.38], color=INK, lw=1.2)
        ax.text(ms, 1.1, f'{ms} ms', ha='center', fontsize=8.8, va='top')
    ax.text(0, 0.45, f'pale part: the {chunk_ms - play:.0f} ms of each chunk that is '
                     f'worked out and then thrown away', fontsize=9.2, color=MUTED)
    ax.set_title(f'A chunk of {CHUNK2} steps is made every {play:.0f} ms and only its '
                 f'first {EXEC2} steps are played', fontsize=12.0, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'receding-horizon.svg')


def late_chunk() -> None:
    play = EXEC2 / RATE * 1000.0
    fast = ENCODE_MS + PASS_MS * 4 + SEND_MS
    slow = ENCODE_MS + PASS_MS * 50 + SEND_MS
    print(f'[df] with 50 passes the chunk takes {slow:.0f} ms, which is '
          f'{slow - play:.0f} ms longer than the {play:.0f} ms of movement in hand, '
          f'so the arm waits {slow - play:.0f} ms in every cycle')
    fig, axes = plt.subplots(2, 1, figsize=(11.6, 5.0), facecolor='white')
    for ax, gen, nm, col in ((axes[0], fast, f'4 passes, {fast:.0f} ms', SLIDE),
                             (axes[1], slow, f'50 passes, {slow:.0f} ms', GRIP)):
        ax.axis('off')
        ax.set_xlim(-60, 1250)
        ax.set_ylim(-0.2, 2.3)
        t = 0.0
        for c in range(3):
            ax.add_patch(plt.Rectangle((t, 1.2), play, 0.4, facecolor=LINK, alpha=0.6,
                                       edgecolor=LINK))
            ax.text(t + play / 2, 1.4, f'chunk {c + 1} plays', ha='center', va='center',
                    fontsize=8.8, color='white')
            ax.add_patch(plt.Rectangle((t, 0.5), gen, 0.4, facecolor=col, alpha=0.85,
                                       edgecolor=col))
            ax.text(t + gen / 2, 0.7, f'{gen:.0f} ms', ha='center', va='center',
                    fontsize=8.6, color='white')
            if gen > play:
                ax.add_patch(plt.Rectangle((t + play, 1.2), gen - play, 0.4,
                                           facecolor=GRIP, alpha=0.3, hatch='///',
                                           edgecolor=GRIP))
                ax.text(t + play + (gen - play) / 2, 1.75, f'arm waits\n{gen - play:.0f} ms',
                        ha='center', fontsize=8.6, color=GRIP)
                t += gen
            else:
                t += play
        ax.text(-55, 1.4, 'arm', fontsize=9.5, va='center')
        ax.text(-55, 0.7, 'network', fontsize=9.5, va='center')
        ax.set_title(nm, fontsize=11.2, weight='bold', loc='left')
    fig.suptitle(f'The same chunk, made two ways, against {play:.0f} ms of movement in '
                 f'hand', fontsize=12.2, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'late-chunk.svg')


def latency_stack() -> None:
    play = EXEC2 / RATE * 1000.0
    counts = [2, 4, 8, 16]
    fig, ax = plt.subplots(figsize=(11.2, 4.8), facecolor='white')
    _plain(ax)
    parts = ['pictures into numbers', 'passes through the network', 'sending the chunk',
             'slack left over']
    cols = [WRIST, PURPLE, SLIDE, GRID]
    for i, n in enumerate(counts):
        vals = [ENCODE_MS, PASS_MS * n, SEND_MS]
        vals.append(max(play - sum(vals), 0.0))
        left = 0.0
        for v, col, nm in zip(vals, cols, parts):
            ax.barh([i], [v], left=[left], color=col, height=0.55, alpha=0.9,
                    label=nm if i == 0 else None, edgecolor='white')
            if v > 18:
                ax.text(left + v / 2, i, f'{v:.0f}', ha='center', va='center',
                        fontsize=9, color=INK if col == GRID else 'white')
            left += v
        print(f'[df] {n:2d} passes: {ENCODE_MS:.0f} + {PASS_MS * n:.0f} + {SEND_MS:.0f} '
              f'= {sum(vals[:3]):.0f} ms used of {play:.0f} ms, '
              f'{vals[3]:.0f} ms spare')
    ax.axvline(play, color=INK, lw=1.6, ls='--')
    ax.text(play + 4, len(counts) - 0.4, f'{play:.0f} ms', fontsize=9.5, color=INK)
    ax.set_yticks(np.arange(len(counts)))
    ax.set_yticklabels([f'{n} passes' for n in counts], fontsize=9.5)
    ax.set_xlabel('milliseconds of the time the last chunk bought', fontsize=9.5)
    ax.set_xlim(0, play * 1.12)
    ax.legend(fontsize=9.0, frameon=False, ncol=4, loc='upper center',
              bbox_to_anchor=(0.5, 1.15))
    ax.set_title('Where the time inside one cycle goes', fontsize=11.8, weight='bold',
                 pad=26)
    fig.tight_layout()
    _save(fig, DF_DOC, 'latency-stack.svg')


# --------------------------------------------------------------------------
# page 2, section 6 --- what they still cannot do
# --------------------------------------------------------------------------

def copied_mistake() -> None:
    p = _pol()
    d = p.data
    rng = np.random.default_rng(66)
    path = obst_rollout('diffusion', 60, rng)
    demo_sp = np.linalg.norm(np.diff(d.paths, axis=0), axis=2) * RATE
    demo_x = d.paths[:-1, :, 0]
    roll_sp = np.linalg.norm(np.diff(path, axis=0), axis=2) * RATE
    roll_x = path[:-1, :, 0]
    bins = np.linspace(0, 40, 41)
    centres = (bins[:-1] + bins[1:]) / 2

    def profile(xs: Arr, sp: Arr) -> Arr:
        idx = np.clip(np.digitize(xs.ravel(), bins) - 1, 0, len(centres) - 1)
        out = np.zeros(len(centres))
        for b in range(len(centres)):
            m = idx == b
            out[b] = sp.ravel()[m].mean() if m.any() else np.nan
        return out

    dp, rp = profile(demo_x, demo_sp), profile(roll_x, roll_sp)
    win = (centres > 26) & (centres < 33)
    print(f'[df] the demonstrator slows from {np.nanmax(dp):.1f} cm/s to '
          f'{np.nanmin(dp[win]):.1f} cm/s at about {centres[win][np.nanargmin(dp[win])]:.0f} cm')
    print(f'[df] the policy slows to {np.nanmin(rp[win]):.1f} cm/s at the same place, '
          f'so it copied the pause')
    fig, ax = plt.subplots(figsize=(11.2, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(centres, dp, 'o-', color=LINK, lw=2.2, ms=5, label='the demonstrations')
    ax.plot(centres, rp, 's-', color=GRIP, lw=2.2, ms=5, label='the diffusion policy')
    ax.axvspan(26, 33, color=WRIST, alpha=0.15)
    ax.text(29.5, np.nanmax(dp) * 0.25, 'the demonstrator\nhesitates here', ha='center',
            fontsize=9.5, color=WRIST)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('speed of the gripper (cm a second)', fontsize=9.5)
    ax.set_ylim(0, np.nanmax(dp) * 1.2)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_title('Nothing in the training says to be quick, so the policy copies the '
                 'pause as carefully as the movement', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'copied-mistake.svg')


def no_notion_of_the_goal() -> None:
    rng = np.random.default_rng(88)
    path = obst_rollout('diffusion', 40, rng)
    moved = GOAL2 + np.array([0.0, 11.0])
    to_old = np.linalg.norm(path[-1] - GOAL2, axis=1).mean()
    to_new = np.linalg.norm(path[-1] - moved, axis=1).mean()
    print(f'[df] with the object moved {moved[1] - GOAL2[1]:.0f} cm sideways, the policy '
          f'still ends {to_old:.2f} cm from the old place and {to_new:.2f} cm from the '
          f'new one')
    fig, ax = plt.subplots(figsize=(11.2, 4.8), facecolor='white')
    _plain(ax)
    for i in range(40):
        ax.plot(path[:, i, 0], path[:, i, 1], color=LINK, lw=0.9, alpha=0.55)
    _draw_box(ax)
    ax.plot(*GOAL2, 'x', color=MUTED, ms=14, mew=3)
    ax.text(GOAL2[0], GOAL2[1] - 2.2, 'where the object\nwas in every demonstration',
            ha='center', fontsize=9.2, color=MUTED, va='top')
    ax.plot(*moved, '*', color=GRIP, ms=18)
    ax.text(moved[0], moved[1] + 1.2, 'where the object is now', ha='center',
            fontsize=9.5, color=GRIP)
    ax.annotate('', xy=(moved[0], moved[1] - 0.8), xytext=(GOAL2[0], GOAL2[1] + 0.8),
                arrowprops=dict(arrowstyle='<->', color=GRIP, lw=1.4))
    ax.text(GOAL2[0] + 0.8, (GOAL2[1] + moved[1]) / 2, f'{to_new:.1f} cm out',
            fontsize=9.5, color=GRIP, va='center')
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.set_ylim(-12, 18)
    ax.set_title('The policy has no idea there is an object: it goes where the hand '
                 'always went', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'no-notion-of-the-goal.svg')


def outside_the_demonstrations() -> None:
    offsets = [0.0, 3.0, 6.0, 10.0, 15.0]
    ends, hits = [], []
    for off in offsets:
        rng = np.random.default_rng(101)
        path = obst_rollout('diffusion', 60, rng, start_offset=off)
        ends.append(float(np.linalg.norm(path[-1] - GOAL2, axis=1).mean()))
        hits.append(float(hits_box(path).mean() * 100))
        print(f'[df] starting {off:4.1f} cm away from any demonstrated start: '
              f'ends {ends[-1]:5.2f} cm from the goal, {hits[-1]:5.1f} per cent hit the box')
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.7), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    _plain(ax)
    for off, col in zip(offsets, (LINK, TEAL, PURPLE, WRIST, GRIP)):
        rng = np.random.default_rng(101)
        path = obst_rollout('diffusion', 12, rng, start_offset=off)
        for i in range(12):
            ax.plot(path[:, i, 0], path[:, i, 1], color=col, lw=1.0, alpha=0.7,
                    label=f'start {off:.0f} cm out' if i == 0 else None)
    _draw_box(ax)
    ax.plot(*GOAL2, '*', color=INK, ms=16, zorder=7)
    ax.set_xlabel('distance along the reach (cm)', fontsize=9.5)
    ax.set_ylabel('sideways (cm)', fontsize=9.5)
    ax.legend(fontsize=8.6, frameon=False, loc='upper left', ncol=2)
    ax.set_ylim(-14, 26)
    ax.set_title('Starting where nobody ever started', fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.plot(offsets, ends, 'o-', color=GRIP, lw=2.2, ms=7)
    for o, e in zip(offsets, ends):
        ax.text(o, e * 1.06, f'{e:.1f}', ha='center', fontsize=9, color=GRIP)
    ax.set_xlabel('how far the start is from any demonstrated start (cm)', fontsize=9.5)
    ax.set_ylabel('distance from the goal at the end (cm)', fontsize=9.5)
    ax.set_ylim(0, max(ends) * 1.2)
    ax.set_title('It does not come back', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, DF_DOC, 'outside-the-demonstrations.svg')


# ==========================================================================
# main
# ==========================================================================

PAGE1 = [action_vector, control_loop, absolute_versus_delta,
         one_example, one_episode, dataset_size, hours_of_a_day,
         drift_paths, error_over_time, more_demos, unseen_inputs,
         chunk_timeline, chunk_drift, chunk_smoothness,
         act_shapes, act_attention_cost, act_output_block,
         temporal_ensembling, ensembling_weights_picture, chunk_length_trade]

PAGE2 = [two_ways_one_average, label_spread, averaging_rollouts,
         noising_a_chunk, denoiser_shapes, reverse_walk, conditioning,
         diffusion_rollouts, side_counts,
         straight_versus_curved, steps_versus_quality, timing_table,
         receding_horizon, late_chunk, latency_stack,
         copied_mistake, no_notion_of_the_goal, outside_the_demonstrations]


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking,
    and --only name1,name2 to redraw a few of them while working."""
    global PNG_DIR
    args = sys.argv[1:]
    only: list[str] = []
    while args:
        if args[0] == '--png' and len(args) > 1:
            PNG_DIR = pathlib.Path(args[1])
            PNG_DIR.mkdir(parents=True, exist_ok=True)
            args = args[2:]
        elif args[0] == '--cache' and len(args) > 1:
            globals()['CACHE'] = pathlib.Path(args[1])
            args = args[2:]
        elif args[0] == '--only' and len(args) > 1:
            only = args[1].split(',')
            args = args[2:]
        else:
            args = args[1:]
    drawn = 0
    for fn in PAGE1 + PAGE2:
        if only and fn.__name__ not in only:
            continue
        fn()
        drawn += 1
    print(f'wrote {drawn} diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
