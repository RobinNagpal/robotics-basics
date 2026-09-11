"""Publish the camera from :mod:`camera_basics.camera` as real ROS 2 messages.

Run it:  make camera.demo

The camera itself is next door in ``camera.py``, with no ROS in it. This file is
only the packaging: it takes the pictures that module produces and puts them on
topics in the shape RViz and the rest of the ecosystem expect.

That split is the point. Swap this node's ray-cast scene for a Gazebo plugin or
a real RealSense driver and the topics below do not change, which is why a
pipeline written against them keeps working.

What it publishes::

    /camera/image_raw          sensor_msgs/Image        rgb8
    /camera/depth/image_raw    sensor_msgs/Image        32FC1, metres
    /camera/camera_info        sensor_msgs/CameraInfo   fx, fy, cx, cy
    /camera/points             sensor_msgs/PointCloud2  xyz + rgb
    /tf                        world -> camera_link
    /tf_static                 camera_link -> camera_link_optical

**Four topics, one moment.** They all carry the same timestamp, and they have to:
a depth picture is only meaningful next to the intrinsics that produced it and
the pose it was taken from. Anything downstream matches them up by that stamp.

**Why the images are stamped in the optical frame.** ``camera_link`` is the
body-convention frame, the one the URDF bolts to a wrist. Images are stamped in
``camera_link_optical``, a quarter turn away, because that is the frame the
projection arithmetic assumes. See :meth:`camera_basics.camera.Pose.body_axes`.

**Why the point cloud is in camera coordinates.** It is stamped in the optical
frame and left there. RViz moves it, by looking up TF — the same lesson as the
rviz area, where the ball never moves and its frame does.
"""

from __future__ import annotations

import array
import math
import struct

from camera_basics.camera import (
    CameraConfig,
    capture,
    look_at,
    OPTICAL_FROM_BODY_QUATERNION,
    TABLE_SCENE,
)
from geometry_msgs.msg import TransformStamped
from rcl_interfaces.msg import ParameterDescriptor
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

#: Bytes per point in the cloud: three float32 for the position, four more for
#: the packed colour.
POINT_STEP = 16


