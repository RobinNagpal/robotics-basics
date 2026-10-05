# A foundation model as it downloads

This page describes the fifth of the six solutions in about seven minutes of
reading. It is the cheapest of the six to set up, because nothing in it is
fitted here: a large model that somebody else trained on hundreds of real robot
datasets is downloaded, shown a picture of the table, told in plain English what
to do, and asked for actions. By the end of this page you will know what kind of
model it is, why the instruction it is given does almost no work here, what it
scored on the shared examiner, and why a poor score from it is the
measurement working rather than a disappointment. The full treatment is in [the
chapter on this
solution](../08_a-foundation-model-as-it-downloads/01_what-it-is.md), which is
about three quarters of an hour of reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored by the examiner](#4-what-it-scored-on-the-examiner)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

A **vision-language-action model** is a single network that takes a picture and
an instruction written in ordinary words, and returns robot actions. The three
parts of the name are its three inputs and outputs: it sees, it is told, and it
acts. The idea is that a model trained on a very large and varied collection of
robot recordings learns manipulation in general, so that it can be pointed at a
new task by being told about it rather than by being trained on it.

The model here is **SmolVLA**, taken from
[LeRobot](https://github.com/huggingface/lerobot) exactly as it downloads. It is
about 450 million parameters, uses a few gigabytes while answering, and runs on
a laptop. **Not one number in it is fitted in this cell.**

It exists in this book for one reason above all others. [The same model,
fine-tuned here](07_the-same-model-fine-tuned-here.md) is this same model, from
this same library, starting from these same downloaded weights, with its
training continued on this cell's own pushes. Everything else is held still: the
same examiner, the same input, the same output, the same marking, and the same
refusal rule running first. Nothing varies between the pair except the training,
so the gap between their scores measures what that training bought and nothing
else. No other pair in this book is that clean.

## 2. How it works

The chain is short, which is the point.

**The model is shown the table from the top**, as the examiner renders it, together
with **one instruction written in plain English** and **the arm's own joint
readings**.

**It returns a run of actions**, which are read as waypoints for the jaw and
handed to the examiner. The examiner carries them out directly rather than through the
push macro it owns, because a run of waypoints already is a trajectory.

**Then the arm looks again** and the model is asked once more, until every glass
has its room or the push budget is spent. There is no training step, no data
collection and no fitted parameter anywhere in the design.

Three things about that chain matter more than they look, and the full chapter
is careful about each.

**The actions arrive in somebody else's units.** The model was trained on other
robots, so an interpretation stands between its output and this jaw. A poor
interpretation would be blamed on the model.

**The instruction does almost no work.** This task has exactly one instruction,
so the language half of the model is nearly dead weight here. A model built to
be pointed at many tasks by words is being used as an expensive visuomotor
policy.

**The force reading has nowhere to go.** What the jaw felt is the only evidence
this cell can produce about the friction, and this model has no input for it, so
the one channel that observes friction is closed.

Behind all three sits the **domain gap**, which is the difference between what
the model was trained on and what it is shown. It learned from real cameras in
cluttered rooms, and it is being shown flat pale shapes on an empty rectangle.

## 3. What it needs

Less than anything else in this book, which is the whole point.

**Software.** LeRobot, licensed Apache-2.0, and PyTorch underneath it, licensed
the three-clause Berkeley Software Distribution licence. Both are permissive, so
neither obliges this project to publish
its own source. **The weights carry their own terms**, which a reader taking
this forward should check before anything is shipped, because a licence on
weights is not the same thing as a licence on the library that loads them.
Nothing in this project records what those terms are.

**The weights**, downloaded and used unchanged, about 450 million parameters.

**Hardware: a laptop.** There is nothing to train, so there is no accelerator to
rent for this solution at all. The one case where renting would be sensible is
evaluation throughput rather than capability, because the scorecard asks for
several runs and many forward passes on a laptop take a while.

**Data: none.** No demonstrations, no labels, no held-out set, and nothing to
keep in step with the cell when the cell changes.

**What the examiner had to grow**: a rendered view of the table from the top, and a
path that accepts a run of waypoints without the push macro. Both are shared
with two other solutions, so the cost was paid once for three rather than for
this one.

## 4. What it scored by the examiner

All six solutions are given the same 50 tables holding 251 glasses, of which 193
have no room at the start. This solution is run several times and the figure
shown is the middle one.

| tables done | tables wrong | glasses racked | toppled | pushes | thinking per push |
|---|---|---|---|---|---|
| 0 | 5 | 56 | 6 | 754 | slow |

**It finished no table at all**, racked about a fifth of the glasses, toppled
six of them, and spent more pushes than any solution except one. It is also the
slowest of the six per push, because every decision is a forward pass through a
large network rather than arithmetic.

The reason is specific and was measured rather than guessed. **About nine of its
pushes in ten touch nothing at all**, because the trajectories it returns hold
the jaw well above the glasses. It is not failing to choose a good push; it is
mostly not reaching the table. That is the domain gap arriving exactly as
predicted: the model produces confident, plausible actions, and nothing
downstream looks suspicious until the glasses have not moved.

**A poor score here is the measurement working**, which is worth stating plainly
because it reads like an excuse and is not. The pair this solution belongs to
isolates fine-tuning exactly. If this half had scored well, there would be
little room left for the fine-tuned half to show anything, and the sharpest
question these six were arranged to answer would have had no range to be
answered in. The full table for all six is in [the
results](../10_the-results.md).

## 5. Where it is strong and where it breaks

Its strengths all come from the same source, which is that nothing is fitted.
There is nothing to collect, nothing to train and nothing to keep in step with
the cell, so it can be tried in an afternoon once the examiner's two missing parts
exist. It needs no accelerator. It gives the book a reading on what a borrowed
robot model is worth before anybody spends a week recording pushes, which is a
decision several of the other solutions depend on. And it is the clean half of
the book's sharpest pair, which is a strength that does not depend on it working
at all.

Its weaknesses divide into what the borrowing costs and what it cannot be asked
to do.

What the borrowing costs is accuracy and every lever for improving it. The
domain gap is large, the force reading cannot reach the model, the actions
arrive in somebody else's units, and the language half does no work. What it
cannot be asked to do is anything that needs fitting: it cannot learn from a
push that went wrong, cannot be corrected on the kind of glass it handles worst,
and has no threshold to tune. **The one repair for all of that is to continue
its training on this cell's own pushes**, which is a different solution with a
different name, and that is exactly why the two are written as a pair.

## 6. When to choose it

Choose this first and expect to replace it. Running a public model unchanged is
the cheapest honest measurement of whether the problem needs fitting at all, and
taking that measurement before recording demonstrations is simply good order of
work. On a task close to what such a model was trained on — a real arm, a real
camera, an ordinary room, an everyday object — it is sometimes good enough on
its own, and then nothing more expensive is needed.

Do not choose it when the scene is unlike anything in the model's training, as
here. Do not choose it when the signal that matters is one the model has no
input for, which here is the force the jaw felt. And do not choose it when the
run-time budget is tight, because a forward pass through a large network per
push is hundreds of times the cost of arithmetic.

The honest position is that this is among the first things to run and very
unlikely to be carried forward. **Its value is the comparison it makes possible
rather than the accuracy it delivers.**

The code is in
[`src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads/`](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads)
and it writes its own `results.json` beside itself. The full treatment, with
where such a model gets its competence, why the instruction is nearly dead
weight, and the domain gap set out in full, starts at [what it
is](../08_a-foundation-model-as-it-downloads/01_what-it-is.md).

← [A world model, then plan with it](05_a-world-model-then-plan-with-it.md) · [The same model, fine-tuned here](07_the-same-model-fine-tuned-here.md) →
