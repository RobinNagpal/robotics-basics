# Imitation from demonstrations

This page describes the third of the six solutions in about eight minutes of
reading. It is the first one in which everything is fitted here from nothing:
the arm is shown what a good push looks like, many times over, and a network is
trained to copy it, with no geometry and no friction model anywhere inside it.
By the end of this page you will know what behaviour cloning is, where the
demonstrations come from and what that costs, what it scored on the shared test
examiner, and the one limit no amount of extra data removes. The full treatment is
in [the chapter on this
solution](../06_imitation-from-demonstrations/01_what-it-is.md), which is about
an hour of reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored by the examiner](#4-what-it-scored-on-the-examiner)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

**Behaviour cloning** is the simplest way to learn a skill from examples. You
collect many pairs of a situation and the action a competent performer took in
it, and then you fit a function that maps a situation to an action. Nothing in
the procedure ever asks whether the action was a good one; the examples are
taken as correct by definition, and the fitting extracts whatever pattern they
contain.

This solution does that for pushing glasses. A view of the table from the top
goes in, and a short run of jaw waypoints comes out. Nobody writes down how to
push a glass: the examples carry that knowledge and the fitting extracts it. Of
the six, this is the one that demands the least prior understanding of the task
from whoever builds it.

The model is **ACT**, an action chunking transformer, taken from
[LeRobot](https://github.com/huggingface/lerobot) and fitted here from random
numbers. A second rung uses **Diffusion Policy**, also in LeRobot, which reaches
the same kind of answer by starting from noise and denoising towards an answer.
Nothing is downloaded except the library.

The demonstrations come from [geometry generates, a model
ranks](03_geometry-generates-a-model-ranks.md), which is a program rather than a
person, so they cost arm time on the examiner's tables and nothing else. That makes this
solution's teacher a sibling solution, and the consequence of that is the most
important thing on this page.

## 2. How it works

**The teacher produces the examples.** The ranked geometric solution runs over
the training half of the examiner's tables, and each push it makes is recorded as a
picture of the table together with the waypoints the jaw followed.

**The successful pushes are kept and the rest are dropped.** This filtering is
necessary, because a cloned policy copies failures as readily as successes. It
is also a bias, and the full chapter is careful about it: keeping only what
worked thins the dataset exactly in the situations where the teacher struggled,
so the student is fitted most densely where help was least needed.

**The network is fitted to map a picture to a chunk.** An **action chunk** is a
short run of consecutive jaw waypoints predicted together in one pass, rather
than one waypoint at a time. Predicting a run at once matters because
consecutive waypoints in a push are strongly related, and a model asked for them
one at a time has to rediscover that relationship at every step while its own
small errors accumulate.

**At run time the chunk is carried out directly.** There is nothing to expand,
because a chunk already *is* a jaw trajectory, so the examiner follows the
waypoints as given. The arm then looks again, and the fresh picture is the next
input. One push is one chunk, and the loop runs until every glass has room, the
remaining glasses have been refused, or the push budget is spent.

The limit built into all of this is worth stating before the scores. **Nothing
in behaviour cloning ever evaluates an outcome**, so this solution cannot
discover that a different glass should have been moved or a different
destination chosen. It can smooth away some of the teacher's inconsistency,
because a fitted function averages over many examples, and it can express
motions the examiner's push macro could not. Beyond those two narrow things, its
ceiling is its teacher.

## 3. What it needs

It needs **LeRobot** and **PyTorch**. LeRobot is Apache-2.0, and because this
solution downloads no weights, the weights file it produces inherits no terms
from anybody. That is as simple as a licence position gets in this book.

It needs **its teacher working**, which is a real dependency rather than a
preference: without a program that chooses pushes well there are no
demonstrations at all, which is why the two are built in that order.

It needed **two things the examiner did not have**, and that was an honest cost of
going off the shelf. The examiner returned numeric readings and rendered the world
only from the arm's side, so a straight-down view of the table had to be built.
And the examiner's push entry point takes three numbers and expands them itself, so
a path that accepts a chunk of waypoints had to be built too. Both exist now,
and every LeRobot policy would have needed them, because they all expect
pictures and a control-rate action space.

It needs **demonstrations**, which cost arm time and nothing else, drawn only
from tables below the examiner's dividing line. One prescription here is **not**
done and is worth knowing: the plan was to over-represent the crowded corner
cases deliberately, so the edge of what the policy will face sits in the middle
of what it was trained on, and in fact the demonstrations are drawn from
consecutive table numbers, so the crowded corners are as rare in training as
they are on the examiner's tables.

It needs **compute, and this is the cheapest entry among the six.** Training
runs in hours on the graphics processor an Apple M4 already has. This document
first budgeted tens of dollars for a rented accelerator and in the event none
was needed, because the dataset is thousands of small pictures, the network is
small beside a foundation model, and nothing has to be learned about vision in
general.

At run time it needs one forward pass per chunk, against a push the arm takes
seconds to carry out. And once fitted it needs **a weights file kept in step
with the examiner**: change how the top view is rendered, or the macro whose
waypoints became the labels, and the file is quietly out of date.

## 4. What it scored by the examiner

All six solutions are given the same 50 tables holding 251 glasses, of which 193
have no room at the start. The teacher's row is shown beside this one, because
student against teacher is what this pairing is for. This solution is run
several times and the figure shown is the middle one.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| this solution (ACT) | 3 | 1 | 68 | 1 | 643 |
| its teacher, the ranked geometry | 31 | 0 | 185 | 0 | 229 |

**The student fell far short of its teacher**, finishing 3 tables against 31 and
spending nearly three times the pushes to do it. It also toppled a glass, which
the geometry never does.

The reason was measured rather than guessed, and it is specific. **It places the
start of a push roughly right and gets the heading about thirty degrees out**,
and the jaw then meets a neighbour on the way down instead of reaching the glass
it was aiming at. Fitting it on four times the demonstrations removed the
memorising but not the averaging, which says the shortfall is **the policy
averaging over pushes that disagree**, not a shortage of examples. When several
good pushes point in different directions from a similar-looking table, a
function fitted to copy them all returns something between them, and something
between two good pushes is not a good push.

That is useful to know, because it tells you what to change. More data is the
wrong lever. A model that can represent several different answers to the same
situation, rather than averaging them, is the right one — which is exactly what
the second rung, Diffusion Policy, is for. The full table for all six solutions
is in [the results](../10_the-results.md).

## 5. Where it is strong and where it breaks

**Nothing has to be written about pushing**: no friction model, no candidate
generator, no features chosen by hand, no geometry. **The output is native**, so
nothing is squeezed or expanded on the way out. **Labels are free and
plentiful**, because the teacher is code and the tables are simulated, so the
usual reason not to attempt imitation learning does not apply. **It is cheap to
train and cheap to run.** And **it is a measurement** — student against teacher,
on the same tables with the same scorecard — which would have earned its place
even if the solution were not carried forward.

Against that, five weaknesses, of which the first three cannot be engineered
away.

**The ceiling is the teacher's quality**, for the reason given above: no
mechanism in this solution compares one outcome against another.

**Filtering the demonstrations biases it towards what the teacher does well.**

**It is open-loop inside a chunk, and it cannot refuse.** During a chunk nothing
is read, and the policy's only output is waypoints, so a refusal has to come
from the shared gate in front of it rather than from the policy itself.

**It needed examiner work the first two solutions did not**, and two smaller costs
are paid on every push: a glass and an aim have to be read back off the
waypoints, and every chunk has to be pulled inside the jaw's limits before it is
followed.

**And it cannot explain itself, or say when it is lost.** It has no confidence
output, and the situation in which it is least reliable — a table unlike
anything in its data — is indistinguishable in its output from the situation in
which it is most reliable.

## 6. When to choose it

Choose behaviour cloning when a competent demonstrator already exists and the
mapping from situation to action is the only thing missing. That is a common
position in practice: a working but slow or expensive procedure can be distilled
into a fast network that imitates it, and the result runs in one forward pass.

Do not choose it to exceed the demonstrator. Nothing in the method can, because
nothing in it evaluates an outcome. If what you need is a better choice than the
teacher makes, you need a method that can compare outcomes, which is [a world
model, then plan with it](05_a-world-model-then-plan-with-it.md).

Do not choose it, either, where several good answers exist for one situation
unless the model can represent more than one of them. That is the failure
measured here, and it is the single most transferable lesson on this page: a
policy fitted to copy disagreeing examples returns their average, and an average
of good actions is often not an action at all.

The code is in
[`src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations/`](../../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations)
and it writes its own `results.json` beside itself. The full treatment, with
behaviour cloning explained, the bias the filtering buys, why action chunking
matters, and the compounding error inside a chunk, starts at [what it
is](../06_imitation-from-demonstrations/01_what-it-is.md).

← [Geometry generates, a model ranks](03_geometry-generates-a-model-ranks.md) · [A world model, then plan with it](05_a-world-model-then-plan-with-it.md) →
