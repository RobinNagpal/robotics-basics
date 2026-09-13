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
"""

from cv_bridge import CvBridge
from image_geometry import PinholeCameraModel
import message_filters
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image
from tf2_ros import Buffer, TransformException, TransformListener
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose
from visualization_msgs.msg import Marker, MarkerArray

from camera_one_box.measure import depth_to_points, measure_box, to_world, transform_matrix


class BoxLocator(Node):
    """Measure the box in every depth picture the camera sends."""

    def __init__(self):
        """Declare the parameters, and connect the subscriptions and publishers."""
        super().__init__('box_locator')
        self.world_frame = self.declare_parameter('world_frame', 'world').value
        self.table_z = self.declare_parameter('table_z', 0.0).value
        self.min_height = self.declare_parameter('min_height', 0.01).value

        self.bridge = CvBridge()
        self.camera = PinholeCameraModel()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # A depth picture only means something next to the lens that took it,
        # so take them in pairs with matching timestamps.
        depth = message_filters.Subscriber(self, Image, '/camera/depth/image_raw')
        info = message_filters.Subscriber(self, CameraInfo, '/camera/camera_info')
        self.pairs = message_filters.TimeSynchronizer([depth, info], queue_size=10)
        self.pairs.registerCallback(self.on_picture)

        self.detections = self.create_publisher(Detection3DArray, 'detections', 10)
        self.markers = self.create_publisher(MarkerArray, 'detection_markers', 10)

    def on_picture(self, depth_msg: Image, info_msg: CameraInfo) -> None:
        """Measure the box in one depth picture, and publish what was found."""
        self.camera.from_camera_info(info_msg)
        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='32FC1')

        try:
            # The camera is bolted to the world, so its transform never changes
            # and the latest one is the right one.
            tf = self.tf_buffer.lookup_transform(
                self.world_frame, depth_msg.header.frame_id, Time())
        except TransformException as error:
            self.get_logger().warn(f'No transform to the camera yet: {error}',
                                   throttle_duration_sec=2.0)
            return
        t, q = tf.transform.translation, tf.transform.rotation
        camera_to_world = transform_matrix((t.x, t.y, t.z), (q.x, q.y, q.z, q.w))

        points = depth_to_points(
            depth, self.camera.fx(), self.camera.fy(), self.camera.cx(), self.camera.cy())
        box = measure_box(to_world(points, camera_to_world), self.table_z, self.min_height)
        if box is None:
            self.get_logger().info('Nothing is standing on the table.', throttle_duration_sec=2.0)
            return

        self.get_logger().info(
            f'box: middle ({box.x:+.3f}, {box.y:+.3f}) m, height {box.height:.3f} m, '
            f'from {box.points:,} points on its top',
            throttle_duration_sec=2.0)
        self.publish(box, depth_msg.header.stamp)

    def publish(self, box, stamp) -> None:
        """Publish the box as a detection, and as a marker RViz can draw."""
        detection = Detection3D()
        detection.header.frame_id = self.world_frame
        detection.header.stamp = stamp
        detection.bbox.center.position.x = box.x
        detection.bbox.center.position.y = box.y
        detection.bbox.center.position.z = self.table_z + box.height / 2.0
        detection.bbox.size.x = box.width_x
        detection.bbox.size.y = box.width_y
        detection.bbox.size.z = box.height
        hypothesis = ObjectHypothesisWithPose()
        hypothesis.hypothesis.class_id = 'box'
        hypothesis.hypothesis.score = 1.0
        hypothesis.pose.pose = detection.bbox.center
        detection.results.append(hypothesis)
        self.detections.publish(Detection3DArray(header=detection.header, detections=[detection]))

        marker = Marker()
        marker.header = detection.header
        marker.ns, marker.id = 'box', 0
        marker.type, marker.action = Marker.CUBE, Marker.ADD
        marker.pose = detection.bbox.center
        marker.scale = detection.bbox.size
        marker.color.r, marker.color.g, marker.color.b, marker.color.a = 0.2, 0.9, 1.0, 0.5
        self.markers.publish(MarkerArray(markers=[marker]))


def main(args=None) -> None:
    """Run the node until Ctrl-C."""
    rclpy.init(args=args)
    node = BoxLocator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass    # Ctrl-C, or the launch file shutting everything down
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
