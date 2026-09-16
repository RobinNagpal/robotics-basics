"""Generate the diagrams used in the camera docs: basics, one-box-intro and one-box-code.

Each doc's images go to a folder named after it: docs/images/camera/basics/,
docs/images/camera/one-box-intro/ and docs/images/camera/one-box-code/.

Run with:  pixi run python docs/diagrams/camera.py

The pictures here are not drawn by hand. They are real captures from the
camera_one_box simulation in Gazebo, recorded by docs/diagrams/record_camera.py
into docs/diagrams/captures/camera/. The box sizes and positions are read from
the Gazebo world file, and pixels are turned into points with the project's own
measure.py. So if you change the world, the camera or the maths, record the
captures again and regenerate, rather than editing the SVGs.
"""

from dataclasses import dataclass
import math
import pathlib
import sys
from typing import Any
import xml.etree.ElementTree as ElementTree

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
# The diagrams turn pixels into points with the same code the box locator uses.
sys.path.insert(0, str(REPO_ROOT / 'src' / 'camera' / 'camera_applied' / 'camera_one_box'))

from cv_bridge import CvBridge  # noqa: E402
from geometry_msgs.msg import Quaternion, TransformStamped, Vector3  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
from matplotlib.image import AxesImage  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Arc, Circle, Rectangle  # noqa: E402  (must follow use)
from matplotlib.patches import Polygon  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
from rclpy.serialization import deserialize_message  # noqa: E402
from rclpy.time import Time  # noqa: E402
import rosbag2_py  # noqa: E402
from rosidl_runtime_py.utilities import get_message  # noqa: E402
from sensor_msgs.msg import CameraInfo  # noqa: E402
from tf2_ros import Buffer  # noqa: E402

from camera_one_box.measure import depth_to_points, to_world, transform_matrix  # noqa: E402

IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'camera'
CAPTURES: pathlib.Path = REPO_ROOT / 'docs' / 'diagrams' / 'captures' / 'camera'
CAMERA_ONE_BOX: pathlib.Path = REPO_ROOT / 'src' / 'camera' / 'camera_applied' / 'camera_one_box'
WORLD: pathlib.Path = CAMERA_ONE_BOX / 'worlds' / 'one_box.sdf'

#: Where _save writes. The main block at the bottom points it at each doc's
#: folder in turn, before drawing that doc's diagrams.
OUT_DIR: pathlib.Path = IMAGES

#: The pixel the one-box intro works through: on top of the red box, off centre
#: so that both halves of the arithmetic have work to do.
SAMPLE_PIXEL: tuple[float, float] = (212.5, 86.5)


@dataclass(frozen=True)
class Camera:
    """A camera's picture size and its four lens numbers, from its camera info."""

    width_px: int
    height_px: int
    fx: float
    fy: float
    cx: float
    cy: float

    @property
    def hfov_deg(self) -> float:
        """How many degrees across the camera sees."""
        return math.degrees(2.0 * math.atan(self.width_px / 2.0 / self.fx))

    @property
    def vfov_deg(self) -> float:
        """How many degrees down the picture it sees."""
        return math.degrees(2.0 * math.atan(self.height_px / 2.0 / self.fy))

    def coverage_m(self, distance_m: float) -> tuple[float, float]:
        """How much of a flat surface this far away fills the picture, across and down."""
        return self.width_px * distance_m / self.fx, self.height_px * distance_m / self.fy

    def metres_per_pixel(self, distance_m: float) -> float:
        """How much of a flat surface this far away one pixel covers."""
        return distance_m / self.fx

    def deproject(self, u: float, v: float, depth_m: float) -> tuple[float, float, float]:
        """Turn one pixel and its depth into a point measured from the camera."""
        return ((u - self.cx) * depth_m / self.fx, (v - self.cy) * depth_m / self.fy, depth_m)


