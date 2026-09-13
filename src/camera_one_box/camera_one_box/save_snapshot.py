"""Record one capture from the camera into a rosbag, then stop.

Run it while the simulation is running:

    ros2 run camera_one_box save_snapshot test/data/one_box

It waits for one depth picture, colour picture and camera info with the same
timestamp, writes them and the camera's static transforms into a rosbag2 file
(MCAP format), and exits. The tests replay that file, so they can check the
measurement without starting Gazebo.

Recording topics into a bag and replaying them later is how perception code
is usually developed and tested on real robots too.
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

TOPICS = {
    '/camera/image_raw': Image,
    '/camera/depth/image_raw': Image,
    '/camera/camera_info': CameraInfo,
}


class SaveSnapshot(Node):
    """Write one synchronised set of camera messages, plus /tf_static, to a bag."""

    def __init__(self, output: str):
        """Open the bag, and subscribe to the camera and the static transforms."""
        super().__init__('save_snapshot')
        self.writer = rosbag2_py.SequentialWriter()
        self.writer.open(
            # zstd_fast compresses the file, which matters for pictures kept in git.
            rosbag2_py.StorageOptions(uri=output, storage_id='mcap',
                                      storage_preset_profile='zstd_fast'),
            rosbag2_py.ConverterOptions('', ''))
        for name, kind in [*TOPICS.items(), ('/tf_static', TFMessage)]:
            self.writer.create_topic(rosbag2_py.TopicMetadata(
                id=0, name=name, type=f'{kind.__module__.split(".")[0]}/msg/{kind.__name__}',
                serialization_format='cdr'))

        self.tf_static = None
        self.done = False
        # /tf_static is published once and kept for late joiners, so ask for that.
        latched = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(TFMessage, '/tf_static', self.on_tf_static, latched)
        subscribers = [message_filters.Subscriber(self, kind, name)
                       for name, kind in TOPICS.items()]
        self.capture = message_filters.TimeSynchronizer(subscribers, queue_size=10)
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
        stamp = depth.header.stamp.sec * 10**9 + depth.header.stamp.nanosec
        for name, msg in zip(TOPICS, (colour, depth, info)):
            self.writer.write(name, serialize_message(msg), stamp)
        self.writer.write('/tf_static', serialize_message(self.tf_static), stamp)
        self.done = True


def main(args=None) -> None:
    """Record one capture into the folder named on the command line."""
    argv = rclpy.utilities.remove_ros_args(sys.argv if args is None else args)
    if len(argv) != 2:
        print('usage: ros2 run camera_one_box save_snapshot <output folder>')
        sys.exit(2)
    rclpy.init(args=args)
    node = SaveSnapshot(argv[1])
    try:
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
