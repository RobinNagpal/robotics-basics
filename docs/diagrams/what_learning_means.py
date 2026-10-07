"""Generate the diagrams for chapter 1 of docs/05_neural-networks/.

    01_what-learning-means/01_why-not-just-write-the-rules.md
        -> images/what-learning-means/why-not-just-write-the-rules/
    01_what-learning-means/02_the-words-everyone-uses.md
        -> images/what-learning-means/the-words-everyone-uses/

Run with:  python3 what_learning_means.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints them so the two documents can quote the same values.

What is measured and what is simulated. The six wrist-sag measurements are a
made-up set of six (mass, sag) pairs chosen so that the fitted line comes out
at exactly 1.4 mm per kilogram plus 0.5 mm, which lets a reader check the
arithmetic on a calculator. Everything else that looks like sensor data is
simulated with a seeded numpy.random.default_rng: the switch trace with its
contact bounce, the joint-angle trajectory, the picture of a glass on a table,
the bent-spoon shapes, the 1,600 cup pictures described by four measured
numbers each, the reach attempts used for the reinforcement-learning curve and
the joint-angle trace with a hidden gap. The methods run on that data are
real, written in NumPy: least squares for a straight line, a threshold sweep,
logistic regression trained by gradient descent with Adam, polynomial fits of
several degrees, and small rectified-linear networks of one to five hidden
layers trained by gradient descent with Adam.
"""

import pathlib
import sys
import warnings

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

warnings.filterwarnings('ignore', message='Polyfit may be poorly conditioned')

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'what-learning-means')
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

RULES_DOC: str = 'why-not-just-write-the-rules'
WORDS_DOC: str = 'the-words-everyone-uses'

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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _box(ax: Axes, x: float, y: float, w: float, h: float, colour: str,
         alpha: float = 0.16, lw: float = 1.2) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=alpha,
                           edgecolor=colour, lw=lw, zorder=2))


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.4) -> None:
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>',
                                 mutation_scale=13, color=colour, lw=lw,
                                 shrinkA=0, shrinkB=0, zorder=5))


def _fit_line(x: Arr, y: Arr) -> tuple[float, float]:
    """Least-squares straight line: returns (slope, intercept)."""
    xm, ym = float(x.mean()), float(y.mean())
    slope = float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())
    return slope, ym - slope * xm


def _mse(pred: Arr, y: Arr) -> float:
    return float(np.mean((pred - y) ** 2))


# ==========================================================================
# PAGE 1, SECTION 1: three jobs where the rule can be written down
# ==========================================================================

def switch_count() -> None:
    """A contact switch with bounce: raw edges against edges after a wait."""
    rng = np.random.default_rng(11)
    hz = 1000
    t = np.arange(0, 2.0, 1.0 / hz)
    level = np.zeros_like(t)
    presses = [0.18, 0.47, 0.83, 1.21, 1.64]
    hold = 0.09
    for p in presses:
        level[(t >= p) & (t < p + hold)] = 1.0
        # contact bounce: a few short extra edges in the first few milliseconds
        for k in range(3):
            a = p + 0.0012 * (2 * k + 1)
            level[(t >= a) & (t < a + 0.0012)] = 0.0
    raw = int(np.sum((level[1:] > 0.5) & (level[:-1] < 0.5)))
    wait_ms = 20
    counted: list[float] = []
    last = -1.0
    for i in range(1, len(t)):
        if level[i] > 0.5 and level[i - 1] < 0.5 and (t[i] - last) * 1000 >= wait_ms:
            counted.append(float(t[i]))
            last = float(t[i])
    print(f'[switch] true presses {len(presses)}; raw rising edges counted {raw}; '
          f'edges after a {wait_ms} ms wait {len(counted)}')
    print(f'[switch] counted at t = ' + ', '.join(f'{c:.3f}s' for c in counted))

    fig, axes = plt.subplots(2, 1, figsize=(11.4, 5.6), facecolor='white',
                             gridspec_kw={'height_ratios': [2.0, 1.0]})
    ax = axes[0]
    _plain(ax)
    ax.step(t, level, where='post', color=LINK, lw=1.3)
    for c in counted:
        ax.plot([c], [1.12], marker='v', color=SLIDE, ms=9)
    ax.set_ylim(-0.15, 1.42)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['open (0)', 'closed (1)'])
    ax.set_xlabel('time (seconds), sampled 1,000 times a second', fontsize=10)
    ax.set_title(f'A switch closing 5 times gives {raw} rising edges, because the metal '
                 f'contacts bounce', fontsize=12, weight='bold', color=INK)
    ax.text(0.02, 1.26, f'green markers: the {len(counted)} closures the rule counts '
                        f'once it ignores anything within {wait_ms} ms of the last one',
            fontsize=9.5, color=SLIDE)

    ax2 = axes[1]
    _plain(ax2)
    zoom = (t >= presses[0] - 0.004) & (t <= presses[0] + 0.014)
    ax2.step(t[zoom] * 1000, level[zoom], where='post', color=LINK, lw=1.6)
    ax2.set_ylim(-0.15, 1.3)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['0', '1'])
    ax2.set_xlabel('time (milliseconds), the first press close up', fontsize=10)
    ax2.set_title(f'The same first press, magnified: 4 rising edges in 8 milliseconds',
                  fontsize=10.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'switch-count.svg')


def mm_to_m() -> None:
    """Converting millimetres to metres: one line of arithmetic, no error."""
    rng = np.random.default_rng(2)
    shown = np.array([0.0, 12.5, 125.0, 420.0, 700.0, 1250.0, 1830.0])
    out = shown / 1000.0
    probe = rng.uniform(0.0, 5000.0, 1_000_000)
    back = (probe / 1000.0) * 1000.0
    worst = float(np.max(np.abs(back - probe)))
    print('[mm] pairs: ' + ', '.join(f'{a:.1f}mm->{b:.4f}m' for a, b in zip(shown, out)))
    print(f'[mm] largest round-trip error over 1,000,000 random lengths: {worst:.2e} mm')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.35, 1.0]})
    ax = axes[0]
    _plain(ax)
    grid = np.linspace(0, 2000, 400)
    ax.plot(grid, grid / 1000.0, color=LINK, lw=2.0)
    ax.scatter(shown, out, s=44, color=GRIP, zorder=5)
    ax.set_xlabel('length as the sensor reports it (millimetres)', fontsize=10)
    ax.set_ylabel('length in metres', fontsize=10)
    ax.set_title('Every answer sits exactly on the line', fontsize=11.2,
                 weight='bold', color=INK)

    ax2 = axes[1]
    _blank(ax2)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.text(0.02, 0.95, 'millimetres', fontsize=10.5, weight='bold', color=INK)
    ax2.text(0.55, 0.95, 'metres', fontsize=10.5, weight='bold', color=INK)
    for i, (a, b) in enumerate(zip(shown, out)):
        yy = 0.86 - 0.105 * i
        ax2.text(0.02, yy, f'{a:,.1f}', fontsize=10, color=INK, family='monospace')
        _arrow(ax2, 0.34, yy + 0.015, 0.52, yy + 0.015, colour=MUTED, lw=1.0)
        ax2.text(0.55, yy, f'{b:.4f}', fontsize=10, color=LINK, family='monospace')
    ax2.set_title('Seven lengths and their answers', fontsize=11.2, weight='bold',
                  color=INK)
    ax2.text(0.02, 0.055, f'over 1,000,000 random lengths the largest\nerror '
                          f'anywhere was {worst:.1e} mm',
             fontsize=10, color=SLIDE)
    fig.suptitle('metres = millimetres / 1000, and that is the whole rule',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'millimetres-to-metres.svg')


def joint_limit() -> None:
    """Checking a commanded joint angle against its two limits."""
    rng = np.random.default_rng(5)
    t = np.arange(0, 4.0, 0.004)
    angle = (120 * np.sin(2 * np.pi * 0.35 * t)
             + 62 * np.sin(2 * np.pi * 0.11 * t + 0.7)
             + rng.normal(0, 0.6, len(t)))
    lo, hi = -170.0, 170.0
    outside = (angle > hi) | (angle < lo)
    n_out = int(outside.sum())
    worst = float(np.max(np.maximum(angle - hi, lo - angle)))
    first = float(t[np.argmax(outside)]) if n_out else float('nan')
    print(f'[limit] {len(t)} samples, {n_out} outside the band [-170, 170] degrees '
          f'({100.0 * n_out / len(t):.2f} per cent)')
    print(f'[limit] worst overshoot {worst:.1f} degrees, first refusal at t = {first:.3f}s')

    fig, ax = plt.subplots(figsize=(11.4, 5.0), facecolor='white')
    _plain(ax)
    ax.axhspan(lo, hi, color='#eef4ea', zorder=0)
    ax.axhline(hi, color=GRIP, lw=1.3, ls='--')
    ax.axhline(lo, color=GRIP, lw=1.3, ls='--')
    ax.plot(t, angle, color=LINK, lw=1.2, zorder=3)
    ax.scatter(t[outside], angle[outside], s=7, color=GRIP, zorder=4)
    ax.text(3.95, hi + 9, 'upper limit +170 deg', fontsize=9.5, color=GRIP, ha='right')
    ax.text(3.95, lo - 24, 'lower limit -170 deg', fontsize=9.5, color=GRIP, ha='right')
    ax.text(2.0, -128, 'the shaded band is inside the limits, where the command is sent',
            fontsize=10, color=SLIDE, ha='center')
    ax.annotate(f'{n_out} of {len(t)} samples refused,\nworst by {worst:.1f} deg',
                xy=(float(t[np.argmax(angle)]), float(np.max(angle))),
                xytext=(1.55, 232), fontsize=9.5, color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.1})
    ax.set_ylim(-250, 268)
    ax.set_xlabel('time (seconds), one check every 4 milliseconds', fontsize=10)
    ax.set_ylabel('commanded joint angle (degrees)', fontsize=10)
    ax.set_title('The rule is one comparison per sample, and it is right every time',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'joint-limit-check.svg')


# ==========================================================================
# PAGE 1, SECTION 2: three jobs where the rule cannot be written down
# ==========================================================================

def _glass_picture() -> tuple[Arr, NDArray[np.bool_]]:
    """A simulated grey picture of a glass standing on a table, and the true mask."""
    rng = np.random.default_rng(23)
    rows, cols = 18, 26
    pic = 122 + rng.normal(0, 5.0, (rows, cols))
    truth = np.zeros((rows, cols), dtype=bool)
    for r in range(rows):
        for c in range(cols):
            if 3 <= r <= 15 and 9 <= c <= 17:
                truth[r, c] = True
    # the glass is see-through, so inside it the table shows through almost unchanged
    pic[truth] = pic[truth] * 0.97 + rng.normal(0, 4.0, int(truth.sum()))
    # bright highlights down the two sides of the glass, and a darker base
    for r in range(3, 16):
        pic[r, 9] = 212 + rng.normal(0, 6)
        pic[r, 17] = 205 + rng.normal(0, 6)
    pic[15, 9:18] = 74 + rng.normal(0, 5, 9)
    pic[3, 9:18] = 188 + rng.normal(0, 6, 9)
    return np.clip(pic, 0, 255), truth


def glass_pixels() -> None:
    """Which pixels belong to the glass: the best brightness rule against the truth."""
    pic, truth = _glass_picture()
    best = (-1.0, 0, '')
    for th in range(0, 256):
        for direction in ('above', 'below'):
            guess = pic > th if direction == 'above' else pic < th
            acc = float((guess == truth).mean())
            if acc > best[0]:
                best = (acc, th, direction)
    acc, th, direction = best
    guess = pic > th if direction == 'above' else pic < th
    wrong = int((guess != truth).sum())
    missed = int((truth & ~guess).sum())
    extra = int((~truth & guess).sum())
    all_bg = float((~truth).mean())
    print(f'[glass] picture {pic.shape[0]}x{pic.shape[1]} = {pic.size} pixels, '
          f'{int(truth.sum())} of them glass')
    print(f'[glass] best single brightness rule: {direction} {th}, '
          f'accuracy {acc:.3f}, {wrong} pixels wrong '
          f'({missed} glass pixels missed, {extra} table pixels claimed)')
    print(f'[glass] saying "no glass anywhere" already scores {all_bg:.3f}')

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.4), facecolor='white')
    for ax, data, title, cmap in (
            (axes[0], pic, 'The picture the camera gives (brightness 0 to 255)', 'gray'),
            (axes[1], truth.astype(float), 'What a person says is glass', 'Greens'),
            (axes[2], guess.astype(float),
             f'Best possible single brightness rule: {direction} {th}', 'Oranges')):
        _blank(ax)
        ax.imshow(data, cmap=cmap, vmin=0, vmax=255 if cmap == 'gray' else 1.4,
                  interpolation='nearest')
        ax.set_title(title, fontsize=10.5, weight='bold', color=INK)
    axes[1].text(12.5, 19.6, f'{int(truth.sum())} glass pixels', fontsize=9.5,
                 color=SLIDE, ha='center')
    axes[2].text(12.5, 19.6, f'{wrong} of {pic.size} pixels wrong '
                             f'(accuracy {acc:.2f})', fontsize=9.5, color=GRIP,
                 ha='center')
    fig.suptitle('A glass is see-through, so the table behind it has the same '
                 'brightness as the glass', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'glass-pixels.svg')


def threshold_sweep() -> None:
    """Every brightness threshold tried in turn, so no better rule is hiding."""
    pic, truth = _glass_picture()
    ths = np.arange(0, 256)
    above = np.array([float(((pic > t) == truth).mean()) for t in ths])
    below = np.array([float(((pic < t) == truth).mean()) for t in ths])
    all_bg = float((~truth).mean())
    bi, bv = int(np.argmax(above)), float(above.max())
    ci, cv = int(np.argmax(below)), float(below.max())
    print(f'[sweep] best "brighter than" rule: {bi} -> {bv:.3f}; '
          f'best "darker than" rule: {ci} -> {cv:.3f}; '
          f'always-table baseline {all_bg:.3f}')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(ths, above, color=LINK, lw=2.0, label='rule: "glass where brighter than t"')
    ax.plot(ths, below, color=PURPLE, lw=2.0, label='rule: "glass where darker than t"')
    ax.axhline(all_bg, color=MUTED, ls='--', lw=1.2)
    ax.text(5, all_bg - 0.105, f'the dashed line is what saying "no glass anywhere"\n'
                               f'already scores: {all_bg:.3f}',
            fontsize=9.5, color=MUTED)
    ax.scatter([bi], [bv], s=55, color=GRIP, zorder=6)
    ax.annotate(f'best of all 512 rules: t = {bi}, accuracy {bv:.3f}',
                xy=(bi, bv), xytext=(bi - 120, bv + 0.055), fontsize=10, color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.1})
    ax.set_xlim(0, 255)
    ax.set_ylim(0.0, 0.92)
    ax.set_xlabel('the threshold t the rule compares each pixel against', fontsize=10)
    ax.set_ylabel('fraction of pixels the rule gets right', fontsize=10)
    ax.set_title('No brightness threshold finds the glass, because every one of the '
                 '512 was tried', fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, RULES_DOC, 'threshold-sweep.svg')


