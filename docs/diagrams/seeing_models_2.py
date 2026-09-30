"""Generate the diagrams for the second half of docs/05_neural-network-models/02_seeing-models/.

The pages covered here are 05_keypoints-and-object-pose, 06_depth-from-pictures,
07_open-vocabulary-models and 08_tracking-and-motion. Each page's pictures go to a
folder named after it, under docs/images/seeing-models/.

Run with:  pixi run python ../docs/diagrams/seeing_models_2.py
Add --png <dir> to also write PNG copies for checking by eye.

Nothing here is the output of a real model. The pictures are drawn by hand to show
one idea each, so they carry no measured numbers.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Arc, Circle, Ellipse, FancyBboxPatch, Polygon,  # noqa: E402
                                Rectangle)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'seeing-models'
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

TABLE: str = '#e9dcc3'
WALL: str = '#f4f4f4'
GLASS: str = '#cfe8ef'
PURPLE: str = '#8e5ec9'


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


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='top', color=MUTED)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.5, style: str = '-|>', z: int = 6) -> None:
    ax.annotate('', xy=b, xytext=a, zorder=z,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0})


def _frame(ax: Axes, x0: float, y0: float, w: float, h: float, color: str = MUTED) -> None:
    """A thin border that marks the edge of one camera picture."""
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor='none', edgecolor=color, lw=1.0,
                           zorder=1))


def _mug(ax: Axes, x: float, y: float, w: float = 1.0, h: float = 1.1, color: str = GRIP,
         handle: str = 'right', alpha: float = 1.0, edge: str = INK, z: int = 3,
         lw: float = 1.0) -> None:
    """A mug seen from the side: a body with its bottom centre at (x, y), and a handle."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=edge, lw=lw,
                           alpha=alpha, zorder=z))
    side: float = 1.0 if handle == 'right' else -1.0
    ax.add_patch(Arc((x + side * w / 2, y + h * 0.52), w * 0.62, h * 0.55,
                     theta1=-90 if side > 0 else 90, theta2=90 if side > 0 else 270,
                     color=color, lw=6 * w, alpha=alpha, zorder=z - 1))


