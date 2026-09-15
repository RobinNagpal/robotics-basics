"""Sampling: grids of positions, values in between, and random numbers.

Robots sample the world at fixed steps: every pixel of a picture, every cell of
a map, every tenth of a second of a trajectory. They also need made-up noise to
test against, and random picks for algorithms that try many guesses. This file
covers:

  1. grids: the position of every pixel with mgrid, and a map of cells
  2. in-between values: np.interp for a trajectory
  3. random numbers: the Generator class, noise, and random picks
  4. what a set of readings looks like: histogram, mean, std

The file is called sampling.py and not random.py, because a file called
random.py would hide Python's own random module from every program run in
this folder.

Run it with:  pixi run python src/numpy/sampling.py
"""

import math

import numpy as np
from numpy.typing import NDArray

# A joint's waypoints: 0 degrees at the start, 40 degrees after 1 second, and
# 60 degrees after 3 seconds.
WAYPOINT_TIMES: NDArray[np.float64] = np.array([0.0, 1.0, 3.0])
WAYPOINT_ANGLES: NDArray[np.float64] = np.array([0.0, 40.0, 60.0])

# A depth camera reading a table 0.40 m away, with noise that spreads 5 mm.
TABLE_DEPTH: float = 0.40
NOISE: float = 0.005


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def grids() -> None:
    """Make the position of every pixel, and put points into the cells of a map."""
    heading('1. Grids: mgrid, meshgrid, and a map of cells')

    # np.mgrid[0:3, 0:4] gives two arrays the shape of a 3 x 4 picture: the
    # row number of every pixel, and the column number of every pixel. Adding
    # 0.5 gives the middle of each pixel. With these, a formula written for one
    # pixel works on the whole picture at once.
    v: NDArray[np.float64]
    u: NDArray[np.float64]
    v, u = np.mgrid[0:3, 0:4] + 0.5
    print('v (row of every pixel):\n', v)
    print('u (column of every pixel):\n', u)

    # np.meshgrid does the same from two lists. It puts x across and y down,
    # so it returns (u, v), in the opposite order to mgrid.
    u2: NDArray[np.float64]
    v2: NDArray[np.float64]
    u2, v2 = np.meshgrid(np.arange(4) + 0.5, np.arange(3) + 0.5)
    print('np.meshgrid gives the same u and v:', np.array_equal(u, u2) and np.array_equal(v, v2))

    # A tiny depth picture, 3 x 4 pixels, all 0.4 m away, turned into one 3D
    # point per pixel, the way the camera area does it for 320 x 240 pixels.
    # Its lens sees 60 degrees across, like the camera area's, which across a
    # picture 4 pixels wide makes the focal length 3.46 pixels.
    depth: NDArray[np.float64] = np.full((3, 4), 0.40)
    fx: float = (4 / 2) / math.tan(math.radians(30))
    cx: float = 2.0
    cy: float = 1.5
    x: NDArray[np.float64] = (u - cx) * depth / fx
    y: NDArray[np.float64] = (v - cy) * depth / fx
    cloud: NDArray[np.float64] = np.stack([x, y, depth], axis=-1).reshape(-1, 3)
    print('12 pixels -> 12 points; the first two:\n', cloud[:2].round(4))

    # A map of the table as cells 10 cm wide, 1 m by 0.5 m, True where
    # something stands. np.floor(position / cell size) gives each point's cell.
    cell: float = 0.10
    occupied: NDArray[np.bool_] = np.zeros((5, 10), dtype=bool)      # rows: y, columns: x
    obstacles: NDArray[np.float64] = np.array([[0.05, 0.12], [0.55, 0.31], [0.57, 0.38]])
    cells: NDArray[np.int64] = np.floor(obstacles / cell).astype(np.int64)
    occupied[cells[:, 1], cells[:, 0]] = True
    print('cells (column, row):', cells.tolist(), ' (the last two share a cell)')
    print('the map, # for occupied:')
    for row in occupied[::-1]:                     # the top row first, so y grows upwards
        print('   ', ''.join('#' if full else '.' for full in row))


