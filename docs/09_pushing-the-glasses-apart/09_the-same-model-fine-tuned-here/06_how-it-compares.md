# The same foundation model, fine-tuned here — how it compares

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

**It is fitted on the inputs it will be shown.** That is the single strongest
thing about it, and the thing its partner cannot claim. The domain gap is
closed by construction rather than left to hope.

**Its demonstrations cost nothing.** The teacher is a program, so the usual
reason not to fine-tune a policy — that somebody has to teleoperate the task
hundreds of times — does not apply here.

**It needs no reward function.** That is a larger advantage than it sounds,
because a reward is a score and what this problem has are constraints. Written
as a fine, "never topple a glass" becomes a price, and a price is a trade the
policy may make. Learning from examples of correct pushes leaves "never topple"
as a constraint the teacher enforced and the shared check enforces again.

**Its training is affordable, and its run-time cost is its partner's.** The
low-rank correction fits in the memory of a laptop, which is further than this
document expected it to go, and it folds into the weights afterwards, so
nothing about running it is more expensive than running the model as it
downloads.

**It is one half of the cleanest comparison in this book**, and that is a
strength of the arrangement rather than of the model.

Against that, four kinds of weakness.

**What it inherits from being a borrowed model.** It is about 450 million
parameters, and a large fraction of them serve a language channel this task
does not use, because there is one instruction. It commits to a chunk, so a
surprise inside a push is carried out. It cannot explain anything it did. And
the correction is low-rank, so it adapts less deeply than a full fine-tune
would, which means it may leave part of what fine-tuning could buy unclaimed.

**What it inherits from its teacher.** Its ceiling is solution 2, because
nothing ever showed it a better push and nothing scores its own attempts. Its
training set was filtered to successes, so it was fitted on the easy half of
its teacher's experience and has never seen the hard half. And it has seen no
refusals at all, so it proposes pushes on glasses that must not be pushed.

**What it owes to being trained on one bench.** It becomes good here and worse
elsewhere. Part of what it gains over its partner is this bench's own friction
absorbed into its weights, which is a memorised constant rather than an ability,
and it would not survive a real table. A small or uniform training set would
teach it the tables rather than the pushing, and only the held-out half would
reveal it. And it is stochastic, so a single run is not a measurement, which
bears on this document more than on any other in this book, because what is
being measured here is a gap.

**What it does not do at all.** It does not refuse, it does not choose
destinations, it does not own the loop, and it does not stop a push that is
going wrong. Each of those belongs to the shared machinery, and a reader who
credits the model with them is crediting it with the geometry's work.

## 2. The general ideas behind this

Nothing in this solution was invented for glassware. Every part of it is a
standard piece of current practice, and each is worth knowing on its own,
including where it is normally the wrong tool.

### Transfer learning and fine-tuning

