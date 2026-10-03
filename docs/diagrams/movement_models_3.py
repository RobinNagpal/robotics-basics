"""Generate the diagrams for three additions to Book 6.

The documents are:

- docs/07_learned-models/06_movement-models/02_most-used/04_actions-and-observations.md
  (pictures go to docs/images/movement-models/actions-and-observations/)
- the section "Telling the policy what to do: goals and many tasks" in
  docs/07_learned-models/06_movement-models/02_most-used/01_behaviour-cloning.md
  (pictures go to docs/images/movement-models/behaviour-cloning/)
- the section "Learning only the part physics gets wrong: residual models" in
  docs/07_learned-models/08_world-models/02_most-used/01_learned-dynamics-models.md
  (pictures go to docs/images/world-models/learned-dynamics-models/)

Run with:  pixi run python ../docs/diagrams/movement_models_3.py
or:        python3 docs/diagrams/movement_models_3.py --png <folder>
The --png option also writes PNG copies for checking by eye.

Every number in these pictures is computed here, with numpy only, from small
made-up scenes: a flat three-joint arm, reaching paths, a pushed block. The
script also prints the numbers that the documents quote, so each one can be
checked by running it again.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
GOOD: str = '#2a9d3f'
GOOD_PALE: str = '#d3ecd8'
BAD: str = '#e05555'
BAD_PALE: str = '#f6d5d5'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
PURPLE: str = '#7b5aa6'
MUG: str = '#c96f3b'
TABLE: str = '#efe6d8'

Arr = NDArray[np.float64]

ACT_DOC: str = 'movement-models/actions-and-observations'
BC_DOC: str = 'movement-models/behaviour-cloning'
DYN_DOC: str = 'world-models/learned-dynamics-models'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _plot_axes(ax: Axes) -> None:
    """A plain chart: light grid, no top or right frame."""
    ax.set_facecolor('white')
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9.5)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=8)


def _title(ax: Axes, text: str) -> None:
    ax.set_title(text, fontsize=12, color=INK, weight='bold', pad=10)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = INK,
           lw: float = 1.6, z: int = 6) -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=z)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder.split("/")[-1]}__{name[:-4]}.png',
                    bbox_inches='tight', pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# a flat three-joint arm, used by the actions page
# --------------------------------------------------------------------------

def _fk(q: Arr, lengths: Arr) -> Arr:
    """Joint positions of a flat arm. q are relative joint angles in radians."""
    pts = [np.zeros(2)]
    heading = 0.0
    for qi, li in zip(q, lengths):
        heading += qi
        pts.append(pts[-1] + li * np.array([math.cos(heading), math.sin(heading)]))
    return np.array(pts)


def _ik(x: float, y: float, phi: float, lengths: Arr, elbow: int = 1) -> Arr:
    """Joint angles that put the gripper at (x, y), pointing at angle phi."""
    l1, l2, l3 = lengths
    wx = x - l3 * math.cos(phi)
    wy = y - l3 * math.sin(phi)
    c2 = (wx * wx + wy * wy - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    q2 = elbow * math.acos(max(-1.0, min(1.0, c2)))
    q1 = math.atan2(wy, wx) - math.atan2(l2 * math.sin(q2), l1 + l2 * math.cos(q2))
    q3 = phi - q1 - q2
    return np.array([q1, q2, q3])


def _ik_up(x: float, y: float, phi: float, lengths: Arr) -> Arr:
    """The elbow-up answer: the one whose elbow is above the shoulder."""
    q = _ik(x, y, phi, lengths, elbow=1)
    return q if _fk(q, lengths)[1, 1] >= 0.05 else _ik(x, y, phi, lengths, elbow=-1)


def _draw_arm(ax: Axes, q: Arr, lengths: Arr, color: str, base: tuple[float, float] = (0, 0),
              width: float = 7) -> Arr:
    pts = _fk(q, lengths) + np.array(base)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=width, solid_capstyle='round', zorder=3)
    for p in pts[:-1]:
        ax.plot([p[0]], [p[1]], 'o', color=JOINT, ms=8, zorder=4)
    # two short fingers at the tip, pointing along the last link
    tip = pts[-1]
    d = (pts[-1] - pts[-2]) / np.linalg.norm(pts[-1] - pts[-2])
    n = np.array([-d[1], d[0]])
    for side in (1, -1):
        root = tip + side * 0.025 * n
        end = root + 0.04 * d
        ax.plot([tip[0], root[0], end[0]], [tip[1], root[1], end[1]], color=BAD, lw=3,
                solid_capstyle='round', zorder=5)
    return pts


def _deg(q: Arr) -> str:
    return ', '.join(f'{math.degrees(v):.0f}°' for v in q)


# --------------------------------------------------------------------------
# 04_actions-and-observations
# --------------------------------------------------------------------------

ARM_A: Arr = np.array([0.30, 0.25, 0.10])
ARM_B: Arr = np.array([0.40, 0.32, 0.10])
TARGET: tuple[float, float, float] = (0.40, 0.10, -math.pi / 2)   # x, y, pointing down


def joints_or_gripper_pose() -> None:
    """Two different arms put the gripper at the same pose with different joint angles."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), facecolor='white')
    x, y, phi = TARGET
    for ax, lengths, name, color in ((axes[0], ARM_A, 'Arm A: links 30, 25 and 10 cm', LINK),
                                     (axes[1], ARM_B, 'Arm B: links 40, 32 and 10 cm', PURPLE)):
        _axes(ax, (-0.12, 0.62), (-0.14, 0.62))
        ax.add_patch(Rectangle((0.22, -0.06), 0.36, 0.06, facecolor=TABLE, edgecolor=MUTED,
                               lw=0.8, zorder=1))
        ax.add_patch(Rectangle((-0.06, -0.06), 0.12, 0.06, facecolor='#bbbbbb',
                               edgecolor=INK, lw=0.8, zorder=2))
        q = _ik_up(x, y, phi, lengths)
        _draw_arm(ax, q, lengths, color)
        ax.plot([x], [y - 0.07], marker='s', color=MUG, ms=16, zorder=2)
        _title(ax, name)
        _label(ax, 0.25, -0.105, f'joint angles: {_deg(q)}', size=10.5, color=color,
               weight='bold')
        _label(ax, 0.25, 0.585, 'gripper pose: x = 40 cm, y = 10 cm, pointing down',
               size=10.5, color=BAD, weight='bold')
        print(f'  {name}: joints {_deg(q)}')
    _save(fig, ACT_DOC, 'joints-or-gripper-pose.svg')


