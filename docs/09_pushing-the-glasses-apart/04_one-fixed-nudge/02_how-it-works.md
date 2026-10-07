# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [Open loop and closed loop](#1-open-loop-and-closed-loop)
2. [The shortfall, and why it is measured to the neighbour's edge](#2-the-shortfall-and-why-it-is-measured-to-the-neighbours-edge)
3. [Why the push is a fraction of the shortfall rather than all of it](#3-why-the-push-is-a-fraction-of-the-shortfall-rather-than-all-of-it)
4. [Why repeating replaces predicting](#4-why-repeating-replaces-predicting)
5. [What is built and what is a design](#5-what-is-built-and-what-is-a-design)
6. [It produces nothing anybody can learn from](#6-it-produces-nothing-anybody-can-learn-from)

## 1. Open loop and closed loop

The four decisions above are small, and the thing that makes them sufficient is
not their content but the loop they sit inside. That loop has a name in control
engineering, and the name is worth learning because the rest of this document
uses it.

A plan that is computed once and then carried out without reading anything back
is **open loop**. It commits to the whole answer in advance, on the strength of
whatever it believed when it started, and it has no way of noticing that the
world disagreed. A plan that measures, acts, measures again and lets the second
measurement change what it does next is **closed loop**. The three parts of a
closed loop always have the same shape: a **measurement** of how things are, an
**error** that says how far that is from how things should be, and a
**correction** that is meant to reduce the error.

The programming comparison is exact, and it is the clearest way to see the
difference. Open loop is unrolling a loop into a fixed sequence of statements
because you are sure how many times it will run. Closed loop is a `while` loop
whose condition re-reads a value that the body of the loop changes. Written as
code, this solution is one such loop and nothing more: while the table is short
of room, measure the shortfall, push, and measure the shortfall again. The
condition is not a count that was worked out before the run. It is a fresh
reading of the world.

Newton's method is the same idea in arithmetic: it finds the root of a
function without anybody having a formula for the root, using only a way to
measure how wrong the current guess is and a rule that makes the wrongness
smaller. This solution is in that position. Nobody can write down where a
glass will be after a push, but anybody can measure how much room it is short
of, and the rule that makes that smaller is to push it away from whatever is
crowding it.

The three parts map onto the cell directly. The measurement is `look()`, which
the examiner provides. The error is the shortfall. The correction is the nudge,
and the fraction that turns the error into the correction is called the
**gain**, which is the standard word for it. A correction that is the error
multiplied by a fixed gain is a **proportional controller**, and that is the
whole of this method's cleverness.

Every one of the six solutions runs inside a loop of this shape, because
[pushing without toppling](../01_the-problem/03_pushing-without-toppling.md) shows that none of
them can do otherwise. What makes this one the control is that in the other
five the loop surrounds something substantial, and here **the loop is the
method**. There is nothing inside it to compare.

## 2. The shortfall, and why it is measured to the neighbour's edge

The loop needs an error, so the error has to be defined before anything else,
and the definition contains the one trap in this problem that catches almost
everybody.

To close on a glass the open jaw has to get round it: a finger and a pad on
each side, with the jaw opened wider than the glass before it closes. Added up
from the glass's middle outwards, that comes to about **70 mm of clear room in
every direction**. Those are the gripper's own numbers, so the project is
allowed to write them down, and the examiner holds the 70 mm as a constant and
applies the test like this: **a glass has room when every other glass's edge is
at least 70 mm from its middle.**

Read that sentence twice, because the word *edge* is what makes the test
asymmetric. The 70 mm is measured from one glass's middle out to another
glass's **edge**, and a glass's edge is half its own widest width out from its
own middle. So what a glass needs from a neighbour depends on **how wide the
neighbour is, not on how wide it is itself**. A narrow glass standing beside a
wide one can be badly short of room while the wide one, at the very same
distance, has room to spare, because the wide one's rim reaches much further
into the gap than the narrow one's does.

![The same pair of glasses from the top at four separations, showing that the wide one comes free before the narrow one does: each glass carries the 70 mm ring the open jaw needs, and a glass is blocked while its neighbour's edge is inside that ring, so the narrow glass, whose neighbour's edge reaches further in, is still blocked at a distance where the wide one already has its room.](../../images/pushing-the-glasses-apart/one-fixed-nudge/01-four-distances-one-pair.png)

From that, the error falls out. The shortfall of one glass against one
neighbour is

    70 mm  +  half the neighbour's widest width  −  the distance between
    their middles

and it is zero or less when that neighbour is not in the way. The glass's own
shortfall is the largest of those values over every other glass on the table,
and the neighbour that produced the largest value is the one whose edge is
nearest to the glass's middle. So **the blocking neighbour and the deepest
intruder are the same glass**, and the method needs no separate rule to find
it.

Written as a subtraction the shortfall is three numbers. Drawn on the table it
is one length, and it is the length the whole method is built around.

![The crowded glass with the 70 mm ring the open jaw needs round it, the neighbour's rim reaching inside that ring, and the overlap marked: the shortfall is how far the neighbour's edge comes inside the ring, which is the same thing as 70 mm plus half the neighbour's width minus the distance between the two middles.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-error.png)

Two consequences matter, and both are easy to miss.

**The test is on an ordered pair rather than on a pair.** Asking whether A and
B are far enough apart is not a question with one answer. A may be crowded by B
while B is not crowded by A. So the method has to evaluate the shortfall in
both directions for every pair, and a method that compares only the distances
between middles will call a pair fine when one of the two cannot be gripped.
This is the same point [the problem](../01_the-problem/01_what-is-asked-for.md) makes with its three
distances, and [the target layout](../01_the-problem/02_the-target-layout.md) makes again when it
insists that a layout has to use the edge version of the condition.

**The shortfall is already in the repository.** The function `shortfall()` in
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py)
computes exactly the expression above and adds it up over the whole table, as a
measure of how crowded the arrangement is. This solution uses the same quantity
one glass at a time, as its error.

## 3. Why the push is a fraction of the shortfall rather than all of it

With the error defined, the only remaining question is how large a correction
to make from it, and the answer is the one place where the missing friction
decides the design rather than merely complicating it.

Start by naming what nobody knows. Call the shortfall `s`, and call the
fraction the method applies to it `k`, which is the gain. The jaw is therefore
commanded to travel `k · s`. What the glass actually does is some other
distance, because the jaw may slip against a curved wall, the glass turns as
well as travels, the friction under its foot is not the same everywhere on that
foot, and the glass may carry on a little after the jaw stops or stop a little
before it. Write that unknown as a factor `g`, so the glass moves `g · k · s`.
**Nothing in the cell measures `g`, and nothing bounds it tightly**, because
every term that would settle it runs through the friction coefficient, and
glass on a dry wooden top plausibly spans a range of more than two to one.

Now the arithmetic. The shortfall after the push is

    s'  =  s − g · k · s  =  s · (1 − g · k)

so the shortfall shrinks whenever the size of `1 − g · k` is less than one,
which happens whenever `g · k` lies between zero and two. That single
inequality is the whole argument for a small gain, and it has two readings.

**A confident push is unstable against the unknown.** Set `k` to one, which is
the obvious choice of aiming to close the whole gap at once, and the method
converges only while `g` stays below two, and overshoots whenever `g` is above
one. Since `g` is not known to within a factor of two, that is a coin toss
rather than a design. An overshoot is not a harmless error either: it carries
the glass past where it needed to be, and the glass has to land somewhere.
Moving one glass out of a crowd can easily move it into a different crowd, so
the push that was meant to end the problem creates a second one, and the extra
travel is extra distance in which something can be knocked over.

**A modest push converges against a wide range of the unknown.** Set `k` well
below one and the product `g · k` stays inside the safe range even when `g`
turns out to be several times what anybody would have guessed. The shortfall
then falls as a geometric sequence: if `g · k` happens to be a half, each push
halves the remaining shortfall, so three pushes take it to an eighth of what
it was and the glass crosses the line. The method does not need to know which
geometric sequence it is on. It only needs the sequence to be decreasing, and
that is what the small gain guarantees.

![What is left of the shortfall after each of four passes, for four values of the product g · k: at 0.3 it shrinks slowly and steadily, at 1 it lands exactly but only because the product happened to be 1, at 1.8 it crosses the line each time and still shrinks, and at 2.4 it grows.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-gain.png)

What the small gain costs is **the number of steps**, because the number of
pushes needed to close a given shortfall grows as the logarithm of the
reduction divided by the logarithm of `1 − g · k`. A smaller gain is therefore
safer and slower in a way that can be written down exactly, and the price is
paid in arm time rather than in risk.

One more point about the gain, and it is about honesty rather than about
control. The gain could be chosen by trying many values over the training
tables and keeping the best, and that would be **fitting a number to data**,
which this solution is not allowed to do: [the overview of the
six](../03_the-six-solutions/01_how-the-six-compare.md) records that this solution fits nothing, and a baseline
that is quietly tuned until it is competitive has stopped being a baseline. So
the gain is argued instead. It is chosen small enough that the convergence
condition holds across the whole plausible friction range, and then frozen, and
that argument is written down where anybody can disagree with it.

## 4. Why repeating replaces predicting

The small gain buys convergence, and the loop buys correctness, so the method
can now be stated in its strongest form: it never says where the glass will
land, and therefore **it cannot be wrong about physics it never claimed to
know**.

It is worth being exact about what is and is not claimed. The method claims a
direction, which does not need the friction. It claims that the shortfall is
measurable, which `look()` makes true up to the measurement error [the camera
work reports](../../08_seeing-the-glasses/11_the-results.md). It claims that a
glass pushed away from its neighbour ends up further from that neighbour, which
is true for any friction whatever. It does not claim how far the glass goes, it
does not claim that the glass will not rotate, and it does not claim to know
whether this table is slippery or sticky. Every solution that fails because its
model of pushing was wrong fails on a claim this one does not make.

The price is arm time, and it should be read as a real price rather than as a
rhetorical one. One push is a whole sequence of arm movements, set out in [the
pushes are what this contributes](03_the-code.md#2-the-pushes-are-what-this-contributes), and
every one of them is followed by a fresh look. **Every push is seconds of arm
time, and the scorecard counts pushes against a fixed budget**, so the
currency this method pays in is finite. A method that converges in four pushes
where another converges in one has not failed, but it has spent four times the
time and four times the travel, and travel is where a glass gets knocked.

So the honest summary of this solution's position is that it moves its cost out
of error and into time. Every other solution in the set is buying a way to
shorten the loop. Solution 4 buys a model of what a push does and plans
through it, so that one push can be aimed at the answer. Solutions 3 and 6 buy
the same shortening implicitly, by fitting a policy that has seen many pushes
and their outcomes. Solution 2 buys a ranking over many candidate pushes, which
is a way of choosing a better single push without predicting its outcome in
detail. **What the comparison between this solution and the other five
measures is exactly what that shortening is worth.**

And repetition has a floor, which it would be dishonest to leave out. Pushes
are not independent: giving one glass its room can take room from another,
which then needs a push of its own, which can take it back. A loop that is
reduced to repeating can oscillate, and the only thing that stops it is the
budget. [A worked example](04_a-worked-example.md#2-a-worked-example) shows that happening.

## 5. What is built and what is a design

Before the output and the refusals, it is worth saying plainly which of all
this exists as code, because this is one of the few solutions in the set where
real code is involved and it would be easy to over-claim.

**Built, in the repository, and run against the examiner:**

- the examiner itself, in [`src/09_pushing-the-glasses-apart/bench/`](../../../code/src/09_pushing-the-glasses-apart/bench), with the
  crowded tables, the measurement error, `look()`, `push()`, `take()` and the
  scorecard;
- the room test, as `has_room()` in
  [`src/09_pushing-the-glasses-apart/bench/bench.py`](../../../code/src/09_pushing-the-glasses-apart/bench/bench.py), which holds the
  70 mm as the gripper's constant and applies it to the neighbour's edge;
- the shortfall, as `shortfall()` in
  [`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py);
- the tipping rule, as `slides()` in the same file, evaluated at the top edge
  of the jaw and at both ends of the plausible friction range, together with
  the small test push that settles the glasses the range cannot;
- the loop, in [`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/run.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/run.py):
  look, rack every glass that already has room, choose one push, make it, look
  again. The budget is the examiner's rather than this solution's, so that the
  six are allowed the same number of tries: four pushes at any one glass, and
  sixteen on any one table;
- the refusal reasons, and the scorecard that counts them with the outcome
  rather than the action.

**A design, not code:**

- the four decisions of [the main idea](01_what-it-is.md#3-the-main-idea). The planner that
  exists chooses its heading and its distance by searching many headings and
  every distance up to a limit, and keeping the shortest push that frees a
  glass — or, when no push on the table frees one, the push that most cuts the
  table's total shortfall of room, so that the next look starts from a looser
  table. That search is the geometry [solution
  2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) generates its candidates with. This solution
  replaces it with one heading and one multiplication, so the parts around the
  rule have been run and the rule itself is the few lines that would sit where
  the search sits;
- the gain, which has no value in the repository;
- the shared target layout, which this solution does not use in any case;
- the rendered view of the table from the top, and the path for a chunk of
  waypoints, neither of which this solution needs;
- the repeats and the compute column that [the examiner](../02_the-examiner.md)
  describes for the scorecard.

One measurement from the built code is worth quoting, with its attribution
made clear. The programmed run reports in
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/results.json`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/results.json)
that its pushed glasses stopped a median of 1.0 mm, and at worst 3.9 mm, from
where they were aimed. **That run uses the searching planner rather than this
solution's rule**, so the figure is not this solution's score. What it does say
is something about the examiner rather than about any rule: in this simulator, a
glass that is pushed follows the jaw closely, so the unknown factor `g` of the
previous section sits near one here. No solution is told that, nothing in the
cell would reveal it, and on a real table with a real cloth or a real spill it
would not hold. It is a reason to expect this method to converge in few pushes
on the examiner's tables, and not a reason to trust it anywhere else.

## 6. It produces nothing anybody can learn from

There is one thing this solution cannot do that its nearest neighbour in the
set can, and because it is the single clearest difference between the two it
belongs here rather than buried at the end.

Solutions 3 and 6 are fitted to demonstrations, which means recorded examples
of the task being done: what the arm saw, and the push that was made from
there. Both of those documents say the examples come from solution 2 for
nothing: solution 2 has geometry generate many candidate pushes for each
crowded glass and then ranks them, so every push it makes is a demonstration
and is also the best of a set that was written down and scored first. It is
what earns solution 2 its place in the set beyond being a second baseline.

**This solution leaves behind nothing of the kind.** It generates exactly one
push per pass and it scores nothing, because there is no alternative to
compare the one push against. A record of its runs would say that a particular
push was made and that the glass afterwards was in a particular place, with no
indication of whether a better push existed. That is a log rather than a
scored candidate set, so no ranker can be fitted to it, and a policy fitted to
it could learn nothing but the one rule that produced it.

So this solution is a control and only a control. It cannot also be the
teacher. Saying so is not a complaint about it, because a control that also
supplied training data would be doing two jobs and the second job would make
the first one suspect. But it does mean that if the ranked geometry did not
exist, the demonstrations for solutions 3 and 6 would have to be bought
somewhere else, either by a person teleoperating the arm or by writing a second
method for the purpose, and both of those are real costs that the comparison
would then have to carry.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
