"""Step 2: the same answer, built out of frames instead of worked out by hand.

Run it:  make arm.learn   (or: ros2 run arm_transforms arm_step2_frames)

THE IDEA
--------
In step 1 we wrote one formula for the whole arm. Here we describe each link on
its own, and let the joining produce the answer.

A **transform** is a rotation plus a shift, kept together. It says where a child
frame sits inside its parent::

    base_link ──turn by q1──▶ link1        joint 1 turns, does not move
    link1     ──move L1, turn by q2──▶ link2
    link2     ──move L2──▶ gripper         a rigid link, no turn

Each line knows nothing about the others. Nothing here mentions ``q1 + q2``.

TWO RULES
---------
Applying a transform to a point: **rotate first, then shift.**

    x' = x*cos(t) - y*sin(t) + tx
    y' = x*sin(t) + y*cos(t) + ty

Joining two transforms A→B and B→C into A→C: put the second one's shift through
the first one's turn, and add the angles.

    joined.shift = the first applied to the second's shift
    joined.angle = first.angle + second.angle

That second rule is where ``q1 + q2`` comes from. We never wrote it down. It
appears on its own once the links are joined, and it will keep appearing for the
third and fourth joint without any more work.

WHY THIS IS BETTER
------------------
Each link is described once, locally, in terms a person can check. Joining is
mechanical. Step 3 shows the two things this buys you that step 1 cannot do
easily: going backwards, and carrying points between frames.
"""

import math

from arm_transforms.arm_math import arm_chain, Transform2D
from arm_transforms.step1_positions import gripper_position, POSES_DEG


def gripper_by_joining(q1: float, q2: float) -> Transform2D:
    """Join the arm's links one at a time, printing each step along the way."""
    result = Transform2D()  # base_link to itself: no shift, no turn
    for parent, child, link in arm_chain(q1, q2):
        result = result.then(link)
        print(
            f'    after joining {parent:>9} -> {child:<9} '
            f'base_link->{child:<9} = (x={result.x:>7.3f}, y={result.y:>7.3f}, '
            f'angle={math.degrees(result.theta):>7.1f}°)'
        )
    return result


def main() -> None:
    """Join the links for each pose, and check the result against step 1."""
    print(__doc__.split('THE IDEA')[0].strip())
    print('\nThe arm as a list of links, each one described on its own:\n')
    for parent, child, link in arm_chain(0.0, 0.0):
        print(f'    {parent:>9} -> {child:<9} shift ({link.x}, {link.y}), turn by its joint')

    print('\nNow join them, one link at a time:\n')
    worst_error = 0.0
    for q1_deg, q2_deg in POSES_DEG:
        q1, q2 = math.radians(q1_deg), math.radians(q2_deg)
        print(f'  q1 = {q1_deg}°, q2 = {q2_deg}°')
        joined = gripper_by_joining(q1, q2)

        # The same numbers step 1 worked out with its hand-written formula.
        hand_x, hand_y = gripper_position(q1, q2)
        error = math.hypot(joined.x - hand_x, joined.y - hand_y)
        worst_error = max(worst_error, error)
        print(f'    step 1 said ({hand_x:.3f}, {hand_y:.3f}) — difference: {error:.2e}\n')

    print(f'Biggest difference across every pose: {worst_error:.2e} metres.')
    print('The two agree. Same maths, assembled differently.')
    print('\nNext: step 3 goes backwards, and carries points between frames.')


if __name__ == '__main__':
    main()
