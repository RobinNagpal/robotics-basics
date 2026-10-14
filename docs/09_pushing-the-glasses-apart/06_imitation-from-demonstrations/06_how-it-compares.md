# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks, names the general ideas behind it, and places it beside the other
five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The earlier pages showed how the solution works, so this section weighs it up.
It has five strengths.

**Nothing about pushing has to be written.** There is no friction model, no
candidate generator, no hand-chosen features and no geometry. The method is a
data set and a training run. A program that already exists made the data. Of
the six, this one needs the least knowledge from its builder.

**The output fits the examiner as it is.** The policy gives a chunk, and the
examiner accepts chunks. Nothing is squeezed or expanded on the way out.

**Labels are free and plentiful.** Usually, someone must show the task by hand
many times. Here the teacher is code and the tables are simulated, so that cost
is gone.

**It is cheap to train and cheap to run.** It takes hours on a laptop's
graphics processor, and one forward pass per push.

**It is a measurement.** The student is tested against its teacher on the same
tables, with the same scorecard. That reading has value even if this solution
is not the one kept.

It also has five weaknesses. The first one cannot be engineered away. None of
them goes away with more data.

**It cannot do much better than its teacher.** Every label came from the
teacher. And nothing in behaviour cloning ever checks an outcome. So it has no
way to find that a different glass, or a different destination, would have been
better. It can beat its teacher in only two small ways. A trained network
averages many examples, so it can be steadier than any one of them. And it can
make motions the macro cannot make. [A world model, then plan with
it](../07_a-world-model-then-plan-with-it/01_what-it-is.md) can compare
outcomes. That is the sharpest difference between the two.

