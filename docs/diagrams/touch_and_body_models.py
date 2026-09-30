"""Generate the diagrams used in docs/05_neural-network-models/08_touch-and-body-models/.

Each document's pictures go to a folder named after it, under
docs/images/touch-and-body-models/.

Run with:  pixi run python ../docs/diagrams/touch_and_body_models.py
or, from the repo root:  python3 docs/diagrams/touch_and_body_models.py --png <dir>

Every signal drawn here is a made-up example shaped like the real thing. None of
the curves is a measurement, and the captions under the pictures say so.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'touch-and-body-models')
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
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b6fd1'
MUG: str = '#8a6bbf'
GEL: str = '#f4e3c1'

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


def _plot_axes(ax: Axes, xlabel: str, ylabel: str) -> None:
    """A plain chart: no top or right border, light grid, muted labels."""
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, color=INK, fontsize=10)
    ax.set_ylabel(ylabel, color=INK, fontsize=10)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 13) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold',
            zorder=9)


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED, zorder=9)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>') -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': style, 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=8)


def _link(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = LINK,
          width: float = 7, z: int = 2) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width, solid_capstyle='round',
            zorder=z)


def _hinge(ax: Axes, p: tuple[float, float], size: float = 12, color: str = JOINT) -> None:
    ax.plot([p[0]], [p[1]], 'o', color=color, ms=size, zorder=4)
    ax.plot([p[0]], [p[1]], 'o', color=INK, ms=size * 0.25, zorder=5)


def _floor(ax: Axes, x0: float, x1: float, y: float = 0.0) -> None:
    ax.plot([x0, x1], [y, y], color=MUTED, lw=1.2, zorder=1)
    for x in np.arange(x0 + 0.1, x1, 0.3):
        ax.plot([x, x - 0.15], [y, y - 0.15], color=GRID, lw=1.0, zorder=1)


def _chain(base: tuple[float, float], angles_deg: list[float],
           lengths: list[float]) -> list[tuple[float, float]]:
    """Return the joint positions of a flat arm, each angle measured from the last link."""
    pts = [base]
    heading = 0.0
    for a, length in zip(angles_deg, lengths):
        heading += math.radians(a)
        x, y = pts[-1]
        pts.append((x + length * math.cos(heading), y + length * math.sin(heading)))
    return pts


def _draw_arm(ax: Axes, pts: list[tuple[float, float]], color: str = LINK,
              width: float = 7, hinges: bool = True) -> None:
    ax.add_patch(Rectangle((pts[0][0] - 0.35, pts[0][1] - 0.3), 0.7, 0.3,
                           facecolor=MUTED, edgecolor='none', zorder=2))
    for a, b in zip(pts[:-1], pts[1:]):
        _link(ax, a, b, color=color, width=width)
    if hinges:
        for p in pts[:-1]:
            _hinge(ax, p)


def _down_gripper(ax: Axes, p: tuple[float, float], gap: float = 0.5,
                  finger: float = 0.45, color: str = GRIP) -> None:
    """A two-finger gripper hanging below point p, fingers pointing down."""
    ax.plot([p[0] - gap / 2 - 0.08, p[0] + gap / 2 + 0.08], [p[1], p[1]], color=color,
            lw=4, solid_capstyle='round', zorder=5)
    for s in (-1, 1):
        x = p[0] + s * gap / 2
        ax.plot([x, x], [p[1], p[1] - finger], color=color, lw=4, solid_capstyle='round',
                zorder=5)


def _mug(ax: Axes, x: float, y: float, w: float = 0.6, h: float = 0.7,
         color: str = MUG) -> None:
    """A mug standing with its base centre at (x, y), handle on the right."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=0.8,
                           zorder=3))
    ax.add_patch(Arc((x + w / 2, y + h / 2), w * 0.55, h * 0.55,
                                        theta1=-90, theta2=90, color=INK, lw=2.2,
                                        zorder=3))


