# One fixed nudge — what it is

> **What it uses** — NumPy for the arithmetic over a handful of positions and
> widths, and nothing else. Carrying the jaw to the places the arithmetic names
> belongs to the cell rather than to this solution: on the test bench the
> physics engine does it, and in the real cell MoveIt does.
> There is no model, no weights file, no training set and no licence
> condition, because not one number in this solution was fitted to anything.
> **What it does** — When a glass has no clear room for the gripper to close
> round it, the method finds the one neighbour whose edge reaches furthest
> into that room, works out how much room the glass is short of, and pushes
> the glass directly away from that neighbour by a fixed fraction of the
> shortfall, at the lowest height the gripper can reach. Then it looks at the
> table again and does the same arithmetic on what it now sees. There is no
> search over directions, no map of the free table, and above all no model of
> what a push does: the method never predicts where the glass will land, so it
> repeats instead of predicting. The repeating ends when every glass has room,
> when the push budget is spent, or when the only honest answer left is a
> refusal.
> **How the output is produced** — from the measurements, compute for each
> glass how much clear room it is short of, measured to each neighbour's edge;
> take the glass with the worst shortfall and the neighbour responsible for
> it; check that glass against the tipping rule and refuse it if it fails;
> point the jaw along the line that runs from the neighbour's middle through
> the glass's middle; set the travel to a fixed fraction of the shortfall; put
> the start point on that same line, a little outside the glass's widest part;
> and hand the result over as one parameterised push, which the bench's own
> macro expands into a jaw trajectory. Then look again and start over.
> **How it differs from the other five** — solution 2 has geometry generate
> many candidate pushes and fits gradient-boosted trees to rank them, so it
> searches where this one computes one answer; solution 3 fits ACT, and then
> Diffusion Policy, to demonstrations and emits a chunk of waypoints rather
> than a push; solution 4 learns a model of what a push does and plans through
> it at run time, which buys exactly the prediction this one refuses to make;
> solution 5 runs SmolVLA as it downloads, so like this one it fits nothing
> here, but it carries 450 million parameters somebody else fitted on 487
> community datasets; and solution 6 is that same SmolVLA with its training
> continued here by low-rank adaptation, which makes it and solution 5 the
> sharpest pair in the set. This one is the only solution that holds no fitted
> numbers at all, and the only one that makes no claim whatever about where a
> pushed glass will go.
> **What it costs** — no data, because nothing learns; no training time, for
> the same reason; no accelerator to rent, so nothing to pay a cloud provider,
> because the whole computation is a few hundred arithmetic operations on four
> to six glasses and it finishes long before the arm has moved; and no licence
> condition, because the two libraries are already in the cell and neither
> constrains what is done with them. The entire cost is arm time, paid in
> pushes and in looks.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes the simplest thing that can move a crowded glass away
from its neighbour, and then argues that the set of six would be worthless
without it. The method is one subtraction, one multiplication and a loop. It
measures how much clear room a glass is short of, pushes that glass a fixed
fraction of the shortfall straight away from whatever is crowding it, and
looks again. Nothing in it was fitted, nothing in it was searched for, and
nothing in it predicts anything.

The reason to write it carefully rather than wave at it is that it is **the
control**. Four of the other five solutions pay for their answers with
labelled data, training runs and rented hardware, and the fifth carries a
large model somebody else paid for. None of those prices can be judged in the
abstract. They can only be judged against what the same table costs when
nobody pays anything at all, and that is the number this document is here to
define. Every other solution in the set has to beat a fixed nudge, and if it
cannot, it has earned nothing.

By the end you will understand what the shortfall is and why it is measured to
the neighbour's edge rather than to its middle, which makes the test on a pair
of glasses asymmetric. You will understand what closed-loop control is, in
plain words and as a piece of programming, and why this solution is nothing
else. You will understand why pushing a fraction of the gap converges where
pushing the whole gap overshoots, and why that argument rests entirely on
nobody knowing the friction. You will understand why never predicting means
never being wrong about physics the method never claimed to know, and what
that costs, which is pushes rather than error. And you will understand the one
thing this solution cannot do that its nearest neighbour in the set can: it
produces no scored candidates, so it is the teacher for nobody.

