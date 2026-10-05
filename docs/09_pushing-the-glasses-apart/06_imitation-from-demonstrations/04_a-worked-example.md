# Imitation from demonstrations — a worked example

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

Every solution document in this chapter answers this question. This one's
answer is that **the refusal does not and cannot live inside the policy**, and
the reasoning is worth following because it is a good illustration of what a
cloned policy is unable to express.

The limit itself is shared and is set out in full in [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md). A pushed glass slides while the
contact height is below half its foot width divided by the friction
coefficient, and tips above it. The height that counts is the **top edge of the
jaw**, which stands at 65 mm, rather than the 50 mm the jaw's middle rides at,
because a glass that is wider higher up meets the top edge first. Those are the
gripper's own numbers. The foot width comes from `look()`. The friction does
not come from anywhere, because nothing in this cell measures it. For a glass
whose foot is narrow enough that the limit falls below the jaw's top edge at any
plausible friction, there is no contact height the arm can offer, and the only
correct answer is to refuse.

**A policy of this kind has no way to say that.** Its output is a chunk of
waypoints. There is no channel in it for "I cannot move this glass, and the
reason is that it tips before it slides". The bench requires a refusal to carry
a reason — a glass abandoned in silence is marked **wrong**, while a glass
refused with a reason is **correct but incomplete**, which is a good outcome —
so the thing the bench wants is a kind of answer this policy cannot produce.

It is tempting to hope the policy learns to refuse by itself, and it is worth
being exact about why it does not. The teacher refuses those glasses, so the
dataset contains no push on them. But **the absence of an example is not a
label.** The network was never shown a situation of that kind paired with an
instruction to do nothing; it was shown nothing at all. Asked about such a
table, it will return a chunk of waypoints, because returning a chunk of
waypoints is the only thing it does, and that chunk will be an extrapolation
with nothing behind it. The one case where the arm must not act is therefore the
case where the policy is least anchored and least able to warn.

So the limit sits **in front of** the policy, as shared arithmetic, exactly as
it does for the other five. The foot width is measured, the limit is evaluated
at the jaw's top edge, and a glass that fails never reaches the policy at all.
If every glass left on a table fails, the run ends *correct but incomplete*,
with each remaining glass reported with its reason. The policy is not consulted
and cannot be blamed, which is the right arrangement for a decision whose wrong
answer cannot be recovered.

Two further points are specific to this solution.

**The gate makes the comparison cleaner, not dirtier.** Because the same
arithmetic refuses the same glasses for all six, no solution can score well by
refusing more or badly by refusing less. What is left to compare is the pushes
on the glasses everybody agreed were pushable.

**The early abort matters more here than elsewhere.** [Pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) describes a monitor that reads the
jaw's force signal during a push and stops the arm the moment the contact stops
behaving like a slide, and notes that it is the only thing in this problem that
can prevent a topple rather than report one. A chunking policy is open-loop
while its chunk runs, so during that window such a monitor would be the only
thing observing at all. **It is still a prescription rather than built code,
and this solution is the one with the strongest reason to want it.** What the
bench does have during a chunk is the jam threshold, which stops a chunk whose
jaw has wedged. That catches a blocked path; it does not recognise a glass
beginning to tip, which is the failure the monitor was for.

## 2. A worked example

Follow one table through, because the places where this solution differs from
its teacher are easier to recognise on a concrete arrangement than in the
abstract.

**The table.** Five straight glasses stand in the glass zone, drawn at
proportions from across that kind's range, so they are not all the same size.
Two of them stand deliberately close — closer than the gripper can work with,
with a little daylight still between them — and one of that pair is also fairly
near the edge of the glass zone. The other three have room. The bench accepted
the table because at least one glass on it has no room, so there is work to do.

**What happened offline.** Long before this table was drawn, the teacher was
run over many tables below the dividing line. On each, it generated legal
candidate pushes, ranked them, pushed, and the bench recorded the picture, the
waypoints and the verdict. The failures were dropped and counted. What was left
was fitted into ACT, several times with different seeds. None of that involves
this table, which comes from above the dividing line.

**The first push.** The arm takes the view from the top and the policy returns
one chunk: a descent behind the outer glass of the crowded pair, a slow feel
forward, a committed slide outward along a heading away from its neighbour, a
back-off, and a lift to travel height. Notice what the chunk is free to do that
a parameterised push is not. It can lean the slide as it travels, so the glass
leaves its neighbour at a slightly different angle from the one it started on,
and it can slow as it approaches the end rather than stopping at speed. Whether
either of those is worth anything is a thing to measure rather than to assert.
The freedom is real, it belongs to the trajectory solutions only, and this is
the kind of place it would show up.

**What the push actually does.** The glass goes further than the teacher's aim
would have put it, because the friction under this glass's foot is not what any
of the demonstrations happened to sit at, and no part of this method models
friction. Nothing is lost by that: the arm looks again, and the fresh reading
says where the glass really is.

**And here is compounding error, in one concrete form.** The table the policy
now faces has a glass closer to the edge of the glass zone than the teacher
would ever have left one, because the teacher aimed at a destination the layout
computed and this push overshot it. If the demonstration set happened to hold
tables with a glass in roughly that position, the policy is on familiar ground
and the second push is as good as the first. If it did not — and the filtering
makes that more likely, because overshoots near the zone edge are exactly the
pushes that failed and were dropped — then the policy is being asked about a
table outside its data. It will answer. The answer will arrive as a chunk of
waypoints like any other, with nothing to distinguish it from a confident one.
This is the failure to watch for in this solution, and the DAgger repair is
aimed precisely at it: ask the teacher what it would have done on this table,
and the gap closes.

**Where the averaging problem would show.** Change the table slightly so that
the crowded pair sits symmetrically, with as much free table to the left of the
left glass as to the right of the right glass. Pushing the left glass left and
pushing the right glass right are equally good, and [the target
layout](../01_the-problem/02_the-target-layout.md) says plainly that both are legal answers. The
demonstration set will hold both kinds of example, taken from arrangements that
look much alike. ACT must name one chunk, and the chunk that is least wrong on
average over those examples is something between them: a short, hesitant motion
that separates nothing. The bench would score that as a push spent with the
table unchanged, and a solution that repeats it would burn its push budget
without failing in any way the counts call wrong. **This is the case the
Diffusion Policy rung exists to test**, because a model that draws its chunk
can commit to one side.

**And the refusal.** Take a different table, of stemmed glasses this time, one
of them drawn with a foot narrow enough that half its width divided by any
plausible friction falls below the jaw's top edge. The shared arithmetic
evaluates that from the measured foot width before the policy is consulted, and
refuses the glass with its reason. The policy never sees it. The other glasses
on the table are pushed as usual, and the run ends *correct but incomplete*,
which is the right result. The important part of this example is the negative
one: nothing the policy could have learned would have improved it, and nothing
the policy might have produced was allowed to make it worse.

**One correction to all of the above, now that it has been run.** Everything in
this example is what the design says the method would do, and it was written
before any of it existed. The refusal behaves exactly as described. The first
push does not. What the fitted policy actually returns on a table it has not
seen is a chunk that starts in roughly the right neighbourhood but points about
thirty degrees away from where the teacher pointed, and the jaw is a quarter of
a metre long behind its fingertips, so on a crowded table it meets a neighbour
while it is still coming down. Almost every push ends there, before any glass
is touched. Nothing in the example about leaning the slide or slowing near the
end was reached, because the motion never got that far. The code folder's
`README.md` has the counts.

← [Imitation from demonstrations — the code](03_the-code.md) · [Imitation from demonstrations — what it needs](05_what-it-needs.md) →
