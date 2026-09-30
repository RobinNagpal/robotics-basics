"""The frames of an arm cell, and a cup carried from the camera to the gripper.

Every number in sections 5 and 6 of
docs/01_robotics-intro/03_arm/02_frames-in-3d.md is printed by this file. It
covers:

  5. the named frames of a cell, and which ones stay put
  6. a worked chain in 3D, with 4 x 4 matrices:
     a. a camera sees a cup; where is the cup from the arm's base?
     b. where should the fingertips go, and where does that put the flange?
     c. flipped: where is the cup, seen from the gripper?

Poses use the ROS roll, pitch and yaw convention, as orientation.py does. The
gripper points along its own x axis.

Run it with:  pixi run python src/frames_3d/cell_chain.py
"""

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

# Print 3 decimals, and never print -0.
np.set_printoptions(precision=3, suppress=True)

#: The camera sits on a stand 1.2 m in front of the arm and 0.7 m up. It is turned
#: round to look back at the arm (yaw 180) and tipped 45 degrees down (pitch 45).
CAMERA_XYZ: tuple[float, float, float] = (1.2, 0.0, 0.7)
CAMERA_RPY: tuple[float, float, float] = (0.0, 45.0, 180.0)

#: What the camera measures: the middle of the cup, 0.849 m straight out of the
#: lens and 0.1 m to the camera's left.
CUP_IN_CAMERA: tuple[float, float, float] = (0.849, 0.1, 0.0)

#: The fingertips (the tool centre point) are 0.15 m beyond the flange, along
#: the gripper's pointing direction. Measured once, when the gripper was fitted.
TCP_OFFSET_M: float = 0.15

#: The grasp: fingertips 0.10 m above the middle of the cup, pointing straight down.
ABOVE_CUP_M: float = 0.10
POINT_DOWN_RPY: tuple[float, float, float] = (0.0, 90.0, 0.0)


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def vec(a: NDArray[np.float64]) -> str:
    """Write a vector as (x, y, z) with 3 decimals."""
    return '(' + ', '.join(f'{v + 0.0:.3f}' for v in a) + ')'


def transform(xyz: tuple[float, float, float],
              rpy_deg: tuple[float, float, float]) -> NDArray[np.float64]:
    """Make a 4 x 4 transform: turn by roll, pitch, yaw, then shift by xyz."""
    t: NDArray[np.float64] = np.eye(4)
    t[:3, :3] = Rotation.from_euler('xyz', rpy_deg, degrees=True).as_matrix()
    t[:3, 3] = xyz
    return t


def flip(t: NDArray[np.float64]) -> NDArray[np.float64]:
    """Flip a transform: undo the turn (transpose it), then undo the shift."""
    r: NDArray[np.float64] = t[:3, :3]
    flipped: NDArray[np.float64] = np.eye(4)
    flipped[:3, :3] = r.T
    flipped[:3, 3] = -r.T @ t[:3, 3]
    return flipped


def point(t: NDArray[np.float64], p: NDArray[np.float64]) -> NDArray[np.float64]:
    """Apply a 4 x 4 transform to a 3D point: add the 1, multiply, drop the 1."""
    result: NDArray[np.float64] = (t @ np.append(p, 1.0))[:3]
    return np.round(result, 9) + 0.0


def frames() -> None:
    """List the frames of the cell, each with its parent and whether it moves."""
    heading('5. The frames of an arm cell')

    rows: list[tuple[str, str, str]] = [
        ('world', '-', 'the room; everything else hangs off it'),
        ('base_link', 'world', 'static: the arm is bolted down'),
        ('tool0 (flange)', 'base_link', 'moves: through the six joints between them'),
        ('tcp', 'tool0', 'static: the gripper is bolted on'),
        ('camera', 'world', 'static: the camera is on a stand'),
        ('cup', 'camera', 'new in every picture'),
    ]
    for name, parent, note in rows:
        print(f'  {name:<15} parent {parent:<10} {note}')


def camera_to_base() -> NDArray[np.float64]:
    """Move the cup the camera saw into the base_link frame."""
    heading('6a. The cup, from the camera to the base')

    base_camera: NDArray[np.float64] = transform(CAMERA_XYZ, CAMERA_RPY)
    print('base_link -> camera (measured once):\n', np.round(base_camera, 9) + 0.0)
    print('the camera looks along its x axis, which in base_link is', vec(base_camera[:3, 0]))

    cup_camera: NDArray[np.float64] = np.array(CUP_IN_CAMERA)
    cup_base: NDArray[np.float64] = point(base_camera, cup_camera)
    print('cup in the camera frame   ', vec(cup_camera))
    print('cup in the base_link frame', vec(cup_base))
    return cup_base


def grasp(cup_base: NDArray[np.float64]) -> NDArray[np.float64]:
    """Work out where the fingertips should go, and where that puts the flange."""
    heading('6b. Where the gripper should go')

    tcp_xyz: tuple[float, float, float] = (
        float(cup_base[0]), float(cup_base[1]), float(cup_base[2]) + ABOVE_CUP_M)
    base_tcp: NDArray[np.float64] = transform(tcp_xyz, POINT_DOWN_RPY)
    print('fingertip target, base_link -> tcp:\n', np.round(base_tcp, 9) + 0.0)
    print('the fingertips point along', vec(base_tcp[:3, 0]), ' <- straight down')

    # tool0 -> tcp is fixed. To find where the flange must go, take the
    # fingertip target and step back along the gripper: join with the flip.
    tool0_tcp: NDArray[np.float64] = transform((TCP_OFFSET_M, 0.0, 0.0), (0.0, 0.0, 0.0))
    base_tool0: NDArray[np.float64] = base_tcp @ flip(tool0_tcp)
    print('flange target, base_link -> tool0: at', vec(base_tool0[:3, 3]),
          f' <- {TCP_OFFSET_M:.2f} m above the fingertips')
    return base_tcp


def cup_from_gripper(cup_base: NDArray[np.float64], base_tcp: NDArray[np.float64]) -> None:
    """Flip the gripper's transform to see the cup from the fingertips."""
    heading('6c. Flipped: the cup, seen from the gripper')

    tcp_base: NDArray[np.float64] = flip(base_tcp)
    print('tcp -> base_link:\n', np.round(tcp_base, 9) + 0.0)
    print('cup in the tcp frame', vec(point(tcp_base, cup_base)),
          ' <- 0.1 m straight ahead of the fingertips')

    # Flipping twice gives back what you started with.
    twice: float = float(np.abs(flip(tcp_base) - base_tcp).max())
    print(f'flipped twice, the biggest difference from the start: {twice:.1e}')


if __name__ == '__main__':
    frames()
    cup = camera_to_base()
    target = grasp(cup)
    cup_from_gripper(cup, target)
