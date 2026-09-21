# Glossary

Robotics has a lot of words, and most of them are used before they are explained.
This page explains them.

It is meant to be looked up rather than read straight through. The terms are grouped
by what they are about, and inside each group the simpler ones come first.

Where a term is explained properly somewhere else in this folder, there is a link.

## Contents

1. [The arm itself](#the-arm-itself)
2. [Describing where things are](#describing-where-things-are)
3. [Seeing](#seeing)
4. [Moving](#moving)
5. [Touching](#touching)
6. [Deciding what to do](#deciding-what-to-do)
7. [Learning](#learning)
8. [Measuring whether it worked](#measuring-whether-it-worked)
9. [The frameworks](#the-frameworks)

---

## The arm itself

**Link.** One rigid piece of the arm. The parts between the joints.

**Joint.** A place where two links move relative to each other. Most robot arm
joints rotate. A few slide instead, and those are called prismatic joints.

**Degree of freedom.** One independent way something can move. A typical industrial
arm has six joints, so it has six degrees of freedom. Six is the useful number
because it is the smallest number that lets you put the gripper at any position and
at any angle. With fewer, some angles become impossible. This is often shortened to
DoF, as in "6-DoF".

**End effector.** Whatever is bolted to the end of the arm. A gripper, a welding
torch, a suction cup, a screwdriver.

**Gripper.** The thing that holds objects. A **parallel gripper** has two fingers
that close towards each other, and it is by far the most common kind. A **suction
gripper** uses a vacuum cup, which is better for flat boxes and useless for porous
objects.

**Payload.** How much weight the arm can carry at full reach. Be careful with this
number: it usually includes the weight of the gripper, so the weight of the object
you can actually lift is smaller.

**Reach.** How far the arm can extend. Usually measured from the base to the wrist.

**Repeatability.** How precisely the arm returns to a place it has been before. A
good industrial arm manages about a tenth of a millimetre. This is the number
vendors advertise.

**Accuracy.** How close the arm gets to a place it has been *told* about but never
visited. This is a different number, and it is much worse than repeatability,
usually by a factor of ten or more. Most people confuse the two. The gap between
them is why [calibration](#calibration) matters.

**Singularity.** An arm pose where the arm loses the ability to move in some
direction, no matter what the joints do. The classic case is the arm stretched
completely straight: it cannot extend any further. Near a singularity the maths
demands enormous joint speeds for a small hand movement, so controllers either slow
down or refuse. Planners avoid these poses.

**Teach pendant.** The handheld control box used to drive an industrial arm by hand
and record positions. See
[teach and replay](02_programmed-methods.md#1-teach-and-replay).

**Lead-through**, also called **kinesthetic teaching**. Programming the arm by
physically pushing it where you want it to go, instead of driving it with buttons.

**Collaborative robot**, usually shortened to **cobot**. An arm built to work near
people without a safety fence, normally by moving slowly and stopping when it feels
an unexpected force.

## Describing where things are

**Pose.** A position *and* an orientation together. Where something is, and which
way it is turned. A full pose in 3D has six numbers: three for position and three
for rotation.

**Frame.** A set of axes that positions are measured against. Every robot system has
many of them: one at the base of the arm, one at the gripper, one on each camera,
one on the table. A position only means something when you say which frame it is in.

**Transform.** The relationship between two frames — how to convert a position in
one into a position in the other. **TF** is the ROS system that keeps track of all
of them and lets you ask "where is the gripper, in the camera's frame?"
[The arm area](../03_arm/01_overview.md) builds these up from scratch.

**Joint space.** Describing the arm by its joint angles. Six numbers for a six-joint
arm. This is what the motors actually care about.

**Cartesian space**, also called **task space**. Describing the arm by where the
gripper is, in ordinary x, y and z. This is what you care about.

**Forward kinematics.** Given the joint angles, work out where the gripper is. This
is the easy direction: there is exactly one answer, and it is a chain of
multiplications.

**Inverse kinematics**, usually shortened to **IK**. Given where you want the
gripper, work out the joint angles. This is the hard direction. There may be several
answers — an arm can often reach the same place with its elbow up or down — and
sometimes there are none, because the place is out of reach.

**Workspace.** All the poses the arm can actually reach. It is a strange shape, and
it has holes in it, usually directly above and behind the base.

**URDF.** The Unified Robot Description Format, an XML file that lists a robot's
links, joints, shapes and limits. ROS, Gazebo and MoveIt all read it.

**MJCF.** MuJoCo's own robot description format. Same job as a URDF, different file.
The same arm needs both if you use both simulators, and keeping them in agreement is
a real chore.

## Seeing

**Depth camera.** A camera whose pixels record distance rather than colour. An
**RGB-D camera** records both, so you get a colour picture and a distance for each
pixel.

**Point cloud.** A set of 3D points, usually produced from a depth picture. This is
what most robot perception code actually works on, because points can be reasoned
about geometrically while pixels cannot.

**Segmentation.** Working out which pixels belong to which object. Doing this well
for objects the system has never seen is what [SAM 2](#sam-2) provides, and it is
the main reason machine learning has been adopted in real robot cells.

**Pose estimation.** Working out the full position and orientation of a known
object. Often called **6-DoF pose estimation**, because the answer has six numbers.

**Occlusion.** One object hiding another from the camera. This is the central
difficulty of bin picking, because in a pile most objects are partly hidden.

**Calibration.** Measuring the fixed relationships that your model assumes. **Hand-eye
calibration** is the important one: it works out exactly where the camera is relative
to the arm. If this is wrong by two millimetres, then everything the camera reports
is wrong by two millimetres, and no amount of good software fixes it. Calibration is
unglamorous and it decides whether a real cell works.

**Grasp pose.** Where the gripper should be, and how it should be turned, in order to
pick something up. A grasp *proposal* system suggests several and ranks them.

**Antipodal grasp.** A grasp where the two fingers close on opposite, roughly
parallel surfaces. This is the shape of grasp a parallel gripper wants, and finding
these on a point cloud is the basis of a simple hand-written grasp generator.

## Moving

**Path.** A sequence of positions from here to there. It says nothing about speed.

**Trajectory.** A path with timing attached — where the arm should be, and when.
Controllers execute trajectories, not paths.

**Waypoint.** One recorded position along a path.

**Motion planning.** Finding a path from the arm's current pose to a target pose
without hitting anything. Explained fully in
[the programmed methods](02_programmed-methods.md#4-motion-planning).

**Configuration space**, often shortened to **C-space**. The space of all possible
joint angle combinations. A six-joint arm has a six-dimensional configuration space.
Planners search in this space rather than in ordinary 3D space, and the reason
planning is hard is that obstacles become complicated, unpredictable shapes once you
translate them into it.

**Sampling-based planner.** A planner that throws random configurations at the
problem, throws away the ones that collide, and connects the rest until a path
appears. **RRT**, the rapidly-exploring random tree, and **PRM**, the probabilistic
roadmap, are the two standard ones. They are good at finding a way through awkward
spaces. They give a different answer every run, which is a genuine problem if
anybody has to certify what the machine will do.

**Optimisation-based planner.** A planner that starts with a guess at the whole path
and pushes it away from obstacles while keeping it short and smooth. **CHOMP** and
**TrajOpt** are the classic ones. The paths are nicer and repeatable, but the method
can get stuck where a random planner would eventually have found a way.

**Point-to-point, linear and circular motion.** The three motion types an industrial
controller actually offers. Point-to-point moves the joints directly, linear moves
the gripper in a straight line, circular moves it along an arc. They are
deterministic, which is why factories use them.

**Collision checking.** Testing whether a given arm pose overlaps anything,
including the arm overlapping itself. Planners do this thousands of times per
query, so it has to be fast.

**Jerk.** The rate at which acceleration changes. Limiting it is what stops an arm
from moving in a way that shakes the whole cell. [Ruckig](#ruckig) does this.

## Touching

**Position control.** Telling the arm where to be. The controller then pushes as
hard as it needs to in order to get there. This is the default, and it is what
breaks parts: commanded into a surface, it sees an error it cannot remove and
pushes harder.

**Force control.** Telling the arm how hard to push, rather than where to be.

**Compliance.** How much the arm gives way when something pushes it. A compliant arm
is soft; a stiff arm is not.

**Stiffness.** The number that says how compliant the arm is — how much force it
produces for a given amount of displacement. Choosing this number deliberately,
rather than inheriting whatever the mechanics give you, is the whole point of
impedance control.

**Impedance control.** Making the arm behave like a spring of a stiffness you chose.
Push it and it pushes back gently, in proportion to how far you moved it.

**Admittance control.** The same idea approached from the other side: measure the
force, then move in response to it. Which of the two you use depends mostly on what
your hardware can sense. Both are covered in
[feedback control](02_programmed-methods.md#6-feedback-control).

**Force-torque sensor.** A sensor, usually at the wrist, that measures the forces and
twists acting on the gripper. Accurate and expensive, and a lot of research
deliberately avoids needing one.

**Compliant flange.** A small spring-loaded device bolted between the arm and the
tool, which holds a set contact force over a few millimetres of travel. It reacts far
faster than the arm can, which is why polishing and deburring use one. It is a
mechanical answer to a control problem.

**Visual servoing.** Closing the control loop on the camera instead of on the joint
sensors. You move so as to reduce the difference between what the camera sees and
what it should see. Its virtue is that it never needs to know where anything is in
world coordinates.

**Model predictive control**, usually shortened to **MPC**. Repeatedly solving a
short planning problem: given where I am now and a model of how things move, what is
the best sequence of commands over the next second? It executes only the first
command, then throws the rest away and solves again. Re-solving is how it absorbs
everything the model got wrong.

## Deciding what to do

**State machine.** A set of named states with rules for moving between them. Easy to
follow with five states, unreadable with fifty, because the number of possible
transitions grows with the square of the number of states.

**Behaviour tree.** A task arranged as a tree of steps, run repeatedly. Each step
reports success, failure, or still running. A **sequence** node runs its children in
order until one fails. A **fallback** node tries each child until one succeeds, which
is the shape of "try the normal thing, and if that fails, try the recovery". They
stay readable at fifty branches, which is why they won.

**Primitive**, or **skill**. One named, reusable piece of robot behaviour, such as
"approach", "grasp" or "retreat". Real systems are built by sequencing these.

**Task and motion planning**, usually shortened to **TAMP**. Searching for what to do
and how to move at the same time, because sometimes they cannot be separated. Very
capable, very slow, and used far less than its reputation suggests.

## Learning

**Policy.** A function that takes what the robot can see and produces what the robot
should do next. When people say "the model" in robot learning, they usually mean
this.

**Demonstration.** One recorded example of a person doing the task, usually by
driving the robot. The recording includes the camera pictures, the joint angles and
the commands the person gave.

**Teleoperation.** Driving the robot remotely so that its motion can be recorded. For
arms this is often done with a **leader arm**, which is a small copy of the robot that
you move with your hand while the real arm follows.

**Imitation learning**, also called **learning from demonstration**. Training a
policy to copy what the demonstrator did.

**Behaviour cloning.** The simplest form of imitation learning: train the network to
output the command the person gave, given what the cameras saw. Explained in
[the learned methods](03_learned-methods.md#11-behaviour-cloning).

**Compounding error.** The central problem of behaviour cloning. A slightly wrong
command puts the arm somewhere slightly unlike the training data, where the next
command is a little worse, and within a second or two the arm is somewhere no
demonstrator ever went. Errors build with every decision taken.

**Action chunking.** Predicting the next hundred commands at once and playing them
out, rather than predicting one command at a time. If you make a hundred times fewer
decisions, you get a hundred times fewer chances to drift. This is the main fix for
compounding error.

**ACT.** Action Chunking with Transformers. The specific policy that made action
chunking popular, and still the recommended first thing to try for a new task. It
trains in under an hour on one ordinary graphics card, which is most of why it is
recommended.

**Diffusion policy.** A policy that generates a whole action sequence the way image
models generate pictures, by starting from noise and refining. The reason to bother
is multimodality: if some demonstrators went left around an obstacle and others went
right, a plain network averages them and drives straight into it. A diffusion policy
can represent "either this or that".

**Flow matching.** A faster relative of diffusion that solves the same problem. In
2026 it is the action-generating part inside nearly every large policy. Worth
knowing that a 2026 study found no measurable advantage over plain regression on its
benchmarks, so this is not as settled as its popularity suggests.

**Multimodal.** Having several valid answers rather than one. The word is used this
way in robot learning, which is unrelated to its other meaning of "using several
kinds of input".

**Reinforcement learning**, usually shortened to **RL**. Learning by trying things
and keeping what worked, guided by a reward rather than by demonstrations.

**Reward.** A number that says how well things are going. Writing one is harder than
it sounds, because any gap between what you wrote and what you meant will be found
and exploited.

**Model-free and model-based RL.** Model-free methods learn directly from experience
with no model of the world, which is simple and needs enormous amounts of practice.
Model-based methods learn a model first and then practise inside it, which needs far
fewer real attempts and has many more moving parts.

**Offline RL.** Learning from a fixed pile of recorded behaviour, with no practising
at all.

**DAgger.** Dataset Aggregation. The idea of letting the policy drive, correcting it
when it goes wrong, and adding those corrections to the training data. Corrections
cover the situations the policy actually reaches, which is why a few dozen of them
beat several hundred fresh demonstrations.

**HIL-SERL.** Human-in-the-Loop Sample-Efficient Robot Learning. The modern version
of that idea, where your take-overs become the reinforcement learning signal. It has
the strongest published numbers in this folder.

**Sim-to-real gap.** The difference between the simulator and the world, and the
reason a policy that works in simulation may not work on hardware.

**Domain randomisation.** The main fix for that gap. Instead of building one accurate
simulator, you train across thousands of randomised ones — varying friction, mass,
lighting and delays — so that reality is just one more variation the policy has
already coped with.

**Foundation model.** A large model trained on a great deal of general data, meant to
be adapted to specific jobs rather than used as-is.

**Pretraining and fine-tuning.** Pretraining is the expensive first stage on a large
general dataset. Fine-tuning is the cheap second stage that adapts the result to your
task with comparatively few examples. On this path you fine-tune and never pretrain.

**Vision-language-action model**, usually shortened to **VLA**. A large pretrained
policy that takes camera pictures and a sentence, and produces arm commands. The
sentence is what lets one model do many tasks.

**Checkpoint**, or **weights**. The saved, trained state of a model — the actual file
you download. The distinction that matters in practice is between a model that has
been *announced* and one whose checkpoint you can actually download. Several of the
most impressive models of 2026 have no released weights.

**World model.** A model that learns to predict what will happen next, so the policy
can act through that prediction. The interesting property is that it can learn from
video with no recorded actions attached, which matters because video is plentiful and
robot demonstrations are not.

**Retargeting.** Converting a motion recorded from one body onto another — most often
a human hand onto a robot gripper. It is the hard, unglamorous core of learning from
human video, because the two have different shapes and different joints.

## Measuring whether it worked

**Episode**, or **rollout**, or **trial.** One attempt at the task, from the starting
state to success or failure. These three words mean the same thing and different
papers pick different ones.

**Success rate.** The fraction of attempts that worked. Meaningless without the
number of attempts.

**Denominator.** The number of trials behind a percentage. A 90% success rate over
ten trials and over a thousand trials are completely different claims. If a source
gives a percentage and no denominator anywhere, treat it as marketing. This habit is
worth more than any single technique, and
[the overview explains why](01_overview.md#11-how-to-read-the-numbers-in-this-field).

**Ablation.** An experiment that removes one piece of a system to find out how much
that piece was contributing. The most informative kind of result, and the one most
often missing.

**Benchmark.** A fixed set of tasks everyone tests on, so that results can be
compared. Useful, and worth remembering that a method tuned on a benchmark is partly
tuned to that benchmark.

## The frameworks

Short entries. The
[learning path explains each of these in depth](04_learning-path.md#the-tools-and-why-each-one),
including why to choose it over the alternative.

The "Mac" column says whether it runs on an Apple Silicon Mac without an NVIDIA
graphics card.

### Simulators

| Name | What it is | Mac |
| --- | --- | --- |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | DeepMind's physics simulator, built for contact and for machine learning. Fast, accurate on contact, and what nearly every robot learning tool expects underneath. | yes |
| [Gazebo](https://github.com/gazebosim/gz-sim) | The simulator ROS uses. Good sensor models, talks to ROS directly, runs the same controllers a real arm runs. | partly — install with conda, and run the window and physics as separate commands |
| [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) | A collection of carefully tuned models of real robot arms, ready to load into MuJoCo. | yes |
| [Isaac Sim / Isaac Lab](https://github.com/isaac-sim/IsaacLab) | NVIDIA's simulator and learning framework. Widely used in research. | **no** — needs CUDA and ray-tracing hardware |
| [ManiSkill](https://github.com/haosulab/ManiSkill) | A large set of manipulation tasks with good graphics. | partly — processor only, and needs a manual Vulkan install |
| [PyBullet](https://github.com/bulletphysics/bullet3) | The previous generation's free simulator. Huge tutorial legacy, barely maintained now. | **no** — no Mac packages, and the source build is broken |
| [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) | A newer simulator, and the one with a genuine Apple graphics backend. Worth watching. | yes |

### Motion and control

| Name | What it is | Mac |
| --- | --- | --- |
| [MoveIt 2](https://moveit.picknik.ai/main/index.html) | The standard ROS motion planning stack: inverse kinematics, collision checking, planning, execution. | yes |
| [OMPL](https://ompl.kavrakilab.org/) | The library of sampling-based planners that MoveIt uses underneath. | yes |
| **Pilz industrial motion planner** | Ships inside MoveIt. Gives deterministic point-to-point, linear and circular motion, the way a real factory controller does. | yes |
| [Ruckig](https://github.com/pantor/ruckig) | Works out the timing along a path so the arm accelerates smoothly instead of jerking. | yes |
| [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | Builds a motion out of stages with alternatives, so you can say "try from the top, else from the side". | yes |
| [ros2_control](https://control.ros.org/jazzy/index.html) | The standard ROS controller framework. The same controllers run in simulation and on real hardware. | yes |
| [gz_ros2_control](https://github.com/ros-controls/gz_ros2_control) | Runs those controllers inside Gazebo. | yes |
| [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | Cartesian force and impedance control for ROS, which is what contact tasks actually need. | yes |
| [Drake](https://drake.mit.edu/) and [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | Serious model-based robotics libraries, for dynamics and optimisation. | yes |
| [cuRobo](https://github.com/NVlabs/curobo) | A motion planner that runs on a graphics card, fast enough to replan continuously. | **no** — needs CUDA |
| [Tesseract](https://github.com/tesseract-robotics/tesseract) | The open industrial process-planning stack, used for real sanding and painting programmes. | builds from source |

### Sequencing

| Name | What it is | Mac |
| --- | --- | --- |
| [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | The standard behaviour tree library. Its Groot editor lets you watch the tree run live. | yes |
| [py_trees](https://py-trees.readthedocs.io/) | The Python behaviour tree library. Easier to start with. | yes |
| [PDDLStream](https://github.com/caelan/pddlstream) | The reference implementation of task and motion planning. Last commit 2023, which tells you something about the field. | yes |

### Seeing

| Name | What it is | Mac |
| --- | --- | --- |
| [SAM 2](https://github.com/facebookresearch/sam2) | Meta's segmentation model. Separates objects it has never been trained on. | yes, on Apple's Metal backend, with the CUDA build step off |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | Finds hand positions in ordinary video, in real time on a laptop camera. | yes |
| [FoundationPose](https://github.com/NVlabs/FoundationPose) | The best open 6-DoF pose estimator. | **no** — CUDA throughout |
| [GraspNet-1Billion](https://graspnet.net/) | A large grasping dataset and benchmark. Useful as data; its detector needs CUDA. | dataset yes, detector no |
| `depth_image_proc` | The standard ROS package that turns a depth picture into a point cloud. | yes |

### Learning

| Name | What it is | Mac |
| --- | --- | --- |
| [LeRobot](https://github.com/huggingface/lerobot) | Hugging Face's robot learning library. Policies, dataset format, training and evaluation, all in one place. Where ACT and diffusion policy now live and are maintained. | yes, on Metal |
| [robosuite](https://robosuite.ai/) | Ready-made manipulation tasks running inside MuJoCo, including peg insertion. | yes |
| [robomimic](https://github.com/ARISE-Initiative/robomimic) | Datasets and careful baseline results on those tasks. Install from GitHub, not PyPI. | yes |
| [HIL-SERL](https://github.com/rail-berkeley/hil-serl) | Improves a policy by practice with human take-overs. Ships inside LeRobot. | yes |
| [SmolVLA](https://huggingface.co/blog/smolvla) | A pretrained vision-language-action model small enough for ordinary hardware. | yes for running; a rented card is better for fine-tuning |
| [openpi](https://github.com/Physical-Intelligence/openpi) | Physical Intelligence's open models, the π family. Larger than SmolVLA. | needs a large card |
| [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) | The clearest implementations of the standard reinforcement learning algorithms. | yes |
| [MimicGen](https://github.com/NVlabs/mimicgen) | Turns a handful of demonstrations into thousands by re-composing them. Research licence only. | yes |
| [gym-aloha](https://github.com/huggingface/gym-aloha) | Two small MuJoCo tasks, useful for learning the training loop quickly. | yes |
| [FurnitureBench](https://github.com/clvrai/furniture-bench) | A benchmark of real furniture assembly, and the honest yardstick for long tasks. | reference |

---

Back to [the overview](01_overview.md), or to
[the learning path](04_learning-path.md) if you want to build something.
