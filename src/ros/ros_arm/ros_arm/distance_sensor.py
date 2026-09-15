"""The simplest sensor: a distance sensor in the gripper, looking down at the table.

A real distance sensor sends out a pulse of sound or light, and times how long
it takes to bounce back. Its driver publishes each reading as a
sensor_msgs/Range message: one distance, and a few numbers that describe the
sensor. This node publishes the same message, ten times a second. It has no real
sensor to read, so it works the distance out itself, the way the camera
publisher draws its own picture: it asks TF where the sensor is, and works out
how far the sensor's beam has to travel to reach the table.

Publishes:
  /tip_range    sensor_msgs/Range   the distance from the gripper to the table, in metres

Run it on its own with:  ros2 run ros_arm distance_sensor
(It needs robot_state_publisher running, so that TF knows where the sensor is.)
"""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from scipy.spatial.transform import Rotation
from sensor_msgs.msg import Range
from tf2_ros import Buffer, TransformException, TransformListener

MIN_RANGE = 0.02           # the nearest the sensor can measure, in metres
MAX_RANGE = 1.0            # the furthest it can measure, in metres
FIELD_OF_VIEW = 0.1        # how wide its beam is, in radians (about 6 degrees)


def distance_to_table(height: float, downwards: float) -> float:
    """Say how far the beam travels to reach the table, in metres.

    :param height: How high the sensor is above the table.
    :param downwards: How much of the beam's direction points down: 1 when it
        points straight down, less when it leans, and 0 or less when it points
        level or up, in which case it never reaches the table.
    """
    if downwards <= 0:
        return math.inf
    return height / downwards


# DistanceSensor extends rclpy's Node, which is what makes this program a ROS
# node: something with a name, that can publish messages on topics.
class DistanceSensor(Node):
    """Publish the distance from the gripper to the table, ten times a second."""

    def __init__(self):
        """Create the publisher, listen to TF, and start a timer."""
        super().__init__('distance_sensor')
        self.publisher = self.create_publisher(Range, '/tip_range', 10)
        # TF keeps track of where every frame is. The Buffer stores what TF
        # hears, and the TransformListener fills it in the background.
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.1, self.measure)

    def measure(self) -> None:
        """Work out one reading, and publish it."""
        try:
            # Where is the sensor, measured from the base? The base sits on the
            # table, so the sensor's height above the base is its height above
            # the table.
            tf = self.tf_buffer.lookup_transform('base_link', 'range_sensor', Time())
        except TransformException:
            return                  # TF has not heard about the arm yet
        height = tf.transform.translation.z
        # A distance sensor measures along its own x axis. Turn that axis into
        # the base's axes: its third number, z, is how much it points up, so
        # minus z is how much it points down.
        q = tf.transform.rotation
        beam = Rotation.from_quat([q.x, q.y, q.z, q.w]).apply([1.0, 0.0, 0.0])
        distance = distance_to_table(height, -beam[2])

        # A Range message holds one reading, and describes the sensor that took
        # it: what kind it is, how wide its beam is, and the nearest and
        # furthest it can measure. A reading it cannot make is sent as infinity.
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'range_sensor'
        msg.radiation_type = Range.INFRARED
        msg.field_of_view = FIELD_OF_VIEW
        msg.min_range = MIN_RANGE
        msg.max_range = MAX_RANGE
        msg.range = distance if MIN_RANGE <= distance <= MAX_RANGE else math.inf
        self.publisher.publish(msg)
        self.get_logger().info(f'{msg.range:.3f} m to the table', throttle_duration_sec=1.0)


def main(args=None) -> None:
    """Start ROS, run the node until Ctrl-C, then stop."""
    rclpy.init(args=args)
    node = DistanceSensor()
    try:
        # spin() keeps the program running, and lets ROS call the node's timer
        # or callbacks whenever they are due. It returns when the program is
        # asked to stop, for example with Ctrl-C.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass        # Ctrl-C, or the launch file stopping everything: not an error


if __name__ == '__main__':
    main()
