"""Parameters: a node's settings, which can be read and changed while it runs.

Robot code is full of numbers that should not be typed into the code: which
serial port, how fast to move, how long to wait, which frame to measure in. In
ROS those are **parameters**. A node declares the ones it has, with a default
and a description, and they can then be set from the command line, from a launch
file, from a YAML file, or changed live while the robot runs.

This node has three, and prints them once a second so that a change shows up.

Run it with:  ros2 run ros_basics basics_parameters

Then, from another terminal (after `make shell`):

  ros2 param list /settings                  what it has
  ros2 param get /settings speed_mps         read one
  ros2 param set /settings speed_mps 0.5     change one, and watch the node
  ros2 param set /settings speed_mps 9.9     refused: see the check below
  ros2 param dump /settings                  save them all as YAML

Starting it with a value already set:

  ros2 run ros_basics basics_parameters --ros-args -p robot_name:=picker
"""

from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.timer import Timer

# The fastest this imaginary robot may be told to move.
SPEED_LIMIT: float = 1.0


class Settings(Node):
    """Hold three settings, and show them changing."""

    def __init__(self) -> None:
        """Declare the parameters, with their defaults and descriptions."""
        super().__init__('settings')

        # declare_parameter(name, default, description). The type comes from the
        # default: a str, a float and an int here. A parameter that is not
        # declared cannot be set, which is what stops a typo on the command line
        # from silently doing nothing.
        self.declare_parameter('robot_name', 'demo',
                               ParameterDescriptor(description='What to call this robot.'))
        self.declare_parameter('speed_mps', 0.2,
                               ParameterDescriptor(description='How fast to move, m/s.'))
        self.declare_parameter('joints', 2,
                               ParameterDescriptor(description='How many joints it has.'))

        # A callback that runs before any parameter changes, and can refuse the
        # change. This is where a node protects itself from impossible values.
        self.add_on_set_parameters_callback(self.check)

        self.timer: Timer = self.create_timer(1.0, self.show)

    def check(self, parameters: list[Parameter]) -> SetParametersResult:
        """Say whether a set of changes is allowed. Refusing one refuses them all."""
        for parameter in parameters:
            if parameter.name == 'speed_mps' and parameter.value > SPEED_LIMIT:
                self.get_logger().warn(
                    f'refused speed_mps = {parameter.value}: the limit is {SPEED_LIMIT}')
                return SetParametersResult(successful=False,
                                           reason=f'speed_mps must be at most {SPEED_LIMIT}')
        return SetParametersResult(successful=True)

    def show(self) -> None:
        """Read the parameters and print them, so a change is visible."""
        # get_parameter(...).value gives the current value, which may have been
        # changed a moment ago from another terminal. A node that only reads its
        # parameters in __init__ will never notice.
        name: str = self.get_parameter('robot_name').value
        speed: float = self.get_parameter('speed_mps').value
        joints: int = self.get_parameter('joints').value
        self.get_logger().info(f'robot_name = {name}, speed_mps = {speed}, joints = {joints}')


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Settings = Settings()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
