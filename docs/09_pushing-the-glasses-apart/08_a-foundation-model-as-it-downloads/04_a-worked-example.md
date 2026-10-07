# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and first through the case this book keeps returning to, a glass that
cannot be pushed safely, because a worked example that shows only the easy case
teaches the wrong lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

A glass slides while the jaw touches it below half its foot width divided by
the friction, and tips above that. The height that counts is the jaw's **top
edge** at 65 mm, not the 50 mm its middle rides at, and for a glass whose foot
is narrow enough there is no contact height the arm can offer below the limit.
The only correct answer for such a glass is to refuse, with the reason
recorded, which marks the run *correct but incomplete* rather than wrong.
[Pushing without toppling](../01_the-problem/03_pushing-without-toppling.md)
sets all of that out once, including what is done when the unknown friction
leaves the limit undecided. It is **arithmetic applied before any model is
consulted**, in all six solutions: the rule is `slides()` in solution 1's
`plan.py`, and this solution imports it rather than writing its own, so the six
refuse exactly the same glasses.

**It is just as well that the refusal is arithmetic, and the reason is the
point of this whole document.** Nothing in a borrowed model's pretraining knows
this cell. The limit depends on a foot width the camera work measures, on a jaw
height that is this gripper's own number, and on a friction coefficient nothing
in this cell measures at all. A model fitted on other people's robots has met
none of the three and cannot acquire them from a picture of plain shapes.
Asking it to respect a limit it cannot compute would be asking it to guess, and
a toppled glass is the one mistake this problem cannot absorb.

There is a second half. Removing a glass from the task does not remove it from
the picture, so a model that reads the picture can still aim at a refused
glass, and a solution that emits waypoints freely can emit a contact higher
than the jaw rides at. **So the trajectory that comes back is read rather than
trusted**: one that would reach a refused glass is thrown away, and the heights
in the rest are bounded into the range the jaw rides at. Both checks are built,
in `clear.py` and `joining.py`, and they sit in this solution's own folder
rather than in the examiner.

How much that first check was needed is worth reporting, because the answer is
not at all. Over the three runs the model was asked 2,260 times, and **not one
of its trajectories was thrown away for reaching a refused glass**. Section 2
explains why: the trajectories do not come down far enough to reach any glass,
refused or not.

## 2. A worked example

Following one of the examiner's own tables through makes the measured behaviour
easier to recognise, because the parts of it appear together rather than one at
a time.

**The table.** Take the second of the 50 held-out tables, which the examiner
draws from seed 10001. It holds six tapered glasses between 109 and 211 mm
tall, from 75 to 104 mm across at their widest, standing on feet between 35 and
45 mm across. Three of the six are crowded at the start: a neighbour's rim
reaches inside the 70 mm of clear room the open jaw needs round them.

**The shared machinery runs first**, and on this table it changes nothing. It
asks `slides()` about every glass from its measured foot, and no glass fails.
That is not special to this table. Over all 251 glasses on the 50 held-out
tables, the rule refuses none of them on their true sizes, and on the sizes the
camera reports — which carry its own measurement error — it refuses at most one
glass in a whole run. So the topple refusal, which the rest of this book spends
a chapter on, hardly binds here, and almost none of this solution's shortfall is
explained by it.

**Then the model is asked.** It receives the rendered view from the top, the
unvarying sentence, and the jaw's parked pose. What comes back is 50 waypoints,
and the measured shape of those answers is the result of this solution. The
median answer's lowest point is 209 mm above the table. Five of this table's
six glasses are shorter than that, so the jaw passes over them without touching
anything. The same answer travels 844 mm across the table, which is further
than the picture's frame is wide, in waypoints 14.3 mm apart — more than the
arm's own top speed, and fourteen times the speed a push macro moves at.

So what the examiner records is a push that happened and touched nothing. That
costs one entry against the budget of 16 pushes per table. **Then the arm looks
again**, the arrangement is unchanged because nothing moved, the model is asked
once more, and the same thing happens. Across a run of 50 tables this solution
spends 754 pushes, which is a little over 15 per table against a budget of 16,
so almost every table runs to the end of its budget. 674 of those 754 pushes
never touched anything.

The 80 that did touch something are the other half of the story. 69 of them
jammed: the jaw arrived at a glass at more than the speed the arm is meant to
move and wedged against it instead of sliding it along. That is where this
solution's toppled glasses come from — 6 in this run, and between 5 and 8 in
the three — and why a glass it does move lands a
median of 74 mm from where the trajectory ended rather than the millimetre or
two solution 1 manages.

A table that goes that way ends with its already-free glasses racked, its
crowded ones refused for want of room, and the outcome *incomplete*. **No table
in any of the three runs was finished.** Put the counts side by side and there is nothing
left over: 58 of the 251 glasses had room before anything was pushed, and 56
were racked. Racking a glass loosens its neighbours, so a solution that freed
anything at all would rack more than 58. This one racks fewer.

The instructive part is what this run does **not** look like. The failure this
solution was written to expect was a well-formed push aimed at the wrong glass,
which nothing downstream would notice. That is not what happened, and the
difference is worth holding on to, because a failure that the scorecard counts
directly — a push that touched nothing — is a far easier thing to diagnose than
a push that looks right and is not. The reasoning about the domain gap in [how
it works](03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
stands. The guess about which way the gap would show did not.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
