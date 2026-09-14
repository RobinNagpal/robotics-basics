"""Check that the arm mover only asks for angles the arm's joints can reach."""

from pathlib import Path
import xml.etree.ElementTree as ElementTree

from ros_arm.arm_mover import arm_pose

URDF = Path(__file__).parents[1] / 'urdf' / 'arm.urdf'


def joint_limits():
    """Read each moving joint's lowest and highest angle out of the URDF."""
    joints = ElementTree.parse(URDF).getroot().iter('joint')
    limits = {}
    for joint in joints:
        if joint.get('type') == 'revolute':
            limit = joint.find('limit')
            limits[joint.get('name')] = (float(limit.get('lower')), float(limit.get('upper')))
    return limits


def test_the_urdf_has_two_moving_joints_called_pan_and_tilt():
    assert sorted(joint_limits()) == ['pan', 'tilt']


def test_every_angle_asked_for_is_within_the_joint_limits():
    limits = joint_limits()
    for tenth in range(600):
        pan, tilt = arm_pose(tenth / 10)
        assert limits['pan'][0] <= pan <= limits['pan'][1]
        assert limits['tilt'][0] <= tilt <= limits['tilt'][1]
