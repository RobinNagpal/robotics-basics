# Questions and answers

This page answers common questions about imitation from demonstrations. Each
answer is short. Each one links to the section of this chapter that explains it
in full.

## Contents

1. [What does solution 3 learn, and what is action chunking?](#1-what-does-solution-3-learn-and-what-is-action-chunking)
2. [What is a demonstration here, and who records it?](#2-what-is-a-demonstration-here-and-who-records-it)
3. [Why are demonstrations free here, and why would they not be free on a real arm?](#3-why-are-demonstrations-free-here-and-why-would-they-not-be-free-on-a-real-arm)
4. [What is behaviour cloning?](#4-what-is-behaviour-cloning)
5. [What is a demonstration band, and why must two solutions share one before they are compared?](#5-what-is-a-demonstration-band-and-why-must-two-solutions-share-one-before-they-are-compared)
6. [Why must the teacher's own training tables be kept out of the band?](#6-why-must-the-teachers-own-training-tables-be-kept-out-of-the-band)
7. [Why is keeping only the successful pushes a problem, and how big is the problem here?](#7-why-is-keeping-only-the-successful-pushes-a-problem-and-how-big-is-the-problem-here)
8. [What is DAgger?](#8-what-is-dagger)
9. [Why does a policy that learned the right push still bring the jaw down on top of a glass?](#9-why-does-a-policy-that-learned-the-right-push-still-bring-the-jaw-down-on-top-of-a-glass)
10. [What did giving solution 3 the camera's readings change?](#10-what-did-giving-solution-3-the-cameras-readings-change)
11. [Would a larger push budget help solution 3?](#11-would-a-larger-push-budget-help-solution-3)

## 1. What does solution 3 learn, and what is action chunking?

It learns to map a picture of the table to the next push. The push comes out as
an **action chunk**: a short run of jaw waypoints, predicted together in one
pass. The arm follows the whole chunk, then looks again. [Action
chunking](03_how-it-works.md#4-action-chunking-and-why-it-matters) explains why
a push needs this.

## 2. What is a demonstration here, and who records it?

A demonstration is one push made by the teacher, solution 2. It holds the
picture before the push, the waypoints the jaw followed, and the examiner's
verdict. The examiner records all three while the teacher runs. [Where the
demonstrations come from](03_how-it-works.md#2-where-the-demonstrations-come-from)
gives the details.

## 3. Why are demonstrations free here, and why would they not be free on a real arm?

Here the teacher is a program, and the tables are simulated. So the only cost
is simulated arm time. On a real arm, a person usually has to guide the arm by
hand for every example. That is often the largest cost of the whole method.
[Where the demonstrations come from](03_how-it-works.md#2-where-the-demonstrations-come-from)
explains both cases.

## 4. What is behaviour cloning?

Behaviour cloning means learning a skill by copying examples. Each example is a
pair: what was seen, and what was done. A network is trained to give the same
action for the same situation. [Behaviour
cloning](03_how-it-works.md#1-behaviour-cloning--learning-a-policy-by-copying)
explains what it needs and where it fails.

## 5. What is a demonstration band, and why must two solutions share one before they are compared?

A demonstration band is the run of table numbers that the examples come from.
This solution uses tables 1000 to 6199. If two solutions learn from different
bands, a gap between them may come from the data, not the method. [Where the
demonstrations come from](03_how-it-works.md#2-where-the-demonstrations-come-from)
says why solution 6 now uses this band.

## 6. Why must the teacher's own training tables be kept out of the band?

The teacher's ranker was fitted on tables 0 to 199. On those tables the teacher
does better than it usually does. Examples from them would show the student a
teacher better than the real one. So the band starts at table 1000. [Where the
demonstrations come from](03_how-it-works.md#2-where-the-demonstrations-come-from)
gives the bands.

## 7. Why is keeping only the successful pushes a problem, and how big is the problem here?

Dropping failed pushes also drops the tables where the teacher often fails. So
the student sees fewest examples where help is most needed. Here the effect is
small. Of 13,063 real pushes, only 407 were dropped, about 3%. [Choosing which
demonstrations to keep](03_how-it-works.md#3-choosing-which-demonstrations-to-keep-and-the-bias-it-buys)
explains the bias.

## 8. What is DAgger?

DAgger means dataset aggregation. Run the policy, and ask the teacher what it
would have done at each state the policy reaches. Add those answers to the data
and train again. It is cheap here because the teacher is a program, but it is
not built yet. [Compounding error](03_how-it-works.md#6-compounding-error)
explains why it is needed.

## 9. Why does a policy that learned the right push still bring the jaw down on top of a glass?

The policy starts its chunk in about the right place, but points it 22 to 27
degrees off. The hand is long. Turning it that far swings the hand's body
over a neighbour glass.
The jaw drops straight down and meets that glass before the push begins. [A
worked example](04_a-worked-example.md#2-a-worked-example) gives the numbers.

## 10. What did giving solution 3 the camera's readings change?

It made the policy more consistent, but not better. Glasses racked went from
59.3 to 61.3, which is within the normal spread. The spread between runs halved,
and every run cleared three tables. Blocked descents did not fall. [Telling the
policy where the glasses
are](04_a-worked-example.md#5-telling-the-policy-where-the-glasses-are) gives
the table.

## 11. Would a larger push budget help solution 3?

No. Eight times the budget added one or two glasses out of 251. The pushes rose
from about 440 to about 3,000. Most extra pushes were blocked on the way down,
just like the first ones. [More pushes would not
help](04_a-worked-example.md#3-more-pushes-would-not-help) gives the table.

← [How it compares](06_how-it-compares.md) · [A world model, then plan with it — what it is](../07_a-world-model-then-plan-with-it/01_what-it-is.md) →
