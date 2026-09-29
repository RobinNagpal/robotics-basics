"""Generate the diagrams used in docs/01_robotics-intro/03_arm/02_frames-in-3d.md.

The pictures go to docs/images/arm/frames-in-3d/.

Run with:  pixi run python ../docs/diagrams/frames_3d.py

Add --png DIR to also write a PNG copy of every picture into DIR, for checking.

The turns come from code/src/frames_3d/orientation.py and the cup's numbers from
code/src/frames_3d/cell_chain.py, so every position in a picture is the same
number the document quotes.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d import proj3d  # noqa: E402
from mpl_toolkits.mplot3d.axes3d import Axes3D  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'code' / 'src' / 'frames_3d'))
# Imported after the sys.path line above, which flake8's import rules cannot see.
from cell_chain import (  # noqa: E402,I100,I202
    ABOVE_CUP_M, CAMERA_RPY, CAMERA_XYZ, CUP_IN_CAMERA, flip, point, POINT_DOWN_RPY,
    TCP_OFFSET_M, transform)
from orientation import rpy  # noqa: E402

OUT_DIR: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images' / 'arm'
                         / 'frames-in-3d')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#3b6fd1'
LINK: str = '#3b82c4'
JOINT: str = '#f0a500'
GRIP: str = '#e05555'
GHOST: str = '#c8c8c8'
CUP: str = '#8e5bd0'
INK: str = '#222222'
MUTED: str = '#777777'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f'{name}.svg', bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        PNG_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(PNG_DIR / f'{name}.png', bbox_inches='tight', pad_inches=0.3,
                    facecolor='white', dpi=110)
    plt.close(fig)


def _ax3d(fig: Figure, pos: tuple[int, int, int], box: tuple[float, float, float, float],
          elev: float = 22, azim: float = -60, zoom: float = 1.0) -> Axes3D:
    """Make a 3D panel. box is (x min, x max, y min, z min); every side is equally long."""
    ax: Axes3D = fig.add_subplot(*pos, projection='3d')   # type: ignore[assignment]
    ax.set_facecolor('white')
    side: float = box[1] - box[0]
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[2] + side)
    ax.set_zlim(box[3], box[3] + side)
    ax.set_box_aspect((1, 1, 1), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    return ax


def _label3d(ax: Axes3D, p: NDArray[np.float64] | tuple[float, float, float], text: str,
             dx: float, dy: float, ha: str = 'left', color: str = INK, size: float = 9.5,
             weight: str = 'normal') -> None:
    """Put a label a fixed number of points away from a 3D point, on the page."""
    x2, y2, _ = proj3d.proj_transform(p[0], p[1], p[2], ax.get_proj())
    ax.annotate(text, xy=(x2, y2), xytext=(dx, dy), textcoords='offset points', ha=ha,
                va='center', fontsize=size, color=color, weight=weight)


def _arrow3d(ax: Axes3D, start: NDArray[np.float64], vec: NDArray[np.float64],
             color: str, lw: float = 2.2) -> None:
    ax.quiver(*start, *vec, color=color, lw=lw, arrow_length_ratio=0.18)


def _triad(ax: Axes3D, t: NDArray[np.float64], length: float, lw: float = 2.0) -> None:
    """Draw a frame's x, y and z axes in red, green and blue."""
    for i, c in enumerate((AXIS_X, AXIS_Y, AXIS_Z)):
        _arrow3d(ax, t[:3, 3], t[:3, i] * length, c, lw)


def _floor3d(ax: Axes3D, x0: float, x1: float, y0: float, y1: float, step: float) -> None:
    for v in np.arange(x0, x1 + 1e-9, step):
        ax.plot([v, v], [y0, y1], [0, 0], color=GRID, lw=0.6)
    for v in np.arange(y0, y1 + 1e-9, step):
        ax.plot([x0, x1], [v, v], [0, 0], color=GRID, lw=0.6)


def _gripper_lines(r: NDArray[np.float64]) -> list[NDArray[np.float64]]:
    """Return the outline of a gripper pointing along its x axis, turned by r, as lines."""
    pieces: list[list[tuple[float, float, float]]] = [
        [(-0.45, 0.0, 0.0), (0.0, 0.0, 0.0)],                                 # wrist
        [(0.0, -0.3, 0.0), (0.0, 0.3, 0.0)],                                  # palm
        [(0.0, -0.3, 0.0), (0.6, -0.3, 0.0)],                                 # finger
        [(0.0, 0.3, 0.0), (0.6, 0.3, 0.0)],                                   # finger
    ]
    return [(r @ np.array(p).T).T for p in pieces]


