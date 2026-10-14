# The six solutions side by side

## 1. Introduction

This page is the scoreboard for the six solutions in this book. It answers one
question: given the same crowded tables and the same marking, how many of them
did each method clear, and what did it knock over on the way? It is written for
a reader who has already met the six, and it is the page to come back to
whenever another document claims that one method did better than another.

The six ways of pushing crowded glasses apart so that each one can then be
picked up are all tested on the same 50 tables holding 251 glasses, 203 of
which have no room at the start. Every solution is given the same tables,
spends the same push budget, and is judged by the same scorecard, which is
described in [the examiner](01_the-problem/03_the-examiner.md).
None of them saw these tables while it was being built or fitted. Every number
on this page is read from a solution's own scorecard: the totals from its
`results.json`, and the single-table numbers further down from the file of
per-table rows that is written beside it.

All six rows were measured with the same hand, and that hand is a real product
rather than a shape invented to suit the task. It is a **Robotiq 2F-85**, held
turned on its side, because held the ordinary way it is 139 mm across its
fingers and the glasses on these tables stand 150 mm apart at the closest.
Every figure on this page was measured with that hand, and the four solutions
that learn something were trained again against it first.

## Contents

1. [Introduction](#1-introduction)
2. [The results](#2-the-results)
3. [The six films, all of the same table](#3-the-six-films-all-of-the-same-table)
4. [Travel, and why that column is a trap](#4-travel-and-why-that-column-is-a-trap)
5. [What the comparison says](#5-what-the-comparison-says)
6. [What these results do not cover](#6-what-these-results-do-not-cover)
7. [Reproducing](#7-reproducing)

## 2. The results

Read the table a column at a time rather than a row at a time, because no
single column decides which solution is better. Each row is one solution and
each column is one measurement, and the figure in bold is the best any of the
six achieved in that column. The two columns that matter most are **tables
wrong** and **toppled**: a table the run left in a state the cell should never
reach, and a glass knocked over, which is the one failure this cell cannot take
back.

| | tables done | tables wrong | glasses racked | toppled | pushes | travel | thinking per push |
|---|---|---|---|---|---|---|---|
| [1 one fixed nudge](../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge) | 14 | **1** | 107 | **1** | **173** | 0.87× | 93 ms |
| [2 geometry ranked](../../code/src/09_pushing-the-glasses-apart/02-geometry-ranked) | 14 | **1** | 107 | **1** | 182 | 1.32× | 102 ms |
| [3 imitation, ACT](../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations) | 2 (1–3) | 11 (7–13) | 63 (51–64) | 12 (7–13) | 438 (414–497) | 0.87× | **11 ms** |
| [4 a world model](../../code/src/09_pushing-the-glasses-apart/04-a-world-model) | **20** | 19 | **146** | 20 | 221 | 1.98× | 374 ms |
| [5 SmolVLA as it downloads](../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads) | 1 (0–1) | 9 (6–10) | 48 (46–51) | 12 (10–14) | 620 (589–641) | 0.42× | 286 ms |
| [6 SmolVLA fine-tuned](../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned) | 1 (0–2) | **36** (31–36) | 56 (50–65) | **40** (33–44) | 369 (351–374) | 1.68× | 404 ms |

A table is **done** when every glass on it was picked up, and **wrong** when
the run ended in a state the cell should never reach, which in practice means a
glass lying on its side.

One word in that sentence promises more than it should, and it is worth knowing
before reading the racked column. The examiner takes a glass away as soon as the
glass has room around it. It never asks whether the cell could really have
picked that glass up. Asked about the same 251 glasses, the cell's own grip rule
finds somewhere to hold only 97 of them, and the hand has a clear way in to only
14 of every 19 the examiner says have room. So *racked* means the job this book
sets was done, not that the glass reached the rack. [What the examiner
measures](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures) gives
both figures and says where they come from. No comparison in the table above
moves because of it, because all six solutions are marked the same way. Solutions 3, 5 and 6 are run three times each, because
they sample while they answer and a single run of one of them is a single draw.
For those three the figure shown is the middle run and the brackets beside it
are the least and the most, so a reader can see which differences between rows
are larger than the wobble within one. Solutions 1, 2 and 4 are the same every
time and carry no brackets.

**The job is much harder with a real hand than it was with the invented blade,
and that is the first thing to read off the table.** 203 of the 251 glasses
begin without room, and the best of these six gets 146 of the 251 off the
table. The refusals say why. The hand is 139 mm across its fingers, so for many
glasses there is nowhere to stand it that is not already inside a neighbour,
and it cannot come lower than 75 mm, so for many others a push would tip the
glass before it slid. Neither refusal is a failure of a method. Both are the
cell telling every method that the job, as the cell is built, is partly
impossible.

Read the brackets before reading the ranking. Solution 6 racks between 50 and
65 glasses and solution 3 between 51 and 64, so those two are not separated by
this test. What is not in doubt is the toppling: solution 6 knocks over between
33 and 44 glasses on every run, and solutions 1 and 2 knock over one in fifty
tables.

The thinking column is each solution's own time, with the simulator's time
taken off, measured on an idle machine. That condition matters, because the
same runs timed while other work was on the machine reported up to three and a
half times these figures, so a compute column measured under load compares the
load rather than the methods.

## 3. The six films, all of the same table

The scorecard above is fifty tables added up, and a sum hides what a run
actually looks like. So each of the six was also filmed clearing one single
table, and the same table for all six, which makes the films comparable in the
same way the numbers above are comparable. Each film is recorded from the
simulator, runs at one and a half times real speed and has no sound.

Two details are the same in all six, and both are easy to misread. The hand
never opens while it is pushing, because this problem holds the gripper shut and
shoves the glasses with the whole closed hand. The pick-up at the end of a take
is drawn rather than simulated, because the examiner takes a glass away by
moving it off the table in one instant. [The film of the
job](01_the-problem/01_what-is-asked-for.md#2-a-film-of-the-job) explains both,
and says what the faint shell drawn around the hand is.

The table filmed is number 10025 of the fifty, and it was chosen to be
**typical rather than flattering**. The rule for choosing it was written down
before it was applied: the table had to be one where every one of the six
reaches its own commonest outcome and racks at least one glass. Exactly one
table of the fifty satisfies both, and this is it. Choosing that way needed
[one row per table](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures)
in the scorecard, because a total over fifty tables cannot say which single
table stands for the rest. It holds six glasses where the average is five, so
it is one glass above average, and that is the one way in which it is not
typical. Five of its six glasses have no room at the start, which is the usual
state of these tables.

Read the table below as the films' own scorecard, in the same columns as the
scorecard above but counting one table instead of fifty.

| | film | outcome | racked | toppled | pushes |
|---|---|---|---|---|---|
| 1 one fixed nudge | [13 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/01-one-fixed-nudge.mp4) | incomplete | 1 of 6 | **0** | **2** |
| 2 geometry ranked | [13 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/02-geometry-ranked.mp4) | incomplete | 1 of 6 | **0** | **2** |
| 3 imitation, ACT | [23 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/03-imitation-from-demonstrations.mp4) | incomplete | 1 of 6 | **0** | 14 |
| 4 a world model | [44 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/04-a-world-model.mp4) | done | **6 of 6** | **0** | 3 |
| 5 SmolVLA as it downloads | [74 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/05-smolvla-as-it-downloads.mp4) | incomplete | 1 of 6 | **0** | 16 |
| 6 SmolVLA fine-tuned | [12 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/06-smolvla-fine-tuned.mp4) | wrong | 1 of 6 | 1 | 4 |

Each film also sits at the top of its own solution's first page, where what
happens in it is described push by push. Taken together the six rows are this
book's argument in miniature. **Solutions 1 and 2 do exactly the same thing**,
making the same two pushes and racking the same glass, which is a result about
the ranked geometry rather than a coincidence: when a table bottoms out on the
hand's width and height, ordering the candidates differently changes nothing.
**Solution 4 clears the whole table in three pushes**, which is what being able
to predict where a glass will stop is worth. **Solutions 3 and 5 spend the
table's budget and rack only the glass that already had room**, because the jaw
is stopped on the way down in one case and never reaches the glasses at all in
the other. **Solution 6 is the only one that ends the table wrong**, with a
glass on its side, which is the price of acting competently enough to reach a
glass and not competently enough to miss it.

One warning belongs with these films, and it applies to solutions 3, 5 and 6.
Those three draw their actions rather than computing them, so a film of one of
their tables is one draw and not an average, and it does not have to match the
row the scorecard holds for that table.
[The examiner](01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why, and each solution's own page says how its film compares with its
scored runs on the same table.

A second warning applies to the racking at the end of every film. The examiner
takes a glass away once it has room, without asking whether the cell could have
picked it up, and the pick-up each film draws is a stand-in that says so on
screen. Asked about all 251 held-out glasses, the cell's own grip rule finds
somewhere to hold only 97 of them. No row in the table above changes because of
it, since all six solutions are marked the same way, and [what the examiner
measures](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures) gives
the breakdown.

The films show what each solution does. The next section explains the one
column of the scorecard that is easy to read backwards.

## 4. Travel, and why that column is a trap

**Travel is how far the glasses were really moved, as a multiple of the least
any legal arrangement needs.** That least is the displacement floor, which
[the target layout](01_the-problem/04_the-target-layout.md) computes from the
geometry of each table, and it comes to 3,284 mm over these fifty tables
altogether. The floor belongs to the table rather than to any method, so no
solution can go below it while doing the job.

**The column therefore means nothing on its own, and has to be read beside the
glasses racked.** A solution that never touches anything travels nothing and
scores best on it. That is exactly what the two smallest numbers are. SmolVLA
as it downloads travels 0.42 times the floor because its jaw comes down about
200 mm above the table and never reaches a glass, and the imitation policy
travels 0.87 because most of its pushes are stopped on the way down. The fixed
nudge is at 0.87 for a third reason, which is that it refuses 143 of the 251
glasses and so never spends the travel they would have needed. **None of those
three is economical. All three are simply not doing the work.**

Among the solutions that do move most of the glasses the column does separate
them. The world model spends 1.98 times the floor to rack 146 glasses, which is
the dearest work on this page and also the most of it. Solution 6 spends 1.68
to rack 56, which is the clearest bad bargain here: the fine-tuning taught it to
move decisively without teaching it where to put the jaw down, so most of that
travel is glasses being shoved somewhere unhelpful or knocked over.

## 5. What the comparison says

**The written rules are the only solutions that could be left running
unattended.** Solutions 1 and 2 each topple one glass in fifty tables and end
one table wrong. Every solution that learns something ends between nine and
thirty-six tables wrong. A glass on its side leaves shards and an arm that will
carry on moving through them, so this is not one trade-off among several. It is
the condition on using any of the rest.

**One learned solution clears many more glasses, and it breaks far more.** The
world model racks 146 against the geometry's 107, which is more than a third
again, and it topples 20 against 1. So the honest summary is not that learning
won or lost. It is that the same mechanism — predicting an outcome instead of
refusing whenever the arithmetic is unsure — is what buys the extra glasses and
what breaks the extra ones, and the two cannot be separated by tuning a
threshold. A lower topple limit refuses more of the pushes the model is unsure
about, and every one of those 20 topples came from a push the model was sure
about.

**The learning that paid attacked the quantity the geometry gets wrong.** The
geometry computes exactly how much room a push would gain, because that is
arithmetic on the destination, and it predicts badly where a pushed glass will
actually stop, because that needs the friction and the weight distribution that
nobody in this cell has measured. Solution 4 fits a model of the second and
racks the most glasses. Solution 2 fits a model of the first and reaches
*exactly* the same fourteen tables and 107 glasses as the printed rule it was
meant to beat, for nine more pushes and half again the travel. **So the useful
question is not whether to learn, but which quantity is worth learning** — and
when every table bottoms out on the hand's width or its height, ordering the
candidates differently only changes the route.

**Imitation fails for a reason that was measured rather than guessed.**
Solution 3 learns from solution 2's own recorded pushes, so its teacher is in
the room and is one of the rows above. On tables it was fitted on, its chunks
point within 4 degrees of the teacher's; on tables it never saw, 22 to 27
degrees out. The hand is 266 mm long behind its fingertips, so a heading that
far off puts the wrist over a neighbour, the descent is stopped, and nothing
moves. Fitting it on four times the tables removed the memorising and took only
about a fifth off that error, which says the shortfall is the policy averaging
over pushes that disagree rather than a shortage of examples.

**The borrowed model cannot act, and fitting it taught it to act unsafely.**
Solution 5 racks 48 glasses, which is exactly the 48 that already had room: its
pushes achieve nothing at all, because the chunks come back about 200 mm above
the table. Solution 6 fits that same model on this cell's own demonstrations
for a thousand steps, and the chunks then come down to exactly the height the
gripper pushes at — and onto the glasses. About two of its pushes in three are
stopped coming down, it topples 40 glasses, and 36 of its fifty tables end
wrong. **Fitting bought enough competence to act and not enough to act safely,
which on this scorecard is worse than inaction.** Its correction was still
improving when the training budget ran out, so that is what a thousand steps
buys rather than what the method can do.

## 6. What these results do not cover

- **Not Gazebo.** The physics is MuJoCo, standing in for the simulator the rest
  of the project uses, because a learned approach needs thousands of pushes.
- **A guessed friction.** No solution is told what the table's friction is, and
  the ones that reason about toppling use a believed range instead. The examiner
  knows the true value and never shares it.
- **No early abort.** [Pushing without
  toppling](01_the-problem/05_pushing-without-toppling.md) argues
  for stopping a push while the glass is still moving. Nothing here implements
  it, and solutions 4 and 6 are what its absence costs.
- **One training seed for solutions 4, 5 and 6.** The spread those three report
  is over evaluation runs rather than over trainings, which is a narrower claim
  than the examiner asks for. Solution 3 is the only learned solution fitted
  several times, and its three seeds disagree by more than a little.
- **One kind of glass per table**, as the cell's own layout produces.

## 7. Reproducing

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
