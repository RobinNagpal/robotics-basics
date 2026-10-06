# One fixed nudge

This page describes the first of the six solutions in about eight minutes of
reading. It is the one solution that holds no fitted numbers at all, and it is
also, on this book's scorecard, the one that finished the most tables. By the
end of this page you will know the single piece of arithmetic it rests on, why
it repeats instead of predicting, what it costs, what it scored on the shared
examiner, and the three things it cannot do that the other five were built to
try. The full method is in [the chapter on this
solution](../04_one-fixed-nudge/01_what-it-is.md), which is about an hour of
reading.

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

The problem this book sets is that glasses stand too close together for the
gripper to close round any of them, so the arm has to drag them apart first,
without knocking any of them over. [What is asked
for](../01_the-problem/01_what-is-asked-for.md) states that in full.

The hard part of the problem is that nobody in this cell knows what a push will
do. Where a pushed glass comes to rest depends on the friction between its base
and the table and on how its weight is distributed, and neither of those has
been measured. Every solution in this book is a different answer to that one
difficulty, and this solution's answer is the simplest available: **do not
predict anything.**

Instead of working out where the glass will stop, it pushes the glass a little
way in a direction that must be an improvement, looks at the table again, and
repeats. A direction away from the neighbour that is crowding a glass is an
improvement for any friction whatever, so the direction cannot be wrong. The
distance is deliberately too small, so overshooting is impossible. What remains
is a method that makes no claim it could be wrong about.

That is what makes it the control for the whole comparison. It cost no data, no
training time and no hardware, so a solution that merely matches it has earned
nothing.

![The camera measures the table, the glass with the worst shortfall of clear room is chosen along with the neighbour responsible for it, the glass is checked against the tipping rule, and it is pushed a fixed fraction of the shortfall straight away from that neighbour before the arm looks again.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-flow-what-it-does.png)

![Predicting where a pushed glass stops needs the friction and the weight distribution that nobody in this cell has measured, so this method makes no prediction at all: the direction is right for any friction and the travel is deliberately too small, which leaves a smaller shortfall rather than an overshoot.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-flow-repeat-not-predict.png)

## 2. How it works

The arithmetic is one quantity, computed again after every push.

**The shortfall.** For each glass, the method works out how much clear room the
gripper is short of, measured to the nearest edge of each neighbour rather than
to the neighbour's middle, because it is the neighbour's edge that the gripper's
fingers would hit. The glass with the worst shortfall is the one to push, and
the neighbour responsible for that shortfall is the one to push away from.

**The tipping check comes before anything else.** A push applied too high up a
glass tips it over instead of sliding it, and the height at which that happens
follows from the glass's foot width and its height. The jaw rides at a fixed
height belonging to the gripper, so for each glass the method can say in advance
whether a push is safe. If it is not, the method refuses rather than pushing. The
refusal is arithmetic, not a judgement, and it happens before any choosing.

**The heading is a line, not a search.** The jaw is pointed along the line that
runs from the neighbour's middle through the glass's middle, which is directly
away from the neighbour. There is no sweep over directions and no map of the
free table.

**The travel is a fixed fraction of the shortfall.** It is not the whole
shortfall, and the fraction is the method's one constant. Pushing a fraction
means the glass always moves less than it needs to, so the method never
overshoots; the remaining shortfall is simply smaller next time, and repeated
pushes close the gap. That constant was chosen by arguing about convergence and
then frozen, which is the entire configuration of the method.

**Then it looks again.** The camera measures the table afresh and the same
arithmetic runs on what it now sees. The loop ends when every glass has room,
when the push budget is spent, or when the only honest answer left is a refusal.

Each push is handed over as three numbers — where to start, which way, how far —
and the examiner's own macro expands those into the jaw trajectory that every
solution in this book is judged on. Carrying the jaw there is the cell's job: on
the examiner the physics engine does it, and in the real cell MoveIt does.

## 3. What it needs

Everything it needs is either already produced by the camera work or is a
constant belonging to the gripper, which is why it could be built first.

**The measurements, and nothing beyond them.** Each glass's position and widest
width, which the room test and the shortfall need, and each glass's foot width
and height, which the tipping rule needs. It does not use the view from the top,
it does not use the force the jaw felt beyond whether it touched anything, and
it never reads the simulator's record.

**The gripper's own numbers**, such as the clear room the fingers need and the
height the jaw rides at. These belong to the hardware rather than to any glass,
so the project allows them to be written down, and none of them is tuned.

**One constant of its own**, the fraction described above.

**One library, and it is NumPy.** Nothing is fitted, so there is no weights file
to redistribute and no licence inherited from anybody else's training data.

