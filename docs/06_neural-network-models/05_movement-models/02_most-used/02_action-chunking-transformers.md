# Action chunking transformers

This page explains ACT, which is short for Action Chunking with Transformers. ACT is a
movement model that looks at the robot's cameras and chooses the next burst of
moves all at once, instead of one move at a time. It was published in 2023 together
with ALOHA, a cheap two-armed robot for recording demonstrations. Today it is the
first policy most people train, usually through a software library called LeRobot.

The page answers five questions. What does ACT take in and give out? How does it
work inside? How is it trained, and on what? What are ALOHA and LeRobot? And when is
ACT the right choice?

It is for a reader who has read [behaviour cloning](01_behaviour-cloning.md). ACT is
a kind of behaviour cloning, and it was built to fix the problem of small mistakes
adding up that is described there.

## Contents

1. [What ACT is](#1-what-act-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [The three steps](#the-three-steps)
   · [The style numbers](#the-style-numbers)
   · [Blending overlapping chunks](#blending-overlapping-chunks)
4. [How it is trained](#4-how-it-is-trained)
5. [ALOHA and LeRobot](#5-aloha-and-lerobot)
6. [Well-known models of this kind](#6-well-known-models-of-this-kind)
7. [A worked example: a cup into a box with a cheap arm](#7-a-worked-example-a-cup-into-a-box-with-a-cheap-arm)
8. [What goes wrong](#8-what-goes-wrong)
9. [Why ACT, and what it costs](#9-why-act-and-what-it-costs)
10. [The written alternative](#10-the-written-alternative)
11. [Where to read next](#11-where-to-read-next)

---

## 1. What ACT is

ACT is a behaviour cloning policy that predicts a whole chunk of future moves at
each decision.

A **chunk** is a short list of moves, one after another. In ACT, a chunk is usually
100 moves long. The arm makes 50 moves a second, so one chunk covers the next two
seconds.

Here is an everyday example. When you pour water from a jug into a glass, you do not
decide what to do every hundredth of a second. You decide on the next second or so
of pouring: tip the jug, hold it, start to tip it back. Then you look at the glass
and decide again. You make a few decisions, and each one covers a stretch of
movement.

ACT does the same. The picture below compares a policy that decides one move at a
time with one that decides a chunk at a time.

![Twelve decisions of one move each, against two decisions of six moves each](../../../images/movement-models/action-chunking-transformers/one-step-vs-chunk.svg)

Each dot is a decision. With one move per decision, there are twelve chances for a
small mistake. With chunks, there are only two.

This is why chunking helps with compounding error, the adding-up of small mistakes
from [behaviour cloning](01_behaviour-cloning.md#small-mistakes-add-up). Mistakes
build on each other at each new decision. Fewer decisions means fewer chances for
them to build up.

The other half of the name is **transformer**. A transformer is a kind of neural
network. It takes a set of pieces, such as parts of a picture, and lets each piece
take information from every other piece. The main step inside it is called
**attention**: for each piece, the network works out which other pieces matter to
it, and how much. Transformers were first used for text, and are now used for
pictures and actions too.

---

## 2. What goes in and what comes out

In the original ACT, the robot is ALOHA, which has two arms. Each arm has six joints
and a gripper, so there are 14 numbers that describe where the robot is.

The observation has two parts.

- Four camera pictures, each 480 pixels tall and 640 pixels wide. One camera looks
  down from above, one looks from the front, and one sits on each wrist.
- The 14 current joint positions: six joint angles and one gripper opening for each
  arm.

The action is a chunk: 100 targets for each of the 14 joints. That is 1,400 numbers.
Each target is a joint position the arm should reach at one moment in the next two
seconds.

The targets are joint positions, not motor commands. Ordinary control code in each
joint moves the motor towards each target, as described in
[the chapter overview](../01_overview.md#2-why-a-movement-model-is-called-a-policy).

---

## 3. How it works inside

### The three steps

When ACT runs on the robot, the data goes through three steps.

1. **An image encoder turns each picture into a grid of numbers.** An **encoder** is
   the part of a network that turns its input into numbers the rest of the network
   can use. ACT uses ResNet-18, a small and well-known convolutional neural network
   (CNN). For each picture, it gives a small grid. Each cell of the grid holds a list
   of numbers that describe one patch of the picture.
2. **A transformer compares every piece with every other piece.** All the grid cells
   from all four cameras go into the transformer, together with the joint positions.
   Attention lets a piece from the wrist camera use a piece from the top camera. This
   is how the network can match "the gripper is here" with "the cup is there".
3. **The transformer gives out the chunk.** The last part of the transformer has 100
   slots, one for each future moment. Each slot is turned into 14 joint targets.

![Four camera pictures and the joint angles go in; 100 future targets for each joint come out](../../../images/movement-models/action-chunking-transformers/inside-act.svg)

The plot on the right shows the chunk for one joint, the elbow. It is 100 targets,
one every fiftieth of a second. The numbers in the plot are made up to show the
shape; a real chunk depends on the task.

### The style numbers

People do the same task in slightly different ways. One time the demonstrator moves
quickly, another time slowly. As the
[behaviour cloning page](01_behaviour-cloning.md#two-good-ways-become-one-bad-way)
shows, a network that has to give one answer blends these ways together.

ACT has a partial fix. During training only, a second small network looks at the
real chunk the person made. It sums up "how the person did it this time" in a few
numbers. We can call these the **style numbers**. The main network gets the style
numbers as an extra input. This way it does not have to blend different styles: the
style numbers tell it which one to produce.

At run time, there is no person, so there is no real chunk to look at. ACT sets the
style numbers to zero, which stands for the most typical style. The result is a
smooth, typical movement.

This design has a name: a **conditional variational autoencoder (CVAE)**. You do not
need the details. The idea is that some of the variation between demonstrations is
put into separate numbers, so it does not blur the actions.

It is only a partial fix. Setting the style to "typical" at run time still gives one
answer. If half the demonstrations go left of an obstacle and half go right, ACT can
still struggle. The [diffusion and flow policies](03_diffusion-and-flow-policies.md)
on the next page handle that case better.

### Blending overlapping chunks

A chunk covers two seconds. If the arm plays the whole chunk without looking again,
it cannot react to anything that happens during those two seconds. There are two
common ways to run ACT.

The first way is to play part or all of a chunk, then ask the policy for a new one.
This is simple. But the arm can jump a little where one chunk ends and the next
begins.

The second way is to ask the policy for a new chunk at every step, and blend them.
The ACT paper calls this **temporal ensembling**. "Temporal" means to do with time,
and "ensembling" means combining several guesses into one.

![Four overlapping chunks each predict the elbow angle for step 3, and the arm uses their weighted average](../../../images/movement-models/action-chunking-transformers/temporal-ensembling.svg)

At step 3, the chunks made at steps 0, 1, 2 and 3 all hold a target for step 3. The
arm uses a weighted average of them. A weighted average is an average where some
values count for more than others. This makes the movement smooth, because one odd
guess is outweighed by the others.

---

## 4. How it is trained

ACT is trained like any behaviour cloning policy, with one change: the answer is a
whole chunk, not one move.

The data is a set of demonstrations. At each moment of each demonstration, the
training program takes the pictures and joint positions as the question. It takes
the next 100 recorded joint positions as the answer. The loss is the size of the
difference between the predicted chunk and the recorded chunk, added up over all
1,400 numbers. The training program nudges the network to make that loss smaller.

How much data? In the ACT paper, each task was learned from about 50
demonstrations, which is about ten minutes of recording. The tasks were fine
two-handed tasks, such as opening a small plastic cup with a lid and slotting a
battery into a holder. This is much less data than people expected fine tasks to
need, and it is the main reason ACT became popular. The Book 3 page on
[data and demonstration](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#31-aloha-and-what-it-made-ordinary)
gives the reported success rates, and warns what they do and do not show.

Training runs on one ordinary graphics card. It does not need a cluster of
computers.

---

## 5. ALOHA and LeRobot

ACT is closely tied to two other names. You will meet both whenever you read about
it.

**ALOHA** is the robot ACT was built for. The name is short for A Low-cost
Open-source Hardware System for Bimanual Teleoperation. "Bimanual" means using two
hands. ALOHA has two follower arms, which do the task, and two smaller leader arms,
which a person holds and moves by hand. Each follower joint copies the matching
leader joint. There are four cameras.

![The person moves two small leader arms; two bigger follower arms copy them joint by joint](../../../images/movement-models/action-chunking-transformers/aloha-rig.svg)

The person moves the grey leader arms. The blue follower arms move to the same
joint angles and do the task, while the cameras and joint sensors record everything.

This way of recording has one big advantage. The person's hands do the task
directly, joint for joint, so they can control all 14 joints at once. That is very
hard with a joystick or a keyboard. The follower arms in the original ALOHA are
ViperX arms and the leader arms are WidowX arms, both sold by Trossen Robotics. The
designs were published openly, so other groups could build the same robot.

**LeRobot** is a free software library from the company Hugging Face, first
released in 2024. It holds, in one place, a standard way to store robot recordings,
the code to train several kinds of policy, and drivers for cheap robot arms. ACT is
one of its policies. LeRobot's own documentation calls ACT its recommended first
policy. The Book 3 page on
[LeRobot](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#71-what-it-is-and-why-it-won)
explains why it became the standard place to start.

LeRobot also works with cheap leader-and-follower arms, such as the SO-101. These
use the same leader-and-follower idea as ALOHA, with small hobby motors and
3D-printed parts. A pair costs a few hundred dollars, so a person can record ACT
demonstrations at home.

---

## 6. Well-known models of this kind

These are the main models and systems in the ACT line.

- **ACT** (2023) is the original. It was published with ALOHA, in a paper called
  "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware". Its original
  code is still online, but it is no longer updated; the maintained version is
  inside LeRobot.
- **ALOHA** (2023) is the two-armed recording robot described above.
- **Mobile ALOHA** (2024) put the ALOHA arms on a wheeled base, so the robot can
  move around a room. It trained ACT and other policies on mobile tasks, such as
  cooking and opening cupboards. It also showed that mixing in data from the
  original, fixed ALOHA helped the mobile tasks.
- **ALOHA 2** (2024), from Google DeepMind, is a sturdier redesign of the ALOHA
  hardware. Its designs and a simulation model were published.
- **LeRobot's ACT** is the version most people use today. It runs on cheap arms
  such as the SO-101.

The idea of predicting a chunk of actions spread well beyond ACT. Diffusion Policy,
on the [next page](03_diffusion-and-flow-policies.md), also outputs chunks. So do
the large
[vision-language-action models](../../06_language-models/02_most-used/01_vision-language-action-models.md),
such as π0. Almost every policy since ACT does some kind of chunking.

---

## 7. A worked example: a cup into a box with a cheap arm

Say you have one SO-101 follower arm with its leader arm, one camera looking down,
and one camera on the wrist. You want the arm to pick up a paper cup and drop it
into a box.

You record 50 demonstrations with LeRobot. For each one, you put the cup in a new
place and drive the follower with the leader arm. LeRobot saves the pictures, the
joint positions and the actions in its standard format.

You train ACT on those 50 demonstrations with LeRobot's training script, on one
graphics card.

You run the trained policy. Every time it is asked, it looks at both cameras and the
joint angles and gives the next chunk of joint targets. The arm reaches down, closes
the gripper, lifts, moves over the box, and opens.

Watch it closely and you will see the effect of chunking. The motion is smooth,
because each chunk is a smooth two-second plan. Now move the cup while the arm is
reaching. If the policy is playing a long chunk, the arm keeps going to the old
place for a moment before it reacts. That delay is the price of the chunk.

---

## 8. What goes wrong

ACT shares the problems of every behaviour cloning policy: it only works in
situations like the ones it was trained on, the cameras must stay where they were,
it cannot say "I don't know", and it knows nothing about collisions. These are
explained on the [behaviour cloning page](01_behaviour-cloning.md#other-problems).
It also has some problems of its own.

The chunk length is a trade-off. Longer chunks mean fewer decisions and less
adding-up of mistakes. But they also mean slower reactions. The ACT paper's own test,
reported in
[learned methods for one arm](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#11-behaviour-cloning),
went from 1% success with one move per decision to 44% with 100 moves per chunk,
and then got worse again with longer chunks. Those numbers are an average over
simulated tasks. The best length depends on your task, and you find it by trying.

The style numbers only partly fix the problem of two good ways becoming one bad way.
If the demonstrations really split into two different paths, ACT can still blend
them or switch between them. Recording demonstrations that all use the same way
helps. So does moving to a diffusion or flow policy.

Fifty demonstrations is enough for a narrow task. It is not enough for a task that
varies a lot. If the cup can be any colour, anywhere on the table, in any light, you
need many more demonstrations, recorded across all of that variety.

ACT learns one task at a time. It does not take a sentence as input, so it cannot be
told to do a different task. For that, see the
[vision-language-action models](../../06_language-models/02_most-used/01_vision-language-action-models.md).

---

## 9. Why ACT, and what it costs

ACT is a behaviour cloning policy that predicts two seconds of joint targets at a
time, using a transformer to combine pictures from several cameras.

It gives you smooth, fine movement from a small number of demonstrations, and it
does this on cheap hardware and one graphics card. That is why it is the usual first
policy for anyone starting out.

The first obvious alternative is plain behaviour cloning, which predicts one move
at a time. Plain behaviour cloning is a smaller network and reacts at every step. But
on real fine tasks its small mistakes add up quickly, and it usually fails where ACT
succeeds. Chunking is the main reason ACT works where plain copying did not.

The second obvious alternative is a
[diffusion or flow policy](03_diffusion-and-flow-policies.md). These handle tasks
with more than one good way of doing them better than ACT does. But they take
several clean-up steps to produce each chunk, so they are slower to run and usually
slower to train. When the demonstrations are consistent, ACT is simpler and cheaper,
and it is the sensible place to start. Move on to a diffusion or flow policy if ACT
blends different ways of doing the task.

What ACT costs you is mostly what behaviour cloning costs you: careful recording, a
policy that only works near its training data, and no way to check it in advance. On
top of that, you must choose a chunk length and live with the slower reactions that
a long chunk brings. And like every policy in this chapter, it needs ordinary control
and safety code underneath it.

---

## 10. The written alternative

ACT does the same job as behaviour cloning, so its written alternative is the same:
a route from [sampling-based
planning](../../../05_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md),
turned into smooth joint targets by [trajectory
generation](../../../05_programming-techniques/07_control-and-motion/02_most-used/02_trajectory-generation.md).
A written motion is planned as one whole movement, so it does not have the adding-up
of small mistakes that chunking was built to fix. Book 3's [programmed
methods](../../../03_frameworks/04_one-arm-training/02_programmed-methods.md) shows
the written parts working together on one arm.

The written motion wins when the objects and the task stay the same, because you can
check it before it runs. ACT wins when the task is fine and easier to show than to
write down, and you can record a few dozen demonstrations of it.

---

## 11. Where to read next

The next page, [diffusion and flow policies](03_diffusion-and-flow-policies.md),
keeps the chunks and adds a way to choose cleanly between different ways of doing a
task. To go back to the list of all five kinds, read
[the chapter overview](../01_overview.md).

To see how chunks of actions are used in very large policies that also take
sentences, read
[vision-language-action models](../../06_language-models/02_most-used/01_vision-language-action-models.md).
To see how a trained policy is run on a robot, read
[running a model on a robot](../../09_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md).

For deeper reading in Book 3,
[learned motion](../../../03_frameworks/03_arm-movement/05_learned-motion.md#1-which-part-of-the-move-a-policy-stands-in-for)
explains why chunking fixed the jerky motion of earlier policies, and lists ACT and
LeRobot with their licences.
[Data and demonstration](../../../03_frameworks/08_frontier/03_data-and-demonstration.md)
covers ALOHA, the SO-101 arm and LeRobot's data format in more detail.
