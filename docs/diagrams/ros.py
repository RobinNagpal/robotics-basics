"""Generate the diagrams used in the docs/01_ros/ docs.

Each doc's images go to a folder named after it, under docs/images/ros/.

Run with:  pixi run python docs/diagrams/ros.py

The camera picture is drawn by the ros_camera package's own code, the arm's
sizes are read from its URDF, and the pixel-to-angle example uses the
follower's own function, so the diagrams match the code.
"""

import math
import pathlib
import sys
import xml.etree.ElementTree as ElementTree

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'src' / 'ros' / 'ros_applied' / 'ros_camera'))
sys.path.insert(0, str(REPO_ROOT / 'src' / 'ros' / 'ros_applied' / 'ros_camera_arm'))

import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from ros_camera.camera_publisher import ball_position, CX, CY, draw_picture, FX  # noqa: E402
from ros_camera.camera_subscriber import find_ball  # noqa: E402
from ros_camera_arm.follower import pixel_to_angles  # noqa: E402

IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'ros'
URDF: pathlib.Path = REPO_ROOT / 'src' / 'ros' / 'ros_applied' / 'ros_arm' / 'urdf' / 'arm.urdf'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
GREY: str = '#9a9a9a'


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def picture() -> None:
    """Draw the picture the camera publisher sends, and the ball the subscriber finds."""
    u: float
    v: float
    u, v = ball_position(2.0)
    image: NDArray[np.uint8] = draw_picture(u, v)
    found: tuple[float, float] | None = find_ball(image)
    assert found is not None        # the ball is always inside this picture
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(7.2, 5.2), facecolor='white')
    ax.imshow(image, extent=(0, image.shape[1], image.shape[0], 0), interpolation='nearest')
    ax.set_xticks([0, 80, 160, 240, 320])
    ax.set_yticks([0, 60, 120, 180, 240])
    ax.tick_params(labelsize=8, colors=MUTED)
    ax.plot([found[0]], [found[1]], marker='+', color=INK, ms=16, mew=2)
    ax.annotate(f'the subscriber finds the ball\nat pixel ({found[0]:.0f}, {found[1]:.0f})',
                xy=found, xytext=(found[0] - 150, found[1] + 45), fontsize=9.5, color=INK,
                arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 1.1},
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2})
    ax.set_xlabel('u: pixels across, from the left', fontsize=9.5, color=RED)
    ax.set_ylabel('v: pixels down, from the top', fontsize=9.5, color=GREEN)
    ax.set_title('One picture from the camera publisher: 320 x 240 pixels',
                 fontsize=12, color=INK, weight='bold', pad=10)
    _save(fig, 'ros-camera', 'picture.svg')


def image_message() -> None:
    """Draw how a picture becomes a sensor_msgs/Image: its pixels, row after row."""
    tiny: list[list[tuple[int, int, int]]] = [[(220, 40, 40), (200, 200, 200), (200, 200, 200)],
                                              [(200, 200, 200), (40, 90, 220), (200, 200, 200)]]
    fig: Figure
    left: Axes
    right: Axes
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 3.6), facecolor='white',
                                      gridspec_kw={'width_ratios': (1, 2.6)})
    for axis in (left, right):
        axis.set_aspect('equal')
        axis.axis('off')

    left.set_xlim(-0.6, 3.4)
    left.set_ylim(2.7, -0.9)
    for row, pixels in enumerate(tiny):
        for col, rgb in enumerate(pixels):
            left.add_patch(Rectangle((col, row), 1, 1, facecolor=[c / 255 for c in rgb],
                                     edgecolor='white', lw=2))
    left.text(1.5, -0.45, 'a picture 3 pixels wide\nand 2 pixels tall', ha='center',
              fontsize=9.5, color=INK)

    # The bytes: every pixel's red, green and blue, row 0 first, then row 1.
    right.set_xlim(-0.5, 18.5)
    right.set_ylim(3.6, -1.6)
    x: int = 0
    for row, pixels in enumerate(tiny):
        start: int = x
        for rgb in pixels:
            for channel, value in zip('RGB', rgb):
                right.add_patch(Rectangle((x, 0), 1, 1, facecolor=[c / 255 for c in rgb],
                                          alpha=0.35, edgecolor=GREY, lw=0.8))
                right.text(x + 0.5, 0.5, str(value), ha='center', va='center', fontsize=7.5,
                           color=INK, family='monospace')
                right.text(x + 0.5, 1.45, channel, ha='center', fontsize=7.5, color=MUTED)
                x += 1
        right.annotate('', xy=(x, 2.3), xytext=(start, 2.3),
                       arrowprops={'arrowstyle': '<|-|>', 'color': BLUE, 'lw': 1.1})
        right.text((start + x) / 2, 3.0, f'row {row}: step = 3 pixels x 3 bytes = 9 bytes',
                   ha='center', fontsize=8.5, color=BLUE)
    right.text(9, -0.8, 'data: all the bytes, row after row, three per pixel (encoding rgb8)',
               ha='center', fontsize=9.5, color=INK)
    fig.suptitle('How a picture becomes a message', fontsize=12, color=INK, weight='bold', y=1.02)
    _save(fig, 'ros-camera', 'image_message.svg')


