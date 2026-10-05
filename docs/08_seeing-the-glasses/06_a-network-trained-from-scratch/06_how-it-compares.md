# A network trained here from scratch — how it compares

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

**It has no domain gap.** Everything it knows came from this cell's own
pictures, so nothing it learned has to be transferred from a world it will
never see. This is the reason it is the control for the comparison, and it is
the one strength no borrowed model can claim.

**It separates glasses that are joined in the picture.** Nothing has to find a
boundary, so nothing can get a boundary wrong, and the separation survives
cases where there is no gap anywhere to find.

**It is unusually good at a partly hidden glass.** A crescent of surviving
pixels still votes towards the right middle, and the votes do not have to be
joined to each other or to make a recognisable shape.

**Its doubt costs nothing.** How many votes a pile holds is a confidence per
glass, and how far its votes sit from its own peak would be a second one. Both
are measurements of the votes rather than the network's opinion of itself,
which is a better kind of warning than most learned methods give; the count is
the one the code measures.

**It is blind to a glass hidden completely.** No pixels means no votes, which
means no pile, no spread and no short count. This is a fact about the input
rather than about the model.

**It needs a training set and a training run before it answers anything.** The
borrowed model that changes nothing can be pointed at a picture on the day it
is downloaded. This one cannot, and that gap in setup cost is real.

**Its answer cannot explain itself.** When a fitted circle is wrong you can
print one number and see why. When a network is wrong you can look at the
picture and guess. The arithmetic wrapped around it is what makes that
tolerable.

**Its weights are a second copy of the cell**, and keeping them in step with
the first copy is a maintenance job rules on the table simply does not
have.

## 2. The general ideas behind this

Every part of this is standard, and most of the parts are not new. Two things
here are unusual: fitting from a random start on rendered pictures rather than
fine-tuning something large, and asking one network a question about classes
and a question about instances from the same shared body.

### Semantic segmentation — a class label at every pixel