def _reach_paths(rng: np.random.Generator, base_shift: Arr, n_paths: int = 30,
                 steps: int = 25) -> tuple[Arr, Arr]:
    """Straight-ish reaches from a home spot to a mug, in the robot's own base frame.

    base_shift is where the table's centre sits in that robot's frame. Returns the
    absolute targets at every step and the change from one step to the next.
    """
    targets = []
    deltas = []
    for _ in range(n_paths):
        start = base_shift + np.array([-0.10, 0.20]) + rng.normal(0, 0.015, 2)
        goal = base_shift + rng.uniform([-0.08, -0.08], [0.12, 0.08])
        t = np.linspace(0, 1, steps + 1)
        s = 3 * t ** 2 - 2 * t ** 3                     # smooth start and stop
        path = start + (goal - start) * s[:, None]
        path += rng.normal(0, 0.002, path.shape)
        targets.append(path[1:])
        deltas.append(np.diff(path, axis=0))
    return np.concatenate(targets), np.concatenate(deltas)


def absolute_or_relative() -> None:
    """Absolute targets from two robots land in different places; step changes overlap."""
    rng = np.random.default_rng(3)
    abs_a, del_a = _reach_paths(rng, np.array([0.45, 0.00]))
    abs_b, del_b = _reach_paths(rng, np.array([0.60, -0.25]))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), facecolor='white')

    ax = axes[0]
    _plot_axes(ax)
    ax.scatter(abs_a[:, 0] * 100, abs_a[:, 1] * 100, s=5, color=LINK, alpha=0.5,
               label='robot A')
    ax.scatter(abs_b[:, 0] * 100, abs_b[:, 1] * 100, s=5, color=PURPLE, alpha=0.5,
               label='robot B')
    ax.set_xlabel('target x in the robot\'s own frame (cm)', fontsize=10)
    ax.set_ylabel('target y (cm)', fontsize=10)
    ax.set_aspect('equal')
    ax.set_xlim(20, 80)
    ax.set_ylim(-40, 30)
    ax.legend(loc='upper right', fontsize=9.5, markerscale=3, frameon=False)
    _title(ax, 'Absolute targets: two separate clouds')

    ax = axes[1]
    _plot_axes(ax)
    ax.scatter(del_a[:, 0] * 1000, del_a[:, 1] * 1000, s=5, color=LINK, alpha=0.5,
               label='robot A')
    ax.scatter(del_b[:, 0] * 1000, del_b[:, 1] * 1000, s=5, color=PURPLE, alpha=0.5,
               label='robot B')
    ax.set_xlabel('change in x per step (mm)', fontsize=10)
    ax.set_ylabel('change in y per step (mm)', fontsize=10)
    ax.set_aspect('equal')
    ax.set_xlim(-6, 25)
    ax.set_ylim(-26, 8)
    ax.legend(loc='upper right', fontsize=9.5, markerscale=3, frameon=False)
    _title(ax, 'Changes from where the gripper is: one cloud')
    fig.tight_layout(w_pad=3)
    print(f'  mean absolute target A {abs_a.mean(0) * 100} cm, B {abs_b.mean(0) * 100} cm')
    print(f'  mean step change A {del_a.mean(0) * 1000} mm, B {del_b.mean(0) * 1000} mm')
    _save(fig, ACT_DOC, 'absolute-or-relative.svg')


