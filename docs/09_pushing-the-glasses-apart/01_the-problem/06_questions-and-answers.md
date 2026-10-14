# Questions and answers

## 1. Introduction

This page answers four questions that readers ask after the pages before it. It
is for a reader who knows the shape of the problem and wants the exact sizes.
Each answer is short and links to the page that explains it in full. Every
number here was printed by the code.

## Contents

1. [Introduction](#1-introduction)
2. [What does a look give back, and what shape is it in?](#2-what-does-a-look-give-back-and-what-shape-is-it-in)
3. [What does a push take, and what shape is it in?](#3-what-does-a-push-take-and-what-shape-is-it-in)
4. [How many looks and pushes is a solution allowed?](#4-how-many-looks-and-pushes-is-a-solution-allowed)
5. [How many runs are there altogether?](#5-how-many-runs-are-there-altogether)

## 2. What does a look give back, and what shape is it in?

A look gives back a list with one row for each glass on the table. Each row has
seven fields: the glass's number, its x and y position, its height, its widest
diameter, its foot width, and whether it is standing. Lengths are in metres.
Each look adds a new small error to the numbers. Three of the six solutions get
a 384 by 384 colour picture from above instead. [What `look()` hands
over](02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over) explains
the fields and the error.

A look at table 10025 starts like this:

```json
[
  {"id": 0, "x": 0.4570, "y": -0.4170, "height": 0.1554, "widest": 0.0740, "foot": 0.0419, "standing": true},
  {"id": 1, "x": 0.5489, "y": -0.2464, "height": 0.1360, "widest": 0.0871, "foot": 0.0462, "standing": true}
]
```

## 3. What does a push take, and what shape is it in?

A push is one object with six fields. They say which glass to move, where the
fingertips come down, the heading of the hand, how far to feel forward, how far
to push after touching, and where the solution expects the glass to stop.
Lengths are in metres and the heading is in radians. The examiner turns every
push into the same moves for all six solutions. The reply has five fields, and
it is the only thing a solution learns about its push. [What `push()` does, and
what it reports
back](02_what-goes-in-and-what-comes-out.md#5-what-push-does-and-what-it-reports-back)
explains each field.

Here is one push on table 10025, and the reply to it. The force is in newtons.

```json
{"glass": 4, "start": [0.3726, -0.4500], "heading": 1.5708, "reach": 0.0881, "travel": 0.0660,
 "aim": [0.3726, -0.3259]}
```

```json
{"blocked": false, "touched": 0.0146, "jammed": false, "peak": 1.73, "pushed": 0.0660}
```

## 4. How many looks and pushes is a solution allowed?

A solution may use 16 pushes on one table, and 4 pushes on any one glass. Looks
have no limit. The limits are the same for all six solutions. When a limit is
reached, every glass still standing is refused with a reason. Pushes are limited
because a push can knock a glass over, and a look cannot. [What the examiner
measures](03_the-examiner.md#5-what-the-examiner-measures) explains how pushes
and thinking time are counted.

## 5. How many runs are there altogether?

One run is the same 50 tables, with 251 glasses in total. No solution is
trained on them. Solutions 1, 2 and 4 run once, because they give the same
answer every time. The other three pick actions at random, so each runs three
times and reports the spread. [Two things this scorecard
needs](03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why one run is not enough. [The results](../10_the-results.md) prints
the spread for all three.

← [Pushing without toppling](05_pushing-without-toppling.md) · [The six solutions — same table, six ways to push](../03_the-six-solutions/01_how-the-six-compare.md) →
