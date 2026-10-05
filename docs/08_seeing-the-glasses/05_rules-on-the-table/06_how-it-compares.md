# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The strengths all come from how little this method assumes.

**It needs nothing fitted, so it can be read.** The rule is one sentence about
distance on the table, and its one setting is computed from two quantities the
project already holds. Anybody can read the rule, disagree with it, and say
exactly which quantity they disagree about. None of the other five offers that,
because a fitted model's rule is spread across its weights and cannot be stated
in a sentence.

**It is exact and repeatable.** The same picture gives the same groups every
time, because nothing in the method samples randomly or depends on an order.
That is worth more than it sounds when a result has to be reproduced months
later.

**When it fails, printing one number usually tells you why.** Every step
produces one quantity worth printing: how many pixels passed the
standing-above-the-table test, how many bins were marked, how many groups came
out, how many dots each group held, and each group's fitted width. These fail
in a characteristic order. A table height set slightly too low turns the whole
table top into one enormous group, and the standing-pixel count says so
immediately. A grouping distance set too small shows up as too many groups,
each with too few dots. One set too large shows up as too few groups with one
impossible width. **A fitted model's failure has no equivalent, because there
is no single number inside it that was wrong first.** That difference is the
strongest practical argument for keeping this solution in the set, whatever its
score.

**It answers in real distances from the arm's base**, because it worked in the
room the whole time rather than converting at the end. Three gifts from the cell
make that easy: the table's height is known, the glasses stand upright so they
flatten to neat discs, and only one kind of glass is on the table at a time.

**It can say where it has not looked.** Almost no perception method can, because
almost none of them has a way to tell "nothing there" from "could not have been
seen". This one can, from arithmetic it is already doing, once that branch is
built.

The weaknesses divide into one limit on the idea itself, one limit on the
sensor, and several assumptions.

**The limit on the idea is that somebody has to be able to state the rule.**
This method works here because the problem hands it a rule that can be written
down: glasses stand further apart than a known distance, so distance separates
them. The moment that promise goes, the rule goes with it. Two glasses that
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
once. In every one of those cases the fix is not a better rule but a method
that does not need one, and that is the argument for the other five.

**The limit on the sensor is that the rule needs depth readings, and real
transparent glass does not give them.** This is the most important sentence in
the document to read honestly. Every dot in this method was born from a depth
reading, so a pixel with no reading contributes nothing. A depth camera measures
distance by what bounces back off a surface, and a beam aimed at real glassware
mostly passes straight through it, so the readings come back missing, or worse,
belonging to whatever stood behind the glass. **The cell gets away with this
only because the simulator renders the glasses as opaque solids**, which is what
the problem statement assumes. So this method would not transfer to a real table
of real glasses as it stands, and that is a limit of the method rather than of
the cell. Methods built on the grey picture rather than on the depth reading do
not share it, which is a real point in their favour and not a courtesy.

The assumptions are worth listing because each of them is true here and is still
an assumption. The method assumes a round footprint, and a jug would come back
as a width the kind allows with nothing to object to it, because the width is
the only number the fit keeps. It assumes things stand apart, which the grouping
distance is derived from rather than tuned to, but derived from an assumption is
still from an assumption. One stray dot in the wrong place chains two groups
into one, and a table height set slightly too low turns the whole table top
into one group; the guards against both are a minimum number of dots per group,
which the code applies, and the minimum-neighbours rule described in the next
section, which discards a dot with nothing around it and is not built. Finally,
points higher than the tallest glass the cell handles are dropped, and although
nothing legal is cut, the design prescribes that the run report how many points
were dropped at each end, because a sudden change there means something is
wrong that nothing else would catch.

## 2. The general ideas behind this

None of this was invented for glassware. It is the standard recipe for a robot
arm working over a table, and has been for about twenty years: treat the depth
picture as a cloud of points, delete the table, and group whatever is left into
clumps, where each clump is one object. It became the default because of what it
does *not* need — no training data, no model file and no idea what the objects
are — so it works on an object the robot has never seen, and it gives positions
in real distances straight away, which is what an arm needs anyway.

Five published ideas sit underneath it. Each is given here with an honest note
on where it is normally right and where it is not, because four of the five
appear in almost every robot that looks at objects on a surface.

### The pinhole camera model — turning a pixel and a depth into a point

A pixel, plus a depth reading, plus the camera's pose, is a point in the room:
the pixel gives a direction, the depth says how far along it to travel, and the
pose says where the ray starts. Reversing a projection this way is called
back-projection, and it is the bridge between everything measured in pixels and
everything an arm does in real distances.

It is used in anything with a depth camera — building point clouds, turning a
detection into a pose the gripper can go to, lining separate scans up with each
other. It is rarely right for surfaces a depth sensor reads badly, such as
glass, polished metal, black plastic, or anything shiny or see-through, because
there the depth is missing or wrong and back-projection then produces confident
nonsense. That is exactly the limit described above.

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

It is used wherever most of the data does not belong to the model you want:
finding the ground, fitting lines and circles, joining pictures together, lining
point clouds up. It is rarely right for scenes with no dominant shape, or where
the thing you want *is* the minority and several models fit equally well. It
also does not give the same answer twice, which matters when a result has to be
repeatable.

