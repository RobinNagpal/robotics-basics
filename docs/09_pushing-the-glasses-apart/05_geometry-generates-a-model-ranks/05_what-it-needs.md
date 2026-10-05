# Geometry generates, a model ranks — what it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights. It is deliberately short and deliberately separate
from the method, so that the cost of any of the six can be read without reading
how it works all over again.

## 1. What it needs

It needs **scikit-learn and NumPy**, both small, both pure software, and both
BSD 3-clause, so there is no licence condition to carry anywhere and nothing to
revisit if this work were taken further.

It needs the **enumerator**, which lives in
`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py` and is loaded
from there rather than copied, so the heading sweep, the stepped travel, the
four tests and the tipping rule have one definition in this repository. It is
also the part that decides the ceiling.

It needs a **training set**, which is a few thousand pairs of a candidate and
what happened to it, generated on the training half of the bench's tables and
executed there. That is minutes of bench time and no human labelling at all,
because the bench measures the table after every push in any case. It needs the
**held-out half** of the tables for marking, which the bench already enforces by
splitting its table numbers.

It needs **no accelerator**, and this is the clearest cost difference between
this solution and the four that follow it. A few hundred shallow trees on a few
thousand rows trains in seconds to minutes on an ordinary processor. There is
nothing to rent for a weekend and nothing to rent by the month, so the figure
to quote against the other solutions' rental costs is zero.

At run time it needs **one pass of the trees per candidate**, which is
arithmetic: each tree is three levels deep, so it asks three threshold
questions, and there are two hundred of them, which is six hundred comparisons
in all and no matrix multiplication anywhere. Even a candidate set in the thousands
costs a small fraction of the seconds one arm movement takes, so the compute
column on the scorecard is close to the fixed nudge's rather than to a
foundation model's.

And once fitted it needs **a model file kept in step with the cell**. Change
the heading sweep, the step length, the glass zone or the way the bench draws
its crowded tables, and the fitted model quietly describes a cell that no
longer exists, in a way no test of the code would notice.

← [Geometry generates, a model ranks — a worked example](04_a-worked-example.md) · [Geometry generates, a model ranks — how it compares](06_how-it-compares.md) →
