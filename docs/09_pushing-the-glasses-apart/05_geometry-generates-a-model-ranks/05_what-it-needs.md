# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

It needs **scikit-learn and NumPy**, both small, both pure software, and both
BSD 3-clause, so there is no licence condition to carry anywhere and nothing to
revisit if this work were taken further.

It needs the **enumerator**, which lives in
`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py` and is loaded
from there rather than copied, so the heading sweep, the stepped travel, the
four tests and the tipping rule have one definition in this repository. It is
also the part that decides the ceiling.

It needs a **training set**, which was 4,844 pairs of a candidate and what
happened to it, generated on 190 of the examiner's training tables and executed
there. That is minutes of examiner time and no human labelling at all, because
the examiner measures the table after every push in any case. It needs the
**held-out half** of the tables for marking, which the examiner already enforces
by splitting its table numbers.

It needs **no accelerator**, and this is the clearest cost difference between
this solution and the four that follow it. Fitting the two hundred trees on
those rows took 2.2 seconds on a laptop processor, with most of the five minutes
`make train` spends going on making the pushes rather than on the fit. There is
nothing to rent for a weekend and nothing to rent by the month, so the figure to
quote against the other solutions' rental costs is zero.

At run time it needs **one pass of the trees per candidate**, which is
arithmetic: each tree is three levels deep, so it asks three threshold
questions, and there are two hundred of them, which is six hundred comparisons
in all and no matrix multiplication anywhere. The whole of one pass of the loop,
enumeration included, took 81 milliseconds against the printed rule's 82, so the
trees are not what the thinking time is spent on, and the compute column on the
scorecard is close to the fixed nudge's rather than to a foundation model's.

And once fitted it needs **a model file kept in step with the cell**. Change
the heading sweep, the step length, the glass zone or the way the examiner draws
its crowded tables, and the fitted model quietly describes a cell that no
longer exists, in a way no test of the code would notice.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
