"""Generate the diagrams used in docs/camera/overview.md.

Images go to docs/images/<area>/, matching the docs/<area>/ folder that uses
them.

Run with:  pixi run python docs/diagrams/camera.py

Unlike the other areas' figures, the photographs here are not drawn by hand.
They are taken by the camera in ``camera_basics/camera.py``, on the scene that
module defines, through the configurations it declares. So if you change the
field of view, the resolution or the scene, regenerate rather than editing the
SVGs — the pictures and the numbers beside them come from the code itself.
"""

import math
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
# The photographs below are taken by the camera this area documents, rather than
# drawn by hand, so the package has to be importable. It has no ROS imports in
# it, which is what makes that possible from a plain `python docs/...` run.
sys.path.insert(0, str(REPO_ROOT / 'src' / 'camera_basics'))

from camera_basics.camera import (  # noqa: E402  (must follow the sys.path line)
    CameraConfig,
    capture,
    CONFIGS,
    ONE_BOX_SCENE,
    TABLE_SCENE,
    TOP_DOWN,
    WRIST,
)
from camera_basics.problems.one_box import SAMPLE_PIXEL  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.patches import Arc, Circle, Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

AREA = 'camera'
OUT_DIR = REPO_ROOT / 'docs' / 'images' / AREA

#: Height the reference camera sits at, in metres. Matches ``TOP_DOWN``.
CAMERA_HEIGHT_M = TOP_DOWN.position[2]

GRID = '#d6d6d6'
AXIS_X = '#d1495b'
AXIS_Y = '#2a9d3f'
AXIS_Z = '#1a99ff'
INK = '#222222'
MUTED = '#777777'
PAPER = '#f4f4f4'
LENS = '#3d5a80'


def _new_axes(size=(6.0, 6.0), xlim=(-3.2, 3.2), ylim=(-3.2, 3.2)):
    fig, ax = plt.subplots(figsize=size, facecolor='white')
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _save(fig, name):
    fig.savefig(OUT_DIR / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {OUT_DIR / name}')


def _title(ax, text, y=None, subtitle=None):
    ax.set_title(text, fontsize=12, color=INK, weight='bold', pad=10)
    if subtitle is not None:
        ax.text(0.5, y, subtitle, transform=ax.transAxes, fontsize=9,
                ha='center', color=MUTED)


def _rgb_array(shot):
    """Return the colour picture as an array matplotlib can show."""
    return np.array(shot.rgb, dtype=np.uint8)


def _depth_array(shot):
    """Return the depth picture as an array, with missing readings as NaN."""
    return np.array(
        [[np.nan if d is None else d for d in row] for row in shot.depth],
        dtype=float,
    )


def _show_picture(ax, image, title, cmap=None, vmin=None, vmax=None):
    ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='nearest')
    ax.set_title(title, fontsize=10, color=INK, pad=6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(GRID)
    return ax


def pinhole():
    """Draw the projection idea: three points at one ratio share one pixel."""
    fig, ax = _new_axes(size=(7.4, 4.4), xlim=(-0.9, 5.2), ylim=(-1.95, 1.75))

    # The optical axis runs to the right; the picture is the vertical line.
    ax.annotate('', xy=(4.8, 0), xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.0, 'ls': ':'})
    ax.text(4.85, 0.0, '+Z\nforward', fontsize=9, color=MUTED, va='center')

    plane_z = 1.25
    ax.plot([plane_z, plane_z], [-1.15, 1.15], color=INK, lw=2.0, zorder=3)
    ax.text(plane_z, -1.32, 'the picture', fontsize=9, ha='center', color=INK)

    # One ray. Every point on it has the same x/z, so it is the same pixel.
    slope = 0.28
    ax.plot([0, 4.6], [0, -slope * 4.6], color=AXIS_X, lw=1.6, zorder=2)

    for z_pos, label in ((1.9, 'near'), (3.1, 'further'), (4.3, 'further still')):
        ax.add_patch(Circle((z_pos, -slope * z_pos), 0.075, color=AXIS_X, zorder=4))
        ax.text(z_pos, -slope * z_pos - 0.26, label, fontsize=9, ha='center', color=INK)

    pixel_y = -slope * plane_z
    ax.add_patch(Circle((plane_z, pixel_y), 0.09, color=INK, zorder=5))
    ax.text(plane_z - 0.12, pixel_y - 0.02, 'one pixel  ', fontsize=9, ha='right',
            va='center', color=INK, family='monospace')

    # The lens, and the two lengths the intrinsics are made of.
    ax.add_patch(Circle((0, 0), 0.1, color=LENS, zorder=5))
    ax.text(-0.12, 0.02, 'lens  ', fontsize=9, ha='right', va='center', color=LENS)

    ax.annotate('', xy=(plane_z, 0.75), xytext=(0, 0.75),
                arrowprops={'arrowstyle': '<|-|>', 'color': AXIS_Y, 'lw': 1.3})
    ax.text(plane_z / 2, 0.85, 'fx', fontsize=10, ha='center', color=AXIS_Y,
            family='monospace')
    ax.text(plane_z + 0.2, 0.85, '(focal length, in pixels)', fontsize=9,
            ha='left', color=AXIS_Y)

    ax.annotate('', xy=(plane_z, pixel_y), xytext=(plane_z, 0),
                arrowprops={'arrowstyle': '<|-|>', 'color': AXIS_Z, 'lw': 1.3})
    ax.text(plane_z + 0.14, pixel_y / 2, 'u - cx', fontsize=9, color=AXIS_Z,
            va='center', family='monospace')

    ax.text(2.15, 1.5, 'A pixel is a direction, not a place',
            fontsize=13, ha='center', color=INK, weight='bold')
    ax.text(2.15, -1.78, 'u = fx · (x / z) + cx',
            fontsize=10, ha='center', color=INK, family='monospace')
    ax.text(2.15, -1.94, 'three points, one ratio, one pixel — dividing by z is '
            'where the third dimension goes',
            fontsize=9, ha='center', color=MUTED)

    _save(fig, 'pinhole.svg')


