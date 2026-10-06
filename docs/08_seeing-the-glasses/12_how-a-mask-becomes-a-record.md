# How a mask becomes a record

Every solution in this book returns masks, and every scorecard reports places
and widths. This document is the step in between: the arithmetic the examiner
runs on a mask to turn it into the record the problem asks for. It is here, at
the end, rather than in the examiner's own document, because **nothing in the
comparison depends on it**. The step is the same for all six solutions, so no
solution can win by measuring more cleverly or lose by measuring worse, and a
reader following the comparison can take it on trust.

Read it if you want to know why a place can be right while an outline is poor,
why a mask that claims pixels the camera never saw has to say which ones, or
why the place error stops telling the six apart long before the masks do.

## Contents

1. [A pixel and a depth reading are a point in the room](#1-a-pixel-and-a-depth-reading-are-a-point-in-the-room)
2. [Why the axis comes from the top of the glass](#2-why-the-axis-comes-from-the-top-of-the-glass)
3. [Why the width is a percentile and not the widest point](#3-why-the-width-is-a-percentile-and-not-the-widest-point)
4. [Why a mask that asserts pixels must say which ones](#4-why-a-mask-that-asserts-pixels-must-say-which-ones)
5. [What it costs: the place stops telling methods apart](#5-what-it-costs-the-place-stops-telling-methods-apart)

## 1. A pixel and a depth reading are a point in the room

A pixel on its own says only a direction: the camera was looking that way when
it recorded that pixel. The depth reading beside it says how far along that
direction the surface was, and the camera's own pose says where the direction
starts. Those three together are a point in the room. Turning a pixel back into
a point this way is called **back-projection**, because it runs a camera's own
projection backwards.

So a mask, which is a set of pixels, becomes a cloud of points standing in the
room. Everything below is a question about that cloud. A mask with fewer than a
hundred usable pixels is not enough to fit anything to, and the examiner says so
rather than returning a number nobody should trust.

## 2. Why the axis comes from the top of the glass

The obvious thing to do with the cloud is to take its middle. That is wrong
here, and the reason is the same splay that makes this book's problem hard.

A camera looking straight down sees a glass's rim nearer than its base, so the
rim is drawn thrown outwards, away from the point directly below the lens. The
cloud a mask back-projects to is therefore not a column standing over the
glass's footprint. It leans. Its middle sits off to one side of where the glass
really stands, and it leans further for a taller glass and for a glass further
out in the frame, so the error is different for every glass in the picture.

The rim does not lean, because the rim is the part the camera sees most nearly
face on and the part whose own points really do ring the glass's axis. So the
examiner takes the points within 8 mm of the highest point in the mask, and
their middle is the axis. That band is narrow enough to be rim and wide enough
to hold a useful number of points, and it works from whichever side the camera
stood.

## 3. Why the width is a percentile and not the widest point

With the axis fixed, the width is how far the cloud reaches from it. Taking the
largest distance would make the answer depend on one point, and one point is
exactly what a stray depth reading gives you. So the examiner takes the 95th
percentile of those distances instead: the reach that 95 of every 100 points
fall inside.

This is a deliberate choice to be insensitive. A ragged mask edge moves the
largest distance a long way and the 95th percentile hardly at all, which is what
makes a width comparable between a solution that outlines tightly and one that
outlines coarsely.

## 4. Why a mask that asserts pixels must say which ones

One solution in this book can be asked for a glass's whole silhouette,
including the part standing behind another glass that nobody saw. That is useful
and it breaks the arithmetic above unless it is handled, because **the depth
reading at an asserted pixel does not belong to that glass**. It belongs to
whatever stood in front. Back-project it and you get a point on the wrong
object, and the axis is dragged towards it.

So a mask that asserts pixels has to name them, and the examiner leaves their
depth readings out rather than guessing a value. What that is worth was
measured. Over the 681 partly hidden glasses of five blocks of crowded arrangements,
naming the asserted pixels puts the place **12.2 mm** out at the middle glass,
and feeding them in puts it **42.7 mm** out.

The same mistake made at scale is worse than that figure suggests, and the
examiner's own floor shows it. The run below hands the renderer's perfect masks
to the arithmetic twice. The two runs use **exactly the same pixels**; the only
difference is whether the asserted ones were named.

| exact masks, crowded arrangements, per 100 glasses | found | missed | merged | mask covered | mask not the glass |
|---|---|---|---|---|---|
| asserted pixels named and left out | 86.4 | 13.6 | 0.6 | 100.0% | 0.0% |
| asserted pixels fed in | **72.4** | **27.6** | **10.7** | 100.0% | 0.0% |

Both score perfectly on both mask measurements, because the masks are identical
and both are perfect. Fourteen glasses in every hundred are lost anyway. That is why the examiner
measures what the arithmetic made of a mask as well as the mask itself: a
comparison of pixels alone cannot see this at all.

## 5. What it costs: the place stops telling methods apart

Everything above is chosen to be forgiving, and forgiving has a price. Because
the axis comes from a band of rim and the width from a percentile, two quite
different masks can produce almost the same place.

The examiner measures how much room is left by running the renderer's own masks
through the same arithmetic, which is the **floor of error**. On the ordinary
arrangements that floor is 6.8 mm at the median and 46.6 mm at worst, averaged
over five blocks, with perfect masks and nothing left to improve. A solution within a hair of that is
not a good solution so much as one whose remaining error is not its fault.

So the place is not the measurement that ranks the six. [What the examiner
measures](03_the-examiner/04_comparing-the-outputs.md#6-how-good-was-the-mask) says which
measurement does: how many glasses were found, missed, merged, split or falsely
reported, and the two numbers comparing a mask against what the camera really
saw of its glass. Those are pixel against pixel, and they separate methods that
the places cannot.

← [The six solutions side by side](11_the-results.md)

← [The six solutions side by side](11_the-results.md)
