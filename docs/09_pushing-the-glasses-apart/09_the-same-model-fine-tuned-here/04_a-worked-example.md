# A worked example

This page follows this solution through one table of glasses. It also covers
the case this book keeps coming back to: a glass that cannot be pushed safely.
An example that shows only the easy case would teach the wrong lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

The unsafe glass comes first, because the rule for it is the same in both
halves of the pair. [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md#3-the-limit-slide-or-tip)
sets that rule out once. It explains which glasses are refused and why the
check sits outside every policy. This section adds only what belongs to this
solution.

**Here this solution and solution 5 are sure to behave the same.** The same
code decides, from the same readings, with the same arithmetic. So any
difference in their refusal counts comes from where their pushes left the
glasses. Neither one is better at refusing.

Training adds one new fact. The training set holds no refusals, because the
teacher refused those glasses and so never pushed them. The policy has never
been shown a glass it must not push.

The check needs the friction, and nobody has it. So the limit is only as good
as the guess. The [early
abort](../01_the-problem/05_pushing-without-toppling.md#an-early-abort-acting-during-the-push)
that would catch a bad guess is a design, not code. So in both halves of the
pair, the only protection is the limit worked out before the jaw moves.

With the rule for unsafe glasses set, the next section follows one whole table.

## 2. A worked example

The rule above applies to both halves of the pair. Now follow one table
through both, because the difference is easier to see on a single table.

**The table.** Five tapered glasses stand in the glass zone. They have
different heights. Two of them stand as close as the examiner allows. So
neither has its 76 mm of clear room to the other's edge. The test is to the
edge, not to the middle, so the narrower glass is crowded while the wider one
may not be. A third glass stands alone. Its foot is so narrow that its tipping
limit is below the jaw's top edge. The examiner renders the view from the top
and hands over the readings, each with its usual error.

**What solution 5 does.** Its model has never seen a picture like this one. It
returns a smooth chunk of waypoints. But the chunk stays far above the glasses
and runs across the whole table, so it nearly always touches nothing. [Solution
5 gives the measured
figures](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#8-what-was-expected-and-what-happened).

**What this solution does.** Its model has seen many pictures like this one in
training. It returns a chunk in this cell's own units. It brings the jaw down
to 75 mm, the height the gripper pushes at. Solution 5 never does that. Then
the chunk's first waypoint decides everything.

The examiner carries out a chunk in two steps. First it places the jaw high
above where the chunk starts. Then it lowers the jaw to the first waypoint.
Suppose the first waypoint is behind the crowded glass, on the side away from
its neighbour. Then the jaw reaches push height in open table, and the rest of
the chunk is a push. Now suppose the first waypoint is over a glass. Then the
jaw meets the glass on the way down, and `follow()` reports the chunk
**blocked on the way down**. Either the jaw goes straight back up without
pushing, or the glass falls over. The model learned the height but not the
place. [How it
compares](06_how-it-compares.md#3-where-it-sits-among-the-others) shows how
often this happens.

![One glass seen from the side with the jaw coming down to its first waypoint from two places: behind the glass, where the jaw reaches 75 mm in open table and the rest of the chunk pushes, and over the glass, where the jaw meets the rim on the way down and the chunk is abandoned without a push.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-where-the-jaw-comes-down.png)

**Which glass to move comes from the teacher.** Solution 2's ranker chooses
which of the crowded pair to move. On a pair like this, the choice is close to
random, because moving either one frees both. The policy copies what the
ranker tended to do. It cannot improve on that choice, because nothing scored
the choice.

**The look-again loop works in both.** A pushed glass does not stop exactly
where it was aimed. The friction guess was wrong, and a glass turns as well as
slides. So the arm looks again. Here the two halves differ. The trained policy
saw recordings from every point in the teacher's loop, including after a glass
stopped short. So it has seen this situation. Solution 5's model has not.
Neither model learns during the run.

**Neither model can answer the last case.** The third glass, with the narrow
foot, cannot be pushed safely. The shared check works out its limit and finds
it below 107 mm. It refuses that glass, with that reason, before either model
is asked anything. The glass is left standing, and the table is marked
*correct but incomplete*. The refusal belongs entirely to the shared geometry.

**But the refused glass is still in the picture.** Neither model can be told
to leave it alone. So a chunk whose path runs into a refused glass is not
carried out, and the loop asks again. The check needs the path, so it can only
run after the model has answered. A rejected chunk is a wasted answer. It is
**not** counted against the push budget, because it never touches the table.
A separate cap allows three times the push budget in answers per table. The
counts in each folder's `asking.json` show how often that cap was reached. It
ended 5 tables in this solution's 1,515 answers over three runs, and none in
solution 5's 1,855.

So the training changes the first half of the example and not the second. The
chunk now comes down at push height, in units this cell can carry out. But it
still often comes down on a glass instead of behind one. The refusal, the
topple limit, the destinations and the loop stay where they were. They were
never the model's job.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
