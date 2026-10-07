# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [Turning a pixel into a point in the room](#1-turning-a-pixel-into-a-point-in-the-room)
2. [Keeping only what stands above the table](#2-keeping-only-what-stands-above-the-table)
3. [Throwing the height away](#3-throwing-the-height-away)
4. [Grouping the dots by how close they are](#4-grouping-the-dots-by-how-close-they-are)
5. [The one setting, and where it comes from](#5-the-one-setting-and-where-it-comes-from)
6. [Checking a group against the widths the kind allows](#6-checking-a-group-against-the-widths-the-kind-allows)

## 1. Turning a pixel into a point in the room

The first concept is the one everything else is built on, and it has a standard
name: **back-projection**. Projection is what a camera does when it turns a
place in the room into a place in a picture, so back-projection is that same
step run backwards.

Running it needs three inputs and no guessing. The pixel's column and row,
measured out from the middle of the picture, give the direction the camera was
looking. The depth reading at that pixel gives how far along that direction to
travel. The camera's pose says where the ray begins and which way it faces, and
the arm knows that pose exactly from its own joint encoders, which is why this
step needs nothing estimated. Scaling the sideways offsets by the depth and then
moving the result into the frame the arm works in gives one point in the room.

![One pixel of the depth picture becomes one point in the room: the pixel's offsets from the middle of the picture give the direction the camera was looking, the depth reading gives how far along that direction to travel, and the camera's own pose says where the ray begins.](../../images/seeing-the-glasses/rules-on-the-table/02-pixel-to-point.png)

The lesson worth carrying away is that **a pixel on its own is not a thing; a
pixel is a direction with a distance written on it.** Two details about that
distance catch people out, and both matter here.

The first is that the depth is measured straight out along the lens axis, and
not along the slanted line from the lens to that particular pixel. So a pixel
near the corner of the picture is genuinely further from the lens than its depth
reading says, and this is exactly why the sideways offsets are needed rather
than treating the depth as the distance.

The second is that some pixels come back with no reading at all. Those are
dropped rather than guessed, because a pixel with no distance cannot be placed
anywhere in the room. That is a small loss here and a large one later, and
[where it is strong and where it
breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks) returns to it, because it is
the single assumption that would stop this method working outside the simulator.

One more thing the camera hands over is easy to misread, which is the **focal
length**. Despite its name it is not a length: it is a conversion factor between
directions and pixels, and it follows from how wide an angle the lens covers and
how many pixels it spreads that angle across. Because that angle and that number
of pixels are both fixed, **how much of the world one pixel covers depends only
on how far away that world is**. From the survey height one pixel covers about
1.6 mm of table top, which is coarse compared with a ruler and fine compared
with a glass, since the narrowest glass the cell handles is still 28 pixels
across. That ratio is why a method built on counting pixels into groups can work
at all.

Doing this for every kept pixel gives a **point cloud**, which is simply a list
of positions in the room with no grid, no neighbours and no order. That loss of
structure sounds like a step backwards, and it is in fact the point:
neighbouring in the picture is the misleading idea this method is trying to
escape.

## 2. Keeping only what stands above the table

The second concept decides which pixels are worth turning into points at all,
and it is the cheapest step in the method because of one gift the cell gives it.

Each point in the room has a height above the table, and the table's own height
is a constant the code can look up, because the table is bolted to the same
frame as the arm. So deciding whether a pixel shows the table or something
standing on it is a comparison between two numbers rather than a search for
anything. A pixel is kept when its point stands more than a small clearance
above the table top, and that clearance is chosen to be larger than the noise on
a depth reading and much smaller than the shortest glass the cell handles, so
nothing real falls between the two.

Two more comparisons trim what is left. Anything whose point stands higher than
the tallest glass the cell handles is dropped, which is mostly the arm's own
fingers passing through the picture. Anything with no depth reading is dropped,
for the reason given above. What survives is a mask of pixels that show
something standing on the table, and nothing else about them is known yet.

This step deserves its own section for a reason that returns later and is easy
to miss. **This test, and not the grouping, is what fixes the outer edge of
every mask this solution reports.** The grouping decides which glass a kept
pixel belongs to; it never adds a pixel this test threw away. So the mask stops
a small distance above the table, where the glass's wall can no longer be told
apart from the table it stands on, and it stops wherever the depth reading was
missing. No later step can recover either, and [the masks are what this
contributes](03_the-code.md#2-the-masks-are-what-this-contributes) is where that matters.

## 3. Throwing the height away

The third concept is the one that surprises people, because it discards
information on purpose. Every point is dropped straight down onto the table, so
a point in three dimensions becomes a dot in two, and the height is simply gone.

To see why that helps, look first at the shape the point cloud actually has. A
camera looking down from the top sees the side wall of a glass almost edge-on,
and an edge-on wall catches very few pixels, so there are many points on the top
of a glass, a few near its base, and almost nothing in between. The cloud is not
shaped like a glass at all. It is shaped more like a lid with a thin ring of
crumbs underneath it.

That shape is fatal if you try to group the points in three dimensions, and the
argument is worth following slowly, because it is the heart of this step. In
three dimensions, the top of a glass and the base of the **same** glass are
separated by the glass's whole height, with a hole in between where the wall
should have been. Meanwhile the nearest points of two **different** glasses are
separated only by the strip of bare table between them, and that strip is
narrower than a glass is tall. So the gap *inside* one object is larger than the
gap *between* two objects.

Once that is true, no grouping distance can work. Any distance small enough to
keep two glasses apart also cuts each glass into a top and a bottom, and any
distance large enough to hold one glass together also reaches across to its
neighbour. There is no value in between to choose, because the two requirements
have crossed over each other.

Flattening removes the problem completely. Each glass becomes a small solid disc
of dots, no taller than the paper it is drawn on, while the strip of bare table
between two discs is exactly as wide as it was, because dropping a point
straight down moves it nowhere sideways. So the gap inside one object becomes
zero and the gap between two objects is the whole strip, and a wide range of
grouping distances now works. The short way to remember it is that **height is
the dimension that varies most and tells you least**.

![In three dimensions the gap inside one glass, from its top down to its base, is larger than the strip of bare table between two glasses, so no one distance holds a glass together and keeps its neighbour out; flattened onto the table each glass is a solid disc of dots and the strip is exactly as wide as it was, so a broad range of distances does both jobs.](../../images/seeing-the-glasses/rules-on-the-table/02-why-flatten.png)

One caveat belongs here so that nobody reads more into the disc than it holds.
The flattened disc is not the glass's base. It is the outline of the glass's
widest horizontal slice, because that slice is what hides everything underneath
it from a camera looking down. For a glass with no stem the widest slice and the
base are nearly the same, and the difference does not matter. For a stemmed
glass, whose bowl is wider than its foot, the disc is the bowl. This problem
asks for a rough width rather than an exact one, so the widest slice is an
honest answer. An exact shape needs the camera brought down and round to look at
the glass **from the side**, which is a different job from this one.

## 4. Grouping the dots by how close they are

The fourth concept is the grouping rule itself, and now that the dots are flat
on the table it fits in one sentence.

> Start from a dot nobody has visited. Take every dot within a chosen distance
> of it. Then take every dot within that distance of those. Keep going until
> nothing new joins, and call that clump one glass. Then start again from a dot
> that has not been used.

This rule has a published name, **Euclidean cluster extraction**, and its most
important property is how little it is told. The only setting is the one
distance. Nobody tells it how many groups to find, or how large they should be,
or what shape they should have. That matters a great deal here, because a method
that is told to find five groups can never report that there were four or six,
and reporting the count honestly is part of what this problem asks for.

The rule also **chains**, which means that if A joins B and B joins C then all
three are one group, even when A and C are far apart. Chaining is what lets the
rule hold a ragged, uneven scatter of dots together without being told anything
about shape. However, chaining is also the rule's one weakness, because a single
stray dot sitting in the strip between two glasses is enough to link them into
one group.

There is a practical point about running the rule. Comparing every dot with
every other dot means a number of comparisons that grows with the square of the
number of dots, which becomes hopeless quickly. The usual fix is to sort the
dots into a structure that answers "what is near this point?" without looking at
the far ones, which in this literature is a k-d tree. The code does something
simpler and never compares two dots at all: it marks a grid of 5 mm squares,
grows every marked square outwards by the grouping distance, and joins the
squares that then touch, which is two OpenCV calls over a small grid.

## 5. The one setting, and where it comes from

Because there is only one setting, it is worth being careful about where its
value comes from, and the good news is that it does not come from trial and
error. It is pinned between two limits that are both known before a run starts,
and then placed in the gap between them. This is the same reasoning used when
choosing a measurement tolerance, which has to be larger than the instrument's
noise and smaller than the smallest real difference that must not be missed.

The **lower limit** is set by how far apart the dots on one glass are.
Neighbouring pixels land on neighbouring pieces of table, so the dots arrive in
a mesh whose spacing is roughly what one pixel covers. Two things change that
spacing. The top of a glass is nearer the lens than the table is, which tightens
the mesh there. But a surface seen at a slant, such as the shoulder of a glass
or the outer curve of a bowl, spreads its dots out, because one pixel now covers
a longer piece of surface. If the chosen distance is smaller than the widest
stretch anywhere in that mesh, the chain breaks in the middle of a single glass
and one glass comes back as two or three groups.

The **upper limit** is set by the strip of bare table between two glasses, and
there is a trap here worth naming. The problem promises a smallest distance
between glass **centres**, but the grouping rule measures **edge to edge**. So
the worst case is that smallest centre distance with the two widest glasses of
the kind standing in it. Take half of each glass off the centre distance, and
what is left is the narrowest strip the method will ever be shown. If the chosen
distance is larger than that strip, the chain hops across it and two glasses
come back as one.

How much room is there between those two limits? The narrowest strip the problem
allows is comfortably wider than the widest stretch in the dot mesh, so there is
a broad window and almost any sensible value inside it works. That is a reason
to compute the value rather than to relax about it. The two quantities that set
the window — the widest rim this kind allows, and the guaranteed distance
between centres — live in two different parts of the project, and neither of
them belongs to this solution. So the design prescribes that the grouping
distance be **computed** from those two rather than typed in, and that the run
print both ends of the window. The code has not caught up: it holds 25 mm as a
constant. A value that is derived stays correct the day somebody widens a kind
or moves the glasses closer together; a value that was typed in once goes
quietly wrong on that day, and takes a long time to find.

![The grouping distance is pinned between a lower end set by how far apart the dots on one glass fall and an upper end set by the narrowest strip of bare table two glasses can leave, and the window between them is broad enough that the value can be computed from the two ends rather than tried out.](../../images/seeing-the-glasses/rules-on-the-table/02-grouping-distance.png)

Inside that window the design places the value deliberately **low** rather than
in the middle, because the two mistakes are not equally bad. A glass split into
two groups usually announces itself: half a footprint is far too narrow to be a
glass of this kind, so both halves fail the width check described next. Usually
and not always, and the exception is worth knowing, because it is the same
exception that check has to make anyway. A glass at the edge of a station's
frame is already short of its own footprint through no fault of the grouping, so
the check cannot refuse a narrow width read off a group whose pixels reach that
edge — and a half of such a glass reaches it too. There the split goes
unannounced. Two glasses merged into one group are quieter still, everywhere. So
the setting leans towards splitting, which is the mistake that mostly gets
caught.

## 6. Checking a group against the widths the kind allows

The fifth concept is a check rather than a step, and it is what makes the method
safe to trust with a moving arm.

A glass seen from the top flattens to a disc, so each group of dots should be a
filled circle. Fitting a circle to the dots of a group gives back a centre and a
width, and the standard fit offers a third number as well: the **residual**,
which is how far the dots sit from the fitted circle on average. None of the
four outcomes below uses the residual, so the code computes only the width, and
it fits the dots on the outside of the patch rather than all of them, because a
circle fitted to a filled disc of dots comes back narrower than the disc. The
fit has a pleasant property worth knowing. Written in the obvious way the
equation of a circle is not linear in its centre and its radius, which would
normally mean an iterative search with a starting guess, but if the equation is
multiplied out and certain combinations of the unknowns are treated as the
unknowns instead, it becomes linear. So the fit has a direct solution: no
iteration, no starting guess, and the radius recovered at the end.

**This fitted width is for the check only, and not for the answer.** The test
examiner computes the place and the width that go into the record, from the mask
pixels this solution hands back, and the same examiner step does it for all six
solutions. So the circle fitted here never leaves this solution. It earns its
place because of what it changes: when it says a group is too wide to be one
glass, the group is split, and splitting a group changes which pixels go into
which mask. That is a decision about masks, which is this solution's own
business.

The ruler the fitted width is held against deserves attention, because it is
stronger here than it looks. Across all four kinds the cell handles, the range
of possible widths is broad, since the narrowest glass of the narrowest kind and
the widest glass of the widest kind are very different objects. Within a
*single* kind the range is much narrower, and this problem says which kind is on
the table. So the check available here is far tighter than a general-purpose
test asking only whether an object is object-sized.

The check is written as a rule that **repeats**, and it has four outcomes. Fit
one circle to the group. If its width lies inside the kind's range, the group is
one glass and its pixels are reported as one mask. If the width is **wider**
than any glass of this kind, the group is not one glass, so it is split in two
and the same question is then asked of each part: a part inside the range is one
glass, and a part still too wide is split again. If the width is **narrower**
than any glass of this kind, splitting cannot help, since both halves of a
footprint are narrower than the footprint; such a part is a glass the picture
did not hold all of when its pixels reach the edge of the frame, and a refusal
when they do not. And if any part cannot be settled either way, the whole group
is reported as doubtful, with which side of the range it failed, rather than
guessed at.

![One circle fitted to the whole group comes out wider than any glass of this kind can be, so the group is rejected as one glass and two circles are fitted instead; both of those lie inside the widths the kind allows, so the group is split in two, and the fitted width decides only the split, because the width that goes into the record is measured by the examiner.](../../images/seeing-the-glasses/rules-on-the-table/02-circle-fit-decides.png)

Splitting a group in two is done with a simple and well-known method called
k-means with two centres: put one seed at each end of the group's longest
direction, give each dot to whichever seed is nearer, move each seed to the
middle of the dots it was given, and repeat until nothing moves. Then fit a
circle to each half. The picture above is one round of that, and the rule above
is that round applied again to a half that is still too wide.

What makes this check worth having is that it is **arithmetic rather than
judgement**. The statement "this group is too wide to be one glass" contains two
quantities, both of which were known before the run started, and both of which
can be printed. It is not a threshold somebody adjusted until the tests passed,
and that difference is the whole reason a written rule can be trusted here.

### Why one split is not enough

Splitting once answers two glasses run together, and two is not what the
difficult arrangements hold. The examiner's crowded family stands **three** glasses
to a line and two lines to an arrangement, closer together than the cell's own
layout rule allows, so a chain of three or more glasses in one group is the
ordinary case there rather than the exception. It was counted over the five
blocks of 20 held-out crowded arrangements the solutions are scored on: 365
groups held more than one glass, and **247 of those held three or more**. One
split into two necessarily leaves at least one part holding two glasses, that
part is still too wide, and a rule that stops after one split can only hand the
whole group over.

![Three glasses of one kind run together into one patch of dots 201 mm across; one cut leaves two parts of 111 mm, which are both still too wide for a glass of this kind; and the same question asked again of each part gives four parts of 69 to 72 mm, every one of them a width the kind allows.](../../images/seeing-the-glasses/rules-on-the-table/05-one-split-is-not-enough.png)

What the difference is worth was measured both ways on those same five blocks,
which hold 485 glasses between them. Stopping after one split finds **92** of
them and hands 240 groups over. Repeating the split on any part still too wide
finds **354** and hands 9 over. The second reports 52 masks covering two glasses
where the first reports 4, and that is the price of it; the places it reports
sit 8.7 mm from the truth at the median against 3.3 mm. On the spawned
arrangements, where the layout rule keeps every glass clear of the next, the two
rules are indistinguishable: both find all 499 glasses, at the same places, and
neither hands anything over. So the repetition costs nothing where it is not
needed.

That is not a new rule so much as the natural form of the one already stated.
"A group too wide for one glass of this kind is not one glass" is a statement
about any patch of dots, including a patch that came out of a split, and
applying it to the parts is what this chapter means by it.

### Where the repetition stops

Nothing is counted down, and no limit is written anywhere. Each split gives both
of its parts strictly fewer dots than the part they came from, so the splitting
runs out on its own, and it runs out in one of three ways. Every part is a width
the kind allows, which is the answer. Or a part comes back narrower than the
kind allows, which splitting cannot repair. Or a part cannot be divided at all —
the halving puts every dot on one side of it, or a half holds too few depth
readings for the examiner to fit a footprint to.

A group with any part left over at the end is handed over **whole**, and not in
pieces. Reporting the parts that happened to fit while dropping the one that did
not would be claiming to know how many glasses the group holds, and the one
thing the fit has just said is that it cannot say.

**The condition that two circles together account for all the dots is answered
by the repetition rather than kept as a test of its own.** It was there to catch
two circles fitted to a smear of three glasses, with the middle glass inside
neither of them; repeating the split answers that case directly, by cutting the
smear again. Keeping it as well was measured on one block of 20 crowded
arrangements, where the rule as it stands finds 71 of the 101 glasses and hands
3 groups over, and it is strictly worse: with the extra condition the same block
gives 53 found and 37 handed over, and on the spawned block it refuses 20 whole
glasses that nothing else objects to. The reason is geometry rather than bad
luck. A part cut out of a filled patch by a straight line is not a disc, so a
circle fitted to it does not reach into the corners the cut left, and the
further the splitting goes the less disc-like the parts become.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
