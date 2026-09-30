"""Generate the diagrams used in docs/05_neural-network-models/07_world-models/.

Each document's pictures go to a folder named after it, under
docs/images/world-models/.

Run with:  pixi run python ../docs/diagrams/world_models.py
or:        python3 docs/diagrams/world_models.py --png <folder>

Every picture is a drawing of one idea. The positions, paths and small numbers
in them are made up to show the idea; none of them is a measured result, and the
documents say so where it matters.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'world-models'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
TABLE: str = '#efe6d8'
TABLE_EDGE: str = '#b89f7a'
PALE_GREEN: str = '#e2f3e5'
PALE_RED: str = '#fbe4e4'
PALE_GREY: str = '#f2f2f2'
PURPLE: str = '#7b5aa6'

RNG = np.random.default_rng(7)


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, style: str = '-|>', ls: str = '-', z: int = 6) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw, 'ls': ls,
                            'shrinkA': 0, 'shrinkB': 0, 'mutation_scale': 14}, zorder=z)


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = 'white',
         edge: str = INK, lw: float = 1.2, ls: str = '-', z: int = 1) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                                facecolor=face, edgecolor=edge, lw=lw, ls=ls, zorder=z))


def _net(ax: Axes, cx: float, cy: float, w: float = 1.4, h: float = 1.2,
         layers: tuple[int, ...] = (3, 4, 4, 3), color: str = PURPLE) -> None:
    """A small neural network: columns of circles joined by thin lines."""
    xs = np.linspace(cx - w / 2, cx + w / 2, len(layers))
    cols: list[list[tuple[float, float]]] = []
    for x, n in zip(xs, layers):
        ys = np.linspace(cy - h / 2, cy + h / 2, n) if n > 1 else np.array([cy])
        cols.append([(float(x), float(y)) for y in ys])
    for a, b in zip(cols, cols[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRID, lw=0.6, zorder=2)
    r = min(0.08, h / (max(layers) * 3.2))
    for col in cols:
        for p in col:
            ax.add_patch(Circle(p, r, facecolor='white', edgecolor=color, lw=1.4, zorder=3))


def _table_side(ax: Axes, x0: float, x1: float, y: float = 0.0, legs: bool = True) -> None:
    ax.add_patch(Rectangle((x0, y - 0.12), x1 - x0, 0.12, facecolor=TABLE,
                           edgecolor=TABLE_EDGE, lw=1.0, zorder=1))
    if legs:
        for lx in (x0 + 0.15, x1 - 0.25):
            ax.add_patch(Rectangle((lx, y - 0.9), 0.1, 0.78, facecolor=TABLE,
                                   edgecolor=TABLE_EDGE, lw=1.0, zorder=1))


def _mug(ax: Axes, x: float, y: float, w: float = 0.42, h: float = 0.5, angle: float = 0.0,
         color: str = LINK, alpha: float = 1.0, ls: str = '-') -> None:
    """A mug seen from the side. (x, y) is the middle of its bottom edge."""
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def rot(px: float, py: float) -> tuple[float, float]:
        return (x + px * c - py * s, y + px * s + py * c)

    body = [rot(-w / 2, 0), rot(w / 2, 0), rot(w / 2, h), rot(-w / 2, h)]
    ax.add_patch(Polygon(body, closed=True, facecolor=color, edgecolor=INK, lw=1.0,
                         alpha=alpha, ls=ls, zorder=4))
    hc = rot(w / 2, h * 0.5)
    ax.add_patch(Arc(hc, h * 0.5, h * 0.55, angle=angle, theta1=-90, theta2=90,
                     color=INK if alpha > 0.6 else MUTED, lw=2.2, zorder=3, ls=ls))


def _gripper_side(ax: Axes, x: float, y: float, open_w: float = 0.5, color: str = GRIP,
                  alpha: float = 1.0) -> None:
    """A parallel gripper seen from the side, fingers pointing down, tips at y."""
    ax.plot([x, x], [y + 0.35, y + 0.9], color=MUTED, lw=4, alpha=alpha, zorder=5,
            solid_capstyle='butt')
    ax.plot([x - open_w / 2, x + open_w / 2], [y + 0.35, y + 0.35], color=color, lw=4,
            alpha=alpha, zorder=5, solid_capstyle='round')
    for sx in (-open_w / 2, open_w / 2):
        ax.plot([x + sx, x + sx], [y, y + 0.35], color=color, lw=4, alpha=alpha, zorder=5,
                solid_capstyle='round')


def _cube_top(ax: Axes, x: float, y: float, size: float = 0.5, angle: float = 0.0,
              color: str = WRIST, ls: str = '-', alpha: float = 1.0, fill: bool = True,
              z: int = 4) -> None:
    """A cube seen from above: a square centred on (x, y)."""
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    h = size / 2
    pts = [(x + dx * c - dy * s, y + dx * s + dy * c)
           for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h))]
    ax.add_patch(Polygon(pts, closed=True, facecolor=color if fill else 'none',
                         edgecolor=INK if fill else color, lw=1.4, ls=ls, alpha=alpha,
                         zorder=z))


def _table_top(ax: Axes, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=TABLE, edgecolor=TABLE_EDGE,
                           lw=1.2, zorder=0))


def _cells(ax: Axes, x: float, y: float, values: list[float], cell: float = 0.32,
           show: bool = True, size: float = 8, alpha: float = 1.0) -> None:
    """A short list of numbers drawn as a column of coloured cells, top to bottom."""
    cmap = plt.get_cmap('RdBu_r')
    for i, v in enumerate(values):
        cy = y - i * cell
        col = cmap(0.5 + max(-1.0, min(1.0, v / 2.0)) * 0.4)
        ax.add_patch(Rectangle((x, cy - cell), cell * 1.9, cell, facecolor=col,
                               edgecolor=INK, lw=0.8, alpha=alpha, zorder=4))
        if show:
            _label(ax, x + cell * 0.95, cy - cell / 2, f'{v:+.1f}', size=size)


def _frame(ax: Axes, img: NDArray[np.float64], x: float, y: float, w: float,
           edge: str = INK, lw: float = 1.2, ls: str = '-') -> None:
    """Draw an RGB picture (rows, cols, 3) as pixels, with its bottom-left at (x, y)."""
    h = w * img.shape[0] / img.shape[1]
    ax.imshow(img, extent=(x, x + w, y, y + h), interpolation='nearest', zorder=3)
    ax.add_patch(Rectangle((x, y), w, h, facecolor='none', edgecolor=edge, lw=lw, ls=ls,
                           zorder=4))


def _hex(c: str) -> NDArray[np.float64]:
    c = c.lstrip('#')
    return np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def _scene(n: int, cube: tuple[float, float] | None, grip: tuple[float, float] | None,
           bowl: tuple[float, float] | None = None, cube_alpha: float = 1.0) -> NDArray[np.float64]:
    """A small top-down camera picture, n x n pixels: table, cube, gripper, bowl.

    Positions are in pixels (column, row from the top)."""
    img = np.ones((n, n, 3)) * _hex(TABLE)
    if bowl is not None:
        for r in range(n):
            for c in range(n):
                d = math.hypot(c - bowl[0], r - bowl[1])
                if 1.6 <= d <= 2.6:
                    img[r, c] = _hex('#8a8a8a')
    if cube is not None:
        for r in range(n):
            for c in range(n):
                if abs(c - cube[0]) <= 1.01 and abs(r - cube[1]) <= 1.01:
                    img[r, c] = cube_alpha * _hex(GRIP) + (1 - cube_alpha) * img[r, c]
    if grip is not None:
        gx, gy = int(round(grip[0])), int(round(grip[1]))
        for c in (gx - 2, gx + 2):
            for r in (gy - 1, gy, gy + 1):
                if 0 <= r < n and 0 <= c < n:
                    img[r, c] = _hex('#555555')
        for c in range(gx - 2, gx + 3):
            if 0 <= gy - 1 < n and 0 <= c < n:
                img[gy - 1, c] = _hex('#555555')
    return img


def _blur(img: NDArray[np.float64], passes: int) -> NDArray[np.float64]:
    out = img.copy()
    for _ in range(passes):
        p = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode='edge')
        out = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 2 * p[1:-1, 1:-1]) / 6
    return out


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _fig(w: float, h: float) -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=(w, h), facecolor='white')
    return fig, ax


# --------------------------------------------------------------------------
# 01_overview.md
# --------------------------------------------------------------------------

def predict_then_choose() -> None:
    """A mug near the table edge, three possible pushes, and the predicted result of each."""
    fig, ax = _fig(12, 6.4)
    _axes(ax, (-0.3, 14.2), (-2.6, 6.1))

    # the scene now
    _title(ax, 1.9, 5.8, 'Now')
    _table_side(ax, 0.0, 3.4, y=2.0)
    _mug(ax, 2.7, 2.0)
    _gripper_side(ax, 1.6, 2.1, open_w=0.45)
    _label(ax, 1.9, 0.6, 'a mug close to\nthe table edge', color=MUTED)

    # the model
    _net(ax, 5.5, 2.3, w=1.3, h=1.3)
    _label(ax, 5.5, 3.5, 'world model', weight='bold', color=PURPLE)
    _label(ax, 5.5, 0.95, 'asked: "what happens\nif I do this?"', size=9, color=MUTED)
    _arrow(ax, (3.7, 2.3), (4.65, 2.3))

    rows = [(4.0, 'push right 10 cm', 'falls off the table', False),
            (1.2, 'push left 10 cm', 'moves to the middle', True),
            (-1.6, 'close gripper, lift', 'lifted safely', True)]
    for yc, action, result, good in rows:
        _arrow(ax, (6.35, 2.3), (7.55, yc + 0.35), color=MUTED, lw=1.2)
        _label(ax, 9.0, yc + 1.1, action, size=9.5, weight='bold')
        face = PALE_GREEN if good else PALE_RED
        edge = SLIDE if good else GRIP
        _box(ax, 7.6, yc - 0.55, 2.8, 1.25, face=face, edge=edge)
        if action.startswith('push right'):
            _table_side(ax, 7.8, 9.3, y=yc - 0.1, legs=False)
            _mug(ax, 9.75, yc - 0.5, angle=-60, alpha=0.9)
            _gripper_side(ax, 8.6, yc - 0.05, open_w=0.4, alpha=0.5)
        elif action.startswith('push left'):
            _table_side(ax, 7.8, 10.2, y=yc - 0.1, legs=False)
            _mug(ax, 8.7, yc - 0.1)
            _gripper_side(ax, 9.45, yc - 0.05, open_w=0.4, alpha=0.5)
        else:
            _table_side(ax, 7.8, 10.2, y=yc - 0.1, legs=False)
            _mug(ax, 9.0, yc - 0.02)
            _gripper_side(ax, 9.0, yc + 0.03, open_w=0.55)
        _label(ax, 10.7, yc + 0.1, result, size=9.5, ha='left', color=edge)
    _title(ax, 9.0, 5.8, 'Predicted result of each action')
    _label(ax, 12.2, -2.35, 'The arm then does one of the green ones.', size=9.5,
           color=MUTED)
    _save(fig, 'overview', 'predict-then-choose.svg')


def four_kinds() -> None:
    """What each of the four kinds of world model predicts, drawn side by side."""
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.6), facecolor='white')
    titles = ['Learned dynamics model', 'Video prediction model', 'Learned simulator',
              'Latent world model']
    subs = ['predicts a few numbers\nabout each object', 'predicts the next\ncamera pictures',
            'predicts where every small\npiece of cloth or liquid goes',
            'predicts a short code\nthat stands for the scene']
    for ax, t, s in zip(axes, titles, subs):
        _axes(ax, (0, 4), (0, 4.2))
        _title(ax, 2, 3.95, t, size=11.5)
        _label(ax, 2, 0.35, s, size=9.5, color=MUTED)

    # 1. dynamics: numbers about a cube
    ax = axes[0]
    _table_top(ax, 0.2, 1.1, 3.8, 3.4)
    _cube_top(ax, 1.1, 2.5, 0.55)
    _cube_top(ax, 2.7, 2.5, 0.55, angle=20, color=WRIST, ls='--', fill=False)
    _arrow(ax, (1.5, 2.5), (2.3, 2.5), color=MUTED)
    _label(ax, 1.1, 1.6, 'x 0.30 m\ny 0.20 m', size=8.5)
    _label(ax, 2.7, 1.6, 'x 0.42 m\ny 0.20 m', size=8.5, color=WRIST)

    # 2. video: frames
    ax = axes[1]
    frames = [_scene(12, (6, 7), (6, 10)), _scene(12, (6, 5.5), (6, 8.5)),
              _blur(_scene(12, (6, 4), (6, 7)), 1)]
    for i, f in enumerate(frames):
        edge = LINK if i == 2 else INK
        _frame(ax, f, 0.2 + i * 1.25, 1.4, 1.1, edge=edge, lw=2.0 if i == 2 else 1.2,
               ls='--' if i == 2 else '-')
    _label(ax, 0.75, 2.85, 'before', size=8.5, color=MUTED)
    _label(ax, 2.0, 2.85, 'now', size=8.5, color=MUTED)
    _label(ax, 3.25, 2.85, 'predicted', size=8.5, color=LINK)

    # 3. simulator: cloth particles
    ax = axes[2]
    xs = np.linspace(0.4, 3.6, 9)
    now_y = np.full_like(xs, 2.9)
    nxt_y = 1.7 + 0.12 * ((xs - 2.0) ** 2) - 0.05
    for yy, col, ls in ((now_y, MUTED, '-'), (nxt_y, LINK, '--')):
        ax.plot(xs, yy, color=col, lw=1.2, ls=ls, zorder=2)
        ax.plot(xs, yy, 'o', color=col, ms=6, zorder=3)
    for x, a, b in zip(xs[::2], now_y[::2], nxt_y[::2]):
        _arrow(ax, (x, a - 0.12), (x, b + 0.14), color=GRID, lw=1.0)
    _label(ax, 2.0, 3.25, 'cloth now', size=8.5, color=MUTED)
    _label(ax, 2.0, 1.35, 'cloth next', size=8.5, color=LINK)

    # 4. latent: picture -> short code -> next code
    ax = axes[3]
    _frame(ax, _scene(12, (6, 6), (6, 9)), 0.15, 1.55, 1.1)
    _arrow(ax, (1.35, 2.1), (1.65, 2.1), color=MUTED)
    _cells(ax, 1.7, 3.0, [0.8, -1.2, 0.3, 1.5, -0.4], cell=0.3, size=7)
    _arrow(ax, (2.35, 2.1), (2.8, 2.1), color=MUTED)
    _cells(ax, 2.85, 3.0, [0.9, -1.0, 0.1, 1.6, -0.9], cell=0.3, size=7)
    _label(ax, 2.0, 3.25, 'code now', size=8.5, color=MUTED)
    _label(ax, 3.4, 3.25, 'code next', size=8.5, color=PURPLE)
    fig.subplots_adjust(wspace=0.12)
    _save(fig, 'overview', 'four-kinds.svg')


# --------------------------------------------------------------------------
# 02_learned-dynamics-models.md
# --------------------------------------------------------------------------

def state_action_next_state() -> None:
    """Numbers for the state and the action go in; numbers for the next state come out."""
    fig, ax = _fig(13, 4.8)
    _axes(ax, (-0.2, 14.4), (-0.6, 4.6))

    _title(ax, 1.9, 4.3, 'State now + action')
    _table_top(ax, 0.1, 0.8, 3.7, 3.7)
    _cube_top(ax, 1.4, 2.25, 0.6)
    ax.add_patch(Circle((0.55, 2.25), 0.16, facecolor=GRIP, edgecolor=INK, zorder=5))
    _arrow(ax, (0.75, 2.25), (1.05, 2.25), color=GRIP, lw=2.2)
    _arrow(ax, (1.8, 2.25), (2.9, 2.25), color=GRIP, lw=2.2, ls='--')
    _label(ax, 2.35, 2.6, 'push 10 cm', size=9, color=GRIP)
    _label(ax, 1.9, 0.3, 'cube: x = 0.30 m, y = 0.20 m, turned 0°\n'
                         'action: push along x by 0.10 m', size=9)

    _arrow(ax, (3.95, 2.25), (5.15, 2.25))
    _net(ax, 6.0, 2.25, w=1.5, h=1.6, layers=(4, 5, 5, 3))
    _label(ax, 6.0, 3.5, 'dynamics model', weight='bold', color=PURPLE)
    _label(ax, 6.0, 0.95, '4 numbers in,\n3 numbers out', size=9, color=MUTED)
    _arrow(ax, (6.9, 2.25), (8.1, 2.25))

    _title(ax, 10.2, 4.3, 'Predicted next state')
    _table_top(ax, 8.3, 0.8, 12.1, 3.7)
    _cube_top(ax, 10.55, 2.1, 0.6, angle=8)
    _cube_top(ax, 10.3, 2.35, 0.6, angle=15, color=LINK, ls='--', fill=False, z=6)
    _label(ax, 10.2, 3.35, 'blue dashed: predicted', size=8.5, color=LINK)
    _label(ax, 10.2, 1.3, 'orange: what really happened', size=8.5, color=WRIST)
    _label(ax, 10.2, 0.3, 'predicted: x = 0.38 m, y = 0.21 m, turned 15°', size=9, color=LINK)
    _label(ax, 13.3, 2.25, 'the gap\nbetween them\nis the error\nused in\ntraining', size=9,
           color=MUTED)
    _save(fig, 'learned-dynamics-models', 'state-action-next-state.svg')


def rolling_forward() -> None:
    """Chaining one-step predictions: small errors add up, and an ensemble spreads out."""
    fig, ax = _fig(10, 5)
    steps = np.arange(0, 21)
    true = 0.9 * np.sin(steps / 6.0) + steps * 0.05
    ax.plot(steps, true, color=INK, lw=2.4, label='what really happens', zorder=4)
    for k in range(5):
        drift = RNG.normal(0, 0.028, size=steps.size).cumsum() * (1 + 0.15 * k)
        drift += (k - 2) * 0.004 * steps ** 1.5
        drift[0] = 0.0
        ax.plot(steps, true + drift, color=LINK, lw=1.2, ls='--', alpha=0.9,
                label='five model copies, each chaining\nits own predictions' if k == 0 else None,
                zorder=3)
    ax.axvspan(0, 3, color=PALE_GREEN, zorder=0)
    ax.axvspan(14, 20, color=PALE_RED, zorder=0)
    ax.text(1.5, 2.55, 'close', ha='center', fontsize=9.5, color=SLIDE)
    ax.text(17, 2.55, 'far apart: do not\ntrust this part', ha='center', fontsize=9.5,
            color=GRIP)
    ax.set_xlim(0, 20)
    ax.set_ylim(-0.6, 3.0)
    ax.set_xlabel('steps into the future', fontsize=10, color=INK)
    ax.set_ylabel('cube position along the table', fontsize=10, color=INK)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_yticks([])
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.legend(loc='lower right', fontsize=9, frameon=False)
    _save(fig, 'learned-dynamics-models', 'rolling-forward.svg')


def try_many_plans() -> None:
    """Planning with a dynamics model: imagine many pushes, keep the best, do its first step."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    _axes(ax, (-0.2, 6.2), (-0.7, 5.0))
    _title(ax, 3.0, 4.7, '1. Imagine many action sequences')
    _table_top(ax, 0, 0, 6, 4.3)
    start = np.array([1.0, 1.2])
    goal = np.array([4.8, 3.2])
    best = None
    best_d = 1e9
    paths = []
    while len(paths) < 14:
        heading = RNG.uniform(-0.35, 1.1)
        turn = RNG.normal(0, 0.12, 6).cumsum()
        pts = [start.copy()]
        for t in range(6):
            a = heading + turn[t]
            pts.append(pts[-1] + 0.58 * np.array([math.cos(a), math.sin(a)]))
        p = np.array(pts)
        if p[:, 1].min() < 0.2 or p[:, 1].max() > 4.0 or p[:, 0].max() > 5.8:
            continue
        paths.append(p)
        d = float(np.linalg.norm(p[-1] - goal))
        if d < best_d:
            best_d, best = d, p
    for p in paths:
        if p is best:
            continue
        ax.plot(p[:, 0], p[:, 1], color=MUTED, lw=1.0, alpha=0.7, zorder=2)
        ax.plot(p[-1, 0], p[-1, 1], 'o', color=MUTED, ms=3.5, zorder=2)
    assert best is not None
    ax.plot(best[:, 0], best[:, 1], color=SLIDE, lw=2.8, zorder=3)
    ax.plot(best[-1, 0], best[-1, 1], 'o', color=SLIDE, ms=6, zorder=3)
    _cube_top(ax, start[0], start[1], 0.5, z=5)
    ax.plot(goal[0], goal[1], marker='*', color=JOINT, ms=22, markeredgecolor=INK, zorder=4)
    _label(ax, goal[0], goal[1] + 0.45, 'goal', size=9.5)
    _label(ax, start[0], start[1] - 0.55, 'cube', size=9.5)
    _label(ax, 3.0, -0.4, 'grey: imagined by the model   green: ends closest to the goal',
           size=9, color=MUTED)

    ax = axes[1]
    _axes(ax, (-0.2, 5.2), (-0.7, 5.0))
    _title(ax, 2.5, 4.7, '2. Do only the first step, then look again')
    _table_top(ax, 0, 0, 5, 4.3)
    shift = np.array([0.0, 0.0]) - start + np.array([1.0, 1.2])
    b = best + shift
    ax.plot(b[1:, 0], b[1:, 1], color=SLIDE, lw=1.4, ls=':', zorder=2)
    _arrow(ax, (b[0, 0], b[0, 1]), (b[1, 0], b[1, 1]), color=SLIDE, lw=3.0)
    _cube_top(ax, b[0, 0], b[0, 1], 0.5, z=5)
    _cube_top(ax, b[1, 0] + 0.05, b[1, 1] - 0.08, 0.5, color=WRIST, ls='--', fill=False, z=5)
    _label(ax, b[1, 0] + 0.35, b[1, 1] - 0.62, 'where the cube\nreally went', size=9,
           color=WRIST, ha='left')
    _label(ax, 2.5, -0.4, 'dotted: the rest of the plan is thrown away and planned again',
           size=9, color=MUTED)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'learned-dynamics-models', 'try-many-plans.svg')


