"""How a camera works, in plain Python: configure it, point it, take pictures.

This file is the camera itself. The two problems the doc works through live next
to it, one file each, and are what ``make camera.learn`` runs::

    problems/one_box.py       part 1: every idea, on one box
    problems/three_boxes.py   part 2: three boxes, and what changes

There is no ROS in this file, and no image library. A camera is a small piece
of arithmetic wrapped around a lens, and the whole of it fits here: four numbers
describe the lens, twelve describe where the camera is, and two formulas move
between pixels and points. Everything else — the ROS message, the driver, the
simulator — is packaging around those.

WHAT A CAMERA ACTUALLY DOES
---------------------------
It flattens. The world is 3D, a picture is 2D, and taking a picture throws the
third dimension away::

    a point 2 m away, 1 m to the left        ─┐
    a point 4 m away, 2 m to the left        ─┼──▶ the same pixel
    a point 8 m away, 4 m to the left        ─┘

Every pixel is a *direction*, not a place. That one sentence explains most of
what follows: why a colour camera cannot measure anything on its own, why a
depth reading is what makes a pixel useful, and why "where was the camera?" has
to be recorded with every picture.

THE FOUR NUMBERS: INTRINSICS
----------------------------
``fx``, ``fy``, ``cx``, ``cy``. They are called the **intrinsics** because they
are intrinsic to the camera itself — its lens and its sensor — and do not change
when it moves.

* ``cx``, ``cy`` are the middle of the picture, in pixels. Straight ahead lands
  there.
* ``fx``, ``fy`` are the **focal length in pixels**. One number for how zoomed
  in the lens is. Big means narrow and magnified; small means wide and shrunk.

Focal length in pixels sounds like a category error — a lens is measured in
millimetres. It is a shortcut. What matters for the arithmetic is *how many
pixels a given angle covers*, which mixes the lens and the sensor together, so
the two are folded into one number and measured in pixels.

FLATTENING, AS ARITHMETIC
--------------------------
A point in front of the camera, measured in the camera's own axes, becomes a
pixel by dividing by how far away it is::

    u = fx * (x / z) + cx
    v = fy * (y / z) + cy

``x / z`` is the whole idea. Twice as far away for twice the offset gives the
same ratio, so it gives the same pixel — the three points in the sketch above.
Dividing by ``z`` is where the third dimension goes.

AND BACK AGAIN
--------------
Turn those two lines around and you get the reverse::

    x = (u - cx) * depth / fx
    y = (v - cy) * depth / fy
    z = depth

That is called **deprojection**, and it is the reason depth cameras exist. The
pixel gave a direction; ``depth`` says how far to go along it. Together they
give back the point. This is the single most useful thing in this file: it is
how a picture of a table becomes a set of points you can measure.

WHAT THIS FILE CONTAINS
-----------------------
1. :class:`CameraConfig` — the lens: intrinsics, field of view, and the two
   formulas above. :data:`CONFIGS` holds five of them to compare.
2. :class:`Pose` and :func:`look_at` — where the camera is and which way it
   faces, in the axis convention ROS uses for cameras.
3. :class:`Scene` — three coloured boxes on a table, so there is something to
   photograph. Rendered by ray casting, in about forty lines.
4. :class:`Capture` — one shot, and the different kinds of picture you can ask
   it for: colour, grey, depth in metres, depth in millimetres, a point cloud,
   and a labelled mask.
5. :func:`main` — the walkthrough that prints all of it.

THE SCENE
---------
Everything is photographed against the same scene, so the pictures can be
compared. A grey table at ``z = 0`` with a 5 cm grid printed on it, and three
boxes of different heights standing on it::

           +Y
            │      ██ green, 9 cm tall
            │            ██ red, 6 cm cube
            └────────── +X
         ██ blue, 4 cm tall

The default camera sits 40 cm above the middle looking straight down. From
there the table reads 0.40 m, the red box top reads 0.34 m, and that 6 cm jump
in the numbers is how a box shows up in a depth picture.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

#: Grey of the table top, as 8-bit RGB.
TABLE_RGB = (148, 148, 148)
#: Slightly darker grey used for the 5 cm grid printed on the table.
TABLE_GRID_RGB = (120, 120, 120)
#: Spacing of that grid, in metres.
TABLE_GRID_SPACING_M = 0.05
#: Width of a grid line, in metres.
TABLE_GRID_WIDTH_M = 0.004

#: How much of a surface's colour survives, per face. Flat shading, so the top
#: of a box reads brighter than its sides and the picture stays readable.
FACE_SHADE = (0.70, 0.85, 1.00)

#: Rays closer than this to the camera are treated as behind it.
_EPS = 1e-9


# --------------------------------------------------------------------------
# 1. The lens
# --------------------------------------------------------------------------


def focal_length_px(width_px: int, hfov_deg: float) -> float:
    """Turn a field of view into a focal length in pixels.

    A camera ``width_px`` wide that sees ``hfov_deg`` across is a triangle: the
    half-width ``width_px / 2`` is the opposite side, the focal length is the
    adjacent side, and half the field of view is the angle between them. So::

        fx = (width_px / 2) / tan(hfov_deg / 2)

    For 320 pixels across 60 degrees that is ``160 / tan(30°)``, or about 277.
    Halve the field of view and the focal length roughly doubles: seeing less
    of the world means each degree of it covers more pixels.
    """
    return (width_px / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)


def field_of_view_deg(size_px: int, focal_px: float) -> float:
    """Go the other way: from a focal length to the angle it covers.

    Real cameras report ``fx`` and ``fy``, not an angle, so this is how you find
    out what a camera can see from what it tells you about itself.
    """
    return math.degrees(2.0 * math.atan((size_px / 2.0) / focal_px))


@dataclass(frozen=True)
class CameraConfig:
    """A lens and a sensor: everything about the camera that moving it cannot change.

    Only three numbers are stored — the picture size and the horizontal field of
    view — because the four intrinsics follow from them for an ideal camera with
    square pixels. A real driver reads the intrinsics off the device instead;
    they mean the same thing either way.

    :param name: Short label, used in the printed tables.
    :param width_px: Picture width, in pixels.
    :param height_px: Picture height, in pixels.
    :param hfov_deg: How many degrees across the picture covers.
    :param depth_min_m: Nearer than this, the depth sensor reports nothing.
    :param depth_max_m: Further than this, likewise.
    """

    name: str
    width_px: int
    height_px: int
    hfov_deg: float
    depth_min_m: float = 0.05
    depth_max_m: float = 3.0

    @property
    def fx(self) -> float:
        """Focal length across the picture, in pixels."""
        return focal_length_px(self.width_px, self.hfov_deg)

    @property
    def fy(self) -> float:
        """Focal length down the picture, in pixels.

        Equal to :attr:`fx` here because the pixels are square, which is true of
        essentially every camera you will meet. The two are kept apart anyway,
        because the message format keeps them apart.
        """
        return self.fx

    @property
    def cx(self) -> float:
        """Middle of the picture, across."""
        return self.width_px / 2.0

    @property
    def cy(self) -> float:
        """Middle of the picture, down."""
        return self.height_px / 2.0

    @property
    def vfov_deg(self) -> float:
        """How many degrees the picture covers top to bottom.

        Not a free choice. With square pixels it falls out of the width, the
        height and the horizontal field of view: a picture 3/4 as tall as it is
        wide sees less vertically, and by how much is fixed by the arithmetic.
        """
        return field_of_view_deg(self.height_px, self.fy)

    @property
    def pixel_count(self) -> int:
        """How many pixels one picture holds."""
        return self.width_px * self.height_px

    def coverage_m(self, distance_m: float) -> tuple[float, float]:
        """How much of a flat surface ``distance_m`` away fits in the picture.

        ``width / fx`` is the width of the picture in *directions*; multiply by
        how far away the surface is and you get metres. Twice as far away means
        twice as much in shot — which is why a camera cannot tell how big
        something is without knowing how far away it is.
        """
        return (
            distance_m * self.width_px / self.fx,
            distance_m * self.height_px / self.fy,
        )

    def metres_per_pixel(self, distance_m: float) -> float:
        """How much of a surface ``distance_m`` away one pixel covers.

        The practical number. If one pixel covers 1.4 mm, nothing 1 mm wide is
        going to be measured reliably, whatever the code does afterwards.
        """
        return distance_m / self.fx

    def project(self, point: tuple[float, float, float]) -> tuple[float, float] | None:
        """Flatten a point in camera axes onto the picture: 3D in, pixel out.

        Returns ``None`` for anything at or behind the lens, which has no pixel.
        The result can still land outside the picture — that is a real point,
        just not one this camera can see. Use :meth:`contains` to check.
        """
        x, y, z = point
        if z <= _EPS:
            return None
        return (self.fx * x / z + self.cx, self.fy * y / z + self.cy)

    def deproject(self, u: float, v: float, depth_m: float) -> tuple[float, float, float]:
        """Unflatten a pixel back into a point, given how far away it is.

        The inverse of :meth:`project`, and the reason a depth camera is worth
        having. Note that ``depth_m`` is the distance measured *straight along
        the direction the camera looks*, not the slanted line to the point — see
        :meth:`Capture.depth_at`.
        """
        return (
            (u - self.cx) * depth_m / self.fx,
            (v - self.cy) * depth_m / self.fy,
            depth_m,
        )

    def ray(self, u: float, v: float) -> tuple[float, float, float]:
        """Return the direction pixel ``(u, v)`` looks in, in camera axes.

        This is :meth:`deproject` at a depth of exactly 1, and it is deliberately
        *not* scaled to unit length. Left as it is, the ``z`` component is 1, so
        walking ``t`` along this direction lands at depth ``t`` — which makes the
        ray caster below hand back a depth for free.
        """
        return ((u - self.cx) / self.fx, (v - self.cy) / self.fy, 1.0)

    def contains(self, u: float, v: float) -> bool:
        """Say whether this pixel is inside the picture."""
        return 0.0 <= u < self.width_px and 0.0 <= v < self.height_px

    def describe(self) -> str:
        """One line of the table :func:`main` prints."""
        return (
            f'{self.name:<10} {self.width_px:>4}x{self.height_px:<4} '
            f'{self.hfov_deg:>5.1f}° {self.vfov_deg:>5.1f}° '
            f'{self.fx:>7.1f} {self.cx:>6.1f} {self.cy:>6.1f}'
        )


#: Five cameras that differ in exactly one thing at a time, so the effect of
#: each is visible on its own. ``wrist`` is the one everything else is compared
#: with; it matches the small RGB-D cameras usually bolted next to a gripper.
CONFIGS: dict[str, CameraConfig] = {
    'wrist': CameraConfig('wrist', 320, 240, 60.0),
    'wide': CameraConfig('wide', 320, 240, 90.0),
    'narrow': CameraConfig('narrow', 320, 240, 30.0),
    'hires': CameraConfig('hires', 640, 480, 60.0),
    'lowres': CameraConfig('lowres', 80, 60, 60.0),
}

#: The default, referred to throughout the docs.
WRIST = CONFIGS['wrist']


# --------------------------------------------------------------------------
# 2. Where the camera is
# --------------------------------------------------------------------------


def _normalise(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    if length < _EPS:
        raise ValueError('cannot normalise a zero-length direction')
    return (v[0] / length, v[1] / length, v[2] / length)


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def axes_to_quaternion(
    col_x: tuple[float, float, float],
    col_y: tuple[float, float, float],
    col_z: tuple[float, float, float],
) -> tuple[float, float, float, float]:
    """Three perpendicular axes in, one ``(x, y, z, w)`` quaternion out.

    ROS stores rotations as four numbers rather than nine, and rather than as
    three angles, which hit awkward cases in 3D where two axes line up and a
    degree of freedom quietly vanishes. The branching picks whichever of the
    four numbers is largest to divide by: dividing by the small one throws away
    precision, and near some rotations it is very small indeed.

    The three arguments are the columns of the rotation, which is to say the
    three axes of the child frame written in the parent's coordinates.
    """
    m00, m01, m02 = col_x[0], col_y[0], col_z[0]
    m10, m11, m12 = col_x[1], col_y[1], col_z[1]
    m20, m21, m22 = col_x[2], col_y[2], col_z[2]
    trace = m00 + m11 + m22
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        return ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s)
    if m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        return (0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
    if m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        return ((m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s)
    s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
    return ((m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s)


@dataclass(frozen=True)
class Pose:
    """Where the camera is and which way it faces. Usually called ``camera_to_world``.

    A picture on its own says "something is 38 cm in front of me". To know where
    that is in the room you also have to know where "me" was, so every capture
    carries one of these.

    THE AXES ARE NOT THE ONES YOU EXPECT
    ------------------------------------
    ROS uses two different conventions and cameras use the awkward one. A
    **body** frame — the robot, the arm, the base — has ``+X`` forward, ``+Y``
    left and ``+Z`` up. A camera **optical** frame has::

        +X  right, across the picture
        +Y  down,  down the picture
        +Z  forward, the way the lens points

    So a camera's "up" is ``-Y``, and forward is ``Z``, not ``X``. This is not
    ROS being difficult: it is inherited from image coordinates, where pixel
    ``(0, 0)`` is the *top* left and ``v`` counts downwards. Keeping the optical
    frame in the same handedness as the picture is what lets the two formulas at
    the top of this file be as short as they are. The convention is written down
    in REP 103 and REP 145, and frames that use it are named ``..._optical_frame``
    by tradition, exactly so nobody has to guess which of the two is meant.

    :param right: The camera's ``+X``, written in world axes.
    :param down: Its ``+Y``, in world axes.
    :param forward: Its ``+Z``, in world axes.
    :param position: Where the lens is, in world axes, in metres.
    """

    right: tuple[float, float, float]
    down: tuple[float, float, float]
    forward: tuple[float, float, float]
    position: tuple[float, float, float]

    def to_world(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """Take a point measured from the camera and say where it is in the room.

        Read it as a sentence: start at the camera, go ``x`` along its right,
        ``y`` along its down, ``z`` along its forward. That is all a rotation
        does — the three axes are the three directions to walk in.
        """
        x, y, z = point
        return (
            self.position[0] + x * self.right[0] + y * self.down[0] + z * self.forward[0],
            self.position[1] + x * self.right[1] + y * self.down[1] + z * self.forward[1],
            self.position[2] + x * self.right[2] + y * self.down[2] + z * self.forward[2],
        )

    def rotate_to_world(
        self, direction: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        """Turn a *direction* from camera axes into world axes.

        The same as :meth:`to_world` with the final "start at the camera" step
        left out. A direction has no position, so shifting it would be wrong:
        "10 cm to my right" is the same arrow wherever you stand.
        """
        x, y, z = direction
        return (
            x * self.right[0] + y * self.down[0] + z * self.forward[0],
            x * self.right[1] + y * self.down[1] + z * self.forward[1],
            x * self.right[2] + y * self.down[2] + z * self.forward[2],
        )

    def to_camera(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """Take a point in the room and measure it from the camera.

        Subtract the camera's position to get an arrow from the camera to the
        point, then ask how far that arrow goes along each of the camera's own
        three directions. "How far along" is a dot product.

        Undoing a rotation is normally hard work. Here it is three dot products,
        because the three axes are perpendicular and one unit long, which makes
        the inverse of the rotation the same numbers read the other way round.
        """
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        dz = point[2] - self.position[2]
        return (
            dx * self.right[0] + dy * self.right[1] + dz * self.right[2],
            dx * self.down[0] + dy * self.down[1] + dz * self.down[2],
            dx * self.forward[0] + dy * self.forward[1] + dz * self.forward[2],
        )

    def matrix(self) -> tuple[tuple[float, ...], ...]:
        """Give the same thing as the 4x4 table drivers and log files hand around.

        The first three columns are the camera's right, down and forward. The
        last column is where it is. The bottom row is always ``0 0 0 1`` and
        carries no information — it is there so that turning a point and
        shifting it become one multiplication instead of two steps.
        """
        return (
            (self.right[0], self.down[0], self.forward[0], self.position[0]),
            (self.right[1], self.down[1], self.forward[1], self.position[1]),
            (self.right[2], self.down[2], self.forward[2], self.position[2]),
            (0.0, 0.0, 0.0, 1.0),
        )

    def quaternion(self) -> tuple[float, float, float, float]:
        """Return the optical rotation as the ``(x, y, z, w)`` quaternion ROS carries."""
        return axes_to_quaternion(self.right, self.down, self.forward)

    def body_axes(self) -> tuple[tuple[float, float, float], ...]:
        """Give the same camera in the *body* convention: forward, left, up.

        ROS describes a camera with two frames stacked on top of each other, in
        the same place, turned a quarter turn from one another:

        * ``camera_link`` — the body convention, ``+X`` forward, ``+Y`` left,
          ``+Z`` up. This is the one that matches the rest of the robot, so it
          is what the URDF bolts to the wrist.
        * ``camera_link_optical`` — the optical convention this class stores,
          ``+X`` right, ``+Y`` down, ``+Z`` forward. Images are stamped in this
          one, because it is the one the projection formulas assume.

        It looks like duplication and it is not. Each convention is the natural
        one for its job, and the fixed quarter turn between them is published
        once, as a static transform, so nothing else ever has to think about it.
        """
        return (
            self.forward,
            (-self.right[0], -self.right[1], -self.right[2]),
            (-self.down[0], -self.down[1], -self.down[2]),
        )

    def body_quaternion(self) -> tuple[float, float, float, float]:
        """Return the ``camera_link`` rotation, as ``(x, y, z, w)``."""
        forward, left, up = self.body_axes()
        return axes_to_quaternion(forward, left, up)


def look_at(
    eye: tuple[float, float, float],
    target: tuple[float, float, float],
    image_up: tuple[float, float, float] = (0.0, 1.0, 0.0),
) -> Pose:
    """Put a camera at ``eye``, pointed at ``target``, and work out its axes.

    Three steps, in order:

    1. **forward** is the arrow from the camera to what it is looking at.
    2. **right** is perpendicular to forward and to ``image_up``. Crossing two
       directions gives one at right angles to both, which is exactly what is
       wanted here.
    3. **down** is then forced: perpendicular to the other two, and pointing the
       way that keeps the three axes right-handed.

    ``image_up`` only says which way up the picture should be. It is a hint, not
    an axis: the true up is worked out in step 3. It must not be parallel to
    ``forward``, because then step 2 has nothing to cross — for a camera looking
    straight down, world ``+Z`` is exactly the wrong hint and the default
    ``+Y`` is the right one.

    Spinning the camera about the direction it looks only rotates the picture; it
    does not change what is in it. ``image_up`` is what pins that spin down.
    """
    forward = _normalise(
        (target[0] - eye[0], target[1] - eye[1], target[2] - eye[2])
    )
    right = _cross(forward, image_up)
    if math.sqrt(right[0] ** 2 + right[1] ** 2 + right[2] ** 2) < 1e-6:
        raise ValueError('image_up is parallel to the viewing direction; pick another')
    right = _normalise(right)
    down = _cross(forward, right)
    return Pose(right=right, down=down, forward=forward, position=tuple(eye))


#: The fixed rotation from ``camera_link`` to ``camera_link_optical``, as
#: ``(x, y, z, w)``. Every ROS camera driver publishes this exact quaternion,
#: and it is worth recognising on sight: four halves with alternating signs.
OPTICAL_FROM_BODY_QUATERNION = (-0.5, 0.5, -0.5, 0.5)

#: 40 cm straight above the middle of the table, looking down. The reference
#: viewpoint: everything flat reads exactly 0.40 m, which makes the depth
#: pictures easy to check by eye.
TOP_DOWN = look_at((0.0, 0.0, 0.40), (0.0, 0.0, 0.0))

#: The same distance away but leaning in from one side by about 20 degrees, so
#: the sides of the boxes come into view and the table no longer reads one
#: number everywhere.
TILTED = look_at((0.14, 0.0, 0.37), (0.0, 0.0, 0.0))

#: Half as far away, for a second, closer look at one box.
CLOSE_UP = look_at((0.0, 0.0, 0.18), (0.0, 0.0, 0.0))


# --------------------------------------------------------------------------
# 3. Something to photograph
# --------------------------------------------------------------------------


def _shade(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (
        min(255, int(rgb[0] * factor)),
        min(255, int(rgb[1] * factor)),
        min(255, int(rgb[2] * factor)),
    )


@dataclass(frozen=True)
class Hit:
    """What one ray ran into: how far along, what colour, and what it was.

    :param depth_m: Distance along the camera's forward axis, not along the ray.
    :param rgb: The colour the pixel takes.
    :param label: Which object was hit, for the mask capture.
    """

    depth_m: float
    rgb: tuple[int, int, int]
    label: str


@dataclass(frozen=True)
class Box:
    """A box standing on the table, with its sides square to the world axes.

    :param label: Name, used by the mask capture.
    :param rgb: Its colour before shading.
    :param centre: Where it stands on the table, as ``(x, y)`` in metres.
    :param size: How big it is along ``(x, y, z)``, in metres.
    """

    label: str
    rgb: tuple[int, int, int]
    centre: tuple[float, float]
    size: tuple[float, float, float]

    @property
    def top_z(self) -> float:
        """Height of the top face above the table, in metres."""
        return self.size[2]

    def bounds(self) -> tuple[tuple[float, float], ...]:
        """Return the box as a ``(low, high)`` pair per axis."""
        half_x, half_y, height = self.size[0] / 2.0, self.size[1] / 2.0, self.size[2]
        return (
            (self.centre[0] - half_x, self.centre[0] + half_x),
            (self.centre[1] - half_y, self.centre[1] + half_y),
            (0.0, height),
        )

    def intersect(
        self,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
    ) -> tuple[float, int] | None:
        """Where a ray enters this box, if it does. Returns ``(t, axis)``.

        The **slab method**. A box is three pairs of parallel planes. For each
        pair, work out the stretch of the ray that is between them. A ray is
        inside the box only where all three stretches overlap, so intersect them:
        keep the latest entry and the earliest exit. If the entry is still before
        the exit, the ray goes through; if not, it misses.

        The axis that supplied the entry is the face that was hit, which is what
        the shading uses to make the top of a box read brighter than its sides.
        """
        t_near, t_far, near_axis = -math.inf, math.inf, 0
        bounds = self.bounds()
        for axis in range(3):
            low, high = bounds[axis]
            o, d = origin[axis], direction[axis]
            if abs(d) < _EPS:
                # Parallel to this pair of planes: either always between them or
                # never, and no value of t changes that.
                if o < low or o > high:
                    return None
                continue
            t_low, t_high = (low - o) / d, (high - o) / d
            if t_low > t_high:
                t_low, t_high = t_high, t_low
            if t_low > t_near:
                t_near, near_axis = t_low, axis
            t_far = min(t_far, t_high)
            if t_near > t_far:
                return None
        if t_far < _EPS:
            return None
        return (t_near, near_axis) if t_near > _EPS else None


@dataclass(frozen=True)
class Scene:
    """A table with boxes on it. The only thing in this file that is made up.

    A real camera looks at a real room; here the room is three boxes and a
    plane, and a picture is taken by **ray casting**: send one ray out through
    each pixel, see what it hits first, write down the colour and the distance.
    That is the reverse of how light works and much easier to compute, and for
    this purpose it gives the same answer.

    :param boxes: What is standing on the table.
    :param table_z: Height of the table top, in metres.
    :param table_half_m: How far the table reaches from the middle; rays that
        miss it entirely hit nothing and come back with no depth.
    """

    boxes: tuple[Box, ...]
    table_z: float = 0.0
    table_half_m: float = 0.60

    def table_colour(self, x: float, y: float) -> tuple[int, int, int]:
        """Grey, with a darker line every 5 cm.

        The grid is not decoration. It is a ruler laid on the table, so that a
        change of lens or of resolution shows up as a visible change in how much
        of it fits and how finely it is sampled.
        """
        half_line = TABLE_GRID_WIDTH_M / 2.0
        for value in (x, y):
            nearest = round(value / TABLE_GRID_SPACING_M) * TABLE_GRID_SPACING_M
            if abs(value - nearest) < half_line:
                return TABLE_GRID_RGB
        return TABLE_RGB

    def trace(
        self,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
    ) -> Hit | None:
        """Send one ray into the scene and return the nearest thing it hits.

        ``direction`` is expected to come from :meth:`CameraConfig.ray` turned
        into world axes — that is, *not* scaled to unit length, with a forward
        component of 1 in camera axes. That is what makes the returned ``t`` the
        depth the camera would report, with no extra arithmetic.
        """
        best: Hit | None = None
        best_t = math.inf

        if abs(direction[2]) > _EPS:
            t = (self.table_z - origin[2]) / direction[2]
            if _EPS < t < best_t:
                x = origin[0] + t * direction[0]
                y = origin[1] + t * direction[1]
                if abs(x) <= self.table_half_m and abs(y) <= self.table_half_m:
                    best_t = t
                    best = Hit(t, self.table_colour(x, y), 'table')

        for box in self.boxes:
            found = box.intersect(origin, direction)
            if found is not None and found[0] < best_t:
                best_t = found[0]
                best = Hit(found[0], _shade(box.rgb, FACE_SHADE[found[1]]), box.label)

        return best


#: The scene every picture in this area is taken of. Three boxes of three
#: different heights, so a depth picture has something to show.
TABLE_SCENE = Scene(
    boxes=(
        Box('red', (196, 64, 54), (0.065, 0.040), (0.06, 0.06, 0.06)),
        Box('green', (72, 160, 84), (-0.060, 0.048), (0.05, 0.05, 0.09)),
        Box('blue', (58, 110, 200), (-0.040, -0.062), (0.09, 0.05, 0.04)),
    ),
)

#: The simplest version of the problem: only the red box, standing exactly where
#: it stands in TABLE_SCENE. Every idea is shown on this first, so that the only
#: thing the three-box scene adds is having more than one thing to tell apart.
ONE_BOX_SCENE = Scene(boxes=(TABLE_SCENE.boxes[0],))


# --------------------------------------------------------------------------
# 4. Taking a picture
# --------------------------------------------------------------------------

#: Characters used by :meth:`Capture.ascii_art`, darkest first.
_RAMP = ' .:-=+*#%@'

#: First letter of each object, for the labelled mask preview.
_LABEL_CHARS = {'table': '.', 'red': 'R', 'green': 'G', 'blue': 'B'}


@dataclass(frozen=True)
class Capture:
    """One shot, and every kind of picture that can be pulled out of it.

    A driver hands back one of these — colour, depth, the intrinsics that were
    in force, and where the camera was — and they belong together. Split them up
    and the depth numbers become unusable: they only mean something alongside
    the lens that produced them and the pose they were taken from.

    Pictures are stored as rows of pixels, top row first, which is the order the
    picture is read in and the order the ROS message stores.

    :param config: The lens this was taken through.
    :param pose: Where the camera was, as ``camera_to_world``.
    :param rgb: Rows of ``(r, g, b)``, each 0-255.
    :param depth: Rows of metres, or ``None`` where nothing was measured.
    :param labels: Rows of object names, or ``None`` where nothing was hit. Not
        something a real camera gives you — it comes free from a simulator, and
        it is what makes a scene like this useful for checking working code.
    """

    config: CameraConfig
    pose: Pose
    rgb: tuple[tuple[tuple[int, int, int], ...], ...]
    depth: tuple[tuple[float | None, ...], ...]
    labels: tuple[tuple[str | None, ...], ...]

    # -- reading one pixel -------------------------------------------------

    def depth_at(self, u: float, v: float) -> float | None:
        """How far away pixel ``(u, v)`` is, in metres, or ``None`` for no reading.

        Measured **along the camera's forward axis**, not along the slanted line
        from the lens to the point. That is why the whole table reads exactly
        0.40 m from the top-down camera, corners included, even though the
        corners are further from the lens than the middle is.

        The distinction matters because :meth:`CameraConfig.deproject` assumes
        it. Feed it a straight-line distance and every point comes out slightly
        too far away, worst at the edges of the picture.
        """
        return self.depth[int(v)][int(u)]

    def rgb_at(self, u: float, v: float) -> tuple[int, int, int]:
        """Return the colour of pixel ``(u, v)``."""
        return self.rgb[int(v)][int(u)]

    def label_at(self, u: float, v: float) -> str | None:
        """Which object pixel ``(u, v)`` landed on."""
        return self.labels[int(v)][int(u)]

    def pixel_to_world(self, u: float, v: float) -> tuple[float, float, float] | None:
        """Pixel in, point in the room out. The whole point of a depth camera.

        Two steps, and they are the two halves of this file:

        1. :meth:`CameraConfig.deproject` uses the depth reading to turn the
           pixel back into a point measured from the camera.
        2. :meth:`Pose.to_world` moves that point into the room's axes.

        Returns ``None`` where the pixel has no depth reading, which is the
        honest answer and the one worth propagating — a missing depth silently
        treated as zero puts a point inside the lens.
        """
        depth_m = self.depth_at(u, v)
        if depth_m is None:
            return None
        return self.pose.to_world(self.config.deproject(u, v, depth_m))

    # -- the different kinds of picture ------------------------------------

    def mono8(self) -> tuple[tuple[int, ...], ...]:
        """Reduce the colour picture to one grey number a pixel: ROS encoding ``mono8``.

        The weights are not thirds. The eye is far more sensitive to green than
        to blue, so matching brightness to what a person sees means weighting
        them 0.299, 0.587 and 0.114. A third of each gives a picture that is
        technically an average and looks wrong.

        Worth having because a third of the data is a third of the bandwidth,
        and plenty of vision work — edges, corners, tracking — never looks at
        colour at all.
        """
        return tuple(
            tuple(int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in row)
            for row in self.rgb
        )

    def depth_millimetres(self) -> tuple[tuple[int, ...], ...]:
        """Convert the depth picture to whole millimetres: ROS encoding ``16UC1``.

        The other depth encoding in common use, and the source of a reliable
        class of bug. ``32FC1`` stores metres as decimals and says "no reading"
        with ``NaN``; ``16UC1`` stores millimetres as whole numbers and says it
        with ``0``. Read a ``16UC1`` picture as though it were metres and
        everything is a thousand times too far away. Forget that ``0`` is a
        missing reading and holes in the depth turn into points sitting exactly
        at the lens.

        Which one you get depends on the camera, so both are worth recognising.
        """
        return tuple(
            tuple(0 if d is None else int(round(d * 1000.0)) for d in row)
            for row in self.depth
        )

    def mask(self, label: str) -> tuple[tuple[bool, ...], ...]:
        """Which pixels landed on one named object.

        Free here because the scene is known. On a real camera this is the hard
        part, and it is what the colour picture is usually for: pick the pixels
        that belong to the thing you care about, then read only their depths.
        """
        return tuple(tuple(cell == label for cell in row) for row in self.labels)

    def point_cloud(
        self, step: int = 1, in_world: bool = True
    ) -> list[tuple[float, float, float, tuple[int, int, int]]]:
        """Every pixel with a depth reading, deprojected into a 3D point.

        This is the fourth kind of capture, and the one the rest of a robot
        actually uses. A picture is a grid of directions; a point cloud is the
        same information as a bag of places, which is what you can measure,
        group and grasp.

        :param step: Take every ``step``-th pixel in each direction. A 320x240
            picture is 76,800 points, and for most purposes every fourth pixel
            in each direction — one sixteenth of them — is plenty.
        :param in_world: Give points in the room's axes. Set ``False`` to keep
            them measured from the camera, which is what the ROS message on
            ``/camera/points`` carries: the message names its frame in the
            header and leaves the moving to whoever reads it.
        """
        points = []
        for row in range(0, self.config.height_px, step):
            for col in range(0, self.config.width_px, step):
                depth_m = self.depth[row][col]
                if depth_m is None:
                    continue
                u, v = col + 0.5, row + 0.5
                point = self.config.deproject(u, v, depth_m)
                if in_world:
                    point = self.pose.to_world(point)
                points.append((point[0], point[1], point[2], self.rgb[row][col]))
        return points

    def measure(self, label: str) -> tuple[float, float, float] | None:
        """Measure one object from this capture: where it stands, and how tall.

        This is the whole point of the area in a few lines. Deproject every
        pixel that landed on the object, move each point into the room, keep
        the highest ones — its top — and average them. The average of the top
        is the middle of the object, and the top's height is how tall it is.

        Nothing about the object is looked up. Only its pixels, their depth
        readings, the four lens numbers and where the camera was.

        :param label: Which object, as named in the mask.
        :returns: ``(x, y, height)`` in metres in the room, or ``None`` if no
            pixel landed on it.
        """
        points = []
        for row in range(self.config.height_px):
            for col in range(self.config.width_px):
                depth_m = self.depth[row][col]
                if self.labels[row][col] != label or depth_m is None:
                    continue
                points.append(self.pose.to_world(
                    self.config.deproject(col + 0.5, row + 0.5, depth_m)))
        if not points:
            return None
        # Pixels at the object's edge catch a strip of its side. Those sit
        # lower than the top, so keep only points within a millimetre of it.
        top_z = max(p[2] for p in points)
        top = [p for p in points if p[2] > top_z - 0.001]
        x = sum(p[0] for p in top) / len(top)
        y = sum(p[1] for p in top) / len(top)
        return (x, y, top_z)

    # -- looking at it in a terminal ---------------------------------------

    def depth_range(self) -> tuple[float, float] | None:
        """Nearest and furthest depth reading, or ``None`` if there are none."""
        values = [d for row in self.depth for d in row if d is not None]
        if not values:
            return None
        return (min(values), max(values))

    def valid_depth_fraction(self) -> float:
        """Report what share of the picture came back with a depth reading, 0 to 1.

        Never 1 on a real depth camera. Shiny surfaces, dark surfaces, glass and
        anything past the sensor's range come back empty, and code that assumes
        otherwise breaks the first time it meets a window.
        """
        total = self.config.pixel_count
        valid = sum(1 for row in self.depth for d in row if d is not None)
        return valid / total if total else 0.0

    def ascii_art(self, kind: str = 'rgb', cols: int = 40) -> list[str]:
        """Draw the picture in the terminal, in one of three ways.

        Not a serious viewer — it is here so that running the walkthrough shows
        an actual picture rather than describing one.

        :param kind: ``'rgb'`` shades by brightness, ``'depth'`` shades by
            nearness (denser characters are closer), ``'label'`` prints the
            first letter of whatever each pixel landed on.
        :param cols: How many characters wide to draw it.
        """
        step = max(1, self.config.width_px // cols)
        # Terminal characters are about twice as tall as they are wide, so
        # sampling rows half as often keeps the picture from looking stretched.
        row_step = max(1, step * 2)
        span = self.depth_range()

        lines = []
        for row in range(0, self.config.height_px, row_step):
            line = []
            for col in range(0, self.config.width_px, step):
                if kind == 'label':
                    label = self.labels[row][col]
                    line.append(' ' if label is None else _LABEL_CHARS.get(label, '?'))
                    continue
                if kind == 'depth':
                    depth_m = self.depth[row][col]
                    if depth_m is None or span is None or span[1] - span[0] < _EPS:
                        line.append(' ' if depth_m is None else _RAMP[-1])
                        continue
                    # Near reads dense, far reads sparse.
                    nearness = (span[1] - depth_m) / (span[1] - span[0])
                    line.append(_RAMP[int(nearness * (len(_RAMP) - 1))])
                    continue
                r, g, b = self.rgb[row][col]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                line.append(_RAMP[int(brightness * (len(_RAMP) - 1))])
            lines.append(''.join(line))
        return lines


def capture(
    scene: Scene = TABLE_SCENE,
    config: CameraConfig = WRIST,
    pose: Pose = TOP_DOWN,
) -> Capture:
    """Take one picture: colour and depth together, from one place, at one moment.

    One ray per pixel, through the middle of that pixel. Pixel ``(0, 0)`` covers
    the square from 0 to 1, so its middle is at ``(0.5, 0.5)`` — hence the
    ``+ 0.5`` below. Half a pixel sounds like a rounding detail; at the edge of
    a box it is the difference between measuring the box and measuring the table
    behind it.

    The ray from :meth:`CameraConfig.ray` has a forward component of exactly 1,
    so however far along it the scene is hit, that distance *is* the depth the
    camera reports. Rotating the ray into world axes does not change that,
    because rotating does not stretch.

    Readings outside the sensor's range are dropped rather than clamped. A depth
    camera that cannot see something reports nothing, and pretending otherwise
    invents surfaces at exactly the near or far limit.
    """
    origin = pose.position
    near, far = config.depth_min_m, config.depth_max_m

    rgb_rows, depth_rows, label_rows = [], [], []
    for row in range(config.height_px):
        v = row + 0.5
        rgb_row, depth_row, label_row = [], [], []
        for col in range(config.width_px):
            direction = pose.rotate_to_world(config.ray(col + 0.5, v))
            hit = scene.trace(origin, direction)
            if hit is None:
                rgb_row.append((0, 0, 0))
                depth_row.append(None)
                label_row.append(None)
                continue
            rgb_row.append(hit.rgb)
            in_range = near <= hit.depth_m <= far
            depth_row.append(hit.depth_m if in_range else None)
            label_row.append(hit.label)
        rgb_rows.append(tuple(rgb_row))
        depth_rows.append(tuple(depth_row))
        label_rows.append(tuple(label_row))

    return Capture(
        config=config,
        pose=pose,
        rgb=tuple(rgb_rows),
        depth=tuple(depth_rows),
        labels=tuple(label_rows),
    )
