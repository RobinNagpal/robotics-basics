# The six solutions side by side

## 1. Introduction

This page is the scoreboard for the six solutions in this book. It answers one
question: given the same crowded tables and the same marking, how many of them
did each method clear, and what did it knock over on the way? It is written for
a reader who has already met the six, and it is the page to come back to
whenever another document claims that one method did better than another.

The six ways of pushing crowded glasses apart so that each one can then be
picked up are all tested on the same 50 tables holding 251 glasses, 193 of
which have no room at the start. Every solution is given the same tables,
spends the same push budget, and is judged by the same scorecard, which is
described in [the examiner](01_the-problem/03_the-examiner.md).
None of them saw these tables while it was being built or fitted. Every number
on this page is read from a solution's own scorecard: the totals from its
`results.json`, and the single-table numbers further down from the file of
per-table rows that is written beside it.

## Contents

1. [Introduction](#1-introduction)
2. [The results](#2-the-results)
3. [The six films, all of the same table](#3-the-six-films-all-of-the-same-table)
4. [What the comparison says](#4-what-the-comparison-says)
5. [What these results do not cover](#5-what-these-results-do-not-cover)
6. [Reproducing](#6-reproducing)

## 2. The results

Read the table a column at a time rather than a row at a time, because no
single column decides which solution is better. Each row is one solution and
each column is one measurement, and the figure in bold is the best any of the
six achieved in that column. The two columns that matter most are the ones on
the right of the middle: a table the run left in a state the cell should never
reach, and a glass knocked over, which is the one failure this cell cannot take
back.

| | tables done | tables wrong | glasses racked | toppled | pushes | thinking per push |
|---|---|---|---|---|---|---|
| [1 one fixed nudge](../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge) | **33** | **0** | 195 | **0** | 213 | fast |
| [2 geometry ranked](../../code/src/09_pushing-the-glasses-apart/02-geometry-ranked) | 31 | **0** | 185 | **0** | 229 | fast |
| [3 imitation, ACT](../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations) | 3 (3–6) | 1 (0–5) | 68 (67–82) | 1 (0–5) | 643 (589–668) | fast |
| [4 a world model](../../code/src/09_pushing-the-glasses-apart/04-a-world-model) | 31 | 1 | **202** | 1 | **114** | middling |
| [5 SmolVLA as it downloads](../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads) | 0 (0–0) | 5 (5–6) | 56 (52–57) | 6 (5–8) | 754 (740–766) | slow |
| [6 SmolVLA fine-tuned](../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned) | 4 (3–4) | 38 (37–39) | 77 (74–85) | 46 (38–49) | 400 (386–461) | slow |

A table is **done** when every glass on it was picked up, and **wrong** when
the run ended in a state the cell should never reach. Solutions 3, 5 and 6 are
run three times each, because they sample while they answer and a single run of
one of them is a single draw. For those three the figure shown is the middle run
and the brackets beside it are the least and the most, so a reader can see which
differences between rows are larger than the wobble within one. Solutions 1, 2
and 4 are the same every time and carry no brackets.

Read the brackets before reading the ranking. Solution 6 racks between 74 and 85
glasses and solution 3 between 67 and 82, so those two are not separated by this
test. What is not in doubt is the toppling: solution 6 knocks over between 38
and 49 glasses on every run, and solutions 1 and 2 never knock over any.

The thinking column is deliberately coarse. Every time on this page was
measured while the machine was busy with other work, and the same solution
timed twice minutes apart gave answers a factor of two apart. The column is
good for the order of magnitude and nothing finer: the two geometry solutions
think for a small fraction of a second, the world model for longer, and the two
that run a large borrowed model take about a second for every push.

## 3. The six films, all of the same table

The scorecard above is fifty tables added up, and a sum hides what a run
actually looks like. So each of the six was also filmed clearing one single
table, and the same table for all six, which makes the films comparable in the
same way the numbers above are comparable. Each film is recorded from the
simulator, runs at three times real speed and has no sound.

The table filmed is number 10003 of the fifty. It was chosen because it stands
for the whole run rather than because it flatters anybody: it holds five
glasses, which is the average of the fifty, and on it every one of the six
reaches the outcome it reaches most often over all fifty. Choosing it needed
[one row per table](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures)
in the scorecard, because a total over fifty tables cannot say which single
table is representative.

Read the table below as the films' own scorecard, in the same columns as the
scorecard above but counting one table instead of fifty. The last column is how
far the glasses were moved in total, which is the measurement that separates
solutions reaching the same outcome.

| | film | outcome | racked | toppled | pushes | glasses moved |
|---|---|---|---|---|---|---|
| 1 one fixed nudge | [30 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/01-one-fixed-nudge.mp4) | done | 5 of 5 | **0** | 7 | 145 mm |
| 2 geometry ranked | [33 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/02-geometry-ranked.mp4) | done | 5 of 5 | **0** | 7 | 288 mm |
| 3 imitation, ACT | [16 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/03-imitation-from-demonstrations.mp4) | incomplete | 1 of 5 | **0** | 16 | 9 mm |
| 4 a world model | [19 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/04-a-world-model.mp4) | done | 5 of 5 | **0** | **2** | 70 mm |
| 5 SmolVLA as it downloads | [32 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/05-smolvla-as-it-downloads.mp4) | incomplete | 1 of 5 | **0** | 16 | none |
| 6 SmolVLA fine-tuned | [10 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/06-smolvla-fine-tuned.mp4) | wrong | 1 of 5 | 1 | 8 | 1 mm |

Each film also sits at the top of its own solution's first page, where what
happens in it is described push by push. Taken together the six rows are this
book's argument in miniature. **Solutions 1 and 2 reach the same outcome by
different amounts of work**, because the ranked geometry moves the glasses twice
as far to finish the same table. **Solution 4 finishes it in two pushes**,
which is what being able to predict where a glass will stop is worth.
**Solutions 3 and 5 spend the table's whole budget of sixteen pushes and move
the glasses almost nothing**, because the jaw is stopped on the way down in one
case and never reaches the glasses at all in the other. **Solution 6 is the only
one that ends the table wrong**, with a glass on its side, which is the price of
acting competently enough to reach a glass and not competently enough to miss
it.

One warning belongs with these films, and it applies to solutions 3, 5 and 6.
Those three draw their actions rather than computing them, so filming one of
their tables on its own does not reproduce the row the scorecard holds for it:
the earlier tables of the run have already moved the policy's random numbers
along. [The examiner](01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why, and the films of those three were made by running the tables
before them first.

The films show what each solution does, and the next section says what the
comparison between them means.

## 4. What the comparison says

**Nothing learned beats the written rules here, and that is the result.** The
fixed nudge finishes the most tables, and the only solution that racks more
glasses is the world model, which does it in half the pushes. Everything built
on a borrowed model finishes almost nothing.

**The learning that paid attacked the quantity the geometry gets wrong.** The
geometry computes exactly how much room a push would gain, because that is
arithmetic on the destination, and it predicts badly where a pushed glass will
actually stop, because that needs the friction and the weight distribution that
nobody in this cell has measured. Solution 4 fits a model of the second and
wins; solution 2 fits a model of the first and loses to the printed rule it was
meant to improve. **So the useful question is not whether to learn, but which
quantity is worth learning.**

**Fitting a borrowed model made it worse, not better.** Solution 5 racks a fifth
of the glasses and finishes no table, because about nine of its pushes in ten
touch nothing at all: the trajectories hold the jaw well above the glasses.
Solution 6 fits that same model on this cell's own demonstrations, and it learns
the height a push happens at without learning where to put the jaw down. Two
thirds of its pushes are blocked coming down, and it topples 46 glasses where
the geometry topples none. **Fitting bought enough competence to act and not
enough to act safely, which on this scorecard is worse than inaction** — and
that is why solution 6 has far more wrong tables than the model that can barely
act at all.

**Imitation fails for a different reason, and the reason was measured rather
than guessed.** Solution 3 learns from solution 2's own recorded pushes, so its
teacher is in the room. It places the start of a push roughly right and gets
the heading about thirty degrees out, and the jaw then meets a neighbour on the
way down. Fitting it on four times the demonstrations removed the memorising
but not the averaging, which says the shortfall is the policy averaging over
pushes that disagree, not a shortage of examples.

**Only the geometry never breaks anything.** Solutions 1 and 2 topple no glass
at all, and every solution that learns something topples at least one. A
toppled glass is the one failure this cell cannot take back, so the two columns
on the right of the table matter more than the one on the left.

## 5. What these results do not cover

- **Not Gazebo.** The physics is MuJoCo, standing in for the simulator the rest
  of the project uses, because a learned approach needs thousands of pushes.
- **A guessed friction.** No solution is told what the table's friction is, and
  the ones that reason about toppling use a believed range instead. The examiner
  knows the true value and never shares it.
- **No early abort.** [Pushing without
  toppling](01_the-problem/05_pushing-without-toppling.md) argues
  for stopping a push while the glass is still moving. Nothing here implements
  it, and solution 6 is what its absence costs.
- **One kind of glass per table**, as the cell's own layout produces.

## 6. Reproducing

```
pixi run python 01-one-fixed-nudge/run.py
```

The same line works for each of the other five, run from
`code/src/09_pushing-the-glasses-apart/`. The ones that fit something need
their training step first, and each solution folder's own README says which
step that is and what it costs.

Two things are worth knowing before running one. A run can be told to start at
a chosen table rather than the first, which is how the films above were made,
and every solution refuses to overwrite its committed scorecard unless it is
running the official fifty tables from the official first seed. That guard
matters more than it sounds: without it a short run of some other fifty tables
would quietly replace the result this page quotes, and nothing would say so.

← [The same foundation model, fine-tuned here — how it compares](09_the-same-model-fine-tuned-here/06_how-it-compares.md)