def _urdf_sizes() -> tuple[float, float, float]:
    """Read the arm's sizes from its URDF: where each joint is, and how long the arm is."""
    root: ElementTree.Element = ElementTree.parse(URDF).getroot()
    joints: dict[str | None, ElementTree.Element] = {j.get('name'): j for j in root.iter('joint')}
    # find() and get() may return None, but arm.urdf always has these tags.
    z: list[float] = [
        float(joints[name].find('origin').get('xyz').split()[2])  # type: ignore[union-attr]
        for name in ('pan', 'tilt')]
    length: float = float(
        joints['tip_joint'].find('origin').get('xyz').split()[0])  # type: ignore[union-attr]
    return z[0], z[0] + z[1], length


def arm() -> None:
    """Draw the arm's two joints: pan, seen from above, and tilt, seen from the side."""
    pan_z: float
    tilt_z: float
    length: float
    pan_z, tilt_z, length = _urdf_sizes()
    pan: float
    tilt: float
    pan, tilt = math.radians(30), math.radians(25)
    fig: Figure
    side: Axes
    top: Axes
    fig, (side, top) = plt.subplots(1, 2, figsize=(11, 4.6), facecolor='white')

    side.set_aspect('equal')
    side.axis('off')
    side.set_xlim(-0.12, 0.34)
    side.set_ylim(-0.03, 0.30)
    side.plot([-0.11, 0.32], [0, 0], color=INK, lw=1.5)
    side.add_patch(Rectangle((-0.06, 0), 0.12, pan_z, facecolor='#cccccc', edgecolor=INK, lw=0.8))
    side.add_patch(Rectangle((-0.03, pan_z), 0.06, tilt_z - pan_z, facecolor='#dddddd',
                             edgecolor=INK, lw=0.8))
    end: tuple[float, float] = (length * math.cos(tilt), tilt_z + length * math.sin(tilt))
    side.plot([0, end[0]], [tilt_z, end[1]], color=ORANGE, lw=9, solid_capstyle='butt')
    side.plot([end[0]], [end[1]], marker='o', color=RED, ms=10)
    side.plot([0, 0.2], [tilt_z, tilt_z], color=MUTED, lw=1, ls=':')
    side.add_patch(Arc((0, tilt_z), 0.16, 0.16, theta1=0, theta2=math.degrees(tilt), color=GREEN,
                       lw=1.5))
    side.text(0.095, tilt_z + 0.018, f'tilt = {math.degrees(tilt):.0f}°', color=GREEN, fontsize=10)
    side.plot([0], [tilt_z], marker='o', color=GREEN, ms=7)
    side.text(-0.035, tilt_z + 0.012, 'tilt joint', color=GREEN, fontsize=9, ha='right')
    side.text(end[0] + 0.012, end[1], 'tip', color=RED, fontsize=9, va='center')
    side.text(0.07, 0.012, 'base_link', color=INK, fontsize=9)
    side.text(0.035, pan_z + 0.02, 'turret', color=INK, fontsize=9)
    side.text(0.12, 0.2, 'arm_link', color=ORANGE, fontsize=9)
    side.set_title('From the side: tilt tips the arm up and down', fontsize=11, color=INK, pad=6)

    top.set_aspect('equal')
    top.axis('off')
    top.set_xlim(-0.12, 0.32)
    top.set_ylim(-0.12, 0.22)
    top.add_patch(Circle((0, 0), 0.06, facecolor='#cccccc', edgecolor=INK, lw=0.8))
    reach: float = length * math.cos(tilt)
    tip: tuple[float, float] = (reach * math.cos(pan), reach * math.sin(pan))
    top.plot([0, tip[0]], [0, tip[1]], color=ORANGE, lw=9, solid_capstyle='butt')
    top.plot([tip[0]], [tip[1]], marker='o', color=RED, ms=10)
    top.plot([0, 0.25], [0, 0], color=MUTED, lw=1, ls=':')
    top.text(0.255, -0.004, 'x: straight ahead', color=MUTED, fontsize=8.5, va='center')
    top.add_patch(Arc((0, 0), 0.2, 0.2, theta1=0, theta2=math.degrees(pan), color=BLUE, lw=1.5))
    top.text(0.105, 0.03, f'pan = {math.degrees(pan):.0f}°', color=BLUE, fontsize=10)
    top.annotate('', xy=(0, 0.1), xytext=(0, 0), arrowprops={'arrowstyle': '-|>', 'color': MUTED})
    top.text(-0.01, 0.105, 'y: to the left', color=MUTED, fontsize=8.5, ha='right')
    top.plot([0], [0], marker='o', color=BLUE, ms=7)
    top.text(0.012, -0.03, 'pan joint', color=BLUE, fontsize=9)
    top.set_title('From above: pan turns the arm left and right', fontsize=11, color=INK, pad=6)

    fig.suptitle(f'The arm: two joints, and a {length * 100:.0f} cm arm that points',
                 fontsize=12, color=INK, weight='bold', y=1.0)
    fig.text(0.5, 0.0, 'Positive pan turns left, and positive tilt tips up. Both are angles in '
             'radians in the JointState message: 30° is 0.52 radians.', ha='center',
             fontsize=9, color=MUTED)
    _save(fig, 'ros-arm', 'arm.svg')