@dataclass(frozen=True)
class Shot:
    """One capture from Gazebo: the two pictures, the lens, and where the camera was."""

    camera: Camera
    rgb: NDArray[np.uint8]
    depth: NDArray[np.float32]
    camera_to_world: NDArray[np.float64]

    def depth_at(self, u: float, v: float) -> float:
        """Return the depth reading of pixel (u, v), in metres."""
        return float(self.depth[int(v), int(u)])

    def pixel_to_world(self, u: float, v: float) -> tuple[float, float, float]:
        """Turn one pixel into a point in the room."""
        point: NDArray[np.float64] = np.array(self.camera.deproject(u, v, self.depth_at(u, v)))
        return tuple(to_world(point, self.camera_to_world)[0])

    def points_in_world(self) -> NDArray[np.float64]:
        """Turn every pixel into a point in the room, as the box locator does."""
        c: Camera = self.camera
        return to_world(depth_to_points(self.depth, c.fx, c.fy, c.cx, c.cy),
                        self.camera_to_world).reshape(self.depth.shape + (3,))


def load(name: str) -> Shot:
    """Read one recorded capture, with the same libraries the box locator uses."""
    reader: rosbag2_py.SequentialReader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(CAPTURES / name), storage_id='mcap'),
                rosbag2_py.ConverterOptions('', ''))
    types: dict[str, str] = {topic.name: topic.type for topic in reader.get_all_topics_and_types()}
    # The messages are of different classes, an Image, a CameraInfo and a TFMessage, so
    # their type is written as Any: "any type at all".
    messages: dict[str, Any] = {}
    while reader.has_next():
        topic: str
        data: bytes
        topic, data, _ = reader.read_next()
        messages[topic] = deserialize_message(data, get_message(types[topic]))

    info: CameraInfo = messages['/camera/camera_info']
    camera: Camera = Camera(info.width, info.height, info.k[0], info.k[4], info.k[2], info.k[5])
    bridge: CvBridge = CvBridge()
    buffer: Buffer = Buffer()
    for transform in messages['/tf_static'].transforms:
        buffer.set_transform_static(transform, 'capture')
    tf: TransformStamped = buffer.lookup_transform('world', info.header.frame_id, Time())
    t: Vector3
    q: Quaternion
    t, q = tf.transform.translation, tf.transform.rotation
    return Shot(
        camera=camera,
        rgb=bridge.imgmsg_to_cv2(messages['/camera/image_raw'], desired_encoding='rgb8'),
        depth=bridge.imgmsg_to_cv2(messages['/camera/depth/image_raw'],
                                   desired_encoding='32FC1'),
        camera_to_world=transform_matrix((t.x, t.y, t.z), (q.x, q.y, q.z, q.w)),
    )


@dataclass(frozen=True)
class Box:
    """A box standing on the table, as the Gazebo world file describes it."""

    label: str
    rgb: tuple[int, int, int]
    centre: tuple[float, float]
    size: tuple[float, float, float]


def world_boxes(sdf: pathlib.Path = WORLD) -> list[Box]:
    """Read every box model out of the world file: its colour, where it is, its size."""
    boxes: list[Box] = []
    for model in ElementTree.parse(sdf).getroot().iter('model'):
        # get() and findtext() give the '' passed to them when a tag is missing,
        # rather than None, so what they return is always a str.
        name: str = model.get('name', '')
        if not name.endswith('_box'):
            continue
        x: float
        y: float
        x, y = (float(value) for value in model.findtext('pose', '').split()[:2])
        size: tuple[float, ...] = tuple(
            float(value) for value in model.findtext('.//visual//size', '').split())
        diffuse: list[str] = model.findtext('.//visual//diffuse', '').split()[:3]
        rgb: tuple[int, ...] = tuple(int(round(float(value) * 255)) for value in diffuse)
        # tuple() cannot know the world file gives three numbers each, so mypy is told.
        boxes.append(Box(name.removesuffix('_box'), rgb, (x, y), size))  # type: ignore[arg-type]
    return boxes


