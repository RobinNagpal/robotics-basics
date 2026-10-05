# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas it is built from so that
you can read about them outside this book, and places it beside the other five.
By the end you will know when this is the solution to reach for, and when it is
the wrong one.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

**It answers the question actually asked.** The problem asks which pixels belong
to which glass, and the output is one mask per glass. Every method in this set
that answers a different question has to add machinery to convert its answer,
and every piece of that machinery is somewhere a mistake can be made.

**It separates glasses whose outlines join, and nothing has to decide where to
cut.** Two glasses that meet in the picture occupy two slots, so there is no
joined region and nothing to divide.

**It has one fewer number to justify than the older shape does.** Because the
slots are matched to the glasses one to one during training, there is no overlap
amount deciding when two claims are duplicates, and so no setting that has to be
generous enough to survive the worst legitimate overlap this cell can produce.
The score threshold remains, and it is a plain number with an obvious meaning
rather than a length that has to be defended against the geometry of the cell.

**It is the only one of the six that can be asked for the part of a glass nobody
saw**, and that is a consequence of its shape rather than a feature bolted on.
With no rectangle round each mask, the completion is a change of target and
nothing else.

**Its licence is permissive**, which matters when the same model has to be
shipped inside something else.

**Its second rung is the easiest thing in this set to implement wrongly.** If
the asserted pixels are fed into the shared arithmetic instead of being named
and excluded, the answer gets worse in exactly the way the rung exists to
prevent, and nothing complains: the mask looks better, the footprint stays
round, and the width stays inside the range the kind allows.

**Models of this family are known to want patience in training.** The one-to-one
matching has to settle before the slots stop changing their minds about which
glass each of them is responsible for, and this cell's pictures are not the kind
of picture the borrowed weights were fitted on, so the fine-tune has a domain
gap to close as well. That is a cost in training time rather than in
correctness, because the pictures the model is fitted on are the pictures it
will be run on.

**It is blind to a glass hidden completely**, and so is its second rung. No
pixels means no slot filled, no low score and nothing to check. That is a fact
about the input rather than about the model.

**Its answer cannot explain itself.** When a page of arithmetic is wrong you can
print one number and see why; when this model is wrong you can look at the
picture and guess. Every quantity inside it is a block of numbers with no
meaning anybody assigned, so working out a failure is a matter of examples
rather than of reasoning, and the prescribed checks on the width and on where
the assertion lies are what have to make that tolerable.

**Its weights are a second copy of the world, and most of them came from
somewhere else.** The code says what the cell is; the weights say what the cell
looked like when they were fitted, on top of what a large collection of ordinary
pictures looked like. Keeping that in step is a maintenance job the arithmetic
solution does not have, and the borrowed part cannot be regenerated here at all.

## 2. The general ideas behind this

Nothing here was invented for glassware. Every part of it is a standard piece of
the modern detection toolkit, and what is specific to this cell is only the
choice of one class, the source of the labels, the grey pictures shaded from
depth, and the decision to ask for whole silhouettes.

### Detection as set prediction