def _box2d(ax: Axes, x: float, y: float, w: float, h: float, color: str = WRIST,
           z: int = 2, alpha: float = 1.0) -> None:
    """A cardboard box seen from the front, with a thin top face for depth."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=1.0,
                           zorder=z, alpha=alpha))
    top = [(x - w / 2, y + h), (x + w / 2, y + h), (x + w / 2 + 0.2 * w, y + h + 0.15 * w),
           (x - w / 2 + 0.2 * w, y + h + 0.15 * w)]
    ax.add_patch(Polygon(top, closed=True, facecolor=color, edgecolor=INK, lw=1.0,
                         zorder=z, alpha=alpha * 0.7))


def _table(ax: Axes, x0: float, x1: float, y: float, depth: float = 0.35) -> None:
    ax.add_patch(Rectangle((x0, y - depth), x1 - x0, depth, facecolor=TABLE, edgecolor='none',
                           zorder=1))


def _camera(ax: Axes, x: float, y: float, facing: float = 90.0, size: float = 0.5,
            color: str = INK) -> None:
    """A small camera body with its lens pointing in the direction `facing` (degrees)."""
    c: float = math.cos(math.radians(facing))
    s: float = math.sin(math.radians(facing))
    hw: float = size * 0.6
    hh: float = size * 0.4
    corners = [(x + dx * c - dy * s, y + dx * s + dy * c)
               for dx, dy in ((-hh, -hw), (hh, -hw), (hh, hw), (-hh, hw))]
    ax.add_patch(Polygon(corners, closed=True, facecolor=color, edgecolor=color, zorder=5))
    lens = [(x + dx * c - dy * s, y + dx * s + dy * c)
            for dx, dy in ((hh, -hw * 0.45), (hh + size * 0.35, -hw * 0.7),
                           (hh + size * 0.35, hw * 0.7), (hh, hw * 0.45))]
    ax.add_patch(Polygon(lens, closed=True, facecolor=color, edgecolor=color, zorder=5))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 05_keypoints-and-object-pose
# --------------------------------------------------------------------------

POSE_DOC: str = 'keypoints-and-object-pose'


def keypoints_on_a_mug() -> None:
    """A photo of a mug, and the same mug with five named points the model marks on it."""
    fig, (left, right) = _panels(2, (11.0, 4.8))
    for ax in (left, right):
        _axes(ax, (-4.4, 4.4), (-1.9, 3.1))
        _frame(ax, -2.9, -0.9, 5.8, 3.6)
        _table(ax, -2.9, 2.9, -0.2, depth=0.7)
    _mug(left, -0.2, -0.2, w=1.6, h=1.9)
    _title(left, 0.0, 2.95, 'What goes in: a photo')
    _caption(left, 0.0, -1.1, 'Only coloured pixels.\nNothing is marked yet.')

    _mug(right, -0.2, -0.2, w=1.6, h=1.9, alpha=0.35, edge=MUTED)
    body_l, body_r, bottom, top = -1.0, 0.6, -0.2, 1.7
    points = [((body_l, top), 'rim, left', (-3.1, 2.3), LINK),
              ((body_r, top), 'rim, right', (3.1, 2.3), LINK),
              ((1.07, 1.24), 'handle, top', (3.1, 1.4), SLIDE),
              ((1.07, 0.46), 'handle, bottom', (3.1, 0.4), SLIDE),
              ((-0.2, bottom), 'base centre', (-3.1, -0.5), WRIST)]
    for (px, py), name, (lx, ly), color in points:
        right.plot([px, lx], [py, ly], color=GRID, lw=1.0, zorder=7)
        right.plot([px], [py], 'o', ms=11, color=color, mec=INK, mew=1.0, zorder=8)
        _label(right, lx, ly, name, size=10, color=INK,
               ha='left' if lx > 0 else 'right')
    _title(right, 0.0, 2.95, 'What comes out: named points')
    _caption(right, 0.0, -1.1, 'Each point is two numbers:\nits column and row in the photo.')
    _save(fig, POSE_DOC, 'keypoints-on-a-mug.svg')


def _oblique(p: NDArray[np.float64]) -> tuple[float, float]:
    """Project a 3D point to the page: x right, z up, y drawn going back at 30 degrees."""
    return (float(p[0] + 0.5 * p[1] * math.cos(math.radians(30))),
            float(p[2] + 0.5 * p[1] * math.sin(math.radians(30))))


def _rot_z(deg: float) -> NDArray[np.float64]:
    c: float = math.cos(math.radians(deg))
    s: float = math.sin(math.radians(deg))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _rot_x(deg: float) -> NDArray[np.float64]:
    c: float = math.cos(math.radians(deg))
    s: float = math.sin(math.radians(deg))
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def _cuboid(ax: Axes, centre: NDArray[np.float64], size: tuple[float, float, float],
            rot: NDArray[np.float64], face: str = WRIST, edge: str = INK, lw: float = 1.0,
            ls: str = '-', fill: bool = True, z: int = 3) -> list[tuple[float, float]]:
    """Draw a box as its twelve edges, with the three faces nearest the viewer filled."""
    sx, sy, sz = (s / 2 for s in size)
    corners: list[NDArray[np.float64]] = []
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            for dz in (-sz, sz):
                corners.append(centre + rot @ np.array([dx, dy, dz]))
    flat = [_oblique(c) for c in corners]
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    if fill:
        # Only the faces that point towards the viewer are drawn, each a different shade.
        normals = [-rot[:, 0], rot[:, 0], -rot[:, 1], rot[:, 1], -rot[:, 2], rot[:, 2]]
        view = np.array([0.43, -1.0, 0.25])
        for f, n in zip(faces, normals):
            facing = float(n @ view) / float(np.linalg.norm(view))
            if facing <= 0.0:
                continue
            base = np.array(matplotlib.colors.to_rgb(face))
            shade = base * (0.8 + 0.2 * facing) + (1.0 - facing) * 0.12
            ax.add_patch(Polygon([flat[i] for i in f], closed=True,
                                 facecolor=np.clip(shade, 0.0, 1.0), edgecolor=edge, lw=lw,
                                 zorder=z))
    else:
        edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7),
                 (0, 4), (1, 5), (2, 6), (3, 7)]
        for a, b in edges:
            ax.plot([flat[a][0], flat[b][0]], [flat[a][1], flat[b][1]], color=edge, lw=lw,
                    ls=ls, zorder=z + 1)
    return flat


def _axes3(ax: Axes, origin: NDArray[np.float64], rot: NDArray[np.float64], length: float,
           names: tuple[str, str, str] = ('x', 'y', 'z'), z: int = 8) -> None:
    o = _oblique(origin)
    for k, color in enumerate((AXIS_X, AXIS_Y, AXIS_Z)):
        tip = _oblique(origin + rot[:, k] * length)
        _arrow(ax, o, tip, color=color, lw=2.2, z=z)
        dx, dy = tip[0] - o[0], tip[1] - o[1]
        norm = math.hypot(dx, dy)
        _label(ax, tip[0] + 0.25 * dx / norm, tip[1] + 0.25 * dy / norm, names[k],
               size=10, color=color, weight='bold')


def pose_is_six_numbers() -> None:
    """The camera's axes, a box somewhere in front of it, and the six numbers linking them."""
    fig, ax = plt.subplots(figsize=(9.6, 5.6), facecolor='white')
    _axes(ax, (-1.4, 8.4), (-1.4, 4.4))
    cam = np.array([0.0, 0.0, 0.0])
    _camera(ax, -0.55, 0.0, facing=0.0, size=0.7)
    _axes3(ax, cam, np.eye(3), 1.3)
    _label(ax, -0.6, -0.8, 'camera', size=10, color=INK)

    rot = _rot_z(-35.0) @ _rot_x(20.0)
    centre = np.array([5.0, 2.5, 1.3])
    _cuboid(ax, centre, (1.6, 1.2, 1.8), rot, face='#f6c89c')
    _axes3(ax, centre, rot, 1.35, names=("x'", "y'", "z'"))

    c = _oblique(centre)
    ax.plot([0.0, c[0]], [0.0, c[1]], color=INK, lw=1.4, ls=(0, (5, 3)), zorder=2)
    _label(ax, 2.2, 1.85, 'where it is:\n3 numbers (x, y, z)', size=10.5, color=INK,
           ha='center')
    _label(ax, 7.9, 3.9, 'which way it is turned:\n3 numbers (three turns)', size=10.5,
           color=INK, ha='right')
    _label(ax, 3.5, -1.1, 'Position (3) + rotation (3) = the 6 numbers of a 6D pose',
           size=11, color=INK, weight='bold')
    _save(fig, POSE_DOC, 'pose-is-six-numbers.svg')


