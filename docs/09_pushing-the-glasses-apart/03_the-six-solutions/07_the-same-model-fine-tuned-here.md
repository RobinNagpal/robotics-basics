# The same model, fine-tuned here

This page describes the sixth of the six solutions in about eight minutes of
reading. It is the same library, the same model and the same downloaded weights
as [a foundation model as it
downloads](06_a-foundation-model-as-it-downloads.md), with one thing added: a
small correction learned from pushes made on this bench. The pair is the
cleanest comparison in the book, and the answer it gave was not the one the book
expected. By the end of this page you will know what low-rank adaptation is,
what the training cost, what it scored, and why a solution that acts badly can
score worse than one that barely acts at all. The full treatment is in [the
chapter on this
solution](../09_the-same-model-fine-tuned-here/01_what-it-is.md), which is the
longest in the book at about seventy minutes.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored on the bench](#4-what-it-scored-on-the-bench)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

**Fine-tuning** means keeping a model's existing weights and continuing their
training on your own, much smaller, collection of examples, so that the general
competence it arrived with is kept while its behaviour moves towards the job in
front of it. It is the standard repair for a domain gap, and the domain gap in
this pair is severe: the borrowed model learned from real cameras in cluttered
rooms, and it is shown flat shapes on an empty rectangle.

This solution applies that repair using **low-rank adaptation**. Rather than
moving all 450 million of the model's numbers, it learns a small correction —
about four million numbers — and adds it to them. Only the correction carries
gradients and optimiser state, so what has to be held in memory is the model
plus a little, and afterwards the correction folds into the weights so that
running the result costs exactly what running the original cost.

The demonstrations come from [geometry generates, a model
ranks](03_geometry-generates-a-model-ranks.md), the same teacher [imitation from
demonstrations](04_imitation-from-demonstrations.md) learns from. That makes
this solution part of two clean pairs at once: against the borrowed model it
measures what fine-tuning buys, and against the solution fitted here from random
numbers it measures what the borrowed weights were worth.

## 2. How it works

**The teacher records the demonstrations.** The ranked geometric solution runs
over the training half of the tables, unattended, and its pushes are recorded. A
filter discards the recordings in which something went wrong. Nobody holds a
controller at any point.

**The correction is fitted.** The borrowed weights stay as they are and the
low-rank correction is trained to reproduce the teacher's actions, so the chunks
the model emits come out in this cell's own range rather than in whatever range
the borrowed recordings happened to use.

**At run time the chain is the borrowed model's chain.** The view from the top,
one instruction in plain English and the arm's own pose go in. The corrected
model returns an **action chunk**, a short run of consecutive jaw waypoints
predicted together in one pass. The shared geometry refuses the glasses that tip
before they slide, and a chunk whose path would reach one of those is not
carried out. The bench then follows the waypoints directly, the arm looks again,
and the loop repeats.

Three things this solution does **not** do are worth naming, because it is easy
to credit the model with them: it does not refuse, it does not choose
destinations, it does not own the loop, and it does not stop a push that is
going wrong. Each of those belongs to the shared machinery around it.

What fine-tuning closes is the gap between the inputs. What it cannot touch is
the shape of the model — a large fraction of those 450 million numbers serve a
language channel this task does not use — or the fact that nothing in behaviour
cloning ever evaluates an outcome, so the teacher remains the ceiling.

## 3. What it needs

It needs **LeRobot**, which is Apache-2.0, and the SmolVLA weights, which the
library fetches by itself. **The terms on the weights are the thing to read
rather than the terms on the library**, because a file produced by continuing
their training inherits whatever they carried, and no amount of training here
relicenses it.

It needs **its teacher built**, because the teacher's pushes are the training
set, and **simulator time** to record them over the training half of the tables.
It needs the **held-out half** for checking that the policy learned pushing
rather than the tables.

**It does not need a rented accelerator, and this is the place the plan was
wrong.** The training ran on this machine, an Apple Silicon Mac with no NVIDIA
card, holding **1.02 GiB** while it ran, with the borrowed weights, the
correction, the correction's gradients and the optimiser's running averages all
in memory at once. Low-rank adaptation is exactly why. Memory was never close to
being the obstacle.

**What renting would buy here is time, not memory**, and that distinction
matters because time is what this solution is short of. A training step on Metal
takes a second or two where a dedicated card would take a fraction of one, and
the library's own recipe for this model is twenty thousand steps at a batch of
sixty-four. What ran here is a thousand steps at a batch of four, which is about
one part in three hundred of that compute, and **every number this solution
reports carries that caveat**.

## 4. What it scored on the bench

All six solutions are given the same 50 tables holding 251 glasses, of which 193
have no room at the start. Its partner's row is shown beside it, because the
pair is the point. Both are run several times and the figure shown is the middle
one.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| this solution, fine-tuned | 4 | 38 | 77 | 46 | 400 |
| the same model, as it downloads | 0 | 5 | 56 | 6 | 754 |

**The training worked and the score got worse.** Both halves of that sentence
are true, and reading only one of them misreads the pair.

The training worked in the sense that matters: the fine-tuned model's chunks are
much closer to the teacher's than the borrowed model's were, and it brings the
jaw down to the table, where the borrowed model simply hovered above it. It
finishes four tables where its partner finishes none, and it racks half again as
many glasses in half the pushes.

The score got worse because **it learned the height a push happens at without
learning where to put the jaw down.** Two thirds of its pushes are blocked
coming down, and it topples 46 glasses a run where the geometry topples none. Its
partner stays out of the "wrong" column by never reaching a glass at all: it
hovers, achieves little, and is marked correct but incomplete.

So the gap between the two is not a measurement of training buying nothing. It
is a measurement of **training buying enough competence to act and not enough to
act safely**, on a scorecard where a toppled glass cannot be undone. **A policy
that does nothing scores better than a policy that does the wrong thing**, and
any reading of this pair that skips that sentence has misread it.

The honest conclusion about the method is therefore still open, and two things
would move it. More training, since the compute spent here is about one part in
three hundred of what the recipe asks. And DAgger, a method in which the teacher
is asked what it would have done in the states the student actually reaches —
because "the jaw came down on a glass" is precisely a state the teacher never
visits, and so precisely what these demonstrations cannot teach. The full table
for all six is in [the results](../10_the-results.md).

## 5. Where it is strong and where it breaks

**It is fitted on the inputs it will be shown**, which is the single strongest
thing about it and the thing its partner cannot claim. **Its demonstrations cost
nothing**, because the teacher is a program. **It needs no reward function**,
which is a larger advantage than it sounds: a reward is a score, and written as
a fine, "never topple a glass" becomes a price, and a price is a trade the
policy may make. Learning from examples of correct pushes leaves "never topple"
as a constraint rather than a price. **Its training is affordable and its
run-time cost is its partner's**, because the correction folds into the weights.

Against that, four kinds of weakness.

**What it inherits from being a borrowed model.** A large fraction of its
parameters serve a language channel this task does not use. It commits to a
chunk, so a surprise inside a push is carried out anyway. It cannot explain
anything it did. And the correction is low-rank, so it adapts less deeply than a
full fine-tune would, which means the gap it shows is a lower bound on what
fine-tuning could buy.

**What it inherits from its teacher.** Its ceiling is the ranked geometry,
because nothing ever showed it a better push. Its training set was filtered to
successes, so it was fitted on the easy half of its teacher's experience. And it
has seen no refusals at all, so it proposes pushes on glasses that must not be
pushed.

**What it owes to being trained on one bench.** Part of what it gains over its
partner is this bench's own friction absorbed into its weights, which is a
memorised constant rather than an ability, and would not survive a real table.

**What it does not do at all**, which is the list in section 2.

## 6. When to choose it

Choose fine-tuning a foundation policy when a borrowed model nearly works, the
demonstrations are cheap, and **something outside the policy can stop it doing
damage**. That last condition is the one this solution shows the cost of
ignoring. The topple refusal in front of it checks whether a *glass* may be
pushed; nothing checks whether the *chunk the model produced* is safe to carry
out, and 46 toppled glasses a run is what that gap is worth.

Do not choose it on this much compute. One part in three hundred of the
recommended training is not a fair test of the method, and the fair conclusion
from this row is about the amount of training rather than about fine-tuning.

Do not choose it, either, where demonstrations from a working teacher are the
only data available and the student will reach states the teacher never does.
That is the structural flaw here, and the repair is to collect corrections in
the states the student actually visits, not to collect more of the same
demonstrations.

If you read this page for one reason, read it for the pair with its partner.
Same library, same model, same weights, same bench, same input, same output,
same marking, same cost per push, and the only difference is the training. And
read the result carefully, because the obvious reading of it is wrong.

The code is in
[`src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned)
and it writes its own `results.json` beside itself. The full treatment, with
low-rank adaptation explained, where the demonstrations come from, the two ways
training on one cell's pushes goes wrong, and a second rung on a markedly larger
model, starts at [what it
is](../09_the-same-model-fine-tuned-here/01_what-it-is.md).

← [A foundation model as it downloads](06_a-foundation-model-as-it-downloads.md) · [One fixed nudge — what it is](../04_one-fixed-nudge/01_what-it-is.md) →
