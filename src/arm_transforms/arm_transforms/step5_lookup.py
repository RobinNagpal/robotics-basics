"""Step 5: ask TF where the gripper is, instead of working it out.

Run it:  make arm.check   (with `make arm.demo` already running in another
terminal, or: ros2 run arm_transforms arm_step5_lookup)

THE IDEA
--------
Step 4 published each link on its own. It never published base_link->gripper.
This node asks for it anyway::

    buffer.lookup_transform('base_link', 'gripper', ...)

and TF joins the chain to answer. Look through this file: there is no
trigonometry in it. No ``cos``, no ``sin``, no ``q1 + q2``. It does not even
import ``arm_math``. It does not know the arm has two joints, how long the
links are, or that the arm is flat.

That is the payoff. Step 2 said each link should be described once, on its own.
Once they are all published, anything on the robot can ask about any pair of
frames without knowing how the robot is built.

THE TOOL TIP, AGAIN
-------------------
Step 3 carried a screwdriver tip from the gripper frame onto the table with
``transform.apply(...)``. Here the same job is done by asking TF for the
transform and applying it to the point. Same three moves — join, flip, apply —
now available to every program on the robot.

WHY LOOKUPS CAN FAIL
--------------------
A lookup can fail, and the node has to cope. Usually it is one of:

* the broadcaster is not running yet, so no transforms have arrived
* you asked for a moment in time that has not been received
* the two frames are in separate trees, with no path between them

Asking for ``Time()`` — meaning "the latest you have" — avoids the timing
problems while you are learning. Real code often wants a specific moment, so
that a measurement is matched against where the robot was when it was taken.
"""

from __future__ import annotations

import math

from geometry_msgs.msg import TransformStamped
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener

#: The screwdriver tip from step 3: 5 cm ahead of the gripper, fixed there.
TOOL_TIP_IN_GRIPPER = (0.05, 0.0)


def yaw_of(transform: TransformStamped) -> float:
    """Pull the flat turn angle back out of a quaternion.

    The reverse of ``yaw_to_quaternion``. Only correct for rotations about the
    up axis, which is all this arm does.
    """
    z = transform.transform.rotation.z
    w = transform.transform.rotation.w
    return 2.0 * math.atan2(z, w)


class GripperWatcher(Node):
    """Ask TF where the gripper is, once a second, and print it."""

    def __init__(self) -> None:
        """Start listening to TF and set up the timer."""
        super().__init__('gripper_watcher')

        # The buffer stores transforms as they arrive; the listener fills it
        # from /tf. Both are needed, and the listener must be kept alive.
        self._buffer = Buffer()
        self._listener = TransformListener(self._buffer, self)

        self.create_timer(1.0, self._on_timer)
        self.get_logger().info('Asking TF for base_link -> gripper once a second')

    def _on_timer(self) -> None:
        try:
            # Time() means "whatever is most recent", rather than a moment.
            found = self._buffer.lookup_transform('base_link', 'gripper', Time())
        except TransformException as error:
            self.get_logger().warn(f'No answer yet: {error}')
            return

        x = found.transform.translation.x
        y = found.transform.translation.y
        yaw_deg = math.degrees(yaw_of(found))

        # Carry the tool tip into base_link. Rotate first, then shift — the
        # same rule as step 2, applied to a transform we never calculated.
        cos_t, sin_t = math.cos(yaw_of(found)), math.sin(yaw_of(found))
        tip_x = x + TOOL_TIP_IN_GRIPPER[0] * cos_t - TOOL_TIP_IN_GRIPPER[1] * sin_t
        tip_y = y + TOOL_TIP_IN_GRIPPER[0] * sin_t + TOOL_TIP_IN_GRIPPER[1] * cos_t

        self.get_logger().info(
            f'gripper at ({x:+.3f}, {y:+.3f}) facing {yaw_deg:+7.1f}°   '
            f'tool tip at ({tip_x:+.3f}, {tip_y:+.3f})'
        )


def main(args: list[str] | None = None) -> None:
    """Entry point for ``ros2 run arm_transforms arm_step5_lookup``."""
    rclpy.init(args=args)
    node = GripperWatcher()
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
