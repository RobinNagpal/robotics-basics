"""Linear algebra: vectors, rotations, transforms, the camera matrix, and fitting.

Where a robot's parts are, where its camera looks, and how to move a point from
one frame to another are all done with small matrices: a 3 x 3 rotation, a
4 x 4 transform, the camera's 3 x 3 matrix k. NumPy does these with the @
operator and the functions in np.linalg. This file covers:

  1. vectors: dot, cross, norm, and a unit vector
  2. rotations: a rotation matrix, turning points, and why its inverse is R.T
  3. 4 x 4 transforms: joining them, applying one to many points, inverting
  4. the camera matrix k: from a 3D point to a pixel, and back
  5. solving and fitting: solve, lstsq, polyfit, and a plane with svd
  6. the arm, moved a little: the Jacobian and pinv
  7. which way an object lies: covariance and eigh

The numbers are the ones the arm and camera docs use, so the answers can be
checked against them: the two-link arm at 30 and 60 degrees reaches
(2.598, 3.5), and the camera sees the point (0.0644, -0.0411, 0.340) at pixel
(212.5, 86.5).

Run it with:  pixi run python src/numpy/linear_algebra.py
"""

import math

import numpy as np
from numpy.typing import NDArray

# The two-link arm from the arm area: link lengths in metres.
LINK1: float = 3.0
LINK2: float = 2.0