def _spoon(bend: float) -> tuple[Arr, Arr, Arr]:
    """Centre line and half-width of a spoon, in millimetres along its length."""
    x = np.linspace(0, 186, 373)
    centre = bend * np.sin(np.pi * x / 180.0)
    bowl = 17.0 / (1.0 + np.exp(-(x - 124.0) / 5.0))
    taper = np.clip((188.0 - x) / 22.0, 0.0, 1.0)
    half = 4.5 + bowl * taper
    return x, centre, half


def spoon_finger_places() -> None:
    """Where to put the fingers on a bent spoon: a hand rule that works, then fails."""
    open_lo, open_hi = 4.0, 30.0
    slope_max = 0.25
    clear_mm = 15.0
    bowl_start = 110.0
    rows = []
    for bend, name in ((6.0, 'gently bent spoon'), (26.0, 'sharply bent spoon')):
        x, centre, half = _spoon(bend)
        slope = np.gradient(centre, x)
        for spot in (20.0, 60.0, 95.0, 140.0, 170.0):
            i = int(np.argmin(np.abs(x - spot)))
            width = 2 * float(half[i])
            sl = float(slope[i])
            ok_w = open_lo <= width <= open_hi
            ok_s = abs(sl) <= slope_max
            ok_c = spot <= bowl_start - clear_mm
            rows.append((name, bend, spot, width, sl, ok_w, ok_s, ok_c,
                         ok_w and ok_s and ok_c))
    for r in rows:
        print(f'[spoon] {r[0]:21s} at {r[2]:5.0f} mm: width {r[3]:5.1f} mm, '
              f'slope {r[4]:+.3f}, width ok {r[5]}, flat ok {r[6]}, clear ok {r[7]} '
              f'-> rule says {"GRIP" if r[8] else "no"}')
    passed = {n: [r[2] for r in rows if r[0] == n and r[8]]
              for n in ('gently bent spoon', 'sharply bent spoon')}
    print(f'[spoon] rule accepts {passed}')

    fig, axes = plt.subplots(2, 1, figsize=(11.6, 6.6), facecolor='white')
    for ax, (bend, name) in zip(axes, ((6.0, 'gently bent spoon'),
                                      (26.0, 'sharply bent spoon'))):
        _plain(ax)
        x, centre, half = _spoon(bend)
        ax.fill_between(x, centre - half, centre + half, color=LINK_PALE,
                        edgecolor=LINK, lw=1.3)
        mine = [r for r in rows if r[0] == name]
        for _n, _b, spot, width, sl, ok_w, ok_s, ok_c, ok in mine:
            colour = SLIDE if ok else GRIP
            i = int(np.argmin(np.abs(x - spot)))
            ax.plot([spot, spot], [centre[i] - half[i] - 7, centre[i] - half[i] - 2],
                    color=colour, lw=3.4, solid_capstyle='butt')
            ax.plot([spot, spot], [centre[i] + half[i] + 2, centre[i] + half[i] + 7],
                    color=colour, lw=3.4, solid_capstyle='butt')
            ax.text(spot, centre[i] + half[i] + 10,
                    f'{width:.0f} mm\nslope {sl:+.2f}', fontsize=8.6, color=colour,
                    ha='center', va='bottom')
        ax.axvline(bowl_start, color=MUTED, ls=':', lw=1.1)
        ax.text(bowl_start + 2, -36, 'bowl starts', fontsize=9, color=MUTED)
        ax.set_xlim(-6, 192)
        ax.set_ylim(-44, 58)
        ax.set_aspect('equal')
        ax.set_yticks([])
        ax.set_xlabel('distance along the spoon (millimetres)', fontsize=9.5)
        ax.set_title(f'{name[0].upper()}{name[1:]}: the rule accepts '
                     f'{len(passed[name])} of the 5 places, at '
                     + ', '.join(f'{p:.0f} mm' for p in passed[name]),
                     fontsize=10.8, weight='bold', color=INK)
    fig.suptitle(f'One hand-written grip rule: width between {open_lo:.0f} and '
                 f'{open_hi:.0f} mm, slope under {slope_max:.2f}, at least '
                 f'{clear_mm:.0f} mm clear of the bowl',
                 fontsize=12, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'spoon-finger-places.svg')


class Cups:
    """1,600 simulated cup pictures, each described by four measured numbers.

    Each cup has its own colour and its own lighting, which both change the
    brightness far more than the coffee in it does. The four numbers are the
    average brightness inside the rim, the spread of that brightness, the
    average brightness of the cup wall, and nothing else.
    """

    def __init__(self, n: int = 1600, seed: int = 31) -> None:
        rng = np.random.default_rng(seed)
        self.full = rng.integers(0, 2, n).astype(float)
        colour = rng.uniform(90, 180, n)
        light = rng.uniform(0.8, 1.2, n)
        base = colour * light
        self.inside = base + np.where(self.full > 0.5, -18.0, 4.0) + rng.normal(0, 8, n)
        self.spread = np.where(self.full > 0.5, 9.0, 4.0) + rng.normal(0, 2.2, n)
        self.wall = base + rng.normal(0, 6, n)
        self.diff = self.inside - self.wall
        self.n = n
        self.split = n // 2

    def features(self, which: str) -> Arr:
        cols = {'inside': self.inside, 'spread': self.spread, 'wall': self.wall,
                'diff': self.diff}
        return cols[which]

    def best_threshold(self, which: str) -> tuple[float, float]:
        """Best single threshold on one of the measured numbers, and its accuracy."""
        v = self.features(which)[:self.split]
        y = self.full[:self.split]
        cuts = np.quantile(v, np.linspace(0.005, 0.995, 400))
        best_acc, best_cut, best_sign = 0.0, 0.0, 1.0
        for c in cuts:
            for sign in (1.0, -1.0):
                acc = float((((v - c) * sign > 0).astype(float) == y).mean())
                if acc > best_acc:
                    best_acc, best_cut, best_sign = acc, float(c), sign
        vt = self.features(which)[self.split:]
        yt = self.full[self.split:]
        held = float((((vt - best_cut) * best_sign > 0).astype(float) == yt).mean())
        return best_acc, held


CUPS: Cups | None = None


def _cups() -> Cups:
    global CUPS
    if CUPS is None:
        CUPS = Cups()
    return CUPS


def _logistic_fit(X: Arr, y: Arr, steps: int = 600, lr: float = 0.08
                  ) -> tuple[Arr, float, list[float]]:
    """Logistic regression by gradient descent with Adam. Returns weights, bias, loss."""
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    mw, vw = np.zeros(d), np.zeros(d)
    mb, vb = 0.0, 0.0
    hist: list[float] = []
    for it in range(1, steps + 1):
        z = X @ w + b
        p = 1.0 / (1.0 + np.exp(-z))
        loss = float(-np.mean(y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9)))
        hist.append(loss)
        g = (p - y) / n
        gw = X.T @ g
        gb = float(g.sum())
        mw = 0.9 * mw + 0.1 * gw
        vw = 0.999 * vw + 0.001 * gw ** 2
        mb = 0.9 * mb + 0.1 * gb
        vb = 0.999 * vb + 0.001 * gb ** 2
        w = w - lr * (mw / (1 - 0.9 ** it)) / (np.sqrt(vw / (1 - 0.999 ** it)) + 1e-8)
        b = b - lr * (mb / (1 - 0.9 ** it)) / (np.sqrt(vb / (1 - 0.999 ** it)) + 1e-8)
    return w, b, hist


def _cup_model(steps: int = 400) -> dict[str, object]:
    """Fit a three-number cup model on half the cups and test it on the other half."""
    c = _cups()
    cols = np.stack([c.inside, c.spread, c.wall], axis=1)
    mu = cols[:c.split].mean(0)
    sd = cols[:c.split].std(0)
    Xtr = (cols[:c.split] - mu) / sd
    Xte = (cols[c.split:] - mu) / sd
    ytr, yte = c.full[:c.split], c.full[c.split:]
    w, b, hist = _logistic_fit(Xtr, ytr, steps=steps)
    ptr = 1.0 / (1.0 + np.exp(-(Xtr @ w + b)))
    pte = 1.0 / (1.0 + np.exp(-(Xte @ w + b)))
    return {'w': w, 'b': b, 'hist': hist, 'mu': mu, 'sd': sd,
            'acc_train': float(((ptr > 0.5).astype(float) == ytr).mean()),
            'acc_test': float(((pte > 0.5).astype(float) == yte).mean()),
            'Xtr': Xtr, 'ytr': ytr, 'Xte': Xte, 'yte': yte, 'pte': pte}


def full_or_empty_cup() -> None:
    """The brightness inside the rim overlaps completely between full and empty cups."""
    c = _cups()
    acc_in, held_in = c.best_threshold('inside')
    full = c.inside[c.full > 0.5]
    empty = c.inside[c.full < 0.5]
    print(f'[cup] {c.n} simulated cups, {int(c.full.sum())} full, '
          f'{int(c.n - c.full.sum())} empty')
    print(f'[cup] brightness inside the rim: full average {full.mean():.1f}, '
          f'empty average {empty.mean():.1f}, full range {full.min():.0f}-'
          f'{full.max():.0f}, empty range {empty.min():.0f}-{empty.max():.0f}')
    print(f'[cup] best single threshold on that one number: {acc_in:.3f} on the cups '
          f'it was chosen on, {held_in:.3f} on cups it had not seen')

    fig, ax = plt.subplots(figsize=(10.8, 5.2), facecolor='white')
    _plain(ax)
    bins = np.linspace(50, 230, 37)
    ax.hist(empty, bins=bins, color=LINK, alpha=0.62, label='empty cups')
    ax.hist(full, bins=bins, color=GRIP, alpha=0.62, label='full cups')
    ax.set_xlabel('average brightness inside the rim (0 to 255)', fontsize=10.5)
    ax.set_ylabel('number of cups', fontsize=10.5)
    ax.set_title(f'The two piles of cups sit on top of each other, so the best '
                 f'threshold gets only {held_in:.2f}',
                 fontsize=11.8, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False)
    _save(fig, RULES_DOC, 'full-or-empty-cup.svg')


def two_numbers_separate_cups() -> None:
    """The same cups separate once the brightness of the wall is known as well."""
    c = _cups()
    below = float(((c.inside < c.wall) == (c.full > 0.5)).mean())
    print(f'[cup2] with both numbers known, "inside darker than the wall" is right on '
          f'{below:.3f} of all {c.n} cups')

    fig, ax = plt.subplots(figsize=(10.0, 5.6), facecolor='white')
    _plain(ax)
    sub = slice(0, 400)
    ax.scatter(c.wall[sub][c.full[sub] < 0.5], c.inside[sub][c.full[sub] < 0.5],
               s=14, color=LINK, alpha=0.7, label='empty cups')
    ax.scatter(c.wall[sub][c.full[sub] > 0.5], c.inside[sub][c.full[sub] > 0.5],
               s=14, color=GRIP, alpha=0.7, label='full cups')
    lim = np.array([60, 225])
    ax.plot(lim, lim, color=MUTED, ls='--', lw=1.3)
    ax.text(214, 206, 'inside = wall', fontsize=9.6, color=MUTED, rotation=38,
            ha='right', va='bottom')
    ax.set_xlabel('average brightness of the cup wall (0 to 255)', fontsize=10.5)
    ax.set_ylabel('average brightness inside the rim (0 to 255)', fontsize=10.5)
    ax.set_title('Full cups sit below the dashed line and empty ones above, so two '
                 'numbers separate what one could not',
                 fontsize=11.4, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='lower right')
    _save(fig, RULES_DOC, 'two-numbers-separate-cups.svg')


# ==========================================================================
# PAGE 1, SECTION 3: what the difference between the two lists is
# ==========================================================================

def how_many_pictures() -> None:
    """The number of different inputs a rule would have to cover."""
    cases = [
        ('a switch:\nopen or closed', 2),
        ('a joint angle,\n0.1 deg steps\nover 340 deg', 3401),
        ('a 5 by 5 grey patch,\n256 brightnesses', 256 ** 25),
        ('the 18 by 26 picture\nabove, 256 brightnesses', 256 ** (18 * 26)),
    ]
    year = 60 * 60 * 24 * 365 * 30     # 30 pictures a second for a year
    logs = [float(np.log10(float(n))) if n < 1e300
            else float(len(str(n)) - 1 + np.log10(float(str(n)[:15]) / 10 ** 14))
            for _l, n in cases]
    shown = [f'{n:,}' if n < 1e6 else f'10^{lg:.0f}' for (_l, n), lg in zip(cases, logs)]
    for (lab, n), lg, sh in zip(cases, logs, shown):
        short = lab.replace('\n', ' ')
        print(f'[count] {short:48s} different inputs: {sh} (10^{lg:.2f})')
    print(f'[count] a camera at 30 pictures a second for a year sees {year:,} '
          f'pictures, which is 10^{np.log10(year):.1f}')

    fig, ax = plt.subplots(figsize=(11.2, 5.2), facecolor='white')
    _plain(ax)
    names = [c[0] for c in cases]
    bars = ax.bar(range(4), logs, color=[SLIDE, SLIDE, GRIP, GRIP], alpha=0.85,
                  edgecolor=INK, lw=0.62, width=0.62)
    for i, sh in enumerate(shown):
        ax.text(i, logs[i] + 60, sh, ha='center', fontsize=11, weight='bold',
                color=INK)
    ax.axhline(float(np.log10(year)), color=LINK, lw=1.6, ls='--')
    ax.text(-0.42, 420,
            f'the dashed line near the bottom is everything a camera\n'
            f'sees in a year at 30 pictures a second: 10^{np.log10(year):.1f} pictures',
            fontsize=9.8, color=LINK, ha='left')
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylabel('how many different inputs there are (powers of ten)', fontsize=10)
    ax.set_ylim(0, max(logs) * 1.14)
    ax.set_title('A rule for the first two jobs can list every case; a rule for a '
                 'picture never can', fontsize=12, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'how-many-pictures.svg')


