# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [What instance segmentation is, and the two kinds beside it](#1-what-instance-segmentation-is-and-the-two-kinds-beside-it)
2. [Why the borrowed names are a filter and never the kind of glass](#2-why-the-borrowed-names-are-a-filter-and-never-the-kind-of-glass)
3. [How the outline is produced, and why it is approximate](#3-how-the-outline-is-produced-and-why-it-is-approximate)
4. [The number beside each outline, and why it is not a probability](#4-the-number-beside-each-outline-and-why-it-is-not-a-probability)
5. [The domain gap, which is the main risk](#5-the-domain-gap-which-is-the-main-risk)

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

The naming is also where the weakness of borrowing first becomes visible, so
this is the section to read most carefully.

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
would be thrown away, and the solution would lose a whole kind for no reason. So
the filter should accept the whole group of drinking-vessel categories, and
accept in exchange that it will sometimes also admit something that is not a
glass.

The second is that **the name must never be carried into the record as the kind
of glass**. The temptation is real, because a free guess at the kind looks like
a gift. It is not a gift: it is a category from somebody else's list, assigned
by a model that was never shown this cell's kinds, and it would be wrong often
enough to be dangerous. This book does not ask for the kind in any case, since
every glass in one arrangement is the same kind and that kind is known. Naming a
kind from a glass's own profile belongs to a different job in this cell, the
earlier one of measuring a single glass once the arm has looked at it from the
side, and that job is not written up here. So the name here serves as a filter
and is then thrown away.

Throwing it away is also what keeps this solution inside the rule that governs
the whole project, which is that **no glass's size is written down anywhere**. A
borrowed category carries an implied size with it, because the model's idea of a
stemmed drinking vessel was formed from photographs of real ones, at the sizes
real ones come in. If the name travelled any further than the filter, that
implied size would travel with it, and a belief about how big a glass is would
have entered the cell without anything having measured it. Dropping the name
immediately after filtering is what prevents that, and it is a deliberate choice
rather than tidiness.

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
cannot hold, and the outline would tend either to thicken it into a stub or to
drop it. The examiner measures how much of each real glass a mask covered and
breaks that number down by kind for precisely this reason, and the expectation
here is the one [the problem
statement](../02_the-problem/01_what-is-asked-for.md) already sets out from the
shapes alone: the two kinds without a stem should be outlined almost exactly,
and the two with a stem should be where the method does worst, and the stemmed
glass worst of all. That is an expectation drawn from the shape of the glasses
and the coarseness of the outline, not a measurement of this model.

**The edge of the outline is approximate, and the arithmetic reads the width
from the edge.** The shared step takes a glass's width from how far its mask's
points reach away from the axis, so an outline that is a little too generous
reports a glass a little too wide, and one that is a little too tight reports it
a little too narrow. The error would not cancel out over many glasses, because
the enlargement step tends to err the same way every time. This is the main
reason to expect this solution to sit further from the best achievable answer
than a model fitted on this cell's own pictures, and it is a limit of the
outline rather than of the finding.

## 4. The number beside each outline, and why it is not a probability

Each outline arrives with a number the model offers as its confidence, and it is
worth being precise about what that number would be worth here, because the
obvious reading of it is wrong.

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
to be honest about their size. So this design may use the number to sort the
outlines and to set a bar below which an outline is ignored, but it must treat
that bar as a **knob set by hand and checked on arrangements from the examiner's
training half**, not as a probability threshold with a meaning. Calling it a
probability would be claiming a property nobody has measured.

This is also the one place where the solution could be improved without
abandoning its central promise. Fitting a small correction from the model's
scores to honest probabilities needs no change to the model and no outlines
drawn by hand, only a set of arrangements where the answer is known. That would
be a few fitted numbers rather than none, and it would buy a bar that means
something. It is worth noting as an option and worth keeping out of the
baseline, because the baseline's whole value is that it fits nothing.

## 5. The domain gap, which is the main risk

Everything above assumes the borrowed model works at all on this cell's
pictures, and that assumption deserves its own section, because the difference
between what the model was fitted on and what it would be shown here is large
and runs in both directions.

A **domain gap** is the difference between the data a model was fitted on and
the data it is used on. Models fail across such a gap in a characteristic way:
not by producing nonsense, but by producing confident, plausible, wrong answers,
which is worse, because nothing downstream looks suspicious.

**The picture is not a photograph.** The cell gives a solution a grey picture
shaded from how far away each surface is. A borrowed model's strength on real
photographs comes largely from real light: the way a surface changes shade as it
curves, the texture of a table, a shadow that says where an object meets the
surface it stands on, and the colour differences that separate one object from
the one behind it. Very little of that is present here. The model would be asked
to work with a fraction of the evidence it learned to use.

**The glasses are not photographed glasses either, and this is the direction
that is easy to forget.** A real drinking glass is transparent, so a photograph
of one shows the background through it, a bright highlight along one side, and a
bright line where the rim catches the light. Those are precisely the features
that tell a model, in a photograph, that it is looking at a glass. The cell's
glasses are rendered as solid shaded shapes, so the strongest evidence the model
has for its own category is absent, while the broad silhouette, which is weaker
evidence, is all that remains. So the gap is not only that the picture is poorer
than a photograph; it is also that the thing in the picture no longer looks like
the thing the model was taught to name.

Put together, this is the clearest reason the solution might fail outright
rather than merely do poorly, and it is also what makes the comparison with
[solution 4](../08_the-same-model-fine-tuned/01_what-it-is.md) the interesting one. Solution 4 takes this
same model and continues its training on this cell's pictures, which is the
standard repair for exactly this gap. The difference between the two would
therefore be a clean measurement of what the gap costs, and that is the most
useful thing this solution could contribute to this chapter even if it performed
badly.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
