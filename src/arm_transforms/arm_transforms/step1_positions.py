"""Step 1: position on its own, worked out with plain trigonometry.

Run it:  make arm.learn   (or: ros2 run arm_transforms arm_step1_positions)

THE IDEA
--------
A position is just two numbers in 2D, or three in 3D. But two numbers on their
own mean nothing. "The gripper is at (0.7, 0.4)" is only useful once you say
*measured from where*. That starting point is the **frame**.

Here everything is measured from ``base_link``, the frame fixed to the table the
arm stands on.

START WITH THE SIMPLEST ARM
---------------------------
One joint, one link, a gripper bolted to the end::

    base_link o───────────────o gripper
              q1    L1

The link leaves the base at angle ``q1`` and is ``L1`` long. A point ``L1`` away
at angle ``q1`` sits at::

    gripper_x = L1 * cos(q1)
    gripper_y = L1 * sin(q1)

That is all ``cos`` and ``sin`` do here. They turn "this far away, at this
angle" into "this far across, this far up".

NOW ADD A SECOND JOINT
----------------------
Two joints, two links, the gripper still bolted to the end::

              q1              q2
    base_link o───────────────o───────────────o gripper
                    L1              L2

The end of link 1 is where the simple arm finished. Link 2 starts there.

The catch is the angle. ``q2`` is measured against link 1, not against the
table. Link 1 is already turned by ``q1``. So measured from the table, link 2
points at ``q1 + q2``. Angles add up along the chain — that is the one thing to
notice in this file::

    gripper_x = joint2_x + L2 * cos(q1 + q2)
    gripper_y = joint2_y + L2 * sin(q1 + q2)

WHY WE DO NOT STOP HERE
-----------------------
Those formulas were worked out by hand, for this arm, to answer this one
question. Add a third joint and you work them out again. Move to 3D and each
step needs three angles. Ask a different question — "where is the table, from
the camera's point of view?" — and you work out a fresh set backwards.

Step 2 gets the same numbers without working out anything.
"""

import math

from arm_transforms.arm_math import LINK1_M, LINK2_M

#: Angles to try on the one-joint arm, in degrees.
ONE_JOINT_DEG = [0, 30, 45, 60, 90]

#: A few joint angles to try on the two-joint arm, in degrees, as (q1, q2).
POSES_DEG = [(0, 0), (45, 0), (0, 90), (45, 45), (90, -45)]


def one_joint_gripper(q1: float) -> tuple[float, float]:
    """Where the gripper is on the simplest arm: one joint, one link."""
    return LINK1_M * math.cos(q1), LINK1_M * math.sin(q1)


def joint2_position(q1: float) -> tuple[float, float]:
    """Where joint 2 is, measured from base_link.

    This is the end of link 1, which is exactly where the one-joint arm's
    gripper was. The second joint is bolted on at that same spot.
    """
    return one_joint_gripper(q1)


def gripper_position(q1: float, q2: float) -> tuple[float, float]:
    """Where the gripper is on the two-joint arm, measured from base_link.

    Note ``q1 + q2``: link 2's angle on the table is its own joint angle plus
    everything the joints before it contributed.
    """
    x, y = joint2_position(q1)
    return (
        x + LINK2_M * math.cos(q1 + q2),
        y + LINK2_M * math.sin(q1 + q2),
    )


def main() -> None:
    """Print gripper positions for the one-joint arm, then the two-joint one."""
    print(__doc__.split('THE IDEA')[0].strip())
    print(f'\nLink lengths: L1 = {LINK1_M} m, L2 = {LINK2_M} m')
    print('All positions are measured from base_link.')

    print('\n--- simplest arm: one joint, one link ---\n')
    print(f"{'q1':>6}  {'gripper (x, y)':>20}")
    print('-' * 30)
    for q1_deg in ONE_JOINT_DEG:
        x, y = one_joint_gripper(math.radians(q1_deg))
        print(f'{q1_deg:>5}°  ({x:>7.3f}, {y:>7.3f})')

    print('\n--- two joints, two links ---\n')
    print(f"{'q1':>6} {'q2':>6}  {'joint 2 (x, y)':>20}  {'gripper (x, y)':>20}")
    print('-' * 58)
    for q1_deg, q2_deg in POSES_DEG:
        q1, q2 = math.radians(q1_deg), math.radians(q2_deg)
        jx, jy = joint2_position(q1)
        gx, gy = gripper_position(q1, q2)
        print(
            f'{q1_deg:>5}° {q2_deg:>5}°  '
            f'({jx:>7.3f}, {jy:>7.3f})  ({gx:>7.3f}, {gy:>7.3f})'
        )

    print(
        '\nCheck the first row by hand: both joints straight, so the arm is a '
        f'straight line along X.\nThe gripper should sit at L1 + L2 = '
        f'{LINK1_M + LINK2_M:.3f} m. It does.'
    )
    print('\nNext: step 2 gets these same numbers without any hand-worked formula.')


if __name__ == '__main__':
    main()