Two honest notes before the method starts, because both change how the rest
should be read.

**Part of this solution is built and part of it is a design**, and the two are
separated plainly in [what is built and what is a
design](02_how-it-works.md#5-what-is-built-and-what-is-a-design). The bench, the room test, the
tipping rule and the loop all exist in this repository and have been run. The
particular rule for choosing a direction and a distance that this document
describes is a design that would sit inside them.

**No glass's size appears below.** The cell's rule is that no glass's
dimensions are written down anywhere, so this document speaks in relations —
wider than its neighbour, standing on the narrowest foot its kind allows — and
quotes numbers only where they belong to the gripper, to the cell, or to a
results file in the repository.

## 2. The problem this solves

[Pushing the glasses apart](../01_the-problem/01_what-is-asked-for.md) begins
where [telling them apart in a
picture](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
ended. The arm knows where every glass stands, how tall it is, how wide it is
at its widest and how wide it is at its foot, and every one of those readings
carries a measurement error rather than being exact. Some of the glasses stand
close enough together that the open jaw cannot get round one of them without
fouling the one beside it, and the arm has to move them apart by dragging them
across the table rather than by lifting them.

What makes that a problem rather than an exercise is one missing number. A
pushed glass slides while the jaw touches it below a height set by its own foot
and by the friction between the glass and the table, and tips above that
height, which is the whole subject of [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md). **The friction is never told to any
solution and nothing in the cell measures it.** So how far a glass travels for
a given push is unknown before the push is made, and it stays unknown
afterwards except through what the table looks like next.

Everything the six solutions disagree about follows from that one gap. A
solution can try to fill it, by estimating the friction, by learning a model of
what a push does, or by learning the push itself from examples of pushes that
worked. Or it can refuse to fill it, make no prediction at all, and recover by
measuring. This solution takes the second branch, and it takes it as far as it
can be taken: it predicts nothing, assumes nothing about friction, and keeps
only the one claim about a push that does not need friction to be true.

## 3. The main idea

That one claim is the whole method, so it is worth stating before the
arithmetic. **Pushing a glass away from a neighbour increases the distance
between them, whatever the friction is.** The friction decides *how far* the
glass goes. It does not decide which way. So a method that is confident about
direction and modest about distance is making the only claim the cell can
support, and it can then fix the distance by repeating rather than by knowing.

From that, the method makes four decisions and no others, and each one is a
single line of arithmetic on numbers the arm already has.

**Which glass.** Take the glass that is short of the most room. The next
section defines that shortfall exactly.

**Which direction.** Straight away from the neighbour whose edge reaches
furthest into that glass's room. The heading is the direction of the line that
runs from the neighbour's middle through the glass's middle, continued
outwards.

**How far.** A fixed fraction of the shortfall. The fraction is less than one,
so the push closes part of the gap rather than all of it, and the rest is left
to the next pass.

**How high.** As low as the gripper can reach, always. This is not really a
decision, because there is never a reason to push higher: the lower the
contact, the further the glass is from tipping, so the only question the height
raises is whether even the lowest contact is low enough. That question is
answered in [when a glass cannot be pushed
safely](04_a-worked-example.md#1-when-a-glass-cannot-be-pushed-safely).

Then the arm looks at the table again, and the four decisions are made afresh
from the new measurements. Nothing is remembered from one pass to the next
except how many pushes have been spent.

The word **fixed** in the name needs care, because it does not mean a fixed
number of millimetres. A rule that pushed the same distance every time would
be badly wrong, since the glasses on a crowded table are short of anything
from almost nothing to several tens of millimetres, and one distance cannot
serve both ends of that range. What is fixed is the **fraction**: one constant,
the same for every glass on every table, chosen once by argument and never
changed. That single constant is the only free number in the entire method.

← [The six solutions — same table, six ways to push](../03_the-six-solutions.md) · [One fixed nudge — how it works](02_how-it-works.md) →