def render_and_compare() -> None:
    """Three rounds of guess, draw, compare: the dashed guess moves onto the real box."""
    fig, axes = _panels(3, (12.0, 3.9))
    true_rot = _rot_z(-35.0)
    true_c = np.array([2.2, 1.0, 1.2])
    guesses = [(_rot_z(20.0) @ _rot_x(25.0), np.array([1.0, 0.4, 1.6]), 'big difference'),
               (_rot_z(-15.0) @ _rot_x(8.0), np.array([1.8, 0.8, 1.35]),
                'smaller difference'),
               (_rot_z(-33.0), np.array([2.17, 0.98, 1.2]), 'almost none: stop')]
    for k, (ax, (g_rot, g_c, verdict)) in enumerate(zip(axes, guesses)):
        _axes(ax, (-0.8, 4.4), (-0.9, 3.5))
        _frame(ax, -0.7, -0.35, 5.0, 3.5)
        _cuboid(ax, true_c, (1.2, 0.8, 1.8), true_rot, face='#f6c89c', edge=MUTED)
        _cuboid(ax, g_c, (1.2, 0.8, 1.8), g_rot, edge=LINK, lw=2.0, ls=(0, (4, 2)),
                fill=False, z=6)
        _title(ax, 1.8, 3.3, f'Guess {k + 1}')
        _caption(ax, 1.8, -0.5, verdict, size=10.5)
    axes[0].plot([], [], color='#f6c89c', lw=6, label='the real box in the photo')
    axes[0].plot([], [], color=LINK, lw=2, ls=(0, (4, 2)),
                 label='the 3D model drawn at the guessed pose')
    fig.legend(loc='lower center', ncol=2, frameon=False, fontsize=10.5,
               bbox_to_anchor=(0.5, 0.1))
    _save(fig, POSE_DOC, 'render-and-compare.svg')


# --------------------------------------------------------------------------
# 06_depth-from-pictures
# --------------------------------------------------------------------------

DEPTH_DOC: str = 'depth-from-pictures'

ROWS: int = 60
COLS: int = 80


def _scene_masks(glass: bool = False) -> dict[str, NDArray[np.bool_]]:
    """Pixel masks for a small scene: a wall, a table, a box at the back and a mug in front."""
    r, c = np.mgrid[0:ROWS, 0:COLS]
    table = r >= 30
    box = (r >= 12) & (r < 38) & (c >= 44) & (c < 66)
    mug_body = (r >= 30) & (r < 52) & (c >= 14) & (c < 30)
    handle = (((r - 40) ** 2 / 36 + (c - 30) ** 2 / 25) <= 1.0) & (c >= 30) & \
        (((r - 40) ** 2 / 12 + (c - 30) ** 2 / 8) > 1.0)
    masks = {'table': table, 'box': box, 'mug': mug_body | handle}
    if glass:
        masks['glass'] = (r >= 26) & (r < 50) & (c >= 34) & (c < 44)
    return masks


def _scene_depth(masks: dict[str, NDArray[np.bool_]]) -> NDArray[np.float64]:
    """Distance from the camera, in made-up units: small numbers are near."""
    r, _c = np.mgrid[0:ROWS, 0:COLS]
    depth = np.full((ROWS, COLS), 3.0)
    # The table top gets nearer towards the bottom of the picture.
    depth[masks['table']] = 3.0 - (r[masks['table']] - 30) / 30 * 2.2
    depth[masks['box']] = 2.1
    depth[masks['mug']] = 1.2
    if 'glass' in masks:
        depth[masks['glass']] = 1.6
    return depth


