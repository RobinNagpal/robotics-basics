# The examiner — the same question for every answer

## 1. Introduction

This problem is answered six different ways, and six answers are only
comparable if they were asked the same question and marked the same way. The
examiner is the program that does both. It works in four steps, and the whole
of this document is those four steps in order. It **arranges** glasses on the
table and photographs them from three camera stations. It **hands** exactly
those three pictures to whichever solution is being tried. It **takes back**
what that solution returns. Then it **marks** the answer against what it knows
it put out.

By the end of this page you will know what the examiner puts on the table, what
it gives a solution, what it keeps to itself, and what has to come back. The
last part of the page follows one real arrangement through all of it, so that
you see the pictures that go in and the answer that comes out. How the marking
itself works is the next page, [comparing the
outputs](02_comparing-the-outputs.md).

Read this before any of the solution documents, because every one of them
assumes it.

## Contents

1. [Introduction](#1-introduction)
2. [Why there is an examiner at all](#2-why-there-is-an-examiner-at-all)
3. [What the examiner draws](#3-what-the-examiner-draws)
4. [What a solution is given](#4-what-a-solution-is-given)
5. [What the examiner keeps to itself](#5-what-the-examiner-keeps-to-itself)
6. [What must come back](#6-what-must-come-back)
7. [One arrangement, from the table to the answer](#7-one-arrangement-from-the-table-to-the-answer)
8. [Where to go next](#8-where-to-go-next)

## 2. Why there is an examiner at all

Without one, each method would arrive with its own arrangements and its own
idea of a good answer, and nothing could be concluded by putting their results
side by side. The examiner exists to remove every difference between the six
except the one being studied.

It does that by holding three things fixed. The **input** is the same pictures
from the same arrangements, in the same order. The **output** is the same record
per glass, produced by the same final step. The **marking** is the same set of
measurements, computed the same way. Everything a solution is free to change
sits between the input and the output, and that is exactly the part we want to
compare.

![The examiner draws the arrangement, parks the camera at three stations, renders a grey picture, a depth reading, a camera pose and an id image, and hands over only the first three; the solution turns those into one mask per glass and contributes nothing else; and the examiner then turns each mask into a place and a width, matches it to a real glass and counts.](../../images/seeing-the-glasses/the-examiner/03-what-the-examiner-does.png)

The comparison that follows from this is sharper than it sounds. Two of the six
solutions use the same model from the same library, starting from the same
downloaded weights, and one of them has had its training continued on this
cell's pictures. That training also cuts the borrowed list of everyday
categories down to a single class, because a model cannot be trained towards
this cell's labels while still being asked which household object it is looking
at — so the two changes cannot be had separately. Because the examiner holds
everything else still, nothing varies between those two that the training did
not bring, which makes the gap between them a measurement of what training
bought.

## 3. What the examiner draws

**It draws the arrangements, not Gazebo.** The real simulator would produce a
slower picture of the same thing, and a few hundred arrangements are needed, so
the examiner renders them directly from the cell's own glass shapes, the cell's own
table layout and the wrist camera's real lens. Nothing about the geometry is
invented for convenience.

**Each arrangement holds four to six glasses of one kind**, and the kind changes
from one arrangement to the next so that all four kinds are met in turn. The
glasses stand far enough apart never to touch.

**There are two families of arrangement.** The ordinary one spaces the glasses
as the cell's spawner would. The crowded one pushes them as close as the cell
allows, which is where the methods separate most, because crowding is what
creates both the merge and the complete hiding.

![In the ordinary family the glasses stand the guaranteed 150 mm apart between centres, and in the crowded family they stand at a third to two thirds of that, which is where two outlines run together in the picture and where one glass can cover another completely.](../../images/seeing-the-glasses/the-examiner/03-two-families.png)

**Arrangements are split into a training half and a test half**, by the number
used to draw them. Anything a method is fitted on comes from below the dividing
line, and everything it is marked on comes from above it, so no method is ever
tested on an arrangement it learned from.

## 4. What a solution is given

For each arrangement, the camera is parked at several overlapping stations above
the glass zone, looking straight down. The overlap matters: a glass cut off at
the edge of one station's picture sits well inside another's.

![One picture from the survey height covers more table than the glass zone is wide but less than a station can be credited with, because the second picture of the pair slides sideways and a glass has to be inside far enough not to be cut off, so the zone takes three stations 93 mm apart and anything lost at one edge lands well inside its neighbour.](../../images/seeing-the-glasses/the-examiner/03-three-stations.png)

From each picture a solution may read three things:

- the **grey picture**, shaded from how far away each surface is;
- the **depth reading** at every pixel;
- the **camera's pose**, which the arm knows from its own joint encoders.

That is the whole input. It is the same for all six, and it is handed over by
the examiner rather than fetched by the solution, so no solution can quietly read
anything else.

![From each picture a solution may read the grey picture shaded from how far away each surface is, the depth reading at every pixel, and the camera pose the arm knows from its own joint encoders, and nothing else reaches it.](../../images/seeing-the-glasses/the-examiner/03-what-a-solution-is-given.png)

## 5. What the examiner keeps to itself

Every picture also carries an **id image**: at each pixel, which glass that
pixel shows, or nothing. The examiner renders it alongside the depth and never
gives it to a solution at run time.

That image is the examiner's whole power, and it is used for two different jobs
which are worth keeping apart.

**As the answer key**, it is how marking works. Because the examiner knows which
glass owns each pixel, it can decide what a returned mask is really a picture
of.

**As a training label**, it is what a fitted method learns from — but only from
the training half of the arrangements. A method may be *trained* on id images
and is never *run* on them. Any method that read one while answering would not
be answering this problem.

![The id image says which glass owns each pixel, and the examiner uses it for two separate jobs: as the answer key when it marks any solution, and as a training label for a fitted solution, available only from the arrangements below the dividing line and never while a solution is answering.](../../images/seeing-the-glasses/the-examiner/03-what-the-examiner-keeps.png)

## 6. What must come back

One record per glass, holding its mask pixels, its place on the table, a rough
width of its footprint, and **whether the picture held the whole glass** — that
last one because a glass at the edge of a station's frame shows only part of its
footprint, so a width read off it is part of a width, and a solution refusing a
report on its width has to be able to tell which it has. The examiner observes it;
what to do about it is the solution's own. Beside those records come the two
honest statements [the problem](../02_the-problem/01_what-is-asked-for.md) asks for: which glasses could not be
separated and why, and which parts of the table could not have been seen at
all. Neither is a list of glasses, and the examiner counts both rather than
treating a reported doubt as a missing answer.

![A solution supplies the mask pixels and whether the picture held the whole glass, the examiner computes the place and the width from the mask itself, and the two honest statements that come beside the records are counted as reported doubt rather than as answers that never arrived.](../../images/seeing-the-glasses/the-examiner/03-what-must-come-back.png)

**The solution picks the pixels, and the examiner does the measuring.** A mask
is a set of pixels, and three things are enough to turn it into a place on the
table and a width: the grey picture says which pixels there are, the depth
reading beside each pixel says how far away that bit of glass was, and the
camera's pose says where the camera was standing while it looked. Those are the
same three things the examiner handed over in section 4, and the examiner runs
that step itself, the same way for every solution.

So the final answer — which glass is where, and how wide — depends on nothing
but which pixels the solution chose. No solution can win by measuring more
cleverly, and none can lose by measuring worse. **The method that scores best is
simply the one whose masks pin down the exact position and size of the glasses**,
because choosing the pixels is the only thing any of the six contributes.
[How a mask becomes a record](../12_how-a-mask-becomes-a-record.md) sets out the
arithmetic of that shared step for a reader who wants it, and nothing in the
comparison depends on reading it.

One thing follows from this and is worth saying plainly here, because it would
otherwise come up in all six solution documents. **No model in this book
produces a pose.** Models produce masks. The place comes afterwards, from the
depth readings and the camera's pose, by arithmetic — and a glass standing
upright on a flat table has no orientation left for anybody to find.

## 7. One arrangement, from the table to the answer

Everything above says what happens in general. This section says it once on a
real arrangement, number 10046, which holds six stemmed glasses. Every picture
below was made by running the examiner's own code on that arrangement, and every
number on them was measured rather than chosen.

It begins with the glasses standing on the table. This is what is really there,
which only the examiner knows, and it is what everything afterwards is marked
against.

![Arrangement 10046 holds six stemmed glasses standing inside the glass zone, with the three camera stations marked above them, and this is the record of what is really there that only the examiner holds.](../../images/seeing-the-glasses/the-examiner/03-example-on-the-table.png)

The camera then takes one picture from each of the three stations, and these
three pictures are the input. They are not interchangeable. **Station 1 holds
glass 1 whole and loses glass 6 entirely**: glass 6's outline falls inside the
frame, and every one of those pixels shows glass 4, whose bowl is thrown out
over it. Station 2 holds no glass whole, because every one of the six reaches a
frame edge. Station 3 holds glass 2 whole. That is the overlap doing its work:
what one station loses, another holds.

![The same arrangement from each of the three stations, with the glasses keeping their numbers, a green outline where the picture holds a glass whole and a red one where it is cut off at the frame edge, and glass 6 absent from station 1 altogether.](../../images/seeing-the-glasses/the-examiner/03-example-three-pictures.png)

One of those three pictures, taken apart, is the whole of what a solution is
given, plus the one thing it is not. The grey picture and the depth reading go
to the solution with the camera's pose. The id picture does not.

![Station 2's picture as its three parts: the grey picture shaded from how far away each surface is, the depth reading at every pixel, and the id picture saying which glass owns each pixel, which the examiner keeps.](../../images/seeing-the-glasses/the-examiner/03-example-what-one-station-gives.png)

Handed that, a solution returns one mask per glass, and those masks are the
output. The ones below are the real output of the written rule, run on station
2's grey picture and depth reading and told only that the glasses are stemmed.
**Every one of the six lost the band at the base of its glass**, which is where
that rule stops being sure; and not one of them claimed a pixel that was not its
glass. That is the habit of a rule written by hand, and it is the kind of thing
the next page measures: it claims too little and never too much.

![The mask the written rule returned for each of the six glasses in station 2's picture, with the part of the glass it covered, the part it missed, and the per-glass coverage below each one.](../../images/seeing-the-glasses/the-examiner/03-example-the-masks.png)

That is one full pass through the examiner: glasses on a table, three pictures
handed over, six masks handed back. What the examiner then does with those six
masks — how it decides which real glass each one is talking about, and how good
an answer it is — is [comparing the outputs](02_comparing-the-outputs.md).

## 8. Where to go next

- [Comparing the outputs](02_comparing-the-outputs.md) — how the examiner marks
  what came back, worked through on the masks above.
- [The problem](../02_the-problem/01_what-is-asked-for.md) — what is asked for, and the two difficulties.
- [Looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) — the shared part that
  recovers a glass no picture held.
- [The six solutions](../04_the-six-solutions/01_how-the-six-compare.md) — what each method puts between the
  input and the output.

← [Looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) · [Comparing the outputs](02_comparing-the-outputs.md) →
