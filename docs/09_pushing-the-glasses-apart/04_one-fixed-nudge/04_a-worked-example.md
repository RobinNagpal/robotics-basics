# A worked example

This page follows this solution through one arrangement of glasses from
beginning to end, with real numbers rather than a description of what would
happen. It then takes the case this book keeps returning to, a glass that
cannot be pushed safely, because a worked example that shows only the easy case
teaches the wrong lesson. By the end you will have seen both what this solution
does well and where it is left with nothing to say.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

Step 5 of that loop is the one that can end a glass's part in the run without
touching it, and it is worth taking slowly, because a refusal here is a correct
answer rather than a failure.

A pushed glass slides while the jaw touches it below a height set by half the
width of its foot divided by the friction between the glass and the table, and
tips above that height. The arm cannot choose that height freely. The middle of
the jaw rides as low as the gripper goes, which is 50 mm above the table,
and the jaw is 30 mm tall, so its **top edge** stands at 65 mm. The height that
counts in the rule is the top edge and not the middle, because a glass that is
wider higher up meets the top edge before any other part of the jaw touches it,
and the tapered glass is wider higher up by definition. So the limit is checked
against 65 mm, and the 15 mm difference is not a rounding question: it falls
entirely in the direction that topples glasses, since every glass the lenient
check wrongly admits is a glass that will be touched above its limit.

![The height at which a push starts tipping a glass, drawn against the foot it stands on, with the jaw's middle at 50 mm and its top edge at 65 mm ruled across it: the push lands on the top edge, those 15 mm cost most of the glasses that the jaw's middle would have been allowed to touch, and the three friction lines, one of which is the simulator's own and none of which the arm is told, give three different answers about the same glass.](../../images/pushing-the-glasses-apart/one-fixed-nudge/02-the-friction-ceiling.png)

The friction in that rule is the number nobody has, so the check is made at
both ends of the range that glass on a dry wooden top plausibly covers, and the
three possible answers are the three the built code already distinguishes. A
glass whose foot is wide enough to slide even at the high end of the range is
safe to push. A glass that tips even at the low end **is refused**, with the
reason that it tips before it slides, and no amount of looking again helps,
because the refusal is a statement about that glass rather than about the
arrangement. A glass that the range cannot settle is given a small test push
and looked at: a glass that slid has moved, and a glass that leaned and fell
back where it stood has not, so the test answers directly a question no
arithmetic in the cell can answer. That test is the one place in this entire
method where the arm reads the world before committing to a decision rather
than after it.

This method has a second reason to refuse, and it is the one that costs it
most, because it follows from the very decision that makes it simple. The jaw
pushes along the direction it points, so **the approach runs along the same
line as the push**, and pushing a glass straight away from its neighbour means
coming in from the neighbour's side. The tool behind the fingertips is 270 mm
long and its body is 90 mm across, and all of it sits at the height of the
push, so all of it has to miss everything standing on the table. In a tight
group the blocking neighbour is standing exactly where the tool would have to
be. This method has one heading to offer and no way of choosing another, so
when that heading is blocked the only honest answer is to refuse with the
reason that there is nowhere clear to push the glass from. Every solution that
searches over headings can ask for a different approach; this one cannot, and
that is the sharpest statement of what the simplicity costs.

Two rules complete the refusal path, and both are shared with every other
solution. A glass that is already lying on its side ends the run, because
nothing in this project stands a glass back up and the arm does not work next
to one. And **no refusal has a fallback that tries anyway.** A glass that was
refused is still a glass standing on a table, and something later may yet move
it or be told to leave it. A glass that was pushed and went over is finished,
and the arm carries on working beside it.

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
