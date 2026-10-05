# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that is completely hidden,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

Every solution in this book has to answer the case where a glass is absent
from the picture altogether, and this one's answer has two halves that point in
opposite directions.

The first half is unusually good. Every other method here separates two glasses
by finding something between them: a gap in the picture, a strip of bare table,
a seam. This one finds nothing between them. Each glass pixel votes for its own
glass's middle whether or not anything can be told apart anywhere, so a glass
that is only **partly** covered still speaks. Its surviving pixels vote for the
right middle, and they do not have to be joined to each other, or to make a
recognisable shape, or to lie on any particular part of the glass. Because one
kind spans a small glass and a much taller one, a glass can be left with only a
crescent of itself even at the gap the cell guarantees, and a crescent is
exactly what voting handles best.

![When a tall glass's outline is thrown far enough outwards to swallow a shorter neighbour standing at the closest separation the cell allows, not one vote mentions the covered glass; swing the same pair off the line out from the camera and the crescent that survives casts few votes, but they pile up almost exactly where that glass really stands.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-above.png)

The second half is a hard stop. **A glass covered completely owns no pixels, so
it casts no votes, so there is no pile to find.** There is no loose spread to
notice and no short count to fail, because both of this solution's own alarms
are measurements of votes and there are no votes to measure. The vote map
simply has one peak where two glasses are standing, and nothing in it is wrong.

![Looking level the near glass's outline covers the far one whole with no outward throw needed, and the single pile of votes left behind is tight, well filled and a believable width, so nothing about it looks wrong; step the far glass off the line of sight and the strip that appears votes for its own middle.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-the-side.png)

It is worth settling whether more training would help, because it is the first
thing anyone suggests. Take the arrangement with the hidden glass and the same
arrangement with that glass taken away: the two produce the same picture, pixel
for pixel. No function of the picture can tell them apart, whatever its shape
and however it was fitted, because the thing that differs between the two
arrangements left no trace in the input. **This is a fact about the input and
not about the model**, and it is the same limit every method here that works
from pixels runs into.

There is one qualification worth working out rather than waving at, because it
is the obvious objection. A network *can* be trained to mark part of an object
it cannot see, and the name for that is **amodal segmentation**, which means
predicting an object's whole extent rather than only its visible pixels. The
examiner could label it, because it can render each glass's mask with the other
glasses taken away. But amodal completion extends evidence, so it needs some of
the object to be visible to extend from, and with no pixels at all there is
nothing to extend. A model asked to mark a glass that *might* be standing
behind this one would be inventing an arrangement rather than reading a
picture. Whether predicting the hidden part of a partly visible glass is worth
doing is studied inside [RF-DETR fine-tuned](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md), which
carries that question as its own second rung.

The two views lose a glass in different ways, and the difference is worth
separating, because what this solution cannot see is not the same in each. From
the top, a glass disappears only under the outward throw of a taller
neighbour's outline, and that throw has to run so far out that the covered glass
was never inside the frame to begin with. Nothing is missing from the picture;
the picture never reached that part of the table.

![Four pictures from the top as the camera slides outwards show the covered glass sitting outside the frame in every one of them, so from the top this solution loses a glass only where its picture never reached, and a short sideways move of the camera ends even that.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-above.png)

From the side nothing is thrown outwards at all. The near glass's outline simply
lies over the far one's along the line the two of them stand on, and pushing the
far glass further back does not help, because it only shrinks in the picture
while the near outline stays as it is. Here the covered glass is inside the
frame, and this solution still has no pixel of it to vote with.

![Looking from the side, the far glass contributes not one pixel while it stands on the line of sight, however much further back it is put, and only sideways movement brings it back — in less of a slide than a survey station already makes between its two pictures.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-the-side.png)

So what this solution hands on is not a glass but a region: the part of the
table it could not have seen. Working out that region is geometry on the
outward throw of the outlines and on the glasses that *were* found, and going
to look at it is a movement of the arm. Both belong to [looking again at what
was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which every one of the six shares, and this
solution contributes the masks that argument starts from and none of the
argument.

## 2. A worked example

This example follows one crowded arrangement through the method, and it is the
case the whole solution exists for.

**What is on the table.** Two glasses of one kind stand much closer together
than the cell's own rule allows, which is the crowded family of arrangements
the examiner draws deliberately. There is still bare table between their rims, but
only a little.

**What the picture does to them.** From the top, each glass's outline is thrown
outwards from the point below the lens, so each covers more of the picture than
its footprint deserves. The two outlines join. A flood fill over the mask comes
back with **one** shape, spanning both glasses and the gap between them, and
that shape is far wider than any glass of this kind can be. A rule that checks
widths therefore notices that something is wrong — and that is all it can do,
because nothing in a class map says where to cut.

**What the votes do.** The pixels of the two glasses are exactly as joined as
before, because nothing has changed about the pixels. Their votes are not. Each
glass's pixels point inwards at their own glass's middle, so the votes land in
two piles whose separation is the full distance between the two middles, which
is comfortably more than the counting step can span. Both piles are tight, both
have plenty of votes, and a circle fitted to each pile's voters comes back
inside the range this kind of glass can be. **Two glasses, two masks, out of a
picture in which the pixels themselves never came apart.**

**The case that defeats the votes.** Now stand one glass mostly behind another,
so that only a crescent down one side of it is ever visible. It contributes a
small fraction of the votes it should, and worse, every one of them comes from
that same crescent, so the votes agree with each other and are wrong in the
same direction. The pile lands off the true middle and its spread comes out
much wider than a tight pile's. The short count is the alarm the code measures
and it fires on its own; the wide spread is the second warning this document
prescribes. Neither of them is the network's own opinion of itself: both are
measurements of the votes. The pair is reported as one the arm could not
separate, with its reason, which is a result this problem asks for and not a
failure.

![The less of a glass reaches the picture the fewer votes it casts and the further its votes sit from their own peak, so a short count and a wide spread are two separate warnings, both of them measurements of the votes rather than the network's opinion of itself.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-too-few-votes.png)

**What it costs in time.** Running the network on a picture costs milliseconds.
Moving the arm to a new place and letting it settle costs seconds. So the
balance of this solution is to compute freely and move rarely, and the whole of
its cost sits in building it rather than in running it.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
