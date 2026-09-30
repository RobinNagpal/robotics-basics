# 3D models: an overview

This chapter is about neural network models that work in three dimensions. The
last chapter, [seeing models](../02_seeing-models/01_overview.md), worked on flat
pictures. The models in this chapter work on 3D points and whole scenes instead.
This page says what they are for, which question each kind answers for a robot
arm, and how they connect to the rest of the book.

It is for a reader who has read the first chapter,
[what models are](../01_what-models-are/01_what-a-model-is.md). You should know that
a model takes some numbers in and gives some numbers out, and that it learns from
examples. You do not need to know anything about 3D maths. The page starts by
explaining the one new idea that the whole chapter uses: the point cloud.

## Contents

1. [What a point cloud is](#1-what-a-point-cloud-is)
2. [What 3D models are for](#2-what-3d-models-are-for)
3. [The question they answer](#3-the-question-they-answer)
4. [The four kinds in this chapter](#4-the-four-kinds-in-this-chapter)
5. [Comparing the four kinds](#5-comparing-the-four-kinds)
6. [How 3D models connect to the other chapters](#6-how-3d-models-connect-to-the-other-chapters)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What a point cloud is

A normal camera takes a photo. A photo is a flat grid of small coloured squares,
called **pixels**. Each pixel says what colour something is. It does not say how far
away that thing is. A photo of a mug on a table tells you that the mug is there, but
not whether it is 30 cm away or 3 m away.

A **depth camera** is a camera that also measures distance. For each pixel, it
reports how far away the surface in that pixel is. Book 2 explains how depth cameras
do this, in [the sensors document](../../02_perception/02_object-perception/02_sensors.md).

Once you know the direction of a pixel and the distance along it, you know one spot
in the room. That spot can be written as three numbers:

- `x`, how far it is to the side,
- `y`, how far it is forwards,
- `z`, how high it is.

These three numbers are called a **point**. Do this for every pixel, and you get a
large collection of points. This collection is called a **point cloud**. The word
"cloud" only means that the points are scattered in space, with no fixed order and
no lines joining them.

![A photo of a mug next to the point cloud of the same scene](../../images/3d-models/overview/what-a-point-cloud-is.svg)

The photo on the left is a grid of colours. The point cloud on the right is a list
of places, and each place is three numbers in metres.

A point cloud has three features that matter for the rest of this chapter.

- It only has points where the camera could see a surface. The back of the mug has no
  points, because the camera never saw it.
- The points have no order. Point number 1 in the list could be on the mug or on the
  table. Swapping two rows of the list changes nothing about the scene.
- A typical depth camera gives tens of thousands of points or more in one shot. The
  camera in Book 2's project gives one point per pixel, and it has 76,800 pixels
  ([the one-box project](../../02_perception/01_camera/03_one-box-intro.md)).

A robot arm wants points more than pixels. A pixel is a direction. A point is a
place, and the gripper has to go to a place.

---

## 2. What 3D models are for

A **3D model** in this book is a neural network that takes 3D information in, or
gives 3D information out, or both. The information is usually a point cloud, or a
set of photos taken from known places around a scene.

The programmed methods in Book 2 already do some 3D work without any learning. They
can find the flat table in a point cloud and cut it away. They can group the points
that are left into separate objects
([programmed methods, section 1.6](../../02_perception/02_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster)).
Those methods only use distances between points. They cannot say that a group of
points is a mug, or that a part of it is the handle. They cannot say what the side
facing away from the camera looks like.

3D models fill those gaps. They learn from many examples what 3D shapes usually look
like, and they use that to name points, guess hidden parts, rebuild a whole scene,
or attach meaning to places in 3D.

---

## 3. The question they answer

For a robot arm, every model in this chapter answers some version of one question:

> **What is where, in 3D, around the arm, including the parts I cannot see yet?**

The arm needs the answer in 3D because its gripper moves in 3D. A box drawn around a
mug in a photo is not enough to pick the mug up. The arm also needs to know how far
away the mug is, how wide it is, and where its handle points.

---

## 4. The four kinds in this chapter

This chapter has four pages after this one. The picture shows the question each kind
answers, all about the same mug.

![Four kinds of 3D model, each answering one question about a mug](../../images/3d-models/overview/four-questions.svg)

Each panel shows one kind of model and the question it answers about the same mug.

- [Point cloud models](02_point-cloud-models.md) take a point cloud and say what it
  is, or which object each point belongs to. PointNet is the best-known one.
- [Shape completion](03_shape-completion.md) takes the points of the side the camera
  saw and guesses the hidden back of the object.
- [Scene reconstruction](04_scene-reconstruction.md) takes many photos from known
  places and builds a whole 3D scene that can be viewed from any direction. NeRF and
  Gaussian splatting are the two best-known methods.
- [3D feature maps](05_3d-feature-maps.md) build a 3D map in which every point also
  carries meaning, so the arm can ask "where is the handle?" in words.

---

## 5. Comparing the four kinds

The table puts the four kinds side by side. Read each row across to see what goes
into that kind of model, what comes out, and how it is usually trained.

| Kind | What goes in | What comes out | How it is trained |
| --- | --- | --- | --- |
| Point cloud models | one point cloud | a name for the cloud, or a name for every point | once, on many labelled point clouds |
| Shape completion | the points of the seen side | the points of the whole object | once, on many complete 3D shapes |
| Scene reconstruction | many photos, and where each was taken | a 3D scene you can view from anywhere | fitted again for every new scene |
| 3D feature maps | photos or point clouds, and a trained image model | a 3D map where each point carries meaning | usually no new training; it borrows an image model |

The next table says when a robot arm reaches for each kind. Read it as "if you need
this, use that".

| If the arm needs to... | use |
| --- | --- |
| know which points are the mug and which are the table | a point cloud model |
| grasp an object from a side the camera cannot see | shape completion |
| see a shiny or see-through object that a depth camera misses | scene reconstruction |
| find "the red cup" or "the handle" from a spoken or typed request | a 3D feature map |

The last row of the first table matters. Point cloud models and shape completion are
trained once and then used on new objects. Scene reconstruction is different. A NeRF
or a Gaussian splat is fitted to one scene, and it has to be fitted again when the
scene changes. The [scene reconstruction page](04_scene-reconstruction.md) explains
why.

---

## 6. How 3D models connect to the other chapters

The book lists seven families of model. Each one has a one-line job:

1. Seeing models turn a picture into names, boxes, outlines, poses or depth.
2. 3D models work on 3D points and whole scenes instead of flat pictures.
3. Grasp models decide where and how to hold an object.
4. Movement models decide how the arm should move, moment by moment.
5. Language models understand words, and connect words to pictures and actions.
6. World models predict what will happen next if the arm does something.
7. Touch and body models make sense of touch, force and the arm's own body.

3D models sit between seeing and grasping. They take in from one side and give out to
the other.

- They take from [seeing models](../02_seeing-models/01_overview.md). A depth model
  from [depth from pictures](../02_seeing-models/06_depth-from-pictures.md) can turn a
  plain photo into a point cloud. An outline from
  [segmentation](../02_seeing-models/04_segmentation.md) can pick out which points
  belong to one object. 3D feature maps lift the numbers of an
  [open-vocabulary model](../02_seeing-models/07_open-vocabulary-models.md) into 3D.
- They give to [grasp models](../04_grasp-models/01_overview.md). Most grasp models
  that choose a full 3D grasp take a point cloud as input, and many of them are built
  on a point cloud model inside. See
  [six-DOF grasps](../04_grasp-models/03_six-dof-grasps.md).
- They give to [movement models](../05_movement-models/01_overview.md). Some policies
  take a point cloud of the scene as their input instead of a photo.
- They give to [language models](../06_language-models/01_overview.md). A 3D feature
  map is one way to turn "the cup on the left" into a place the arm can reach.
- [World models](../07_world-models/01_overview.md) can predict how points will move
  when the arm pushes something. That is the same kind of input, used to look ahead.

The [map of models](../01_what-models-are/06_the-map-of-models.md) shows all seven
families on one page.

---

## 7. Where to read next

Start with [point cloud models](02_point-cloud-models.md). The other three pages in
this chapter build on its idea of a model that reads points directly.

If you want the deeper, non-learned side of 3D first, Book 2 covers it:

- [The one-box project](../../02_perception/01_camera/03_one-box-intro.md) makes a
  point cloud from a depth camera, step by step.
- [Programmed methods](../../02_perception/02_object-perception/03_programmed-methods.md)
  finds objects in a point cloud without any model.
- [Models that measure](../../02_perception/02_object-perception/05_models-that-measure.md)
  compares 3D reconstruction methods by how accurate they are, and lists their
  licences.
