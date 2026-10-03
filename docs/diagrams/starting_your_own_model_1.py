"""Generate the diagrams for the first page of docs/05_neural-networks/13_starting-your-own-model/.

    01_before-you-train-anything.md -> images/starting-your-own-model/before-you-train-anything/

Run with:  python3 starting_your_own_model_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so the document can quote the same values.

What is simulated, and what is real:

* One work cell is simulated with a seeded generator. An arm picks small parts
  off trays. There are 40 trays, 6 parts on each tray, and the camera measures
  each part 12 times as the arm approaches, so the recording holds 240 parts
  and 2,880 frames. Each tray has its own lighting and calibration offset,
  which is what makes a tray a scene; each part has its own measurement offset;
  each frame adds a small jitter.
* Each part has true properties (width, height, mass, shininess, flatness of
  its top face) and the right grip for it (pinch, wrap or suction) follows from
  those properties through a fixed scoring rule with one genuine interaction in
  it, since a suction cup needs a face that is flat and shiny and wide enough
  at the same time. The model only ever sees the measured numbers.
* A second job on the same parts is how hard to squeeze, in newtons, worked out
  from the part's mass and the friction of its surface. A third, easier job is
  whether the gripper is holding anything, from the finger gap in millimetres
  and the motor current in amperes.
* Everything done to that simulated data is real arithmetic: the hand-written
  rules, the greedy decision lists, the majority-class baseline, nearest
  neighbour with and without scaling, the small networks trained by gradient
  descent in NumPy, the three kinds of split, the binomial intervals and the
  best-of-k inflation measurement.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'starting-your-own-model')
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

DOC: str = 'before-you-train-anything'

Arr = NDArray[np.float64]
Ints = NDArray[np.int64]

GRIPS: list[str] = ['pinch', 'wrap', 'suction']
GRIP_COLOURS: list[str] = [LINK, SLIDE, PURPLE]
FEATURES: list[str] = ['width (mm)', 'height (mm)', 'mass (g)', 'shine (0-1)', 'flat top (0-1)']


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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _wilson(k: int, n: int) -> tuple[float, float]:
    """95 per cent interval for a success rate, the Wilson form."""
    if n == 0:
        return 0.0, 1.0
    z = 1.959964
    p = k / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


# --------------------------------------------------------------------------
# the simulated work cell
# --------------------------------------------------------------------------

N_TRAYS: int = 40
PARTS_PER_TRAY: int = 6
FRAMES: int = 12


class Cell:
    """Every simulated number for the cell, worked out once."""

    def __init__(self) -> None:
        rng = np.random.default_rng(13)
        n_parts = N_TRAYS * PARTS_PER_TRAY
        self.n_parts = n_parts
        self.tray_of_part: Ints = np.repeat(np.arange(N_TRAYS), PARTS_PER_TRAY)

        # --- true properties of each part -------------------------------
        width = rng.uniform(8.0, 95.0, n_parts)                 # mm
        height = rng.uniform(5.0, 60.0, n_parts)                # mm
        metal = rng.random(n_parts) < 0.45
        shine = np.where(metal, rng.uniform(0.45, 0.95, n_parts),
                         rng.uniform(0.04, 0.40, n_parts))
        flat = rng.uniform(0.0, 1.0, n_parts)
        density = np.where(metal, 2.7e-3, 1.1e-3)               # g per cubic mm
        volume = width * height * (0.5 * height) * 0.5          # cubic mm
        mass = np.clip(volume * density * rng.uniform(0.7, 1.3, n_parts), 6.0, 260.0)
        self.true_props = np.stack([width, height, mass, shine, flat], axis=1)

        # --- the right grip for each part -------------------------------
        wn = (width - 8.0) / 87.0
        mn = np.clip(mass / 260.0, 0.0, 1.0)
        s_pinch = 1.30 - 1.55 * wn - 0.95 * mn + 0.35 * (1.0 - shine)
        s_wrap = 0.12 + 1.45 * wn + 1.15 * mn - 0.80 * flat
        s_suction = -0.62 + 3.20 * flat * shine + 0.55 * wn
        scores = np.stack([s_pinch, s_wrap, s_suction], axis=1)
        scores = scores + rng.normal(0.0, 0.12, scores.shape)
        self.grip: Ints = np.argmax(scores, axis=1)
        self.margin = np.sort(scores, axis=1)[:, -1] - np.sort(scores, axis=1)[:, -2]

        # --- how hard to squeeze, in newtons ----------------------------
        mu = 0.85 - 0.55 * shine                                # shiny is slippery
        self.force = mass / 1000.0 * 9.81 * 1.6 / (2.0 * mu)
        self.mu = mu

        # --- cracks: the unbalanced job ---------------------------------
        self.cracked = rng.random(n_parts) < 0.08

        # --- what the camera measures, frame by frame -------------------
        tray_calib = rng.normal(0.0, 5.5, N_TRAYS)              # mm, camera offset
        tray_light = rng.normal(0.0, 0.17, N_TRAYS)             # shine offset
        part_off = rng.normal(0.0, 1.0, (n_parts, 5))
        rows, part_of_frame = [], []
        for p in range(n_parts):
            t = self.tray_of_part[p]
            base = np.array([
                width[p] + tray_calib[t] + 1.4 * part_off[p, 0],
                height[p] + 0.9 * part_off[p, 1],
                mass[p] * (1.0 + 0.10 * part_off[p, 2]),
                shine[p] + tray_light[t] + 0.045 * part_off[p, 3],
                flat[p] + 0.065 * part_off[p, 4],
            ])
            jitter = rng.normal(0.0, 1.0, (FRAMES, 5)) * np.array([0.35, 0.25, 1.1, 0.012, 0.016])
            frames = base[None, :] + jitter
            frames[:, 3] = np.clip(frames[:, 3], 0.0, 1.0)
            frames[:, 4] = np.clip(frames[:, 4], 0.0, 1.0)
            rows.append(frames)
            part_of_frame.extend([p] * FRAMES)
        self.X: Arr = np.concatenate(rows, axis=0)
        self.part_of_frame: Ints = np.array(part_of_frame)
        self.tray_of_frame: Ints = self.tray_of_part[self.part_of_frame]
        self.y: Ints = self.grip[self.part_of_frame]
        self.f: Arr = self.force[self.part_of_frame]

        # --- the three splits, all 60 / 20 / 20 -------------------------
        srng = np.random.default_rng(5)
        trays = srng.permutation(N_TRAYS)
        self.split_tray = self._by_group(self.tray_of_frame, trays, 24, 8)
        parts = srng.permutation(n_parts)
        self.split_part = self._by_group(self.part_of_frame, parts, 144, 48)
        frames_perm = srng.permutation(len(self.y))
        n_tr = int(0.6 * len(self.y))
        n_va = int(0.2 * len(self.y))
        mask = np.zeros(len(self.y), dtype=int)
        mask[frames_perm[n_tr:n_tr + n_va]] = 1
        mask[frames_perm[n_tr + n_va:]] = 2
        self.split_frame = mask
        self.held_out_trays = np.sort(trays[24 + 8:])
        self.val_trays = np.sort(trays[24:24 + 8])

        # standardise using the training part of the tray split only
        tr = self.split_tray == 0
        self.mean = self.X[tr].mean(axis=0)
        self.sd = self.X[tr].std(axis=0)
        self.Z: Arr = (self.X - self.mean) / self.sd

    @staticmethod
    def _by_group(group_of_row: Ints, order: Ints, n_train: int, n_val: int) -> Ints:
        """Give every row a 0/1/2 split label from which group it belongs to."""
        where = np.zeros(order.max() + 1, dtype=int)
        where[order[:n_train]] = 0
        where[order[n_train:n_train + n_val]] = 1
        where[order[n_train + n_val:]] = 2
        return where[group_of_row]


CELL = Cell()


# --------------------------------------------------------------------------
# the four things we compare: majority, written rule, nearest neighbour, model
# --------------------------------------------------------------------------

def hand_rule(X: Arr) -> Ints:
    """The grip rule a person writes in an afternoon, on the measured numbers."""
    width, shine, flat = X[:, 0], X[:, 3], X[:, 4]
    out = np.zeros(len(X), dtype=int)                      # 0 = pinch
    out[width > 45.0] = 1                                  # 1 = wrap
    out[(flat > 0.5) & (shine > 0.4) & (width > 25.0)] = 2  # 2 = suction
    return out


def nearest_neighbour(Xtr: Arr, ytr: Ints, Xte: Arr) -> Ints:
    """One nearest neighbour, brute force."""
    out = np.zeros(len(Xte), dtype=int)
    step = 400
    for a in range(0, len(Xte), step):
        chunk = Xte[a:a + step]
        d = ((chunk[:, None, :] - Xtr[None, :, :]) ** 2).sum(axis=2)
        out[a:a + step] = ytr[np.argmin(d, axis=1)]
    return out


def nn_regress(Xtr: Arr, ftr: Arr, Xte: Arr) -> Arr:
    out = np.zeros(len(Xte))
    step = 400
    for a in range(0, len(Xte), step):
        chunk = Xte[a:a + step]
        d = ((chunk[:, None, :] - Xtr[None, :, :]) ** 2).sum(axis=2)
        out[a:a + step] = ftr[np.argmin(d, axis=1)]
    return out


def train_classifier(Xtr: Arr, ytr: Ints, hidden: int = 24, steps: int = 6000,
                     lr: float = 0.6, seed: int = 0) -> tuple[Arr, Arr, Arr, Arr]:
    """A 5 -> hidden -> 3 network, full-batch gradient descent, NumPy only."""
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0.0, 0.6, (Xtr.shape[1], hidden))
    b1 = np.zeros(hidden)
    W2 = rng.normal(0.0, 0.6, (hidden, 3))
    b2 = np.zeros(3)
    Y = np.eye(3)[ytr]
    for _ in range(steps):
        h = np.tanh(Xtr @ W1 + b1)
        p = _softmax(h @ W2 + b2)
        g = (p - Y) / len(Xtr)
        gW2, gb2 = h.T @ g, g.sum(axis=0)
        gh = (g @ W2.T) * (1.0 - h ** 2)
        gW1, gb1 = Xtr.T @ gh, gh.sum(axis=0)
        W1 -= lr * gW1
        b1 -= lr * gb1
        W2 -= lr * gW2
        b2 -= lr * gb2
    return W1, b1, W2, b2


def predict_classifier(net: tuple[Arr, Arr, Arr, Arr], X: Arr) -> Ints:
    W1, b1, W2, b2 = net
    return np.argmax(np.tanh(X @ W1 + b1) @ W2 + b2, axis=1)


def mean_score(Ztr: Arr, ytr: Ints, Zte: Arr, yte: Ints, seeds: int = 4) -> float:
    """Train the same network from several starts and average the held-out score.

    One run of gradient descent from one random start wanders by a point or two,
    so every score this page quotes is the average of several runs.
    """
    out = []
    for seed in range(seeds):
        net = train_classifier(Ztr, ytr, seed=seed)
        out.append(float((predict_classifier(net, Zte) == yte).mean()) * 100)
    return float(np.mean(out))


def train_regressor(Xtr: Arr, ftr: Arr, hidden: int = 16, steps: int = 3000,
                    lr: float = 0.25, seed: int = 0) -> tuple[Arr, Arr, Arr, float]:
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0.0, 0.6, (Xtr.shape[1], hidden))
    b1 = np.zeros(hidden)
    W2 = rng.normal(0.0, 0.6, hidden)
    b2 = 0.0
    for _ in range(steps):
        h = np.tanh(Xtr @ W1 + b1)
        pred = h @ W2 + b2
        e = (pred - ftr) / len(Xtr)
        gW2, gb2 = h.T @ e, e.sum()
        gh = np.outer(e, W2) * (1.0 - h ** 2)
        gW1, gb1 = Xtr.T @ gh, gh.sum(axis=0)
        W1 -= lr * gW1
        b1 -= lr * gb1
        W2 -= lr * gW2
        b2 -= lr * gb2
    return W1, b1, W2, b2


def predict_regressor(net: tuple[Arr, Arr, Arr, float], X: Arr) -> Arr:
    W1, b1, W2, b2 = net
    return np.tanh(X @ W1 + b1) @ W2 + b2


# --------------------------------------------------------------------------
# the easy job: is the gripper holding anything
# --------------------------------------------------------------------------

class Holding:
    """Finger gap in mm and motor current in amperes, with and without a part."""

    def __init__(self) -> None:
        rng = np.random.default_rng(21)
        n = 1200
        gap_hold = rng.uniform(2.0, 31.0, n)
        cur_hold = 0.52 + 0.020 * gap_hold + rng.normal(0.0, 0.070, n)
        empty_closed = rng.random(n) < 0.6
        gap_free = np.where(empty_closed, rng.normal(3.0, 2.0, n), rng.normal(37.0, 1.2, n))
        gap_free = np.clip(gap_free, 0.0, 40.0)
        cur_free = np.where(empty_closed, rng.normal(0.31, 0.055, n), rng.normal(0.11, 0.035, n))
        self.gap = np.concatenate([gap_hold, gap_free])
        self.cur = np.concatenate([cur_hold, cur_free])
        self.held = np.concatenate([np.ones(n, dtype=int), np.zeros(n, dtype=int)])
        self.X = np.stack([self.gap, self.cur], axis=1)
        order = rng.permutation(len(self.held))
        self.train = order[:1400]
        self.test = order[1400:]

    def rule(self, drift: float = 0.0, cut: float = 0.45) -> Ints:
        return ((self.cur - drift > cut) & (self.gap > 1.5) & (self.gap < 34.0)).astype(int)


HOLD = Holding()


# --------------------------------------------------------------------------
# a greedy decision list: how many hand conditions does a job need
# --------------------------------------------------------------------------

def decision_list(Xtr: Arr, ytr: Ints, n_classes: int, depth: int = 20) -> list:
    """Greedily add single-threshold conditions, each covering what it gets right."""
    left = np.ones(len(ytr), dtype=bool)
    rules = []
    for _ in range(depth):
        best = None
        for j in range(Xtr.shape[1]):
            cuts = np.percentile(Xtr[left, j], np.arange(4, 97, 4))
            for c in cuts:
                for sign in (1, -1):
                    cover = left & ((Xtr[:, j] > c) if sign == 1 else (Xtr[:, j] <= c))
                    if cover.sum() < 8:
                        continue
                    counts = np.bincount(ytr[cover], minlength=n_classes)
                    k = int(np.argmax(counts))
                    gain = 2 * counts[k] - cover.sum()
                    if best is None or gain > best[0]:
                        best = (gain, j, float(c), sign, k)
        if best is None or best[0] <= 0:
            break
        _, j, c, sign, k = best
        rules.append((j, c, sign, k))
        cover = left & ((Xtr[:, j] > c) if sign == 1 else (Xtr[:, j] <= c))
        left = left & ~cover
        if left.sum() < 8:
            break
    default = int(np.argmax(np.bincount(ytr[left], minlength=n_classes))) if left.sum() else \
        int(np.argmax(np.bincount(ytr, minlength=n_classes)))
    return rules + [(None, 0.0, 0, default)]


def apply_list(rules: list, X: Arr, upto: int) -> Ints:
    out = np.full(len(X), rules[-1][3], dtype=int)
    done = np.zeros(len(X), dtype=bool)
    for (j, c, sign, k) in rules[:upto]:
        if j is None:
            break
        hit = (~done) & ((X[:, j] > c) if sign == 1 else (X[:, j] <= c))
        out[hit] = k
        done |= hit
    return out


# ==========================================================================
# section 1: is a model the right answer at all
# ==========================================================================

RESULTS: dict[str, float] = {}


def s1_written_rule_works() -> None:
    te = HOLD.test
    pred = HOLD.rule()[te]
    acc = float((pred == HOLD.held[te]).mean())
    net = train_classifier(
        (HOLD.X[HOLD.train] - HOLD.X[HOLD.train].mean(0)) / HOLD.X[HOLD.train].std(0),
        HOLD.held[HOLD.train], hidden=12, steps=2000, lr=0.5)
    Zte = (HOLD.X[te] - HOLD.X[HOLD.train].mean(0)) / HOLD.X[HOLD.train].std(0)
    mod = float((predict_classifier(net, Zte) == HOLD.held[te]).mean())
    RESULTS['hold_rule'] = acc
    RESULTS['hold_model'] = mod
    print(f'[s1] holding job: written rule {acc * 100:.1f}% on {len(te)} held-out readings, '
          f'trained network {mod * 100:.1f}%')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.75, 1.0]})
    _plain(ax)
    for v, colour, lab in ((0, MUTED, 'holding nothing'), (1, LINK, 'holding a part')):
        m = HOLD.held == v
        ax.scatter(HOLD.gap[m], HOLD.cur[m], s=7, color=colour, alpha=0.55,
                   edgecolors='none', label=lab)
    ax.axhline(0.45, color=GRIP, lw=2)
    ax.axvline(1.5, color=GRIP, lw=2)
    ax.axvline(34.0, color=GRIP, lw=2)
    ax.text(17.0, 1.30, 'current > 0.45 A  and  1.5 mm < gap < 34 mm', fontsize=10,
            color=GRIP, ha='center', weight='bold')
    ax.set_xlabel('finger gap (mm)', fontsize=10)
    ax.set_ylabel('motor current (A)', fontsize=10)
    ax.set_xlim(-2, 42)
    ax.set_ylim(0, 1.45)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('Three conditions separate holding from not holding',
                 fontsize=12, weight='bold')

    _plain(bx)
    bars = bx.bar(['written\nrule', 'trained\nnetwork'], [acc * 100, mod * 100],
                  color=[GRIP, LINK], width=0.55)
    bx.bar_label(bars, fmt='%.1f%%', fontsize=11, padding=3)
    bx.set_ylim(0, 112)
    bx.axhline(50, color=MUTED, ls=':', lw=1.4)
    bx.set_xlim(-0.6, 1.9)
    bx.text(1.62, 50, 'guessing', fontsize=9.5, color=MUTED, ha='left', va='center')
    bx.set_ylabel('share of held-out readings right (%)', fontsize=10)
    bx.set_title('The model buys nothing here', fontsize=12, weight='bold')
    _save(fig, 'written-rule-works.svg')


def s1_written_rule_fails() -> None:
    tr, te = CELL.split_tray == 0, CELL.split_tray == 2
    pred = hand_rule(CELL.X[te])
    acc = float((pred == CELL.y[te]).mean())
    RESULTS['grip_rule'] = acc
    counts = np.bincount(CELL.grip, minlength=3)
    print(f'[s1] grip job: hand rule {acc * 100:.1f}% on {int(te.sum())} held-out frames; '
          f'class counts pinch {counts[0]} wrap {counts[1]} suction {counts[2]} of {CELL.n_parts}')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.2), facecolor='white')
    _plain(ax)
    first = (np.arange(len(CELL.y)) % FRAMES) == 0
    keep = first & (CELL.split_tray == 0)
    for g in range(3):
        m = keep & (CELL.y == g)
        ax.scatter(CELL.X[m, 0], CELL.X[m, 3], s=6, alpha=0.5, color=GRIP_COLOURS[g],
                   edgecolors='none', label=f'{GRIPS[g]} is right')
    ax.axvline(45.0, color=INK, lw=1.8, ls='--')
    ax.axhline(0.4, color=INK, lw=1.8, ls='--')
    ax.text(47.5, 0.03, 'width > 45 mm', fontsize=9.5, color=INK, rotation=90, va='bottom')
    ax.text(2.0, 0.43, 'shine > 0.4', fontsize=9.5, color=INK)
    ax.set_xlabel('measured width (mm)', fontsize=10)
    ax.set_ylabel('measured shine (0 to 1)', fontsize=10)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-0.03, 1.03)
    ax.legend(fontsize=9, frameon=False, loc='upper left', ncol=1)
    ax.set_title('The three grips overlap wherever you cut', fontsize=12, weight='bold')

    _plain(bx)
    per = [float((pred[CELL.y[te] == g] == g).mean()) * 100 for g in range(3)]
    bars = bx.bar(GRIPS, per, color=GRIP_COLOURS, width=0.55)
    bx.bar_label(bars, fmt='%.1f%%', fontsize=11, padding=3)
    bx.axhline(acc * 100, color=GRIP, lw=2)
    bx.set_xlim(-0.6, 3.1)
    bx.text(2.6, acc * 100, f'all frames\n{acc * 100:.1f}%', fontsize=10,
            color=GRIP, ha='left', va='center')
    bx.set_ylim(0, 108)
    bx.set_ylabel('share of that grip found (%)', fontsize=10)
    bx.set_title('Where the hand rule loses: suction', fontsize=12, weight='bold')
    _save(fig, 'written-rule-fails.svg')


def s1_conditions_needed() -> None:
    tr, te = CELL.split_tray == 0, CELL.split_tray == 2
    top = 12
    rules_grip = decision_list(CELL.X[tr], CELL.y[tr], 3, depth=top)
    grip_curve = [float((apply_list(rules_grip, CELL.X[te], k) == CELL.y[te]).mean()) * 100
                  for k in range(0, top + 1)]
    rules_hold = decision_list(HOLD.X[HOLD.train], HOLD.held[HOLD.train], 2, depth=top)
    hold_curve = [float((apply_list(rules_hold, HOLD.X[HOLD.test], k)
                         == HOLD.held[HOLD.test]).mean()) * 100 for k in range(0, top + 1)]
    # with no conditions at all the rule can only name the most common answer
    grip_curve[0] = float((CELL.y[te] == np.argmax(np.bincount(CELL.y[tr],
                                                               minlength=3))).mean()) * 100
    hold_curve[0] = float((HOLD.held[HOLD.test] ==
                           np.argmax(np.bincount(HOLD.held[HOLD.train]))).mean()) * 100
    thresholds = [f'{FEATURES[j].split(" ")[0]} {">" if s == 1 else "<="} {c:.1f}'
                  for (j, c, s, _k) in rules_grip[:5] if j is not None]
    RESULTS['grip_list_1'] = grip_curve[1]
    RESULTS['grip_list_5'] = grip_curve[5]
    RESULTS['grip_list_top'] = grip_curve[top]
    RESULTS['hold_list_1'] = hold_curve[1]
    RESULTS['hold_list_3'] = hold_curve[3]
    print(f'[s1] conditions: holding job {hold_curve[0]:.1f}% with none, '
          f'{hold_curve[1]:.1f}% with one, {hold_curve[3]:.1f}% with three')
    print(f'[s1] conditions: grip job {grip_curve[0]:.1f}% with none, '
          f'{grip_curve[1]:.1f}% with one, {grip_curve[3]:.1f}% with three, '
          f'{grip_curve[5]:.1f}% with five, {grip_curve[top]:.1f}% with {top}')
    print(f'[s1] the first five conditions the data picks: ' + '; '.join(thresholds))

    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(range(top + 1), hold_curve, marker='o', ms=4.5, color=SLIDE, lw=2,
            label='is the gripper holding anything')
    ax.plot(range(top + 1), grip_curve, marker='s', ms=4.5, color=GRIP, lw=2,
            label='which of three grips to use')
    ax.annotate(f'{hold_curve[1]:.1f}% after one condition',
                xy=(1, hold_curve[1]), xytext=(2.0, 88.0), fontsize=10, color=SLIDE,
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.4))
    ax.annotate(f'{grip_curve[5]:.1f}% after five, and no further',
                xy=(5, grip_curve[5]), xytext=(5.4, 86.0), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.4))
    ax.text(5.6, 64.0, 'the five thresholds the recording picks:\n' +
            '\n'.join('    ' + t for t in thresholds), fontsize=9.5, color=MUTED,
            va='top')
    ax.set_xticks(range(0, top + 1))
    ax.set_xlabel('number of conditions in the rule', fontsize=10)
    ax.set_ylabel('share of held-out examples right (%)', fontsize=10)
    ax.set_ylim(22, 106)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('One job is finished in one condition, the other needs five and '
                 'a recording to set them', fontsize=12.5, weight='bold')
    _save(fig, 'conditions-to-get-there.svg')


def s1_rule_that_changed() -> None:
    te = HOLD.test
    drifts = np.linspace(0.0, 0.40, 17)
    fixed, retuned, cuts = [], [], []
    for d in drifts:
        fixed.append(float((HOLD.rule(drift=d)[te] == HOLD.held[te]).mean()) * 100)
        trial = np.arange(0.05, 0.95, 0.01)
        sc = [float((HOLD.rule(drift=d, cut=c)[HOLD.train] == HOLD.held[HOLD.train]).mean())
              for c in trial]
        best = float(trial[int(np.argmax(sc))])
        cuts.append(best)
        retuned.append(float((HOLD.rule(drift=d, cut=best)[te] == HOLD.held[te]).mean()) * 100)
    RESULTS['drift_0'] = fixed[0]
    RESULTS['drift_18'] = float(np.interp(0.18, drifts, fixed))
    RESULTS['drift_18_retuned'] = float(np.interp(0.18, drifts, retuned))
    print(f'[s1] drift: fixed threshold {fixed[0]:.1f}% at no drift, '
          f'{RESULTS["drift_18"]:.1f}% at 0.18 A of drift, '
          f'{fixed[-1]:.1f}% at 0.40 A; re-tuning the one number gives back '
          f'{RESULTS["drift_18_retuned"]:.1f}% at 0.18 A')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.3, 1.0]})
    _plain(ax)
    ax.plot(drifts, fixed, marker='o', ms=4.5, color=GRIP, lw=2,
            label='threshold left at 0.45 A')
    ax.plot(drifts, retuned, marker='s', ms=4.5, color=SLIDE, lw=2,
            label='threshold measured again')
    ax.axvline(0.18, color=MUTED, ls=':', lw=1.4)
    ax.text(0.185, 60.0, 'six weeks of\nbrush wear', fontsize=9.5, color=MUTED)
    ax.set_xlabel('how much lower the current sensor reads (A)', fontsize=10)
    ax.set_ylabel('share of readings right (%)', fontsize=10)
    ax.set_ylim(45, 104)
    ax.legend(fontsize=10, frameon=False, loc='lower left')
    ax.set_title('A written rule fails by drifting, not by being wrong',
                 fontsize=12, weight='bold')

    _plain(bx)
    bx.plot(drifts, cuts, marker='o', ms=4.5, color=LINK, lw=2)
    bx.set_xlabel('how much lower the sensor reads (A)', fontsize=10)
    bx.set_ylabel('threshold the training readings pick (A)', fontsize=10)
    bx.set_title('The repair is one number, found in minutes', fontsize=12, weight='bold')
    _save(fig, 'the-rule-that-changed.svg')


# ==========================================================================
# section 2: input, output, one number
# ==========================================================================

def s2_input_output() -> None:
    choices = ['5 measured\nnumbers', '7 joint\nangles', 'one 224x224\ncolour frame',
               'four such\nframes']
    sizes = [5, 7, 224 * 224 * 3, 4 * 224 * 224 * 3]
    first_layer = [s * 16 for s in sizes]
    print(f'[s2] input sizes: ' + ', '.join(f'{c.replace(chr(10), " ")}={s}'
                                            for c, s in zip(choices, sizes)))
    print(f'[s2] first layer of 16 units needs ' +
          ', '.join(f'{v:,}' for v in first_layer) + ' weights')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(choices, sizes, color=[LINK, LINK, PURPLE, PURPLE], width=0.6)
    ax.bar_label(bars, labels=[f'{s:,}' for s in sizes], fontsize=10.5, padding=3)
    ax.set_yscale('log')
    ax.set_ylim(1, 4e6)
    ax.set_ylabel('numbers in one example (log scale)', fontsize=10)
    ax.set_title('What goes in, counted', fontsize=12, weight='bold')

    _plain(bx)
    bars = bx.bar(choices, first_layer, color=[SLIDE, SLIDE, WRIST, WRIST], width=0.6)
    bx.bar_label(bars, labels=[f'{v:,}' for v in first_layer], fontsize=10.5, padding=3)
    bx.set_yscale('log')
    bx.set_ylim(10, 6e8)
    bx.set_ylabel('weights in a first layer of 16 units (log scale)', fontsize=10)
    bx.set_title('What that choice costs before you train anything',
                 fontsize=12, weight='bold')
    _save(fig, 'input-and-output-written-down.svg')


class Attempts:
    """200 simulated pick attempts, scored three ways."""

    def __init__(self) -> None:
        tr, te = CELL.split_tray == 0, CELL.split_tray == 2
        net = train_classifier(CELL.Z[tr], CELL.y[tr])
        pred_frame = predict_classifier(net, CELL.Z[te])
        parts = CELL.part_of_frame[te]
        right_part = {}
        for p in np.unique(parts):
            m = parts == p
            vote = int(np.argmax(np.bincount(pred_frame[m], minlength=3)))
            right_part[int(p)] = vote == int(CELL.grip[p])
        rng = np.random.default_rng(77)
        pick = rng.choice(list(right_part.keys()), size=200)
        right = np.array([right_part[int(p)] for p in pick])
        closed = rng.random(200) < np.where(right, 0.98, 0.80)
        in_box = closed & (rng.random(200) < np.where(right, 0.90, 0.26))
        intact = in_box & (rng.random(200) < np.where(right, 0.97, 0.78))
        self.n = 200
        self.closed = int(closed.sum())
        self.in_box = int(in_box.sum())
        self.intact = int(intact.sum())
        self.right_share = float(right.mean())


def s2_vague_becomes_measurable() -> None:
    at = Attempts()
    labels = ['the gripper\nclosed on\nsomething',
              'the part is\nin the box\nwithin 10 s',
              'in the box,\nwithin 10 s,\nand undamaged']
    vals = [at.closed / at.n * 100, at.in_box / at.n * 100, at.intact / at.n * 100]
    RESULTS['def_a'] = vals[0]
    RESULTS['def_b'] = vals[1]
    RESULTS['def_c'] = vals[2]
    print(f'[s2] the same {at.n} attempts: {at.closed} closed on something '
          f'({vals[0]:.1f}%), {at.in_box} reached the box in time ({vals[1]:.1f}%), '
          f'{at.intact} of those undamaged ({vals[2]:.1f}%)')
    lo, hi = _wilson(at.intact, at.n)
    RESULTS['def_c_lo'], RESULTS['def_c_hi'] = lo * 100, hi * 100
    print(f'[s2] the strict number with its 95% interval: {vals[2]:.1f}% '
          f'({lo * 100:.1f} to {hi * 100:.1f})')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    bars = ax.bar(labels, vals, color=[LINK_PALE, LINK, PURPLE], width=0.55)
    ax.bar_label(bars, labels=[f'{v:.1f}%' for v in vals], fontsize=12, padding=4)
    for x, v, k, col in zip(range(3), vals, [at.closed, at.in_box, at.intact],
                            [INK, 'white', 'white']):
        ax.text(x, v / 2, f'{k} of {at.n}\nattempts', fontsize=10.5, color=col,
                ha='center', va='center', weight='bold')
    ax.set_ylim(0, 108)
    ax.set_ylabel('share of attempts counted as a success (%)', fontsize=10)
    ax.set_title('One recording of 200 attempts, three answers to '
                 '"does it pick things up reliably"', fontsize=12.5, weight='bold')
    _save(fig, 'vague-becomes-measurable.svg')


def s2_wrong_one_number() -> None:
    rng = np.random.default_rng(31)
    cracked = CELL.cracked
    n = len(cracked)
    score = np.where(cracked, rng.normal(0.62, 0.20, n), rng.normal(0.22, 0.17, n))
    found = score > 0.5
    always_no = np.zeros(n, dtype=bool)

    def stats(pred: NDArray[np.bool_]) -> tuple[float, float, float]:
        acc = float((pred == cracked).mean()) * 100
        rec = float(pred[cracked].mean()) * 100 if cracked.sum() else 0.0
        prec = float(cracked[pred].mean()) * 100 if pred.sum() else 0.0
        return acc, rec, prec

    a_no, r_no, p_no = stats(always_no)
    a_det, r_det, p_det = stats(found)
    RESULTS['crack_share'] = float(cracked.mean()) * 100
    RESULTS['always_no_acc'] = a_no
    RESULTS['det_acc'], RESULTS['det_rec'], RESULTS['det_prec'] = a_det, r_det, p_det
    print(f'[s2] cracks: {int(cracked.sum())} of {n} parts are cracked '
          f'({RESULTS["crack_share"]:.1f}%)')
    print(f'[s2] always-no scores {a_no:.1f}% accuracy, finds {r_no:.1f}% of cracks; '
          f'the detector scores {a_det:.1f}% accuracy, finds {r_det:.1f}% of cracks, '
          f'and {p_det:.1f}% of the parts it flags really are cracked')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.0, 1.2]})
    _plain(ax)
    x = np.arange(2)
    w = 0.36
    b1 = ax.bar(x - w / 2, [a_no, a_det], w, color=MUTED, label='accuracy')
    b2 = ax.bar(x + w / 2, [r_no, r_det], w, color=GRIP, label='share of cracks found')
    ax.bar_label(b1, fmt='%.1f%%', fontsize=10.5, padding=3)
    ax.bar_label(b2, fmt='%.1f%%', fontsize=10.5, padding=3)
    ax.set_xticks(x)
    ax.set_xticklabels(['always answer\n"no crack"', 'a real\ndetector'], fontsize=10)
    ax.set_ylim(0, 128)
    ax.set_ylabel('per cent', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='upper center', ncol=2)
    ax.set_title('Accuracy says the useless answer is nearly perfect',
                 fontsize=12, weight='bold')

    _plain(bx)
    bins = np.linspace(-0.3, 1.3, 36)
    bx.hist(score[~cracked], bins=bins, color=LINK, alpha=0.65, label='sound parts')
    bx.hist(score[cracked], bins=bins, color=GRIP, alpha=0.75, label='cracked parts')
    bx.axvline(0.5, color=INK, lw=1.8, ls='--')
    bx.text(0.52, bx.get_ylim()[1] * 0.9, 'flagged above here', fontsize=9.5, color=INK)
    bx.set_xlabel('detector score for one part', fontsize=10)
    bx.set_ylabel('number of parts', fontsize=10)
    bx.set_title(f'Only {int(cracked.sum())} of {n} parts are cracked at all',
                 fontsize=12, weight='bold')
    _save(fig, 'the-wrong-one-number.svg')


def s2_how_many_trials() -> None:
    rng = np.random.default_rng(44)
    p = 0.70
    counts = [20, 60, 200, 600]
    draws = {n: rng.binomial(n, p, 4000) / n * 100 for n in counts}
    widths = []
    for n in counts:
        lo, hi = _wilson(int(round(p * n)), n)
        widths.append((hi - lo) * 100)
        print(f'[s2] {n:3d} trials of a true 70% model: 95% interval '
              f'{lo * 100:.1f} to {hi * 100:.1f}, which is {(hi - lo) * 100:.1f} points wide')
    RESULTS['width_20'] = widths[0]
    RESULTS['width_200'] = widths[2]
    RESULTS['width_600'] = widths[3]

    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    parts = ax.violinplot([draws[n] for n in counts], positions=range(4), widths=0.75,
                          showextrema=False)
    for body in parts['bodies']:
        body.set_facecolor(LINK_PALE)
        body.set_edgecolor(LINK)
        body.set_alpha(0.9)
    for i, n in enumerate(counts):
        lo, hi = _wilson(int(round(p * n)), n)
        ax.plot([i, i], [lo * 100, hi * 100], color=GRIP, lw=3, solid_capstyle='butt')
        ax.text(i, hi * 100 + 1.5, f'{(hi - lo) * 100:.1f} points wide',
                fontsize=10, color=GRIP, ha='center', va='bottom')
    ax.axhline(70.0, color=INK, ls='--', lw=1.5)
    ax.text(-0.45, 105.0, 'the model really succeeds 70% of the time, every time',
            fontsize=10.5, color=INK)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f'{n} trials' for n in counts], fontsize=10.5)
    ax.set_ylabel('success rate the trials report (%)', fontsize=10)
    ax.set_ylim(35, 112)
    ax.set_title('How many attempts the one number needs before it means anything',
                 fontsize=12.5, weight='bold')
    _save(fig, 'how-many-trials.svg')


# ==========================================================================
# section 3: the three cheap baselines
# ==========================================================================

class Baselines:
    """The three baselines and one small model, on the tray split."""

    def __init__(self) -> None:
        tr = CELL.split_tray == 0
        te = CELL.split_tray == 2
        y, Z, X = CELL.y, CELL.Z, CELL.X
        self.n_train = int(tr.sum())
        self.n_test = int(te.sum())
        self.majority_class = int(np.argmax(np.bincount(y[tr], minlength=3)))
        self.majority = float((y[te] == self.majority_class).mean()) * 100
        self.rule = float((hand_rule(X[te]) == y[te]).mean()) * 100
        self.nn_raw = float((nearest_neighbour(X[tr], y[tr], X[te]) == y[te]).mean()) * 100
        self.nn_scaled = float((nearest_neighbour(Z[tr], y[tr], Z[te]) == y[te]).mean()) * 100
        net = train_classifier(Z[tr], y[tr])
        self.pred_model = predict_classifier(net, Z[te])
        self.model = mean_score(Z[tr], y[tr], Z[te], y[te])
        self.model_one_run = float((self.pred_model == y[te]).mean()) * 100
        self.chance = 100.0 / 3.0
        self.pred = {
            'most common class': np.full(self.n_test, self.majority_class),
            'written rule': hand_rule(X[te]),
            'nearest neighbour\n(raw numbers)': nearest_neighbour(X[tr], y[tr], X[te]),
            'small network': self.pred_model,
        }
        self.y_te = y[te]

        # the force job
        f = CELL.f
        self.force_mean = float(np.abs(f[te] - f[tr].mean()).mean())
        rule_f = X[:, 2] / 1000.0 * 9.81 * 1.6 / (2.0 * 0.60)
        self.force_rule = float(np.abs(f[te] - rule_f[te]).mean())
        self.force_nn = float(np.abs(f[te] - nn_regress(X[tr], f[tr], X[te])).mean())
        self.force_model = float(np.mean([
            np.abs(f[te] - predict_regressor(train_regressor(Z[tr], f[tr], seed=s),
                                             Z[te])).mean() for s in range(3)]))
        self.force_spread = float(f[te].std())
        self.force_rule_shiny = float(np.abs(f[te] - rule_f[te])[CELL.X[te, 3] > 0.5].mean())
        self.force_rule_dull = float(np.abs(f[te] - rule_f[te])[CELL.X[te, 3] <= 0.5].mean())


BASE = Baselines()


def s3_three_baselines() -> None:
    names = ['most common\nclass', 'written\nrule', 'nearest neighbour\n(raw numbers)',
             'nearest neighbour\n(scaled numbers)', 'small\nnetwork']
    vals = [BASE.majority, BASE.rule, BASE.nn_raw, BASE.nn_scaled, BASE.model]
    RESULTS['b_majority'] = BASE.majority
    RESULTS['b_rule'] = BASE.rule
    RESULTS['b_nn_raw'] = BASE.nn_raw
    RESULTS['b_nn_scaled'] = BASE.nn_scaled
    RESULTS['b_model'] = BASE.model
    print(f'[s3] grip job on {BASE.n_train} training and {BASE.n_test} held-out frames:')
    for nm, v in zip(names, vals):
        print(f'[s3]   {nm.replace(chr(10), " "):36s} {v:5.1f}%')
    print(f'[s3] guessing one of three would score {BASE.chance:.1f}%')

    fig, ax = plt.subplots(figsize=(11.6, 5.6), facecolor='white')
    _plain(ax)
    colours = [MUTED, GRIP, WRIST, JOINT, LINK]
    bars = ax.bar(names, vals, color=colours, width=0.6)
    ax.bar_label(bars, fmt='%.1f%%', fontsize=12, padding=4)
    ax.axhline(BASE.chance, color=INK, ls=':', lw=1.6)
    ax.set_xlim(-0.6, 5.6)
    ax.text(4.55, BASE.chance, f'guessing one\nof three: {BASE.chance:.1f}%',
            fontsize=10, color=INK, ha='left', va='center')
    ax.axhline(max(BASE.majority, BASE.rule, BASE.nn_raw, BASE.nn_scaled),
               color=GRIP, ls='--', lw=1.6)
    ax.text(-0.45, max(BASE.majority, BASE.rule, BASE.nn_raw, BASE.nn_scaled) + 1.5,
            'the line a model has to clear', fontsize=10, color=GRIP)
    ax.set_ylim(0, 108)
    ax.set_ylabel('share of held-out frames right (%)', fontsize=10)
    ax.set_title('Three cheap baselines and one small network, same data, same split',
                 fontsize=12.5, weight='bold')
    _save(fig, 'three-baselines-classification.svg')


def s3_force_baselines() -> None:
    names = ['predict the\naverage force', 'written physics\nrule', 'nearest\nneighbour',
             'small\nnetwork']
    vals = [BASE.force_mean, BASE.force_rule, BASE.force_nn, BASE.force_model]
    RESULTS['f_mean'] = BASE.force_mean
    RESULTS['f_rule'] = BASE.force_rule
    RESULTS['f_nn'] = BASE.force_nn
    RESULTS['f_model'] = BASE.force_model
    print(f'[s3] squeeze force, average error in newtons: average {BASE.force_mean:.3f}, '
          f'physics rule {BASE.force_rule:.3f}, nearest neighbour {BASE.force_nn:.3f}, '
          f'network {BASE.force_model:.3f}; the forces themselves spread by '
          f'{BASE.force_spread:.3f} N')
    print(f'[s3] the physics rule is wrong by {BASE.force_rule_dull:.3f} N on dull parts '
          f'and {BASE.force_rule_shiny:.3f} N on shiny ones')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.2), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.1, 1.0]})
    _plain(ax)
    bars = ax.bar(names, vals, color=[MUTED, GRIP, WRIST, LINK], width=0.6)
    ax.bar_label(bars, labels=[f'{v:.3f} N' for v in vals], fontsize=11, padding=4)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('average error on held-out frames (N)', fontsize=10)
    ax.set_title(f'Predicting the average costs {BASE.force_mean:.3f} N, a line of '
                 f'school physics {BASE.force_rule:.3f} N', fontsize=12, weight='bold')

    _plain(bx)
    te = CELL.split_tray == 2
    shine = CELL.X[te, 3]
    err = CELL.f[te] - CELL.X[te, 2] / 1000.0 * 9.81 * 1.6 / 1.2
    bx.scatter(shine, err, s=7, color=GRIP, alpha=0.4, edgecolors='none')
    bx.axhline(0.0, color=INK, lw=1.4)
    bx.set_xlabel('measured shine (0 to 1)', fontsize=10)
    bx.set_ylabel('force needed minus force the rule asks for (N)', fontsize=10)
    bx.set_title('And where it is wrong: shiny parts slip',
                 fontsize=12, weight='bold')
    _save(fig, 'three-baselines-regression.svg')


def s3_baseline_moves() -> None:
    tr_all = np.where(CELL.split_tray == 0)[0]
    te = CELL.split_tray == 2
    parts_tr = np.unique(CELL.part_of_frame[tr_all])
    rng = np.random.default_rng(9)
    sizes = [4, 8, 16, 32, 64, 144]
    nn_curve, model_curve = [], []
    for n in sizes:
        nn_runs, md_runs = [], []
        for rep in range(6):
            chosen = rng.choice(parts_tr, size=min(n, len(parts_tr)), replace=False)
            m = np.isin(CELL.part_of_frame, chosen)
            nn_runs.append(float((nearest_neighbour(CELL.X[m], CELL.y[m], CELL.X[te])
                                  == CELL.y[te]).mean()) * 100)
            if rep < 3:
                md_runs.append(mean_score(CELL.Z[m], CELL.y[m], CELL.Z[te], CELL.y[te],
                                          seeds=3))
        nn_curve.append(float(np.mean(nn_runs)))
        model_curve.append(float(np.mean(md_runs)))
    RESULTS['curve_model_4'] = model_curve[0]
    RESULTS['curve_model_16'] = model_curve[2]
    RESULTS['curve_model_144'] = model_curve[-1]
    RESULTS['curve_nn_4'] = nn_curve[0]
    RESULTS['curve_nn_144'] = nn_curve[-1]
    print('[s3] learning curve by number of training parts '
          '(6 draws for the neighbour, 3 draws x 3 starts for the network):')
    for n, a, b in zip(sizes, nn_curve, model_curve):
        print(f'[s3]   {n:4d} parts: nearest neighbour {a:5.1f}%, network {b:5.1f}%')
    passed = [n for n, v in zip(sizes, model_curve) if v > BASE.rule]
    first_pass = passed[0] if passed else None
    print(f'[s3] the network first passes the written rule ({BASE.rule:.1f}%) at '
          f'{first_pass} training parts')
    RESULTS['curve_first_pass'] = float(first_pass or 0)

    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(sizes, model_curve, marker='o', ms=5, color=LINK, lw=2, label='small network')
    ax.plot(sizes, nn_curve, marker='s', ms=5, color=WRIST, lw=2,
            label='nearest neighbour on raw numbers')
    ax.axhline(BASE.rule, color=GRIP, ls='--', lw=1.8, label='written rule')
    ax.axhline(BASE.majority, color=MUTED, ls=':', lw=1.8, label='most common class')
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('number of training parts (12 frames each, log scale)', fontsize=10)
    ax.set_ylabel('share of held-out frames right (%)', fontsize=10)
    ax.set_ylim(25, 100)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title(f'The network first passes the written rule at {first_pass} '
                 'training parts, and not before', fontsize=12.5, weight='bold')
    _save(fig, 'baseline-moves-with-data.svg')


def s3_per_class() -> None:
    names = list(BASE.pred.keys())
    fig, ax = plt.subplots(figsize=(11.8, 5.4), facecolor='white')
    _plain(ax)
    w = 0.2
    xs = np.arange(3)
    print('[s3] share of each grip found, by method:')
    for i, nm in enumerate(names):
        pred = BASE.pred[nm]
        vals = [float((pred[BASE.y_te == g] == g).mean()) * 100 for g in range(3)]
        bars = ax.bar(xs + (i - 1.5) * w, vals, w,
                      color=[MUTED, GRIP, WRIST, LINK][i], label=nm.replace('\n', ' '))
        ax.bar_label(bars, fmt='%.0f', fontsize=9, padding=2)
        print(f'[s3]   {nm.replace(chr(10), " "):32s} ' +
              '  '.join(f'{g}:{v:5.1f}%' for g, v in zip(GRIPS, vals)))
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{g} is the right grip' for g in GRIPS], fontsize=10.5)
    ax.set_ylabel('share of those frames answered right (%)', fontsize=10)
    ax.set_ylim(0, 118)
    ax.legend(fontsize=9.5, frameon=False, ncol=2, loc='upper center')
    ax.set_title(f'The most common class scores {BASE.majority:.1f} per cent by getting '
                 'one grip right and the others never', fontsize=12.5, weight='bold')
    _save(fig, 'baseline-per-class.svg')


# ==========================================================================
# section 4: the first hundred examples
# ==========================================================================

def s4_looking_finds_it() -> None:
    ns = np.arange(1, 301)
    p5 = 1.0 - (1.0 - 0.05) ** ns
    p2 = 1.0 - (1.0 - 0.02) ** ns
    p20 = 1.0 - (1.0 - 0.20) ** ns
    picks = [10, 30, 100, 300]
    print('[s4] chance of seeing at least one example of a fault while looking by hand:')
    for n in picks:
        print(f'[s4]   look at {n:3d}: fault in 20% of examples {p20[n - 1] * 100:5.1f}%, '
              f'in 5% {p5[n - 1] * 100:5.1f}%, in 2% {p2[n - 1] * 100:5.1f}%')
    RESULTS['look10_5'] = p5[9] * 100
    RESULTS['look100_5'] = p5[99] * 100
    RESULTS['look100_2'] = p2[99] * 100

    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(ns, p20 * 100, color=SLIDE, lw=2, label='fault in 20% of examples')
    ax.plot(ns, p5 * 100, color=LINK, lw=2, label='fault in 5% of examples')
    ax.plot(ns, p2 * 100, color=PURPLE, lw=2, label='fault in 2% of examples')
    for n, colour, curve in ((10, LINK, p5), (100, LINK, p5)):
        ax.plot([n], [curve[n - 1] * 100], marker='o', ms=7, color=colour)
        ax.annotate(f'{curve[n - 1] * 100:.1f}% after {n}',
                    xy=(n, curve[n - 1] * 100),
                    xytext=(n + 24, curve[n - 1] * 100 - 16), fontsize=10, color=colour,
                    arrowprops=dict(arrowstyle='->', color=colour, lw=1.3))
    ax.set_xlabel('examples you open and look at', fontsize=10)
    ax.set_ylabel('chance of meeting the fault at least once (%)', fontsize=10)
    ax.set_ylim(0, 105)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('Ten examples miss most faults, a hundred catch nearly all of them',
                 fontsize=12.5, weight='bold')
    _save(fig, 'faults-in-the-first-hundred.svg')


def s4_enough_to_cover() -> None:
    """How many parts it takes before every kind of part has been recorded twice."""
    metal = CELL.true_props[:, 3] > 0.42
    flat = CELL.true_props[:, 4] > 0.5
    kind = CELL.grip * 4 + metal.astype(int) * 2 + flat.astype(int)
    all_counts = np.bincount(kind, minlength=12)
    # a suction grip on a dull curved part never happens, so count only the kinds
    # that occur at all: those are the situations the recording has to cover.
    present = np.where(all_counts >= 4)[0]
    n_kinds = len(present)
    counts = all_counts[present]
    remap = -np.ones(12, dtype=int)
    remap[present] = np.arange(n_kinds)
    kind = remap[kind]
    kind = np.where(kind < 0, n_kinds, kind)        # the empty kinds fall off the end
    rng = np.random.default_rng(88)
    sizes = list(range(4, 241, 4))
    covered, all_covered = [], []
    for n in sizes:
        got, full = [], []
        for _ in range(300):
            take = rng.choice(CELL.n_parts, size=n, replace=False)
            c = np.bincount(kind[take], minlength=n_kinds + 1)[:n_kinds]
            got.append(int((c >= 2).sum()))
            full.append(bool((c >= 2).all()))
        covered.append(float(np.mean(got)))
        all_covered.append(float(np.mean(full)) * 100)
    for n in (8, 24, 48, 100, 200):
        i = sizes.index(min(sizes, key=lambda s: abs(s - n)))
        print(f'[s4] {sizes[i]:3d} parts recorded: {covered[i]:.1f} of {n_kinds} kinds seen '
              f'at least twice, all {n_kinds} in {all_covered[i]:.1f}% of draws')
    RESULTS['n_kinds'] = float(n_kinds)
    RESULTS['cover_24'] = covered[sizes.index(24)]
    RESULTS['cover_100'] = covered[sizes.index(100)]
    RESULTS['cover_all_100'] = all_covered[sizes.index(100)]
    rarest = int(present[int(np.argmin(counts))])
    print(f'[s4] the {n_kinds} kinds that occur hold {counts.min()} to {counts.max()} of '
          f'the 240 parts (the rarest is {GRIPS[rarest // 4]} on a '
          f'{"shiny" if (rarest % 4) // 2 else "dull"} part with a '
          f'{"flat" if rarest % 2 else "curved"} top)')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.2, 1.0]})
    _plain(ax)
    ax.plot(sizes, covered, color=LINK, lw=2)
    ax.plot(sizes, np.array(all_covered) / 100.0 * n_kinds, color=PURPLE, lw=2, ls='--')
    ax.axhline(n_kinds, color=MUTED, ls=':', lw=1.4)
    ax.text(242, n_kinds, f'all {n_kinds} kinds', fontsize=9.5, color=MUTED, va='center')
    for n in (24, 100):
        i = sizes.index(n)
        ax.plot([n], [covered[i]], marker='o', ms=7, color=LINK)
        ax.annotate(f'{covered[i]:.1f} kinds after {n} parts', xy=(n, covered[i]),
                    xytext=(n + 16, covered[i] - 2.0), fontsize=10, color=LINK,
                    arrowprops=dict(arrowstyle='->', color=LINK, lw=1.3))
    ax.text(96, 1.0, f'dashed line: the share of draws in which\nall {n_kinds} appear '
                     'twice, on the same scale', fontsize=9.5, color=PURPLE)
    ax.set_xlim(0, 290)
    ax.set_ylim(0, n_kinds + 1.6)
    ax.set_xlabel('parts recorded', fontsize=10)
    ax.set_ylabel('kinds of part seen at least twice', fontsize=10)
    ax.set_title('How few examples you can honestly start with', fontsize=12, weight='bold')

    _plain(bx)
    labels = [f'{GRIPS[k // 4]}\n{"shiny" if (k % 4) // 2 else "dull"}, '
              f'{"flat" if k % 2 else "curved"}' for k in present]
    order = np.argsort(counts)
    bars = bx.barh([labels[i] for i in order], counts[order], color=LINK, height=0.65)
    bx.bar_label(bars, fontsize=9.5, padding=3)
    bx.set_xlim(0, counts.max() * 1.22)
    bx.tick_params(labelsize=8.5)
    bx.set_xlabel('parts of that kind among the 240', fontsize=10)
    bx.set_title('The kinds are not equally common', fontsize=12, weight='bold')
    _save(fig, 'enough-to-cover-the-cases.svg')


def s4_what_faults_cost() -> None:
    tr = CELL.split_tray == 0
    te = CELL.split_tray == 2
    rng = np.random.default_rng(101)

    y_clean = CELL.y.copy()
    X_clean = CELL.X.copy()

    # fault 1: 7 per cent of parts labelled with the wrong grip
    parts_tr = np.unique(CELL.part_of_frame[tr])
    bad_parts = rng.choice(parts_tr, size=int(round(0.07 * len(parts_tr))), replace=False)
    y_bad = y_clean.copy()
    for p in bad_parts:
        m = CELL.part_of_frame == p
        y_bad[m] = (y_clean[m] + rng.integers(1, 3)) % 3

    # fault 2: on a third of the trays the shine reading is stuck at one value
    stuck_trays = np.unique(CELL.tray_of_frame[tr])[:8]
    X_stuck = X_clean.copy()
    m = np.isin(CELL.tray_of_frame, stuck_trays)
    X_stuck[m, 3] = 0.31

    # fault 3: 24 parts recorded four times each, against 96 different parts, same rows
    many = rng.choice(parts_tr, size=96, replace=False)
    many_idx = np.where(np.isin(CELL.part_of_frame, many))[0]
    few = rng.choice(parts_tr, size=24, replace=False)
    few_idx = np.where(np.isin(CELL.part_of_frame, few))[0]
    dup_idx = np.concatenate([few_idx] * 4)

    def score(Xa: Arr, ya: Ints, idx: NDArray[np.int64] | None = None) -> float:
        mtr = np.where(tr)[0] if idx is None else idx
        base = np.where(tr)[0]
        Z = (Xa - Xa[base].mean(0)) / Xa[base].std(0)
        return mean_score(Z[mtr], ya[mtr], Z[te], CELL.y[te])

    clean = score(X_clean, y_clean)
    mislabel = score(X_clean, y_bad)
    stuck = score(X_stuck, y_clean)
    variety = score(X_clean, y_clean, many_idx)
    dup = score(X_clean, y_clean, dup_idx)
    RESULTS['fault_clean'] = clean
    RESULTS['fault_mislabel'] = mislabel
    RESULTS['fault_stuck'] = stuck
    RESULTS['fault_variety'] = variety
    RESULTS['fault_dup'] = dup
    RESULTS['n_bad_parts'] = float(len(bad_parts))
    print(f'[s4] faults planted in the training frames, same held-out frames throughout: '
          f'clean {clean:.1f}%, {len(bad_parts)} of {len(parts_tr)} parts mislabelled '
          f'{mislabel:.1f}%, shine stuck on {len(stuck_trays)} of 24 trays {stuck:.1f}%')
    print(f'[s4] same {len(many_idx)} training frames either way: 96 different parts '
          f'{variety:.1f}%, 24 parts recorded four times each {dup:.1f}%')

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13.2, 5.2), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.35, 1.0]})
    _plain(ax)
    names = ['all 144 parts,\nas recorded', f'{len(bad_parts)} parts\nlabelled wrongly',
             f'shine stuck on\n{len(stuck_trays)} trays',
             '96 different\nparts', '24 parts, each\nrecorded 4 times']
    vals = [clean, mislabel, stuck, variety, dup]
    bars = ax.bar(names, vals, color=[SLIDE, GRIP, GRIP, LINK, GRIP], width=0.6)
    ax.bar_label(bars, fmt='%.1f%%', fontsize=11, padding=4)
    ax.axhline(clean, color=SLIDE, ls='--', lw=1.5)
    ax.tick_params(axis='x', labelsize=9.5)
    ax.set_ylim(0, 108)
    ax.set_ylabel('share of held-out frames right (%)', fontsize=10)
    ax.set_title('What each fault costs, measured on the same held-out frames',
                 fontsize=12, weight='bold')

    _plain(bx)
    bx.scatter(CELL.X[tr, 0], CELL.X[tr, 3], s=6, color=LINK, alpha=0.35,
               edgecolors='none', label='as recorded')
    bx.scatter(X_stuck[m, 0], X_stuck[m, 3], s=9, color=GRIP, alpha=0.8,
               edgecolors='none', label=f'{len(stuck_trays)} trays, shine stuck at 0.31')
    bx.set_xlabel('measured width (mm)', fontsize=10)
    bx.set_ylabel('measured shine (0 to 1)', fontsize=10)
    bx.set_ylim(-0.03, 1.03)
    bx.legend(fontsize=9.5, frameon=False, loc='upper left')
    bx.set_title('A stuck sensor is a flat line you can see in one plot',
                 fontsize=12, weight='bold')
    _save(fig, 'what-the-faults-cost.svg')


def s4_labellers_disagree() -> None:
    rng = np.random.default_rng(55)
    margin = CELL.margin
    flip = rng.random(CELL.n_parts) < np.exp(-margin / 0.22) * 0.5
    second = CELL.grip.copy()
    second[flip] = (CELL.grip[flip] + rng.integers(1, 3, int(flip.sum()))) % 3
    agree = float((second == CELL.grip).mean()) * 100
    edges = [0.0, 0.1, 0.25, 0.5, 1.0, 3.0]
    rates, labels, counts = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (margin >= a) & (margin < b)
        rates.append(float((second[m] == CELL.grip[m]).mean()) * 100)
        counts.append(int(m.sum()))
        labels.append(f'{a:g} to {b:g}')
    RESULTS['agree'] = agree
    RESULTS['agree_closest'] = rates[0]
    print(f'[s4] two labellers agree on {agree:.1f}% of the {CELL.n_parts} parts; '
          f'by how clear the right grip is: ' +
          ', '.join(f'{lab} -> {r:.1f}% ({c} parts)'
                    for lab, r, c in zip(labels, rates, counts)))

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.25, 1.0]})
    _plain(ax)
    bars = ax.bar(labels, rates, color=LINK, width=0.6)
    ax.bar_label(bars, fmt='%.1f%%', fontsize=10.5, padding=3)
    for x, c in enumerate(counts):
        ax.text(x, 4, f'{c}\nparts', fontsize=9.5, color='white', ha='center', weight='bold')
    ax.axhline(agree, color=GRIP, ls='--', lw=1.8)
    ax.text(-0.45, agree + 10, f'all parts: {agree:.1f}%', fontsize=10, color=GRIP)
    ax.set_xlabel('how far ahead the right grip is of the next best', fontsize=10)
    ax.set_ylabel('two labellers give the same answer (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('Where the labels disagree: the parts that are nearly either',
                 fontsize=12, weight='bold')

    _plain(bx)
    bx.hist(margin, bins=np.linspace(0, 2.0, 30), color=LINK_PALE, edgecolor=LINK)
    bx.axvline(0.1, color=GRIP, lw=2)
    bx.text(0.13, bx.get_ylim()[1] * 0.85, f'{counts[0]} parts this close',
            fontsize=10, color=GRIP)
    bx.set_xlabel('how far ahead the right grip is of the next best', fontsize=10)
    bx.set_ylabel('number of parts', fontsize=10)
    bx.set_title('How many borderline parts there are at all', fontsize=12, weight='bold')
    _save(fig, 'labellers-disagree.svg')


# ==========================================================================
# section 5: the split
# ==========================================================================

def _draw_split(kind: str, seed: int) -> Ints:
    """Draw one 60/20/20 split of the recording, cut along frames, parts or trays."""
    rng = np.random.default_rng(seed)
    if kind == 'tray':
        return Cell._by_group(CELL.tray_of_frame, rng.permutation(N_TRAYS), 24, 8)
    if kind == 'part':
        return Cell._by_group(CELL.part_of_frame, rng.permutation(CELL.n_parts), 144, 48)
    n = len(CELL.y)
    order = rng.permutation(n)
    mask = np.zeros(n, dtype=int)
    mask[order[int(0.6 * n):int(0.8 * n)]] = 1
    mask[order[int(0.8 * n):]] = 2
    return mask


def s5_three_splits() -> None:
    out, spread = {}, {}
    for name, kind in (('random frame split', 'frame'),
                       ('whole part held out', 'part'),
                       ('whole tray held out', 'tray')):
        runs = []
        for draw in range(5):
            split = _draw_split(kind, 100 + draw)
            tr, te = split == 0, split == 2
            mean, sd = CELL.X[tr].mean(0), CELL.X[tr].std(0)
            Z = (CELL.X - mean) / sd
            runs.append(mean_score(Z[tr], CELL.y[tr], Z[te], CELL.y[te], seeds=2))
        out[name] = float(np.mean(runs))
        spread[name] = (float(np.min(runs)), float(np.max(runs)))
        print(f'[s5] {name:22s} over 5 different draws of the split: '
              f'{out[name]:.1f}% on average, between {spread[name][0]:.1f} and '
              f'{spread[name][1]:.1f}')
    RESULTS['split_frame'] = out['random frame split']
    RESULTS['split_part'] = out['whole part held out']
    RESULTS['split_tray'] = out['whole tray held out']

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 5.2), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.1, 1.0]})
    _plain(ax)
    names = ['random\nframe split', 'whole part\nheld out', 'whole tray\nheld out']
    keys = ['random frame split', 'whole part held out', 'whole tray held out']
    vals = [out[k] for k in keys]
    err = np.array([[v - spread[k][0] for v, k in zip(vals, keys)],
                    [spread[k][1] - v for v, k in zip(vals, keys)]])
    bars = ax.bar(names, vals, color=[GRIP, JOINT, SLIDE], width=0.55,
                  yerr=err, capsize=6, ecolor=INK)
    ax.bar_label(bars, fmt='%.1f%%', fontsize=12, padding=14)
    ax.axhline(100.0 / 3.0, color=INK, ls=':', lw=1.5)
    ax.set_xlim(-0.6, 3.1)
    ax.text(2.6, 100.0 / 3.0, 'guessing', fontsize=9.5, color=INK, ha='left', va='center')
    ax.set_ylim(0, 118)
    ax.set_ylabel('share of held-out frames right (%)', fontsize=10)
    ax.set_title('One model, one recording, three answers\n(bars are the average of five '
                 'draws, whiskers the range)', fontsize=12, weight='bold')

    _plain(bx)
    same, other = [], []
    rng = np.random.default_rng(3)
    Z = CELL.Z
    for p in rng.choice(CELL.n_parts, 80, replace=False):
        m = CELL.part_of_frame == p
        idx = np.where(m)[0]
        d_in = ((Z[idx[0]] - Z[idx[1:]]) ** 2).sum(axis=1) ** 0.5
        others = np.where(~m)[0]
        d_out = ((Z[idx[0]] - Z[others]) ** 2).sum(axis=1) ** 0.5
        same.append(float(d_in.min()))
        other.append(float(d_out.min()))
    bins = np.linspace(0, 1.4, 34)
    bx.hist(same, bins=bins, color=GRIP, alpha=0.8, label='nearest frame of the same part')
    bx.hist(other, bins=bins, color=LINK, alpha=0.65, label='nearest frame of another part')
    bx.set_xlabel('distance in the five measured numbers (standardised)', fontsize=10)
    bx.set_ylabel('number of frames', fontsize=10)
    bx.legend(fontsize=9.5, frameon=False, loc='upper right')
    bx.set_title(f'Why: the same part again is {np.mean(other) / np.mean(same):.1f} times '
                 'closer than any other part', fontsize=12, weight='bold')
    print(f'[s5] nearest frame of the same part sits {np.mean(same):.3f} away on average '
          f'and the nearest frame of any other part {np.mean(other):.3f}, which is '
          f'{np.mean(other) / np.mean(same):.1f} times further')
    RESULTS['near_same'] = float(np.mean(same))
    RESULTS['near_other'] = float(np.mean(other))
    RESULTS['near_ratio'] = float(np.mean(other) / np.mean(same))
    _save(fig, 'three-splits-three-scores.svg')


def s5_split_written_down() -> None:
    fig, ax = plt.subplots(figsize=(12.0, 5.2), facecolor='white')
    _blank(ax)
    role = np.zeros(N_TRAYS, dtype=int)
    role[CELL.val_trays] = 1
    role[CELL.held_out_trays] = 2
    colours = {0: LINK_PALE, 1: JOINT, 2: GRIP}
    names = {0: 'train', 1: 'validation', 2: 'test'}
    for t in range(N_TRAYS):
        row, col = divmod(t, 10)
        for p in range(PARTS_PER_TRAY):
            x = col * 1.0 + p * 0.14
            y = -row * 1.0
            ax.add_patch(mpatches.Rectangle((x, y), 0.12, 0.62, facecolor=colours[role[t]],
                                            edgecolor='white', lw=0.6))
        ax.text(col + 0.42, y - 0.22, f'tray {t}', fontsize=8, color=MUTED, ha='center')
    counts = {k: int((CELL.split_tray == k).sum()) for k in (0, 1, 2)}
    part_counts = {k: int(role[role == k].size) * PARTS_PER_TRAY for k in (0, 1, 2)}
    handles = [mpatches.Patch(facecolor=colours[k],
                              label=f'{names[k]}: {int((role == k).sum())} trays, '
                                    f'{part_counts[k]} parts, {counts[k]} frames')
               for k in (0, 1, 2)]
    ax.legend(handles=handles, fontsize=10.5, frameon=False, loc='lower center',
              bbox_to_anchor=(0.5, -0.12), ncol=3)
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-3.45, 0.85)
    ax.set_title('The split written down before training: 40 trays, 6 parts each, '
                 '12 frames a part', fontsize=12.5, weight='bold')
    print(f'[s5] tray split: ' +
          ', '.join(f'{names[k]} {int((role == k).sum())} trays / {part_counts[k]} parts '
                    f'/ {counts[k]} frames' for k in (0, 1, 2)))
    print(f'[s5] the held-out trays are {[int(t) for t in CELL.held_out_trays]} and the '
          f'validation trays are {[int(t) for t in CELL.val_trays]}')
    _save(fig, 'the-split-written-down.svg')


def s5_trays_differ() -> None:
    """A tray is a real thing: its camera reads wider and its light reads brighter."""
    # the offset itself: how far that tray's readings sit from the part's real size,
    # which is the camera alignment and the lighting rather than which parts were on it
    err_w = CELL.X[:, 0] - CELL.true_props[CELL.part_of_frame, 0]
    err_s = CELL.X[:, 3] - CELL.true_props[CELL.part_of_frame, 3]
    dw = np.array([err_w[CELL.tray_of_frame == t].mean() for t in range(N_TRAYS)])
    ds = np.array([err_s[CELL.tray_of_frame == t].mean() for t in range(N_TRAYS)])
    print(f'[s5] tray by tray, the width reading sits between {dw.min():+.1f} and '
          f'{dw.max():+.1f} mm from the part\'s real width, and the shine reading between '
          f'{ds.min():+.3f} and {ds.max():+.3f}')
    within = float(np.mean([CELL.X[CELL.part_of_frame == p, 0].std()
                            for p in range(CELL.n_parts)]))
    print(f'[s5] the twelve frames of one part differ by {within:.2f} mm, while the '
          f'tray-to-tray spread of the width offset is {dw.std():.2f} mm')
    RESULTS['within_part_mm'] = within
    RESULTS['tray_w_sd'] = float(dw.std())
    RESULTS['tray_w_lo'], RESULTS['tray_w_hi'] = float(dw.min()), float(dw.max())
    RESULTS['tray_s_lo'], RESULTS['tray_s_hi'] = float(ds.min()), float(ds.max())

    fig, (ax, bx) = plt.subplots(2, 1, figsize=(12.0, 5.8), facecolor='white', sharex=True)
    _plain(ax)
    held = np.zeros(N_TRAYS, dtype=bool)
    held[CELL.held_out_trays] = True
    ax.bar(range(N_TRAYS), dw, color=np.where(held, GRIP, LINK), width=0.68)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_ylabel('width reading minus\nthe part\'s real\nwidth (mm)', fontsize=9.5)
    ax.set_title('Every tray reads differently, and the held-out trays (red) were never '
                 'seen', fontsize=12, weight='bold')
    _plain(bx)
    bx.bar(range(N_TRAYS), ds, color=np.where(held, GRIP, LINK), width=0.68)
    bx.axhline(0, color=INK, lw=1.0)
    bx.set_xticks(range(0, N_TRAYS, 2))
    bx.set_xlabel('tray number', fontsize=10)
    bx.set_ylabel('shine reading minus\nthe part\'s real\nshine', fontsize=9.5)
    _save(fig, 'trays-differ.svg')


def s5_how_many_held_out() -> None:
    rng = np.random.default_rng(66)
    ns = [10, 20, 40, 80, 160, 320]
    curves = {}
    for gap in (0.10, 0.05):
        wins = []
        for n in ns:
            a = rng.binomial(n, 0.70, 20000)
            b = rng.binomial(n, 0.70 + gap, 20000)
            wins.append(float((b > a).mean() + 0.5 * (b == a).mean()) * 100)
        curves[gap] = wins
        print(f'[s5] telling a {int((0.70 + gap) * 100)}% model from a 70% one: ' +
              ', '.join(f'{n} attempts each -> right {w:.1f}% of the time'
                        for n, w in zip(ns, wins)))
    RESULTS['tell_20_10'] = curves[0.10][1]
    RESULTS['tell_160_10'] = curves[0.10][4]
    RESULTS['tell_320_5'] = curves[0.05][5]

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(ns, curves[0.10], marker='o', ms=5, color=LINK, lw=2,
            label='80% model against a 70% one')
    ax.plot(ns, curves[0.05], marker='s', ms=5, color=PURPLE, lw=2,
            label='75% model against a 70% one')
    ax.axhline(50, color=MUTED, ls=':', lw=1.5)
    ax.text(10, 51.5, 'a coin toss', fontsize=9.5, color=MUTED, ha='left')
    ax.axhline(90, color=SLIDE, ls='--', lw=1.5)
    ax.text(10, 91.5, 'right nine times in ten', fontsize=9.5, color=SLIDE, ha='left')
    ax.set_xscale('log')
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel('held-out attempts given to each model (log scale)', fontsize=10)
    ax.set_ylabel('how often the better model is chosen (%)', fontsize=10)
    ax.set_ylim(40, 102)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('How big the held-out set has to be to tell two models apart',
                 fontsize=12.5, weight='bold')
    _save(fig, 'how-many-held-out-attempts.svg')


# ==========================================================================
# section 6: what you should have written down
# ==========================================================================

def s6_the_gate() -> None:
    te = CELL.split_tray == 2
    n_parts_te = len(np.unique(CELL.part_of_frame[te]))
    tr_all = np.where(CELL.split_tray == 0)[0]
    parts_tr = np.unique(CELL.part_of_frame[tr_all])
    rng = np.random.default_rng(12)
    parts = CELL.part_of_frame[te]

    def per_part(pred: Ints) -> int:
        """How many of the held-out parts the answer gets right, one vote a part."""
        right = 0
        for p in np.unique(parts):
            mm = parts == p
            vote = int(np.argmax(np.bincount(pred[mm], minlength=3)))
            right += int(vote == int(CELL.grip[p]))
        return right

    cands = {}
    for n in (6, 24, 144):
        chosen = rng.choice(parts_tr, size=min(n, len(parts_tr)), replace=False)
        m = np.isin(CELL.part_of_frame, chosen)
        got = int(round(float(np.mean([
            per_part(predict_classifier(train_classifier(CELL.Z[m], CELL.y[m], seed=s),
                                        CELL.Z[te])) for s in range(4)]))))
        cands[n] = (got, got / n_parts_te * 100, _wilson(got, n_parts_te))

    right_parts = per_part(hand_rule(CELL.X[te]))
    lo, hi = _wilson(right_parts, n_parts_te)
    base = right_parts / n_parts_te * 100
    RESULTS['gate_base'] = base
    RESULTS['gate_lo'], RESULTS['gate_hi'] = lo * 100, hi * 100
    RESULTS['gate_6'], RESULTS['gate_24'], RESULTS['gate_144'] = \
        cands[6][1], cands[24][1], cands[144][1]
    print(f'[s6] every answer below is scored one vote a part on the same '
          f'{n_parts_te} held-out parts')
    print(f'[s6] the written rule gets {right_parts} of {n_parts_te} right, '
          f'which is {base:.1f}% with a 95% interval of {lo * 100:.1f} to {hi * 100:.1f}')
    for n in (6, 24, 144):
        got, pct, (a, b) = cands[n]
        print(f'[s6] a network trained on {n:3d} parts gets {got} of {n_parts_te} right, '
              f'{pct:.1f}% ({a * 100:.1f} to {b * 100:.1f})')

    fig, ax = plt.subplots(figsize=(11.0, 5.6), facecolor='white')
    _plain(ax)
    ax.axhspan(lo * 100, hi * 100, color=GRIP, alpha=0.14)
    ax.axhline(base, color=GRIP, lw=2)
    ax.text(3.52, base, f'the written rule\n{base:.1f}% '
                        f'({lo * 100:.0f} to {hi * 100:.0f})',
            fontsize=10.5, color=GRIP, ha='left', va='center')
    names = ['network on\n6 parts', 'network on\n24 parts', 'network on\n144 parts']
    vals = [cands[n][1] for n in (6, 24, 144)]
    err = np.array([[v - cands[n][2][0] * 100 for v, n in zip(vals, (6, 24, 144))],
                    [cands[n][2][1] * 100 - v for v, n in zip(vals, (6, 24, 144))]])
    bars = ax.bar(names, vals, color=[MUTED, JOINT, LINK], width=0.5,
                  yerr=err, capsize=6, ecolor=INK)
    ax.bar_label(bars, fmt='%.1f%%', fontsize=11.5, padding=16)
    ax.axhline(100.0 / 3.0, color=INK, ls=':', lw=1.4)
    ax.text(3.52, 100.0 / 3.0, 'guessing', fontsize=9.5, color=INK, ha='left', va='center')
    ax.set_xlim(-0.6, 4.6)
    ax.set_ylim(0, 118)
    ax.set_ylabel(f'share of the {n_parts_te} held-out parts right (%)', fontsize=10)
    cleared = [n for n in (6, 24, 144) if cands[n][2][0] * 100 > hi * 100]
    ax.set_title(f'With {n_parts_te} held-out parts, ' +
                 ('every interval still overlaps the written rule\'s'
                  if not cleared else
                  f'only the network on {cleared[0]} parts clears the written rule'),
                 fontsize=12.5, weight='bold')
    print(f'[s6] candidates whose interval clears the written rule\'s: '
          f'{cleared if cleared else "none"}')
    _save(fig, 'the-gate.svg')


CANDIDATES: dict[str, Arr] = {}


def s6_best_of_k() -> None:
    """Train 24 candidates, then measure what choosing the best of k costs."""
    te = CELL.split_tray == 2
    val = CELL.split_tray == 1
    tr_all = np.where(CELL.split_tray == 0)[0]
    parts_tr = np.unique(CELL.part_of_frame[tr_all])
    rng = np.random.default_rng(17)
    scores_val, scores_te = [], []
    for seed in range(24):
        chosen = rng.choice(parts_tr, size=rng.integers(60, 145), replace=False)
        m = np.isin(CELL.part_of_frame, chosen)
        net = train_classifier(CELL.Z[m], CELL.y[m], seed=seed)
        scores_val.append(float((predict_classifier(net, CELL.Z[val])
                                 == CELL.y[val]).mean()) * 100)
        scores_te.append(float((predict_classifier(net, CELL.Z[te])
                                == CELL.y[te]).mean()) * 100)
    sv, st = np.array(scores_val), np.array(scores_te)
    CANDIDATES['val'], CANDIDATES['test'] = sv, st
    ks = list(range(1, 25))
    pick_rng = np.random.default_rng(23)
    chosen_val, chosen_te = [], []
    for k in ks:
        a, b = [], []
        for _ in range(2000):
            idx = pick_rng.choice(24, size=k, replace=False)
            win = idx[int(np.argmax(sv[idx]))]
            a.append(sv[win])
            b.append(st[win])
        chosen_val.append(float(np.mean(a)))
        chosen_te.append(float(np.mean(b)))
    gaps = [v - t for v, t in zip(chosen_val, chosen_te)]
    RESULTS['bestofk_gap'] = gaps[9]
    RESULTS['bestofk_val'] = chosen_val[9]
    RESULTS['bestofk_te'] = chosen_te[9]
    for k in (1, 4, 10, 24):
        print(f'[s6] best of {k:2d} candidates: looks like {chosen_val[k - 1]:.1f}% on the '
              f'set it was chosen on, really {chosen_te[k - 1]:.1f}% on the set read once, '
              f'a gap of {gaps[k - 1]:.1f} points')

    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(ks, chosen_val, marker='o', ms=4.5, color=GRIP, lw=2,
            label='score on the set it was chosen on')
    ax.plot(ks, chosen_te, marker='s', ms=4.5, color=LINK, lw=2,
            label='score on the set read once at the end')
    ax.fill_between(ks, chosen_te, chosen_val, color=GRIP, alpha=0.12)
    ax.annotate(f'{gaps[-1]:.1f} points of\nfree score', xy=(24, (chosen_val[-1] +
                                                               chosen_te[-1]) / 2),
                xytext=(18.0, chosen_te[-1] - 4.0), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.3))
    ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel('candidate models compared before one is kept', fontsize=10)
    ax.set_ylabel('share of held-out frames right (%)', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='lower right')
    ax.set_title('The more candidates you compare, the more the chosen one flatters itself',
                 fontsize=12.5, weight='bold')
    _save(fig, 'best-of-k.svg')


def s6_inflation() -> None:
    chosen_inflation = RESULTS['bestofk_gap']

    items = [
        ('splitting frames at\nrandom instead of\nby whole tray',
         RESULTS['split_frame'] - RESULTS['split_tray']),
        ('calling "the gripper\nclosed" a success\ninstead of "in the box,\nundamaged"',
         RESULTS['def_a'] - RESULTS['def_c']),
        (f'reporting accuracy on\na job where {RESULTS["crack_share"]:.0f}% of\n'
         'parts are cracked', RESULTS['always_no_acc'] - 0.0),
        ('reading the score off\nthe set you chose on',
         chosen_inflation),
    ]
    print('[s6] points of free score from each shortcut: ' +
          ', '.join(f'{nm.replace(chr(10), " ")} = {v:+.1f}' for nm, v in items))

    fig, ax = plt.subplots(figsize=(12.0, 5.6), facecolor='white')
    _plain(ax)
    bars = ax.barh([nm for nm, _ in items], [v for _, v in items],
                   color=[GRIP, WRIST, PURPLE, JOINT], height=0.55)
    ax.bar_label(bars, labels=[f'+{v:.1f} points' for _, v in items], fontsize=11, padding=4)
    ax.invert_yaxis()
    ax.set_xlim(0, max(v for _, v in items) * 1.3)
    ax.set_xlabel('points the reported number gains over the honest one', fontsize=10)
    ax.tick_params(labelsize=9.5)
    ax.set_title('Four ways to make the number look better without making the robot better',
                 fontsize=12.5, weight='bold')
    _save(fig, 'what-each-line-rules-out.svg')


def s6_sheet() -> None:
    rows = [
        ('the job, in one sentence',
         'choose pinch, wrap or suction for one part on a tray'),
        ('what goes in',
         f'{len(FEATURES)} numbers a frame: ' + ', '.join(FEATURES)),
        ('what comes out',
         'one of three grips (pinch, wrap, suction)'),
        ('the one number',
         'share of held-out parts placed in the box within 10 s, undamaged'),
        ('measured on',
         f'{len(np.unique(CELL.part_of_frame[CELL.split_tray == 2]))} parts from '
         f'{len(CELL.held_out_trays)} trays nobody trained on'),
        ('target before training',
         f'beat {RESULTS["gate_base"]:.1f}% by more than the interval '
         f'({RESULTS["gate_lo"]:.0f} to {RESULTS["gate_hi"]:.0f})'),
        ('baseline 1: most common class', f'{RESULTS["b_majority"]:.1f}%'),
        ('baseline 2: written rule', f'{RESULTS["b_rule"]:.1f}%'),
        ('baseline 3: nearest neighbour',
         f'{RESULTS["b_nn_raw"]:.1f}% raw, {RESULTS["b_nn_scaled"]:.1f}% scaled'),
        ('the split, fixed on day one',
         f'{int((CELL.split_tray == 0).sum())} / {int((CELL.split_tray == 1).sum())} / '
         f'{int((CELL.split_tray == 2).sum())} frames, split by tray'),
        ('what the labels can be trusted to',
         f'two labellers agree on {RESULTS["agree"]:.1f}% of parts'),
    ]
    fig, ax = plt.subplots(figsize=(12.6, 6.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(rows) + 1.1)
    for i, (left, right) in enumerate(rows):
        y = len(rows) - i
        ax.add_patch(mpatches.Rectangle((0.005, y - 0.42), 0.99, 0.84,
                                        facecolor=LINK_PALE if i % 2 == 0 else 'white',
                                        edgecolor='none'))
        ax.text(0.02, y, left, fontsize=10.5, color=INK, va='center', weight='bold')
        ax.text(0.37, y, right, fontsize=10.5, color=INK, va='center')
    ax.plot([0.355, 0.355], [0.5, len(rows) + 0.5], color=GRID, lw=1.2)
    ax.set_title('The sheet filled in for this page\'s job, every number measured before '
                 'any training', fontsize=12.5, weight='bold')
    print('[s6] the sheet: ' + ' | '.join(f'{a}: {b}' for a, b in rows))
    _save(fig, 'the-sheet-filled-in.svg')


# --------------------------------------------------------------------------

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    s1_written_rule_works()
    s1_written_rule_fails()
    s1_conditions_needed()
    s1_rule_that_changed()
    s2_input_output()
    s2_vague_becomes_measurable()
    s2_wrong_one_number()
    s2_how_many_trials()
    s3_three_baselines()
    s3_force_baselines()
    s3_baseline_moves()
    s3_per_class()
    s4_enough_to_cover()
    s4_looking_finds_it()
    s4_what_faults_cost()
    s4_labellers_disagree()
    s5_three_splits()
    s5_trays_differ()
    s5_split_written_down()
    s5_how_many_held_out()
    s6_the_gate()
    s6_best_of_k()
    s6_inflation()
    s6_sheet()
    print(f'wrote the diagrams under {IMAGES / DOC}')


if __name__ == '__main__':
    main()
