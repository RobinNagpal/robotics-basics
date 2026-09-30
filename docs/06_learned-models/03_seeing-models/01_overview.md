# Seeing models: an overview

This page opens the chapter on seeing models. Seeing models turn a picture into
names, boxes, outlines, poses or depth. They are the first of the seven kinds of
model in this book, and a robot arm with a camera almost always uses at least one.

The page answers four questions. What are seeing models for? What question do
they answer for a robot arm? What kinds are there, and how do they differ? And
how do they connect to the other kinds of model in this book?

It is for a reader who has read the first chapter,
[what models are](../01_what-models-are/01_what-a-model-is.md). You should know
that a model is a function learned from examples, and that a picture is a grid of
numbers to a computer. You do not need to know how any seeing model works inside.
Each of the next seven pages explains one kind.

## Contents

1. [What seeing models are for](#1-what-seeing-models-are-for)
2. [The question they answer for a robot arm](#2-the-question-they-answer-for-a-robot-arm)
3. [The seven kinds](#3-the-seven-kinds)
4. [How the seven kinds compare](#4-how-the-seven-kinds-compare)
5. [What they have in common](#5-what-they-have-in-common)
6. [How seeing models connect to the other kinds](#6-how-seeing-models-connect-to-the-other-kinds)
7. [Which page to read first](#7-which-page-to-read-first)
8. [Where to read next](#8-where-to-read-next)

---

## 1. What seeing models are for

A camera gives the robot a picture. A picture is a grid of small coloured dots,
called **pixels**. A normal camera picture has hundreds of thousands of pixels.
Each pixel is stored as three numbers: how much red, how much green and how much
blue it has.

The robot cannot use those numbers directly. It does not need to know that pixel
number 51,200 is dark blue. It needs to know that there is a mug on the table,
where the mug is, and which way its handle points.

A **seeing model** is a model that takes a picture in and gives back something
the robot can use. People also call these **computer vision models**. "Computer
vision" is the name of the field that teaches computers to make sense of
pictures.

Almost every seeing model in use today is a **neural network**. A neural network
is a model built from many layers of simple sums, as the page
[inside a neural network](../01_what-models-are/03_inside-a-neural-network.md)
explains. The network learns its sums from many example pictures. Each example
picture comes with the correct answer, written by a person.

Before neural networks, people wrote the steps by hand. For example, a program
could find every orange pixel and call that area "the orange ball". Book 2 shows
this method in
[finding an object in a picture](../../02_perception/01_camera/02_finding-objects.md).
Hand-written steps still work well for simple cases. They stop working when the
object has many colours, when the light changes, or when there are many kinds of
object. A seeing model handles those cases, because it has seen thousands of
examples of each.

---

## 2. The question they answer for a robot arm

Every seeing model answers some form of one question: **what is in front of the
camera, and where is it?**

The different kinds answer it at different levels of detail. The simplest answer
is just a name. A more useful answer adds a box around each object. A more
detailed answer gives the exact outline.

The picture below shows the same mug, answered at three levels of detail.

![A name, a box and an outline of the same mug](../../images/seeing-models/overview/name-box-outline.svg)

With only a name, the arm knows that a mug is there, but not where to reach. With
a box, it knows roughly where to reach. With an outline, it knows exactly which
pixels are mug, so it can find the handle or the middle of the side.

More detail usually costs more. A model that gives outlines is often slower than
one that gives boxes. Its training pictures also take longer for a person to
label, because somebody has to trace every outline by hand.

---

## 3. The seven kinds

This chapter splits seeing models into seven kinds. The picture below shows the
answer each kind gives for the same photo of two mugs and a bottle on a table.

![One photo and the seven kinds of answer](../../images/seeing-models/overview/seven-answers.svg)

Each panel is one kind of model. The top-left panel is the photo that goes in.
The other seven panels show what comes out.

Here is each kind in one line, with a link to its page.

1. [Image classification](03_also-used/01_image-classification.md) gives one name for the
   whole picture, such as "mug".
2. [Object detection](02_most-used/01_object-detection.md) draws a box around each object and
   names it.
3. [Segmentation](02_most-used/02_segmentation.md) marks the exact pixels that belong to each
   object or each kind of thing.
4. [Keypoints and object pose](02_most-used/04_keypoints-and-object-pose.md) finds named points
   on an object, and works out which way the object faces.
5. [Depth from pictures](03_also-used/02_depth-from-pictures.md) works out how far away each
   pixel is.
6. [Open-vocabulary models](02_most-used/03_open-vocabulary-models.md) find objects that you
   describe in words, or that you point at with a click.
7. [Tracking and motion](03_also-used/03_tracking-and-motion.md) follows objects and points
   from one picture to the next.

The first three kinds build on each other. A detector contains most of a
classifier. A segmentation model often contains a detector.

The chapter puts the seven pages into two groups. The **most used** group holds the
four kinds that almost every robot arm with a camera relies on: object detection,
segmentation, open-vocabulary models, and keypoints and object pose. Together they
answer "which object, exactly where, and which way is it turned", which is what a
pick needs. The pose page also covers following a pose through a video, called
[6D pose tracking](02_most-used/04_keypoints-and-object-pose.md#7-following-a-pose-over-time-6d-pose-tracking).
The **also used** group holds the three kinds that are common but needed less often:
image classification, depth from pictures, and tracking and motion. A classifier
gives too little detail for most picks. Depth from pictures is mainly for when a
depth camera fails. Tracking matters only when things move.

The list below shows the two groups. It is in the chapter's reading order.

- Most used:
  [object detection](02_most-used/01_object-detection.md),
  [segmentation](02_most-used/02_segmentation.md),
  [open-vocabulary models](02_most-used/03_open-vocabulary-models.md),
  [keypoints and object pose](02_most-used/04_keypoints-and-object-pose.md).
- Also used:
  [image classification](03_also-used/01_image-classification.md),
  [depth from pictures](03_also-used/02_depth-from-pictures.md),
  [tracking and motion](03_also-used/03_tracking-and-motion.md).

---

## 4. How the seven kinds compare

The table below compares the seven kinds. Each row is one kind. Read across a row
to see its group, what goes in, what comes out, and a typical use on a robot arm.
The last column is a well-known example of that kind, which its own page explains.

| Kind | Group | What goes in | What comes out | A typical use on an arm | A well-known example |
| --- | --- | --- | --- | --- | --- |
| [Object detection](02_most-used/01_object-detection.md) | most used | one picture | a box, a name and a score for each object | find each cup on a table | YOLO |
| [Segmentation](02_most-used/02_segmentation.md) | most used | one picture | the exact pixels of each object | find the rim or the handle of a mug | Mask R-CNN |
| [Open-vocabulary models](02_most-used/03_open-vocabulary-models.md) | most used | one picture and some words, or a click | boxes or outlines of whatever the words describe | "pick up the red mug" | Grounding DINO, SAM |
| [Keypoints and object pose](02_most-used/04_keypoints-and-object-pose.md) | most used | one picture, sometimes with depth; or a video, for pose tracking | named points, and the object's position and turn in 3D, once or on every frame | line up a peg with a hole | FoundationPose |
| [Image classification](03_also-used/01_image-classification.md) | also used | one picture | one name, with a score | check whether the gripper is holding something | ResNet |
| [Depth from pictures](03_also-used/02_depth-from-pictures.md) | also used | one picture, or two side by side | a distance for every pixel | find the distance to a shiny object that a depth camera misses | Depth Anything |
| [Tracking and motion](03_also-used/03_tracking-and-motion.md) | also used | a video, one picture after another | where each object or point moved | follow a part on a moving conveyor | CoTracker |

Two columns in the table matter most when you choose. The "what comes out" column
tells you whether the answer is detailed enough for your job. The "what goes in"
column tells you what camera you need. A depth model can work from an ordinary
camera, while a pose model often wants a depth camera as well.

---

## 5. What they have in common

All seven kinds share three things.

First, they all start the same way. The first layers of the network turn the
pixels into a smaller grid of numbers that describe edges, corners and shapes.
This part of the network is called the **backbone**. Different kinds of seeing
model often use the same backbone, and only change the last layers. The last
layers are called the **head**. A classification head gives a name. A detection
head gives boxes. A segmentation head gives outlines.

Second, they all learn from labelled pictures. A **label** is the correct answer
that a person wrote down for one picture. For a classifier the label is a name.
For a detector it is a box and a name for each object. For a segmentation model
it is an outline for each object. The page
[where the data comes from](../01_what-models-are/05_where-the-data-comes-from.md)
explains how people collect these.

Third, they only know what they were trained on. A model trained on kitchen photos
may miss a metal part in a factory. It does not say "I do not know". It usually
gives a wrong answer, or no answer. The usual fix is to collect a few hundred
pictures of your own objects and train the model a little more on them. This is
called **fine-tuning**. The chapter-one page
[fine-tuning](../10_making-models-work-on-an-arm/02_most-used/01_fine-tuning.md) explains the ways to do it and
what each costs. Each of the next pages says how it is done for that kind.

---

## 6. How seeing models connect to the other kinds

Seeing models usually come first in a robot's program. They turn the camera
picture into facts about objects. The other kinds of model use those facts.

- [3D models](../04_3d-models/01_overview.md) work on 3D points and whole scenes
  instead of flat pictures. A seeing model often picks out the pixels of one
  object first. The 3D model then works only on that object's points.
- [Grasp models](../05_grasp-models/01_overview.md) decide where and how to hold
  an object. Many of them take a mask from a segmentation model, so that they only
  look for grasps on the object the robot should pick.
- [Movement models](../06_movement-models/01_overview.md) decide how the arm
  should move, moment by moment. Many of them contain a seeing model's backbone
  inside them, which turns each camera picture into numbers.
- [Language models](../07_language-models/01_overview.md) understand words, and
  connect words to pictures and actions. The open-vocabulary models in this
  chapter sit on the border between seeing and language.
- [World models](../08_world-models/01_overview.md) predict what will happen next
  if the arm does something. Some of them predict future pictures, which is close
  to the tracking and motion models here.
- [Touch and body models](../09_touch-and-body-models/01_overview.md) make sense
  of touch, force and the arm's own body. Some touch sensors produce pictures, and
  the same kinds of network read them.

The page [the map of models](../01_what-models-are/06_the-map-of-models.md) shows
all seven kinds of model together.

---

## 7. Which page to read first

If you are new to seeing models, read the most-used pages in order, starting with
[object detection](02_most-used/01_object-detection.md). If a word such as backbone
or score is new to you there, read
[image classification](03_also-used/01_image-classification.md) first. It is the
simplest seeing model, and it explains the parts that every other seeing model
reuses.

If you already know what you need, the list below points to the right page.

- To find objects on a table and pick them up, read
  [object detection](02_most-used/01_object-detection.md), then
  [segmentation](02_most-used/02_segmentation.md).
- To put a part into a fixture at an exact angle, read
  [keypoints and object pose](02_most-used/04_keypoints-and-object-pose.md).
- To follow a part's full pose while it moves, read
  [6D pose tracking](02_most-used/04_keypoints-and-object-pose.md#7-following-a-pose-over-time-6d-pose-tracking).
- To measure distances with only an ordinary camera, read
  [depth from pictures](03_also-used/02_depth-from-pictures.md).
- To handle objects that no model was trained on, read
  [open-vocabulary models](02_most-used/03_open-vocabulary-models.md).
- To follow objects that move, read
  [tracking and motion](03_also-used/03_tracking-and-motion.md).

---

## 8. Where to read next

The next page is [object detection](02_most-used/01_object-detection.md), the first
of the most-used group. It explains how a network draws a box round each object and
names it. If you want the simplest seeing model first,
[image classification](03_also-used/01_image-classification.md) opens the also-used
group.

For practical detail on the models you can download, their licences and their
speed, Book 2 has two deeper documents:
[models that find objects](../../02_perception/02_object-perception/04_models-that-find.md)
and [models that measure](../../02_perception/02_object-perception/05_models-that-measure.md).
