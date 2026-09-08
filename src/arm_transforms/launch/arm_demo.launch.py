"""Launch the arm broadcaster with RViz, and optionally the TF watcher."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Build the launch description: the broadcaster, RViz, and the watcher."""
    pkg_share = FindPackageShare('arm_transforms')
    default_rviz_config = PathJoinSubstitution([pkg_share, 'rviz', 'arm_demo.rviz'])

    launch_args = [
        DeclareLaunchArgument(
            'use_rviz', default_value='true', description='Start RViz alongside the node.'),
        DeclareLaunchArgument(
            'rviz_config', default_value=default_rviz_config,
            description='Absolute path to an .rviz config file.'),
        DeclareLaunchArgument(
            'watch', default_value='false',
            description='Also run step 5, which asks TF where the gripper is.'),
    ]

    broadcaster = Node(
        package='arm_transforms',
        executable='arm_step4_broadcast',
        name='arm_broadcaster',
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    watcher = Node(
        package='arm_transforms',
        executable='arm_step5_lookup',
        name='gripper_watcher',
        output='screen',
        condition=IfCondition(LaunchConfiguration('watch')),
    )

    return LaunchDescription([*launch_args, broadcaster, rviz, watcher])
