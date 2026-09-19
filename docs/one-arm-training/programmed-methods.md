# Programmed methods for one arm

These are the methods where a person writes down what the arm should do. They are
precise, inspectable and safe; they cannot cope with variety; and they are what
runs in essentially every factory in the world today.

That last sentence is the reason this document comes first. It is tempting, in
2026, to skip straight to the learned methods, because that is where the exciting
results are. But almost all the arms actually working for a living are programmed
ones, almost all the paid work involves them, and — the part people miss — the
learned methods are far easier to understand once you know exactly what they are
replacing. A policy that outputs joint commands is replacing a trajectory
controller. A vision-language-action model is replacing a behaviour tree plus a
planner. If you do not know what those are, the replacement means nothing to you.

Read [the overview](overview.md) first if you have not — it sets out the tasks
these methods are for, the layers of a system they fill, and a grid saying which
method suits which task.

## Contents

1. [Teach and replay](#1-teach-and-replay)
2. [Offline programming](#2-offline-programming)
3. [Scripted logic: state machines and behaviour trees](#3-scripted-logic-state-machines-and-behaviour-trees)
4. [Motion planning](#4-motion-planning)
5. [Task and motion planning](#5-task-and-motion-planning)
6. [Feedback control](#6-feedback-control)
7. [What to take from all six](#7-what-to-take-from-all-six)

The order is roughly from least to most machinery. Each method says which tasks
it suits, what its status is in 2026, **whether it is worth your time to learn
right now**, and which open code to look at. The task group letters — A to D —
are the ones from
[the overview's task catalogue](overview.md#1-what-an-arm-is-actually-asked-to-do).

---

## 1. Teach and replay

An operator drives the arm to a position using a handheld control box called a
**teach pendant**, presses a button to record that position, and repeats until the
whole motion is stored. The recorded positions are called **waypoints**, and
playing them back in order is the programme. Newer arms let you simply push the
arm around with your hands instead of driving it with buttons, which is much
quicker; that is called **lead-through** or **kinesthetic teaching**.

It is worth being clear about how little this method assumes. There is no model of
the robot, no camera, no simulation, no programmer and no mathematics. An operator
who already understands the job can teach a new motion in an afternoon, and if the
motion is wrong they re-teach the waypoint that was wrong. This is a genuinely
good property and it is why the method has survived fifty years.

What it assumes instead is that the world never changes. Every waypoint is a set
of joint angles, recorded once, meaning nothing except "put the joints here". Move
the fixture two centimetres to the left and every waypoint is now wrong, and
nothing in the system knows it. The arm will drive confidently into the new
position of the part.

**Good for:** Group A tasks where the part is held in a jig and the motion is the
same every time — which, in a factory, is most of them.
**Useless for:** anything in Groups B, C or D, because there is nothing stable to
record against. If the object moves, a recording of where it used to be is not
useful.

**Status in 2026: not declining, and being made easier rather than replaced.** You
will meet the claim that "over 90% of industrial robots are programmed by teach
pendant" in a dozen places. Every one of those traces back to the same undated
trade-association page, which now returns a 403 error, and the academic version of
the claim dates from 2012. There is no trustworthy current public figure and this
document will not invent one. What *can* be said from vendor material is more
interesting anyway: collaborative-robot welding is growing quickly, and its entire
selling point is that you hand-guide the torch along the seam and press start —
which is *more* teaching, done by *less* specialised people. Palletising is the
one genuine case where teaching was replaced, and it was replaced by a wizard that
computes the stacking pattern from the box dimensions, not by anything learned.

**Worth learning now?** Not as a technique — there is nothing to learn, which is
the point of it. But it is worth *understanding*, because it is the baseline every
other method is implicitly competing against. When someone proposes a learned
policy for a task, the first honest question is whether teaching it would have
worked, and often the answer is yes.

**Code to look at:** none worth naming. This lives entirely in vendor software,
and each vendor's is different.

## 2. Offline programming

The same idea, done in software instead of on the factory floor. You model the
workcell as CAD geometry — the robot, the fixture, the part, the tooling — write
the motion against that model, simulate it to check that nothing collides, and
download the finished programme to the real robot.

The reason this exists is economic rather than technical. Teaching by hand
requires the production line to stop, and a line that is stopped is not making
anything. Offline programming lets the next product's programme be written while
the current one is still running.

This is how car bodies get welded, and it is worth knowing the pipeline because it
is the single largest use of robot arms on earth. The spot-welding programmes in a
body shop are generated from CAD in tools such as DELMIA, Process Simulate or ABB
RobotStudio, downloaded to the line, and touched up by hand once on the real cell.
There is no sensing and no learning anywhere in it, and there does not need to be:
the part is in a jig, and the jig is the thing that makes the geometry true.

**The weakness is inherited directly from the strength.** The programme is correct
with respect to the *model*. A fixture three millimetres from where the drawing
says it is becomes a run-time error, and the arm has no way to notice. Closing
that gap is what calibration is for, and it is a surprisingly large part of what
commissioning a real cell actually involves.

Where the part itself varies, the fix is still classical sensing rather than
learning. Arc welding handles variation with through-arc seam tracking, touch
sensing and laser seam trackers, and the major vendors' arc-welding product pages
describe no machine learning at all.

**The axis that is genuinely moving here is from CAD-based to scan-based.** Scan
the actual part, generate the toolpath from the scan, and skip both the drawing
and the teaching. Path Robotics does this for welding with no CAD model, and
ROS-Industrial's Scan-N-Plan is the open demonstration of the same idea. Note what
this is and is not: it removes the CAD requirement, and it is still programming.
Nothing in it is a learned policy.

**Good for:** the planned motions of Group A, and any cell where the layout is
fixed and the sequence is known in advance.
**Status in 2026:** standard, and the backbone of high-mix production.
**Worth learning now?** Yes, and this is the least fashionable advice in this
document. Offline programming and the calibration that makes it work are a large
fraction of what robot integrators are actually paid for, and the skill transfers
directly to any arm from any vendor. It is also the fastest way to develop an
intuition for why geometry is hard.

**Code to look at:** the mainstream tools are commercial, and
[RoboDK](https://robodk.com/) is the accessible one to try. The industrial
process-path stack has a serious open counterpart worth knowing:
[Tesseract](https://github.com/tesseract-robotics/tesseract) is the planning
environment and solver set, used on real sanding and painting programmes;
[Noether](https://github.com/ros-industrial/noether) generates toolpaths from a
surface mesh; and
[scan_n_plan_workshop](https://github.com/ros-industrial-consortium/scan_n_plan_workshop)
wires scan → reconstruct → toolpath → plan → execute together into one working
example. Be warned that Tesseract ships no packaged binaries, so you build it from
source.

## 3. Scripted logic: state machines and behaviour trees

Real tasks are not single motions, they are sequences with conditions attached: if
the gripper is empty, pick; if the pick failed, retry; if it has failed three
times, stop and call someone. Something has to hold that structure, and there are
two standard answers.

A **state machine** is a set of named states — "approaching", "gripping",
"retreating" — with rules for moving between them. It is easy to understand with
five states and becomes unreadable at fifty, because the number of possible
transitions grows with the square of the number of states.

A **behaviour tree** arranges the same task as a tree of nodes that is "ticked"
repeatedly, perhaps fifty times a second. Each node reports one of three things:
success, failure, or "still running". Composite nodes combine children in useful
ways — a **sequence** node runs its children in order until one fails, a
**fallback** node tries each child until one succeeds, which is exactly the shape
of "try the normal thing; if that fails, try the recovery". Behaviour trees came
from video games and were adopted in robotics for one specific property: they stay
readable at fifty branches, and you can add a recovery behaviour without rewriting
anything around it.

That property matters more than it sounds. Most of the code in a working robot
system is not the happy path, it is what happens when the happy path fails, and
the structure that lets you keep adding failure handling without the whole thing
collapsing is worth a great deal.

**Good for:** the sequencing layer of every task in every group, and especially
the twenty-step jobs in Group A where step four quietly ruins step nine.
**Status in 2026:** standard, and the default answer for the top layer of a
system. The only thing now competing for this job is a language model
([directed by language](learned-methods.md#5-directed-by-language)) — and even
where a language model is used, the tree usually remains underneath as the thing
that actually runs, with the model choosing which subtree to invoke.
**Worth learning now?** Yes, and it is cheap to learn. An afternoon with
BehaviorTree.CPP's examples will teach you more about how robot software is
actually organised than a month of reading about policies.

**Code to look at:** [BehaviorTree.CPP](https://www.behaviortree.dev/)
([repo](https://github.com/BehaviorTree/BehaviorTree.CPP), 4.2k stars, active) is
the standard, and its Groot editor lets you watch the tree tick in real time,
which is the best way to understand them.
[py_trees](https://py-trees.readthedocs.io/) is the Python and ROS equivalent and
the easier place to start if you are more comfortable in Python.

## 4. Motion planning

Given where the arm is now and where you want the gripper to be, find a path that
gets there and collides with nothing. The planner needs a model of the robot — a
URDF file, as built up in this repo's [arm area](../arm/overview.md) — and a model
of the surroundings, which usually comes from a depth camera turned into an
occupancy map.

The problem is much harder than it sounds, and it is worth understanding why. A
six-joint arm has a six-dimensional space of possible configurations, and every
obstacle in the world carves a complicated forbidden region out of that space.
Those regions have no simple description: a box on the table becomes, in joint
space, a shape nobody can draw. So planners do not try to describe the free space,
they explore it.

**Sampling-based planners** — RRT, the rapidly-exploring random tree, and PRM, the
probabilistic roadmap — throw random configurations at the space, throw away the
ones that collide, and connect the survivors until a path from start to goal
emerges. They are very good at finding *a* path through awkward spaces, and they
have two annoying properties that follow from being random: the path is usually
ugly, with unnecessary detours, and it is different every time you run it. The
ugliness is fixed by a smoothing pass afterwards; the non-determinism is not
fixable and is a genuine problem for anyone who has to validate a cell.

**Optimisation-based planners** — CHOMP, TrajOpt, and the modern GPU solvers —
start from a guess at the whole path, often just a straight line in joint space,
and push it away from obstacles while keeping it short and smooth. The paths are
far nicer and repeatable. The cost is that the method can get stuck in a local
minimum where a sampler would eventually have found a way round.

![The same start and goal, solved three ways](../images/one-arm-training/programmed-methods/planner-families.svg)

**A third family is the one learners consistently miss and industry uses
constantly.** Industrial controllers mostly do not plan at all. They execute
**point-to-point, linear and circular** motions between taught poses, computed
deterministically, at a speed profile the controller guarantees. If you have only
met sampling planners you will find this surprisingly limited; if you have to
certify a cell you will find it indispensable, because the arm does the same thing
every time and you can prove what it will do. MoveIt 2 ships this as the **Pilz
industrial motion planner**, and it is the closest thing in open source to how a
real factory arm moves.

**Good for:** Groups A, B and C, and the "how to move" layer of D. Motion planning
is the piece that lets a system respond to *where things actually are* rather than
replaying a recording, and that is the single biggest capability jump over teach
and replay.
**Status in 2026:** standard and healthy. The live development is speed — GPU
planners now replan continuously, many times a second, rather than planning once
and executing. That turns the planner from something that produces a path into
something that produces a reaction, which is a genuinely different capability.
**Worth learning now?** Yes. This is the single most useful technical skill in this
document for paid work, because every system needs it and it is fiddly enough that
people pay for someone who has done it before. It also happens to be the part of
the stack that learned methods have *not* displaced.

**Code to look at:** [MoveIt 2](https://moveit.ai/)
([repo](https://github.com/moveit/moveit2), 2.0k stars, active) wraps both
families and is what you will meet in practice;
[OMPL](https://ompl.kavrakilab.org/) (2.2k) provides the samplers underneath it;
[cuRobo](https://curobo.org/) ([repo](https://github.com/NVlabs/curobo), 1.9k) is
the GPU-parallel optimisation planner and is what "replan continuously" means in
practice. Two pieces worth knowing beyond the obvious: the **Pilz industrial
motion planner** inside MoveIt 2, described above, and
[Ruckig](https://github.com/pantor/ruckig), which generates jerk-limited
time-optimal trajectories online — between them they are much closer to how a
factory arm actually moves than a randomised sampler is.

## 5. Task and motion planning

Sometimes what to do and how to move cannot be separated. To put a mug in the sink
you may first have to move the pan that is in the way — but whether you must move
it depends on geometry, and whether you *can* move it depends on whether a
collision-free path exists for the pan. Deciding the sequence without checking the
geometry gives you plans that cannot be executed; checking the geometry requires
knowing the sequence.

Task and motion planning, almost always shortened to **TAMP**, searches both at
once. A symbolic layer proposes action sequences — "move the pan, then place the
mug" — and a geometric layer tests whether each proposed action is physically
achievable, feeding the failures back so the symbolic layer can try something
else.

It is the most capable purely-programmed approach for long tasks, and it is also
the hardest to build, the slowest to run, and the one that demands the most from
you before it will do anything: somebody has to write a symbolic model of the
domain, listing every action with its preconditions and effects.

**Good for:** in principle, the long rearrangement problems in Groups B and D.
**Status in 2026: research, and used less than its reputation suggests.**
Industrial long-horizon work is done with behaviour trees instead, because a
behaviour tree is free to write and a domain model is not. The research energy has
largely moved to language models doing the same sequencing job with far less
modelling effort — which is a fair trade in a research setting and a questionable
one anywhere safety matters.
**Worth learning now?** Read enough to know what it is and why it has not taken
over. Do not invest in it unless you are going into research. The honest signal is
that the reference implementation's last commit was in 2023.

**Code to look at:** [PDDLStream](https://github.com/caelan/pddlstream) (486 stars,
last commit 2023) is the well-documented reference, and its own activity level is a
fair indicator of the state of the field.

## 6. Feedback control

Underneath every method in this document and the next one, something has to
convert an intention into actual motor currents and react to what happens. This is
the layer people skip and then discover the hard way. Four ideas matter.

**Inverse kinematics and trajectory tracking** work out the joint angles that put
the gripper where you want it, and drive the joints along the path. This is the
subject of this repo's [arm area](../arm/overview.md), and it is the minimum you
need to make an arm do anything at all.

**Force control** matters the moment the arm touches something, and it is the most
important idea in this section.

![Commanding a position into a surface, against commanding a stiffness](../images/one-arm-training/programmed-methods/position-vs-force.svg)

Consider what happens when you command a position that is one millimetre inside a
rigid steel surface. The controller sees a
position error it cannot remove, so it increases the command. The error is still
there, so it increases it again. This is how arms break things, and it is not a
bug, it is exactly what a position controller is supposed to do.

The alternative is to stop commanding position and start commanding *how the arm
should respond to force* — behave like a spring with a stiffness you choose, so
that a millimetre of unexpected contact produces a modest push rather than an
escalating one. That is **impedance control**, and its close relative **admittance
control**, which measures the force and moves in response rather than the other
way round. If you learn one thing from this document, learn the difference between
commanding a position and commanding a stiffness.

**Visual servoing** closes the loop on the camera instead of on the joint
encoders: measure the difference between what the camera sees and what it should
see, and move to reduce it. Its great virtue is that it sidesteps a whole class of
calibration errors, because it never needs to know where the object is in world
coordinates — only whether the picture is getting closer to the target picture.

**Model predictive control** repeatedly solves a short optimisation problem: given
where I am now and a model of how the system moves, what is the best sequence of
commands over the next second? It executes only the first command, then throws the
rest away and re-solves. That sounds wasteful and is the whole point, because
re-solving is how it absorbs everything the model got wrong.

**Good for:** Group A is force control's home — insertion, screwdriving, polishing,
anything where a part is pressed against another — and it underlies the release in
Group D. It is also the bottom layer under every learned method, because a policy
that outputs positions still needs something beneath it that will not snap the part.

**Status in 2026: standard, essential, and still the answer to contact-rich
assembly.** Every major vendor sells this as a product: force sensors and fitting
functions from FANUC, two separate force-control options from ABB — one for
machining, one that searches for the right location during assembly without
jamming the part — KUKA's force-torque package, and joint-torque impedance control
on torque-sensing arms.

One detail is worth absorbing because it tells you something about the physics. For
polishing and deburring, the force loop usually does not live in the arm at all. It
lives in a **compliant flange** bolted between the arm and the tool, a small device
that holds a set force over a few millimetres of travel. It does this far faster
than the arm could, and one vendor markets it explicitly as a loop that works
independently of the robot — which is the industry quietly conceding that a big
six-axis arm is too heavy and too slow to control contact well. A learned policy
does not change that physics.

Visual servoing is the one piece here that has narrowed. It survives in specific
niches while the general case moved to learned perception feeding a planner.

**Worth learning now?** Force control, yes, emphatically, and it is the most
undersupplied skill of the lot. Contact-rich assembly is where both the unsolved
industrial problems and the interesting learned methods live, and you cannot
evaluate either without understanding what the controller underneath is doing.

**Code to look at:** [ros2_control](https://control.ros.org/)
([repo](https://github.com/ros-controls/ros2_control), active) including a
ready-made admittance controller; [Drake](https://drake.mit.edu/) and
[Pinocchio](https://github.com/stack-of-tasks/pinocchio) for the model-based side;
[ViSP](https://visp.inria.fr/) for visual servoing; and
[MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc) to watch predictive
control work interactively, which is by far the fastest way to develop an
intuition for it.

Be aware of where the open stack stops. `ros2_control` gives you admittance control
and a force-torque broadcaster, and beyond that — hybrid force-position control,
contact-rich assembly strategies, seam tracking — you either write it yourself or
buy it from the robot vendor. That gap is real, and it is the main reason serious
contact work still runs on vendor software.

---

## 7. What to take from all six

Three things, if you are reading this to decide where to spend your time.

**The top and bottom of the stack are solved and the middle is contested.** Nobody
is trying to replace behaviour trees at the top or trajectory controllers at the
bottom. Everything in the learned-methods document is competing for the middle:
deciding which skill, where, and how to move and touch.

**Programmed methods fail loudly and learned methods fail quietly.** When a taught
programme goes wrong you know which waypoint; when a planner fails it says so and
stops. That property is why industry adopted these methods and why it has been slow
to replace them, and it is worth weighing before you propose replacing one.

**The two families are not alternatives so much as layers.** Almost every real
system that uses machine learning is one of these programmed stacks with a network
substituted for the part that requires recognising something. That pattern —
covered in
[learned pieces inside a programmed system](learned-methods.md#4-learned-pieces-inside-a-programmed-system)
— is the most deployed use of machine learning on robot arms by a very wide margin,
and it only makes sense if you know the stack it is sitting inside.

Next: [learned methods](learned-methods.md), or back to
[the overview](overview.md).
