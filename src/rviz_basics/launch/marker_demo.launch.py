"""Launch the marker publisher alongside RViz2 with a preloaded config."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Build the launch description: the marker publisher plus an optional RViz2."""
    pkg_share = FindPackageShare('rviz_basics')
    default_rviz_config = PathJoinSubstitution([pkg_share, 'rviz', 'marker_demo.rviz'])

    launch_args = [
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Start RViz2 alongside the node.',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=default_rviz_config,
            description='Absolute path to an .rviz config file.',
        ),
        DeclareLaunchArgument(
            'orbit_period_s',
            default_value='6.0',
            description='Seconds per revolution of the marker frame.',
        ),
    ]

    marker_publisher = Node(
        package='rviz_basics',
        executable='marker_publisher',
        name='marker_publisher',
        output='screen',
        # A LaunchConfiguration is a string; without an explicit value_type the
        # node rejects it as a type mismatch against its double parameter.
        parameters=[
            {
                'orbit_period_s': ParameterValue(
                    LaunchConfiguration('orbit_period_s'), value_type=float
                )
            }
        ],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([*launch_args, marker_publisher, rviz])
