# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and the licence that comes
with the weights.

## 1. What it needs

It needs a **deep learning framework** and the environment to run it, which is a
large dependency for a cell whose simplest answer is a page of arithmetic.

It needs a **weights file this project does not own**: 320 MB for
`facebook/sam2.1-hiera-base-plus`, fetched once into the solution's own
`weights/` folder and pinned to a version. That is a real difference from
solutions 2, 4 and 6, whose weights are produced here and can be produced again
at any time. These cannot be produced here at all.

It needs **arrangements for the keeper**, and far fewer of them than a network
fitted from scratch needs, because the keeper learns from a short table of
numbers rather than from pictures. The code's default is 12 arrangements, which
is 36 pictures across the three survey stations, and the run that produced this
solution's scorecard got 208 proposals out of them — 208 rows to fit 180 shallow
trees on. The examiner renders and labels them for nothing. The calibration needs
no arrangements beyond those, because it is fitted in folds of the keeper's own
table rather than on a second set of its own.

Fitting the keeper then takes **under a second** on the processor, with no
graphics card. What takes the time is running the borrowed model over those
arrangements to get the proposals: about eight seconds a picture on this
machine, so the 36 took 273 seconds, and that is where nearly all of
this solution's cost sits, at fitting time and at run time both. At run time it
needs one pass of the picture encoder per picture, which is the largest single
cost here and still small beside one movement of the arm. The machine is an
Apple processor with integrated graphics and memory shared with the processor,
which PyTorch reaches through its MPS backend, falling back to the processor
where that is absent; no separate graphics card and no CUDA are involved, and
the shared memory is why a model this size fits at all.

And it needs **the shading got right**, which is the only part where a careless
choice makes everything after it worse without anything complaining.

Finally, the **licence is permissive**, which is a real advantage rather than a
footnote. SAM 2's weights are Apache 2.0 and download without an account.
Solutions 3 and 4 use weights under the AGPL, which places conditions on
anything built around them, so on the day this cell becomes a product rather
than an experiment those two have a question to answer and this one does not.
The advantage does not carry forward: the newer generation this solution's
second way would use is gated and released under terms of its own.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
