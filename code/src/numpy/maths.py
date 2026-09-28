"""Maths on whole arrays: one line of arithmetic works on every value at once.

This is the reason robotics code uses NumPy. A depth picture has 76,800
readings, and a Python loop over them is slow and long. NumPy does the same
arithmetic on the whole array in one line, and far faster. This file covers:

  1. element-wise maths: +, -, *, /, sin, cos, arctan2, hypot, degrees and radians
  2. broadcasting: arithmetic between arrays of different shapes
  3. reductions: sum, mean, min, max, norm, along one axis or all of them
  4. values over time: diff, cumsum, and smoothing with convolve
  5. angles: wrapping to -180..180 degrees, and unwrap
  6. comparing decimal numbers: isclose and allclose
  7. how much faster it is than a loop

The file is called maths.py and not math.py, because a file called math.py
would hide Python's own math module from every program run in this folder.

Run it with:  pixi run python src/numpy/maths.py
"""

from collections.abc import Callable
import math
import time

import numpy as np
from numpy.typing import NDArray

# The same six points as indexing.py: two on the table, four on top of a box.
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


def element_wise() -> None:
    """Do the same arithmetic on every value, with no loop."""
    heading('1. Element-wise maths')

    # Arithmetic between two arrays of the same shape pairs them up value by
    # value: the first with the first, the second with the second, and so on.
    start: NDArray[np.float64] = np.array([0.0, 0.5, 1.0])
    goal: NDArray[np.float64] = np.array([0.3, 0.5, 0.4])
    print('goal - start      ', goal - start, '  how far each joint has to turn')
    print('(goal - start) / 2', (goal - start) / 2, '  half way')

    # Maths functions work on every value too. Joint angles in ROS are radians;
    # np.deg2rad and np.rad2deg convert (np.radians and np.degrees are the same).
    degrees: NDArray[np.float64] = np.array([0.0, 30.0, 45.0, 90.0])
    radians: NDArray[np.float64] = np.deg2rad(degrees)
    print('np.deg2rad', degrees, '->', radians)
    print('np.sin of those     ', np.sin(radians))
    print('np.cos of those     ', np.cos(radians))

    # np.arctan2(y, x) gives the angle of the direction (x, y). Plain arctan(y / x)
    # cannot tell (1, 1) from (-1, -1), because y / x is 1 for both. arctan2
    # gets every direction right, which is why it is the one robots use.
    x: NDArray[np.float64] = np.array([1.0, -1.0, 0.0])
    y: NDArray[np.float64] = np.array([1.0, -1.0, 2.0])
    print('np.rad2deg(np.arctan(y / x)) ', np.rad2deg(np.arctan(y[:2] / x[:2])),
          ' (wrong for (-1, -1))')
    print('np.rad2deg(np.arctan2(y, x)) ', np.rad2deg(np.arctan2(y, x)))
    # np.hypot(x, y) is the length sqrt(x*x + y*y): how far away each point is.
    print('np.hypot(x, y)               ', np.hypot(x, y))


