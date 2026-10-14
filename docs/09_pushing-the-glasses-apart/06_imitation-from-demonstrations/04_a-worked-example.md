# A worked example

This page follows this solution through one table with real numbers. First it
covers the case this book keeps coming back to: a glass that cannot be pushed
safely. A worked example that shows only the easy case would teach the wrong
lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

The hard case comes first, because it shows what a cloned policy cannot say. A
glass slides when the jaw touches it low enough, and tips when the jaw is too
high. [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) sets out that rule
once. This section covers only what is special to this solution.

**This policy has no way to refuse.** Its only output is a chunk of waypoints.
It has no way to say "I cannot move this glass, because it would tip". But the
examiner wants every refusal to come with a reason. So the answer the examiner
needs is one this policy cannot give.

The policy does not learn to refuse by itself either. The teacher refuses those
glasses, so the data holds no push on them. But **a missing example is not a
label.** The network was never shown such a glass with the label "do nothing".
It was shown nothing at all. When asked about such a glass, it returns a chunk,
because that is all it can do. So the one case where the arm must not act is
the case where the policy knows least.

So the refusal is made in front of the policy. It uses the same arithmetic as
the two solutions before this one. The policy is never asked about a glass that
fails it. The push budget, and the limit on pushes per glass, also act in front
of the policy.

![One pass of the run-time loop, with the two routes that take a glass out of play reaching the refusal without passing through the policy at all.](../../images/pushing-the-glasses-apart/imitation-from-demonstrations/imitation-where-a-refusal-comes-from.png)

There is one more cost of the same limit. Sometimes the friction range leaves
the answer undecided. The teacher then makes a 5 mm test push and looks before
and after. This solution makes no test push, because a chunk cannot ask a
question. So the gate refuses only the glasses that tip even at the lowest
friction allowed. An undecided glass goes to the policy as it is.

No force monitor watches a chunk while it runs. [Action
chunking](03_how-it-works.md#4-action-chunking-and-why-it-matters) explains why
this solution needs one most.

The next section follows one whole table, where the refusal is only one part.

## 2. A worked example

The refusal above is one case, and this section follows a whole table. The
places where this solution differs from its teacher are easier to see on a real
table. This example was written before the policy was trained, so it shows what
the design expected. The end of the section says what really happened.

**The table.** Five straight glasses stand in the glass zone, in a range of
sizes. Two of them stand too close for the gripper, with a small gap still
between them. One of that pair is also near the edge of the zone. The other
three have room.

**What happened offline.** Before this table was drawn, the teacher ran over
many training tables. The failures were dropped and counted. ACT was trained on
the rest, several times with different seeds. None of that used this table,
which is a test table.

**The first push, as designed.** The policy returns one chunk. The jaw comes
down behind the outer glass of the close pair and feels forward slowly. It
slides the glass away from its neighbour. Then it backs off and lifts. A chunk can do things a
normal push cannot. For example, it can curve the slide, or slow down near the
end. Whether that helps is something to measure.

**What the push does, as designed.** The glass goes further than the teacher
aimed, because the friction under it differs from the examples. Nothing in this
method models friction. Nothing is lost, because the arm looks again and sees
where the glass really is.

**Compounding error, as designed.** The table now has a glass closer to the zone
edge than the teacher would ever leave one. If the examples held tables like
this, the next push is as good as the first. If not, the policy is outside its
data. It will still answer, with the same confidence as before. [Compounding
error](03_how-it-works.md#6-compounding-error) explains this failure and the
DAgger fix.

**The refusal.** Take a different table, of stemmed glasses. One has a foot so
narrow that it would tip at any likely friction. The shared arithmetic checks
this from the measured foot width before the policy is asked. It refuses the
glass with its reason. The policy never sees it. The other glasses are pushed as
usual, and the table ends *correct but incomplete*. That is the right result.
Nothing the policy learned could improve it, and nothing it produced could make
it worse.

**What really happened.** The refusal works as described. The first push does
not. The trained policy starts its chunk in about the right place, within a
centimetre or two of the teacher's fingertips. But it points about 25 degrees
away from the teacher. Across the three seeds, this error is 22 to 27 degrees on
tables the policy never saw. On tables it was trained on, it is under 4 degrees.

This matters because the hand is long. It reaches 266 mm back behind its
fingertips. Turning it 25 degrees about the fingertips swings the far end of the
wrist 135 mm sideways. On a crowded table, that puts the 90 mm body over a glass
that the teacher's heading cleared.

![The same fingertip at the teacher's heading and at twenty-five degrees off it, with a third glass twenty millimetres clear of the jaw's body in the first and underneath it in the second.](../../images/pushing-the-glasses-apart/imitation-from-demonstrations/imitation-the-heading-error.png)

The examiner brings the jaw down to the first waypoint, and stops if it touches
anything. So most pushes end there, before any glass is touched. The curved
slide and the slow finish were never reached. The code folder's `README.md` has
the counts.

The next page lists what this solution needs in order to run.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