def _draw_gripper(ax: Axes3D, r: NDArray[np.float64], color: str, lw: float) -> None:
    for seg in _gripper_lines(r):
        ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color, lw=lw, solid_capstyle='round')


# --------------------------------------------------------------------------
# section 2: the axes
# --------------------------------------------------------------------------

def axes() -> None:
    """Draw x forward, y left, z up, and which way a positive turn about z goes."""
    fig = plt.figure(figsize=(6.4, 5.6), facecolor='white')
    ax = _ax3d(fig, (1, 1, 1), box=(-0.6, 1.2, -0.6, -0.5), elev=24, azim=-130, zoom=1.35)
    _floor3d(ax, -0.4, 1.0, -0.4, 1.0, 0.2)
    origin: NDArray[np.float64] = np.zeros(3)
    _arrow3d(ax, origin, np.array([1.0, 0.0, 0.0]), AXIS_X, 3.0)
    _arrow3d(ax, origin, np.array([0.0, 1.0, 0.0]), AXIS_Y, 3.0)
    _arrow3d(ax, origin, np.array([0.0, 0.0, 1.0]), AXIS_Z, 3.0)
    _label3d(ax, (1.05, 0.0, 0.0), 'x  forward', 4, -12, color=AXIS_X, weight='bold')
    _label3d(ax, (0.0, 1.05, 0.0), 'y  left', -6, -10, ha='right', color=AXIS_Y, weight='bold')
    _label3d(ax, (0.0, 0.0, 1.05), 'z  up', 8, 4, color=AXIS_Z, weight='bold')

    # A positive turn about z: x swings towards y, counter-clockwise seen from above.
    t = np.linspace(math.radians(15), math.radians(75), 40)
    rad: float = 0.55
    ax.plot(rad * np.cos(t), rad * np.sin(t), np.full_like(t, 0.35), color=INK, lw=1.6)
    tip = np.array([rad * math.cos(t[-1]), rad * math.sin(t[-1]), 0.35])
    back = np.array([rad * math.cos(t[-4]), rad * math.sin(t[-4]), 0.35])
    ax.quiver(*back, *(tip - back), color=INK, lw=1.6, arrow_length_ratio=1.2)
    _label3d(ax, (rad * math.cos(t[20]), rad * math.sin(t[20]), 0.35),
             'positive turn about z:\nx swings towards y', 14, 18, size=9)
    fig.text(0.5, 0.06, 'Right hand: thumb along z, and the fingers curl from x towards y.\n'
             'Every viewer draws x red, y green and z blue.',
             ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'axes')


# --------------------------------------------------------------------------
# section 3: roll, pitch and yaw
# --------------------------------------------------------------------------

def roll_pitch_yaw() -> None:
    """Draw the same gripper, turned by roll, by pitch and by yaw on its own."""
    fig = plt.figure(figsize=(12.0, 3.6), facecolor='white')
    panels: list[tuple[str, tuple[float, float, float]]] = [
        ('no turn', (0.0, 0.0, 0.0)),
        ('roll 90°: spins about x', (90.0, 0.0, 0.0)),
        ('pitch 45°: tips down, about y', (0.0, 45.0, 0.0)),
        ('yaw 90°: turns left, about z', (0.0, 0.0, 90.0)),
    ]
    for i, (title, angles) in enumerate(panels):
        ax = _ax3d(fig, (1, 4, i + 1), box=(-0.6, 0.9, -0.75, -0.8), elev=20, azim=-60,
                   zoom=1.7)
        _floor3d(ax, -0.6, 0.8, -0.6, 0.8, 0.2)
        if i > 0:
            _draw_gripper(ax, np.eye(3), GHOST, 2.0)
        r: NDArray[np.float64] = rpy(*angles).as_matrix()
        _draw_gripper(ax, r, INK, 3.0)
        # The gripper's own axes: x where it points (red), z its up (blue).
        _arrow3d(ax, np.zeros(3), r[:, 0] * 0.85, AXIS_X, 2.2)
        _arrow3d(ax, np.zeros(3), r[:, 2] * 0.6, AXIS_Z, 2.2)
        ax.set_title(title, fontsize=10.5, color=INK, pad=-4)
    fig.text(0.5, 0.04, 'red: where the gripper points (its x)    blue: its up (its z)    '
             'grey: before the turn', ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'roll-pitch-yaw')


