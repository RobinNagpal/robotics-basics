# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

Two pieces of this solution are written and running in the repository, and they
belong together, so they are worth reading before the prose explains them. The
first decides whether a glass can be pushed at all: a few lines of arithmetic
on the glass's own foot and height that answer "yes", "no" or "not without
trying it". The second is the one small fixed push the method makes when the
answer is the third of those. They are the heart of this solution because the
arithmetic is the piece [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) and three of the
others borrow rather than write again, and because the small push is the only
place in the whole method where the arm reads the world before committing to a
decision rather than after it.

The tipping test, from
[`src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py`](../../../code/src/09_pushing-the-glasses-apart/01-one-fixed-nudge/plan.py).
No library decides anything in it. The whole of it is a few divisions, two
comparisons and two arctangents from Python's own `math`, which is the plainest
illustration of what this solution being the control means.

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
    half_foot = glass.foot / 2
    if half_foot / MU_HIGHEST > JAW_TOP:
        return "yes"
    if half_foot / MU_LOWEST <= JAW_TOP:
        return "no"
    falls_past = math.atan2(half_foot, CENTRE_OF_MASS_SHARE * glass.height)
    return "try" if math.atan2(PROBE, JAW_TOP) < PROBE_LEAN_SHARE * falls_past else "no"
```

A glass that comes back "try" gets the fixed nudge, which is the same file's
`probe`: the chosen push cut down to one constant length, aimed along the same
line, and looked at before and after. NumPy appears here, and only to turn a
heading into a unit vector.

```python
# A glass that slides only at the low end is tried with a push this long, and
# looked at before and after. Short pushes lose up to 2.5 mm to the contact
# taking up and the glass settling onto its far edge, so this is well over that.
PROBE = 0.005
...
def probe(push: Push) -> Push:
    """The same push, cut down to PROBE."""
    u = np.array([math.cos(push.heading), math.sin(push.heading)])
    middle = np.array(push.aim) - push.travel * u
    aim = middle + PROBE * u
    return Push(push.glass, push.start, push.heading, push.reach, PROBE, (float(aim[0]), float(aim[1])))

def needs_probe(glass: Seen, proven: set[int]) -> bool:
    return slides(glass) == "try" and glass.id not in proven
```

Read together, the two blocks show the whole bargain of this solution in a
dozen lines: where the arithmetic can answer, it answers, and where it cannot —
because the friction is missing from it — the method spends one short push to
find out instead of guessing. Note which fixed nudge this is. The proportional
nudge of [the main idea](01_what-it-is.md#3-the-main-idea) has no constant in the repository,
while `PROBE` does, so the fixed length above is the one this code really
commits to.

## 2. The pushes are what this contributes

With the method, its loop and its honest extent all stated, what remains is the
thing it actually hands over, and the bench is strict about the shape of that.

**The shared output is a jaw trajectory**, as [the bench](../02_the-test-bench.md)
explains, and a solution that thinks in whole pushes does not have to produce
one itself. This solution thinks in whole pushes. What it emits is a
**parameterised push**: which glass is meant to move, where the fingertips come
down, which way the jaw points and travels, how far forward to feel before
giving up on finding the glass, how far to push once it is touching, and where
the glass is expected to arrive. The bench owns the macro that turns those
numbers into the descent, the feel, the push, the retreat and the lift, and
every parameterised push from every solution is expanded by that same macro. So
the simplicity of this solution costs it nothing in the comparison and gains it
nothing either.

The field that names where the glass is expected to arrive deserves a word,
because it looks like a prediction and this document has insisted there is
none. The bench asks for it so that it can measure how far each glass ended
from where it was sent, which is a reading on every solution's own model of
pushing. This solution fills it with the place its fingertips are carried to,
on the assumption that the glass travels with the jaw and no further. That is a
statement of intent rather than a prediction of physics, and the method does
nothing with the answer: it does not compare the outcome with the aim, adjust
anything, or remember. It simply looks again.

The approach to the glass is the one part of the push that is not arithmetic,
and it matters more than it looks. The jaw does not drive to a computed contact
point. It comes down behind the glass, a little outside the glass's widest
part, and then feels forward slowly until the force it feels passes a small
threshold. A motion that is commanded with a sensor condition that stops it
early is called a **guarded move**, and it is used here because the glass's
wall sits at its measured middle minus half its measured width, so the error in
the position and the error in the width add together. A step that drove to that
computed point would either stop short and push nothing or arrive past the wall
at speed, which is a knock. Where the sensor fired beats what the camera said.

The push then reports what the jaw felt: whether it was blocked on the way
down, how far it travelled before touching or that it never touched, whether it
jammed, the most force it felt, and how far it moved after touching. **This
solution reads almost none of that report.** It uses only whether the jaw
touched anything at all. That is a deliberate omission rather than an
oversight, and it is the deepest reason this solution is the floor of the set:
[the bench](../02_the-test-bench.md) points out that the force reading is the only
channel through which the friction is observable at all, and every solution
that does better than a blind nudge does so by reading that channel, either by
reasoning about it or by learning from it. This one throws it away and relies on
the next look instead.

Finally, the pushing is what this solution contributes and not the whole run.
The runner racks every glass that already has clear room before it pushes
anything, because a glass in the rack is a glass that is nobody's neighbour,
and that step is shared machinery rather than part of this method. What this
document describes is what happens to the glasses that are left.

## 3. How the concepts fit together

The pieces can now be put in the order the arm meets them, which is also the
order in which each one depends only on what came before.

The **room test** turns a table into a list of glasses that cannot be gripped,
and because it measures to the neighbour's edge it is asymmetric, so it is
applied in both directions for every pair. The **shortfall** turns each of
those glasses into a single number, which is the error a closed loop needs. The
**blocking neighbour** is whichever glass produced that number, and the line
from its middle through the crowded glass's middle is the **direction**, which
is the one claim the method makes that does not need the friction. The **gain**
turns the error into a distance, and it is small so that the sequence of
shortfalls decreases even though the factor relating a commanded push to a
delivered movement is unknown. The **tipping rule** then decides whether this
glass may be touched at all, at the lowest height the gripper can reach, and
refuses it if it may not. The **guarded move** finds the glass without striking
it. And the **loop** closes the whole thing, because a fresh `look()` replaces
every assumption the previous pass made.

Written as the loop it is:

1. Look at the table.
2. Rack every glass that already has clear room, which is shared machinery.
3. For each glass that is left, compute its shortfall against every
   neighbour's edge, and keep the worst.
4. Take the glass with the largest shortfall, and the neighbour that caused it.
5. Check that glass against the tipping rule. If it fails, refuse it with the
   reason and go back to step 3 without that glass.
6. Push it away from that neighbour, a fixed fraction of the shortfall, at the
   lowest height the gripper reaches, feeling forward for the contact rather
   than driving to it.
7. Go back to step 1.

The loop ends when no glass is short of room, when the budget of pushes is
spent, or when every glass that is left has been refused.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
