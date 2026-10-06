# An example of the input

## 1. Introduction

The previous page, [the examiner](01_the-examiner.md), said in general terms
what the examiner puts on the table and what it hands over. This page does the
same thing once, on one real arrangement, so that you can see the input rather
than read a description of it.

The arrangement is the examiner's own number 10038. It is one of the
arrangements held back for testing, so it is what the cell's spawner really
produces rather than anything built for a diagram. It holds four glasses, which
is the smallest number the spawner draws and the number that makes a picture of
every glass readable. Every picture on this page was made by running the
examiner's own code on that arrangement, and every number was measured rather
than chosen.

By the end of this page you will have seen the three things that go in: the
glasses standing on the table, the three pictures the three camera stations take
of them, and one of those pictures taken apart into the parts a solution is
given. What comes back is the next page, [an example of the
output](03_an-example-of-the-output.md).

## Contents

1. [Introduction](#1-introduction)
2. [The glasses on the table](#2-the-glasses-on-the-table)
3. [The three pictures](#3-the-three-pictures)
4. [What one station hands over](#4-what-one-station-hands-over)
5. [Where to go next](#5-where-to-go-next)

## 2. The glasses on the table

Everything starts with what is really there. The picture below is the
arrangement seen from straight above, before any photograph has been taken.
Each shaded circle is the part of the table one glass covers, the cross at its
middle is where that glass stands, and the dotted rectangle is the glass zone,
which is the 320 mm by 360 mm part of the table that glasses are put on. Only
the examiner knows this, and it is what everything reported later is marked
against.

![Arrangement 10038 seen from straight above: four stemmed glasses inside the glass zone, with the three camera stations marked on a line down the middle of it.](../../images/seeing-the-glasses/the-examiner/03-example-on-the-table.png)

All four glasses are **stemmed glasses**, because an arrangement holds four to
six glasses of a single kind and the kind changes from one arrangement to the
next. A stemmed glass in this cell may be 165 to 230 mm tall with a bowl 60 to
100 mm across. The table below gives each glass the number the examiner's
answer key gives it, and that number is used in every picture that follows.
Read across a row for how tall that glass is, how wide its bowl is, and where it
stands on the table.

| glass | height | bowl across | stands at |
|---|---|---|---|
| 1 | 228 mm | 82 mm | x = 424 mm, y = −276 mm |
| 2 | 174 mm | 84 mm | x = 591 mm, y = −273 mm |
| 3 | 189 mm | 80 mm | x = 477 mm, y = −116 mm |
| 4 | 172 mm | 81 mm | x = 321 mm, y = −142 mm |

The closest pair here stands 158 mm apart, against the 150 mm the spawner
guarantees, so no glass touches another. Glass 1 is the tall one, and that
matters later: the taller a glass is, the further its rim leans outwards in a
picture taken from above, and the more of its neighbour it can cover.

The three black dots on the line down the middle of the picture are where the
camera stands to take the three pictures. They are 93 mm apart, all 450 mm above
the table, and all looking straight down.

## 3. The three pictures

The camera then takes one picture from each of those three stations, and those
three pictures are the whole of what the examiner hands over for this
arrangement. They are not interchangeable, which is the reason there are three
of them rather than one.

![The same arrangement from each of the three stations, with the glasses keeping their numbers, a green outline where the picture holds a glass whole and a red one where the glass is cut off at the frame edge.](../../images/seeing-the-glasses/the-examiner/03-example-three-pictures.png)

Read it by the colour of each outline. A green outline is a glass the picture
holds whole; a red one is a glass that runs off the edge of the frame. **Station
3 is the only one that holds any glass whole**, and the glass it holds is glass
3. At stations 1 and 2 every one of the four glasses reaches a frame edge, and
at station 3 the other three still do.

That sounds like a poor result and is not, because the stations overlap on
purpose. A glass cut off at the edge of one station's picture sits further
inside the next station's, so what one picture loses another holds. The examiner
later keeps one report per glass and takes it from the station that stood
nearest that glass, which is how the overlap is cashed in.

One more thing is visible at station 1 and is worth naming, because it is the
difficulty the whole book is about. **Glass 4 keeps only 730 pixels in that
picture and loses 966 of them to glass 1**, whose bowl is thrown out over it. No
method can recover a pixel that was never taken, so a glass standing behind
another is read as a smaller glass in the wrong place by every one of the six
solutions.

## 4. What one station hands over

A picture is not one thing. The examiner renders three arrays for every station,
and hands over two of them.

![Station 2's picture as its three parts: the grey picture, the depth reading at every pixel, and the id image, which the examiner keeps.](../../images/seeing-the-glasses/the-examiner/03-example-what-one-station-gives.png)

The **grey picture** is 320 by 240 pixels with one shade per pixel, bright where
the surface is near the lens. It is shaded by the examiner rather than by any
solution, so all six are handed the same bytes.

The **depth reading** gives the distance to whatever that pixel shows. Here the
nearest rim reads 222 mm below the camera and the bare table reads 450 mm, which
is the survey height. This is the array that turns a pixel into a point in the
room, and so it is the array the places all come from.

Those two go to the solution, together with the **camera's pose**, which for
station 2 is x = 480 mm, y = −260 mm, 450 mm up, looking straight down. The arm
knows that from its own joint encoders rather than from the picture. Those three
things are the whole input, and the examiner hands them over rather than letting
a solution fetch them, so no solution can quietly read anything else.

The **id image** is the third array and it stays with the examiner. At each
pixel it says which glass that pixel shows, or nothing; 74 per cent of this
picture is table. It is the answer key, and a solution that read it while
answering would not be answering this problem at all.

## 5. Where to go next

- [An example of the output](03_an-example-of-the-output.md) — what the written
  rule hands back when it is given the three pictures above.
- [The examiner](01_the-examiner.md) — the same arrangement in general terms,
  for every arrangement rather than this one.
- [Comparing the outputs](04_comparing-the-outputs.md) — how what comes back is
  marked.

← [The examiner — the same question for every answer](01_the-examiner.md) · [An example of the output](03_an-example-of-the-output.md) →
