# Segmentation

This page explains segmentation, which means models that mark the exact pixels of
each object in a picture instead of drawing a box around it. It answers five
questions: what a segmentation model does, what the difference is between its two
main kinds, how it works inside, how it is trained, and why a robot arm often needs
an outline rather than a box.

It is written for a reader who has already read the pages on
[image classification](../03_also-used/01_image-classification.md) and
[object detection](01_object-detection.md), because those pages explain pixels,
scores, the backbone, fine-tuning, boxes and confidence, and this page uses those
words without explaining them again.

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
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

A **segmentation model** is a model that gives an answer for every single pixel of
a picture, because for each pixel it says what that pixel belongs to.

The answer for a whole picture is called a **mask**, and a mask is a second picture
of the same size as the photo. In the mask, each pixel holds a class or an object
number instead of a colour. So you can think of it as the photo with every object
painted in its own flat colour.

Here is an everyday example: imagine a colouring book page, and a child who colours
every mug blue, every bottle green and the table brown, staying inside the lines.
Once they finish, every part of the page has one colour, and that colour says what
the part is. A segmentation model produces the same kind of result from a photo.

The difference from a detector is the level of detail, because a detector says
"there is a mug inside this rectangle", while a segmentation model says "these
exact pixels are the mug". So the pixels outside the mug's edge are not mug, even
when they lie inside the rectangle.

---

## 2. What goes in and what comes out

The input is one camera picture, exactly as it is for a detector, but the output is
one or more masks rather than boxes. There are two main kinds of segmentation, and
they give different outputs.

### Semantic and instance segmentation

**Semantic segmentation** gives every pixel a class, so it says "this pixel is
mug", "this pixel is table" and "this pixel is wall". However, it does not tell one
mug from another, which means two mugs standing side by side become a single "mug"
area.

Instead, **instance segmentation** gives each separate object its own mask, so it
says "these pixels are mug 1" and "these pixels are mug 2". Each object is called
an **instance**, and the background, such as the wall and the table, is usually
left out.

The picture below shows the same photo with both kinds of answer.

![A photo, its semantic segmentation and its instance segmentation](../../../images/seeing-models/segmentation/semantic-and-instance.svg)

In the middle panel, both mugs share one colour, because they are the same class.
In the right panel, each mug has its own colour, because each of them is a separate
object.

A third kind, **panoptic segmentation**, does both at once, since it gives every
pixel a class and also separates the objects, and the word "panoptic" itself means
"seeing everything".

A robot arm that picks objects usually needs instance segmentation, because it has
to pick one particular mug rather than "the mug area". Semantic segmentation is
more useful for questions about places, such as which part of the picture is table,
where the free space is, or which pixels are a person who has walked into the cell.

An instance segmentation model gives a list with one item per object, and each item
has the object's class, a confidence and a mask. Most models also give the object's
box, since the box is easy to work out from the mask.

### Why an outline and not a box

A box holds the object, but it also holds whatever happens to be around the object.
The picture below compares a box and a mask for one mug.

![A box includes wall, table and the handle gap; a mask includes only the mug](../../../images/seeing-models/segmentation/box-and-mask.svg)

In the left panel, the striped pixels are inside the box but are not part of the
mug, and for a mug with a handle that is a large part of the box. In the right
panel the mask covers only the mug, and it also shows the gap inside the handle,
which a box cannot show at all.

For a robot arm, this matters in three ways.

- The middle of the mask is the middle of the mug, while the middle of the box is
  pulled towards the handle.
- The depth pixels inside the mask all belong to the mug, whereas the depth pixels
  inside a box include the table behind it. So a mask gives much cleaner 3D points
  for the object.
- The mask shows the shape, so the program can find the handle, the rim or the
  narrowest part, and then choose where the fingers go.

---

## 3. How it works inside

Those two kinds of output are produced in two different ways, so there are two main
ways to build a segmentation model. The first is usual for semantic segmentation,
while the second is usual for instance segmentation.

### Shrink, then grow back

