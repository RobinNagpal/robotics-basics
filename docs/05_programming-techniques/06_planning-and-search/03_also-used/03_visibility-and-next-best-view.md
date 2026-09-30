# Visibility and next-best-view

This page explains two linked techniques. The first is **visibility**: working out
what a camera can see from a given place, and what is hidden behind something. The
second is **next-best-view planning**: choosing where to put the camera next, so
that it sees as much as possible of what the robot does not know yet. The page
answers four questions. How do you test whether one object hides another? How do you
score a place to look from? Where does a robot arm use these? And when is a fixed
list of views the better choice?

It is for a reader who has read the [chapter overview](../01_overview.md) and knows
what a camera pose is, at the level of the
[pinhole camera model](../../02_geometry-and-cameras/02_most-used/01_pinhole-camera-model.md).
You do not need any geometry beyond a straight line and a circle. Every number on
this page comes from a real run of
[`planning_and_search_3.py`](../../../diagrams/planning_and_search_3.py).

Book 2's [choosing where to look](../../../02_perception/02_object-perception/09_choosing-where-to-look.md)
covers the same subject from the camera's side, with real camera sizes and
measured timings. This page is the technique underneath it: the test itself, and
the loop that uses it.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [Lines of sight and shadows](#2-lines-of-sight-and-shadows)
3. [How it works, step by step](#3-how-it-works-step-by-step)
   · [Testing one sight line against one cylinder](#testing-one-sight-line-against-one-cylinder)
   · [A worked example with two sight lines](#a-worked-example-with-two-sight-lines)
   · [Choosing where to look next](#choosing-where-to-look-next)
   · [A worked example with eleven candidate views](#a-worked-example-with-eleven-candidate-views)
   · [The pseudocode](#the-pseudocode)
   · [Choosing several views at once](#choosing-several-views-at-once)
4. [Where it is used on a robot arm](#4-where-it-is-used-on-a-robot-arm)
5. [Where it is useful, and where it is not](#5-where-it-is-useful-and-where-it-is-not)
6. [Libraries that provide it](#6-libraries-that-provide-it)
7. [Why this, and what it costs](#7-why-this-and-what-it-costs)
8. [Where to read next](#8-where-to-read-next)

---

## 1. The idea in one sentence

A camera sees a point only if the straight line from the camera to that point passes
through nothing on the way. To choose where to look next, test that line for every
point you still know nothing about, from every place the camera could go, and go to
the place that would show you the most.

Here is an everyday example. You are looking for your keys on a crowded shelf. From
where you stand, a tall vase hides a patch of the shelf behind it. You do not know
whether the keys are in that patch. So you think about where to stand. Standing a
step to the left would show you the patch behind the vase. Standing on a chair would
show you the whole shelf top, but the chair is in the next room. You take the step
to the left, because it shows you the most for a place you can actually get to. Then
you look again and decide again.

That is the whole technique. The rest of this page makes each part exact: what
"passes through nothing" means for a real shape, how to count what a view would
show, and how to handle the places the arm cannot reach.

---

## 2. Lines of sight and shadows

A **line of sight**, also called a **sight line** or a **ray**, is the straight line
from the camera's centre to a point in the scene. Light travels along it. If an
object sits across that line, the point is **occluded**, which means hidden.

Each object hides a region behind it. This region is called its **shadow**, or its
**occlusion shadow**. It is the same shape as a real shadow would be if the camera
were a lamp. The camera cannot see anything inside it.

The scene on this page is a row of four upright cylinders on a table. Units are
centimetres. The table top is at height 0. The table below lists them. Read each row
as one object: where its centre is along the table, its radius, and its height.

| Object | Centre along the table | Radius | Height |
| --- | --- | --- | --- |
| bottle 1 | 35 cm | 4 cm | 30 cm |
| cup 1 | 50 cm | 4 cm | 10 cm |
| bottle 2 | 70 cm | 3.5 cm | 26 cm |
| cup 2 | 82 cm | 5 cm | 8 cm |

The picture below shows the row from the side. Seen from the side, each cylinder is
a rectangle. The grey regions are the shadows. The script found them by testing the
sight line to every point on a 2.5 mm grid, from the table to 45 cm up.

![A camera at the side sees only the front of the first bottle; a camera above sees nearly everything](../../../images/planning-and-search/visibility-and-next-best-view/seen-from-side-and-above.svg)

On the left, the camera is at the side of the table, 20 cm up. That is lower than
the first bottle. So the first bottle's shadow covers everything behind it: both cups
and the second bottle. 55% of the free space in the dashed box is hidden. The
camera cannot see the top of any object. It would report one bottle and nothing
else.

On the right, the camera is 60 cm above the middle of the table, looking down. Each
bottle now casts a thin shadow that leans away from the camera. Only 11% of the free
space is hidden. The camera sees the tops of both bottles and cup 1. It sees only a
small part of the top of cup 2, because bottle 2's shadow falls across it.

Two things follow from this picture. First, a tall object close to the camera hides
far more than a short object further away. Second, the same scene can be almost
invisible from one place and almost fully visible from another. That is why it is
worth choosing where to look.

---

## 3. How it works, step by step

The technique has two layers. The lower layer is a test: is this one point visible
from this one camera position? The upper layer is a loop: use the test many times to
score each place the camera could go, then pick the best.

### Testing one sight line against one cylinder

Many objects on a table are close to upright cylinders: bottles, cups, cans, jars
and posts. An upright cylinder has a very simple exact test. It is exact because it
uses the real shape, not a grid of points. A test like this, done with a formula
rather than by trying many points, is called an **analytic** test.

Write every point on the sight line as

```
point(t) = camera + t × (target − camera)
```

The number `t` says how far along the line the point is. At `t = 0` the point is at
the camera. At `t = 1` it is at the target. Halfway along, `t = 0.5`.

A point is inside a solid upright cylinder when two things are true at the same
time.

1. **Seen from above, it is inside the circle.** Ignore the height. The distance from
   the point to the cylinder's centre line must be less than the radius. Putting
   `point(t)` into the circle's equation gives a **quadratic equation** in `t`: an
   equation with a `t²` term, a `t` term and a plain number. Its two answers are
   where the line enters and leaves the circle. If it has no answers, the line
   misses the circle completely.
2. **Seen from the side, it is between the table and the top.** Ignore the circle.
   The point's height must be between 0 and the cylinder's height. The height changes
   in a straight line with `t`, so this gives one more stretch of `t`.

Each test gives a stretch of `t`, called an **interval**. The cylinder blocks the
sight line only if the two intervals overlap, and the overlap lies between the
camera and the target, which means somewhere between `t = 0` and `t = 1`.

It is tempting to test from above only, or from the side only. Both are wrong. From
above, a sight line can cross a cup's circle while passing well over the cup's top.
From the side, a sight line can cross a bottle's rectangle while passing beside
the bottle. The next example shows both mistakes.

For a box whose sides line up with the table, the same idea works with three
intervals, one for each direction. That is the **slab method** in Book 2's
[ray cast in three dimensions](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#32-the-ray-cast-in-three-dimensions).

### A worked example with two sight lines

A camera sits at the left end of the table, 10 cm in front of the row of objects and
30 cm up. Its position is (0, −10, 30). The first two numbers are the position on
the table, and the third is the height. The red sight line goes to the middle of the
top of cup 1, at (50, 0, 10). The green sight line goes to the middle of the top of
bottle 2, at (70, 0, 26).

![Each sight line is blocked only when "inside the circle" and "below the top" happen at the same t](../../../images/planning-and-search/visibility-and-next-best-view/cylinder-sight-line-test.svg)

Here is the red line against bottle 1, worked by hand. Bottle 1's centre is at
(35, 0), and its radius is 4.

1. The line moves 50 across, 10 sideways and −20 in height from the camera to the
   target.
2. From above, the circle equation becomes
   `2600 t² − 3700 t + 1309 = 0`. Its two answers are `t = 0.66` and `t = 0.76`.
   So the line is inside the circle from 66% to 76% of the way along.
3. From the side, the height is `30 − 20 t`. It is below the bottle's top of 30 cm
   for every `t` above 0, and it reaches the table at `t = 1.5`. So the line is
   below the top from `t = 0` to `t = 1.5`.
4. The two intervals overlap from `t = 0.66` to `t = 0.76`. That is between the
   camera and the target. So bottle 1 blocks the red line, and the camera cannot see
   the top of cup 1.

The green line gives the two opposite traps.

- Against cup 1, it is inside the circle from `t = 0.68` to `t = 0.76`. But it is
  below the cup's top only from `t = 5.0` onwards, far past the target. Over that
  stretch the line is about 27 cm up, and the cup is 10 cm tall. There is no
  overlap, so cup 1 does not block it. A test from above alone would have said it
  did.
- Against bottle 1, it is below the top all the way, because the camera is at the
  same height as the bottle's top. But from above it never enters bottle 1's circle.
  So bottle 1 does not block it either. A test from the side alone would have said
  it did.

The script tests both lines against all four cylinders. The red line is blocked by
bottle 1 only. The green line is blocked by nothing, so the camera can see the top of
bottle 2.

The test costs one square root and a few multiplications per cylinder. Book 2
[measured](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#33-what-it-costs-measured)
the box version at about 40 nanoseconds per obstacle. So a program can test
thousands of sight lines against dozens of objects in well under a millisecond.

### Choosing where to look next

The loop that uses the test is called **next-best-view planning**. The chosen pose is
the **next best view**. Here are its steps.

1. **Keep a record of what you do not know yet.** The usual record is a grid of small
   cells covering the work area. Each cell is marked free, occupied or **unknown**.
   At the start, every cell is unknown. The page on
   [volumetric maps](../../05_image-and-point-cloud-processing/03_also-used/02_volumetric-maps.md)
   covers these grids.
2. **List the candidate poses.** A **candidate** is one place the camera could go,
   with the direction it would face. A common choice is a ring or a half-sphere of
   points around the work area, each one facing its centre.
3. **Remove the ones the arm cannot reach.** The cheapest check is distance: a pose
   further from the arm's shoulder than the arm is long is out. A stricter check asks
   [inverse kinematics](../02_most-used/02_numerical-inverse-kinematics.md) for joint
   angles that put the camera there.
4. **Predict what each one would reveal.** For each remaining candidate, test the
   sight line to every unknown cell. Count the cells that are inside the camera's
   picture and not hidden. This count is the candidate's **gain**. The gain can also
   be the number of objects not yet seen, or any other count of new information.
5. **Take the best.** Move the camera to the candidate with the highest gain. Take a
   picture. Mark every cell it saw as known.
6. **Repeat** from step 4, because the gains have changed. Stop when the budget runs
   out, or when no candidate would reveal enough to be worth the move.

Step 6 matters. After the first view, the cells it saw are no longer unknown. So a
candidate that looks at the same region from nearly the same place now gains almost
nothing, even though it scored well in round 1.

### A worked example with eleven candidate views

The scene is the same row of four cylinders, seen from the side. The unknown space
is the region from the table to 32 cm up, over the whole 100 cm of table, cut into
2 cm squares. Leaving out the squares inside objects, that makes 629 unknown cells.

There are 11 candidate views. They sit on a half circle of radius 55 cm around the
middle of the table, every 15 degrees from 15° to 165°. The angle is measured from
the right-hand end of the table. Each camera faces a point 5 cm above the middle of
the table. Its picture is 70 degrees wide. The arm's shoulder is 10 cm to the left
of the table, and the arm can hold the camera at most 100 cm from the shoulder. The
budget is three views.

![Eleven candidate cameras; three are out of reach; the one at 105 degrees would see the most unknown cells](../../../images/planning-and-search/visibility-and-next-best-view/candidate-views-and-reach.svg)

Step 3 removes the three candidates at the right-hand end. They are 114.0, 111.1 and
106.3 cm from the shoulder. The one at 60° is 99.6 cm away, so it just stays in.

Step 4 gives the round 1 gains. The table below lists them. Read each column as one
candidate and the number of unknown cells it would see.

| Candidate | 60° | 75° | 90° | 105° | 120° | 135° | 150° | 165° |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Round 1 gain | 179 | 194 | 194 | **218** | 193 | 214 | 159 | 156 |
| Round 2 gain | 48 | 22 | 17 | taken | 42 | **129** | 114 | 117 |
| Round 3 gain | 30 | 13 | 14 | taken | 6 | taken | 51 | **72** |

The loop runs three rounds.

1. Round 1 takes 105°, which would see 218 cells. That is 35% of the unknown space.
2. Round 2 recounts. The views at 75° and 90° looked strong in round 1, with 194 cells
   each. Now they would add only 22 and 17, because most of what they see was seen
   from 105°. The view at 135° adds 129. It sees the space just left of bottle 1,
   which was in bottle 1's shadow from 105°, and a strip high up at the right-hand
   end. The known space rises to 347 cells, 55%.
3. Round 3 takes 165°, a low view from the left end of the table. It adds 72 cells
   near the table at the left end. The known space rises to 419 cells, 67%.

![Three rounds: each takes the view that adds the most unknown cells, so later views fill in what earlier ones missed](../../../images/planning-and-search/visibility-and-next-best-view/three-rounds-of-next-best-view.svg)

After three views, most of the right-hand end is still unknown. The reason is reach.
The views that look into the region behind bottle 2 from the right are the three
out-of-reach candidates. The one at 45° alone would see 195 cells. A robot in this
position would need to move its base, or accept that the right-hand end stays
unknown. The loop tells you this plainly, which is useful in itself.

### The pseudocode

The pseudocode below is the whole loop. `blocked` is the cylinder test from earlier
on this page.

```
function blocked(camera, target, cylinder):
    # points on the line are camera + t × (target − camera), t from 0 to 1
    circle_t  = where the line is inside the cylinder's circle, seen from above
    height_t  = where the line is between the table and the cylinder's top
    if circle_t is empty or height_t is empty:
        return false
    start = the largest of circle_t.start, height_t.start, 0
    end   = the smallest of circle_t.end, height_t.end, 1
    return start < end

function sees(camera, cell, objects):
    if cell is outside the camera's picture:
        return false
    for each object in objects:
        if blocked(camera, cell, object):
            return false
    return true

function next_best_views(candidates, unknown_cells, objects, budget):
    candidates = the ones in candidates the arm can reach
    chosen = empty list
    repeat budget times:
        best = nothing, best_gain = 0
        for each candidate not in chosen:
            gain = number of cells in unknown_cells where sees(candidate, cell, objects)
            if gain > best_gain:
                best = candidate, best_gain = gain
        if best is nothing or best_gain is too small to be worth a move:
            stop
        move the camera to best, take a picture, update the map
        remove every cell best saw from unknown_cells
        add best to chosen
    return chosen
```

On a real robot, the line "update the map" uses the real picture, not the
prediction. The prediction assumed that unknown cells are empty. If the picture
shows a new object, the map gains an occupied region, and that object will cast
its own shadow in the next round's predictions.

### Choosing several views at once

The loop above chooses one view, looks, and then chooses again. That is right when
each picture can change the plan. Sometimes the objects are known in advance, and
the task is to pick a fixed set of views, all at once, that together see everything.

That is a different problem called **set cover**: each view is a set of things it
sees, and you want the fewest sets that together cover everything. The same greedy
rule solves it well: take the view that adds the most, then the next, and so on.
[Greedy algorithms and set cover](../../08_decisions-and-task-logic/03_also-used/01_greedy-algorithms-and-set-cover.md#2-set-cover-the-problem-greedy-is-best-known-for)
works an example with eight glasses and shows how far from the best the greedy
choice can be. The visibility test on this page is what builds the sets that page
takes as given.

---

## 4. Where it is used on a robot arm

Here are the places where an arm cell uses visibility tests or a next-best-view loop.

- **Throwing away useless camera poses early.** Before any view reaches the motion
  planner, the visibility test removes the ones from which the target is hidden.
  Book 2's worked scene removed 62% of the views that had passed every other
  check, in its
  [section on occlusion](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#3-occlusion-as-a-precondition-not-a-difficulty).
- **Picking a small fixed set of views for a cell.** When the objects are roughly
  known, an engineer runs the visibility test on many candidates once, offline,
  and keeps two or three good ones. The arm then drives to them by name every cycle.
- **Looking into a bin or a shelf.** The sides of a bin, and the objects near the
  front of a shelf, hide what is behind them. A next-best-view loop with an unknown
  grid finds a view down past the edge.
- **Finding a hidden object.** When the object the robot needs is not in the first
  picture, the unknown cells are the only places it can be. The loop scores views by
  how many of those cells they would show.
- **Building a model of an unfamiliar object.** To scan an object it has never seen,
  the robot needs many views. Each new view should show surface that the earlier
  ones missed. This is the job next-best-view planning was invented for.
- **Checking a grasp before committing.** A grasp chosen from a single view may land
  on a side the camera never saw. A second view aimed at that side, chosen by the
  same test, confirms the surface is there.
- **Keeping the camera's view clear while the arm moves.** A camera on a post can be
  hidden by the arm itself. The same sight-line test, with the arm's links as the
  obstacles, tells the planner which arm poses would block the camera's view of the
  gripper.

---

## 5. Where it is useful, and where it is not

The visibility test is exact for the shapes it models. The next-best-view loop is
only as good as its record of the unknown and its list of candidates. The table below
lists the common problems. Read each row as a problem, the sign you would see, and
what people do instead.

| Problem | The sign you would see | What people do instead |
| --- | --- | --- |
| The task needs only one or two views | the loop runs once, and costs an extra move and a map for no gain | a fixed set of views chosen offline, as Book 2's [honest verdict](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#22-the-honest-verdict) recommends |
| Objects are not simple shapes | the test says a view is clear, but a handle or a lid blocks it | wrap each object in a slightly larger cylinder or box, or ray-cast against a mesh |
| The test uses footprints only, ignoring height | views over short objects are thrown away although they were fine | test in three dimensions, with the height interval |
| The best view is out of reach | the gains are high but the arm cannot get there | check reach before scoring; move the base; or accept what is left unknown |
| Every move is slow | the loop finds good views but the cycle time doubles | a fixed set, or a gain that is divided by the time to reach the view |
| The scene changes between pictures | cells marked known are now wrong | re-mark cells as unknown after a set time, or re-scan the changed region |
| Candidates are too few, or all at one height | the loop stops with large regions still unknown | add candidates at other heights and angles; the gains show where they are needed |
| Gains assume unknown cells are empty | a view that should see behind a box sees a new object instead | nothing to fix: update the map from the real picture and score again |
| The number of rounds varies with the scene | the cycle time is different every run and hard to guarantee | cap the budget; fall back to a fixed set when the cap is reached |

The first row is the most important. Book 2
[counts the views each task needs](../../../02_perception/02_object-perception/08_the-wrist-camera.md#2-how-many-pictures-each-task-needs)
and finds that most arm tasks need one or two. A fixed set of views can also be
tested and signed off, which a loop that decides at run time cannot. So the
visibility test is almost always worth having, and the full loop is worth having only
when the robot genuinely does not know what is in front of it.

---

## 6. Libraries that provide it

The cylinder test and the loop on this page are a few dozen lines of plain code, and
no library is needed for them. The libraries below give you ray casting against more
complex shapes, or the grid of unknown cells. Read each row as one library, the
languages it serves, the names to look for, and a note.

| Library | Languages | Function or class | Note |
| --- | --- | --- | --- |
| Open3D | Python, C++ | `open3d.t.geometry.RaycastingScene`, `PointCloud.hidden_point_removal` | casts many rays against meshes at once; the second removes points a camera could not see |
| trimesh | Python | `mesh.ray.intersects_any`, `mesh.ray.intersects_location` | ray tests against triangle meshes |
| MuJoCo | Python, C | `mj_ray`, `mj_multiRay` | ray casts against every shape in a simulated scene |
| PyBullet | Python | `rayTest`, `rayTestBatch` | the same, in the Bullet simulator |
| OctoMap | C++ | `OcTree`, `OcTree::castRay`, `OcTree::computeRay` | the standard free, occupied and unknown grid; cells cost little when empty |
| PCL | C++ | `pcl::VoxelGridOcclusionEstimation` | marks which cells of a voxel grid are hidden from a camera |
| MoveIt 2 | C++ (ROS 2) | `VisibilityConstraint` | asks the planner to keep a sensor's view of a target clear |

Book 2's [libraries section](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#7-the-libraries-and-what-runs-on-an-apple-silicon-mac)
gives the licence of each of these and says which run on an Apple Silicon Mac.

---

## 7. Why this, and what it costs

This section answers the four questions for visibility and next-best-view planning:
what it is, what it does for you, why it rather than the obvious alternative, and
what it costs.

The visibility test checks whether a straight line from the camera to a point passes
through any object. For simple shapes such as upright cylinders and boxes it is an
exact formula. Next-best-view planning uses that test to score candidate camera
poses by how much new they would show, then takes the best one and repeats.

What it does for you is replace guessing with counting. Without it, a program
chooses a view, drives there, takes a picture, and only then finds out the target
was behind a bottle. With it, the program knows before the arm moves. Each wasted
move costs between a few hundred milliseconds and a couple of seconds on a real arm,
and the test costs microseconds.

The obvious alternative is to **render** each candidate view: draw the whole scene
as a picture from that pose, as a game engine would, and look at the picture. That
works for any shape and gives a full image. But it is far slower than a few sight
lines, and it needs a full model of the scene. For the question "is this target
hidden from here?", a handful of sight-line tests answers it exactly. Choose
rendering when you need the whole predicted picture, for example to predict what a
detector will see. Choose sight lines when you need a yes or no, or a count.

The second alternative is to skip the loop and use a **fixed list of views**. For
most arm tasks this is the better choice, as section 5 says. The loop earns its place
when the robot does not know the scene in advance.

The costs are these. You must model each object as a simple shape, and a shape that
is too small lets a blocked view through. The loop needs a record of the unknown
space, which is a map you now have to keep correct. Its cycle time depends on the
scene, so it is harder to promise a fixed time per task. And its choices are only as
good as its candidate list: it cannot choose a view you did not offer it.

---

## 8. Where to read next

- Book 2's [choosing where to look](../../../02_perception/02_object-perception/09_choosing-where-to-look.md)
  applies this page with a real camera: distance, viewing angle, reach, and the
  order in which to visit the chosen views.
- [Greedy algorithms and set cover](../../08_decisions-and-task-logic/03_also-used/01_greedy-algorithms-and-set-cover.md)
  covers picking several views at once, and how far greedy can be from the best.
- [Volumetric maps](../../05_image-and-point-cloud-processing/03_also-used/02_volumetric-maps.md)
  covers the grid of free, occupied and unknown cells that the loop scores against.
- [Numerical inverse kinematics](../02_most-used/02_numerical-inverse-kinematics.md)
  is the stricter reach check for each candidate view.
- [Sampling-based planning](../02_most-used/01_sampling-based-planning.md) plans the
  arm's move to the chosen view.
- Book 2's [the wrist camera](../../../02_perception/02_object-perception/08_the-wrist-camera.md)
  covers what a view costs and how many views each task needs.