# The camera from the camera area: 320 x 240 pixels, seeing 60 degrees across.
FX: float = 277.1
FY: float = 277.1
CX: float = 160.0
CY: float = 120.0


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def rotation_z(angle: float) -> NDArray[np.float64]:
    """Make the 3 x 3 matrix that turns points by this many radians around the z axis."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[c, -s, 0.0],
                     [s, c, 0.0],
                     [0.0, 0.0, 1.0]])


def transform(rotation: NDArray[np.float64],
              translation: NDArray[np.float64]) -> NDArray[np.float64]:
    """Put a 3 x 3 rotation and a shift of 3 numbers into one 4 x 4 transform."""
    matrix: NDArray[np.float64] = np.eye(4)
    matrix[:3, :3] = rotation         # top left: the turn
    matrix[:3, 3] = translation       # right column: the shift
    return matrix


def vectors() -> None:
    """Measure and combine directions."""
    heading('1. Vectors: dot, cross, norm')

    a: NDArray[np.float64] = np.array([1.0, 0.0, 0.0])
    b: NDArray[np.float64] = np.array([1.0, 1.0, 0.0])
    # The length of a vector: np.linalg.norm.
    print('np.linalg.norm(b)          ', np.linalg.norm(b))
    # Divided by its length, a vector becomes a unit vector: length 1, the
    # same direction. Directions such as a camera's viewing ray are kept this way.
    print('b / np.linalg.norm(b)      ', b / np.linalg.norm(b))
    # The dot product, a @ b or np.dot(a, b), is |a| |b| cos(angle between
    # them), so it gives the angle between two directions.
    cos_angle: float = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    print('a @ b', a @ b, ' angle between them', round(math.degrees(math.acos(cos_angle)), 1),
          'degrees')
    # The cross product is a vector at right angles to both. From two edges of
    # a table it gives the table's upward direction, its "normal".
    edge1: NDArray[np.float64] = np.array([0.6, 0.0, 0.0])
    edge2: NDArray[np.float64] = np.array([0.0, 0.4, 0.0])
    print('np.cross(edge1, edge2)     ', np.cross(edge1, edge2), ' points straight up')


def rotations() -> None:
    """Turn points with a rotation matrix."""
    heading('2. Rotations')

    # A rotation matrix turns a point when you multiply: R @ point. The @
    # operator is matrix multiplication; * would multiply value by value instead.
    r: NDArray[np.float64] = rotation_z(math.radians(90))
    point: NDArray[np.float64] = np.array([1.0, 0.0, 0.0])
    print('rotation_z(90 degrees):\n', r)
    print('R @ [1, 0, 0] ->', r @ point, '  x turned into y')

    # Many points at once: with one point per row, points @ R.T turns them all.
    points: NDArray[np.float64] = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    print('points @ R.T ->\n', points @ r.T)

    # Turning back is the transpose, R.T, because the columns of a rotation are
    # at right angles and of length 1. R.T @ R is the identity, and the
    # determinant is 1 (a rotation neither stretches nor mirrors).
    print('np.allclose(R.T @ R, np.eye(3))', np.allclose(r.T @ r, np.eye(3)),
          ' np.linalg.det(R)', round(float(np.linalg.det(r)), 6))


def transforms() -> None:
    """Join, apply and invert 4 x 4 transforms."""
    heading('3. 4 x 4 transforms: the arm, and the camera')

    # The two-link arm at q1 = 30 and q2 = 60 degrees, one transform per step
    # along it, as in the arm area: joint 1 turns, then link 1 is travelled
    # and joint 2 turns, then link 2 is travelled to the gripper.
    q1: float = math.radians(30)
    q2: float = math.radians(60)
    base_to_link1: NDArray[np.float64] = transform(rotation_z(q1), np.zeros(3))
    link1_to_link2: NDArray[np.float64] = transform(rotation_z(q2), np.array([LINK1, 0.0, 0.0]))
    link2_to_gripper: NDArray[np.float64] = transform(np.eye(3), np.array([LINK2, 0.0, 0.0]))
    # Joining transforms is multiplying them, in order from the base out.
    base_to_gripper: NDArray[np.float64] = base_to_link1 @ link1_to_link2 @ link2_to_gripper
    print('base_to_gripper:\n', base_to_gripper)
    print('the gripper is at', base_to_gripper[:3, 3], ' (the arm area says 2.598, 3.5)')

    # Applying a transform to many points: add a 1 to each point, multiply,
    # and drop the 1 again. Two points 1 m and 2 m in front of the gripper:
    in_gripper: NDArray[np.float64] = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    homogeneous: NDArray[np.float64] = np.hstack([in_gripper, np.ones((2, 1))])
    in_base: NDArray[np.float64] = (base_to_gripper @ homogeneous.T).T[:, :3]
    print('in front of the gripper, in the base frame:\n', in_base)
    # The same without the 1s: turn with the top-left 3 x 3, then shift.
    same: NDArray[np.float64] = in_gripper @ base_to_gripper[:3, :3].T + base_to_gripper[:3, 3]
    print('rotation then shift gives the same:', np.allclose(in_base, same))

    # Inverting a transform turns "gripper in base" into "base in gripper".
    # np.linalg.inv works, and so does the quicker rule for a rotation R and a
    # shift t: the inverse turns by R.T and shifts by -R.T @ t.
    r: NDArray[np.float64] = base_to_gripper[:3, :3]
    t: NDArray[np.float64] = base_to_gripper[:3, 3]
    quick: NDArray[np.float64] = transform(r.T, -r.T @ t)
    print('np.linalg.inv agrees with (R.T, -R.T @ t):',
          np.allclose(np.linalg.inv(base_to_gripper), quick))

    # The camera area's camera, 0.40 m above the table and looking straight
    # down: its right is the room's x, its down is the room's -y, and its
    # forward is the room's -z. Those three are the rotation's columns.
    camera_to_world: NDArray[np.float64] = transform(
        np.array([[1.0, 0.0, 0.0],
                  [0.0, -1.0, 0.0],
                  [0.0, 0.0, -1.0]]),
        np.array([0.0, 0.0, 0.40]))
    seen: NDArray[np.float64] = np.array([0.0644, -0.0411, 0.340, 1.0])
    print('a point the camera sees, in the room:', (camera_to_world @ seen)[:3],
          ' (6 cm up: the top of the box)')


def camera_matrix() -> None:
    """Project a 3D point to a pixel with the camera matrix k, and back."""
    heading('4. The camera matrix k')

    # k is the camera's lens as a 3 x 3 matrix. ROS sends it in every
    # CameraInfo message, as nine numbers row by row.
    k: NDArray[np.float64] = np.array([[FX, 0.0, CX],
                                       [0.0, FY, CY],
                                       [0.0, 0.0, 1.0]])
    # k @ point gives (fx x + cx z, fy y + cy z, z). Dividing by the last
    # number, z, gives the pixel (u, v).
    point: NDArray[np.float64] = np.array([0.0644, -0.0411, 0.340])
    projected: NDArray[np.float64] = k @ point
    pixel: NDArray[np.float64] = projected[:2] / projected[2]
    print('k @ point ->', projected, ' / z -> pixel', pixel.round(1))

    # Going back needs the depth, because a pixel is only a direction. The
    # inverse of k turns (u, v, 1) into that direction, one metre ahead, and
    # the depth reading stretches it to the point.
    direction: NDArray[np.float64] = np.linalg.inv(k) @ np.array([pixel[0], pixel[1], 1.0])
    print('np.linalg.inv(k) @ (u, v, 1) * depth ->', (direction * 0.340).round(4))

    # Every pixel of a picture at once: one (u, v, 1) row per pixel, and
    # (k^-1 @ rows.T).T gives every direction.
    pixels: NDArray[np.float64] = np.array([[CX, CY, 1.0], [0.0, 0.0, 1.0]])
    print('the middle pixel and the top-left corner look along:\n',
          (np.linalg.inv(k) @ pixels.T).T.round(4))


def solving_and_fitting() -> None:
    """Solve equations exactly, and fit lines and planes to noisy readings."""
    heading('5. Solving and fitting')

    # np.linalg.solve(A, b) finds x with A @ x = b, for as many equations as
    # unknowns. Where do the lines y = 2x and x + y = 3 meet? Written as
    # A @ (x, y) = b, row by row: 2x - y = 0 and x + y = 3.
    a: NDArray[np.float64] = np.array([[2.0, -1.0], [1.0, 1.0]])
    b: NDArray[np.float64] = np.array([0.0, 3.0])
    print('np.linalg.solve ->', np.linalg.solve(a, b))

    # With more readings than unknowns, and some noise, no line goes through
    # them all. Least squares finds the best one. A distance sensor's raw
    # readings against the true distances: find the scale and offset that
    # correct it. np.polyfit fits a line (degree 1) and gives the slope first.
    true_m: NDArray[np.float64] = np.array([0.10, 0.20, 0.30, 0.40, 0.50])
    raw_m: NDArray[np.float64] = np.array([0.125, 0.228, 0.331, 0.429, 0.532])
    slope: float
    offset: float
    slope, offset = (float(v) for v in np.polyfit(raw_m, true_m, 1))
    print(f'np.polyfit: true = {slope:.4f} * raw {offset:+.4f},',
          ' so a raw 0.30 means', round(slope * 0.30 + offset, 4), 'm')

    # np.linalg.lstsq does the same for any number of unknowns. Here, the
    # table as the plane z = a x + b y + c, from five points with a little noise.
    table: NDArray[np.float64] = np.array([
        [0.0, 0.0, 0.001], [0.3, 0.0, -0.001], [0.0, 0.3, 0.000],
        [0.3, 0.3, 0.002], [0.15, 0.15, 0.000]])
    columns: NDArray[np.float64] = np.column_stack([table[:, 0], table[:, 1], np.ones(5)])
    abc: NDArray[np.float64] = np.linalg.lstsq(columns, table[:, 2], rcond=None)[0]
    # (Adding 0.0 after rounding turns a printed -0. into 0.)
    print('np.linalg.lstsq: plane z = a x + b y + c, with a, b, c =', abc.round(4) + 0.0)

    # The same plane with np.linalg.svd, which works whichever way the plane
    # faces: take the middle away, and the last row of vt is the direction the
    # points spread least in, which is the plane's normal.
    centred: NDArray[np.float64] = table - table.mean(axis=0)
    vt: NDArray[np.float64] = np.linalg.svd(centred)[2]
    normal: NDArray[np.float64] = vt[-1] * np.sign(vt[-1][2])     # made to point up
    print('np.linalg.svd: the table normal is', normal.round(4) + 0.0)


def jacobian_step() -> None:
    """Work out how to turn the arm's joints to move its gripper a little."""
    heading('6. Moving the arm a little: the Jacobian and pinv')

    q: NDArray[np.float64] = np.radians([30.0, 60.0])

    def gripper(q: NDArray[np.float64]) -> NDArray[np.float64]:
        """Say where the gripper is, as (x, y), for joint angles q, as in the arm area."""
        return np.array([LINK1 * math.cos(q[0]) + LINK2 * math.cos(q[0] + q[1]),
                         LINK1 * math.sin(q[0]) + LINK2 * math.sin(q[0] + q[1])])

    # The Jacobian says how far the gripper moves for a small turn of each
    # joint: column 1 is (dx, dy) per radian of joint 1, column 2 for joint 2.
    j: NDArray[np.float64] = np.array([
        [-LINK1 * math.sin(q[0]) - LINK2 * math.sin(q[0] + q[1]), -LINK2 * math.sin(q[0] + q[1])],
        [LINK1 * math.cos(q[0]) + LINK2 * math.cos(q[0] + q[1]), LINK2 * math.cos(q[0] + q[1])],
    ])
    print('Jacobian at (30, 60) degrees:\n', j)

    # To move the gripper 1 cm in x, the joints must turn by J^-1 @ (0.01, 0).
    # np.linalg.pinv, the pseudo-inverse, is used instead of inv, because it
    # still gives a sensible answer when the arm is stretched straight and J
    # has no inverse, and when an arm has more joints than there are directions.
    step: NDArray[np.float64] = np.linalg.pinv(j) @ np.array([0.01, 0.0])
    print('joint turns for 1 cm in x:', np.degrees(step).round(4) + 0.0, 'degrees')
    # The Jacobian is exact only for tiny moves, so a real step of 1 cm also
    # moves the gripper a little in y: here, 0.02 mm.
    moved: NDArray[np.float64] = gripper(q + step) - gripper(q)
    print(f'the gripper moves x {moved[0]:+.5f} m, y {moved[1]:+.5f} m')


