"""Actions: long jobs, with progress while they run and a result at the end.

A service answers at once. But "move the arm to this pose", "drive to the
kitchen" and "close the gripper until it grips" take seconds, may need watching
while they run, and may need cancelling. That is an **action**, and it is how
every arm and every mobile base is commanded in ROS.

An action has three parts, and this file shows all three:

  goal      what to do, sent once
  feedback  how it is going, sent again and again while it runs
  result    how it ended, sent once

This node offers /count_up, which counts to the number asked for, one a second,
reporting each step. example_interfaces/action/Fibonacci is the type ROS ships
for this example: its goal is `order`, its feedback and result are a sequence.

Run it with:  ros2 run ros_basics basics_action_server

Then from another terminal (after `make shell`):

  ros2 run ros_basics basics_action_client 5
  ros2 action list
  ros2 action info /count_up -t
  ros2 action send_goal /count_up example_interfaces/action/Fibonacci "{order: 5}" --feedback
"""

import time

from example_interfaces.action import Fibonacci
import rclpy
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

# How long each step of the job pretends to take, in seconds.
STEP: float = 1.0


class Counter(Node):
    """Count up to the number asked for, one step a second."""

    def __init__(self) -> None:
        """Offer the action."""
        super().__init__('counter')

        # create it with the action type, its name, and the function that does
        # the work. That function runs while the caller waits, so it may take
        # as long as it likes, as long as it reports and can be cancelled.
        self.action: ActionServer = ActionServer(self, Fibonacci, '/count_up', self.count)
        self.get_logger().info('offering /count_up')

    def count(self, goal: ServerGoalHandle) -> Fibonacci.Result:
        """Do the job: count to goal.order, saying where it has got to."""
        wanted: int = goal.request.order
        self.get_logger().info(f'goal accepted: count to {wanted}')

        feedback: Fibonacci.Feedback = Fibonacci.Feedback()
        feedback.sequence = []
        for number in range(1, wanted + 1):
            # A goal can be cancelled by whoever sent it. A server that never
            # checks cannot be stopped, which is why this comes first.
            if goal.is_cancel_requested:
                goal.canceled()
                self.get_logger().warn('goal cancelled')
                return Fibonacci.Result()

            feedback.sequence.append(number)
            # Feedback goes back to the caller while the job runs. This is what
            # lets a screen show a progress bar, or another node react early.
            goal.publish_feedback(feedback)
            self.get_logger().info(f'  at {number} of {wanted}')
            time.sleep(STEP)

        # Saying it succeeded, and then the result, ends the goal.
        goal.succeed()
        result: Fibonacci.Result = Fibonacci.Result()
        result.sequence = feedback.sequence
        self.get_logger().info(f'done: {list(result.sequence)}')
        return result


def main(args: list[str] | None = None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node: Counter = Counter()
    try:
        # The work above sleeps, and a cancel has to be noticed while it does,
        # so this node needs more than one thread. A MultiThreadedExecutor is
        # the usual answer, and action servers almost always want one.
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
