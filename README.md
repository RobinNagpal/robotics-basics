# robotics-basics

A ROS 2 Jazzy workspace for learning RViz, running natively on macOS.

The demo publishes a TF frame that orbits the origin, plus a marker attached to
that frame. In RViz you see a sphere circling a grid. The marker never moves in
its own frame — RViz animates it by resolving TF, which is how a real robot's
meshes move.

Dependencies are managed by [pixi](https://pixi.sh). Nothing is installed
system-wide; everything lives in `.pixi/` inside this directory.

## Setup

```
make setup
```

First run downloads ROS 2, a few GB.

## Commands

Run `make` to see all targets. The ones that matter:

```
make demo      build, then launch the node and RViz together
make build     rebuild after changing code
make test      run the unit tests
make lint      check code style
make shell     shell with ROS sourced, for plain ros2 commands
```

With `make demo` running, from another terminal:

```
make topics    list active topics
make marker    print one marker message
make tf        stream the world -> marker_frame transform
make frames    save the TF tree as a PDF
make graph     open rqt_graph
```

## Layout

```
pixi.toml                              dependencies and tasks
Makefile                               entry point for everything
src/rviz_basics/
  rviz_basics/marker_publisher.py      the node
  launch/marker_demo.launch.py         starts the node and RViz
  rviz/marker_demo.rviz                saved RViz layout
  test/                                unit tests
```

## Adding to it

**A node:** add the module under `rviz_basics/`, register it in `setup.py`
under `console_scripts`, then `make build`.

**A package:** create `src/<name>/` with its own `package.xml` and `setup.py`.
`make build` finds it automatically.

**A ROS dependency:** add `ros-jazzy-<name>` to `pixi.toml` and the plain name
to `package.xml`.

**A different motion:** `circular_orbit()` in `marker_publisher.py` is a plain
function of time, radius and period, with no ROS types in it. Replace it and
nothing else changes.

## Notes

Python 3.12, setuptools `<80` and pytest `<8` are pinned on purpose. Each one
breaks the build if loosened — the reasons are in `pixi.toml`.

ROS 2 packages come from [RoboStack](https://robostack.github.io), because
there are no official ROS 2 binaries for macOS.

Closing the `make graph` window prints a non-zero exit warning. That is an rqt
bug on macOS, not a problem here.

Commit `pixi.lock` — it is what makes the environment reproducible.
