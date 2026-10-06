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

**This is the one place where this solution and its untrained partner are
guaranteed to behave the same**, because the thing that decides the outcome is
the same code in both, reading the same readings and applying the same
arithmetic. Any difference in their refusal counts comes from their pushes
having left the glasses in different places, not from either being better at
refusing.

Three reasons the check has to sit outside the policy are worth keeping
together, because they are easy to lose in a document about training. A policy
has no field in it for a rule, so it cannot be told. Its training set contained
no refusals, because the teacher refused those glasses and what remains are
recordings of pushes that happened. And the cost of being wrong is not
symmetric: a glass left standing with a reason can be revisited by anything
later, while a glass that went over is finished.

Two qualifications keep that from sounding safer than it is. The check needs
the friction, nobody has it, and the limit is only as good as the guess. And
the guard against a guess that was too generous — the early abort that reads
the jaw's force as the push happens — **is a design and not code**. So the only
thing protecting a glass in either half of this pair is the limit computed
before the jaw moves.

## 2. A worked example

Follow one table through, because the difference from solution 5 is easier to
recognise once both have been run over the same one.

**The table.** Five tapered glasses stand in the glass zone, drawn at
proportions from across the kind's range, so they are not all the same height.
Two of them stand as close together as the examiner allows, so neither has its
70 mm of clear room measured to the other's edge, and because the test is to
the edge rather than to the middle, the narrower of the two is crowded while
the wider one may not be. A third glass, standing alone, is drawn with a foot
narrow enough that its limit falls below the jaw's top edge. The examiner renders
the view from the top and hands over the readings, each carrying the error that
telling the glasses apart in a picture leaves in it.

**What solution 5 would do.** The downloaded model is shown a rendered view of
a kind it has never seen — pale blue glasses, opaque, shaded, standing on a
tan table — together with an instruction, and it returns
a chunk of waypoints on the scale of robots that are not this one, read
through the convention the pair agreed in advance. What comes out is a smooth,
well-formed jaw motion whose relationship to these five glasses is genuinely in
doubt — it may come down in open table, or behind the wrong glass, or behind
the right glass pointing the wrong way. Nothing in the output looks wrong,
which is the characteristic failure of a model used across a domain gap.

**What this solution would do.** The corrected model is shown a view of a kind
every example in its training set looked like, and returns a chunk in this
cell's own units. The expected shape of that chunk is the shape its teacher's
pushes had: the closed jaw travels to a point behind the crowded glass, on the
line leading away from its neighbour, comes down to the lowest height the
gripper reaches, feels forward until it touches, and pushes. That is what
solution 2 does, and this solution was fitted on recordings of it doing so.

**Where this solution is only as good as its teacher.** Which of the crowded
pair to move is a choice solution 2's ranker makes, and on a pair like this one
it is close to arbitrary, because moving either one would give both their room.
The policy inherits whatever the ranker tended to do, averaged over many
tables. It does not improve on the choice, because nothing scored the choice;
it only makes it more consistently than a ranker whose answer flips on a
millimetre of measurement error.

**Where the look-again loop does the work in both.** The pushed glass does not
land where it was aimed, because the friction guess was wrong and a glass
rotates as well as slides. The arm looks again and sees where the glass really
is. Here the two halves of the pair diverge in a way the scorecard can see: the
fine-tuned policy has been fitted on many recordings in which a glass landed
short, so its next chunk is of the kind that followed a short landing in
training, while the downloaded model is in the same position it was in before
and has learned nothing from the attempt. Neither of them improves its own
model of pushing during the run, because neither is being trained at run time.
What differs is whether the model had ever seen this situation at all.

**And the case neither can answer.** The third glass, with the narrow foot,
cannot be pushed safely. The shared check computes the limit from the glass's
measured foot width and the jaw's top edge, finds it below 65 mm, and refuses
that glass with that reason before either model is asked anything. The glass is
left standing and the table is marked *correct but incomplete*. The refusal,
its reason and its correctness belong entirely to the shared geometry.

**But the refused glass stays in the picture, and that is the part the code
had to settle.** Neither model can be told to leave it alone — there is no
field in a policy for a rule — so a chunk whose path runs into a refused glass
is simply not carried out. That check reads the path, which is something the
geometry can only do once the model has answered, so it costs one of the
table's pushes every time it fires: an answer was asked for and spent, and the
model cannot be asked for a different one. Both halves of the pair pay that in
the same code, which is why it does not disturb the comparison, and the counts
in each folder's `asking.json` say how often it happened.

The honest summary of the example is that fine-tuning changes the first half of
it and not the second. The chunk becomes a push aimed at a glass on this table,
in units this cell can carry out, informed by what pushes on this table
actually did. The refusal, the topple limit, the destinations and the loop are
exactly where they were, because they were never the model's to begin with.

← [The code](03_the-code.md) · [What it needs](05_what-it-needs.md) →
