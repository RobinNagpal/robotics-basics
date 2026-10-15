# What it needs

This page lists what this solution needs: the libraries, the machine, the data
and any licence.

## 1. What it needs

The list below follows the method from the earlier pages, one need at a time.

**No labelled data.** Nothing in the method is fitted. So it never reads the
examiner's training half of the arrangements.

**No training and no weights file.** There is nothing to train, and nothing to
keep up to date with the cell. So there is also no licence to follow.

**No graphics processor.** The work is simple arithmetic on a picture of 320 by
240 pixels. It compares heights, back-projects the kept pixels, drops one
column of numbers, grows a grid of 5 mm squares, and does one direct solve per
group. An ordinary processor does all of it.

**Two libraries, both already in the cell.** NumPy does the arithmetic on the
depth readings. OpenCV grows and joins the marked squares into groups. It also
finds the outline of a patch of dots before a circle is fitted to it.

**Three facts from the problem, not from the sensor:**

- the table's height, which the cell knows because the table is bolted to the arm's frame;
- the smallest distance between two glass centres, which sets the upper limit on the grouping distance;
- the range of widths this kind of glass can have, which the width check uses.

**Depth readings.** This is the one need that is not free. [How it
compares](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains why.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
