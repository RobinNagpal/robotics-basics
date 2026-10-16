# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks. It names the published ideas behind it, and it places it beside the
other solutions.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the others](#3-where-it-sits-among-the-others)

## 1. Where it is strong and where it breaks

The earlier pages showed how the solution works and what it costs. This section
lists its strengths first, and then its weaknesses.

**It could plan a sequence of pushes, and no other solution here could.** The
built planner looks only one push ahead, so this is a design, not yet a result.
[Planning a
sequence](03_how-it-works.md#9-planning-a-sequence-which-only-this-solution-could-do)
explains it.

**Its model needs no written physics.** It holds no friction value and no
tipping formula. It learns from what it saw happen, including things nobody
thought to write down. But the shared topple rule is also missing, as [the main
idea](01_what-it-is.md#4-the-main-idea) explains.

**It knows cheaply where it is ignorant.** The five copies disagree where the
training data did not cover a push. [Ensembles as a measure of
ignorance](03_how-it-works.md#5-ensembles-as-a-measure-of-ignorance) explains
this.

**Its training data costs no human time.** [What it
needs](05_what-it-needs.md#1-what-it-needs) explains why.

**The same model can serve a different goal without retraining.** [The main
idea](01_what-it-is.md#4-the-main-idea) explains this.

**Its worst failure is being sure and wrong.** The planner makes a push only
when all five copies give it less than a 1% chance of a topple. So any push that
toppled a glass was a push that all five copies had rated as safe. Where
the training data was thin in a way the copies did not notice, **the five copies
agree and are wrong together.** On the 50 test tables, this happened 20 times,
on 19 tables. A lower topple limit does not fix this, because these are pushes
the model was sure about. A lower limit only refuses more. More training
examples of those situations would help.

**Its model can only learn what its 34 numbers describe.** The inputs hold five
neighbours with five numbers each. They say nothing about the body of the jaw.
More data cannot teach the model what the inputs cannot express. The folder's
README records causes of this kind. In one, the jaw's body hit a neighbour
behind the pushed glass, and the 34 numbers do not describe that at all. In
another, the jaw met a stemmed glass at its stem, under the bowl. The 34
numbers describe that glass only as three widths.

**It spends more computing time per push than the geometry solutions.** It
searches before every push, while they compute an answer directly. [The
results](../11_the-results.md#2-the-results) compare the times.

**Its error grows with depth.** This limits how far ahead a sequence could be
planned. [Compounding error over a
rollout](03_how-it-works.md#8-compounding-error-over-a-rollout) explains why.

**It cannot be read the way written geometry can.** When a written rule is
wrong, you can print one number and see why. Here you print 34 numbers, five
answers and what really happened, and then you have to work out the cause.
That is much better than nothing, and better than the second way. But it is
not an explanation.

**It needs the most machinery of the seven.** It has a data collector, a trainer,
five copies of a model, a search and a loop. [One fixed
nudge](../04_one-fixed-nudge/01_what-it-is.md) is a page of arithmetic. This
extra setup cost is real, and it should be weighed against the scores.

The next section names the published ideas this solution is built from.

## 2. The general ideas behind this

The strengths and weaknesses above come from five lines of published work.
This section separates them, because they are often mixed together under the
one word "learning".

### Model-based against model-free control

A **model-free** method learns what to do. A **model-based** method learns
what will happen, and works out what to do from that.

Each has a known advantage. Model-based methods need far fewer interactions,
because each interaction teaches them about the world, not about one goal. They
can also be aimed at a new goal without new data. Model-free methods can reach
a higher ceiling, because they only need to be right about the action, not
about the world.

Model-based is usually right when interactions are costly or cannot be undone,
and when the goal may change. It is usually wrong when interactions are cheap
and the goal never changes. In that case the extra machinery adds nothing that
a policy would not learn anyway. In this cell, a topple cannot be undone, which
favours model-based. But simulator pushes are cheap and the goal has not
changed, which favours model-free. The comparison with the other solutions is meant
to test this.

### Fitting a dynamics model to recorded interaction

Nagabandi, Kahn, Fearing and Levine's [*Neural Network Dynamics for Model-Based
Deep Reinforcement Learning with Model-Free
Fine-Tuning*](https://arxiv.org/abs/1708.02596) (2017) describes the recipe the
first way follows. It fits a plain network to situation, action and next
situation, collected by random exploration. Then it controls the robot with
model-predictive control on top. Its main result is that it needs far fewer
interactions than a model-free policy for the same task.

This recipe is usually right when the situation can be written as a short list
of measured numbers. That is true here once [the glasses have been told
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md) and
measured. It is usually wrong when the situation cannot be written that way.
Then the model has to predict pictures, which is much harder.

### Ensembles, and planning with them

Lakshminarayanan, Pritzel and Blundell's [*Simple and Scalable Predictive
Uncertainty Estimation using Deep
Ensembles*](https://arxiv.org/abs/1612.01474) (2016) is the reference for
training the same network several times and reading the spread between the
copies as uncertainty. Chua, Calandra, McAllister and Levine's [*Deep
Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics
Models*](https://arxiv.org/abs/1805.12114) (2018) is usually called PETS. It
plans with the cross-entropy method against such a set of copies, and it tracks
where the copies disagree. **The first way is a simple version of PETS**: five
networks, the cross-entropy method, and a veto based on the worst copy, not the
average.

A set of copies is usually right wherever a search will run against the model,
because a search finds a model's weak spots on purpose. It is not a complete
measure of doubt. Copies trained on the same data can agree about a situation
none of them has seen. That is the failure described in the section above.
Bauza and Rodriguez's [*A Probabilistic Data-Driven Model for Planar
Pushing*](https://arxiv.org/abs/1704.03033) (2017) does report when it is
outside what it knows. It fits a Gaussian process to pushing data, and it
returns a spread with every value. But it is slower to ask, and it does not
scale to tens of thousands of examples. A set of copies makes the opposite
trade.

### The cross-entropy method, and model-predictive control

The search is Rubinstein's **cross-entropy method**. De Boer, Kroese, Mannor and
Rubinstein's *A Tutorial on the Cross-Entropy Method* (2005) describes it for a
general reader. It samples, keeps the best, fits the sampling to the best, and
repeats. Planning a short sequence, making only its first step, and planning
again is called **model-predictive control**. It is decades old, and it came
from industrial process control before it was used on robots.

The cross-entropy method is usually right when the action has few numbers, the
cost is cheap to compute, and the cost is not smooth or has hard limits. It is
usually wrong when the action has many numbers, because the samples it needs
grow with the number of dimensions. This is why only pushes are searched for
this way here, and no policy is. Model-predictive control is usually right
when the model is imperfect but the state can be measured often. It is usually
wrong when measuring is slow or costly, because then the plan runs without
checks for too long.

### Learned world models with their own representation

Hafner and colleagues' [*Learning Latent Dynamics for Planning from
Pixels*](https://arxiv.org/abs/1811.04551) (PlaNet, 2018) and [*Dream to
Control*](https://arxiv.org/abs/1912.01603) (Dreamer, 2019) started the other
branch. They do not predict what the camera sees. They learn a short internal
description and predict how that changes. Hansen, Wang and Su's
[TD-MPC](https://arxiv.org/abs/2203.04955) (2022) and
[TD-MPC2](https://arxiv.org/abs/2310.16828) (2023) add planning at run time to
such an internal model. They also learn a value that stands in for everything
past the end of the plan. This is how they avoid long rollouts. TD-MPC2 is the
second way, and [what it needs](05_what-it-needs.md#1-what-it-needs) says where
it would come from.

This family is usually right when the situation cannot be written down. For
example, the input may be raw pictures, or the task may have many contacts. It
is usually wasteful when the situation can be written down and already has
been. That is the case here. The camera work that [tells the glasses
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
already measured the positions and widths. A learned internal description would
have to find that information again. So the expected result is that the second
way does no better here. Building it would test that expectation.

### Where the push data of record comes from

Some readers will want real pushes instead of simulated ones. Yu, Bauza, Fazeli
and Rodriguez's [*More than a Million Ways to Be
Pushed*](https://arxiv.org/abs/1604.04038) (2016) recorded a robot pushing
objects across several surfaces. It logged the pusher's path, the object's
motion and the contact forces. Its value is pushes on *more than one surface*.
That is the only way to ask whether a learned push model works on a new
surface. This solution cannot ask that, because its examiner has one table with
one friction. The cost of such data is a robot, a motion-capture system and
months of work.

The next section places this solution beside the other solutions.

## 3. Where it sits among the others

The ideas above explain how this solution works. This section compares its
result with the other measured solutions. It is the only solution that learns what will
happen instead of what to do.

The scores come from one run on the 50 test tables, in
[`results.json`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/04-a-world-model/results.json).
It racks 146 of the 251 glasses in 221 pushes. It finishes 20 tables and leaves
19 tables wrong. It topples 20 glasses.

**Against [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md)**, the
question is whether any learning beats none. The answer is split. This solution
racks 146 glasses to the fixed nudge's 107, and it finishes 20 tables to its 14.
But it topples 20 glasses, where the fixed nudge topples one. **So it racks 39
more glasses and topples 19 more.** That is a trade, not a win, because a
toppled glass cannot be stood up again. Also, the fixed nudge needs no data, no
training and no weights, and it can explain each of its own failures.

**Against [geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md)**, the
difference is what the learned part returns. Both search over candidate pushes,
and both score them with something learned. The ranker returns a score. A score
can choose among candidates, but it cannot say what the table will look like.
So the ranker can never chain two pushes or aim at a new goal. This solution's
model returns a table, which costs more to train and allows both. [What the
comparison says](../11_the-results.md#5-what-the-comparison-says) compares the
two scores.

**Against [imitation from
demonstrations](../06_imitation-from-demonstrations/01_what-it-is.md)**, the
question is: plan with a model, or learn the push directly? A policy answers in
one step with no search, so it is much cheaper to run. But it needs
demonstrations, and a new goal means training again. This solution needs no
demonstrations and no teacher. It can take a new goal by changing arithmetic.
It pays for that with computing time and machinery.

**Against [SmolVLA as it
downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and
[SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md)**,
the contrast is size. This solution is small and knows only this table.
SmolVLA is large, has seen many real robot datasets, and knows almost nothing
about this table. Both SmolVLA solutions are policies, so the contrast with
imitation above applies to them too. [Solution
7](../10_a-newer-larger-model-fine-tuned-here/01_what-it-is.md) is a newer and larger borrowed model, fitted
the same way as solution 6. It was fitted three times, and no fit learned the
task, so it has no score here. [Its
results](../10_a-newer-larger-model-fine-tuned-here/03_results.md) explain why.

**Inside this solution**, the comparison is the hand-built model against
TD-MPC2. It would show whether building the model by hand was worth it. In a
cell this narrow, with the state already measured, the hand-built model should
do about as well. Building the second way is how to find out.

← [What it needs](05_what-it-needs.md) · [Questions and answers](07_questions-and-answers.md) →
