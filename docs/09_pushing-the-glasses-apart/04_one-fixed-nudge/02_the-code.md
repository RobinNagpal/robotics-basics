# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md), and [how it works](03_how-it-works.md) explains, part by
part, what the code below is doing. The second explains the first,
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
No library decides anything in it. The whole of it is three divisions, three
comparisons and two arctangents from Python's own `math`, which is the
plainest illustration of what this solution being the control means.

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

Read the first two comparisons as a question about the foot. A glass slides
when the push is lower than half its foot divided by the friction, so the
first comparison asks whether the foot is wide enough for that to hold even at
the grippiest end of the range, and the second asks whether it is so narrow
that the limit is below the jaw's top edge even at the slipperiest end.
Between those two widths the arithmetic has nothing left to say.

![The foot a glass stands on, with the two widths the arithmetic compares against marked on it: below 26 mm a glass tips at every friction in the range and is refused, above 65 mm it slides at every friction and is pushed, and between the two the answer depends on a number nobody has. The ranges the four kinds of glass are drawn from show that neither the tapered kind nor the short stemmed one ever reaches the right-hand zone.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-three-answers.png)

The last line of the function is the one exception to that. A glass tall
enough that even the short test push could lean it most of the way to falling
is refused rather than tried, which is what the two arctangents compare.

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
thing it actually hands over, and the examiner is strict about the shape of that.

**The shared output is a jaw trajectory**, as [the examiner](../02_the-examiner.md)
explains, and a solution that thinks in whole pushes does not have to produce
one itself. This solution thinks in whole pushes. What it emits is a
**parameterised push**: which glass is meant to move, where the fingertips come
down, which way the jaw points and travels, how far forward to feel before
giving up on finding the glass, how far to push once it is touching, and where
the glass is expected to arrive. The examiner owns the macro that turns those
numbers into the descent, the feel, the push, the retreat and the lift, and
every parameterised push from every solution is expanded by that same macro. So
the simplicity of this solution costs it nothing in the comparison and gains it
nothing either.

![One push drawn on the table: where the fingertips come down, 10 mm outside the glass's widest part; the heading the jaw points and travels along; how far forward to feel, which is 30 mm past the glass's middle; how far to push; and where the glass is expected to arrive.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-the-parameters.png)

The field that names where the glass is expected to arrive deserves a word,
because it looks like a prediction and this document has insisted there is
none. The examiner asks for it so that it can measure how far each glass ended
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
threshold. A motion commanded with a sensor condition that stops it early is
called a **guarded move**, and it is used here because the glass's wall sits at
its measured middle minus half its measured width, so the error in the position
and the error in the width add together. A step that drove to that computed
point would either stop short and push nothing or arrive past the wall at
speed, which is a knock.

The push then reports what the jaw felt: whether it was blocked on the way
down, how far it travelled before touching or that it never touched, whether it
jammed, the most force it felt, and how far it moved after touching. **This
solution reads almost none of that report.** It uses only whether the jaw
touched anything at all. That is a deliberate omission rather than an
oversight, and it is the deepest reason this solution is the floor of the set:
[the examiner](../02_the-examiner.md) points out that the force reading is the only
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
order in which each one depends only on what came before. The room test turns
a table into a list of glasses that cannot be gripped. The shortfall turns
each of those glasses into a single number, which is the error a closed loop
needs. The blocking neighbour is whichever glass produced that number, and the
line from its middle through the crowded glass's middle is the direction. The
gain turns the error into a distance. The tipping rule decides whether the
glass may be touched at all. The guarded move finds it without striking it.
And the loop closes the whole thing, because a fresh `look()` replaces every
assumption the previous pass made.

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

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
