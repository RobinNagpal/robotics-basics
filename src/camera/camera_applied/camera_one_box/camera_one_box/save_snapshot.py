"""Record one capture from the camera into a rosbag, then stop.

Run it while the simulation is running:

    ros2 run camera_one_box save_snapshot test/data/one_box

It waits for one depth picture, colour picture and camera info with the same
timestamp, writes them and the camera's static transforms into a rosbag2 file
(MCAP format), and exits. The tests replay that file, so they can check the
measurement without starting Gazebo.

Recording topics into a bag and replaying them later is how perception code
is usually developed and tested on real robots too.

A rosbag, or bag, is a recording of ROS messages. It stores each message as the
exact bytes that travelled between the nodes, with the topic it came on and the
time it was sent, so that it can be played back later as if it were live.
"""

import sys

import message_filters
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from rclpy.serialization import serialize_message
import rosbag2_py
from sensor_msgs.msg import CameraInfo, Image
from tf2_msgs.msg import TFMessage

# The camera topics to record, and the type of message each one carries.
TOPICS: dict[str, type] = {
    '/camera/image_raw': Image,
    '/camera/depth/image_raw': Image,
    '/camera/camera_info': CameraInfo,
}


# Like BoxLocator, this class extends rclpy's Node, which is what lets it
# subscribe to topics. box_locator.py explains what a Node is and why.
class SaveSnapshot(Node):
    """Write one synchronised set of camera messages, plus /tf_static, to a bag."""

    def __init__(self, output: str) -> None:
        """Open the bag, and subscribe to the camera and the static transforms."""
        super().__init__('save_snapshot')

        # rosbag2_py is the Python side of ros2 bag, the recording tool. A
        # SequentialWriter writes messages into a bag one after another.
        self.writer: rosbag2_py.SequentialWriter = rosbag2_py.SequentialWriter()
        self.writer.open(
            # Where to write, and in which file format. uri is the folder the
            # bag goes in, and MCAP is the standard format for ROS 2 bags.
            # zstd_fast compresses the file, which matters for pictures kept in git.
            rosbag2_py.StorageOptions(uri=output, storage_id='mcap',
                                      storage_preset_profile='zstd_fast'),
            # Two empty strings mean "store the messages exactly as they
            # arrive", without converting them to another format.
            rosbag2_py.ConverterOptions('', ''))
        # A bag has to be told about each topic before any message on it is
        # written: its name, and its type written as package/msg/Name, such as
        # sensor_msgs/msg/Image. 'cdr' is the byte format ROS 2 sends messages
        # in, so the bag stores them in the same format.
        for name, kind in [*TOPICS.items(), ('/tf_static', TFMessage)]:
            self.writer.create_topic(rosbag2_py.TopicMetadata(
                id=0, name=name, type=f'{kind.__module__.split(".")[0]}/msg/{kind.__name__}',
                serialization_format='cdr'))

        self.tf_static: TFMessage | None = None
        self.done: bool = False

        # /tf_static holds the transforms that never change, such as where the
        # camera is bolted. robot_state_publisher sends them once, when it
        # starts, and ROS keeps that last message for anyone who subscribes
        # later. A subscriber only gets that kept message if it asks for it, and
        # this QoS setting ("quality of service") is how it asks: TRANSIENT_LOCAL
        # means "also give me the message you kept from before I joined".
        latched: QoSProfile = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(TFMessage, '/tf_static', self.on_tf_static, latched)

        # The camera's three topics, taken together: the TimeSynchronizer waits
        # until it has one message on each with the same timestamp, and then
        # calls on_capture with all three. box_locator.py explains this in more
        # detail.
        subscribers: list[message_filters.Subscriber] = [
            message_filters.Subscriber(self, kind, name) for name, kind in TOPICS.items()]
        self.capture: message_filters.TimeSynchronizer = message_filters.TimeSynchronizer(
            subscribers, queue_size=10)
        self.capture.registerCallback(self.on_capture)

    def on_tf_static(self, msg: TFMessage) -> None:
        """Keep every static transform: robot_state_publisher may send them in parts."""
        if self.tf_static is None:
            self.tf_static = TFMessage()
        self.tf_static.transforms.extend(msg.transforms)

    def on_capture(self, colour: Image, depth: Image, info: CameraInfo) -> None:
        """Write the first capture that arrives after the transforms."""
        if self.done or self.tf_static is None:
            return
        # A bag stores each message's time as one whole number of nanoseconds.
        # A ROS timestamp is kept as whole seconds plus nanoseconds, so join them.
        stamp: int = depth.header.stamp.sec * 10**9 + depth.header.stamp.nanosec
        # serialize_message turns a message into the bytes ROS sends between
        # nodes, which is what a bag stores. Reading the bag back turns the bytes
        # into the same message again.
        #
        # rosbag2_py's type information says write() takes the data as a str,
        # but it takes the bytes that serialize_message returns, and that is what
        # ROS's own examples pass it. "type: ignore" tells mypy, the type
        # checker, not to report that one mismatch.
        for name, msg in zip(TOPICS, (colour, depth, info)):
            data: bytes = serialize_message(msg)
            self.writer.write(name, data, stamp)  # type: ignore[call-overload]
        tf_data: bytes = serialize_message(self.tf_static)
        self.writer.write('/tf_static', tf_data, stamp)  # type: ignore[call-overload]
        self.done = True


def main(args: list[str] | None = None) -> None:
    """Record one capture into the folder named on the command line."""
    # ros2 run can add its own arguments after --ros-args. Take those out, so
    # that only ours, the output folder, is left.
    argv: list[str] = rclpy.utilities.remove_ros_args(sys.argv if args is None else args)
    if len(argv) != 2:
        print('usage: ros2 run camera_one_box save_snapshot <output folder>')
        sys.exit(2)
    rclpy.init(args=args)
    node: SaveSnapshot = SaveSnapshot(argv[1])
    try:
        # spin_once() waits up to half a second for a message, handles it by
        # calling the right callback, and returns. Looping on it, rather than
        # calling spin() once, lets the program stop as soon as the capture is
        # written.
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        del node.writer          # closes the bag and writes its index
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    print(f'Saved one capture to {argv[1]}')


if __name__ == '__main__':
    main()