def field_of_view():
    """Draw what each lens can see of the table from the same height."""
    fig, ax = _new_axes(size=(7.4, 4.4), xlim=(-0.48, 0.48), ylim=(-0.06, 0.50))
    ax.set_aspect('auto')

    # The table, edge on.
    ax.plot([-0.46, 0.46], [0, 0], color=INK, lw=2.0, zorder=3)
    for tick in np.arange(-0.45, 0.46, 0.05):
        ax.plot([tick, tick], [0, -0.012], color=GRID, lw=1.0, zorder=2)
    ax.text(-0.465, -0.032, 'the table', fontsize=9, ha='left', color=MUTED)

    eye = (0.0, CAMERA_HEIGHT_M)
    ax.add_patch(Circle(eye, 0.011, color=LENS, zorder=6))
    ax.text(0.015, CAMERA_HEIGHT_M, f'  camera, {CAMERA_HEIGHT_M:g} m up',
            fontsize=9, va='center', color=LENS)

    styles = (('wide', AXIS_Y, 0.30), ('wrist', AXIS_X, 0.55), ('narrow', AXIS_Z, 0.85))
    for name, colour, alpha in styles:
        config = CONFIGS[name]
        half = math.tan(math.radians(config.hfov_deg) / 2.0) * CAMERA_HEIGHT_M
        ax.fill([eye[0], -half, half], [eye[1], 0, 0], color=colour, alpha=0.12, zorder=1)
        for sign in (-1, 1):
            ax.plot([eye[0], sign * half], [eye[1], 0], color=colour, lw=1.4,
                    alpha=alpha, zorder=4)
        width_m, _ = config.coverage_m(CAMERA_HEIGHT_M)
        # One row per lens, so the three measurements do not sit on top of
        # each other.
        row = styles.index((name, colour, alpha))
        arrow_y = -0.055 - 0.075 * row
        ax.annotate('', xy=(half, arrow_y), xytext=(-half, arrow_y),
                    arrowprops={'arrowstyle': '<|-|>', 'color': colour, 'lw': 1.2})
        ax.text(0.0, arrow_y - 0.042,
                f'{name}: {config.hfov_deg:g}° → {width_m:.3f} m across, '
                f'{config.metres_per_pixel(CAMERA_HEIGHT_M) * 1000:.2f} mm per pixel',
                fontsize=9, ha='center', va='center', color=colour, family='monospace',
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})

    ax.set_ylim(-0.285, 0.50)
    ax.text(0.0, 0.47, 'Field of view decides how much is in shot',
            fontsize=13, ha='center', color=INK, weight='bold')
    _save(fig, 'field_of_view.svg')


def focal_length(out='focal_length.svg'):
    """Show what focal length is: the gap between lens and sensor, and what it changes."""
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.3), facecolor='white')
    box_z, box_h, sensor_half = -3.0, 0.9, 0.8
    lens_colour, focal_colour, scene_colour = LENS, '#2f6db0', '#b5433a'
    row = -1.12                            # the row the lengths along the axis are drawn on

    def span(ax, start, end, colour):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops={'arrowstyle': '<|-|>', 'color': colour, 'lw': 1.2,
                                'shrinkA': 0, 'shrinkB': 0})

    for ax, (f, name) in zip(axes, ((1.0, 'short focal length: a wide view'),
                                    (2.0, 'twice the focal length: zoomed in'))):
        ax.set_xlim(-4.4, 3.0)
        ax.set_ylim(-2.25, 1.3)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(name, fontsize=11, color=INK, pad=4)

        # Straight ahead, through the middle of the lens and the sensor.
        ax.plot([-3.4, f + 0.3], [0, 0], color=MUTED, lw=0.9, ls=':')

        # What the edges of the sensor can see: the field of view. Cut off above the
        # row of lengths, so the wide view does not run into the labels.
        view = Rectangle((-3.3, -0.95), f + 3.6, 2.2, transform=ax.transData)
        for sign in (-1, 1):
            reach = sensor_half / f * 3.3
            edge, = ax.plot([f, -3.3], [sign * sensor_half, -sign * reach], color=MUTED,
                            lw=0.8, ls=(0, (4, 3)))
            edge.set_clip_path(view)
        shade, = ax.fill([0, -3.3, -3.3], [0, sensor_half / f * 3.3, -sensor_half / f * 3.3],
                         color='#e8eef5', zorder=0)
        shade.set_clip_path(view)
        ax.text(-2.3, -0.3, 'what the sensor\ncan see', fontsize=8.5,
                color=MUTED, ha='center', va='top')

        # The box, and the light from its top corner through the lens.
        ax.add_patch(Rectangle((box_z - 0.12, 0), 0.24, box_h, facecolor='#e6a39c',
                               edgecolor=INK, lw=0.6, zorder=3))
        image_h = box_h * f / -box_z
        ax.plot([box_z, f], [box_h, -image_h], color=AXIS_X, lw=1.4, zorder=2)

        # The sensor, and the picture of the box on it, upside down.
        ax.plot([f, f], [-sensor_half, sensor_half], color=INK, lw=3.0, zorder=4)
        ax.plot([f, f], [0, -image_h], color=AXIS_X, lw=5.0, zorder=5,
                solid_capstyle='butt')
        ax.text(f + 0.12, sensor_half - 0.05, 'sensor', fontsize=9, color=INK, va='top')

        ax.add_patch(Circle((0, 0), 0.09, color=lens_colour, zorder=6))
        ax.text(0, 0.2, 'lens', fontsize=9, color=lens_colour, ha='center')

        # The four lengths the sum below uses. Dotted lines drop each end onto one row.
        for x in (box_z, 0, f):
            ax.plot([x, x], [0 if x else -0.1, row], color=GRID, lw=0.9, ls=':', zorder=1)
        span(ax, (-3.38, 0), (-3.38, box_h), scene_colour)
        ax.text(-3.5, box_h / 2, f'{box_h:g} to\nthe side', fontsize=9, color=scene_colour,
                ha='right', va='center')
        span(ax, (box_z, row), (-0.04, row), scene_colour)
        ax.text(box_z / 2, row - 0.1, f'{-box_z:g} ahead', fontsize=9.5, color=scene_colour,
                ha='center', va='top')
        span(ax, (0.04, row), (f, row), focal_colour)
        ax.text(f + 0.1, row - 0.1, f'focal length = {f:g}', fontsize=9.5,
                color=focal_colour, ha='right' if f > 1.5 else 'left', va='top')
        span(ax, (f + 0.2, 0), (f + 0.2, -image_h), AXIS_X)
        ax.text(f + 0.3, -image_h / 2, f'lands\n{image_h:g} from\nthe middle', fontsize=8.5,
                color=AXIS_X, ha='left', va='center')

        ax.text(-0.7, -1.95, f'{f:g} × {box_h:g} / {-box_z:g} = {image_h:g}', fontsize=10,
                color=INK, ha='center', va='center', family='monospace')

    fig.suptitle('Focal length is the distance from the lens to the sensor', fontsize=13,
                 color=INK, weight='bold', y=1.02)
    fig.text(0.5, 0.0, 'Twice the focal length: the same box lands twice as far from the '
             'middle, so it looks twice as big,\nand the same sensor takes in a narrower '
             'view. Real cameras flip the upside-down picture back.',
             fontsize=9, ha='center', color=MUTED)
    _save(fig, out)


