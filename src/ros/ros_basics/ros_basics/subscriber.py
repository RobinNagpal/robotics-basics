"""Subscribing: receiving the messages another node publishes.

A node that subscribes hands ROS a function, and ROS calls it every time a
message arrives on the topic. That function is called a **callback**. Between
messages the node does nothing at all: it is not a loop that checks, it is a
program that is woken up.

This node receives what publisher.py sends on /countdown.

Run the two together, in two terminals (each after `make shell`):

  ros2 run ros_basics basics_publisher
  ros2 run ros_basics basics_subscriber

Or start both at once with the launch file:  ros2 launch ros_basics basics.launch.py
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.subscription import Subscription
from std_msgs.msg import String


class Listener(Node):
    """Print every message that arrives on /countdown."""

    def __init__(self) -> None:
        """Subscribe to the topic, and say which function should get the messages."""
        super().__init__('countdown_subscriber')

        # The four arguments: the message type, the topic name, the function to
        # call with each message, and the queue length. The type and the name
        # must match the publisher's exactly, or nothing arrives and nothing
        # complains. `ros2 topic info -v /countdown` shows both sides when in doubt.
        self.subscription: Subscription = self.create_subscription(
            String, '/countdown', self.on_message, 10)
        self.received: int = 0
        self.get_logger().info('waiting for messages on /countdown')

    def on_message(self, message: String) -> None:
        """Print one message: ROS calls this for each one, with the message itself."""
        self.received += 1
        self.get_logger().info(f'received: {message.data}')

    # Keeping the work in the callback short matters: while it runs, this node
    # receives nothing else. Anything slow — planning, a model, writing a file —
    # belongs somewhere else, or the messages pile up and are dropped.


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Listener = Listener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
