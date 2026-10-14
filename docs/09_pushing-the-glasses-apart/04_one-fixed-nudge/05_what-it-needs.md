# What it needs

This page is the bill for this solution. It lists the libraries it uses, the
machine it needs, the data someone must supply, and any licence that comes with
the weights.

## 1. What it needs

Everything the method needs is either measured by [the camera
work](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md) or is
a fixed number of the gripper. That is why it can be built first.

**It needs the measurements, and nothing more.** From `look()` it uses each
glass's position and widest width, for the room test and the shortfall. It uses
each glass's foot width and height, for the tipping rule and the test push. It
does not use the top view. It uses only one thing from the force report:
whether the jaw touched anything. It never reads the simulator's own record.

**It needs the gripper's own numbers.** These are the 76 mm of clear room, the
jaw heights, and the size of the tool. [The
examiner](../01_the-problem/03_the-examiner.md#3-what-the-examiner-draws) and
[pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md#the-height-that-counts-is-the-top-edge-of-the-jaw)
give these numbers. They belong to the hardware, not to any glass, and none of
them is tuned.

**It needs one constant of its own, which is the gain.** It is chosen by [the
convergence
argument](03_how-it-works.md#3-why-the-push-is-a-fraction-of-the-shortfall-rather-than-all-of-it)
and then frozen. It is the whole setup of the method.

**It needs one library, which is NumPy.** This solution only does arithmetic.
Moving the jaw is not part of it. The examiner moves the jaw with its physics
engine, and the real cell moves it with MoveIt. Both libraries have permissive
licences. Nothing is fitted, so there is no weights file and no licence that
comes with one.

**It needs no rented compute.** The room test compares every pair of glasses,
and there are only four to six. The shortfall, the direction and the push
length take a few sums each. The whole decision is a few hundred operations. It
finishes long before the arm moves. [The
examiner](../01_the-problem/03_the-examiner.md) puts a compute column on the
scorecard. On that column, this solution is **the zero the others are read
against**. A solution that plans with a learned model, or runs a large neural
network, costs hundreds or thousands of times more.

**What it does need is arm time.** This is the one real cost of the method.
Every push is a sequence of arm movements, and each one is followed by a fresh
look. Each takes seconds. A small gain means more pushes for the same gap. So
this method may use four pushes where a method that predicts uses one. That is
four times the time and four times the travel. Travel matters, because travel
is when a glass can be knocked. The examiner allows a fixed budget of pushes, so
this cost has a hard limit.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