def rules_stack_up() -> None:
    """Adding hand-written conditions one at a time, against fitting the same numbers."""
    c = _cups()
    names = ['brightness\ninside the rim', 'spread of that\nbrightness',
             'brightness of\nthe cup wall', 'inside minus wall\n(a person works it out)']
    keys = ['inside', 'spread', 'wall', 'diff']
    held = []
    for k in keys:
        _a, h = c.best_threshold(k)
        held.append(h)
    m = _cup_model()
    fitted = float(m['acc_test'])
    w = np.asarray(m['w'])
    print('[stack] best single threshold, measured on cups it had not seen:')
    for k, h in zip(keys, held):
        print(f'[stack]   {k:8s} {h:.3f}')
    print(f'[stack] a fitted model given the first three numbers: {fitted:.3f}')
    print(f'[stack] its three weights: inside {w[0]:+.2f}, spread {w[1]:+.2f}, '
          f'wall {w[2]:+.2f}')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _plain(ax)
    vals = held + [fitted]
    labs = names + ['a fitted model, given\nthe first three numbers']
    cols = [GRIP, JOINT, GRIP, SLIDE, LINK]
    bars = ax.bar(range(5), vals, color=cols, alpha=0.85, edgecolor=INK, lw=0.6,
                  width=0.6)
    for i, v in zip(range(5), vals):
        ax.text(i, v + 0.013, f'{v:.3f}', ha='center', fontsize=11, weight='bold',
                color=INK)
    ax.axhline(0.5, color=MUTED, ls='--', lw=1.2)
    ax.text(-0.42, 1.015, 'the dashed line at 0.5 is what tossing a coin scores',
            fontsize=9.5, color=MUTED, ha='left', va='top')
    ax.set_xticks(range(5))
    ax.set_xticklabels(labs, fontsize=9.3)
    ax.set_ylim(0.4, 1.04)
    ax.set_ylabel('fraction of unseen cups called right', fontsize=10)
    ax.set_title(f'The rule only works once a person has found the right combination, '
                 f'and then fitting finds it anyway ({fitted:.3f})',
                 fontsize=11.8, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'rules-stack-up.svg')


def one_answer_per_input() -> None:
    """Where a rule works, each input value has exactly one right answer."""
    mm = np.linspace(0, 1800, 25)
    print('[kinds] the millimetre job: each input value has exactly one answer, and '
          'the answers lie on one line')

    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(mm, mm / 1000.0, color=SLIDE, lw=1.6, alpha=0.6)
    ax.scatter(mm, mm / 1000.0, s=40, color=SLIDE, zorder=4)
    ax.plot([1250, 1250], [0, 1.25], color=MUTED, ls=':', lw=1.2)
    ax.plot([0, 1250], [1.25, 1.25], color=MUTED, ls=':', lw=1.2)
    ax.annotate('1,250 mm has one answer, 1.250 m,\nand never any other',
                xy=(1250, 1.25), xytext=(170, 1.46), fontsize=10, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.1})
    ax.set_xlabel('the one input: length in millimetres', fontsize=10.5)
    ax.set_ylabel('the answer: length in metres', fontsize=10.5)
    ax.set_ylim(-0.05, 1.95)
    ax.set_title('Where a rule can be written, one input value gives one answer',
                 fontsize=11.8, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'one-answer-per-input.svg')


def both_answers_at_one_input() -> None:
    """Where no rule works, the same input value happens with both answers."""
    c = _cups()
    overlap_lo = max(c.inside[c.full > 0.5].min(), c.inside[c.full < 0.5].min())
    overlap_hi = min(c.inside[c.full > 0.5].max(), c.inside[c.full < 0.5].max())
    share = float(((c.inside >= overlap_lo) & (c.inside <= overlap_hi)).mean())
    print(f'[kinds] the two kinds of cup share the brightness range '
          f'{overlap_lo:.0f} to {overlap_hi:.0f}, which holds {share:.3f} '
          f'of all the cups')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plain(ax)
    sub = slice(0, 500)
    jit = np.random.default_rng(7).normal(0, 0.03, 500)
    ax.scatter(c.inside[sub], c.full[sub] + jit, s=12,
               color=[GRIP if f > 0.5 else LINK for f in c.full[sub]], alpha=0.6)
    ax.axvspan(overlap_lo, overlap_hi, color='#f6e6e6', zorder=0)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['empty', 'full'])
    ax.set_ylim(-0.42, 1.52)
    ax.set_xlabel('the one input: average brightness inside the rim (0 to 255)',
                  fontsize=10.5)
    ax.annotate(f'both answers appear everywhere in the shaded range, '
                f'{overlap_lo:.0f} to {overlap_hi:.0f}',
                xy=((overlap_lo + overlap_hi) / 2, 1.28), fontsize=10, color=GRIP,
                ha='center', va='center')
    ax.set_title('Where no rule can be written, one input value gives both answers',
                 fontsize=11.8, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'both-answers-at-one-input.svg')


# ==========================================================================
# PAGE 1, SECTION 4: the worked example
# ==========================================================================

SAG_X: Arr = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
SAG_Y: Arr = np.array([0.7, 0.9, 1.8, 2.7, 3.6, 3.8])
HAND_SLOPE: float = 1.0
HAND_INTERCEPT: float = 0.0


def _sag_numbers() -> dict[str, float]:
    slope, intercept = _fit_line(SAG_X, SAG_Y)
    fitted = slope * SAG_X + intercept
    hand = HAND_SLOPE * SAG_X + HAND_INTERCEPT
    mean_only = np.full_like(SAG_Y, SAG_Y.mean())
    return {'slope': slope, 'intercept': intercept,
            'mse_fit': _mse(fitted, SAG_Y), 'mse_hand': _mse(hand, SAG_Y),
            'mse_mean': _mse(mean_only, SAG_Y),
            'sse_fit': float(((fitted - SAG_Y) ** 2).sum()),
            'sse_hand': float(((hand - SAG_Y) ** 2).sum()),
            'sse_mean': float(((mean_only - SAG_Y) ** 2).sum()),
            'xbar': float(SAG_X.mean()), 'ybar': float(SAG_Y.mean())}


def sag_points() -> None:
    """The six measurements, a hand-written rule and the fitted line."""
    s = _sag_numbers()
    slope, intercept = s['slope'], s['intercept']
    fitted = slope * SAG_X + intercept
    hand = HAND_SLOPE * SAG_X + HAND_INTERCEPT
    print(f'[sag] six pairs: ' + ', '.join(f'({a:.1f} kg, {b:.1f} mm)'
                                          for a, b in zip(SAG_X, SAG_Y)))
    print(f'[sag] fitted line: sag = {slope:.4f} * mass + {intercept:.4f}')
    print(f'[sag] fitted predictions: ' + ', '.join(f'{v:.2f}' for v in fitted))
    print(f'[sag] fitted misses:      ' + ', '.join(f'{v:+.2f}' for v in SAG_Y - fitted))
    print(f'[sag] hand rule (1 mm per kg) misses: '
          + ', '.join(f'{v:+.2f}' for v in SAG_Y - hand))
    print(f'[sag] total squared error: hand {s["sse_hand"]:.3f}, '
          f'fitted {s["sse_fit"]:.3f}; average squared error: hand '
          f'{s["mse_hand"]:.4f}, fitted {s["mse_fit"]:.4f}')
    print(f'[sag] typical miss: hand {np.sqrt(s["mse_hand"]):.3f} mm, '
          f'fitted {np.sqrt(s["mse_fit"]):.3f} mm, '
          f'which is {s["mse_hand"] / s["mse_fit"]:.1f} times smaller in squared error')

    fig, ax = plt.subplots(figsize=(10.8, 5.8), facecolor='white')
    _plain(ax)
    grid = np.linspace(-0.1, 2.75, 100)
    ax.plot(grid, HAND_SLOPE * grid + HAND_INTERCEPT, color=GRIP, lw=1.8, ls='--',
            label=f'hand-written rule: sag = 1.0 x mass')
    ax.plot(grid, slope * grid + intercept, color=LINK, lw=2.2,
            label=f'fitted line: sag = {slope:.1f} x mass + {intercept:.1f}')
    for xv, yv, fv in zip(SAG_X, SAG_Y, fitted):
        ax.plot([xv, xv], [yv, fv], color=LINK, lw=1.4, alpha=0.75)
        ax.annotate(f'misses by {yv - fv:+.1f}', (xv, (yv + fv) / 2), fontsize=9,
                    color=LINK, textcoords='offset points', xytext=(8, -3))
    ax.scatter(SAG_X, SAG_Y, s=62, color=INK, zorder=6, label='six measurements')
    for xv, yv in zip(SAG_X, SAG_Y):
        ax.annotate(f'({xv:.1f}, {yv:.1f})', (xv, yv), fontsize=9, color=INK,
                    ha='right', va='center', textcoords='offset points',
                    xytext=(-10, 0))
    ax.set_xlim(-0.62, 2.95)
    ax.set_ylim(-0.2, 4.6)
    ax.set_xlabel('mass hung on the wrist (kilograms)', fontsize=10.5)
    ax.set_ylabel('how far the tool tip drops (millimetres)', fontsize=10.5)
    ax.set_title(f'Six measurements, and the line that misses them by the least: '
                 f'{slope:.1f} mm per kg plus {intercept:.1f} mm',
                 fontsize=12, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='upper left')
    _save(fig, RULES_DOC, 'sag-points.svg')


def fit_arithmetic() -> None:
    """The calculator steps that turn six pairs into a slope and an intercept."""
    s = _sag_numbers()
    xbar, ybar = s['xbar'], s['ybar']
    dx = SAG_X - xbar
    dy = SAG_Y - ybar
    prod = dx * dy
    sq = dx ** 2
    print(f'[arith] average mass {xbar:.2f} kg, average sag {ybar:.2f} mm')
    print(f'[arith] sum of (mass - average) x (sag - average) = {prod.sum():.4f}')
    print(f'[arith] sum of (mass - average) squared          = {sq.sum():.4f}')
    print(f'[arith] slope = {prod.sum():.4f} / {sq.sum():.4f} = {s["slope"]:.4f}')
    print(f'[arith] intercept = {ybar:.2f} - {s["slope"]:.4f} x {xbar:.2f} = '
          f'{s["intercept"]:.4f}')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    heads = ['mass\n(kg)', 'sag\n(mm)', 'mass - 1.25', 'sag - 2.25',
             'the two\nmultiplied', '(mass - 1.25)\nsquared']
    xs = [0.07, 0.21, 0.37, 0.53, 0.70, 0.88]
    for xx, hh in zip(xs, heads):
        ax.text(xx, 0.90, hh, fontsize=10, weight='bold', color=INK, ha='center',
                va='bottom')
    ax.plot([0.02, 0.96], [0.875, 0.875], color=INK, lw=1.1)
    for i in range(6):
        yy = 0.80 - 0.093 * i
        vals = [f'{SAG_X[i]:.1f}', f'{SAG_Y[i]:.1f}', f'{dx[i]:+.2f}', f'{dy[i]:+.2f}',
                f'{prod[i]:+.4f}', f'{sq[i]:.4f}']
        cols = [INK, INK, MUTED, MUTED, LINK, PURPLE]
        for xx, vv, cc in zip(xs, vals, cols):
            ax.text(xx, yy, vv, fontsize=10.5, color=cc, ha='center',
                    family='monospace')
    ax.plot([0.60, 0.96], [0.215, 0.215], color=INK, lw=1.1)
    ax.text(0.70, 0.16, f'{prod.sum():+.4f}', fontsize=11.5, color=LINK, ha='center',
            weight='bold', family='monospace')
    ax.text(0.88, 0.16, f'{sq.sum():.4f}', fontsize=11.5, color=PURPLE, ha='center',
            weight='bold', family='monospace')
    ax.text(0.52, 0.16, 'totals', fontsize=10.5, color=INK, ha='right')
    _box(ax, 0.04, 0.015, 0.90, 0.105, LINK, alpha=0.09)
    ax.text(0.49, 0.065,
            f'slope = {prod.sum():.4f} / {sq.sum():.4f} = {s["slope"]:.1f} mm per kg      '
            f'intercept = {ybar:.2f} - {s["slope"]:.1f} x {xbar:.2f} = '
            f'{s["intercept"]:.1f} mm',
            fontsize=11.5, color=INK, ha='center', va='center', weight='bold')
    ax.set_title('The whole fit is six subtractions, six multiplications, two totals '
                 'and one division', fontsize=12.2, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'fit-arithmetic.svg')


