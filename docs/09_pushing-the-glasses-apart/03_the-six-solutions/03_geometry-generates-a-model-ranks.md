# Geometry generates, a model ranks

This page describes the second of the six solutions in about eight minutes of
reading. It is the one that lets a fitted model choose but never decide: plain
geometry writes down every push that is safe, and a small fitted model only puts
those candidates in order. By the end of this page you will know why the learned
part is placed where it is, what it scored on the shared examiner, why it lost
to the printed rule it was meant to improve, and why it is still the most useful
of the six to understand. The full treatment is in [the chapter on this
solution](../05_geometry-generates-a-model-ranks/01_what-it-is.md), which is
about an hour of reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

[One fixed nudge](02_one-fixed-nudge.md) computes a single answer and carries it
out. This solution does the opposite: it writes down *every* answer that is
legal, which is usually a large set rather than one push, and then something has
to choose one of them.

The choosing is where the fitted model goes, and the placement is the whole
idea. The model gives each surviving candidate one score, the candidates are
sorted by that score, and the arm makes the first push on the sorted list. **The
model can never add a push to the list and never bring back one the geometry
rejected.** So it decides the order of the attempts and nothing about whether an
attempt is safe.

That matters because of what this cell cannot undo. A toppled glass cannot be
stood back up, and in a cell whose one unrecoverable failure is a toppled glass,
keeping every safety decision in arithmetic that a person wrote is the property
worth designing around. Here the worst a badly fitted model can do is waste a
push.

The model itself is a set of **gradient-boosted regression trees**, of order two
hundred trees, which is the standard tool for predicting a number from a short
list of quantities of different kinds. There is no neural network anywhere in
it, and no accelerator is needed to train it.

## 2. How it works

The work happens in three stages, and only the last one is fitted.

**The geometry proposes.** It sweeps every heading around each crowded glass and
steps the travel out along each heading, which produces a large set of candidate
pushes described by where to start, which way and how far.

**The geometry filters, before the model is consulted at all.** A candidate
survives only if the arm can reach it, if the push drags the glass and swings
the jaw clear of every neighbour, if the glass lands inside the glass zone, and
if the jaw touches the glass below the height at which it would tip over instead
of sliding. Everything that could cause an unrecoverable failure is settled
here.

**The model ranks what survived.** Each surviving candidate is described by a
short list of lengths, angles, counts and ratios, the model turns that list into
one number, and the highest-scoring candidate is handed to the examiner as a
parameterised push. The examiner's macro expands it into the jaw trajectory, the
same one every solution here is judged on.

Training it costs almost nothing. The examiner measures the table after every push
in any case, so the label — how much room a push actually gained — is free. A
few thousand pairs of a candidate and what happened to it are collected on the
training half of the tables, which is minutes of examiner time with no human
labelling at all, and the trees then fit in seconds to minutes on an ordinary
processor.

One more thing this solution produces matters to the book as a whole. Its scored
candidates are recorded pushes, so **it is the teacher**: [imitation from
demonstrations](04_imitation-from-demonstrations.md) and [the same model,
fine-tuned here](07_the-same-model-fine-tuned-here.md) both learn by copying
what this solution did.

## 3. What it needs

It needs **scikit-learn and NumPy**, both small, both pure software and both
under the three-clause Berkeley Software Distribution licence, so no licence
condition is carried anywhere.

It needs the **enumerator**, which is shared with solution 1 rather than copied,
so the heading sweep, the stepped travel, the four tests and the tipping rule
have one definition in this repository. That shared part is also what sets the
ceiling on how good this solution can be, because the model cannot invent a
candidate the enumerator did not produce.

It needs a **training set** of a few thousand candidate-and-outcome pairs,
generated and executed on the training half of the examiner's tables, and the
**held-out half** for marking, which the examiner enforces by splitting its table
numbers.

It needs **no accelerator**, and this is the clearest cost difference between
this solution and the four that follow it. At run time each tree is three levels
deep, so it asks three threshold questions, and with two hundred trees that is
six hundred comparisons in all and no matrix multiplication anywhere. Even a
candidate set in the thousands costs a small fraction of the seconds one arm
movement takes.

Once fitted it needs **a model file kept in step with the cell.** Change the
heading sweep, the step length, the glass zone or the way the examiner draws its
crowded tables, and the fitted model quietly describes a cell that no longer
exists, in a way no test of the code would notice.

## 4. What it scored

All six solutions are given the same 50 tables holding 251 glasses, of which 193
have no room at the start. The second row below is this solution with its model
deleted, so that the printed rule inside it picks instead, which is the
comparison this solution exists to make.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| the fitted ranker | 31 | **0** | 185 | **0** | 229 |
| the same loop, printed rule picking | 33 | **0** | 195 | **0** | 213 |

