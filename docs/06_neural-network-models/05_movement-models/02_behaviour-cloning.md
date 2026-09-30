# Behaviour cloning

This page explains behaviour cloning, the simplest way to teach a robot arm to move
by itself. A person does a task many times while the robot records everything. A
neural network then learns to copy what the person did.

The page answers five questions. What goes into a behaviour cloning model, and what
comes out? How does the model learn? How much recording does it need? What goes
wrong when you use it on a real arm? And why would you choose it over writing the
motion by hand?

It is for a reader who has read [the chapter overview](01_overview.md), and knows
what a policy, an observation and an action are. If you have not read
[how a model learns](../01_what-models-are/02_how-a-model-learns.md), read that
first. This page uses its idea of a model making a guess, being told the right
answer, and adjusting.

## Contents

1. [What behaviour cloning is](#1-what-behaviour-cloning-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
6. [A worked example: picking up a mug](#6-a-worked-example-picking-up-a-mug)
7. [What goes wrong](#7-what-goes-wrong)
   · [Small mistakes add up](#small-mistakes-add-up)
   · [Two good ways become one bad way](#two-good-ways-become-one-bad-way)
   · [Other problems](#other-problems)
8. [Why behaviour cloning, and what it costs](#8-why-behaviour-cloning-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What behaviour cloning is

Behaviour cloning means training a network to copy what a person did in each
situation.

Here is an everyday example. Imagine you are learning to make tea by watching a
friend. You do not ask them to explain the rules. You watch what they do at each
moment. The kettle has boiled, so they pour. The cup is full, so they stop. Later you
make tea yourself by doing what they did in the same situation.

Behaviour cloning works the same way. The situation is what the robot's cameras see
and where its joints are. The thing to copy is the move the person made next.

A few words are needed for this.

- A **demonstration** is one recording of a person doing the task once, from start
  to finish. People also call it an **episode**.
- **Teleoperation** means a person controls the robot from a distance, with some
  kind of controller. It is the most common way to record demonstrations. The
  robot's own sensors then record exactly what the robot did.
- The **demonstrator** is the person who does the task during recording.

The word "cloning" means making a copy. The model tries to make a copy of the
demonstrator's behaviour.

---

## 2. What goes in and what comes out

A behaviour cloning model is a policy, so it turns an observation into an action.

For a robot arm, the observation usually has two parts. The first part is one or
more camera pictures, taken at this moment. The second part is the arm's current
joint angles, read from the sensors in each joint.

The action is what the arm should do next. It is usually one of two things.

- The joint angles the arm should move to next. For a six-joint arm, that is six
  numbers.
- How far the gripper should move, forwards and back, left and right, up and down,
  and how much it should turn.

Either way, one more number says how open or closed the gripper should be.

A demonstration is recorded as a long list of moments, often 10 to 50 moments a
second. At each moment the recording holds the pictures, the joint angles, and the
move the person made next. The picture below shows four moments from a recording of
someone picking up a mug.

![Four moments from a recording: the picture, the joint angles, and the move the person made next](../../images/movement-models/behaviour-cloning/demonstration-pairs.svg)

Each column is one moment. The picture and the joint angles are the question, and
the green box is the answer the network must learn to give.

This is the key point. The whole recording is cut into many small question-and-answer
pairs. Each pair says: "in this situation, the person did this". The network never
sees the task as a whole. It only sees many separate moments.

---

## 3. How it works inside

A behaviour cloning model is an ordinary neural network. It has three parts, and the
data flows through them in order.

1. **The picture part.** The camera picture goes into a network that is good at
   pictures. This is often a **convolutional neural network (CNN)**, a kind of
   network that looks at small patches of the picture at a time. A common choice is
   ResNet, a well-known CNN. This part turns the picture into a list of a few hundred
   numbers. The numbers describe what is in the picture, such as where the mug is.
   [Inside a neural network](../01_what-models-are/03_inside-a-neural-network.md)
   explains how this works.
2. **Joining.** The list of numbers from the picture is joined with the joint angles.
   Now one list describes the whole situation.
3. **The deciding part.** A few more layers of the network turn that list into the
   action numbers: the next joint angles and the gripper opening.

Training works like any other network. For each question-and-answer pair, the
network makes a guess. The guess is compared with the move the person actually made.
The difference between them is called the **loss**. If the network guessed 62
degrees and the person moved to 63 degrees, the loss for that joint is 1 degree. The
training program then nudges every number inside the network a tiny amount, so that
the next guess is a little closer. It does this over and over, for every pair, many
times.

When training is finished, the network is run on the robot. It takes the live
camera picture and joint angles, and gives an action. The arm makes that move. Then
the network takes the next picture and gives the next action.

Some versions also give the network the last few pictures, not just the current one.
This helps it tell whether the arm is moving up or down, which one picture cannot
show.

---

## 4. How it is trained

The data is a set of demonstrations of one task. There are three common ways to
record them.

- **Leader and follower arms.** The person moves a small copy of the robot arm by
  hand. The real arm copies each joint angle. This is how the ALOHA system records
  its data, and it is described on
  [the next page](03_action-chunking-transformers.md#5-aloha-and-lerobot).
- **A handheld controller or a virtual reality headset.** The person moves a
  controller in the air, and the robot's gripper follows it.
- **Moving the arm by hand.** Some arms let you push them around directly while they
  record. This is called **kinesthetic teaching**. It is simple, but your hand is in
  the camera picture, and the robot will not see a hand when it runs on its own.

How many demonstrations are needed? For one narrow task, such as picking up one mug
from different places on a table, people usually record from a few dozen to a few
hundred. The more the task varies, the more demonstrations it needs. The page
[where the data comes from](../01_what-models-are/04_where-the-data-comes-from.md)
explains how people collect data at larger scale.

Training a small behaviour cloning policy on one graphics card usually takes hours,
not days. The recording usually takes longer than the training.

It helps a great deal if the demonstrations are consistent. If the demonstrator
sometimes pauses, sometimes hesitates, and sometimes goes a different way, the
network gets mixed answers for the same question. A study called robomimic, listed
below, found that data from one skilled demonstrator trained better policies than
data from a mix of more and less skilled demonstrators.

---

## 5. Well-known models of this kind

Behaviour cloning is an old idea. These are some well-known examples, from oldest to
newest.

- **ALVINN** (Autonomous Land Vehicle In a Neural Network) was built at Carnegie
  Mellon University at the end of the 1980s. It watched a person drive a van, and
  learned to choose the steering direction from a camera picture of the road. It is
  one of the first examples of behaviour cloning with a neural network.
- **DAgger** (Dataset Aggregation), from 2011, is not a network but a way of
  collecting data. The trained policy drives, and a person says what they would have
  done in the places the policy reaches. Section 7 shows why this helps.
- **robomimic**, from 2021, is a careful study of behaviour cloning on robot arms.
  It compared many versions on the same tasks and data, and showed which details
  matter most, such as the quality of the demonstrations and whether the network
  sees past moments.
- **BC-Z**, from Google in 2021, trained one behaviour cloning policy on about a
  hundred tasks. It was told which task to do with a sentence or a video of a person
  doing it.
- **RT-1** (Robotics Transformer 1), from Google in 2022, trained one policy on
  about 130,000 demonstrations of more than 700 tasks, collected with a fleet of
  robots. It showed that behaviour cloning can cover many tasks if the data is large
  enough.
- **Implicit Behavioural Cloning** (2021) and **Behavior Transformers** (2022) are
  two ways to fix the averaging problem described in section 7. The first scores
  many possible actions and picks the best. The second sorts the actions into groups
  and picks a group first.

The newer policies on the next two pages are also behaviour cloning. They copy
demonstrations too. They differ in what they output, and those differences fix the
problems below.

---

## 6. A worked example: picking up a mug

Say you want an arm to pick up a mug from a table and put it on a shelf. The mug can
be anywhere in a square about 30 cm wide. There is one camera above the table and one
camera on the arm's wrist.

First you record demonstrations. You use a leader arm to drive the robot. Each time,
you put the mug in a new place in the square, and turn it a little. You record 100
demonstrations. Each one takes about 10 seconds. At 30 moments a second, that is
about 300 moments per demonstration, and 30,000 question-and-answer pairs in total.

Next you train. The network sees each pair many times. It learns that when the mug is
on the left in the top camera picture, the arm moves left. It learns that when the
mug fills the wrist camera picture, the gripper closes.

Then you run it. You put the mug down and start the policy. It takes a picture,
chooses a small move, and repeats. If the mug is in a place close to where you put
it during recording, the arm will very likely pick it up.

Now you test the edges. You put the mug outside the square, or put a second mug next
to it, or turn on a different light. Each of these makes the pictures look unlike
anything in the recordings. The policy still gives an action, because it always
does. But the action may be wrong. The next section explains why this happens and
what people do about it.

---

## 7. What goes wrong

Behaviour cloning has two main problems. Both come from the fact that the network
learns single moments, not the task as a whole.

### Small mistakes add up

Every guess the network makes is a little bit wrong. That is normal. But a small
mistake moves the arm to a place that is slightly different from anywhere the
demonstrator went. In that new place, the pictures look slightly unfamiliar. So the
next guess is a little worse. That puts the arm somewhere even less familiar, and the
guess after that is worse again.

This is called **compounding error**. "Compounding" means that each error builds on
the one before.

![The copied path drifts out of the band where the demonstrations went, and misses the mug](../../images/movement-models/behaviour-cloning/compounding-error.svg)

The green band shows where the demonstrations went. Once the red copy leaves the
band, the network is guessing about places it has never seen, and the drift gets
faster.

There are three common fixes.

The first fix is to record demonstrations that include small mistakes and their
corrections. Then the network has seen what to do when the arm is slightly off.

The second fix is DAgger. You let the trained policy drive. When it drifts, a person
says what they would do from that exact spot. Those answers are added to the data,
and the policy is trained again. The new data covers exactly the places the policy
actually reaches.

![The copy drifts, and a person adds the right move at each place it reaches](../../images/movement-models/behaviour-cloning/dagger-corrections.svg)

The green arrows are the person's corrections. They cover the yellow area, which the
original demonstrations never reached.

The third fix is to make fewer decisions. If the network chooses a whole burst of
moves at once, it makes far fewer guesses during the task, so there are fewer chances
for mistakes to add up. This is the idea behind
[action chunking transformers](03_action-chunking-transformers.md).

### Two good ways become one bad way

The second problem comes from people doing the same thing in different ways.

Say there is a box on the table between the arm and the mug. Sometimes the
demonstrator goes round the left of the box. Sometimes they go round the right. Both
are fine.

The network is trained to make its guess as close as possible to the recorded answer.
When the same situation has two different answers, the guess that is closest to both
on average is the one in the middle. In this case, the middle is straight through the
box.

![Half the demonstrations go round the top of the box, half round the bottom, and the average goes through it](../../images/movement-models/behaviour-cloning/averaging-left-and-right.svg)

The green and blue paths are both good. The red path is their average, and it hits
the box.

People say the data has more than one **mode**, meaning more than one typical
answer. A plain behaviour cloning network can only give one answer, so it blends the
modes. The fix is a model that can give one of several answers and pick one of them
cleanly. [Diffusion and flow policies](04_diffusion-and-flow-policies.md) are the
most common way to do this today.

### Other problems

These problems are shared with the other policies in this chapter.

- **The camera must stay where it was.** If the camera moves a few centimetres, the
  pictures look different, and the policy may fail. Keep the cameras fixed, or
  record with the camera in several positions.
- **It cannot say "I don't know".** A policy always gives an action, even in a
  situation it has never seen. Something outside the policy has to watch for
  trouble and stop the arm.
- **It knows nothing about collisions.** The policy has no list of obstacles. It
  only avoids the table because the demonstrations did. A separate safety layer
  has to keep the arm out of places it must not go.
- **It learns one task.** A policy trained to pick up a mug knows nothing about
  opening a drawer. Tasks that chain many steps need something above the policy to
  choose the next step.

---

## 8. Why behaviour cloning, and what it costs

It helps to look at behaviour cloning through four questions: what it is, what it
does for you, why you would pick it over the obvious alternative, and what it costs.

Behaviour cloning is a neural network trained to copy the move a person made in each
recorded situation.

It lets you teach the arm a task by doing it, instead of
by writing it down. You do not need to measure the mug's position, write rules about
where to grasp, or plan a path. You also do not need a simulator or a scoring rule.

The obvious alternative is to program the motion by hand. You would find the mug with a seeing model, work out a
grasp, and send the arm there with a motion planner. That is the better choice when
the objects are rigid, their shape is known, and the task is always the same. It is
easier to check and it does the same thing every time. Behaviour cloning is the
better choice when the task is easier to show than to describe. Folding a towel,
wiping a spill, and opening a stiff drawer are examples. There is no simple rule for
these, but a person can do them easily.

The other alternative is reinforcement learning, where the arm learns by trying.
That needs a scoring rule and millions of tries, usually in a simulator. Behaviour
cloning needs neither. If you can do the task yourself, copying is much cheaper.

The cost is in the data and in what you cannot check. You have to record demonstrations, and record them
carefully. The policy only works in situations like the ones you recorded. When it
fails, it cannot tell you why, and the usual answer is to record more data. It cannot
promise to avoid collisions. And plain behaviour cloning has the two problems in
section 7, which is why most real systems use one of the improved versions on the
next pages.

---

## 9. Where to read next

The next page, [action chunking transformers](03_action-chunking-transformers.md),
shows how choosing a burst of moves at once reduces the adding-up of small
mistakes. The page after it,
[diffusion and flow policies](04_diffusion-and-flow-policies.md), shows how to keep
two good ways of doing a task apart.

To compare copying with learning by trial, read
[reinforcement learning policies](05_reinforcement-learning-policies.md). To go back
to the list of all five kinds, read [the chapter overview](01_overview.md).

For more on where demonstrations come from, read
[where the data comes from](../01_what-models-are/04_where-the-data-comes-from.md),
and for the rigs people use to record them, Book 3's
[data and demonstration page](../../03_frameworks/08_frontier/03_data-and-demonstration.md).
For a more critical account of behaviour cloning, with published numbers, read
[section 1 of learned methods for one arm](../../03_frameworks/04_one-arm-training/03_learned-methods.md#11-behaviour-cloning).
Its section on
[interactive imitation](../../03_frameworks/04_one-arm-training/03_learned-methods.md#12-interactive-imitation-correcting-it-as-it-goes)
explains DAgger and its modern versions.