def _net(ax: Axes, x0: float, y0: float, sizes: tuple[int, ...], dx: float = 0.55,
         dy: float = 0.32, r: float = 0.09, color: str = LINK) -> None:
    """A small drawing of a neural network: columns of circles joined by thin lines."""
    cols = []
    for i, n in enumerate(sizes):
        ys = [y0 + (k - (n - 1) / 2) * dy for k in range(n)]
        cols.append([(x0 + i * dx, yy) for yy in ys])
    for a, b in zip(cols[:-1], cols[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRID, lw=0.6, zorder=2)
    for col in cols:
        for p in col:
            ax.add_patch(Circle(p, r, facecolor=color, edgecolor=INK, lw=0.6, zorder=3))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'


def three_kinds_of_signal() -> None:
    """One arm holding a mug, with the three places its touch and body signals come from."""
    fig, ax = plt.subplots(figsize=(10.5, 6.2), facecolor='white')
    _axes(ax, (-4.2, 8.0), (-0.6, 6.4))
    _floor(ax, -1.2, 6.2)
    pts = _chain((0.0, 0.3), [80.0, -70.0, -100.0], [2.6, 2.6, 0.9])
    _draw_arm(ax, pts)
    wrist = pts[-1]
    # force-torque sensor: a short thick disc at the wrist
    ax.add_patch(Rectangle((wrist[0] - 0.32, wrist[1] - 0.18), 0.64, 0.18,
                           facecolor=WRIST, edgecolor=INK, lw=0.8, zorder=6))
    grip_top = (wrist[0], wrist[1] - 0.18)
    _down_gripper(ax, grip_top, gap=0.66, finger=0.6)
    _mug(ax, wrist[0], grip_top[1] - 0.72, w=0.6, h=0.62)
    table_y = 0.0
    ax.add_patch(Rectangle((wrist[0] - 1.2, table_y), 2.4, 0.02, color=MUTED))

    # 1. touch: pad on the right finger, with a tactile picture next to it
    pad = (wrist[0] + 0.33, grip_top[1] - 0.35)
    ax.plot([pad[0]], [pad[1]], 's', ms=8, color=SLIDE, zorder=7)
    img_x, img_y = 5.3, 0.5
    for i in range(6):
        for j in range(6):
            d = math.hypot(i - 2.5, j - 2.5)
            v = max(0.0, 1.0 - d / 3.0)
            ax.add_patch(Rectangle((img_x + i * 0.22, img_y + j * 0.22), 0.22, 0.22,
                                   facecolor=plt.cm.Greens(0.15 + 0.8 * v),
                                   edgecolor='white', lw=0.5, zorder=3))
    _arrow(ax, (pad[0] + 0.1, pad[1] - 0.05), (img_x - 0.08, img_y + 0.66), color=SLIDE)
    _label(ax, img_x + 0.66, img_y + 1.72, 'Touch', size=11, color=SLIDE, weight='bold')
    _label(ax, img_x + 0.66, img_y + 1.45, 'a small picture of the contact', size=9,
           color=SLIDE)

    # 2. force: six numbers at the wrist
    _arrow(ax, (wrist[0] + 0.35, wrist[1] - 0.08), (5.6, 3.3), color=WRIST)
    _label(ax, 5.7, 3.85, 'Force', size=11, color=WRIST, weight='bold', ha='left')
    _label(ax, 5.7, 3.5, 'six numbers at the wrist:', size=9, color=WRIST, ha='left')
    _label(ax, 5.7, 3.2, 'three pushes and three twists', size=9, color=WRIST, ha='left')

    # 3. body: angle and motor current at every joint
    for k, p in enumerate(pts[:-1]):
        ax.plot([p[0]], [p[1]], 'o', ms=24, mfc='none', mec=AXIS_Z, mew=1.6, zorder=6)
    _arrow(ax, (pts[1][0] - 0.3, pts[1][1] + 0.1), (-1.9, 4.6), color=AXIS_Z)
    _arrow(ax, (pts[0][0] - 0.3, pts[0][1] + 0.15), (-1.9, 4.2), color=AXIS_Z)
    _label(ax, -2.0, 5.3, 'Body', size=11, color=AXIS_Z, weight='bold', ha='right')
    _label(ax, -2.0, 5.0, 'at every joint:', size=9, color=AXIS_Z, ha='right')
    _label(ax, -2.0, 4.7, 'its angle, its speed', size=9, color=AXIS_Z, ha='right')
    _label(ax, -2.0, 4.4, 'and its motor current', size=9, color=AXIS_Z, ha='right')

    _title(ax, 1.9, 6.15, 'Three kinds of signal that no camera gives you')
    _save(fig, OVERVIEW, 'three-kinds-of-signal.svg')


def one_pick_five_questions() -> None:
    """A pick drawn as five moments, with the question each model answers at that moment."""
    fig, ax = plt.subplots(figsize=(12.0, 4.6), facecolor='white')
    _axes(ax, (-0.8, 15.2), (-2.6, 3.4))
    xs = [0.8, 4.0, 7.2, 10.4, 13.6]
    names = ['1  fingers close', '2  lift a little', '3  carry', '4  put down',
             'all the time']
    for x, name in zip(xs, names):
        _label(ax, x, 3.0, name, size=10, weight='bold')
    # 1 fingers close on the mug
    _floor(ax, xs[0] - 1.0, xs[0] + 1.0)
    _mug(ax, xs[0], 0.0)
    _down_gripper(ax, (xs[0], 1.4), gap=0.62, finger=0.7)
    _link(ax, (xs[0], 1.4), (xs[0], 2.4))
    # 2 lift
    _floor(ax, xs[1] - 1.0, xs[1] + 1.0)
    _mug(ax, xs[1], 0.35)
    _down_gripper(ax, (xs[1], 1.75), gap=0.62, finger=0.7)
    _link(ax, (xs[1], 1.75), (xs[1], 2.5))
    _arrow(ax, (xs[1] + 0.8, 0.7), (xs[1] + 0.8, 1.6), color=INK)
    # 3 carry, with a box in the way
    _floor(ax, xs[2] - 1.3, xs[2] + 1.3)
    _mug(ax, xs[2] - 0.5, 0.9)
    _down_gripper(ax, (xs[2] - 0.5, 2.3), gap=0.62, finger=0.7)
    _link(ax, (xs[2] - 0.5, 2.3), (xs[2] - 0.5, 2.8))
    _arrow(ax, (xs[2] + 0.05, 1.3), (xs[2] + 0.6, 1.3), color=INK)
    ax.add_patch(Rectangle((xs[2] + 0.75, 0.0), 0.5, 1.6, facecolor=GRID, edgecolor=INK,
                           lw=0.8, zorder=3))
    # 4 put down
    _floor(ax, xs[3] - 1.0, xs[3] + 1.0)
    _mug(ax, xs[3], 0.0)
    _down_gripper(ax, (xs[3], 1.4), gap=0.62, finger=0.7)
    _link(ax, (xs[3], 1.4), (xs[3], 2.4))
    _arrow(ax, (xs[3] + 0.8, 1.6), (xs[3] + 0.8, 0.7), color=INK)
    # 5 the arm itself
    pts = _chain((xs[4] - 0.6, 0.3), [70.0, -80.0], [1.3, 1.3])
    _floor(ax, xs[4] - 1.2, xs[4] + 1.2)
    _draw_arm(ax, pts, width=6)

    questions = [('Is the grip in the', 'right place?', 'touch models', SLIDE),
                 ('Is it starting', 'to slip?', 'force and slip', WRIST),
                 ('Did the arm bump', 'into something?', 'collision and failure', GRIP),
                 ('Did it really', 'let go?', 'failure detection', GRIP),
                 ('What torque does each', 'joint need right now?', 'learned arm models',
                  AXIS_Z)]
    for x, (q1, q2, who, color) in zip(xs, questions):
        _label(ax, x, -0.75, q1, size=10)
        _label(ax, x, -1.1, q2, size=10)
        _label(ax, x, -1.75, who, size=10, color=color, weight='bold')
    for a, b in zip(xs[:3], xs[1:4]):
        _arrow(ax, (a + 1.25, 1.2), (b - 1.35, 1.2), color=GRID, lw=2.0)
    _save(fig, OVERVIEW, 'one-pick-five-questions.svg')


# --------------------------------------------------------------------------
# 02_touch-sensing-models
# --------------------------------------------------------------------------

TOUCH: str = 'touch-sensing-models'


def gel_camera_sensor() -> None:
    """A cut-through of a camera-behind-gel touch sensor, and the picture its camera sees."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 5.4), facecolor='white',
                                      gridspec_kw={'width_ratios': [1.35, 1]})
    _axes(left, (-4.5, 3.6), (-2.6, 3.3))
    # housing
    left.add_patch(Rectangle((-2.2, -2.0), 4.4, 2.3, facecolor='#eeeeee', edgecolor=INK,
                             lw=1.0, zorder=1))
    # clear block and gel, with a dent where a screw head presses
    left.add_patch(Rectangle((-2.2, 0.3), 4.4, 0.35, facecolor='#dff0fb', edgecolor=INK,
                             lw=0.8, zorder=2))
    xs = np.linspace(-2.2, 2.2, 200)
    top = 1.2 - 0.32 * np.exp(-((xs - 0.3) / 0.45) ** 2)
    gel = np.concatenate([np.column_stack([xs, top]),
                          [[2.2, 0.65], [-2.2, 0.65]]])
    left.add_patch(Polygon(gel, closed=True, facecolor=GEL, edgecolor='none', zorder=2))
    left.plot(xs, top, color='#555555', lw=3.0, zorder=3)          # painted skin
    # the object pressing in
    left.add_patch(Rectangle((-0.25, 0.9), 1.1, 0.5, facecolor=MUTED, edgecolor=INK,
                             lw=0.8, zorder=4))
    left.add_patch(Rectangle((0.15, 1.4), 0.3, 1.1, facecolor=MUTED, edgecolor=INK,
                             lw=0.8, zorder=4))
    _arrow(left, (1.3, 2.6), (1.3, 1.7), color=INK)
    _label(left, 1.45, 2.2, 'press', size=9, ha='left')
    # camera
    left.add_patch(Rectangle((-0.4, -1.8), 0.8, 0.5, facecolor=INK, zorder=3))
    left.add_patch(Polygon([(-0.15, -1.3), (0.15, -1.3), (0.9, 0.3), (-0.9, 0.3)],
                           closed=True, facecolor=LINK_PALE, edgecolor='none', alpha=0.6,
                           zorder=1.5))
    # lights
    for x, c in ((-1.9, AXIS_X), (1.9, AXIS_Z)):
        left.add_patch(Circle((x, -0.2), 0.14, facecolor=c, edgecolor=INK, lw=0.6,
                              zorder=3))
        _arrow(left, (x, -0.05), (x * 0.4, 0.55), color=c, lw=1.1)
    _label(left, -4.4, 1.05, 'soft gel with a\npainted skin', size=9, ha='left')
    _arrow(left, (-2.9, 1.05), (-1.4, 1.15), color=MUTED, lw=1.0)
    _label(left, -4.4, 0.45, 'clear block', size=9, ha='left')
    _label(left, -4.4, -0.2, 'coloured\nlights', size=9, ha='left')
    _label(left, -4.4, -1.55, 'camera', size=9, ha='left')
    _arrow(left, (-3.5, -1.55), (-0.5, -1.55), color=MUTED, lw=1.0)
    _label(left, -0.4, 2.3, 'a screw\npressing in', size=9, ha='right')
    _title(left, 0.0, 3.1, 'Inside the sensor')

    # right: the picture the camera takes
    _axes(right, (-2.4, 2.4), (-2.6, 3.3))
    n = 24
    img = np.zeros((n, n, 3))
    yy, xx = np.mgrid[0:n, 0:n]
    cx, cy = 13.0, 11.5
    for i in range(n):
        for j in range(n):
            inside = (abs(xx[i, j] - cx) < 5.5) and (abs(yy[i, j] - cy) < 3.0)
            base = np.array([0.93, 0.90, 0.84])
            if inside:
                # red light from the left, blue from the right: the slope shows as colour
                sx = (xx[i, j] - cx) / 5.5
                base = np.array([0.95 - 0.6 * max(0, sx), 0.78, 0.95 - 0.6 * max(0, -sx)])
                if abs(xx[i, j] - cx) < 1.2 and abs(yy[i, j] - cy) < 1.0:
                    base = np.array([0.60, 0.58, 0.62])
            img[i, j] = base
    right.imshow(img, extent=(-2.0, 2.0, -2.0, 2.0), origin='lower',
                 interpolation='nearest', zorder=2)
    right.add_patch(Rectangle((-2.0, -2.0), 4.0, 4.0, fill=False, edgecolor=INK, lw=1.0,
                              zorder=3))
    _title(right, 0.0, 3.1, 'What the camera sees')
    _caption(right, 0.0, 2.45, 'the dent shows as coloured shading')
    _caption(right, 0.0, -2.35, 'a small image, many times a second')
    _save(fig, TOUCH, 'gel-camera-sensor.svg')


def tactile_image_to_answers() -> None:
    """A grid of tactile pixel numbers going into a small network, and what comes out."""
    fig, ax = plt.subplots(figsize=(12.0, 4.8), facecolor='white')
    _axes(ax, (-0.4, 14.2), (-2.6, 3.1))
    vals = np.array([[0, 0, 1, 1, 0, 0],
                     [0, 2, 5, 6, 2, 0],
                     [1, 5, 9, 9, 5, 1],
                     [1, 6, 9, 8, 4, 0],
                     [0, 2, 4, 5, 2, 0],
                     [0, 0, 1, 1, 0, 0]])
    s = 0.55
    x0, y0 = 0.0, -1.6
    for r in range(6):
        for c in range(6):
            v = vals[r, c]
            ax.add_patch(Rectangle((x0 + c * s, y0 + (5 - r) * s), s, s,
                                   facecolor=plt.cm.Oranges(0.08 + v / 11), edgecolor='white',
                                   lw=0.8, zorder=2))
            _label(ax, x0 + c * s + s / 2, y0 + (5 - r) * s + s / 2, str(v), size=9,
                   color=INK if v < 7 else 'white')
    _label(ax, x0 + 3 * s, 2.35, 'The tactile image', size=11, weight='bold')
    _label(ax, x0 + 3 * s, 1.95, 'how deep the gel is pressed', size=9, color=MUTED)
    _label(ax, x0 + 3 * s, -2.1, '0 = untouched, 9 = pressed deepest', size=9, color=MUTED)
    _arrow(ax, (3.6, 0.0), (4.6, 0.0), color=INK)
    _net(ax, 5.1, 0.0, (5, 6, 6, 3), dx=0.9, dy=0.42, r=0.11)
    _label(ax, 6.45, 2.35, 'A small network', size=11, weight='bold')
    _label(ax, 6.45, 1.95, 'learned from many presses', size=9, color=MUTED)
    _arrow(ax, (8.1, 0.0), (9.0, 0.0), color=INK)
    answers = [('Touching?', 'yes'),
               ('Where on the pad?', 'a little left of centre'),
               ('How hard?', 'a force, in newtons'),
               ('Pushed sideways?', 'a sideways force')]
    for k, (q, a) in enumerate(answers):
        y = 1.1 - k * 0.8
        _label(ax, 9.2, y + 0.15, q, size=10, ha='left', weight='bold')
        _label(ax, 9.2, y - 0.17, a, size=10, ha='left', color=SLIDE)
    _label(ax, 11.0, 2.35, 'What comes out', size=11, weight='bold')
    _save(fig, TOUCH, 'tactile-image-to-answers.svg')


def _marker_grid(ax: Axes, cx: float, cy: float, shift, title: str, note: str) -> None:
    """Dots printed on the gel. Grey rings: where each dot sat at rest. Black: where it is now."""
    ax.add_patch(Rectangle((cx - 1.5, cy - 1.5), 3.0, 3.0, facecolor=GEL, edgecolor=INK,
                           lw=0.8, zorder=1))
    for i in range(6):
        for j in range(6):
            x = cx - 1.25 + i * 0.5
            y = cy - 1.25 + j * 0.5
            dx, dy = shift(x - cx, y - cy)
            ax.plot([x], [y], 'o', ms=7, mfc='none', mec=MUTED, mew=1.0, zorder=2)
            if math.hypot(dx, dy) > 0.03:
                ax.plot([x, x + dx], [y, y + dy], color=LINK, lw=2.2, zorder=2.5)
            ax.plot([x + dx], [y + dy], 'o', ms=5, color=INK, zorder=3)
    _label(ax, cx, cy + 2.0, title, size=11, weight='bold')
    if note:
        _caption(ax, cx, cy - 2.0, note, size=9)


def markers_show_shear() -> None:
    """Dots printed on the gel: straight pressing spreads them, a sideways push shifts them."""
    fig, ax = plt.subplots(figsize=(11.5, 4.9), facecolor='white')
    _axes(ax, (-1.9, 11.9), (-2.6, 2.6))

    def none(_x: float, _y: float) -> tuple[float, float]:
        return (0.0, 0.0)

    def press(x: float, y: float) -> tuple[float, float]:
        d = math.hypot(x, y)
        k = 0.32 * math.exp(-(d / 0.9) ** 2) * (d / 0.9)
        return (k * x / (d + 1e-9), k * y / (d + 1e-9))

    def push(x: float, y: float) -> tuple[float, float]:
        d = math.hypot(x, y)
        return (0.26 * math.exp(-(d / 1.0) ** 2), 0.0)

    _marker_grid(ax, 0.0, 0.0, none, 'Nothing touching', 'dots sit on a grid')
    _marker_grid(ax, 5.0, 0.0, press, 'Pressed straight in', 'dots spread outwards')
    _marker_grid(ax, 10.0, 0.0, push, 'Pressed and pushed right',
                 'dots in the contact all move right')
    _label(ax, 5.0, -2.5, 'Grey ring: where a dot sits when nothing touches.   '
           'Black dot: where it is now.   Blue line: how far it moved.', size=9)
    _save(fig, TOUCH, 'dots-show-sideways-force.svg')


# --------------------------------------------------------------------------
# 03_force-and-slip-models
# --------------------------------------------------------------------------

SLIP: str = 'force-and-slip-models'


def _grip_trace() -> tuple[np.ndarray, np.ndarray]:
    """A drawn, not measured, grip-force trace: close, lift, hold, then slip."""
    t = np.linspace(0.0, 4.0, 800)
    f = np.zeros_like(t)
    f += np.where(t > 0.5, 6.0 * (1 - np.exp(-(t - 0.5) / 0.05)), 0.0)
    f += np.where((t > 0.5) & (t < 0.9),
                  2.5 * np.exp(-(t - 0.5) / 0.08) * np.sin(60 * (t - 0.5)), 0.0)
    f += np.where((t > 1.4) & (t < 1.8),
                  1.2 * np.exp(-(t - 1.4) / 0.1) * np.sin(45 * (t - 1.4)), 0.0)
    slip = (t > 2.9)
    f += np.where(slip, 0.6 * np.sin(2 * math.pi * 38 * t) * np.minimum(1, (t - 2.9) * 4),
                  0.0)
    f += np.where(t > 3.4, -3.0 * (1 - np.exp(-(t - 3.4) / 0.1)), 0.0)
    f += 0.08 * RNG.standard_normal(len(t))
    return t, f


def grip_force_trace() -> None:
    """One grip, as the force a finger sensor might report: close, lift, hold, slip."""
    t, f = _grip_trace()
    fig, ax = plt.subplots(figsize=(10.5, 4.6), facecolor='white')
    _plot_axes(ax, 'time (seconds)', 'force on the pad')
    ax.plot(t, f, color=WRIST, lw=1.2)
    ax.set_xlim(0, 4.0)
    ax.set_ylim(-1.5, 10.5)
    ax.set_yticklabels([])
    marks = [(0.5, 'fingers\nclose'), (1.4, 'lift\nstarts'), (2.9, 'slip\nstarts'),
             (3.4, 'mug\nslides out')]
    for x, text in marks:
        ax.axvline(x, color=MUTED, lw=0.8, ls=':')
        ax.text(x + 0.04, 9.6, text, fontsize=9, color=INK, va='top')
    ax.annotate('the jolt of the fingers\nclosing: not slip', xy=(0.545, 4.5),
                xytext=(0.75, 2.2), fontsize=9, color=MUTED,
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 0.8})
    ax.annotate('fast small shaking:\nthe sign of slip', xy=(3.15, 6.6), xytext=(2.05, 3.6),
                fontsize=9, color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.0})
    ax.set_title('A drawn example of one grip, not a measurement', fontsize=11,
                 color=MUTED)
    _save(fig, SLIP, 'grip-force-trace.svg')


def sliding_window() -> None:
    """The last short stretch of the signal goes into a small network, which says slip or not."""
    t, f = _grip_trace()
    fig = plt.figure(figsize=(12.0, 4.4), facecolor='white')
    ax = fig.add_axes((0.04, 0.18, 0.5, 0.7))
    _plot_axes(ax, 'time (seconds)', 'force on the pad')
    ax.plot(t, f, color=WRIST, lw=1.0)
    ax.set_xlim(2.0, 3.6)
    ax.set_ylim(2.5, 8.5)
    ax.set_yticklabels([])
    windows = [(2.25, 2.45, SLIDE, 'no slip'), (2.95, 3.15, GRIP, 'slip')]
    for a, b, c, _name in windows:
        ax.axvspan(a, b, color=c, alpha=0.15)
        ax.text((a + b) / 2, 8.2, 'window', fontsize=9, color=c, ha='center')
    right = fig.add_axes((0.56, 0.05, 0.43, 0.9))
    _axes(right, (0.0, 8.0), (-2.6, 2.6))
    _net(right, 1.4, 0.0, (5, 5, 2), dx=1.1, dy=0.45, r=0.12)
    _label(right, 2.5, 1.9, 'the same small network,', size=10)
    _label(right, 2.5, 1.55, 'run on every window', size=10)
    _arrow(right, (0.1, 0.0), (1.1, 0.0), color=INK)
    _arrow(right, (4.0, 0.0), (4.8, 0.0), color=INK)
    _label(right, 5.0, 0.55, 'green window:', size=10, ha='left', color=SLIDE)
    _label(right, 5.0, 0.2, '"no slip"', size=10, ha='left', color=SLIDE, weight='bold')
    _label(right, 5.0, -0.35, 'red window:', size=10, ha='left', color=GRIP)
    _label(right, 5.0, -0.7, '"slip"', size=10, ha='left', color=GRIP, weight='bold')
    _label(right, 4.0, -1.8, 'answer comes out once per window,', size=9, color=MUTED)
    _label(right, 4.0, -2.15, 'so a short window means a fast answer', size=9, color=MUTED)
    _save(fig, SLIP, 'one-window-at-a-time.svg')


def slip_from_the_edge() -> None:
    """Dots on a gel pad at three moments: stuck, slipping at the edge, sliding all over."""
    fig, ax = plt.subplots(figsize=(11.5, 5.0), facecolor='white')
    _axes(ax, (-1.9, 11.9), (-2.9, 2.7))

    def stuck(x: float, y: float) -> tuple[float, float]:
        d = math.hypot(x, y)
        return (0.14 * max(0.0, 1 - d / 1.3), 0.0)

    def edge(x: float, y: float) -> tuple[float, float]:
        d = math.hypot(x, y)
        if d < 0.6:
            return (0.14 * (1 - d / 1.3), 0.0)
        if d < 1.1:
            return (0.28, 0.0)
        return (0.0, 0.0)

    def whole(x: float, y: float) -> tuple[float, float]:
        d = math.hypot(x, y)
        return (0.28, 0.0) if d < 1.1 else (0.0, 0.0)

    for cx, fn, title, note in ((0.0, stuck, '1  Held', 'the whole contact sticks;\n'
                                 'dots lean a little'),
                                (5.0, edge, '2  Starting to slip', 'the rim of the contact\n'
                                 'slides first; the centre sticks'),
                                (10.0, whole, '3  Slipping', 'every dot in the contact\n'
                                 'moves the same way')):
        _marker_grid(ax, cx, 0.0, fn, title, '')
        ax.add_patch(Circle((cx, 0.0), 1.1, fill=False, edgecolor=MUTED, lw=1.0,
                            ls='--', zorder=2))
        _caption(ax, cx, -2.2, note, size=9)
    _label(ax, 5.0, 2.45, 'Grey ring: where a dot sits when nothing touches.   '
           'Black dot: where it is now.   Dashed circle: the contact.', size=9)
    _label(ax, 5.0, -2.75, 'Stage 2 is the moment a slip model tries to catch: '
           'there is still time to squeeze harder.', size=10, color=GRIP)
    _save(fig, SLIP, 'slip-starts-at-the-edge.svg')


# --------------------------------------------------------------------------
# 04_collision-and-failure-detection
# --------------------------------------------------------------------------

COLL: str = 'collision-and-failure-detection'


def expected_vs_measured() -> None:
    """Predicted and measured torque on one joint, and the gap that flags a collision."""
    t = np.linspace(0.0, 3.0, 600)
    expected = 12 + 6 * np.sin(1.8 * t) + 2 * np.sin(4.1 * t)
    hit = np.where(t > 1.9, 9.0 * (1 - np.exp(-(t - 1.9) / 0.04)), 0.0)
    hit *= np.where(t > 2.15, np.exp(-(t - 2.15) / 0.05), 1.0)
    measured = expected + 0.35 * RNG.standard_normal(len(t)) + hit
    gap = np.abs(measured - expected)
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10.0, 6.4), facecolor='white',
                                      sharex=True, gridspec_kw={'height_ratios': [1.3, 1]})
    _plot_axes(top, '', 'torque on joint 2')
    top.plot(t, expected, color=AXIS_Z, lw=2.0, ls='--', label='what the model expects')
    top.plot(t, measured, color=WRIST, lw=1.0, label='what the motor measures')
    top.legend(loc='upper left', frameon=False, fontsize=9)
    top.set_yticklabels([])
    top.annotate('the forearm\nhits a box', xy=(1.95, measured[t > 1.95][0] + 2),
                 xytext=(2.35, 25), fontsize=9, color=GRIP,
                 arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.0})
    top.set_ylim(0, 29)
    _plot_axes(bottom, 'time (seconds)', 'the gap')
    bottom.plot(t, gap, color=INK, lw=1.0)
    bottom.axhline(3.0, color=GRIP, lw=1.2, ls='--')
    bottom.text(0.05, 3.5, 'stop line', color=GRIP, fontsize=9)
    first = t[np.argmax(gap > 3.0)]
    bottom.axvline(first, color=GRIP, lw=0.8, ls=':')
    bottom.text(first + 0.3, 7.5, 'gap crosses the line:\nthe arm stops', color=GRIP,
                fontsize=9, va='top')
    bottom.set_ylim(0, 10)
    bottom.set_yticklabels([])
    top.set_title('A drawn example, not a measurement', fontsize=11, color=MUTED)
    _save(fig, COLL, 'expected-against-measured.svg')


def which_link_was_hit() -> None:
    """A push on the forearm shows up at the joints before it, and not at the ones after."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 5.0), facecolor='white',
                                      gridspec_kw={'width_ratios': [1.2, 1]})
    _axes(left, (-1.6, 6.6), (-0.8, 5.2))
    _floor(left, -1.2, 6.2)
    pts = _chain((0.0, 0.3), [75.0, -85.0, -40.0], [2.3, 2.3, 0.8])
    _draw_arm(left, pts)
    for k, p in enumerate(pts[:-1]):
        off = [(-0.55, 0.0), (-0.3, 0.4), (0.0, 0.45)][k]
        _label(left, p[0] + off[0], p[1] + off[1], f'J{k + 1}', size=10, weight='bold')
    mid = ((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2)
    left.add_patch(Rectangle((mid[0] - 0.4, 0.0), 0.8, mid[1] - 0.12, facecolor=GRID,
                             edgecolor=INK, lw=0.8, zorder=1))
    left.plot([mid[0]], [mid[1]], '*', ms=18, color=GRIP, zorder=7)
    _label(left, mid[0] + 0.75, mid[1] - 1.6, 'the forearm\ntouches a box', size=9,
           color=GRIP, ha='left')
    _arrow(left, (mid[0] + 0.7, mid[1] - 1.35), (mid[0] + 0.15, mid[1] - 0.2), color=GRIP,
           lw=1.0)
    _title(left, 2.5, 4.9, 'A contact on link 2')
    _axes(right, (-0.2, 4.6), (-0.8, 5.2))
    right.set_aspect('auto')
    heights = [2.4, 1.6, 0.05]
    for k, h in enumerate(heights):
        right.add_patch(Rectangle((0.5 + k * 1.3, 0.4), 0.8, h,
                                  facecolor=GRIP if h > 0.1 else GRID, edgecolor=INK,
                                  lw=0.8))
        _label(right, 0.9 + k * 1.3, 0.1, f'J{k + 1}', size=10, weight='bold')
    right.plot([0.3, 4.3], [0.4, 0.4], color=MUTED, lw=1.0)
    _label(right, 3.5, 1.0, 'no change:\nthe push is\nafter this joint', size=9,
           color=MUTED)
    _title(right, 2.2, 4.9, 'Gap at each joint')
    _caption(right, 2.2, 4.3, 'expected torque minus measured torque')
    _save(fig, COLL, 'which-link-was-hit.svg')


def normal_band() -> None:
    """Many good picks make a band; a pick that leaves the band is flagged as odd."""
    t = np.linspace(0.0, 5.0, 400)

    def good(scale: float, shift: float) -> np.ndarray:
        up = 1 / (1 + np.exp(-(t - 1.0 - shift) * 12))
        down = 1 / (1 + np.exp(-(t - 4.0 - shift) * 12))
        return scale * (up - down) + 0.05 * RNG.standard_normal(len(t))

    fig, ax = plt.subplots(figsize=(10.0, 4.6), facecolor='white')
    _plot_axes(ax, 'time (seconds)', 'weight felt at the wrist')
    for _ in range(25):
        ax.plot(t, good(RNG.uniform(1.9, 2.1), RNG.uniform(-0.08, 0.08)), color=GRID, lw=1.0)
    bad = good(2.0, 0.0)
    fall = np.exp(-np.clip(t - 2.4, 0, None) / 0.05)
    bad = bad * fall + (1 - fall) * 0.05 * RNG.standard_normal(len(t))
    ax.plot(t, bad, color=GRIP, lw=2.0)
    ax.plot([], [], color=GRID, lw=2, label='25 picks that went well')
    ax.plot([], [], color=GRIP, lw=2, label='this pick')
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.annotate('the weight vanishes in the middle\nof the carry: the mug fell',
                xy=(2.47, 0.9), xytext=(2.75, 0.95), fontsize=9, va='center', color=GRIP,
                arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.0})
    ax.text(1.1, 2.35, 'lift', fontsize=9, color=MUTED)
    ax.text(3.7, 2.35, 'put down', fontsize=9, color=MUTED)
    ax.set_ylim(-0.3, 2.8)
    ax.set_yticklabels([])
    ax.set_title('A drawn example, not a measurement', fontsize=11, color=MUTED)
    _save(fig, COLL, 'outside-the-normal-band.svg')


