# What it needs

This page lists what this solution needs: its libraries, its machine, its data
and its licence.

## 1. What it needs

It needs **scikit-learn and NumPy**. Both are small, and both are under the BSD
3-clause licence. So there is no licence condition to follow.

It needs the **enumerator**, which is the code that lists the pushes. It lives
in [`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py). This solution
loads it from there and does not copy it. So the headings, the steps, the four
tests and the tipping rule are written in one place only. The enumerator also
sets the limit on how good this solution can be.

It needs a **training set**. This was 4,844 pushes with their results, made on
190 of the examiner's training tables. That takes minutes of simulator time and
no human labelling. It also needs the **held-out tables** for scoring. The
examiner already keeps those apart.

It needs **no accelerator**. This is the clearest cost difference from the four
solutions after it. Fitting the two hundred trees took 0.9 seconds on a laptop
processor. Most of the five minutes that `make train` takes goes on making the
pushes, not on the fit. So there is nothing to rent, and its rental cost is
zero.

At run time, it needs **one pass through the trees for each candidate**. Each
tree asks three questions, and there are two hundred trees. That is six hundred
comparisons, with no matrix maths. One full pass of the loop took 102
milliseconds per push, against 98 for the printed rule. So the trees add very
little thinking time.

Once fitted, it needs **a model file that matches the cell**. If the cell
changes, the model goes out of date and nothing warns you. [How it
compares](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains this weakness.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
