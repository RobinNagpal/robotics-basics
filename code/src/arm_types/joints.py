"""Joints and degrees of freedom, on a flat arm with three turning joints.

This file prints the numbers quoted in
docs/01_robotics-intro/05_arm-types/01_joints-and-degrees-of-freedom.md:

  1. the chain: where every joint and the gripper are, and which of them move
     when joint 1 turns and when joint 3 turns
  2. why the angles add up along the chain
  3. joint limits: an angle the joint cannot reach is clipped
  4. two joints against three: reaching a cup with the gripper at a chosen angle

The arm is the one from the frames doc, with a third link added:
L1 = 3 m, L2 = 2 m, L3 = 1 m, lying flat on a table.

Run it with:  pixi run python src/arm_types/joints.py
"""

import math

import numpy as np
from numpy.typing import NDArray

LINKS: tuple[float, ...] = (3.0, 2.0, 1.0)


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def chain_points(angles_deg: list[float],
                 links: tuple[float, ...] = LINKS) -> NDArray[np.float64]:
    """Return the base, every joint after it, and the gripper, as rows of (x, y).

    Each joint's angle is measured from the link before it, so the direction of
    a link is the sum of every angle up to and including its own joint.
    """
    points: list[tuple[float, float]] = [(0.0, 0.0)]
    x: float = 0.0
    y: float = 0.0
    heading_rad: float = 0.0
    for angle, length in zip(angles_deg, links):
        heading_rad += math.radians(angle)
        x += length * math.cos(heading_rad)
        y += length * math.sin(heading_rad)
        points.append((x, y))
    return np.array(points)


def show(points: NDArray[np.float64]) -> None:
    """Print the base, each joint and the gripper, one per line."""
    names: list[str] = ['base', 'joint 2', 'joint 3', 'gripper'][:len(points)]
    for name, (x, y) in zip(names, points):
        print(f'  {name:8s} ({x:6.3f}, {y:6.3f})')


def moved(before: NDArray[np.float64], after: NDArray[np.float64]) -> None:
    """Print how far each point travelled between two poses."""
    names: list[str] = ['base', 'joint 2', 'joint 3', 'gripper']
    for name, a, b in zip(names, before, after):
        distance: float = float(np.linalg.norm(b - a))
        print(f'  {name:8s} moved {distance:5.3f} m')


def clip(angle: float, low: float, high: float) -> float:
    """Return the angle a joint with limits actually goes to when asked for one."""
    return min(max(angle, low), high)


def two_joint_solutions(x: float, y: float, l1: float,
                        l2: float) -> list[tuple[float, float]]:
    """Both ways a two-joint arm can put its tip on (x, y), in degrees."""
    cos_q2: float = (x * x + y * y - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    answers: list[tuple[float, float]] = []
    for sign in (1.0, -1.0):
        q2: float = sign * math.acos(cos_q2)
        q1: float = math.atan2(y, x) - math.atan2(l2 * math.sin(q2), l1 + l2 * math.cos(q2))
        answers.append((math.degrees(q1), math.degrees(q2)))
    return answers


def main() -> None:
    """Print each numbered section in turn."""
    heading('1. the chain: q = (30, 60, -60) degrees')
    start: NDArray[np.float64] = chain_points([30.0, 60.0, -60.0])
    show(start)

    heading('1a. turn joint 1 by +20 degrees: q = (50, 60, -60)')
    j1: NDArray[np.float64] = chain_points([50.0, 60.0, -60.0])
    show(j1)
    moved(start, j1)

    heading('1b. turn joint 3 by +20 degrees instead: q = (30, 60, -40)')
    j3: NDArray[np.float64] = chain_points([30.0, 60.0, -40.0])
    show(j3)
    moved(start, j3)

    heading('2. the angles add up along the chain')
    q: list[float] = [30.0, 60.0, -60.0]
    total: float = 0.0
    for i, angle in enumerate(q, start=1):
        total += angle
        print(f'  link {i}: its joint says {angle:+5.0f}, '
              f'it points at {total:+5.0f} from the table')

    heading('3. joint limits: joint 2 can only reach -150 to +150 degrees')
    for asked in (60.0, 170.0, -200.0):
        print(f'  asked for {asked:+6.0f}, the joint goes to {clip(asked, -150.0, 150.0):+6.0f}')

    heading('4. reach the cup handle at (3, 2), gripper pointing straight down (-90)')
    # Two joints, links 3 m and 2 m: the tip itself must be on the handle.
    for q1, q2 in two_joint_solutions(3.0, 2.0, 3.0, 2.0):
        tip = chain_points([q1, q2], (3.0, 2.0))[-1]
        print(f'  2 joints: q = ({q1:7.2f}, {q2:7.2f})  tip ({tip[0]:.3f}, {tip[1]:.3f})'
              f'  gripper points at {q1 + q2:7.2f}')
    # Three joints: put the wrist 1 m above the handle, then aim the last link down.
    wrist_x: float = 3.0
    wrist_y: float = 2.0 + 1.0
    for q1, q2 in two_joint_solutions(wrist_x, wrist_y, 3.0, 2.0):
        q3: float = -90.0 - q1 - q2
        tip = chain_points([q1, q2, q3])[-1]
        print(f'  3 joints: q = ({q1:7.2f}, {q2:7.2f}, {q3:7.2f})  tip ({tip[0]:.3f}, '
              f'{tip[1]:.3f})  gripper points at {q1 + q2 + q3:7.2f}')


if __name__ == '__main__':
    main()
