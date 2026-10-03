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

def rollout(Q: Arr, rng: np.random.Generator, eps: float, t: Tables,
            slip: float = 0.0, maxsteps: int = MAXSTEPS, s0: int = S0
            ) -> tuple[NDArray[np.int64], NDArray[np.int64], Arr, str]:
    """One attempt with an epsilon-greedy policy read off the table Q."""
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
            a = int(cand[0]) if len(cand) == 1 else int(rng.choice(cand))
        ss.append(s)
        aa.append(a)
        rr.append(R[s, a])
        s2 = int(P[s, a])
        if slip > 0.0 and a < 4 and rng.random() < slip:
            s2 = int(STAY[s, a])
        if D[s, a]:
            out = OUT[s, a]
            break
        s = s2
    return np.array(ss), np.array(aa), np.array(rr), out


def q_learn(episodes: int, eps0: float, seed: int, eps1: float | None = None,
            gamma: float = 0.95, alpha: float = 0.3, slip: float = 0.0,
            t: Tables = WORLD, maxsteps: int = MAXSTEPS
            ) -> tuple[Arr, Arr, Arr, list[Arr]]:
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
        ss, aa, rr, out = rollout(Q, rng, e, t, slip, maxsteps)
        for i in range(len(ss) - 1, -1, -1):
            s, a = int(ss[i]), int(aa[i])
            tgt = rr[i] if D[s, a] else rr[i] + gamma * Q[P[s, a]].max()
            Q[s, a] += alpha * (tgt - Q[s, a])
        rets[ep] = rr.sum()
        succ[ep] = 1.0 if out == 'bin' else 0.0
        if ep in marks:
            snaps.append(Q.copy())
    return Q, rets, succ, snaps


def evaluate(Q: Arr, n: int = 60, seed: int = 0, slip: float = 0.0, t: Tables = WORLD,
             maxsteps: int = MAXSTEPS, score: Tables | None = None
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
        ss, aa, rr, out = rollout(Q, rng, 0.0, t, slip, maxsteps)
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

def _table(ax: Axes, title: str = '', marks: bool = True, small: bool = False) -> None:
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
            ax.text(c + 0.5, ROWS - 1 - r + 0.08, label, ha='center', va='bottom',
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
                  size: float = 9.5, shade: bool = True) -> None:
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
            ax.text(x, y - 0.14, fmt.format(layer[r, c]), ha='center', va='center',
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
    axes[0].legend(fontsize=9, frameon=False, loc='upper left')
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
        _table(ax, name, small=True)
        _draw_numbers(ax, V, holding, '{:.2f}', 8.5)
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
    pred: list[float] = []
    real: list[float] = []
    seen: list[bool] = []
    for s in range(NS):
        ss, aa, rr, out = greedy_path(Q, s0=s)
        pred.append(float(Q[s].max()))
        real.append(discounted(rr, gamma))
        seen.append(bool(np.abs(Q[s]).sum() > 1e-9))
    pred_a, real_a, seen_a = np.array(pred), np.array(real), np.array(seen)
    gap = float(np.mean(np.abs(pred_a[seen_a] - real_a[seen_a])))
    print(f'[check] {int(seen_a.sum())} of {NS} states were ever visited; for those the '
          f'value estimate is out by {gap:.3f} on average')
    print(f'[check] the {int((~seen_a).sum())} states never visited keep the value 0 '
          f'they started with')
    fig, ax = plt.subplots(figsize=(7.0, 6.0), facecolor='white')
    _plain(ax)
    lo = min(real_a.min(), pred_a.min()) - 0.5
    hi = max(real_a.max(), pred_a.max()) + 0.5
    ax.plot([lo, hi], [lo, hi], ls='--', color=MUTED, lw=1.2)
    ax.scatter(real_a[seen_a], pred_a[seen_a], s=34, color=LINK, zorder=5,
               label=f'{int(seen_a.sum())} states the learner visited')
    ax.scatter(real_a[~seen_a], pred_a[~seen_a], s=34, color=GRIP, zorder=5,
               marker='x', label=f'{int((~seen_a).sum())} states it never visited')
    ax.set_xlabel('the discounted return the policy really collects from that state',
                  fontsize=10)
    ax.set_ylabel('the value the learner predicts for that state', fontsize=10)
    ax.set_title(f'The value estimate matches the real return to {gap:.2f} on average',
                 fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
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
    for frac in (0.25, 0.5, 0.75, 1.0):
        i = int(frac * len(succ)) - 1
        ax.text(i, _smooth(succ, k)[i] + 0.04, f'{_smooth(succ, k)[i]:.2f}',
                ha='right', fontsize=9, color=PURPLE)
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
    ax.set_ylim(min(0, float(Q[s].min())) - 0.6, float(Q[s].max()) + 1.2)
    ax.set_title('What one state learned: "up" is worth most, because the bin is up '
                 'and to the right', fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, RL_DOC, 'q-values-one-state.svg')
