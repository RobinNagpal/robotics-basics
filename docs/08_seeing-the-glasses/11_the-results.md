# The six solutions side by side

## 1. Introduction

This page is the scoreboard for the six solutions in this book. It answers one
question: given the same pictures and the same marking, how many glasses did
each method find, and how good were the masks it drew? It is written for a
reader who has already met the six, and it is the page to come back to whenever
another document claims that one method did better than another.

The six ways of turning the same pictures into the same masks are all scored on
one examiner, described in [the examiner](03_the-examiner/01_the-examiner.md).
**Every solution is run twice**, once on the ordinary arrangements the cell's
own layout rule produces and once on crowded arrangements that stand the glasses
closer than that rule allows, which is why there are two tables below rather
than one. Each run uses the same arrangements, the same three survey stations
per arrangement, the same shared arithmetic turning a mask into a place and a
width, and the same scorecard. None of the six was trained or tuned on these
arrangements.

**Each of those two runs is repeated over five separate blocks of 20
arrangements**, and the numbers below are the average of the five. Twenty
arrangements is a small sample, and a score read off one of them moves when the
arrangements change. Averaging five blocks of 20 gives 100 arrangements and
about 500 glasses per table, and the brackets beside each number say how far the
blocks spread, so a reader can see which differences are real and which are the
luck of the draw.

**The blocks measure which arrangements were drawn, not which training run was
got.** All five are scored with the same fitted weights, so nothing here says
how much a solution's score would move if it were trained again. Measuring that
would mean refitting, which is a different and much more expensive question.

**Both runs use all four kinds of glass**, not one. An arrangement holds four to
six glasses of a single kind, and the kind changes from one arrangement to the
next, so the glasses come out at roughly a quarter of each kind. Every number in
the tables below is therefore an average over the four as well as over the five
blocks, which matters because the kinds are not equally hard to outline. Section
3 gives the breakdown.

## Contents

