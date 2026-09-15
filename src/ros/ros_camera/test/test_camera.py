"""Check the picture the camera publisher draws, and that the subscriber finds the ball in it."""

from image_geometry import PinholeCameraModel
import pytest

from ros_camera.camera_publisher import ball_position, camera_info, draw_picture, HEIGHT, WIDTH
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


def test_k_puts_the_lens_numbers_where_programs_look_for_them():
    k = camera_info().k
    assert (k[0], k[4], k[2], k[5]) == (277.1, 277.1, 160.0, 120.0)     # fx, fy, cx, cy


def test_the_standard_camera_library_reads_the_same_lens():
    """image_geometry reads its lens numbers from p, so p has to match k."""
    camera = PinholeCameraModel()
    camera.from_camera_info(camera_info())
    assert (camera.fx(), camera.fy(), camera.cx(), camera.cy()) == (277.1, 277.1, 160.0, 120.0)
    # The point from the camera docs, 0.34 m in front, lands on pixel (212.5, 86.5).
    assert camera.project_3d_to_pixel((0.0644, -0.0411, 0.340)) == pytest.approx(
        (212.5, 86.5), abs=0.1)
