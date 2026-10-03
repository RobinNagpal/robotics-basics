# Scale, data and compute

The page before this one, [self-supervised
pretraining](01_self-supervised-pretraining.md), showed where the training signal
comes from when nobody writes labels, and it ended with a frozen backbone that a
few hundred labelled examples could be built on. It did not say what making that
backbone costs. This page does, in machines, in memory, in arithmetic and in
human time, because those costs are the reason almost nobody pretrains a model
and almost everybody starts from one that somebody else pretrained.

It answers five questions in order. What is the machine that training runs on,
and why does it suit this work? What does one parameter cost to store? What does
training need on top of the parameters, and why is that several times more than
running the finished model? How is a whole run measured, and how long does it
take? And, given a budget, how should it be split between a bigger model and more
data? The last section is about the data itself, which is where robotics parts
company with everything else, because every robot example costs a person time at
a real arm.

The reader is assumed to have read the pages on [the shape of the
numbers](../02_inside-a-network/03_the-shape-of-the-numbers.md), which explains
what a matrix multiply is and what float32 and bfloat16 mean, and [the training
loop](../03_how-training-works/04_the-training-loop.md), which explains gradients
and the optimiser. Every number here is worked out in
`docs/diagrams/pretraining_and_adapting_1.py`. The model, the accelerator, the
mixture of data and the scaling formula are example configurations written for
this page and stated in full, and none of them is a measurement of a real
product.

## Contents