# --------------------------------------------------------------------------
# 03_video-prediction-models.md
# --------------------------------------------------------------------------

def frames_in_frames_out() -> None:
    """Past camera pictures and planned actions go in; future pictures come out, blurrier."""
    fig, ax = _fig(14, 4.2)
    _axes(ax, (-0.2, 15.2), (-0.9, 3.4))
    n = 14
    grip = [(3, 10), (4.5, 9), (6, 8)]
    past = [_scene(n, (10, 6), g) for g in grip]
    for i, img in enumerate(past):
        _frame(ax, img, 0.1 + i * 1.9, 0.3, 1.7)
        _label(ax, 0.95 + i * 1.9, 2.3, ['2 steps ago', '1 step ago', 'now'][i], size=9.5)
    _label(ax, 2.85, 2.85, 'Camera pictures seen', weight='bold')

    _arrow(ax, (5.9, 1.15), (6.55, 1.15))
    _net(ax, 7.35, 1.15, w=1.2, h=1.3)
    _label(ax, 7.35, 2.3, 'video model', weight='bold', color=PURPLE)
    _label(ax, 7.35, -0.3, '+ planned actions:\nmove right, right, right', size=9,
           color=GRIP)
    _arrow(ax, (8.15, 1.15), (8.8, 1.15))

    fut = [(7.5, 7), (9, 6.3), (10.5, 6)]
    cube = [(10, 6), (11, 6), (12, 6)]
    for i in range(3):
        img = _blur(_scene(n, cube[i], fut[i]), i)
        _frame(ax, img, 9.0 + i * 1.9, 0.3, 1.7, edge=LINK, lw=2.0, ls='--')
        _label(ax, 9.85 + i * 1.9, 2.3, f'{i + 1} step{"s" if i else ""} ahead', size=9.5,
               color=LINK)
    _label(ax, 11.75, 2.85, 'Pictures it predicts', weight='bold', color=LINK)
    _label(ax, 11.75, -0.3, 'further ahead: less sure, so blurrier', size=9, color=MUTED)
    _save(fig, 'video-prediction-models', 'frames-in-frames-out.svg')


