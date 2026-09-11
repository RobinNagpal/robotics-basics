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
| [rviz](docs/rviz/overview.md) | markers, frames and the 3D viewer | `make rviz.demo` |
| [arm](docs/arm/overview.md) | position, frames and transforms | `make arm.learn` |
| [camera](docs/camera/overview.md) | lenses, pictures and the points inside them | `make camera.learn` |

<p align="center">
  <img src="docs/images/rviz/scene.svg" width="31%" alt="A ball circling a grid in RViz">
  <img src="docs/images/arm/arm.svg" width="31%" alt="A two-joint arm and its frames">
  <img src="docs/images/camera/pinhole.svg" width="31%" alt="A pixel is a direction, not a place">
</p>

New to this? Start with **rviz**. It is the easiest of the three, and it shows
you what you are looking at before the arm area explains the maths behind it.
Then **arm**, then **camera**, which uses that maths to turn a picture into
points.

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
src/<package>/        the code for each area
```

## Repo-wide commands

```
make build     rebuild everything
make test      run every test
make lint      check code style
make shell     a shell with ROS ready, for typing ros2 commands
make doctor    print versions of everything that matters
```
