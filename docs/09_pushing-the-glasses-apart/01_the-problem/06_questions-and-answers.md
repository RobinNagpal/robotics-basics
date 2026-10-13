# Questions and answers

## 1. Introduction

The four documents before this one describe the problem, the three calls a
solution may make, the examiner that marks a run, and the rule that decides
whether a glass slides or tips. This page answers four questions that readers
ask after those, and each answer is one paragraph. It is for a reader who has
understood the shape of the problem and now wants the exact sizes: what a look
hands back, what a push takes, how much of each a solution is allowed, and how
many times the whole thing is run. Every number here was read out of the code
that produces it rather than remembered, and each answer says which document
carries the longer explanation.

## Contents

1. [Introduction](#1-introduction)
2. [What does a look give back, and what shape is it in?](#2-what-does-a-look-give-back-and-what-shape-is-it-in)
3. [What does a push take, and what shape is it in?](#3-what-does-a-push-take-and-what-shape-is-it-in)
4. [How many looks and pushes is a solution allowed?](#4-how-many-looks-and-pushes-is-a-solution-allowed)
5. [How many runs are there altogether?](#5-how-many-runs-are-there-altogether)

## 2. What does a look give back, and what shape is it in?

A look gives back a **list with one entry for each glass still standing on the
table**, and each entry holds seven fields: the glass's number, its position on
the table as an x and a y in metres, its total height, its widest diameter, the
diameter of the foot it stands on, and whether it is still upright. A glass
counts as upright while it leans less than 20 degrees, and a glass that has been
taken away to the rack simply stops appearing, so the list grows shorter as a
table is cleared. The numbers are measurements rather than facts: fresh error is
added on every single look, about half a millimetre on the position, two and a
half millimetres on the two widths and a little over a millimetre on the height,
which is why looking twice at the same glass gives two slightly different
answers. The three solutions that read pictures instead of numbers are given the
same table at the same moment as a 384 by 384 colour picture taken from straight
above, because a list of numbers is not an input they can use. What a look
leaves out matters as much as what it holds, and [what goes in and what comes
out](02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over)
sets that out in full.

A look at table 10025 begins like this, with one row for each of its six
standing glasses and every length in metres:

```json
[
  {"id": 0, "x": 0.4570, "y": -0.4170, "height": 0.1554, "widest": 0.0740, "foot": 0.0419, "standing": true},
  {"id": 1, "x": 0.5489, "y": -0.2464, "height": 0.1360, "widest": 0.0871, "foot": 0.0462, "standing": true}
]
```

## 3. What does a push take, and what shape is it in?

A push takes **one value with six fields**: which glass the push is meant to
move, the point on the table where the fingertips come down, the heading the
hand points and travels along in radians, how far forward to feel for the glass
before giving up, how far to push once something is touched, and where the
solution expects the glass to end up. That last field, the aim, is never used to
move the arm; the examiner keeps it so that it can later measure how far the
glass really finished from where the solution thought it would. The whole value
is a request rather than a movement, which is the point: the examiner expands
every push the same way for all six solutions, bringing the closed hand down to
75 mm above the table, feeling forward until a very light touch, pushing the
requested distance unless the force says something has jammed, then backing off
and lifting. What comes back is equally small, five fields saying whether the
hand was blocked on the way down, how far it travelled before touching anything,
whether it jammed, the largest force it felt, and how far it actually pushed.
That report is the only thing a solution ever learns about its own push, and
[what goes in and what comes
out](02_what-goes-in-and-what-comes-out.md#5-what-push-does-and-what-it-reports-back) explains
how each field is produced.

The push that solution reads from that look, and the reply the examiner gives
back, are these two objects, with lengths in metres and the heading in radians:

```json
{"glass": 4, "start": [0.3726, -0.4500], "heading": 1.5708, "reach": 0.0881, "travel": 0.0660,
 "aim": [0.3726, -0.3259]}
```

```json
{"blocked": false, "touched": 0.0146, "jammed": false, "peak": 1.73, "pushed": 0.0660}
```

## 4. How many looks and pushes is a solution allowed?

Pushes are rationed and looks are not. On any one table a solution may spend at
most **16 pushes in total and at most 4 at any single glass**, and the same pair
of numbers applies to all six solutions, because the budget lives in the
examiner rather than in each solution's own loop. When either limit is reached
every glass still standing has to be refused with a reason, which scores the
table as correct but incomplete rather than wrong. Looks carry no limit at all,
so a solution may call for one as often as it likes, and the fixed nudge uses
that freedom deliberately: when it has made a test push and wants to know
whether the glass slid or merely rocked, it takes several looks and averages
them, because the error is fresh each time and averaging shrinks it. The
asymmetry is not an oversight. A look cannot break anything, while a push can
topple a glass and a toppled glass cannot be stood back up, so the thing worth
rationing is the action and not the observation. Thinking time is measured for
every solution and reported beside the scores, but it is not capped, and [the
examiner](03_the-examiner.md#5-what-the-examiner-measures) says how both are
counted.

## 5. How many runs are there altogether?

There are three levels to this, and they are easy to confuse. Inside a single
table the loop runs until there is nothing left worth pushing or the budget
above is spent, so the number of rounds is not fixed and is itself part of what
is being measured. One **run** is always the same 50 tables, numbered 10000
upwards and holding 251 glasses between them, which are held back from training
so that no solution has ever seen them. The six are then run different numbers
of times, for a reason worth knowing: three of them answer the same way every
time they are asked, so solutions 1, 2 and 4 are run once, while the three that
draw their actions from a distribution are run three times over those same 50
tables and report the spread. For the imitation policy those three runs are
three separately fitted models, which is the stronger test, and for the two
borrowed models they are three evaluation runs of one fitted model, which is the
weaker one. [The results](../10_the-results.md) prints the spread for all three
and says plainly where it is narrower than it should be.

← [Pushing without toppling](05_pushing-without-toppling.md) · [The six solutions — same table, six ways to push](../03_the-six-solutions/01_how-the-six-compare.md) →
