# A borrowed model, as it downloads — a worked example

This page follows this solution through one arrangement of glasses from
beginning to end, with real numbers rather than a description of what would
happen. It then takes the case this book keeps returning to, a glass that is
completely hidden, because a worked example that shows only the easy case
teaches the wrong lesson. By the end you will have seen both what this solution
does well and where it is left with nothing to say.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

Every solution document in this chapter answers this question, and the answers
differ in a way worth comparing. This one's answer is **no, from either of the
camera's two places**, and the reason is the same reason as for the other
mask-producing solutions.

**Looking from the top**, a tall glass's outline can sweep over a short one and
cover it completely, so the short glass appears in no picture at all. A model
that finds objects in a picture can only find objects the picture contains.
There would be nothing at those pixels but the tall glass, so one outline would
come back, correctly describing the glass the camera could see, and the covered
glass would not merely be mis-measured but absent from the model's output
entirely. No bar on the confidence number and no change of model size alters
this, because the evidence is not weak, it is missing.

**Looking from the side**, the situation is cleaner and worse. Two arrangements,
one with a far glass standing behind a near one and one with the far glass taken
away, produce the same picture pixel for pixel. The model is a function of the
picture, so it would return the same outlines with the same names and the same
numbers for both. Nothing the model could be asked would distinguish them.

The cure for both lies outside this solution, in [looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which every one of the six points at. It works
out which parts of the table nobody could have seen and sends the camera to
cover them from new positions. This solution would contribute the outlines that
argument starts from, and would contribute nothing to the argument itself.

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

← [A borrowed model, as it downloads — the code](03_the-code.md) · [A borrowed model, as it downloads — what it needs](05_what-it-needs.md) →