def _rotz(theta: float, tilt: float = 0.0) -> Arr:
    c, s = math.cos(theta), math.sin(theta)
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    ct, st = math.cos(tilt), math.sin(tilt)
    rx = np.array([[1, 0, 0], [0, ct, -st], [0, st, ct]])
    return rz @ rx


def _yaw_from_matrix(r: Arr) -> float:
    return math.atan2(r[1, 0], r[0, 0])


def _quat_from_matrix(r: Arr) -> Arr:
    """(x, y, z, w) with w kept positive, as many libraries return it."""
    w = math.sqrt(max(0.0, 1 + r[0, 0] + r[1, 1] + r[2, 2])) / 2
    if w > 1e-6:
        x = (r[2, 1] - r[1, 2]) / (4 * w)
        y = (r[0, 2] - r[2, 0]) / (4 * w)
        z = (r[1, 0] - r[0, 1]) / (4 * w)
    else:
        x = math.sqrt(max(0.0, 1 + r[0, 0] - r[1, 1] - r[2, 2])) / 2
        y = (r[0, 1] + r[1, 0]) / (4 * x) if x > 1e-6 else 0.0
        z = math.sqrt(max(0.0, 1 - r[0, 0] - r[1, 1] + r[2, 2])) / 2
    q = np.array([x, y, z, w])
    return q if q[3] >= 0 else -q


def rotation_number_jumps() -> None:
    """The gripper turns smoothly past 180°. Euler angles and quaternions jump; 6 numbers do not."""
    t = np.linspace(0, 1, 241)
    theta = np.radians(150 + 60 * t)              # 150° to 210°, one smooth turn
    tilt = math.radians(10)
    mats = [_rotz(th, tilt) for th in theta]
    yaw = np.degrees([_yaw_from_matrix(r) for r in mats])
    quat = np.array([_quat_from_matrix(r) for r in mats])
    six = np.array([np.concatenate([r[:, 0], r[:, 1]]) for r in mats])

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), facecolor='white')
    turned = np.degrees(theta)
    ax = axes[0]
    _plot_axes(ax)
    ax.plot(turned, yaw, color=BAD, lw=2.2)
    ax.set_ylim(-200, 200)
    ax.set_yticks([-180, -90, 0, 90, 180])
    ax.set_ylabel('yaw number (degrees)', fontsize=10)
    _title(ax, 'Three angles: yaw jumps by 360°')

    ax = axes[1]
    _plot_axes(ax)
    for i, (name, col) in enumerate((('x', LINK), ('y', GOOD), ('z', PURPLE), ('w', WRIST))):
        ax.plot(turned, quat[:, i], color=col, lw=2.0, label=name)
    ax.set_ylim(-1.15, 1.15)
    ax.legend(loc='center right', bbox_to_anchor=(1.0, 0.7), fontsize=9, ncol=2,
              frameon=False)
    ax.set_ylabel('quaternion numbers', fontsize=10)
    _title(ax, 'Quaternion (w kept positive): jumps')

    ax = axes[2]
    _plot_axes(ax)
    cols = (LINK, GOOD, PURPLE, WRIST, BAD, MUTED)
    for i in range(6):
        ax.plot(turned, six[:, i], color=cols[i], lw=2.0)
    ax.set_ylim(-1.15, 1.15)
    ax.set_ylabel('the six numbers', fontsize=10)
    _title(ax, 'Six numbers: smooth all the way')
    for ax in axes:
        ax.axvline(180, color=MUTED, lw=1, ls='--')
        ax.set_xlabel('how far the gripper has turned (degrees)', fontsize=10)
        ax.set_xlim(150, 210)
        ax.set_xticks([150, 165, 180, 195, 210])
    fig.tight_layout(w_pad=2.5)
    i179 = int(np.argmin(abs(turned - 179)))
    i181 = int(np.argmin(abs(turned - 181)))
    print(f'  yaw at 179°: {yaw[i179]:.1f}, at 181°: {yaw[i181]:.1f}')
    print(f'  quat at 179°: {np.round(quat[i179], 3)}, at 181°: {np.round(quat[i181], 3)}')
    print(f'  six at 179°: {np.round(six[i179], 3)}, at 181°: {np.round(six[i181], 3)}')
    _save(fig, ACT_DOC, 'rotation-number-jumps.svg')