def blurry_future() -> None:
    """Two equally likely futures; a model that averages them draws a blurry ghost."""
    fig, ax = _fig(13, 4.4)
    _axes(ax, (-0.3, 14.2), (-1.1, 3.6))
    n = 14
    now = _scene(n, (7, 6), (7, 10))
    left = _scene(n, (4, 5), (7, 8))
    right = _scene(n, (10, 5), (7, 8))
    avg = 0.5 * left + 0.5 * right
    _frame(ax, now, 0.0, 0.3, 2.3)
    _label(ax, 1.15, 3.0, 'Now', weight='bold')
    _label(ax, 1.15, -0.25, 'gripper pushes the\ncube at its middle', size=9, color=MUTED)

    _frame(ax, left, 3.6, 0.3, 2.3)
    _frame(ax, right, 6.5, 0.3, 2.3)
    _label(ax, 6.2, 3.0, 'Two futures that both happen in the data', weight='bold')
    _label(ax, 4.75, -0.25, 'cube slides left', size=9, color=MUTED)
    _label(ax, 7.65, -0.25, 'cube slides right', size=9, color=MUTED)
    _arrow(ax, (2.5, 1.45), (3.4, 1.45), color=MUTED)

    _frame(ax, avg, 10.4, 0.3, 2.3, edge=GRIP, lw=2.0)
    _label(ax, 11.55, 3.0, 'What a simple model draws', weight='bold', color=GRIP)
    _label(ax, 11.55, -0.35, 'half a cube in both places:\nthe average of the two', size=9,
           color=GRIP)
    _arrow(ax, (9.0, 1.45), (10.2, 1.45), color=GRIP)
    _save(fig, 'video-prediction-models', 'blurry-future.svg')


