"""Step 1: position on its own, worked out with plain trigonometry.

Run it:  make arm.learn   (or: ros2 run arm_transforms arm_step1_positions)

THE IDEA
--------
A position is just two numbers in 2D, or three in 3D. But two numbers on their
own mean nothing. "The gripper is at (0.7, 0.4)" is only useful once you say
*measured from where*. That starting point is the **frame**.

Here everything is measured from ``base_link``, the frame bolted to the table
the arm stands on.

THE ARM
-------
Two joints, two links, flat on a table::

        shoulder (q1)        elbow (q2)
    base_link o───────────────o───────────────o gripper
                  L1 = 0.5m        L2 = 0.4m

WORKING IT OUT BY HAND
----------------------
The upper arm leaves the shoulder at angle ``q1``. A line of length ``L1`` at
angle ``q1`` ends at::

    elbow_x = L1 * cos(q1)
    elbow_y = L1 * sin(q1)

The forearm starts at the elbow. It is turned by ``q2`` *relative to the upper
arm*, so measured from the table it points at ``q1 + q2``. Angles add up along
the chain — that is the one thing to notice in this file::

    gripper_x = elbow_x + L2 * cos(q1 + q2)
    gripper_y = elbow_y + L2 * sin(q1 + q2)

This works, and for two joints it is honestly fine.

WHY WE DO NOT STOP HERE
-----------------------
Those formulas were derived by hand, for this arm only. Add a third joint and
you derive them again. Move to 3D and each step needs three angles. Ask a
different question — "where is the camera compared to the gripper?" — and you
derive a fresh set backwards.

Step 2 gets the same numbers without deriving anything.
"""

import math

from arm_transforms.arm_math import LINK1_M, LINK2_M

#: A few joint angles to try, in degrees, as (q1, q2).
POSES_DEG = [(0, 0), (45, 0), (0, 90), (45, 45), (90, -45)]


def elbow_position(q1: float) -> tuple[float, float]:
    """Where the elbow is, measured from base_link."""
    return LINK1_M * math.cos(q1), LINK1_M * math.sin(q1)


def gripper_position(q1: float, q2: float) -> tuple[float, float]:
    """Where the gripper is, measured from base_link.

    Note ``q1 + q2``: the forearm's angle on the table is its own joint angle
    plus everything the joints before it contributed.
    """
    elbow_x, elbow_y = elbow_position(q1)
    return (
        elbow_x + LINK2_M * math.cos(q1 + q2),
        elbow_y + LINK2_M * math.sin(q1 + q2),
    )


def main() -> None:
    """Print the elbow and gripper positions for a few joint angles."""
    print(__doc__.split('THE IDEA')[0].strip())
    print(f'\nLink lengths: L1 = {LINK1_M} m, L2 = {LINK2_M} m')
    print('\nAll positions are measured from base_link.\n')
    print(f"{'q1':>6} {'q2':>6}  {'elbow (x, y)':>20}  {'gripper (x, y)':>20}")
    print('-' * 58)

    for q1_deg, q2_deg in POSES_DEG:
        q1, q2 = math.radians(q1_deg), math.radians(q2_deg)
        ex, ey = elbow_position(q1)
        gx, gy = gripper_position(q1, q2)
        print(
            f'{q1_deg:>5}° {q2_deg:>5}°  '
            f'({ex:>7.3f}, {ey:>7.3f})  ({gx:>7.3f}, {gy:>7.3f})'
        )

    print(
        '\nCheck the first row by hand: both joints straight, so the arm is a '
        f'straight line along X.\nThe gripper should sit at L1 + L2 = '
        f'{LINK1_M + LINK2_M:.3f} m. It does.'
    )
    print('\nNext: step 2 gets these same numbers without any hand-derived formula.')


if __name__ == '__main__':
    main()
