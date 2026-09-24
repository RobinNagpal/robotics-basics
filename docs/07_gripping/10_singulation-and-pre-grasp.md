# Singulation and pre-grasp manipulation

Every document in this area so far has assumed that a grasp exists and the job is
to find it, rate it and execute it. This one starts from the case where no good
grasp exists yet, and the robot's next action is therefore not a pick at all. It
is a push, a sweep, a nudge or a topple whose only purpose is to make a pick
possible a second later.

Two names cover this. **Singulation** means separating objects that are touching
so that they can be handled one at a time; **decluttering** is the same word used
when the aim is to open up space rather than to isolate one particular thing.
**Pre-grasp manipulation** is the wider category: any deliberate action on an
object that does not hold it, performed so that a later action can hold it.
Singulation is one member of that category. Sliding a plate away from a wall,
tipping a box onto its narrow face and spinning a part so the arm can reach it
are the others.

This is routine work in a real cell and it is almost absent from tutorials,
because a tutorial scene has one object on an empty table and that object is
always graspable. A tote of parts is not like that. The single most common reason
an otherwise correct pick-and-place system stalls in production is that it looked
at a pile, found nothing it could grip, and had no action available except to look
again.

## Who this is for

Someone who has a working grasp planner — whether the geometric one from
[choosing a grip](03_choosing-a-grip.md) or a downloaded model from
[models that grasp](04_models-that-grasp.md) — and has found that it sometimes
returns nothing, or returns something the arm cannot execute. You do not need to
have written a pushing controller. Every term is explained where it first
appears.

This document is about *when and why* to push. The physics of pushing — whether a
pushed object slides or tips, the friction cone, the motion cone and the limit
surface — belongs to [pushing and sliding](09_pushing-and-sliding.md), and is
referred to rather than repeated here. If you want to know how far an object will
rotate for a given contact point, that is the document to read. If you want to
know whether pushing is the right thing to do at all, stay here.

## Contents

