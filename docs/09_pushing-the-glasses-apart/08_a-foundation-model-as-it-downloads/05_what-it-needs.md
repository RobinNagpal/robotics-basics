# What it needs

This page lists what this solution needs: the libraries, the machine, the data
and the licences.

## 1. What it needs

This solution needs less than any other in this book, and that is its point.

**Software.** It uses [LeRobot](https://github.com/huggingface/lerobot), which
is licensed Apache-2.0, and PyTorch, which is licensed BSD-3-Clause. Both
licences are permissive. This means this project does not have to publish its
own source, as a copyleft licence such as the AGPL would require. The weights
have their own terms, which are separate from the library's licence. This
project does not record those terms, so check them before shipping anything.
[Solution 6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) makes a
new file by training these weights further, and that file keeps the weights'
terms. This solution makes no new file.

**The weights.** They are downloaded and used unchanged. The first run fetches
2.9 GB: 907 MB of SmolVLA's own weights and 2.0 GB of the
`HuggingFaceTB/SmolVLM2-500M-Video-Instruct` backbone. LeRobot fetches the
backbone separately because the model asks for it. After that, both are read
from the local cache.

**Hardware.** A laptop is enough. There is nothing to train, so there is no
accelerator to rent. [How it
works](03_how-it-works.md#9-the-price-of-the-model-and-why-this-model) gives
the model's size and the time per answer. Solution 6 also trains on this
laptop. [Its own page](../09_the-same-model-fine-tuned-here/05_what-it-needs.md)
gives the memory that training used.

**Data.** None. There are no demonstrations, no labels and no training set.
Nothing has to be kept up to date when the cell changes.

**What the examiner had to add.** It had to add two things before this
solution could run. One is the top-down picture of the table. The other is a
path that accepts a run of waypoints without the push macro. [The test
examiner](../01_the-problem/02_what-goes-in-and-what-comes-out.md) provides
both. Solutions 3 and 6 use them too, so the work was done once for three
solutions.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