A classifier's backbone makes the grid of numbers smaller and smaller, because that
is how it learns what is in the picture. But a mask must be as big as the photo,
with one answer per pixel, so a semantic segmentation model adds a second half that
makes the grid big again.

1. The first half is a normal backbone, which shrinks the picture step by step. At
   each step the grid gets smaller, and each number carries more meaning, so this
   half is called the **encoder**.
2. The second half grows the grid back, step by step, until it is the size of the
   photo again, and this half is called the **decoder**.
3. At each step of the decoder, the model copies in the grid of the same size from
   the encoder. The small grids know what is in the picture, while the large grids
   from the encoder still know exactly where the edges are, so joining them gives
   an answer that is both right about the class and sharp at the edges. These
   copies are called **skip connections**.
4. At the end, each pixel gets one score per class, and the pixel takes the class
   with the highest score, just as a classifier does for a whole picture.

The picture below shows the idea on a tiny 8 by 8 picture.

![The picture shrinks to find what is there, then grows back to say which pixel is which](../../../images/seeing-models/segmentation/shrink-then-grow.svg)

The left grid is the photo, the small grey grids in the middle are the encoder's
and decoder's numbers, and the right grid is the mask, where each pixel is either
mug or not mug. The orange arrows are the skip connections. Once the model is drawn
this way, it looks like a letter U, which is where the U-Net model got its name.

### A detector with a mask added

For instance segmentation, the most common way is to start from a detector and then
add a mask to each box.

1. A detector finds the boxes, as on the [object detection](01_object-detection.md)
   page.
2. For each box, the model cuts out the matching part of the backbone's grids.
3. A small extra network, called the **mask head**, looks at that cut-out part, and
   gives a small mask, often 28 by 28, that says which pixels inside the box are
   the object.
4. The small mask is then stretched to the size of the box in the photo.

Because each box gets its own mask, two mugs that touch still get two separate
masks, and this is exactly how Mask R-CNN works.

Newer models use a transformer instead, in the same way as the detection
transformers on the object detection page. So each query gives one object, and each
object comes with a mask rather than only a box, which is how Mask2Former works.
This means one such model can do semantic, instance and panoptic segmentation.

---

## 4. How it is trained

Whichever of those two ways a model is built, it learns from pictures where a
person has marked the exact outline of every object. However, that is much
slower than drawing boxes. For each object, the person clicks many points around
its edge to trace a shape, and that shape is called a **polygon**. So a picture
with ten objects can take several minutes to label, where boxes would take less
than one.

Two public collections of labelled pictures are used most often.

- **COCO**, the same collection used for detectors, also has an outline for every
  labelled object. So most instance segmentation models you can download were
  trained on it, with its 80 classes.
- **ADE20K** is used for semantic segmentation instead, because it labels whole
  scenes, such as kitchens and offices, with 150 classes of things and places,
  including "wall", "floor" and "table".

Training works in the same way as it does for a detector. Then the model gives
its masks for a batch of pictures, and a program compares every pixel of each
mask with the traced outline. It counts how many pixels are wrong, and nudges
the network's numbers to reduce that count. While doing so, it also checks the
classes and the boxes, as for a detector.

