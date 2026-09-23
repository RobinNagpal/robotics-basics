# Measuring the object: from pixels to millimetres

The [previous document](../06_object-segmentation/01_overview.md) ends with the
robot knowing which pixels the object is on. This one turns that into a size: how
wide, how tall, how deep, and which way it is turned. It covers the sensors, the
geometry, the models you can download, the frameworks, and — for each — where it
fits and where it does not.

The reason this is a separate document, rather than the last paragraph of the
previous one, is a fact that catches almost everybody once. **A picture contains
no sizes.** A perfect mask, correct to the pixel, still does not say whether the
object is seven centimetres across or seventy. Every technique here is a
different way of supplying the missing fact, and knowing which fact you are
supplying is most of the skill.

## Who this is for, and what it is for

This is for someone who has a camera working, can find the object in the picture,
and now has to hand the arm a number in millimetres. It assumes you have read the
[camera area](../05_camera/01_basics.md) or know what the four lens numbers are.
Everything else is explained where it appears.

As with its companion, every technique carries five jobs it suits and five it does
not, every licence is named, and everything says whether it runs on a Mac without
an NVIDIA graphics card.

One more thing shapes this document. Accuracy claims in this field are quoted far
more often than they are met. Where a number appears here, it says what conditions
it was measured under, because "one millimetre accuracy" from a data sheet and one
millimetre on your bench are rarely the same millimetre.

## Contents

