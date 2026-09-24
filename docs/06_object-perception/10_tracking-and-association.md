# Tracking and association: deciding it is the same object

The moment a robot arm looks twice, it has a problem that looking once did not
create. The first picture contained four objects. The second picture contains
four objects. Which of the second four is which of the first four?

That question is called **data association**, and this document is about it.
Association is the step that takes two sets of detections and decides which
detection in one set refers to the same physical object as which detection in the
other. It sits between perception and everything downstream, and it is almost
never drawn on a pipeline diagram, because the diagram shows one arrow going from
"detect" to "grasp" and the arrow silently assumes the answer.

The reason it deserves a document of its own is the shape of its failure. A
detector that fails returns nothing, and nothing is an honest answer that the rest
of the system can act on. Association that fails returns a **confident position
for an object that is not there**: object A's identity attached to object B's
coordinates, with a covariance that says three millimetres. The arm then goes to
the right place for the wrong object and does what object A's plan said to do.
Nothing in the numbers looks wrong, which is why this is the failure that takes
longest to find.

## Who this is for

Someone who has a working detector and has started taking more than one picture.
That happens sooner than people expect: a second view to break a symmetry, a
fixed camera above the table and a camera on the wrist, or simply a detector
running at ten frames a second while the scene sits still. Any of those is an
association problem.

You need [the overview](01_overview.md) and no more than that. You do not need to
have used a Kalman filter; section 3 explains what one is. Every number here is
computed from the repository's own camera, which has a focal length of
`fx = fy = 277.1` pixels on a 320 by 240 sensor, and every step of the arithmetic
is shown.

## Contents

