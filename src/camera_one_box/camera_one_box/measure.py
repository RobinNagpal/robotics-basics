"""Measure a box from one depth picture: where it stands, and how tall it is.

This file has no ROS in it. It works on plain NumPy arrays, which is what the
node in box_locator.py hands it, and what the tests hand it from a recorded
capture. Keeping the maths apart from the ROS plumbing is the usual way to
make perception code testable.

The four steps are the ones in section 1 of docs/camera/one-box-intro.md:

1. turn every pixel and its depth reading into a point measured from the camera
2. move those points into the room, using camera_to_world
3. keep the points standing on the table, and of those, the highest ones
4. average them: that is the middle of the box, and its height is how tall it is
"""

from dataclasses import dataclass

# NumPy does arithmetic on whole arrays at once. A depth picture is a 240 x 320
# array, and one line of NumPy works on all 76,800 pixels without a Python loop.
import numpy as np
# SciPy's Rotation turns between the different ways of writing down a turn,
# such as the quaternion TF uses and the 3 x 3 table the maths needs.
from scipy.spatial.transform import Rotation


# A dataclass is a plain Python class for holding a few named values. frozen=True
# means the values cannot be changed after it is made, so a measurement stays
# exactly what was measured.
@dataclass(frozen=True)
class BoxMeasurement:
    """What the camera measured about one box, in metres, in the room."""

    x: float           # the middle of the box's top, along the room's x
    y: float           # and along the room's y
    height: float      # how far its top is above the table
    width_x: float     # how far its top spreads along x
    width_y: float     # and along y
    points: int        # how many points landed on its top


def depth_to_points(depth: np.ndarray, fx: float, fy: float, cx: float, cy: float) -> np.ndarray:
    """Turn a whole depth picture into points measured from the camera.

    This is section 1.1 of docs/camera/one-box-intro.md, done for every pixel
    at once. The result has the same shape as the picture, with three numbers per
    pixel: x to the right, y down the picture and z straight ahead, in the
    camera's optical frame. Pixels with no reading stay NaN, so they can never
    become a point.

    Gazebo, like the doc, measures pixel positions from the pixel's top-left
    corner, so the middle of a pixel is at +0.5.
    """
    rows, cols = depth.shape
    # np.mgrid makes two arrays the same size as the picture: one holding each
    # pixel's row number, and one holding its column number. Adding 0.5 moves
    # every number from the pixel's corner to its middle. So v and u are the
    # pixel positions of every pixel at once, ready for the formulas below.
    v, u = np.mgrid[0:rows, 0:cols] + 0.5
    # The two formulas from the doc. Because u, v and depth are whole arrays,
    # each line works out x or y for every pixel in one go.
    x = (u - cx) * depth / fx
    y = (v - cy) * depth / fy
    # np.dstack puts the three arrays together, so that each pixel holds its
    # three numbers side by side: (x, y, z), where z is the depth itself.
    return np.dstack([x, y, depth])


def transform_matrix(translation, rotation_xyzw) -> np.ndarray:
    """Build camera_to_world as a 4 x 4 matrix, from what TF gives.

    TF stores a transform as a translation and a quaternion. The first three
    columns of the matrix are the camera's right, down and forward, written in
    the room's axes, and the last column is where the camera is: section 1.2.
    """
    # Start from a 4 x 4 table with ones down the diagonal and zeros elsewhere,
    # which is a transform that does nothing. Its bottom row, 0 0 0 1, is then
    # already right.
    matrix = np.eye(4)
    # Fill the top-left 3 x 3 with the rotation. from_quat reads the quaternion,
    # four numbers in the order x, y, z, w, which is the order TF uses, and
    # as_matrix writes the same turn as three columns: the camera's three axes.
    matrix[:3, :3] = Rotation.from_quat(rotation_xyzw).as_matrix()
    # The last column is where the camera is.
    matrix[:3, 3] = translation
    return matrix


def to_world(points: np.ndarray, camera_to_world: np.ndarray) -> np.ndarray:
    """Move points from the camera's axes into the room's. Returns an N x 3 array."""
    # Lay the points out as one long list, one row per point with three numbers
    # in it. The -1 asks NumPy to work out how many rows that makes.
    flat = points.reshape(-1, 3)
    # Move every point at once. @ is matrix multiplication: it turns each point
    # from the camera's axes into the room's, and .T lays the table on its side
    # so that it fits points written as rows. Adding the camera's position then
    # shifts every point from "measured from the camera" to "measured from the
    # middle of the table". This is the walk from section 1.2 of the doc, for
    # all the points together.
    return flat @ camera_to_world[:3, :3].T + camera_to_world[:3, 3]


def measure_box(points_in_world: np.ndarray, table_z: float = 0.0,
                min_height: float = 0.01, top_tolerance: float = 0.001):
    """Find the box among the points and measure it. Returns None if nothing stands up.

    :param points_in_world: N x 3 points in the room, NaN where there was no reading.
    :param table_z: How high the table top is.
    :param min_height: Anything this far above the table counts as the box.
    :param top_tolerance: Points this close to the highest one count as its top.
        The pixels at the box's edge catch a strip of its side, which is lower,
        and this leaves them out.
    """
    # NaN, "not a number", marks a pixel with no depth reading. isnan finds
    # them, any(axis=1) flags a point if any of its three numbers is NaN, and ~
    # turns that round into "this point is fine". Indexing with a list of
    # True/False values keeps only the rows marked True.
    valid = ~np.isnan(points_in_world).any(axis=1)
    points = points_in_world[valid]
    # points[:, 2] is the third number of every point: its height in the room.
    # Keep the points standing more than min_height above the table.
    standing = points[points[:, 2] > table_z + min_height]
    if len(standing) == 0:
        return None
    # The highest point is the top of the box. Keep every point within
    # top_tolerance of it, which leaves out the lower strip of the box's side.
    top_z = standing[:, 2].max()
    top = standing[standing[:, 2] > top_z - top_tolerance]
    # The middle of the top is the average of its points along x and along y.
    # np.ptp, "peak to peak", is the largest value minus the smallest, which is
    # how far the top spreads in each direction.
    return BoxMeasurement(
        x=float(top[:, 0].mean()),
        y=float(top[:, 1].mean()),
        height=float(top_z - table_z),
        width_x=float(np.ptp(top[:, 0])),
        width_y=float(np.ptp(top[:, 1])),
        points=len(top),
    )
