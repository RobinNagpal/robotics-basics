"""Which way a gripper points in 3D, written four ways.

Every number in sections 1 to 4 of
docs/01_robotics-intro/03_arm/02_frames-in-3d.md is printed by this file. It
covers:

  1. a pose: three numbers for where, three for which way
  2. the axes: x forward, y left, z up, and the right-hand rule
  3. roll, pitch and yaw, each shown on a gripper on its own
  4. one orientation written four ways, and the awkward case (gimbal lock)

The gripper points along its own x axis, the way the tool tip in the frames doc
sits 1 m along the gripper's x axis. Its z axis is the gripper's "up".

Roll, pitch and yaw here are the ROS convention (REP 103): turns about the fixed
x, y and z axes, applied in that order. SciPy calls that 'xyz', in lower case.

Run it with:  pixi run python src/frames_3d/orientation.py
"""

import math
import warnings

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

# Print 3 decimals, and never print -0.
np.set_printoptions(precision=3, suppress=True)

X_AXIS: NDArray[np.float64] = np.array([1.0, 0.0, 0.0])
Y_AXIS: NDArray[np.float64] = np.array([0.0, 1.0, 0.0])
Z_AXIS: NDArray[np.float64] = np.array([0.0, 0.0, 1.0])

#: The orientation section 4 writes four ways: turned 30 degrees left, tilted
#: 45 degrees down, and twisted 20 degrees about its own pointing direction.
ROLL_DEG: float = 20.0
PITCH_DEG: float = 45.0
YAW_DEG: float = 30.0


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def clean(a: NDArray[np.float64]) -> NDArray[np.float64]:
    """Round away floating-point dust, so cos(90) prints as 0 and not 6e-17."""
    return np.round(a, 9) + 0.0


def vec(a: NDArray[np.float64]) -> str:
    """Write a vector as (x, y, z) or (x, y, z, w) with 3 decimals, lined up in columns."""
    return '(' + ', '.join(f'{v + 0.0:6.3f}' for v in a) + ')'


def rpy(roll_deg: float, pitch_deg: float, yaw_deg: float) -> Rotation:
    """Make a turn from roll, pitch and yaw in degrees, the ROS way."""
    return Rotation.from_euler('xyz', [roll_deg, pitch_deg, yaw_deg], degrees=True)


def pose() -> None:
    """Print a pose: three numbers for the position, three for the orientation."""
    heading('1. A pose: where, and which way')

    position: NDArray[np.float64] = np.array([0.6, 0.1, 0.2])
    print('position    (x, y, z) in metres    ', position)
    print(f'orientation (roll, pitch, yaw)       '
          f'({ROLL_DEG:.0f}, {PITCH_DEG:.0f}, {YAW_DEG:.0f}) degrees')
    print('six numbers in all')


def axes() -> None:
    """Check the right-hand rule that ties x forward, y left and z up together."""
    heading('2. The axes and the right-hand rule')

    # The right-hand rule, as arithmetic: the cross product of x and y is z.
    print('x cross y =', np.cross(X_AXIS, Y_AXIS), ' <- z, pointing up')
    print('y cross z =', np.cross(Y_AXIS, Z_AXIS), ' <- x')
    print('z cross x =', np.cross(Z_AXIS, X_AXIS), ' <- y')
    # Put y on the right instead of the left, and z comes out pointing down.
    y_right: NDArray[np.float64] = -Y_AXIS
    print('x cross (y on the right) =', np.cross(X_AXIS, y_right) + 0.0,
          ' <- z would point down')


def roll_pitch_yaw() -> None:
    """Show each of the three turns on its own, on a gripper."""
    heading('3. Roll, pitch and yaw on a gripper')

    print('                      points along (its x)       its up (its z)')
    print(f'no turn               {vec(X_AXIS)}    {vec(Z_AXIS)}')
    for name, turn in (('roll 90 (about x)', rpy(90, 0, 0)),
                       ('pitch 45 (about y)', rpy(0, 45, 0)),
                       ('yaw 90 (about z)', rpy(0, 0, 90))):
        pointing: NDArray[np.float64] = clean(turn.apply(X_AXIS))
        up: NDArray[np.float64] = clean(turn.apply(Z_AXIS))
        print(f'{name:<20}  {vec(pointing)}    {vec(up)}')


