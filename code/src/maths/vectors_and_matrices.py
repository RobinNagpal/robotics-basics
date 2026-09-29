"""Vectors and matrices, worked out on the two-link arm.

Every number in docs/01_robotics-intro/02_maths/02_vectors-and-matrices.md is
printed by this file. It covers:

  1. vectors: each link as an arrow, and adding them tip to tail
  2. length and direction of a vector
  3. the dot product: the angle between two links
  4. a rotation matrix, and what its columns are
  5. multiplying matrices, and why the order matters
  6. the 3 x 3 transform matrix: a turn and a shift together
  7. turning in 3D about x, y and z, and the 4 x 4 transform

The arm is the one the frames doc uses: link 1 is 3 m, link 2 is 2 m, and the
pose is q1 = 30 degrees, q2 = 60 degrees.

Run it with:  pixi run python src/maths/vectors_and_matrices.py
"""

import math

import numpy as np
from numpy.typing import NDArray

# The two-link arm from the frames doc: link lengths in metres.
LINK1: float = 3.0
LINK2: float = 2.0
Q1: float = math.radians(30.0)
Q2: float = math.radians(60.0)

# Print 3 decimals, and never print -0.
np.set_printoptions(precision=3, suppress=True)


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def clean(a: NDArray[np.float64]) -> NDArray[np.float64]:
    """Round away floating-point dust, so cos(90) prints as 0 and not 6e-17."""
    return np.round(a, 9) + 0.0


def rot2(angle: float) -> NDArray[np.float64]:
    """Make the 2 x 2 matrix that turns a point by this many radians."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[c, -s],
                     [s, c]])


def transform2(angle: float, shift_x: float, shift_y: float) -> NDArray[np.float64]:
    """Make the 3 x 3 matrix that turns by an angle, then shifts."""
    matrix: NDArray[np.float64] = np.eye(3)
    matrix[:2, :2] = rot2(angle)       # top left: the turn
    matrix[:2, 2] = [shift_x, shift_y]  # right column: the shift
    return matrix


def rot_x(angle: float) -> NDArray[np.float64]:
    """Turn about the x axis: y swings towards z."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_y(angle: float) -> NDArray[np.float64]:
    """Turn about the y axis: z swings towards x."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rot_z(angle: float) -> NDArray[np.float64]:
    """Turn about the z axis: x swings towards y."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def link_vectors() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Each link as an arrow: its length, in the direction it points on the table."""
    link1: NDArray[np.float64] = LINK1 * np.array([math.cos(Q1), math.sin(Q1)])
    link2: NDArray[np.float64] = LINK2 * np.array([math.cos(Q1 + Q2), math.sin(Q1 + Q2)])
    return clean(link1), clean(link2)


def vectors() -> None:
    """Add the link arrows tip to tail to find the gripper."""
    heading('1. Vectors: the links as arrows')

    link1, link2 = link_vectors()
    print('link 1 arrow  ', link1)
    print('link 2 arrow  ', link2)
    print('link1 + link2 ', link1 + link2, ' <- the gripper, seen from the base')


def length_and_direction() -> None:
    """Split an arrow into how long it is and which way it points."""
    heading('2. Length and direction')

    link1, link2 = link_vectors()
    gripper: NDArray[np.float64] = link1 + link2
    print(f'length of link 1 arrow   {np.linalg.norm(link1):.3f}')
    print(f'length of link 2 arrow   {np.linalg.norm(link2):.3f}')
    distance: float = float(np.linalg.norm(gripper))
    print(f'length of gripper arrow  {distance:.3f}  (not 3 + 2: the links are not in line)')
    print('direction (unit vector)  ', gripper / distance)
    print(f'its length               {np.linalg.norm(gripper / distance):.3f}')


def dot_product() -> None:
    """Use the dot product to read the elbow angle off the two link arrows."""
    heading('3. The dot product: the angle between the links')

    link1, link2 = link_vectors()
    dot: float = float(link1 @ link2)
    print(f'link1 . link2 = {link1[0]:.3f} x {link2[0]:.0f} + {link1[1]:.1f} x '
          f'{link2[1]:.0f} = {dot:.3f}')
    cos_angle: float = dot / (np.linalg.norm(link1) * np.linalg.norm(link2))
    print(f'cos(angle) = {dot:.3f} / (3 x 2) = {cos_angle:.3f}')
    print(f'angle = {math.degrees(math.acos(cos_angle)):.1f} degrees  <- that is q2')

    # At right angles the dot product is 0, whatever the lengths.
    print('(3, 0) . (0, 2) =', float(np.array([3.0, 0.0]) @ np.array([0.0, 2.0])),
          ' links at right angles')


