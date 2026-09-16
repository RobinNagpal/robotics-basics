"""Frames: saying where the parts of a robot are, and asking where they are.

Every position a robot works with is measured from somewhere: the room, the
base, the camera, the gripper. Each of those is a **frame**, a set of axes, and
the same point has different numbers in each one. **TF** is the part of ROS that
keeps track of how the frames sit relative to each other, so that no node has to
work it out.

This one node does both halves of TF:

  broadcasting  it publishes where "tool" is inside "base_link", twice a second,
                with the tool going slowly round in a circle
  looking up    it asks TF where "tool" is, and prints the answer

In a real robot those two halves are in different programs, usually many of
them, and that is the point: nobody has to know the whole chain.

Run it with:  ros2 run ros_basics basics_frames

Then from another terminal (after `make shell`):

  ros2 run tf2_ros tf2_echo base_link tool     the same lookup, from the command line
  ros2 topic echo /tf                          the raw messages
  ros2 run tf2_tools view_frames               draw the tree of frames as a PDF
"""

import math

from geometry_msgs.msg import TransformStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from rclpy.timer import Timer
from tf2_ros import Buffer, TransformBroadcaster, TransformException, TransformListener

# The circle the tool travels: its radius in metres, and its period in seconds.
RADIUS: float = 0.30
PERIOD: float = 8.0


class Frames(Node):
    """Publish one moving frame, and look it up again."""

    def __init__(self) -> None:
        """Start a broadcaster, a listener, and the two timers that use them."""
        super().__init__('frames')

        # The broadcaster sends transforms out on /tf. A node publishes only
        # the joints it is responsible for: here, base_link -> tool.
        self.broadcaster: TransformBroadcaster = TransformBroadcaster(self)

        # The buffer collects every transform anyone publishes, and the listener
        # is what fills it from /tf. Both are needed, and the listener has to be
        # kept, or it is thrown away and the buffer stays empty.
        self.buffer: Buffer = Buffer()
        self.listener: TransformListener = TransformListener(self.buffer, self)

        self.start: Time = self.get_clock().now()
        self.send_timer: Timer = self.create_timer(0.5, self.send)
        self.ask_timer: Timer = self.create_timer(1.0, self.ask)

    def send(self) -> None:
        """Say where the tool is now, inside base_link."""
        seconds: float = (self.get_clock().now() - self.start).nanoseconds / 1e9
        angle: float = 2 * math.pi * seconds / PERIOD

        transform: TransformStamped = TransformStamped()
        # The header says when this was true and which frame it is measured in:
        # the parent. child_frame_id is the frame being placed.
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = 'base_link'
        transform.child_frame_id = 'tool'
        transform.transform.translation.x = RADIUS * math.cos(angle)
        transform.transform.translation.y = RADIUS * math.sin(angle)
        transform.transform.translation.z = 0.10
        # The turn, as a quaternion: four numbers instead of three angles,
        # because three angles have awkward cases in 3D. This one is "no turn".
        transform.transform.rotation.w = 1.0
        self.broadcaster.sendTransform(transform)

    def ask(self) -> None:
        """Ask TF where the tool is, the way any other node would."""
        try:
            # Time() means "the latest you have". Asking for a moment TF does
            # not know yet, or has already forgotten, raises the exception below,
            # and every node that uses TF has to expect it: at start-up, nothing
            # has been published yet.
            found: TransformStamped = self.buffer.lookup_transform('base_link', 'tool', Time())
        except TransformException as error:
            self.get_logger().warn(f'no answer yet: {error}')
            return

        where = found.transform.translation
        self.get_logger().info(
            f'tool is at ({where.x:+.3f}, {where.y:+.3f}, {where.z:+.3f}) in base_link')


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Frames = Frames()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