def error_vs_slope() -> None:
    """Total squared error against the slope, with the intercept held at 0.5."""
    s = _sag_numbers()
    slopes = np.linspace(0.2, 2.6, 241)
    err = np.array([float((((m * SAG_X + s['intercept']) - SAG_Y) ** 2).sum())
                    for m in slopes])
    i = int(np.argmin(err))
    hand_err = float((((HAND_SLOPE * SAG_X + s['intercept']) - SAG_Y) ** 2).sum())
    print(f'[curve] lowest total squared error {err[i]:.4f} at slope '
          f'{slopes[i]:.2f} (the exact best is {s["slope"]:.4f}, '
          f'error {s["sse_fit"]:.4f})')
    print(f'[curve] at slope 1.0 with the same intercept the error is {hand_err:.4f}, '
          f'which is {hand_err / s["sse_fit"]:.0f} times larger')
    print(f'[curve] at slope 2.0 the error is '
          f'{float((((2.0 * SAG_X + s["intercept"]) - SAG_Y) ** 2).sum()):.4f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(slopes, err, color=LINK, lw=2.2)
    ax.scatter([s['slope']], [s['sse_fit']], s=70, color=SLIDE, zorder=6)
    ax.annotate(f'best slope {s["slope"]:.1f}, error {s["sse_fit"]:.2f}',
                xy=(s['slope'], s['sse_fit']), xytext=(1.68, 7.4), fontsize=10.5,
                color=SLIDE, arrowprops={'arrowstyle': '-|>', 'color': SLIDE, 'lw': 1.2})
    ax.scatter([HAND_SLOPE], [hand_err], s=70, color=GRIP, zorder=6)
    ax.annotate(f'the hand-written 1.0, error {hand_err:.2f}',
                xy=(HAND_SLOPE, hand_err), xytext=(0.52, 10.4), fontsize=10.5,
                color=GRIP, arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    ax.set_xlabel('the slope the line is given (millimetres of sag per kilogram)',
                  fontsize=10.5)
    ax.set_ylabel('total squared miss over the six measurements', fontsize=10.5)
    ax.set_ylim(-0.6, 13.6)
    ax.set_title('Every slope was tried, and the error has one lowest point',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'error-vs-slope.svg')


def signed_misses_cancel() -> None:
    """Why the misses are squared: added as they are, they cancel each other out."""
    s = _sag_numbers()
    slope = 0.4
    offset = s['ybar'] - slope * s['xbar']
    pred = slope * SAG_X + offset
    miss = SAG_Y - pred
    signed = float(miss.sum())
    squared = float((miss ** 2).sum())
    best_signed = float((SAG_Y - (s['slope'] * SAG_X + s['intercept'])).sum())
    print(f'[cancel] a poor line, sag = {slope:.1f} x mass + {offset:.2f}, misses by '
          + ', '.join(f'{v:+.2f}' for v in miss))
    print(f'[cancel] those six misses add up to {signed:+.2f} mm, and the best line\'s '
          f'six misses add up to {best_signed:+.2f} mm as well')
    print(f'[cancel] squared, the poor line totals {squared:.3f} and the best line '
          f'{s["sse_fit"]:.3f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.6), facecolor='white')
    _plain(ax)
    grid = np.linspace(-0.1, 2.7, 60)
    ax.plot(grid, slope * grid + offset, color=GRIP, lw=2.2,
            label=f'a poor line: sag = {slope:.1f} x mass + {offset:.2f}')
    ax.scatter(SAG_X, SAG_Y, s=58, color=INK, zorder=6, label='the six measurements')
    for xv, yv, pv, mv in zip(SAG_X, SAG_Y, pred, miss):
        ax.plot([xv, xv], [yv, pv], color=GRIP, lw=1.6, alpha=0.8)
        ax.annotate(f'{mv:+.2f}', (xv, (yv + pv) / 2), fontsize=9.6, color=GRIP,
                    textcoords='offset points', xytext=(8, -2))
    ax.set_xlim(-0.25, 3.05)
    ax.set_ylim(-0.1, 4.9)
    ax.set_xlabel('mass hung on the wrist (kilograms)', fontsize=10.5)
    ax.set_ylabel('how far the tool tip drops (millimetres)', fontsize=10.5)
    ax.text(0.0, 4.6, f'the six misses add up to {signed:+.2f} mm, and so do the best '
                      f'line\'s,\nso adding them cannot tell a poor line from a good '
                      f'one',
            fontsize=10.2, color=INK, va='top')
    ax.set_title(f'Added as they are, the misses cancel; squared they total '
                 f'{squared:.2f} against the best line\'s {s["sse_fit"]:.2f}',
                 fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='lower right')
    _save(fig, RULES_DOC, 'signed-misses-cancel.svg')


def squaring_punishes_big_misses() -> None:
    """Squaring a miss makes one large miss cost more than several small ones."""
    marks = [0.5, 1.0, 2.0]
    print('[square] what one miss adds to the score: '
          + ', '.join(f'{m:.1f} mm -> {m * m:.2f}' for m in marks))
    print(f'[square] doubling a miss multiplies what it adds by '
          f'{(1.0 ** 2) / (0.5 ** 2):.0f}')

    fig, ax = plt.subplots(figsize=(9.8, 5.2), facecolor='white')
    _plain(ax)
    e = np.linspace(0, 2.4, 200)
    ax.plot(e, e ** 2, color=PURPLE, lw=2.4)
    offsets = {0.5: (-10, 30), 1.0: (14, 2), 2.0: (-14, 24)}
    for mv in marks:
        ax.plot([mv, mv], [0, mv * mv], color=MUTED, ls=':', lw=1.0)
        ax.plot([0, mv], [mv * mv, mv * mv], color=MUTED, ls=':', lw=1.0)
        ax.scatter([mv], [mv * mv], s=52, color=PURPLE, zorder=6)
        ax.annotate(f'a miss of {mv:.1f} mm\nadds {mv * mv:.2f}', (mv, mv * mv),
                    fontsize=10, color=PURPLE, textcoords='offset points',
                    xytext=offsets[mv], va='center',
                    ha='left' if mv == 1.0 else 'right')
    ax.set_xlim(0, 2.75)
    ax.set_ylim(0, 5.0)
    ax.set_xlabel('how far the line misses one measurement (millimetres)',
                  fontsize=10.5)
    ax.set_ylabel('what that one miss adds to the score\n(square millimetres)',
                  fontsize=10.5)
    ax.set_title('Twice the miss adds four times as much, so one large miss costs '
                 'more than several small ones',
                 fontsize=11.6, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'squaring-punishes-big-misses.svg')


def three_answers() -> None:
    """Three ways to answer the sag question, and what each one misses by."""
    s = _sag_numbers()
    names = ['always say the average,\n2.25 mm', 'the hand-written rule,\n1.0 mm per kg',
             f'the fitted line,\n{s["slope"]:.1f} x mass + {s["intercept"]:.1f}']
    mses = [s['mse_mean'], s['mse_hand'], s['mse_fit']]
    typical = [float(np.sqrt(v)) for v in mses]
    for n, m, t in zip(names, mses, typical):
        print(f'[three] {n.replace(chr(10), " "):48s} average squared miss {m:.4f} '
              f'mm^2, typical miss {t:.3f} mm')
    print(f'[three] the fitted line misses by {typical[1] / typical[2]:.1f} times less '
          f'than the hand-written rule')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), facecolor='white')
    for ax, vals, lab, title in (
            (axes[0], mses, 'average squared miss (square millimetres)',
             'The score the fit was chosen to make small'),
            (axes[1], typical, 'typical miss (millimetres)',
             'The same thing in millimetres you can picture')):
        _plain(ax)
        bars = ax.bar(range(3), vals, color=[MUTED, GRIP, SLIDE], alpha=0.85,
                      edgecolor=INK, lw=0.6, width=0.58)
        for i, v in enumerate(vals):
            ax.text(i, v + max(vals) * 0.025, f'{v:.3f}', ha='center', fontsize=11,
                    weight='bold', color=INK)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=9.3)
        ax.set_ylim(0, max(vals) * 1.2)
        ax.set_ylabel(lab, fontsize=10)
        ax.set_title(title, fontsize=11.2, weight='bold', color=INK)
    fig.suptitle('Fitting the two numbers to the six measurements cuts the typical '
                 f'miss from {typical[1]:.2f} mm to {typical[2]:.2f} mm',
                 fontsize=12.2, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'three-answers.svg')


# ==========================================================================
# PAGE 1, SECTION 5: the words for the pieces
# ==========================================================================

def one_example() -> None:
    """The six measurements as a table, with each word pointing at a part of it."""
    s = _sag_numbers()
    fitted = s['slope'] * SAG_X + s['intercept']
    fig, ax = plt.subplots(figsize=(12.4, 5.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    cols = [(0.055, 0.155, LINK, 'input: the feature', 'mass (kg)'),
            (0.225, 0.165, SLIDE, 'output: the label', 'measured sag (mm)'),
            (0.405, 0.185, PURPLE, 'the prediction', 'what the line says (mm)')]
    for x, w, colour, head, sub in cols:
        _box(ax, x, 0.245, w, 0.545, colour, alpha=0.11)
        ax.text(x + w / 2, 0.835, head, fontsize=10.8, weight='bold', color=colour,
                ha='center')
        ax.text(x + w / 2, 0.795, sub, fontsize=9.6, color=INK, ha='center')
    for i in range(6):
        yy = 0.735 - 0.085 * i
        for (x, w, colour, _h, _s), val in zip(
                cols, (f'{SAG_X[i]:.1f}', f'{SAG_Y[i]:.1f}', f'{fitted[i]:.1f}')):
            ax.text(x + w / 2, yy, val, fontsize=11.5, ha='center', va='center',
                    family='monospace', color=INK if colour is not PURPLE else PURPLE)
    ax.add_patch(Rectangle((0.048, 0.4575), 0.552, 0.058, facecolor='none',
                           edgecolor=GRIP, lw=2.0, zorder=7))
    _arrow(ax, 0.655, 0.4865, 0.607, 0.4865, colour=GRIP, lw=1.4)
    ax.text(0.665, 0.4865, 'one example: one input with the\nanswer that goes with it',
            fontsize=10.5, color=GRIP, ha='left', va='center')
    ax.text(0.665, 0.715, f'fitting picked the two numbers {s["slope"]:.1f} and '
                          f'{s["intercept"]:.1f}\nso that the third column would sit '
                          f'close\nto the second one',
            fontsize=10.5, color=PURPLE, ha='left', va='center')
    ax.text(0.325, 0.175, 'all six rows together are the dataset', fontsize=11,
            color=INK, ha='center')
    ax.set_title('Every word on this page names one part of this table',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'one-example.svg')


def prediction_vs_label() -> None:
    """Predictions at masses nobody measured, against measurements taken later."""
    s = _sag_numbers()
    rng = np.random.default_rng(17)
    new_x = np.array([0.25, 0.75, 1.25, 1.75, 2.25])
    truth = 1.4 * new_x + 0.5
    new_y = np.round(truth + rng.normal(0, 0.22, len(new_x)), 2)
    pred = s['slope'] * new_x + s['intercept']
    err = new_y - pred
    print('[new] masses nobody had measured:')
    for a, p, m in zip(new_x, pred, new_y):
        print(f'[new]   {a:.2f} kg: prediction {p:.3f} mm, later measured {m:.2f} mm, '
              f'miss {m - p:+.3f} mm')
    print(f'[new] typical miss on these five {float(np.sqrt(np.mean(err ** 2))):.3f} mm, '
          f'against {float(np.sqrt(s["mse_fit"])):.3f} mm on the six it was fitted to')

    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    grid = np.linspace(-0.1, 2.6, 80)
    ax.plot(grid, s['slope'] * grid + s['intercept'], color=LINK, lw=2.0,
            label=f'the fitted line, from the six black points')
    ax.scatter(SAG_X, SAG_Y, s=55, color=INK, zorder=5,
               label='the six examples it was fitted to')
    ax.scatter(new_x, pred, s=70, marker='s', color=PURPLE, zorder=6,
               label='predictions at five new masses')
    ax.scatter(new_x, new_y, s=70, marker='D', color=SLIDE, zorder=6,
               label='the labels measured later')
    for a, p, m in zip(new_x, pred, new_y):
        ax.plot([a, a], [p, m], color=GRIP, lw=1.6)
        ax.annotate(f'{m - p:+.2f}', (a, (p + m) / 2), fontsize=9.3, color=GRIP,
                    textcoords='offset points', xytext=(12, 0), ha='left',
                    va='center')
    ax.set_xlabel('mass hung on the wrist (kilograms)', fontsize=10.5)
    ax.set_ylabel('tool tip drop (millimetres)', fontsize=10.5)
    ax.set_xlim(-0.2, 2.85)
    ax.set_ylim(-0.1, 5.3)
    ax.set_title(f'A prediction is what the line says; a label is what the tape '
                 f'measure said, and they differ by up to '
                 f'{float(np.max(np.abs(err))):.2f} mm',
                 fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left')
    _save(fig, RULES_DOC, 'prediction-vs-label.svg')


def feature_choice() -> None:
    """A feature is a number chosen because the answer depends on it."""
    rng = np.random.default_rng(29)
    n = 60
    mass = rng.uniform(0.0, 2.5, n)
    paint = rng.uniform(20, 230, n)
    sag = 1.4 * mass + 0.5 + rng.normal(0, 0.22, n)
    r_mass = float(np.corrcoef(mass, sag)[0, 1])
    r_paint = float(np.corrcoef(paint, sag)[0, 1])
    m1, b1 = _fit_line(mass, sag)
    m2, b2 = _fit_line(paint, sag)
    e1 = _mse(m1 * mass + b1, sag)
    e2 = _mse(m2 * paint + b2, sag)
    print(f'[feature] 60 simulated loads. sag against mass: agreement {r_mass:+.3f}, '
          f'fitted line misses by {np.sqrt(e1):.3f} mm')
    print(f'[feature] sag against the colour of the object: agreement {r_paint:+.3f}, '
          f'fitted line misses by {np.sqrt(e2):.3f} mm')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), facecolor='white', sharey=True)
    for ax, xv, m, b, r, e, lab, colour in (
            (axes[0], mass, m1, b1, r_mass, e1, 'mass of the object (kilograms)', SLIDE),
            (axes[1], paint, m2, b2, r_paint, e2,
             'brightness of the object\'s paint (0 to 255)', GRIP)):
        _plain(ax)
        ax.scatter(xv, sag, s=22, color=colour, alpha=0.75)
        g = np.linspace(xv.min(), xv.max(), 40)
        ax.plot(g, m * g + b, color=INK, lw=1.8)
        ax.set_xlabel(lab, fontsize=10)
        ax.set_title(f'agreement {r:+.2f}, the line misses by {np.sqrt(e):.2f} mm',
                     fontsize=11.2, weight='bold', color=colour)
    axes[0].set_ylabel('tool tip drop (millimetres)', fontsize=10)
    fig.suptitle('The mass is a feature of this job and the paint colour is not, '
                 'because only one of them moves the answer',
                 fontsize=12.2, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, RULES_DOC, 'feature-choice.svg')


def label_noise() -> None:
    """The same mass measured twelve times gives twelve slightly different labels."""
    rng = np.random.default_rng(41)
    reps = np.round(1.4 * 1.0 + 0.5 + rng.normal(0, 0.22, 12), 2)
    print(f'[noise] twelve measurements at 1.0 kg: '
          + ', '.join(f'{v:.2f}' for v in reps))
    print(f'[noise] average {reps.mean():.3f} mm, spread {reps.std(ddof=1):.3f} mm, '
          f'range {reps.min():.2f} to {reps.max():.2f} mm')

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    order = np.arange(1, 13)
    ax.scatter(reps, order, s=80, color=LINK, alpha=0.85, zorder=4)
    for v, k in zip(reps, order):
        ax.annotate(f'{v:.2f}', (v, k), fontsize=9.3, color=INK, ha='left',
                    va='center', textcoords='offset points', xytext=(10, 0))
    ax.axvline(float(reps.mean()), color=SLIDE, lw=1.8)
    ax.text(float(reps.mean()) - 0.012, 13.1, f'average of the twelve: '
                                              f'{reps.mean():.2f} mm',
            fontsize=10, color=SLIDE, ha='right')
    ax.axvline(1.9, color=GRIP, lw=1.6, ls='--')
    ax.text(1.915, 0.1, 'what the fitted line says for 1.0 kg: 1.9 mm', fontsize=9.8,
            color=GRIP, ha='left')
    ax.set_xlim(reps.min() - 0.1, reps.max() + 0.25)
    ax.set_ylim(-0.4, 14.0)
    ax.set_yticks([1, 4, 8, 12])
    ax.set_ylabel('which of the twelve tries', fontsize=10.5)
    ax.set_xlabel('tool tip drop measured with the same 1.0 kg mass (millimetres)',
                  fontsize=10.5)
    ax.set_title(f'A label is a measurement, so twelve tries at one mass spread over '
                 f'{reps.max() - reps.min():.2f} mm',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, RULES_DOC, 'label-noise.svg')


# ==========================================================================
# PAGE 1, SECTION 6: what fitting costs
# ==========================================================================

def _true_sag(x: Arr) -> Arr:
    """Made-up truth: the sag stops growing once the arm's belt reaches its stop."""
    return np.where(x <= 2.8, 1.4 * x + 0.5, 1.4 * 2.8 + 0.5 + 0.25 * (x - 2.8))


def outside_the_range() -> None:
    """The fitted line is only trustworthy over the masses that were measured."""
    s = _sag_numbers()
    xs = np.array([3.0, 4.0, 5.0, 6.0])
    pred = s['slope'] * xs + s['intercept']
    real = _true_sag(xs)
    for a, p, r in zip(xs, pred, real):
        print(f'[outside] {a:.0f} kg: line says {p:.2f} mm, the arm really drops '
              f'{r:.2f} mm, miss {p - r:+.2f} mm')
    grid = np.linspace(0, 6, 200)

    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    ax.axvspan(0, 2.5, color='#eef4ea', zorder=0)
    ax.text(1.25, 9.4, 'masses that were measured', fontsize=10, color=SLIDE,
            ha='center')
    ax.text(4.25, 9.4, 'masses nobody measured', fontsize=10, color=GRIP, ha='center')
    ax.plot(grid, s['slope'] * grid + s['intercept'], color=LINK, lw=2.2,
            label=f'the fitted line, carried on past 2.5 kg')
    ax.plot(grid, _true_sag(grid), color=INK, lw=1.8, ls='--',
            label='what the arm really does (simulated)')
    ax.scatter(SAG_X, SAG_Y, s=52, color=INK, zorder=5, label='the six examples')
    for a, p, r in zip(xs, pred, real):
        ax.plot([a, a], [p, r], color=GRIP, lw=1.6)
        ax.annotate(f'{p - r:+.2f}', (a, (p + r) / 2), fontsize=9.6, color=GRIP,
                    textcoords='offset points', xytext=(10, 9), ha='left',
                    va='center')
    ax.set_xlim(0, 6.6)
    ax.set_ylim(0, 10.2)
    ax.set_xlabel('mass hung on the wrist (kilograms)', fontsize=10.5)
    ax.set_ylabel('tool tip drop (millimetres)', fontsize=10.5)
    ax.set_title(f'At 6 kg the line is wrong by {pred[-1] - real[-1]:+.2f} mm, because '
                 f'nothing told it the belt reaches a stop',
                 fontsize=11.8, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, RULES_DOC, 'outside-the-range.svg')


def more_examples_less_error() -> None:
    """How the miss on unseen loads falls as the number of examples grows."""
    rng = np.random.default_rng(53)
    sizes = [3, 5, 8, 12, 20, 40, 80, 160]
    test_x = np.linspace(0.0, 2.5, 400)
    means, lows, highs = [], [], []
    for n in sizes:
        errs = []
        for _ in range(200):
            x = rng.uniform(0, 2.5, n)
            y = 1.4 * x + 0.5 + rng.normal(0, 0.22, n)
            m, b = _fit_line(x, y)
            # the test labels are fresh measurements, so they carry their own spread
            test_y = 1.4 * test_x + 0.5 + rng.normal(0, 0.22, len(test_x))
            errs.append(float(np.sqrt(np.mean((m * test_x + b - test_y) ** 2))))
        means.append(float(np.mean(errs)))
        lows.append(float(np.quantile(errs, 0.1)))
        highs.append(float(np.quantile(errs, 0.9)))
    for n, mu in zip(sizes, means):
        print(f'[grow] {n:3d} examples: typical miss on unseen masses {mu:.3f} mm')
    print(f'[grow] going from {sizes[0]} to {sizes[-1]} examples cuts the miss by '
          f'{means[0] / means[-1]:.1f} times')

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    ax.fill_between(sizes, lows, highs, color=LINK, alpha=0.18,
                    label='middle 80 per cent of 200 repeats')
    ax.plot(sizes, means, marker='o', color=LINK, lw=2.0, label='average over 200 repeats')
    ax.axhline(0.22, color=GRIP, ls='--', lw=1.4)
    ax.text(150, 0.40, 'the dashed line is the spread of the\nmeasurements '
                       'themselves, 0.22 mm', fontsize=9.8, color=GRIP, ha='right')
    for n, mu in zip(sizes, means):
        if n in (3, 5, 20):
            ax.annotate(f'{mu:.3f}', (n, mu), fontsize=9.5, color=INK,
                        textcoords='offset points', xytext=(7, 8))
        elif n == 160:
            ax.annotate(f'{mu:.3f}', (n, mu), fontsize=9.5, color=INK, ha='right',
                        textcoords='offset points', xytext=(-6, 9))
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('number of examples the line was fitted to (log scale)', fontsize=10.5)
    ax.set_ylabel('typical miss on masses it had not seen (millimetres)', fontsize=10.5)
    ax.set_ylim(0, 1.0)
    ax.set_title('More examples buy a better line, but only down to the spread of the '
                 'measurements themselves', fontsize=11.8, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False)
    _save(fig, RULES_DOC, 'more-examples-less-error.svg')


def one_bad_example() -> None:
    """One stuck sensor reading drags the whole line."""
    s = _sag_numbers()
    bad_y = SAG_Y.copy()
    bad_y[4] = 12.0
    m2, b2 = _fit_line(SAG_X, bad_y)
    good = np.delete(np.arange(6), 4)
    err_clean = float(np.sqrt(_mse(s['slope'] * SAG_X[good] + s['intercept'],
                                   SAG_Y[good])))
    err_dirty = float(np.sqrt(_mse(m2 * SAG_X[good] + b2, SAG_Y[good])))
    print(f'[bad] one reading changed from 3.6 mm to 12.0 mm')
    print(f'[bad] the line moves from {s["slope"]:.2f} x mass + {s["intercept"]:.2f} '
          f'to {m2:.2f} x mass + {b2:.2f}')
    print(f'[bad] on the five good measurements the miss grows from {err_clean:.3f} mm '
          f'to {err_dirty:.3f} mm')

    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    grid = np.linspace(-0.1, 2.7, 60)
    ax.plot(grid, s['slope'] * grid + s['intercept'], color=LINK, lw=2.2,
            label=f'fitted to the six good readings: {s["slope"]:.1f} x mass + '
                  f'{s["intercept"]:.1f}')
    ax.plot(grid, m2 * grid + b2, color=GRIP, lw=2.2, ls='--',
            label=f'fitted with the stuck reading: {m2:.2f} x mass + {b2:.2f}')
    ax.scatter(SAG_X[good], SAG_Y[good], s=58, color=INK, zorder=5,
               label='five good readings')
    ax.scatter([SAG_X[4]], [SAG_Y[4]], s=58, color=SLIDE, zorder=5,
               label='the real reading at 2.0 kg: 3.6 mm')
    ax.scatter([SAG_X[4]], [12.0], s=90, marker='X', color=GRIP, zorder=6,
               label='the stuck reading: 12.0 mm')
    ax.annotate('the sensor stuck once', xy=(2.0, 12.0), xytext=(0.9, 11.2),
                fontsize=10, color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.2})
    ax.set_xlim(-0.15, 2.8)
    ax.set_ylim(-1.0, 13.2)
    ax.set_xlabel('mass hung on the wrist (kilograms)', fontsize=10.5)
    ax.set_ylabel('tool tip drop (millimetres)', fontsize=10.5)
    ax.set_title(f'One wrong example in six moves the line, and the miss on the good '
                 f'readings grows from {err_clean:.2f} mm to {err_dirty:.2f} mm',
                 fontsize=11.5, weight='bold', color=INK)
    ax.legend(fontsize=9.2, frameon=False, loc='upper left')
    _save(fig, RULES_DOC, 'one-bad-example.svg')


