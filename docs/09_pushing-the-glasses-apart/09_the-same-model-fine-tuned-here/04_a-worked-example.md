# A worked example

This page follows this solution through one arrangement of glasses with real
numbers, and then through the case this book keeps returning to, a glass that
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
narrow enough that its limit falls below the jaw's top edge. The examiner
renders the view from the top and hands over the readings, each carrying the
error that telling the glasses apart in a picture leaves in it.

**What solution 5 does.** The downloaded model is shown a rendered view of a
kind it has never seen — pale blue glasses, opaque, shaded, standing on a tan
table — together with an instruction, and it returns a chunk of waypoints on
the scale of robots that are not this one, read through the convention the pair
agreed in advance. What comes out is a smooth, well-formed jaw motion whose
relationship to these five glasses is genuinely in doubt. Measured over the
held-out tables, that motion stays a median of 209 mm above the table and runs
844 mm across it, which is clear of every glass but the tallest, so nearly nine
pushes in ten touch nothing at all. Nothing in the output looks wrong, which is
the characteristic failure of a model used across a domain gap.

**What this solution does.** The corrected model is shown a view of a kind
every example in its training set looked like, and returns a chunk in this
cell's own units. It brings the jaw down to 50 mm, the height the gripper
pushes at, which is what its teacher's pushes did and what solution 5 never
does. Then the chunk's first waypoint decides everything, and this is where the
measurement is harsher than the expectation.

The examiner carries out a chunk by placing the jaw clear above where the chunk
starts and lowering it to the first waypoint. If that first waypoint stands
behind the crowded glass, on the line leading away from its neighbour, the jaw
reaches push height in open table and the rest of the chunk is a push. If it
stands over a glass, the jaw meets the glass coming down, `follow()` reports
the chunk **blocked on the way down**, and the jaw goes straight back up
without pushing anything — or the glass goes over. The model learned the height
and did not learn the place: about three of its pushes in five end that way.

![One glass seen from the side with the jaw coming down to its first waypoint from two places: behind the glass, where the jaw reaches 50 mm in open table and the rest of the chunk pushes, and over the glass, where the jaw meets the rim on the way down and the chunk is abandoned without a push.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-where-the-jaw-comes-down.png)

**Where this solution is only as good as its teacher.** Which of the crowded
pair to move is a choice solution 2's ranker makes, and on a pair like this one
it is close to arbitrary, because moving either one would give both their room.
The policy inherits whatever the ranker tended to do, averaged over many
tables. It does not improve on the choice, because nothing scored the choice.

**Where the look-again loop does the work in both.** A glass that was pushed
does not land where it was aimed, because the friction guess was wrong and a
glass rotates as well as slides. The arm looks again and sees where it really
is. Here the two halves of the pair diverge in a way the scorecard can see: the
fine-tuned policy has been fitted on recordings taken at every point in the
teacher's own loop, including after a glass landed short, so the situation is
one it has seen. The downloaded model is in the same position it was in before
and has learned nothing from the attempt. Neither improves its own model of
pushing during the run, because neither is being trained at run time. What
differs is whether the model had ever seen this situation at all.

**And the case neither can answer.** The third glass, with the narrow foot,
cannot be pushed safely. The shared check computes the limit from the glass's
measured foot width and the jaw's top edge, finds it below 65 mm, and refuses
that glass with that reason before either model is asked anything. The glass is
left standing and the table is marked *correct but incomplete*. The refusal, its
reason and its correctness belong entirely to the shared geometry.

**But the refused glass stays in the picture, and that is the part the code had
to settle.** Neither model can be told to leave it alone — there is no field in
a policy for a rule — so a chunk whose path runs into a refused glass is simply
not carried out, and the loop asks again. That check reads the path, which the
geometry can only do once the model has answered, so a rejected chunk is a
forward pass spent for nothing. It is **not** charged to the push budget,
though, because the budget is what makes the six solutions' push counts
comparable and a rejected chunk never touches the table. What guards against a
model that keeps aiming at a glass it may not touch is a separate cap on
answers per table, set at three times the push budget, which is slack rather
than a limit. In practice none of this bound: the counts in each folder's
`asking.json` say it fired once in this solution's 1,248 answers and not at all
in solution 5's 2,260.

The honest summary of the example is that fine-tuning changes the first half of
it and not the second. The chunk becomes a motion at the height a push happens
at, in units this cell can carry out, informed by what pushes on this table
actually did — and still aimed badly enough that it more often comes down on a
glass than behind one. The refusal, the topple limit, the destinations and the
loop are exactly where they were, because they were never the model's to begin
with.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
