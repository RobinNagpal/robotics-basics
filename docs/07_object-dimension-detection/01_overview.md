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
