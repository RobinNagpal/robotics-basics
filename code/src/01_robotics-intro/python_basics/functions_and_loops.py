"""Functions and loops: turning joint angles into a position, once and many times.

A function packs a calculation up under a name, so it is written once and used
everywhere. A loop repeats a step for every joint, or every pose. This file
builds the position of a two-joint arm's gripper with both:

  1. a function: where is the end of one link?
  2. returning two numbers at once, as a tuple
  3. a for loop over the joints, adding up the angles
  4. if: is a target close enough to reach?
  5. a loop over many poses, printing a small table

The arm is the one used in the frames and transforms doc: link 1 is 3 m long,
link 2 is 2 m long.

Run it with:  pixi run python src/python_basics/functions_and_loops.py
"""

import math

LINK_LENGTHS_M: list[float] = [3.0, 2.0]


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def link_end(length_m: float, angle_deg: float) -> tuple[float, float]:
    """Return how far across and how far up the end of one link is from its start."""
    angle_rad: float = math.radians(angle_deg)
    return length_m * math.cos(angle_rad), length_m * math.sin(angle_rad)


def gripper_position(q_deg: list[float]) -> tuple[float, float]:
    """Walk out along the arm, one link at a time, and return where the gripper is.

    Each joint angle is measured from the link before it, so the direction of a
    link is the sum of every angle up to and including its own joint.
    """
    x: float = 0.0
    y: float = 0.0
    direction_deg: float = 0.0
    for length_m, angle_deg in zip(LINK_LENGTHS_M, q_deg):
        direction_deg += angle_deg
        dx, dy = link_end(length_m, direction_deg)
        x += dx
        y += dy
    return x, y


def can_reach(x: float, y: float) -> bool:
    """Say whether a point is no further away than both links laid end to end."""
    distance: float = math.hypot(x, y)
    return distance <= sum(LINK_LENGTHS_M)


def one_function() -> None:
    """Call link_end at two angles."""
    heading('1. A function: the end of one link')
    across, up = link_end(3.0, 30.0)
    print(f'link_end(3.0, 30.0) -> ({across:.3f}, {up:.3f})')
    across, up = link_end(3.0, 60.0)
    print(f'link_end(3.0, 60.0) -> ({across:.3f}, {up:.3f})')


def tuples() -> None:
    """Take the tuple link_end returns apart."""
    heading('2. Returning two numbers: a tuple')
    result: tuple[float, float] = link_end(3.0, 30.0)
    print('the whole tuple:', result)
    x, y = result                       # unpack it into two names
    print(f'unpacked:        x = {x:.3f}, y = {y:.3f}')


def the_loop() -> None:
    """Add up the angles joint by joint, then find the gripper."""
    heading('3. A for loop over the joints')
    q: list[float] = [30.0, 60.0]
    direction_deg: float = 0.0
    for i, angle_deg in enumerate(q):
        direction_deg += angle_deg
        print(f'joint {i + 1}: turns {angle_deg:5.1f} deg, link {i + 1} points at '
              f'{direction_deg:5.1f} deg from the table')
    x, y = gripper_position(q)
    print(f'gripper_position({q}) -> ({x:.3f}, {y:.3f})')


def checks() -> None:
    """Test one target that can be reached and one that cannot."""
    heading('4. if: can the arm reach it?')
    for target in [(4.0, 2.0), (4.0, 4.0)]:
        x, y = target
        if can_reach(x, y):
            print(f'{target}: {math.hypot(x, y):.3f} m away, reachable')
        else:
            print(f'{target}: {math.hypot(x, y):.3f} m away, too far '
                  f'(the arm is {sum(LINK_LENGTHS_M)} m long)')


def many_poses() -> None:
    """Print the gripper position for six poses."""
    heading('5. A loop over many poses')
    print('   q1    q2  ->  gripper x   gripper y')
    for q1 in [0.0, 30.0, 60.0]:
        for q2 in [0.0, 60.0]:
            x, y = gripper_position([q1, q2])
            print(f'{q1:5.0f} {q2:5.0f}  ->  {x:9.3f}   {y:9.3f}')


if __name__ == '__main__':
    one_function()
    tuples()
    the_loop()
    checks()
    many_poses()