WRIST: Shot = load('wrist')
RED_BOX: Box = world_boxes()[0]
#: How high the camera is above the table, in metres, from its transform.
CAMERA_HEIGHT_M: float = float(WRIST.camera_to_world[2, 3])

GRID: str = '#d6d6d6'
AXIS_X: str = '#d1495b'
AXIS_Y: str = '#2a9d3f'
AXIS_Z: str = '#1a99ff'
INK: str = '#222222'
MUTED: str = '#777777'
PAPER: str = '#f4f4f4'
LENS: str = '#3d5a80'


def _new_axes(size: tuple[float, float] = (6.0, 6.0),
              xlim: tuple[float, float] = (-3.2, 3.2),
              ylim: tuple[float, float] = (-3.2, 3.2)) -> tuple[Figure, Axes]:
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=size, facecolor='white')
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def _save(fig: Figure, name: str) -> None:
    fig.savefig(OUT_DIR / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {OUT_DIR / name}')


def _title(ax: Axes, text: str, y: float | None = None, subtitle: str | None = None) -> None:
    ax.set_title(text, fontsize=12, color=INK, weight='bold', pad=10)
    if subtitle is not None:
        # A subtitle is always given with the y to put it at, so y is not None here.
        ax.text(0.5, y, subtitle, transform=ax.transAxes, fontsize=9,  # type: ignore[arg-type]
                ha='center', color=MUTED)


def _rgb_array(shot: Shot) -> NDArray[np.uint8]:
    """Return the colour picture as an array matplotlib can show."""
    return shot.rgb


def _depth_array(shot: Shot) -> NDArray[np.float32]:
    """Return the depth picture as an array, with missing readings as NaN."""
    return shot.depth


def _show_picture(ax: Axes, image: NDArray[np.uint8], title: str, cmap: str | None = None,
                  vmin: float | None = None, vmax: float | None = None) -> Axes:
    ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='nearest')
    ax.set_title(title, fontsize=10, color=INK, pad=6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(GRID)
    return ax


def pinhole() -> None:
    """Draw the projection idea: three points at one ratio share one pixel."""
    fig: Figure
    ax: Axes
    fig, ax = _new_axes(size=(7.4, 4.4), xlim=(-0.9, 5.2), ylim=(-1.95, 1.75))

    # The optical axis runs to the right; the picture is the vertical line.
    ax.annotate('', xy=(4.8, 0), xytext=(0, 0),
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.0, 'ls': ':'})
    ax.text(4.85, 0.0, '+Z\nforward', fontsize=9, color=MUTED, va='center')

    plane_z: float = 1.25
    ax.plot([plane_z, plane_z], [-1.15, 1.15], color=INK, lw=2.0, zorder=3)
    ax.text(plane_z, -1.32, 'the picture', fontsize=9, ha='center', color=INK)

    # One ray. Every point on it has the same x/z, so it is the same pixel.
    slope: float = 0.28
    ax.plot([0, 4.6], [0, -slope * 4.6], color=AXIS_X, lw=1.6, zorder=2)

    for z_pos, label in ((1.9, 'near'), (3.1, 'further'), (4.3, 'further still')):
        ax.add_patch(Circle((z_pos, -slope * z_pos), 0.075, color=AXIS_X, zorder=4))
        ax.text(z_pos, -slope * z_pos - 0.26, label, fontsize=9, ha='center', color=INK)

    pixel_y: float = -slope * plane_z
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


