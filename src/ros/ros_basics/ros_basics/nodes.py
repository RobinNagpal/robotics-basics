"""A node: the smallest ROS program there is.

Everything a robot runs is a **node**: one program, with a name, that joins the
robot's network and can then send and receive. This file is a node that does
nothing except say it is alive once a second, which is enough to show the four
parts every node has:

  1. rclpy.init()      start ROS for this program
  2. a Node with a name, which is how everything else refers to it
  3. work: here a timer, in a real node a subscription, a service, a controller
  4. rclpy.spin()      hand the program over to ROS until it is stopped

Run it with:  ros2 run ros_basics basics_node

While it runs, another terminal can see it, with `make shell` first:

  ros2 node list             /heartbeat is in the list
  ros2 node info /heartbeat  what it publishes, subscribes to and offers
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.timer import Timer


class Heartbeat(Node):
    """Say "I am alive" once a second, and count how many times."""

    def __init__(self) -> None:
        """Give the node its name, and start a timer."""
        # The name is what `ros2 node list` shows, and what every log line is
        # marked with. Two nodes with the same name confuse ROS, so each
        # program in a robot gets its own.
        super().__init__('heartbeat')

        self.beats: int = 0
        # A timer is how a node does something regularly. ROS calls the given
        # function every 1.0 seconds, and the node does nothing in between.
        self.timer: Timer = self.create_timer(1.0, self.beat)

        # get_logger() prints through ROS rather than with print(), so the line
        # carries the node's name and its level, and tools can collect it.
        # The levels, from quietest to loudest: debug, info, warn, error, fatal.
        self.get_logger().info('started: this node does nothing but count')

    def beat(self) -> None:
        """Count one beat, and say so."""
        self.beats += 1
        self.get_logger().info(f'alive, beat {self.beats}')
        if self.beats == 5:
            self.get_logger().warn('five beats already; nothing else to do here')


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    # init() connects this program to ROS. Nothing above can be done before it.
    rclpy.init(args=args)
    node: Heartbeat = Heartbeat()
    try:
        # spin() gives the program to ROS: it waits, and calls the node's
        # timers and callbacks as they come due. It returns when ROS is asked
        # to stop, with Ctrl-C or by a launch file shutting everything down.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
