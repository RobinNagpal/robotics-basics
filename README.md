# robotics-basics

A minimal, reproducible **ROS 2 Jazzy + RViz2** workspace on macOS (Apple Silicon),
with dependencies managed by [pixi](https://pixi.sh).

The demo publishes a TF frame that orbits the origin, plus a marker attached to
that frame — the two mechanisms nearly every RViz visualisation is built on.

## Quick start

```bash
make demo
```

That resolves the environment (first run downloads ROS 2, a few GB), builds the
workspace, and opens RViz2 with a blue sphere circling the grid.

Run `make` on its own for the full list of targets.

## Available targets

Every target runs inside the pixi environment with the colcon overlay already
sourced — there is no `pixi shell` or `source install/setup.bash` step to
remember.

| Target | What it does |
| --- | --- |
| `make demo` | Build, then launch the node + RViz2 — start here |
| `make node` | Run only the marker publisher (no RViz) |
| `make rviz` | Run only RViz2 with the saved config |
| `make build` | `colcon build --symlink-install` |
| `make test` | Run the unit tests |
| `make lint` | Check code style with flake8 |
| `make doctor` | Print versions of everything that matters |
| `make setup` | Resolve/install the environment |
| `make clean` | Remove `build/`, `install/`, `log/` |
| `make shell` | Bash shell with ROS **and** the workspace overlay sourced |

With `make demo` running in another terminal, these inspect the live system:

| Target | What it does |
| --- | --- |
| `make topics` | List active topics |
| `make marker` | Print one marker message |
| `make tf` | Stream the `world -> marker_frame` transform |
| `make frames` | Snapshot the TF tree to a PDF and open it |
| `make graph` | Open `rqt_graph` to see nodes and topics |

The targets delegate to pixi tasks, so `pixi run demo`, `pixi run test` etc.
still work if you prefer. Anything not covered: `make shell`, then normal
`ros2 ...` commands.

## Layout

```
robotics-basics/
├── pixi.toml                  # dependency + task definitions
├── pixi.lock                  # exact resolved versions — commit this
└── src/
    └── rviz_basics/           # a standard ament_python package
        ├── package.xml        # ROS dependencies + build type
        ├── setup.py           # entry points and installed data files
        ├── rviz_basics/
        │   └── marker_publisher.py
        ├── launch/
        │   └── marker_demo.launch.py
        ├── rviz/
        │   └── marker_demo.rviz   # saved RViz display config
        └── test/
            └── test_marker_publisher.py
```

## How the demo works

```
world ──TF──▶ marker_frame        broadcast at 30 Hz
/visualization_marker             Marker, stamped in marker_frame
```

The marker sits at the *origin* of `marker_frame` and never moves in its own
frame. RViz animates it purely by resolving TF — the same mechanism that moves a
real robot's meshes, so this pattern scales up unchanged.

Tunable at launch, e.g. `pixi run demo` then override:

```bash
pixi run shell
ros2 launch rviz_basics marker_demo.launch.py orbit_period_s:=2.0 use_rviz:=false
```

Node parameters: `world_frame`, `marker_frame`, `publish_rate_hz`,
`orbit_radius_m`, `orbit_period_s`, `marker_diameter_m`.

## Extending it

**Add a node.** Drop `src/rviz_basics/rviz_basics/my_node.py`, then register it in
`setup.py`:

```python
entry_points={'console_scripts': [
    'marker_publisher = rviz_basics.marker_publisher:main',
    'my_node = rviz_basics.my_node:main',
]},
```

**Add a package.** Create `src/<pkg>/` with its own `package.xml` + `setup.py`;
`colcon build` picks it up automatically.

**Change the motion.** `circular_orbit()` in `marker_publisher.py` is a pure
function of `(elapsed, radius, period)` with no ROS types in its signature —
swap it for any trajectory and the node is unaffected. Its tests need no ROS
graph.

**Add a ROS dependency.** Add the conda package to `pixi.toml`
(`ros-jazzy-<name>`) *and* the ROS name to `package.xml`. The former installs it,
the latter records it for `rosdep`/downstream builds.

**Save an RViz layout.** Arrange RViz, then File → Save Config As over
`src/rviz_basics/rviz/marker_demo.rviz`.

## Environment notes

Pinned deliberately in `pixi.toml`; each of these breaks the build if loosened:

- **Python 3.12** — ROS 2 Jazzy's compiled extensions (`rclpy`) link against it.
  Not a free choice.
- **setuptools `<80`** — v80 removed the `develop` command that
  `colcon build --symlink-install` uses for `ament_python` packages.
- **pytest `<8`** — ROS 2 Jazzy's bundled `launch_testing` plugin still uses the
  `path` hook argument that pytest 8 removed; anything newer fails at plugin load.

`setup.py` declares `extras_require={'test': ['pytest']}` — colcon only selects
its pytest runner when it sees that, otherwise `colcon test` silently falls back
to unittest and collects nothing. (The older `tests_require=` spelling no longer
works: setuptools 72 removed it.)

ROS 2 packages come from the [RoboStack](https://robostack.github.io) conda
channel, which is what makes a native macOS ARM install possible — there are no
official ROS 2 binaries for macOS.

To reproduce the environment elsewhere, commit `pixi.toml` **and** `pixi.lock`,
then run `pixi install`. To target another OS, add it to `platforms` in
`pixi.toml`.