# --------------------------------------------------------------------------
# 05_learned-arm-models
# --------------------------------------------------------------------------

ARM: str = 'learned-arm-models'


def textbook_plus_correction() -> None:
    """Torque needed at one joint against speed: textbook line, real dots, learned curve."""
    v = np.linspace(-1.0, 1.0, 400)
    textbook = 2.0 * v
    real = 2.0 * v + 1.4 * np.tanh(v / 0.05) + 0.8 * v
    fig, ax = plt.subplots(figsize=(9.0, 5.2), facecolor='white')
    _plot_axes(ax, 'joint speed (backwards  <-  0  ->  forwards)', 'torque the motor must give')
    vs = RNG.uniform(-1.0, 1.0, 70)
    dots = 2.0 * vs + 1.4 * np.tanh(vs / 0.05) + 0.8 * vs + 0.25 * RNG.standard_normal(70)
    ax.plot(vs, dots, 'o', ms=4, color=MUTED, label='measured on the real arm')
    ax.plot(v, textbook, color=AXIS_Z, lw=2.0, ls='--', label='textbook model (no friction)')
    ax.plot(v, real, color=SLIDE, lw=2.0, label='textbook model + learned correction')
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.annotate('the jump at zero speed:\nfriction the textbook left out',
                xy=(0.03, 1.2), xytext=(0.25, -2.3), fontsize=9, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.0})
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_title('A drawn example, not a measurement', fontsize=11, color=MUTED)
    _save(fig, ARM, 'textbook-plus-correction.svg')