def video_then_actions() -> None:
    """Generate a video of the task, then read the arm's moves off pairs of pictures."""
    fig, ax = _fig(14, 5.2)
    _axes(ax, (-0.2, 15.0), (-2.4, 3.6))
    _box(ax, 0.0, 0.6, 2.6, 1.2, face=PALE_GREY)
    _label(ax, 1.3, 1.2, '"put the red cube\nin the bowl"', size=10)
    _label(ax, 1.3, 2.3, '1. The task in words', weight='bold')
    _arrow(ax, (2.75, 1.2), (3.45, 1.2))

    n = 14
    bowl = (10.5, 4.5)
    seq = [_scene(n, (4, 9), (4, 12), bowl), _scene(n, (4, 9), (4, 10), bowl),
           _scene(n, (7, 7), (7, 8), bowl), _scene(n, (10.5, 4.5), (10.5, 5.5), bowl)]
    for i, img in enumerate(seq):
        _frame(ax, img, 3.6 + i * 1.75, 0.35, 1.55, edge=LINK, ls='--', lw=1.6)
    _label(ax, 6.8, 2.3, '2. A video model draws the task being done', weight='bold')

    # highlight a pair of frames
    ax.add_patch(Rectangle((5.25, 0.2), 3.4, 1.85, facecolor='none', edgecolor=JOINT, lw=2.2,
                           zorder=5))
    _arrow(ax, (6.95, 0.15), (6.95, -0.7), color=JOINT)
    _box(ax, 4.2, -2.2, 5.5, 1.35, face='#fff4dc', edge=JOINT)
    _label(ax, 6.95, -1.25, '3. Inverse dynamics model', weight='bold', size=10)
    _label(ax, 6.95, -1.8, '"which move turns this picture\ninto the next one?"', size=9)

    _arrow(ax, (9.85, -1.5), (10.9, -1.5))
    _box(ax, 11.0, -2.2, 3.8, 1.35, face=PALE_GREEN, edge=SLIDE)
    _label(ax, 12.9, -1.25, '4. Arm command', weight='bold', size=10)
    _label(ax, 12.9, -1.8, 'move 3 cm right and\n3 cm forward', size=9)
    _save(fig, 'video-prediction-models', 'video-then-actions.svg')


