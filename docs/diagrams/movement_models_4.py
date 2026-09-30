"""Generate the diagrams for two "also used" pages of the movement-models chapter.

The documents are in docs/06_learned-models/06_movement-models/03_also-used/:
03_reward-and-progress-models.md and 04_learning-from-human-video.md. Each picture
illustrates one idea from its own document, and goes to
docs/images/movement-models/<doc-name>/.

Run with:  pixi run python ../docs/diagrams/movement_models_4.py
Add --png <folder> to also write PNG copies for checking by eye.

Where a picture shows a result, the script computes it here with numpy: the
progress scores, the threshold counts, the filtered demonstrations, the
retargeted gripper, the reach check and the grouping of motions into codes. The
inputs are made up for teaching, with fixed random seeds, and are not
measurements from a real robot. The documents say so where it matters.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, Wedge  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'movement-models'
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
OBSTACLE: str = '#9a9a9a'
OBSTACLE_PALE: str = '#e4e4e4'
PURPLE: str = '#7b5aa6'
MUG: str = '#c96f3b'
SKIN: str = '#d9a27a'

Point = tuple[float, float]


# --------------------------------------------------------------------------
# small drawing helpers (same style as movement_models_2.py)
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=7)


def _title(ax: Axes, x: float, y: float, text: str) -> None:
    ax.text(x, y, text, fontsize=12, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 9.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _plot_style(ax: Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=12, weight='bold', color=INK)
    ax.set_xlabel(xlabel, fontsize=10, color=INK)
    ax.set_ylabel(ylabel, fontsize=10, color=INK)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9, colors=INK)


def _arrow(ax: Axes, a: Point, b: Point, color: str = INK, lw: float = 1.6,
           style: str = '-|>', z: int = 6) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=z)


def _mug(ax: Axes, x: float, y: float, w: float = 0.5, h: float = 0.6,
         color: str = MUG) -> None:
    """A mug seen from the side, standing on (x, y)."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=0.8,
                           zorder=4))
    hx = [x + w / 2, x + w / 2 + w * 0.3, x + w / 2 + w * 0.3, x + w / 2]
    hy = [y + h * 0.25, y + h * 0.3, y + h * 0.7, y + h * 0.75]
    ax.plot(hx, hy, color=INK, lw=1.6, zorder=3)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 03_reward-and-progress-models
# --------------------------------------------------------------------------

REWARD_DOC: str = 'reward-and-progress-models'

# The worked example in the document: six frames of one attempt, each turned into
# three numbers by a camera encoder, and the goal picture turned into three numbers.
GOAL: NDArray[np.float64] = np.array([0.9, 0.1, 0.8])
FRAMES: NDArray[np.float64] = np.array([[0.1, 0.7, 0.2], [0.3, 0.6, 0.3], [0.5, 0.4, 0.5],
                                        [0.6, 0.4, 0.5], [0.8, 0.2, 0.7], [0.9, 0.1, 0.8]])


def _progress(frames: NDArray[np.float64], goal: NDArray[np.float64]) -> NDArray[np.float64]:
    """Progress = 1 - (distance to goal now) / (distance to goal at the start)."""
    d = np.linalg.norm(frames - goal, axis=1)
    return 1.0 - d / d[0]


def _episode(kind: str, rng: np.random.Generator, n: int = 40) -> NDArray[np.float64]:
    """A made-up attempt as a path of 8-number embeddings, then its progress curve.

    kind is 'steady' (goes straight to the goal), 'stuck' (stops halfway) or
    'slip' (gets close, drops the mug, starts again).
    """
    start = np.zeros(8)
    goal = np.ones(8)
    t = np.linspace(0, 1, n)
    if kind == 'steady':
        s = t
    elif kind == 'stuck':
        s = np.minimum(t * 1.6, 0.48 + 0.04 * np.sin(12 * t))
    else:
        s = np.where(t < 0.5, t * 1.6, np.where(t < 0.58, 0.8 - (t - 0.5) * 7.5, 0.2 + (t - 0.58)
                                                  * 1.9))
        s = np.clip(s, 0, 1)
    path = start + s[:, None] * (goal - start) + rng.normal(0, 0.035, (n, 8))
    path[0] = start
    return _progress(path, goal)


