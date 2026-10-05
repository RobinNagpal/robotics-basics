# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas it is built from so that
you can read about them outside this book, and places it beside the other five.
By the end you will know when this is the solution to reach for, and when it is
the wrong one.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

**Nothing has to be written about pushing.** No friction model, no candidate
generator, no features chosen by hand, no geometry. The method's entire content
is a dataset and a fitting procedure, and the dataset was produced by a program
that already exists. Of the six, this is the one that demands the least prior
understanding of the task from whoever builds it.

**The output is native.** This solution emits a chunk because a chunk is what
it is built to emit, so nothing is squeezed or expanded on the way out, and the
bench's decision to accept waypoints costs it nothing.

**Labels are free and plentiful.** The usual reason not to attempt imitation
learning — that somebody has to demonstrate the task by hand, many times — does
not apply, because the teacher is code and the tables are simulated.

**It is cheap to train and cheap to run.** Hours on a laptop's own graphics
processor, and one forward pass per push.

**It is a measurement.** Student against teacher, on the same tables with the
same scorecard, with every shared part held still. Even if this solution were
not the one carried forward, that reading would have earned its place.

Against that, five weaknesses, and the first three cannot be engineered away.

**The ceiling is the teacher's quality.** Every label came from the teacher,
and nothing in behaviour cloning ever evaluates an outcome, so **this solution
cannot beat its teacher by much on the pushes it imitates.** It is worth being
precise about the two narrow ways it might exceed its teacher, because they are
real but small: it can smooth away some of the teacher's inconsistency, since a
fitted function averages over many examples and so is steadier than any one of
them; and it can express motions the bench's macro cannot, since its output is
waypoints rather than push parameters. What it cannot do is discover that a
different glass should have been moved, or a different destination chosen,
because no mechanism in it compares one outcome against another. [A world
model, then plan with it](../07_a-world-model-then-plan-with-it/01_what-it-is.md) has such a
mechanism, which is the sharpest difference between the two.

**Filtering the demonstrations biases it towards what the teacher does well.**
Keeping only the pushes that succeeded is necessary, because a cloned policy
copies failures as readily as successes, and it thins the dataset exactly in
the situations where the teacher struggled. So the student is fitted most
densely where help was least needed.

**It needed bench work the first two solutions did not.** A straight-down
rendered view and a waypoint path, both missing when this solution was designed
and both now built. That cost is paid, but two smaller ones are paid on every
push rather than once. The bench's chunk wants a glass and an aim that the
policy does not produce, so both are read back off the waypoints outside it.
And nothing stops a network emitting a coordinate the jaw cannot reach, so
every chunk is pulled inside the jaw's limits before it is followed, and how
often that happens has to be counted and reported rather than hidden.

**It is open-loop inside a chunk, and it cannot refuse.** During a chunk
nothing is read, and the monitor that would watch the force is not built, so
the only thing stopping a chunk is the jam threshold. And the policy's only
output is waypoints, so a refusal has to come from the shared gate in front of
it rather than from the policy itself.

**And it cannot explain itself, or say when it is lost.** When the teacher is
wrong you can print the candidates and the scores and see which step went
astray. When this policy is wrong you can look at the picture and guess. It has
no confidence output, and the situation in which it is least reliable — a table
unlike anything in its data — is indistinguishable in its output from the
situation in which it is most reliable. Combined with it being stochastic and
with training varying by seed, that is why the bench insists that one run is
not a measurement and that a result quoted without a spread is not a result.

## 2. The general ideas behind this

Nothing in this solution was invented for glassware. Every part of it is a
standard piece of modern practice, and each is worth knowing on its own,
including where it is normally the wrong tool.

### Behaviour cloning

Fit a policy by supervised learning on pairs of what the demonstrator saw and
what the demonstrator did. It is the oldest and simplest form of imitation
learning, going back to driving a vehicle from camera images with a small
network trained on a person's steering, and it remains the first thing to try
whenever demonstrations exist.

