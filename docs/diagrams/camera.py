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
import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.patches import Circle, Rectangle  # noqa: E402  (must follow use)
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


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Part 1 of the doc: every idea, shown on one box.
    scene(ONE_BOX_SCENE, 'scene_one.svg')
    pixels(ONE_BOX_SCENE)
    pinhole()
    field_of_view()
    one_capture(ONE_BOX_SCENE)
    configurations(ONE_BOX_SCENE)
    deprojection(ONE_BOX_SCENE)
    # Part 2: three boxes.
    scene(TABLE_SCENE, 'scene.svg')
    mask(TABLE_SCENE)
    # The ROS reference section.
    frames()
