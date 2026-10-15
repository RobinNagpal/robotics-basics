# What it needs

This page lists what this solution needs: the software, the computer, the
data, and the upkeep.

## 1. What it needs

This is the hardest of the six solutions to set up. This section lists why.

**PyTorch, on this machine's built-in graphics.** It runs through PyTorch's
MPS backend, which uses the graphics chip built into a Mac. No separate
graphics card is needed. Nothing is downloaded, so there is no licence to
meet.

**A training set.** The first way needs arrangements rendered by the examiner,
with their id images. These cost only render time. The second way needs pairs
of pictures with the camera's movement logged. These cost arm time.

**A training run before it can answer anything.** The network has 144,339
weights. The pictures are 160 by 120 pixels. So a training run is short on
this machine. It can be run again whenever the cell changes.

**A file of weights that matches the cell.** This cost is easy to forget. The
code says what the cell is. The weights say what the cell looked like when
they were trained. Change the lighting, the camera or the glass sizes, and the
weights are out of date. No test of the code will notice.

**Very little at run time.** One pass of a small network over a small picture
takes milliseconds. One arm movement takes seconds. So this solution can
compute freely, and all its real cost is in building it.

The next page judges how well it works.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