# ==========================================================================
# PAGE 2, SECTION 1: the model, its parameters, its weights
# ==========================================================================

def two_numbers_inside() -> None:
    """One model, three settings of its two numbers, three different errors."""
    s = _sag_numbers()
    settings = [(2.0, -1.0), (HAND_SLOPE, HAND_INTERCEPT),
                (s['slope'], s['intercept'])]
    labels = ['slope 2.0, offset -1.0', 'slope 1.0, offset 0.0',
              f'slope {s["slope"]:.1f}, offset {s["intercept"]:.1f}']
    errs = [_mse(m * SAG_X + b, SAG_Y) for m, b in settings]
    for lab, e in zip(labels, errs):
        print(f'[two] {lab:34s} average squared miss {e:.4f} mm^2, '
              f'typical miss {np.sqrt(e):.3f} mm')

    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.6), facecolor='white', sharey=True)
    grid = np.linspace(-0.1, 2.7, 60)
    for ax, (m, b), lab, e, colour in zip(axes, settings, labels, errs,
                                          [GRIP, JOINT, SLIDE]):
        _plain(ax)
        ax.plot(grid, m * grid + b, color=colour, lw=2.2)
        for xv, yv in zip(SAG_X, SAG_Y):
            ax.plot([xv, xv], [yv, m * xv + b], color=colour, lw=1.0, alpha=0.65)
        ax.scatter(SAG_X, SAG_Y, s=46, color=INK, zorder=5)
        ax.set_xlabel('mass (kg)', fontsize=10)
        ax.set_title(f'{lab}\ntypical miss {np.sqrt(e):.3f} mm', fontsize=10.8,
                     weight='bold', color=colour)
        ax.set_ylim(-1.2, 4.9)
    axes[0].set_ylabel('tool tip drop (mm)', fontsize=10)
    fig.suptitle('The same model three times: only the two numbers inside it changed',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WORDS_DOC, 'two-numbers-inside.svg')


def _layer_params(sizes: list[int]) -> int:
    return int(sum(a * b + b for a, b in zip(sizes[:-1], sizes[1:])))


def _block_params(width: int, blocks: int, ff: int = 4) -> int:
    per = 4 * width * width + 2 * ff * width * width
    return int(per * blocks)


PARAM_CASES: list[tuple[str, int]] = []


def _param_cases() -> list[tuple[str, int]]:
    global PARAM_CASES
    if not PARAM_CASES:
        small = _layer_params([3, 8, 1])
        pic = _layer_params([64 * 64, 256, 256, 1])
        big = _block_params(2048, 48)
        PARAM_CASES = [
            ('the fitted line\n(slope and offset)', 2),
            ('a tiny network\n3 -> 8 -> 1', small),
            ('a network reading a\n64 by 64 grey picture\n4096 -> 256 -> 256 -> 1', pic),
            ('a stack of 48 blocks,\neach 2,048 wide', big),
        ]
    return PARAM_CASES


def parameter_count() -> None:
    """How many adjustable numbers each of four models holds."""
    cases = _param_cases()
    for lab, n in cases:
        print(f'[params] {lab.replace(chr(10), " "):56s} {n:,} parameters')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    vals = [n for _l, n in cases]
    bars = ax.bar(range(4), vals, color=[SLIDE, LINK, PURPLE, GRIP], alpha=0.85,
                  edgecolor=INK, lw=0.6, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.5, f'{v:,}', ha='center', fontsize=11, weight='bold',
                color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, max(vals) * 25)
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab for lab, _n in cases], fontsize=9.3)
    ax.set_ylabel('number of adjustable numbers (log scale)', fontsize=10.5)
    ax.set_title('Every one of these is a model, and the only difference is how many '
                 'numbers training has to choose', fontsize=11.8, weight='bold',
                 color=INK)
    _save(fig, WORDS_DOC, 'parameter-count.svg')


def weights_are_dials() -> None:
    """A weight says how much one input counts, and its size says how much."""
    m = _cup_model()
    w = np.asarray(m['w'])
    b = float(m['b'])
    names = ['brightness inside\nthe rim', 'spread of that\nbrightness',
             'brightness of\nthe cup wall']
    print(f'[weights] the cup model has 3 weights and 1 offset: '
          f'inside {w[0]:+.3f}, spread {w[1]:+.3f}, wall {w[2]:+.3f}, offset {b:+.3f}')
    print(f'[weights] nobody told it to subtract the wall brightness, but the first '
          f'and third weights came out with opposite signs')

    fig, ax = plt.subplots(figsize=(10.8, 5.0), facecolor='white')
    _plain(ax)
    cols = [SLIDE if v > 0 else GRIP for v in w]
    ax.barh(range(3), w, color=cols, alpha=0.85, edgecolor=INK, lw=0.6, height=0.5)
    for i, v in enumerate(w):
        ax.text(v + (0.07 if v > 0 else -0.07), i, f'{v:+.2f}',
                va='center', ha='left' if v > 0 else 'right', fontsize=11.5,
                weight='bold', color=INK)
    ax.axvline(0, color=INK, lw=1.1)
    ax.set_yticks(range(3))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlim(min(w) * 1.5 - 0.2, max(w) * 1.5 + 0.2)
    ax.set_ylim(-0.6, 2.95)
    ax.set_xlabel('the weight training chose for that number', fontsize=10.5)
    ax.text(min(w) * 1.42, 2.62, f'the fourth parameter is not a weight, because it '
                                 f'multiplies nothing:\nit is the offset, and training '
                                 f'set it to {b:+.2f}',
            fontsize=10, color=MUTED, ha='left', va='center')
    ax.set_title('A weight is one number saying how much one input counts, and a '
                 'minus sign means it counts against',
                 fontsize=11.8, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'weights-are-the-dials.svg')


def model_file_size() -> None:
    """What a parameter costs in memory at three common number sizes."""
    cases = _param_cases()
    kinds = [('4 bytes each (float32)', 4), ('2 bytes each (bfloat16)', 2),
             ('1 byte each (int8)', 1)]

    def pretty(b: int) -> str:
        if b < 1024:
            return f'{b} bytes'
        if b < 1024 ** 2:
            return f'{b / 1024:,.1f} KB'
        if b < 1024 ** 3:
            return f'{b / 1024 ** 2:,.1f} MB'
        return f'{b / 1024 ** 3:,.2f} GB'

    for lab, n in cases:
        row = ', '.join(f'{k}: {pretty(n * by)}' for k, by in kinds)
        print(f'[size] {lab.replace(chr(10), " "):56s} {row}')

    fig, ax = plt.subplots(figsize=(11.6, 5.2), facecolor='white')
    _plain(ax)
    width = 0.26
    for j, (lab, by) in enumerate(kinds):
        vals = [n * by for _l, n in cases]
        ax.bar(np.arange(4) + (j - 1) * width, vals, width=width,
               color=[LINK, PURPLE, GRIP][j], alpha=0.85, edgecolor=INK, lw=0.5,
               label=lab)
    for i, (_l, n) in enumerate(cases):
        ax.text(i, n * 4 * 2.6, pretty(n * 4), ha='center', fontsize=9.8, color=INK)
    ax.set_yscale('log')
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab for lab, _n in cases], fontsize=9.3)
    ax.set_ylabel('size of the saved parameters, in bytes (log scale)', fontsize=10.5)
    ax.set_ylim(1, max(n * 4 for _l, n in cases) * 90)
    ax.set_title('A parameter count is also a file size, which is why how many bytes '
                 'a number takes matters', fontsize=11.8, weight='bold', color=INK)
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, WORDS_DOC, 'model-file-size.svg')


# ==========================================================================
# PAGE 2, SECTION 2: training and inference
# ==========================================================================

def _sag_gd(steps: int = 300, lr: float = 0.08) -> dict[str, Arr]:
    """Train the two-number sag model by plain gradient descent, keeping the path."""
    m, b = 0.0, 0.0
    ms, bs, losses = [m], [b], [_mse(np.zeros_like(SAG_X), SAG_Y)]
    n = len(SAG_X)
    for _ in range(steps):
        pred = m * SAG_X + b
        gm = float(2.0 * np.sum((pred - SAG_Y) * SAG_X) / n)
        gb = float(2.0 * np.sum(pred - SAG_Y) / n)
        m -= lr * gm
        b -= lr * gb
        ms.append(m)
        bs.append(b)
        losses.append(_mse(m * SAG_X + b, SAG_Y))
    return {'m': np.array(ms), 'b': np.array(bs), 'loss': np.array(losses)}


