# What it is

> **What it uses** — the Ultralytics package, PyTorch running on this machine's
> integrated graphics through Apple's MPS backend, and the Ultralytics
> YOLO26-seg instance segmentation model exactly as it downloads. The weights
> fetch themselves the first time the model is used.
> **What it does** — it shows the borrowed model a survey picture from the top,
> takes the list of objects the model reports, and keeps the outlines whose
> name is a drinking vessel while dropping everything else the model named. A
> survey is three pictures from three overlapping stations, and the model is
> asked about each one on its own, which is the bench's arrangement rather than
> this solution's.
> Nothing whatsoever is fitted in this cell, so there is not a single number in
> this solution that came from this project's own data.
> **How the output is produced** — the grey picture shaded from depth goes into
> the model; the model returns, for each object it believes it found, a box, a
> name from a fixed list of categories, a confidence number and an outline; the
> design keeps the outlines named as drinking vessels and discards the names
> afterwards; the kept outlines are the masks, and the shared arithmetic in [the
> test bench](../03_the-test-bench.md) turns each mask into a place on the table and a
> rough width.
> **How it differs from the other five** — [solution
> 1](../05_rules-on-the-table/01_what-it-is.md) uses no model at all and reasons about depth with
> arithmetic a person can read. [Solution 2](../06_a-network-trained-from-scratch/01_what-it-is.md) fits
> every number it holds on this cell's own pictures, where this one fits none.
> [Solution 4](../08_the-same-model-fine-tuned/01_what-it-is.md) is this same library, this same model and
> these same starting weights with training on this cell's pictures added, and
> with the borrowed list of category names cut to the single class "glass",
> which is part of that training rather than a separate choice. Nothing else
> varies between the two, and that is the point of running both. [Solution
> 5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md) borrows a model that outlines without naming, so
> it has to fit a small keeper here to decide which outlines are glasses, which
> is the one thing this solution never needs. [Solution
> 6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md) trains a different architecture here and carries
> a permissive licence instead of this one's.
> **What it costs** — no labels, no training run, no weights file to keep in
> step with the cell, and no graphics card of its own. The whole cost is the
> licence, which is why it has a section to itself below.

> **The cell is described once, in [the cell](../01_the-cell.md)** — the layout,
> the two places the camera works from, from the top and from the side, all four
> sensors, and the words this project uses them with. What follows is only what
> is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes how [what this book asks
for](../02_the-problem/01_what-is-asked-for.md) could be answered by downloading
a model and running it, without collecting a single label and without training
anything at all. The solution is built, and what it scored is recorded beside
the code, in
[`03-yolo-zero-shot/README.md`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/README.md)
and in that folder's `results.json`. The reasoning below was written before the
run and is kept in the voice it was written in, so where it says what the method
would do, read that as what the design expected rather than as a measurement.

The design is worth writing down because of what it does not contain. Every
other solution that uses a model pays something before it can answer: a set of
labelled pictures, a training run, and a weights file that has to be refitted
whenever the cell changes. This one would pay none of that, because the model it
borrows was already fitted on photographs of everyday scenes, and the list of
things that model can name already contains drinking vessels. So the model would
be asked for glasses and would answer on the first picture, having never seen
this cell.

That makes it the cheapest of the six to try, and it also makes it the baseline
for the sharpest comparison in the set. By the end you will understand what an
instance segmentation model returns and how that differs from the two
neighbouring kinds of segmentation model, why the borrowed category names can
only ever be a filter, how the outline is built and why it is approximate in a
way the arithmetic downstream feels, why the confidence number beside each
outline is not a probability on these pictures even though it looks like one,
what the domain gap is and why it runs in both directions here, and what the
licence costs, because on this solution the licence is a real cost rather than a
footnote.

## 2. The problem this solves

This book asks for one record per glass on the table, each with a mask, a place
and a rough width. The difficulty is not seeing that something is there but
deciding **how many things are there**. Two glasses standing well apart on the
table can still leave one connected shape in a picture taken from the top,
because the rim of each glass is nearer the lens than the table is, so each
glass covers more of the picture than its footprint deserves. A method that
treats each connected shape as one object then reports one glass where two are
standing. That is the merge, and it is what most of the six solutions attack.

A model built to find objects attacks the merge directly, because such a model
returns **one outline per object** rather than one outline per connected shape.
Two glasses whose outlines join in the picture are still two objects, and a
model fitted on crowded photographs has met that situation many thousands of
times, in scenes where cups and glasses stand side by side on tables. So the
hope is a reasonable one: the separation this cell finds hard is the separation
the borrowed model was fitted to perform.

What makes this version of the hope worth testing first is its price. The other
model-based solutions need pictures of this cell with every glass outlined, and
then a training run that has to be repeated whenever the cell changes. Here
there would be nothing to collect and nothing to repeat. If the borrowed model
worked even moderately well, it would be the fastest route from no perception at
all to a working report, and that is worth knowing in an afternoon rather than
after a week spent building a training set.

## 3. The main idea

The idea has three steps, and only the first two belong to this solution at all.

**First, run the borrowed model on the survey picture from the top.** The model
is Ultralytics YOLO26-seg, taken exactly as it downloads. It is an **instance
segmentation model**, which means that for every object it believes it has found
it returns four things together: a box around the object, a name taken from a
fixed list of categories, a number saying how sure it is, and an outline marking
which pixels inside the box belong to that object rather than to the background
or to a neighbouring object.

**Second, keep the outlines whose name is a drinking vessel.** The fixed list of
categories the model was fitted on is a general one, covering the ordinary
contents of ordinary photographs, and several of its entries are things a person
drinks from. Those are the ones this design would keep, and everything else the
model named would be dropped.

**Third, hand the kept outlines to the shared arithmetic.** An outline is a set
of pixels, and turning a set of pixels into a place on the table and a width is
a job the test bench does, the same way, for every solution that produces masks.
Nothing about that step changes here.

So the whole of this solution is the first two steps, and the second step is a
filter on a list of names rather than anything fitted. That is the point to
remember: **this solution would contain no numbers fitted in this cell at all**,
not one.

← [A network trained here from scratch — how it compares](../06_a-network-trained-from-scratch/06_how-it-compares.md) · [How it works](02_how-it-works.md) →
