# Grasp models

This chapter is about models that decide where and how to hold an object. A robot
arm can see a mug on a table, and it can move its gripper to any point it can
reach. Neither of those tells it where to put the fingers. A grasp model answers
that question.

This page is the overview of the chapter. It answers four questions. What is a
grasp model for? What does its answer look like? What kinds are there, and how do
they differ? And how do grasp models connect to the other kinds of model in this
book?

It is for a reader who has read
[what a model is](../01_what-models-are/01_what-a-model-is.md) and
[how a model learns](../01_what-models-are/02_how-a-model-learns.md). It helps to
have read the [seeing models overview](../03_seeing-models/01_overview.md) too,
because a grasp model usually starts from the same pictures. Every new word is
explained where it first appears.

## Contents

1. [What a grasp model is for](#1-what-a-grasp-model-is-for)
2. [What a grasp is](#2-what-a-grasp-is)
3. [The label every grasp model learns from](#3-the-label-every-grasp-model-learns-from)
4. [The four kinds of grasp model](#4-the-four-kinds-of-grasp-model)
5. [The four kinds side by side](#5-the-four-kinds-side-by-side)
6. [What a grasp model does not know](#6-what-a-grasp-model-does-not-know)
7. [How grasp models connect to the other kinds](#7-how-grasp-models-connect-to-the-other-kinds)
8. [Where to read next](#8-where-to-read-next)

---

## 1. What a grasp model is for

Grasp models decide where and how to hold an object.

Think about picking up a mug. You do not think hard about it, but you make several
choices. You choose which part to hold: the handle, the body or the rim. You choose
which way your hand comes in: from above or from the side. You choose how wide to
open your fingers before they close. A grasp model makes the same choices for a
robot gripper.

The question it answers is this:

> Where should the gripper go, which way should it face, and how wide should it
> open, so that the object stays in the gripper when the arm lifts it?

A robot arm needs this answer before it can pick anything up. For a small number
of known objects, a person can write the answer down by hand. The
[choosing a grip](../../03_frameworks/02_gripping/03_choosing-a-grip.md) document
in Book 3 shows how. A grasp model is for the case where nobody can write it down,
because the objects are new, mixed and lying in any position. A box of mixed
shopping is the usual example.

---

## 2. What a grasp is

A **grasp** is one complete instruction for the gripper. It has three parts.

- A **position**: the point in space where the middle of the gripper's fingertips
  should end up.
- A **direction**: which way the gripper faces as it comes in, and which way its
  fingers close.
- An **opening width**: how far apart the fingers should be just before they close.

A **gripper** here means the two-finger kind, called a **parallel-jaw gripper**,
because its two fingers stay parallel as they close. Each finger is called a
**jaw**. Some pages also cover a **suction cup**, which holds an object by sucking
air out from under a soft rubber cup.

Different grasp models give this answer in different forms. Some give a rectangle
drawn on a picture. Some give a full position and direction in 3D. Some give a
spot where a suction cup should go. Some do not give a grasp at all. Instead they
take a grasp that something else proposed and give it a score. The picture below
shows these four kinds of answer on simple objects.

![Four kinds of answer a grasp model gives](../../images/grasp-models/overview/four-answers.svg)

From left to right: a rectangle on a picture seen from above, a full pose that
comes in from the side, a spot on a box where a suction cup will seal, and one
grip with a score of 0.91 next to it.

---

## 3. The label every grasp model learns from

A model learns from examples, and each example needs a **label**: the right answer
that the model should learn to give. The
[how a model learns](../01_what-models-are/02_how-a-model-learns.md) page explains
this in full.

For grasp models, the label is almost always the same simple thing. A grasp was
tried, and then somebody checked whether the object was still in the gripper after
the arm lifted it. If it was, the label is 1. If it fell out, the label is 0.

![Three grasp attempts and their labels](../../images/grasp-models/overview/did-it-hold.svg)

Each attempt ends with one number: 1 if the object stayed in the gripper, and 0 if
it fell out.

The attempts can happen in two places. A real arm can try thousands of grasps on
real objects. Or a computer can test grasps on 3D models of objects, using the rules
of physics, with no robot at all. The second way is much faster, and most grasp
models today learn from it. The
[grasp quality models](03_also-used/02_grasp-quality-models.md#4-how-it-is-trained) page shows
both ways side by side.

---

## 4. The four kinds of grasp model

There are four kinds of grasp model. Each has its own page.

1. [Top-down grasp detection](03_also-used/01_top-down-grasp-detection.md). The model looks at
   one picture taken from above and draws rectangles on it. Each rectangle says
   where the two jaws should close. The gripper always comes straight down.
2. [Six-degree-of-freedom grasps](02_most-used/01_six-dof-grasps.md). The model looks at a 3D
   picture of the scene and gives full grasps that can come from any direction.
   "Six degrees of freedom" means six numbers: three for the position and three
   for the direction.
3. [Suction and affordance](02_most-used/02_suction-and-affordance.md). The model paints a
   score on every part of the picture. For suction, the score says where a cup
   will seal. For affordance, it says what each part of an object is for, such as
   "hold here" or "this part cuts".
4. [Grasp quality models](03_also-used/02_grasp-quality-models.md). The model is given one
   possible grasp and says how likely it is to work. Something else proposes the
   grasps. The quality model picks the best.

---

### Most used, and also used

The pages of this chapter are in two groups. The first group, most used, holds
[6-DoF grasps](02_most-used/01_six-dof-grasps.md) and
[suction and affordance](02_most-used/02_suction-and-affordance.md). Grasp
models that work in any direction are what most new arm projects reach for,
and suction is the most common gripper in warehouse picking. The second group,
also used, holds [top-down grasp detection](03_also-used/01_top-down-grasp-detection.md)
and [grasp quality models](03_also-used/02_grasp-quality-models.md). Top-down
detection still works well for flat bins seen from above. Quality models are
most often met inside a larger system, scoring the grasps another method
proposes.

## 5. The four kinds side by side

The table below compares the four kinds. Each row is one kind. Read across a row
to see what that kind takes in, what it gives back, and what it is good and bad
at.

| Kind | What goes in | What comes out | Good at | Bad at |
| --- | --- | --- | --- | --- |
| [Top-down grasp detection](03_also-used/01_top-down-grasp-detection.md) | one depth picture from above | rectangles: where to close, at what angle, how wide | small and fast; runs without a graphics card | only straight-down grasps |
| [Six-degree-of-freedom grasps](02_most-used/01_six-dof-grasps.md) | a point cloud of the scene | many full grasps, each with a score | cluttered bins; grasps from any side | needs a strong graphics card; strict licences |
| [Suction and affordance](02_most-used/02_suction-and-affordance.md) | a colour or depth picture | a score for every pixel | flat-faced objects; knowing which part to hold | objects with no flat face; parts it has not seen labelled |
| [Grasp quality models](03_also-used/02_grasp-quality-models.md) | a picture plus one proposed grasp | one number: the chance it holds | choosing the best of many grasps | slow when there are many grasps to check |

A **depth picture** is a picture where each pixel holds a distance from the camera
instead of a colour. A **point cloud** is a list of 3D points on the surfaces the
camera saw. The [camera basics](../../02_perception/01_camera/01_basics.md) page
in Book 2 explains both.

The four kinds are often joined together. A six-degree-of-freedom model proposes
grasps, and a quality model scores them. A suction model and a finger-grasp model
can run side by side, and the robot uses whichever gives the better score.

---

## 6. What a grasp model does not know

A grasp model learned one thing: whether the object stayed in the gripper. So it
knows nothing else. Three examples show what that leaves out.

- It does not know which part must not be touched. It may pick the blade of a
  knife, because the blade is easy to hold.
- It does not know what happens next. It may hold a mug by the rim, which is fine
  for lifting but makes it impossible to pour.
- It does not know your arm. It may choose a grasp that your arm cannot reach, or
  one that is wider than your gripper can open.

The usual answer is to treat the model's grasps as suggestions. Other checks throw
away the ones that are unreachable, that would hit something, or that break a rule
about the task. The
[six-degree-of-freedom page](02_most-used/01_six-dof-grasps.md#7-what-goes-wrong) shows this
in a picture. Book 3's
[models that grasp](../../03_frameworks/02_gripping/04_models-that-grasp.md#9-using-a-model-as-a-candidate-generator)
gives the checks in order.

---

## 7. How grasp models connect to the other kinds

A grasp model is one step in a longer chain. Here is the chain for picking up a
mug.

1. A [seeing model](../03_seeing-models/01_overview.md) finds the mug in the
   camera picture, often as an outline around its pixels.
2. A [3D model](../04_3d-models/01_overview.md) turns the depth picture into a
   point cloud, and may guess the back of the mug that the camera cannot see.
3. A grasp model chooses where the gripper should go on the mug.
4. A [movement model](../06_movement-models/01_overview.md), or an ordinary motion
   planner, moves the arm to that grasp without hitting anything.
5. A [touch and body model](../09_touch-and-body-models/01_overview.md) checks
   that the mug is really held and is not slipping.

A [language model](../07_language-models/01_overview.md) can sit in front of this
chain and turn "pick up the red mug" into the choice of which mug. Some newer
models join steps 3 and 4 into one. A vision-language-action model, for example,
goes from a picture and a sentence straight to arm movements, and never gives a
separate grasp. Those models are covered in the
[vision-language-action models](../07_language-models/02_most-used/01_vision-language-action-models.md)
page.

A separate grasp model is still the common choice in real work. It gives an answer
that a person can look at, check and filter before the arm moves.

---

## 8. Where to read next

- Start with [top-down grasp detection](03_also-used/01_top-down-grasp-detection.md). It is the
  simplest kind and the easiest to picture.
- For the full list of real grasp models, their licences, and which ones run
  without an NVIDIA graphics card, read Book 3's
  [models that grasp](../../03_frameworks/02_gripping/04_models-that-grasp.md).
- For grasps you can compute by hand, without any model, read
  [choosing a grip](../../03_frameworks/02_gripping/03_choosing-a-grip.md).
- For what happens after the fingers close, read
  [holding on](../../03_frameworks/02_gripping/05_holding-on.md).
- To see where grasp models sit among all the kinds in this book, go back to
  [the map of models](../01_what-models-are/06_the-map-of-models.md).
