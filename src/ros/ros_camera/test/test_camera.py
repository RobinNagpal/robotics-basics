"""Check the picture the camera publisher draws, and that the subscriber finds the ball in it."""

import pytest

from ros_camera.camera_publisher import ball_position, draw_picture, HEIGHT, WIDTH
from ros_camera.camera_subscriber import find_ball


def test_the_picture_is_320_by_240_with_three_colours_per_pixel():
    assert draw_picture(160, 120).shape == (HEIGHT, WIDTH, 3) == (240, 320, 3)


def test_the_subscriber_finds_the_ball_where_it_was_drawn():
    u, v = find_ball(draw_picture(100.5, 80.5))
    assert (u, v) == pytest.approx((100.5, 80.5), abs=0.1)


def test_a_picture_without_the_ball_has_no_ball():
    assert find_ball(draw_picture(-100, -100)) is None


def test_the_ball_stays_inside_the_picture():
    for tenth in range(600):
        u, v = ball_position(tenth / 10)
        assert 15 <= u <= WIDTH - 15 and 15 <= v <= HEIGHT - 15
