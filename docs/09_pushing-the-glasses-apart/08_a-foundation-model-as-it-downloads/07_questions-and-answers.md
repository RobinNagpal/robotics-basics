# Questions and answers

This page answers six questions a reader may still have after this chapter.
Each answer is short. It links to the section that explains it in full.

## Contents

1. [What is a foundation model, and why does solution 5 use one with no training?](#1-what-is-a-foundation-model-and-why-does-solution-5-use-one-with-no-training)
2. [What does it mean to borrow a model, and what does the borrowed model already know?](#2-what-does-it-mean-to-borrow-a-model-and-what-does-the-borrowed-model-already-know)
3. [What is the domain gap, and how does it show in this cell?](#3-what-is-the-domain-gap-and-how-does-it-show-in-this-cell)
4. [What is flow matching?](#4-what-is-flow-matching)
5. [Why must a model that draws its answer be measured several times?](#5-why-must-a-model-that-draws-its-answer-be-measured-several-times)
6. [Why must a borrowed model be given the cell's state in fixed slots, and what is permutation invariance?](#6-why-must-a-borrowed-model-be-given-the-cells-state-in-fixed-slots-and-what-is-permutation-invariance)

## 1. What is a foundation model, and why does solution 5 use one with no training?

A foundation model is trained on a very large and broad set of data. It is
meant for tasks nobody planned for. [Robot foundation
models](06_how-it-compares.md#robot-foundation-models--one-model-pretrained-for-manipulation-in-general)
explains the robot kind. Solution 5 trains nothing, because that is the
cheapest test there is. It also makes a clean starting point for solution 6,
which adds training and changes nothing else.

## 2. What does it mean to borrow a model, and what does the borrowed model already know?

To borrow a model is to download its design and its weights, and use them as
they are. [What is borrowed, and what is
not](03_how-it-works.md#3-what-is-borrowed-and-what-is-not) lists each part.
The model has seen many real robots handle objects. So it knows how handling
usually goes. It knows nothing about this cell, as [where such a model gets its
competence](03_how-it-works.md#2-where-such-a-model-gets-its-competence) says.

## 3. What is the domain gap, and how does it show in this cell?

The [domain
gap](03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
is the difference between the data a model learned from and the data it is
used on. SmolVLA learned from real photos, but here it sees drawn shapes. So it
mostly holds the jaw too high, and most pushes touch nothing. [What
happened](03_how-it-works.md#8-what-was-expected-and-what-happened) gives the
counts.

## 4. What is flow matching?

Flow matching is how SmolVLA makes its answer. It starts from random noise. It
moves that noise, step by step, towards a run of actions. The noise is new each
time, so the same picture can get a different answer. [How the model draws its
answer](03_how-it-works.md#how-the-model-draws-its-answer-flow-matching)
explains it.

## 5. Why must a model that draws its answer be measured several times?

The model draws each answer from fresh noise. So two runs on the same tables
give different scores. One run could be lucky or unlucky. Solution 5 was run
three times, and it racked 48, 51 and 46 glasses. [The pushes are what this
contributes](02_the-code.md#2-the-pushes-are-what-this-contributes) gives this
spread.

## 6. Why must a borrowed model be given the cell's state in fixed slots, and what is permutation invariance?

Each input slot of a borrowed model means one thing, fixed when it was trained.
So the jaw's pose always goes in the same slot, as [the actions arrive with no
units](03_how-it-works.md#4-the-actions-arrive-with-no-units-in-them) explains.
A model is permutation invariant when listing its inputs in another order does
not change its answer. Glasses have no natural order, but SmolVLA sees them in
a picture, not in a list, so the order never comes up.

← [How it compares](06_how-it-compares.md) · [The same foundation model, fine-tuned here — what it is](../09_the-same-model-fine-tuned-here/01_what-it-is.md) →
