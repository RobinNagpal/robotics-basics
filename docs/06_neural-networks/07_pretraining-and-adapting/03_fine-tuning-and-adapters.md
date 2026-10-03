# Fine-tuning and adapters

The page before this one, [scale, data and compute](02_scale-data-and-compute.md),
worked out what it takes to train a large model from nothing, and the honest
summary was that almost nobody does it. The graphics cards, the months of running
time and the trillions of words of text are out of reach for all but a handful of
organisations. What almost everybody does instead is take a model that somebody
else has already trained and change it a little, so that it does the particular job
in front of them. That last step is what this page is about, and it is the one step
in this chapter that you are likely to perform yourself.

The job has a name. **Fine-tuning** means taking a model whose weights were set by
[pretraining](01_self-supervised-pretraining.md) and training it further on a
smaller set of examples of your own, so that it does your job rather than the
general one it was pretrained for. There is more than one way to do it, and the ways
form a ladder from almost free to very expensive, so most of this page is about
where on that ladder you should stand and what each rung costs you.

It is written for a reader who has read the two pages before it, so it assumes you
know what pretraining is, what a frozen backbone is, what a graphics processing unit
does, and what a floating-point operation (FLOP) is, all of which those two pages
explain. It also assumes you know what a transformer block holds, from [a
transformer block](../06_the-transformer/02_a-transformer-block.md), and what an
optimiser such as AdamW keeps in memory, from [the training
loop](../03_how-training-works/04_the-training-loop.md).

Two kinds of number appear in the pictures. The parameter counts, the memory sizes
and the adapter counts are exact arithmetic on one stated model shape, which is a
transformer of 32 blocks with a width of 4096, 32 attention heads, a feed-forward
inner width of 11008 and a vocabulary of 32000. The learning experiments are
simulated: a small network is trained in NumPy on made-up readings of six objects,
and then fine-tuned, so that the behaviour you are being shown is real behaviour of
a real training run on invented data. Every number is printed by
`docs/diagrams/pretraining_and_adapting_2.py`.

## Contents

