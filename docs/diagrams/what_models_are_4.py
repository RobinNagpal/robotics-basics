"""Generate the diagrams for two pages of docs/07_learned-models/.

    01_what-models-are/04_learning-signals.md
        -> images/what-models-are/learning-signals/
    09_making-models-work-on-an-arm/01_overview.md
        -> images/making-models-work-on-an-arm/overview/

Run with:  pixi run python ../docs/diagrams/what_models_are_4.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the documents can quote the same values. The worked example is
simulated: a one-joint arm must put its gripper over a mug that sits somewhere
on a 40 cm line. The arm has a quirk nobody wrote down: it lands at
0.9 x command + 1.0 cm, plus a little noise. The arm is taught the job three
ways, with the three kinds of learning signal that fit an action:

    imitation          20 demonstrations from a careful person, then a straight-line fit
    self-supervised    50 random pokes, each one labelled by the arm's own position sensor
    reinforcement      trial and error with a score, from scratch and from the copied policy

The methods are real (least squares and a simple keep-the-better-one search),
written in NumPy.
"""

import pathlib
import sys
from dataclasses import dataclass

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (  # noqa: E402
    Arc, FancyArrowPatch, FancyBboxPatch, Rectangle,
)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

DOCS: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
IMAGES: pathlib.Path = DOCS / 'images'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
PURPLE: str = '#6a4fb3'
INK: str = '#222222'
MUTED: str = '#777777'
PALE: str = '#f4f4f4'

MUG: str = LINK
GOOD: str = SLIDE
BAD: str = GRIP
MONO: str = 'DejaVu Sans Mono'

Arr = NDArray[np.float64]

# the one-joint arm of the worked example
GAIN: float = 0.9        # the arm lands at GAIN * command + OFFSET
OFFSET: float = 1.0      # cm
NOISE: float = 0.3       # cm, spread of where the arm lands for the same command
TOL: float = 1.0         # cm, a reach counts as a success if it lands this close
MID: float = 20.0        # cm, the middle of the line, used to centre the policy
LO, HI = 5.0, 35.0       # cm, where the mug can be
N_DEMOS: int = 20
HABIT: float = 1.2       # cm, the person stops this far short of the mug
HAND: float = 0.6        # cm, spread of where the person stops
N_POKES: int = 50
N_TRIALS: int = 400
PER_TRIAL: int = 5       # mugs per trial; each trial reaches 2 x PER_TRIAL times
SCRATCH: tuple[float, float] = (0.5, 5.0)   # the starting guess with no demonstrations


# --------------------------------------------------------------------------
# small drawing helpers (same style as what_models_are_1.py)
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', family: str | None = None,
           va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            family=family, zorder=7)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 13,
           color: str = INK) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=color, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.8, rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=16, color=color,
                                 lw=lw, connectionstyle=f'arc3,rad={rad}', zorder=6))


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = LINK_PALE,
         edge: str = LINK, lw: float = 1.5) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.15',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=3))


