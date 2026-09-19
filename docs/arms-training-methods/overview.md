# Ways to train or programme a robot arm

There is no single way to make an arm do something complicated. There are about
a dozen, they split into two families, and every system that actually works in
the world is a **mix** of several of them.

This doc lays them all out: what each one is, what it costs, when to reach for
it, and where to read the good version of it. It is a map. The
[stone stacking](../stone-stacking.md) and
[full training](../full-training/overview.md) docs are two paths across it.

## Contents

1. [The family tree](#1-the-family-tree)
2. [Programmed: a person writes the behaviour](#2-programmed-a-person-writes-the-behaviour)
3. [Learned from demonstrations](#3-learned-from-demonstrations)
4. [Learned from trial and error](#4-learned-from-trial-and-error)
5. [Learned from large pretraining](#5-learned-from-large-pretraining)
6. [Learned pieces inside a programmed stack](#6-learned-pieces-inside-a-programmed-stack)
7. [Directed by language](#7-directed-by-language)
8. [The comparison grid](#8-the-comparison-grid)
9. [Mixes that are actually used](#9-mixes-that-are-actually-used)
10. [Which to use when](#10-which-to-use-when)
11. [Where this repo fits](#11-where-this-repo-fits)

---

## 1. The family tree

![The family tree of methods](../images/arms-training-methods/overview/taxonomy.svg)

Two families, and the split is simply **where the behaviour comes from**. In the
programmed family a person decides what the arm does and writes it down, in
code, in a plan, or by leading the arm through it. In the learned family the
behaviour comes from examples or from practice, and nobody can point at the line
where it is written.

Both families have nested types, which is where most of the confusion lives:
"reinforcement learning" is four quite different things depending on whether it
learns a model, and whether it practises in simulation, on a real robot, or only
from logs. The tree above is the shape of this doc: sections 2 to 7 walk it.

The other axis, which cuts across the tree, is **which layer of the system you
are talking about**. A robot doing a real job has four layers, and the usual
answer is a different family at each:

![The four layers, and what usually fills each](../images/arms-training-methods/overview/layers.svg)

---

## 2. Programmed: a person writes the behaviour

### Teach and replay

Lead the arm through the motion — by hand, or with a teach pendant — record the
waypoints, and play them back. This is how the majority of industrial arms
installed today are still programmed. It is unbeatable when the parts arrive in
the same place every time, and useless the moment they do not.

Read more: any arm vendor's teach-pendant manual; the idea has not changed in
forty years.

### Offline programming

Write the path against a CAD model of the cell, simulate it, then send it to the
robot. Same idea as teach and replay, but the "teaching" happens in software, so
the line does not have to stop while you do it.

Read more: [RoboDK](https://robodk.com/) is the accessible example of the tool
category.

### Scripted logic

The task as a program: a state machine, or a **behaviour tree** — the structure
that games use for non-player characters and that robotics adopted for the same
reason, that it stays readable when the task grows to fifty branches.

Read more: [BehaviorTree.CPP](https://www.behaviortree.dev/),
[py_trees](https://py-trees.readthedocs.io/).

### Motion planning

Given where the arm is and where it should be, find a path that hits nothing.
Two nested kinds:

- **Sampling-based** (RRT, PRM): throw random configurations at the problem and
  connect the ones that are collision-free. Finds a path in awkward spaces, but
  the path is ugly and different every time.
- **Optimisation-based** (CHOMP, TrajOpt, and GPU-era solvers): start from a
  guess and push it away from obstacles while keeping it short and smooth.
  Prettier and faster, and it can fail by getting stuck.

Read more: [MoveIt 2](https://moveit.ai/) and its
[docs](https://moveit.picknik.ai/main/index.html),
[OMPL](https://ompl.kavrakilab.org/) for the sampling family,
[cuRobo](https://curobo.org/) for the modern GPU-parallel optimisation family.

### Task and motion planning

Deciding *what to do* and *how to move* at the same time, because the two
interact: "put the mug in the sink" may require moving the pan first, and
whether that is even possible depends on geometry. TAMP searches over symbolic
plans and geometric motions together. Powerful, and the hardest thing on this
page to get working.

Read more: [PDDLStream](https://github.com/caelan/pddlstream).

### Feedback control

Underneath all of the above, something turns "go there" into motor commands and
reacts to what happens:

- **Inverse kinematics and trajectory tracking** — the basic layer, and what
  this repo's [arm area](../arm/overview.md) is about.
- **Force control: impedance and admittance** — instead of commanding a
  position, command how stiff the arm should be. This is what makes contact safe
  and is essential for insertion, wiping, polishing and placing.
- **Visual servoing** — steer by the camera: drive the difference between what
  you see and what you want to see to zero, without ever computing a 3D pose.
- **Model predictive control** — re-solve a short optimisation every few
  milliseconds using a model of the robot. Strong when you have a good model.

Read more: [ros2_control](https://control.ros.org/) for the ROS 2 stack,
[Drake](https://drake.mit.edu/) and [Pinocchio](https://github.com/stack-of-tasks/pinocchio)
for the model-based side, [ViSP](https://visp.inria.fr/) for visual servoing,
[MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc) for predictive
control you can watch.

---

## 3. Learned from demonstrations

Show the task; the policy copies. This is the most practical learning method
today, and the whole of the [full training doc](../full-training/overview.md).

### Behaviour cloning

Record a person doing the task, then train a network to output what they did.
The modern versions predict a **chunk** of future actions rather than one step,
which is what made this work on contact-rich, two-arm tasks:

- **ACT** — the action-chunking transformer behind the ALOHA results.
- **Diffusion policy** — generates the action sequence by denoising; copes
  better when demonstrators disagree with each other.

Read more: [ALOHA and ACT](https://tonyzhaozh.github.io/aloha/)
([paper](https://arxiv.org/abs/2304.13705)),
[diffusion policy](https://diffusion-policy.cs.columbia.edu/)
([paper](https://arxiv.org/abs/2303.04137)),
[LeRobot](https://github.com/huggingface/lerobot) to run either,
[robomimic](https://robomimic.github.io/) for the careful study of what matters.

### Interactive imitation

Plain cloning has one deep flaw: the policy only ever saw states where the
demonstrator was in control, so its own mistakes take it somewhere it has never
been. The fix is to let it drive and correct it when it goes wrong — DAgger and
its human-gated descendants.

Read more: [the DAgger paper](https://arxiv.org/abs/1011.0686),
[HIL-SERL](https://hil-serl.github.io/) for the modern version where human
take-overs feed a real-robot RL loop.

### Learning the reward instead of the actions

Rather than copy the motion, infer *what the demonstrator was trying to do*, and
then optimise that. Inverse reinforcement learning, adversarial imitation, and
learning from human preferences all sit here. More general than cloning,
considerably more fragile.

Read more: [GAIL](https://arxiv.org/abs/1606.03476),
[learning from human preferences](https://arxiv.org/abs/1706.03741).

---

## 4. Learned from trial and error

Reinforcement learning: define what "good" means, let the robot practise, keep
what works. Four nested kinds, and they behave very differently.

- **Model-free RL** (PPO, SAC) — learn directly from experience with no model of
  the world. Simple and general; needs an enormous number of attempts, so in
  practice it means simulation.
- **Model-based RL** (Dreamer, TD-MPC) — learn a model of the world, then plan or
  train inside it. Far more sample-efficient, and more machinery.
- **Offline RL** (IQL, CQL) — learn only from a fixed pile of logged data, with
  no practising at all. Attractive when a robot is already running and producing
  data; hard to make reliable.
- **Real-world RL** — practise on the actual robot, usually with human
  supervision and resets. Slow and risky, but it learns the real contact physics
  rather than the simulator's.

The bridge from simulated practice to a real robot is its own subject:
**domain randomisation** (train across many randomised worlds so reality is just
one more sample) and system identification (measure the real thing and fix the
simulator).

Read more: [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) for
the algorithms, [PPO](https://arxiv.org/abs/1707.06347) and
[SAC](https://arxiv.org/abs/1801.01290) for the two workhorses,
[DreamerV3](https://danijar.com/project/dreamerv3/) and
[TD-MPC2](https://www.tdmpc2.com/) for model-based,
[IQL](https://arxiv.org/abs/2110.06169) and [CQL](https://arxiv.org/abs/2006.04779)
for offline, [Isaac Lab](https://isaac-sim.github.io/IsaacLab/) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) for
where the practising happens,
[domain randomisation](https://arxiv.org/abs/1703.06907) for the transfer idea,
and [SERL](https://serl-robot.github.io/) for RL on a real arm.

---

## 5. Learned from large pretraining

Train one large model on enormous amounts of robot data — often pooled across
many robot types — then fine-tune it on your task with a comparatively tiny
dataset. These are **vision-language-action models**: pictures and a sentence
in, arm commands out.

The bet is the same one that worked in language: that a model which has seen
everything transfers to the thing you care about with far fewer examples than
training from scratch would need. The evidence is genuinely encouraging and not
yet conclusive.

Read more: [RT-2](https://robotics-transformer2.github.io/),
[Open X-Embodiment](https://robotics-transformer-x.github.io/) for the pooled
dataset idea, [OpenVLA](https://openvla.github.io/) and
[π₀](https://www.physicalintelligence.company/blog/pi0)
([code](https://github.com/Physical-Intelligence/openpi)) for open weights,
[SmolVLA](https://huggingface.co/blog/smolvla) for a small one you can actually
fine-tune, [GR00T](https://github.com/NVIDIA/Isaac-GR00T) for the humanoid
version.

---

## 6. Learned pieces inside a programmed stack

The quietest and most widely deployed use of learning: keep the classical
pipeline, and replace the parts that need to recognise something.

- **Where to grasp** — a network proposes grasp poses on a point cloud, and a
  classical planner executes them.
- **What and where the object is** — segmentation and 6D pose estimation,
  increasingly from models that need no CAD file and no task-specific training.
- **Will this work** — learned stability or cost models that score candidates a
  planner generated, which is the cheapest useful learning in a system like
  [stone stacking](../stone-stacking.md#6-programmed-or-trained).

Read more: [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) and
[GraspNet-1Billion](https://graspnet.net/) for grasping,
[FoundationPose](https://nvlabs.github.io/FoundationPose/) for pose estimation
without training per object,
[Segment Anything](https://github.com/facebookresearch/segment-anything) for the
segmentation half.

---

## 7. Directed by language

A language model sits above either family and decides the *order* of things:
which step comes next, and sometimes writing the code that calls the skills.
The skills underneath are still programmed or learned by the methods above —
this layer only chooses between them.

- **Plan with a language model, act with learned skills** — the model proposes
  steps, and the robot's own skill values decide which are actually possible.
- **Code as policies** — the model writes a short program that calls perception
  and control functions. Surprisingly effective, and legible, because the output
  is code you can read.
- **Language to spatial goals** — the model produces cost maps or waypoints for
  a planner rather than actions.

Read more: [SayCan](https://say-can.github.io/),
[Code as Policies](https://code-as-policies.github.io/),
[VoxPoser](https://voxposer.github.io/),
[Inner Monologue](https://innermonologue.github.io/) for feeding failures back
to the planner.

---

## 8. The comparison grid

Eight families across twenty points. Two tables, because twenty rows in one
table is unreadable; the columns are the same in both.

**What it asks of you**

| | Teach & replay | Offline prog. + planner | TAMP | Classical control | Imitation | RL (sim → real) | VLA fine-tune | Learned pieces in a classical stack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **1. What you must supply** | the motion | a CAD model | symbolic rules + geometry | a model of the robot | demonstrations | a reward | demonstrations | labelled perception data, or a ready model |
| **2. Robot model needed** | no | yes | yes | yes | no | yes (for sim) | no | no |
| **3. Demonstrations needed** | one, by hand | none | none | none | 50–1000+ | none | 10–500 | none |
| **4. Reward needed** | no | no | no | no | no | **yes, and it is the hard part** | no | no |
| **5. Simulator needed** | no | helpful | helpful | helpful | no | **yes, in practice** | no | no |
| **6. Training compute** | none | none | none | none | hours on one GPU | days, many GPUs | hours to days | hours |
| **7. Compute when running** | trivial | planner, ms–s | seconds+ | trivial | one network pass | one network pass | large network pass | one network pass |
| **8. Time to something working** | hours | days | weeks | days | weeks | weeks–months | days (if a checkpoint fits) | days |
| **9. Who has to be skilled** | an operator | a robot programmer | a researcher | a control engineer | anyone who can do the task | an RL practitioner | an ML engineer | an ML engineer |
| **10. Iteration cost afterwards** | re-teach | re-programme | re-model | re-tune | collect more data | re-train, re-tune reward | fine-tune again | retrain one component |

**What you get**

| | Teach & replay | Offline prog. + planner | TAMP | Classical control | Imitation | RL (sim → real) | VLA fine-tune | Learned pieces in a classical stack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **11. Novel objects** | no | no | limited | no | somewhat | somewhat | **best of these** | **yes, that is the point** |
| **12. Contact-rich work** | poor | poor | poor | **good** | **good** | **good** | good | n/a |
| **13. Long-horizon tasks** | yes, if fixed | yes | **yes, by design** | no | poor | poor | improving | n/a |
| **14. New task, no new code** | no | no | partly | no | no | no | **partly** | no |
| **15. Copes with a changed scene** | no | no | yes | n/a | somewhat | somewhat | yes | yes |
| **16. Can you see why it failed** | **yes** | **yes** | **yes** | **yes** | no | no | no | partly |
| **17. Safety story** | **strong** | **strong** | strong | **strong** | weak | weak | weak | inherits the stack's |
| **18. Risk while learning** | none | none | none | none | none (offline) | **high on real hardware** | none | none |
| **19. Industrial maturity** | **decades** | **decades** | research | **decades** | early deployment | niche | early | **deployed widely** |
| **20. How it typically fails** | the part moved | the world differed from CAD | no plan found, or too slow | model was wrong | drifts into unseen states | won't transfer from sim | confidently wrong | one component's blind spot |

Read the grid by row, not by column: **no column wins**. Rows 16 to 19 are why
industry still runs on the left-hand columns, and rows 11 to 13 are why research
is in the right-hand ones.

---

## 9. Mixes that are actually used

Almost nothing real is one method. Here is what the split looks like in systems
you can read about.

| System | Programmed part | Learned part | Why that split |
| --- | --- | --- | --- |
| Typical industrial cell | teach-and-replay or offline path, force control on insertion | often nothing; increasingly a grasp or pose network | the scene is fixed, so learning buys little and costs verification |
| Bin picking (modern) | motion planning, collision checking, gripper logic | grasp pose prediction, segmentation ([Contact-GraspNet](https://github.com/NVlabs/contact_graspnet)) | objects vary, so perception must generalise; motion need not |
| [ETH stone stacking](https://doi.org/10.1109/ICRA.2017.7989272) | everything: scan, physics search for the pose, plan, place | nothing | with a physics engine the search *is* the reasoning |
| [MIT Jenga](https://news.mit.edu/2019/robot-jenga-0130) | the manipulation strategy and controller | a model of how the block responds, learned from vision and force | the contact behaviour is what no one can write down |
| [MimicGen](https://mimicgen.github.io/) / [DexMimicGen](https://dexmimicgen.github.io) | a classical routine transforms a few demos into thousands | the final policy is imitation-learned on that generated data | programming is used to *manufacture the data* that training needs |
| [RoboTwin 2.0](https://github.com/RoboTwin-Platform/RoboTwin) | simulated expert generation, randomisation, evaluation protocol | the policies being benchmarked (ACT, diffusion, VLAs) | the benchmark is programmed; the thing under test is learned |
| [SayCan](https://say-can.github.io/) | the skill library's interfaces | language model picks the step; learned skills execute; learned value functions veto | the planner needs to know what is *possible*, which only the skills know |
| [Code as Policies](https://code-as-policies.github.io/) | perception and control APIs | a language model writes the glue code | the composition is language-shaped; the primitives are not |
| [OpenAI's Rubik's cube hand](https://arxiv.org/abs/1910.07113) | the cube solver itself — a classical algorithm | the in-hand manipulation, RL in simulation with heavy randomisation | solving the cube is solved; moving fingers is not |
| [HIL-SERL](https://hil-serl.github.io/) | safety limits, resets, the controller underneath | RL on the real robot, with a human taking over on bad states | real contact cannot be simulated well enough, so practise for real, carefully |
| [Figure's Helix](https://www.figure.ai/news/helix) | the split itself, and the robot's low-level stack | a vision-language model at 7–9 Hz for understanding, a visuomotor policy at 200 Hz for acting | slow thinking and fast reacting have different rates, so they are different models |
| [TRI's Large Behavior Models](https://toyotaresearchinstitute.github.io/lbm1/) | data collection and evaluation protocol | one diffusion transformer, pretrained on ~1,700 hours, then fine-tuned per task | pretraining is reported to cut the data a new task needs several-fold |
| [ALOHA / ACT](https://tonyzhaozh.github.io/aloha/) | almost nothing above the controller | the whole task, from 50 demonstrations | the counter-example: sometimes cloning alone is enough |

The pattern across that table: **the top of the stack is programmed, the bottom
is learned, and the middle is where the argument is.** Language planners took
over the top from state machines; policies took the bottom from hand-written
controllers; which of them owns "pick the object and put it there" is the live
question of the moment.

---

## 10. Which to use when

| If this is your situation | Start with | Worked example to copy |
| --- | --- | --- |
| The parts arrive in the same place, every time | teach and replay, or offline programming | any vendor cell |
| The scene changes but the objects are known | planner + learned perception | [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) |
| You need a safe, certifiable machine | classical everything, force control for contact | [ros2_control](https://control.ros.org/) |
| The task is long and combinatorial (many steps, ordering matters) | task and motion planning, or a language planner over skills | [PDDLStream](https://github.com/caelan/pddlstream), [SayCan](https://say-can.github.io/) |
| The hard part is contact, and you can demonstrate it | imitation learning with chunked actions | [ACT](https://tonyzhaozh.github.io/aloha/), [diffusion policy](https://diffusion-policy.cs.columbia.edu/) |
| You cannot demonstrate it, but you can score it | RL in simulation, then transfer | [Isaac Lab](https://isaac-sim.github.io/IsaacLab/), [domain randomisation](https://arxiv.org/abs/1703.06907) |
| You have a real robot and no simulator good enough | real-world RL with human take-overs | [HIL-SERL](https://hil-serl.github.io/) |
| You want one policy for many tasks, told in words | fine-tune a VLA | [π₀ / openpi](https://github.com/Physical-Intelligence/openpi), [SmolVLA](https://huggingface.co/blog/smolvla) |
| You have a working classical system that fails on perception | swap in a learned perception component only | [FoundationPose](https://nvlabs.github.io/FoundationPose/) |
| You have a classical system that is slow but correct | use it to generate data, then train a policy on it | [MimicGen](https://mimicgen.github.io/), [RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin) |
| You have logs from a deployed robot and no simulator | offline RL, or just imitation on the good episodes | [IQL](https://arxiv.org/abs/2110.06169) |
| You are learning, and want to see all of it work once | imitation, in simulation, on a two-arm task | [the two-arm route](../two-arm-manipulation.md) |

Three rules of thumb that hold up across all of it:

1. **Programme what is easy to say; learn what is not.** Sequencing is easy to
   say. What to do in the last centimetre is not.
2. **Learning is a way of buying generalisation with data.** If you do not need
   generalisation, do not pay.
3. **Whatever you pick, the loop matters more than the method**: run it, measure
   it, change one thing. That is the same advice as the
   [two-arm doc](../two-arm-manipulation.md#3-how-to-work-through-a-step).

---

## 11. Where this repo fits

This repo is almost entirely in the programmed family, deliberately, because
those are the parts you have to understand before the learned ones mean
anything:

- [ROS basics](../ros/ros-basics.md) — the plumbing every one of these methods
  runs on.
- [The arm area](../arm/overview.md) — frames, transforms and kinematics: the
  model that classical methods need and learned ones quietly rediscover.
- [The camera area](../camera/basics.md) and
  [finding objects](../camera/finding-objects.md) — a classical perception
  pipeline, and then a trained model doing the same job, side by side.
- [Two-arm manipulation](../two-arm-manipulation.md) — the open projects for the
  learned family, in five steps.
- [Stone stacking](../stone-stacking.md) and
  [full training](../full-training/overview.md) — one task, worked through the
  programmed way and then the trained way.

None of the external systems in this doc were run here; the links go to the
people who did. Everything inside the repo has been run, and says so.
