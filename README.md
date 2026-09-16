# robotics-basics

Small, runnable examples for learning robotics with ROS 2 on a Mac.

ROS is the Robot Operating System, a set of libraries and tools for writing
robot software. RViz, short for ROS Visualization, is the 3D viewer that comes
with it. This project uses ROS 2, the current version.

```
make setup    # the first run downloads ROS 2, a few gigabytes
make          # list everything you can run
```

## Areas

The repo is split into areas. Each one is a topic you can work through on its
own, with its own code, its own doc, and two or three commands.

| Area | What it covers | Start with |
| --- | --- | --- |
| [ros](docs/ros/ros-intro.md) | the basics of ROS, one program per idea, then a camera, an arm, and the two together | `make ros.basics` |
| [rviz](docs/rviz/overview.md) | markers, frames and the 3D viewer | `make rviz.demo` |
| [arm](docs/arm/overview.md) | position, frames and transforms | `make arm.learn` |
| [camera](docs/camera/basics.md) | how a camera works, then a depth camera in Gazebo that finds a box | `make camera.one_box` |
| [numpy](docs/numpy/numpy-intro.md) | the parts of NumPy robotics code uses most: arrays, masks, transforms, grids | `make numpy.learn` |
| [finding objects](docs/camera/finding-objects.md) | finding a thing in a picture: by colour, with depth, and with a trained model | `make camera.colour` |

<p align="center">
  <img src="docs/images/rviz/scene.svg" width="31%" alt="A ball circling a grid in RViz">
  <img src="docs/images/arm/arm.svg" width="31%" alt="A two-joint arm and its frames">
  <img src="docs/images/camera/basics/pinhole.svg" width="31%" alt="A pixel is a direction, not a place">
</p>

New to this? Start with **ros**, which explains what ROS is: first one small
program for each thing ROS does — a node, a topic, a parameter, a service, an
action, a frame, a launch file — and then three worked examples, one that works
with a camera, one that moves an arm, and one that uses both. Then **rviz**, which shows you what
you are looking at before the arm area explains the maths behind it. Then
**arm**, then **camera**, which uses that maths to turn a picture into points.
The camera code is mostly NumPy, so if NumPy is new to you, read **numpy** before
**camera**; it needs no ROS, and each of its five files runs on its own.

## Beyond the areas

**[Tools and libraries](docs/tools-and-libraries.md)** is a map of the main
tools used with arms mounted on a table: ROS 2, URDF, MoveIt, ros2_control,
simulators, perception, calibration and more. For each it explains the job it
does, then shows pseudo code and a few lines of real code. Read it after the
areas, when you want to know what to reach for next.

## Layout

```
Makefile              every command
pixi.toml             what to install
docs/<area>/          the doc for each area
docs/images/<area>/   its pictures
docs/diagrams/        the scripts that draw them
src/                  the code for each area:
  ros/ros_basics/       one small program for each thing ROS is used for
  ros/ros_applied/      the three worked ROS examples, one package each
  camera/camera_basics/    finding an object by colour, by depth, and with a model
  camera/camera_applied/   the Gazebo depth camera that finds and measures a box
  numpy/                five plain Python files, not a ROS package
  rviz_basics/          a marker in a moving frame
  arm_transforms/       position, frames and transforms, in five steps
```

## Repo-wide commands

```
make build     rebuild everything
make test      run every test
make lint      check code style
make shell     a shell with ROS ready, for typing ros2 commands
make doctor    print versions of everything that matters
```