def training_curve() -> None:
    """The score of being wrong falling step by step while the two numbers move."""
    s = _sag_numbers()
    r = _sag_gd()
    loss, ms, bs = r['loss'], r['m'], r['b']
    for k in (0, 10, 50, 100, 300):
        print(f'[train] step {k:3d}: slope {ms[k]:.4f}, offset {bs[k]:.4f}, '
              f'average squared miss {loss[k]:.4f}')
    print(f'[train] the exact best is slope {s["slope"]:.4f}, offset '
          f'{s["intercept"]:.4f}, average squared miss {s["mse_fit"]:.4f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.9, 1.0]})
    ax = axes[0]
    _plain(ax)
    ax.plot(np.arange(len(loss)), loss, color=LINK, lw=2.2)
    ax.set_yscale('log')
    ax.axhline(s['mse_fit'], color=SLIDE, ls='--', lw=1.4)
    ax.text(298, s['mse_fit'] * 1.25, f'the lowest these two numbers can reach: '
                                      f'{s["mse_fit"]:.4f}', fontsize=9.8, color=SLIDE,
            ha='right')
    for k in (0, 10, 50, 300):
        ax.scatter([k], [loss[k]], s=48, color=GRIP, zorder=6)
        ax.annotate(f'step {k}', (k, loss[k]), fontsize=9.6, color=GRIP,
                    textcoords='offset points', xytext=(9, 9))
    ax.set_xlim(-12, 320)
    ax.set_ylim(0.03, 12)
    ax.set_xlabel('training step (one pass over all six examples each time)',
                  fontsize=10.5)
    ax.set_ylabel('average squared miss (square millimetres, log scale)', fontsize=10.5)
    ax.set_title('The score of being wrong falls fast and then stops',
                 fontsize=11.2, weight='bold', color=INK)

    ax2 = axes[1]
    _blank(ax2)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    heads = ['step', 'slope', 'offset', 'miss']
    xs = [0.10, 0.36, 0.62, 0.88]
    for xx, hh in zip(xs, heads):
        ax2.text(xx, 0.80, hh, fontsize=10.5, weight='bold', color=INK, ha='center')
    ax2.plot([0.02, 0.98], [0.775, 0.775], color=INK, lw=1.1)
    for i, k in enumerate((0, 10, 50, 100, 300)):
        yy = 0.70 - 0.105 * i
        for xx, vv in zip(xs, (f'{k}', f'{ms[k]:.2f}', f'{bs[k]:.2f}',
                               f'{loss[k]:.4f}')):
            ax2.text(xx, yy, vv, fontsize=10.5, color=INK, ha='center',
                     family='monospace')
    ax2.text(0.5, 0.11, f'the exact best is slope {s["slope"]:.1f} and offset '
                        f'{s["intercept"]:.1f},\nwhich 300 steps have reached',
             fontsize=10, color=SLIDE, ha='center')
    ax2.set_title('The two numbers at five moments', fontsize=11.2, weight='bold',
                  color=INK)
    fig.suptitle('Training is a search: the two numbers move downhill and the score '
                 'of being wrong falls', fontsize=12.2, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, WORDS_DOC, 'training-curve.svg')


def parameters_walking() -> None:
    """The path the two parameters take across the map of the error."""
    s = _sag_numbers()
    r = _sag_gd()
    mg = np.linspace(-0.2, 2.6, 160)
    bg = np.linspace(-1.6, 2.2, 160)
    MM, BB = np.meshgrid(mg, bg)
    Z = np.zeros_like(MM)
    for i in range(len(SAG_X)):
        Z += (MM * SAG_X[i] + BB - SAG_Y[i]) ** 2
    Z /= len(SAG_X)
    print(f'[walk] the path starts at slope 0.00, offset 0.00 with miss '
          f'{r["loss"][0]:.4f} and ends at slope {r["m"][-1]:.4f}, offset '
          f'{r["b"][-1]:.4f} with miss {r["loss"][-1]:.4f}')
    print(f'[walk] the lowest point of the map is slope {s["slope"]:.4f}, offset '
          f'{s["intercept"]:.4f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.6), facecolor='white')
    _plain(ax)
    cs = ax.contourf(MM, BB, Z, levels=np.geomspace(0.04, 20, 18), cmap='Blues',
                     alpha=0.85)
    ax.contour(MM, BB, Z, levels=np.geomspace(0.04, 20, 18), colors=[MUTED],
               linewidths=0.4)
    fig.colorbar(cs, ax=ax, label='average squared miss (square millimetres)')
    ax.plot(r['m'], r['b'], color=GRIP, lw=2.0)
    ax.scatter([r['m'][0]], [r['b'][0]], s=70, color=INK, zorder=6)
    ax.annotate('step 0: both numbers 0', (r['m'][0], r['b'][0]), fontsize=9.8,
                color=INK, textcoords='offset points', xytext=(10, -14))
    ax.scatter([s['slope']], [s['intercept']], s=110, marker='*', color=SLIDE, zorder=6)
    ax.annotate(f'the lowest point:\nslope {s["slope"]:.1f}, offset '
                f'{s["intercept"]:.1f}', (s['slope'], s['intercept']), fontsize=9.8,
                color=SLIDE, ha='left', va='top',
                textcoords='offset points', xytext=(12, -12))
    ax.set_xlabel('the first parameter: the slope', fontsize=10.5)
    ax.set_ylabel('the second parameter: the offset', fontsize=10.5)
    ax.set_title('Training walks the two parameters downhill across this map, in 300 '
                 'steps', fontsize=11.8, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'parameters-walking.svg')


def training_vs_inference_cost() -> None:
    """How much arithmetic training does, against how much one answer costs."""
    sag_infer = 2
    sag_train = 300 * len(SAG_X) * 6
    cup_infer = 2 * 3 + 1
    cup_train = 400 * 800 * (2 * 3 + 1 + 2 * 3)
    labels = ['one answer from\nthe sag model', 'training the\nsag model\n(300 steps, '
              '6 examples)', 'one answer from\nthe cup model',
              'training the cup model\n(400 steps, 800 examples)']
    vals = [sag_infer, sag_train, cup_infer, cup_train]
    for lab, v in zip(labels, vals):
        print(f'[cost] {lab.replace(chr(10), " "):56s} {v:,} multiplications and '
              f'additions')
    print(f'[cost] training the cup model does {cup_train // cup_infer:,} times the '
          f'arithmetic of answering once')

    fig, ax = plt.subplots(figsize=(11.4, 5.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(4), vals, color=[SLIDE, GRIP, SLIDE, GRIP], alpha=0.85,
                  edgecolor=INK, lw=0.6, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.6, f'{v:,}', ha='center', fontsize=11, weight='bold',
                color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1, max(vals) * 30)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=9.3)
    ax.set_ylabel('multiplications and additions (log scale)', fontsize=10.5)
    ax.set_title(f'Training is done once and costs {cup_train // cup_infer:,} times an '
                 f'answer; inference is done every time the robot looks',
                 fontsize=11.6, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'training-vs-inference-cost.svg')


def one_inference_by_hand() -> None:
    """What inference does to one input: two fixed numbers and two operations."""
    s = _sag_numbers()
    x = 1.75
    step1 = s['slope'] * x
    out = step1 + s['intercept']
    print(f'[infer] one answer for {x:.2f} kg: {s["slope"]:.1f} x {x:.2f} = '
          f'{step1:.3f}, plus the offset {s["intercept"]:.1f} = {out:.3f} mm')
    print(f'[infer] the two parameters are the same before and after, because '
          f'inference never changes them')

    fig, ax = plt.subplots(figsize=(12.2, 3.9), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    stages = [
        (0.005, 0.190, LINK, 'the input', f'{x:.2f} kg', 'a mass nobody measured'),
        (0.240, 0.235, PURPLE, 'multiply by the weight',
         f'{s["slope"]:.1f} x {x:.2f} = {step1:.2f}', 'the weight stays at 1.4'),
        (0.520, 0.235, PURPLE, 'add the offset',
         f'{step1:.2f} + {s["intercept"]:.1f} = {out:.2f}', 'the offset stays at 0.5'),
        (0.800, 0.190, SLIDE, 'the output', f'{out:.2f} mm', 'one answer, one input'),
    ]
    for xx, w, colour, head, value, note in stages:
        _box(ax, xx, 0.30, w, 0.44, colour, alpha=0.12)
        ax.text(xx + w / 2, 0.675, head, fontsize=11.2, weight='bold', color=colour,
                ha='center')
        ax.text(xx + w / 2, 0.515, value, fontsize=11.5, color=INK, ha='center',
                va='center', family='monospace')
        ax.text(xx + w / 2, 0.365, note, fontsize=9.4, color=MUTED, ha='center')
    for xx in (0.200, 0.481, 0.761):
        _arrow(ax, xx, 0.52, xx + 0.034, 0.52, colour=INK, lw=1.6)
    ax.text(0.5, 0.14, 'one multiplication and one addition, using the two numbers '
                       'training left behind',
            fontsize=10.5, color=INK, ha='center')
    ax.set_title('Inference on the sag model: the input moves, the two parameters do '
                 'not', fontsize=12.5, weight='bold', color=INK, pad=12)
    _save(fig, WORDS_DOC, 'one-inference-by-hand.svg')


# ==========================================================================
# PAGE 2, SECTION 3: the dataset and generalisation
# ==========================================================================

def dataset_split() -> None:
    """The 1,600 cups divided into the half fitted on and the half kept back."""
    c = _cups()
    m = _cup_model()
    print(f'[split] {c.n} cups: {c.split} used for training, {c.n - c.split} kept back')
    print(f'[split] accuracy {float(m["acc_train"]):.3f} on the half it was fitted to, '
          f'{float(m["acc_test"]):.3f} on the half it had never seen')

    fig, ax = plt.subplots(figsize=(11.6, 4.0), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    _box(ax, 0.03, 0.50, 0.46, 0.38, LINK, alpha=0.18)
    _box(ax, 0.51, 0.50, 0.46, 0.38, PURPLE, alpha=0.18)
    ax.text(0.26, 0.805, f'{c.split} cups used for training', fontsize=12,
            weight='bold', color=LINK, ha='center')
    ax.text(0.74, 0.805, f'{c.n - c.split} cups kept back', fontsize=12,
            weight='bold', color=PURPLE, ha='center')
    ax.text(0.26, 0.685, 'the four parameters are chosen\nto fit these labels',
            fontsize=10, color=INK, ha='center')
    ax.text(0.74, 0.685, 'the parameters never saw these,\nso the score on them is '
                         'the honest one', fontsize=10, color=INK, ha='center')
    ax.text(0.26, 0.565, f'accuracy {float(m["acc_train"]):.3f}', fontsize=12.5,
            weight='bold', color=LINK, ha='center')
    ax.text(0.74, 0.565, f'accuracy {float(m["acc_test"]):.3f}', fontsize=12.5,
            weight='bold', color=PURPLE, ha='center')
    rng = np.random.default_rng(3)
    for k in range(80):
        xx = 0.04 + 0.44 * (k % 40) / 39.0 + (0.48 if k >= 40 else 0.0)
        yy = 0.355
        ax.add_patch(Circle((xx, yy), 0.009,
                            color=GRIP if rng.random() > 0.5 else TEAL, zorder=4))
    ax.text(0.50, 0.21, 'each dot is one example: three measured numbers and one label',
            fontsize=10, color=INK, ha='center')
    ax.text(0.50, 0.10, 'red dots are full cups, green dots are empty ones',
            fontsize=9.5, color=MUTED, ha='center')
    ax.set_title(f'A dataset is the examples; generalisation is the score on the ones '
                 f'held back ({float(m["acc_test"]):.3f})',
                 fontsize=12.2, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'dataset-split.svg')


def _poly_curves() -> dict[str, object]:
    rng = np.random.default_rng(67)
    x = np.linspace(0.03, 0.97, 10) + rng.normal(0, 0.012, 10)
    truth = lambda t: 0.9 * np.sin(2.6 * t) + 0.35 * t  # noqa: E731
    y = truth(x) + rng.normal(0, 0.06, len(x))
    # only inputs between the smallest and largest example count as unseen inputs
    xt = np.linspace(float(x.min()), float(x.max()), 300)
    yt = truth(xt)
    degs = list(range(1, 9))
    seen, unseen = [], []
    for d in degs:
        co = np.polyfit(x, y, d)
        seen.append(float(np.sqrt(np.mean((np.polyval(co, x) - y) ** 2))))
        unseen.append(float(np.sqrt(np.mean((np.polyval(co, xt) - yt) ** 2))))
    return {'x': x, 'y': y, 'xt': xt, 'yt': yt, 'degs': degs,
            'seen': seen, 'unseen': unseen}


def seen_vs_unseen() -> None:
    """The score on the examples it fitted against the score on everything else."""
    p = _poly_curves()
    degs = p['degs']
    seen = p['seen']
    unseen = p['unseen']
    best = int(np.argmin(unseen))
    n_ex = len(np.asarray(p['x']))
    for d, a, b in zip(degs, seen, unseen):
        print(f'[gen] a curve with {d + 1} parameters: miss {a:.4f} on the {n_ex} '
              f'examples, {b:.4f} everywhere else')
    print(f'[gen] the best on unseen points has {degs[best] + 1} parameters '
          f'({unseen[best]:.4f}); the most flexible has {degs[-1] + 1} '
          f'({unseen[-1]:.4f}) while fitting the examples to {seen[-1]:.4f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(degs, seen, marker='o', color=LINK, lw=2.0,
            label=f'miss on the {n_ex} examples it fitted')
    ax.plot(degs, unseen, marker='s', color=GRIP, lw=2.0,
            label='miss on inputs in between')
    ax.scatter([degs[best]], [unseen[best]], s=130, marker='*', color=SLIDE, zorder=6)
    ax.annotate(f'best on unseen inputs: {degs[best] + 1} parameters, '
                f'{unseen[best]:.3f}', (degs[best], unseen[best]), fontsize=9.6,
                color=SLIDE, ha='left', va='top', textcoords='offset points',
                xytext=(12, -8))
    ax.set_yscale('log')
    ax.set_ylim(min(min(seen), min(unseen)) * 0.45, max(max(seen), max(unseen)) * 1.6)
    ax.set_xlabel('number of parameters in the curve', fontsize=10.5)
    ax.set_xticks(degs)
    ax.set_xticklabels([str(d + 1) for d in degs])
    ax.set_ylabel('typical miss (log scale)', fontsize=10.5)
    ax.set_title('More parameters always help on the examples and stop helping on '
                 'everything else', fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='lower center')
    _save(fig, WORDS_DOC, 'seen-vs-unseen.svg')


def flexible_curve_wanders() -> None:
    """The shape a curve with too many parameters draws between its examples."""
    p = _poly_curves()
    degs = p['degs']
    unseen = p['unseen']
    best = int(np.argmin(unseen))
    n_ex = len(np.asarray(p['x']))
    print(f'[wander] the {degs[best] + 1}-parameter curve and the {degs[-1] + 1}-'
          f'parameter curve pass through the same {n_ex} examples, missing unseen '
          f'inputs by {unseen[best]:.4f} and {unseen[-1]:.4f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(p['xt'], p['yt'], color=INK, lw=1.6, ls='--',
            label='the shape the data really has')
    for d, colour in ((degs[best], SLIDE), (degs[-1], GRIP)):
        co = np.polyfit(p['x'], p['y'], d)
        ax.plot(p['xt'], np.polyval(co, p['xt']), color=colour, lw=2.0,
                label=f'{d + 1} parameters, miss {unseen[degs.index(d)]:.3f}')
    ax.scatter(p['x'], p['y'], s=48, color=LINK, zorder=6,
               label=f'the {n_ex} examples')
    ax.set_ylim(-0.1, 1.85)
    ax.set_xlabel('input', fontsize=10.5)
    ax.set_ylabel('output', fontsize=10.5)
    ax.set_title(f'The {degs[-1] + 1}-parameter curve passes closer to the points and '
                 f'wanders between them', fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.6, frameon=False, loc='upper left')
    _save(fig, WORDS_DOC, 'flexible-curve-wanders.svg')


def generalisation_vs_size() -> None:
    """How many examples a flexible curve needs before it generalises."""
    rng = np.random.default_rng(71)
    truth = lambda t: 0.9 * np.sin(2.6 * t) + 0.35 * t  # noqa: E731
    xt = np.linspace(0.05, 0.95, 400)
    yt = truth(xt)
    sizes = [9, 12, 16, 25, 40, 70, 120, 200]
    out = []
    for n in sizes:
        errs = []
        for _ in range(120):
            x = rng.uniform(0, 1, n)
            y = truth(x) + rng.normal(0, 0.06, n)
            co = np.polyfit(x, y, 7)
            errs.append(float(np.sqrt(np.mean((np.polyval(co, xt) - yt) ** 2))))
        out.append(float(np.median(errs)))
    for n, v in zip(sizes, out):
        print(f'[gensize] an 8-parameter curve fitted to {n:3d} examples misses unseen '
              f'inputs by {v:.4f}')
    print(f'[gensize] going from {sizes[0]} to {sizes[-1]} examples cuts that by '
          f'{out[0] / out[-1]:.0f} times')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(sizes, out, marker='o', color=PURPLE, lw=2.2)
    for n, v in zip(sizes, out):
        if n in (sizes[0], 25):
            ax.annotate(f'{v:.3f}', (n, v), fontsize=10, color=INK,
                        textcoords='offset points', xytext=(8, 8))
        elif n == sizes[-1]:
            ax.annotate(f'{v:.3f}', (n, v), fontsize=10, color=INK, ha='right',
                        textcoords='offset points', xytext=(-8, 8))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('number of examples (log scale)', fontsize=10.5)
    ax.set_ylabel('typical miss on unseen inputs (log scale)', fontsize=10.5)
    ax.set_title(f'The same flexible curve generalises badly on {sizes[0]} examples '
                 f'and well on {sizes[-1]}', fontsize=11.8, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'generalisation-vs-size.svg')


# ==========================================================================
# PAGE 2, SECTION 4: supervised, self-supervised, reinforcement
# ==========================================================================

def supervised_labels() -> None:
    """What labelling costs a person, in hours, for the cup dataset."""
    c = _cups()
    seconds = 25
    hours = c.n * seconds / 3600.0
    bigger = [(1_600, 25), (20_000, 25), (200_000, 25), (200_000, 120)]
    for n, sec in bigger:
        print(f'[label] {n:,} examples at {sec} seconds each: '
              f'{n * sec / 3600.0:,.1f} person-hours')
    print(f'[label] the {c.n} cups on this page would take {hours:.1f} person-hours '
          f'at {seconds} seconds a cup')

    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    labs = [f'{n:,} cups\n{sec} s each' for n, sec in bigger]
    vals = [n * sec / 3600.0 for n, sec in bigger]
    ax.bar(range(4), vals, color=[SLIDE, LINK, PURPLE, GRIP], alpha=0.85,
           edgecolor=INK, lw=0.6, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.5, f'{v:,.0f} hours', ha='center', fontsize=11,
                weight='bold', color=INK)
    ax.axhline(37.5, color=MUTED, ls='--', lw=1.3)
    ax.text(-0.45, 44, 'one person-week\n(the dashed line)', fontsize=9.5,
            color=MUTED, ha='left')
    ax.set_yscale('log')
    ax.set_ylim(1, max(vals) * 25)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labs, fontsize=9.6)
    ax.set_ylabel('person-hours of labelling (log scale)', fontsize=10.5)
    ax.set_title('Supervised learning needs a person to write down the right answer, '
                 'and that is what it costs', fontsize=11.8, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'supervised-labels.svg')


def self_supervised_gap() -> None:
    """A hidden stretch of a joint-angle recording, filled in from the rest of it."""
    rng = np.random.default_rng(83)
    t = np.arange(0, 6.0, 0.02)
    ang = (34 * np.sin(2 * np.pi * 0.31 * t) + 12 * np.sin(2 * np.pi * 0.77 * t + 1.1)
           + rng.normal(0, 0.4, len(t)))
    gap = (t >= 3.75) & (t < 4.25)
    keep = ~gap
    window = (t >= 3.1) & (t < 4.9) & keep
    co = np.polyfit(t[window], ang[window], 4)
    guess = np.polyval(co, t[gap])
    err = float(np.mean(np.abs(guess - ang[gap])))
    print(f'[self] {len(t)} samples of one joint, {int(gap.sum())} of them hidden '
          f'(0.5 seconds), including the moment the joint turns round')
    print(f'[self] filled in from the samples either side, the guess is out by '
          f'{err:.2f} degrees on average, worst '
          f'{float(np.max(np.abs(guess - ang[gap]))):.2f} degrees')
    print(f'[self] nobody wrote a label: the hidden samples were the answer')

    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    ax.axvspan(3.75, 4.25, color='#f4eef8', zorder=0)
    shown = np.where(gap, np.nan, ang)
    ax.plot(t, shown, color=LINK, lw=1.5, label='the recording, as the model sees it')
    ax.plot(t[gap], ang[gap], color=INK, lw=1.5, ls='--',
            label='the part hidden from the model')
    ax.plot(t[gap], guess, color=GRIP, lw=2.2, label='what the model filled in')
    ax.text(4.0, 76, f'hidden: 0.5 s\nfilled in to within\n{err:.2f} degrees',
            fontsize=9.6, color=PURPLE, ha='center', va='top')
    ax.set_xlabel('time (seconds)', fontsize=10.5)
    ax.set_ylabel('joint angle (degrees)', fontsize=10.5)
    ax.set_ylim(-60, 80)
    ax.set_title('Self-supervised learning hides part of the data and asks for it '
                 'back, so no person writes a label',
                 fontsize=11.8, weight='bold', color=INK)
    ax.legend(fontsize=9.3, frameon=False, loc='lower left')
    _save(fig, WORDS_DOC, 'self-supervised-fill-the-gap.svg')


def _reach_run(n: int = 400, seed: int = 5) -> tuple[Arr, Arr, Arr]:
    """A simulated reach: the robot searches for the grasp height that works."""
    rng = np.random.default_rng(seed)
    best_h = 18.0
    heights, rewards = [], []
    for _ in range(n):
        h = best_h + rng.normal(0, 9.0)
        chance = float(np.exp(-((h - 42.0) / 13.0) ** 2))
        got = 1.0 if rng.random() < chance else 0.0
        if got > 0.5:
            best_h = best_h + 0.5 * (h - best_h)
        heights.append(h)
        rewards.append(got)
    return np.array(heights), np.array(rewards), np.array([best_h])


def reinforcement_tries() -> None:
    """Learning from the outcome of each try, with no labelled answer anywhere."""
    heights, rewards, final = _reach_run()
    block = 20
    rate = rewards.reshape(-1, block).mean(1)
    mid = (np.arange(len(rate)) + 0.5) * block
    print(f'[rl] 400 attempts in blocks of {block}: success rate '
          + ', '.join(f'{v:.2f}' for v in rate))
    print(f'[rl] first block {rate[0]:.2f}, last block {rate[-1]:.2f}, '
          f'total successes {int(rewards.sum())} of 400')
    print(f'[rl] the height it settled on is {float(final[0]):.1f} mm, against the '
          f'best possible 42.0 mm')

    fig, ax = plt.subplots(figsize=(10.2, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(mid, rate, marker='o', color=TEAL, lw=2.0)
    ax.set_xlabel('attempt number', fontsize=10.5)
    ax.set_ylabel(f'share of the last {block} attempts that worked', fontsize=10.5)
    ax.set_ylim(0, 1.0)
    ax.set_title(f'Told only whether each try worked, the robot goes from '
                 f'{rate[0]:.2f} in the first 20 attempts to {rate[-1]:.2f} in the '
                 f'last 20', fontsize=11.4, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'reinforcement-tries.svg')


def reinforcement_heights() -> None:
    """Every height the search tried, and whether that try lifted the object."""
    heights, rewards, final = _reach_run()
    print(f'[rl2] the 400 heights tried run from {heights.min():.1f} to '
          f'{heights.max():.1f} mm, and the search settled on {float(final[0]):.1f} mm')

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    ax.scatter(np.arange(len(heights)), heights, s=13,
               color=[SLIDE if r > 0.5 else GRIP for r in rewards], alpha=0.75)
    ax.axhline(42.0, color=INK, ls='--', lw=1.4)
    ax.annotate('the dashed line is the height that works best, 42 mm',
                xy=(60, 42.0), xytext=(16, 84), fontsize=10, color=INK, ha='left',
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.1})
    ax.set_ylim(-6, 92)
    ax.set_xlabel('attempt number', fontsize=10.5)
    ax.set_ylabel('grasp height tried (millimetres above the table)', fontsize=10.5)
    ax.set_title(f'Green tries lifted the object and red ones dropped it, and the '
                 f'search closes on {float(final[0]):.0f} mm',
                 fontsize=11.6, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'reinforcement-heights.svg')


def three_signals_cost() -> None:
    """What a person has to supply for each of the three kinds of learning."""
    c = _cups()
    _h, rewards, _f = _reach_run()
    rows = [
        ('supervised:\none written answer\nper example', c.n, 'answers written\nby hand'),
        ('self-supervised:\nthe data is its own\nanswer', 0, 'answers written\nby hand'),
        ('reinforcement:\none rule that scores\na try', 1, 'rule written\nby hand'),
    ]
    print(f'[signals] supervised needs {c.n} written answers for the cup job')
    print(f'[signals] self-supervised needs 0 written answers, because the hidden '
          f'samples are the answer')
    print(f'[signals] reinforcement needs 1 written scoring rule, plus '
          f'{len(rewards)} attempts on the real arm, of which '
          f'{int(rewards.sum())} worked')

    fig, ax = plt.subplots(figsize=(11.2, 5.0), facecolor='white')
    _plain(ax)
    vals = [r[1] for r in rows]
    ax.bar(range(3), [max(v, 0.4) for v in vals], color=[GRIP, SLIDE, LINK],
           alpha=0.85, edgecolor=INK, lw=0.6, width=0.55)
    notes = [f'{c.n:,} answers', '0 answers', '1 scoring rule\n+ 400 real attempts']
    for i, (v, note) in enumerate(zip(vals, notes)):
        ax.text(i, max(v, 0.4) * 1.5, note, ha='center', fontsize=10.5, weight='bold',
                color=INK)
    ax.set_yscale('log')
    ax.set_ylim(0.3, c.n * 25)
    ax.set_xticks(range(3))
    ax.set_xticklabels([r[0] for r in rows], fontsize=9.6)
    ax.set_ylabel('things a person has to write down (log scale)', fontsize=10.5)
    ax.set_title('The three kinds of learning differ in who supplies the right answer, '
                 'not in the arithmetic', fontsize=11.8, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'three-signals-cost.svg')


# ==========================================================================
# PAGE 2, SECTION 5: the four names
# ==========================================================================

def four_names_nested() -> None:
    """Which of the four names contains which, with one real example in each ring."""
    cases = _param_cases()
    line_n = cases[0][1]
    net_n = cases[2][1]
    big_n = cases[3][1]
    print(f'[nest] artificial intelligence holds the joint-limit check of page one, '
          f'which has 0 learned numbers')
    print(f'[nest] machine learning holds the fitted sag line, {line_n} learned numbers')
    print(f'[nest] deep learning holds the 4-layer picture network, {net_n:,} learned '
          f'numbers')
    print(f'[nest] foundation models are deep models of the size of the 48-block '
          f'stack, {big_n:,} learned numbers, trained once and then adapted')

    fig, ax = plt.subplots(figsize=(11.8, 5.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    rings = [
        (0.03, 0.030, 0.940, 0.940, LINK, 'artificial intelligence',
         'the joint-limit check: 0 learned numbers'),
        (0.10, 0.095, 0.800, 0.740, PURPLE, 'machine learning',
         f'the fitted wrist-sag line: {line_n} learned numbers'),
        (0.17, 0.160, 0.660, 0.540, TEAL, 'deep learning',
         f'the 64 by 64 picture network: {net_n:,} learned numbers'),
        (0.24, 0.225, 0.520, 0.340, GRIP, 'foundation models',
         f'the 48-block stack: {big_n:,} learned numbers'),
    ]
    for x, y, w, h, colour, name, body in rings:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=0.085,
                               edgecolor=colour, lw=2.0, zorder=2))
        ax.text(x + 0.016, y + h - 0.040, name, fontsize=13.5, weight='bold',
                color=colour, va='center')
        ax.text(x + 0.016, y + h - 0.082, body, fontsize=10.4, color=INK, va='center')
    ax.set_title('Each name is inside the one before it, and the count of learned '
                 'numbers grows at every step', fontsize=12.5, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'four-names-nested.svg')


def _mlp_fit(x: Arr, y: Arr, hidden: list[int], seed: int, steps: int = 3000,
             lr: float = 0.02) -> tuple[list[list[Arr]], int]:
    """Train a rectified-linear network of the given hidden widths with Adam."""
    rng = np.random.default_rng(seed)
    sizes = [1] + hidden + [1]
    ps: list[list[Arr]] = []
    for a, b in zip(sizes[:-1], sizes[1:]):
        ps.append([rng.normal(0, np.sqrt(2.0 / a), (a, b)), np.zeros(b)])
    n_par = int(sum(W.size + bb.size for W, bb in ps))
    mom = [[np.zeros_like(W), np.zeros_like(bb)] for W, bb in ps]
    vel = [[np.zeros_like(W), np.zeros_like(bb)] for W, bb in ps]
    X = x[:, None]
    Y = y[:, None]
    for it in range(1, steps + 1):
        acts = [X]
        h = X
        for i, (W, bb) in enumerate(ps):
            z = h @ W + bb
            h = np.maximum(z, 0.0) if i < len(ps) - 1 else z
            acts.append(h)
        g = 2.0 * (acts[-1] - Y) / len(X)
        for i in reversed(range(len(ps))):
            W, bb = ps[i]
            gW = acts[i].T @ g
            gb = g.sum(0)
            if i > 0:
                g = (g @ W.T) * (acts[i] > 0)
            for k, (grad, par) in enumerate(((gW, W), (gb, bb))):
                mom[i][k] = 0.9 * mom[i][k] + 0.1 * grad
                vel[i][k] = 0.999 * vel[i][k] + 0.001 * grad ** 2
                step = (lr * (mom[i][k] / (1 - 0.9 ** it))
                        / (np.sqrt(vel[i][k] / (1 - 0.999 ** it)) + 1e-8))
                par -= step
    return ps, n_par


def _mlp_eval(ps: list[list[Arr]], x: Arr) -> Arr:
    h = x[:, None]
    for i, (W, bb) in enumerate(ps):
        z = h @ W + bb
        h = np.maximum(z, 0.0) if i < len(ps) - 1 else z
    return h[:, 0]


def depth_helps() -> None:
    """What the word deep buys: the same width, more layers, on one simulated job."""
    rng = np.random.default_rng(101)
    truth = lambda t: np.sin(6.0 * t) * np.exp(-1.1 * t) + 0.3 * t  # noqa: E731
    x = rng.uniform(0, 2, 220)
    y = truth(x) + rng.normal(0, 0.02, len(x))
    xt = np.linspace(0, 2, 400)
    yt = truth(xt)
    shapes = [([12], 'one hidden layer'), ([12, 12], 'two hidden layers'),
              ([12, 12, 12], 'three'), ([12, 12, 12, 12], 'four'),
              ([12] * 5, 'five')]
    errs, pars, curves = [], [], []
    for hidden, _name in shapes:
        ps, n_par = _mlp_fit(x, y, hidden, seed=7)
        pred = _mlp_eval(ps, xt)
        errs.append(float(np.sqrt(np.mean((pred - yt) ** 2))))
        pars.append(n_par)
        curves.append(pred)
    for (hidden, name), e, p in zip(shapes, errs, pars):
        print(f'[depth] {len(hidden)} hidden layers of 12, {p:4d} parameters: '
              f'typical miss on unseen inputs {e:.4f}')
    best = int(np.argmin(errs))
    print(f'[depth] the best is {len(shapes[best][0])} hidden layers at {errs[best]:.4f}, '
          f'which is {errs[0] / errs[best]:.1f} times better than one layer')

    fig, ax = plt.subplots(figsize=(10.2, 5.2), facecolor='white')
    _plain(ax)
    ax.plot([len(h) for h, _n in shapes], errs, marker='o', color=TEAL, lw=2.2)
    for i, ((hidden, _n), e, p) in enumerate(zip(shapes, errs, pars)):
        off = (0, 13) if i < 2 else (0, -26)
        ax.annotate(f'{p}\nparameters', (len(hidden), e), fontsize=8.8, ha='center',
                    color=MUTED, textcoords='offset points', xytext=off)
    ax.set_yscale('log')
    ax.set_xlim(0.55, 5.45)
    ax.set_ylim(min(errs) * 0.38, max(errs) * 2.4)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel('number of hidden layers, each 12 neurons wide', fontsize=10.5)
    ax.set_ylabel('typical miss on unseen inputs (log scale)', fontsize=10.5)
    ax.set_title(f'Stacking layers of the same width cuts the miss '
                 f'{errs[0] / errs[best]:.1f} times on one simulated job',
                 fontsize=11.6, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'depth-helps.svg')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(xt, yt, color=INK, lw=1.6, ls='--', label='the shape to be matched')
    ax.plot(xt, curves[0], color=GRIP, lw=1.9,
            label=f'1 hidden layer, miss {errs[0]:.3f}')
    ax.plot(xt, curves[best], color=SLIDE, lw=1.9,
            label=f'{len(shapes[best][0])} hidden layers, miss {errs[best]:.3f}')
    ax.scatter(x[:60], y[:60], s=12, color=MUTED, alpha=0.7,
               label='60 of the 220 examples')
    ax.set_ylim(-0.4, 1.35)
    ax.set_xlabel('input', fontsize=10.5)
    ax.set_ylabel('output', fontsize=10.5)
    ax.set_title('The three-layer network follows the bends that the one-layer '
                 'network rounds off', fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.4, frameon=False, loc='upper right')
    _save(fig, WORDS_DOC, 'deep-curve-follows-bends.svg')


def one_model_many_jobs() -> None:
    """Why a foundation model is worth training once: the shared part dwarfs the rest."""
    cases = _param_cases()
    shared = cases[3][1]
    width = 2048
    heads = [('name the object\n(500 kinds)', width * 500 + 500),
             ('full or empty cup\n(2 kinds)', width * 2 + 2),
             ('where to put the fingers\n(3 numbers)', width * 3 + 3)]
    total_heads = sum(n for _l, n in heads)
    for lab, n in heads:
        print(f'[found] a head for "{lab.replace(chr(10), " ")}": {n:,} new parameters, '
              f'{100.0 * n / shared:.5f} per cent of the shared part')
    print(f'[found] shared part {shared:,} parameters; all three heads together '
          f'{total_heads:,}, which is {shared / total_heads:,.0f} times smaller')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    labs = ['the shared part,\ntrained once'] + [h[0] for h in heads]
    vals = [shared] + [n for _l, n in heads]
    ax.bar(range(4), vals, color=[GRIP, LINK, PURPLE, TEAL], alpha=0.85,
           edgecolor=INK, lw=0.6, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v * 2.0, f'{v:,}', ha='center', fontsize=10.6, weight='bold',
                color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1e2, shared * 60)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labs, fontsize=9.5)
    ax.set_ylabel('number of parameters (log scale)', fontsize=10.5)
    ax.set_title(f'A foundation model earns its cost by being shared: each new job adds '
                 f'about {shared / total_heads:,.0f} times fewer parameters',
                 fontsize=11.4, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'one-model-many-jobs.svg')


# ==========================================================================
# PAGE 2, SECTION 6: every word on one job
# ==========================================================================

def words_on_one_job() -> None:
    """Every word of the page placed on the cup job, with that job's real numbers."""
    c = _cups()
    m = _cup_model()
    w = np.asarray(m['w'])
    print(f'[job] dataset: {c.n} examples, each 3 features and 1 label; '
          f'{c.split} for training, {c.n - c.split} held back')
    print(f'[job] model: 3 weights and 1 offset, so 4 parameters')
    print(f'[job] training: 400 steps; inference: 1 pass giving one number')
    print(f'[job] generalisation: {float(m["acc_test"]):.3f} on the held-back half')

    fig, ax = plt.subplots(figsize=(12.6, 5.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    stages = [
        (0.015, 'dataset', LINK,
         f'{c.n:,} examples\neach one: 3 features\nand 1 label (full or empty)\n'
         f'{c.split} trained on, {c.n - c.split} held back'),
        (0.265, 'training', GRIP,
         f'400 steps\neach step changes all\n4 parameters a little\n'
         f'score of being wrong falls\nfrom {m["hist"][0]:.3f} to {m["hist"][-1]:.3f}'),
        (0.515, 'the model', PURPLE,
         f'3 weights:\n{w[0]:+.2f}  {w[1]:+.2f}  {w[2]:+.2f}\n'
         f'1 offset: {float(m["b"]):+.2f}\n4 parameters in all'),
        (0.765, 'inference', SLIDE,
         f'one new cup in,\none number out,\nthen "full" above 0.5\n'
         f'right on {float(m["acc_test"]):.3f} of the\nheld-back cups'),
    ]
    for x, name, colour, body in stages:
        _box(ax, x, 0.17, 0.22, 0.56, colour, alpha=0.12)
        ax.text(x + 0.11, 0.665, name, fontsize=13, weight='bold', color=colour,
                ha='center')
        ax.text(x + 0.11, 0.42, body, fontsize=9.8, color=INK, ha='center',
                va='center')
    for x in (0.235, 0.485, 0.735):
        _arrow(ax, x, 0.45, x + 0.028, 0.45, colour=INK, lw=1.6)
    ax.text(0.50, 0.08, f'generalisation is the word for {float(m["acc_test"]):.3f} on '
                        f'cups it never saw being almost as good as '
                        f'{float(m["acc_train"]):.3f} on the ones it trained on',
            fontsize=10.5, color=INK, ha='center')
    ax.set_title('The whole vocabulary on one job: telling a full cup from an empty one',
                 fontsize=12.8, weight='bold', color=INK, pad=14)
    _save(fig, WORDS_DOC, 'words-on-one-job.svg')


def cup_training_run() -> None:
    """The cup model's own training run, and what it scores on both halves."""
    c = _cups()
    m = _cup_model()
    hist = list(m['hist'])
    print(f'[cupfit] score of being wrong: step 0 {hist[0]:.4f}, step 50 {hist[50]:.4f}, '
          f'step 200 {hist[200]:.4f}, step 399 {hist[-1]:.4f}')
    print(f'[cupfit] accuracy {float(m["acc_train"]):.3f} on the training half, '
          f'{float(m["acc_test"]):.3f} on the held-back half')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(np.arange(len(hist)), hist, color=GRIP, lw=2.2)
    for k in (0, 50, 200, 399):
        ax.scatter([k], [hist[k]], s=42, color=INK, zorder=6)
        ax.annotate(f'{hist[k]:.3f}', (k, hist[k]), fontsize=9.8, color=INK,
                    textcoords='offset points', xytext=(8, 8))
    ax.set_xlabel('training step', fontsize=10.5)
    ax.set_ylabel('score of being wrong (lower is better)', fontsize=10.5)
    ax.set_title('Training the cup model: 400 steps, each one changing all 4 '
                 'parameters', fontsize=11.6, weight='bold', color=INK)
    _save(fig, WORDS_DOC, 'train-and-run-the-cup-model.svg')


def cup_model_answers() -> None:
    """Inference 800 times over: the one number the model gives each held-back cup."""
    m = _cup_model()
    pte = np.asarray(m['pte'])
    yte = np.asarray(m['yte'])
    wrong = int(((pte > 0.5).astype(float) != yte).sum())
    print(f'[answers] of the {len(yte)} held-back cups the model calls '
          f'{int((pte > 0.5).sum())} full, and {wrong} of its answers are wrong')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    bins = np.linspace(0, 1, 26)
    ax.hist(pte[yte < 0.5], bins=bins, color=TEAL, alpha=0.65, label='empty cups')
    ax.hist(pte[yte > 0.5], bins=bins, color=GRIP, alpha=0.65, label='full cups')
    ax.axvline(0.5, color=INK, ls='--', lw=1.4)
    ax.text(0.52, ax.get_ylim()[1] * 0.45, 'called full above 0.5', fontsize=9.8,
            color=INK, rotation=90, va='center')
    ax.set_xlabel('the one number the model gives for a held-back cup', fontsize=10.5)
    ax.set_ylabel('number of cups', fontsize=10.5)
    ax.set_title(f'Inference, 800 times over: {wrong} of the answers fall on the wrong '
                 f'side of 0.5', fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.8, frameon=False, loc='upper left',
              bbox_to_anchor=(0.14, 1.0))
    _save(fig, WORDS_DOC, 'cup-model-answers.svg')


def which_word_when() -> None:
    """The parameters move during training and are frozen during inference."""
    c = _cups()
    cols = np.stack([c.inside, c.spread, c.wall], axis=1)
    mu, sd = cols[:c.split].mean(0), cols[:c.split].std(0)
    Xtr = (cols[:c.split] - mu) / sd
    ytr = c.full[:c.split]
    track = []
    for steps in [1, 5, 10, 20, 40, 80, 150, 250, 400]:
        w, b, _h = _logistic_fit(Xtr, ytr, steps=steps)
        track.append((steps, w.copy(), b))
    for steps, w, b in track:
        print(f'[freeze] after {steps:3d} steps: weights {w[0]:+.3f} {w[1]:+.3f} '
              f'{w[2]:+.3f}, offset {b:+.3f}')

    fig, ax = plt.subplots(figsize=(11.2, 5.2), facecolor='white')
    _plain(ax)
    xs = [t[0] for t in track]
    names = ['weight on the brightness inside the rim',
             'weight on the spread of that brightness',
             'weight on the brightness of the cup wall']
    for j, (name, colour) in enumerate(zip(names, (LINK, JOINT, PURPLE))):
        ax.plot(xs, [t[1][j] for t in track], marker='o', color=colour, lw=2.0,
                label=name)
    ax.plot(xs, [t[2] for t in track], marker='s', color=MUTED, lw=1.6,
            label='the offset')
    ax.axvline(400, color=INK, lw=1.4)
    ax.axvspan(400, 900, color='#eef4ea', zorder=0)
    ax.text(650, 4.85, 'training has stopped, so these four\nnumbers never change '
                       'again',
            fontsize=10.5, color=SLIDE, ha='center', va='center')
    for j, colour in enumerate((LINK, JOINT, PURPLE)):
        ax.plot([400, 900], [track[-1][1][j]] * 2, color=colour, lw=2.0, ls=':')
    ax.plot([400, 900], [track[-1][2]] * 2, color=MUTED, lw=1.6, ls=':')
    ax.set_xlim(0, 900)
    ax.set_ylim(-12.0, 7.8)
    ax.set_xlabel('training step (the shaded part is after training, during inference)',
                  fontsize=10.5)
    ax.set_ylabel('the value of that parameter', fontsize=10.5)
    ax.set_title('The same four numbers are called parameters throughout, but they only '
                 'move during training', fontsize=11.6, weight='bold', color=INK)
    ax.legend(fontsize=9.2, frameon=False, loc='lower left', ncol=2)
    _save(fig, WORDS_DOC, 'which-word-when.svg')


# ==========================================================================

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)

    # page 1
    switch_count()
    mm_to_m()
    joint_limit()
    glass_pixels()
    threshold_sweep()
    spoon_finger_places()
    full_or_empty_cup()
    two_numbers_separate_cups()
    how_many_pictures()
    rules_stack_up()
    one_answer_per_input()
    both_answers_at_one_input()
    sag_points()
    fit_arithmetic()
    error_vs_slope()
    signed_misses_cancel()
    squaring_punishes_big_misses()
    three_answers()
    one_example()
    prediction_vs_label()
    feature_choice()
    label_noise()
    outside_the_range()
    more_examples_less_error()
    one_bad_example()

    # page 2
    two_numbers_inside()
    parameter_count()
    weights_are_dials()
    model_file_size()
    training_curve()
    parameters_walking()
    training_vs_inference_cost()
    one_inference_by_hand()
    dataset_split()
    seen_vs_unseen()
    flexible_curve_wanders()
    generalisation_vs_size()
    supervised_labels()
    self_supervised_gap()
    reinforcement_tries()
    reinforcement_heights()
    three_signals_cost()
    four_names_nested()
    depth_helps()
    one_model_many_jobs()
    words_on_one_job()
    cup_training_run()
    cup_model_answers()
    which_word_when()

    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
