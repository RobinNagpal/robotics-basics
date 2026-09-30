# RANSAC: fitting when some points are wrong

This page explains random sample consensus (RANSAC), which fits a line, a plane,
a circle or a cylinder to a set of points. It is meant for the case where many of
those points belong to something else. It answers four questions, and the first
of them is how RANSAC finds the right shape when a third or half of the points
are wrong. The other three are how many tries it needs, where a robot arm uses
it, and what makes it fail.

It is for a reader who has read the page on
[least-squares fitting](01_least-squares-fitting.md). That page explains
parameters, residuals and the root mean square (RMS) residual, and it shows that
one bad point can move a least-squares line a long way. This page starts from
that problem, and every number on it comes from a real run of the diagram script,
`docs/diagrams/fitting_and_estimation.py`.

RANSAC is the standard way a table-top robot finds the table in a depth camera's
point cloud. Although Martin Fischler and Robert Bolles published it as long ago
as 1981, it is still the first thing most perception pipelines run on a new point
cloud.

## Contents

1. [What this page answers](#1-what-this-page-answers)
2. [The idea in one sentence](#2-the-idea-in-one-sentence)
3. [How it works, step by step](#3-how-it-works-step-by-step)
   · [The loop](#the-loop)
   · [A worked example: a table edge with stray points](#a-worked-example-a-table-edge-with-stray-points)
   · [The steps as pseudocode](#the-steps-as-pseudocode)
   · [How many tries are enough](#how-many-tries-are-enough)
   · [Planes and cylinders in a point cloud](#planes-and-cylinders-in-a-point-cloud)
   · [Choosing the distance limit](#choosing-the-distance-limit)
4. [Where it is used on a robot arm](#4-where-it-is-used-on-a-robot-arm)
5. [Where it is useful, and where it is not](#5-where-it-is-useful-and-where-it-is-not)
6. [Libraries that provide it](#6-libraries-that-provide-it)
7. [Why RANSAC, and what it costs](#7-why-ransac-and-what-it-costs)
8. [The learned alternative](#8-the-learned-alternative)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What this page answers

Real point clouds are messy, and a depth camera looking at a table shows why. It
sees the table, but it also sees the objects standing on it, the edge of the
table and the floor beyond. Then there are the false readings, which are
scattered points that appear where the light hit a shiny surface. So if you want
the table's plane, only some of those points belong to it.

Least squares uses every point, so the other points drag the answer away. You
could remove them first, but to know which points to remove you would need to
know where the table is, and that is the question you started with.

RANSAC breaks this circle, because it does not need to know in advance which
points are good. Instead, it finds the shape and the points that belong to it at
the same time. The points that belong to the shape are called **inliers**, and
the rest are called **outliers**.

---

## 2. The idea in one sentence

Section 1 said that RANSAC finds the shape and its good points at the same time.
However, it did not say how, and the answer fits into a single sentence.

**Guess the shape from a few randomly chosen points, count how many other points
agree with the guess, repeat many times, and keep the guess that most points
agree with.**

Here is an everyday example, in which a group of people each point at where they
think a lost ball landed. Most of them saw it, so they point near the same spot,
while a few are guessing and point all over the field. If you take the average of
all the pointing directions, the guessers drag it away from the true spot.
Instead, you pick one person at random and ask everyone else whether they agree
with that person, give or take a metre. If most hands go up, then you have found
the spot. But if only two hands go up, you picked a guesser, so you pick someone
else and ask again.

The key point is that a guess made only from good points will be agreed with by
all the other good points. However, a guess that includes even one bad point will
be agreed with by almost nobody. So you do not need to know which points are
good. You only need to keep trying until one guess is made entirely from good
points.

---

## 3. How it works, step by step

### The loop

Section 2 gave the idea as one sentence, so this section turns that sentence into
a loop you could program. RANSAC needs three things from you: the kind of shape,
the smallest number of points that defines one such shape, and a distance limit.

- The smallest number of points is 2 for a line, 3 for a plane and 3 for a
  circle on a table.
- The **distance limit** says how close a point must be to the shape to count
  as agreeing with it, so it should be a little larger than the sensor's noise.

Once you have given it those three things, it runs this loop:

1. Pick the smallest number of points at random.
2. Make the one shape that passes exactly through them.
3. Measure every point's distance from that shape, and count the points closer
   than the distance limit, because those points are this try's inliers.
4. If this try has more inliers than the best try so far, remember it.
5. Repeat from step 1 a fixed number of times.
6. Take the inliers of the best try, and fit the shape to all of them with
   [least squares](01_least-squares-fitting.md), so that this last step uses
   every good point and not just the two or three that were picked.

### A worked example: a table edge with stray points

The example has 55 points in a side view of a table edge, measured in
millimetres. Forty of them lie along the edge, whose true line is
`y = 0.25 x + 20`, with 1.5 mm of noise. The other fifteen are stray readings
scattered above the edge. So 27% of the points are outliers.

The picture below shows three of the 100 tries RANSAC made, with a distance
limit of 4 mm.

![Three RANSAC tries: one through a stray point with 7 agreeing points, one through two edge points far along with 20 agreeing points, and the best try with 40](../../../images/fitting-and-estimation/ransac/three-tries.svg)

Try 1 picked a stray point and an edge point. Its line therefore crosses the edge
at an angle, so only 7 points lie within 4 mm of it. Try 3 picked two edge points
close together at the right end, and their noise tilts the line a little. So it
fits the right part of the edge and misses the left part, which leaves only 20
points agreeing. Try 9 picked two edge points 65 mm apart, so its line follows
the whole edge and all 40 edge points agree with it. No try did better than 40,
which is why try 9 is the one RANSAC kept.

The final step fits a least-squares line to those 40 inliers, and the picture
below compares the result with a least-squares line through all 55 points.

![Left: a least-squares line through all points is pulled up by the outliers. Right: the RANSAC line follows the edge, with the outliers marked and ignored](../../../images/fitting-and-estimation/ransac/best-line.svg)

The least-squares line through everything is `y = 0.188 x + 34.0`. Its offset is
therefore 14 mm too high, and its slope is a quarter too shallow. The RANSAC line
is `y = 0.260 x + 19.1`, which is close to the true `y = 0.25 x + 20`. RANSAC
also labelled every one of the 55 points correctly, with the 40 edge points as
inliers and the 15 stray points as outliers.

### The steps as pseudocode

```
function ransac(points, sample_size, distance_limit, tries):
    best_inliers = empty set
    repeat tries times:
        sample = choose sample_size points at random, without repeats
        shape = the shape that passes exactly through sample
        if shape could not be made (for example, the points are on one line):
            continue with the next try
        inliers = every point whose distance to shape < distance_limit
        if size of inliers > size of best_inliers:
            best_inliers = inliers
    final_shape = least-squares fit of the shape to best_inliers
    inliers = every point whose distance to final_shape < distance_limit
    return final_shape, inliers
```

Two common improvements to this loop are worth knowing, and the first of them
stops early. Once a new best try is found, recompute how many tries are needed
from the share of inliers just found. The next section gives that formula, and
you stop as soon as that many tries have been done. The second improvement,
called **MSAC**, scores each try by how close the agreeing points are, not just
how many there are, which breaks ties between guesses more sensibly.

### How many tries are enough

The loop above repeats a fixed number of times, so the next thing to work out is
what that number should be. A try succeeds when every point in its sample is an
inlier. So if a share `w` of the points are inliers and a sample has `s` points,
one try succeeds with a chance of `w` multiplied by itself `s` times, written
`wˢ`. To be sure, with a chance `p` such as 99%, that at least one try succeeds,
you need this many tries:

```
tries = log(1 − p) / log(1 − wˢ)
```

In the worked example, `w` is 40 out of 55, which is 0.727, and `s` is 2. So one
try succeeds with a chance of 0.53. For 99% certainty the formula gives 6.1,
which means 7 tries are enough, and yet the example used 100. That is common in
practice, because a line or plane try is cheap, so people use a generous number.

The picture below plots the formula for a line, a plane and a shape that needs 6
points.

![Tries needed for 99% success against the share of outliers, on a logarithmic scale, for samples of 2, 3 and 6 points](../../../images/fitting-and-estimation/ransac/how-many-tries.svg)

The number of tries grows slowly at first and then very fast. For a plane with
half the points as outliers, 35 tries are enough. But for a plane with 70%
outliers, 168 tries are needed. A shape that needs 6 points, with half the points
as outliers, needs 292 tries. This is why RANSAC works best for shapes defined by
very few points. It is also why it slows down sharply when the wanted shape is
only a small part of the scene.

### Planes and cylinders in a point cloud

A plane needs a sample of only 3 points, so it is one of the cheap shapes in the
chart above. This is also the shape a table-top robot wants most often. The plane
through those 3 points has a normal, which is the direction at right angles to
the plane. Because the three points make a triangle, that normal is equal to the
cross product of two edges of the triangle. The cross product is a standard
operation that gives the direction at right angles to two other directions. A
point's distance from the plane is then the size of its offset from one of the
three points, measured along the normal.

The picture below runs RANSAC on a simulated depth camera view of a table with a
box and a cup on it, plus 25 stray readings. It used 200 tries and a distance
limit of 5 mm.

![Left: the full point cloud. Right: the table plane's points in brown and the leftover points of the box, the cup and the stray readings in blue](../../../images/fitting-and-estimation/ransac/table-plane.svg)

Of the 1669 points, 1120 are on the table plane and 549 are left over. The fitted
plane's normal is (−0.030, 0.020, 0.999). The table itself was made tilted with a
normal of (−0.030, 0.020, 0.999), so the fit matches to three decimal places. The
top of the box is also a plane, but it has only 90 points against the table's
1100 or so, so RANSAC keeps the table. The leftover points go to
[clustering](../../05_image-and-point-cloud-processing/02_most-used/03_clustering.md), which
splits them into one group per object.

A cylinder, such as a can, a bottle or a pipe, is harder, because two or three
positions alone do not fix its axis. The usual method therefore works out each
point's **normal** first, meaning the direction the surface faces at that point,
from a small plane fit to its nearest neighbours. Then a try picks 2 points
together with their normals. Because both normals on a cylinder point straight
away from the axis, the axis must run at right angles to both. That gives the
axis direction, and from the axis direction the position and the radius follow. A
point agrees if its distance from the axis is close to the radius and its normal
points away from the axis. The Point Cloud Library (PCL) does this with its
cylinder model, which section 6 describes.

### Choosing the distance limit

Of the three things RANSAC needs from you, the distance limit is the one that
matters most. A good start is two to three times the sensor's noise. For example,
on a table half a metre away, a depth camera has about 1.5 mm of noise, so a
limit of 4 to 5 mm is common.

If the limit is too small, real surface points count as outliers. So the inlier
count of the true shape drops, and a wrong shape can win. If the limit is too
large, points just above the surface count as inliers. On a table, that means the
bottom few millimetres of every object are deleted along with the table. That
matters most for flat objects such as a coin or a phone lying down, because those
can vanish completely.

---

## 4. Where it is used on a robot arm

The sections above explained how the loop works and how to set it up, so this
section says where a real arm uses it. RANSAC is mostly a perception tool, but it
also appears in calibration and sensing.

- **Removing the table.** The classic table-top recipe finds the biggest plane,
  deletes it, and clusters what is left into objects. Book 2 describes this in
  [remove the plane, then cluster](../../../02_perception/02_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster),
  and the [tools and libraries](../../../03_frameworks/01_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
  page shows it as real Open3D code.
- **Finding walls and bin sides.** A robot picking from a bin runs RANSAC
  several times: find the biggest plane (the bin floor), remove its points, find
  the next (a wall), and so on, until what is left is the parts.
- **Fitting cylinders.** A robot that picks cans, bottles or pipes fits a
  cylinder to each cluster to get its axis and radius, and so the direction to
  approach it from.
- **Finding a circle in a noisy rim.** A glass's rim seen by a camera often has
  a few pixels from a reflection or from a neighbouring glass, so a circle
  RANSAC finds the rim first, and then least squares refines it.
- **Matching features between pictures.** When a camera on the arm moves, a
  program matches small patches between the old and the new picture, and some of
  those matches are wrong, so RANSAC finds the camera movement that most matches
  agree with. The same idea finds an object's pose from matched points, which
  OpenCV provides as `solvePnPRansac`.
- **Calibration.** When some checkerboard corners or marker detections in a
  calibration set are wrong, a RANSAC step can drop those poses before the final
  least-squares fit, which the
  [calibration](../../02_geometry-and-cameras/02_most-used/03_calibration.md) page covers.
- **Checking a known table.** When the table is fixed to the arm and measured
  once, RANSAC is not needed on every picture, as the glass-picking project in
  the sibling repo explains in its
  [clustering notes](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/docs/problem-2/solutions/02-cluster-on-the-table.md).
  RANSAC can still run now and then, to check that the camera has not been
  knocked.

---

## 5. Where it is useful, and where it is not

All of the uses above work for the same reason, so it is worth saying plainly
when RANSAC is the right tool. The shape you want must be the biggest single
shape in the data, and it must be defined by a few points. You must also be able
to say how far from the shape a good point may be, because that distance is what
decides which points agree. Once those conditions hold, it copes with half or
more of the points being outliers, which almost nothing else does.

But once one of them fails, RANSAC fails with it, so the table below lists the
ways that happens. Each row gives the cause, the sign you would see,
and what people use instead.

| What goes wrong | The sign you would see | What to use instead |
| --- | --- | --- |
| The wanted shape is not the biggest (a large box top beside a small patch of visible table) | the "table" is 60 mm too high, or tilted | check the plane's normal and height against what you expect; restrict the search to a region; or use a known table plane |
| Two shapes of similar size | the answer flips between them from one picture to the next | find one, remove its points, find the other; decide between them by a rule such as "lowest" |
| Too few tries for the share of outliers | a different, wrong answer on some runs | raise the number of tries, or use the formula above to set it |
| Distance limit too small | many real surface points marked as outliers; the answer jumps around | raise the limit to two or three times the noise |
| Distance limit too large | flat objects vanish with the table; the bottom of every object is cut off | lower the limit; keep points just above the plane for small objects |
| Shape needs many points to define | very many tries, slow | a method that starts from a good guess, such as [iterative closest point](../../03_searching-and-matching/02_most-used/02_iterative-closest-point.md), or a learned model |
| You need the same answer every run | tiny differences between runs, which make tests flaky | fix the random seed, or refit with least squares on the inliers (which is usually stable) |
| No shape dominates (a cluttered pile of parts) | low inlier counts for every try | a [point cloud model](../../../06_learned-models/04_3d-models/02_most-used/01_point-cloud-models.md) that labels each point, or [clustering](../../05_image-and-point-cloud-processing/02_most-used/03_clustering.md) first |

---

## 6. Libraries that provide it

Section 3 showed the loop as pseudocode, but you do not have to write that code
yourself, because RANSAC is built into every major point cloud and vision
library. The table below lists well-known ones, and each row gives the library,
the languages it is used from, the function or class, and a note.

| Library | Languages | Function or class | Note |
| --- | --- | --- | --- |
| Open3D | Python, C++ | `PointCloud.segment_plane(distance_threshold, ransac_n, num_iterations)` | returns the plane and the inlier indices; the usual table-removal call |
| PCL (Point Cloud Library) | C++ | `pcl::SACSegmentation` with `pcl::SACMODEL_PLANE`; `pcl::SACSegmentationFromNormals` with `pcl::SACMODEL_CYLINDER` | planes, lines, circles, spheres and cylinders; also MSAC and other variants |
| OpenCV | C++, Python | `cv::findHomography`, `cv::estimateAffine2D`, `cv::solvePnPRansac`, `cv::findEssentialMat` with the `RANSAC` flag | for matched points between pictures; newer versions also offer the USAC family of improved methods |
| scikit-learn | Python | `sklearn.linear_model.RANSACRegressor` | wraps any regression model; good for lines and planes in NumPy arrays |
| scikit-image | Python | `skimage.measure.ransac` | general RANSAC with ready-made line, circle and ellipse models |

For a table plane in Python, the Open3D call is a single line. The
[tools and libraries](../../../03_frameworks/01_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
page calls it with `distance_threshold=0.005`, which is 5 mm written in metres,
and 3 points per try.

---

## 7. Why RANSAC, and what it costs

The libraries above make RANSAC easy to call, so the question left is why you
would call it instead of something simpler. RANSAC is a fitting method that tries
many shapes, each one through a few random points, and keeps the shape that most
points agree with. It gives the arm the right shape even when many of the points
belong to other things. It also says which of the points belong to that shape.

The obvious alternative is least squares on all the points, perhaps after
throwing away the points far from a first fit and fitting again. That works when
only a few points are bad. But the first fit is already pulled towards the bad
points, so it may throw away good points and keep bad ones. In the worked
example, the first least-squares line was 14 mm too high at the left end. The
turn-top-flat project's repeated refit, described on the
[least-squares page](01_least-squares-fitting.md#4-where-it-is-used-on-a-robot-arm),
works because only a thin strip of edge points was wrong. RANSAC never averages
bad points in, so it works when a third or half of the points are bad.

A second alternative is a robust loss: a least-squares variant that counts large
errors less, such as the Huber loss in SciPy's `least_squares`. It is smooth and
repeatable, and it is good when outliers are a small share. But it starts from a
guess, so with many outliers it can settle on the wrong shape, while RANSAC needs
no starting guess at all.

RANSAC costs you five things, and the first is that it uses random choices, so
two runs can give slightly different answers unless the seed is fixed. Second, it
needs a distance limit, which means you must know the sensor's noise before you
can set it. Third, it is slower than one least-squares fit, because it makes many
tries, and it gets very slow for shapes that need many points. Fourth, it finds
only the biggest shape, which may not be the one you meant. Finally, it needs a
least-squares refit at the end to get the best accuracy.

---

## 8. The learned alternative

Section 7 weighed RANSAC against other ways of fitting a shape, but there is also
an alternative that does not fit a shape at all. A segmentation model, described
in Book 6's
[point cloud models](../../../06_learned-models/04_3d-models/02_most-used/01_point-cloud-models.md),
gives every point a name, such as "mug", "box" or "table". So it replaces RANSAC
when no single shape dominates the scene, such as a cluttered pile of parts. For
shapes that need many points to define, a pose model from
[keypoints and object pose](../../../06_learned-models/03_seeing-models/02_most-used/04_keypoints-and-object-pose.md)
finds the object's pose directly. But a point cloud model needs labelled 3D data,
which is much scarcer than labelled photos. It also needs a graphics card for
large clouds, and it knows only the kinds of object it was trained on. RANSAC is
still the better choice for the table, the walls of a bin and other simple
shapes. This is because it needs no training, runs on an ordinary processor and
says exactly which points belong to the shape.

---

## 9. Where to read next

This page left several things to other documents, so the list below says where
each of them is covered.

- [Least-squares fitting](01_least-squares-fitting.md) explains the final refit
  and the plane and circle fits that RANSAC calls.
- The [Kalman filter](03_kalman-filter.md) handles readings that arrive over
  time, rather than one batch of points.
- [Clustering](../../05_image-and-point-cloud-processing/02_most-used/03_clustering.md) takes
  the points left after the table is removed and splits them into objects.
- [Nearest-neighbour search](../../03_searching-and-matching/02_most-used/01_nearest-neighbour-search.md)
  finds the neighbours used to compute each point's normal before a cylinder fit.
- Book 2 shows the full recipe in
  [remove the plane, then cluster](../../../02_perception/02_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster).
