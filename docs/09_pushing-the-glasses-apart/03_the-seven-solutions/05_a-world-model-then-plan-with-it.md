# A world model, then plan with it

This page is a short summary of the fourth solution. This solution learns what
a push will do, not which push to make. Then it tries many pushes against what
it learned and picks the best one. The page says what it does, what it scored,
and its one main lesson. The full story is in [the chapter on this
solution](../07_a-world-model-then-plan-with-it/01_what-it-is.md).

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

A **forward model** takes a situation and an action. It returns the situation
that follows. With it, you can compare two actions without doing either one.

This solution fits a forward model of the table. It says where each glass will
end up after a push, and whether anything will fall over.

This is what makes it different. [Geometry generates, a model
ranks](03_geometry-generates-a-model-ranks.md) learns how much a push helps. The
geometry already knows that. This solution learns where a pushed glass will
stop. The geometry gets that wrong, because it does not know the friction.

![Thousands of pushes are made in the simulator and nobody labels any of them, because the answer to every example is what the second look found; five copies of a small network are fitted to say what the table looks like after a push; and before every push the arm makes, candidates are drawn, put to all five, filtered and scored, and only the best one is carried out.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-flow-what-it-does.png)

The next section shows how the model is used to choose a push.

## 2. How it works

This section follows one decision from start to end.

1. Five copies of a small network are trained on the same pushes. Where the
   copies disagree, the training data did not cover that kind of push.
2. Before each push, about 1,500 possible pushes are tried against the copies.
3. A push is dropped if any copy says it might topple a glass.
4. The push that leaves the least missing room is sent to the examiner.

[How it works](../07_a-world-model-then-plan-with-it/03_how-it-works.md)
explains each step. The next section says what this costs.

## 3. What it needs

This section lists the cost of the solution before we look at its score.

It needs tens of thousands of pushes made in the simulator. Nobody has to label
them, because the answer is what the camera saw after each push. Training takes
about half an hour on a laptop. [What it
needs](../07_a-world-model-then-plan-with-it/05_what-it-needs.md) gives the
details. The next section shows what this cost bought.

## 4. What it scored

This section puts this solution beside the ranked geometry, because the pair
answers this solution's main question. Both had the same 50 tables.

| | tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|---|
| this solution (the first way) | **20** | 19 | **146** | 20 | 221 |
| the ranked geometry | 14 | **1** | 107 | **1** | 182 |

It racked more glasses than any other measured solution. It also toppled 20 glasses
against the geometry's 1. Both facts have one cause. The geometry refuses a
push when it cannot prove it is safe. This solution predicts the outcome and
acts on it instead. [The results](../11_the-results.md#5-what-the-comparison-says)
compares this with the other measured solutions. The next section says what this score
teaches.

## 5. Where it is strong and where it breaks

This section uses the score above to show the method's good and bad sides.

It needs no written physics and no guessed friction. The same model can serve a
new goal without new training. But where the data is thin, all five copies can
agree and still be wrong together. It is also slow. [How it
compares](../07_a-world-model-then-plan-with-it/06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
gives the evidence for each point. The next section turns this into advice.

## 6. When to choose it

This section says when this method is the right choice.

Choose it when you cannot write down what your actions do, and a simulator can
make the examples. Here the friction is unknown, and the simulator makes
thousands of pushes for free.

Do not choose it when a rule already predicts your actions well. Do not choose
it when a wrong guess is not allowed, unless a separate safety check can stop
it. The main lesson is about what to learn. The learning that helped was aimed
at what the geometry gets wrong.

The code is in
[`src/09_pushing-the-glasses-apart/04-a-world-model/`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model).
The full chapter starts at [what it
is](../07_a-world-model-then-plan-with-it/01_what-it-is.md).

← [Imitation from demonstrations](04_imitation-from-demonstrations.md) · [A foundation model as it downloads](06_a-foundation-model-as-it-downloads.md) →
