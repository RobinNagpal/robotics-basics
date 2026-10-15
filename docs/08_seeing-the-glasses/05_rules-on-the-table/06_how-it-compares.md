# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks. It names the general ideas behind it. Then it places it beside the
other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The earlier pages showed how the method works, so this section starts with how
well it works. [The examiner](../03_the-examiner/01_the-examiner.md) marked it
over five blocks of 20 held-out arrangements. On the spaced arrangements it
finds 100.0 glasses in every 100, in all five blocks. On the crowded
arrangements it finds 73.0 in every 100, and the five blocks range from 70.3 to
75.5. [The results](../11_the-results.md) puts these rows beside the other five
solutions.

The strengths come first.

**It can be read.** Nothing is fitted. The rule is one sentence about distance
on the table. Its one setting could be computed from two numbers the project
already holds.

**It is exact and repeatable.** The same picture always gives the same groups.
Nothing in the method is random or depends on an order.

**When it fails, one printed number usually shows why.** Each step gives one
number worth printing: the pixels kept above the table, the squares marked, the
groups found, the dots per group, and each group's width. For example, if the
table height is set a little too low, the whole table top becomes one huge group.
The count of kept pixels shows this at once. A grouping distance that is too
small gives too many groups with too few dots. One that is too large gives too
few groups, with one impossible width.

**It gives places in real distances from the arm's base**, because it works in
the room from the start.

**It fits the search for hidden glass.** It already knows each found glass's
place, width and height. So the arithmetic in [looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) needs nothing
more from it.

It has two weaknesses. One is a limit of the idea, and one is a limit of the
sensor.

**Someone has to be able to state the rule.** Touching glasses leave no strip of
bare table, so the rule cannot separate them. [The case the rule cannot
answer](04_a-worked-example.md#the-case-the-rule-cannot-answer) shows this. Two
glasses one behind the other, at the same distance from the camera, also stay
one group. And if all four kinds could be on the table at once, the range of
allowed widths would be much wider. The width check would then be much weaker.

**The rule needs depth readings, and real clear glass does not give them.**
Every dot in this method comes from a depth reading. A pixel with no reading
gives nothing. The cell works only because the simulator draws the glasses as
solid and opaque. [What is on the
table](../02_the-problem/01_what-is-asked-for.md#2-what-is-on-the-table) states
this assumption. So this method would not work on real glasses as it
stands. That is a limit of the method, not of the cell.

The next section shows that none of these ideas is new.

## 2. The general ideas behind this

The strengths and weaknesses above come from well-known ideas, and this section
names them. Together they are the standard recipe for an arm working over a
table, and have been for about twenty years. Treat the depth picture as a cloud
of points. Delete the table. Group what is left, one group per object. It became
the default because it needs no training data, no model file, and no idea what
the objects are. It also gives places in real distances, which an arm needs
anyway.

### The pinhole camera model — turning a pixel and a depth into a point

The pinhole camera model is the simple camera model behind back-projection.
[Turning a pixel into a point in the
room](03_how-it-works.md#1-turning-a-pixel-into-a-point-in-the-room) explains
it. It goes wrong on surfaces a depth sensor reads badly, such as glass,
polished metal or black plastic. There the depth is missing or wrong, so the
points are wrong too.

For more, see the [pinhole camera
model](https://en.wikipedia.org/wiki/Pinhole_camera_model), and Hartley and
Zisserman's [Multiple View Geometry](https://www.robots.ox.ac.uk/~vgg/hzbook/).

### Plane segmentation with RANSAC — finding and deleting the table

**RANSAC** stands for random sample consensus (Fischler and Bolles, *CACM*,
1981). It fits a model to data that has many stray readings. For a table, it
picks three points at random and makes the plane through them. It counts how
many other points lie on that plane. It keeps the best plane after a few hundred
tries. Deleting that plane leaves just the objects.

It works badly when no one shape fills most of the scene. It also works badly
when the thing you want is the smaller part and several models fit equally well.

**This solution does not need it.** The table is fixed to the arm's frame, so
its height is known. Finding it is a comparison, not a search. For more, see
[RANSAC](https://en.wikipedia.org/wiki/Random_sample_consensus).

### Density-based clustering — grouping points by how close they are

This is the grouping rule in [grouping the dots by how close they
are](03_how-it-works.md#4-grouping-the-dots-by-how-close-they-are). Robotics
calls it **Euclidean cluster extraction**. Its better-known relative in
statistics is **DBSCAN** (Ester and others, KDD 1996). DBSCAN adds a rule that a
point needs a minimum number of neighbours, so scattered noise cannot form a
group. This solution keeps noise out more simply. It throws away any group with
fewer than 100 dots. Like every rule of this kind, it cannot separate objects
that touch.

For more, see [DBSCAN](https://en.wikipedia.org/wiki/DBSCAN) and [cluster
analysis](https://en.wikipedia.org/wiki/Cluster_analysis).

### Least-squares shape fitting — turning a cloud of dots into a number

This is the circle fit in [checking a group against the widths the kind
allows](03_how-it-works.md#6-checking-a-group-against-the-widths-the-kind-allows).
It works badly on shapes the model does not describe. Then it returns a
confident number, and only the residual would show the problem.

For more, Kåsa's circle fit and the Pratt and Taubin versions are the three
standard forms. The geometry is in [circular
segment](https://en.wikipedia.org/wiki/Circular_segment).

### Visibility reasoning — knowing where you could not have looked

A sensor's view splits space into three parts, not two. There is the part it
saw something in, the part it saw nothing in, and **the part it could not see at
all**. Treating the third part as the second is an easy mistake, because both
look empty in the data. Mobile robots keep a map that marks each cell as free,
occupied or **unknown**. This cell is a lucky case. The hidden part can be
worked out exactly, because the glasses are upright round solids on a known
plane. [Looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) does that.

For more, see [occupancy grid
mapping](https://en.wikipedia.org/wiki/Occupancy_grid_mapping).

These ideas explain the method on its own. The last section compares it with
the other five solutions.

## 3. Where it sits among the other five

This section uses everything above to place this solution among the six. It is
the only one with **no fitted numbers at all**. Solution 3 also fits nothing in
this cell, so it is closest in cost. But it still carries a weights file. The
rule inside that file was fitted on someone else's photos for someone else's
purpose. Nobody using it can say what the rule is. **This solution's rule is one
sentence, and that is the difference.**

That makes it the baseline. The examiner keeps the input, the output and the
marking the same for every solution. So a model's score can be compared with
this one directly. The reading is simple: **if a model cannot beat a written
rule, it has gained nothing.**

This solution also shows what the problem's *promises* are worth. Its rule
exists only because of four promises. The glasses stand apart. The table's
height is known. Only one kind is on the table at a time. The glasses give depth
readings. **A problem that a written rule can solve is a problem with generous
promises.** The other five are worth what they do when those promises break.

← [What it needs](05_what-it-needs.md) · [A network trained here from scratch — what it is](../06_a-network-trained-from-scratch/01_what-it-is.md) →
