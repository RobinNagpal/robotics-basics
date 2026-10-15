# What it needs

This page lists what solution 7 costs. Every number here was measured while
the project built it. The score is not known yet, so this page says nothing
about it.

## Contents

1. [What it needs](#1-what-it-needs)
2. [The measured costs](#2-the-measured-costs)

## 1. What it needs

[What it is](01_what-it-is.md) said what the model is. This section lists the
parts that must exist before it runs.

- **Solution 6's demonstrations.** Solution 7 trains on that folder. So it
  must be made first.
- **The Evo-1 weights.** They download once, the first time training runs.
- **About an hour of training for each seed.** A seed is the number that
  starts the random parts of one training run. There are three seeds.

It does not need an NVIDIA graphics card. Evo-1's code names NVIDIA's CUDA
system in three places. None of them stops it running on this Mac. Three
settings were enough, and no code was changed.

The table lists each setting and the reason for it.

| setting | why |
|---|---|
| flash attention off | an NVIDIA-only part; the model uses ordinary attention instead |
| mixed precision off | the model already turns it off without CUDA |
| 32-bit numbers, not bfloat16 | a result should not rest on Metal's bfloat16 |

The project does not state the licence of the Evo-1 weights. Read their terms
before anything trained from them leaves the project.

The next section gives the measured costs.

## 2. The measured costs

The parts are listed. This section says how much memory and time the model
takes.

The table has one row for each measurement. The numbers come from the
project's
[README for this solution](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/README.md).

| | |
|---|---|
| numbers in the model | 775.2 million |
| numbers fitted | 122.0 million |
| memory held while answering | 3.60 GiB |
| one forward pass | 1.7 s |
| one backward pass | 0.1 s |

A forward pass runs a picture through the model. A backward pass works out how
to change the fitted numbers. Solution 6 fits only 3.8 million numbers, so
solution 7 changes about 30 times as many.

The next page, [the results](03_results.md), says what is still being measured.

← [What it is](01_what-it-is.md) · [Results](03_results.md) →
