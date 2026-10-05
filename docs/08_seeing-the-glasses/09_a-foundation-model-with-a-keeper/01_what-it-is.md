# SAM 2 with a keeper — what it is

> **What it uses** — SAM 2, the second generation of the Segment Anything model,
> loaded through Hugging Face `transformers` and never trained here;
> scikit-learn for the one small model that is fitted here; PyTorch underneath,
> which reaches this machine's integrated graphics through its MPS backend.
> **What it does** — SAM 2 outlines whatever is at a place it is pointed at, and
> it names none of what it outlines. Pointed at a plain grid of places spread
> over the whole picture, it therefore outlines everything the picture contains:
> the glasses, the table, the rim of a glass, two glasses that ran together into
> one shape. A small model fitted in this cell, called the **keeper**, is then
> handed each of those outlines on its own and decides whether it is one glass.
> So the half of the job that finds shapes is borrowed whole, and the half that
> decides what a shape is gets replaced.
> **How the output is produced** — the depth readings are shaded into a grey
> picture; SAM 2 reads that picture once; a grid of point prompts turns into a
> heap of outlines; scoring, stability and duplicate removal cut the heap down
> to a shortlist of **proposals**; each proposal's pixels and their depth
> readings become a handful of measurements on the table; the keeper reads those
> measurements and answers keep, drop, or more than one glass; what it keeps
> still has to pass a width check against the kind, which is known; and the
> proposals that survive all of that are the masks this solution reports.
> **How it differs from the other five** — **solution 1** writes the deciding
> down as rules and fits nothing at all, where this one fits the deciding and
> borrows the seeing. **Solution 2** fits every number it uses on this cell's
> own pictures, where this one fits almost none of them. **Solution 3** borrows
> a model's shapes *and* its names, where this one borrows the shapes and
> replaces the names. **Solution 4** moves borrowed weights towards this cell's
> pictures, where here the borrowed weights never move at all. **Solution 6**
> fits a whole transformer segmenter in this cell, which makes it the largest
> fitted thing in the set against the smallest.
> **What it costs** — no hand labelling, because the bench's own answer key
> turns a proposal into a training label by arithmetic. Fitting the keeper is
> seconds of processor time with no graphics card; what takes real time is
> running SAM 2 over the arrangements to collect the proposals to fit it on. At
> run time it costs one pass of the picture encoder per picture and very little
> after that. The weights are large and are not owned by this project, so they
> have to be fetched and pinned to a version. The licence is permissive, which
> is something solutions 3 and 4 cannot say.

> **The cell is described once, in [the cell](../01_the-cell.md)** — the layout,
> the two places the camera works from, from the top and from the side, all four
> sensors, and the words this project uses them with. What follows is only what
> is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes a way to do [the job this book sets
out](../02_the-problem/01_what-is-asked-for.md) in which almost nothing is
fitted in this cell. The other five solutions either write every rule down by
hand or fit a model to this cell's own pictures. This one
does neither for the part that finds objects: the finding is done by a very
large model that somebody else fitted, somewhere else, on photographs of the
real world, and it is used exactly as it downloads. The only numbers fitted here
belong to a small model that looks at what the large one produced and decides
which parts of it are glasses.

The solution therefore has two halves, and they are very unequal in size. The
first half is a **borrowed model** that can be asked *what is at this point?*
and answers with an outline of the thing at that point. Asked at many points at
once, it outlines everything the picture holds, while naming none of it, because
it produces regions and not labels. The second half is the **keeper**, a small
model fitted in this cell, which is handed each of those outlines in turn and
says whether it is one glass.

By the end you will understand what a foundation model is and what it means for
one to be promptable, how a plain grid of points turns such a model into a
proposer of everything in a scene, why the large model is never trained here and
what that buys, what the keeper is shown and why it is fitted rather than
written as a page of thresholds, why it must give three answers rather than two,
and what its probability has to have done to it before a threshold can be put on
it.

