# Questions and answers

## 1. Introduction

The four pages before this one explain the problem, the three calls a solution
may make, the examiner that marks a run, and the rule that decides whether a
glass slides or tips. This page answers four questions that readers ask after
those pages. Each answer is one paragraph. It is written for a reader who
already knows the shape of the problem and now wants the exact sizes. Every
number here was printed by the code that produces it.

## Contents

1. [Introduction](#1-introduction)
2. [What does a look give back, and what shape is it in?](#2-what-does-a-look-give-back-and-what-shape-is-it-in)
3. [What does a push take, and what shape is it in?](#3-what-does-a-push-take-and-what-shape-is-it-in)
4. [How many looks and pushes is a solution allowed?](#4-how-many-looks-and-pushes-is-a-solution-allowed)
5. [How many runs are there altogether?](#5-how-many-runs-are-there-altogether)

## 2. What does a look give back, and what shape is it in?

A look gives back a list. The list has one row for every glass still standing on
the table. Each row has seven fields: the glass's number, its position as an x
and a y, its total height, its widest diameter, the width of the foot it stands
on, and whether it is still standing. All lengths are in metres. A glass counts
as standing while it leans less than 20 degrees. A glass that has been taken to
the rack drops out of the list, so the list gets shorter as the table is
cleared. The numbers are measurements, not facts. The examiner adds a new error
every time: about 0.5 mm on the position, 2.5 mm on the two widths and 1.2 mm on
the height. Two looks at the same glass therefore give two slightly different
answers. Three of the six solutions read pictures instead of numbers. They are
given the same table at the same moment, as a 384 by 384 colour picture taken
from straight above. [What goes in and what comes
out](02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over) explains the
error in full.

A look at table 10025 starts like this:

```json
[
  {"id": 0, "x": 0.4570, "y": -0.4170, "height": 0.1554, "widest": 0.0740, "foot": 0.0419, "standing": true},
  {"id": 1, "x": 0.5489, "y": -0.2464, "height": 0.1360, "widest": 0.0871, "foot": 0.0462, "standing": true}
]
```

## 3. What does a push take, and what shape is it in?

A push takes one object with six fields: which glass to move, the point where
the fingertips come down, the heading the hand points along, how far to feel
forward before giving up, how far to push after touching, and where the solution
expects the glass to stop. The lengths are in metres and the heading is in
radians. That last field is called the aim, and the arm never uses it. The
examiner keeps it so that it can measure later how far the glass really stopped
from where the solution expected it. A push is a request, not a movement. The
examiner turns every push into the same sequence of moves for all six
solutions: come down to 75 mm above the table, feel forward until a light touch,
push the asked distance, back off, and lift. What comes back has five fields. It
says whether the hand was blocked on the way down, how far it moved before it
touched anything, whether it jammed, the largest force it felt, and how far it
really pushed. This reply is the only thing a solution ever learns about its own
push.

Here is one push on table 10025, and the reply to it. The force is in newtons.

```json
{"glass": 4, "start": [0.3726, -0.4500], "heading": 1.5708, "reach": 0.0881, "travel": 0.0660,
 "aim": [0.3726, -0.3259]}
```

```json
{"blocked": false, "touched": 0.0146, "jammed": false, "peak": 1.73, "pushed": 0.0660}
```

## 4. How many looks and pushes is a solution allowed?

Pushes are limited and looks are not. On one table a solution may use 16 pushes
in total, and 4 pushes at any single glass. The same two numbers apply to all six
solutions, because the budget belongs to the examiner and not to each solution.
When either limit is reached, every glass still standing has to be refused with
a reason. The table then scores as correct but incomplete, not as wrong. Looks
have no limit at all, so a solution may ask for one as often as it likes.
Solution 1 uses that freedom on purpose. After a test push it takes several
looks and averages them. The error is new each time, so an average of several
looks is closer to the truth. The difference between the two limits is
deliberate. A look cannot break anything, while a push can knock a glass over,
and a glass on its side is never stood up again. Thinking time is measured for
every solution and reported beside the scores, but it is not limited. [The
examiner](03_the-examiner.md#5-what-the-examiner-measures) says how both are
counted.

## 5. How many runs are there altogether?

There are three levels here and they are easy to mix up. Inside one table, the
loop repeats until no glass needs a push, or until the push budget is spent. The
number of rounds is therefore not fixed, and it is itself one of the things
being measured. One run is always the same 50 tables. They are numbered from
10000 and hold 251 glasses in total, and no solution is ever trained on them.
Solutions 1, 2 and 4 are run once each, because each of them answers the same
way every time it is asked. The other three pick their actions at random, so
each of them is run three times over the same 50 tables and reports the spread.
For the imitation policy those three runs are three separately trained models.
For the two borrowed models they are three runs of one trained model, which is a
weaker test. [The results](../10_the-results.md) prints the spread for all three
and says where it is weaker than it should be.

← [Pushing without toppling](05_pushing-without-toppling.md) · [The six solutions — same table, six ways to push](../03_the-six-solutions/01_how-the-six-compare.md) →
