# The same model, fine-tuned here

This page is a short summary of the sixth solution. It uses the same model and
the same downloaded weights as [a foundation model as it
downloads](06_a-foundation-model-as-it-downloads.md). It adds one thing: a small
correction learned from pushes on this cell's tables. The page says what it
does, what it scored, and its one main lesson. The full story is in [the
chapter on this solution](../09_the-same-model-fine-tuned-here/01_what-it-is.md).

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

**Fine-tuning** means you keep a model's weights and train them a little more
on your own examples. The model keeps what it knew, and it moves towards your
task.

This solution uses **low-rank adaptation**. It learns a small correction of
about four million numbers, and leaves the rest of the model alone. The
examples come from [geometry generates, a model
ranks](03_geometry-generates-a-model-ranks.md).

![The same chain as the borrowed model with a training step put in front: the teacher records its pushes, the failures are dropped, and a small correction is fitted so the chunks come out in this cell's own range, after which the shared geometry still refuses the glasses that tip before they slide.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-what-it-does.png)

The next section shows the steps from the teacher's pushes to the model's
pushes.

## 2. How it works

This section follows the data through the solution in order.

1. The teacher's pushes on the training tables are recorded. Failed pushes
   are dropped.
2. The correction is trained to copy the teacher's pushes.
3. At run time the steps are the same as for the downloaded model. A shared
   rule still refuses the glasses that would tip.

[How it
works](../09_the-same-model-fine-tuned-here/03_how-it-works.md) explains each
step. The next section says what this costs.

## 3. What it needs

This section lists the cost of the solution before we look at its score.

It needs LeRobot, the SmolVLA weights, and a working teacher. Training ran on a
laptop, so no rented hardware was needed. But it ran only about one part in 300
of the training the library suggests. So every score below comes with that
warning. [What it
needs](../09_the-same-model-fine-tuned-here/05_what-it-needs.md) gives the
details. The next section shows what this training bought.

## 4. What it scored

This section puts the two halves of the pair side by side. Both had the same 50
tables. Each was run three times, and the table shows the middle run.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| this solution, fine-tuned | 1 | 36 | 56 | 40 | 369 |
| the same model, as it downloads | 1 | 9 | 48 | 12 | 620 |

The training worked, and the score got worse. Both are true. The training
brought the jaw down from hovering too high to the right height for a push. But
the model did not learn where to put the jaw down. So about three in five of
its pushes hit a neighbour on the way down.

These numbers come from the first fit, on 1,074 demonstrations. A later fit
used six and a half times as many, with three seeds. [It changed
nothing](../09_the-same-model-fine-tuned-here/06_how-it-compares.md#4-more-demonstrations-and-a-result-that-did-not-come-back).

[How it compares](../09_the-same-model-fine-tuned-here/06_how-it-compares.md)
shows where the pushes went. The six measured scores are in [the
results](../11_the-results.md). The next section says what this score teaches.

## 5. Where it is strong and where it breaks

This section uses the score above to show the method's good and bad sides.

It is trained on the kind of picture it sees at run time, and its examples are
free. But it can never beat its teacher. It never saw a refusal, so it tries to
push glasses that must not be pushed. [How it
compares](../09_the-same-model-fine-tuned-here/06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
gives the evidence. The next section turns this into advice.

## 6. When to choose it

This section says when this method is the right choice.

Choose it when a borrowed model nearly works, the examples are cheap, and
something outside the model can stop it doing damage. Here the safety rule
checks whether a glass may be pushed. Nothing checks whether the model's own
path is safe. That gap cost 40 toppled glasses in a run.

Do not judge the method on this much training. One part in 300 is not a fair
test. More demonstrations did not help, so more training steps and DAgger are
the next things to try.

The main lesson is this. A model that does nothing can score better than a
model that does the wrong thing. The training gave the model enough skill to
act, but not enough to act safely.

The code is in
[`src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned).
The full chapter starts at [what it
is](../09_the-same-model-fine-tuned-here/01_what-it-is.md).

← [A foundation model as it downloads](06_a-foundation-model-as-it-downloads.md) · [A newer, larger model, fine-tuned here](08_a-newer-larger-model-fine-tuned-here.md) →