**The ranker lost to the rule it was meant to improve**, on both tables finished
and glasses racked, and using more pushes to do it. That is the finding of this
solution, and it was measured rather than guessed: both rows ran the same loop
over the same held-out tables with the same budget and the same candidate set,
and the only difference was who picks.

It is not an unlucky fit, because three rankers fitted on resamples of the same
rows racked 180, 181 and 184. **The reason is the label.** The model is fitted on
*room gained* and the run is marked on *glasses that end up grippable*, and a
push that spreads a little room over three glasses scores higher than one that
finishes a single glass outright. By its own label the ranker is the better
chooser — it gives up 4.4 mm of room against the best available candidate where
the rule gives up 18.7 mm — and it still clears fewer tables.

There is a second reason the ordering could not help much, and it was also
measured. Within one glass's job-finishing candidates the room gained ranges
0.0 mm at the median over 161 groups, which is an exact tie, so in precisely the
part of the candidate set where the task is being finished there is nothing for
an ordering to tell apart. What the fit says mattered points the same way: the
topple ratio and the foot width came first and the push distance last, so the
model mostly learned which glass is risky to push rather than which push is
good. The verdict is to keep the simpler one. The full table for all six
solutions is in [the results](../10_the-results.md).

## 5. Where it is strong and where it breaks

**The learned part cannot cause the failure that cannot be undone.** Toppling,
leaving the glass zone, leaving the arm's reach and striking the rack are all
settled before the model is consulted, and the zero in the toppled column is
what that looks like when it holds.

**It degrades to something that works.** Delete the model and the printed rule
runs the table, so there is no state in which this solution is broken rather
than merely unimproved.

**It is checkable.** Every candidate can be printed with its score, every
refusal remains the geometry's and prints with a reason, and the model reports
which of its inputs mattered.

**It is cheap in every currency**, and **it is the teacher**, which is the
contribution that survives even though its own score is unremarkable.

Against that, three kinds of weakness.

**What the design cannot do.** It cannot invent a candidate, so its quality is
the enumerator's quality rather than the model's. It cannot express a push that
is not a straight drag along one heading. And it says nothing at all about the
commonest refusal in the record, which is a glass with nowhere clear to go.

**What it cannot survive.** A log collected while the model is driving holds
outcomes only for the candidates the model already prefers, so retraining on it
without occasionally taking the second-ranked candidate locks in an early
mistake. And every label in the training set was decided by the examiner's private
friction, which was never measured against anything real.

**How it fails is quietly.** A badly fitted ranker orders the candidates roughly
at random. Nothing errors, nothing topples, and the run simply spends more
pushes and leaves more glasses behind than it needed to. That is exactly how it
failed here, and the only reason it was caught is that somebody ran the test
with the model deleted and everything else held the same.

## 6. When to choose it

Choose this arrangement — geometry proposes, a model only orders — whenever one
kind of failure cannot be undone. It is the right shape for any cell where a
mistake breaks something, because the model's worst case is a wasted attempt
rather than a broken object, and because deleting the model leaves a working
system behind. That property is worth more than the score it earned here.

Do not fit the ranker before checking that the ordering carries information.
That is the lesson this solution paid for. Two cheap measurements would have
predicted the outcome: how much the candidates differ in the outcome you care
about, and whether the label you can measure is the thing you are marked on.
Here the candidates were tied and the label was the wrong quantity, and the
model could not have helped however well it was fitted.

The most useful comparison in the book runs between this solution and [a world
model, then plan with it](05_a-world-model-then-plan-with-it.md), and it is
about *which question deserved a model*. This solution fits a model of **how
much a push would help**, which is a quantity the geometry already computes
exactly. That solution fits a model of **what a push will actually do**, which
is the quantity the geometry gets wrong, because predicting where a pushed glass
stops needs the friction nobody here has measured. On the same tables it racked
202 glasses in 114 pushes, against 185 in 229 for the fitted ranker and 195 in
213 for the printed rule. **The learning that paid attacked the quantity the
geometry gets wrong, not the quantity it gets right.** It cost one toppled
glass to do it, which neither row above ever does, so the two approaches are not
ordered on a single number.

The code is in
[`src/09_pushing-the-glasses-apart/02-geometry-ranked/`](../../../code/src/09_pushing-the-glasses-apart/02-geometry-ranked)
and it writes its own `results.json` beside itself. The full treatment, with
what the geometry proposes, what the filter removes, how the trees are trained
and why the placement of the learned part is what makes it safe, starts at [what
it is](../05_geometry-generates-a-model-ranks/01_what-it-is.md).

← [One fixed nudge](02_one-fixed-nudge.md) · [Imitation from demonstrations](04_imitation-from-demonstrations.md) →
