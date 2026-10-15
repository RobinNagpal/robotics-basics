# Questions and answers

This page answers two common questions about solution 2. Each answer is short.
Each one links to the place in this chapter that explains it in full.

## Contents

1. [What does solution 2 add to solution 1, and what is a ranker?](#1-what-does-solution-2-add-to-solution-1-and-what-is-a-ranker)
2. [Why is solution 2 called the teacher, and why can a student not do better than its teacher?](#2-why-is-solution-2-called-the-teacher-and-why-can-a-student-not-do-better-than-its-teacher)

## 1. What does solution 2 add to solution 1, and what is a ranker?

Solution 2 lists every safe push for a glass, not just one. A ranker is a
fitted model that puts such a list in order, best first. Here it is a set of
small decision trees. It cannot add a push or bring back an unsafe one. See
[the model](03_how-it-works.md#3-the-model-boosted-trees-that-score-one-candidate-at-a-time).
On 50 tables it racked the same 107 glasses as the printed rule. It used 182
pushes, and the rule used 173.

## 2. Why is solution 2 called the teacher, and why can a student not do better than its teacher?

Its recorded pushes are the examples that solutions 3, 6 and 7 copy. They cost
only simulator time. A student that only copies sees only the pushes this
solution can list. So it cannot learn a better push than these. See [it is the
teacher](03_how-it-works.md#7-it-is-the-teacher).

← [How it compares](06_how-it-compares.md) · [Imitation from demonstrations — what it is](../06_imitation-from-demonstrations/01_what-it-is.md) →
