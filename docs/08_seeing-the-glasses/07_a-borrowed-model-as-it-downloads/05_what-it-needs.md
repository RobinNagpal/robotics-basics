# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## Contents

1. [What it needs](#1-what-it-needs)
2. [The licence, which is the real cost here](#2-the-licence-which-is-the-real-cost-here)

## 1. What it needs

Very little, which is the whole point.

It needs the Ultralytics package and the model's weights, which the package
downloads by itself the first time the model is used, so there is no data
preparation step of any kind. The download is 6.4 MB and is not committed. It
runs on this machine's integrated graphics through PyTorch's MPS backend, the
same backend the rest of this project's learned work uses, and the weights are
small enough that memory is not a concern. The model family comes in several
sizes, and the smaller end is the sensible place to start, because the glasses
fill a reasonable part of the frame and a larger model costs time without
obviously buying accuracy on silhouettes this plain. Whichever size is chosen,
solution 4 continues the training of that same one, because the pair is only
clean while both start from the same file.

At run time it is cheap. One picture takes 0.02 seconds with the model already
loaded, so a whole 20-arrangement block of 60 pictures takes about six seconds
including the rendering.

What it does not need is the expensive part of every other learned solution
here: no labelled pictures, no training run, no weights file to keep in step
with the cell, and no held-out set beyond the small one used to set the bar on
the confidence number.

## 2. The licence, which is the real cost here

This section exists because the choice of model carries a condition the rest of
the project does not, and a reader who takes this solution forward should meet
that condition here rather than discover it later.

Ultralytics YOLO26-seg is licensed under the AGPL-3.0. The AGPL requires that
anybody who distributes the software, **or offers its functionality over a
network**, makes the complete corresponding source available under the same
terms. That network clause is the demanding part, because it reaches a product
that never ships a copy of the model to anybody and only ever serves answers
from it. Everything else this project depends on is permissively licensed and
can be used commercially without that obligation, so this one component would
change the terms of the whole perception step if it were carried into a product.

The choice is made here with that understood. These six solutions exist to
compare methods and to learn what each kind of model buys, and for that purpose
the licence costs nothing, because nothing is shipped and nothing is served.
Nothing in this solution's design depends on the borrowed model being this
particular one, which is worth saying plainly: what is being tested is whether
an off-the-shelf instance segmenter works here at all, and the answer to that
question transfers to whichever one is licensed conveniently. [Solution
6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md) already uses a permissively licensed segmenter, and
it is not the only permissively licensed segmenter that could do this job, so
the replacement is straightforward if the method proved to be the right one and
the work were headed somewhere commercial.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