def _mug(ax: Axes, x: float, y: float, w: float, h: float, color: str = MUG) -> None:
    """A mug seen from the side: a body with a handle on the right. (x, y) is the bottom left."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=INK, lw=1.0, zorder=4))
    ax.add_patch(Arc((x + w, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90, theta2=90,
                     color=INK, lw=3.2, zorder=3))
    ax.add_patch(Arc((x + w, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90, theta2=90,
                     color=color, lw=1.8, zorder=3))


def _gripper(ax: Axes, x: float, y: float, w: float = 0.9, h: float = 0.7,
             color: str = INK) -> None:
    """A two-finger gripper seen from the side, fingers pointing down. (x, y) is the fingertip middle."""
    ax.plot([x, x], [y + h, y + h + 1.2], color=color, lw=3, zorder=5, solid_capstyle='butt')
    ax.plot([x - w / 2, x + w / 2], [y + h, y + h], color=color, lw=3, zorder=5)
    ax.plot([x - w / 2, x - w / 2], [y, y + h], color=color, lw=3, zorder=5)
    ax.plot([x + w / 2, x + w / 2], [y, y + h], color=color, lw=3, zorder=5)


def _frame(ax: Axes, x: float, y: float, w: float, h: float) -> None:
    """A camera picture: a grey frame with a table line along the bottom."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor='white', edgecolor=MUTED, lw=1.2, zorder=2))
    ax.plot([x + 0.2, x + w - 0.2], [y + 0.8, y + 0.8], color=MUTED, lw=1.2, zorder=3)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        flat = folder.replace('/', '__')
        fig.savefig(PNG_DIR / f'{flat}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


# --------------------------------------------------------------------------
# the worked example: a one-joint arm reaching for a mug
# --------------------------------------------------------------------------

def _lands(w: float, c: float, p: Arr, noise: Arr) -> Arr:
    """Where the gripper lands when the policy 'command = w * (p - MID) + c' sees a mug at p."""
    return GAIN * (w * (p - MID) + c) + OFFSET + noise


_TEST_RNG = np.random.default_rng(99)
TEST_P: Arr = _TEST_RNG.uniform(LO, HI, 2000)
TEST_N: Arr = _TEST_RNG.normal(0.0, NOISE, 2000)


def success(w: float, c: float) -> float:
    """Share of 2000 test mugs that the policy lands within TOL of."""
    return float(np.mean(np.abs(_lands(w, c, TEST_P, TEST_N) - TEST_P) < TOL))


@dataclass
class Worked:
    demo_p: Arr
    demo_miss: Arr
    imit: tuple[float, float]
    poke_u: Arr
    poke_x: Arr
    self_fit: tuple[float, float]           # fitted gain and offset
    self_policy: tuple[float, float]
    curve_scratch: Arr
    curve_imit: Arr
    rl_scratch: tuple[float, float]
    rl_imit: tuple[float, float]


def _trial_and_error(w: float, c: float, seed: int) -> tuple[Arr, tuple[float, float]]:
    """Keep-the-better-one search. Each trial tries a small random change on PER_TRIAL mugs.

    The old and the new policy reach for the same mugs, and the one with the smaller
    average miss is kept. The score is the only feedback: nobody says what the right
    command was.
    """
    r = np.random.default_rng(seed)
    curve = [success(w, c)]
    for _ in range(N_TRIALS):
        w2, c2 = w + r.normal(0, 0.02), c + r.normal(0, 0.3)
        p = r.uniform(LO, HI, PER_TRIAL)
        nz = r.normal(0, NOISE, PER_TRIAL)
        old = np.mean(np.abs(_lands(w, c, p, nz) - p))
        new = np.mean(np.abs(_lands(w2, c2, p, nz) - p))
        if new < old:
            w, c = w2, c2
        curve.append(success(w, c))
    return np.array(curve), (w, c)


def _worked() -> Worked:
    rng = np.random.default_rng(0)

    # imitation: a careful person stops a little short of the mug
    p = rng.uniform(LO, HI, N_DEMOS)
    stop = p - HABIT + rng.normal(0, HAND, N_DEMOS)
    u = (stop - OFFSET) / GAIN                     # the command that made the arm stop there
    a = np.column_stack([p - MID, np.ones_like(p)])
    w, c = np.linalg.lstsq(a, u, rcond=None)[0]

    # self-supervised: the arm pokes at random and its own sensor says where it landed
    pr = np.random.default_rng(1)
    pu = pr.uniform(0, 40, N_POKES)
    px = GAIN * pu + OFFSET + pr.normal(0, NOISE, N_POKES)
    g, o = np.linalg.lstsq(np.column_stack([pu, np.ones_like(pu)]), px, rcond=None)[0]
    self_policy = (1 / g, (MID - o) / g)          # command that lands on p: (p - o) / g

    curve_s, rl_s = _trial_and_error(*SCRATCH, seed=10)
    curve_i, rl_i = _trial_and_error(w, c, seed=10)
    return Worked(p, stop - p, (w, c), pu, px, (g, o), self_policy,
                  curve_s, curve_i, rl_s, rl_i)


def _first_at(curve: Arr, level: float) -> int:
    hit = np.nonzero(curve >= level)[0]
    return int(hit[0]) if hit.size else -1


def _report(k: Worked) -> None:
    true = (1 / GAIN, (MID - OFFSET) / GAIN)
    print(f'[arm] lands at {GAIN} x command + {OFFSET} cm, noise {NOISE} cm; success = within {TOL} cm')
    print(f'[arm] perfect policy w = {true[0]:.3f}, c = {true[1]:.2f}: success {success(*true):.3f}')
    print(f'[imitation] {N_DEMOS} demos, person stops {HABIT} cm short (spread {HAND}); '
          f'demo miss mean {k.demo_miss.mean():.2f} cm, within {TOL} cm: '
          f'{np.mean(np.abs(k.demo_miss) < TOL):.2f}')
    print(f'[imitation] fitted w = {k.imit[0]:.3f}, c = {k.imit[1]:.2f}: success {success(*k.imit):.3f}; '
          f'mean miss {np.mean(_lands(*k.imit, TEST_P, TEST_N) - TEST_P):.2f} cm')
    print(f'[self] {N_POKES} pokes: fitted gain {k.self_fit[0]:.3f}, offset {k.self_fit[1]:.2f}; '
          f'policy w = {k.self_policy[0]:.3f}, c = {k.self_policy[1]:.2f}: success {success(*k.self_policy):.3f}')
    for name, cv, fin in (('scratch', k.curve_scratch, k.rl_scratch),
                          ('from imitation', k.curve_imit, k.rl_imit)):
        pts = ', '.join(f'{t}: {cv[t]:.3f}' for t in (0, 10, 50, 100, 150, 200, 300, 400))
        print(f'[trial and error, {name}] success after trials: {pts}')
        print(f'[trial and error, {name}] first trial at >= 0.90: {_first_at(cv, 0.9)}, '
              f'>= 0.95: {_first_at(cv, 0.95)}; final w = {fin[0]:.3f}, c = {fin[1]:.2f}; '
              f'reaches per trial {2 * PER_TRIAL}')


# --------------------------------------------------------------------------
# 04_learning-signals.md
# --------------------------------------------------------------------------

def four_kinds() -> None:
    """One training example of each kind: what the model is given, and where its answer comes from."""
    fig, axes = plt.subplots(1, 4, figsize=(17, 6.6), facecolor='white')
    heads = [('Supervised', LINK), ('Self-supervised', PURPLE),
             ('Imitation', SLIDE), ('Reinforcement', WRIST)]
    for ax, (head, col) in zip(axes, heads):
        _axes(ax, (0, 10), (0, 12.5))
        _title(ax, 5, 12.0, head, color=col)
        _label(ax, 5, 11.1, 'the model is given', size=10, color=MUTED)
        _frame(ax, 1.5, 6.3, 7.0, 4.3)
        _arrow(ax, (5, 6.1), (5, 4.9), color=col)
        _label(ax, 5, 4.5, 'what it gets back' if head == 'Reinforcement' else 'the right answer',
               size=10, color=MUTED)
        _box(ax, 1.0, 1.9, 8.0, 2.2, face='white', edge=col)

    # supervised: a person drew a box and wrote a name
    ax = axes[0]
    _mug(ax, 4.0, 7.1, 1.4, 1.9)
    ax.add_patch(Rectangle((3.6, 6.9), 2.6, 2.5, fill=False, edgecolor=GRIP, lw=2, zorder=6))
    _label(ax, 3.7, 9.8, '"mug"', size=10, color=GRIP, ha='left')
    _label(ax, 5, 3.0, 'a box and the name "mug"', size=11)
    _label(ax, 5, 0.9, 'from a person\'s labels', size=11, weight='bold', color=LINK)

    # self-supervised: part of the picture is hidden, and the hidden part is the answer
    ax = axes[1]
    _mug(ax, 4.0, 7.1, 1.4, 1.9)
    ax.add_patch(Rectangle((5.1, 7.0), 1.6, 2.3, facecolor='#9a9a9a', edgecolor=INK, lw=1,
                           zorder=6))
    _label(ax, 5.9, 8.15, '?', size=16, color='white', weight='bold')
    # the answer: the patch that was hidden
    ax.add_patch(Rectangle((3.0, 2.2), 1.6, 1.6, facecolor='white', edgecolor=INK, lw=1,
                           zorder=4))
    ax.add_patch(Arc((3.1, 3.0), 1.1, 1.1, theta1=-90, theta2=90, color=INK, lw=3.2, zorder=5))
    ax.add_patch(Arc((3.1, 3.0), 1.1, 1.1, theta1=-90, theta2=90, color=MUG, lw=1.8, zorder=5))
    _label(ax, 5.1, 3.0, 'the hidden\npart', size=11, ha='left')
    _label(ax, 5, 0.9, 'from the picture itself', size=11, weight='bold', color=PURPLE)

    # imitation: what the person did with the arm at this moment
    ax = axes[2]
    _mug(ax, 5.3, 7.1, 1.4, 1.9)
    _gripper(ax, 3.0, 8.0)
    _label(ax, 5, 3.0, 'the command the person\ngave: "move 2 cm right"', size=11)
    _label(ax, 5, 0.9, 'from a person\'s demonstration', size=11, weight='bold', color=SLIDE)

    # reinforcement: the arm tried, and got a score
    ax = axes[3]
    ax.add_patch(Rectangle((4.2, 7.1), 1.9, 1.4, facecolor=MUG, edgecolor=INK, lw=1.0,
                           zorder=4))
    _label(ax, 5.15, 7.8, 'fell over', size=8, color='white')
    _gripper(ax, 6.9, 8.5)
    _label(ax, 5, 3.3, 'no right answer, only a score:', size=10.5)
    _label(ax, 5, 2.6, 'reward = 0', size=12, family=MONO, color=BAD, weight='bold')
    _label(ax, 5, 0.9, 'from a score after the try', size=11, weight='bold', color=WRIST)
    _save(fig, 'what-models-are/learning-signals', 'four-kinds.svg')


def copied_habit(k: Worked) -> None:
    """Imitation copies the person's habit: every demonstration stops short, so the copy does too."""
    fig, ax = plt.subplots(figsize=(10.5, 5.6), facecolor='white')
    _plain(ax)
    ax.axhspan(-TOL, TOL, color=GOOD, alpha=0.12, lw=0)
    ax.axhline(0, color=GOOD, lw=1.0)
    ax.text(35.6, 0.55, f'success: within {TOL:.0f} cm', color=GOOD, fontsize=10, va='center')
    ax.scatter(k.demo_p, k.demo_miss, s=46, color=SLIDE, edgecolor=INK, lw=0.6, zorder=4,
               label=f'the {N_DEMOS} demonstrations')
    xs = np.linspace(LO, HI, 50)
    ax.plot(xs, _lands(*k.imit, xs, np.zeros_like(xs)) - xs, color=GRIP, lw=2.4, zorder=3,
            label=f'the copied policy: success {success(*k.imit):.0%}')
    ax.plot(xs, _lands(*k.self_policy, xs, np.zeros_like(xs)) - xs, color=PURPLE, lw=2.0,
            ls='--', zorder=3,
            label=f'learned from the arm\'s own {N_POKES} pokes: success {success(*k.self_policy):.0%}')
    ax.set_xlim(3, 42)
    ax.set_ylim(-2.4, 2.2)
    ax.set_xlabel('where the mug is (cm along the table)')
    ax.set_ylabel('where the gripper stopped,\nminus where the mug is (cm)')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.set_title('Copying a careful person copies their habit of stopping short', fontsize=13,
                 weight='bold', color=INK)
    _save(fig, 'what-models-are/learning-signals', 'copied-habit.svg')


def trial_and_error(k: Worked) -> None:
    """Success rate against trials, starting from a blank guess and starting from the copied policy."""
    fig, ax = plt.subplots(figsize=(10.5, 5.4), facecolor='white')
    _plain(ax)
    t = np.arange(N_TRIALS + 1)
    ax.plot(t, 100 * k.curve_scratch, color=WRIST, lw=2.2, label='trial and error from a blank guess')
    ax.plot(t, 100 * k.curve_imit, color=SLIDE, lw=2.2,
            label='trial and error starting from the copied policy')
    ax.axhline(100 * success(*k.imit), color=GRIP, lw=1.2, ls=':')
    ax.text(N_TRIALS, 100 * success(*k.imit) + 2.5, 'copied policy alone', color=GRIP,
            fontsize=10, ha='right')
    for cv, col in ((k.curve_scratch, WRIST), (k.curve_imit, SLIDE)):
        f = _first_at(cv, 0.9)
        ax.plot([f], [100 * cv[f]], 'o', color=col, ms=7, mec=INK, zorder=5)
        ax.annotate(f'90% after {f} trials', (f, 100 * cv[f]), xytext=(f + 18, 100 * cv[f] - 16),
                    fontsize=10, color=col, arrowprops={'arrowstyle': '-', 'color': col})
    ax.set_xlim(0, N_TRIALS)
    ax.set_ylim(-3, 108)
    ax.set_xlabel(f'trials (each trial is {2 * PER_TRIAL} reaches: old and new policy, '
                  f'{PER_TRIAL} mugs each)')
    ax.set_ylabel('reaches that land within 1 cm (%)')
    ax.legend(loc='lower right', frameon=False, fontsize=10, bbox_to_anchor=(1.0, 0.04))
    ax.set_title('Trial and error fixes the habit, and is much faster from a good start',
                 fontsize=13, weight='bold', color=INK)
    _save(fig, 'what-models-are/learning-signals', 'trial-and-error.svg')


def three_stages() -> None:
    """How one vision-language-action model is trained: three stages, three kinds of signal."""
    fig, ax = plt.subplots(figsize=(15, 6.2), facecolor='white')
    _axes(ax, (0, 30), (0, 12))
    stages = [
        (PURPLE, '1. Pretrain', 'mostly self-supervised',
         'internet pictures, captions\nand text; no robot at all',
         'hundreds of millions\nof examples or more',
         'what things look like\nand what words mean'),
        (SLIDE, '2. Train on robot data', 'imitation',
         'robot episodes: camera\npictures and the commands\na person gave',
         'about a million episodes\nfrom many robots, then\ntens to hundreds for your task',
         'which movement goes\nwith which picture'),
        (WRIST, '3. Refine (sometimes)', 'reinforcement',
         'the robot\'s own tries,\neach with a score',
         'hundreds to thousands\nof tries on one task',
         'to do better than\nthe demonstrations'),
    ]
    x0, w, gap = 0.5, 8.6, 1.4
    for i, (col, head, kind, data, amount, learns) in enumerate(stages):
        x = x0 + i * (w + gap)
        _box(ax, x, 0.6, w, 9.4, face='white', edge=col, lw=2)
        _title(ax, x + w / 2, 11.0, head, color=col)
        _label(ax, x + w / 2, 9.2, kind, size=12, color=col, weight='bold')
        _label(ax, x + 0.4, 8.2, 'data', size=9.5, color=MUTED, ha='left')
        _label(ax, x + w / 2, 7.1, data, size=10.5)
        _label(ax, x + 0.4, 5.95, 'how much', size=9.5, color=MUTED, ha='left')
        _label(ax, x + w / 2, 4.8, amount, size=10.5)
        _label(ax, x + 0.4, 3.4, 'what it learns', size=9.5, color=MUTED, ha='left')
        _label(ax, x + w / 2, 2.5, learns, size=10.5)
        if i < 2:
            _arrow(ax, (x + w + 0.15, 5.3), (x + w + gap - 0.15, 5.3), color=INK)
    _label(ax, 15, -0.3, 'The same network goes through all three stages. '
           'Each stage starts from the numbers the stage before it left.', size=10.5,
           color=MUTED)
    _save(fig, 'what-models-are/learning-signals', 'three-stages.svg')


# --------------------------------------------------------------------------
# 09_making-models-work-on-an-arm/01_overview.md
# --------------------------------------------------------------------------

def notebook_to_arm() -> None:
    """The four questions between a model that works in a notebook and one that works on the arm."""
    fig, ax = plt.subplots(figsize=(15, 6.8), facecolor='white')
    _axes(ax, (0, 30), (1.8, 12.6))
    # the two ends
    _box(ax, 0.3, 4.4, 4.4, 4.2, face=PALE, edge=MUTED)
    _label(ax, 2.5, 7.6, 'works in a\nnotebook', size=12, weight='bold')
    _label(ax, 2.5, 5.5, 'right on the\ntest pictures', size=10, color=MUTED)
    _box(ax, 25.3, 4.4, 4.4, 4.2, face='#e3f3e6', edge=GOOD)
    _label(ax, 27.5, 7.6, 'works on\nthe arm', size=12, weight='bold')
    _label(ax, 27.5, 5.5, 'right on your\nobjects, in time,\nand safe', size=10, color=MUTED)

    steps = [
        (LINK, 'most used', 'Fine-tuning', 'Does it know\nyour objects?'),
        (LINK, 'most used', 'Running a model\non a robot', 'Is it fast enough,\ninside the loop?'),
        (LINK, 'most used', 'Evaluation\nand failure', 'Does it really\nwork, and how\ndoes it fail?'),
        (PURPLE, 'also used', 'Uncertainty and\nconfidence', 'Does it know\nwhen it is unsure?'),
    ]
    xs = [5.4, 10.4, 15.4, 20.4]
    for x, (col, _group, name, q) in zip(xs, steps):
        _box(ax, x, 6.8, 4.2, 2.8, face=LINK_PALE if col == LINK else '#e6e0f4', edge=col)
        _label(ax, x + 2.1, 8.2, name, size=10.5, weight='bold')
        _label(ax, x + 2.1, 4.9, q, size=10, color=INK)
    for a, b in zip([4.8] + [x + 4.3 for x in xs], xs + [25.2]):
        _arrow(ax, (a, 8.2), (b - 0.05, 8.2), color=INK, lw=1.4)
    ax.plot([5.4, 19.6], [11.1, 11.1], color=LINK, lw=2)
    ax.plot([20.4, 24.6], [11.1, 11.1], color=PURPLE, lw=2)
    _label(ax, 12.5, 11.8, 'most used', size=10.5, color=LINK, weight='bold')
    _label(ax, 22.5, 11.8, 'also used', size=10.5, color=PURPLE, weight='bold')
    _label(ax, 15, 2.6, 'Each page answers one question. A model has to pass all four '
           'before the arm can rely on it.', size=10.5, color=MUTED)
    _save(fig, 'making-models-work-on-an-arm/overview', 'notebook-to-arm.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    k = _worked()
    _report(k)
    four_kinds()
    copied_habit(k)
    trial_and_error(k)
    three_stages()
    notebook_to_arm()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