1. [Introduction](#1-introduction)
2. [The results](#2-the-results)
3. [What the numbers mean](#3-what-the-numbers-mean)
4. [What the comparison says](#4-what-the-comparison-says)
5. [What these results do not cover](#5-what-these-results-do-not-cover)
6. [Reproducing](#6-reproducing)

## 2. The results

Each solution's own README explains its numbers; this page only sets them side
by side. [The six solutions](04_the-six-solutions/01_how-the-six-compare.md) says what each
of the six methods is.

### Spawned layouts — the spacing the cell's own layout rule gives

Every count is per 100 glasses, averaged over the five blocks, with the lowest
and the highest block in brackets. The place and the mask columns are the mean
of the five blocks' medians.

| | found per 100 | missed | merged | split | place | mask covered | mask not the glass |
|---|---|---|---|---|---|---|---|
| **floor** (exact masks) | 100.0 (100.0–100.0) | 0.0 | 0.0 | 0.0 | 6.8 mm | 100.0% | 0.0% |
| [1 rules on the table](../../code/src/08_seeing-the-glasses/01-rules-on-the-table) | **100.0** (100.0–100.0) | 0.0 | 0.0 | 0.2 | 8.3 mm | 99.1% | **0.0%** |
| [2 trained from scratch](../../code/src/08_seeing-the-glasses/02-train-from-scratch) | 64.1 (62.4–66.7) | 35.9 | 0.0 | 0.0 | **0.6 mm** | 98.3% | 1.6% |
| [3 YOLO as it downloads](../../code/src/08_seeing-the-glasses/03-yolo-zero-shot) | 6.4 (2.0–11.9) | 93.6 | 0.0 | 0.0 | 23.7 mm | 95.2% | 3.3% |
| [4 YOLO fine-tuned](../../code/src/08_seeing-the-glasses/04-yolo-fine-tuned) | **99.4** (99.0–100.0) | 0.6 | 0.0 | 0.2 | 6.6 mm | **99.7%** | 4.6% |
| [5 SAM 2 with a keeper](../../code/src/08_seeing-the-glasses/05-sam2-with-a-keeper) | 83.0 (78.0–86.1) | 17.0 | 0.0 | 0.2 | 5.6 mm | 97.2% | **0.0%** |
| [6 RF-DETR fine-tuned](../../code/src/08_seeing-the-glasses/06-rf-detr-fine-tuned) | 96.4 (94.9–98.0) | 3.6 | 0.0 | 0.0 | 6.0 mm | 96.6% | **0.0%** |

### Crowded layouts — closer than the layout rule allows

| | found per 100 | missed | merged | split | place | mask covered | mask not the glass |
|---|---|---|---|---|---|---|---|
| **floor** (exact masks) | 86.4 (82.2–88.5) | 13.6 | 0.6 | 0.6 | 0.4 mm | 100.0% | 0.0% |
| [1 rules on the table](../../code/src/08_seeing-the-glasses/01-rules-on-the-table) | 73.0 (70.3–75.5) | 27.0 | 10.7 | 1.9 | 8.7 mm | 91.9% | **0.0%** |
| [2 trained from scratch](../../code/src/08_seeing-the-glasses/02-train-from-scratch) | 74.6 (71.3–79.8) | 25.4 | 0.6 | 0.2 | 0.9 mm | 97.1% | 1.4% |
| [3 YOLO as it downloads](../../code/src/08_seeing-the-glasses/03-yolo-zero-shot) | 2.1 (0.0–4.2) | 97.9 | 0.0 | 0.0 | 39.1 mm | 96.0% | 4.9% |
| [4 YOLO fine-tuned](../../code/src/08_seeing-the-glasses/04-yolo-fine-tuned) | 72.0 (70.8–72.9) | 28.0 | 0.8 | 1.0 | **0.6 mm** | **99.2%** | 3.7% |
| [5 SAM 2 with a keeper](../../code/src/08_seeing-the-glasses/05-sam2-with-a-keeper) | 73.6 (71.9–76.6) | 26.4 | 0.0 | 0.0 | 0.8 mm | 98.3% | **0.0%** |
| [6 RF-DETR fine-tuned](../../code/src/08_seeing-the-glasses/06-rf-detr-fine-tuned) | **81.9** (77.2–86.5) | 18.1 | 1.4 | 0.4 | 0.5 mm | 97.2% | **0.0%** |

**Read the brackets before reading the ranking.** On the crowded layouts
solutions 1, 2, 4 and 5 average 73.0, 74.6, 72.0 and 73.6, and their brackets
all overlap, so those four are not separated by this test at all. Only two
statements survive it: solution 6 is ahead, and solution 3 is far behind. On the
spawned layouts the brackets are tight enough to separate everything except
solutions 1 and 4, which sit a fraction of a glass apart.

Solutions 5 and 6 can each be built two ways; the rows above are the `sam2` and
`modal` runs, which are the ways that were built. The floor is `bench/floor.py`
with the renderer's own masks, which no segmenter can improve on. Even it misses
13.6 crowded glasses per 100, because a glass standing wholly behind another is
in no picture at all, so read the crowded column against 86.4 rather than
against 100.

**Four of the six rows moved when one refusal was repaired.** Solutions 4, 5 and
6 each refused a report whose width no glass of the kind could have, and each
made that refusal on a report measured from a mask the frame had cut in half.
Handed the examiner's own exact masks, one station at a time, the kind's range
refuses 66 of 297 glass sightings and **every one of those 66 reaches the frame
edge** — the examiner refusing its own perfect masks. `masks_to_glasses` now says
whether a mask reached the picture's edge and the three solutions read it before
refusing: 92 → 99, 76 → 81 and 90 → 96 found on spawned layouts, 66 → 73,
71 → 73 and 74 → 78 on crowded ones. Solution 1 gained the width check its own
document prescribes and never had, which is where its two rows come from: 28 of
101 crowded glasses with 21 merged reports before it, 71 with 10 after.

## 3. What the numbers mean

**Found, missed, merged, split, false.** *Found* is how many distinct real
glasses got a report, judged by the pixels of the mask rather than by where the
report said the glass was. *Missed* is a real glass that got no report at all,
and it is the count to watch hardest: a split glass announces itself and a
merged pair looks like one large glass, but a missed glass leaves no trace
anywhere in the run.

**Position error.** How far a reported place sits from where the glass really
stands. **This number saturates**, which is why the floor row is in both tables: the
shared arithmetic is deliberately insensitive to a ragged mask edge, so two
quite different masks can give almost the same place. [How a mask becomes a
record](12_how-a-mask-becomes-a-record.md) says why. A solution at the floor is
not a good solution so much as one whose remaining error is not its fault.

**Mask covered, mask not the glass.** How much of the real glass the mask
covered, and how much of the mask was not that glass. These are the
measurements that separate methods when the places cannot. The first falls when
an outline loses a thin stem; the second rises when an outline leaks onto the
table or swallows a neighbour. Both are medians over glasses, measured in the
picture the mask was drawn in.

**Those two numbers are the place where averaging over four kinds hides
something**, so it is worth opening up once. The table below gives how much of
the glass the mask covered at the middle glass, kind by kind, on the spawned
layouts, for the written rule and for the fine-tuned model.

| kind | rules on the table | the same model, fine-tuned |
|---|---|---|
| straight | 99.5% | 99.7% |
| tapered | 100.0% | 99.8% |
| short stemmed | 88.7% | 99.7% |
| stemmed | 86.6% | 99.8% |

The written rule covers the two kinds with no stem almost completely and loses
an eighth of the two kinds with one, because what a bowl-only outline really
misses is the foot and the sliver of stem beside it. The fitted model has no
such gap. Neither of those facts is visible in the single figure of 98.9 per
cent against 99.8, which is why each solution's README breaks the measurement
down by kind.

## 4. What the comparison says

**The written rule and the fitted network fail in opposite directions.**
Solution 1 finds every glass the layout spaces, in every one of the five blocks,
which no other solution manages. On the crowded layouts the only thing standing
between its one grouping distance and a merged report is the check on the width,
and that check does not always hold: it recovers 73.0 glasses per 100 against
the 86.4 any method could find, at the price of 10.7 reports per 100 still
covering two glasses and a place 8.7 mm from the truth against the floor's 0.4
mm, because a cut drawn where the dots divide is not where the glasses divide.
Solution 2 merges almost nothing and misses a third of the glasses on the easy
layouts, because a glass whose middle falls outside the picture casts votes that
land nowhere — a limit of the voting design rather than of its training.

**Borrowed weights carry the names, not the shapes.** Solution 3 finds 6.4
glasses per 100 with nothing merged, split or false: it locates a few objects
and calls them sports balls and frisbees. Continuing its training on this cell
and cutting the vocabulary to one class is solution 4, and the gap between the
two — 6.4 against 99.4 — is the measurement of what that training bought. That
gap is far larger than either solution's spread across blocks, which is what
makes it the one comparison in the book that this test could not have got wrong.

**Four of the six are not separated on crowded tables, and saying so is the
point of running five blocks.** Solutions 1, 2, 4 and 5 average 73.0, 74.6, 72.0
and 73.6 glasses per 100, and every one of those four has a block somewhere
between 70 and 80, so the order they come out in is the order the arrangements
happened to fall. Solution 2 has the widest spread of any solution anywhere,
71.3 to 79.8, and on one block it beats every other method on the table. Only
solution 6, at 81.9, sits clear of the group.

**The two mask numbers disagree about who is best, and that is the useful
result.** Solution 1's masks never claim a pixel that is not glass at the middle
glass, because a pixel reaches a mask only by standing above the table; the
fitted and borrowed models all claim a thin margin around the glass, from 1.4 to
4.6 per cent, because a learned outline follows a shape coarsely. Neither habit
is visible in the places at all, which is why the mask is measured separately.

## 5. What these results do not cover

- **Not Gazebo.** The pictures come from the examiner's own renderer,
  [`bench/render.py`](../../code/src/08_seeing-the-glasses/bench/render.py),
  which uses the wrist camera's lens and the cell's own survey stations, but not
  the simulator. The arm never moves, and no inverse kinematics or motion
  planning is checked.
- **Opaque glasses and clean depth.** No noise, no reflections, no
  transparency, which flatters the methods built on the depth reading.
- **One table, one light.** Nothing about the rendering is varied, so a model
  fitted here is free to use the renderer's own constants as a clue, and no
  number on this page would show it.
- **Nothing about hidden glasses.** Every solution here reports only what some
  picture held. Recovering a glass no picture held is
  [a shared step of its own](02_the-problem/02_looking-again-at-what-was-hidden.md).
- **Not how much a retrained model would move.** The five blocks change which
  arrangements a solution is shown, not which weights it was given. Four of the
  six were fitted once, and whether a second training run would land in the same
  place is a question these numbers cannot answer.

## 6. Reproducing

Run these from `code/src/08_seeing-the-glasses/`, the folder that holds this
book's Makefile and its pixi environment. One block of 20 arrangements is one
run, and `--from-seed` says which block.

```
pixi run python bench/floor.py --scenes 20 --from-seed 10000
pixi run python 01-rules-on-the-table/run.py --scenes 20 --from-seed 10000
pixi run python 01-rules-on-the-table/run.py --scenes 20 --from-seed 10000 --crowded
```

The five blocks on this page are `--from-seed 10000`, `10020`, `10040`, `10060`
and `10080`, and the same two lines run each of the other five solutions. Every
seed at or above 10000 is held out, so a block may be chosen anywhere in that
range without any training having seen it.

Then average the blocks:

```
pixi run python bench/average_blocks.py
pixi run python bench/average_blocks.py --crowded
```

The fitted solutions need their training step before any of this, and each
solution's own README says which.

← [RF-DETR-Seg, fine-tuned here — how it compares](10_a-transformer-segmenter-fine-tuned/06_how-it-compares.md) · [How a mask becomes a record](12_how-a-mask-becomes-a-record.md) →
