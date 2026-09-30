# Iterative closest point

This page explains iterative closest point (ICP): a method that moves one set of
points onto another set of points that shows the same shape. On a robot arm, the
first set is usually a stored model of a part, and the second is a depth scan of
the real part. ICP answers the question "exactly where is the part, and which way
is it turned?". This page shows how ICP works, round by round, on a small example
with real numbers. It also shows when ICP gives a wrong answer, and how you can
tell.

It is for a reader who has read
[nearest-neighbour search](02_nearest-neighbour-search.md), because every round of
ICP runs that search. It also helps to know what a rotation and a shift are, from
[rigid transforms](../02_geometry-and-cameras/03_rigid-transforms.md), but the
page explains what it needs.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [How it works, step by step](#2-how-it-works-step-by-step)
   · [The example: a bracket on a table](#21-the-example-a-bracket-on-a-table)
   · [Step one: pair each model point with its closest scan point](#22-step-one-pair-each-model-point-with-its-closest-scan-point)
   · [Step two: the best move for those pairs](#23-step-two-the-best-move-for-those-pairs)
   · [Repeat until the gap stops shrinking](#24-repeat-until-the-gap-stops-shrinking)
   · [The pseudocode](#25-the-pseudocode)
   · [Point-to-plane: a faster version](#26-point-to-plane-a-faster-version)
3. [Where it is used on a robot arm](#3-where-it-is-used-on-a-robot-arm)
4. [Where it is useful, and where it is not](#4-where-it-is-useful-and-where-it-is-not)
5. [Libraries that provide it](#5-libraries-that-provide-it)
6. [Why ICP, and what it costs](#6-why-icp-and-what-it-costs)
7. [Where to read next](#7-where-to-read-next)

---

## 1. The idea in one sentence

ICP guesses which scan point each model point belongs to by taking the closest
one, moves the model to fit those guesses as well as possible, and repeats until
the model stops moving.

The move ICP finds is a **rigid transform**: a rotation plus a shift, with no
stretching or bending. A part on a table cannot change its shape, so a rigid
transform is the right kind of answer.

Here is an everyday example. You have a paper outline of a key, and you want to
lay it over the real key on a table. You put the paper down roughly where the key
is. You see that each edge of the paper is a little to the left of the matching
edge of the key, so you slide the paper right and turn it a little. Now the edges
are closer, and you can see better which edge goes with which. You slide and turn
again. After a few small moves the paper sits on the key. ICP does the same, with
points instead of edges.

---

## 2. How it works, step by step

### 2.1 The example: a bracket on a table

The example is an L-shaped metal bracket lying flat on a table, seen from above by
a depth camera. It is flat so that the pictures fit on a page. A real scan has
three coordinates per point, and every step below works the same way in 3D.

- The **model** is the bracket's outline as it was drawn: 120 mm long, 80 mm high,
  with arms 30 mm wide. It has one point every 10 mm round the outline, 40 points
  in all.
- The **scan** is what the camera saw. It has one point every 6 mm, 66 points in
  all. Each point is moved by a small random amount, the way a real depth camera's
  points are. The random amount has a standard deviation of 0.8 mm in each
  direction; the **standard deviation** is the typical size of a random error.
- The real bracket is turned 20° from the model and shifted by 30 mm in x and 20 mm
  in y. ICP is not told this. Its job is to find it.
- ICP starts from a first guess: the model exactly where it was drawn, not turned
  and not shifted.

All the numbers on this page come from the diagram script
`docs/diagrams/searching_and_matching.py`, which runs the ICP described here. Run it with `--numbers` to print them.

### 2.2 Step one: pair each model point with its closest scan point

ICP does not know which scan point belongs to which model point. So it guesses:
each model point is paired with the scan point nearest to it. This is a
[nearest-neighbour search](02_nearest-neighbour-search.md) for each model point.
The pairs are called **correspondences**.

The picture below shows the pairs at the start.

![Round one: every model point is paired with its closest scan point](../../images/searching-and-matching/iterative-closest-point/closest-pairs.svg)

Many of these pairs are wrong. The model points along the left edge all reach to
the scan's left edge, which is higher up and turned. Several model points share
one scan point. The mean length of the red lines, called the **mean gap** on this
page, is 15.7 mm.

The pairs are wrong, but they are not random. On the whole they pull the model up,
to the right, and anticlockwise. That is enough, because the next step only needs
to move the model in roughly the right direction.

### 2.3 Step two: the best move for those pairs

Given the pairs, ICP works out the one rotation and shift that brings each model
point as close as possible to its partner. "As close as possible" means that the
sum of the squared distances between partners is as small as it can be. There is
an exact method for this, and it takes three steps.

1. Find the middle of the model points, and the middle of their partners. The
   middle is the average of all the x values and of all the y values. It is called
   the **centroid**.
2. Measure every model point from the model's centroid, and every partner from the
   partners' centroid. Now both sets are centred on the same spot. Find the turn
   that lines the first set up with the second best. A standard piece of linear
   algebra, the **singular value decomposition (SVD)**, gives this turn directly.
   The method is known as the Kabsch method, or the Umeyama method.
3. The shift is whatever then moves the turned model's centroid onto the partners'
   centroid.

Here is the method on three points, small enough to check by hand. The model is a
triangle with corners (0, 0), (40, 0) and (0, 20). The partners are the same
triangle turned 30° and shifted by (10, 5). Their corners are (10.00, 5.00),
(44.64, 25.00) and (0.00, 22.32).

1. The model's centroid is (13.33, 6.67). The partners' centroid is (18.21, 17.44).
2. Centred on their centroids, the two triangles differ only by a turn. The SVD
   finds it: 30.0°.
3. Turning the model's centroid by 30° about the origin moves it to (8.21, 12.44).
   The shift that takes it to (18.21, 17.44) is (10.00, 5.00).

The method finds the turn and the shift exactly, because here the pairs are right.
In ICP the pairs are only guesses, so the move it finds is only partly right. The
model is then moved by it, and ICP goes back to step one.

### 2.4 Repeat until the gap stops shrinking

After each move, the model is closer to the scan, so the closest-point pairs are
better, so the next move is better. The picture below shows the model at the start,
after one round, after four rounds, and at the end.

![The model after rounds 0, 1, 4 and 18](../../images/searching-and-matching/iterative-closest-point/rounds.svg)

After one round the model has barely turned, after four it is part of the way
there, and after 18 it sits on the scan.

The table below gives the numbers after some of the rounds. "Turned" and "shifted"
are the model's total movement since the start; the real answers are 20° and
(30, 20) mm.

| Round | Mean gap (mm) | Turned | Shifted (mm) |
|---|---|---|---|
| 0 (start) | 15.74 | 0.00° | (0.0, 0.0) |
| 1 | 13.16 | 2.14° | (5.3, 6.5) |
| 2 | 11.05 | 4.15° | (8.6, 11.3) |
| 4 | 7.62 | 7.77° | (15.8, 17.4) |
| 8 | 3.80 | 14.14° | (24.7, 20.6) |
| 12 | 1.91 | 18.33° | (28.5, 20.0) |
| 17 | 1.70 | 19.18° | (30.0, 20.3) |
| 18 | 1.70 | 19.18° | (30.0, 20.3) |

ICP needs a rule for when to stop. The rule here is: stop when the mean gap falls by
less than 0.001 mm in one round. That happened after round 18. Real libraries use
the same kind of rule, and also a largest number of rounds, such as 30 or 50, so
that ICP always ends.

The picture below plots the mean gap after each round.

![The mean gap falls quickly, then flattens](../../images/searching-and-matching/iterative-closest-point/gap-per-round.svg)

The gap falls fast for the first twelve rounds, then hardly changes, and that is
when the stop rule ends the loop.

The answer is 19.2° instead of 20°, and (30.0, 20.3) mm instead of (30, 20) mm.
It is close but not exact, for two reasons. The scan's points have noise. And the
model's points and the scan's points do not sit at the same places along each
edge, because one set is spaced 10 mm apart and the other 6 mm. So even at the
right pose, each model point's closest scan point is up to 3 mm along the edge from
it. That is also why the mean gap ends at 1.70 mm, not at the 0.8 mm of noise.

### 2.5 The pseudocode

This pseudocode is written in plain steps, not in any real programming language.

```
icp(model_points, scan_points, first_guess, max_rounds, stop_change, max_pair_distance):
    pose = first_guess
    moved = model_points moved by pose
    previous_gap = infinity
    repeat up to max_rounds times:
        # step one: pairs
        pairs = empty list
        for each point m in moved:
            s = nearest point to m in scan_points          # use a k-d tree built once
            if distance(m, s) <= max_pair_distance:
                add (m, s) to pairs
        gap = mean distance over pairs
        if previous_gap - gap < stop_change: stop
        previous_gap = gap

        # step two: best move for these pairs
        cm = centroid of the m's in pairs
        cs = centroid of the s's in pairs
        R  = the rotation that best lines up (m - cm) with (s - cs)   # SVD
        t  = cs - R * cm
        moved = R * moved + t
        pose  = (R, t) combined with pose
    return pose, gap
```

The scan does not move, so its k-d tree is built once, before the first round.
The `max_pair_distance` test throws away pairs that are too far apart to be real.
It matters when the scan also holds other things, such as the table or a
neighbouring part.

### 2.6 Point-to-plane: a faster version

The version above is called **point-to-point** ICP, because it measures the gap
from each model point to one scan point. It is slow when a surface slides along
itself. In the example, the long flat edges of the bracket took many rounds to
slide into place.

**Point-to-plane** ICP measures the gap from each model point to the flat surface
through its partner instead. This surface is set by the partner's
[normal](02_nearest-neighbour-search.md#3-where-it-is-used-on-a-robot-arm), the
direction straight out of the surface. With this measure, a model point that slides
along the right surface costs nothing, so ICP spends its moves only on the
direction that matters. It usually needs far fewer rounds. It needs normals for the
scan, which means one more k-nearest search per scan point before ICP starts. Open3D
and PCL both provide it.

---

## 3. Where it is used on a robot arm

ICP is used wherever the arm has a rough idea of where something is and needs an
exact one.

- **Finding the exact pose of a known part.** A detector or a simple rule finds
  roughly where a part lies in a bin. ICP then lines the part's computer-aided
  design (CAD) model up with the depth scan, and gives a pose accurate enough to
  grip it at a chosen spot. The robot-arm project
  [v5-pick-glasses](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/docs/problem-1/step2-approaches.md)
  lists matching against known glass models with Open3D's ICP as one of its
  approaches.
- **Finishing a learned pose.** A learned pose model, such as those in Book 6's
  [keypoints and object pose](../../06_neural-network-models/02_seeing-models/05_keypoints-and-object-pose.md),
  gives a pose that is often a few millimetres or a few degrees off. A few rounds
  of ICP from that pose fix the last part of the error. This is a common pairing:
  the learned model gives the first guess, and ICP gives the precision.
- **Joining several views into one cloud.** A camera on the wrist takes pictures
  from several arm poses. The arm's joint readings say roughly where the camera
  was for each picture. ICP lines each new cloud up with the ones before it, to
  remove the small errors left by calibration and by the joints.
- **Following a part that moves a little.** When a part is being pushed or is in
  the gripper, its pose in one frame is a good first guess for the next frame.
  ICP from that guess follows the part with a small number of rounds per frame.
- **Checking a placement.** After the arm sets a part down, a scan and ICP against
  the model say where the part actually ended up. If the pose differs from the
  planned one by more than a limit, the robot can try again.
- **Checking calibration.** If the camera-to-arm calibration is right, a scan of a
  known object at a known place lines up with its model with almost no movement.
  If ICP has to move it by several millimetres, the calibration has drifted. The
  [calibration](../02_geometry-and-cameras/04_calibration.md) page explains the
  calibration itself.

---

## 4. Where it is useful, and where it is not

ICP is precise when it starts close to the answer. The main danger is that it
always returns an answer, even when that answer is wrong. It stops when the gap
stops shrinking, and that can happen at a wrong pose.

The picture below shows this. The same bracket is scanned twice: once turned 20°,
and once turned 120°. ICP starts from the same first guess both times.

![A start 20 degrees off ends right; a start 120 degrees off ends stuck and wrong](../../images/searching-and-matching/iterative-closest-point/wrong-start.svg)

From 20° away, ICP finds the bracket. It also found it from 45°, 60° and 90° away,
after 25 to 36 rounds. From 120° away, it stops after 9 rounds with
the model turned −5.9°, lying across the scan. Its mean gap is 13.7 mm, against
1.7 mm for the good result. That is the sign to watch for: a final gap that is much
bigger than the camera's noise. Such a stuck answer is called a **local minimum**:
a pose from which every small move makes the gap worse, although it is not the
best pose overall.

The table below lists the common problems. Read each row as: what goes wrong, the
sign you see, and what people use instead.

| Problem | The sign you see | What people use instead |
|---|---|---|
| The first guess is too far off. How far is too far depends on the shape: the diagram script's bracket was found from 90° away, but not from 100° | the final gap is much larger than the camera noise | a global method first, such as random sample consensus ([RANSAC](../04_fitting-and-estimation/03_ransac.md)) on matched surface features, or several ICP runs from different starting turns, keeping the best |
| The part is symmetric, such as a cylinder or a square plate | the gap is small, but the turn about the symmetry axis is random from run to run | accept that the turn is unknown, or use colour or a marking, as in coloured ICP |
| The scan also holds the table or other parts | the model is pulled towards the table or a neighbour | cut the part out of the scan first, and reject pairs further apart than a limit |
| Only part of the object is visible | the model slides to cover the missing side | reject far pairs; use a model of only the side the camera can see |
| A large flat surface, such as a box lying on a table | the model slides along the surface and never settles, or settles in the wrong place along it | point-to-plane ICP helps with speed; a feature such as an edge or a hole is needed to fix the position |
| The model is in millimetres and the scan in metres | a nonsense answer after one round | check the units before calling ICP |
| Many rounds on large clouds | ICP is too slow for the camera rate | downsample both clouds to a point every few millimetres first; use point-to-plane |

---

## 5. Libraries that provide it

ICP is part of every major point cloud library. The table below lists well-known
ones. The "function or class" column gives the name to look up in each library's
documentation.

| Library | Languages | Function or class | Note |
|---|---|---|---|
| Open3D | Python, C++ | `open3d.pipelines.registration.registration_icp`, with `TransformationEstimationPointToPoint` or `TransformationEstimationPointToPlane` | also has coloured ICP, and global registration with RANSAC on features |
| Point Cloud Library (PCL) | C++ | `pcl::IterativeClosestPoint`, `pcl::GeneralizedIterativeClosestPoint` | the generalised version models each point as a small patch of surface |
| OpenCV (contrib) | C++, Python | `cv::ppf_match_3d::ICP`, in the `surface_matching` module | paired in that module with a global matcher for a first guess |
| trimesh | Python | `trimesh.registration.icp` | small and easy; aligns points to a mesh |
| Eigen | C++ | `Eigen::umeyama` | only the best-move step (section 2.3), for writing your own ICP |

Book 3's [tools and libraries](../../03_frameworks/01_tools-and-libraries.md#9-perception-camera-drivers-opencv-and-open3d)
explains where Open3D fits into a robot arm's software.

---

## 6. Why ICP, and what it costs

This section answers four questions: what the technique is, what it does for you,
why it rather than the obvious alternative, and what it costs.

ICP moves a model point set onto a scanned point set by pairing closest points and
fitting a rigid move, over and over. It turns a rough pose into an exact one, often
to within a millimetre or a degree, using only the shape of the part.

The obvious alternative is to try every pose: every turn in steps of one degree and
every shift in steps of one millimetre, and keep the pose with the smallest gap. In
3D that is millions of poses, each checked against the whole scan, which is far too
slow for a robot. The second alternative is to match distinctive features, such as
corners, between the model and the scan, and fit the pose to those matches with
RANSAC. Feature matching does not need a first guess, which is its great advantage.
But it is less exact, because it uses only a few points. So the usual answer is to
use both: features for the first guess, then ICP to make it exact. A learned pose
model can take the place of the features.

The costs are these. ICP needs a first guess, and it gives a confident wrong answer
when the guess is poor, so you must check the final gap. It needs a model of the
part, which means a CAD file or an earlier scan. It needs a clean scan, with the
table and other objects cut away. It runs a nearest-neighbour search for every
model point in every round, so it needs downsampled clouds to run at camera rate.
And it cannot tell apart poses that a symmetric part makes look the same.

---

## 7. Where to read next

- [Nearest-neighbour search](02_nearest-neighbour-search.md) is the search inside
  every ICP round.
- [Rigid transforms](../02_geometry-and-cameras/03_rigid-transforms.md) explains
  the rotation and shift that ICP returns, and how to chain it with the camera's
  pose to get the part's pose in the arm's frame.
- [RANSAC](../04_fitting-and-estimation/03_ransac.md) gives a first guess that does
  not need to be close.
- [Least-squares fitting](../04_fitting-and-estimation/02_least-squares-fitting.md)
  explains "the smallest sum of squared distances", the measure ICP's best-move
  step uses.
- Book 6's [keypoints and object pose](../../06_neural-network-models/02_seeing-models/05_keypoints-and-object-pose.md)
  finds a pose with a learned model, and
  [scene reconstruction](../../06_neural-network-models/03_3d-models/04_scene-reconstruction.md)
  builds a 3D scene from many views with learning.
- [Assignment and matching](04_assignment-and-matching.md) pairs whole objects
  rather than points, with a strict one-to-one rule that ICP does not have.
