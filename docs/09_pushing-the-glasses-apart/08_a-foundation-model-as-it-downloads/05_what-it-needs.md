# What it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights. It is deliberately short and deliberately separate
from the method, so that the cost of any of the six can be read without reading
how it works all over again.

## 1. What it needs

Less than anything else in this book, which is the whole point.

**Software.** [LeRobot](https://github.com/huggingface/lerobot), licensed
Apache-2.0, which holds the policy as a reference implementation, and PyTorch
underneath it, licensed BSD-3-Clause. Both are permissive, so neither obliges
this project to publish its own source, which is what a copyleft licence such
as the AGPL would do. The weights themselves carry their own terms, which a
reader taking this forward should check before anything is shipped, because a
licence on weights is not the same thing as a licence on the library that
loads them. Nothing here says what those terms are, since nothing in this
project records them. What can be
said structurally is that a file produced by continuing their training, as
[solution 6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) produces one, inherits whatever the
borrowed weights carried, so this solution is the half of the pair that leaves
no new file to carry anything.

**The weights.** Downloaded, used unchanged, and about 450 million parameters,
so a few gigabytes while answering.

**Hardware.** A laptop. There is nothing to train, so there is no accelerator
to rent for this solution at all. This document said that solution 6 would pay
for the accelerator while solution 5 paid for nothing, and that turned out to
be wrong about the other half of the pair: [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md)'s low-rank fine-tune of this same model held
**1.02 GiB** while it ran, on this machine's own Metal, so neither half rented
anything. The 22 GB and 70 GB floors quoted above belong to π0, which is
several times larger. The one case where renting would still be sensible is
evaluation throughput rather than capability — the scorecard asks for several
runs per solution, and many forward passes on a laptop take a while. For
scale, renting an accelerator for a weekend costs of order a hundred dollars,
and a small one for a month costs of order five hundred, so even running the
evaluation on rented hardware is at the cheap end of this book.

**Data.** None. No demonstrations, no labels, no held-out set, and nothing to
keep in step with the cell when the cell changes.

**What the bench had to grow.** Two things, and both were gates rather than
conveniences: the rendered view of the table from the top, and the path that
accepts a run of waypoints without the push macro. [The test
bench](../02_the-test-bench.md) now provides both, and both are shared with solutions
3 and 6, so the cost was paid once for three solutions rather than for this
one.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
