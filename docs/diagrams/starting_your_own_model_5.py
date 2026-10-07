"""Generate the diagrams for one page of docs/05_neural-networks/13_starting-your-own-model/.

    05_recipes-for-models-that-act-and-predict.md
        -> images/starting-your-own-model/recipes-for-models-that-act-and-predict/

Run with:  pixi run python ../docs/diagrams/starting_your_own_model_5.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script prints
them all so the document can quote the same values.

The world is simulated. It is a flat table seen from above, with a gripper that
starts near one corner, a goal that can be anywhere in a patch of the table, and a
box in the way whose place also moves. A scripted demonstrator drives the gripper
to the goal round the box, with a different clearance, speed and shake every time,
and the recordings it makes are the training data. Everything done to those
recordings is real: the policies are networks trained by Adam in NumPy, the
diffusion policy is a real denoising diffusion model over action chunks, the
dynamics model is a real learned one-step predictor, the planner is real random
shooting, and the reinforcement-learned policy is found by a real cross-entropy
search against a reward. The file-size, person-hour, memory and timing figures are
arithmetic from stated assumptions, and the assumptions are printed with them.
"""

import os

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import pathlib                                                      # noqa: E402
import sys                                                          # noqa: E402

import matplotlib                                                   # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes                                    # noqa: E402
from matplotlib.figure import Figure                                # noqa: E402
from matplotlib.patches import Rectangle                            # noqa: E402
import matplotlib.pyplot as plt                                     # noqa: E402
import numpy as np                                                  # noqa: E402
from numpy.typing import NDArray                                    # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'starting-your-own-model')
DOC: str = 'recipes-for-models-that-act-and-predict'
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

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, name: str) -> None:
    out: pathlib.Path = IMAGES / DOC
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)


def _table_axes(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


# --------------------------------------------------------------------------
# the simulated table, the demonstrator and the recordings
# --------------------------------------------------------------------------

HZ: int = 30                     # commands a second
STEPS: int = 120                 # one episode is 4 seconds
TOL: float = 0.015               # a run succeeds within 15 mm of the goal
HW: float = 0.040                # half the box's width, metres
HH: float = 0.045                # half the box's depth, metres
GX: tuple[float, float] = (0.30, 0.50)      # where the goal can be, metres
GY: tuple[float, float] = (-0.06, 0.12)
OX: tuple[float, float] = (0.16, 0.24)      # where the box can be, metres
OY: tuple[float, float] = (-0.04, 0.04)
FIXED_BOX: tuple[float, float] = (0.20, 0.00)


class Style:
    """One demonstrator's habits: clearance, speed shape and hand shake."""

    def __init__(self, clear: float, clear_sd: float, warp: float, tremor: float) -> None:
        self.clear = clear
        self.clear_sd = clear_sd
        self.warp = warp
        self.tremor = tremor


PERSON_A: Style = Style(0.025, 0.006, 1.00, 0.0012)
PERSON_B: Style = Style(0.060, 0.006, 1.45, 0.0022)


def demos(n: int, rng: np.random.Generator, style: Style = PERSON_A,
          both_sides: bool = False, gx: tuple[float, float] = GX,
          gy: tuple[float, float] = GY, ox: tuple[float, float] = OX,
          oy: tuple[float, float] = OY,
          side_sign: float = 1.0) -> tuple[Arr, Arr, Arr, Arr]:
    """Record n demonstrations.

    Returns the gripper paths (n, STEPS+1, 2) in metres, the goals (n, 2), the
    box centres (n, 2) and the sideways swing each path used (n,).
    """
    start = rng.normal(0, 0.004, (n, 2))
    goal = np.stack([rng.uniform(*gx, n), rng.uniform(*gy, n)], 1)
    box = np.stack([rng.uniform(*ox, n), rng.uniform(*oy, n)], 1)
    t = np.linspace(0, 1, STEPS + 1)
    smooth = 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5
    warp = np.clip(rng.normal(style.warp, 0.08, (n, 1)), 0.5, 2.5)
    u = np.clip(smooth[None, :], 1e-9, 1.0) ** warp
    d = goal - start
    line = start[:, None, :] + u[:, :, None] * d[:, None, :]
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm = nrm / np.linalg.norm(nrm, axis=1, keepdims=True)
    clear = rng.normal(style.clear, style.clear_sd, n)
    side = rng.choice([-1.0, 1.0], n) if both_sides else np.full(n, side_sign)
    bump = np.sin(np.pi * u)
    # the smallest sideways swing that keeps the whole path clear of the box
    grid = np.linspace(0.0, 0.30, 61)
    amp = np.full(n, grid[-1]) * side
    done = np.zeros(n, bool)
    for a in grid:
        cand = line + (side[:, None] * a * bump)[:, :, None] * nrm[:, None, :]
        gapx = np.abs(cand[:, :, 0] - box[:, None, 0]) - HW
        gapy = np.abs(cand[:, :, 1] - box[:, None, 1]) - HH
        ok = ((gapx > clear[:, None] + 0.005) | (gapy > clear[:, None] + 0.005)).all(1)
        amp = np.where(ok & ~done, side * a, amp)
        done = done | ok
    path = line + (amp[:, None] * bump)[:, :, None] * nrm[:, None, :]
    shake = rng.normal(0, style.tremor, (n, STEPS + 1, 2))
    k = np.ones(5) / 5.0
    for i in range(2):
        shake[:, :, i] = np.apply_along_axis(
            lambda r: np.convolve(r, k, 'same'), 1, shake[:, :, i])
    shake[:, 0] = 0.0
    shake[:, -1] = 0.0
    return path + shake, goal, box, amp


def examples(path: Arr, goal: Arr, box: Arr, chunk: int) -> tuple[Arr, Arr]:
    """Turn recordings into training pairs: six numbers in, a chunk of steps out."""
    step = np.diff(path, axis=1)
    n = len(path)
    pad = np.concatenate([step, np.zeros((n, chunk, 2))], 1)
    task = np.concatenate([goal, box], 1)
    obs = np.concatenate([path[:, :STEPS, :], np.repeat(task[:, None, :], STEPS, 1)], 2)
    blk = np.stack([pad[:, s:s + chunk, :] for s in range(STEPS)], 1)
    return obs.reshape(-1, 6), blk.reshape(-1, chunk * 2)


# --------------------------------------------------------------------------
# a small network, trained by Adam on mini-batches
# --------------------------------------------------------------------------

def net_init(sizes: list[int], seed: int) -> list[list[Arr]]:
    rng = np.random.default_rng(seed)
    return [[rng.normal(0, np.sqrt(2.0 / a), (a, b)), np.zeros(b)]
            for a, b in zip(sizes[:-1], sizes[1:])]


def net_fwd(p: list[list[Arr]], x: Arr) -> tuple[Arr, list[Arr]]:
    h, acts = x, [x]
    for i, (w, b) in enumerate(p):
        z = h @ w + b
        h = np.tanh(z) if i < len(p) - 1 else z
        acts.append(h)
    return h, acts


def net_train(p: list[list[Arr]], X: Arr, Y: Arr, steps: int, batch: int,
              lr: float, seed: int, wd: float = 1e-6) -> list[list[Arr]]:
    """Squared-error training with Adam. Returns the same list, changed in place."""
    rng = np.random.default_rng(seed)
    m = [[np.zeros_like(w), np.zeros_like(b)] for w, b in p]
    v = [[np.zeros_like(w), np.zeros_like(b)] for w, b in p]
    for it in range(1, steps + 1):
        idx = rng.integers(0, len(X), batch)
        out, acts = net_fwd(p, X[idx])
        g = (out - Y[idx]) * (2.0 / batch)
        for i in range(len(p) - 1, -1, -1):
            w, b = p[i]
            gw = acts[i].T @ g + wd * w
            gb = g.sum(0)
            if i > 0:
                g = (g @ w.T) * (1 - acts[i] ** 2)
            for k, (par, gr) in enumerate(((w, gw), (b, gb))):
                m[i][k] = 0.9 * m[i][k] + 0.1 * gr
                v[i][k] = 0.999 * v[i][k] + 0.001 * gr ** 2
                par -= lr * (m[i][k] / (1 - 0.9 ** it)) / (
                    np.sqrt(v[i][k] / (1 - 0.999 ** it)) + 1e-8)
    return p


class Policy:
    """A trained chunk policy: six numbers in, `chunk` future steps out."""

    def __init__(self, p: list[list[Arr]], scale: float, chunk: int) -> None:
        self.p = p
        self.scale = scale
        self.chunk = chunk

    def __call__(self, obs: Arr) -> Arr:
        return net_fwd(self.p, obs)[0].reshape(len(obs), self.chunk, 2) * self.scale


def clone(path: Arr, goal: Arr, box: Arr, chunk: int, seed: int,
          steps: int = 3000, hidden: int = 128) -> Policy:
    """Behaviour cloning: fit a chunk policy to recorded moments."""
    X, Y = examples(path, goal, box, chunk)
    scale = float(Y.std())
    p = net_train(net_init([6, hidden, hidden, chunk * 2], seed), X, Y / scale,
                  steps, 256, 3e-3, seed + 1)
    return Policy(p, scale, chunk)


def run(pol: Policy, goal: Arr, box: Arr, play: int, rng: np.random.Generator,
        gain: float = 1.0, noise: float = 0.0008, lag: float = 0.0,
        move: tuple[int, Arr] | None = None) -> Arr:
    """Drive the gripper with the policy, playing `play` steps per decision."""
    m = len(goal)
    pos = rng.normal(0, 0.004, (m, 2))
    g = goal.copy()
    out = [pos.copy()]
    last = np.zeros((m, 2))
    t = 0
    while t < STEPS:
        blk = pol(np.concatenate([pos, g, box], 1))
        for j in range(min(play, pol.chunk)):
            if t >= STEPS:
                break
            if move is not None:
                hit_now = np.asarray(move[0]) == t
                if hit_now.any():
                    g = np.where(hit_now[:, None], g + move[1], g)
            last = (1 - lag) * blk[:, j, :] + lag * last
            pos = pos + gain * last + rng.normal(0, noise, (m, 2))
            out.append(pos.copy())
            t += 1
    return np.stack(out, 1)


def hits_box(paths: Arr, box: Arr) -> NDArray[np.bool_]:
    return ((np.abs(paths[:, :, 0] - box[:, None, 0]) < HW)
            & (np.abs(paths[:, :, 1] - box[:, None, 1]) < HH)).any(1)


def judge(paths: Arr, goal: Arr, box: Arr) -> tuple[Arr, NDArray[np.bool_], NDArray[np.bool_]]:
    """Final distance to the goal, whether the box was hit, and whether it worked."""
    d = np.linalg.norm(paths[:, -1, :] - goal, axis=1)
    c = hits_box(paths, box)
    return d, c, (d < TOL) & ~c


# --------------------------------------------------------------------------
# section 1: a policy by copying a person
# --------------------------------------------------------------------------

CAM_ROWS, CAM_COLS, CAMS = 480, 640, 2
FLOAT_BYTES = 4
JOINTS = 7                       # six joints and a gripper on a small arm
VIDEO_RATIO = 40                 # how much smaller the frames go as H.264 video


def one_demonstration_on_disk() -> None:
    """What one recorded demonstration is as files, in bytes."""
    frame = CAM_ROWS * CAM_COLS * 3
    frames = frame * CAMS * STEPS
    video = frames / VIDEO_RATIO
    numbers = (JOINTS * 2 + 1) * FLOAT_BYTES * STEPS      # state, action, timestamp
    sentence = len('put the block in the tray')
    total = video + numbers + sentence
    print(f'[files] one episode = {STEPS} steps at {HZ} Hz = {STEPS / HZ:.1f} s')
    print(f'[files] one camera frame {CAM_ROWS}x{CAM_COLS}x3 = {frame:,} bytes')
    print(f'[files] raw frames {frames:,} bytes = {frames / 1e6:.2f} MB')
    print(f'[files] as video at {VIDEO_RATIO}:1 = {video / 1e6:.2f} MB')
    print(f'[files] numbers {numbers:,} bytes; sentence {sentence} bytes')
    print(f'[files] one video file {video / 2e6:.2f} MB, one numbers file '
          f'{STEPS} rows')
    print(f'[files] episode on disk {total / 1e6:.2f} MB, of which pictures are '
          f'{100 * video / total:.4f} per cent')
    for n in (50, 200, 1000):
        print(f'[files] {n} episodes = {n * frames / 1e9:.2f} GB raw, '
              f'{n * total / 1e9:.3f} GB stored')

    # picture 1: one training example, cut out of one episode
    fig, ax = plt.subplots(figsize=(11.2, 4.4), facecolor='white')
    _table_axes(ax)
    ax.set_xlim(-34, STEPS + 4)
    ax.set_ylim(0.1, 5.05)
    lanes = [('top camera', 3.6, LINK), ('wrist camera', 2.8, LINK),
             (f'{JOINTS} joint readings', 2.0, SLIDE),
             (f'{JOINTS} commands', 1.2, JOINT)]
    for name, y, col in lanes:
        ax.add_patch(Rectangle((0, y), STEPS, 0.5, color=col, alpha=0.20))
        for s in range(0, STEPS + 1, 10):
            ax.plot([s, s], [y, y + 0.5], color='white', lw=0.9)
        ax.text(-3, y + 0.25, name, ha='right', va='center', fontsize=10.5, color=INK)
    t0, chunk_len = 46, 8
    ax.add_patch(Rectangle((t0, 1.95), 1.6, 2.20, color=GRIP, alpha=0.9, zorder=3))
    ax.add_patch(Rectangle((t0, 1.15), chunk_len, 0.60, color=GRIP, alpha=0.9, zorder=3))
    ax.plot([t0 + 0.8, t0 + 0.8], [4.15, 4.52], color=GRIP, lw=1.2)
    ax.text(t0 + 2.5, 4.56, 'one training example', fontsize=11, color=GRIP,
            weight='bold', va='bottom')
    ax.text(t0 + chunk_len + 3, 1.45, 'the commands after it', fontsize=9.5,
            color=GRIP, va='center')
    ax.plot([0, STEPS], [0.98, 0.98], color=MUTED, lw=1.0)
    for s in (0, 30, 60, 90, 120):
        ax.plot([s, s], [0.90, 0.98], color=MUTED, lw=1.0)
        ax.text(s, 0.82, str(s), ha='center', va='top', fontsize=9, color=MUTED)
    ax.text(STEPS / 2, 0.52, f'step of the episode: {STEPS} steps, '
                             f'{STEPS / HZ:.0f} seconds at {HZ} a second',
            ha='center', va='top', fontsize=10, color=INK)
    ax.set_title(f'One episode of {STEPS / HZ:.0f} seconds, and one example cut out of it',
                 fontsize=12, weight='bold')
    _save(fig, 'one-training-example.svg')

    # picture 2: where the bytes of one episode go
    fig, ax = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(ax)
    names = ['raw frames', 'frames as\nvideo', 'joint and action\nnumbers', 'task\nsentence']
    vals = [frames, video, numbers, sentence]
    cols = [GRIP, LINK, SLIDE, JOINT]
    ax.bar(names, vals, color=cols, width=0.62)
    ax.set_yscale('log')
    ax.set_ylim(1, frames * 12)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.6, f'{v:,.0f} B' if v < 1e6 else f'{v / 1e6:,.1f} MB',
                ha='center', fontsize=10, color=INK)
    ax.set_ylabel('bytes for one episode (log scale)', fontsize=10)
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f'The pictures are {100 * video / total:.2f} per cent of what you store',
                 fontsize=12, weight='bold')
    _save(fig, 'where-the-bytes-go.svg')


