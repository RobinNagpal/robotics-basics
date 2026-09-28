"""Indexing: picking out the values you want from an array.

A robot rarely wants a whole array. It wants the heights of the points, the part
of the picture where the object is, the readings that are not missing, or the
nearest obstacle. This file covers the ways NumPy picks values out:

  1. indexes and slices: one value, one row, one column, one part of a picture
  2. boolean masks: keeping only the values that pass a test
  3. missing readings: NaN, and the functions that skip it
  4. finding things: argmin, argmax, where, nonzero, clip
  5. picking by a list of indexes: sorting, the k nearest, unique labels

Run it with:  pixi run python src/numpy/indexing.py
"""

import numpy as np
from numpy.typing import NDArray

# Six points from a depth camera, in the room, in metres: x, y and z (the
# height above the table). Two lie on the table, and four on a box 6 cm tall.
POINTS: NDArray[np.float64] = np.array([
    [0.10, 0.20, 0.000],
    [0.05, 0.04, 0.060],
    [0.07, 0.03, 0.060],
    [0.06, 0.05, 0.059],
    [0.08, 0.04, 0.060],
    [-0.20, 0.10, 0.001],
])


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def indexes_and_slices() -> None:
    """Pick out one value, one row, one column, or one part of a picture."""
    heading('1. Indexes and slices')

    # One index per axis, separated by commas. Row 1, column 2: the second
    # point's height. Counting starts at 0, and -1 means the last one.
    print('POINTS[1, 2]  (point 1, its z)', POINTS[1, 2])
    print('POINTS[-1]    (the last point) ', POINTS[-1])

    # A colon on its own means "all of them" along that axis. POINTS[:, 2] is
    # every row, column 2: the height of every point.
    heights: NDArray[np.float64] = POINTS[:, 2]
    print('POINTS[:, 2]  (every height)   ', heights)

    # start:stop picks a range; stop is not included. Rows 1, 2 and 3.
    print('POINTS[1:4, :2] (x and y of points 1 to 3):\n', POINTS[1:4, :2])

    # A picture is indexed [row, column, colour]. Rows count down from the
    # top, and columns count right from the left.
    picture: NDArray[np.uint8] = np.zeros((240, 320, 3), dtype=np.uint8)
    picture[100:140, 150:170] = (220, 40, 40)          # a red patch
    # Cropping is slicing: the 40 x 20 pixel patch, all three colours.
    patch: NDArray[np.uint8] = picture[100:140, 150:170]
    print('picture[100:140, 150:170].shape', patch.shape)
    # picture[:, :, 0] is one colour for every pixel: the red channel.
    red: NDArray[np.uint8] = picture[:, :, 0]
    print('picture[:, :, 0].shape', red.shape, ' red at (120, 160):', red[120, 160])
    # A step after a second colon skips values: every second row and column
    # halves the picture's size in each direction, a quick way to shrink it.
    print('picture[::2, ::2].shape', picture[::2, ::2].shape)


def boolean_masks() -> None:
    """Keep only the values that pass a test."""
    heading('2. Boolean masks')

    # A comparison on an array compares every value, and gives an array of
    # True and False of the same shape: a mask.
    standing: NDArray[np.bool_] = POINTS[:, 2] > 0.01
    print('POINTS[:, 2] > 0.01 ->', standing)
    # Indexing with a mask keeps the rows where it is True.
    print('POINTS[standing]  (the points on the box):\n', POINTS[standing])
    # True counts as 1 and False as 0, so sum() counts them.
    print('standing.sum() ->', standing.sum(), 'points')

    # Masks combine with & (and), | (or) and ~ (not). Each test needs brackets
    # round it, because & is worked out before > and <.
    near_middle: NDArray[np.bool_] = (np.abs(POINTS[:, 0]) < 0.07) & (POINTS[:, 2] > 0.01)
    print('(|x| < 0.07) & (z > 0.01) ->', near_middle)
    print('~standing                  ->', ~standing)

    # A mask can also be written into: set every pixel darker than 30 to 0.
    grey: NDArray[np.uint8] = np.array([[10, 200], [25, 90]], dtype=np.uint8)
    grey[grey < 30] = 0
    print('grey[grey < 30] = 0 ->', grey.tolist())