1. [The five rungs, from a better prompt to a full retrain](#1-the-five-rungs-from-a-better-prompt-to-a-full-retrain)
2. [What each rung costs in numbers and in memory](#2-what-each-rung-costs-in-numbers-and-in-memory)
3. [Low-rank adaptation, worked out with real shapes](#3-low-rank-adaptation-worked-out-with-real-shapes)
4. [QLoRA: an adapter on a squeezed base](#4-qlora-an-adapter-on-a-squeezed-base)
5. [Catastrophic forgetting, and what actually helps](#5-catastrophic-forgetting-and-what-actually-helps)
6. [How much data a fine-tune needs](#6-how-much-data-a-fine-tune-needs)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. The five rungs, from a better prompt to a full retrain

Because the model you start from was pretrained by somebody else, the question is
not whether to train it but how much of it to let training touch, and the answers
form a ladder of five rungs that runs from changing nothing at all to changing every
number in the file. The picture below shows the same model five times, once for each
rung, with the parts that training is allowed to move drawn in colour and the parts
that stay exactly as they were drawn in grey.

![Five copies of a 32-block transformer, with nothing coloured for a prompt, a new head for a frozen backbone, thin side paths for an adapter, the last four blocks for partial unfreezing, and everything for a full fine-tune](../../images/pretraining-and-adapting/fine-tuning-and-adapters/rungs-what-moves.svg)

Each rung lets training move more of the model than the one before it, and the count
under each column is how many numbers that rung actually changes.

The first rung is to leave the weights alone and write a better **prompt**, which
means the text or the picture you put in front of the model before you ask it the
real question. This changes nothing inside the file, so it costs no training at all
and you can try a new one every minute, and that speed is exactly why it is the rung
to try first. What it cannot do is teach the model something it does not already
contain, because every behaviour a prompt can reach is a behaviour the pretrained
weights already hold, and a prompt also has to be paid for on every single call,
which the third picture below works out.

The second rung freezes the pretrained model and trains one small new layer on top
of it, usually called a **head**, which is a short layer that turns the model's
internal numbers into the answers your job needs. The model's own layers are then
only used to turn an input into a list of numbers that describes it, which the
previous pages called a representation, and training only has to find the few
thousand numbers in the head. This is cheap and it almost never breaks anything,
because the pretrained part cannot change, but it can only recombine what the
pretrained model already measures, and section 6 shows that running into exactly
that wall.

The third rung adds an **adapter**, which is a small set of extra weights placed
beside the existing ones and trained while the existing ones stay frozen. The most
used kind by far is low-rank adaptation (LoRA), which section 3 works out in full.
The fourth rung stops freezing part of the model and lets the last few blocks train
normally, which gives training real room to move while still leaving most of the
file alone. The fifth rung is **full fine-tuning**, where every weight is free to
change, and it is the most capable and by a wide margin the most expensive.

![Horizontal log bars of the trainable count for each rung: 0, 24,582, 4,194,304, 809,533,440 and 6,738,415,616](../../images/pretraining-and-adapting/fine-tuning-and-adapters/rung-trainable-bars.svg)

Each rung multiplies the number of trainable weights by roughly a hundred, so the
bars have to be drawn on a scale where each gridline is a hundred times the one
before it.

The jumps are enormous. A new six-way head on this model holds 24,582 numbers, a
rank-8 adapter on the query and value matrices holds 4,194,304, unfreezing the last
four blocks puts 809,533,440 in play, and a full fine-tune puts all 6,738,415,616 in
play. The three middle rungs together are what people mean by **parameter-efficient
fine-tuning**, which is the general name for any method that trains a small fraction
of a model's weights and leaves the rest frozen.

Because a prompt is free to make and a fine-tune is not, it is tempting to stop at
the first rung, but a prompt is not actually free, because the extra words are read
again on every single call. A forward pass through a model costs about two
floating-point operations for each parameter and each token, which the [scale
page](02_scale-data-and-compute.md) explained, so for this model one token of prompt
costs 13.48 GFLOP, and 600 extra tokens of instructions cost 8.09 TFLOP every time
the model is called.

![A log-log plot of cumulative arithmetic against the number of calls, with a rising line for the prompt and a flat line for the fine-tune, crossing at 3,000 calls](../../images/pretraining-and-adapting/fine-tuning-and-adapters/prompt-cost-crossover.svg)

The arithmetic a longer prompt costs grows with every call, while a fine-tune is
paid once, so the two lines cross at a point that can be worked out exactly.

Training this model on 500 examples of 400 tokens for three passes costs about
24.26 PFLOP, because training costs about six floating-point operations per
parameter per token rather than two. Dividing one by the other says that the longer
prompt has cost as much arithmetic as the fine-tune after 3,000 calls, and by
100,000 calls it has cost 808.61 PFLOP, which is 33 times the fine-tune. So a prompt
is the cheap answer for something you do rarely and the expensive answer for
something a robot does all day.

![Horizontal log bars of the bytes you must store per job: nothing, 48 KiB, 8 MiB, 1.51 GiB and 12.55 GiB](../../images/pretraining-and-adapting/fine-tuning-and-adapters/bytes-you-ship.svg)

The last thing each rung costs is storage, because every job you adapt the model for
leaves you a file to keep, and the size of that file decides whether you can have
twenty jobs or only one.

Storing the changed weights at two bytes each, a head costs 48 KiB, a rank-8 adapter
costs 8 MiB, four unfrozen blocks cost 1.51 GiB, and a full fine-tune costs the whole
12.55 GiB again. This is why a robot fleet with twenty jobs usually keeps one base
model and twenty adapters rather than twenty models, and it is a practical reason to
prefer the middle rungs that has nothing to do with accuracy.

---

## 2. What each rung costs in numbers and in memory

The counts in the last section came from one stated model shape, so before using
them for anything it is worth seeing where they come from, because the same
arithmetic will tell you the cost of any other model you meet. The model is a
transformer of 32 blocks, each block of width 4096 with 32 attention heads and a
feed-forward inner width of 11008, reading a vocabulary of 32000 tokens.

![A stacked bar and a log bar chart splitting 6,738,415,616 parameters into embeddings, attention, feed-forward, output head and norms](../../images/pretraining-and-adapting/fine-tuning-and-adapters/model-shape-parameter-count.svg)

The parameters are not spread evenly through the model, and the feed-forward parts
of the blocks hold almost two thirds of them.

The embedding table is 32000 times 4096, which is 131,072,000 numbers, and the
output head is the same size again. Inside one block the attention part holds four
matrices of 4096 by 4096, which is 67,108,864 numbers, and the feed-forward part
holds three matrices of 4096 by 11008, which is 135,266,304, so one whole block is
202,383,360 and the 32 blocks together are 6,476,267,520. Adding the embeddings, the
output head and the small normalisation scales gives 6,738,415,616 parameters, which
is what people round off to seven billion.

Counting parameters is only half of the memory question, because during training a
parameter that is free to change costs much more than a parameter that is frozen.

![Two bars broken into bytes: a frozen parameter costs 2, and a trainable one costs 2 for the weight, 2 for the gradient and 4 plus 4 for the optimiser](../../images/pretraining-and-adapting/fine-tuning-and-adapters/bytes-per-parameter.svg)

A frozen parameter needs its own value and nothing else, while a trainable one needs
its value, its gradient and two running averages that the optimiser keeps.

Under the common recipe shown here, a weight stored as bfloat16 takes 2 bytes, its
gradient takes 2 more, and AdamW keeps a running average of the gradient and a
running average of the squared gradient as float32, which is 4 bytes each. So a
frozen parameter costs 2 bytes and a trainable one costs 12, which is six times as
much, and that factor of six is the whole reason freezing saves what it saves.

![Stacked bars of training memory per rung, from 12.55 GiB for a prompt to 75.31 GiB for a full fine-tune, with a 24 GiB card line](../../images/pretraining-and-adapting/fine-tuning-and-adapters/memory-per-rung.svg)

Reading the bars from the bottom up, each one shows the frozen weights, then the
gradients of whatever is being trained, then the optimiser state for the same
weights, with the total printed above.

A full fine-tune of this model needs 75.31 GiB before a single activation has been
stored, which does not fit on one 24 GiB graphics card and does not fit on two.
Unfreezing the last four blocks needs 20.09 GiB, which fits but leaves almost nothing
for the activations. A rank-8 adapter needs 12.60 GiB, which is the 12.55 GiB of
frozen weights plus 0.05 GiB for the adapter and everything training needs for it,
and that is why so many people's first successful fine-tune is a LoRA one.

![Two panels showing memory and trainable share rising as more blocks are unfrozen, with 6 blocks fitting inside 24 GiB](../../images/pretraining-and-adapting/fine-tuning-and-adapters/unfreeze-how-many-blocks.svg)

Unfreezing is not an all-or-nothing choice, so the left panel shows what each extra
unfrozen block costs in memory and the right panel shows what share of the model it
puts in play.

Each block costs 1.88 GiB more memory once its gradients and optimiser state are
counted, and each block is 3.00% of the model, so on a 24 GiB card you can unfreeze
6 blocks and reach 23.86 GiB before you run out, with nothing left over. That number
is the honest reason people reach for adapters: not that unfreezing is wrong, but
that the memory runs out after a sixth of the model.

---

## 3. Low-rank adaptation, worked out with real shapes

The memory figures in the last section made the third rung look attractive, so this
section explains exactly what that rung does, because low-rank adaptation is the
method you are most likely to use and it is simpler than its name suggests.

Start from one weight matrix in the model, say one of the 4096 by 4096 matrices in
the attention part of a block. Fine-tuning it normally would mean working out a
change for each of its 16,777,216 numbers. **Low-rank adaptation (LoRA)** says that
the change does not need that much freedom, so instead of learning the change
directly it learns two thin matrices whose product has the same shape as the
original, and it trains only those.

![A 4096 by 4096 square, a tall thin 4096 by 8 block, a long thin 8 by 4096 block, and their product drawn as a square of the same size as the first](../../images/pretraining-and-adapting/fine-tuning-and-adapters/lora-two-thin-matrices.svg)

The product of a 4096 by 8 matrix and an 8 by 4096 matrix is itself 4096 by 4096, so
it can be added to the original weights, even though it was built from far fewer
numbers.

The number 8 here is the **rank**, which is how many columns the first thin matrix
has and how many rows the second one has, and it is the one number you choose. At
rank 8 the two thin matrices hold 8 times 4096 twice, which is 65,536 numbers, and
that is 0.391% of the 16,777,216 in the matrix they stand in for. During training
the original matrix never changes, and only those 65,536 numbers move.

![A log bar chart of trainable numbers against rank from 1 to 128, with the full matrix size drawn as a line far above](../../images/pretraining-and-adapting/fine-tuning-and-adapters/lora-rank-counts.svg)

Doubling the rank doubles the numbers you train, and even at rank 128 the adapter is
a small fraction of the matrix.

A rank-1 adapter holds 8,192 numbers, which is 0.049% of the matrix, rank 4 holds
32,768, rank 16 holds 131,072, and rank 128 holds 1,048,576, which is still only
6.250%. The two shapes only break even at rank 2048, so any rank you would actually
pick is far cheaper than training the matrix itself. A higher rank gives the adapter
more freedom and therefore more of the accuracy a full fine-tune would reach, and
what it costs is memory and the risk of fitting your small set of examples too
closely, so people usually start between 8 and 32 and only go higher if the job
needs it.

A transformer block holds seven weight matrices, and you have to decide which of
them get adapters, because that choice changes the count as much as the rank does.

![A table of the seven weight matrices in a block with their shapes and counts, beside bars for three choices of where to attach adapters](../../images/pretraining-and-adapting/fine-tuning-and-adapters/lora-where-in-the-block.svg)

The left side lists each matrix in a block with its shape, the numbers it holds and
what a rank-8 adapter on it would cost, and the right side totals three common
choices over all 32 blocks.

Attaching rank-8 adapters to the query and value matrices only, which is the most
common starting point, trains 4,194,304 numbers, or 0.0622% of the model. Covering
all four attention matrices doubles that to 8,388,608. Covering the feed-forward
matrices as well brings it to 19,988,480, which is 0.2966% of the model, and it is
more because each feed-forward matrix is 4096 by 11008 so its rank-8 adapter holds
120,832 numbers rather than 65,536. Adding the feed-forward matrices usually helps
when the new job needs new knowledge rather than a new style, and it costs about
five times the memory of the query-and-value choice.

Two details finish the picture. The first is the **scaling factor**, which is a
number the adapter's output is multiplied by before it is added to the original
weights, written as alpha divided by the rank. The second is that the whole thing
can be folded away before the model is ever run.

![Two panels: the size of the added update against rank for three ways of scaling it, and bars of multiply-adds for the matrix alone, with a side path, and folded in](../../images/pretraining-and-adapting/fine-tuning-and-adapters/lora-scaling-and-folding.svg)

The left panel measures how big a change the adapter adds as the rank grows, and the
right panel counts the arithmetic the adapter costs when the model is used.

If nothing scales the adapter, then raising the rank raises the size of the change
it makes, because the product of the two thin matrices adds up more terms, and a
learning rate that suited rank 4 will then be too large at rank 64. Dividing by the
rank pulls the other way and makes the change smaller as the rank grows, and
dividing by the square root of the rank leaves it almost unchanged, which is why
some libraries now offer that third choice. What matters in practice is that alpha
is one knob you set for the overall strength of the adapter, and once it is set you
can change the rank without re-tuning everything else.

The folding is the part that makes LoRA cheap to deploy. Because the adapter's
product has the same shape as the original matrix, you can add it into the original
weights once, before the model is used, and from then on the model is an ordinary
model of exactly the original shape. Computing it as a separate side path costs
16,842,752 multiply-adds for each token instead of 16,777,216, which is 0.39% more,
while folding it in brings the count back to exactly 16,777,216. The two ways of
computing the answer agree to within 3.8e-17, which is the rounding of the
arithmetic itself, so the folded model is not an approximation of the adapted one,
it is the same model.

---

## 4. QLoRA: an adapter on a squeezed base

Section 2 showed that even a LoRA fine-tune still has to hold 12.55 GiB of frozen
weights, and since the frozen weights never change, it is fair to ask why they have
to be stored so precisely. **QLoRA** is the answer: it stores the frozen base model
in 4 bits for each weight instead of 16, and trains ordinary LoRA adapters on top of
it. The next page explains quantisation properly, so this section only says what the
combination makes possible.

![Stacked bars of memory for a full fine-tune, an adapter on a bfloat16 base and an adapter on a 4-bit base, against a 24 GiB card line](../../images/pretraining-and-adapting/fine-tuning-and-adapters/qlora-memory-stack.svg)

The bars show the frozen weights and everything training needs on top of them, for
the three ways of fine-tuning that matter most.

With the base in 4 bits and groups of 64 weights sharing a scale, the frozen part
comes to 3.33 GiB instead of 12.55 GiB, and the rank-8 adapters add 0.05 GiB, so the
whole thing starts from 3.38 GiB. On a 24 GiB card that leaves more than 20 GiB for
the activations, which is what decides how long a sequence you can train on, and it
is the difference between fine-tuning a seven-billion-parameter model on one ordinary
desktop graphics card and not being able to fine-tune it at all.

![Two panels: a stacked bar of bits per weight for five group sizes, and a curve of read-back error against the bits spent on scales](../../images/pretraining-and-adapting/fine-tuning-and-adapters/qlora-bits-and-groups.svg)

The left panel shows that 4-bit storage is never exactly 4 bits a weight, and the
right panel shows what the extra bits buy, measured on a real trained weight matrix.

Four-bit integers cannot cover the range of a weight matrix on their own, so each
small group of weights also stores a scale, which is a single ordinary number that
every integer in the group is multiplied by. With groups of 64 and a 16-bit scale
for each group, the true cost is 4.250 bits a weight, which is 3.33 GiB for this
model, while groups of 32 cost 4.500 bits and 3.53 GiB. Smaller groups cost more bits
and leave less error, and measured on one real 48 by 48 trained matrix the error left
in the weights falls from 15.54% with a single scale for the whole matrix to 10.27%
with one scale per group of 48 and 7.20% with one per group of 8.

The obvious worry about QLoRA is that the base model is now slightly wrong, so the
last picture measures what that costs and what the adapter wins back, using the small
simulated network.

![Two panels of bar charts: accuracy on the old job for a float, 8-bit and 4-bit base, and accuracy on a new job for four combinations of base and adapter](../../images/pretraining-and-adapting/fine-tuning-and-adapters/qlora-adapter-recovers.svg)

The left panel is what squeezing the frozen base costs on the job it was already good
at, and the right panel is what it costs on a new job once a small adapter has been
trained on 64 examples.

Squeezing this network's weights to 4 bits moves its accuracy on the old six-way job
from 0.933 to 0.930, which is a loss of 0.003, and at 8 bits there is no measurable
loss at all. On the new job the 4-bit base on its own scores 0.495, which is no
better than guessing between two classes, and a rank-2 adapter lifts it to 0.691,
against 0.708 for the same adapter on an unsqueezed base. So the base being slightly
wrong costs a little, the adapter does nearly all of the work either way, and what
you buy with that small loss is the ability to do the training at all. The cost that
is easy to forget is speed, because 4-bit weights have to be turned back into
ordinary numbers before every multiplication, which makes each training step slower
even though it uses less memory.

---

## 5. Catastrophic forgetting, and what actually helps

Every rung above the first changes weights that were set by pretraining, and those
weights were what made the model good at everything else, so the obvious danger is
that teaching it the new job quietly destroys the old one. This is called
**catastrophic forgetting**, and it is not a rare accident but the normal result of
training hard on a narrow set of examples.

The experiment behind the next four pictures is simulated and small enough to run in
full. A network of 1,670 parameters is trained on a six-way job, made of twelve
readings of six objects, and it reaches 0.933 on a held-out test set. It is then
fine-tuned on a narrow new job that only ever shows two of the six objects, in a new
part of the reading space where the two are harder to tell apart, and the old job is
measured after every step.

![Two curves against fine-tuning steps: the old job falling from 0.933 to 0.181 while the new job rises from 0.495 to about 0.8](../../images/pretraining-and-adapting/fine-tuning-and-adapters/forgetting-curves.svg)

The blue line is the job being taught and the red line is the job nobody is teaching
any more, and the red line falls much faster than the blue line rises.

After ten steps the new job has already reached 0.780, which is most of what it will
ever reach, and the old job has fallen from 0.933 to 0.693. After fifty steps the new
job is at 0.825 and the old job is at 0.257, and by three hundred steps the old job
is at 0.181, which is barely better than guessing one of six classes. The damage is
front-loaded, which is worth knowing, because it means a short fine-tune is not safe
simply by being short.

![Grouped bars for six recipes, showing the old job and the new job after each](../../images/pretraining-and-adapting/fine-tuning-and-adapters/forgetting-what-helps.svg)

Each pair of bars is one fine-tuning recipe, with the old six-way job on the left and
the new two-way job on the right, so a good recipe is one where both bars are tall.

Four things are usually suggested against forgetting, and this experiment tests all
four. Stopping early, after ten steps rather than three hundred, leaves the old job
at 0.709 and the new job at 0.759, so it helps but it gives up some of the new job
too. Using a learning rate of 0.012 instead of 0.15 leaves the old job at 0.771 and
the new job at 0.816, which is better on both counts and makes it the single most
useful change. Mixing a quarter of the old data back into every batch leaves the old
job at 0.874 and the new job at 0.800, which is the best result here. Using a rank-2
adapter at the same gentle learning rate leaves the old job at 0.699, which is no
better than tuning everything gently, because an adapter still changes what every
layer computes.

That last result deserves to be stated plainly, because adapters are often described
as a cure for forgetting and this experiment says they are not, at least not by
themselves. What an adapter really gives you is shown by the sixth pair of bars: the
original weights were never touched, so switching the adapter off restores the old
job to exactly 0.933, the number it had before any fine-tuning. A full fine-tune
cannot be undone that way unless you kept a second copy of the file.

![Two curves against the share of old data mixed into each batch, showing the old job jumping from 0.157 to 0.841 at 5%](../../images/pretraining-and-adapting/fine-tuning-and-adapters/forgetting-mix-fraction.svg)

The horizontal axis is how many old examples are added to each batch of new ones, as
a share of the batch, and the two lines are the two jobs.

The striking part is how little old data is needed. With none, the old job ends at
0.157, and with only 5% it ends at 0.841, which is most of the damage undone, while
the new job stays at 0.786 rather than 0.809. Going on to 25% gives 0.900 and 50%
gives 0.907, so the returns fall away quickly. This is why the usual advice is to
keep some of the pretraining data, or something like it, and to mix a little of it
into every fine-tuning batch, and it is cheap advice to follow.

![A scatter of old-job accuracy against new-job accuracy, with one line per learning rate running from 25 steps to 400](../../images/pretraining-and-adapting/fine-tuning-and-adapters/forgetting-frontier.svg)

Every point is one complete fine-tuning run, placed by how well it did on the new job
and how much of the old job it kept, and each line follows one learning rate as the
run gets longer.

The picture makes the trade visible. The gentlest learning rate stays high on the old
job throughout and reaches almost as far on the new one, while the two largest
learning rates end up below 0.21 on the old job whatever you do about the number of
steps. So the lever that matters most is the size of the step, not the length of the
run, and a fine-tune that is going badly is more often going badly because the
learning rate is too large than because it ran too long.

---

## 6. How much data a fine-tune needs

The last question everybody asks is how many examples a fine-tune needs, and the
honest answer is a range rather than a number, because it depends on which rung you
stand on and on how far the new job is from the old one. The same simulated setup can
measure all of that, so this section gives the reasoning rather than a figure to
quote.

![Three curves of new-job accuracy against the number of examples, for a head, a rank-2 adapter and a full fine-tune, with a ceiling line at 0.833](../../images/pretraining-and-adapting/fine-tuning-and-adapters/data-learning-curves.svg)

Each line is one rung of the ladder from section 1, averaged over fifteen runs, and
the dashed line at the top is the best accuracy anything could reach on this job,
which is 0.833 because the two clouds of readings overlap.

Before any tuning the model scores 0.495 on this job, which is useless. Training only
a new head climbs quickly to about 0.68 and then stops, and it even wobbles downwards
with more examples, because the frozen features simply do not contain the distinction
the new job needs and more examples only move the compromise the head settles on. A
rank-2 adapter reaches about 0.75 by 32 examples and keeps a small lead for a while.
A full fine-tune starts worst, at 0.579 with four examples, because it has the most
freedom and the fewest examples to constrain it, and it ends best, at 0.813 with 512
examples, which is within 0.02 of the ceiling. That is the shape of the whole
trade-off: fewer trainable numbers win when examples are scarce, and more trainable
numbers win when they are plentiful.

![Three curves for three new jobs at increasing distance from the old one, beside bars of the accuracy before tuning with the examples each needed](../../images/pretraining-and-adapting/fine-tuning-and-adapters/data-vs-distance.svg)

The three jobs differ in how far they are from what the model already knew, and the
right panel shows both where each one starts and how many examples it took to come
within 0.03 of its own ceiling.

The first job is the same two objects one step away in the reading space, and the
model already scores 0.818 on it before any training, so 32 examples finish it. The
second is the same two objects four steps away, where the model starts at 0.511, and
it still only needs 32 examples, because once it has seen a few the old distinction
still applies. The third job is the hard one: a finer distinction the model never had
to make, where it starts at 0.496 and needs 512 examples to come within 0.03 of its
ceiling of 0.833. So distance in the obvious sense, meaning how much the readings have
moved, mostly costs you accuracy before you start, while what really costs examples
is a distinction the pretrained model never learned to make.

![Five curves for jobs of increasing scatter, beside bars showing 64, 256, 512, 512 and more than 512 examples needed](../../images/pretraining-and-adapting/fine-tuning-and-adapters/data-vs-variation.svg)

Here the new job is held at the same distance and only its own variety is changed, so
the left panel shows the curves and the right panel the examples each one needed.

A job whose readings scatter by 0.50 has a ceiling of 0.973 and reaches it with 64
examples, while the same job scattered by 1.00 has a ceiling of 0.833 and needs 512,
and scattered by 1.60 it does not get there within 512 at all. So doubling the variety
of the job multiplied the examples needed by eight, and that is the mechanism behind
the usual advice to collect examples that cover every lighting condition, every
gripper, every table and every object pose you intend to meet.

Putting the three pictures together gives a way to reason rather than a number to
quote. If the new job is the old job in a new style, so that the model already does
better than chance on it, then tens to a few hundred examples on a small adapter are
usually enough. If the new job needs a distinction the model never had to make, you
should expect thousands, and you should expect a plain head to fail no matter how
many you collect. And whatever the job, the number of examples has to cover its
variety, so a narrow set of examples collected in one afternoon in one corner of one
room will give you a model that works in that corner of that room.

---

## 7. Where to read next

- [Making a model smaller and
  faster](04_making-a-model-smaller-and-faster.md) is the next page, and it explains
  the quantisation that section 4 used here, together with distillation and pruning.
- [Self-supervised pretraining](01_self-supervised-pretraining.md) is where the model
  you are fine-tuning came from, and it explains what a frozen backbone already
  knows.
- [Scale, data and compute](02_scale-data-and-compute.md) gives the arithmetic behind
  the FLOP counts in section 1 and the memory cost of a parameter.
- [Post-training a language
  model](../10_language-and-multimodal-models/02_post-training-a-language-model.md)
  uses these methods for a particular job, which is turning a raw pretrained model
  into one that follows instructions.
- [Vision-language-action
  models](../12_models-that-act/03_vision-language-action-models.md) shows a robot
  model that is almost always reached by fine-tuning something larger rather than
  training from nothing.
- [Fine-tuning](../../07_learned-models/10_making-models-work-on-an-arm/02_most-used/01_fine-tuning.md)
  in the models catalogue gives the same choice from the robot's side, with the named
  scripts and libraries you would actually run.

---

## 8. Using it in Python

Sections 1 to 3 counted trainable parameters by hand, and this section does the same
counting with real libraries, because the counts are the part you should check before
starting a run that will take hours. The code uses PyTorch and the Hugging Face
`peft` package, which is the usual way to attach LoRA adapters to a model you did not
write.

```python
import torch
from torch import nn
from peft import LoraConfig, get_peft_model

# Section 2's arithmetic, as a function of the stated shape.
d, layers, d_ff, vocab = 4096, 32, 11008, 32000
block = 4 * d * d + 3 * d * d_ff + 2 * d          # attention + feed-forward + norms
total = vocab * d + layers * block + d + vocab * d
print(f'{total:,}')                                # 6,738,415,616

# Section 2's memory recipe: 2 bytes frozen, 2 + 2 + 4 + 4 bytes trainable.
def gib(frozen, trainable):
    return (frozen * 2 + trainable * 12) / 2 ** 30
print(f'{gib(total, 0):.2f} GiB')                  # 12.55 GiB, weights only
print(f'{gib(total, total):.2f} GiB')              # 75.31 GiB, full fine-tune

# Section 3, on one attention matrix: the adapter is two thin matrices.
rank = 8
print(f'{2 * rank * d:,} of {d * d:,}')            # 65,536 of 16,777,216

# The same thing on a real model, with peft doing the surgery.
base = nn.ModuleDict({'q_proj': nn.Linear(d, d, bias=False)})     # stand-in for a block
config = LoraConfig(r=rank, lora_alpha=16, target_modules=['q_proj'])
model = get_peft_model(base, config)
model.print_trainable_parameters()   # trainable params: 65,536 || all params: 16,842,752

merged = model.merge_and_unload()    # section 3's folding: back to the original shape
print(sum(p.numel() for p in merged.parameters()))                # 16,777,216
```

The first three blocks are plain arithmetic, and you can run them on any laptop,
because nothing is loaded. They are worth running before you rent a machine, since
they tell you in one second whether the fine-tune you are planning will fit in the
memory you are about to pay for.

What the library does for you in the fourth block is the surgery. `get_peft_model`
walks the model, finds every layer whose name matches `target_modules`, puts a pair
of thin matrices beside it, sets every other parameter so that training ignores it,
and arranges the forward pass so that the side path is added with the alpha over rank
factor from section 3. `merge_and_unload` then performs the folding, adding the
product back into the frozen weights and giving you an ordinary model that runs at
the original speed. For a quantised base, as in section 4, the model is loaded with
`bitsandbytes` in 4 bits first and the same adapter code then applies unchanged.

What you still have to decide is everything this page has been about. You choose the
rung, and if it is LoRA you choose the rank and which matrices to attach to, which
together set the counts in section 3. You choose the learning rate and the number of
steps, which section 5 showed to be the main lever on forgetting, and whether to mix
old data back in. And you decide how many examples to collect and how widely to
spread them, which section 6 showed to depend on how far your job is from the one the
model was pretrained for. No library will make those choices, because they depend on
your job rather than on your model.