def gripper_and_sensor() -> None:
    """Draw the gripper's fingers from above, and the distance sensor's beam from the side."""
    fig: Figure
    top: Axes
    side: Axes
    fig, (top, side) = plt.subplots(1, 2, figsize=(11, 4.6), facecolor='white',
                                    gridspec_kw={'width_ratios': (1, 1.4)})

    # From above: the palm, and two fingers each slid out by `gripper` metres.
    gripper: float = 0.015
    top.set_aspect('equal')
    top.axis('off')
    top.set_xlim(-0.04, 0.11)
    top.set_ylim(-0.055, 0.06)
    top.add_patch(Rectangle((-0.03, -0.015), 0.03, 0.03, facecolor=ORANGE, edgecolor=INK, lw=0.6))
    top.add_patch(Rectangle((0, -0.035), 0.02, 0.07, facecolor='#cccccc', edgecolor=INK, lw=0.8))
    for sign in (1, -1):
        low: float = sign * gripper + (0 if sign > 0 else -0.008)
        top.add_patch(Rectangle((0.02, low), 0.04, 0.008, facecolor=RED, edgecolor=INK, lw=0.8))
        top.annotate('', xy=(0.07, sign * gripper), xytext=(0.07, 0),
                     arrowprops={'arrowstyle': '-|>', 'color': BLUE, 'lw': 1.2})
    top.text(0.075, 0.0, f'gripper =\n{gripper:.3f} m:\nhow far each\nfinger slides',
             color=BLUE, fontsize=9, va='center')
    top.text(-0.015, -0.028, 'arm', color=ORANGE, fontsize=9, ha='center')
    top.text(0.01, 0.04, 'palm', color=INK, fontsize=9, ha='center')
    top.text(0.04, -0.047, f'open {2 * gripper * 100:.0f} cm', color=RED, fontsize=9, ha='center')
    top.set_title('The gripper, from above: one sliding joint', fontsize=11, color=INK, pad=6)

    # From the side: the arm tilted up, and the beam leaving the palm at right
    # angles to the arm, down to the table.
    pan_z: float
    tilt_z: float
    length: float
    pan_z, tilt_z, length = _urdf_sizes()
    tilt: float = math.radians(25)
    side.set_aspect('equal')
    side.axis('off')
    side.set_xlim(-0.10, 0.36)
    side.set_ylim(-0.03, 0.26)
    side.plot([-0.09, 0.35], [0, 0], color=INK, lw=1.5)
    side.add_patch(Rectangle((-0.06, 0), 0.12, pan_z, facecolor='#cccccc', edgecolor=INK, lw=0.8))
    side.add_patch(Rectangle((-0.03, pan_z), 0.06, tilt_z - pan_z, facecolor='#dddddd',
                             edgecolor=INK, lw=0.8))
    side.text(0.34, -0.022, 'the table', color=MUTED, fontsize=9, ha='right')
    end: tuple[float, float] = (length * math.cos(tilt), tilt_z + length * math.sin(tilt))
    side.plot([0, end[0]], [tilt_z, end[1]], color=ORANGE, lw=8, solid_capstyle='butt')
    side.plot([0], [tilt_z], marker='o', color=GREEN, ms=7)
    beam: tuple[float, float]
    beam = (math.sin(tilt), -math.cos(tilt))           # at right angles to the arm, downwards
    reach: float = end[1] / math.cos(tilt)
    hit: tuple[float, float] = (end[0] + beam[0] * reach, end[1] + beam[1] * reach)
    side.plot([end[0], hit[0]], [end[1], hit[1]], color=BLUE, lw=1.6, ls=(0, (5, 3)))
    side.plot([end[0]], [end[1]], marker='s', color=INK, ms=6)
    side.text(end[0] + 0.01, end[1] + 0.012, 'the sensor, under the palm', fontsize=9, color=INK)
    side.plot([end[0], end[0]], [end[1], 0], color=MUTED, lw=1, ls=':')
    side.text(end[0] - 0.006, end[1] / 2, 'height', color=MUTED, fontsize=9, ha='right')
    side.text((end[0] + hit[0]) / 2 + 0.012, end[1] / 2, 'the beam:\nthe distance\nit measures',
              color=BLUE, fontsize=9, va='center')
    side.add_patch(Arc(end, 0.09, 0.09, theta1=270, theta2=270 + math.degrees(tilt), color=GREEN,
                       lw=1.4))
    side.text(end[0] + 0.012, end[1] - 0.075, f'{math.degrees(tilt):.0f}°', color=GREEN, fontsize=9)
    side.text(0.0, tilt_z + 0.035, f'tilt = {math.degrees(tilt):.0f}°', color=GREEN, fontsize=9,
              ha='center')
    side.set_title('The distance sensor, from the side: its beam leans with the arm',
                   fontsize=11, color=INK, pad=6)
    fig.text(0.62, 0.02, 'distance = height / cos(tilt): the more the arm tilts, the longer '
             'the beam', ha='center', fontsize=9.5, color=INK, family='monospace')
    _save(fig, 'ros-arm', 'gripper_sensor.svg')


