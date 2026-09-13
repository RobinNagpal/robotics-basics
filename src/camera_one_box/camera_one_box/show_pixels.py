"""Print one picture from the basic camera in the terminal, every pixel of it.

Run it while the simulation is running:

    ros2 run camera_one_box show_pixels

It waits for one colour picture and one depth picture from the 80 x 60 basic
camera, draws both one coloured square per pixel, prints the actual depth
readings for a small patch on the box's edge, and exits. Nothing is smoothed
or left out: this is exactly what the camera published.
"""

from cv_bridge import CvBridge
import message_filters
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

#: A patch of the 80 x 60 picture on the box's left edge, as (first column,
#: last column, first row, last row), so it holds table, side and top.
PATCH = (43, 50, 19, 23)


def draw_pixels(colours: np.ndarray) -> None:
    """Print a picture in the terminal, one coloured square for every pixel.

    Each character on screen holds two pixels, one above the other. The top
    pixel is the colour of the half block '▀' itself, and the bottom pixel is
    the colour behind it. Terminal characters are about twice as tall as they
    are wide, so this makes every pixel come out square.

    The colours use the standard 24-bit colour codes, which almost every modern
    terminal understands.
    """
    rows = [[tuple(int(c) for c in pixel) for pixel in row] for row in colours]
    if len(rows) % 2:
        rows.append([(0, 0, 0)] * len(rows[0]))    # an odd last row gets a black partner
    for top, bottom in zip(rows[0::2], rows[1::2]):
        line = ''.join(
            f'\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀'
            for (r1, g1, b1), (r2, g2, b2) in zip(top, bottom)
        )
        print('  ' + line + '\x1b[0m')


def depth_to_grey(depth: np.ndarray) -> np.ndarray:
    """Turn each depth reading into a shade of grey: the nearer, the brighter.

    The furthest reading in the picture becomes dark grey and the nearest
    becomes white. A pixel with no reading is black.
    """
    near, far = np.nanmin(depth), np.nanmax(depth)
    level = 60 + 195 * (far - depth) / ((far - near) or 1.0)
    grey = np.where(np.isnan(depth), 0, np.round(level)).astype(np.uint8)
    return np.dstack([grey, grey, grey])


def show(colour: np.ndarray, depth: np.ndarray) -> None:
    """Print the colour picture, the depth picture and one patch of raw numbers."""
    rows, cols = depth.shape
    print(f'\nThe colour picture: {cols} pixels across and {rows} down, each one a single '
          'colour.\n')
    draw_pixels(colour)

    near, far = np.nanmin(depth), np.nanmax(depth)
    print(f'\nThe depth picture: the same pixels, each holding a distance instead. '
          f'Nearer is\nbrighter: {far:.3f} m is dark grey and {near:.3f} m is white.\n')
    draw_pixels(depth_to_grey(depth))

    first_col, last_col, first_row, last_row = PATCH
    print(f'\nA picture is only numbers. The depth readings, in metres, for columns '
          f'{first_col} to {last_col}\nand rows {first_row} to {last_row}, on the left '
          'edge of the box:\n')
    print('         ' + ''.join(f'{col:>7}' for col in range(first_col, last_col + 1)))
    for row in range(first_row, last_row + 1):
        readings = depth[row, first_col:last_col + 1]
        print(f'  row {row:<3}' + ''.join(f'{d:>7.3f}' for d in readings))
    table, side, top = (tuple(int(c) for c in colour[first_row, col])
                        for col in (first_col, first_col + 3, first_col + 4))
    print('\nThe colour picture holds three numbers in each pixel instead, for red, '
          f'green and blue:\n\n  {table} on the table\n  {side} on the side of the box\n'
          f'  {top} on the top')


class ShowPixels(Node):
    """Wait for one colour and depth picture from the basic camera, print them, stop."""

    def __init__(self):
        """Subscribe to the basic camera's colour and depth pictures, in pairs."""
        super().__init__('show_pixels')
        self.bridge = CvBridge()
        self.done = False
        colour = message_filters.Subscriber(self, Image, '/basic_camera/image_raw')
        depth = message_filters.Subscriber(self, Image, '/basic_camera/depth/image_raw')
        self.pairs = message_filters.TimeSynchronizer([colour, depth], queue_size=10)
        self.pairs.registerCallback(self.on_pictures)

    def on_pictures(self, colour_msg: Image, depth_msg: Image) -> None:
        """Print the first pair of pictures, then ask to stop."""
        if self.done:
            return
        colour = self.bridge.imgmsg_to_cv2(colour_msg, desired_encoding='rgb8')
        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='32FC1')
        show(colour, depth)
        self.done = True


def main(args=None) -> None:
    """Spin until one pair of pictures has been printed."""
    rclpy.init(args=args)
    node = ShowPixels()
    print('Waiting for the basic camera. Is the simulation running (make camera.one_box)?')
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
