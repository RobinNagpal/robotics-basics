# Searching and matching

This chapter covers the techniques that find the closest thing, and decide which
thing is which. It answers three questions that come up again and again in
robot-arm software. Which point, object or pose is nearest to this one? Where
exactly is a known part, given a scan of it? And which of the objects seen now
is which of the objects seen before?

It is for a reader who knows what a point cloud, a frame and a camera picture
are, from Books 1 and 2, but who has not met these algorithms before. This page
is the map of the chapter. Each technique then has its own page with a worked
example, pseudocode and a list of libraries.

## Contents

1. [What these techniques are for](#1-what-these-techniques-are-for)
2. [The three techniques](#2-the-three-techniques)
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

## 2. The three techniques

The chapter has three technique pages:

- [Nearest-neighbour search](02_nearest-neighbour-search.md) finds, for a query
  point, the closest point in a set, or the k closest, or all points within a
  radius. It uses a tree of boxes, called a k-d tree, so that it does not have to
  measure the distance to every point.
- [Iterative closest point (ICP)](03_iterative-closest-point.md) moves a model
  of a part onto a scan of the part. It pairs each model point with its nearest
  scan point, moves the model to fit those pairs, and repeats.
- [Assignment and matching](04_assignment-and-matching.md) pairs up two lists,
  such as the mugs seen one frame ago and the mugs seen now, so that each thing
  gets at most one partner and the total cost is as small as possible. The
  Hungarian algorithm does this exactly. A greedy method does it approximately.

The table below compares the three. Read it one row at a time: the row names the
technique, and the columns say what goes in, what comes out, and where the
technique usually fails.

| Technique | What goes in | What comes out | Where it usually fails |
|---|---|---|---|
| Nearest-neighbour search | a set of points and a query point | the nearest point, the k nearest, or all within a radius | nothing is near enough, or the "distance" does not match what "similar" means |
| Iterative closest point | a model point set, a scan point set, and a first guess of the pose | the rotation and shift that line the model up with the scan | the first guess is too far off, or the part is symmetric |
| Assignment (Hungarian or greedy) | two lists and a cost for every possible pair | a one-to-one pairing, and the things left without a partner | the costs are wrong, or objects are closer together than the measurement error |

The three build on each other. ICP runs a nearest-neighbour search in every
round. Assignment often uses nearest-neighbour search to fill in its table of
costs, or to throw away pairs that are clearly too far apart before it starts.

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
  [rigid transform](../02_geometry-and-cameras/03_rigid-transforms.md), the same
  rotation and shift that chapter explains.
- [Fitting and estimation](../04_fitting-and-estimation/01_overview.md) uses
  nearest neighbours to find the points on which to fit a plane or a normal. It
  also supplies the [Kalman filter](../04_fitting-and-estimation/04_kalman-filter.md),
  which predicts where a tracked object should be now, so that assignment can
  compare detections against the prediction rather than the old position.
- [Image and point cloud processing](../05_image-and-point-cloud-processing/01_overview.md)
  uses radius search to grow clusters of points into objects, in
  [clustering](../05_image-and-point-cloud-processing/05_clustering.md).
- [Decisions and task logic](../08_decisions-and-task-logic/01_overview.md)
  uses the same greedy idea as greedy matching, in
  [greedy algorithms and set cover](../08_decisions-and-task-logic/04_greedy-algorithms-and-set-cover.md),
  and solves larger assignment problems with the
  [optimisation solvers](../08_decisions-and-task-logic/05_optimisation-solvers.md).

Learned models, described in Book 6, do some of the same jobs. A learned tracker
can follow objects from frame to frame, as
[tracking and motion](../../06_neural-network-models/02_seeing-models/08_tracking-and-motion.md)
explains. A learned pose model can find where a known part is without ICP, as
[keypoints and object pose](../../06_neural-network-models/02_seeing-models/05_keypoints-and-object-pose.md)
explains. Even then, the programmed techniques stay in the pipeline. A learned
tracker still usually pairs its boxes with the Hungarian algorithm, and a learned
pose is often finished off with a few rounds of ICP to make it more exact.

---

## 5. Where to read next

- Start with [nearest-neighbour search](02_nearest-neighbour-search.md). The
  other two pages use it.
- Then read [iterative closest point](03_iterative-closest-point.md) and
  [assignment and matching](04_assignment-and-matching.md), in either order.
- Book 2's
  [tracking and association](../../02_perception/02_object-perception/10_tracking-and-association.md)
  goes much deeper into matching objects over time, including how wide to make
  the gate and what to do when a match fails.
