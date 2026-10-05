# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas it is built from so that
you can read about them outside this book, and places it beside the other five.
By the end you will know when this is the solution to reach for, and when it is
the wrong one.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The strengths all follow from how little the method claims, and the weaknesses
all follow from the same thing, which is what makes it a clean control rather
than merely a weak solution.

**It cannot be wrong about pushing, because it says nothing about pushing.**
Every other solution has a prediction somewhere that can be wrong. This one has
a direction, which is right for any friction, and a distance that is
deliberately too small.

**Its answer can be read.** Every step is a number that can be printed, so a
wrong answer is something a person reads rather than something they guess at,
and every refusal has a reason that can be checked with a ruler.

**One run of it is a measurement.** Nothing in it was fitted and nothing in it
is drawn at random, so it behaves the same way on the hundredth table as on the
first. The repeats that [the bench](../02_the-test-bench.md) requires of the trained
solutions, because their training and their actions both vary, are not needed
here, and that makes it the one solution in the set whose number carries no
spread.

**It exercises the whole contact sequence.** Closing the jaw, dropping to
height, feeling in until the force threshold fires, pushing slowly along a
line, retreating before lifting: every one of those steps is where a real glass
gets knocked over, and this method runs all of them with no planning code in
the way. When something falls over while the work in this book is being built,
this method tells you the fault was in the contact, because there was no plan
to be wrong.

**Short pushes are safe pushes.** Every millimetre of travel is a millimetre in
which something can be knocked, so a method whose instinct is to move a glass
as little as possible has a good instinct, and the small gain gives it that
instinct for free.

The weaknesses divide into one that makes the others academic and several that
matter in their own right.

**It has nowhere to stand.** The approach runs along the same line as the push,
so pushing a glass straight away from its neighbour asks the arm to put 270 mm
of tool where the neighbour is. In a tight group that is impossible, and the
method cannot offer a second heading, so it refuses. The honest reading is that
**the approach is a harder constraint than the departure**, and this solution
is the one that cannot choose its approach at all.

**It cannot help a glass that is crowded from two sides.** A push away from one
neighbour is a push towards the other, so the method oscillates or runs out of
budget. No gain fixes it, because the difficulty is in the direction.

**It never looks at the free table.** The shortfall says how far, and nothing
in the method says where to. It does not ask whether the place the glass is
being sent is empty, inside the glass zone, inside the arm's reach or clear of
the rack, and it does not ask whether another glass is standing in the corridor
the glass will travel down. A push that drives one glass into another is the
failure this creates, and it is also the failure that cannot be recovered,
because a collision between two upright glasses is how a glass goes over.

**It does not use the shared target layout.** [The target
layout](../01_the-problem/02_the-target-layout.md) computes where every glass should finish and
reports the least travel the task could possibly need, and this method consults
neither. It pushes away rather than towards, so its total travel will sit well
above the displacement floor, and reading it against that floor is the clearest
way to see what choosing a destination is worth.

**It does not choose the safer glass of a pair.** Of two crowded glasses, the
one standing on the wider foot has the more room under the tipping limit, so it
is the safer one to push. This rule always pushes the glass that is short of
room, which may be the narrower of the two, and when that glass fails the
tipping check the method refuses rather than pushing the other one. That is
safe, but it costs yield, and it is the kind of easy improvement a baseline has
to decline in order to remain a baseline.

**It throws away the force report.** The force the jaw felt and the distance the
glass moved for it are consequences of the friction, so they are the only
evidence about the friction that this cell can produce. The method reads none
of it, which is exactly why every other solution has something to improve on.

**It pays in pushes, and the currency is limited.** The budget bounds the
repetition, so a method whose only recovery is to repeat can run out of
recoveries on a table that needs many.

## 2. The general ideas behind this

Nothing here was invented for glassware. Knowing which older ideas the method
is made of says where it should be expected to work and where it should not.

### Proportional control

