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

**The keeper is never consulted**, which is worth following because it closes
the escape route this solution seems to offer. The borrowed model grows a mask
from the picture's own content at the place the prompt points at, so a prompt
anywhere over the hidden glass lands on the covering glass and returns the
covering glass — and that answer is correct. Prompting harder does not help,
because **a prompt selects and does not add information**: there is no point,
no box and no rough mask that makes a model return a glass which cast no
pixels. With no proposal for the hidden glass, the keeper's three answers are
never asked for, and every check here is a check on a proposal.

![A prompt point over the piece of table where the hidden glass stands lands on the covering glass, so the mask that comes back is the covering glass's, no proposal for the hidden glass ever exists, and the keeper is never consulted about it.](../../images/seeing-the-glasses/a-foundation-model-with-a-keeper/08-where-it-stops.png)

One temptation is worth naming, because this solution invites it. A foundation
model's strength is that it generalises to objects it never saw, and it is easy
to hope that covers this. It does not. The difficulty is not an unfamiliar
object but **an absent one**, and generalisation handles evidence of a new
kind, while here there is no evidence of any kind.

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
