# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that cannot be pushed safely,
because a worked example that shows only the easy case teaches the wrong
lesson.

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

What learning the physics adds is a **second** refusal, from the evidence
rather than from the rule: a glass is refused when every push the search asked
about was turned down, and the planner reports which kind of rejection
dominated. That is a stronger statement than it first appears, because of how
it was reached. Fifteen hundred candidate pushes are examined, each by five
independently trained copies of the model, each on four copies of the table
shifted by the camera's error. **A glass refused here is one for which no push
survived all of that** — a different claim from a one-line inequality with a
guessed number in it, and an addition to it rather than a replacement.

The weakness has to be stated with it. **The model can be confidently wrong**,
because the ensemble only disagrees where the training data was thin in a way
the copies noticed, and a kind of failure absent from the data altogether
produces five copies that agree wrongly. The record shows exactly that: one
glass went over on the fifty held-out tables and one on a hundred tuning
tables, and **the model had rated as safe every topple it missed.** Lowering a
limit does not fix that, because these are pushes the model is confident about;
more examples of those situations does.

## 2. A worked example

The clearest way to see the whole arrangement run is on one of the examiner's
held-out tables, and the first way can be traced step by step on any of them.

Take a table of six glasses of one kind. The first look reports six readings.
Several pairs are closer than the 70 mm of clear room the gripper needs, so
nothing can be taken yet, and the planner goes to work on every crowded glass
in turn.

For the first of them, the search draws six hundred candidate pushes spread over
every heading, every offset across the glass and every travel from a centimetre
to ten. All of them go to the five copies, and most die on the table that comes
back: the predicted landing is outside the glass zone, or the jaw's own path
leaves the arm's comfortable reach, or the predicted movement is longer than
the push itself. A further batch is struck out by the topple veto — some
because a short jab at a wide part of the glass genuinely looks like tipping
it, and some because the five copies simply disagree, which counts the same
way. What is left is scored by how much clear room is still missing on the
table afterwards.

Three more rounds contract the cloud of candidates onto the region that scored
best, and the winner is a push of a few centimetres that moves the target
glass away from its nearest neighbour without pushing it towards any other. The
same search runs for each of the other crowded glasses, and the single best push
over all of them is the one made.

The jaw comes down behind the glass, feels forward until it touches, pushes, and
backs off. Then the arm looks again — and this is the step that makes the whole
arrangement work, because the glass has not landed exactly where the model said
it would, and the planner neither knows nor cares, since it re-plans from the
measurement rather than from the prediction.

After this push one glass has room and is taken. Two pushes later the rest are
clear and are taken as well, and the table finishes done.

Not every table finishes that way, and the two interesting endings are both
recorded in the first way's traces. On one, a push is blocked on the way down — the
jaw touches something before reaching the table, goes straight back up without
pushing, and the loop simply looks again and plans afresh, so a blocked push
costs a push and nothing else. On another, two pushes are made and then no
further push survives the filters, so three glasses are reported refused with
their reasons and the table finishes **correct but incomplete**, which [the
problem](../01_the-problem/01_what-is-asked-for.md) counts as a correct outcome rather than a failure.

Across the fifty held-out tables as a whole, the first way's recorded results — read
from its own `results.json` — are two hundred and two of two hundred and
fifty-one glasses racked in a hundred and fourteen pushes, thirty-one tables
finished, and the glasses that were left all reported with a reason. **That is
the most glasses any of the six racks, and it is done in the fewest pushes.**
It is also the one line where this solution is worse than the geometry it is
measured against: **one glass went over**, which makes that table wrong and
makes this the only one of the three push-parameter solutions to topple
anything at all — [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md) and [geometry
generates, a model ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md) both topple none. The section
above on refusals says why it can happen: the model can be confidently wrong,
and the shared topple gate that would have caught the rest is not in front of
this planner yet. Those numbers are read against the other solutions on
the shared scorecard, and against the displacement floor from [the target
layout](../01_the-problem/02_the-target-layout.md), which says how little movement the task
needed in the first place.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
