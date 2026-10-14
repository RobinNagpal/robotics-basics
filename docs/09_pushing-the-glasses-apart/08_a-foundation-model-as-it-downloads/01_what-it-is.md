# What it is

> **What it uses.** It uses [LeRobot](https://github.com/huggingface/lerobot),
> a library of robot learning code built on PyTorch. It also uses one borrowed
> model, **SmolVLA**, exactly as it downloads. No number in the model is
> fitted in this cell.
> **What it does.** It shows the model a top-down picture of the table, one
> fixed sentence, and the jaw's pose. It then carries out the waypoints the
> model returns. Then it looks again and asks again. This repeats until every
> glass has room or the push budget is spent.
> **How the output is produced.** The model returns 50 actions. These are read
> as waypoints for the jaw. The examiner moves the jaw along them directly,
> without its push macro.
> **What it costs.** It needs no demonstrations, no labels and no training. It
> needs the library, a 2.9 GB download and a laptop. The remaining cost is time,
> because every push needs a pass through a large network.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md).**
> That page covers the layout, the two camera positions, the four sensors, and
> the words this project uses for them. This page covers only what is specific
> to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [A film of one table](#2-a-film-of-one-table)
3. [The problem this solves](#3-the-problem-this-solves)
4. [The main idea](#4-the-main-idea)

## 1. Introduction

This chapter answers [the problem this book
sets](../01_the-problem/01_what-is-asked-for.md) in the simplest possible way.
It downloads a general robot model and runs it. Nothing is collected, trained
or fitted in this cell. The model is shown the table, told in words what to do,
and asked for actions. Whatever it returns is carried out.

**This solution is built and has run.** The code is in
[`05-smolvla-as-it-downloads/`](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads).
It runs on the same 50 held-out tables as the other five solutions. It did
badly, and in an unexpected way: most of its pushes pass high above the glasses
and touch nothing. [How it
works](03_how-it-works.md#8-what-was-expected-and-what-happened) gives the
measured details.

There are two reasons to build it. First, it is the cheapest solution in this
book to try, because the whole setup is a download. Second, it is the starting
point of the cleanest comparison in the book. [Solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) is this same model
with more training done here. So the gap between the two measures what that
training gave, and nothing else. This means the score of this solution matters
less than the comparison it makes possible.

This page says what kind of model this is, what goes in and what comes out. The
pages after it explain where the model's skill comes from, what it cannot use,
and why a poor result here is still useful.

![The view from the top, one instruction in plain English and the arm's joint readings go into the downloaded model, which returns a run of actions that are read as waypoints and carried out, with no training step, no data collection and no fitted parameter anywhere in the chain.](../../images/pushing-the-glasses-apart/a-foundation-model-as-it-downloads/smolvla-flow-what-it-does.png)

The introduction said what this solution is. The next section shows it at work
on one table.

## 2. A film of one table

The introduction described the borrowed model. This film shows it on one table
in the simulator, at one and a half times real speed.

[A large borrowed model used exactly as it downloads, on one table, 74 seconds and no sound](https://docs.dodao.io/videos/pushing-the-glasses-apart/05-smolvla-as-it-downloads.mp4 "video")

The table holds six glasses, where the average is five. Five of them have no
room at the start.

In the film, the jaw sweeps across the table sixteen times. It never reaches a
glass, because the model's answers stay high above the table. One glass is
racked, and only because it already had room. This is the longest of the six
films and the emptiest. That is the real result, not a fault in the recording.

The model draws a fresh answer each time, so the film is one draw, not an
average. The scored runs on this table racked one glass each and made thirteen
pushes on average. So the film is a little busier than a typical run.

All six solutions are filmed on this same table. [The six
films](../10_the-results.md#3-the-six-films-all-of-the-same-table) collects
them and says how the table was chosen.

The film shows a capable model acting in the wrong place. The next section says
which problem an unchanged model is meant to answer.

## 3. The problem this solves

The film showed what the model does. This section says why anyone would try an
unchanged model at all.

[The problem](../01_the-problem/01_what-is-asked-for.md) asks for jaw
movements, one after another, until every glass has about 76 mm of clear room
and nothing has fallen over. This is hard because a push does not go where it
was aimed. [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) explains why.

Every other solution in this book builds something for this. Solution 1 builds
a rule. Solution 2 builds geometry and a ranker. Solution 3 learns a policy from
recorded pushes. Solution 4 learns a model of the table and searches through it.
Each of these costs work, and three of them need data collected in this cell.

This solution does something else. Pushing objects on a table is not special to
this project. Many people have recorded robots doing this kind of thing. Someone
has already trained one model on a huge pool of those recordings. So this
solution borrows a model made for tables in general. It asks if that is good
enough for this table. The answer is worth knowing before anyone spends a week
recording demonstrations.

The question is now clear. The next section gives the idea that answers it.

## 4. The main idea

The last section said this solution borrows instead of builds. This section
gives the three steps that make up the whole idea.

**First, download the model and show it the table from the top.** [The test
examiner](../01_the-problem/02_what-goes-in-and-what-comes-out.md#3-what-look-hands-over)
draws this picture so that solutions that read pictures get the same
information as solutions that read numbers. A fixed camera 750 mm above the
glass zone looks straight down. It gives a colour picture of 384 by 384 pixels.

**Second, tell it in words what to do, and give it a pose.** The instruction is
the same every time: *the glasses are too close together, push them apart*.
The pose goes in the slot the model keeps for an arm's joint readings. This
cell puts the jaw's position there, because the model was trained on a
different arm. This cell's joint angles would mean nothing to it. This small
change turns out to matter a lot. [How it
works](03_how-it-works.md#5-two-of-the-three-inputs-say-the-same-thing-every-time)
explains why.

**Third, carry out what comes back.** The model returns 50 actions. Read as
waypoints for the jaw, they are already the output the examiner accepts. The
examiner moves the jaw along them, and the table changes. The model is then
asked again about the new table.

So this solution has no fitted numbers, no hand-written geometry and no search.
It has a download, a sentence and a loop. **Keep this in mind on the pages that
follow**, because almost every strength and weakness comes from it.

← [A world model, then plan with it — how it compares](../07_a-world-model-then-plan-with-it/06_how-it-compares.md) · [How it works](03_how-it-works.md) →
