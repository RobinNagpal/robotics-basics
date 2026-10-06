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
in the rest are bounded into the range the jaw rides at. Both checks are built
— and they sit in this solution's own folder rather than in the examiner, which
is where a thing five solutions need would belong.

## 2. A worked example

Following one crowded table through makes the expectations above easier to
recognise, because they appear together rather than one at a time.

Five glasses of the tapered kind stand in the glass zone. Two of them are
standing deliberately close together, closer than the gripper can work with but
not touching, which is how [the examiner](../02_the-examiner.md) builds its tables.
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