def in_between() -> None:
    """Fill in the values between a few waypoints."""
    heading('2. In-between values: np.interp')

    # A joint told to be at 0 degrees at the start, 40 degrees after 1 second,
    # and 60 degrees after 3 seconds. The controller needs an angle every few
    # moments, so np.interp fills in the ones in between, on straight lines
    # from waypoint to waypoint. Here, one every half second.
    every_half_second: NDArray[np.float64] = np.arange(0.0, 3.01, 0.5)
    print('times ', every_half_second)
    print('angles', np.interp(every_half_second, WAYPOINT_TIMES, WAYPOINT_ANGLES))

    # np.linspace gives a number of evenly spaced values, including both ends:
    # here, 5 positions on a straight line from the gripper to a cup.
    gripper: NDArray[np.float64] = np.array([0.30, 0.00, 0.20])
    cup: NDArray[np.float64] = np.array([0.50, 0.20, 0.05])
    steps: NDArray[np.float64] = np.linspace(0.0, 1.0, 5)[:, np.newaxis]
    print('np.linspace path, gripper to cup:\n', gripper + steps * (cup - gripper))


def random_numbers() -> None:
    """Make noise, random positions and random picks, the same every run."""
    heading('3. Random numbers: the Generator class')

    # np.random.default_rng makes a Generator, NumPy's source of random
    # numbers. Giving it a seed makes it produce the same numbers every run,
    # which a test needs, so that a failure can be repeated.
    rng: np.random.Generator = np.random.default_rng(seed=0)
    print('type:', type(rng).__name__)

    # normal(mean, spread, count): noise like a real sensor's. A depth camera
    # reading a table 0.40 m away, with a spread of 5 mm.
    readings: NDArray[np.float64] = rng.normal(TABLE_DEPTH, NOISE, 5)
    print('rng.normal(0.40, 0.005, 5)  ', readings.round(4))
    # uniform(low, high, shape): anywhere in a range, all equally likely. Three
    # places to put a box on a 60 x 40 cm table, as (x, y).
    print('rng.uniform(...) box places:\n', rng.uniform([0.0, 0.0], [0.6, 0.4], (3, 2)).round(3))
    # integers(low, high, count): whole numbers; high is not included.
    print('rng.integers(0, 320, 4)     ', rng.integers(0, 320, 4), ' random columns')
    # choice(count, how many, replace=False): picks without repeats. RANSAC,
    # which finds a table in a point cloud, picks 3 random points again and again.
    print('rng.choice(1000, 3, replace=False)', rng.choice(1000, 3, replace=False))
    # The same seed gives the same numbers again.
    again: NDArray[np.float64] = np.random.default_rng(seed=0).normal(TABLE_DEPTH, NOISE, 5)
    print('same seed, same readings:', np.array_equal(readings, again))


def noisy_readings(count: int) -> NDArray[np.float64]:
    """Make this many readings of the table, with the sensor's noise, the same every run."""
    rng: np.random.Generator = np.random.default_rng(seed=0)
    return rng.normal(TABLE_DEPTH, NOISE, count)


def readings_summary() -> None:
    """Describe many noisy readings with a few numbers and a histogram."""
    heading('4. What a set of readings looks like: histogram, mean, std')

    readings: NDArray[np.float64] = noisy_readings(10_000)
    print(f'10,000 readings: mean {readings.mean():.4f} m, std {readings.std():.4f} m,'
          f' min {readings.min():.4f}, max {readings.max():.4f}')
    # np.histogram counts how many readings fall in each band ("bin").
    counts: NDArray[np.intp]
    edges: NDArray[np.float64]
    counts, edges = np.histogram(readings, bins=8, range=(0.38, 0.42))
    for count, low in zip(counts, edges[:-1]):
        print(f'  {low:.3f} to {low + 0.005:.3f} m  {count:5d}  {"#" * int(count // 100)}')
    # About 68 % of normal noise is within one spread of the mean.
    within: float = float(np.mean(np.abs(readings - TABLE_DEPTH) < NOISE))
    print(f'within 5 mm of 0.40 m: {within:.1%}')


def main() -> None:
    """Run every section in order."""
    np.set_printoptions(precision=4, suppress=True)
    grids()
    in_between()
    random_numbers()
    readings_summary()


if __name__ == '__main__':
    main()
