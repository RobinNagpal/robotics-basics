# Shape completion

This page is about models that guess the hidden back of an object, because a camera
only ever sees the side of an object that faces it. A shape completion model takes the
points of that seen side and fills in the rest. So the page answers the three questions below, in that order.
How can a model guess a side it never saw, and what does it need to learn from? And
when should a robot arm trust the guess instead of simply looking again from another
side?

It is for a reader who has read the [chapter overview](../01_overview.md) and
[point cloud models](../02_most-used/01_point-cloud-models.md). You should know what a
point cloud is, and that a point cloud model can turn a cloud into a list of numbers
that describes its shape.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Squeeze, then grow](#squeeze-then-grow)
   · [Three ways to write down the whole shape](#three-ways-to-write-down-the-whole-shape)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: grasping a box from the side](#6-a-worked-example-grasping-a-box-from-the-side)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than looking again, and what it costs](#8-why-this-rather-than-looking-again-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

Since the introduction said the model guesses, this section says what it guesses
from. A shape completion model takes the part of an object that a camera saw and
guesses the whole object.

People do this all the time without noticing it. When you see the front of a mug, you already expect a
round back, a flat bottom and an open top. This is because you have seen thousands of
mugs, so you know what mugs usually look like without walking round this one. A shape
completion model learns the same kind of expectation from thousands of 3D shapes.

The problem it solves is easy to see from above. A depth camera sends out its
measurements in straight lines, and each line stops at the first surface it hits.

![A depth camera sees only the front half of a mug](../../../images/3d-models/shape-completion/camera-sees-one-side.svg)

The lines from the camera reach the front of the mug, so the front has points, while
the back and the handle get no points at all.

So the point cloud of a single object is never a whole object. It is a thin shell over
the half that faces the camera, and often it is less than half, because other objects
stand in the way.

---

## 2. What goes in and what comes out

Because that thin shell is all the model has, what goes in is the point cloud of one
object as the camera saw it. Usually a
[segmentation model](../02_most-used/01_point-cloud-models.md) or an outline from a
[seeing model](../../03_seeing-models/02_most-used/02_segmentation.md) has already cut
this object out of the scene. Many models also want the points moved so that the
middle of the seen points sits at zero, because that makes all inputs look alike in
size and position.

What comes out is the whole object, written down in one of three ways that the next
section describes. The simplest of the three is a new point cloud with points all
over the object, front and back.

![The seen points go in, and the whole mug comes out](../../../images/3d-models/shape-completion/partial-in-complete-out.svg)

The model keeps the blue points it was given and adds the orange points it guessed
for the back and the handle.

---

## 3. How it works inside

### Squeeze, then grow

Most shape completion models have two halves, which are called the **encoder** and
the **decoder**.

1. The **encoder** reads the seen points and squeezes them into one short list of
    numbers. That list describes the shape only in general, such as "a round thing,
    about this wide, with something sticking out on one side". The encoder is usually
    a point cloud model like PointNet, from the
    [previous page](../02_most-used/01_point-cloud-models.md).
2. The **decoder** takes that short list and grows a whole shape from it. It has never
    seen the back of this object, so it only knows what backs usually look like for
    shapes whose front gives this list.

The squeeze in the middle is what makes this work, because the short list has no room
for every point and can only hold the general shape. The decoder then draws that
general shape in full, including the parts that were missing.

Many decoders work in two passes rather than one. The first pass gives a rough cloud of a few hundred
points that shows the overall shape, and the second pass adds detail around each of
those points. This is the same "coarse first, fine later" pattern that PointNet++ uses
in the other direction.

### Three ways to write down the whole shape

As the last section said, there are three common ways for the decoder to write down
the whole object.

- **A point cloud.** The decoder gives a fixed number of points, such as 2,048 or
    16,384, spread over the whole surface, and this is the easiest form to use with
    other point cloud tools.
- **A voxel grid.** Space around the object is cut into small cubes, and the decoder
    says for each cube whether it is inside the object. A grid of 40 cubes along each
    side is already 64,000 cubes, so grids have to stay coarse.
- **A function.** The decoder becomes a small network that answers, for any spot in
    space, whether that spot is inside the object. Some versions answer how far the
    spot is from the surface instead. You can ask about as many spots as you like, so
    the shape has no fixed resolution, and software then finds the surface where the
    answer changes from inside to outside.

The function form is the most detailed of the three. However, the point cloud form is
the most common on robots, because the next step, a grasp model, usually wants
points.

---

## 4. How it is trained

Whichever form the decoder uses, shape completion has one great advantage over other
models in this book. Its training data can be made on a computer, with nobody
labelling anything by hand.

![A full 3D model and the part a camera would see make one training pair](../../../images/3d-models/shape-completion/training-pairs.svg)

The seen part is the question and the whole shape is the right answer, and both come
from the same 3D model.

The training program then does the following for each example.

1. Take a full 3D model of an object from a collection such as ShapeNet, which holds
    many thousands of 3D models of everyday things, made by people in 3D design
    programs.
2. Pick a random viewpoint and pretend a depth camera looks at the model from there,
    keeping only the points that camera would see. Those points are the question.
3. Keep points from the whole surface as the right answer.
4. Show the model the question, and compare its guess with the right answer.
5. Adjust the model a little so that its next guess is closer.

Each 3D model gives many training pairs, one for every viewpoint, so a few thousand 3D
models give hundreds of thousands of pairs.

To compare the guess with the answer, most models use a simple score called the
**Chamfer distance**. For every guessed point, find the nearest point in the right
answer and measure the distance, and then do the same the other way round for every
right-answer point. Add all those distances up, and a small total means the two
clouds lie on top of each other. Training makes this total as small as it can.

Before it is used on a real robot, the model is usually also trained with noise added
to the question points. This is because a real depth camera never gives the clean
points that a computer model does.

---

## 5. Well-known models

All three output forms above appear in real models, and these are the ones that come
up in robot shape completion work.

- **Shape completion for grasping, by Varley and others** (2017), was one of the
    first to use this on a robot arm, and it fills in a voxel grid from one depth view
    and then plans a grasp on the completed shape.
- **PCN**, the Point Completion Network (2018), takes a point cloud and gives a point
    cloud, and it uses the coarse-then-fine decoder described above.
- **PoinTr** (2021) uses attention, the same idea that language models use, to let
    groups of seen points decide which missing groups to add.
- **DeepSDF** (2019) writes the shape down as a function, so that for any spot it
    gives the distance to the nearest surface, with a minus sign for spots inside the
    object.
- **Occupancy Networks** (2019) also use a function, but for any spot they give how
    likely it is that the spot is inside the object.

---

## 6. A worked example: grasping a box from the side

The value of completion is clearest in a case where the hidden part decides the
grasp. An arm has to pick up a closed box from a shelf. The shelf is shallow, so the
gripper has to reach in from the front and close its fingers on the left and right
sides of the box. The camera itself stands in front of the shelf.

The camera therefore sees the front face of the box and a little of each side, and
nothing further back. The picture below compares two ways of choosing where to close
the fingers.

![A side grasp placed using only the seen points, and using the completed box](../../../images/3d-models/shape-completion/grasp-with-and-without.svg)

On the left, the grasp is centred on the seen points and holds only the front edge,
while on the right it is centred on the completed box and holds the box across its
depth.

Here is what happens on the left, without completion.

1. The software takes the average of the seen points as the middle of the box.
2. Almost all the seen points are on the front face, so this "middle" sits just
    behind the front face.
3. The fingers close there and catch only the front edge of the box, so the box tips
    and slips out when the arm lifts.

Here is what happens on the right, with completion.

1. The shape completion model adds the back and the back part of both sides.
2. The middle of the completed box is now in the right place, half way back.
3. The fingers close across the whole depth of the box, so the grasp holds.

Completion helps with a second job as well, because a motion planner needs to know
the whole shape of the object in the gripper. Otherwise it may knock the hidden back
into the shelf on the way out, and the
[learned motion planners page](../../06_movement-models/03_also-used/02_learned-motion-planners.md)
covers that kind of planning.

---

## 7. What goes wrong

That worked example went well, but the completed shape can be wrong in four ways.

**The guess is only a guess.** The model fills the back with what backs usually look
like. So if this mug has a second handle on the far side, or a dent, the model will
not guess it. It draws the most usual shape instead, and it does not tell you where it
is unsure unless it was built to.

**Unfamiliar kinds of object.** A model trained on mugs, bottles and boxes has no idea
what the back of a strangely shaped machine part looks like. So it will draw something
that looks like a shape it already knows.

**Clutter.** If another object hides part of the front too, then the model gets even
less to work from. It may also mix up the edge of the other object with the edge of
this one, if the segmentation was not clean.

**Too smooth.** The decoder often gives rounded, blurry shapes, so thin parts such as
a handle or a rim are the first to get lost.

People deal with these four problems in four matching ways.

- Use the guess only for the hidden part, and keep the real measured points wherever
    there are any. The picture in section 2 does exactly this.
- Ask for several guesses and see how much they disagree, because where the guesses
    differ a lot the arm should be careful.
- Choose a grasp that does not depend much on the hidden part at all.
- Check with touch, because when the fingers close the gripper measures how wide the
    object really is. The
    [touch and body models chapter](../../09_touch-and-body-models/01_overview.md)
    covers this.

---

## 8. Why this rather than looking again, and what it costs

Since the guess can be wrong, the honest question is why guess at all. A shape
completion model **is** a network that guesses the whole shape of an object from one
partial view. It **does** give the arm a full shape to plan a grasp and a path around,
straight away, from one camera shot.

The obvious alternative is to look again, because the arm can move its wrist camera to
the side and behind the object, take more depth shots, and merge the point clouds.
Then there is nothing left for a model to guess at.

So why would anyone guess instead of looking again?

- Looking again takes time, because every extra view means a movement of the arm and
    another shot. In a factory that picks thousands of objects an hour, those seconds
    add up.
- Often the arm cannot look behind at all, since on a shelf, in a bin, or against a
    wall there is no place for the camera to go.
- A fixed camera on a stand cannot move in the first place.

A second alternative is to fit a 3D model you already have. If the arm only ever picks
one known part, then you can store its exact 3D model and match it to the seen points.
Book 2 describes this in
[models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md).
That is more accurate than any guess, but it only works for objects you already have a
model of. Instead, shape completion works for new objects of familiar kinds.

What it costs you comes in the three parts below.

- The back is invented rather than measured, so any grasp or path that depends on it
    can be wrong.
- The model only guesses well for kinds of object that look like its training data.
- It is one more model to run, which takes time on a small computer, though usually
    much less time than moving the arm.

So a good rule is to use completion when you cannot look, and to look when you can
afford it.

---

## 9. The written alternative

No written method can guess the back of a new object, because that guess only comes
from having seen thousands of similar objects. Instead, Book 5 offers three written
ways around the problem. For one known part, [iterative closest
point](../../../05_programming-techniques/03_searching-and-matching/02_most-used/02_iterative-closest-point.md)
lines up the stored 3D model with the seen points, and the model then gives the whole
shape, measured rather than guessed. For a simple shape,
[RANSAC](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md)
fits a cylinder or a plane to the seen points, and the fitted shape covers the hidden
side too. To look instead of guess, [visibility and
next-best-view](../../../05_programming-techniques/06_planning-and-search/03_also-used/03_visibility-and-next-best-view.md)
chooses where to move the camera to see most of what is hidden. So shape completion
wins for new objects of familiar kinds when the camera cannot move.

---

## 10. Where to read next

- [Scene reconstruction](../02_most-used/02_scene-reconstruction.md) is the next
    page, and it covers the "look again" route in full, by building a whole scene from
    many photos.
- [Point cloud models](../02_most-used/01_point-cloud-models.md) explains the encoder
    that most completion models start with.
- [Six-DOF grasps](../../05_grasp-models/02_most-used/01_six-dof-grasps.md) shows the
    grasp models that take the completed points.
- [Models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md) in
    Book 3 goes deeper into grasp models and the data they need.

---

## 11. Using it in Python

The page has explained that a depth camera sees only a thin shell of an object, and
that a completion model guesses the rest. This section is about running that in
Python, and it has to start with an unwelcome fact, because the honest answer here
is different from the one on the detection pages. After reading it you will know
what you can install today, what you cannot, and what the alternative is.

None of the models in [section 5](#5-well-known-models) is a packaged library. PCN,
PoinTr, DeepSDF and Occupancy Networks were all released as research
repositories that accompany a paper, so there is no `pip install pointr` and no
import to write. You clone the repository, install what its own instructions ask
for, and run its script on a checkpoint the authors published. Those checkpoints were
usually trained on ShapeNet, which is a large collection of computer-made 3D models,
so they know chairs, tables and mugs in general and not your parts.

What you can install is the classical way to close a surface over the points you do
have, plus the measure that every one of those papers reports. Open3D does the
first with Poisson surface reconstruction, and PyTorch3D does the second with the
chamfer distance.

```python
import numpy as np
import open3d as o3d
import torch
from pytorch3d.loss import chamfer_distance

seen = o3d.io.read_point_cloud("mug_one_view.ply")
seen.estimate_normals()     # Poisson needs to know which way each surface faces

mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    seen, depth=9)
filled = mesh.sample_points_uniformly(number_of_points=2048)

# How far the guessed shape is from the real one, when you have the real one.
truth = o3d.io.read_point_cloud("mug_all_round.ply")
a = torch.from_numpy(np.asarray(filled.points)).float().unsqueeze(0)
b = torch.from_numpy(np.asarray(truth.points)).float().unsqueeze(0)
print(chamfer_distance(a, b)[0].item())   # mean squared distance, in square metres
```

What those two libraries give you out of the box is real but limited, and the limit
is exactly the point of this page. Poisson reconstruction stretches a surface over
the points it was given, so it closes small gaps and smooths noise, but it cannot
invent the back of the mug because no points there ever suggested one. That is what
a learned model adds, and it is why the learned models exist. The chamfer distance
is genuinely free and is the number to report, because it is what the papers
compare.

What you still have to write yourself is almost all of it, which is the cost of
choosing this kind of model. You clone and run the completion repository, you get
its output into the frame your arm works in, and you decide how much of the guessed
shape to trust when planning a grasp. A sensible rule is to place the fingers only
where the model actually saw points, and to use the completed part of the shape only
to judge whether the gripper will collide.

What you have to decide first is whether to complete the shape at all, which
[section 8](#8-why-this-rather-than-looking-again-and-what-it-costs) weighs against
simply moving the camera and looking from another side. Looking again gives you real
points instead of guessed ones, so completion earns its place only when a second
view is slow or impossible. If you do use it, you also decide which output form
suits you, because a point cloud is easy to handle while a signed distance function
gives a watertight surface that collision checking prefers.