RESET_S, CHECK_S, SPOIL = 18.0, 6.0, 6      # seconds, and one take in six is thrown away


def hours_of_a_person() -> None:
    """The cost of a demonstration in a person's time."""
    move = STEPS / HZ
    raw = move + RESET_S + CHECK_S
    per = raw * SPOIL / (SPOIL - 1)
    per_hour = 3600.0 / per
    print(f'[hours] one take = {move:.1f} s moving + {RESET_S:.0f} s resetting + '
          f'{CHECK_S:.0f} s checking = {raw:.1f} s')
    print(f'[hours] one in {SPOIL} spoiled, so one usable episode costs {per:.1f} s')
    print(f'[hours] {per_hour:.1f} usable episodes an hour = '
          f'{per_hour * STEPS:,.0f} training examples an hour')
    for n in (50, 200, 1000, 5000):
        print(f'[hours] {n:5d} episodes = {n * per / 3600:6.2f} person-hours '
              f'({n * per / 3600 / 7:.2f} working days of 7 hours)')

    # picture 1: where the 33.6 seconds of one episode go
    fig, ax = plt.subplots(figsize=(9.4, 3.6), facecolor='white')
    _plain(ax)
    parts = [('moving the arm', move, LINK), ('putting the objects back', RESET_S, JOINT),
             ('checking and saving', CHECK_S, SLIDE),
             (f'the 1 take in {SPOIL} thrown away', per - raw, GRIP)]
    left = 0.0
    for name, w, c in parts:
        ax.barh([0], [w], left=left, color=c, height=0.5, label=f'{name} ({w:.1f} s)')
        if w > 3:
            ax.text(left + w / 2, 0, f'{w:.1f} s', ha='center', va='center',
                    fontsize=10, color='white', weight='bold')
        left += w
    ax.set_yticks([])
    ax.set_xlim(0, per * 1.02)
    ax.set_xlabel('seconds of one person\'s time', fontsize=10)
    ax.set_ylim(-0.45, 0.45)
    ax.legend(fontsize=9.5, frameon=False, loc='upper center', ncol=2,
              bbox_to_anchor=(0.5, -0.22))
    ax.set_title(f'One usable episode costs {per:.1f} seconds of a person',
                 fontsize=12, weight='bold')
    _save(fig, 'what-one-episode-costs.svg')

    # picture 2: what a pile of episodes costs in hours
    fig, ax = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(ax)
    ns = np.array([10, 20, 50, 100, 200, 500, 1000, 2000, 5000])
    hrs = ns * per / 3600.0
    ax.plot(ns, hrs, marker='o', color=PURPLE, lw=2)
    for n in (50, 200, 1000, 5000):
        h = n * per / 3600.0
        ax.annotate(f'{n}: {h:.1f} h', (n, h), textcoords='offset points',
                    xytext=(-8, 7), fontsize=9.5, color=INK, ha='right')
    ax.axhline(7.0, color=MUTED, ls='--', lw=1.1)
    ax.text(11, 7.6, 'one working day', fontsize=9, color=MUTED)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns], fontsize=9)
    ax.set_xlabel('usable episodes (log scale)', fontsize=10)
    ax.set_ylabel('person-hours (log scale)', fontsize=10)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0.06, 100)
    ax.set_title('Demonstrations cost hours of a person', fontsize=12, weight='bold')
    _save(fig, 'hours-of-a-person.svg')


SIZES: tuple[int, ...] = (5, 10, 20, 40, 80, 160, 320)
REPS: int = 4
EVAL: int = 300
PLAY: int = 8
CHUNK: int = 8


def _sweep(sizes: tuple[int, ...], vary_box: bool) -> tuple[Arr, Arr, Arr]:
    """Success of a cloned policy against the number of demonstrations."""
    ev = np.random.default_rng(555)
    if vary_box:
        _, gev, bev, _ = demos(EVAL, ev)
    else:
        _, gev, bev, _ = demos(EVAL, ev, ox=(FIXED_BOX[0],) * 2, oy=(FIXED_BOX[1],) * 2)
    mean, lo, hi = [], [], []
    for n in sizes:
        got = []
        for rep in range(REPS):
            r = np.random.default_rng(1000 + 31 * rep + n)
            if vary_box:
                pth, gl, bx, _ = demos(n, r)
            else:
                pth, gl, bx, _ = demos(n, r, ox=(FIXED_BOX[0],) * 2, oy=(FIXED_BOX[1],) * 2)
            pol = clone(pth, gl, bx, CHUNK, 40 + rep, steps=2500)
            paths = run(pol, gev, bev, PLAY, np.random.default_rng(900 + rep))
            got.append(float(judge(paths, gev, bev)[2].mean()))
        mean.append(float(np.mean(got)))
        lo.append(float(np.min(got)))
        hi.append(float(np.max(got)))
    return np.array(mean), np.array(lo), np.array(hi)


