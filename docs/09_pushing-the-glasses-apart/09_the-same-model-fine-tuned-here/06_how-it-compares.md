# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks. It names the general ideas behind it, and places it beside the
other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The earlier pages showed how the solution works. This section adds up its
strengths and weaknesses.

It has four strengths. First, it is trained on the kind of input it will be
shown, so the domain gap is closed. Solution 5 cannot claim this. Second, its
demonstrations cost nothing, because the teacher is a program. Third, its
training fits on a laptop, and it costs the same to run as solution 5. Fourth,
it is one half of the cleanest comparison in the book.

**It also needs no reward function.** A reward is a score, but this problem
has rules. Written as a penalty, "never topple a glass" becomes a price, and a
policy may choose to pay a price. Copying correct pushes keeps "never topple"
as a rule. The teacher kept it, and the shared check keeps it again.

Its weaknesses come in four groups. [How it
works](03_how-it-works.md#5-what-fine-tuning-closes-and-what-it-cannot-touch)
explains each one where it arises.

- Some come from the borrowed model. It has about 450 million parameters, and
  many of them serve a language part this task does not use. It commits to a
  whole chunk. It cannot explain what it did. And its correction is low-rank,
  so it may not get all that fine-tuning could give.
- Some come from its teacher. It cannot push better than solution 2. Its
  training set held only successes. It saw no refusals, so it proposes pushes
  on glasses that must not be pushed.
- Some come from training on one examiner. It gets better here and worse
  elsewhere. Part of its gain is this examiner's friction stored as a fixed
  value. And it is random, so one run is not a measurement.
- Some jobs it does not do at all. It does not refuse, choose destinations,
  own the loop, or stop a push that goes wrong. The shared machinery does all
  of these.

These strengths and weaknesses come from standard ideas. The next section
names them.

## 2. The general ideas behind this

The strengths and weaknesses above come from a few standard ideas. None was
invented for glasses. Each is worth knowing on its own, including when it is
the wrong tool.

### Transfer learning and fine-tuning

Take a model trained on a large general task, keep its weights, and continue
training on new data. This works because early layers learn general things,
such as edges in pictures or smoothness in motion. Yosinski and colleagues
([arXiv:1411.1792](https://arxiv.org/abs/1411.1792)) measured this for vision.
They showed that a layer transfers less well the deeper it is.

It is usually right when data for the real task is scarce. It is usually wrong
when data is free **and** the new task looks nothing like the old one. Then the
borrowed weights bring knowledge you do not need, and fix the model's size
too. This solution is between those two cases. Its data is free, and its
inputs are unlike the borrowed data. [Solution
3](../06_imitation-from-demonstrations/01_what-it-is.md) takes the other side
of this choice. For more, see [transfer
learning](https://en.wikipedia.org/wiki/Transfer_learning).

### Low-rank adaptation

Add a small correction through a narrow squeeze, instead of changing every
weight. The method is **LoRA**, from Hu and colleagues
([arXiv:2106.09685](https://arxiv.org/abs/2106.09685)). It is the standard way
to adapt a large model on modest hardware.

It is right when the model is too large to train fully and the new task is
close to the old one. It is weak when the new task is far away. It buys nothing
when the model is small enough to train fully for the same money. Here the
model is small and the task is far. So the result is a lower bound, as [how it
works](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
explains.

### Behaviour cloning, and its ceiling

Record what an expert did, and train a model to copy it. There is no reward
and no trial and error. The expert is the ceiling, and **DAgger** is the
standard repair for the states the expert never visits. [Solution 3
explains both](../06_imitation-from-demonstrations/03_how-it-works.md#6-compounding-error).

### Domain adaptation

A model trained on one kind of data and used on another works across a
**domain gap**. The methods for closing it are called **domain adaptation**.
Fine-tuning on data from the new domain is the simplest of them. It is also
the strongest, when such data exists.

When such data cannot be had, harder methods are needed. One is **domain
randomisation**. It varies the training data so widely that the new domain
falls inside it. This is the usual way to move a simulator policy to a real
robot. It would be needed before this policy reached a real table, because
this policy has learned one examiner's friction as a fixed value.

### Catastrophic forgetting

A network trained on a new task tends to lose what it knew of the old one.
McCloskey and Cohen first described this for simple networks. Kirkpatrick and
colleagues ([arXiv:1612.00796](https://arxiv.org/abs/1612.00796)) protect the
weights that mattered most to the old task.

It matters when a model must stay good at several things. It matters little
here, because the model is only wanted for one examiner. Low-rank adaptation
also softens it, because the borrowed weights are never overwritten.

### Overfitting and the held-out split

A model can learn chance details of its examples instead of the skill. The
standard defence is to train on one part of the data and test on another. The
usual difficulty is that data is scarce. Here it is not, because tables are
generated from numbers. For more, see
[overfitting](https://en.wikipedia.org/wiki/Overfitting).

### Action chunking

Predict a short run of actions in one pass, instead of one action at a time.
ACT does this, and so does SmolVLA. [Solution 3
explains](../06_imitation-from-demonstrations/03_how-it-works.md#4-action-chunking-and-why-it-matters)
why it suits pushing and what it costs.

These ideas explain the method. The next section shows where its score puts
it among the six.

## 3. Where it sits among the other five

The ideas above explain how the solution behaves. This section places its
measured score beside the others.

[The six solutions](../03_the-six-solutions/01_how-the-six-compare.md) form a
ladder, ordered by how much of each one was fitted in this cell. This solution
is at the top, because all of its fitting is done on a borrowed model.

Against [solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md),
only the training differs. [Solution 5's
comparison](../08_a-foundation-model-as-it-downloads/06_how-it-compares.md#3-where-it-sits-among-the-other-five)
explains why this is the cleanest pair. Two limits apply. The correction is
low-rank, so the gap is a lower bound. And the reading of the waypoints must be
fair to both, or the gap measures that too.

**The measurement gives an answer this book did not expect.** The training
worked as training. The trained model's chunks are much closer to the
teacher's, and it brings the jaw down to the table. But it made the score
worse. The numbers below are the median of three runs over the 50 held-out
tables.

- About three pushes in five are **blocked on the way down**: 227 of 369. The
  jaw comes down onto a glass, because the model never learned where to put it
  down.
- **40 glasses fall over** in a run. Solution 5 topples 12.
- **36 of the 50 tables are marked wrong.** Solution 5 has 9.

![Where the pushes went before and after the training: the borrowed model's pushes nearly all touch nothing, because its chunks stay 217 mm above the table, while the fine-tuned model's come down to the 75 mm the jaw pushes at and are then mostly stopped by a glass on the way down.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-where-the-pushes-went.png)

Solution 5 stays out of the *wrong* column because it never reaches a glass.
It hovers, refuses nearly everything, and is marked correct but incomplete. So
the gap does not show that training bought nothing. It shows that training
bought enough skill to act, but not enough to act safely. A toppled glass
cannot be undone. **So a policy that does nothing scores better than a policy
that does the wrong thing.** Any reading of this pair must keep that sentence.

The verdict on the method is still open. Two things should be tried first. One
is more training, because this run used [about one part in three hundred of
the recipe's compute](05_what-it-needs.md). The other is DAgger. "The jaw came
down on a glass" is a state the teacher never visits, so these demonstrations
cannot teach it.

Against [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md),
the question is borrowing against building. Both learn from the same
demonstrations, so the data is held still. Solution 3 trains ACT here from
random numbers, owns every number in it, and pays nothing for language. This
solution borrows 450 million numbers trained on other robots and adjusts a few.
So the pair asks whether general knowledge of robot motion beats a small model
trained only on this cell.

Against [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md),
the question is teacher against student. Solution 2 explains its refusals and
needs no borrowed weights. It is also the ceiling on the pushes this solution
copies. So a large win for this solution would be a question about the
teacher's ranker, not a success.

Against [solution 1](../04_one-fixed-nudge/01_what-it-is.md), the question is
the cheapest method against the most expensive. Solution 1 is a fixed nudge,
and every other solution must beat it. If this solution does not beat it by
more than its own spread, the 450 million parameters bought nothing.

Against [solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md),
the question is planning against reacting. Solution 4 learns how the table
changes and searches over pushes at run time. So it can take a new rule by
changing its search, and it pays in computation on every push. This solution
holds its whole answer in its weights. It can only change by training again.

On the ladder, this solution is where all the fitting happens on borrowed
weights. Solution 5, one step below, is where none of it does. The distance
between those two is the most useful single number this book can give. [The
results](../10_the-results.md) set all six scores side by side.

← [What it needs](05_what-it-needs.md) · [The six solutions side by side](../10_the-results.md) →
