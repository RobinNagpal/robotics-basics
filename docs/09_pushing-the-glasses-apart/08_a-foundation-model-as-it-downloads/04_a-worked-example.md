# A worked example

This page follows this solution through one table with real numbers. It starts
with the case this book keeps coming back to: a glass that cannot be pushed
safely. A worked example that shows only the easy case would teach the wrong
lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

A borrowed model knows nothing about tipping glasses. So this section shows the
check that runs before the model is asked.

Some glasses tip over before they slide, and the only correct answer for them
is to refuse. [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) explains the rule
in full. All six solutions use the same rule, `slides()`, from solution 1's
`plan.py`. This solution imports it instead of writing its own. So all six
refuse exactly the same glasses.

**It is good that this check is plain arithmetic.** The limit depends on the
glass's foot width, the jaw's height and the friction. A model trained on other
people's robots knows none of these. It cannot learn them from a picture of
plain shapes. Asking it to respect the limit would be asking it to guess. And a
toppled glass is the one mistake this problem cannot undo.

There is a second check. A refused glass is still in the picture, so the model
can still aim at it. **So each answer is checked before it is used.** An answer
that would reach a refused glass is thrown away. The heights in the other
answers are held inside the range the jaw rides at. Both checks are in this
solution's own folder, in `clear.py` and `joining.py`.

The first check was almost never needed. Over three runs the model was asked
1,855 times. Only 5 answers were thrown away for reaching a refused glass. [The
worked example](#2-a-worked-example) below shows why: the answers rarely come
down low enough to reach any glass.

The checks are now clear. The next section follows one real table through
them.

## 2. A worked example

The last section showed the checks that run first. This section follows one of
the examiner's own tables, so the parts can be seen together.

**The table.** It is the second of the 50 held-out tables, made from seed
10001. It holds six tapered glasses. They are 109 to 211 mm tall and 75 to
104 mm across at their widest. Their feet are 35 to 45 mm across. Three of the
six are crowded at the start. This means a neighbour's edge is inside the 76 mm
of room the jaw needs.

**The shared rule runs first, and on this table it decides almost everything.**
It asks `slides()` about each glass. Two of the three crowded glasses have feet
too narrow to slide safely, so the rule refuses them. In all three runs, this
table ended the same way: one push, two glasses racked, four refused, and the
outcome *incomplete*. Solutions 1 and 2 end this table the same way. So on this
table the shared rule decides the result, and the model hardly gets a turn.

**On most tables the model does get a turn, and the result is the same each
time.** The model is given the picture, the fixed sentence and the parked pose.
Most answers pass high above the glasses and touch nothing. [How it
works](03_how-it-works.md#8-what-was-expected-and-what-happened) gives the full
measurements. A push that touches nothing still uses one of the 16 pushes each
table is allowed. The arm looks again, nothing has moved, and the model gives a
similar answer. So most tables run to the end of their budget.

The few pushes that do touch a glass mostly jam, because the jaw arrives too
fast. That is where this solution's toppled glasses come from. The median run
toppled 12 glasses, and the three runs toppled between 10 and 14.

Such a table ends with its free glasses racked, its crowded ones refused, and
the outcome *incomplete*. [How it
compares](06_how-it-compares.md#3-where-it-sits-among-the-other-five) shows
that the glasses racked are only the ones that already had room.

The lesson is in what did **not** happen. This page expected a well-formed push
aimed at the wrong glass, which nothing would notice. Instead the examiner
counts every push that touched nothing. That is far easier to diagnose than a
push that looks right and is wrong. [The domain
gap](03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
is still the cause. Only the guess about how it would show was wrong.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
