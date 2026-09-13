"""Start the one-box simulation: Gazebo, the camera, the bridge to ROS, the box locator, RViz.

This is the usual shape of a simulated robot bring-up:

1. robot_state_publisher reads the robot description (here, a camera on a
   stand) and publishes its frames on TF.
2. Gazebo loads the world, and ros_gz_sim's ``create`` adds the robot to it
   from the same description.
3. ros_gz_bridge copies Gazebo's camera topics onto ROS topics, and
   depth_image_proc turns the depth picture into a point cloud.
4. The project's own node, box_locator, reads those topics and publishes what
   it finds.
5. RViz shows all of it.

Gazebo prints one error on macOS, "Unable to load Ogre Plugin". It is looking
for a Vulkan renderer, which macOS does not have. It uses Metal instead, and the
cameras work.
"""

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Build the launch description."""
    share = FindPackageShare('camera_one_box')
    world = PathJoinSubstitution([share, 'worlds', 'one_box.sdf'])
    description = PathJoinSubstitution([share, 'urdf', 'camera.urdf.xacro'])
    bridge_config = PathJoinSubstitution([share, 'config', 'bridge.yaml'])
    rviz_config = PathJoinSubstitution([share, 'config', 'one_box.rviz'])
    sim_time = {'use_sim_time': True}

    arguments = [
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz.'),
        DeclareLaunchArgument(
            'gui', default_value='false',
            description='Also open the Gazebo window. On macOS it runs as its own process.'),
    ]

    # Lets Gazebo find the table's grid texture, which lives next to the world file.
    resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', PathJoinSubstitution([share, 'worlds']))

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[sim_time, {
            'robot_description': ParameterValue(Command(['xacro ', description]), value_type=str),
        }],
    )

    # -s runs the Gazebo server only, with no window, and -r starts the
    # simulation straight away instead of paused.
    gazebo = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={'gz_args': ['-r -s -v 1 ', world]}.items(),
    )

    gazebo_window = ExecuteProcess(
        cmd=['gz', 'sim', '-g', '-v', '1'],
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    spawn_camera = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-world', 'one_box', '-topic', 'robot_description', '-name', 'camera_stand'],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[sim_time, {'config_file': bridge_config}],
    )

    # depth_image_proc expects rectified pictures. Gazebo's lens has no
    # distortion, so its raw pictures are already rectified.
    point_cloud = ComposableNodeContainer(
        name='point_cloud_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[ComposableNode(
            package='depth_image_proc',
            plugin='depth_image_proc::PointCloudXyzrgbNode',
            name='point_cloud_xyzrgb',
            parameters=[sim_time],
            remappings=[
                ('rgb/image_rect_color', '/camera/image_raw'),
                ('rgb/camera_info', '/camera/camera_info'),
                ('depth_registered/image_rect', '/camera/depth/image_raw'),
                ('points', '/camera/points'),
            ],
        )],
    )

    box_locator = Node(
        package='camera_one_box',
        executable='box_locator',
        parameters=[sim_time],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[sim_time],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        *arguments,
        resource_path,
        robot_state_publisher,
        gazebo,
        gazebo_window,
        spawn_camera,
        bridge,
        point_cloud,
        box_locator,
        rviz,
    ])