1. [What a graphics processing unit does](#1-what-a-graphics-processing-unit-does)
2. [What one parameter costs to store](#2-what-one-parameter-costs-to-store)
3. [What training needs on top of the parameters](#3-what-training-needs-on-top-of-the-parameters)
4. [Measuring a run in floating-point operations](#4-measuring-a-run-in-floating-point-operations)
5. [Scaling laws, and what they let you plan](#5-scaling-laws-and-what-they-let-you-plan)
6. [The data, and why the robot kind is scarce](#6-the-data-and-why-the-robot-kind-is-scarce)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. What a graphics processing unit does

The first of the five questions above is about the machine, and the answer is
that training runs on a **graphics processing unit (GPU)**, which is a chip built
first for drawing games and then kept because it turned out to suit neural
networks. An ordinary central processing unit has a few very clever cores that
each do one thing at a time quickly. A GPU instead has thousands of simple
arithmetic units that all do the same kind of sum at the same time on different
numbers, and that is only useful if your work can be cut into thousands of
identical pieces that do not need to talk to each other.

A matrix multiply can be cut that way exactly, which is why this hardware fits.
Every cell of the answer is worked out by running along one row of the first grid
and one column of the second, multiplying the pairs and adding them up, and no
cell needs any other cell's result.

![Three grids of small whole numbers, with one row, one column and the resulting cell highlighted](../../images/pretraining-and-adapting/scale-data-and-compute/one-matrix-multiply.svg)

The cell in row 2 and column 3 is (1 x 3) + (0 x 1) + (1 x 0) = 3, and the whole 4 by 5 answer is 4 x 5 x 3 = 60 multiply-and-add pairs.

Scale that up and the two counts pull apart in a way that favours the hardware.
Multiplying two grids of 1,024 by 1,024 takes 2.147 thousand million operations
spread over 1.049 million cells that can all be worked out at once, so each piece
of work is 2,048 operations long, and at 16,384 it is 8.796 million million
operations across 268.4 million independent cells.

![Two lines on a log scale: operations rising as the cube of n, and independent cells rising as the square](../../images/pretraining-and-adapting/scale-data-and-compute/work-and-independence.svg)

The work grows as the cube of the side while the number of pieces it can be cut into grows as the square, so bigger multiplies both need more arithmetic units and can use them.

There is a second reason, about memory rather than arithmetic. Fetching a number
from the chip's memory is slow compared with multiplying it, so what matters is
how much arithmetic each fetched byte pays for. A matrix multiply of side 1,024
does 341 operations per byte fetched and at 16,384 it does 5,461, while adding
two grids does 0.17 at every size, because it touches each number once and is
then finished with it.

![Two lines: operations per byte fetched, rising steeply for a matrix multiply and flat at 0.17 for adding two grids](../../images/pretraining-and-adapting/scale-data-and-compute/arithmetic-per-byte.svg)

A big matrix multiply pays for each fetched byte many times over, while adding two grids touches each number once and spends its life waiting for memory.

This has a direct consequence for how a model is run. Take one layer of 4,096 by
4,096 weights, which is 33.6 megabytes at two bytes a weight. Putting a single
row of input through it takes 0.1 microseconds of arithmetic and 16.8
microseconds of fetching those weights, so the chip is idle 99 per cent of the
time. The arithmetic only catches up at a batch of 256, and at 1,024 the
arithmetic takes 85.9 microseconds against 25.2 for the fetching.

![Two lines crossing: arithmetic time rising with batch size, and weight-fetching time almost flat](../../images/pretraining-and-adapting/scale-data-and-compute/batch-fills-the-chip.svg)

With one row at a time the weights are fetched for almost nothing, and only at a batch of 256 does this layer spend more time on arithmetic than on memory.

That is why training uses large batches and why serving a model to one user at a
time is wasteful. The next section looks at what those weights cost to hold in
the first place.

---

## 2. What one parameter costs to store

The last section counted operations, and this one counts bytes, starting with the
fact that a parameter is just a number and its cost is the size of the number
format it is kept in. The example model used from here on is a transformer of 32
blocks with a width of 4,096 and a vocabulary of 128,000, and its parameter count
follows from that shape alone: 2.15 thousand million in the attention parts, 4.29
thousand million in the feed-forward parts and 0.52 thousand million in the
embedding table, which is 6.97 thousand million in all.

![A stacked bar chart of parameters by part for three example model shapes](../../images/pretraining-and-adapting/scale-data-and-compute/where-the-parameters-are.svg)

A small model of 12 blocks and width 768 has 0.18 thousand million parameters and one of 24 blocks and width 2,048 has 1.47, and the feed-forward part always holds twice what attention does.

Multiplying that count by the bytes of the format gives the memory. At float32,
which is four bytes, the example model needs 27.9 gigabytes before anything else
is counted; at bfloat16, two bytes, it needs 13.9; at int8, one byte, 7.0; and at
int4, half a byte, 3.5.

![A bar chart of 27.9, 13.9, 7.0 and 3.5 gigabytes for four number formats](../../images/pretraining-and-adapting/scale-data-and-compute/bytes-per-parameter.svg)

The same 6.97 thousand million parameters cost 27.9 gigabytes or 3.5, depending only on how many bits each one is kept in.

Fewer bits are not free, because a format with fewer bits rounds harder. The
script stores five numbers in four formats and measures how far each stored value
is from the true one as a share of it. float32 is out by about one part in a
hundred million, float16 by two or three parts in ten thousand, and bfloat16 by
about four parts in a thousand, because bfloat16 spends its bits on the range of
the number rather than its precision. Those three keep the same relative accuracy
whatever the size of the number, which is what makes them safe for training.

![A log-scale bar chart of the rounding error of five numbers in four formats](../../images/pretraining-and-adapting/scale-data-and-compute/rounding-at-each-precision.svg)

Storing 0.1 gives 0.1000000015 in float32 and 0.0996093750 in bfloat16, while one shared int8 scale of 0.074803 turns it into 0.0748031496, a quarter out.

That last column is the warning about whole numbers. int8 does not store a
number, it stores how many steps of a fixed size the number is, and here the step
had to be set by the largest value in the set, so the smallest value lost a
quarter of itself. Keeping a separate step for each part of the model is what
makes int8 usable, and the page on [making a model smaller and
faster](04_making-a-model-smaller-and-faster.md) is about doing that properly.

![Four lines on a log-log chart of memory against parameter count, with lines marking example cards of 16, 24 and 80 gigabytes](../../images/pretraining-and-adapting/scale-data-and-compute/model-size-versus-card.svg)

A model of 7 thousand million parameters needs 28 gigabytes at float32 and 14 at bfloat16, so the format decides whether it fits on one card.

So far this is only the memory to hold a finished model and answer with it.
Training needs considerably more, which is the next section.

---

## 3. What training needs on top of the parameters

The memory counted in section 2 is only what a finished model needs to answer a
question, and holding the parameters turns out to be the small part of training,
because gradient descent has to keep several more numbers for every one of
them. The gradient of each
parameter has to be stored while the backward pass runs. The optimiser, which is
AdamW in almost every modern run, keeps two running averages for each parameter
and keeps them at float32 along with a float32 master copy of the parameter
itself, because adding a tiny step to a bfloat16 number loses the step entirely.
And every activation worked out on the way forward has to be kept until the
backward pass has used it.

![A stacked bar of five parts of training memory against a single bar for running, and a bar chart of their shares](../../images/pretraining-and-adapting/scale-data-and-compute/training-memory-budget.svg)

Training the example model on four sequences of 4,096 words needs 14 gigabytes for the parameters, 14 for the gradients, 28 for the master copy, 56 for the optimiser averages and 69 for the activations: 180 in all, against 16 for running it.

Those five numbers are worth reading twice. The parameters are 8 per cent of the
total, the optimiser's own state is 46 per cent, and training needs 11.2 times as
much memory as answering with the finished model, which is why a model you can
run on one card may need a rack of them to train.

The last line of the budget behaves differently from the others, because the
activations grow with the batch size while everything else stays fixed at 111
gigabytes. At one sequence the activations are 17.2 gigabytes and at 32 they are
549.8, which is what sets the largest batch that fits.

![Two lines of total memory against batch size, one keeping every activation and one recomputing them](../../images/pretraining-and-adapting/scale-data-and-compute/activations-grow-with-batch.svg)

The fixed cost of parameters, gradients and optimiser state is 111 gigabytes whatever the batch, and only the activations grow with it.

There is a standard way of buying memory back, and it is to throw most of the
activations away and work them out again during the backward pass. Keeping one
activation per block instead of all of them cuts the example budget from 180
gigabytes to 116, a saving of 36 per cent, and the price is an extra forward pass,
which raises the arithmetic of a step by about a third.

![Two bar charts: memory falling from 180 to 116 gigabytes, and arithmetic rising by a third](../../images/pretraining-and-adapting/scale-data-and-compute/recompute-tradeoff.svg)

Recomputing the activations trades 33 per cent more arithmetic for 36 per cent less memory, and it is switched on in almost every large run.

Counting sixteen bytes a parameter, which is the fixed part of the budget above,
turns model size straight into a count of machines. A model of 7 thousand million
parameters fits on one example card of 80 gigabytes to run and needs two to train,
one of 70 thousand million needs 2 and 14, and one of 180 thousand million needs 5
and 36.

![A grouped bar chart on a log scale of cards needed to run and to train, for seven model sizes](../../images/pretraining-and-adapting/scale-data-and-compute/how-many-cards.svg)

Running needs two bytes a parameter and training needs sixteen before activations, so training a large model is a room full of cards rather than one.

Memory decides whether a run is possible at all. How long it then takes is the
next section.

---

## 4. Measuring a run in floating-point operations

Section 3 decided whether a run fits in memory at all, and this one decides how
long it takes. A **floating-point operation (FLOP)** is one multiply or one add
on numbers with a decimal point, and the size of a training run is measured by
counting them,
because that count does not depend on which machine you use. The rule of thumb is
simple enough to do in your head: pushing one token through one parameter costs
about two operations in the forward pass, because each parameter is multiplied by
something and the result is added on, and the backward pass costs about twice the
forward pass, because it works out a gradient for the activations and a gradient
for the weights. So a run over **D** tokens with **N** parameters costs about 6 x
N x D operations in all.

![A stacked bar of forward and backward operations for the example run](../../images/pretraining-and-adapting/scale-data-and-compute/six-n-d.svg)

With 6.97 thousand million parameters and 1.4 million million tokens the forward passes cost 1.95e+22 operations and the backward passes 3.90e+22, so 5.85e+22 in all.

That number means nothing until it is divided by a machine. The example
accelerator used here does 400 million million operations a second at full
stretch, and a real run keeps about 40 per cent of that busy, so it sustains 160
million million a second. One of them would take 12 years to finish the example
run, which is why these runs are split across many.

![A grouped bar chart on a log scale of training days for three example runs on 8, 64 and 512 accelerators](../../images/pretraining-and-adapting/scale-data-and-compute/flops-and-days.svg)

The example run takes 532 days on 8 accelerators, 66 on 64 and 8.3 on 512, while 70 thousand million parameters over 10 million million tokens takes 593 days even on 512.

Because the cost is a product of two numbers, many different pairs of model size
and token count cost the same. Drawing lines of equal cost makes the choice
visible, and choosing a point on one of those lines is the subject of section 5.

![A heat map of 6ND over model size and token count, with lines of equal cost drawn across it](../../images/pretraining-and-adapting/scale-data-and-compute/iso-compute-grid.svg)

Every line is one budget of arithmetic held fixed, and the example run sits at 7 thousand million parameters and 1.4 million million tokens.

The same rule prices answering as well as training. Producing one token with the
finished model costs about 2 x N operations, which is 1.39e+10 here, so the
training run costs as much as producing 4.2 million million tokens of answers,
which is three times the number of tokens it was trained on. Training a model is
a single large bill and serving it is a small bill that never stops.

![A rising line of cumulative serving cost crossing a flat line for the training run](../../images/pretraining-and-adapting/scale-data-and-compute/training-versus-serving.svg)

Answering costs as much as the training run once 4.2 million million tokens have been produced, and everything after that is more than training ever cost.

---

## 5. Scaling laws, and what they let you plan

Section 4 left a question open: given a fixed **compute budget**, which is the
total number of operations you are willing to spend on one run, should it buy a
bigger model trained on less data, or a smaller model trained on more? The answer
comes from **scaling laws**, which are the measured relations between model size,
data size, arithmetic and the loss the run ends at.

What people found, by doing many runs of different sizes, is that the loss falls
smoothly and predictably as all three grow, and that the shape of the fall is a
straight line when both axes are squashed logarithmically. The curves here come
from a formula written for this page, which has that shape without being anybody's
measurement, and the formula is a floor of 1.60 plus 500 divided by the number of
parameters to the power 0.35 plus 500 divided by the number of tokens to the power
0.30.

![Two charts: loss falling against arithmetic, and the same curve as a straight line with the floor taken off](../../images/pretraining-and-adapting/scale-data-and-compute/power-law-curve.svg)

In this illustrative formula 7e+18 operations reach a loss of 2.802, 4.9e+20 reach 2.205 and 2.4e+24 reach 1.753, and the fall is a straight line once the floor is taken off.

Two things in that picture matter more than the exact numbers. The curve bends,
so each further improvement costs more than the last, and the curve has a floor,
so no amount of arithmetic takes the loss to zero. Both are true of the measured
ones as well.

The second thing the laws say is that growing one of the three alone does not
work, and that is the practical lesson. With the data held at 10 thousand million
tokens, the loss in this formula cannot go below 2.100 however large the model
gets; it is 2.454 at a thousand million parameters and still 2.171 at a hundred
thousand million, so a hundred times the model has bought almost nothing.

![Four curves of loss against model size, one for each token budget, each flattening onto its own floor](../../images/pretraining-and-adapting/scale-data-and-compute/bigger-model-alone.svg)

Each amount of data has its own floor, 2.100 for 10 thousand million tokens and 1.726 for a thousand thousand million, and growing the model alone walks onto that floor and stops.

So the budget has to be split, and the split that the formula recommends grows
both together. Multiplying the budget by ten multiplies the best model size by
2.89 and the best token count by 3.46, which keeps the number of training tokens
for each parameter nearly steady: it drifts from about 13 at the smallest budget
here to about 54 at the largest, while the budget itself has gone up by a factor
of a hundred million.

![Two charts: the best model size and token count both rising with the budget, and their ratio drifting slowly](../../images/pretraining-and-adapting/scale-data-and-compute/grow-together.svg)

Spending a budget well means growing the model and the data together, because the best number of tokens for each parameter moves slowly while the budget moves by factors of ten.

The reason anyone cares is planning. A large run is expensive enough that you
want to know roughly where it will land before you start it, and because the
relation is smooth you can do several small runs, fit the line and read off the
answer. Doing that with this formula, fitting only runs between 1e+18 and 1e+21
operations, predicts a loss of 1.7856 at 1e+24, where the formula itself gives
1.7768, an error of half a per cent.

![Seven small runs with a fitted line extrapolated to a point a thousand times further out](../../images/pretraining-and-adapting/scale-data-and-compute/predict-the-big-run.svg)

The line fitted to the small runs predicts 1.786 for a run a thousand times larger than any of them, and the formula says 1.777.

The honest caveat is that these laws predict the loss, which is how well the model
guesses the next token, and not whether it can do the job you want. A better loss
usually means a better model, and "usually" is doing real work in that sentence.

---

## 6. The data, and why the robot kind is scarce

Section 5 treated the data as a number of tokens, as if all tokens were alike.
They are not, and the first thing that matters is how many of them are wrong. The
script trains the same head on the same features with no wrong labels, with one
label in five wrong and with two in five wrong. With 200 clean examples it reaches
95.9 per cent, which is what 3,200 examples reach when two labels in five are
wrong.

![Three accuracy curves against training-set size, for clean labels, 20 per cent wrong and 40 per cent wrong](../../images/pretraining-and-adapting/scale-data-and-compute/quality-beats-volume.svg)

Two hundred clean examples are worth 3,200 dirty ones, and at 400 the clean set reaches 96.4 per cent against 72.1.

The second thing that matters is how many of them are the same. Text scraped from
the web is full of duplicates, and a duplicate costs exactly as much to train on
as a fresh example while teaching nothing, so **deduplication**, which means
finding and removing near-identical examples, is one of the first things done to
a collected pile. The script holds the training set at 1,600 examples and raises
the share of them that are copies: accuracy falls from 97.9 per cent with no
copies to 94.9 at nine tenths copies and 39.8 at 98 per cent copies, where only 32
different examples are left.

![Two charts: the number of different examples falling while the set stays at 1,600, and accuracy falling with it](../../images/pretraining-and-adapting/scale-data-and-compute/duplicates-waste-the-budget.svg)

The set is always 1,600 examples, but as more of them become copies the accuracy follows the number of different ones down, from 97.9 per cent to 39.8.

The third thing is which sources the tokens come from and in what proportion,
which is called the **data mixture**. The mixture is chosen rather than taken,
because the amount of text available from each source has nothing to do with how
much of it the model should read. The table below is an example mixture for a run
of 1.4 million million tokens, and the number to look at in it is the last one,
which is how many times each token of a source is read.

![Two bar charts: tokens available against tokens read for five sources, and how many times each source is read](../../images/pretraining-and-adapting/scale-data-and-compute/a-data-mixture.svg)

Of 9 million million tokens of web pages the run reads 0.7 million million, so 0.08 of them, while the 0.02 million million tokens of robot logs make up 8 per cent of the run, which means reading each one 5.6 times.

That last row is the whole problem of robotics in one number. The source you care
about most is the smallest one, so it has to be read over and over, and reading
the same example many times is how a model memorises instead of learning. Robot
data is scarce for a reason that no amount of money removes quickly, which is that
every example is somebody sitting at a real arm. At 25 seconds to perform a task
and 12 seconds to put the scene back, one person-hour yields 97 demonstrations.

![Two bar charts: 97 demonstrations in one person-hour, and the person-hours needed for 10,000, 100,000 and a million](../../images/pretraining-and-adapting/scale-data-and-compute/robot-data-costs-time.svg)

Ten thousand demonstrations cost 103 person-hours, a hundred thousand cost 1,028, and a million cost 10,278, which is 5.8 person-years of eight-hour days.

Four things are actually done about this, and each one buys examples more cheaply
in exchange for examples that are less like the robot you will run on. Sharing
data across robots, which is called **cross-embodiment** data, means training on
episodes recorded on other people's arms, which costs the time to convert them
and leaves you with data recorded on a body unlike yours. Simulation with
randomised appearance and physics costs the time to build and randomise the
scene, after which it produces episodes by the hundred thousand, and it leaves a
gap between the simulator's physics and the real world. **Synthetic data**,
meaning examples generated by another model, costs the time to set it up and
check what it produced, and it carries over the mistakes of the model that made
it. Learning from video of people doing the task costs least per example, because
the video already exists, and it loses most, because a human hand is not a
gripper and a video has no record of the forces.

![Two bar charts: examples per person-hour for five ways of getting data, and the person-hours each needs for 100,000 examples](../../images/pretraining-and-adapting/scale-data-and-compute/four-ways-to-get-more-data.svg)

Under the example costings written for this page, teleoperation gives 97 examples a person-hour and needs 1,028 hours for a hundred thousand, while simulation gives 5,000 an hour and needs 20, and every cheaper route gives data that is further from the real arm.

None of this is a solved problem, and the page on [where the data comes
from](../../07_learned-models/01_what-models-are/05_where-the-data-comes-from.md)
describes how real robot datasets are actually collected. The practical position
today is that a robot model is pretrained on web text and pictures, where data is
plentiful, and then adapted with the small amount of robot data that exists, which
is what the next page is about.

---

## 7. Where to read next

- [Fine-tuning and adapters](03_fine-tuning-and-adapters.md) is the next page, and
  it shows how a pretrained model is bent to one job without paying any of the
  costs on this page twice.
- [Making a model smaller and faster](04_making-a-model-smaller-and-faster.md)
  picks up section 2's int8 column and turns it into a model that fits on a
  robot's own computer.
- [Running and evaluating a model](../13_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  takes section 1's point about batches and memory and turns it into a latency
  budget for a real arm.
- [Vision-language-action models](../12_models-that-act/03_vision-language-action-models.md)
  shows what is built from web pretraining plus the scarce robot data of section 6.
- [Where the data comes from](../../07_learned-models/01_what-models-are/05_where-the-data-comes-from.md)
  is the catalogue page on real robot datasets, their sizes and how they were
  collected.
- [Hardware](../../03_frameworks/08_frontier/05_hardware.md) describes the arms and
  the computers that this arithmetic ends up running on.

---

## 8. Using it in Python

Most of this page is arithmetic you can do without a library, and the first half
of the program below does exactly that. The second half measures the thing that is
easiest to get wrong, which is how much the optimiser adds to the memory, by
building one real transformer block, taking one step and asking the optimiser what
it is holding.

```python
import torch
from torch import nn

# section 2: the parameter count of the example model, from its shape alone
def parameters(layers, width, vocab):
    return 12 * width * width * layers + vocab * width

n = parameters(layers=32, width=4096, vocab=128_000)
print(round(n / 1e9, 2))                       # 6.97 thousand million
for name, each in [("float32", 4), ("bfloat16", 2), ("int8", 1)]:
    print(name, round(n * each / 1e9, 1))      # float32 27.9 / bfloat16 13.9 / int8 7.0

# section 4: the arithmetic of a whole training run, 6 x N x D
tokens = 1.4e12
print(f"{6 * n * tokens:.2e}")                 # 5.85e+22

# section 3: what the optimiser adds, measured on one real block
block = nn.TransformerEncoderLayer(d_model=512, nhead=8, dim_feedforward=2048,
                                   batch_first=True)
small = sum(p.numel() for p in block.parameters())
print(small)                                   # 3152384

opt = torch.optim.AdamW(block.parameters(), lr=1e-4)
block(torch.randn(2, 16, 512)).sum().backward()
opt.step()
state = sum(v.numel() for s in opt.state.values()
            for v in s.values() if torch.is_tensor(v))
print(state, round(state / small, 1))          # 6304780 2.0
```

The first three prints are section 2 and section 4 with no library involved at
all, because a parameter count follows from the shape of the model and the cost of
a run follows from the parameter count. The formula 12 x width x width x layers is
the attention and feed-forward parts of a standard block added together, and the
vocabulary times the width is the embedding table.

The last two prints are the measurement. One real block of width 512 holds
3,152,384 parameters, and after a single AdamW step the optimiser is holding
6,304,780 numbers of its own, which is 2.0 times the model. Those are the two
running averages of section 3, and at float32 they are eight bytes for every
parameter, which is where 46 per cent of the training budget went.

What PyTorch will not tell you is any of the planning. It does not warn you that
your batch is too small to keep the chip busy, that your model is too large for
the data you have, or that half your training set is duplicates. Those are
decisions, and sections 3 to 6 are how they are made: count the bytes before you
start, count the operations, pick a point on the iso-compute line, and look at
the data before you buy more of it.
