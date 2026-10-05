# What it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights. It is deliberately short and deliberately separate
from the method, so that the cost of any of the six can be read without reading
how it works all over again.

## 1. What it needs

It needs a **deep learning framework** and the environment to run it, which is a
large dependency for a cell whose simplest answer is a page of arithmetic.

It needs a **weights file this project does not own**, which is a real
difference from solutions 2, 4 and 6, whose weights are produced here and can be
produced again at any time. These cannot be produced here at all, so they have
to be fetched, pinned to a version, and stored where a run can find them.

It needs **arrangements for the keeper**, which the bench renders and labels for
nothing, and far fewer of them than a network fitted from scratch needs, because
the keeper learns from a short table of numbers rather than from pictures. The
calibration needs no arrangements beyond those, because it is fitted in folds of
the keeper's own table rather than on a second set of its own.

Fitting the keeper takes **seconds** once the proposals are in hand, with no
graphics card. What takes the time is running the borrowed model over those
arrangements to get the proposals, which is where nearly all of this solution's
cost sits, at fitting time and at run time both. At run time it needs one pass
of the picture encoder per picture, which is the largest single cost here and
still small beside one movement of the arm. The machine is an Apple processor
with integrated graphics and memory shared with the processor, which PyTorch
reaches through its MPS backend, falling back to the processor where that is
absent; no separate graphics card and no CUDA are involved, and the shared
memory is why a model this size fits at all.

And it needs **the shading got right**, which is the only part where a careless
choice makes everything after it worse without anything complaining.

Finally, the **licence is permissive**, which is a real advantage rather than a
footnote. Solutions 3 and 4 use weights under the AGPL, which places conditions
on anything built around them, so on the day this cell becomes a product rather
than an experiment those two have a question to answer and this one does not.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
