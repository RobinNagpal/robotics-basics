"""Launch the camera publisher alongside RViz2 with a preloaded config."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Build the launch description: the camera publisher plus an optional RViz2."""
    pkg_share = FindPackageShare('camera_basics')
    default_rviz_config = PathJoinSubstitution([pkg_share, 'rviz', 'camera_demo.rviz'])

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
            'hfov_deg',
            default_value='60.0',
            description='Horizontal field of view. Try 90 for wide, 30 for a zoom.',
        ),
        DeclareLaunchArgument(
            'width_px',
            default_value='160',
            description='Picture width. Every pixel is a ray, so this costs CPU.',
        ),
        DeclareLaunchArgument(
            'height_px',
            default_value='120',
            description='Picture height.',
        ),
    ]

    camera_publisher = Node(
        package='camera_basics',
        executable='camera_publisher',
        name='camera_publisher',
        output='screen',
        # A LaunchConfiguration is a string; without an explicit value_type the
        # node rejects it as a type mismatch against its declared parameter.
        parameters=[
            {
                'hfov_deg': ParameterValue(LaunchConfiguration('hfov_deg'), value_type=float),
                'width_px': ParameterValue(LaunchConfiguration('width_px'), value_type=int),
                'height_px': ParameterValue(LaunchConfiguration('height_px'), value_type=int),
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

    return LaunchDescription([*launch_args, camera_publisher, rviz])