def _demo_numbers(rng: np.random.Generator, n: int = 3000) -> dict[str, Arr]:
    """Numbers from a made-up set of recordings: one of each kind a policy sees."""
    return {
        'shoulder angle (rad)': rng.normal(0.4, 0.6, n),
        'wrist speed (rad/s)': rng.normal(0.0, 2.5, n),
        'gripper width (m)': np.clip(rng.choice([0.005, 0.07], n) + rng.normal(0, 0.004, n),
                                     0, 0.08),
        'change in x (m)': rng.normal(0.002, 0.004, n),
    }


def normalising_each_number() -> None:
    """Four numbers on their own scales, then after taking off the mean and dividing by the spread."""
    rng = np.random.default_rng(7)
    data = _demo_numbers(rng)
    names = list(data)
    cols = (LINK, PURPLE, GOOD, WRIST)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.4), facecolor='white')
    for panel, ax in enumerate(axes):
        _plot_axes(ax)
        for i, name in enumerate(names):
            v = data[name]
            if panel == 1:
                v = (v - v.mean()) / v.std()
            lo, hi = np.percentile(v, [1, 99])
            q1, q3 = np.percentile(v, [25, 75])
            yv = len(names) - 1 - i
            ax.plot([lo, hi], [yv, yv], color=cols[i], lw=2, solid_capstyle='butt')
            ax.add_patch(Rectangle((q1, yv - 0.18), max(q3 - q1, 1e-4), 0.36,
                                   facecolor=cols[i], edgecolor=cols[i], zorder=3))
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(list(reversed(names)) if panel == 0 else [''] * len(names),
                           fontsize=10)
        ax.set_ylim(-0.7, len(names) - 0.3)
    axes[0].set_xlim(-8, 8)
    axes[0].set_xlabel('value, in its own unit', fontsize=10)
    _title(axes[0], 'As recorded: the small ones vanish')
    axes[1].set_xlim(-3.2, 3.2)
    axes[1].set_xlabel('value after normalising (spreads of about 1)', fontsize=10)
    _title(axes[1], 'After normalising: all the same size')
    fig.tight_layout(w_pad=2)
    for name in names:
        v = data[name]
        print(f'  {name}: mean {v.mean():.4f}, std {v.std():.4f}, min {v.min():.4f}, '
              f'max {v.max():.4f}')
    # what an error of one "spread" in each number adds to a plain squared-error loss
    spreads = np.array([data[k].std() for k in names])
    share = spreads ** 2 / (spreads ** 2).sum()
    print('  share of raw loss from an error of one spread each:',
          {k: f'{s * 100:.4f}%' for k, s in zip(names, share)})
    _save(fig, ACT_DOC, 'normalising-each-number.svg')


def worked_step_numbers() -> None:
    """The numbers quoted in the page's worked example (printed, not drawn)."""
    q_now = _ik_up(0.40, 0.10, -math.pi / 2, ARM_A)
    q_next = _ik_up(0.39, 0.10, -math.pi / 2 + math.radians(2), ARM_A)
    tip_now = _fk(q_now, ARM_A)[-1]
    tip_next = _fk(q_next, ARM_A)[-1]
    print(f'  joints now {np.round(np.degrees(q_now), 2)}, next {np.round(np.degrees(q_next), 2)}')
    print(f'  joint change {np.round(np.degrees(q_next - q_now), 2)} deg')
    print(f'  tip now {np.round(tip_now * 100, 2)} cm, next {np.round(tip_next * 100, 2)} cm')
    r = _rotz(math.radians(30))
    print(f'  6 numbers for 30° about z: {np.round(np.concatenate([r[:, 0], r[:, 1]]), 3)}')
    raw = np.array([0.80, 0.55, 0.05, -0.45, 0.84, 0.02])   # a network's untidy guess
    a = raw[:3] / np.linalg.norm(raw[:3])
    b = raw[3:] - a * (a @ raw[3:])
    b /= np.linalg.norm(b)
    c = np.cross(a, b)
    print(f'  tidied columns: a {np.round(a, 3)}, b {np.round(b, 3)}, c {np.round(c, 3)}')
    print(f'  that is a turn of {math.degrees(math.atan2(a[1], a[0])):.1f}° about z')
    avg = (179 + -179) / 2
    print(f'  average of yaw 179 and -179 = {avg}')


# --------------------------------------------------------------------------
# 01_behaviour-cloning: goals and many tasks
# --------------------------------------------------------------------------

BINS: dict[str, Arr] = {'red': np.array([-0.25, 0.45]), 'blue': np.array([0.25, 0.45])}


