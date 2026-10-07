# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

Everything the method requires is either already produced by [the camera work
that measures the
glasses](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md) or
is a constant that belongs to the gripper, which is why it can be built first.

**The measurements, and nothing beyond them.** From `look()` it uses each
glass's position and widest width, which are what the room test and the
shortfall need, and each glass's foot width and height, which are what the
tipping rule and its test push need. It does not use the rendered view from the
top, it does not use the force report beyond whether the jaw touched anything,
and it never reads the simulator's record.

**The gripper's own numbers.** The 70 mm of clear room, the 50 mm the jaw's
middle rides at, the 30 mm height of the jaw that puts its top edge at 65 mm,
the 270 mm of tool behind the fingertips and the 90 mm width of its body. All of
these belong to the hardware rather than to any glass, so the project allows
them to be written down, and none of them is tuned.

**One constant of its own**, which is the gain. It is chosen by [the
convergence
argument](02_how-it-works.md#3-why-the-push-is-a-fraction-of-the-shortfall-rather-than-all-of-it)
and then frozen, and it is the entire configuration of the method.

**One library, and it is NumPy.** The arithmetic over a handful of positions
and widths is all this solution does for itself. Carrying the jaw to the place
that arithmetic names is not part of it, because every solution here hands the
same kind of instruction to the same cell: the examiner carries the jaw with
its physics engine, and the real cell carries it with MoveIt. Both libraries
are permissively licensed, and because nothing is fitted there is no weights
file to redistribute and no licence inherited with it.

**No compute to rent.** The room test compares a pair of distances for every
pair of glasses, so its cost grows as the square of the number of glasses, and
there are four to six of them. The shortfall, the heading and the travel are a
few arithmetic operations each. The whole decision is a few hundred
floating-point operations and it finishes in far less time than the arm takes
to move anywhere. On the compute column that [the
examiner](../02_the-examiner.md) describes for the scorecard, this solution is
the zero the others are read against, and a solution that plans through a
learned model at run time or evaluates a large neural network sits hundreds or
thousands of times above it.

**What it does need is arm time.** The honest cost of this method is pushes and
looks, and the budget is what bounds them.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
