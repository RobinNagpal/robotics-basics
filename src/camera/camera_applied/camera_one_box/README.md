# camera_one_box

A depth camera in Gazebo looks down at a table, finds the box standing on it, and
measures where the box is and how tall it is. This package is laid out the way a
real robot arm's perception code is, and it uses the same libraries.

This file is about running the code and finding your way around it. The ideas
behind it, and the maths, are explained in
[docs/camera/one-box-intro.md](../../../../docs/camera/one-box-intro.md), which builds
on [docs/camera/basics.md](../../../../docs/camera/basics.md), and
[docs/camera/one-box-code.md](../../../../docs/camera/one-box-code.md) explains the
code and the basics of every library it uses.

## Contents

1. [Commands](#1-commands)
   - [1.1 The everyday commands](#11-the-everyday-commands)
   - [1.2 Changing the camera](#12-changing-the-camera)
   - [1.3 Tests and recordings](#13-tests-and-recordings)
2. [The main Python files](#2-the-main-python-files)
3. [Layout](#3-layout)

## 1. Commands

Every command here runs from the top of the repository, not from this folder.
`make camera.one_box` builds the workspace before it starts, so it always runs
the latest code.

### 1.1 The everyday commands

The first command starts the whole simulation, and the other two look at it
while it runs, so run them in a second terminal.

| Command | What it does |
| --- | --- |
| `make camera.one_box` | Starts Gazebo, the camera, the box locator and RViz. The box locator prints what it measures every two seconds. Press Ctrl-C to stop everything. |
| `make camera.pixels` | Prints one picture from the 80 × 60 basic camera, one coloured square per pixel, followed by the actual depth readings for a patch on the box's edge. |
| `make camera.check` | Lists the topics, and prints the camera info, one message from each picture topic, the point cloud and the measured box. |

When the simulation is running, the box locator prints this line every two
seconds:

```
box: middle (+0.064, +0.040) m, height 0.060 m, from 2,401 points on its top
```

The `make` commands are short names for ordinary ROS 2 commands. To type those
yourself, open a shell with ROS ready first, with `make shell`, and then:

```
ros2 launch camera_one_box one_box.launch.py     # the same as make camera.one_box
ros2 run camera_one_box show_pixels              # the same as make camera.pixels
```

### 1.2 Changing the camera

The launch file takes arguments, so the camera can be changed without editing
any code. Pass them after the launch command, as `name:=value`:

```
ros2 launch camera_one_box one_box.launch.py hfov_deg:=90 rviz:=false
```

| Argument | Default | What it does |
| --- | --- | --- |
| `width` | 320 | pixels across |
| `height` | 240 | pixels down |
| `hfov_deg` | 60 | how wide the camera sees, in degrees. Try 90 for wide, or 30 for zoomed in |
| `rviz` | true | open RViz |
| `gui` | false | also open Gazebo's own window, which on macOS runs as a separate process |

The box locator has three parameters of its own, which can be set in the same
way with `--ros-args -p name:=value` when running it on its own:

| Parameter | Default | What it does |
| --- | --- | --- |
| `world_frame` | `world` | the frame the box is reported in |
| `table_z` | 0.0 | how high the table top is, in metres |
| `min_height` | 0.01 | how far above the table a point must be to count as the box, in metres |

### 1.3 Tests and recordings

The tests replay a capture that was recorded from Gazebo, so they run in about a
second and do not need the simulation. The first command runs every test in the
repository, and the second runs only this package's tests:

```
make test
pixi run bash -c 'source install/setup.bash && \
  colcon test --packages-select camera_one_box && colcon test-result --verbose'
```

That capture is a rosbag in `test/data/one_box`. To record a new one, start the
simulation, delete the old folder, and run `save_snapshot` in a second terminal.
It refuses to write over a folder that already exists, so it cannot delete a
recording by accident:

```
rm -r src/camera/camera_applied/camera_one_box/test/data/one_box
pixi run bash -c 'source install/setup.bash && \
  ros2 run camera_one_box save_snapshot src/camera/camera_applied/camera_one_box/test/data/one_box'
```

The pictures in the camera docs are drawn from captures of this simulation too.
After changing the world or the camera, record them again and redraw the
pictures:

```
pixi run python docs/diagrams/record_camera.py
pixi run python docs/diagrams/camera.py
```

## 2. The main Python files

The package has four Python files of its own, in `camera_one_box/`, and one
Python launch file. The node and the maths are kept in separate files on
purpose: the node only does ROS work, such as receiving messages and publishing
results, while all of the maths works on plain NumPy arrays, so it can be tested
without ROS or Gazebo.

**`box_locator.py`** is the node that does the job. It subscribes to the depth
picture and the camera info, and uses `message_filters` to take them in pairs
with matching timestamps, because a depth picture only means something next to
the lens that took it. For each pair it turns the picture into a NumPy array with
`cv_bridge`, reads the four lens numbers with `image_geometry`, and asks `tf2`
where the camera is. It then hands all of that to `measure.py`, and publishes the
answer twice: as a `vision_msgs/Detection3DArray` on `/detections`, which is what
a grasp planner would read, and as a cube on `/detection_markers`, which RViz
draws.

**`measure.py`** holds the maths, and has no ROS in it. It follows the four
steps in section 1 of the one-box intro, one function each:

| Function | What it does |
| --- | --- |
| `depth_to_points()` | turns every pixel and its depth reading into a point measured from the camera |
| `transform_matrix()` | turns the camera's transform from TF, a translation and a quaternion, into a 4 × 4 matrix |
| `to_world()` | moves points from the camera's axes into the room's, using that matrix |
| `measure_box()` | keeps the points standing on the table, keeps the highest of them, and averages them into the box's middle and height |

**`show_pixels.py`** is a small tool for looking at what the camera really
returns. It waits for one colour picture and one depth picture from the 80 × 60
basic camera, prints both in the terminal one coloured square per pixel, prints
the raw depth numbers for a small patch, and exits.

**`save_snapshot.py`** records one capture into a rosbag and exits. It waits for
a colour picture, a depth picture and a camera info with the same timestamp, and
writes them, together with the camera's static transforms, into an MCAP file.
Recording topics like this and replaying them later is how perception code is
usually developed and tested on real robots.

**`launch/one_box.launch.py`** starts everything together: robot_state_publisher
with the camera description, Gazebo with the world, `ros_gz_sim create` to add
the camera to the world, `ros_gz_bridge` to copy the camera's topics onto ROS,
depth_image_proc to build the point cloud, the box locator, and RViz. Section 4.1
of the one-box code doc draws how these pieces connect.

**`test/test_measure.py`** reads the recorded capture with the same libraries the
node uses, and checks that the lens, the camera's position, the depth readings
and the measured box all match the numbers in the docs.

## 3. Layout

```
src/camera/camera_applied/camera_one_box/
  README.md                          this file
  package.xml                        what the package needs from ROS
  setup.py, setup.cfg                how it is installed, and its three commands
  launch/
    one_box.launch.py                starts everything together
  urdf/
    camera.urdf.xacro                the camera on its stand, and its two sensors
  worlds/
    one_box.sdf                      the table, the box and a light, for Gazebo
    textures/table_grid.png          the 5 cm grid printed on the table
  config/
    bridge.yaml                      which Gazebo topics become which ROS topics
    one_box.rviz                     the saved RViz layout
  camera_one_box/
    box_locator.py                   the node: finds the box and publishes it
    measure.py                       the maths, with no ROS in it
    show_pixels.py                   prints every pixel of the basic camera
    save_snapshot.py                 records one capture into a rosbag
  resource/camera_one_box            an empty marker file ROS uses to find the package
  test/
    test_measure.py                  checks the maths on a recorded capture
    data/one_box/                    that capture, a rosbag in the MCAP format
```

The files that are not Python describe the setup rather than the behaviour, which
is why they can be changed without touching any code:

- **`urdf/camera.urdf.xacro`** says where the camera is and what it sees. It is
  written in xacro, which is URDF with variables. Its `<sensor>` blocks set each
  camera's resolution, field of view, update rate and depth range.
- **`worlds/one_box.sdf`** says what is in the world. Move or resize the box here,
  and the box locator measures the new one.
- **`config/bridge.yaml`** lists each topic that crosses from Gazebo to ROS, with
  its name and message type on each side.
