# A foundation model with a keeper

This page describes the fifth of the six solutions in about eight minutes of
reading. It is the one that splits the job in two and borrows only half of it:
a large model that somebody else trained outlines every region in the picture
and names none of them, and a small model fitted here decides which of those
outlines are glasses. By the end of this page you will know what a foundation
model is, why the naming half is the half worth replacing, how little training
data this needs, what it scored on the shared examiner, and why it still does
not survive real glassware. The full treatment is in [the chapter on this
solution](../09_a-foundation-model-with-a-keeper/01_what-it-is.md), which is
about an hour of reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

A **foundation model** is a model fitted once, at great expense, on a very
broad collection of data, and then used for many different jobs without being
fitted again. The one used here is **SAM 2**, the second generation of the
Segment Anything model. Its job is narrow and unusual: pointed at a place in a
picture, it outlines whatever is at that place, and it does not say what the
thing is. It outlines without naming.

That missing half is the reason this solution exists. Every segmenter has to do
two things, find shapes and decide what they are, and the two transfer very
differently from one kind of picture to another. A boundary between one surface
and the surface behind it looks much the same in a photograph and in a grey
picture shaded from depth, so the shape-finding half transfers well. What counts
as a cup, on the other hand, is somebody else's judgement fitted to somebody
else's photographs, so the naming half transfers badly — which is exactly what
[a borrowed model, as it
downloads](04_a-borrowed-model-as-it-downloads.md) demonstrated when it found
ten glasses out of a hundred.

So this solution borrows the half that transfers and replaces the half that does
not. The replacement is a small model fitted in this cell, and this project
calls it the **keeper**, because its whole job is to decide which outlines to
keep.

## 2. How it works

The work runs in five steps.

**The depth readings are shaded into a grey picture**, and SAM 2 reads that
picture once. This single pass is the largest cost in the solution, and
everything after it is cheap.

**A grid of point prompts turns into a heap of outlines.** The model is pointed
at a plain grid of places spread evenly over the whole picture, with no idea
where the glasses are, so it outlines everything the picture contains: the
glasses, the table, the rim of one glass on its own, two glasses that ran
together into a single shape. Asking a model that answers one prompt at a time
to describe the whole scene is done by asking it everywhere.

**The heap is cut down to a shortlist.** Scoring, a stability check and the
removal of near-duplicates leave a manageable list, and this project calls each
survivor a **proposal**.

**Each proposal becomes a handful of measurements on the table.** Its pixels and
their depth readings are turned into points in the room, which gives quantities
such as the width of its footprint and its height above the table top. The
keeper reads that short list of named numbers and answers one of three things:
keep it, drop it, or this is more than one glass. Three answers rather than two
is deliberate, because it lets the solution report doubt instead of guessing.

**What the keeper keeps still has to pass a width check** against the range of
widths the known kind of glass is allowed. The proposals that survive all of
that are the masks this solution reports.

The keeper is small on purpose. It learns from a short table of numbers rather
than from pictures, so it is fitted with scikit-learn in seconds on an ordinary
processor, and printing its inputs beside its answer is an explanation a person
can read. Its training labels cost nothing either, because the examiner's answer
key turns a proposal into a label by arithmetic: a proposal whose pixels mostly
belong to one glass is a keep, and one spread across two is a more-than-one.

The borrowed model is never trained here, and that is a decision rather than an
omission. Leaving it untouched is what keeps the solution's data cost almost
nothing and its weights free of any dependence on this cell; the cost is that
its domain gap cannot be closed from inside.

## 3. What it needs

It needs a **deep learning framework** and the environment to run it, which is a
large dependency for a cell whose simplest answer is a page of arithmetic. It
needs **a weights file this project does not own** and cannot produce, so the
file has to be fetched, pinned to a version, and stored where a run can find it.
This is a real difference from the solutions whose weights are produced here and
can be produced again at any time.

It needs **arrangements for the keeper**, which the examiner renders and labels for
nothing, and **far fewer of them than a network fitted from scratch needs**,
because the keeper learns from a short table of numbers rather than from
pictures. Fitting the keeper then takes seconds with no graphics card. What takes
the time is running the borrowed model over those arrangements to collect the
proposals, and that is where nearly all of this solution's cost sits, at fitting
time and at run time both.

It needs **the shading got right**, which is the only part where a careless
choice makes everything after it worse without anything complaining.

And its **licence is permissive**, which is a real advantage rather than a
footnote. The two solutions built on Ultralytics YOLO26-seg are covered by the
Affero General Public License, so on the day this cell becomes a product rather
than an experiment those
two have a question to answer and this one does not.

