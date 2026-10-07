# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

Marked by [the examiner](../03_the-examiner/01_the-examiner.md) over five blocks
of 20 held-out arrangements, it reports 6.4 glasses per 100 on the layouts the
cell's own rule spaces, and 2.1 per 100 when the glasses are crowded closer than
that rule allows. Both are the worst in the book by a wide margin, and both are
the least settled numbers in it: the five blocks run from 2.0 to 11.9 per 100 on
the spaced layouts, and from 0.0 to 4.2 on the crowded ones, where one whole
block of 20 arrangements produced **no glass at all**. The spread does not change
what a reader should conclude, because the best block is still far below the
worst block of any other solution. [The results](../11_the-results.md) sets
those two rows beside the other five.

![Found per 100 for the borrowed model and for the same model fine-tuned, on spaced and on crowded arrangements, with each of the five blocks of 20 held-out arrangements drawn as its own mark: the block-to-block spread of either solution is small beside the distance between them.](../../images/seeing-the-glasses/a-borrowed-model-as-it-downloads/07-the-pair-block-by-block.png)

The strengths all come from the same source, which is that nothing is fitted.

There is nothing to collect, nothing to train and nothing to keep in step with
the cell, so this solution was tried in an afternoon and gave this chapter a
reading on what a borrowed model is worth before anybody invested in labels. It
attacks the merge directly, because a model that finds objects returns one
outline per object rather than one per connected shape. It needs no graphics card
of its own. And it is a genuine upper bound on convenience: no other solution
here can be cheaper, so if this one had been good enough, several of the others
would not need to exist.

Two measurements are worth keeping even though the headline is a failure.
**Nothing was merged, split or false, in any block.** Every glass this solution
reported was a real glass, so it fails by silence rather than by inventing
anything. And on the glasses it did find, the masks were good: on the two kinds
with no stem the block medians cover 99.8 to 100.0 per cent of the glass. The
model's trouble is not that it outlines badly. It is that it almost never offers
an outline to be kept.

The weaknesses divide into what the borrowing costs and what it cannot be asked
to do.

**What the borrowing costs is the naming, and the naming is what decided this.**
The names are somebody else's categories, and shown a grey picture shaded from
depth the model reaches for a sports ball or a frisbee rather than a cup. Over
the 36 pictures of the naming measurement in [how it works](03_how-it-works.md),
five of 87 named objects carried a name the filter accepts. Beside that, the
other two costs are small: the outline is built coarsely and then enlarged, so a
width carries an error that does not average away, and the confidence number is
uncalibrated on these pictures, so any bar on it is a hand-set knob.

What it cannot be asked to do is anything that needs fitting. The outlines mark
only pixels where the camera actually saw the object, so a glass standing partly
behind another is read as a smaller glass in the wrong place, and the repair for
that is to train a model to return the whole silhouette, which this solution
cannot do because it trains nothing. A completely hidden glass is invisible to
it, and no model can find what left no pixels. Neither limit has a fix inside
this solution, and the project's usual answer applies to both: report the doubt
rather than the guess, and send the arm to look again.

The honest position is therefore that this is the first thing to run and not the
thing carried into a finished product. Its value is the comparison it makes
possible rather than the accuracy it delivers.

## 2. The general ideas behind this

Four named ideas sit under this solution, and each is worth knowing in its own
right, including where it is normally the wrong tool.

### Zero-shot transfer — using a model on a task it was never fitted for

A model is used **zero-shot** when it is applied to a task with no examples of
that task at all, relying entirely on what it learned elsewhere. It works when
the new task is genuinely a special case of the old one. That sounded true here,
because finding drinking vessels standing on a table is something the borrowed
model's training set contained, and it was not true, because the pictures are
not photographs and a glass in them is not a photographed glass. The lesson is
that "the same objects" is not enough; the inputs have to be the same kind of
input as well.

It is normally the right first move whenever a general model exists and labels
are expensive, because it costs an afternoon and tells you how hard your problem
really is. It is normally wrong as a final answer when the input differs visibly
from what the model was fitted on, which is the case here, and wrong whenever
the categories you need are finer than the categories the model knows, which is
also the case here.

