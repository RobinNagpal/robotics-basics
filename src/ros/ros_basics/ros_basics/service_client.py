"""The other side of a service: asking, and waiting for the answer.

This program asks /add_two_ints to add two numbers, prints the answer and exits.
It is the shape every "ask another node to do something" looks like:

  1. make a client for the service's name and type
  2. wait until something is offering it
  3. fill in a request and send it, which gives back a future
  4. spin until the future has the answer

Run the server first, in another terminal (after `make shell`):

  ros2 run ros_basics basics_service_server
  ros2 run ros_basics basics_service_client 7 5
"""

import sys

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.client import Client
from rclpy.node import Node
from rclpy.task import Future

# How long to wait for the server to appear before giving up, in seconds.
WAIT: float = 5.0


class AskToAdd(Node):
    """Ask /add_two_ints for one sum."""

    def __init__(self) -> None:
        """Make the client, and wait until the service is there."""
        super().__init__('add_two_ints_client')
        self.client: Client = self.create_client(AddTwoInts, '/add_two_ints')

    def ask(self, a: int, b: int) -> int | None:
        """Send the two numbers, wait for the answer, and give it back."""
        # A service call fails if nobody is offering it, so a client waits.
        # This is the usual first line of any node that depends on another.
        if not self.client.wait_for_service(timeout_sec=WAIT):
            self.get_logger().error(f'nothing is offering /add_two_ints after {WAIT} s')
            return None

        request: AddTwoInts.Request = AddTwoInts.Request()
        request.a = a
        request.b = b

        # call_async sends the request and hands back a "future": a promise of
        # an answer that has not arrived yet. spin_until_future_complete keeps
        # the node running until it does. (Calling the blocking call() from
        # inside a callback would deadlock, which is why async is the habit.)
        future: Future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response: AddTwoInts.Response = future.result()
        return int(response.sum)


def main(args: list[str] | None = None) -> None:
    """Read two numbers from the command line, ask, and print the answer."""
    # remove_ros_args drops arguments meant for ROS, such as --ros-args
    # -r __node:=..., leaving the program's own.
    argv: list[str] = rclpy.utilities.remove_ros_args(sys.argv if args is None else args)
    if len(argv) != 3:
        print('usage: ros2 run ros_basics basics_service_client <a> <b>')
        sys.exit(2)

    rclpy.init(args=args)
    node: AskToAdd = AskToAdd()
    answer: int | None = node.ask(int(argv[1]), int(argv[2]))
    if answer is not None:
        node.get_logger().info(f'{argv[1]} + {argv[2]} = {answer}')
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