def progress_along_an_attempt() -> None:
    """The worked example as bars, then three whole attempts as progress curves."""
    fig, axes = _panels(2, (13.0, 4.8))
    p = _progress(FRAMES, GOAL)

    ax = axes[0]
    bars = ax.bar(np.arange(len(p)), p, color=LINK, width=0.6, zorder=3)
    bars[-1].set_color(SLIDE)
    for i, v in enumerate(p):
        ax.text(i, v + 0.03, f'{v:.2f}', ha='center', fontsize=9.5, color=INK)
    for i in range(1, len(p)):
        r = p[i] - p[i - 1]
        ax.text(i - 0.5, -0.2, f'+{r:.2f}', ha='center', fontsize=9, color=WRIST)
    ax.text(-0.55, -0.2, 'reward:', ha='right', fontsize=9, color=WRIST)
    ax.set_ylim(-0.3, 1.18)
    ax.set_xlim(-1.4, 5.6)
    ax.set_xticks(range(len(p)), [f'frame {i}' for i in range(len(p))])
    _plot_style(ax, 'The worked example: six frames of one attempt', '',
                'progress (0 = start, 1 = goal)')
    ax.axhline(0, color=MUTED, lw=0.8)

    ax = axes[1]
    rng = np.random.default_rng(4)
    t = np.linspace(0, 1, 40) * 8.0
    for kind, color, text in (('steady', SLIDE, 'goes straight to the goal'),
                              ('stuck', OBSTACLE, 'gets stuck halfway'),
                              ('slip', GRIP, 'drops the mug, tries again')):
        ax.plot(t, _episode(kind, rng), color=color, lw=2.2, label=text)
    ax.axhline(0.9, color=INK, lw=1, ls=(0, (4, 3)))
    ax.text(0.1, 0.94, 'counted as done above 0.9', fontsize=9, color=INK)
    ax.set_ylim(-0.1, 1.12)
    ax.legend(fontsize=9, loc='lower right', frameon=False)
    _plot_style(ax, 'Three whole attempts, scored frame by frame', 'time (seconds)',
                'progress')
    fig.tight_layout(w_pad=3)
    _save(fig, REWARD_DOC, 'progress-along-an-attempt.svg')


