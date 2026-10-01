"""The box locator node: reads the depth camera, finds the box, publishes where it is.

Subscribes to:
  /camera/depth/image_raw   sensor_msgs/Image, depth in metres (32FC1)
  /camera/camera_info       sensor_msgs/CameraInfo, the four lens numbers
  TF                        where the camera is, from robot_state_publisher

Publishes:
  /detections               vision_msgs/Detection3DArray, what a grasp planner reads
  /detection_markers        visualization_msgs/MarkerArray, the same thing for RViz

The libraries are the ones a real arm project uses: cv_bridge turns the image
message into a NumPy array, image_geometry reads the lens numbers out of the
camera info, message_filters pairs each picture with its camera info, and tf2
says where the camera is. The maths itself is in measure.py.

A few words used in the comments below:

* A **node** is one running ROS program. Nodes talk to each other by sending
  **messages** on named channels called **topics**, such as
  /camera/depth/image_raw. A node that sends on a topic **publishes** to it, and
  a node that receives from it **subscribes** to it.
* A **callback** is a function we hand to ROS, which ROS then calls for us
  whenever the thing we asked for arrives, such as a new picture.
* A **frame** is a set of axes: a starting point and three directions. Every
  position in ROS is measured in some frame, such as the room (`world`) or the
  camera (`camera_optical_frame`), and **TF** is the part of ROS that knows how
  every frame sits relative to every other one.
"""

# builtin_interfaces.msg.Time is the message type for a timestamp, named TimeMsg
# here to tell it apart from rclpy's Time, a point in time that can do arithmetic.
from builtin_interfaces.msg import Time as TimeMsg
from cv_bridge import CvBridge
from geometry_msgs.msg import Quaternion, TransformStamped, Vector3
from image_geometry import PinholeCameraModel
import message_filters
import numpy as np
from numpy.typing import NDArray
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image
from tf2_ros import Buffer, TransformException, TransformListener
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose
from visualization_msgs.msg import Marker, MarkerArray

from camera_one_box.measure import (
    BoxMeasurement,
    depth_to_points,
    measure_box,
    to_world,
    transform_matrix,
)


