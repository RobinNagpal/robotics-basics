# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

**It could plan a sequence, and nothing else here could.** That is the
capability this document is built around, and it follows from the model
returning a table rather than a score — though the built planner's horizon is
one push, so the sequence is a design and not yet a result.

**Its model needs no written physics, and so no guessed friction.** There is no
friction value, no tipping formula and no rule about where the jaw fits
anywhere inside it, and the only thing written down in the built planner is the
map — where a glass may stand and where the arm can reach. The shared topple
gate that belongs in front of it is not wired up yet, which is a gap rather
than a virtue. Whatever decides whether a push slides,
tips or is blocked is whatever the model saw happen, which means it also
absorbs the things nobody thought to write down.

**It knows where it is ignorant, cheaply.** Five copies of a small network cost
five times nothing, and their disagreement is a usable signal that the training
data did not cover this push. Most learned methods give no such signal at all.

**Its training data costs no human time.** Every label is what the second look
found. A demonstration-based method needs somebody to produce the
demonstrations; this one needs only the simulator to run.

**The same model serves a different goal.** Change the arithmetic that scores a
predicted table and the solution aims somewhere else, with no retraining. A
learned policy would have to be trained again.

**It can be confidently wrong, and that is its worst failure.** Where the
training data is thin in a way the copies did not notice, five copies agree and
are wrong together. The topples recorded on the tuning tables were exactly
this: the model had rated every one of them safe, and a lower limit does not
catch that.

**Its model is only as wide as its encoding.** Five neighbours, four
measurements each, and no representation of the jaw's body. Anything the
thirty-four numbers cannot express cannot be learned however much data is
collected, and most of the recorded failure causes are of that kind.

**It is slow at run time, and in a different way from a foundation model.**
Hundreds of model calls per push is the price of searching rather than
answering.

**It compounds error over depth**, which caps how far a sequence can usefully be
planned, and the cap for a one-step-trained model is low.

**It cannot be inspected the way written geometry can.** When a written rule is
wrong you can print one number and see why. Here you print thirty-four numbers,
five answers and what really happened, and infer. That is far better than
nothing — and it is better than rung two offers — but it is not an explanation.

**And it is the most machinery of the six.** A data collector, a trainer, an
ensemble, a search and a loop, against [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md),
which is a page of arithmetic. That difference in setup cost is real and it
should be weighed against the scores rather than hidden behind them.

## 2. The general ideas behind this

Five lines of published work meet in this solution, and they are worth
separating because they are usually run together under the word "learning".

### Model-based against model-free control

A **model-free** method learns what to do. A **model-based** method learns what
will happen and computes what to do from it. The trade is well established in
both directions. Model-based methods need far fewer interactions, because every
interaction teaches them about the world rather than about one goal, and they
can be re-aimed at a new goal without new data. Model-free methods reach a
higher ceiling, because they never have to be right about the world, only about
the action.

It is normally right where interactions are expensive or irreversible and the
goal may change. It is normally wrong where interactions are cheap and plentiful
and the goal is fixed for ever, because then the extra machinery buys nothing a
policy would not have learned anyway. In this cell a topple is irreversible,
which argues for model-based; but simulator pushes are cheap and the goal has
not changed, which argues the other way. That tension is real and it is part of
what the comparison with the other five is meant to settle.

### Fitting a dynamics model to recorded interaction