# --------------------------------------------------------------------------
# 04_learned-simulators.md
# --------------------------------------------------------------------------

def _water(n: int = 70) -> NDArray[np.float64]:
    pts = []
    while len(pts) < n:
        p = RNG.uniform([0.3, 0.3], [5.7, 2.6])
        if all(np.hypot(*(p - q)) > 0.33 for q in pts):
            pts.append(p)
    return np.array(pts)


def particles_and_edges() -> None:
    """Water as particles; each particle is joined to the neighbours within a set distance."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), facecolor='white')
    pts = _water()
    radius = 0.62
    for k, ax in enumerate(axes):
        _axes(ax, (-0.3, 6.3), (-0.8, 3.8))
        ax.plot([0, 0, 6, 6], [3.1, 0, 0, 3.1], color=INK, lw=2.0, zorder=1)
        ax.plot(pts[:, 0], pts[:, 1], 'o', color=LINK, ms=7, zorder=3)
    _title(axes[0], 3.0, 3.55, '1. Water in a tray, as small particles', size=11.5)
    _label(axes[0], 3.0, -0.45, 'each dot stores its position and its speed', size=9.5,
           color=MUTED)

    ax = axes[1]
    _title(ax, 3.0, 3.55, '2. Join every pair that is close together', size=11.5)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if np.hypot(*(pts[i] - pts[j])) < radius:
                ax.plot(pts[[i, j], 0], pts[[i, j], 1], color=GRID, lw=1.0, zorder=2)
    centre = int(np.argmin(np.hypot(pts[:, 0] - 3.0, pts[:, 1] - 1.4)))
    c = pts[centre]
    ax.add_patch(Circle(tuple(c), radius, facecolor='none', edgecolor=JOINT, lw=1.6, ls='--',
                        zorder=4))
    for j in range(len(pts)):
        if j != centre and np.hypot(*(pts[j] - c)) < radius:
            ax.plot([c[0], pts[j, 0]], [c[1], pts[j, 1]], color=JOINT, lw=2.2, zorder=4)
            ax.plot(pts[j, 0], pts[j, 1], 'o', color=JOINT, ms=8, zorder=5)
    ax.plot(c[0], c[1], 'o', color=GRIP, ms=10, zorder=6, markeredgecolor=INK)
    _label(ax, 3.0, -0.45, 'red: one particle   orange: its neighbours inside the dashed circle',
           size=9.5, color=MUTED)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'learned-simulators', 'particles-and-edges.svg')


def message_passing_step() -> None:
    """One particle collects a message from each neighbour and turns them into a push."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), facecolor='white')
    c = np.array([2.0, 1.8])
    nbrs = [np.array(p) for p in ((0.7, 2.6), (1.0, 0.8), (3.2, 2.7), (3.3, 1.2))]
    msgs = [np.array(v) for v in ((0.3, -0.12), (0.28, 0.3), (-0.05, -0.28), (-0.12, 0.18))]
    gravity = np.array([0.0, -0.35])
    total = sum(msgs, np.zeros(2)) + gravity
    for ax in axes:
        _axes(ax, (-0.1, 4.1), (-0.4, 3.9))

    ax = axes[0]
    _title(ax, 2.0, 3.6, '1. Each neighbour sends a message', size=11.5)
    for p, m in zip(nbrs, msgs):
        ax.plot(*p, 'o', color=JOINT, ms=12, markeredgecolor=INK, zorder=4)
        d = c - p
        d = d / np.linalg.norm(d)
        _arrow(ax, tuple(p + 0.2 * d), tuple(c - 0.2 * d), color=JOINT, lw=2.0)
    ax.plot(*c, 'o', color=GRIP, ms=14, markeredgecolor=INK, zorder=5)
    _label(ax, 2.0, -0.15, 'the message is computed by a small network\n'
                           'from the two positions and speeds', size=9, color=MUTED)

    ax = axes[1]
    _title(ax, 2.0, 3.6, '2. The particle adds them up', size=11.5)
    ax.plot(*c, 'o', color=GRIP, ms=14, markeredgecolor=INK, zorder=5)
    k = 3.2
    for m in msgs:
        _arrow(ax, tuple(c), tuple(c + m * k), color=JOINT, lw=1.8)
    _arrow(ax, tuple(c), tuple(c + gravity * k), color=MUTED, lw=1.8)
    _label(ax, c[0] - 0.12, c[1] + gravity[1] * k - 0.1, 'gravity', size=9, color=MUTED,
           ha='right')
    _arrow(ax, tuple(c), tuple(c + total * k), color=LINK, lw=3.2)
    end = c + total * k
    _label(ax, end[0] + 0.12, end[1] - 0.12, 'total push', size=9.5, color=LINK, ha='left')
    _label(ax, 2.0, -0.15, 'orange: the four messages\nblue: all of them added together',
           size=9, color=MUTED)

    ax = axes[2]
    _title(ax, 2.0, 3.6, '3. It moves a small step', size=11.5)
    ax.plot(*c, 'o', color=GRIP, ms=14, markeredgecolor=INK, alpha=0.35, zorder=4)
    new = c + total * 2.6
    ax.plot(*new, 'o', color=GRIP, ms=14, markeredgecolor=INK, zorder=5)
    _arrow(ax, tuple(c), tuple(new + 0.1 * total / np.linalg.norm(total)), color=LINK, lw=2.2)
    _label(ax, c[0] + 0.35, c[1] + 0.3, 'before', size=9, color=MUTED, ha='left')
    _label(ax, new[0] + 0.3, new[1], 'after one step', size=9, ha='left')
    _label(ax, 2.0, -0.15, 'every particle does this at the same time,\n'
                           'then the whole thing repeats', size=9, color=MUTED)
    fig.subplots_adjust(wspace=0.1)
    _save(fig, 'learned-simulators', 'message-passing-step.svg')


