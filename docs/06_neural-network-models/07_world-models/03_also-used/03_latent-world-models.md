# Latent world models

This page explains world models that predict the future as a short code
instead of as a picture. The best-known family of them is called Dreamer. The
page answers four questions. What is the "short code", and where does it come
from? How can a robot practise a task inside the model's predictions? How is
such a model trained? And why would anyone choose it over the other kinds of
world model?

It is for a reader who has read the [world models overview](../01_overview.md), the
page on [learned dynamics models](../02_most-used/01_learned-dynamics-models.md) and the page on
[video prediction models](01_video-prediction-models.md). You should know what a
state, an action, a rollout and a policy are. This page joins ideas from both of
those pages.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Squeezing a picture into a code](#squeezing-a-picture-into-a-code)
   · [Predicting the next code](#predicting-the-next-code)
   · [Practising inside the model](#practising-inside-the-model)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
6. [A worked example: learning to put a cube in a bowl](#6-a-worked-example-learning-to-put-a-cube-in-a-bowl)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

A latent world model turns each camera picture into a short list of numbers,
called a **code**, and predicts how that code will change when the arm acts.

The word **latent** means "hidden". The code is hidden in the sense that no
person chose what its numbers mean. Nobody decided "number 3 is the cube's
position". The model found, during training, a set of numbers that keeps what
matters about the picture and drops the rest.

Here is an everyday example. Imagine you are planning how to carry a sofa up a
narrow staircase. You do not picture every thread of the sofa's fabric or the
colour of the walls. You think about a few things only: how long the sofa is,
how wide the stairs are, and where the corner is. You try out a few ways in your
head before you lift anything. A latent world model plans in the same kind of
reduced description. It keeps the things that matter for the task and drops
the rest.

This joins the two earlier pages. Like a [learned dynamics model](../02_most-used/01_learned-dynamics-models.md),
it predicts a short list of numbers, which is fast. Like a
[video prediction model](01_video-prediction-models.md), it learns straight from
camera pictures, so nobody has to measure positions by hand.

---

## 2. What goes in and what comes out

A latent world model for a robot arm has one input at the start and then works
only with codes.

- **At the start: a camera picture.** For example, the picture from a camera
  above the table, showing the gripper, a cube and a bowl.
- **At each step: an action.** For example, "move the gripper 2 cm to the right".
- **At each step, it gives back the next code**, and also a **predicted score**:
  a number that says how well the task is going. The score is called the
  **reward**. For example, it could be 1 when the cube is in the bowl and 0
  otherwise.

The model can also turn a code back into a picture, so that a person can check
what it is thinking. But it does not need to do this in order to plan or
practise.

A typical code has a few hundred to a few thousand numbers. That sounds like a
lot. But a camera picture of 64 × 64 pixels, with 3 colours for each pixel, is
already 12,288 numbers. Real camera pictures are much larger than that.

---

## 3. How it works inside

A latent world model has four parts. The first turns a picture into a code. The
second predicts the next code. The third predicts the score. The fourth turns a
code back into a picture, and it is used mainly during training.

### Squeezing a picture into a code

The **encoder** is a network that takes a camera picture and gives back a short
code. The **decoder** is a network that does the opposite: it takes a code and
draws a picture.

During training, the two are joined. The picture goes into the encoder, the
code goes into the decoder, and the picture that comes out is compared with the
one that went in. The training makes the two pictures as close as it can. The
only way to do that is for the code to keep the important things about the
picture: where the gripper is, where the cube is, whether the gripper is open.

![A camera picture goes through an encoder into six numbers, and a decoder draws the picture back from those six numbers](../../../images/world-models/latent-world-models/picture-to-short-code.svg)

Here a picture of 768 numbers is squeezed into 6, and the picture drawn back is
close to the original but slightly blurred.

The drawing uses a tiny picture and a tiny code so that you can see each part.
Real codes are larger, as the last section said, but the idea is the same.

### Predicting the next code

The **dynamics part** is a network that takes the code now and an action, and
gives back the next code. This is exactly the learned dynamics model from the
[previous pages](../02_most-used/01_learned-dynamics-models.md#one-step), working on codes
instead of measured positions.

Most latent world models also keep a **memory**: a second list of numbers that is
carried from step to step. The memory lets the model remember things that the
current picture does not show, such as a cube that the gripper is now hiding.

The **score part** is a small network that looks at a code and predicts the
reward. It lets the model say not only "what will the scene be?" but also "is
that good for the task?".

With these parts, the model can run forward on its own. It starts from the code
of one real picture. It then predicts the next code for each action, again and
again, without drawing a single picture.

![From one real picture, the model predicts codes step by step for three actions, with a predicted score at each step, and draws no pictures in between](../../../images/world-models/latent-world-models/imagining-in-code.svg)

Only the first picture is real, and every later code and score is a prediction;
the numbers are made up to show the idea.

Predicting codes is much faster than drawing pictures, because a code has far
fewer numbers than a picture. A small network can predict many steps in the time
a large video model takes to draw one frame. That speed is what makes the next
idea possible.

### Practising inside the model

The model's predictions are sometimes called **imagination**, or a **dream**. The
names only mean "a rollout that the model made up, not one that happened". The
key idea of the Dreamer family is that a policy can practise inside this
imagination.

It works in three steps.

1. **Start from real moments.** Take codes from real pictures that the robot saw
   earlier.
2. **Imagine.** From each one, let the policy choose actions, and let the world
   model predict the codes and scores that follow, for a short stretch of steps.
3. **Improve the policy.** Change the policy so that it chooses actions that led
   to higher predicted scores.

A second small network helps with step 3. It is called the **critic**. It looks
at a code and guesses the total score still to come from there. This lets the
policy learn from imagined stretches that are too short to reach the end of the
task.

Many of these imagined stretches can run in the time the real arm makes one
move. The real arm is used only to collect new pictures now and then, and to
check that the policy works.

![On the left, three practice attempts on the real arm; on the right, many imagined attempts inside the world model](../../../images/world-models/latent-world-models/real-vs-imagined.svg)

Each real attempt feeds the world model, and the policy then practises many
times inside it.

---

## 4. How it is trained

A latent world model learns from the robot's own recordings. Each recording is
a sequence of camera pictures, the action taken after each one, and the reward
at each step.

Training repeats a cycle of three stages.

1. **Collect.** The robot tries the task on the real arm with its current
   policy, and records everything. At first the policy is random.
2. **Train the world model.** The encoder, decoder, dynamics part and score part
   all learn from the recordings. They learn to squeeze pictures, to draw them
   back, to predict the next code, and to predict the reward.
3. **Train the policy.** The policy and the critic practise inside the world
   model, as described above.

Then the cycle starts again. The better policy collects more useful recordings,
which make the world model better, which makes the practice better.

The reward must come from somewhere. In a simulator, a program can compute it
exactly. On a real arm, it might come from a sensor, from a person pressing a
button, or from another model that looks at the camera and says whether the task
succeeded. The [vision-language models](../../06_language-models/02_most-used/02_vision-language-models.md)
page describes models that can check success from a picture.

How much real data is needed depends on the task, but it is usually far less
than for a policy that learns without a model. That is the whole reason for
this kind of model.

---

## 5. Well-known models of this kind

These are real, published models.

- **World Models** (Ha and Schmidhuber, 2018) gave the field its name. It
  squeezed game pictures into codes, predicted the next code, and trained a very
  small policy entirely inside the model's predictions, for a car racing game.
- **PlaNet** (Hafner and others, 2019) learned a latent world model from pictures
  and planned inside it with the cross-entropy method from the
  [learned dynamics models](../02_most-used/01_learned-dynamics-models.md#planning-with-it) page.
- **Dreamer** (Hafner and others, 2020) replaced planning with a policy and a
  critic that practise inside the model. Its later versions, **DreamerV2** and
  **DreamerV3**, worked on many more tasks. DreamerV3 used the same settings
  across very different tasks, and it learned to collect diamonds in the game
  Minecraft without any human examples.
- **DayDreamer** (Wu and others, 2022) ran Dreamer on real robots, learning on
  the robot with no simulator. A four-legged robot learned to walk within about
  an hour, and robot arms learned to pick up objects and place them from
  camera pictures.
- **TD-MPC2** (Hansen and others, 2024) has no decoder at all. It learns codes
  that are good for predicting the score, not for drawing pictures, and plans
  with them.
- **V-JEPA 2** (Meta, 2025) learns codes from a large amount of internet video
  by predicting the codes of hidden parts of the video, again without drawing
  pictures. A version trained further on robot video with actions was used to
  plan pick-and-place moves for robot arms, given a picture of the goal.

---

## 6. A worked example: learning to put a cube in a bowl

Here is how a Dreamer-style latent world model teaches a real arm to put a cube
in a bowl, from pictures alone.

1. **Set up.** A camera looks down at the table. A small program detects
   whether the cube is inside the bowl. It gives a reward of 1 when it is, and 0
   when it is not.
2. **Collect a little.** The arm makes some random moves for a few minutes. The
   system records the pictures, the moves and the rewards.
3. **Train the world model.** It learns to squeeze each picture into a code and to
   predict the next code after each move.
4. **Practise in imagination.** The policy practises thousands of times inside
   the model, starting from real recorded moments. At first it only learns to
   move the gripper towards the cube, because that is where the imagined scores
   start to rise.
5. **Try for real.** The arm now tries the task with the improved policy. Most
   tries fail, but they fail closer to the cube. Every try is recorded.
6. **Repeat.** Steps 3 to 5 run again and again, often all day, with the real
   arm collecting while the computer trains. The imagined practice gets more
   accurate as the recordings grow, and the policy gets better with it.

At no point did anyone measure the cube's position or write down the physics of
the gripper. Everything the robot knows came from its own camera and its own
tries.

---

## 7. What goes wrong, and what people do about it

**Nobody can read the code.** When the model makes a wrong prediction, you
cannot look at the code to see why. People use the decoder to draw the predicted
codes as pictures. That shows what the model imagines, even though the planning
does not use those pictures.

**The decoder wastes effort.** A model that must draw pictures back spends
effort on the table's colour and on shadows. It can miss a small object that
matters, such as a screw, because a screw is only a few pixels. Models such as
TD-MPC2 and V-JEPA 2 drop the decoder. They must then use other training tricks
to stop the codes from becoming useless, for example the same code for every
picture, which would be trivially easy to predict.

**The policy finds the model's mistakes.** The policy is trained to get high
predicted scores. If the model wrongly predicts a high score for some strange
move, the policy learns that move. The real arm then fails. People keep the
imagined stretches short, and they keep collecting real data so that the
mistakes get corrected.

**The reward is hard to get on a real arm.** In a game, the score is given. On a
real arm, someone has to build a reliable success check. A wrong check teaches
the wrong task.

**It still needs data for each task.** Latent world models need far less real
practice than learning with no model, but usually still hours of it for each
new task. Pretraining on large amounts of video, as V-JEPA 2 does, is the main
way people are trying to reduce this.

---

## 8. Why this kind, and what it costs

There are two obvious alternatives, one on each side.

The first is a [video prediction model](01_video-prediction-models.md). It also
learns from pictures, and its predictions are easy for a person to check,
because they are pictures. But drawing pictures is slow. A latent world model
predicts codes instead, which is fast enough to practise thousands of times per
real move. When the goal is to *practise* inside the model, speed wins.

The second is a [reinforcement learning policy](../../05_movement-models/03_also-used/01_reinforcement-learning-policies.md)
that learns with no world model at all. It is simpler, and it has fewer parts to
go wrong. But it learns only from real tries, and on a real arm it needs far
more of them than the arm can make in a sensible time. A latent world model
reuses each real try for many imagined ones.

What it costs you:

- **More parts.** An encoder, a decoder, a dynamics part, a score part, a policy
  and a critic, all trained together. Each has its own settings, and a problem
  in one shows up in all the others.
- **Hard to check.** You cannot read the codes, so mistakes are hard to find.
- **A reward on the real arm.** You must build a success check you can trust.
- **Still one task at a time.** A model trained on putting a cube in a bowl does
  not know how to open a drawer. Training on large amounts of video and many
  tasks is how the field is trying to change that.

---

## 9. Where to read next

- Go back to the [world models overview](../01_overview.md) for how the four kinds
  compare.
- [Reinforcement learning policies](../../05_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  explain the trial-and-error learning that a latent world model speeds up.
- [Vision-language-action models](../../06_language-models/02_most-used/01_vision-language-action-models.md)
  explain the large robot policies that, in 2026, started to use world models
  as a training signal.
- [Learned arm models](../../08_touch-and-body-models/03_also-used/02_learned-arm-models.md)
  apply the world model idea to the arm's own body.
- For more depth, read Book 3's
  [learned methods for one arm](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#2-learning-from-trial-and-error),
  which places Dreamer and TD-MPC next to the other ways an arm learns from
  trying, and
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies),
  which describes the latent world model VLA-JEPA and what it cannot yet do.