Nagabandi, Kahn, Fearing and Levine's [*Neural Network Dynamics for Model-Based
Deep Reinforcement Learning with Model-Free
Fine-Tuning*](https://arxiv.org/abs/1708.02596) (2017) is the clearest statement
of the recipe rung one follows: fit a plain network to situation, action and
next situation gathered by random exploration, then control with
model-predictive control on top of it. Its headline result is sample
efficiency — far fewer interactions than a model-free policy needs for the same
task.

It is normally right when the situation can be written down as a short list of
measured numbers, which is exactly this problem once [the glasses have been
told apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
and measured. It is normally wrong when it cannot, because then the model has
to predict pictures, which is a far harder fit for a far worse prediction.

### Ensembles, and planning with them

Lakshminarayanan, Pritzel and Blundell's [*Simple and Scalable Predictive
Uncertainty Estimation using Deep
Ensembles*](https://arxiv.org/abs/1612.01474) (2016) is the reference for
training the same network several times and reading the spread between the
copies as uncertainty. Chua, Calandra, McAllister and Levine's [*Deep
Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics
Models*](https://arxiv.org/abs/1805.12114) (2018), usually called PETS, is the
version that plans with the cross-entropy method against such an ensemble and
keeps track of where the copies disagree. **Rung one is a simplified PETS**:
five networks, the cross-entropy method, and a veto driven by the worst copy
rather than the average.

An ensemble is normally right wherever a model will be searched against, because
a search finds a model's blind spots on purpose. It is normally wrong as a
complete account of uncertainty: copies trained on the same data can agree
confidently about a situation none of them has seen, which is precisely the
failure recorded above. For a method that does report when it has left the
region it knows, Bauza and Rodriguez's [*A Probabilistic Data-Driven Model for
Planar Pushing*](https://arxiv.org/abs/1704.03033) (2017) fits a Gaussian
process to pushing data and returns a spread with every value; it is slower to
query and does not scale to tens of thousands of examples, which is the trade an
ensemble takes the other side of.

### The cross-entropy method, and model-predictive control

The search is Rubinstein's **cross-entropy method**, described for a general
audience in de Boer, Kroese, Mannor and Rubinstein's *A Tutorial on the
Cross-Entropy Method* (2005): sample, keep the elite, refit the sampling
distribution to the elite, repeat. Planning a short sequence, executing only its
first step and re-planning is **model-predictive control**, which is decades old
and came from process control long before anybody applied it to robots.

The cross-entropy method is normally right where the action has few dimensions,
the cost is cheap to evaluate and the landscape is awkward — not smooth, full of
hard limits, or both. It is normally wrong where the action has many dimensions,
because the number of samples it needs to cover a space grows with the
dimension, which is why no policy here is searched for this way and only pushes
are. Model-predictive control is normally right whenever the model is imperfect
but the state can be re-measured often, and normally wrong when measuring is
slow or expensive, which would leave the plan running open-loop for exactly as
long as it is unreliable.

### Learned world models with their own representation

Hafner and colleagues' [*Learning Latent Dynamics for Planning from
Pixels*](https://arxiv.org/abs/1811.04551) (PlaNet, 2018) and [*Dream to
Control*](https://arxiv.org/abs/1912.01603) (Dreamer, 2019) established the
other branch: do not predict the observation at all, learn a compact internal
description and predict how *that* changes. Hansen, Wang and Su's
[TD-MPC](https://arxiv.org/abs/2203.04955) (2022) and
[TD-MPC2](https://arxiv.org/abs/2310.16828) (2023) combine such a learned
internal model with planning at run time and a learned value to stand in for
everything beyond the planning horizon, which is how they avoid needing a deep
rollout. TD-MPC2 is rung two, and it reaches this project through LeRobot.

This family is normally right where the situation cannot be written down — raw
pictures, contact-rich manipulation, anything where the useful variables are
not the measured ones. It is normally wrong, or at least wasteful, where the
situation *can* be written down and already has been, which is the case here:
the camera work that [tells the glasses
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md) has
already measured the positions and widths, so a learned encoding is being asked
to rediscover information the cell already supplies. That is the honest prior
expectation for rung two here, and it is exactly the expectation the
comparison exists to test.

### Where the push data of record comes from

Finally, for anyone who wants real pushes rather than simulated ones: Yu, Bauza,
Fazeli and Rodriguez's [*More than a Million Ways to Be
Pushed*](https://arxiv.org/abs/1604.04038) (2016) recorded a robot pushing
objects across several different surfaces with the pusher's path, the object's
motion and the contact forces all logged. What it buys is pushes on *more than
one surface*, which is the only way to ask whether a fitted push model transfers
at all — the question this solution cannot ask, because its examiner has one table
with one friction. What it costs is a robot, a motion-capture rig and months.

## 3. Where it sits among the other five

This solution is the only one that learns what will happen rather than what to
do, and its place in the comparison follows from that rather than from its
score.

Against [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md), the comparison is whether any
learning beats no learning. The fixed nudge needs no data, no training and no
weights, it explains every one of its own failures, and on any table where a
small shove in a sensible direction is enough it is the easier tool by a wide
margin. This solution earns its place where choosing the push matters — where a
nudge in the obvious direction moves a glass into a different crowd.

Against [geometry generates, a model ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md), the
comparison is the closest in the set and the easiest to misread. Both search
over candidate pushes and both score them with something fitted. The difference
is what the fitted part returns. A ranker returns a score, which is enough to
choose among the candidates in front of it and not enough to say what the table
will look like, so it can never chain two pushes or be re-aimed at a different
goal. This solution's model returns a table, which costs more to fit and buys
both of those. Note also that the geometric solution is the teacher for the
imitation solutions, and this one is not: it needs no demonstrations, because
its labels come from the second look.

Against [imitation from demonstrations](../06_imitation-from-demonstrations/01_what-it-is.md),
the comparison is one of the sharpest among the six: *plan with a model, or
learn the push directly*. A policy answers in one pass with no search, which
makes it far cheaper to run, and it needs no explicit idea of the world at all.
But it needs demonstrations, which somebody or something has to produce; it
inherits whatever its teacher did wrong; and changing the goal means training
again. This solution needs no demonstrations and no teacher, and it can be
re-aimed by editing arithmetic. It pays for that in run-time compute and in
machinery.

Against [SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and [SmolVLA
fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md), the comparison is between a small thing
that knows only this table and a large thing that has seen hundreds of real
teleoperation datasets and knows almost nothing about this one. Those two are
also policies, so they share the contrast with imitation above. The pair of them
is the sharpest comparison in the whole set — the same model and the same
weights, with the only difference being whether its training was continued
here — and this solution is not part of that comparison at all.

And the comparison inside this solution is its own: five small networks written
for this cell against TD-MPC2 off the shelf, which measures whether building the
model by hand was worth the effort. The honest expectation is that in a cell
this narrow, with the state already measured, the hand-built model is
competitive. Finding out is the point.

← [What it needs](05_what-it-needs.md) · [A foundation model as it downloads — what it is](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) →
