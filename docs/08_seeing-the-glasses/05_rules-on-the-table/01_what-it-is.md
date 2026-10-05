# What it is

> **What it uses** — NumPy for the arithmetic over the depth readings, and
> OpenCV for the picture handling the cell already does. There is no model, no
> weights file, no training data and no licence condition, because no number in
> this solution was fitted to anything.
> **What it does** — Every pixel the camera hands over carries a depth reading,
> and a depth reading is enough to turn that pixel into a point in the room. So
> the solution turns the picture into a crowd of points, drops every point
> straight down onto the table, and then groups the resulting dots by nothing
> more than how far apart they are on the table. Each group is taken to be one
> glass, and the pixels that fed a group are that glass's mask. The whole method
> is one written rule applied to distances in the room, and the reason it is
> worth writing is that the rule works where the picture cannot: two glasses
> whose outlines run together in the picture are still standing well apart on
> the table.
> **How the output is produced** — from each picture, keep the pixels whose
> points stand above the table top; turn each kept pixel into a point in the
> room using its depth reading and the camera's own pose; drop the height, so
> each glass becomes a flat patch of dots on the table; join dots that lie
> within one chosen distance of each other into groups; check each group against
> the widths this kind of glass is allowed, and split a group that is too wide
> to be one glass; then hand back, for each surviving group, the picture pixels
> its dots came from. Those pixels are the mask, and the mask is the whole
> contribution.
> **What it costs** — no labels, because nothing learns; no training time, for
> the same reason; no graphics processor, because the work is a few passes over
> a small grid of numbers; and no licence condition, because the two libraries
> it uses are already in the cell and neither carries one. The whole cost is the
> thinking needed to state the rule and to justify its one setting.

> **The cell is described once, in [the cell](../01_the-cell.md)** — the layout,
> the two places the camera works from, from the top and from the side, all four
> sensors, and the words this project uses them with. What follows is only what
> is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes the one answer to [the problem this book
sets](../02_the-problem/01_what-is-asked-for.md) that contains no model of any
kind. The problem is to say which pixels belong to which glass when several
glasses stand on a table and the camera looks at them from the top. This one
fits nothing. It states a rule, in words a person can read, and applies it.

The rule is possible because of one fact about the input. Every pixel arrives
with a depth reading beside it, and a pixel with a depth reading is not really
a pixel at all: it is a point in the room, waiting to be worked out. Once the
picture has become a crowd of points in the room, the question "which glass is
this?" stops being a question about the picture and becomes a question about
distance on the table. That change of place is the whole idea, and everything
else in this document follows from it.

**The method is built, and the numbers quoted below were measured by running
it.** The code is in
[`src/08_seeing-the-glasses/01-rules-on-the-table/`](../../../code/src/08_seeing-the-glasses/01-rules-on-the-table)
and it writes its own `results.json` beside itself. Five things this document
describes are still prescriptions rather than code, and each is named where it
appears: the grouping distance is a constant rather than computed from the two
limits it sits between, the fit returns a width and no residual, there is no
minimum-neighbours guard, a group only one station found is not reported as
doubtful, and the branch that works out where a glass could have been hiding is
arithmetic set out here rather than code that runs.

**Nothing here quotes a size.** The cell's rule is that no glass's size is
written down anywhere, so this document speaks in relations — wider than any
glass of this kind can be, narrower than the strip of bare table between two
glasses — and never in figures.

## 2. The problem this solves

The situation is the one [this book's problem
statement](../02_the-problem/01_what-is-asked-for.md) sets out. Four to six
drinking glasses stand upright on a table, all of the same kind, and the kind
is known. They stand inside the rectangle of table this project calls the glass
zone. The camera is on the arm's wrist, and for this problem it works **from
the top**, which means the arm lifts it well clear of the tallest glass the
cell handles and points it straight down. The job is to say which pixels belong
to which glass.

The first word is **mask**. A mask is a picture the same size as the camera's
picture, in which every pixel holds only yes or no, and yes means that this
pixel is believed to show a glass.

The second word is **patch**. A patch is one group of touching yes pixels —
what you get by starting at a yes pixel and spreading out to every neighbouring
yes pixel until nothing new joins. **One patch is not the same as one glass**,
however, and that gap is the first difficulty of this problem.

The third word is the promise the problem makes about where the glasses stand.
There is a guaranteed smallest distance between the centres of any two glasses,
and it is wide enough that even the two widest glasses of a kind leave bare
table between their rims. So two glasses can never touch, and there is always a
strip of bare table between them. Everything below rests on that strip
existing, which is why it is stated here rather than assumed later.

### Why a picture from the top joins two glasses that stand apart

A picture of a tall object is not a picture of its base. The camera looks down,
so the table is the furthest thing from the lens and a glass's rim is the
nearest, because the rim has climbed most of the way from the table up towards
the camera. Nearer things look larger and they also land further out from the
middle of the picture. So a glass's outline is drawn as though the glass stood
further out from the point directly below the camera than it really does, and
**the taller the glass, the further out it is thrown**. This project calls that
effect **splay**, and [the cell](../01_the-cell.md) derives it in full.

The practical result is that a tall glass's outline leans outwards, away from
the point below the camera, and it can come to rest on top of whatever stands
in that direction. A tall glass of that kind is thrown outwards a long way
while a short glass standing beyond it is barely thrown at all, so the tall
glass's outline can reach the short one and pass over it.

**The merge is the loud failure.** If the tall glass's outline reaches the short
one without covering it, the two touch and come back as a single patch. That
patch is wider than any glass of this kind can be, so something can notice.

**The complete cover is the quiet failure.** If the tall glass's outline covers
the short one entirely, the short glass contributes no pixels at all. What comes
back is one patch, of one perfectly ordinary width, with a clean outline, and
nothing about it is wrong. The picture simply holds one glass fewer than the
table does.

![Four glasses of one kind stand a legal distance apart, and from the top two of their outlines run together into a single patch while a tall glass's outline covers a short one completely, although on the table all four stand clear of one another.](../../images/seeing-the-glasses/rules-on-the-table/02-merged-in-the-picture.png)

The second failure cannot be answered by grouping pixels better, because the
pixels are not there to group. It is answered instead by arithmetic that never
looks at the picture's contents, and [when the glasses are completely
hidden](04_a-worked-example.md#1-when-the-glasses-are-completely-hidden) is
where that arithmetic is set out.

## 3. The main idea

A depth camera gives a distance for every pixel, which is enough to turn each
pixel into a point in the room: the pixel says which direction the camera was
looking, the depth says how far along that direction to travel, and the
camera's own pose says where that direction starts. Once every pixel has become
a point in the room, the glasses are told apart by distance on the table, and
the strip of bare table between two glasses — which the picture could not show
us — is simply there to be measured.

← [A transformer segmenter, fine-tuned](../04_the-six-solutions/07_a-transformer-segmenter-fine-tuned.md) · [How it works](02_how-it-works.md) →
