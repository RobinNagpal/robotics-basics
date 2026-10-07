# A world model, then plan with it

This page describes the fourth of the six solutions in about eight minutes of
reading. It is the only one that learns **what will happen** rather than what to
do: it fits a model that answers "if I make this push, what will the table look
like afterwards?", and then finds a good push by trying candidates against that
model instead of against the real table. By the end of this page you will know
what a forward model is, how the search uses it, what it scored on the shared
examiner, and why its result is the most interesting one in the book. The full
treatment is in [the chapter on this
solution](../07_a-world-model-then-plan-with-it/01_what-it-is.md), which is
about an hour of reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

A **forward model** is a function that takes a situation and an action and
returns the situation that follows. It is the thing a chess player uses when
they picture the board after a move, and it is what lets you compare two actions
without carrying either of them out.

That is what this solution fits. The model takes the table as the camera
measured it, plus one candidate push, and answers with the table afterwards:
where every glass moves, whether anything topples, and whether the jaw is
blocked on the way down. Because the answer is a **table** rather than a score,
the same answer can be fed back in as the next question, which is what would let
this solution plan a *sequence* of pushes — move one glass out of the way first
so that a second glass has somewhere to go. No other solution here could do
that. The planner that was built has a horizon of one push, so the sequence is a
design in the full chapter rather than code that runs.

The reason to learn this particular quantity is the point of the whole solution.
[Geometry generates, a model ranks](03_geometry-generates-a-model-ranks.md) fits
a model of *how much a push would help*, which is a quantity the geometry
already computes exactly from the destination. This solution fits a model of
*what a push will actually do*, which is the quantity the geometry gets wrong,
because predicting where a pushed glass stops needs the friction and the weight
distribution that nobody in this cell has measured. Those are two different
bets about which question deserved a model, and the examiner settles it.

The first way is five copies of a small network written for this cell and trained
here, with no downloaded weights of any kind. The second way would be TD-MPC2, the
model-based entry in LeRobot. **The second way is not built**, so no number here is
its.

![Thousands of pushes are made in the simulator and nobody labels any of them, because the answer to every example is what the second look found; five copies of a small network are fitted to say what the table looks like after a push; and before every push the arm makes, candidates are drawn, put to all five, filtered and scored, and only the best one is carried out.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-flow-what-it-does.png)

![Five networks fitted on the same data from different random starts agree where the training data covered that kind of push and diverge where it did not, which is a measure of ignorance that costs almost nothing — and where the data was thin in a way none of them noticed, all five agree and are wrong together.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-flow-the-five-copies.png)

## 2. How it works

**The readings and a candidate push become one row of numbers.** Each glass's
position and widths come from the camera, the push is three numbers, and the
whole situation is written in the push's own frame — along the push and across
it — rather than in the room's frame. That is deliberate: in the room's frame
the model would have to learn the same physics separately for every compass
direction, and in the push's frame the direction carries no information at all,
so one set of weights covers every heading.

**Five copies of the model each answer.** Fitting five networks on the same data
with different random starts costs five times very little, and their
**disagreement is a usable measure of ignorance**: where they agree, the
training data covered this kind of push, and where they diverge, it did not.
Most learned methods give no such signal at all.

**A candidate is discarded if any copy thinks it might topple something**, or if
the predicted table breaks the map of where a glass may stand and where the arm
can reach. The map is the only thing written down inside the built planner;
there is no friction value, no tipping formula and no rule about where the jaw
fits.

**The survivors are scored by how much room is still missing afterwards**, and a
sampling search refines the good ones. The search draws candidate pushes,
evaluates them all against the model, keeps the best, draws again near those,
and repeats — the method known as the cross-entropy method. About fifteen
hundred candidates are evaluated before every push the arm makes.

**The best push is handed to the examiner** as three numbers, and the examiner's macro
expands it into the jaw trajectory every solution here is judged on.

Two honest gaps are worth knowing before the scores. The shared topple rule that
every other solution applies as arithmetic *before* any model is consulted is
not wired up in front of this one, so here the ceiling on how badly a push can
go comes from the model rather than from arithmetic. And error compounds over
depth, which caps how far a sequence could usefully be planned with a model
trained on single pushes.

## 3. What it needs

It needs **a physics engine and tens of thousands of pushes made in it**, and
this is the real cost, which no other solution pays in the same currency. The
first way records 38,012 pushes, collected in two rounds: a first round of
random pushes, and a second round chosen by the planner using the first round's
model, which fills the holes the search would otherwise exploit. Nobody labels
any of it, because the answer to every example is simply what the second look
found. That is the single biggest practical advantage this family has over
anything trained on demonstrations.

It needs **a training run before it can answer anything**, which is five small
networks and about half an hour on a laptop processor, with no accelerator at
all. That is unusual among the learned solutions here, and it follows from the
model being small and its input being a few dozen numbers rather than a
picture.

