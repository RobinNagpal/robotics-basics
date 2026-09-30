"""Generate the diagrams for one page of docs/06_learned-models/02_classical-machine-learning/.

    03_also-used/03_pca-and-shrinking-data.md -> images/classical-machine-learning/pca-and-shrinking-data/

Run with:  pixi run python ../docs/diagrams/classical_ml_5.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the page can quote the same values. The data is simulated: two finger
joints that bend together, the 15 joint angles of a robot hand closing on
objects, and recorded reaching moves of a 7-joint arm. The method run on that
data is real principal component analysis (PCA), written in NumPy with
np.linalg.eigh.
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

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'classical-machine-learning')
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

DOC: str = 'pca-and-shrinking-data'

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


def pca(x: Arr) -> tuple[Arr, Arr, Arr]:
    """Principal component analysis in four lines.

    Returns the mean of each column, the variances along each direction
    (largest first) and the directions themselves, one per column.
    """
    mean = x.mean(axis=0)
    cov = np.cov((x - mean).T)
    values, vectors = np.linalg.eigh(cov)        # smallest first
    order = np.argsort(values)[::-1]
    return mean, values[order], vectors[:, order]


# --------------------------------------------------------------------------
# 1. the worked example: two finger joints that bend together
# --------------------------------------------------------------------------

def finger_data() -> Arr:
    rng = np.random.default_rng(3)
    middle = rng.uniform(10.0, 80.0, size=8)
    end = 0.7 * middle + 5.0 + rng.normal(0.0, 3.0, size=8)
    return np.round(np.column_stack([middle, end]), 0)


def worked_example() -> None:
    x = finger_data()
    mean, values, vectors = pca(x)
    v1 = vectors[:, 0]
    if v1[0] < 0:
        v1 = -v1
    v2 = vectors[:, 1]
    if v2[1] < 0:
        v2 = -v2
    xc = x - mean
    cov = np.cov(xc.T)
    score = xc @ v1
    rebuilt = mean + np.outer(score, v1)
    err = np.linalg.norm(x - rebuilt, axis=1)
    kept = values[0] / values.sum()
    print('--- worked example: two finger joints ---')
    print('readings (middle, end) degrees:')
    for row in x:
        print(f'   {row[0]:5.0f} {row[1]:5.0f}')
    print(f'mean = ({mean[0]:.1f}, {mean[1]:.1f})')
    print(f'covariance = [[{cov[0,0]:.1f}, {cov[0,1]:.1f}], [{cov[1,0]:.1f}, {cov[1,1]:.1f}]]')
    print(f'eigenvalues (variance) = {values[0]:.1f}, {values[1]:.1f}')
    print(f'spread (sd) along each = {np.sqrt(values[0]):.1f}, {np.sqrt(values[1]):.1f} deg')
    print(f'direction 1 = ({v1[0]:.3f}, {v1[1]:.3f}), '
          f'angle {np.degrees(np.arctan2(v1[1], v1[0])):.1f} deg')
    print(f'direction 2 = ({v2[0]:.3f}, {v2[1]:.3f})')
    print(f'share kept by direction 1 = {100 * kept:.1f} %')
    print('scores:', ' '.join(f'{s:.1f}' for s in score))
    i = int(np.argmax(x[:, 0]))
    print(f'reading {i}: {x[i]} -> score {score[i]:.1f} -> rebuilt '
          f'({rebuilt[i,0]:.1f}, {rebuilt[i,1]:.1f}), error {err[i]:.1f} deg')
    print(f'rebuild error: mean {err.mean():.1f}, largest {err.max():.1f} deg')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.4))
    # left: the points, the mean and the two directions
    ax = axes[0]
    _plain(ax)
    ax.scatter(x[:, 0], x[:, 1], s=46, color=LINK, zorder=3, label='reading')
    ax.scatter([mean[0]], [mean[1]], s=90, marker='X', color=INK, zorder=4, label='mean')
    for v, val, col, name in ((v1, values[0], GRIP, 'direction 1'),
                              (v2, values[1], SLIDE, 'direction 2')):
        L = 2.0 * np.sqrt(val)
        ax.annotate('', xy=mean + L * v, xytext=mean,
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=2.4), zorder=5)
    ax.text(*(mean + 2.0 * np.sqrt(values[0]) * v1 + np.array([1.5, -4.0])),
            f'direction 1\nspread {np.sqrt(values[0]):.1f}°', color=GRIP, fontsize=10.5,
            ha='left', va='top')
    ax.text(*(mean + 2.0 * np.sqrt(values[1]) * v2 + np.array([-2.0, 2.0])),
            f'direction 2\nspread {np.sqrt(values[1]):.1f}°', color=SLIDE, fontsize=10.5,
            ha='right', va='bottom')
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 75)
    ax.set_aspect('equal')
    ax.set_xlabel('middle joint (degrees)', fontsize=10.5)
    ax.set_ylabel('end joint (degrees)', fontsize=10.5)
    ax.set_title('1. Find the directions of most and least spread', fontsize=11.5,
                 weight='bold', loc='left')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')

    # right: drop each point onto direction 1
    ax = axes[1]
    _plain(ax)
    t = np.linspace(score.min() - 8, score.max() + 8, 2)
    line = mean + np.outer(t, v1)
    ax.plot(line[:, 0], line[:, 1], color=GRIP, lw=1.6, zorder=2)
    for a, b in zip(x, rebuilt):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=MUTED, lw=1.0, ls=':', zorder=2)
    ax.scatter(x[:, 0], x[:, 1], s=46, color=LINK, zorder=3, label='reading')
    ax.scatter(rebuilt[:, 0], rebuilt[:, 1], s=40, facecolor='white', edgecolor=GRIP,
               lw=1.8, zorder=4, label='rebuilt from one number')
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 75)
    ax.set_aspect('equal')
    ax.set_xlabel('middle joint (degrees)', fontsize=10.5)
    ax.set_title(f'2. Keep one number per reading: {100 * kept:.1f} % of the spread kept',
                 fontsize=11.5, weight='bold', loc='left')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.tight_layout(w_pad=3.0)
    _save(fig, DOC, 'spread-directions.svg')


# --------------------------------------------------------------------------
# 2. hand synergies: 15 joint angles of a robot hand
# --------------------------------------------------------------------------

FINGERS: list[str] = ['thumb', 'index', 'middle', 'ring', 'little']
TYPES: list[str] = ['power grasp', 'pinch', 'flat hand']


def hand_data() -> tuple[Arr, NDArray[np.int64]]:
    """210 hand postures, 15 joint angles each, in three grasp types.

    Each finger has 3 joints (base, middle, end). A posture is a resting
    posture plus two hidden 'synergies' (close the whole hand; thumb and
    index against the other three), a weak third one (bend the end joints)
    and 3 degrees of independent noise on each joint.
    """
    rng = np.random.default_rng(11)
    rest = np.tile([15.0, 20.0, 10.0], 5)
    close = np.tile([1.0, 1.1, 0.8], 5)
    pinch = np.concatenate([np.array([1.0, 1.0, 0.8]), np.array([0.9, 1.0, 0.6]),
                            np.full(3, -0.4), np.full(3, -0.7), np.full(3, -0.8)])
    tips = np.tile([0.0, 0.2, 1.0], 5)
    rows, labels = [], []
    centres = {0: (45.0, 0.0), 1: (18.0, 22.0), 2: (0.0, -4.0)}
    for k in range(3):
        for _ in range(70):
            c1 = centres[k][0] + rng.normal(0, 7.0)
            c2 = centres[k][1] + rng.normal(0, 5.0)
            c3 = rng.normal(0, 4.0)
            rows.append(rest + c1 * close + c2 * pinch + c3 * tips + rng.normal(0, 3.0, 15))
            labels.append(k)
    return np.array(rows), np.array(labels)


def hand_synergies() -> None:
    x, labels = hand_data()
    mean, values, vectors = pca(x)
    share = values / values.sum()
    cum = np.cumsum(share)
    print('--- hand synergies: 210 postures x 15 joints ---')
    print('share of spread per component (%):',
          ' '.join(f'{100 * s:.1f}' for s in share))
    print('cumulative (%):', ' '.join(f'{100 * c:.1f}' for c in cum))
    k95 = int(np.searchsorted(cum, 0.95) + 1)
    print(f'components needed for 95 %: {k95}')
    for j in range(2):
        v = vectors[:, j] * np.sign(vectors[:, j].sum() or 1.0)
        if j == 1 and v[0] < 0:
            v = -v
        print(f'synergy {j + 1} weights by finger (base, middle, end):')
        for f, name in enumerate(FINGERS):
            print(f'   {name:6s} ' + ' '.join(f'{w:+.2f}' for w in v[3 * f:3 * f + 3]))
    xc = x - mean
    for k in (1, 2, 3):
        rebuilt = mean + xc @ vectors[:, :k] @ vectors[:, :k].T
        rms = np.sqrt(np.mean((x - rebuilt) ** 2))
        print(f'rebuild with {k} numbers: RMS error {rms:.1f} deg per joint')

    # picture 1: the share of spread per component
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    _plain(ax)
    idx = np.arange(1, 16)
    ax.bar(idx, 100 * share, color=[GRIP, GRIP] + [LINK_PALE] * 13, edgecolor=LINK,
           lw=0.8, label='share of this direction')
    ax.plot(idx, 100 * cum, color=INK, marker='o', ms=4, lw=1.4,
            label='total kept with this many directions')
    ax.axhline(95, color=MUTED, lw=1.0, ls='--')
    ax.text(15.3, 93.5, '95 %', color=MUTED, fontsize=9.5, ha='right', va='top')
    for i in range(3):
        ax.text(idx[i] + 0.25, 100 * share[i] + 1.5, f'{100 * share[i]:.1f} %',
                fontsize=9.5, color=INK, ha='left')
    ax.text(2.35, 100 * cum[1] - 6, f'first two together: {100 * cum[1]:.1f} %',
            fontsize=10, color=INK, ha='left', va='top')
    ax.set_xticks(idx)
    ax.set_xlabel('direction (principal component), largest spread first', fontsize=10.5)
    ax.set_ylabel('share of the spread (%)', fontsize=10.5)
    ax.set_ylim(0, 108)
    ax.set_title('15 joint angles, but two directions hold almost all of the spread',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    _save(fig, DOC, 'spread-per-direction.svg')

    # picture 2: every grasp as two numbers
    scores = xc @ vectors[:, :2]
    if vectors[:, 0].sum() < 0:
        scores[:, 0] *= -1
    v2 = vectors[:, 1]
    if v2[0] < 0:
        scores[:, 1] *= -1
    fig, ax = plt.subplots(figsize=(8.4, 6.0))
    _plain(ax)
    for k, (name, col) in enumerate(zip(TYPES, (LINK, GRIP, SLIDE))):
        m = labels == k
        ax.scatter(scores[m, 0], scores[m, 1], s=22, color=col, alpha=0.8, label=name)
    ax.axhline(0, color=GRID, lw=0.8, zorder=0)
    ax.axvline(0, color=GRID, lw=0.8, zorder=0)
    ax.set_xlabel('score on synergy 1: how far the whole hand is closed', fontsize=10.5)
    ax.set_ylabel('score on synergy 2: thumb and index\nagainst the other three', fontsize=10.5)
    ax.set_title('210 grasps, 15 numbers each, drawn with two numbers each',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=10, frameon=False, loc='upper left')
    _save(fig, DOC, 'grasps-as-two-numbers.svg')


# --------------------------------------------------------------------------
# 3. compressing recorded reaching moves of a 7-joint arm
# --------------------------------------------------------------------------

def reach_data() -> tuple[Arr, Arr]:
    """300 recorded reaches, 7 joints x 50 time steps = 350 numbers each.

    Each reach goes from a fixed home posture to a goal posture along a
    smooth S-shaped timing curve, with an extra lift in the middle. The goal
    postures come from 3 hidden numbers (where the object is) and the lift
    from 1, plus 0.3 degrees of sensor noise on every number.
    """
    rng = np.random.default_rng(5)
    t = np.linspace(0.0, 1.0, 50)
    s = 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5          # smooth start and stop
    bump = np.sin(np.pi * t) ** 2
    home = np.array([0.0, -30.0, 0.0, -120.0, 0.0, 90.0, 45.0])
    mix = rng.normal(0.0, 1.0, size=(3, 7)) * np.array([25, 15, 10, 20, 8, 12, 15])
    lift_dir = np.array([0.0, -8.0, 0.0, 12.0, 0.0, -4.0, 0.0])
    reaches = []
    for _ in range(300):
        z = rng.normal(0.0, 1.0, size=3)
        goal = home + np.array([10, 20, 0, 30, 0, -10, 0]) + z @ mix
        lift = rng.uniform(0.5, 1.5)
        q = home + np.outer(s, goal - home) + lift * np.outer(bump, lift_dir)
        q += rng.normal(0.0, 0.3, size=q.shape)
        reaches.append(q.T.ravel())                     # joint 1 steps, joint 2 steps, ...
    return np.array(reaches), t


def reach_compression() -> None:
    x, t = reach_data()
    train, test = x[:250], x[250:]
    mean, values, vectors = pca(train)
    share = values / values.sum()
    cum = np.cumsum(share)
    print('--- reaching moves: 300 reaches x 350 numbers ---')
    print('first 6 shares (%):', ' '.join(f'{100 * s:.2f}' for s in share[:6]))
    print('cumulative (%):', ' '.join(f'{100 * c:.3f}' for c in cum[:6]))
    errs = {}
    for k in (1, 2, 4, 8):
        w = vectors[:, :k]
        rebuilt = mean + (test - mean) @ w @ w.T
        err = np.abs(test - rebuilt)
        errs[k] = rebuilt
        print(f'keep {k}: {350 // k if k else 0}x smaller, test RMS {np.sqrt(np.mean(err ** 2)):.2f} deg, '
              f'largest {err.max():.2f} deg')
    # picture: one test reach, joint 2 and joint 4, rebuilt from 1 and 4 numbers
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), sharex=True)
    for ax, j, name in ((axes[0], 1, 'joint 2'), (axes[1], 3, 'joint 4')):
        _plain(ax)
        sl = slice(50 * j, 50 * j + 50)
        ax.plot(t, test[0, sl], color=INK, lw=0, marker='o', ms=3.2,
                label='recorded (50 readings)')
        ax.plot(t, errs[1][0, sl], color=JOINT, lw=2.0, ls='--', label='rebuilt from 1 number')
        ax.plot(t, errs[4][0, sl], color=GRIP, lw=2.0, label='rebuilt from 4 numbers')
        ax.set_xlabel('time through the reach (0 = start, 1 = end)', fontsize=10.5)
        ax.set_ylabel(f'{name} angle (degrees)', fontsize=10.5)
        ax.set_title(name, fontsize=11.5, weight='bold', loc='left')
    axes[0].legend(fontsize=9.5, frameon=False, loc='best')
    fig.suptitle('A reach of 350 numbers, stored as 4 numbers and rebuilt',
                 fontsize=12.5, weight='bold')
    fig.tight_layout(w_pad=3.0)
    _save(fig, DOC, 'reach-rebuilt.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    worked_example()
    hand_synergies()
    reach_compression()
    print(f'wrote the diagrams under {IMAGES / DOC}')


if __name__ == '__main__':
    main()
