# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks. It names the older ideas behind it. Then it places it beside the
other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The earlier pages showed the method at work. This section adds up its
strengths and weaknesses. Both come from the same fact: the method claims very
little. That is what makes it a clean control.

### Its strengths

**It cannot be wrong about pushing, because it predicts nothing about
pushing.** Every other solution has a prediction that can be wrong. This one
has only a direction, which is right for any friction. Its distance is small on
purpose.

**Its answer can be read.** Every step is a number that can be printed. So a
person can read why it went wrong, instead of guessing. Every refusal has a
reason you can check with a ruler.

**One run of it is a measurement.** Nothing in it is fitted, and nothing is
random. So it behaves the same way on the hundredth table as on the first. [The
examiner](../01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
asks the trained solutions for several runs, because they vary. This one does
not need that. Its number has no spread.

**It tests the whole contact sequence.** The jaw closes, drops to height, feels
forward until the force fires, pushes along a line, backs off and lifts. A real
glass can be knocked over at any of these steps. This method runs all of them
with no planning code in the way. So if a glass falls while you build this
project, the fault is in the contact, not in a plan.

**Short pushes are safe pushes.** A glass can be knocked during any millimetre
of travel. This method moves each glass as little as it can. The small gain
gives it that habit.

### Its weaknesses

One weakness matters more than the rest, so it comes first.

**It has nowhere to stand.** The jaw pushes in the direction it points. So the
arm comes in along the same line as the push. To push a glass straight away
from its neighbour, the arm must come in from the neighbour's side. The tool is
long and gets wider behind the fingertips. All of it is at the height of the
push, so all of it must miss every glass on the table.
[What the examiner draws](../01_the-problem/03_the-examiner.md#3-what-the-examiner-draws)
gives the tool's sizes. In a tight group, the neighbour stands exactly where the
tool would need to be. This method has only one direction to offer. So when
that direction is blocked, it must refuse the glass. **Every solution that
searches over directions can ask for a different approach. This one cannot.**
So for this method, where the arm comes in from matters more than where the
glass goes.

![The glass to be pushed, the neighbour it is being pushed away from, and the closed jaw drawn to scale on the line between them: the fingertips come down 10 mm outside the glass, and the 266 mm of tool behind them lies along the same line, straight through the place the neighbour is standing.](../../images/pushing-the-glasses-apart/one-fixed-nudge/nudge-pages-nowhere-to-stand.png)

**It cannot help a glass crowded from two sides.** A push away from one
neighbour is a push towards the other.
[A table where it does not](04_a-worked-example.md#a-table-where-it-does-not)
shows this.

**It never looks at the free table.** The shortfall says how far, but nothing
says where to. The method does not check that the place it sends a glass is
empty. It does not check that the place is in the glass zone, in the arm's
reach, or clear of the rack. It does
not check for a glass in the path either. So it can drive one glass into
another. That cannot be undone, because two upright glasses that hit each other
is how a glass falls over.

**It does not use the shared target layout.** [The target
layout](../01_the-problem/04_the-target-layout.md) works out where every glass
should finish, and the least travel the task needs. This method uses neither.
It pushes away, not towards a goal. So its travel will be well above that
least travel.

**It does not pick the safer glass of a pair.** Of two crowded glasses, the one
on the wider foot is safer to push. This rule always pushes the glass that is
short of room, which may be the narrower one. If that glass fails the tipping
check, the method refuses it. It does not try the other one. That is safe, but
it racks fewer glasses. A baseline must turn down easy fixes like this to stay a
baseline.

**It throws away the force report.** The jaw reports how hard it pushed and how
far the glass moved. Both depend on the friction. So they are the only clue
about the friction that this cell gives.
[Why the force reading matters](../01_the-problem/02_what-goes-in-and-what-comes-out.md#why-the-force-reading-matters)
explains this. This method reads none of it. It only checks whether the jaw
touched anything. This is the deepest reason it is the weakest of the six.
Every solution that does better reads that report in some way.

**It pays in pushes, and the budget is limited.** Its only way to recover is to
push again. A table that needs many pushes can use up the budget.

These strengths and weaknesses are not new. The next section names the older
ideas the method is made of.

## 2. The general ideas behind this

The last section judged the method on its own. This section names the older
ideas it is built from. Knowing them tells you where to expect it to work and
where not.

### Proportional control

A correction equal to the error times a fixed gain is a **proportional
controller**. It is the simplest member of a family called PID. PID adds a term
for the error added up over time, and a term for how fast the error changes.

It works well when three things are true. The error can be measured. The
correction acts in the right direction. And the effect of the correction is at
least within known limits. Then a small gain is stable with no model at all.
These are weak needs, which is why proportional control is used everywhere.

It has two known weak points. First, it is slow when a good model exists,
because a model can do in one step what the controller does in several.
Second, it leaves a steady error if something keeps pulling against it. The
second point does not apply here, because nothing pulls the glass back. The
first point applies fully. The six solutions exist to find out what a good
model is worth.

### Singulation

Separating crowded objects so they can be picked one at a time is called
**singulation**. Chang, Smith and Fox's *Interactive Singulation of Objects
from a Pile* (ICRA 2012) named this problem for robot handling. It already uses
the same pattern as this solution: act on the pile, look again, repeat.

It works well in bin picking and warehouse work, where the only question is how
to reach each object. It fits less well here. That work assumes walls that
keep objects in, and objects lying flat that cannot fall over. An open table of
upright glasses has neither. So the pattern carries over, but the safety does
not.

### Fixed push policies

Pushing a short fixed distance in a direction chosen by a simple rule is a real
method. Danielczuk and others' *Linear Push Policies to Increase Grasp Access
in Dense Clutter* (IEEE CASE 2018) describes it clearly. They found that such
pushes are cheap, and often open enough space for a grasp. This solution relies
on that finding.

It works well for dense clutter in a bin, where a push does little harm. It
fits less well here, for the reasons in the last section and one more. A flat
object in a bin can be pushed from a side the gripper can easily reach. An
upright glass must be pushed from its side, and the side is where the neighbour
is.

### Quasi-static planar pushing, which this solution deliberately does not use

There is a well-developed theory of what happens when an object is pushed
slowly across a table. Mason's *Mechanics and Planning of Manipulator Pushing
Operations* (IJRR 1986) gave the main result, called the voting theorem. It
says which way a pushed object turns. That depends on where the line of the
push passes, compared with the object's centre of friction. Lynch and Mason's
*Stable Pushing: Mechanics, Controllability and Planning* (IJRR 1996) used this
to plan pushes that carry an object along a chosen path.

This theory works when the friction, and how the weight sits on the foot, are
known or can be measured. Here, neither is measured. Yu, Bauza, Fazeli and
Rodriguez's *More than a Million Ways to Be Pushed* (IROS 2016) measured what
that costs. They pushed the same objects the same way many thousands of times.
The results spread out widely, and the spread does not average away. So the
choice is between a prediction that needs an unknown number, and no prediction.
This solution makes no prediction. [Solution
4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) makes the other
choice and learns a model instead.

### Guarded moves

A motion that ends when a sensor fires, not at a computed point, is a **guarded
move**. It is one of the oldest ideas in robot assembly. Lozano-Pérez, Mason and
Taylor's *Automatic Synthesis of Fine-Motion Strategies for Robots* (IJRR 1984)
explains why it helps. When an object's position is uncertain, a motion that
stops on a sensor is reliable. A motion that stops at a computed point is not.

It helps with every contact against an object measured from a distance. That is
every contact in this project. But it is not a full answer. A guarded move
finds the surface. It does not say what to do next. So it prevents some
collisions, but it does no planning.

### Baselines, as a discipline

Last, this solution is a **baseline**. A baseline is the simplest method that
does the job at all. It is built first and kept as the number every other
method is scored against. A method that beats nothing has not been shown to be
good.

Baselines matter most when several methods are compared and some are
expensive. A price can only be judged against a free choice. A baseline goes
wrong when someone keeps improving it until it competes. Each small change
seems reasonable, but together they spoil it. This method has one place where
that could happen, which is the gain. That is why the gain is argued, not tuned
on the training tables. A baseline must also be scored on the same tables, in
the same way, as the methods meant to beat it. [The
examiner](../01_the-problem/03_the-examiner.md) does that.

These ideas say what kind of method this is. The next section places it beside
the other five solutions.

## 3. Where it sits among the other five

The last section named the ideas inside the method. This section compares it
with the other five. [The overview of the
six](../03_the-six-solutions/01_how-the-six-compare.md) states the question it
answers: **does any learning beat a fixed nudge?** [What it
is](01_what-it-is.md#1-introduction) says why a solution that cannot beat it has
earned nothing. The scores are in [the results](../10_the-results.md#2-the-results).

**Against [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md),**
the difference is a search and a ranker. Solution 2 uses the same input, room
test and tipping rule. Then geometry makes many possible pushes for each
crowded glass, and a model ranks them. Because it can choose its direction, it
avoids two of this solution's main weaknesses. Its scored pushes are also
examples that other solutions can learn from. So it teaches solutions 3 and 6,
and this solution teaches nobody.

**Against [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md),**
the difference is everything that is fitted. Solution 3 learns from solution
2's examples, and outputs a chunk of waypoints instead of a push. The examples
are free, so it pays for training runs on this laptop. If it does not clear
more tables than a fixed nudge, that training bought nothing.

**Against [solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md),**
the comparison is the sharpest. Solution 4 learns a model of what a push does,
and plans with it while it runs. It buys exactly the prediction this solution
refuses to make. It pays twice: once for training data, and once for planning
time on every push. So this pair asks the question directly: **is a prediction
worth more than a repeat?**

**Against [solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md),**
the link is that both fit nothing in this cell. This one has one argued
constant. Solution 5 uses a large model trained somewhere else.
**Against [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md),** which is that same
model trained further here, the fixed nudge is the floor. Both solutions 5 and 6
must clear it before the difference between them matters.

So think of this method as **the first thing to build and the last thing to
ship**. Build it first. It is the cheapest way to get a real push against a
real glass. Everything after it needs the same contact steps and the same
refusals. Do not ship it, because of the weaknesses in [where it is strong and
where it breaks](#1-where-it-is-strong-and-where-it-breaks).

Also read it the other way round, as the book on telling the glasses apart
reads [its own written
rule](../../08_seeing-the-glasses/05_rules-on-the-table/01_what-it-is.md). This
method works at all only because of four promises. The glasses stand upright on
a flat table. The gripper's clear room is a known constant. [The camera
work](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
reports a position and a width for every glass. And a refusal is an acceptable
answer. Each of the other five needs fewer of these promises. So if a fixed
nudge looks good to you, that says how generous this book's promises are. The
value of the other five is what they do when those promises fail.

← [What it needs](05_what-it-needs.md) · [Geometry generates, a model ranks — what it is](../05_geometry-generates-a-model-ranks/01_what-it-is.md) →
