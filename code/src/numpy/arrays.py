"""Arrays: NumPy's one class, what it holds, and how to make, reshape and send one.

Almost everything a robot senses or controls is a grid of numbers: the angles of
its joints, a colour picture, a depth picture, a cloud of 3D points, a 4 x 4
transform. NumPy stores each of these as an ndarray, short for "n-dimensional
array": one block of numbers, all of the same type, with a shape that says how
they are arranged. This file covers that class:

  1. one array, and what it knows about itself: shape, ndim, size, dtype
  2. the number types (dtypes) robotics uses, and the one trap in uint8
  3. making arrays: zeros, ones, full, eye, arange, linspace
  4. changing the shape: reshape, flatten, transpose, new axes
  5. joining arrays: stack, column_stack, concatenate
  6. views and copies: when changing one array changes another
  7. bytes and files: how an array travels in a ROS message, and is saved

Run it with:  pixi run python src/numpy/arrays.py
"""

import math
import pathlib
import tempfile

import numpy as np
from numpy.typing import NDArray

# Four points measured by a depth camera, in metres. Each row is one point,
# and the three columns are its x, y and z.
POINTS: NDArray[np.float64] = np.array([
    [0.10, 0.20, 0.00],
    [0.05, 0.04, 0.06],
    [0.07, 0.03, 0.06],
    [-0.20, 0.10, 0.00],
])


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def one_array() -> None:
    """Make three arrays a robot uses, and ask each one what it holds."""
    heading('1. One array, and what it knows about itself')

    # The angles of a three-joint arm, in radians: 0, 30 and 60 degrees. One
    # row of numbers, so it has one axis.
    joints: NDArray[np.float64] = np.array([0.0, math.radians(30), math.radians(60)])
    print('joints:', joints)
    print('  shape', joints.shape, ' ndim', joints.ndim, ' size', joints.size,
          ' dtype', joints.dtype)

    # Four points, one per row, with x, y and z in the columns, so the shape is
    # (4, 3): four rows along axis 0, three columns along axis 1.
    print('POINTS:\n', POINTS)
    print('  shape', POINTS.shape, ' ndim', POINTS.ndim, ' size', POINTS.size)

    # A colour picture, 240 rows by 320 columns, with three numbers in each
    # pixel: red, green and blue, from 0 to 255. Three axes.
    picture: NDArray[np.uint8] = np.zeros((240, 320, 3), dtype=np.uint8)
    print('picture: shape', picture.shape, ' ndim', picture.ndim, ' size', picture.size,
          ' dtype', picture.dtype, ' nbytes', picture.nbytes)


def dtypes() -> None:
    """Show the number types robotics uses, and why the type matters."""
    heading('2. dtypes: the type of every number in the array')

    # Decimal numbers are float64 unless you ask for something else: 8 bytes each.
    print(np.array([0.5, 1.0]).dtype, '  decimal numbers: positions, angles, transforms')
    # A depth picture from a ROS camera is float32, 4 bytes each: its encoding,
    # 32FC1, means one 32-bit float per pixel.
    print(np.zeros(2, dtype=np.float32).dtype, '  depth pictures, point clouds from sensors')
    # A colour picture is uint8: whole numbers from 0 to 255, one byte each.
    print(np.zeros(2, dtype=np.uint8).dtype, '    colour pictures')
    # A comparison gives an array of True and False, which is how points are picked out.
    print((np.array([0.3, 0.5]) > 0.4).dtype, '     masks: which points to keep')
    # Whole numbers are int64: pixel positions, counts, indexes.
    print(np.array([3, 4]).dtype, '    pixel positions, indexes')

    # astype() makes a copy in another type. Going to a whole-number type cuts
    # off the decimals; it does not round.
    readings: NDArray[np.float64] = np.array([0.4, 1.6, 254.7])
    print('astype(np.uint8) of', readings, '->', readings.astype(np.uint8))

    # The trap: uint8 has no room above 255, so arithmetic wraps round to 0.
    # Brightening a picture by adding 10 turns a nearly white pixel nearly black.
    pixel: NDArray[np.uint8] = np.array([250, 100], dtype=np.uint8)
    print('uint8 [250 100] + 10       ->', pixel + np.uint8(10), '  (250 wrapped round to 4)')
    # The fix: do the arithmetic in a bigger type, clip to 0..255, convert back.
    brighter: NDArray[np.uint8] = np.clip(pixel.astype(np.int16) + 10, 0, 255).astype(np.uint8)
    print('in int16, clipped to 0..255 ->', brighter)