def _scene_rgb(masks: dict[str, NDArray[np.bool_]]) -> NDArray[np.float64]:
    def rgb(hex_color: str) -> NDArray[np.float64]:
        return np.array([int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    img = np.zeros((ROWS, COLS, 3))
    img[:] = rgb('#eeeeee')
    img[masks['table']] = rgb(TABLE)
    img[masks['box']] = rgb(WRIST)
    img[masks['mug']] = rgb(GRIP)
    if 'glass' in masks:
        img[masks['glass']] = rgb('#dff0f5')
    return img


def photo_to_depth_map() -> None:
    """A photo of a mug and a box, and the depth map a model makes: one distance per pixel."""
    fig, (left, right) = _panels(2, (11.0, 4.9))
    masks = _scene_masks()
    left.imshow(_scene_rgb(masks), interpolation='nearest')
    depth = _scene_depth(masks)
    im = right.imshow(depth, cmap='gray_r', vmin=0.6, vmax=3.2, interpolation='nearest')
    for ax, title in ((left, 'What goes in: one ordinary photo'),
                      (right, 'What comes out: a depth map')):
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=12, weight='bold', color=INK)
    # A few pixels picked out to show that each one holds a distance.
    for (rr, cc) in ((40, 20), (22, 55), (8, 8)):
        right.add_patch(Rectangle((cc - 0.5, rr - 0.5), 1, 1, facecolor='none',
                                  edgecolor=AXIS_X, lw=2.0))
    right.annotate('mug pixel: near', xy=(20, 40), xytext=(5, 57), color=AXIS_X,
                   fontsize=10, arrowprops={'arrowstyle': '-', 'color': AXIS_X, 'lw': 1})
    right.annotate('box pixel: further', xy=(55, 22), xytext=(50, 5), color=AXIS_X,
                   fontsize=10, arrowprops={'arrowstyle': '-', 'color': AXIS_X, 'lw': 1})
    right.annotate('wall pixel: far', xy=(8, 8), xytext=(14, 5), color=AXIS_X,
                   fontsize=10, arrowprops={'arrowstyle': '-', 'color': AXIS_X, 'lw': 1})
    bar = fig.colorbar(im, ax=right, fraction=0.035, pad=0.03, ticks=[0.8, 3.0])
    bar.ax.set_yticklabels(['near', 'far'])
    bar.outline.set_visible(False)
    _save(fig, DEPTH_DOC, 'photo-to-depth-map.svg')


def relative_vs_metric() -> None:
    """One relative answer (order only) fits a doll's house and a real kitchen equally well."""
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _axes(ax, (-3.2, 11.0), (-4.6, 2.4))
    items = (('mug', GRIP, 0.2), ('box', WRIST, 0.6), ('wall', MUTED, 1.0))

    def ruler(y: float, title: str, values: list[str], unit_line: bool) -> None:
        ax.plot([0, 10], [y, y], color=INK if unit_line else GRID, lw=2, zorder=2)
        _label(ax, -0.3, y, title, size=10.5, ha='right')
        for (name, color, rel), text in zip(items, values):
            x = rel * 10
            ax.plot([x], [y], 'o', ms=13, color=color, mec=INK, zorder=4)
            _label(ax, x, y - 0.5, text, size=10, color=INK)

    ruler(1.2, 'relative model says', ['mug 0.2', 'box 0.6', 'wall 1.0'], False)
    _label(ax, 5.0, 2.1, 'Only the order is known: the mug is nearest, the wall is furthest.',
           size=10.5, color=MUTED)
    ruler(-1.0, "if it is a doll's house", ['0.10 m', '0.20 m', '0.30 m'], True)
    ruler(-3.2, 'if it is a real kitchen', ['0.60 m', '1.20 m', '1.80 m'], True)
    for _name, _color, rel in items:
        x = rel * 10
        ax.plot([x, x], [0.55, -0.7], color=GRID, lw=1, ls=':', zorder=1)
        ax.plot([x, x], [-1.55, -2.9], color=GRID, lw=1, ls=':', zorder=1)
    _label(ax, 5.0, -4.3, 'Both fit the same relative answer. A metric model has to pick one.',
           size=10.5, color=INK, weight='bold')
    _save(fig, DEPTH_DOC, 'relative-vs-metric.svg')


def two_cameras_disparity() -> None:
    """Seen from above: two cameras side by side. A near mug shifts a lot between them."""
    fig = plt.figure(figsize=(11.0, 5.6), facecolor='white')
    top = fig.add_axes((0.0, 0.0, 0.48, 1.0))
    bot = fig.add_axes((0.52, 0.0, 0.48, 1.0))
    _axes(top, (-3.2, 3.2), (-1.3, 6.2))
    left_cam, right_cam = (-0.8, 0.0), (0.8, 0.0)
    mug, box = (0.0, 2.0), (0.4, 5.0)
    for cam in (left_cam, right_cam):
        _camera(top, cam[0], cam[1], facing=90.0, size=0.5)
        for target, color in ((mug, GRIP), (box, WRIST)):
            top.plot([cam[0], target[0]], [cam[1] + 0.35, target[1]], color=color, lw=1.0,
                     ls=(0, (4, 3)), zorder=2)
    top.add_patch(Circle(mug, 0.35, facecolor=GRIP, edgecolor=INK, zorder=4))
    top.add_patch(Rectangle((box[0] - 0.55, box[1] - 0.35), 1.1, 0.7, facecolor=WRIST,
                            edgecolor=INK, zorder=4))
    _label(top, mug[0] + 0.6, mug[1], 'mug (near)', ha='left')
    _label(top, box[0] + 0.75, box[1], 'box (far)', ha='left')
    _label(top, 0.0, -0.8, 'two cameras a known distance apart', size=10, color=MUTED)
    _title(top, 0.0, 5.95, 'Seen from above')

    _axes(bot, (-0.3, 6.3), (-1.3, 6.2))
    _title(bot, 3.0, 5.95, 'The two pictures')
    # Each object's place in a picture follows its angle from that camera (see the top view).
    for row, (name, mug_x, box_x) in enumerate((('left picture', 3.76, 3.47),
                                                ('right picture', 2.24, 2.84))):
        y0 = 3.2 - row * 3.0
        _frame(bot, 0.0, y0, 6.0, 2.2)
        _label(bot, 0.1, y0 + 2.45, name, ha='left', size=10, color=MUTED)
        _box2d(bot, box_x, y0 + 1.15, 0.6, 0.45)
        _mug(bot, mug_x, y0 + 0.2, w=0.6, h=0.75, z=4)
    # Dotted guides that show how far each object moved between the two pictures.
    for x0, x1, y, color, text in ((3.76, 2.24, -0.35, GRIP, 'mug shifts a lot'),
                                   (3.47, 2.84, -0.85, WRIST, 'box shifts a little')):
        bot.plot([x0, x0], [y, 3.4], color=color, lw=0.8, ls=':', zorder=1)
        _arrow(bot, (x0, y), (x1, y), color=color, lw=1.8)
        _label(bot, 4.1, y, text, ha='left', size=10, color=color)
    _save(fig, DEPTH_DOC, 'two-cameras-disparity.svg')


def glass_depth_hole() -> None:
    """A depth camera gets no reading on a clear glass; a completion model fills the hole."""
    fig, axes = _panels(3, (13.0, 4.4))
    masks = _scene_masks(glass=True)
    true_depth = _scene_depth(masks)
    raw = true_depth.copy()
    raw[masks['glass']] = np.nan
    # Light passes through the glass, so its top part reads as the wall and table behind.
    behind = _scene_depth(_scene_masks(glass=False))
    rows = np.mgrid[0:ROWS, 0:COLS][0]
    through = masks['glass'] & (rows < 34)
    raw[through] = behind[through]
    cmap = plt.get_cmap('gray_r').copy()
    cmap.set_bad(AXIS_X)
    axes[0].imshow(_scene_rgb(masks), interpolation='nearest')
    axes[1].imshow(np.ma.masked_invalid(raw), cmap=cmap, vmin=0.6, vmax=3.2,
                   interpolation='nearest')
    axes[2].imshow(true_depth, cmap='gray_r', vmin=0.6, vmax=3.2, interpolation='nearest')
    titles = ('Photo: a mug and a clear glass', 'Depth camera: a hole (red)',
              'After depth completion')
    captions = ('The glass is almost invisible.', 'No reading on most of the glass. Its top\n'
                'reads as the wall and table behind it.', 'The model fills in the glass\n'
                'at a sensible distance.')
    for ax, title, cap in zip(axes, titles, captions):
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=11.5, weight='bold', color=INK)
        ax.set_xlabel(cap, fontsize=10, color=MUTED)
    axes[0].add_patch(Rectangle((33.5, 25.5), 10, 24, facecolor='none', edgecolor=LINK,
                                lw=1.2))
    _save(fig, DEPTH_DOC, 'glass-depth-hole.svg')


