# Ways to programme or train a robot arm

If you set out to make a robot arm do something genuinely complicated — empty a
dishwasher, assemble a part, stack rough stones into a tower — you will quickly
find that there is no agreed way to do it. Read three papers and you will meet
three different approaches that share almost no vocabulary. One talks about
planners and constraints, one about demonstrations and policies, one about
rewards and episodes. All three work, and all three are describing the same job.

This doc is a map of that landscape. It explains every method that is in serious
use for getting an arm to do a complex task, what problem each one was invented
to solve, what it costs you, and when it breaks. It then shows how real systems
combine several of them, because almost nothing that works in the world uses
only one.

**Who this is for.** Someone who can picture a robot arm moving and knows
roughly what a camera and a joint angle are, but who has not yet had to choose
between these approaches. You do not need to have used any of them. Where a
method needs an idea from elsewhere in this repo — frames, depth pictures,
topics — there is a link.

**The short answer, before the long one.** The two families are *programming*,
where a person writes down what the arm should do, and *training*, where the
behaviour is learned from examples or from practice. Programming is precise,
inspectable and safe, and it cannot cope with variety. Training copes with
variety, needs a great deal of data, and cannot tell you why it failed. Every
serious system therefore uses both: it programmes the parts that are easy to say
and trains the parts that are not. The rest of this doc is about knowing which
parts are which.

**How to read it.** Sections 1 to 3 give the background and the shape of the
field. Sections 4 to 9 explain each family of methods in turn, with links to
where each is explained properly by the people who invented it. Section 10 is a
grid comparing all of them on twenty points, section 11 shows what real systems
actually do, and section 12 turns it into a "if your situation is this, start
here" table.

## Contents

