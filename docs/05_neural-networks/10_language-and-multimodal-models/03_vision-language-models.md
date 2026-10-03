# Vision-language models

The page before this one, [post-training a language
model](02_post-training-a-language-model.md), finished a model that reads words
and writes words. That model is useful to a robot only when somebody types what
the robot can see, because the model itself has never looked at anything. This
page removes that restriction, and it answers one question: how do you join a
model that looks at pictures to a model that reads and writes words, so that one
model does both?

The answer is a construction you can draw. A vision backbone turns the camera
picture into a set of vectors, a small trained part called the projector turns
those into something shaped like word tokens, and the result is pushed into the
middle of the model's token stream as though somebody had typed it, after which
the model carries on predicting one token at a time as before.

This page is for a reader who has read [large language
models](01_large-language-models.md), so you already know that a model turns a
conversation into tokens and writes its reply one token at a time, and that the
number of tokens it can hold at once is limited. It also helps to have read
[vision backbones](../09_models-that-see/01_vision-backbones.md), because the
seeing half of what follows is one of those with nothing changed.

Every number in the pictures is worked out in
`docs/diagrams/language_and_multimodal_2.py` and printed when that script runs.
The sizes it works from are illustrative rather than a measurement of any named
model: an input square of 224 pixels cut into patches of 14, a vision backbone of
24 transformer blocks of width 1024, and a language model of 32 blocks of width
4096. The workbench pictures and the vector clouds are simulated with a stated
seed, and the arithmetic on top of them is real.

## Contents

