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

**It answers the question actually asked.** This book asks which pixels belong
to which glass, and this model's output is one outline per object. Nothing has
to be converted, and no step has to find a seam in a joined region.

**It is fitted on the pictures it will be shown.** That is the single strongest
thing about it, and the thing its partner cannot claim. The domain gap is closed
by construction rather than left to hope.

**Its labels cost nothing.** The bench's id image gives exact masks for free, so
the usual reason not to fine-tune a model does not apply here.

**It has little to set by hand.** There is no grouping distance and no seam
threshold. Its two settings, the bar on the confidence number and the overlap
allowed before a candidate is discarded, are plain numbers with obvious
meanings, and neither is a length that has to be justified against the geometry
of the cell.

**It is one half of the cleanest comparison in this chapter**, and that is a
strength of the design rather than of the model.

Against that, three kinds of weakness.

**What it inherits from the model.** The outline is built coarsely and enlarged,
so the width carries an error that does not average away. That error is not
worse on the stemmed glass than on the others at the median, as the marking
above says, although the one glass the masks covered least well in the whole run
was a stemmed one. The masks are modal, so a partly hidden glass is
reported as a smaller glass in the wrong place. A completely hidden glass is
invisible to it, and no training can change that. The confidence number is about
the class and not about the mask, so a badly cut outline can still be scored
highly.

**What it owes to being trained.** A fine-tuned model becomes good at this cell
and worse elsewhere, so its weights are a narrow asset that has to be kept in
step with the cell. A small or uniform training set would teach it the
arrangements rather than the glasses, and only the test half of the arrangements
would reveal it. And its answer cannot explain itself: when solution 1's rules
are wrong you can print a number and see why, and when this model is wrong you
can look at the picture and guess.

**What it owes to the licence.** The AGPL reaches both the library and the
weights file fine-tuning produces, which is the one weakness here that no amount
of engineering removes.

## 2. The general ideas behind this

Nothing in this solution was invented for glassware. Every part of it is a
standard piece of modern practice, and each is worth knowing on its own,
including where it is normally the wrong tool.

### Transfer learning and fine-tuning