def _scene(ax: Axes, mug: tuple[float, float] | None, title: str, x0: float, y0: float,
           w: float = 1.6, h: float = 1.15) -> None:
    """A small top-down picture: table, two bins, and maybe a mug."""
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor=TABLE, edgecolor=MUTED, lw=1, zorder=1))
    for name, dx in (('red', 0.35), ('blue', 1.05)):
        col = BAD if name == 'red' else LINK
        ax.add_patch(Rectangle((x0 + dx, y0 + 0.6), 0.35, 0.35, facecolor='white',
                               edgecolor=col, lw=2.2, zorder=2))
    if mug is not None:
        ax.add_patch(Circle((x0 + mug[0], y0 + mug[1]), 0.1, facecolor=MUG, edgecolor=INK,
                            lw=0.8, zorder=3))
    _label(ax, x0 + w / 2, y0 - 0.14, title, size=10)


def three_ways_to_give_a_goal() -> None:
    """The same camera picture, plus a goal given as a picture, a task number or a sentence."""
    fig, ax = plt.subplots(figsize=(12.5, 5.2), facecolor='white')
    _axes(ax, (-0.2, 10.4), (-0.6, 4.1))
    # the camera picture now, on the left
    _scene(ax, (0.8, 0.25), 'camera picture now', 0.0, 1.45)
    _label(ax, 0.8, 3.0, 'What the policy sees', size=11, weight='bold')
    # three goal forms in the middle column
    _label(ax, 4.2, 3.95, 'plus one way of saying the goal', size=11, weight='bold')
    _scene(ax, (1.23, 0.78), 'a goal picture: how it should end', 3.4, 2.35)
    ax.add_patch(FancyBboxPatch((3.4, 1.15), 1.6, 0.5, boxstyle='round,pad=0.04',
                                facecolor='white', edgecolor=PURPLE, lw=1.6, zorder=2))
    _label(ax, 4.2, 1.4, '[0, 1, 0, 0]', size=12, color=PURPLE, weight='bold')
    _label(ax, 4.2, 0.92, 'a task number, as a one-hot list', size=10)
    ax.add_patch(FancyBboxPatch((2.8, -0.05), 2.8, 0.5, boxstyle='round,pad=0.04',
                                facecolor='white', edgecolor=GOOD, lw=1.6, zorder=2))
    _label(ax, 4.2, 0.2, '"put the mug in the blue bin"', size=10.5, color=GOOD)
    _label(ax, 4.2, -0.3, 'a sentence, turned into numbers', size=10)
    # the policy and its answer
    ax.add_patch(FancyBboxPatch((6.3, 1.2), 1.4, 1.1, boxstyle='round,pad=0.05',
                                facecolor=LINK_PALE, edgecolor=LINK, lw=1.6, zorder=2))
    _label(ax, 7.0, 1.75, 'policy', size=12, weight='bold')
    _arrow(ax, (1.65, 2.0), (6.25, 1.95), color=MUTED)
    for x, y in ((5.1, 2.9), (5.1, 1.4), (5.7, 0.2)):
        _arrow(ax, (x, y), (6.25, 1.75), color=MUTED, lw=1.2)
    _arrow(ax, (7.75, 1.75), (8.4, 1.75), color=INK)
    _scene(ax, (0.8, 0.25), 'next move: towards the blue bin', 8.5, 1.2)
    _arrow(ax, (8.5 + 0.88, 1.2 + 0.33), (8.5 + 1.12, 1.2 + 0.56), color=GOOD, lw=2.6, z=7)
    _save(fig, BC_DOC, 'three-ways-to-give-a-goal.svg')


def _goal_demos(rng: np.random.Generator, n: int = 40, steps: int = 20
                ) -> tuple[Arr, Arr, Arr]:
    """Demonstrations: from a start near the bottom to the red or the blue bin.

    Returns state (x, y), the one-hot goal, and the recorded move at each step.
    """
    states, goals, moves = [], [], []
    for k in range(n):
        name = 'red' if k % 2 == 0 else 'blue'
        g = BINS[name]
        onehot = np.array([1.0, 0.0]) if name == 'red' else np.array([0.0, 1.0])
        p = rng.normal([0.0, -0.05], 0.04)
        for _ in range(steps):
            move = 0.2 * (g - p) + rng.normal(0, 0.004, 2)
            states.append(p.copy())
            goals.append(onehot)
            moves.append(move)
            p = p + move
    return np.array(states), np.array(goals), np.array(moves)