1. [The two halves, and the gap between them](#1-the-two-halves-and-the-gap-between-them)
2. [The projector: one small matrix that is trained first](#2-the-projector-one-small-matrix-that-is-trained-first)
3. [A picture inside the token stream](#3-a-picture-inside-the-token-stream)
4. [The order the training happens in](#4-the-order-the-training-happens-in)
5. [Resolution: why one small square is not enough](#5-resolution-why-one-small-square-is-not-enough)
6. [What a vision-language model is weak at](#6-what-a-vision-language-model-is-weak-at)
7. [What it gives a robot that a detector cannot](#7-what-it-gives-a-robot-that-a-detector-cannot)
8. [Where to read next](#8-where-to-read-next)
9. [Using it in Python](#9-using-it-in-python)

---

## 1. The two halves, and the gap between them

A **vision-language model** is one model that takes a picture and some words
together and writes an answer in words, and it is built by joining two models
that already exist rather than by training something new from nothing. The
seeing half cuts the picture into small squares called patches and turns each
patch into a list of numbers, and the reading half turns each word piece into a
list of numbers and predicts what comes next.

![Two columns of boxes, the seeing half ending in 256 vectors of 1024 numbers and the reading half in tokens of 4096 numbers, with a red arrow between them](../../images/language-and-multimodal-models/vision-language-models/two-halves.svg)

The seeing half ends with 256 vectors of 1024 numbers each, and the reading half
wants vectors of 4096 numbers, so the two ends do not fit together.

Follow the left column down: a square of 224 pixels cut into patches of 14 gives
16 patches across and 16 down, which is 256 patches, and each becomes one vector
of 1024 numbers. On the right each word piece becomes one vector of 4096 numbers,
so the first problem is plain arithmetic. The second problem is harder to see and
matters more, because even if the two lists were the same length nothing has ever
made the backbone's numbers mean what the language model's numbers mean, since
the two halves were trained separately and neither has seen the other's output.

![Two histograms: patch vectors sit at length 24 and token embeddings at length 3, and after one block the answers differ by the same factor](../../images/language-and-multimodal-models/vision-language-models/vector-lengths.svg)

In a simulated set of vectors the backbone's are about 7 times as long as the
language model's, and feeding them straight in makes the first block answer about
7 times too loudly.

The left panel measures how long each kind of vector is in the ordinary way, as
the square root of the sum of the squares of its numbers, and the simulated patch
vectors average 23.89 against 3.33 for the token embeddings. The right panel
pushes both sets through the same small stand-in for a language model's first
block, and the answers from the patch vectors come out 6.9 times as long. A model
whose first block is shouted at like that gives nonsense, so something has to fix
both the length of the list and the size of the numbers in it.

![Three bars on a log scale: the backbone at 302 million parameters, the language model at 6.44 billion, and the projector at 4.2 million](../../images/language-and-multimodal-models/vision-language-models/parameter-shares.svg)

The part that does the joining holds 0.062 per cent of the whole model's
parameters, which is why it is the part that gets trained first.

The counting is plain arithmetic on the illustrative sizes: 302,592,000
parameters in the backbone, 6,442,450,944 in the language model, and 4,198,400 in
the joining part, which is 0.062 per cent of the 6,749,241,344 in all. That very
small share is what the rest of this page hangs on.

---

## 2. The projector: one small matrix that is trained first

The part that sits between the two halves is called the **projector**, and it is
one matrix multiply followed by one add, which is the arithmetic a single fully
connected layer does. It takes one patch vector and gives back one vector of the
width the language model wants, and all of its cleverness is in the numbers
inside the matrix, which are learned by training in the ordinary way.

![A five-number patch vector, a four by five matrix of weights, the four output numbers, and the four rows of arithmetic written out in full](../../images/language-and-multimodal-models/vision-language-models/projector-arithmetic.svg)

A patch vector of five numbers goes through a matrix of four rows, and each row
gives one output number.

Work the first row through by hand and you will see there is nothing else to it.
The patch vector is +0.40, -0.90, +1.30, +0.20 and -0.50, the first row of the
matrix is +0.5, -0.2, +0.9, +0.1 and -0.4, the five products add up to +1.770,
and the row's own extra number of +0.10 makes +1.870. The other three rows give
-1.220, -0.920 and +0.580, and those four numbers are now one token as far as the
language model is concerned.

![Three boxes: 256 patch vectors of 1024 numbers, a projector matrix of 1024 in by 4096 out, and 256 picture tokens of 4096 numbers](../../images/language-and-multimodal-models/vision-language-models/projector-shapes.svg)

At the real sizes the same multiply turns 256 vectors of 1024 numbers into 256
vectors of 4096 numbers, using 4,198,400 parameters.

The real matrix has 1024 columns and 4096 rows, which is 4,194,304 weights, and
4,096 more numbers to add, one per row. Every one of the 256 patches goes through
that same matrix, so one picture costs 256 times 1024 times 4096, or
1,073,741,824 multiply-and-adds, which is small beside what the language model
does on every token it writes.

![Two bar charts comparing one linear layer, two layers with GELU and a resampler, by parameters and by tokens produced](../../images/language-and-multimodal-models/vision-language-models/projector-kinds.svg)

The three common shapes of projector trade parameters against the number of
tokens the picture costs.

The simplest is the single layer just described. A slightly larger one puts two
such layers back to back with a smooth bending rule between them, which comes to
20,979,712 parameters and still 256 tokens out, and it is used because one layer
sometimes cannot change the shape of the numbers enough. The third kind, called a
resampler, uses attention to squeeze the 256 patch vectors down to a fixed
smaller number, 64 in the drawing, which costs 75,759,616 parameters but hands
the language model a quarter of the tokens. Most builders start with the single
layer because it is the cheapest thing that works, and they reach for the
resampler when context is what they run out of.

![Two scatter plots of simulated vectors: before training the picture tokens sit apart from the word cloud, after training they sit inside it](../../images/language-and-multimodal-models/vision-language-models/projector-pulls-in.svg)

Training the projector moves the picture tokens from an average distance of 7.19
from the middle of the word cloud down to 1.23.

The panels are drawn from simulated vectors, so they show the shape of what
training does rather than a measurement. What training changes is the matrix, and
what the matrix does is move and stretch and rotate the whole cloud of patch
vectors until it sits where the language model's own tokens sit, while nothing
about the backbone or the language model changes at all.

---

## 3. A picture inside the token stream

Once the projector has done its work the picture is 256 ordinary tokens, and they
are placed in the stream where the picture appeared in the conversation. The
result is called a **multimodal token stream**, which means one row of tokens in
which some came from words and some came from a picture, and multimodal only
means that more than one kind of input went into it.

![A bar divided into four parts, 38 system tokens, 256 picture tokens, 17 question tokens and 24 answer tokens, adding to 335](../../images/language-and-multimodal-models/vision-language-models/token-stream.svg)

One picture and one short question make a stream of 335 tokens, of which the
picture is 256, or 76 per cent.

Read the bar in the order the model reads it: 38 tokens of standing instructions,
then the 256 from the picture, then 17 for the question, then 24 of answer. The
model cannot tell from the row itself which tokens came from a camera, because by
the time they reach the first block they are all vectors of 4096 numbers, and
that sameness is the whole trick. Answering a question about a picture this way
is called **visual question answering**.

![Three horizontal bars against a context window of 8,192 tokens, showing 3.1 per cent, 31.2 per cent and 78.1 per cent](../../images/language-and-multimodal-models/vision-language-models/context-share.svg)

Against a context window of 8,192 tokens, one squeezed picture takes 3.1 per
cent, a tiled picture of 672 pixels takes 31.2 per cent, and a tiled camera frame
takes 78.1 per cent.

The two tiled schemes are explained in section 5, but their cost is worth seeing
now because it shapes every later decision. A 672 pixel picture cut into 9 crops
plus a thumbnail is 10 lots of 256, which is 2,560 tokens, and a 1,280 by 720
camera frame cut into 24 crops plus a thumbnail is 6,400 tokens, which leaves
almost nothing for the conversation.

![A log-scale bar chart of how many pictures fit in an 8,192 token window and a 131,072 token window](../../images/language-and-multimodal-models/vision-language-models/pictures-that-fit.svg)

An 8,192 token window holds 32 squeezed pictures, 3 tiled 672-pixel pictures or 1
tiled camera frame, and a 131,072 token window holds 512, 51 and 20.

The larger window helps, and windows of that size are ordinary now, but it helps
less than it looks, because a robot watching a cell produces a frame many times a
second and twenty frames is under a second of video. The deeper problem is not
storage but work.

![Two curves of attention pairs against the number of pictures, one flat for squeezed crops and one rising steeply for tiled pictures](../../images/language-and-multimodal-models/vision-language-models/attention-cost.svg)

Eight tiled pictures need 421,686,225 attention comparisons against 4,422,609 for
eight squeezed ones, which is 95 times the work.

[Attention](../06_the-transformer/01_attention.md) explained why the cost grows
with the square of the length of the stream, and this curve is that square drawn
out. Doubling the detail in a picture multiplies the work by about four, which is
the real reason resolution is rationed, and section 5 returns to that once the
training order is settled.

---

## 4. The order the training happens in

The parts are joined, but a projector filled with random numbers hands the
language model noise, so all three parts have to be trained, and the order
matters more than anything else in this construction. The usual order has two
stages: first the two big parts are frozen, which means their weights are held
still while only the projector changes, and then the language model is unfrozen
so that it can change too.

![Two stages side by side, the first moving 4,198,400 parameters and the second moving 6,446,649,344](../../images/language-and-multimodal-models/vision-language-models/freeze-stages.svg)

The first stage moves 0.062 per cent of the model's parameters and the second
moves 95.520 per cent of them.

The backbone usually stays frozen through both stages, and its last few blocks
are unfrozen only when the pictures are unlike anything it was pretrained on,
such as medical scans or a depth camera's output.

![Stacked bars of memory: 12.6 gibibytes for stage one, 96.6 for stage two and 100.6 for training everything at once](../../images/language-and-multimodal-models/vision-language-models/stage-memory.svg)

Holding the weights takes 12.57 gibibytes, and training adds about 14 bytes for
every parameter that moves, which takes the first stage to 12.6 gibibytes and the
second to 96.6.

Read the bars as two layers. The grey layer is the weights at 2 bytes each, which
you pay whatever you train, and the red layer is what training adds: a gradient
for each trained parameter, the optimiser's two running averages, and a more
accurate copy. The first stage fits on one ordinary graphics card and the second
needs several, which alone is a reason to do the cheap stage first, because you
find out whether the projector can learn anything before paying for the expensive
one.

![Two log-scale loss curves: both orders learn the picture task, but training everything at once sends the old text loss up to 3.46 before it comes back](../../images/language-and-multimodal-models/vision-language-models/order-curves.svg)

In a small real training run, freezing first keeps the text loss between 0.0777
and 0.0960 throughout, while training everything at once sends it up to 3.456,
which is 44 times where it started.

The curves come from a small network written in NumPy and trained by real
gradient descent on a made-up task, so they are measured rather than drawn by
hand. A two-layer body is first trained on a text task until it is good at it, a
random projector is attached, and the picture task is then trained in the two
orders. Both orders end up reading the pictures, with the picture loss falling
from 61.4 to 0.1227 and 0.0891, so on that measure there is nothing to choose
between them. The difference is in the second panel, where training everything at
once lets the gradients from a random projector flow straight into the body and
wreck what it already knew.

In this small run the damage is repaired, because the original text data is still
there in full. In a real run it is not, because nobody has the whole pretraining
corpus to hand, which is the problem that [fine-tuning and
adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md) calls
catastrophic forgetting. Freezing first avoids it for a simple reason: a frozen
weight cannot be damaged, and by the time the big parts are let loose the
projector already produces something sensible, so the gradients reaching them are
small.

---

## 5. Resolution: why one small square is not enough

The order of training settles how the model is built, and resolution settles what
it can actually see, which is where these models disappoint on a robot. The
backbone takes a square of a fixed size, so a camera picture is squeezed to fit,
and squeezing throws away exactly the small details an arm cares about.

![A 672-pixel workbench picture and the same picture squeezed to 224 pixels, with the bottle's printed label enlarged in both](../../images/language-and-multimodal-models/vision-language-models/squeezed-picture.svg)

Squeezing a 672-pixel picture to 224 drops the brightness spread across the
printed line from 0.416 to 0.146, a fall of 65 per cent, and turns 10-pixel
characters into 3.3-pixel ones.

The workbench picture is drawn by the script rather than photographed, and the
squeezing is a real 3 by 3 block average, which is what resizing does. The label
is printed with strokes 2 pixels wide, so after averaging each stroke is 0.67 of
a pixel and is blended with the white paper on either side of it, which is the
arithmetic behind the fact that the small version cannot be read.

![A 672-pixel picture divided into nine crops of 224 pixels, a thumbnail of the whole picture, and a table adding the tokens to 2,560](../../images/language-and-multimodal-models/vision-language-models/tiling-layout.svg)

Cutting the picture into 9 crops and adding one thumbnail costs 10 lots of 256
tokens, which is 2,560, or 10 times one squeezed picture.

The common fix is to stop squeezing and start cutting. The picture is divided
into squares the size the backbone wants, each goes through the backbone
separately, and all the resulting tokens go into the stream together. The
thumbnail is added so that the model can see how the pieces fit together, because
a model given only the nine crops has no easy way to know they came from one
scene.

![Two bar charts: tokens for one picture rising from 256 to 6,400, against the millimetres of table one patch covers falling from 21 to 7](../../images/language-and-multimodal-models/vision-language-models/token-bill.svg)

Squeezing costs 256 tokens and gives each patch 42 original pixels, or 21
millimetres of table, while tiling costs 2,560 or 6,400 tokens and gives each
patch 14 pixels, or 7 millimetres.

To turn pixels into something an arm can use, the drawing assumes a camera that
sees 640 millimetres of bench across its 1,280 pixels, or half a millimetre per
pixel.

![A falling curve of millimetres under one patch against tokens spent, from 40 millimetres at 512 tokens down to 7 at 6,400](../../images/language-and-multimodal-models/vision-language-models/detail-curve.svg)

Cutting a camera frame into more crops improves the detail with the square root
of the tokens spent, and stops at 7 millimetres, which is the camera's own limit.

Follow the curve from left to right. One crop over the whole frame costs 512
tokens for 40 millimetres a patch, 2 crops across cost 1,280 tokens for 20
millimetres, 3 across cost 1,792 for 13.3, 4 across cost 3,328 for 10, 5 across
cost 4,096 for 8, and 6 across cost 6,400 for 7, at which point the crops are at
the camera's own resolution and further cutting buys nothing. Spending twelve and
a half times the tokens bought under six times the detail, because tokens count
area and detail counts length.

---

## 6. What a vision-language model is weak at

That measurement turns straight into the list of things the model gets wrong,
because every weakness here follows from the patch grid rather than from the
model being badly trained.

![A workbench picture with a 42-pixel patch grid, the same with a 14-pixel grid, and three sentences a model might write about where the bottle is](../../images/language-and-multimodal-models/vision-language-models/position-grain.svg)

The finest position the stream can refer to is one patch, which is 21 millimetres
of bench on a squeezed picture and 7 millimetres on a tiled one, and the answer
comes out as words rather than as pixel numbers.

There are two separate limits here. The first is the grid, because the model's
evidence about where something is comes from which patch it was in, and the
second is the output, because a sentence such as "just left of centre, standing
up" carries no pixel numbers at all. A model can be asked to write numbers and it
will, but they can only be as good as the grid the evidence came from.

![A log-scale curve of patches covered against object size, with a screw head, a bolt and a mug marked, beside bars of the smallest readable character](../../images/language-and-multimodal-models/vision-language-models/object-size.svg)

A 6-millimetre screw head covers 0.082 of a patch on a squeezed picture and 0.73
of a patch on a tiled one, and printed characters must be 22.5 millimetres tall
to survive squeezing against the 5 millimetres on the bottle's label.

The dotted line at one patch is the line that matters, because an object below it
has no token of its own and only tints a token it shares with whatever is around
it. The right panel applies a simple rule to print, that a stroke needs about 3
pixels to be told apart from the gap beside it, so squeezing by 3 means a stroke
needs 9 original pixels and the smallest readable character is 22.5 millimetres,
while tiling brings that down to 7.5. The label is under both, which is why
reading small print off a part is one of the things these models are worst at.

![A tray of 17 simulated screws under a 42-pixel grid and a 14-pixel grid, with the crowded patches shaded pink](../../images/language-and-multimodal-models/vision-language-models/counting-grid.svg)

Under the coarse grid 17 simulated screws fall into only 13 patches, with 3
patches holding more than one, while under the fine grid each screw gets its own.

This is the mechanism behind the fact that these models count badly. Counting
needs each thing to be countable separately, and when several share one patch the
stream holds no separate evidence for them, so the model guesses from a general
impression of crowdedness, which gets worse as the objects get smaller and the
count gets higher.

![The detector's box on a bottle, the coarsest box the patch grid can hold, and four bars showing the error on each side in millimetres](../../images/language-and-multimodal-models/vision-language-models/box-grain.svg)

A detector returns the bottle at pixels 266, 150, 406 and 470, while the best the
patch grid can hold is 252, 126, 420 and 504, which is out by 7, 12, 7 and 17
millimetres on the four sides.

That is why a detector is used alongside a vision-language model rather than
being replaced by it. The coarse box is snapped to the nearest patch edge, and
every one of its four sides is outside a 5-millimetre gripper tolerance.
[Detection and
segmentation](../09_models-that-see/02_detection-and-segmentation.md) describes
the models that give the exact box and the mask, and they remain the right tool
for anything measured in pixels, counted, or run many times a second.

---

## 7. What it gives a robot that a detector cannot

All of that makes it fair to ask what the model is for, and the answer is the
thing a detector has no way of producing: an answer about the scene in ordinary
words, including about things that no list of class names contains.

![Thirty things listed on a workbench, split into the 7 a 12-name class list covers and the 23 it does not](../../images/language-and-multimodal-models/vision-language-models/class-list.svg)

Of 30 things listed on one workbench, a detector trained on 12 class names has a
name for 7 and no name for the other 23, which is 77 per cent.

Read the second group carefully, because the point is not that those things are
exotic. Some are objects nobody put in the class list, such as a hex key or a
cable tie; some are ordinary objects described by their state, such as a cup with
a chip in its rim or a bottle with no label; and some are described by where they
are, such as the bottle nearest the edge. A class list has no way of holding a
description of the last two kinds at all. [Open-vocabulary
vision](../09_models-that-see/03_open-vocabulary-vision.md) closes part of the
gap by letting you name a class in words when you ask, but it still returns a box
for a phrase rather than an answer to a question.

![Six questions from a robot cell, with what a detector can do with each and what a vision-language model can do](../../images/language-and-multimodal-models/vision-language-models/questions.svg)

Of six questions a cell actually needs answered, the detector answers 2 and the
vision-language model answers 4, and the two sets barely overlap.

The first two rows are the detector's, asking how many cups are on the tray and
which pixel the cup rim is at. The last four are the other model's, asking
whether this cup is clean enough to put away, whether somebody has left a tool in
the cell, whether the bottle is upright or on its side, and why the gripper
cannot reach it. Nobody could write a class list that answers those four, because
each asks about a state or a relation or a reason rather than about the presence
of an object.

![A five-step pipeline from an operator's request through a vision-language model and a detector to a grasp pose in millimetres](../../images/language-and-multimodal-models/vision-language-models/handover.svg)

The useful arrangement passes words to words to pixels to millimetres, with each
part handing on the only thing it is good at producing.

The operator asks for the cup somebody has left on its side, the vision-language
model reads the picture and writes "the white cup, front left, lying down", an
open-vocabulary detector turns that phrase into one box in pixels, a grasp model
turns the box and the depth frame into a gripper pose in millimetres, and the arm
moves with no model anywhere inside its control loop. That arrangement costs four
parts and four places to go wrong, and the obvious alternative is one model that
takes the picture and the sentence and writes the joint commands itself, which is
[vision-language-action
models](../12_models-that-act/03_vision-language-action-models.md). That model is
built out of exactly the construction on this page, with the stream extended so
that some of the tokens the model writes are movements.

---

## 8. Where to read next

- [Reasoning and tool use](04_reasoning-and-tool-use.md) is the next page, and it
  explains what happens when the model writes its working out before the answer
  and calls a program to get facts right, and what that costs in time on a robot.
- [Detection and segmentation](../09_models-that-see/02_detection-and-segmentation.md)
  is the model that section 6 said stays, and it explains how a box and a mask
  are produced to the pixel.
- [Open-vocabulary vision](../09_models-that-see/03_open-vocabulary-vision.md)
  shows how a phrase written by a vision-language model is turned into a region
  of the picture.
- [Vision-language-action models](../12_models-that-act/03_vision-language-action-models.md)
  takes this construction one step further, so that the model writes the arm's
  movements as well as words.
- [Fine-tuning and adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md)
  explains freezing, unfreezing and catastrophic forgetting properly.
- [Vision-language models in the model catalogue](../../07_learned-models/07_language-models/02_most-used/02_vision-language-models.md)
  lists the real models of this kind, what they cost to run and where they fail
  on an arm.

---

## 9. Using it in Python

Section 2 worked the projector out by hand and section 3 counted the tokens a
picture costs. This section builds both in PyTorch, so that you can see the
construction really is one small layer and one insertion into a sequence. The
code makes up random numbers in place of a trained backbone and a trained
language model, but the shapes and the counts are the ones the page used.

```python
import torch
from torch import nn

PATCH, SIDE, V_WIDTH, L_WIDTH = 14, 224, 1024, 4096
n_patches = (SIDE // PATCH) ** 2                 # section 1: 16 x 16 patches

# section 2: the projector is one linear layer, nothing more
projector = nn.Linear(V_WIDTH, L_WIDTH)
print(n_patches)                                        # 256
print(sum(p.numel() for p in projector.parameters()))   # 4198400

patch_vectors = torch.randn(1, n_patches, V_WIDTH)      # what a backbone gives
picture_tokens = projector(patch_vectors)               # what the model reads
print(tuple(picture_tokens.shape))                      # (1, 256, 4096)

# section 3: put the picture tokens into the stream where the picture appeared
before = torch.randn(1, 38, L_WIDTH)             # the standing instructions
after = torch.randn(1, 17, L_WIDTH)              # the question in words
stream = torch.cat([before, picture_tokens, after], dim=1)
print(tuple(stream.shape))                       # (1, 311, 4096)

# section 5: tiling a 672 pixel picture into crops of 224, plus a thumbnail
picture = torch.randn(1, 3, 672, 672)
crops = picture.unfold(2, SIDE, SIDE).unfold(3, SIDE, SIDE)
crops = crops.reshape(1, 3, -1, SIDE, SIDE).permute(0, 2, 1, 3, 4)
print(crops.shape[1], (crops.shape[1] + 1) * n_patches)   # 9 2560
```

Every number printed there is one the page quoted: the projector's 4,198,400
parameters from section 2, a stream of 311 tokens before the model writes
anything, which is section 3's 38 plus 256 plus 17, and 9 crops which with a
thumbnail come to section 5's bill of 2,560 tokens. The one line of real work is
`projector(patch_vectors)`, and `unfold` is the ordinary tensor operation that
cuts a picture into tiles.

In a real build you would write none of this yourself, because Hugging Face's
`transformers` package ships these models whole, with the three parts already
joined and trained, and a processor object that takes a picture and a question
and produces the token stream, tiling and thumbnail included.

What you still have to decide is everything this page measured. You choose how
much resolution the job needs, which fixes the token bill and so the cost and the
latency of every call; you choose whether to keep a detector alongside the model,
which section 6 says you should whenever anything is measured in pixels or
counted; and if you fine-tune, you choose which parts are frozen in which stage,
because section 4 showed that getting that order wrong damages the reading half
in a way that is cheap to avoid and expensive to repair.
