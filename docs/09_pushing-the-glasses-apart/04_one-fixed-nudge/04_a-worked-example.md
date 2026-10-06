# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that cannot be pushed safely,
because a worked example that shows only the easy case teaches the wrong
lesson.

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
leaves the limit undecided, and it is **arithmetic applied before any model is
consulted** in five of the six solutions. What follows is only what is this
solution's own.

**This solution has a second reason to refuse, and it is the one that costs it
most.** The jaw pushes along the direction it points, so the approach runs
along the same line as the push, and pushing a glass straight away from its
neighbour means coming in from the neighbour's side. The tool behind the
fingertips is 270 mm long and 90 mm across, all of it at the height of the
push, so all of it has to miss everything on the table — and in a tight group
the blocking neighbour is standing exactly where the tool would have to be.

This method has one heading to offer and no way of choosing another, so when
that heading is blocked the only honest answer is that there is nowhere clear
to push the glass from. **Every solution that searches over headings can ask
for a different approach; this one cannot**, and that is the sharpest statement
of what the simplicity costs.

![The height at which a push starts tipping a glass, drawn against the foot it stands on, with the jaw's middle at 50 mm and its top edge at 65 mm ruled across it: the push lands on the top edge, those 15 mm cost most of the glasses that the jaw's middle would have been allowed to touch, and the three friction lines, one of which is the simulator's own and none of which the arm is told, give three different answers about the same glass.](../../images/pushing-the-glasses-apart/one-fixed-nudge/02-the-friction-ceiling.png)

## 2. A worked example

The method is small enough that one example can show all of it, so this section
follows two tables through the loop: one where the method is sufficient and one
where it is not. Both are described in relations rather than in sizes, as the
project's rule requires, and both hold glasses of the tapered kind, because
that is the kind whose contact is at the jaw's top edge and therefore the kind
the tipping rule bites hardest on.

### A table where it works

Three glasses stand in the glass zone. Call them A, B and C.

| | where it stands | as this kind goes |
| --- | --- | --- |
| A | the middle of the zone | narrow, standing on a broad foot |
| B | close beside A, further from the arm | the widest the kind allows, on a broad foot |
| C | the far corner of the zone, clear of both | middling |

**The room test.** A needs 70 mm plus half of B's widest width, and B is as
wide as the kind allows, so B's rim reaches well inside A's ring and A is short
of room by some tens of millimetres. Turn the test round and B needs 70 mm plus
half of A's widest width, and A is narrow, so B has room to spare at the very
same distance. C is clear of both. **So A alone is on the list**, which is the
asymmetry doing its work: one gap, two different answers, and the glass with
the problem is the narrow one.

**Can A be pushed.** A stands on a broad foot, so half its foot divided by the
highest friction in the plausible range is still above the jaw's top edge. A
slides at every friction worth considering, so no test push is needed and
nothing is refused.

**The push.** The blocking neighbour is B, so the heading is the direction from
B's middle through A's middle, continued outwards. The travel is the gain times
A's shortfall, which is a fraction of what A needs rather than all of it. The
fingertips come down on that line, a little outside A's widest part, and feel
forward until they touch. The push is made, the jaw backs off and lifts.

**Look again.** A has moved most of the commanded distance, so its shortfall is
smaller but not zero. Nothing else on the table changed, because A moved along
the line away from B and C was never near either of them. The second pass does
the same arithmetic on the smaller shortfall and therefore makes a shorter
push, and the third pass finds A's shortfall at or below zero and stops
pushing. A is then racked, and so are B and C.

**What that cost.** Three pushes and four looks, where a method that computed
the right distance in one go would have spent one push and two looks. Each push
was shorter than the one before it, which is what a geometric sequence looks
like on a real table. Nothing was knocked over, nothing left the glass zone,
and no claim about friction was made at any point. That is the whole bargain of
this solution in one table: it pays in arm time and buys immunity from being
wrong.

### A table where it does not

Four glasses, and the difference is that one of them is crowded from two sides.

| | where it stands | as this kind goes |
| --- | --- | --- |
| A | the middle of the zone | middling, on a broad foot |
| B | close beside A, further from the arm | wide |
| C | close beside A on the opposite side, nearer the arm | wide |
| D | a corner of the zone, clear of everything | middling, on the narrowest foot the kind allows |

**A is short of room against both B and C.** The blocking neighbour is whichever
of the two reaches further into A's ring, so say it is B. The heading is
straight away from B, and because C stands on the opposite side, straight away
from B is straight towards C. The push reduces A's shortfall against B and
increases its shortfall against C by about the same amount. The worst of the two
is what the method measures, so the next look finds A short of room against C
instead, asks for a push straight away from C, and undoes the first push. **The
method oscillates between two directions and spends its budget**, and no choice
of gain changes that, because the problem is the direction and not the
distance. When the budget runs out the glasses that are left are reported with a
reason, which scores the table as correct but incomplete rather than wrong.

That is the structural failure, and it is worth seeing why the next solution in
the set does not share it. A push that moved A sideways, along a line that is
away from neither B nor C but out of the gap between them, would free A in one
go. Such a push exists on this table; the information needed to find it is
already in the measurements; and finding it needs a search over directions,
which is precisely what this method gave up in exchange for being one
multiplication.

**The same table also shows the approach failure.** If B and C stand closer to
A than the tool is long, then pushing A away from B asks the arm to put 270 mm
of tool where B is standing, and pushing A away from C asks the same of C's
place. The method has no third heading to offer, so it refuses A with the
reason that there is nowhere clear to push it from. The refusal arrives before
any push is attempted, which is the right order, and the table ends as correct
but incomplete with nothing knocked over.

**And D shows the refusal that is nobody's fault.** D is clear of every other
glass, so it is never on the list at all and is simply racked. But if D had
been crowded, it would have been refused, because it stands on the narrowest
foot its kind allows: half that foot divided by even the low end of the
friction range is below the jaw's top edge, so D tips before it slides at any
friction the cell might have. No method in the set can push D, and the only
correct answer for it is a refusal with the reason.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
