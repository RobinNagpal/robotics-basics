# How it works

This page explains what happens inside this solution, part by part. It follows
[the code](02_the-code.md), and explains what each part of that code is doing.

## Contents

1. [Open loop and closed loop](#1-open-loop-and-closed-loop)
2. [The shortfall, and why it is measured to the neighbour's edge](#2-the-shortfall-and-why-it-is-measured-to-the-neighbours-edge)
3. [Why the push is a fraction of the shortfall rather than all of it](#3-why-the-push-is-a-fraction-of-the-shortfall-rather-than-all-of-it)
4. [Why repeating replaces predicting](#4-why-repeating-replaces-predicting)
5. [What is built and what is a design](#5-what-is-built-and-what-is-a-design)
6. [It produces nothing anybody can learn from](#6-it-produces-nothing-anybody-can-learn-from)

## 1. Open loop and closed loop

The four decisions in [the main idea](01_what-it-is.md#4-the-main-idea) are
small. What makes them enough is the loop around them. This section names that
loop, because the rest of the page uses the name.

An **open loop** plan is worked out once and then carried out without checking
anything. A **closed loop** plan measures, acts, and measures again. The new
measurement changes what it does next.
[The loop: plan, feel, look again](../01_the-problem/05_pushing-without-toppling.md#5-the-loop-plan-feel-look-again)
explains the difference for every solution.

A closed loop has three parts. The **measurement** says how things are. The
**error** says how far that is from how things should be. The **correction**
tries to make the error smaller.

In this solution the measurement is `look()`, which the examiner provides. The
error is the shortfall, which the next section defines. The correction is the
nudge. The share that turns the error into the nudge is called the **gain**. A
correction that is the error times a fixed gain is called a **proportional
controller**. That is all the cleverness in this method.

Newton's method for finding roots works the same way. Nobody has a formula for
the answer. But you can measure how wrong the current guess is, and you have a
rule that makes it less wrong. Here, nobody can say where a glass will stop.
But anybody can measure how much room it is missing. And the rule that makes
that smaller is to push it away from the glass that crowds it.

Every solution runs inside a loop like this. In the other six, the loop
holds something large, such as a model. Here, **the loop is the method**. There
is nothing else inside it.

The loop needs an error to work on. The next section defines it.

## 2. The shortfall, and why it is measured to the neighbour's edge

The loop in the last section needs an error. This section defines it. The open
gripper needs 76 mm of clear room from a glass's middle to every neighbour's
edge. [The gap that matters](../01_the-problem/01_what-is-asked-for.md#6-the-gap-that-matters-is-not-the-gap-between-the-glasses)
explains where 76 mm comes from. Because it is measured to the neighbour's
**edge**, what a glass needs depends on how wide the neighbour is, not on its
own width. So a narrow glass beside a wide one can be short of room, while the
wide one has room at the same distance.

![The same pair of glasses from the top at four separations, showing that the wide one comes free before the narrow one does: each glass carries the 76 mm ring the open jaw needs, and a glass is blocked while its neighbour's edge is inside that ring, so the narrow glass, whose neighbour's edge reaches further in, is still blocked at a distance where the wide one already has its room.](../../images/pushing-the-glasses-apart/one-fixed-nudge/01-four-distances-one-pair.png)

The shortfall of one glass against one neighbour is

    76 mm  +  half the neighbour's widest width  −  the distance between
    their middles

It is zero or less when that neighbour is not in the way. A glass's own
shortfall is the largest of these values over all the other glasses. The
neighbour that gives the largest value is the one whose edge is nearest. So
**the blocking neighbour and the deepest intruder are the same glass**. The
method needs no extra rule to find it.

The picture below draws the shortfall as one length on the table.

![The crowded glass with the 76 mm ring the open jaw needs round it, the neighbour's rim reaching inside that ring, and the overlap marked: the shortfall is how far the neighbour's edge comes inside the ring, which is the same thing as 76 mm plus half the neighbour's width minus the distance between the two middles.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-error.png)

Two points follow.

**The test is on an ordered pair rather than on a pair.** Glass A may be
crowded by glass B while B is not crowded by A. So the method checks the
shortfall in both directions for every pair. A method that only compares the
distance between middles can miss a glass that cannot be gripped.

**The shortfall is already in the repository.** The function `shortfall()` in
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py)
computes the expression above. It adds it up over the whole table to measure
how crowded the table is. This solution uses the same number for one glass at
a time.

Now the error is defined. The next section asks how big a correction to make
from it.

## 3. Why the push is a fraction of the shortfall rather than all of it

The last section defined the error. This section decides how much of it to
correct in one push. This is where the unknown friction shapes the design.

Call the shortfall `s`, and call the gain `k`. The jaw is told to push `k · s`.
The glass really moves some other distance. The jaw may slip on a curved wall.
The glass may turn. The friction may not be the same all over its foot. The
glass may slide on after the jaw stops, or stop early. Write all of this as one
unknown factor `g`, so the glass moves `g · k · s`. **Nothing in the cell
measures `g`, and nothing keeps it in a narrow range.** It depends on the
friction, and the friction could differ by more than two times.

The shortfall after the push is

    s'  =  s − g · k · s  =  s · (1 − g · k)

So the shortfall gets smaller whenever `g · k` is between zero and two. That
one condition is the whole argument for a small gain.

**A large gain is risky.** Set `k` to one, to close the whole gap at once. Then
the glass overshoots whenever `g` is above one, and the error grows whenever
`g` is above two. Since nobody knows `g`, that is a gamble. An overshoot can
carry the glass into another crowd. The extra travel is also extra distance in
which something can be knocked over.

**A small gain is safe.** Set `k` well below one. Then `g · k` stays in the safe
range even if `g` is several times larger than expected. The shortfall shrinks
by the same share each pass. For example, if `g · k` is one half, each push
halves what is left. After three pushes, an eighth is left. The method does not
need to know the exact share. It only needs the shortfall to keep shrinking.

![What is left of the shortfall after each of four passes, for four values of the product g · k: at 0.3 it shrinks slowly and steadily, at 1 it lands exactly but only because the product happened to be 1, at 1.8 it crosses the line each time and still shrinks, and at 2.4 it grows.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-gain.png)

The cost of a small gain is more pushes. A smaller gain is safer and slower.

There is one more point about the gain. You could pick it by trying many values
on the training tables and keeping the best. That would be **fitting a number to
data**, and this solution must not do that.
[The overview of the solutions](../03_the-seven-solutions/01_how-the-six-compare.md)
records that it fits nothing. A baseline that is tuned until it does well is no
longer a baseline. So the gain is chosen by argument instead. It is small enough
to shrink the shortfall across the whole likely friction range. Then it is
frozen.

The small gain makes the loop shrink the error. The next section says why that
is enough without any prediction.

## 4. Why repeating replaces predicting

The last section showed that a small gain always shrinks the error. So the
method never needs to say where a glass will stop. This means **it cannot be
wrong about physics it never claimed to know**.

Here is what the method does claim. It claims a direction, which needs no
friction. It claims the shortfall can be measured, which `look()` makes true up
to the error [the camera work reports](../../08_seeing-the-glasses/11_the-results.md).
It claims that a glass pushed away from its neighbour ends further from it.
That is true for any friction.

Here is what it does not claim. It does not claim how far the glass goes. It
does not claim the glass will not turn. It does not claim to know the friction.
Any solution that fails because its model of pushing was wrong fails on a
claim this one never makes.

The price is more pushes, and so more arm time.
[What it needs](05_what-it-needs.md) counts that cost. The other six solutions
each pay for a way to need fewer pushes. Solution 4 learns what a push does and
plans with it. Solutions 3, 6 and 7 learn a policy from many pushes. Solution 2
ranks many possible pushes and picks the best one. **The comparison between
this solution and the other six measures what needing fewer pushes is
worth.**

Repeating has a limit. Giving one glass room can take room from another. A loop
that only repeats can then go back and forth until the budget runs out.
[A worked example](04_a-worked-example.md#2-a-worked-example) shows this on a
glass crowded from two sides.

The next section says which of these parts are real code and which are only a
design.

## 5. What is built and what is a design

The sections so far described the method. This section says which parts of it
exist as code. It would be easy to claim too much here.

These parts are **built, in the repository, and run against the examiner**:

- The examiner itself, in [`src/09_pushing-the-glasses-apart/bench/`](../../../code/src/09_pushing-the-glasses-apart/bench). It has the crowded tables, the measurement error, `look()`, `push()`, `take()` and the scorecard.
- The room test, as `has_room()` in [`src/09_pushing-the-glasses-apart/bench/bench.py`](../../../code/src/09_pushing-the-glasses-apart/bench/bench.py).
- The shortfall, as `shortfall()` in [`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py).
- The tipping rule, as `slides()` in the same file, with the short test push.
- The loop, in [`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/run.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/run.py). It looks, racks every glass that has room, chooses one push, makes it, and looks again. The examiner sets the budget, so every solution gets the same number of tries. That is four pushes at one glass, and sixteen on one table.
- The refusal reasons, and the scorecard that counts them.

These parts are **a design, not code**:

- The four decisions of [the main idea](01_what-it-is.md#4-the-main-idea). The planner in the repository does something else. It searches many directions and many distances, and keeps the shortest push that frees a glass. If no push frees a glass, it keeps the push that most reduces the table's total shortfall. That search is how [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) makes its candidates. This solution would replace the search with one direction and one multiplication.
- The gain, which has no value in the repository.
- The shared target layout, which this solution does not use.
- The top view of the table and the path for a chunk of waypoints. This solution needs neither.
- The repeats and the compute column that [the examiner](../01_the-problem/03_the-examiner.md) describes for the scorecard.

One measurement from the built code is useful. The run in
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/results.json`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/results.json)
reports how far each pushed glass stopped from its aim. The median is 1.7 mm,
and the worst is 57.6 mm. **That run uses the searching planner, not this
solution's rule.** So it says something about the simulator, not about this
rule. In this simulator, a pushed glass usually follows the jaw closely, so
`g` is near one. No solution is told this. On a real table with a cloth or a
spill, it would not hold. So this method should need few pushes on the
examiner's tables, but you should not trust that anywhere else.

The next section names the one thing this solution cannot do that its nearest
neighbour can.

## 6. It produces nothing anybody can learn from

The last section listed what this solution is made of. This section names the
one thing it cannot give the others.

Solutions 3 and 6 learn from demonstrations. A demonstration is a recorded
example of the task: what the arm saw, and the push it made. Their examples
come from solution 2, which scores many possible pushes and keeps the best.
[Solution 2's how it works](../05_geometry-generates-a-model-ranks/03_how-it-works.md)
explains why that makes it a teacher.

**This solution leaves nothing like that.** It makes one push per pass and
scores nothing, because there is nothing to compare that push with. A record of
its runs says which push was made and where the glass ended. It does not say
whether a better push existed. No ranker can be fitted to that, and a policy
fitted to it could only learn the same one rule.

So this solution is a control and nothing more. That is not a fault. A control
that also supplied training data would be doing two jobs, and the second job
would make the first one less trustworthy. But without solution 2, the
demonstrations for solutions 3 and 6 would have to come from somewhere else,
such as a person driving the arm. That would be a real extra cost.

← [The code](02_the-code.md) · [A worked example](04_a-worked-example.md) →
