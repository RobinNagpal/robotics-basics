"""Launching: starting several nodes together, with their settings.

A robot is never one program. Starting six of them by hand, in six terminals,
each with the right settings, would be slow and easy to get wrong, so ROS has
launch files. One command starts everything, and Ctrl-C stops everything.

This one starts the publisher, the subscriber and the settings node, and shows
the four things launch files are used for:

  arguments   values you pass on the command line, as name:=value
  parameters  settings handed to a node as it starts
  remapping   renaming a node's topics without touching its code
  conditions  starting a node only if asked for

Run it with:

  ros2 launch ros_basics basics.launch.py
  ros2 launch ros_basics basics.launch.py robot_name:=picker with_settings:=false
  ros2 launch ros_basics basics.launch.py --show-args      what it takes

A launch file is a Python file with a function called generate_launch_description
that returns a list of things to start. It does not start anything itself, and
most of the values in it are "substitutions": placeholders that get their real
value only when the launch runs, which is why paths and settings are built out
of LaunchConfiguration and the like instead of plain strings.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Build the list of things to start."""
    arguments: list[DeclareLaunchArgument] = [
        DeclareLaunchArgument('robot_name', default_value='demo',
                              description='The name the settings node should hold.'),
        DeclareLaunchArgument('with_settings', default_value='true',
                              description='Also start the settings node.'),
    ]

    # One Node entry starts one program: which package, which executable from
    # its setup.py, and what to call the node once it is running.
    publisher: Node = Node(
        package='ros_basics',
        executable='basics_publisher',
        name='countdown_publisher',
        output='screen',        # send its log lines to this terminal
    )

    # remappings renames topics as the node starts. The publisher above still
    # thinks it publishes /countdown; this subscriber is told that what it calls
    # /countdown is really /countdown too, which changes nothing here but is
    # exactly how the same node is pointed at a different camera or a different
    # arm without editing it.
    subscriber: Node = Node(
        package='ros_basics',
        executable='basics_subscriber',
        name='countdown_subscriber',
        output='screen',
        remappings=[('/countdown', '/countdown')],
    )

    # parameters hands the node its settings as it starts, which is where a real
    # robot's numbers come from. LaunchConfiguration('robot_name') is the value
    # given on the command line, or the default above.
    settings: Node = Node(
        package='ros_basics',
        executable='basics_parameters',
        name='settings',
        output='screen',
        parameters=[{'robot_name': LaunchConfiguration('robot_name'), 'joints': 6}],
        condition=IfCondition(LaunchConfiguration('with_settings')),
    )

    return LaunchDescription([*arguments, publisher, subscriber, settings])
