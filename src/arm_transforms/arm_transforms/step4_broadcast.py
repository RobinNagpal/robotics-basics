"""Step 4: hand the arm's frames over to TF, so RViz can draw it.

Run it:  make arm.demo   (or: ros2 run arm_transforms arm_step4_broadcast)

THE IDEA
--------
Steps 1 to 3 were plain Python. Nothing was shared, and nothing else could ask
where the gripper was. This step publishes the *same* transforms from
``arm_math`` onto ``/tf``, where any program on the robot can use them.

What changes: nothing about the maths. ``arm_transforms(q1, q2)`` is imported
unchanged. The node only turns each link into a ROS message and sends it.

WHAT GETS SENT
--------------
Three transforms, once per tick::

    base_link -> upper_arm      turn by q1
    upper_arm -> forearm        move L1, turn by q2
    forearm   -> gripper        move L2

Notice we publish each link on its own, exactly as written in step 2. We never
publish base_link->gripper. Anyone who wants it asks TF, and TF joins the chain.
That is step 5.

AND THE SHAPES
--------------
The arm is drawn with markers, and each one is placed **in the frame it belongs
to**: the upper arm box is described in ``upper_arm`` and never moves in that
frame. TF moves the frame; the box follows. Same idea as the ball in the RViz
area, now with five shapes instead of one.

ROTATIONS IN ROS
----------------
ROS stores a rotation as four numbers, a quaternion, rather than an angle. Our
arm is flat, so only a turn about the up axis is needed, which lands in the
third and fourth slots. ``yaw_to_quaternion`` does the conversion.
"""

from __future__ import annotations

import math

from arm_transforms.arm_math import arm_transforms, LINK1_M, LINK2_M, yaw_to_quaternion
from geometry_msgs.msg import TransformStamped
from rcl_interfaces.msg import ParameterDescriptor
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray

MARKER_TOPIC = 'arm_markers'
LINK_THICKNESS_M = 0.06


class ArmBroadcaster(Node):
    """Swing the two joints, and publish the arm's frames and shapes."""

    def __init__(self) -> None:
        """Read the settings, then start the broadcaster, publisher and timer."""
        super().__init__('arm_broadcaster')

        rate_hz = self._float_param('publish_rate_hz', 30.0, 'Updates per second.')
        self._shoulder_swing = self._float_param(
            'shoulder_swing_deg', 45.0, 'How far the shoulder swings each way.')
        self._elbow_swing = self._float_param(
            'elbow_swing_deg', 60.0, 'How far the elbow swings each way.')
        self._shoulder_period = self._float_param(
            'shoulder_period_s', 8.0, 'Seconds for one shoulder swing cycle.')
        self._elbow_period = self._float_param(
            'elbow_period_s', 5.0, 'Seconds for one elbow swing cycle.')

        self._tf_broadcaster = TransformBroadcaster(self)
        self._marker_pub = self.create_publisher(MarkerArray, MARKER_TOPIC, 10)

        self._start_time = self.get_clock().now()
        self.create_timer(1.0 / rate_hz, self._on_timer)

        self.get_logger().info(
            f'Publishing base_link -> upper_arm -> forearm -> gripper '
            f"and shapes on '{MARKER_TOPIC}' at {rate_hz:g} Hz"
        )

    def _float_param(self, name: str, default: float, description: str) -> float:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().double_value

    def joint_angles(self, elapsed_s: float) -> tuple[float, float]:
        """Swing both joints back and forth, at different speeds.

        The two periods do not divide into each other, so the arm keeps
        producing new poses instead of repeating a short loop.
        """
        q1 = math.radians(self._shoulder_swing) * math.sin(
            2.0 * math.pi * elapsed_s / self._shoulder_period)
        q2 = math.radians(self._elbow_swing) * math.sin(
            2.0 * math.pi * elapsed_s / self._elbow_period)
        return q1, q2

    def _on_timer(self) -> None:
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds * 1e-9
        q1, q2 = self.joint_angles(elapsed_s)

        # One message per link, straight from the same list step 2 used.
        transforms = [
            self._to_message(now, parent, child, link)
            for parent, child, link in arm_transforms(q1, q2)
        ]
        self._tf_broadcaster.sendTransform(transforms)
        self._marker_pub.publish(self._build_markers(now))

    def _to_message(self, stamp, parent: str, child: str, link) -> TransformStamped:
        """Turn one Transform2D into the ROS message TF expects."""
        message = TransformStamped()
        message.header.stamp = stamp.to_msg()
        message.header.frame_id = parent
        message.child_frame_id = child
        message.transform.translation.x = link.x
        message.transform.translation.y = link.y
        message.transform.translation.z = 0.0
        (
            message.transform.rotation.x,
            message.transform.rotation.y,
            message.transform.rotation.z,
            message.transform.rotation.w,
        ) = yaw_to_quaternion(link.theta)
        return message

    def _build_markers(self, stamp) -> MarkerArray:
        """Draw two link boxes and three joint balls, each in its own frame."""
        return MarkerArray(markers=[
            self._bar(stamp, 0, 'upper_arm', LINK1_M, (0.25, 0.55, 0.95)),
            self._bar(stamp, 1, 'forearm', LINK2_M, (0.25, 0.75, 0.95)),
            self._ball(stamp, 2, 'upper_arm', 0.09, (0.95, 0.75, 0.15)),
            self._ball(stamp, 3, 'forearm', 0.09, (0.95, 0.75, 0.15)),
            self._ball(stamp, 4, 'gripper', 0.07, (0.95, 0.35, 0.35)),
        ])

    def _bar(self, stamp, marker_id: int, frame: str, length: float, rgb) -> Marker:
        """Draw a link as a box lying along its own frame's X axis."""
        marker = self._blank(stamp, marker_id, frame, Marker.CUBE, rgb)
        # Half the length along X, so the box starts at the joint rather than
        # being centred on it.
        marker.pose.position.x = length / 2.0
        marker.scale.x = length
        marker.scale.y = LINK_THICKNESS_M
        marker.scale.z = LINK_THICKNESS_M
        return marker

    def _ball(self, stamp, marker_id: int, frame: str, size: float, rgb) -> Marker:
        """Draw a joint as a ball at its frame's origin."""
        marker = self._blank(stamp, marker_id, frame, Marker.SPHERE, rgb)
        marker.scale.x = marker.scale.y = marker.scale.z = size
        return marker

    def _blank(self, stamp, marker_id: int, frame: str, shape: int, rgb) -> Marker:
        marker = Marker()
        marker.header.stamp = stamp.to_msg()
        marker.header.frame_id = frame
        marker.ns = 'arm'
        marker.id = marker_id
        marker.type = shape
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.color.r, marker.color.g, marker.color.b = rgb
        marker.color.a = 1.0
        return marker


def main(args: list[str] | None = None) -> None:
    """Entry point for ``ros2 run arm_transforms arm_step4_broadcast``."""
    rclpy.init(args=args)
    node = ArmBroadcaster()
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