def fx_fy(out='fx_fy.svg'):
    """Put fx, fy, cx and cy on this doc's camera: once seen from above, once from the side."""
    _shot, u, v, _depth, _point = _worked_point()
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.4), facecolor='white')
    focal_colour = '#2f6db0'
    panels = (
        (axes[0], 'Across the picture: fx and cx', WRIST.fx, WRIST.width_px, WRIST.cx,
         u - WRIST.cx, WRIST.hfov_deg, AXIS_X, 'u', 'left edge', 'right edge',
         f'{u - WRIST.cx:g} pixels right\nof the middle'),
        (axes[1], 'Down the picture: fy and cy', WRIST.fy, WRIST.height_px, WRIST.cy,
         v - WRIST.cy, WRIST.vfov_deg, AXIS_Y, 'v', 'top edge', 'bottom edge',
         f'{-(v - WRIST.cy):g} pixels above\nthe middle'),
    )
    for ax, title, f, size, middle, offset, fov, colour, letter, low, high, spot in panels:
        ax.set_xlim(-230, 230)
        ax.set_ylim(-395, 60)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=11.5, color=INK, pad=2)
        half = size / 2

        # The lens, and the picture fx (or fy) pixels in front of it.
        ax.fill([0, -half, half], [0, -f, -f], color='#e8eef5', zorder=0)
        for sign in (-1, 1):
            ax.plot([0, sign * half], [0, -f], color=MUTED, lw=0.9, ls=(0, (4, 3)))
        ax.plot([-half, half], [-f, -f], color=INK, lw=3.0, zorder=3)
        ax.plot([0, 0], [0, -f], color=MUTED, lw=0.9, ls=':')
        ax.add_patch(Circle((0, 0), 7, color=LENS, zorder=6))
        ax.text(0, 14, 'lens', fontsize=9.5, color=LENS, ha='center')

        ax.annotate('', xy=(-half - 22, -f), xytext=(-half - 22, 0),
                    arrowprops={'arrowstyle': '<|-|>', 'color': focal_colour, 'lw': 1.3})
        name = 'fx' if letter == 'u' else 'fy'
        ax.text(-half - 30, -f / 2, f'{name} =\n{f:.1f}\npixels', fontsize=9.5,
                color=focal_colour, ha='right', va='center', family='monospace')

        # The field of view: the angle between the two edges, at the lens.
        ax.add_patch(Arc((0, 0), 110, 110, theta1=270 - fov / 2, theta2=270 + fov / 2,
                         color=MUTED, lw=1.0))
        side = -1 if offset > 0 else 1
        ax.text(side * 24, -80, f'{fov:.1f}°'.replace('.0°', '°'), fontsize=9.5, color=MUTED,
                ha='center', va='center')

        # Pixel numbers along the picture: 0, the middle, and the far edge.
        for pos, label in ((-half, f'{letter} = 0\n{low}'),
                           (0, f'{letter} = {middle:g}\nthe middle\n'
                               f'(c{"x" if letter == "u" else "y"})'),
                           (half, f'{letter} = {size}\n{high}')):
            ax.plot([pos, pos], [-f - 6, -f + 6], color=INK, lw=1.2, zorder=4)
            ax.text(pos, -f - 14, label, fontsize=8.5, color=INK, ha='center', va='top')

        # The spot on the red box, and where its line of sight lands.
        ax.plot([0, offset], [0, -f], color=colour, lw=1.4, zorder=2)
        ax.plot([offset], [-f], marker='o', color=colour, ms=6, zorder=5)
        ax.text(offset + (8 if offset > 0 else -8), -f + 30, spot, fontsize=8.5, color=colour,
                ha='left' if offset > 0 else 'right', va='bottom')

    fig.suptitle('fx and fy: the focal length, counted in pixels', fontsize=13,
                 color=INK, weight='bold', y=0.99)
    fig.text(0.5, 0.02, 'Left: the camera seen from above.   Right: seen from the side.   '
             'The pixels are square, so fx and fy are both 277.1.',
             fontsize=9, ha='center', color=MUTED)
    _save(fig, out)


