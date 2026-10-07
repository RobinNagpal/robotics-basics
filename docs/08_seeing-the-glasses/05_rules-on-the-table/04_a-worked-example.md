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
picture. [Looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) is the shared
answer every solution relies on, and **no method that reads pictures can do
better**, because the arrangement with the hidden glass and the same arrangement
with it removed produce the same picture, pixel for pixel. What follows is only
what is this solution's own.

**This is the one solution that can say where a glass could have been hiding**,
and it can because it already works in the room rather than in the picture. It
holds, for every glass it found, where that glass stands, how wide it is and
how tall it is, and it holds the camera's own position in the same distances.
From those it can work out which pieces of table no ray from the lens reached,
without looking at the picture's contents again.

Two properties of splay make that region cheap to write down rather than
expensive to search for. A taller glass is thrown further out than a shorter
one at the same distance, so the only things that can cover a glass are the
glasses taller than it. And splay scales a glass's distance from the point
below the camera and its radius by the same factor, so the angle it covers does
not change with height: **the region a glass hides is a wedge**, and height
decides only where along that wedge the outline starts and stops. The union of
those wedges, with the frame edge contributing a ring outside everything, is
the blind region, and a patch of it matters only if it is wide enough to hold
the smallest footprint the kind allows.

![The same two glasses stand the same distance apart in both panels: lying along one line out from the camera, the taller one's outline is thrown far enough outwards to cover the shorter one completely, and lying across that line the two are drawn clear of each other and both are found.](../../images/seeing-the-glasses/rules-on-the-table/02-hidden-from-above.png)

One limit belongs with it. **The arithmetic reasons from the glasses it found,
so a glass hidden behind a glass that was itself hidden is outside its reach**,
and a badly grouped glass casts a badly computed wedge. Neither arises while no
glass is hidden from every station, and both arrive together the day one is.

## 2. A worked example

This example follows one arrangement through the whole method. It is described
in terms of what happens rather than what is measured, and the two relations
that make it interesting were both chosen as worst cases rather than drawn at
random.

Six glasses of the widest-ranging kind stand in the glass zone. Call them G1 to
G6. The table below says where each one stands and how large it is for its kind;
read every row as a relation to the others rather than as a measurement, because
no glass's size is written down anywhere in this cell.

| | where it stands | how big, as this kind goes |
| --- | --- | --- |
| G1 | middle of the zone, a little to the near side | large: tall and wide |
| G2 | the far corner of the zone, out past G1 on a diagonal | middling |
| G3 | the near corner on the other side | middling |
| G4 | out along the far edge, away from G2 | middling |
| G5 | the near corner on G1's side | middling |
| G6 | on the same diagonal as G1, beyond it | the smallest the kind allows |

The first relation that matters is that **G1 and G2 are the closest pair and
they are only just legally apart**, so their centres are barely further apart
than the smallest distance this problem promises. They also lie along the
diagonal running away from the middle of the zone, which is the direction splay
throws things.

The second is that **G6 is the smallest glass of the kind and it stands beyond
the largest one, on that same diagonal**. G1 is tall, so splay throws its
outline a long way out along the diagonal, and G6 is short, so splay barely
moves it at all.

The camera goes to one survey station above the zone, lifted to the survey
height and pointed straight down. One picture from there covers more table than
the glass zone is wide, so no glass's own place is outside the frame. That does
not mean no glass's *outline* is, as the next paragraphs show.

### What grouping in the picture would return

G1 stands a short way out from the point directly below the camera, on the
diagonal towards the far corner, so splay throws its rim outwards along that
diagonal and G1's outline does not sit over G1. It leans out past it, towards
G2.

G2 stands much further out along the same diagonal, so splay throws its rim
outwards too, and by more, because the further a glass stands from the point
below the camera the further splay pushes it. That is where the trouble comes
from. G2's outline is pushed so far out that part of it runs past the edge of
the picture, and only the near part of it is drawn. G1's outline, leaning
outwards, reaches the near edge of what is left of G2's. The two outlines touch,
so collecting touching pixels into patches would give one patch where two
glasses stand, and the picture would show four patches for five visible glasses.

It is worth being careful about *why* this pair merges, because two outlines can
meet by either of two routes and the two are worth keeping apart.

The first route needs the frame edge. When two glasses of similar height stand
along the same line out from the point below the camera, splay pushes both
outwards and pushes the further one more, so the distance between them in the
picture **grows** rather than closes, and they meet only when one of them is
partly out of frame. That is G1 and G2's route here.

The second route needs no frame edge at all. If the nearer glass is much taller
than the further one, splay pushes the near one's outline out by a large factor
and the far one's by a small factor, so the distance between them in the picture
**closes**.

![The same two places on the table drawn twice: with both glasses the same height the gap between their outlines grows from 30 mm on the table to 45 mm in the picture, and with the near one at the tall end of the kind and the far one at the short end the two outlines run together over 78 mm.](../../images/seeing-the-glasses/rules-on-the-table/05-why-two-outlines-meet.png)

So whether two outlines meet is a question about the difference in their heights
as much as about where they stand, and the first guess — that splay pushes
neighbouring glasses together — is the wrong way round for two glasses of one
height.

The merged patch would run from G1's near edge all the way to the corner of the
frame, several times wider than any glass of this kind can be. So the picture
*can* tell that something is wrong. What it cannot tell is *what* is wrong —
whether one impossibly wide object, or two glasses, or three — because the one
thing that would separate them was thrown away the moment the scene became
pixels.

### What grouping on the table returns

On the table, G1 and G2 are nowhere near touching. Take the distance between
their centres, subtract half of each glass, and what is left is a strip of bare
table several times wider than the grouping distance. The chain cannot cross a
strip of nothing, so G1 and G2 come back as two separate groups. Every other
pair in the arrangement stands further apart than that pair, so every other pair
is separate too. Five groups come out of the one picture that would have given
four patches, and five masks go back to the examiner.

The table below has one row per group: what the dots on the table looked like,
and the mask that group hands back.

| | the group | the mask it gives |
| --- | --- | --- |
| G1 | a full disc of dots | a complete outline, less the band at the base |
| G2 | a partial disc: its top ran past the frame edge | the near part of the glass only |
| G3 | a full disc of dots | a complete outline, less the band at the base |
| G4 | a full disc of dots | a complete outline, less the band at the base |
| G5 | a full disc of dots | a complete outline, less the band at the base |

Four of the five masks are as good as this method can make them, and the one
thing missing from each is the thin band at the base that the depth test
removed. That is the shortfall [the masks are what this
contributes](02_the-code.md#2-the-masks-are-what-this-contributes) describes, and it is the same
band on all four.

G2 needs its footnote, and the footnote is the interesting part. Part of G2 is
simply not in this picture, so its group is short of dots and its mask covers
only the near part of the glass. The width a circle fitted to that group would
report is perfectly ordinary for this kind, and **that is precisely the
danger**: the arithmetic of one picture has nothing to object to. What makes it
safe is that the camera visits more than one station. Each station stands
somewhere different, so each one cuts G2 along a different line, and two
stations that put G2 in the same place have fitted it to the glass rather than
to the edge of a picture. A group that only one station found has nothing to
check against, so the design prescribes reporting it as doubtful — not because
it is probably wrong, but because it has been seen once.

### And the glass that is not in the list at all

Count the rows of that table again. There are five, and six glasses are standing
on the table.

G6 is missing, and nothing above noticed. G1 is tall and wide and stands nearer
the point below the camera, while G6 is the kind's smallest glass standing
further out along the same diagonal. Splay throws G1's outline a long way out
along that diagonal and barely moves G6's, so G1's outline sweeps over G6 and
covers it completely. G6 contributes no pixels, so there is no group, no mask
and no flag.

Look at what the checks had to work with. The width check compares a fitted
width against the kind's limits, and there is no fitted width. The residual
measures how well a circle explains a group's dots, and there are no dots. The
rule about stations agreeing asks how many stations found a group, and no group
exists to ask about. **Every check is a check on something that was found.**

Now run the other branch, the one that never looks at the pixels. G1 was found,
so where it stands, how wide it is and how tall it is are all known. Its wedge
of hidden directions can be computed, and so can the stretch of that wedge its
own outline covers. G6's position falls inside that stretch. The arithmetic does
not know that G6 is there, and it cannot, but it does know that **a patch of
table large enough to hold the kind's smallest glass lies inside that wedge and
would have left no trace.** So the patch is reported as unsearched.

The next station then settles it. From there the point below the camera has
moved, so G1's wedge has swung away and G6 is plainly visible. The union of the
two stations holds all six glasses, and the unsearched patch from the first
station is closed by the second.

That is what the arithmetic bought, and it is worth being precise about it. It
did not find G6. **It made the difference between a run that reports five
glasses and a run that reports five glasses and one place it had not looked.**
The first of those is wrong and silent. The second is incomplete and says so.

### The case the rule cannot answer

The examiner never draws the next case, because it always keeps the glasses a legal
distance apart. The rule still has to behave sensibly in it, because [pushing
crowded glasses
apart](../../09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md)
is about exactly this.

If two glasses stood closer together than the cell allows, the strip of bare
table between them would be narrower than the grouping distance, the chain would
cross it, and they would come back as one group. This is where the width check
earns its place: the circle fitted to that group would come out about twice as
wide as a glass of this kind can be, so the group would be rejected as one glass
and split in two, two circles would be fitted to the halves, and if both landed
inside the kind's range the answer would be two glasses. That answer is
recovered not by distance, which had already failed, but by the check on the
width.

If the two glasses were actually touching, there would be no strip of bare table
at any grouping distance, so distance would have nothing left to say. It would
be one group, always, and everything about the answer would then rest on the
width: the group is too wide for one glass, so it is cut in two, and the two
parts are believed only if both come back widths the kind allows. With three
touching in a row the cut repeats, and the arithmetic can still arrive at three
parts that each fit — but every one of those cuts is a straight line through a
patch of dots with no gap in it, drawn where the dots happen to divide rather
than where the glasses do, so where the masks meet is a guess and the places
read off them are worth less the more cuts it took. That is the handover to
[the job of pushing the glasses
apart](../../09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md),
and it is the honest edge of this method.

![Two glasses are brought closer together in three steps: while the strip of bare table between them is wider than the grouping distance, distance alone separates them; once the strip is narrower than that, only the check on the width recovers them; and when they touch there is no strip left for either to work on.](../../images/seeing-the-glasses/rules-on-the-table/02-touching-is-the-limit.png)

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
