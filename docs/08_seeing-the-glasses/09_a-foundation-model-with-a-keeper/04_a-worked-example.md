# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that is completely hidden,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

A glass can be missing from a picture altogether. It stands on the table, it is
opaque, the camera is pointed at the part of the table it stands on, and not one
pixel of it comes back, because a taller glass's outline has been thrown
outwards by splay until it sweeps right over the shorter one. This is the most
dangerous of the [three difficulties this book
names](../02_the-problem/01_what-is-asked-for.md), every solution has to say what
it does about it, and this solution's answer is a clean
and complete no.

Being exact about why takes five steps, and each one closes a different escape
route.

**There is no region to propose.** The borrowed model grows a mask from the
picture's own content at the place the prompt points at. A prompt point anywhere
over the piece of picture where the hidden glass ought to be lands on the
covering glass, so what comes back is the covering glass, and that answer is
*correct*. Nothing has malfunctioned.

**Prompting harder does not help**, and this is where the property named earlier
matters. A prompt selects; it does not add information. There is no point, no
box and no rough mask that makes the model return a glass which cast no pixels,
because a prompt works on the pixels that are there. A box drawn round the empty
stretch of table returns the table, or the covering glass, depending on where
its edges fall.

**The keeper is never consulted**, because it only ever sees proposals and there
is no proposal for this glass. All three of its answers are about a region that
exists.

**No check can fire.** Every check here is a check on a proposal: the measured
width, how round it is, how far it stands above the table, how many prompts
agreed on it, how it sits among the other proposals. What comes back for the
covering glass is one proposal with a legal width, a round footprint, a proper
height above the table and the agreement of many prompts. **Nothing about it is
wrong.** The picture is one believable glass where two are standing, which is
the shape this difficulty always takes.

![A prompt point over the piece of table where the hidden glass stands lands on the covering glass, so the mask that comes back is the covering glass's, no proposal for the hidden glass ever exists, and the keeper is never consulted about it.](../../images/seeing-the-glasses/a-foundation-model-with-a-keeper/08-where-it-stops.png)

**And more model does not help either.** The arrangement with the hidden glass
and the same arrangement with that glass removed produce the same picture, pixel
for pixel. No function of the picture can tell them apart, whatever its size and
however it was fitted, because the thing that differs between the two left no
trace in the input. A larger checkpoint changes nothing, a text prompt on the
second way changes nothing, and neither would training the borrowed model if
training it were allowed.

One more thing is worth saying, because it is the temptation this solution
invites. A foundation model's strength is that it generalises to objects it
never saw, and it is easy to hope that this covers the hidden case as well. It
does not. The difficulty here is not an unfamiliar object but **an absent one**,
and generalisation handles evidence of a new kind, while here there is no
evidence of any kind.

So this solution cannot handle the completely hidden case and has to hand it on,
and what it hands on is not a glass but a **region**: the part of the table it
could not have seen. Working out that region is arithmetic on splay and on the
glasses that *were* found, and moving the camera to look again is the shared
part of this problem, described once in [looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which every solution points at. This solution
contributes the masks those two argue from, and none of the argument.

## 2. A worked example

One picture from the top shows the whole chain working, and failing once. It is
a walk through the design rather than a record of a run.

**The picture.** Five glasses stand in the glass zone, drawn across the kind's
range of sizes, two of them along a line running out from the point below the
camera. The depth is shaded into grey, normalised so that the tallest rim and
the table sit at opposite ends of the range of grey.

**The proposals.** The grid of prompts returns a heap, and after scoring,
stability and duplicate removal a shortlist is left: the table, four regions
each about one glass wide, one region far wider than the kind allows, three rims
and two mouths.

**The keeper.** The table is dropped, on its width and on lying at the table's
own height. The rims are dropped, on being rings rather than filled discs and on
sitting inside proposals whose widths are legal. The mouths are the interesting
case, because their footprints are perfectly legal, so the keeper may well hold
one of them as a glass and nothing it is shown says otherwise. Four proposals
are kept as one glass each, and the wide one is answered "more than one glass".

**The width check and the second round.** All four kept proposals have a width
inside the kind's range, so all four are reported with a mask, and the wide one
fails the check as it should. A fresh grid of points inside that wide region
returns two masks, split along the step between the near glass's rim and the far
glass's wall, and both of their widths land inside the kind's range, so the pair
is reported as two glasses rather than as an unseparated pair.

**One report per place.** The near glass of that pair was also proposed on its
own, so it now arrives twice, and the mouth the keeper held stands at the place
its own glass already occupies. Both are second reports at a place already
taken, so both are dropped, and five glasses are reported where five stand.

**Where it fails.** Behind the tallest glass in the arrangement a sixth glass is
standing that nothing in this run has any opinion about. It cast no pixels, so
no prompt point could reach it, so no proposal exists for it, so the keeper was
never asked. The report says five glasses and one region of table that could not
have been seen, and the second of those two statements is this solution's entire
contribution to finding the sixth.

**What it costs.** Running the borrowed model is the whole of the cost to within
a rounding error: the picture encoder runs once per picture, every prompt after
it is cheap, and what the keeper adds is too small to see beside them. The whole
chain still costs far less than one movement of the arm.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
