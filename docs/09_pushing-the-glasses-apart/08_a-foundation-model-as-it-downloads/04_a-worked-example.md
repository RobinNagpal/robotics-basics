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

Every solution document in this book answers this question, and this one's
answer is the shortest of the six, because **the answer does not involve the
model at all**.

[Pushing without toppling](../01_the-problem/03_pushing-without-toppling.md) sets out the rule. A
glass slides while the height the jaw touches it is below half its foot width
divided by the friction coefficient, and tips above it. The height that counts
is the top edge of the jaw, which is 65 mm rather than the 50 mm the middle of
the jaw rides at, because a glass that is wider higher up meets the top edge
first. For a glass whose limit falls below that, there is no contact height the
arm can offer that is safe, and the only correct answer is to refuse — the run
ends as *correct but incomplete*, the glass stays where it was, and the reason
is reported.

That check is **applied on the measurements, before any model is consulted.**
A glass that fails it is removed from the task and reported, so the model is
never asked to move it. The arithmetic is shared rather than rewritten here:
it is solution 1's `slides`, in `01-one-fixed-nudge/plan.py`, which solutions
2, 3, 6 and this one import rather than rewrite, so those five refuse exactly
the same glasses. [Solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) is the exception: it judges
toppling with its own learned model and says that the shared gate in front of
it is not there yet. It does not live in the bench, which the second half of
this section comes back to.

**That arrangement is just as well, and the reason is the point of this whole
document.** Nothing in a borrowed model's pretraining knows this cell's jaw or
this kind's foot width. The limit depends on a foot width measured by [the
camera work that tells the glasses
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md), on a
jaw height that is this gripper's own number, and on a friction coefficient
that nothing in this cell measures at all. A model fitted on other people's
robots has met none of those three quantities, and it has no way to acquire
them from a picture of plain shapes. Asking it to respect a limit
it cannot compute would be asking it to guess, and the one mistake this problem
cannot absorb is a toppled glass. So the refusal is taken out of the model's
hands entirely and made arithmetic that runs first.

There is a second half to this. Removing a glass from the task does not remove
it from the picture, so a model that reads the picture can still aim at a
refused glass, and a solution that emits waypoints freely is also free to emit
a contact higher than the lowest the gripper reaches. Nothing in the model's
pretraining would warn it against either. So the trajectory that comes back is
read rather than trusted: one that would reach a refused glass is thrown away,
and the heights in the rest are bounded into the range the jaw rides at.

Both of those checks are built, in `05-smolvla-as-it-downloads/clear.py` and
`joining.py`. This document expected them to sit in the bench beside the
refusal, so that they would be identical for all six and not something a model
can argue with. They do not: the bench grew the straight-down view and the
waypoint path but no shared guard, and the tipping refusal lives in solution
1's folder rather than in the bench either. So the checks are this solution's
own, written to the same rule, and solution 6 should import them from here
rather than write them again. Between them, this solution cannot topple a
refused glass by choosing badly.

## 2. A worked example

Following one crowded table through makes the expectations above easier to
recognise, because they appear together rather than one at a time.

Five glasses of the tapered kind stand in the glass zone. Two of them are
standing deliberately close together, closer than the gripper can work with but
not touching, which is how [the test bench](../02_the-test-bench.md) builds its tables.
A third stands a little way off and is crowded by accident. The remaining two
are clear of everything. One of the close pair is at the narrow-footed end of
what its kind allows, and the tapered kind is wider higher up by definition, so
that glass meets the top edge of the jaw first and its limit is the tightest on
the table.

**The shared machinery runs first.** It evaluates the topple limit for every
glass from its measured foot width, and the narrow-footed glass of the close
pair fails: its limit falls below the jaw's top edge. That glass is refused with
its reason, and it is removed from the task. Four glasses remain as a question
for the model, though the view it is shown still contains all five, so a push
aimed at the refused glass is rejected rather than carried out. The crowding
around that glass is now a problem nothing can solve, which is a correct
outcome rather than a failure.

**Then the model is asked.** It receives the rendered view from the top, the
unvarying sentence, and the joint readings. What would probably come back is a
run of waypoints that is well formed as movement — smooth, at a sensible
speed, descending and then travelling in one direction, which is the shape a
push has. What is far less certain is whether it is the right push. The most
likely mistakes, reasoning from the gap, are three. It may aim at the wrong
glass, because every glass in the picture is the same colour and nothing in it
says which pair is the tight one, and in a rendered view with no shadows the
cue that would normally say how close two objects are standing is weak. It may
push in a direction that moves the glass out of one crowd and into another,
because the arrangement as a whole is what decides a good direction and
reading an arrangement is the part that needs the picture to be understood.
Or it may push much too far or much too little, because the distance a push
should cover is a property of this table's clearances and nothing in the
model's pretraining knows them.

**Then the arm looks again**, and this is where the loop earns its keep. The
fresh measurements say where the glasses really are, the refused glass is still
refused, and the model is asked once more from the new arrangement. A wrong push
is therefore not fatal, only wasteful, and what it costs is one entry against
the push budget. Repeated often enough, that is the signature this solution
would most likely leave on the scorecard: a run that spends many pushes, moves
the glasses a long way in total compared with the displacement floor, and
clears fewer tables than the solutions that were fitted here.

The instructive part is what the run would *not* contain. There would be no
crash, no fault, no refusal the model generated, and no number anywhere in the
output marked as doubtful. Every push would look like a push. That is the
characteristic failure across a domain gap, and it is why this solution's result
has to be read against solution 6's rather than on its own.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