def _bezier(p0: NDArray[np.float64], p1: NDArray[np.float64], p2: NDArray[np.float64],
            n: int = 60) -> NDArray[np.float64]:
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def _cloth_shape(grip: tuple[float, float], right_end: float, length: float,
                 nodes: int = 13) -> NDArray[np.float64]:
    """A cloth lying on the table with one corner lifted and carried over the rest.

    The bottom layer lies flat from a fold point to the fixed right end; the top layer
    curves from the fold point up to the gripper. The fold point is found so that the
    whole cloth keeps its length."""
    g = np.array(grip)

    def build(fold: float) -> NDArray[np.float64]:
        bottom = np.column_stack([np.linspace(right_end, fold, 40), np.zeros(40)])
        ctrl = np.array([fold - 0.6, max(g[1], 0.3) * 0.9 + 0.2])
        top = _bezier(np.array([fold, 0.0]), ctrl, g)
        return np.vstack([bottom, top[1:]])

    lo, hi = -5.0, right_end
    for _ in range(60):
        mid = (lo + hi) / 2
        pts = build(mid)
        total = float(np.sum(np.hypot(*np.diff(pts, axis=0).T)))
        if total > length:
            lo = mid
        else:
            hi = mid
    pts = build((lo + hi) / 2)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    want = np.linspace(0, s[-1], nodes)
    return np.column_stack([np.interp(want, s, pts[:, 0]), np.interp(want, s, pts[:, 1])])


