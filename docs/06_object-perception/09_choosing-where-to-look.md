# Choosing where to look

This area has already decided where to bolt the camera on.
[Sensors, section 1.4](02_sensors.md#14-where-to-put-the-camera) chooses between a
camera on the wrist and a camera on a post, and
[the wrist camera](08_the-wrist-camera.md) works the wrist case through in detail.
Neither of them answers the question that appears the moment the camera is on the
arm, which is **where to move it**. A wrist camera can be at any pose the arm can
reach, and almost all of those poses are useless. This document is about ruling
them out.

The subject has a name. **Viewpoint planning** is choosing the pose from which a
sensor will observe something. Its online form, where the robot looks, thinks, and
then decides where to look next, is called **next-best-view planning**. The
literature on it is large and the practical verdict is blunt: most working robot
cells use two or three fixed viewpoints worked out in advance and never solve the
online problem at all. Section 2 explains why that is usually the right call.

What is worth having, and what most treatments skip, is the cheap half. Before any
viewpoint reaches a motion planner, you can test whether the target is even
visible from it. That test is a ray cast, it costs about forty nanoseconds per
obstacle on the machine this document was written on, and in the worked scene in
section 3 it removes sixty-two per cent of the viewpoints that had already
survived every other filter. **Occlusion is usually treated as a difficulty to
suffer. It is better used as a predicate to filter on.** That change is the point
of this document.

[Making it work, section 4](07_making-it-work.md#4-occlusion-and-clutter) treats
occlusion the first way, which is correct for a fixed camera, because a fixed
camera cannot do anything about it. A camera on an arm can.

Every number below uses the repository's own camera, with a focal length
`fx` = `fy` = 277.1 pixels, a principal point at `cx` = 160 and `cy` = 120, and a
320 by 240 sensor. Those are the four numbers from
[the lens as four numbers](../05_camera/01_basics.md#6-the-lens-as-four-numbers),
so every figure can be checked by hand. The timings were measured on an Apple M4
with NumPy 2.5.3 and are reproduced with the code that produced them.

## Who this is for

Someone with a camera on an arm, who has read
[the wrist camera](08_the-wrist-camera.md) or knows how many pictures their task
needs, and now has to decide which poses to take those pictures from. You do not
need to have used a motion planner. Every term is explained where it first
appears.

The companion document is [the wrist camera](08_the-wrist-camera.md). It answers
*how many views*, and concludes that two views with a wide separation beat twenty
views packed together. This one answers *which views*, and its answer depends on
that conclusion throughout: if the count is small, each viewpoint has to be chosen
well, because there is no averaging left to hide behind.

## Contents

1. [What the question actually is](#1-what-the-question-actually-is)
2. [Active perception and the next best view](#2-active-perception-and-the-next-best-view)
3. [Occlusion as a precondition, not a difficulty](#3-occlusion-as-a-precondition-not-a-difficulty)
4. [What makes a viewpoint good](#4-what-makes-a-viewpoint-good)
5. [Choosing the viewpoint set offline](#5-choosing-the-viewpoint-set-offline)
6. [The order to visit them in](#6-the-order-to-visit-them-in)
7. [The libraries, and what runs on an Apple Silicon Mac](#7-the-libraries-and-what-runs-on-an-apple-silicon-mac)
8. [The whole selection, as pseudo code then Python](#8-the-whole-selection-as-pseudo-code-then-python)
9. [What is specific to choosing where to look](#9-what-is-specific-to-choosing-where-to-look)

---

## 1. What the question actually is

A robot arm with a camera on its wrist has a continuous space of viewing poses.
Six numbers describe one of them: three for where the camera is, three for which
way it points. You cannot search a continuous six-dimensional space, so the first
thing every practical method does is replace it with a finite list of candidates
and then throw most of them away.

Two simplifications make the list small enough to enumerate, and both are almost
always safe.

The camera points at the target. That removes two of the six numbers, because once
you have fixed the camera's position and said it must look at a known point, only
the roll about the viewing axis is left. Roll changes which way up the picture is
and changes nothing else that matters, so it is usually fixed by the arm's own
preference rather than chosen.

The camera sits on a sphere around the target. That turns the remaining three
numbers into an azimuth, an elevation and a radius, which are easy to sample
evenly and easy to reason about. The sphere is centred on the thing you want to
look at, not on the robot, which is the part people get backwards.

With those two moves, a candidate list is a grid. The worked scene used throughout
this document samples thirty-six azimuths ten degrees apart, four elevations, and
five radii between 150 mm and 400 mm, which is 36 × 4 × 5 = **720 candidates**.
That number is deliberately generous. Section 3 shows it can be filtered in well
under a millisecond, so there is no reason to be stingy.

The job is then to answer one question about each candidate: is it worth asking
the motion planner to go there. The rest of this document is the set of tests that
answer it.

Two terms are needed before section 2. A **predicate** is a test that returns
true or false and nothing else, so it can only include or exclude a candidate. A
**score** is a number that ranks candidates against each other. Predicates and
scores behave very differently under error, and section 4.5 argues that you should
prefer predicates for as long as you can.

## 2. Active perception and the next best view

**Active perception** means changing the sensor to make the perception problem
easier, instead of taking whatever picture arrives and working harder on it. Its
oldest and most useful example is moving a camera to see round something.

The online version has a standard name. Take a picture, work out what you still do
not know, choose the pose that would reduce that unknown the most, move there, and
repeat. The pose you choose is the **next best view**. The loop continues until
the remaining unknown is small enough or the budget runs out.

### 2.1 The three classical formulations

The formulations differ in what they call the unknown. Read the table as: the
quantity being maximised, what the robot has to keep in memory to compute it, and
what the formulation is genuinely good at.

| Formulation | Maximises | Needs to keep | Good at |
| --- | --- | --- | --- |
| coverage | new surface area seen | a record of which surface patches have been observed | building a complete model of an unfamiliar object |
| information gain | expected reduction in entropy of an occupancy map | a three-dimensional occupancy grid with a probability per cell | exploring a space whose shape is unknown |
| uncertainty reduction | expected shrinkage of a specific estimate, such as a pose covariance | the estimator's own covariance matrix | pinning down one quantity you already almost know |

**Coverage** is the simplest and treats the problem as a set-cover. Every
candidate viewpoint sees some set of surface patches; you want the smallest set of
viewpoints whose union is everything. Set-cover is NP-hard, which means no method
is known that always finds the smallest set without, in the worst case, taking
time that grows faster than any polynomial in the number of viewpoints. So in
practice everyone runs the greedy version, which repeatedly takes the viewpoint
that adds the most new patches and accepts that the result may not be the
smallest.

**Information gain** replaces the surface with a grid of cells, each of which is
free, occupied or unknown with some probability. A viewpoint's value is how much
the entropy of that grid would fall if you looked from there. This is the version
that most research systems use, because the occupancy grid is a structure they
already maintain for collision checking. [OctoMap](https://github.com/OctoMap/octomap)
is the usual implementation of the grid, and it is an octree rather than a dense
array so that empty space costs almost nothing to store.

**Uncertainty reduction** is the version that fits a robot arm best and is used
least. If the thing you are unsure about is one object's pose, and you have a
covariance matrix for it, you can ask which viewpoint would shrink that matrix
most. The answer is usually a viewpoint roughly perpendicular to the direction you
are least certain about, which is the same conclusion
[baseline, not count](08_the-wrist-camera.md#5-baseline-not-count) reaches by
geometry, without any of the machinery.

### 2.2 The honest verdict

Online next-best-view planning is correct for one shape of problem and wasteful
for the rest. The shape it is correct for is the one where you genuinely do not
know what is in front of you and the number of looks is large.

The arithmetic that decides it comes straight from
[what a view actually costs](08_the-wrist-camera.md#4-what-a-view-actually-costs).
Moving the arm to a new viewpoint costs somewhere between a few hundred
milliseconds and a couple of seconds on a real arm. Deciding where to move costs,
as section 3.3 measures, well under a millisecond. So **the computation is free
and the move is not**, which means the only thing worth optimising is the number
of moves. An online planner that saves you one move out of ten has done well. An
online planner applied to a task that needs two views has nothing to save.

Most arm tasks need one or two views. [How many pictures each task
needs](08_the-wrist-camera.md#2-how-many-pictures-each-task-needs) works that out
per task and finds that only reconstruction — building a model of a shape you have
none of — genuinely wants tens of views. Everything else wants one or two. A
next-best-view loop over two views is a loop that runs once, and a loop that runs
once is a fixed choice with extra machinery around it.

There is a second reason, and it is the one that decides real installations. **A
fixed viewpoint set can be tested.** You can drive the arm to each of two poses,
check that it gets there, check the picture, check the cycle time, and write the
result down. An online planner produces a different trajectory every run, so the
worst case has to be bounded by argument rather than by measurement, and a cell
that has to pass a safety review will not thank you for that.

Five jobs online next-best-view planning suits:

- reconstructing an object you have no model of, where view twenty really does see
  material views one to nineteen did not
- inspecting a part whose geometry varies between units, so a fixed set cannot be
  guaranteed to cover the features
- exploring a container or a shelf whose contents and depth are unknown before the
  first look
- searching for an object that may be anywhere in a space too large for one view
- any task where the arm is already moving for another reason, so the extra
  viewpoint costs no additional motion

Five jobs it cannot do:

- pay for itself on a task that needs one or two views, which is most arm tasks
- give you a bounded cycle time, because the number of iterations is data-dependent
- work without a maintained occupancy map or surface model, which is a component
  you now own and must keep correct
- help when the limiting error is calibration rather than coverage, which
  [the error budget](01_overview.md#8-where-the-millimetres-go) shows it usually is
- recover from a target that moves between iterations, since every iteration
  assumes the scene stood still

The rest of this document therefore spends its effort on the parts that are cheap
and always worth having: the occlusion predicate in section 3, the four quality
tests in section 4, and the offline set in section 5.

## 3. Occlusion as a precondition, not a difficulty

**Occlusion** means something is in the way, so part or all of the target does not
appear in the picture. The usual treatment is to describe it as a hazard, note
that segmentation degrades under it, and suggest taking another view. That is
correct and it is not actionable, because it does not say which other view.

The change this section argues for is small and it is the most useful thing in
this document. **Visibility is a geometric property of a candidate pose, computable
before the camera goes there and before any planner is consulted.** It is a
predicate. You can evaluate it on every candidate in your list, throw away the ones
that fail, and only then spend planner time on what is left.

The reason nobody does this is a false assumption about cost. People assume that
testing visibility means rendering the scene, and rendering is expensive. It does
not. Testing whether a straight line from the camera to the target passes through
anything is a handful of subtractions, multiplications and comparisons. Section
3.3 measures it.

### 3.1 The wedge test on footprints

The cheapest version works in two dimensions and needs nothing but the positions
and radii of things on the table.

Look down on the table from above. The camera is at a point, the target is at
another point with some radius, and each obstacle is a circle. From the camera,
the target occupies a range of bearings — a wedge — and so does each obstacle.
The target is occluded exactly when an obstacle's wedge overlaps the target's
wedge **and** the obstacle is nearer than the target.

For a circle of radius `r` whose centre is at distance `d` from the camera, the
half-width of its wedge is

```
half angle = asin(r / d)
```

That is one inverse sine per obstacle. The bearing to its centre is one
two-argument arctangent, the function every language calls `atan2`, which turns a
pair of coordinates into an angle without losing the quadrant. The test is then
whether the difference between the two bearings is smaller than the sum of the two
half-angles.

The arithmetic is worth seeing on real sizes. The repository's standard object is
73.6 mm across, so its radius is 36.8 mm. Read the table as: an object of that
radius at that distance from the camera subtends that half-angle.

| Radius | Distance from camera | Half-angle |
| --- | --- | --- |
| 36.8 mm (the target) | 340 mm | 6.214° |
| 36.8 mm (the target) | 260 mm | 8.137° |
| 25 mm (a small obstacle) | 100 mm | 14.478° |
| 40 mm (a typical obstacle) | 150 mm | 15.466° |
| 40 mm (the same obstacle, further off) | 250 mm | 9.207° |

Take the fourth row against the first. A 40 mm obstacle at 150 mm blocks part of a
target at 340 mm whenever the two bearings differ by less than
15.466° + 6.214° = **21.68°**, and blocks all of it whenever they differ by less
than 15.466° − 6.214° = **9.25°**. One obstacle of that size therefore rules out
2 × 21.68 = 43.4 degrees of the 360 degrees of azimuth, which is **12.0 per cent**
of the ring, for the cost of one inverse sine and one `atan2`.

The test has one honest defect and it is important. **It ignores height, so it
rejects viewpoints that would have worked.** An obstacle 60 mm tall does not block
a camera looking down from 300 mm, but its footprint circle says it does. In the
worked scene of section 3.3, on the 222 candidates that survived the other
filters, the three-dimensional test kept 219 and the footprint test kept 150. It
threw away **69 viewpoints that were actually fine**, which is 31 per cent of the
list.

That would be a reasonable price if the footprint test were much cheaper. It is
not. Section 3.3 measures both, and the three-dimensional ray cast costs 39.6
nanoseconds per obstacle against the footprint test's 41.2. **The two-dimensional
shortcut is not a shortcut.** Use it only when a footprint is genuinely all you
have — a table scanned by a laser at one height, for instance — and use the ray
cast otherwise.

### 3.2 The ray cast in three dimensions

Represent each obstacle as an axis-aligned box, which is a box whose faces are
parallel to the world axes. Represent the sight line as a segment from the camera
centre to a point on the target. The question is whether the segment meets any
box.

The standard answer is the **slab method**. A box is the intersection of three
slabs, one per axis: everything between `x_lo` and `x_hi`, everything between
`y_lo` and `y_hi`, everything between `z_lo` and `z_hi`. For each axis, work out
the two values of the path parameter `t` at which the ray enters and leaves that
slab. Keep the largest of the three entry values and the smallest of the three
exit values. If the largest entry is not greater than the smallest exit, the ray
is inside all three slabs at once for some stretch, which means it is inside the
box.

In arithmetic, for one axis:

```
t1 = (lo - origin) / direction
t2 = (hi - origin) / direction
enter = max(enter, min(t1, t2))
exit  = min(exit,  max(t1, t2))
```

Three axes, so six subtractions, six multiplications by a reciprocal, six
comparisons for the minimum and maximum pairs, six more to fold them into the
running entry and exit, and one final comparison. Call it **about twenty-five
floating-point operations per ray-box pair.** That is the whole cost, and it is
why the test is worth running on everything.

Clamping matters. The sight line is a segment, not an infinite ray, so start the
entry value at 0 and the exit value at 1. Without the clamp, an obstacle behind
the camera or beyond the target counts as a blocker, and you will quietly reject
good viewpoints because of a box on the far side of the room.

One ray tells you whether the centre of the target is visible. That is rarely
enough, because a target half hidden behind a box still fails a measurement.
**Cast several rays, to points spread over the target, and use the fraction that
get through.** The worked scene casts five: the centre, four points at the
target's radius, and one at the top. Five rays give a visibility fraction in fifths,
which is coarse and sufficient — you want the difference between fully visible,
partly visible and hidden, and you do not need it to three decimal places.

The fraction is a genuine improvement on a boolean, because the three outcomes
want different treatment. A fully visible target is a candidate. A hidden target is
not. A partly visible target is a candidate only for finding, never for measuring,
because [a geometric measurement with a corner missing is simply wrong and nothing
in the arithmetic notices](07_making-it-work.md#4-occlusion-and-clutter).

### 3.3 What it costs, measured

The worked scene is a target 73.6 mm across and 100 mm tall standing at the
origin, eight obstacle cylinders on the table with radii from 25 mm to 50 mm and
heights from 60 mm to 150 mm, and an arm whose base is 450 mm away with a reach of
850 mm. The candidate list is the 720 poses of section 1. Visibility is tested
with five rays against eight boxes.

These are measured on an Apple M4, with Python 3.12.14 and NumPy 2.5.3, averaged
over at least a hundred repetitions. Read the table as: the operation, the total time
for the whole candidate list, and the unit cost.

| Operation | Total for 720 candidates | Unit cost |
| --- | --- | --- |
| ray against one box, slab method, vectorised | 228 µs for 720 × 8 pairs | **39.6 ns per ray-box pair** |
| footprint wedge test, vectorised | 237 µs for 720 × 8 pairs | 41.2 ns per candidate-obstacle pair |
| five-ray visibility fraction, vectorised | 1174 µs | 1.63 µs per candidate |
| the whole filter cascade, vectorised | 0.21–0.46 ms | 0.30–0.64 µs per candidate |
| the whole filter cascade, plain Python loops | 0.47–1.62 ms | 0.65–2.24 µs per candidate |

Two things in that table are the argument.

**The plain Python version is fast enough.** It is three to four times slower than
the vectorised one and it still filters 720 candidates in under two milliseconds.
You do not need NumPy, a graphics card, or a rendering library to do this. You
need a loop.

**The cost is nowhere near the cost of a move.** [The wrist
camera](08_the-wrist-camera.md#4-what-a-view-actually-costs) derives a theoretical
floor of 37 milliseconds for a small arm move from Universal Robots' own published
joint-speed cap, and observes that the real figure is hundreds of milliseconds to
seconds. Filtering the entire candidate list costs less than two per cent of the
most optimistic possible single move. There is no budget argument against doing it.

### 3.4 Where it earns its place, and where it does not

The same cascade was run twice on the same scene, changing only what the camera
has to see. In the first run the interesting face is the top of the object, so the
camera looks down from elevations of 15 to 60 degrees. In the second the
interesting face is a vertical side — reading a label, or measuring a profile — so
the camera looks from elevations of 0 to 30 degrees.

Read the table as: the filter, in the order it was applied, and how many of the
720 candidates were still alive after it.

| Filter | Looking at the top face | Looking at a side face |
| --- | --- | --- |
| all candidates | 720 | 720 |
| distance window, 191.2 mm to 339.9 mm | 432 | 432 |
| camera at least 60 mm above the table | 432 | 324 |
| angle to the surface normal at most 60° | 222 | 99 |
| camera within 850 mm of the arm base | 222 | 99 |
| **fully visible, five rays** | **219** | **38** |

The two columns say opposite things, and both are true.

Looking down at the top of an object, occlusion removed three candidates out of
222, which is 1.4 per cent. The elevation filter had already put the camera above
everything on the table, so nothing was left to be in the way. On this task the
occlusion predicate is close to worthless, and saying so is more useful than
pretending otherwise.

Looking at a vertical side face, occlusion removed 61 of 99, which is **62 per
cent**, leaving 38. Fifty-six of those 61 were partly visible rather than fully
hidden, which is the worst case in practice: a partly visible target produces a
mask, the mask looks plausible, and the measurement taken from it is wrong.

The general statement is that **occlusion binds when the sight line runs across
the table and does not bind when it comes down from above.** If your task lets you
look straight down, you have solved occlusion by geometry and can skip the test.
If it does not — because the feature is on the side, because the object is in a
bin, because the arm cannot get above it — the test is the difference between a
viewpoint set that works and one that fails on the third unit.

The ordering matters too. In the top-face run, the four cheap filters removed 498
of 720 candidates, which is 69.2 per cent, before a single ray was cast. Casting
rays on everything first would have cost 1.14 ms; casting them only on survivors
cost 0.46 ms for the whole cascade. **Put the tests that need no scene knowledge
first.** Distance, height and angle depend only on the candidate and the target.
Visibility depends on every obstacle, so it should see the shortest list you can
hand it.

### 3.5 The predicate, as pseudo code

```
function visible_fraction(camera, target_points, obstacle_boxes):
    blocked = 0
    for each point P in target_points:              # five: centre, four edges, one top
        for each box B in obstacle_boxes:
            enter = 0.0                             # the segment starts at the camera
            exit  = 1.0                             # and ends at P, so clamp to [0, 1]
            hit   = true
            for each axis a in (x, y, z):
                d = P[a] - camera[a]
                if |d| is essentially zero:
                    if camera[a] outside [B.lo[a], B.hi[a]]:
                        hit = false; break          # parallel to the slab and outside it
                    continue
                t1 = (B.lo[a] - camera[a]) / d
                t2 = (B.hi[a] - camera[a]) / d
                if t1 > t2: swap t1, t2
                enter = max(enter, t1)
                exit  = min(exit,  t2)
                if enter > exit:
                    hit = false; break              # the slabs do not overlap
            if hit:
                blocked = blocked + 1; break        # one blocker is enough for this point
    return 1 - blocked / count(target_points)
```

Three details in that are the reason for writing it out rather than describing it.

**The inner loop breaks on the first blocker.** You are asking whether anything is
in the way, not what is in the way, so the moment one box blocks the point you can
stop. On a cluttered scene most rays that are blocked at all are blocked by the
first or second box you test, which is why the measured cost is lower than
twenty-five operations times eight boxes would suggest.

**The clamp to `[0, 1]` is what makes it a segment.** Section 3.2 explains why.
This is the single most common bug in a hand-written visibility test.

**The axis-parallel case is handled explicitly.** A ray exactly parallel to a slab
divides by zero. Either special-case it, as above, or rely on the sign of infinity
behaving correctly, which it does in floating point but which is harder to read
and breaks under compiler flags that disable it.

Five jobs the occlusion predicate suits:

- removing candidate viewpoints before a motion planner is asked about any of them,
  which is what it was derived for
- deciding whether a second view is needed at all, since a fully visible target
  from the first pose is a reason to stop
- explaining a failure after the fact, because a recorded visibility fraction tells
  you whether the measurement was taken through a gap
- choosing which of several objects to look at first, by looking at the one whose
  visibility is about to be spoiled by the arm's own approach
- checking, in simulation, that a proposed camera mount can see the whole
  workspace before anyone drills a hole

Five jobs it cannot do:

- see anything the world model does not contain, which includes every object the
  perception system has not yet found, and the cable draped over the fixture
- handle transparent or reflective obstacles, which block a sight line optically in
  ways a solid box does not describe and do not block it at all in ways it does
- account for the arm's own links, unless you put them in the obstacle list, which
  means running forward kinematics for the candidate pose first
- tell you whether the target is recognisable, only whether light can reach the
  camera from it; a visible target in deep shadow still fails
- replace a reachability check, since a perfectly visible viewpoint inside a wall
  is still not a viewpoint

## 4. What makes a viewpoint good

Visibility is necessary and not sufficient. Four further properties decide whether
a visible viewpoint is worth going to, and each of them is a simple calculation on
the candidate's position.

### 4.1 Distance, which sets a window rather than a target

Going closer improves accuracy, as [the wrist
camera](08_the-wrist-camera.md#1-what-changes-when-the-camera-is-on-the-arm)
establishes, because one pixel covers `depth / fx` metres and the hand-eye error
grows with distance. Going closer also shrinks the field of view by the same
factor. So distance is bounded from both ends, and what you want is the window
between the bounds rather than the smallest number available.

The upper bound comes from resolution. Decide how many pixels across the object
has to be, and the distance follows from `d = (width / pixels) × fx`. Read the
table as: the pixel count you insist on, and the furthest you may stand from a
73.6 mm object to get it, on the repository's camera.

| Pixels across a 73.6 mm object | Furthest the camera may be |
| --- | --- |
| 40 | 509.9 mm |
| 60 | 339.9 mm |
| 80 | 254.9 mm |
| 100 | 203.9 mm |

Sixty pixels is a reasonable working figure and it lands on 339.9 mm, which is the
340 mm used throughout this area. That is not a coincidence; it is where the
figure came from.

The lower bound comes from the field of view. The frame is `d × 320 / fx` wide, so
insisting the object occupy no more than a third of it gives
`d ≥ 73.6 × 3 × 277.1 / 320` = **191.2 mm**. Below that the object starts to run
off the edge of the picture, and an object touching the frame edge has no measurable
boundary on that side.

The window is therefore **191.2 mm to 339.9 mm** for this object on this camera,
and it is worth noticing how narrow that is. It is a factor of 1.78 in distance.
Any candidate outside it fails, and in the worked scene of section 3.3 that first
filter alone removed 288 of 720 candidates.

Two things also live at the near end and are easy to forget. A depth camera has a
minimum range below which it returns nothing; the RealSense D405 that
[the wrist camera](08_the-wrist-camera.md#71-the-camera-on-the-arm) recommends is
a short-range part for exactly this reason. And the camera is on the end of an
arm, so at close range the arm's own wrist and the gripper fingers start to appear
in the frame.

### 4.2 Angle to the surface normal

A **surface normal** is the direction a surface faces, at right angles to it. If
the camera looks along the normal, it sees the surface face-on. If it looks at an
angle `α` away from the normal, the surface appears compressed by `cos α` in that
direction. This is called **foreshortening**.

The consequence for a measurement is direct, because the apparent width in pixels
falls by the same factor. Read the table as: the angle between the sight line and
the surface normal, the factor the apparent width is multiplied by, and what that
does to a 73.6 mm object viewed from 340 mm, which is 60.0 pixels head-on.

| Angle off the normal | Width factor | Pixels across |
| --- | --- | --- |
| 0° | 1.000 | 60.0 |
| 15° | 0.966 | 57.9 |
| 30° | 0.866 | 51.9 |
| 45° | 0.707 | 42.4 |
| 60° | 0.500 | 30.0 |
| 75° | 0.259 | 15.5 |

Sixty degrees costs half your resolution, which is the same as doubling the
distance. That is the natural place to put the cap, and it is what the worked
scene uses. Below 30 degrees the loss is under 14 per cent and not worth worrying
about.

There are two further reasons to cap the angle that have nothing to do with
resolution. A depth sensor's returns degrade at grazing incidence, because less of
the projected pattern or the emitted pulse comes back. And a grazing view of a
curved object shows you its silhouette rather than its face, so the boundary you
segment is a horizon on the object rather than an edge of it, and it moves when
the camera moves.

This test is also the one piece of viewpoint reasoning that ROS 2 already ships.
The `max_view_angle` field of
[`moveit_msgs/msg/VisibilityConstraint`](https://github.com/moveit/moveit_msgs/blob/ros2/msg/VisibilityConstraint.msg)
is exactly this angle, documented in the message itself as the angle between the
normal to a target disc and the direction from the sensor. The same message models
the sight line as a cone with a configurable number of sides, which is the wedge
of section 3.1 in three dimensions. It is worth reading even if you do not use
MoveIt, and its own comments are candid about what it leaves out: it says plainly
that the constraint "does NOT enforce minimum or maximum distances between the
sensor and the target, nor does it enforce the target to be in the field of view".
Those are sections 4.1 and 4.4, and you still have to supply them.

### 4.3 Baseline against the views you already have

The first viewpoint is chosen on its own merits. Every viewpoint after it is
chosen relative to the ones already taken, and the quantity that matters is the
**baseline**, which is the straight-line distance between two camera positions.

[Baseline, not count](08_the-wrist-camera.md#5-baseline-not-count) derives the
relationship and it is worth having to hand here:

```
depth error = z² × e / (fx × b)
```

for an object at distance `z`, a matching error of `e` pixels, and a baseline `b`.
The baseline is in the denominator, so it is the only term you can improve by
choosing where to stand.

On a sphere of radius `R` around the target, two viewpoints separated by an angle
`β` have a baseline of `b = 2R sin(β/2)`. That is the conversion between the
candidate grid's coordinates and the quantity that decides accuracy. Read the
table as: the angular separation between two viewpoints at a 340 mm radius, the
baseline it produces, and the resulting depth uncertainty from a one-pixel
matching error.

| Angular separation | Baseline | Depth uncertainty |
| --- | --- | --- |
| 10° | 59.3 mm | 7.04 mm |
| 20° | 118.1 mm | 3.53 mm |
| 35° | 204.5 mm | 2.04 mm |
| 60° | 340.0 mm | 1.23 mm |
| 90° | 480.8 mm | 0.87 mm |

Thirty-five degrees of separation is the row to remember. It produces the 200 mm
baseline that [the wrist camera's own
table](08_the-wrist-camera.md#5-baseline-not-count) prices at 2.1 mm, and it is
a modest move — a fifth of a turn round the object.

The practical rule is to **take the widest separation over which the target stays
fully visible and the surface stays within the angle cap**. Those two conditions
are what stop you from simply going to 180 degrees, and they are both already
computed: visibility by section 3, angle by section 4.2. In the worked scene, the
widest surviving pair for the side-face task was 466.2 mm apart, which puts the
depth uncertainty at 0.51 mm.

The parallax method in [two photos from one moving
camera](03_programmed-methods.md#23-two-photos-from-one-moving-camera) is worth
naming here because it changes what the second viewpoint has to be. That method
does not need a wide angular separation at all; it needs a known sideways
translation, and it works with 40 mm. If your second view exists to undo the
outward bias of a plane measurement, a short sideways step is enough, and you
should not pay for a 90-degree arc you do not need.

### 4.4 Whether the arm can actually get there

A viewpoint the arm cannot reach is not a viewpoint, and this is the test that
catches the most beginners, because a pose can look entirely reasonable and still
be unavailable. [The workspace and its
holes](../08_arm-movement/02_reaching-and-reachability.md#2-the-workspace-and-its-holes)
covers why. The short version is that a robot arm's reachable set is not a ball;
it has a hollow centre it cannot fold into, it has orientations it can only achieve
from one side, and it has poses that are reachable in principle but only through a
singularity.

The tests split into three tiers by cost, and you should run them in this order.

A **distance bound** is one subtraction and one comparison. The camera position
must lie between the arm's minimum and maximum reach from the shoulder. This
rejects a great deal for almost nothing and it is what the worked scene uses.

An **inverse kinematics query** asks whether any joint configuration puts the
camera at that pose. It is milliseconds for a closed-form solver on a
six-jointed arm and it is the first test that can say no for a reason you would not
have guessed. It also returns the configuration, which you need for the next tier.

A **collision-checked plan** asks whether the arm can get there from where it is
without hitting anything. This is the expensive one and it is the one every filter
above exists to protect.

**Run the free tests before the expensive ones.** That is the whole architectural
point of this document. In the worked scene the four cheap tests plus visibility
took 720 candidates down to 38, so the planner is asked 38 questions instead of
720, and the questions it is asked are ones it has a good chance of answering yes
to.

One test that is easy to forget: the camera must not be inside anything. A
candidate 150 mm from the target at zero elevation can be inside the table. The
worked scene requires the camera to be at least 60 mm above the table surface, and
that one line removed 108 candidates in the side-face run.

### 4.5 Why not to fold the four into one score

The obvious next step is to turn the four properties into numbers, weight them,
add them up, and take the highest. Resist it, for three reasons.

**The weights are unjustifiable.** How many millimetres of extra distance is one
degree of view angle worth? There is no answer, and the number you pick will be
tuned on one scene and wrong on the next.

**A score hides a failure.** A candidate that is unreachable should be removed, not
given a low score, because a low score can be outweighed by a high score somewhere
else in the sum and the candidate comes back. This is the failure mode where a
system confidently drives at a pose it cannot reach.

**Predicates compose and scores do not.** Two predicates are combined by `and`, and
the result is still a predicate with the same meaning. Two scores are combined by
a weighted sum that means nothing in particular, and adding a third term changes
the ranking of everything.

The structure that works is to use predicates for everything that can fail, and
then one single honest score over the survivors. A good default for that score is
the pixels across the target, which is `width × fx / distance` and which you
already have. It is a real quantity, it means something, and it needs no weights.
When a second view is being chosen, the score is the baseline instead, for the
reasons in section 4.3.

## 5. Choosing the viewpoint set offline

If the objects are roughly where you expect them, the right answer is to work out
two or three good viewpoints once, store them, and drive to them by name. This
section is how to work them out, and it contains one result that cuts against
what people assume.

### 5.1 The coverage arithmetic, and the surprise in it

Suppose the workspace is a 600 by 400 mm area of table and the camera looks
straight down at it. The frame at height `h` is `h × 320 / fx` wide by
`h × 240 / fx` tall. Allow ten per cent overlap between adjacent views so nothing
falls in a seam. Then a grid of `nx` by `ny` viewpoints needs a height of

```
h = max( (600/nx × 1.1) × fx / 320 , (400/ny × 1.1) × fx / 240 )
```

and the resolution follows from that height. Read the table as: the grid, the
height it forces, and how many pixels a 73.6 mm object spans from there.

| Grid | Views | Tile covered | Height needed | One pixel | Pixels across 73.6 mm |
| --- | --- | --- | --- | --- | --- |
| 1 × 1 | 1 | 660 × 440 mm | 571.5 mm | 2.062 mm | 35.7 |
| 2 × 1 | 2 | 330 × 440 mm | 508.0 mm | 1.833 mm | 40.1 |
| 1 × 2 | 2 | 660 × 220 mm | 571.5 mm | 2.062 mm | 35.7 |
| 2 × 2 | 4 | 330 × 220 mm | 285.8 mm | 1.031 mm | 71.4 |
| 3 × 2 | 6 | 220 × 220 mm | 254.0 mm | 0.917 mm | 80.3 |
| 3 × 3 | 9 | 220 × 147 mm | 190.5 mm | 0.688 mm | 107.1 |

The surprise is in rows two and three. **Going from one viewpoint to two buys you
almost nothing, and which two you choose may buy you nothing at all.** Splitting
the long axis takes you from 35.7 to 40.1 pixels, a gain of 12 per cent. Splitting
the short axis takes you from 35.7 to 35.7, a gain of zero, because the height was
already set by the other axis.

The reason is that a camera's frame has two dimensions and the binding constraint
is whichever one runs out first. Halving the tile in one direction does nothing
until you also halve it in the other. Resolution from coverage therefore improves
roughly as the square root of the view count, and 2 × 2 = four views is the first
step that actually doubles it, from 35.7 to 71.4 pixels.

That has a clear consequence for how to think about a two-viewpoint or
three-viewpoint set. **Do not choose them for coverage. Choose them for angle and
for occlusion.** Two views that both cover the whole table from different sides
buy you the thing a single view cannot have at any resolution: a second line of
sight past whatever is in the way, and a baseline. Two views that tile the table
buy you 12 per cent.

### 5.2 How to pick them

The procedure is the filter cascade of sections 3 and 4, run once, offline, against
the worst scene you expect rather than the scene in front of you.

1. Write down the target points you must be able to see. For a table-top cell that
   is a grid over the working area, at the heights objects actually stand at, not a
   single point in the middle.
2. Write down the obstacles that are always there. Fixtures, the bin walls, the
   feeder, the tool changer. Leave out the objects being handled, because they move.
3. Enumerate candidates on a sphere, as in section 1.
4. Apply the predicates: distance window, angle to the normal, reachability,
   visibility of every target point.
5. Take the candidate that sees the most target points. Remove those points. Repeat
   until every point is covered. This is the greedy set-cover from section 2.1, run
   once at your desk rather than repeatedly on the robot.
6. If the task needs two views of the same object, take the second as the surviving
   candidate furthest from the first, by section 4.3.
7. Drive the arm to each chosen pose and check it. This step is not optional and it
   is the reason the whole approach is worth having.

Step 7 deserves the emphasis. An offline set is valuable because it can be tested,
and a set that has not been tested has thrown away its only advantage.

Five jobs a fixed offline viewpoint set suits:

- any cell where the objects arrive in roughly known places, which is most
  production cells
- any cell with a cycle time to meet, because the motion is identical every run and
  can be timed
- any cell that must be explained to a safety reviewer, because the trajectories
  are a short finite list
- teaching and commissioning, since an operator can be shown the poses and can
  adjust them
- a first implementation of anything, because it establishes what the online
  version would have to beat

Five jobs it cannot do:

- cope with an object outside the region the set was chosen to cover
- cope with new obstacles, since the visibility was computed against a fixed
  obstacle list
- reconstruct an object it has no model of, which needs the view count to follow
  the geometry
- handle a workspace too large for a practical number of fixed views, where the
  square-root scaling in section 5.1 becomes expensive
- adapt when the first view reveals that the second one is now pointless, which is
  precisely the case online planning was invented for

## 6. The order to visit them in

When several objects have to be looked at, the viewpoints have been chosen and the
only remaining question is the sequence. The sequence decides the total arm travel,
and arm travel is the dominant cost in the whole exercise.

This is a **travelling salesman problem**: given a set of places and the distance
between each pair, find the shortest route visiting all of them. It is NP-hard, so
no efficient method is known that always finds the best route. The relevant
question for a robot arm is not how to solve it but whether solving it matters.

It usually does not, for two reasons.

**The instances are tiny.** A cell looking at five to ten objects has five to ten
places. At that size you can find the exact answer by trying every order: seven
places fixed at a start point is 6! = 720 orders, which a plain loop evaluates in
milliseconds. There is no need for an approximation at all below about ten places.

**The greedy answer is close anyway.** **Nearest-neighbour** ordering means:
start where you are, go to the closest place you have not visited, repeat. It is
two lines of code. Measured over a thousand random instances of points scattered
in a 600 by 400 mm area, with the exact optimum computed by exhaustive search, it
comes out as follows. Read the table as: the number of places, how much longer the
greedy route is than the best possible on average, and how bad it gets.

| Places | Greedy, mean | Greedy, worst | Greedy then 2-opt, mean | 2-opt, worst | 2-opt finds the optimum |
| --- | --- | --- | --- | --- | --- |
| 5 | 1.037× | 1.477× | 1.006× | 1.335× | 91.9% |
| 6 | 1.051× | 1.442× | 1.009× | 1.401× | 86.1% |
| 8 | 1.074× | 1.436× | 1.016× | 1.381× | 73.8% |
| 10 | 1.097× | 1.422× | 1.021× | 1.238× | 59.3% |

Greedy costs between four and ten per cent more travel than the best possible on
average, and its worst case in these trials was 48 per cent worse. **2-opt** is
the standard repair: repeatedly pick two places in the route, reverse the stretch
between them, and keep the change if the route got shorter. Running 2-opt on the
greedy route brings the average within two per cent of optimal and finds the exact
optimum outright most of the time. It is about fifteen lines of code and it runs
in microseconds at these sizes.

The recommendation is therefore: **use nearest-neighbour, and add 2-opt if the
instance is large enough that you cannot simply enumerate.** Reach for
[OR-Tools](https://github.com/google/or-tools), which has a proper routing solver
under the Apache 2.0 licence, only when you have hundreds of places, which a robot
arm looking at objects on a table does not.

One special case is worth knowing because it removes the problem entirely. If the
viewpoints lie on a ring around a single object — which is what section 4.3's
advice produces — then the total travel round the ring is the ring's
circumference regardless of how many viewpoints are on it. A 300 mm ring is
1885 mm around whether you stop at two places or six. Going round in order is
optimal, and there is nothing to decide.

Two honest cautions about all of the above. The distance that matters is the arm's
travel, not the straight line between camera positions, and those differ whenever
the arm has to go round something or change configuration. And a route that is
shortest in distance is not necessarily shortest in time, because a short move
through an awkward joint configuration can take longer than a long move through a
comfortable one. If the ordering genuinely matters to your cycle time, measure
pair-to-pair times on the real arm and put those in the distance matrix instead of
Euclidean distances.

Five jobs greedy nearest-neighbour ordering suits:

- any inspection sequence over a handful of known points, which is the common case
- ordering a set of grasps, where the same arithmetic applies to approach poses
- a first implementation, since it is two lines and gives you a baseline to beat
- cases where the points change every cycle, so a precomputed optimal route is not
  available anyway
- cases where the cost matrix is approximate, since optimising an approximate cost
  precisely is wasted effort

Five jobs it cannot do:

- guarantee anything, its worst case in the trials above being 48 per cent over
- respect a required order, such as looking at the near objects before the arm's
  own motion occludes the far ones
- account for the arm's configuration changes, which a Euclidean distance matrix
  does not see
- handle time windows, such as a part that must be inspected within so many seconds
  of arriving
- scale past a few dozen points, where a real routing solver starts to earn its
  place

## 7. The libraries, and what runs on an Apple Silicon Mac

The honest headline is that nothing in this document needs a library. The whole
cascade is arithmetic on a few hundred numbers, and section 3.3 measures a plain
Python implementation of it at under two milliseconds. The libraries below are
worth knowing because they solve the neighbouring problems, and because you will
find them in other people's viewpoint-planning code.

Every licence was read from the repository's own LICENSE file. Read the table as:
the library, what it contributes to this problem, its licence, and whether it runs
on an Apple Silicon Mac without an NVIDIA graphics card.

| Library | What it gives you here | Licence | Apple Silicon |
| --- | --- | --- | --- |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | `mj_ray` and `mj_multiRay` cast rays against the whole simulated scene, with the geometry you already have | Apache 2.0 | yes, arm64 wheels on PyPI |
| [trimesh](https://github.com/mikedh/trimesh) | ray casting against triangle meshes, when boxes are too coarse | MIT | yes, pure Python |
| [Open3D](https://github.com/isl-org/Open3D) | ray casting against a scene of meshes, plus point-cloud handling | MIT | yes, arm64 wheels on PyPI |
| [FCL](https://github.com/flexible-collision-library/fcl) and [python-fcl](https://github.com/BerkeleyAutomation/python-fcl) | distance and collision queries between convex shapes, which is the reachability tier of section 4.4 | BSD 3-clause both | yes, arm64 wheels for python-fcl |
| [OctoMap](https://github.com/OctoMap/octomap) | the occupancy octree that information-gain formulations need | New BSD for the library; **GPL v2 for the octovis viewer** | builds from source |
| [Embree](https://github.com/embree/embree) | fast ray tracing, when you have millions of rays rather than thousands | Apache 2.0 | yes, its README lists macOS Arm64 as a supported platform |
| [MoveIt 2](https://github.com/moveit/moveit2) and [moveit_msgs](https://github.com/moveit/moveit_msgs) | `VisibilityConstraint`, inverse kinematics, and the planner all of this exists to protect | BSD 3-clause both | only by building ROS 2 from source |
| [OR-Tools](https://github.com/google/or-tools) | a routing solver, for section 6 at a scale that needs one | Apache 2.0 | yes, arm64 wheels on PyPI |
| [OMPL](https://github.com/ompl/ompl) | the sampling-based planners underneath MoveIt | 3-clause BSD | builds from source |

The OctoMap row is the licence trap in this list. The library is New BSD and the
`octovis` viewer that ships in the same repository is GPL v2, stated in its own
[LICENSE file](https://github.com/OctoMap/octomap/blob/devel/octovis/LICENSE.txt),
because it links against libQGLViewer. Linking the library into a product is one
decision and shipping the viewer is a different one.

One repository that gets cited in this area is worth a warning.
[nbvplanner](https://github.com/ethz-asl/nbvplanner) is the reference receding-horizon
next-best-view implementation and it is the one most papers point at. **It has no
LICENSE file anywhere in the repository.** A `package.xml` inside it declares
"ASL 2.0", which is not a licence text and is not a substitute for one. Read it for
the method; do not ship it without asking the authors.

On Apple Silicon specifically, the split is clean and the ROS side is the problem.
Everything numeric in this document runs natively: NumPy, MuJoCo, Open3D, trimesh,
python-fcl and OR-Tools all publish `macosx_11_0_arm64` wheels on PyPI, and trimesh
is pure Python so it needs no wheel at all. There is no CUDA anywhere in a
viewpoint filter, because there is no neural network in one.

ROS 2 is a different matter and the official position is worth quoting rather than
guessing at. ROS Enhancement Proposal 2000, always written REP 2000, is the
document that defines which platforms a ROS 2 release supports and how well. It
lists macOS for the current Kilted Kaiju distribution as **Tier 3, amd64 only,
with compilation from source as the only delivery mechanism**. Apple Silicon is
not listed at all. You can read the table in
[rep-2000.rst](https://github.com/ros-infrastructure/rep/blob/master/rep-2000.rst).
The practical consequence is that the filter described here should be written as
plain Python or C++ that does not import anything from ROS, so that it can be
developed and tested on the Mac and then called from a ROS 2 node on the Linux
machine that drives the arm. That separation is worth keeping for its own sake, and
[licences and platforms, section 3](06_licences-and-platforms.md#3-what-runs-on-an-apple-silicon-mac)
makes the same argument for the perception code generally.

## 8. The whole selection, as pseudo code then Python

The sequence that chooses a viewpoint, with every decision from the sections above
in it. In pseudo code first.

```
# choosing where to look, once, for one target

target      = the point to observe, and a few points around it
obstacles   = the boxes you know about, from the world model
taken       = the camera positions already used this cycle (empty at the start)

candidates = []
for azimuth in 0, 10, ... 350 degrees:
    for elevation in the range the task allows:
        for radius in the distance window:
            candidates.append(the pose on that sphere looking at the target)

# the predicates, cheapest first. Each one is an "and", not a weight.
keep = candidates
keep = [c in keep if distance(c, target) within [d_near, d_far]]      # 4.1
keep = [c in keep if c is at least clearance above the table]         # 4.4
keep = [c in keep if angle(view(c), surface normal) <= angle cap]     # 4.2
keep = [c in keep if within_reach_bound(c)]                           # 4.4, tier 1
keep = [c in keep if visible_fraction(c, target, obstacles) == 1.0]   # 3.5

if keep is empty:
    the target cannot be seen from anywhere the arm can stand.
    This is an answer. Report it; do not lower the thresholds silently.

# one score over the survivors, and only one.
if taken is empty:
    best = the candidate with the most pixels across the target        # 4.5
else:
    best = the candidate furthest from everything in taken             # 4.3

# only now does anything expensive happen
solution = inverse_kinematics(best)                                    # 4.4, tier 2
if solution is none:
    drop best from keep and take the next one
plan = plan_motion(current pose, solution)                             # 4.4, tier 3
```

Two things in that are the shape of the argument. **The empty case is an answer,
not an error.** If no viewpoint survives, the honest response is to say the target
is not observable from this cell, which is a fact somebody needs to know. Quietly
relaxing the angle cap until something survives produces a viewpoint that will
produce a bad measurement, and the bad measurement will be blamed on the
segmentation model. [Declining, as a
mechanism](07_making-it-work.md#6-declining-as-a-mechanism-rather-than-an-intention)
makes the general version of this argument.

**Inverse kinematics is below the filter, not above it.** Every line before it
costs nanoseconds. It costs milliseconds. Putting it last is the entire
optimisation.

The same thing in Python, with only the parts that carry a decision:

```python
import numpy as np

FX, W, H = 277.1, 320, 240          # the repository's camera
OBJ_W    = 0.0736                   # metres across, the standard object

# 1. The distance window comes from resolution at one end and framing at the other.
d_far  = OBJ_W / 60 * FX            # at least 60 px across  -> 0.3399 m
d_near = OBJ_W * 3 * FX / W         # at most 1/3 of the frame -> 0.1912 m

# 2. Candidates on a sphere centred on the TARGET, not on the robot.
az = np.radians(np.arange(0, 360, 10))
el = np.radians(np.array([0.0, 10.0, 20.0, 30.0]))
rr = np.linspace(d_near, d_far, 5)
A, E, R = (a.ravel() for a in np.meshgrid(az, el, rr, indexing="ij"))
cam = target + np.stack([R * np.cos(E) * np.cos(A),
                         R * np.cos(E) * np.sin(A),
                         R * np.sin(E)], axis=1)

# 3. The cheap predicates. Order matters: each one shortens the list for the next.
d    = np.linalg.norm(cam - target, axis=1)
view = (cam - target) / d[:, None]
keep  = (d >= d_near) & (d <= d_far)
keep &= cam[:, 2] >= table_z + 0.060            # do not stand inside the table
keep &= (view @ surface_normal) >= np.cos(np.radians(60.0))   # 60 deg cap
keep &= np.linalg.norm(cam - shoulder, axis=1) <= reach

# 4. Visibility, by the slab method, on the survivors only. ~25 flops per ray-box.
def visible_fraction(origins, points, box_lo, box_hi):
    o = origins[:, None, None, :]                       # candidates x points x boxes
    dirn = points[None, :, None, :] - o
    inv = 1.0 / np.where(np.abs(dirn) < 1e-12, 1e-12, dirn)
    t1 = (box_lo[None, None, :, :] - o) * inv
    t2 = (box_hi[None, None, :, :] - o) * inv
    enter = np.maximum(np.minimum(t1, t2).max(axis=3), 0.0)   # clamp: it is a segment
    leave = np.minimum(np.maximum(t1, t2).min(axis=3), 1.0)
    return 1.0 - np.any(leave >= enter, axis=2).mean(axis=1)

idx = np.flatnonzero(keep)
frac = visible_fraction(cam[idx], target_points, box_lo, box_hi)
survivors = idx[frac > 0.999]                    # fully visible only, for measuring

# 5. One score, and it is a real quantity: how many pixels across the object is.
pixels = OBJ_W * FX / np.linalg.norm(cam[survivors] - target, axis=1)
best = survivors[np.argmax(pixels)]

# 6. A second view is chosen by baseline, not by score.
if taken:
    b = np.linalg.norm(cam[survivors][:, None, :] - np.array(taken)[None, :, :], axis=2)
    second = survivors[np.argmax(b.min(axis=1))]
```

Three details in that code are the reason for writing it out.

**`enter` starts at 0.0 and `leave` at 1.0.** Those two constants turn an infinite
ray into the segment between the camera and the target. Without them, a box behind
the camera reports a hit and you lose good viewpoints for no visible reason.

**The visibility test runs on `cam[idx]`, not on `cam`.** The cheap predicates ran
first, and in the worked scene they removed 69.2 per cent of the list before a
single ray was cast. Reversing those two lines costs nothing in correctness and
roughly triples the time.

**The second view maximises the *minimum* distance to the views already taken.**
Maximising the mean would let a candidate that is very far from one existing view
and almost on top of another come out on top, which is exactly the case where
[the baseline is short](08_the-wrist-camera.md#5-baseline-not-count) and the depth
uncertainty is large.

## 9. What is specific to choosing where to look

Worth separating, because much of the advice in this area was written for a camera
that stays where it is put, and it is not always obvious which parts stop applying
once the camera can move.

**Occlusion becomes a filter rather than a fate.** For a fixed camera it is a
property of the installation, and
[making it work](07_making-it-work.md#4-occlusion-and-clutter) is right to treat it
as something to diagnose after the fact. For a camera on an arm it is a function of
a pose you have not committed to yet, so it can be evaluated on every candidate for
forty nanoseconds each and used to remove them. The same physical phenomenon, in
one case a problem and in the other a tool.

**The expensive step is the move, so everything upstream of it is free.** Section
3.3's measurements are not interesting because the filter is fast. They are
interesting because the thing it protects is ten thousand times slower. Any test
you can perform before committing the arm should be performed, and the question
"is this worth computing" essentially never has the answer no.

**The candidate set is a modelling decision, not a search.** Nothing here searches
a continuous space. The sphere, the azimuth spacing and the elevation range are
choices you make, and they matter more than anything the filter does afterwards.
An elevation range that excludes the only angle from which the feature is visible
cannot be rescued by a better score.

**A viewpoint is chosen relative to the ones you already have.** The first
viewpoint is chosen for resolution. The second is chosen for baseline, and by
section 4.3 that is a completely different criterion, which is why the same scoring
function should not be used for both. This is the point where this document and
[the wrist camera](08_the-wrist-camera.md#5-baseline-not-count) meet: it answers
how many, this answers which, and its answer to "which is the second one" is
"as far from the first as visibility allows".

**Reporting that there is no viewpoint is a feature.** A filter cascade that
returns an empty list has told you something true about the cell, and it has told
you before the arm moved. A system that always produces a viewpoint, by lowering
its thresholds until one survives, has replaced that information with a bad
measurement.

Five jobs the approach in this document suits:

- deciding where to send a wrist camera, which is what it was derived for
- checking at design time whether a proposed camera mount can see the whole
  workspace, by running the same cascade over a grid of target points
- choosing the second of two views so that the baseline is as wide as visibility
  allows
- ordering a sequence of inspections so the arm travels as little as possible
- explaining after the fact why one measurement in a hundred was wrong, because the
  visibility fraction was recorded and was not 1.0

Five jobs it cannot do:

- find an object, which is what the rest of this area is for; every test here
  assumes you already know roughly where the target is
- account for anything missing from the world model, which includes every object
  not yet detected and every cable, clamp and offcut nobody modelled
- decide the lighting, which has as much effect on whether a measurement works and
  appears nowhere in the geometry
- replace a motion planner, since a reachable, visible, well-angled pose can still
  be unreachable from where the arm currently is
- help a fixed camera at all, whose viewpoint was decided when someone tightened
  the bolts
