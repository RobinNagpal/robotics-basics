# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that is completely hidden,
because a worked example that shows only the easy case teaches the wrong
lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

Every document in this set has to answer this, and this one answers it twice,
because the second rung moves the boundary without removing it.

A glass can be missing from a picture altogether. It is standing on the table,
it is solid, the depth camera is pointed straight at the part of the table it
stands on, and not one pixel of it comes back. From the top that happens through
splay: the tall end of this kind is more than twice the height of its short end,
so a tall glass's outline is thrown much further out than a short one's, and
standing the short glass beyond the tall one along the line running out from the
point below the camera lets the tall glass's stretched outline cover it
entirely.

**A glass with no pixels fills no slot.** The queries read the picture, and what
the picture holds where the hidden glass stands is the tall glass in front of it
and the table around it. Nothing in that part of the picture came from the
hidden glass, so one slot is filled with the tall glass, correctly, with a
correct mask over the tall glass's pixels, and the hidden glass appears nowhere.

**Nothing in the output is wrong.** There is no low score, because the glass
that was found really is a glass. There is no impossible width either, because
the surviving pixels back-project to the tall glass's own real footprint: splay
decides which pixels exist and not where they land, so every pixel returns to
its own true place on the table. Every check prescribed above is a check on
something that was found, and there is nothing to check.

**No amount of training helps, and this can be put more strongly than "it does
not work".** Take the scene with the hidden glass, and the same scene with that
glass taken away. The renderer produces the same picture for both, pixel for
pixel. A model is a function of its input, so no model of any size, trained by
any method for any length of time, can return different answers for two
identical inputs. What differs between the two scenes left no trace in the
input, so this is a fact about the input rather than about the model, and
training cannot change facts about the input.

The second rung does not escape that, and the reason is what completion is.
**Completion extends evidence.** The model sees a boundary that stops, sees a
surface in front of where it stopped, and continues the boundary behind that
surface in the way a glass of this kind would continue. Every part of that
description begins with something in the picture: the visible sliver says where
the glass is, how wide it is, and how far the completion has to reach. Take the
sliver away and there is no boundary that stops, no partial outline to continue
and no scrap of surface to say which glass of the kind's range this is. There is
nothing to extend, and a model that extends nothing produces nothing.

A model *could* be trained to mark a glass that **might** be behind this one,
since the examiner can supply that label too, and it is worth saying what such a
model would be doing. It would be reporting where glasses tend to stand in
arrangements like this one, which is a statement about the range of arrangements
rather than about this arrangement. That is **inventing a scene rather than
reading a picture**, and it would mark a glass behind every tall glass,
including all the times there is nothing there. Trading a silent miss for a
confident invention is a bad trade where the next step is an arm moving, and it
is the trade this project's rules refuse: anything doubtful is reported, never
guessed.

What the second rung does contribute is a boundary further out. Completion needs
less of a glass than anything else in this set, so the point at which hiding
becomes complete is further away with it than without it, and a glass that would
have gone missing entirely is reported from the sliver that is left. **The
boundary moves; it does not disappear.** Beyond wherever it now sits, this
solution has nothing to say, and should say so.

![A partly covered glass still reaches the picture, so it fills a slot of its own and leaves an edge to carry on from, while a glass whose outline is swallowed whole reaches it nowhere and leaves nothing to extend, which is the rung at which completion stops.](../../images/seeing-the-glasses/a-transformer-segmenter-fine-tuned/10-where-it-stops.png)

So the completely hidden case has to be handed on, and what is handed on is not
a glass but a region: the part of the table this picture could not have seen.
Working that region out is arithmetic on splay and on the glasses that *were*
found, and going to look at it is a move of the arm. Both belong to the shared
part of the job described in [looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md), which every one of the six points at rather than
restating. This solution contributes the masks that argument starts from, and
none of the argument.

## 2. A worked example

Everything below follows from the cell's own geometry and from the design above.
It is a walk through the design rather than a record of a run, and nothing in it
is a measurement.

**The arrangement.** Five glasses of one kind stand on the table, and the camera
looks down from the top. Three of them stand clear of each other. The other two
stand much closer together than the cell's rule allows, roughly along the line
running out from the point below the camera, with the taller one nearer that
point, so splay stretches the taller one's outline across part of the shorter
one. In the picture their two outlines join into one region with no seam along
it.

**What the first rung would return.** The queries work over the whole picture,
so the two close glasses occupy two different slots, and the joined region is
never considered as one thing. Five slots come back filled, and because the
training matched slots to glasses one to one, no sixth slot reports either of
the close pair a second time and nothing has to discard a duplicate. The two
masks of the close pair overlap where the taller glass covers the shorter one,
and that is allowed, because each mask says "these pixels are part of me" about
a different glass. Nothing separated the two, and that is the point worth taking
away: there was never a joined region for anything to divide.

**What the first rung would still get wrong.** The shorter glass's mask stops
where the taller one begins, so it is a slice lying all to one side. Handed to
the shared arithmetic, that slice gives a width under the truth and a place off
to one side of where the glass stands, and the width is still one this kind
allows, so nothing objects. Five glasses are reported, one of them smaller than
it is and standing where it is not.

**What the second rung would return instead.** The shorter glass's mask covers
the part behind the taller one as well, so the shorter glass is a region of its
own and its visible slice is credited to it rather than absorbed into the taller
glass's region. The mask is then split: the observed part is the slice, and the
asserted part is the rest. The asserted pixels carry the taller glass's depth
readings, so they are named and the examiner leaves them out, and the place and the
width come from the slice alone. The place is good enough to send a camera to.
The width is still under the truth, and the visible fraction travelling with the
answer says so. The asserted part lies in the taller glass's own shadow, where
the camera could not see, so nothing is claimed where the camera had a clear
view, and neither prescribed check has anything to refuse.

**What the flag then buys.** Because the visible fraction is low, the reported
width plans and does not grip. The arm goes round to the side, stands back at
the measuring standoff and looks level, and from there nothing is in front of
the shorter glass, so its two masks coincide and its footprint is measured
rather than asserted. The completion decided **where to look**, and the look
from the side decides **what is true**.

**Now the case neither rung answers.** Push the shorter glass directly behind
the taller one along that line, close enough that the taller one's stretched
outline covers it completely. The picture holds no pixel of it, so no slot is
filled with it and there is no sliver to extend. Four glasses are reported where
five stand, every report correct, every width legal, every score confident, and
no check fires, because every check here is a check on something that was found.
That is the case handed to the geometry.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
