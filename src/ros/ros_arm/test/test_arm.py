"""Check the arm mover stays within the joint limits, and the distance sensor's sum."""

import math
from pathlib import Path
import xml.etree.ElementTree as ElementTree

import pytest

from ros_arm.arm_mover import arm_pose
from ros_arm.distance_sensor import distance_to_table

URDF = Path(__file__).parents[1] / 'urdf' / 'arm.urdf'


def joint_limits():
    """Read each moving joint's lowest and highest position out of the URDF.

    A joint with <mimic> copies another joint, so nothing publishes its
    position, and it is left out.
    """
    limits = {}
    for joint in ElementTree.parse(URDF).getroot().iter('joint'):
        if joint.get('type') in ('revolute', 'prismatic') and joint.find('mimic') is None:
            limit = joint.find('limit')
            limits[joint.get('name')] = (float(limit.get('lower')), float(limit.get('upper')))
    return limits


def test_the_urdf_has_three_moving_joints_pan_tilt_and_gripper():
    assert sorted(joint_limits()) == ['gripper', 'pan', 'tilt']


def test_every_position_asked_for_is_within_the_joint_limits():
    limits = joint_limits()
    for tenth in range(600):
        for name, position in zip(('pan', 'tilt', 'gripper'), arm_pose(tenth / 10)):
            assert limits[name][0] <= position <= limits[name][1]


def test_a_beam_pointing_straight_down_measures_the_height():
    assert distance_to_table(0.1, 1.0) == pytest.approx(0.1)


def test_a_beam_leaning_60_degrees_travels_twice_as_far():
    assert distance_to_table(0.1, math.cos(math.radians(60))) == pytest.approx(0.2)


def test_a_beam_pointing_level_never_reaches_the_table():
    assert distance_to_table(0.1, 0.0) == math.inf