def scene(world=TABLE_SCENE, out='scene.svg'):
    """Draw the table, the boxes and the camera, from above and from the side."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    plan, side = axes

    # -- from above ------------------------------------------------------
    plan.set_aspect('equal')
    plan.set_xlim(-0.27, 0.27)
    plan.set_ylim(-0.24, 0.24)
    plan.axis('off')
    for tick in np.arange(-0.25, 0.26, 0.05):
        plan.plot([-0.25, 0.25], [tick, tick], color=GRID, lw=0.7, zorder=0)
        plan.plot([tick, tick], [-0.22, 0.22], color=GRID, lw=0.7, zorder=0)

    seen_w, seen_h = WRIST.coverage_m(CAMERA_HEIGHT_M)
    plan.add_patch(Rectangle((-seen_w / 2, -seen_h / 2), seen_w, seen_h, fill=False,
                             ls=(0, (5, 4)), color=MUTED, lw=1.3, zorder=2))
    plan.text(0.0, seen_h / 2 + 0.012,
              f'what the wrist camera sees: {seen_w:.3f} x {seen_h:.3f} m',
              fontsize=9, ha='center', color=MUTED)

    for box in world.boxes:
        low_x, low_y = box.centre[0] - box.size[0] / 2, box.centre[1] - box.size[1] / 2
        colour = '#%02x%02x%02x' % box.rgb
        plan.add_patch(Rectangle((low_x, low_y), box.size[0], box.size[1],
                                 facecolor=colour, edgecolor=INK, lw=0.8, zorder=3))
        # Above each box, so nothing lands on the camera marker at the origin.
        plan.text(box.centre[0], low_y + box.size[1] + 0.009,
                  f'{box.label}, {box.size[2] * 100:g} cm tall',
                  fontsize=9, ha='center', va='bottom', color=INK)

    plan.plot([0], [0], marker='+', color=LENS, ms=14, mew=2.0, zorder=5)
    # Led out to empty table: at the origin the label runs into the red box.
    plan.annotate(f'camera, {CAMERA_HEIGHT_M:g} m above', xy=(0.006, -0.006),
                  xytext=(0.075, -0.165), fontsize=9, color=LENS, ha='center',
                  arrowprops={'arrowstyle': '-|>', 'color': LENS, 'lw': 1.0})
    for (dx, dy), name, colour in (((0.05, 0), '+X', AXIS_X), ((0, 0.05), '+Y', AXIS_Y)):
        plan.annotate('', xy=(-0.22 + dx, -0.19 + dy), xytext=(-0.22, -0.19),
                      arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.6})
        plan.text(-0.22 + dx * 1.45, -0.19 + dy * 1.45, name, fontsize=9,
                  color=colour, ha='center', va='center', family='monospace')
    plan.set_title('From above', fontsize=12, color=INK, weight='bold', pad=12)

    # -- from the side ---------------------------------------------------
    side.set_aspect('equal')
    side.set_xlim(-0.27, 0.27)
    side.set_ylim(-0.055, 0.46)
    side.axis('off')
    side.plot([-0.25, 0.25], [0, 0], color=INK, lw=2.0, zorder=3)
    side.text(-0.25, -0.028, 'the table, z = 0', fontsize=9, color=MUTED, ha='left')

    side.plot([0], [CAMERA_HEIGHT_M], marker='o', color=LENS, ms=9, zorder=6)
    side.text(0.012, CAMERA_HEIGHT_M, '  camera', fontsize=9, color=LENS, va='center')

    # Depth to the table, then to each box top: the numbers a depth picture holds.
    side.annotate('', xy=(-0.20, 0.0), xytext=(-0.20, CAMERA_HEIGHT_M),
                  arrowprops={'arrowstyle': '<|-|>', 'color': MUTED, 'lw': 1.2})
    side.text(-0.205, CAMERA_HEIGHT_M / 2, f'{CAMERA_HEIGHT_M:.2f} m  ', fontsize=9,
              color=MUTED, ha='right', va='center', family='monospace')

    for box in sorted(world.boxes, key=lambda b: b.centre[0]):
        low_x = box.centre[0] - box.size[0] / 2
        colour = '#%02x%02x%02x' % box.rgb
        side.add_patch(Rectangle((low_x, 0.0), box.size[0], box.size[2],
                                 facecolor=colour, edgecolor=INK, lw=0.8, zorder=4))
        side.annotate('', xy=(box.centre[0], box.size[2]), xytext=(box.centre[0], CAMERA_HEIGHT_M),
                      arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.2})
        # zorder above the boxes: green is drawn first and would cover blue's label.
        side.text(box.centre[0] + 0.012, box.size[2] + 0.020,
                  f'{CAMERA_HEIGHT_M - box.size[2]:.2f} m',
                  fontsize=9, ha='left', color=colour, family='monospace', zorder=7,
                  bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.0})

    side.set_title('From the side: what the depth picture reads',
                   fontsize=12, color=INK, weight='bold', pad=12)
    fig.text(0.5, 0.02,
             'Subtract each reading from the 0.40 m the table reads, and you have '
             + ('the height of the box.' if len(world.boxes) == 1
                else 'the height of every box.'),
             fontsize=9.5, ha='center', color=MUTED)
    _save(fig, out)


def one_capture(world=TABLE_SCENE, out='capture.svg'):
    """Take one shot and show it as colour, as depth, and as the numbers behind it."""
    shot = capture(world, WRIST, TOP_DOWN)
    depth = _depth_array(shot)

    # A window straddling the far edge of the red box, where the depth steps
    # cleanly from the box top to the table behind it.
    col_from, col_to = 233, 241
    row_from, row_to = 84, 89

    fig = plt.figure(figsize=(12.0, 4.5), facecolor='white')
    grid = fig.add_gridspec(1, 3, width_ratios=(1.0, 1.0, 1.25), wspace=0.22)

    colour_ax = fig.add_subplot(grid[0, 0])
    _show_picture(colour_ax, _rgb_array(shot), 'colour — rgb8, 3 bytes a pixel')
    depth_ax = fig.add_subplot(grid[0, 1])
    image = depth_ax.imshow(depth, cmap='viridis_r', interpolation='nearest')
    depth_ax.set_title('depth — 32FC1, metres', fontsize=10, color=INK, pad=6)
    depth_ax.set_xticks([])
    depth_ax.set_yticks([])
    bar = fig.colorbar(image, ax=depth_ax, fraction=0.046, pad=0.03)
    bar.ax.tick_params(labelsize=8)
    bar.set_label('metres', fontsize=8)

    for axis in (colour_ax, depth_ax):
        axis.add_patch(Rectangle((col_from - 0.5, row_from - 0.5),
                                 col_to - col_from, row_to - row_from,
                                 fill=False, color=AXIS_X, lw=1.8))
    depth_ax.annotate('these pixels', xy=(col_to, row_from), xytext=(col_to - 20, 34),
                      fontsize=9, color=AXIS_X, ha='center',
                      arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.2})

    # The same handful of pixels, written out as the numbers they are.
    zoom = fig.add_subplot(grid[0, 2])
    zoom.set_xlim(-0.5, col_to - col_from - 0.5)
    zoom.set_ylim(row_to - row_from - 0.5, -0.5)
    zoom.set_aspect('equal')
    zoom.axis('off')
    for row in range(row_from, row_to):
        for col in range(col_from, col_to):
            value = depth[row][col]
            on_box = shot.labels[row][col] != 'table'
            zoom.add_patch(Rectangle((col - col_from - 0.5, row - row_from - 0.5), 1, 1,
                                     facecolor='#fbe6e4' if on_box else PAPER,
                                     edgecolor=GRID, lw=0.6))
            zoom.text(col - col_from, row - row_from, f'{value:.3f}', fontsize=7.5,
                      ha='center', va='center', color=AXIS_X if on_box else INK,
                      family='monospace')
    zoom.set_title('the marked pixels, as metres', fontsize=10, color=INK, pad=6)
    zoom.text(0.5, -0.10, 'red box top, then the table behind it — a 6 cm step',
              transform=zoom.transAxes, fontsize=9, ha='center', color=MUTED)

    fig.suptitle('One capture is two pictures of the same size',
                 fontsize=13, color=INK, weight='bold', y=1.0)
    _save(fig, out)


def configurations(world=TABLE_SCENE, out='configurations.svg'):
    """Compare the two knobs: what is in shot, and how finely it is sampled."""
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 7.4), facecolor='white')

    for axis, name in zip(axes[0], ('wide', 'wrist', 'narrow')):
        config = CameraConfig(name, 240, 180, CONFIGS[name].hfov_deg)
        shot = capture(world, config, TOP_DOWN)
        width_m, _ = config.coverage_m(CAMERA_HEIGHT_M)
        _show_picture(axis, _rgb_array(shot),
                      f'{name} — {config.hfov_deg:g}°, {width_m:.3f} m across')

    for axis, name in zip(axes[1], ('lowres', 'wrist', 'hires')):
        config = CONFIGS[name]
        shot = capture(world, config, TOP_DOWN)
        _show_picture(axis, _rgb_array(shot),
                      f'{name} — {config.width_px}x{config.height_px}, '
                      f'{config.metres_per_pixel(CAMERA_HEIGHT_M) * 1000:.2f} mm a pixel')

    axes[0][0].text(-0.13, 0.5, 'change the lens', transform=axes[0][0].transAxes,
                    fontsize=11, rotation=90, va='center', ha='center',
                    color=INK, weight='bold')
    axes[1][0].text(-0.13, 0.5, 'change the sensor', transform=axes[1][0].transAxes,
                    fontsize=11, rotation=90, va='center', ha='center',
                    color=INK, weight='bold')

    fig.suptitle('Field of view and resolution are separate knobs',
                 fontsize=13, color=INK, weight='bold', y=0.97)
    fig.text(0.5, 0.045,
             'Top row: same sensor, different lens — more of the table, fewer pixels on '
             + ('the box' if len(world.boxes) == 1 else 'each box') + '.\n'
             'Bottom row: same lens, different sensor — the same view, sampled coarsely '
             'or finely.',
             fontsize=9.5, ha='center', color=MUTED)
    fig.subplots_adjust(top=0.90, bottom=0.13, hspace=0.22)
    _save(fig, out)


def deprojection(world=TABLE_SCENE, out='deprojection.svg'):
    """Walk one pixel and its depth reading back out to a point in the room."""
    shot = capture(world, WRIST, TOP_DOWN)
    u, v = 212.5, 86.5
    depth_m = shot.depth_at(u, v)
    cam_x, cam_y, cam_z = WRIST.deproject(u, v, depth_m)
    in_room = shot.pixel_to_world(u, v)

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.3), facecolor='white')

    picture, sums, room = axes
    picture.imshow(_depth_array(shot), cmap='viridis_r', interpolation='nearest')
    picture.plot([u], [v], marker='o', ms=9, mfc='none', mec=AXIS_X, mew=2.0)
    picture.annotate(f'({u:g}, {v:g})', xy=(u, v), xytext=(u - 95, v - 45),
                     fontsize=9, color=AXIS_X, family='monospace',
                     arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.2})
    picture.set_xticks([])
    picture.set_yticks([])

    sums.axis('off')
    # Three lines per coordinate: formula, the numbers put in, the answer. On one
    # line the answer runs into the formula.
    lines = [
        ('x = (u - cx) · depth / fx',
         f'  = ({u:g} - {WRIST.cx:g}) · {depth_m:.3f} / {WRIST.fx:.1f}',
         f'  = {cam_x:+.4f} m'),
        ('y = (v - cy) · depth / fy',
         f'  = ({v:g} - {WRIST.cy:g}) · {depth_m:.3f} / {WRIST.fy:.1f}',
         f'  = {cam_y:+.4f} m'),
        ('z =  depth', '', f'  = {cam_z:+.4f} m'),
    ]
    for i, (lhs, middle, rhs) in enumerate(lines):
        top = 0.92 - i * 0.27
        sums.text(0.0, top, lhs, fontsize=10, family='monospace', color=INK)
        if middle:
            sums.text(0.0, top - 0.075, middle, fontsize=9, family='monospace', color=MUTED)
        # z has nothing to substitute, so its answer closes up the gap.
        sums.text(0.0, top - (0.15 if middle else 0.075), rhs, fontsize=10,
                  family='monospace', color=AXIS_X)
    sums.text(0.0, 0.10, 'measured from the camera; camera_to_world then moves',
              fontsize=9.5, color=MUTED)
    sums.text(0.0, 0.02, 'it into the room', fontsize=9.5, color=MUTED)

    room.set_aspect('equal')
    room.set_xlim(-0.16, 0.16)
    room.set_ylim(-0.16, 0.16)
    room.axis('off')
    for tick in np.arange(-0.15, 0.16, 0.05):
        room.plot([-0.15, 0.15], [tick, tick], color=GRID, lw=0.7, zorder=0)
        room.plot([tick, tick], [-0.15, 0.15], color=GRID, lw=0.7, zorder=0)
    for box in world.boxes:
        low_x, low_y = box.centre[0] - box.size[0] / 2, box.centre[1] - box.size[1] / 2
        room.add_patch(Rectangle((low_x, low_y), box.size[0], box.size[1],
                                 facecolor='#%02x%02x%02x' % box.rgb, alpha=0.55,
                                 edgecolor=INK, lw=0.8, zorder=2))
    room.plot([in_room[0]], [in_room[1]], marker='o', ms=9, color=AXIS_X, zorder=5)
    room.annotate(f'({in_room[0]:+.3f}, {in_room[1]:+.3f}, {in_room[2]:+.3f})',
                  xy=(in_room[0], in_room[1]), xytext=(-0.145, 0.125), fontsize=9,
                  color=AXIS_X, family='monospace',
                  arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.2})
    room.text(0.5, -0.08, f'z = {in_room[2]:.3f} m: the height of the red box top',
              transform=room.transAxes, fontsize=9, ha='center', color=MUTED)

    # The three panels are different shapes, so their own titles would sit at
    # three different heights. Place them all on one line instead.
    titles = (
        f'1. a pixel, and its depth: {depth_m:.3f} m',
        '2. undo the divide by depth',
        '3. a point in the room',
    )
    fig.subplots_adjust(top=0.80)
    for axis, title in zip(axes, titles):
        box = axis.get_position()
        fig.text((box.x0 + box.x1) / 2, 0.855, title, fontsize=10.5, color=INK,
                 ha='center')

    fig.suptitle('Pixel plus depth gives back the point',
                 fontsize=13, color=INK, weight='bold', y=0.98)
    _save(fig, out)


def _iso(point):
    """Flatten a 3D direction onto the page, isometric style."""
    x, y, z = point
    return ((x - y) * math.cos(math.radians(30.0)),
            (x + y) * math.sin(math.radians(30.0)) + z)


def frames():
    """Draw the two axis conventions a ROS camera carries at once."""
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.6), facecolor='white')

    # The camera body points along world +X in both panels; only the naming of
    # the axes differs, which is the entire point.
    forward, left, up = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    right = (0.0, -1.0, 0.0)
    down = (0.0, 0.0, -1.0)

    panels = (
        ('camera_link — the body convention',
         ((forward, '+X forward', AXIS_X), (left, '+Y left', AXIS_Y), (up, '+Z up', AXIS_Z)),
         'matches the rest of the robot, so this is what the URDF bolts to a wrist'),
        ('camera_link_optical — the optical convention',
         ((right, '+X right', AXIS_X), (down, '+Y down', AXIS_Y),
          (forward, '+Z forward', AXIS_Z)),
         'matches the picture, so this is what images are stamped in'),
    )

    for axis, (title, triad, caption) in zip(axes, panels):
        axis.set_aspect('equal')
        axis.set_xlim(-1.6, 1.9)
        axis.set_ylim(-1.5, 1.7)
        axis.axis('off')

        # A small camera body with its lens on the +X face.
        body = [(-0.22, -0.22, -0.18), (0.22, -0.22, -0.18),
                (0.22, 0.22, -0.18), (-0.22, 0.22, -0.18)]
        flat = [_iso(corner) for corner in body]
        axis.fill([p[0] for p in flat], [p[1] for p in flat],
                  facecolor='#dfe6ee', edgecolor=LENS, lw=1.2, zorder=2)
        lens_at = _iso((0.30, 0.0, 0.0))
        axis.add_patch(Circle(lens_at, 0.1, facecolor=LENS, edgecolor=LENS, zorder=3))
        axis.text(lens_at[0] + 0.12, lens_at[1] - 0.26, 'lens', fontsize=8.5,
                  color=LENS, ha='left')

        for direction, label, colour in triad:
            tip = _iso(tuple(component * 1.15 for component in direction))
            axis.annotate('', xy=tip, xytext=_iso((0.0, 0.0, 0.0)),
                          arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 2.0},
                          zorder=4)
            label_at = _iso(tuple(component * 1.38 for component in direction))
            axis.text(label_at[0], label_at[1], label, fontsize=9.5, color=colour,
                      ha='center', va='center', family='monospace', zorder=5,
                      bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})

        axis.set_title(title, fontsize=11, color=INK, weight='bold', pad=10)
        axis.text(0.5, -0.04, caption, transform=axis.transAxes, fontsize=9,
                  ha='center', color=MUTED)

    fig.text(0.5, 0.005,
             'Same camera, same place, a quarter turn between the two. '
             'The turn is published once, on /tf_static.',
             fontsize=9.5, ha='center', color=INK)
    fig.subplots_adjust(bottom=0.16)
    _save(fig, 'frames.svg')


def pixels(world=TABLE_SCENE, out='pixels.svg'):
    """Show what a pixel is, using a capture small enough to see each one."""
    tiny = CameraConfig('tiny', 16, 12, WRIST.hfov_deg)
    small_shot = capture(world, tiny, TOP_DOWN)
    full_shot = capture(world, WRIST, TOP_DOWN)
    w, h = tiny.width_px, tiny.height_px

    fig, (left, right) = plt.subplots(1, 2, figsize=(11.6, 5.0), facecolor='white',
                                      gridspec_kw={'wspace': 0.18})

    # The tiny picture, with each pixel drawn as the square it is. The extent
    # puts pixel (u, v) on the square from u to u+1 and v to v+1, which is the
    # convention the rest of the doc uses.
    left.imshow(_rgb_array(small_shot), interpolation='nearest', extent=(0, w, h, 0))
    for x in range(w + 1):
        left.plot([x, x], [0, h], color='white', lw=0.9)
    for y in range(h + 1):
        left.plot([0, w], [y, y], color='white', lw=0.9)
    left.set_xlim(-2.6, w + 0.4)
    left.set_ylim(h + 2.2, -2.4)
    left.set_aspect('equal')
    left.axis('off')

    left.annotate('', xy=(5.5, -1.0), xytext=(0, -1.0),
                  arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.8})
    left.text(5.9, -1.0, 'u counts across', color=AXIS_X, fontsize=10,
              family='monospace', va='center')
    left.annotate('', xy=(-1.0, 5.5), xytext=(-1.0, 0),
                  arrowprops={'arrowstyle': '-|>', 'color': AXIS_Y, 'lw': 1.8})
    left.text(-1.0, 6.1, 'v counts\ndown', color=AXIS_Y, fontsize=10,
              family='monospace', ha='center', va='top')
    left.text(0.1, -0.25, '(0, 0)', color=INK, fontsize=9.5, family='monospace',
              ha='left', va='bottom')

    left.add_patch(Rectangle((3, 2), 1, 1, fill=False, edgecolor=INK, lw=2.4, zorder=5))
    left.annotate('one pixel:\none square, one colour', xy=(3.5, 3.0), xytext=(3.5, h + 1.4),
                  fontsize=9.5, color=INK, ha='center', va='center', family='monospace',
                  arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.2})

    left.plot([w / 2], [h / 2], marker='+', color='white', ms=16, mew=3, zorder=6)
    left.plot([w / 2], [h / 2], marker='+', color=INK, ms=13, mew=1.6, zorder=7)
    left.annotate(f'the middle\n({w // 2}, {h // 2})', xy=(w / 2, h / 2),
                  xytext=(w - 2.2, h + 1.4), fontsize=9.5, color=INK, ha='center',
                  va='center', family='monospace',
                  arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.2})
    left.set_title(f'{w} × {h} pixels', fontsize=11, color=INK, pad=4)

    right.imshow(_rgb_array(full_shot), interpolation='nearest')
    right.set_xticks([])
    right.set_yticks([])
    for spine in right.spines.values():
        spine.set_color(GRID)
    right.set_title(f'{WRIST.width_px} × {WRIST.height_px} pixels: the same view, cut finer',
                    fontsize=11, color=INK, pad=4)

    fig.suptitle('A picture is a grid of pixels', fontsize=13, color=INK,
                 weight='bold', y=0.98)
    _save(fig, out)


def mask(world=TABLE_SCENE, out='mask.svg'):
    """Show the colour picture next to which box each pixel landed on."""
    shot = capture(world, WRIST, TOP_DOWN)
    colours = {'table': (236, 236, 236), None: (255, 255, 255)}
    colours.update({box.label: box.rgb for box in world.boxes})
    which = np.array([[colours[label] for label in row] for row in shot.labels],
                     dtype=np.uint8)
    counts = {}
    for row in shot.labels:
        for label in row:
            counts[label] = counts.get(label, 0) + 1

    fig, (left, right) = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white',
                                      gridspec_kw={'wspace': 0.12})
    _show_picture(left, _rgb_array(shot), 'what the camera sees: colour')
    _show_picture(right, which, 'which box each pixel landed on')
    for box in world.boxes:
        rows = [r for r, row in enumerate(shot.labels) if box.label in row]
        cols = [c for row in shot.labels for c, lab in enumerate(row) if lab == box.label]
        right.text(sum(cols) / len(cols), max(rows) + 16,
                   f'{box.label}: {counts[box.label]:,} pixels', fontsize=9,
                   ha='center', va='center', color=INK, family='monospace',
                   bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})
    right.text(6, 12, f"table: {counts['table']:,} pixels", fontsize=9, ha='left',
               va='center', color=MUTED, family='monospace')

    fig.suptitle('Three boxes: the new job is telling them apart',
                 fontsize=13, color=INK, weight='bold', y=1.0)
    fig.text(0.5, 0.02, 'Colour and depth do not say which box a pixel belongs to. '
             'That has to be worked out before each box can be measured.',
             fontsize=9.5, ha='center', color=MUTED)
    _save(fig, out)


def _worked_point():
    """Return the section 2.1 example: the pixel, its depth, and the point it gives."""
    shot = capture(ONE_BOX_SCENE, WRIST, TOP_DOWN)
    u, v = SAMPLE_PIXEL
    depth = shot.depth_at(u, v)
    return shot, u, v, depth, WRIST.deproject(u, v, depth)


def deproject_setup(out='deproject_setup.svg'):
    """Show, from the side, where the camera is and which spot is being measured."""
    shot, u, v, depth, (x, _y, _z) = _worked_point()
    box = ONE_BOX_SCENE.boxes[0]
    low_x, top = box.centre[0] - box.size[0] / 2, box.size[2]

    fig, ax = _new_axes(size=(8.6, 5.6), xlim=(-0.38, 0.34), ylim=(-0.07, 0.47))
    ax.plot([-0.22, 0.26], [0, 0], color=INK, lw=2.0, zorder=3)
    ax.text(0.26, -0.03, 'the table', fontsize=9.5, color=MUTED, ha='right')
    ax.add_patch(Rectangle((low_x, 0), box.size[0], top, facecolor='#%02x%02x%02x' % box.rgb,
                           edgecolor=INK, lw=0.8, zorder=4))
    ax.text(low_x + box.size[0] + 0.008, top / 2, 'red box,\n6 cm tall', fontsize=9,
            color=INK, va='center')

    ax.plot([0], [CAMERA_HEIGHT_M], marker='s', color=LENS, ms=13, zorder=6)
    ax.text(-0.02, CAMERA_HEIGHT_M + 0.03, 'the camera, 0.40 m above the middle\n'
            'of the table, looking straight down', fontsize=9.5, color=LENS,
            ha='center', va='bottom')

    # The camera's own axes: X to the right, Z straight ahead, which here is down.
    for (dx, dz), name, colour in (((0.07, 0), 'X: right', AXIS_X),
                                   ((0, -0.07), 'Z: ahead (down)', AXIS_Z)):
        ax.annotate('', xy=(dx, CAMERA_HEIGHT_M + dz), xytext=(0, CAMERA_HEIGHT_M),
                    arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 1.8}, zorder=7)
    ax.text(0.078, CAMERA_HEIGHT_M, 'X: right', fontsize=9, color=AXIS_X, va='center')
    ax.text(-0.008, CAMERA_HEIGHT_M - 0.085, 'Z: straight ahead,\nwhich is down', fontsize=9,
            color=AXIS_Z, ha='right', va='top')

    # The line of sight to the spot, and the straight-ahead line.
    ax.plot([0, x], [CAMERA_HEIGHT_M, top], color=AXIS_X, lw=1.4, ls=(0, (5, 3)), zorder=5)
    ax.plot([0, 0], [CAMERA_HEIGHT_M, top], color=GRID, lw=1.2, ls=(0, (2, 2)), zorder=2)
    ax.plot([x], [top], marker='o', color=INK, ms=7, zorder=8)
    ax.annotate('the spot we measure,\nseen at pixel (212.5, 86.5)', xy=(x, top),
                xytext=(0.16, 0.16), fontsize=9, color=INK, ha='left',
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.0})

    # What we want: how far right (x), and how far ahead (depth, which is z).
    ax.annotate('', xy=(x, top + 0.012), xytext=(0, top + 0.012),
                arrowprops={'arrowstyle': '<|-|>', 'color': AXIS_X, 'lw': 1.3})
    ax.text(x / 2, top + 0.024, 'x', fontsize=11, color=AXIS_X, ha='center', weight='bold')
    ax.annotate('', xy=(-0.17, top), xytext=(-0.17, CAMERA_HEIGHT_M),
                arrowprops={'arrowstyle': '<|-|>', 'color': AXIS_Z, 'lw': 1.3})
    ax.text(-0.18, (top + CAMERA_HEIGHT_M) / 2, f'depth = z\n= {depth:.3f} m', fontsize=9.5,
            color=AXIS_Z, ha='right', va='center', family='monospace')
    ax.plot([-0.175, 0], [top, top], color=GRID, lw=0.8, zorder=1)
    ax.annotate('', xy=(-0.28, 0), xytext=(-0.28, CAMERA_HEIGHT_M),
                arrowprops={'arrowstyle': '<|-|>', 'color': MUTED, 'lw': 1.0})
    ax.text(-0.29, CAMERA_HEIGHT_M / 2, '0.40 m', fontsize=9, color=MUTED, ha='right',
            va='center', family='monospace')

    fig.suptitle('Where the camera is, and what we are measuring', fontsize=13,
                 color=INK, weight='bold', y=0.97)
    fig.text(0.5, 0.03, 'Seen from the side. We want x (how far right of the camera) and z '
             '(how far ahead of it). y, towards the top of the picture, works the same way.',
             fontsize=9.5, ha='center', color=MUTED)
    _save(fig, out)


def deproject_pixel(out='deproject_pixel.svg'):
    """Mark u, v, cx, cy and the two pixel offsets on the real picture."""
    shot, u, v, _depth, _point = _worked_point()
    w, h = WRIST.width_px, WRIST.height_px
    cx, cy = WRIST.cx, WRIST.cy

    fig, ax = plt.subplots(figsize=(8.4, 6.4), facecolor='white')
    ax.imshow(_rgb_array(shot), interpolation='nearest', extent=(0, w, h, 0), alpha=0.55)
    ax.set_xlim(-62, w + 6)
    ax.set_ylim(h + 44, -44)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), w, h, fill=False, edgecolor=MUTED, lw=1.0))

    # The directions u and v count in, and the picture's edges.
    ax.annotate('', xy=(120, -22), xytext=(0, -22),
                arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 1.8})
    ax.text(126, -22, 'u counts across: left to right, 0 to 320', fontsize=9.5,
            color=AXIS_X, va='center')
    ax.annotate('', xy=(-22, 90), xytext=(-22, 0),
                arrowprops={'arrowstyle': '-|>', 'color': AXIS_Y, 'lw': 1.8})
    ax.text(-22, 96, 'v counts\ndown:\ntop to\nbottom,\n0 to 240', fontsize=9.5,
            color=AXIS_Y, ha='center', va='top')

    # The middle of the picture, and our pixel.
    ax.plot([cx], [cy], marker='+', color=INK, ms=18, mew=2.2, zorder=6)
    ax.text(cx - 6, cy + 16, f'the middle: (cx, cy) = ({cx:g}, {cy:g})', fontsize=9.5,
            color=INK, ha='center', va='top',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})
    ax.plot([u], [v], marker='o', color=INK, ms=9, mfc='none', mew=2.2, zorder=7)
    ax.text(u + 10, v - 12, f'our pixel: (u, v) = ({u:g}, {v:g})', fontsize=9.5,
            color=INK, ha='left', va='bottom',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})

    # How far the pixel is from the middle: right, then up.
    ax.annotate('', xy=(u, cy), xytext=(cx, cy),
                arrowprops={'arrowstyle': '-|>', 'color': AXIS_X, 'lw': 2.2,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=5)
    ax.text((cx + u) / 2, cy + 38, f'{u - cx:g} pixels to the right\nu − cx = {u - cx:g}',
            fontsize=9.5, color=AXIS_X, ha='left', va='top',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})
    ax.annotate('', xy=(u, v), xytext=(u, cy),
                arrowprops={'arrowstyle': '-|>', 'color': AXIS_Y, 'lw': 2.2,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=5)
    ax.text(u + 32, (cy + v) / 2 + 6, f'{cy - v:g} pixels up\nv − cy = {v - cy:g}\n'
            '(negative, because\nv counts down)', fontsize=9.5, color=AXIS_Y,
            ha='left', va='center',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})

    fig.suptitle('The variables in the picture', fontsize=13, color=INK, weight='bold', y=0.95)
    fig.text(0.5, 0.06, 'The colour picture from the camera, 320 × 240 pixels, faded so the '
             'markings stand out.', fontsize=9.5, ha='center', color=MUTED)
    _save(fig, out)


def deproject_triangles(out='deproject_triangles.svg'):
    """Show the two same-shaped triangles that make the formula work."""
    _shot, u, v, depth, (x, _y, _z) = _worked_point()
    fx, cx = WRIST.fx, WRIST.cx
    box = ONE_BOX_SCENE.boxes[0]
    top = box.size[2]
    lens = CAMERA_HEIGHT_M
    slope = (u - cx) / fx                  # sideways per unit forwards, the same for both
    pic_z = lens - 0.12                    # where the picture is drawn: only its shape matters

    fig, ax = plt.subplots(figsize=(8.6, 6.0), facecolor='white')
    ax.set_xlim(-0.16, 0.215)
    ax.set_ylim(-0.03, 0.46)
    # Sideways is drawn 2.5 times wider than forwards, so the thin triangles can be
    # read. Stretching both the same way keeps them the same shape as each other.
    ax.set_aspect(0.4)
    ax.axis('off')

    ax.plot([-0.10, 0.20], [0, 0], color=INK, lw=2.0)
    low_x = box.centre[0] - box.size[0] / 2
    ax.add_patch(Rectangle((low_x, 0), box.size[0], top, facecolor='#e6a39c',
                           edgecolor=INK, lw=0.6, zorder=1))
    ax.plot([0], [lens], marker='o', color=LENS, ms=10, zorder=6)
    ax.text(-0.01, lens + 0.012, 'lens', fontsize=10, color=LENS, ha='right')

    # The straight-ahead line and the line of sight to the spot.
    ax.plot([0, 0], [lens, top], color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.plot([0, x], [lens, top], color=INK, lw=1.6, zorder=3)
    ax.plot([x], [top], marker='o', color=INK, ms=7, zorder=6)

    # Small triangle: inside the camera, measured in pixels.
    small = slope * (lens - pic_z)
    ax.fill([0, 0, small], [lens, pic_z, pic_z], color='#cfe3f5', zorder=2)
    ax.plot([0, small], [pic_z, pic_z], color=AXIS_X, lw=2.4, zorder=4)
    ax.annotate('', xy=(-0.018, pic_z), xytext=(-0.018, lens),
                arrowprops={'arrowstyle': '<|-|>', 'color': '#2f6db0', 'lw': 1.2})
    ax.text(-0.024, (lens + pic_z) / 2, f'fx = {fx:.1f}\npixels', fontsize=9.5,
            color='#2f6db0', ha='right', va='center', family='monospace')
    ax.text(small + 0.004, pic_z - 0.004, f'u − cx = {u - cx:g} pixels', fontsize=9.5,
            color=AXIS_X, ha='left', va='top', family='monospace')
    ax.text(0.06, pic_z + 0.045, 'small triangle: the picture,\ninside the camera, in pixels',
            fontsize=9, color='#2f6db0', ha='left')

    # Large triangle: outside the camera, measured in metres.
    ax.fill([0, 0, x], [lens, top, top], color='#fbe0dc', alpha=0.55, zorder=1)
    ax.plot([0, x], [top, top], color=AXIS_X, lw=2.4, zorder=4)
    ax.annotate('', xy=(-0.075, top), xytext=(-0.075, lens),
                arrowprops={'arrowstyle': '<|-|>', 'color': '#b5433a', 'lw': 1.2})
    ax.text(-0.081, (lens + top) / 2 - 0.04, f'z = depth\n= {depth:.3f} m', fontsize=9.5,
            color='#b5433a', ha='right', va='center', family='monospace')
    ax.text(x / 2, top - 0.012, f'x = {x:.4f} m', fontsize=9.5, color=AXIS_X,
            ha='center', va='top', family='monospace',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.0})
    ax.text(0.10, top + 0.075, 'large triangle: from the lens\nto the spot, in metres',
            fontsize=9, color='#b5433a', ha='left')

    fig.suptitle('Why it works: two triangles with the same shape', fontsize=13,
                 color=INK, weight='bold', y=0.96)
    fig.text(0.5, 0.05, 'Same shape, so the same ratio:   '
             f'{u - cx:g} / {fx:.1f}  =  x / {depth:.3f}'
             f'     so     x = {x:.4f} m', fontsize=10.5, ha='center', color=INK,
             family='monospace')
    fig.text(0.5, 0.01, 'Sideways distances are drawn 2.5 times wider than they really are, '
             'so the triangles are easier to see.', fontsize=9, ha='center', color=MUTED)
    _save(fig, out)


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Part 1 of the doc: every idea, shown on one box.
    scene(ONE_BOX_SCENE, 'scene_one.svg')
    pixels(ONE_BOX_SCENE)
    pinhole()
    field_of_view()
    focal_length()
    fx_fy()
    one_capture(ONE_BOX_SCENE)
    configurations(ONE_BOX_SCENE)
    deprojection(ONE_BOX_SCENE)
    deproject_setup()
    deproject_pixel()
    deproject_triangles()
    # Part 2: three boxes.
    scene(TABLE_SCENE, 'scene.svg')
    mask(TABLE_SCENE)
    # The ROS reference section.
    frames()
