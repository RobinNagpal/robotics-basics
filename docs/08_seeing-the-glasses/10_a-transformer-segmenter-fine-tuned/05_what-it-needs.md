# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

This is one of the more demanding solutions in the set to set up, and it is
worth being plain about that before anyone starts.

It needs a **deep learning framework and the environment to run it in**, which
is a large dependency for a cell whose simplest answer is a page of arithmetic.
It needs a **downloaded file of weights**, which is large, which is fetched
rather than committed with the code, and which this project cannot produce, so
it comes from outside and is taken on trust.

It needs a **training set**, which the bench renders and labels for nothing,
including the crowded arrangements the cell's own rule would never produce. That
is the genuinely cheap part and it is what makes fine-tuning reasonable here. It
needs **time on the machine** for the fine-tune, far less than a start from
random numbers would need but still the largest cost in the solution, and the
second rung may need more of it than the first.

It needs **hardware it fits on**. The machine here is a laptop whose graphics
processor shares memory with the main processor, and PyTorch reaches that
graphics processor through its MPS backend, so the code would select MPS when it
is available and fall back to the main processor otherwise. There is no NVIDIA
card here and no CUDA. The shared memory is part of why a model of this size
fits at all, and the model being offered in a range of sizes is the other part,
because a smaller size can be chosen if the larger one does not fit.

And once fine-tuned it needs **a file of weights kept in step with the world**.
Change the camera, the way depth is shaded into grey, or the range of
proportions a kind is drawn from, and the file is quietly out of date in a way
no test of the code will notice. Against all that, what it needs at run time is
modest: one pass over one picture is a small fraction of the seconds an arm
movement costs, so the cost of this solution sits almost entirely in building it
rather than in running it.

The licence is the one thing it does not need to worry about. Apache 2.0 is
permissive: the model may be used, changed and shipped inside other work without
any obligation falling on the code around it. That is a real difference from
[YOLO as it downloads](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md) and [the same YOLO fine-tuned
here](../08_the-same-model-fine-tuned/01_what-it-is.md), both of which are covered by the AGPL, and it is
worth knowing before a choice is made rather than after.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
