# What it needs

This page is the bill for this solution. It lists the libraries, the machine,
the data and the licence of the weights. The worked example ended on the time
one picture takes, and this page puts that time in the full cost.

## 1. What it needs

It needs a **deep learning framework**, PyTorch, and the setup to run it. That
is a large dependency for a cell whose simplest answer is a page of arithmetic.

It needs a **weights file this project does not own**. The file for
`facebook/sam2.1-hiera-base-plus` is 320 MB. It is fetched once into the
solution's `weights/` folder and pinned to a version. Solutions 2, 4 and 6 make
their weights here and can make them again. These weights cannot be made here
at all.

It needs **arrangements for the keeper**, but far fewer than a network trained
from scratch. The keeper learns from a short table of numbers, not from
pictures. The default is 12 arrangements. That is 36 pictures across the three
stations. The scored run got 208 regions from them, so 208 rows to train 180
small trees. The examiner draws and labels them for free. The calibration needs
no extra arrangements, because it is trained in folds of the same table.

Training the keeper takes **under a second** on the processor. No graphics card
is needed. The slow part is running SAM 2 over the arrangements to get the
regions. That takes about eight seconds a picture on this machine, so the 36
pictures took 273 seconds. At run time, each picture needs one pass of the
picture encoder. That is the largest cost here, but it is still small next to
one movement of the arm.

The machine is an Apple computer with built-in graphics. The graphics share
memory with the processor. PyTorch uses the graphics through its MPS backend,
and falls back to the processor without it. There is no separate graphics card
and no CUDA. The shared memory is why a model this size fits.

It needs **the shading done right**. It is the one place where a careless
choice makes every later step worse, and nothing reports it.

The **licence is permissive**. SAM 2's weights are under Apache 2.0 and
download without an account. Solutions 3 and 4 use weights under the AGPL,
which [solution 3's chapter
explains](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#6-what-it-costs-to-run-and-the-licence).
This advantage does not carry over to SAM 3, the newer version, whose weights
are gated and come under their own terms.

The next page judges this solution against the other five.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
