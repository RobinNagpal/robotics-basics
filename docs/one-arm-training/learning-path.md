# A learning path for robot arms, in simulation

The rest of this folder explains what the methods are and why the field moves the
way it does. This document is the practical companion to all of it: **five complete
projects, each of which you build four times**, starting from something you write by
hand and ending at the 2026 frontier.

Two things about that shape are deliberate, and they are what makes this different
from a list of exercises.

**Every project is a whole system, not a step.** Each one has a camera or two, a
motion, a grasp, and a way of telling whether it worked. That matters because the
interesting problems in robotics live in the joins between those things, and an
exercise that only moves a joint hides every one of them. A project you can
describe to somebody else — "it tidies a desk" — is also a project you can put in
front of a client.

**Every project is then rebuilt, three more times.** The first version is written by
hand. The second replaces the perception with something learned. The third replaces
a skill with something learned. The fourth is whatever the field is currently
excited about. Building the *same* task four ways is the fastest honest way to form
an opinion about which methods actually earn their keep, because you are comparing
on a problem you understand rather than on somebody's benchmark.

Working only in simulation is also deliberate. Everything that makes robot hardware
slow to learn from — the wiring, the calibration, the safety, resetting the
workspace between attempts — is absent, while almost everything that makes the
*software* hard is still there. You will still have to work out why the planner
cannot find a path, why the gripper jams, and why the policy drifts away on the
fourth attempt.

## Contents

