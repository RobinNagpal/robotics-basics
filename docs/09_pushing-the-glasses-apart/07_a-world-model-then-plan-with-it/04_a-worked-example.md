# A worked example

This page starts with this solution's refusals, because an example that shows
only the easy case teaches the wrong lesson. Then it follows the solution
through three of the examiner's 50 test tables. Each number for a table comes
from the run recorded in
[`results-tables.json`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/results-tables.json).

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

A planner must know when not to push. This section shows how this solution
refuses a glass.

[Pushing without toppling](../01_the-problem/05_pushing-without-toppling.md)
gives the shared rule for when a glass would tip instead of slide. This
solution does not apply that rule yet. [The main
idea](01_what-it-is.md#4-the-main-idea) explains this gap.

Instead, the planner has its own refusals, based on the model. It can refuse a
glass in two ways, and it records which one.

- **Every candidate was dropped.** All 1,500 candidate pushes for that glass
  failed one of the three filters. So no push got past all five copies of the
  model on all five readings of the table. The reason names the filter that
  dropped the most: the topple veto or the map.
- **No push was worth making.** Some pushes passed the filters. But the best
  push on the whole table would clear less than 2 mm of the missing room.

**On the 50 test tables, only the second kind ever happened.** The run left 85
glasses behind, and
[`results.json`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/results.json)
gives each one's reason:

- 53 were on a table where a glass had fallen over. Nothing more is touched on
  such a table.
- 14 had no push that the model expected to make room.
- 10 were on a table whose 16 pushes were spent.
- 8 had been pushed four times, the most any glass is allowed, and still had no
  room.

No glass was refused because every push was dropped. So the first kind of
refusal exists in the code but did not fire here.

The model has one serious weakness here. It can be sure and wrong, because all
five copies can agree on a wrong answer. [Where it is strong and where it
breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains this.

The next section follows the planner through single tables, step by step.

## 2. A worked example

The section above showed the refusals. This section follows the planner
through three single tables.

The first way can trace any test table step by step. Its folder writes a
picture for each step. It also writes a file with three things for each push:
the 34 numbers the model was given, the 14 numbers each of the five copies gave
back, and the 14 numbers that really happened.

**Table 10004 is the ordinary case.** The first look reports six glasses of one
kind. Several pairs are closer than the 76 mm of clear room the gripper needs.
So no glass can be taken yet, and the planner works on every crowded glass in
turn.

For the first glass, the search draws 600 candidate pushes. They cover every
direction, every point across the glass, and every travel from one to ten
centimetres. All of them go to the five copies, and most fail on the predicted
table:

- the glass would land outside the glass zone, or
- the jaw's path would leave the arm's reach, or
- the predicted movement is much longer than the push.

The topple veto drops more. Some of these really look like they would tip the
glass, such as a short push high on a wide part. For others the five copies
simply disagree. Both count the same. The rest are scored by how much clear
room is still missing afterwards.

Three more rounds narrow the candidates onto the region that scored best. The
same search runs for each of the other crowded glasses. The single best push
over all of them is the one made.

The jaw comes down behind the glass, moves forward until it touches, pushes,
and backs off. Then the arm looks again. This step is what makes the method
work. The glass did not land exactly where the model said. The planner does not
need to know, because it plans again from the new look, not from the
prediction. **Three pushes on three different glasses finish this table, and
all six glasses are racked.**

**Table 10006 ends badly.** It holds five stemmed glasses. The planner makes two
pushes, and one glass falls over. Nothing more is touched on a table with a
glass lying on it. So the other glasses are refused, and the table counts as
wrong.

**Table 10012 ends well.** It holds five straight glasses. The planner makes
three pushes, and all five glasses are racked.

Some pushes go wrong without breaking anything. A push can be blocked on the
way down, when the jaw touches something before it reaches the table. The jaw
then goes straight back up. The loop simply looks again and plans again, so a
blocked push costs one push and nothing else. A table can also end with glasses
refused and nothing broken. The examiner counts that as **correct but
incomplete**, as [the problem](../01_the-problem/01_what-is-asked-for.md)
explains.

This page followed single tables. [Where it sits among the other
five](06_how-it-compares.md#3-where-it-sits-among-the-others) gives the
score over all 50 tables.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