A correction that is the measured error multiplied by a fixed gain is a
**proportional controller**, the simplest member of the family usually written
as PID, which adds a term for the accumulated error and a term for its rate of
change. **Where it is normally right:** when the error can be measured, when
the correction is known to act in the right direction, and when the factor
relating the correction to its effect is at least bounded, a small gain is
stable with no model of the system whatever. That is a remarkably weak set of
requirements, and it is the reason proportional control is everywhere. **Where
it is not right:** a proportional controller is slow when an accurate model is
available, because a model lets one step do what the controller does in
several; and it leaves a steady error whenever the system has a constant offset
pulling against it, which is the usual reason for adding the integral term.
Here the second objection does not bite, because the measurement is of position
and the correction moves position, so there is no offset to accumulate against.
The first objection bites exactly, and the whole set of six exists to find out
what an accurate model would be worth.

### Singulation

Separating crowded objects so that they can be picked up one at a time is
called **singulation**, and it is the word to search for. Chang, Smith and
Fox's *Interactive Singulation of Objects from a Pile* (ICRA 2012) named the
problem for manipulation, and it already contains the structure this solution
uses: act on the pile, look again, repeat. **Where it is normally right:** bin
picking and warehouse work, where a pile has to become a sequence of graspable
objects and the only question is access. **Where it is not:** the setting that
work assumes has walls that stop an object leaving the workspace and objects
lying flat that cannot be knocked over. Neither is true on an open table of
upright glasses, so the structure carries over and the safety does not.

### Fixed push policies

Pushing a short fixed distance along a direction chosen by a simple rule is a
real method rather than a straw man. Danielczuk and colleagues' *Linear Push
Policies to Increase Grasp Access in Dense Clutter* (IEEE CASE 2018) is the
clearest statement of it, and its finding is the one this solution relies on:
such pushes are cheap and often sufficient to open enough space for a grasp.
**Where it is normally right:** dense clutter inside a bin, where a push cannot
do much harm. **Where it is not:** here, for the two reasons above and for a
third that is specific to upright objects. A flat object in a bin can be pushed
from a direction the gripper can easily occupy, while an upright glass must be
pushed from the side, and the side is where the neighbour is.

### Quasi-static planar pushing, which this solution deliberately does not use

There is a well developed theory of what happens when an object is pushed
across a table. Mason's *Mechanics and Planning of Manipulator Pushing
Operations* (IJRR 1986) established the result the field rests on, usually
called the voting theorem: which way a pushed object rotates is decided by
where the line of pushing passes relative to the object's centre of friction,
and that can be worked out without knowing the pressure under the object in
detail. Lynch and Mason's *Stable Pushing: Mechanics, Controllability and
Planning* (IJRR 1996) turned it into planned pushes that carry an object along
a chosen path. **Where it is normally right:** when the friction and the way
the object's weight sits on its foot are known or can be measured. **Where it
is not:** here, because nothing in this cell measures either. Yu, Bauza, Fazeli
and Rodriguez's *More than a Million Ways to Be Pushed* (IROS 2016) is the
honest measurement of what that costs: they pushed the same objects the same
way many thousands of times and recorded how far the outcomes scatter, and the
scatter is neither small nor noise that averages away. So the choice is between
a prediction that needs a number nobody has and no prediction at all. This
solution takes no prediction at all. [Solution
4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) takes the other branch and learns the model instead.

### Guarded moves

Ending a motion on a sensed condition rather than at a computed coordinate is a
**guarded move**, and it is one of the oldest ideas in robot assembly.
Lozano-Pérez, Mason and Taylor's *Automatic Synthesis of Fine-Motion Strategies
for Robots* (IJRR 1984) is the reference statement of why: when the position of
a thing is uncertain, a motion that stops on a sensor is reliable where a motion
that stops at a coordinate is not. **Where it is normally right:** every
contact made against an object whose position was measured from a distance,
which is every contact in this project. **Where it is not a complete answer:** a
guarded move tells the arm where the surface is and says nothing about what to
do once it is found, so it removes a class of collisions and solves no part of
the planning.

### Baselines, as a discipline