A robot project usually fine-tunes, so it starts from a model trained on COCO
and trains it on a few hundred of its own pictures. To save labelling time, most
labelling tools now use a model to trace the outline. So the person clicks once
on the object, a promptable model such as SAM draws the outline, and the person
only fixes its mistakes. SAM itself is covered on the [open-vocabulary
models](03_open-vocabulary-models.md) page, and Book 2 lists such tools in
[labelling
tools](../../../02_perception/02_object-perception/04_models-that-find.md#5-labelling-tools).

Pictures from a simulator help even more for segmentation than they do for
detection, because the simulator knows which object each pixel belongs to, so it
produces perfect masks for free.

---

## 5. Well-known models

It helps to see the models named so far side by side, and these are all real
segmentation models. The first two are the ones this page has already described.

- **U-Net** came out in 2015 for pictures of cells under a microscope, and it gave
  good masks from very few training pictures. Its shrink-then-grow shape, with skip
  connections, is now used in many other models.
- **Mask R-CNN** is an instance segmentation model from Facebook AI Research, from
  2017, and it adds a mask head to the Faster R-CNN detector. It is well understood
  and easy to fine-tune, and it is part of the PyTorch library.
- **DeepLab** is a family of semantic segmentation models from Google, and it looks
  at the picture at several scales at once, which helps it get both large areas and
  small objects right.
- **Mask2Former** is a transformer model from Meta, and one design of it does
  semantic, instance and panoptic segmentation.
- **YOLO segmentation models** are versions of the YOLO detectors that also give a
  mask for each box. They are fast, so they are the easiest way to get masks from a
  live camera.
- **SAM**, the Segment Anything Model from Meta, from 2023, is a different kind,
  because it does not have a list of classes at all. You click on an object, or draw
  a rough box, and it gives the object's exact outline. It was trained on over one
  billion masks, and it is covered fully on the
  [open-vocabulary models](03_open-vocabulary-models.md) page.

Book 2's [models that find
objects](../../../02_perception/02_object-perception/04_models-that-find.md#12-mask-models)
lists mask models with their licences.

---

## 6. Where it is used on a robot arm

The clearest way to see what those masks buy you is a worked example, so here is
one: picking up a mug by its body rather than its handle.

1. A depth camera above the table takes a colour picture and a depth picture.
2. An instance segmentation model, fine-tuned on the lab's mugs, gives a mask for
   each mug.
3. The program chooses one mug, for example the one with the highest confidence.
4. It takes every depth pixel inside that mug's mask, and turns each one into a
   point in 3D, in metres. The result is a small cloud of points that belong only
   to the mug, with no table points mixed in.
5. It finds the handle, which is the thin part of the mask that sticks out to one
   side, and it finds the main body, which is the wide round part.
6. It places the gripper on the side of the body away from the handle, so the
   fingers close across the body and the handle does not get in the way.
7. The arm moves to that pose, closes the gripper and lifts.

A box alone could not do steps 4 to 6, because the box's depth pixels would include
the table, and the box does not show where the handle is.

Other common uses on an arm:

- Picking parts from a bin where they touch and overlap, since instance masks
  separate parts that a box would merge into one.
- Finding the free space on a table, to decide where to put an object down, because
  semantic segmentation marks every "table" pixel.
- Keeping people safe, since semantic segmentation marks every "person" pixel, and
  the arm slows down when any of them appear near it.
- Giving a clean object to the next model, so that a
  [grasp model](../../05_grasp-models/01_overview.md)
  or a [3D model](../../04_3d-models/01_overview.md) can work only on the points
  inside the mask.

---

## 7. What goes wrong

However useful those masks are, segmentation models fail in some of the same ways
as detectors, and in a few ways of their own.

First, the edges are rough, because masks are often a few pixels off at the edges,
and they can cut off thin parts such as a handle or a cable. A few pixels in the
picture can be several millimetres on the object. So the fix is a higher resolution
picture, or a model known for sharp edges. Some projects run SAM on the detector's
box to get a cleaner edge.

Second, touching objects of the same kind merge, so two identical parts pressed
side by side may become one mask, or one part may be split into two. The fix is to
include many such crowded scenes in training.

Third, see-through and shiny objects are hard, because the edge of a glass is hard
to see even for a person, so its mask is often wrong. The fix is to train on many
such pictures, or to add a sensor that sees them better.

Fourth, a mask says nothing about depth or turn, since it gives the pixels
rather than which way the object faces or how far away it is. The fix is to
combine it with a depth camera, a [depth
model](../03_also-used/02_depth-from-pictures.md), or a [pose
model](04_keypoints-and-object-pose.md).

Fifth, unknown objects are missed, just as they are with a detector, because a
model trained on 80 classes finds nothing for an 81st. The fix is fine-tuning, or a
promptable model such as SAM that works on any object.

Finally, it is slower than a detector, because giving an answer for every pixel
costs more work than giving a few boxes. So the fix is a smaller model, a smaller
picture, or running the segmentation model only when the robot needs a precise
outline.

---

## 8. Why segmentation, and what it costs

Now that you have seen what segmentation gives you and where it fails, this section
answers the four questions for it: what it is, what it does for you, why it rather
than the obvious alternative, and what it costs.

It is a network that says, for every pixel, which class or which object that pixel
belongs to. So it gives the robot the exact shape of each object, and clean 3D
points for it when it is combined with depth.

The obvious alternative is an [object detector](01_object-detection.md), which is
faster and whose training pictures are quicker to label. For round or boxy objects
that stand apart, a box is often enough. So choose segmentation when the shape
decides the grasp: a mug with a handle, a tool with a long grip, parts that touch
in a bin, or any object where the box would include a lot of table.

The other alternative is a hand-written rule that finds an area of one colour,
and Book 2 shows this in [finding it by
colour](../../../02_perception/01_camera/02_finding-objects.md#3-finding-it-by-colour).
The colour rule also gives a mask, and it needs no training, but it only works
when each object has a colour nothing else shares, and when the light stays the
same.

The costs are these. Labelling outlines takes several times longer than drawing
boxes, although labelling tools with SAM inside have made this much faster. Then
the models themselves are larger and slower than detectors, so a live camera may
need a graphics card. Finally, a mask is still only a flat shape, which means
the robot still needs depth before it can reach for the object.

---

## 9. The written alternative

A trained network is not the only way to get a mask, because Book 5 makes masks
with written rules instead. [Thresholding and colour
masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
makes a mask from a colour, a brightness or a height above the table. Then
[morphology and the distance
transform](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/02_morphology-and-distance-transform.md)
removes specks, fills holes, and can split parts that touch.
[Clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
then turns the mask, or the depth points above the table, into one piece per
object. The written way wins when each object has a colour or a height that
nothing else shares, because it runs in milliseconds and needs no traced
outlines. The segmentation model wins when objects touch as a matter of course,
when they share colours with the background, or when they vary too much for any
one rule to cover.

---

## 10. Where to read next

- The next page is [keypoints and object pose](04_keypoints-and-object-pose.md),
  which finds named points on an object and which way the object faces.
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

---

## 11. Using it in Python

The page has argued that an exact outline tells a robot more than a box, because
the outline follows the object and the box does not. This section shows the Python
that produces such an outline. After reading it you will be able to get one mask
per object from a photo, and you will know which part of turning that mask into a
grasp is still yours to write.

The quickest way is a YOLO segmentation model, because Ultralytics ships one that
gives a box and an outline together in a single pass.

```python
from ultralytics import YOLO

model = YOLO("yolo11n-seg.pt")           # the "-seg" file adds the mask head
result = model("table.jpg", conf=0.25)[0]

# masks.xy holds one outline per object, as an array of points in picture pixels.
for box, outline in zip(result.boxes, result.masks.xy):
    name = result.names[int(box.cls)]
    centre_u, centre_v = outline.mean(axis=0)
    print(f"{name}: {len(outline)} outline points, "
          f"centre of the outline at ({centre_u:.0f}, {centre_v:.0f})")
```

The same result also holds `result.masks.data`, which is the mask as a grid of true
and false values, one grid per object. That form is the one you want when you need
to pick out the depth pixels that belong to a single object, because you can use it
directly to select from the depth image.

What the pretrained model gives you out of the box is an outline for each of the 80
COCO classes, so a mug on a table is outlined without any training from you. That
saves you the whole of [section 4](#4-how-it-is-trained), and it matters more here
than for a detector, because tracing outlines by hand is the slowest kind of
labelling there is.

What you still have to write yourself is the step from a mask to a place in the
room. You select the depth pixels inside the mask, throw away the ones with no
reading, average the rest into a point in metres, and then work out a direction for
the gripper, for example by fitting a line through the mask to find which way a
long object points. The library gives you the shape in the picture, never the pose
on the table.

What you have to decide is first whether you need an outline at all, because a
detector is faster and simpler when a box is enough. Then you decide the confidence
threshold, as you would for a detector. Finally you decide whether to fine-tune. If
your parts are not among the 80 classes you have to, and the cost of that is real,
because every training picture needs an outline traced round every object rather
than a box drawn round it.