1. [Why matching is harder than it sounds](#1-why-matching-is-harder-than-it-sounds)
2. [Two problems that people treat as one](#2-two-problems-that-people-treat-as-one)
3. [The methods, cheapest first](#3-the-methods-cheapest-first)
4. [Gating is the whole trick](#4-gating-is-the-whole-trick)
5. [What to do when association fails](#5-what-to-do-when-association-fails)
6. [Identity across a grasp](#6-identity-across-a-grasp)
7. [The libraries, and the thirty lines](#7-the-libraries-and-the-thirty-lines)
8. [What is specific to a robot arm](#8-what-is-specific-to-a-robot-arm)

---

## 1. Why matching is harder than it sounds

### 1.1 The two numbers, and only one of them is a problem

Take `N` detections in the first picture and `M` in the second. There are two
different counts people quote, and they mean very different things.

The first is the number of **pairs you have to score**, which is `N × M`. Every
detection in one set could in principle be any detection in the other, so a
complete cost table has that many entries. This number grows quadratically and it
is not a problem at the scale a robot arm works at.

The second is the number of **complete one-to-one assignments**, which for
`N = M = n` is `n` factorial. This is the number of distinct ways to pair every
object in one set with exactly one object in the other, and it is the number
people mean when they say association is combinatorial. It grows faster than any
polynomial.

The table below is those two counts against the cost of the standard algorithm,
which runs in time proportional to `n` cubed. Read it as: how many objects, how
big the cost table is, how many complete answers exist, and how many steps the
solver actually takes.

| Objects `n` | Pairs to score, `n × n` | Complete assignments, `n!` | Solver steps, about `n³` |
| --- | --- | --- | --- |
| 5 | 25 | 120 | 125 |
| 10 | 100 | 3,628,800 | 1,000 |
| 12 | 144 | 479,001,600 | 1,728 |
| 20 | 400 | 2.43 × 10¹⁸ | 8,000 |

The factorial column is why nobody enumerates the possibilities. The last column
is why that does not matter. Twenty objects need about eight thousand operations,
which is microseconds. **The computational cost of association was solved in 1955
and has not been a problem since.** If you are reading a tutorial whose main
concern is how to make association fast, it is answering a question that is no
longer open.

### 1.2 The count that actually rises is the number of ways to be wrong

Here is the growth that matters. Section 4 derives a **gate**, which is a
distance beyond which a match is refused outright. On the repository's camera at a
340 mm working distance the gate comes out at 34.6 mm. Any other object that
falls inside that radius of the one you are matching is a candidate for a wrong
match.

Take a table 600 mm by 400 mm, which is 240,000 mm² of working area, and `N`
objects scattered on it at random. A gate of radius 34.6 mm covers a disc of
`π × 34.6²` = 3,761 mm², which is 1.567 per cent of the table. The expected
number of ordered pairs of objects close enough to be confused is therefore
`N × (N − 1) × 0.01567`.

Read the table below as: how many objects are on the table, and how many
confusable pairs you should expect among them, on average, for the two gate sizes
section 4 arrives at.

| Objects on the table | Confusable pairs, 34.6 mm gate | Confusable pairs, 9.29 mm gate |
| --- | --- | --- |
| 5 | 0.31 | 0.023 |
| 10 | 1.41 | 0.102 |
| 20 | 5.96 | 0.429 |
| 40 | 24.4 | 1.76 |

Going from five objects to twenty multiplies the objects by four and the
confusable pairs by nineteen. That quadratic term is the real scaling law of
association, and it is the reason a system that is flawless on a demonstration
with three blocks starts producing inexplicable behaviour on a tray of twenty.
The detector did not get worse. The chances to be wrong went up nineteen-fold.

### 1.3 The optimal answer is not the same as the right answer

An assignment algorithm returns the cheapest complete pairing. It has no way to
know whether the cheapest pairing is the true one, and when objects are close
together the true pairing is frequently not the cheapest.

Here is that stated exactly, for the simplest possible case. Two tracks, two
detections, separated by a vector `s`. The correct pairing costs the sum of the
two squared measurement errors. The swapped pairing costs that plus
`2|s|² + 2 s·(e₁ − e₂)`, where `e₁` and `e₂` are the two errors. The swap is
cheaper whenever the component of `e₁ − e₂` along `s` is more negative than
`|s|`. That component is a Gaussian with a standard deviation of `σ√2`, so the
probability that the optimal assignment is the wrong one is the normal
distribution evaluated at `−|s| / (σ√2)`.

With the per-observation error of 9.38 mm that section 4 derives, that gives the
following. Read it as: how far apart two objects are, and how often the optimal
assignment swaps them.

| Separation | Chance the optimal assignment is the swapped one |
| --- | --- |
| 20 mm | 6.6 per cent |
| 40 mm | 0.13 per cent |
| 70 mm | 0.000007 per cent |

Two objects twenty millimetres apart get swapped one time in fifteen, by an
algorithm that is provably optimal, on measurements that are within
specification. Nothing is broken. The information to tell them apart was never in
the measurements.

### 1.4 What a wrong match costs, in numbers

The damage is not the single wrong reading. It is what the filter downstream does
with it.

A tracker's job is to combine many measurements of the same object into one
better estimate. With `k` independent measurements of a stationary object, each
with standard deviation `σ`, the combined estimate has standard deviation
`σ / √k`. After ten frames the repository's 9.38 mm per-observation error becomes
`9.38 / √10` = **2.97 mm**. The system now reports a position it believes to
three millimetres.

Suppose one of those ten measurements was actually a different object 20 mm away.
The mean is pulled by `20 / 10` = **2.0 mm**, and the reported uncertainty is
still 2.97 mm, because the filter counted ten good measurements and does not know
otherwise. The error is inside the stated confidence interval, so no check based
on the filter's own numbers will ever fire.

Now suppose the wrong match persists — the track locks onto the other object.
Every subsequent frame confirms the new object, the uncertainty keeps shrinking,
and the track ends up reporting the wrong object's position with high confidence
while carrying the right object's identity, its class, and its grasp plan. **A
Kalman filter does not recover from a sustained wrong association; it becomes
more certain of it.**

From outside, this presents exactly like rungs 3 and 4 of the
[diagnosis ladder](07_making-it-work.md#3-when-it-does-not-work-a-diagnosis-ladder)
— the arm goes to a place that is wrong by a few millimetres in a way that looks
like calibration. It is not calibration, and the two most common responses, a
better model and a re-calibration, both leave it exactly where it was.

## 2. Two problems that people treat as one

The word "matching" covers two situations that share a vocabulary and almost
nothing else. Conflating them is why people reach for a video tracker to solve a
stereo problem, and for a geometric check on a problem that has no geometry in
it.

### 2.1 Matching two views taken at one moment: geometry answers it

Two cameras looking at the same scene at the same instant, or one wrist camera at
two poses with a stationary scene, give you a hard constraint. It is called the
**epipolar constraint**: given the relative pose between the two viewpoints, a
point seen at one pixel in the first image must lie somewhere on a single
straight line in the second image. Not a region — a line. The search drops from
two dimensions to one.

For a wrist camera the relative pose comes free, from the arm's forward
kinematics and the hand-eye calibration, so the line is available without any
extra work. Its width is set by how well you know that pose. A rotation error of
one degree moves a point at 340 mm by `340 × tan(1°)` = 5.935 mm, which on the
repository's camera is `5.935 × 277.1 / 340` = **4.84 pixels**. So the line is
really a band about ten pixels wide.

That band is `320 × 10` = 3,200 pixels out of the 76,800 in a 320 by 240 image,
which is **4.17 per cent**. Geometry alone eliminates ninety-six per cent of the
image before any appearance comparison happens, and it does so with no model, no
training and no assumption about what the objects are.

Geometry fails in exactly one situation, and it is a common one: when several
candidate objects lie along the same epipolar line. That happens when objects are
arranged along the direction of the baseline between the two viewpoints, which on
a table of similar parts in a row is the normal case rather than the exception.
The cure is to move the second viewpoint so the baseline is across the row rather
than along it, which is the same reasoning as
[baseline, not count](08_the-wrist-camera.md#5-baseline-not-count).

### 2.2 Matching across time: only prediction answers it

Between two pictures taken at different moments, nothing geometric links the two
sets of detections. The object may have moved. There is no line to search along,
no constraint to satisfy, and no amount of calibration that supplies one.

The only thing you have is that the world has inertia. An object that was here a
tenth of a second ago is near here now, and if it was moving it is near where its
velocity says it should be. That is a **prediction**, not a constraint: it can be
wrong, and its usefulness is exactly how much it narrows the region you search.

This distinction has a practical consequence for a robot arm that is worth
stating directly. A fixed camera watching a still table has a trivial time
problem, because nothing moves between frames, so a very tight gate works. A
wrist camera moving between viewpoints has a hard problem dressed up as an easy
one: the objects did not move, but the **camera** did, so every detection lands
somewhere completely different in the image. Association in the image plane is
meaningless for a wrist camera. It has to be done in the robot's frame, after
transforming both sets of detections through the arm's pose — which is why tf2
and the time synchronisation machinery are part of the association stack and not
an afterthought.

### 2.3 Why the conflation is expensive

Read the table as: the two cases, what actually constrains the match, what is
left ambiguous, and what a wrong match does.

| | Constrained by | Still ambiguous when | A wrong match gives you |
| --- | --- | --- | --- |
| **two views, one moment** | the epipolar line, from known relative pose | several objects lie along that line | one wrong 3D point, now — a bad triangulation that is usually obviously bad |
| **two moments, one or more cameras** | nothing. Only a prediction from a motion model | the prediction is no tighter than the object spacing | a track that carries the wrong identity forward and confirms itself every frame |

The right-hand column is the whole argument for keeping them apart. A bad stereo
match produces a point at an implausible depth, which a sanity check catches
immediately. A bad temporal match produces a perfectly plausible point that is
simply the wrong object, and it persists.

## 3. The methods, cheapest first

Each of these adds one thing to the one before it. In almost every robot arm
project the right answer is one of the first three.

### 3.1 Nearest neighbour with a gate

**What it is.** For each object in the first set, take the nearest object in the
second set, and refuse the match if it is further away than the gate. That is the
whole method.

**Why this rather than something cleverer.** Because when the objects are further
apart than the measurement error, it is already correct, and section 1.3 gives
you the arithmetic to check whether that is true of your scene. Below about four
standard deviations of separation, nothing more sophisticated helps either; the
information is not there.

**What it costs you.** Two things. It is greedy, so the result depends on the
order you process the objects in, and a different order can give a different
answer on the same data. And two objects can both claim the same nearest
neighbour, which leaves you with a match the arithmetic never noticed was
double-booked.

Five jobs it suits:

- a table-top scene with fewer than about ten well-separated objects
- a fixed camera on a static scene, where the gate can be very tight
- matching a fresh detection against a single known object, where there is no
  assignment problem at all
- the first version of anything, so that you find out whether you have a problem
  before building for one
- any case where you can cheaply re-detect, so that refusing a match is free

Five jobs it cannot do:

- guarantee a one-to-one result, which it simply does not attempt
- give a repeatable answer independent of processing order
- handle a dense scene, where its greedy choices compound
- handle objects entering and leaving, without counting logic bolted on top
- use anything other than distance, such as size or colour, without a cost
  function that section 3.2 is the natural home for

### 3.2 The Hungarian algorithm, for the optimal assignment

**What it is.** An algorithm that takes the full `N × M` table of costs and
returns the one-to-one pairing whose total cost is lowest. It was published by
Harold Kuhn in 1955 and is also called the Kuhn–Munkres algorithm. In tracking
papers the same idea is called **global nearest neighbour**, to distinguish it
from the greedy version above.

**Why this rather than nearest neighbour.** Because it considers the assignment
as a whole. Where two objects are close together, greedy matching lets the first
one processed take the shared detection and leaves the second one stranded;
global matching notices that swapping them costs less overall. It also guarantees
one-to-one, which greedy matching does not.

**What it costs you.** Almost nothing computationally — section 1.1 shows why.
What it costs you is a false sense of security, because "optimal" sounds like
"correct" and section 1.3 shows that it is not. It also needs a real cost
function rather than just a distance if you want to bring in size or appearance,
and choosing the weights between those terms is a genuine judgement with no
principled answer.

In Python this is `scipy.optimize.linear_sum_assignment`, which implements the
shortest augmenting path algorithm for the rectangular assignment problem, as
documented in [its own source
file](https://github.com/scipy/scipy/blob/main/scipy/optimize/rectangular_lsap/rectangular_lsap.cpp).
Rectangular matters: it handles `N ≠ M` directly, assigning `min(N, M)` pairs and
leaving the rest over, which is exactly the behaviour you want when objects
appear and disappear.

Five jobs it suits:

- any scene dense enough that two tracks compete for one detection
- matching across a wide baseline, where several candidates are plausible
- combining several cues into one cost — distance, size, colour, class
- rectangular problems, where the two sets are different sizes
- producing a repeatable answer that does not depend on iteration order

Five jobs it cannot do:

- tell you that its optimal answer is wrong, which is section 1.3's point
- express a preference for leaving something unmatched, without the gate trick in
  section 7.3
- handle one object splitting into two detections, or two merging into one
- use a cost that is not a sum over independent pairs, which rules out reasoning
  about the arrangement as a whole
- do anything about objects that are genuinely identical and genuinely adjacent

### 3.3 A predictor: constant velocity, then the Kalman filter

**What it is.** A model of where the object will be at the time of the next
picture, so the gate is centred on the prediction rather than on the last
observation. The cheapest useful version is **constant velocity**: assume the
object keeps doing what it was doing, so the predicted position is the last
position plus the estimated velocity times the elapsed time.

A **Kalman filter** is the same idea with the bookkeeping done properly. It
carries a state — position and velocity — and a covariance matrix that says how
uncertain each part of that state is. At each step it predicts the state forward,
growing the covariance to reflect that prediction is less certain than
observation, then folds in the new measurement weighted by the relative sizes of
the two uncertainties. Its output is not just a better position but an explicit
statement of how uncertain that position is, and that statement is what section 4
turns into a gate.

**Why this rather than gating around the last position.** Because for a moving
object, gating around the last position forces the gate to be at least as big as
the distance the object travels between frames. An object crossing at 100 mm/s
with frames 100 ms apart moves 10 mm, so a static gate has to grow by 10 mm to
avoid losing it, and section 1.2 shows what growing the gate does to the
confusable-pair count. Prediction removes that term instead of absorbing it.

**What it costs you.** A motion model that is wrong when the object does
something the model does not allow, and the filter's confidence is highest
exactly when the model has been right for a while — which is the moment before an
object changes direction. It also adds state, so a bug now persists across frames
instead of being confined to one.

Five jobs it suits:

- anything on a conveyor, where constant velocity is nearly exact
- filling in a frame where the detector missed, by coasting on the prediction
- smoothing a noisy detector, which section 1.4 quantifies as `σ / √k`
- supplying the covariance that a proper gate needs
- deciding when to give up on a track, from how far the covariance has grown

Five jobs it cannot do:

- predict an object that a person or another arm has just picked up
- help at all on a static scene, where the prediction is just the last position
- notice that it has locked onto the wrong object, which is section 1.4
- model a rotating object's orientation without extra care about angle wrap
- survive being fed measurements at irregular intervals, unless you use the real
  timestamps rather than a nominal frame rate — the same discipline as
  [pose staleness](08_the-wrist-camera.md#1-what-changes-when-the-camera-is-on-the-arm)

### 3.4 Appearance descriptors

**What it is.** A short summary of what an object looks like, computed from its
pixels, compared between the two sets so that the cost function knows about more
than position. The cheap version is a colour histogram: count the pixels of the
mask into bins by colour, normalise, and compare two histograms with a distance
measure. The classical version is a set of keypoint descriptors such as ORB,
which survive rotation and scale change.

**Why this rather than more geometry.** Because when two objects are inside each
other's gates, geometry has nothing left to say, and appearance is the only
remaining channel. A red block and a blue block 15 mm apart are trivially
separable by colour and hopeless by position.

**What it costs you.** It is a cost you pay every frame on every detection, and
on a wrist camera it is fragile in a specific way: the arm shadows the object, so
the same object photographed from two arm poses has two different histograms. It
is also worthless in the case robotics cares most about, which section 3.5
returns to.

Five jobs it suits:

- objects that genuinely differ in colour or texture
- re-acquiring an object after it was hidden, where position has gone stale
- matching across a wide baseline, where the position prior is weak
- sorting tasks, where appearance is the thing you are sorting on anyway
- breaking ties that the gate has left open, as a second-stage cost

Five jobs it cannot do:

- distinguish identical objects, which is the usual industrial case
- survive a lighting change, which a moving arm causes by shadowing
- survive a viewpoint change on a non-uniform object, where a histogram of the
  front and a histogram of the back have nothing in common
- work on a transparent object, whose pixels are mostly the background
- work on a small or distant object — at 340 mm a 40 mm object is 33 pixels
  across, and a histogram of a thousand pixels is a noisy statistic

### 3.5 Learned re-identification

**What it is.** A neural network that turns a crop of an object into a fixed-length
vector, trained so that two crops of the same object land close together and
crops of different objects land far apart. The distance between vectors becomes a
term in the cost function. The technique comes from person and vehicle
re-identification in surveillance, and that origin decides everything about what
it is good for.

**Why this rather than a colour histogram.** Because it tolerates viewpoint,
scale and lighting changes that destroy a histogram, and because it learns which
differences matter rather than being told. On a scene of visually distinct
objects viewed from very different angles, it is markedly better.

**What it costs you**, and this is the part that decides it for most arm
projects. Re-identification networks are trained on the assumption that
individuals differ. People have different clothes; cars have different colours and
number plates. **Factory parts are manufactured to be identical, and warehouse
stock comes in cases of the same item.** On five identical bolts, a
re-identification embedding is not slightly worse than it is on people — it is
exactly as useless as a colour histogram, because there is no appearance
difference to encode. It also brings a model that has never seen your objects, a
download, and an inference cost every frame.

Five jobs it suits:

- a mixed scene of visually distinct objects — a kitchen, a desk, recycling
- re-acquiring an object after a long gap, where all motion information has
  expired
- handing a track between two cameras with very different viewpoints
- tracking people or vehicles near the robot, for safety rather than for grasping
- scenes where a detector already runs on a graphics card, so the marginal cost
  is small

Five jobs it cannot do:

- distinguish identical parts, which is the case robotics most often faces
- give calibrated distances — embedding distances have no units and no
  probability attached, so they cannot be gated the way section 4 gates position
- run at full frame rate on a small on-robot computer alongside the detector
- transfer cleanly from its training domain to a bin of machined metal
- explain a match, which matters when you are trying to work out why the arm went
  to the wrong place

### 3.6 Mask propagation in video, and where SAM 2 actually fits

[Models that find](04_models-that-find.md#13-promptable-segmenters-the-segment-anything-family)
covers the Segment Anything family, and SAM 2 in that family adds video. It is
worth placing precisely, because "SAM 2 does tracking" is true in a sense that
does not cover the problem this document is about.

**What it does.** You prompt it once, on one frame, with a point or a box. It
then propagates that mask through the rest of the video, carrying a memory of the
object's appearance, and it is very good at it — through partial occlusion,
through deformation, and through the object leaving and re-entering the frame. The
identity it maintains is real. It is [Apache-2.0 in both code and
weights](https://github.com/facebookresearch/sam2), and it reaches an Apple
Silicon Mac through `transformers` as described in
[what runs on a Mac](06_licences-and-platforms.md#3-what-runs-on-an-apple-silicon-mac).

**What it does not do.** It works on a **continuous video from one camera**. A
wrist camera that stops at viewpoint one, takes eight frames, moves 200 mm, and
takes eight more is not a video in that sense: the intervening motion is exactly
the part SAM 2's memory has no frames for. It also produces masks in the image
plane and no position in the robot's frame, and it attaches no uncertainty to
anything, so there is nothing to gate on and nothing to feed a filter. It solves
mask propagation. It does not solve data association.

Five jobs it suits:

- a fixed overhead camera watching a scene continuously, where it can replace a
  detector-plus-tracker pair outright
- following one object a human pointed at, through a whole manipulation
- labelling video data, where one click per object produces masks for every frame
- objects that change shape, such as cloth or food, where a box tracker has
  nothing stable to follow
- occlusion within a continuous sequence, which is where its memory earns its keep

Five jobs it cannot do:

- bridge the gap while the arm travels between two viewpoints
- associate detections between two different cameras
- give a 3D position, or any uncertainty on one
- run at frame rate on a small on-robot computer
- decide, on its own, which objects to follow — something still has to prompt it,
  which is the same limitation the whole Segment Anything family has

## 4. Gating is the whole trick

A **gate** is a distance beyond which a match is refused outright. Inside the
gate, the algorithm picks the best candidate. Outside it, the algorithm returns
nothing at all, and nothing is a result the rest of the system is expected to
handle.

Everything in this document depends on the gate being the right size, and the
right size is derivable rather than a matter of taste. This section derives it
from the repository's own
[error budget](01_overview.md#8-where-the-millimetres-go).

### 4.1 The error budget, restated as a position error

The error budget in the overview is about the measured **width** of an object.
For association what matters is the error in its **position**, so the same four
causes have to be re-worked. A detection's position in the camera frame is

```
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = the depth reading
```

so the four causes contribute as follows. The scene is the repository's standard
one: a detection 60 pixels from the principal point, which at 340 mm is
`60 × 0.340 / 277.1` = 73.6 mm off the optical axis, seen by a depth camera whose
error is 7 mm at that range — the figure the overview uses for a RealSense D405
at two per cent of range.

Read the table as: the cause, the arithmetic, and how many millimetres of
position error it produces on its own.

| Cause | Arithmetic | Error |
| --- | --- | --- |
| the mask centroid is one pixel out | `1 × 0.340 / 277.1` | 1.227 mm, across the ray |
| the depth reading is 7 mm out, along the ray | direct | 7.000 mm, along the ray |
| the same depth error, sideways | `60 × 0.007 / 277.1` | 1.516 mm, across the ray |
| hand-eye calibration one degree out | `340 × tan(1°)` | 5.935 mm, in the robot frame |

Combining them in quadrature, and treating each as one standard deviation — which
is an assumption worth being explicit about, since the published figures are
typical errors rather than measured distributions:

```
sqrt(1.227^2 + 7.000^2 + 1.516^2 + 5.935^2) = 9.38 mm
```

**One observation of an object's centre is good to about 9.4 mm.** That is the
number everything below is built from, and the striking thing about it is how
little of it comes from perception. The mask contributes 1.2 mm; the depth sensor
and the calibration contribute the rest.

### 4.2 What cancels between two observations, and what does not

A gate is applied to the **difference** between two positions, not to either one.
That means an error which is identical in both observations cancels exactly and
should not be in the gate at all.

The hand-eye calibration error is systematic in the sense set out in
[the wrist camera](08_the-wrist-camera.md#1-what-changes-when-the-camera-is-on-the-arm):
it takes the same value every time, so long as the arm is in the same place. Two
detections in the same picture, or in two pictures taken from one arm pose, share
it completely. Two detections from different arm poses do not, because the same
rotation error projects differently at a different pose.

That gives two different per-observation errors:

```
same arm pose:       sqrt(1.227^2 + 7.000^2 + 1.516^2)            = 7.27 mm
different arm poses: sqrt(1.227^2 + 7.000^2 + 1.516^2 + 5.935^2)  = 9.38 mm
```

This is worth noticing because it inverts an instinct. A better hand-eye
calibration is the single most valuable improvement you can make to absolute
accuracy, and it does **nothing at all** for association between frames taken
from one arm pose. Conversely, moving the arm between two pictures makes
association harder for a reason that has nothing to do with the pictures.

### 4.3 From a standard deviation to a gate

The difference of two independent observations, each with standard deviation `σ`,
has standard deviation `σ√2`. The distance between them in three dimensions,
divided by that standard deviation, is distributed as the square root of a
chi-square with three degrees of freedom, so a gate that admits the true match 99
per cent of the time is set at `sqrt(11.345)` = 3.368 standard deviations.

That gives the two gates below. Read the table as: which situation, the
per-observation error from section 4.2, the gate radius, and the resulting rule
about how far apart objects have to be.

| Situation | `σ` per observation | `σ√2` | Gate at 99 per cent | Objects must be at least |
| --- | --- | --- | --- | --- |
| both pictures from one arm pose | 7.27 mm | 10.28 mm | **34.6 mm** | 69.2 mm apart |
| pictures from different arm poses | 9.38 mm | 13.27 mm | **44.7 mm** | 89.4 mm apart |

The last column is the consequence people do not expect, and it follows
immediately: if two objects are closer together than twice the gate, each one
falls inside the other's gate, and the gate can no longer refuse the wrong match.
**A 34.6 mm gate means you cannot separate objects closer than 69 mm centre to
centre by position alone.** Seven centimetres is a lot. A tray of parts, a bowl of
fruit or a row of test tubes is well inside it.

### 4.4 The error is not the same in every direction, and using that is worth 14 times

Section 4.3 treated the error as the same in every direction, which it is not.
Look again at the four causes: 7 mm of it is along the camera's line of sight and
about 1.95 mm of it is across the line of sight.

```
across the ray: sqrt(1.227^2 + 1.516^2) = 1.95 mm
along the ray:                            7.00 mm
```

The error is an elongated ellipsoid whose long axis points at the camera, three
and a half times longer than it is wide. Gating with a sphere big enough to contain it wastes almost all of
its volume. Using the covariance properly — which is what a **Mahalanobis
distance** is, a distance measured in units of the standard deviation along each
axis — gives an ellipsoid with these semi-axes:

```
across the ray: 3.368 * sqrt(2) * 1.95 =  9.29 mm
along the ray:  3.368 * sqrt(2) * 7.00 = 33.34 mm
```

The sphere from section 4.3 has volume `(4/3)π × 34.61³` = 173,711 mm³. The
ellipsoid has volume `(4/3)π × 9.29² × 33.34` = 12,052 mm³. **The ellipsoid is
14.4 times smaller for the same 99 per cent coverage**, and section 1.2 shows that
cutting the gate volume by 14 cuts the confusable-pair count by the same factor.
This is the highest-value single change in the whole document and it costs three
lines of code.

It also produces a piece of camera-placement advice that is not obvious. If the
camera looks straight down at the table, the long axis of the error points
vertically, and the footprint on the table is a disc of radius 9.29 mm — so the
minimum separation drops from 69.2 mm to **18.6 mm**. If the camera looks in at
45 degrees, the long axis projects onto the table with length
`33.34 × cos(45°)` = 23.6 mm, and the minimum separation is 18.6 mm across the
viewing direction but 47.2 mm along it. **Point the camera along the axis you measure
worst**, so that your worst axis is the one the table does not use.

### 4.5 When the gate cannot be made small enough

Sometimes the arithmetic says your objects are closer together than your gate,
and there are only four honest responses.

**Reduce the error that dominates.** Section 4.1 shows the depth reading is the
largest term at 7 mm. A closer working distance improves the pixel term
proportionally but not the depth term, so on this camera depth is the thing to
attack — which usually means a better sensor rather than better software.

**Turn the geometry to your advantage**, as section 4.4 describes, by putting the
long axis of the error where the objects are not spread out.

**Add a second cue**, from section 3.4 or 3.5, and accept that it fails on
identical objects.

**Separate the objects.** Spread them out with the arm before looking. This is
the same move that
[occlusion and clutter](07_making-it-work.md#4-occlusion-and-clutter) recommends,
and it is usually cheaper than everything above it.

What is not on the list is widening the gate. A gate wide enough to always find
the true match is a gate that cannot refuse a false one, which converts a
recoverable failure into an unrecoverable one — which is section 5.

## 5. What to do when association fails

### 5.1 The four outcomes, and the two that get forgotten

An association step has four possible outcomes per object, and most code written
in a hurry handles two of them.

A **match** pairs an existing track with a new detection; the track updates.

A **new detection with no track** means something appeared: an object was placed
on the table, or the previous frame's detector missed it. The correct response is
to start a new track, marked **tentative** — it exists, but nothing acts on it
yet.

A **track with no detection** means something disappeared: it was picked up, it
went behind something, or the detector missed it. The correct response is to
**coast** — keep predicting the track forward, grow its uncertainty, and act on
it only if you must.

A **gated-out pair** is the outcome that is easy to lose. The solver found a
pairing but the gate refused it. That is not the same as either of the two above,
and it is worth logging separately, because a rising count of gated-out pairs is
the earliest warning that your gate and your scene no longer fit each other.

The standard bookkeeping is counting. A tentative track becomes confirmed after
it has been matched in some number of consecutive frames — three is the usual
choice — and a coasting track is deleted after some number of consecutive misses.
Both numbers are yours to set and both have an obvious trade: confirm slowly and
you are late to act; delete slowly and you accumulate ghosts.

### 5.2 The asymmetry, which is the rule to remember

Here is the rule this whole document is arranged around.

**Refusing to match is recoverable. A wrong match is not.**

When you refuse a match, you have a track with no detection and a detection with
no track. The costs are a frame of delay, a slightly wider search next time, and,
at worst, taking another picture. On a wrist camera another frame from the same
pose costs 11 milliseconds, as
[the wrist camera](08_the-wrist-camera.md#2-how-many-pictures-each-task-needs)
sets out. Recovery is cheap because the situation is visible: something is
unmatched, and unmatched things can be counted, logged and looked at.

When you accept a wrong match, you get a track carrying one object's identity and
another object's position, section 1.4's filter makes it more confident every
frame, and nothing anywhere in the system is in an unusual state. There is no
count to watch and no flag to check. The error only surfaces when the arm acts on
it, which is the most expensive place for it to surface.

The two are not symmetric and should not be traded off as though they were. When
in doubt, set the gate from the arithmetic in section 4 and let it refuse.

### 5.3 A refusal has to be visible

Refusing is only useful if the refusal reaches a person or a report.
[Declining, as a mechanism](07_making-it-work.md#6-declining-as-a-mechanism-rather-than-an-intention)
sets out the pattern this repository uses, and association is a natural fit for
it: an unresolvable association raises with the sentence
`"two candidate objects 18 mm apart, inside a 34.6 mm gate — cannot tell them
apart"`, one layer catches it, marks that object as not to be retried, and moves
on. A wrong match produces no sentence at all, which is exactly why the gate has
to do the work.

Three counts are worth keeping in every association step, because together they
tell you whether the gate is right: matches, gated-out pairs, and tracks deleted
after coasting. A gate that is too tight shows up as gated-out pairs and deleted
tracks rising together. A gate that is too loose shows up as neither of those
rising, and as the arm occasionally doing something inexplicable — which is why
you cannot tune the gate from the counts alone, and have to derive it.

## 6. Identity across a grasp

Here is the case that is specific to arms, is underrated, and is free.

### 6.1 Continuous contact is a stronger claim than any model

When the arm has picked an object up, carried it, and put it down, the question
"is the object in the new picture the same one?" has an answer that does not come
from the camera at all. **The gripper held it the whole way. It could not have
become a different object.**

This is provenance through the actuator rather than through perception, and it is
categorically stronger than anything in section 3. A re-identification network
gives you a similarity score. Continuous mechanical contact gives you a physical
argument: for the identity to be wrong, the object would have had to leave the
fingers and be replaced, and the gripper's own state says it did not open.

It is also free. Nothing extra is computed, no model is downloaded, and there is
no per-frame cost. It is a by-product of doing the task.

### 6.2 The three conditions, each of which is checkable

The argument holds only if three things are true, and each one can be tested
rather than assumed.

**The gripper never opened between the pick and the place.** The controller knows
this. It is a matter of not throwing the information away — the identity claim
should be tied to a specific uninterrupted grasp, and any open command in between
invalidates it.

**Exactly one object entered the fingers.** The width at which the fingers stop is
a measurement, as
[the grasp sequence](../07_gripping/06_two-finger-gripper.md#4-the-grasp-as-pseudo-code)
sets out, and comparing it against the width the camera predicted tests this
directly. Note the threshold there is 4 mm, and that section 4.1 puts the
camera's own width error at about 2.5 mm when the mask edge is one pixel out on
each side. A threshold tighter than the camera's own error would fire on every
good grasp, so 4 mm is about as tight as that check can honestly be.

**The object did not slip out and get re-acquired.** A gripper that is
self-locking, as most parallel grippers are, makes this unlikely rather than
impossible, and a force or width reading that changed mid-carry is the signal.

If all three hold, the identity survives the grasp with certainty. If any one
fails, you are back to the camera, and you should say so rather than quietly
carrying the claim forward.

### 6.3 What the grasp does not preserve

The grasp preserves **identity**. It does not preserve **pose**. An object can
rotate between the fingers while being carried, and an underactuated gripper
positively encourages it to settle into whatever orientation the fingers prefer.

Treating those two as one thing is the mistake this section exists to prevent. It
is entirely consistent to say "this is certainly the same bolt" and "I no longer
know which way up it is", and a system that conflates them will place the object
using an orientation measured before the pick and be wrong by whatever the object
did in the fingers.

The practical consequence is that after a place, you re-measure orientation and
you do not re-establish identity. That is the reverse of what a vision-first
design does, and it is cheaper in both directions.

### 6.4 The world model should be told by the arm, and checked by the camera

After the arm puts an object down, there are two claims about what is now in that
place. The arm says "I put A here", from the argument in section 6.1. The camera
says "there is an object here that looks like A".

The arm's claim should win, and the camera's job is to **verify** rather than to
decide. The reason is that the camera has no way to tell "I put A here" from
"there was already an identical B here" — the two produce the same picture. The
arm's claim carries information the picture does not contain.

When the two disagree — the arm says it placed something and the camera sees
nothing there, or sees two things — that is an **event to report**, not an
association to resolve. Something was dropped, something was knocked over, or
something was already there. Silently re-associating to whatever is nearest is
how a dropped object becomes a confidently tracked phantom.

There is a free corroboration worth taking. **The object should also have
disappeared from where it was picked up.** If the pick location still shows a
detection, you either picked something else, picked two, or did not pick at all,
and you have learned that without moving the arm.

### 6.5 Moving an object is how you identify it without a tracker

The most reliable object identification available to an arm is to nudge the
object and see what moves. **The pixels that changed are the object, and they are
one object, because one thing was pushed.** This answers "which pixels" and
"which object" in the same operation, and the second answer is not available from
any static picture.

This is a real technique with a name — interactive perception — and it is what
[background subtraction](03_programmed-methods.md#12-background-subtraction) turns
into when the arm rather than the world supplies the change. It resolves the two
hardest cases in this document. Touching objects separate,
because only one of them moves. Identical objects become distinguishable, because
only one of them moves.

What it costs is real and worth stating. It is destructive: the arrangement you
were looking at is no longer the arrangement you have, so it is unavailable
whenever the layout is what you must preserve. It doubles the cycle time on the
objects you apply it to. It can knock things over. And it only works on objects
the arm can safely push, which rules out anything fragile, anything top-heavy and
anything sitting in a stack.

The rule to take away is that an arm has an option no passive vision system has.
Before spending a week on a re-identification model, check whether a 20 mm nudge
answers the question.

## 7. The libraries, and the thirty lines

### 7.1 What exists

Every licence below was read from the project's own `LICENSE` file with
`gh api repos/OWNER/REPO/license` in September 2026. Read the table as: what the
package does for association specifically, its licence, and whether it runs on an
Apple Silicon Mac with no NVIDIA card.

| Package | What it does for association | Licence | On Apple Silicon |
| --- | --- | --- | --- |
| [SciPy](https://github.com/scipy/scipy) | [`linear_sum_assignment`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html), the optimal assignment of section 3.2 | BSD-3-Clause | yes |
| [FilterPy](https://github.com/rlabbe/filterpy) | a readable Kalman filter, with the textbook it was written alongside | MIT | yes |
| [OpenCV](https://github.com/opencv/opencv) | [`KalmanFilter`](https://github.com/opencv/opencv/blob/4.x/modules/video/include/opencv2/video/tracking.hpp), colour histograms and `compareHist`, ORB descriptors | Apache-2.0 | yes |
| [Norfair](https://github.com/tryolabs/norfair) | a small tracker where *you* supply the distance function; works in three dimensions and states that it supports a moving camera | BSD-3-Clause | yes |
| [Stone Soup](https://github.com/dstl/Stone-Soup) | a full tracking framework — joint probabilistic association, multiple-hypothesis tracking, several gate types | MIT | yes |
| [MRPT](https://github.com/MRPT/mrpt) | [`data_association.h`](https://github.com/MRPT/mrpt/blob/master/modules/mrpt_slam/include/mrpt/slam/data_association.h), nearest-neighbour and joint-compatibility association in C++ | BSD-3-Clause | yes, it runs a macOS build in CI |
| [vision_msgs](https://github.com/ros-perception/vision_msgs) | [`Detection3D.id`](https://github.com/ros-perception/vision_msgs/blob/ros2/vision_msgs/msg/Detection3D.msg), the field the identity is meant to go in | Apache-2.0 | yes |
| [message_filters](https://github.com/ros2/message_filters) | pairing a picture with the arm pose of the same instant | BSD-3-Clause | yes |
| [geometry2](https://github.com/ros2/geometry2) | tf2, which puts both sets of detections in one frame before you compare them | BSD-3-Clause | yes |
| [autoware_multi_object_tracker](https://github.com/autowarefoundation/autoware_universe/tree/main/perception/autoware_multi_object_tracker) | a working ROS 2 multi-object tracker with gating and assignment, from a self-driving stack | Apache-2.0 | builds for Linux ROS 2; not practical on a Mac |
| [ByteTrack](https://github.com/FoundationVision/ByteTrack) | the current baseline 2D box tracker | MIT | yes |
| [OC-SORT](https://github.com/noahcao/OC_SORT), [BoT-SORT](https://github.com/NirAharon/BoT-SORT) | 2D box trackers with better behaviour through occlusion | MIT | yes |
| [supervision](https://github.com/roboflow/supervision) | a maintained, installable ByteTrack you do not have to vendor | MIT | yes |
| [SAM 2](https://github.com/facebookresearch/sam2) | mask propagation through a continuous video, per section 3.6 | Apache-2.0 | yes, through `transformers` |
| [lap](https://github.com/gatagat/lap), [lapx](https://github.com/rathaROG/lapx) | the assignment solver ByteTrack lists in its `requirements.txt` | BSD-2-Clause / MIT | yes |
| [SORT](https://github.com/abewley/sort), [DeepSORT](https://github.com/nwojke/deep_sort) | the two originals, and the reason everything above exists | **GPL-3.0** | yes, and the licence is copyleft |
| [BoxMOT](https://github.com/mikel-brostrom/boxmot) | many trackers and re-identification weights in one package | **AGPL-3.0** | yes, and the licence is the strongest copyleft here |

Two licence notes, both easy to trip over. SORT and DeepSORT are GPL-3.0, and a
great deal of tracking code on the internet is a copy of one of them with the
header removed. BoxMOT is AGPL-3.0, which is the same trap discussed in
[licences and platforms](06_licences-and-platforms.md#1-licences-and-the-one-that-will-catch-you-out)
and which reaches further than the GPL because it triggers on network use.
ByteTrack, OC-SORT and BoT-SORT are MIT and do the same job, so there is no reason
to take the risk.

### 7.2 Why most of that table does not fit a robot arm

Nine of the entries above are 2D multi-object trackers from the surveillance and
self-driving world, and it is worth being explicit about why they are the wrong
shape for an arm.

They track **axis-aligned boxes in the image plane**, and their cost function is
overlap between a predicted box and a detected box. That is a sound design for a
camera bolted to a pole. It does not work on a wrist camera, for a reason that has
nothing to do with the tracker's quality: when the arm moves, every box in the
image moves, so the overlap between consecutive frames goes to zero even though
nothing in the world moved at all. The constant-velocity model is being applied in
the wrong coordinate frame.

They also give you a box identity and not a position. An arm needs a point in the
robot's frame with an uncertainty attached to it, and a 2D box tracker produces
neither.

Norfair is the exception in the list, and that is why it is worth naming
separately. It lets you supply your own distance function, it works in three
dimensions, and its documentation states support for a moving camera. If you want
a library rather than your own loop, that is the one whose shape matches the
problem.

### 7.3 The thirty lines

For a table-top arm, association is genuinely a short function, and writing it is
often better than taking a dependency, because the gate is the part you must
understand and a library hides it behind a parameter.

In pseudo code first:

```
predict each existing track forward to the timestamp of the new picture
transform both sets of positions into the robot's frame
cost[i][j] = Mahalanobis distance between track i predicted and detection j
where cost[i][j] exceeds the gate, replace it with a very large number
rows, cols = the optimal assignment of that cost table
discard any assigned pair whose cost is still the very large number
matched pairs update their tracks
detections with no track start a tentative track
tracks with no detection count a miss, and are deleted after enough misses
```

The same thing in Python, which is the whole of it:

```python
import numpy as np
from scipy.optimize import linear_sum_assignment

GATE = 3.368   # sqrt of the 99% point of chi-square with 3 degrees of freedom
BIG = 1.0e6    # a cost large enough that the solver never prefers it

def associate(predicted, detections, sigma):
    """Match predicted track positions to new detections.

    predicted:  (T, 3) positions in the robot frame, metres
    detections: (D, 3) positions in the robot frame, metres
    sigma:      (3,)   one standard deviation per axis, metres

    Returns matched pairs, unmatched track indices, unmatched detection indices.
    """
    diff = predicted[:, None, :] - detections[None, :, :]        # (T, D, 3)
    d = np.sqrt(((diff / sigma) ** 2).sum(axis=2))               # Mahalanobis
    cost = np.where(d <= GATE, d, BIG)                           # the gate

    rows, cols = linear_sum_assignment(cost)
    keep = cost[rows, cols] < BIG          # the solver fills the matrix; we do not
    matched = list(zip(rows[keep].tolist(), cols[keep].tolist()))

    lost = sorted(set(range(len(predicted))) - set(rows[keep].tolist()))
    new = sorted(set(range(len(detections))) - set(cols[keep].tolist()))
    return matched, lost, new
```

Three details in that function are the reason for writing it out rather than
describing it.

**`sigma` is a vector, not a scalar, and that is section 4.4.** Passing
`np.array([0.00195, 0.00195, 0.00700])` — across, across, along the ray — instead
of a single number is the entire fourteen-fold gain, and it is one argument.
The axes have to be the camera's, so if you are working in the robot frame you
rotate the covariance into it rather than pretending the error is aligned with
the world.

**The `keep` filter is not optional.** `linear_sum_assignment` returns a complete
assignment of `min(T, D)` pairs and will happily assign a pair costing `BIG`
rather than leave a row empty, because leaving a row empty is not something it is
allowed to do. Without the filter, every gate you wrote is ignored in exactly the
situation the gate existed for. This is the single most common bug in hand-written
association code.

**Use a large finite number, not `np.inf`.** SciPy accepts infinities when a
feasible assignment still exists, but raises `ValueError: cost matrix is
infeasible` the moment a row is entirely gated out — which is the normal case when
an object leaves the scene. A large finite number degrades gracefully where
infinity crashes.

What you have not written, and should reach for a library for, is genuine
multiple-hypothesis tracking: keeping several competing interpretations alive
across frames and resolving them later. Stone Soup implements that properly and
you should not. But a table-top arm essentially never needs it, because it has
section 6 available instead — it can move the object and find out.

## 8. What is specific to a robot arm

Most writing about tracking comes from surveillance and self-driving, where the
camera is fixed or the scene is a road. Five things are different for an arm, and
together they are why this document does not read like a tracking survey.

**The camera moves and the objects do not.** That is the reverse of the usual
assumption, and it makes image-plane association useless while making the
robot-frame version straightforward, because the arm's forward kinematics tells
you exactly how the camera moved.

**The objects are frequently identical on purpose.** Appearance-based methods
work well elsewhere and contribute nothing here, which is why section 4
spends its effort on geometry.

**The scene is small and the error budget is dominated by depth and
calibration.** Section 4.1 puts the mask's contribution at 1.2 mm out of 9.4 mm.
Better perception is not the lever.

**The arm can act on the scene.** Nudging an object, or picking it up, converts an
association problem into a certainty. No passive system has that option, and
section 6 is the argument for using it before building anything.

**The cost of a wrong answer is physical.** A surveillance tracker that swaps two
identities produces a wrong statistic. An arm that swaps two identities reaches
into the wrong place with a plan made for something else. That asymmetry is why
the gate in section 4 is set to refuse, and why a refusal is a result rather than
a failure.
