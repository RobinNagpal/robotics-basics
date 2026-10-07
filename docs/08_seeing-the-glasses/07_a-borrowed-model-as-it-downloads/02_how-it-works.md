# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [What instance segmentation is, and the two kinds beside it](#1-what-instance-segmentation-is-and-the-two-kinds-beside-it)
2. [Why the borrowed names are a filter and never the kind of glass](#2-why-the-borrowed-names-are-a-filter-and-never-the-kind-of-glass)
3. [How the outline is produced, and why it is approximate](#3-how-the-outline-is-produced-and-why-it-is-approximate)
4. [The number beside each outline, and why it is not a probability](#4-the-number-beside-each-outline-and-why-it-is-not-a-probability)
5. [The domain gap, which is what broke it](#5-the-domain-gap-which-is-what-broke-it)

## 1. What instance segmentation is, and the two kinds beside it

Three kinds of model all produce outlines, and they are not interchangeable, so
they are worth separating before going further.

**Semantic segmentation** labels every pixel with a category and stops there. It
would mark all the glass pixels in the picture as glass, which sounds like what
this problem wants until you notice that two glasses whose outlines join produce
one connected region of glass pixels, with nothing in the output saying where
one ends and the next begins. A semantic model therefore hands the merge
straight back, unsolved.

**Instance segmentation** labels every pixel *and* says which object it belongs
to. Two glasses whose outlines join come back as two outlines that happen to be
adjacent, so the merge is answered inside the model. This is why this book
reaches for this kind of model and not for the simpler one.

**Promptable segmentation** outlines whatever is at a place you point to, and
names nothing at all. It separates objects very well and has no opinion about
what they are. That is the kind of model [solution 5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md)
borrows.

That last difference is the whole reason this document is shorter than solution
5's. A model that outlines without naming has to be followed by something that
decides which of its outlines are glasses, and in solution 5 that something is a
small keeper fitted on this cell's pictures. A model that outlines **and** names
needs no such thing, because the naming is already done. The borrowed model's
list of categories does the job that solution 5 has to fit a keeper to do, and
that is exactly why this solution can claim that nothing in it is fitted here.

## 2. Why the borrowed names are a filter and never the kind of glass

The naming is where borrowing turns out to cost everything, so this is the
section to read most carefully.

The list of categories the model knows was drawn up to describe photographs of
the everyday world, and it contains several entries a drinking glass could
plausibly belong to: a stemmed drinking vessel, a plain cup, and a few shapes
that are near neighbours of both. The cell's four kinds do not correspond to
those entries. The two kinds with a stem, the stemmed glass and the short
stemmed glass, resemble the stemmed vessel in the list. The two without a stem,
the straight glass and the tapered glass, resemble the plain cup. But the
resemblance is loose, the model has never seen these particular shapes, and the
boundary it draws between its own categories was never meant to tell this cell's
two stemmed kinds apart.

Two consequences follow from that mismatch.

The first is that **the filter on names has to be generous**. If only one
category were accepted, every glass the model named with a neighbouring category
would be thrown away. So the filter accepts the whole group of drinking-vessel
categories — a wine glass or a cup, and a bowl, a vase or a bottle beside them —
and accepts in exchange that it may sometimes admit something that is not a
glass.

Being generous was not enough, and the measurement that says so is the single
most useful thing this solution produced.
[`what_it_named.py`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/what_it_named.py)
runs the model over three held-out arrangements of each kind, three stations
each, which is nine pictures per kind and 36 in all, and prints every name the
model offered with no filter in front of it. Across those 36 pictures the model
returned 87 named objects. Five of them carried a name the filter accepts.

![Every name the borrowed model offered over 36 held-out pictures, with the five names the filter accepts marked: the model's answer to a glass seen from above is a sports ball or a frisbee, so only five of its 87 named objects survived the filter at all.](../../images/seeing-the-glasses/a-borrowed-model-as-it-downloads/07-what-the-model-called-them.png)

The failure is therefore not that the model sees nothing. It finds things in
these pictures and calls them sports balls and frisbees. A
glass seen from straight above is a disc, and in a grey picture shaded from
depth a disc has no transparency, no highlight and no bright rim, which are the
features that say "glass" in a photograph. What is left is a round silhouette,
and the nearest round silhouettes on the model's list are a ball and a frisbee.
The model is answering a different question correctly.

The second consequence of the mismatch is that **the name must never be carried
into the record as the kind of glass**. The temptation is real, because a free
guess at the kind looks like a gift. It is not a gift: it is a category from
somebody else's list, assigned by a model that was never shown this cell's
kinds, and the measurement above is what that guess is worth. This book does not
ask for the kind in any case, since every glass in one arrangement is the same
kind and that kind is known. Naming a kind from a glass's own profile belongs to
a different job in this cell, the earlier one of measuring a single glass once
the arm has looked at it from the side, and that job is not written up here. So
the name here serves as a filter and is then thrown away.

Throwing it away is also what keeps this solution inside the rule that governs
the whole project, which is that **no glass's size is written down anywhere**. A
borrowed category carries an implied size with it, because the model's idea of a
stemmed drinking vessel was formed from photographs of real ones, at the sizes
real ones come in. If the name travelled any further than the filter, that
implied size would travel with it, and a belief about how big a glass is would
have entered the cell without anything having measured it. Dropping the name
immediately after filtering prevents that, and it is a deliberate choice rather
than tidiness.

One repair is available and is refused. Adding "sports ball" and "frisbee" to
the accepted list would lift the score at once, and it would be fitting the
filter on this cell's own data, which is the single thing this solution exists
not to do. The baseline is worth having only while nothing in it was chosen
after somebody looked at the answers.

## 3. How the outline is produced, and why it is approximate

The outline needs some explanation too, because its shape is not free to be
anything, and the restriction has a consequence the arithmetic downstream feels.

A model of this kind does not draw an outline pixel by pixel. Instead it
computes, once for the whole picture, a short list of coarse pattern images, and
then for each object it returns a short list of weights. The object's outline is
the weighted sum of those patterns, cut at a threshold, and then enlarged to the
size of the picture. The useful comparison is a familiar one from maths: this is
the same move as approximating a curve by a short weighted sum of fixed basis
functions. A handful of terms captures the broad shape of almost anything, and
no handful of them will ever capture a fine detail that none of the basis shapes
contains.

Two things follow for this cell.

**A thin part of a glass is the first thing lost.** A stem is narrow compared
with the bowl above it, so it is exactly the sort of detail a coarse pattern
cannot hold, and the outline tends either to thicken it into a stub or to drop
it. The examiner measures how much of each real glass a mask covered and breaks
that number down by kind for precisely this reason, and the breakdown says the
same thing in all five blocks of spaced arrangements. This solution found 12
glasses of the two kinds with a stem and 20 of the two without. On the kinds
with a stem the block medians run from 44 to 79 per cent of the glass covered.
On the kinds without one they run from 99.8 to 100.0.

Twelve glasses are too few to prove much, and the direction is at least
consistent. Whether the coarse outline or the borrowed weights are to blame is
settled in [the same model,
fine-tuned](../08_the-same-model-fine-tuned/02_how-it-works.md), where the same
outline machinery is given hundreds of glasses to be measured on. The answer
there is not the one expected here.

**The edge of the outline is approximate, and the arithmetic reads the width
from the edge.** The shared step takes a glass's width from how far its mask's
points reach away from the axis, so an outline that is a little too generous
reports a glass a little too wide, and one that is a little too tight reports it
a little too narrow. The error does not cancel out over many glasses, because
the enlargement step tends to err the same way every time. On the few glasses
this solution did find, 3.3 per cent of the mask was not the glass at the
median, against 0.0 for a rule written by hand, and that margin is the
enlargement showing up in the marking.

## 4. The number beside each outline, and why it is not a probability

Each outline arrives with a number the model offers as its confidence, and it is
worth being precise about what that number is worth here, because the obvious
reading of it is wrong.

A number is a **calibrated** probability when its claims come true about as
often as it says they will: among the outlines it scores very highly, nearly all
should really be glasses, and among those it scores middling, a middling share
should be. Whatever calibration this model has was obtained on photographs. This
cell's pictures are not photographs, and a model's confidence under changed
input is the first thing to drift, usually becoming too sure rather than too
cautious.

What survives the change better than the numbers is their **order**. A model
whose scores are badly calibrated may still rank a clear glass above a doubtful
one, because ranking only needs the scores to move in the right direction, not
to be honest about their size. So the design uses the number to sort the
outlines and to set a bar below which an outline is ignored, and treats that bar
as a **knob set by hand and checked on arrangements from the examiner's training
half**, not as a probability threshold with a meaning. Calling it a probability
would be claiming a property nobody has measured.

This is also the one place where the solution could be improved without
abandoning its central promise. Fitting a small correction from the model's
scores to honest probabilities needs no change to the model and no outlines
drawn by hand, only a set of arrangements where the answer is known. That would
be a few fitted numbers rather than none, and it would buy a bar that means
something. It is worth noting as an option and worth keeping out of the
baseline, because the baseline's whole value is that it fits nothing. It would
also not have saved this solution, because the outlines that were lost were lost
to their names and never reached the bar.

## 5. The domain gap, which is what broke it

Everything above assumes the borrowed model works at all on this cell's
pictures. It does not, and the reason has a name.

A **domain gap** is the difference between the data a model was fitted on and
the data it is used on. Models usually fail across such a gap by producing
confident, plausible, wrong answers, which is worse than nonsense because
nothing downstream looks suspicious. Here the gap is large enough to produce the
blunter failure as well, which is silence. Each block of 20 held-out
arrangements is 60 pictures, and the model named no drinking vessel at all in 49
to 58 of the 60 when the glasses were spaced, and in 56 to 60 of the 60 when
they were crowded.

The gap runs in both directions, and both halves matter.

**The picture is not a photograph.** The cell gives a solution a grey picture
shaded from how far away each surface is. A borrowed model's strength on real
photographs comes largely from real light: the way a surface changes shade as it
curves, the texture of a table, a shadow that says where an object meets the
surface it stands on, and the colour differences that separate one object from
the one behind it. Very little of that is present here, so the model is working
with a fraction of the evidence it learned to use.

**The glasses are not photographed glasses either, and this is the direction
that is easy to forget.** What tells a model in a photograph that it is looking
at a glass is the transparency, the highlight along one side and the bright line
on the rim, and this cell renders its glasses as solid shaded shapes. So the
strongest evidence for the model's own category is absent, and the broad
silhouette, which is much weaker evidence, is all that is left.

That second direction is why this failed as completely as it did, and it is also
what makes the comparison with [solution
4](../08_the-same-model-fine-tuned/01_what-it-is.md) the interesting one.
Solution 4 takes this same model and continues its training on this cell's
pictures, which is the standard repair for exactly this gap. The difference
between the two is a clean measurement of what the gap costs, and that is the
most useful thing this solution contributes to the chapter.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