def broadcasting() -> None:
    """Do arithmetic between arrays of different shapes."""
    heading('2. Broadcasting')

    # A (6, 3) array plus a (3,) array: NumPy lines the shapes up from the
    # right, sees that the 3s match, and uses the one row for every row. Every
    # point is shifted by the same amount: here, moved 0.40 m up.
    shift: NDArray[np.float64] = np.array([0.0, 0.0, 0.40])
    print('POINTS.shape', POINTS.shape, '+ shift.shape', shift.shape, '->',
          (POINTS + shift).shape)
    print('(POINTS + shift)[:2]:\n', (POINTS + shift)[:2])

    # A column (4, 1) against a row (1, 3) grows into a (4, 3) table: every
    # row value paired with every column value. This is how a camera program
    # makes the column number u of every pixel without a loop.
    rows: NDArray[np.float64] = np.arange(4.0)[:, np.newaxis]     # shape (4, 1)
    cols: NDArray[np.float64] = np.arange(3.0)[np.newaxis, :]     # shape (1, 3)
    print('rows (4, 1) * 10 + cols (1, 3) ->\n', rows * 10 + cols)

    # A depth picture divided by one number: every reading at once. Here the
    # pixel size in metres, depth / fx, for a whole (240, 320) picture.
    depth: NDArray[np.float32] = np.full((240, 320), 0.40, dtype=np.float32)
    pixel_size: NDArray[np.float32] = depth / np.float32(277.1)
    print('depth / 277.1 ->', pixel_size.shape, 'values, each', f'{pixel_size[0, 0]:.5f} m')

    # If the shapes do not line up, NumPy refuses rather than guess.
    try:
        POINTS + np.array([1.0, 2.0])
    except ValueError as error:
        print('POINTS + a (2,) array -> ValueError:', error)


def reductions() -> None:
    """Boil an array down to fewer numbers: along one axis, or all of them."""
    heading('3. Reductions: sum, mean, min, max, norm')

    # With no axis, a reduction uses every value.
    print('POINTS.max()        ', POINTS.max())
    # axis=0 goes down the rows, and gives one answer per column: the average
    # x, the average y and the average z. That is the middle, or centroid, of
    # the points, which is how the camera area finds the middle of the box.
    box: NDArray[np.float64] = POINTS[POINTS[:, 2] > 0.01]
    print('box.mean(axis=0)    ', box.mean(axis=0), '  the middle of the box top')
    print('box.min(axis=0)     ', box.min(axis=0))
    print('box.max(axis=0)     ', box.max(axis=0))
    # max minus min, per column, is the size of the smallest box round them.
    print('np.ptp(box, axis=0) ', np.ptp(box, axis=0), '  size along x, y, z')
    # axis=1 goes along each row, and gives one answer per point: here, how
    # far each point is from the camera's spot, with np.linalg.norm.
    camera: NDArray[np.float64] = np.array([0.0, 0.0, 0.40])
    print('np.linalg.norm(POINTS - camera, axis=1)', np.linalg.norm(POINTS - camera, axis=1))
    # std is the spread: how far the values are, on average, from their mean.
    print('box[:, 2].std()     ', f'{box[:, 2].std():.5f}')

    # The median is the middle value when they are sorted. One wild reading
    # moves the mean a lot, and the median hardly at all, so the median is the
    # safer average for sensor readings.
    readings: NDArray[np.float64] = np.array([0.40, 0.41, 0.39, 0.40, 3.00])
    print('readings', readings, f' mean {readings.mean():.2f}', ' median', np.median(readings))


def over_time() -> None:
    """Work with readings taken one after another."""
    heading('4. Values over time: diff, cumsum, convolve')

    # A gripper's x position, read ten times a second.
    dt: float = 0.1
    x: NDArray[np.float64] = np.array([0.00, 0.01, 0.03, 0.06, 0.10, 0.15])
    # np.diff gives the change from each reading to the next, one fewer than
    # there are readings. Divided by the time between them, it is the speed.
    speed: NDArray[np.float64] = np.diff(x) / dt
    print('np.diff(x) / dt  ', speed, ' m/s')
    # np.cumsum adds up as it goes: from the speeds back to the positions.
    print('np.cumsum(speed) * dt', np.cumsum(speed) * dt)

    # np.convolve slides a small window along the readings. A window of three
    # thirds is a moving average, which smooths out a noisy sensor.
    noisy: NDArray[np.float64] = np.array([0.40, 0.43, 0.38, 0.41, 0.39, 0.42])
    window: NDArray[np.float64] = np.ones(3) / 3
    print('moving average   ', np.convolve(noisy, window, mode='valid'))


