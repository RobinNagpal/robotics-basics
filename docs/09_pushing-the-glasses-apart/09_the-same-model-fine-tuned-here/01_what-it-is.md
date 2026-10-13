# What it is

> **What it uses** — LeRobot, with PyTorch underneath, and this machine's own
> Metal GPU for the training run, which is further than this document expected
> a 450-million-parameter fine-tune to go. The model is SmolVLA: the same
> library, the same model and the same downloaded weights as [solution
> 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md), with its
> training continued by low-rank adaptation on pushes made on the examiner's
> tables.
> **What it does** — a model that arrives fitted to real teleoperation of
> other robots is neither thrown away nor used as it arrives. Its numbers are
> kept, and a small correction to them is learned from pushes made on this
> examiner, so that it stops being a general copier of robot motion and becomes
> a pusher of glasses on this table. The action chunks it then emits are this
> solution's answer to the problem this book sets.
> **How the output is produced** — a rendered view of the table from the top
> goes in, together with one instruction in plain English and the arm's own
> pose, which is the same every time because the jaw is parked between
> actions. The corrected model returns an **action chunk**: a short run of
> consecutive jaw waypoints predicted together in one pass. The shared
> geometry refuses the glasses that tip before they slide, and a chunk whose
> path would reach one of those is not carried out. The examiner then carries
> the waypoints out directly, because a chunk needs no expansion. The arm looks
> again, and the loop repeats until the table is done or the push budget is
> spent.
> **What it costs** — the demonstrations are free, because solution 2
> generates them and the examiner executes them without anybody holding a
> controller. The training is a low-rank fine-tune and it fits in 1.02 GiB on a
> laptop, so nothing was rented; hours of a small rented accelerator, of order
> tens of dollars, is what it would take to spend real compute on it. Running
> it costs one large forward pass per chunk, the same as its partner's, so the
> two cost the same to run and differ only in what it cost to build them. The
> licence is not the obstacle it was for [the pair that tells the glasses
> apart](../../08_seeing-the-glasses/08_the-same-model-fine-tuned/04_results-and-comparison.md#4-what-it-costs),
> but a fine-tuned file inherits whatever terms the borrowed file carried, so
> the terms have to be read before anything leaves this project.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [A film of one table](#2-a-film-of-one-table)
3. [The problem this solves](#3-the-problem-this-solves)
4. [The main idea](#4-the-main-idea)

## 1. Introduction

This document explains how to answer [the problem this book
sets](../01_the-problem/01_what-is-asked-for.md) by taking a robot foundation
model that was already fitted elsewhere and continuing its training on pushes
made in this cell. The method has a name, **fine-tuning**, and it is the
ordinary way a borrowed model is put to work on a particular job. Nothing in
it is unusual, and that is deliberate: this is the standard move, written out
in full so that what it buys can be measured rather than assumed.

**The whole reason this solution exists is that it is one half of a matched
pair.** [Solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md)
is this model with no training in this cell. This is the same model with
training in this cell. The [examiner](../01_the-problem/03_the-examiner.md) holds everything
else still — the same tables in the same order, the same instruction, the same
joint readings, the same shared checks, the same output of jaw waypoints and
the same scorecard — and the two solutions use the same library, the same model
and the same downloaded file. One thing differs, which is the training.
[Whether anything else does](03_how-it-works.md#4-whether-anything-but-the-training-differs)
is a question a matched pair invites, and the answer worked out there is that
nothing else does. So the gap between solution 5 and this one is a measurement
of what this training bought on a robot foundation model, and of nothing else.

That makes this pair the same question [telling the glasses apart in a
picture](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
asks about a segmenter, asked one level up. There the pair was a model that
finds objects in pictures, borrowed untouched against borrowed and fine-tuned,
and the answer was about perception alone. Here the model does not report what
it sees; it decides what the arm does next. So the question is no longer "does
training help a model describe this cell" but "does training help a model act
in it", and the two answers do not have to agree. A model can be fitted to a
cell well enough to find every glass in it and still be a poor chooser of
pushes, because choosing a push needs a sense of what a push does, and nothing
in a picture contains that.

**Most of this is built, and the parts that are not are named where they
appear.** The solution lives in
[`06-smolvla-fine-tuned/`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned):
it records its demonstrations from the teacher, fits the correction, and has
been run by the examiner's held-out tables, with its numbers in
[its own README](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/README.md).
The two parts of the shared contract it waited on are in the examiner
now — a rendered view looking straight down in `bench/top_view.py`, and
`Bench.follow()`, which carries a chunk of waypoints out as an action. Three
things here are still prescriptions rather than code, and each says so where it
is described: **DAgger**, the **second way on π0.5**, and the **several
training seeds** the examiner asks for, of which one was fitted.

**And the measured result is the uncomfortable one, so it belongs at the top
rather than only at the end: the fitting made the score worse.** The training
did what training is supposed to do, and the model learned the height at which
a push happens — its chunks come down to the height the gripper pushes at,
where the borrowed model's never came near the glasses. What it did not learn
is where to put the jaw down. So **about two pushes in three are blocked on
the way down**, the jaw descending onto a glass instead of behind one: over
three evaluation runs that is 223 of 369 pushes, then 227 of 351, then 240 of
374. From there follow **40 toppled glasses a run** and 36 of the 50 tables
marked *wrong*, against solution 5's 12 toppled and 9 wrong. Nothing in this
project stands a glass back up, so on this scorecard a policy that never
reaches a glass scores better than one that reaches the wrong part of it. [How
it compares](06_how-it-compares.md#3-where-it-sits-among-the-other-five) reads
that gap in full, and nothing between here and there should be taken to promise
otherwise.

By the end you will understand what fine-tuning is, what low-rank adaptation
trades away to fit in the memory it has to fit in, where the demonstrations
come from and why being free also caps what this solution can ever be, and
which of solution 5's weaknesses the training repairs and which survive it
untouched.

![The same chain as the borrowed model with a training step put in front: the teacher records its pushes, the failures are dropped, and a small correction is fitted so the chunks come out in this cell's own range, after which the shared geometry still refuses the glasses that tip before they slide.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-what-it-does.png)

![The borrowed weights stay as they are and a correction of about four million numbers is learned beside them, so only the correction carries gradients and the training fits on a laptop, and afterwards the correction folds into the weights so running it costs what running the original cost.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-the-correction.png)

## 2. A film of one table

The introduction described what was done to the borrowed model's numbers and why,
and the film here shows the corrected model on one table in the simulator,
played at one and a half times real speed.

[The same borrowed model after fine-tuning here, on one table, 12 seconds and no sound](https://docs.dodao.io/videos/pushing-the-glasses-apart/06-smolvla-fine-tuned.mp4 "video")

The table holds six glasses where the average is five, and five of those six
have no room at the start, which is the usual state of these tables.

In the film the jaw comes down to the right height, which is what the
fine-tuning bought, and it comes down **onto** a glass, which is what the
fine-tuning did not fix. Four pushes are made, one glass is racked, one is
knocked over, and the table is therefore marked **wrong**. That is this
solution's commonest outcome: 36 of its fifty tables end the same way.

Competence enough to reach the glasses and not enough to miss them is worse
here than not reaching them at all, because a glass on its side is the one
failure this cell cannot undo. The film and the one before it are the clearest
statement of that in the book: the borrowed model never touches anything, and
fitting it made it dangerous rather than useful.

This solution draws its answer rather than computing it, so the film is one
draw rather than an average. The scored runs on this table all ended wrong and
averaged six pushes and two glasses racked, against the film's four pushes and
one glass, so the film is a shorter draw than the middle one. Which draw a film
shows is not a detail here, and [the
examiner](../01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why: a table filmed on its own is not the same table reached part-way
through a run, because the tables before it have already moved the policy's
random numbers along.

Two details are the same in all six films: the hand never opens while it is
pushing, and the pick-up at the end of a take is drawn rather than simulated.
[The film of the
job](../01_the-problem/01_what-is-asked-for.md#2-a-film-of-the-job) explains
both of them, and it is worth reading once before watching any of the six.

Every one of the six solutions is filmed on this same table, number 10025 of
the fifty the examiner holds back, so the six films can be watched against each
other. The table was chosen to be **typical rather than flattering**, by a rule
written down before it was applied: every one of the six had to reach its own
commonest outcome there and rack at least one glass, and exactly one table of
the fifty does both. Choosing that way needed [one row per
table](../01_the-problem/03_the-examiner.md#5-what-the-examiner-measures) in the
scorecard, because a total over fifty tables cannot say which single table
stands for the rest. All six films are collected in [the six solutions side by
side](../10_the-results.md).

## 3. The problem this solves

This book asks for a jaw trajectory, and then another, until every glass has
about 76 mm of clear room around it or the glasses that are left have been
refused with a reason. [The problem](../01_the-problem/01_what-is-asked-for.md)
explains why that is hard, and the hardest part of it is a missing number:
whether a pushed glass slides or tips depends on the friction between the glass
and the table, **nothing in the cell measures friction**, and the examiner never
tells any solution what it is using.

A learned policy answers that difficulty in the only way available to anything
here, which is by sampling outcomes rather than deriving them. It is shown many
pushes and what they did, and what it ends up holding is a sense of what a push
of this kind tends to produce on this table, friction included, without any
term in it standing for friction. Solution 5 already borrows a model built that
way, from a very large collection of real robot motion.

The question this solution exists to answer is therefore narrower and more
interesting than "does learning help". It is: **having borrowed a policy, what
is still wrong with it, and does training here fix that?**

Three things are still wrong in solution 5, and all three have one cause. The
model was fitted on 487 community datasets of real teleoperation — real
cameras, real rooms, real robots of other shapes — and this cell hands it a
view rendered by a simulator, of opaque glasses standing on a bare table, seen
straight down from above. The pictures are of a world the weights never met.
The numbers it produces are actions on the scale of the robots it was fitted
on, so whether they are the right size for this jaw is left to chance. And
underneath both, it has never seen the consequence of a push on this table.
Continuing its training on pushes made here is the standard repair for all
three at once.

## 4. The main idea

The idea is one sentence long: keep the borrowed numbers, and learn a small
correction to them from pushes made on the examiner's tables.

Three things follow from that sentence, and most of this document is those
three things.

**The numbers do not start from nothing.** A model's weights are the numbers
inside it, and SmolVLA holds about 450 million of them. Fitting that many from
random values would mean teaching the model everything, down to the fact that
an edge in a picture is worth noticing and that a motion should be smooth. The
borrowed weights already hold all of that, so the training continues from them.

**The pushes are this examiner's pushes.** This is the part that makes the
difference to solution 5. Solution 5 asks a model fitted on real teleoperation
to act on a rendered view of a simulated table, which is a different kind of
input leading to a different kind of outcome. Fine-tuning does not ask that: it
shows the model this examiner's views and this examiner's pushes during
training, so at run time the model is being shown the kind of thing it was
fitted on. The difference between the two kinds of input is called the **domain
gap**, and fine-tuning is how a domain gap is closed.

**Only a small part of the model is actually changed.** Rather than moving all
450 million numbers, the training leaves every borrowed number where it is and
learns a small correction that is added alongside them. That technique is
called **low-rank adaptation**, it is what makes the training affordable, and
what it trades away matters to how the pair's result should be read.

Everything else about the model is unchanged, including the things that limit
it. It still takes one instruction in words, and the task still has one
instruction, so that channel carries nothing. It still takes the arm's own
pose, and the examiner parks the jaw between actions, so the same six numbers
go in at every ask. It still predicts a chunk of fifty waypoints and commits to
the whole of it before looking again. And it still has no field in it for a
rule, so it still cannot be the thing that refuses a glass.

← [A foundation model as it downloads — how it compares](../08_a-foundation-model-as-it-downloads/06_how-it-compares.md) · [How it works](03_how-it-works.md) →
