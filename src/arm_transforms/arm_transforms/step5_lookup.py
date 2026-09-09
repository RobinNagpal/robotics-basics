"""Step 5: ask TF where things are, instead of working it out.

Run it:  make arm.watch   (with `make arm.demo` already running in another
terminal, or: ros2 run arm_transforms arm_step5_lookup)

THE IDEA
--------
Step 4 published each link on its own. It never published base_link->gripper,
and it never published base_link->camera. This node asks for both anyway::

    buffer.lookup_transform('base_link', 'gripper', ...)
    buffer.lookup_transform('base_link', 'camera', ...)

TF joins the chains to answer. Look through this file: there is no trigonometry
in it. No ``cos``, no ``sin``, no ``q1 + q2``. It does not import ``arm_math``.
It does not know how long the links are, how many joints the arm has, or that
the arm is flat.

That is the payoff. Step 2 said each link should be described once, on its own.
Once they are all published, anything on the robot can ask about any pair of
frames without knowing how the robot is built.

TWO QUESTIONS, ONE MECHANISM
----------------------------
The node answers the two questions the doc opened with:

* The gripper holds a screwdriver, 5 cm ahead of it. Where is the tip?
* The camera sees a screw 20 cm in front of it. Where is that screw?

Both are the same move: take a point that is fixed in some frame, and carry it
into ``base_link``. The two points never change in their own frames. The answers
change constantly, because the frames move.

Note also that the camera answer does not involve the gripper at all. The camera
hangs off link 2, so TF walks a different route to reach it.

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

#: A screwdriver tip, 5 cm ahead of the gripper, fixed there.
TOOL_TIP_IN_GRIPPER = (0.05, 0.0)
#: A screw the camera can see, 20 cm in front of it.
SCREW_IN_CAMERA = (0.20, 0.0)


def yaw_of(transform: TransformStamped) -> float:
    """Pull the flat turn angle back out of a quaternion.

    The reverse of ``yaw_to_quaternion``. Only correct for rotations about the
    up axis, which is all this arm does.
    """
    z = transform.transform.rotation.z
    w = transform.transform.rotation.w
    return 2.0 * math.atan2(z, w)


def carry_into_base(found: TransformStamped, x: float, y: float) -> tuple[float, float]:
    """Carry a point from the looked-up frame into base_link.

    Rotate first, then shift — the same rule as step 2, applied to a transform
    this program never calculated.
    """
    yaw = yaw_of(found)
    cos_t, sin_t = math.cos(yaw), math.sin(yaw)
    return (
        found.transform.translation.x + x * cos_t - y * sin_t,
        found.transform.translation.y + x * sin_t + y * cos_t,
    )


class ArmWatcher(Node):
    """Ask TF where the gripper and the camera are, once a second."""

    def __init__(self) -> None:
        """Start listening to TF and set up the timer."""
        super().__init__('arm_watcher')

        # The buffer stores transforms as they arrive; the listener fills it
        # from /tf. Both are needed, and the listener must be kept alive.
        self._buffer = Buffer()
        self._listener = TransformListener(self._buffer, self)

        self.create_timer(1.0, self._on_timer)
        self.get_logger().info('Asking TF for base_link -> gripper and -> camera once a second')

    def _lookup(self, frame: str) -> TransformStamped | None:
        try:
            # Time() means "whatever is most recent", rather than a moment.
            return self._buffer.lookup_transform('base_link', frame, Time())
        except TransformException as error:
            self.get_logger().warn(f'No answer for {frame} yet: {error}')
            return None

    def _on_timer(self) -> None:
        gripper = self._lookup('gripper')
        camera = self._lookup('camera')
        if gripper is None or camera is None:
            return

        tip_x, tip_y = carry_into_base(gripper, *TOOL_TIP_IN_GRIPPER)
        screw_x, screw_y = carry_into_base(camera, *SCREW_IN_CAMERA)

        self.get_logger().info(
            f'gripper ({gripper.transform.translation.x:+.3f}, '
            f'{gripper.transform.translation.y:+.3f})  '
            f'tool tip ({tip_x:+.3f}, {tip_y:+.3f})  |  '
            f'camera ({camera.transform.translation.x:+.3f}, '
            f'{camera.transform.translation.y:+.3f})  '
            f'screw ({screw_x:+.3f}, {screw_y:+.3f})'
        )


def main(args: list[str] | None = None) -> None:
    """Entry point for ``ros2 run arm_transforms arm_step5_lookup``."""
    rclpy.init(args=args)
    node = ArmWatcher()
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