### Closed-vocabulary detection — a fixed list of things that can be named

A model of this kind can only ever return names from a list fixed when it was
fitted. That is called a **closed vocabulary**, and it is the structural reason
the names here can be a filter and nothing more: the list cannot contain this
cell's four kinds, because it was written without this cell in view. It is also
why the failure took the form it did. The model had no way to say "a round thing
I have not met", so it said sports ball.

A closed vocabulary is right when your categories really are on the list, and
then it is efficient, predictable and easy to reason about. It is wrong when
they are not, and the two usual repairs are to continue the model's training on
your own categories, which is [solution 4](../08_the-same-model-fine-tuned/01_what-it-is.md), or to use a
model that accepts a description in words instead of a fixed list, which removes
the restriction at the cost of being markedly less reliable about outlines.

### One-stage detect-and-segment, against propose-then-classify

This solution's model does the finding and the naming together in a single pass.
The alternative arrangement, used by [solution 5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md),
proposes regions first with one model and decides afterwards with a second which
of them to keep.

Doing both at once is faster and simpler, and it is the right choice when the
categories you want are the ones the model names. Separating the two is the
right choice when they are not, because the proposing half survives a domain gap
much better than the naming half does: a shape is a shape everywhere, while what
counts as a cup is a judgement that was fitted to somebody else's data. This
cell is the clearest possible demonstration of that split. The finding half of
this model works; the naming half is what failed.

### Calibration under changed input

A model's confidence is fitted, without anybody intending it, on the data the
model was trained and checked on, so moving the model to different data breaks
the calibration while often leaving the ranking usable. Knowing which of those
two properties you depend on is the practical point.

Trusting the ranking is usually safe, and it is what this solution does.
Trusting the numbers requires a repair, which is a small correction fitted on
data where the answer is known, and that repair is cheap and almost always worth
doing before a bar on a confidence number is allowed to decide anything that
matters.

## 3. Where it sits among the other five

This solution is one end of a line that runs through three of the others, and
the line is the useful way to see it.

At this end, nothing is fitted in the cell and the borrowed model's own
vocabulary picks the glasses out. One step along, [solution
5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md) borrows a model that outlines without naming and
fits a small keeper here to pick the glasses, so a little is fitted and the part
that transfers worst is the part replaced. Another step along, [solution
4](../08_the-same-model-fine-tuned/01_what-it-is.md) continues this very model's training on this cell's
own pictures, so the finding is borrowed and then adjusted, and [solution
6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md) does the same for a different architecture. At the
far end, [solution 2](../06_a-network-trained-from-scratch/01_what-it-is.md) fits everything here and borrows
nothing, and [solution 1](../05_rules-on-the-table/01_what-it-is.md) sits outside the line
altogether, with no model and no fitting of any kind.

Read in that order, [the six solutions](../04_the-six-solutions/01_how-the-six-compare.md) measure what each increment
of fitting buys, and this one is the baseline the others are read against.

One of those comparisons is sharper than the rest, and it is the reason this
document and the next one should be read together. **Solution 4 is this same
model, from this same library, starting from these same downloaded weights, with
its training continued on this cell's own pictures.** The examiner holds the input,
the output and the marking still for both. One further thing changes with the
training, and it is honest to name it: solution 4 replaces the borrowed list of
category names with the single class "glass", because a model cannot be trained
towards this cell's own labels while still being asked which everyday object it
is looking at. That change comes with the training rather than beside it, so
nothing varies between the pair that the training did not bring. The gap between
their scores is 6.4 per 100 against 99.4, and it is a measurement of what the
training bought and of nothing else. No other pair in this chapter is that clean,
and that is the reason this solution was worth building even though its own score
is the worst in the book.

← [What it needs](05_what-it-needs.md) · [The same model, fine-tuned here — what it is](../08_the-same-model-fine-tuned/01_what-it-is.md) →
