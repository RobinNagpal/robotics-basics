"""Start the arm: its description, the program that moves it, and RViz to show it.

Run it with:  ros2 launch ros_arm arm.launch.py
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
    share: str = get_package_share_directory('ros_arm')
    rviz_layout: str = os.path.join(share, 'config', 'arm.rviz')
    # robot_state_publisher needs the arm's description as text, so read the
    # URDF file in.
    with open(os.path.join(share, 'urdf', 'arm.urdf')) as urdf:
        description: str = urdf.read()

    return LaunchDescription([
        # A launch argument: a setting you can change on the command line, such
        # as rviz:=false to run without the RViz window.
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz.'),
        # robot_state_publisher reads the description, listens to /joint_states,
        # and publishes where every part of the arm is on TF.
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description}]),
        # Our program: it publishes the joint angles that make the arm move.
        Node(package='ros_arm', executable='arm_mover'),
        # The distance sensor in the gripper: it publishes how far the table is.
        Node(package='ros_arm', executable='distance_sensor', output='screen'),
        # RViz, with a layout that draws the arm and its frames.
        Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_layout],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