def forward_and_inverse() -> None:
    """Forward model: torques in, next pose out. Inverse model: wanted pose in, torques out."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), facecolor='white')
    for ax, title, now_label, next_label, given, found in (
            (axes[0], 'Forward model', 'now', 'predicted next', 'given: the torques',
             'answers: where the arm will be'),
            (axes[1], 'Inverse model', 'now', 'wanted next', 'given: where you want it',
             'answers: the torques to get there')):
        _axes(ax, (-1.4, 5.0), (-1.3, 4.8))
        _floor(ax, -0.8, 1.0)
        now = _chain((0.0, 0.3), [60.0, -50.0], [2.0, 1.8])
        nxt = _chain((0.0, 0.3), [45.0, -35.0], [2.0, 1.8])
        _draw_arm(ax, nxt, color=LINK_PALE, hinges=False)
        _draw_arm(ax, now)
        _label(ax, now[2][0] + 0.2, now[2][1] + 0.35, now_label, size=10, color=LINK)
        _label(ax, nxt[2][0] + 0.45, nxt[2][1] - 0.35, next_label, size=10, color=MUTED)
        for p, r in ((now[0], 0.55), (now[1], 0.45)):
            ax.add_patch(Arc(p, 2 * r, 2 * r, theta1=200, theta2=320,
                                                color=WRIST, lw=2.0, zorder=6))
            ang = math.radians(320)
            tip = (p[0] + r * math.cos(ang), p[1] + r * math.sin(ang))
            _arrow(ax, (tip[0] - 0.12, tip[1] - 0.08), (tip[0] + 0.02, tip[1] + 0.05),
                   color=WRIST, lw=2.0)
        _label(ax, 1.4, -0.55, 'orange arrows: torque at each joint', size=9, color=WRIST)
        _title(ax, 1.8, 4.5, title)
        _label(ax, 1.8, 4.05, given, size=10)
        _label(ax, 1.8, 3.7, found, size=10, color=SLIDE, weight='bold')
    _save(fig, ARM, 'forward-and-inverse.svg')


def self_model() -> None:
    """Left: the arm waves at random while a camera records it. Right: the learned shape."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 5.2), facecolor='white')
    _axes(left, (-3.6, 4.2), (-0.8, 5.4))
    _floor(left, -3.2, 3.6)
    for _ in range(14):
        a1 = RNG.uniform(35, 145)
        a2 = RNG.uniform(-90, 90)
        pts = _chain((0.0, 0.3), [a1, a2], [2.0, 1.7])
        _draw_arm(left, pts, color=LINK_PALE, width=4, hinges=False)
    pts = _chain((0.0, 0.3), [70.0, -40.0], [2.0, 1.7])
    _draw_arm(left, pts)
    # camera watching
    left.add_patch(Rectangle((3.3, 3.9), 0.6, 0.4, facecolor=INK, zorder=5))
    left.add_patch(Polygon([(3.3, 4.1), (2.2, 4.8), (2.2, 3.3)], closed=True,
                           facecolor=LINK_PALE, alpha=0.4, edgecolor='none', zorder=0))
    _label(left, 3.6, 4.6, 'camera', size=9)
    _title(left, 0.3, 5.15, '1  Move at random and record')
    _caption(left, 0.3, -0.55, 'each frame pairs joint angles with where the arm appeared')

    _axes(right, (-3.6, 4.2), (-0.8, 5.4))
    _floor(right, -3.2, 3.6)
    target = _chain((0.0, 0.3), [120.0, -70.0], [2.0, 1.7])
    xs = RNG.uniform(-3.0, 3.5, 9000)
    ys = RNG.uniform(0.05, 4.8, 9000)

    def near(px: float, py: float) -> bool:
        for a, b in zip(target[:-1], target[1:]):
            ax_, ay_ = a
            bx, by = b
            dx, dy = bx - ax_, by - ay_
            u = max(0.0, min(1.0, ((px - ax_) * dx + (py - ay_) * dy) / (dx * dx + dy * dy)))
            if math.hypot(px - (ax_ + u * dx), py - (ay_ + u * dy)) < 0.2:
                return True
        return False

    inside = np.array([near(x, y) for x, y in zip(xs, ys)])
    right.plot(xs[inside], ys[inside], '.', ms=3.0, color=SLIDE, zorder=3)
    right.plot(xs[~inside][::25], ys[~inside][::25], '.', ms=1.5, color=GRID, zorder=2)
    right.add_patch(Rectangle((-0.35, 0.0), 0.7, 0.3, facecolor=MUTED, zorder=2))
    _title(right, 0.3, 5.15, '2  Ask about new angles')
    _label(right, 2.2, 4.4, 'for a pair of angles\nnever seen before', size=10)
    _caption(right, 0.3, -0.55, 'green: points the model says the arm will fill')
    _save(fig, ARM, 'self-model-from-a-camera.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    three_kinds_of_signal()
    one_pick_five_questions()
    gel_camera_sensor()
    tactile_image_to_answers()
    markers_show_shear()
    grip_force_trace()
    sliding_window()
    slip_from_the_edge()
    expected_vs_measured()
    which_link_was_hit()
    normal_band()
    textbook_plus_correction()
    forward_and_inverse()
    self_model()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