# --------------------------------------------------------------------------
# section 4: gimbal lock
# --------------------------------------------------------------------------

def gimbal_lock() -> None:
    """Tip the gripper past straight down: the angles jump, the quaternion does not."""
    tilts = np.linspace(80.0, 100.0, 201)
    readback = np.array([rpy(10, p, 0).as_euler('xyz', degrees=True) for p in tilts
                         if abs(p - 90.0) > 1e-9])
    quats = np.array([rpy(10, p, 0).as_quat() for p in tilts])
    kept = np.array([p for p in tilts if abs(p - 90.0) > 1e-9])

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(7.2, 6.4), facecolor='white', sharex=True)
    ax: Axes
    for ax in (top, bottom):
        ax.axvline(90.0, color=MUTED, lw=1.0, ls='--')
        ax.grid(color=GRID, lw=0.6)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)

    below = kept < 90.0
    above = kept > 90.0
    # Past the lock the yaw reads +180 or -180, which are the same direction.
    # Draw both as -180 so the line does not flick between them.
    readback[above, 2] = np.where(readback[above, 2] > 0, readback[above, 2] - 360.0,
                                  readback[above, 2])
    readback[above, 0] = np.where(readback[above, 0] > 0, readback[above, 0] - 360.0,
                                  readback[above, 0])
    for mask in (below, above):
        top.plot(kept[mask], readback[mask, 0], color=AXIS_X, lw=2.2)
        top.plot(kept[mask], readback[mask, 2], color=AXIS_Z, lw=2.2)
    top.set_ylabel('degrees, read back', fontsize=10)
    top.set_ylim(-200, 60)
    top.text(83.5, 22, 'roll 10', color=AXIS_X, fontsize=10)
    top.text(83.5, -22, 'yaw 0', color=AXIS_Z, fontsize=10)
    top.text(94.0, -158, 'roll −170', color=AXIS_X, fontsize=10)
    top.text(94.0, -196, 'yaw ±180', color=AXIS_Z, fontsize=10)
    top.set_title('Read back as roll and yaw, the same smooth tilt jumps at 90°', fontsize=11,
                  color=INK)
    top.text(89.6, -80, 'pointing\nstraight down', color=MUTED, fontsize=9, ha='right')

    colors = (AXIS_X, AXIS_Y, AXIS_Z, INK)
    for j in range(4):
        bottom.plot(tilts, quats[:, j], color=colors[j], lw=2.2)
    bottom.text(80.4, quats[0, 0] + 0.05, 'x', color=AXIS_X, fontsize=10)
    bottom.text(80.4, quats[0, 1] - 0.09, 'y', color=AXIS_Y, fontsize=10)
    bottom.text(80.4, quats[0, 2] - 0.09, 'z', color=AXIS_Z, fontsize=10)
    bottom.text(80.4, quats[0, 3] + 0.04, 'w', color=INK, fontsize=10)
    bottom.set_ylim(-0.3, 0.95)
    bottom.set_ylabel('quaternion parts', fontsize=10)
    bottom.set_xlabel('how far the gripper is tipped down (degrees of pitch), with roll 10',
                      fontsize=10)
    bottom.set_title('The quaternion changes smoothly through the same tilt', fontsize=11,
                     color=INK)
    fig.tight_layout()
    _save(fig, 'gimbal-lock')


# --------------------------------------------------------------------------
# section 5: the frames of a cell
# --------------------------------------------------------------------------

def _cell_numbers() -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
                             NDArray[np.float64]]:
    """base_link -> camera, the cup in base_link, and the tcp and tool0 targets."""
    base_camera = transform(CAMERA_XYZ, CAMERA_RPY)
    cup_base = point(base_camera, np.array(CUP_IN_CAMERA))
    tcp_xyz = (float(cup_base[0]), float(cup_base[1]), float(cup_base[2]) + ABOVE_CUP_M)
    base_tcp = transform(tcp_xyz, POINT_DOWN_RPY)
    base_tool0 = base_tcp @ flip(transform((TCP_OFFSET_M, 0.0, 0.0), (0.0, 0.0, 0.0)))
    return base_camera, cup_base, base_tcp, base_tool0


