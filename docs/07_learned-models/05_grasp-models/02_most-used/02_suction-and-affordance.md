# Suction and affordance

This page is about grasp models that paint a score onto every part of a picture.
There are two kinds of them, and they share one design. A **suction model** paints
where a suction cup would seal. An **affordance model** instead paints what each
part of an object is for, such as "hold here" or "this part cuts".

So the page answers these questions, one section at a time. What is a suction
grasp, and why is it easier to predict than a finger grasp? What is an affordance,
and what do these models take in and give back? How do they work inside, and how
are they trained? Which real models do this, and when are they the right choice?

It is for a reader who has read the [grasp models overview](../01_overview.md) and
[top-down grasp detection](../03_also-used/01_top-down-grasp-detection.md), because
the per-pixel maps on that page are the same idea used here. It also helps to have
read [segmentation](../../03_seeing-models/02_most-used/02_segmentation.md), since
an affordance model is a kind of segmentation model.

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
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

The two kinds named in the introduction have more in common than their names
suggest. Both of them paint a map over the picture that says, for each pixel, how
well a certain action would work there.

### Suction

A **suction gripper** holds an object with a soft rubber cup, and a pump sucks the
air out from under that cup. The air outside then pushes the object against the cup
and holds it there, which is the same thing that happens when a suction hook sticks
to a bathroom tile.

The cup only holds if its rim touches the surface all the way round, and that
contact is called a **seal**. So if any part of the rim hangs in the air, air leaks
in and the object drops.

![A suction cup on a flat top, over an edge, and on a small ball](../../../images/grasp-models/suction-and-affordance/seal-or-leak.svg)

On the flat top of a box, the rim touches all the way round and the cup seals. Over
the edge, or on a small ball, part of the rim does not touch, so air leaks in.

That makes a suction grasp a simpler question than a finger grasp. This is because
there is only one contact instead of two, and the cup always pushes straight into
the surface. The only question left is whether a cup touching a given spot would seal
and would hold the weight. So a suction model answers that for every pixel.

### Affordance

An **affordance** is what a part of an object lets you do with it. For example, a
mug's handle affords holding, the inside of the mug affords containing liquid, and
a knife's blade affords cutting. The word comes from the study of how people and
animals see the world, and robotics borrowed it.

An affordance model paints each pixel of an object with the job that part is for.
That means a robot can then hold a knife by the handle, or hand a mug to a person
with the handle towards them.

![A mug and a knife, coloured by what each part is for](../../../images/grasp-models/suction-and-affordance/parts-for-jobs.svg)

The mug's handle is for holding, its inside is for containing and its outside is
for wrapping a hand round. The knife's handle is the only safe part to hold, so a
grasp model that only asks whether a grip will hold might choose the blade
instead.

---

## 2. What goes in and what comes out

Because the two kinds answer different questions, their inputs and outputs differ
as well. For a **suction model**:

- The input is a colour picture, a depth picture, or both, taken from above.
- The output is a **suction map**, which holds one score between 0 and 1 for every
    pixel. A high score means a cup placed there, pressing straight into the
    surface, is likely to seal and hold.
- Code then picks the pixel with the best score, and it works out from the depth
    picture which direction the surface faces at that pixel. The cup comes in along
    that direction.

![A picture of a tote and the suction score for every pixel](../../../images/grasp-models/suction-and-affordance/suction-map.svg)

On the left is a tote with a box, a can, a ball and a soft bag. On the right is the
suction score for every pixel. The flat middle of the box and the can's lid score
high, while the edges, the ball and the lumpy bag score low. The red star marks the
best spot of all.

For an **affordance model**:

- The input is a colour picture, sometimes with depth.
- The output is a **label map**, which gives for every pixel the name of the job
    that part of the object is for, such as "grasp", "cut" or "contain". Some
    models also draw a box around each object first, and paint the labels inside
    the box.
- Code then keeps only the grasps that land on a part labelled "grasp", and those
    grasps can come from any grasp model in this chapter.

---

## 3. How it works inside

Although the two kinds paint different maps, both use the same shape of network,
which is the same shape used for
[segmentation](../../03_seeing-models/02_most-used/02_segmentation.md).