def goal_stops_the_averaging() -> None:
    """Without the goal as input the fitted policy heads between the bins; with it, to the right one."""
    rng = np.random.default_rng(11)
    s, g, m = _goal_demos(rng)
    ones = np.ones((len(s), 1))
    feats_plain = np.hstack([s, ones])
    feats_goal = np.hstack([s, g])        # the one-hot also acts as a per-goal offset
    w_plain, *_ = np.linalg.lstsq(feats_plain, m, rcond=None)
    w_goal, *_ = np.linalg.lstsq(feats_goal, m, rcond=None)

    def roll(w: Arr, goal: Arr | None, steps: int = 25) -> Arr:
        p = np.array([0.0, -0.05])
        out = [p.copy()]
        for _ in range(steps):
            f = np.concatenate([p, [1.0]]) if goal is None else np.concatenate([p, goal])
            p = p + f @ w
            out.append(p.copy())
        return np.array(out)

    plain = roll(w_plain, None)
    to_red = roll(w_goal, np.array([1.0, 0.0]))
    to_blue = roll(w_goal, np.array([0.0, 1.0]))

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), facecolor='white')
    for ax in axes:
        _axes(ax, (-0.5, 0.5), (-0.16, 0.62))
        for name, c in BINS.items():
            col = BAD if name == 'red' else LINK
            ax.add_patch(Rectangle((c[0] - 0.07, c[1] - 0.07), 0.14, 0.14, facecolor='white',
                                   edgecolor=col, lw=2.4, zorder=2))
        # the demonstrations, faint
        for k in range(0, 40, 2):
            seg = s[k * 20:(k + 1) * 20]
            col = BAD if k % 2 == 0 else LINK
            ax.plot(seg[:, 0], seg[:, 1], color=col, alpha=0.18, lw=1)
        for k in range(1, 40, 2):
            seg = s[k * 20:(k + 1) * 20]
            ax.plot(seg[:, 0], seg[:, 1], color=LINK, alpha=0.18, lw=1)
        ax.plot([0], [-0.05], 'o', color=INK, ms=7, zorder=6)
        _label(ax, 0.0, -0.11, 'start', size=9.5)
    ax = axes[0]
    ax.plot(plain[:, 0], plain[:, 1], color=INK, lw=2.6, zorder=5)
    ax.plot(plain[-1, 0], plain[-1, 1], 'X', color=INK, ms=11, zorder=6)
    _title(ax, 'No goal given: it goes between the bins')
    ax = axes[1]
    ax.plot(to_red[:, 0], to_red[:, 1], color=BAD, lw=2.6, zorder=5)
    ax.plot(to_blue[:, 0], to_blue[:, 1], color=LINK, lw=2.6, zorder=5)
    _label(ax, -0.25, 0.575, 'goal = red', size=10, color=BAD, weight='bold')
    _label(ax, 0.25, 0.575, 'goal = blue', size=10, color=LINK, weight='bold')
    _title(ax, 'Goal given as input: it goes to that bin')
    print(f'  no goal ends at {np.round(plain[-1], 3)}; red {np.round(to_red[-1], 3)}; '
          f'blue {np.round(to_blue[-1], 3)}')
    _save(fig, BC_DOC, 'goal-stops-the-averaging.svg')


def hindsight_relabelling() -> None:
    """Play paths that missed their goal become successes for the place they did reach."""
    rng = np.random.default_rng(2)
    goal = np.array([0.30, 0.30])
    paths = []
    for _ in range(8):
        p = np.zeros(2)
        v = 0.03 * (goal / np.linalg.norm(goal)) + rng.normal(0, 0.008, 2)
        pts = [p.copy()]
        for _ in range(14):
            v = 0.8 * v + 0.2 * 0.03 * (goal / np.linalg.norm(goal)) + rng.normal(0, 0.008, 2)
            p = p + v
            pts.append(p.copy())
        paths.append(np.array(pts))
    reached = [np.linalg.norm(pth[-1] - goal) < 0.05 for pth in paths]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), facecolor='white')
    for ax in axes:
        _axes(ax, (-0.08, 0.62), (-0.08, 0.62))
        ax.plot([0], [0], 'o', color=INK, ms=7, zorder=6)
    ax = axes[0]
    ax.add_patch(Circle(tuple(goal), 0.05, facecolor=GOOD_PALE, edgecolor=GOOD, lw=1.4))
    ax.plot(*goal, '*', color=GOOD, ms=16, zorder=6)
    for pth, ok in zip(paths, reached):
        ax.plot(pth[:, 0], pth[:, 1], color=GOOD if ok else BAD, lw=1.8, alpha=0.9)
        ax.plot(*pth[-1], 'o', color=GOOD if ok else BAD, ms=5)
    _title(ax, f'As recorded: {sum(reached)} of 8 reached the star')
    ax = axes[1]
    for pth in paths:
        ax.plot(pth[:, 0], pth[:, 1], color=GOOD, lw=1.8, alpha=0.9)
        ax.plot(*pth[-1], '*', color=GOOD, ms=13, zorder=6)
    _title(ax, 'Relabelled: 8 of 8 reached their own star')
    for ax in axes:
        _label(ax, 0.0, -0.05, 'start', size=9.5)
    print(f'  hindsight: {sum(reached)} of 8 reached the original goal')
    _save(fig, BC_DOC, 'hindsight-relabelling.svg')