## 4. What it scored

The two sets of arrangements are the ones every solution is given: spawned
layouts at the cell's own spacing, and crowded layouts closer than that.

| | found | missed | merged | position median | mask covered | mask not the glass |
|---|---|---|---|---|---|---|
| spawned, 100 glasses | 81 | 19 | 0 | 3.0 mm | 96.8% | 0.0% |
| crowded, 101 glasses | 73 | 28 | 0 | 1.0 mm | 98.4% | 0.0% |

**The result to take seriously is the last column.** None of its masks leaked
onto a neighbouring glass or onto the table, in either set, and it merged
nothing and split nothing. That is what the keeper and the width check are for:
every doubtful case was turned into a dropped proposal rather than into a wrong
glass. It is also the best crowded mask coverage of the six after the fine-tuned
model, which is a good showing for a model that was never trained on these
pictures at all.

What it pays for that caution is in the first column. It found 81 glasses out of
100 on the spawned set, so about one glass in five arrived as a proposal the
keeper would not keep or as no proposal at all. The borrowed model is being
shown a kind of picture it has never seen, and nothing in this solution can
teach it otherwise. The full table for all six is in [the
results](../11_the-results.md).

## 5. Where it is strong and where it breaks

**Almost nothing is fitted here, and what is fitted is small, fast and can be
inspected.** The borrowed half cannot fall out of step with this cell, because
it never knew anything about it. No other solution in this book has that
property.

**It needs the least data of the four that fit anything.** **It splits the job
along the line that transfers**, which is the clearest reason to prefer it to
solution 3. **It notices things nobody described**, because the grid proposes
every region in the scene, so a spoon left on the table arrives as a proposal
and is answered "not a glass" rather than passed over in silence; every other
solution here is blind to whatever falls outside the one class it knows. And
**its doubt is cheap and explicit**, which is what the zero in the last column
of the table is made of.

Against those, the weaknesses are not small.

**The domain gap is the largest risk and it cannot be closed from inside.** The
only levers available are the shading and the grid, because nothing here is
trained. Where those are not enough, the answer is one of the fine-tuned
solutions.

**It cannot be taught this cell's hard cases.** Pairs standing closer than the
rule allows, pairs actually touching, a glass half hidden behind another: all of
those can go into a training set for the fine-tuned solutions, and none of them
can be communicated to the borrowed model at all.

**It depends on depth twice over.** The keeper's best inputs come from depth
readings, and so does the picture itself, because the picture *is* shaded depth.
So on the day the glasses become real transparent glass and the depth camera
stops returning anything through them, this solution has no input at all, not
even a picture. It is not the solution that survives real glassware; it is the
solution that survives having almost no training data, which is a different and
narrower virtue.

**It is blind to a glass hidden completely**, which is a fact about the input
rather than about the model, and is answered by geometry instead in [looking
again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md).

## 6. When to choose it

Choose this when labelled examples are scarce and a large promptable segmenter
is available. It is the right shape whenever the shapes in your pictures are
ordinary but the categories are not: industrial parts, medical structures, or
anything a public model has never been asked to name. A keeper fitted on a few
hundred proposals is a day's work, where fine-tuning a whole model on hand-drawn
outlines is weeks.

Choose it also when a wrong answer is more expensive than a missing one, because
the three-answer keeper and the width check after it are built to turn doubt
into silence.

Do not choose it when the pictures themselves are far from what the borrowed
model was fitted on and accuracy matters more than setup cost, because then the
gap has to be closed by training and only [the same model,
fine-tuned](05_the-same-model-fine-tuned.md) or [a transformer segmenter,
fine-tuned](07_a-transformer-segmenter-fine-tuned.md) can close it. And do not
choose it if the sensor itself is the problem: this solution needs depth for
both of its halves.

The code is in
[`src/08_seeing-the-glasses/05-sam2-with-a-keeper/`](../../../code/src/08_seeing-the-glasses/05-sam2-with-a-keeper)
and it writes its own `results.json` beside itself. The full treatment, with
what a foundation model is, how a promptable model becomes a proposer of
everything, the keeper's inputs in detail, and the second rung that prompts with
a word instead of a grid, starts at [what it
is](../09_a-foundation-model-with-a-keeper/01_what-it-is.md).

← [The same model, fine-tuned](05_the-same-model-fine-tuned.md) · [A transformer segmenter, fine-tuned](07_a-transformer-segmenter-fine-tuned.md) →
