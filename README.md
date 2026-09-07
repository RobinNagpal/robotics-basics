# robotics-basics

A ROS 2 Jazzy workspace for learning RViz, running natively on macOS.

One node publishes a coordinate frame that orbits the origin and a marker
attached to it, so RViz shows a blue sphere circling a grid.

![What you see in RViz](docs/images/overview/scene.svg)

```
make setup    # first run downloads ROS 2, a few GB
make demo     # build, then launch the node and RViz
```

Run `make` to see every target.

**[docs/overview.md](docs/overview.md)** explains how it fits together, what to
expect when you run it, and how to build on it.