def missing_readings() -> None:
    """Handle NaN: the value a depth camera gives where it could not measure."""
    heading('3. Missing readings: NaN')

    # A depth camera cannot measure everywhere: a shiny surface, an edge, or
    # something too close. ROS depth pictures mark those pixels NaN, "not a
    # number". Here the middle reading is missing.
    depth: NDArray[np.float32] = np.array([0.40, np.nan, 0.34], dtype=np.float32)
    print('depth               ', depth)

    # NaN spreads through arithmetic: any sum or mean that includes it is NaN.
    print('depth.mean()        ', depth.mean())
    # And NaN is not equal to anything, not even itself, so == cannot find it.
    print('depth == np.nan     ', depth == np.nan)
    # np.isnan finds it; np.isfinite finds the real readings (not NaN, not infinite).
    print('np.isnan(depth)     ', np.isnan(depth))
    print('depth[np.isfinite(depth)]', depth[np.isfinite(depth)])
    # The nan- functions skip NaN: nanmean, nanmin, nanmax, nanmedian, ...
    print('np.nanmean(depth)   ', np.nanmean(depth), ' np.nanmin(depth)', np.nanmin(depth))


def finding_things() -> None:
    """Ask where the smallest, largest or matching values are."""
    heading('4. Finding things: argmin, argmax, where, nonzero, clip')

    # A distance sensor that turns, like a lidar, gives one reading per angle.
    angles_deg: NDArray[np.int64] = np.arange(-90, 91, 30)
    ranges: NDArray[np.float64] = np.array([2.1, 1.4, 0.8, 0.6, 1.9, 3.0, 2.5])
    # argmin gives the index of the smallest value, not the value itself, so
    # it can be used to look up the matching angle: where the nearest obstacle is.
    nearest: int = int(np.argmin(ranges))
    print('ranges', ranges, ' np.argmin ->', nearest,
          ' so the nearest obstacle is', ranges[nearest], 'm at', angles_deg[nearest], 'degrees')

    # On a picture, argmax counts through all the pixels as if they were one
    # long row. np.unravel_index turns that count back into (row, column).
    brightness: NDArray[np.uint8] = np.zeros((240, 320), dtype=np.uint8)
    brightness[86, 212] = 255
    flat_index: int = int(np.argmax(brightness))
    row: int
    col: int
    row, col = (int(i) for i in np.unravel_index(flat_index, brightness.shape))
    print('np.argmax(brightness) ->', flat_index, ' np.unravel_index ->', (row, col))

    # np.where(test, a, b) picks from a where the test is True, and from b
    # where it is False: here, replace missing depth readings with 0.
    depth: NDArray[np.float64] = np.array([0.40, np.nan, 0.34])
    print('np.where(np.isnan(depth), 0.0, depth) ->', np.where(np.isnan(depth), 0.0, depth))

    # np.nonzero (or np.where with only a test) gives the indexes where a mask
    # is True: the rows and columns of every pixel of a small red blob.
    blob: NDArray[np.bool_] = np.zeros((5, 5), dtype=bool)
    blob[1:3, 2:4] = True
    rows: NDArray[np.intp]
    cols: NDArray[np.intp]
    rows, cols = np.nonzero(blob)
    print('np.nonzero(blob) -> rows', rows, 'cols', cols,
          ' middle of the blob:', (float(rows.mean()), float(cols.mean())))

    # np.clip keeps every value inside limits, like a joint's lower and upper limit.
    wanted: NDArray[np.float64] = np.array([-2.0, 0.3, 1.9])
    print('np.clip([-2.0, 0.3, 1.9], -1.57, 1.57) ->', np.clip(wanted, -1.57, 1.57))


def picking_by_index() -> None:
    """Pick rows by a list of their indexes."""
    heading('5. Picking by a list of indexes')

    # A list of indexes picks those rows, in that order.
    print('POINTS[[0, 5]]  (the two table points):\n', POINTS[[0, 5]])

    # argsort gives the indexes that would sort the values. Sorting the points
    # by how far they are from the gripper, then taking the first two, gives
    # the two nearest points.
    gripper: NDArray[np.float64] = np.array([0.05, 0.04, 0.10])
    distances: NDArray[np.float64] = np.linalg.norm(POINTS - gripper, axis=1)
    order: NDArray[np.intp] = np.argsort(distances)
    print('distances', distances.round(3))
    print('np.argsort(distances) ->', order, ' the two nearest:', order[:2])

    # np.unique lists the different values, which is how you find which
    # objects a segmentation picture (one label per pixel) contains.
    labels: NDArray[np.int64] = np.array([[0, 0, 2], [1, 1, 2], [0, 0, 2]])
    values: NDArray[np.int64]
    counts: NDArray[np.intp]
    values, counts = np.unique(labels, return_counts=True)
    print('np.unique(labels, return_counts=True) -> labels', values, 'pixels', counts)


def main() -> None:
    """Run every section in order."""
    np.set_printoptions(precision=4, suppress=True)
    indexes_and_slices()
    boolean_masks()
    missing_readings()
    finding_things()
    picking_by_index()


if __name__ == '__main__':
    main()
