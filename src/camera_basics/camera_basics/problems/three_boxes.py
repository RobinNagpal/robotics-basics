"""Part 2: three boxes. What changes when there is more than one.

Run it:  make camera.learn   (or: ros2 run camera_basics camera_three_boxes)

The green and blue boxes go back on the table. Everything from part 1 carries
over unchanged: the same lens, the same pose, the same arithmetic from a pixel
to a point.

THE IDEA
--------
One thing breaks. In part 1, "anything nearer than the table is the box" found
the box's pixels. With three boxes that rule finds all three at once, as one
lump. So before a box can be measured, its pixels have to be told apart from
the others. That is the mask: which box each pixel landed on.

A simulator knows the mask for free, because it knows what every ray hit. A
real camera has to work it out, usually from colour or from gaps in the depth,
and that is a large part of real vision work. Once the pixels are sorted, each
box is measured exactly as in part 1.

The last section is the other thing more boxes bring: from one place, a box can
hide part of another, and the sides are hard to see. That is why a robot
usually takes more than one picture.
"""

from camera_basics.camera import Capture, capture, TABLE_SCENE, TILTED, TOP_DOWN, WRIST
from camera_basics.problems.one_box import (
    heading,
    PREVIEW,
    show_depth_numbers,
    show_measurements,
    side_by_side,
    start_numbering,
)


def show_labels(shot: Capture) -> None:
    """Print which box each pixel landed on."""
    heading('telling the boxes apart')
    print('What each pixel actually landed on. A simulator knows this for free;')
    print('a real camera has to work it out, and it is the one new job that')
    print('more than one box brings.\n')
    for line in shot.ascii_art('label', 40):
        print('  ' + line)


def show_viewpoints() -> None:
    """Take the scene from two places and compare the depth readings."""
    heading('move the camera, and the same scene reads differently')
    print('Straight down on the left, leaning in about 20° on the right.\n')
    top = capture(TABLE_SCENE, PREVIEW, TOP_DOWN)
    tilted = capture(TABLE_SCENE, PREVIEW, TILTED)
    for line in side_by_side(top.ascii_art('depth', 34), tilted.ascii_art('depth', 34)):
        print('  ' + line)
    print(
        '\nFrom above you see tops, and a tall box can hide a short one. The'
        '\ntilted view sees some of the sides instead, and its table no longer'
        '\nreads one number: the far edge is further away than the near edge.'
    )
    span_top, span_tilted = top.depth_range(), tilted.depth_range()
    print(f'\n  straight down   {span_top[0]:.3f} m to {span_top[1]:.3f} m')
    print(f'  leaning in      {span_tilted[0]:.3f} m to {span_tilted[1]:.3f} m')
    print('\nThat is why a robot takes more than one picture before it measures.')


def main() -> None:
    """Print part 2: three boxes, and what changes."""
    print(__doc__.split('THE IDEA')[0].strip())
    start_numbering()

    shot = capture(TABLE_SCENE, WRIST, TOP_DOWN)
    show_labels(capture(TABLE_SCENE, PREVIEW, TOP_DOWN))
    show_depth_numbers(shot, TABLE_SCENE)
    show_measurements(shot, TABLE_SCENE)
    show_viewpoints()

    print('\nNext: make camera.demo publishes these same pictures to RViz,')
    print('as sensor_msgs/Image, sensor_msgs/CameraInfo and a point cloud.')


if __name__ == '__main__':
    main()
