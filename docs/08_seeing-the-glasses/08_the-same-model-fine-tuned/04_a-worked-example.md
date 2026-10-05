# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that is completely hidden,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

Every solution document in this chapter answers this question, which is whether
the method can find a glass that no picture holds. This one's answer is **that
it cannot, from either of the camera's places**, and the reasoning is short and
absolute.

Looking **from the top**, a glass's outline is thrown outwards away from the
point directly below the camera, and the taller the glass the further out it
goes. Because one kind holds both short glasses and much taller ones, a tall
glass's stretched outline can sweep over a short neighbour and cover it
completely. The short glass then produces no pixels at all. A model finds
objects in a picture, and there is nothing of that glass in the picture to find,
so no candidate is produced and no entry appears.

Looking **from the side**, it is plainer. A near glass stands in the way, and
because it is nearer it is drawn larger, so a glass directly behind it
disappears however far behind it stands.

**No amount of training helps, and this is worth settling exactly, because more
training is the first thing anyone suggests.** Take the arrangement with the
hidden glass, and the same arrangement with that glass taken away. The renderer
produces the same picture for both, pixel for pixel. A model is a function of
its input, so no model of any size, fitted by any method, can return two
different answers for two identical inputs. What differs between the two
arrangements left no trace in the input. This is therefore a fact about the
input and not about the model, and it is the one place where this solution and
its untrained partner are guaranteed to score the same.

Nothing in the output raises a question either. There is no low confidence
number, because the glass that was found really is a glass and the model is
right to be sure. There is no impossible width, because the visible pixels
belong to the glass in front and return to its own true footprint. Every check
on this solution's output is a check on something that was found, and here there
is nothing to check.

So this solution reports the case rather than answering it, and what it reports
is not a glass but a region of table it could not have seen. Working out that
region is arithmetic on the outward throw and on the glasses that **were**
found, and then going to look at it is a move of the arm. Both belong to the
part every solution in this chapter shares rather than to any one of them, as
[looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) sets out. This solution
contributes the masks that shared part argues from, and none of the argument.

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
saw. Both solutions return modal masks, so both would hand the bench a slice of
a silhouette rather than the whole of one. The bench would then report that
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