def cloth_fold_prediction() -> None:
    """The simulator's predicted cloth shape as the gripper folds it in half."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), facecolor='white')
    length = 4.0
    right = 4.3
    stages = [('Now', None), ('Predicted after 10 steps', (1.7, 1.5)),
              ('Predicted after 20 steps', (3.9, 0.35))]
    for ax, (t, grip) in zip(axes, stages):
        _axes(ax, (-0.1, 4.8), (-1.0, 2.9))
        _table_side(ax, 0.0, 4.7, y=-0.06, legs=False)
        if grip is None:
            pts = np.column_stack([np.linspace(0.3, right, 13), np.zeros(13)])
            gp = (0.3, 0.0)
            col = INK
        else:
            pts = _cloth_shape(grip, right, length)
            gp = grip
            col = LINK
        ax.plot(pts[:, 0], pts[:, 1], color=col, lw=2.0, zorder=3,
                ls='-' if grip is None else '--')
        ax.plot(pts[:, 0], pts[:, 1], 'o', color=col, ms=6, zorder=4)
        _gripper_side(ax, gp[0], gp[1] - 0.05, open_w=0.28)
        _title(ax, 2.4, 2.65, t, size=11.5)
    _label(axes[0], 2.4, -0.6, 'a towel lying flat; the gripper\nholds its left corner', size=9,
           color=MUTED)
    _label(axes[1], 2.4, -0.6, 'corner lifted up', size=9, color=MUTED)
    _label(axes[2], 2.4, -0.6, 'folded in half', size=9, color=MUTED)
    fig.subplots_adjust(wspace=0.06)
    _save(fig, 'learned-simulators', 'cloth-fold-prediction.svg')


# --------------------------------------------------------------------------
# 05_latent-world-models.md
# --------------------------------------------------------------------------

def _trapezoid(ax: Axes, x: float, y: float, w: float, h_big: float, h_small: float,
               narrowing: bool, label: str) -> None:
    if narrowing:
        pts = [(x, y - h_big / 2), (x + w, y - h_small / 2), (x + w, y + h_small / 2),
               (x, y + h_big / 2)]
    else:
        pts = [(x, y - h_small / 2), (x + w, y - h_big / 2), (x + w, y + h_big / 2),
               (x, y + h_small / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor='#ece6f5', edgecolor=PURPLE, lw=1.4,
                         zorder=2))
    _label(ax, x + w / 2, y, label, size=9.5, color=PURPLE, weight='bold')


def picture_to_short_code() -> None:
    """An encoder squeezes a picture into a few numbers; a decoder draws it back."""
    fig, ax = _fig(13, 4.6)
    _axes(ax, (-0.2, 14.0), (-1.0, 3.8))
    n = 16
    img = _scene(n, (10, 6), (6, 11), bowl=(4, 4))
    _frame(ax, img, 0.0, 0.1, 2.8)
    _label(ax, 1.4, 3.3, 'Camera picture', weight='bold')
    _label(ax, 1.4, -0.5, '16 × 16 pixels, 3 colours each:\n768 numbers', size=9, color=MUTED)

    _trapezoid(ax, 3.1, 1.5, 2.2, 2.8, 1.0, True, 'encoder')
    code = [0.8, -1.2, 0.3, 1.5, -0.4, 0.9]
    _cells(ax, 5.7, 2.45, code, cell=0.32, size=8)
    _label(ax, 6.0, 3.3, 'Short code', weight='bold', color=PURPLE)
    _label(ax, 6.0, -0.5, '6 numbers', size=9, color=MUTED)
    _trapezoid(ax, 6.7, 1.5, 2.2, 2.8, 1.0, False, 'decoder')

    _frame(ax, _blur(img, 1), 9.2, 0.1, 2.8)
    _label(ax, 10.6, 3.3, 'Picture drawn back', weight='bold')
    _label(ax, 10.6, -0.5, 'close to the original,\nbut not exact', size=9, color=MUTED)
    _label(ax, 13.0, 1.5, 'training\nmakes these\ntwo pictures\nmatch', size=9, color=MUTED)
    _save(fig, 'latent-world-models', 'picture-to-short-code.svg')


def imagining_in_code() -> None:
    """Rolling the world model forward on codes only, with a predicted score at each step."""
    fig, ax = _fig(14, 5.6)
    _axes(ax, (-0.3, 14.6), (-0.8, 4.0))
    n = 12
    _frame(ax, _scene(n, (8, 5), (4, 9)), 0.0, 1.0, 1.8)
    _label(ax, 0.9, 3.2, 'one real\npicture', size=9.5, weight='bold')
    _arrow(ax, (1.95, 1.9), (2.55, 1.9), color=PURPLE)
    _label(ax, 2.25, 2.25, 'encoder', size=8.5, color=PURPLE)

    codes = [[0.8, -1.2, 0.3, 1.5, -0.4], [0.6, -0.8, 0.6, 1.2, 0.2],
             [0.2, -0.3, 1.0, 0.9, 0.8], [-0.1, 0.3, 1.4, 0.4, 1.3]]
    scores = [0.1, 0.2, 0.5, 0.9]
    actions = ['move right', 'move down', 'close gripper']
    xs = [2.7, 6.2, 9.7, 13.2]
    for i, (x, code) in enumerate(zip(xs, codes)):
        _cells(ax, x, 2.8, code, cell=0.35, size=8)
        _label(ax, x + 0.33, 3.15, 'now' if i == 0 else f'step {i}', size=9.5,
               color=INK if i == 0 else PURPLE, weight='bold')
        _box(ax, x - 0.05, -0.45, 0.8, 0.55, face=PALE_GREEN, edge=SLIDE)
        _label(ax, x + 0.35, -0.17, f'{scores[i]:.1f}', size=9.5, color=SLIDE)
        _arrow(ax, (x + 0.35, 1.0), (x + 0.35, 0.18), color=SLIDE, lw=1.0)
        if i > 0:
            _box(ax, x - 1.9, 1.45, 1.2, 1.0, face='white', edge=GRID, ls='--')
            _label(ax, x - 1.3, 1.95, 'no picture\ndrawn', size=8, color=MUTED)
    for i, a in enumerate(actions):
        x0, x1 = xs[i] + 0.8, xs[i + 1] - 0.1
        _arrow(ax, (x0, 2.95), (x1, 2.95), color=PURPLE, lw=1.8)
        _label(ax, (x0 + x1) / 2, 3.35, a, size=9, color=GRIP)
    _label(ax, 0.9, -0.17, 'predicted score\n(how well it is going)', size=9, color=SLIDE)
    _save(fig, 'latent-world-models', 'imagining-in-code.svg')


def _arm_icon(ax: Axes, x: float, y: float, s: float, q1: float, q2: float,
              color: str = LINK, alpha: float = 1.0, ls: str = '-') -> None:
    ax.add_patch(Rectangle((x - 0.18 * s, y), 0.36 * s, 0.14 * s, facecolor=MUTED,
                           edgecolor='none', alpha=alpha, zorder=2))
    p0 = np.array([x, y + 0.14 * s])
    p1 = p0 + 0.7 * s * np.array([math.cos(q1), math.sin(q1)])
    p2 = p1 + 0.6 * s * np.array([math.cos(q1 + q2), math.sin(q1 + q2)])
    ax.plot([p0[0], p1[0], p2[0]], [p0[1], p1[1], p2[1]], color=color, lw=3 * s,
            alpha=alpha, ls=ls, solid_capstyle='round', zorder=3)
    ax.plot([p1[0]], [p1[1]], 'o', color=JOINT, ms=5 * s, alpha=alpha, zorder=4)
    ax.add_patch(Rectangle((x + 0.75 * s, y), 0.2 * s, 0.2 * s, facecolor=WRIST,
                           edgecolor=INK if alpha > 0.6 else 'none', lw=0.6, alpha=alpha,
                           zorder=2))


def real_vs_imagined() -> None:
    """A few real practice runs feed the model; the policy practises many times inside it."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1, 2.1]})
    ax = axes[0]
    _axes(ax, (0, 4.2), (-0.6, 4.4))
    _title(ax, 2.1, 4.1, 'Practice on the real arm', size=11.5)
    for i, (q1, q2) in enumerate(((1.2, -1.4), (1.0, -1.2), (0.9, -1.1))):
        yy = 2.6 - i * 1.35
        _box(ax, 0.4, yy - 0.15, 3.4, 1.15, face=PALE_GREY, edge=GRID)
        _arm_icon(ax, 1.4, yy, 0.9, q1, q2)
        _label(ax, 2.9, yy + 0.45, f'try {i + 1}', size=9.5)
    _label(ax, 2.1, -0.4, 'slow, and wears the arm', size=9.5, color=MUTED)

    ax = axes[1]
    _axes(ax, (0, 8.6), (-0.6, 4.4))
    _title(ax, 4.3, 4.1, 'Practice inside the world model', size=11.5)
    k = 0
    for r in range(4):
        for c in range(8):
            q1 = 0.7 + 0.08 * ((k * 5) % 9)
            q2 = -1.6 + 0.07 * ((k * 7) % 11)
            _arm_icon(ax, 0.45 + c * 1.05, 3.05 - r * 0.95, 0.55, q1, q2, color=PURPLE,
                      alpha=0.55)
            k += 1
    _label(ax, 4.3, -0.4, 'fast and cheap: many imagined tries for each real one', size=9.5,
           color=MUTED)
    fig.subplots_adjust(wspace=0.05)
    _save(fig, 'latent-world-models', 'real-vs-imagined.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    predict_then_choose()
    four_kinds()
    state_action_next_state()
    rolling_forward()
    try_many_plans()
    frames_in_frames_out()
    blurry_future()
    video_then_actions()
    particles_and_edges()
    message_passing_step()
    cloth_fold_prediction()
    picture_to_short_code()
    imagining_in_code()
    real_vs_imagined()


if __name__ == '__main__':
    main()
