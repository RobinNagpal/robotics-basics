"""Step 3: going backwards, and carrying points between frames.

Run it:  make arm.learn   (or: ros2 run arm_transforms arm_step3_chain)

THE IDEA
--------
Step 2 joined links forwards, base to gripper. Two more moves make the idea
genuinely useful, and both are awkward with step 1's hand-derived formulas.

GOING BACKWARDS
---------------
Every transform can be flipped. If you know where the gripper is inside
base_link, you also know where base_link is *seen from the gripper*. You do not
measure anything new; you undo the turn and undo the shift::

    inverse.angle  = -angle
    inverse.offset = the offset, rotated backwards, then negated

This is how a robot answers "where is the table, from the gripper's point of
view?" when all it was told is where each joint is turned to.

CARRYING A POINT BETWEEN FRAMES
-------------------------------
A gripper holding a tool cares about the tip, not the gripper itself.
The tip is easy to describe *in the gripper frame*: 1 m straight ahead, and it
stays there no matter how the arm moves.

To find the tip on the table, apply base_link→gripper to that fixed point. The
description stays still; the transform does the work. This is the same idea as
the ball in the RViz area: you do not move the point, you move the frame.

WHY THIS MATTERS
----------------
These three moves — join, flip, apply — cover almost everything you do with
positions on a robot. TF is a service that does exactly them, on a whole robot,
with timestamps. Step 4 hands this arm over to it.
"""

import math

from arm_transforms.arm_math import gripper_in_base, Transform2D

#: A tool tip, 1 m ahead of the gripper. Fixed in the gripper frame.
TOOL_TIP_IN_GRIPPER = (1.0, 0.0)


def describe(name: str, transform: Transform2D) -> str:
    """Format a transform for printing."""
    return (
        f'{name:<28} x={transform.x:>7.3f}  y={transform.y:>7.3f}  '
        f'angle={math.degrees(transform.theta):>7.1f}°'
    )


def main() -> None:
    """Show joining, flipping and applying, on one arm pose."""
    print(__doc__.split('THE IDEA')[0].strip())

    # Right angles, so every number printed below is whole.
    q1, q2 = math.radians(180.0), math.radians(-90.0)
    print('\nArm pose: q1 = 180°, q2 = -90°\n')

    # --- forwards ------------------------------------------------------
    base_to_gripper = gripper_in_base(q1, q2)
    print('Joining every link, base to gripper:')
    print('   ', describe('base_link -> gripper', base_to_gripper))

    # --- backwards -----------------------------------------------------
    gripper_to_base = base_to_gripper.inverse()
    print('\nThe same transform, flipped round:')
    print('   ', describe('gripper -> base_link', gripper_to_base))
    print(
        '\n    Read that as: from where the gripper is sitting, the table\n'
        '    corner is back over there. No new measurement was needed.'
    )

    # Flipping twice must land back where we started. Worth checking, because a
    # sign error in an inverse is easy to write and hard to spot by eye.
    round_trip = gripper_to_base.inverse()
    drift = math.hypot(round_trip.x - base_to_gripper.x, round_trip.y - base_to_gripper.y)
    print(f'\n    Flipping it twice returns the original, to within {drift:.2e} m.')

    # --- carrying a point ----------------------------------------------
    tip_x, tip_y = base_to_gripper.apply(*TOOL_TIP_IN_GRIPPER)
    print('\nA tool tip, 1 m ahead of the gripper:')
    print(f'    in the gripper frame: ({TOOL_TIP_IN_GRIPPER[0]:.3f}, '
          f'{TOOL_TIP_IN_GRIPPER[1]:.3f})   <- never changes')
    print(f'    on the table:         ({tip_x:.3f}, {tip_y:.3f})   <- changes as the arm moves')

    print('\nMove the arm and run again: the first line stays put, the second moves.')
    print('That is the whole point of frames.')
    print('\nNext: step 4 publishes these frames to TF, so RViz can draw the arm.')


if __name__ == '__main__':
    main()