1. [Where this problem comes from](#1-where-this-problem-comes-from)
2. [The four layers of any arm system](#2-the-four-layers-of-any-arm-system)
3. [The family tree](#3-the-family-tree)
4. [Programmed: a person writes the behaviour](#4-programmed-a-person-writes-the-behaviour)
5. [Learning from demonstrations](#5-learning-from-demonstrations)
6. [Learning from trial and error](#6-learning-from-trial-and-error)
7. [Learning from large-scale pretraining](#7-learning-from-large-scale-pretraining)
8. [Learned pieces inside a programmed system](#8-learned-pieces-inside-a-programmed-system)
9. [Directed by language](#9-directed-by-language)
10. [The comparison grid](#10-the-comparison-grid)
11. [What real systems actually do](#11-what-real-systems-actually-do)
12. [Which to use when](#12-which-to-use-when)
13. [Where this repo fits](#13-where-this-repo-fits)

---

## 1. Where this problem comes from

It helps to know why there are so many answers, and the reason is historical:
each method was invented because the one before it hit a wall.

**The factory arm, and why it was enough for forty years.** The first industrial
arms were programmed by leading them through the motion. An operator holds a
control box — a **teach pendant** — drives the arm to a position, presses a
button to record it, and repeats. The recorded positions are called
**waypoints**, and playing them back in order is the whole programme. This
sounds primitive, and it is still how most of the arms working today are
programmed, because in a factory it is entirely sufficient: the part arrives in
the same fixture, in the same orientation, every time, for a million repetitions.
When nothing varies, a recording of the right motion *is* the solution, and it is
fast, cheap and completely predictable.

**What breaks it.** Three things, and every method after this exists because of
one of them.

The first is **variation**. If the part arrives at a slightly different angle,
the recording is now wrong. The fix is to sense where the part is and adjust,
which means the robot needs a model of itself and its surroundings, and something
that computes a new motion each time rather than replaying an old one. That is
where motion planning comes from.

The second is **novelty**. Sensing the part's position only helps if you knew
what the part looked like in advance. A robot that must handle an object it has
never seen, in a scene arranged in a way nobody anticipated, cannot be given a
model of it beforehand. That is where learned perception comes from.

The third, and the hardest, is **contact**. As long as the arm is moving through
free space, a plan is a good description of what will happen. The moment it
touches something, the outcome depends on friction, on exactly which corners
meet, on tiny deflections — quantities nobody can measure in advance or write
down. Tasks like inserting a plug, wiping a surface, or balancing a stone live
almost entirely in this regime. That is where force control, and later learning
from demonstrations, come from.

**The two ways to answer.** Faced with those three problems, the field split.
One answer is to *describe the world better*: build a model of the robot and the
objects, and compute what to do from the model. The other is to *stop describing
it* and let the behaviour come from data — from watching a person, or from the
robot practising. The first family is what this doc calls **programmed**, the
second **learned**.

Neither family won. Programmed methods still run essentially all of
manufacturing, because they can be verified and explained, which matters when a
machine can hurt someone. Learned methods handle tasks that no one has managed to
programme at all, but they need data, and they fail in ways that are hard to
predict or diagnose. The interesting question in 2026 is not which family is
better but **which parts of a system belong to which**, and that is what section
2 is about.

---

## 2. The four layers of any arm system

Underneath the vocabulary, any robot doing a real job has to answer four
questions, over and over. It is worth seeing them separately, because "which
method should I use" almost always has a different answer at each one.

![The four layers, and the methods that usually fill each](../images/arms-training-methods/overview/layers.svg)

**What to do next.** The task has steps, and something decides their order. For
emptying a dishwasher: open it, pull out the rack, take the top-left plate, put
it away, take the next one. This layer is about sequence and choice, and it is
the layer where the robot's "understanding" of the task lives.

**Which skill, and where.** Given the step "take the top-left plate", something
has to turn it into a specific action on a specific object in a specific place:
which plate, gripped where, lifted in which direction.

**How to move.** Given a target, something must produce a path from where the arm
is now to where it needs to be, without hitting the dishwasher, the counter, the
other arm or itself.

**How to touch.** Once the gripper reaches the plate, position control is no
longer the right language. Closing on a plate is about force, not position; so is
sliding it out of a rack it is wedged in. This layer is short in time — the last
centimetre and the last second — and it is where most tasks actually fail.

Now the useful part. In practice, the top layer is usually **programmed** and the
bottom layer is increasingly **learned**, for a good reason: the order of steps
is something a person can write down in a morning, while what to do in the last
centimetre is something even an expert cannot write down at all, though they can
demonstrate it. The middle two layers are contested, and that contest is what
most current robotics research is about.

Keep the layers in mind while reading the methods below. Several of them — a
motion planner, say — only ever answer one of the four questions, and comparing
them with a method that answers all four is comparing a wheel with a car.

---

## 3. The family tree

Here is the whole landscape in one picture. It is a tree because several of these
names are families rather than single methods: "reinforcement learning" in
particular covers four quite different things, and people arguing about it are
often arguing about different branches.

![The family tree of methods](../images/arms-training-methods/overview/taxonomy.svg)

Reading it from the left: the first split is the one from section 1, between
behaviour a person writes and behaviour that comes from data. Within the
programmed family, the branches run roughly from least to most sophisticated —
from replaying a recorded motion, through computing motions from a model, to
planning what to do and how to move together. Within the learned family, the
branches are divided by **where the learning signal comes from**: from a person's
demonstrations, from the robot's own practice, or from a large pool of data
collected by many robots elsewhere.

One family in the tree deserves attention because it is the quiet workhorse:
*learned pieces inside a programmed system*. Most deployed robots that use
machine learning at all use it this way — a classical system with one neural
network doing the perception — rather than the end-to-end approach that gets the
attention.

The sections that follow walk the tree branch by branch.

---

## 4. Programmed: a person writes the behaviour

### 4.1 Teach and replay

Described in section 1: drive the arm through the motion, record the waypoints,
play them back. Modern versions let you push the arm around by hand rather than
driving it with buttons, which is quicker and is called *lead-through* or
*kinesthetic teaching*.

It is worth being clear about why this survives despite being the oldest method
here. It requires no model of the robot, no camera, no simulation and no
programmer — an operator who knows the job can teach a new motion in an
afternoon. Against that, it assumes the world never changes. Move the fixture two
centimetres and every waypoint is wrong.

Because the technique is universal and vendor-specific, the documentation that
matters is whichever arm you have; the concept has not changed in decades.

### 4.2 Offline programming

The same idea, done in software. You build a model of the workcell — the arm, the
table, the fixtures, the part, all as CAD geometry — and write the motion against
that model, simulating it to check for collisions before anything moves. The
robot only sees the finished programme.

The reason this exists is economic rather than technical: teaching by hand
requires the production line to stop, and offline programming does not. It also
lets one person prepare a hundred variants of a job and test them all. It
inherits teach-and-replay's weakness, with a twist: now the programme is correct
with respect to *the model*, so any difference between the model and reality —
a fixture 3 mm from where the drawing says — becomes an error at run time.

[RoboDK](https://robodk.com/) is an accessible example of this category of tool,
and its documentation is a good way to see what the workflow feels like.

### 4.3 Scripted logic: state machines and behaviour trees

Everything above concerns a single motion. Real tasks are sequences with
conditions: if the gripper is empty, pick; if the pick failed, try again; if it
failed three times, stop and call someone. Writing that as ordinary code works
until it does not, because branching logic grows tangled quickly.

Robotics borrowed two structures for this. A **state machine** is a set of named
states with rules for moving between them. A **behaviour tree** arranges the task
as a tree of nodes that are ticked repeatedly, where each node reports success,
failure or "still running", and composite nodes like "do these in order until one
fails" or "try these until one succeeds" build up the logic. Behaviour trees came
from video games, where they organise non-player-character behaviour, and
robotics adopted them for the same property: they stay readable when the task has
fifty branches, and you can add a recovery behaviour without rewriting the rest.

This layer is almost always programmed, even in systems that are otherwise
heavily learned, because a person can state the order of steps easily and would
struggle to demonstrate it thousands of times.

[BehaviorTree.CPP](https://www.behaviortree.dev/) is the standard C++
implementation and its documentation explains the concepts well;
[py_trees](https://py-trees.readthedocs.io/) is the Python equivalent used in
ROS.

### 4.4 Motion planning

A motion planner answers the third layer's question: given the arm's current
configuration and a target, find a path that collides with nothing. It needs a
model of the robot (a URDF, as in this repo's [arm area](../arm/overview.md)) and
a model of the surroundings, usually built from a depth camera.

The problem is harder than it sounds because a six-joint arm has a six-dimensional
space of configurations, and the obstacles carve complicated forbidden regions
out of it. Two families attack this differently.

**Sampling-based planners** — RRT (rapidly-exploring random tree) and PRM
(probabilistic roadmap) are the two names you will meet — give up on
understanding the space and explore it randomly. They try random configurations,
keep the collision-free ones, and connect them into a tree or graph until a path
emerges. They are remarkably good at finding *a* path through awkward spaces, and
the path they find is typically ugly, wanders, and is different every run.

**Optimisation-based planners** start from a guess at the whole path and improve
it, pushing it away from obstacles while keeping it short and smooth. CHOMP and
TrajOpt are the classic names, and modern GPU-based solvers do it in
milliseconds. The paths are much nicer, and the method can fail by settling into
a poor solution where a sampling planner would have found a way through.

In ROS the practical entry point is [MoveIt 2](https://moveit.ai/), which wraps
both families behind one interface; its [documentation](https://moveit.picknik.ai/main/index.html)
is the place to start, and [OMPL](https://ompl.kavrakilab.org/) is the library
providing the sampling planners underneath. [cuRobo](https://curobo.org/) is the
modern GPU-parallel optimisation planner, fast enough to replan continuously.

### 4.5 Task and motion planning

Sometimes the choice of *what to do* and the choice of *how to move* cannot be
separated. To put a mug in a sink you may first have to move the pan that is in
the way — but whether you need to depends on geometry, and whether you *can*
depends on whether a collision-free path exists for the pan. Deciding the steps
without checking the motions produces plans that turn out to be impossible;
planning motions without deciding the steps has nothing to plan.

Task and motion planning, usually shortened to **TAMP**, searches both at once:
a symbolic layer proposes sequences of actions ("move pan, then grasp mug"), and
a geometric layer tests whether each proposed action is physically achievable,
feeding failures back. It is the most capable purely-programmed approach for long
multi-step tasks, and also the hardest to build and the slowest to run, which is
why it remains largely a research technique.

[PDDLStream](https://github.com/caelan/pddlstream) is a well-documented open
implementation and a reasonable way to see how the two layers talk to each other.

### 4.6 Feedback control

Underneath every method in this doc, something converts intentions into motor
commands and reacts to what actually happens. This is control, and four ideas
from it matter here.

**Inverse kinematics and trajectory tracking** are the basic layer: work out the
joint angles that put the gripper where you want it, and drive the joints along
the planned path. This repo's [arm area](../arm/overview.md) is about the maths
underneath this.

**Force control** matters the moment the arm touches something. Commanding a
position against a rigid surface is a good way to break something: the controller
sees an error it cannot remove, and pushes harder. The alternative is to command
*how the arm should respond to force* — behave like a spring of a given stiffness
— which is called impedance control, or its cousin admittance control. This is
what makes contact safe, and it is required for insertion, wiping, polishing and
for setting a stone down without knocking the tower over.

**Visual servoing** closes the loop on the camera rather than on a computed
position. Instead of working out where the object is in 3D and moving there, it
measures the difference between what the camera sees and what it should see, and
moves to reduce that difference. This sidesteps a whole class of calibration
errors, at the cost of needing the target in view.

**Model predictive control** repeatedly solves a short optimisation — "given
where I am and a model of the dynamics, what sequence of commands over the next
second is best?" — executes the first command, and re-solves. It is powerful when
you have a good model and enough compute, and it is how many legged and dynamic
systems are controlled.

In ROS, [ros2_control](https://control.ros.org/) is the framework these live in,
including a ready-made admittance controller.
[Drake](https://drake.mit.edu/) and [Pinocchio](https://github.com/stack-of-tasks/pinocchio)
are the serious model-based toolkits, [ViSP](https://visp.inria.fr/) is the
reference library for visual servoing, and
[MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc) lets you watch
predictive control work in an interactive simulator, which is the fastest way to
understand it.

---

## 5. Learning from demonstrations

Now the other family. The idea here is the oldest one in teaching: show the task,
repeatedly, and let the learner copy. It is the most practical learning method
for manipulation today, and this repo works through it in detail in the
[full training](../full-training/overview.md) docs.

### 5.1 Behaviour cloning

A person performs the task while everything is recorded: the camera images, the
arm's joint angles, and the commands the person was giving. A neural network is
then trained on that record to produce the command the person gave, given what
the cameras saw. Nothing about the task is described to it — not the objects, not
the goal, not the physics. It copies.

The naive version of this has been tried since the 1990s and works poorly, for a
reason worth understanding. Asked for one command per camera frame, the network
is queried fifty times a second, and each answer is a fresh opportunity to be
slightly wrong; the errors compound, the motion jitters, and the arm drifts into
situations the demonstrator never visited. Two developments fixed this enough to
matter.

The first is **action chunking**: instead of one command, the network predicts
the next hundred, and they are played out in order before it looks again. A
hundred steps at fifty per second is two seconds of coherent motion decided in
one go, which removes the jitter and — importantly for two arms — keeps the arms
in step with each other. This is what ACT, the policy behind the ALOHA results,
does.

The second is **generative modelling of the action**. Demonstrators are
inconsistent: asked to place the same stone twice, a person may choose two
different but equally good approaches. A network trained to output one number per
command will average them, and the average of two good motions is often a bad
one. Diffusion policies generate the action sequence the way image models
generate pictures — by refining noise — which lets them represent "either this
motion or that one" rather than the midpoint.

To read the good version: [ALOHA and ACT](https://tonyzhaozh.github.io/aloha/),
with the [paper](https://arxiv.org/abs/2304.13705), is the clearest demonstration
that this approach works on fiddly two-arm tasks;
[diffusion policy](https://diffusion-policy.cs.columbia.edu/)
([paper](https://arxiv.org/abs/2303.04137)) is the other half of the modern
recipe. [LeRobot](https://github.com/huggingface/lerobot) implements both and is
how you would actually run them, and [robomimic](https://robomimic.github.io/) is
a careful study of which details in this pipeline matter, which saves a great
deal of guessing.

### 5.2 Interactive imitation: correcting it as it goes

Behaviour cloning has one structural flaw. The policy only ever saw states that
the demonstrator, who was competent, put the robot in. The first time the policy
makes a small mistake it finds itself somewhere slightly unfamiliar, where its
next action is a little worse, which takes it somewhere less familiar still. The
failure is not that it is bad at the task; it is that it has never seen its own
mistakes.

The fix is to let the policy drive and correct it when it goes wrong, adding
those corrections to the training data. DAgger is the classic formulation, and
the modern practical version has a person watching the robot with a hand on a
controller, taking over when it is about to fail and handing back when it is
recovered. A few dozen such corrections are often worth several hundred fresh
demonstrations, because they cover exactly the situations the policy actually
gets into.

[The DAgger paper](https://arxiv.org/abs/1011.0686) is the original argument, and
[HIL-SERL](https://hil-serl.github.io/) is the modern system where human
take-overs feed a reinforcement learning loop on a real robot.

### 5.3 Learning the goal instead of the motion

A different idea: rather than copy what the demonstrator *did*, work out what
they were *trying to achieve*, and then optimise for that. If you can recover the
objective, you can pursue it in situations the demonstrations never covered,
which is more general than copying.

This is inverse reinforcement learning, with relatives including adversarial
imitation (train a discriminator to tell the robot's behaviour from the human's,
and have the robot try to fool it) and learning from preferences (show a person
two attempts, ask which was better, and fit a reward to the answers). The
generality is real, and so is the fragility: inferring intent from behaviour is
badly under-determined, and these methods are correspondingly finicky.

[GAIL](https://arxiv.org/abs/1606.03476) is the canonical adversarial version and
[learning from human preferences](https://arxiv.org/abs/1706.03741) the canonical
preference-based one; the latter is also the ancestor of the technique used to
tune language models.

---

## 6. Learning from trial and error

Reinforcement learning takes the opposite input. Instead of demonstrations, you
supply a **reward**: a number saying how well things are going. The robot tries,
observes the reward, and adjusts to get more of it.

The appeal is obvious — you need not be able to do the task yourself, only to
recognise success — and so is the difficulty. Getting the reward right is
genuinely hard, because any gap between what you wrote and what you meant will be
found and exploited. A robot rewarded for the height of a stack may learn to
throw a stone in the air. Practitioners call this reward hacking, and it is the
main reason RL projects fail.

The second difficulty is volume. Learning from scratch takes millions of attempts,
which no real robot will survive, so in practice reinforcement learning means
learning in simulation. That makes the simulator's fidelity the limiting factor,
which matters most for exactly the contact-rich tasks where learning is most
wanted.

Four branches differ enough to be worth separating.

**Model-free reinforcement learning** learns the behaviour directly from
experience, with no model of how the world works. PPO and SAC are the two
workhorses — PPO is the robust default for simulation, SAC is more
sample-efficient and fiddlier. Simple, general, and hungry: millions of episodes.

**Model-based reinforcement learning** first learns a model of the world, then
uses it to plan or to generate imagined experience for training. Since the model
can be reused and imagined attempts are free, this is far more sample-efficient,
at the cost of more moving parts. Dreamer and TD-MPC are the modern examples.

**Offline reinforcement learning** learns only from a fixed dataset of previously
recorded behaviour, without practising at all. This is attractive when a robot is
already running and generating logs, and it is hard to make reliable: the
algorithm must avoid over-estimating actions it has never actually seen tried.
IQL and CQL are the standard methods.

**Real-world reinforcement learning** practises on the actual robot. This solves
the fidelity problem by definition, and creates every other problem: attempts are
slow, the robot can damage itself, and someone must reset the scene between
attempts. Modern systems make it workable with careful safety limits, automatic
resets, and a human who can intervene.

**Crossing from simulation to reality** is its own subject. The dominant
technique is **domain randomisation**: rather than build one accurate simulator,
train across thousands of randomised ones — varying friction, mass, lighting,
delays — so that the real world looks like one more variation. This was what made
OpenAI's in-hand cube manipulation transfer, and it remains the default advice.

For reading: [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) is
the clearest implementation of the standard algorithms, with
[PPO](https://arxiv.org/abs/1707.06347) and
[SAC](https://arxiv.org/abs/1801.01290) as the source papers;
[DreamerV3](https://danijar.com/project/dreamerv3/) and
[TD-MPC2](https://www.tdmpc2.com/) are the model-based ones;
[IQL](https://arxiv.org/abs/2110.06169) and
[CQL](https://arxiv.org/abs/2006.04779) cover offline;
[Isaac Lab](https://isaac-sim.github.io/IsaacLab/) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) are
where the practising usually happens; the
[domain randomisation paper](https://arxiv.org/abs/1703.06907) is short and worth
reading in full; and [SERL](https://serl-robot.github.io/) shows RL running on a
real arm.

---

## 7. Learning from large-scale pretraining

The newest branch borrows the strategy that worked for language models. Rather
than train a model for your task, train one enormous model on as much robot data
as exists — often pooled from many different robots doing many different tasks —
and then adapt it to your task with a comparatively tiny number of examples.

These models are usually called **vision-language-action models**, or VLAs, and
the name describes the interface: they take camera images and a sentence, and
they output arm commands. Telling the robot what to do in words is not a gimmick;
it is what lets one model cover many tasks, since the instruction distinguishes
them.

The bet is that a model which has seen thousands of hours of manipulation has
learned something general about objects, grasping and contact, so it needs far
fewer examples of *your* task than training from scratch would. The evidence so
far is encouraging rather than conclusive: pretrained models do reach a given
success rate with several times less task-specific data, and they remain
expensive to run and prone to confident nonsense on anything sufficiently unlike
their training data.

[RT-2](https://robotics-transformer2.github.io/) is the paper that made the idea
visible, and [Open X-Embodiment](https://robotics-transformer-x.github.io/)
explains the pooled-dataset approach it depends on. For models you can actually
use, [OpenVLA](https://openvla.github.io/) and
[π₀](https://www.physicalintelligence.company/blog/pi0) (with
[code](https://github.com/Physical-Intelligence/openpi)) publish open weights,
[SmolVLA](https://huggingface.co/blog/smolvla) is small enough to fine-tune on
modest hardware, and [GR00T](https://github.com/NVIDIA/Isaac-GR00T) is the
humanoid-oriented one.

---

## 8. Learned pieces inside a programmed system

This is the least glamorous branch and by a wide margin the most deployed. The
idea: keep the classical system — planner, controller, logic — and replace only
the parts that require recognising something, which is precisely what classical
methods are worst at and learned ones are best at.

Three components account for most of it.

**Where to grasp.** Given a point cloud of a cluttered bin, a network proposes
places the gripper could close successfully, ranked. A conventional planner then
executes the best reachable one. This is the backbone of modern bin picking, and
it works on objects the system has never seen because the network learned what
grippable geometry looks like in general.

**What the object is, and where.** Segmentation networks say which pixels belong
to which object; pose estimators say how a known object is oriented. The recent
generation does this without needing to be trained on your specific object,
which removes the step that used to make this approach impractical.

**Whether something will work.** A learned model that scores candidates a
classical planner has generated — will this grasp hold, will this stack stay up —
is often the highest-value learning in a whole system, because the classical part
can generate thousands of candidates and only needs help choosing. The
[stone stacking doc](../stone-stacking.md#6-programmed-or-trained) describes
exactly this arrangement.

The value of this approach is that the system remains inspectable: when it fails
you can look at the proposed grasps, the estimated pose and the planned path, and
see which was wrong. You get generalisation exactly where you need it and
determinism everywhere else.

[Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) and
[GraspNet-1Billion](https://graspnet.net/) are the reference points for grasping,
[FoundationPose](https://nvlabs.github.io/FoundationPose/) for pose estimation
without per-object training, and
[Segment Anything](https://github.com/facebookresearch/segment-anything) for the
segmentation half.

---

## 9. Directed by language

The last branch is not a way of producing motion at all: it is a way of choosing
what to do, sitting above whatever produces the motion. A language model is given
the task in words, told what skills the robot has, and asked to decide the order
of the steps.

This works better than it sounds, for a specific reason: sequencing a familiar
task is a knowledge problem rather than a physical one, and knowledge is exactly
what a model trained on the internet has. It knows that spilled liquid suggests a
sponge, and that a dishwasher must be opened before it can be emptied. What it
does not know is what this particular robot can reach, which is why the useful
designs pair the model's suggestions with the robot's own estimate of whether
each step is achievable, and let the two vote.

There are three shapes worth knowing. In the first, the model **proposes steps**
and learned skills execute them. In the second, the model **writes code** that
calls the robot's perception and control functions — surprisingly effective, and
pleasantly debuggable, since the output is a short program you can read before
running. In the third, the model **produces spatial goals**, such as regions to
avoid or approach, which a conventional planner then uses.

[SayCan](https://say-can.github.io/) is the clearest example of the first shape,
[Code as Policies](https://code-as-policies.github.io/) of the second, and
[VoxPoser](https://voxposer.github.io/) of the third.
[Inner Monologue](https://innermonologue.github.io/) adds the obvious and
important refinement of telling the model when a step failed so it can replan.

---

## 10. The comparison grid

Here are the eight families side by side on twenty points. Before reading it,
three notes on how to use it.

**The columns are not interchangeable.** Some of these answer one of the four
layers from [section 2](#2-the-four-layers-of-any-arm-system) and some answer all
four. A motion planner and a vision-language-action model are not competitors;
they are different sizes of thing.

**The rows are what to argue about.** Rows 1 to 10 are what a method demands
before it will work at all, which is usually what decides the matter in practice.
Rows 11 to 20 are what you get in return.

**Vocabulary for the cells.** "None" means genuinely none. "Somewhat" means it
will cope with variation of the kind it has seen but not with a new kind.
"Deployed widely" means you can buy it; "research" means you would be building
it yourself from papers.

**What it asks of you**

| | Teach & replay | Offline prog. + planner | TAMP | Classical control | Imitation | RL (sim → real) | VLA fine-tune | Learned pieces in a classical stack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **1. What you must supply** | the motion | a CAD model | symbolic rules + geometry | a model of the robot | demonstrations | a reward | demonstrations | labelled data, or a ready model |
| **2. Robot model needed** | no | yes | yes | yes | no | yes (for sim) | no | no |
| **3. Demonstrations needed** | one, by hand | none | none | none | 50–1000+ | none | 10–500 | none |
| **4. Reward needed** | no | no | no | no | no | yes, and it is the hard part | no | no |
| **5. Simulator needed** | no | helpful | helpful | helpful | no | yes, in practice | no | no |
| **6. Training compute** | none | none | none | none | hours on one GPU | days, many GPUs | hours to days | hours |
| **7. Compute when running** | trivial | milliseconds to seconds | seconds or more | trivial | one network pass | one network pass | a large network pass | one network pass |
| **8. Time to something working** | hours | days | weeks | days | weeks | weeks to months | days, if a checkpoint fits | days |
| **9. Who has to be skilled** | an operator | a robot programmer | a researcher | a control engineer | anyone who can do the task | an RL practitioner | an ML engineer | an ML engineer |
| **10. Cost of a change later** | re-teach it | re-programme it | re-model it | re-tune it | collect more data | re-train, re-tune the reward | fine-tune again | retrain one component |

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

**What the grid says.** Read row 16 and row 19 together: the methods you can
debug are the methods industry has adopted, and that is not a coincidence — a
factory needs to know why a machine stopped. Then read rows 11 to 13, which are
the mirror image: the methods that cope with novelty and contact are the learned
ones, and those are the tasks nobody has managed to automate. The whole field is
currently working in the gap between those two observations.

The other thing the grid shows is that the *entry requirements* differ more than
the capabilities. Reinforcement learning needs a reward and a simulator; imitation
needs a way to demonstrate; TAMP needs a symbolic model of your domain. Very
often the choice is made not by which would work best but by which of those you
can actually produce.

---

## 11. What real systems actually do

Almost nothing real uses one method. The pattern, visible across every system
below, is the one from [section 2](#2-the-four-layers-of-any-arm-system): the top
of the stack tends to be programmed, the bottom tends to be learned, and the
interesting engineering is in where the line falls.

A few worth understanding properly, before the full table.

**A modern bin-picking cell** is a classical system with one learned component.
Motion planning, collision checking and gripper logic are conventional code; a
neural network proposes grasps on the point cloud. The split is deliberate: the
objects vary, so perception must generalise, but the motion does not need to, and
keeping it classical means the cell can be verified and explained.

**MIT's Jenga robot** inverts the usual assumption about what to learn. The
strategy and the controller are conventional; what is learned is a model of how
the block responds to being pushed, from vision and force together. The team
learned the part nobody can write down — contact behaviour — and programmed
everything else.

**MimicGen and its two-arm successor DexMimicGen** use programming to
*manufacture the data that training needs*. A classical routine takes a handful
of human demonstrations and transforms them into thousands of variants by
re-composing them around the objects' positions; a policy is then trained by
imitation on that generated data. Neither family could produce the result alone.

**SayCan** pairs a language model with learned skills, and its contribution is
the pairing rather than either half. The language model knows that a spill needs
a sponge; it has no idea whether this robot can reach the sponge. Each skill
carries a learned estimate of its own chance of succeeding right now, and the
step chosen is the one that is both sensible and feasible.

**Figure's Helix** splits by *speed*. A vision-language model runs at 7–9 Hz to
understand the scene and the instruction, and a separate visuomotor policy runs
at 200 Hz to produce the actual motion, taking the slower model's output as
context. Thinking and reacting have genuinely different timescales, so they are
two models rather than one.

The fuller list:

| System | Programmed part | Learned part | Why the split falls there |
| --- | --- | --- | --- |
| Typical industrial cell | taught or offline path, force control on insertion | often nothing | nothing varies, so learning buys little and costs verification |
| Bin picking, modern | planning, collision checking, gripper logic | grasp proposals, segmentation ([Contact-GraspNet](https://github.com/NVlabs/contact_graspnet)) | objects vary, motions do not |
| [ETH stone stacking](https://doi.org/10.1109/ICRA.2017.7989272) | all of it: scan, search poses in physics, plan, place | nothing | with a physics engine, the search is the reasoning |
| [MIT Jenga](https://news.mit.edu/2019/robot-jenga-0130) | strategy and control | a model of contact, from vision and force | contact is the part that cannot be written down |
| [MimicGen](https://mimicgen.github.io/) / [DexMimicGen](https://dexmimicgen.github.io) | the routine that multiplies demonstrations | the final policy, by imitation | programming manufactures the data training needs |
| [RoboTwin 2.0](https://github.com/RoboTwin-Platform/RoboTwin) | expert data generation, randomisation, evaluation | the policies under test | the benchmark is programmed, the subject is learned |
| [SayCan](https://say-can.github.io/) | the skill interfaces | language model picks steps; skills execute; learned values veto | the planner must know what is possible |
| [Code as Policies](https://code-as-policies.github.io/) | perception and control functions | a language model writes the glue | composition is language-shaped, primitives are not |
| [OpenAI's cube-solving hand](https://arxiv.org/abs/1910.07113) | the cube solver, a classical algorithm | in-hand finger motion, RL in simulation with heavy randomisation | solving the cube was solved; moving fingers was not |
| [HIL-SERL](https://hil-serl.github.io/) | safety limits, resets, the underlying controller | RL on the real robot, with human take-overs | real contact cannot be simulated well enough |
| [Figure's Helix](https://www.figure.ai/news/helix) | the robot's low-level stack | a VLM at 7–9 Hz, a visuomotor policy at 200 Hz | thinking and reacting run at different rates |
| [TRI's Large Behavior Models](https://toyotaresearchinstitute.github.io/lbm1/) | data collection and evaluation protocol | one diffusion model pretrained on ~1,700 hours, fine-tuned per task | pretraining reportedly cuts the data a new task needs several-fold |
| [ALOHA / ACT](https://tonyzhaozh.github.io/aloha/) | almost nothing above the controller | the entire task, from 50 demonstrations | the counter-example: sometimes copying is enough |

---

## 12. Which to use when

The honest decision procedure is shorter than the list of methods, because most
choices are forced by what you can produce rather than by what would work best.
Ask three questions in order.

**Can you write the task down?** If the scene is fixed and the motion is always
the same, teach it and stop reading. Automation's biggest wins still come from
recognising when a problem is this one.

**If not, what can you supply?** A model of the world points at planners. The
ability to demonstrate points at imitation. A way to score attempts, plus a
simulator, points at reinforcement learning. If you cannot supply any of the
three, the task is not ready to be automated yet, and the useful work is making
one of them possible.

**Where does the difficulty actually sit?** If it is in sequencing, programme the
sequence and do not learn it. If it is in recognising things, add a learned
perception component to a classical system. If it is in contact, that is the part
to learn.

In table form, with somewhere to start for each:

| If this is your situation | Start with | Worked example |
| --- | --- | --- |
| Parts arrive in the same place every time | teach and replay, or offline programming | any vendor's cell |
| The scene varies but the objects are known | a planner with learned perception | [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) |
| You need a machine that can be certified | classical throughout, force control for contact | [ros2_control](https://control.ros.org/) |
| The task is long, with ordering that matters | task and motion planning, or a language planner over skills | [PDDLStream](https://github.com/caelan/pddlstream), [SayCan](https://say-can.github.io/) |
| The hard part is contact, and you can demonstrate it | imitation learning with action chunking | [ACT](https://tonyzhaozh.github.io/aloha/), [diffusion policy](https://diffusion-policy.cs.columbia.edu/) |
| You cannot demonstrate it, but you can score it | reinforcement learning in simulation, then transfer | [Isaac Lab](https://isaac-sim.github.io/IsaacLab/), [domain randomisation](https://arxiv.org/abs/1703.06907) |
| You have a real robot and no simulator good enough | real-world RL with human take-overs | [HIL-SERL](https://hil-serl.github.io/) |
| You want one policy for many tasks, told in words | fine-tune a vision-language-action model | [π₀](https://github.com/Physical-Intelligence/openpi), [SmolVLA](https://huggingface.co/blog/smolvla) |
| A working classical system fails on perception | replace only the perception component | [FoundationPose](https://nvlabs.github.io/FoundationPose/) |
| A classical system works but is too slow | use it to generate data, then train a policy on that | [MimicGen](https://mimicgen.github.io/), [RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin) |
| You have logs from a deployed robot, and no simulator | offline RL, or imitation on the successful episodes | [IQL](https://arxiv.org/abs/2110.06169) |
| You are learning, and want to see it all work once | imitation, in simulation, on a two-arm task | [the two-arm route](../two-arm-manipulation.md) |

Three rules of thumb survive most arguments. **Programme what is easy to say and
learn what is not** — sequencing is easy to say, the last centimetre is not.
**Learning buys generalisation, and you pay in data**, so if you do not need
generalisation, do not pay. And whichever you choose, **the loop matters more
than the method**: run it, measure it, change one thing, as in the
[two-arm doc](../two-arm-manipulation.md#3-how-to-work-through-a-step).

---

## 13. Where this repo fits

Nearly everything in this repo sits in the programmed family, deliberately. The
learned methods are easier to understand once you know what they are replacing,
and the pieces they assume — frames, transforms, depth pictures, message passing
— are the same either way.

- [ROS basics](../ros/ros-basics.md) is the plumbing every method here runs on.
- [The arm area](../arm/overview.md) covers frames, transforms and kinematics:
  the model classical methods need explicitly and learned ones absorb implicitly.
- [The camera area](../camera/basics.md) and
  [finding objects](../camera/finding-objects.md) show a classical perception
  pipeline and a trained model doing the same job, which is the clearest small
  illustration of the trade this whole doc is about.
- [Two-arm manipulation](../two-arm-manipulation.md) lists the open projects for
  the learned family, in five steps.
- [Stone stacking](../stone-stacking.md) and
  [full training](../full-training/overview.md) take one task and work it through
  the programmed way and then the trained way.

None of the external systems described here were run in this repo; the links go
to the people who built them. Everything inside the repo has been run, and each
doc says so.