1. **An encoder shrinks the picture.** A convolutional neural network (CNN) reads
    the picture and turns it into a smaller grid of numbers, where each number
    describes a patch of the picture such as "flat surface" or "curved edge".
2. **A decoder grows it back.** A second part of the network turns the small grid
    back into a picture the same size as the input.
3. **Each pixel gets an answer.** For a suction model each pixel gets one score,
    while for an affordance model each pixel gets one score per job and the job
    with the highest score wins.

A network whose output is a picture the same size as its input is called a **fully
convolutional network**. The
[encoders and decoders](../../01_what-models-are/03_inside-a-neural-network.md#7-encoders-and-decoders)
section of the inside a neural network page explains its two halves.

Systems that paint a finger-grasp map next to the suction map need one extra step
for angles. This is because a finger grasp needs an angle while a suction cup does
not. So they turn the input picture by several angles, run the network on each
turned copy, and keep the best answer. That means a network which only learned one
jaw direction can find grasps at any angle.

Suction models often split the score into two parts rather than one. A **seal
score** says whether the cup will seal on the surface. A **wrench score** then says
whether that seal is strong enough to hold the object's weight, given where the cup
sits compared with the object's centre of mass. A cup at the very edge of a heavy box may seal and still
tear off, because the box's weight twists it.

---

## 4. How it is trained

### Suction models

Those networks cannot paint anything until they are shown examples, and suction
labels come from the same three sources as other grasp labels.

- People can mark pictures by hand, so a person colours the pixels where a cup
    would seal. This is quick to start with, but a person cannot label millions of
    pictures.
- A computer can use physics on 3D models, so it places a virtual cup on a 3D model
    of an object and checks whether the rim touches all the way round and whether
    the seal can hold the object's weight. It then draws a depth picture of the
    scene, which means millions of labelled examples can be made with no robot.
- A real robot can try, so it places the cup, turns the pump on and lifts, and a
    pressure sensor in the tube says whether the cup sealed. This gives true
    labels, but each one takes several seconds of robot time.

### Affordance models

Affordance labels mostly come from people instead, because a person has to colour
each part of an object in a picture with the name of its job. This is slow, so
affordance datasets are small. The **UMD part affordance dataset** from the
University of Maryland is a well-known example. It labels kitchen, garden and
workshop tools with seven jobs, which are grasp, cut, scoop, contain, pound,
support and wrap-grasp.

Because hand labels are slow, newer work learns affordances in other ways. One way
is to watch videos of people using objects, since the spot where a person's hand
touches a drawer is probably the handle. Another way is to let a robot poke and
pull objects in a simulator and record which spots made something move.

---

## 5. Well-known models

Both designs above appear in models you can read about, and these are the real
ones. Book 3's
[suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section lists the suction code and its licences.

- **The MIT and Princeton picking system (2018)**, by Andy Zeng and others, was
    built for the Amazon Robotics Challenge. Fully convolutional networks painted a
    suction map and a finger-grasp map over pictures of a cluttered tote, so the
    robot could pick the best spot from either map.
- **Dex-Net 3.0** (2018) learned suction grasps from millions of synthetic depth
    pictures, labelled by a physics model of how a rubber cup bends and seals.
- **Dex-Net 4.0** (2019) trained one system for both a suction cup and a
    parallel-jaw gripper, so that for each object it chooses which of the two to
    use.
- **SuctionNet-1Billion** (2021) is a suction dataset and baseline model built on
    the same scenes as GraspNet-1Billion, and it gives each spot a seal score and a
    wrench score.
- **AffordanceNet** (2018) finds each object in a picture, draws a box around it,
    and colours each part of the object with its job.
- **Where2Act** (2021) learned, in a simulator, where to push or pull on doors,
    drawers and other objects with moving parts.

---

## 6. A worked example: a tote and a kitchen drawer

### Suction: a tote of parcels

Those models are easier to follow once they run in order, so here an arm with a
suction cup must empty a tote of boxes, cans and soft bags.

1. A camera above the tote takes a colour and a depth picture.
2. The suction model paints a score on every pixel, so the middles of the flat box
    tops score high while the edges, the bags and anything round score low.
3. Code picks the best pixel, measures from the depth picture which way the surface
    faces there, and sends the cup in along that direction.
4. The arm presses the cup on and the pump starts, and a pressure sensor checks
    that the cup sealed before the arm lifts.
5. If the seal fails, the pixel is marked as bad for this round, and the arm tries
    the next best one.

### Affordance: a knife in a drawer

The affordance side runs in the same shape, so here a kitchen robot must take a
knife out of a drawer and hand it to a person.

1. An affordance model colours the knife, marking the handle as "grasp" and the
    blade as "cut".
2. A [six-degree-of-freedom grasp model](01_six-dof-grasps.md) proposes many grasps
    on the knife.
3. Code keeps only the grasps whose finger contacts land on pixels labelled
    "grasp", so the blade grasps are thrown away.
4. The arm takes the knife by the handle, and then it turns so that the handle
    points at the person before handing it over.

---

## 7. What goes wrong

Both examples above went smoothly, but each kind fails in its own way. For suction
models:

- Some surfaces cannot seal, because porous, textured, ribbed, dusty or oily
    surfaces leak and the model may not see the difference in a picture. A
    cardboard box with a mesh window may look flat but leak through the mesh.
- Heavy objects can tear off when held off centre, so a cup near the edge of a
    heavy box can seal and still tear off. Models with a wrench score handle this
    better.
- Soft bags change shape when the cup presses on them, which means the picture
    taken before the press does not show the shape after it.
- Shiny and see-through objects leave holes in the depth picture, so the direction
    the surface faces is unknown there.

For affordance models:

- Objects it has not seen may be labelled wrongly, because the model learned its
    jobs from a small set of labelled objects. A tool with an unusual shape is the
    usual case.
- Some parts do two jobs, since the rim of a cup is for drinking from and is also a
    fine place to hold an empty cup. The label map can give only one answer per
    pixel.
- The list of jobs is fixed, so each new job needs new labelled pictures. The
    [open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
    page covers models that can be asked about a part in words instead, which
    removes the fixed list.

---

## 8. Why this kind, and what it costs

Since those failures are real, it is worth setting out what each kind buys you. A
suction model takes a picture and gives a score for every pixel that says where a
cup would seal. An affordance model instead takes a picture and says what each part
of an object is for.

### Suction

So what a suction model does for you is pick many kinds of object fast. Boxes, books,
bottles and bags can all be held by one cup, and the arm does not need to get its
fingers round anything.

The obvious alternative is not a finger-grasp model but plain geometry. Code can
fit small flat patches to the depth picture and reject the patches that are too
curved or too small. It then ranks what is left by size and by distance from the
edge. Book 3's
[suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section says this takes a dozen lines of code and is hard to beat, so try it first.

So a suction model is worth its cost only when that geometry keeps choosing badly.
That happens with lumpy bags, tight clutter where edges are hard to find, and
objects whose surface looks flat but leaks. The model can learn those cases from
examples, which is what you are paying for.

What it costs you is labelled data, a graphics card for training, and a model that
still cannot tell a porous surface from a smooth one in some pictures.

### Affordance

What an affordance model does for you is add the one thing grasp models lack, which
is knowing which part of the object is meant for holding.

The obvious alternative is to write that down by hand, because "hold a knife by the
handle" is already a rule. For a small set of known tools a rule is cheaper and
more reliable, and Book 3's
[choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#10-why-a-rule-beats-a-network)
makes exactly this case. So an affordance model is for many tools at once, or for
tools you have not listed.

What it costs you is hand-labelled pictures, which are slow to make, and a fixed
list of jobs.

---

## 9. The written alternative

For suction, the plain geometry that section 8 describes is built from Book 5
pages.
[RANSAC](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md)
fits flat patches to the depth points. Then the [distance
transform](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/02_morphology-and-distance-transform.md)
finds the point of a part's mask that is furthest from every edge, and says whether
the cup fits there. For affordances, the written way is instead a rule for each kind
of object, such as "hold a knife by the handle", written as Book 3's [rules from a
measured
profile](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#6-rules-from-a-measured-profile)
describes. The written methods win on boxes and on tools you have listed. Instead,
the models win on lumpy bags, tight clutter, surfaces that look flat but leak, and
tools nobody has listed.

---

## 10. Where to read next

- [Grasp quality models](../03_also-used/02_grasp-quality-models.md) scores one
    grasp at a time, including suction grasps.
- [Segmentation](../../03_seeing-models/02_most-used/02_segmentation.md) explains
    the per-pixel networks these models are built from.
- [Open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
    can find a part of an object from words such as "the handle".
- Book 3's [grippers and hardware](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md)
    explains suction cups and how much they can lift.
- Book 3's [holding on](../../../03_frameworks/02_gripping/05_holding-on.md) covers
    what to do once the cup or fingers are on the object.

---

## 11. Using it in Python

Section 3 said that a suction model paints a score over every pixel and then picks
the best one, and section 5 named Dex-Net 3.0 and Dex-Net 4.0 as the models that do
this. This section shows how their code is actually called, so that after reading it
you will know what the download gives you and how old it is.

The code for Dex-Net's suction models lives in
[gqcnn](https://github.com/BerkeleyAutomation/gqcnn), from the University of
California, Berkeley. It is not on the Python package index, so you clone it and
install it from the clone. The class below plans a suction grasp on one depth
picture.

```python
import numpy as np
from autolab_core import (BinaryImage, CameraIntrinsics, ColorImage, DepthImage,
                          RgbdImage, YamlConfig)
from gqcnn.grasping import FullyConvolutionalGraspingPolicySuction, RgbdImageState

config = YamlConfig("cfg/examples/fc_gqcnn_suction.yaml")   # names the weights folder
policy = FullyConvolutionalGraspingPolicySuction(config["policy"])

camera_intr = CameraIntrinsics.load("primesense.intr")
depth_im = DepthImage(np.load("depth_0.npy"), frame=camera_intr.frame).inpaint()
color_im = ColorImage(np.zeros([depth_im.height, depth_im.width, 3], np.uint8),
                      frame=camera_intr.frame)
segmask = BinaryImage.open("segmask_0.png")   # which pixels are objects, from my own code

state = RgbdImageState(RgbdImage.from_color_and_depth(color_im, depth_im),
                       camera_intr, segmask=segmask)
action = policy(state)
print(action.q_value, action.grasp.center, action.grasp.axis, action.grasp.depth)
```

The library gives you the trained network, the sliding of it over the whole picture,
and the choosing of the best pixel. It also gives you the answer in a form you can
act on: `action.grasp` is a `SuctionPoint2D`, whose `center` is the pixel to put the
cup on, whose `axis` is the direction the cup should point along, and whose `depth`
is how far away that pixel is. The `q_value` beside it is the model's estimate of
how likely the seal is to hold, between 0 and 1, and that number is the whole point
of the model. The call to `inpaint` is also the library's, and you need it, because a
depth camera returns holes where it saw nothing and the network cannot read a hole.

What you have to supply is the segmentation mask, which says which pixels belong to
objects rather than to the bin, and the fully convolutional policy will refuse to
run without one. You also have to supply the camera's intrinsic parameters in
Berkeley's own `.intr` file format, and to download the weights separately, because
the repository ships code and not models. Then, as with every grasp model, you have
to move the answer into the robot's frame with your own calibration and write the
motion that goes there, switches the pump on and lifts.

The cost you have to accept here is the age of the code. `gqcnn` pins TensorFlow to
version 1.15 or below and had its last commit in January 2022, so it will not
install alongside a current PyTorch or TensorFlow, and in practice people run it in
a container with an old Python. Its licence allows education, research and
not-for-profit use only. SuctionNet-1Billion, the newer dataset from section 5, has
a baseline repository of the same kind rather than a package, and it was written
against PyTorch 1.4. For affordance models such as Where2Act there is no packaged
release at all, only the authors' training code and the simulator they used.

The decision that is yours is whether your cup matches theirs. The Dex-Net suction
weights were trained on one particular rubber cup, of one diameter and one
stiffness, and the seal score means "would that cup seal here". A larger cup needs a
flatter patch than the model was taught to look for, and a stiffer cup tolerates
less curvature, so the scores drift away from the truth in a direction you cannot
see from the number. Retraining on your own cup is possible, because the labels come
from a physics model rather than from real attempts, but it means running Dex-Net's
dataset generation, which is a much larger job than calling the policy.
