"""The other side of an action: send a goal, watch the progress, take the result.

This program asks /count_up to count to a number, prints every step it reports
along the way, and prints the result at the end. It is the shape of every
"tell the arm to go somewhere and wait for it" program.

Run the server first, in another terminal (after `make shell`):

  ros2 run ros_basics basics_action_server
  ros2 run ros_basics basics_action_client 5
"""

import sys

from example_interfaces.action import Fibonacci
import rclpy
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.node import Node
from rclpy.task import Future

# How long to wait for the server to appear before giving up, in seconds.
WAIT: float = 5.0


class AskToCount(Node):
    """Send one goal to /count_up and follow it to the end."""

    def __init__(self) -> None:
        """Make the client."""
        super().__init__('count_up_client')
        self.client: ActionClient = ActionClient(self, Fibonacci, '/count_up')

    def send(self, order: int) -> list[int] | None:
        """Send the goal, print the feedback as it comes, and give back the result."""
        if not self.client.wait_for_server(timeout_sec=WAIT):
            self.get_logger().error(f'nothing is offering /count_up after {WAIT} s')
            return None

        goal: Fibonacci.Goal = Fibonacci.Goal()
        goal.order = order

        # Sending a goal happens in two steps. First the server says whether it
        # accepts the goal at all, which is what this future carries.
        accepted: Future = self.client.send_goal_async(
            goal, feedback_callback=self.on_feedback)
        rclpy.spin_until_future_complete(self, accepted)
        handle: ClientGoalHandle = accepted.result()
        if not handle.accepted:
            self.get_logger().error('the server refused the goal')
            return None
        self.get_logger().info('goal accepted, waiting for it to finish')

        # Then the result, which arrives when the job is done. In between, the
        # feedback callback below runs every time the server reports progress.
        finished: Future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, finished)
        return list(finished.result().result.sequence)

    def on_feedback(self, message: Fibonacci.Impl.FeedbackMessage) -> None:
        """Print the progress, which ROS reports every time the server sends some."""
        self.get_logger().info(f'  progress: {list(message.feedback.sequence)}')


def main(args: list[str] | None = None) -> None:
    """Read the number from the command line, send the goal, print the result."""
    argv: list[str] = rclpy.utilities.remove_ros_args(sys.argv if args is None else args)
    if len(argv) != 2:
        print('usage: ros2 run ros_basics basics_action_client <count to>')
        sys.exit(2)

    rclpy.init(args=args)
    node: AskToCount = AskToCount()
    result: list[int] | None = node.send(int(argv[1]))
    if result is not None:
        node.get_logger().info(f'result: {result}')
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
