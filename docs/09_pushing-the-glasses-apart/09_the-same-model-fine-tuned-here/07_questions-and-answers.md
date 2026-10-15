# Questions and answers

This page answers the questions a reader most often asks about this solution.
Each answer is short. Each one links to the section that explains it in full.

## Contents

1. [What does solution 6 change about solution 5, and why only that one thing?](#1-what-does-solution-6-change-about-solution-5-and-why-only-that-one-thing)
2. [What is fine-tuning?](#2-what-is-fine-tuning)
3. [What is low-rank adaptation, and why is changing a few weights enough?](#3-what-is-low-rank-adaptation-and-why-is-changing-a-few-weights-enough)
4. [What is catastrophic forgetting, and why is it less likely here but still possible?](#4-what-is-catastrophic-forgetting-and-why-is-it-less-likely-here-but-still-possible)
5. [Does fine-tuning make the solution slower to run?](#5-does-fine-tuning-make-the-solution-slower-to-run)
6. [Why did six and a half times as many demonstrations change nothing?](#6-why-did-six-and-a-half-times-as-many-demonstrations-change-nothing)

## 1. What does solution 6 change about solution 5, and why only that one thing?

It adds training on pushes made in this cell. The model, the weights, the
picture and the scorecard stay the same. Only one thing changes, so the gap
in score measures what the training bought. [Whether anything but the training
differs](03_how-it-works.md#4-whether-anything-but-the-training-differs) checks
this.

## 2. What is fine-tuning?

Fine-tuning means you start from weights that someone else trained. Then you
train them a little more on your own examples. The model keeps what it knew
and moves towards your task. [Fine-tuning](03_how-it-works.md#1-fine-tuning--continuing-somebody-elses-training)
explains it in full.

## 3. What is low-rank adaptation, and why is changing a few weights enough?

Low-rank adaptation leaves every borrowed weight as it is. It learns a small
correction beside them, here about four million numbers out of about 450
million. That fits on a laptop. It may not be enough for a task this far from
the old ones. [Low-rank
adaptation](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
explains this.

## 4. What is catastrophic forgetting, and why is it less likely here but still possible?

A model trained on a new task tends to lose what it knew before. Here the
borrowed weights are never overwritten, so removing the correction gives the
old model back. But the corrected model is the one that runs, and it is worse
on other robots. [Two ways training goes
wrong](03_how-it-works.md#6-two-ways-training-on-one-cells-pushes-goes-wrong)
explains this.

## 5. Does fine-tuning make the solution slower to run?

No. After training, the correction is added into the borrowed weights. So the
trained model does the same work as solution 5's model. [Low-rank
adaptation](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
explains why. One run looked slower, but [it shared the graphics chip with
another fit](06_how-it-compares.md#4-more-demonstrations-and-a-result-that-did-not-come-back).

## 6. Why did six and a half times as many demonstrations change nothing?

The model fails because its jaw comes down onto a glass. The teacher never
does that. So no demonstration shows the way out, however many there are. More
of the same examples do not teach a new state. [More
demonstrations](06_how-it-compares.md#4-more-demonstrations-and-a-result-that-did-not-come-back)
gives the measurement.

← [How it compares](06_how-it-compares.md) · [A newer, larger model fine-tuned here — what it is](../10_a-newer-larger-model-fine-tuned-here/01_what-it-is.md) →
