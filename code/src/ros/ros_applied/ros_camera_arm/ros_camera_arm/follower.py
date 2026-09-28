"""The camera and the arm together: find the ball in each picture, and point the arm at it.

The camera sits at the arm's base, looking the same way the arm points when both
of its joints are at zero. When the ball appears to the right of the middle of
the picture, the arm has to turn right, and when the ball appears above the
middle, the arm has to tilt up. How far to turn comes from the camera basics:
a pixel is a direction, and the angle of that direction is worked out from how
far the pixel is from the middle of the picture, and the focal length.

Subscribes to:
  /camera/image_raw     sensor_msgs/Image        the pictures
  /camera/camera_info   sensor_msgs/CameraInfo   the lens numbers

Publishes:
  /joint_states         sensor_msgs/JointState   the arm's two joint angles

Run it on its own with:  ros2 run ros_camera_arm follower
"""

import math

from cv_bridge import CvBridge
import numpy as np
from numpy.typing import NDArray
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.publisher import Publisher
from sensor_msgs.msg import CameraInfo, Image, JointState

# Reuse the ball finder from the ros_camera package. One ROS package can use
# another's Python code, as long as package.xml says it depends on it.
from ros_camera.camera_subscriber import find_ball


def pixel_to_angles(u: float, v: float, fx: float, fy: float,
                    cx: float, cy: float) -> tuple[float, float]:
    """Turn a pixel into the pan and tilt angles that point at it, in radians.

    (u - cx) / fx is how far to the side the pixel's direction goes, for every
    step forward, and atan2 turns that into an angle. Right of the middle is a
    turn to the right, which is a negative pan. Above the middle, where v is
    smaller than cy, is a tilt up, which is a positive tilt.
    """
    pan: float = -math.atan2(u - cx, fx)
    tilt: float = math.atan2(cy - v, fy)
    return pan, tilt


# Follower extends rclpy's Node, which is what makes this program a ROS node:
# something with a name, that can subscribe to topics and publish on them.
class Follower(Node):
    """Point the arm at the ball, every time a picture arrives."""

    def __init__(self) -> None:
        """Subscribe to the pictures and the lens numbers, and publish joint angles."""
        super().__init__('follower')
        self.bridge: CvBridge = CvBridge()
        # (fx, fy, cx, cy), once the first camera info arrives, and None until then.
        self.lens: tuple[float, float, float, float] | None = None

        self.create_subscription(CameraInfo, '/camera/camera_info', self.on_camera_info, 10)
        self.create_subscription(Image, '/camera/image_raw', self.on_picture, 10)
        self.publisher: Publisher = self.create_publisher(JointState, '/joint_states', 10)

    def on_camera_info(self, msg: CameraInfo) -> None:
        """Keep the four lens numbers, to turn pixels into angles.

        k holds them in a 3 x 3 grid, written out row by row:
        [fx, 0, cx,  0, fy, cy,  0, 0, 1]. So fx is k[0], fy is k[4], cx is k[2]
        and cy is k[5].
        """
        self.lens = (msg.k[0], msg.k[4], msg.k[2], msg.k[5])

    def on_picture(self, msg: Image) -> None:
        """Find the ball, and publish the joint angles that point the arm at it."""
        if self.lens is None:
            return              # no lens numbers yet, so no way to turn pixels into angles
        picture: NDArray[np.uint8] = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        ball: tuple[float, float] | None = find_ball(picture)
        if ball is None:
            return              # nothing to point at: leave the arm where it is

        pan: float
        tilt: float
        pan, tilt = pixel_to_angles(*ball, *self.lens)
        joints: JointState = JointState()
        joints.header.stamp = msg.header.stamp
        # The arm's URDF also has a gripper. It has nothing to hold here, so keep
        # it open, at 0.02 metres, or RViz would not know where to draw its fingers.
        joints.name = ['pan', 'tilt', 'gripper']
        joints.position = [pan, tilt, 0.02]
        self.publisher.publish(joints)
        self.get_logger().info(
            f'ball at pixel ({ball[0]:.0f}, {ball[1]:.0f}): pan {math.degrees(pan):+.0f}°, '
            f'tilt {math.degrees(tilt):+.0f}°',
            throttle_duration_sec=1.0)


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Follower = Follower()
    try:
        # spin() keeps the program running, and lets ROS call the node's timer
        # or callbacks whenever they are due. It returns when the program is
        # asked to stop, for example with Ctrl-C.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