# --------------------------------------------------------------------------
# 07_open-vocabulary-models
# --------------------------------------------------------------------------

OPEN_DOC: str = 'open-vocabulary-models'


def _banana(ax: Axes, x: float, y: float, s: float = 1.0, z: int = 3) -> None:
    ax.add_patch(Arc((x, y + 0.9 * s), 1.6 * s, 1.6 * s, theta1=200, theta2=340,
                     color=JOINT, lw=9 * s, zorder=z))


def _sponge(ax: Axes, x: float, y: float, s: float = 1.0, z: int = 3) -> None:
    ax.add_patch(Rectangle((x - 0.55 * s, y), 1.1 * s, 0.35 * s, facecolor=JOINT,
                           edgecolor=INK, lw=0.8, zorder=z))
    ax.add_patch(Rectangle((x - 0.55 * s, y + 0.35 * s), 1.1 * s, 0.18 * s,
                           facecolor=SLIDE, edgecolor=INK, lw=0.8, zorder=z))


def _bowl(ax: Axes, x: float, y: float, s: float = 1.0, z: int = 3) -> None:
    ax.add_patch(Polygon([(x - 0.7 * s, y + 0.5 * s), (x + 0.7 * s, y + 0.5 * s),
                          (x + 0.4 * s, y), (x - 0.4 * s, y)], closed=True,
                         facecolor='#f2f2f2', edgecolor=INK, lw=1.0, zorder=z))


