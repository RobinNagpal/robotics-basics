# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

This is the most demanding of the six to set up, and it is worth being plain
about that before anyone starts.

**A deep learning framework and the environment to run it in.** PyTorch, on
this machine's integrated graphics through the MPS backend. No dedicated
graphics card is needed, and nothing is downloaded, so there is no licence
condition on anything this solution uses.

**A training set.** For the first way, arrangements rendered by the examiner with their
id images, which costs render time and nothing else. For the second way, pairs of
pictures with the camera's movement logged beside each one, which costs arm
time.

**A training run**, before the solution can answer anything at all. The network
is small and the pictures are small, so the run is short enough on this machine
to be repeated whenever the cell changes, which is the property that makes the
next line bearable.

**A file of weights kept in step with the cell.** This is the cost that is easy
to forget. The code says what the cell is; the weights say what the cell looked
like when they were fitted. Change the lighting, the camera or the range of
proportions a kind is drawn from, and the file is quietly out of date in a way
that no test of the code will notice.

At run time what it needs is small: one pass of a small network over a small
picture, which is nothing beside the seconds an arm movement costs.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
