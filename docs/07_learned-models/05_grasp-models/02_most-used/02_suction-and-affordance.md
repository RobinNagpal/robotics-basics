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
6. [Where this is going](#6-where-this-is-going)
7. [Where to read next](#7-where-to-read-next)

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
SuctionNet-1Billion, in
[section 5.2](#52-suctionnet-1billion-the-current-suction-benchmark), is a network
of exactly this shape, and AffordanceNet, in
[section 5.4](#54-affordancenet-the-one-the-affordance-papers-measure-against),
puts a second branch beside it that draws a box round each object first and then
paints the labels inside the box.

Systems that paint a finger-grasp map next to the suction map need one extra step
for angles. This is because a finger grasp needs an angle while a suction cup does
not. So they turn the input picture by several angles, run the network on each
turned copy, and keep the best answer. That means a network which only learned one
jaw direction can find grasps at any angle. Dex-Net 4.0, in
[section 5.1](#51-the-dex-net-suction-models-30-and-40), is a system of that kind,
because it paints a suction map and a finger-grasp map for the same object and
then picks whichever of the two scores better.

Suction models often split the score into two parts rather than one. A **seal
score** says whether the cup will seal on the surface. A **wrench score** then says
whether that seal is strong enough to hold the object's weight, given where the cup
sits compared with the object's centre of mass. A cup at the very edge of a heavy box may seal and still
tear off, because the box's weight twists it. SuctionNet-1Billion's baseline model
does exactly this, because it gives the network two output channels and multiplies
them together, and
[section 5.2](#52-suctionnet-1billion-the-current-suction-benchmark) describes
it.

Two models in the shortlist paint a map that is neither of the two described so
far. Where2Act, in
[section 5.5](#55-where2act-affordances-for-things-that-move), scores a pixel for
one action at a time, so its answer says how likely a push or a pull is to move
something there rather than what the part is for. CLIPSeg, in
[section 5.6](#56-clipseg-asking-for-a-part-in-words), has no fixed list of jobs
at all. An affordance model's last layer has one channel for each job it was
trained on, and that is what fixes the list. CLIPSeg replaces those channels with
a text encoder, so you give it a phrase and it scores every pixel against that
phrase instead. The
[open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
page explains that design.

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

Sections 1 to 4 explained the two kinds of model. This section names the ones you
can download, says what cup or gripper each one assumes, and shows the shortest
real code for each. Fewer models exist here than for finger grasps, and for both
kinds the best answer often involves no model at all, so read
[section 5.7](#57-how-to-choose) before you start installing anything.

Every licence below was read from the project's own licence file, and Book 3's
[suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section covers the suction half in more detail. The table has one row per model,
in the order the sub-sections cover them. The left column names the model and says
how current it is. The right column starts with the cup or the gripper the model
assumes, because that is what decides whether its answer applies to your hardware,
and then gives what the model is best at, how big it is, the licence of its code
and when to pick it. A size is the download size of the weights, given where the
file is published somewhere its size can be read, because none of these projects
publishes a parameter count.

| Model | What decides it |
| --- | --- |
| **Dex-Net 3.0 and 4.0**, historical | The cup is one rubber cup of one diameter and one stiffness, fixed in the weights, and nothing in the answer tells you how far your own cup differs from it. It is best at giving you a packaged suction policy you can call in five lines. The size of the weights is `not stated`, and the licence is a University of California grant for education, research and not-for-profit use only. Pick it when you want a working suction policy today and can run it under an old Python. |
| **SuctionNet-1Billion**, most used in 2026 | The cup is the one its physics model used when the labels were made, and the repository offers no way to change it. It is a current suction model, and it is the benchmark other people report their numbers on. The size of the weights is `not stated`, and there is no licence file at all. Pick it when you are measuring a suction model against published numbers. |
| **GraspGen's suction model**, worth betting on | It is the only model here that states its cup, which is a single cup of 30 millimetre radius, and its README gives a correction for a different one: scale the object's points by your radius divided by 0.030. So it is the one to use when you know your cup's radius. The weights are 907 megabytes plus 166 megabytes, and the code is under the NVIDIA License, which permits non-commercial use only. Pick it when your cup is not 30 millimetres and you can rescale for it. |
| **AffordanceNet**, historical | It assumes no cup and no gripper, because it paints part labels that you then filter another model's grasps against. It is best at finding objects and painting their parts in one pass, and the paper reports 150 milliseconds per picture. The size of the weights is `not stated`, and the only licences in the repository are those of the code it was built from. Pick it when you are reading the paper, not shipping the model. |
| **Where2Act**, historical | It assumes no cup and no gripper either, and what it paints is where a push or a pull would move something rather than where a hold would work. So it is best at saying where to push or pull a door, a drawer or a lid. The size of the weights is `not stated`, and there is no licence file at all. Pick it when your objects have moving parts and you work in simulation. |
| **CLIPSeg, used for parts**, most used in 2026 | It assumes no cup and no gripper, because you type a phrase, it paints the pixels that match, and you filter grasps with that. It is best at asking for "the handle" in words, and nothing has to be trained first. The weights are 603 megabytes, the output is 352 by 352 pixels whatever size you gave it, and the licence is Apache-2.0 on the model card and on `transformers`. Pick it when you need part labels now, for objects nobody listed. |

Every row above opens with a cup or a gripper for one reason. A suction model's
score answers the question "would the cup I was trained on seal here", and that cup
is fixed in the weights. A model trained on a 30 millimetre cup scores a flat patch
25 millimetres wide as good, because that cup fits there, while a 50 millimetre cup
does not. Each sub-section below says more about the cup its model assumes.

### 5.1 The Dex-Net suction models, 3.0 and 4.0

**Both are historical**, because they were published in 2018 and 2019 and the
library that runs them has not followed the rest of Python.

Size not stated, the size of the weights not stated, a laptop, and a University of
California grant for education, research and not-for-profit use only.

They come from Ken Goldberg's laboratory at the University of California,
Berkeley. [Dex-Net 3.0](https://arxiv.org/abs/1709.06670) learned suction grasps from
millions of simulated depth pictures labelled by a physics model of how a rubber
cup bends and seals. Dex-Net 4.0 then trained one system for a suction cup and a
two-finger gripper together, so that for each object it chooses which of the two
to use; the [Dex-Net project page](https://berkeleyautomation.github.io/dex-net/)
collects both.

The one idea Dex-Net is built on is that "will this cup hold here" is a local
question. Whether the rim seals depends on the shape of the surface under the rim
and on nothing else in the picture. So the network never has to see the whole
scene: a small patch of the depth picture around the candidate point, lined up with
the direction the cup would come in, is enough to answer with. Everything else
follows from that, including how the training data was made, because a physics
model of a rubber cup bending onto a surface can label millions of such patches
with no robot in the room.

Inside, the model is one small convolutional network, called a GQ-CNN for grasp
quality convolutional network, and it answers with a single number: the estimated
chance that this grasp holds. The first version was run once for each candidate
patch. The version the code below uses, the fully convolutional one, does the same
arithmetic in a single pass over the whole picture, because a network built only of
convolutions can be slid across a large picture instead of being re-run on crops,
and what comes back is then a score for every pixel. Dex-Net 4.0 adds a second
network of the same kind for the two-finger gripper, and the policy runs both and
keeps whichever score is higher, which is how one system chooses between a cup and
fingers.

That last step is where suction and fingers part company, and the repository's own
configuration files show it plainly. For the cup, the answer at a pixel is one
number. The cup is round, so there is no angle to choose, and the direction it
comes in is the direction the surface faces, which code reads straight off the
depth picture: the suction policy takes the surface normal at the chosen pixel
rather than asking the network for it. A finger grasp at the same pixel is not one
number. It also needs an angle for the jaws and a height at which to close, and
neither of those is settled by the surface. So the parallel-jaw policy gives its
network one output channel per jaw angle and runs it again on a copy of the picture
for each of sixteen heights, which is what the `num_depth_bins: 16` line in its
configuration file means, while the suction policy has one channel and one copy of
the picture. That is the general rule: a suction model can be a plain
picture-to-picture network because its answer is one number per pixel, and a finger
model becomes one only by stacking channels and copies, at a cost multiplied by
every angle and height you want to consider.

On an arm, the difference from SuctionNet-1Billion below is what you are handed
back. Dex-Net's policy returns a cup pose, which is a pixel, the axis to come in
along and how far away that pixel is, and that is almost what the robot needs.
SuctionNet's repository returns a map and a benchmark score, and the normal
estimation, the pose and the live camera loop are yours to write. So if the job
this week is to get a cup onto flat-topped cartons, Dex-Net is the shorter path.
The moment those cartons become a tight tote of mixed items, its single-object
simulated training is what starts to cost you.

You would pick Dex-Net rather than SuctionNet-1Billion for one reason, which is
that Dex-Net is the only suction model in this section that ships as a library
with a policy object you can call. SuctionNet publishes training and benchmark
scripts and expects you to write the rest. If what you want is a suction score on
your own depth picture this afternoon, Dex-Net is the shortest path there.

What it costs you is the age of the code. The
[gqcnn](https://github.com/BerkeleyAutomation/gqcnn) repository was last changed
in April 2024 and pins TensorFlow to version 1.15 or below, so it will not install
beside a current PyTorch or TensorFlow, and people run it in a container with an
old Python. That old TensorFlow is also the reason a laptop is enough: the
installer looks for an NVIDIA device and installs the processor-only build when it
finds none. The thing that most often goes wrong is the segmentation mask, because
the fully convolutional policy refuses to run without one and the repository does not
provide a way to make it.

```python
import numpy as np
from autolab_core import (BinaryImage, CameraIntrinsics, ColorImage, DepthImage,
                          RgbdImage, YamlConfig)
from gqcnn.grasping import FullyConvolutionalGraspingPolicySuction, RgbdImageState

config = YamlConfig("cfg/examples/fc_gqcnn_suction.yaml")   # names the weights
policy = FullyConvolutionalGraspingPolicySuction(config["policy"])

camera_intr = CameraIntrinsics.load("primesense.intr")
# inpaint fills the holes a depth camera leaves; the network cannot read a hole.
depth_im = DepthImage(np.load("depth_0.npy"), frame=camera_intr.frame).inpaint()
color_im = ColorImage(np.zeros([depth_im.height, depth_im.width, 3], np.uint8),
                      frame=camera_intr.frame)
segmask = BinaryImage.open("segmask_0.png")   # which pixels are objects: yours

state = RgbdImageState(RgbdImage.from_color_and_depth(color_im, depth_im),
                       camera_intr, segmask=segmask)
action = policy(state)
# q_value is the estimated chance the seal holds; center is the pixel to press on
print(action.q_value, action.grasp.center, action.grasp.axis, action.grasp.depth)
```

The library slides the network over the whole picture, picks the best pixel, and
hands back a `SuctionPoint2D` whose `center` is where to put the cup, whose `axis`
is the direction to come in along, and whose `depth` is how far away that pixel
is. What you supply is the segmentation mask, the camera's intrinsic parameters in
Berkeley's own `.intr` file format, and the weights, which are downloaded
separately from the code. The cup in those weights is one particular rubber cup of
one diameter and one stiffness, and nothing in the answer tells you how far your
own cup differs from it.

### 5.2 SuctionNet-1Billion, the current suction benchmark

**SuctionNet-1Billion is the most used of these models in 2026 for measurement.**

Size not stated, the size of the weights not stated, an NVIDIA card whose memory
the project never names, and no licence file at all.

Hanwen Cao and others at Shanghai Jiao Tong University published it in 2021, in
the [SuctionNet-1Billion paper](https://arxiv.org/abs/2103.12311), with a
[baseline repository](https://github.com/graspnet/suctionnet-baseline) of code. It
comes from the same group as the GraspNet-1Billion dataset that
[section 4](#4-how-it-is-trained) described, and its labels are made the same way,
on real camera pictures of real cluttered scenes rather than on simulated ones.
Its physics model scores two things separately, which are whether the cup seals
and whether the seal resists the twisting force the object's weight applies, and
the [dataset page](https://graspnet.net/suction) publishes the labels.

The one idea is to change nothing about the network and everything about what its
channels mean. The model is DeepLabV3+, an ordinary semantic segmentation network
of the encoder and decoder shape described in
[section 3](#3-how-it-works-inside), taken as it comes. Nothing inside it knows
what suction is. The suction is entirely in the labels it was trained on and in
how its two output channels are read, which is what `--num_classes 2` in the
command below is saying: those are not two kinds of object, they are the seal
score and the wrench score.

Next to Dex-Net, what that changes is that the two halves of the physics stay
apart. Dex-Net's physics model also works out a seal and a resistance to twisting,
but it folds them into one label before training, so its network learns one number.
SuctionNet trains the network to predict both, and the inference script multiplies
them to get the final map, then blurs the product with a 15 by 15 box filter before
taking the highest pixels. So a pixel has to pass both tests, and a lone high pixel
surrounded by low ones is averaged away. The labels differ as well: Dex-Net's come
from simulated depth pictures of objects standing alone, while SuctionNet's physics
was applied to real camera pictures of real cluttered scenes.

What the split buys is a model that can tell the two failures apart. The flat top
of a heavy box seals wherever you press on it, and yet a spot near one edge will
still tear off as the weight twists the cup. One score cannot say both of those
things at once, and a product of two can, which also means you can look at the two
maps separately when the model picks badly and see which half was wrong. The blur
buys something smaller but real: a cup is wide, so a flat spot one pixel across is
no use to it, and averaging over a window is a cheap way of saying so. What it
costs is that nothing in the network is about suction, so nothing comes back except
the map. There is no cup pose, no cup radius and no notion of which object a pixel
belongs to, and every step after "which pixel" is yours to write.

On an arm, the difference from Dex-Net is the camera. SuctionNet's labels were
computed on pictures from real depth cameras of real clutter, so its map over a
tote of mixed bags and boxes fails in the ways its training data already failed,
while Dex-Net saw clean simulated depth of single objects and meets the noise for
the first time on your bench. Set against that, Dex-Net hands you a pose and
SuctionNet hands you a map. Pick SuctionNet when your number has to be comparable
with published ones, and set aside the afternoon it takes to turn its best pixel
into something the robot can reach for.

You would pick it rather than Dex-Net because its scenes are real camera pictures
of real clutter, while Dex-Net's are simulated pictures. That is the difference
that shows up when a cup has to find a flat patch among other objects rather than
on an object standing by itself.

What it costs you is the environment and the preparation. Its README states it was
tested with CUDA 10.1 and PyTorch 1.4.0 on Ubuntu 16.04, which is old enough that
people build a container for it, and the **absent licence file** means default
copyright and no permission to use it. The thing that most often goes wrong is the
preparation, because training needs extra labels that you generate yourself with
two of its scripts before you can start.

```bash
# Run the published suction model over the benchmark's test scenes.
# --num_classes 2 is the seal score and the wrench score, not two object classes.
python inference.py --model deeplabv3plus_resnet101 --num_classes 2 \
  --checkpoint_path checkpoints/checkpoint_30 --camera realsense \
  --split test_seen --dataset_root /path/to/suctionnet --save_dir results
```

What you supply is the dataset on disk, the compiled environment, and your own
program if you want the model on a live camera, because this script reads the
benchmark's files. The cup behind these labels is the one SuctionNet's physics
model used, and the repository does not offer a way to change it.

### 5.3 GraspGen's suction model, the one that tells you the cup radius

**GraspGen's suction model is worth betting on**, because it is the only suction
model here that states the radius of the cup it was trained for and then tells you
what to do about a different one.

Size not stated, the weights are 907 megabytes plus 166 megabytes, an NVIDIA card
because `spconv-cu120` has no processor-only build, NVIDIA's own non-commercial
licence for the code and the NVIDIA Open Model License for the weights.

[GraspGen](https://github.com/NVlabs/GraspGen) is NVIDIA's 2025 grasp generator,
and alongside its two finger grippers it publishes a checkpoint for a
single-contact suction gripper with a 30 millimetre radius, trained on part of the
57 million grasps it released for 8,515 objects from the Objaverse XL object
collection.

The one idea is that a suction grasp is a pose, not a pixel. GraspGen treats the
cup as one more gripper: it produces full 3D cup poses from an object's points and
then scores them, and the same code path serves its Franka hand and its Robotiq
hand.

That makes it different from both models above in the place that matters most.
Dex-Net and SuctionNet paint a score onto a picture, and turning the chosen pixel
into a pose is your work. GraspGen never makes a picture. It encodes one segmented
object's points, starts from poses that are pure noise floating around the object,
nudges each of them towards something that looks like a real grasp over many small
steps, and then has a second network score what came out. That is a diffusion
model, and the
[six-degree-of-freedom page](01_six-dof-grasps.md#56-graspgen-and-graspgenx-the-models-that-ask-which-gripper-you-have)
describes the same machinery for finger grippers. Because no step is per-pixel,
the answer is not limited to the camera's grid, and a cup pose can be offered for
a face the camera only saw at a glancing angle.

Where the cup itself lives is in the labels, and the repository shows it. The code
that made the suction data models the rim as a ring of points pressed onto the
object's surface and checks whether all of them touch, which is the same kind of
compliant model Dex-Net 3.0 introduced, and the radius of that ring is the 30
millimetres in the checkpoint's file name. Nothing in a trained model can be
adjusted to fit a different cup afterwards, which is why the correction two
paragraphs below works on the object rather than on the model.

What the design buys is one answer form for cups and fingers, so a cell that might
use either can call one library and compare the two scores, and a cup you can name.
What it costs is many passes of the network for one answer, where a map costs one,
plus the segmentation step before any of it. On an arm, that pays off in a cell
that sometimes wants fingers instead of the cup. Dex-Net 4.0 is the only other
model here that will make that choice for you, and it makes it for a cup you cannot
identify, under terms from a different university; GraspGen makes it for a cup
whose radius is written on the file.

You would pick it rather than SuctionNet-1Billion because of the cup. SuctionNet
and Dex-Net both hide their cup inside the weights, so you cannot tell whether
their score applies to your hardware. GraspGen names its cup and its README gives
a correction: scale the object's points by your radius divided by 0.030 before
running inference, so a 45 millimetre cup means scaling by 1.5. That is a rough
correction rather than a retrained model, but it is the only one on offer.

What it costs you beyond the line above is an admission in the README. It says the
suction checkpoint was released without the on-generator training the finger models
received, so its scores may be worse than its own method allows; on-generator
training means the scorer was trained on the generator's own output, and without it
the scorer has not seen the mistakes this generator makes. The licence's section
3.3 is the other decision worth reading, because it limits use to research or
evaluation while permitting NVIDIA itself to use the work commercially. The
thing that most often goes wrong is giving it a whole scene, because these
models expect one segmented object's points.

GraspGen runs from its own scripts rather than from an importable function.

```bash
# GraspGen runs from its own demo scripts, inside its container.
# --gripper_config is what picks suction rather than a two-finger gripper.
python scripts/demo_object_pc.py \
  --sample_data_dir /models/sample_data/real_object_pc \
  --gripper_config /models/checkpoints/graspgen_single_suction_cup_30mm.yml
```

The scripts give you the diffusion sampler, the scorer and a viewer. What you
supply is the segmentation that cuts one object out of the scene, the rescaling
above if your cup is not 30 millimetres, and the move from the camera's frame into
the robot's. The name of the configuration file is itself the point here. The two
finger checkpoints beside it are called `graspgen_franka_panda.yml` and
`graspgen_robotiq_2f_140.yml`, so you can always read off which gripper a GraspGen
answer was computed for.

### 5.4 AffordanceNet, the one the affordance papers measure against

**AffordanceNet is historical.**

Size not stated, the size of the weights not stated, a graphics card old enough to
build Caffe against, and no licence from the authors at all.

Thanh-Toan Do, Anh Nguyen and Ian Reid published it in 2017, in the
[AffordanceNet paper](https://arxiv.org/abs/1709.07326). It has two branches that
run together: one finds each object and draws a box around it, and the other gives
every pixel inside that box its most likely affordance label. The paper reports
150 milliseconds per picture, which was fast enough for a robot at the time.

The one idea is to find the object first and label its parts inside it. The
affordance question is asked once per object rather than once per picture, and
that ordering is the whole design.

Inside, it is Faster R-CNN with a different mask on the end. A proposal step offers
boxes, a detection branch says what each box contains, and in place of the usual
single mask per object an affordance branch gives every pixel inside the box its
most likely job out of the list it was trained on. The paper names three parts that
make that multi-class mask work: a sequence of deconvolution layers, which grow the
mask back to size in several steps rather than one jump, a resizing strategy it
calls robust, and a loss that trains both branches together.

What asking per object buys is that a label belongs to something. Two mugs touching
each other give two boxes and two handles, so the arm can be told to take the left
one. A plain per-pixel painter such as CLIPSeg in
[section 5.6](#56-clipseg-asking-for-a-part-in-words) returns one blob of
handle-coloured pixels, and nothing in that answer says which mug each pixel came
from. What it costs, besides the fixed list of jobs that the paragraph after next
is about, is the box itself. Every label lives inside a box the detector drew, so
an object the detector missed has no affordances at all, and a part that sticks out
past the edge of its box is cut off there.

On an arm, that shows up on a tray of tools lying across each other. Two
screwdrivers crossing give AffordanceNet two boxes and two handles, while CLIPSeg
gives one mask that covers both handles, and a grasp filtered with it may close on
the wrong tool. The way people fix that today is to run a current instance
segmenter first and keep only the pixels where its mask and CLIPSeg's agree, which
is AffordanceNet's idea rebuilt out of parts that still install. That is the reason
to read this paper rather than to run it.

You would read it rather than install it, and the alternative that explains why is
CLIPSeg in [section 5.6](#56-clipseg-asking-for-a-part-in-words). AffordanceNet can
only ever answer with the affordances it was trained on, because the last layer of
the network has one channel for each of them, and adding one costs new labelled
pictures. CLIPSeg takes the affordance as a phrase you type, so adding one costs
nothing. Once that is available, a list somebody fixed in 2017 is hard to
justify.

What it costs you is unrunnable code and an empty licence. It is built on Caffe
and on the 2015 Faster R-CNN code, and its
[repository](https://github.com/nqanh/affordance-net) was last changed in
September 2021. Its `LICENSE` file is worth opening, because it contains
Microsoft's MIT grant for Faster R-CNN and Berkeley's BSD grant for Caffe and
nothing at all from the AffordanceNet authors, so you have permission to use the
code it was built from and no stated permission for the part that does the
affordances, which is the only part you wanted.

There is no code example here, because there is no call to show. The repository
offers a Caffe build and a demo script, and getting Caffe to compile in 2026 is a
larger job than the model is worth. What this sub-section gives you instead is the
reason the papers you read still cite it and the reason you should not start from
it.

### 5.5 Where2Act, affordances for things that move

**Where2Act is historical**, in the useful sense that it defined the problem
rather than that it has been replaced.

Size not stated, no packaged weights to download, an NVIDIA card and the SAPIEN
simulator, and no licence file at all.

Kaichun Mo and others published it in 2021, in the
[Where2Act paper](https://arxiv.org/abs/2101.02692). It asks a different
question from every other model on this page: not "will a grip hold" and not "what
is this part for", but "if I push or pull here, will anything move". It learned
the answer by poking simulated doors, drawers, lids and switches and recording
which pokes moved something.

The one idea is that the label is the result of an action rather than a name.
Nobody tells this network what a part is for. The robot pushes and pulls in a
simulator, records whether anything moved, and that recording is the label. An
affordance, here, is simply whatever made something move.

Inside, the repository's network has a point cloud backbone from the PointNet++
family and three heads, and its own code names them. `ActionScore` gives each
point one number for how likely any action is to work there. `Actor` turns
random numbers into a gripper orientation for that point, so it proposes
directions instead of choosing from a list. `Critic` takes a point together with
a proposed orientation and predicts whether the action would succeed. One
network is trained for each kind of action, such as pushing or pulling. Next to
AffordanceNet, where the output is a label out of a fixed list, there is no list
of part names anywhere in this model; the output is a score attached to an
action and to a direction.

What that buys is an answer the arm can act on, which is where to push, which way
to push, and how likely it is to work, and labels that cost no human time, so more
data means more simulator hours rather than more hand labelling. What it costs is
that the simulator is part of the training loop rather than the source of a
dataset, because the paper's sampling strategy chooses what to try next from what
the model currently believes, so you cannot train this from a folder of pictures.
Everything it learned is also about the simulator's articulated objects.

On an arm, the difference from AffordanceNet is a cupboard door. AffordanceNet
labels the door "grasp", and the robot still does not know which way it swings.
Where2Act answers "pull here, in this direction", which is the whole of what the
arm needs. But the published work answers for the simulator's doors, and a real
drawer has friction, a catch and a handle the simulated one does not, so what you
take from this project is the design and the training loop rather than a model.

You would pick it rather than an affordance model such as AffordanceNet when your
objects have moving parts. AffordanceNet labels a cupboard door "grasp" and stops
there, which does not tell a robot which way the door opens. Where2Act predicts,
for every pixel and for a given action such as pushing or pulling, how likely that
action is to work there, and it predicts the direction too.

What it costs you is that there is nothing packaged to install. Its
[repository](https://github.com/daerduoCarey/where2act) was last changed in August
2023 and has **no licence file at all**, so default copyright applies and you have
no permission to use it. It is training code plus the simulator the authors used,
and its results are results in simulation. The thing that most often goes wrong is
expecting it to transfer to a real kitchen, because a real drawer has friction, a
catch and a handle that the simulated one does not.

There is no short code example for Where2Act either, for the same reason as
AffordanceNet. Read the paper, and expect to train your own version on your own
objects, which is what the work building on it does.

### 5.6 CLIPSeg, asking for a part in words

**CLIPSeg is the most used in 2026 of the models in this section that will give
you part labels.**

Size m, a laptop, and Apache-2.0 for the code and the weights. It is the only
model in this section whose parameter count is published at all.

Timo Lüddecke and Alexander Ecker published it in 2021, in
[Image Segmentation Using Text and Image Prompts](https://arxiv.org/abs/2112.10003).
It is not an affordance model and it was not trained on affordances. You give it a
picture and a phrase, and it paints the pixels that match the phrase, so "the
handle of the knife" is a question you can simply ask.

The one idea is to replace the fixed list of output channels with a sentence. In an
affordance network the last layer has one channel for each job, and that layer is
the list. CLIPSeg has a single output channel whose meaning is set by the phrase
you type.

Inside, the picture goes through CLIP's image encoder and the phrase goes through
CLIP's text encoder, which turns the phrase into one vector. A small transformer
decoder then reads the image encoder's activations from a few of its layers and
grows them back into a map, and the phrase's vector enters by multiplying and then
adding to the decoder's numbers at each step. In the published code those two
operations are layers called `film_mul` and `film_add`, and the trick is called
feature-wise modulation, which means one vector is used to scale and shift another
layer's numbers. So the phrase does not choose a channel. It changes what the
decoder is looking for. The last layer gives one channel, which is why the answer
is one map per phrase, and why the code below repeats the same picture once for
every phrase.

What that buys is a new part for the price of a sentence instead of a dataset.
What it costs comes from the same place. There is no list, so there is nothing for
a phrase to fail to match against, and the model has no way of reporting that your
words described nothing in the picture. And because the decoder grows the image
encoder's patch grid by a fixed factor, rather than up to the size of the picture
you handed in, the answer always comes back the same size; the costs paragraph
below says what that means in practice.

On an arm, this is the difference on the day a new tool arrives. With AffordanceNet
you would be labelling pictures of your own knives before the robot could hold one
by the handle. With CLIPSeg you type "the handle of the knife", get a mask, and keep
only the grasps whose finger contacts land inside it, and when the next tool arrives
you type its name instead. What you give up is any guarantee that the mask means
something, which is the cost the rest of this sub-section is about.

You would pick it rather than AffordanceNet because the list of jobs stops being
fixed. AffordanceNet's list of affordances was decided in 2017, and extending it
costs new labelled pictures. CLIPSeg's jobs are whatever you type, and you can
change them between one picture and the next. The
[open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
page explains how models of this kind work.

What it costs you is accuracy on parts, and this is a real cost rather than a
caution. CLIPSeg was trained on whole objects far more than on parts, so "the
handle" works better than "the blade", and much better than "the part that is safe
to hold". It also returns a confident-looking map when nothing matches, and the map
alone does not tell you that. The thing that most often goes wrong is the output
size, because the model answers at 352 by 352 pixels whatever size you gave it, so
a mask resized up from that is rough at the edges.

It is in Hugging Face `transformers`, which is the package that holds most
published research models behind one set of class names.

```python
import torch
from transformers import AutoProcessor, CLIPSegForImageSegmentation

model_id = "CIDAS/clipseg-rd64-refined"
processor = AutoProcessor.from_pretrained(model_id)
model = CLIPSegForImageSegmentation.from_pretrained(model_id)

# One phrase per part you want. The same picture is repeated once per phrase.
texts = ["the handle of the knife", "the blade of the knife"]
inputs = processor(text=texts, images=[image] * len(texts),
                   padding=True, return_tensors="pt")

with torch.inference_mode():
    logits = model(**inputs).logits        # shape (2, 352, 352), one map per phrase

handle = torch.sigmoid(logits[0]) > 0.5    # turn scores into a true-or-false mask
```

The library gives you the model, the weights and the text encoder, and nothing had
to be trained. What you supply is the phrases, the resize from 352 by 352 back to
your picture's size, and a check that the answer means anything. The cheapest such
check is to compare the best phrase's score with the next best and refuse when
they are close. Then you use the mask by keeping only the grasps whose finger
contacts land inside it.

### 5.7 How to choose

For suction, do not start with a model at all. Fit flat patches to the depth
picture, reject the patches that are too curved or too small for your cup, and
rank what is left by area and by distance from the nearest edge. Book 3's
[suction models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#6-suction-models)
section reports that it takes about a dozen lines of code and performs about as
well as a model. It also runs on a laptop and raises no licence question.

For affordances, start with CLIPSeg, because it is the only model in this section
that installs cleanly, carries a clear licence, and is not limited to a list
somebody decided years ago. Use it to make a mask, then filter a grasp model's
candidates with that mask, rather than expecting CLIPSeg to choose a grasp.

Three things change those two answers.

If the suction geometry keeps choosing badly on lumpy bags, on tight clutter, or
on surfaces that look flat and leak, add a suction model. Use Dex-Net if you want
a policy you can call and can accept an old Python and research-only terms. Use
GraspGen's suction checkpoint if your cup is not 30 millimetres and you can
rescale for it. Use SuctionNet-1Billion if you are publishing a number.

If your objects have moving parts, no model here is ready to install, and
Where2Act is the paper to read before you build what you need.

If you have a small, known set of tools, write the rule instead of using any model
here. "Hold a knife by
the handle" is cheaper and more reliable written down than learned.

---

## 6. Where this is going

This section is about the direction suction and affordance models are moving in. It is
written on 4 October 2026, and it borrows the vocabulary Book 3's frontier chapter uses
for
[the four kinds of claim](../../../03_frameworks/08_frontier/06_what-is-coming.md#1-four-kinds-of-claim-and-why-the-difference-decides-everything),
because the difference decides how much weight a sentence can carry. A demonstration is a
recording of something working once under conditions the publisher chose. A product
announcement says a thing can be bought or downloaded, and you can go and check, which
makes it the most useful kind. A research result is a measured number under a stated
protocol. A projection is about a date that has not arrived, and it is the weakest. Every
claim below says which kind it is, and where the judgement is mine the sentence says so.

### How it got here

The two halves of this page moved in opposite directions. Suction prediction started as a
physics calculation about a seal and a twisting force, became a learned per-pixel score
trained on that same physics, and has largely gone back to geometry with a segmentation
model in front of it. Affordance went the other way, from a fixed list of part names
drawn on photographs by hand to a phrase you type. Both moves had the same cause: the
hand-made part of the system was the part that did not generalise.

### Where it is used in industry today

This is the one page in this book whose subject runs at scale, for money, today. Every
large warehouse picking system named below holds the item with a suction cup. Amazon's
[Cardinal](https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center)
lifts a parcel "with air suction", and its
[Vulcan](https://www.aboutamazon.com/news/operations/amazon-vulcan-robot-pick-stow-touch)
picks with "an arm that carries a camera and a suction cup"; Amazon states Vulcan can
handle about 75 per cent of the types of item it stores, and that it will be added to
sites in Europe and the United States "over the next couple of years".
[Sparrow](https://www.aboutamazon.com/news/operations/amazon-introduces-sparrow-a-state-of-the-art-robot-that-handles-millions-of-diverse-products)
is Amazon's item-level picking arm, and Amazon does not state its gripper. Boston
Dynamics' [Stretch](https://bostondynamics.com/stretch/) unloads shipping containers with
an array of cups, and in May 2025 it and DHL
[signed an agreement covering more than 1,000 further robots](https://bostondynamics.com/news/dhl-signs-mou-for-additional-1000-robot-deployment/),
with DHL reporting unloading rates of up to 700 cases per hour. Those are product
announcements with company-reported numbers attached.

Two deployments matter more than the rest, because of what they say about
[section 5.7](#57-how-to-choose). Ocado's
[On-Grid Robotic Pick](https://www.ocadogroup.com/newsroom/stories/ocado-robotic-arms)
arm packs grocery bags with a single suction cup, and Ocado says it picked over 30
million items with it in 2024 and
[expects it to reach "more than 70% of an extensive online grocery range"](https://www.ocadogroup.com/newsroom/news/kroger-rolls-out-new-technology-enhancements-with-ocado-group)
at full capacity. An interview with its researchers describes
[a 3D vision system that finds grasp points "big enough, flat enough and horizontal enough for the suction cup to attach to"](https://www.imveurope.com/feature/automating-grocery-shopping),
and calls it "a model-free approach". That is the geometric flat-patch method section 5.7
recommends, running in a working grocery warehouse. The other is
[Ambi Robotics](https://www.ambirobotics.com/), founded by Ken Goldberg and Jeff Mahler,
two of the authors of the Dex-Net work in
[section 5.1](#51-the-dex-net-suction-models-30-and-40). Its AmbiSort parcel sorter runs
software descended from Dex-Net, and
[Pitney Bowes expanded its deployment across its United States hubs](https://www.robotics247.com/article/pitney_bowes_to_deploy_ambisort_ai_powered_robots_in_e_commerce_network).
So both of the suction approaches on this page have a company behind them.

Suction rarely runs alone. RightHand Robotics'
[RightPick](https://www.righthandrobotics.com/products/rightpick) grips with "three
compliant fingers and suction" and claims more than 1.2 million production picks a month,
and [Plus One Robotics](https://www.plusonerobotics.com/automated-parcel-induction) and
[Dexterity](https://www.dexterity.ai/) sell parcel handling of the same shape. For
affordance models the industrial picture is empty, and that is the honest answer. I could
find no company shipping an affordance model and no deployment of anything like
AffordanceNet or Where2Act. What does ship is open-vocabulary segmentation used as a
filter, which is what [section 5.6](#56-clipseg-asking-for-a-part-in-words) describes.

### What is being worked on right now

The papers below come from an arXiv search of the computer science categories for
"suction" and for "affordance" in the abstract, sorted by date and run on 4 October 2026,
so you can repeat it and see what has arrived since.

The first thread is giving the cup a sense of whether it is actually holding anything.
[CLAP](https://arxiv.org/abs/2609.32767), from September 2026, taps a pressure module
into the vacuum line, feeds the reading into the policy in place of the suction command,
and uses it to abandon an action already under way. Its stated reason for doing this is
the sharpest sentence written about suction this year: at the moment it matters, the cup
and the face it is holding hide each other from the camera, so vision cannot answer the
question. That is a research result. The same thread is appearing in hardware, with
[FlexiCup](https://arxiv.org/abs/2511.14139) and
[SuckTac](https://arxiv.org/abs/2511.02294) building cups that see and feel what they are
pressed against.

The second thread is suction without a suction model at all, and it is the one with
measured numbers. A July 2026 system called [Seg2Grasp](https://arxiv.org/abs/2607.17757)
splits bin picking into segmentation, then suction points from surface normals, then
open-vocabulary classification, and argues explicitly that end-to-end learning falters on
unfamiliar objects. An August 2026 paper on
[sorting deformed beverage cartons](https://arxiv.org/abs/2608.28246) goes further and
uses no training at all: a vision-language model finds the cartons from a text prompt,
[SAM 2](https://github.com/facebookresearch/sam2), the second version of Meta's Segment
Anything Model, turns each detection into a mask, and a geometric score combines flatness
with surface direction to pick the point. On a real robot across 35 cluttered scenes it
reports 88.2 per cent single-object grasp success and 72.6 per cent end-to-end retrieval
in clutter. Read the protocol before carrying those numbers anywhere: the objects are one
product type at three levels of deformation, not a mixed bin.

The third thread is the affordance half catching up with the rest of computer vision.
[UniAfford](https://arxiv.org/abs/2609.37264), from September 2026, is one model for both
2D and 3D affordance prediction, with a dataset that pairs pixel-level and point-level
labels under a single taxonomy. The problem it names is the one
[section 5](#5-well-known-models) exposes: 2D and 3D affordance work grew up as separate
problems with different datasets and evaluation protocols, so nothing transfers between
them.

The fourth thread is hardware that holds things both ways, with a policy that knows which
tool it is using. [VacuumVLA](https://arxiv.org/abs/2511.21557) drives suction and
gripping from one policy, and the
[Everything-Grasping gripper](https://arxiv.org/abs/2510.04585) and
[Suction Leap-Hand](https://arxiv.org/abs/2509.20646) put cups on fingers. This is the
research side of what RightHand Robotics already sells.

### What is still unsolved

Suction hides the problem rather than solving it, and this is the most important sentence
on the page. A cup works when an item has one reachable face that is roughly flat, clean
and airtight, and the warehouses where suction works are warehouses whose items are
packaged for shipping and therefore mostly have such a face. The boundary is visible in
the vendors' own numbers. Amazon says Vulcan handles about 75 per cent of item types.
Ocado expects more than 70 per cent of its range. RightHand Robotics sells a Suction Cup
Swapper whose stated benefit is making "roughly 1.5x as many orders 100% robot pickable",
which is a company telling you how many orders one cup could not finish. The remaining
items are not a slightly harder version of the same problem. They are the finger-grasping
problem of [six-degree-of-freedom grasps](01_six-dof-grasps.md), untouched, and a better
suction score does not move the boundary one item, because what fails is the shape of the
object rather than the quality of the prediction.

Picking unseen items from a cluttered bin at a rate a business will pay for is therefore
still not solved, and the industry's answer is to put a person back in the loop. Plus One
Robotics sells remote human supervision as a named product feature, so somebody elsewhere
can take over when a robot is stuck. That is an honest engineering decision and it is
also a measurement: a product built around human intervention is a product whose author
does not expect autonomy to be enough.

The smaller unsolved things are worth naming. A suction score is a prediction about an
event the model cannot observe, which is why CLAP exists, and
[SuctionNet-1Billion](#52-suctionnet-1billion-the-current-suction-benchmark) scores
against labels a physics model produced rather than against picks, so no number on this
page is picks per hour. Depth cameras still return nothing where a glass jar or a shiny
foil tray was, which breaks a flat-patch method and a learned model equally. Affordance
has no benchmark anybody agrees on, no model in [section 5](#5-well-known-models) with a
licence a company can use, and nothing shipped for objects with moving parts.

### The next two to three years

Everything in this part is my expectation rather than anybody's announcement, and the
reason matters more than the prediction.

I expect the learned suction scorer not to come back, and the shipped shape to stay a
segmentation model plus geometry plus a pressure sensor. Three independent things point
the same way: Ocado's description of its own vision system, the measured numbers from the
training-free carton work, and Seg2Grasp's argument that modular beats end-to-end on
unfamiliar objects. The reason underneath all three is cost. The geometric method is a
dozen lines, runs on a laptop, raises no licence question and fails in ways an engineer
can see, and no published suction model beats it by enough to pay for the rest.

I expect the cup to be instrumented before the model is improved, and this is the
prediction I hold most firmly. The reason is that the failure which matters is a seal
that leaks, that failure is directly observable with a pressure tap in the vacuum line,
and it is not observable from a camera at the moment of contact. A sensor that answers
the question costs less than a model that guesses at it. CLAP is a research result today,
and my expectation is that reading the vacuum line becomes ordinary in commercial end
effectors.

I expect end effectors that combine a cup with fingers to become the default rather than
an upgrade. The reason is the boundary above. An order is only finished when every line
in it is picked, so the last item decides what the cell is worth, and nobody can sell
"about 75 per cent of item types" to a customer whose orders mix freely. RightHand
Robotics already ships fingers and suction together, and the research has started writing
policies that know which tool they hold.

I expect affordance to become a prompt into a general segmentation model, and dedicated
robot affordance datasets to stop being the route to a product. The reason is that
[CLIPSeg](#56-clipseg-asking-for-a-part-in-words) and SAM 2 install cleanly under
permissive licences and need no training, the carton work above already uses exactly that
stack, and a part vocabulary somebody fixed years ago cannot cover a warehouse. UniAfford
is the honest counter-case, so the fair prediction is that the dedicated work continues
in research while products use the promptable segmenter and a written rule.

I do not expect a suction model you can buy that states your cup. GraspGen is the only
one on this page that names its cup radius at all, and its licence forbids commercial
use. Nobody has announced a commercially licensed suction model, and the companies who
could publish one sell whole picking cells, so publishing it would give away the part
they charge for. That is a structural reason rather than a technical one, and structural
reasons hold.

---

## 7. Where to read next

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
