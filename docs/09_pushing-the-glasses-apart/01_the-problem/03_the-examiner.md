# The examiner — the same question for every answer

## 1. Introduction

This problem is answered in seven different ways. Seven answers can only be
compared if they get the same question and the same marking. The examiner gives
them both. It draws the crowded tables. It runs the physics in which the
glasses slide and tip. It gives each solution the same readings. It carries out
each push that comes back. Then it marks the result against what really
happened.

This page explains these things:

- why there is an examiner at all;
- how it draws its tables, and why its physics is MuJoCo;
- why the marking looks at the outcome and never at the action;
- what the scorecard counts;
- two things this scorecard needs that the examiner for [telling the glasses
  apart](../../08_seeing-the-glasses/03_the-examiner/01_the-examiner.md) did
  not.

The page before this one, [what goes in and what comes
out](02_what-goes-in-and-what-comes-out.md), describes `look()`, `push()` and
`take()`. This page assumes you have read it.

The examiner is built. Its code is in
`code/src/09_pushing-the-glasses-apart/bench/`, and every solution in this book
runs on it. Where this page describes a decision that is not yet working code,
it says so.

## Contents

1. [Introduction](#1-introduction)
2. [Why there is an examiner at all](#2-why-there-is-an-examiner-at-all)
3. [What the examiner draws](#3-what-the-examiner-draws)
4. [The score is the outcome, not the action](#4-the-score-is-the-outcome-not-the-action)
5. [What the examiner measures](#5-what-the-examiner-measures)
6. [Two things this scorecard needs that the camera work's did not](#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
7. [Where to go next](#7-where-to-go-next)

## 2. Why there is an examiner at all

Without an examiner, each solution would bring its own tables. Each would have
its own idea of a good push and its own way of counting success. Then nothing
could be learned by comparing their results. The examiner removes every
difference between the solutions except the method itself.

It does this by keeping three things fixed.

- The **input** is the same readings of the same tables, in the same order.
- The **output** is the same kind of thing, carried out by the same code.
- The **marking** is the same set of counts, worked out the same way.

A solution is free to change only what happens between the input and the
output. That middle part is exactly what we want to compare. So suppose a
learned policy clears more tables than a fixed nudge. Then the difference comes
from the policy, not from an easier table or a kinder scorecard.

![The input, the output and the marking are all held fixed, and the one box between them is whatever the solution does, so a difference between two scorecards belongs to the method.](../../images/pushing-the-glasses-apart/the-examiner/examiner-flow-what-is-held-still.png)

The first fixed thing is the tables, so the next section describes them.

## 3. What the examiner draws

The tables are the first of the three fixed things, so they come first.

**Every table is crowded on purpose.** It holds four to six glasses of one
kind. The kind and the count change from one table to the next. So all four
kinds appear in turn: the straight glass, the tapered glass, the stemmed glass
and the short stemmed glass. The glasses stand inside the glass zone. No two of
them touch. There is always a little space between them.

**The crowding comes from where the glasses stand, not from their shapes.**
When the examiner places a glass, it usually puts it close to a glass already
there. It is closer than the gripper can work with, but not touching. The other
glasses go anywhere in the zone they fit. Some of these end up crowded by
chance. The examiner keeps a table only if at least one glass on it has no
room. So there is never a table where the right answer is to do nothing.

**A glass has room when no other glass's edge is within 76 mm of its
middle.** This is the gripper's test. [The gap that
matters](01_what-is-asked-for.md#6-the-gap-that-matters-is-not-the-gap-between-the-glasses)
explains the number and why the test is not symmetric.

**The tables are numbered, and the numbers are split in two.** Each table is
made from one number. The same number always gives the same table. So any
solution can be run on exactly the tables another solution was run on.

There is a fixed dividing line among the numbers. Training uses only numbers
below the line. Testing uses only numbers above it. These test tables are
called held-out tables. This means no solution is ever marked on a table it
trained on. This matters more here than it did when [telling the glasses
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md),
because five of the seven solutions are trained. The test set has 50 tables with
251 glasses on them, and 203 of those glasses start without room.

**The physics is MuJoCo, used in place of Gazebo.** There are two reasons. The
first is speed. A learned method needs thousands of pushes. Gazebo runs each
push at real-time speed. So training data that MuJoCo makes in hours would take
weeks in Gazebo.

The second reason is fairness. Nobody on this project wrote MuJoCo's physics.
Suppose the examiner used a push model written for this project instead. Then a
solution built on that same model would win because it already knew the answer.
The comparison would measure nothing. A physics engine that nobody here wrote
is equally unknown to every solution.

The glasses in MuJoCo keep their real shape. Each one is built as a stack of
cylinders. Each cylinder is as wide as the glass is at its widest inside that
cylinder. So the collision shape is never thinner than the real glass. The
bottom cylinder is the foot. Its edge is where the glass tips over.

![Every glass the examiner stands on a table is a stack of cylinders, each one as wide as the glass is anywhere inside it, and the bottom cylinder is the foot it would tip over; the height at which a push starts tipping a glass rather than sliding it follows from that foot and from a friction the examiner keeps to itself.](../../images/pushing-the-glasses-apart/the-examiner/04-the-model-that-was-built.png)

The tables are now fixed. The next section says how a run on them is marked.

## 4. The score is the outcome, not the action

The first rule of the marking answers an obvious question. [What must come
out](02_what-goes-in-and-what-comes-out.md#6-what-must-come-out) allows two
kinds of output. One solution may give three numbers. Another may give twenty
waypoints. How can their results be compared?

![The questions the examiner never asks in one column and the ones it counts instead in the other: a solution that reaches the rack by an unexpected route scores as well as one that followed the obvious one.](../../images/pushing-the-glasses-apart/the-examiner/examiner-flow-outcome-not-action.png)

The answer is that **the examiner never marks the action**. It does not ask
whether a push was a good choice. It does not ask whether the waypoints were
smooth. It looks only at the table afterwards. It checks which glasses have
room, which are still standing, where each one ended, and how many pushes it
took.

This is what makes the two kinds of output comparable. To mark the action, you
would need one common way to describe every action. No such way is fair to
both a three-number push and a learned chunk of waypoints. Marking the table
needs no such description, because the table is the same either way. Every
solution is asked the one question the problem cares about. Are the glasses far
enough apart now, and is every glass still standing?

The rule says what is marked. The next section lists exactly what is counted.

## 5. What the examiner measures

This section lists everything on the scorecard. After a run ends, the scoring
code reads the simulator's record. It turns that record into one scorecard,
with the same layout for every solution.

**Each table gets one of three outcomes.** These are the three that [the
problem](01_what-is-asked-for.md#10-what-done-means) defines.

- A table is **done** when every glass was racked, and each one really had
  room when it was taken.
- A table is **correct but incomplete** when some glasses are still on the
  table, each one has a reason, and nothing went wrong.
- A table is **wrong** when anything went wrong at all.

**Each glass is then counted on its own.** A glass may be racked. It may be
refused with a reason. Or it may have gone wrong. The problem names three wrong
endings: a glass **toppled**, a glass **pushed off the table**, and a glass
**pushed into the rack**. The examiner finds all three with two tests.

- It decides that a glass toppled by how far the glass leans from upright.
- The other two endings are the same in shape. In both, the glass is outside
  the area it may be in. So one test covers both: the glass **left the glass
  zone**.

The examiner adds two more wrong endings of its own. A glass **picked without
room** is one the arm thought it could grip when it could not. The arm would
not notice this mistake by itself. A glass **left with no reason** is one left
on the table without any explanation.

**The number of glasses grippable at the end is what the problem is really
about.** The examiner gets this number from racking, not by measuring gaps. A
glass counts as racked only if it really had room when it was taken. So a run
that clears the table has shown that every glass was grippable.

**That number rests on an assumption.** When the examiner racks a glass, it
asks only whether the glass had room around it. It never asks whether the cell
could really pick that glass up. These are two different questions, and the
difference is large. The cell has its own rule for where to hold a glass, in
[`glasses/rules.py`](../../../code/src/08_seeing-the-glasses/work_cell/work_cell/glasses/rules.py).
We can ask that rule directly. We give it the real gripper's size and each test
glass's shape. **It finds a place to hold only 97 of the 251 glasses.**

The table below has one row for each kind of glass. Each number says how many
glasses of that kind the rule can hold, out of how many there are.

| kind | a grip found |
|---|---|
| straight | 62 of 65 |
| tapered | 18 of 66 |
| stemmed | 17 of 60 |
| short stemmed | **0 of 60** |

**The most common reason is reach, not width.** The gripper comes in level from
the side. So the whole tool lies across the height where it holds. The part
that hangs lowest below the tool decides how low it can go. That gives a floor
50 mm above the table. If a glass has nothing to hold between that floor and
its own halfway height, the rule refuses it. A short stemmed glass is all stem
below that line. This is why none of the 60 can be held.

**Room around a glass is also not the same as a clear way in to it.** This
second gap belongs to the examiner, not to the picking step. The room test asks
whether anything stands within a fixed distance of the glass. That is the right
test for an open hand coming straight down. But this hand does not come
straight down. It comes in level. It is 266 mm long, from its fingertips to the
back of its force sensor. So it needs a long, narrow path across the table, not
just a circle around one glass. Whether that path is clear depends on which
side the hand comes from. On a crowded table, most sides are blocked by
something far outside the room test's circle.

This was checked over the first twenty of the fifty tables. It looked at every
glass the examiner says has room, and at every side of it. **A clear way in
exists for 14 of those glasses. For the other 5, the hand would have to stop
short.**

The films make the same check before they draw a pick-up. A drawn hand cannot
hit anything. Without the check, a film could show the hand passing straight
through a glass. A viewer would then think there was room when there was not.
So the hand comes in from a clear side. When no side is clear, the hand is
drawn stopping where it would touch, and a line on the picture says so. Across
the six films, eleven pick-ups are drawn, and one of them stops short. That is
rarer than 5 in 19. The reason is that by the time a glass is racked, the
solution has already pushed its neighbours away.

This is a limit of the picking step, not of anything in this book. No
solution's score depends on it, because the same examiner marks every solution in
the same way. The films say so too. Each drawn pick-up is a stand-in, and the line
on screen says that the cell's own grip rule does the real pick. What this
finding adds is that **spreading the glasses apart is not the whole job**. This
book's half of the work can succeed fully and still leave a glass that the
hand cannot take.

**Pushes are counted against a budget.** The scorecard records how many pushes
were used in total. It records how many were repeat pushes on a glass already
pushed. It also records how many went wrong in each way: blocked on the way
down, never touching anything, or getting stuck.

The budget is a fixed largest number of pushes per glass and per table. After
that, the remaining glasses must be refused. The budget used to be set in each
solution's own code, so the counts could not be compared. Now it is set in the
examiner, as `PUSHES_PER_GLASS` and `PUSHES_PER_TABLE`. So every solution gets the
same budget. When the two budgets were joined, the larger pair was kept: 4 and 16,
not 3 and 15. This way no solution that already worked lost any pushes. The
fixed nudge had been using the smaller pair. It was measured under both and
scores the same either way. It refuses for lack of room long before it runs out
of pushes.

A glass refused because the budget ran out was not always cut short. The
budget says where a run stopped, not why it went badly. For solution 3, eight
times the budget racks only one or two more glasses of 251. [More pushes would
not
help](../06_imitation-from-demonstrations/04_a-worked-example.md#3-more-pushes-would-not-help)
gives the measurement. The budget stayed at 4 and 16, because a number tuned on
the test tables would bias every later result.

**Refusals are counted with their reason, and a refusal is a result, not a
failure.** Some glasses cannot be pushed safely at all, because they tip before
they slide. For those, the only correct answer is to refuse. So the examiner
groups refusals by their reason and reports each group. Here is how this is
scored.

- A solution that refuses those glasses and gives the reason scores *correct
  but incomplete*. This is a good outcome.
- A solution that leaves those same glasses with no reason scores *wrong*.

So saying "I cannot do this, and here is why" is part of a correct answer.

**Last, the examiner records how far each glass ended from where the push aimed
it.** Every push carries the place where the solution expects the glass to
stop. Once the glass settles, the examiner measures the real distance between
the two. It reports the middle value and the worst value. For most of the solutions,
the expected place comes from [the target layout](04_the-target-layout.md).

This number is **for reference, not a pass mark**. A push that stops some way
from its aim is not wrong, because the problem only asks for the glasses to be
far enough apart. The number shows how well a solution predicts its pushes. If
its glasses stop close to the aim, it understands what a push does. If its
glasses scatter, it succeeds by looking again, not by predicting. That is a real
strategy, but a different one.

**The scorecard also keeps one row for each table.** Everything above is a
total over the whole run. A total says how a solution did overall, but not how
it did on any one table. For example, a run that finishes 14 tables out of 50
does not say which table is worth looking at. So the examiner also writes a
second file with one row per table. Each row records that table's outcome and
how many glasses were racked or knocked over. It also records how many pushes
were used and how far the glasses moved in total.

These rows let us choose a table because it is typical of the run, not because
it makes the solution look good. This is how the film on each solution's own
page was chosen. The typical table turns out to be different for each solution.
Six solutions are filmed. The one table on which all six are filmed was chosen
by a rule that covers all six at once. [The six films](../11_the-results.md#3-the-six-films-all-of-the-same-table)
says more about this.

The counts above are enough for a solution that is written, not trained. The
next section adds two things that trained solutions need.

## 6. Two things this scorecard needs that the camera work's did not

The examiner for [telling the glasses
apart](../../08_seeing-the-glasses/03_the-examiner/01_the-examiner.md) could run
each solution once and read the result. This examiner cannot, for two reasons.
Both reasons come from the fact that five of the seven solutions are trained,
not written. Both are now in `scoring.py`. `Repeats` holds several runs and reports
the spread of every number. `Scorecard` reports the time per push beside the
counts.

**One run is not a measurement.** The learned policies here are random in part.
Asked the same question twice, they may act differently, because each action is
drawn at random from a set of likely actions. Training also uses its own random
number, called a seed. So the same method trained twice gives two different
policies of different quality.

The problem is that this variation is sometimes **larger than the gap between
two methods**. Then a single run of each can name the wrong winner. And it
gives no sign that the result is uncertain. So each trained solution must be
trained with several seeds and tested over several runs. The scorecard must
report the **spread**, not only the middle value. A result without a spread is
not a result. A method that wins by less than its own spread has not been shown
to win.

Drawing actions at random has one more effect, and it is easy to miss. For such
a solution, **one table run on its own is not the same as that table reached
inside a run**. Every random draw on the earlier tables has already moved the
policy's stream of random numbers forward. So to repeat what a row says about
the fourth table of a run, you must also run the first three tables. And a
solution filmed one table at a time will not always do what the scorecard says
it did.

**The cost of running each solution differs hugely, so it belongs on the
scorecard.** The solutions do not cost the same for one push. A fixed nudge is simple
arithmetic and costs almost nothing. A planner that uses a learned world model
tries many candidate pushes at run time. It tests each one inside the model
before it acts. So each push costs hundreds or thousands of times more than the
arithmetic. A foundation model runs a large neural network for every answer.
That is a different kind of cost again, and it usually needs rented hardware.

Leaving cost out would make the scorecard misleading. **A solution that wins
but takes a hundred times longer has not clearly won.** On a real arm it might
not be usable at all. The fair question is not "which scored best?" It is
"which scored best for what it cost?" So each solution reports what hardware it
needs and roughly what renting it costs, as it also states its licence. The
time per push sits on the scorecard beside the counts. [The
results](../11_the-results.md) compare these times for the six that have been measured.
The seventh is still being measured.

This completes the scorecard. The next section says where to read on.

## 7. Where to go next

- [The target layout](04_the-target-layout.md) — where the glasses should end
  up, worked out rather than learned, and the least movement the task needs.
- [Pushing without toppling](05_pushing-without-toppling.md) — how low the push
  has to be, why that depends on the glass, the refusal path, and the loop of
  plan, feel and look again.
- [The seven solutions](../03_the-seven-solutions/01_how-the-six-compare.md) — what
  each method puts between the input and the output.

← [What goes in and what comes out](02_what-goes-in-and-what-comes-out.md) · [The target layout](04_the-target-layout.md) →
