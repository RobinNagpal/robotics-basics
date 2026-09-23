# Methods you write yourself

Perception you write rather than download. No model, no training data, no
graphics card: you state the rule and the computer applies it.

These methods are unfashionable and they are the right answer more often than
their reputation suggests, for three reasons nothing learned can match. They run
in about a millisecond. They need no data. And when one fails you can work out
exactly why by looking at a single number, which is not true of a neural network.

The first half is about **finding** the object — which pixels it is on. The
second is about **measuring** it — turning those pixels into millimetres. They
are in one document because they are one job at the keyboard: the same libraries,
the same skills, usually the same afternoon.

Everything here is in [OpenCV](https://github.com/opencv/opencv), which is
Apache-2.0 and free to use commercially, or in
[Open3D](https://github.com/isl-org/Open3D) (MIT) and the
[Point Cloud Library](https://github.com/PointCloudLibrary/pcl) (BSD-3) for the
3D parts.

## Contents

1. [Finding the object](#1-finding-the-object)
2. [Measuring the object](#2-measuring-the-object)

---

## 1. Finding the object

Seven ways to decide which pixels the object is on, without a model. They are
roughly in order of how much they assume: the first needs the object to be one
colour, the last needs only that it is made of glass.

### 1.1 A colour range

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

### 1.2 Background subtraction

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

### 1.3 Edges, contours and connected components

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

### 1.4 Template matching

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

### 1.5 Watershed and GrabCut

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

### 1.6 Point clouds: remove the plane, then cluster

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

The [tools and libraries doc](../07_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
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
  [dimension document](05_models-that-measure.md)

Five jobs it cannot do:

- naming anything, which is the whole of the "what is it" question
- objects lying flat against the surface, which get deleted along with the plane
- objects that touch each other, which cluster into one
- transparent and shiny objects, which produce no depth points to cluster
- scenes with no dominant plane, such as a cluttered shelf or a pile

### 1.7 The depth hole, for glass and chrome

**What it is.** Not so much a technique as a fact worth exploiting. A depth camera
returns nothing where a transparent object is, because the light goes through it
or is bent aside by the curved surface. So the depth picture has a hole in the
shape of the glass, while the colour picture shows it perfectly well. A hole in
the depth, with something visible through it in colour, is a transparent object.

This sounds like a trick and it is not. It is the same signal a real depth camera
gives, and a pipeline built on it meets the same difficulty a real one does. The
[glass-picking case study](../08_one-arm-training/07_case-study/01_place-glass.md)
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

## 2. Measuring the object

Seven ways to turn those pixels into millimetres. Between them they cover most of
what a table-top arm actually needs, they run in microseconds, and — unlike
anything in [models that measure](05_models-that-measure.md) — their failure
modes are ones you can reason about in advance rather than discover.

### 2.1 A known depth, and the two-line calculation

**What it is.** [The one
calculation](01_overview.md#6-the-one-calculation-underneath-everything), applied
directly: take the mask, count its width in pixels, read the depth at the object,
and multiply. This is the baseline every
other method is compared against.

**What it costs.** A depth sensor, and care about *which* depth you read. The
depth at the centre of the object is the front face, not the middle, so an object
50 mm deep measured this way is reported 25 mm too near. For a width measurement
that hardly matters; for a grasp it can.

Five jobs it suits:

- boxes, blocks and flat-faced parts, measured face-on
- any object where a few per cent is good enough
- a first implementation, to find out what accuracy the rest of the system needs
- checking a more elaborate method, since it is easy to get right
- objects large enough that a pixel is a small fraction of them

Five jobs it cannot do:

- small objects far away, where the pixel count is too low to be precise
- transparent or mirrored objects, which return no usable depth
- measuring the dimension pointing away from the camera, which is invisible
- objects seen at an angle, where the apparent width is foreshortened
- anything needing better than about a millimetre with a consumer sensor

### 2.2 The plane the object stands on

**What it is.** Instead of measuring the distance to the object, measure the
distance to the table once, and use the fact that the object is standing on it.
The camera ray through the bottom of the object meets the table at a known point,
which gives the distance, which gives the scale.

**Why this rather than a depth reading.** Because it works on objects the depth
sensor cannot see. A wine glass returns no depth at all, but it stands on a table
that does, so its height and its diameter at every height can be measured from a
plain side-on picture. The [glass case
study](../08_one-arm-training/07_case-study/01_place-glass.md) is built entirely
on this.

**What it costs.** The assumption. If the object is not on the plane — if it is
tilted, stacked on another object, or in the gripper — the answer is confidently
wrong.

Five jobs it suits:

- glassware, and anything else transparent, standing on a surface
- shiny metal parts, which also defeat depth sensors
- any table-top cell, as a cheap check on the depth sensor's answer
- measuring with an ordinary colour camera, with no depth sensor at all
- measuring the height of an object, which is exactly the distance from the plane

Five jobs it cannot do:

- objects held in the gripper, which are no longer on the plane
- stacked or leaning objects
- scenes where the support surface is not flat or not visible
- objects hanging, on a hook or a conveyor
- anything where the plane's own measurement has drifted, which it does if the
  camera is knocked

### 2.3 A marker of known size

**What it is.** Put a printed square of known dimensions in the scene. Because you
know it is, say, 40 mm across and you can see how many pixels across it is, you
have the scale everywhere on that plane. The common families are
[ArUco](https://github.com/opencv/opencv_contrib/tree/4.x/modules/aruco), which
ships with OpenCV's contrib modules under the [Apache 2.0
licence](https://github.com/opencv/opencv_contrib/blob/4.x/LICENSE), and
[AprilTag](https://github.com/AprilRobotics/apriltag), which is
[BSD-2](https://github.com/AprilRobotics/apriltag/blob/master/LICENSE.md) and
generally the more robust of the two at long range and shallow angles. ChArUco is
a chessboard with ArUco markers in the white squares, and is the usual choice for
calibration because it gives many precise corners.

**What it costs.** Somebody has to put the marker there and keep it flat and
clean. A bent or partly obscured marker gives a pose that is wrong in a way that
looks plausible.

Five jobs it suits:

- calibration of every kind, which is where markers earn their keep
- giving a robot a reliable reference frame on a table or a fixture
- scaling a photogrammetric reconstruction, which otherwise has no size at all
- locating a pallet, a tray or a fixture whose contents you then measure
- checking that a camera has not moved, by watching a fixed marker

Five jobs it cannot do:

- measure an object that is not coplanar with the marker, without more geometry
- work when the marker is hidden by the very object you are measuring
- survive a dirty, wet or scratched environment
- operate where you cannot attach anything to the scene, such as a customer's
  goods
- give a good angle estimate from a single small square, which is famously
  unstable near face-on

### 2.4 The smallest rectangle round the mask

**What it is.** Given the object's pixels, `cv2.minAreaRect` finds the smallest
*rotated* rectangle that contains them, returning a centre, a width, a height and
an angle. It is the standard way to get a length, a width and an orientation from
a mask in one call, and it is documented among [OpenCV's contour
features](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_contours/py_contour_features/py_contour_features.markdown).

**Why this rather than the bounding box from a detector.** A detector's box is
axis-aligned, so for anything long and turned it reports a size that belongs to no
real dimension of the object. The rotated rectangle reports the object's own
length and width.

Five jobs it suits:

- long thin parts lying at any angle: screwdrivers, bars, cable segments
- deciding which way to turn the gripper, from the rectangle's angle
- measuring rectangular things, where the fit is exact
- a quick length and width for sorting by size
- anything flat, viewed from directly above

Five jobs it cannot do:

- round objects, where the angle it returns is meaningless noise
- concave shapes, where the rectangle contains a great deal that is not object
- objects seen at an angle, where the rectangle measures the projection
- giving any information about the third dimension
- objects whose mask is broken into pieces

### 2.5 An oriented box round the point cloud

**What it is.** The 3D version of the same idea. Take the object's points, find
the directions they vary along most — which is principal component analysis — and
fit a box aligned to those directions. Open3D does it with
[`get_oriented_bounding_box`](https://www.open3d.org/docs/release/python_api/open3d.geometry.OrientedBoundingBox.html),
and PCL with its [moment of
inertia](https://pointclouds.org/documentation/tutorials/moment_of_inertia.html)
estimator.

**What it costs.** The result is only as good as the points. A camera sees one
side of an object, so the cloud is a shell, and a box fitted to a shell is
systematically too small in the direction pointing away from the camera. Fitting a
box to two views taken from different sides fixes most of this.

Five jobs it suits:

- getting all three dimensions at once, when the point cloud is good
- finding which way a part is lying, for planning an approach
- boxes, cartons and pallets, where the fit is genuinely a box
- feeding a collision model to a motion planner, where a slightly large box is
  safe
- comparing two objects for size without knowing what either is

Five jobs it cannot do:

- measure the hidden side, without a second viewpoint
- fit anything round or irregular tightly — a box round a mug is mostly air
- work on transparent objects, which have no points
- distinguish orientation for a symmetric object, where the axes can swap
  arbitrarily between frames
- work with fewer than a few hundred points, below which the axes are noise

### 2.6 Silhouettes of a solid of revolution

**What it is.** A special case that is worth knowing because it is unreasonably
powerful when it applies. An object made on a lathe or a potter's wheel — a glass,
a bottle, a bearing, a turned leg — is a shape spun about an axis. Its outline
looks the same from every side, and the width of that outline at any height *is*
the diameter there. So one side-on picture gives the complete profile of the
object.

This is the technique the [glass case
study](../08_one-arm-training/07_case-study/01_place-glass.md) is built on, and it
turns "measure this object" into "measure one silhouette".

Five jobs it suits:

- glassware, bottles, cans, cups and jars
- turned and machined parts: bushes, bearings, spacers, pulleys
- measuring a full profile rather than a bounding size, which is what a shaped
  grip needs
- objects a depth sensor cannot see, since only the outline is needed
- inspection, where the profile can be compared against a nominal one

Five jobs it cannot do:

- anything not round: a mug with a handle breaks the assumption exactly at the
  handle
- objects lying on their side, where the axis is no longer vertical
- objects whose silhouette is hidden behind another object
- internal features, which a silhouette cannot show
- telling a solid from a hollow one, which is why the glass study weighs the
  glass instead

### 2.7 Measuring by touching it

**What it is.** Move the gripper until a contact sensor fires, and record where
the arm was. It is the oldest measuring method in robotics and it is still the
most accurate one available to an arm, because it removes the camera from the
chain entirely and leaves only the arm's own repeatability, which on an industrial
arm is a few hundredths of a millimetre.

**Why this rather than a camera.** Because for transparent, mirrored and matt
black objects, touch works and vision does not. And because a contact reading is a
fact about the world, where a camera reading is an inference about it.

Five jobs it suits:

- finding the exact top of a surface before placing something on it
- measuring a feature the camera cannot see, such as the inside of a bore
- glass and polished metal, which defeat every optical method here
- verifying an optical measurement before committing to a delicate action
- establishing the work surface's height at the start of a job

Five jobs it cannot do:

- measure quickly — each touch takes seconds, where a picture takes milliseconds
- measure anything soft, which moves before the sensor fires
- measure an object that is not fixed in place, which slides away
- survey a scene, since you must already know roughly where to touch
- measure anything fragile, which is why the glass study touches only with a
  known, capped force

