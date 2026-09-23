# Licences, platforms and the comparison grids

The cross-cutting document: what you are allowed to ship, what will run on your
machine, how it all fits into ROS 2, and every method in this area side by side.

It exists separately because these questions do not belong to reaching, or to
planning, or to controlling. They are the same questions whichever part you are
working on, and answering them three times is how the three quietly drift apart.

Every licence below was read from the project's own LICENSE file or package
manifest, fetched in September 2026, and never from a badge or a blog. Every
link was checked. Where code and weights differ, both are named.

If you read one section, read section 1. The default inverse kinematics solver in
the main open-source motion planning framework is LGPL, not BSD, and almost
nothing says so.

## Contents

1. [Licences, and the four that will catch you out](#1-licences-and-the-four-that-will-catch-you-out)
2. [The libraries, and what state each is in](#2-the-libraries-and-what-state-each-is-in)
3. [What runs on an Apple Silicon Mac](#3-what-runs-on-an-apple-silicon-mac)
4. [ROS 2: distributions, packages and versions](#4-ros-2-distributions-packages-and-versions)
5. [The comparison grids](#5-the-comparison-grids)

---

## 1. Licences, and the four that will catch you out

The good news first. **The core of this area is permissive and clean.** MoveIt 2,
OMPL, the Pilz industrial motion planner, MoveIt Task Constructor, moveit_servo,
TRAC-IK, pick_ik and bio_ik are all BSD-3. ros2_control, ros2_controllers, the
admittance controller and the motion primitives controller are all Apache-2.0.
Pinocchio is BSD-2, Drake is BSD-3, and — the one that surprises people — cuRobo
is Apache-2.0, despite being NVIDIA research code, which is usually not.

Four things are not clean, and each catches people in a different way.

### 1.1 MoveIt's default IK solver is LGPL-2.1

**KDL, the Kinematics and Dynamics Library, is LGPL-2.1.** GitHub's licence
detector does not identify it, because the licence text lives in
`orocos_kdl/COPYING` rather than at the repository root, so the repository shows
no licence at all in the usual places. The file itself is the GNU Lesser General
Public License, version 2.1.

KDL is MoveIt's default kinematics plugin, so a very large number of ROS arm
projects have LGPL code in the path between "here is a pose" and "here are the
joint angles" without anyone having decided that. The LGPL is much weaker than
the GPL and dynamic linking is the case it was written to permit, so for most
people this is a thing to know rather than a thing to fix. It is worth knowing
because the assumption in the room is invariably "MoveIt is BSD, so this is BSD",
and that assumption is wrong about one specific component.

If it matters, the replacements are permissive and better:
[TRAC-IK](https://github.com/traclabs/trac_ik) and
[pick_ik](https://github.com/PickNikRobotics/pick_ik) are both BSD-3.

### 1.2 ViSP, the visual servoing library, is GPL-2.0 or later

[ViSP](https://github.com/lagadic/visp) is the reference implementation of visual
servoing, it is actively maintained, and its LICENSE.txt is the GNU General
Public License version 2 or later. The ROS wrapper
[vision_visp](https://github.com/lagadic/vision_visp) is the same code.

Visual servoing is a small enough corner that there is no permissive equivalent
of comparable depth, so the practical positions are to use it and accept the
obligation, to write the specific controller you need yourself — image-based
servoing on a known feature is not a large piece of code — or to buy it.

### 1.3 Ruckig is MIT and calls a cloud API

[Ruckig](https://github.com/pantor/ruckig) is MIT, and this is not a licence
problem. It is a deployment problem hiding behind a licence that looks settled.

Ruckig's own README states that the Community Version supports intermediate
waypoints using a cloud API for remote calculation, that it switches to that
cloud API as soon as intermediate positions are given, and that this path is not
real-time capable. Local calculation of intermediate waypoints is a Pro feature,
as are position limits and interrupting a calculation.

A trajectory generator that makes a network call is worth knowing about before it
is in a control loop. **MoveIt is not in that case** — its Ruckig use smooths an
existing waypoint sequence rather than supplying intermediate positions — and
anyone calling Ruckig directly with `intermediate_positions` is.

### 1.4 Isaac ROS cuMotion is proprietary, and cuRobo is not

This is the same trap the
[perception area found in Isaac ROS](../06_object-perception/06_licences-and-platforms.md#4-putting-it-in-ros-2),
in a different package, and it is worth restating because the two halves point
opposite ways.

[cuRobo](https://github.com/NVlabs/curobo) itself is Apache-2.0, read from its
LICENSE file. The ROS 2 packaging of it,
`isaac_ros_cumotion`, declares `NVIDIA Isaac ROS Software License` in its own
`package.xml`. That is NVIDIA's proprietary licence, not an open one, and
GitHub's detector reports the repository as having no recognised licence.

So the library is permissive and the convenient way to use it from ROS is not.
Both also require CUDA, so neither runs here at all.

### 1.5 The patterns worth recognising

- **Code permissive, weights not.** GR00T N1.5's repository is Apache-2.0 and its
  weights are under the NVIDIA One Way Noncommercial License, with the model card
  stating the model is ready for non-commercial use.
- **No licence is worse than a restrictive one.** openpi's repository is
  Apache-2.0 and its checkpoints ship from a Google Cloud Storage bucket with no
  stated terms. Absent a statement, nothing is granted.
- **A licence file at the root need not describe the whole repository.** Tesseract
  ships a LICENSE that says the package contains Apache-2.0, BSD-2 and BSD-3 code,
  each file marked at the top. It has to be read per file.
- **GitHub's detector is not the licence.** It misses KDL entirely and reports
  Isaac ROS cuMotion as unlicensed. Fetch the file.

## 2. The libraries, and what state each is in

Read these as: what it is, what its licence is, and what state it is in, verified
by its last push in September 2026. A stale library is a slow problem rather than
an obvious one.

### 2.1 Planning

These are the libraries that decide a route. MoveIt is the framework and the
others are either plugins inside it or alternatives to it.

| Library | Licence | State |
| --- | --- | --- |
| [MoveIt 2](https://github.com/moveit/moveit2) | BSD-3 | very active, pushed daily. 2.0k stars |
| [OMPL](https://github.com/ompl/ompl) | BSD-3 | active. The sampling planners underneath MoveIt |
| [Pilz industrial motion planner](https://github.com/moveit/moveit2/tree/main/moveit_planners/pilz_industrial_motion_planner) | BSD-3 | inside MoveIt. PTP, LIN and CIRC, plus a sequence action |
| [CHOMP](https://github.com/moveit/moveit2/tree/main/moveit_planners/chomp) and [STOMP](https://github.com/moveit/moveit2/tree/main/moveit_planners/stomp) | BSD-3 | inside MoveIt. The optimisation-based plugins |
| [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | BSD-3 | maintained, pushed September 2026. 287 stars, which is a fair measure of how widely the idea has been taken up |
| [Tesseract](https://github.com/tesseract-robotics/tesseract) and [tesseract_planning](https://github.com/tesseract-robotics/tesseract_planning) | mixed Apache-2.0, BSD-2, BSD-3, marked per file | active. The maintained TrajOpt lives here |
| [cuRobo](https://github.com/NVlabs/curobo) | Apache-2.0 | active. CUDA only |
| [MPlib](https://github.com/haosulab/MPlib) | MIT | a lightweight planner outside ROS; last pushed May 2026 |

### 2.2 Kinematics and trajectories

These turn poses into joint angles, and paths into timed trajectories. The first
row is the licence trap from section 1.1.

| Library | Licence | State |
| --- | --- | --- |
| [KDL](https://github.com/orocos/orocos_kinematics_dynamics) | **LGPL-2.1**, in `orocos_kdl/COPYING` | active. MoveIt's default IK |
| [TRAC-IK](https://github.com/traclabs/trac_ik) | BSD-3 | stable; last pushed June 2026. Exists because KDL fails on poses that have solutions |
| [pick_ik](https://github.com/PickNikRobotics/pick_ik) | BSD-3 | active. The modern MoveIt IK plugin |
| [bio_ik](https://github.com/TAMS-Group/bio_ik) | BSD-3 | quiet; last pushed February 2025 |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | BSD-2 | very active, 3.7k stars. Kinematics and dynamics from a URDF |
| [Ruckig](https://github.com/pantor/ruckig) | MIT, with the cloud caveat in section 1.3 | very active |
| [TOPP-RA](https://github.com/hungpham2511/toppra) | MIT | maintained; last pushed August 2026 |
| [Drake](https://github.com/RobotLocomotion/drake) | BSD-3 | very active, 4.2k stars. Modelling, optimisation and control |

### 2.3 Control

These execute the motion and decide what happens on contact. The ViSP row is the
licence trap from section 1.2.

| Library | Licence | State |
| --- | --- | --- |
| [ros2_control](https://github.com/ros-controls/ros2_control) | Apache-2.0 | very active |
| [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | very active. Contains `joint_trajectory_controller`, `admittance_controller` and the new `motion_primitives_controllers` |
| [moveit_servo](https://github.com/moveit/moveit2/tree/main/moveit_ros/moveit_servo) | BSD-3 | inside MoveIt. Real-time Cartesian jogging |
| [FZI cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | BSD-3 | **stale**: last pushed October 2024 |
| [ViSP](https://github.com/lagadic/visp) | **GPL-2.0 or later** | very active |
| [acados](https://github.com/acados/acados) | BSD-2 | very active. Embedded MPC |
| [OCS2](https://github.com/leggedrobotics/ocs2) | BSD-3 | active |
| [Crocoddyl](https://github.com/loco-3d/crocoddyl) | BSD-3 | active |
| [MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc) | Apache-2.0 | active. The best way to develop an intuition for MPC |

### 2.4 Reachability

There are only two tools worth naming and both are quiet, which is itself the
finding: reachability analysis has no healthy open-source ecosystem.

| Tool | Licence | State |
| --- | --- | --- |
| [reach](https://github.com/ros-industrial/reach) | Apache-2.0 | last pushed March 2025. The maintained option |
| [Reuleaux](https://github.com/ros-industrial-consortium/reuleaux) | **none at all** — no licence file in the repository | **in ROS-Industrial's attic**, last pushed July 2024. Papers still cite it; do not build on it |

### 2.5 Learned motion

Every one of these is covered with its weights licence in
[section 2 of learned motion](05_learned-motion.md#2-policies-you-can-download).
The short version: [LeRobot](https://github.com/huggingface/lerobot) is
Apache-2.0 and is where the ecosystem now lives; ACT, Diffusion Policy, Octo,
OpenVLA, RDT-1B and Motion Policy Networks are MIT; openpi's code is Apache-2.0
and its weights are unstated; GR00T N1.5's code is Apache-2.0 and its weights are
non-commercial.

## 3. What runs on an Apple Silicon Mac

The headline is better than its reputation, and it is not documented anywhere
obvious, so this section is the result of checking rather than of reading.

**ROS 2 has no official Apple Silicon support at all.** In REP-2000, which
defines the target platforms for every distribution, macOS appears only in the
`amd64` row at tier 3, for both Jazzy and Kilted. The `arm64` row has no macOS
cell. This is the same finding
[the perception area reports](../06_object-perception/06_licences-and-platforms.md#3-what-runs-on-an-apple-silicon-mac),
and the practical route is the same: [RoboStack](https://robostack.github.io/), a
community conda redistribution, which is what this repository uses.

**And through RoboStack, nearly the whole motion stack is there.** Checked
against the `robostack-jazzy` channel: `ros-jazzy-moveit` 2.12.4,
`ros-jazzy-moveit-py`, `ros-jazzy-moveit-servo`, `ros-jazzy-ompl`,
`ros-jazzy-pilz-industrial-motion-planner`,
`ros-jazzy-moveit-task-constructor-core`, `ros-jazzy-ros2-control` 4.47.0,
`ros-jazzy-ros2-controllers` 4.42.1, `ros-jazzy-ur-robot-driver`,
`ros-jazzy-octomap`, `ros-jazzy-behaviortree-cpp` and `ros-jazzy-py-trees` all
publish an `osx-arm64` build. So planning, Cartesian servoing, industrial motion
primitives, task construction and control all run on the Mac, which is more than
most people assume.

The table below is what works against what does not. Read the right column as
the list of things to plan around rather than to fight.

| Works on Apple Silicon | Does not |
| --- | --- |
| MoveIt 2, OMPL, Pilz, MoveIt Task Constructor, moveit_servo, via RoboStack | cuRobo, entirely — it is built on CUDA and has no CPU path |
| ros2_control and ros2_controllers, via RoboStack | Isaac ROS cuMotion, which needs CUDA and is proprietary besides |
| Pinocchio, from conda-forge and from a `macosx_11_0_arm64` PyPI wheel | Isaac Lab, which needs Isaac Sim and an NVIDIA card |
| MuJoCo and MuJoCo MPC, natively | openpi, whose README states an NVIDIA GPU requirement and that only Ubuntu 22.04 is supported |
| Drake, from a `macosx_15_0_arm64` wheel — note it requires macOS 15 | TOPP-RA, which publishes no macOS wheel at all; build from source |
| Ruckig, from a `macosx_11_0_arm64` wheel | `ros-jazzy-visp` and `ros-jazzy-vision-visp`, which RoboStack does not build |
| ViSP itself, from conda-forge with an `osx-arm64` build | acados, which is not on conda-forge and needs building |
| LeRobot, which selects `mps` automatically when Metal is available | large-scale policy fine-tuning, which needs 22 GB or more of GPU memory |
| Stable-Baselines3 and robosuite, since MuJoCo is native | the accelerated paths in MuJoCo Playground and Genesis |

Two of those deserve a sentence rather than a cell.

**LeRobot's Apple Silicon support is in the code, not merely in the README.** Its
device selection tries CUDA, then `torch.backends.mps`, and returns
`torch.device("mps")` when Metal is available. Training a small policy and
running inference both work on a Mac.

**The ViSP split is the awkward one.** The library has an `osx-arm64` build on
conda-forge, and the ROS wrapper has no RoboStack build. So visual servoing on a
Mac means calling ViSP directly rather than through ROS, and the GPL obligation
from section 1.2 comes with it.

## 4. ROS 2: distributions, packages and versions

ROS 2's current release is **Lyrical**, from May 2026;
[ros2_controllers carries a `ros2_controllers.lyrical.repos`](https://github.com/ros-controls/ros2_controllers)
alongside its Jazzy and Kilted files. **Jazzy Jalisco** runs from May 2024 to May
2029 and is the safer choice today, which is what this repository uses.
**Kilted Kaiju** ends in November 2026, so starting on it now is starting on
something with two months left. Those dates are from
[REP-2000](https://github.com/ros-infrastructure/rep/blob/master/rep-2000.rst),
and the distribution list is in
[rosdistro](https://github.com/ros/rosdistro).

The packages that matter for motion, with the licence of each:

| Package | Licence | What it is for |
| --- | --- | --- |
| `moveit` | BSD-3 | planning, IK, collision checking, the planning scene |
| `moveit_servo` | BSD-3 | real-time Cartesian and joint jogging |
| `moveit_task_constructor` | BSD-3 | planning a task as stages rather than as steps |
| `pilz_industrial_motion_planner` | BSD-3 | PTP, LIN, CIRC and blended sequences |
| `ros2_control` | Apache-2.0 | the control loop and the hardware interface |
| `joint_trajectory_controller` | Apache-2.0 | executing a planner's trajectory — read section 3 of [controlling the move](04_controlling-the-move.md#3-what-the-move-failed-actually-means) before trusting its defaults |
| `admittance_controller` | Apache-2.0 | the one contact controller the open stack ships |
| `motion_primitives_controllers` | Apache-2.0 | sending PTP, LIN and CIRC to the vendor's own controller |
| `force_torque_sensor_broadcaster` | Apache-2.0 | publishing the wrist sensor |
| `octomap` | BSD, declared in its `package.xml`; there is no root LICENSE file | the occupancy map MoveIt uses for unknown obstacles |
| `ur_robot_driver` | BSD-3 | the Universal Robots driver, with an `osx-arm64` RoboStack build |
| `franka_ros2` | Apache-2.0 | the Franka driver. Its example controllers include joint and Cartesian impedance, which is the practical route to compliance on that arm |
| `isaac_ros_cumotion` | **NVIDIA Isaac ROS Software License** | GPU planning — proprietary, see section 1.4 |

One thing worth stating because it is a category error people make. **MoveIt's
perception pipeline builds an octomap so the planner can avoid unknown obstacles.
It is not a measuring tool and was never meant to be.** The
[perception area says the same thing](../06_object-perception/06_licences-and-platforms.md#41-packages-for-measuring),
and the mistake in this direction is the mirror image: using the octomap as the
model of the part you are about to grasp, rather than as the model of the things
you must not hit.

## 5. The comparison grids

Everything in one place.

### 5.1 The five kinds of move

Read this as a decision table: the four middle columns are what each kind of move
demands of you, and the last says where it is covered properly.

| Kind | Deterministic | Needs a world model | Needs force sensing | Needs a fast sensor loop | Where it is covered |
| --- | --- | --- | --- | --- | --- |
| free move | no, for samplers; yes, for optimisers | yes | no | no | [planning, sections 2 and 3](03_planning-a-path.md#2-sampling-based-planners) |
| straight line | yes | only if you check collisions | no | no | [planning, section 5](03_planning-a-path.md#5-cartesian-paths-and-what-they-are-not) |
| guarded | yes | no | yes | no | [control, section 5](04_controlling-the-move.md#5-guarded-moves-and-what-the-sensor-can-actually-observe) |
| compliant | yes | no | yes, or joint torque | no | [control, section 4](04_controlling-the-move.md#4-position-stiffness-and-force) |
| servoed | no | no | no | yes, 30 Hz or better | [control, section 6](04_controlling-the-move.md#6-visual-servoing) |

### 5.2 Choosing a planner

Speed is an order of magnitude on ordinary hardware rather than a benchmark
figure, because the benchmark figure depends on a card you probably do not have.

| Approach | Same answer every run | Finds awkward routes | Path quality | Typical time | Licence |
| --- | --- | --- | --- | --- | --- |
| RRT-Connect | no | very good | poor, needs smoothing | tens of ms, with a long tail | BSD-3 |
| RRT\* and PRM\* | no | very good | improves with time | hundreds of ms | BSD-3 |
| CHOMP, STOMP | yes | poor — local minima | good | tens to hundreds of ms | BSD-3 |
| TrajOpt | yes | moderate | very good | tens of ms | mixed, marked per file |
| Pilz PTP, LIN, CIRC | yes | none — it does not search | exactly what you specified | sub-millisecond | BSD-3 |
| Cartesian interpolation | yes | none | a line, or part of one | milliseconds | BSD-3 |
| cuRobo | close to, with a warm start | good | very good | around a millisecond | Apache-2.0, **CUDA only** |
| a learned motion policy | no | as good as its training set | good | fixed, and small | MIT for Motion Policy Networks |

### 5.3 Choosing a controller

Read this as: what you hand the controller, what hardware that needs, and what it
is for. The licence column is the one that decides whether you may ship it.

| Approach | What you command | Needs | Suits | Licence |
| --- | --- | --- | --- | --- |
| joint trajectory | joint positions over time | nothing extra | executing a plan | Apache-2.0 |
| Cartesian motion | a tool pose or twist | a Jacobian, and singularity handling | straight lines, jogging, servoing | BSD-3 |
| admittance | a stiffness, measured through a sensor | a wrist force-torque sensor | insertion, hand guiding, contact on a position-controlled arm | Apache-2.0 |
| impedance | a stiffness, at the joint | joint torque sensing or control | fast contact, on arms that support it | vendor, or Apache-2.0 via `franka_ros2` |
| explicit force | a force along chosen axes | a sensor, or a compliant flange | polishing, deburring, pressing | vendor, mostly |
| visual servo | a target in image or pose terms | 30 Hz perception | aligning to something that moved | **GPL-2.0** for ViSP |
| model predictive | a cost and constraints over a horizon | a dynamics model and a solver | constraints over time, moving targets | BSD-2 or BSD-3 |
| a learned policy | nothing — it emits the command | a dataset, and a controller underneath | contact and appearance-driven tasks | MIT to non-commercial; check the weights |

### 5.4 The silent failures, in one place

Every failure in this area that produces no error message, with the setting or
the assumption it hides behind and the section that works it out.

| The failure | Where it hides | Covered in |
| --- | --- | --- |
| a straight line whose ends are reachable and whose middle is not | nothing checks the path, only the poses | [reaching, section 2](02_reaching-and-reachability.md#2-the-workspace-and-its-holes) |
| "unreachable" meaning "not found in 50 ms" | `kinematics_solver_timeout`, default 0.05 | [reaching, section 8.1](02_reaching-and-reachability.md#81-the-solvers-answer-is-weaker-than-it-looks) |
| joint limits narrowed in the description file | the UR5e elbow, halved on purpose | [reaching, section 4](02_reaching-and-reachability.md#4-joint-limits-and-the-range-that-is-not-there) |
| an early grasp choice making a later place impossible | each step plans successfully | [reaching, section 5](02_reaching-and-reachability.md#5-configurations-the-eight-ways-to-reach-the-same-pose) |
| a partial Cartesian path executed as if complete | the returned fraction, ignored | [planning, section 5](03_planning-a-path.md#5-cartesian-paths-and-what-they-are-not) |
| zero collision padding | `default_robot_padding`, default 0.0 | [planning, section 7.1](03_planning-a-path.md#71-the-default-clearance-is-zero) |
| a path through a thin obstacle | `longest_valid_segment_fraction`, default 0.01 | [planning, section 7.2](03_planning-a-path.md#72-collisions-are-checked-at-sampled-points-not-continuously) |
| a held object not attached to the arm model | nothing reports it | [planning, section 7.3](03_planning-a-path.md#73-the-object-in-the-gripper-is-part-of-the-arm) |
| a trajectory controller that checks nothing | `constraints.trajectory` and `constraints.goal`, both 0.0 | [control, section 3](04_controlling-the-move.md#3-what-the-move-failed-actually-means) |
| a guarded move on a sensor that cannot see the event | the arm simply keeps going | [control, section 5](04_controlling-the-move.md#5-guarded-moves-and-what-the-sensor-can-actually-observe) |
| a real-time library making a network call | Ruckig's intermediate waypoints | [section 1.3](#13-ruckig-is-mit-and-calls-a-cloud-api) |
| weights licensed differently from the code | GR00T N1.5, openpi | [learned motion, section 2.1](05_learned-motion.md#21-the-two-licence-traps) |

Back to [the overview](01_overview.md).
