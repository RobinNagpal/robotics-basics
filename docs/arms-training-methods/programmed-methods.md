# Programmed methods for two arms

These are the methods where a person writes down what the arms should do. They
are precise, inspectable and safe; they cannot cope with variety; and they are
what runs in essentially every factory today.

Read [the overview](overview.md) first if you have not — it sets out the tasks
these methods are for, the three kinds of two-arm coordination they have to
support, and a grid saying which method suits which task.

The order below is roughly from least to most machinery. Each method says which
tasks it suits, **what changes when there are two arms instead of one**, what its
status is in 2026, and which open code to look at. The task group letters — A to
D — are the ones from
[the overview's task catalogue](overview.md#2-the-tasks-two-arms-are-asked-to-do).

## Contents

1. [Teach and replay](#1-teach-and-replay)
2. [Offline programming](#2-offline-programming)
3. [Scripted logic: state machines and behaviour trees](#3-scripted-logic-state-machines-and-behaviour-trees)
4. [Motion planning](#4-motion-planning)
5. [Task and motion planning](#5-task-and-motion-planning)
6. [Feedback control](#6-feedback-control)

---

## 1. Teach and replay

An operator drives the arm to a position with a control box called a **teach
pendant**, presses a button to record it, and repeats; the recorded positions are
**waypoints**, and playing them back is the programme. Newer versions let you
push the arm around by hand, which is quicker and is called lead-through or
kinesthetic teaching.

It needs no model, no camera, no simulation and no programmer, and an operator
who knows the job can teach a new motion in an afternoon. Against that, it
assumes the world never changes: move the fixture two centimetres and every
waypoint is wrong.

**With two arms** this is still perfectly workable, and it is how dual-arm
industrial robots are actually programmed — but only for the *independent* and
*hold-and-work* patterns from [the overview](overview.md#4-the-three-ways-two-arms-can-be-coordinated),
and only when the timing between the arms can be written down as simple waiting.
You teach the holding arm its one pose, you teach the working arm its sequence,
and you insert waits so that neither moves while the other is in its space.
What you cannot teach this way is anything where the two arms must move
*together* along a coordinated path — carrying one object between them, or keeping
a cloth in tension — because that is not a pair of recordings, it is a constraint
that has to hold continuously. For that you need the coordinated control in
[section 6](#6-feedback-control).

**Good for:** the free-space parts of Group A, and any two-arm task where one arm
simply holds a known part in a known place.
**Useless for:** Groups B, C and D, because there is nothing stable to record
against.
**Status in 2026: not declining, and being made easier rather than replaced.**
You will meet the claim that "over 90% of industrial robots are programmed by
teach pendant" in a dozen places. Every one of them traces back to the same
undated trade-association page, which now returns a 403 error, and the academic
version of the claim is from 2012. There is no trustworthy current public figure,
and this doc will not invent one. What can be said from vendor material is more
interesting anyway: cobot welding is growing quickly and its selling point is
that you hand-guide the torch and press start, which is *more* teaching done by
*less* specialised people. Palletising is the one genuine case where teaching was
replaced — and it was replaced by a wizard that computes the stacking pattern
from box dimensions, not by anything learned.
**Code to look at:** none worth naming — this lives in vendor software.

## 2. Offline programming

The same idea done in software: model the workcell as CAD geometry, write the
motion against the model, simulate it to check for collisions, and send the
finished programme to the robot. The reason is economic rather than technical —
teaching by hand stops the production line and this does not.

This is how car bodies get welded. The spot-welding programmes in a body shop are
generated from CAD in tools such as DELMIA, Process Simulate or ABB RobotStudio,
downloaded to the line, and touched up by hand once. There is no sensing and no
learning anywhere in that pipeline, and there does not need to be: the part is in
a jig.

**With two arms** this is the natural home for the problem teach-and-replay cannot
handle, because the simulation contains both arms and can therefore check the one
thing that matters most in a two-arm cell: that the arms never occupy the same
space at the same time. Multi-robot cells have been modelled this way for decades,
and the standard tools handle synchronisation points — markers saying "arm one
waits here until arm two reaches there" — which is exactly the loose coupling the
hold-and-work pattern needs. It remains a poor fit for continuously coordinated
motion, and it inherits all of its single-arm brittleness twice over: now *two*
sets of waypoints are wrong if the fixture moves.

**Good for:** the planned motions of Group A, and any two-arm cell where the
layout is fixed and the sequence is known in advance.
**Status in 2026:** standard. Its weakness is inherited: the programme is correct
with respect to the model, so a fixture three millimetres from where the drawing
says becomes an error at run time. Where the part varies, the fix is still
classical sensing rather than learning — arc welding handles variation with
through-arc seam tracking, touch sensing and laser seam trackers, and the major
vendors' arc-welding product pages describe no machine learning at all.

The axis that is genuinely moving here is **from CAD-based to scan-based**: scan
the actual part, generate the path from the scan, and skip both the drawing and
the teaching. Path Robotics does this for welding without CAD, and ROS-Industrial's
Scan-N-Plan is the open demonstration of the same idea. That removes the CAD
requirement — it is still programming, and none of it is a learned policy.
**Code to look at:** the mainstream tools are commercial
([RoboDK](https://robodk.com/) is an accessible example), but the industrial
process-path stack has a serious open counterpart in
[Tesseract](https://github.com/tesseract-robotics/tesseract) (planning environment
and solvers, used on real sanding and painting programmes),
[Noether](https://github.com/ros-industrial/noether) (toolpaths from a surface
mesh) and
[scan_n_plan_workshop](https://github.com/ros-industrial-consortium/scan_n_plan_workshop),
which wires scan → reconstruct → toolpath → plan → execute together. Be warned
that Tesseract has no packaged binaries, so you build it from source.

## 3. Scripted logic: state machines and behaviour trees

Real tasks are sequences with conditions: if the gripper is empty, pick; if the
pick failed, retry; if it failed three times, stop and call someone. A **state
machine** is a set of named states with rules for moving between them. A
**behaviour tree** arranges the task as a tree of nodes ticked repeatedly, each
reporting success, failure or "still running", with composite nodes such as "do
these in order until one fails". Behaviour trees came from video games and were
adopted in robotics for the same property: they stay readable at fifty branches,
and you can add a recovery without rewriting the rest.

**With two arms this is where role assignment lives**, and it is the most
important thing in this section. The tree is what says "left arm holds, right arm
works", what sequences the two, and what expresses the waiting — *do not start
driving the screw until the holding arm reports it has the part*. Two arms also
make the recovery logic sharply more valuable, because there are more ways to
fail: a handover can drop the object, the holding arm can lose its grip while the
other pushes, and either arm can be the one that got stuck. Behaviour trees handle
this well because each arm's behaviour can be its own subtree, with a small amount
of shared state between them, so you can read off which arm is doing what.

**Good for:** the sequencing and role-assignment layers of every task in every
group, and especially the twenty-step jobs in Group A and the recovery behaviour
that Groups B and D need.
**Status in 2026:** standard, and the default answer for the top layer. The only
thing now competing for this job is a language model
([a language model](learned-methods.md#5-directed-by-language)), and even then the tree usually remains
underneath as the thing that actually runs.
**Code to look at:** [BehaviorTree.CPP](https://www.behaviortree.dev/)
([repo](https://github.com/BehaviorTree/BehaviorTree.CPP), 4.2k stars, active),
[py_trees](https://py-trees.readthedocs.io/) for the Python and ROS equivalent.

## 4. Motion planning

Given the arm's current configuration and a target, find a path that collides
with nothing. It needs a model of the robot — a URDF, as in this repo's
[arm area](../arm/overview.md) — and a model of the surroundings, usually built
from a depth camera.

The problem is harder than it sounds because a six-joint arm has a
six-dimensional space of configurations and the obstacles carve complicated
forbidden regions out of it. **Sampling-based planners** (RRT, rapidly-exploring
random tree; PRM, probabilistic roadmap) explore that space randomly, keeping
collision-free configurations and connecting them until a path emerges; they are
very good at finding *a* path through awkward spaces, and the path is typically
ugly and different every run. **Optimisation-based planners** (CHOMP, TrajOpt and
modern GPU solvers) start from a guess at the whole path and push it away from
obstacles while keeping it short and smooth; the paths are far nicer and the
method can get stuck where a sampler would have found a way.

**With two arms, this is the method that changes most, in three ways.**

*The space to search doubles.* Two six-joint arms make a twelve-dimensional
configuration space, and the volume to be searched grows exponentially with
dimension, so a planner that solved one arm comfortably can become slow or fail to
find a path at all. The standard answer is to plan the two arms as one robot — a
combined group over all twelve joints — which is correct but expensive, so most
systems plan the arms *separately* wherever the task allows and only fall back to
the combined plan when the arms must interleave in the same space.

*Each arm is the other's moving obstacle.* Self-collision checking now includes
arm against arm, and unlike a table or a fixture that obstacle moves during the
plan. Planning them one at a time is what causes the classic two-arm bug: each
path is fine on its own, and together they collide, because the first plan did not
know where the second arm would be at that moment.

*Timing becomes part of the answer.* For one arm a path is a sequence of
configurations and the speed is a separate matter. For two arms that must meet —
a handover, or a joint carry — *when* each arm is where is part of the
specification, so the planner has to produce two time-synchronised trajectories
rather than two paths.

And the case a planner cannot express at all is the closed chain, where both arms
grip one object. The two arms' positions are no longer free to choose
independently — the object's rigidity ties them — and an ordinary planner has no
way to represent that constraint. Handling it needs either a planner that supports
closed-chain constraints or, much more commonly in practice, a controller that
holds the constraint while a simpler planner moves the object.

**Good for:** Groups A, B and C, and the "how to move" layer of D. It is the piece
that lets a system respond to *where things are* rather than replaying a
recording.
**Status in 2026:** standard and healthy. The live development is speed: GPU
planners now replan continuously rather than planning once, which matters
disproportionately for two arms, because continuous replanning is what lets one
arm get out of the other's way rather than waiting for it.
**Code to look at:** [MoveIt 2](https://moveit.ai/)
([repo](https://github.com/moveit/moveit2), 2.0k stars, active) wraps both
families; [OMPL](https://ompl.kavrakilab.org/) (2.2k) provides the samplers
underneath; [cuRobo](https://curobo.org/)
([repo](https://github.com/NVlabs/curobo), 1.9k) is the GPU-parallel
optimisation planner. Two pieces that learners consistently miss and industry
uses constantly: the **Pilz industrial motion planner**, which ships inside
MoveIt 2 and gives deterministic point-to-point, linear and circular motions the
way a real industrial controller does, and
[Ruckig](https://github.com/pantor/ruckig), which generates jerk-limited
time-optimal trajectories online. Between them they are much closer to how a
factory arm actually moves than a randomised sampler is.

## 5. Task and motion planning

Sometimes what to do and how to move cannot be separated. To put a mug in the
sink you may first have to move the pan in the way — but whether you must depends
on geometry, and whether you *can* depends on whether a collision-free path
exists for the pan. Task and motion planning, usually shortened to **TAMP**,
searches both at once: a symbolic layer proposes action sequences and a geometric
layer tests whether each is physically achievable, feeding failures back.

**With two arms** the appeal grows, because "which arm should do this step" is
exactly the kind of decision a symbolic planner could make instead of a person —
and re-grasping, the thing two arms are best at, is naturally expressed as a
symbolic action with geometric preconditions. That is the theory. In practice the
search gets harder for the same reason motion planning does, and the honest
position is that role assignment in working systems is written by hand.

**Good for:** in principle, the long rearrangement problems in Groups B and D,
and deciding which arm does what.
**Status in 2026: research, and used less than its reputation suggests.** It is
the most capable purely-programmed approach for long tasks and also the hardest
to build and the slowest to run, and it needs a symbolic model of your domain
that someone must write. Industrial long-horizon work is done with behaviour
trees instead, and the research energy has largely moved to language models doing
the same sequencing job with less modelling effort.
**Code to look at:** [PDDLStream](https://github.com/caelan/pddlstream) (486
stars, last commit 2023) is the well-documented reference — and its own activity
is a fair indicator of the state of the field.

## 6. Feedback control

Underneath everything, something converts intentions into motor commands and
reacts to what happens. Four ideas matter here.

**Inverse kinematics and trajectory tracking** work out the joint angles that put
the gripper where you want it and drive the joints along the path — the subject
of this repo's [arm area](../arm/overview.md).

**Force control** matters the moment the arm touches something. Commanding a
position against a rigid surface is how you break things: the controller sees an
error it cannot remove and pushes harder. The alternative is to command *how the
arm should respond to force* — behave like a spring of a chosen stiffness — which
is impedance control, or its cousin admittance control.

**Visual servoing** closes the loop on the camera instead: measure the difference
between what the camera sees and what it should see, and move to reduce it,
sidestepping a whole class of calibration errors.

**Model predictive control** repeatedly solves a short optimisation — given where
I am and a model of the dynamics, what commands over the next second are best? —
executes the first command and re-solves.

**With two arms, force control stops being optional and becomes the thing that
makes coordination possible at all.** Three points, in order of importance.

*The closed chain has to be controlled, not planned.* When both grippers hold one
object, commanding both arms by position guarantees a fight, because no two
position commands agree to the precision the object's rigidity demands. The
standard fix is to stop thinking about two arms and think about one object: command
where the *object* should go and how hard the arms should squeeze it, and let the
controller work out what each arm does. The squeeze — the part of the force that
presses the grippers together and produces no motion — is then something you
choose deliberately, firm enough not to drop the object and gentle enough not to
crush it.

*The holding arm needs the opposite setting to the working arm.* An arm that
steadies a part while the other pushes into it should be stiff, so the part does
not move. An arm that pushes a connector home should be soft, so a small
misalignment is absorbed rather than jamming. That means two different control
configurations running at once — which is ordinary to set up, and easy to get
backwards.

*Release timing is a force problem.* A handover, or setting a stone down and
letting go, comes down to transferring load from one arm to the other or to the
world. Doing it by position is guesswork; doing it by watching the force fall as
the other support takes the weight is measurable.

**An open gap worth knowing about.** Control theory has had a proper mathematical
treatment of two cooperating arms for decades — formulations that describe the
pair as a single system with one set of coordinates for the object's motion and
another for the internal squeeze, so that the two can be commanded separately.
Learned policies do not use any of it. A search for work combining a trained
policy with an explicit cooperative formulation turns up essentially nothing; the
learned side reinvents the idea informally, by putting each gripper's position
relative to the other into the network's input and hoping the constraint is picked
up from the data. Whether the formal structure would help a learned policy is, as
far as this doc could establish, an unanswered question rather than a settled one.

**Good for:** Group A is force control's home — insertion, screwdriving, anything
where a part is held while another is fitted — and it underlies the release in
Group D. It is also the bottom layer under every learned method, because a policy
that outputs positions still needs something underneath that will not snap the
part or tear what both arms are holding.
**Status in 2026: standard, essential, and still the answer to contact-rich
assembly.** Every major vendor sells this as a product — force sensors and fitting
functions from FANUC, two separate force-control options from ABB (one for
machining, one that searches for the right location during assembly without
jamming the part), KUKA's force-torque package, and joint-torque impedance on
torque-sensing arms. A detail worth absorbing: for polishing and deburring the
force loop usually does not live in the arm at all but in a **compliant flange**
bolted between the arm and the tool, which holds a set force over a few
millimetres of travel far faster than the arm could. One vendor markets that
device explicitly as a loop that works independently of the robot — which is the
industry conceding that a big six-axis arm is too heavy and too slow to control
contact well.

Visual servoing is the one piece here that has narrowed: it survives in specific
niches, while the general case moved to learned perception feeding a planner.
**Code to look at:** [ros2_control](https://control.ros.org/)
([repo](https://github.com/ros-controls/ros2_control), active) including a
ready-made admittance controller; [Drake](https://drake.mit.edu/) and
[Pinocchio](https://github.com/stack-of-tasks/pinocchio) for the model-based
side; [ViSP](https://visp.inria.fr/) for visual servoing;
[MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc) to watch predictive
control work interactively. Be aware of where the open stack stops: `ros2_control`
gives you admittance control and a force-torque broadcaster, and beyond that —
hybrid force-position control, contact-rich assembly strategies, seam tracking —
you either write it yourself or buy it from the robot vendor. That gap is real
and it is the main reason serious contact work still runs on vendor software.