# What a Node is, and why this class extends it
# ---------------------------------------------
# A robot's software is not one big program. It is many small programs, called
# nodes, each doing one job: one talks to the camera, one works out where the
# box is, one plans how the arm should move, and so on. They run at the same
# time and send each other messages. Splitting the work up like this means each
# part can be written, tested and restarted on its own, and a part can be swapped
# for another, for example a real camera instead of a simulated one, without
# touching the rest.
#
# rclpy is the ROS library for Python, and its Node class is what makes a
# program one of those nodes. A Node has a name, and it knows how to find the
# other nodes and talk to them. It provides the methods this class uses:
#
#   create_publisher()      to send messages on a topic
#   create_subscription()   to receive them (message_filters uses it for us)
#   declare_parameter()     to read settings from the launch file
#   get_logger()            to print messages, marked with the node's name
#
# BoxLocator extends Node, which means it is a Node, with all of those methods,
# plus the code for its own job. That is the usual way to write a node in ROS 2:
# the node's settings, its subscriptions and publishers, and the callbacks that
# do the work all live together in one class, and self is both "the box locator"
# and "the ROS node". It is also what lets ROS run it: rclpy.spin() in main()
# takes a Node, and keeps calling that node's callbacks as messages arrive.
class BoxLocator(Node):
    """Measure the box in every depth picture the camera sends."""

    def __init__(self) -> None:
        """Declare the parameters, and connect the subscriptions and publishers."""
        # Register this program with ROS under the name 'box_locator'. That is
        # the name `ros2 node list` shows, and the name at the start of every
        # line this node prints.
        super().__init__('box_locator')

        # Parameters are settings that can be changed from the launch file or
        # the command line, without editing this code. Each line declares one,
        # with its default value, and .value reads what it was actually set to.
        self.world_frame: str = self.declare_parameter('world_frame', 'world').value
        self.table_z: float = self.declare_parameter('table_z', 0.0).value
        self.min_height: float = self.declare_parameter('min_height', 0.01).value

        # A picture arrives as a ROS message: a long list of bytes, plus its
        # width, its height and a note saying what the bytes mean. CvBridge turns
        # that message into a NumPy array, one number per pixel, which is what
        # we can do arithmetic on. It is called a bridge because it connects ROS
        # images to OpenCV, the standard picture library, which uses the same
        # arrays.
        self.bridge: CvBridge = CvBridge()

        # PinholeCameraModel holds the camera's lens: the four numbers fx, fy,
        # cx and cy from the basics doc. It is empty for now, and it is filled in
        # from each camera info message as it arrives. "Pinhole" is the name of
        # the simple camera model the basics doc explains.
        self.camera: PinholeCameraModel = PinholeCameraModel()

        # TF keeps track of where every frame is. The Buffer is its memory: it
        # stores every transform it hears about, so that we can ask it later
        # where one frame is compared with another. The TransformListener fills
        # the Buffer by subscribing to TF's topics, /tf and /tf_static, in the
        # background, which is why it is given the node (self) to subscribe
        # with. It has to be kept in a variable, even though this code never
        # uses it again, because otherwise Python would throw it away and it
        # would stop listening.
        self.tf_buffer: Buffer = Buffer()
        self.tf_listener: TransformListener = TransformListener(self.tf_buffer, self)

        # A depth picture only means something next to the lens that took it,
        # so take them in pairs with matching timestamps. A message_filters
        # Subscriber works like an ordinary subscription, but instead of calling
        # our code for every message, it hands the messages to a filter.
        depth: message_filters.Subscriber = message_filters.Subscriber(
            self, Image, '/camera/depth/image_raw')
        info: message_filters.Subscriber = message_filters.Subscriber(
            self, CameraInfo, '/camera/camera_info')
        # The TimeSynchronizer is that filter. It holds on to messages until it
        # has a depth picture and a camera info with exactly the same timestamp,
        # and then calls on_picture with both. queue_size is how many unmatched
        # messages it keeps while it waits for their partners.
        self.pairs: message_filters.TimeSynchronizer = message_filters.TimeSynchronizer(
            [depth, info], queue_size=10)
        self.pairs.registerCallback(self.on_picture)

        # A publisher announces that this node will send messages of one type on
        # one topic. The 10 is how many messages ROS keeps waiting if a
        # subscriber is slow to take them, before it starts dropping old ones.
        self.detections: Publisher = self.create_publisher(Detection3DArray, 'detections', 10)
        self.markers: Publisher = self.create_publisher(MarkerArray, 'detection_markers', 10)

    def on_picture(self, depth_msg: Image, info_msg: CameraInfo) -> None:
        """Measure the box in one depth picture, and publish what was found."""
        # Read the four lens numbers out of the camera info. The camera sends
        # them with every picture, so this is always the lens that took this
        # picture, even if someone changes the camera while it runs.
        self.camera.from_camera_info(info_msg)

        # Turn the depth message into a NumPy array. '32FC1' means one 32-bit
        # decimal number per pixel, which here is the distance in metres. Asking
        # for it by name makes cv_bridge check that the picture really is that.
        depth: NDArray[np.float32] = self.bridge.imgmsg_to_cv2(
            depth_msg, desired_encoding='32FC1')

        try:
            # Ask TF where the camera was, measured in the room. Every picture
            # says which frame it was taken in, in header.frame_id, which here is
            # camera_optical_frame. The answer is the transform that moves a point
            # from that frame into the world frame. Time() means "the latest you
            # have". The camera is bolted to the world, so its transform never
            # changes and the latest one is the right one.
            tf: TransformStamped = self.tf_buffer.lookup_transform(
                self.world_frame, depth_msg.header.frame_id, Time())
        except TransformException as error:
            # For the first moment after starting, TF may not have heard about
            # the camera yet. Say so and skip this picture: another arrives soon.
            # Pictures arrive five times a second, so throttle_duration_sec limits
            # this message to once every two seconds.
            self.get_logger().warn(f'No transform to the camera yet: {error}',
                                   throttle_duration_sec=2.0)
            return

        # TF gives the transform as a translation, where the camera is, and a
        # rotation, which way it is turned. The rotation is a quaternion, four
        # numbers that describe a turn. transform_matrix() turns both into the
        # camera_to_world table from the one-box intro.
        t: Vector3 = tf.transform.translation
        q: Quaternion = tf.transform.rotation
        camera_to_world: NDArray[np.float64] = transform_matrix(
            (t.x, t.y, t.z), (q.x, q.y, q.z, q.w))

        # The maths, from measure.py: every pixel becomes a point measured from
        # the camera, those points are moved into the room, and the box is found
        # among them and measured.
        points: NDArray[np.float64] = depth_to_points(
            depth, self.camera.fx(), self.camera.fy(), self.camera.cx(), self.camera.cy())
        box: BoxMeasurement | None = measure_box(
            to_world(points, camera_to_world), self.table_z, self.min_height)
        if box is None:
            self.get_logger().info('Nothing is standing on the table.', throttle_duration_sec=2.0)
            return

        # Print the answer in the terminal, at most once every two seconds.
        self.get_logger().info(
            f'box: middle ({box.x:+.3f}, {box.y:+.3f}) m, height {box.height:.3f} m, '
            f'from {box.points:,} points on its top',
            throttle_duration_sec=2.0)
        # Publish it with the depth picture's timestamp, so that anyone reading
        # it knows exactly which moment it describes.
        self.publish(box, depth_msg.header.stamp)

    def publish(self, box: BoxMeasurement, stamp: TimeMsg) -> None:
        """Publish the box as a detection, and as a marker RViz can draw."""
        # A Detection3D is the standard ROS message for "I found something, and
        # here it is". Every message that carries a position has a header, which
        # says which frame the numbers are measured in and when they were true.
        detection: Detection3D = Detection3D()
        detection.header.frame_id = self.world_frame
        detection.header.stamp = stamp
        # bbox is the bounding box: the smallest box that holds the object,
        # given by its middle and its size. Its middle is half way up the box.
        detection.bbox.center.position.x = box.x
        detection.bbox.center.position.y = box.y
        detection.bbox.center.position.z = self.table_z + box.height / 2.0
        detection.bbox.size.x = box.width_x
        detection.bbox.size.y = box.width_y
        detection.bbox.size.z = box.height
        # A detection also says what the object is and how sure we are, as a
        # hypothesis: a label, and a score from 0 to 1. This node only ever
        # looks for one thing, so it is always a 'box', and always certain.
        hypothesis: ObjectHypothesisWithPose = ObjectHypothesisWithPose()
        hypothesis.hypothesis.class_id = 'box'
        hypothesis.hypothesis.score = 1.0
        hypothesis.pose.pose = detection.bbox.center
        detection.results.append(hypothesis)
        # A Detection3DArray holds everything found in one picture. Here that is
        # a single box, but a grasp planner expects a list.
        self.detections.publish(Detection3DArray(header=detection.header, detections=[detection]))

        # A Marker is a shape for RViz to draw. The namespace and id name this
        # marker, so each new message replaces the old cube instead of adding
        # another one. ADD means "add it, or change it if it is already there".
        marker: Marker = Marker()
        marker.header = detection.header
        marker.ns, marker.id = 'box', 0
        marker.type, marker.action = Marker.CUBE, Marker.ADD
        marker.pose = detection.bbox.center
        marker.scale = detection.bbox.size
        # Red, green and blue from 0 to 1, and a for alpha: 0.5 is see-through,
        # so the real box shows through the measured one.
        marker.color.r, marker.color.g, marker.color.b, marker.color.a = 0.2, 0.9, 1.0, 0.5
        self.markers.publish(MarkerArray(markers=[marker]))


def main(args: list[str] | None = None) -> None:
    """Run the node until Ctrl-C."""
    # Start ROS for this program. This has to happen before any node is made.
    rclpy.init(args=args)
    node: BoxLocator = BoxLocator()
    try:
        # spin() keeps the program running, waiting for messages and calling
        # the callbacks, such as on_picture, as they arrive. It only returns
        # when the program is asked to stop.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass    # Ctrl-C, or the launch file shutting everything down
    finally:
        # Close the node's subscriptions and publishers, then stop ROS. The
        # "try" in try_shutdown is because Ctrl-C may already have stopped it.
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