def field_of_view() -> None:
    """Draw what each lens can see of the table from the same height."""
    fig: Figure
    ax: Axes
    fig, ax = _new_axes(size=(7.4, 4.4), xlim=(-0.48, 0.48), ylim=(-0.06, 0.50))
    ax.set_aspect('auto')

    # The table, edge on.
    ax.plot([-0.46, 0.46], [0, 0], color=INK, lw=2.0, zorder=3)
    for tick in np.arange(-0.45, 0.46, 0.05):
        ax.plot([tick, tick], [0, -0.012], color=GRID, lw=1.0, zorder=2)
    ax.text(-0.465, -0.032, 'the table', fontsize=9, ha='left', color=MUTED)

    eye: tuple[float, float] = (0.0, CAMERA_HEIGHT_M)
    ax.add_patch(Circle(eye, 0.011, color=LENS, zorder=6))
    ax.text(0.015, CAMERA_HEIGHT_M, f'  camera, {CAMERA_HEIGHT_M:g} m up',
            fontsize=9, va='center', color=LENS)

    styles: tuple[tuple[str, str, float], ...]
    styles = (('wide', AXIS_Y, 0.30), ('wrist', AXIS_X, 0.55), ('narrow', AXIS_Z, 0.85))
    for name, colour, alpha in styles:
        config: Camera = load(name).camera
        half: float = math.tan(math.radians(config.hfov_deg) / 2.0) * CAMERA_HEIGHT_M
        ax.fill([eye[0], -half, half], [eye[1], 0, 0], color=colour, alpha=0.12, zorder=1)
        for sign in (-1, 1):
            ax.plot([eye[0], sign * half], [eye[1], 0], color=colour, lw=1.4,
                    alpha=alpha, zorder=4)
        width_m: float
        width_m, _ = config.coverage_m(CAMERA_HEIGHT_M)
        # One row per lens, so the three measurements do not sit on top of
        # each other.
        row: int = styles.index((name, colour, alpha))
        arrow_y: float = -0.055 - 0.075 * row
        ax.annotate('', xy=(half, arrow_y), xytext=(-half, arrow_y),
                    arrowprops={'arrowstyle': '<|-|>', 'color': colour, 'lw': 1.2})
        ax.text(0.0, arrow_y - 0.042,
                f'{name}: {config.hfov_deg:.0f}° → {width_m:.3f} m across, '
                f'{config.metres_per_pixel(CAMERA_HEIGHT_M) * 1000:.2f} mm per pixel',
                fontsize=9, ha='center', va='center', color=colour, family='monospace',
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})

    ax.set_ylim(-0.285, 0.50)
    ax.text(0.0, 0.47, 'Field of view decides how much is in shot',
            fontsize=13, ha='center', color=INK, weight='bold')
    _save(fig, 'field_of_view.svg')


def focal_length(out: str = 'focal_length.svg') -> None:
    """Show what focal length is: the gap between lens and sensor, and what it changes."""
    fig: Figure
    axes: NDArray[np.object_]       # a NumPy array holding one Axes per panel
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.3), facecolor='white')
    box_z: float
    box_h: float
    sensor_half: float
    box_z, box_h, sensor_half = -3.0, 0.9, 0.8
    lens_colour: str
    focal_colour: str
    scene_colour: str
    lens_colour, focal_colour, scene_colour = LENS, '#2f6db0', '#b5433a'
    row: float = -1.12                           # the row the lengths along the axis are drawn on

    def span(ax: Axes, start: tuple[float, float], end: tuple[float, float], colour: str) -> None:
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
        view: Rectangle = Rectangle((-3.3, -0.95), f + 3.6, 2.2, transform=ax.transData)
        for sign in (-1, 1):
            reach: float = sensor_half / f * 3.3
            edge: Line2D
            edge, = ax.plot([f, -3.3], [sign * sensor_half, -sign * reach], color=MUTED,
                            lw=0.8, ls=(0, (4, 3)))
            edge.set_clip_path(view)
        shade: Polygon
        shade, = ax.fill([0, -3.3, -3.3], [0, sensor_half / f * 3.3, -sensor_half / f * 3.3],
                         color='#e8eef5', zorder=0)
        shade.set_clip_path(view)
        ax.text(-2.3, -0.3, 'what the sensor\ncan see', fontsize=8.5,
                color=MUTED, ha='center', va='top')

        # The box, and the light from its top corner through the lens.
        ax.add_patch(Rectangle((box_z - 0.12, 0), 0.24, box_h, facecolor='#e6a39c',
                               edgecolor=INK, lw=0.6, zorder=3))
        image_h: float = box_h * f / -box_z
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


