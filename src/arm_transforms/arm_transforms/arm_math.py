"""The maths behind frames and transforms, written out longhand.

Everything here is plain Python. No ROS, no matrix library. The point is that a
transform is a small, ordinary thing: a rotation and a shift, kept together.

The arm used throughout this area is flat (2D) and has two joints:

    base_link ──rotate q1──▶ upper_arm ──move L1, rotate q2──▶ forearm ──move L2──▶ gripper

Real arms are 3D and have more joints, but the rules do not change. A 3D
transform is the same idea with three angles instead of one.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

#: Length of the upper arm, in metres.
LINK1_M = 0.5
#: Length of the forearm, in metres.
LINK2_M = 0.4


def rotate_point(x: float, y: float, theta: float) -> tuple[float, float]:
    """Turn the point ``(x, y)`` around the origin by ``theta`` radians.

    This is the one formula the rest of the file is built on::

        x' = x * cos(theta) - y * sin(theta)
        y' = x * sin(theta) + y * cos(theta)

    Sanity check it by hand: rotating ``(1, 0)`` by a quarter turn gives
    ``(0, 1)``, because ``cos(90°) = 0`` and ``sin(90°) = 1``.
    """
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    return x * cos_t - y * sin_t, x * sin_t + y * cos_t


def yaw_to_quaternion(yaw: float) -> tuple[float, float, float, float]:
    """Turn a flat rotation into the four numbers ROS stores, ``(x, y, z, w)``.

    ROS keeps rotations as a **quaternion** — four numbers — instead of angles,
    because three angles hit awkward cases in 3D where two axes line up and one
    degree of freedom quietly disappears. Four numbers have no such case.

    Nothing here spins about the X or Y axis, so those two stay at zero and the
    turn lands entirely in ``z`` and ``w``. You do not need the full theory to
    use this: one angle in, four numbers out.
    """
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


@dataclass(frozen=True)
class Transform2D:
    """Where a child frame sits inside its parent frame.

    Three numbers say it completely:

    :param x: how far along the parent's X axis the child's origin is
    :param y: how far along the parent's Y axis
    :param theta: how far the child is turned, in radians

    Read an instance as a sentence: "the child is at (x, y), turned by theta,
    measured in the parent".
    """

    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

    @staticmethod
    def rotation(theta: float) -> Transform2D:
        """Make a turn on the spot, with no shift. This is what a joint does."""
        return Transform2D(0.0, 0.0, theta)

    @staticmethod
    def translation(x: float, y: float) -> Transform2D:
        """Make a shift with no turn. This is what a rigid link does."""
        return Transform2D(x, y, 0.0)

    def apply(self, x: float, y: float) -> tuple[float, float]:
        """Take a point given in the child frame, and say where it is in the parent.

        Rotate first, then shift. The order matters: shifting first and then
        rotating would swing the shift around too, and give a different answer.
        """
        rx, ry = rotate_point(x, y, self.theta)
        return rx + self.x, ry + self.y

    def then(self, child: Transform2D) -> Transform2D:
        """Join two transforms into one.

        If ``self`` is A→B and ``child`` is B→C, the result is A→C. This is the
        whole trick: you describe each link once, on its own, and joining them
        gives you any pair you want.
        """
        x, y = self.apply(child.x, child.y)
        return Transform2D(x, y, self.theta + child.theta)

    def inverse(self) -> Transform2D:
        """Flip the direction: if ``self`` is A→B, this is B→A.

        Undo the turn, then undo the shift — in that order, which is why the
        shift gets rotated backwards on the way out.
        """
        x, y = rotate_point(-self.x, -self.y, -self.theta)
        return Transform2D(x, y, -self.theta)


def arm_transforms(q1: float, q2: float) -> list[tuple[str, str, Transform2D]]:
    """Describe the arm as a list of ``(parent, child, transform)`` links.

    Each entry knows only about its own two frames. Nothing here knows where
    the gripper ends up — that falls out of joining them together.
    """
    return [
        # The shoulder joint turns, but does not move.
        ('base_link', 'upper_arm', Transform2D.rotation(q1)),
        # Travel the length of the upper arm, then the elbow turns.
        ('upper_arm', 'forearm', Transform2D(LINK1_M, 0.0, q2)),
        # The forearm is rigid: a shift with no turn.
        ('forearm', 'gripper', Transform2D.translation(LINK2_M, 0.0)),
    ]


def gripper_in_base(q1: float, q2: float) -> Transform2D:
    """Join every link of the arm into one base_link→gripper transform."""
    result = Transform2D()
    for _parent, _child, link in arm_transforms(q1, q2):
        result = result.then(link)
    return result