**This solution skips it**, because the table is fixed to the arm's frame and
its height is known, so the plane is a constant and finding it is a comparison
rather than a search. For more, see
[RANSAC](https://en.wikipedia.org/wiki/Random_sample_consensus).

### Density-based clustering — grouping points by how close they are

Start from a point, take everything within a chosen distance, take everything
within that distance of those, and repeat until nothing new joins. There is one
setting and no assumption about what the objects are. In the robotics literature
this is **Euclidean cluster extraction**; its better-known cousin in the
statistics literature is **DBSCAN**, which adds a minimum-neighbours rule so
that scattered noise cannot form clusters of its own (Ester and colleagues, KDD
1996). That extra rule is what the guard described above borrows.

It is used for table-top work and bin picking, where objects are separated in
space and nobody wants to say in advance what they look like, and it is the
first thing to try on any depth picture of a scene. It is rarely right for
objects that genuinely touch, because distance can only separate things that
have distance between them. It is also poor when the right grouping distance
differs across the scene, since one number has to serve everywhere.

For more, see [DBSCAN](https://en.wikipedia.org/wiki/DBSCAN) and [cluster
analysis](https://en.wikipedia.org/wiki/Cluster_analysis) for the wider family.

### Least-squares shape fitting — turning a cloud of dots into a number

Fit a shape to a set of points by minimising an error that can be written as a
linear equation, which then has a direct solution and needs no iteration. A fit
uses every point rather than the two extreme ones, so one stray dot moves it far
less than it moves a box drawn round the extremes. And its **residual**, meaning
how far the points sit from the fitted shape on average, is a free measure of
how well the shape really explains the data.

It is used for measuring manufactured parts, which are mostly made of circles,
lines and planes, so it appears throughout metrology and inspection and anywhere
an object's geometry is known in advance. It is rarely right for shapes the
model does not describe, because then it returns a confident number together
with a large residual that nobody checks. The residual is the guard, and
ignoring it is the classic mistake.

For more, Kåsa's algebraic circle fit with the Pratt and Taubin refinements are
the three standard versions, and the geometry is in [circular
segment](https://en.wikipedia.org/wiki/Circular_segment).

### Visibility reasoning — knowing where you could not have looked

The fifth idea is the least familiar of the five, although it is old and
standard in its own field. It is that a sensor's view divides space into three
parts rather than two: the part it can see and found something in, the part it
can see and found nothing in, and **the part it could not have seen at all**.
Treating the third as if it were the second is the mistake, and it is an easy
one, because both of them look like absence in the data.

Mobile robots meet this constantly and have standard machinery for it. They keep
a map in which every cell is marked free, occupied or **unknown**, and the
unknown cells are what exploration is for: a robot that treats unknown as free
drives into walls, and one that treats it as occupied never moves. The same
three-way distinction is what turns "I found nothing there" into the two quite
different statements "there is nothing there" and "I have not looked there".

It is used for exploration and mapping, for planning when things are hidden
behind other things, and for any inspection task where saying "clear" carries a
cost if it is wrong. It is rarely done **analytically**, as it is here, because
most scenes are too irregular for the hidden region to have a closed form, so
the usual approach is to divide space into cells and trace rays through them.
This cell is the lucky case: the objects are upright round solids on a known
plane and the camera looks straight down, so the hidden region is a union of
wedges and can be computed exactly and cheaply.

For more, the general form is [occupancy grid
mapping](https://en.wikipedia.org/wiki/Occupancy_grid_mapping), where the
three-way marking is the whole point.

## 3. Where it sits among the other five

This is the solution the other five are read against, and it is worth being
exact about why, because the comparison is sharper than "rules against models".

It is the only one of the six that holds **no fitted numbers at all**. Solution
2 fits a small network here, and solutions 4 and 6 fine-tune a borrowed model
here, so all three need labelled arrangements, a training run and a weights file
to keep in step with the cell. Solution 5 fits only a small keeper on top of SAM
2, which is much less, but it is not nothing, and the model underneath it was
fitted by somebody else. Solution 3 fits nothing in this cell, which makes it
the closest of the five to this one in cost — but it still carries a weights
file, and the rule inside that file was fitted on somebody else's photographs
for somebody else's purpose, so nobody using it can say what the rule is. **This
solution's rule is one sentence, and that is the difference.**

One more thing follows from holding no fitted numbers, and it is worth naming
because the other documents lean on it. Four of the six start from weights
fitted on photographs of the everyday world rather than on this cell's own
pictures, and that difference between the two sets of pictures is called the
**domain gap**. This solution has none — trivially, because it has no model
that could have one. Solution 2 is the one for which having no gap is a real
property, because it is fitted, and fitted here.

That is what makes it the baseline. The test bench holds the input, the output
and the marking fixed, so a model's score can be compared with this one's
directly, and the comparison has a plain reading: **if a model cannot beat a
written rule, it has earned nothing.** It cost labels, training time and
hardware that this one did not, so matching it is not a result. Beating it is,
and the bench's mask measurements are where that would show, because this
solution's masks are limited by the step that decides which pixels stand above
the table and a model's are not.

The comparison runs the other way as well, which is the part that is easy to
forget. This solution is the one that shows what the problem's *promises* are
worth. Its rule exists only because the glasses are guaranteed to stand apart,
the table's height is known, one kind is on the table at a time, and the glasses
return depth readings. Each of the five models needs fewer of those promises
than this one does, and the harder jobs in the series remove them one at a
time. So a reader who finds this solution convincing should read it as a
statement about the problem rather than about the method: **a problem that a
written rule can answer is a problem whose promises were generous**, and the
value of the other five is what they do when the promises stop.

← [What it needs](05_what-it-needs.md) · [A network trained here from scratch — what it is](../06_a-network-trained-from-scratch/01_what-it-is.md) →
