# What it is

> **What it uses** — the RF-DETR package, with PyTorch underneath it, reaching
> this machine's graphics processor through the MPS backend. The model is
> **RF-DETR-Seg**, a transformer that detects and segments in one pass. It is
> published under the Apache 2.0 licence and it is offered in a range of sizes,
> so the size can be chosen to suit the machine.
> **What it does** — it takes one picture from the top and returns one mask per
> glass, with no step in between that has to cut a joined region apart. The
> first of its two rungs is built and has been scored; the second was never
> fitted to completion and claims no number. The model arrives with its weights
> already fitted to a large collection of ordinary labelled pictures, and
> training then continues on this cell's own pictures with the list of classes
> cut down to the single class "glass". The model carries a fixed number of
> **queries**, each of which either reports one glass or reports nothing, and a
> mask is predicted over the whole picture rather than inside a rectangle.
> Because of that, this is also the one solution of the six that can be asked
> for the part of a glass nobody saw.
> **How the output is produced** — the grey picture shaded from depth goes in;
> the model's body turns it into a description of every part of the picture; the
> queries read that description and each returns a class, a rectangle and a mask
> over the whole picture; the queries that report "nothing" are dropped; each
> surviving mask is handed to the bench, which back-projects its pixels with
> their depth readings and the camera's own pose and returns a place and a rough
> width.
> **What it costs** — the labels cost nothing, because the bench renders which
> glass owns each pixel and a mask is a selection over that. The training time
> is the time of a fine-tune rather than of a start from nothing, so it is far
> less than building the same model from random numbers would take, and it is
> still the largest single cost in this solution. The hardware is one laptop
> with a graphics processor sharing the machine's memory, reached through
> PyTorch's MPS backend; there is no NVIDIA card here and no CUDA. The licence
> is Apache 2.0, which permits the model to be used without any obligation on
> the code standing around it.

> **The cell is described once, in [the cell](../01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the side,
> all four sensors, and the words this project uses them with. What follows is
> only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes the sixth of the six answers this book gives, and it is
the one built on the most modern of the architectures in the set. The problem asks
which pixels belong to which glass, and this solution answers it by taking a
transformer that detects and segments objects, RF-DETR-Seg, and continuing its
training on this cell's own pictures with one class, "glass".

Two things make it worth a document of its own rather than a line in a table.
The first is the shape of its output. Older segmenters find a rectangle round an
object first and then paint a mask inside that rectangle, so the mask can never
reach past the rectangle's edge. This model has no such rectangle standing in
the way of its masks, and that single structural fact is what the rest of this
document builds on. The second is what that fact permits: this is the only one
of the six that can reasonably be asked to mark the part of a glass that nothing
in the picture shows, which is the **second rung** of this solution and is
described in full below.

One thing has to be said before the rest. **The first rung is built and has
been scored on the bench; the second rung is not.** Its fine-tune was started
with the same settings as the first and stopped unfinished when the machine
filled up, so no number is claimed for it anywhere. This document quotes no
scorecard of its own either: the first rung's numbers sit beside its code, in
[`06-rf-detr-fine-tuned/`](../../../code/src/08_seeing-the-glasses/06-rf-detr-fine-tuned).
So where this document says what the second rung would do, that is the design
speaking and not a run.

By the end you will understand what a query is and why a fixed number of them is
a different idea from a search that proposes regions, what set prediction means
and why it removes a cleanup step that other detectors need, what cutting the
class list down to one class does and does not change, why this architecture
suits the request for a glass's whole silhouette better than a rectangle-based
one does, and the single mistake that would do the most damage if this solution
were built carelessly.

## 2. The problem this solves

Four to six glasses stand on the table. They are all of one kind, the kind is
known, and they are solid, so the depth camera reads them. The job, set out in
full in [the problem](../02_the-problem/01_what-is-asked-for.md), is to say which pixels belong to which
glass, to give each glass a place on the table, and to give each a rough
footprint width. Nothing is picked up here and no shape is measured.

What makes that hard is the way a picture from the top treats a glass. A camera
looking straight down does not draw a glass's outline on top of the glass,
because the rim is nearer the lens than the table is, so the outline is thrown
outwards away from the point directly below the camera, and the taller the glass
the further out it goes. This project calls that outward throw **splay**.
Because the kind on the table draws from a wide range of proportions, with its
tall end more than twice the height of its short end, two glasses of one kind
are splayed by very different amounts, and the taller one's stretched outline
can reach across the ground where the shorter one stands.

Two different failures follow from that, and this solution is aimed at both.

The first is that two glasses standing clear of each other on the table can
leave **one joined region** in the picture. A **mask** is a picture the same
size as the photograph in which every pixel holds nothing but yes or no, where
yes means "this is glass". When two outlines meet, the yes pixels of the two
glasses form one joined region, and the usual way of turning such a region into
objects — spread out from a yes pixel to every yes pixel touching it, and call
everything reached one object — returns one object where two glasses stand. That
spreading answers only the question *are these pixels joined?*, and joined is
exactly what the two outlines are.

The second is that a glass can be **partly covered** by the glass in front of
it. Its mask then stops where the near glass begins, and what is left is not a
smaller copy of the glass but a slice of it, lying all to one side. That failure
is quiet rather than loud, and the whole of [the second
rung](02_how-it-works.md#6-the-second-rung--training-against-the-whole-silhouette) is about it.

There is a third difficulty neither of those reaches, which is a glass covered
so completely that it contributes no pixels at all. [When the glasses are
completely hidden](04_a-worked-example.md#1-when-the-glasses-are-completely-hidden) settles what this
solution can and cannot do about it, and the answer is short.

## 3. The main idea

The main idea is to use a model whose output already holds separate objects, and
to use one whose masks are not shut inside rectangles.

Those are two separate claims and it is worth keeping them apart. The first is
shared with other solutions in this set: a model that returns one mask per
object needs no step that divides a joined region, because the division never
had to happen. The second belongs to this solution alone, and it is what the
second rung rests on, because a mask asked to cover more than the camera saw has
to be free to grow.

The second half of the main idea is where the numbers inside the model come
from. A model of this kind holds a great many weights, and determining all of
them from this cell's pictures alone would be unreasonable. It does not have to
be done, because the weights arrive already fitted to a large collection of
ordinary labelled pictures, and training continues from those weights on this
cell's own pictures with the class list cut down to one entry. That is
**fine-tuning**, and it is why a model this size is a sensible thing to put on
one laptop.

← [SAM 2 with a keeper — how it compares](../09_a-foundation-model-with-a-keeper/06_how-it-compares.md) · [How it works](02_how-it-works.md) →