# --------------------------------------------------------------------------
# 01_learned-dynamics-models: residual models
# --------------------------------------------------------------------------

G: float = 9.81
MU_BOOK: float = 0.30                      # friction taken from a table of materials


def _slide_physics(v: Arr) -> Arr:
    """How far a block slides after it is let go at speed v (m): v² / (2 μ g)."""
    return v ** 2 / (2 * MU_BOOK * G)


def _slide_real(v: Arr) -> Arr:
    """The 'real' block: its friction is higher, and grows with speed."""
    mu = 0.33 + 0.08 * v
    return v ** 2 / (2 * mu * G)


def _bumps(v: Arr, lo: float, hi: float, n: int = 8) -> Arr:
    """A small learned model: n smooth bumps spread over the speeds seen in training."""
    centres = np.linspace(lo, hi, n)
    width = (hi - lo) / (n - 1)
    return np.exp(-0.5 * ((v[:, None] - centres[None, :]) / width) ** 2)


def _fit(v: Arr, target: Arr, lo: float, hi: float, lam: float = 1e-2):
    """Fit the bumps by least squares with a small penalty on large weights."""
    a = _bumps(v, lo, hi)
    w = np.linalg.solve(a.T @ a + lam * np.eye(a.shape[1]), a.T @ target)
    return lambda x: _bumps(x, lo, hi) @ w


def _pushes(rng: np.random.Generator, n: int, lo: float, hi: float,
            spread: bool = False) -> tuple[Arr, Arr]:
    if spread:                      # one push in each of n equal speed bands
        v = lo + (hi - lo) * (np.arange(n) + rng.uniform(0, 1, n)) / n
    else:
        v = rng.uniform(lo, hi, n)
    d = _slide_real(v) + rng.normal(0, 0.002, n)          # 2 mm measuring noise
    return v, d


def physics_plus_correction() -> None:
    """Measured slides, the textbook formula, and the formula plus a fitted correction."""
    rng = np.random.default_rng(2)
    lo, hi = 0.1, 0.8
    v, d = _pushes(rng, 12, lo, hi, spread=True)
    corr = _fit(v, d - _slide_physics(v), lo, hi)
    vv = np.linspace(lo, hi, 200)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    ax = axes[0]
    _plot_axes(ax)
    ax.plot(vv, _slide_physics(vv) * 100, color=MUTED, lw=2, ls='--',
            label='textbook formula, μ = 0.30')
    ax.plot(vv, (_slide_physics(vv) + corr(vv)) * 100, color=GOOD, lw=2.4,
            label='formula + learned correction')
    ax.scatter(v, d * 100, color=INK, s=26, zorder=5, label='12 measured pushes')
    ax.set_xlabel('speed when the gripper lets go (m/s)', fontsize=10)
    ax.set_ylabel('distance the block slides (cm)', fontsize=10)
    ax.legend(loc='upper left', fontsize=9.5, frameon=False)
    _title(ax, 'The formula, and the formula plus a correction')
    ax = axes[1]
    _plot_axes(ax)
    ax.axhline(0, color=MUTED, lw=1)
    ax.scatter(v, (d - _slide_physics(v)) * 100, color=INK, s=26, zorder=5,
               label='measured minus formula')
    ax.plot(vv, corr(vv) * 100, color=GOOD, lw=2.4, label='learned correction')
    ax.set_xlabel('speed when the gripper lets go (m/s)', fontsize=10)
    ax.set_ylabel('what the formula gets wrong (cm)', fontsize=10)
    ax.legend(loc='lower left', fontsize=9.5, frameon=False)
    _title(ax, 'What the network has to learn')
    fig.tight_layout(w_pad=3)
    for s in (0.3, 0.5, 0.7):
        x = np.array([s])
        print(f'  v={s}: formula {_slide_physics(x)[0] * 100:.2f} cm, real '
              f'{_slide_real(x)[0] * 100:.2f} cm, formula+corr '
              f'{(_slide_physics(x) + corr(x))[0] * 100:.2f} cm')
    _save(fig, DYN_DOC, 'physics-plus-correction.svg')


