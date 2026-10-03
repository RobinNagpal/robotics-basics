# The order of the work

The page before this one, [before you train
anything](01_before-you-train-anything.md), ends with two things written down:
the job, set out as an input, an output and one number that says whether it
worked, and a baseline, which is the simplest rule you could follow instead of a
model and which the model has to beat before anybody may call it evidence. This
page is what you do on the day after that, and it is about the order of the work
rather than about any one method.

The order matters because a model can fail for a dozen reasons that cost wildly
different amounts to find, some showing in a single forward pass with no training
at all and some only in a run that takes a week. So the work is a ladder of four
milestones climbed from the cheapest upwards, and each rung rules out a group of
causes so that a failure on the next rung has a short list of suspects. The rungs
are to put one batch through the untrained model and read the loss, to make the
model memorise ten examples on purpose, to do one small honest run with a
held-back set, and only then to make things bigger, one change at a time.

The page assumes the loop from [the training
loop](../03_how-training-works/04_the-training-loop.md), the loss from [the score
of being
wrong](../03_how-training-works/01_the-score-of-being-wrong.md#4-cross-entropy-the-price-of-a-wrong-probability)
and the held-back set from [overfitting and
generalisation](../04_making-training-work/01_overfitting-and-generalisation.md).
What it adds is what to look at, what the number should be before you look at it,
and what each result rules out.

Every number here was measured. The data is simulated: one example is sixteen
readings standing in for features pulled out of a camera frame, its label is one
of ten classes, and enough noise is added that the classes overlap. A pool of
2,200 examples was drawn once and 600 set aside as the held-back set before any
training. Everything done to it is real PyTorch, and
`docs/diagrams/starting_your_own_model_2.py` prints every figure quoted below.

## Contents

1. [The ladder, and why the cheapest rung comes first](#1-the-ladder-and-why-the-cheapest-rung-comes-first)
2. [Rung one: one batch through an untrained model](#2-rung-one-one-batch-through-an-untrained-model)
3. [Rung two: memorise ten examples on purpose](#3-rung-two-memorise-ten-examples-on-purpose)
4. [Rung three: one small honest run](#4-rung-three-one-small-honest-run)
5. [Rung four: scale, one change at a time](#5-rung-four-scale-one-change-at-a-time)
6. [The run folder, and the run you keep](#6-the-run-folder-and-the-run-you-keep)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. The ladder, and why the cheapest rung comes first

The job and the baseline say nothing about what to do first, so this section sets
the four rungs out and measures what each costs in examples put through the model,
which is the thing that takes the time.

![Four stacked boxes for the four rungs, each with what it proves and the number of example-views it costs, with arrows pointing upwards and the running total beside each one](../../images/starting-your-own-model/the-order-of-the-work/the-ladder.svg)

The four rungs cost 64, 4,000, 24,000 and 216,000 examples put through the model, so 244,064 have been spent by the end.

Read it from the bottom. One batch of 64 examples through an untrained model costs
64 example-views and proves that the data arrives, the shapes line up and the loss
starts where it should. Four hundred steps on the same ten examples costs 4,000
and proves the loop, the gradients and the labels work together. A run of 960
examples for 25 passes costs 24,000 and is the first that can say whether the job
is learnable. Nine runs of that size cost 216,000, nearly nine tenths of the
bill.

![A bar chart on a log scale of the example-views spent before a fault shows, rising from 64 at rung one to 244,064 at rung four](../../images/starting-your-own-model/the-order-of-the-work/cost-of-finding-late.svg)

The same fault found on the fourth rung has cost 244,064 example-views instead of 64, which is 3,814 times as much work for the same answer.

Those numbers count the arithmetic rather than minutes, which depend on hardware
this page knows nothing about, and the ratio is the point: catching a disconnected
input on the second rung rather than the fourth saves sixty runs of waiting.

![On the left, thirteen named faults with a marker at the rung that first catches each one, and on the right a step chart of the number of causes still open falling from thirteen to zero](../../images/starting-your-own-model/the-order-of-the-work/causes-ruled-out.svg)

Of thirteen common faults, five die on the first rung, four more on the second and three more on the third, so the number still open falls from 13 to 8 to 4 to 1.

The left panel is the useful half. A label outside the list of classes and a last
layer with the wrong number of outputs both show on the very first batch, while
the input not reaching the output, the labels not being lined up and the optimiser
never having been given the weights all survive the first rung and die on the
second. So if you are on the fourth rung wondering why the loss will not fall, the
answer is almost never something the first two rungs would have caught.

---

## 2. Rung one: one batch through an untrained model

The first rung costs one forward pass, and most people skip it, which is why it is
the most useful check on this page. You put one batch through the model before any
training and look at the shape of what comes out and at the loss, and the loss is
no mystery because you can work out in advance what it has to be.

![A chart of cross-entropy loss against number of classes on a log x axis, with the curve of the natural logarithm drawn through measured points at 2, 10, 80 and 1000 classes, each with the range over twenty untrained models](../../images/starting-your-own-model/the-order-of-the-work/first-loss-by-classes.svg)

Twenty untrained models give 0.511 to 1.162 on 2 classes against an expected 0.693, 2.247 to 2.651 on 10 against 2.303, 4.397 to 4.726 on 80 against 4.382, and 6.966 to 7.263 on 1000 against 6.908.

A model that knows nothing spreads its belief evenly, so it gives each class a
probability of one divided by the number of classes, and the cross-entropy of
that is the natural logarithm of the number of classes: 2.303 for ten, 6.908 for
a thousand, 0.693 for a two-way choice. The measured values sit near those lines
rather than on them, because random starting weights give a model mild opinions it
did not earn, so a first loss within a few tenths is healthy and a first loss of
11 on a ten-class job is a bug.

![Six boxes in a row showing the shape and the number of values after each layer of a small convolutional network, from the batch going in to the ten class scores coming out](../../images/starting-your-own-model/the-order-of-the-work/shape-chain.svg)

One real forward pass goes from (8, 3, 64, 64), which is 98,304 numbers, through (8, 16, 32, 32) and (8, 32, 16, 16) down to (8, 32) and finally (8, 10), in a model holding 5,418 weights.

Two of those shapes matter, and they are marked in green. The first number is the
batch, 8 here, and it must still be 8 at the end, because a layer that loses it
has mixed your examples together. The last is the classes, 10 here, and it must
match the number of labels in your data, because a model with eleven outputs and
ten labels trains happily and is wrong in a way no loss curve shows.

![A horizontal bar chart on a log scale of five first losses from the same untrained model, with a dashed line at ln(10)](../../images/starting-your-own-model/the-order-of-the-work/planted-first-losses.svg)

A correct untrained model gives 2.271, a last layer started twelve times too large gives 7.730, a stale bias favouring one class gives 7.839, and the wrong loss gives 0.415.

The two values near 7.8 are the easy catch, because weights that start too large
make the model certain of nonsense, and cross-entropy charges most for certainty
about a wrong answer. The 0.415 sits below the expected loss instead, because
squared error on ten outputs is a different quantity with no reason to be near
2.303. The last bar is the honest warning: a softmax applied by hand before a loss
that applies its own gives 2.291, nearer 2.303 than the correct model is, so the
next rung has to catch that one.

![Two bar charts of mean squared error on the first batch, one with the target in millimetres and one with the same target standardised, each showing the untrained model, always guessing the average, and the variance of the target](../../images/starting-your-own-model/the-order-of-the-work/first-loss-regression.svg)

With the target left in millimetres the untrained model scores 289,732 against a variance of 105,933, while the same target standardised gives 1.114 against 0.998.

For a job that predicts a number, compare against the variance of the target,
which is what you score by always guessing the average. The left panel shows what
happens when the target keeps its own units: the untrained model starts near zero
while the targets average 428.7 millimetres, so most of the first loss is that gap
squared, 183,809 on its own. That is not a bug, but it hides any real bug behind
it, which is why targets are centred and scaled before training.

---

## 3. Rung two: memorise ten examples on purpose

The first rung proved the data goes in with the right shape and said nothing about
whether training does anything, so the second rung is the smallest experiment that
does. You train on ten examples over and over and demand that the loss go to
nearly zero. This is the most useful hour in the whole process, because a model
that cannot memorise ten examples will not learn ten thousand, and finding that
out costs 4,000 example-views instead of a week. Choose one example of each class,
as the runs below do, because ten drawn at random prove much less.

![A chart on a log scale of the loss over 400 steps for three runs on the same ten examples, one falling to about a millionth and two sitting on a dashed line at ln(10)](../../images/starting-your-own-model/the-order-of-the-work/overfit-ten.svg)

The healthy run starts at 2.553, is below 0.0001 by step 6 and ends at 6.676e-07, while the run with the input zeroed and the run with the labels re-paired every step both sit exactly on 2.303.

The green line is what passing looks like, and it is not subtle. Both flat lines
land on 2.303, the natural logarithm of ten, which is precisely where an untrained
model starts, and that is no coincidence: a model that cannot see the input, or
whose labels are shuffled against the inputs every step, can do no better than
give every class the same probability. So a plateau at exactly the first loss says
that nothing in the input is reaching the answer.

![A chart of the share of ten examples got right over 400 steps for four runs, with two reaching 100 per cent and two staying at 10 per cent](../../images/starting-your-own-model/the-order-of-the-work/overfit-accuracy.svg)

The correct run and the run whose labels were shuffled once and left alone both go from 0 or 10 per cent right to 100 per cent after one step, while the two broken runs stay at 10 per cent.

Shuffling the labels once does not stop the model memorising them, because
memorising is all this test asks for and a wrong answer is as memorisable as a
right one. That is why this rung proves the machinery and not the meaning: it says
gradients flow, the optimiser is connected to the weights and the model can
separate these examples, and it says nothing about whether your labels are right.
Wrong labels show up on the third rung instead.

![Three heatmaps of the ten-by-ten table of probabilities each run ends up giving the ten examples, one a clean diagonal, one every cell at 0.10, and one a partial diagonal](../../images/starting-your-own-model/the-order-of-the-work/plateau-fingerprints.svg)

The healthy run gives 1.0000 to the right class every time, the run with the input cut off gives 0.1000 to every class with its rows differing by 0.0000, and a one-unit model gets 60 per cent right at 0.9627.

The middle panel is the fingerprint worth memorising, because every row equals
every other row to four decimal places, so the model is giving the same answer
whatever it is shown, and nothing but a broken connection does that. The right
panel is a different failure, since a hidden layer of one unit can separate
examples along a single direction only, so it gets some right and smears the rest.
That is a model too small for the job rather than a bug, and the picture tells
them apart where the number alone would not.

![A horizontal bar chart on a log scale of the final loss of seven single-batch runs, with the one that memorised all ten in green and six that did not in red](../../images/starting-your-own-model/the-order-of-the-work/bug-catalogue.svg)

The correct run ends at 6.676e-07, a learning rate of zero stays at its first loss of 2.553, one 2000 times too large ends at 4.198, a one-unit layer at 0.9627, only the final bias moving at 2.432, and the two disconnected runs at 2.303.

Three of those have signatures you can read without any other evidence. A learning
rate of zero leaves the loss at exactly the first batch's value, which is a flat
line rather than a plateau. A learning rate far too large ends above the logarithm
of the number of classes, which is worse than knowing nothing and only happens
when the steps throw the weights about. A plateau at exactly the logarithm means
one answer for everything. An hour here buys four suspects instead of thirteen.

---

## 4. Rung three: one small honest run

The second rung proved the machinery works on ten examples, and memorising ten
examples is not learning, so the third rung is the first run that uses the split
decided on the page before. It trains on 960 examples in batches of 32 for 25
passes, which is 750 steps, and measures the loss after each pass on the 600
examples it never trains on.

![Two panels, one with the training and held-back loss over 25 passes and the gap between them shaded, and one with the error rates of the same run against two baseline lines](../../images/starting-your-own-model/the-order-of-the-work/first-honest-curve.svg)

The training loss falls from 1.435 to 0.322 and the held-back loss from 1.494 to a lowest 0.652 at pass 10 and then 0.697, with 23.8 per cent of held-back answers wrong against 44.2 per cent for nearest neighbour and 90.8 per cent for the commonest class.

The left panel on its own only says the loss went down. The right panel answers
the question the page before set, because the dashed lines are the baselines and
the model is worth something only below them. It is, since 23.8 per cent wrong
against nearest neighbour's 44.2 per cent is what the simple rule cannot do. Had the red line settled at 46 per cent the run would have failed with a
healthy-looking loss curve, which is why the baseline is drawn on the chart.

![Three pairs of curves, dashed for training and solid for held back, for runs on 60, 240 and 960 examples, with the end gap written beside each pair](../../images/starting-your-own-model/the-order-of-the-work/three-dataset-sizes.svg)

With 60 training examples the gap at the end is 1.00 and 48.0 per cent of held-back answers are wrong, with 240 it is 0.55 and 28.3 per cent, and with 960 it is 0.37 and 23.8 per cent.

The training loss is low in all three, because a model with enough weights fits
whatever is in front of it, so the held-back loss separates them. A wide gap that
more examples keep closing is the clearest sign that the next thing to buy is data
rather than a bigger model, and quadrupling the examples twice took it from 1.00
to 0.55 to 0.37. The 60-example run was also still
falling at pass 25 while the 960 run flattened by pass 10, so a number of passes
that suits one size does not suit another.

![Two panels, one with the training loss and two held-back curves for a clean and a leaky split, and one with a bar for each final held-back loss](../../images/starting-your-own-model/the-order-of-the-work/leaky-split.svg)

The clean split ends at a held-back loss of 0.842 with 28.3 per cent wrong, while a split in which half the held-back rows are copies of training rows ends at 0.621 with 19.1 per cent wrong.

A **leak** is an example that is in the held-back set and the training set at
once, and the one planted here is blatant, so its lie is 0.220 of loss and 9.3
points of error in your favour. Real leaks are quieter and lie the same way: two
camera frames a tenth of a second apart, one object photographed twice, one
demonstration counted as several examples. That is why
[overfitting and
generalisation](../04_making-training-work/01_overfitting-and-generalisation.md#3-leakage-when-the-split-tells-you-a-lie)
insists the split be made along whatever line groups those near-duplicates, made
once, written down, and never made again by another piece of code.

![Four small panels of training and held-back loss curves, labelled still falling, flat from the first pass, held-back loss climbing, and jumping about](../../images/starting-your-own-model/the-order-of-the-work/first-curve-shapes.svg)

The still-falling run ends at 0.591 and 0.699, the flat run sits at 2.469 and 2.488 from the first pass, the 60-example run reaches 0.046 on training while its held-back loss climbs to 1.286, and the fourth jumps as high as 37.528.

Two lines falling together means nothing is wrong and the run should be longer.
Two flat lines from the first pass mean nothing is learning, and after the second
rung you know that is a learning rate near zero rather than a disconnected model.
A training loss near zero with a held-back loss climbing is memorising, and the
cure is more examples or a smaller model. A curve that jumps by tens is a learning
rate far too large, which the size of the numbers on the axis gives away at a
glance.

---

## 5. Rung four: scale, one change at a time

The third rung gave one run that works and one number that beats the baseline,
which is the first point at which making anything bigger makes sense. The fourth
rung is a sequence of runs with one rule, that each changes one thing from the run
before it, and the measurements below are what happens when that rule is
broken.

![A bar chart of the final held-back loss of a starting run and four runs that each change one thing, with the change written inside each bar and a grey band for the seed spread](../../images/starting-your-own-model/the-order-of-the-work/one-at-a-time.svg)

From a starting run that ends at 0.842, four times the examples gives 0.697, four times the width gives 0.898, three times as many passes gives 1.076 and four times the batch gives 1.012.

Each run is readable because exactly one thing moved. Four times the examples is
worth 0.145 of loss and is the only change here that helps. Three times as many
passes costs 0.234, because this run was already past its best point, and four
times the batch costs 0.171, because the same passes with a bigger batch mean a
quarter as many steps. Four times the width moves the answer by 0.056, which the
grey band says is no result at all, for the reason two pictures below.

![Two panels, one with bars for a starting run, two single changes and both changes together, and one with the held-back curves of the same four runs](../../images/starting-your-own-model/the-order-of-the-work/two-at-once.svg)

Four times the examples takes the loss from 0.842 to 0.697 and cutting the hidden layer from 64 units to 8 takes it to 1.424, but doing both at once gives 0.853, which is 0.011 from where it started.

That is the demonstration. One of those changes was worth having and the other was
a disaster, and the run that made both came back saying nothing had happened.
Somebody who changed two things and saw no change would conclude that neither
mattered, and would be wrong twice over. Nothing about the combined run is faulty,
but 0.853 cannot be attributed, because two effects of opposite sign landed on top
of each other.

![Two panels, one showing the final held-back loss of six runs of identical settings with different seeds, and one showing the four single changes against a band of twice that spread](../../images/starting-your-own-model/the-order-of-the-work/seed-spread.svg)

Six runs with identical settings and only the seed changed end at 0.842, 0.854, 0.790, 0.846, 0.904 and 0.836, which is a spread of 0.034 and a difference of 0.115 between the best and the worst.

A **seed** is the number that decides every random choice a run makes, which here
is the starting weights and the order the examples are shuffled into. Six runs
differing only in that land 0.115 apart, so any change smaller is luck rather than
progress, and twice the spread, 0.067, is a reasonable line to draw. By it, three
of the four changes above are real and the wider model at 0.056 is not. The honest
report for a change inside the band is that you cannot tell, and two or three
seeds of each setting settle it cheaply.

![A chart on a log scale of the number of runs needed against the number of things you want to change, with one line for one change at a time and one for every mixture](../../images/starting-your-own-model/the-order-of-the-work/runs-needed.svg)

Telling eight changes apart takes 9 runs when they are made one at a time and 256 runs when every mixture is tried, which at 6,000 example-views a run is 54,000 against 1,536,000.

The obvious alternative is to try every combination, which does find effects that
appear only when two settings move together, and which costs 2 raised to the power
of the number of changes. For eight changes that is 256 runs, and at the size of a
real training job it is not a week anybody has. So people change one setting, keep
the winner and move on, accepting that a pair which only works jointly will be
missed, which is a real cost.

---

## 6. The run folder, and the run you keep

The fourth rung produces a pile of runs, and a pile of runs is worth nothing
unless you can say which settings produced which number. So this section is about
what to write down, and its rule is that the run you keep is not the one with the
best number but the one you can do again.

![A drawing of a run folder listing six files with their real byte sizes and a note on what each one is for](../../images/starting-your-own-model/the-order-of-the-work/run-folder.svg)

A real run folder holds config.json at 581 bytes, metrics.csv at 1,025 bytes, split-ids.txt at 11,760 bytes, stdout.log at 1,025 bytes, weights.pt at 9,181 bytes and checkpoint.pt at 26,549 bytes, which is 50,121 bytes in all.

Those six are a good minimum, and the first carries most of the value, because it
holds all 21 settings the run used. The metrics file has one row a pass, so a
curve can be redrawn without rerunning anything, and the list of which example
went into which half stops the split quietly changing between runs. The last two
are the model saved twice, once as the weights alone for using and once with the
optimiser state for carrying the run on, as [the training
loop](../03_how-training-works/04_the-training-loop.md#6-reading-the-curve-the-time-a-run-takes-and-the-checkpoint)
explains.

![Two panels, one with two curves from the same settings and the same seed lying exactly on top of each other, and one with two curves from the same settings and different seeds](../../images/starting-your-own-model/the-order-of-the-work/reproduce-or-not.svg)

Running the same settings with the same seed twice gives two curves whose largest difference is 0.0e+00, while a different seed gives curves that differ by as much as 0.114 and end at 0.842 against 0.846.

The left panel is what reproducible means in practice, which is that the second run
lands on the first to the last digit the computer keeps, and it happens only
because the seed was written down with everything else. A folder without one holds
a run you can approximately repeat, which is not the same thing when you are
chasing a difference of 0.05.

![A horizontal bar chart of how far the final held-back loss moves when each setting is changed one at a time, sorted by size, with a grey band for the seed noise](../../images/starting-your-own-model/the-order-of-the-work/which-settings-matter.svg)

Cutting the width from 64 to 8 costs 0.582 and dropping the learning rate to 0.0004 costs 0.571, while the passes cost 0.234, the batch 0.171, more examples gain 0.145, and weight decay and the seed move it by 0.006 and 0.004.

The two at the top would make a run unrecognisable if they were lost, and the
learning rate in particular is why a run folder with no config file is barely a
result. The two at the bottom land inside the seed band, which does not mean they
can be left out, because a setting that does not matter here may matter on the
next job and writing it down costs one line.

![A bar chart on a log scale of the byte sizes of four text files, a small checkpoint and the checkpoint of a wider model](../../images/starting-your-own-model/the-order-of-the-work/log-cost.svg)

The three files that describe the run come to 2,631 bytes, while a checkpoint of a model with 55,306 weights is 669,453 bytes, which is 254 times as much.

Writing down what a run was costs about a thousandth of what its output costs, and
real models are far larger than this one, so the ratio only gets more lopsided.
There is no version of this in which logging is the expensive part. What is
expensive is a folder of twelve runs and no way of telling which produced the
number you liked, and the cure is to write the settings down before the run rather
than after it.

---

## 7. Where to read next

- [What to reuse and what to train](03_what-to-reuse-and-what-to-train.md) is the
  next page, and it decides what the model on rung three should actually be, from
  using somebody else's model as it is through to training from nothing.
- [Before you train anything](01_before-you-train-anything.md) is the page this
  one follows, and it is where the job, the baseline and the split that rung three
  depends on are decided.
- [When it does not work](06_when-it-does-not-work.md) is the diagnosis page, and
  it picks up where the ladder ends, with the failures that survive all four
  rungs.
- [Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
  explains the gap in section 4 properly, and how a split is built so that it
  cannot leak.
- [The training loop](../03_how-training-works/04_the-training-loop.md) is where
  the loop, the optimiser and the checkpoint of section 6 come from.
- [Evaluation and failure](../../07_learned-models/10_making-models-work-on-an-arm/02_most-used/03_evaluation-and-failure.md)
  in the catalogue book is what the fourth rung becomes once the model is on a real
  arm, where the number to beat is trials rather than loss.

---

## 8. Using it in Python

The first two rungs are about twenty lines of PyTorch between them, and this is
all of it. The block runs as it stands on ten made-up examples, and it prints the
check from section 2 and both the test and the planted bug from section 3, so
passing and failing appear side by side.

```python
import json
import pathlib

import torch
from torch import nn
import torch.nn.functional as F

torch.manual_seed(0)
x = torch.randn(10, 16)                      # ten examples, sixteen readings each
y = torch.arange(10)                         # section 3: one example of each class
model = nn.Sequential(nn.Linear(16, 64), nn.ReLU(), nn.Linear(64, 10))

# Section 2: one batch through the untrained model, before any training at all.
with torch.no_grad():
    out = model(x)
    first = F.cross_entropy(out, y)
print('what comes out has shape', tuple(out.shape))
print('first loss %.3f, and ln(10) is %.3f' % (first, torch.tensor(10.0).log()))

# Section 3: memorise those ten on purpose. If this will not fall, stop here.
opt = torch.optim.AdamW(model.parameters(), lr=0.05)
for _step in range(200):
    loss = F.cross_entropy(model(x), y)
    opt.zero_grad()
    loss.backward()
    opt.step()
print('after 200 steps on ten examples, loss %.2e' % loss.item())

# Section 3 again, with the input cut off, which is the bug the test catches.
broken = nn.Sequential(nn.Linear(16, 64), nn.ReLU(), nn.Linear(64, 10))
opt = torch.optim.AdamW(broken.parameters(), lr=0.05)
for _step in range(200):
    loss = F.cross_entropy(broken(torch.zeros_like(x)), y)
    opt.zero_grad()
    loss.backward()
    opt.step()
print('with the input zeroed, loss %.3f' % loss.item())

# Section 6: write the settings down before the run, not after it.
cfg = {'seed': 0, 'learning_rate': 0.05, 'steps': 200, 'batch': 10, 'classes': 10}
pathlib.Path('config.json').write_text(json.dumps(cfg, indent=2) + '\n')
print('config.json is', pathlib.Path('config.json').stat().st_size, 'bytes')
```

That block prints a shape of `(10, 10)`, a first loss of 2.332 against an expected
2.303, a loss of 4.17e-07 after 200 steps, a loss of 2.303 for the run whose input
was zeroed, and a config file of 89 bytes. Those five numbers are the whole of the
first two rungs, and the only part to change for your own job is the line that
makes `x` and `y`.

The library gives you very little of this, which is the point. PyTorch will not
tell you that your first loss is wrong, because it does not know how many classes
you meant to have, and `F.cross_entropy` will cheerfully accept probabilities
where it wanted raw scores and hand back a number that looks fine. Nothing in it
will tell you that a model cannot memorise ten examples either, because from the
library's side nothing failed.

What you still choose is the ten examples, and one of each class is worth having,
because a batch that happens to hold three classes proves less. You choose the
number of steps, and a few hundred is plenty, since a model that will memorise ten
examples usually does it in under fifty. You also choose what goes in the config
file, and the rule from section 6 is that anything you would have to guess in
order to repeat the run belongs in it, with the seed first.