def which_way_it_lies() -> None:
    """Find the long direction of an object from its points."""
    heading('7. Which way an object lies: covariance and eigh')

    # Points on the top of a bar lying at 45 degrees on the table: 10 cm long,
    # 2 cm wide. A gripper should close across it, not along it.
    rng: np.random.Generator = np.random.default_rng(seed=1)
    along: NDArray[np.float64] = rng.uniform(-0.05, 0.05, 200)
    across: NDArray[np.float64] = rng.uniform(-0.01, 0.01, 200)
    turn: NDArray[np.float64] = rotation_z(math.radians(45))[:2, :2]
    xy: NDArray[np.float64] = np.column_stack([along, across]) @ turn.T

    # np.cov gives how the x and y values spread together, as a 2 x 2 matrix.
    # np.linalg.eigh finds its eigenvectors, the directions of most and least
    # spread, with the matching eigenvalues in increasing order. (eigh is for
    # symmetric matrices, which a covariance always is; eig is the general one.)
    spread: NDArray[np.float64] = np.cov(xy.T)
    values: NDArray[np.float64]
    directions: NDArray[np.float64]
    values, directions = np.linalg.eigh(spread)
    longest: NDArray[np.float64] = directions[:, -1]
    angle: float = math.degrees(math.atan2(longest[1], longest[0])) % 180
    # The square root of an eigenvalue is the spread, as a distance.
    across_cm: float
    along_cm: float
    across_cm, along_cm = (float(math.sqrt(v) * 100) for v in values)
    print('np.cov(xy.T) has shape', spread.shape)
    print(f'np.linalg.eigh: spread {along_cm:.1f} cm along the bar and {across_cm:.1f} cm across,'
          f' and the bar lies at {angle:.1f} degrees')


def main() -> None:
    """Run every section in order."""
    np.set_printoptions(precision=4, suppress=True)
    vectors()
    rotations()
    transforms()
    camera_matrix()
    solving_and_fitting()
    jacobian_step()
    which_way_it_lies()


if __name__ == '__main__':
    main()
