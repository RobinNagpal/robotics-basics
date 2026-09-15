"""The simplest program that uses a camera: receive each picture, and find the ball in it.

It subscribes to the pictures the camera publishes, turns each one into a
NumPy array with cv_bridge, finds the red ball, and prints where it is in the
picture, once a second.

Subscribes to:
  /camera/image_raw     sensor_msgs/Image        the pictures

Run it on its own with:  ros2 run ros_camera camera_subscriber
"""

from cv_bridge import CvBridge
import numpy as np
from numpy.typing import NDArray
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image


def find_ball(picture: NDArray[np.uint8]) -> tuple[float, float] | None:
    """Find the red ball in a picture. Returns the pixel (u, v) of its middle, or None.

    A pixel is red when its red number is high and its green and blue numbers
    are low. The middle of the ball is the average position of its red pixels,
    plus 0.5, because a pixel's middle is half a pixel from its corner.
    """
    red: NDArray[np.uint8] = picture[..., 0]
    green: NDArray[np.uint8] = picture[..., 1]
    blue: NDArray[np.uint8] = picture[..., 2]
    # True for every pixel that is red enough, False for the rest.
    is_red: NDArray[np.bool_] = (red > 150) & (green < 100) & (blue < 100)
    if not is_red.any():
        return None
    # The row and column numbers of every red pixel: arrays of whole numbers.
    rows: NDArray[np.intp]
    cols: NDArray[np.intp]
    rows, cols = np.nonzero(is_red)
    return float(cols.mean()) + 0.5, float(rows.mean()) + 0.5


# CameraSubscriber extends rclpy's Node, which is what makes this program a ROS
# node: something with a name, that can subscribe to topics.
class CameraSubscriber(Node):
    """Find the ball in every picture that arrives."""

    def __init__(self) -> None:
        """Subscribe to the pictures."""
        super().__init__('camera_subscriber')

        # cv_bridge turns a picture message, which is one long list of bytes,
        # into a NumPy array with one entry per pixel, which is what we can
        # search. It saves unpacking the bytes by hand.
        self.bridge: CvBridge = CvBridge()
        self.pictures: int = 0

        # A subscription says "whenever a message arrives on this topic, call
        # this function with it". That function is called a callback.
        self.create_subscription(Image, '/camera/image_raw', self.on_picture, 10)

    def on_picture(self, msg: Image) -> None:
        """Find the ball in one picture, and report it at most once a second."""
        self.pictures += 1
        picture: NDArray[np.uint8] = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        ball: tuple[float, float] | None = find_ball(picture)
        where: str = 'no ball' if ball is None else f'ball at pixel ({ball[0]:.0f}, {ball[1]:.0f})'
        # Pictures arrive ten times a second. throttle_duration_sec keeps this
        # to one line a second, so the terminal stays readable.
        self.get_logger().info(
            f'picture {self.pictures}: {msg.width} x {msg.height}, {msg.encoding}, {where}',
            throttle_duration_sec=1.0)


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: CameraSubscriber = CameraSubscriber()
    try:
        # spin() keeps the program running, and lets ROS call the node's timer
        # or callbacks whenever they are due. It returns when the program is
        # asked to stop, for example with Ctrl-C.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
