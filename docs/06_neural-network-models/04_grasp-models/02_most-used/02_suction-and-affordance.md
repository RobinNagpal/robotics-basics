# Suction and affordance

This page is about grasp models that paint a score onto every part of a picture.
There are two kinds, and they share one design. A **suction model** paints where a
suction cup would seal. An **affordance model** paints what each part of an object
is for, such as "hold here" or "this part cuts".

The page answers these questions. What is a suction grasp, and why is it easier
to predict than a finger grasp? What is an affordance? What do these models take in
and give back? How do they work inside, and how are they trained? Which real models
do this? When are they the right choice?

It is for a reader who has read the [grasp models overview](../01_overview.md) and
[top-down grasp detection](../03_also-used/01_top-down-grasp-detection.md). The per-pixel maps on
that page are the same idea used here. It also helps to have read
[segmentation](../../02_seeing-models/02_most-used/02_segmentation.md), because an affordance model
is a kind of segmentation model.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a tote and a kitchen drawer](#6-a-worked-example-a-tote-and-a-kitchen-drawer)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

Both kinds of model paint a map over the picture that says, for each pixel, how
well a certain action would work there.

### Suction

A **suction gripper** holds an object with a soft rubber cup. A pump sucks the air
out from under the cup. The air outside then pushes the object against the cup and
holds it there. You have seen the same thing when a suction hook sticks to a
bathroom tile.

The cup only holds if its rim touches the surface all the way round. This is called
a **seal**. If any part of the rim hangs in the air, air leaks in and the object
drops.

![A suction cup on a flat top, over an edge, and on a small ball](../../../images/grasp-models/suction-and-affordance/seal-or-leak.svg)

On the flat top of a box, the rim touches all the way round and the cup seals. Over
the edge, or on a small ball, part of the rim does not touch, and air leaks in.

So a suction grasp is a simpler question than a finger grasp. There is only one
contact, not two. The cup always pushes straight into the surface. The question is
just: "if the cup touches here, will it seal, and will it hold the weight?" A
suction model answers that for every pixel.

### Affordance

An **affordance** is what a part of an object lets you do with it. A mug's handle
affords holding. The inside of the mug affords containing liquid. A knife's blade
affords cutting. The word comes from the study of how people and animals see the
world, and robotics borrowed it.

An affordance model paints each pixel of an object with the job that part is for.
A robot can then hold a knife by the handle, or hand a mug to a person with the
handle towards them.

![A mug and a knife, coloured by what each part is for](../../../images/grasp-models/suction-and-affordance/parts-for-jobs.svg)

The mug's handle is for holding, its inside is for containing and its outside is
for wrapping a hand round. The knife's handle is the only safe part to hold. A grasp
model that only asks "will it hold?" might choose the blade.

---

## 2. What goes in and what comes out

For a **suction model**:

- The input is a colour picture, a depth picture, or both, taken from above.
- The output is a **suction map**: one score between 0 and 1 for every pixel. A
  high score means a cup placed there, pressing straight into the surface, is
  likely to seal and hold.
- Code then picks the pixel with the best score. It works out the direction the
  surface faces at that pixel from the depth picture. The cup comes in along that
  direction.

![A picture of a tote and the suction score for every pixel](../../../images/grasp-models/suction-and-affordance/suction-map.svg)

On the left, a tote with a box, a can, a ball and a soft bag. On the right, the
suction score for every pixel. The flat middle of the box and the can's lid score
high. The edges, the ball and the lumpy bag score low. The red star is the best
spot.

For an **affordance model**:

- The input is a colour picture, sometimes with depth.
- The output is a **label map**: for every pixel, the name of the job that part of
  the object is for, such as "grasp", "cut" or "contain". Some models also give a
  box around each object first, and paint the labels inside the box.
- Code then keeps only the grasps that land on a part labelled "grasp". Those
  grasps can come from any grasp model in this chapter.

---

## 3. How it works inside

Both kinds use the same shape of network. It is the same shape used for
[segmentation](../../02_seeing-models/02_most-used/02_segmentation.md).

1. **An encoder shrinks the picture.** A convolutional neural network (CNN) reads
   the picture and turns it into a smaller grid of numbers. Each number in the
   small grid describes a patch of the picture, such as "flat surface" or "curved
   edge".
2. **A decoder grows it back.** A second part of the network turns the small grid
   back into a picture the same size as the input.
3. **Each pixel gets an answer.** For a suction model, each pixel gets one score.
   For an affordance model, each pixel gets one score per job, and the job with
   the highest score wins.

A network whose output is a picture the same size as its input is called a
**fully convolutional network**. The
[encoders and decoders](../../01_what-models-are/03_inside-a-neural-network.md#7-encoders-and-decoders)
section of the inside a neural network page explains the two halves.

Systems that paint a finger-grasp map next to the suction map add a trick for
angles. A finger grasp needs an angle, but a suction cup does not. So they turn the
input picture by several angles, run the network on each turned copy, and keep the
best answer. This lets a network that only learned one jaw direction find grasps at
any angle.

Suction models often split the score in two. A **seal score** says whether the cup
will seal on the surface. A **wrench score** says whether the seal is strong enough
to hold the object's weight, given where the cup is compared with the object's
centre of mass. A cup at the very edge of a heavy box may seal but still tear off,
because the box's weight twists it.

---

## 4. How it is trained

### Suction models

Suction labels come from the same three sources as other grasp labels.

- People can mark pictures by hand. A person colours the pixels where a cup would
  seal. This is quick to start, but a person cannot label millions of pictures.
- A computer can use physics on 3D models. A computer places a virtual cup on a 3D model of an
  object. It checks whether the rim touches all the way round and whether the seal
  can hold the object's weight. It then renders a depth picture of the scene. This
  can make millions of labelled examples with no robot.
- A real robot can try. A robot places the cup, turns the pump on and lifts. A
  pressure sensor in the tube says whether the cup sealed. This gives true labels,
  but each one takes several seconds of robot time.

### Affordance models

Affordance labels mostly come from people. A person colours each part of an object
in a picture with the name of its job. This is slow, so affordance datasets are
small. The **UMD part affordance dataset** from the University of Maryland is a
well-known example. It labels kitchen, garden and workshop tools with seven jobs:
grasp, cut, scoop, contain, pound, support and wrap-grasp.

Because hand labels are slow, newer work learns affordances in other ways. One way
is to watch videos of people using objects. Where a person's hand touches a
drawer, that spot is probably the handle. Another way is to let a robot poke and
pull objects in a simulator and record which spots made something move.

---

## 5. Well-known models

These are real models. Book 3's
[suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section lists the suction code and its licences.

- **The MIT and Princeton picking system (2018)**, by Andy Zeng and others, was built
  for the Amazon Robotics Challenge. Fully convolutional networks painted a suction
  map and a finger-grasp map over pictures of a cluttered tote. The robot picked the
  best spot from either map.
- **Dex-Net 3.0** (2018) learned suction grasps from millions of synthetic depth
  pictures, labelled by a physics model of how a rubber cup bends and seals.
- **Dex-Net 4.0** (2019) trained one system for both a suction cup and a
  parallel-jaw gripper. For each object it chooses which of the two to use.
- **SuctionNet-1Billion** (2021) is a suction dataset and baseline model built on
  the same scenes as GraspNet-1Billion. It gives each spot a seal score and a wrench
  score.
- **AffordanceNet** (2018) finds each object in a picture, draws a box around it,
  and colours each part of the object with its job.
- **Where2Act** (2021) learned, in a simulator, where to push or pull on doors,
  drawers and other objects with moving parts.

---

## 6. A worked example: a tote and a kitchen drawer

### Suction: a tote of parcels

An arm with a suction cup must empty a tote of boxes, cans and soft bags.

1. A camera above the tote takes a colour and a depth picture.
2. The suction model paints a score on every pixel. The middles of the flat box tops
   score high. The edges, the bags and anything round score low.
3. Code picks the best pixel. It measures which way the surface faces there, from
   the depth picture, and sends the cup in along that direction.
4. The arm presses the cup on, and the pump starts. A pressure sensor checks that the
   cup sealed before the arm lifts.
5. If the seal fails, the pixel is marked as bad for this round, and the arm tries
   the next best one.

### Affordance: a knife in a drawer

A kitchen robot must take a knife out of a drawer and hand it to a person.

1. An affordance model colours the knife: the handle as "grasp", the blade as
   "cut".
2. A [six-degree-of-freedom grasp model](01_six-dof-grasps.md) proposes many grasps
   on the knife.
3. Code keeps only the grasps whose finger contacts land on pixels labelled
   "grasp". The blade grasps are thrown away.
4. The arm takes the knife by the handle. To hand it over, it turns so that the
   handle points at the person.

---

## 7. What goes wrong

For suction models:

- Some surfaces cannot seal. Porous, textured, ribbed, dusty or oily surfaces
  leak. The model may not see the difference in a picture. A cardboard box with a
  mesh window may look flat but leak through the mesh.
- Heavy objects can tear off when held off centre. A cup near the edge of a heavy box can seal and
  still tear off. Models with a wrench score handle this better.
- Soft bags change shape. A bag's surface changes shape when the cup presses on it. The
  picture taken before the press does not show the shape after it.
- Shiny and see-through objects leave holes. The depth picture has holes there, so the
  direction the surface faces is unknown.

For affordance models:

- Objects it has not seen may be labelled wrongly. The model learned jobs from a small set of labelled
  objects. A tool with an unusual shape may be labelled wrongly.
- Some parts do two jobs. The rim of a cup is for drinking from, and it is
  also a fine place to hold an empty cup. The label map can give only one answer
  per pixel.
- The list of jobs is fixed. Each new job needs new labelled pictures. The
  [open-vocabulary models](../../02_seeing-models/02_most-used/03_open-vocabulary-models.md) page
  covers models that can be asked about a part in words instead, which removes the
  fixed list.

---

## 8. Why this kind, and what it costs

A suction model takes a picture and gives a score for every pixel that says where
a cup would seal. An affordance model takes a picture and says what each part of an
object is for.

### Suction

What a suction model does for you is pick many kinds of object fast. Boxes, books,
bottles and bags can all be held by one cup, and the arm does not need to get its
fingers round anything.

The obvious alternative is not a finger-grasp model. It is plain geometry. Code
fits small flat patches to the depth picture, rejects patches that are too curved
or too small, and ranks what is left by size and by distance from the edge. Book
3's [suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section says this takes a dozen lines of code and is hard to beat. Try it first.

A suction model is worth its cost when the geometry keeps choosing badly. That
happens with lumpy bags, tight clutter where edges are hard to find, and objects
whose surface looks flat but leaks. The model can learn those cases from examples.

What it costs you is labelled data, a graphics card for training, and a model that
still cannot tell a porous surface from a smooth one in some pictures.

### Affordance

What an affordance model does for you is add the one thing grasp models lack: which
part of the object is for holding.

The obvious alternative is to write it down by hand. "Hold a knife by the handle"
is a rule, and for a small set of known tools a rule is cheaper and more reliable.
Book 3's
[choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#10-why-a-rule-beats-a-network)
makes this case. An affordance model is for many tools, or tools you have not
listed.

What it costs you is hand-labelled pictures, which are slow to make, and a fixed
list of jobs.

---

## 9. The written alternative

For suction, the plain geometry that section 8 describes is built from Book 5
pages. [RANSAC](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md) fits flat patches to the depth points. The
[distance transform](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/02_morphology-and-distance-transform.md) finds the point of a part's mask that is furthest
from every edge, and says whether the cup fits there. For affordances, the
written way is a rule for each kind of object, such as "hold a knife by the
handle", written as Book 3's [rules from a measured
profile](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#6-rules-from-a-measured-profile) describes. The written methods
win on boxes and on tools you have listed. The models win on lumpy bags, tight
clutter, surfaces that look flat but leak, and tools nobody has listed.

---

## 10. Where to read next

- [Grasp quality models](../03_also-used/02_grasp-quality-models.md) scores one grasp at a time,
  including suction grasps.
- [Segmentation](../../02_seeing-models/02_most-used/02_segmentation.md) explains the per-pixel
  networks these models are built from.
- [Open-vocabulary models](../../02_seeing-models/02_most-used/03_open-vocabulary-models.md) can find
  a part of an object from words such as "the handle".
- Book 3's [grippers and hardware](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md)
  explains suction cups and how much they can lift.
- Book 3's [holding on](../../../03_frameworks/02_gripping/05_holding-on.md) covers
  what to do once the cup or fingers are on the object.