def rotation_matrix() -> None:
    """Build the 30 degree rotation and read its columns."""
    heading('4. A rotation matrix')

    r: NDArray[np.float64] = clean(rot2(Q1))
    print('rot2(30 degrees) =\n', r)
    print('first column  ', r[:, 0], ' where the x axis ends up')
    print('second column ', r[:, 1], ' where the y axis ends up')
    print('R @ (3, 0)    ', r @ np.array([3.0, 0.0]), ' the end of link 1')
    print('R @ (0, 1)    ', r @ np.array([0.0, 1.0]))


def order_matters() -> None:
    """Multiply matrices in both orders and compare."""
    heading('5. Multiplying matrices: one move, then another')

    # Two turns in the flat plane: the angles add, and the order does not matter.
    print('rot2(30) @ rot2(60) =\n', clean(rot2(Q1) @ rot2(Q2)))
    print('rot2(90) =\n', clean(rot2(math.radians(90))))
    print('same the other way round:',
          np.allclose(rot2(Q1) @ rot2(Q2), rot2(Q2) @ rot2(Q1)))

    # A turn and a shift: the order does matter. The point (2, 0), the shift
    # (3, 0) and the turn 60 degrees are the frames doc's "order matters" example.
    turn: NDArray[np.float64] = transform2(math.radians(60), 0.0, 0.0)
    shift: NDArray[np.float64] = transform2(0.0, 3.0, 0.0)
    point: NDArray[np.float64] = np.array([2.0, 0.0, 1.0])
    print('shift @ turn @ point ', clean(shift @ turn @ point)[:2], ' turn first, then shift')
    print('turn @ shift @ point ', clean(turn @ shift @ point)[:2], ' shift first, then turn')


def transform_matrix() -> None:
    """Pack a turn and a shift into one 3 x 3 matrix, and chain the arm with them."""
    heading('6. The 3 x 3 transform matrix')

    base_to_link1: NDArray[np.float64] = transform2(Q1, 0.0, 0.0)
    link1_to_link2: NDArray[np.float64] = transform2(Q2, LINK1, 0.0)
    link2_to_gripper: NDArray[np.float64] = transform2(0.0, LINK2, 0.0)
    print('link1 -> link2 =\n', clean(link1_to_link2))

    base_to_gripper: NDArray[np.float64] = clean(base_to_link1 @ link1_to_link2
                                                 @ link2_to_gripper)
    print('base -> gripper = base_to_link1 @ link1_to_link2 @ link2_to_gripper =\n',
          base_to_gripper)
    print('first column  ', base_to_gripper[:2, 0], " the gripper's x axis, on the table")
    print('second column ', base_to_gripper[:2, 1], " the gripper's y axis, on the table")
    print('third column  ', base_to_gripper[:2, 2], ' where the gripper is')

    # A tool tip 1 m in front of the gripper: write it as (1, 0, 1) and multiply.
    tip: NDArray[np.float64] = base_to_gripper @ np.array([1.0, 0.0, 1.0])
    print('tool tip (1, 0) in the gripper frame is', tip[:2], 'on the table')


def three_d() -> None:
    """Turn about each axis in 3D, show order matters, and build one 4 x 4 transform."""
    heading('7. Turning in 3D, and the 4 x 4 transform')

    quarter: float = math.radians(90)
    tool: NDArray[np.float64] = np.array([1.0, 0.0, 0.0])    # a tool pointing along x
    print('tool points along', tool)
    print('rot_z(90) @ tool  ', clean(rot_z(quarter) @ tool), ' swung sideways, like a base')
    print('rot_y(-90) @ tool ', clean(rot_y(-quarter) @ tool),
          ' lifted to point up, like a shoulder')
    print('rot_x(90) @ tool  ', clean(rot_x(quarter) @ tool), ' unchanged: it spins about itself')

    # Two turns in 3D, in both orders. Read right to left: the matrix nearest
    # the point is the move that happens first.
    z_then_x: NDArray[np.float64] = clean(rot_x(quarter) @ rot_z(quarter) @ tool)
    x_then_z: NDArray[np.float64] = clean(rot_z(quarter) @ rot_x(quarter) @ tool)
    print('turn about z, then about x ->', z_then_x)
    print('turn about x, then about z ->', x_then_z)

    # A 4 x 4 transform: a base column 1 m tall, turned 30 degrees about z.
    base: NDArray[np.float64] = np.eye(4)
    base[:3, :3] = rot_z(Q1)
    base[:3, 3] = [0.0, 0.0, 1.0]
    print('4 x 4 transform =\n', clean(base))
    print('a point 3 m along its x axis, (3, 0, 0, 1), lands at',
          clean(base @ np.array([3.0, 0.0, 0.0, 1.0]))[:3])


if __name__ == '__main__':
    vectors()
    length_and_direction()
    dot_product()
    rotation_matrix()
    order_matters()
    transform_matrix()
    three_d()
