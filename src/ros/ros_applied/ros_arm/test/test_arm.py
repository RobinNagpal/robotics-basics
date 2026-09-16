"""Check the arm mover stays within the joint limits, and the distance sensor's sum."""

import math
from pathlib import Path
import xml.etree.ElementTree as ElementTree

import pytest

from ros_arm.arm_mover import arm_pose
from ros_arm.distance_sensor import distance_to_table

URDF: Path = Path(__file__).parents[1] / 'urdf' / 'arm.urdf'


def joint_limits() -> dict[str, tuple[float, float]]:
    """Read each moving joint's lowest and highest position out of the URDF.

    A joint with <mimic> copies another joint, so nothing publishes its
    position, and it is left out.
    """
    limits: dict[str, tuple[float, float]] = {}
    joint: ElementTree.Element
    for joint in ElementTree.parse(URDF).getroot().iter('joint'):
        moves: bool = joint.get('type') in ('revolute', 'prismatic')
        # find() gives None when the tag is not there, so the type says so.
        limit: ElementTree.Element | None = joint.find('limit')
        if moves and joint.find('mimic') is None and limit is not None:
            lower: float = float(limit.get('lower', 'nan'))
            upper: float = float(limit.get('upper', 'nan'))
            limits[joint.get('name', '')] = (lower, upper)
    return limits


def test_the_urdf_has_three_moving_joints_pan_tilt_and_gripper() -> None:
    assert sorted(joint_limits()) == ['gripper', 'pan', 'tilt']


def test_every_position_asked_for_is_within_the_joint_limits() -> None:
    limits = joint_limits()
    for tenth in range(600):
        for name, position in zip(('pan', 'tilt', 'gripper'), arm_pose(tenth / 10)):
            assert limits[name][0] <= position <= limits[name][1]


def test_a_beam_pointing_straight_down_measures_the_height() -> None:
    assert distance_to_table(0.1, 1.0) == pytest.approx(0.1)


def test_a_beam_leaning_60_degrees_travels_twice_as_far() -> None:
    assert distance_to_table(0.1, math.cos(math.radians(60))) == pytest.approx(0.2)


def test_a_beam_pointing_level_never_reaches_the_table() -> None:
    assert distance_to_table(0.1, 0.0) == math.inf