**No accelerator, and the figure is zero.** The whole decision is a few hundred
arithmetic operations over four to six glasses, and it finishes long before the
arm has moved anywhere. On the compute column of the scorecard this solution is
the zero the others are read against.

What it does need is **arm time**, paid in pushes and in looks, and the budget
is what bounds them.

## 4. What it scored

Every solution is given the same 50 tables holding 251 glasses, of which 193
have no room at the start, spends the same push budget, and is judged by the
same scorecard, which [the examiner](../02_the-examiner.md) describes. A
table is **done** when every glass on it could be picked up, and **wrong** when
the run ended in a state the cell should never reach.

| tables done | tables wrong | glasses racked | toppled | pushes |
|---|---|---|---|---|
| **33** | **0** | 195 | **0** | 213 |

**It finished more tables than any of the other five, and it broke nothing.**
Those are the two columns that matter most, and this solution holds the best
figure in both. The only solution that racked more glasses is [a world model,
then plan with it](05_a-world-model-then-plan-with-it.md), which did it in half
the pushes and toppled one glass doing so.

One more property of this row is worth knowing. Nothing in this method was
fitted and nothing in it is drawn at random, so it behaves the same way on the
hundredth table as on the first. The repeated runs the examiner requires of the
trained solutions, because their training and their actions both vary, are not
needed here, so this is the one row in the book that carries no spread. The full
table for all six is in [the results](../10_the-results.md).

## 5. Where it is strong and where it breaks

Its strengths all follow from how little it claims, and so do its weaknesses,
which is what makes it a clean control rather than merely a weak solution.

**It cannot be wrong about pushing, because it says nothing about pushing.**
Every other solution has a prediction somewhere that can be wrong. This one has
a direction that is right for any friction and a distance that is deliberately
too small.

**Its answer can be read.** Every step is a number that can be printed, and
every refusal has a reason that can be checked with a ruler.

**Short pushes are safe pushes.** Every millimetre of travel is a millimetre in
which something can be knocked, so a method whose instinct is to move a glass as
little as possible has a good instinct, and the small fraction gives it that
instinct for free.

**It exercises the whole contact sequence**, with no planning code in the way.
When something falls over while this book's work is being built, this method
tells you the fault was in the contact, because there was no plan to be wrong.

The weaknesses are real and they are structural.

**It has nowhere to stand.** The approach runs along the same line as the push,
so pushing a glass straight away from its neighbour asks the arm to put a long
tool where the neighbour is. In a tight group that is impossible, and the method
cannot offer a second heading, so it refuses. **The approach is a harder
constraint than the departure**, and this is the solution that cannot choose its
approach at all.

**It cannot help a glass crowded from two sides**, because a push away from one
neighbour is a push towards the other. No value of the fraction fixes that; the
difficulty is in the direction.

**It never looks at the free table.** The shortfall says how far and nothing
says where to, so the method does not ask whether the place it is sending a
glass is empty, inside the glass zone, within the arm's reach, or clear of the
rack. A push that drives one glass into another is the failure this creates, and
it is also the one that cannot be recovered.

**It throws away the force report.** What the jaw felt and how far the glass
moved for it are the only evidence this cell can produce about the friction, and
the method reads none of it. That is exactly why every other solution has
something to improve on.

## 6. When to choose it

Choose this first, always. It is the cheapest way to get a real push happening
against a real glass, every later solution needs the same contact sequence and
the same refusals, and it gives the comparison its floor before anything
expensive is built.

Think hard before shipping it, and the reason is not its score. It has one
heading to offer, it cannot help a glass crowded from two sides, and it never
asks whether the place it is sending a glass is clear. On this book's fifty
tables those limits cost it seventeen unfinished tables and nothing worse,
because a refusal is an acceptable answer here. In a cell where a refusal is not
acceptable, they would matter much more.

Read it in both directions. The usual reading is about the other five: if a
model cannot beat a fixed nudge, it has earned nothing. The other reading is
about the problem. This method works at all only because the glasses stand
upright on a flat table, the gripper's clear room is a known constant, the
camera reports a position and a width for every glass, and a refusal is an
acceptable answer. **Each of the other five needs fewer of those promises than
this one does**, and that is what they are for.

The code is in
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge)
and it writes its own `results.json` beside itself. The full treatment, with
open and closed loop explained, why the push is a fraction rather than all of
the shortfall, and why repeating replaces predicting, starts at [what it
is](../04_one-fixed-nudge/01_what-it-is.md).

← [The six solutions — same table, six ways to push](01_how-the-six-compare.md) · [Geometry generates, a model ranks](03_geometry-generates-a-model-ranks.md) →
