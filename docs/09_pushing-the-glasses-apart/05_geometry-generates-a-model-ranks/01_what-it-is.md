# What it is

> **What it uses.** It uses NumPy for the geometry and scikit-learn for the
> one fitted part. The fitted part is a model of **two hundred
> gradient-boosted regression trees**. This is the standard tool for
> predicting one number from a short list of mixed quantities. There is no
> neural network in it, and it needs no accelerator.
> **What it does.** Plain geometry writes down every push that is safe and
> allowed. A fitted model then gives each of those pushes a score. The arm
> makes the push with the highest score.
> **How the output is produced.** `look()` gives the place and the widths of
> each glass. The geometry lists the safe pushes. The model scores each one.
> The best push goes to the examiner as a parameterised push, which is a push
> described by a few numbers. The examiner turns it into a movement of the jaw.
> **What it costs.** The labels are free, because the examiner measures the
> table after every push anyway. The training set is 4,844 pushes with their
> results, and it takes minutes of simulator time. scikit-learn and NumPy are
> both under the BSD 3-clause licence, so the licence costs nothing.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md).**
> That page gives the layout, the two camera positions (from the top and from
> the side), all four sensors, and the words this project uses. This page
> covers only what is special to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [A film of one table](#2-a-film-of-one-table)
3. [The problem this solves](#3-the-problem-this-solves)
4. [The main idea](#4-the-main-idea)

## 1. Introduction

This page explains a safe way to put a fitted model inside a machine that can
break things. It is for a reader who has read the problem chapter and wants to
see the simplest solution that learns anything.

The method has a name: **generate, veto, then rank**. It has three steps.

1. Arithmetic writes down every push that is allowed. This is the "generate"
   step.
2. Arithmetic removes every push that is not safe. This is the "veto" step. A
   veto is a refusal that nothing later can undo.
3. A fitted model puts the pushes that are left in order. This is the "rank"
   step. The arm makes the first push on the list.

The model cannot invent a push. It also cannot bring back a push that the
geometry removed. So **the worst a wrong model can do is waste one push**. It
cannot topple a glass, because the tipping test in [pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) runs before the
model is asked. Everything that could cause a failure that cannot be undone is
settled before the model sees anything. This matters a lot here, because
nothing in this project can stand a toppled glass up again.

The same idea is used in the camera book. There, a fitted model orders the
places to look from, in [looking again at what was
hidden](../../08_seeing-the-glasses/02_the-problem/02_looking-again-at-what-was-hidden.md).
The geometry removes the bad places first, for the same reason.

The main result comes first, because it is the finding. The fitted model does
**not** beat the plain printed rule, which takes the shortest push that
finishes the job. Both see the same pushes. They rack the same number of
glasses, but the model uses more pushes. [Where it is strong and where it
breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks) gives
the numbers and the reason.

This solution also matters for a second reason. It is the teacher for two
other solutions, which learn by copying its pushes. [It is the
teacher](03_how-it-works.md#7-it-is-the-teacher) explains what that gives them
and what it costs them.

![Geometry sweeps every heading and steps the travel out along each one, geometry then discards every candidate that cannot be reached, that clashes with a neighbour, that leaves the zone or that would tip the glass, and only the survivors are put in order by the fitted trees.](../../images/pushing-the-glasses-apart/geometry-generates-a-model-ranks/ranked-flow-what-it-does.png)

![Everything that could cause an unrecoverable failure is settled before the model is consulted, the model can never add a candidate or bring back one the geometry rejected, and deleting the model leaves a working system behind.](../../images/pushing-the-glasses-apart/geometry-generates-a-model-ranks/ranked-flow-where-the-model-sits.png)

The introduction said what the method does. The next section shows it working
on one table.

## 2. A film of one table

This film shows the method on one table in the simulator. It plays at one and a
half times real speed.

[Geometry generates and a model ranks, on one table, 13 seconds and no sound](https://docs.dodao.io/videos/pushing-the-glasses-apart/02-geometry-ranked.mp4 "video")

The table holds six glasses. The average table holds five. Five of the six
glasses have no room at the start.

In the film, this solution makes the same two pushes as the printed rule. It
racks the same one glass and refuses the same five. It gives slightly different
reasons for the refusals, but the table ends in the same state.

This is not luck. Ranking can only help when there is more than one good push to
choose from. On this table, the width and height of the hand rule out almost
every push. So the model and the rule choose from the same very short list, and
they choose the same push.

All six solutions are filmed on this same table, so you can compare the films.
[The six films](../10_the-results.md#3-the-six-films-all-of-the-same-table)
collects them and says how the table was chosen.

The film shows the method at work. The next section says which problem it is
meant to solve.

## 3. The problem this solves

The film showed the method choosing a push. This section says why choosing is
the problem.

[Pushing the glasses apart](../01_the-problem/01_what-is-asked-for.md) gives
the arm a table of four to six glasses. Some stand too close together for the
open jaw to fit round them. The arm must push them apart.

A push needs three decisions: which glass, which direction, and how far. The
geometry can find many safe pushes for one crowded glass. So the hard question
is not how to find a safe push. It is **how to choose among safe pushes**.

The problem is not safety. The geometry in this repository toppled only one
glass over the examiner's fifty held-out tables, as
`01-one-fixed-nudge/results.json` records. The problem is the number of pushes.
That run made **173 pushes, and 63 of them were repeat pushes of a glass it had
already moved**. A repeat push means the first push did not do its job. A
better choice among the same pushes should need fewer of them. That is the gap
a ranker aims at.

One number in that file is out of this solution's reach. **53 of the 251
glasses were refused because there was nowhere clear to push them.** That is a
lack of pushes, not a bad order of pushes. Ranking an empty list still gives an
empty list. So this solution cannot help with those glasses.

The problem is now clear. The next section gives the idea that answers it.

## 4. The main idea

The previous section said the task is to choose among safe pushes. The idea is
one sentence: ask the geometry for **every** safe push, and let a fitted model
put them in order.

Three things follow from this.

First, **every test that can reject a push is arithmetic.** The tests check
reach, the paths of the glass and the jaw, the glass zone, the rack and
tipping. They all run before the model, as [the
introduction](#1-introduction) explains.

Second, **the model only gives an order.** It gives one number for each push,
and the pushes are sorted by that number. Nothing else reads the number. So the
model does not need to predict the result correctly. It only needs to put the
pushes in the right order.

Third, **without the model, you still have a working system.** Delete the model
and keep the printed rule, and you get the geometry in
`src/09_pushing-the-glasses-apart/01-one-fixed-nudge` exactly. So you can try
this solution and drop it at no cost.

The obvious alternative is a model that chooses the push directly. It reads the
table and outputs a direction and a distance. That model can output **any push
at all, safe or not**. So a safety check must be added after it, and that check
does the same work as the geometry here. Solutions 3, 5 and 6 work this way.
[Solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) uses a
fitted model of what a push will do to judge safety. Those designs are not
wrong. A model that chooses the push can make pushes that the geometry never
lists. This solution makes the opposite choice: it gives up those pushes to
keep safety in the arithmetic.

![The enumerator writes down every push, the filter keeps only the safe ones, and the model reorders what is left, so nothing it can emit is unsafe; a model that chooses the push instead has every push in its output space and needs a geometric check bolted on after it.](../../images/pushing-the-glasses-apart/geometry-generates-a-model-ranks/06-generate-veto-then-rank.png)

The next page, [the code](02_the-code.md), shows how this idea is written.

← [One fixed nudge — how it compares](../04_one-fixed-nudge/06_how-it-compares.md) · [How it works](03_how-it-works.md) →
