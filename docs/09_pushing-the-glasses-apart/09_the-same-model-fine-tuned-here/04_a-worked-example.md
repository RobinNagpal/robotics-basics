# The same foundation model, fine-tuned here — a worked example

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
answer is short, because the answer does not come from the model.

A glass slides while the jaw's contact height is below half its foot width
divided by the friction coefficient, and tips above it. The height that counts
is the **top edge of the jaw**, which stands at 65 mm: the middle of the jaw
rides as low as the gripper goes, at 50 mm, and the finger is 30 mm tall, so
its top edge is half of that, 15 mm, higher again. For a glass whose foot is
narrow enough, the limit falls below 65 mm, and there is then no contact height
the arm can offer that is below it. Such a glass tips before it slides whatever
the arm does, and **the only correct answer for it is to refuse**, with the
reason recorded. A refusal is a result, and a run that refuses the glasses it
should refuse is marked *correct but incomplete*, which is a good outcome.

**That check is not this solution's and cannot be made this solution's.** It
belongs to [pushing without toppling](../01_the-problem/03_pushing-without-toppling.md), where it
is explained once for all six, and it runs on every glass before the jaw moves.
In code it is `slides` in `01-one-fixed-nudge/plan.py`, which is worth saying
because that is not where a thing shared by six solutions would naturally sit.
There is no shared module for it: solutions 2, 3, 5 and this one all reach into
solution 1's folder for the same arithmetic rather than each writing it out, so
those five do refuse the same glasses, but by borrowing rather than by sharing.
[Solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) is the one that does not apply it, and says
so.
The reasons it has to sit outside the policy are worth repeating in
one place, because they are easy to lose in the middle of a document about
training. A policy has no field in it for a rule, so it cannot be told. Its
training set contained no refusals, because the teacher refused those glasses
and the recordings that remain are of pushes that happened, so it has never
seen the case. And the cost of being wrong is not symmetric: a glass left
standing with a reason can be revisited by anything later in the project, while
a glass that went over is finished, because nothing in this project can stand a
glass back up.

So this solution's honest position is that it proposes and the shared geometry
disposes. **This is the one place where this solution and its untrained partner
are guaranteed to behave the same**, because the thing that decides the outcome
is the same code in both, reading the same readings, applying the same
arithmetic. Any difference in the refusal counts between the two comes from
their pushes having left the glasses in different places, not from either of
them being better at refusing.

Two qualifications keep that from sounding safer than it is. The check needs
the friction coefficient, nobody has it, and the limit it computes is only as
good as the guess. And the guard against a guess that was too generous — the
early abort that reads the jaw's force while the push is happening and stops it
when the contact stops behaving like a slide — **is a design and not code**.
The bench stops a push at a jam, which is far more force than a glass needs to
begin tipping, and nothing reads the force as it develops. So the only thing
protecting a glass in either half of this pair is the limit computed before the
jaw moves, and a 5 mm test push where that limit is undecided.

## 2. A worked example

Follow one table through, because the difference from solution 5 is easier to
recognise once both have been run over the same one.

**The table.** Five tapered glasses stand in the glass zone, drawn at
proportions from across the kind's range, so they are not all the same height.
Two of them stand as close together as the bench allows, so neither has its
70 mm of clear room measured to the other's edge, and because the test is to
the edge rather than to the middle, the narrower of the two is crowded while
the wider one may not be. A third glass, standing alone, is drawn with a foot
narrow enough that its limit falls below the jaw's top edge. The bench renders
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

← [The same foundation model, fine-tuned here — the code](03_the-code.md) · [The same foundation model, fine-tuned here — what it needs](05_what-it-needs.md) →
