"""Generate the diagrams for docs/06_programming-techniques/02_geometry-and-cameras/.

This covers 01_overview, 02_pinhole-camera-model, 03_rigid-transforms and
04_calibration. Each document's pictures go to a folder named after it, under
docs/images/geometry-and-cameras/.

Run with:  pixi run python ../docs/diagrams/geometry_and_cameras.py
Add --png <dir> to also write PNG copies for checking.

Every number drawn on a picture is computed here, with the same camera as Book 2:
320 x 240 pixels, fx = fy = 277.1, cx = 160, cy = 120, hanging 0.40 m above the
middle of the table and looking straight down. The projections, the rays, the
transforms and the blends are worked out with NumPy when the picture is drawn,
so the pictures and the numbers in the documents come from the same arithmetic.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'geometry-and-cameras'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'

WALL: str = '#f3f3f3'
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'

# The camera every page shares, from Book 2.
FX: float = 277.1
CX: float = 160.0
CY: float = 120.0
W_PX: int = 320
H_PX: int = 240
CAM_HEIGHT: float = 0.40

# The spot on top of the red box that Book 2 measures.
SPOT_UV: tuple[float, float] = (212.5, 86.5)
SPOT_DEPTH: float = 0.340


# --------------------------------------------------------------------------
# the arithmetic the pictures show
# --------------------------------------------------------------------------

def project(p: np.ndarray, fx: float = FX, cx: float = CX, cy: float = CY) -> np.ndarray:
    """A point in the camera's frame (x right, y down, z ahead) to a pixel."""
    return np.array([fx * p[0] / p[2] + cx, fx * p[1] / p[2] + cy])


def deproject(u: float, v: float, depth: float) -> np.ndarray:
    """A pixel and its depth reading back to a point in the camera's frame."""
    return np.array([(u - CX) * depth / FX, (v - CY) * depth / FX, depth])


def transform(r: np.ndarray, t: np.ndarray) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = r
    m[:3, 3] = t
    return m


def invert(m: np.ndarray) -> np.ndarray:
    r = m[:3, :3]
    t = m[:3, 3]
    return transform(r.T, -r.T @ t)


def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def apply(m: np.ndarray, p: np.ndarray) -> np.ndarray:
    return (m @ np.append(p, 1.0))[:3]


# The fixed camera above the table, as Book 2's camera_to_world.
T_WORLD_CAMERA: np.ndarray = transform(np.diag([1.0, -1.0, -1.0]), np.array([0.0, 0.0, CAM_HEIGHT]))
# The arm's base, 0.35 m to the left of the table's middle and 0.10 m back, turned 30 degrees.
T_WORLD_BASE: np.ndarray = transform(rot_z(math.radians(30)), np.array([-0.35, 0.10, 0.0]))


# --------------------------------------------------------------------------
# small drawing helpers
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
           ha: str = 'center', weight: str = 'normal', va: str = 'center') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9)


def _boxed(ax: Axes, x: float, y: float, text: str, size: float = 9.5, color: str = INK,
           ha: str = 'center', edge: str = GRID) -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, zorder=10,
            bbox={'boxstyle': 'round,pad=0.35', 'facecolor': 'white', 'edgecolor': edge})


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>', z: int = 8) -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': style, 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=z)


def _curved(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str,
            rad: float = 0.3, lw: float = 2.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, connectionstyle=f'arc3,rad={rad}', arrowstyle='-|>',
                                 mutation_scale=14, color=color, lw=lw, zorder=7))


