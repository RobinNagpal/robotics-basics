"""Check the measurement on a capture recorded from Gazebo, without running Gazebo.

test/data/one_box is a rosbag made with ``ros2 run camera_one_box save_snapshot``
while the simulation was running. It holds one colour picture, one depth
picture, the camera info and the static transforms. Replaying it here goes
through the same libraries the node uses: rosbag2 to read it, cv_bridge for the
pictures, image_geometry for the lens and tf2 for where the camera is.

The tests use pytest. A fixture, marked @pytest.fixture, is a set-up function:
any test that names it as an argument gets its result. scope='module' means it
runs once for the whole file, so the bag is read only once.
"""

from pathlib import Path

from cv_bridge import CvBridge
from image_geometry import PinholeCameraModel
import numpy as np
import pytest
from rclpy.serialization import deserialize_message
from rclpy.time import Time
import rosbag2_py
from rosidl_runtime_py.utilities import get_message
from tf2_ros import Buffer

from camera_one_box.measure import depth_to_points, measure_box, to_world, transform_matrix

SNAPSHOT = Path(__file__).parent / 'data' / 'one_box'


@pytest.fixture(scope='module')
def capture():
    """Read every message in the snapshot, by topic."""
    # A bag stores each message as the bytes that were sent between the nodes.
    # The reader hands them back one at a time, with the topic they came on.
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(SNAPSHOT), storage_id='mcap'),
                rosbag2_py.ConverterOptions('', ''))
    # The bag also records each topic's message type, such as
    # 'sensor_msgs/msg/Image'. get_message turns that name into the Python
    # class, and deserialize_message turns the bytes back into a message of
    # that class, exactly as the box locator received it.
    types = {topic.name: topic.type for topic in reader.get_all_topics_and_types()}
    messages = {}
    while reader.has_next():
        topic, data, _ = reader.read_next()
        messages[topic] = deserialize_message(data, get_message(types[topic]))
    return messages


@pytest.fixture(scope='module')
def camera(capture):
    """Read the lens numbers from the camera info."""
    model = PinholeCameraModel()
    model.from_camera_info(capture['/camera/camera_info'])
    return model


@pytest.fixture(scope='module')
def camera_to_world(capture):
    """Look up where the camera is in the static transforms, as a 4 x 4 matrix."""
    # A TF Buffer can be used without a running robot: give it the recorded
    # transforms by hand, and it answers questions about them just the same.
    # The second argument names where they came from, for error messages.
    buffer = Buffer()
    for transform in capture['/tf_static'].transforms:
        buffer.set_transform_static(transform, 'snapshot')
    tf = buffer.lookup_transform('world', 'camera_optical_frame', Time())
    t, q = tf.transform.translation, tf.transform.rotation
    return transform_matrix((t.x, t.y, t.z), (q.x, q.y, q.z, q.w))


@pytest.fixture(scope='module')
def depth(capture):
    """Turn the depth picture into a NumPy array of metres."""
    return CvBridge().imgmsg_to_cv2(capture['/camera/depth/image_raw'], desired_encoding='32FC1')


def test_the_lens_is_the_one_the_doc_uses(camera):
    assert camera.full_resolution() == (320, 240)
    assert camera.fx() == pytest.approx(277.1, abs=0.05)
    assert camera.fy() == pytest.approx(277.1, abs=0.05)
    assert (camera.cx(), camera.cy()) == (160.0, 120.0)


def test_the_camera_hangs_40_cm_above_the_table_looking_down(camera_to_world):
    assert camera_to_world[:3, 3] == pytest.approx([0.0, 0.0, 0.40], abs=1e-6)
    # Its forward axis, the third column, points straight down.
    assert camera_to_world[:3, 2] == pytest.approx([0.0, 0.0, -1.0], abs=1e-6)


def test_the_table_reads_40_cm_and_the_box_top_34_cm(depth):
    assert np.nanmax(depth) == pytest.approx(0.400, abs=1e-4)
    assert np.nanmin(depth) == pytest.approx(0.340, abs=1e-4)
    assert int((depth < 0.399).sum()) == 2624       # the readings on the box, as in the doc


def test_the_doc_pixel_becomes_the_doc_point(depth, camera):
    """Section 1.1: pixel (212.5, 86.5) at depth 0.340 m is (+0.0644, -0.0411, 0.340)."""
    points = depth_to_points(depth, camera.fx(), camera.fy(), camera.cx(), camera.cy())
    assert points[86, 212] == pytest.approx([0.0644, -0.0411, 0.340], abs=5e-5)


def test_the_box_is_measured(depth, camera, camera_to_world):
    """Section 1.4: middle within a millimetre of (0.065, 0.040), height exactly 6 cm."""
    points = depth_to_points(depth, camera.fx(), camera.fy(), camera.cx(), camera.cy())
    box = measure_box(to_world(points, camera_to_world))
    assert (round(box.x, 3), round(box.y, 3)) == (0.064, 0.040)
    assert box.x == pytest.approx(0.065, abs=0.001)
    assert box.y == pytest.approx(0.040, abs=0.001)
    assert box.height == pytest.approx(0.060, abs=1e-4)


def test_a_bare_table_has_no_box():
    table = np.full((5, 5, 3), np.nan)
    table[..., 2] = 0.0
    assert measure_box(table.reshape(-1, 3)) is None
