# A worked example

This page follows this solution through one arrangement of glasses with the
numbers the run produced, and then through the case this book keeps returning to,
a glass that is completely hidden, because a worked example that shows only the
easy case teaches the wrong lesson.

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

**This is the one place where this solution and its untrained partner score the
same.** Training moves what a model does with the pixels it is given, and here
there are no pixels to do anything with, so the pair that exists to measure what
fine-tuning buys measures nothing at all on this case. Nothing in the output
raises a question either: there is no low confidence number and no impossible
width, because the visible pixels belong to the glass in front and return its own
true footprint.

## 2. A worked example

Follow one arrangement through, because the difference from solution 3 is easier
to see once both have been run over the same table.

**The arrangement.** Five stemmed glasses stand in the glass zone, drawn at
proportions from across the kind's range, so they are not all the same height.
Two of them stand as close together as the cell's layout rule allows, roughly
along the line running out from the point below the camera, with the taller one
nearer that point. The camera takes the survey picture from the top. In that
picture the two close glasses leave one connected shape, with no seam along it.

**What solution 3 returns.** Nothing. Over three held-out arrangements of
stemmed glasses, nine pictures, the borrowed model named 20 objects and called
none of them a drinking vessel, so the filter on names kept nothing and every
picture came back as a doubt with no glasses in it. Five glasses go out and no
entries come back. Across all five blocks of spaced arrangements it reports 6.4
glasses per 100.

**What this solution returns.** Five entries. The fitted model is shown a kind of
picture it was trained on, and the five glasses are five instances of the only
class it knows. Each glass produces several candidates, and the step that
discards candidates overlapping a better one reduces each cluster to a single
answer. Over five blocks of spaced arrangements this solution reports 99.4
glasses per 100, misses 3 in 499 and splits one, so five out of five is the
ordinary result rather than a lucky one. No entry can be lost to a name, because
there is one name. The bowls are outlined well and so are the stems: the masks
cover 99.6 per cent of a stemmed glass at the median, which is the measurement
behind the claim in [how it works](03_how-it-works.md) that training holds a stem
the written rule loses.

**Where the two still agree.** The nearer of the close pair covers part of the
one behind it, so the mask of the one behind holds only the part the camera saw.
Both solutions return modal masks, so both hand the examiner a slice of a
silhouette rather than the whole of one. The examiner then reports that glass too
narrow and at a place pulled towards the part that stayed visible. If its width
still falls inside the range a stemmed glass can have, nothing refuses it, and a
wrong report reaches the marking with nothing marking it as doubtful.

**What that costs is visible in the crowded arrangements**, where glasses stand
closer than the layout rule allows and cover each other far more often. There
this solution reports 72.0 glasses per 100 rather than 99.4, and the width check
hands over between 25 and 47 candidates per block of 20 arrangements as having a
width no glass of the kind could have. A candidate refused that way is a
candidate the check believes is a slice, and the 28 glasses per 100 that go
missing on the crowded set are some mixture of those, of glasses that left too
few pixels to fit anything to, and of glasses that were covered outright. The
scorecard does not separate the three, so neither does this page.

**And the case neither can answer.** Complete covering needs a kind whose range
of proportions holds both short glasses and much taller ones, and that is the
tapered glass rather than the stemmed glass, so take an arrangement of tapered
glasses instead. Stand one of them, drawn at the short end of that range, beyond
the tallest glass in the arrangement along the line running out from the point
below the camera, close enough that the tall glass's stretched outline covers it
completely. It produces no pixels, so neither solution produces an entry for it.
Every entry that did come back is legal and confident, and the count is one short
of the number put out. Only the shared geometry that works out where a glass
could have been hiding can raise that question, and only moving the arm can
answer it.

The honest summary of the example is that fine-tuning changes the first half of
it and not the second. The finding becomes reliable and the naming failures
disappear; the coarse edge, the slice of a hidden silhouette and the glass with
no pixels are all exactly where they were.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
