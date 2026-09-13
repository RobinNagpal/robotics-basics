"""Measure a box from one depth picture: where it stands, and how tall it is.

This file has no ROS in it. It works on plain NumPy arrays, which is what the
node in box_locator.py hands it, and what the tests hand it from a recorded
capture. Keeping the maths apart from the ROS plumbing is the usual way to
make perception code testable.

The four steps are the ones in section 1 of docs/camera/one-box.md:

1. turn every pixel and its depth reading into a point measured from the camera
2. move those points into the room, using camera_to_world
3. keep the points standing on the table, and of those, the highest ones
4. average them: that is the middle of the box, and its height is how tall it is
"""

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation


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

    This is section 1.1 of docs/camera/one-box.md, done for every pixel at
    once. The result has the same shape as the picture, with three numbers per
    pixel: x to the right, y down the picture and z straight ahead, in the
    camera's optical frame. Pixels with no reading stay NaN, so they can never
    become a point.

    Gazebo, like the doc, measures pixel positions from the pixel's top-left
    corner, so the middle of a pixel is at +0.5.
    """
    rows, cols = depth.shape
    v, u = np.mgrid[0:rows, 0:cols] + 0.5
    x = (u - cx) * depth / fx
    y = (v - cy) * depth / fy
    return np.dstack([x, y, depth])


def transform_matrix(translation, rotation_xyzw) -> np.ndarray:
    """Build camera_to_world as a 4 x 4 matrix, from what TF gives.

    TF stores a transform as a translation and a quaternion. The first three
    columns of the matrix are the camera's right, down and forward, written in
    the room's axes, and the last column is where the camera is: section 1.2.
    """
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_quat(rotation_xyzw).as_matrix()
    matrix[:3, 3] = translation
    return matrix


def to_world(points: np.ndarray, camera_to_world: np.ndarray) -> np.ndarray:
    """Move points from the camera's axes into the room's. Returns an N x 3 array."""
    flat = points.reshape(-1, 3)
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
    valid = ~np.isnan(points_in_world).any(axis=1)
    points = points_in_world[valid]
    standing = points[points[:, 2] > table_z + min_height]
    if len(standing) == 0:
        return None
    top_z = standing[:, 2].max()
    top = standing[standing[:, 2] > top_z - top_tolerance]
    return BoxMeasurement(
        x=float(top[:, 0].mean()),
        y=float(top[:, 1].mean()),
        height=float(top_z - table_z),
        width_x=float(np.ptp(top[:, 0])),
        width_y=float(np.ptp(top[:, 1])),
        points=len(top),
    )
