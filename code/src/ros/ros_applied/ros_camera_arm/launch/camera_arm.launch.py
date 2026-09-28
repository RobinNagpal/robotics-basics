"""Start the camera, the arm and the follower, which points the arm at the ball.

Run it with:  ros2 launch ros_camera_arm camera_arm.launch.py

This launch file reuses the other two packages: the camera publisher comes from
ros_camera, and the arm's description from ros_arm. Only the follower is new.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """List the programs to start. ros2 launch starts them all, and Ctrl-C stops them all."""
    with open(os.path.join(get_package_share_directory('ros_arm'), 'urdf', 'arm.urdf')) as urdf:
        description: str = urdf.read()
    rviz_layout: str = os.path.join(
        get_package_share_directory('ros_camera_arm'), 'config', 'camera_arm.rviz')

    return LaunchDescription([
        # A launch argument: a setting you can change on the command line, such
        # as rviz:=false to run without the RViz window.
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz.'),
        # The camera, from the ros_camera package.
        Node(package='ros_camera', executable='camera_publisher'),
        # The arm's description, from the ros_arm package, turned into TF.
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description}]),
        # The new part: watch the camera, and publish joint angles that point
        # the arm at the ball. It takes the place of ros_arm's arm_mover.
        Node(package='ros_camera_arm', executable='follower', output='screen'),
        # RViz, showing the arm and the camera's picture side by side.
        Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_layout],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
