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

**This solution has the least to add**, because it fits nothing and has no
check of its own to fire. The borrowed model returns one outline per object it
believes it found, the hidden glass is not an object in the picture, and so no
candidate is produced and no entry appears. The confidence number is about the
objects that were found, and they really are glasses.

## 2. A worked example

Following one crowded arrangement through makes the failures above easier to
recognise, because they appear together rather than one at a time.

Four glasses of the stemmed kind stand in the glass zone, which is the fewest an
arrangement holds. Three of them are where the interest is: one near the middle,
standing at the tall end of the range its kind allows, one a little way out from
it at the short end of that range, and one off near the edge of the frame. The
fourth stands clear of the other three and is outlined without any trouble. The
camera takes the survey picture from the top.

Suppose the borrowed model returns six outlines. The tall glass comes back
twice, once under each of two neighbouring drinking-vessel categories, with
nearly the same pixels both times, its bowl outlined well and its stem thickened
into a stub. The glass near the edge comes back once and is outlined reasonably,
because the bowl is the easy part and the stem is the hard part wherever the
glass stands. The glass standing clear comes back once as well, outlined
cleanly. The short glass comes back once too, but the tall glass's outline leans
outwards from the point directly below the camera and overlaps it, so the short
glass's outline holds only the part of it the tall one did not cover. The table
itself is named and dropped by the filter, which accounts for the sixth outline.

What the arithmetic would make of that is the instructive part. The two outlines
of the tall glass cover substantially the same pixels, so merging them before
handing anything over turns them into one record and the double naming costs
nothing. The glass standing clear is reported accurately, and the glass near the
edge is reported with a place that is good and a width pulled in a little by the
lost stem. The short glass is reported at a place pulled towards the part of it
that stayed visible, and with a width read from a slice of its silhouette rather
than from the whole of it, so it is reported narrower than it is.

That last report is the honest summary of this solution. Four glasses were put
out and four reports came back, so the counts look right. One of the four is
quietly wrong, and nothing in the run marks it as doubtful. It is the failure a
borrowed model used as the decider would produce most often, and it is the
reason the comparison against the same model fitted here matters.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