def words_and_pictures_matched() -> None:
    """CLIP-style scoring: three pictures against three sentences. Darker means a closer match."""
    fig, ax = plt.subplots(figsize=(9.6, 6.4), facecolor='white')
    _axes(ax, (-3.0, 7.0), (-1.7, 5.8))
    captions = ('"a photo of\na mug"', '"a photo of\na banana"', '"a photo of\na sponge"')
    draw = (lambda x, y: _mug(ax, x, y - 0.45, w=0.7, h=0.85),
            lambda x, y: _banana(ax, x, y - 0.35, s=0.8),
            lambda x, y: _sponge(ax, x, y - 0.3, s=0.9))
    # Hand-set shades, not model output: the matching pair is dark, the rest pale.
    shade = np.array([[0.9, 0.15, 0.2], [0.1, 0.9, 0.25], [0.2, 0.2, 0.85]])
    cell: float = 1.6
    for j, text in enumerate(captions):
        _label(ax, 0.8 + j * cell + cell / 2, 4.6, text, size=10)
    for i in range(3):
        y = 3.2 - i * cell
        ax.add_patch(Rectangle((-1.9, y - cell / 2 + 0.1), 1.4, cell - 0.2, facecolor='white',
                               edgecolor=MUTED, lw=1.0, zorder=1))
        draw[i](-1.2, y)
        for j in range(3):
            v = shade[i, j]
            ax.add_patch(Rectangle((0.8 + j * cell, y - cell / 2), cell, cell,
                                   facecolor=plt.get_cmap('Blues')(0.1 + 0.8 * v),
                                   edgecolor='white', lw=2, zorder=2))
            if i == j:
                _label(ax, 0.8 + j * cell + cell / 2, y, 'match', size=10, color='white',
                       weight='bold')
    _label(ax, -1.2, 4.6, 'pictures', size=10, color=MUTED)
    _label(ax, 3.2, 5.5, 'sentences', size=10, color=MUTED)
    _label(ax, 3.2, -1.3, 'Darker square = the picture and the sentence are a closer match.',
           size=10.5, color=INK)
    _save(fig, OPEN_DOC, 'words-and-pictures-matched.svg')


def _table_scene(ax: Axes) -> dict[str, tuple[float, float, float, float]]:
    """A table with a red mug, a blue mug, a bowl and a banana. Returns each object's box."""
    _axes(ax, (-0.3, 8.3), (-1.4, 4.5))
    _frame(ax, -0.2, -0.6, 8.4, 4.0)
    _table(ax, -0.2, 8.2, 0.4, depth=1.0)
    _mug(ax, 1.3, 0.2, w=0.9, h=1.1, color=GRIP)
    _mug(ax, 3.4, 0.2, w=0.9, h=1.1, color=LINK)
    _bowl(ax, 5.3, 0.2, s=1.0)
    _banana(ax, 7.0, 0.1, s=0.75)
    return {'red mug': (0.7, 0.05, 1.6, 1.45), 'blue mug': (2.8, 0.05, 1.6, 1.45),
            'bowl': (4.45, 0.05, 1.7, 0.8), 'banana': (6.25, 0.05, 1.5, 0.75)}


def text_prompt_to_box() -> None:
    """The same photo, two different sentences, two different boxes."""
    fig, axes = _panels(2, (12.6, 4.4))
    for ax, prompt, colour in ((axes[0], 'blue mug', AXIS_Z), (axes[1], 'banana', SLIDE)):
        boxes = _table_scene(ax)
        x, y, w, h = boxes[prompt]
        ax.add_patch(Rectangle((x, y), w, h, facecolor='none', edgecolor=colour, lw=2.5,
                               zorder=8))
        _label(ax, x + 0.05, y + h + 0.2, prompt, size=10, color='white', ha='left',
               weight='bold')
        ax.texts[-1].set_bbox({'facecolor': colour, 'edgecolor': 'none', 'pad': 2})
        ax.add_patch(FancyBboxPatch((1.8, 3.55), 4.4, 0.6, boxstyle='round,pad=0.1',
                                    facecolor='white', edgecolor=INK, lw=1.2, zorder=8))
        _label(ax, 4.0, 3.85, f'words typed in: "{prompt}"', size=11)
        _caption(ax, 4.0, -0.8, 'Box drawn only around what the words describe.')
    _save(fig, OPEN_DOC, 'text-prompt-to-box.svg')