1. [The five projects at a glance](#the-five-projects-at-a-glance)
2. [Why MuJoCo and Gazebo, and why both](#why-mujoco-and-gazebo-and-why-both)
3. [Project 1: tidy the desk](#project-1-tidy-the-desk)
4. [Project 2: fit the connector](#project-2-fit-the-connector)
5. [Project 3: empty the bin](#project-3-empty-the-bin)
6. [Project 4: copy it from video](#project-4-copy-it-from-video)
7. [Project 5: build the kit](#project-5-build-the-kit)
8. [Where the cloud actually helps](#where-the-cloud-actually-helps)
9. [What this path deliberately leaves out](#what-this-path-deliberately-leaves-out)

---

## The five projects at a glance

![Five projects, each built four times, and where the Mac stops](../images/one-arm-training/learning-path/learning-path.svg)

| Project | What it does | Its character | Simulator |
| --- | --- | --- | --- |
| **1. Tidy the desk** | sorts a tabletop of mixed objects into bins | mostly programmed, the classical cell | Gazebo |
| **2. Fit the connector** | mates a plug into a socket it cannot see | contact and force, then learning on top | MuJoCo |
| **3. Empty the bin** | picks mixed objects out of a cluttered bin | perception-heavy, the deployed pattern | Gazebo |
| **4. Copy it from video** | learns a task from a video of your own hand | learning from human video, the frontier | MuJoCo |
| **5. Build the kit** | assembles five parts in order, and recovers | long-horizon sequencing, programmed against learned | both |

Every project, at every layer, involves **one or two cameras, a planned motion, a
grasp, and an evaluation over enough trials to mean something**. That repetition is
on purpose: by project five those four things are muscle memory, and your attention
is free for what is actually new.

The four layers are the same each time:

| Layer | What changes | Typically |
| --- | --- | --- |
| **1. Written by hand** | you write every rule | a planner, a controller and a behaviour tree |
| **2. One learned piece** | perception becomes a model | a network recognises, ordinary code decides |
| **3. A learned skill** | a behaviour becomes a policy | demonstrations replace a hand-written skill |
| **4. The 2026 frontier** | whatever the field is betting on | pretrained policies, language, practice |

## Why MuJoCo and Gazebo, and why both

Newcomers usually assume that picking a simulator is like picking a text editor, so
that learning two of them is wasted effort. It is not, because these two are built
for different jobs.

**[Gazebo](https://github.com/gazebosim/gz-sim) is for simulating a robot
*system*.** It speaks ROS 2 natively through
[ros_gz](https://github.com/gazebosim/ros_gz), it simulates sensors properly — depth
cameras, colour cameras, lidar, with noise — and it runs the same
[`ros2_control`](https://control.ros.org/jazzy/index.html) controllers a real arm
would run, through [`gz_ros2_control`](https://github.com/ros-controls/gz_ros2_control).
That last point is what matters: the controller code you write against Gazebo is
the controller code you would ship. When the thing you are testing is the plumbing —
topics, frames, controllers, cameras, launch files — Gazebo is the right tool, which
is why projects 1, 3 and 5 live there.

**[MuJoCo](https://github.com/google-deepmind/mujoco) is for simulating *physics
and policies*.** It was built for contact-rich simulation and for machine learning,
it is fast enough to run many thousands of steps a second, and essentially every
imitation-learning benchmark in this folder is written against it. When the thing
you are testing is a controller's response to contact, or a policy, MuJoCo is the
right tool, which is why projects 2 and 4 live there.

They also fail differently, and comparing them teaches you something neither teaches
alone. A model that behaves in Gazebo and misbehaves in MuJoCo is usually telling
you that your contact parameters are fiction. A controller that works in MuJoCo and
falls apart in Gazebo is usually telling you that your real problem is timing or
message plumbing rather than physics.

### What that means on a Mac, honestly

MuJoCo is the easy half. It publishes native Apple Silicon builds and a native
viewer, and nothing about it is second-class. One wrinkle catches everybody: macOS
insists that rendering happens on the main thread, so the interactive viewer must be
started with the `mjpython` launcher rather than with `python`. If you would rather
avoid that, [mjviser](https://pypi.org/project/mjviser/) renders MuJoCo in a browser
instead.

Gazebo is the awkward half, and it is worth knowing before you lose an evening. It
does work — this repository already runs Gazebo Harmonic on this machine for
[the camera area](../camera/basics.md) — but macOS is a best-effort platform with no
Apple Silicon testing behind it. **Install it through conda rather than Homebrew**,
because Gazebo's own documentation points at Homebrew and there is no prebuilt
Homebrew package for the version that pairs with ROS 2 Jazzy, so that route means
compiling the whole stack from source. And **the graphical window and the physics
server cannot share a process on macOS**, so you start them as two commands; this
has been [an open issue since 2019](https://github.com/gazebosim/gz-sim/issues/44).

The ROS 2 pieces are in better shape than their reputation suggests. MoveIt 2,
RViz2 and `ros2_control` all publish Apple Silicon builds, and the crashes that made
them painful were fixed through 2025 and early 2026. Prefer the Cyclone DDS
middleware over the default, which still has an open thread-affinity bug on recent
macOS.

---

## Project 1: tidy the desk

**What you are building.** A cell that looks at a tabletop covered with a dozen
mixed objects — pens, mugs, tools, small boxes — and sorts them into three bins by
category. It runs unattended until the table is clear, and it does not stop when one
grasp fails.

**Why this one first.** It is the complete classical cell in miniature, and it is
the shape of an enormous fraction of real deployed robot work. It also gives you,
by the end of layer one, something you can demonstrate, which is worth more than
four disconnected exercises.

**The setup.** An arm with a parallel gripper, an overhead depth camera that sees
the whole table, and a wrist camera that sees what the gripper is about to touch.
Two cameras rather than one, deliberately: the overhead view tells you where things
are and the wrist view tells you whether the grasp is going to work, and learning
why you need both is part of the project.

### The four layers

**Layer 1, written by hand.** Segment the table by colour and height above the
plane, fit a bounding box to each blob, choose a top-down grasp at the centroid,
plan to it with MoveIt, close the gripper, and drop the object in the bin the colour
rule chose. A [behaviour tree](programmed-methods.md#3-scripted-logic-state-machines-and-behaviour-trees)
sequences the whole thing and handles the retry when a grasp fails. Expect this to
work beautifully on the objects you tuned it for and to fall over the moment you add
a shiny one.

**Layer 2, one learned piece.** Replace the colour-and-height rule with
[SAM 2](https://github.com/facebookresearch/sam2), which segments objects it was
never trained on. Nothing else in the system changes, and that is the lesson: the
planner, the controller and the tree all carry on exactly as before. You have
swapped twenty lines you fully understood, which broke under new lighting, for a
download that handles objects you never described and which you cannot debug when
it is wrong. That trade is the subject of this whole folder, and here you get to
feel it rather than read about it.

**Layer 3, a learned skill.** Your grasp choice is still a centroid, which is why it
drops the mug. Collect outcomes — every grasp you attempt, and whether it held —
then train a small model that scores candidate grasps, and let it choose. The
important part is that **you generate the training labels yourself by trying
grasps in simulation**, so no dataset and no large model is needed. This is the
cheapest possible taste of the pattern in
[learned pieces inside a programmed system](learned-methods.md#4-learned-pieces-inside-a-programmed-system).

**Layer 4, the frontier.** Put a language model on top, so the instruction becomes
"put the tools away and leave the mugs out". The model chooses which subtree to
invoke for each object; the tree still does the running. Read
[directed by language](learned-methods.md#5-directed-by-language) first, and note
that the interesting failure is the model confidently asking for something the arm
cannot reach.

### The stack

| Tool | What it does | Why this one |
| --- | --- | --- |
| [Gazebo](https://github.com/gazebosim/gz-sim) + [ros_gz](https://github.com/gazebosim/ros_gz) | the world, the two cameras, the noise | the only simulator here with sensor models worth trusting |
| [MoveIt 2](https://moveit.picknik.ai/main/index.html) | planning and execution | the standard, and available for Apple Silicon through RoboStack |
| [ros2_control](https://control.ros.org/jazzy/index.html) | the controller the arm actually runs | the same controllers work on real hardware |
| [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) or [py_trees](https://py-trees.readthedocs.io/) | sequencing and recovery | recovery is most of a real system, and trees stay readable |
| `depth_image_proc` | depth picture to point cloud | already in this repo's dependencies |
| [SAM 2](https://github.com/facebookresearch/sam2) | segmentation, layer 2 onwards | runs on Apple's Metal backend in practice; build it with the CUDA step off. Stay on 2, because SAM 3 requires CUDA |

### Who does this for a living

This is what the 3D-vision companies sell. [Photoneo](https://www.photoneo.com/),
[Zivid](https://www.zivid.com/) and [Keyence](https://www.keyence.com/) all ship
systems whose job is exactly layer 2. At the top of the scale,
[Amazon's item-stowing system](https://arxiv.org/abs/2505.04572) is this pattern at
half a million real attempts, and its paper states plainly which parts are learned
and which are conventional — the best free description of a production system
anywhere.

**Done looks like:** the table clears without you touching it, over twenty runs, and
you can say which layer improved which failure.

---

## Project 2: fit the connector

**What you are building.** A cell that picks a connector from a fixture and mates it
into a socket whose exact position it does not know, with a clearance tighter than
the arm can repeat. It reports whether the connector is properly seated.

**Why this one.** This is the task where position is not enough, and it is the
single best place in robotics to compare programmed and learned methods honestly,
because both have strong published results on it. It is also the most commercially
valuable thing in this document, since contact-rich assembly is where the unsolved
industrial problems are.

**The setup.** An arm, a wrist camera to find the socket, and force readings at the
wrist. The socket is deliberately placed a few millimetres from where the model says
it is, because that misalignment is the entire problem.

### The four layers

**Layer 1, written by hand, and it fails.** Find the socket with the camera, plan to
it, and push. The connector jams and the contact forces climb alarmingly. Do this
first and watch it properly, because the failure is not a bug in anything — it is
exactly what a position controller is designed to do, as
[the programmed-methods document explains](programmed-methods.md#6-feedback-control).

**Layer 2, force control.** Switch to commanding *stiffness* rather than position:
come in soft, so a small misalignment pushes the arm aside instead of jamming it,
and search in a small spiral until the force readings say the pin has dropped in.
Then push. This is the single most reusable idea in contact-rich robotics, and
having felt it work, the distinction between commanding a position and commanding a
stiffness stops being abstract. Sweep the stiffness across twenty attempts each and
plot success against it — you will find a window, with jamming at one end and not
enough push at the other.

**Layer 3, a learned skill.** Collect fifty demonstrations of the search, and train
an [ACT policy](learned-methods.md#11-behaviour-cloning) on the contact phase only,
leaving the approach planned. Confining the policy to the phase that actually needs
it is the design decision worth taking away, and it is what the deployed systems do.

**Layer 4, the frontier.** Apply the 2026 recipe: take the imitated policy and
improve it with a short burst of reinforcement learning, with you intervening when
it is about to fail.
[Four independent groups converged on this in one year](what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do),
which makes it the best-evidenced method in this folder.
[HIL-SERL](https://github.com/rail-berkeley/hil-serl) inside LeRobot is the open
implementation.

### The stack

| Tool | What it does | Why this one |
| --- | --- | --- |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | the contact physics | Gazebo's contact model is not built for this; MuJoCo's is |
| [robosuite](https://robosuite.ai/) | ready contact tasks, including peg insertion | saves building the task, and is what the papers benchmark on. It pins an older MuJoCo, so let it choose |
| [robomimic](https://github.com/ARISE-Initiative/robomimic) | careful baselines on those tasks | tells you what a good result looks like. Install from GitHub; its PyPI release has been frozen since 2023 |
| [LeRobot](https://github.com/huggingface/lerobot) | training the layer 3 policy | where ACT lives and is maintained |
| [HIL-SERL](https://github.com/rail-berkeley/hil-serl) | the layer 4 practice loop | ships inside LeRobot; its predecessor SERL is deprecated |
| [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | Cartesian force and impedance control in ROS | read it for how the real thing is structured, even while prototyping in MuJoCo |

### Who does this for a living

Every major vendor sells force control as a product: FANUC ships force sensors and
fitting functions, ABB has two separate options — one for machining and one that
searches for the right location during assembly — and KUKA has a force-torque
package. [Micropsi's MIRAI](https://www.micropsi-industries.com/) is the interesting
learned case, because it removes positional variance with a trained visuomotor skill
while leaving force control underneath to handle the actual contact. On the research
side, [IndustRealKit](https://github.com/NVLabs/industrealkit) trained insertion
purely in simulation and transferred at 83% to 99% across 600 trials.

**Done looks like:** a plot of success against stiffness for layer 2, and a
layer-by-layer comparison of success rate over at least fifty attempts each.

---

## Project 3: empty the bin

**What you are building.** A bin of thirty mixed objects, piled and overlapping, and
an arm that empties it onto a conveyor without damaging anything or giving up when
an object is wedged.

**Why this one.** Bin picking is the task that learned perception turned from a
research problem into a product, so it is the clearest demonstration of what machine
learning has actually bought robotics. It is also where clutter and occlusion make
perception genuinely hard rather than a formality.

**The setup.** An overhead depth camera looking into the bin, a wrist camera for the
approach, and a gripper narrow enough to reach between objects.

### The four layers

**Layer 1, written by hand.** Take the point cloud, find pairs of roughly parallel
surfaces the gripper could close on, score them by how square-on the approach is and
how far they are from other objects, and pick the best reachable one. This geometric
grasp generator is perhaps a hundred lines and it works. Writing it is also the only
sensible route here, because — and this is worth knowing before you go looking —
**every open learned grasp model needs NVIDIA hardware**, since they all compile
CUDA operations. There is no download that will do this on a Mac.

**Layer 2, one learned piece.** Add [SAM 2](https://github.com/facebookresearch/sam2)
so that you know which points belong to which object, and rank your candidate grasps
per object rather than over an undifferentiated cloud. The improvement on a cluttered
bin is large and immediate.

**Layer 3, a learned skill.** Now train your own grasp scorer, and note that the
interesting part is where the data comes from: **you generate it by trying**. Every
attempt in simulation is a labelled example, so a few thousand attempts overnight
give you a dataset nobody had to annotate. This is the same trick as
[MimicGen](https://github.com/NVlabs/mimicgen) at a smaller scale — using programming
to manufacture the data that training needs — and it is the most practically useful
idea in this whole document for anyone without a GPU budget.

**Layer 4, the frontier.** Fine-tune [SmolVLA](https://huggingface.co/blog/smolvla)
on your collected data and compare it against your hand-written pipeline. Be honest
about the result: the modular approach may well win, and
[no published paper anywhere reports a head-to-head](learned-methods.md#4-learned-pieces-inside-a-programmed-system)
of a general pretrained policy against one of these pipelines. This is the one layer
in the project that wants a rented GPU.

### The stack

| Tool | What it does | Why this one |
| --- | --- | --- |
| [Gazebo](https://github.com/gazebosim/gz-sim) | bin, clutter, depth camera with noise | the noise matters; a perfect camera teaches you nothing |
| `depth_image_proc` | depth to point cloud | the standard ROS route |
| [SAM 2](https://github.com/facebookresearch/sam2) | which points are which object | the model that removed the need for a vision engineer per customer |
| [MoveIt 2](https://moveit.picknik.ai/main/index.html) | reachability and execution | reachability filtering is most of the grasp choice |
| [GraspNet-1Billion](https://graspnet.net/) | grasp dataset and benchmark | data to score your own generator against; its detector needs CUDA |
| [LeRobot](https://github.com/huggingface/lerobot) + [SmolVLA](https://huggingface.co/blog/smolvla) | layer 4 | the only pretrained policy sized for ordinary hardware |

### Who does this for a living

This is the most commercially settled task in the document. Beyond the vision
vendors named in project 1, the published numbers are strong: AnyGrasp reported
clearing bins of over 300 unseen objects at 93.3% success and more than 900 picks an
hour. Note that AnyGrasp ships as a licence-gated binary and is not open source
despite appearances, which is itself a useful thing to know about this market.

**Done looks like:** picks per hour and success rate for all four layers, on the
same thirty objects, with the bin emptied at least ten times.

---

## Project 4: copy it from video

**What you are building.** You record a video of your own hand doing a simple
tabletop task — pushing a block into a target square, or stacking two cups — and the
arm learns to do it. No teleoperation rig, no demonstrations driven through the
robot.

**Why this one.** This is the clearest bet in the field right now.
[Robot demonstrations are the binding constraint](what-is-changing.md#2-the-five-forces-driving-2026)
and more of them have stopped helping, so the obvious way out is to learn from
video, of which there is effectively an unlimited supply. Doing a small version
yourself teaches you why it is hard in a way no paper will, and it is the project
here most likely to be genuinely novel to whoever you show it to.

**The setup.** Your phone or laptop camera for recording yourself, and in
simulation an arm with a wrist camera and a parallel gripper.

### The four layers

**Layer 1, written by hand.** Record thirty attempts at the task and track your hand
through them with
[MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker),
which runs natively on Apple Silicon and gives you hand landmarks per frame. Plot
the resulting trajectories. Nothing is learned yet, and already you have met the
first real problem: the scale and the origin of your hand's coordinates have nothing
to do with the robot's.

**Layer 2, retargeting.** Map the hand pose onto a gripper pose — the pinch between
thumb and forefinger becomes the gripper's opening, the palm becomes the wrist —
then replay the retargeted trajectory open-loop in MuJoCo. It will miss, and *why*
it misses is the lesson: your hand and the gripper have different kinematics, your
camera never measured depth accurately, and nothing ever closed a loop. Retargeting
is the hard, unglamorous core of this entire research direction.
[dex-retargeting](https://github.com/dexsuite/dex-retargeting) is worth reading for
how it is done properly.

**Layer 3, a learned skill.** Train a policy on the retargeted trajectories rather
than replaying them, so that it can correct rather than repeat. Evaluate it
honestly. Expect a low number — this is genuinely hard, and a low number here is a
correct result rather than a failure of yours.

**Layer 4, the frontier.** Mix a handful of proper demonstrations, collected in
simulation, in with the video data, and find out how few real demonstrations it
takes to rescue the policy. That ratio is exactly what the research community is
currently trying to establish, so you are asking a live question rather than a
settled one. [UMI](https://github.com/real-stanford/universal_manipulation_interface)
is the ancestor of this whole idea, and
[Grabette](https://huggingface.co/blog/grabette) is the €490 handheld device that
does it properly today.

### The stack

| Tool | What it does | Why this one |
| --- | --- | --- |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | hand tracking from ordinary video | ships Apple Silicon wheels and runs on a laptop camera in real time |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | where the arm replays and trains | fast, scriptable, and what LeRobot expects |
| [dex-retargeting](https://github.com/dexsuite/dex-retargeting) | hand pose to robot pose, done properly | the reference for the hardest part of the project |
| [LeRobot](https://github.com/huggingface/lerobot) | dataset format, training, evaluation | its dataset format is what everything else in this area expects |
| [UMI](https://github.com/real-stanford/universal_manipulation_interface) | the research this descends from | read it before building, to see which problems are already solved |

### Who does this for a living

Nobody is selling this yet, which is the point of including it. The research line is
active, almost nothing has been released, and the one thing you can actually buy —
[Grabette](https://huggingface.co/blog/grabette), Apache-2.0 — is a handheld recorder
with cameras and a gripper encoder that lets you collect training data with no robot
present. If your eventual goal is service work, being able to say you have built a
video-to-policy pipeline, however small, is unusual.

**Done looks like:** a success rate for layer 3, and a curve showing how it improves
as you add real demonstrations in layer 4.

---

## Project 5: build the kit

**What you are building.** A tray holding five parts, which must be assembled in a
fixed order: place the base, fit the board, drive two fasteners, clip the cover,
and put the finished unit in an output tray. If a step fails, the cell recovers and
carries on rather than stopping.

**Why this one last.** Long tasks are where the learned methods are weakest and the
programmed ones are strongest, and having built the previous four projects you are
now in a position to demonstrate that rather than take it on trust. This is also the
project that most resembles actual industrial work.

**The setup.** An overhead camera to locate parts in the tray, a wrist camera for
each fitting operation, force readings for the fastening, and a gripper that can
handle all five parts.

### The four layers

**Layer 1, written by hand.** A behaviour tree over the skills you have already
built in projects 1 to 3, with a recovery branch for every step. Most of your code
here will be about what happens when something fails, which is true of every real
robot system and is the main thing this layer teaches.

**Layer 2, one learned piece.** Feed the tree with learned perception, so the parts
no longer have to start in known positions. The tree does not change at all, which
is the same lesson as project 1's layer 2, now at a scale where it matters more.

**Layer 3, a learned skill, and it will fail.** Replace the whole tree with a single
policy trained end to end, and evaluate it. It will do much worse, and the failures
will cluster near the end rather than spreading evenly — that clustering is
[compounding error](learned-methods.md#11-behaviour-cloning), and seeing it in your
own numbers is the fastest way to understand why the programmed methods have not
gone anywhere. The published evidence agrees with you:
[FurnitureBench](https://github.com/clvrai/furniture-bench) found that behaviour
cloning completes none of its full assemblies except the very simplest.

**Layer 4, the frontier.** Put a language model above the behaviour tree, choosing
which subtree to run next and replanning when a step reports failure, and compare it
against the fixed tree from layer 1. For a task whose sequence is genuinely fixed,
the tree should win, and understanding *why* — it is deterministic, free and provable
— is worth more than the layer itself.
[SayCan](https://say-can.github.io/) and
[Code as Policies](https://code-as-policies.github.io/) are the two shapes to read.

### The stack

| Tool | What it does | Why this one |
| --- | --- | --- |
| [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | the sequence and the recovery | its Groot editor lets you watch the tree tick, which is the best way to understand them |
| [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | multi-stage motion with alternatives | the mainstream way to express "try this, else that" |
| [Gazebo](https://github.com/gazebosim/gz-sim) + [MoveIt 2](https://moveit.picknik.ai/main/index.html) | layers 1 and 2 | the system half of the project |
| [MuJoCo](https://github.com/google-deepmind/mujoco) + [LeRobot](https://github.com/huggingface/lerobot) | layer 3 | the policy half, and the comparison |
| [FurnitureBench](https://github.com/clvrai/furniture-bench) | the honest yardstick | read the results before you are disappointed by your own |

### Who does this for a living

This is ordinary industrial assembly, and it is done with behaviour trees and
programmed skills essentially everywhere. The interesting commercial question is not
who does it but who is trying to replace it, which is
[Physical Intelligence](https://github.com/Physical-Intelligence/openpi),
[Figure](https://www.figure.ai/news/helix) and
[Toyota Research Institute](https://toyotaresearchinstitute.github.io/lbm1/) — none
of whom can yet do a twenty-step assembly reliably end to end.

**Done looks like:** a completion rate for the full assembly at each layer, and a
breakdown of which step the failures happen at.

---

## Where the cloud actually helps

Almost all of this runs on the Mac, and that is worth defending, because a local
loop you can run twenty times in an evening teaches you far more than a cloud job
you run twice. Rent a machine for the steps that genuinely need one.

**Worth renting a graphics card for.** The layer-4 pretrained fine-tunes in projects
3 and 4. Any NVIDIA-specific perception model, such as
[FoundationPose](https://github.com/NVlabs/FoundationPose), if you decide you want
six-degree-of-freedom pose estimation. Anything involving
[Isaac Lab](https://github.com/isaac-sim/IsaacLab), which requires CUDA and will not
run on Apple Silicon at all — though this path avoids it entirely, because MuJoCo
covers the same ground for what you are learning.

**Not worth renting for.** Every layer 1 and layer 2 in this document. Training an
ACT policy on a small task, which is an hour of compute rather than a day. Your own
small grasp scorer in project 3, which is the whole point of generating the data
yourself. Any amount of Gazebo, MoveIt or `ros2_control` work, none of which is
compute-bound.

**The habit worth building** is to develop locally at small scale until the pipeline
is correct, and only then rent something to run it at full size. The most common way
to waste cloud credit is to debug in the cloud.

## What this path deliberately leaves out

**Real hardware, and therefore calibration.** Everything above is simulated, which
means you will not have met the problem of making a model agree with reality. If you
later buy a cheap arm, expect that to be the surprise.

**Two arms.** Coordination is a genuinely different problem with
[its own folder](../two-arm-training/overview.md). Do this path first, because
almost every two-arm method is a single-arm method with a coordination problem added.

**Reinforcement learning from scratch.** It needs a simulator, a reward function and
a compute budget, and the field itself is using it less each year as a first stage.
Project 2's layer 4 teaches the use that actually matters, which is practice applied
to an already-demonstrated policy.

**Isaac Lab and the NVIDIA stack.** Excellent, widely used, and requires hardware you
do not have. MuJoCo teaches the same lessons. Note that
[MuJoCo Warp](https://github.com/google-deepmind/mujoco_warp), where the
high-throughput version of that story is going, is NVIDIA-first as well — it runs on
a Mac for reading and debugging, not for training. The simulator to watch if you
want a genuine Apple graphics backend is
[Genesis](https://github.com/Genesis-Embodied-AI/Genesis).

---

Back to [the overview](overview.md). For the methods themselves, see
[programmed methods](programmed-methods.md) and
[learned methods](learned-methods.md); for the direction the field is moving, see
[what is changing, and why](what-is-changing.md).
