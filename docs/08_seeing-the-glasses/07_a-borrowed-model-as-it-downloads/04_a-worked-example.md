# A worked example

This page follows this solution through real arrangements with the numbers the
run produced, and then through the case this book keeps returning to, a glass
that is completely hidden, because a worked example that shows only the easy case
teaches the wrong lesson.

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

**This solution has the least to add**, because it fits nothing and has no
check of its own to fire. The borrowed model returns one outline per object it
believes it found, the hidden glass is not an object in the picture, and so no
candidate is produced and no entry appears.

## 2. A worked example

The ordinary outcome is the one worth following first, because in this solution
the ordinary outcome is nothing at all.

**Three arrangements of stemmed glasses, nine pictures.** Take three held-out
arrangements where the kind on the table is the stemmed glass, and take all three
survey stations for each, which is nine pictures. The model is shown each one
and returns 20 named objects across the nine: twelve sports balls, four
frisbees, two birds, a cake and a donut. Not one of those names is in the
accepted list, so the filter keeps nothing, and `Finder.find` returns an empty
list of glasses with the doubt "the model named nothing in this picture a
drinking vessel" against every picture. The examiner marks four to six glasses
missed in every arrangement, and the scorecard records no merge, no split and
nothing false, because nothing was reported.

That is not an unlucky sample. Across a whole block of 20 spaced arrangements —
60 pictures — the same doubt comes back from 49 of them, and the solution
reports 10 glasses out of the 100 on the tables. Over five such blocks the
average is 6.4 found per 100.

**The exception is worth following too**, because it shows what happens on the
rare occasion the filter does keep something. In the same block the model named
three short stemmed glasses something the filter accepts, and their masks
covered 66.8 per cent of the glass at the median. The bowl is the easy part and
the stem is the hard part, so the mask is a bowl with the stem thickened or
dropped, and the shared arithmetic reads a width from the edge of that bowl. The
report comes back with a place that is roughly right and a width pulled in by
the missing stem. Nothing in the run marks it as doubtful, because the
confidence number is about the category rather than about the outline.

**The failure to take away from this is silence, not error.** Every glass this
solution reported in the whole run was a real glass: no merges, no splits and no
false reports in any block. What it did instead was say nothing about 93 glasses
in every 100. A method that reports a wrong glass announces itself. A method that
reports no glass looks, from downstream, exactly like an empty table, and the
only thing that distinguishes the two is the count of doubts the examiner
collects.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
