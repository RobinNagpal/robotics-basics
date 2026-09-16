"""Check the step from a pixel to the angles that point the arm at it."""

import math

import pytest

from ros_camera_arm.follower import pixel_to_angles

LENS: tuple[float, float, float, float] = (277.1, 277.1, 160.0, 120.0)     # fx, fy, cx, cy


def test_the_middle_of_the_picture_is_straight_ahead() -> None:
    assert pixel_to_angles(160.0, 120.0, *LENS) == pytest.approx((0.0, 0.0))


def test_right_of_the_middle_turns_right_and_above_it_tilts_up() -> None:
    pan, tilt = pixel_to_angles(200.0, 100.0, *LENS)
    assert pan < 0 and tilt > 0


def test_one_focal_length_to_the_side_is_45_degrees() -> None:
    pan, tilt = pixel_to_angles(160.0 + 277.1, 120.0 - 277.1, *LENS)
    assert math.degrees(pan) == pytest.approx(-45.0)
    assert math.degrees(tilt) == pytest.approx(45.0)
