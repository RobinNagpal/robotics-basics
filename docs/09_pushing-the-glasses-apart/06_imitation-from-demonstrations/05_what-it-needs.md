# What it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights. It is deliberately short and deliberately separate
from the method, so that the cost of any of the six can be read without reading
how it works all over again.

## 1. What it needs

It needs **[LeRobot](https://github.com/huggingface/lerobot)**, which holds ACT
and Diffusion Policy as reference implementations, with **PyTorch** underneath.
LeRobot is Apache-2.0, and because this solution downloads no weights, the
weights file it produces is fitted entirely on data generated inside this
project and inherits no terms from anybody. That is as simple as a licence
position gets in this book: [SmolVLA as it
downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and [SmolVLA
fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md) both carry borrowed weights,
and this one carries none.

It needs **[geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md) working**, because that solution
is the teacher. This is a real dependency and not a preference: without a
program that chooses pushes well, there are no demonstrations, and with a
teacher that chooses badly the student has nothing worth copying. That is why
the two are built in that order.

It needed **two things the bench did not have**, and that was the third of the
honest costs. Both were missing from the bench's own `bench.py` when this
solution was designed. The first was a **rendered view of the table from the
top**: the bench returned numeric readings, and it did render the world, but
from the arm's side rather than straight down, and only for the films used to
check a run by eye. The second was a **path that accepts a chunk of
waypoints**: `push()` takes a parameterised push and *is* the macro that
expands it, so there was no way in for a trajectory. Both are now built —
`bench/top_view.py` and `Bench.follow` — and both were the real price of going
off the shelf, because every LeRobot policy expects pictures and a control-rate
action space. [One fixed nudge](../04_one-fixed-nudge/01_what-it-is.md) and the teacher need
neither, which is one more reason to build them first.

It needs **demonstrations**, which cost arm time on the bench and nothing else,
drawn only from table numbers below the dividing line. The prescription here
is to over-represent the crowded corner cases deliberately, so that the edge
of what the policy will face sits somewhere in the middle of what it was
trained on. **That part is not done**: the demonstration set is drawn from
consecutive table numbers, which is whatever mixture the bench's own table
generator produces, and the crowded corners are therefore as rare in the
training set as they are on the bench.

It needs **compute**, and this is the cheapest entry among the six. **Training
runs in hours.** The reason it is so modest is worth stating, because it is
easy to assume that anything with a transformer in it is expensive. The dataset
is small — thousands of pushes, each a picture and a short chunk — the network
is small by the standards of the foundation models in [SmolVLA as it
downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and [SmolVLA
fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md), and nothing has to be
learned about vision in general, only about this one cell's pictures of this
one task.

**In the end nothing was rented.** This document first budgeted tens of
dollars for a small accelerator, and that is still the right figure for
anybody who wants one. But a network of a few tens of millions of parameters
on a few thousand small pictures fits on the graphics processor an Apple M4
already has, in about an hour per training seed, so the whole of this solution —
demonstrations, several training seeds and the held-out run — was made on the
machine the project is written on. For comparison, renting an accelerator for
a weekend is of order a hundred dollars, and a small one for a month of order
five hundred, so even a generous schedule of retraining stays well inside a
weekend's rental if a laptop is not available.

At run time it needs very little: **one forward pass per chunk** for ACT, and
several passes per chunk for the denoising rung, against a push that takes the
arm seconds to carry out. The compute column on the scorecard is where that
difference between the two rungs becomes visible.

And once fitted, it needs **a weights file kept in step with the bench**.
Change how the view from the top is rendered, or the macro whose waypoints
became the labels, or the error the readings carry, and the file is quietly out
of date in a way no test of the code would notice.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
