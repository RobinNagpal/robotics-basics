"""Forward kinematics: joint angles in, gripper position and angle out.

This file prints every number quoted in the forward kinematics doc, in the
order the doc uses them:

  1. the two-joint arm, joined one link at a time with 3 x 3 matrices
  2. the same arm described twice: in joint space and in task space
  3. the three-joint arm, whose gripper angle can now be chosen
  4. the workspace: every place the gripper can reach
  5. what joint limits take away from the workspace

Run it with:  pixi run python src/kinematics/forward.py
"""

import math

import numpy as np
from numpy.typing import NDArray
from planar_arm import chain, forward, THREE_LINKS, TWO_LINKS


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the doc."""
    print(f'\n--- {text} ---')


def show(matrix: NDArray[np.float64]) -> str:
    """Print a 3 x 3 matrix with three decimals, and no -0.000."""
    return np.array2string(np.round(matrix, 3) + 0.0, precision=3, suppress_small=True)


def two_joints() -> None:
    """Join the two-joint arm, one matrix at a time."""
    heading('1. The two-joint arm, joined with matrices')
    joints: list[float] = [math.radians(30.0), math.radians(60.0)]
    frames: list[NDArray[np.float64]] = chain(joints, TWO_LINKS)
    names: list[str] = ['base', 'joint 2 (the elbow)', 'gripper']
    for name, frame in zip(names, frames):
        print(f'{name}:')
        print(show(frame))
    x, y, angle = forward(joints, TWO_LINKS)
    print(f'gripper at ({x:.3f}, {y:.3f}), pointing at {math.degrees(angle):.1f} degrees')


def joint_space_and_task_space() -> None:
    """Describe the same three poses as joint angles and as gripper positions."""
    heading('2. Joint space and task space')
    poses: dict[str, tuple[float, float]] = {'A': (30.0, 60.0),
                                             'B': (0.0, 90.0),
                                             'C': (90.0, -45.0)}
    print('pose   q1      q2        gripper x   gripper y   gripper angle')
    for name, (q1, q2) in poses.items():
        x, y, angle = forward([math.radians(q1), math.radians(q2)], TWO_LINKS)
        print(f'{name}    {q1:5.1f}   {q2:6.1f}      {x:7.3f}     {y:7.3f}     '
              f'{math.degrees(angle):6.1f}')


def three_joints() -> None:
    """Add a third joint, and the gripper's angle becomes free to choose."""
    heading('3. The three-joint arm')
    for q in [(30.0, 60.0, -60.0), (30.0, 60.0, 0.0), (30.0, 60.0, 60.0)]:
        x, y, angle = forward([math.radians(a) for a in q], THREE_LINKS)
        print(f'q = {q}: gripper at ({x:.3f}, {y:.3f}), '
              f'pointing at {math.degrees(angle):.1f} degrees')


def workspace() -> None:
    """Try every pair of joint angles, one degree apart, and see where the gripper lands."""
    heading('4. The workspace, with no joint limits')
    angles: NDArray[np.float64] = np.radians(np.arange(-180.0, 180.0, 1.0))
    q1, q2 = np.meshgrid(angles, angles)
    x: NDArray[np.float64] = TWO_LINKS[0] * np.cos(q1) + TWO_LINKS[1] * np.cos(q1 + q2)
    y: NDArray[np.float64] = TWO_LINKS[0] * np.sin(q1) + TWO_LINKS[1] * np.sin(q1 + q2)
    reach: NDArray[np.float64] = np.hypot(x, y)
    print(f'{q1.size} poses tried')
    print(f'closest to the base:  {reach.min():.3f} m')
    print(f'furthest from base:   {reach.max():.3f} m')


def with_limits() -> None:
    """Repeat the sweep, with joint limits like a real arm has."""
    heading('5. The workspace, with joint limits')
    q1_deg: NDArray[np.float64] = np.arange(-90.0, 90.0 + 1e-9, 1.0)
    q2_deg: NDArray[np.float64] = np.arange(-150.0, 150.0 + 1e-9, 1.0)
    q1, q2 = np.meshgrid(np.radians(q1_deg), np.radians(q2_deg))
    x: NDArray[np.float64] = TWO_LINKS[0] * np.cos(q1) + TWO_LINKS[1] * np.cos(q1 + q2)
    y: NDArray[np.float64] = TWO_LINKS[0] * np.sin(q1) + TWO_LINKS[1] * np.sin(q1 + q2)
    reach: NDArray[np.float64] = np.hypot(x, y)
    print('joint 1 from -90 to +90 degrees, joint 2 from -150 to +150 degrees')
    print(f'closest to the base:  {reach.min():.3f} m')
    print(f'furthest from base:   {reach.max():.3f} m')
    print(f'most negative x:      {x.min():.3f} m')


def main() -> None:
    """Print every section, in the order the doc uses them."""
    two_joints()
    joint_space_and_task_space()
    three_joints()
    workspace()
    with_limits()


if __name__ == '__main__':
    main()
