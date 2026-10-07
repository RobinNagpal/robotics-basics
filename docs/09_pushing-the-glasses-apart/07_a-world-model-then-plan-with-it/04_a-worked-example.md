# A worked example

This page takes this solution's refusals first, because a worked example that
shows only the easy case teaches the wrong lesson, and then follows the solution
through three of the examiner's held-out tables with the numbers its own run
recorded.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

A glass slides while the jaw touches it below half its foot width divided by
the friction, and tips above that. The height that counts is the jaw's **top
edge** at 65 mm, not the 50 mm its middle rides at, and for a glass whose foot
is narrow enough there is no contact height the arm can offer below the limit.
The only correct answer for such a glass is to refuse, with the reason
recorded, which marks the run *correct but incomplete* rather than wrong.
[Pushing without toppling](../01_the-problem/03_pushing-without-toppling.md)
sets all of that out once, including what is done when the unknown friction
leaves the limit undecided, and it is **arithmetic applied before any model is
consulted** in five of the six solutions. What follows is only what is this
solution's own.

**This is the one solution that does not apply that arithmetic, and that is a
gap in it rather than a second opinion.** The built planner holds no friction
value and no tipping formula, so the shared rule belongs in front of it and is
not there yet.

What learning the physics adds is a **second** refusal, from the evidence rather
than from the rule. The planner can turn a glass down in two different ways, and
it records which. It can find that every one of the fifteen hundred candidate
pushes was struck out by one of the three filters, in which case no push on that
glass got past five independently trained copies of the model asked on five
readings of the table, and the reason it reports names whichever of the topple
veto and the map struck out more of them. Or it can find that pushes survived
and none of them was worth making, because the best one on the whole table would
clear less than 2 mm of the room the table is missing.

**On the fifty held-out tables only the second of those ever happened.** Of the
48 glasses left behind, 44 were refused because no surviving push would have
made enough room, one because it had already been pushed the four times any
glass is allowed, and three because a glass had gone over on their table and
nothing more is touched after that. Not one glass was refused for want of a push
the model would allow. So the stronger refusal is machinery that exists and did
not fire here, and the claim worth making for it is about the arithmetic it
replaces — a judgement from fifteen hundred recorded-push comparisons rather
than from a one-line inequality with a guessed number in it — not about how
often it saved this run.

The weakness has to be stated with it. **The model can be confidently wrong**,
because the ensemble only disagrees where the training data was thin in a way
the copies noticed, and a kind of failure absent from the data altogether
produces five copies that agree wrongly. The record shows exactly that: one
glass went over on the fifty held-out tables and one on a hundred tuning
tables, and **the model had rated as safe every topple it missed.** Lowering a
limit does not fix that, because these are pushes the model is confident about;
more examples of those situations does.

## 2. A worked example

The first way can be traced step by step on any held-out table, and its folder
writes the trace out: a picture of each step, and a file holding the
thirty-four numbers the model was given, the fourteen each of the five copies
gave back, and the fourteen that really happened. Four tables are worth tracing,
and the three described here are among them.

Table 10004 is the ordinary case. The first look reports six readings of one
kind of glass. Several pairs are closer than the 70 mm of clear room the gripper
needs, so nothing can be taken yet, and the planner goes to work on every
crowded glass in turn.

For the first of them, the search draws six hundred candidate pushes spread over
every heading, every offset across the glass and every travel from a centimetre
to ten. All of them go to the five copies, and most die on the table that comes
back: the predicted landing is outside the glass zone, the jaw's own path leaves
the arm's comfortable reach, or the predicted movement is far longer than the
push that caused it. A further batch is struck out by the topple veto — some
because a short jab at a wide part of the glass genuinely looks like tipping it,
and some because the five copies simply disagree, which counts the same way.
What is left is scored by how much clear room is still missing on the table
afterwards.

Three more rounds contract the cloud of candidates onto the region that scored
best. The same search runs for each of the other crowded glasses, and the single
best push over all of them is the one made.

The jaw comes down behind the glass, feels forward until it touches, pushes, and
backs off. Then the arm looks again — and this is the step that makes the whole
arrangement work, because the glass has not landed exactly where the model said
it would, and the planner neither knows nor cares, since it re-plans from the
measurement rather than from the prediction. Three pushes on three different
glasses finish this table, and all six glasses are racked.

The other two tables are the endings that are not that. On table 10006 a push is
blocked on the way down: the jaw touches something before reaching the table,
goes straight back up without pushing, and the loop simply looks again and plans
afresh, so a blocked push costs a push and nothing else. That glass ends up
pushed twice. On table 10012 two pushes are made
and then no push is worth making, so three glasses are reported refused with
their reasons and the table finishes **correct but incomplete**, which [the
problem](../01_the-problem/01_what-is-asked-for.md) counts as a correct outcome
rather than a failure.

Across the fifty held-out tables as a whole, the first way's recorded results — read
from its own `results.json` — are two hundred and two of two hundred and
fifty-one glasses racked in a hundred and fourteen pushes, thirty-one tables
finished, and the glasses that were left all reported with a reason. **That is
the most glasses any of the six racks, and it is done in the fewest pushes.**

One line of that record is worth reading against the written geometry, because
it says something the totals hide. The scorecard measures how far each pushed
glass stopped from where its solution aimed it, which for this solution is the
model's own prediction. The median is 1.6 mm and the worst is 48.2 mm. The
programmed run recorded in
[`01-one-fixed-nudge/results.json`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/results.json),
aiming by arithmetic, manages 1.0 mm and 3.9 mm. **So this solution wins while
being the less accurate of the two**, and it wins because accuracy is not what
the task pays for: the geometry knows exactly where a glass will go and not
whether that makes room, so it pushes, looks and often pushes again. Ninety of
its 213 pushes are repeats of a push that fell short, against 14 of this
solution's 114.

The line it loses on is the one that cannot be taken back. **One glass went
over**, which makes that table wrong and makes this the only one of the three
push-parameter solutions to topple anything at all — [one fixed
nudge](../04_one-fixed-nudge/01_what-it-is.md) and [geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md) both topple none.
Ten more pushes went wrong without breaking anything: seven blocked on the way
down and three jammed, each caught by the next look. The section above on
refusals says why the topple can happen: the model can be confidently wrong, and
the shared topple gate that would have caught it is not in front of this planner
yet. Those numbers are read against the other solutions on the shared scorecard,
and against the displacement floor from [the target
layout](../01_the-problem/02_the-target-layout.md), which says how little movement
the task needed in the first place.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