def click_to_mask() -> None:
    """One click on a mug handle, and the three outlines a segment-anything model offers."""
    fig, axes = _panels(4, (13.4, 4.0))
    click = (2.05, 1.04)
    titles = ('One click', 'Answer 1: the handle', 'Answer 2: the mug',
              'Answer 3: mug and saucer')
    for k, (ax, title) in enumerate(zip(axes, titles)):
        _axes(ax, (-1.0, 3.2), (-0.9, 3.2))
        _frame(ax, -0.9, -0.5, 4.0, 3.4)
        ax.add_patch(Ellipse((1.0, 0.0), 2.6, 0.45, facecolor='#f2f2f2', edgecolor=INK,
                             lw=1.0, zorder=2))
        _mug(ax, 1.0, 0.1, w=1.3, h=1.8, color=GRIP if k == 0 else '#f0b9b9',
             edge=INK, z=3)
        _title(ax, 1.1, 3.05, title, size=11)
        if k == 0:
            ax.plot([click[0]], [click[1]], marker='*', ms=20, color=JOINT, mec=INK,
                    zorder=9)
            _caption(ax, 1.1, -0.6, 'The yellow star is the click.')
            continue
        if k == 1:
            ax.add_patch(Arc((1.65, 1.04), 0.81, 0.99, theta1=-90, theta2=90,
                             color=AXIS_Z, lw=10, alpha=0.55, zorder=6))
        if k == 2:
            ax.add_patch(Rectangle((0.35, 0.1), 1.3, 1.8, facecolor=AXIS_Z, alpha=0.45,
                                   edgecolor=AXIS_Z, lw=2, zorder=6))
            ax.add_patch(Arc((1.65, 1.04), 0.81, 0.99, theta1=-90, theta2=90,
                             color=AXIS_Z, lw=10, alpha=0.55, zorder=6))
        if k == 3:
            ax.add_patch(Ellipse((1.0, 0.0), 2.6, 0.45, facecolor=AXIS_Z, alpha=0.45,
                                 edgecolor=AXIS_Z, lw=2, zorder=6))
            ax.add_patch(Rectangle((0.35, 0.1), 1.3, 1.8, facecolor=AXIS_Z, alpha=0.45,
                                   edgecolor=AXIS_Z, lw=2, zorder=6))
            ax.add_patch(Arc((1.65, 1.04), 0.81, 0.99, theta1=-90, theta2=90,
                             color=AXIS_Z, lw=10, alpha=0.55, zorder=6))
        ax.plot([click[0]], [click[1]], marker='*', ms=14, color=JOINT, mec=INK, zorder=9)
        _caption(ax, 1.1, -0.6, 'Blue = the outline offered.')
    _save(fig, OPEN_DOC, 'click-to-mask.svg')


# --------------------------------------------------------------------------
# 08_tracking-and-motion
# --------------------------------------------------------------------------

TRACK_DOC: str = 'tracking-and-motion'


def optical_flow_arrows() -> None:
    """Two frames where only the box moves, and the flow: an arrow on each moving pixel."""
    fig, axes = _panels(3, (13.0, 4.2))
    box_before = (1.2, 0.6)
    box_after = (2.4, 1.0)
    for k, ax in enumerate(axes):
        _axes(ax, (-0.3, 6.3), (-0.9, 4.3))
        _frame(ax, -0.2, -0.2, 6.4, 4.2)
    _box2d(axes[0], box_before[0] + 0.8, box_before[1], 1.6, 1.2)
    _mug(axes[0], 5.0, 0.3, w=0.8, h=1.0, color=LINK)
    _title(axes[0], 3.0, 4.2, 'Frame 1')
    _box2d(axes[1], box_after[0] + 0.8, box_after[1], 1.6, 1.2)
    _mug(axes[1], 5.0, 0.3, w=0.8, h=1.0, color=LINK)
    _title(axes[1], 3.0, 4.2, 'Frame 2, a moment later')
    _caption(axes[1], 3.0, -0.35, 'The box slid right and up.\nThe mug stayed still.')

    ax = axes[2]
    _title(ax, 3.0, 4.2, 'Optical flow')
    dx, dy = box_after[0] - box_before[0], box_after[1] - box_before[1]
    for gx in np.arange(0.2, 6.2, 0.5):
        for gy in np.arange(0.1, 3.9, 0.5):
            on_box = (box_before[0] <= gx <= box_before[0] + 1.6 and
                      box_before[1] <= gy <= box_before[1] + 1.4)
            if on_box:
                _arrow(ax, (gx, gy), (gx + dx * 0.8, gy + dy * 0.8), color=WRIST, lw=1.4)
            else:
                ax.plot([gx], [gy], '.', color=GRID, ms=4)
    _caption(ax, 3.0, -0.35, 'An arrow on every pixel that moved.\nA dot means "did not move".')
    _save(fig, TRACK_DOC, 'optical-flow-arrows.svg')


