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

**This is the one place where this solution and its untrained partner are
guaranteed to score the same.** Training moves what a model does with the
pixels it is given, and here there are no pixels to do anything with, so the
pair that exists to measure what fine-tuning buys measures nothing at all on
this case. Nothing in the output raises a question either: there is no low
confidence number and no impossible width, because the visible pixels belong to
the glass in front and return to its own true footprint.

## 2. A worked example

Follow one arrangement through, because the difference from solution 3 is easier
to recognise once both have been run over the same table.

**The arrangement.** Five stemmed glasses stand in the glass zone, drawn at
proportions from across the kind's range, so they are not all the same height.
Two of them stand as close together as the cell allows, roughly along the line
running out from the point below the camera, with the taller one nearer that
point. The camera takes the survey picture from the top. In that
picture the two close glasses leave one connected shape, with no seam along it.

**What solution 3 would return.** The borrowed model would find shapes, and
every outline would then have to survive the filter on names. The taller of the
close pair might be named under two neighbouring everyday categories and arrive
twice. One of the clear glasses might be named as something the filter does not
accept and be dropped, which would cost a glass with nothing in the output to
show for it. And every outline would be produced by weights that had never seen
a picture like this one, so how many of the five were found at all is genuinely
in doubt.

**What this solution would return.** The fitted model would be shown a kind of
picture it had been trained on, and the five glasses would be five instances of
the only class it knows. Each glass would produce several candidates; the step
that discards candidates overlapping a better one would reduce each cluster to a
single answer, so five entries would be expected rather than seven or three. No
entry could be lost to a name, because there is one name. The bowls would be
outlined well, and the stems would be outlined about as well, because the
marking above shows that training does hold a stem even though the outline
machinery is coarse.

**Where the two would still agree.** The nearer of the close pair covers part of
the one behind it, so the mask of the one behind holds only the part the camera
saw. Both solutions return modal masks, so both would hand the examiner a slice of
a silhouette rather than the whole of one. The examiner would then report that
glass too narrow and at a place pulled towards the part that stayed visible. Its
width might still fall inside the range a stemmed glass can have, in which case
nothing would refuse it, and a wrong report would reach the marking with nothing
marking it as doubtful.

**And the case neither can answer.** Complete covering needs a kind whose range
of proportions holds both short glasses and much taller ones, and that is the
tapered glass rather than the stemmed glass, so take an arrangement of tapered
glasses instead. Stand one of them, drawn at the short end of that range, beyond
the tallest glass in the arrangement along the line running out from the point
below the camera, close enough that the tall glass's stretched outline covers it
completely. It produces no pixels, so neither solution produces an entry for it.
Every entry that did come back would be legal and confident, and the count would
be one short of the number put out. Only the shared geometry that works out
where a glass could have been hiding can raise that question, and only moving
the arm can answer it.

The honest summary of the example is that fine-tuning changes the first half of
it and not the second. The finding becomes reliable and the naming failures
disappear; the coarse edge, the slice of a hidden silhouette and the glass with
no pixels are all exactly where they were.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
