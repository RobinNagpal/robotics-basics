"""The simplest program that moves an arm: publish the angle of each joint, twenty times a second.

In ROS, where an arm's joints are is shared on one topic, /joint_states, as
sensor_msgs/JointState messages: a list of joint names, and the angle of each
one. robot_state_publisher listens to that topic, works out where every part of
the arm is, and publishes it on TF, and RViz draws the arm there. So publishing
new angles is enough to make the arm move on screen.

On a real arm, this node would instead send the angles to the arm's controller,
the part that drives the motors, and the controller would publish /joint_states
as the motors actually moved. Here this node plays both parts.

Publishes:
  /joint_states     sensor_msgs/JointState   "pan" and "tilt", in radians, and "gripper",
                                             in metres

Run it on its own with:  ros2 run ros_arm arm_mover
"""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.time import Time
from rclpy.timer import Timer
from sensor_msgs.msg import JointState


def arm_pose(seconds: float) -> tuple[float, float, float]:
    """Say where the three joints should be after this many seconds.

    The arm swings left and right by up to 1 radian (about 57 degrees), and nods
    up and down between 0 and 0.8 radians, at different speeds, so it traces a
    slow loop. The gripper opens and closes between 0 and 0.02 metres, which is
    how far each finger slides out.
    """
    pan: float = 1.0 * math.sin(0.5 * seconds)
    tilt: float = 0.4 + 0.4 * math.sin(0.8 * seconds)
    gripper: float = 0.01 + 0.01 * math.sin(1.2 * seconds)
    return pan, tilt, gripper


# ArmMover extends rclpy's Node, which is what makes this program a ROS node:
# something with a name, that can publish messages on topics.
class ArmMover(Node):
    """Publish the next position of the arm's joints, twenty times a second."""

    def __init__(self) -> None:
        """Create the publisher, and a timer that calls publish_pose."""
        super().__init__('arm_mover')
        # The topic name /joint_states is the one robot_state_publisher listens
        # to. Every ROS arm uses it.
        self.publisher: Publisher = self.create_publisher(JointState, '/joint_states', 10)
        self.start: Time = self.get_clock().now()
        # Call publish_pose every 0.05 seconds: twenty times a second, which is
        # often enough for the arm to move smoothly on screen.
        self.timer: Timer = self.create_timer(0.05, self.publish_pose)

    def publish_pose(self) -> None:
        """Publish where the joints are now."""
        now: Time = self.get_clock().now()
        pan: float
        tilt: float
        gripper: float
        pan, tilt, gripper = arm_pose((now - self.start).nanoseconds / 1e9)

        # A JointState lists the joints by the names they have in the URDF, and
        # their positions in the same order. For a turning joint, the position
        # is an angle in radians, and for a sliding joint, such as the
        # gripper's, it is a distance in metres. The second finger's joint is not
        # listed: the URDF says it copies "gripper".
        msg: JointState = JointState()
        msg.header.stamp = now.to_msg()
        msg.name = ['pan', 'tilt', 'gripper']
        msg.position = [pan, tilt, gripper]
        self.publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: ArmMover = ArmMover()
    try:
        # spin() keeps the program running, and lets ROS call the node's timer
        # or callbacks whenever they are due. It returns when the program is
        # asked to stop, for example with Ctrl-C.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
