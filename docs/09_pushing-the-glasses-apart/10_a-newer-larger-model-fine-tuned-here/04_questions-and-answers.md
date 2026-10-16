# Questions and answers

This page answers four common questions about solution 7. Each answer is
short. Each one links to the place in this chapter that explains it in full.

## Contents

1. [What is solution 7, and why add a newer and larger model after six?](#1-what-is-solution-7-and-why-add-a-newer-and-larger-model-after-six)
2. [What does freezing the vision-language half mean, and why is solution 7 fitted that way?](#2-what-does-freezing-the-vision-language-half-mean-and-why-is-solution-7-fitted-that-way)
3. [What happens when the borrowed model refuses the cell's picture size, and why is that recorded?](#3-what-happens-when-the-borrowed-model-refuses-the-cells-picture-size-and-why-is-that-recorded)
4. [Did solution 7 beat solution 6, and does that show which model is better?](#4-did-solution-7-beat-solution-6-and-does-that-show-which-model-is-better)

## 1. What is solution 7, and why add a newer and larger model after six?

Solution 7 is solution 6 with the model swapped for Evo-1. Evo-1 is about 70%
larger and about two years newer than SmolVLA. Everything else is held still.
So the gap between the two scores was meant to show what the model is worth.
See [why add it](01_what-it-is.md#2-why-add-it).

## 2. What does freezing the vision-language half mean, and why is solution 7 fitted that way?

Frozen means those numbers are not changed in training. Only the action half
learns: 122.0 million of 775.2 million numbers. This is Evo-1's own first
training stage, so it is the model used as its authors intended. See [what is
fitted](01_what-it-is.md#3-what-is-fitted).

## 3. What happens when the borrowed model refuses the cell's picture size, and why is that recorded?

Evo-1 accepts only 448-pixel pictures. So the cell's 384-pixel view is scaled
up. This adds no detail, but it is still a difference from solution 6. It is
recorded so that no reader thinks the model was the only change. See [two
differences the model forces](01_what-it-is.md#4-two-differences-the-model-forces).

## 4. Did solution 7 beat solution 6, and does that show which model is better?

No, and no. After 1,000 steps Evo-1's waypoints were still about 288 mm from
the teacher's. Solution 6 reached 90 to 106 mm on the same demonstrations. So
the scoring run was stopped. But Evo-1 fits 32 times as many numbers, from
random values. The fit may simply be too short. See [the
results](03_results.md#1-what-is-being-measured).

← [Results](03_results.md) · [The results of all the solutions](../11_the-results.md) →