It is normally the right choice when demonstrations are plentiful and the task
is reactive — when what to do next really is a function of what is in front of
you. It is normally the wrong choice when demonstrations are scarce, when the
task needs a long-horizon plan that no single observation implies, or when the
demonstrator cannot be consulted again, because then the compounding error
below has no cheap repair. For more, see [imitation
learning](https://en.wikipedia.org/wiki/Imitation_learning).

### Compounding error, and dataset aggregation

A cloned policy's own small mistakes move it to states its demonstrations never
covered, where it acts worse, which moves it further out. The standard analysis
of this and the standard repair are both in **DAgger** — dataset aggregation —
by Ross and colleagues ([arXiv:1011.0686](https://arxiv.org/abs/1011.0686)):
run the policy, label the states it actually visits with what the expert would
have done there, add them to the training set, and retrain.

It is the right method whenever the expert can be queried at a state of your
choosing, which is the case here because the expert is a program. It is wrong,
or rather unavailable, when the expert is a person, because asking a person to
label thousands of states the policy wandered into is slower and more
unpleasant than asking them to demonstrate the task properly in the first
place. That asymmetry is the main reason a programmed teacher is worth so much
more than a human one for this particular method.

### Action chunking

Predict a short sequence of future actions in one pass and execute it, rather
than predicting one action per control step. ACT introduced this for fine
manipulation learned from inexpensive hardware (Zhao and colleagues,
[arXiv:2304.13705](https://arxiv.org/abs/2304.13705)) and it has become a
standard component of imitation policies, including the vision-language-action
models [SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and
[SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md) use.

It is right for continuous, committed motions — a push, a wipe, a pour — where
re-deciding every instant produces dithering and averages away the commitment
the motion needs. It is wrong when the environment can change faster than a
chunk takes to run, because a chunk is blind while it executes: a policy
chunking through a moving obstacle is a policy driving with its eyes closed.
This cell is quasi-static and nothing moves except what the arm moves, which is
why chunking is safe here and would not be in a scene with people in it.

### Denoising diffusion, and Diffusion Policy

Learn to remove noise from a corrupted sample, then generate by starting from
pure noise and removing a little at a time. The modern form of this is the
denoising diffusion probabilistic model (Ho and colleagues,
[arXiv:2006.11239](https://arxiv.org/abs/2006.11239)), and **[Diffusion
Policy](https://diffusion-policy.cs.columbia.edu/)** applies it to action
chunks for robot control (Chi and colleagues,
[arXiv:2303.04137](https://arxiv.org/abs/2303.04137)).

It is right when the right answer is not unique — when several actions would
all be good and a model forced to name one would return their average, which is
often no answer at all. It is wrong when the answer genuinely is unique and
speed matters, because the several denoising passes buy nothing and cost real
time per decision. The honest reading in this problem is that uncrowding a
table has many good answers, which argues for it, and that a push happens at
the speed of an arm rather than of a processor, which means the extra passes are
affordable.

### Mode averaging under a single-answer loss

The failure the previous idea repairs deserves its own name, because it is
general and it catches people out. Fitting a model to produce one output while
minimising its average error over examples that disagree makes the model produce
something between those examples. Where the examples are two sensible choices,
the something between them is frequently a third thing that is not sensible at
all.

It is worth knowing because the symptom is misleading. The model's training
error looks reasonable and its behaviour looks timid, and the natural diagnosis
— that it needs more data or more training — is the wrong one, since more
examples of both choices make the averaging worse rather than better. The
repairs are to represent a distribution rather than a point, as the denoising
model does, or to remove the ambiguity from the data by making the choice part
of the input.

### Distilling a planner or a program into a policy

Use a slow but good procedure as the teacher for a fast network, so that the
network ends up doing at run time what the procedure did offline. This is a
common and unglamorous pattern, and it is exactly what the relationship between
the teacher and this solution is.

It is right when the teacher is correct but too slow to run where it is needed,
or when the teacher needs information at training time that is unavailable at
run time. It is wrong when the student is expected to be better than the
teacher, because distillation has no mechanism for improvement — it is copying,
and copying has a ceiling. In this book the honest statement is that
distillation is being used for its measurement value rather than for speed,
since the teacher is not slow; what the pair establishes is whether the mapping
is learnable at all.

## 3. Where it sits among the other five

[The six solutions](../03_the-six-solutions/01_how-the-six-compare.md) form a ladder, ordered by how much of each one
was fitted in this cell, and this solution is the first rung on which
everything was.

Against [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md), the comparison is the basic
one this whole book is built around: does any learning beat a fixed nudge? That
solution fits nothing, pushes the same distance in the same way every time, and
looks again. It is arithmetic and it costs essentially nothing to run. If this
solution cannot clear more tables than that, no part of the machinery above has
earned its place.

Against [geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md), the comparison is student
against teacher, and it is the most informative pairing this solution has.
Every label this policy saw came from that solution, so it cannot discover a
better choice of glass or destination than the one it was shown, and it should
not be expected to beat its teacher by much on the pushes it imitates. What the
gap measures is therefore not which method is better but whether the mapping
from a picture to a good push is learnable: a student that nearly matches its
teacher says the policy class is adequate and the remaining error belongs to
the teacher's geometry, and a student that falls well short says the opposite.
The two places this solution can legitimately exceed its teacher are narrow and
worth watching for in the numbers — a steadier push, from averaging over many
examples, and a motion the bench's macro could not have expressed.

Against [a world model, then plan with
it](../07_a-world-model-then-plan-with-it/01_what-it-is.md), the comparison is the sharpest
question among the six after the foundation-model pair: plan with a model, or
learn the push directly? That solution learns how the world changes and
searches over candidate actions at run time, simulating each one forward before
committing, so **it can find a push nobody ever demonstrated** — which is
exactly the thing this solution cannot do. It pays for that on every push, in
run-time cost that [the test bench](../02_the-test-bench.md) puts at hundreds
or thousands of times the arithmetic a fixed nudge costs, and it pays again in
needing a model of the world accurate enough to plan against, which is a harder
thing to learn than a mapping. So the pair trades a ceiling against a cost:
this solution is cheap and capped by its teacher, that one is expensive and
capped by what its own encoding can express rather than by anybody else's work.

Against [SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md),
the comparison is fitting here against borrowing wholesale. That solution runs
SmolVLA exactly as it downloads, with about 450 million parameters and a
pretraining set of 487 community datasets of real teleoperation behind it, and
fits nothing in this cell. So it brings a vast amount of experience of robot
manipulation in general and none of this cell in particular, while this
solution brings the opposite: a small network that has seen nothing but this
bench, this jaw and these four kinds of glass. Which of those two is the better
trade is precisely what this book is for.

Against [SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md), the
comparison is where the fitting happens. That solution takes SmolVLA's borrowed
weights and continues their training on this cell's own data with low-rank
adaptation, which is this solution's method — imitation from demonstrations
collected here — applied to somebody else's starting point instead of to random
numbers. Reading the two together separates what the demonstrations are worth
from what the pretraining is worth. And those two are the sharpest pair of the
six in their own right: same model, same weights, and the only difference
between them is that one has had its training continued here.

Read as a ladder, the six measure what each increment of fitting buys. This one
is the rung where all the fitting is done here, from nothing, on examples a
program produced for free — the cheapest honest attempt at learning this task
that this book contains, and the one whose limits are easiest to state in
advance.

← [What it needs](05_what-it-needs.md) · [A world model, then plan with it — what it is](../07_a-world-model-then-plan-with-it/01_what-it-is.md) →