def fx_fy(out: str = 'fx_fy.svg') -> None:
    """Put fx, fy, cx and cy on this doc's camera: once seen from above, once from the side."""
    _shot: Shot
    u: float
    v: float
    _depth: float
    _point: tuple[float, float, float]
    _shot, u, v, _depth, _point = _worked_point()
    camera: Camera = WRIST.camera
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.4), facecolor='white')
    focal_colour: str = '#2f6db0'
    # Each panel: its axes, title, focal length, size, middle, offset, field of view,
    # colour, letter, the names of its two edges, and the words by the spot.
    panels: tuple[tuple[Axes, str, float, int, float, float, float, str, str, str, str, str], ...]
    panels = (
        (axes[0], 'Across the picture: fx and cx', camera.fx, camera.width_px, camera.cx,
         u - camera.cx, camera.hfov_deg, AXIS_X, 'u', 'left edge', 'right edge',
         f'{u - camera.cx:g} pixels right\nof the middle'),
        (axes[1], 'Down the picture: fy and cy', camera.fy, camera.height_px, camera.cy,
         v - camera.cy, camera.vfov_deg, AXIS_Y, 'v', 'top edge', 'bottom edge',
         f'{-(v - camera.cy):g} pixels above\nthe middle'),
    )
    for ax, title, f, size, middle, offset, fov, colour, letter, low, high, spot in panels:
        ax.set_xlim(-230, 230)
        ax.set_ylim(-395, 60)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=11.5, color=INK, pad=2)
        half: float = size / 2

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
        name: str = 'fx' if letter == 'u' else 'fy'
        ax.text(-half - 30, -f / 2, f'{name} =\n{f:.1f}\npixels', fontsize=9.5,
                color=focal_colour, ha='right', va='center', family='monospace')

        # The field of view: the angle between the two edges, at the lens.
        ax.add_patch(Arc((0, 0), 110, 110, theta1=270 - fov / 2, theta2=270 + fov / 2,
                         color=MUTED, lw=1.0))
        side: int = -1 if offset > 0 else 1
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


def scene(out: str = 'scene.svg') -> None:
    """Draw the table, the box and the camera, from above and from the side."""
    boxes: list[Box] = world_boxes()
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), facecolor='white')
    plan: Axes
    side: Axes
    plan, side = axes

    # -- from above ------------------------------------------------------
    plan.set_aspect('equal')
    plan.set_xlim(-0.27, 0.27)
    plan.set_ylim(-0.24, 0.24)
    plan.axis('off')
    for tick in np.arange(-0.25, 0.26, 0.05):
        plan.plot([-0.25, 0.25], [tick, tick], color=GRID, lw=0.7, zorder=0)
        plan.plot([tick, tick], [-0.22, 0.22], color=GRID, lw=0.7, zorder=0)

    seen_w: float
    seen_h: float
    seen_w, seen_h = WRIST.camera.coverage_m(CAMERA_HEIGHT_M)
    plan.add_patch(Rectangle((-seen_w / 2, -seen_h / 2), seen_w, seen_h, fill=False,
                             ls=(0, (5, 4)), color=MUTED, lw=1.3, zorder=2))
    plan.text(0.0, seen_h / 2 + 0.012,
              f'what the camera sees: {seen_w:.3f} x {seen_h:.3f} m',
              fontsize=9, ha='center', color=MUTED)

    for box in boxes:
        low_x: float
        low_y: float
        low_x, low_y = box.centre[0] - box.size[0] / 2, box.centre[1] - box.size[1] / 2
        colour: str = '#%02x%02x%02x' % box.rgb
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

    for box in sorted(boxes, key=lambda b: b.centre[0]):
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
             'Subtract the reading on the box from the 0.40 m the table reads, and you '
             'have the height of the box.',
             fontsize=9.5, ha='center', color=MUTED)
    _save(fig, out)


