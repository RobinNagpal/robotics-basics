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

![The eleven steps of the world-model solution: collect pushes, train five copies of a network, then search for the best push before every push the arm makes.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-flow-what-it-does.png)

The picture gives each step a short heading and a number. The steps are in three
groups: collecting the pushes, which happens once; fitting the network, which
happens once; and planning, which happens before every push the arm makes.

1. **Round one: random pushes in the simulator.** 24,759 pushes are made at
   random on 4,000 tables. Every example is one push that was really made: look,
   push, look again. The push is made because nobody can say in advance what it
   will do, since the friction between a glass and the table is not measured
   anywhere in the cell.
2. **Round two: pushes the planner picks.** 13,253 more pushes are made on 5,000
   new tables, mostly chosen by the planner using the round-one model. The planner
   finds the pushes that the model is wrong about in its own favour. Making those
   pushes fills exactly those gaps.
3. **Nobody labels the pushes.** The answer to every example is what the second
   look found. The model therefore learns what the camera will report, not what
   the simulator knows.
4. **Train five copies of one small network.** Each copy starts from its own
   random weights and learns from all 38,012 pushes. It takes in 34 numbers, which
   are the glasses as the camera measured them and the push. It gives back 14: a
   displacement for every glass, whether anything toppled, and whether the jaw
   was blocked on the way down. Training takes about 31 minutes on a laptop
   processor.
5. **Draw candidate pushes.** For every crowded glass, candidates are drawn that
   differ in which way the jaw points, where across the glass it meets it, and how
   far it travels.
6. **Put every candidate to all five copies.** Asking the model is arithmetic, so
   a search that would be reckless against the real table is ordinary against the
   model.
7. **Drop candidates that might topple a glass.** A candidate is thrown away if
   any one copy gives it more than a 1% chance of toppling something. The check
   is made on the table as seen and on four copies of it moved by about the
   camera's error, so a push that only looks safe by luck does not survive.
8. **Drop candidates that break the map.** A candidate is thrown away if a glass
   it moves would land outside the zone glasses may stand in, or if the jaw would
   leave the arm's reach. This map is written-down arithmetic, because reach is
   not the same in every direction and the model was never shown it.
9. **Score the survivors.** Each is scored on the table the model predicts for it:
   how much clear room is still missing around every glass, plus a small penalty
   for each millimetre pushed. The shortest push that does the job wins.
10. **Refine the good ones, in rounds.** The first round draws 600 candidates over
    the whole range. Each of three further rounds draws 300 more around the best
    30 of the round before. That gives about 1,500 candidates for every crowded
    glass, and the dashed arrow in the picture is this loop back to step 5.
11. **Make the one best push, then look again.** The best push over all the
    crowded glasses is handed to the examiner, and only that one push is made.
    The arm then looks again and the whole search runs afresh, so whatever the
    model got wrong is measured away instead of being inherited.

Nothing in these steps holds a friction value or a tipping rule. What a push does
is a regularity in the recorded pushes, and what counts as a good table is plain
arithmetic kept outside the model.

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

It needs about 15,000 pushes made in the simulator. The project's
[`README.md`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/04-a-world-model/README.md) records 15,379. Nobody has to label them, because the
answer is what the camera saw after each push. Training takes
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
[`src/09_pushing-the-glasses-apart/04-a-world-model/`](https://github.com/RobinNagpal/robotics-basics/tree/main/code/src/09_pushing-the-glasses-apart/04-a-world-model).
The full chapter starts at [what it
is](../07_a-world-model-then-plan-with-it/01_what-it-is.md).

← [Imitation from demonstrations](04_imitation-from-demonstrations.md) · [A foundation model as it downloads](06_a-foundation-model-as-it-downloads.md) →
