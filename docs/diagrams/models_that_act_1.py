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


def _silu(x: Arr) -> Arr:
    return x / (1.0 + np.exp(-x))


def _dsilu(x: Arr) -> Arr:
    s = 1.0 / (1.0 + np.exp(-x))
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
        ax.text(n, v * 10 * 1.04, f'{v * 10:.3f} mm', ha='center', fontsize=9,
                color=LINK)
    ax.set_xscale('log')
    ax.set_xticks(list(sizes))
    ax.set_xticklabels([str(n) for n in sizes])
    ax.set_ylim(0, max(steps_err) * 10 * 1.2)
    ax.set_xlabel('demonstrations in the training set (log scale)', fontsize=9.5)
    ax.set_ylabel('error of one predicted step (mm)', fontsize=9.5, color=LINK)
    ax2 = ax.twinx()
    ax2.plot(sizes, finals, 's--', color=GRIP, lw=2.0, ms=7)
    for n, v in zip(sizes, finals):
        ax2.text(n, v * 0.93, f'{v:.2f} cm', ha='center', fontsize=9, color=GRIP,
                 va='top')
    ax2.set_ylim(0, max(finals) * 1.2)
    ax2.set_ylabel('distance from where it should be after 4 s (cm)', fontsize=9.5,
                   color=GRIP)
    ax2.tick_params(labelsize=9.5, colors=GRIP)
    ax.set_title('One step gets much better; the whole reach hardly does',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BC_DOC, 'more-demos.svg')


def unseen_inputs() -> None:
    s = _sim()
    t = np.arange(REACH_STEPS) * DT
    path, _c, gap = s.runs[1]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    keep = s.store.obs
    sub = np.random.default_rng(1).choice(len(keep), 2500, replace=False)
    ax.plot(keep[sub, 0], keep[sub, 1], '.', color=LINK_PALE, ms=2.6,
            label='where the demonstrations went')
    worst = int(np.argsort(np.linalg.norm(path - s.ref, axis=2)[-1])[-1])
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
    ax.set_title('Adding a camera adds tokens, and the work goes up with the square',
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
    ax.set_title(f'Even a {chunks[-1]}-step chunk gives the decoder '
                 f'{dec[-1] / c["enc_pairs"]:.2f} of an encoder layer\'s pairs',
                 fontsize=10.6, weight='bold')
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
    ax.plot(tt, ens_a[:, 1] * 10, color=LINK, lw=2.2,
            label=f'weighted average of up to {m}')
    ax.set_xlabel('time through the run (seconds)', fontsize=9.5)
    ax.set_ylabel('command, sideways part (mm)', fontsize=9.5)
    ax.legend(fontsize=9.2, frameon=False, loc='upper right')
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
# main
# ==========================================================================

PAGE1 = [action_vector, control_loop, absolute_versus_delta,
         one_example, one_episode, dataset_size, hours_of_a_day,
         drift_paths, error_over_time, more_demos, unseen_inputs,
         chunk_timeline, chunk_drift, chunk_smoothness,
         act_shapes, act_attention_cost, act_output_block,
         temporal_ensembling, ensembling_weights_picture, chunk_length_trade]

PAGE2: list = []


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
