# The code

This page shows the main code of this solution. It also says what the solution
hands back to the rest of the cell. It follows [what it is](01_what-it-is.md).
[How it works](03_how-it-works.md) then explains each part of this code.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

It helps to read the code before the explanation. Two pieces of this solution
are written and running in the repository. The first decides whether a glass
can be pushed at all. It answers "yes", "no" or "try". The second is the short
test push the method makes when the answer is "try". [Solution
2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) and three others
reuse the first piece. The second piece is the only place where the arm checks
the world before it decides, not after.

The tipping test comes from
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py).
No library decides anything in it. It is three divisions, three comparisons and
two arctangents from Python's own `math`. The rule behind it is set out in
[pushing without toppling](../01_the-problem/05_pushing-without-toppling.md#3-the-limit-slide-or-tip).

The function runs in three steps, and each step is marked in the code.

1. Take half the width of the glass's foot. Divide it by the highest friction
   in the range. This gives the lowest push height that could tip the glass. If
   the jaw is below it, the answer is "yes". Then divide by the lowest
   friction. This gives the highest such height. If the jaw is at or above it,
   the answer is "no".
2. Between those two heights, the unknown friction decides. So measure how far
   this glass can lean before it falls. This depends on its foot and the height
   of its centre of mass.
3. Compare the lean the short test push could cause with that angle. Answer
   "try" only if the lean stays well inside it.

```python
# Glass on a dry wooden top is somewhere in here. Nothing in the cell measures
# it, so the tipping check is made at both ends.
MU_LOWEST = 0.2
MU_HIGHEST = 0.5
...
def slides(glass: Seen) -> str:
    """Whether a push at the jaw's top edge slides this glass: "yes", "no" or "try".

    It slides while the push is lower than a / mu: half the foot, over the
    friction. The top edge, because a glass wider higher up meets the jaw
    there first. "try" means it depends on the friction, and a probe is safe.
    """
    # Step 1: take half the width of the foot the glass stands on -- how far the foot's edge
    # is from the middle, which is what keeps the glass from going over
    half_foot = glass.foot / 2
    # Step 1: divide it by the grippiest friction in the range, which gives the lowest push
    # height that tips this glass; a jaw under that slides it at every friction in the range
    if half_foot / MU_HIGHEST > JAW_TOP:
        return "yes"
    # Step 1: divide it by the slipperiest friction, which gives the highest such height; a
    # jaw at or above that one tips the glass at every friction in the range, so refuse it
    if half_foot / MU_LOWEST <= JAW_TOP:
        return "no"
    # Step 2: between the two widths the friction decides it, so measure how far this glass
    # can lean before it falls: half its foot against the height of its centre of mass
    falls_past = math.atan2(half_foot, CENTRE_OF_MASS_SHARE * glass.height)
    # Step 3: allow the short test push only while the lean it could cause stays well inside
    # that angle, so a glass tall enough to be leaned most of the way over is refused instead
    return "try" if math.atan2(PROBE, JAW_TOP) < PROBE_LEAN_SHARE * falls_past else "no"
```

Step 1 is a question about the foot. The picture below marks the two foot
widths it compares against. Between those two widths, the arithmetic cannot
decide.

![The foot a glass stands on, with the two widths the arithmetic compares against marked on it: below 43 mm a glass tips at every friction in the range and is refused, above 107 mm it slides at every friction and is pushed, and between the two the answer depends on a number nobody has. The ranges the four kinds of glass are drawn from show that neither the tapered kind nor the short stemmed one ever reaches the right-hand zone.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-three-answers.png)

Steps 2 and 3 handle that middle zone. Some glasses are so tall that even the
short test push could lean them most of the way over. Those glasses are refused
instead of tried.

A glass that gets "try" gets the short test push. This is `probe` in the same
file. It takes the chosen push, cuts it to one short length, and keeps the same
line. The arm looks before and after. The
[test push](../01_the-problem/05_pushing-without-toppling.md#5-the-loop-plan-feel-look-again)
is part of the shared rules. `probe` runs in three steps.

1. Turn the push's direction into a unit vector, which is what NumPy is for
   here.
2. Step back from the aim by the whole push length. This gives the glass's
   middle. Aim five millimetres past that middle instead.
3. Return the same push with the short length and the new aim. Keep the start
   point, the direction and the feeling distance.

The two-line `needs_probe` below it decides when a test push is needed.

```python
# A glass that slides only at the low end is tried with a push this long, and
# looked at before and after. Short pushes lose up to 2.5 mm to the contact
# taking up and the glass settling onto its far edge, so this is well over that.
PROBE = 0.005
...
def probe(push: Push) -> Push:
    """The same push, cut down to PROBE."""
    # Step 1: turn the heading into a unit vector, so distances can be stepped along the push
    u = np.array([math.cos(push.heading), math.sin(push.heading)])
    # Step 2: step back from the aim by the whole travel, which lands on the glass's middle
    middle = np.array(push.aim) - push.travel * u
    # Step 2: aim PROBE past that middle instead, so the jaw carries the glass 5 mm and stops
    aim = middle + PROBE * u
    # Step 3: hand back the same push with the short travel and the near aim; where the
    # fingertips come down, the heading and the feeling forward are all unchanged
    return Push(push.glass, push.start, push.heading, push.reach, PROBE, (float(aim[0]), float(aim[1])))

def needs_probe(glass: Seen, proven: set[int]) -> bool:
    # Step 1: ask for the test push only while the arithmetic says "try" and this glass has
    # not already slid under one -- a glass that slid once is pushed for real after that
    return slides(glass) == "try" and glass.id not in proven
```

Together, the two blocks show the whole idea of this solution. Where the
arithmetic can answer, it answers. Where it cannot, because the friction is
unknown, the method makes one short push to find out. It does not guess.

Note which fixed nudge this is. The share-of-the-gap nudge in
[the main idea](01_what-it-is.md#4-the-main-idea) has no constant in the
repository. `PROBE` does. So the fixed length above is the one this code really
uses.

The next section says what this code hands to the rest of the cell.

## 2. The pushes are what this contributes

The last section showed how the method decides. This section shows what it
hands over. The method thinks in whole pushes. So it hands over a
**parameterised push**. That is a small set of numbers. They say which glass to
move and where the fingertips come down. They say which way the jaw points, how
far to feel forward and how far to push. And they say where the glass should
end up. The examiner's own code turns
those numbers into jaw movements, the same way for every solution.
[What must come out](../01_the-problem/02_what-goes-in-and-what-comes-out.md#6-what-must-come-out)
explains this.

![One push drawn on the table: where the fingertips come down, 10 mm outside the glass's widest part; the heading the jaw points and travels along; how far forward to feel, which is 30 mm past the glass's middle; how far to push; and where the glass is expected to arrive.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-parameters.png)

One field says where the glass should end up. That looks like a prediction, but
it is not. The examiner asks for it so it can measure how far each glass ended
from its aim. This solution fills it with the place the fingertips stop. It
assumes the glass moves with the jaw and no further. It never uses this number
again. It just looks again.

The jaw does not drive to a computed point on the glass. It comes down behind
the glass, a little outside its widest part. Then it moves forward slowly until
it feels a small force. A movement that stops when a sensor fires is called a
**guarded move**. It is needed because the glass's position and width each have
some error. A jaw driven to a computed point could stop short, or hit the glass
too fast.

After the push, the jaw reports what it felt, including the force. **This
solution uses almost none of that report.** It only checks whether the jaw
touched anything. This is the main reason it is the weakest of the six.
[Where it is strong and where it breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains why.

Pushing is not the whole run. Before any push, the runner racks every glass
that already has room. That step is shared by all six solutions. This page only
describes what happens to the glasses that are left.

The next section puts all these parts in the order the arm meets them.

## 3. How the concepts fit together

The last two sections showed the parts one at a time. This section puts them in
the order the arm uses them. The room test finds the glasses that cannot be
gripped. The shortfall gives each of them one number, which is the error. The
neighbour that causes the shortfall gives the direction. The gain turns the
error into a distance. The tipping rule decides if the glass may be touched.
The guarded move finds the glass without hitting it. A fresh `look()` then
replaces everything the last pass assumed.

As a loop, it is:

1. Look at the table.
2. Rack every glass that already has room. This step is shared.
3. For each glass that is left, compute its shortfall against every
   neighbour's edge, and keep the worst.
4. Take the glass with the largest shortfall, and the neighbour that caused it.
5. Check that glass against the tipping rule. If it fails, refuse it with the
   reason, and go back to step 3 without that glass.
6. Push it away from that neighbour, by a fixed share of the shortfall, at the
   lowest height the gripper reaches. Feel forward for the glass instead of
   driving to it.
7. Go back to step 1.

The loop ends when no glass is short of room, when the push budget is used up,
or when every glass left has been refused. [How it works](03_how-it-works.md)
explains each of these steps in turn.

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
