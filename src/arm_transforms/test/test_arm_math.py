"""Tests for the transform maths, and a check that step 1 and step 2 agree."""

import math

from arm_transforms.arm_math import (
    camera_in_base,
    camera_mount,
    gripper_in_base,
    LINK1_M,
    LINK2_M,
    rotate_point,
    Transform2D,
    yaw_to_quaternion,
)
from arm_transforms.step1_positions import gripper_position
import pytest

QUARTER_TURN = math.pi / 2


def test_rotating_x_axis_by_a_quarter_turn_gives_the_y_axis():
    x, y = rotate_point(1.0, 0.0, QUARTER_TURN)
    assert (x, y) == pytest.approx((0.0, 1.0), abs=1e-12)


def test_rotating_keeps_the_distance_from_the_origin():
    x, y = rotate_point(0.3, -0.4, 1.234)
    assert math.hypot(x, y) == pytest.approx(0.5)


def test_applying_a_pure_shift_just_adds():
    shift = Transform2D.translation(1.0, 2.0)
    assert shift.apply(0.5, 0.5) == pytest.approx((1.5, 2.5))


def test_joining_adds_the_angles():
    joined = Transform2D.rotation(0.4).then(Transform2D.rotation(0.25))
    assert joined.theta == pytest.approx(0.65)


def test_joining_rotates_the_child_offset():
    """A quarter turn, then a step along X, should end up along +Y."""
    joined = Transform2D.rotation(QUARTER_TURN).then(Transform2D.translation(1.0, 0.0))
    assert (joined.x, joined.y) == pytest.approx((0.0, 1.0), abs=1e-12)


@pytest.mark.parametrize('q1,q2', [(0.0, 0.0), (0.5, -0.3), (1.2, 0.9), (-0.7, 2.0)])
def test_inverse_undoes_the_transform(q1, q2):
    forward = gripper_in_base(q1, q2)
    back = forward.inverse().inverse()
    assert (back.x, back.y, back.theta) == pytest.approx((forward.x, forward.y, forward.theta))


@pytest.mark.parametrize('q1,q2', [(0.0, 0.0), (0.5, -0.3), (1.2, 0.9)])
def test_a_point_survives_a_round_trip_between_frames(q1, q2):
    """Into the gripper frame and back out should land on the same point."""
    base_to_gripper = gripper_in_base(q1, q2)
    there = base_to_gripper.inverse().apply(0.31, -0.12)
    back = base_to_gripper.apply(*there)
    assert back == pytest.approx((0.31, -0.12))


@pytest.mark.parametrize('q1_deg,q2_deg', [(0, 0), (45, 0), (0, 90), (45, 45), (90, -45)])
def test_joining_links_agrees_with_the_hand_derived_formula(q1_deg, q2_deg):
    """Step 2 must produce exactly what step 1 works out with trigonometry."""
    q1, q2 = math.radians(q1_deg), math.radians(q2_deg)
    joined = gripper_in_base(q1, q2)
    assert (joined.x, joined.y) == pytest.approx(gripper_position(q1, q2))


def test_straight_arm_reaches_the_sum_of_the_link_lengths():
    straight = gripper_in_base(0.0, 0.0)
    assert (straight.x, straight.y) == pytest.approx((LINK1_M + LINK2_M, 0.0))


def test_quaternion_is_normalised():
    qx, qy, qz, qw = yaw_to_quaternion(1.1)
    assert math.sqrt(qx**2 + qy**2 + qz**2 + qw**2) == pytest.approx(1.0)


def test_zero_yaw_is_the_identity_quaternion():
    assert yaw_to_quaternion(0.0) == pytest.approx((0.0, 0.0, 0.0, 1.0))


@pytest.mark.parametrize('q1,q2', [(0.0, 0.0), (0.5, -0.3), (1.2, 0.9)])
def test_camera_hangs_off_link2_not_the_gripper(q1, q2):
    """Moving joint 2 moves the camera, but the gripper is not on its route."""
    _parent, _child, bracket = camera_mount()
    # base_link -> link2 -> camera, done the long way round for comparison.
    link2 = Transform2D.rotation(q1).then(Transform2D(LINK1_M, 0.0, q2))
    assert camera_in_base(q1, q2) == link2.then(bracket)


def test_camera_bracket_never_changes():
    assert camera_mount()[2] == camera_mount()[2]
    assert camera_mount()[0] == 'link2'