def cell_frames() -> None:
    """Draw the named frames of an arm cell, and mark which ones move."""
    base_camera, cup_base, base_tcp, base_tool0 = _cell_numbers()

    fig = plt.figure(figsize=(8.4, 6.4), facecolor='white')
    ax = _ax3d(fig, (1, 1, 1), box=(-0.3, 1.35, -0.8, -0.45), elev=18, azim=-72, zoom=1.35)
    _floor3d(ax, -0.2, 1.3, -0.5, 0.4, 0.1)

    # The arm, as a stick figure from the base up to the flange.
    shoulder = np.array([0.0, 0.0, 0.25])
    elbow = np.array([0.2, -0.05, 0.62])
    flange = base_tool0[:3, 3]
    arm = np.array([np.zeros(3), shoulder, elbow, flange])
    ax.plot(arm[:, 0], arm[:, 1], arm[:, 2], color=LINK, lw=6, solid_capstyle='round')
    for p in arm[1:3]:
        ax.scatter(*p, color=JOINT, s=60, edgecolors=INK, linewidths=0.6, depthshade=False)
    tcp = base_tcp[:3, 3]
    ax.plot([flange[0], tcp[0]], [flange[1], tcp[1]], [flange[2], tcp[2]], color=GRIP, lw=4)

    # The camera on its stand. Its line of sight is drawn in the next picture.
    cam = base_camera[:3, 3]
    ax.plot([cam[0], cam[0]], [cam[1], cam[1]], [0, cam[2]], color=MUTED, lw=3)

    # The cup: an upright bar, with its middle at the measured point.
    ax.plot([cup_base[0]] * 2, [cup_base[1]] * 2, [0.0, 2 * cup_base[2]], color=CUP, lw=10,
            alpha=0.5, solid_capstyle='butt')

    world = np.eye(4)
    world[:3, 3] = [-0.15, 0.3, 0.0]
    cup_frame = np.eye(4)
    cup_frame[:3, 3] = cup_base
    for t, length in ((world, 0.15), (np.eye(4), 0.15), (base_tool0, 0.1), (base_tcp, 0.1),
                      (base_camera, 0.12), (cup_frame, 0.1)):
        _triad(ax, t, length)

    _label3d(ax, world[:3, 3], 'world\n(static)', -10, 6, ha='right', color=MUTED)
    _label3d(ax, (0.0, 0.0, 0.0), 'base_link\n(static)', -12, -16, ha='right', color=MUTED)
    _label3d(ax, flange, 'tool0, the flange\n(moves with the joints)', 36, -8,
             color=JOINT, weight='bold')
    _label3d(ax, tcp, 'tcp, the fingertips\n(static on tool0)', 36, -10,
             color=GRIP)
    _label3d(ax, cam, 'camera\n(static, on a stand)', 10, 26, color=MUTED)
    _label3d(ax, (cup_base[0], cup_base[1], 0.0), 'cup\n(new in every picture)', 16, -26,
             color=CUP, weight='bold')
    fig.text(0.5, 0.1, 'grey label: fixed once the cell is built    '
             'bold label: changes while the arm works', ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'cell-frames')


# --------------------------------------------------------------------------
# section 6: the cup, from the camera to the gripper
# --------------------------------------------------------------------------

def _arrow2d(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str,
             lw: float = 2.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=13, color=color,
                                 lw=lw, shrinkA=0, shrinkB=0))


