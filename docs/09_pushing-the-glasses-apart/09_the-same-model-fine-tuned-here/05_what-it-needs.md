# What it needs

This page lists what this solution needs. It covers the libraries, the
machine, the data somebody has to supply, and the licence on the weights.

## 1. What it needs

It needs **LeRobot**, which has the Apache-2.0 licence. It needs the SmolVLA
weights, which the library downloads by itself. That file is large and comes
from outside the project, so it is not committed with the code. Read the terms
on the weights, not only the terms on the library. A file made by training
those weights further keeps their terms. Training here does not change the
licence. It also needs **PyTorch**, which runs both the training and the
model.

It needs **two parts of the examiner**, and both exist now. The first is a view
looking straight down, in [`bench/top_view.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/bench/top_view.py). A camera is fixed 750 mm above
the middle of the glass zone. It returns a 384 by 384 picture of the whole
zone. It is not the camera the films use, which looks down at a steep angle
from the arm's side. The second part is `Bench.follow()`, which carries out a
chunk of waypoints. It uses the waypoints at a fixed rate. It reports the same
record as a parameterised push, so the scorecard cannot tell the two apart.
Neither part was hard to build. They were needed because every LeRobot policy
expects pictures in and waypoints out.

It needs **solution 2**, because solution 2 is the teacher and its pushes are
the training set. It needs **simulator time** to record those pushes over the
training half of the tables. It needs a filter that drops the recordings where
something went wrong. And it needs the **held-out half** of the tables, to
check that the policy learned pushing and not the tables. The examiner already
keeps that split.

**It does not need a rented accelerator.** This page first said it would. The
training runs on this machine, an Apple Silicon Mac with no NVIDIA card,
through Metal. It held **1.02 GiB** of memory while it ran. [Low-rank
adaptation](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
explains why so little. Memory was never the problem. The trained model also runs here,
because SmolVLA needs only a few gigabytes to answer.

**Renting would buy time, not memory, and time is what this solution lacks.**
The thousand steps took 47 minutes on Metal, about three seconds a step.
[`correction/training.json`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/correction/training.json)
records this. The laptop was also running other training at the time. An
NVIDIA card would take a fraction of a second. LeRobot's own SmolVLA recipe is twenty thousand steps at
a batch of sixty-four. This run was a thousand steps at a batch of four. That
is **about one part in three hundred of the recipe's compute**, and every
number this solution reports carries that limit. To spend real compute, you
would rent. A few hours of a small accelerator costs tens of dollars. A weekend
costs about a hundred dollars, and a month about five hundred. Several training
seeds would multiply this. None of it was spent.

The project's old rule was that everything must run on this machine. This book
drops that rule. Each solution states what it needs and roughly what renting
it costs. **This solution turned out not to need the change.** A much larger
model would. [Solution 5 compares SmolVLA with
π0](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#9-the-price-of-the-model-and-why-this-model),
where memory really decides whether training fits.

Once trained, it needs **a correction kept in step with the cell**. Change the
camera, the way the top view is drawn, the range of glass shapes, or the
teacher. Then the correction is out of date, and no test of the code will
notice.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