def making_arrays() -> None:
    """Make arrays from nothing: filled with one value, the identity, or a range."""
    heading('3. Making arrays')

    print('np.zeros(3)          ', np.zeros(3))                  # e.g. the arm's start pose
    print('np.ones(3)           ', np.ones(3))
    print('np.full(3, 0.4)      ', np.full(3, 0.4))              # e.g. a flat table's depth
    # eye(n) is the identity matrix: ones down the diagonal. As a transform it
    # means "no turn and no shift", the usual starting value.
    print('np.eye(3):\n', np.eye(3))
    # arange: like Python's range, a step at a time. linspace: a number of
    # evenly spaced values, including both ends, which is what a trajectory needs.
    print('np.arange(0, 1, 0.25)', np.arange(0, 1, 0.25))
    print('np.linspace(0, 1, 5) ', np.linspace(0, 1, 5))
    # zeros_like makes an array with the same shape and dtype as another, such
    # as an empty mask the size of a depth picture.
    depth: NDArray[np.float32] = np.full((2, 3), 0.4, dtype=np.float32)
    empty: NDArray[np.float32] = np.zeros_like(depth)
    print('np.zeros_like(depth): shape', empty.shape, 'dtype', empty.dtype)


def reshaping() -> None:
    """Change how the same numbers are arranged, without changing the numbers."""
    heading('4. Changing the shape')

    # A ROS PointCloud2 or a file often gives the points as one long row:
    # x, y, z, x, y, z, ... reshape(-1, 3) turns it into one row per point.
    # -1 means "work this one out from the size": 12 numbers / 3 = 4 rows.
    flat: NDArray[np.float64] = np.arange(12, dtype=np.float64)
    points: NDArray[np.float64] = flat.reshape(-1, 3)
    print('np.arange(12).reshape(-1, 3):\n', points)

    # A picture as a list of pixels: every pixel a row of three colours. Handy
    # for colour statistics, where rows and columns do not matter.
    picture: NDArray[np.uint8] = np.zeros((240, 320, 3), dtype=np.uint8)
    print('picture', picture.shape, '-> reshape(-1, 3)', picture.reshape(-1, 3).shape)

    # ravel() or flatten() go the other way, back to one row.
    print('points.ravel()', points.ravel())

    # .T swaps the axes: (4, 3) becomes (3, 4), so each row is now all the x
    # values, all the y values, and all the z values.
    print('points.T: shape', points.T.shape, ' first row (every x)', points.T[0])

    # np.newaxis (or None) adds an axis of size 1. It turns one point, shape
    # (3,), into a one-row table, shape (1, 3), or a column, shape (3, 1).
    point: NDArray[np.float64] = np.array([1.0, 2.0, 3.0])
    print('point', point.shape, ' point[np.newaxis, :]', point[np.newaxis, :].shape,
          ' point[:, np.newaxis]', point[:, np.newaxis].shape)


def joining() -> None:
    """Put arrays together into one."""
    heading('5. Joining arrays')

    # Four points, given as their x values, their y values and their z values.
    x: NDArray[np.float64] = np.array([0.1, 0.2, 0.3, 0.4])
    y: NDArray[np.float64] = np.array([1.0, 1.1, 1.2, 1.3])
    z: NDArray[np.float64] = np.zeros(4)

    # column_stack puts separate x, y and z arrays side by side as columns:
    # one row per point, the usual shape for a point list.
    points: NDArray[np.float64] = np.column_stack([x, y, z])
    print('np.column_stack([x, y, z]):\n', points)

    # stack puts them on a new axis. axis=0 gives one row per coordinate, so
    # (3, 4); axis=1 gives one row per point, (4, 3), the same as column_stack.
    print('np.stack([x, y, z]).shape', np.stack([x, y, z]).shape,
          ' np.stack([x, y, z], axis=1).shape', np.stack([x, y, z], axis=1).shape)

    # concatenate joins along an existing axis: two scans of points become one
    # longer list. vstack and hstack are concatenate along axis 0 and axis 1.
    more: NDArray[np.float64] = np.array([[0.5, 0.5, 0.1]])
    print('np.concatenate([points, more]).shape', np.concatenate([points, more]).shape)

    # A column of ones on the right gives "homogeneous" points, (x, y, z, 1),
    # which a 4 x 4 transform can multiply. linear_algebra.py uses this.
    homogeneous: NDArray[np.float64] = np.hstack([points, np.ones((len(points), 1))])
    print('np.hstack([points, ones]):\n', homogeneous)


