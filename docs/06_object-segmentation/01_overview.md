# Finding the object: detection and segmentation

A robot that is going to pick something up has to answer two questions before it
moves. **What is this thing**, and **which part of the picture is it on**. This
document is about answering both. It covers every family of technique that is in
real use, the frameworks that implement them, the models you can download today,
the models you would train yourself, and — for each one — where it fits and
where it does not.

Its companion, [object dimension detection](../07_object-dimension-detection/01_overview.md),
takes the answer this document produces and turns it into millimetres. The split
between the two is deliberate and it matters: everything here works in pixels,
and pixels are not a size. A mask that is perfect to the pixel still does not
tell you how wide the object is.

## Who this is for, and what it is for

This is written for someone who can picture a robot arm and a camera, has read
the [camera area](../05_camera/01_basics.md) or knows the equivalent, and now has
to choose a perception approach for a real project. You do not need to have
trained a model. Every term is explained where it first appears.

It is written to be *used for choosing*, which shapes it in three ways.

Every technique carries five jobs it suits and five it does not. That is more
useful than a score, because almost every technique in this field works well on
the demonstration its authors chose, and the interesting question is always
which job is the one it quietly fails at.

Every licence is named, because licences here are not a formality. The most
popular object detector in the world is published under a licence that makes it
unusable in a commercial product without paying, and a great many tutorials do
not mention this.

Everything says whether it runs on a Mac. A large part of this field assumes an
NVIDIA graphics card, and finding that out after two days of setup is a common
and avoidable waste.

## Contents

