# Questions and answers

This page answers the questions readers often ask about the problem itself. It
is for a reader who has read the pages before it, or who wants a quick answer
first. Each answer is short. Each one links to the section that explains it in
full. The questions about one solution are on that solution's own questions
page.

## Contents

1. [What is this problem asking the arm to do?](#1-what-is-this-problem-asking-the-arm-to-do)
2. [Why push glasses apart at all, and why not lift a crowded glass straight out?](#2-why-push-glasses-apart-at-all-and-why-not-lift-a-crowded-glass-straight-out)
3. [What does "crowded" mean, and how does the arm know a glass is crowded?](#3-what-does-crowded-mean-and-how-does-the-arm-know-a-glass-is-crowded)
4. [Why is pushing harder than picking?](#4-why-is-pushing-harder-than-picking)
5. [What makes a glass topple, and why is toppling the failure that matters most?](#5-what-makes-a-glass-topple-and-why-is-toppling-the-failure-that-matters-most)
6. [Does a slower push topple fewer glasses?](#6-does-a-slower-push-topple-fewer-glasses)
7. [Why is a refused glass a result and not a failure?](#7-why-is-a-refused-glass-a-result-and-not-a-failure)
8. [What does the arm know before a push, and what must it find out by touch?](#8-what-does-the-arm-know-before-a-push-and-what-must-it-find-out-by-touch)
9. [What is the examiner, and why is there one examiner for all solutions?](#9-what-is-the-examiner-and-why-is-there-one-examiner-for-all-solutions)
10. [How does the examiner draw a table, and what is a table seed?](#10-how-does-the-examiner-draw-a-table-and-what-is-a-table-seed)
11. [What is a solution given at each look and push?](#11-what-is-a-solution-given-at-each-look-and-push)
12. [Why is the output a path for the jaw, not a command like "push this glass left"?](#12-why-is-the-output-a-path-for-the-jaw-not-a-command-like-push-this-glass-left)
13. [What does a push report back, and why does it matter?](#13-what-does-a-push-report-back-and-why-does-it-matter)
14. [Why is the score the table afterwards, not the action?](#14-why-is-the-score-the-table-afterwards-not-the-action)
15. [How can one glass end, and how can a whole table end?](#15-how-can-one-glass-end-and-how-can-a-whole-table-end)
16. [Why is there a limit on pushes per glass and per table?](#16-why-is-there-a-limit-on-pushes-per-glass-and-per-table)
17. [What are the held-out tables, and why are they used only once?](#17-what-are-the-held-out-tables-and-why-are-they-used-only-once)
18. [Which parts are shared by all solutions, and which part is each solution's own?](#18-which-parts-are-shared-by-all-solutions-and-which-part-is-each-solutions-own)
19. [What is the top view, and why does the camera look straight down?](#19-what-is-the-top-view-and-why-does-the-camera-look-straight-down)
20. [How does the project avoid writing down any glass's size?](#20-how-does-the-project-avoid-writing-down-any-glasss-size)
21. [Why does the gripper's shape appear in the rules when the glass's shape does not?](#21-why-does-the-grippers-shape-appear-in-the-rules-when-the-glasss-shape-does-not)
22. [What changed when the invented blade was replaced by a real gripper?](#22-what-changed-when-the-invented-blade-was-replaced-by-a-real-gripper)

## 1. What is this problem asking the arm to do?

Some glasses stand too close together for the gripper to pick them up. The arm
must drag them apart across the table until every glass has room. It must not
knock any glass over. [What is asked for](01_what-is-asked-for.md) states the
whole question.

## 2. Why push glasses apart at all, and why not lift a crowded glass straight out?

To lift a glass, the arm needs its side shape. To measure that shape, it needs
a clear photograph from the side. The crowding blocks that view. A push needs
much less: where the glass stands and how wide its foot is. [Why dragging and
not lifting](01_what-is-asked-for.md#3-why-dragging-and-not-lifting) explains
this circle.

## 3. What does "crowded" mean, and how does the arm know a glass is crowded?

The open hand needs 76 mm of clear room around a glass's middle. A glass is
crowded when a neighbour's edge is closer than that. The arm checks this from
the positions and widths that `look()` gives. [The gap that
matters](01_what-is-asked-for.md#6-the-gap-that-matters-is-not-the-gap-between-the-glasses)
explains why the test uses the neighbour's edge.

## 4. Why is pushing harder than picking?

A push does not land exactly where it was aimed. The glass slides and turns,
and the friction under it is unknown. A push can also tip the glass over. So
the arm must look again after every push. [What else makes this
hard](01_what-is-asked-for.md#8-what-else-makes-this-hard) lists the reasons.

## 5. What makes a glass topple, and why is toppling the failure that matters most?

A glass tips when the jaw touches it too high for its foot and the friction.
Nothing in this cell can stand a fallen glass back up, so a topple is final.
The limit is the same for every solution. Six of the seven check it before any
model is asked. [The limit: slide, or
tip](05_pushing-without-toppling.md#3-the-limit-slide-or-tip) gives the rule.

## 6. Does a slower push topple fewer glasses?

No. Speed does not appear in the tipping rule. A test at a quarter of the
normal speed toppled 19.9% of glasses, against 18.0% at the normal speed. That
difference is noise. [A slower push does not topple fewer
glasses](05_pushing-without-toppling.md#a-slower-push-does-not-topple-fewer-glasses)
gives the full table.

## 7. Why is a refused glass a result and not a failure?

Some glasses tip before they slide, whatever the arm does. For them, refusing
is the only correct answer. A refused glass is still standing, so nothing is
lost. A refusal with a reason scores *correct but incomplete*. [Some glasses
cannot be pushed at
all](05_pushing-without-toppling.md#some-glasses-cannot-be-pushed-at-all)
explains this.

## 8. What does the arm know before a push, and what must it find out by touch?

Before a push, the arm knows each glass's position, height and widths, each with
a small error. It also knows its own gripper's size. It is never told the
friction, because nothing in a real cell can measure it. Only the force felt
during a push gives evidence of it. [What a solution is never
told](02_what-goes-in-and-what-comes-out.md#4-what-a-solution-is-never-told)
explains why.

## 9. What is the examiner, and why is there one examiner for all solutions?

The examiner is the shared code that draws the tables, runs the physics and
marks each run. One examiner gives every solution the same question and the
same marking. So a difference in score comes from the method alone. [Why there
is an examiner at
all](03_the-examiner.md#2-why-there-is-an-examiner-at-all) explains this.

## 10. How does the examiner draw a table, and what is a table seed?

A table seed is the number a table is made from. The same seed always gives the
same table. The examiner places four to six glasses of one kind, many of them
close together. It keeps a table only if at least one glass has no room. [What
the examiner draws](03_the-examiner.md#3-what-the-examiner-draws) gives the
details.

## 11. What is a solution given at each look and push?

A look gives one row per glass: its number, position, height, widest width,
foot width, and whether it stands. Four of the seven solutions also get a
picture from above. After each push, the solution gets a short report of what
the jaw felt. [What `look()` hands
over](02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over) shows a
real look.

## 12. Why is the output a path for the jaw, not a command like "push this glass left"?

Some solutions think in a few push numbers. Others give a short run of
waypoints at once. A path is the one output both can give. Forcing everyone into
a few numbers would damage the policies that give waypoints. [What must come
out](02_what-goes-in-and-what-comes-out.md#6-what-must-come-out) explains this.

## 13. What does a push report back, and why does it matter?

A push reports five things. Was the hand blocked on the way down? How far did
it move before it touched? Did it get stuck? What was the largest force, and
how far did it really push? This is the only evidence about friction. [Why the
force reading
matters](02_what-goes-in-and-what-comes-out.md#why-the-force-reading-matters)
explains its value.

## 14. Why is the score the table afterwards, not the action?

Solutions give different kinds of action, so no single way to mark an action is
fair to all. The table afterwards is the same kind of thing for every solution.
The examiner asks only which glasses have room and which still stand. [The
score is the outcome, not the
action](03_the-examiner.md#4-the-score-is-the-outcome-not-the-action) explains
this.

## 15. How can one glass end, and how can a whole table end?

A glass is racked, refused with a reason, or wrong. A glass is wrong if it
toppled, left the glass zone, was picked without room, or was left with no
reason. A table is done, correct but incomplete, or wrong. "Wrong" is final,
because no step can undo a fall. [What the examiner
measures](03_the-examiner.md#5-what-the-examiner-measures) lists every count.

## 16. Why is there a limit on pushes per glass and per table?

A push can knock a glass over, and a look cannot. So pushes are limited to 4
per glass and 16 per table, the same for every solution. Looks have no limit.
When a limit is reached, every glass still standing is refused with a reason.
[What the examiner measures](03_the-examiner.md#5-what-the-examiner-measures)
explains the budget.

## 17. What are the held-out tables, and why are they used only once?

The held-out tables are the 50 test tables, with 251 glasses. No solution
trains on them. No setting is tuned on them either, because a number chosen to
score well there would bias every result. Each run uses the same 50 tables.
[What the examiner draws](03_the-examiner.md#3-what-the-examiner-draws)
explains the split.

## 18. Which parts are shared by all solutions, and which part is each solution's own?

The examiner, the tipping limit, the target layout and the loop of push and
look again are shared. Each solution owns only how it chooses the next push.
[Why this is shared and not a
solution](04_the-target-layout.md#5-why-this-is-shared-and-not-a-solution)
gives the rule: the shared part is everything not being compared.

## 19. What is the top view, and why does the camera look straight down?

The top view is a colour picture, 384 by 384 pixels. A fixed camera takes it
from 750 mm above the middle of the glass zone. It looks straight down, so it
shows the whole zone the same way on every table. A policy cannot be compared
with itself if its view moves. [What `look()` hands
over](02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over) describes
it.

## 20. How does the project avoid writing down any glass's size?

The rules a solution follows never fix a glass's size. Every size comes from
`look()`, for that glass on that table. The safe push height is then worked out for each
glass. [The push height is worked out per
glass](05_pushing-without-toppling.md#the-push-height-is-worked-out-per-glass)
explains this pattern.

## 21. Why does the gripper's shape appear in the rules when the glass's shape does not?

The gripper is one real product, and its size never changes. So its numbers
can be written down once: 76 mm of room, 75 mm and 107 mm of height. Glasses
differ on every table, so their sizes must be measured each time. [The height
that counts is the top edge of the
jaw](05_pushing-without-toppling.md#the-height-that-counts-is-the-top-edge-of-the-jaw)
uses both kinds of number.

## 22. What changed when the invented blade was replaced by a real gripper?

The problem first assumed a thin made-up blade. The real Robotiq 2F-85 is
139 mm across when held normally. It could hardly fit between the glasses. So
the hand is turned on its side, where it is 27 mm across. But then it rides at
75 mm instead of 50 mm, which makes tipping more likely. [The
jaw](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/bench/README.md#the-jaw)
gives the measurements.

← [Pushing without toppling](05_pushing-without-toppling.md) · [The seven solutions — same table, seven ways to push](../03_the-seven-solutions/01_how-the-six-compare.md) →
