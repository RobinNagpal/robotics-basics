# What it is

> **What it uses** — NumPy for the geometry, and scikit-learn for the one
> fitted part. The model is a set of **gradient-boosted regression trees**, of
> order two hundred trees, which is the standard tool for predicting a number
> from a short list of quantities of different kinds. There is no neural
> network anywhere in it and no accelerator is needed to train it.
> **What it does** — plain geometry writes down every push that is legal, which
> means every push that the arm can reach, that drags the glass and swings the
> jaw clear of every neighbour, that lands inside the glass zone, and that
> touches the glass below the height at which it would tip over instead of
> sliding. That is usually a large set rather than a single answer, so
> something has to choose one of them. The fitted model does that and only
> that: it gives each surviving candidate one score, the candidates are sorted
> by it, and the arm makes the first push on the sorted list. The model can
> never add a push to the list and never bring back one the geometry rejected,
> so it decides the order of the attempts and nothing about whether an attempt
> is safe.
> **How the output is produced** — `look()` hands over where each glass stands
> and how wide it is at its widest and at its foot. The geometry sweeps every
> heading round each crowded glass, steps the travel out along each heading,
> applies its tests, and keeps what survives. Each survivor is described by a
> short list of lengths, angles, counts and ratios, and the model turns that
> list into one number. The highest-scoring push is handed to the examiner as a
> parameterised push, and the examiner's own macro expands it into the jaw
> trajectory that every solution here is judged on.
> **What it costs** — the labels are free, because the examiner measures the table
> after every push in any case. The training set is a few thousand pairs of a
> candidate and what happened to it, which is minutes of examiner time, because a
> push in MuJoCo is cheap. Training a few hundred shallow trees on a table of a
> few thousand rows takes seconds to minutes on an ordinary processor, so there
> is no accelerator to rent and the running cost per push is arithmetic.
> scikit-learn and NumPy are both BSD 3-clause, so the licence costs nothing
> either.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document explains the safest way there is to put a fitted model inside a
machine that can break something, and then says honestly what that particular
model is worth on these particular tables.

The arrangement has a name worth learning, because it recurs wherever learning
meets hardware: **generate, veto, then rank**. Arithmetic writes down every
action that is allowed. Arithmetic then rejects the ones that are not. A model
that has been fitted to data is handed whatever survives, and its only job is
to put that list in order. The arm makes the first push on the list. The model
cannot invent a push and cannot overturn a rejection, so **the worst a wrong
prediction can do is waste one attempt**. In a cell where a toppled glass
cannot be stood back up by anything in this project, that property is worth a
great deal.

All of this is now written, and the result is worth stating before anything
else, because it is the finding rather than a footnote. The candidate
generation exists:
`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py` sweeps the
headings, steps the travel out, applies the tests and returns every push that
survives. The printed rule that takes the shortest push which finishes the job
exists beside it. And the trees described below — their inputs, the number they
predict, the training set and the labelling — are built too, in
`src/09_pushing-the-glasses-apart/02-geometry-ranked`, fitted, and run over the
same fifty held-out tables as the rule, with the model deleted, so that both
sides see exactly the same candidates and the only difference between the two
runs is who picks. **The ranker loses that comparison.** It racked 185 of the
251 glasses in 229 pushes where the printed rule racked 195 in 213, finishing
two fewer tables and toppling nothing either way. The ablation is in
`src/09_pushing-the-glasses-apart/02-geometry-ranked`: `results.json` is the
ranker's run and `rule.json` is the rule's. Why it loses is explained in [where
it is strong and where it breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks), and
the short answer is that the model is fitted on room gained while the run is
scored on glasses racked, and those are not the same quantity.

By the end of this document you will understand what a decision tree is and
what boosting a set of them means, why a handful of geometric quantities suits
trees better than it suits a network, why every input is a length, a count or
a ratio and never an address on the table, how the training set is collected
and labelled for nothing, and two things about this solution that matter more
than wherever it lands on the scorecard.

Those two things are worth stating in the introduction, because they are the
reason to read the rest.

**The first is where the learned part sits.** Geometry generates every
candidate and refuses the unsafe ones, and the model only orders what survives.
So a wrong answer costs one wasted push and nothing worse. It cannot topple a
glass, because the topple limit described in [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) is a refusal
applied before the model is consulted at all. That is the same position the
learned ranker in [looking again at what was
hidden](../../08_seeing-the-glasses/02_the-problem/02_looking-again-at-what-was-hidden.md)
occupies, for the same reason, and the parallel is drawn out below.