The last thing this solution is, is a **baseline**: the simplest method that
does the job at all, built first and kept as the number everything else is
scored against. The practice does not come from robotics. It is what keeps a
claim honest, because a method that beats nothing has not been shown to be
good. **Where it is normally right:** whenever several methods are compared,
and especially when some of them are expensive, because a price can only be
judged against a free alternative. **Where it goes wrong:** a baseline that is
quietly improved until it is competitive has stopped being a baseline, and the
improvements are usually small and reasonable one at a time. This method has
exactly one place where that could happen, which is the gain, and that is why
the gain is argued rather than swept over the training tables. The discipline
also requires that the baseline be measured on the same tables with the same
scoring as the methods meant to beat it, which is what [the
bench](../02_the-test-bench.md) is for.

## 3. Where it sits among the other five

[The overview of the six](../03_the-six-solutions.md) states the question this solution
answers in one line: **does any learning beat a fixed nudge?** It is answered
by comparing this solution against all five of the others, and that is the only
comparison in the set with this shape, because every other comparison is
between two methods that both cost something.

**Against [solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md)** the gap is a search and a
ranker. Solution 2 uses the same input, the same room test and the same tipping
rule, and then has geometry generate many candidate pushes for each crowded
glass and gradient-boosted trees rank them. Two of this solution's three
structural weaknesses are weaknesses solution 2 does not have, because a method
that may choose its direction can find a push out of the gap between two
neighbours and can find an approach the tool actually fits into. Solution 2 also
has the one thing this solution does not, which is that its scored candidates
are demonstrations, so it is the teacher for solutions 3 and 6 and this one is
the teacher for nobody.

**Against [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md)** the gap is
everything fitted. Solution 3 fits ACT, and then Diffusion Policy, to those
demonstrations, and emits a chunk of waypoints rather than a push. The
demonstrations themselves are free, so what it pays is a training run with
several seeds. That run was budgeted for a rented accelerator and in the event
needed none, so the price is hours of this laptop rather than money. If it does
not clear more tables than a fixed nudge, every one of those prices bought
nothing.

**Against [solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md)** the comparison is the sharpest
statement of what this document is about. Solution 4 learns a model of what a
push does and plans through it at run time, first with the small ensemble
already written in this project and then with TD-MPC2 off the shelf. It is
buying exactly the prediction this solution refuses to make, and it pays twice:
once in training data and once in planning time per push, which the compute
column records. So the pair of them asks the question directly: **is a
prediction worth more than a repetition?**

**Against [solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md)** the two of them are the
only solutions in the set that fit nothing here, which makes the pair worth
reading together even though they have nothing else in common. This one carries
one argued constant. Solution 5 carries SmolVLA as it downloads, which is about
450 million parameters pretrained on 487 community datasets of real
teleoperation, so it fits nothing in *this cell* while resting entirely on
fitting done somewhere else. **Against [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md)**, which is the same SmolVLA weights with their
training continued here by low-rank adaptation, the fixed nudge is the floor
that both halves of that pair have to clear before the difference between them
is worth discussing at all.

The right way to think about this method, then, is as **the first thing to
build and the last thing to ship**. Build it first, because it is the cheapest
way to get a real push happening against a real glass, and because everything
after it needs the same contact sequence and the same refusals. Do not ship it,
because it has one heading to offer, it cannot help a glass crowded from two
sides, and it never asks whether the place it is sending a glass is clear.

And read it in both directions, as the book on telling the glasses apart reads
[its own written
rule](../../08_seeing-the-glasses/05_rules-on-the-table/01_what-it-is.md).
The usual reading is about the other five: if a model cannot beat a
fixed nudge, it has earned nothing, because it cost data, training time and
hardware that this one did not, so matching it is not a result. The other
reading is about the problem. This method works at all only because the glasses
stand upright on a flat table, because the gripper's clear room is a known
constant, because [the camera
work](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
reports a position and a width for every glass, and because a refusal is an
acceptable answer. Each of the other five needs fewer of those promises than
this one does. So a reader who finds a fixed nudge convincing should read that
as a statement about how generous this book's promises are, and the value of
the other five is what they do when the promises stop.

← [What it needs](05_what-it-needs.md) · [Geometry generates, a model ranks — what it is](../05_geometry-generates-a-model-ranks/01_what-it-is.md) →
