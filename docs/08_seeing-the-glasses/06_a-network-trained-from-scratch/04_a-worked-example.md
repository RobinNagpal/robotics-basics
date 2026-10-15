# A worked example

This page follows this solution through one crowded arrangement, with real
numbers. First it looks at hidden glasses, because an example that shows only
the easy case teaches the wrong lesson.

## Contents

1. [When the glasses are completely hidden](#1-when-the-glasses-are-completely-hidden)
2. [A worked example](#2-a-worked-example)

## 1. When the glasses are completely hidden

A glass can be fully hidden behind another. Then it gives no pixel to any
picture. No method that reads pictures can find it.
[Looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md)
explains why, and gives the shared answer. This section covers only what is
special to this solution.

**This solution is good at a glass that is only partly hidden.** Other methods
must find something between two glasses, such as a gap or a seam. This one
does not. Each glass pixel votes for its own glass's middle. So even a thin
crescent of a glass still votes. Its votes do not need to touch each other.

![When a tall glass's outline is thrown far enough outwards to swallow a shorter neighbour standing at the closest separation the cell allows, not one vote mentions the covered glass; swing the same pair off the line out from the camera and the crescent that survives casts few votes, but they pile up almost exactly where that glass really stands.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-above.png)

**A fully hidden glass raises no alarm.** This solution's warnings are
measurements of votes. A hidden glass has no votes to measure. The vote map
simply shows one pile where two glasses stand.

![Looking level the near glass's outline covers the far one whole with no outward throw needed, and the single pile of votes left behind is tight, well filled and a believable width, so nothing about it looks wrong; step the far glass off the line of sight and the strip that appears votes for its own middle.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-hidden-from-the-side.png)

![Four pictures from the top as the camera slides outwards show the covered glass sitting outside the frame in every one of them, so from the top this solution loses a glass only where its picture never reached, and a short sideways move of the camera ends even that.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-above.png)

![Looking from the side, the far glass contributes not one pixel while it stands on the line of sight, however much further back it is put, and only sideways movement brings it back — in less of a slide than a survey station already makes between its two pictures.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-hidden-from-the-side.png)

Hidden glasses are the limit. The next section shows the case this solution is
built for.

## 2. A worked example

The last section showed what this solution cannot see. This section follows
one crowded arrangement that it can solve.

**What is on the table.** Two glasses of one kind stand much closer than the
layout rule allows. They are between a third and two thirds of 150 mm apart.
There is still a little bare table between their rims.

**What the picture does.** The two outlines join in the picture from above.
A flood fill finds **one** shape covering both glasses. That shape is much
wider than any glass of this kind. A width check can see that something is
wrong. But a class map cannot say where to cut.

**What the votes do.** The pixels are still joined. The votes are not. Each
glass's pixels point at their own middle, so the votes form two piles. At the
closest crowded spacing, 45 mm, the two middles are 17 to 28 pixels apart in
the half-size picture. The exact gap depends on how tall the glasses are. The
counting step removes 16 pixels around each middle it takes. So the second pile
survives. For two tall glasses the margin is large. For two of the shortest,
it is one pixel. Both piles are tight and have plenty of votes. A circle
fitted to each pile has a believable width. **The result is two glasses and
two masks, from pixels that never came apart.**

**The case that defeats the votes.** Now stand one glass mostly behind
another. Only a crescent down one side of it is seen. It casts only a few of
the votes it should. All of them come from the same crescent, so they are all
wrong in the same direction. The pile lands off the true middle, and it is
more spread out than a normal pile. The low vote count is the built alarm, and
it fires. The wide spread is the second warning, which is only a design. Both
are measurements of the votes. The pair is then reported as one the arm could
not separate, with its reason. This problem accepts that as an answer.

![The less of a glass reaches the picture the fewer votes it casts and the further its votes sit from their own peak, so a short count and a wide spread are two separate warnings, both of them measurements of the votes rather than the network's opinion of itself.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-too-few-votes.png)

The next page lists what this solution needs before it can do any of this.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
