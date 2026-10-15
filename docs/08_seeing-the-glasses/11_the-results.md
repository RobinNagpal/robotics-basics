# The six solutions side by side

## 1. Introduction

This page is the scoreboard for the six solutions in this book. It answers one
question. With the same pictures and the same marking, how many glasses did
each method find, and how good were its masks? It is for a reader who has
already met the six. Come back to it whenever a page claims one method did
better than another.

All six are scored by one examiner, described in [the
examiner](03_the-examiner/01_the-examiner.md). Each solution is run on two kinds
of arrangement. Spawned arrangements use the cell's own layout rule. Crowded
arrangements stand the glasses closer than that rule allows. So there are two
tables below. [Every solution is tested
twice](03_the-examiner/01_the-examiner.md#every-solution-is-tested-twice-once-on-each-family)
explains the two kinds. None of the six was trained or tuned on these
arrangements.

Each kind of run is repeated over five blocks of 20 arrangements. The numbers
below are the average of the five blocks. That gives 100 arrangements and about
500 glasses per table. The brackets beside a number give the lowest and highest
block. They show which differences are real and which are luck.

All five blocks use the same trained weights. So the blocks measure which
arrangements were drawn. They do not measure how much a score would move if a
model were trained again.

Both runs use all four kinds of glass. Each arrangement holds one kind, so about
a quarter of the glasses are of each kind. Every number below is an average over
the four kinds. The kinds are not equally hard, and [what the numbers
mean](#3-what-the-numbers-mean) shows where that matters.

## Contents

1. [Introduction](#1-introduction)
2. [The results](#2-the-results)
3. [What the numbers mean](#3-what-the-numbers-mean)
4. [What the comparison says](#4-what-the-comparison-says)
5. [What these results do not cover](#5-what-these-results-do-not-cover)
6. [Reproducing](#6-reproducing)

## 2. The results

The introduction set out how the runs were made. This section gives what they
scored. Each solution's own README explains its numbers. [The six
solutions](04_the-six-solutions/01_how-the-six-compare.md) says what each method
is.

### Spawned layouts — the spacing the cell's own layout rule gives

In both tables, every count is per 100 glasses, averaged over the five blocks.
The lowest and highest block are in brackets. The place and the two mask columns
are the mean of the five blocks' medians.

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

**Read the brackets before you read the ranking.** On crowded layouts, solutions
1, 2, 4 and 5 average 73.0, 74.6, 72.0 and 73.6. Their brackets all overlap.
So this test does not separate those four at all. Solution 2 has the widest
spread, 71.3 to 79.8. On one block it beats every other method. Only two
statements hold. Solution 6 is ahead, and solution 3 is far behind. On spawned
layouts the brackets are narrow. They separate every pair except solutions 1
and 4, which are less than one glass apart.

The floor row is the examiner's own exact masks, from `bench/floor.py`. No
segmenter can do better. Even the floor misses 13.6 crowded glasses per 100,
because a glass wholly behind another is in no picture. So read the crowded
table against **86.4**, not against 100. Solutions 5 and 6 can each be built two
ways. The rows above are the `sam2` and `modal` runs, which are the ways that
were built.

**Four of the six rows changed when one refusal was fixed.** Solutions 4, 5 and
6 refused any report whose width no glass of the kind could have. Each of them
refused some reports measured from a mask the picture's edge had cut in half.
The examiner tested this with its own exact masks, one station at a time. The
width range refused 66 of 297 glass sightings, and **all 66 touched the edge of
the picture**. Now `masks_to_glasses` says when a mask reaches the edge, and the
three solutions check that before they refuse. On spawned layouts, found glasses
rose from 92 to 99, 76 to 81 and 90 to 96. On crowded layouts they rose from 66
to 73, 71 to 73 and 74 to 78. Solution 1 also gained the width check its own
pages describe but it never had. Before that, it found 28 of 101 crowded glasses
in one block, with 21 merged reports. After it, it found 71, with 10 merged.

The next section explains what each column measures.

## 3. What the numbers mean

The tables above use seven columns. This section says what they measure.
[Comparing the outputs](03_the-examiner/04_comparing-the-outputs.md) defines
each one in full.

**Found, missed, merged, split.** *Found* counts real glasses that got a report,
judged by the mask's pixels. *Missed* counts real glasses with no report. Watch
it most closely, because a missed glass leaves no sign anywhere in the run.

**Place.** This is how far a reported place is from where the glass stands. It
stops improving at the floor. So it cannot rank the six. [The best possible
answer](03_the-examiner/04_comparing-the-outputs.md#7-the-best-possible-answer-and-the-trap-below-it)
and [what it costs](12_how-a-mask-becomes-a-record.md#5-what-it-costs-the-place-stops-telling-methods-apart)
explain why.

**Mask covered, mask not the glass.** The first is how much of the glass the
mask covered. The second is how much of the mask was not that glass. These two
numbers separate methods when the places cannot.

Averaging over four kinds hides something in the mask covered column. The table
below shows it. Each row is one kind of glass on spawned layouts. Each cell is
how much of the glass the mask covered, for the median glass.

| kind | rules on the table | the same model, fine-tuned |
|---|---|---|
| tapered | 99.9% | 99.7% |
| straight | 99.5% | 99.6% |
| short stemmed | 89.1% | 99.7% |
| stemmed | 82.1% | 99.6% |

The written rule covers the two kinds with no stem almost fully. It loses about
a sixth of the two kinds with a stem. Its outline of the bowl misses the foot
and the thin stem beside it. The fine-tuned model has no such gap. The single
figures, 99.1% against 99.7%, do not show this. That is why each solution's
README breaks the measure down by kind.

With the columns explained, the next section says what the comparison shows.

## 4. What the comparison says

The columns above can now be read across the six. This section gives the
comparisons the book relies on.

**The written rule and the network trained from scratch fail in opposite ways.**
Solution 1 finds every spawned glass in all five blocks. No other solution does.
On crowded layouts it finds 73.0 of the 86.4 possible. But 10.7 reports per 100
still cover two glasses. Its place is 8.7 mm out, against the floor's 0.4 mm.
This is because its cut falls where the depth points divide, not where the
glasses divide. Solution 2 merges almost nothing. But it misses a third of the
spawned glasses. A glass whose middle is outside the picture gets no votes.
[Solution 2's own comparison](06_a-network-trained-from-scratch/06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains this.

**Borrowed weights bring names, not shapes.** Solution 3 finds 6.4 glasses per
100. It finds a few objects and calls them sports balls and frisbees. Solution 4
is the same model, trained further on this cell with one class. It finds 99.4.
The two differ only in that training. So the gap, 6.4 against 99.4, measures
what the training gave. That gap is far larger than either spread across blocks.
So this is the one comparison in the book this test could not get wrong.

**Finding shapes can be borrowed, but naming them cannot.** Solutions 3 and 5
both use a borrowed model without changing it. They are not the same model.
Solution 3 trusts its model's own names to decide which outlines are glasses.
Solution 5 ignores names. A small keeper trained here decides which outlines are
glasses. Solution 3 finds 6.4 and solution 5 finds 83.0 on spawned layouts. On
crowded layouts they find 2.1 and 73.6. [SAM 2 with a
keeper](09_a-foundation-model-with-a-keeper/01_what-it-is.md) explains the
keeper.

**The model design matters once training is equal.** Solutions 4 and 6 are
trained the same way, on the same pictures, with one class and the same free
labels. Only the model design differs. Solution 4 wins on spawned layouts, 99.4
against 96.4. Solution 6 wins on crowded layouts, 81.9 against 72.0. The
brackets do not overlap in either table, so both gaps are real.

**The two mask numbers disagree about which is best.** Solution 1's masks
never claim a pixel that is not glass, at the median glass. A pixel joins its
mask only if it stands above the table. Solutions 5 and 6 also score 0.0%. The
other trained and borrowed models claim a thin margin round the glass, from 1.4
to 4.9 per cent. The place column does not show this habit at all. That is why
the mask is measured on its own.

The next section lists what these numbers do not test.

## 5. What these results do not cover

The comparisons above hold only inside this test. This section lists what the
test leaves out.

- **It is not Gazebo.** The pictures come from the examiner's own renderer,
  [`bench/render.py`](../../code/src/08_seeing-the-glasses/bench/render.py). It
  uses the wrist camera's lens and the cell's survey stations, but not the
  simulator. The arm never moves. Arm motion is not tested.
- **The glasses are opaque and the depth is clean.** There is no noise, no
  reflection and no transparency. This helps the methods that rely on depth.
  [What is asked for](02_the-problem/01_what-is-asked-for.md) explains this
  assumption.
- **There is one table and one light.** Nothing about the rendering changes. A
  trained model could rely on the renderer's fixed settings, and no number here
  would show it.
- **Hidden glasses are not covered.** Every solution reports only what some
  picture held. Finding a glass no picture held is [a shared step of its
  own](02_the-problem/02_looking-again-at-what-was-hidden.md).
- **Retraining is not covered.** The five blocks change the arrangements, not
  the weights. Four of the six were trained once. These numbers cannot say
  whether a second training run would score the same.

The last section says how to make these numbers again.

## 6. Reproducing

The tables above can be made again with a few commands. Run them from
`code/src/08_seeing-the-glasses/`, the folder that holds this book's Makefile
and pixi environment. One block of 20 arrangements is one run. `--from-seed`
picks the block.

```
pixi run python bench/floor.py --scenes 20 --from-seed 10000
pixi run python 01-rules-on-the-table/run.py --scenes 20 --from-seed 10000
pixi run python 01-rules-on-the-table/run.py --scenes 20 --from-seed 10000 --crowded
```

The five blocks on this page use `--from-seed 10000`, `10020`, `10040`, `10060`
and `10080`. The same two lines run each of the other five solutions. No
training ever sees a seed of 10000 or more. So you may choose a block anywhere in
that range.

Then average the blocks:

```
pixi run python bench/average_blocks.py
pixi run python bench/average_blocks.py --crowded
```

The trained solutions need their training step first. Each solution's own
README says which step.

← [RF-DETR-Seg, fine-tuned here — how it compares](10_a-transformer-segmenter-fine-tuned/06_how-it-compares.md) · [How a mask becomes a record](12_how-a-mask-becomes-a-record.md) →
