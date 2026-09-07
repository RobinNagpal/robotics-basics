# robotics-basics

A small project for learning RViz on a Mac.

A blue ball moves in a circle. That is all it does. The point is to show how
ROS keeps track of where things are, and how RViz draws them.

ROS is the Robot Operating System, a set of libraries and tools for writing
robot software. RViz, short for ROS Visualization, is the 3D viewer that comes
with it. This project uses ROS 2, the current version.

![What you see in RViz](docs/images/overview/scene.svg)

```
make setup    # the first run downloads ROS 2, a few gigabytes
make demo     # build, then start the node and RViz
```

Run `make` on its own to see every command.

**[docs/overview.md](docs/overview.md)** explains what the parts are, what to
expect when you run it, and how to add to it. It starts from the basics, so you
do not need to know ROS already.