def views_and_copies() -> None:
    """Show that a slice shares its numbers with the array it came from."""
    heading('6. Views and copies')

    # A slice is a view: a new way of looking at the same numbers, not a copy.
    # That makes slicing fast, even of a big picture, but writing into the view
    # writes into the original too.
    picture: NDArray[np.uint8] = np.zeros((4, 6), dtype=np.uint8)
    corner: NDArray[np.uint8] = picture[0:2, 0:3]      # the top-left corner
    corner[:, :] = 255                                 # paint the corner white
    print('after painting the slice, the original picture is:\n', picture)
    print('np.shares_memory(picture, corner):', np.shares_memory(picture, corner))

    # .copy() makes an independent array. Use it when the original must stay
    # as it was, for example the camera's picture before you draw on it.
    safe: NDArray[np.uint8] = picture[0:2, 0:3].copy()
    safe[:, :] = 7
    print('after painting a copy, the corner is still', picture[0, 0],
          ' shares_memory:', np.shares_memory(picture, safe))


def bytes_and_files() -> None:
    """Turn an array into bytes and back, as a ROS message does, and save one."""
    heading('7. Bytes and files')

    # A sensor_msgs/Image carries its pixels as one long row of bytes, row after
    # row. tobytes() gives exactly that; it is how a camera driver fills
    # image.data.
    picture: NDArray[np.uint8] = np.zeros((240, 320, 3), dtype=np.uint8)
    picture[120, 160] = (220, 40, 40)                  # one red pixel in the middle
    data: bytes = picture.tobytes()
    print('picture.tobytes():', len(data), 'bytes')

    # frombuffer() goes back: it reads the bytes as numbers of the given type,
    # and reshape puts them back into rows, columns and colours. This is what
    # cv_bridge does for you when it turns an Image message into an array.
    received: NDArray[np.uint8] = np.frombuffer(data, dtype=np.uint8).reshape(240, 320, 3)
    print('np.frombuffer(...).reshape(240, 320, 3)[120, 160]:', received[120, 160])
    # The result looks at the message's own bytes, so NumPy makes it read-only.
    print('  writeable:', received.flags.writeable, ' (use .copy() to draw on it)')

    # A depth picture is float32, so its bytes are read back as float32.
    depth: NDArray[np.float32] = np.full((240, 320), 0.4, dtype=np.float32)
    depth_again: NDArray[np.float32] = np.frombuffer(
        depth.tobytes(), dtype=np.float32).reshape(240, 320)
    print('depth:', depth.nbytes, 'bytes, read back as', depth_again.dtype,
          'with', depth_again[0, 0], 'm in the first pixel')

    # np.save and np.load keep an array in a .npy file, with its shape and
    # dtype, for example a calibration or a recorded point cloud. np.savez keeps
    # several arrays in one .npz file, each under a name.
    with tempfile.TemporaryDirectory() as folder:
        path: pathlib.Path = pathlib.Path(folder) / 'lens.npz'
        lens: NDArray[np.float64] = np.array([[277.1, 0.0, 160.0],
                                              [0.0, 277.1, 120.0],
                                              [0.0, 0.0, 1.0]])
        np.savez(path, k=lens, d=np.zeros(5))
        loaded = np.load(path)
        print('np.savez then np.load: names', sorted(loaded.files),
              ' k[0, 0] =', loaded['k'][0, 0])


def main() -> None:
    """Run every section in order."""
    np.set_printoptions(precision=4, suppress=True)
    one_array()
    dtypes()
    making_arrays()
    reshaping()
    joining()
    views_and_copies()
    bytes_and_files()


if __name__ == '__main__':
    main()
