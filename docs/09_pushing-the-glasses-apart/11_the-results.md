# The seven solutions side by side

## 1. Introduction

This page is the scoreboard for the seven solutions in this book. It answers one
question. On the same crowded tables, with the same marking, how many glasses
did each method clear, and how many did it knock over? It is for a reader who
has already met the seven. Come back to it whenever a page says one method did
better than another. Six solutions have been measured. Solution 7 is still being
measured, so it has no score here yet.

The six are tested on the same 50 tables. The tables hold 251 glasses, and 203
of them have no room at the start. Every solution gets the same push budget and
the same scorecard, described in [the
examiner](01_the-problem/03_the-examiner.md). No solution saw these tables
while it was being built or trained. Every number here comes from a solution's
own `results.json`, or from the file of per-table rows beside it. The two later
runs in the table have their own result files, linked where they appear.

All six used the same real hand, a **Robotiq 2F-85**, turned on its side.
[How low the push has to
be](01_the-problem/01_what-is-asked-for.md#7-how-low-the-push-has-to-be-and-why-it-is-a-property-of-the-glass)
explains why it is turned and what that costs. The four solutions that learn
something were trained again with this hand first. The next section gives the
scores.

## Contents

1. [Introduction](#1-introduction)
2. [The results](#2-the-results)
3. [The six films, all of the same table](#3-the-six-films-all-of-the-same-table)
4. [Travel, and why that column is a trap](#4-travel-and-why-that-column-is-a-trap)
5. [What the comparison says](#5-what-the-comparison-says)
6. [What these results do not cover](#6-what-these-results-do-not-cover)
7. [Reproducing](#7-reproducing)
8. [How a result is claimed](#8-how-a-result-is-claimed)
9. [Questions and answers](#9-questions-and-answers)

## 2. The results

This section holds the main table, so everything after it refers back here.

Read the table one column at a time. No single column decides which solution
is best. Each row is one solution, and each column is one measurement. A bold
figure is the best or the worst of the first six rows in that column. The two
columns that matter most are **tables wrong** and **toppled**. A toppled glass
is the one failure this cell cannot undo.

| | tables done | tables wrong | glasses racked | toppled | pushes | travel | thinking per push |
|---|---|---|---|---|---|---|---|
| [1 one fixed nudge](../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge) | 14 | **1** | 107 | **1** | **173** | 0.87× | 93 ms |
| [2 geometry ranked](../../code/src/09_pushing-the-glasses-apart/02-geometry-ranked) | 14 | **1** | 107 | **1** | 182 | 1.32× | 102 ms |
| [3 imitation, ACT](../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations) | 2 (1–3) | 11 (7–13) | 63 (51–64) | 12 (7–13) | 438 (414–497) | 0.87× | **11 ms** |
| [4 a world model](../../code/src/09_pushing-the-glasses-apart/04-a-world-model) | **20** | 19 | **146** | 20 | 221 | 1.98× | 374 ms |
| [5 SmolVLA as it downloads](../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads) | 1 (0–1) | 9 (6–10) | 48 (46–51) | 12 (10–14) | 620 (589–641) | 0.42× | 286 ms |
| [6 SmolVLA fine-tuned](../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned) | 1 (0–2) | **36** (31–36) | 56 (50–65) | **40** (33–44) | 369 (351–374) | 1.68× | 404 ms |
| 3 with the camera's readings, [later run](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/03-imitation-from-demonstrations/results-act-readings.json) | 3 (3–3) | 11 (8–12) | 61 (58–65) | 12 (6–13) | 434 (417–482) | 0.57× | 11 ms |
| 6 on solution 3's band, [later run](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/06-smolvla-fine-tuned/results-aligned.json) | 1 (0–1) | 36 (35–38) | 53 (52–56) | 42 (40–47) | 360 (295–411) | 2.23× | 387 ms |
| [7 Evo-1 fine-tuned](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/README.md) | being measured | | | | | | |

A table is **done** when every glass on it was picked up. It is **wrong** when
the run ended in a state the cell should never reach. In practice this means a
glass lying on its side.

Solutions 3, 5 and 6 were run three times each, because they draw their answers
at random. For those three, the table shows the middle run. The brackets give
the lowest and the highest. Solutions 1, 2 and 4 give the same result every
time, so they have no brackets.

The last three rows are newer. They sit below the first results and do not
replace them. The first new row is solution 3's three fits, given the camera's
readings beside the picture. The second is solution 6 trained on solution 3's
tables: 6,935 demonstrations from 5,200 tables, against 1,074 from 800. In
both, the brackets come from three training seeds, each run once. Neither
solution's score changed detectably from its first row. [How a result is
claimed](#8-how-a-result-is-claimed) explains what "detectably" means here.
Solution 7 has no score yet.

Read the brackets before the ranking. Solution 6 racks between 50 and 65
glasses. Solution 3 racks between 51 and 64. So this test does not separate
those two. The toppling is clear, though. Solution 6 knocks over 33 to 44
glasses on every run. Solutions 1 and 2 knock over one glass in fifty tables.

"Racked" promises more than it means. The examiner takes a glass away as soon as
it has room. It never asks whether the cell could really grip that glass. The
cell's own grip rule can hold only 97 of the 251 glasses. So *racked* means the
job this book sets was done, not that the glass reached the rack. [What the
examiner
measures](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures) gives
the figures. This does not change any comparison, because all six are marked
the same way.

The job is hard with a real hand. The best solution gets only 146 of the 251
glasses off the table. The refusals say why. For many glasses there is no place
to put the hand that is clear of a neighbour. For many others, the hand cannot
go low enough, so a push would tip the glass. Neither refusal is a fault of a
method. Both say that the job, with this cell, is partly impossible.

The thinking column is each solution's own time per push. The simulator's time
is taken off. It was measured on an idle machine. This matters, because runs
timed while other work was running showed up to three and a half times these
figures.

A total over fifty tables hides what one run looks like. The next section shows
one table on film.

## 3. The six films, all of the same table

This section shows each solution clearing one table, so you can see the numbers
above in action. The six measured solutions were filmed on the same table, so
the films can be compared. Solution 7 has no film yet. Each film is recorded
from the simulator, runs at one and a half times real speed, and has no sound.

Two things are the same in all six films. The hand stays shut while it pushes,
because the whole closed hand does the pushing. The pick-up at the end is drawn,
not simulated, because the examiner removes a glass in one instant. [The film of
the job](01_the-problem/01_what-is-asked-for.md#2-a-film-of-the-job) explains
both.

The table filmed is number 10025. It was chosen to be **typical, not
flattering**. The rule was written down before it was used. On the chosen
table, each of the six had to reach its own most common outcome and rack at
least one glass. Exactly one table of the fifty passed, and this is it. Choosing
it needed [one row per
table](01_the-problem/03_the-examiner.md#5-what-the-examiner-measures) in the
scorecard. The table holds six glasses, one more than the average of five. Five
of its six glasses have no room at the start, which is usual.

The table below is the films' own scorecard. It has the same columns as the
main table, but it counts one table instead of fifty.

| | film | outcome | racked | toppled | pushes |
|---|---|---|---|---|---|
| 1 one fixed nudge | [13 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/01-one-fixed-nudge.mp4) | incomplete | 1 of 6 | **0** | **2** |
| 2 geometry ranked | [13 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/02-geometry-ranked.mp4) | incomplete | 1 of 6 | **0** | **2** |
| 3 imitation, ACT | [23 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/03-imitation-from-demonstrations.mp4) | incomplete | 1 of 6 | **0** | 14 |
| 4 a world model | [44 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/04-a-world-model.mp4) | done | **6 of 6** | **0** | 3 |
| 5 SmolVLA as it downloads | [74 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/05-smolvla-as-it-downloads.mp4) | incomplete | 1 of 6 | **0** | 16 |
| 6 SmolVLA fine-tuned | [12 s](https://docs.dodao.io/videos/pushing-the-glasses-apart/06-smolvla-fine-tuned.mp4) | wrong | 1 of 6 | 1 | 4 |

Each film is also shown on its solution's first page, with each push described.
Together the six rows are this book's argument in small.

- **Solutions 1 and 2 do exactly the same thing.** They make the same two
  pushes and rack the same glass. This is not luck. When the hand's width and
  height decide what is possible, a different order of candidates changes
  nothing.
- **Solution 4 clears the whole table in three pushes.** This is what it is
  worth to predict where a glass will stop.
- **Solutions 3 and 5 use up the budget and rack only the glass that already had
  room.** In solution 3 the jaw is stopped on the way down. In solution 5 it
  never reaches the glasses.
- **Solution 6 is the only one that ends the table wrong**, with a glass on its
  side. It acts well enough to reach a glass, but not well enough to miss one.

Solutions 3, 5 and 6 draw their actions at random. So a film of one of them is
one draw, not an average. It may not match that table's row in the scorecard.
[The
examiner](01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why. Each solution's own page compares its film with its scored runs.

The films show what each solution does. The next section explains the one
column of the main table that is easy to read the wrong way.

## 4. Travel, and why that column is a trap

This section explains the travel column, because a low number there looks good
but often is not.

**Travel is how far the glasses really moved, as a multiple of the least any
legal layout needs.** That least distance is the displacement floor. [The
target layout](01_the-problem/04_the-target-layout.md) works it out from each
table. Over these fifty tables it comes to 3,284 mm. The floor belongs to the
table, not to any method. So no solution can do the job and go below it.

**So the column means nothing on its own. Read it beside the glasses racked.**
A solution that never touches anything travels nothing, and it scores best
here. That is what the smallest numbers show.

- SmolVLA as it downloads travels 0.42 times the floor, because its jaw never
  reaches a glass.
- The imitation policy travels 0.87, because most of its pushes are stopped on
  the way down.
- The fixed nudge travels 0.87 for a third reason. It refuses 143 of the 251
  glasses, so it never spends the travel they would need.

**None of those three is saving effort. All three are not doing the work.**

The column does separate the solutions that move most of the glasses. The world
model spends 1.98 times the floor to rack 146 glasses. This is the most travel
on this page, and also the most work done. Solution 6 spends 1.68 to rack only
56. This is the worst trade here. The fine-tuning taught it to move firmly, but
not where to put the jaw down. So most of its travel is glasses pushed to
unhelpful places or knocked over.

The scores and the travel are now both read. The next section says what they
mean together.

## 5. What the comparison says

This section draws the lessons that need more than one row of the main table.

**Only the written rules could be left to run alone.** Solutions 1 and 2 each
topple one glass in fifty tables and end one table wrong. Every solution that
learns something ends between nine and thirty-six tables wrong. A glass on its
side leaves broken glass, and the arm keeps moving through it. So safety is not
one trade among several. It is the condition for using any of the others.

**One learned solution clears many more glasses, and it breaks far more.** The
world model racks 146 glasses against the geometry's 107. That is more than a
third more. But it topples 20 against 1. So learning did not simply win or
lose. One mechanism causes both results. The model predicts an outcome instead
of refusing when the arithmetic is unsure. That buys the extra glasses, and it
also breaks the extra ones. A tighter topple limit cannot separate the two. It
would refuse more of the pushes the model is unsure about. But every one of the
20 topples came from a push the model was sure about.

**The learning that helped was aimed at what the geometry gets wrong.** The
geometry knows exactly how much room a push would gain, because that is simple
arithmetic. But it predicts badly where a pushed glass will stop, because that
needs the friction and weight, and nobody measured them. Solution 4 learns where
a glass stops, and it racks the most glasses. Solution 2 learns how much room a
push gains. It reaches *exactly* the same 14 tables and 107 glasses as the
printed rule it was meant to beat. It also uses nine more pushes and half again
the travel. **So the useful question is not whether to learn. It is which
quantity is worth learning.** When the hand's width or height decides every
table, a different order of candidates only changes the route.

**Imitation fails for a reason that was measured.** Solution 3 learns from
solution 2's recorded pushes, so its teacher is a row in the table above. On
tables it trained on, its pushes point within 4 degrees of the teacher's. On
tables it never saw, they point 22 to 27 degrees off. The hand is 266 mm long
behind its fingertips. So a push that far off puts the wrist over a neighbour,
the jaw is stopped on the way down, and nothing moves. Training on four times
the tables took only about a fifth off that error. This means the policy is
averaging pushes that disagree. It is not short of examples. Giving it the
camera's readings made its three fits agree more, but it racked no more
glasses. [Telling the policy where the glasses
are](06_imitation-from-demonstrations/04_a-worked-example.md#5-telling-the-policy-where-the-glasses-are)
explains why.

**The borrowed model cannot act, and training taught it to act unsafely.**
Solution 5 racks 48 glasses, which are exactly the 48 that already had room. Its
pushes do nothing, because the jaw stays about 200 mm above the table. Solution
6 trains that same model on this cell's pushes for a thousand steps. The jaw
then comes down to exactly the height the gripper pushes at, and onto the
glasses. About three in five of its pushes are stopped on the way down. It
topples 40 glasses, and 36 of its fifty tables end wrong. **Training gave it
enough skill to act, but not enough to act safely. On this scorecard, that is
worse than doing nothing.** Six and a half times as many demonstrations changed
nothing that could be measured. One early fit seemed to be still improving when
training stopped. Three later fits did not confirm it. [More demonstrations,
and a result that did not come back](09_the-same-model-fine-tuned-here/06_how-it-compares.md#4-more-demonstrations-and-a-result-that-did-not-come-back)
explains both.

These lessons hold only inside the limits of this test. The next section lists
those limits.

## 6. What these results do not cover

This section lists what the test above left out, so you do not read more into
it than it shows.

- **Not Gazebo.** The physics engine is MuJoCo, not the simulator the rest of
  the project uses. A learned method needs thousands of pushes, and MuJoCo makes
  them fast.
- **A guessed friction.** No solution is told the table's friction. The ones
  that reason about toppling use a believed range instead. Only the examiner
  knows the true value.
- **No early stop.** [Pushing without
  toppling](01_the-problem/05_pushing-without-toppling.md) argues for stopping a
  push while the glass is still moving. Nothing here does this. Solutions 4 and
  6 show what its absence costs.
- **One training seed for solutions 4 and 6 in the first six rows.** Their
  spread comes from repeated test runs, not from repeated trainings. That is a
  weaker claim than the examiner asks for. Solution 3 was trained three times,
  and its three seeds differ by more than a little. Solution 6's later run also
  used three seeds.
- **No score for solution 7 yet.** Its three fits and its scoring run are still
  in progress.
- **One kind of glass per table**, because that is what the cell's own layout
  makes.

The next section says how to make these numbers yourself.

## 7. Reproducing

This section shows how to run a solution and get its scorecard again.

```
pixi run python 01-one-fixed-nudge/run.py
```

The same line works for each of the other five. Solution 7's code is only in
[the
project](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/README.md) for now. Run it from
`code/src/09_pushing-the-glasses-apart/`. The solutions that learn something
need their training step first. Each solution folder's own README says which
step that is and what it costs.

Two things are worth knowing before you run one. First, a run can start at a
chosen table instead of the first one. This is how the films were made. Second,
every solution refuses to overwrite its saved scorecard unless it runs the
official fifty tables from the official first seed. Without this guard, a short
run on other tables could replace the result this page quotes, and nothing would
warn you.

Running a number again is one half of trusting it. The next section is the
other half: when a gap between two numbers counts as a result.

## 8. How a result is claimed

This section says when a gap on this page counts as a finding. It builds on
[the examiner's rule on runs and
seeds](01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not),
which says why one run is not a measurement.

**The spread comes first.** A learned solution is trained and run several
times. The runs do not agree. The spread says how far apart they are. Here it
is the standard deviation, the usual measure of how far values sit from their
average.

**A gap is measured in standard errors of the difference.** Take the gap
between two averages. The standard error of the difference is the size of gap
that chance alone often makes. It is worked out from the two spreads and the
number of runs. Divide the gap by it.

**A gap under two standard errors is not claimed.** Solution 6 on solution 3's
tables is the example. Its racked glasses moved by 0.7 standard errors. Its
toppled glasses moved by 1.0, and its wrong tables by 1.1. So no change is
claimed. Solution 3 racked 61.3 glasses on average with the readings, and 59.3
without. That gap is only 0.4 of the run-to-run spread. The [solution 6
README](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/06-smolvla-fine-tuned/README.md) and the [solution 3
README](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/03-imitation-from-demonstrations/README.md) give these
figures.

**"No change detected" is not "equal".** A gap under two standard errors means
the test could not see a change. A small real change may still hide in the
spread. So this page says "no change was detected", never "the scores are the
same".

**Seeds are part of the spread.** A seed is the random number a training starts
from. Two seeds give two different policies. Solution 3's three seeds racked 64,
51 and 63 glasses from the picture alone. So a learned solution is trained
several times, not once.

**One striking run is checked again.** In one control run, solution 6's
refusals rose from 138 to 145. That was ten standard errors, the largest effect
in the comparison. On the matched band they were 137 again. The same happened to
a claim about training. With one seed, the held-out error seemed to be still
falling at the end. With three seeds, it rose in two of them.

**A timing counts only on an idle machine.** The thinking column is clock time.
If another program shares the machine, the time includes that program's work.
That control run read 1.07 s a push, against 0.39 s on the matched band. It
shared the graphics chip with a training run. So that timing measures nothing
about the model.

**Every number on a picture is checked against the run's own file.** A picture
is made once and can go stale. In the project, a caption under solution 6's
compute picture quoted an older fit. The training record held other numbers.
Another sentence guessed that the drawn hand often stops short of a glass.
Counted in the films, it happens once in six films. A number is checked against
the file the run wrote, or it is not written.

These rules decide what this page may claim. The last section answers the
common questions about results in short.

## 9. Questions and answers

This section answers common questions about the results. Each answer is short
and links to the place that explains it in full.

### Why is a number without a spread not a result, and what is a standard error of the difference?

Learned solutions give a different number on each run. One number cannot show
whether a gap is real or chance. The standard error of the difference is the
gap that chance alone often makes. [How a result is
claimed](#8-how-a-result-is-claimed) shows how it is used.

### Why does "no change was detected" not mean "the scores are equal"?

A gap under two standard errors is too small to see in a few runs. A real but
small change can still be there. So the honest statement is that the test did
not detect one. [How a result is claimed](#8-how-a-result-is-claimed) gives the
example of solution 6.

### Why is a policy trained several times with different seeds?

Each training starts from a random number, the seed. Different seeds give
policies of different quality. Solution 3's three seeds racked 64, 51 and 63
glasses. One seed could have told either story.

### Why is a striking result from one run treated with suspicion?

A large effect from one set of runs may belong to those runs only. Solution 6's
refusals rose by ten standard errors in a control run. On the matched band they
went back to where they started. [How a result is
claimed](#8-how-a-result-is-claimed) tells the story.

### Why measure thinking time per push, and when is that timing meaningless?

A solution that wins but costs a hundred times more has not clearly won. So the
time per push sits beside the counts. A timing is meaningless when another
program shares the machine. [The
examiner](01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why cost is on the scorecard.

### Why must every number on a diagram be checked against real output?

A picture is made once and does not update itself. In the project, one caption
quoted an older fit, and one sentence guessed at something the films did not
show. Checking each number against the run's file catches both.

### What is the clearest finding so far?

Only the written rules could be left to run alone. Solutions 1 and 2 topple one
glass in fifty tables. Every learned solution ends between nine and thirty-six
tables wrong.
[What the comparison says](#5-what-the-comparison-says) gives the full argument.

### Which questions are still open, and what would settle each one?

Three are open. Is a newer, larger model worth its cost? Solution 7's scores
will settle it. Can a copying policy learn not to bring the jaw down on a glass?
Its teacher never makes that mistake, so the demonstrations never show the way
out. [DAgger](06_imitation-from-demonstrations/07_questions-and-answers.md#8-what-is-dagger)
would test it. Would stopping a push early save glasses? Building [the
early stop](01_the-problem/05_pushing-without-toppling.md#an-early-abort-acting-during-the-push)
would settle it.

← [A newer, larger model, fine-tuned here — questions and answers](10_a-newer-larger-model-fine-tuned-here/04_questions-and-answers.md)
