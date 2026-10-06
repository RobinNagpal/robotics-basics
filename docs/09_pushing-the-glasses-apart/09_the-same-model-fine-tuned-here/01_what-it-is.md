# What it is

> **What it uses** — LeRobot, with PyTorch underneath, and this machine's own
> Metal GPU for the training run, which is further than this document expected
> a 450-million-parameter fine-tune to go. The model is SmolVLA: the same
> library,
> the same model and the same downloaded weights as [solution
> 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md), with its training continued on pushes
> made on the examiner's tables by low-rank adaptation, so that the actions it emits are
> fitted to this cell's own range rather than left to the range the borrowed
> recordings happened to use.
> **What it does** — a model that arrives fitted to real teleoperation of
> other robots is neither thrown away nor used as it arrives. Its numbers are
> kept, and a small correction to them is learned from pushes made on this
> examiner, so that it stops being a general copier of robot motion and becomes a
> pusher of glasses on this table. The action chunks it then emits are this
> solution's answer to the problem this book sets.
> **How the output is produced** — a rendered view of the table from the top
> goes in, together with one instruction in plain English and the arm's own
> pose, which is the same every time because the jaw is parked between
> actions. The corrected model returns an **action chunk**: a short run of
> consecutive jaw waypoints predicted together in one pass. The shared
> geometry refuses the glasses that tip before they slide, and a chunk whose
> path would reach one of those is not carried out.
> The examiner then carries the waypoints out directly, because a chunk needs no
> expansion. The arm looks again, and the loop repeats until the table is done
> or the push budget is spent.
> **What it costs** — the demonstrations are free, because solution 2
> generates them and the examiner executes them without anybody holding a
> controller. The training is a low-rank fine-tune, and it fits in 1.02 GiB on
> a laptop, so nothing was rented; hours of a small rented accelerator, of
> order tens of dollars, is what it would take to spend real compute on it.
> Running it costs one large forward
> pass per chunk, the same as its partner's, so the two cost the same to run
> and differ only in what it cost to build them. The licence is not the
> obstacle it was for [the pair that tells the glasses
> apart](../../08_seeing-the-glasses/08_the-same-model-fine-tuned/05_what-it-needs.md#2-the-licence),
> but a fine-tuned file inherits whatever terms the borrowed file carried, so
> the terms have to be read before anything leaves this project.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document explains how to answer [the problem this book
sets](../01_the-problem/01_what-is-asked-for.md) by taking a robot foundation
model that was already fitted elsewhere and continuing its training on pushes
made in this cell. The method has a name, **fine-tuning**, and it is the
ordinary way a borrowed model is put to work on a particular job. Nothing in
it is unusual, and that is deliberate: this is the standard move, written out
in full so that what it buys can be measured rather than assumed.

**The whole reason this solution exists is that it is one half of a matched
pair.** [Solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) is this model with no
training in this cell. This is the same model with training in this cell.
Everything else between the two is held still, and the list of what
"everything else" covers is the argument, so it is worth setting out one item
at a time. The [examiner](../02_the-examiner.md) holds the input still, so both
are shown the same rendered view of the same tables in the same order, with
the same instruction and the same joint readings, and the same measurements
reach the shared checks in both. It holds the output still, so both hand back a
chunk of jaw waypoints. It holds the marking still, so both are read off the
same scorecard, computed the same way. And these two solutions hold the
library, the model and the starting weights still, because they are the same
library, the same model and the same downloaded file.

One thing differs, which is the training. The section below asks whether
anything else does, because a matched pair invites exactly that mistake, and
the answer it reaches is that nothing else does. The model's output does stop
being numbers in the range the borrowed recordings used and becomes numbers in
the range this cell's own pushes use, but that is a property of the weights the
training changed rather than a second thing changed beside them, and the
convention by which those numbers are read as jaw waypoints is chosen once and
used by both. So **nothing varies between the two that the training did not
bring**, and the gap between solution 5 and this one is therefore a measurement
of what this training bought on a robot foundation model, and of nothing else.

That makes this pair the same question [telling the glasses apart in a
picture](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md) asks about a segmenter, asked one
level up. There the pair was a model that finds objects in pictures, borrowed
untouched against borrowed and fine-tuned, and the answer was about perception
alone. Here the model does not report what it sees; it decides what the arm
does next. So the question is no longer "does training help a model describe
this cell" but "does training help a model act in it", and the two answers do
not have to agree. A model can be fitted to a cell well enough to find every
glass in it and still be a poor chooser of pushes, because choosing a push
needs a sense of what a push does, and nothing in a picture contains that.

**Most of this is built, and the parts that are not are named where they
appear.** The solution lives in
[`06-smolvla-fine-tuned/`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned):
it records its demonstrations from the teacher, fits the correction, and has
been run by the examiner's held-out tables, with its numbers in
[its own README](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/README.md).
The two parts of the shared contract it waited on are in the examiner
now — a rendered view looking straight down in `bench/top_view.py`, and
`Bench.follow()`, which carries a chunk of waypoints out as an action — so
nothing below is blocked on them. Three things here are still prescriptions
rather than code, and each says so where it is described: **DAgger**, the
**second way on π0.5**, and the **several training seeds** the examiner asks for,
of which one was fitted. Everything else in this document describes a program
that has run.

**And the measured result is the uncomfortable one, so it belongs at the top
rather than only at the end: the fitting made the score worse.** The training
did what training is supposed to do, and the model learned the height at which
a push happens — its chunks come down to the height the gripper pushes at,
where the borrowed model's never came near the glasses. What it did not learn
is where to put the jaw down. So **259 of its 400 pushes a run are blocked on
the way down**, the jaw descending onto a glass instead of behind one, and from
there follow **46 toppled glasses a run** and 38 of the 50 tables marked
*wrong*, against solution 5's 6 toppled and 5 wrong. Nothing in this project
stands a glass back up, so on this scorecard a policy that never reaches a
glass scores better than one that reaches the wrong part of it. The last
section of this document reads that gap in full, and nothing between here and
there should be taken to promise otherwise.

By the end you will understand what fine-tuning is and why it is far cheaper
than fitting a model of this size from random numbers, what low-rank
adaptation is and what it trades away to fit in the memory it has to fit in,
where the demonstrations come from and why they are free while also capping
what this solution can ever be, which of solution 5's weaknesses the training
repairs and which of them survive it untouched, the two ways training on one
cell's pushes goes wrong, and why a markedly larger foundation model is a
second way here rather than the main line.

![The same chain as the borrowed model with a training step put in front: the teacher records its pushes, the failures are dropped, and a small correction is fitted so the chunks come out in this cell's own range, after which the shared geometry still refuses the glasses that tip before they slide.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-what-it-does.png)

![The borrowed weights stay as they are and a correction of about four million numbers is learned beside them, so only the correction carries gradients and the training fits on a laptop, and afterwards the correction folds into the weights so running it costs what running the original cost.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-the-correction.png)

## 2. The problem this solves

This book asks for a jaw trajectory, and then another, until every glass has
about 70 mm of clear room around it or the glasses that are left have been
refused with a reason. [The problem](../01_the-problem/01_what-is-asked-for.md) explains why that is hard,
and the hardest part of it is a missing number: whether a pushed glass slides
or tips depends on the friction between the glass and the table, **nothing in
the cell measures friction**, and the examiner never tells any solution what it
is using.

A learned policy answers that difficulty in the only way available to anything
here, which is by sampling outcomes rather than deriving them. It is shown
many pushes and what they did, and what it ends up holding is a sense of what
a push of this kind tends to produce on this table, friction included, without
any term in it standing for friction. Solution 5 already borrows a model built
that way, and borrows it from a very large collection of real robot motion, so
the general shape of that answer is available without fitting anything.

The question this solution exists to answer is therefore narrower and more
interesting than "does learning help". It is: **having borrowed a policy, what
is still wrong with it, and does training here fix that?**

Three things are still wrong in solution 5, and all three have one cause. The
model was fitted on 487 community datasets of real teleoperation — real
cameras, real rooms, real robots of other shapes — and this cell hands it a
view rendered by a simulator, of opaque glasses standing on a bare table, seen
straight down from above. First, the pictures are of a world the weights never
met, so what the model finds in them may have little to do with what is there.
Second, the numbers it produces are actions on the scale of the robots it was
fitted on, so whether they are the right size for this jaw on this table is
left to chance rather than fitted. Third, and underneath both, the model has
never seen the consequence of a push on this table, so whatever sense of
pushing it holds belongs to other tables.

Continuing the model's training on pushes made here is the standard repair for
all three at once, and that is what this solution does.

## 3. The main idea

The idea is one sentence long: keep the borrowed numbers, and learn a small
correction to them from pushes made on the examiner's tables.

Three things follow from that sentence, and most of this document is those
three things.

**The numbers do not start from nothing.** A model's weights are the numbers
inside it, and SmolVLA holds about 450 million of them. Fitting that many from
random values would mean teaching the model everything, down to the fact that
an edge in a picture is worth noticing and that a motion should be smooth. The
borrowed weights already hold all of that, so the training continues from them
rather than beginning beside them.

**The pushes are this examiner's pushes.** This is the part that makes the
difference to solution 5. Solution 5 asks a model fitted on real teleoperation
to act on a rendered view of a simulated table, which is a different kind of
input leading to a different kind of outcome. Fine-tuning does not ask that.
It shows the model this examiner's views and this examiner's pushes during training,
so at run time the model is being shown the kind of thing it was fitted on.
The difference between the two kinds of input is called the **domain gap**, and
fine-tuning is how a domain gap is closed.

**Only a small part of the model is actually changed.** Rather than moving all
450 million numbers, the training leaves every borrowed number where it is and
learns a small correction that is added alongside them. That technique is
called **low-rank adaptation**, it is what makes the training affordable, and
it has its own section below, because what it trades away matters to how the
pair's result should be read.

Everything else about the model is unchanged, including the things that limit
it. It still takes one instruction in words, and the task still has one
instruction, so that channel still carries nothing. It still takes the arm's
own pose, and the examiner parks the jaw between actions, so that channel carries
nothing either: the same six numbers go in at every ask. It still predicts a
chunk of waypoints and commits to the whole of it before looking again, because
the number of actions SmolVLA emits in a pass and the number it is configured
to carry out are the same fifty. And it still has no field in it for a rule, so
it still cannot be the thing that refuses a glass.

← [A foundation model as it downloads — how it compares](../08_a-foundation-model-as-it-downloads/06_how-it-compares.md) · [How it works](02_how-it-works.md) →