class CameraPublisher(Node):
    """Renders one RGB-D frame per tick and publishes it four ways."""

    def __init__(self) -> None:
        """Declare parameters, build the publishers, and start the timer."""
        super().__init__('camera_publisher')

        self._world_frame = self._str_param('world_frame', 'world', 'Fixed frame for RViz.')
        self._body_frame = self._str_param(
            'camera_frame', 'camera_link', 'Body-convention camera frame: X forward, Z up.'
        )
        self._optical_frame = self._str_param(
            'optical_frame', 'camera_link_optical', 'Frame the images are stamped in.'
        )

        width = self._int_param('width_px', 160, 'Picture width, in pixels.')
        height = self._int_param('height_px', 120, 'Picture height, in pixels.')
        hfov_deg = self._float_param('hfov_deg', 60.0, 'Horizontal field of view, degrees.')
        self._config = CameraConfig('demo', width, height, hfov_deg)

        self._height_m = self._float_param('camera_height_m', 0.40, 'Height above the table.')
        self._radius_m = self._float_param('orbit_radius_m', 0.13, 'How far the camera leans out.')
        self._period_s = self._float_param('orbit_period_s', 20.0, 'Seconds per lap.')
        self._cloud_step = self._int_param('cloud_step', 2, 'Take every Nth pixel for the cloud.')
        rate_hz = self._float_param('publish_rate_hz', 2.0, 'Frames per second.')

        self._rgb_pub = self.create_publisher(Image, 'camera/image_raw', 10)
        self._depth_pub = self.create_publisher(Image, 'camera/depth/image_raw', 10)
        self._info_pub = self.create_publisher(CameraInfo, 'camera/camera_info', 10)
        self._cloud_pub = self.create_publisher(PointCloud2, 'camera/points', 10)

        self._tf = TransformBroadcaster(self)
        # The turn between the two conventions never changes, so it goes out
        # once on /tf_static rather than every frame. Latched, so RViz picks it
        # up whenever it starts.
        self._static_tf = StaticTransformBroadcaster(self)
        self._static_tf.sendTransform(self._build_optical_transform())

        self._start_time = self.get_clock().now()
        self._timer = self.create_timer(1.0 / rate_hz, self._on_timer)

        self.get_logger().info(
            f'Publishing {width}x{height} RGB-D at {rate_hz:g} Hz: '
            f'fx = {self._config.fx:.1f} px, {hfov_deg:g}° across, '
            f'{self._config.metres_per_pixel(self._height_m) * 1000:.2f} mm per pixel'
        )

    # -- parameter helpers -------------------------------------------------

    def _str_param(self, name: str, default: str, description: str) -> str:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().string_value

    def _int_param(self, name: str, default: int, description: str) -> int:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().integer_value

    def _float_param(self, name: str, default: float, description: str) -> float:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().double_value

    # -- periodic work -----------------------------------------------------

    def _on_timer(self) -> None:
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds * 1e-9

        # Lean out and walk slowly round, always looking at the middle of the
        # table. Nothing in the scene moves; only the viewpoint does.
        angle = 2.0 * math.pi * (elapsed_s / self._period_s)
        eye = (
            self._radius_m * math.cos(angle),
            self._radius_m * math.sin(angle),
            self._height_m,
        )
        pose = look_at(eye, (0.0, 0.0, 0.0))
        shot = capture(TABLE_SCENE, self._config, pose)

        stamp = now.to_msg()
        self._tf.sendTransform(self._build_camera_transform(stamp, pose))
        self._info_pub.publish(self._build_camera_info(stamp))
        self._rgb_pub.publish(self._build_rgb_image(stamp, shot))
        self._depth_pub.publish(self._build_depth_image(stamp, shot))
        self._cloud_pub.publish(self._build_point_cloud(stamp, shot))

    # -- transforms --------------------------------------------------------

    def _build_camera_transform(self, stamp, pose) -> TransformStamped:
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self._world_frame
        transform.child_frame_id = self._body_frame
        (
            transform.transform.translation.x,
            transform.transform.translation.y,
            transform.transform.translation.z,
        ) = pose.position
        (
            transform.transform.rotation.x,
            transform.transform.rotation.y,
            transform.transform.rotation.z,
            transform.transform.rotation.w,
        ) = pose.body_quaternion()
        return transform

    def _build_optical_transform(self) -> TransformStamped:
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self._body_frame
        transform.child_frame_id = self._optical_frame
        # Same place, quarter turn round: no translation, only a rotation.
        (
            transform.transform.rotation.x,
            transform.transform.rotation.y,
            transform.transform.rotation.z,
            transform.transform.rotation.w,
        ) = OPTICAL_FROM_BODY_QUATERNION
        return transform

    # -- messages ----------------------------------------------------------

    def _stamp_header(self, message, stamp) -> None:
        message.header.stamp = stamp
        message.header.frame_id = self._optical_frame

    def _build_camera_info(self, stamp) -> CameraInfo:
        config = self._config
        info = CameraInfo()
        self._stamp_header(info, stamp)
        info.width = config.width_px
        info.height = config.height_px
        # An ideal lens: no barrel distortion to undo. A real driver ships the
        # five numbers a calibration produced, and they are rarely all zero.
        info.distortion_model = 'plumb_bob'
        info.d = [0.0] * 5
        # The four intrinsics, laid out as a 3x3 read row by row.
        info.k = [config.fx, 0.0, config.cx, 0.0, config.fy, config.cy, 0.0, 0.0, 1.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.p = [
            config.fx, 0.0, config.cx, 0.0,
            0.0, config.fy, config.cy, 0.0,
            0.0, 0.0, 1.0, 0.0,
        ]
        return info

    def _build_rgb_image(self, stamp, shot) -> Image:
        message = Image()
        self._stamp_header(message, stamp)
        message.width = self._config.width_px
        message.height = self._config.height_px
        message.encoding = 'rgb8'
        message.is_bigendian = 0
        # `step` is the bytes in one row. Three bytes a pixel here; getting it
        # wrong shears the picture diagonally, which is a recognisable symptom.
        message.step = message.width * 3
        # array('B', ...) is the fast path rclpy takes for a uint8[] field; a
        # plain list makes it validate every byte one at a time.
        message.data = array.array(
            'B', bytes(value for row in shot.rgb for pixel in row for value in pixel)
        )
        return message

    def _build_depth_image(self, stamp, shot) -> Image:
        message = Image()
        self._stamp_header(message, stamp)
        message.width = self._config.width_px
        message.height = self._config.height_px
        # One 32-bit float of metres per pixel. The other common encoding is
        # 16UC1 in millimetres; consumers key off this string, so it has to be
        # honest about what the bytes are.
        message.encoding = '32FC1'
        message.is_bigendian = 0
        message.step = message.width * 4
        values = [
            math.nan if depth is None else depth for row in shot.depth for depth in row
        ]
        # NaN, not 0, for "no reading": 0 would put a surface inside the lens.
        message.data = array.array('B', struct.pack(f'<{len(values)}f', *values))
        return message

    def _build_point_cloud(self, stamp, shot) -> PointCloud2:
        # Left in camera coordinates and stamped in the optical frame, exactly
        # as a real driver does. RViz moves it by looking up TF.
        points = shot.point_cloud(step=self._cloud_step, in_world=False)

        cloud = PointCloud2()
        self._stamp_header(cloud, stamp)
        # An unordered cloud: one row of however many points survived. Pixels
        # with no depth reading are simply not in it, which is why the count
        # varies and why `is_dense` can stay true.
        cloud.height = 1
        cloud.width = len(points)
        cloud.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            # Colour goes in as four bytes declared FLOAT32 but read as
            # 0x00RRGGBB. It is a wart of the format, and it is what RViz's
            # "Color Transformer: RGB8" expects to find.
            PointField(name='rgb', offset=12, datatype=PointField.FLOAT32, count=1),
        ]
        cloud.is_bigendian = False
        cloud.point_step = POINT_STEP
        cloud.row_step = POINT_STEP * cloud.width
        cloud.is_dense = True
        cloud.data = array.array('B', b''.join(
            struct.pack('<fffI', x, y, z, (colour[0] << 16) | (colour[1] << 8) | colour[2])
            for x, y, z, colour in points
        ))
        return cloud


def main(args: list[str] | None = None) -> None:
    """Entry point registered as the ``camera_publisher`` console script."""
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