1. [The situation this document is about](#1-the-situation-this-document-is-about)
2. [Why touching objects have to be separated](#2-why-touching-objects-have-to-be-separated)
3. [The separating moves](#3-the-separating-moves)
4. [Choosing the separation direction](#4-choosing-the-separation-direction)
5. [Separate, or pick from the pile anyway](#5-separate-or-pick-from-the-pile-anyway)
6. [Telling whether separation worked](#6-telling-whether-separation-worked)
7. [Pre-grasp manipulation as a category](#7-pre-grasp-manipulation-as-a-category)
8. [The feasibility test: will the grasp exist afterwards](#8-the-feasibility-test-will-the-grasp-exist-afterwards)
9. [Learned approaches, and their licences](#9-learned-approaches-and-their-licences)
10. [What runs on an Apple Silicon Mac](#10-what-runs-on-an-apple-silicon-mac)
11. [Where this sits in the rest of the area](#11-where-this-sits-in-the-rest-of-the-area)

---

## 1. The situation this document is about

A pick begins with a request: pick up an object from this region. Perception
produces a set of candidate objects. The grasp planner produces, for each
candidate, a set of poses the gripper could adopt. The motion planner checks that
the arm can reach one of them. Somewhere in that chain, the answer comes back
empty.

There are exactly four reasons it can come back empty, and they need different
responses.

**Nothing was detected.** The region is empty, or the sensor cannot see what is
there. This is a perception problem and it belongs to
[object perception](../06_object-perception/01_overview.md). No amount of pushing
helps if the camera returns nothing.

**Something was detected but it is not one object.** Two or three objects were
reported as a single blob, because the method that found them merges things that
touch. Any grasp computed on that blob is computed on a shape that does not
exist. This is the singulation case, and section 2 explains why the merging
happens.

**One object was detected correctly and no grasp fits it where it is.** The
object is real, the measurement is right, and the gripper cannot get to it: a
neighbour is too close, a wall is behind it, the face you need is underneath, or
the grasp axis points somewhere the arm cannot reach. This is the pre-grasp
manipulation case, and section 7 is about it.

**A grasp exists and the arm cannot execute it.** The pose is valid and
unreachable, or reachable only through a configuration that collides. This is an
arm problem, covered in
[reaching and reachability](../08_arm-movement/02_reaching-and-reachability.md).
Sometimes the cheapest fix is still to move the object, which puts it back in
this document.

### 1.1 Two failures that look identical from the outside

The second and third cases produce the same symptom — the system reports "no
grasp" and stops — and they need opposite responses. Getting them the wrong way
round wastes a great deal of time, so it is worth stating the distinguishing
test plainly.

If the reported object's measured dimensions are larger than any single object in
your part family, you have a merged blob and you need to separate. If the
dimensions are plausible for one part and the grasp planner still returns
nothing, you have a real object that is blocked and you need a pre-grasp action.

That test is cheap, it needs nothing you do not already have, and it turns one
undiagnosable failure into two diagnosable ones. It also fails in one specific
way worth knowing: two identical small parts side by side can merge into a blob
whose dimensions are exactly those of one larger part in the same family. If your
family contains a part that is about twice another part in one dimension, this
test cannot separate the two cases and you need the cluster-gap check from
section 6 instead.

## 2. Why touching objects have to be separated

Two independent reasons, which is why the requirement is so hard to design
around. Removing one of them does not remove the need.

### 2.1 Every cheap perception method merges touching objects

The standard table-top recipe is to take a depth picture as a cloud of
three-dimensional points, delete the largest flat surface in it, and group what
remains into clumps of nearby points. Each clump is called an object.
[Programmed methods, section 1.6](../06_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster)
sets out the recipe and states its limitation directly: objects that touch each
other cluster into one.

The reason is in the algorithm's one parameter. Euclidean cluster extraction takes
a **cluster tolerance**, which is the distance below which two points are
considered to belong to the same object. Two objects whose surfaces come closer
than that tolerance produce points closer than that tolerance, and the algorithm
joins them. It has no other information to go on.

The tolerance cannot simply be made small. The same parameter has to be large
enough that a *single* object does not shatter into several clusters, and what
sets that floor is the spacing of the points on the object's own surface. Point
clouds are almost always downsampled onto a voxel grid first — the cloud is
divided into cubes of a fixed size and each occupied cube contributes one point —
so the point spacing is set by the cube size.

The Point Cloud Library's own cluster extraction tutorial makes both choices
explicitly. Reading them from
[the tutorial source in the PCL repository](https://github.com/PointCloudLibrary/pcl/blob/master/doc/tutorials/content/sources/cluster_extraction/cluster_extraction.cpp):

```cpp
vg.setLeafSize (0.01f, 0.01f, 0.01f);   // 10 mm voxels
...
ec.setClusterTolerance (0.02);          // 20 mm, and the comment says "2cm"
ec.setMinClusterSize (100);
ec.setMaxClusterSize (25000);
```

Those two numbers are related, and the relation is arithmetic you can check. With
10 mm cubes, two points that survive downsampling from cubes that touch only at a
corner sit about one cube diagonal apart, and the diagonal of a 10 mm cube is
10 × √3 = 17.32 mm. A tolerance below that risks splitting one object in two. The
tutorial's 20 mm leaves 20 − 17.32 = 2.68 mm of margin, which is thin but
deliberate.

The consequence for singulation is direct. **With those settings, two objects
report as separate only when their surfaces are more than 20 mm apart.** Anything
closer is one cluster, whatever it really is.

### 2.2 The gripper needs a channel, and here is how wide

The second reason is mechanical and has nothing to do with perception. A
two-finger gripper does not close onto a point. It arrives as a physical body that
must occupy the space either side of the object before it can squeeze, and that
space has to be empty.

[Choosing a grip, section 7](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body)
makes the general point that the gripper's own body should bound the grasp
search. Here is the same arithmetic run the other way, to get the number that
decides whether separation is needed.

Take a Robotiq 2F-85, whose stroke — the opening between the pads — is 85 mm, and
put 6 mm pads on each finger, the same figures
[section 7 of choosing a grip](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body)
uses. Suppose the object is 40 mm across at the grasp line and you want 5 mm of
clearance on each side so that the fingers do not scrape it on the way in.

- The opening between pads must be 40 + (2 × 5) = 50 mm.
- The outer width the gripper sweeps is that opening plus both pads:
  50 + (2 × 6) = 62 mm.
- The object occupies 40 mm of that 62 mm, so the free space needed on each side
  is (62 − 40) / 2 = **11 mm**.

Eleven millimetres. A neighbour any closer than that on either side of the grasp
line blocks the grasp, no matter how good the grasp looks in a top-down picture.
The same gripper's largest graspable object is 85 − (2 × 6) = 73 mm, which is the
other bound from the same two numbers.

That 11 mm is the number your whole singulation policy is built on, and it is
specific to your gripper and your fingertips. Compute it for yours before
anything else in this document.

### 2.3 The two reasons do not cancel

Compare the two numbers just derived. Perception with the tutorial's settings
reports objects as separate when they are more than 20 mm apart. The gripper needs
11 mm. So with those settings the perception check is *more* conservative than the
hardware requires, by 20 − 11 = 9 mm, and the robot will occasionally push things
apart that it could already have picked.

The temptation is to lower the cluster tolerance to 11 mm so the two agree. That
breaks the other constraint: 11 mm is below the 17.32 mm voxel diagonal, so single
objects start shattering into several clusters. The fix is to change the leaf size
as well. With 5 mm cubes the diagonal is 5 × √3 = 8.66 mm, so a tolerance of
11 mm leaves 11 − 8.66 = 2.34 mm of margin — about the same margin the tutorial
chose — and the perception threshold now matches the gripper's requirement
exactly.

**Set the cluster tolerance from the gripper's channel width, and set the voxel
size from the cluster tolerance.** That is the one piece of parameter advice in
this document that is worth more than everything else in it, because the default
parameters in every tutorial were chosen for a different purpose and nobody
revisits them.

Two costs come with the smaller voxel. The cloud carries roughly eight times as
many points, since halving the cube edge multiplies the count per unit volume by
2³ = 8, so clustering time rises correspondingly. And the smaller cubes are more
sensitive to depth noise, so a noisy sensor will produce spurious small clusters
that `setMinClusterSize` then has to reject.

## 3. The separating moves

The methods are mostly pushing, because pushing is the only thing a robot arm can
do to an object it is not holding. What varies is the shape of the push and what
it is aimed at. This section covers five, each with the jobs it suits and the jobs
it cannot do.

The mechanics under all of them — whether the object slides or tips, which way it
rotates, how the contact point decides that — are in
[pushing and sliding](09_pushing-and-sliding.md). What follows is the task-level
choice.

### 3.1 The straight push

Close the fingers, put the closed gripper down beside the target object, and move
the arm in a straight line so the fingertips drive the object across the surface.
This is the primitive everything else is built from.

It suits five jobs:

- separating one object from a group when you know which object you want
- moving an object out from a corner or away from a bin wall, where there is no
  room for the gripper but there is room for the object
- opening a gap on one specific side of the object, which is what the 11 mm
  figure in section 2.2 asks for
- moving an object into the part of the workspace where the arm has the most
  freedom, which
  [reaching and reachability, section 2](../08_arm-movement/02_reaching-and-reachability.md#2-the-workspace-and-its-holes)
  describes
- acting on an object far too large or heavy for the gripper, where pushing is
  the only interaction available at all

It cannot do five jobs:

- separate objects that are stacked rather than side by side, since a horizontal
  push moves the pile
- act on an object with nothing behind it, because the surface takes the reaction
  force and an object at the edge simply falls
- be predicted accurately in rotation, which is the whole subject of
  [pushing and sliding](09_pushing-and-sliding.md) and the reason section 8
  exists
- work on a light object on a low-friction surface, which skitters unpredictably
  instead of sliding steadily
- avoid disturbing the objects behind the target, which frequently undoes the
  separation you just achieved somewhere else

### 3.2 The sweep

The same motion with a longer contact, made by presenting the side of a finger or
a closed gripper broadside and drawing it across the surface. A sweep touches
several objects at once and moves them together in the sweep direction.

It suits five jobs:

- clearing a landing zone, so that objects picked later have somewhere to be put
  down in a known pose
- moving a whole group away from a wall, after which straight pushes can separate
  them from each other
- flattening a low pile by dragging its top layer sideways
- gathering scattered small parts against a fixture or a wall so they present a
  known face, which is the trick behind many vibratory feeders done by hand
- clearing an object that must not be gripped at all, such as swarf or packaging

It cannot do five jobs:

- separate objects from each other, since it moves them in the same direction
  and generally preserves their relative positions
- be used where the swept objects have nowhere to go
- handle anything fragile, since the contact is uncontrolled across a long face
- be aimed at one object, which is the difference between a sweep and a push
- act on objects taller than the sweeping surface, which topple over it instead
  of moving with it

### 3.3 The spread

Put the *open* gripper down between two touching objects and open it further, so
the two fingers drive the objects apart in opposite directions. Some grippers can
do this and some cannot; it needs a stroke that is not already at its maximum and
enough finger length to reach the surface.

It suits five jobs:

- separating exactly two touching objects with one action, which a straight push
  needs two actions to do
- opening a gap symmetrically, so neither object travels far and both post-action
  poses stay predictable
- working in the middle of a group where there is no room to approach from
  outside
- separating two objects of similar mass, where a one-sided push tends to move
  both
- doing the separation and the subsequent grasp from the same approach pose,
  which saves an arm move

It cannot do five jobs:

- work on a gripper already at full stroke, or one whose fingers are too short to
  reach between the objects
- work where the fingers cannot be inserted between the objects in the first
  place, which is the common case in a dense pile
- act on more than two objects
- apply a controlled force, since most parallel grippers command force only for
  closing
- be done at all with a suction gripper or a magnet, which have no fingers

### 3.4 Toppling and tipping

Push high on a tall object so that it tips over instead of sliding. This changes
which face is presented and usually changes the object's footprint as well. It
belongs in this list because a toppled object is often separated from its
neighbours as a side effect of falling away from them.

It suits five jobs:

- turning a tall narrow object into a low wide one, which is far more stable to
  grasp and far more stable to carry
- presenting a different face, which is the pre-grasp use in section 7
- reducing the height a gripper must clear, which matters in a bin with high
  walls
- knocking an object away from a wall it is leaning against
- breaking up a leaning pile without lifting anything

It cannot do five jobs:

- be applied to an object already lying flat, which has nothing to tip about
- be controlled finely, since the object accelerates under gravity once it passes
  the tipping point
- guarantee which face ends up upward, for exactly the reason
  [holding on, section 6](05_holding-on.md#6-regrasping) gives about setting an
  object down: it settles into whichever stable pose it was nearest, and
  predicting that needs the centre of mass and the friction
- be used on anything fragile, or anything with liquid in it
- be reversed, since standing an object back up needs a grasp you did not have

### 3.5 Pick from the pile and put down separately

Not a push at all. Grasp whatever the pile offers, even a poor grasp, lift it
clear, and put it down in empty space where a proper grasp is available. The
second pick is then easy. This is the same mechanism as regrasping, described in
[holding on, section 6](05_holding-on.md#6-regrasping), applied to a different
problem.

It suits five jobs:

- piles where no push has room to act, such as a full tote
- cells that already have a clear staging area, where the second placement costs
  little
- objects that can be gripped somehow but not gripped *well*, where the first
  grasp needs only to survive a short lift
- getting an object out of a corner that a push cannot reach into
- reducing the requirement on perception, since you no longer need to know which
  object you have until it is out of the pile

It cannot do five jobs:

- work when no grasp at all exists, which is the case that sent you to this
  document
- fit a tight cycle time, since it costs a full extra pick and place
- guarantee the intermediate pose, unless a fixture provides it
- handle anything that must not be set down twice, such as something sterile or
  something wet
- avoid disturbing the pile, since removing an object from a pile collapses it

### 3.6 The non-arm options, which are often better

Three mechanisms separate objects without the arm doing anything, and they are
worth naming because a cell that can use one of them should not be solving this
problem with an arm at all.

A **vibratory feeder** shakes parts along a shaped track until each one is
presented in a single known orientation. A **conveyor with a gap** between belts
running at different speeds spreads touching objects apart because the faster belt
pulls the leading object away. A **tilted or vibrating tote** settles parts into
one layer. All three trade capital cost and part-specific tooling for a problem
that simply does not arise.

The trade is the usual one. Fixed feeding hardware is fast, completely reliable
and works for exactly one part. Arm-based singulation is slow, imperfect and works
for parts that do not exist yet. Choose the hardware when the part mix is fixed
and the volume is high, and the arm when it is not.

## 4. Choosing the separation direction

Once you have decided to push, you must decide which way. This is the part most
implementations get wrong, usually by pushing towards whatever is nearest.

### 4.1 The three candidate directions, ranked

For a target object touching one or more neighbours, three directions are worth
generating, and they can be ranked by a property that has nothing to do with
grasp quality.

Read the table below as a ranking by *how predictable the result is*, best first,
because a push whose outcome you cannot predict is a push you cannot verify.

| Direction | How it is computed | Why it ranks here |
| --- | --- | --- |
| Away from the centroid of the neighbours | the vector from the mean position of the touching clusters to the target's centroid | it separates on every side at once, and it needs only positions you already have |
| Along the largest free-space ray | cast rays outward from the target in the horizontal plane and keep the one with the most empty distance | it is the direction least likely to make a new collision, but it may not increase the gap where you need it |
| Perpendicular to the contact line | the normal of the shared boundary between the target and its nearest neighbour | it opens the specific gap the gripper needs, and it is the most likely to cause rotation |

The first is the default and should be what your code does when it has no reason
to do anything else. The second is what you fall back to when the first points
into a wall. The third is for the case where you know exactly which side of the
grasp line is blocked, which you do know once you have computed the 11 mm figure
from section 2.2 for each side independently.

### 4.2 The constraint the direction has to satisfy

A push direction is only usable if three things are true at once, and all three
are cheap to test.

There must be somewhere for the object to go. The straight-line corridor of the
object's footprint, extended by the push distance in the push direction, must be
free of other clusters and of the bin walls. This is the same swept-volume test
the grasp search uses, run on the object instead of the gripper.

There must be somewhere for the gripper to start. The pusher has to be placed on
the far side of the object from the push direction, and that position has to be
reachable and collision-free. A push away from the wall usually fails here, not on
the corridor: the object has room to move and the gripper has no room to get
behind it.

The push must not pass through the objects you are trying to keep still. A push
that separates the target from one neighbour by driving it into another has
achieved nothing.

### 4.3 The direction choice, as pseudo code

```
choose_push_direction(target, neighbours, obstacles):

    candidates = []

    # 1. away from the neighbours, the default
    away = normalise(target.centroid - mean(n.centroid for n in neighbours))
    candidates.append(away)

    # 2. the emptiest ray, as a fallback
    for angle in 0, 15, 30, ... 345 degrees:
        d = unit vector at angle in the support plane
        candidates.append(d) with score = free_distance(target, d, obstacles)

    # 3. the normal of the nearest contact, when one side is known blocked
    if blocked_side is known:
        candidates.append(outward normal of the contact with that neighbour)

    for d in candidates, best score first:
        if not corridor_is_free(target, d, push_distance, obstacles):  continue
        if not pusher_can_be_placed(target, -d, obstacles):            continue
        if corridor_hits(target, d, push_distance, keep_still_set):    continue
        return d

    return NONE      # and this is a real answer: say so, do not push anyway
```

The last line matters. A separation planner that always returns a direction will
push into a wall, and the failure is silent — the arm stalls against the bin, the
object does not move, perception reports the same scene, and the loop repeats
forever. Returning nothing and escalating is the correct behaviour, and the
escalation is usually to section 3.5, picking from the pile anyway.

## 5. Separate, or pick from the pile anyway

Separating is not free. It costs an arm move, and it costs the risk of making the
scene worse. The decision of whether to separate at all is an arithmetic one, and
the arithmetic is simple enough to do properly.

Let `c_pick` be the time one pick attempt costs, `p` the probability that a pick
attempt on the unseparated pile succeeds, `c_sep` the time one separation action
costs, and `p'` the probability a pick succeeds after separation.

If you never separate and simply retry until you succeed, the expected time is
`c_pick / p`, because the number of attempts needed is geometrically distributed
with mean `1 / p`. If you separate once first, the expected time is
`c_sep + c_pick / p'`.

Put real numbers in. Suppose a pick attempt takes 8 seconds, succeeds half the
time on the pile, succeeds 90 per cent of the time after separation, and a
separation action takes 3 seconds.

- Without separating: 8 / 0.5 = **16.0 seconds**.
- With separating: 3 + 8 / 0.9 = 3 + 8.89 = **11.89 seconds**.

Separating wins by 4.11 seconds per pick, which over a shift is a large number.

Now find the point where it stops winning. Separation is worth doing while
`c_sep + c_pick / p' < c_pick / p`, which rearranges to
`p < c_pick / (c_sep + c_pick / p')`. With the same numbers that is
8 / 11.89 = **0.673**.

So: **if a pick from the untouched pile succeeds more than about 67 per cent of
the time, separating first makes the cell slower.** That threshold is high, and it
surprises people. The instinct is to tidy the scene before acting, and the
arithmetic says to act and let the scene tidy itself.

Three things this calculation leaves out, each of which pushes the threshold down
and therefore favours separating more than the bare numbers suggest.

A failed pick is not free beyond its time. It can drop a part, jam a neighbour
further, or knock something out of the tote. If a failure costs a human
intervention even one time in fifty, and that intervention takes two minutes, it
adds 120 / 50 = 2.4 seconds to every failure.

A pick on a merged blob is worse than a failed pick. The grasp was computed on a
shape that does not exist, so the fingers may close across two objects and lift
both, or close on a gap and lift neither. Lifting two objects is the dangerous one
because [the grasp-detected signal](05_holding-on.md#23-the-grasp-detected-signal-answers-a-weaker-question-than-it-appears-to)
reports success. The wrist weight check from
[the two-finger gripper, section 5](06_two-finger-gripper.md#5-the-feedback-loop-as-pseudo-code)
catches it and nothing else does.

`p` is not one number. It falls as the tote empties and the remaining parts end up
in corners, and it falls as the pile gets flatter and grasps get shallower. A
policy fixed on a measured average `p` will separate too little at the start of a
tote and too much at the end. Measuring `p` over the last twenty attempts rather
than over all history costs nothing and tracks the change.

## 6. Telling whether separation worked

This is the question the rest of the loop depends on, and it has a specific
answer rather than a vague one. Do not use the arm's own sense of whether the push
completed; a push completes perfectly well against an object that did not move.

### 6.1 The answer: re-cluster, and measure the minimum gap

Take a new depth picture. Run exactly the same plane removal and clustering you
ran before. Then check two things.

**Did the cluster count increase?** If the blob was one cluster and is now two,
the separation worked in the sense that perception can now see two objects. If the
count is unchanged, nothing useful happened.

**Is the minimum distance between the two new clusters greater than the gripper's
channel requirement?** This is the 11 mm from section 2.2, computed for your
gripper. Two clusters can be reported separately and still be closer together than
the gripper can fit between — which is exactly the situation section 2.3 warns
about when the cluster tolerance is set below the channel width.

Both checks use only what you already have. There is no extra sensor, no extra
model, and no extra parameter beyond the one you derived from the gripper's own
dimensions.

If you set the cluster tolerance equal to the channel requirement as section 2.3
recommends, the two checks collapse into one: the cluster count increasing is
*exactly* the statement that the gap now exceeds the channel width. That is the
reason to set it that way.

### 6.2 Three ways the check lies

**The clusters split for the wrong reason.** A cluster can divide into two because
the objects separated, or because the push rotated one object so that part of it
went out of the camera's view and the visible remainder broke in half. Guard
against it by checking that the total point count across the new clusters is
within a tolerance of the old blob's count. A large drop means you are looking at
occlusion, not separation.

**The clusters merge with something else.** Pushing an object away from one
neighbour can push it into another. The cluster count then stays at two, but they
are a different two. Guard against it by tracking the centroid: the new cluster
nearest the predicted post-push position is the target, and if nothing is near
that position the push did something you did not predict.

**The gap is in the wrong place.** The minimum distance between two clusters can
exceed 11 mm while the gap along the *grasp line you actually want* is smaller,
because the objects separated at one end and stayed together at the other. The
honest check measures clearance along the intended grasp axis rather than the
global minimum, which costs one extra line and catches a genuinely common case.

### 6.3 The check, as pseudo code

```
verify_separation(cloud_before, cloud_after, blob_id, wanted_grasp):

    before = cluster(remove_plane(cloud_before), tolerance = CHANNEL_MM)
    after  = cluster(remove_plane(cloud_after),  tolerance = CHANNEL_MM)

    if len(after) <= len(before):
        return NOT_SEPARATED          # nothing moved, or it moved into something

    if total_points(after) < 0.85 * total_points(before):
        return OCCLUDED               # points went missing, not apart

    target = nearest cluster in after to predicted_position
    if target is None or distance > PREDICTION_TOLERANCE_MM:
        return UNEXPECTED             # the push did something else; re-plan

    # the check that actually matters
    for other in after, other != target:
        gap = clearance along wanted_grasp.axis between target and other
        if gap < CHANNEL_MM:
            return STILL_BLOCKED

    return SEPARATED
```

`NOT_SEPARATED` and `STILL_BLOCKED` should lead to another push increment.
`OCCLUDED` should lead to another look from a different viewpoint, which is what
[the wrist camera](../06_object-perception/08_the-wrist-camera.md) is for.
`UNEXPECTED` should lead back to the start of the planner, because your model of
the scene is now wrong and everything computed from it is worthless.

## 7. Pre-grasp manipulation as a category

Singulation is one case of a wider pattern, and the wider pattern is more useful
than the list of tricks that make it up. The pattern is this: **the wanted grasp
is unavailable for one identifiable reason, and each reason has a small set of
actions that remove it.**

Treating it as a category rather than a list matters because the list is never
complete. A new blocking condition turns up in every cell, and what transfers is
the procedure for finding the action, not the actions themselves.

### 7.1 The four blocking conditions and their standard moves

The table below lists the conditions in the order you should test for them, which
is the order of how cheap the test is. Read each row as: this is the symptom, this
is how you confirm it, and these are the actions that remove it.

| Condition | How you confirm it | The standard moves |
| --- | --- | --- |
| Free space is intruded on: a neighbour, a bin wall or a fixture occupies the gripper's swept volume | the swept-volume test from [choosing a grip, section 7](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body) fails, and the intruding geometry is not the target | slide the target clear of the obstruction; push the neighbour away; sweep the group away from the wall |
| The needed face is inaccessible: the object lies on the surface you wanted to grip | grasp candidates exist in the object's frame but all of them point into the support plane | topple the object onto a different face; roll it; flip it with a two-stage pick and place |
| The arm cannot reach the grasp although the grasp is valid | the grasp passes every geometric test and inverse kinematics returns no solution, or only colliding ones | rotate the object in place so the grasp axis turns; slide it to a part of the workspace with more freedom |
| No grasp exists on the object at its current pose | the object's presented dimension exceeds the gripper's maximum, or it is too flat to get under | topple a wide box onto its narrow face; slide it to a table edge so a side grasp becomes possible; change to a suction gripper, which needs only one face |

The fourth row's last entry is not a manipulation and it is in the table on
purpose. A surprising number of pre-grasp problems are really tooling problems,
and the honest answer to "this object has no two-finger grasp" is sometimes that
it needs a different gripper rather than a cleverer push.
[Grippers and hardware](02_grippers-and-hardware.md) covers the alternatives.

### 7.2 The decision procedure

Here is the procedure, and it is deliberately short, because the whole value of
treating this as a category is that the same five steps answer every instance.

1. **Ask the grasp planner for candidates and record why each one was rejected.**
   Not whether — *why*. A planner that returns an empty list tells you nothing; a
   planner that returns "eleven candidates, nine rejected for collision with
   cluster 4, two rejected for unreachable" tells you which row of the table above
   you are in. This is a change to your planner, it costs almost nothing, and it
   is the step people skip.

2. **Map the dominant rejection reason to its row, and enumerate that row's
   moves.** Two or three candidate actions, not a search over all possible
   motions. This is the step that makes the whole thing cheap: the space of
   pre-grasp actions is enormous and the space you actually need to consider is
   tiny, because the rejection reason has already narrowed it.

3. **For each candidate action, predict the resulting scene and re-run the grasp
   planner on it.** The feasibility test is *your existing grasp planner applied
   to a predicted scene*. You do not need a model that scores pre-grasp actions.
   You need a cheap forward prediction and one more call to code you already have.
   Section 8 is about how good that prediction is.

4. **Rank the surviving actions by how little they change.** A rotation in place
   moves the object less than a slide, a slide less than a push against a
   neighbour, a push less than a topple. Less change means less prediction error,
   which means the re-run planner's answer is more likely to still be true when
   the action finishes. Prefer the smallest action that works, not the one whose
   predicted grasp scores highest.

5. **Execute incrementally and stop as soon as a grasp becomes available.** The
   goal is not to complete the planned action. The goal is to reach a state where
   a grasp exists, which frequently happens a third of the way through.

The question that procedure answers, at every step, is the same one: *what single
action turns an impossible grasp into a possible one.* Not what sequence — a
single action. If no single action works, the honest answer is usually section
3.5, pick something out of the way and try again, rather than a longer plan whose
prediction error compounds.

### 7.3 The procedure, as pseudo code

```
plan_pre_grasp(target, scene, gripper):

    grasps, rejections = grasp_planner(target, scene, explain = True)
    if grasps:
        return PICK(best(grasps))          # nothing to do here

    reason = most_common(rejections)

    if   reason == COLLISION_WITH_NEIGHBOUR: moves = [slide_target_clear,
                                                      push_neighbour_away]
    elif reason == COLLISION_WITH_WALL:      moves = [slide_target_clear,
                                                      sweep_group_inward]
    elif reason == FACE_ON_SUPPORT:          moves = [topple, roll]
    elif reason == UNREACHABLE:              moves = [rotate_in_place,
                                                      slide_to_open_workspace]
    elif reason == NO_GRASP_ON_SHAPE:        moves = [topple_onto_narrow_face,
                                                      slide_to_edge]
    else:                                    return ESCALATE

    viable = []
    for m in moves:
        predicted = predict_scene(scene, m, target)       # section 8
        if grasp_planner(target, predicted, explain = False):
            viable.append((m, change_magnitude(m)))

    if not viable:
        return ESCALATE                # pick something else out of the way

    return EXECUTE_INCREMENTALLY(min(viable, key = change_magnitude))
```

`ESCALATE` should have a real destination. In a supervised cell it asks a human.
In an unsupervised one it removes the nearest graspable object from the scene and
tries again, which changes the configuration even when you cannot say how.

### 7.4 What pre-grasp manipulation suits, and what it does not

Five jobs the whole category suits:

- bin picking, where a fraction of the presentations are always unpickable and the
  alternative is stopping
- cells with a fixed part family, where the blocking conditions repeat and the
  moves that fix them can be tuned once
- any task where a wall, a corner or a fixture is part of the environment, since
  those produce the first row of the table constantly
- objects with one good grasp face and several bad ones, where a single topple
  converts the hard case into the easy case
- reducing the requirement on the grasp planner, which can then be a simple
  geometric rule that works on well-presented objects only

Five jobs it cannot do:

- work in a full tote with no free space, since every move needs somewhere for
  something to go
- act on anything fragile, since all of it is uncontrolled contact
- be planned more than one or two actions deep, because the prediction error
  compounds and section 8 explains why
- handle objects that must not be slid, scratched or laid on a different face —
  optical parts, finished surfaces, food
- replace a fixture or a feeder where cycle time is tight, since every pre-grasp
  action is pure overhead on the pick

## 8. The feasibility test: will the grasp exist afterwards

Step 3 of the procedure asks you to predict the scene after an action and re-run
the grasp planner on it. That prediction is the weakest link in the whole
document, and being honest about how weak it is changes the design.

### 8.1 What predicting a post-push pose requires

To say where a pushed object ends up you need its shape, the friction between it
and the surface, the friction between it and the pusher, and the distribution of
pressure under it. The first is measurable. The second and third are guessable
within a factor. The fourth is essentially unknowable: the pressure distribution
under a rigid object on a rigid surface is statically indeterminate, meaning the
equations of statics have more unknowns than they have equations, and the actual
distribution depends on microscopic surface detail.

[Pushing and sliding](09_pushing-and-sliding.md) sets out what can be predicted
without that fourth quantity. The short version, so this document stands alone:
the *direction* of an object's rotation under a push is determined by geometry
alone and can be predicted reliably; the *magnitude* of that rotation depends on
the pressure distribution and cannot.

### 8.2 How unreliable it is, from people who measured it

Two pieces of work are worth knowing about, because they are the measurements
rather than the theory.

The MIT push dataset, published as
[More than a Million Ways to Be Pushed](https://arxiv.org/abs/1604.04038), records
an industrial robot pushing objects along precisely controlled trajectories while
logging poses and contact forces, varying the surface material, the object shape,
the contact position, the push direction, the speed and the acceleration. Its
stated purpose is to answer how close the usual models are and how reasonable
their assumptions are, and its own conclusion is that it characterises the
variability of friction and evaluates the common simplifications. That a dataset
this size was needed to answer the question is itself the finding.

[A probabilistic data-driven model for planar pushing](https://arxiv.org/abs/1704.03033)
takes the next step and models the *variance* as well as the mean, using Gaussian
processes with input-dependent noise. Its abstract states that the learned models
outperform analytical models after fewer than 100 samples and saturate in
performance below 1000. Two things follow. A learned push model is cheap to fit,
which is good news. And it saturates, which means the residual variability is a
property of pushing rather than a shortage of data.

The practical reading: **treat a predicted post-push pose as a mean with a spread
around it, and never as a fact.** If your planner takes the predicted pose and
computes a grasp to a tenth of a millimetre, it is computing a precise answer to
the wrong question.

### 8.3 The practical answer: push a little, look again

Since one long push cannot be predicted, do not make one. Make a short push, take
a new picture, and decide again. Each increment is short enough that the
prediction error stays small, and the loop corrects whatever error accumulates.

This is strictly better in accuracy and strictly worse in time, so the cost is
worth computing. Take a separation that needs 25 mm of travel, a push speed of
100 mm/s, an arm move of about 1.0 second to get into position and the same to
retract, and a perception cycle of about 0.5 seconds.

One push of 25 mm, executed and then verified once:

- approach 1.0 s, push 25 / 100 = 0.25 s, retract 1.0 s, look 0.5 s
- total **2.75 s**

Five increments of 5 mm, retracting the arm before each look because the arm is
in the camera's way:

- 5 × (1.0 + 0.05 + 1.0 + 0.5) = 5 × 2.55 = **12.75 s**, which is 12.75 / 2.75 =
  **4.64 times** the one-shot cost

Five increments of 5 mm, with a fixed overhead camera that can see the scene past
the arm, so the arm stays in contact between increments:

- 1.0 + 5 × (0.05 + 0.5) + 1.0 = 1.0 + 2.75 + 1.0 = **4.75 s**, which is
  4.75 / 2.75 = **1.73 times** the one-shot cost

Those arm and perception times are assumptions and you should measure your own;
[the wrist camera, section 4](../06_object-perception/08_the-wrist-camera.md#4-what-a-view-actually-costs)
works through why the arm move is the part that is hard to look up and easy to
measure. What survives any values you substitute is the shape of the result:
**incremental pushing costs under twice as much when you have a camera that does
not need the arm to move out of the way, and nearly five times as much when you
do.** That is a strong argument for the fixed overhead camera in a cell that does
much singulation, and
[the wrist camera, section 6](../06_object-perception/08_the-wrist-camera.md#6-when-you-also-need-a-fixed-camera)
is where that choice is set out properly.

Two refinements make the loop cheaper without giving up the correction.

Use a large first increment and small ones after. The first push is the one where
you know least about the object's response, but it is also the one where the
object is furthest from where you want it. Pushing 15 mm and then 5 mm twice
covers the same 25 mm in three increments rather than five.

Stop as soon as the grasp exists, not when the push finishes. Run the section 6
check after every increment and abandon the moment it returns `SEPARATED`. In
practice a good fraction of separations succeed on the first increment, and the
planned distance was a worst case that most instances do not need.

### 8.4 The loop, as pseudo code

```
push_until_graspable(target, direction, total_mm, gripper):

    place the closed gripper behind target along -direction
    moved = 0
    increments = [15, 5, 5]          # large first, then correct

    for step in increments:
        if moved >= total_mm: break

        predicted = predict_pose(target, direction, step)   # a mean, not a fact
        move the arm step mm along direction, in contact

        cloud = look()                                      # fixed camera: no retract
        result = verify_separation(cloud_before, cloud, target, wanted_grasp)

        if result == SEPARATED:
            return SUCCESS                                  # stop early, always

        if result == UNEXPECTED:
            return REPLAN                                   # the scene model is wrong

        if actual_pose(cloud, target) has not changed by at least 0.5 * step:
            return BLOCKED    # pushing against something; a wall, or a jam

        moved += step
        cloud_before = cloud

    return NOT_SEPARATED
```

The `BLOCKED` test is the one that saves you. An arm pushing against a bin wall
moves the commanded distance, reports success, and moves nothing. Comparing the
object's *measured* displacement against the commanded one catches it in one
increment, and this is the singulation version of the guarded move described in
[controlling the move, section 5](../08_arm-movement/04_controlling-the-move.md#5-guarded-moves-and-what-the-sensor-can-actually-observe).

## 9. Learned approaches, and their licences

There is a research literature on learning singulation policies, and a
straightforward summary of it is that the ideas are good, the code is old, and the
licences are worse than in almost any other part of this repository. Read this
section before you get attached to a repository.

### 9.1 What the learned approaches actually do

Three ideas recur.

**Learning pushes that help future grasps.**
[Learning Synergies between Pushing and Grasping with Self-supervised Deep
Reinforcement Learning](https://arxiv.org/abs/1803.09956) trains two networks
together, one scoring pushes and one scoring grasps at every pixel, with the
reward coming only from successful grasps. The push network therefore learns
pushes that make later grasps work, without anyone specifying what a good push is.
The idea is the one worth taking from this literature: the value of a pre-grasp
action is defined entirely by the grasp it enables, which is the same claim
section 7.2 step 3 makes about using your existing grasp planner as the test.

**Proposing pushes directly from a picture.**
[Learning to Singulate Objects using a Push Proposal Network](https://arxiv.org/abs/1707.08101)
trains a network on data collected by a robot interacting autonomously with
cluttered scenes, and it proposes push actions from over-segmented colour and
depth images. It reports singulating up to eight unknown objects.

**Segmenting objects that touch, so that no push is needed to tell them apart.**
This attacks the perception half of section 2 rather than the mechanical half.
[Segmenting Unknown 3D Objects from Real Depth Images using Mask R-CNN Trained on
Synthetic Data](https://arxiv.org/abs/1809.05825) trains on synthetic depth
pictures and segments objects the model has never seen, including objects that are
touching, which the clustering recipe cannot do.

A fourth, [Mechanical Search](https://arxiv.org/abs/1903.01588), is about
retrieving a *specific* target buried under clutter, which is the sequential
version of the same problem.

### 9.2 The licences, which are the reason to read this section

Every licence below was read from the repository's own licence file through the
GitHub licence interface, not from a badge or a README claim. Read the table as
what you may actually ship, with the licence first because it decides whether the
rest of the row matters.

| Repository | Licence, read from the file | State | What it is |
| --- | --- | --- | --- |
| [visual-pushing-grasping](https://github.com/andyzeng/visual-pushing-grasping) | BSD-2-Clause | last pushed May 2021 | the push-and-grasp synergy method; the only permissive one here |
| [sd-maskrcnn](https://github.com/BerkeleyAutomation/sd-maskrcnn) | MIT | last pushed January 2022 | synthetic-depth instance segmentation, which separates touching objects in perception |
| [UnseenObjectClustering](https://github.com/NVlabs/UnseenObjectClustering) | **NVIDIA Source Code License, non-commercial** | last pushed December 2023 | RGB-D feature embeddings for unseen object instance segmentation |
| [uoais](https://github.com/gist-ailab/uoais) | **bespoke non-commercial licence** | last pushed July 2025 | amodal instance segmentation, which infers the hidden parts of occluded objects |
| [Efficient_goal-oriented_push-grasping_synergy](https://github.com/xukechun/Efficient_goal-oriented_push-grasping_synergy) | **no licence file at all** | last pushed January 2022 | goal-conditioned push-and-grasp in clutter |
| [dex-net](https://github.com/BerkeleyAutomation/dex-net) | **UC Berkeley research and not-for-profit only** | the classic grasp-quality work several of these build on | grasp quality from synthetic data |

Four things in that table need saying in sentences rather than in cells.

**The NVIDIA Source Code License is explicitly non-commercial, and it defines the
term narrowly.** Its section 3.3 reads: "The Work and any derivative works thereof
only may be used or intended for use non-commercially. ... As used herein,
'non-commercially' means for research or evaluation purposes only." A pilot inside
a company that intends to sell something is not research or evaluation. The same
section grants Nvidia and its affiliates commercial use, which is worth noticing
for what it tells you about the intent.

**The `uoais` licence is a bespoke academic one and it is unambiguous.** It grants
the right to copy and modify "for the sole purpose of performing non-commercial
scientific research, non-commercial education, or non-commercial artistic
projects", and then says directly that "Any other use, in particular any use for
commercial purposes, is prohibited. This includes, without limitation,
incorporation in a commercial product, use in a commercial service, or production
of other artefacts for commercial purposes."

**A repository with no licence file grants you nothing.** This is the trap
[licences and platforms, section 1.1](07_licences-and-platforms.md#11-no-licence-at-all)
covers, and the goal-oriented push-grasping repository is a clean example of it:
public code, an academic paper, 85 stars, and no permission to use it. Copyright
is the default, and the default is that you may not copy.

**Dex-Net's licence is the one that catches people out most often**, because
Dex-Net is famous and people assume fame implies permissiveness. Its licence file
grants permission "for educational, research, and not-for-profit purposes" and
directs commercial users to the UC Berkeley Office of Technology Licensing. That
is a non-commercial licence in everything but name.

The practical conclusion is short. **Of the learned singulation work, exactly two
repositories are shippable: `visual-pushing-grasping` under BSD-2-Clause, and
`sd-maskrcnn` under MIT.** Both are four to five years old. Everything newer in
this space is either non-commercial or unlicensed.

### 9.3 Five jobs a learned singulation policy suits

- research and evaluation, which is what most of the licences permit anyway
- scenes where the objects are unknown and no geometric rule describes them
- generating a push proposal when your geometric direction chooser from section
  4.1 returns nothing
- systems that already collect their own interaction data, where the policy can be
  trained on the actual cell rather than transferred
- the perception half of the problem, where segmenting touching objects is a
  genuinely solved capability that clustering cannot match

### 9.4 Five jobs it cannot do

- ship in a commercial product, for four of the six repositories above
- run without an NVIDIA graphics card, in every case where a policy network is
  involved
- explain why it chose a push, which matters when you have to diagnose a cell that
  has stopped
- be checked before it acts, since a policy outputs an action rather than a
  prediction you can test against a grasp planner
- replace the geometric feasibility test from section 7, which is cheap, auditable
  and needs no training data

## 10. What runs on an Apple Silicon Mac

Everything in this document that you would actually write yourself runs on an
Apple Silicon Mac with no graphics card. Everything learned does not. The split is
unusually clean.

Read the table as: what you need it for, whether it installs and runs on this
machine, and what the obstacle is when it does not.

| Software | Licence, read from the file | Runs on Apple Silicon | Note |
| --- | --- | --- | --- |
| [PCL](https://github.com/PointCloudLibrary/pcl) | BSD 3-clause | yes | the clustering in section 2 and the check in section 6; installs through RoboStack |
| [Open3D](https://github.com/isl-org/Open3D) | MIT | yes | publishes `macosx_11_0_arm64` wheels; version 0.20.0 at the time of writing |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | Apache-2.0 | yes | publishes `macosx_11_0_arm64` wheels; version 3.14.0 at the time of writing. This is the one to use for the push prediction in section 8 |
| [Bullet / PyBullet](https://github.com/bulletphysics/bullet3) | zlib | compiles from source | PyPI carries only `manylinux_x86_64` wheels for pybullet 3.2.7 plus a source distribution, so `pip install pybullet` builds it locally |
| [Drake](https://github.com/RobotLocomotion/drake) | BSD 3-clause | yes | release 1.57.0 publishes `macosx_15_0_arm64` wheels alongside the Linux ones; a full multibody simulator with contact modelling, and heavier than MuJoCo for this purpose |
| [visual-pushing-grasping](https://github.com/andyzeng/visual-pushing-grasping) | BSD-2-Clause | no | needs CoppeliaSim and, in its own words, "8GB of GPU memory" for the pre-trained models, tested on CUDA 8.0 with a Titan X |
| [SAM 2](https://github.com/facebookresearch/sam2) | Apache-2.0 | yes, slowly | runs through PyTorch's Metal backend; see [models that find, section 1.3](../06_object-perception/04_models-that-find.md#13-promptable-segmenters-the-segment-anything-family) |
| [UnseenObjectClustering](https://github.com/NVlabs/UnseenObjectClustering) | non-commercial | no | CUDA-targeted, and the licence rules it out for most purposes anyway |

The reading for someone on this machine is that the whole of sections 2 through 8
is available: the clustering, the channel arithmetic, the direction choice, the
verification and the incremental loop are all plain geometry over point clouds,
and MuJoCo gives you a physics engine for the prediction step that installs with
one command. What you cannot do locally is train or run the learned policies of
section 9, and given their licences that is a smaller loss than it sounds.

## 11. Where this sits in the rest of the area

Four connections are worth making explicitly, because this document sits between
several others and it is easy to solve the wrong problem.

The mechanics of every action in section 3 are in
[pushing and sliding](09_pushing-and-sliding.md). If you have chosen to push and
now need to know where the object goes, that is the document.

The reason touching objects merge is in
[programmed methods, section 1.6](../06_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster),
and the models that avoid the merging are in
[models that find](../06_object-perception/04_models-that-find.md). If your
singulation problem is really a segmentation problem, fixing perception is
cheaper than pushing.

The gripper geometry that produces the 11 mm channel figure is in
[choosing a grip, section 7](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body),
and the consequences of getting the fingertip dimensions wrong are in the same
place. Recompute the number for your own fingertips; the catalogue stroke is not
it.

The alternative to pre-grasp manipulation is often regrasping, in
[holding on, section 6](05_holding-on.md#6-regrasping), and occasionally in-hand
manipulation, in
[holding on, section 7](05_holding-on.md#7-in-hand-manipulation). The difference
is whether you are holding the object. If you are, those are the tools. If you are
not, this document is.

One last thing, which is the sentence to keep if you keep nothing else. **A
pre-grasp action is worth doing only if you can say, before you do it, which grasp
it is going to make available.** An action taken because the scene looks untidy is
not a plan, and it is the most common way a singulation loop ends up running
forever without picking anything up.
