"""Start the camera publisher, the camera subscriber, and RViz to show the pictures.

Run it with:  ros2 launch ros_camera camera.launch.py
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
    # The package's installed files, such as the saved RViz layout, live in its
    # "share" folder. get_package_share_directory finds that folder.
    rviz_layout = os.path.join(get_package_share_directory('ros_camera'), 'config', 'camera.rviz')

    return LaunchDescription([
        # A launch argument: a setting you can change on the command line, such
        # as rviz:=false to run without the RViz window.
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz.'),
        # Each Node(...) starts one program: an executable from a package.
        Node(package='ros_camera', executable='camera_publisher'),
        # output='screen' shows the program's messages in this terminal.
        Node(package='ros_camera', executable='camera_subscriber', output='screen'),
        # RViz, with a layout that shows the pictures on /camera/image_raw.
        Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_layout],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