def tracked_points_through_frames() -> None:
    """Three points on a mug followed through four frames while a gripper lifts and turns it."""
    fig, axes = _panels(4, (13.4, 4.4))
    colors = (AXIS_X, SLIDE, AXIS_Z)
    history: list[list[tuple[float, float]]] = [[], [], []]
    poses = ((1.5, 0.3, 0.0), (1.8, 0.9, 10.0), (2.1, 1.5, 20.0), (2.4, 2.0, 30.0))
    for k, (ax, (mx, my, turn)) in enumerate(zip(axes, poses)):
        _axes(ax, (-0.4, 4.2), (-0.9, 4.8))
        _frame(ax, -0.3, -0.2, 4.4, 4.4)
        # The mug is drawn as a tilted body so that the three points turn with it.
        c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))

        def at(u: float, v: float, mx: float = mx, my: float = my, c: float = c,
               s: float = s) -> tuple[float, float]:
            return (mx + u * c - v * s, my + u * s + v * c)
        body = [at(-0.5, 0.0), at(0.5, 0.0), at(0.5, 1.2), at(-0.5, 1.2)]
        ax.add_patch(Polygon(body, closed=True, facecolor='#f0b9b9', edgecolor=INK,
                             zorder=3))
        # The gripper fingers hold the mug from the right side.
        f1 = [at(0.5, 0.35), at(1.2, 0.35)]
        f2 = [at(0.5, 0.85), at(1.2, 0.85)]
        for f in (f1, f2):
            ax.plot([f[0][0], f[1][0]], [f[0][1], f[1][1]], color=MUTED, lw=6,
                    solid_capstyle='butt', zorder=6)
        pts = [at(-0.3, 1.0), at(0.3, 0.6), at(0.45, 0.25)]
        hidden = [False, False, k >= 2]
        for i, (p, col) in enumerate(zip(pts, colors)):
            history[i].append(p)
            xs = [q[0] for q in history[i]]
            ys = [q[1] for q in history[i]]
            ax.plot(xs, ys, color=col, lw=1.2, ls=':', zorder=7)
            if hidden[i]:
                ax.plot([p[0]], [p[1]], 'o', ms=10, mfc='white', mec=col, mew=2, zorder=8)
            else:
                ax.plot([p[0]], [p[1]], 'o', ms=10, color=col, mec=INK, zorder=8)
        _title(ax, 1.9, 4.55, f'Frame {k + 1}', size=11)
    _caption(axes[2], 1.9, -0.35, 'Hollow circle: the point is behind\n'
             'the finger. Its place is still guessed.', size=9.5)
    _caption(axes[0], 1.9, -0.35, 'Three points picked on\nthe mug in frame 1.', size=9.5)
    _caption(axes[3], 1.9, -0.35, 'Dotted lines: the path of\neach point so far.', size=9.5)
    _save(fig, TRACK_DOC, 'tracked-points-through-frames.svg')


def same_id_across_frames() -> None:
    """Two identical mugs. One goes behind a box and comes out; the tracker keeps its number."""
    fig, axes = _panels(3, (12.6, 4.2))
    mug1 = ((1.2, 0.3), (3.1, 0.3), (4.6, 0.3))
    mug2 = (5.8, 0.3)
    for k, ax in enumerate(axes):
        _axes(ax, (-0.3, 7.2), (-1.0, 4.1))
        _frame(ax, -0.2, -0.3, 7.3, 3.7)
        _table(ax, -0.2, 7.1, 0.3, depth=0.6)
        hidden = k == 1
        if not hidden:
            _mug(ax, mug1[k][0], mug1[k][1], w=0.8, h=1.0, color=LINK, z=3)
        _box2d(ax, 3.2, 0.3, 1.5, 1.6, z=5)
        mx2 = mug2[0] if k < 2 else 6.1
        _mug(ax, mx2, mug2[1], w=0.8, h=1.0, color=LINK, z=3)
        tag_boxes = [] if hidden else [(mug1[k], '#1', GRIP)]
        tag_boxes.append(((mx2, mug2[1]), '#2', SLIDE))
        for (x, y), tag, col in tag_boxes:
            ax.add_patch(Rectangle((x - 0.55, y - 0.1), 1.25, 1.25, facecolor='none',
                                   edgecolor=col, lw=2, zorder=7))
            _label(ax, x - 0.5, y + 1.35, tag, size=10.5, color='white', weight='bold',
                   ha='left')
            ax.texts[-1].set_bbox({'facecolor': col, 'edgecolor': 'none', 'pad': 1.5})
        if hidden:
            ax.add_patch(Rectangle((2.55, 0.2), 1.25, 1.25, facecolor='none',
                                   edgecolor=GRIP, lw=2, ls=(0, (4, 3)), zorder=7))
            _label(ax, 3.2, 2.55, '#1 hidden: its place is predicted', size=9.5,
                   color=GRIP)
        _title(ax, 3.45, 3.8, f'Frame {k + 1}', size=11)
    _caption(axes[2], 3.45, -0.45, 'It comes out as #1 again, not as a new mug.')
    _caption(axes[0], 3.45, -0.45, 'Two mugs that look the same.')
    _caption(axes[1], 3.45, -0.45, 'Mug #1 is behind the box.')
    _save(fig, TRACK_DOC, 'same-id-across-frames.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    keypoints_on_a_mug()
    pose_is_six_numbers()
    render_and_compare()
    photo_to_depth_map()
    relative_vs_metric()
    two_cameras_disparity()
    glass_depth_hole()
    words_and_pictures_matched()
    text_prompt_to_box()
    click_to_mask()
    optical_flow_arrows()
    tracked_points_through_frames()
    same_id_across_frames()


if __name__ == '__main__':
    main()