Take a model fitted on a large general task, keep its weights, reshape the last
layers for the new task, and continue training on the new data. It works because
the early layers of a vision model learn things common to all vision — edges,
corners, gradients, textures — and only the later layers learn things specific
to the original task. Yosinski and colleagues
([arXiv:1411.1792](https://arxiv.org/abs/1411.1792)) measured that directly,
showing how well a layer transfers falling away with depth.

It is normally the right choice whenever labelled data for the real task is
scarce, which is almost always. It is normally the wrong choice when labels are
free and plentiful **and** the new pictures look nothing like the borrowed ones,
because then the borrowed weights bring knowledge of a world you do not have
while also forcing your model to be the size somebody else chose. This cell sits
awkwardly between those two, since its labels are free and its pictures are
unlike photographs, which is exactly the argument [solution
2](../06_a-network-trained-from-scratch/01_what-it-is.md) makes and this solution deliberately takes the
other side of. For more, see [transfer
learning](https://en.wikipedia.org/wiki/Transfer_learning).

### Domain adaptation

A model fitted on one kind of data and used on another is working across a
**domain gap**, and the family of methods for closing it is called **domain
adaptation**. Fine-tuning on labelled data from the new domain is the simplest
member of that family and the strongest when such data exists.

It is right whenever you can obtain labelled examples of the real input, as
here. It is wrong, or rather unavailable, when you cannot, and then the harder
members of the family are needed: adapting with no labels at all, or
deliberately varying the training data so widely that the new domain falls
inside the range already covered. The second of those, **domain randomisation**,
is the usual answer when a model trained in a simulator has to work on real
pictures, and it is worth knowing because the problem it solves is the mirror
image of the one here.

### Single-class detection, against a closed vocabulary

A detector fitted with a fixed list of categories can only return names from
that list, which is called a **closed vocabulary**. Cutting the list to one
entry turns naming into pure finding, and the model's remaining job is to
separate instances.

One class is right when the question really is "where are the instances of this
one thing", which is what this book asks, and it is efficient, because none of
the model's capacity is spent telling categories apart. It is wrong when the
categories matter, and it then throws away information that was free: a model
that has to distinguish several classes can use the disagreement between them as
evidence, and a single-class model has no such signal. In this cell the kinds
are known in advance, so there is nothing to give up.

### Catastrophic forgetting

A network trained on a new task tends to lose what it knew of the old one,
because the weights that held the old knowledge are the same weights the new
training moves. The effect was first described for simple networks by McCloskey
and Cohen, and the modern treatment protects the weights that mattered most to
the old task (Kirkpatrick and colleagues,
[arXiv:1612.00796](https://arxiv.org/abs/1612.00796)).

It matters a great deal when a model must stay good at several things, which is
why continual learning is a field at all. It matters very little here, because
the model is wanted for one cell and nothing else, and this is the honest reason
the usual precautions against it are not taken: not that the effect is absent,
but that its cost in this project is zero.

### Overfitting and the held-out split

A model fitted on a finite set of examples can fit accidents of those examples
rather than the thing they are examples of. The standard defence is to divide
the data, fit on one part and measure on another, so that any such accident
shows as a gap between the two scores.

It is the right practice everywhere and there is no case against it. Its usual
difficulty is that data is scarce, so dividing it hurts. That difficulty does
not arise here, because arrangements are rendered rather than collected and more
of them cost only time. For more, see
[overfitting](https://en.wikipedia.org/wiki/Overfitting).

### Non-maximum suppression

When many overlapping claims describe the same thing, sort them by confidence,
keep the best, discard everything overlapping it too heavily, and repeat on what
is left. The procedure appears in every detector, because every detector
produces more candidates than there are objects. Its only setting is the overlap
allowed, and because that is a ratio of areas rather than a distance, it does
not have to be justified against the size of anything in the room.

It is right wherever a detector's candidates cluster on one object. It is wrong
without care in crowded scenes, because it cannot tell duplication from genuine
overlap, and this cell is one of the awkward cases: the outward throw from the
top can push one glass's outline right across another's. A softer variant, which
reduces an overlapping candidate's score rather than deleting it, is
**Soft-NMS** (Bodla and colleagues,
[arXiv:1704.04503](https://arxiv.org/abs/1704.04503)), and it exists for exactly
that difficulty.

## 3. Where it sits among the other five

[The six solutions](../04_the-six-solutions/01_how-the-six-compare.md) form a ladder, ordered by how much of them was
fitted in this cell, and this one stands near the top of it.

Against [solution 3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md), there is nothing to compare except
training, and that is the point. Same library, same model, same starting
weights, same input, same output, same marking. The single class that replaces
the borrowed category list comes with the training rather than beside it, so it
is part of what is being measured and not a second variable. Whatever separates
the two scores is what fine-tuning bought, and nothing else can be blamed for
it. If this document is read for one reason, it should be that one.

Against [solution 1](../05_rules-on-the-table/01_what-it-is.md), the comparison is model against
rules. Solution 1 is a page of arithmetic that explains its own failures and
needs no training set, no weights file and no licence. This solution needs all
three and answers the merge by the shape of its output rather than by a rule
somebody had to get right. On any day the depth readings are good, the rules are
better in almost every way that is not accuracy.

Against [solution 2](../06_a-network-trained-from-scratch/01_what-it-is.md), the comparison is borrowing
against building. Solution 2 fits a small network here from random numbers, so
the project owns every number in it and can regenerate them, and in exchange it
has to learn the general machinery of vision from this cell's pictures alone.
This solution borrows that machinery and adjusts it, so it is trainable in much
less time, and the price is a large downloaded file the project cannot reproduce
and a licence attached to it.

Against [solution 5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md), the comparison is how much to
fit. Solution 5 borrows a larger model untouched and fits only a small keeper
that decides which of its outlines are glasses, which needs the least training
data of any learned solution here and leaves its domain gap wide open, as
solution 3 also does, because nothing in the borrowed weights is ever adjusted
to this cell's pictures. This solution fits the whole model, so its weights have
actually seen the pictures they will be asked about.

Against [solution 6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md), the comparison is architecture.
Both are fine-tuned here on this cell's own pictures with one class and free
labels, so the training is held still and the model is what differs. That makes
the pair a test of whether the choice of architecture still matters once both
have been trained on the job, which is the natural question to ask after this
solution's own pair has answered what training is worth at all.

Read as a ladder, the six measure what each increment of fitting buys. This
solution is the rung where all of the fitting happens on a borrowed model, and
its partner one rung below is the rung where none of it does.

← [What it needs](05_what-it-needs.md) · [SAM 2 with a keeper — what it is](../09_a-foundation-model-with-a-keeper/01_what-it-is.md) →