def _classifier_scores() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Made-up scores from a success classifier on 100 real successes and 100 failures."""
    rng = np.random.default_rng(7)
    succ = 1 / (1 + np.exp(-rng.normal(2.0, 1.3, 100)))
    fail = 1 / (1 + np.exp(-rng.normal(-1.5, 1.5, 100)))
    return succ, fail


def choosing_the_threshold() -> None:
    """Score histograms for successes and failures, with three cut-off lines."""
    succ, fail = _classifier_scores()
    fig, ax = plt.subplots(figsize=(11.0, 4.8), facecolor='white')
    bins = np.linspace(0, 1, 21)
    ax.hist(fail, bins=bins, color=GRIP, alpha=0.55, label='attempts that really failed',
            zorder=3)
    ax.hist(succ, bins=bins, color=SLIDE, alpha=0.55,
            label='attempts that really succeeded', zorder=3)
    top = 40
    for th in (0.5, 0.7, 0.9):
        fs = int((fail >= th).sum())
        ms = int((succ < th).sum())
        ax.axvline(th, color=INK, lw=1.2, ls=(0, (4, 3)))
        ax.text(th, top + 1, f'cut-off {th}\n{fs} false successes\n{ms} missed successes',
                ha='center', va='bottom', fontsize=9, color=INK,
                bbox={'facecolor': 'white', 'edgecolor': GRID, 'pad': 3})
    ax.set_ylim(0, top + 14)
    ax.set_xlim(0, 1)
    ax.legend(fontsize=9, loc='upper left', frameon=False, bbox_to_anchor=(0.0, 0.62))
    _plot_style(ax, 'Where you put the cut-off decides which mistake you get',
                'the classifier\'s score: how sure it is that the task succeeded',
                'number of attempts (of 100 each)')
    _save(fig, REWARD_DOC, 'choosing-the-threshold.svg')


def false_success_one_camera() -> None:
    """A mug held above a bowl: the top camera sees 'in', the side camera sees a gap."""
    fig, axes = _panels(2, (12.0, 5.0))

    ax = axes[0]
    _axes(ax, (-2.6, 2.6), (-0.6, 4.4))
    _title(ax, 0, 4.2, 'What really happened (side view)')
    ax.plot([-2.4, 2.4], [0, 0], color=MUTED, lw=1.2)
    bowl = Wedge((0, 0.75), 0.95, 180, 360, facecolor=LINK_PALE, edgecolor=INK, lw=1)
    ax.add_patch(bowl)
    _mug(ax, 0, 1.55, w=0.6, h=0.7)
    ax.plot([-0.45, -0.45, -0.3], [2.9, 2.0, 2.0], color=GRIP, lw=3)
    ax.plot([0.45, 0.45, 0.3], [2.9, 2.0, 2.0], color=GRIP, lw=3)
    ax.plot([-0.45, 0.45], [2.9, 2.9], color=GRIP, lw=3)
    ax.plot([0, 0], [2.9, 3.5], color=LINK, lw=6, solid_capstyle='round')
    _arrow(ax, (-1.1, 0.75), (-1.1, 1.55), color=WRIST, style='<|-|>')
    ax.plot([-1.2, -0.3], [1.55, 1.55], color=WRIST, lw=0.8, ls=(0, (2, 2)))
    _label(ax, -1.25, 1.15, 'gap: the mug is\nstill in the air', size=9.5, color=WRIST,
           ha='right')
    # top camera
    ax.add_patch(Rectangle((-2.3, 3.4), 0.5, 0.35, facecolor=INK, zorder=5))
    _label(ax, -2.05, 3.05, 'top camera', size=9)
    ax.add_patch(Rectangle((2.0, 1.0), 0.35, 0.45, facecolor=INK, zorder=5))
    _label(ax, 2.18, 0.7, 'side\ncamera', size=9)
    _caption(ax, 0, -0.35, 'The gripper has not let go yet.')

    ax = axes[1]
    _axes(ax, (-2.6, 2.6), (-0.6, 4.4))
    _title(ax, 0, 4.2, 'What the top camera sees')
    ax.add_patch(Rectangle((-1.9, 0.3), 3.8, 3.4, facecolor='white', edgecolor=MUTED, lw=1))
    ax.add_patch(Circle((0, 2.0), 1.2, facecolor=LINK_PALE, edgecolor=INK, lw=1))
    ax.add_patch(Circle((0, 2.0), 0.45, facecolor=MUG, edgecolor=INK, lw=0.8, zorder=4))
    ax.plot([0.45, 0.72], [2.0, 2.0], color=INK, lw=3, zorder=3)
    ax.add_patch(Rectangle((-0.12, 1.2), 0.24, 1.6, facecolor=GRIP, alpha=0.6, zorder=5))
    _label(ax, 0, 0.0, 'classifier: "success", score 0.93', size=10.5, color=GRIP,
           weight='bold')
    _caption(ax, 0, -0.4, 'From above, a mug over the bowl and a mug in the bowl look alike.')
    _save(fig, REWARD_DOC, 'false-success-one-camera.svg')


def filtering_demonstrations() -> None:
    """Score 24 made-up demonstrations and keep those that finish and do not go backwards."""
    rng = np.random.default_rng(11)
    n = 24
    finals = np.empty(n)
    drops = np.empty(n)
    for i in range(n):
        kind = 'steady'
        if i in (3, 10, 17):
            kind = 'stuck'
        elif i in (6, 20):
            kind = 'slip'
        p = _episode(kind, rng)
        finals[i] = p[-3:].mean()
        drops[i] = max(0.0, float(np.max(np.maximum.accumulate(p) - p)))
    keep = (finals >= 0.9) & (drops < 0.25)

    fig, ax = plt.subplots(figsize=(11.5, 4.6), facecolor='white')
    colors = [SLIDE if k else GRIP for k in keep]
    ax.bar(np.arange(n) + 1, finals, color=colors, width=0.7, zorder=3)
    for i in range(n):
        if drops[i] >= 0.25:
            ax.text(i + 1, finals[i] + 0.03, 'fell\nback', ha='center', fontsize=8.5,
                    color=GRIP)
    ax.axhline(0.9, color=INK, lw=1.2, ls=(0, (4, 3)))
    ax.text(n + 0.9, 0.9, 'keep if the\nlast score is\nabove 0.9 and\nit never fell\nback by 0.25', fontsize=9, va='center',
            ha='left', color=INK)
    ax.set_xticks(np.arange(n) + 1)
    ax.set_xlim(0.3, n + 0.7)
    ax.set_ylim(0, 1.25)
    _plot_style(ax, f'24 recorded demonstrations: {int(keep.sum())} kept (green), '
                f'{int((~keep).sum())} dropped (red)', 'demonstration number',
                'progress at the end')
    _save(fig, REWARD_DOC, 'filtering-demonstrations.svg')


# --------------------------------------------------------------------------
# 04_learning-from-human-video
# --------------------------------------------------------------------------

VIDEO_DOC: str = 'learning-from-human-video'

# The worked example in the document. Camera-frame points (metres) for three hand
# landmarks, and the camera's pose in the robot's frame from calibration.
CAM_R: NDArray[np.float64] = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]], float)
CAM_T: NDArray[np.float64] = np.array([0.10, 0.0, 0.60])
THUMB_C: NDArray[np.float64] = np.array([0.020, 0.150, 0.520])
INDEX_C: NDArray[np.float64] = np.array([0.075, 0.140, 0.505])
GRIPPER_MAX_M: float = 0.08


def _to_robot(p: NDArray[np.float64]) -> NDArray[np.float64]:
    return CAM_R @ p + CAM_T


def _hand_points() -> NDArray[np.float64]:
    """21 hand landmarks in 2D, in the same order MediaPipe Hands uses (0 = wrist).

    The hand is making a pinch: the thumb tip and the index tip nearly meet.
    """
    return np.array([
        (0.0, 0.0),                                                    # 0 wrist
        (-0.30, 0.25), (-0.58, 0.55), (-0.72, 0.90), (-0.72, 1.22),    # 1-4 thumb
        (-0.25, 1.00), (-0.40, 1.48), (-0.62, 1.78), (-0.86, 1.62),    # 5-8 index
        (0.00, 1.05), (0.00, 1.60), (0.00, 1.95), (0.00, 2.20),        # 9-12 middle
        (0.22, 1.00), (0.28, 1.50), (0.30, 1.82), (0.32, 2.05),        # 13-16 ring
        (0.42, 0.90), (0.52, 1.30), (0.57, 1.55), (0.60, 1.75),        # 17-20 little
    ])


def hand_to_gripper() -> None:
    """21 hand points, the pinch between thumb and index tips, and the gripper it becomes."""
    fig, axes = _panels(2, (12.0, 5.4))
    pts = _hand_points()

    ax = axes[0]
    _axes(ax, (-1.9, 1.4), (-0.4, 2.6))
    _title(ax, -0.25, 2.5, 'A hand pose estimator: 21 points per frame')
    for f in range(5):
        idx = [0] + list(range(1 + 4 * f, 5 + 4 * f))
        ax.plot(pts[idx, 0], pts[idx, 1], color=SKIN, lw=3, zorder=2,
                solid_capstyle='round')
    ax.plot(pts[[1, 5, 9, 13, 17], 0], pts[[1, 5, 9, 13, 17], 1], color=SKIN, lw=3, zorder=2)
    ax.plot(pts[:, 0], pts[:, 1], 'o', color=INK, ms=4, zorder=3)
    for i, name in ((0, '0 wrist'), (4, '4 thumb tip'), (8, '8 index tip')):
        ax.plot(pts[i, 0], pts[i, 1], 'o', color=GRIP, ms=8, zorder=4)
        _label(ax, pts[i, 0] - 0.14 if i else pts[i, 0] + 0.12,
               pts[i, 1] if i else pts[i, 1] - 0.15, name, size=9.5,
               ha='right' if i else 'left', color=GRIP)
    ax.plot(pts[[4, 8], 0], pts[[4, 8], 1], color=WRIST, lw=2, ls=(0, (3, 2)), zorder=3)
    mid = pts[[4, 8]].mean(axis=0)
    _label(ax, mid[0] - 0.14, mid[1], 'pinch', size=9.5, color=WRIST, ha='right')

    thumb = _to_robot(THUMB_C)
    index = _to_robot(INDEX_C)
    centre = (thumb + index) / 2
    width = float(np.clip(np.linalg.norm(thumb - index), 0.0, GRIPPER_MAX_M))

    ax = axes[1]
    _axes(ax, (-1.8, 1.8), (-0.4, 2.6))
    _title(ax, 0, 2.5, 'The gripper command it becomes')
    half = width * 1000 / 2 / 40     # millimetres drawn at 40 mm per unit
    ax.plot([-0.6, 0.6], [1.6, 1.6], color=GRIP, lw=4)
    ax.plot([0, 0], [1.6, 2.1], color=LINK, lw=7, solid_capstyle='round')
    for s in (-1, 1):
        ax.plot([s * half, s * half], [0.7, 1.6], color=GRIP, lw=5, solid_capstyle='butt')
    _arrow(ax, (-half, 0.5), (half, 0.5), color=WRIST, style='<|-|>')
    _label(ax, 0, 0.3, f'opening = pinch distance = {width * 1000:.1f} mm', size=10,
           color=WRIST)
    ax.plot([0], [1.15], '+', color=INK, ms=12, mew=2)
    _label(ax, 0.12, 1.15, 'centre = midpoint of the two tips', size=9, ha='left')
    _caption(ax, 0, -0.1, f'In the robot\'s frame: x {centre[0]:.3f}, y {centre[1]:.3f}, '
             f'z {centre[2]:.3f} metres')
    _save(fig, VIDEO_DOC, 'hand-to-gripper.svg')


def pinch_over_time() -> None:
    """Pinch distance from a tracker over a grasp, and the cleaned gripper command."""
    rng = np.random.default_rng(5)
    t = np.linspace(0, 4, 121)
    true = np.where(t < 1.0, 60 + 45 * t, np.where(t < 2.0, 105 - 80 * (t - 1.0),
                                                   np.where(t < 3.2, 25.0, 25 + 60 * (t - 3.2))))
    true = np.clip(true, 25, 110)
    raw = true + rng.normal(0, 4.0, t.size)
    raw[62:66] = [5, 3, 8, 6]           # the hand hides the index finger for a moment
    k = 9
    padded = np.pad(raw, (k // 2, k // 2), mode='edge')
    median = np.array([np.median(padded[i:i + k]) for i in range(raw.size)])
    command = np.clip(median, 0, GRIPPER_MAX_M * 1000)

    fig, ax = plt.subplots(figsize=(11.0, 4.6), facecolor='white')
    ax.plot(t, raw, color=OBSTACLE, lw=1.2, label='pinch distance from the tracker')
    ax.plot(t, command, color=LINK, lw=2.4, label='gripper command after cleaning')
    ax.axhline(80, color=GRIP, lw=1, ls=(0, (4, 3)))
    ax.text(0.05, 84, 'gripper fully open: 80 mm', fontsize=9, color=GRIP)
    ax.annotate('index finger hidden:\ntracker jumps to near 0', xy=(t[63], 5),
                xytext=(2.3, 60), fontsize=9, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1})
    ax.text(2.75, 31, 'holding the mug', fontsize=9, color=INK, ha='center')
    ax.set_ylim(-5, 125)
    ax.legend(fontsize=9, loc='upper right', frameon=False)
    _plot_style(ax, 'A grasp in a video, turned into a gripper opening', 'time (seconds)',
                'millimetres')
    _save(fig, VIDEO_DOC, 'pinch-over-time.svg')


def outside_the_reach() -> None:
    """A hand path retargeted into the robot's frame, checked against the arm's reach."""
    inner, outer = 0.20, 0.85
    s = np.linspace(0, 1, 80)
    x = 0.35 + 0.65 * s
    y = -0.45 + 0.9 * s + 0.12 * np.sin(2 * np.pi * s)
    r = np.hypot(x, y)
    ok = (r >= inner) & (r <= outer)

    fig, ax = plt.subplots(figsize=(7.4, 6.4), facecolor='white')
    _axes(ax, (-0.95, 1.3), (-0.95, 1.0))
    ax.add_patch(Circle((0, 0), outer, facecolor=LINK_PALE, edgecolor=LINK, lw=1.2,
                        alpha=0.6))
    ax.add_patch(Circle((0, 0), inner, facecolor='white', edgecolor=LINK, lw=1.2))
    ax.plot([0], [0], 's', color=INK, ms=10)
    _label(ax, 0, -0.08, 'arm base', size=9)
    _label(ax, -0.35, 0.45, 'the arm can reach\nanywhere in blue', size=9.5, color=LINK)
    for i in range(len(s) - 1):
        good = ok[i] and ok[i + 1]
        ax.plot(x[i:i + 2], y[i:i + 2], color=SLIDE if good else GRIP, lw=3.2,
                solid_capstyle='round')
    ax.plot([x[0]], [y[0]], 'o', color=INK, ms=7)
    _label(ax, x[0] + 0.02, y[0] - 0.08, 'start', size=9)
    ax.plot([x[-1]], [y[-1]], '*', color=INK, ms=13)
    _label(ax, x[-1] - 0.02, y[-1] + 0.08, 'end', size=9)
    frac = 100 * (1 - ok.mean())
    _title(ax, 0.17, 0.95, 'A person\'s hand path, moved into the robot\'s frame')
    _caption(ax, 0.17, -0.9, f'Red: {frac:.0f} % of the path is out of the arm\'s reach.\n'
             'Nothing in the video warns you.')
    _save(fig, VIDEO_DOC, 'outside-the-reach.svg')


def _kmeans(points: NDArray[np.float64], k: int, rng: np.random.Generator,
            steps: int = 20) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    centres = points[rng.choice(len(points), k, replace=False)]
    labels = np.zeros(len(points), dtype=np.int64)
    for _ in range(steps):
        dist = np.linalg.norm(points[:, None, :] - centres[None, :, :], axis=2)
        labels = np.argmin(dist, axis=1)
        centres = np.array([points[labels == j].mean(axis=0) for j in range(k)])
    return centres, labels


def latent_actions() -> None:
    """Frame-to-frame motions from video, grouped into four codes with no labels."""
    rng = np.random.default_rng(2)
    true_moves = np.array([[3.0, 0.0], [-3.0, 0.0], [0.0, 3.0], [0.0, -3.0]])
    which = rng.integers(0, 4, 240)
    moves = true_moves[which] + rng.normal(0, 0.7, (240, 2))
    centres, labels = _kmeans(moves, 4, rng)
    order = np.argsort(np.arctan2(centres[:, 1], centres[:, 0]))
    palette = [LINK, SLIDE, WRIST, PURPLE]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.15]})
    ax = axes[0]
    for code, j in enumerate(order):
        m = labels == j
        ax.scatter(moves[m, 0], moves[m, 1], s=14, color=palette[code], alpha=0.7, zorder=3)
        ax.plot(centres[j, 0], centres[j, 1], 'X', color=INK, ms=11, zorder=4)
        u = centres[j] / np.linalg.norm(centres[j])
        ax.text(u[0] * 5.6, u[1] * 5.6, f'code {code}', ha='center',
                va='center', fontsize=10, color=palette[code], weight='bold')
    ax.set_xlim(-7, 7)
    ax.set_ylim(-7, 7)
    ax.set_aspect('equal')
    _plot_style(ax, 'How the object moved between two frames', 'sideways (cm)',
                'up and down (cm)')

    ax = axes[1]
    _axes(ax, (0, 10), (0, 7.2))
    _title(ax, 5, 6.9, 'Codes found without labels, then named with robot data')
    _label(ax, 2.3, 6.1, 'code, from video', size=10, weight='bold')
    _label(ax, 7.3, 6.1, 'what it means on this arm', size=10, weight='bold')
    _caption(ax, 7.3, 5.65, '(learned from a few robot demonstrations)', size=9)
    words = {}
    for code, j in enumerate(order):
        c = centres[j]
        if abs(c[0]) > abs(c[1]):
            words[code] = 'move the gripper right' if c[0] > 0 else 'move the gripper left'
        else:
            words[code] = 'move the gripper up' if c[1] > 0 else 'move the gripper down'
    for code in range(4):
        y = 4.8 - code * 1.2
        c = centres[order[code]]
        ax.add_patch(Rectangle((1.3, y - 0.35), 2.0, 0.7, facecolor=palette[code],
                               edgecolor=INK, lw=0.8))
        _label(ax, 2.3, y, f'code {code}', size=10, color='white', weight='bold')
        _arrow(ax, (3.6, y), (4.9, y), color=MUTED)
        _label(ax, 5.1, y + 0.17, words[code], size=10, ha='left')
        _label(ax, 5.1, y - 0.2, f'centre ({c[0]:+.1f}, {c[1]:+.1f}) cm per frame', size=9,
               ha='left', color=MUTED)
    fig.tight_layout(w_pad=2)
    _save(fig, VIDEO_DOC, 'latent-actions.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    progress_along_an_attempt()
    choosing_the_threshold()
    false_success_one_camera()
    filtering_demonstrations()
    hand_to_gripper()
    pinch_over_time()
    outside_the_reach()
    latent_actions()


if __name__ == '__main__':
    main()