def four_ways() -> None:
    """Write one orientation as a matrix, as roll-pitch-yaw, as axis-angle and as a quaternion."""
    heading('4a. One orientation, four ways')

    turn: Rotation = rpy(ROLL_DEG, PITCH_DEG, YAW_DEG)
    print(f'made from roll {ROLL_DEG:.0f}, pitch {PITCH_DEG:.0f}, yaw {YAW_DEG:.0f} degrees')

    matrix: NDArray[np.float64] = turn.as_matrix()
    print('\nrotation matrix (9 numbers):\n', matrix)
    print('first column, where the gripper points:', matrix[:, 0])

    print('\nroll, pitch, yaw read back (3 numbers):', turn.as_euler('xyz', degrees=True))

    rotvec: NDArray[np.float64] = turn.as_rotvec()
    angle: float = float(np.linalg.norm(rotvec))
    print(f'\naxis-angle (4 numbers): axis {rotvec / angle}, '
          f'angle {math.degrees(angle):.1f} degrees')

    quat: NDArray[np.float64] = turn.as_quat()
    print('\nquaternion (x, y, z, w), 4 numbers:', quat)
    print(f'its length: {np.linalg.norm(quat):.3f}')
    half: float = angle / 2.0
    print(f'w = cos(angle / 2) = cos({math.degrees(half):.1f}) = {math.cos(half):.3f}')
    print('(x, y, z) = axis * sin(angle / 2) =', rotvec / angle * math.sin(half))

    # All four describe one turn, so all four point the gripper the same way.
    from_rotvec: NDArray[np.float64] = Rotation.from_rotvec(rotvec).apply(X_AXIS)
    from_quat: NDArray[np.float64] = Rotation.from_quat(quat).apply(X_AXIS)
    print('\npointing, from the axis-angle:', from_rotvec)
    print('pointing, from the quaternion:', from_quat)


def gimbal_lock() -> None:
    """At pitch 90 degrees, roll and yaw stop being different things."""
    heading('4b. The awkward case: pitch 90 degrees (gimbal lock)')

    print('three different sets of numbers, at pitch 90 (the gripper points straight down):')
    first: Rotation = rpy(10, 90, 0)
    for r, p, y in ((10, 90, 0), (0, 90, -10), (30, 90, 20)):
        turn: Rotation = rpy(r, p, y)
        same: bool = bool(np.allclose(turn.as_matrix(), first.as_matrix()))
        print(f'  roll {r:>3}, pitch {p}, yaw {y:>4}  ->  quaternion {vec(turn.as_quat())}'
              f'  same turn as the first: {same}')

    print('the same test at pitch 80, where nothing is locked:')
    a: Rotation = rpy(10, 80, 0)
    b: Rotation = rpy(0, 80, -10)
    print(f'  roll 10, yaw 0  and  roll 0, yaw -10  same turn: '
          f'{bool(np.allclose(a.as_matrix(), b.as_matrix()))}')

    # Reading angles back at the lock: SciPy cannot tell roll from yaw, and says so.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        back: NDArray[np.float64] = first.as_euler('xyz', degrees=True)
    print('\nroll 10, pitch 90, yaw 0 read back as', back + 0.0)
    for w in caught:
        print('  SciPy warns:', str(w.message).split('.')[0])

    # Near the lock, a small tilt makes roll and yaw jump.
    print('\ntilting down past straight down, 1 degree at a time:')
    for pitch in (88.0, 89.0, 91.0, 92.0):
        tilt: Rotation = rpy(10, pitch, 0)
        read: NDArray[np.float64] = tilt.as_euler('xyz', degrees=True) + 0.0
        print(f'  tilted {pitch:.0f} degrees  ->  roll {read[0]:7.1f}  pitch {read[1]:5.1f}'
              f'  yaw {read[2]:7.1f}   quaternion {vec(tilt.as_quat())}')


if __name__ == '__main__':
    pose()
    axes()
    roll_pitch_yaw()
    four_ways()
    gimbal_lock()
