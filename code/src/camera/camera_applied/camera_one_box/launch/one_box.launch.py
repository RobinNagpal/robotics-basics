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

How a launch file works
-----------------------
A robot needs many programs running at once, and starting each one by hand, in
its own terminal, with the right settings, would be slow and easy to get wrong.
A launch file is a Python file that describes all of them in one place, and
`ros2 launch` starts them together and stops them together on Ctrl-C.

The function below does not start anything itself. It returns a
LaunchDescription: a list of things to start. Most of the values in it are
"substitutions", such as LaunchConfiguration or PathJoinSubstitution, which are
placeholders that get their real value only when the launch actually runs. That
is why paths and settings are built out of these objects instead of plain
strings.
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
    # When the package is built, setup.py copies its launch, urdf, worlds and
    # config folders into the package's "share" folder, inside install/.
    # FindPackageShare finds that folder, and PathJoinSubstitution builds a path
    # inside it, so this works wherever the workspace is.
    share: FindPackageShare = FindPackageShare('camera_one_box')
    world: PathJoinSubstitution = PathJoinSubstitution([share, 'worlds', 'one_box.sdf'])
    description: PathJoinSubstitution = PathJoinSubstitution([share, 'urdf', 'camera.urdf.xacro'])
    bridge_config: PathJoinSubstitution = PathJoinSubstitution([share, 'config', 'bridge.yaml'])
    rviz_config: PathJoinSubstitution = PathJoinSubstitution([share, 'config', 'one_box.rviz'])
    # Gazebo keeps its own clock, which starts at zero and can run slower or
    # faster than real time. Every node is told to use that clock, which it
    # reads from the /clock topic, so that the timestamps on the pictures and on
    # TF all agree.
    sim_time: dict[str, bool] = {'use_sim_time': True}

    # Launch arguments are the settings you can pass on the command line, as
    # name:=value. Each one is declared here with its default, and read further
    # down with LaunchConfiguration('name').
    arguments: list[DeclareLaunchArgument] = [
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz.'),
        DeclareLaunchArgument(
            'gui', default_value='false',
            description='Also open the Gazebo window. On macOS it runs as its own process.'),
        # The camera's picture size and lens. The defaults are the doc's camera.
        DeclareLaunchArgument('width', default_value='320', description='Pixels across.'),
        DeclareLaunchArgument('height', default_value='240', description='Pixels down.'),
        DeclareLaunchArgument('hfov_deg', default_value='60',
                              description='How wide the camera sees, in degrees.'),
    ]
    # The same settings, written as arguments for xacro, so that they reach the
    # camera description: xacro width:=320 height:=240 hfov_deg:=60.
    camera_settings: list[str | LaunchConfiguration] = [
        ' width:=', LaunchConfiguration('width'),
        ' height:=', LaunchConfiguration('height'),
        ' hfov_deg:=', LaunchConfiguration('hfov_deg'),
    ]

    # Lets Gazebo find the table's grid texture, which lives next to the world
    # file. An environment variable is a setting every program started from here
    # can read, and GZ_SIM_RESOURCE_PATH is the list of folders Gazebo searches
    # for files such as textures and models.
    resource_path: AppendEnvironmentVariable = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', PathJoinSubstitution([share, 'worlds']))

    # Node(...) starts one ROS program: the executable named here, from the
    # package named here, with these parameters.
    #
    # robot_state_publisher reads the robot description, here the camera on its
    # stand, and publishes where every part of it is on TF. The description is
    # made by running xacro on the .xacro file when the launch starts: Command
    # runs a program and uses what it prints. ParameterValue(value_type=str)
    # says to keep that as plain text. Without it, the launch system would try
    # to read the description as YAML, the format settings are usually written
    # in, and the XML would not make sense as YAML.
    robot_state_publisher: Node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[sim_time, {
            'robot_description': ParameterValue(
                Command(['xacro ', description, *camera_settings]), value_type=str),
        }],
    )

    # IncludeLaunchDescription runs another launch file, here the one that comes
    # with ros_gz_sim for starting Gazebo. gz_args are the options for Gazebo
    # itself: -s runs the Gazebo server only, with no window, -r starts the
    # simulation straight away instead of paused, and -v 1 prints errors only.
    gazebo: IncludeLaunchDescription = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={'gz_args': ['-r -s -v 1 ', world]}.items(),
    )

    # ExecuteProcess runs an ordinary command, not a ROS node. This one opens
    # Gazebo's window, but only if gui:=true was passed: IfCondition makes an
    # action happen only when a setting is true.
    gazebo_window: ExecuteProcess = ExecuteProcess(
        cmd=['gz', 'sim', '-g', '-v', '1'],
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    # create adds a model to a running Gazebo world, the same way a robot arm
    # would be added. It reads the camera description from the
    # robot_description topic, which robot_state_publisher publishes, so Gazebo
    # and ROS are guaranteed to use the same description. The world name must
    # match <world name="one_box"> in the world file.
    spawn_camera: Node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-world', 'one_box', '-topic', 'robot_description', '-name', 'camera_stand'],
        output='screen',
    )

    # Gazebo has its own message system, separate from ROS. The bridge copies
    # messages across, topic by topic, as listed in config/bridge.yaml.
    bridge: Node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[sim_time, {'config_file': bridge_config}],
    )

    # depth_image_proc turns the depth picture into a point cloud. It is written
    # as a "component", a node that is loaded into a container process instead
    # of running as its own program. Several components can share one
    # container, and can then be set to hand each other messages without
    # copying them, which matters for large messages such as pictures. That is
    # why image-processing nodes are written as components, even when, as here,
    # only one of them runs in the container.
    #
    # The component listens on fixed topic names, such as rgb/image_rect_color.
    # remappings connect each of those names to the topic this project uses.
    # depth_image_proc expects rectified pictures, meaning pictures with the
    # lens's bending taken out. Gazebo's lens has no distortion, so its raw
    # pictures are already rectified.
    point_cloud: ComposableNodeContainer = ComposableNodeContainer(
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

    # The project's own node. output='screen' makes its messages appear in the
    # terminal, which is where it prints what it measures.
    box_locator: Node = Node(
        package='camera_one_box',
        executable='box_locator',
        parameters=[sim_time],
        output='screen',
    )

    # RViz, the 3D viewer, opened with the saved layout in config/one_box.rviz
    # (-d names the layout file), unless rviz:=false was passed.
    rviz: Node = Node(
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