Rather than a box round an object, produce a label for every pixel. The idea
became practical with **fully convolutional networks** (Long, Shelhamer and
Darrell, [arXiv:1411.4038](https://arxiv.org/abs/1411.4038)), which replaced a
classifier's final layers with convolutions so that a picture of any size maps
to a label map of the same size.

It is used wherever the extent of a thing matters more than a box round it,
such as medical imaging, aerial pictures and industrial inspection. It is
rarely right for counting or separating individuals, because a class label has
nowhere to record which object a pixel belongs to, and that is the limitation
the second head here exists to remove. For more, see [image
segmentation](https://en.wikipedia.org/wiki/Image_segmentation).

### The encoder–decoder with skip connections

Halve the resolution repeatedly while widening the channels, then enlarge it
back, copying each level on the way down across to the matching level on the
way up so that detail lost going down is available coming back. That is the
**U-Net** (Ronneberger, Fischer and Brox,
[arXiv:1505.04597](https://arxiv.org/abs/1505.04597)), designed for biomedical
images with very few training examples, which is exactly why it suits a small
rendered training set.

It remains the default for a small segmentation problem. It is rarely right for
problems needing broad understanding of a scene or many classes, where a large
pre-trained network earns its size, because a small network knows only what its
receptive field and its training set contained.

### Overlap losses — scoring the shape rather than the pixel count

Cross entropy averages over pixels, so on a picture that is mostly background a
model can score well by predicting background everywhere. **Dice** and
**intersection over union** losses score the overlap between the predicted and
the true regions instead, and they are usually added to cross entropy rather
than used in place of it (Milletari and colleagues,
[arXiv:1606.04797](https://arxiv.org/abs/1606.04797)).

They are used wherever one class is far rarer than the other, which covers most
medical and industrial segmentation. They are rarely enough on their own,
because an overlap score says nothing about how confident the individual pixels
were, which is information a feedback loop can use.

### The Hough transform — local evidence for a global claim

A single edge pixel cannot say where a shape is, but it can vote for every
shape that would explain it; add up the votes and the peaks are the shapes
really present. Hough's 1962 patent did this for straight lines, and the
**generalised Hough transform** (Ballard, 1981) extended it to any shape by
replacing the equation with a table of offsets.

It is used for finding shapes in noisy, cluttered pictures where much of the
outline is missing. Voting is naturally robust to things being hidden, because
the visible part still votes correctly. It is rarely right for shapes with many
parameters, because the table of votes grows explosively with them. For more,
see the [Hough transform](https://en.wikipedia.org/wiki/Hough_transform).

### Learned voting — replacing the table of offsets with a model

**Hough forests** (Gall and Lempitsky, 2009) first replaced the hand-built
table of offsets with a learned one. The neural descendants apply the same
structure to pixels and points: **VoteNet**
([arXiv:1904.09664](https://arxiv.org/abs/1904.09664)) has points from a depth
sensor vote for object middles, and **PVNet**
([arXiv:1812.11788](https://arxiv.org/abs/1812.11788)) has pixels vote for
landmark points, specifically because voting survives things being hidden.

These are used for finding objects in cluttered scenes and bin picking, where a
method needing the whole object visible fails and a method needing only a
fraction does not. They are rarely right for objects with no well-defined
middle, or where the offsets are large compared with the picture, because then
the number the network has to predict grows and the votes scatter.

### Mean shift — finding peaks without being told how many

Slide a window to the average of the points inside it and repeat until it stops
moving; every starting point that ends in the same place belongs to one peak
(Comaniciu and Meer, 2002). Unlike methods that divide data into a fixed number
of groups, it does not need the count in advance, which is the whole point
here, because the number of groups is the answer.

It is used for finding peaks when the count is unknown, such as tracking and
colour segmentation. It is rarely right for data with many dimensions, where it
is slow and the window size becomes impossible to choose, and it is poor for
groups of very different densities, where one window size cannot serve both.
For more, see [mean shift](https://en.wikipedia.org/wiki/Mean_shift).

### Self-supervised learning — labels from the structure of the data

Rather than annotate anything, construct a task whose answer is already implied
by the data, so that the supervision is free and unlimited. Rung two is this
idea with the arm's own encoders as the generator of labels.

It is used where unlabelled data is abundant and labels are expensive, and in
robotics, where a robot's sense of its own position is a label generator that
never tires. It is rarely right where the invented task can be solved by a
shortcut that does not need the understanding you wanted, and designing a task
with no shortcut is the hard part of the field. For more, see [self-supervised
learning](https://en.wikipedia.org/wiki/Self-supervised_learning).

### Geometry as supervision, and depth without depth labels

If a camera's movement between two pictures is known, then a point's position
in the first picture determines where it must appear in the second, given its
depth. That is the **epipolar constraint**, and it turns a depth guess into a
checkable prediction. **SfMLearner** (Zhou and colleagues,
[arXiv:1704.07813](https://arxiv.org/abs/1704.07813)) built a training recipe
on it with no depth labels at all, and **Monodepth2** (Godard and colleagues,
[arXiv:1806.01260](https://arxiv.org/abs/1806.01260)) fixed most of its
practical failures.

Those methods have to **estimate** the camera's movement, and that estimate is
where a large part of their error lives. In this cell the movement is not
estimated but commanded, so the hardest half of that literature's problem does
not exist here. The approach is rarely right for surfaces without texture or
for scenes where the objects move between the two pictures, which breaks the
still-scene assumption entirely. For more, see [structure from
motion](https://en.wikipedia.org/wiki/Structure_from_motion).

### Grouping by shared motion — common fate

Points on one rigid surface move together in the picture and points on a
different surface at a different distance do not. The Gestalt psychologists
called that **common fate**: a flock of birds is one flock because the birds
turn together. It is one of the very few grouping cues that needs no model of
appearance at all, which is why it works on two identical glasses.

It is used for video segmentation and tracking, and anywhere objects are hard
to tell apart by how they look. It is rarely right where nothing moves relative
to anything else, which is exactly why rung two is weak from the top: two rims
at nearly the same distance have almost no relative movement to group by.

### Contrastive training — turning "these belong together" into a loss

Pull together the outputs for things that belong together and push apart the
outputs for things that do not. **SimCLR** (Chen and colleagues,
[arXiv:2002.05709](https://arxiv.org/abs/2002.05709)) and **MoCo** (He and
colleagues, [arXiv:1911.05722](https://arxiv.org/abs/1911.05722)) are the
standard references, and the related idea of giving each pixel an identity code
and grouping the codes is **associative embedding** (Newell and colleagues,
[arXiv:1611.05424](https://arxiv.org/abs/1611.05424)).

It is used wherever pairs that belong together are easy to construct but
categories are not, which is most of self-supervised vision. It is rarely
enough on its own when the count of groups matters, because an embedding says
which things belong together and never how many groups there are, and that is
exactly the gap the checks after the network fill here.

### Training from scratch against fine-tuning a large model

The last idea is the choice this whole document turns on. Fine-tuning wins
whenever labels are scarce, which is almost always. Training from scratch wins
in the narrow case where labels are free, the problem is small, and the borrowed
weights would bring knowledge of a world you do not have. This cell is that
narrow case, and it is worth noticing how rare that is rather than generalising
from it.

## 3. Where it sits among the other five

This solution is the one with nothing borrowed in it, so its place in the
comparison is fixed by that and not by its score.

Against [rules on the table](../05_rules-on-the-table/01_what-it-is.md), the comparison is
whether a fitted grouping rule beats a written one. The written rule is a page
of arithmetic that explains its own failures and needs no training set, and on
any day the depth readings work it is the easier tool. This solution earns its
place where no single written rule can be made to work, which is where two
glasses leave no gap anywhere to find.

Against the four that borrow weights, the comparison is the one this solution
exists for. [YOLO as it downloads](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md) borrows everything and
fits nothing. [YOLO fine-tuned](../08_the-same-model-fine-tuned/01_what-it-is.md) and [RF-DETR
fine-tuned](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md) borrow a starting point and then fit on
this cell's pictures as this solution does. [SAM 2 with a
keeper](../09_a-foundation-model-with-a-keeper/01_what-it-is.md) borrows a large model and fits only a small
decider on top of it. Every one of those four carries a domain gap of unknown
size, and this solution carries none, so **the distance between this line and
those four is the measurement of what borrowing was worth**. If the borrowed
models do no better than a network fitted here from random numbers, then their
size and their licences bought nothing in this cell.

One pairing is sharper than the rest and is worth knowing while reading this
one. [YOLO as it downloads](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md) and [YOLO
fine-tuned](../08_the-same-model-fine-tuned/01_what-it-is.md) are the same model from the same library
with the same starting weights, and the only difference between them is whether
it was trained on this cell's pictures. The gap between those two measures what
training bought. The gap between this solution and the pair of them measures
what the starting weights bought.

And what this solution cannot do, on any day, is notice a glass that is absent
from the picture. That failure is answered by geometry rather than by
appearance, in [looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which
all six share. This solution contributes the masks that argument starts from,
and none of the argument.

← [A network trained here from scratch — what it needs](05_what-it-needs.md) · [A borrowed model, as it downloads — what it is](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md) →