You will also understand the one design question this solution carries inside
itself, which is the most interesting part of the document. A newer generation
of the same borrowed model takes a **word** instead of a point: ask it for
"drinking glass" and it returns every instance of that concept. That would
delete the keeper completely. So this solution has two **rungs**, meaning two
versions of one approach, one of them a generation newer than the other. The
last concept section weighs the two against each other, and the honest answer is
not simply that the newer one is better, because the keeper is the one place in
this whole set of six solutions where the deciding can be explained by printing
its inputs beside its answer.

## 2. The problem this solves

This book puts four to six glasses on the table. They are all of one kind, the
kind is known, and they are opaque, so the depth camera sees them. The job is to
say which pixels belong to which glass, and to give each glass a place on the
table and a rough footprint width. Nothing is picked up and no shape is
measured.

What is asked for is therefore **instance segmentation**, meaning one outline
per object rather than one label per pixel, because how many glasses there are
is part of the answer. The difficulty is not noticing that something is on the
table but deciding **how many things are there**, since two glasses standing
clearly apart can still leave one connected shape in a picture taken from the
top.

Four of the other five solutions reach that answer at one of two prices, and
this one is an attempt to pay neither in full.

Solution 1 pays in **rules somebody has to write**. Every limit inside which it
is safe has to be worked out by a person and stated in code, so its cost is that
somebody must be able to state the rule at all.

Solutions 2, 4 and 6 pay in **fitting**. Each of them ends up with a file of
weights that is a second copy of this cell, produced by hours of rendering and
hours of training. That copy has a quiet failure mode: change the lighting,
change the table's surface, widen the range of sizes a kind is drawn from, and
the file is out of date in a way that no test of the code can notice.

This solution avoids the second price by borrowing weights that were never
fitted to this cell, so there is nothing in them that can fall out of step with
it, and it avoids most of the first price by fitting the one decision that is
left over.

The catch arrives with the first sentence of the design, and much of the rest of
this document is about it. **A model that was never fitted to this cell also
never saw this cell.** It does not know about splay, it does not know that
everything on the table is one kind of object, it does not know the gap the cell
guarantees between two glasses, and there is no way to tell it any of those
things.

## 3. The main idea

The main idea is to stop asking for glasses and start asking for everything,
then to throw away what is not a glass.

**The first half is to ask for everything.** Rather than fit something that
finds glasses, take a model that can be asked what is at a point and get back an
outline of the thing at that point, and then ask it at points spread evenly over
the whole picture. Every point lands on something, so what comes back is an
outline of the table, an outline of each glass that is distinguishable at all,
outlines of parts of glasses such as a rim, and outlines of groups of glasses.
None of them carries a name. The model is SAM 2, and no gradient is ever
computed through it in this project.

**The second half is to decide what to keep.** Each outline that survives a
first cleanup is called a **proposal** from here on. The **keeper** is a small
model which is shown a handful of measurements about one proposal and answers
whether that proposal is one glass. The keeper is the only thing fitted in this
solution, it would fit in seconds, and the examples it would learn from cost
nothing, because the bench already knows which pixels belong to which glass in
the arrangements it draws.

So, in the plainest terms: **everything that finds objects is borrowed whole,
and everything fitted here is one small decision at the end.** Beside the
borrowed model's weights, the keeper's numbers are a rounding error.

That split is not an accident of convenience, and it is the sentence worth
carrying through the rest of the document. **The job is divided along the line
that transfers best.** A shape is a shape everywhere: a step in distance between
one surface and the surface behind it is the same kind of evidence in a
photograph of a kitchen and in a grey picture shaded from depth, which is why
the proposing half can be borrowed from a model that never saw this cell. What
counts as a cup, on the other hand, is a judgement that somebody fitted to
somebody else's collection of pictures, and it has no reason to agree with what
counts as a glass here. So the proposing half is borrowed and the naming half is
replaced. **That is the opposite trade from solution 3**, which borrows both
halves and takes the borrowed model's names as the answer.

← [The same model, fine-tuned here — how it compares](../08_the-same-model-fine-tuned/06_how-it-compares.md) · [SAM 2 with a keeper — how it works](02_how-it-works.md) →
