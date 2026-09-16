"""Publishing: sending messages on a topic, for anyone who wants them.

A **topic** is a named stream of messages. A node that publishes does not know
or care who is listening: it puts a message on the topic and moves on. That is
how nearly all of a robot's data travels — pictures, joint angles, speeds,
distances — because it lets any number of programs read the same stream, and
lets you replace the sender without touching the receivers.

This node publishes a counting message on /countdown twice a second.
subscriber.py receives it.

Run it with:  ros2 run ros_basics basics_publisher

While it runs, from another terminal (after `make shell`):

  ros2 topic list                 /countdown is in the list
  ros2 topic echo /countdown      print the messages as they arrive
  ros2 topic hz /countdown        how many a second
  ros2 topic info /countdown      the type, and how many are sending and receiving
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.timer import Timer
from std_msgs.msg import String

# How often a message goes out, in seconds.
PERIOD: float = 0.5


class Countdown(Node):
    """Publish a message on /countdown, twice a second."""

    def __init__(self) -> None:
        """Make the publisher, and a timer to use it."""
        super().__init__('countdown_publisher')

        # create_publisher says: "I will send messages of this type, on this
        # topic". The type must match what receivers expect, or they will not
        # even see each other. The 10 is the queue: how many messages ROS keeps
        # waiting if a receiver is slow, before it drops the oldest.
        self.publisher: Publisher = self.create_publisher(String, '/countdown', 10)
        self.sent: int = 0
        self.timer: Timer = self.create_timer(PERIOD, self.send)
        self.get_logger().info(f'publishing on /countdown every {PERIOD} s')

    def send(self) -> None:
        """Build one message and publish it."""
        self.sent += 1
        # A message is an ordinary Python object of its class. std_msgs/String
        # has one field, data. Most robot messages have many more, and a header
        # saying when and in which frame they were measured.
        message: String = String()
        message.data = f'message number {self.sent}'
        self.publisher.publish(message)
        self.get_logger().info(f'sent: {message.data}')


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Countdown = Countdown()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
