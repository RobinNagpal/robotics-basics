# Depth from pictures

This page answers one question. How can a model tell how far away things are, when
all it has is ordinary photos? A robot arm needs distances to reach for anything.
A photo alone does not contain them, so this is a harder problem than it first
looks.

It is for a reader who has read the earlier pages of this chapter, and who knows
what a model is from [what a model is](../../01_what-models-are/01_what-a-model-is.md).
It covers three kinds of model. The first guesses depth from one photo. The second
measures depth from two photos taken side by side. The third repairs the holes that
a depth camera leaves on shiny and clear objects.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: picking a glass](#6-a-worked-example-picking-a-glass)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

The one-sentence idea is this. A depth model looks at one or two photos and gives
every pixel a distance from the camera.

You already do this with your own eyes. Close one eye and look at a room. You still
know the chair is nearer than the wall. You know because the chair covers part of
the wall, because the chair looks big, and because you know how big chairs usually
are. Nobody measured anything. You used clues you have learned over your life. A
depth model learns the same kinds of clues from millions of photos.

Now open both eyes. Each eye sees the scene from a slightly different place. Near
things shift a lot between the two views. Far things shift only a little. Your
brain uses that shift to judge distance more precisely. A stereo depth model does
the same thing with two cameras.

There are three kinds of model on this page.

- A **monocular depth** model uses one photo. Monocular means "one eye".
- A **stereo** model uses two photos taken at the same moment by two cameras a
  known distance apart.
- A **depth completion** model takes a depth image that has holes or wrong values
  in it and fills them in, using the colour photo as a guide.

---

## 2. What goes in and what comes out

The output of all three kinds is a **depth map**. A depth map is a picture the same
size as the photo, where each pixel holds a distance instead of a colour. People
usually show it in grey, with near things light and far things dark.

![A photo and its depth map](../../../images/seeing-models/depth-from-pictures/photo-to-depth-map.svg)

The mug is near, so its pixels are light, and the wall is far, so its pixels are
dark.

The inputs differ. The table below shows what each kind of model takes in and what
its output means. Read each row across.

| Kind | What goes in | What comes out | Are the distances in metres? |
| --- | --- | --- | --- |
| Monocular | one colour photo | one distance per pixel | only for some models, and only roughly |
| Stereo | two colour photos, taken side by side | one distance per pixel | yes, if the cameras are measured carefully |
| Depth completion | a colour photo and a depth image with holes | the depth image with the holes filled | yes, because it starts from real measurements |

The last column matters a great deal. Many monocular models give **relative depth**.
Relative depth tells you the order of things: the mug is nearer than the box, and
the box is nearer than the wall. It does not tell you how many metres away anything
is. A model that gives real distances in metres gives **metric depth**.

![Relative depth fits a small scene and a large scene equally well](../../../images/seeing-models/depth-from-pictures/relative-vs-metric.svg)

The same relative answer fits a doll's house and a real kitchen, so relative depth
alone cannot tell the arm how far to reach.

For a robot arm, the depth map is rarely the final answer. The robot turns it into
a **point cloud**. A point cloud is a list of 3D points, one for each pixel, worked
out from the pixel's position and its distance. The [3D models chapter](../../03_3d-models/01_overview.md)
works with point clouds.

---

## 3. How it works inside

### One photo

A monocular model is usually built from two parts. The first part is an
**encoder**. It is a network that turns the photo into a large set of numbers that
describe what is where in the picture. Many recent models use a **vision
transformer (ViT)** as the encoder. A vision transformer cuts the picture into small
square patches and lets every patch compare itself with every other patch. This
helps it use clues from the whole picture at once, such as where the floor meets
the wall.

The second part is a **decoder**. It turns those numbers back into a picture of the
original size, with one distance per pixel.

The model uses clues it learned in training. Things higher in the picture are often
further away. A thing that covers another thing is nearer. Parallel lines, such as
the edges of a table, get closer together as they go away. Known objects, such as
mugs and doors, have typical sizes.

### Two photos

A stereo model follows the shift idea from section 1. The shift of a thing between
the left and the right photo is called **disparity**.

![Two cameras see a near mug shift more than a far box](../../../images/seeing-models/depth-from-pictures/two-cameras-disparity.svg)

The near mug moves a long way between the two pictures and the far box moves only
a little, so the size of the shift tells the distance.

The steps are these.

1. Both photos go through the same encoder, which turns small patches into lists of
   numbers that describe them.
2. For each patch in the left photo, the model compares it with patches along the
   same row in the right photo. The one that matches best shows how far it shifted.
3. A learned network cleans up the matches. It smooths flat areas and keeps sharp
   edges between objects.
4. Simple geometry turns each shift into a distance. The rule is that distance
   equals a fixed number divided by the shift. The fixed number comes from the
   distance between the two cameras and the camera's lens. A big shift means near.
   A small shift means far.

Step 4 is why stereo gives real metres. The model does not guess the scale. It
comes from the measured gap between the cameras.

### Filling holes

A depth completion model gets two inputs: the colour photo and the real depth image
from a depth camera. The depth image is good in most places. On a clear glass or a
shiny spoon it is empty or wrong, because the camera's light passes through the
glass or bounces off the metal.

The model learns to use the good depth around the hole, plus the shape it can see
in the colour photo, to fill the hole. For example, it sees the outline and the
highlights of a glass in the colour photo. It sees the table depth all around the
glass. It fills in the glass as a surface standing on that table.

![A depth hole on a clear glass, and the filled depth](../../../images/seeing-models/depth-from-pictures/glass-depth-hole.svg)

The depth camera returns nothing on most of the glass (red), and the completion
model fills that area with a sensible distance.

---

## 4. How it is trained

A depth model learns from photos paired with the correct depth. Getting that
correct depth is the hard part, and different models use different sources.

- **Depth cameras indoors.** A depth camera records a colour photo and a depth image
  together. The pairs become training examples. This gives real distances, but the
  depth has holes on shiny and dark things.
- **Laser scanners outdoors.** Self-driving car datasets drive a car with cameras
  and a laser scanner, which measures distance with light. The scanner gives
  correct distances for part of each photo.
- **3D films.** Films shot for 3D cinema have a left and a right picture for every
  frame. The shift between them gives relative depth. MiDaS was trained partly on
  pictures like these.
- **Computer-made scenes.** A program renders a 3D scene and knows the exact depth
  of every pixel. This is the main source for stereo models and for clear-object
  models, because real clear objects are so hard to measure.
- **Pictures labelled by another model.** Depth Anything used a large model, trained
  first on labelled pictures, to label millions of unlabelled internet photos. A
  student model then learned from all of them. This is called **pseudo-labelling**:
  the labels come from a model, not from a measurement.

Relative-depth models are trained to get the order right and to ignore the scale.
That lets them learn from many datasets whose units do not agree. It is also why
their output is not in metres.

---

## 5. Well-known models

These are real models. The first four work from one photo, the next two use a
stereo pair, and the last one fills holes.

- **MiDaS** showed that one model trained on many mixed datasets could guess
  relative depth for almost any photo. It is now archived, but many later models
  build on its ideas.
- **Depth Anything**, and its later versions Depth Anything V2 and Depth Anything 3,
  are widely used for relative depth from one photo. Some versions also give metric
  depth. They learned from a very large set of photos with pseudo-labels.
- **Depth Pro**, from Apple, gives metric depth from one photo. It does not need to
  be told the camera's lens settings.
- **Marigold** starts from an image-generating model, the kind that draws a picture
  from a sentence. It retrains that model to draw a depth map of a given photo
  instead. It gives relative depth.
- **RAFT-Stereo** is a stereo model. It improves its guess of the shift for every
  pixel over many small rounds. It is a common, sensible default.
- **FoundationStereo**, from NVIDIA, is a stereo model trained on a very large set
  of computer-made scenes. It works on scenes unlike its training data without
  retraining. Its licence allows research use only.
- **ClearGrasp**, from Google and Columbia University, was made for clear objects.
  It finds the clear objects, their edges and the direction their surfaces face,
  then uses those to fill in the missing depth. It was trained on computer-made
  pictures of glass objects.

The deeper document [models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md#1-depth-from-a-single-picture)
compares these models with their licences and measured accuracy. Its section on
[transparent and shiny objects](../../../02_perception/02_object-perception/04_models-that-find.md#17-transparent-and-shiny-objects)
lists newer depth completion work.

---

## 6. A worked example: picking a glass

The robot must pick up an empty drinking glass from a table. It has a depth camera
on its wrist.

1. The camera takes a colour photo and a depth image. The depth image has a hole
   where most of the glass is. The top of the glass reads as the wall behind it.
2. If the robot used this depth image directly, it would think there was nothing
   there. It would reach through the glass and knock it over.
3. A [segmentation](../02_most-used/02_segmentation.md) model finds the outline of the glass in the
   colour photo.
4. The robot deletes all depth readings inside that outline, because it cannot
   trust any of them.
5. A depth completion model fills in the deleted area. It uses the table depth
   around the glass and the glass's shape in the colour photo.
6. The robot turns the repaired depth into a point cloud. Now the glass appears as a
   solid object standing on the table.
7. A grasp model chooses where to close the gripper. The robot closes the gripper
   slowly, and it checks the grip force, because the repaired depth is a careful
   guess, not a measurement.

A robot without a depth camera could use a stereo pair instead, or a monocular
model. With a monocular model it must fix the scale first. One common way is to
measure a few points in another way, for example the known height of the table,
and stretch the model's answer to match them.

---

## 7. What goes wrong

- **Monocular depth is a guess, not a measurement.** The errors are often several
  centimetres at a distance of one metre. That is too large for a gripper that must
  close around a thin object. People use monocular depth for rough jobs, such as
  telling the foreground from the background, and use real sensors for the final
  measurement.
- **No scale.** A relative-depth answer has no units. The robot must pin it to a
  few real measurements before it can use it.
- **Confident mistakes.** A depth model gives an answer for every pixel, even where
  it has no idea. It does not usually say which pixels it is unsure about. Mirrors
  are a typical case: the model sees the room in the mirror and reports it as a
  room behind the wall.
- **Stereo on plain surfaces.** A plain white wall looks the same everywhere, so
  the model cannot find which patch matches which. Some cameras project a pattern
  of dots onto the scene to give stereo something to match.
- **Stereo up close.** Very close to the cameras, the two views differ too much, and
  some parts appear in only one of them.
- **Filled holes are made up.** A depth completion model draws a sensible surface.
  It may be the wrong surface. A glass lying on its side may be filled in as a
  glass standing up.

---

## 8. Why this kind, and what it costs

This section answers four questions: what these models are, what they do for you,
why you would choose them over the obvious alternative, and what they cost.

Depth models are networks that give every pixel of a photo a distance, from one
photo, from a stereo pair, or from a depth image with holes.

They give the arm distances where it would otherwise have none. That can be
because the robot has no depth camera, because the depth camera fails on a clear or
shiny object, or because the scene is outside, where sunlight can swamp a depth
camera's own light.

The obvious alternative is a depth camera, such as an Intel RealSense. For ordinary
objects on a table, a depth camera is more accurate than any monocular model, needs
no training and costs little. So a depth camera should be the first choice. A
learned stereo model is worth choosing when you want to pick your own cameras, or
work in bright light or at longer range. A depth completion model is worth adding
when the objects are clear or shiny, because a depth camera alone cannot see them.
Monocular depth is worth choosing only when there is truly no second camera and no
depth sensor, or as a rough helper next to one.

The costs are these. Most depth models need a GPU to run at a useful speed.
Monocular depth has errors of centimetres and no reliable scale. Stereo needs two
cameras bolted firmly together and measured carefully, and it gets worse if they
move even slightly. Depth completion invents a surface that may be wrong. And
several of the best models have research-only licences.

---

## 9. Where to read next

- [Keypoints and object pose](../02_most-used/04_keypoints-and-object-pose.md) is the page before
  this one. Most pose models need good depth.
- [Open-vocabulary models](../02_most-used/03_open-vocabulary-models.md) is the next page. It shows
  how to find an object from words before you measure it.
- [Point cloud models](../../03_3d-models/02_most-used/01_point-cloud-models.md) and
  [shape completion](../../03_3d-models/03_also-used/01_shape-completion.md) work on the 3D points a
  depth map turns into.
- [Running a model on a robot](../../01_what-models-are/05_running-a-model-on-a-robot.md)
  explains why a GPU matters and how fast a model must be.
- For the sensors themselves, read
  [the sensors, and the software for each](../../../02_perception/02_object-perception/02_sensors.md).
- For measured accuracy and licences, read
  [models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md).
