# Reaching and reachability: can the arm get there at all

Before any question about how to move, there is a question about whether the move
exists. This document is about that question, and about the fact that it has four
separate answers rather than one.

It is the most under-documented subject in this area. Motion planning has books,
tutorials and a healthy open-source ecosystem. Reachability has a parameter in a
configuration file and a solver that returns nothing when it fails. A great deal
of real project time is lost here, and almost all of it is lost to failures that
do not announce themselves: a pose that is reachable in one wrist configuration
and not the other, a straight line whose two ends are fine and whose middle is
not, a joint limit that a description file quietly narrowed, and a solver that
said no when it meant "not yet".

This is written for someone who is about to bolt an arm to a table, or has done
so and is now finding that a third of the poses they wanted do not work. It
follows on from [the overview](01_overview.md) and assumes the frames and
transforms of the [arm area](../03_arm/01_overview.md).

## Contents

1. [Four things "reachable" can mean](#1-four-things-reachable-can-mean)
2. [The workspace and its holes](#2-the-workspace-and-its-holes)
3. [Singularities, and what the controller does at one](#3-singularities-and-what-the-controller-does-at-one)
4. [Joint limits, and the range that is not there](#4-joint-limits-and-the-range-that-is-not-there)
5. [Configurations: the eight ways to reach the same pose](#5-configurations-the-eight-ways-to-reach-the-same-pose)
6. [Redundancy, and the seventh joint](#6-redundancy-and-the-seventh-joint)
7. [Where to bolt the arm down](#7-where-to-bolt-the-arm-down)
8. [Finding out before you commit](#8-finding-out-before-you-commit)
9. [The five failures that do not announce themselves](#9-the-five-failures-that-do-not-announce-themselves)

---

## 1. Four things "reachable" can mean

When somebody says a pose is reachable they may mean any of four different
things, and a system can pass three of them and fail the fourth.

**The position is inside the workspace.** The tool centre point can be put at
that point in space by some combination of joint angles. This is the weakest of
the four and it is the one people usually check.

**The position and the orientation are both achievable.** Most positions inside
the workspace can only be reached with the tool pointing in some directions and
not others. The set of positions reachable with *every* orientation is called the
dexterous workspace and it is much smaller than the reachable workspace — for a
typical six-joint arm it is a modest region in the middle, not the whole envelope.

**A joint solution exists that is also collision-free and inside the joint
limits.** Inverse kinematics can return an answer that puts the elbow through the
table. Reachability without a collision check is a statement about geometry, not
about the cell.

**A path exists from where the arm is now to that solution.** This is the one
that is almost never checked and the one that bites. Two configurations can both
be valid while no continuous motion connects them, because getting from one to
the other would mean passing through a joint limit or through the table.

The table below is those four against what tells you the answer. Read it as a
checklist in order: each row assumes the row above it passed.

| The question | What answers it | What it misses |
| --- | --- | --- |
| is the point inside the envelope | arithmetic on the link lengths | orientation, entirely |
| is this full pose achievable | an inverse kinematics solver | collisions, and the joint limits if the solver ignores them |
| is there a valid, collision-free joint solution | the solver plus a planning scene | that reaching it may require passing through something |
| can the arm get there from here | a motion planner, run for real | nothing — but it is the most expensive of the four |

## 2. The workspace and its holes

The reachable workspace is the set of points the tool can be put at. For an arm
whose links are `L1` and `L2` and whose joints have no limits, it is the region
between two spheres: an outer one at `L1 + L2` and an inner one at `|L1 − L2|`.
The inner sphere is a hole, and nothing inside it is reachable at any joint
angle, because the two links cannot fold closer together than the difference in
their lengths.

The [arm area](../03_arm/01_overview.md) builds an arm with `L1 = 3 m` and
`L2 = 2 m`, so its reachable region runs from 1 m to 5 m from the base. The
picture below is that region, with a move whose two ends are comfortably inside
it and whose middle is not.

![A move whose ends are reachable and whose middle is not](../images/arm-movement/reaching-and-reachability/workspace-hole.svg)

Both ends of that move sit 4.9 m from the base. Ask for a path in joint space and
one is found immediately: the joints simply rotate from one set of angles to the
other. Ask for a straight line between the same two poses and it fails in the
middle, because the straight line passes 0.851 m from the base and nothing nearer
than 1.0 m exists. A metre and five centimetres of the requested path is outside
the arm's world.

Three things about that are worth stating plainly.

**Checking each pose for reachability does not catch it.** Both poses pass. The
check is on poses and the failure is on the path between them.

**Turning the base does not help.** The hole is a solid of revolution about the
base axis, so it is in the way for every direction the arm might approach from.

**A real six-joint arm has the same hole, and it is bigger than the arithmetic
suggests.** The wrist is offset sideways from the shoulder, so the dead region
around the base axis is a cylinder rather than a point. The official Universal
Robots description gives the UR5e a 133.3 mm offset between the forearm and the
first wrist joint, which is the length that sets it. This is why an arm cannot
reach the spot directly underneath its own shoulder, which is exactly where
people like to put the part tray.

The practical consequence is a rule worth adopting early: **put nothing important
in the first fifth of the arm's reach, and nothing important in the last tenth.**
The inner region is the hole, and the outer region is the subject of the next
section.

## 3. Singularities, and what the controller does at one

A singularity is a configuration in which the arm loses the ability to move its
tool in some direction, however fast the joints turn. It is not a fault and not a
collision. It is the geometry running out.

[The one calculation](01_overview.md#5-the-one-calculation-underneath-everything)
gives the condition for the repo's two-link arm exactly: the Jacobian determinant
is `L1 · L2 · sin(q2)`, so the arm is singular when the elbow angle `q2` is zero
or 180 degrees — straight out, or folded back on itself.

The important thing is not the singular point. It is the region around it, and
how expensive that region gets. The chart below holds the tool speed constant at
50 mm/s straight out along the arm's own length, and asks what the elbow has to
do to deliver it.

![Holding the tool at 50 mm/s while the arm straightens](../images/arm-movement/reaching-and-reachability/singularity-cost.svg)

At 10 mm from full extension the elbow needs 18.5 degrees per second, which is
nothing. At 1 mm it needs 58.5. At a tenth of a millimetre it needs 184.9, and
the official Universal Robots description caps every UR5e joint at 180 degrees
per second. So the last tenth of a millimetre of reach costs more joint speed
than the whole first 190 mm, and on a real arm it is not available at all.

What actually happens on the bench takes one of three forms, depending on what
the controller does when the arithmetic asks for more than it has.

**The arm slows down.** A well-behaved Cartesian controller scales the whole
motion back so no joint exceeds its limit. The tool no longer travels at the
speed you asked for, which is safe and which breaks any process that depends on
speed — welding, dispensing, anything with a flow rate.

**The arm lurches.** A controller that clamps each joint independently produces
a motion that is no longer along the path at all. Near a wrist singularity this
shows up as the wrist spinning rapidly through half a turn while the tool barely
moves.

**The arm faults and stops.** Most industrial controllers refuse, which is the
honest answer and is the one that gets reported as "the robot will not do the
program".

A six-joint arm with a spherical wrist has three families of singularity, and
they need to be recognised by sight because they are diagnosed on the bench more
often than in software.

| Kind | The configuration | What is lost |
| --- | --- | --- |
| shoulder | the wrist centre lies on the axis of joint 1 | motion in the direction perpendicular to the arm's plane; joint 1 would have to turn infinitely fast |
| elbow | the arm is fully extended, or fully folded | motion along the arm's own length, which is the case drawn above |
| wrist | two of the three wrist axes line up | one rotational degree of freedom; the two aligned joints do the same thing, and their difference is undetermined |

The wrist one is the most common in practice and the most surprising, because
nothing about the arm looks extended. It happens whenever the tool points
straight along a wrist axis, which is exactly what happens when you ask an arm to
point straight down at a table — a request that comes up constantly.

**Five situations where a singularity will find you:**

- a straight-line move that reaches for something at the edge of the envelope
- pointing the tool straight down at a table from directly above
- any path you generated by interpolating tool poses without checking the joints
- teaching poses by hand, where a person naturally straightens the arm to reach
- a task that needs a full turn of the tool about its own axis

**Five situations where it will not:**

- joint-space moves between taught poses well inside the envelope
- work confined to a region a third to two thirds of the way out
- a seven-joint arm using its extra freedom to keep the wrist away from alignment
- planning that scores configurations on manipulability, which is a measure of
  how far a configuration is from being singular
- a mounting that puts the work in front of the arm rather than directly above
  or below the base

## 4. Joint limits, and the range that is not there

Joint limits are simple to state and are the source of two of the least obvious
failures in this document.

**A joint that can turn more than a full circle makes the planner's problem
harder, not easier.** Several arms have wrists that travel two full turns. That
means the same tool pose corresponds to several distinct joint values, and the
planner has to decide which. Get it wrong and the arm unwinds its own wrist in
the middle of a task, which is a valid motion and is not what anybody wanted.

**A joint whose real range is divided in two produces a search space that is
divided in two.** This is worth quoting in full, because it is in a file that
thousands of projects load without reading. The official Universal Robots ROS 2
description says this about the UR5e's elbow, in
[config/ur5e/joint_limits.yaml](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/ros2/config/ur5e/joint_limits.yaml):

> we artificially limit this joint to half its actual joint position limit to
> avoid (MoveIt/OMPL) planning problems, as due to the physical construction of
> the robot, it's impossible to rotate the 'elbow_joint' over more than approx
> +- 1 pi (the shoulder lift joint gets in the way). This leads to planning
> problems as the search space will be divided into two sections, with no
> connections from one to the other.

Read what that says. The joint's nominal limit is plus or minus 360 degrees. Its
physical limit is about plus or minus 180, because the shoulder gets in the way.
If the planner is told the nominal figure it explores a space in two disconnected
halves and behaves badly, so the description file tells it the physical figure
instead. The decision is correct. The consequence is that **half the elbow's
nominal travel is invisible to every planner that loads this file**, and nothing
anywhere reports that.

That is the general shape of the problem. The limits the planner sees come from a
description file, and a description file is a claim about the arm rather than the
arm. Three ways it drifts from the truth:

- a limit narrowed deliberately, as above, for a reason that was true then
- a limit that does not account for the tool, the cable, or the dress pack, all
  of which reduce the real range
- a limit that is right for the joint and wrong for the pair, because two joints
  that are each within range can still collide with each other

**Five things a joint limit stops you doing that are easy to miss:**

- following a circular path that requires the wrist to keep turning the same way
- approaching the same object from two sides without an intervening reset
- executing a taught programme after the tool has been changed for a longer one
- reaching a pose that inverse kinematics found, because the solver was not told
  about the limits
- reversing a path, because the way back can need a joint value the way out did
  not

## 5. Configurations: the eight ways to reach the same pose

For a six-joint arm with a spherical wrist — which is most industrial arms — a
given tool pose generally has **eight** distinct joint solutions. They come from
three independent binary choices.

**Shoulder, left or right.** The arm can reach the same point with the base
turned towards it or turned away from it and reaching backwards over its own
shoulder.

**Elbow, up or down.** The classic pair. Same wrist position, elbow above or
below the line from shoulder to wrist.

**Wrist, flip or no-flip.** The wrist can be turned through half a turn on joints
4 and 6 while joint 5 changes sign, which puts the tool in the same place
pointing the same way.

Two by two by two is eight. Every one of them is a correct answer to "where do I
put the joints", and they are not interchangeable:

- they have different distances to the joint limits
- they have different distances to a singularity
- they collide with different things
- the arm cannot generally get from one to another without passing through a
  singularity, which is the reason it matters

That last point is the one to hold on to. **The eight solutions are not eight
points in a connected space you can slide between.** They are, for practical
purposes, eight separate regions. A path that starts elbow-up and ends elbow-down
has to straighten the arm completely somewhere in the middle, and a planner will
either refuse or produce a motion that alarms whoever is watching.

This is where an early choice makes a later step impossible, and it is worth
being concrete. Suppose a pick-and-place: reach into a bin, grasp a part, place
it in a fixture. The grasp is chosen first, because the part's pose decides it.
That grasp has eight joint solutions and the planner picks one — usually the one
nearest the current configuration, which is a reasonable default and is not a
decision anybody made. Now the place pose is planned, and from that
configuration the only solutions for the place are on the other side of a joint
limit. The place fails. Nothing was wrong with the grasp, nothing was wrong with
the place, and the error message will be about the place.

The fix is in [section 9 of planning a path](03_planning-a-path.md#9-planning-the-whole-task-as-one-thing),
and it is not a framework. It is to solve the whole chain before committing to
the first step of it.

**Five jobs where configuration choice is the whole problem:**

- any task with a fixed approach direction, such as inserting into a machine
- palletising, where the same motion repeats at many positions and must not flip
  configuration halfway across the pallet
- a cell with a wall or a fence on one side, which makes one shoulder solution
  illegal everywhere
- bin picking, where the grasp pose varies and the configuration must not
- any task where a person watches, because a configuration flip looks exactly
  like a malfunction

**Five jobs where it does not matter:**

- a single move between two taught poses in the middle of the envelope
- work on a small, flat region where all eight solutions are far from limits
- a seven-joint arm with a null-space policy, which handles it continuously
- teaching and replay, where the configuration is recorded along with the pose
- simulation with no joint limits modelled, which is why the problem is usually
  discovered on hardware

## 6. Redundancy, and the seventh joint

Six numbers describe a pose: three for position, three for orientation. An arm
with six joints has exactly enough freedom to hit a pose, and generally a finite
number of ways to do it. An arm with seven joints has one more than it needs, and
therefore an infinite family of joint solutions for the same tool pose — a
continuous one-dimensional set you can slide along without the tool moving at
all. That set is called the null space, and sliding along it is usually described
as the elbow swinging round while the hand stays put.

What the extra joint buys you:

- it can hold the tool still while moving the elbow out of the way of an obstacle
- it can hold the tool still while moving away from a joint limit
- it can hold the tool still while moving away from a singularity
- it can serve a secondary objective continuously, rather than by choosing
  between eight discrete options
- it makes a configuration flip unnecessary, because there is a continuous route
  between solutions that a six-joint arm would have to jump between

What it costs:

- inverse kinematics no longer has a closed-form answer, so you are solving
  numerically and the solution depends on where you started
- the null-space policy becomes part of your system, and a policy nobody chose is
  still a policy
- repeatability of the *configuration* is lost: the same tool pose commanded
  twice can give two different arm shapes, which matters near obstacles
- a joint more is a motor more, a brake more, and a failure mode more
- it is harder to explain to anybody signing off the cell

Seven-joint arms include the Franka research arms and Kinova's Gen3. Six-joint
arms include the whole Universal Robots range and most of what is installed in
factories. The choice is not about capability in the abstract; it is about
whether your cell has obstacles the arm has to reach past.

## 7. Where to bolt the arm down

This is the cheapest decision in the whole area and the most expensive to reverse.
It is usually made by whoever built the bench.

Four things the mounting decides, in rough order of how often they are
overlooked.

**How much of the workspace is usable.** Bolt the arm in the middle of a table
and the region directly above the base — the hole from section 2 — sits over the
most convenient part of the table. Mount it at the edge, facing in, and the hole
is off the table.

**Whether the arm can reach a pose in a good configuration or only a bad one.**
The same point can be well inside the dexterous region for one mounting and right
at the singular edge for another. Moving the base 150 mm is often the difference
between a task that works and a task that needs a seven-joint arm.

**What the arm collides with.** An arm mounted upright collides with its own
table when reaching low. An arm mounted on a wall or inverted on a frame does
not, which is why so many production cells hang the arm upside down.

**Gravity, and therefore payload and force control.** An inverted arm carries its
own weight differently, and its gravity compensation model must know which way up
it is. This is a configuration item, and getting it wrong shows up as an arm that
drifts when you enable compliance.

The table below is the three usual mountings against what each is for. Read the
last column as the reason people regret it.

| Mounting | Suits | Regretted because |
| --- | --- | --- |
| upright on a bench | most table-top work, teaching, anything a person stands beside | the hole sits over the best part of the bench, and reaching low means reaching around the base |
| inverted on a frame | dense cells, machine tending, anything needing reach down onto a surface | everything is harder to reach by hand, and the frame is in the way of a person |
| on a wall or a pillar | long reaches across a bench, keeping the bench clear | the reachable region is a half-space, so half the eight configurations are unavailable everywhere |

One further point that is specific enough to be worth naming. **Deciding the
mounting requires knowing the task poses, and deciding the task poses requires
knowing the mounting.** The way out is to compute a reachability map for two or
three candidate mountings before anything is bolted to anything, which is the
subject of the next section and takes an afternoon.

## 8. Finding out before you commit

There are four levels of answer here and they cost wildly different amounts. Take
the cheapest one that settles your question.

**Arithmetic on the link lengths.** The inner and outer radii, worked out by
hand. Costs nothing, answers only the crudest question, and rules out more bad
layouts than people expect.

**Inverse kinematics on every pose you care about.** Write the list of poses the
task needs, ask the solver for each, and count the failures. Costs an hour and
answers the second and third of the four questions in section 1. This is the
step most projects skip and it is the one with the best return.

**A reachability map.** Sample the volume in front of the arm on a grid, try many
orientations at each point, and record what fraction succeeded. The result is a
picture of where the arm is genuinely comfortable, and it makes the mounting
decision for you.
[reach](https://github.com/ros-industrial/reach), from ROS-Industrial, is the
maintained tool for this and is Apache-2.0. It was last pushed in March 2025, so
it is stable rather than active. The older and better-known
[Reuleaux](https://github.com/ros-industrial-consortium/reuleaux) has been moved
into ROS-Industrial's attic and was last touched in July 2024; it is worth
knowing the name because papers cite it, and it is not worth building.

**Running the planner.** The only thing that answers the fourth question. Costs
the most and is the only honest test of "can the arm get there from here".

### 8.1 The solver's answer is weaker than it looks

One detail matters more than everything else in this section, because it makes
the second and third levels above unreliable if you take them at face value.

MoveIt's default inverse kinematics solver is KDL, which is iterative. It starts
from a seed, steps towards the goal, and gives up when it runs out of time. The
time it is given is the `kinematics_solver_timeout` parameter, and its default
value in MoveIt is **0.05 seconds**.

So when a reachability check reports a pose as unreachable, what it has actually
established is: *no solution was found within 50 ms, starting from the seeds this
run happened to try.* That is not the same statement as "no solution exists", and
the two are reported identically. Poses near the edge of the workspace, and poses
that need an unusual configuration, are exactly the ones a seeded iterative
solver is worst at, and they are exactly the ones you are testing.

Three practical responses:

- raise the timeout when you are surveying rather than executing; 50 ms is a
  runtime figure, not a survey figure
- retry from several seeds and count how many succeed, which turns a yes-or-no
  answer into a measure of how marginal the pose is
- use a solver with a different failure mode when it matters.
  [TRAC-IK](https://github.com/traclabs/trac_ik) (BSD-3) exists because KDL fails
  on poses that have solutions, and it runs two methods in parallel and takes
  whichever answers first. [pick_ik](https://github.com/PickNikRobotics/pick_ik)
  (BSD-3) is the maintained modern alternative inside MoveIt and is under active
  development.

## 9. The five failures that do not announce themselves

Collected here because they are the return on reading this document.

**The straight line between two reachable poses is not reachable.** Section 2.
Both ends check out; the middle does not. Nothing in a per-pose check can see it.

**"Unreachable" means "not found in 50 milliseconds".** Section 8.1. A survey
built on the runtime default will mark good poses as bad, and the marginal poses
are the ones it gets wrong.

**The joint limits in the description are not the joint limits of the arm.**
Section 4. The UR5e's elbow is deliberately halved in the file everybody loads.
The decision is right; the silence about it is the problem.

**The grasp you chose decided the configuration, and the configuration decided
that the place is impossible.** Section 5. Both plans succeed on their own. The
failure appears at the second step and was caused by the first.

**The dexterous workspace is much smaller than the workspace, and every
tutorial's example pose is in the middle of it.** Section 1. A task developed on
poses 400 mm in front of the arm will work. The same task at 700 mm, with the
tool pointing sideways, may have no solution at all, and the first symptom will
be a planner that times out rather than a message about orientation.

Next: [planning a path](03_planning-a-path.md), which assumes the goal is
reachable and asks how to get to it. Or back to
[the overview](01_overview.md).
