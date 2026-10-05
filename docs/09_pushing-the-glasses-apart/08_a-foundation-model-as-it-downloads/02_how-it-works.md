# How it works

This page explains what happens inside this solution, part by part. It follows
[what it is](01_what-it-is.md), which states the question the solution answers
and the single idea it rests on, and it assumes you have read that page first.
By the end of this one you will understand what the method is built from, what
each part does with what the part before it produced, and which part decides
the answer.

## Contents

1. [A model that sees, is told, and acts](#1-a-model-that-sees-is-told-and-acts)
2. [Where such a model gets its competence](#2-where-such-a-model-gets-its-competence)
3. [What is borrowed, and what is not](#3-what-is-borrowed-and-what-is-not)
4. [The actions come out in somebody else's units](#4-the-actions-come-out-in-somebody-elses-units)
5. [The instruction is nearly dead weight here](#5-the-instruction-is-nearly-dead-weight-here)
6. [The force reading has nowhere to go](#6-the-force-reading-has-nowhere-to-go)
7. [The domain gap, which is the heart of this document](#7-the-domain-gap-which-is-the-heart-of-this-document)
8. [The honest expectation](#8-the-honest-expectation)
9. [The price of the model, and why this model](#9-the-price-of-the-model-and-why-this-model)

## 1. A model that sees, is told, and acts

The kind of model being borrowed needs explaining before anything else,
because the rest of this document depends on what goes into it and what comes
out.

Three things go in together. The first is **what the camera sees**, as an
ordinary picture. The second is **an instruction in ordinary words**, written
the way a person would write it, such as "pick up the red block" or "push the
glasses apart". The third is **the robot's own joint readings**, which say
where each joint is at this moment, so the model knows the shape the arm is
currently in and not only what is in front of it.

One thing comes out: **robot actions**. The model returns targets for the robot
to move to, at the rate a controller consumes them, so a single answer from the
model is a short run of movement rather than a single pose.

A model with those three inputs and that one output is called a
**vision-language-action model**, and the name is simply the three parts listed
in order. The useful thing about the name is that it says where the model sits
in a system. It is not a perception component that reports what it sees and
leaves the acting to something else, and it is not a controller that is handed
a goal in numbers. It takes the raw picture and the human sentence at one end
and emits movement at the other, with nothing in between that a person writes.

That is a genuinely different shape from the other learned solutions in this
book. Solution 4's learned part is a model of how the world changes, and a
separate search uses it to choose. Solution 2's learned part is a ranker, and
hand-written geometry proposes what it ranks. Here there is one network and it
does the whole job, which is why a single borrowed file can be a complete
answer to the problem, and also why there is no small piece of it that can be
corrected when it is wrong.

## 2. Where such a model gets its competence

A model with no knowledge of this cell can only be worth trying if it knows
something general, so it is worth being precise about where that general
knowledge comes from.

It comes from **pretraining on very many recorded demonstrations, across many
different robots and many different tasks**. Somebody collected an enormous
pool of recordings in which a robot arm was driven by a person through some
piece of manipulation — reaching for things, grasping them, moving them,
putting them down — with the camera picture, the instruction and the joint
readings all recorded together, and the model was fitted on all of it at once.
SmolVLA's pool is **487 community datasets of real teleoperation**, which means
real robots in real rooms, driven by real people.

What a model learns from a pool like that is not any one of those tasks. It is
the shape that manipulation has in general: that an arm approaching an object
slows as it arrives, that a gripper closes when it is on the object and not
before, that movement near a surface stays near the surface, that a push is a
contact followed by travel in one direction rather than a jerk in several. The
comparison from programming is a library of general routines rather than a
program for one job: nothing in it solves your problem, but the parts it offers
are the parts most problems of that family are built from.

**So what this model brings to this problem is a general sense of how
manipulation goes, and nothing whatever about this cell.** It has no idea that
this table has a glass zone, that a rack sits in one corner, that the arm
reaches comfortably between 300 and 780 mm from its base, or that pushing a
glass above a certain height tips it over instead of moving it. Those are
facts about this cell, they are published once in [the
cell](../../08_seeing-the-glasses/01_the-cell.md) and [the problem](../01_the-problem/01_what-is-asked-for.md), and a model fitted
elsewhere has never met any of them.

## 3. What is borrowed, and what is not

That division matters enough to state it flatly, because it is what makes this
solution the baseline it is meant to be.

**Nothing whatsoever is fitted here.** The weights are downloaded and used
unchanged. There is no training run, no fine-tuning, no small correction fitted
on this cell's data, and no threshold tuned on the bench's training tables. If
a number in this solution came from somewhere, it came from somebody else's
robots.

So the model has never seen this cell. It has never seen these glasses — not
the straight glass, not the tapered glass, not the stemmed glass and not the
short stemmed glass. It has never seen this jaw, which is two fingers and two
pads held closed and level, 30 mm tall, riding as low as the gripper reaches.
And it has never seen a table rendered the way this bench renders one.

What **is** borrowed is everything else: the architecture, the weights, the
convention by which pictures are read, the convention by which words are read,
and the convention by which actions are emitted. Every one of those was fixed
by somebody else, for somebody else's robots, before this project existed. That
is the trade this solution makes, and the next three sections are the three
places where the trade bites.

## 4. The actions come out in somebody else's units

The first place it bites is at the output, and it is a practical difficulty
rather than a deep one, but it has to be solved before anything can run at all.

A model fitted on recordings of particular robots emits actions in the layout
and the units those robots used. The arm here is a UR5e with a two-finger
gripper, and it is not the arm the recordings were made on. So the numbers the
model returns are not automatically waypoints for this jaw; **turning them into
waypoints is an interpretation, and somebody has to choose it.** Nothing in the
model's pretraining knows this arm's joint layout, its reach, or how high above
the table a height of zero means.

This matters for the comparison in a specific way. A bad interpretation would
make the model look worse than it is, and the result would then be a
measurement of the interpretation rather than of the model. So whatever
convention is chosen has to be **chosen once and used by both solution 5 and
solution 6**, because the pair is only clean while everything except the
training is held still. That convention is now chosen and written down, in
`05-smolvla-as-it-downloads/joining.py`, and the folder's README says what had
to be decided in it and why. It turned out to be a larger decision than this
section expected, because the checkpoint settles less about its own action
space than the section assumed.

It is also worth noting that this is the step the bench's own arrangement was
designed to allow. [The test bench](../02_the-test-bench.md) accepts a run of
waypoints directly, without the push macro, precisely so that a policy which
thinks in movement is not squeezed into three numbers describing a push. Both
that path and the rendered view from the top now exist in the bench, and this
solution uses them as they come.

## 5. The instruction is nearly dead weight here

The second place the trade bites is at the input, and it is the one most likely
to be misread, so it needs stating carefully.

A model of this kind earns its middle word by taking **different instructions
for different tasks**. That is the whole reason the language half is there: one
set of weights can be asked to pick a thing up, or to put a thing down, or to
open a drawer, and the sentence is what selects which. The pool it was fitted
on contained a great many different instructions, and the model's ability to
respond to them is a real capability that took a great deal of data to acquire.

**This problem has one instruction.** Every table, every push, every look again:
the same sentence, because the task never changes. A quantity that takes the
same value every time carries no information, in exactly the sense information
is normally meant — knowing the instruction tells you nothing you did not
already know about the situation. So the language half of this model, in this
problem, does no work.

Two consequences follow, and the second one is the important one.

The first is that **the model is being used here as an expensive visuomotor
policy**: a thing that looks at a picture and produces movement. That is
precisely what solution 3 fits from demonstrations, with a far smaller network
and nothing borrowed. So the natural question — what is the extra size buying?
— has an answer that does not involve language at all. It is buying the
pretraining, and only the pretraining.

The second is a warning about reading the result. **A reader should know this
before concluding anything about vision-language-action models in general from
this number.** If this solution scores badly, it has not been shown that
vision-language-action models are a poor idea. It has been shown that one such
model, used with a constant instruction, on rendered pictures unlike its
training pictures, with nothing fitted, scores badly — which leaves the
model's actual selling point untested, because this problem never asks it to
do the one thing the language half exists for. A single-task cell is simply
not where that capability can be seen.

## 6. The force reading has nowhere to go

The third place the trade bites is the most interesting, because it is a
mismatch between what this problem gives a solution and what this model is able
to accept.

[The test bench](../02_the-test-bench.md) is emphatic that the force reading is the
single most valuable thing it reports. Friction is never told to any solution
and nothing in the cell measures it, so how much force it took to start a glass
moving, and how far the glass travelled for that push, are the only evidence
about friction that exists anywhere. The bench's own words are that every
solution which does better than a blind nudge does so by reading that channel,
either by reasoning about it or by learning from it.

**This model has three input slots, and force is not one of them.** It takes a
picture, a sentence and the joint readings. The jaw's report of what it felt —
whether it was blocked on the way down, how far it travelled before touching,
whether it jammed, the most force it felt, how far the glass moved after
contact — has nowhere to enter. So the one channel through which friction is
observable at all is, for this solution, closed.

That does not leave the solution blind, and it is worth being exact about what
remains. The arm looks again after every push, so the **outcome** of a push is
visible in the next picture: a glass that moved a long way looks different from
a glass that barely moved. What is lost is everything that happened *during*
the push, which is where the force signal lives, and which is the part that
distinguishes a glass that slid from a glass that leaned and settled back. So
this solution can learn nothing from a push except where the glasses ended up,
and it cannot even do that, because it learns nothing at all — it only sees
the new arrangement and answers again.

This is also the clearest statement of what solution 6 has to gain, and of how
little. Continuing the training here cannot add an input slot. What it can do
is fit the model's response on pushes whose outcomes are known, so that this
bench's own friction ends up absorbed into the weights as a constant. That is
not a way of observing friction, and [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) names it as a liability away from this bench
rather than as a repair for the closed channel.

## 7. The domain gap, which is the heart of this document

Everything above assumes the borrowed model works at all on the pictures this
bench would show it, and that assumption is the one most likely to fail. It
deserves the longest section here, because the difference between what the
model was fitted on and what it would be given is large.

A **domain gap** is the difference between the data a model was fitted on and
the data it is used on. Here the two sides of that gap can be set out plainly.

**What it was fitted on is real teleoperation.** 487 community datasets of real
robots, driven by real people, in real rooms. That means real cameras, with the
noise, the blur and the colour a real lens produces. It means real lighting,
with shadows that say where an object meets the surface it stands on, and
highlights that curve the way a curved surface makes them curve. It means real
scenes, which are cluttered: a workbench with other objects on it, a background
that is a room, texture everywhere, and the particular visual mess that tells a
model what is near and what is far.

**What this bench offers is a rendered view from the top of pale blue glasses
on a tan table.** The glasses are built as stacks of cylinders and shaded as
solid objects, the table is a flat rectangle, there is nothing else in the
frame, and nothing in the picture was produced by light passing through a
lens. Every glass is the same colour, so nothing in the picture tells one kind
from another. There is no clutter, almost no texture, and nothing of the
transparency a real drinking glass has, which in a photograph is the strongest
single clue that a glass is what you are looking at.

So the model is asked about pictures quite unlike the ones it learned from,
with much of the evidence it learned to use simply absent.

**The way models fail across such a gap is the part that matters.** They do not
usually produce nonsense. Nonsense would be convenient, because nonsense is
easy to detect and easy to refuse. What they produce instead is **confident,
plausible, wrong actions**: movement that looks like a push, aimed somewhere
reasonable, at a sensible speed, that is simply not the push this table needed.
That is worse than nonsense for one specific reason — **nothing downstream
looks suspicious.** The waypoints are well formed, the jaw follows them, the
arm does not fault, the bench records a push, and the only sign that anything
went wrong is in the arrangement afterwards. There is no error to catch and no
confidence number to put a bar on.

It is worth noticing which direction those mistakes point. A push aimed at the
wrong place is recoverable, because the arm looks again and the next pass
replans from where the glasses really are. A push that topples a glass is not,
because nothing in this problem stands a glass back up. So a borrowed model
producing plausible wrong actions is not merely inaccurate; it is inaccurate in
the one way this problem cannot absorb, which is the whole reason the next
section but one takes the topple limit out of the model's hands entirely.

## 8. The honest expectation

It follows from all of the above that this solution may well do badly, and it
is better to say so here than to let a reader discover it in the scorecard.

The expectation, reasoned from what the model brings and what it is given, is
roughly this. The model should produce well-formed movement, because producing
well-formed movement is what its pretraining is for and that capability does
not depend on recognising the scene. It should sometimes produce a sensible
push, because a crowded group of upright objects on a flat table is not an
unfamiliar shape and pushing one of them apart from its neighbours is a motion
the pool it learned from certainly contained. And it should often choose the
wrong glass, or the wrong direction, or a distance unrelated to what the
arrangement needed, because choosing correctly needs the picture to be read
accurately and the picture is the part that does not match.

Against [the target layout](../01_the-problem/02_the-target-layout.md)'s yardstick that is a
specific prediction: glasses that end up far from where the push aimed them,
and a total travel that is a large multiple of the displacement floor. A method
whose glasses scatter is succeeding by looking again rather than by predicting,
and this is the solution in this book most likely to be doing exactly that.

**And that is this solution's job.** It is the baseline for the sharpest
comparison in the set, and a baseline is useful in proportion to how cleanly it
isolates one variable, not in proportion to how well it scores. Solution 6 is
the same library, the same weights and the same bench, with its training
continued on this cell's own pushes. If this solution scored well, the pair
would measure very little, because there would be little room for training to
improve anything. A poor score here is what gives that comparison its range.

## 9. The price of the model, and why this model

Before leaving the model itself, it is worth being clear about what it costs to
run, because the cost is unusually low and that is part of why it is the first
thing to try.

**The model is about 450 million parameters.** It uses a few gigabytes of
memory while answering, and it runs on a laptop. There is no accelerator to
rent to use it, no cluster, and no special hardware of any kind. Combined with
the fact that nothing is collected and nothing is trained, that makes this
**the cheapest of the learned solutions in this book to try** by a wide
margin: the whole setup cost is a download.

What it does cost is time per push, and that belongs on the scorecard. Every
decision is a forward pass through a large network, which is a different kind
of expense from solution 1's arithmetic and a different kind again from
solution 4's run-time search. The bench carries a compute column for exactly
this reason, because a solution that wins while taking a hundred times longer
has not obviously won. The honest expectation here is a cost per push far above
the hand-written solutions, and a different kind of expense from a planner that
simulates many candidate actions forward before committing.

**Why this model and not a larger one** is worth answering, because larger
robot foundation models exist and the obvious question is whether a bigger one
would close the domain gap. The alternative considered is π0, which is about
3.3 billion parameters — roughly seven times the size. The difficulty is not
running it but training it, and training it is what [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) has to do: π0's low-rank fine-tuning needs more
than 22 GB of accelerator memory, and a full fine-tune more than 70 GB. Those
floors decide the matter. A pair of solutions is only worth building if both
halves can actually be built, and **SmolVLA is chosen here because it is the
one whose fine-tuning is affordable**, which makes the 5-against-6 comparison
possible at all. π0.5 appears in this book only as a further rung inside
solution 6, reached by low-rank adaptation, to ask whether a markedly larger
model is worth it.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
