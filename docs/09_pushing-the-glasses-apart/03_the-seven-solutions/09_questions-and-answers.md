# Questions and answers

This page answers four questions about the seven solutions as a group. It is
for a reader who has read the short pages of this chapter. Each answer is short.
It links to the page that explains the idea in full.

## Contents

1. [What are the seven solutions, in one line each?](#1-what-are-the-seven-solutions-in-one-line-each)
2. [Why are there seven solutions instead of one good one?](#2-why-are-there-seven-solutions-instead-of-one-good-one)
3. [What does each pair of solutions compare, and why is that worth more than a ranking?](#3-what-does-each-pair-of-solutions-compare-and-why-is-that-worth-more-than-a-ranking)
4. [Why do the learned solutions score below the plain geometry, and what would it take to beat it?](#4-why-do-the-learned-solutions-score-below-the-plain-geometry-and-what-would-it-take-to-beat-it)

## 1. What are the seven solutions, in one line each?

1. A printed rule takes the shortest safe push.
2. A trained model puts the same safe pushes in order.
3. A network copies solution 2's pushes from a picture.
4. A learned model predicts each push, and a search picks the best.
5. A borrowed robot model is used as it downloads.
6. The same borrowed model is trained a little on this cell's pushes.
7. A newer, larger borrowed model is trained the same way.

[How each one works](01_how-the-six-compare.md#4-how-each-one-works) gives a
fuller line for each.

## 2. Why are there seven solutions instead of one good one?

One solution would give one score and no reason for it. Seven solutions put the
learning in seven different places. Each one is a test of where learning helps.
[The introduction to this chapter](01_how-the-six-compare.md#1-introduction)
says this in full.

## 3. What does each pair of solutions compare, and why is that worth more than a ranking?

Each pair differs in one thing, so the gap in score is that thing's worth.
Solution 1 against 2 asks whether ranking safe pushes helps. Solution 3 against
4 asks whether to copy pushes or to plan with a model. Solution 5 against 6 asks
what training buys. Solution 6 against 7 asks what a newer, larger model buys.
A ranking says who won. A pair says why. [What the comparison
says](../11_the-results.md#5-what-the-comparison-says) reads each pair.

## 4. Why do the learned solutions score below the plain geometry, and what would it take to beat it?

Most of them do. Solutions 3, 5 and 6 rack fewer glasses and topple more. They
make the push themselves, and the jaw often comes down on a glass. Solution 4
racks more glasses than the geometry, but it topples 20 where the geometry
topples 1. To beat the geometry, a model must learn what the geometry gets
wrong: where a pushed glass stops. [What the comparison
says](../11_the-results.md#5-what-the-comparison-says) gives the evidence.

← [A newer, larger model, fine-tuned here](08_a-newer-larger-model-fine-tuned-here.md) · [One fixed nudge — what it is](../04_one-fixed-nudge/01_what-it-is.md) →
