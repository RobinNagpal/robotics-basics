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
   1. [A colour range](#11-a-colour-range)
   2. [Background subtraction](#12-background-subtraction)
   3. [Edges, contours and connected components](#13-edges-contours-and-connected-components)
   4. [Template matching](#14-template-matching)
   5. [Watershed and GrabCut](#15-watershed-and-grabcut)
   6. [Point clouds: remove the plane, then cluster](#16-point-clouds-remove-the-plane-then-cluster)
   7. [The depth hole, for glass and chrome](#17-the-depth-hole-for-glass-and-chrome)
   8. [Reading a mask honestly](#18-reading-a-mask-honestly)
   9. [Choosing the grouping distance, and clustering on the plane](#19-choosing-the-grouping-distance-and-clustering-on-the-plane)
   10. [Validating a segmentation against a known size range](#110-validating-a-segmentation-against-a-known-size-range)
2. [Measuring the object](#2-measuring-the-object)
   1. [A known depth, and the two-line calculation](#21-a-known-depth-and-the-two-line-calculation)
   2. [The plane the object stands on](#22-the-plane-the-object-stands-on)
   3. [Two photos from one moving camera](#23-two-photos-from-one-moving-camera)
   4. [A marker of known size](#24-a-marker-of-known-size)
   5. [The smallest rectangle round the mask](#25-the-smallest-rectangle-round-the-mask)
   6. [An oriented box round the point cloud](#26-an-oriented-box-round-the-point-cloud)
   7. [Silhouettes of a solid of revolution](#27-silhouettes-of-a-solid-of-revolution)
   8. [From a measurement to a decision](#28-from-a-measurement-to-a-decision)
   9. [Measuring by touching it](#29-measuring-by-touching-it)

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

The [tools and libraries doc](../09_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
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
[glass-picking case study](../10_one-arm-training/07_case-study/01_place-glass.md)
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

### 1.8 Reading a mask honestly

Two corrections that apply to every method above, and that are wrong in most
first implementations because both failures are silent.

**A pixel's position is its centre, so measure to the outside of the edge
pixels.** The distance from the leftmost glass pixel to the rightmost is one
pixel *short* of the object's width, because it runs centre to centre. Take half
a pixel off each end:

    width = (rightmost − leftmost + 1) pixels

That single pixel is a **bias, not noise** — it never averages out, and it is
always in the same direction. At a third of a metre on a modest sensor it is
about a millimetre, which is the same order as everything else in the error
budget.

**Check the mask's quality on the raw widths, never the smoothed ones.** Any
sensible pipeline smooths the width profile, because a segmentation edge wanders
by a pixel or two and an unsmoothed profile has a false narrowing in every
wobble. The trap is applying the quality check afterwards. A five-row median
makes *any* mask look clean, so a raggedness test downstream of it never fires,
on good masks or bad.

The check and the measurement want different inputs, and saying so is the whole
fix: **ask the raw widths whether the mask was worth trusting, then measure the
smoothed ones.** A check that never fails is worse than no check, because it is
also reassuring.

### 1.9 Choosing the grouping distance, and clustering on the plane

Section 1.6 gives the recipe and not the two numbers it needs. Euclidean
clustering is controlled by a **grouping distance**, which is how far apart two
points may be and still count as belonging to the same object. PCL calls it the
cluster tolerance and Open3D calls it `eps`. It is also controlled by a
**minimum cluster size**, which is how many points a clump must have before it is
called an object at all. Both are usually copied from whichever tutorial the code
came from. Both can be derived from the camera in about a minute, and this
subsection does that, then gives a change to the recipe that is worth more than
either number.

One word first, because the rest of this subsection and the next one both use it.
An object's **footprint** is the shape it covers on the surface it stands on, seen
from directly above. A bottle's footprint is a disc a little larger than its base.

**The grouping distance has a floor and a ceiling, and they come from different
places.** Getting either one wrong produces a failure with a name.

The floor comes from the sensor. Two points on the same flat face of one object
are one pixel apart in the picture, so on that face they are `depth / fx` apart in
the world, which is [the one
calculation](01_overview.md#6-the-one-calculation-underneath-everything) again. If
the grouping distance is below that spacing, no two points are ever neighbours and
every object comes apart into fragments or single points. That is
**over-segmentation**: one object returned as several clusters. The arm then
reaches for a quarter of a bottle.

The ceiling comes from the scene. Two objects standing a gap apart are separated
by that gap and by nothing else, so a grouping distance larger than the gap joins
them. That is **under-segmentation**: two objects returned as one cluster. It is
the more dangerous of the two, because the merged cluster's centre lies in the
space between the two objects, which is exactly where the gripper closes on
nothing.

Three things push the floor above the bare pixel spacing. A surface turned away
from the camera is sampled more sparsely, by a factor of one over the cosine of
the angle between the camera's line of sight and the surface's normal: at 60
degrees the spacing doubles, at 70 degrees it triples. The depth reading scatters,
so two neighbouring points on a flat face differ along the ray as well as across
it. And pixels drop out at boundaries, which leaves real holes in a real object. A
working rule that covers slant up to about 70 degrees is three times the pixel
spacing, with the sensor's own depth scatter added on top of that.

Read the table below as one row per distance from the camera to the object, with
everything in it computed from `depth / fx` on the repository's camera, where `fx`
is 277.1 pixels.

| Camera to object | One pixel covers | A working floor, three times that | Smallest gap it can still split |
| --- | --- | --- | --- |
| 150 mm | 0.541 mm | 1.6 mm | about 2 mm |
| 340 mm | 1.227 mm | 3.7 mm | about 4 mm |
| 600 mm | 2.165 mm | 6.5 mm | about 7 mm |
| 1000 mm | 3.609 mm | 10.8 mm | about 11 mm |

The last column is the floor read as a promise rather than a setting, because a
clustering step separates two objects only when their gap is larger than the
grouping distance.

Add the sensor's depth scatter to those floors before using them. A RealSense
D435i is quoted at about 2 mm root-mean-square at one metre in [the sensor
table](02_sensors.md#1-what-each-sensor-gives-you). Two neighbouring points can
each scatter by that much and in opposite directions, so at a metre with that
camera the floor is `10.8 + 2 × 2` = 14.8 mm rather than 10.8 mm. The
repository's simulated camera has no depth scatter at all, which is worth
remembering, because a grouping distance tuned in simulation is always too small
for the same scene in the world.

So at a 340 mm reach the usable window runs from about 4 mm up to the smallest gap
you must respect. The [Open3D recipe in the tools
document](../09_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
uses `eps=0.02`, which is 20 mm. That sits near the top of the window: comfortably
above the floor, and large enough to merge anything standing closer together than
20 mm. It is the right choice for three well-spaced boxes and the wrong one for a
tray of bottles.

Now read the bottom row again. **The window closes as the camera backs off.** At a
metre the floor alone is 10.8 mm, so two objects that have to be told apart at
10 mm of separation cannot be, at any setting of any clustering algorithm. No
parameter fixes that, because the points needed to see the gap were never
captured. Moving the camera closer does fix it, which is the argument [the wrist
camera document](08_the-wrist-camera.md#1-what-changes-when-the-camera-is-on-the-arm)
makes at greater length.

**The minimum cluster size comes from the smallest object you must keep.** An
object `w` metres across at depth `z` is `w · fx / z` pixels across, and if the
camera sees roughly a square patch of it the cluster holds about the square of
that many points. A 60 mm block at 340 mm is `0.060 × 277.1 / 0.340` = 48.9 pixels
across, so about 2,400 points. A 20 mm object at 600 mm is 9.24 pixels across, so
about 85 points. The camera sees part of a face and rarely all of it, so set the
minimum at roughly a quarter of the smallest expected count: about 20 points for
that 20 mm object.

That figure is worth separating from a second one it is often confused with. In
DBSCAN the minimum does double duty, because a point needs that many neighbours
within the grouping distance before it counts as sitting in a dense region at all.
On a flat face at 340 mm, a disc of radius 20 mm holds about `π × (20 / 1.227)²` =
835 points, so a minimum of 20 excludes only genuinely isolated points. It is a
noise filter. The recipe in the tools document then throws away every clump under
100 points as a *separate* step, and that one is the size filter. Two thresholds,
two different questions, and merging them is how a pipeline ends up either keeping
speckle or deleting small parts.

**Project the points onto the support plane and cluster in two dimensions.** This
is the change that is worth more than either number, and it is the part that gets
left out of every tutorial.

The plane removal in 1.6 has already found the surface. Every remaining point can
be dropped straight down onto it, which throws away the height and keeps the
position on the surface. PCL does the projection with [its ProjectInliers
filter](https://pointclouds.org/documentation/tutorials/project_inliers.html); in
Open3D or in plain NumPy it is one subtraction of each point's component along the
plane's normal. Cluster those flattened points instead of the original ones.

Two things improve at once, and both improve most for objects that are tall
relative to their footprint.

The first is that the distance being tested becomes the distance you actually
know. Two bottles standing 30 mm apart on a table are 30 mm apart on the table and
nowhere else. Clustering in three dimensions asks for the *smallest* distance
between any point of one bottle and any point of the other, taken over the whole
height of both, and that minimum lands wherever the two happen to come closest:
at the shoulders where the glass bulges out, at a neck that leans, at a rim caught
by a reflection. One bridging pair of points anywhere up that height merges the
two clusters completely, and a tall object offers many more chances for such a
pair to exist. Flattened onto the plane there is only one distance left to test,
and it is the gap between the two footprints, which is the number you designed the
cell around.

The second is the grazing wall. The side of a tall object seen from above is
nearly edge-on to the camera, so consecutive pixels down that wall land far apart
in the world. At 340 mm, on a wall whose normal is 80 degrees from the camera's
line of sight, the spacing along the wall is `1.227 / cos 80°` = 7.07 mm, which is
5.8 times the face-on figure. Holding that wall together in three dimensions needs
a grouping distance above 7 mm, which is already more than a third of the 20 mm
gap you were relying on to keep two objects apart. Flattened onto the plane, the
whole wall collapses into a ring a few millimetres wide whose points are spaced by
the ordinary 1.227 mm, so a 4 mm grouping distance holds it together and still
splits a 10 mm gap.

**What it costs.** The projection assumes each object stands above its own
footprint. Anything that overhangs its base lands on a neighbour's footprint and
merges with it, which is the one case where two dimensions are worse than three.
It also throws the height away, so the height has to be recovered afterwards by
looking at the original points belonging to each two-dimensional cluster. That is
one extra pass over the data and no extra parameters.

Five jobs it suits:

- bottles, jars, cans and cups standing on a table, which is the case the trick
  was derived for
- a tray or a bin of upright parts, where the gaps on the surface are the ones
  that matter
- any cell where the camera looks down steeply and therefore sees the objects'
  sides almost edge-on
- separating two objects whose tops nearly touch while their bases do not
- producing one footprint per object, which is exactly the input the next
  subsection's size check wants

Five jobs it cannot do:

- objects that overhang their base — a mug's handle, a T-shaped part, a lid wider
  than the jar under it — which project onto whatever stands beside them
- stacked objects, which share one footprint exactly and come back as one cluster
- scenes with no usable support plane, since there is nothing to project onto
- objects lying flat, whose footprint is the whole of them and which the plane
  removal has usually deleted already
- giving heights directly, since the height is the thing that was thrown away

### 1.10 Validating a segmentation against a known size range

**What it is.** A check rather than a method. You usually know roughly how big the
things in a cell are, before the robot looks at anything. Turn each region's
measured footprint into millimetres, and reject any region whose implied size could
not belong to the class it claims to be. A blob whose implied width is 400 mm, in a
cell where nothing exceeds 120 mm, is not a large object. It is two objects merged,
or a strip of table that survived the plane fit, or a shadow joined onto a part.
Rejecting it costs one multiplication and one comparison.

It is worth seeing on real numbers how far outside the possible such a region is.
On the repository's camera at a 340 mm reach one pixel covers 1.227 mm, so an
implied width of 400 mm is
`0.400 × 277.1 / 0.340` = 326 pixels. The sensor is 320 pixels wide and the frame
covers 392.6 mm at that distance, so a 400 mm object could not have fitted in the
picture in the first place. The arithmetic that establishes this is two lines long
and it runs in nanoseconds, which is why it is worth doing on every region of every
frame.

**A range is a rule and a specific size is not, and that decides where each
belongs.** "A mug is between 70 and 120 mm across" is a statement about mugs, it
was true last year, and it will be true tomorrow. "The mug was 94 mm across" is a
measurement of one mug on one day. The range belongs in configuration, next to the
list of classes, as one row per class giving a minimum and a maximum for each
dimension in millimetres. It does not belong inside the vision code, because it
changes when the cell's job changes and the vision code does not. It also should
not be learned from whatever objects you happen to have, because the range you want
is the range of the class and not the range of your sample.

Widen each range by the measurement error before testing against it. A mask edge
one pixel out on each side is 2.454 mm at 340 mm and 7.218 mm at one metre on this
camera, so a 120 mm ceiling tested at a metre has to be 127 mm or it will reject
correct masks. The check exists to catch answers that are impossible, not answers
that are merely a little wrong.

**Fit a shape to the footprint and test the residual.** A **residual** is how far
the measured points sit from the shape that was fitted to them, and a large one
says the shape is the wrong description. Three fits are worth having, and which one
to use is decided by what the class's footprint actually is.

A circle is the first. `cv2.minEnclosingCircle` gives the smallest circle that
contains the footprint and a least-squares fit gives the best-fitting one, both
documented among [OpenCV's contour
features](https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_contours/py_contour_features/py_contour_features.markdown).
The residual is the root-mean-square distance from each boundary point to that
circle. For one round object it is a millimetre or two. For two round objects
merged into one region it is comparable to their radius, because no single circle
passes through both outlines.

A rectangle is the second. `cv2.minAreaRect`, from [section
2.5](#25-the-smallest-rectangle-round-the-mask), gives the smallest rotated
rectangle containing the footprint. The residual here is best expressed as the
**extent**, which is the footprint's area divided by the rectangle's area. A real
rectangle gives about 0.95. A circle inside its own smallest rectangle gives
`π / 4` = 0.785, which is not a failure but a correct statement that the object is
round. An L-shape formed by two merged parts gives about 0.5, which is a failure.

An oriented box in three dimensions is the third, from [section
2.6](#26-an-oriented-box-round-the-point-cloud). Its residual is how much of the
box the points actually occupy. It catches the same merges in a scene that has no
clean support plane to project onto.

The fit is what turns "how wide is this blob" into "how wide is the object this
blob claims to be", and the residual is what says whether the claim is worth
testing at all. A footprint that no circle and no rectangle fits is already a
failed segmentation, before any size has been compared to anything.

**Aspect ratio and area are two further checks, and their value is that they are
independent of the first two.** The rotated rectangle's long side divided by its
short side is the **aspect ratio**, a single number saying how elongated the
footprint is. The footprint's area in square millimetres is the other. They fail in
different directions, which is the whole reason to keep both:

- two identical objects merged side by side roughly double the area and roughly
  double the aspect ratio
- a strip of table joined onto an object raises the area a great deal and can leave
  the aspect ratio entirely plausible
- half an object, where the mask broke in the middle, halves the area and moves the
  aspect ratio the other way
- an object seen at an angle keeps its aspect ratio and loses area, because the
  dimension pointing away from the camera is foreshortened

Three numbers that can each fail on their own catch more than one number that has
to fail for three reasons at once.

**The check, as pseudo code.** The ranges in it are facts about your own cell. The
thresholds are starting points rather than recommendations, and you tighten them
until the rejections stop being useful.

```
# One row per class, in millimetres. This lives in configuration,
# next to the class list, not in the vision code.
SIZE = {                  # class:  (min_short, max_short, min_long, max_long)
    'mug':               (    70,       120,       70,       130),
    'bottle':            (    55,        90,       55,        90),
}
ASPECT = {'mug': 1.1, 'bottle': 1.0}      # long side over short side, per class

mm_per_pixel = depth / fx                 # the one calculation, from the overview
edge_mm      = 2.0 * mm_per_pixel         # a mask edge one pixel out on each side

for each region found by any method above:

    footprint = the region's points, dropped onto the support plane   # from 1.9
    circle    = smallest enclosing circle of footprint
    rect      = smallest rotated rectangle of footprint

    # 1. Does any simple shape describe this region at all?
    residual = rms distance from the footprint's boundary to the better fit
    if residual > 0.15 * rect.short_side:
        reject "no shape fits: this is probably more than one object"

    # 2. Could the implied size belong to this class?
    lo_s, hi_s, lo_l, hi_l = SIZE[class]
    if not (lo_s - edge_mm <= rect.short_side <= hi_s + edge_mm):
        reject "implied width impossible for this class"
    if not (lo_l - edge_mm <= rect.long_side  <= hi_l + edge_mm):
        reject "implied length impossible for this class"

    # 3. Two checks that fail differently from the two above.
    if rect.long_side / rect.short_side > 2.0 * ASPECT[class]:
        reject "shaped like two of them side by side"
    if footprint.area_mm2 > 1.6 * hi_s * hi_l:
        reject "too much area: a merge, or the table came with it"

    accept, and carry residual forward as part of the answer
```

The last line is the one that is usually missed. A check that only accepts and
rejects throws away what it learned on the way. Passing the residual forward lets
the next stage prefer the cleanest of three surviving regions, rather than taking
whichever one happened to be tested first.

**The honest limit, which is that this catches gross failures and not subtle
ones.** The range you have to allow is the class's real variation plus the
measurement error. On this camera at one metre the measurement error alone is
7.2 mm on a 120 mm object, which is six per cent before any real variation in the
class has been allowed for. Anything wrong by less than about ten per cent
therefore passes every test above. Two objects of the same class merged into a region whose
implied size still lands inside the range pass. A perfectly segmented object of the
wrong class passes, because the check knows sizes and knows nothing about
identities. And an object that is genuinely outside the range it was given — the
doll's-house mug from [the
overview](01_overview.md#5-why-one-picture-has-no-size) — is thrown away. The rule
behaves exactly as written and the cell refuses a real mug. Treat this as a filter
that removes answers which cannot be true, and never as a measure of how good the
surviving answers are.

Five jobs it suits:

- rejecting merged clusters in a bin or on a crowded table, which is the common
  failure of nearly every method in this section
- catching a piece of the support surface that survived the plane fit, which is
  large and flat and nothing like the object
- filtering the output of a promptable segmenter, which returns plausible-looking
  regions at every scale and offers no size opinion of its own
- choosing between several candidate regions, by preferring the one whose shape
  fits best rather than the one with the highest score
- a standing check on a pipeline that used to work, which is how a knocked camera
  or a moved table gets noticed on the day it happens

Five jobs it cannot do:

- catch an error smaller than the tolerance it had to allow, which is most real
  errors
- work on a class whose size genuinely varies over a wide range, such as "a rock",
  "a parcel" or "a piece of fruit"
- tell two objects of the same size and different identity apart
- work without the distance to the object, since without it the footprint is in
  pixels and pixels have no size
- say anything about pose, grasp or condition, none of which a size range touches

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
study](../10_one-arm-training/07_case-study/01_place-glass.md) is built entirely
on this.

**What it costs.** The assumption. If the object is not on the plane — if it is
tilted, stacked on another object, or in the gripper — the answer is confidently
wrong.

**And a bias that is easy to miss, because the method looks exact.** It is exact
only for a point actually *on* the plane. Every point above it lands too far out.
The ray from the camera through a feature at height `h` does not stop there; laid
onto the table it carries on and strikes the plane further away, by a factor of

    H / (H − h)

where `H` is the camera's height above the table. That is a systematic error, not
noise, and it grows fast. With a wrist camera 280 mm up:

| Feature at | Reads this much too wide |
| --- | --- |
| on the table | exact |
| 25 mm up | 10% over |
| 50 mm up | 22% over |
| 100 mm up | **55% over** |
| 150 mm up | **115% over** |

The widest part of a wine glass is around 100 mm up. Measured this way it comes
back over half as wide again as it is — a real case had a 157 mm glass reported
as 244 mm. Everything downstream then believes it, because nothing about the
number looks wrong.

The base of the glass is on the plane, so **the footprint is trustworthy and the
silhouette above it is not.** Either use the plane only for what touches it, or
recover the height with the next section.

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

### 2.3 Two photos from one moving camera

The fix for the bias above, and a technique that gets missed because it sits
between two things people already know.

Take a picture, move the camera a known distance sideways, take another. A
feature standing on the plane does not move between the two views once both are
laid onto the plane. A feature *above* the plane does, and how far it moves tells
you how high it is.

For a baseline `b`, the apparent position on the plane shifts by

    Δ = b · h / (H − h)

and rearranging gives the shrink factor that undoes the bias directly:

    k = b / (b + Δ)          true width = apparent width × k
                             height h   = H · (1 − k)

Worked through on the case above: the glass reads 244 mm wide, the camera is
280 mm up. Move the camera 40 mm and the apparent width shifts by 22.2 mm, so
k = 40 / 62.2 = 0.643, and 244 × 0.643 = **157 mm**, which is the right answer.
Any baseline gives the same k; a longer one just measures Δ more precisely.

**This is not [stereo matching](05_models-that-measure.md#2-stereo-matching)**,
and the difference is worth being clear about. Stereo uses two cameras and
matches every pixel to build a dense disparity map. This uses *one* camera that
the arm moves, and matches whole blobs — the object's outline in view A against
its outline in view B. There is nothing dense about it and no matcher to tune.

It also has a property a stereo rig does not: **the baseline comes from the arm's
own encoders, so it is known exactly and for free.** A stereo rig's baseline is a
calibration you have to establish and maintain. Here it is whatever the arm was
told to move, to a few hundredths of a millimetre.

Five jobs it suits:

- undoing the outward bias of the plane method, which is what it was derived for
- getting a height for an object a depth sensor cannot see
- any cell where the camera is on the arm, since the move is free
- checking a depth reading against something measured a different way
- objects whose outline is clean enough to match as a whole

Five jobs it cannot do:

- dense depth over a scene, which is what stereo is for
- work if the object moves between the two pictures
- work on a fixed camera, having no way to make a baseline
- resolve features smaller than the shift is precise
- help at all when the object is lying on the plane, where there is no parallax
  to measure

### 2.4 A marker of known size

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

### 2.5 The smallest rectangle round the mask

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

### 2.6 An oriented box round the point cloud

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

### 2.7 Silhouettes of a solid of revolution

**What it is.** A special case that is worth knowing because it is unreasonably
powerful when it applies. An object made on a lathe or a potter's wheel — a glass,
a bottle, a bearing, a turned leg — is a shape spun about an axis. Its outline
looks the same from every side, and the width of that outline at any height *is*
the diameter there. So one side-on picture gives the complete profile of the
object.

This is the technique the [glass case
study](../10_one-arm-training/07_case-study/01_place-glass.md) is built on, and it
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

### 2.8 From a measurement to a decision

The last step is turning a number into a choice, and two patterns are worth
naming because both are got wrong in the same way.

**Work out what the measurement allows, rather than assuming a fixed tolerance.**
An object going into a slot has `(spacing − width) / 2` of clearance each side,
and because it pivots about its base as it goes down, the lean that uses up that
clearance is

    atan(clearance / height)

which depends on *this* object's measured width and height, not on a number you
chose in advance. Slots 100 mm apart give an 80 mm object 10 mm a side: 6.3
degrees if it is 90 mm tall, 3.3 if it is 175 mm, and 1.6 if it is also 90 mm
wide. If the arm holds 3 degrees, the first two are fine and the third must have
the neighbouring slot left empty — which doubles the spacing and takes it to 17.4
degrees. Same rule, three different answers, decided per object on the day.

**Let the hardware bound the search, not the answer.** A gripper body is a solid
object that arrives alongside whatever it grips, so there is a lowest height it
can reach without fouling the table. That limit belongs in the search: look for a
grip *within the reachable band*. Put it on the answer instead — find the best
grip, then reject it for being too low — and a rule that would have found a
perfectly good grip 10 mm higher instead reports that the object cannot be held
at all.

The distinction sounds pedantic and is not. Bounding the answer turns a
constraint into a refusal; bounding the search turns it into a different, valid
result. Every constraint the hardware imposes should be pushed into the search
for the same reason.

### 2.9 Measuring by touching it

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

