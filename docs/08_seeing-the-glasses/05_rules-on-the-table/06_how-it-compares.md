# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

Marked by [the examiner](../03_the-examiner/01_the-examiner.md) over five blocks
of 20 held-out arrangements, it finds every glass the cell's own layout spaces —
100.0 per 100, in all five blocks — and 73.0 per 100 when the glasses are
crowded closer than that layout allows, with the five blocks spread between 70.3
and 75.5. [The results](../11_the-results.md) sets those two rows beside the
other five solutions. What follows is why they came out that way.

**It needs nothing fitted, so it can be read.** The rule is one sentence about
distance on the table, and its one setting could be computed from two quantities
the project already holds.

**It is exact and repeatable.** The same picture gives the same groups every
time, because nothing in the method samples randomly or depends on an order.

**When it fails, printing one number usually tells you why.** Every step
produces one quantity worth printing: how many pixels passed the
standing-above-the-table test, how many squares were marked, how many groups
came out, how many dots each group held, and each group's fitted width. A table
height set slightly too low turns the whole table top into one enormous group,
and the standing-pixel count says so immediately. A grouping distance set too
small shows up as too many groups, each with too few dots. One set too large
shows up as too few groups with one impossible width.

**It answers in real distances from the arm's base**, because it worked in the
room the whole time rather than converting at the end.

**It can say where it has not looked**, from arithmetic it is already doing,
once that branch is built. Almost no perception method can tell "nothing there"
from "could not have been seen".

The weaknesses are one limit on the idea itself and one limit on the sensor.

**The limit on the idea is that somebody has to be able to state the rule.**
Two glasses that
touch leave no strip of bare table at any grouping distance, which is why
[the job of pushing crowded glasses
apart](../../09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md)
exists; two glasses one behind the other at the same distance from the camera
stay one group, because distance cannot separate things that are not apart in
the direction being measured. And allowing
all four kinds on the table at once widens the acceptable range of widths and
weakens the width check by exactly as much, since a group that would be
impossible for the narrowest kind is ordinary for the widest, which is the
difficulty in the harder job where several kinds of glass stand on the table at
once.

**The limit on the sensor is that the rule needs depth readings, and real
transparent glass does not give them.** Every dot in this method was born from a depth
reading, so a pixel with no reading contributes nothing. **The cell gets away with this
only because the simulator renders the glasses as opaque solids**, which is what
the problem statement assumes. So this method would not transfer to a real table
of real glasses as it stands, and that is a limit of the method rather than of
the cell.

## 2. The general ideas behind this

None of this was invented for glassware. It is the standard recipe for a robot
arm working over a table, and has been for about twenty years: treat the depth
picture as a cloud of points, delete the table, and group whatever is left into
clumps, where each clump is one object. It became the default because of what
it does *not* need — no training data, no model file and no idea what the
objects are — so it works on an object the robot has never seen, and it gives
positions in real distances straight away, which is what an arm needs anyway.

### The pinhole camera model — turning a pixel and a depth into a point

A pixel, plus a depth reading, plus the camera's pose, is a point in the room:
the pixel gives a direction, the depth says how far along it to travel, and the
pose says where the ray starts. Reversing a projection this way is called
back-projection, and it is the bridge between everything measured in pixels and
everything an arm does in real distances.

It is rarely right for surfaces a depth sensor reads badly, such as glass,
polished metal, black plastic, or anything shiny or see-through, because there
the depth is missing or wrong and back-projection then produces confident
nonsense.

For more, see the [pinhole camera
model](https://en.wikipedia.org/wiki/Pinhole_camera_model), and Hartley and
Zisserman's [Multiple View Geometry](https://www.robots.ox.ac.uk/~vgg/hzbook/).

### Plane segmentation with RANSAC — finding and deleting the table

**RANSAC**, which stands for random sample consensus, fits a model to data full
of stray readings by guessing repeatedly from small samples (Fischler and
Bolles, *CACM*, 1981). For a table that means picking three points at random,
making the plane through them, counting how many other points lie on that plane,
and keeping the best plane after a few hundred tries. Deleting the biggest plane
is how a table-top scene becomes just the objects.

It is rarely right for scenes with no dominant shape, or where the thing you
want *is* the minority and several models fit equally well.

**This solution skips it**, because the table is fixed to the arm's frame and
its height is known, so the plane is a constant and finding it is a comparison
rather than a search. For more, see
[RANSAC](https://en.wikipedia.org/wiki/Random_sample_consensus).

### Density-based clustering — grouping points by how close they are

Start from a point, take everything within a chosen distance, take everything
within that distance of those, and repeat until nothing new joins. There is one
setting and no assumption about what the objects are. In the robotics
literature this is **Euclidean cluster extraction**; its better-known cousin in
the statistics literature is **DBSCAN**, which adds a minimum-neighbours rule
so that scattered noise cannot form clusters of its own (Ester and colleagues,
KDD 1996). This solution keeps noise out more bluntly, by throwing away any
whole group holding fewer than 100 dots.

It is rarely right for objects that genuinely touch, because distance can only
separate things that have distance between them.

For more, see [DBSCAN](https://en.wikipedia.org/wiki/DBSCAN) and [cluster
analysis](https://en.wikipedia.org/wiki/Cluster_analysis) for the wider family.

### Least-squares shape fitting — turning a cloud of dots into a number

Fit a shape to a set of points by minimising an error that can be written as a
linear equation, which then has a direct solution and needs no iteration. The
fit also offers a **residual**, meaning how far the points sit from the fitted
shape on average, which is a free measure of how well the shape really explains
the data. Nothing here uses it: none of the four outcomes asks the question it
answers, so the code computes the width and stops.

It is rarely right for shapes the model does not describe, because then it
returns a confident number together with a large residual that nobody checks.

For more, Kåsa's algebraic circle fit with the Pratt and Taubin refinements are
the three standard versions, and the geometry is in [circular
segment](https://en.wikipedia.org/wiki/Circular_segment).

### Visibility reasoning — knowing where you could not have looked

A sensor's view divides space into three parts rather than two: the part it can
see and found something in, the part it can see and found nothing in, and **the
part it could not have seen at all**. Treating the third as the second is the
mistake, and an easy one, because both look like absence in the data. Mobile
robots keep a map marking every cell free, occupied or **unknown**, and this
cell is the lucky case where the hidden region can be computed exactly, because
the objects are upright round solids on a known plane and the camera looks
straight down.

For more, the general form is [occupancy grid
mapping](https://en.wikipedia.org/wiki/Occupancy_grid_mapping), where the
three-way marking is the whole point.

## 3. Where it sits among the other five

It is the only one of the six that holds **no fitted numbers at all**. Solution
3 fits nothing in this cell, which makes it the closest of the five to this one
in cost — but it still carries a weights file, and the rule inside that file
was fitted on somebody else's photographs for somebody else's purpose, so
nobody using it can say what the rule is. **This solution's rule is one
sentence, and that is the difference.**

That is what makes it the baseline. The examiner holds the input, the output
and the marking fixed, so a model's score can be compared with this one's
directly, and the comparison has a plain reading: **if a model cannot beat a
written rule, it has earned nothing.**

This solution is the one that shows what the problem's *promises* are worth.
Its rule exists only because the glasses are guaranteed to stand apart, the
table's height is known, one kind is on the table at a time, and the glasses
return depth readings. **A problem that a written rule can answer is a problem
whose promises were generous**, and the value of the other five is what they do
when the promises stop.

← [What it needs](05_what-it-needs.md) · [A network trained here from scratch — what it is](../06_a-network-trained-from-scratch/01_what-it-is.md) →
