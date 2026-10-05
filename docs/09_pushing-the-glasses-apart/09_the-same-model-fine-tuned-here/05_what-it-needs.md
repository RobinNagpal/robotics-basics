# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

It needs **LeRobot**, which is Apache-2.0, and the SmolVLA weights, which the
library fetches by itself. That file is large, it comes from outside the
project, and it is not something to commit beside the code. The terms on the
weights are the thing to read rather than the terms on the library, because a
file produced by continuing their training inherits whatever they carried, and
no amount of training here relicenses it. It needs **PyTorch** underneath,
which is what both the training and the forward pass run on.

It needs **the two parts of the examiner this solution waited on**, and both are
there now. A rendered view looking straight down is the input this model takes,
and `bench/top_view.py` is that view: a camera fixed 750 mm above the middle of
the glass zone, looking straight down, returning a 384 by 384 picture that
frames the whole zone. It is separate from the camera the films use, which
looks steeply down from the arm's side. A path by which a chunk of waypoints is
carried out as an action is the output this model produces, and `Bench.follow()`
is that path: it takes the waypoints as they come, consumes them a fixed period
apart, and reports the same record a parameterised push does, so the scorecard
cannot tell which door an action came through. Neither was hard, and both were
the real price of going off the shelf, because every LeRobot policy expects
pictures and an action space at control rate.

It needs **solution 2 built**, because solution 2 is the teacher and its pushes
are the training set. It needs **simulator time** to record those pushes over
the training half of the tables, unattended, and a filter that discards the
recordings in which something went wrong. It needs the **held-out half** of the
tables, which the examiner already enforces, for checking that the policy learned
pushing rather than the tables.

**It does not need a rented accelerator, and this is the place the document
was wrong.** The training runs on this machine, an Apple Silicon Mac with no
NVIDIA card, through Metal. Measured while it ran: **1.02 GiB held**, with the
borrowed weights, the correction, the correction's gradients and the
optimiser's running averages all in memory at once. Low-rank adaptation is
exactly why, and for exactly the reason the section above gives — only the
correction's four million numbers carry gradients and optimiser state, so what
has to be held is the model plus a little. What the writing got wrong was how
little "a little" is at 450 million parameters. Memory was never close to being
the obstacle.

**What renting buys here is time, not memory, and that distinction matters
because time is what this solution is actually short of.** A training step on
Metal takes a second or two where an NVIDIA card would take a fraction of one,
and LeRobot's own SmolVLA fine-tune is twenty thousand steps at a batch of
sixty-four. What ran here is a thousand at a batch of four, which is a small
fraction of that compute, and **every number this solution reports carries
that caveat**. A step took about four seconds, on a laptop that was also
running three other solutions' training at the time. Renting is still how real compute would be spent on it:
hours of a small accelerator is of order tens of dollars, a weekend of order a
hundred, and a month of order five hundred, which is the scale to keep in mind
if the training has to be repeated over several seeds. None of it was spent.

The project's old rule was that everything must run on this machine. This book
lifts that rule, so that each solution states what it needs and roughly what
renting it costs, in the same way a licence is stated. **The lifting turned
out not to be needed for this solution**, which is the opposite of what this
section first claimed. Where it is still needed is the second rung: π0, which
belongs to the same family, holds
about 3.3 billion parameters and its full fine-tune floor is above 70 GB, and
there the question really is whether the training fits. At 450 million it was
not a question. And **the trained model runs here perfectly well** too,
because SmolVLA uses a few gigabytes at inference, so neither building this
solution nor using it needed anything rented.

And once trained, it needs **a correction kept in step with the cell**. Change
the camera, the way the view from the top is rendered, the range of proportions
a kind is drawn from, or the teacher, and the file is quietly out of date in a
way no test of the code would notice.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
