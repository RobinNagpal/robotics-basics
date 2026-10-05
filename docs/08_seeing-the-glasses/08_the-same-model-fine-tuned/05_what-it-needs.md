# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## Contents

1. [What it needs](#1-what-it-needs)
2. [The licence](#2-the-licence)

## 1. What it needs

It needs the **Ultralytics package** and the model's weights, which the package
fetches by itself. That file is large, it comes from outside the project, and it
is not something to commit beside the code.

It needs **PyTorch**, reaching this machine's integrated graphics through its
MPS backend. There is no separate graphics card here, and memory is shared
between the graphics processor and the main processor, which is what lets a
model this size be trained at all on this machine.

It needs a **training set**, which the examiner renders and labels for nothing from
the training half of the arrangements, including the crowded arrangements the
cell's own placement rule would never produce. It needs **time on the machine**
for the training run, far less than a random start would need but not nothing.
It needs a **held-out half** for setting the bar on the confidence number and
for checking that the model learned the glasses rather than the arrangements,
and the examiner provides exactly that.

And once fitted, it needs **a weights file kept in step with the cell**. Change
the camera, the way depth is shaded into grey, or the range of proportions a
kind is drawn from, and the file is quietly out of date in a way no test of the
code would notice. Against all of that, what it needs at run time is modest: one
pass over one picture, which is a small fraction of the seconds an arm movement
costs. The cost of this solution sits almost entirely in building it rather than
in running it.

## 2. The licence

The choice of model carries a condition the rest of this project does not, and
anyone who chooses this solution should meet that condition here rather than
discover it later.

Ultralytics YOLO26-seg is licensed under the **AGPL-3.0**. The AGPL requires
that anybody who distributes the software, **or offers its functionality over a
network**, makes the complete corresponding source available under the same
terms. The network clause is the part that matters most here, because it reaches
a product that never gives a copy of the model to anybody and only serves
answers from it. Everything else this project depends on is permissively
licensed and can be used commercially, so this one component would change the
terms of the whole perception step if it were carried into a product.

**This solution carries the condition twice over, and that is the difference
from solution 3.** Solution 3 runs the downloaded weights and nothing more. This
one produces a new weights file by continuing the training of those weights, and
a file derived from an AGPL work is bound by the same terms. So the output of
the training run is not a clean asset the project owns outright: it inherits the
licence of the thing it was derived from, and it cannot be relicensed by having
been trained here.

That is understood and accepted, because these six solutions exist to compare
methods and learn what each one buys, and for that purpose the licence costs
nothing. If this method proved to be the right one and the work were headed
somewhere commercial, the replacement is straightforward, because permissively
licensed instance segmenters that do the same job exist: [solution
6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md) already uses one of them under
Apache 2.0. Nothing in this solution's design depends on the borrowed model
being this particular one. What is being tested is what fine-tuning buys on this
kind of picture, and that answer transfers to whichever model is licensed
conveniently.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
