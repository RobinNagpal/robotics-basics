# Object detection

This page explains object detection: models that find each object in a picture,
draw a box around it and name it. It answers five questions. What does a detector
do? What goes in and what comes out? How does it work inside? How is it trained?
And how does a robot arm use its boxes to pick something up?

It is for a reader who has read the page on
[image classification](../03_also-used/01_image-classification.md). That page explains pixels,
scores, layers, the backbone and fine-tuning. This page uses those words without
explaining them again.

Object detection is the most used seeing model on robot arms. It is often the
first model a robot project tries, because good detectors are free to download and
fast enough for a live camera.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Two stages: first guess the places, then check each one](#two-stages-first-guess-the-places-then-check-each-one)
   · [One stage: look once, answer for every cell](#one-stage-look-once-answer-for-every-cell)
   · [Cleaning up the extra boxes](#cleaning-up-the-extra-boxes)
   · [Transformers: a fixed set of answers](#transformers-a-fixed-set-of-answers)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [Where it is used on a robot arm](#6-where-it-is-used-on-a-robot-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why detection, and what it costs](#8-why-detection-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

An **object detector** is a model that finds every object it knows in a picture.
For each one, it gives a box around the object, the object's class and a score.

The box is called a **bounding box**. It is the smallest upright rectangle that
holds the whole object. The class is a name from a fixed list, as for a
classifier. The score says how sure the model is, from 0 to 1. On a detector the
score is usually called the **confidence**.

Here is an everyday example. Think of a person counting cars in a car park from a
photo. They look over the photo, point at each car, and say "car, car, van, car".
A detector does the same. It points at each object with a box, and gives each box a
name.

The difference from a classifier is this. A classifier gives one name for the
whole picture. A detector gives one answer per object, and says where each object
is. So a detector can tell the robot that there are three cups, and which one is
nearest.

---

## 2. What goes in and what comes out

The input is one camera picture. On a robot arm this is usually a picture of the
table or bin in front of the arm, from a camera on a stand or on the arm's wrist.

The output is a list. Each item in the list describes one object with six numbers
and a name:

- four numbers for the box, in pixels. These are usually the left and top edges and
  the right and bottom edges. Some models give the middle of the box, its width and
  its height instead.
- the class, such as "mug" or "bottle".
- the confidence, such as 0.94.

The picture below shows the answer a detector gives for a photo of two mugs and a
bottle.

![A box, a name and a confidence for each object on the table](../../../images/seeing-models/object-detection/boxes-on-a-table.svg)

Each box has a tag with the class and the confidence. The confidence numbers in this
picture are examples, not real output.

The list can be empty. That means the model found nothing it knows. The list can
also hold objects the model is not sure about. So every program that uses a
detector sets a **confidence threshold**. It throws away every box whose confidence
is lower than that number. A threshold of 0.25 to 0.5 is a common start. Book 2
discusses this choice in
[confidence, and the threshold](../../../02_perception/01_camera/02_finding-objects.md#53-confidence-and-the-threshold).

---

## 3. How it works inside

A detector starts like a classifier. A backbone turns the picture into grids of
numbers that describe edges, parts and objects. Then a detection **head** turns
those grids into boxes. There are three main ways to build the head.

### Two stages: first guess the places, then check each one

The oldest way uses two steps.

1. The first step looks over the backbone's grids and suggests a few hundred places
   that might hold an object. Each suggestion is a rough box. These suggestions are
   called **region proposals**.
2. The second step looks at each proposal on its own. It gives the proposal a class
   and a confidence, as a classifier would. It also moves the edges of the box a
   little, so that the box fits the object better.

This way is accurate, but it is slower, because the second step runs once for each
proposal. The best-known model of this kind is Faster R-CNN, described in
[section 5](#5-well-known-models).

### One stage: look once, answer for every cell

A faster way does everything in one step. The name of the best-known model of this
kind says it: YOLO, short for "you only look once".

1. The picture is split into a grid of cells. A real model uses several grids at
   once, with small cells for small objects and large cells for large ones.
2. For each cell, the head asks: is the middle of an object inside this cell?
3. If yes, that cell gives the object's box, its class and a confidence.

The picture below shows the idea with one coarse grid.

![The cell that holds the middle of an object reports its box](../../../images/seeing-models/object-detection/grid-of-cells.svg)

The white dot marks the middle of each object. The yellow cell around each dot is
the cell that reports that object. Its box can be larger than the cell, because the
backbone's numbers for each cell already carry information about the area around
it.

The whole picture goes through the network once. That is why one-stage detectors
are fast enough to run on every frame of a live camera.

### Cleaning up the extra boxes

A one-stage or two-stage detector usually gives several boxes for the same object.
Nearby cells, or nearby proposals, all see the same mug, and each one reports it.

So the detector runs a cleanup step after the network. The step is called
**non-maximum suppression**, or NMS. It works like this.

1. Sort all the boxes of one class by confidence, highest first.
2. Keep the box with the highest confidence.
3. Remove every other box that overlaps the kept box by more than a set amount.
4. Repeat with the next highest box that is still left.

The overlap is measured as the area the two boxes share, divided by the area they
cover together. This number is called **intersection over union (IoU)**. It is 1 when
the two boxes are the same and 0 when they do not touch. A common setting removes
boxes with an IoU above 0.5 or so.

The picture below shows five boxes for one mug, and the one box that is left after
the cleanup.

![Five overlapping boxes for one mug become one box after the cleanup step](../../../images/seeing-models/object-detection/many-guesses-one-box.svg)

The cleanup has a weakness. Two real objects that stand very close together have
boxes that overlap a lot. The cleanup may then remove one of them by mistake.

### Transformers: a fixed set of answers

A newer way uses a transformer, the kind of network that the
[classification page](../03_also-used/01_image-classification.md#3-how-it-works-inside) mentioned. The
first model of this kind was DETR, short for "detection transformer".

1. The model starts with a fixed number of empty answer slots, for example 100.
   These slots are called **queries**.
2. Each query looks at all of the backbone's grids through the attention step. It
   gathers what it needs to describe one object.
3. Each query then gives one box and one class. A query can also give the class "no
   object".

During training, each real object is matched to exactly one query. So the model
learns to give one box per object, and it needs no cleanup step. This makes the
program after the network simpler, and it avoids the weakness with close objects.

---

## 4. How it is trained

A detector learns from pictures where a person has drawn a box around every object
and written its class. This work is called **labelling**, or **annotation**. Drawing
boxes is quick compared with tracing outlines, but it is slower than writing one
name per picture.

The most used collection is **COCO**, short for "Common Objects in Context". It has
about 120,000 labelled photos for training, with 80 classes. The classes include
"cup", "bottle", "bowl", "scissors" and "person". Most detectors you can download
were trained on COCO.

Training works like classifier training. The network makes its guesses for a batch
of pictures. A program compares each guess with the drawn boxes and measures three
kinds of error: the box is in the wrong place, the class is wrong, or an object was
missed. It then nudges the network's numbers to reduce those errors, and repeats.

A robot project almost always fine-tunes. It starts from a detector trained on
COCO, and trains it further on its own pictures with its own classes. A few hundred
labelled pictures is a common starting point. Book 2 walks through a complete
example with 80 pictures in
[training a model of your own](../../../02_perception/01_camera/02_finding-objects.md#6-training-a-model-of-your-own).

Some projects make their training pictures in a simulator instead. The simulator
draws the objects and knows exactly where every box is, so nobody has to label by
hand. The page
[where the data comes from](../../01_what-models-are/05_where-the-data-comes-from.md)
explains this.

---

## 5. Well-known models

These are real detectors. The first three are the ones this page described.

- **Faster R-CNN** is the best-known two-stage detector, from 2015. The name comes
  from "region-based convolutional neural network". It is accurate and well
  understood, and it is part of the PyTorch library, so it is easy to try.
- **YOLO** is a family of one-stage detectors. The first version came out in 2015.
  Many groups have made newer versions since, and the Ultralytics versions are
  the easiest to use. They are fast enough for a live camera on an ordinary
  computer.
- **SSD**, short for "single shot detector", is another early one-stage detector.
  It found objects of different sizes by using grids of several sizes.
- **RetinaNet** is a one-stage detector that changed how training counts errors.
  It pays less attention to the many easy empty cells, and more to the hard cases.
  This made one-stage detectors as accurate as two-stage ones.
- **DETR** is the first detection transformer, from Facebook AI Research in 2020.
  It needs no cleanup step, but it was slow to train.
- **RT-DETR**, short for "real-time DETR", is a later detection transformer built
  to be fast. It keeps DETR's advantage of needing no cleanup step.

Book 2's [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md#11-box-detectors)
lists these and newer ones, with their licences. The licence matters: some popular
detectors carry a licence that affects how you can share your own code.

---

## 6. Where it is used on a robot arm

Here is a worked example: picking a cup from a table.

1. A camera above the table takes a picture. The camera is a depth camera, so every
   pixel also has a distance.
2. The detector finds three boxes: two with the class "cup", and one with the class
   "bottle".
3. The program throws away boxes below its threshold and keeps only the class
   "cup". It picks the cup with the highest confidence.
4. It takes the middle pixel of that box.
5. It reads the distance at that pixel from the depth picture. With the camera's
   known lens settings, it turns the pixel and the distance into a point in 3D, in
   metres. Book 2 explains this step in
   [adding depth: from a pixel to metres](../../../02_perception/01_camera/02_finding-objects.md#4-adding-depth-from-a-pixel-to-metres).
6. It turns that point from the camera's frame into the arm's frame, using the
   camera's known position.
7. The arm moves its gripper above the point, lowers it, and closes it.

This works well for round cups standing apart, because the middle of the box is the
middle of the cup. It works less well for a mug with its handle to one side. The
middle of the box is then a little off the middle of the mug. The
[segmentation](02_segmentation.md) page shows how an outline fixes this.

Other common uses on an arm:

- Counting objects, or checking that every part is in its tray.
- Telling the robot which object to pick first, for example the nearest.
- Giving a rough box to another model. A segmentation model can turn the box into
  an outline, and a grasp model can look for grasps only inside the box.
- Following objects on a moving belt, by detecting them in each picture. The page
  [tracking and motion](../03_also-used/03_tracking-and-motion.md) covers this.

---

## 7. What goes wrong

A detector fails in a few common ways. Each one has a usual fix.

It misses objects it was not trained on. A COCO detector knows "cup" but not "brake
disc". It is not only worse on unknown objects. It usually finds nothing at all.
Book 2 shows this in
[a model only knows what it was trained on](../../../02_perception/01_camera/02_finding-objects.md#54-a-model-only-knows-what-it-was-trained-on).
The fix is fine-tuning on your own objects, or an
[open-vocabulary model](03_open-vocabulary-models.md) that finds objects from a
word.

It misses objects that are partly hidden, or that touch each other. When cups stand
in a tight group, the cleanup step may merge two cups into one box. The fix is to
include such scenes in the training pictures, or to use a detector without the
cleanup step.

It misses small objects. A screw that covers 10 by 10 pixels gives the network very
little to work with. The fix is to move the camera closer, or to use a higher
resolution picture.

It struggles with see-through and shiny objects. A glass or a polished metal part
looks different from every angle. The fix is more training pictures of such objects,
from many angles and in varied light.

Its boxes do not fit tilted or long objects. A pen lying at an angle gets a large
box that is mostly table. The box says little about which way the pen points. Some
detectors can give turned boxes instead. Others use [segmentation](02_segmentation.md)
or [keypoints](04_keypoints-and-object-pose.md).

---

## 8. Why detection, and what it costs

This section answers the four questions for a detector: what it is, what it does
for you, why it rather than the obvious alternative, and what it costs.

It is a network that gives a box, a name and a confidence for every object it
knows. It tells the robot what is on the table, how many of each, and roughly
where.

The first obvious alternative is a hand-written colour rule. Book 2 shows one in
[finding it by colour](../../../02_perception/01_camera/02_finding-objects.md#3-finding-it-by-colour).
A colour rule needs no training and runs very fast. But it only works when each
object has one known colour that nothing else shares. A detector can tell a white
mug from a white bowl, which a colour rule cannot.

The second obvious alternative is [segmentation](02_segmentation.md), which gives the
exact outline instead of a box. An outline tells the robot more. But labelling
outlines takes much longer than drawing boxes, and segmentation models are usually
slower. Choose a detector when a box is enough to pick the object, for example
round or boxy objects that stand apart. Choose segmentation when the shape matters.

The costs are these. You need labelled pictures of your own objects, with a box
around every one. You need a computer that can run the network on each camera
picture; a small detector runs on an ordinary processor, while a large one wants a
graphics card. You need to choose a threshold, and accept that some objects will be
missed and some boxes will be wrong. And you need a check on the licence of the
model and its trained weights before you ship your robot.

---

## 9. The written alternative

Book 5 finds objects with written rules instead of a trained network. First,
[thresholding and colour masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md) marks the pixels that have a chosen
colour, or the points that stand above the table in a depth picture. Then
[clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md) splits those pixels or points into separate objects, and
gives each one a box and a centre. For one known object with printing on it,
such as a boxed product, [image features and matching](../../../05_programming-techniques/03_searching-and-matching/03_also-used/01_image-features-and-matching.md) finds it by
matching small spots against a stored picture. The written way wins in a cell
you control, for example parts in colours nothing else shares, standing apart on
a plain table: it needs no labelled pictures and gives the same answer every
time. The detector wins when there are many kinds of object, when colours are
shared or the light changes, and when the robot must say what each object is,
which a threshold cannot do.

---

## 10. Where to read next

- The next page is [segmentation](02_segmentation.md). It replaces the box with the
  exact outline of each object.
- [Image classification](../03_also-used/01_image-classification.md) explains the backbone and
  fine-tuning that every detector uses.
- [Open-vocabulary models](03_open-vocabulary-models.md) find objects from a word,
  without training on them first.
- [Tracking and motion](../03_also-used/03_tracking-and-motion.md) follows detected objects from
  one picture to the next.
- [Running a model on a robot](../../09_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains how fast a model must be, and where it runs.
- Book 2 goes deeper in
  [finding an object in a picture](../../../02_perception/01_camera/02_finding-objects.md),
  which runs a real YOLO detector, and in
  [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md).