def one_capture(out: str = 'capture.svg') -> None:
    """Show one capture as colour, as depth, and as the numbers behind it."""
    shot: Shot = WRIST
    depth: NDArray[np.float32] = _depth_array(shot)

    # A window straddling the far edge of the red box, where the depth steps
    # cleanly from the box top to the table behind it.
    col_from: int
    col_to: int
    col_from, col_to = 233, 241
    row_from: int
    row_to: int
    row_from, row_to = 84, 89

    fig: Figure = plt.figure(figsize=(12.0, 4.5), facecolor='white')
    grid: GridSpec = fig.add_gridspec(1, 3, width_ratios=(1.0, 1.0, 1.25), wspace=0.22)

    colour_ax: Axes = fig.add_subplot(grid[0, 0])
    _show_picture(colour_ax, _rgb_array(shot), 'colour — rgb8, 3 bytes a pixel')
    depth_ax: Axes = fig.add_subplot(grid[0, 1])
    image: AxesImage = depth_ax.imshow(depth, cmap='viridis_r', interpolation='nearest')
    depth_ax.set_title('depth — 32FC1, metres', fontsize=10, color=INK, pad=6)
    depth_ax.set_xticks([])
    depth_ax.set_yticks([])
    bar: Colorbar = fig.colorbar(image, ax=depth_ax, fraction=0.046, pad=0.03)
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
    zoom: Axes = fig.add_subplot(grid[0, 2])
    zoom.set_xlim(-0.5, col_to - col_from - 0.5)
    zoom.set_ylim(row_to - row_from - 0.5, -0.5)
    zoom.set_aspect('equal')
    zoom.axis('off')
    for row in range(row_from, row_to):
        for col in range(col_from, col_to):
            value: np.float32 = depth[row][col]
            on_box: np.bool_ = value < 0.399            # nearer than the table
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


def configurations(out: str = 'configurations.svg') -> None:
    """Compare the two knobs: what is in shot, and how finely it is sampled."""
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 7.4), facecolor='white')

    for axis, name in zip(axes[0], ('wide', 'wrist', 'narrow')):
        shot: Shot = load(name)
        config: Camera = shot.camera
        width_m: float
        width_m, _ = config.coverage_m(CAMERA_HEIGHT_M)
        _show_picture(axis, _rgb_array(shot),
                      f'{name} — {config.hfov_deg:.0f}°, {width_m:.3f} m across')

    for axis, name in zip(axes[1], ('lowres', 'wrist', 'hires')):
        shot = load(name)
        config = shot.camera
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
             'the box.\n'
             'Bottom row: same lens, different sensor — the same view, sampled coarsely '
             'or finely.',
             fontsize=9.5, ha='center', color=MUTED)
    fig.subplots_adjust(top=0.90, bottom=0.13, hspace=0.22)
    _save(fig, out)


