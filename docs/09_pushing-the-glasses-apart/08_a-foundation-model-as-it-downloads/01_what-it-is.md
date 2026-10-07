# What it is

> **What it uses** — [LeRobot](https://github.com/huggingface/lerobot), the
> library that holds reference implementations of every learned policy in this
> book, with PyTorch underneath it, and one borrowed model taken exactly as it
> downloads. That model is **SmolVLA**, about 450 million parameters, which
> uses a few gigabytes while answering and runs on a laptop. Not one number in
> it is fitted in this cell.
> **What it does** — it shows the borrowed model the rendered view of the
> table from the top, hands it one instruction written in plain English, hands
> it the jaw's own pose in the slot the model keeps for an arm's joint
> readings, and carries out the waypoints it returns. Then it looks at the
> table again and asks once more, until every glass has its room or the push
> budget is spent. There is no training step, no data collection and no fitted
> parameter anywhere in the design.
> **How the output is produced** — the picture, the sentence and the pose go
> into the model; the model returns a run of 50 actions; those actions are read
> as waypoints for the jaw and handed to the examiner, which carries them out
> directly rather than through the push macro it owns. So the chain is short:
> picture and words in, waypoints out, table changed, look again.
> **What it costs** — no demonstrations, no labels, no training run and no
> weights file to keep in step with the cell. It needs the library, the 2.9 GB
> the library downloads, and a laptop. The expense that remains is time per
> push, because every decision is a forward pass through a large network rather
> than arithmetic: about a second each, measured, against 0.06 s for the
> arithmetic of [solution 1](../04_one-fixed-nudge/01_what-it-is.md).

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This document describes how [the problem this book
sets](../01_the-problem/01_what-is-asked-for.md) is answered by downloading a
general-purpose robot model and running it, with nothing collected, nothing
trained and nothing fitted in this cell at all. The model is shown the table
from the top, told in words what to do, and asked for actions. Whatever it
returns is carried out.

**This solution is built and has run.** It lives in
[`05-smolvla-as-it-downloads/`](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads),
it downloads the weights and makes the pushes on the same 50 held-out tables as
the other five, and
[its README](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads/README.md)
carries the numbers. It did badly, which was expected, and it did badly in a
way nobody here expected: of the 754 pushes it made in a run, about nine in ten
never touched a glass at all, because the trajectories it returns stay roughly
200 mm above the table. The pages that follow report that rather than the
failure the design argued for.

The design is worth writing down for two separate reasons, and it is worth
separating them at the start because they pull in opposite directions. The
first is that it is the cheapest thing in this book to try. There is nothing to
collect and nothing to train, so the whole setup cost is a download. The second
is that it was very likely to do badly. Those two facts are not in tension,
because this solution's value is not its score. Its value is that it is the
starting point of the sharpest comparison in the set: [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) is this same model with its training continued
here, so the gap between the two measures what that training bought and
measures nothing else.

By the end of this document you will understand what kind of model this is,
what goes into it and what comes out, where its competence comes from and why
that competence is general rather than local, and exactly what is borrowed and
exactly what is not. The pages after it say why the difference between the
pictures the model learned from and the pictures this examiner shows it is the
central risk, why two of the model's three inputs carry no information in this
problem, why the one channel that observes friction cannot reach it, and why a
poor result here is still the most useful thing in this book.

![The view from the top, one instruction in plain English and the arm's joint readings go into the downloaded model, which returns a run of actions that are read as waypoints and carried out, with no training step, no data collection and no fitted parameter anywhere in the chain.](../../images/pushing-the-glasses-apart/a-foundation-model-as-it-downloads/smolvla-flow-what-it-does.png)

## 2. The problem this solves

[The problem](../01_the-problem/01_what-is-asked-for.md) asks for a jaw trajectory, and then another, until
every glass on the table has about 70 mm of clear room in every direction and
nothing has been knocked over. Choosing those trajectories is hard because a
push does not go where it was aimed, for the reasons [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) sets out in full.

Every other solution in this book responds to that by building something.
Solution 1 builds a rule, solution 2 builds geometry and a ranker, solution 3
builds a policy from recorded pushes, and solution 4 builds a model of the
table and searches through it. Each of those costs work, and three of the four
cost data collected in this cell.

This solution responds differently. It observes that pushing an object across a
flat surface with a gripper is not a task peculiar to this project, that very
many people have recorded robots doing exactly that sort of thing, and that
somebody has already fitted a single model on an enormous pool of those
recordings. So instead of building a method for this table, it borrows a method
for tables in general and asks whether the general thing is good enough for the
particular one. That is a real question with a real answer, and the answer is
worth knowing before anybody spends a week recording demonstrations.

## 3. The main idea

The idea is three steps, and there is nothing else in it.

**First, download the model and show it the table from the top.** The input is
a picture of the table looking straight down, which [the test
examiner](../02_the-examiner.md) renders so that the solutions which read
pictures get the same information as the solutions which read numbers. A fixed
camera 750 mm above the middle of the glass zone, looking straight down, gives
384 by 384 pixels of red, green and blue, the same frame on every table.

**Second, tell it in words what to do, and hand it a pose.** The instruction is
one line of plain English, the same line every time: *the glasses are too close
together, push them apart*. The pose goes in the slot the model keeps for an
arm's joint readings. What this cell puts there is where the jaw is standing,
because the model was fitted on a different arm and this cell's joint angles
would mean nothing to it. That substitution looks small here and turns out to
matter a great deal, which [how it works](03_how-it-works.md#5-two-of-the-three-inputs-say-the-same-thing-every-time) explains.

**Third, carry out what comes back.** The model returns 50 actions. Read as
waypoints for the jaw, those actions are already the shared output the contract
asks for, so they go straight to the examiner. The examiner moves the jaw along
them, the table changes, fresh measurements are taken, and the model is asked
again from the new arrangement.

So this solution contains no fitted numbers, no hand-written geometry and no
search. It contains a download, an instruction and a loop. **That is the point
to hold on to while reading the rest**, because almost every strength and every
weakness below follows from it directly.

← [A world model, then plan with it — how it compares](../07_a-world-model-then-plan-with-it/06_how-it-compares.md) · [How it works](03_how-it-works.md) →