1. [Four answers, and which one you need](#1-four-answers-and-which-one-you-need)
2. [What you know before the robot looks](#2-what-you-know-before-the-robot-looks)
3. [Closed set, open vocabulary, and promptable](#3-closed-set-open-vocabulary-and-promptable)
4. [Techniques that do not learn anything](#4-techniques-that-do-not-learn-anything)
5. [Models you can download](#5-models-you-can-download)
6. [Models you would train yourself](#6-models-you-would-train-yourself)
7. [Frameworks and libraries](#7-frameworks-and-libraries)
8. [Datasets](#8-datasets)
9. [Labelling tools](#9-labelling-tools)
10. [Licences, and the one that will catch you out](#10-licences-and-the-one-that-will-catch-you-out)
11. [What runs on an Apple Silicon Mac](#11-what-runs-on-an-apple-silicon-mac)
12. [Putting it in ROS 2](#12-putting-it-in-ros-2)
13. [The comparison grid](#13-the-comparison-grid)
14. [What to actually reach for](#14-what-to-actually-reach-for)
15. [Where to read more](#15-where-to-read-more)

---

## 1. Four answers, and which one you need

People say "the robot sees the object" as though seeing were one thing. It is
four, and they are different jobs with different costs. The picture below shows
all four applied to the same mug, with what each one is worth to a gripper.

![The four shapes an answer can take](../images/object-segmentation/overview/four-answers.svg)

**Classification** says what is in the picture and nothing about where. It is the
oldest of the four and the least useful on its own, because a robot cannot reach
for "somewhere".

**Detection** gives a rectangle around the object, usually with a confidence
score. The rectangle is axis-aligned, which means that for anything long and
turned at an angle, a large part of what is inside the rectangle is not the
object. For a mug standing alone on a table that hardly matters. For a screwdriver
lying diagonally it matters a great deal.

**Segmentation** gives the pixels themselves. There are three kinds of it, and
mixing them up is the most common confusion in this whole area:

- **Semantic segmentation** labels every pixel with a class. Every mug pixel is
  labelled "mug". If two mugs touch, they come back as one region, because
  nothing in the answer distinguishes them.
- **Instance segmentation** labels every pixel with a class *and* which object it
  belongs to. Two touching mugs come back as two regions. This is nearly always
  what a robot needs, because a robot picks up one thing at a time.
- **Panoptic segmentation** is both at once: every pixel gets a class, and
  every countable thing also gets an instance. It matters for scene
  understanding and rarely for a table-top arm.

**Pose** gives position and orientation — six numbers, usually called 6-DoF, for
six degrees of freedom: three for where the object is and three for which way it
is turned. This is the only one of the four that tells you which way up something
is, and it is the only one that generally needs a model of the object in advance.
It belongs to the [dimension document](../07_object-dimension-detection/01_overview.md),
where it is covered properly.

The practical rule is that you should pick the cheapest of the four that answers
the question your next step actually asks. A great deal of effort goes into
producing masks for robots that would have been perfectly happy with a box.

| The answer | What it gives you | Enough to... | Not enough to... |
| --- | --- | --- | --- |
| classification | a label | sort pictures | reach for anything |
| detection | a box and a label | reach for one object on a clear table | grip round an odd shape, or measure it |
| instance segmentation | the pixels of each object | measure the outline, avoid a handle, tell touching objects apart | know which way up it is |
| 6-DoF pose | position and orientation | put it down the right way up, fit it into something | measure an object you have no model of |

## 2. What you know before the robot looks

The single best predictor of which technique you should use is not how hard the
scene looks. It is how much you know about the object before the robot ever sees
it. The table below reads from the top down, from knowing the most to knowing the
least, and the work goes up as you go down.

![Choosing by what you know in advance](../images/object-segmentation/overview/what-you-know.svg)

Most projects that get into trouble here have reached for the bottom row when
they were really in the top two. The bottom row is what papers are written
about, so it is what people read about first.

## 3. Closed set, open vocabulary, and promptable

Trained models split into three kinds by what you are allowed to ask them for,
and the difference is not accuracy. It is what happens to an object nobody
thought of in advance.

![A fixed list of classes against a model you can ask for anything](../images/object-segmentation/overview/closed-vs-open.svg)

A **closed-set** model was trained on a fixed list of classes and can only ever
return one of them. Trained on the eighty classes of COCO, it knows "cup" but has
never heard of a beaker, a wing nut, or a brake caliper. Ask it about one and it
does not come back wrong — it comes back empty, which in a robot cell reads as
"there is nothing there".

An **open-vocabulary** model takes a description in words and finds whatever
matches. You type "the glass beaker" and it looks for one. Nothing was trained on
beakers; the model has learned a shared space of pictures and words, so a phrase
it has never seen still lands somewhere sensible. The cost is that the wording is
now part of your system. "Bottle", "water bottle" and "the clear plastic bottle"
can give three different answers, and nothing warns you.

A **promptable** model does not name anything at all. You give it a point, a box
or a rough scribble, and it returns the exact region containing that. Segment
Anything is the famous one. It is extraordinarily good at the boundary and
completely silent on the label, so on its own it cannot start a robot pipeline —
something has to decide where to click. In practice it is paired with a detector
that produces boxes, and the pair does what neither does alone.

| | What you give it | What comes back | Fails when |
| --- | --- | --- | --- |
| closed-set | a picture | one of N fixed classes | the object is not one of the N |
| open-vocabulary | a picture and a phrase | whatever matches the phrase | the phrase is ambiguous, or your object has no common name |
| promptable | a picture and a point or box | the region around that point | nothing tells it where to point |

## 4. Techniques that do not learn anything

These are the methods that have no model behind them. You write the rule, the
computer applies it. They are unfashionable and they are still the right answer
surprisingly often, for three reasons that no learned method matches: they run in
about a millisecond, they need no training data, and when they fail you can work
out exactly why by looking at one number.

All of them are in [OpenCV](https://github.com/opencv/opencv), which is the standard computer
vision library, published under the [Apache 2.0
licence](https://github.com/opencv/opencv/blob/4.x/LICENSE) and free to use in a
commercial product. The point-cloud ones are in
[Open3D](https://www.open3d.org/) ([MIT
licence](https://github.com/isl-org/Open3D/blob/main/LICENSE)) or the [Point
Cloud Library](https://pointclouds.org/) ([BSD-3
licence](https://github.com/PointCloudLibrary/pcl/blob/master/LICENSE.txt)).

### 4.1 A colour range

**What it is.** You state which colours count as the object, and every pixel in
that range is kept. Almost always done in HSV — hue, saturation and value —
rather than in red, green and blue, because in HSV the *colour* is one number and
the *brightness* is a separate one, so a shadow across a red block changes the
value and leaves the hue alone. In RGB a shadow changes all three.

**What it costs.** Nothing to install beyond OpenCV, nothing to train, about a
millisecond a frame, and roughly six numbers to tune. It is the fastest route
from no perception to some perception that exists.

**Why this rather than a model.** If the object is genuinely one strong colour
against a background that is not, a model is a great deal of machinery to arrive
at the same answer more slowly and less predictably.

The camera area works a real example end to end in
[finding an object by colour](../05_camera/02_finding-objects.md#3-finding-it-by-colour).

Five jobs it suits:

- a coloured part on a conveyor, under factory lighting that does not change
- fiducial markers and coloured tape used deliberately as targets
- a simulator, where colours are exactly what you set them to
- separating one known object from a background you control, such as a light box
- a first version, built in an afternoon, to find out whether the rest of the
  pipeline works at all

Five jobs it cannot do:

- anything the same colour as its surroundings — a white mug on a white table
- anything whose colour is not the point, such as "find the screws", where screws
  come in every finish
- scenes under daylight, where the colour of everything moves through the day
- telling two objects of the same colour apart when they touch, since they merge
  into one region
- transparent or mirrored objects, which have no colour of their own at all

### 4.2 Background subtraction

**What it is.** You learn what the empty scene looks like, then call anything
that differs from it an object. The usual implementations model each pixel's
history as a mixture of Gaussians — `MOG2` in OpenCV — or by nearest neighbours,
`KNN`, both documented in the [background subtraction
tutorial](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_video/py_bg_subtraction/py_bg_subtraction.markdown).

**What it costs.** A fixed camera, and a period at the start where the scene is
empty. Both are usually free in a robot cell and both are fatal if you do not
have them.

**Why this rather than a colour range.** It does not care what colour the object
is. It only cares that the object was not there before, which for a cell where
parts arrive is exactly the right question.

Five jobs it suits:

- a fixed overhead camera watching a workspace where parts arrive and leave
- detecting that a human has entered a cell, as a safety trigger
- finding items on a conveyor against a belt that is always the same
- counting things that pass through a frame
- picking out the one thing on a table that moved since the last picture

Five jobs it cannot do:

- anything with a camera on the robot's wrist, because the background moves with it
- a scene that is never empty, so there is nothing to learn as background
- distinguishing the object from its own shadow, which also differs from the
  background
- lighting that changes, which the model slowly accepts as the new background
- an object that arrives and then stays still for a long time, which is gradually
  absorbed into the background and disappears

### 4.3 Edges, contours and connected components

**What it is.** Three related steps. Edge detection, usually
[Canny](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_canny/py_canny.markdown), marks where
brightness changes sharply. [Contour
finding](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_contours/py_contours_begin/py_contours_begin.markdown)
traces those edges into closed outlines. [Connected
components](https://github.com/opencv/opencv/blob/4.x/samples/cpp/connected_components.cpp)
numbers the separate blobs in a mask so you can treat each as an object.

Connected components in particular is the step that turns "these pixels are
object" into "these are object number one and those are object number two", and
it is needed after almost every other method in this section.

**What it costs.** Very little, but edge methods have thresholds that are
sensitive to contrast, and contours only close properly when the outline is
unbroken. A single gap in an edge lets the contour leak out into the background.

Five jobs it suits:

- separating a mask into one region per object, after colour or depth found the
  pixels
- flat parts on a plain background, such as gaskets or sheet-metal blanks
- printed markers, labels and anything with a strong printed boundary
- measuring an outline once you already know which blob is the object
- checking whether two things are touching, by seeing whether they are one blob

Five jobs it cannot do:

- textured objects, which are full of internal edges that look just like the
  outline
- low-contrast scenes, where the object's edge is not the strongest edge present
- objects that overlap, where the outline of one runs into the other
- anything where you need a *label* — edges tell you where something is and never
  what it is
- cluttered scenes, where the number of contours explodes and none of them is
  clearly the object

### 4.4 Template matching

**What it is.** You keep a small picture of the object and slide it over the
scene, scoring how well it matches at every position. The best-scoring position
is where the object is. OpenCV's [template matching
tutorial](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_template_matching/py_template_matching.markdown)
covers the basic form, and the shape-based industrial version is what commercial
libraries such as [MVTec HALCON](https://www.mvtec.com/products/halcon) sell.

**What it costs.** Speed, as soon as the object might be rotated or at a different
distance: you have to search over rotations and scales as well as positions, and
the cost multiplies. It is also brittle in exactly one way that surprises people —
it matches appearance, so a change of lighting can break it even when nothing
moved.

**Why this rather than a trained detector.** For a single rigid part, always the
same way up, on a production line, template matching is more accurate, needs no
training data at all, and its failures are predictable. This is what a great deal
of real factory vision still is.

Five jobs it suits:

- one rigid part, always presented the same way up, on a machine that repeats
- printed-circuit inspection, finding a known component at a known place
- locating a fiducial or a logo for alignment
- finding a tool in a tool holder, where the holder fixes the orientation
- any job where you have exactly one example of the object and no ability to
  collect more

Five jobs it cannot do:

- objects that vary in shape between instances, such as fruit, or mine, or a
  hand-made part
- objects at unknown rotation and scale, unless you can afford to search all of
  them
- deformable things: cable, fabric, bags, anything that drapes
- scenes where lighting changes, since the template encodes the lighting it was
  captured under
- partially hidden objects, where most of the template has nothing to match against

### 4.5 Watershed and GrabCut

**What it is.** Two classical algorithms for splitting a region properly once you
roughly know where it is.
[Watershed](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_watershed/py_watershed.markdown) treats
the image as a landscape and floods it from markers you supply, which is the
standard way to split a clump of touching objects into individual ones.
[GrabCut](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_grabcut/py_grabcut.markdown) takes a
rough box around the object and refines it into an accurate outline by modelling
the colours inside and outside.

**Why this rather than a promptable neural model.** These are the ancestors of
Segment Anything, and they do the same job: turn a rough hint into a precise
boundary. They are worse at it and they are a thousand times cheaper, need no
model file, and run anywhere.

Five jobs they suit:

- splitting touching objects of the same colour, which watershed was designed for
- cleaning up a rough box into a usable mask, on a machine with no GPU
- counting objects in a clump — grains, pills, coins
- a preprocessing step before measurement, where the boundary has to be tight
- offline labelling, where a human supplies the hints

Five jobs they cannot do:

- running unattended, since both need markers or a box from somewhere
- objects whose colour statistics match the background, which defeats GrabCut
- scenes with soft or blurred boundaries, where the flood spills over
- giving any kind of label or identity
- reflective and transparent objects, whose apparent colour comes from elsewhere
  in the room

### 4.6 Point clouds: remove the plane, then cluster

**What it is.** The classic recipe for a table-top robot, and still the most
reliable thing in this document. Take the depth picture as a cloud of 3D points.
Find the biggest flat surface in it and delete it — that is the table. Group what
is left into clumps of nearby points. Each clump is an object.

The plane is found by [RANSAC](https://pointclouds.org/documentation/tutorials/planar_segmentation.html),
which means random sample consensus: pick three points at random, make the plane
through them, count how many other points lie on it, keep the best after a few
hundred tries. Clustering is usually [Euclidean cluster
extraction](https://pointclouds.org/documentation/tutorials/cluster_extraction.html)
in PCL or [DBSCAN](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html)
in Open3D.

The [tools and libraries doc](../08_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
shows this recipe as real code.

**Why this rather than anything learned.** It works on objects it has never seen,
which no closed-set model does. It gives you 3D positions directly, in metres,
which is what the arm needs. It has no training data and no licence problem. For
"pick up whatever is on this table", it is still the default in industry.

**What it costs.** A depth camera. And it tells you nothing whatever about what
the objects *are*.

Five jobs it suits:

- bin picking and table clearing, where identity does not matter and geometry does
- any object the robot has never seen, including objects that do not exist yet
- finding the work surface itself, which almost every other step then needs
- checking whether two objects are touching, in 3D rather than in the picture
- producing a first estimate of an object's size and position, ready for the
  [dimension document](../07_object-dimension-detection/01_overview.md)

Five jobs it cannot do:

- naming anything, which is the whole of the "what is it" question
- objects lying flat against the surface, which get deleted along with the plane
- objects that touch each other, which cluster into one
- transparent and shiny objects, which produce no depth points to cluster
- scenes with no dominant plane, such as a cluttered shelf or a pile

### 4.7 The depth hole, for glass and chrome

**What it is.** Not so much a technique as a fact worth exploiting. A depth camera
returns nothing where a transparent object is, because the light goes through it
or is bent aside by the curved surface. So the depth picture has a hole in the
shape of the glass, while the colour picture shows it perfectly well. A hole in
the depth, with something visible through it in colour, is a transparent object.

This sounds like a trick and it is not. It is the same signal a real depth camera
gives, and a pipeline built on it meets the same difficulty a real one does. The
[glass-picking case study](../09_one-arm-training/07_case-study/01_place-glass.md)
is built on exactly this.

**What it costs.** It finds transparency, not identity, and it needs the object to
be in front of something the camera can see.

Five jobs it suits:

- glassware handling: bars, laboratories, dishwashers, bottling
- detecting that a transparent object is present at all, which most methods miss
- flagging regions the depth data cannot be trusted on, before something else
  uses them
- separating glass from opaque clutter, which colour cannot
- a cheap check on a specular metal part, which produces the same missing readings

Five jobs it cannot do:

- work against a background the camera also cannot see, such as a glass on a
  mirror
- distinguish a glass from a hole, a dark absorbing surface, or the edge of the
  camera's range
- tell one glass from another
- give the size of the glass, which needs a side view and a measurement
- work with a sensor that fills in missing depth automatically, which many
  cameras now do by default and which quietly destroys the signal
