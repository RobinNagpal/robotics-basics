# Ways to programme or train a robot arm

If you set out to make a robot arm do something genuinely complicated — drive
the screws into an assembly and pack it, fold laundry, weld a seam on a line,
balance rough stones into a tower — you will find there is no agreed way to do
it. Read three papers and you meet three approaches that share almost no
vocabulary. One talks about planners and constraints, one about demonstrations
and policies, one about rewards and episodes. All three work, and all three are
describing the same job.

This doc is a map of that landscape, written for arms specifically rather than
for robots in general. It starts with the **tasks**, because which method you
need is decided almost entirely by the task, and a list of methods with no tasks
attached is what makes this subject confusing. It then takes each method in turn
and says three things: which of those tasks it is good for, what its status is
in 2026 — standard, fading, research-only, or brand new — and which well-known
piece of open code to look at.

**Who this is for.** Someone who can picture an arm moving and knows roughly
what a camera and a joint angle are, but who has not yet had to choose between
these approaches. You do not need to have used any of them.

**The short answer, before the long one.** The two families are *programming*,
where a person writes down what the arm should do, and *training*, where the
behaviour comes from examples or practice. Programming is precise, inspectable
and safe, and cannot cope with variety. Training copes with variety, needs a
great deal of data, and cannot tell you why it failed. Every serious system uses
both: it programmes the parts that are easy to say and trains the parts that are
not. Most of the skill is knowing which parts are which.