**The second is that this solution is the teacher.** Solutions 3 and 6 learn
from demonstrations, and a solution that generates safe pushes geometrically
and ranks them supplies those demonstrations for nothing. That is the largest
single thing this solution contributes, and it comes with an honest cost: the
two solutions that learn from it inherit its ceiling, and keeping only the
demonstrations that succeeded trains them on a biased sample of what this
solution happens to do well.

## 2. The problem this solves

[Pushing the glasses apart](../01_the-problem/01_what-is-asked-for.md) hands
the arm a table with four to six glasses on it, some standing too close
together for the open jaw to fit round one without fouling its neighbour. The
arm has to drag them apart, because it may not lift them: lifting needs a
measured profile, measuring needs a clear view from the side, and a clear view
from the side is exactly what the crowding has taken away.

A push therefore needs three things decided — which glass to move, in which
direction, and how far — and the honest difficulty is that the first attempt
at this produces far too many answers rather than too few. Sweep the headings
round one crowded glass and step the travel out along each of them, and a large
number of those pushes turn out to be perfectly legal. So the problem this
solution addresses is not how to find a safe push. It is **how to choose among
safe pushes**, which is a different question and a smaller one.

The complaint it is aimed at is therefore not safety. The geometry already in
this repository toppled nothing at all over the examiner's fifty held-out tables,
as its results file records. The complaint is the number of attempts: that run
spent **213 pushes on 251 glasses, and 90 of those were repeat pushes of a
glass it had already moved once**. A repeat push is a push that did not achieve
what it was chosen for, so a method that chose better among the same candidates
would spend fewer of them. That is the gap a ranker is pointed at.

It is worth naming the other number in that same results file, because this
solution does not touch it. **56 of the 251 glasses were refused for having
nowhere clear to push them to.** That is a shortage of candidates rather than a
bad ordering of them, and a ranking over an empty set is still empty. So
whatever this solution is worth, it is worth nothing at all against the largest
single failure in that record.

## 3. The main idea

The idea is one sentence long: ask the geometry for **every** safe push rather
than for the best one, and let a fitted model put the survivors in order.

Three things follow from that sentence, and they are the shape of the whole
solution.

**Everything that can reject a push is arithmetic.** Reach, the swept paths of
the glass and of the jaw, the glass zone, the rack and the topple limit are all
tests, they all run before the model, and each of them can remove a candidate
outright. None of them consults the model, so the model has no way to make an
unsafe push available.

**The model's entire output is an ordering.** It produces one number per
candidate, the candidates are sorted by that number, and nothing downstream
reads the number itself. A model that was wrong by the same amount on every
candidate would still order them perfectly, which is a much weaker thing to ask
of a fitted function than predicting the outcome correctly.

**The method degrades to what already exists.** Delete the fitted model, keep
the printed rule that takes the shortest job-finishing push, and the run is the
geometry in `src/09_pushing-the-glasses-apart/01-one-fixed-nudge` exactly. So
this solution extends that code rather than replacing it, and it can be tried
and then abandoned at no cost.

The contrast that makes the arrangement worth understanding is with the obvious
alternative, which is to let a model choose the push directly. Such a model
reads the arrangement and emits a heading and a distance, so **its output space
is every push there is, safe or unsafe**. Nothing in the shape of the model
says which of the two it just produced, so a geometric check has to be placed
after it, and once that check is there it is doing the same safety work the
geometry does here, for a model that is far harder to fit. Solutions 3 to 6 are
all of that kind, and they are not wrong to be: a model that chooses the push
can express pushes the enumerator never offers. The point of this solution is
the opposite trade, and the next sections are the two halves of it.

![The enumerator writes down every push, the filter keeps only the safe ones, and the model reorders what is left, so nothing it can emit is unsafe; a model that chooses the push instead has every push in its output space and needs a geometric check bolted on after it.](../../images/pushing-the-glasses-apart/geometry-generates-a-model-ranks/06-generate-veto-then-rank.png)

← [One fixed nudge — how it compares](../04_one-fixed-nudge/06_how-it-compares.md) · [How it works](02_how-it-works.md) →
