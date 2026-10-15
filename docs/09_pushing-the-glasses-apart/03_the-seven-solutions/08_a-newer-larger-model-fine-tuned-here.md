# A newer, larger model, fine-tuned here

This page is a short summary of the seventh solution. It is [the same model,
fine-tuned here](07_the-same-model-fine-tuned-here.md) with one change: a newer
and larger borrowed model, Evo-1. **This solution is still being measured.** So
this page has no score yet. The full story is in [the chapter on this
solution](../10_a-newer-larger-model-fine-tuned-here/01_what-it-is.md).

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)

## 1. What it is

Evo-1 is a vision-language-action model, like SmolVLA. It was published in
November 2025. It has about 775 million numbers, about 70% more than SmolVLA.
Solution 7 changes only the model. So the gap from solution 6 shows what the
model is worth.

The next section says how it is trained.

## 2. How it works

This section says what is trained and what is shared.

Only the action half of Evo-1 is trained. The picture-and-text half is frozen.
The demonstrations, the training effort and the loop over a table are
solution 6's and solution 5's own. Two things differ, because the model forces
them. The picture is scaled from 384 to 448 pixels. And the model answers 24
numbers a waypoint, which are trimmed to 6. [What it
is](../10_a-newer-larger-model-fine-tuned-here/01_what-it-is.md) explains each
part. The next section says what this costs.

## 3. What it needs

This section gives the measured costs.

It fits 122.0 million of 775.2 million numbers. It holds 3.60 GiB while
answering. It needs no NVIDIA card and no change to Evo-1's code. [What it
needs](../10_a-newer-larger-model-fine-tuned-here/02_what-it-needs.md) gives the
details. The next section says what it scored.

## 4. What it scored

**Being measured.** The three fits and the scoring run are under way. [The
results page of this
chapter](../10_a-newer-larger-model-fine-tuned-here/03_results.md) says where
the score will appear.

← [The same model, fine-tuned here](07_the-same-model-fine-tuned-here.md) · [Questions and answers](09_questions-and-answers.md) →
