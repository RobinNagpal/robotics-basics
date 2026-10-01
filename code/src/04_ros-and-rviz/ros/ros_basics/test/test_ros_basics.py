"""Tests for the basics package: the parts that can be checked without a robot.

Nodes need a running ROS to test properly, which is what the launch tests of a
real project do. These check the pieces that are ordinary Python: the launch
file builds, the settings node's check refuses an impossible speed, and every
program named in setup.py really exists.
"""

from collections.abc import Iterator
import importlib
import importlib.util
import pathlib

from launch import LaunchDescription
import pytest
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.parameter import Parameter

from ros_basics.parameters import Settings, SPEED_LIMIT
from ros_basics.publisher import PERIOD

PACKAGE: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
SETUP: pathlib.Path = PACKAGE / 'setup.py'
LAUNCH: pathlib.Path = PACKAGE / 'launch' / 'basics.launch.py'


@pytest.fixture(scope='module')
def ros() -> Iterator[None]:
    """Start ROS once for the tests that make a node, and stop it afterwards."""
    rclpy.init()
    yield
    rclpy.shutdown()


def test_the_launch_file_builds() -> None:
    """generate_launch_description must return a description, with its arguments.

    A launch file is not part of the Python package, so it is loaded from its
    path rather than imported by name.
    """
    spec = importlib.util.spec_from_file_location('basics_launch', LAUNCH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    description: LaunchDescription = module.generate_launch_description()
    assert isinstance(description, LaunchDescription)
    names: list[str] = [str(action.name) for action in description.entities
                        if hasattr(action, 'name')]
    assert 'robot_name' in names
    assert 'with_settings' in names


def test_the_publisher_sends_twice_a_second() -> None:
    assert PERIOD == 0.5


def test_a_speed_inside_the_limit_is_allowed(ros: None) -> None:
    node: Settings = Settings()
    result: SetParametersResult = node.check([Parameter('speed_mps', value=SPEED_LIMIT)])
    node.destroy_node()
    assert result.successful


def test_a_speed_over_the_limit_is_refused(ros: None) -> None:
    node: Settings = Settings()
    result: SetParametersResult = node.check([Parameter('speed_mps', value=SPEED_LIMIT + 0.1)])
    node.destroy_node()
    assert not result.successful
    assert 'speed_mps' in result.reason


def test_every_program_in_setup_py_exists() -> None:
    """Each console script names a module and a function: both must be real."""
    lines: list[str] = [line.strip().strip("',")
                        for line in SETUP.read_text().splitlines()
                        if line.strip().startswith("'basics_")]
    assert len(lines) == 9
    for line in lines:
        target: str = line.split(' = ')[1]
        module_name: str
        function_name: str
        module_name, function_name = target.split(':')
        module = importlib.import_module(module_name)
        assert callable(getattr(module, function_name))