def pixel_to_angle() -> None:
    """Draw, from above, how a pixel right of the middle becomes a turn to the right."""
    # The ball from the camera doc's picture, where the subscriber found it.
    found: tuple[float, float] | None = find_ball(draw_picture(*ball_position(2.0)))
    assert found is not None        # the ball is always inside this picture
    u: float
    v: float
    u, v = found
    pan: float
    _tilt: float
    pan, _tilt = pixel_to_angles(u, v, FX, FX, CX, CY)
    offset: float = u - CX
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(8.4, 6.2), facecolor='white')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-190, 190)
    ax.set_ylim(-40, 560)

    # The camera at the bottom, looking up the page. The picture is drawn fx
    # pixels in front of it, and the ball's line of sight passes through pixel u.
    ax.plot([0], [0], marker='s', color=INK, ms=12)
    ax.text(8, -24, 'the camera, at the base of the arm', fontsize=9, color=INK)
    ax.plot([-CX, CX], [FX, FX], color=INK, lw=3)
    ax.text(-CX - 4, FX + 14, 'the picture, 320 pixels wide', fontsize=9, color=INK)
    ax.plot([0, 0], [0, 520], color=MUTED, lw=1, ls=':')
    ax.text(4, 525, 'straight ahead: pixel u = 160', fontsize=8.5, color=MUTED)
    far: float = 520 / FX
    ax.plot([0, offset * far], [0, 520], color=RED, lw=1.6)
    ax.plot([offset], [FX], marker='o', color=RED, ms=8)
    ax.plot([offset * 1.75], [FX * 1.75], marker='o', color=RED, ms=22, alpha=0.8)
    ax.text(offset * 1.75 - 22, FX * 1.75, 'the ball', fontsize=9.5, color=RED, va='center',
            ha='right')

    ax.annotate('', xy=(offset, FX - 16), xytext=(0, FX - 16),
                arrowprops={'arrowstyle': '<|-|>', 'color': RED, 'lw': 1.1})
    ax.text(offset / 2, FX - 34, f'u - cx = {offset:.0f} pixels', fontsize=9, color=RED,
            ha='center')
    ax.annotate('', xy=(-120, FX), xytext=(-120, 0),
                arrowprops={'arrowstyle': '<|-|>', 'color': BLUE, 'lw': 1.1})
    ax.text(-126, FX / 2, f'fx = {FX:.1f}\npixels', fontsize=9, color=BLUE, ha='right',
            va='center')
    ax.add_patch(Arc((0, 0), 240, 240, theta1=90 - math.degrees(-pan), theta2=90, color=GREEN,
                     lw=1.6))
    ax.text(26, 128, f'{math.degrees(-pan):.1f}°', fontsize=10, color=GREEN)

    ax.set_title('From above: how far right the ball is in the picture sets the turn',
                 fontsize=12, color=INK, weight='bold', pad=8)
    ax.text(0, -60, f'angle = atan({offset:.0f} / {FX:.1f}) = {math.degrees(-pan):.1f}° to the '
            f'right, so pan = {math.degrees(pan):.1f}°', fontsize=10, color=INK, ha='center',
            family='monospace')
    _save(fig, 'ros-camera-arm', 'pixel_to_angle.svg')


if __name__ == '__main__':
    picture()
    image_message()
    arm()
    gripper_and_sensor()
    pixel_to_angle()