def angles() -> None:
    """Keep angles in one turn, and undo the jumps where they wrap round."""
    heading('5. Angles: wrap and unwrap')

    # An angle and the same angle plus a full turn point the same way. Robots
    # keep angles between -pi and pi (-180 and 180 degrees). This one line
    # brings any angle into that range: add half a turn, take the remainder
    # after whole turns, and take the half turn off again.
    raw: NDArray[np.float64] = np.deg2rad(np.array([190.0, -200.0, 370.0, 90.0]))
    wrapped: NDArray[np.float64] = (raw + np.pi) % (2 * np.pi) - np.pi
    print('wrap [190, -200, 370, 90] ->', np.rad2deg(wrapped).round(1), 'degrees')

    # The opposite problem: a wheel that keeps turning, recorded as wrapped
    # angles, jumps from 170 to -170 degrees. np.unwrap removes the jumps, so
    # the angle keeps growing and can be differenced into a speed.
    recorded: NDArray[np.float64] = np.deg2rad(np.array([150.0, 170.0, -170.0, -150.0]))
    print('np.unwrap([150, 170, -170, -150]) ->', np.rad2deg(np.unwrap(recorded)).round(1))


def comparing() -> None:
    """Compare decimal numbers, which are almost never exactly equal."""
    heading('6. Comparing decimal numbers')

    # Decimal numbers are stored in binary, so 0.1 + 0.2 is not exactly 0.3.
    print('0.1 + 0.2 == 0.3           ', 0.1 + 0.2 == 0.3)
    # np.isclose allows a tiny difference; np.allclose asks it for every value.
    # Tests use these to check a transform or a position.
    print('np.isclose(0.1 + 0.2, 0.3) ', np.isclose(0.1 + 0.2, 0.3))
    arm_says: NDArray[np.float64] = np.array([3 * math.cos(math.radians(30)), 3.5])
    print('np.allclose([3 cos 30°, 3.5], [2.598, 3.5], atol=1e-3)',
          np.allclose(arm_says, [2.598, 3.5], atol=1e-3))


def timed(job: Callable[[], object]) -> float:
    """Run a job once, and say how many seconds it took."""
    start: float = time.perf_counter()
    job()
    return time.perf_counter() - start


def speed_against_a_loop() -> None:
    """Time a Python loop and NumPy doing the same job on a whole depth picture."""
    heading('7. How much faster it is than a loop')

    # The camera area's calculation: x = (u - cx) * depth / fx for every pixel
    # of a 320 x 240 depth picture.
    depth: NDArray[np.float64] = np.full((240, 320), 0.40)
    fx: float = 277.1
    cx: float = 160.0

    def with_a_loop() -> list[list[float]]:
        return [[(col + 0.5 - cx) * float(depth[row, col]) / fx for col in range(320)]
                for row in range(240)]

    def with_numpy() -> NDArray[np.float64]:
        u: NDArray[np.float64] = np.arange(320, dtype=np.float64) + 0.5   # every column's middle
        return (u - cx) * depth / fx

    # Each is timed five times, and the fastest run kept, so that the computer
    # doing something else for a moment does not spoil the comparison.
    loop_seconds: float = min(timed(with_a_loop) for _ in range(5))
    numpy_seconds: float = min(timed(with_numpy) for _ in range(5))
    x_loop: list[list[float]] = with_a_loop()
    x_numpy: NDArray[np.float64] = with_numpy()

    print('same answer:', np.allclose(x_loop, x_numpy))
    print(f'loop  {loop_seconds * 1000:7.2f} ms')
    print(f'numpy {numpy_seconds * 1000:7.2f} ms,'
          f' about {loop_seconds / numpy_seconds:,.0f} times faster')


def main() -> None:
    """Run every section in order."""
    np.set_printoptions(precision=4, suppress=True)
    element_wise()
    broadcasting()
    reductions()
    over_time()
    angles()
    comparing()
    speed_against_a_loop()


if __name__ == '__main__':
    main()