def residual_needs_less_data() -> None:
    """Average error against the number of training pushes, for a whole-learned and a residual model."""
    lo, hi = 0.1, 0.8
    counts = [3, 5, 8, 12, 20, 35, 60, 100]
    test_v = np.linspace(lo, hi, 300)
    truth = _slide_real(test_v)
    err_whole, err_resid = [], []
    for n in counts:
        ew, er = [], []
        for seed in range(200):
            rng = np.random.default_rng(1000 + seed)
            v, d = _pushes(rng, n, lo, hi)
            whole = _fit(v, d, lo, hi)
            resid = _fit(v, d - _slide_physics(v), lo, hi)
            ew.append(np.sqrt(np.mean((whole(test_v) - truth) ** 2)))
            er.append(np.sqrt(np.mean((_slide_physics(test_v) + resid(test_v) - truth) ** 2)))
        err_whole.append(np.median(ew))
        err_resid.append(np.median(er))
    formula_err = np.sqrt(np.mean((_slide_physics(test_v) - truth) ** 2))
    fig, ax = plt.subplots(figsize=(8.0, 4.8), facecolor='white')
    _plot_axes(ax)
    ax.plot(counts, np.array(err_whole) * 100, 'o-', color=BAD, lw=2.2,
            label='network learns the whole slide')
    ax.plot(counts, np.array(err_resid) * 100, 'o-', color=GOOD, lw=2.2,
            label='formula + network learns the correction')
    ax.axhline(formula_err * 100, color=MUTED, ls='--', lw=1.5,
               label='formula alone, no learning')
    ax.set_xscale('log')
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('number of recorded pushes used for training', fontsize=10)
    ax.set_ylabel('typical error in the slide (cm)', fontsize=10)
    ax.set_ylim(0, None)
    ax.legend(loc='center right', bbox_to_anchor=(1.0, 0.58), fontsize=9.5, frameon=False)
    _title(ax, 'The same small model, trained two ways')
    print('  pushes:', counts)
    print('  whole  (cm):', [f'{e * 100:.2f}' for e in err_whole])
    print('  resid  (cm):', [f'{e * 100:.2f}' for e in err_resid])
    print(f'  formula alone: {formula_err * 100:.2f} cm')
    _save(fig, DYN_DOC, 'residual-needs-less-data.svg')


def residual_outside_the_data() -> None:
    """Trained on gentle pushes only; asked about harder ones."""
    rng = np.random.default_rng(4)
    lo, hi = 0.1, 0.45
    v, d = _pushes(rng, 20, lo, hi)
    whole = _fit(v, d, lo, hi)
    resid = _fit(v, d - _slide_physics(v), lo, hi)
    vv = np.linspace(0.1, 0.9, 300)
    fig, ax = plt.subplots(figsize=(8.5, 4.8), facecolor='white')
    _plot_axes(ax)
    ax.axvspan(lo, hi, color=GOOD_PALE, zorder=0)
    ax.text((lo + hi) / 2, 14.2, 'speeds seen\nin training', ha='center', va='top',
            fontsize=9.5, color=GOOD)
    ax.plot(vv, _slide_real(vv) * 100, color=INK, lw=1.5, ls=':', label='the real block')
    ax.plot(vv, whole(vv) * 100, color=BAD, lw=2.4, label='network learns the whole slide')
    ax.plot(vv, (_slide_physics(vv) + resid(vv)) * 100, color=GOOD, lw=2.4,
            label='formula + learned correction')
    ax.scatter(v, d * 100, color=INK, s=18, zorder=5)
    ax.set_xlabel('speed when the gripper lets go (m/s)', fontsize=10)
    ax.set_ylabel('distance the block slides (cm)', fontsize=10)
    ax.set_xlim(0.1, 0.9)
    ax.set_ylim(-1, 14.5)
    ax.legend(loc='upper left', bbox_to_anchor=(0.34, 1.0), fontsize=9.5, frameon=False)
    _title(ax, 'Asked about pushes harder than any it has seen')
    for s in (0.4, 0.6, 0.8):
        x = np.array([s])
        print(f'  v={s}: real {_slide_real(x)[0] * 100:.2f}, whole {whole(x)[0] * 100:.2f}, '
              f'residual {(_slide_physics(x) + resid(x))[0] * 100:.2f}, formula '
              f'{_slide_physics(x)[0] * 100:.2f} cm')
    _save(fig, DYN_DOC, 'residual-outside-the-data.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    print('actions and observations')
    joints_or_gripper_pose()
    absolute_or_relative()
    rotation_number_jumps()
    normalising_each_number()
    worked_step_numbers()
    print('behaviour cloning: goals')
    three_ways_to_give_a_goal()
    goal_stops_the_averaging()
    hindsight_relabelling()
    print('learned dynamics: residual models')
    physics_plus_correction()
    residual_needs_less_data()
    residual_outside_the_data()


if __name__ == '__main__':
    main()
