"""A flat arm with any number of joints, as 3 x 3 matrices.

This is the arm from the frames and transforms area, written the way real
robot code writes it: each joint is a turn, each link is a shift, and both are
3 x 3 matrices. Joining two of them is one matrix multiply, with the @ operator.

The two files next to this one use it:

  forward.py   joint angles in, gripper position and angle out
  inverse.py   gripper position in, joint angles out

A 3 x 3 matrix for a flat transform looks like this::

    [[cos(t), -sin(t), x],
     [sin(t),  cos(t), y],
     [0,       0,      1]]

The top-left 2 x 2 block is the turn, and the right-hand column is the shift.
The bottom row is always 0, 0, 1. It is there so that a turn and a shift can be
joined by one multiply.
"""

import math

import numpy as np
from numpy.typing import NDArray

#: The two-joint arm from the frames area: link lengths in metres.
TWO_LINKS: tuple[float, ...] = (3.0, 2.0)
#: The three-joint arm from section 8 of the frames area.
THREE_LINKS: tuple[float, ...] = (3.0, 2.0, 1.0)


def turn(angle: float) -> NDArray[np.float64]:
    """Make the matrix for a joint: a turn by this many radians, and no shift."""
    c: float = math.cos(angle)
    s: float = math.sin(angle)
    return np.array([[c, -s, 0.0],
                     [s, c, 0.0],
                     [0.0, 0.0, 1.0]])


def shift(length: float) -> NDArray[np.float64]:
    """Make the matrix for a rigid link: a shift along its own x axis, and no turn."""
    return np.array([[1.0, 0.0, length],
                     [0.0, 1.0, 0.0],
                     [0.0, 0.0, 1.0]])


def chain(joints: list[float], links: tuple[float, ...]) -> list[NDArray[np.float64]]:
    """Join the arm from the base outwards, and keep the answer after every link.

    The list that comes back starts with the base, then holds where each joint
    after the first sits, and ends with the gripper. Each entry is a 3 x 3
    transform measured from the base.
    """
    answer: NDArray[np.float64] = np.eye(3)
    frames: list[NDArray[np.float64]] = [answer]
    for angle, length in zip(joints, links):
        answer = answer @ turn(angle) @ shift(length)
        frames.append(answer)
    return frames


def forward(joints: list[float], links: tuple[float, ...]) -> tuple[float, float, float]:
    """Forward kinematics: joint angles in radians, out comes (x, y, angle) of the gripper."""
    gripper: NDArray[np.float64] = chain(joints, links)[-1]
    x: float = float(gripper[0, 2])
    y: float = float(gripper[1, 2])
    angle: float = math.atan2(gripper[1, 0], gripper[0, 0])
    return x, y, angle


def points(joints: list[float], links: tuple[float, ...]) -> list[tuple[float, float]]:
    """Where the base, each joint and the gripper are, for drawing the arm."""
    return [(float(f[0, 2]), float(f[1, 2])) for f in chain(joints, links)]


def two_joint_ik(x: float, y: float, l1: float, l2: float) -> list[tuple[float, float]]:
    """Inverse kinematics for two joints, worked out with the law of cosines.

    Returns every pair (q1, q2), in radians, that puts the gripper on (x, y).
    That is two pairs, one pair, or none.
    """
    d_squared: float = x * x + y * y
    cos_q2: float = (d_squared - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
    if cos_q2 > 1.0 + 1e-12 or cos_q2 < -1.0 - 1e-12:
        return []                                  # too far away, or too close in
    cos_q2 = max(-1.0, min(1.0, cos_q2))
    answers: list[tuple[float, float]] = []
    for sign in (1.0, -1.0):
        q2: float = sign * math.acos(cos_q2)
        q1: float = math.atan2(y, x) - math.atan2(l2 * math.sin(q2), l1 + l2 * math.cos(q2))
        # At full stretch or fully folded, +q2 and -q2 are the same pose: keep one.
        if all(abs(math.sin(q2) - math.sin(a[1])) > 1e-9 for a in answers):
            answers.append((q1, q2))
    return answers


def three_joint_ik(x: float, y: float, gripper_angle: float,
                   links: tuple[float, ...]) -> list[tuple[float, float, float]]:
    """Inverse kinematics for three joints, once the gripper's angle is chosen.

    Link 3 has to point along the gripper angle, so the wrist (joint 3) must be
    one link-3 length back from the target. That leaves a two-joint problem for
    the wrist, and joint 3 makes up whatever angle is still missing.
    """
    l1, l2, l3 = links
    wrist_x: float = x - l3 * math.cos(gripper_angle)
    wrist_y: float = y - l3 * math.sin(gripper_angle)
    return [(q1, q2, gripper_angle - q1 - q2)
            for q1, q2 in two_joint_ik(wrist_x, wrist_y, l1, l2)]


def jacobian(joints: list[float], links: tuple[float, ...],
             nudge: float = 1e-6) -> NDArray[np.float64]:
    """How far the gripper moves, in x and y, for a small turn of each joint.

    Found the plain way: turn one joint a tiny amount, see how far the gripper
    went, and divide by the amount. Column i is joint i's answer.
    """
    x0, y0, _ = forward(joints, links)
    columns: list[list[float]] = []
    for i in range(len(joints)):
        moved: list[float] = list(joints)
        moved[i] += nudge
        x1, y1, _ = forward(moved, links)
        columns.append([(x1 - x0) / nudge, (y1 - y0) / nudge])
    return np.array(columns).T


def numerical_ik(x: float, y: float, guess: list[float], links: tuple[float, ...],
                 tolerance: float = 1e-6,
                 max_steps: int = 100) -> list[tuple[list[float], float]]:
    """Inverse kinematics by repeated small corrections.

    Start from a guess. Work out how far the gripper is from the target. Use the
    Jacobian to turn that miss into joint turns, and apply them. Repeat until the
    miss is smaller than the tolerance. Returns every (joints, miss) along the way.
    """
    joints: list[float] = list(guess)
    history: list[tuple[list[float], float]] = []
    for _ in range(max_steps):
        gx, gy, _ = forward(joints, links)
        miss: NDArray[np.float64] = np.array([x - gx, y - gy])
        distance: float = float(np.linalg.norm(miss))
        history.append((list(joints), distance))
        if distance < tolerance:
            break
        step: NDArray[np.float64] = np.linalg.pinv(jacobian(joints, links)) @ miss
        # A correction bigger than about 30 degrees at once tends to overshoot,
        # because the Jacobian is only right for small moves. So cap it.
        largest: float = float(np.max(np.abs(step)))
        if largest > 0.5:
            step = step * (0.5 / largest)
        joints = [j + float(s) for j, s in zip(joints, step)]
    return history