1. [Why one picture has no size](#1-why-one-picture-has-no-size)
2. [The one calculation underneath everything](#2-the-one-calculation-underneath-everything)
3. [The three ways to supply the missing fact](#3-the-three-ways-to-supply-the-missing-fact)
4. [Where the millimetres go](#4-where-the-millimetres-go)
5. [Sensors that measure distance](#5-sensors-that-measure-distance)
6. [Geometry you write yourself](#6-geometry-you-write-yourself)
7. [Depth from a single picture](#7-depth-from-a-single-picture)
8. [Stereo matching](#8-stereo-matching)
9. [Pose estimation, when you have a model](#9-pose-estimation-when-you-have-a-model)
10. [Reconstruction, when you do not](#10-reconstruction-when-you-do-not)
11. [Calibration, which decides all of it](#11-calibration-which-decides-all-of-it)
12. [Frameworks and libraries](#12-frameworks-and-libraries)
13. [Datasets and benchmarks](#13-datasets-and-benchmarks)
14. [What runs on an Apple Silicon Mac](#14-what-runs-on-an-apple-silicon-mac)
15. [Putting it in ROS 2](#15-putting-it-in-ros-2)
16. [The comparison grid](#16-the-comparison-grid)
17. [What to actually reach for](#17-what-to-actually-reach-for)
18. [Where to read more](#18-where-to-read-more)

---

## 1. Why one picture has no size

A camera turns directions into pixels. Two objects lying along the same direction
land on the same pixels, whatever their size, as long as the bigger one is
proportionally further away. The picture below is that statement drawn out, using
the repo's own camera.

![Twice as far and twice as big fall on the same pixels](../images/object-dimension-detection/overview/no-scale.svg)

An object 73.6 mm wide at 340 mm and an object 147.2 mm wide at 680 mm both fill
exactly sixty pixels. No amount of image processing separates them, because there
is nothing in the image to separate. The information was lost by the lens, not by
the software.

This has a consequence worth stating plainly, because it is the root of a lot of
wasted effort. **Any method that gives you a size from one ordinary photograph has
assumed something.** Sometimes the assumption is reasonable and stated. Sometimes
it is buried in a trained model that learned, from its training set, that things
which look like mugs are about the size of mugs. That is a useful prior and it is
not a measurement, and the difference shows up the first time you point it at a
doll's-house mug.

## 2. The one calculation underneath everything

Every camera measurement in this document reduces to the same two steps. Divide by
the focal length to turn a pixel count into an angle. Multiply by the distance to
turn an angle into a length.

![Pixels to an angle to millimetres](../images/object-dimension-detection/overview/pixels-to-mm.svg)

In code that is two lines, and the [camera
area](../05_camera/04_one-box-code.md) runs them on a real picture:

```python
size_across = depth / fx          # how many metres one pixel covers, at that depth
width = pixels_across * size_across
```

With the repo's camera, where `fx` is 277.1 pixels, one pixel covers 1.227 mm at
340 mm and 3.609 mm at one metre. Both numbers are worth remembering, because they
set the floor on what you can measure. If your object is 40 mm across at a metre,
it is eleven pixels wide, and a one-pixel error at each edge is an eighteen per
cent error in the answer.

The first step is exact. The second step is where every error in this document
enters, because the distance is itself a measurement.

## 3. The three ways to supply the missing fact

There are only three, and everything else is a variation on one of them.

**Measure the distance.** Use a sensor that reports how far away each pixel is: a
stereo pair, a structured-light projector, a time-of-flight sensor, or a laser
scanner. This is the most direct route and the one most robot cells take. Section
5 is about these sensors and what they actually achieve.

**Know the surface the object sits on.** If the object is standing on a table, and
you know where the table is, then you know the distance to the bottom of the
object without measuring it. This is how the [glass-picking case
study](../09_one-arm-training/07_case-study/01_place-glass.md) measures a glass
that a depth camera cannot see at all. It costs nothing, it needs no extra
hardware, and it fails the moment the object is not on the plane you assumed.

**Put something of known size in the picture.** A printed marker — ArUco, AprilTag,
ChArUco — of known dimensions gives the scale directly, because you know how big
it really is and you can see how big it appears. This is what photogrammetry does
with a scale bar, and it is the only way to get a true size out of a single
ordinary camera moved around an object.

The three are not exclusive and good systems use two of them, so that one can
check the other.

| The fact you add | How you get it | Costs | Breaks when |
| --- | --- | --- | --- |
| the distance to each pixel | a depth sensor | the sensor, and its failure modes on shiny and clear things | the surface returns no reading |
| the plane it stands on | measure the table once | nothing | the object is tilted, stacked or held |
| something of known size in view | a printed marker | putting the marker there | the marker is hidden, or not coplanar with the object |

## 4. Where the millimetres go

Before reaching for a better model it is worth knowing what the error actually
consists of. The chart below works it out for a 73.6 mm object at 340 mm, on the
repo's camera, with each cause acting on its own.

![Four ways to be a few millimetres wrong](../images/object-dimension-detection/overview/error-budget.svg)

Two things in it are worth pulling out.

A hand-eye calibration that is one degree out costs 5.9 mm at a 340 mm reach — more
than twice what a one-pixel segmentation error costs. Calibration is the least
glamorous item in this document and it is usually the largest term in the budget.
Section 11 is about it.

A depth reading that is 20 mm out — which is what a consumer depth camera does at
the rim of a shiny object — costs 4.3 mm in the width. Notice that this is a
*width* error caused by a *depth* error: the depth multiplies through the whole
measurement, so a sensor that is reliable in the middle of a flat face and poor at
the edges gives you an object of the wrong size, not merely the wrong distance.

Neither of these improves if you swap the segmentation model for a better one,
which is the most common wrong response to a measurement that is off.

## 6. Geometry you write yourself

These are the methods with no model behind them. Between them they cover most of
what a table-top arm actually needs, they run in microseconds, and their failure
modes are ones you can reason about rather than discover.

### 6.1 A known depth, and the two-line calculation

**What it is.** Section 2, applied directly: take the mask, count its width in
pixels, read the depth at the object, and multiply. This is the baseline every
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

### 6.2 The plane the object stands on

**What it is.** Instead of measuring the distance to the object, measure the
distance to the table once, and use the fact that the object is standing on it.
The camera ray through the bottom of the object meets the table at a known point,
which gives the distance, which gives the scale.

**Why this rather than a depth reading.** Because it works on objects the depth
sensor cannot see. A wine glass returns no depth at all, but it stands on a table
that does, so its height and its diameter at every height can be measured from a
plain side-on picture. The [glass case
study](../09_one-arm-training/07_case-study/01_place-glass.md) is built entirely
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

### 6.3 A marker of known size

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

### 6.4 The smallest rectangle round the mask

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

### 6.5 An oriented box round the point cloud

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

### 6.6 Silhouettes of a solid of revolution

**What it is.** A special case that is worth knowing because it is unreasonably
powerful when it applies. An object made on a lathe or a potter's wheel — a glass,
a bottle, a bearing, a turned leg — is a shape spun about an axis. Its outline
looks the same from every side, and the width of that outline at any height *is*
the diameter there. So one side-on picture gives the complete profile of the
object.

This is the technique the [glass case
study](../09_one-arm-training/07_case-study/01_place-glass.md) is built on, and it
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

### 6.7 Measuring by touching it

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