def success_against_demonstrations() -> None:
    """The measurement behind 'how many demonstrations do I need'."""
    fix = _sweep(SIZES, False)
    var = _sweep(SIZES, True)
    for name, (m, lo, hi) in (('box always in one place', fix), ('box moves as well', var)):
        print(f'[demos] {name}: ' + '  '.join(
            f'n={n}:{v:.3f}' for n, v in zip(SIZES, m)))
        reach = [n for n, v in zip(SIZES, m) if v >= 0.80]
        print(f'[demos] {name}: first size at or above 0.80 success = '
              f'{reach[0] if reach else "none"}, best = {m.max():.3f} at '
              f'n={SIZES[int(np.argmax(m))]}, spread at n=320 '
              f'{lo[-1]:.3f} to {hi[-1]:.3f}')
    print(f'[demos] each point is {REPS} fresh sets of demonstrations, each judged on '
          f'{EVAL} runs, success = within {TOL * 100:.1f} cm and no box hit')

    # picture 1: how success grows with the number of demonstrations
    fig, ax = plt.subplots(figsize=(7.8, 4.8), facecolor='white')
    _plain(ax)
    for (m, lo, hi), c, lab in ((fix, LINK, 'box always in the same place'),
                                (var, GRIP, 'box moves as well as the goal')):
        ax.fill_between(SIZES, lo, hi, color=c, alpha=0.16)
        ax.plot(SIZES, m, marker='o', color=c, lw=2.2, label=lab)
    ax.axhline(0.80, color=MUTED, ls='--', lw=1.1)
    ax.text(60, 0.70, 'useful: 4 runs in 5', fontsize=9.5, color=MUTED)
    ax.set_xscale('log')
    ax.set_xticks(SIZES)
    ax.set_xticklabels([str(s) for s in SIZES], fontsize=9.5)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel('demonstrations recorded (log scale)', fontsize=10)
    ax.set_ylabel('runs that reach the goal and miss the box', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_title('Success climbs steeply, then flattens', fontsize=12, weight='bold')
    _save(fig, 'success-against-demonstrations.svg')

    # picture 2: what the first useful policy costs in minutes of a person
    per = (STEPS / HZ + RESET_S + CHECK_S) * SPOIL / (SPOIL - 1)
    want = 0.80
    first_fix = next((n for n, v in zip(SIZES, fix[0]) if v >= want), SIZES[-1])
    first_var = next((n for n, v in zip(SIZES, var[0]) if v >= want), SIZES[-1])
    fig, ax = plt.subplots(figsize=(7.0, 4.6), facecolor='white')
    _plain(ax)
    names = ['box always in\nthe same place', 'box moves as\nwell as the goal']
    vals = [first_fix * per / 60.0, first_var * per / 60.0]
    bars = ax.bar(names, vals, color=[LINK, GRIP], width=0.5)
    for b, n_, v in zip(bars, (first_fix, first_var), vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2,
                f'{n_} demonstrations\n{v:.0f} minutes of a person',
                ha='center', fontsize=10.5, color=INK)
    ax.set_ylim(0, max(vals) * 1.45)
    ax.set_ylabel(f'minutes of one person at {per:.1f} s each', fontsize=10)
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_title("What the first useful policy costs in a person's time",
                 fontsize=12, weight='bold')
    print(f'[demos] reaching {want:.0%}: {first_fix} demonstrations with the box fixed '
          f'({first_fix * per / 60:.1f} min), {first_var} with the box moving '
          f'({first_var * per / 60:.1f} min)')
    _save(fig, 'minutes-for-the-first-useful-policy.svg')


def action_space_locked() -> None:
    """Why the action space has to be written down before any data is collected."""
    rng = np.random.default_rng(21)
    path, goal, box, _ = demos(120, rng)
    step = np.diff(path, axis=1)
    abs_range = float(path[:, :, 0].max() - path[:, :, 0].min())
    dlt_range = float(step[:, :, 0].max() - step[:, :, 0].min())
    print(f'[space] same recordings: gripper x spans {abs_range * 100:.2f} cm as places '
          f'to go to, and {dlt_range * 1000:.2f} mm as changes per step, a ratio of '
          f'{abs_range / dlt_range:.1f}')

    pol = clone(path, goal, box, CHUNK, 61, steps=2500)
    _, gev, bev, _ = demos(EVAL, np.random.default_rng(555))
    right = run(pol, gev, bev, PLAY, np.random.default_rng(7))
    d_right = judge(right, gev, bev)[0]

    # the same policy, read as places to go to instead of changes
    m = EVAL
    r2 = np.random.default_rng(7)
    pos = r2.normal(0, 0.004, (m, 2))
    out = [pos.copy()]
    t = 0
    while t < STEPS:
        blk = pol(np.concatenate([pos, gev, bev], 1))
        for j in range(PLAY):
            pos = blk[:, j, :] + r2.normal(0, 0.0008, (m, 2))
            out.append(pos.copy())
            t += 1
            if t >= STEPS:
                break
    d_abs = np.linalg.norm(np.stack(out, 1)[:, -1, :] - gev, axis=1)

    # the same policy with the two axes swapped, the commonest wiring mistake
    r3 = np.random.default_rng(7)
    pos = r3.normal(0, 0.004, (m, 2))
    out = [pos.copy()]
    t = 0
    while t < STEPS:
        blk = pol(np.concatenate([pos, gev, bev], 1))[:, :, ::-1]
        for j in range(PLAY):
            pos = pos + blk[:, j, :] + r3.normal(0, 0.0008, (m, 2))
            out.append(pos.copy())
            t += 1
            if t >= STEPS:
                break
    d_swap = np.linalg.norm(np.stack(out, 1)[:, -1, :] - gev, axis=1)
    print(f'[space] median final distance: as recorded {np.median(d_right) * 100:.2f} cm, '
          f'read as places {np.median(d_abs) * 100:.2f} cm, axes swapped '
          f'{np.median(d_swap) * 100:.2f} cm')

    # picture 1: one set of recordings, written down in the two conventions
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11.0, 4.3), facecolor='white')
    tt = np.arange(STEPS + 1) / HZ
    _plain(ax0)
    for i in range(6):
        ax0.plot(tt, path[i, :, 0] * 100, color=LINK, lw=1.4, alpha=0.85)
    ax0.set_xlabel('seconds', fontsize=10)
    ax0.set_ylabel('gripper along the table (cm)', fontsize=10)
    ax0.set_title(f'As places to go to: a span of {abs_range * 100:.0f} cm',
                  fontsize=11.5, weight='bold')
    ax0.grid(color=GRID, lw=0.6)
    ax0.set_axisbelow(True)
    _plain(ax1)
    for i in range(6):
        ax1.plot(tt[1:], step[i, :, 0] * 1000, color=SLIDE, lw=1.4, alpha=0.85)
    ax1.set_xlabel('seconds', fontsize=10)
    ax1.set_ylabel('change along the table per step (mm)', fontsize=10)
    ax1.set_title(f'As changes: a span of {dlt_range * 1000:.1f} mm',
                  fontsize=11.5, weight='bold')
    ax1.grid(color=GRID, lw=0.6)
    ax1.set_axisbelow(True)
    fig.suptitle('The same six recordings, written down two ways',
                 fontsize=12.5, weight='bold')
    _save(fig, 'places-or-changes.svg')

    # picture 2: one policy, three readings of its numbers
    fig, ax2 = plt.subplots(figsize=(6.6, 4.4), facecolor='white')
    _plain(ax2)
    labs = ['played as\nrecorded', 'read as places\nto go to', 'two axes\nswapped']
    vals = [float(np.median(d_right)) * 100, float(np.median(d_abs)) * 100,
            float(np.median(d_swap)) * 100]
    bars = ax2.bar(labs, vals, color=[SLIDE, GRIP, GRIP], width=0.55)
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03,
                 f'{v:.1f} cm', ha='center', fontsize=10.5, color=INK)
    ax2.set_ylim(0, max(vals) * 1.2)
    ax2.set_ylabel('median miss at the end (cm)', fontsize=10)
    ax2.grid(axis='y', color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('One trained policy, three readings of its numbers',
                  fontsize=11.5, weight='bold')
    _save(fig, 'action-space-locked.svg')


def two_demonstrators() -> None:
    """Two people's recordings are not the same data."""
    fixed = dict(gx=(0.42, 0.42), gy=(0.03, 0.03),
                 ox=(FIXED_BOX[0],) * 2, oy=(FIXED_BOX[1],) * 2)
    pa, ga, ba, _ = demos(60, np.random.default_rng(5), PERSON_A, **fixed)
    pb, gb, bb, _ = demos(60, np.random.default_rng(6), PERSON_B, **fixed)
    mid = STEPS // 2
    aa = np.diff(pa, axis=1)[:, mid:mid + CHUNK, :].reshape(60, -1)
    ab = np.diff(pb, axis=1)[:, mid:mid + CHUNK, :].reshape(60, -1)
    both = np.concatenate([aa, ab], 0)
    spread_a = float(np.sqrt(((aa - aa.mean(0)) ** 2).sum(1).mean()) * 1000)
    spread_m = float(np.sqrt(((both - both.mean(0)) ** 2).sum(1).mean()) * 1000)
    gap = float(np.linalg.norm(aa.mean(0) - ab.mean(0)) * 1000)
    print(f'[people] at the same moment of the same task, the spread of one chunk of '
          f'{CHUNK} steps is {spread_a:.2f} mm within one person and {spread_m:.2f} mm '
          f'across two, and the two people differ by {gap:.2f} mm')
    print(f'[people] so the best single answer is wrong by '
          f'{(spread_m / spread_a) ** 2:.2f} times as much, squared, on the mixed set')

    _, gev, bev, _ = demos(EVAL, np.random.default_rng(555))
    cases = []
    for lab, n_a, n_b, style_b, side_b in (
            ('80 from A', 80, 0, PERSON_B, 1.0),
            ('80 from B', 0, 80, PERSON_B, 1.0),
            ('40 from A, 40 from B', 40, 40, PERSON_B, 1.0),
            ('40 from A, 40 from B going round the other side', 40, 40,
             PERSON_B, -1.0)):
        got = []
        for rep in range(3):
            parts = []
            if n_a:
                parts.append(demos(n_a, np.random.default_rng(70 + rep), PERSON_A))
            if n_b:
                parts.append(demos(n_b, np.random.default_rng(90 + rep), style_b,
                                   side_sign=side_b))
            pth = np.concatenate([p[0] for p in parts], 0)
            gl = np.concatenate([p[1] for p in parts], 0)
            bx = np.concatenate([p[2] for p in parts], 0)
            pol = clone(pth, gl, bx, CHUNK, 50 + rep, steps=2500)
            paths = run(pol, gev, bev, PLAY, np.random.default_rng(900 + rep))
            got.append(float(judge(paths, gev, bev)[2].mean()))
        cases.append((lab, float(np.mean(got))))
        print(f'[people] {lab.replace(chr(10), " ")}: success {np.mean(got):.3f}')

    # picture 1: the two people's paths round the same box
    fig, ax0 = plt.subplots(figsize=(7.2, 4.6), facecolor='white')
    _plain(ax0)
    cx, cy = FIXED_BOX
    ax0.add_patch(Rectangle((cx - HW, cy - HH), 2 * HW, 2 * HH, color='#bbbbbb'))
    for i in range(12):
        ax0.plot(pa[i, :, 0], pa[i, :, 1], color=LINK, lw=1.3, alpha=0.8)
        ax0.plot(pb[i, :, 0], pb[i, :, 1], color=WRIST, lw=1.3, alpha=0.8)
    ax0.plot([], [], color=LINK, lw=2, label='person A')
    ax0.plot([], [], color=WRIST, lw=2, label='person B')
    ax0.plot(ga[0, 0], ga[0, 1], marker='*', ms=15, color=SLIDE)
    ax0.set_ylim(-0.06, 0.22)
    ax0.set_xlabel('along the table (m)', fontsize=10)
    ax0.set_ylabel('across the table (m)', fontsize=10)
    ax0.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax0.set_title('Same goal, same box, two people', fontsize=11.5, weight='bold')
    _save(fig, 'two-demonstrators.svg')

    # picture 2: what the two people answered at the same moment
    fig, ax1 = plt.subplots(figsize=(7.2, 4.4), facecolor='white')
    _plain(ax1)
    ax1.hist(np.linalg.norm(aa.reshape(60, CHUNK, 2), axis=2).sum(1) * 1000, bins=14,
             color=LINK, alpha=0.75, label='person A')
    ax1.hist(np.linalg.norm(ab.reshape(60, CHUNK, 2), axis=2).sum(1) * 1000, bins=14,
             color=WRIST, alpha=0.75, label='person B')
    ax1.set_xlabel(f'distance moved in the next {CHUNK} steps (mm)', fontsize=10)
    ax1.set_ylabel('recordings', fontsize=10)
    ax1.legend(fontsize=9.5, frameon=False)
    ax1.set_title(f'The same moment, {gap:.1f} mm apart', fontsize=11.5, weight='bold')
    _save(fig, 'the-same-moment-two-people.svg')

    # picture 3: four ways of gathering eighty recordings
    fig, ax2 = plt.subplots(figsize=(8.4, 4.2), facecolor='white')
    _plain(ax2)
    labs = [c[0] for c in cases]
    vals = [c[1] for c in cases]
    cols = [LINK, WRIST, PURPLE, GRIP]
    ax2.barh(range(len(labs)), vals, color=cols, height=0.40)
    ax2.set_yticks([])
    ax2.set_ylim(len(labs) - 0.5, -0.75)
    for i, v in enumerate(vals):
        ax2.text(0.01, i - 0.33, labs[i].replace(chr(10), ' '), va='bottom',
                 fontsize=9.5, color=INK)
        ax2.text(v + 0.02, i, f'{v:.2f}', va='center', fontsize=10.5, color=INK)
    ax2.set_xlim(0, 1.15)
    ax2.set_xlabel('runs that work, out of 1', fontsize=10)
    ax2.grid(axis='x', color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('Eighty recordings, four ways of getting them',
                  fontsize=11.5, weight='bold', loc='left')
    _save(fig, 'eighty-recordings-four-ways.svg')


# --------------------------------------------------------------------------
# section 2: a policy that writes a chunk of actions
# --------------------------------------------------------------------------

BIG_CHUNK: int = 32
PLAYS: tuple[int, ...] = (1, 2, 4, 8, 16, 32)
MODEL_MS: tuple[tuple[str, float], ...] = (('a small policy, 15 ms', 15.0),
                                           ('a diffusion policy, 60 ms', 60.0),
                                           ('a large model, 240 ms', 240.0))


def one_chunk_example() -> None:
    """What one training example is once the label is a block of future steps."""
    path, goal, box, _ = demos(4, np.random.default_rng(12))
    step = np.diff(path, axis=0 + 1)
    mid = step[0, 40:40 + BIG_CHUNK, :] * 1000
    tail = np.concatenate([step[0, 100:, :], np.zeros((BIG_CHUNK - 20, 2))], 0) * 1000
    padded = BIG_CHUNK - 1
    print(f'[chunk] one episode still gives {STEPS} examples, but each label is now '
          f'{BIG_CHUNK} steps x 2 numbers = {BIG_CHUNK * 2} numbers')
    print(f'[chunk] the last {padded} examples of every episode need padding, which is '
          f'{100 * padded / STEPS:.1f} per cent of them')
    for h in (1, 8, 16, 32, 64):
        print(f'[chunk] chunk of {h:2d}: {STEPS * h * 2:,} label numbers an episode, '
              f'{h - 1} padded examples')

    # picture 1: one label, and the padding at the end of an episode
    fig, axl = plt.subplots(figsize=(8.0, 4.8), facecolor='white')
    _plain(axl)
    k = np.arange(BIG_CHUNK)
    axl.plot(k, mid[:, 0], marker='o', ms=3.5, color=LINK, lw=1.8,
             label='along the table, from the middle')
    axl.plot(k, mid[:, 1], marker='o', ms=3.5, color=WRIST, lw=1.8,
             label='across the table, from the middle')
    axl.plot(k, tail[:, 0], color=LINK, lw=1.4, ls='--', alpha=0.8,
             label='along the table, from the last second')
    axl.plot(k, tail[:, 1], color=WRIST, lw=1.4, ls='--', alpha=0.8,
             label='across the table, from the last second')
    axl.axvspan(20, BIG_CHUNK - 1, color=GRIP, alpha=0.12)
    axl.set_ylim(-7.5, 11.5)
    axl.text(25.5, 1.1, 'padding: the episode ran out',
             fontsize=9.5, color=GRIP, ha='center')
    axl.set_xlabel(f'step within the chunk (0 to {BIG_CHUNK - 1})', fontsize=10)
    axl.set_ylabel('movement commanded (mm)', fontsize=10)
    axl.legend(fontsize=8.5, frameon=False, loc='upper left', ncol=1)
    axl.grid(color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title(f'One label: {BIG_CHUNK} future steps, {BIG_CHUNK * 2} numbers',
                  fontsize=12, weight='bold')
    _save(fig, 'one-chunk-example.svg')

    # picture 2: how many label numbers one episode carries
    fig, axr = plt.subplots(figsize=(7.4, 4.4), facecolor='white')
    _plain(axr)
    hs = [1, 8, 16, 32, 64]
    nums = [STEPS * h * 2 for h in hs]
    bars = axr.bar([str(h) for h in hs], nums, color=LINK_PALE, edgecolor=LINK, width=0.6)
    for b, h, v in zip(bars, hs, nums):
        axr.text(b.get_x() + b.get_width() / 2, v * 1.05, f'{v:,}',
                 ha='center', fontsize=10, color=INK)
    axr.set_yscale('log')
    axr.set_ylim(100, max(nums) * 4)
    axr.set_xlabel('steps in a chunk', fontsize=10)
    axr.set_ylabel('label numbers per episode (log scale)', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title(f'The same {STEPS} examples, a longer label each',
                  fontsize=12, weight='bold')
    _save(fig, 'label-numbers-per-episode.svg')


def chunk_length_trade() -> None:
    """How many steps to play before looking again, measured both ways."""
    path, goal, box, _ = demos(160, np.random.default_rng(77))
    pol = clone(path, goal, box, BIG_CHUNK, 81, steps=3000)
    _, gev, bev, _ = demos(EVAL, np.random.default_rng(555))
    shift = np.tile(np.array([[0.0, 0.08]]), (EVAL, 1))
    when = np.random.default_rng(32).integers(20, 100, EVAL)
    still, moved, coll = [], [], []
    for play in PLAYS:
        p1 = run(pol, gev, bev, play, np.random.default_rng(31))
        d1, c1, s1 = judge(p1, gev, bev)
        p2 = run(pol, gev, bev, play, np.random.default_rng(31), move=(when, shift))
        d2 = np.linalg.norm(p2[:, -1, :] - (gev + shift), axis=1)
        still.append(float(np.median(d1)) * 100)
        moved.append(float(np.median(d2)) * 100)
        coll.append(float(s1.mean()))
        print(f'[play] {play:2d} steps a decision, {int(np.ceil(STEPS / play)):3d} decisions '
              f'an episode: miss {still[-1]:.2f} cm, success {coll[-1]:.3f}, '
              f'miss when the goal moves {moved[-1]:.2f} cm')
    total = [a + b for a, b in zip(still, moved)]
    best = PLAYS[int(np.argmin(total))]
    print(f'[play] the two costs added are lowest at {best} steps a decision, which is '
          f'{1000 * best / HZ:.0f} ms of movement')

    # picture 1: what a long chunk costs when the goal moves part way through
    fig, axl = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axl)
    axl.plot(PLAYS, still, marker='o', color=LINK, lw=2, label='goal stays put')
    axl.plot(PLAYS, moved, marker='s', color=GRIP, lw=2,
             label='goal moves 8 cm part way through')
    axl.plot(PLAYS, total, marker='^', color=PURPLE, lw=1.6, ls='--', label='the two added')
    axl.axvline(best, color=MUTED, ls=':', lw=1.2)
    axl.text(9.0, max(total) * 0.80, f'the two added are\nlowest at {best} steps',
             fontsize=9.5, color=MUTED, ha='left', va='top')
    axl.set_xscale('log', base=2)
    axl.set_xticks(PLAYS)
    axl.set_xticklabels([str(p) for p in PLAYS], fontsize=9.5)
    axl.set_xlabel('steps played before the model is asked again', fontsize=10)
    axl.set_ylabel('median miss at the end (cm)', fontsize=10)
    axl.legend(fontsize=9.5, frameon=False, loc='upper left')
    axl.grid(color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('A long chunk cannot react when the goal moves',
                  fontsize=12, weight='bold')
    _save(fig, 'chunk-length-trade.svg')

    # picture 2: what a long chunk buys when nothing moves
    fig, axr = plt.subplots(figsize=(7.4, 4.4), facecolor='white')
    _plain(axr)
    axr.bar([str(p) for p in PLAYS], coll, color=SLIDE, width=0.6)
    for i, v in enumerate(coll):
        axr.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=10, color=INK)
    axr.set_ylim(0, 1.08)
    axr.set_xlabel('steps played before the model is asked again', fontsize=10)
    axr.set_ylabel('runs that work, out of 1', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('One policy, six ways of playing its answer', fontsize=12, weight='bold')
    _save(fig, 'success-against-chunk-length.svg')


def chunk_and_the_clock() -> None:
    """The chunk length is set by the clock, not by the model."""
    period = 1000.0 / HZ
    rows = []
    for name, ms in MODEL_MS:
        need = int(np.ceil(ms / period))
        rows.append((name, ms, need, need * period - ms))
        print(f'[clock] {name}: needs at least {need} step(s) a decision '
              f'({need * period:.1f} ms of movement), leaving {need * period - ms:.1f} ms spare')
    print(f'[clock] the arm wants a command every {period:.2f} ms at {HZ} a second')
    for p in PLAYS:
        print(f'[clock] playing {p:2d} steps buys {p * period:6.1f} ms of thinking time')

    fig, axl = plt.subplots(figsize=(8.2, 4.8), facecolor='white')
    _plain(axl)
    move_ms = [p * period for p in PLAYS]
    axl.bar([str(p) for p in PLAYS], move_ms, color=LINK_PALE, edgecolor=LINK, width=0.6,
            label='time the chunk covers')
    for name, ms in MODEL_MS:
        axl.axhline(ms, color={15.0: SLIDE, 60.0: JOINT, 240.0: GRIP}[ms], lw=1.6, ls='--')
        axl.text(5.45, ms * 1.08, name, fontsize=9.5, ha='right',
                 color={15.0: SLIDE, 60.0: JOINT, 240.0: GRIP}[ms],
                 bbox=dict(facecolor='white', edgecolor='none', pad=1.5))
    axl.set_yscale('log')
    axl.set_ylim(8, 2500)
    axl.set_xlabel('steps played before the model is asked again', fontsize=10)
    axl.set_ylabel('milliseconds (log scale)', fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title(f'At {HZ} commands a second, a chunk of {PLAYS[3]} covers '
                  f'{PLAYS[3] * period:.0f} ms', fontsize=12, weight='bold')
    _save(fig, 'chunk-and-the-clock.svg')


# --------------------------------------------------------------------------
# section 3: a policy that generates its answer
# --------------------------------------------------------------------------

DIFF_T: int = 100                # noise levels used in training
GEN_CHUNK: int = 16              # the chunk both section 3 policies produce
NARROW: dict[str, tuple[float, float]] = dict(gx=(0.38, 0.46), gy=(-0.015, 0.015),
                                              ox=(0.19, 0.21), oy=(-0.01, 0.01))


def _abar(T: int) -> Arr:
    """Cosine schedule: how much of the original is left at each noise level."""
    t = np.arange(T + 1) / T
    f = np.cos((t + 0.008) / 1.008 * np.pi / 2) ** 2
    return f / f[0]


class Diffusion:
    """A denoising diffusion model over one chunk of actions, trained in NumPy."""

    def __init__(self, p: list[list[Arr]], scale: float, chunk: int, abar: Arr,
                 omu: Arr, osd: Arr) -> None:
        self.p = p
        self.scale = scale
        self.chunk = chunk
        self.abar = abar
        self.omu = omu
        self.osd = osd

    def _eps(self, x: Arr, obs: Arr, t: int) -> Arr:
        frac = t / DIFF_T
        feats = np.tile(np.array([[frac, np.cos(np.pi * frac), np.sin(2 * np.pi * frac)]]),
                        (len(x), 1))
        return net_fwd(self.p, np.concatenate([x, (obs - self.omu) / self.osd, feats], 1))[0]

    def __call__(self, obs: Arr, passes: int = 16,
                 rng: np.random.Generator | None = None) -> Arr:
        rng = rng or np.random.default_rng(0)
        x = rng.normal(0, 1, (len(obs), self.chunk * 2))
        steps = np.linspace(DIFF_T, 0, passes + 1).astype(int)
        for a, b in zip(steps[:-1], steps[1:]):
            eps = self._eps(x, obs, a)
            x0 = (x - np.sqrt(1 - self.abar[a]) * eps) / np.sqrt(self.abar[a])
            x0 = np.clip(x0, -4, 4)
            x = np.sqrt(self.abar[b]) * x0 + np.sqrt(1 - self.abar[b]) * eps
        return x.reshape(len(obs), self.chunk, 2) * self.scale


def diffusion_fit(path: Arr, goal: Arr, box: Arr, chunk: int, seed: int,
                  steps: int = 16000, hidden: int = 320) -> Diffusion:
    X, Y = examples(path, goal, box, chunk)
    scale = float(Y.std())
    Y = Y / scale
    omu, osd = X.mean(0), X.std(0) + 1e-9
    X = (X - omu) / osd
    abar = _abar(DIFF_T)
    p = net_init([chunk * 2 + 6 + 3, hidden, hidden, chunk * 2], seed)
    rng = np.random.default_rng(seed + 3)
    m = [[np.zeros_like(w), np.zeros_like(b)] for w, b in p]
    v = [[np.zeros_like(w), np.zeros_like(b)] for w, b in p]
    batch = 256
    for it in range(1, steps + 1):
        idx = rng.integers(0, len(X), batch)
        y0, obs = Y[idx], X[idx]
        tt = rng.integers(1, DIFF_T + 1, batch)
        eps = rng.normal(0, 1, y0.shape)
        xt = np.sqrt(abar[tt])[:, None] * y0 + np.sqrt(1 - abar[tt])[:, None] * eps
        frac = tt / DIFF_T
        feats = np.stack([frac, np.cos(np.pi * frac), np.sin(2 * np.pi * frac)], 1)
        inp = np.concatenate([xt, obs, feats], 1)
        out, acts = net_fwd(p, inp)
        g = (out - eps) * (2.0 / batch)
        lr = 2e-3 * (0.05 + 0.95 * 0.5 * (1 + np.cos(np.pi * it / steps)))
        for i in range(len(p) - 1, -1, -1):
            w, b = p[i]
            gw = acts[i].T @ g
            gb = g.sum(0)
            if i > 0:
                g = (g @ w.T) * (1 - acts[i] ** 2)
            for k, (par, gr) in enumerate(((w, gw), (b, gb))):
                m[i][k] = 0.9 * m[i][k] + 0.1 * gr
                v[i][k] = 0.999 * v[i][k] + 0.001 * gr ** 2
                par -= lr * (m[i][k] / (1 - 0.9 ** it)) / (
                    np.sqrt(v[i][k] / (1 - 0.999 ** it)) + 1e-8)
    return Diffusion(p, scale, chunk, abar, omu, osd)


def run_diffusion(gen: Diffusion, goal: Arr, box: Arr, play: int,
                  rng: np.random.Generator, passes: int = 16) -> Arr:
    m = len(goal)
    pos = rng.normal(0, 0.004, (m, 2))
    out = [pos.copy()]
    t = 0
    while t < STEPS:
        blk = gen(np.concatenate([pos, goal, box], 1), passes=passes, rng=rng)
        for j in range(min(play, gen.chunk)):
            if t >= STEPS:
                break
            pos = pos + blk[:, j, :] + rng.normal(0, 0.0008, (m, 2))
            out.append(pos.copy())
            t += 1
    return np.stack(out, 1)


class Section3:
    """Everything section 3 measures, worked out once."""

    def __init__(self) -> None:
        self.two = demos(400, np.random.default_rng(301), both_sides=True, **NARROW)
        self.one = demos(400, np.random.default_rng(302), both_sides=False, **NARROW)
        self.ev = demos(EVAL, np.random.default_rng(303), **NARROW)
        self.reg_two = clone(*self.two[:3], GEN_CHUNK, 311, steps=3000)
        self.reg_one = clone(*self.one[:3], GEN_CHUNK, 312, steps=3000)
        self.gen_two = diffusion_fit(*self.two[:3], GEN_CHUNK, 321)
        self.gen_one = diffusion_fit(*self.one[:3], GEN_CHUNK, 322)


_S3: Section3 | None = None


def _s3() -> Section3:
    global _S3
    if _S3 is None:
        _S3 = Section3()
    return _S3


def two_answer_test() -> None:
    """The test that says whether a task needs a generated answer."""
    s = _s3()
    mid = 30
    out = {}
    for name, (path, goal, box, amp) in (('two ways', s.two), ('one way', s.one)):
        blk = np.diff(path, axis=1)[:, mid:mid + GEN_CHUNK, :]
        side = blk[:, :, 1].sum(1) * 1000
        mean = float(side.mean())
        near = float(np.min(np.abs(side - mean)))
        groups = [side[amp > 0], side[amp <= 0]]
        within = float(np.mean([g.std() for g in groups if len(g) > 3]))
        out[name] = (side, mean, near, within)
        print(f'[twoway] {name}: the mean of the labels is {mean:+.2f} mm, the nearest '
              f'label anybody recorded is {near:.2f} mm away, and the spread inside one '
              f'group is {within:.2f} mm, a ratio of {near / within:.2f}')

    # picture 1: the recordings themselves, and the average of them
    fig, ax0 = plt.subplots(figsize=(7.4, 4.6), facecolor='white')
    path, goal, box, _ = s.two
    _plain(ax0)
    ax0.add_patch(Rectangle((box[0, 0] - HW, box[0, 1] - HH), 2 * HW, 2 * HH,
                            color='#bbbbbb'))
    up = np.diff(path, axis=1)[:, mid:mid + GEN_CHUNK, 1].sum(1) > 0
    for i in np.where(up)[0][:25]:
        ax0.plot(path[i, :, 0], path[i, :, 1], color=LINK, lw=1.1, alpha=0.6)
    for i in np.where(~up)[0][:25]:
        ax0.plot(path[i, :, 0], path[i, :, 1], color=TEAL, lw=1.1, alpha=0.6)
    ax0.plot(path[:, :, 0].mean(0), path[:, :, 1].mean(0), color=GRIP, lw=3,
             label='the average of them all')
    ax0.set_xlabel('along the table (m)', fontsize=10)
    ax0.set_ylabel('across the table (m)', fontsize=10)
    ax0.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax0.set_title('Both ways round are right, and the average is neither',
                  fontsize=11.5, weight='bold')
    _save(fig, 'both-ways-round-are-right.svg')

    # picture 2: the same measurement on a two-answer task and a one-answer task
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.4), facecolor='white',
                                   gridspec_kw={'wspace': 0.26})
    for ax, name, col in ((ax1, 'two ways', TEAL), (ax2, 'one way', SLIDE)):
        _plain(ax)
        side, mean, near, within = out[name]
        ax.hist(side, bins=30, color=col, alpha=0.8)
        ax.axvline(mean, color=GRIP, lw=2.2)
        ax.set_xlabel(f'sideways movement over the next {GEN_CHUNK} steps (mm)',
                      fontsize=10)
        ax.set_ylabel('recorded moments', fontsize=10)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
        ax.text(mean, ax.get_ylim()[1] * 0.97, f' mean {mean:+.1f} mm', fontsize=9.5,
                color=GRIP, va='top')
        ax.set_title(f'{"Both ways recorded" if name == "two ways" else "One way recorded"}: '
                     f'{near:.1f} mm from any real label', fontsize=10.5, weight='bold')
    fig.suptitle('The same measurement at one moment, on two tasks',
                 fontsize=12.5, weight='bold')
    _save(fig, 'two-answer-test.svg')


def averaging_and_generating() -> None:
    """What the two kinds of policy do with the same recordings."""
    s = _s3()
    _, gev, bev, _ = s.ev
    reg = run(s.reg_two, gev, bev, PLAY, np.random.default_rng(41))
    gen = run_diffusion(s.gen_two, gev, bev, PLAY, np.random.default_rng(41), passes=16)
    d_r, c_r, s_r = judge(reg, gev, bev)
    d_g, c_g, s_g = judge(gen, gev, bev)
    up_g = (gen[:, :, 1].max(1) - gen[:, 0, 1]) > 0.03
    print(f'[gen] averaging policy: hits the box on {c_r.mean():.3f} of runs, '
          f'works on {s_r.mean():.3f}, median miss {np.median(d_r) * 100:.2f} cm')
    print(f'[gen] diffusion policy: hits the box on {c_g.mean():.3f} of runs, '
          f'works on {s_g.mean():.3f}, median miss {np.median(d_g) * 100:.2f} cm')
    print(f'[gen] the generated runs go above the box on {up_g.mean():.3f} of runs')

    # picture 1: the same table and the same box, driven by the two policies
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white',
                             gridspec_kw={'wspace': 0.24})
    for ax, paths, bad, name in ((axes[0], reg, c_r, 'One answer'),
                                 (axes[1], gen, c_g, 'Generated answer')):
        _plain(ax)
        ax.add_patch(Rectangle((bev[0, 0] - HW, bev[0, 1] - HH), 2 * HW, 2 * HH,
                               color='#bbbbbb'))
        for i in range(120):
            ax.plot(paths[i, :, 0], paths[i, :, 1],
                    color=GRIP if bad[i] else LINK, lw=1.0,
                    alpha=0.8 if bad[i] else 0.45)
        ax.set_xlabel('along the table (m)', fontsize=10)
        ax.set_ylabel('across the table (m)', fontsize=10)
        ax.set_ylim(-0.14, 0.14)
        ax.set_title(f'{name}: {bad.mean():.0%} hit the box',
                     fontsize=11.5, weight='bold')
    fig.suptitle('The same 400 recordings, the same box, two policies driving',
                 fontsize=12.5, weight='bold')
    _save(fig, 'averaging-and-generating.svg')

    # picture 2: the two policies counted
    fig, ax2 = plt.subplots(figsize=(7.0, 4.6), facecolor='white')
    _plain(ax2)
    labs = ['hits the box', 'reaches the goal\nand misses the box']
    reg_v = [float(c_r.mean()), float(s_r.mean())]
    gen_v = [float(c_g.mean()), float(s_g.mean())]
    x = np.arange(2)
    ax2.bar(x - 0.18, reg_v, width=0.34, color=GRIP, label='one answer')
    ax2.bar(x + 0.18, gen_v, width=0.34, color=LINK, label='generated answer')
    for xi, v in zip(x - 0.18, reg_v):
        ax2.text(xi, v + 0.02, f'{v:.2f}', ha='center', fontsize=10, color=INK)
    for xi, v in zip(x + 0.18, gen_v):
        ax2.text(xi, v + 0.02, f'{v:.2f}', ha='center', fontsize=10, color=INK)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labs, fontsize=9.5)
    ax2.set_ylim(0, 1.1)
    ax2.set_ylabel('share of 300 runs', fontsize=10)
    ax2.legend(fontsize=9.5, frameon=False, loc='upper center')
    ax2.grid(axis='y', color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('The same 400 recordings, two policies counted',
                  fontsize=11.5, weight='bold')
    _save(fig, 'box-hits-and-successes.svg')


def what_generating_costs() -> None:
    """On a task with one right answer, generating buys nothing and costs passes."""
    s = _s3()
    _, gev, bev, _ = s.ev
    reg = run(s.reg_one, gev, bev, PLAY, np.random.default_rng(43))
    s_reg = float(judge(reg, gev, bev)[2].mean())
    passes = (1, 2, 4, 8, 16, 32)
    succ, miss = [], []
    for k in passes:
        paths = run_diffusion(s.gen_one, gev, bev, PLAY, np.random.default_rng(43), passes=k)
        d, c, ok = judge(paths, gev, bev)
        succ.append(float(ok.mean()))
        miss.append(float(np.median(d)) * 100)
        print(f'[cost] one right answer, {k:2d} passes: success {succ[-1]:.3f}, '
              f'median miss {miss[-1]:.2f} cm')
    print(f'[cost] the plain policy on the same recordings: success {s_reg:.3f}, '
          f'and it needs one pass')
    period = 1000.0 / HZ
    per_pass = 3.0
    for k in passes:
        need = int(np.ceil(k * per_pass / period))
        print(f'[cost] at {per_pass:.0f} ms a pass, {k:2d} passes take {k * per_pass:.0f} ms '
              f'and need a chunk of at least {need} step(s)')

    # picture 1: what the passes buy on a task with one right answer
    fig, axl = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axl)
    axl.plot(passes, succ, marker='o', color=LINK, lw=2, label='generated answer')
    axl.axhline(s_reg, color=GRIP, lw=1.8, ls='--', label='one answer, one pass')
    axl.set_xscale('log', base=2)
    axl.set_xticks(passes)
    axl.set_xticklabels([str(k) for k in passes], fontsize=9.5)
    axl.set_ylim(0, 1.05)
    axl.set_xlabel('passes through the network for one chunk', fontsize=10)
    axl.set_ylabel('runs that work, out of 1', fontsize=10)
    axl.legend(fontsize=9.5, frameon=False, loc='lower right')
    axl.grid(color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('When there is one right answer, generating adds nothing',
                  fontsize=12, weight='bold')
    _save(fig, 'what-generating-costs.svg')

    # picture 2: what the passes cost in milliseconds
    fig, axr = plt.subplots(figsize=(7.4, 4.4), facecolor='white')
    _plain(axr)
    ms = [k * per_pass for k in passes]
    axr.bar([str(k) for k in passes], ms, color=LINK_PALE, edgecolor=LINK, width=0.6)
    axr.axhline(PLAY * period, color=SLIDE, lw=1.8, ls='--')
    axr.text(0.1, PLAY * period * 1.06, f'what a chunk of {PLAY} covers: '
                                        f'{PLAY * period:.0f} ms', fontsize=9.5, color=SLIDE)
    for i, v in enumerate(ms):
        axr.text(i, v + 2, f'{v:.0f}', ha='center', fontsize=10, color=INK)
    axr.set_ylim(0, max(max(ms), PLAY * period) * 1.3)
    axr.set_xlabel('passes through the network for one chunk', fontsize=10)
    axr.set_ylabel(f'milliseconds, at {per_pass:.0f} ms a pass', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('Every pass takes time out of the chunk', fontsize=12, weight='bold')
    _save(fig, 'passes-cost-milliseconds.svg')


def too_few_passes() -> None:
    """The mistake: cutting the passes to meet the clock, on a two-answer task."""
    s = _s3()
    _, gev, bev, _ = s.ev
    passes = (1, 2, 4, 8, 16, 32)
    coll, done = [], []
    keep = {}
    for k in passes:
        paths = run_diffusion(s.gen_two, gev, bev, PLAY, np.random.default_rng(47), passes=k)
        d, c, ok = judge(paths, gev, bev)
        coll.append(float(c.mean()))
        done.append(float(ok.mean()))
        if k in (2, 16):
            keep[k] = (paths, c)
        print(f'[passes] two right answers, {k:2d} passes: hits the box {coll[-1]:.3f}, '
              f'works {done[-1]:.3f}, median miss {np.median(d) * 100:.2f} cm')

    # picture 1: the same policy and the same box, at two pass counts
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white',
                             gridspec_kw={'wspace': 0.24})
    for ax, k in zip(axes, (2, 16)):
        _plain(ax)
        paths, bad = keep[k]
        ax.add_patch(Rectangle((bev[0, 0] - HW, bev[0, 1] - HH), 2 * HW, 2 * HH,
                               color='#bbbbbb'))
        for i in range(120):
            ax.plot(paths[i, :, 0], paths[i, :, 1],
                    color=GRIP if bad[i] else LINK, lw=1.0,
                    alpha=0.8 if bad[i] else 0.45)
        ax.set_ylim(-0.16, 0.16)
        ax.set_xlabel('along the table (m)', fontsize=10)
        ax.set_ylabel('across the table (m)', fontsize=10)
        ax.set_title(f'{k} passes: works on {done[passes.index(k)]:.2f} of runs',
                     fontsize=11, weight='bold')
    fig.suptitle('One generating policy, the same box, two numbers of passes',
                 fontsize=12.5, weight='bold')
    _save(fig, 'too-few-passes.svg')

    # picture 2: the passes counted against what they produce
    fig, axr = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(axr)
    axr.plot(passes, done, marker='o', color=SLIDE, lw=2, label='works')
    axr.plot(passes, coll, marker='s', color=GRIP, lw=2, label='hits the box')
    axr.set_xscale('log', base=2)
    axr.set_xticks(passes)
    axr.set_xticklabels([str(k) for k in passes], fontsize=9.5)
    axr.set_ylim(0, 1.05)
    axr.set_xlabel('passes through the network for one chunk', fontsize=10)
    axr.set_ylabel('share of 300 runs', fontsize=10)
    axr.legend(fontsize=9.5, frameon=False, loc='center right')
    axr.grid(color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('Cutting the passes destroys the policy', fontsize=12, weight='bold')
    _save(fig, 'passes-and-box-hits.svg')


# --------------------------------------------------------------------------
# section 4: a model that is told the job in words
# --------------------------------------------------------------------------

WIDTH: int = 1024                # how wide one attention matrix is, assumed
BLOCKS: int = 24                 # how many blocks carry adapters, assumed
PER_BLOCK: int = 4               # how many square matrices in a block carry one
W_BYTES, G_BYTES, OPT_BYTES = 2, 2, 8


def what_fine_tuning_costs() -> None:
    """The memory arithmetic that decides whether you can fine-tune at all."""
    sizes = (('a small one, 450 million weights', 450e6),
             ('a large one, 7 billion weights', 7e9))
    rank = 16
    per_mat = 2 * WIDTH * rank
    adapter = BLOCKS * PER_BLOCK * per_mat
    print(f'[tune] an adapter of rank {rank} on {BLOCKS} blocks x {PER_BLOCK} matrices of '
          f'{WIDTH}x{WIDTH}: {per_mat:,} weights a matrix, {adapter:,} in all, which is '
          f'{100 * per_mat / WIDTH ** 2:.2f} per cent of each matrix')
    full, part = [], []
    for name, n in sizes:
        f = n * (W_BYTES + G_BYTES + OPT_BYTES)
        a = n * W_BYTES + adapter * (W_BYTES + G_BYTES + OPT_BYTES)
        full.append(f / 1e9)
        part.append(a / 1e9)
        print(f'[tune] {name}: training every weight needs {f / 1e9:.2f} GB, '
              f'training only the adapter needs {a / 1e9:.2f} GB, '
              f'{f / a:.1f} times less')

    # picture 1: what has to fit in the graphics card
    fig, axl = plt.subplots(figsize=(7.6, 4.8), facecolor='white')
    _plain(axl)
    x = np.arange(2)
    axl.bar(x - 0.18, full, width=0.34, color=GRIP, label='train every weight')
    axl.bar(x + 0.18, part, width=0.34, color=LINK, label=f'train a rank-{rank} adapter')
    for xi, v in zip(x - 0.18, full):
        axl.text(xi, v * 1.08, f'{v:.1f} GB', ha='center', fontsize=10, color=INK)
    for xi, v in zip(x + 0.18, part):
        axl.text(xi, v * 1.08, f'{v:.2f} GB', ha='center', fontsize=10, color=INK)
    axl.set_xticks(x)
    axl.set_xticklabels(['450 million\nweights', '7 billion\nweights'], fontsize=10)
    axl.set_yscale('log')
    axl.set_ylim(0.3, 400)
    axl.set_ylabel('memory for the weights, their gradients\nand the optimiser (GB, log scale)',
                   fontsize=10)
    axl.legend(fontsize=9.5, frameon=False, loc='upper left')
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('What has to fit in the graphics card', fontsize=12, weight='bold')
    _save(fig, 'what-fine-tuning-costs.svg')

    # picture 2: the rank decides how many weights are trained
    fig, axr = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(axr)
    ranks = [4, 8, 16, 32, 64]
    counts = [BLOCKS * PER_BLOCK * 2 * WIDTH * r for r in ranks]
    millions = [c / 1e6 for c in counts]
    axr.bar([str(r) for r in ranks], millions, color=LINK_PALE, edgecolor=LINK, width=0.6)
    for i, (r, c) in enumerate(zip(ranks, counts)):
        axr.text(i, c / 1e6 * 1.04, f'{c / 1e6:.2f} M', ha='center', fontsize=10, color=INK)
        print(f'[tune] rank {r:2d}: {c:,} trainable weights, '
              f'{100 * c / 450e6:.3f} per cent of a 450-million-weight model')
    axr.set_ylim(0, max(millions) * 1.25)
    axr.set_xlabel('rank of the adapter', fontsize=10)
    axr.set_ylabel('weights you actually train (millions)', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title(f'A rank-{rank} adapter trains {100 * adapter / 450e6:.2f} per cent of '
                  f'the small model', fontsize=12, weight='bold')
    _save(fig, 'rank-and-trained-weights.svg')


TASK_GOALS: Arr = np.array([[0.34, 0.10], [0.46, 0.10], [0.34, -0.04], [0.46, -0.04]])


def _task_demos(n_each: int, k: int, rng: np.random.Generator) -> tuple[Arr, Arr, Arr, Arr]:
    """Demonstrations of k fixed jobs, with the job written down as a tag."""
    paths, tags, goals, boxes = [], [], [], []
    for j in range(k):
        p, g, b, _ = demos(n_each, rng, gx=(TASK_GOALS[j, 0],) * 2,
                           gy=(TASK_GOALS[j, 1],) * 2)
        paths.append(p)
        goals.append(g)
        boxes.append(b)
        t = np.zeros((n_each, k))
        t[:, j] = 1.0
        tags.append(t)
    return (np.concatenate(paths, 0), np.concatenate(goals, 0),
            np.concatenate(boxes, 0), np.concatenate(tags, 0))


def _fit_tagged(path: Arr, extra: Arr, chunk: int, seed: int,
                steps: int = 2500) -> Policy:
    """Train a chunk policy whose observation is the gripper and whatever `extra` holds."""
    step = np.diff(path, axis=1)
    n = len(path)
    pad = np.concatenate([step, np.zeros((n, chunk, 2))], 1)
    obs = np.concatenate([path[:, :STEPS, :], np.repeat(extra[:, None, :], STEPS, 1)],
                         2).reshape(-1, 2 + extra.shape[1])
    blk = np.stack([pad[:, s:s + chunk, :] for s in range(STEPS)], 1).reshape(-1, chunk * 2)
    scale = float(blk.std())
    p = net_train(net_init([obs.shape[1], 128, 128, chunk * 2], seed), obs, blk / scale,
                  steps, 256, 3e-3, seed + 1)
    return Policy(p, scale, chunk)


def _run_tagged(pol: Policy, extra: Arr, play: int, rng: np.random.Generator) -> Arr:
    m = len(extra)
    pos = rng.normal(0, 0.004, (m, 2))
    out = [pos.copy()]
    t = 0
    while t < STEPS:
        blk = pol(np.concatenate([pos, extra], 1))
        for j in range(min(play, pol.chunk)):
            if t >= STEPS:
                break
            pos = pos + blk[:, j, :] + rng.normal(0, 0.0008, (m, 2))
            out.append(pos.copy())
            t += 1
    return np.stack(out, 1)


def _eval_tasks(k: int, rng: np.random.Generator) -> tuple[Arr, Arr, Arr]:
    which = rng.integers(0, k, EVAL)
    tag = np.zeros((EVAL, k))
    tag[np.arange(EVAL), which] = 1.0
    box = np.stack([rng.uniform(*OX, EVAL), rng.uniform(*OY, EVAL)], 1)
    return TASK_GOALS[which], box, tag


def instruction_information() -> None:
    """A sentence only helps when the recordings differ in what the sentence says."""
    told, guess = [], []
    for k in (1, 2, 4):
        rng = np.random.default_rng(401 + k)
        path, goal, box, tag = _task_demos(40, k, rng)
        pol_t = _fit_tagged(path, np.concatenate([box, tag], 1), CHUNK, 410 + k)
        pol_n = _fit_tagged(path, box, CHUNK, 420 + k)
        g_ev, b_ev, t_ev = _eval_tasks(k, np.random.default_rng(99))
        pt = _run_tagged(pol_t, np.concatenate([b_ev, t_ev], 1), PLAY,
                         np.random.default_rng(5))
        pn = _run_tagged(pol_n, b_ev, PLAY, np.random.default_rng(5))
        told.append(float(np.median(np.linalg.norm(pt[:, -1, :] - g_ev, axis=1))) * 100)
        guess.append(float(np.median(np.linalg.norm(pn[:, -1, :] - g_ev, axis=1))) * 100)
        print(f'[words] {k} job(s), {np.log2(k):.0f} bit(s) in the instruction: '
              f'told which job {told[-1]:.2f} cm, not told {guess[-1]:.2f} cm')

    # picture 1: how much an instruction can possibly say
    fig, axl = plt.subplots(figsize=(7.4, 4.4), facecolor='white')
    _plain(axl)
    ks = [1, 2, 4, 8, 16]
    axl.bar([str(k) for k in ks], [np.log2(k) for k in ks], color=JOINT, width=0.6)
    for i, k in enumerate(ks):
        b = np.log2(k)
        axl.text(i, b + 0.08, f'{b:.0f} bit' + ('' if b == 1 else 's'), ha='center',
                 fontsize=10, color=INK)
    axl.set_ylim(0, 4.8)
    axl.set_xlabel('different jobs in the recordings', fontsize=10)
    axl.set_ylabel('information the instruction carries (bits)', fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('One job recorded means the words say nothing',
                  fontsize=12, weight='bold')
    _save(fig, 'instruction-information.svg')

    # picture 2: the same network, with and without the job tag
    fig, axr = plt.subplots(figsize=(7.4, 4.6), facecolor='white')
    _plain(axr)
    x = np.arange(3)
    axr.bar(x - 0.18, told, width=0.34, color=LINK, label='told which job')
    axr.bar(x + 0.18, guess, width=0.34, color=GRIP, label='not told')
    for xi, v in zip(x - 0.18, told):
        axr.text(xi, v + 0.3, f'{v:.1f}', ha='center', fontsize=10, color=INK)
    for xi, v in zip(x + 0.18, guess):
        axr.text(xi, v + 0.3, f'{v:.1f}', ha='center', fontsize=10, color=INK)
    axr.set_xticks(x)
    axr.set_xticklabels(['1 job', '2 jobs', '4 jobs'], fontsize=10)
    axr.set_ylim(0, max(guess) * 1.25)
    axr.set_ylabel('median miss at the end (cm)', fontsize=10)
    axr.legend(fontsize=9.5, frameon=False, loc='upper left')
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('The same network, with and without the job tag',
                  fontsize=12, weight='bold')
    _save(fig, 'told-which-job-or-not.svg')


def jobs_and_data() -> None:
    """What each extra job costs in recordings."""
    totals = (20, 40, 80, 160, 320)
    lines = {}
    for k in (1, 4):
        got = []
        for total in totals:
            reps = []
            for rep in range(2):
                rng = np.random.default_rng(471 + 7 * rep + total)
                path, goal, box, tag = _task_demos(total // k, k, rng)
                pol = _fit_tagged(path, np.concatenate([box, tag], 1), CHUNK,
                                  480 + rep * 11 + total)
                g_ev, b_ev, t_ev = _eval_tasks(k, np.random.default_rng(99))
                paths = _run_tagged(pol, np.concatenate([b_ev, t_ev], 1), PLAY,
                                    np.random.default_rng(5 + rep))
                d = np.linalg.norm(paths[:, -1, :] - g_ev, axis=1)
                c = hits_box(paths, b_ev)
                reps.append(float(((d < TOL) & ~c).mean()))
            got.append(float(np.mean(reps)))
            print(f'[jobs] {k} job(s), {total:3d} recordings in all '
                  f'({total // k} each): success {got[-1]:.3f}')
        lines[k] = got

    # picture 1: one job and four jobs, at the same total number of recordings
    fig, axl = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axl)
    axl.plot(totals, lines[1], marker='o', color=LINK, lw=2, label='one job')
    axl.plot(totals, lines[4], marker='s', color=GRIP, lw=2, label='four jobs, one model')
    axl.axhline(0.80, color=MUTED, ls='--', lw=1.1)
    axl.set_xscale('log', base=2)
    axl.set_xticks(totals)
    axl.set_xticklabels([str(t) for t in totals], fontsize=9.5)
    axl.set_ylim(0, 1.05)
    axl.set_xlabel('demonstrations recorded in all (log scale)', fontsize=10)
    axl.set_ylabel('runs that work, out of 1', fontsize=10)
    axl.legend(fontsize=9.5, frameon=False, loc='lower right')
    axl.grid(color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('Four jobs need more recordings than one',
                  fontsize=12, weight='bold')
    _save(fig, 'jobs-and-data.svg')

    # picture 2: the distance between those two curves, drawn on its own
    fig, axr = plt.subplots(figsize=(7.4, 4.4), facecolor='white')
    _plain(axr)
    gaps = [a - b for a, b in zip(lines[1], lines[4])]
    axr.bar([str(t) for t in totals], gaps, color=WRIST, width=0.6)
    for i, g in enumerate(gaps):
        axr.text(i, g + 0.012, f'{g:+.2f}', ha='center', fontsize=10, color=INK)
        print(f'[jobs] at {totals[i]} recordings the four-job model is '
              f'{g:+.3f} behind the one-job model')
    axr.axhline(0, color=INK, lw=1.0)
    axr.set_ylim(min(0, min(gaps)) - 0.05, max(gaps) + 0.09)
    axr.set_xlabel('demonstrations recorded in all', fontsize=10)
    axr.set_ylabel('how far the four-job model is behind', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('The gap closes as the recordings grow in number',
                  fontsize=12, weight='bold')
    _save(fig, 'the-gap-between-one-job-and-four.svg')


# --------------------------------------------------------------------------
# section 5: a model that predicts what happens next
# --------------------------------------------------------------------------

DT: float = 1.0 / HZ
PUSH: float = 0.025              # speed gained from a full command, m/s a step
DRAG_LIN: float = 0.06
DRAG_SQ: float = 0.80
STICK: float = 0.006             # below this speed the table grips, m/s


def true_step(s: Arr, a: Arr) -> Arr:
    """The real table: a gripper with momentum, drag that changes from place to
    place, and a patch of stiction near standstill."""
    x, v = s[:, :2], s[:, 2:]
    a = np.clip(a, -1.0, 1.0)
    rough = 1.0 + 0.8 * np.sin(14.0 * x[:, :1]) * np.cos(9.0 * x[:, 1:])
    v = v + PUSH * a - DRAG_LIN * rough * v - DRAG_SQ * v * np.abs(v)
    v = np.where(np.abs(v) < STICK, v * 0.45, v)
    return np.concatenate([x + v * DT, v], 1)


def poke(n_ep: int, rng: np.random.Generator) -> tuple[Arr, Arr, Arr]:
    """Collect transitions by pushing the gripper about at random, with nobody there."""
    s = np.concatenate([np.stack([rng.uniform(0.0, 0.45, n_ep),
                                  rng.uniform(-0.15, 0.15, n_ep)], 1),
                        rng.normal(0, 0.03, (n_ep, 2))], 1)
    a = rng.uniform(-1, 1, (n_ep, 2))
    S, A, N = [], [], []
    for _ in range(STEPS):
        a = np.clip(0.85 * a + 0.5 * rng.normal(0, 1, (n_ep, 2)), -1, 1)
        s2 = true_step(s, a)
        S.append(s.copy())
        A.append(a.copy())
        N.append(s2.copy())
        s = s2
    return (np.concatenate(S, 0), np.concatenate(A, 0), np.concatenate(N, 0))


class Dynamics:
    """A learned one-step predictor: where the gripper goes next."""

    def __init__(self, p: list[list[Arr]], mu: Arr, sd: Arr, dmu: Arr, dsd: Arr) -> None:
        self.p, self.mu, self.sd, self.dmu, self.dsd = p, mu, sd, dmu, dsd

    def __call__(self, s: Arr, a: Arr) -> Arr:
        inp = np.concatenate([(s - self.mu) / self.sd, a], 1)
        return s + net_fwd(self.p, inp)[0] * self.dsd + self.dmu


def fit_dynamics(S: Arr, A: Arr, N: Arr, seed: int, steps: int = 4000) -> Dynamics:
    mu, sd = S.mean(0), S.std(0) + 1e-9
    d = N - S
    dmu, dsd = d.mean(0), d.std(0) + 1e-9
    X = np.concatenate([(S - mu) / sd, A], 1)
    Y = (d - dmu) / dsd
    p = net_train(net_init([6, 64, 64, 4], seed), X, Y, steps, 256, 3e-3, seed + 1)
    return Dynamics(p, mu, sd, dmu, dsd)


class Section5:
    """The dynamics model and its test data, worked out once."""

    def __init__(self) -> None:
        self.S, self.A, self.N = poke(100, np.random.default_rng(501))
        self.model = fit_dynamics(self.S, self.A, self.N, 511)
        self.tS, self.tA, self.tN = poke(40, np.random.default_rng(502))


_S5: Section5 | None = None


def _s5() -> Section5:
    global _S5
    if _S5 is None:
        _S5 = Section5()
    return _S5


def horizon_you_can_trust() -> None:
    """How far ahead a learned model may be trusted, measured."""
    s = _s5()
    one = float(np.mean(np.linalg.norm(
        s.model(s.tS, s.tA)[:, :2] - s.tN[:, :2], axis=1)) * 1000)
    rng = np.random.default_rng(521)
    m = 400
    st = np.concatenate([np.stack([rng.uniform(0.05, 0.4, m), rng.uniform(-0.1, 0.1, m)], 1),
                         rng.normal(0, 0.02, (m, 2))], 1)
    acts = []
    a = rng.uniform(-1, 1, (m, 2))
    for _ in range(60):
        a = np.clip(0.85 * a + 0.5 * rng.normal(0, 1, (m, 2)), -1, 1)
        acts.append(a.copy())
    real, pred = st.copy(), st.copy()
    gaps, reals, preds = [], [real[:, :2].copy()], [pred[:, :2].copy()]
    for a in acts:
        real = true_step(real, a)
        pred = s.model(pred, a)
        gaps.append(float(np.mean(np.linalg.norm(real[:, :2] - pred[:, :2], axis=1)) * 1000))
        reals.append(real[:, :2].copy())
        preds.append(pred[:, :2].copy())
    gaps_arr = np.array(gaps)
    cross = int(np.argmax(gaps_arr > 1.0)) + 1 if (gaps_arr > 1.0).any() else 0
    print(f'[world] one step ahead the model is out by {one:.3f} mm')
    for h in (1, 5, 10, 20, 40, 60):
        print(f'[world] {h:2d} steps ahead ({h / HZ:.2f} s): out by {gaps[h - 1]:.2f} mm')
    print(f'[world] the gap passes 1 mm at step {cross}, which is {cross / HZ:.2f} s')

    # picture 1: the model's prediction drawn over what really happened
    fig, axl = plt.subplots(figsize=(7.4, 4.6), facecolor='white')
    _plain(axl)
    R = np.stack(reals, 1)
    P = np.stack(preds, 1)
    for i in range(4):
        axl.plot(R[i, :, 0], R[i, :, 1], color=INK, lw=1.8,
                 label='what really happened' if i == 0 else None)
        axl.plot(P[i, :, 0], P[i, :, 1], color=GRIP, lw=1.6, ls='--',
                 label='what the model predicted' if i == 0 else None)
        axl.plot(R[i, 0, 0], R[i, 0, 1], marker='o', ms=5, color=SLIDE)
    axl.set_xlabel('along the table (m)', fontsize=10)
    axl.set_ylabel('across the table (m)', fontsize=10)
    axl.legend(fontsize=9.5, frameon=False, loc='best')
    axl.set_title('Four runs of 60 steps, predicted from the start',
                  fontsize=11.5, weight='bold')
    _save(fig, 'predictions-over-sixty-steps.svg')

    # picture 2: how the gap grows with the number of steps predicted ahead
    fig, axr = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(axr)
    axr.plot(np.arange(1, 61), gaps, color=PURPLE, lw=2.2)
    axr.axhline(1.0, color=MUTED, ls='--', lw=1.1)
    axr.text(34, 1.2, 'a millimetre out', fontsize=9.5, color=MUTED)
    if cross:
        axr.axvline(cross, color=GRIP, ls=':', lw=1.4)
        axr.text(cross + 1.5, max(gaps) * 0.55, f'step {cross}\n{cross / HZ:.2f} s',
                 fontsize=9.5, color=GRIP)
    axr.set_xlabel('steps predicted ahead', fontsize=10)
    axr.set_ylabel('average gap from the truth (mm)', fontsize=10)
    axr.grid(color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title(f'One step out by {one:.2f} mm, sixty steps out by {gaps[-1]:.1f} mm',
                  fontsize=11.5, weight='bold')
    _save(fig, 'horizon-you-can-trust.svg')


PLAN_N: int = 64
PLAN_H: int = 20
BOX_PEN: float = 8.0


def _shoot(model, s: Arr, goal: Arr, box: Arr, rng: np.random.Generator,
           n: int = PLAN_N, h: int = PLAN_H) -> Arr:
    """Random shooting: try n futures inside the model, return the best plan."""
    m = len(s)
    a = rng.uniform(-1, 1, (m, n, 2))
    plans = np.zeros((m, n, h, 2))
    for t in range(h):
        a = np.clip(0.8 * a + 0.6 * rng.normal(0, 1, (m, n, 2)), -1, 1)
        plans[:, :, t, :] = a
    ss = np.repeat(s, n, 0)
    gg = np.repeat(goal, n, 0)
    bb = np.repeat(box, n, 0)
    cost = np.zeros(m * n)
    for t in range(h):
        ss = model(ss, plans[:, :, t, :].reshape(m * n, 2))
        last = np.linalg.norm(ss[:, :2] - gg, axis=1)
        cost += last
        inside = ((np.abs(ss[:, 0] - bb[:, 0]) < HW) & (np.abs(ss[:, 1] - bb[:, 1]) < HH))
        cost += BOX_PEN * inside
    cost += 6.0 * last
    best = np.argmin(cost.reshape(m, n), 1)
    return plans[np.arange(m), best]


def _drive(model, goal: Arr, box: Arr, every: int, rng: np.random.Generator) -> Arr:
    m = len(goal)
    s = np.concatenate([rng.normal(0, 0.004, (m, 2)), np.zeros((m, 2))], 1)
    out = [s[:, :2].copy()]
    t = 0
    while t < STEPS:
        plan = _shoot(model, s, goal, box, rng)
        for j in range(min(every, PLAN_H)):
            if t >= STEPS:
                break
            s = true_step(s, plan[:, j, :])
            out.append(s[:, :2].copy())
            t += 1
    return np.stack(out, 1)


def _rule(goal: Arr, box: Arr, rng: np.random.Generator, gainp: float = 40.0,
          gaind: float = 11.0) -> Arr:
    """The written rule to beat: push towards the goal, damped."""
    m = len(goal)
    s = np.concatenate([rng.normal(0, 0.004, (m, 2)), np.zeros((m, 2))], 1)
    out = [s[:, :2].copy()]
    for _ in range(STEPS):
        a = gainp * (goal - s[:, :2]) - gaind * s[:, 2:]
        s = true_step(s, np.clip(a, -1, 1))
        out.append(s[:, :2].copy())
    return np.stack(out, 1)


def planning_against_it() -> None:
    """What a predicting model buys: a new job without new data."""
    s5 = _s5()
    m = 150
    rng = np.random.default_rng(531)
    goal = np.stack([rng.uniform(0.34, 0.44, m), rng.uniform(-0.05, 0.08, m)], 1)
    box = np.stack([rng.uniform(*OX, m), rng.uniform(*OY, m)], 1)
    runs = {}
    runs['written rule'] = _rule(goal, box, np.random.default_rng(1))
    runs['planning in the\nlearned model'] = _drive(s5.model, goal, box, 5,
                                                    np.random.default_rng(2))
    runs['planning in the\nreal physics'] = _drive(true_step, goal, box, 5,
                                                   np.random.default_rng(2))
    res = {}
    for name, paths in runs.items():
        d, c, ok = judge(paths, goal, box)
        res[name] = (float(np.median(d)) * 100, float(c.mean()), float(ok.mean()))
        print(f'[plan] {name.replace(chr(10), " ")}: median miss {res[name][0]:.2f} cm, '
              f'hits the box {res[name][1]:.3f}, works {res[name][2]:.3f}')
    every = (1, 2, 5, 10, 20)
    far = []
    for e in every:
        paths = _drive(s5.model, goal, box, e, np.random.default_rng(3))
        far.append(float(np.median(judge(paths, goal, box)[0])) * 100)
        print(f'[plan] replanning every {e:2d} steps ({e / HZ * 1000:.0f} ms): '
              f'median miss {far[-1]:.2f} cm')

    # picture 1: the same table and the same box, under the two ways of deciding
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white',
                             gridspec_kw={'wspace': 0.24})
    shift = np.stack([0.20 - box[:, 0], -box[:, 1]], 1)
    for ax, name, col, short in (
            (axes[0], 'written rule', GRIP, 'A written rule'),
            (axes[1], 'planning in the\nlearned model', LINK, 'A planner')):
        _plain(ax)
        paths = runs[name]
        hit = res[name][1]
        for i in range(24):
            ax.plot(paths[i, :, 0] + shift[i, 0], paths[i, :, 1] + shift[i, 1],
                    color=col, lw=1.0, alpha=0.65)
        ax.add_patch(Rectangle((0.20 - HW, -HH), 2 * HW, 2 * HH, color='#999999'))
        ax.set_xlim(-0.08, 0.48)
        ax.set_ylim(-0.11, 0.11)
        ax.set_xlabel('along the table, every run lined up on its box (m)', fontsize=10)
        ax.set_ylabel('across the table (m)', fontsize=10)
        ax.set_title(f'{short}: {hit:.0%} hit the box', fontsize=11.5, weight='bold')
    fig.suptitle('A new job, written as a cost', fontsize=12.5, weight='bold')
    _save(fig, 'planning-against-it.svg')

    # picture 2: the three ways of deciding, counted
    fig, ax1 = plt.subplots(figsize=(7.4, 4.6), facecolor='white')
    _plain(ax1)
    names = list(res)
    hit = [res[n][1] for n in names]
    work = [res[n][2] for n in names]
    x = np.arange(len(names))
    ax1.bar(x - 0.18, hit, width=0.34, color=GRIP, label='hits the box')
    ax1.bar(x + 0.18, work, width=0.34, color=SLIDE, label='works')
    for xi, v in zip(x - 0.18, hit):
        ax1.text(xi, v + 0.02, f'{v:.2f}', ha='center', fontsize=9.5, color=INK)
    for xi, v in zip(x + 0.18, work):
        ax1.text(xi, v + 0.02, f'{v:.2f}', ha='center', fontsize=9.5, color=INK)
    ax1.set_xticks(x)
    ax1.set_xticklabels(['written\nrule', 'learned\nmodel', 'real\nphysics'], fontsize=9.5)
    ax1.set_ylim(0, 1.15)
    ax1.set_ylabel('share of 150 runs', fontsize=10)
    ax1.legend(fontsize=9.5, frameon=False, loc='upper center')
    ax1.grid(axis='y', color=GRID, lw=0.6)
    ax1.set_axisbelow(True)
    ax1.set_title('No demonstrations at all', fontsize=11.5, weight='bold')
    _save(fig, 'planner-against-written-rule.svg')

    # picture 3: how often the plan has to be made again
    fig, ax2 = plt.subplots(figsize=(7.4, 4.6), facecolor='white')
    _plain(ax2)
    ax2.plot([e / HZ * 1000 for e in every], far, marker='o', color=PURPLE, lw=2)
    for e, v in zip(every, far):
        ax2.annotate(f'{e}', (e / HZ * 1000, v), textcoords='offset points',
                     xytext=(0, 8), ha='center', fontsize=9.5, color=INK)
    ax2.set_xlabel('milliseconds between one plan and the next', fontsize=10)
    ax2.set_ylabel('median miss at the end (cm)', fontsize=10)
    ax2.grid(color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('An old plan costs more than a wrong model',
                  fontsize=11.5, weight='bold')
    _save(fig, 'how-often-to-replan.svg')


def planning_arithmetic() -> None:
    """How many futures fit between two commands."""
    period = 1000.0 / HZ
    speeds = (0.5, 5.0, 50.0, 500.0)
    fits = [period * 1000.0 / (us * PLAN_H) for us in speeds]
    for us, f in zip(speeds, fits):
        print(f'[arith] at {us:5.1f} microseconds a model step, {f:,.0f} futures of '
              f'{PLAN_H} steps fit in {period:.1f} ms')
    print(f'[arith] one decision with {PLAN_N} futures of {PLAN_H} steps is '
          f'{PLAN_N * PLAN_H:,} model steps')

    # picture 1: how many futures fit between two commands
    fig, axl = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axl)
    labs = [f'{u:g}' for u in speeds]
    axl.bar(labs, fits, color=[SLIDE, LINK, JOINT, GRIP], width=0.6)
    for i, f in enumerate(fits):
        axl.text(i, f * 1.25, f'{f:,.0f}', ha='center', fontsize=10, color=INK)
    axl.axhline(PLAN_N, color=MUTED, ls='--', lw=1.2)
    axl.text(3.4, PLAN_N * 1.3, f'{PLAN_N} futures, the search used here',
             fontsize=9.5, color=MUTED, ha='right')
    axl.set_yscale('log')
    axl.set_ylim(0.5, max(fits) * 12)
    axl.set_xlabel('time one step of the model takes (microseconds)', fontsize=10)
    axl.set_ylabel(f'futures of {PLAN_H} steps that fit in {period:.1f} ms (log scale)',
                   fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('A big model leaves no room to search', fontsize=12, weight='bold')
    _save(fig, 'planning-arithmetic.svg')

    # picture 2: what one decision costs in calls of the model
    fig, axr = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(axr)
    cand = np.array([4, 16, 64, 256, 1024])
    for h, c in ((10, LINK), (20, PURPLE), (40, GRIP)):
        axr.plot(cand, cand * h, marker='o', color=c, lw=2, label=f'{h} steps ahead')
    axr.axhline(period * 1000 / 5.0, color=MUTED, ls='--', lw=1.2)
    axr.text(4.5, period * 1000 / 5.0 * 1.25, 'what fits at 5 microseconds a step',
             fontsize=9.5, color=MUTED)
    axr.set_xscale('log')
    axr.set_yscale('log')
    axr.set_xticks(cand)
    axr.set_xticklabels([str(c) for c in cand], fontsize=9.5)
    axr.set_xlabel('futures tried for one decision (log scale)', fontsize=10)
    axr.set_ylabel('model steps for one decision (log scale)', fontsize=10)
    axr.legend(fontsize=9.5, frameon=False, loc='upper left')
    axr.grid(color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('One decision costs futures multiplied by how far ahead',
                  fontsize=12, weight='bold')
    _save(fig, 'calls-for-one-decision.svg')


def data_without_a_person() -> None:
    """Where a world model's training data comes from, and how much is needed."""
    poke_s, reset_s = 20.0, 10.0
    per_hour = 3600.0 / (poke_s + reset_s) * poke_s * HZ
    per = (STEPS / HZ + RESET_S + CHECK_S) * SPOIL / (SPOIL - 1)
    demo_hour = 3600.0 / per * STEPS
    print(f'[auto] pushing the arm about for {poke_s:.0f} s and resetting for '
          f'{reset_s:.0f} s gives {per_hour:,.0f} transitions an hour with nobody there')
    print(f'[auto] demonstrating gives {demo_hour:,.0f} examples an hour of somebody\'s time, '
          f'so the script collects {per_hour / demo_hour:.1f} times as much')
    print(f'[auto] left running for 8 hours overnight it gathers {per_hour * 8:,.0f}')

    counts = (600, 1200, 3000, 6000, 12000, 30000)
    s5 = _s5()
    errs = []
    for c in counts:
        mdl = fit_dynamics(s5.S[:c], s5.A[:c], s5.N[:c], 551, steps=2500)
        e = float(np.mean(np.linalg.norm(
            mdl(s5.tS, s5.tA)[:, :2] - s5.tN[:, :2], axis=1)) * 1000)
        errs.append(e)
        print(f'[auto] {c:6,} transitions: one-step error {e:.3f} mm '
              f'({c / (per_hour / 60):.1f} minutes of pushing)')

    # picture 1: who has to be in the room, and how much that gathers in an hour
    fig, axl = plt.subplots(figsize=(6.8, 4.6), facecolor='white')
    _plain(axl)
    axl.bar(['a script pushing\nthe arm about', 'a person\ndemonstrating'],
            [per_hour, demo_hour], color=[SLIDE, GRIP], width=0.5)
    for i, v in enumerate([per_hour, demo_hour]):
        axl.text(i, v * 1.03, f'{v:,.0f}', ha='center', fontsize=11, color=INK)
    axl.set_ylim(0, per_hour * 1.25)
    axl.set_ylabel('training examples gathered in one hour', fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('Only one of these needs somebody in the room',
                  fontsize=12, weight='bold')
    _save(fig, 'data-without-a-person.svg')

    # picture 2: how the one-step error falls as transitions pile up
    fig, axr = plt.subplots(figsize=(7.6, 4.6), facecolor='white')
    _plain(axr)
    axr.plot(counts, errs, marker='o', color=PURPLE, lw=2)
    axr.set_xscale('log')
    axr.set_yscale('log')
    axr.set_xticks(counts)
    axr.set_xticklabels([f'{c / 1000:g}k' if c >= 1000 else str(c) for c in counts],
                        fontsize=9.5)
    axr.set_xlabel('transitions used to fit the model (log scale)', fontsize=10)
    axr.set_ylabel('one-step error (mm, log scale)', fontsize=10)
    axr.grid(color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('Ten minutes of pushing is enough', fontsize=12, weight='bold')
    _save(fig, 'transitions-and-one-step-error.svg')


# --------------------------------------------------------------------------
# section 6: a policy found by trying, not by copying
# --------------------------------------------------------------------------

POP: int = 50
ELITE: int = 10
GENS: int = 25
TASKS: int = 16
MAX_STEP: float = 0.015


def _feats(pos: Arr, goal: Arr, box: Arr) -> Arr:
    """Five simple numbers the searched policy multiplies: towards the goal,
    away from the box, and a constant."""
    to_goal = goal - pos
    away = pos - box
    r = np.linalg.norm(away, axis=-1, keepdims=True)
    rep = away / (r ** 3 + 1e-4) * 1e-4
    one = np.ones(pos.shape[:-1] + (1,))
    return np.concatenate([to_goal, rep, one], -1)


def rl_run(W: Arr, goal: Arr, box: Arr, rng: np.random.Generator, gain=1.0,
           delay=0, goal_err: Arr | None = None, steps: int = STEPS) -> Arr:
    """Run a batch of searched policies. W is (C, 5, 2), goal and box are (E, 2).

    The policy is always told the nominal box and the reported goal. What the arm
    really does is set by `gain` and by `delay`, the number of steps a command
    takes to reach the joints, and by `margin` inside rl_score.
    """
    c = len(W)
    e = len(goal)
    g = np.asarray(gain, float).reshape(1, -1, 1) if np.ndim(gain) else float(gain)
    dly = np.broadcast_to(np.asarray(delay, int), (e,)).copy()
    buf = np.zeros((int(dly.max()) + 1, c, e, 2))
    pos = rng.normal(0, 0.004, (c, e, 2))
    told_goal = goal if goal_err is None else goal + goal_err
    out = [pos.copy()]
    idx = np.arange(e)
    for _ in range(steps):
        f = _feats(pos, told_goal[None, :, :], box[None, :, :])
        a = np.clip(np.einsum('cef,cfa->cea', f, W) * 0.03, -MAX_STEP, MAX_STEP)
        buf = np.concatenate([a[None], buf[:-1]], 0) if len(buf) > 1 else a[None]
        applied = np.transpose(buf[dly, :, idx, :], (1, 0, 2))
        pos = pos + g * applied + rng.normal(0, 0.0008, (c, e, 2))
        out.append(pos.copy())
    return np.stack(out, 2)


def rl_score(paths: Arr, goal: Arr, box: Arr, margin=0.0) -> tuple[Arr, Arr]:
    """Reward for the search, and whether each run worked."""
    mg = np.asarray(margin, dtype=float).reshape(1, -1) if np.ndim(margin) else float(margin)
    d = np.linalg.norm(paths[:, :, -1, :] - goal[None, :, :], axis=-1)
    gx = np.abs(paths[:, :, :, 0] - box[None, :, None, 0])
    gy = np.abs(paths[:, :, :, 1] - box[None, :, None, 1])
    hw = HW + (mg[:, :, None] if np.ndim(mg) else mg)
    hh = HH + (mg[:, :, None] if np.ndim(mg) else mg)
    inside = ((gx < hw) & (gy < hh)).any(2)
    length = np.linalg.norm(np.diff(paths, axis=2), axis=-1).sum(2)
    reward = -100.0 * d - 30.0 * inside - 2.0 * length
    return reward, (d < TOL) & ~inside


def cem_search(rng: np.random.Generator, randomise: bool = False,
               gens: int = GENS) -> tuple[Arr, list[float], list[float]]:
    """The plainest reinforcement learning there is: try, keep the best, repeat."""
    mu = np.zeros((5, 2))
    sd = np.ones((5, 2))
    best_r, best_s = [], []
    for _g in range(gens):
        W = mu[None] + sd[None] * rng.normal(0, 1, (POP, 5, 2))
        goal = np.stack([rng.uniform(0.34, 0.46, TASKS), rng.uniform(-0.05, 0.10, TASKS)], 1)
        box = np.stack([rng.uniform(*OX, TASKS), rng.uniform(*OY, TASKS)], 1)
        if randomise:
            gain = rng.uniform(0.80, 1.20, TASKS)
            margin = rng.uniform(0.0, 0.025, TASKS)
            gerr = rng.uniform(-0.010, 0.010, (TASKS, 2))
            dly = rng.integers(0, 7, TASKS)
        else:
            gain, margin, gerr, dly = 1.0, 0.0, None, 0
        paths = rl_run(W, goal, box, rng, gain=gain, delay=dly, goal_err=gerr)
        reward, ok = rl_score(paths, goal, box, margin=margin)
        mean_r = reward.mean(1)
        keep = np.argsort(-mean_r)[:ELITE]
        mu = W[keep].mean(0)
        sd = W[keep].std(0) + 0.02
        best_r.append(float(mean_r[keep].mean()))
        best_s.append(float(ok[keep].mean()))
    return mu, best_r, best_s


class Section6:
    """The two searched policies, found once."""

    def __init__(self) -> None:
        self.plain, self.curve_r, self.curve_s = cem_search(np.random.default_rng(601))
        self.rand, self.rcurve_r, self.rcurve_s = cem_search(np.random.default_rng(602),
                                                             randomise=True)
        self.goal = None


_S6: Section6 | None = None


def _s6() -> Section6:
    global _S6
    if _S6 is None:
        _S6 = Section6()
    return _S6


def _rl_eval(W: Arr, rng: np.random.Generator, **kw) -> float:
    goal = np.stack([rng.uniform(0.34, 0.46, EVAL), rng.uniform(-0.05, 0.10, EVAL)], 1)
    box = np.stack([rng.uniform(*OX, EVAL), rng.uniform(*OY, EVAL)], 1)
    margin = kw.pop('margin', 0.0)
    gerr = kw.pop('goal_err_size', 0.0)
    kw['goal_err'] = None if gerr == 0 else np.full((EVAL, 2), gerr)
    paths = rl_run(W[None], goal, box, rng, **kw)
    return float(rl_score(paths, goal, box, margin=margin)[1].mean())


def what_the_search_costs() -> None:
    """Reinforcement learning means a simulator, and this is why."""
    s = _s6()
    episodes = GENS * POP * TASKS
    per = (STEPS / HZ + RESET_S + CHECK_S) * SPOIL / (SPOIL - 1)
    arm_h = episodes * (STEPS / HZ + 20.0) / 3600.0
    demo_h = 40 * per / 3600.0
    print(f'[search] {GENS} rounds x {POP} candidates x {TASKS} tasks = {episodes:,} episodes')
    print(f'[search] reward of the best ten went from {s.curve_r[0]:.1f} to '
          f'{s.curve_r[-1]:.1f}, and their success from {s.curve_s[0]:.3f} to '
          f'{s.curve_s[-1]:.3f}')
    print(f'[search] the randomised search went from {s.rcurve_s[0]:.3f} to '
          f'{s.rcurve_s[-1]:.3f} over the same {GENS} rounds')
    print(f'[search] on a real arm at {STEPS / HZ:.0f} s a try and 20 s to reset, that is '
          f'{arm_h:.1f} hours, or {arm_h / 24:.1f} days of running')
    print(f'[search] the cloned policy of section 1 needed 40 demonstrations, '
          f'{demo_h * 60:.0f} minutes of a person')

    # picture 1: the search learning from its own attempts
    fig, axl = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axl)
    g = np.arange(1, GENS + 1)
    axl.plot(g, s.curve_s, marker='o', ms=4, color=SLIDE, lw=2, label='nothing randomised')
    axl.plot(g, s.rcurve_s, marker='s', ms=4, color=PURPLE, lw=2,
             label='simulator randomised')
    axl.set_xlabel('round of the search', fontsize=10)
    axl.set_ylabel('runs the best ten policies get right', fontsize=10)
    axl.set_ylim(0, 1.05)
    axl.legend(fontsize=9.5, frameon=False, loc='lower right')
    axl.grid(color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title(f'{episodes:,} tries, and no person in the room',
                  fontsize=12, weight='bold')
    _save(fig, 'what-the-search-costs.svg')

    # picture 2: the same two policies, bought on a real arm instead
    fig, axr = plt.subplots(figsize=(6.8, 4.6), facecolor='white')
    _plain(axr)
    hrs = [demo_h, arm_h]
    axr.bar(['40 demonstrations\nfor copying', f'{episodes:,} tries\nfor searching'],
            hrs, color=[LINK, GRIP], width=0.5)
    for i, v in enumerate(hrs):
        axr.text(i, v * 1.4, f'{v:.2f} hours' if v < 1 else f'{v:,.0f} hours\n'
                                                            f'({v / 24:.1f} days)',
                 ha='center', fontsize=10.5, color=INK)
    axr.set_yscale('log')
    axr.set_ylim(0.1, arm_h * 20)
    axr.set_ylabel('hours on a real arm (log scale)', fontsize=10)
    axr.grid(axis='y', color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('What each of the two would cost on a real arm',
                  fontsize=12, weight='bold')
    _save(fig, 'hours-on-a-real-arm.svg')


def the_simulator_must_be_right() -> None:
    """Each thing the simulator gets wrong, measured on its own."""
    s = _s6()
    base = _rl_eval(s.plain, np.random.default_rng(611))
    cases = [('nothing\nwrong', dict()),
             ('arm moves\n0.85 of what\nit is told', dict(gain=0.85)),
             ('commands\n5 steps\nlate', dict(delay=5)),
             ('obstacle\n2.5 cm bigger\nall round', dict(margin=0.025)),
             ('all three\nat once', dict(gain=0.85, delay=5, margin=0.025))]
    vals = []
    for name, kw in cases:
        v = _rl_eval(s.plain, np.random.default_rng(611), **kw)
        vals.append(v)
        print(f'[gap] {name.replace(chr(10), " ")}: success {v:.3f} '
              f'({100 * (v - base) / base:+.0f} per cent)')

    # picture 1: one searched policy, five arms it might meet
    fig, axl = plt.subplots(figsize=(8.4, 4.8), facecolor='white')
    _plain(axl)
    cols = [SLIDE] + [GRIP] * 3 + [INK]
    bars = axl.bar(range(len(cases)), vals, color=cols, width=0.6)
    axl.set_xticks(range(len(cases)))
    axl.set_xticklabels([c[0] for c in cases], fontsize=9.5)
    for b, v in zip(bars, vals):
        axl.text(b.get_x() + b.get_width() / 2, v + 0.02, f'{v:.2f}', ha='center',
                 fontsize=10, color=INK)
    axl.set_ylim(0, 1.1)
    axl.set_ylabel('runs that work, out of 1', fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('One policy, five arms it might meet', fontsize=12, weight='bold')
    _save(fig, 'the-simulator-must-be-right.svg')

    # picture 2: what randomising the simulator does to the range that works
    dls = list(range(0, 8))
    plain = [_rl_eval(s.plain, np.random.default_rng(612), delay=d) for d in dls]
    rand = [_rl_eval(s.rand, np.random.default_rng(612), delay=d) for d in dls]
    fig, axr = plt.subplots(figsize=(7.8, 4.6), facecolor='white')
    _plain(axr)
    axr.plot(dls, plain, marker='o', color=GRIP, lw=2, label='searched in one simulator')
    axr.plot(dls, rand, marker='s', color=PURPLE, lw=2, label='searched in many')
    axr.axvline(0, color=MUTED, ls='--', lw=1.1)
    axr.text(0.15, 0.22, 'what the simulator assumed', fontsize=9.5, color=MUTED)
    axr.set_ylim(0, 1.05)
    axr.set_xlabel('steps a command takes to reach the joints', fontsize=10)
    axr.set_ylabel('runs that work, out of 1', fontsize=10)
    axr.legend(fontsize=9.5, frameon=False, loc='center left')
    axr.grid(color=GRID, lw=0.6)
    axr.set_axisbelow(True)
    axr.set_title('Randomising widens the range that works', fontsize=12, weight='bold')
    for d, a, b in zip(dls, plain, rand):
        print(f'[gap] commands {d} steps late ({d / HZ * 1000:.0f} ms): '
              f'one simulator {a:.3f}, randomised {b:.3f}')
    _save(fig, 'randomising-widens-the-range.svg')


def cloning_against_searching() -> None:
    """Which of the two to start, given one arm and a few weeks."""
    s = _s6()
    real = dict(gain=0.85, delay=5, margin=0.025)
    sim_plain = _rl_eval(s.plain, np.random.default_rng(621))
    real_plain = _rl_eval(s.plain, np.random.default_rng(621), **real)
    real_rand = _rl_eval(s.rand, np.random.default_rng(621), **real)
    path, goal, box, _ = demos(40, np.random.default_rng(631))
    pol = clone(path, goal, box, CHUNK, 641, steps=2500)
    _, gev, bev, _ = demos(EVAL, np.random.default_rng(555))
    bc = float(judge(run(pol, gev, bev, PLAY, np.random.default_rng(9)), gev, bev)[2].mean())
    per = (STEPS / HZ + RESET_S + CHECK_S) * SPOIL / (SPOIL - 1)
    print(f'[choose] searched policy in its own simulator {sim_plain:.3f}, on the '
          f'different arm {real_plain:.3f}, randomised then on the different arm '
          f'{real_rand:.3f}')
    print(f'[choose] cloned policy from 40 demonstrations, on the arm they were '
          f'recorded on: {bc:.3f}')
    print(f'[choose] copying uses 40 episodes, {40 * per / 60:.0f} minutes of a person; '
          f'searching uses {GENS * POP * TASKS:,} episodes from the simulator only')

    fig, axl = plt.subplots(figsize=(8.6, 4.8), facecolor='white')
    _plain(axl)
    labs = ['searched,\nin its simulator', 'searched,\non the other arm',
            'searched with\nrandomising,\non the other arm',
            'copied from 40\ndemonstrations,\non its own arm']
    vals = [sim_plain, real_plain, real_rand, bc]
    cols = [MUTED, GRIP, PURPLE, LINK]
    bars = axl.bar(range(4), vals, color=cols, width=0.6)
    axl.set_xticks(range(4))
    axl.set_xticklabels(labs, fontsize=9)
    for b, v in zip(bars, vals):
        axl.text(b.get_x() + b.get_width() / 2, v + 0.02, f'{v:.2f}', ha='center',
                 fontsize=10.5, color=INK)
    axl.set_ylim(0, 1.1)
    axl.set_ylabel('runs that work, out of 1', fontsize=10)
    axl.grid(axis='y', color=GRID, lw=0.6)
    axl.set_axisbelow(True)
    axl.set_title('Four policies on the same job', fontsize=12, weight='bold')
    _save(fig, 'cloning-against-searching.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    one_demonstration_on_disk()
    hours_of_a_person()
    success_against_demonstrations()
    action_space_locked()
    two_demonstrators()
    one_chunk_example()
    chunk_length_trade()
    chunk_and_the_clock()
    two_answer_test()
    averaging_and_generating()
    what_generating_costs()
    too_few_passes()
    what_fine_tuning_costs()
    instruction_information()
    jobs_and_data()
    horizon_you_can_trust()
    planning_against_it()
    planning_arithmetic()
    data_without_a_person()
    what_the_search_costs()
    the_simulator_must_be_right()
    cloning_against_searching()
    print(f'wrote the diagrams under {IMAGES / DOC}')


if __name__ == '__main__':
    main()
