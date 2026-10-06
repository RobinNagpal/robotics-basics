# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that cannot be pushed safely,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

Every solution in this set has to answer this question, and this one answers it
twice over, which makes it the most interesting place to look at what learning
the physics really buys.

[Pushing without toppling](../01_the-problem/03_pushing-without-toppling.md) gives the written
rule, and it is shared by all six without exception: a glass slides while the
contact height is below half its foot width divided by the friction
coefficient, and tips above it. A glass whose limit is below the jaw's top edge
cannot be pushed safely at any height the gripper can reach, and the only
correct answer for it is to refuse. That arithmetic is applied before any model
is consulted, so no model here can cause the failure this problem cares most
about, and because the friction in it is a guess it is evaluated across the
range a glass on a dry wooden top plausibly covers rather than at one value.

**The built planner does not evaluate that rule, and that is a gap in it rather
than a second opinion.** It holds no friction value and no tipping formula, so
the shared gate belongs in front of it and is not there yet. What it adds —
and this is what learning the physics buys — is a **second** refusal, which
comes from the evidence rather than from the rule: a glass is refused when
**every push the search asked about was turned down**, and the planner reports
which kind of rejection dominated. If most candidates died on the topple limit,
the glass is reported as one where every push the model was asked about might
tip something over. If most died on the map, it is reported as having nowhere
inside the zone and within reach to push it to. Two further refusals come from
the loop rather than the model: a glass that has been pushed its allowed number
of times and still has no room, and a table whose push budget is spent.

A refusal reached this way is a stronger statement than it first appears,
because of how it was reached. Fifteen hundred candidate pushes were examined,
each by five independently trained copies of the model, each also on four copies
of the table shifted by the camera's error. "No push survived" means no push
survived all of that. **A glass refused here is a glass for which the search
could not find a single push that five separately trained models and five
slightly different tables all agreed was safe**, which is a different claim
from the one-line inequality with a guessed number in it, and an addition to
that inequality rather than a replacement for it.

The honest weakness has to be stated with it, because it is this solution's
worst one. **The model can be confidently wrong.** The ensemble measures
disagreement, and disagreement only appears where the training data was thin in
a way the copies noticed. A kind of failure that is absent from the training
data altogether can produce five copies that agree, agree confidently, and agree
wrongly. The first way's own results record exactly this: one glass went over on the
fifty held-out tables and one on a hundred tuning tables, and the model had
rated as safe every topple it missed. The three causes recorded there are
instructive, because all three are
things the thirty-four numbers cannot express — the jaw meeting a stemmed glass
at its stem and lifting under the bowl, the jaw's body clipping a neighbour
behind the target, and a tapered glass tipping on its own.

Lowering the topple limit does not fix that. A limit only moves the line among
pushes the model has an opinion about, and these are pushes the model is
confident about. What fixes it is more examples of exactly those situations,
which is an argument for more data collection and, for the body clipping a
neighbour, an argument for telling the model that the jaw has a body at all.

And the limit that cannot be fixed by either is the one [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) states for all six: **nothing in this
loop stands a toppled glass back up.** That is why the topple test is a veto
rather than a cost to be weighed against the value of moving the glass. A risk
worth taking is one whose bad outcome the system can absorb, and this one it
cannot.

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
