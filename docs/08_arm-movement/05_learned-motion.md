# Learned motion

A trained policy can move an arm. This document is about what that actually
replaces, what you can download in 2026, and the cases where learning is honestly
the wrong tool for moving an arm.

It does not repeat the taxonomy.
[Learned methods for one arm](../10_one-arm-training/03_learned-methods.md) sets
out the families — behaviour cloning, reinforcement learning, large-scale
pretraining, learned pieces inside a programmed system, language direction — and
whether each is worth learning. That is the map. This is the narrower question:
given an arm that has to get from here to there, which part of the motion stack
does a policy stand in for, and what does the rest of the stack still have to do.

The short answer, stated at the top because it is the point of the document, is
that **a policy almost never replaces the planner.** It replaces the segment of
motion nearest the object, where the difficulty is contact and perception rather
than routing. The free-space part of the move is solved by other means and
learning it is worse on every axis that matters.

## Contents

1. [Which part of the move a policy stands in for](#1-which-part-of-the-move-a-policy-stands-in-for)
2. [Policies you can download](#2-policies-you-can-download)
3. [Learned pieces inside a planned system](#3-learned-pieces-inside-a-planned-system)
4. [Reinforcement learning for contact](#4-reinforcement-learning-for-contact)
5. [The four things a policy does not have](#5-the-four-things-a-policy-does-not-have)
6. [Judging whether it works](#6-judging-whether-it-works)
7. [Where learning is and is not the right tool](#7-where-learning-is-and-is-not-the-right-tool)

---

## 1. Which part of the move a policy stands in for

The motion stack has five layers. Learning can enter at any of them, and the
consequences are entirely different.

| Layer | What it decides | What a policy would replace |
| --- | --- | --- |
| task | which move to make next | a language model or a high-level policy choosing the skill |
| path | the route through free space | a learned planner or a learned sampler |
| trajectory | the timing along that route | rarely anything; this layer is arithmetic |
| joint command | where each joint should be right now | the visuomotor policies of section 2, which output exactly this |
| contact | what force to apply and how to react | a reinforcement-learned contact policy |

The layer nearly every downloadable policy occupies is the fourth. A visuomotor
policy takes camera images and the arm's current state, and outputs either joint
positions or a tool-pose delta, at somewhere between 10 and 50 times a second.
It is not planning a route; it is choosing the next small motion, over and over,
the way a person does.

Two consequences follow and both are easy to miss.

**The policy still needs a controller underneath it.** A stream of joint targets
at 15 Hz is not a motor command. Something has to interpolate it up to the
hundreds of hertz the hardware runs at, respect the joint velocity and
acceleration limits, and decide what to do when the policy asks for something the
arm cannot deliver. That something is everything in
[controlling the move](04_controlling-the-move.md), and it does not go away.

**The gap between the policy's rate and the controller's rate is where the
jerkiness comes from.** A 10 Hz policy driving a 500 Hz controller means each
output is held or interpolated across 50 control cycles. Hold it and the arm
moves in steps. Interpolate it naively and the arm is always a tenth of a second
behind what the policy decided. This is a real engineering problem with a real
answer — action chunking, below — and it is not visible in any published success
rate.

**Action chunking** is the idea that made imitation learning work on real arms.
Instead of predicting the next action, the policy predicts the next fifty or so
and the system executes them as a block, with overlapping predictions blended
together. It was the central contribution of ACT, and it fixes two problems at
once: the arm no longer pauses between decisions, and the compounding error from
predicting one step at a time is bounded by the length of the chunk. Nearly every
policy since does some version of it.

## 2. Policies you can download

Read the table below as: what each one is, what its code licence is, what its
weights licence is, and whether the two agree. The last column is the one to
check, because code and weights very often differ and the repository badge only
describes the code. Every licence here was read from the project's own LICENSE
file or model card.

| Policy | What it is | Code licence | Weights | State |
| --- | --- | --- | --- | --- |
| [ACT](https://github.com/tonyzhaozh/act) | action-chunking transformer; the imitation baseline everyone reimplements | MIT | trained by you | research code, last pushed July 2024; the maintained version is inside LeRobot |
| [Diffusion Policy](https://github.com/real-stanford/diffusion_policy) | denoises an action chunk instead of regressing it; better at multi-modal behaviour | MIT | trained by you | last pushed December 2024; also reimplemented in LeRobot |
| [Octo](https://github.com/octo-models/octo) | early open generalist policy, trained on Open X-Embodiment | MIT | MIT | last pushed July 2024; superseded but still cited |
| [OpenVLA](https://github.com/openvla/openvla) | 7-billion-parameter vision-language-action model | MIT | MIT on Hugging Face | last pushed March 2025 |
| [openpi](https://github.com/Physical-Intelligence/openpi) | Physical Intelligence's π₀ and π₀.₅ | Apache-2.0 | **no stated licence** — see below | very active, 14k stars |
| [GR00T N1.5](https://github.com/NVIDIA/Isaac-GR00T) | NVIDIA's open foundation model for manipulation | Apache-2.0 | **NVIDIA One Way Noncommercial** | active, 8k stars |
| [RDT-1B](https://github.com/thu-ml/RoboticsDiffusionTransformer) | diffusion foundation model for bimanual manipulation | MIT | MIT | last pushed January 2026 |
| [SmolVLA](https://huggingface.co/lerobot/smolvla_base) | small vision-language-action model built for consumer hardware | Apache-2.0 | Apache-2.0 | part of LeRobot, active |
| [LeRobot](https://github.com/huggingface/lerobot) | the framework the others now ship inside: datasets, training, evaluation | Apache-2.0 | per policy | extremely active, 27k stars, pushed daily |

### 2.1 The two licence traps

**GR00T N1.5's weights are non-commercial and its code is not.** The repository
is Apache-2.0, which looks entirely permissive. The model card for
`nvidia/GR00T-N1.5-3B` says "This model is ready for non-commercial use" and
links the NVIDIA One Way Noncommercial License. So you may ship the code and you
may not ship the model, which is the pattern the
[perception area's licence document](../06_object-perception/06_licences-and-platforms.md#1-licences-and-the-one-that-will-catch-you-out)
warns about in a different corner of the field, for the same reason: people read
the badge.

**openpi's checkpoints have no stated licence at all.** The repository is
Apache-2.0. The checkpoints are distributed from a Google Cloud Storage bucket,
`gs://openpi-assets`, and the README that lists them names no separate terms for
them. That is not the same as permission. Absent a statement, what governs the
weights is not established, and "no licence" is a weaker position than a
restrictive one, because default copyright grants nothing.

### 2.2 What runs on an Apple Silicon Mac

The framework answer is good and the foundation-model answer is not.

**LeRobot runs on a Mac and says so in code.** Its device selection tries CUDA
first, then Metal, and returns `torch.device("mps")` when Metal is available. So
training a small policy such as SmolVLA, and running any of the LeRobot-hosted
policies for inference, works on Apple Silicon without special effort.

**openpi does not.** Its README states the minimum requirement as an NVIDIA GPU —
more than 8 GB for inference, more than 22.5 GB for LoRA fine-tuning, more than
70 GB for full fine-tuning — and says plainly that the repository has been tested
with Ubuntu 22.04 and that other operating systems are not currently supported.

The general rule is the same as in perception: a policy reimplemented inside a
portable framework often runs where its original repository does not, and "the
repository needs CUDA" and "it will not run on your Mac" are different statements.

### 2.3 Five jobs a downloadable visuomotor policy suits

- a short manipulation skill you can demonstrate a few hundred times, where the
  variation is in the object rather than in the task
- tasks whose difficulty is contact and whose geometry you cannot write down:
  wiping, folding, unplugging, opening a drawer
- deformable objects, where there is no pose to estimate and therefore nothing
  for a planner to plan to
- a task where the object's appearance rather than its geometry decides what to
  do
- research and evaluation, where the point is the comparison rather than the
  deployment

### 2.4 Five jobs it cannot do

- guarantee it will not hit something. There is no planning scene, no collision
  check, and no mechanism by which the policy could be given one
- generalise to a camera in a different place. Move the wrist camera 30 mm and
  the policy's inputs are outside its training distribution, with no warning
- decline. A policy always emits an action. It has no way to say that it does not
  recognise the situation, which is the argument
  [the perception overview](../06_object-perception/01_overview.md#21-when-a-model-makes-things-worse)
  makes about detectors and which is stronger here, because an action moves a
  physical arm
- explain a failure. When the arm does the wrong thing there is no waypoint to
  point at, and the diagnosis is to collect more data and hope
- cover the long free-space move, which is solved, deterministic and free in the
  programmed stack

## 3. Learned pieces inside a planned system

This is where learning has most clearly paid for itself in motion, and it gets
much less attention than end-to-end policies because it is unglamorous.

**Learned inverse kinematics.** A network trained on an arm's kinematics can
produce a joint solution in a fixed, tiny time, and — this is the useful part —
can produce a *distribution* of solutions for a redundant arm rather than one
answer. It removes the timeout problem from
[section 8.1 of reaching and reachability](02_reaching-and-reachability.md#81-the-solvers-answer-is-weaker-than-it-looks),
because inference time does not depend on how awkward the pose is.

**Learned collision distance.** A network that maps a configuration to a distance
from the nearest obstacle gives an optimiser the smooth gradient it needs without
maintaining a distance field, and evaluates in microseconds. This is one of the
things that makes graphics-card planning fast.

**Learned motion policies that replace the planner for free space.**
[Motion Policy Networks](https://github.com/NVlabs/motion-policy-networks), MIT,
is the clearest example: a network trained on millions of planner outputs that
produces a collision-free motion directly from a point cloud, in a fixed time,
where the planner it imitates takes a variable time. The honest framing is that
this is a planner compressed into a network, not a new capability — and that
fixed time is a genuine capability when the alternative's ninety-ninth percentile
is a second.

**Learned samplers.** Instead of drawing configurations uniformly, draw them from
a distribution trained to favour regions where the solution tends to be. The
planner is unchanged and converges faster.

Five jobs this pattern suits:

- an existing planned system whose planning time varies too much
- a redundant arm where choosing among infinitely many solutions needs a policy
  anyway
- optimisation-based planning, which needs a smooth obstacle cost and is happy to
  get it from a network
- generating a good initial guess for an optimiser, where a rough answer fast is
  worth more than an exact answer slowly
- anywhere you have a slow correct method and need a fast approximate one, since
  the slow method generates the training data for free

Five jobs it cannot do:

- offer a guarantee. The network is an approximation of the planner and can
  return a path the planner would have rejected, so the output still has to be
  checked
- transfer to a different arm, because the kinematics it learned are the
  kinematics it was trained on
- handle an obstacle configuration unlike anything in training, which for a
  point-cloud input means an unusual scene shape rather than an unusual object
- replace the collision checker, only the cost used while searching
- be debugged. When it returns a bad path there is nothing to inspect

## 4. Reinforcement learning for contact

If learning has a home in arm movement, it is the last twenty millimetres.
Insertion, seating, and search-until-it-drops-in are tasks where the right
behaviour is a reactive policy conditioned on force, where the demonstration is
hard to give by hand, and where a simulator can produce millions of attempts.

The practical shape is nearly always the same: train in simulation, transfer to
hardware, and accept that the transfer is the hard part rather than the training.
The tools, with licences read from their repositories:

| Tool | Licence | What it is for | Apple Silicon |
| --- | --- | --- | --- |
| [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) | MIT | the reference algorithm implementations | yes |
| [robosuite](https://github.com/ARISE-Initiative/robosuite) | MIT | manipulation environments on MuJoCo | yes, since MuJoCo runs natively |
| [MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) | Apache-2.0 | GPU-accelerated MuJoCo environments | partly — MuJoCo runs, the accelerated path does not |
| [Isaac Lab](https://github.com/isaac-sim/IsaacLab) | BSD-3 | NVIDIA's large-scale training framework | no — it needs Isaac Sim and an NVIDIA card |
| [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) | Apache-2.0 | a newer fast simulator | partly |

Five jobs it suits:

- peg-in-hole and connector insertion with tolerances tighter than your sensing
- any task where the correct action depends on a force you cannot predict
- learning a search pattern, which is tedious to write and easy to score
- tasks where a simulator models the contact adequately, which means rigid parts
  with simple geometry
- refining a programmed strategy that works most of the time, rather than
  replacing it

Five jobs it cannot do:

- transfer from a simulator whose contact model is wrong, which is most of them
  for soft, curved, brittle or slippery things. The
  [perception area says this plainly](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you)
  and it is the single largest limitation here
- train on hardware in any reasonable time, because the sample counts are in the
  millions and the arm is one arm
- give a safety argument, since the policy's outputs are unbounded by
  construction and have to be bounded by something else
- work without a reward you can compute, which for "the connector is seated"
  means instrumenting the thing
- cover the approach as well as the contact, so the programmed stack is still
  needed for everything up to first touch

## 5. The four things a policy does not have

Worth stating as a list, because each one is something the programmed stack
supplies for free and which nothing in the learned stack replaces.

**A planning scene.** The policy has no model of the obstacles and cannot be
given one. Whatever prevents the arm from driving into the table is a separate
mechanism that sits underneath the policy and overrides it, and building that
mechanism means building the collision checking from
[section 7 of planning a path](03_planning-a-path.md#7-the-planning-scene-and-what-collision-checking-really-checks)
anyway.

**A notion of reachability.** The policy emits a tool-pose delta. If that delta
is unreachable, the controller underneath clamps it or the IK fails, and what the
policy observes next is a world that did not respond the way it expected. It has
no way to distinguish "I asked for the wrong thing" from "the world is unusual".

**A way to refuse.** There is no confidence threshold that means anything, no
mechanism for declining, and no state in which the policy does nothing. The
[perception area's account of declining as a mechanism](../06_object-perception/07_making-it-work.md#6-declining-as-a-mechanism-rather-than-an-intention)
applies here with more force, because the consequence of proceeding is an arm
that moves.

**Repeatability.** Two runs from the same starting state can differ, and for a
diffusion policy they differ by design, because sampling different modes is the
whole point. A cell that must do the same thing every time cannot use one without
something above it constraining the result.

## 6. Judging whether it works

Three points, and the first two are the same arguments the perception area makes
about mAP, transposed.

**The published success rate is on the setup it was tuned on.** Almost every
number in this field is measured with the same arm, the same cameras in the same
places, the same lighting, and the same objects. None of those is your setup, and
the relationship between their number and yours is not known. Treat a published
success rate as evidence that the method works at all, not as a prediction.

**Count the failures that happen after committing, separately.** A policy that
succeeds 18 times out of 20 and knocks the part off the bench twice is worse than
one that succeeds 15 times and stops harmlessly 5 times, for anything that costs
money to break. One number cannot express that, so use two.

**Evaluate the whole system, not the policy.** The policy is one layer of five,
and a failure at the joint-command layer is indistinguishable from a failure at
the contact layer if you only look at whether the task succeeded. Log the
commanded and actual tool poses alongside the outcome, so that section 9 of
[controlling the move](04_controlling-the-move.md#9-a-diagnosis-ladder) is
available to you.

## 7. Where learning is and is not the right tool

**Learning is the right tool** when the behaviour is easier to demonstrate than
to describe, when the difficulty is in contact or in appearance, when the object
has no pose worth estimating, and when you have a simulator whose physics you
trust for the specific contact involved.

**Learning is the wrong tool** for free-space motion. This deserves saying
bluntly because the demonstrations do not distinguish it. Getting an arm from one
side of a bench to the other without hitting anything is solved, deterministic,
fast, verifiable and free. A learned policy doing the same job is slower to
develop, impossible to certify, worse at generalising to a new obstacle, and
needs a collision check underneath it anyway. Every minute spent teaching a
network to route around a fixture is a minute not spent on the part of the task
that is actually hard.

**Learning is the wrong tool** when the scene is fixtured. If the part arrives in
the same place every time, the whole question disappears and a taught pose
answers it. This is the same argument
[the overview](01_overview.md#2-what-your-task-actually-needs) makes about
planners, and it is worth making twice.

**Learning is the wrong tool** when you have to state in advance what the machine
will do. Nothing in this document can be written down as a guarantee, and some
buyers require one.

**And learning is the wrong tool when it costs you the ability to iterate.** A
rule tested against a generated family runs in a second with no weights and no
graphics card. A policy's test loop needs a dataset, a device and a training run.
The speed at which you can try a new idea is not separate from the architecture;
it is caused by it, and it is usually the thing that decides whether a project
finishes.

Next: [licences and platforms](06_licences-and-platforms.md), which puts every
licence and platform question in this area in one place. Or back to
[the overview](01_overview.md).
