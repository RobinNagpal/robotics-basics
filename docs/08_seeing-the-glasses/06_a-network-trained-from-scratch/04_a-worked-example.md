# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that is completely hidden,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

A glass can be covered completely, and then it contributes no pixel to any
picture. [What is asked for](../02_the-problem/01_what-is-asked-for.md) gives
the geometry and says how close two glasses have to stand for it, and [looking
again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) is the shared
answer: work out from arithmetic where a glass could have been standing unseen,
and go and look there. **No method that reads pictures can do better**, because
the arrangement with the hidden glass and the same arrangement with it removed
produce the same picture, pixel for pixel. What follows is only what is this
solution's own.

**This solution is unusually good at a glass that is only partly covered**, and
the reason is that it finds nothing between two glasses. Every other method
here separates them by finding something — a gap, a strip of bare table, a
seam. Here each glass pixel votes for its own glass's middle whether or not
anything can be told apart anywhere, so a glass left with only a crescent of
itself still speaks, and its votes do not have to be joined to each other or to
make a recognisable shape.

![When a tall glass's outline is thrown far enough outwards to swallow a shorter neighbour standing at the closest separation the cell allows, not one vote mentions the covered glass; swing the same pair off the line out from the camera and the crescent that survives casts few votes, but they pile up almost exactly where that glass really stands.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-above.png)

**Covered completely, it has no alarm to raise.** Both of this solution's own
warnings are measurements of votes — how many a pile holds, and how far they
sit from their own peak — and there are no votes to measure. The vote map
simply has one peak where two glasses are standing, and nothing in it is wrong.

![Looking level the near glass's outline covers the far one whole with no outward throw needed, and the single pile of votes left behind is tight, well filled and a believable width, so nothing about it looks wrong; step the far glass off the line of sight and the strip that appears votes for its own middle.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-the-side.png)

![Four pictures from the top as the camera slides outwards show the covered glass sitting outside the frame in every one of them, so from the top this solution loses a glass only where its picture never reached, and a short sideways move of the camera ends even that.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-above.png)

![Looking from the side, the far glass contributes not one pixel while it stands on the line of sight, however much further back it is put, and only sideways movement brings it back — in less of a slide than a survey station already makes between its two pictures.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-the-side.png)

## 2. A worked example

This example follows one crowded arrangement through the method, and it is the
case the whole solution exists for.

**What is on the table.** Two glasses of one kind stand much closer together
than the cell's own rule allows, as the examiner's crowded family stands them:
somewhere between a third and two thirds of the 150 mm the layout rule
guarantees. There is still bare table between their rims, but only a little.

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
two piles whose separation is the full distance between the two middles. At the
closest the crowded family ever stands two glasses, 45 mm, those middles come
out 17 to 28 pixels apart in the half-size picture, depending on how tall the
two glasses are, against the 16 pixels the counting step rubs out round each
middle it takes. So the second pile survives to be counted — comfortably for two
tall glasses, and by one pixel for two of the shortest the kind allows.
Both are tight, both have plenty of votes, and a circle fitted to each pile's
voters comes back inside the range this kind of glass can be. **Two glasses, two
masks, out of a picture in which the pixels themselves never came apart.**

**The case that defeats the votes.** Now stand one glass mostly behind another,
so that only a crescent down one side of it is ever visible. It contributes a
small fraction of the votes it should, and worse, every one of them comes from
that same crescent, so the votes agree with each other and are wrong in the
same direction. The pile lands off the true middle and its spread comes out
much wider than a tight pile's. The short count is the alarm the code measures
and it fires on its own; the wide spread is the second warning this chapter
prescribes. Neither of them is the network's own opinion of itself: both are
measurements of the votes. The pair is reported as one the arm could not
separate, with its reason, which is a result this problem asks for and not a
failure.

![The less of a glass reaches the picture the fewer votes it casts and the further its votes sit from their own peak, so a short count and a wide spread are two separate warnings, both of them measurements of the votes rather than the network's opinion of itself.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-too-few-votes.png)

**What it costs in time.** Running the network on a picture costs milliseconds.
Moving the arm to a new place and letting it settle costs seconds. So the
balance of this solution is to compute freely and move rarely, and the whole of
its cost sits in building it rather than in running it.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