The second way would need **rented hardware**. TD-MPC2 is reinforcement
learning, it trains on far more interaction than a one-step fit needs, and it
wants an accelerator: of order a hundred dollars for a weekend, or five hundred
for a month if several training seeds are to be run.

It needs **run-time compute**, and this is where the solution is expensive.
About fifteen hundred candidates, each put to five networks, for every crowded
glass, before every push. That is cheap in absolute terms and still hundreds of
times the arithmetic a fixed nudge costs, which is why the scorecard carries a
compute column.

It needs **a file of weights kept in step with the cell**, and it borrows no
model, so there is no model licence to meet in either way.

## 4. What it scored

All six solutions are given the same 50 tables holding 251 glasses, of which 193
have no room at the start. The geometry's row is shown beside this one, because
the pair is what this solution exists to settle.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| this solution (the first way) | 31 | 1 | **202** | 1 | **114** |
| the ranked geometry | 31 | 0 | 185 | 0 | 229 |

**It racked more glasses than any other solution in the book, in half the
pushes of the geometry it was measured against.** The ranked geometry had to
repeat 109 of its 229 pushes; this solution repeated 14 of its 114. That is what
a usable prediction buys: a push aimed with a model of where the glass will stop
does not need to be tried again.

It also finished the same number of tables, not more, and it cost something the
geometry never costs. **It toppled one glass and lost one table to a state the
cell should never reach.** A toppled glass is the one failure this cell cannot
take back, so the two rows are not ordered on a single number. Replacing a rule
that refuses whenever the arithmetic is unsure with a model that predicts an
outcome means the model is right more often and also occasionally confidently
wrong.

Read together with the geometry's own finding — that its ranker, fitted on *how
much a push helps*, lost to the printed rule it was meant to improve — this row
gives the book its clearest conclusion. **The learning that paid attacked the
quantity the geometry gets wrong, not the quantity it gets right.** So the
useful question is not whether to learn, but which quantity is worth learning.
The full table for all six solutions is in [the results](../10_the-results.md).

## 5. Where it is strong and where it breaks

It could plan a sequence, and nothing else here could. Its model needs no
written physics and therefore no guessed friction, which means it also absorbs
the things nobody thought to write down. It knows where it is ignorant, and
knows it cheaply, from the disagreement between the five copies. Its training
data costs no human time. And the same model serves a different goal: change
the arithmetic that scores a predicted table and the solution aims somewhere
else, with no retraining at all, where a learned policy would have to be
trained again.

Against that, four weaknesses.

It can be confidently wrong, and that is its worst failure. Where the training
data is thin in a way the copies did not notice, all five agree and are wrong
together. The topples recorded while it was being tuned were exactly this: the
model had rated every one of them safe, and a stricter limit does not catch
that.

Its model is only as wide as its encoding, which is five neighbours, four
measurements each, and no representation of the jaw's body. Anything those
numbers cannot express cannot be learned however much data is collected, and
most of the recorded failure causes are of that kind.

It is slow at run time, because hundreds of model calls per push is the price
of searching rather than answering, and it compounds error over depth, which
caps how far a sequence could usefully be planned.

And it cannot be inspected the way written geometry can. It is the most
machinery of the six — a data collector, a trainer, an ensemble, a search and a
loop — against a page of arithmetic.

## 6. When to choose it

Choose this when the thing you cannot write down is *what your actions do*, and
when a simulator can produce the examples. Those two conditions together are
what make it work here: friction is unknown, and the examiner will make thirty-eight
thousand pushes in under an hour for nothing. In that position learning the
forward model is the highest-value thing to learn, because everything else — the
choosing, the scoring, the goal — can stay as arithmetic a person wrote and can
be changed without retraining.

Choose it also when the goal is likely to change, because this is the only
solution here that can be re-aimed by editing a scoring function.

Do not choose it when a rule already predicts your actions well enough, because
then you are fitting a model of something you already know, which is what the
ranked geometry did and why it lost. Do not choose it where a confidently wrong
prediction is unacceptable unless something outside the model can veto it: on
this examiner the missing arithmetic gate in front of the planner is exactly what
the one toppled glass cost. And do not choose it when the run-time budget is
tight, because searching is hundreds of times more expensive than answering.

The code is in
[`src/09_pushing-the-glasses-apart/04-a-world-model/`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model)
and it writes its own `results.json` beside itself. The full treatment, with the
push's own frame explained, ensembles as a measure of ignorance, the sampling
search, and the sequence this solution alone could plan, starts at [what it
is](../07_a-world-model-then-plan-with-it/01_what-it-is.md).

← [Imitation from demonstrations](04_imitation-from-demonstrations.md) · [A foundation model as it downloads](06_a-foundation-model-as-it-downloads.md) →