def cup_chain() -> None:
    """Draw a side view of the worked chain, with the numbers from cell_chain.py."""
    base_camera, cup_base, base_tcp, base_tool0 = _cell_numbers()
    cam = base_camera[:3, 3]
    cx, cz = float(cup_base[0]), float(cup_base[2])
    tcp_z = float(base_tcp[2, 3])
    flange_z = float(base_tool0[2, 3])

    fig, ax = plt.subplots(figsize=(8.6, 5.6), facecolor='white')
    ax.set_aspect('equal')
    ax.set_xlim(-0.3, 1.65)
    ax.set_ylim(-0.1, 0.98)
    ax.axis('off')
    ax.plot([-0.3, 1.65], [0, 0], color=INK, lw=1.2)

    # base_link, on the table: x forward (red), z up (blue)
    _arrow2d(ax, (0.0, 0.0), (0.14, 0.0), AXIS_X)
    _arrow2d(ax, (0.0, 0.0), (0.0, 0.14), AXIS_Z)
    ax.text(0.0, -0.05, 'base_link (0, 0, 0)', ha='center', fontsize=9.5, color=INK)

    # the camera, its stand, which way it looks, and its line of sight
    ax.plot([cam[0], cam[0]], [0, cam[2]], color=MUTED, lw=3)
    view = base_camera[:3, 0]
    ax.plot([cam[0], cx], [cam[2], cz], color=MUTED, lw=1.2, ls='--')
    _arrow2d(ax, (cam[0], cam[2]), (cam[0] + 0.14 * view[0], cam[2] + 0.14 * view[2]), AXIS_X)
    ax.scatter([cam[0]], [cam[2]], s=90, color=INK, marker='s', zorder=5)
    ax.text(cam[0], cam[2] + 0.05, f'camera at ({cam[0]:.1f}, {cam[1]:.1f}, {cam[2]:.1f})\n'
            'turned round, looking 45° down', ha='center', fontsize=9.5, color=INK)
    ax.text(cam[0] + 0.05, 0.3, f"{CUP_IN_CAMERA[0]:.3f} m along\nthe camera's x",
            ha='left', va='center', fontsize=9.5, color=MUTED)
    ax.text(cam[0] + 0.05, 0.15, f'cup in camera =\n({CUP_IN_CAMERA[0]:.3f}, '
            f'{CUP_IN_CAMERA[1]:.3f}, {CUP_IN_CAMERA[2]:.3f})', ha='left', va='center',
            fontsize=9.5, color=MUTED)

    # the cup
    ax.add_patch(Rectangle((cx - 0.04, 0.0), 0.08, 2 * cz, color=CUP, alpha=0.35, lw=0))
    ax.scatter([cx], [cz], s=40, color=CUP, zorder=5)
    ax.text(cx - 0.07, cz, 'cup in base_link =\n'
            f'({cup_base[0]:.3f}, {cup_base[1]:.3f}, {cup_base[2]:.3f})',
            ha='right', va='center', fontsize=9.5, color=CUP, weight='bold')

    # the gripper, pointing down: fingertips 0.1 m over the cup's middle, flange above
    ax.plot([cx, cx], [tcp_z + 0.05, flange_z], color=GRIP, lw=4)
    ax.plot([cx - 0.035, cx + 0.035], [tcp_z + 0.05, tcp_z + 0.05], color=GRIP, lw=3)
    for dx in (-0.035, 0.035):
        ax.plot([cx + dx, cx + dx], [tcp_z, tcp_z + 0.05], color=GRIP, lw=3)
    ax.plot([cx, cx - 0.12], [flange_z, flange_z + 0.2], color=LINK, lw=6,
            solid_capstyle='round')
    ax.scatter([cx], [flange_z], s=50, color=JOINT, edgecolors=INK, zorder=5)
    ax.scatter([cx], [tcp_z], s=30, color=GRIP, zorder=5)
    ax.text(cx - 0.07, flange_z, 'tool0 target\n'
            f'({base_tool0[0, 3]:.3f}, {base_tool0[1, 3]:.3f}, {flange_z:.3f})',
            ha='right', va='center', fontsize=9.5, color=INK)
    ax.text(cx - 0.07, tcp_z + 0.01, 'tcp target\n'
            f'({base_tcp[0, 3]:.3f}, {base_tcp[1, 3]:.3f}, {tcp_z:.3f})',
            ha='right', va='center', fontsize=9.5, color=GRIP)
    ax.text(0.675, 0.94, "Seen from the arm's right side: x to the right, z up. y is not drawn.",
            ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'cup-chain')


def main() -> None:
    """Draw every picture for the frames in 3D doc."""
    axes()
    roll_pitch_yaw()
    gimbal_lock()
    cell_frames()
    cup_chain()
    print(f'wrote 5 SVGs to {OUT_DIR}')


if __name__ == '__main__':
    if '--png' in sys.argv:
        PNG_DIR = pathlib.Path(sys.argv[sys.argv.index('--png') + 1])
    main()