**Keeping only good pushes biases its data.** Here that bias turned out small,
and it did not hold this solution back. [Choosing which examples to
keep](03_how-it-works.md#3-choosing-which-demonstrations-to-keep-and-the-bias-it-buys)
explains it.

**It needed extra work from the examiner.** [What it
needs](05_what-it-needs.md) describes the two parts that had to be built. Two
small costs also come on every push. The glass and the aim must be read off the
waypoints afterwards. And every chunk must be pulled inside the jaw's reach,
and the pulls counted.

**It is blind inside a chunk, and it cannot refuse.** Nothing is read while a
chunk runs, as [action
chunking](03_how-it-works.md#4-action-chunking-and-why-it-matters) explains.
Refusals must come from the shared gate in front of the policy, as [when a
glass cannot be pushed
safely](04_a-worked-example.md#1-when-a-glass-cannot-be-pushed-safely)
explains.

**It cannot explain itself, or say when it is lost.** When the teacher is
wrong, you can print its candidates and scores and find the bad step. When this
policy is wrong, you can only look at the picture and guess. It gives no
confidence value. Its output looks the same on a strange table as on a familiar
one. Training also changes with the seed, so [one run is not a
measurement](../01_the-problem/03_the-examiner.md).

The next section names the general ideas behind these strengths and weaknesses.

## 2. The general ideas behind this

The strengths and weaknesses above come from standard ideas, not from anything
made for glasses. This section names each idea and says when it is the right
tool and when it is the wrong one.

### Behaviour cloning

Fit a policy by supervised learning on pairs of what the teacher saw and what
it did. It is the oldest and simplest kind of imitation learning. An early
example drove a car from camera images with a small network trained on a
person's steering. It is still the first thing to try when examples exist.

It is usually right when examples are plentiful and the task reacts to what is
in front of it. It is usually wrong when examples are scarce, or when the task
needs a long plan, or when the teacher cannot be asked again. For more, see
[imitation learning](https://en.wikipedia.org/wiki/Imitation_learning).

### Compounding error, and dataset aggregation

A cloned policy's small mistakes take it to states its examples never covered.
There it acts worse, which takes it further out. **DAgger**, or dataset
aggregation, is the standard fix, by Ross and colleagues
([arXiv:1011.0686](https://arxiv.org/abs/1011.0686)). Run the policy, label
the states it reaches with the expert's answer, add them to the data, and
train again.

It works when the expert can be asked about any state, as here, where the
expert is a program. It is hard to use when the expert is a person. [Compounding
error](03_how-it-works.md#6-compounding-error) explains why it is cheap here.

### Action chunking

Predict a short run of future actions in one pass, and carry it out. ACT
introduced this for fine manipulation with low-cost hardware (Zhao and
colleagues, [arXiv:2304.13705](https://arxiv.org/abs/2304.13705)). It is now a
standard part of imitation policies. The vision-language-action models in
[SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md)
and [SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md)
use it too.

It is right for steady motions such as a push, a wipe or a pour. It is wrong
when the scene can change faster than a chunk runs, because a chunk is blind
while it runs. In this cell nothing moves except what the arm moves. So
chunking is safe here, but it would not be safe near people.

### Denoising diffusion, and Diffusion Policy

Train a model to remove noise from a damaged sample. Then make new samples by
starting from pure noise and removing a little at a time. The modern form is
the denoising diffusion probabilistic model (Ho and colleagues,
[arXiv:2006.11239](https://arxiv.org/abs/2006.11239)). **[Diffusion
Policy](https://diffusion-policy.cs.columbia.edu/)** uses it on action chunks
for robot control (Chi and colleagues,
[arXiv:2303.04137](https://arxiv.org/abs/2303.04137)).

It is right when there are several good answers, because a one-answer model
would average them. It is wrong when there is only one answer and speed
matters, because the extra passes cost time. Moving glasses apart has many good
answers. And a push runs at the speed of an arm, not of a processor. So the
extra passes are affordable here.

### Mode averaging under a single-answer loss

This is the failure that diffusion fixes. Train a model to give one output, on
examples that disagree. It will then give something between them. When the
examples are two good choices, the answer between them is often a bad third
choice. [A second way](03_how-it-works.md#5-a-second-way--diffusion-policy)
draws one such case.

The symptom misleads people. The training error looks fine, and the behaviour
looks timid. The natural guess is that the model needs more data. That guess is
wrong, because more examples of both choices make the averaging worse. There
are two real fixes. One is to predict a spread of answers, as diffusion does.
The other is to make the choice part of the input.

### Distilling a planner or a program into a policy

Use a slow but good program as the teacher for a fast network. The network then
does at run time what the program did. This is a common pattern, and it is
exactly how this solution relates to its teacher.

It is right when the teacher is correct but too slow, or when the teacher uses
information that is missing at run time. It is wrong when the student is meant
to beat the teacher, because copying has a ceiling. Here the teacher is not
slow. So this pair is used to measure something: whether a good push can be
learned at all.

The next section places this solution beside the other five.

## 3. Where it sits among the other five

The general ideas above explain this solution on its own, and this section
compares it with the rest. [The six
solutions](../03_the-six-solutions/01_how-the-six-compare.md) form a ladder,
ordered by how much of each one was trained in this cell. This solution is the
first where everything was trained here.

Against [one fixed nudge](../04_one-fixed-nudge/01_what-it-is.md), the question
is whether any learning beats a fixed rule. Every learned solution must pass
that test.

Against [geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md), the student
meets its teacher. This is the most useful pair for this solution. The gap
does not say which method is better. It says whether a good push can be learned
from a picture. A student close to its teacher would mean yes. A student far
behind means no, at least for this kind of policy.

This student is far behind. The table below gives the median of three seeds,
with the range in brackets, on the 50 test tables. Read each row as one
measure, with the student on the left and the teacher on the right.

| | ACT (this solution) | Teacher |
|---|---|---|
| Tables done | 2 (1–3) | 14 |
| Tables wrong | 11 (7–13) | 1 |
| Glasses racked | 63 (51–64) | 107 |
| Glasses toppled | 12 (7–13) | 1 |
| Pushes spent | 438 (414–497) | 182 |
| Thinking per push | 11 ms | 102 ms |

The student clears far fewer tables and topples far more glasses. Most of its
pushes are stopped on the way down, for the reason [the worked
example](04_a-worked-example.md#2-a-worked-example) gives. It is faster to
think, but the arm, not the thinking, sets the pace. [The
results](../10_the-results.md#2-the-results) compare all six.

Against [a world model, then plan with
it](../07_a-world-model-then-plan-with-it/01_what-it-is.md), the question is
whether to plan with a model or learn the push directly. That solution learns
how the world changes. It tries many pushes in its model before acting, so
**it can find a push nobody ever showed it.** This solution cannot. But the
world model costs much more on every push. And it needs a model of the world
good enough to plan with, which is harder to learn than a mapping. So this
solution is cheap but limited by its teacher. That one is costly but limited
only by its own model.

Against [SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md),
the question is training here against borrowing a large model. SmolVLA brings
much experience of robots in general, but none of this cell. This solution
brings the opposite: a small network that knows only this cell.

Against [SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md),
the question is where training starts. That solution uses this same method,
copying examples made here. But it starts from SmolVLA's borrowed weights, not
from random numbers. So the pair separates what the examples are worth from
what the pretraining is worth.

On the ladder, this solution is the first rung where all the learning happens
here, from nothing, on free examples. It is the cheapest real attempt at
learning this task in the book. Its limits are also the easiest to state in
advance.

← [What it needs](05_what-it-needs.md) · [A world model, then plan with it — what it is](../07_a-world-model-then-plan-with-it/01_what-it-is.md) →
