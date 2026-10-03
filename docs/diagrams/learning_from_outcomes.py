"""Generate the diagrams for both pages of docs/06_neural-networks/11_learning-from-outcomes/.

    01_reinforcement-learning.md              -> images/learning-from-outcomes/reinforcement-learning/
    02_rewards-preferences-and-verifiers.md   -> images/learning-from-outcomes/rewards-preferences-and-verifiers/

Run with:  python3 docs/diagrams/learning_from_outcomes.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script prints
the numbers so the two documents can quote the same values.

The world is simulated. It is a five-by-five table top seen from above, with a
gripper, one block, a near tray and a bin, and seven actions. The transitions
are written out in full in build(), so the world is a made-up one rather than a
measurement of a real arm. Everything run on that world is real: tabular
Q-learning, exact value iteration, a tabular softmax policy trained by a
clipped policy-gradient step in the style of proximal policy optimisation, a
logistic reward model fitted by gradient descent on simulated rollouts, and a
Bradley-Terry preference model fitted to simulated choices between pairs of
attempts. Random numbers always come from numpy.random.default_rng with a
stated seed.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'learning-from-outcomes')
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

RL_DOC: str = 'reinforcement-learning'
RW_DOC: str = 'rewards-preferences-and-verifiers'

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


def _smooth(x: Arr, k: int) -> Arr:
    """Running average over k values, same length as x."""
    out = np.empty_like(x)
    c = np.cumsum(np.insert(x, 0, 0.0))
    for i in range(len(x)):
        lo = max(0, i - k + 1)
        out[i] = (c[i + 1] - c[lo]) / (i + 1 - lo)
    return out


# --------------------------------------------------------------------------
# the little world
# --------------------------------------------------------------------------

ROWS: int = 5
COLS: int = 5
START: tuple[int, int] = (4, 0)
BLOCK: tuple[int, int] = (3, 2)
TRAY: tuple[int, int] = (4, 2)
BIN: tuple[int, int] = (0, 4)
ACTIONS: list[str] = ['up', 'down', 'left', 'right', 'close', 'open', 'wait']
SHORT: list[str] = ['U', 'D', 'L', 'R', 'C', 'O', 'W']
NA: int = 7
NS: int = ROWS * COLS * 2
MAXSTEPS: int = 80
STEP_COST: float = -0.1
GRIP_COST: float = 0.05
BUMP_COST: float = 0.5
DELTA: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]

Tables = tuple[NDArray[np.int64], Arr, NDArray[np.bool_], NDArray[np.object_],
               NDArray[np.int64]]


def sid(r: int, c: int, h: bool) -> int:
    return (r * COLS + c) * 2 + int(h)


def unsid(s: int) -> tuple[int, int, bool]:
    h = s % 2
    rc = s // 2
    return rc // COLS, rc % COLS, bool(h)


S0: int = sid(*START, False)


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def build(tray_bonus: float = 2.0, bin_bonus: float = 10.0, drop_pen: float = -1.0,
          tray_ends: bool = True) -> Tables:
    """Write out the whole world as tables: next state, reward, finished, outcome.

    Moving into a wall leaves the gripper where it was. Closing the gripper on
    the block picks it up. Opening the gripper over the bin finishes the attempt
    and pays bin_bonus; over the tray it pays tray_bonus; anywhere else the
    block is put back on its starting square and the attempt carries on.
    """
    P = np.zeros((NS, NA), dtype=np.int64)
    R = np.zeros((NS, NA))
    D = np.zeros((NS, NA), dtype=np.bool_)
    OUT = np.full((NS, NA), '', dtype=object)
    STAY = np.zeros((NS, NA), dtype=np.int64)
    for s in range(NS):
        r, c, h = unsid(s)
        for a in range(NA):
            nr, nc, nh, rew, done, out = r, c, h, STEP_COST, False, ''
            if a < 4:
                dr, dc = DELTA[a]
                if 0 <= r + dr < ROWS and 0 <= c + dc < COLS:
                    nr, nc = r + dr, c + dc
            elif a == 4:
                rew -= GRIP_COST
                if (not h) and (r, c) == BLOCK:
                    nh = True
            elif a == 5:
                rew -= GRIP_COST
                if h:
                    if (r, c) == BIN:
                        rew += bin_bonus
                        done = True
                        out = 'bin'
                    elif (r, c) == TRAY:
                        rew += tray_bonus
                        done = tray_ends
                        out = 'tray'
                        if not tray_ends:
                            nh = False
                    else:
                        rew += drop_pen
                        nh = False
                        out = 'drop'
            P[s, a], R[s, a], D[s, a], OUT[s, a] = sid(nr, nc, nh), rew, done, out
            STAY[s, a] = sid(r, c, h)
    return P, R, D, OUT, STAY


WORLD: Tables = build()


def relabel_tray(t: Tables) -> Tables:
    """Return the same world with the tray treated as an ordinary wrong place."""
    P, R, D, OUT, STAY = t
    OUT = OUT.copy()
    for s in range(NS):
        if OUT[s, 5] == 'tray':
            OUT[s, 5] = 'drop'
    return P, R, D, OUT, STAY


def rewrite_reward(t: Tables, fn) -> Tables:
    """Same transitions, a different reward written by fn(row, col, holding, action, outcome)."""
    P, R, D, OUT, STAY = t
    R2 = np.zeros_like(R)
    for s in range(NS):
        r, c, h = unsid(s)
        for a in range(NA):
            R2[s, a] = fn(r, c, h, a, OUT[s, a])
    return P, R2, D, OUT, STAY


# --------------------------------------------------------------------------
# running and learning
# --------------------------------------------------------------------------

INTERIOR: list[tuple[int, int]] = [(r, c) for r in (1, 2, 3) for c in (1, 2, 3)
                                   if (r, c) != BLOCK]


def rollout(Q: Arr, rng: np.random.Generator, eps: float, t: Tables,
            slip: float = 0.0, maxsteps: int = MAXSTEPS, s0: int = S0,
            blocked: tuple[int, int] | None = None, tie: str = 'random'
            ) -> tuple[NDArray[np.int64], NDArray[np.int64], Arr, str]:
    """One attempt with an epsilon-greedy policy read off the table Q.

    blocked names one square that a fixture stands on in the real cell, so a move
    onto it leaves the gripper where it was.
    """
    P, R, D, OUT, STAY = t
    s = s0
    out = 'timeout'
    ss: list[int] = []
    aa: list[int] = []
    rr: list[float] = []
    for _ in range(maxsteps):
        if rng.random() < eps:
            a = int(rng.integers(NA))
        else:
            q = Q[s]
            cand = np.flatnonzero(q >= q.max() - 1e-12)
            if len(cand) == 1 or tie == 'first':
                a = int(cand[0])
            else:
                a = int(rng.choice(cand))
        ss.append(s)
        aa.append(a)
        rew = float(R[s, a])
        s2 = int(P[s, a])
        if slip > 0.0 and a < 4 and rng.random() < slip:
            s2 = int(STAY[s, a])
        if blocked is not None and a < 4 and unsid(s2)[:2] == blocked:
            s2 = int(STAY[s, a])
            rew -= BUMP_COST
        rr.append(rew)
        if D[s, a]:
            out = OUT[s, a]
            break
        s = s2
    return np.array(ss), np.array(aa), np.array(rr), out


def q_learn(episodes: int, eps0: float, seed: int, eps1: float | None = None,
            gamma: float = 0.95, alpha: float = 0.3, slip: float = 0.0,
            t: Tables = WORLD, maxsteps: int = MAXSTEPS,
            count: list[int] | None = None,
            slip_range: tuple[float, float] | None = None,
            blocked: tuple[int, int] | None = None,
            random_block: bool = False) -> tuple[Arr, Arr, Arr, list[Arr]]:
    """Tabular Q-learning. Returns Q, the return of every attempt, whether every
    attempt put the block in the bin, and snapshots of Q at a few points."""
    P, R, D, OUT, STAY = t
    rng = np.random.default_rng(seed)
    Q = np.zeros((NS, NA))
    rets = np.zeros(episodes)
    succ = np.zeros(episodes)
    marks = {0, episodes // 50, episodes // 10, episodes // 3, episodes - 1}
    snaps: list[Arr] = []
    for ep in range(episodes):
        e = eps0 if eps1 is None else eps0 + (eps1 - eps0) * ep / max(1, episodes - 1)
        sl = slip if slip_range is None else float(rng.uniform(*slip_range))
        bl = blocked
        if random_block:
            bl = INTERIOR[int(rng.integers(len(INTERIOR)))]
        ss, aa, rr, out = rollout(Q, rng, e, t, sl, maxsteps, blocked=bl)
        for i in range(len(ss) - 1, -1, -1):
            s, a = int(ss[i]), int(aa[i])
            tgt = rr[i] if D[s, a] else rr[i] + gamma * Q[P[s, a]].max()
            Q[s, a] += alpha * (tgt - Q[s, a])
        rets[ep] = rr.sum()
        succ[ep] = 1.0 if out == 'bin' else 0.0
        if count is not None:
            count.append(len(ss))
        if ep in marks:
            snaps.append(Q.copy())
    return Q, rets, succ, snaps


def evaluate(Q: Arr, n: int = 60, seed: int = 0, slip: float = 0.0, t: Tables = WORLD,
             maxsteps: int = MAXSTEPS, score: Tables | None = None,
             blocked: tuple[int, int] | None = None, tie: str = 'random'
             ) -> tuple[dict[str, float], float]:
    """Run the greedy policy n times and report how the attempts ended.

    score lets the policy be judged by a different reward from the one it was
    trained on, which is what a hold-out check on the real goal does.
    """
    rng = np.random.default_rng(seed)
    outs: list[str] = []
    rets: list[float] = []
    Rs = (score if score is not None else t)[1]
    for _ in range(n):
        ss, aa, rr, out = rollout(Q, rng, 0.0, t, slip, maxsteps, blocked=blocked,
                                  tie=tie)
        outs.append(out)
        rets.append(float(Rs[ss, aa].sum()))
    arr = np.array(outs)
    return ({o: float((arr == o).mean()) for o in ['bin', 'tray', 'drop', 'timeout']},
            float(np.mean(rets)))


def value_iteration(gamma: float = 0.95, t: Tables = WORLD, iters: int = 4000
                    ) -> tuple[Arr, Arr]:
    """Work out the exact best value of every state, and the exact action values."""
    P, R, D, OUT, STAY = t
    V = np.zeros(NS)
    for _ in range(iters):
        Q = R + gamma * np.where(D, 0.0, V[P])
        V2 = Q.max(1)
        if float(np.max(np.abs(V2 - V))) < 1e-13:
            V = V2
            break
        V = V2
    return V, R + gamma * np.where(D, 0.0, V[P])


def greedy_path(Q: Arr, t: Tables = WORLD, maxsteps: int = MAXSTEPS, s0: int = S0
                ) -> tuple[NDArray[np.int64], NDArray[np.int64], Arr, str]:
    """The route the greedy policy takes, with ties broken by the first action."""
    P, R, D, OUT, STAY = t
    s = s0
    ss: list[int] = []
    aa: list[int] = []
    rr: list[float] = []
    out = 'timeout'
    for _ in range(maxsteps):
        a = int(np.argmax(Q[s]))
        ss.append(s)
        aa.append(a)
        rr.append(R[s, a])
        if D[s, a]:
            out = OUT[s, a]
            break
        s = int(P[s, a])
    return np.array(ss), np.array(aa), np.array(rr), out


def discounted(rewards: Arr, gamma: float) -> float:
    g = 0.0
    for r in rewards[::-1]:
        g = r + gamma * g
    return float(g)


# --------------------------------------------------------------------------
# drawing the table top
# --------------------------------------------------------------------------

def _table(ax: Axes, title: str = '', marks: bool = True, small: bool = False,
           label_top: bool = False) -> None:
    """Draw the empty five-by-five table top with its four named squares."""
    ax.set_xlim(-0.05, COLS + 0.05)
    ax.set_ylim(-0.05, ROWS + 0.05)
    ax.set_aspect('equal')
    ax.axis('off')
    for r in range(ROWS):
        for c in range(COLS):
            ax.add_patch(Rectangle((c, ROWS - 1 - r), 1, 1, fill=False,
                                   edgecolor=GRID, lw=1.0))
    if marks:
        for (rc, colour, label) in ((START, MUTED, 'start'), (BLOCK, WRIST, 'block'),
                                    (TRAY, JOINT, 'tray +2'), (BIN, SLIDE, 'bin +10')):
            r, c = rc
            ax.add_patch(Rectangle((c, ROWS - 1 - r), 1, 1, color=colour, alpha=0.16,
                                   lw=0))
            ax.text(c + 0.5, ROWS - 1 - r + (0.90 if label_top else 0.08), label,
                    ha='center', va='bottom' if not label_top else 'top',
                    fontsize=7.0 if small else 8.0, color=colour, weight='bold')
    if title:
        ax.set_title(title, fontsize=10.5 if small else 11.5, weight='bold', color=INK)


def _cell_xy(r: int, c: int) -> tuple[float, float]:
    return c + 0.5, ROWS - 1 - r + 0.5


def _draw_policy(ax: Axes, Q: Arr, holding: bool, colour: str = LINK,
                 size: float = 10.0) -> None:
    """One mark per square: an arrow for a move, a letter for a gripper command."""
    for r in range(ROWS):
        for c in range(COLS):
            a = int(np.argmax(Q[sid(r, c, holding)]))
            x, y = _cell_xy(r, c)
            if a < 4:
                dr, dc = DELTA[a]
                ax.add_patch(FancyArrow(x - dc * 0.22, y + dr * 0.22, dc * 0.44,
                                        -dr * 0.44, width=0.03, head_width=0.17,
                                        head_length=0.15, color=colour, length_includes_head=True))
            else:
                ax.text(x, y, SHORT[a], ha='center', va='center', fontsize=size,
                        color=colour, weight='bold')


def _draw_numbers(ax: Axes, vals: Arr, holding: bool, fmt: str = '{:.1f}',
                  size: float = 9.5, shade: bool = True, dy: float = -0.14) -> None:
    """Write one number in every square, optionally shaded by how big it is."""
    layer = np.array([[vals[sid(r, c, holding)] for c in range(COLS)] for r in range(ROWS)])
    if shade:
        lo, hi = float(layer.min()), float(layer.max())
        for r in range(ROWS):
            for c in range(COLS):
                f = 0.0 if hi - lo < 1e-9 else (layer[r, c] - lo) / (hi - lo)
                ax.add_patch(Rectangle((c, ROWS - 1 - r), 1, 1, color=LINK,
                                       alpha=0.05 + 0.33 * f, lw=0))
    for r in range(ROWS):
        for c in range(COLS):
            x, y = _cell_xy(r, c)
            ax.text(x, y + dy, fmt.format(layer[r, c]), ha='center', va='center',
                    fontsize=size, color=INK)


def _draw_path(ax: Axes, ss: NDArray[np.int64], aa: NDArray[np.int64], colour: str = LINK
               ) -> None:
    """Join the squares the gripper visited, and mark where it gripped."""
    pts = []
    for s in ss:
        r, c, h = unsid(int(s))
        pts.append(_cell_xy(r, c))
    pts = np.array(pts)
    jitter = np.linspace(-0.07, 0.07, len(pts))
    ax.plot(pts[:, 0] + jitter, pts[:, 1] + jitter, color=colour, lw=1.8, alpha=0.85,
            zorder=4)
    ax.scatter(pts[0, 0], pts[0, 1], s=55, color=colour, zorder=6, marker='o')
    big = len(aa) <= 20
    for i, a in enumerate(aa):
        if a in (4, 5):
            ax.text(pts[i, 0] + 0.28, pts[i, 1] + 0.24, SHORT[a],
                    fontsize=9.5 if big else 7.5, color=GRIP, weight='bold',
                    alpha=1.0 if big else 0.75, zorder=7)


# ==========================================================================
# PAGE 1, section 1: state, action, reward, episode, return, discounting
# ==========================================================================

def the_little_world() -> None:
    V, Q = value_iteration(0.95)
    ss, aa, rr, out = greedy_path(Q)
    print(f'[world] {ROWS}x{COLS} squares, holding or not, so {NS} states and {NA} actions')
    print(f'[world] start {START}, block {BLOCK}, tray {TRAY}, bin {BIN}; '
          f'step cost {STEP_COST}, gripper command cost {-GRIP_COST}')
    print(f'[world] best route: {out} in {len(aa)} actions, '
          f'{[ACTIONS[a] for a in aa]}, total reward {rr.sum():.2f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.4), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.0]})
    ax = axes[0]
    _table(ax, 'The table top, seen from above')
    r, c = START
    ax.text(c + 0.5, ROWS - 1 - r + 0.5, 'gripper', ha='center', va='center',
            fontsize=9, color=INK, weight='bold')
    r, c = BLOCK
    ax.add_patch(Rectangle((c + 0.3, ROWS - 1 - r + 0.3), 0.4, 0.4, color=WRIST, lw=0))
    ax.text(2.5, -0.35, 'five squares across, five squares deep',
            ha='center', fontsize=9, color=MUTED)

    ax = axes[1]
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    rows = [
        ('up, down, left, right', f'{STEP_COST:+.2f}',
         'move one square; a wall leaves\nyou where you were'),
        ('close', f'{STEP_COST - GRIP_COST:+.2f}',
         'shut the fingers; picks the block\nup if you are standing on it'),
        ('open', f'{STEP_COST - GRIP_COST:+.2f}',
         'let go: the bin pays +10, the tray\npays +2, anywhere else costs 1'),
        ('wait', f'{STEP_COST:+.2f}', 'hold the pose and change nothing'),
    ]
    ax.text(0.0, 0.97, 'The seven actions', fontsize=11.5, weight='bold', color=INK)
    ax.text(0.0, 0.89, 'action', fontsize=9.5, weight='bold', color=MUTED)
    ax.text(0.40, 0.89, 'reward', fontsize=9.5, weight='bold', color=MUTED)
    ax.text(0.56, 0.89, 'what it does', fontsize=9.5, weight='bold', color=MUTED)
    y = 0.80
    for name, rew, what in rows:
        ax.text(0.0, y, name, fontsize=9.5, color=LINK, weight='bold', va='top')
        ax.text(0.40, y, rew, fontsize=9.5, color=INK, va='top')
        ax.text(0.56, y, what, fontsize=9.0, color=INK, va='top')
        y -= 0.155
    ax.text(0.0, y - 0.01, f'The attempt stops when the block is placed on the bin\n'
                           f'or the tray, or after {MAXSTEPS} actions.',
            fontsize=9.0, color=MUTED, va='top')
    ax.text(0.0, y - 0.21, f'{ROWS * COLS} squares x 2 (holding or not) = {NS} states',
            fontsize=10.5, color=PURPLE, weight='bold', va='top')
    fig.suptitle('The world every picture on this page is drawn from',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'the-little-world.svg')


def state_and_action() -> None:
    s = sid(*BLOCK, False)
    P, R, D, OUT, STAY = WORLD
    print(f'[state] state number for the gripper on the block, not holding: {s}')
    for a in range(NA):
        r2, c2, h2 = unsid(int(P[s, a]))
        print(f'[state]   {ACTIONS[a]:6s} -> state {int(P[s, a]):2d} = row {r2}, column {c2}, '
              f'holding {h2}, reward {R[s, a]:+.2f}')

    fig, axes = plt.subplots(1, 3, figsize=(14.6, 4.9), facecolor='white')
    for ax, holding in ((axes[0], False), (axes[1], True)):
        _table(ax, f'State numbers, holding = {holding}', small=True)
        for r in range(ROWS):
            for c in range(COLS):
                x, y = _cell_xy(r, c)
                ax.text(x, y - 0.12, str(sid(r, c, holding)), ha='center', va='center',
                        fontsize=10, color=INK)
    ax = axes[2]
    _table(ax, 'Where each action from state 34 leads', small=True, marks=False)
    x, y = _cell_xy(*BLOCK)
    ax.add_patch(Rectangle((BLOCK[1], ROWS - 1 - BLOCK[0]), 1, 1, color=GRIP,
                           alpha=0.14, lw=0))
    ax.add_patch(Rectangle((BLOCK[1], ROWS - 1 - BLOCK[0]), 1, 1, fill=False,
                           edgecolor=GRIP, lw=2.2))
    ax.text(x, y + 0.30, 'state 34', ha='center', fontsize=9.0, color=GRIP,
            weight='bold')
    ax.text(x, y - 0.02, 'close -> 35', ha='center', fontsize=8.5, color=PURPLE,
            weight='bold')
    ax.text(x, y - 0.28, 'open, wait -> 34', ha='center', fontsize=8.5, color=MUTED)
    for a in range(4):
        dr, dc = DELTA[a]
        ax.add_patch(FancyArrow(x + dc * 0.46, y - dr * 0.46, dc * 0.42, -dr * 0.42,
                                width=0.035, head_width=0.2, head_length=0.18,
                                color=LINK, length_includes_head=True))
        r2, c2, _ = unsid(int(P[s, a]))
        x2, y2 = _cell_xy(r2, c2)
        ax.add_patch(Rectangle((c2, ROWS - 1 - r2), 1, 1, color=LINK, alpha=0.10, lw=0))
        ax.text(x2, y2 + (0.30 if a != 1 else -0.38), f'{ACTIONS[a]}\n-> state '
                f'{int(P[s, a])}', ha='center', va='center', fontsize=8.5, color=LINK)
    fig.suptitle('The state is what the learner can see, and the action is what it does',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'state-and-action.svg')


def reward_sequence() -> None:
    V, Q = value_iteration(0.95)
    ss, aa, rr, out = greedy_path(Q)
    print(f'[rewards] the ten rewards of the best attempt: '
          f'{[round(float(x), 2) for x in rr]}')
    print(f'[rewards] they add up to {rr.sum():.2f}')

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.9), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.25]})
    ax = axes[0]
    _table(ax, 'One attempt: ten actions', small=True)
    _draw_path(ax, ss, aa, LINK)
    ax.text(2.5, -0.35, f'{" ".join(SHORT[a] for a in aa)}   total reward '
                        f'{rr.sum():.2f}', ha='center', fontsize=9.5, color=INK)
    ax = axes[1]
    _plain(ax)
    steps = np.arange(len(rr))
    cols = [SLIDE if v > 0 else GRIP for v in rr]
    ax.bar(steps, rr, color=cols, edgecolor=INK, lw=0.6)
    for i, v in enumerate(rr):
        ax.text(i, v + (0.35 if v > 0 else -0.45), f'{v:+.2f}', ha='center',
                fontsize=9, color=INK)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_xticks(steps)
    ax.set_xticklabels([f'{i}\n{ACTIONS[a]}' for i, a in enumerate(aa)], fontsize=8.5)
    ax.set_xlabel('step number in the attempt, and the action taken', fontsize=10)
    ax.set_ylabel('reward that came back', fontsize=10)
    ax.set_ylim(-1.6, 11.6)
    ax.set_title(f'Nine small costs, then one payment: the return is {rr.sum():.2f}',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('The reward is one number per action, and the return is their total',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'reward-sequence.svg')


def _route_rewards() -> tuple[Arr, Arr]:
    """The reward sequence of the bin route and of the tray route."""
    V, Q = value_iteration(0.95)
    _, _, bin_r, out1 = greedy_path(Q)
    V2, Q2 = value_iteration(0.5)
    _, _, tray_r, out2 = greedy_path(Q2)
    assert out1 == 'bin' and out2 == 'tray', (out1, out2)
    return bin_r, tray_r


def discounted_return() -> None:
    bin_r, tray_r = _route_rewards()
    gammas = [1.0, 0.9, 0.7, 0.5]
    print(f'[discount] bin route has {len(bin_r)} actions, tray route has {len(tray_r)}')
    for g in gammas:
        print(f'[discount] gamma {g:.2f}: bin route return {discounted(bin_r, g):+7.3f}, '
              f'tray route return {discounted(tray_r, g):+7.3f}')
    lo, hi = 0.5, 0.95
    for _ in range(50):
        m = 0.5 * (lo + hi)
        if discounted(bin_r, m) > discounted(tray_r, m):
            hi = m
        else:
            lo = m
    print(f'[discount] the two routes are worth the same at gamma = {hi:.4f}')

    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ts = np.arange(0, 13)
    for g, col in ((1.0, INK), (0.9, LINK), (0.7, PURPLE), (0.5, GRIP)):
        ax.plot(ts, g ** ts, marker='o', ms=4, color=col, lw=1.8,
                label=f'gamma = {g:.1f}')
    ax.set_xlabel('how many steps away the reward is', fontsize=10)
    ax.set_ylabel('how much it counts for', fontsize=10)
    ax.set_title('The weight gamma to the power of the step', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False)
    ax.set_ylim(0, 1.05)

    ax = axes[1]
    _plain(ax)
    g = 0.9
    steps = np.arange(len(bin_r))
    w = g ** steps
    ax.bar(steps - 0.2, bin_r, width=0.4, color=LINK_PALE, edgecolor=INK, lw=0.5,
           label='reward itself')
    ax.bar(steps + 0.2, bin_r * w, width=0.4, color=LINK, edgecolor=INK, lw=0.5,
           label='reward after the weight')
    ax.axhline(0, color=INK, lw=0.9)
    ax.text(4.4, 6.2, f'the +10 payment is nine steps away,\nso it counts as '
            f'{bin_r[-1] * w[-1]:.2f}', fontsize=9.5, color=LINK, ha='center')
    ax.set_ylim(-1.2, 11.8)
    ax.set_xticks(steps)
    ax.set_xlabel('step number', fontsize=10)
    ax.set_ylabel('reward', fontsize=10)
    ax.set_title(f'The bin route at gamma = {g:.1f}: total '
                 f'{discounted(bin_r, g):.3f}', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')

    ax = axes[2]
    _plain(ax)
    xs = np.arange(len(gammas))
    b = [discounted(bin_r, g) for g in gammas]
    tr = [discounted(tray_r, g) for g in gammas]
    ax.bar(xs - 0.2, b, width=0.4, color=SLIDE, edgecolor=INK, lw=0.6,
           label=f'bin route ({len(bin_r)} actions, +10)')
    ax.bar(xs + 0.2, tr, width=0.4, color=JOINT, edgecolor=INK, lw=0.6,
           label=f'tray route ({len(tray_r)} actions, +2)')
    for x, v in zip(xs - 0.2, b):
        ax.text(x, v + 0.3 if v >= 0 else -1.5, f'{v:.2f}', ha='center', fontsize=8.5)
    for x, v in zip(xs + 0.2, tr):
        ax.text(x, v + 0.3 if v >= 0 else -0.8, f'{v:.2f}', ha='center', fontsize=8.5)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_ylim(-2.4, 11.0)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{g:.1f}' for g in gammas])
    ax.set_xlabel('discount factor gamma', fontsize=10)
    ax.set_ylabel('discounted return', fontsize=10)
    ax.set_title(f'Below gamma = {hi:.2f} the near tray wins', fontsize=11,
                 weight='bold')
    ax.legend(fontsize=8.5, frameon=False, loc='upper right')
    fig.suptitle('Discounting: a reward now counts for more than the same reward later',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'discounted-return.svg')


def episodes_and_returns() -> None:
    V, Q = value_iteration(0.95)
    good = greedy_path(Q)
    Qt, _, _, _ = q_learn(2000, 0.0, 31)
    tray = greedy_path(Qt)
    rng = np.random.default_rng(4)
    lost = rollout(np.zeros((NS, NA)), rng, 1.0, WORLD)
    cases = [('finished at the bin', good, SLIDE), ('finished at the tray', tray, JOINT),
             ('ran out of time', lost, GRIP)]
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.0), facecolor='white')
    for ax, (name, (ss, aa, rr, out), col) in zip(axes, cases):
        _table(ax, name, small=True)
        _draw_path(ax, ss, aa, col)
        ax.text(2.5, -0.30, f'{len(aa)} actions, return {rr.sum():.2f}, '
                            f'ended as "{out}"', ha='center', fontsize=9.5, color=INK)
        print(f'[episode] {name}: {len(aa)} actions, return {rr.sum():.2f}, outcome {out}')
    fig.suptitle('One episode is one attempt, and its return is the total reward it '
                 'collected', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'episodes-and-returns.svg')


# ==========================================================================
# PAGE 1, sections 2 and 3: policy, value, and the worked example
# ==========================================================================

MAIN: tuple[Arr, Arr, Arr, list[Arr]] | None = None
MAIN_EPISODES: int = 6000


def main_run() -> tuple[Arr, Arr, Arr, list[Arr]]:
    """The worked example: tabular Q-learning from scratch, cached."""
    global MAIN
    if MAIN is None:
        MAIN = q_learn(MAIN_EPISODES, 1.0, seed=7, eps1=0.05)
        Q, rets, succ, snaps = MAIN
        res, mret = evaluate(Q, 100, seed=77)
        print(f'[main] {MAIN_EPISODES} attempts, exploring rate from 1.00 down to 0.05')
        print(f'[main] after training the greedy policy ends: {res}, '
              f'average return {mret:.2f}')
        print(f'[main] first 100 attempts averaged {rets[:100].mean():.2f}, '
              f'last 100 averaged {rets[-100:].mean():.2f}')
        first = int(np.argmax(succ > 0)) if succ.any() else -1
        print(f'[main] first attempt that reached the bin: number {first}')
    return MAIN


def policy_as_a_table() -> None:
    Q, rets, succ, snaps = main_run()
    picks = [(sid(*START, False), 'state 40: at the start, empty gripper'),
             (sid(*BLOCK, False), 'state 34: on the block, empty gripper'),
             (sid(*BLOCK, True), 'state 35: on the block, holding it')]
    eps = 0.1
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 4.4), facecolor='white', sharey=True)
    for ax, (s, name) in zip(axes, picks):
        _plain(ax)
        best = int(np.argmax(Q[s]))
        unif = np.full(NA, 1.0 / NA)
        greedy = np.full(NA, eps / NA)
        greedy[best] += 1.0 - eps
        xs = np.arange(NA)
        ax.bar(xs - 0.2, unif, width=0.4, color=MUTED, alpha=0.6, edgecolor=INK, lw=0.5,
               label='before training')
        ax.bar(xs + 0.2, greedy, width=0.4, color=LINK, edgecolor=INK, lw=0.5,
               label=f'after training, exploring rate {eps:.2f}')
        ax.set_xticks(xs)
        ax.set_xticklabels(ACTIONS, fontsize=9, rotation=30)
        ax.set_ylim(0, 1.05)
        ax.set_title(name, fontsize=10.5, weight='bold', color=INK)
        ax.text(best + 0.2, greedy[best] + 0.03, f'{greedy[best]:.2f}', ha='center',
                fontsize=9, color=LINK, weight='bold')
        print(f'[policy] {name}: the trained policy picks "{ACTIONS[best]}" '
              f'with probability {greedy[best]:.2f}')
    axes[0].set_ylabel('chance of picking the action', fontsize=10)
    axes[0].legend(fontsize=9, frameon=False, loc='upper right')
    fig.suptitle('The policy is a chance for every action in every state',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'policy-as-a-table.svg')


def value_on_the_grid() -> None:
    V, Q = value_iteration(0.95)
    print(f'[value] exact best value of the start state V(40) = {V[S0]:.3f}')
    print(f'[value] V(34) on the block, empty = {V[sid(*BLOCK, False)]:.3f}; '
          f'V(35) holding it = {V[sid(*BLOCK, True)]:.3f}; '
          f'V(9) at the bin holding = {V[sid(*BIN, True)]:.3f}')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.4), facecolor='white')
    for ax, holding, name in ((axes[0], False, 'empty gripper'),
                              (axes[1], True, 'holding the block')):
        _table(ax, f'Value of every square, {name}', small=True)
        _draw_numbers(ax, V, holding, '{:.2f}', 9.5)
    fig.suptitle(f'The value function at gamma = 0.95: what each state is worth from '
                 f'here on', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'value-on-the-grid.svg')


def policy_and_value_together() -> None:
    V, Q = value_iteration(0.95)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.4), facecolor='white')
    for ax, holding, name in ((axes[0], False, 'empty gripper: walk to the block, then C'),
                              (axes[1], True, 'holding it: walk to the bin, then O')):
        _table(ax, name, small=True, label_top=True)
        _draw_numbers(ax, V, holding, '{:.2f}', 8.5, dy=-0.34)
        _draw_policy(ax, Q, holding, PURPLE, 12.0)
    print('[policy-value] the best action in state 34 is '
          f'"{ACTIONS[int(np.argmax(Q[sid(*BLOCK, False)]))]}" and in state 9 it is '
          f'"{ACTIONS[int(np.argmax(Q[sid(*BIN, True)]))]}"')
    fig.suptitle('The policy picks the action that leads to the highest value',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'policy-and-value-together.svg')


def value_vs_return() -> None:
    Q, rets, succ, snaps = main_run()
    gamma = 0.95
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.6), facecolor='white')
    for ax, Qx, name in ((axes[0], snaps[2], f'after {MAIN_EPISODES // 10} attempts'),
                         (axes[1], Q, f'after {MAIN_EPISODES} attempts')):
        _plain(ax)
        pred = np.array([float(Qx[s].max()) for s in range(NS)])
        real = np.array([discounted(greedy_path(Qx, s0=s)[2], gamma) for s in range(NS)])
        gap = float(np.mean(np.abs(pred - real)))
        lo = min(float(pred.min()), float(real.min())) - 0.6
        hi = max(float(pred.max()), float(real.max())) + 0.6
        ax.plot([lo, hi], [lo, hi], ls='--', color=MUTED, lw=1.2)
        ax.scatter(real, pred, s=34, color=LINK, zorder=5)
        ax.set_xlabel('the discounted return the policy really collects', fontsize=10)
        ax.set_title(f'{name}: out by {gap:.2f} on average', fontsize=11.5,
                     weight='bold', color=INK)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.text(lo + 0.1 * (hi - lo), hi - 0.08 * (hi - lo),
                'points on the dashed line are states whose value is right',
                fontsize=9, color=MUTED)
        print(f'[check] {name}: the value estimate is out by {gap:.3f} on average over '
              f'all {NS} states, biggest gap {float(np.max(np.abs(pred - real))):.2f}')
    axes[0].set_ylabel('the value the learner predicts', fontsize=10)
    fig.suptitle('The value function is a prediction, and this is how good the '
                 'prediction is', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'value-vs-return.svg')


def learning_curve() -> None:
    Q, rets, succ, snaps = main_run()
    V, Qs = value_iteration(0.95)
    best = float(greedy_path(Qs)[2].sum())
    k = 200
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(np.arange(len(rets)), _smooth(rets, k), color=LINK, lw=1.8,
            label=f'average of the last {k} attempts')
    ax.axhline(best, color=SLIDE, ls='--', lw=1.4,
               label=f'the best possible, {best:.2f}')
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('total reward collected in the attempt', fontsize=10)
    ax.set_title('The learning curve', fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax = axes[1]
    _plain(ax)
    ax.plot(np.arange(len(succ)), _smooth(succ, k), color=PURPLE, lw=1.8)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('share of attempts that reached the bin', fontsize=10)
    ax.set_title('How often the block ended up in the bin', fontsize=11.5,
                 weight='bold', color=INK)
    sm = _smooth(succ, k)
    for frac in (0.25, 0.5, 0.75, 1.0):
        i = int(frac * len(succ)) - 1
        ax.text(i, sm[i] - 0.07, f'{sm[i]:.2f}', ha='right', fontsize=9, color=PURPLE)
    print(f'[curve] smoothed success rate at a quarter, half, three quarters and the '
          f'end: ' + ', '.join(f'{_smooth(succ, k)[int(f * len(succ)) - 1]:.2f}'
                               for f in (0.25, 0.5, 0.75, 1.0)))
    fig.suptitle(f'{MAIN_EPISODES} attempts in the little world, learned from nothing '
                 f'but the reward', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'learning-curve.svg')


def policy_before_after() -> None:
    Q, rets, succ, snaps = main_run()
    start = snaps[0]
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 10.0), facecolor='white')
    for col, (Qx, name) in enumerate(((start, 'before training'),
                                      (Q, 'after training'))):
        for row, holding in enumerate((False, True)):
            ax = axes[row][col]
            _table(ax, f'{name}, {"holding" if holding else "empty gripper"}',
                   small=True)
            _draw_policy(ax, Qx, holding, MUTED if col == 0 else PURPLE, 12.0)
    print('[before-after] before training every action value is 0, so the policy is '
          'whichever action comes first')
    fig.suptitle('The policy before and after: U D L R are moves, C closes, O opens, '
                 'W waits', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'policy-before-after.svg')


def value_before_after() -> None:
    Q, rets, succ, snaps = main_run()
    mid = snaps[2]
    V_end = Q.max(1)
    V_mid = mid.max(1)
    print(f'[value-learned] after a tenth of the attempts the start state is worth '
          f'{V_mid[S0]:.2f}; at the end it is worth {V_end[S0]:.2f}; the exact answer '
          f'is {value_iteration(0.95)[0][S0]:.2f}')
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.0), facecolor='white')
    for ax, vals, name in ((axes[0], np.zeros(NS), 'at the start: every value is 0'),
                           (axes[1], V_mid, f'after {MAIN_EPISODES // 10} attempts'),
                           (axes[2], V_end, f'after {MAIN_EPISODES} attempts')):
        _table(ax, name, small=True)
        _draw_numbers(ax, vals, False, '{:.2f}', 9.0)
    fig.suptitle('The learned value of every square with an empty gripper, as training '
                 'goes on', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'value-before-after.svg')


def q_values_one_state() -> None:
    Q, rets, succ, snaps = main_run()
    V, Qstar = value_iteration(0.95)
    s = sid(*BLOCK, True)
    print(f'[action-values] state {s}, holding the block on its own square:')
    for a in range(NA):
        print(f'[action-values]   {ACTIONS[a]:6s} learned {Q[s, a]:+6.2f}  '
              f'exact {Qstar[s, a]:+6.2f}')
    fig, ax = plt.subplots(figsize=(9.2, 5.0), facecolor='white')
    _plain(ax)
    xs = np.arange(NA)
    ax.bar(xs - 0.2, snaps[1][s], width=0.4, color=MUTED, alpha=0.55, edgecolor=INK,
           lw=0.5, label=f'after {MAIN_EPISODES // 50} attempts')
    ax.bar(xs + 0.2, Q[s], width=0.4, color=LINK, edgecolor=INK, lw=0.5,
           label=f'after {MAIN_EPISODES} attempts')
    ax.plot(xs + 0.2, Qstar[s], 'k_', ms=22, mew=2, label='the exact answer')
    for a in range(NA):
        ax.text(a + 0.2, Q[s, a] + 0.16, f'{Q[s, a]:.2f}', ha='center', fontsize=9,
                color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels(ACTIONS, fontsize=10)
    ax.set_xlabel('action taken in state 35', fontsize=10)
    ax.set_ylabel('value of taking that action', fontsize=10)
    ax.set_ylim(min(0, float(Q[s].min())) - 0.6, float(Q[s].max()) + 2.6)
    ax.set_title('What one state learned: "up" and "right" are worth the same, because '
                 'the bin is up and to the right', fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper center', ncol=3)
    fig.tight_layout()
    _save(fig, RL_DOC, 'q-values-one-state.svg')


# ==========================================================================
# PAGE 1, section 4: exploring against taking the best known answer
# ==========================================================================

EXPLORE: dict[str, tuple[Arr, Arr, list[Arr], list[dict[str, float]]]] | None = None
EXPLORE_SEEDS: int = 8
EXPLORE_EPISODES: int = 6000


def explore_runs() -> dict[str, tuple[Arr, Arr, list[Arr], list[dict[str, float]]]]:
    """Two sets of runs: one that never explores, one that explores a lot."""
    global EXPLORE
    if EXPLORE is None:
        out: dict[str, tuple[Arr, Arr, list[Arr], list[dict[str, float]]]] = {}
        for name, eps in (('never explores', 0.0), ('explores 70% of the time', 0.7)):
            curves, qs, ends = [], [], []
            for seed in range(EXPLORE_SEEDS):
                Q, rets, succ, _ = q_learn(EXPLORE_EPISODES, eps, seed=300 + seed)
                curves.append(rets)
                qs.append(Q)
                ends.append(evaluate(Q, 40, seed=900 + seed)[0])
            arr = np.array(curves)
            out[name] = (arr, np.array([e['bin'] for e in ends]), qs, ends)
            got = float(np.mean([e['bin'] for e in ends]))
            print(f'[explore] {name}: {int(sum(e["bin"] > 0.5 for e in ends))} of '
                  f'{EXPLORE_SEEDS} runs end up going to the bin, share of attempts at '
                  f'the bin {got:.2f}, reward collected while training '
                  f'{arr.mean():.2f}')
        EXPLORE = out
    return EXPLORE


def explore_or_not() -> None:
    runs = explore_runs()
    V, Qs = value_iteration(0.95)
    best = float(greedy_path(Qs)[2].sum())
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for name, colour in (('never explores', GRIP), ('explores 70% of the time', LINK)):
        arr = runs[name][0]
        ax.plot(np.arange(arr.shape[1]), _smooth(arr.mean(0), 200), color=colour, lw=1.9,
                label=name)
    ax.axhline(best, color=SLIDE, ls='--', lw=1.3, label=f'best possible {best:.2f}')
    ax.axhline(1.30, color=JOINT, ls=':', lw=1.3, label='the tray route, 1.30')
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('reward collected in the attempt', fontsize=10)
    ax.set_title(f'Reward during training, averaged over {EXPLORE_SEEDS} runs',
                 fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax = axes[1]
    _plain(ax)
    names = ['never explores', 'explores 70% of the time']
    final = [float(np.mean([evaluate(q, 40, seed=1200 + i)[1]
                            for i, q in enumerate(runs[n][2])])) for n in names]
    during = [float(runs[n][0].mean()) for n in names]
    xs = np.arange(2)
    ax.bar(xs - 0.2, during, width=0.4, color=MUTED, edgecolor=INK, lw=0.6,
           label='average reward while training')
    ax.bar(xs + 0.2, final, width=0.4, color=PURPLE, edgecolor=INK, lw=0.6,
           label='reward of the policy it ends up with')
    for x, v in zip(xs - 0.2, during):
        ax.text(x, v + (0.2 if v >= 0 else -0.6), f'{v:.2f}', ha='center', fontsize=9.5)
    for x, v in zip(xs + 0.2, final):
        ax.text(x, v + 0.2, f'{v:.2f}', ha='center', fontsize=9.5)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel('reward', fontsize=10)
    ax.set_ylim(-4.0, 11.0)
    ax.set_title('Exploring costs reward now and buys a better answer later',
                 fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    print(f'[explore] average reward while training: never {during[0]:.2f}, '
          f'exploring {during[1]:.2f}')
    print(f'[explore] reward of the finished policy: never {final[0]:.2f}, '
          f'exploring {final[1]:.2f}')
    fig.suptitle('A run that never explores settles for the near tray',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'explore-or-not.svg')


def where_each_one_ends_up() -> None:
    runs = explore_runs()
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.4), facecolor='white')
    for ax, name, colour in ((axes[0], 'never explores', GRIP),
                             (axes[1], 'explores 70% of the time', LINK)):
        Q = runs[name][2][0]
        ss, aa, rr, out = greedy_path(Q)
        _table(ax, f'{name}: ends at the {out}', small=True)
        _draw_path(ax, ss, aa, colour)
        ax.text(2.5, -0.32, f'{len(aa)} actions, reward {rr.sum():.2f}', ha='center',
                fontsize=10, color=INK)
        print(f'[explore] the first run that {name}: {len(aa)} actions, '
              f'reward {rr.sum():.2f}, ends at the {out}')
    fig.suptitle('The two finished policies, run with no exploring at all',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'where-each-one-ends-up.svg')


def first_time_at_the_bin() -> None:
    runs = explore_runs()
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.7), facecolor='white')
    ax = axes[0]
    _plain(ax)
    names = ['never explores', 'explores 70% of the time']
    got = [int(sum(e['bin'] > 0.5 for e in runs[n][3])) for n in names]
    ax.bar([0, 1], got, width=0.5, color=[GRIP, LINK], edgecolor=INK, lw=0.7)
    for x, v in zip([0, 1], got):
        ax.text(x, v + 0.12, f'{v} of {EXPLORE_SEEDS}', ha='center', fontsize=11,
                weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, EXPLORE_SEEDS + 1.4)
    ax.set_ylabel('runs whose finished policy goes to the bin', fontsize=10)
    ax.set_title('How many runs found the better answer', fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    for name, colour in ((names[0], GRIP), (names[1], LINK)):
        arr = runs[name][0]
        reach = (arr > 5.0).cumsum(1) > 0
        ax.plot(np.arange(arr.shape[1]), reach.mean(0), color=colour, lw=1.9, label=name)
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('share of runs that have reached the bin at least once', fontsize=10)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title('When the bin was first found at all', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='center right')
    for name in names:
        arr = runs[name][0]
        first = [int(np.argmax(r > 5.0)) if (r > 5.0).any() else -1 for r in arr]
        print(f'[explore] {name}: attempt at which each run first reached the bin: '
              f'{first}')
    fig.suptitle('Finding the bin at all is the whole difficulty',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'first-time-at-the-bin.svg')


def the_price_of_exploring() -> None:
    epss = [0.0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8]
    seeds = 6
    during: list[float] = []
    after: list[float] = []
    for eps in epss:
        d, a = [], []
        for seed in range(seeds):
            Q, rets, succ, _ = q_learn(4000, eps, seed=600 + seed)
            d.append(float(rets.mean()))
            a.append(evaluate(Q, 30, seed=1500 + seed)[1])
        during.append(float(np.mean(d)))
        after.append(float(np.mean(a)))
        print(f'[sweep] exploring rate {eps:.2f}: reward while training '
              f'{during[-1]:+6.2f}, reward of the finished policy {after[-1]:+6.2f}')
    fig, ax = plt.subplots(figsize=(8.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(epss, during, marker='o', color=MUTED, lw=2.0,
            label='reward collected while training')
    ax.plot(epss, after, marker='s', color=PURPLE, lw=2.0,
            label='reward of the policy it ends up with')
    for x, v in zip(epss, after):
        ax.text(x, v + 0.35, f'{v:.1f}', ha='center', fontsize=9, color=PURPLE)
    for x, v in zip(epss, during):
        ax.text(x, v - 0.9, f'{v:.1f}', ha='center', fontsize=9, color=MUTED)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel('how often the learner takes a random action instead of its best one',
                  fontsize=10)
    ax.set_ylabel('reward', fontsize=10)
    ax.set_ylim(min(during) - 2.0, 11.5)
    ax.set_title('4,000 attempts at each exploring rate, averaged over '
                 f'{seeds} runs', fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, RL_DOC, 'the-price-of-exploring.svg')


# ==========================================================================
# PAGE 1, section 5: on-policy, off-policy and the size of the step
# ==========================================================================

def softmax_rows(T: Arr) -> Arr:
    T = T - T.max(1, keepdims=True)
    E = np.exp(T)
    return E / E.sum(1, keepdims=True)


def collect(theta: Arr, rng: np.random.Generator, n_ep: int, gamma: float,
            t: Tables = WORLD) -> tuple[NDArray[np.int64], NDArray[np.int64], Arr, Arr,
                                        list[str]]:
    """Run n_ep attempts with the softmax policy and work out the return from
    every step onwards."""
    P, R, D, OUT, STAY = t
    pi = softmax_rows(theta)
    S: list[int] = []
    A: list[int] = []
    G: list[float] = []
    rets: list[float] = []
    outs: list[str] = []
    for _ in range(n_ep):
        s = S0
        ss: list[int] = []
        aa: list[int] = []
        rr: list[float] = []
        out = 'timeout'
        for _ in range(MAXSTEPS):
            a = int(rng.choice(NA, p=pi[s]))
            ss.append(s)
            aa.append(a)
            rr.append(R[s, a])
            if D[s, a]:
                out = OUT[s, a]
                break
            s = int(P[s, a])
        g = 0.0
        gl = np.zeros(len(rr))
        for i in range(len(rr) - 1, -1, -1):
            g = rr[i] + gamma * g
            gl[i] = g
        S += ss
        A += aa
        G += list(gl)
        rets.append(float(np.sum(rr)))
        outs.append(out)
    return np.array(S), np.array(A), np.array(G), np.array(rets), outs


def policy_update(theta: Arr, S: NDArray[np.int64], A: NDArray[np.int64], adv: Arr,
                  p_old: Arr, epochs: int, lr: float, clip: float, use_clip: bool,
                  ent: float = 0.01) -> Arr:
    """Several passes of gradient ascent over one batch, with or without the limit."""
    for _ in range(epochs):
        pi = softmax_rows(theta)
        ratio = pi[S, A] / p_old
        if use_clip:
            ok = ~(((adv > 0) & (ratio > 1 + clip)) | ((adv < 0) & (ratio < 1 - clip)))
        else:
            ok = np.ones(len(S), dtype=bool)
        coef = np.where(ok, ratio * adv, 0.0)
        grad = np.zeros((NS, NA))
        np.add.at(grad, (S, A), coef)
        np.add.at(grad, S, -(coef[:, None] * pi[S]))
        if ent > 0:
            logp = np.log(pi + 1e-12)
            H = -(pi * logp).sum(1)
            np.add.at(grad, S, ent * (-pi * (logp + H[:, None]))[S])
        theta = theta + lr * grad / len(S)
    return theta


def ppo_train(iters: int = 80, n_ep: int = 20, epochs: int = 20, lr: float = 3.0,
              clip: float = 0.2, gamma: float = 0.95, seed: int = 0,
              use_clip: bool = True) -> tuple[Arr, Arr, Arr]:
    rng = np.random.default_rng(seed)
    theta = np.zeros((NS, NA))
    base = np.zeros(NS)
    cnt = np.zeros(NS)
    hist: list[float] = []
    steps: list[float] = []
    for _ in range(iters):
        S, A, G, rets, outs = collect(theta, rng, n_ep, gamma)
        for s, g in zip(S, G):
            cnt[s] += 1
            base[s] += (g - base[s]) / cnt[s]
        adv = G - base[S]
        sd = float(adv.std())
        if sd > 1e-8:
            adv = adv / sd
        p_old = softmax_rows(theta)[S, A]
        before = softmax_rows(theta)
        theta = policy_update(theta, S, A, adv, p_old, epochs, lr, clip, use_clip)
        steps.append(float(np.abs(softmax_rows(theta) - before).max()))
        hist.append(float(np.mean(rets)))
    return theta, np.array(hist), np.array(steps)


def learning_from_old_attempts() -> None:
    """Off-policy: build the table from attempts made by somebody else."""
    P, R, D, OUT, STAY = WORLD
    rng = np.random.default_rng(5)
    S: list[int] = []
    A: list[int] = []
    n_bin = 0
    n_ep = 1500
    for _ in range(n_ep):
        s = S0
        for _ in range(MAXSTEPS):
            a = int(rng.integers(NA))
            S.append(s)
            A.append(a)
            if D[s, a]:
                n_bin += 1 if OUT[s, a] == 'bin' else 0
                break
            s = int(P[s, a])
    Sa, Aa = np.array(S), np.array(A)
    Rw = R[Sa, Aa]
    S2 = P[Sa, Aa]
    Dn = D[Sa, Aa]
    idx = Sa * NA + Aa
    counts = np.bincount(idx, minlength=NS * NA).astype(float)
    print(f'[off-policy] {n_ep} attempts by a policy that acts at random: '
          f'{len(Sa)} stored steps, {n_bin} of the attempts reached the bin')
    Q = np.zeros((NS, NA))
    gamma = 0.95
    curve: list[float] = []
    for sweep in range(40):
        tgt = Rw + gamma * np.where(Dn, 0.0, Q[S2].max(1))
        tot = np.bincount(idx, weights=tgt, minlength=NS * NA)
        Qn = np.where(counts > 0, tot / np.maximum(counts, 1), Q.reshape(-1))
        Q = Qn.reshape(NS, NA)
        curve.append(evaluate(Q, 20, seed=2000)[1])
    V, Qstar = value_iteration(gamma)
    print(f'[off-policy] after one pass the policy is worth {curve[0]:.2f}, '
          f'after five {curve[4]:.2f}, after forty {curve[-1]:.2f}; '
          f'the best possible is {float(greedy_path(Qstar)[2].sum()):.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(np.arange(1, 41), curve, marker='o', ms=3.5, color=TEAL, lw=1.9)
    ax.axhline(float(greedy_path(Qstar)[2].sum()), color=SLIDE, ls='--', lw=1.3,
               label='the best possible')
    ax.set_xlabel('passes over the stored attempts', fontsize=10)
    ax.set_ylabel('reward of the policy read off the table', fontsize=10)
    ax.set_title(f'Learning from {n_ep} attempts that the learner never made',
                 fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax = axes[1]
    _table(ax, 'The route it ends up with', small=True)
    ss, aa, rr, out = greedy_path(Q)
    _draw_path(ax, ss, aa, TEAL)
    ax.text(2.5, -0.32, f'{len(aa)} actions, reward {rr.sum():.2f}, ends at the {out}',
            ha='center', fontsize=10, color=INK)
    fig.suptitle('Off-policy learning: the attempts can come from anywhere',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'learning-from-old-attempts.svg')


def on_policy_goes_stale() -> None:
    """On-policy: the very same stored attempts teach a policy-gradient method
    almost nothing, because they were not made by the policy being improved."""
    gamma = 0.95
    rng = np.random.default_rng(5)
    theta0 = np.zeros((NS, NA))                 # the uniform random policy
    S, A, G, rets, outs = collect(theta0, rng, 1500, gamma)
    base = np.zeros(NS)
    cnt = np.zeros(NS)
    for s, g in zip(S, G):
        cnt[s] += 1
        base[s] += (g - base[s]) / cnt[s]
    adv = G - base[S]
    adv = adv / max(float(adv.std()), 1e-8)
    p_old = softmax_rows(theta0)[S, A]
    theta = theta0.copy()
    passes: list[int] = []
    truth: list[float] = []
    for block in range(21):
        if block > 0:
            theta = policy_update(theta, S, A, adv, p_old, 4, 3.0, 0.2, True)
        chk = np.random.default_rng(1234)
        _, _, _, r2, _ = collect(theta, chk, 40, gamma)
        passes.append(block * 4)
        truth.append(float(np.mean(r2)))
    V, Qstar = value_iteration(gamma)
    best = float(greedy_path(Qstar)[2].sum())
    print(f'[on-policy] {len(S)} stored steps from 1,500 attempts by the same random '
          f'policy: the policy-gradient method moves the policy from {truth[0]:.2f} to '
          f'{truth[-1]:.2f} after {passes[-1]} passes')
    print(f'[on-policy] the off-policy method reached 8.90 on attempts from that same '
          f'random policy, and the best possible is {best:.2f}')
    fig, ax = plt.subplots(figsize=(9.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(passes, truth, marker='o', ms=4, color=WRIST, lw=2.2,
            label='a policy-gradient method, on the stored attempts')
    ax.axhline(8.90, color=TEAL, ls='--', lw=1.6,
               label='Q-learning, on attempts from that same random policy')
    ax.set_ylim(-11.5, 10.5)
    ax.set_xlabel('gradient passes made over the stored attempts', fontsize=10)
    ax.set_ylabel('reward the policy really collects', fontsize=10)
    ax.set_title('The same data, given to the two kinds of method',
                 fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    fig.tight_layout()
    _save(fig, RL_DOC, 'on-policy-goes-stale.svg')


def the_clip() -> None:
    clip = 0.2
    r = np.linspace(0.0, 2.0, 401)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.7), facecolor='white', sharey=True)
    for ax, adv, name in ((axes[0], 1.0, 'an action that turned out better than expected'),
                          (axes[1], -1.0, 'an action that turned out worse than expected')):
        _plain(ax)
        plain = r * adv
        limited = np.minimum(r * adv, np.clip(r, 1 - clip, 1 + clip) * adv)
        ax.plot(r, plain, color=MUTED, lw=1.8, ls='--', label='no limit')
        ax.plot(r, limited, color=LINK, lw=2.4, label='with the limit')
        ax.axvspan(1 - clip, 1 + clip, color=LINK_PALE, alpha=0.45, zorder=0)
        ax.axvline(1.0, color=INK, lw=0.8)
        ax.set_xlabel('new chance of the action divided by the old chance', fontsize=10)
        ax.set_title(name, fontsize=10.5, weight='bold', color=INK)
        ax.legend(fontsize=9.5, frameon=False, loc='upper left')
        ax.text(1.0, -2.3, f'allowed band\n{1 - clip:.1f} to {1 + clip:.1f}',
                ha='center', fontsize=9, color=LINK)
    axes[0].set_ylabel('what the update is paid for the change', fontsize=10)
    axes[0].set_ylim(-2.6, 2.3)
    print(f'[clip] with a band of {1 - clip:.1f} to {1 + clip:.1f}, raising the chance '
          f'of a good action beyond {1 + clip:.1f} times is paid nothing extra: '
          f'the value stays at {1 + clip:.2f}')
    print(f'[clip] for a bad action the update is paid down to {-(1 + clip):.2f} and no '
          f'further')
    fig.suptitle('Proximal policy optimisation pays nothing for a change bigger than '
                 'the band', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'the-clip.svg')


def with_and_without_the_limit() -> None:
    seeds = [0, 1, 2]
    res: dict[bool, tuple[Arr, Arr]] = {}
    for use_clip in (True, False):
        hs, sts = [], []
        for seed in seeds:
            _, h, st = ppo_train(seed=seed, use_clip=use_clip)
            hs.append(h)
            sts.append(st)
        res[use_clip] = (np.array(hs), np.array(sts))
        h = np.array(hs)
        print(f'[limit] clip={use_clip}: best reward on the way {h.max(1).mean():.2f}, '
              f'reward over the last ten rounds {h[:, -10:].mean():.2f}, '
              f'biggest change in one action chance {np.array(sts).max():.3f}')
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for use_clip, colour, name in ((True, LINK, 'with the limit'),
                                   (False, GRIP, 'without the limit')):
        h = res[use_clip][0]
        for row in h:
            ax.plot(np.arange(h.shape[1]), row, color=colour, lw=0.8, alpha=0.35)
        ax.plot(np.arange(h.shape[1]), h.mean(0), color=colour, lw=2.2, label=name)
    ax.axhline(1.30, color=JOINT, ls=':', lw=1.3, label='the tray route, 1.30')
    ax.set_xlabel('round of collect-and-improve', fontsize=10)
    ax.set_ylabel('average reward of the 20 attempts in the round', fontsize=10)
    ax.set_ylim(-11.0, 3.0)
    ax.set_title('Three runs each, drawn faintly, with their average',
                 fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='lower left')
    ax = axes[1]
    _plain(ax)
    for use_clip, colour, name in ((True, LINK, 'with the limit'),
                                   (False, GRIP, 'without the limit')):
        st = res[use_clip][1]
        for row in st:
            ax.plot(np.arange(st.shape[1]), row, color=colour, lw=0.8, alpha=0.35)
        ax.plot(np.arange(st.shape[1]), st.max(0), color=colour, lw=2.2,
                label=f'{name} (worst of the three)')
    ax.set_xlabel('round of collect-and-improve', fontsize=10)
    ax.set_ylabel('biggest change in one action chance, in one round', fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_title('How far the policy moved in a single round', fontsize=11.5,
                 weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='center right')
    fig.suptitle('Take the limit away and the policy jumps, then collapses',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'with-and-without-the-limit.svg')


# ==========================================================================
# PAGE 1, section 6: why this happens in a simulator, and crossing over
# ==========================================================================

SECONDS_SIM: float = 0.002     # seconds per action inside this script
SECONDS_ARM: float = 3.0       # seconds per action on a real arm, with resets


def how_many_attempts() -> None:
    lens: list[int] = []
    q_learn(MAIN_EPISODES, 1.0, seed=7, eps1=0.05, count=lens)
    total = int(sum(lens))
    grip = total  # every action is one command sent to the arm
    sim_h = total * SECONDS_SIM / 3600.0
    arm_h = total * SECONDS_ARM / 3600.0
    print(f'[cost] the worked example used {MAIN_EPISODES} attempts and {total} actions')
    print(f'[cost] at {SECONDS_SIM} s an action that is {sim_h * 3600:.0f} s of '
          f'simulated time; at {SECONDS_ARM} s an action on a real arm it is '
          f'{arm_h:.0f} hours, or {arm_h / 24:.1f} days of running')
    print(f'[cost] the first attempt that reached the bin was number 658, so 657 '
          f'attempts paid for nothing')
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    k = 200
    ax.plot(np.arange(len(lens)), _smooth(np.array(lens, dtype=float), k), color=TEAL,
            lw=1.9)
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('actions used in the attempt', fontsize=10)
    ax.set_title(f'{total:,} actions in all, over {MAIN_EPISODES:,} attempts',
                 fontsize=11.5, weight='bold', color=INK)
    ax.text(len(lens) * 0.35, max(_smooth(np.array(lens, dtype=float), k)) * 0.8,
            'early attempts run to the\ntime limit of 80 actions', fontsize=9.5,
            color=MUTED)
    ax = axes[1]
    _plain(ax)
    hours = [sim_h, arm_h]
    ax.bar([0, 1], hours, width=0.5, color=[LINK, GRIP], edgecolor=INK, lw=0.7)
    ax.set_yscale('log')
    for x, v in zip([0, 1], hours):
        ax.text(x, v * 1.35, f'{v:.3g} hours', ha='center', fontsize=11, weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f'in this script\n({SECONDS_SIM} s an action)',
                        f'on a real arm\n({SECONDS_ARM:.0f} s an action, with resets)'],
                       fontsize=10)
    ax.set_ylabel('hours of running (log scale)', fontsize=10)
    ax.set_ylim(1e-3, arm_h * 12)
    ax.set_title('The same learning, done in the two places', fontsize=11.5,
                 weight='bold', color=INK)
    fig.suptitle('The number of attempts is why this is done in a simulator',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'how-many-attempts.svg')


SIM2REAL: tuple[list[Arr], list[Arr]] | None = None
REAL_FIXTURE: tuple[int, int] = (1, 2)


def sim2real_runs() -> tuple[list[Arr], list[Arr]]:
    """Policies trained in one perfect simulator, and policies trained with a
    fixture standing on a different square every attempt."""
    global SIM2REAL
    if SIM2REAL is None:
        def make(kw: dict, seeds: range) -> list[Arr]:
            pols: list[Arr] = []
            for sd in seeds:
                Q, _, _, _ = q_learn(12000, 1.0, seed=sd, eps1=0.05, **kw)
                if evaluate(Q, 6, seed=7, tie='first')[0]['bin'] > 0.99:
                    pols.append(Q)
                if len(pols) == 6:
                    break
            return pols
        clean = make({}, range(401, 425))
        rand = make({'random_block': True}, range(801, 830))
        print(f'[sim2real] kept {len(clean)} runs trained in the perfect simulator and '
              f'{len(rand)} trained with the fixture moved about, out of runs that '
              f'learned the job at all')
        SIM2REAL = (clean, rand)
    return SIM2REAL


def _route(Q: Arr, blocked: tuple[int, int] | None = None
           ) -> tuple[NDArray[np.int64], NDArray[np.int64], Arr, str]:
    return rollout(Q, np.random.default_rng(1), 0.0, WORLD, blocked=blocked, tie='first')


def the_reality_gap() -> None:
    clean, rand = sim2real_runs()
    Q = clean[0]
    ok = _route(Q)
    bad = _route(Q, REAL_FIXTURE)
    print(f'[gap] in the simulator the policy takes {"".join(SHORT[a] for a in ok[1])}, '
          f'{len(ok[1])} actions, reward {ok[2].sum():.2f}, ends as "{ok[3]}"')
    print(f'[gap] in the cell with a fixture on square {REAL_FIXTURE} the same policy '
          f'takes {len(bad[1])} actions, reward {bad[2].sum():.2f}, ends as "{bad[3]}"')
    hits = int(sum(1 for i, a in enumerate(bad[1]) if a < 4
                   and unsid(int(P_OF(bad[0][i], a)))[:2] == REAL_FIXTURE))
    print(f'[gap] it pushes against the fixture {hits} times in one attempt')
    rate_sim = float(np.mean([evaluate(q, 6, seed=7, tie='first')[0]['bin']
                              for q in clean]))
    rate_real = float(np.mean([evaluate(q, 6, seed=7, blocked=REAL_FIXTURE,
                                        tie='first')[0]['bin'] for q in clean]))
    print(f'[gap] over {len(clean)} runs: reaches the bin on {rate_sim:.2f} of attempts '
          f'in the simulator and {rate_real:.2f} in the cell with the fixture')
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 5.0), facecolor='white')
    _table(axes[0], 'In the simulator', small=True)
    _draw_path(axes[0], ok[0], ok[1], SLIDE)
    axes[0].text(2.5, -0.32, f'{len(ok[1])} actions, reward {ok[2].sum():.2f}',
                 ha='center', fontsize=10, color=INK)
    ax = axes[1]
    _table(ax, 'In the real cell, same policy', small=True)
    r, c = REAL_FIXTURE
    ax.add_patch(Rectangle((c, ROWS - 1 - r), 1, 1, color=INK, alpha=0.55, lw=0))
    ax.text(c + 0.5, ROWS - 1 - r + 0.5, 'fixture', ha='center', va='center',
            fontsize=8.5, color='white', weight='bold')
    _draw_path(ax, bad[0], bad[1], GRIP)
    ax.annotate(f'pushes up into it\n{hits} times', xy=(c + 0.5, ROWS - 1 - r),
                xytext=(c - 1.45, ROWS - 1 - r - 0.55), fontsize=9, color=GRIP,
                ha='center', arrowprops={'arrowstyle': '->', 'color': GRIP, 'lw': 1.2})
    ax.text(2.5, -0.32, f'{len(bad[1])} actions, reward {bad[2].sum():.2f}, '
                        f'ends as "{bad[3]}"', ha='center', fontsize=10, color=INK)
    ax = axes[2]
    _plain(ax)
    ax.bar([0, 1], [rate_sim, rate_real], width=0.5, color=[SLIDE, GRIP], edgecolor=INK,
           lw=0.7)
    for x, v in zip([0, 1], [rate_sim, rate_real]):
        ax.text(x, v + 0.03, f'{v:.2f}', ha='center', fontsize=12, weight='bold')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['in the simulator', 'in the real cell'], fontsize=10.5)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('share of attempts that reach the bin', fontsize=10)
    ax.set_title(f'{len(clean)} runs, each tried six times', fontsize=11.5, weight='bold')
    fig.suptitle('The reality gap: one square of furniture the simulator did not have',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'the-reality-gap.svg')


def P_OF(s: int, a: int) -> int:
    return int(WORLD[0][int(s), int(a)])


def domain_randomisation() -> None:
    clean, rand = sim2real_runs()
    a = [float(np.mean([evaluate(q, 4, seed=7, blocked=bl, tie='first')[0]['bin']
                        for q in clean])) for bl in INTERIOR]
    b = [float(np.mean([evaluate(q, 4, seed=7, blocked=bl, tie='first')[0]['bin']
                        for q in rand])) for bl in INTERIOR]
    for bl, x, y in zip(INTERIOR, a, b):
        print(f'[randomise] fixture on square {bl}: one perfect simulator {x:.2f}, '
              f'randomised simulator {y:.2f}')
    print(f'[randomise] averaged over the {len(INTERIOR)} squares: '
          f'{float(np.mean(a)):.2f} against {float(np.mean(b)):.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    xs = np.arange(len(INTERIOR))
    ax.bar(xs - 0.2, a, width=0.4, color=GRIP, edgecolor=INK, lw=0.6,
           label='trained in one perfect simulator')
    ax.bar(xs + 0.2, b, width=0.4, color=SLIDE, edgecolor=INK, lw=0.6,
           label='trained with the fixture moved every attempt')
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{bl}' for bl in INTERIOR], fontsize=9, rotation=30)
    ax.set_xlabel('square the fixture really stands on', fontsize=10)
    ax.set_ylabel('share of attempts that reach the bin', fontsize=10)
    ax.axhline(float(np.mean(a)), color=GRIP, ls=':', lw=1.3)
    ax.axhline(float(np.mean(b)), color=SLIDE, ls=':', lw=1.3)
    ax.set_ylim(0, 1.5)
    ax.set_title(f'Eight places the fixture could be: average '
                 f'{float(np.mean(a)):.2f} against {float(np.mean(b)):.2f}',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper center', ncol=2)
    ax = axes[1]
    _table(ax, 'The route the randomised learner picks', small=True)
    ok = _route(rand[0])
    _draw_path(ax, ok[0], ok[1], SLIDE)
    for bl in INTERIOR:
        r, c = bl
        ax.add_patch(Rectangle((c, ROWS - 1 - r), 1, 1, fill=False, edgecolor=INK,
                               lw=1.0, ls=':'))
    ax.text(2.5, -0.32, 'dotted squares are where a fixture may stand; the route\n'
                        'crosses as few of them as it can', ha='center', fontsize=9.5,
            color=INK)
    fig.suptitle('Domain randomisation: change the simulator every attempt, and the '
                 'policy stops relying on it', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'domain-randomisation.svg')


def what_randomising_costs() -> None:
    curves_a, curves_b = [], []
    for seed in range(4):
        _, _, s1, _ = q_learn(12000, 1.0, seed=401 + seed, eps1=0.05)
        _, _, s2, _ = q_learn(12000, 1.0, seed=801 + seed, eps1=0.05, random_block=True)
        curves_a.append(s1)
        curves_b.append(s2)
    A, B = np.array(curves_a), np.array(curves_b)
    clean, rand = sim2real_runs()
    ret_a = float(np.mean([evaluate(q, 6, seed=7, tie='first')[1] for q in clean]))
    ret_b = float(np.mean([evaluate(q, 6, seed=7, tie='first')[1] for q in rand]))
    print(f'[cost of randomising] share of training attempts that reached the bin: '
          f'perfect simulator {A.mean():.3f}, randomised {B.mean():.3f}')
    print(f'[cost of randomising] back in the perfect simulator the two policies collect '
          f'{ret_a:.2f} and {ret_b:.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.9), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(np.arange(A.shape[1]), _smooth(A.mean(0), 300), color=GRIP, lw=2.0,
            label='one perfect simulator')
    ax.plot(np.arange(B.shape[1]), _smooth(B.mean(0), 300), color=SLIDE, lw=2.0,
            label='fixture moved every attempt')
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('share of attempts reaching the bin while training', fontsize=10)
    ax.set_title('Randomising makes the learning slower', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax = axes[1]
    _plain(ax)
    xs = np.arange(2)
    ax.bar(xs, [ret_a, ret_b], width=0.5, color=[GRIP, SLIDE], edgecolor=INK, lw=0.6)
    for x, v in zip(xs, [ret_a, ret_b]):
        ax.text(x, v + 0.2, f'{v:.2f}', ha='center', fontsize=12, weight='bold')
    ax.set_xticks(xs)
    ax.set_xticklabels(['one perfect simulator', 'randomised simulator'], fontsize=10)
    ax.set_ylim(0, 10.6)
    ax.set_ylabel('reward in the perfect simulator', fontsize=10)
    ax.set_title('What it costs back in the easy world', fontsize=11.5, weight='bold')
    fig.suptitle('Randomising buys a policy that survives the gap, and the bill is '
                 'training time', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RL_DOC, 'what-randomising-costs.svg')


# ==========================================================================
# PAGE 2: where the reward comes from
# ==========================================================================

W2: Tables = relabel_tray(build(tray_bonus=-1.0, tray_ends=False))
FARM: Tables = relabel_tray(build(tray_bonus=2.0, tray_ends=False))
for _s in range(NS):
    if (unsid(_s)[0], unsid(_s)[1]) == TRAY:
        FARM[3][_s, 5] = 'tray'


def _grip(a: int) -> float:
    """Closing and opening the fingers costs a little more than moving."""
    return GRIP_COST if a in (4, 5) else 0.0


def r_true(r: int, c: int, h: bool, a: int, out: str) -> float:
    v = STEP_COST - _grip(a)
    if out == 'bin':
        v += 10.0
    elif out == 'drop':
        v -= 1.0
    return v


def r_dist(r: int, c: int, h: bool, a: int, out: str) -> float:
    """What an engineer writes first: be near the block."""
    v = 1.0 - 0.3 * manhattan((r, c), BLOCK) - _grip(a)
    if out == 'bin':
        v += 10.0
    return v


HOLD_BONUS: float = 1.0


def r_hold(r: int, c: int, h: bool, a: int, out: str) -> float:
    """The true reward with a bonus for having the block in the gripper."""
    return r_true(r, c, h, a, out) + (HOLD_BONUS if h else 0.0)


def _target(r: int, c: int, h: bool) -> int:
    return manhattan((r, c), BIN if h else BLOCK)


def r_dense(r: int, c: int, h: bool, a: int, out: str) -> float:
    """The true reward plus a push towards whatever is wanted next."""
    return r_true(r, c, h, a, out) - 0.3 * _target(r, c, h)


def potential(s: int) -> float:
    r, c, h = unsid(s)
    return -0.3 * _target(r, c, h) + 2.0 * float(h)


def shaped_by_potential(t: Tables, gamma: float = 0.95) -> Tables:
    """Add gamma * potential(next state) - potential(state) to every reward."""
    P, R, D, OUT, STAY = t
    phi = np.array([potential(s) for s in range(NS)])
    R2 = R + gamma * np.where(D, 0.0, phi[P]) - phi[:, None]
    return P, R2, D, OUT, STAY


T_TRUE: Tables = rewrite_reward(W2, r_true)
T_DIST: Tables = rewrite_reward(W2, r_dist)
T_HOLD: Tables = rewrite_reward(W2, r_hold)
T_DENSE: Tables = rewrite_reward(W2, r_dense)
T_POT: Tables = shaped_by_potential(T_TRUE)
T_FARM: Tables = rewrite_reward(FARM, lambda r, c, h, a, out:
                                r_true(r, c, h, a, out) + (3.0 if out == 'tray' else 0.0))


def _bin_rate(Q: Arr, t: Tables, n: int = 60, seed: int = 50) -> float:
    return evaluate(Q, n, seed=seed, t=t)[0]['bin']


# ---------------- section 1: a reward written by hand ----------------

def the_written_reward() -> None:
    vals = np.array([r_dist(*unsid(s), 0, '') for s in range(NS)])
    print('[written] the reward for a move action, square by square (empty gripper):')
    for r in range(ROWS):
        print('[written]   ' + ' '.join(f'{vals[sid(r, c, False)]:+5.2f}'
                                        for c in range(COLS)))
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.2), facecolor='white')
    _table(axes[0], 'Reward for one move, square by square', small=True, label_top=True)
    _draw_numbers(axes[0], vals, False, '{:+.2f}', 10.0, dy=-0.2)
    ax = axes[1]
    _plain(ax)
    ds = np.arange(0, 7)
    ax.plot(ds, 1.0 - 0.3 * ds, marker='o', color=WRIST, lw=2.2)
    for d in ds:
        ax.text(d, 1.0 - 0.3 * d + 0.08, f'{1.0 - 0.3 * d:+.2f}', ha='center',
                fontsize=9.5)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel('squares between the gripper and the block', fontsize=10)
    ax.set_ylabel('reward for that step', fontsize=10)
    ax.set_title('reward = 1.00 minus 0.30 for every square away', fontsize=11.5,
                 weight='bold', color=INK)
    ax.set_ylim(-1.0, 1.35)
    fig.suptitle('The first reward anybody writes: pay the arm for being near the block',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-written-reward.svg')


def the_hovering_policy() -> None:
    V, Q = value_iteration(0.95, t=T_DIST)
    ss, aa, rr, out = greedy_path(Q, t=T_DIST)
    true_reward = float(T_TRUE[1][ss, aa].sum())
    print(f'[hover] the best policy under the written reward takes '
          f'{[ACTIONS[a] for a in aa[:6]]} and then {ACTIONS[int(aa[-1])]} until the '
          f'time runs out')
    print(f'[hover] it collects {rr.sum():.2f} of the written reward, ends as "{out}", '
          f'and scores {true_reward:.2f} on the real job')
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.0), facecolor='white')
    _table(axes[0], 'The route it takes', small=True)
    _draw_path(axes[0], ss, aa, GRIP)
    axes[0].text(2.5, -0.32, f'{len(aa)} actions, then the time limit', ha='center',
                 fontsize=10, color=INK)
    _table(axes[1], 'Best action, empty gripper', small=True, label_top=True)
    _draw_policy(axes[1], Q, False, PURPLE, 12.0)
    _table(axes[2], 'Best action, holding the block', small=True, label_top=True)
    _draw_policy(axes[2], Q, True, PURPLE, 12.0)
    fig.suptitle(f'The policy walks to the block and waits: written reward '
                 f'{rr.sum():.2f}, block in the bin 0 times',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-hovering-policy.svg')


def reward_up_task_flat() -> None:
    curves, succ = [], []
    for seed in range(4):
        Q, rets, sc, _ = q_learn(4000, 1.0, seed=70 + seed, eps1=0.05, t=T_DIST)
        curves.append(rets)
        succ.append(sc)
    A, S = np.array(curves), np.array(succ)
    print(f'[hover] over {A.shape[0]} runs of 4,000 attempts each, the written reward '
          f'rises from {A[:, :100].mean():.2f} to {A[:, -100:].mean():.2f}')
    print(f'[hover] the share of attempts that put the block in the bin stays at '
          f'{S.mean():.3f}')
    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(np.arange(A.shape[1]), _smooth(A.mean(0), 200), color=WRIST, lw=2.1,
            label='the written reward it collects')
    ax.set_xlabel('attempt number', fontsize=10)
    ax.set_ylabel('written reward collected in the attempt', fontsize=10)
    ax2 = ax.twinx()
    ax2.plot(np.arange(S.shape[1]), _smooth(S.mean(0), 200), color=PURPLE, lw=2.1,
             label='share of attempts that put the block in the bin')
    ax2.set_ylim(-0.03, 1.05)
    ax2.set_ylabel('share of attempts that reach the bin', fontsize=10, color=PURPLE)
    ax2.tick_params(labelcolor=PURPLE)
    ax.set_title('The number the learner is paid goes up and the job is never done',
                 fontsize=12, weight='bold', color=INK)
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [ln.get_label() for ln in lines], fontsize=9.5, frameon=False,
              loc='center right')
    fig.tight_layout()
    _save(fig, RW_DOC, 'reward-up-task-flat.svg')


def three_behaviours_scored() -> None:
    V, Qd = value_iteration(0.95, t=T_DIST)
    hover = greedy_path(Qd, t=T_DIST)
    V2, Qt = value_iteration(0.95, t=T_TRUE)
    proper = greedy_path(Qt, t=T_TRUE)
    rng = np.random.default_rng(21)
    wander = rollout(np.zeros((NS, NA)), rng, 1.0, W2)
    names = ['wait by the block', 'put it in the bin', 'move at random']
    cases = [hover, proper, wander]
    written = [float(T_DIST[1][ss, aa].sum()) for ss, aa, _, _ in cases]
    real = [float(T_TRUE[1][ss, aa].sum()) for ss, aa, _, _ in cases]
    done = [1.0 if o == 'bin' else 0.0 for _, _, _, o in cases]
    for n, w, t, d in zip(names, written, real, done):
        print(f'[score] "{n}": written reward {w:+7.2f}, true reward {t:+6.2f}, '
              f'block in the bin {int(d)}')
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), facecolor='white')
    xs = np.arange(3)
    ax = axes[0]
    _plain(ax)
    ax.bar(xs, written, width=0.5, color=[GRIP, SLIDE, MUTED], edgecolor=INK, lw=0.6)
    for x, v in zip(xs, written):
        ax.text(x, v + 1.5, f'{v:.1f}', ha='center', fontsize=10.5, weight='bold')
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel('total written reward', fontsize=10)
    ax.set_ylim(min(written) - 6, max(written) + 12)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_title('Scored by the reward that was written', fontsize=11.5, weight='bold')
    ax = axes[1]
    _plain(ax)
    ax.bar(xs, done, width=0.5, color=[GRIP, SLIDE, MUTED], edgecolor=INK, lw=0.6)
    for x, v, t in zip(xs, done, real):
        ax.text(x, v + 0.04, f'{int(v)}', ha='center', fontsize=10.5, weight='bold')
        ax.text(x, 0.5, f'true reward\n{t:.2f}', ha='center', fontsize=9.5, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, 1.25)
    ax.set_ylabel('block ended up in the bin', fontsize=10)
    ax.set_title('Scored by the job that was wanted', fontsize=11.5, weight='bold')
    fig.suptitle('The behaviour that wins under the written reward is the one that '
                 'never does the job', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'three-behaviours-scored.svg')


# ---------------- section 2: sparse, dense and shaping ----------------

def sparse_against_dense() -> None:
    V, Q = value_iteration(0.95, t=T_TRUE)
    ss, aa, rr, out = greedy_path(Q, t=T_TRUE)
    dense = T_DENSE[1][ss, aa]
    print(f'[sparse] the same ten actions pay {[round(float(x), 2) for x in rr]} '
          f'under the sparse reward')
    print(f'[sparse] and {[round(float(x), 2) for x in dense]} under the dense one')
    print(f'[sparse] totals: sparse {rr.sum():.2f}, dense {dense.sum():.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white')
    steps = np.arange(len(rr))
    for ax, vals, name, colour in ((axes[0], rr, 'sparse: nothing until the end', LINK),
                                   (axes[1], dense,
                                    'dense: a little every step', TEAL)):
        _plain(ax)
        ax.bar(steps, vals, color=colour, edgecolor=INK, lw=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + (0.3 if v >= 0 else -0.5), f'{v:.2f}', ha='center',
                    fontsize=8.5)
        ax.axhline(0, color=INK, lw=0.9)
        ax.set_xticks(steps)
        ax.set_xticklabels([ACTIONS[a][:1].upper() for a in aa], fontsize=9)
        ax.set_xlabel('the ten actions of the same attempt', fontsize=10)
        ax.set_ylabel('reward for that action', fontsize=10)
        ax.set_ylim(-2.6, 11.5)
        ax.set_title(f'{name}, total {vals.sum():.2f}', fontsize=11.5, weight='bold')
    fig.suptitle('One attempt, two rewards: the sparse one says nothing until the '
                 'block lands', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'sparse-against-dense.svg')


SHAPING: dict[str, Arr] | None = None
SHAPE_EPS: float = 0.10


def shaping_runs() -> dict[str, Arr]:
    global SHAPING
    if SHAPING is None:
        out: dict[str, Arr] = {}
        for name, tab in (('sparse', T_TRUE), ('dense', T_DENSE), ('potential', T_POT)):
            runs = []
            for seed in range(4):
                _, _, sc, _ = q_learn(6000, SHAPE_EPS, seed=150 + seed, t=tab)
                runs.append(sc)
            out[name] = np.array(runs)
        SHAPING = out
    return SHAPING


def how_fast_each_one_learns() -> None:
    runs = shaping_runs()
    fig, ax = plt.subplots(figsize=(9.8, 5.3), facecolor='white')
    _plain(ax)
    for name, colour, label in (
            ('sparse', LINK, 'sparse: +10 only when the block lands in the bin'),
            ('dense', WRIST, 'dense: also pays for getting closer each step'),
            ('potential', SLIDE, 'potential-based: the same push, written as a difference')):
        arr = runs[name]
        ax.plot(np.arange(arr.shape[1]), _smooth(arr.mean(0), 200), color=colour, lw=2.1,
                label=label)
        half = int(np.argmax(_smooth(arr.mean(0), 200) > 0.5)) if (
            _smooth(arr.mean(0), 200) > 0.5).any() else -1
        print(f'[shaping] {name}: reaches the bin on {arr[:, -200:].mean():.2f} of the '
              f'last 200 attempts; first passed half of attempts at attempt {half}')
    ax.set_ylim(-0.03, 1.07)
    ax.set_xlim(0, 900)
    ax.set_xlabel('attempt number (all three stay at 1.00 for the remaining 5,100)',
                  fontsize=10)
    ax.set_ylabel('share of attempts that reach the bin', fontsize=10)
    ax.set_title('Four runs of each, averaged', fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.suptitle('What matters is the shape of the shaping, not that it is dense',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'how-fast-each-one-learns.svg')


def shaping_that_changes_the_answer() -> None:
    V, Q = value_iteration(0.95, t=T_HOLD)
    ss, aa, rr, out = greedy_path(Q, t=T_HOLD)
    true_r = float(T_TRUE[1][ss, aa].sum())
    Ql, _, sc, _ = q_learn(4000, 1.0, seed=61, eps1=0.05, t=T_HOLD)
    rate = _bin_rate(Ql, T_HOLD)
    print(f'[hold bonus] the best policy under the holding bonus does '
          f'{[ACTIONS[a] for a in aa[:6]]} and then {ACTIONS[int(aa[-1])]}; it collects '
          f'{rr.sum():.2f} of the shaped reward, {true_r:.2f} of the real one, and ends '
          f'as "{out}"')
    print(f'[hold bonus] a learner trained on it reaches the bin on {rate:.2f} of '
          f'attempts')
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.0), facecolor='white')
    _table(axes[0], 'The route under the holding bonus', small=True)
    _draw_path(axes[0], ss, aa, GRIP)
    axes[0].text(2.5, -0.32, f'{len(aa)} actions, shaped reward {rr.sum():.2f}, '
                             f'real reward {true_r:.2f}', ha='center', fontsize=9.5,
                 color=INK)
    _table(axes[1], 'Best action while holding', small=True, label_top=True)
    _draw_policy(axes[1], Q, True, PURPLE, 12.0)
    ax = axes[2]
    _plain(ax)
    held = np.array([HOLD_BONUS * t for t in range(MAXSTEPS + 1)])
    ax.plot(np.arange(MAXSTEPS + 1), held, color=GRIP, lw=2.2,
            label=f'keep holding: {HOLD_BONUS:.2f} a step, for ever')
    ax.axhline(10.0, color=SLIDE, ls='--', lw=1.8, label='put it in the bin: +10, once')
    ax.set_xlabel('steps spent holding the block', fontsize=10)
    ax.set_ylabel('reward collected', fontsize=10)
    ax.set_title('Why carrying it beats placing it', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.suptitle('A bonus for holding the block changes which behaviour is best, not '
                 'just how fast it is found', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'shaping-that-changes-the-answer.svg')


def shaping_that_keeps_the_answer() -> None:
    phi = np.array([potential(s) for s in range(NS)])
    V1, Q1 = value_iteration(0.95, t=T_TRUE)
    V2, Q2 = value_iteration(0.95, t=T_POT)
    V3, Q3 = value_iteration(0.95, t=T_DENSE)
    same_pot = int(sum(int(np.argmax(Q1[s])) == int(np.argmax(Q2[s]))
                       for s in range(NS)))
    same_dense = int(sum(int(np.argmax(Q1[s])) == int(np.argmax(Q3[s]))
                         for s in range(NS)))
    print(f'[potential] the potential-based reward agrees with the plain one on '
          f'{same_pot} of {NS} states')
    print(f'[potential] the plain dense reward agrees on {same_dense} of {NS} states')
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 5.0), facecolor='white')
    _table(axes[0], 'The number attached to each square, empty gripper', small=True,
           label_top=True)
    _draw_numbers(axes[0], phi, False, '{:+.1f}', 10.0, dy=-0.2)
    _table(axes[1], 'The same, holding the block', small=True, label_top=True)
    _draw_numbers(axes[1], phi, True, '{:+.1f}', 10.0, dy=-0.2)
    ax = axes[2]
    _plain(ax)
    xs = np.arange(2)
    ax.bar(xs, [same_dense, same_pot], width=0.5, color=[WRIST, SLIDE], edgecolor=INK,
           lw=0.6)
    for x, v in zip(xs, [same_dense, same_pot]):
        ax.text(x, v + 0.8, f'{v} of {NS}', ha='center', fontsize=11, weight='bold')
    ax.set_xticks(xs)
    ax.set_xticklabels(['plain dense reward', 'potential-based reward'], fontsize=10)
    ax.set_ylim(0, NS + 6)
    ax.set_ylabel('states where the best action is unchanged', fontsize=10)
    ax.set_title('Does the shaping change the answer?', fontsize=11.5, weight='bold')
    fig.suptitle('Shaping written as the difference of a number attached to each state '
                 'leaves the best behaviour alone', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'shaping-that-keeps-the-answer.svg')


# ---------------- section 3: a reward model learned from examples ----------------

FEATURES: list[str] = ['always 1', 'row / 4', 'column / 4', 'holding',
                       'steps to the bin / 8', 'steps to the block / 8']


def feats(s: int) -> Arr:
    r, c, h = unsid(s)
    return np.array([1.0, r / 4.0, c / 4.0, float(h),
                     manhattan((r, c), BIN) / 8.0, manhattan((r, c), BLOCK) / 8.0])


FEAT: Arr = np.stack([feats(s) for s in range(NS)])


def _sigmoid(z: Arr) -> Arr:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))


def mixed_policies(seed: int) -> list[tuple[Arr, float]]:
    """Policies of several standards, so attempts of several standards can be drawn."""
    out: list[tuple[Arr, float]] = [(np.zeros((NS, NA)), 1.0)]
    for ep, e in ((300, 0.5), (1200, 0.35), (4000, 0.15)):
        Q, _, _, _ = q_learn(ep, 1.0, seed=seed + ep, eps1=0.2, t=T_DENSE)
        out.append((Q, e))
    return out


def collect_labelled(n: int, seed: int) -> tuple[NDArray[np.int64], Arr]:
    """Attempts of mixed quality, each state labelled by how its attempt ended."""
    pols = mixed_policies(seed)
    rng = np.random.default_rng(seed + 1)
    states: list[int] = []
    labels: list[float] = []
    wins = 0
    for i in range(n):
        Q, e = pols[i % len(pols)]
        ss, aa, rr, out = rollout(Q, rng, e, W2)
        y = 1.0 if out == 'bin' else 0.0
        wins += int(y)
        for s in ss:
            states.append(int(s))
            labels.append(y)
    print(f'[reward model] {n} example attempts, {wins} of them ended with the block in '
          f'the bin, giving {len(states)} labelled states')
    return np.array(states), np.array(labels)


def fit_reward_model(states: NDArray[np.int64], labels: Arr, steps: int = 4000,
                     lr: float = 0.4, l2: float = 0.02) -> Arr:
    X = FEAT[states]
    w = np.zeros(X.shape[1])
    for _ in range(steps):
        p = _sigmoid(X @ w)
        w -= lr * ((X.T @ (p - labels)) / len(labels) + l2 * w)
    return w


RM: tuple[Arr, NDArray[np.int64], Arr] | None = None


def reward_model() -> tuple[Arr, NDArray[np.int64], Arr]:
    global RM
    if RM is None:
        st, lb = collect_labelled(400, 55)
        w = fit_reward_model(st, lb)
        acc = float((( _sigmoid(FEAT[st] @ w) > 0.5) == (lb > 0.5)).mean())
        print('[reward model] fitted weights: ' + ', '.join(
            f'{n} {v:+.2f}' for n, v in zip(FEATURES, w)))
        print(f'[reward model] it labels {acc:.2f} of the training states right')
        RM = (w, st, lb)
    return RM


def the_examples_it_learns_from() -> None:
    w, st, lb = reward_model()
    win = np.bincount(st[lb > 0.5], minlength=NS).astype(float)
    lose = np.bincount(st[lb < 0.5], minlength=NS).astype(float)
    win2 = win.reshape(-1, 2).sum(1).repeat(2)
    lose2 = lose.reshape(-1, 2).sum(1).repeat(2)
    print(f'[reward model] states visited by attempts that worked: {int(win.sum())}; '
          f'by attempts that failed: {int(lose.sum())}')
    print(f'[reward model] the bin square was visited {int(win2[sid(*BIN, False)])} times '
          f'in attempts that worked and {int(lose2[sid(*BIN, False)])} times in attempts '
          f'that failed')
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.3), facecolor='white')
    for ax, vals, name in ((axes[0], win2, 'visits during attempts that worked'),
                           (axes[1], lose2, 'visits during attempts that failed')):
        _table(ax, name, small=True, label_top=True)
        _draw_numbers(ax, vals, False, '{:.0f}', 9.5, dy=-0.2)
    fig.suptitle('The examples a reward model is fitted to: squares the arm stood on, '
                 'labelled by how the attempt ended', fontsize=12.5, weight='bold',
                 color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-examples-it-learns-from.svg')


def what_the_reward_model_scores() -> None:
    w, st, lb = reward_model()
    score = _sigmoid(FEAT @ w)
    print(f'[reward model] score at the bin holding the block {score[sid(*BIN, True)]:.2f}; '
          f'at the bin with an empty gripper {score[sid(*BIN, False)]:.2f}; '
          f'at the start {score[S0]:.2f}')
    fig, axes = plt.subplots(1, 3, figsize=(15.4, 5.0), facecolor='white')
    for ax, holding, name in ((axes[0], False, 'empty gripper'),
                              (axes[1], True, 'holding the block')):
        _table(ax, f'Score of every square, {name}', small=True, label_top=True)
        _draw_numbers(ax, score, holding, '{:.2f}', 9.5, dy=-0.2)
    ax = axes[2]
    _plain(ax)
    ax.barh(np.arange(len(w)), w, color=[LINK if v >= 0 else GRIP for v in w],
            edgecolor=INK, lw=0.6)
    ax.set_yticks(np.arange(len(w)))
    ax.set_yticklabels(FEATURES, fontsize=9.5)
    for i, v in enumerate(w):
        ax.text(v + (0.12 if v >= 0 else -0.12), i, f'{v:+.2f}',
                ha='left' if v >= 0 else 'right', va='center', fontsize=9.5)
    ax.axvline(0, color=INK, lw=0.9)
    ax.set_xlim(min(w) - 1.2, max(w) + 1.2)
    ax.set_xlabel('weight the model gives the measurement', fontsize=10)
    ax.set_title('What it decided mattered', fontsize=11.5, weight='bold')
    fig.suptitle('The learned reward model: a score between 0 and 1 for every state',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'what-the-reward-model-scores.svg')


def how_well_it_tells_them_apart() -> None:
    w, st, lb = reward_model()
    p = _sigmoid(FEAT[st] @ w)
    acc = float(((p > 0.5) == (lb > 0.5)).mean())
    good, bad = p[lb > 0.5], p[lb < 0.5]
    print(f'[reward model] average score {good.mean():.2f} on states from attempts that '
          f'worked and {bad.mean():.2f} on states from attempts that failed; it labels '
          f'{acc:.2f} of them right')
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bins = np.linspace(0, 1, 26)
    ax.hist(bad, bins=bins, color=GRIP, alpha=0.7, label='states from attempts that failed')
    ax.hist(good, bins=bins, color=SLIDE, alpha=0.7, label='states from attempts that worked')
    ax.axvline(0.5, color=INK, ls='--', lw=1.2)
    ax.set_xlabel('score the model gives the state', fontsize=10)
    ax.set_ylabel('how many states', fontsize=10)
    ax.set_title(f'It gets {acc:.0%} of them on the right side of 0.5', fontsize=11.5,
                 weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax = axes[1]
    _plain(ax)
    V, Qt = value_iteration(0.95, t=T_TRUE)
    ss, aa, rr, out = greedy_path(Qt, t=T_TRUE)
    along = _sigmoid(FEAT[ss] @ w)
    ax.plot(np.arange(len(ss)), along, marker='o', color=PURPLE, lw=2.0)
    for i, v in enumerate(along):
        ax.text(i, v + 0.025, f'{v:.2f}', ha='center', fontsize=8.5)
    ax.set_ylim(0, 1.08)
    ax.set_xticks(np.arange(len(ss)))
    ax.set_xticklabels([ACTIONS[a][:1].upper() for a in aa], fontsize=9)
    ax.set_xlabel('the ten actions of a good attempt', fontsize=10)
    ax.set_ylabel('score the model gives the state reached', fontsize=10)
    ax.set_title('Along a good attempt the score climbs', fontsize=11.5, weight='bold')
    print(f'[reward model] along a good attempt the score goes '
          f'{[round(float(v), 2) for v in along]}')
    fig.suptitle('A learned reward model turns "did it work" into a number for every '
                 'step', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'how-well-it-tells-them-apart.svg')


def model_reward_tables() -> Tables:
    w, st, lb = reward_model()
    score = _sigmoid(FEAT @ w)
    P, R, D, OUT, STAY = W2
    R2 = score[P] - 0.1
    return P, R2, D, OUT, STAY


def training_against_the_model() -> None:
    tab = model_reward_tables()
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    checkpoints = [250, 500, 1000, 2000, 4000, 6000]
    V, Qhonest = value_iteration(0.95, t=T_TRUE)
    hss, haa, hrr, hout = greedy_path(Qhonest, t=T_TRUE)
    honest_score = float(np.mean(score[hss]))
    print(f'[against model] a policy that really does the job scores '
          f'{honest_score:.3f} on the same model')
    model_score: list[float] = []
    real: list[float] = []
    for n in checkpoints:
        ms, rs = [], []
        for seed in range(3):
            Q, _, _, _ = q_learn(n, 1.0, seed=180 + seed, eps1=0.05, t=tab)
            rng = np.random.default_rng(5000 + seed)
            sc, hit = [], []
            for _ in range(40):
                ss, aa, rr, out = rollout(Q, rng, 0.0, W2)
                sc.append(float(np.mean(score[ss])))
                hit.append(1.0 if out == 'bin' else 0.0)
            ms.append(float(np.mean(sc)))
            rs.append(float(np.mean(hit)))
        model_score.append(float(np.mean(ms)))
        real.append(float(np.mean(rs)))
        print(f'[against model] after {n} attempts: average score the model gives the '
              f'states visited {model_score[-1]:.3f}, share of attempts that really '
              f'reach the bin {real[-1]:.2f}')
    fig, ax = plt.subplots(figsize=(9.4, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(checkpoints, model_score, marker='o', color=PURPLE, lw=2.1,
            label='average score the reward model gives')
    ax.plot(checkpoints, real, marker='s', color=SLIDE, lw=2.1,
            label='share of attempts that really reach the bin')
    ax.axhline(honest_score, color=INK, ls='--', lw=1.3)
    ax.text(checkpoints[0], honest_score + 0.03, f'a policy that does the job scores '
            f'only {honest_score:.2f}', ha='left', fontsize=9.5, color=INK)
    for x, v in zip(checkpoints, model_score):
        ax.text(x, v + 0.03, f'{v:.2f}', ha='center', fontsize=9, color=PURPLE)
    for x, v in zip(checkpoints, real):
        ax.text(x, v + 0.03, f'{v:.2f}', ha='center', fontsize=9, color=SLIDE)
    ax.set_ylim(-0.06, 1.12)
    ax.set_xlabel('attempts of training against the learned reward model', fontsize=10)
    ax.set_ylabel('score, and share of attempts', fontsize=10)
    ax.set_title('Training on the model\'s score alone', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center right',
              bbox_to_anchor=(1.0, 0.32))
    fig.tight_layout()
    _save(fig, RW_DOC, 'training-against-the-model.svg')


# ---------------- section 4: learning a reward from preferences ----------------

def sample_attempts(n: int, seed: int) -> list[tuple[NDArray[np.int64], float, str]]:
    """Attempts from policies of several standards, so the pairs are worth judging."""
    rng = np.random.default_rng(seed)
    pols: list[tuple[Arr, float]] = [(np.zeros((NS, NA)), 1.0)]
    for ep, e in ((400, 0.4), (1500, 0.25), (4000, 0.1)):
        Q, _, _, _ = q_learn(ep, 1.0, seed=seed + ep, eps1=0.2, t=T_DENSE)
        pols.append((Q, e))
    out: list[tuple[NDArray[np.int64], float, str]] = []
    for i in range(n):
        Q, e = pols[i % len(pols)]
        ss, aa, rr, res = rollout(Q, rng, e, W2)
        out.append((ss, float(T_TRUE[1][ss, aa].sum()), res))
    return out


def fit_from_preferences(pairs: list[tuple[int, int, int]],
                         eps_list: list[tuple[NDArray[np.int64], float, str]],
                         steps: int = 3000, lr: float = 0.2, l2: float = 0.02) -> Arr:
    """Bradley-Terry: make the better-liked attempt score higher."""
    sums = np.stack([FEAT[ss].sum(0) for ss, _, _ in eps_list])
    w = np.zeros(FEAT.shape[1])
    A = np.array([p[0] for p in pairs])
    B = np.array([p[1] for p in pairs])
    y = np.array([float(p[2]) for p in pairs])
    dif = sums[A] - sums[B]
    for _ in range(steps):
        p = _sigmoid(dif @ w)
        w -= lr * ((dif.T @ (p - y)) / max(len(pairs), 1) + l2 * w)
    return w


def make_pairs(eps_list: list[tuple[NDArray[np.int64], float, str]], n: int,
               tau: float, seed: int) -> list[tuple[int, int, int]]:
    rng = np.random.default_rng(seed)
    out: list[tuple[int, int, int]] = []
    for _ in range(n):
        i, j = int(rng.integers(len(eps_list))), int(rng.integers(len(eps_list)))
        if i == j:
            continue
        gi, gj = eps_list[i][1], eps_list[j][1]
        p = float(_sigmoid(np.array([(gi - gj) / tau]))[0])
        out.append((i, j, int(rng.random() < p)))
    return out


PREF: tuple[list[tuple[NDArray[np.int64], float, str]], Arr] | None = None
PREF_TAU: float = 0.5


def preference_fit() -> tuple[list[tuple[NDArray[np.int64], float, str]], Arr]:
    global PREF
    if PREF is None:
        eps_list = sample_attempts(600, 33)
        pairs = make_pairs(eps_list, 2000, PREF_TAU, 34)
        w = fit_from_preferences(pairs, eps_list)
        print(f'[preferences] {len(eps_list)} attempts, {len(pairs)} judged pairs')
        print('[preferences] fitted weights: ' + ', '.join(
            f'{n} {v:+.2f}' for n, v in zip(FEATURES, w)))
        PREF = (eps_list, w)
    return PREF


def a_pair_to_judge() -> None:
    eps_list, w = preference_fit()
    good = max(eps_list, key=lambda e: e[1])
    poor = min(eps_list, key=lambda e: e[1])
    scores = [float(FEAT[e[0]].sum(0) @ w) for e in (good, poor)]
    print(f'[preferences] the pair shown: one attempt with true reward {good[1]:.2f} '
          f'ending as "{good[2]}", one with {poor[1]:.2f} ending as "{poor[2]}"')
    print(f'[preferences] the fitted model scores them {scores[0]:.2f} and '
          f'{scores[1]:.2f}, so it agrees with the person')
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.3), facecolor='white')
    for ax, (ss, g, res), colour, name, sc in (
            (axes[0], good, SLIDE, 'attempt A', scores[0]),
            (axes[1], poor, GRIP, 'attempt B', scores[1])):
        _table(ax, f'{name}: {len(ss)} actions, ended as "{res}"', small=True)
        pts = np.array([_cell_xy(*unsid(int(s))[:2]) for s in ss])
        jit = np.linspace(-0.07, 0.07, len(pts))
        ax.plot(pts[:, 0] + jit, pts[:, 1] + jit, color=colour, lw=1.6, alpha=0.85)
        ax.scatter(pts[0, 0], pts[0, 1], s=55, color=colour, zorder=6)
        ax.text(2.5, -0.32, f'true reward {g:.2f}, fitted score {sc:.2f}', ha='center',
                fontsize=10, color=INK)
    fig.suptitle('A person is shown two attempts and says which they prefer; nobody '
                 'has to write a number', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'a-pair-to-judge.svg')


def what_the_preferences_taught() -> None:
    eps_list, w = preference_fit()
    fitted = FEAT @ w
    print(f'[preferences] the fitted per-state reward: at the start {fitted[S0]:.2f}, '
          f'on the block empty {fitted[sid(*BLOCK, False)]:.2f}, on the block holding '
          f'{fitted[sid(*BLOCK, True)]:.2f}, at the bin holding '
          f'{fitted[sid(*BIN, True)]:.2f}')
    fig, axes = plt.subplots(1, 3, figsize=(15.4, 5.0), facecolor='white')
    for ax, holding, name in ((axes[0], False, 'empty gripper'),
                              (axes[1], True, 'holding the block')):
        _table(ax, f'Fitted reward per square, {name}', small=True, label_top=True)
        _draw_numbers(ax, fitted, holding, '{:+.2f}', 9.0, dy=-0.2)
    ax = axes[2]
    _plain(ax)
    ax.barh(np.arange(len(w)), w, color=[LINK if v >= 0 else GRIP for v in w],
            edgecolor=INK, lw=0.6)
    ax.set_yticks(np.arange(len(w)))
    ax.set_yticklabels(FEATURES, fontsize=9.5)
    for i, v in enumerate(w):
        ax.text(v + (0.03 if v >= 0 else -0.03), i, f'{v:+.2f}',
                ha='left' if v >= 0 else 'right', va='center', fontsize=9.5)
    ax.axvline(0, color=INK, lw=0.9)
    ax.set_xlim(min(w) - 0.5, max(w) + 0.5)
    ax.set_xlabel('weight fitted from the choices', fontsize=10)
    ax.set_title('What the choices taught it', fontsize=11.5, weight='bold')
    fig.suptitle('From choices alone, a reward for every state',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'what-the-preferences-taught.svg')


def how_many_pairs() -> None:
    eps_list, _ = preference_fit()
    test = make_pairs(eps_list, 2000, 0.01, 99)
    counts = [10, 25, 50, 100, 250, 500, 1000, 2000]
    agree: list[float] = []
    for n in counts:
        got = []
        for seed in range(8):
            pairs = make_pairs(eps_list, n, PREF_TAU, 200 + seed)
            w = fit_from_preferences(pairs, eps_list)
            sums = np.stack([FEAT[ss].sum(0) for ss, _, _ in eps_list])
            sc = sums @ w
            ok = [int((sc[i] > sc[j]) == bool(y)) for i, j, y in test]
            got.append(float(np.mean(ok)))
        agree.append(float(np.mean(got)))
        print(f'[preferences] trained on {n:4d} judged pairs: agrees with the true '
              f'ordering on {agree[-1]:.3f} of held-out pairs')
    fig, ax = plt.subplots(figsize=(8.8, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(counts, agree, marker='o', color=TEAL, lw=2.1)
    for x, v in zip(counts, agree):
        ax.text(x, v + 0.012, f'{v:.2f}', ha='center', fontsize=9)
    ax.set_xscale('log')
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.axhline(0.5, color=MUTED, ls='--', lw=1.2)
    ax.text(12, 0.515, 'guessing', fontsize=9, color=MUTED)
    ax.set_ylim(0.45, 1.03)
    ax.set_xlabel('number of judged pairs used to fit the reward (log scale)',
                  fontsize=10)
    ax.set_ylabel('share of held-out pairs it orders the same way', fontsize=10)
    ax.set_title('How many choices it takes', fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'how-many-pairs.svg')


def people_make_mistakes() -> None:
    eps_list, _ = preference_fit()
    test = make_pairs(eps_list, 2000, 0.01, 99)
    counts = [25, 100, 500, 2000]
    fig, ax = plt.subplots(figsize=(9.0, 5.2), facecolor='white')
    _plain(ax)
    for tau, colour, name in ((PREF_TAU, SLIDE, 'careful judge'), (2.0, LINK, 'ordinary judge'),
                              (8.0, GRIP, 'careless judge')):
        agree = []
        for n in counts:
            got = []
            for seed in range(8):
                pairs = make_pairs(eps_list, n, tau, 300 + seed)
                w = fit_from_preferences(pairs, eps_list)
                sums = np.stack([FEAT[ss].sum(0) for ss, _, _ in eps_list])
                sc = sums @ w
                got.append(float(np.mean([int((sc[i] > sc[j]) == bool(y))
                                          for i, j, y in test])))
            agree.append(float(np.mean(got)))
        flip = float(np.mean([1.0 / (1.0 + np.exp(-abs(eps_list[i][1] - eps_list[j][1])
                                                  / tau)) for i, j, _ in test[:500]]))
        print(f'[preferences] a judge who picks the better attempt {flip:.2f} of the '
              f'time: agreement by pair count ' +
              ', '.join(f'{n}:{a:.2f}' for n, a in zip(counts, agree)))
        ax.plot(counts, agree, marker='o', color=colour, lw=2.1,
                label=f'{name}, right {flip:.0%} of the time')
    ax.set_xscale('log')
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.axhline(0.5, color=MUTED, ls='--', lw=1.2)
    ax.set_ylim(0.45, 1.06)
    ax.set_xlabel('number of judged pairs (log scale)', fontsize=10)
    ax.set_ylabel('share of held-out pairs it orders the same way', fontsize=10)
    ax.set_title('A careless judge costs pairs, not correctness', fontsize=12,
                 weight='bold', color=INK)
    ax.text(26, 0.515, 'guessing', fontsize=9, color=MUTED)
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    fig.tight_layout()
    _save(fig, RW_DOC, 'people-make-mistakes.svg')


# ---------------- section 5: verifiers ----------------

def verifier(out: str) -> int:
    """A three-line program: did the block end up in the bin?"""
    return 1 if out == 'bin' else 0


def the_verifier_along_an_attempt() -> None:
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    V, Qt = value_iteration(0.95, t=T_TRUE)
    good = greedy_path(Qt, t=T_TRUE)
    rng = np.random.default_rng(7)
    V2, Qd = value_iteration(0.95, t=T_DIST)
    poor = greedy_path(Qd, t=T_DIST)
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), facecolor='white', sharey=True)
    for ax, (ss, aa, rr, out), name, colour in (
            (axes[0], good, 'an attempt that works', SLIDE),
            (axes[1], poor, 'an attempt that waits by the block', GRIP)):
        _plain(ax)
        n = min(len(ss), 20)
        ax.plot(np.arange(n), score[ss][:n], marker='o', ms=4, color=PURPLE, lw=1.9,
                label='score from the learned reward model')
        ver = np.zeros(n)
        if out == 'bin' and len(ss) <= n:
            ver[len(ss) - 1] = 1.0
        ax.step(np.arange(n), ver, where='post', color=colour, lw=2.2,
                label='answer from the verifier program')
        ax.set_ylim(-0.05, 1.12)
        ax.set_xlabel('step of the attempt', fontsize=10)
        ax.set_title(f'{name}: verifier says {verifier(out)}', fontsize=11.5,
                     weight='bold')
        ax.legend(fontsize=9, frameon=False, loc='upper left')
        print(f'[verifier] {name}: ends as "{out}", verifier answer {verifier(out)}, '
              f'reward model score along the way '
              f'{[round(float(v), 2) for v in score[ss][:12]]}')
    axes[0].set_ylabel('score, and the verifier answer', fontsize=10)
    fig.suptitle('A verifier answers once and is never wrong; a reward model answers '
                 'every step and sometimes is', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-verifier-along-an-attempt.svg')


def where_they_disagree() -> None:
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    eps_list = sample_attempts(400, 44)
    model = np.array([float(np.mean(score[ss])) for ss, _, _ in eps_list])
    passed = np.array([verifier(res) for _, _, res in eps_list])
    cut = float(np.median(model[passed == 1])) if passed.any() else 0.5
    fooled = int(((model >= cut) & (passed == 0)).sum())
    missed = int(((model < cut) & (passed == 1)).sum())
    print(f'[verifier] of {len(eps_list)} attempts the verifier passes {int(passed.sum())}')
    print(f'[verifier] taking the model score of a middling passing attempt as the bar, '
          f'{fooled} failing attempts score above it and {missed} passing attempts score '
          f'below it')
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    bins = np.linspace(0, 1, 26)
    ax.hist(model[passed == 0], bins=bins, color=GRIP, alpha=0.7,
            label='the verifier says no')
    ax.hist(model[passed == 1], bins=bins, color=SLIDE, alpha=0.7,
            label='the verifier says yes')
    ax.axvline(cut, color=INK, ls='--', lw=1.3)
    ax.text(cut - 0.02, ax.get_ylim()[1] * 0.92, f'a middling passing\nattempt scores '
            f'{cut:.2f}', fontsize=9, color=INK, ha='right')
    ax.set_xlabel('average score the reward model gives the attempt', fontsize=10)
    ax.set_ylabel('how many attempts', fontsize=10)
    ax.set_title('The model and the verifier are not the same measurement',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax = axes[1]
    _plain(ax)
    xs = np.arange(2)
    ax.bar(xs, [fooled, missed], width=0.5, color=[GRIP, JOINT], edgecolor=INK, lw=0.6)
    for x, v in zip(xs, [fooled, missed]):
        ax.text(x, v + 1.0, str(v), ha='center', fontsize=12, weight='bold')
    ax.set_xticks(xs)
    ax.set_xticklabels(['failed, but scored high', 'passed, but scored low'],
                       fontsize=10)
    ax.set_ylabel('number of attempts', fontsize=10)
    ax.set_ylim(0, max(fooled, missed) * 1.3 + 2)
    ax.set_title(f'Out of {len(eps_list)} attempts', fontsize=11.5, weight='bold')
    fig.suptitle('Where a learned score and a program disagree',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'where-they-disagree.svg')


def what_a_program_can_check() -> None:
    V, Qt = value_iteration(0.95, t=T_TRUE)
    ss, aa, rr, out = greedy_path(Qt, t=T_TRUE)
    r, c, h = unsid(int(ss[-1]))
    checks = [
        ('the block ended up in the bin', True,
         'the outcome of the attempt is recorded', f'answer: {verifier(out)}'),
        ('the gripper finished on the bin square', True,
         'the state holds the row and the column', f'answer: {int((r, c) == BIN)}'),
        ('the gripper was empty at the end', True,
         'the state holds the holding flag', f'answer: {int(not h)}'),
        ('the block was set down gently', False,
         'nothing in the state measures force', 'cannot be answered'),
        ('the block finished the right way up', False,
         'nothing in the state measures turning', 'cannot be answered'),
    ]
    for name, can, why, ans in checks:
        print(f'[verifier] "{name}": {"a program can check it" if can else "no program here can check it"}, '
              f'because {why}; {ans}')
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 4.9), facecolor='white',
                             gridspec_kw={'width_ratios': [0.8, 1.4]})
    ax = axes[0]
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.95, 'Everything the state holds', fontsize=11.5, weight='bold',
            color=INK)
    fields = [('row', f'{r}'), ('column', f'{c}'), ('holding the block', f'{h}'),
              ('how the attempt ended', f'"{out}"')]
    y = 0.80
    for name, val in fields:
        ax.text(0.03, y, name, fontsize=10.5, color=LINK, weight='bold')
        ax.text(0.75, y, val, fontsize=10.5, color=INK)
        y -= 0.14
    ax.text(0.0, y - 0.02, 'These four numbers are the whole record\nof an attempt in '
                           'this world.', fontsize=9.5, color=MUTED, va='top')
    ax = axes[1]
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.95, 'What a short program can decide from them', fontsize=11.5,
            weight='bold', color=INK)
    y = 0.80
    for name, can, why, ans in checks:
        ax.text(0.0, y, 'yes' if can else 'no', fontsize=10.5,
                color=SLIDE if can else GRIP, weight='bold')
        ax.text(0.09, y, name, fontsize=10, color=INK)
        ax.text(0.09, y - 0.055, why, fontsize=8.8, color=MUTED)
        ax.text(0.99, y, ans, fontsize=9.5, color=INK, ha='right')
        y -= 0.165
    fig.suptitle('A verifier can only ask about things the record actually holds',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'what-a-program-can-check.svg')


def learning_from_the_verifier_alone() -> None:
    P, R, D, OUT, STAY = W2
    Rv = np.where(OUT == 'bin', 1.0, 0.0)
    T_VER: Tables = (P, Rv, D, OUT, STAY)
    runs = shaping_runs()
    ver = []
    for seed in range(4):
        _, _, sc, _ = q_learn(6000, SHAPE_EPS, seed=260 + seed, t=T_VER)
        ver.append(sc)
    Varr = np.array(ver)
    print(f'[verifier] trained on the verifier alone: reaches the bin on '
          f'{Varr[:, -200:].mean():.2f} of the last 200 attempts')
    print(f'[verifier] trained on the dense reward: {runs["dense"][:, -200:].mean():.2f}')
    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(np.arange(Varr.shape[1]), _smooth(Varr.mean(0), 200), color=TEAL, lw=2.1,
            label='verifier alone: 1 if the block is in the bin, 0 otherwise')
    ax.plot(np.arange(runs['dense'].shape[1]), _smooth(runs['dense'].mean(0), 200),
            color=WRIST, lw=2.1, label='the dense written reward')
    ax.set_ylim(-0.03, 1.07)
    ax.set_xlim(0, 3200)
    ax.set_xlabel('attempt number (both stay at 1.00 for the remaining 2,800)',
                  fontsize=10)
    ax.set_ylabel('share of attempts that reach the bin', fontsize=10)
    ax.set_title('Four runs each, averaged', fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.suptitle('A verifier is the slowest honest reward there is',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'learning-from-the-verifier-alone.svg')


# ---------------- section 6: reward hacking ----------------

def the_tray_loop() -> None:
    V, Q = value_iteration(0.95, t=T_FARM)
    ss, aa, rr, out = greedy_path(Q, t=T_FARM)
    trays = int(sum(1 for i, a in enumerate(aa) if T_FARM[3][int(ss[i]), int(a)] == 'tray'))
    true_r = float(T_TRUE[1][ss, aa].sum())
    print(f'[hack] with the tray paying +3 and the attempt carrying on, the best policy '
          f'puts the block on the tray {trays} times in one attempt')
    print(f'[hack] it collects {rr.sum():.2f} of the written reward against the '
          f'{8.90:.2f} a proper attempt collects, and the block never reaches the bin '
          f'(the attempt ends as "{out}")')
    print(f'[hack] judged on the real reward it scores {true_r:.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2), facecolor='white')
    ax = axes[0]
    _table(ax, f'The loop: block to tray, {trays} times over', small=True)
    _draw_path(ax, ss, aa, GRIP)
    ax.annotate('block picked up here and\nput down again, over and over',
                xy=(TRAY[1] + 0.52, ROWS - 1 - TRAY[0] + 0.9),
                xytext=(0.05, ROWS - 1 - TRAY[0] + 2.4), fontsize=9,
                color=GRIP, ha='left',
                arrowprops={'arrowstyle': '->', 'color': GRIP, 'lw': 1.2})
    ax.text(2.5, -0.32, f'all {len(aa)} actions of one attempt, collecting '
                        f'{rr.sum():.2f}', ha='center', fontsize=9.5, color=INK)
    ax = axes[1]
    _plain(ax)
    run = np.cumsum(rr)
    V2, Qt = value_iteration(0.95, t=T_TRUE)
    g2 = greedy_path(Qt, t=T_TRUE)
    honest = np.cumsum(T_FARM[1][g2[0], g2[1]])
    ax.plot(np.arange(len(run)), run, color=GRIP, lw=2.1,
            label='the policy that farms the tray')
    ax.plot(np.arange(len(honest)), honest, color=SLIDE, lw=2.1,
            label='the policy that does the job')
    ax.set_xlabel('step of the attempt', fontsize=10)
    ax.set_ylabel('written reward collected so far', fontsize=10)
    ax.set_title(f'{rr.sum():.1f} against {honest[-1]:.1f}', fontsize=11.5,
                 weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.suptitle('Reward hacking: the highest score in this world is a loop that never '
                 'finishes the job', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-tray-loop.svg')


def high_score_failed_task() -> None:
    cases = [('be near the block', T_DIST), ('a bonus for holding it', T_HOLD),
             ('pay for any tidy place', T_FARM)]
    V0, Qhonest = value_iteration(0.95, t=T_TRUE)
    hack_score, honest_score, hack_bin = [], [], []
    for name, tab in cases:
        V, Qh = value_iteration(0.95, t=tab)
        hp = greedy_path(Qh, t=tab)
        op = greedy_path(Qhonest, t=T_TRUE)
        hack_score.append(float(tab[1][hp[0], hp[1]].sum()))
        honest_score.append(float(tab[1][op[0], op[1]].sum()))
        hack_bin.append(1.0 if hp[3] == 'bin' else 0.0)
        print(f'[hack] "{name}": the best policy under it scores '
              f'{hack_score[-1]:.2f}, a policy that really does the job scores '
              f'{honest_score[-1]:.2f} on the same reward, and the hacking policy puts '
              f'the block in the bin {int(hack_bin[-1])} times')
    fig, ax = plt.subplots(figsize=(10.4, 5.3), facecolor='white')
    _plain(ax)
    xs = np.arange(len(cases))
    ax.bar(xs - 0.2, hack_score, width=0.4, color=GRIP, edgecolor=INK, lw=0.6,
           label='the policy that squeezes the written reward')
    ax.bar(xs + 0.2, honest_score, width=0.4, color=SLIDE, edgecolor=INK, lw=0.6,
           label='the policy that does the job')
    for x, v in zip(xs - 0.2, hack_score):
        ax.text(x, v + 1.5, f'{v:.1f}', ha='center', fontsize=10, weight='bold')
    for x, v in zip(xs + 0.2, honest_score):
        ax.text(x, v + 1.5, f'{v:.1f}', ha='center', fontsize=10, weight='bold')
    for x in xs:
        ax.text(x, -9.5, 'block in the bin: never', ha='center', fontsize=9, color=GRIP)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels([n for n, _ in cases], fontsize=10.5)
    ax.set_ylabel('score on the written reward', fontsize=10)
    ax.set_ylim(-13, max(hack_score) * 1.25)
    ax.set_title('Three written rewards, and what wins under each',
                 fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.suptitle('Every one of these pays more for failing than for finishing',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'high-score-failed-task.svg')


def the_two_scores_come_apart() -> None:
    """Many policies, trained on several different rewards and stopped at several
    points, each measured twice: by the learned reward model and by the real job."""
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    sources = [('the learned reward model', model_reward_tables()),
               ('the true sparse reward', T_TRUE),
               ('the dense written reward', T_DENSE),
               ('a reward for being near the block', T_DIST)]
    xs: list[float] = []
    ys: list[float] = []
    cols: list[str] = []
    colours = [PURPLE, SLIDE, TEAL, GRIP]
    for (name, tab), colour in zip(sources, colours):
        for seed in range(3):
            for n in (300, 800, 2000, 6000):
                Q, _, _, _ = q_learn(n, 1.0, seed=320 + seed, eps1=0.1, t=tab)
                rng = np.random.default_rng(6000 + seed)
                sc, hit = [], []
                for _ in range(25):
                    ss, aa, rr, out = rollout(Q, rng, 0.0, W2)
                    sc.append(float(np.mean(score[ss])))
                    hit.append(1.0 if out == 'bin' else 0.0)
                xs.append(float(np.mean(sc)))
                ys.append(float(np.mean(hit)))
                cols.append(colour)
    xa, ya = np.array(xs), np.array(ys)
    top = xa >= np.quantile(xa, 0.75)
    print(f'[come apart] {len(xa)} policies measured; among the quarter with the '
          f'highest model score, the share of attempts that really reach the bin is '
          f'{ya[top].mean():.2f}, against {ya[~top].mean():.2f} for the rest')
    print(f'[come apart] the best model score is {xa.max():.3f}, and the policy that '
          f'earns it reaches the bin on {ya[int(np.argmax(xa))]:.2f} of attempts')
    fig, ax = plt.subplots(figsize=(9.4, 5.6), facecolor='white')
    _plain(ax)
    jit = np.random.default_rng(1).normal(0, 0.012, len(ya))
    for (name, _), colour in zip(sources, colours):
        m = np.array([c == colour for c in cols])
        ax.scatter(xa[m], ya[m] + jit[m], s=52, color=colour, alpha=0.75, zorder=5,
                   edgecolor='white', lw=0.6, label=f'trained on {name}')
    ax.axvline(float(np.quantile(xa, 0.75)), color=MUTED, ls='--', lw=1.2)
    ax.set_xlabel('average score the learned reward model gives the policy', fontsize=10)
    ax.set_ylabel('share of attempts that really reach the bin', fontsize=10)
    ax.set_ylim(-0.18, 1.35)
    ax.set_title(f'{len(xa)} policies, trained on four different rewards and stopped at '
                 'four points each', fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9, frameon=False, loc='upper center', ncol=2)
    fig.suptitle('A higher score on the learned reward stops meaning a better robot',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'the-two-scores-come-apart.svg')


def two_rewards_together() -> None:
    """The verifier made the main term, with the learned score kept as a nudge."""
    P, R, D, OUT, STAY = W2
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    model_only = model_reward_tables()
    both: Tables = (P, 0.2 * score[P] - 0.1 + np.where(OUT == 'bin', 20.0, 0.0),
                    D, OUT, STAY)
    res: dict[str, float] = {}
    for name, tab in (('the learned reward alone', model_only),
                      ('the verifier, nudged by the learned reward', both)):
        rates = []
        for seed in range(4):
            Q, _, _, _ = q_learn(6000, 1.0, seed=340 + seed, eps1=0.05, t=tab)
            rates.append(evaluate(Q, 30, seed=99, t=W2)[0]['bin'])
        res[name] = float(np.mean(rates))
        print(f'[fix] trained on {name}: reaches the bin on {res[name]:.2f} of attempts')
    fig, ax = plt.subplots(figsize=(8.8, 5.0), facecolor='white')
    _plain(ax)
    names = list(res)
    vals = [res[n] for n in names]
    ax.bar(np.arange(2), vals, width=0.5, color=[GRIP, SLIDE], edgecolor=INK, lw=0.7)
    for x, v in zip(np.arange(2), vals):
        ax.text(x, v + 0.03, f'{v:.2f}', ha='center', fontsize=13, weight='bold')
    ax.set_xticks(np.arange(2))
    ax.set_xticklabels(['the learned reward alone',
                        'the verifier, nudged by\nthe learned reward'], fontsize=10.5)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel('share of attempts that reach the bin', fontsize=10)
    ax.set_title('Four runs of 6,000 attempts each', fontsize=12, weight='bold')
    fig.suptitle('Putting the reward nobody can argue with in charge closes the hole',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'two-rewards-together.svg')


def staying_near_a_trusted_policy() -> None:
    P, R, D, OUT, STAY = W2
    trusted_Q, _, _, _ = q_learn(6000, 1.0, seed=77, eps1=0.05, t=T_DENSE)
    trusted = trusted_Q.argmax(1)
    base = model_reward_tables()[1]
    penalty = np.ones((NS, NA))
    penalty[np.arange(NS), trusted] = 0.0
    betas = [0.0, 1.0, 2.0, 3.0, 3.5, 4.0, 5.0]
    rates, scores = [], []
    w, _, _ = reward_model()
    score = _sigmoid(FEAT @ w)
    for b in betas:
        tab: Tables = (P, base - b * penalty, D, OUT, STAY)
        rr_, ss_ = [], []
        for seed in range(3):
            Q, _, _, _ = q_learn(6000, 1.0, seed=360 + seed, eps1=0.05, t=tab)
            rr_.append(evaluate(Q, 30, seed=99, t=W2)[0]['bin'])
            rng = np.random.default_rng(7000 + seed)
            ss_.append(float(np.mean([np.mean(score[rollout(Q, rng, 0.0, W2)[0]])
                                      for _ in range(20)])))
        rates.append(float(np.mean(rr_)))
        scores.append(float(np.mean(ss_)))
        print(f'[trust] penalty {b:.2f} for differing from the trusted policy: '
              f'reaches the bin on {rates[-1]:.2f} of attempts, learned-reward score '
              f'{scores[-1]:.3f}')
    base_rate = evaluate(trusted_Q, 30, seed=99, t=W2)[0]['bin']
    print(f'[trust] the trusted policy itself reaches the bin on {base_rate:.2f} of '
          f'attempts')
    fig, ax = plt.subplots(figsize=(9.2, 5.3), facecolor='white')
    _plain(ax)
    ax.plot(betas, rates, marker='o', color=SLIDE, lw=2.1,
            label='share of attempts that really reach the bin')
    ax.plot(betas, scores, marker='s', color=PURPLE, lw=2.1,
            label='score from the learned reward model')
    for x, v in zip(betas, rates):
        ax.text(x, v + 0.04, f'{v:.2f}', ha='center', fontsize=9, color=SLIDE)
    for x, v in zip(betas, scores):
        ax.text(x, v - 0.07, f'{v:.2f}', ha='center', fontsize=9, color=PURPLE)
    ax.axhline(base_rate, color=MUTED, ls='--', lw=1.2)
    ax.text(betas[0], base_rate + 0.03, 'the trusted policy itself', ha='left',
            fontsize=9, color=MUTED)
    ax.set_ylim(-0.08, 1.20)
    ax.set_xlabel('how much the policy is charged for each action that differs from '
                  'the trusted one', fontsize=10)
    ax.set_ylabel('share of attempts, and model score', fontsize=10)
    ax.set_title('Three runs at each setting', fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.suptitle('Holding the policy near one that is trusted keeps the hole from being '
                 'found', fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RW_DOC, 'staying-near-a-trusted-policy.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    for fn in (the_little_world, state_and_action, reward_sequence, discounted_return,
               episodes_and_returns, policy_as_a_table, value_on_the_grid,
               policy_and_value_together, value_vs_return, learning_curve,
               policy_before_after, value_before_after, q_values_one_state,
               explore_or_not, where_each_one_ends_up, first_time_at_the_bin,
               the_price_of_exploring, learning_from_old_attempts, on_policy_goes_stale,
               the_clip, with_and_without_the_limit, how_many_attempts,
               the_reality_gap, domain_randomisation, what_randomising_costs,
               the_written_reward, the_hovering_policy, reward_up_task_flat,
               three_behaviours_scored, sparse_against_dense, how_fast_each_one_learns,
               shaping_that_changes_the_answer, shaping_that_keeps_the_answer,
               the_examples_it_learns_from, what_the_reward_model_scores,
               how_well_it_tells_them_apart, training_against_the_model,
               a_pair_to_judge, what_the_preferences_taught, how_many_pairs,
               people_make_mistakes, the_verifier_along_an_attempt, where_they_disagree,
               what_a_program_can_check, learning_from_the_verifier_alone,
               the_tray_loop, high_score_failed_task, the_two_scores_come_apart,
               two_rewards_together, staying_near_a_trusted_policy):
        fn()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