Take a model fitted on a large general task, keep its weights, and continue
training on the new data. It works because the early layers of a model learn
things common to the whole domain — edges and textures for vision, smoothness
and approach for motion — and only the later layers learn what is specific to
the original task. Yosinski and colleagues
([arXiv:1411.1792](https://arxiv.org/abs/1411.1792)) measured that directly for
vision, showing how well a layer transfers falling away with depth.

It is normally the right choice whenever data for the real task is scarce,
which is almost always. It is normally the wrong choice when data is free and
plentiful **and** the new task looks nothing like the borrowed one, because
then the borrowed weights bring knowledge of a world you do not have while also
forcing your model to be the size somebody else chose. This solution sits
awkwardly between those two, since its demonstrations are free and its inputs
are unlike anything in the borrowed datasets, which is precisely the argument
[solution 3](../06_imitation-from-demonstrations/01_what-it-is.md) makes and this one
deliberately takes the other side of. For more, see [transfer
learning](https://en.wikipedia.org/wiki/Transfer_learning).

### Low-rank adaptation

Instead of changing every weight, add a correction forced through a narrow
squeeze, so that only a small number of new values have to be learned and
stored. The method is **LoRA**, Hu and colleagues
([arXiv:2106.09685](https://arxiv.org/abs/2106.09685)), and it is the standard
way a large borrowed model is adapted on modest hardware.

It is right whenever the model is too large to fine-tune fully and the new task
is near enough to the old one that a small correction can express the change.
It is wrong, or at least limiting, when the new task is far from the old one,
because a correction confined to a few directions cannot hold a change that
needs the whole of a weight table. It is also the wrong tool when the model is
small enough to fine-tune fully for the same money, since then the constraint
buys nothing. Here the model is small and the task is far, which is an
uncomfortable combination and the honest reason the result reads as a lower
bound.

### Behaviour cloning, and its ceiling

Record what a working expert did at each moment, and fit a model to predict the
action from the observation. It is ordinary supervised learning, with no reward
and no exploration, which is what makes it cheap and stable. The price is that
the expert is the ceiling, and that the policy only ever sees states the expert
visits.

It is right when a correct expert already exists and the thing wanted is a fast
or more robust version of it, which is the case here. It is wrong when the
expert is the thing you were trying to improve on, because imitation cannot
exceed what it imitates. The classic failure is **compounding error**: the
policy is slightly wrong, so it drifts into states the demonstrations never
covered, where it is more wrong. **DAgger** (Ross, Gordon and Bagnell, 2011) is
the standard repair, and it is unusually cheap here because the expert is a
program that can be asked for a label at any state.

### Domain adaptation

A model fitted on one kind of data and used on another is working across a
**domain gap**, and the family of methods for closing it is **domain
adaptation**. Fine-tuning on data from the new domain is the simplest member of
that family and the strongest when such data exists.

It is right whenever examples of the real input can be obtained, as here. It is
unavailable when they cannot, and then the harder members are needed: adapting
with no labels, or varying the training data so widely that the new domain
falls inside the range already covered. That second one, **domain
randomisation**, is the usual answer when a policy trained in a simulator has
to work on a real robot, and it is worth knowing here because the problem it
solves is the mirror image of this one. It is also the thing that would have to
be added before any of this reached a real table, since a policy that absorbed
one bench's friction has learned a number rather than a skill.

### Catastrophic forgetting

A network trained on a new task tends to lose what it knew of the old one,
because the weights that held the old knowledge are the weights the new
training moves. The effect was first described for simple networks by McCloskey
and Cohen, and the modern treatment protects the weights that mattered most to
the old task (Kirkpatrick and colleagues,
[arXiv:1612.00796](https://arxiv.org/abs/1612.00796)).

It matters a great deal when a model has to stay good at several things, which
is why continual learning is a field at all. It matters little here, because the
model is wanted for one bench and nothing else, and that is the honest reason
the usual precautions are not taken: not that the effect is absent, but that its
cost in this project is close to zero. Low-rank adaptation happens to soften it
for free, since the borrowed weights are never overwritten and the correction
can be removed.

### Overfitting and the held-out split

A model fitted on a finite set of examples can fit accidents of those examples
rather than the thing they are examples of. The standard defence is to divide
the data, fit on one part and measure on another, so that any such accident
shows as a gap between the two scores.

It is the right practice everywhere and there is no case against it. Its usual
difficulty is that data is scarce, so dividing it hurts. That difficulty does
not arise here, because tables are generated from numbers rather than collected,
and more of them cost only simulator time. For more, see
[overfitting](https://en.wikipedia.org/wiki/Overfitting).

### Action chunking

Predict a short run of consecutive actions in one pass rather than one action at
a time. It is the mechanism behind ACT and it is what SmolVLA emits. One action
at a time makes a policy dither, and dither during a push is a knock; a chunk
commits to a smooth short motion, which is what a push is, and it also cuts the
number of decisions per table, which matters because compounding error compounds
per decision.

It is right for smooth contact-rich motions, which is what this problem has. It
is wrong where a fast reaction inside the chunk is needed, because the chunk is
already decided, and here nothing fills that gap: the early abort that would
have filled it is a design and the bench only stops a push at a jam. For the
same
reason, the bench had to be designed to accept chunks: forcing a chunked policy
down to three numbers would have measured a damaged version of the method rather
than the method.

## 3. Where it sits among the other five

[The six solutions](../03_the-six-solutions.md) form a ladder, ordered by how much of each one
was fitted in this cell, and this one stands at the top of it, because all of
its fitting happens on a borrowed model.

Against [solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) there is nothing to compare
except the training, and that is the whole point. Same library, same model,
same downloaded weights, same tables, same readings, same rendered view, same
instruction, same output, same shared checks, same marking, same cost per
forward pass, and the same agreed convention for reading a waypoint. The one
thing that could be mistaken for a second variable — that this solution's
actions are fitted to this cell's own scale — is a property of those trained
weights rather than something changed beside them, so it is part of what is
being measured. Whatever separates the two scores is what fine-tuning bought,
and nothing else can be blamed for it, with the two qualifications this
document has already made: the correction is low-rank, so the answer is a lower
bound, and the agreed convention has to be chosen fairly or the gap measures
that too. **If this document is read for one reason, it should be that one.**

**And the measurement, now that it exists, answers it in a way this document
did not anticipate.** This solution's own README has the numbers; what they
say is that training worked and the score got worse. The fine-tuned model's chunks
are much closer to the teacher's than the borrowed model's, and it brings the
jaw down to the table where the borrowed model never did — but two thirds of
its pushes are blocked coming down, because it never learned where to put the
jaw down, and 46 glasses a run go over. Solution 5 stays out of the *wrong*
column by never reaching a glass at all: it hovers, refuses nearly everything,
and is marked correct but incomplete. So the gap between the two is not a
measurement of training buying nothing. It is a measurement of training buying
enough competence to act and not enough to act safely, on a scorecard where a
toppled glass cannot be undone. **A policy that does nothing scores better
than a policy that does the wrong thing**, and any reading of this pair that
skips that sentence has misread it. The honest conclusion about the method is
therefore still open, and what it is waiting on is more training — the compute
spent here is about one part in three hundred of what the recipe asks — and
DAgger, because "the jaw came down on a glass" is precisely a state the
teacher never visits and so precisely what these demonstrations cannot teach.

Against [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md), the comparison is
borrowing against building, and it is the second clean pair this solution is
part of. Both learn from the same demonstrations, drawn from the same training
half of the same tables, so the data is held still. Solution 3 fits ACT here
from random numbers, so the project owns every number in it, can regenerate
them, and pays nothing for a language channel it does not use. This solution
borrows 450 million numbers fitted on other robots and adjusts a few of them.
The pair therefore asks whether general knowledge of robot motion, gathered
from 487 datasets of a world this cell is not, is worth more than a small model
fitted exactly to this one.

Against [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md), the comparison is the teacher
against the student, and it is not an even comparison in either direction.
Solution 2 is geometry with a small fitted ranker on top; it explains its
refusals, needs no accelerator and no borrowed weights, and it is the ceiling
on the pushes this solution imitates. This solution cannot push better than its
teacher at its best, so if it wins anything it wins consistency in the cases
where the teacher was brittle. Anyone reading the scorecard should expect
solution 2 to be hard to beat, and should treat a large win for this solution
as a question about the teacher's ranker rather than a triumph.

Against [solution 1](../04_one-fixed-nudge/01_what-it-is.md), the comparison is the cheapest
thing against the most expensive. Solution 1 computes one push by fixed
arithmetic and looks again, costs nothing to build or run, and is in this book
to answer the question of whether any learning beats a fixed nudge at all. If
this solution does not beat it by a margin larger than its own spread, the
450 million parameters and the hours of training have bought nothing.

Against [solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md), the comparison is planning against
reacting. Solution 4 learns how the table changes and searches over candidate
pushes at run time, so it can be told about a new constraint by changing what
it searches for, and it pays for that in computation on every push. This
solution holds its whole answer in its weights and emits a chunk in one pass,
so it is a different kind of expense per push, and can only be changed by
training it again.

Read as a ladder, the six measure what each increment of fitting buys. This
solution is the rung where all of the fitting happens on borrowed weights, and
its partner one rung below is the rung where none of it does. The distance
between those two rungs is the most valuable single number this book can
produce, which is why it is the first thing this document said and the last.

← [The same foundation model, fine-tuned here — what it needs](05_what-it-needs.md) · [The six solutions side by side](../10_the-results.md) →
