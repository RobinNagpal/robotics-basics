"""Unit tests for the pure-geometry helpers in :mod:`rviz_basics.marker_publisher`.

These deliberately avoid rclpy so they run fast and need no ROS graph.
"""

import math

import pytest

from rviz_basics.marker_publisher import circular_orbit, yaw_to_quaternion

RADIUS = 2.0
PERIOD = 6.0


def test_orbit_starts_on_positive_x_axis():
    x, y, _ = circular_orbit(0.0, RADIUS, PERIOD)
    assert x == pytest.approx(RADIUS)
    assert y == pytest.approx(0.0)


def test_orbit_reaches_positive_y_axis_at_quarter_period():
    x, y, _ = circular_orbit(PERIOD / 4.0, RADIUS, PERIOD)
    assert x == pytest.approx(0.0, abs=1e-9)
    assert y == pytest.approx(RADIUS)


def test_orbit_is_periodic():
    start = circular_orbit(0.0, RADIUS, PERIOD)
    full_lap = circular_orbit(PERIOD, RADIUS, PERIOD)
    assert full_lap[0] == pytest.approx(start[0])
    assert full_lap[1] == pytest.approx(start[1])


@pytest.mark.parametrize('elapsed', [0.0, 1.3, 4.7, 11.0])
def test_orbit_stays_on_the_circle(elapsed):
    x, y, _ = circular_orbit(elapsed, RADIUS, PERIOD)
    assert math.hypot(x, y) == pytest.approx(RADIUS)


@pytest.mark.parametrize('elapsed', [0.0, 1.3, 4.7])
def test_yaw_is_tangent_to_the_orbit(elapsed):
    """Heading must be perpendicular to the radius — i.e. along the path."""
    x, y, yaw = circular_orbit(elapsed, RADIUS, PERIOD)
    radial = (x / RADIUS, y / RADIUS)
    heading = (math.cos(yaw), math.sin(yaw))
    assert radial[0] * heading[0] + radial[1] * heading[1] == pytest.approx(0.0, abs=1e-9)


def test_quaternion_is_normalised():
    qx, qy, qz, qw = yaw_to_quaternion(1.234)
    assert math.sqrt(qx**2 + qy**2 + qz**2 + qw**2) == pytest.approx(1.0)


def test_zero_yaw_is_identity_quaternion():
    assert yaw_to_quaternion(0.0) == pytest.approx((0.0, 0.0, 0.0, 1.0))