The general idea is to make a detector output a **set** of a fixed size and to
train it by matching that set against the true objects one to one, so that
duplicate answers are trained away instead of pruned away. **DETR** (Carion and
colleagues, [arXiv:2005.12872](https://arxiv.org/abs/2005.12872)) did this
first, with a fixed number of queries, a transformer reading the whole picture,
and a one-to-one matching computed by the **Hungarian algorithm** (Kuhn, *Naval
Research Logistics Quarterly*, 1955), which finds the cheapest complete pairing
between two sets and is a standard piece of combinatorial optimisation rather
than anything to do with vision.

It is used wherever a clean list of objects is wanted without a pruning step,
and it suits crowded scenes, because two genuinely overlapping objects are not
competing for one answer. It is rarely the right choice when the number of
objects in a picture can exceed the number of slots, since the slots are fixed
and the surplus objects simply have nowhere to go, and it is a poor choice when
training time is the binding constraint, because the matching takes a while to
settle. For more, see [object
detection](https://en.wikipedia.org/wiki/Object_detection).

### Attending to a few places rather than everywhere

Reading a whole picture with every query attending to every position is
expensive, and the standard answer is to have each query sample a small number
of positions it chooses rather than all of them. **Deformable DETR** (Zhu and
colleagues, [arXiv:2010.04159](https://arxiv.org/abs/2010.04159)) introduced
that, together with running it over several scales at once, which is what made
this family practical and sped up the training it is known for needing. Later
work in the line, including **DINO** (Zhang and colleagues,
[arXiv:2203.03605](https://arxiv.org/abs/2203.03605)) and the real-time variants
after it, is largely about making the matching settle faster and the whole model
run in a fixed small time.

It is used in nearly every current transformer detector. It is rarely necessary
when every object is about the same size in every picture, where a single scale
and simpler attention do the job for less arithmetic. That is not this cell,
where the same glass covers a small patch of the picture from the top and much
of the frame from the side.

### A mask per query, over the whole picture

The general idea is to stop painting masks inside boxes. Give each query a short
description of the object it found, produce a description of every pixel, and
take the mask to be the pixels whose description matches the query's.
**MaskFormer** and **Mask2Former** (Cheng and colleagues,
[arXiv:2107.06278](https://arxiv.org/abs/2107.06278) and
[arXiv:2112.01527](https://arxiv.org/abs/2112.01527)) set out that formulation
and showed that one model in this shape answers segmentation by class, by
instance and by both at once, differing only in the target it is trained
against.

It is used wherever objects of one class touch or overlap and have to be
reported separately, and it is the right shape whenever a mask may need to reach
past where the evidence for the object stops, which is exactly why it is chosen
here. It is rarely right when a single map of classes is all that is wanted,
because the queries are then pure cost.

### Transfer learning and fine-tuning

Take a model fitted on a large general task, keep its weights, change the last
part to suit the new task, and continue training on the new data. It works
because the early parts of a vision model learn things common to all vision —
edges, corners, gradients, textures — and only the later parts learn things
specific to the original task. Yosinski and colleagues
([arXiv:1411.1792](https://arxiv.org/abs/1411.1792)) measured that directly,
showing how much transfers and how it falls away with depth. The pictures such
weights are usually fitted on are collections like COCO (Lin and colleagues,
[arXiv:1405.0312](https://arxiv.org/abs/1405.0312)), and a backbone may instead
arrive fitted without labels at all, as in **DINOv2** (Oquab and colleagues,
[arXiv:2304.07193](https://arxiv.org/abs/2304.07193)), which is the route recent
detectors in this family favour.

It is used whenever labelled data for the real task is scarce, which is almost
always. It is rarely the right choice when labels are free and plentiful and the
new pictures look nothing like the borrowed ones, because the borrowed weights
then bring knowledge of a world you do not have while also fixing your model at
the size somebody else chose. That is the argument [a network trained from
scratch](../06_a-network-trained-from-scratch/01_what-it-is.md) makes, and this solution takes the other side
of it on purpose. For more, see [transfer
learning](https://en.wikipedia.org/wiki/Transfer_learning).

### Amodal segmentation

The general idea is to mark the whole extent of an object including the part
another object covers, rather than only the visible part. **Amodal instance
segmentation** was posed as a task by Li and Malik
([arXiv:1604.08202](https://arxiv.org/abs/1604.08202)), with an earlier
formulation over whole scenes by Zhu and colleagues
([arXiv:1509.01329](https://arxiv.org/abs/1509.01329)), and later work predicts
the visible and the whole mask side by side so that the hidden part is available
on its own (Follmann and colleagues,
[arXiv:1804.08864](https://arxiv.org/abs/1804.08864)).

It is used in robot picking, in driving, and anywhere a partly covered object
has to be reasoned about as a whole, and it is right whenever the step after the
segmenter assumes a whole object, which is exactly the case here. It is rarely
right on real photographs without care, because the label has to be drawn
through a place nobody can see, so two careful annotators disagree with no way
to settle who was right, and a model trained on such labels is fitted partly to
the annotators' guesses. **None of that applies in a simulator**, which is why
this rung is cheap here: the bench can render the arrangement again with the
other glasses taken away, and the mask that comes back is the whole silhouette
exactly, with no guessing in it. For more, see [image
segmentation](https://en.wikipedia.org/wiki/Image_segmentation).

![The whole silhouette is asked of the simulator rather than of a person: render the scene once for the pixels the camera sees of each glass, render the covered glass again with the others taken away for the shape it would have had, and the difference between the two is the hidden part.](../../images/seeing-the-glasses/a-transformer-segmenter-fine-tuned/10-labels-for-free.png)

## 3. Where it sits among the other five

This solution sits at the far end of the ladder, with everything fitted here and
the most modern architecture under it. Each comparison below holds something
still and changes one thing, which is what makes the set worth having.

Against [the same YOLO fine-tuned here](../08_the-same-model-fine-tuned/01_what-it-is.md), the comparison
is the sharpest in the set after solutions 3 and 4, and it is the reason this
solution exists. Both are fitted the same way, on the same pictures, with the
same single class and the same free labels, so **the amount of fitting is held
still and the architecture is what changes**. The gap between those two is
therefore about design rather than about training. Two differences of design are
worth naming. The first is the one-to-one matching, which removes the overlap
amount deciding when two claims are duplicates. The second is that there is no
rectangle round each mask, which is what lets this solution be asked for a whole
silhouette while the other cannot be without reworking what its rectangles are
trained to cover. The licence differs too, and it is not a small thing: that
solution is covered by the AGPL and this one by Apache 2.0.

Against [YOLO as it downloads](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md), two things change at once,
so the comparison is coarser. That solution is fitted nowhere and this one is
fitted here, and the architectures differ as well. The pair worth reading for
what training alone buys is solutions 3 and 4, which share a library, a model
and a set of starting weights and differ only in whether the model was trained
on this cell's pictures. This solution and solution 4 are the pair worth reading
for what architecture buys once both are trained.

Against [SAM 2 with a keeper](../09_a-foundation-model-with-a-keeper/01_what-it-is.md), the trade runs the
other way round. That solution borrows more and fits less: its segmenter is used
exactly as it downloads, and the only thing fitted is a small decision about
which of its regions are glasses. That needs almost no training data and leaves
its domain gap wide open, as solution 3 also does, because nothing in the
borrowed weights is ever adjusted to the pictures this cell renders. This
solution fits the whole model, so its weights have actually seen the pictures it
will be run on, which is why its domain gap is expected to cost accuracy and
training time rather than correctness. If the question is how little training
one can get away with, that solution wins; if it is which of them has met this
cell's pictures, this one does.

Against [a network trained from scratch](../06_a-network-trained-from-scratch/01_what-it-is.md), both fit
everything here and the difference is where the numbers start and what the
output is. That solution begins from random numbers and owns every weight, which
means a small file that can be kept beside the code and regenerated without
thinking about it. It reaches separate glasses by a step outside the network
rather than from the network's own output: its network answers two questions at
every pixel, whether the pixel is glass and which way the middle of that pixel's
own glass lies, and the glasses are then the piles that those votes form, which
are counted afterwards. So both solutions hold separate objects, and what
differs is where the separating happens. This solution asks the model for
instances and gets them with nothing counted afterwards, in exchange for a large
downloaded file it cannot regenerate. So the choice is not "borrowed is better";
it is capability now against a model the project fully owns.

Against [rules on the table](../05_rules-on-the-table/01_what-it-is.md), the comparison is the
one every fitted solution here faces, and it is not flattering. On any day the
depth readings work, that solution is better in almost every way that matters:
it is a page of arithmetic rather than a file of weights, it needs no training
set, it explains its own failures, and it can say where it has not looked. This
solution needs depth too, because depth shaded into grey is the only picture the
renderer makes, so it buys no independence from the depth camera. What it does
buy is that no length has to be chosen and defended, that two joined glasses
were never one region, and that the part of a glass nobody saw can be asked for
at all.

And the thing none of the six can do is notice a glass absent from the picture.
That is answered by geometry rather than by appearance, in [looking again at
what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which all six point at. This solution
moves the boundary at which hiding becomes complete further out than the other
five, and it does not remove it. The whole comparison, with all six side by
side, is in [the overview](../04_the-six-solutions/01_how-the-six-compare.md).

← [What it needs](05_what-it-needs.md) · [The six solutions side by side](../11_the-results.md) →
