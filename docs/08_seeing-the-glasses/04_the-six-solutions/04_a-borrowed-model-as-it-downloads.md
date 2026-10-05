# A borrowed model, as it downloads

This page describes the third of the six solutions in about seven minutes of
reading. It is the cheapest of the six to set up, because it fits nothing at
all: a model that somebody else trained on photographs of everyday objects is
downloaded, pointed at this cell's pictures, and asked which things it can see.
By the end of this page you will know what kind of model it is, why its own
vocabulary is used as a filter and never as an answer, what the licence costs,
what it scored on the shared test bench, and why its score is the most useful
failure in the book. The full treatment is in [the chapter on this
solution](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md), which is
about half an hour of reading and the shortest of the six.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored on the bench](#4-what-it-scored-on-the-bench)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

The model is Ultralytics YOLO26-seg, and it performs **instance
segmentation**, which means that for each separate object it believes it has
found it returns four things: a rectangle round the object, a name taken from a
fixed list of everyday categories, a number saying how sure it is, and an
outline of the pixels inside that rectangle which belong to the object. The
outline is what this book asks for, so the model's output needs no conversion.

The important word is **borrowed**. The weights were fitted by somebody else, on
somebody else's photographs, for somebody else's purpose, and they are used here
exactly as they download. Not one number in this solution came from this
project's own data. That is what makes it worth building: it is the upper bound
on convenience, so if it were good enough, several of the other five would not
need to exist.

It is also one half of the sharpest comparison in the book. [The same model,
fine-tuned](05_the-same-model-fine-tuned.md) is this same library, this same
model and these same downloaded weights, with training on this cell's pictures
added. Nothing else varies between the two, so whatever separates their scores
is what training bought and nothing else can be blamed for it.

## 2. How it works

There are only three steps, which is the point of this solution.

**The picture goes in as it is.** The renderer produces a grey picture shaded
from the depth readings, and that picture is handed to the model unchanged. A
survey is three pictures from three overlapping camera stations, and the model
is asked about each one on its own, which is the bench's arrangement for all six
solutions rather than a choice this one makes.

**The model returns a list of objects.** For each one it gives the rectangle,
the name, the confidence number and the outline.

**The names are used as a filter and then thrown away.** The design keeps the
outlines whose name is a drinking vessel, such as a cup or a wine glass, and
drops everything else the model named. The names are then discarded, because
they are somebody else's categories: they are useful for separating the glasses
from the table and nothing else, and in particular they never say which *kind*
of glass is on the table. The kind is already known from the problem statement.

The kept outlines are the masks, and [the test bench](../03_the-test-bench.md)
turns each mask into a place on the table and a rough width using the same
shared arithmetic it applies to all six solutions.

Two properties of this output are worth knowing before the scores. The outline
is built at a coarse resolution inside the rectangle and then enlarged, so its
edge carries an error that does not average away, and a thin stem is where that
is worst. And the confidence number is about the category rather than about the
outline, so a badly cut outline can still be scored highly.

## 3. What it needs

Very little, which is the whole point.

It needs the **Ultralytics package** and the model's weights, which the package
downloads by itself the first time the model is used, so there is no data
preparation step of any kind. It runs through PyTorch on this machine's
integrated graphics, and the weights are small enough that memory is not a
concern. The model family comes in several sizes, and the smaller end is the
sensible place to start, because the glasses fill a reasonable part of the frame.

What it does **not** need is the expensive part of every other learned solution
here: no labelled pictures, no training run, no file of weights to keep in step
with the cell, and no held-out set beyond the small one used to set the bar on
the confidence number.

The whole cost is the licence, and it is a real one. Ultralytics YOLO26-seg is
licensed under the **AGPL-3.0**, the third version of the Affero General Public
License, which requires anybody who distributes the
software, **or offers its functionality over a network**, to make the complete
corresponding source available under the same terms. The network clause is the
demanding part, because it reaches a product that never ships a copy of the
model to anybody and only ever serves answers from it. Everything else this
project depends on is permissively licensed, so this one component would change
the terms of the whole perception step if it were carried into a product. That
is accepted here, because this chapter exists to compare methods and nothing is
shipped or served. Nothing in the design depends on the borrowed model being
this particular one, so the reading transfers to whichever instance segmenter is
licensed conveniently.

## 4. What it scored on the bench

Every solution is given the same arrangements and marked the same way. There are
two sets: spawned layouts, at the spacing the cell's own layout rule gives, and
crowded layouts, closer than that rule allows.

| | found | missed | position median | mask covered | mask not the glass |
|---|---|---|---|---|---|
| spawned, 100 glasses | 10 | 90 | 28.1 mm | 100.0% | 4.3% |
| crowded, 101 glasses | 4 | 97 | 36.5 mm | 84.5% | 3.6% |

**It found ten glasses out of a hundred, and it is the worst score in the book
by a wide margin.** That is not a disappointing result; it is the result this
solution was built to produce, and it is the most informative single number in
the chapter. The reason is the domain gap. What identifies a drinking glass in a
photograph is light passing through it, the highlights on its curve and the
scene around it, and almost none of that survives in a grey picture shaded from
depth readings. The model is not confused about glasses in general. It is being
shown a kind of picture it has never seen.

The other columns are worth a glance, because they say something more precise
than "it failed". On the few glasses it did find, the masks covered the glass
completely on the spawned set, so when this model commits to an object it
outlines it well. Its position error is nonetheless the largest of the six,
because a mask that covers the visible part of a glass standing partly behind
another still describes a smaller glass in the wrong place. The full table for
all six solutions is in [the results](../11_the-results.md).

## 5. Where it is strong and where it breaks

Its strengths all come from the same source, which is that nothing is fitted.
There is nothing to collect, nothing to train and nothing to keep in step with
the cell, so this solution can be tried in an afternoon and gives a reading on
what a borrowed model is worth before anybody invests in labels. It attacks the
joining of two outlines directly, because a model that finds objects returns one
outline per object rather than one per connected shape. And it needs no graphics
card of its own.

Its weaknesses divide into what the borrowing costs and what it cannot be asked
to do.

What the borrowing costs is accuracy at the edge and honesty in its numbers. The
outline carries an enlargement error, the confidence number is not calibrated on
these pictures so any bar on it is a hand-set knob, and the names are somebody
else's categories, so they filter usefully and mean nothing beyond that. Above
all the domain gap is large enough that the method may simply not work here,
which is what happened.

What it cannot be asked to do is anything that needs fitting. Its outlines mark
only pixels where the camera actually saw the object, so a glass standing partly
behind another is read as a smaller glass in the wrong place, and the repair for
that is to train a model to return the whole silhouette — which this solution
cannot do, because it trains nothing. A completely hidden glass is invisible to
it, and no model can find what left no pixels.

## 6. When to choose it

Choose this first, always, and expect to replace it. It is the cheapest honest
measurement available of whether the problem needs a fitted model at all, and
taking that measurement before collecting labels is simply good order of work.
On pictures that look like the photographs the model was trained on, an
off-the-shelf instance segmenter is often good enough on its own, and then none
of the expensive solutions is needed.

Do not choose it when the pictures are unlike ordinary photographs, which is the
case here and is the case for most depth-derived, infra-red, medical or
industrial imagery. The repair is to move the weights towards the pictures the
model will actually be shown, which is [the same model,
fine-tuned](05_the-same-model-fine-tuned.md), or to borrow only the part that
transfers, which is [a foundation model with a
keeper](06_a-foundation-model-with-a-keeper.md).

The honest position is therefore that this is the first thing to run and
unlikely to be the one carried into a finished product. **Its value is the
comparison it makes possible rather than the accuracy it delivers**, and the
pairing with solution 4 is the reason it is worth building even though its own
score is poor.

The code is in
[`src/08_seeing-the-glasses/03-yolo-zero-shot/`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot)
and it writes its own `results.json` beside itself. The full treatment, which
explains instance segmentation against the two kinds beside it, how the outline
is produced, and why the confidence number is not a probability, starts at [what
it is](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md).

← [A network trained from scratch](03_a-network-trained-from-scratch.md) · [The same model, fine-tuned](05_the-same-model-fine-tuned.md) →