def _frame(ax: Axes, origin: tuple[float, float], x_dir: tuple[float, float],
           y_dir: tuple[float, float], length: float, name: str, name_at: tuple[float, float],
           x_label: str = 'x', y_label: str = 'y', size: float = 9) -> None:
    """Two axis arrows, x red and y green, as RViz draws a frame."""
    ox, oy = origin
    for d, col, lab in ((x_dir, GRIP, x_label), (y_dir, SLIDE, y_label)):
        if d is None:
            continue
        tip = (ox + d[0] * length, oy + d[1] * length)
        _arrow(ax, origin, tip, color=col, lw=2.0, z=9)
        _label(ax, ox + d[0] * length * 1.28, oy + d[1] * length * 1.28, lab, size=size,
               color=col, weight='bold')
    ax.plot([ox], [oy], 'o', color=INK, ms=4, zorder=10)
    _label(ax, name_at[0], name_at[1], name, size=size, color=INK)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white',
                metadata={'Date': None})
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _table_and_box(ax: Axes, x0: float, x1: float, box: tuple[float, float, float]) -> None:
    """A side view: the table top at height 0 and a box (left, right, height) on it."""
    ax.add_patch(Rectangle((x0, -0.03), x1 - x0, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
    ax.plot([x0, x1], [0, 0], color='#b9a888', lw=1.5, zorder=2)
    left, right, height = box
    ax.add_patch(Rectangle((left, 0), right - left, height, facecolor=GRIP, edgecolor='#a83232',
                           lw=1.2, alpha=0.85, zorder=3))


def _camera_body(ax: Axes, x: float, z: float, angle_deg: float = -90.0, size: float = 0.035,
                 color: str = INK) -> None:
    """A small camera seen from the side: a box with the lens pointing along angle_deg."""
    a = math.radians(angle_deg)
    f = np.array([math.cos(a), math.sin(a)])
    s = np.array([-f[1], f[0]])
    c = np.array([x, z])
    back = c - f * size
    corners = [back + s * size * 0.7, back - s * size * 0.7, c - s * size * 0.7, c + s * size * 0.7]
    ax.add_patch(Polygon(corners, closed=True, facecolor='#444444', edgecolor=color, zorder=6))
    lens = [c + s * size * 0.35, c - s * size * 0.35, c - s * size * 0.2 + f * size * 0.35,
            c + s * size * 0.2 + f * size * 0.35]
    ax.add_patch(Polygon(lens, closed=True, facecolor='#666666', edgecolor=color, zorder=6))


# ==========================================================================
# 01_overview
# ==========================================================================

def overview_pixel_to_gripper() -> None:
    """The whole chain on one scene: pixel and depth, camera frame, base frame."""
    fig, ax = plt.subplots(figsize=(10.5, 6.0), facecolor='white')
    _axes(ax, (-0.62, 0.42), (-0.11, 0.56))

    spot_c = deproject(*SPOT_UV, SPOT_DEPTH)
    spot_w = apply(T_WORLD_CAMERA, spot_c)
    spot_b = apply(invert(T_WORLD_BASE), spot_w)

    # side view along the world y axis: horizontal is world x, vertical is world z
    _table_and_box(ax, -0.60, 0.40, (0.035, 0.095, 0.060))
    cam = (0.0, CAM_HEIGHT)
    # the field of view, 60 degrees across
    half = math.atan(CX / FX)
    for sgn in (-1, 1):
        ax.plot([0, sgn * CAM_HEIGHT * math.tan(half)], [CAM_HEIGHT, 0], color=GRID, lw=1.0,
                ls='--', zorder=2)
    _camera_body(ax, cam[0], cam[1] + 0.015, -90)
    # the ray through the pixel to the spot
    ax.plot([0, spot_w[0]], [CAM_HEIGHT, spot_w[2]], color=JOINT, lw=2.4, zorder=5)
    ax.plot([spot_w[0]], [spot_w[2]], 'o', color=JOINT, mec=INK, ms=9, zorder=8)

    # the arm, standing on its base at the left
    base_x = T_WORLD_BASE[0, 3]
    ax.add_patch(Rectangle((base_x - 0.05, 0), 0.10, 0.04, facecolor='#999999', edgecolor=INK,
                           zorder=4))
    shoulder = np.array([base_x, 0.12])
    ax.plot([base_x, base_x], [0.04, 0.12], color=LINK, lw=7, solid_capstyle='round', zorder=4)
    elbow = np.array([base_x + 0.13, 0.33])
    wrist = np.array([spot_w[0] - 0.12, spot_w[2] + 0.17])
    ax.plot(*zip(shoulder, elbow, wrist), color=LINK, lw=7, solid_capstyle='round', zorder=4)
    for j in (shoulder, elbow, wrist):
        ax.plot(*j, 'o', color=JOINT, mec=INK, ms=9, zorder=5)
    grip_tip = wrist + np.array([0.06, -0.06])
    ax.plot(*zip(wrist, grip_tip), color=GRIP, lw=4, zorder=4)
    _arrow(ax, (grip_tip[0] + 0.01, grip_tip[1] - 0.01), (spot_w[0] - 0.012, spot_w[2] + 0.012),
           color=MUTED, lw=1.2)

    # frames
    _frame(ax, (0.0, CAM_HEIGHT + 0.035), (1, 0), None, 0.06, 'camera', (-0.07, CAM_HEIGHT + 0.045))
    ax.plot([0.0, 0.0], [CAM_HEIGHT + 0.035, CAM_HEIGHT + 0.035], color=INK)
    _frame(ax, (base_x, 0.0), (1, 0), None, 0.07, 'arm base', (base_x - 0.09, -0.045))

    # the three steps, as numbered notes
    _boxed(ax, 0.23, 0.49,
           '1  pinhole camera model\npixel (212.5, 86.5) + depth 0.340 m\n'
           f'→ camera frame ({spot_c[0]:.3f}, {spot_c[1]:.3f}, {spot_c[2]:.3f}) m',
           edge=JOINT, ha='left', size=9.5)
    _boxed(ax, 0.23 + 0.0, 0.215,
           '2  rigid transform\ncamera frame → arm base frame\n'
           f'→ base ({spot_b[0]:.3f}, {spot_b[1]:.3f}, {spot_b[2]:.3f}) m',
           edge=LINK, ha='left', size=9.5)
    _boxed(ax, -0.58, 0.49,
           '3  calibration\nmeasures fx, fy, cx, cy and the\ncamera\'s place, once, before any of this',
           edge=PURPLE, ha='left', size=9.5)
    _arrow(ax, (-0.33, 0.455), (-0.035, CAM_HEIGHT + 0.02), color=PURPLE, lw=1.4)
    _arrow(ax, (0.228, 0.47), (0.03, CAM_HEIGHT - 0.03), color=JOINT, lw=1.4)
    _arrow(ax, (0.228, 0.20), (spot_w[0] + 0.012, spot_w[2] + 0.005), color=LINK, lw=1.4)
    _label(ax, -0.1, -0.095, 'side view: the table, a red box, a camera 0.40 m above, and an arm',
           size=9.5, color=MUTED)
    _save(fig, 'overview', 'from-pixel-to-gripper.svg')


def overview_errors_with_distance() -> None:
    """How each kind of small mistake turns into millimetres, as the object gets further away."""
    fig, ax = plt.subplots(figsize=(8.6, 5.0), facecolor='white')
    d = np.linspace(0.1, 1.0, 50)
    one_pixel = d / FX * 1000
    focal_1pc = (CX / FX) * d * 0.01 * 1000         # a point at the picture's edge, fx 1 % out
    rot_1deg = d * math.tan(math.radians(1)) * 1000
    shift_1mm = np.full_like(d, 1.0)
    ax.plot(d * 1000, rot_1deg, color=PURPLE, lw=2.4, label='camera pose turned 1° out (calibration)')
    ax.plot(d * 1000, focal_1pc, color=WRIST, lw=2.4, label='fx 1 % out, at the picture\'s edge (calibration)')
    ax.plot(d * 1000, one_pixel, color=LINK, lw=2.4, label='one pixel out (finding the object)')
    ax.plot(d * 1000, shift_1mm, color=MUTED, lw=2.0, ls='--', label='camera pose shifted 1 mm (calibration)')
    x0 = 340
    for y, col in ((340 * math.tan(math.radians(1)), PURPLE), (0.340 / FX * 1000, LINK)):
        ax.plot([x0], [y], 'o', color=col, mec=INK, ms=7, zorder=5)
    ax.annotate(f'{340 * math.tan(math.radians(1)):.3f} mm at 340 mm', (340, 340 * math.tan(math.radians(1))),
                (130, 8.5), fontsize=9.5, color=PURPLE,
                arrowprops={'arrowstyle': '-', 'color': PURPLE, 'lw': 1})
    ax.annotate(f'{0.340 / FX * 1000:.3f} mm at 340 mm', (340, 0.340 / FX * 1000), (560, 0.25),
                fontsize=9.5, color=LINK, arrowprops={'arrowstyle': '-', 'color': LINK, 'lw': 1})
    ax.set_xlabel('distance from the camera to the object (mm)', color=INK)
    ax.set_ylabel('how far off the point lands (mm)', color=INK)
    ax.set_xlim(100, 1000)
    ax.set_ylim(0, 18)
    ax.grid(color=GRID, lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper left', fontsize=9, frameon=False)
    _save(fig, 'overview', 'errors-grow-with-distance.svg')


# ==========================================================================
# 02_pinhole-camera-model
# ==========================================================================

def pinhole_one_ray() -> None:
    """Rays from the pinhole through two pixels, and three points on one ray."""
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    # horizontal: z ahead of the camera (m); vertical: x to the side (m). Image plane drawn at a
    # scaled distance in front, where the picture is the right way up.
    _axes(ax, (-0.10, 0.62), (-0.14, 0.17))
    ray = np.array([(SPOT_UV[0] - CX) / FX, 1.0])     # x per metre ahead
    img_z = 0.08                                     # where the picture is drawn, in the same units
    # the picture, as a line segment 320 pixels tall at scale img_z / FX per pixel
    half = CX * img_z / FX
    ax.plot([img_z, img_z], [-half, half], color=INK, lw=3, zorder=5)
    _label(ax, img_z, half + 0.018, 'the picture\n(u = 0 to 320)', size=9, color=INK)
    # the pinhole
    ax.plot([0], [0], 'o', color=INK, ms=8, zorder=7)
    _label(ax, -0.015, 0.018, 'pinhole', size=9.5, ha='right')
    # optical axis
    ax.plot([0, 0.6], [0, 0], color=GRID, lw=1, ls='--', zorder=1)
    _label(ax, 0.6, -0.012, 'z, straight ahead', size=9, color=MUTED, ha='right')
    # ray through the middle pixel
    ax.plot([0, 0.6], [0, 0], color=LINK, lw=1.8, zorder=3)
    ax.plot([img_z], [0], 's', color=LINK, ms=8, zorder=8)
    _label(ax, img_z + 0.01, -0.02, 'u = 160 (cx)', size=9, color=LINK, ha='left')
    # ray through u = 212.5
    ax.plot([0, 0.6], [0, 0.6 * ray[0]], color=JOINT, lw=2.4, zorder=3)
    ax.plot([img_z], [img_z * ray[0]], 's', color=JOINT, mec=INK, ms=8, zorder=8)
    _label(ax, img_z - 0.008, img_z * ray[0] + 0.022, 'u = 212.5', size=9, color=WRIST, ha='right')
    for z, lab in ((0.20, 'at 0.20 m'), (0.34, 'at 0.34 m'), (0.50, 'at 0.50 m')):
        x = z * ray[0]
        ax.plot([z], [x], 'o', color=GRIP, mec=INK, ms=9, zorder=8)
        _label(ax, z, x + 0.022, f'{lab}\nx = {x:.3f} m', size=9, color=INK)
    _label(ax, 0.31, -0.10,
           'All three red points are 0.1895 m to the side for every metre ahead,\n'
           'so all three land on pixel u = 212.5. The pixel keeps the direction and loses the distance.',
           size=9.5, color=MUTED)
    _save(fig, 'pinhole-camera-model', 'one-ray-many-points.svg')


def _depth_row() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cast one row of rays (v = 120) at a table 0.40 m away with a 6 cm box on it."""
    box_left, box_right, box_top = 0.035, 0.095, 0.340
    us = np.arange(0, W_PX, 8) + 0.5
    depths = []
    for u in us:
        s = (u - CX) / FX                                  # x per metre ahead
        z = CAM_HEIGHT
        # the ray hits the box top if x at depth 0.34 lies over the box
        x_top = s * box_top
        if box_left <= x_top <= box_right:
            z = box_top
        else:
            # it may hit the box's left side (x = box_left) between depth 0.34 and 0.40
            if s > 0:
                z_side = box_left / s
                if box_top <= z_side <= CAM_HEIGHT:
                    z = z_side
        depths.append(z)
    depths = np.array(depths)
    xs = (us - CX) * depths / FX
    return us, depths, xs


def pinhole_depth_row() -> None:
    """One row of a depth picture, and the points it becomes."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white',
                                 gridspec_kw={'width_ratios': [1, 1.25]})
    us, depths, xs = _depth_row()
    a1.step(us, depths, where='mid', color=LINK, lw=2)
    a1.plot(us, depths, 'o', color=LINK, ms=4)
    a1.set_ylim(0.43, 0.30)
    a1.set_xlim(0, 320)
    a1.set_xlabel('u, pixels across the row v = 120', color=INK)
    a1.set_ylabel('depth reading (m)', color=INK)
    a1.grid(color=GRID, lw=0.6)
    for s in ('top', 'right'):
        a1.spines[s].set_visible(False)
    a1.set_title('What the camera gives: one number per pixel', fontsize=11, color=INK)
    a1.annotate('table: 0.400', (40, 0.400), (40, 0.37), fontsize=9, color=INK,
                arrowprops={'arrowstyle': '-', 'color': MUTED, 'lw': 1})
    a1.annotate('box top: 0.340', (215, 0.340), (240, 0.32), fontsize=9, color=INK,
                arrowprops={'arrowstyle': '-', 'color': MUTED, 'lw': 1})

    _axes(a2, (-0.30, 0.30), (-0.08, 0.47))
    _table_and_box(a2, -0.28, 0.28, (0.035, 0.095, 0.060))
    _camera_body(a2, 0.0, CAM_HEIGHT + 0.012, -90, size=0.025)
    for x, d in zip(xs, depths):
        a2.plot([0, x], [CAM_HEIGHT, CAM_HEIGHT - d], color=LINK_PALE, lw=0.7, zorder=2)
    a2.plot(xs, CAM_HEIGHT - depths, 'o', color=LINK, mec=INK, ms=4.5, zorder=8)
    a2.set_title('What deprojection makes: one point per pixel', fontsize=11, color=INK)
    _label(a2, 0.0, -0.06, 'x = (u − cx) · depth / fx,  z = depth', size=9.5, color=MUTED)
    _save(fig, 'pinhole-camera-model', 'depth-row-to-points.svg')


def pinhole_mm_per_pixel() -> None:
    """How much of the table one pixel covers, against distance, for two sensors."""
    fig, ax = plt.subplots(figsize=(8.0, 4.6), facecolor='white')
    d = np.linspace(0.1, 1.0, 50)
    for fx, col, lab in ((FX, LINK, '320 × 240, fx = 277.1'), (554.3, SLIDE, '640 × 480, fx = 554.3')):
        ax.plot(d * 1000, d / fx * 1000, color=col, lw=2.4, label=f'{lab}: depth / fx')
    for z in (0.34, 0.40):
        mm = z / FX * 1000
        ax.plot([z * 1000], [mm], 'o', color=LINK, mec=INK, ms=7, zorder=5)
        ax.annotate(f'{mm:.3f} mm at {z * 1000:.0f} mm', (z * 1000, mm), (120, 2.2 + (z - 0.34) * 9),
                    fontsize=9.5, color=INK, arrowprops={'arrowstyle': '-', 'color': MUTED, 'lw': 1})
    ax.set_xlabel('depth: distance straight ahead of the camera (mm)', color=INK)
    ax.set_ylabel('width one pixel covers (mm)', color=INK)
    ax.set_xlim(100, 1000)
    ax.set_ylim(0, 4)
    ax.grid(color=GRID, lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper left', fontsize=9.5, frameon=False)
    _save(fig, 'pinhole-camera-model', 'millimetres-per-pixel.svg')


def tilted_camera() -> tuple[np.ndarray, np.ndarray]:
    """A camera 0.40 m up, 0.20 m back, looking forward (+y) and 60 degrees down."""
    a = math.radians(60)
    forward = np.array([0.0, math.cos(a), -math.sin(a)])
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    return np.column_stack([right, down, forward]), np.array([0.0, -0.20, 0.40])


def ray_meets_plane(u: float, v: float) -> tuple[np.ndarray, float]:
    r, c = tilted_camera()
    ray_world = r @ np.array([(u - CX) / FX, (v - CY) / FX, 1.0])
    t = -c[2] / ray_world[2]
    return c + t * ray_world, t


def pinhole_ray_meets_table() -> None:
    """With no depth, a known table plane gives the distance along the ray."""
    fig, ax = plt.subplots(figsize=(9.4, 5.0), facecolor='white')
    _axes(ax, (-0.50, 0.30), (-0.07, 0.50))
    r, c = tilted_camera()
    ax.add_patch(Rectangle((-0.48, -0.03), 0.76, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
    ax.plot([-0.48, 0.28], [0, 0], color='#b9a888', lw=1.5, zorder=2)
    _label(ax, 0.27, 0.015, 'table plane: z = 0', size=9, color=MUTED, ha='right')
    # side view: horizontal world y, vertical world z
    _camera_body(ax, c[1], c[2], -60, size=0.028)
    for (u, v), col, name in (((160, 120), LINK, 'pixel (160, 120)'), ((200, 150), JOINT, 'pixel (200, 150)')):
        p, t = ray_meets_plane(u, v)
        ax.plot([c[1], p[1]], [c[2], p[2]], color=col, lw=2.2, zorder=4)
        ax.plot([p[1]], [0], 'o', color=col, mec=INK, ms=9, zorder=8)
        txt = f'{name}\nmeets the table after {t:.4f} m of depth\nat (x, y) = ({p[0]:.4f}, {p[1]:.4f}) m'
        if u == 160:
            _boxed(ax, 0.02, 0.28, txt, edge=col, ha='left', size=9)
            _arrow(ax, (0.06, 0.24), (p[1] - 0.005, 0.02), color=col, lw=1.2)
        else:
            _boxed(ax, -0.49, 0.10, txt, edge=col, ha='left', size=9)
            _arrow(ax, (-0.25, 0.065), (p[1] - 0.008, 0.012), color=col, lw=1.2)
    # the camera height and tilt
    ax.plot([c[1], c[1]], [0, c[2]], color=GRID, lw=1, ls=':', zorder=1)
    _label(ax, c[1] - 0.012, 0.2, '0.40 m', size=9, color=MUTED, ha='right')
    ax.add_patch(Arc((c[1], c[2]), 0.14, 0.14, theta1=-60, theta2=0, color=MUTED, lw=1))
    ax.plot([c[1], c[1] + 0.1], [c[2], c[2]], color=GRID, lw=1, ls=':')
    _label(ax, c[1] + 0.085, c[2] - 0.03, '60°', size=9, color=MUTED)
    _label(ax, c[1], c[2] + 0.045, 'camera, 0.20 m back from the table\'s middle', size=9, color=INK)
    _label(ax, -0.1, -0.055, 'side view along x; y runs left to right', size=9, color=MUTED)
    _save(fig, 'pinhole-camera-model', 'ray-meets-table.svg')


# ==========================================================================
# 03_rigid-transforms
# ==========================================================================

def rigid_one_point_three_frames() -> None:
    """One spot on the box, written in three frames, seen from above."""
    fig, ax = plt.subplots(figsize=(9.8, 9.0), facecolor='white')
    _axes(ax, (-0.52, 0.40), (-0.36, 0.64))
    spot_c = deproject(*SPOT_UV, SPOT_DEPTH)
    spot_w = apply(T_WORLD_CAMERA, spot_c)
    spot_b = apply(invert(T_WORLD_BASE), spot_w)
    # joining the two transforms in the wrong order gives a triple the arm reads as base
    # coordinates; drawn where the arm would really go, in the world
    wrong_b = apply(T_WORLD_CAMERA @ invert(T_WORLD_BASE), spot_c)
    wrong = apply(T_WORLD_BASE, wrong_b)
    ax.add_patch(Rectangle((-0.30, -0.25), 0.60, 0.50, facecolor=TABLE, edgecolor='#b9a888', zorder=0))
    ax.add_patch(Rectangle((0.035, 0.012), 0.06, 0.06, facecolor=GRIP, edgecolor='#a83232', alpha=0.8,
                           zorder=2))
    # world frame at the middle of the table
    _frame(ax, (0.0, 0.0), (1, 0), (0, 1), 0.08, 'world\n(table middle)', (-0.07, -0.05))
    # camera frame: same place seen from above, x along world x, y along world -y
    _frame(ax, (0.0, 0.0), (0.72, 0), (0, -0.72), 0.08, '', (0, 0), x_label='', y_label='')
    _label(ax, 0.09, -0.07, 'camera\n(0.40 m above;\ny points to −y)', size=8.5, color=MUTED, ha='left')
    # base frame
    bx, by = T_WORLD_BASE[0, 3], T_WORLD_BASE[1, 3]
    a = math.radians(30)
    _frame(ax, (bx, by), (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a)), 0.09,
           'arm base\n(turned 30°)', (bx, by - 0.07))
    ax.add_patch(Rectangle((bx - 0.05, by - 0.05), 0.10, 0.10, facecolor='#bbbbbb', edgecolor=INK,
                           alpha=0.5, zorder=1))
    # the spot, and the base's view of it
    ax.plot([spot_w[0]], [spot_w[1]], 'o', color=JOINT, mec=INK, ms=10, zorder=11)
    ax.plot([bx, spot_w[0]], [by, spot_w[1]], color=LINK, lw=1.3, ls='--', zorder=3)
    ax.plot([wrong[0]], [wrong[1]], 'X', color=MUTED, ms=11, zorder=11)
    ax.plot([bx, wrong[0]], [by, wrong[1]], color=MUTED, lw=1.1, ls='--', zorder=3)
    _boxed(ax, -0.50, -0.30,
           'the same spot, in three frames\n'
           f'camera:  ({spot_c[0]:.4f}, {spot_c[1]:.4f}, {spot_c[2]:.3f})\n'
           f'world:   ({spot_w[0]:.4f}, {spot_w[1]:.4f}, {spot_w[2]:.3f})\n'
           f'base:    ({spot_b[0]:.4f}, {spot_b[1]:.4f}, {spot_b[2]:.3f})',
           edge=JOINT, ha='left', size=9)
    ax.texts[-1].set_family('monospace')
    _arrow(ax, (-0.12, -0.26), (spot_w[0] - 0.006, spot_w[1] - 0.012), color=JOINT, lw=1.2)
    _boxed(ax, -0.20, 0.53,
           f'the same two transforms joined\nin the wrong order: the arm reads\n({wrong_b[0]:.4f}, {wrong_b[1]:.4f}) and goes here',
           edge=GRID, ha='left', size=9, color=MUTED)
    _label(ax, -0.06, 0.62, 'seen from above: world x to the right, world y up the page', size=9.5, color=MUTED)
    _save(fig, 'rigid-transforms', 'one-point-three-frames.svg')


def _two_link(shoulder: np.ndarray, target: np.ndarray, l1: float, l2: float,
              elbow_up: bool = True) -> np.ndarray:
    """Elbow position for a two-link arm reaching target."""
    d = target - shoulder
    dist = np.linalg.norm(d)
    a = math.acos((l1 ** 2 + dist ** 2 - l2 ** 2) / (2 * l1 * dist))
    base_ang = math.atan2(d[1], d[0])
    ang = base_ang + a if elbow_up else base_ang - a
    return shoulder + l1 * np.array([math.cos(ang), math.sin(ang)])


def rigid_wrist_chain() -> None:
    """Joining base to flange, flange to camera, and the camera's point."""
    fig, ax = plt.subplots(figsize=(10.4, 6.0), facecolor='white')
    _axes(ax, (-0.14, 0.86), (-0.10, 0.74))
    t_base_flange = transform(rot_x(math.pi), np.array([0.40, 0.0, 0.45]))
    t_flange_cam = transform(np.eye(3), np.array([0.06, 0.0, 0.0]))
    p_cam = np.array([0.0644, -0.0411, 0.340])
    p_base = apply(t_base_flange @ t_flange_cam, p_cam)

    ax.add_patch(Rectangle((-0.12, -0.03), 0.96, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
    ax.plot([-0.12, 0.84], [0, 0], color='#b9a888', lw=1.5, zorder=2)
    ax.add_patch(Rectangle((0.495, 0), 0.06, p_base[2], facecolor=GRIP, edgecolor='#a83232', alpha=0.85,
                           zorder=3))
    ax.add_patch(Rectangle((-0.06, 0), 0.12, 0.05, facecolor='#999999', edgecolor=INK, zorder=4))
    shoulder = np.array([0.0, 0.20])
    flange = np.array([0.40, 0.45])
    wrist = flange + np.array([0.0, 0.09])
    elbow = _two_link(shoulder, wrist, 0.38, 0.30)
    ax.plot([0, 0], [0.05, 0.20], color=LINK, lw=8, solid_capstyle='round', zorder=4)
    ax.plot(*zip(shoulder, elbow, wrist, flange), color=LINK, lw=8, solid_capstyle='round', zorder=4)
    for j in (shoulder, elbow, wrist):
        ax.plot(*j, 'o', color=JOINT, mec=INK, ms=10, zorder=5)
    # the gripper fingers below the flange
    ax.plot([flange[0] - 0.02, flange[0] - 0.02], [flange[1], flange[1] - 0.06], color=GRIP, lw=4, zorder=4)
    ax.plot([flange[0] + 0.02, flange[0] + 0.02], [flange[1], flange[1] - 0.06], color=GRIP, lw=4, zorder=4)
    ax.plot([flange[0] - 0.03, flange[0] + 0.07], [flange[1], flange[1]], color=INK, lw=3, zorder=5)
    cam = flange + np.array([0.06, 0.0])
    _camera_body(ax, cam[0], cam[1] - 0.005, -90, size=0.022)
    # the ray from camera to the spot
    ax.plot([cam[0], p_base[0]], [cam[1] - 0.02, p_base[2]], color=JOINT, lw=2.2, zorder=4)
    ax.plot([p_base[0]], [p_base[2]], 'o', color=JOINT, mec=INK, ms=9, zorder=8)
    # frames: base (x right, z up), flange (x right, z down), camera (x right, z down)
    _frame(ax, (0.0, 0.0), (1, 0), None, 0.09, '', (0, 0))
    _label(ax, -0.09, -0.04, 'base frame', size=9.5)
    # label the transforms along the chain
    _curved(ax, (0.02, 0.06), (flange[0] - 0.035, flange[1] + 0.02), LINK, rad=-0.35, lw=2.0)
    _boxed(ax, -0.12, 0.64, 'T base→flange\nfrom the joint angles\n(forward kinematics)', edge=LINK,
           ha='left', size=9)
    _curved(ax, (flange[0] + 0.005, flange[1] + 0.025), (cam[0] + 0.005, cam[1] + 0.02), PURPLE, rad=-0.9,
            lw=2.0)
    _boxed(ax, 0.50, 0.64, 'T flange→camera\n0.06 m along the flange\'s x\n(hand-eye calibration)',
           edge=PURPLE, ha='left', size=9)
    _arrow(ax, (0.53, 0.595), (cam[0] + 0.01, cam[1] + 0.05), color=PURPLE, lw=1.1)
    _boxed(ax, 0.60, 0.30, f'p in camera frame\n({p_cam[0]:.4f}, {p_cam[1]:.4f}, {p_cam[2]:.3f})',
           edge=JOINT, ha='left', size=9)
    _boxed(ax, 0.60, 0.17,
           f'T base→flange · T flange→camera · p\n= ({p_base[0]:.4f}, {p_base[1]:.4f}, {p_base[2]:.3f}) in base',
           edge=INK, ha='left', size=9)
    _arrow(ax, (0.60, 0.20), (p_base[0] + 0.01, p_base[2] + 0.005), color=INK, lw=1.1)
    _label(ax, 0.36, -0.08, 'side view: base x to the right, base z up. The flange and camera z point down.',
           size=9, color=MUTED)
    _save(fig, 'rigid-transforms', 'wrist-camera-chain.svg')


def rigid_quaternion() -> None:
    """Two rotations as one axis and one angle, and the four numbers they give.

    Each panel looks straight down the turning axis, so the turn is a plain turn on the page and
    the axis is the dot in the middle, pointing out of the page at the reader.
    """
    fig, axes = _panels(2, (11.0, 5.6))
    cases = [
        ('30° about z', np.array([0.0, 0.0, 1.0]), 30.0, (0, 1), 'z',
         'the arm base, turned on the floor\n(seen from above: x right, y up the page)'),
        ('180° about x', np.array([1.0, 0.0, 0.0]), 180.0, (1, 2), 'x',
         'the camera above the table, looking down\n(seen along x: y right, z up the page)'),
    ]
    colours = (GRIP, SLIDE, LINK)
    for ax, (title, axis, deg, (i, j), axis_name, note) in zip(axes, cases):
        _axes(ax, (-1.5, 1.5), (-1.85, 1.5))
        r = _rodrigues(axis, math.radians(deg))
        for k in (i, j):
            e = np.zeros(3)
            e[k] = 1.0
            turned = r @ e
            before = (e[i], e[j])
            after = (turned[i], turned[j])
            _arrow(ax, (0, 0), before, color=GRID, lw=2.2)
            _label(ax, before[0] * 1.16, before[1] * 1.16 + (0.0 if before[1] == 0 else 0.0), 'xyz'[k], size=10,
                   color=MUTED)
            _arrow(ax, (0, 0), after, color=colours[k], lw=2.8)
            off = np.array(after) * 1.2 + np.array([0.0, 0.12 if abs(after[1]) < 0.6 else 0.0])
            _label(ax, off[0], off[1], 'xyz'[k] + '′', size=11, color=colours[k], weight='bold')
        # the arc of the turn, drawn from the first in-plane axis
        th = np.linspace(0, math.radians(deg), 60)
        ax.plot(0.45 * np.cos(th), 0.45 * np.sin(th), color=PURPLE, lw=1.6, zorder=3)
        mid = math.radians(deg) / 2
        _label(ax, 0.62 * math.cos(mid), 0.62 * math.sin(mid), f'{deg:.0f}°', size=10.5, color=PURPLE,
               weight='bold')
        # the turning axis, out of the page
        ax.plot([0], [0], 'o', color='white', mec=PURPLE, ms=13, mew=2, zorder=9)
        ax.plot([0], [0], 'o', color=PURPLE, ms=4, zorder=10)
        _label(ax, -0.12, -0.2, f'turning axis: {axis_name},\nout of the page', size=9, color=PURPLE,
               ha='right')
        half = math.radians(deg) / 2
        q = (axis[0] * math.sin(half), axis[1] * math.sin(half), axis[2] * math.sin(half), math.cos(half))
        _title(ax, 0.0, 1.4, title)
        _label(ax, 0.0, -1.4, note, size=9.5, color=MUTED)
        _boxed(ax, 0.0, -1.75,
               f'(x, y, z, w) = ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})',
               edge=PURPLE, size=9.5)
    _save(fig, 'rigid-transforms', 'quaternion-axis-and-angle.svg')


def _rodrigues(axis: np.ndarray, angle: float) -> np.ndarray:
    k = axis / np.linalg.norm(axis)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(angle) * kx + (1 - math.cos(angle)) * (kx @ kx)


def rigid_blending() -> None:
    """Blending from 0 to 90 degrees: along the circle, or straight across."""
    fig, ax = plt.subplots(figsize=(7.4, 6.2), facecolor='white')
    _axes(ax, (-0.25, 1.35), (-0.22, 1.25))
    th = np.linspace(0, math.pi / 2, 80)
    ax.plot(np.cos(th), np.sin(th), color=PURPLE, lw=1.6, zorder=2)
    ax.plot([1, 0], [0, 1], color=WRIST, lw=1.6, ls='--', zorder=2)
    _arrow(ax, (0, 0), (1, 0), color=INK, lw=2.0)
    _arrow(ax, (0, 0), (0, 1), color=INK, lw=2.0)
    _label(ax, 1.05, -0.07, 'start: 0°', size=9.5, ha='left')
    _label(ax, -0.05, 1.08, 'end: 90°', size=9.5, ha='right')
    for t in (0.25, 0.5, 0.75):
        a = math.pi / 2 * t
        s = np.array([math.cos(a), math.sin(a)])
        lin = (1 - t) * np.array([1.0, 0.0]) + t * np.array([0.0, 1.0])
        ax.plot([0, s[0]], [0, s[1]], color=PURPLE, lw=0.8, alpha=0.5, zorder=1)
        ax.plot([0, lin[0]], [0, lin[1]], color=WRIST, lw=0.8, alpha=0.6, zorder=1)
        ax.plot(*s, 'o', color=PURPLE, mec=INK, ms=9, zorder=6)
        ax.plot(*lin, 's', color=WRIST, mec=INK, ms=8, zorder=6)
        ang = math.degrees(math.atan2(lin[1], lin[0]))
        _label(ax, s[0] + 0.05, s[1] + 0.05, f't = {t}: {math.degrees(a):.1f}°', size=9, color=PURPLE,
               ha='left')
        ax.text(lin[0] - 0.04, lin[1] - 0.055, f'{ang:.1f}°, length {np.linalg.norm(lin):.3f}', fontsize=8.5,
                color=WRIST, ha='right', va='center', zorder=9,
                bbox={'boxstyle': 'square,pad=0.15', 'facecolor': 'white', 'edgecolor': 'none'})
    _label(ax, 0.55, -0.16,
           'purple: spherical blend (slerp), equal steps of angle, length stays 1\n'
           'orange: straight blend of the numbers, uneven steps, and the axis shrinks',
           size=9, color=INK)
    _save(fig, 'rigid-transforms', 'blending-two-turns.svg')


# ==========================================================================
# 04_calibration
# ==========================================================================

BOARD_COLS: int = 9
BOARD_ROWS: int = 6
BOARD_SQ: float = 0.020
K1_TRUE: float = -0.12
K2_TRUE: float = 0.03


def _board_points() -> np.ndarray:
    return np.array([[i * BOARD_SQ, j * BOARD_SQ, 0.0] for j in range(BOARD_ROWS) for i in range(BOARD_COLS)])


def _board_pose(dist: float, tilt_x: float, tilt_y: float, roll: float,
                shift: tuple[float, float] = (0.0, 0.0)) -> tuple[np.ndarray, np.ndarray]:
    r = rot_x(math.radians(tilt_x)) @ rot_y(math.radians(tilt_y)) @ rot_z(math.radians(roll))
    ctr = np.array([(BOARD_COLS - 1) * BOARD_SQ / 2, (BOARD_ROWS - 1) * BOARD_SQ / 2, 0.0])
    t = np.array([shift[0], shift[1], dist]) - r @ ctr
    return r, t


def _project_distorted(pts: np.ndarray, r: np.ndarray, t: np.ndarray, fx: float = FX,
                       k1: float = K1_TRUE, k2: float = K2_TRUE) -> np.ndarray:
    pc = pts @ r.T + t
    x = pc[:, 0] / pc[:, 2]
    y = pc[:, 1] / pc[:, 2]
    r2 = x * x + y * y
    f = 1 + k1 * r2 + k2 * r2 * r2
    return np.column_stack([fx * x * f + CX, fx * y * f + CY])


def _picture_frame(ax: Axes, x0: float, y0: float, scale: float) -> None:
    ax.add_patch(Rectangle((x0, y0), W_PX * scale, H_PX * scale, facecolor=WALL, edgecolor=INK, lw=1.0,
                           zorder=1))


def _draw_board(ax: Axes, px: np.ndarray, x0: float, y0: float, scale: float, color: str = INK,
                marker: str = 'o', ms: float = 2.5, lines: bool = True) -> None:
    # page coordinates: v counts down, so flip it
    xs = x0 + px[:, 0] * scale
    ys = y0 + (H_PX - px[:, 1]) * scale
    g_x = xs.reshape(BOARD_ROWS, BOARD_COLS)
    g_y = ys.reshape(BOARD_ROWS, BOARD_COLS)
    if lines:
        for j in range(BOARD_ROWS):
            ax.plot(g_x[j], g_y[j], color=color, lw=0.8, zorder=3)
        for i in range(BOARD_COLS):
            ax.plot(g_x[:, i], g_y[:, i], color=color, lw=0.8, zorder=3)
    ax.plot(xs, ys, marker, color=color, ms=ms, zorder=4, ls='none')


def calibration_board_views() -> None:
    """The printed board, seen by the camera from six different angles."""
    poses = [(0.24, 0, 0, 0, (0, 0)), (0.27, 30, 0, 10, (0.02, 0.0)), (0.26, 0, -32, -15, (-0.02, 0.01)),
             (0.30, -28, 20, 20, (0.0, -0.01)), (0.24, 20, 25, -5, (0.02, 0.01)), (0.28, -20, -25, 30, (-0.02, 0.0))]
    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    s = 1.0
    gap = 30
    _axes(ax, (-10, 3 * W_PX + 2 * gap + 10), (-50, 2 * H_PX + gap + 10))
    pts = _board_points()
    for k, (d, tx, ty, rz, sh) in enumerate(poses):
        col = k % 3
        row = 1 - k // 3
        x0 = col * (W_PX + gap)
        y0 = row * (H_PX + gap)
        _picture_frame(ax, x0, y0, s)
        r, t = _board_pose(d, tx, ty, rz, sh)
        px = _project_distorted(pts, r, t)
        assert px.min() > 0 and px[:, 0].max() < W_PX and px[:, 1].max() < H_PX, 'board leaves the picture'
        _draw_board(ax, px, x0, y0, s, color=LINK)
        # mark the first corner, so the numbering is visible
        ax.plot(x0 + px[0, 0] * s, y0 + (H_PX - px[0, 1]) * s, 'o', color=GRIP, ms=6, zorder=5)
        _label(ax, x0 + 6, y0 + H_PX - 12, f'view {k + 1}', size=9, color=MUTED, ha='left')
    _label(ax, (3 * W_PX + 2 * gap) / 2, -30,
           'The same 9 × 6 corners in six pictures. The red dot is corner 0 in every view,\n'
           'so each detected corner can be matched to its known place on the board.',
           size=9.5, color=MUTED)
    _save(fig, 'calibration', 'board-in-many-views.svg')


def calibration_flat_views() -> None:
    """A flat-on board cannot tell a near, wide camera from a far, zoomed one; a tilted board can."""
    pts = _board_points()
    fx_b = 1754.0
    d_a = 0.30
    d_b = d_a * fx_b / FX
    fig, axes = _panels(2, (11.4, 4.8))
    for ax, tilt, title in ((axes[0], 0, 'board facing the camera'), (axes[1], 35, 'board tilted 35°')):
        _axes(ax, (-10, W_PX + 10), (-50, H_PX + 30))
        _picture_frame(ax, 0, 0, 1.0)
        r_a, t_a = _board_pose(d_a, tilt, 0, 8)
        r_b, t_b = _board_pose(d_b, tilt, 0, 8)
        pa = _project_distorted(pts, r_a, t_a, fx=FX, k1=0, k2=0)
        pb = _project_distorted(pts, r_b, t_b, fx=fx_b, k1=0, k2=0)
        _draw_board(ax, pa, 0, 0, 1.0, color=LINK, ms=4)
        _draw_board(ax, pb, 0, 0, 1.0, color=GRIP, marker='x', ms=5, lines=False)
        diff = np.linalg.norm(pa - pb, axis=1).max()
        _title(ax, W_PX / 2, H_PX + 17, title, size=11)
        _label(ax, W_PX / 2, -22, f'largest gap between blue and red corners: {diff:.2f} pixels',
               size=9.5, color=INK)
    fig.text(0.5, 0.06,
             f'blue: fx = {FX} with the board {d_a:.2f} m away.   red crosses: fx = {fx_b:.0f} '
             f'with the board {d_b:.2f} m away.',
             ha='center', fontsize=9.5, color=MUTED)
    _save(fig, 'calibration', 'flat-views-cannot-tell.svg')


def calibration_distortion() -> None:
    """Where a pinhole puts a grid of straight lines, and where the real lens puts them."""
    fig, ax = plt.subplots(figsize=(8.8, 6.6), facecolor='white')
    _axes(ax, (-15, W_PX + 15), (-45, H_PX + 15))
    _picture_frame(ax, 0, 0, 1.0)
    # a grid of directions that a pinhole would put on a regular grid of pixels
    us = np.linspace(8, W_PX - 8, 9)
    vs = np.linspace(8, H_PX - 8, 7)

    def lens(u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = (u - CX) / FX
        y = (v - CY) / FX
        r2 = x * x + y * y
        f = 1 + K1_TRUE * r2 + K2_TRUE * r2 * r2
        return FX * x * f + CX, FX * y * f + CY

    fine = np.linspace(0, 1, 60)
    for v in vs:
        u_line = us[0] + (us[-1] - us[0]) * fine
        v_line = np.full_like(u_line, v)
        ax.plot(u_line, H_PX - v_line, color=GRID, lw=1.0, zorder=2)
        lu, lv = lens(u_line, v_line)
        ax.plot(lu, H_PX - lv, color=LINK, lw=1.4, zorder=3)
    for u in us:
        v_line = vs[0] + (vs[-1] - vs[0]) * fine
        u_line = np.full_like(v_line, u)
        ax.plot(u_line, H_PX - v_line, color=GRID, lw=1.0, zorder=2)
        lu, lv = lens(u_line, v_line)
        ax.plot(lu, H_PX - lv, color=LINK, lw=1.4, zorder=3)
    uu, vv = np.meshgrid(us, vs)
    lu, lv = lens(uu, vv)
    ax.plot(uu.ravel(), H_PX - vv.ravel(), 'o', color=MUTED, ms=3, zorder=4)
    ax.plot(lu.ravel(), H_PX - lv.ravel(), 'o', color=GRIP, ms=4, zorder=5)
    corner = (us[0], vs[0])
    cu, cv = lens(np.array(corner[0]), np.array(corner[1]))
    shift = math.hypot(float(cu) - corner[0], float(cv) - corner[1])
    ax.annotate(f'moved {shift:.1f} pixels', (float(cu), H_PX - float(cv)), (60, 190), fontsize=9.5,
                color=GRIP, zorder=10, arrowprops={'arrowstyle': '-', 'color': GRIP, 'lw': 1},
                bbox={'boxstyle': 'round,pad=0.3', 'facecolor': 'white', 'edgecolor': GRIP})
    _label(ax, W_PX / 2, -18,
           f'grey: where a pinhole puts straight lines.  blue: where a lens with k1 = {K1_TRUE}, '
           f'k2 = {K2_TRUE} puts them.\nred dots: where each crossing really lands. '
           f'At the corner pixel ({corner[0]:.0f}, {corner[1]:.0f}) it is {shift:.1f} pixels; '
           'in the middle it is 0.',
           size=9.2, color=INK)
    _save(fig, 'calibration', 'lens-bends-straight-lines.svg')


def _t2(angle: float, x: float, y: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, x], [s, c, y], [0, 0, 1.0]])


def _inv2(m: np.ndarray) -> np.ndarray:
    r = m[:2, :2]
    t = m[:2, 2]
    out = np.eye(3)
    out[:2, :2] = r.T
    out[:2, 2] = -r.T @ t
    return out


def calibration_hand_eye() -> None:
    """Two poses of a wrist camera looking at one fixed board: A X = X B."""
    fig, ax = plt.subplots(figsize=(10.6, 6.4), facecolor='white')
    _axes(ax, (-0.10, 1.00), (-0.08, 0.70))
    ax.add_patch(Rectangle((-0.08, -0.03), 0.98, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
    ax.plot([-0.08, 0.90], [0, 0], color='#b9a888', lw=1.5, zorder=2)
    # the board, lying on the table
    board = _t2(0.0, 0.52, 0.0)
    ax.add_patch(Rectangle((0.44, 0.0), 0.16, 0.008, facecolor='#333333', zorder=3))
    for k in range(8):
        ax.add_patch(Rectangle((0.44 + k * 0.02, 0.0), 0.01, 0.008, facecolor='white', zorder=4))
    _label(ax, 0.52, -0.05, 'the board: fixed on the table', size=9, color=INK)
    # in this flat drawing a pose is (angle, x, y); the flange's own x axis points out of the flange
    x_hand_eye = _t2(math.radians(0), 0.06, 0.03)   # camera 6 cm out and 3 cm to the side of the flange
    poses = [(_t2(math.radians(-80), 0.30, 0.42), LINK, 'pose 1'),
             (_t2(math.radians(-115), 0.70, 0.38), SLIDE, 'pose 2')]
    cams = []
    flanges = []
    for m, col, name in poses:
        f = m[:2, 2]
        fx_dir = m[:2, 0]
        wrist = f - fx_dir * 0.09
        ax.plot(*zip(wrist - fx_dir * 0.08, wrist), color=col, lw=6, alpha=0.35, solid_capstyle='round',
                zorder=4)
        ax.plot(*zip(wrist, f), color=col, lw=6, solid_capstyle='round', zorder=5)
        ax.plot(*wrist, 'o', color=JOINT, mec=INK, ms=7, zorder=5)
        cm = m @ x_hand_eye
        c = cm[:2, 2]
        ang = math.degrees(math.atan2(cm[1, 0], cm[0, 0]))
        _camera_body(ax, c[0], c[1], ang, size=0.02)
        # the camera's line of sight to the board
        ax.plot([c[0], 0.52], [c[1], 0.004], color=col, lw=1.0, ls=':', zorder=2)
        ax.plot(*f, 's', color=INK, ms=6, zorder=6)
        _label(ax, f[0] + (-0.10 if name == 'pose 1' else 0.10), f[1] + (0.10 if name == 'pose 1' else 0.02),
               name, size=10.5, color=col, weight='bold')
        cams.append(cm)
        flanges.append(m)
    # A: flange 1 to flange 2 (from joint angles). B: camera 1 to camera 2 (from the board).
    f1, f2 = flanges[0][:2, 2], flanges[1][:2, 2]
    c1, c2 = cams[0][:2, 2], cams[1][:2, 2]
    _curved(ax, (f1[0] + 0.02, f1[1] + 0.04), (f2[0] - 0.02, f2[1] + 0.05), INK, rad=-0.35)
    _label(ax, (f1[0] + f2[0]) / 2, 0.64, 'A: how the flange moved\n(read from the joint angles)',
           size=9.5, color=INK)
    _curved(ax, (c1[0] + 0.03, c1[1] - 0.02), (c2[0] - 0.03, c2[1] - 0.02), PURPLE, rad=0.3)
    _label(ax, 0.82, 0.17, 'B: how the camera moved\n(worked out from the board)',
           size=9.5, color=PURPLE)
    for f, c in ((f1, c1), (f2, c2)):
        ax.plot([f[0], c[0]], [f[1], c[1]], color=GRIP, lw=2.4, zorder=7)
    _boxed(ax, -0.07, 0.44, 'X: flange → camera\n(the red bar: the same\nat both poses, unknown)',
           edge=GRIP, color=GRIP, ha='left', size=9.5)
    _arrow(ax, (0.13, 0.44), ((f1[0] + c1[0]) / 2 - 0.01, (f1[1] + c1[1]) / 2), color=GRIP, lw=1.2)
    # check the relation numerically for the drawing
    a = _inv2(flanges[0]) @ flanges[1]
    c1_board = _inv2(cams[0]) @ board
    c2_board = _inv2(cams[1]) @ board
    b = c1_board @ _inv2(c2_board)
    err = np.abs(a @ x_hand_eye - x_hand_eye @ b).max()
    ang_a = math.degrees(math.atan2(a[1, 0], a[0, 0]))
    ang_b = math.degrees(math.atan2(b[1, 0], b[0, 0]))
    _boxed(ax, -0.07, 0.12,
           f'A · X = X · B\nA turns {ang_a:.1f}°, B turns {ang_b:.1f}°\n'
           + ('the two sides agree to 12 decimal places' if err < 1e-12 else f'the two sides differ by {err:.2g}'),
           edge=INK, ha='left', size=9.5)
    _save(fig, 'calibration', 'hand-eye-two-poses.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    overview_pixel_to_gripper()
    overview_errors_with_distance()
    pinhole_one_ray()
    pinhole_depth_row()
    pinhole_mm_per_pixel()
    pinhole_ray_meets_table()
    rigid_one_point_three_frames()
    rigid_wrist_chain()
    rigid_quaternion()
    rigid_blending()
    calibration_board_views()
    calibration_flat_views()
    calibration_distortion()
    calibration_hand_eye()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
