# Case study: standing an empty glass upside down on a drying rack

This document takes one household job and says how it would actually be built: which
part of it is a planner, which part is a model, which part is a force loop, and which
named tool does each one.

The job is this. Glasses are standing on a table. The robot has to pick up the empty
ones, turn each through 180 degrees, and stand it mouth-down on a drying rack — the
ordinary kitchen kind with a flat base and vertical pegs standing up from it. The
glasses that still have water in them must be left alone.

It sounds trivial and the moving part of it is trivial. Everything hard about it
comes from the object. The glass is transparent, so a depth camera cannot see it. It
has to be turned completely over, which most arms cannot do from an arbitrary
starting pose. It breaks if squeezed. And a glass with water in it must be spotted
before the turn, because after the turn the water is on the floor.

This is for somebody who has read [the overview](../01_overview.md) and wants the
method choices in it applied to one concrete problem. It is a design document, not
code. [The glossary](../06_glossary.md) has the longer explanation of any term.

## Contents

1. [The task](#1-the-task)
2. [What makes it hard](#2-what-makes-it-hard)
3. [The four versions](#3-the-four-versions)
4. [Which part uses what](#4-which-part-uses-what)
5. [When a new glass turns up](#5-when-a-new-glass-turns-up)
6. [What will bite you](#6-what-will-bite-you)
7. [What to measure](#7-what-to-measure)
8. [Where to go next](#8-where-to-go-next)

---

## 1. The task

The sequence, in the order it happens:

1. Find the glasses on the table, and find the rack.
2. Decide which ones are empty.
3. Choose a free peg.
4. Grasp an empty glass and lift it clear.
5. Confirm it is empty.
6. Turn it 180 degrees, so the mouth points down.
7. Lower it over the peg until the rim reaches the rack base.
8. Let go.
9. Check that it is standing.

Every number below comes from one example setup, which is also what the pictures are
drawn to. Measure your own before using any of them.

| Thing | Number |
| --- | --- |
| Glass rim, outside and inside | 70 mm and 64 mm |
| Glass height, wall thickness | 120 mm, 3 mm |
| Glass mass, empty and full | 220 g and 564 g |
| Peg diameter, peg height | 12 mm, 100 mm |
| Pegs on the rack, spacing | 6 in two rows of three, 90 mm apart |

The arm is an ordinary six-axis arm bolted to the table, with a repeatability of
around a tenth of a millimetre. Saying that early saves wasted effort: nothing here
fails because the arm cannot hit a position accurately enough.

An attempt succeeds when the glass is mouth-down on a peg, still standing ten seconds
later, with no neighbour moved and nothing broken. A full glass left untouched is
also a success. Water anywhere is a failure, however the run ended.

---

## 2. What makes it hard

Five things, each solved by a different part of the system.

### The depth camera cannot see it

A depth camera, meaning one that reports a distance for every pixel, sends light out
and measures what comes back. Most of that light goes straight through a glass, and
what does not is bent sideways by the curved wall. The depth picture therefore has a
hole exactly where the glass is.

![Why a depth camera returns a hole where the glass is](../../images/one-arm-training/case-study/place-glass/why-depth-fails.svg)

The ordinary camera picture still shows the glass, in its edges and its highlights.
So the outline comes from a segmentation model run on that picture, and depth is
demoted to two jobs it can still do: measuring the table plane, and confirming a
result the model has already produced.

### A glass with water in it must be caught before the turn

There are two signals and they are worth using in order. Looking for a water line in
the picture is cheap and can be done before the arm touches anything. Weighing is
certain but only available after the lift, because the arm is the scales.

![Both checks for water come before the turn](../../images/one-arm-training/case-study/place-glass/empty-or-full.svg)

Weighing means reading the payload from the joint torques, or from a wrist force
sensor, with the glass lifted clear. The margin is large — 220 g against 564 g — so
the threshold is not delicate. Set it low, at around 260 g, so that a glass with a
mouthful left in it is still refused.

### The turn has to be planned backwards

Turning the glass over is 180 degrees about a horizontal line. The last joint of most
arms has a limited range, commonly plus or minus 175 degrees, and 180 degrees of turn
does not fit into that if you start in the middle of it.

![Where in the wrist's range the turn starts decides whether it finishes](../../images/one-arm-training/case-study/place-glass/wrist-budget.svg)

The fix is to turn the wrist back before closing the fingers. That means the grasp
has to already know the release orientation, which is the thing most people get wrong
the first time: they write a grasp, then a turn, and find the turn impossible.

### The tolerance is not where you would guess

Getting a 64 mm glass over a 12 mm peg allows 26 mm of sideways error. The real
constraint is the rack filling up.

![The peg is easy to hit; the glasses already on the rack are not](../../images/one-arm-training/case-study/place-glass/rack-clearance.svg)

Pegs 90 mm apart and glasses 70 mm across leave 10 mm each side. Because the glass is
tall, orientation spends that budget faster than position does: a 5-degree tilt swings
the far end 10.5 mm sideways. So the descent must be vertical, and holding the glass
upright matters more than placing it exactly.

### Squeezing it wrong breaks it, once

There is a band of grip force that works. Below it the glass slips; above it the rim
cracks. The upper edge belongs to the glass and cannot be moved. The lower edge can,
by using fingers with more friction, and that is the only lever there is.

![The grip force window, and what widens it](../../images/one-arm-training/case-study/place-glass/grip-window.svg)

Wet glass, which is what comes out of a sink, pushes the lower edge up and narrows the
band further.

---

## 3. The four versions

Build it four times, the way [the learning path](../04_learning-path.md) does. Each
version removes one assumption from the one before, and each is a system you can run
and measure on its own. The rule worth keeping is that you do not start the next
version until the current one fails for a reason you can state out loud.

### Version 1: everything known in advance

**Assumes:** the glass always starts on a marked spot, every glass is the same, a
person puts out only empty ones, and the rack was measured once and has not moved.

**What it is:** a fixed sequence, with two of its steps controlled by force rather
than by position.

```
for peg in pegs:                          # measured once, in fill order
    move_to(pickup, wrist = -90°)         # pre-turned, so the flip will fit
    close_gripper(force = grip_force)
    if gripper_width > 68 mm: stop("no glass")
    lift(); turn_wrist(to = +90°)         # the glass is now mouth down
    move_above(peg, clearance = 130 mm)
    descend_until(vertical_force > 2 N)   # the rim has met the base
    open_slowly(); retreat(); check_standing()
```

**Stack:** ROS 2, the Robot Operating System, with URDF, the Unified Robot
Description Format, to describe the arm; MoveIt 2 for the moves; ros2_control with an
admittance controller for the descent.

**Buys you:** a complete working loop in days, a cycle time you can measure, and a rig
to test everything that follows. **Cannot do:** anything if the glass moves, the rack
moves, or somebody puts out a full one.

### Version 2: the glass can be anywhere, and it might be full

**Adds perception.** An overhead camera finds every glass and classifies each one as
empty or full; the wrist camera checks the last stretch of the approach; the lift
confirms the weight before the turn.

**Stack, on top of version 1:** a YOLO segmentation model — You Only Look Once, a fast
network that outlines objects in a picture — trained on two classes, empty glass and
full glass; Open3D to fit a cylinder to each outline against the measured table plane;
an AprilTag fiducial marker on the rack base to locate it; BehaviorTree.CPP for the
sequencing, because this version is where recovery branches start to multiply.

**Buys you:** the assumption that hurt most in version 1 is gone. The table can be
loaded any way round, and full glasses are handled correctly. **Costs you:** training
data and a labelling job, plus a component whose reasoning you cannot read.

This is where most of the value in the whole ladder sits, and for a kitchen it may be
the last version you need.

### Version 3: the awkward part is learned

**Replaces a skill.** The descent and release — the part with the 10 mm corridor, the
contact and the slow opening — is replaced by a policy learned from demonstrations,
while perception, planning and the safety checks stay exactly as they were.

**Stack, on top of version 2:** LeRobot, which is where the imitation-learning methods
such as ACT and diffusion policy are now maintained, for recording demonstrations,
training and running the policy.

**Buys you:** tolerance of things you did not model — a rack that shifted, a glass of
an unfamiliar size, a neighbour leaning slightly. **Costs you:** a few hundred
demonstrations and a rig to collect them, and a part of the system that can no longer
be inspected line by line. Keep `check_standing()` and the weight gate in ordinary
code either way.

### Version 4: one policy, driven by an instruction

**Replaces the pipeline.** A pretrained vision-language-action model takes the camera
pictures and an instruction such as "put the empty glasses on the rack" and produces
the arm commands directly.

**Stack:** openpi, or another open pretrained policy, fine-tuned on the demonstrations
collected for version 3.

**Buys you:** new glassware, and new instructions, without new demonstrations.
**Costs you:** predictability. This is the version whose behaviour you can forecast
least, so it is the one where the weight gate, the force limits and the final check
matter most. Treat it as an experiment run inside version 2's safety cage, not as a
replacement for it.

---

## 4. Which part uses what

This is the shortlist. Read it as one row per job: what we use, and the obvious
alternative we are not using, with the reason.

| Job | What we use | Rather than |
| --- | --- | --- |
| Simulate it first | Gazebo | MuJoCo — better contact, but simulated cameras and ROS in the loop matter more here |
| Describe the arm | URDF | a bespoke model nothing else can read |
| Find the glasses | a YOLO segmentation model on the ordinary picture | colour thresholding, which has nothing to work with on a transparent object |
| Tell empty from full | the same model, two classes, then confirmed by weight | vision alone, because the turn cannot be undone |
| Fill the depth hole, if needed | ClearGrasp or TransCG | waiting for the depth camera to get better |
| Fit the shape and the table | Open3D | PCL, the Point Cloud Library — capable, but heavier than this needs |
| Locate the rack | an AprilTag marker on its base | FoundationPose, unless you cannot glue a marker on |
| Plan the motion | MoveIt 2 | hand-written waypoints, which stop working the day the rack moves |
| Plan grasp, turn and place together | MoveIt Task Constructor | planning each stage separately, then finding the grasp forbids the release |
| Drive the joints | ros2_control | your own control loop, where the hard part is the timing |
| Descend onto the rack | the admittance controller in ros2_controllers, or cartesian_controllers | commanding a height into a rigid base |
| Sequence and recover | BehaviorTree.CPP | a state machine, which turns illegible once recovery branches multiply |
| Learn a skill, version 3 | LeRobot | the original ACT and diffusion policy repositories, which are quiet now |
| Pretrained policy, version 4 | openpi | training your own from nothing |
| Record every attempt | rosbag2 | log lines, which cannot show you the frame before the drop |

The hardware choices are shorter, and there are only three that matter.

| Part | What we use | Why |
| --- | --- | --- |
| Gripper | two-finger parallel, with soft silicone pads | the pads raise friction, which widens the low side of the force band; suction fails on a curved, wet, inverted 220 g object |
| Where it holds | the end that becomes the *top* after the turn | the fingers then stay clear of the pegs and the neighbouring rims during the descent |
| Cameras | one overhead, one on the wrist | the wrist camera removes the camera-to-arm calibration error, which is the error that actually sinks this task |
| Force | a wrist force sensor, or joint-torque estimates | it is needed twice: to weigh the glass, and to stop the descent on contact |

Three of those carry a cost worth knowing before you commit. MoveIt Task Constructor
is a noticeably steeper learning curve than plain MoveIt, and version 1 does not need
it. BehaviorTree.CPP adds a second representation, in XML, that a newcomer must learn
before they can read your logic at all. And the admittance controller needs a force
reading you trust plus an afternoon of stiffness tuning with nothing to show for it.

**Links:** [Gazebo](https://github.com/gazebosim/gz-sim) ·
[MoveIt 2](https://github.com/moveit/moveit2) ·
[MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) ·
[ros2_control](https://github.com/ros-controls/ros2_control) ·
[ros2_controllers](https://github.com/ros-controls/ros2_controllers) ·
[cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) ·
[BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) ·
[Ultralytics YOLO](https://github.com/ultralytics/ultralytics) ·
[SAM 2](https://github.com/facebookresearch/sam2) ·
[Open3D](https://github.com/isl-org/Open3D) ·
[ClearGrasp](https://github.com/Shreeyak/cleargrasp) ·
[TransCG](https://github.com/Galaxies99/TransCG) ·
[FoundationPose](https://github.com/NVlabs/FoundationPose) ·
[LeRobot](https://github.com/huggingface/lerobot) ·
[openpi](https://github.com/Physical-Intelligence/openpi)

---

## 5. When a new glass turns up

Keep everything glass-specific in one small file, one record per type, out of the
programme entirely. A record holds the rim diameters, the height, the empty mass, the
grasp height, the grip force dry and wet, and the shape family. Adding a glass is then
a new record and a test run, not a code change, and somebody with a ruler and a
kitchen scale can write one in five minutes.

The dangerous case is not a new glass. It is a new glass treated as an old one — a
cylinder fitted to a wine glass returns an answer, and the answer is confident and
wrong. So make the fit report how well it fitted, compare the measured dimensions
against what is on file, and stop and ask when nothing matches. Refusing to act is a
perfectly good outcome.

How much that buys you depends on the version, and the pattern is the same at all of
them: **a new size is nearly free, a new shape never is.** Changing size changes
numbers. Changing shape changes which surfaces can be held and which way up the thing
can stand, and no amount of training data turns that into the same problem.

---

## 6. What will bite you

- **Broken glass is not a retry.** It leaves shards, and an arm that will happily
  carry on moving through them. The response to a drop is to stop the cell and call a
  person. Decide that before writing the recovery logic, because it changes its shape.
- **Water is worse than breakage.** It spreads, it reaches the electronics, and it is
  a slip hazard for the people nearby. That is why there are two gates before the turn
  rather than one.
- **A nearly-empty glass looks empty.** A centimetre of water left in the bottom is
  hard to see and easy to weigh, which is the whole argument for the second gate.
- **Calibration drift eats your margin.** You have 10 mm between rims. A 3 mm error
  between where the camera thinks the rack is and where it is has taken a third of it
  before the arm has moved.
- **Wet glass is a different object.** It slips at forces a dry one holds at. If the
  glasses come from a sink, every grip number has to be measured wet.
- **The rack moves, and it fills.** It is light plastic on a table. Fix it down or
  find it every cycle — and fill the pegs in an order that keeps the occupied ones
  away from the next one for as long as possible.
- **Simulation will not give you the grip numbers.** Rigid fingers on a thin rigid
  shell is close to the worst case for a physics engine. Use the simulator for
  reaching, planning, the turn and the clearances; get the grip from a real glass.

---

## 7. What to measure

Robot demonstrations are easy to make look good, so decide what you are counting
before you start. These six numbers are enough.

| Number | How to count it |
| --- | --- |
| Success rate | glasses standing ten seconds after release, over attempts |
| Full glasses correctly left alone | over full glasses presented — a miss here is a wet floor |
| Breakages per thousand attempts | the number that decides whether this can ever ship |
| Attempts per glass | how often it has to let go and try again |
| Cycle time | from reaching for the glass to the arm clear of the rack |
| Failures caught before release | as a share of all failures — whether the checks are working |

The last row is the one people leave out and the one to watch most closely. A system
that notices it has the glass wrong and puts it back down is in a different class from
one that finds out by hearing it break, even at the same success rate.

Log every attempt: the camera frames, the force trace, the gripper width, and the
planned and actual poses. Without those, a failure two weeks from now is a story
rather than a bug.

---

## 8. Where to go next

- [The overview](../01_overview.md), and its
  [grid of which method suits which task](../01_overview.md#5-which-method-for-which-task),
  is where these choices came from.
- [Programmed methods](../02_programmed-methods.md) covers the planning, the behaviour
  trees and the [force control](../02_programmed-methods.md#6-feedback-control) used in
  versions 1 and 2.
- [Learned methods](../03_learned-methods.md) covers what versions 3 and 4 involve.
- [The learning path](../04_learning-path.md) has five projects to build in
  simulation; projects 1 and 2 between them cover most of what this task needs.
- [Tools and libraries](../../06_tools-and-libraries.md) is the fuller version of
  [section 4](#4-which-part-uses-what).
