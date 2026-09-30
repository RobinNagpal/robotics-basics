# Diffusion and flow policies

This page answers one question. When people show a robot arm the same task in
different ways, how can a model copy them without mixing the ways together? The
answer is a kind of movement model called a diffusion policy, and its faster
relative, the flow policy.

The page is for a reader who has met the two pages before it:
[behaviour cloning](01_behaviour-cloning.md), which copies demonstrations, and
[action chunking transformers](02_action-chunking-transformers.md), which plan a
short run of movements at a time. You do not need any maths. Every new word is
explained where it first appears.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [Diffusion and flow matching: the difference](#4-diffusion-and-flow-matching-the-difference)
5. [How it is trained](#5-how-it-is-trained)
6. [Well-known models of this kind](#6-well-known-models-of-this-kind)
7. [A worked example: reaching round a box to a mug](#7-a-worked-example-reaching-round-a-box-to-a-mug)
8. [What goes wrong, and what people do about it](#8-what-goes-wrong-and-what-people-do-about-it)
9. [Why this kind, and what it costs](#9-why-this-kind-and-what-it-costs)
10. [The written alternative](#10-the-written-alternative)
11. [Where to read next](#11-where-to-read-next)

---

## 1. What it is

Here is the one-sentence idea. A diffusion policy starts from a random guess at
the arm's next movements, and cleans that guess up in several small steps until it
looks like something a person really did.

A **policy** is the name for any model that decides what the arm does next. It
looks at the world and gives back an action. An **action** is a movement command,
such as "move the gripper 1 cm to the left and close it a little".

To see why a new kind of policy was needed, think about an everyday example. You
ask six people to carry a mug from one side of a table to the other. There is a
box in the middle. Three people go round the left of the box. Three people go
round the right. All six did the job well.

Now suppose a simple model learns from these six people. A simple model gives one
answer for each situation, and it tries to be as close as possible to all six
people at once. The answer closest to "three go left and three go right" is the
middle. So the model learns to go straight through the middle, into the box. None
of the six people ever did that.

![Demonstrations go over or under a box; the average of them goes into the box](../../../images/movement-models/diffusion-and-flow-policies/average-goes-through.svg)

The left picture shows the problem: the red dashed line is the average of the
pale demonstrations, and it runs into the box. The right picture shows what a
diffusion policy does instead: each time it runs, it picks one whole path that
looks like a real demonstration.

A task with more than one good way to do it is called **multi-modal**. A **mode**
is one of the good ways. Going left is one mode and going right is another.
Diffusion policies were built to handle multi-modal tasks. They learn the whole
spread of ways that people did the task, and each time they run, they pick one of
them.

A **flow policy** does the same job with a method called **flow matching**. It
usually needs fewer clean-up steps, so it runs faster.
[Section 4](#4-diffusion-and-flow-matching-the-difference) explains the difference.

---

## 2. What goes in and what comes out

A diffusion policy for a robot arm takes in three things.

- **The latest camera pictures.** Often there is one camera looking at the table
  and one camera on the wrist of the arm. Some policies take the last two or three
  pictures, so they can see which way things are moving.
- **The arm's own state.** This is the angle of each joint and how open the
  gripper is. The arm's own sensors measure these numbers.
- **Some random numbers.** This is the starting guess that gets cleaned up. It is
  called **noise**, because it is random and has no meaning yet.

It gives back a **chunk** of actions. A chunk is a short list of the next
movements, one after another, such as the next sixteen positions for the gripper.
The [action chunking page](02_action-chunking-transformers.md) explains why a chunk
works better than one action at a time. Diffusion policies use chunks for the same
reasons.

The table below shows one concrete example. Read each row as one kind of input or
output, with what it looks like for an arm picking up a mug.

| | What it is | An example for picking up a mug |
| --- | --- | --- |
| In | camera pictures | one picture from above the table, one from the wrist |
| In | arm state | six joint angles and the gripper width |
| In | noise | a list of random numbers, the same size as the output |
| Out | an action chunk | the next sixteen gripper positions, each with "open" or "closed" |

---

## 3. How it works inside

The cleaning-up happens in steps. Each step uses the same neural network. A
**neural network** is a large calculation with many adjustable numbers, which a
computer tunes by showing it examples. Chapter 1 explains this in
[inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md).

Here is what happens each time the policy is asked for a new chunk.

1. The policy looks at the camera pictures and the arm state. A part of the
   network turns them into a list of numbers that describes the scene.
2. The policy makes a random chunk. Every position in it is random, so the chunk
   is a messy scatter of points.
3. The network looks at three things: the scene description, the messy chunk, and
   how many clean-up steps are left. It works out which way each point should move
   to look more like a real movement.
4. The policy moves each point a little in that direction.
5. Steps 3 and 4 repeat. After the last step, the chunk is a clean, smooth path.
6. The arm plays the first part of the chunk. Then the policy looks again and makes
   a new chunk.

![Random dots are moved a little at each step until they form a clean path round the box](../../../images/movement-models/diffusion-and-flow-policies/noise-to-path.svg)

The picture shows one chunk being cleaned up. At the start the dots are random. At
each step every dot moves a little, and by the last step they form a path from the
start round the box to the mug.

Why does this avoid the average? The answer is in step 2. The random start is
different each time. If the random dots happen to lean a little towards the top,
the clean-up pulls them into the "go over" path. If they lean towards the bottom,
the clean-up pulls them into the "go under" path. The network has learned where
real paths are. It has not learned a single answer. So the random start decides
which real path you get, and you never get the impossible middle.

The last step in the list, playing only part of the chunk, matters on a real
robot. The world can change while the arm moves. A mug can be nudged. So the
policy plays a few movements, looks again, and plans again. This pattern is
sometimes called **receding horizon**, because the plan always reaches a fixed
distance ahead of where the arm is now.

![Each plan is eight positions; the arm plays four, then a new plan starts](../../../images/movement-models/diffusion-and-flow-policies/predict-play-repeat.svg)

In the picture, each row is one plan of eight positions. The arm plays the four
filled positions, throws away the four hollow ones, and starts a new plan from
where it now is.

---

## 4. Diffusion and flow matching: the difference

Diffusion and flow matching both turn noise into a good chunk. They differ in how
the network learns the way from noise to the answer.

In **diffusion**, the network learns to remove a little noise at a time. The idea
came from models that make pictures. Those models learn to turn a screen of random
coloured dots into a photo. A diffusion policy does the same thing with a list of
arm positions instead of a picture. The path from noise to answer is wiggly, so it
usually takes many small steps.

In **flow matching**, the network learns a direction to travel from the noise to
the answer. During training, the method connects each noise sample to a real chunk
by a straight line, and the network learns to point along those lines. Because the
lines are straight, the policy can take a few big steps instead of many small ones.

![Diffusion walks from noise to an answer in many small steps; flow matching takes a few straight steps](../../../images/movement-models/diffusion-and-flow-policies/many-steps-or-few.svg)

The left picture shows the many small, wobbly steps of diffusion. The right picture
shows the few straight steps of flow matching, which end at the same kind of answer
in less time.

Speed matters here because the network runs once per step. If a policy needs many
steps and each takes a few thousandths of a second, the arm waits. Fewer steps
means the arm can get a new chunk more often. This is one main reason most large
robot models built in 2025 and 2026 use flow matching for their actions.

The table below compares the two. Read across each row.

| | Diffusion | Flow matching |
| --- | --- | --- |
| What the network learns | how to remove a little noise | which direction to travel |
| Shape of the way from noise to answer | wiggly | close to a straight line |
| Clean-up steps needed | many | few |
| Handles several good ways to do a task | yes | yes |
| Where you meet it | Diffusion Policy, RDT-1B, Octo | π0 and most newer large robot models |

---

## 5. How it is trained

A diffusion policy learns from **demonstrations**. A demonstration is one recording
of a person doing the task by driving the robot. The recording keeps the camera
pictures, the joint angles, and the commands the person gave, all at the same
moments. Chapter 1 explains where such recordings come from, in
[where the data comes from](../../01_what-models-are/05_where-the-data-comes-from.md).

Training a diffusion policy works like this.

1. Take a short piece of one demonstration: the pictures at one moment, and the
   next sixteen actions the person really took.
2. Add a known amount of random noise to those sixteen actions, so they become
   messy.
3. Ask the network which way the messy actions should move to get back to the
   real ones.
4. Compare its answer with the right answer, which you know, because you added the
   noise yourself.
5. Adjust the network's numbers a little so the next answer is closer.
6. Repeat with many pieces and many different amounts of noise.

Flow matching training is almost the same. The difference is in step 3: the network
is asked for the straight-line direction from the noise to the real actions.

How much data does this need? For one task, such as "put the mug on the plate",
people usually record somewhere between tens and a few hundred demonstrations.
Large general models that do many tasks are trained on far more, pooled from many
robots, and then adjusted to a new task with a smaller set. The
[vision-language-action page](../../07_language-models/02_most-used/01_vision-language-action-models.md)
covers those.

Training needs a computer with a graphics card. A **graphics card**, or graphics
processing unit (GPU), is a chip that does many small sums at once, which is what
training a network mostly is.

---

## 6. Well-known models of this kind

These are real, published models. Each line says what it is in plain words.

- **Diffusion Policy** (Columbia University, Toyota Research Institute and MIT,
  2023). This is the paper that made the idea popular for robot arms. It takes camera
  pictures and makes a chunk of actions by diffusion. It showed clearly that the
  approach copes with tasks that have several good ways to do them.
- **3D Diffusion Policy, or DP3** (2024). It does the same job, but its input is a
  3D point cloud instead of flat pictures. A **point cloud** is a list of 3D dots
  on the surfaces a depth camera sees. The
  [point cloud models page](../../04_3d-models/02_most-used/01_point-cloud-models.md) explains these.
- **Consistency Policy** (2024). It takes a trained diffusion policy and teaches a
  second network to jump to the answer in one or a few steps, so it runs much faster.
- **Octo** (2024). An early open, general model trained on many robots' data. It
  uses a small diffusion part at the end to produce its actions.
- **RDT-1B** (Tsinghua University, 2024). A large diffusion model built for robots
  with two arms working together.
- **π0, said "pi zero"** (Physical Intelligence, 2024). A large model that
  understands pictures and words. It uses flow matching in a separate part, called
  the action expert, to turn its understanding into arm movements.

You can download and run Diffusion Policy inside the LeRobot framework, which the
[learned motion document](../../../03_frameworks/03_arm-movement/05_learned-motion.md#2-policies-you-can-download)
lists together with each project's licence.

---

## 7. A worked example: reaching round a box to a mug

Suppose you want a small arm to pick up a mug and put it on a plate. A cereal box
stands between the arm and the mug. You record 100 demonstrations. In some of them
you went round the left of the box, and in some you went round the right, because
that is what felt natural each time.

First, you train a plain behaviour-cloning policy on the recordings. On the robot,
it heads for the box, slows down near it, and bumps into it. It learned the middle
of the two ways.

Next, you train a diffusion policy on the same recordings. Here is what happens on
the robot.

1. The two cameras send a picture each, and the arm reports its joint angles.
2. The policy makes a random chunk of sixteen gripper positions and cleans it up in
   several steps. This time the random start leans left, so the chunk goes round
   the left of the box.
3. The arm plays the first eight positions.
4. The policy looks again. It is already on the left, so the new chunk carries on
   round the left. It does not switch sides halfway, because a path that switches
   halfway does not look like any demonstration.
5. Near the mug, the chunks slow down and bring the gripper round the handle, as the
   demonstrations did. The gripper closes.
6. The policy carries the mug to the plate in the same way and opens the gripper.

The next time you run it, the random start may lean right. Then the arm goes round
the right. Both runs are correct. They are also different, and section 8 explains
why that can be a problem.

---

## 8. What goes wrong, and what people do about it

**It is slower than a plain policy.** Each chunk needs several passes through the
network, where a plain policy needs one. People reduce the number of steps with
flow matching or with a faster version such as Consistency Policy. They also run
the next chunk's clean-up while the arm is still playing the current chunk.

**It does not do the same thing twice.** Two runs from the same start can take
different paths, by design. A factory cell that must repeat exactly the same motion
cannot accept that. People fix the random start to the same numbers each time, or
they put a classical check above the policy.

**It only knows the situations it was shown.** Like every copying method, it is
confused by a scene unlike its demonstrations: a new table colour, a camera moved
by a few centimetres, or a mug it has never seen. The fix is more varied
demonstrations, which cost time.

**It has no idea of obstacles it was not shown.** The policy does not check for
collisions. If you put a new object in the way, it may drive into it. A separate
safety layer under the policy has to stop the arm. The
[learned motion document](../../../03_frameworks/03_arm-movement/05_learned-motion.md#5-the-four-things-a-policy-does-not-have)
lists what a policy lacks and what has to sit around it.

**Its advantage is not always proven.** A 2026 study found that on its tests,
flow matching did no better than plain copying, while running several times more
slowly. The
[what is changing document](../../../03_frameworks/04_one-arm-training/05_what-is-changing.md#flow-matching-and-an-honest-doubt-about-it)
describes it. So try the simpler policy first, and measure whether the diffusion
version really helps on your task.

---

## 9. Why this kind, and what it costs

The obvious alternative is plain behaviour cloning, which gives one answer for each
situation. It is simpler, faster, and easier to understand.

You choose a diffusion or flow policy when your demonstrations really contain
several good ways to do the task, and averaging them would be wrong. Reaching round
an obstacle is one example. Grasping a mug by the handle or by the rim is another.
Folding a cloth, where people fold in different orders, is a third.

What it gives you is a policy that stays inside one of the real ways of doing the
task, instead of a blend that nobody ever performed.

What it costs you is speed and repeatability. It needs several network passes per
chunk. Its results vary from run to run. It also needs the same amount of careful
demonstration data as any copying method, and a graphics card to train on.

The table below sums up the choice. Read each row as a question you might ask about
your task.

| Question about your task | If the answer is yes |
| --- | --- |
| Is there only one sensible way to do it? | plain behaviour cloning or ACT is enough |
| Did people do it in clearly different ways? | a diffusion or flow policy is worth trying |
| Must the motion be the same every run? | neither; use a programmed motion |
| Is the policy too slow on your computer? | use flow matching, fewer steps, or a smaller model |

---

## 10. The written alternative

The written way to reach round an obstacle is a motion planner. [Sampling-based
planning](../../../05_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md)
is told where the box is, finds one route round it, and checks that route for
collisions. It returns one route, so it never blends a way round the left with a way
round the right. [Trajectory
generation](../../../05_programming-techniques/07_control-and-motion/02_most-used/02_trajectory-generation.md)
then makes that route smooth. Book 3's [planning a
path](../../../03_frameworks/03_arm-movement/03_planning-a-path.md) explains how
these planners behave on a real arm.

The written way wins when the obstacles can be measured and the motion must be the
same on every run. A diffusion or flow policy wins when the task has several good
ways that are easy to show but hard to write down, such as folding a cloth in
different orders.

---

## 11. Where to read next

In this chapter:

- [Behaviour cloning](01_behaviour-cloning.md) explains copying demonstrations, and
  the drifting problem that chunks help with.
- [Action chunking transformers](02_action-chunking-transformers.md) explains chunks
  in detail.
- [Reinforcement learning policies](../03_also-used/01_reinforcement-learning-policies.md) is the
  next page. It learns by trying and scoring, instead of by copying.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Vision-language-action models](../../07_language-models/02_most-used/01_vision-language-action-models.md)
  are large models that use flow matching inside them.
- [Running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains why speed matters on a real arm.

Deeper documents elsewhere in this repository:

- [Learned methods for one arm, behaviour cloning](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#11-behaviour-cloning)
  covers diffusion and flow matching in more detail, with evidence.
- [Learned motion](../../../03_frameworks/03_arm-movement/05_learned-motion.md) explains
  which part of an arm's movement a policy should and should not replace.
