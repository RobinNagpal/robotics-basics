# Segmentation

This page explains segmentation: models that mark the exact pixels of each object
in a picture, instead of drawing a box around it. It answers five questions. What
does a segmentation model do? What is the difference between its two main kinds?
How does it work inside? How is it trained? And why does a robot arm often need an
outline rather than a box?

It is for a reader who has read the pages on
[image classification](../03_also-used/01_image-classification.md) and
[object detection](01_object-detection.md). Those pages explain pixels, scores,
the backbone, fine-tuning, boxes and confidence. This page uses those words without
explaining them again.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
   · [Semantic and instance segmentation](#semantic-and-instance-segmentation)
   · [Why an outline and not a box](#why-an-outline-and-not-a-box)
3. [How it works inside](#3-how-it-works-inside)
   · [Shrink, then grow back](#shrink-then-grow-back)
   · [A detector with a mask added](#a-detector-with-a-mask-added)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [Where it is used on a robot arm](#6-where-it-is-used-on-a-robot-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why segmentation, and what it costs](#8-why-segmentation-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

A **segmentation model** is a model that gives an answer for every single pixel of
a picture. For each pixel, it says what that pixel belongs to.

The answer for a whole picture is called a **mask**. A mask is a second picture, the
same size as the photo. In the mask, each pixel holds a class or an object number
instead of a colour. You can think of it as the photo with every object painted in
its own flat colour.

Here is an everyday example. Imagine a colouring book page, and a child who colours
every mug blue, every bottle green and the table brown. The child stays inside the
lines. When they finish, every part of the page has one colour, and the colour says
what that part is. A segmentation model produces the same kind of result from a
photo.

The difference from a detector is the level of detail. A detector says "there is a
mug inside this rectangle". A segmentation model says "these exact pixels are the
mug". The pixels outside the mug's edge, even inside the rectangle, are not mug.

---

## 2. What goes in and what comes out

The input is one camera picture, the same as for a detector. The output is one or
more masks. There are two main kinds of segmentation, and they give different
outputs.

### Semantic and instance segmentation

**Semantic segmentation** gives every pixel a class. It says "this pixel is mug",
"this pixel is table", "this pixel is wall". It does not tell one mug from another.
Two mugs that stand side by side become one "mug" area.

**Instance segmentation** gives each separate object its own mask. It says "these
pixels are mug 1" and "these pixels are mug 2". Each object is called an
**instance**. The background, such as the wall and the table, is usually left out.

The picture below shows the same photo with both kinds of answer.

![A photo, its semantic segmentation and its instance segmentation](../../../images/seeing-models/segmentation/semantic-and-instance.svg)

In the middle panel, both mugs share one colour, because they are the same class.
In the right panel, each mug has its own colour, because each is a separate object.

A third kind, **panoptic segmentation**, does both at once. It gives every pixel a
class, and it also separates the objects. "Panoptic" means "seeing everything".

A robot arm that picks objects usually needs instance segmentation. It has to pick
one mug, not "the mug area". Semantic segmentation is more useful for questions
about places: which part of the picture is table, where the free space is, or which
pixels are a person who has walked into the cell.

An instance segmentation model gives a list, one item per object. Each item has
the object's class, a confidence and a mask. Most models also give the object's
box, since the box is easy to work out from the mask.

### Why an outline and not a box

A box holds the object, but it also holds whatever is around the object. The picture
below compares a box and a mask for one mug.

![A box includes wall, table and the handle gap; a mask includes only the mug](../../../images/seeing-models/segmentation/box-and-mask.svg)

In the left panel, the striped pixels are inside the box but are not part of the
mug. For a mug with a handle, that is a large part of the box. In the right panel,
the mask covers only the mug. It also shows the gap inside the handle, which a box
cannot show.

For a robot arm, this matters in three ways.

- The middle of the mask is the middle of the mug. The middle of the box is pulled
  towards the handle.
- The depth pixels inside the mask all belong to the mug. The depth pixels inside a
  box include the table behind it. So a mask gives much cleaner 3D points for the
  object.
- The mask shows the shape. The program can find the handle, the rim, or the
  narrowest part, and choose where the fingers go.

---

## 3. How it works inside

There are two main ways to build a segmentation model. The first is usual for
semantic segmentation. The second is usual for instance segmentation.

### Shrink, then grow back

A classifier's backbone makes the grid of numbers smaller and smaller. That is how it
learns what is in the picture. But a mask must be as big as the photo, with one
answer per pixel. So a semantic segmentation model adds a second half that makes the
grid big again.

1. The first half is a normal backbone. It shrinks the picture step by step. At each
   step the grid gets smaller, and each number carries more meaning. This half is
   called the **encoder**.
2. The second half grows the grid back, step by step, until it is the size of the
   photo again. This half is called the **decoder**.
3. At each step of the decoder, the model copies in the grid of the same size from
   the encoder. The small grids know what is in the picture. The large grids from the
   encoder still know exactly where the edges are. Joining them gives an answer that
   is both right about the class and sharp at the edges. These copies are called
   **skip connections**.
4. At the end, each pixel gets one score per class. The pixel takes the class with
   the highest score, as a classifier does for a whole picture.

The picture below shows the idea on a tiny 8 by 8 picture.

![The picture shrinks to find what is there, then grows back to say which pixel is which](../../../images/seeing-models/segmentation/shrink-then-grow.svg)

The left grid is the photo. The small grey grids in the middle are the encoder's and
decoder's numbers. The right grid is the mask, where each pixel is either mug or not
mug. The orange arrows are the skip connections. When the model is drawn this way it
looks like a letter U, which is where the U-Net model got its name.

### A detector with a mask added

For instance segmentation, the most common way is to start from a detector and add a
mask to each box.

1. A detector finds the boxes, as on the [object detection](01_object-detection.md)
   page.
2. For each box, the model cuts out the matching part of the backbone's grids.
3. A small extra network, called the **mask head**, looks at that cut-out part. It
   gives a small mask, often 28 by 28, that says which pixels inside the box are the
   object.
4. The small mask is stretched to the size of the box in the photo.

Because each box gets its own mask, two mugs that touch still get two separate masks.
This is exactly how Mask R-CNN works.

Newer models use a transformer, in the same way as the detection transformers on the
object detection page. Each query gives one object, and each object comes with a mask
instead of only a box. Mask2Former works this way. One such model can do semantic,
instance and panoptic segmentation.

---

## 4. How it is trained

A segmentation model learns from pictures where a person has marked the exact outline
of every object. This is much slower than drawing boxes. For each object, the person
clicks many points around its edge to trace a shape. That shape is called a
**polygon**. A picture with ten objects can take several minutes to label, where
boxes would take less than one.

Two public collections are used most.

- **COCO**, the same collection used for detectors, also has an outline for every
  labelled object. So most instance segmentation models you can download were trained
  on it, with its 80 classes.
- **ADE20K** is used for semantic segmentation. It labels whole scenes, such as
  kitchens and offices, with 150 classes of things and places, including "wall",
  "floor" and "table".

Training works as for a detector. The model gives its masks for a batch of pictures.
A program compares every pixel of each mask with the traced outline. It counts how
many pixels are wrong, and nudges the network's numbers to reduce that count. The
program also checks the classes and boxes, as for a detector.

A robot project usually fine-tunes. It starts from a model trained on COCO and trains
it on a few hundred of its own pictures. To save labelling time, most labelling tools
now use a model to trace the outline. The person clicks once on the object. A
promptable model such as SAM, covered on the
[open-vocabulary models](03_open-vocabulary-models.md) page, draws the outline. The
person only fixes its mistakes. Book 2 lists such tools in
[labelling tools](../../../02_perception/02_object-perception/04_models-that-find.md#5-labelling-tools).

Pictures from a simulator help even more for segmentation than for detection. The
simulator knows which object each pixel belongs to, so it produces perfect masks for
free.

---

## 5. Well-known models

These are real segmentation models. The first two are the ones this page described.

- **U-Net** came out in 2015 for pictures of cells under a microscope. It gave
  good masks from very few training pictures. Its shrink-then-grow shape, with skip
  connections, is now used in many other models.
- **Mask R-CNN** is an instance segmentation model from Facebook AI Research, from
  2017. It adds a mask head to the Faster R-CNN detector. It is well understood and
  easy to fine-tune, and it is part of the PyTorch library.
- **DeepLab** is a family of semantic segmentation models from Google. It looks at
  the picture at several scales at once, which helps it get both large areas and
  small objects right.
- **Mask2Former** is a transformer model from Meta. One design does semantic, instance
  and panoptic segmentation.
- **YOLO segmentation models** are versions of the YOLO detectors that also give a
  mask for each box. They are fast, and they are the easiest way to get masks from a
  live camera.
- **SAM**, the Segment Anything Model from Meta, from 2023, is a different kind. It
  does not have a list of classes. You click on an object, or draw a rough box, and
  it gives the object's exact outline. It was trained on over one billion masks. It
  is covered fully on the [open-vocabulary models](03_open-vocabulary-models.md) page.

Book 2's [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md#12-mask-models)
lists mask models with their licences.

---

## 6. Where it is used on a robot arm

Here is a worked example: picking up a mug by its body, not its handle.

1. A depth camera above the table takes a colour picture and a depth picture.
2. An instance segmentation model, fine-tuned on the lab's mugs, gives a mask for
   each mug.
3. The program chooses one mug, for example the one with the highest confidence.
4. It takes every depth pixel inside that mug's mask. It turns each one into a point
   in 3D, in metres. The result is a small cloud of points that belong only to the
   mug, with no table points mixed in.
5. It finds the handle. The handle is the thin part of the mask that sticks out to
   one side. It finds the main body, which is the wide round part.
6. It places the gripper on the side of the body away from the handle. The fingers
   close across the body, so the handle does not get in the way.
7. The arm moves to that pose, closes the gripper and lifts.

A box alone could not do steps 4 to 6. The box's depth pixels would include the table,
and the box does not show where the handle is.

Other common uses on an arm:

- Picking parts from a bin where they touch and overlap. Instance masks separate
  parts that a box would merge.
- Finding the free space on a table, to decide where to put an object down. Semantic
  segmentation marks every "table" pixel.
- Keeping people safe. Semantic segmentation marks every "person" pixel, and the arm
  slows down when any appear near it.
- Giving a clean object to the next model. A [grasp model](../../05_grasp-models/01_overview.md)
  or a [3D model](../../04_3d-models/01_overview.md) can work only on the points inside
  the mask.

---

## 7. What goes wrong

Segmentation models fail in some of the same ways as detectors, and in a few ways of
their own.

The edges are rough. Masks are often a few pixels off at the edges, and they can
cut off thin parts, such as a handle or a cable. A few pixels in the picture can be
several millimetres on the object. The fix is a higher resolution picture, or a model
known for sharp edges. Some projects run SAM on the detector's box to get a cleaner
edge.

Touching objects of the same kind merge. Two identical parts pressed side by side may
become one mask, or one part may be split into two. The fix is to include many such
scenes in training.

See-through and shiny objects are hard. The edge of a glass is hard to see even for a
person. Its mask is often wrong. The fix is to train on many such pictures, or to add
a sensor that sees them better.

A mask says nothing about depth or turn. It gives the pixels, not which way the
object faces or how far away it is. The fix is to combine it with a depth camera, a
[depth model](../03_also-used/02_depth-from-pictures.md), or a
[pose model](04_keypoints-and-object-pose.md).

Unknown objects are missed, as with a detector. A model trained on 80 classes finds
nothing for an 81st. The fix is fine-tuning, or a promptable model such as SAM that
works on any object.

It is slower than a detector. Giving an answer for every pixel costs more work than
giving a few boxes. The fix is a smaller model, a smaller picture, or running the
segmentation model only when the robot needs a precise outline.

---

## 8. Why segmentation, and what it costs

This section answers the four questions for segmentation: what it is, what it does
for you, why it rather than the obvious alternative, and what it costs.

It is a network that says, for every pixel, which class or which object it belongs
to. It gives the robot the exact shape of each object, and clean 3D points for it
when combined with depth.

The obvious alternative is an [object detector](01_object-detection.md). A detector
is faster, and its training pictures are quicker to label. For round or boxy objects
that stand apart, a box is often enough. Choose segmentation when the shape decides
the grasp: a mug with a handle, a tool with a long grip, parts that touch in a bin, or
any object where the box would include a lot of table.

The other alternative is a hand-written rule that finds an area of one colour. Book 2
shows this in
[finding it by colour](../../../02_perception/01_camera/02_finding-objects.md#3-finding-it-by-colour).
The colour rule also gives a mask, and it needs no training. But it only works when
each object has a colour nothing else shares, and when the light stays the same.

The costs are these. Labelling outlines takes several times longer than drawing boxes,
although labelling tools with SAM inside have made this much faster. The models are
larger and slower than detectors, so a live camera may need a graphics card. And a mask
is still only a flat shape: to reach for the object, the robot still needs depth.

---

## 9. The written alternative

Book 5 makes masks with written rules. [Thresholding and colour
masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md) makes a mask from a colour, a brightness or a height above the
table. [Morphology and the distance transform](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/02_morphology-and-distance-transform.md) removes specks, fills
holes, and can split parts that touch. [Clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md) then turns the mask,
or the depth points above the table, into one piece per object. The written way
wins when each object has a colour or a height that nothing else shares: it runs
in milliseconds and needs no traced outlines. The segmentation model wins when
objects touch as a matter of course, when they share colours with the
background, or when they vary too much for one rule.

---

## 10. Where to read next

- The next page is [keypoints and object pose](04_keypoints-and-object-pose.md). It
  finds named points on an object and which way the object faces.
- [Open-vocabulary models](03_open-vocabulary-models.md) covers SAM fully, and models
  that find objects from words.
- [Object detection](01_object-detection.md) explains the detector that Mask R-CNN
  builds on.
- [Grasp models](../../05_grasp-models/01_overview.md) use masks to decide where to hold an
  object.
- [The seeing models overview](../01_overview.md) compares all seven kinds of seeing
  model.
- Book 2 goes deeper in
  [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md),
  which covers mask models and the SAM family with their licences, and in
  [finding an object in a picture](../../../02_perception/01_camera/02_finding-objects.md),
  which builds a colour mask by hand.
