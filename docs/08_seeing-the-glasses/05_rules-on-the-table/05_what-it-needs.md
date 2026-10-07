# What it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights.

## 1. What it needs

**No labelled data.** Nothing in the method is fitted, so the examiner's training
half of the arrangements is never read.

**No training time and no weights file.** There is nothing to train and nothing
to keep in step with the cell.

**No graphics processor.** The work is a comparison over a grid of depth
readings, a back-projection per kept pixel, dropping one column of numbers, a
spreading-out step over a grid of 5 mm squares, and a direct least-squares solve
per group. All of it is ordinary processor work on a picture of 320 by 240
pixels.

**Two libraries, both already in the cell.** NumPy does the arithmetic over the
depth readings. OpenCV does the picture handling the cell already does, which
here means growing and joining the marked squares into groups, and finding the
outside of a patch of dots before a circle is fitted to it.

**Three things from the problem rather than from the sensor.** The method needs
the table's height, which the cell knows because the table is bolted to the
arm's own frame; the guaranteed smallest distance between two glass centres,
which is what gives the grouping distance an upper limit; and the range of
widths the kind on the table is allowed, which is what gives the width check
something to compare against.

**And depth readings**, which is the one requirement that is not free, and the
one [how it compares](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
is mostly about.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
