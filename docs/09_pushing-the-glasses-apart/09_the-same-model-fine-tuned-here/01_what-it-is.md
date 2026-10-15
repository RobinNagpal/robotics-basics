# What it is

> **What it uses** — LeRobot, with PyTorch underneath. The training ran on this
> Mac's own Metal GPU. The model is SmolVLA, with the same library, the same
> model and the same downloaded weights as [solution
> 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md). Here its
> training is continued by low-rank adaptation, on pushes made on the
> examiner's tables.
> **What it does** — it keeps the borrowed model's numbers and learns a small
> correction to them. The correction comes from pushes made on this examiner.
> So the model stops being a general copier of robot motion and becomes a
> pusher of glasses on this table.
> **How the output is produced** — a view of the table from the top goes in,
> with one instruction in plain English and the arm's own pose. The pose is
> the same every time, because the jaw is parked between actions. The model
> returns an **action chunk**, which is a short run of jaw waypoints predicted
> together in one pass. The shared geometry refuses the glasses that tip
> before they slide. A chunk whose path would reach one of those is not
> carried out. The examiner carries the waypoints out directly. Then the arm
> looks again, and the loop repeats until the table is done or the push budget
> is spent.
> **What it costs** — the demonstrations are free, because solution 2 makes
> them and no person holds a controller. The training fits in 1.02 GiB on a
> laptop, so nothing was rented. Running it costs the same as running solution
> 5. The licence is not the obstacle it was for [the pair that tells the
> glasses
> apart](../../08_seeing-the-glasses/08_the-same-model-fine-tuned/04_results-and-comparison.md#4-what-it-costs).
> But a fine-tuned file keeps the terms of the file it came from, so read
> those terms before anything leaves this project.

> **The cell is described once, in [the cell](../../08_seeing-the-glasses/01_the-cell.md)** — the
> layout, the two places the camera works from, from the top and from the
> side, all four sensors, and the words this project uses them with. What
> follows is only what is specific to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [A film of one table](#2-a-film-of-one-table)
3. [The problem this solves](#3-the-problem-this-solves)
4. [The main idea](#4-the-main-idea)

## 1. Introduction

This page explains how this solution answers [the problem this book
sets](../01_the-problem/01_what-is-asked-for.md). It takes a robot foundation
model that was trained somewhere else. Then it continues that training on
pushes made in this cell. This is called **fine-tuning**. It is the ordinary
way to put a borrowed model to work on one job.

**This solution is one half of a matched pair.** [Solution
5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) is the same
model with no training in this cell. This solution is the same model with
training here. Everything else is held still, so the gap between the two
scores measures what the training bought.
[Solution 5's comparison](../08_a-foundation-model-as-it-downloads/06_how-it-compares.md#3-where-it-sits-among-the-others)
explains why this is the cleanest pair in the book. [Whether anything but the
training differs](03_how-it-works.md#4-whether-anything-but-the-training-differs)
checks the few places where something else might.

The book on [telling the glasses apart in a
picture](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
asked the same question about a model that finds objects in pictures. Here the
model does more. It decides what the arm does next. A model can find every
glass in a picture and still choose bad pushes. This is because choosing a
push needs a sense of what a push does, and a picture does not show that.

**Most of this solution is built.** The code is in
[`06-smolvla-fine-tuned/`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned).
It records demonstrations from the teacher, fits the correction, and has been
run on the examiner's held-out tables. Its numbers are in
[its own README](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/README.md).
**DAgger** is still a plan and not code. The first result came from one
training seed on one set of tables. The model was later fitted again on
solution 3's tables, with three seeds. [How it
compares](06_how-it-compares.md#4-more-demonstrations-and-a-result-that-did-not-come-back)
shows that this changed nothing.

**The measured result is a bad one, so it is stated here at the start: the
training made the score worse.** The model learned the height at which a push
happens. Its chunks now come down to the height the gripper pushes at. But it
did not learn where to put the jaw down. So many pushes come down onto a glass
instead of behind it, and many glasses fall over. [How it
compares](06_how-it-compares.md#3-where-it-sits-among-the-others) gives
the numbers and reads them in full.

By the end you will know what fine-tuning is, and what low-rank adaptation
gives up to fit in memory. You will know where the demonstrations come from,
and which of solution 5's weaknesses the training repairs.

![The same chain as the borrowed model with a training step put in front: the teacher records its pushes, the failures are dropped, and a small correction is fitted so the chunks come out in this cell's own range, after which the shared geometry still refuses the glasses that tip before they slide.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-what-it-does.png)

![The borrowed weights stay as they are and a correction of about four million numbers is learned beside them, so only the correction carries gradients and the training fits on a laptop, and afterwards the correction folds into the weights so running it costs what running the original cost.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/smolvla-finetuned-flow-the-correction.png)

The next section shows the trained model at work on one table.

## 2. A film of one table

The introduction said what the training changed. The film below shows the
trained model on one table in the simulator, at one and a half times real
speed.

[The same borrowed model after fine-tuning here, on one table, 12 seconds and no sound](https://docs.dodao.io/videos/pushing-the-glasses-apart/06-smolvla-fine-tuned.mp4 "video")

The table holds six glasses, where the average is five. Five of them have no
room at the start.

In the film the jaw comes down to the right height. The training fixed that.
But the jaw comes down **onto** a glass. The training did not fix that. The arm
makes four pushes. One glass is racked and one is knocked over, so the table is
marked **wrong**. This is the most common outcome for this solution.

A glass on its side cannot be stood up again. So reaching the glasses in the
wrong place is worse than not reaching them at all. Solution 5's model never
touches anything. The training made it touch things, and that made it
dangerous.

The model draws its answer at random, so the film shows one draw. The scored
runs on this table all ended wrong, with six pushes and two glasses racked on
average. [The
examiner](../01_the-problem/03_the-examiner.md#6-two-things-this-scorecard-needs-that-the-camera-works-did-not)
explains why a filmed table can differ from the same table in a scored run.

The six measured solutions are filmed on this same table. [The six
films](../11_the-results.md#3-the-six-films-all-of-the-same-table) puts them
side by side.

The film shows what happened. The next section says which problem this
solution was built to solve.

## 3. The problem this solves

The film showed the trained model at work. This section says what it was meant
to fix.

The book asks for jaw trajectories until every glass has about 76 mm of clear
room. A glass that cannot get room must be refused with a reason. [The
problem](../01_the-problem/01_what-is-asked-for.md) explains why this is hard.
The hardest part is friction. Friction decides whether a glass slides or tips.
Nothing in the cell measures it, and the examiner never tells it.

A learned policy deals with this by seeing many pushes and what they did. It
ends up with a sense of what a push does on this table, friction included.
Solution 5 already borrows a model trained in this way, on a very large set of
real robot motion.

So the question here is narrow. **Having borrowed a policy, what is still
wrong with it, and does training here fix that?**

Solution 5's problems have one cause. Its model was trained on real robots in
real rooms. This cell shows it a rendered picture of a simulated table, which
looks nothing like that. This difference is called the **domain gap**. [Solution
5](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
explains it in full. Continuing the training on pushes made here is the
standard repair.

The next section gives the main idea of that repair.

## 4. The main idea

The problem is the domain gap. The idea for closing it is short. Keep the
borrowed numbers, and learn a small correction to them from pushes made on the
examiner's tables.

Three things follow from this idea.

**The numbers do not start from nothing.** A model's weights are the numbers
inside it. SmolVLA has about 450 million of them. They already know general
things, for example that a motion should be smooth. So the training starts
from them.

**The pushes are this examiner's pushes.** The model is trained on this
examiner's pictures and pushes. So at run time it sees the same kind of input
it was trained on. This is how fine-tuning closes the domain gap.

**Only a small part of the model changes.** The training leaves every borrowed
number as it is. It learns a small correction that is added beside them. This
is called **low-rank adaptation**. It makes the training cheap, but it also
limits how far the model can change.

Everything else about the model stays the same, including its limits. The
instruction is still the same sentence every time, so it carries nothing, as
[solution 5
explains](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#5-two-of-the-three-inputs-say-the-same-thing-every-time).
The model still commits to a whole chunk of fifty waypoints before it looks
again. And it still cannot refuse a glass.

[How it works](03_how-it-works.md) takes each of these parts in turn.

← [A foundation model as it downloads — questions and answers](../08_a-foundation-model-as-it-downloads/07_questions-and-answers.md) · [The code](02_the-code.md) →