**A note on honesty.** Robotics is full of impressive demonstrations that are
not deployed anywhere, and unglamorous methods that run half the world's
factories. Where a method is only a laboratory result, this doc says so. Where a
claim could not be verified, it says that too, and
[section 13](#13-what-is-current-and-what-is-fading) lists what was checked and
when.

## Contents

1. [The tasks an arm is asked to do](#1-the-tasks-an-arm-is-asked-to-do)
2. [The five things that make a task hard](#2-the-five-things-that-make-a-task-hard)
3. [The four layers of any arm system](#3-the-four-layers-of-any-arm-system)
4. [The family tree](#4-the-family-tree)
5. [Programmed: a person writes the behaviour](#5-programmed-a-person-writes-the-behaviour)
6. [Learning from demonstrations](#6-learning-from-demonstrations)
7. [Learning from trial and error](#7-learning-from-trial-and-error)
8. [Learning from large-scale pretraining](#8-learning-from-large-scale-pretraining)
9. [Learned pieces inside a programmed system](#9-learned-pieces-inside-a-programmed-system)
10. [Directed by language](#10-directed-by-language)
11. [Which method for which task](#11-which-method-for-which-task)
12. [The four worked examples](#12-the-four-worked-examples)
13. [What is current, and what is fading](#13-what-is-current-and-what-is-fading)
14. [What each method costs you](#14-what-each-method-costs-you)
15. [What real systems actually do](#15-what-real-systems-actually-do)
16. [Where this repo fits](#16-where-this-repo-fits)

---

## 1. The tasks an arm is asked to do

Here is a spread of real jobs arms are bought to do, in five groups ordered by
how much is known in advance. That ordering is not arbitrary: it is the single
best predictor of which method you will end up using.

### Group A: everything is known, and nothing moves

The part arrives in a fixture, in the same orientation, a million times. The arm
has to be accurate and fast, and that is all.

| Task | What it involves | What makes it hard |
| --- | --- | --- |
| **Spot and arc welding** | follow a seam on a body held in a jig | speed, accuracy and heat; the geometry is given to you |
| **Machine tending** | load a blank into a machine, take the finished part out | cycle time and reliability, not perception |
| **Palletising** | stack boxes onto a pallet in a computed pattern | weight, reach, and keeping the stack stable |
| **Dispensing and painting** | run a nozzle along a path on a known surface | holding speed and stand-off constant |
| **Lab sample handling** | move tubes and plates between instruments | precision, and never dropping anything |

### Group B: the parts are known, but the fit decides everything

You have the drawings and the parts arrive in feeders, yet the job still fails,
because success is settled in the last millimetre by contact rather than by
position. **This group is where most industrial difficulty actually lives.**

| Task | What it involves | What makes it hard |
| --- | --- | --- |
| **Screwdriving and small assembly** | pick a screw from a feeder, align the part, drive the screw, place the finished unit in its packaging | screws cross-thread and parts jam; the tolerance is tighter than the arm's repeatability; twenty steps in a row must all work |
| **Connector and plug insertion** | push a connector into a socket | clearances under a millimetre, and the contact is hidden from view |
| **Polishing, sanding, deburring** | run a tool over a surface with controlled force | force matters more than position, and every surface differs slightly |
| **Kitting** | collect a set of known items into a tray | many small motions, and the items start somewhere different each time |

### Group C: the objects are known, but their arrangement is not

The catalogue is fixed, or nearly so, but nothing is where you left it. This is
the class that learned perception unlocked, and the one where machine learning
is genuinely in production today.

| Task | What it involves | What makes it hard |
| --- | --- | --- |
| **Bin picking of mixed items** | reach into a bin of jumbled parts and pull one out | clutter, occlusion, parts touching each other, no fixture |
| **Parcel and waste sorting** | pick an item off a moving belt and route it | rate, variety, and items never seen before |
| **Unloading a dishwasher** | take crockery out and put it away | clutter, occlusion, fragility, and many steps |

### Group D: the object itself is hard to describe

The object has no single shape. Its state is high-dimensional, hard to perceive,
and changes as you touch it.

| Task | What it involves | What makes it hard |
| --- | --- | --- |
| **Laundry folding** | pick up a garment, flatten it, fold it | a cloth has effectively infinite configurations and changes shape as you grip it |
| **Cable and harness routing** | lay a cable along a path and seat it in clips | the cable moves while you work, and the task is long |
| **Food handling** | pick fruit, arrange food on a tray | soft, fragile, and different every time |

### Group E: the geometry is unknown and physics decides the outcome

The hardest class, and the one this repo's worked example lives in.

| Task | What it involves | What makes it hard |
| --- | --- | --- |
| **Stacking irregular stones** | balance rough stones into a tower | no model of the object, and success is only known after you let go |
| **Building from rubble or scrap** | make a wall from whatever is to hand | every piece differs, and errors accumulate upwards |

---

## 2. The five things that make a task hard

Five properties do most of the work in those tables. Placing a new task on these
five tells you more about which method you need than any amount of reading about
methods.

**How much is known in advance.** Fixtures, drawings and a fixed catalogue of
parts at one end; a jumbled bin or a rough stone at the other. Programmed
methods need this knowledge, and are excellent when it exists.

**How much of the job is contact.** Moving through free space is well understood
and easy to plan. Deciding what to do while pressing one object against another
is neither, because the outcome depends on friction and on contacts you cannot
see. Insertion, polishing, folding and stacking are contact tasks; welding and
palletising are not.

**How many steps, and whether order matters.** Driving one screw is a single
skill. Assembling and packing a component is twenty steps, where step four
quietly ruins step nine. Long tasks need something that keeps track and can
recover.

**How tight the tolerance is.** An arm that repeats to a tenth of a millimetre
still cannot reliably seat a connector with a fifty-micron clearance by position
alone. Once the tolerance is tighter than the accuracy you can achieve, the task
stops being about geometry and becomes about feedback.

**What a failure costs.** Failing to place a stone costs a retry; scratching a
car body costs a great deal. Tasks where failure is cheap and repeatable can be
learned by practice; tasks where it is not must be verified before they run.

---

## 3. The four layers of any arm system

Underneath the vocabulary, any arm doing a real job answers four questions over
and over, and "which method" usually has a different answer at each.

![The four layers, and the methods that usually fill each](../images/arms-training-methods/overview/layers.svg)

Take the screwdriving-and-packing job from Group B. **What to do next** is the
sequence: fetch the housing, fit the board, drive four screws, clip the lid, put
it in the tray. **Which skill, and where** turns "drive a screw" into this screw,
from this feeder, into that hole. **How to move** is the path that gets the
driver there without hitting the fixture. **How to touch** is the part that
actually decides whether it works: engaging the thread without cross-threading,
and knowing from the torque when it is seated.

In practice the top layer is nearly always programmed, because a person can write
the sequence down in a morning, and the bottom layer is increasingly learned,
because nobody can write down what to do in the last millimetre though they can
demonstrate it. The middle two are contested, and that contest is most of current
robotics research.

Several methods below only ever answer one of the four questions. Comparing a
motion planner with a vision-language-action model is comparing a wheel with a
car.

---

## 4. The family tree

![The family tree of methods](../images/arms-training-methods/overview/taxonomy.svg)

The first split is the one from the introduction: behaviour a person writes,
against behaviour that comes from data. Within the programmed family the
branches run from replaying a recorded motion, through computing motions from a
model, to planning what to do and how to move together. Within the learned
family they are divided by **where the learning signal comes from**: a person's
demonstrations, the robot's own practice, or a large pool of data gathered
elsewhere.

One branch deserves attention up front because it is the quiet workhorse:
*learned pieces inside a programmed system*. Most deployed robots that use
machine learning at all use it that way — a conventional system with one network
doing the perception — rather than the end-to-end approach that gets the
attention.

---

## 5. Programmed: a person writes the behaviour

### 5.1 Teach and replay

An operator drives the arm to a position with a control box called a **teach
pendant**, presses a button to record it, and repeats; the recorded positions are
**waypoints**, and playing them back is the programme. Newer versions let you
push the arm around by hand, which is quicker and is called lead-through or
kinesthetic teaching.

It needs no model, no camera, no simulation and no programmer, and an operator
who knows the job can teach a new motion in an afternoon. Against that, it
assumes the world never changes: move the fixture two centimetres and every
waypoint is wrong.

**Good for:** all of Group A, and the free-space parts of Group B.
**Useless for:** anything in Groups C, D or E, because there is nothing stable to
record against.
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

### 5.2 Offline programming

The same idea done in software: model the workcell as CAD geometry, write the
motion against the model, simulate it to check for collisions, and send the
finished programme to the robot. The reason is economic rather than technical —
teaching by hand stops the production line and this does not.

This is how car bodies get welded. The spot-welding programmes in a body shop are
generated from CAD in tools such as DELMIA, Process Simulate or ABB RobotStudio,
downloaded to the line, and touched up by hand once. There is no sensing and no
learning anywhere in that pipeline, and there does not need to be: the part is in
a jig.

**Good for:** Group A, especially welding and dispensing where the path follows
complicated geometry; and the planned motions of Group B.
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

### 5.3 Scripted logic: state machines and behaviour trees

Real tasks are sequences with conditions: if the gripper is empty, pick; if the
pick failed, retry; if it failed three times, stop and call someone. A **state
machine** is a set of named states with rules for moving between them. A
**behaviour tree** arranges the task as a tree of nodes ticked repeatedly, each
reporting success, failure or "still running", with composite nodes such as "do
these in order until one fails". Behaviour trees came from video games and were
adopted in robotics for the same property: they stay readable at fifty branches,
and you can add a recovery without rewriting the rest.

**Good for:** the sequencing layer of every task in every group, and especially
the twenty-step jobs in Group B and the recovery behaviour Groups C and E need.
**Status in 2026:** standard, and the default answer for the top layer. The only
thing now competing for this job is a language model
([section 10](#10-directed-by-language)), and even then the tree usually remains
underneath as the thing that actually runs.
**Code to look at:** [BehaviorTree.CPP](https://www.behaviortree.dev/)
([repo](https://github.com/BehaviorTree/BehaviorTree.CPP), 4.2k stars, active),
[py_trees](https://py-trees.readthedocs.io/) for the Python and ROS equivalent.

### 5.4 Motion planning

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

**Good for:** Groups A, B and C, and the "how to move" layer of D and E. It is
the piece that lets a system respond to *where things are* rather than replaying
a recording.
**Status in 2026:** standard and healthy. The live development is speed: GPU
planners now replan continuously rather than planning once, which is what lets a
planner sit underneath a learned perception system in a bin picker.
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

### 5.5 Task and motion planning

Sometimes what to do and how to move cannot be separated. To put a mug in the
sink you may first have to move the pan in the way — but whether you must depends
on geometry, and whether you *can* depends on whether a collision-free path
exists for the pan. Task and motion planning, usually shortened to **TAMP**,
searches both at once: a symbolic layer proposes action sequences and a geometric
layer tests whether each is physically achievable, feeding failures back.

**Good for:** in principle, the long rearrangement problems in Groups C and E.
**Status in 2026: research, and used less than its reputation suggests.** It is
the most capable purely-programmed approach for long tasks and also the hardest
to build and the slowest to run, and it needs a symbolic model of your domain
that someone must write. Industrial long-horizon work is done with behaviour
trees instead, and the research energy has largely moved to language models doing
the same sequencing job with less modelling effort.
**Code to look at:** [PDDLStream](https://github.com/caelan/pddlstream) (486
stars, last commit 2023) is the well-documented reference — and its own activity
is a fair indicator of the state of the field.

### 5.6 Feedback control

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

**Good for:** Group B is force control's home: insertion, polishing,
screwdriving. It is also the bottom layer under every learned method, including
the trained ones, because a policy that outputs positions still needs something
underneath that will not snap the part.
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

---

## 6. Learning from demonstrations

Show the task repeatedly and let the learner copy. This is the most practical
learning method for arms today, and this repo works through it in detail in the
[full training](../full-training/overview.md) docs.

### 6.1 Behaviour cloning

A person performs the task while the cameras, the joint angles and the commands
they gave are all recorded. A network is trained to produce the command the
person gave, given what the cameras saw. Nothing about the task is described to
it — not the objects, not the goal, not the physics.

The naive version has been tried since the 1990s and works poorly. Asked for one
command per camera frame, the network is queried fifty times a second, each
answer is a fresh chance to be slightly wrong, the errors compound, and the arm
drifts into situations no demonstrator ever visited. Two developments fixed this
enough to matter.

**Action chunking**: predict the next hundred commands rather than one, and play
them out before looking again. A hundred steps at fifty a second is two seconds
of coherent motion decided in one go, which removes the jitter and keeps two arms
in step with each other. This is what ACT does.

**Generative action models**: demonstrators are inconsistent, and a network
trained to output one number per command averages their different approaches,
where the average of two good motions is often a bad one. Diffusion policies
generate the action sequence the way image models generate pictures, which lets
them represent "either this motion or that one". In 2026 the same job is usually
done by **flow matching**, a faster relative of diffusion, which is the action
head inside every current large policy. It is worth knowing that this is not
settled: a 2026 study
([MINERVA](https://arxiv.org/abs/2609.03715)) found flow matching gave no
detectable advantage over plain regression on its benchmarks while being
several times slower, so the field is optimising a choice it has not fully
justified.

**Where it stops.** Copying works for one skill and falls apart over a long
sequence. FurnitureBench, a benchmark of real IKEA-furniture assembly, is the
honest yardstick: behaviour cloning and offline reinforcement learning complete
none of its full assemblies except the simplest one, and the insertion and
screwing stages mostly fail outright. A twenty-step job needs something above the
policy that sequences and recovers, which is why
[section 10](#10-directed-by-language) exists.

**Good for:** the contact-heavy parts of Group B, and Groups D and E where no
model of the object exists. Laundry folding is the flagship case: nobody can
write down how to flatten a shirt, and demonstrating it is easy.
**Status in 2026:** the default first thing to try for a new learned task.
LeRobot's own documentation calls ACT "our recommended first policy", which is
about cost as much as quality — it trains in under an hour on a single consumer
GPU where a large policy takes a day.
**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) (27.6k
stars, pushed today) is where all of this now lives. Note that the original
implementations are historical: [ACT](https://github.com/tonyzhaozh/act) (2.2k)
has not been touched since 2024, and
[diffusion_policy](https://github.com/real-stanford/diffusion_policy) (4.6k) is
the reference implementation everyone cites and nobody develops. Use LeRobot's
versions. [robomimic](https://github.com/ARISE-Initiative/robomimic) (1.6k)
remains the careful study of which details matter.

### 6.2 Interactive imitation: correcting it as it goes

Behaviour cloning has a structural flaw: the policy only ever saw states a
competent demonstrator put the robot in, so its own small mistakes take it
somewhere unfamiliar, where its next action is worse. The fix is to let it drive
and correct it when it goes wrong, adding those corrections to the data. A few
dozen corrections are often worth several hundred fresh demonstrations, because
they cover exactly the situations the policy actually reaches.

**Good for:** Group B precision work on real hardware, where the last few percent
of reliability is the whole problem.
**Status in 2026:** this is how a good policy is made reliable, and the technique
has merged with reinforcement learning — the human's take-overs become the
learning signal. The published numbers are the best in this whole document:
HIL-SERL reached **100% success on every task it was tried on, after one to two
and a half hours of training on the real robot** — seating RAM in a motherboard,
inserting an SSD and a USB connector, clipping a cable, fitting a timing belt,
assembling IKEA panels and a car dashboard — where the strongest imitation
baseline averaged under 50%. That is a peer-reviewed result in *Science Robotics*
rather than a blog post, which is worth noting in a field where most impressive
numbers are self-reported.
**Code to look at:** [the DAgger paper](https://arxiv.org/abs/1011.0686) for the
original argument; [HIL-SERL](https://hil-serl.github.io/)
([repo](https://github.com/rail-berkeley/hil-serl), 1.5k stars) for the modern
system, now shipped inside LeRobot. Its predecessor SERL is formally deprecated
in favour of it.

### 6.3 Learning the goal instead of the motion

Rather than copy what the demonstrator did, infer what they were *trying to
achieve* and optimise that — inverse reinforcement learning, with relatives in
adversarial imitation and learning from preferences.

**Status in 2026: a minority approach for arms.** The generality is real and so
is the fragility, and the flagship open library
([imitation](https://github.com/HumanCompatibleAI/imitation), 1.8k stars) has had
no commits since January 2025, though surveys still treat the family as live. The
preference-learning branch found its real home tuning language models rather than
arms. Read [GAIL](https://arxiv.org/abs/1606.03476) and
[learning from human preferences](https://arxiv.org/abs/1706.03741) for the ideas;
do not expect to meet them in a working arm system.

---

## 7. Learning from trial and error

Reinforcement learning takes the opposite input: instead of demonstrations you
supply a **reward**, a number saying how well things are going, and the robot
tries, observes, and adjusts. The appeal is that you need not be able to do the
task, only to recognise success. The difficulties are that writing a reward is
genuinely hard — any gap between what you wrote and what you meant gets found and
exploited — and that learning from scratch takes millions of attempts, which no
real arm survives, so in practice it means simulation.

Four branches behave differently enough to separate:

**Model-free** (PPO, SAC) learns directly from experience with no model of the
world: simple, general, and hungry. **Model-based** (Dreamer, TD-MPC) learns a
model first and plans or trains inside it: far more sample-efficient, more moving
parts. **Offline** (IQL, CQL) learns from a fixed pile of recorded behaviour with
no practising at all. **Real-world** RL practises on the actual robot, which
solves the fidelity problem and creates every other one.

Crossing from simulation to reality is its own subject, and the dominant
technique is **domain randomisation**: rather than build one accurate simulator,
train across thousands of randomised ones — friction, mass, lighting, delays — so
the real world is one more variation.

The clearest evidence that this works on arms comes from insertion. NVIDIA's
[IndustReal](https://github.com/NVLabs/industrealkit) line trained entirely in
simulation and transferred to a real Franka with no real-world data at all,
reaching 83–99% across 600 trials on parts modelled on a standard assembly test
board, and its successor FORGE improved gear meshing to 98% and nut threading to
69% while halving contact forces. Read the caveats, because they are the
interesting part: the authors deliberately used **no force-torque sensor**,
relying on vision and joint positions, because such sensors are "costly, noisy
and fragile"; the clearances were half a millimetre, which is looser than real
connectors; and none of it is deployed in a factory.

**Good for:** Group B contact skills you can simulate and score, above all
insertion; and in-hand dexterity generally. It is also the only option when you
cannot demonstrate the task at all.
**Status in 2026, and this has changed recently:** training a policy from scratch
with RL is now the exception. The tooling tells the story — LeRobot ships around
twenty pretrained and imitation policies against two RL entries. What RL is
increasingly used for is **fine-tuning a policy that was first trained from
demonstrations**, which is [section 8](#8-learning-from-large-scale-pretraining).
Offline RL followed the same path: its benchmark suite was formally deprecated,
and its algorithms reappeared as components inside policy post-training.
**One deprecation worth knowing:** Isaac Gym, the GPU simulator many RL papers
used, is officially legacy — NVIDIA's own page says it "is no longer supported"
and points at [Isaac Lab](https://isaac-sim.github.io/IsaacLab/) (8.2k stars,
pushed today). If you meet a tutorial using Isaac Gym, it is out of date.
**Code to look at:** [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
(13.8k) for the algorithms themselves;
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) (2.2k)
for where the practising happens; the
[domain randomisation paper](https://arxiv.org/abs/1703.06907), which is short
and worth reading in full; and [HIL-SERL](https://github.com/rail-berkeley/hil-serl)
for RL on a real arm.

---

## 8. Learning from large-scale pretraining

The newest branch borrows the strategy that worked for language. Rather than
train a model for your task, train one large model on as much robot data as
exists — pooled across many robots and many tasks — then adapt it to your task
with comparatively few examples. These are **vision-language-action models**, or
VLAs: camera images and a sentence in, arm commands out. The instruction is what
lets one model cover many tasks.

**Good for:** Groups C and D, and any situation where you want one policy to do
several tasks rather than one policy per task. This is where laundry folding and
household clutter have produced their most convincing demonstrations.
**Status in 2026: the frontier, and moving fast enough that specific model names
date quickly.** Three things are worth knowing rather than any particular model.

First, **what is open and what is not.** The openly released models are π₀,
π₀-FAST and π₀.₅ from [openpi](https://github.com/Physical-Intelligence/openpi)
(13.9k stars, Apache-2.0) and
[GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T) (8.1k), which is the current
version of that line — N1.5 and N1.6 are no longer maintained. The models these
groups have published since, including Physical Intelligence's π\*0.6 and π0.7,
have **no released code or weights**, so read about them but do not plan on using
them.

Second, **the previous generation is already historical.** RT-1 is archived, RT-2
never released code or weights at all, and Octo has had no commits since mid-2024.
[OpenVLA](https://github.com/openvla/openvla) (7.0k) is the interesting case: it
is still the most-downloaded robotics model and the baseline in most papers, yet
it has had no commits since March 2025 and is absent from LeRobot's policy list.
It is a reference point, not a foundation to build on.

Third, **the 2026 recipe for a hard task is a pipeline, not a model**: fine-tune
a pretrained policy on roughly fifty demonstrations, run it with real-time
chunking so a slow model produces smooth motion, and then use a short burst of
reinforcement learning on the real robot to sharpen the precise phase. Physical
Intelligence reported exactly this on tasks from Group B — driving screws,
fitting zip ties, inserting Ethernet and power connectors — with about fifteen
minutes of real-world data and roughly two hours including resets, reaching up to
three times faster execution and beating human teleoperation on one of them. That
work is not released; the open equivalent of its last stage is HIL-SERL inside
LeRobot, and in simulation
[SimpleVLA-RL](https://github.com/PRIME-RL/SimpleVLA-RL) (1.9k, MIT).

That recipe is worth taking seriously because it turned up four separate times in
a single year, from four different groups, on four different tasks: on laundry and
box assembly, on shoe-lacing (where success went from 46% to 83% after about 150
episodes of practice), on precision insertion, and in the winning entry of a
garment-folding competition, which built on the open π₀.₅ and added a
reinforcement-learning loop. When independent groups converge on the same shape
of solution, that shape is the current state of the art.

Fourth, **be careful to separate demonstrations from deployment.** Almost every
headline VLA result is self-reported by the company that trained the model, and
graded on a rubric rather than as a plain success rate. The most useful public
data point is smaller and more honest: a logistics company put a VLA into
production picking for an e-commerce customer in 2026 and reported that it roughly
halved the rate of robot-caused interventions — while stating plainly that their
VLAs are not at 99.9% success on their own, that nobody's customer-deployed VLAs
are, and that a classical stack sits around the model as a "harness" catching its
errors and enforcing safety. That is the accurate picture of VLAs in production
today. The most rigorous evaluation anyone has published, from Toyota Research
Institute in *Science Robotics*, points the same way: across 1,800 real rollouts
and 47,000 simulated ones, large-scale pretraining bought a genuine three-to-five
fold improvement in data efficiency, and yet the pretrained model beat
single-task baselines on only about half the tasks tested — with the authors
warning that much of the field may be measuring statistical noise.

**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) again, which
now hosts about twenty policies including the open VLAs, plus
[openpi](https://github.com/Physical-Intelligence/openpi) and
[Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) for the models themselves.

---

## 9. Learned pieces inside a programmed system

The least glamorous branch, and by a wide margin the most deployed. Keep the
classical system — planner, controller, logic — and replace only the parts that
require recognising something.

**Where to grasp.** Given a point cloud of a cluttered bin, a network proposes
places the gripper could close successfully, ranked; a conventional planner
executes the best reachable one. It works on objects the system has never seen,
because the network learned what grippable geometry looks like in general.

**What the object is, and where.** Segmentation says which pixels belong to which
object; pose estimation says how it is oriented. The recent generation does this
without being trained on your specific object, which removed the step that used
to make the approach impractical.

**Whether something will work.** A learned model that scores candidates the
planner generated — will this grasp hold, will this stack stay up — is often the
highest-value learning in a system, because the classical part can generate
thousands of candidates and only needs help choosing.

**The best evidence in this whole document is for this branch.** Amazon published
a detailed account of a system that packs items into fabric storage pods, after
more than half a million real stows in a working fulfilment centre. It reports
**85.86% success over 100,000 attempts**, with the failures broken out honestly —
9.31% unproductive cycles, 3.77% dropped items, 0.24% damage — and a rate of 224
units per hour against 243 for the humans working the same floor. Most usefully,
it says exactly which parts are learned and which are not: **learned** are the
depth estimation, the segmentation, the product identification and the models that
score risk and estimate free space; **classical** are the motion planning, the
grasp planning, the force control and a hand-written library of primitives with
names like "approach", "extend blade", "sweep" and "eject item". That is the
shape of essentially every deployed system that uses machine learning on an arm.

**Good for:** Group C above all — this is what made bin picking of mixed items a
product rather than a demo — and the perception layer of Groups D and E.
**Status in 2026:** deployed and mature, and the default way to add learning to a
working system. But note the split carefully, because it is widely got wrong:
**if you know the part, the industry still matches its CAD model**, and the major
3D-vision vendors describe their products in exactly those terms, because a model
match gives a full six-degree-of-freedom pose with a geometric residual you can
check. Learned grasp proposal took over for **unknown or mixed items**, where
there is no model to match. Both are current; which you use is decided by whether
the object is in your catalogue. Either way the system stays inspectable: when it
fails you can look at the proposed grasps, the estimated pose and the planned
path and see which was wrong.

The published numbers for unknown-object picking are strong. AnyGrasp reported
clearing bins of over 300 unseen objects at 93.3% success and more than 900 mean
picks per hour, described as on a par with human subjects; Dex-Net 4.0 reported
over 95% reliability at over 300 picks per hour on bins of novel objects. It is
also worth knowing that **no paper anywhere reports a head-to-head of a general
vision-language-action model against one of these pipelines on cluttered bin
picking**. The modular approach wins here by the absence of a challenger rather
than by a measured victory.

**Code to look at, with a health warning.** This corner of open source has aged
badly and the well-known repositories are mostly frozen:
[Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) (532 stars) has
not been touched since 2024 and depends on a long-dead TensorFlow generation;
[GraspNet-1Billion](https://graspnet.net/) (1.0k) is most valuable as a dataset
and benchmark; Dex-Net and its `gqcnn` implementation have been dead since 2022;
and the one with real commercial traction, AnyGrasp, ships as a licence-gated
binary and is **not open source** despite appearances. Treat these as concepts and
data rather than as things to build on. The current research line is diffusion
models that generate grasps, of which NVIDIA's `GraspGen` is the notable example —
visible source, but under a research licence rather than a permissive one. For the
pieces that are genuinely maintained, use
[FoundationPose](https://github.com/NVlabs/FoundationPose) (3.6k) for pose
estimation without per-object training and
[Segment Anything](https://github.com/facebookresearch/segment-anything) (54.9k)
for segmentation.

---

## 10. Directed by language

The last branch does not produce motion at all: it chooses what to do, sitting
above whatever does produce motion. A language model is given the task in words,
told what skills the robot has, and asked to decide the order of the steps.

This works better than it sounds, because sequencing a familiar task is a
knowledge problem rather than a physical one, and knowledge is what a model
trained on the internet has. What it does not know is what this particular robot
can reach, which is why the useful designs pair its suggestions with the robot's
own estimate of whether each step is achievable and let the two vote.

Three shapes are worth knowing. The model can **propose steps** that learned
skills execute; it can **write code** that calls the robot's perception and
control functions, which is pleasantly debuggable because the output is a short
program you can read; or it can **produce spatial goals** that a conventional
planner uses.

**Good for:** the sequencing layer of long tasks in Groups C, D and E —
especially household-style work where the instruction varies. For Group B, where
the sequence is fixed and known, a behaviour tree remains the better answer: it
is deterministic and free.
**Status in 2026:** established in research, appearing in products for
high-level task selection rather than for anything safety-critical. The
sequencing layer is also being absorbed into the large policies themselves, which
take an instruction directly.
**Code to look at:** [SayCan](https://say-can.github.io/),
[Code as Policies](https://code-as-policies.github.io/) and
[VoxPoser](https://voxposer.github.io/) for the three shapes;
[Inner Monologue](https://innermonologue.github.io/) for feeding failures back so
the model can replan.

---

## 11. Which method for which task

The direct answer to "is this the right method for this task". Read a row to plan
a system; read a column to see where a method earns its keep.

**★** the usual choice today · **✓** used, and works · **~** emerging, or used in
part · **–** not used

| Task | Teach / offline | Motion planning | Force control | Learned perception | Imitation | RL in sim | Real-robot RL | VLA | Language planner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Welding, painting, dispensing** | ★ | ✓ | ~ | – | – | – | – | – | – |
| **A. Machine tending** | ★ | ✓ | – | ~ | – | – | – | – | – |
| **A. Palletising** | ★ | ✓ | – | ~ | – | – | – | – | – |
| **A. Lab sample handling** | ★ | ✓ | ~ | ~ | – | – | – | – | – |
| **B. Screwdriving and packing** | ★ | ✓ | ★ | ✓ | ~ | ~ | ~ | – | – |
| **B. Connector insertion** | ✓ | ✓ | ★ | ✓ | ✓ | ★ | ★ | ~ | – |
| **B. Polishing, deburring** | ✓ | ✓ | ★ | ~ | ~ | ~ | ~ | – | – |
| **B. Kitting** | ✓ | ★ | ~ | ★ | ~ | – | – | ~ | ~ |
| **C. Bin picking, mixed** | – | ★ | ~ | ★ | ~ | ~ | – | ~ | – |
| **C. Parcel and waste sorting** | – | ★ | – | ★ | ~ | – | – | ~ | – |
| **C. Dishwasher unloading** | – | ✓ | ✓ | ✓ | ★ | – | – | ★ | ✓ |
| **D. Laundry folding** | – | ~ | ✓ | ✓ | ★ | ~ | ~ | ★ | ~ |
| **D. Cable routing** | ~ | ✓ | ★ | ✓ | ✓ | ~ | ~ | ~ | – |
| **D. Food handling** | ~ | ✓ | ✓ | ★ | ✓ | – | – | ~ | – |
| **E. Stacking irregular stones** | – | ★ | ★ | ✓ | ~ | ~ | ~ | – | ~ |
| **E. Building from rubble** | – | ★ | ✓ | ✓ | ~ | ~ | – | – | ~ |

Three things fall out of the grid.

**The left-hand columns own Group A completely.** No learned method has any
business in a welding cell: the environment is fixed, and a recording is the
correct answer. If someone proposes machine learning for a Group A task, they are
solving a problem that does not exist.

**Group B is where the two families meet.** Force control does the work today,
learned methods are arriving specifically for the precise phase, and the 2026
approach — demonstrations to get the shape of the task, then a short burst of
reinforcement learning to make it reliable — was demonstrated on exactly these
jobs. This is the group to watch if you care about manufacturing.

**Groups D and E cannot be done any other way.** There is no CAD model of a
shirt, and no published system folds laundry by planning. Where the object cannot
be described, learning is not an improvement but the only option.

---

## 12. The four worked examples

Taking the four tasks from the top of this page and answering them directly.

**Picking screws, fitting parts, screwing, and packing the component** — the
known-environment assembly job. Programme almost all of it: the sequence as a
behaviour tree, the motions offline against the CAD model, and the screwdriving
with torque and force control, which is what actually decides success. Add
learned perception only if the parts arrive unfixtured. Consider a learned policy
only for a step that keeps failing on contact — cross-threading, or a connector
that will not seat — and then the modern recipe is demonstrations followed by a
short reinforcement-learning burst on the real robot rather than a policy for the
whole job. A single policy trained end to end for twenty steps is the wrong shape,
and there is evidence rather than just intuition behind that: on a benchmark of
real furniture assembly, end-to-end learned policies complete none of the full
assemblies except the very simplest. The sequence is free to write and expensive
to learn.

There is one genuinely deployed learned product in this class worth knowing about.
Micropsi's MIRAI is trained by demonstration over a few days, needs no CAD model
and no camera calibration, runs on ordinary industrial and collaborative arms, and
adjusts the path in real time from camera images; its published customers include a
turbine maker, an appliance maker and a screwdriving-equipment manufacturer. The
detail that makes it instructive is that it can train and run most skills **without
a force-torque sensor** — so what it learned is how to absorb positional variance
and remove fixturing, not how to handle contact. The contact is still force
control underneath. That is a fair summary of where learning has genuinely reached
the factory floor for this task.

**Laundry folding.** Nothing programmed will do this, because there is no model
of the object. The demonstrated approach is a large pretrained policy fine-tuned
on many demonstrations and then improved by practice on the robot, and the
best-reported systems are all closed. The open ones are genuinely usable though:
the winning entry of a 2026 garment-folding competition released its code and
checkpoints, having built on the open π₀.₅ and added a reinforcement-learning
loop over roughly twelve thousand practice episodes, and at least one open
specialist policy reports over 90% on real shirts, skirts, trousers and towels.
Worth knowing as a counterweight: a 2022 system built the classical way —
perception plus planning, with the fold lines given to it — reported 93% success
at thirty to forty folds an hour from a crumpled start. Nobody has run the two
approaches against each other on the same garments, so "learning won here" is the
direction of travel rather than a measured result.

**Welding on an assembly line.** Teach or offline-programme it. This is Group A,
it has been solved since the 1980s, and the interesting engineering is in
fixtures, seam tracking and cycle time rather than in method choice. The major
vendors' arc-welding products list no machine learning at all; variation is
handled by through-arc and laser seam tracking, which are sensing rather than
learning. The one genuinely AI-forward direction is scan-to-weld — generate the
path from a scan of the actual part, with no CAD and no teaching — and even there
the honest vendors describe themselves as looking for integrators rather than as
deployed at scale.

**Placing rocks one on top of another.** The
[stone stacking doc](../stone-stacking.md) works this through in full. Short
version: the choice of where to place is best answered by searching candidate
poses in a physics engine rather than by learning; the perception — turning rough
stones into shapes — is best learned; and the placement and release want force
control, with a learned policy as a reasonable option for that last centimetre.

This is the one task on the list where the classical approach is still clearly
ahead, and the evidence is large. An ETH Zurich team put this pipeline on an
autonomous walking excavator and built a **six-metre-high, sixty-five-metre-long
dry-stone wall** out of boulders and demolition debris found on the site: scan
each stone, estimate its weight and centre of gravity, search for a placement,
plan, place. No learned policy anywhere. Learning is only now arriving — a 2026
result used a physics-guided diffusion model to choose placements and reported
being both more robust to disturbance and faster than the geometric method — but
that one is simulation-only with no code released. If you want to stack irregular
objects today, search over scanned geometry.

---

## 13. What is current, and what is fading

Methods rarely die of old age; they are displaced by something that needs less of
what is expensive. This chart is a rough guide to when each became common and
which are now on the way out.

![Roughly when each method became common, and which are fading](../images/arms-training-methods/overview/timeline.svg)

**Clearly superseded, with the evidence.** Isaac Gym, the GPU simulator behind
many reinforcement learning papers, is marked legacy by NVIDIA and its example
repository is archived; Isaac Lab replaced it. The D4RL benchmark suite that
offline reinforcement learning was measured on was formally deprecated in favour
of Minari, and its canonical baseline implementations are archived. SERL was
deprecated by its own authors in favour of HIL-SERL. RT-1 is archived and RT-2
never released code. OpenAI Gym was archived in favour of Gymnasium, and ROS 1
reached end of life in May 2025. Hand-designed visual features were displaced by
learned perception a decade ago, and computing grasps from CAD models has been
displaced **for mixed-item picking** by learned grasp proposal — though not for
known parts, where model matching is still the standard product and the right
engineering choice.

**Quietly fading rather than deprecated.** Several important repositories have
simply stopped: the original ACT implementation has had no commits since 2024,
diffusion_policy since late 2024, Octo since mid-2024, and OpenVLA since March
2025. None carries a deprecation notice. The work moved into LeRobot, which is
where those methods now live and are maintained. The same has happened to the
classical grasping repositories — Contact-GraspNet, the GraspNet baseline,
Dex-Net and `gqcnn` are all quiet or dead — and to PyBullet, which has an enormous
tutorial legacy and about one commit a year. On the industrial side, the
ROS-Industrial vendor drivers for FANUC, Motoman, ABB and KUKA are all dormant
ROS 1 code, and there is **no maintained open-source ROS 2 driver for FANUC or
Motoman at all**, which is a genuine gap rather than an oversight. The calibration
tool most tutorials still recommend, `moveit_calibration`, has had no commits in
a year; use `industrial_calibration` or OpenCV's hand-eye function directly.

**Used less than its reputation suggests.** Task and motion planning remains
largely a research technique. Inverse reinforcement learning and adversarial
imitation are a minority approach for arms, and their main open library has been
untouched since early 2025 — though surveys still treat the family as live, so
"declining" is fairer than "dead".

**The newest things, which a doc written in 2024 would miss entirely.**
Reinforcement learning used to sharpen an already-trained policy rather than to
train one from scratch. World-model policies, which learn to predict what will
happen and act through that prediction, now a first-class category in LeRobot but
not yet proven on production arms. Training on large amounts of ordinary human
video rather than robot demonstrations, where the scaling behaviour looks
promising and almost nothing has been released. Verification at run time — trying
several candidate actions and checking them — where at least one 2026 result
claims that scaling the checking beats scaling the policy. And tactile
foundation models, trained across many different touch sensors at once.

Treat that last paragraph as a weather report rather than a forecast: these are
months old, mostly unreleased, and several will not survive contact with real
deployments.

---

## 14. What each method costs you

The same eight families on twenty points, which is the practical question once
you know which methods could work.

**How to read it.** Rows 1 to 10 are what a method demands before it will work at
all, which is usually what settles the matter. Rows 11 to 20 are what you get
back. "Somewhat" means it copes with variation of a kind it has seen, but not
with a new kind; "deployed widely" means you can buy it, "research" means you
would build it from papers.

**What it asks of you**

| | Teach & replay | Offline prog. + planner | TAMP | Classical control | Imitation | RL (sim → real) | VLA fine-tune | Learned pieces in a classical stack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **1. What you must supply** | the motion | a CAD model | symbolic rules + geometry | a model of the robot | demonstrations | a reward | demonstrations | labelled data, or a ready model |
| **2. Robot model needed** | no | yes | yes | yes | no | yes, for the simulator | no | no |
| **3. Demonstrations needed** | one, by hand | none | none | none | 50–1000+ | none | 10–500 | none |
| **4. Reward needed** | no | no | no | no | no | yes, and it is the hard part | no | no |
| **5. Simulator needed** | no | helpful | helpful | helpful | no | yes, in practice | no | no |
| **6. Training compute** | none | none | none | none | hours on one GPU | days, many GPUs | hours to days | hours |
| **7. Compute when running** | trivial | milliseconds to seconds | seconds or more | trivial | one network pass | one network pass | a large network pass | one network pass |
| **8. Time to something working** | hours | days | weeks | days | weeks | weeks to months | days, if a checkpoint fits | days |
| **9. Who has to be skilled** | an operator | a robot programmer | a researcher | a control engineer | anyone who can do the task | an RL practitioner | an ML engineer | an ML engineer |
| **10. Cost of a change later** | re-teach it | re-programme it | re-model it | re-tune it | collect more data | re-train and re-tune the reward | fine-tune again | retrain one component |

**What you get**

| | Teach & replay | Offline prog. + planner | TAMP | Classical control | Imitation | RL (sim → real) | VLA fine-tune | Learned pieces in a classical stack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **11. Objects it has never seen** | no | no | limited | no | somewhat | somewhat | best of these | yes, that is the point |
| **12. Contact-rich work** | poor | poor | poor | good | good | good | good | not applicable |
| **13. Long multi-step tasks** | yes, if nothing varies | yes | yes, by design | no | poor | poor | improving | not applicable |
| **14. A new task without new code** | no | no | partly | no | no | no | partly | no |
| **15. A scene arranged differently** | no | no | yes | not applicable | somewhat | somewhat | yes | yes |
| **16. Can you see why it failed** | yes | yes | yes | yes | no | no | no | partly |
| **17. Can it be verified for safety** | yes | yes | mostly | yes | weak | weak | weak | inherits the stack's |
| **18. Risk while it is learning** | none | none | none | none | none, it is offline | high on real hardware | none | none |
| **19. Industrial maturity in 2026** | decades | decades | research | decades | early deployment | niche | early | deployed widely |
| **20. How it typically fails** | the part moved | reality differed from the model | no plan found, or too slow | the model was wrong | drifts into unseen states | will not transfer from simulation | confidently wrong | one component's blind spot |

Read rows 16 and 19 together and the industrial picture explains itself: the
methods you can debug are the methods industry adopted, because a factory must
know why a machine stopped. Read rows 11 to 13 for the mirror image: the methods
that cope with novelty and contact are the learned ones, and those are the tasks
nobody has automated. The field is working in the gap between those two facts.

---

## 15. What real systems actually do

Almost nothing real uses one method. A few worth understanding properly.

**A modern bin-picking cell** is a classical system with one learned component.
Planning, collision checking and gripper logic are conventional code; a network
proposes grasps. The objects vary so perception must generalise; the motion does
not, so it stays verifiable. Amazon's published account of its item-stowing
system, with the learned and classical parts listed separately, is the best
worked example of this split anyone has released.

**MIT's Jenga robot** inverts the usual assumption about what to learn. The
strategy and the controller are conventional; what is learned is a model of how
the block responds to being pushed, from vision and force together — the part
nobody can write down.

**MimicGen and its two-arm successor DexMimicGen** use programming to
*manufacture the data that training needs*: a classical routine turns a handful
of demonstrations into thousands by re-composing them around the objects'
positions, and a policy is then trained on that.

**SayCan** pairs a language model with learned skills, and the contribution is
the pairing. The model knows a spill needs a sponge; it has no idea whether the
robot can reach the sponge. Each skill carries a learned estimate of its own
chance of success, and the step chosen must be both sensible and feasible.

**Figure's Helix** splits by speed: a vision-language model at 7–9 Hz to
understand the scene, and a separate visuomotor policy at 200 Hz to move.
Thinking and reacting have different timescales, so they are different models.

| System | Programmed part | Learned part | Why the split falls there |
| --- | --- | --- | --- |
| Typical industrial cell | taught or offline path, force control on insertion | often nothing | nothing varies, so learning buys little and costs verification |
| Bin picking, modern | planning, collision checking, gripper logic | grasp proposals, segmentation | objects vary, motions do not |
| [Amazon item stowing](https://arxiv.org/abs/2505.04572) | motion planning, grasp planning, force control, a library of named primitives | depth, segmentation, product identity, risk and free-space scoring | 500,000 real stows; 85.86% success; the split is stated by the authors |
| [Micropsi MIRAI](https://www.micropsi-industries.com/) | the force control underneath | a visuomotor skill trained by demonstration in days | learning removes positional variance; force control still handles contact |
| [ETH HEAP dry-stone wall](https://ethz.ch/en/news-and-events/eth-news/news/2023/11/autonomous-excavator-constructs-a-six-metre-high-dry-stone-wall.html) | all of it: scan, estimate mass, search poses, plan, place | nothing | a 6 m × 65 m wall from found boulders, with no learned policy anywhere |
| [MIT Jenga](https://news.mit.edu/2019/robot-jenga-0130) | strategy and control | a model of contact, from vision and force | contact is what cannot be written down |
| [MimicGen](https://mimicgen.github.io/) / [DexMimicGen](https://dexmimicgen.github.io) | the routine that multiplies demonstrations | the final policy, by imitation | programming manufactures the data training needs |
| [RoboTwin 2.0](https://github.com/RoboTwin-Platform/RoboTwin) | expert data generation, randomisation, evaluation | the policies under test | the benchmark is programmed, the subject is learned |
| [SayCan](https://say-can.github.io/) | the skill interfaces | the planner, the skills, and the feasibility estimates | the planner must know what is possible |
| [Code as Policies](https://code-as-policies.github.io/) | perception and control functions | a language model writes the glue | composition is language-shaped, primitives are not |
| [OpenAI's cube-solving hand](https://arxiv.org/abs/1910.07113) | the cube solver, a classical algorithm | in-hand finger motion, RL in simulation with heavy randomisation | solving the cube was solved; moving fingers was not |
| [HIL-SERL](https://hil-serl.github.io/) | safety limits, resets, the controller underneath | RL on the real robot, with human take-overs | real contact cannot be simulated well enough |
| [Figure's Helix](https://www.figure.ai/news/helix) | the low-level stack | a VLM at 7–9 Hz, a visuomotor policy at 200 Hz | thinking and reacting run at different rates |
| [TRI's Large Behavior Models](https://toyotaresearchinstitute.github.io/lbm1/) | data collection and evaluation | one diffusion model pretrained on ~1,700 hours, fine-tuned per task | pretraining reportedly cuts the data a new task needs several-fold |
| [ALOHA / ACT](https://tonyzhaozh.github.io/aloha/) | almost nothing above the controller | the entire task, from 50 demonstrations | the counter-example: sometimes copying is enough |

---

## 16. Where this repo fits

Nearly everything here sits in the programmed family, deliberately: the learned
methods are easier to understand once you know what they replace, and the pieces
they assume — frames, transforms, depth pictures, message passing — are the same
either way.

- [ROS basics](../ros/ros-basics.md) is the plumbing every method above runs on.
- [The arm area](../arm/overview.md) covers frames, transforms and kinematics:
  the model classical methods need explicitly and learned ones absorb implicitly.
- [The camera area](../camera/basics.md) and
  [finding objects](../camera/finding-objects.md) show a classical perception
  pipeline and a trained model doing the same job, which is the smallest clear
  illustration of the trade this whole doc is about.
- [Two-arm manipulation](../two-arm-manipulation.md) lists the open projects for
  the learned family, in five steps.
- [Stone stacking](../stone-stacking.md) and
  [full training](../full-training/overview.md) take one task and work it through
  the programmed way and then the trained way.

**How to read the numbers in this doc.** Robotics reporting is unusually
unreliable, so it is worth knowing which claims here carry weight. The strongest
are peer-reviewed with the trial counts published: the 100% insertion results from
one to two and a half hours of real-robot practice, the 85.86% over a hundred
thousand real stows, the sixty-five-metre dry-stone wall, the benchmark showing
end-to-end policies failing at furniture assembly, and the evaluation across 1,800
real rollouts whose authors warn that much of the field is measuring noise.
Weaker, and marked as such above, are company blog posts — every "2× throughput"
and "99% accuracy" in this area is self-reported, usually without a denominator.
And at least one very widely repeated statistic, the claim that over 90% of
industrial robots are teach-pendant programmed, traces to a single undated page
that no longer exists; it is not used here.

**What was checked, and when.** The repository statistics, licences and activity
dates in this doc were read from the GitHub API on 19 September 2026, and the
deprecation claims come from the projects' own notices rather than from
summaries. None of the external systems described here were run in this repo; the
links go to the people who built them. Everything inside the repo has been run,
and each doc says so. Project lists go stale quickly — before relying on anything
here, check the licence and the last commit date yourself.
