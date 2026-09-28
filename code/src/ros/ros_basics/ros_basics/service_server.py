"""Services: asking one node a question and getting one answer back.

A topic is a stream that nobody has to be listening to. A **service** is the
other shape: one node asks, one node answers, and the asker waits for that
answer. Robots use services for short jobs with a yes or no at the end: turn the
gripper's power on, clear the map, take a snapshot, work something out.

The rule of thumb: a service must be quick. Anything that takes seconds and
might need to be cancelled or watched is an **action**, which is action_server.py.

This node offers /add_two_ints, which takes two whole numbers and answers with
their sum. example_interfaces/srv/AddTwoInts is the type ROS ships for exactly
this example, so no new message package is needed.

Run it with:  ros2 run ros_basics basics_service_server

Then from another terminal (after `make shell`), either the client in this
package or the command line:

  ros2 run ros_basics basics_service_client 7 5
  ros2 service list
  ros2 service type /add_two_ints
  ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 7, b: 5}"
"""

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.service import Service


class Adder(Node):
    """Answer /add_two_ints with the sum of the two numbers."""

    def __init__(self) -> None:
        """Offer the service."""
        super().__init__('adder')

        # create_service(type, name, callback). From now on the node answers
        # anyone who calls that name with that type.
        self.service: Service = self.create_service(AddTwoInts, '/add_two_ints', self.add)
        self.get_logger().info('offering /add_two_ints')

    def add(self, request: AddTwoInts.Request,
            response: AddTwoInts.Response) -> AddTwoInts.Response:
        """Work out the answer: ROS calls this with the asker's request.

        A service type has two halves, Request and Response, and ROS hands both
        to the callback: the request filled in, the response empty for you to
        fill. Whatever is returned goes back to the asker, who has been waiting.
        """
        response.sum = request.a + request.b
        self.get_logger().info(f'asked {request.a} + {request.b}, answering {response.sum}')
        return response


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Adder = Adder()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
