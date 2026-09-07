"""Publish a moving TF frame plus an RViz marker attached to that frame.

This is the smallest example that still exercises the two mechanisms nearly
every RViz visualisation is built on:

1. a **TF tree**, which tells RViz where things are, and
2. a **topic of drawable primitives** (``visualization_msgs/Marker``), which
   tells RViz what to draw.

Graph produced by this node::

    world ──TF──▶ marker_frame          (broadcast at ``publish_rate_hz``)
    /visualization_marker               (Marker, stamped in ``marker_frame``)

The marker sits at the *origin* of ``marker_frame`` and never moves in its own
frame — RViz animates it purely by resolving TF. That is exactly how a real
robot's meshes move, so the pattern here scales up unchanged.
"""

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker

#: Topic RViz's Marker display subscribes to by default.
MARKER_TOPIC = 'visualization_marker'


def circular_orbit(elapsed_s: float, radius_m: float, period_s: float) -> tuple[float, float, float]:
    """Return the ``(x, y, yaw)`` pose of a body orbiting the origin.

    Kept as a free function — with no ROS types in its signature — so the
    trajectory can be unit tested without spinning up a node. Swap this out for
    a different path (lissajous, waypoint follower, a real controller) and the
    rest of the node is unaffected.

    :param elapsed_s: Seconds since the motion started.
    :param radius_m: Orbit radius, in metres.
    :param period_s: Seconds for one full revolution.
    :returns: ``(x, y, yaw)``, where ``yaw`` points along the direction of travel.
    """
    angle = 2.0 * math.pi * (elapsed_s / period_s)
    # +pi/2 makes the frame's +X axis tangent to the circle, i.e. "forwards".
    return radius_m * math.cos(angle), radius_m * math.sin(angle), angle + math.pi / 2.0


def yaw_to_quaternion(yaw: float) -> tuple[float, float, float, float]:
    """Convert a yaw-only rotation to a ``(x, y, z, w)`` quaternion."""
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class MarkerPublisher(Node):
    """Broadcasts ``world -> marker_frame`` and draws a sphere on that frame."""

    def __init__(self) -> None:
        super().__init__('marker_publisher')

        self._world_frame = self._declare_str('world_frame', 'world', 'Fixed frame RViz displays in.')
        self._marker_frame = self._declare_str('marker_frame', 'marker_frame', 'Moving child frame.')
        rate_hz = self._declare_float('publish_rate_hz', 30.0, 'TF and marker broadcast rate.')
        self._radius_m = self._declare_float('orbit_radius_m', 2.0, 'Orbit radius in metres.')
        self._period_s = self._declare_float('orbit_period_s', 6.0, 'Seconds per revolution.')
        self._diameter_m = self._declare_float('marker_diameter_m', 0.4, 'Sphere diameter in metres.')

        self._tf_broadcaster = TransformBroadcaster(self)
        # Default QoS (reliable, volatile, depth 10) matches what the RViz Marker
        # display expects; the marker is republished every tick, so a late-joining
        # RViz picks it up within one period without needing transient-local.
        self._marker_pub = self.create_publisher(Marker, MARKER_TOPIC, 10)

        self._start_time = self.get_clock().now()
        self._timer = self.create_timer(1.0 / rate_hz, self._on_timer)

        self.get_logger().info(
            f"Publishing TF '{self._world_frame}' -> '{self._marker_frame}' "
            f"and markers on '{MARKER_TOPIC}' at {rate_hz:g} Hz"
        )

    # -- parameter helpers -------------------------------------------------

    def _declare_str(self, name: str, default: str, description: str) -> str:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().string_value

    def _declare_float(self, name: str, default: float, description: str) -> float:
        self.declare_parameter(name, default, ParameterDescriptor(description=description))
        return self.get_parameter(name).get_parameter_value().double_value

    # -- periodic work -----------------------------------------------------

    def _on_timer(self) -> None:
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds * 1e-9
        x, y, yaw = circular_orbit(elapsed_s, self._radius_m, self._period_s)

        self._tf_broadcaster.sendTransform(self._build_transform(now, x, y, yaw))
        self._marker_pub.publish(self._build_marker(now))

    def _build_transform(self, stamp, x: float, y: float, yaw: float) -> TransformStamped:
        transform = TransformStamped()
        transform.header.stamp = stamp.to_msg()
        transform.header.frame_id = self._world_frame
        transform.child_frame_id = self._marker_frame
        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = 0.0
        (
            transform.transform.rotation.x,
            transform.transform.rotation.y,
            transform.transform.rotation.z,
            transform.transform.rotation.w,
        ) = yaw_to_quaternion(yaw)
        return transform

    def _build_marker(self, stamp) -> Marker:
        marker = Marker()
        marker.header.stamp = stamp.to_msg()
        # Stamped in the *moving* frame, at its origin — TF supplies the motion.
        marker.header.frame_id = self._marker_frame
        # (ns, id) is the marker's identity: reuse it to update, vary it to add
        # more markers to the same topic.
        marker.ns = 'rviz_basics'
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = self._diameter_m
        marker.scale.y = self._diameter_m
        marker.scale.z = self._diameter_m
        marker.color.r = 0.1
        marker.color.g = 0.6
        marker.color.b = 1.0
        marker.color.a = 1.0  # alpha 0 renders nothing — a classic silent failure
        # lifetime defaults to 0 == never auto-expire.
        return marker


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MarkerPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # Ctrl-C may already have torn the context down; shutting down twice raises.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
