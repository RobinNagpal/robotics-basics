# A worked example

This page follows this solution through one arrangement of glasses. It also
follows the hard case, a glass that is completely hidden. An example that shows
only the easy case would teach the wrong lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

The worked example below includes a hidden glass, so this section first says
what this solution can do about one. A glass that is covered completely leaves
no pixel in any picture. No method that reads pictures can find it. [Looking
again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md#3-step-one-where-could-a-glass-have-been-hiding)
explains why, and it describes the shared answer: work out the wedge of table
each found glass hides, and report any patch nobody saw.

That arithmetic fits this solution well, because this solution already works in
room distances. For every glass it found, it knows the place, the width and the
height. It also knows where the camera is. That is all the wedge arithmetic
needs, and it never looks at the picture again.

![The same two glasses stand the same distance apart in both panels: lying along one line out from the camera, the taller one's outline is thrown far enough outwards to cover the shorter one completely, and lying across that line the two are drawn clear of each other and both are found.](../../images/seeing-the-glasses/rules-on-the-table/02-hidden-from-above.png)

The arithmetic has one limit. **It starts from the glasses it found.** So it
cannot see a glass hidden behind a glass that was itself hidden. A badly grouped
glass also gives a wrong wedge.

The next section shows this arithmetic at work, together with the grouping.

## 2. A worked example

This example follows one arrangement through the whole method, including the
hidden-glass arithmetic from the last section. It describes what happens rather
than giving measurements. Its two key relations were chosen as worst cases.

Six glasses of the kind with the widest range of sizes stand in the glass zone.
Call them G1 to G6. The table below says where each one stands and how large it
is for its kind. Read each row as a comparison with the others, because no
glass's size is written down in this cell.

| | where it stands | how big, as this kind goes |
| --- | --- | --- |
| G1 | middle of the zone, a little to the near side | large: tall and wide |
| G2 | the far corner of the zone, out past G1 on a diagonal | middling |
| G3 | the near corner on the other side | middling |
| G4 | out along the far edge, away from G2 | middling |
| G5 | the near corner on G1's side | middling |
| G6 | on the same diagonal as G1, beyond it | the smallest the kind allows |

Two relations matter. **G1 and G2 are the closest legal pair.** Their centres are
only just further apart than the problem promises. They also lie on a diagonal
running away from the middle of the zone, which is the direction splay pushes
things.

**G6 is the smallest glass, and it stands just beyond the largest one, on the
same diagonal.** It stands closer to G1 than the layout rule allows, as in the
examiner's crowded family. A spaced layout cannot hide a glass at all, as [what
is asked
for](../02_the-problem/01_what-is-asked-for.md#a-glass-can-be-missing-from-the-picture-altogether)
shows.

The camera goes to one survey station above the zone and points straight down.
One picture from there covers more table than the zone is wide. So every glass's
place is inside the frame. That does not mean every glass's *outline* is inside
it, as the next part shows.

### What grouping in the picture would return

This part shows what a method that groups touching pixels would get. G1 stands a
short way out from the point below the camera. Splay pushes its outline further
out along the diagonal, towards G2.

G2 stands much further out, so splay pushes it even more. Part of G2's outline
runs off the edge of the picture. G1's outline reaches the near edge of what is
left of G2's. The two outlines touch. So grouping touching pixels would give one
patch for two glasses.

Two outlines can meet in two different ways, and it helps to keep them apart.

- **With the frame edge.** Take two glasses of similar height on one line out
  from the point below the camera. Splay pushes the further one more, so the gap
  between them in the picture **grows**. They can meet only when one is partly
  out of frame. This is how G1 and G2 meet here.
- **Without the frame edge.** If the nearer glass is much taller than the
  further one, splay pushes the near outline out much more. Then the gap between
  them in the picture **closes**.

![The same two places on the table drawn twice: with both glasses the same height the gap between their outlines grows from 30 mm on the table to 45 mm in the picture, and with the near one at the tall end of the kind and the far one at the short end the two outlines run together over 78 mm.](../../images/seeing-the-glasses/rules-on-the-table/05-why-two-outlines-meet.png)

So whether two outlines meet depends on their heights as much as on their
places. For two glasses of the same height, splay pushes them apart, not
together.

The merged patch of G1 and G2 is several times wider than any glass of this
kind. So the picture *can* tell that something is wrong. It cannot tell *what*
is wrong: one huge object, two glasses or three.

The table can tell. The next part shows how.

### What grouping on the table returns

This part runs the same arrangement through this solution's grouping. On the
table, G1 and G2 are far from touching. The strip of bare table between them is
several times wider than the grouping distance. The chain cannot cross it, so G1
and G2 come back as two groups. Every other visible pair is further apart, so it
is separate too. The picture gave four patches. The table gives five groups, and
five masks go to the examiner.

The table below has one row per group. It shows what the dots looked like and
what mask the group gives.

| | the group | the mask it gives |
| --- | --- | --- |
| G1 | a full disc of dots | a complete outline, less the band at the base |
| G2 | a partial disc: its top ran past the frame edge | the near part of the glass only |
| G3 | a full disc of dots | a complete outline, less the band at the base |
| G4 | a full disc of dots | a complete outline, less the band at the base |
| G5 | a full disc of dots | a complete outline, less the band at the base |

Four of the five masks are as good as this method can make them. Each one lacks
only the thin band at the base. [The masks are what this
contributes](02_the-code.md#2-the-masks-are-what-this-contributes) explains
that band.

G2 is the interesting one. Part of G2 is not in this picture, so its mask covers
only the near part. The width of its group still looks ordinary for this kind.
**That is the danger**, because nothing in one picture objects to it. The
defence is that the camera visits more than one station. Each station cuts G2
along a different line. If two stations put G2 in the same place, the fit
followed the glass and not the frame edge. The design says a group that only
one station found should be reported as doubtful. It may be fine, but it was
seen only once.

### And the glass that is not in the list at all

Now count the rows in that table. There are five, but six glasses stand on the
table.

G6 is missing, and nothing noticed. G1 is tall and stands nearer the point below
the camera. G6 is the smallest glass and stands just beyond it. Splay pushes
G1's outline far out over G6 and covers it completely. G6 leaves no pixels. So
there is no group, no mask and no warning.

Look at what the checks had to work with. The width check needs a fitted width,
and there is none. The residual needs dots, and there are none. The station
check needs a group, and there is none. **Every check is a check on something
that was found.**

Now run the other branch, which never looks at the pixels. G1 was found, so its
place, width and height are known. Its wedge of hidden table can be worked out.
G6 stands inside that wedge. The arithmetic does not know G6 is there. But it
does know that **a patch big enough for the kind's smallest glass lies inside
that wedge, and nobody saw it.** So it reports that patch as unsearched.

The next station settles it. From there, the point below the camera has moved,
so G1's wedge points somewhere else and G6 is in plain view. The two stations
together see all six glasses.

So the arithmetic did not find G6. **It turned a run that reports five glasses
into a run that reports five glasses and one place it did not look.** The first
is wrong and silent. The second is incomplete and says so.

Hidden glasses are one limit. Glasses that touch are another, and the last part
covers them.

### The case the rule cannot answer

This last part covers glasses that stand too close, the case the grouping cannot
separate. The examiner's spaced arrangements never draw it, but the crowded ones
do. [Pushing crowded glasses
apart](../../09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md)
is about exactly this case.

Suppose two glasses stand closer than the cell allows. The strip between them is
narrower than the grouping distance, so the chain crosses it. They come back as
one group. Now the width check does the work. The fitted width is about twice
what one glass can be. So the group is split in two. If both halves have widths
the kind allows, the answer is two glasses. Distance has failed here, and the
width check recovers the answer.

Now suppose the two glasses touch. There is no strip of bare table at all. So
they are always one group, and the answer rests only on the width. The group is
too wide, so it is cut in two. The two parts are believed only if both have
allowed widths. With three touching in a row, the cut repeats. But each cut is a
straight line through a patch with no gap in it. The line falls where the dots
divide, not where the glasses do. So the borders between masks are guesses. The
more cuts it took, the less the places are worth.

**Touching glasses leave no strip of bare table, and that is the limit of this
method.** That is why [the job of pushing the glasses
apart](../../09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md)
exists.

![Two glasses are brought closer together in three steps: while the strip of bare table between them is wider than the grouping distance, distance alone separates them; once the strip is narrower than that, only the check on the width recovers them; and when they touch there is no strip left for either to work on.](../../images/seeing-the-glasses/rules-on-the-table/02-touching-is-the-limit.png)

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