def deprojection(out: str = 'deprojection.svg') -> None:
    """Walk one pixel and its depth reading back out to a point in the room."""
    shot: Shot = WRIST
    u: float
    v: float
    u, v = SAMPLE_PIXEL
    depth_m: float = shot.depth_at(u, v)
    cam_x: float
    cam_y: float
    cam_z: float
    cam_x, cam_y, cam_z = shot.camera.deproject(u, v, depth_m)
    in_room: tuple[float, float, float] = shot.pixel_to_world(u, v)

    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.3), facecolor='white')

    picture: Axes
    sums: Axes
    room: Axes
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
    lines: list[tuple[str, str, str]] = [
        ('x = (u - cx) · depth / fx',
         f'  = ({u:g} - {shot.camera.cx:g}) · {depth_m:.3f} / {shot.camera.fx:.1f}',
         f'  = {cam_x:+.4f} m'),
        ('y = (v - cy) · depth / fy',
         f'  = ({v:g} - {shot.camera.cy:g}) · {depth_m:.3f} / {shot.camera.fy:.1f}',
         f'  = {cam_y:+.4f} m'),
        ('z =  depth', '', f'  = {cam_z:+.4f} m'),
    ]
    for i, (lhs, middle, rhs) in enumerate(lines):
        top: float = 0.92 - i * 0.27
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
    for box in world_boxes():
        low_x: float
        low_y: float
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
    titles: tuple[str, str, str] = (
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


def _iso(point: tuple[float, ...]) -> tuple[float, float]:
    """Flatten a 3D direction onto the page, isometric style."""
    x: float
    y: float
    z: float
    x, y, z = point
    return ((x - y) * math.cos(math.radians(30.0)),
            (x + y) * math.sin(math.radians(30.0)) + z)


def frames() -> None:
    """Draw the two axis conventions a ROS camera carries at once."""
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.6), facecolor='white')

    # The camera body points along world +X in both panels; only the naming of
    # the axes differs, which is the entire point.
    forward: tuple[float, float, float]
    left: tuple[float, float, float]
    up: tuple[float, float, float]
    forward, left, up = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    right: tuple[float, float, float] = (0.0, -1.0, 0.0)
    down: tuple[float, float, float] = (0.0, 0.0, -1.0)

    # Each panel: its title, its three arrows (direction, label, colour), and its caption.
    panels: tuple[tuple[str, tuple[tuple[tuple[float, float, float], str, str], ...], str], ...]
    panels = (
        ('camera_link — the body convention',
         ((forward, '+X forward', AXIS_X), (left, '+Y left', AXIS_Y), (up, '+Z up', AXIS_Z)),
         'matches the rest of the robot, so this is what the URDF bolts to the stand'),
        ('camera_optical_frame — the optical convention',
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
        body: list[tuple[float, float, float]] = [(-0.22, -0.22, -0.18), (0.22, -0.22, -0.18),
                                                  (0.22, 0.22, -0.18), (-0.22, 0.22, -0.18)]
        flat: list[tuple[float, float]] = [_iso(corner) for corner in body]
        axis.fill([p[0] for p in flat], [p[1] for p in flat],
                  facecolor='#dfe6ee', edgecolor=LENS, lw=1.2, zorder=2)
        lens_at: tuple[float, float] = _iso((0.30, 0.0, 0.0))
        axis.add_patch(Circle(lens_at, 0.1, facecolor=LENS, edgecolor=LENS, zorder=3))
        axis.text(lens_at[0] + 0.12, lens_at[1] - 0.26, 'lens', fontsize=8.5,
                  color=LENS, ha='left')

        for direction, label, colour in triad:
            tip: tuple[float, float] = _iso(tuple(component * 1.15 for component in direction))
            axis.annotate('', xy=tip, xytext=_iso((0.0, 0.0, 0.0)),
                          arrowprops={'arrowstyle': '-|>', 'color': colour, 'lw': 2.0},
                          zorder=4)
            label_at: tuple[float, float] = _iso(tuple(component * 1.38 for component in direction))
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


def pixels(out: str = 'pixels.svg') -> None:
    """Show what a pixel is, using a capture small enough to see each one."""
    small_shot: Shot = load('tiny')
    full_shot: Shot = WRIST
    w: int
    h: int
    w, h = small_shot.camera.width_px, small_shot.camera.height_px

    fig: Figure
    left: Axes
    right: Axes
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
    right.set_title(f'{full_shot.camera.width_px} × {full_shot.camera.height_px} pixels: '
                    'the same view, cut finer',
                    fontsize=11, color=INK, pad=4)

    fig.suptitle('A picture is a grid of pixels', fontsize=13, color=INK,
                 weight='bold', y=0.98)
    _save(fig, out)


def _worked_point() -> tuple[Shot, float, float, float, tuple[float, float, float]]:
    """Return the one-box intro's section 1.1 example: the pixel, its depth, its point."""
    shot: Shot = WRIST
    u: float
    v: float
    u, v = SAMPLE_PIXEL
    depth: float = shot.depth_at(u, v)
    return shot, u, v, depth, shot.camera.deproject(u, v, depth)


def deproject_setup(out: str = 'deproject_setup.svg') -> None:
    """Show, from the side, where the camera is and which spot is being measured."""
    shot: Shot
    u: float
    v: float
    depth: float
    x: float
    _y: float
    _z: float
    shot, u, v, depth, (x, _y, _z) = _worked_point()
    box: Box = RED_BOX
    low_x: float
    top: float
    low_x, top = box.centre[0] - box.size[0] / 2, box.size[2]

    fig: Figure
    ax: Axes
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


def deproject_pixel(out: str = 'deproject_pixel.svg') -> None:
    """Mark u, v, cx, cy and the two pixel offsets on the real picture."""
    shot: Shot
    u: float
    v: float
    _depth: float
    _point: tuple[float, float, float]
    shot, u, v, _depth, _point = _worked_point()
    w: int
    h: int
    w, h = WRIST.camera.width_px, WRIST.camera.height_px
    cx: float
    cy: float
    cx, cy = WRIST.camera.cx, WRIST.camera.cy

    fig: Figure
    ax: Axes
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


def deproject_triangles(out: str = 'deproject_triangles.svg') -> None:
    """Show the two same-shaped triangles that make the formula work."""
    _shot: Shot
    u: float
    v: float
    depth: float
    x: float
    _y: float
    _z: float
    _shot, u, v, depth, (x, _y, _z) = _worked_point()
    fx: float
    cx: float
    fx, cx = WRIST.camera.fx, WRIST.camera.cx
    box: Box = RED_BOX
    top: float = box.size[2]
    lens: float = CAMERA_HEIGHT_M
    slope: float
    pic_z: float
    slope = (u - cx) / fx                  # sideways per unit forwards, the same for both
    pic_z = lens - 0.12                    # where the picture is drawn: only its shape matters

    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(8.6, 6.0), facecolor='white')
    ax.set_xlim(-0.16, 0.215)
    ax.set_ylim(-0.03, 0.46)
    # Sideways is drawn 2.5 times wider than forwards, so the thin triangles can be
    # read. Stretching both the same way keeps them the same shape as each other.
    ax.set_aspect(0.4)
    ax.axis('off')

    ax.plot([-0.10, 0.20], [0, 0], color=INK, lw=2.0)
    low_x: float = box.centre[0] - box.size[0] / 2
    ax.add_patch(Rectangle((low_x, 0), box.size[0], top, facecolor='#e6a39c',
                           edgecolor=INK, lw=0.6, zorder=1))
    ax.plot([0], [lens], marker='o', color=LENS, ms=10, zorder=6)
    ax.text(-0.01, lens + 0.012, 'lens', fontsize=10, color=LENS, ha='right')

    # The straight-ahead line and the line of sight to the spot.
    ax.plot([0, 0], [lens, top], color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.plot([0, x], [lens, top], color=INK, lw=1.6, zorder=3)
    ax.plot([x], [top], marker='o', color=INK, ms=7, zorder=6)

    # Small triangle: inside the camera, measured in pixels.
    small: float = slope * (lens - pic_z)
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
    # Each doc's diagrams go into a folder named after the doc.
    for folder, drawings in (
        ('basics', (scene, pixels, field_of_view, pinhole, one_capture, focal_length, fx_fy,
                    configurations)),
        ('one-box-intro', (scene, deproject_setup, deproject_pixel, deproject_triangles,
                           deprojection)),
        ('one-box-code', (frames,)),
    ):
        OUT_DIR = IMAGES / folder
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for draw in drawings:
            draw()
