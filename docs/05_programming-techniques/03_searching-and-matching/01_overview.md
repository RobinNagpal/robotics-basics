# Searching and matching

This chapter covers the techniques that find the closest thing, and decide which
thing is which. It answers three questions that come up again and again in
robot-arm software. Which point, object or pose is nearest to this one? Where
exactly is a known part, given a scan of it? And which of the objects seen now
is which of the objects seen before? A fourth question comes up with camera
pictures: which small spots in one picture show the same thing as spots in another?

It is for a reader who knows what a point cloud, a frame and a camera picture
are, from Books 1 and 2, but who has not met these algorithms before. This page
is the map of the chapter. Each technique then has its own page with a worked
example, pseudocode and a list of libraries.

## Contents

1. [What these techniques are for](#1-what-these-techniques-are-for)
2. [The four techniques, in two groups](#2-the-four-techniques-in-two-groups)
3. [Why the obvious method is not enough](#3-why-the-obvious-method-is-not-enough)
4. [How this chapter connects to the others](#4-how-this-chapter-connects-to-the-others)
5. [Where to read next](#5-where-to-read-next)

---

## 1. What these techniques are for

This family of techniques does one job: finding the closest thing, and deciding
which thing is which.

A robot arm meets this job all the time. A depth camera gives a cloud of tens of
thousands of points. The software needs, for each point, the few points next to
it, to work out which way the surface faces. A gripper tip moves over a table,
and the software needs the object nearest to it. A camera sees three mugs, and
the software needs to know which mug is the one it was already carrying.

The picture below shows the three questions on one table, seen from above. Each
answer in it was computed by the diagram script, not drawn by hand.

![The three questions this chapter answers, on one table](../../images/searching-and-matching/overview/three-questions.svg)

The first panel finds the object nearest to the gripper. The second moves a
stored outline of a bracket onto a scan of the real bracket. The third pairs
each mug seen now with a mug seen one frame ago.

All three share one idea. You measure how far apart two things are, with a
number called a **distance** or a **cost**. Then you look for the smallest
distance, or the set of pairs whose distances add up to the smallest total.

---

## 2. The four techniques, in two groups

The chapter has four technique pages, in two groups.

The **most used** group holds the three techniques that nearly every robot arm with
a camera runs, often many times a second. The other techniques in this book lean on
them too.

- [Nearest-neighbour search](02_most-used/01_nearest-neighbour-search.md) finds, for a query
  point, the closest point in a set, or the k closest, or all points within a
  radius. It uses a tree of boxes, called a k-d tree, so that it does not have to
  measure the distance to every point.
- [Iterative closest point (ICP)](02_most-used/02_iterative-closest-point.md) moves a model
  of a part onto a scan of the part. It pairs each model point with its nearest
  scan point, moves the model to fit those pairs, and repeats.
- [Assignment and matching](02_most-used/03_assignment-and-matching.md) pairs up two lists,
  such as the mugs seen one frame ago and the mugs seen now, so that each thing
  gets at most one partner and the total cost is as small as possible. The
  Hungarian algorithm does this exactly. A greedy method does it approximately.
  ICP's page also has a section on
  [getting a first guess](02_most-used/02_iterative-closest-point.md#5-getting-a-first-guess-3d-features-and-global-registration)
  from 3D shape features, for when the part could be turned any way at all.

The **also used** group holds a technique that is common, but only on some robots:
those that must find objects with printing or texture on them from a camera picture.

- [Image features and matching](03_also-used/01_image-features-and-matching.md)
  finds corners in two pictures, describes the patch round each one as a list of
  numbers, pairs corners whose lists are alike, and keeps the pairs that agree on
  one movement of the object. It finds a known flat object, such as a label, and
  gives the pairs that a 3D pose calculation needs.

The table below compares the four. Read it one row at a time: the row names the
technique, and the columns say what goes in, what comes out, and where the
technique usually fails.

| Technique | What goes in | What comes out | Where it usually fails |
|---|---|---|---|
| Nearest-neighbour search | a set of points and a query point | the nearest point, the k nearest, or all within a radius | nothing is near enough, or the "distance" does not match what "similar" means |
| Iterative closest point | a model point set, a scan point set, and a first guess of the pose | the rotation and shift that line the model up with the scan | the first guess is too far off, or the part is symmetric |
| Assignment (Hungarian or greedy) | two lists and a cost for every possible pair | a one-to-one pairing, and the things left without a partner | the costs are wrong, or objects are closer together than the measurement error |
| Image features and matching | a stored picture of an object and a camera picture | pairs of matching spots, and the homography or pose that most of them agree on | the object has no texture, or a repeated pattern |

The four build on each other. ICP runs a nearest-neighbour search in every
round. Assignment often uses nearest-neighbour search to fill in its table of
costs, or to throw away pairs that are clearly too far apart before it starts.
Image feature matching pairs spots with a nearest-neighbour search among their
descriptions, and its answer is often the first guess that ICP then makes exact.

---

## 3. Why the obvious method is not enough

For each question there is an obvious method that is always right: try every
possibility. For the nearest point, measure the distance to every point. For the
best pairing, try every possible way of pairing the objects up.

The obvious method is often the right choice when the numbers are small. A
table with ten objects needs ten distance checks, which takes no time. The
trouble is how fast the work grows. The picture below shows it.

![Trying every possibility grows much faster than the clever method](../../images/searching-and-matching/overview/work-grows.svg)

The left panel matches every point of one scan to its nearest point in a second
scan of the same size. Checking every pair needs 9,000,000 distance checks for
3,000 points. The k-d tree in the diagram script needed 44,425, about 15 per
point. The right panel pairs up objects. Trying every pairing of 12 objects
means trying 479,001,600 pairings. The Hungarian algorithm needs roughly 12 × 12
× 12 = 1,728 steps.

A depth camera with a 640 by 480 picture gives up to 307,200 points in each
picture, and it gives 30 pictures a second. So checking every pair is not possible on a live camera, and
the k-d tree is what makes point cloud work run at all.

---

## 4. How this chapter connects to the others

This is the second of the seven families of techniques in this book. The
[map of techniques](../01_what-techniques-are/04_the-map-of-techniques.md) shows
all seven. Searching and matching connects to the others in these ways.

- [Geometry and cameras](../02_geometry-and-cameras/01_overview.md) turns
  pixels and depth into 3D points in the arm's frame. Those points are what this
  chapter searches. ICP's answer is a
  [rigid transform](../02_geometry-and-cameras/02_most-used/02_rigid-transforms.md), the same
  rotation and shift that chapter explains. Its
  [pose from points](../02_geometry-and-cameras/02_most-used/04_pose-from-points.md)
  page turns the pairs found by image feature matching into a 3D pose.
- [Fitting and estimation](../04_fitting-and-estimation/01_overview.md) uses
  nearest neighbours to find the points on which to fit a plane or a normal. It
  also supplies the [Kalman filter](../04_fitting-and-estimation/02_most-used/03_kalman-filter.md),
  which predicts where a tracked object should be now, so that assignment can
  compare detections against the prediction rather than the old position. Its
  [RANSAC](../04_fitting-and-estimation/02_most-used/02_ransac.md) throws away the
  wrong pairs in image feature matching and in ICP's global first guess.
- [Image and point cloud processing](../05_image-and-point-cloud-processing/01_overview.md)
  uses radius search to grow clusters of points into objects, in
  [clustering](../05_image-and-point-cloud-processing/02_most-used/03_clustering.md).
- [Decisions and task logic](../08_decisions-and-task-logic/01_overview.md)
  uses the same greedy idea as greedy matching, in
  [greedy algorithms and set cover](../08_decisions-and-task-logic/03_also-used/01_greedy-algorithms-and-set-cover.md),
  and solves larger assignment problems with the
  [optimisation solvers](../08_decisions-and-task-logic/03_also-used/02_optimisation-solvers.md).

Learned models, described in Book 6, do some of the same jobs. A learned tracker
can follow objects from frame to frame, as
[tracking and motion](../../06_neural-network-models/02_seeing-models/03_also-used/03_tracking-and-motion.md)
explains. A learned pose model can find where a known part is without ICP, as
[keypoints and object pose](../../06_neural-network-models/02_seeing-models/02_most-used/04_keypoints-and-object-pose.md)
explains. Even then, the programmed techniques stay in the pipeline. A learned
tracker still usually pairs its boxes with the Hungarian algorithm, and a learned
pose is often finished off with a few rounds of ICP to make it more exact.

---

## 5. Where to read next

- Start with [nearest-neighbour search](02_most-used/01_nearest-neighbour-search.md). The
  other two pages use it.
- Then read [iterative closest point](02_most-used/02_iterative-closest-point.md) and
  [assignment and matching](02_most-used/03_assignment-and-matching.md), in either order.
- Read [image features and matching](03_also-used/01_image-features-and-matching.md)
  when the arm must find objects from a camera picture rather than a depth scan. It
  uses nearest-neighbour search, and it helps to have read
  [RANSAC](../04_fitting-and-estimation/02_most-used/02_ransac.md) first.
- Book 2's
  [tracking and association](../../02_perception/02_object-perception/10_tracking-and-association.md)
  goes much deeper into matching objects over time, including how wide to make
  the gate and what to do when a match fails.
