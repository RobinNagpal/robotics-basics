"""The simplest camera driver: publish a picture on a topic, ten times a second.

A real camera driver reads each picture from the camera and publishes it as a
sensor_msgs/Image message. This node publishes exactly the same kind of message,
but it draws the picture itself: a red ball moving over a grey background. That
way it runs on any computer, even one with no camera, and the programs that
receive the pictures cannot tell the difference.

Publishes:
  /camera/image_raw     sensor_msgs/Image        the picture, 320 x 240 pixels
  /camera/camera_info   sensor_msgs/CameraInfo   the camera's four lens numbers

Run it on its own with:  ros2 run ros_camera camera_publisher
"""

import math

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image

# The picture's size, and the four lens numbers from the camera docs: a lens
# that sees 60 degrees across, which makes the focal length 277.1 pixels.
WIDTH, HEIGHT = 320, 240
FX = FY = 277.1
CX, CY = WIDTH / 2, HEIGHT / 2

BALL_RADIUS = 15                       # in pixels
BALL_COLOUR = (220, 40, 40)            # red, green, blue
BACKGROUND = (200, 200, 200)           # light grey


def ball_position(seconds: float) -> tuple[float, float]:
    """Say where the middle of the ball is, in pixels, after this many seconds.

    The ball moves in a slow loop that stays inside the picture.
    """
    u = CX + 110 * math.sin(0.6 * seconds)
    v = CY + 70 * math.sin(0.9 * seconds)
    return u, v


def draw_picture(u: float, v: float) -> np.ndarray:
    """Draw the grey picture with the red ball at pixel (u, v).

    The result is a NumPy array with one row per row of pixels, and three
    numbers in each pixel: red, green and blue, from 0 to 255.
    """
    picture = np.full((HEIGHT, WIDTH, 3), BACKGROUND, dtype=np.uint8)
    rows, cols = np.mgrid[0:HEIGHT, 0:WIDTH] + 0.5          # the middle of every pixel
    inside = (cols - u) ** 2 + (rows - v) ** 2 <= BALL_RADIUS ** 2
    picture[inside] = BALL_COLOUR
    return picture


# CameraPublisher extends rclpy's Node, which is what makes this program a ROS
# node: something with a name, that can publish messages on topics.
class CameraPublisher(Node):
    """Publish a new picture, and the lens numbers, ten times a second."""

    def __init__(self):
        """Create the two publishers, and a timer that calls publish_picture."""
        super().__init__('camera_publisher')

        # A publisher announces "I will send messages of this type on this
        # topic". The 10 is how many messages to keep waiting if a subscriber is
        # slow to take them.
        self.image_publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_publisher = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # A timer calls a function again and again, here every 0.1 seconds.
        # That is how a node does something regularly without a loop of its own.
        self.start = self.get_clock().now()
        self.timer = self.create_timer(0.1, self.publish_picture)

    def publish_picture(self) -> None:
        """Draw the next picture, and publish it with its lens numbers."""
        now = self.get_clock().now()
        seconds = (now - self.start).nanoseconds / 1e9
        picture = draw_picture(*ball_position(seconds))

        # Every picture carries a header: when it was taken, and which frame
        # (which set of axes) it was taken in. Both messages get the same
        # timestamp, so a receiver knows they belong together.
        stamp = now.to_msg()

        # A sensor_msgs/Image holds the picture's size, an encoding that says
        # what each pixel's numbers mean, and every pixel's numbers as one long
        # list of bytes, row after row. 'rgb8' means three numbers per pixel, red,
        # green and blue, one byte each, so each row is WIDTH * 3 bytes long.
        image = Image()
        image.header.stamp = stamp
        image.header.frame_id = 'camera'
        image.height, image.width = HEIGHT, WIDTH
        image.encoding = 'rgb8'
        image.step = WIDTH * 3
        image.data = picture.tobytes()
        self.image_publisher.publish(image)

        # A sensor_msgs/CameraInfo describes the lens. The four lens numbers go
        # into k, a 3 x 3 grid written out as nine numbers, row by row.
        info = CameraInfo()
        info.header = image.header
        info.height, info.width = HEIGHT, WIDTH
        info.k = [FX, 0.0, CX,
                  0.0, FY, CY,
                  0.0, 0.0, 1.0]
        self.info_publisher.publish(info)


def main(args=None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        # spin() keeps the program running, and lets ROS call the node's timer
        # or callbacks whenever they are due. It returns when the program is
        # asked to stop, for example with Ctrl-C.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
