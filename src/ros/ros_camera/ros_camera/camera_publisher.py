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


def camera_info() -> CameraInfo:
    """Describe the camera's lens, as a sensor_msgs/CameraInfo message.

    A picture only says what colour each pixel is. It does not say which
    direction each pixel looks in, and a program needs that to turn a pixel into
    a direction, or a point in the room into a pixel. That depends on the lens
    and the sensor, which a program receiving the pictures cannot know, so the
    camera sends it, in this message, alongside every picture.
    """
    info = CameraInfo()
    info.height, info.width = HEIGHT, WIDTH

    # k: the four lens numbers, arranged as a 3 x 3 grid called the camera
    # matrix (or intrinsic matrix, because the numbers are part of the camera
    # itself):
    #
    #     | fx   0  cx |
    #     |  0  fy  cy |
    #     |  0   0   1 |
    #
    # A message cannot hold a grid, so the nine numbers are written out row by
    # row. That puts fx at k[0], cx at k[2], fy at k[4] and cy at k[5], which is
    # where programs that read this message look for them.
    #
    # The numbers are laid out as a grid, with those zeros and that 1, because
    # the grid turns the camera formula into one multiplication. Multiply it by
    # a point (x, y, z), measured from the camera, and you get
    # (fx * x + cx * z, fy * y + cy * z, z). Divide the first two by the third,
    # z, and you have u = fx * x / z + cx and v = fy * y / z + cy: the pixel the
    # point lands on, as in section 6 of the camera basics. The zeros say that
    # how far a point is to the side does not change how far down the picture
    # it lands, and the other way round. The 1 keeps z as it is, ready for the
    # division.
    info.k = [FX, 0.0, CX,
              0.0, FY, CY,
              0.0, 0.0, 1.0]

    # p: the same four numbers, in a 3 x 4 grid, for the picture after its
    # lens's bending has been taken out. ROS's standard camera tools, such as
    # image_geometry and depth_image_proc, read their lens numbers from p, not
    # from k, so a camera must fill it in too. This lens bends nothing, so p is
    # k with a column of zeros added.
    info.p = [FX, 0.0, CX, 0.0,
              0.0, FY, CY, 0.0,
              0.0, 0.0, 1.0, 0.0]

    # How the lens bends straight lines. 'plumb_bob' is the usual model, with
    # five numbers in d, and five zeros mean "no bending at all".
    info.distortion_model = 'plumb_bob'
    info.d = [0.0, 0.0, 0.0, 0.0, 0.0]

    # r is a turn, used only by stereo cameras, which have two lenses side by
    # side. A camera with one lens sends "no turn": ones down the diagonal.
    info.r = [1.0, 0.0, 0.0,
              0.0, 1.0, 0.0,
              0.0, 0.0, 1.0]
    return info


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

        # The lens numbers, with the same header as the picture, so that a
        # program receiving both knows this is the lens that took it.
        info = camera_info()
        info.header = image.header
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
