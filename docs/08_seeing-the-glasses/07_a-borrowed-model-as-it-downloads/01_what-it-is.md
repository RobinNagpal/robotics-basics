# What it is

> **What it uses** — Ultralytics YOLO26-seg at the small end of the family,
> exactly as it downloads, run through PyTorch on this machine's integrated
> graphics. The weights fetch themselves the first time the model is used.
> **What it does** — it shows the model a survey picture from the top, takes the
> list of objects the model reports, and keeps the outlines whose name is a
> drinking vessel. The names are then thrown away.
> **What is fitted here** — nothing. The model gives every outline a confidence
> score between 0 and 1, and this solution throws away any outline that scores
> below 0.25. So an outline counts as a glass only when its name is a drinking
> vessel **and** its score is at least 0.25. The 0.25 was chosen by hand, not
> fitted, and [the main idea](#2-the-main-idea) says where it is used.
> Solution 4 uses the same 0.25, so the comparison between the two is unaffected
> by it.
> **What it costs** — no labels, no training run, no weights file to keep in step
> with the cell, and no graphics card of its own. The whole cost is the licence,
> which [what it needs](05_what-it-needs.md) sets out.

> **The cell is described once, in [the cell](../01_the-cell.md)** — the layout,
> the two places the camera works from, all four sensors, and the words this
> project uses them with. What follows is only what is specific to this solution.

## Contents

1. [What it is, and what it scored](#1-what-it-is-and-what-it-scored)
2. [The main idea](#2-the-main-idea)

---

## 1. What it is, and what it scored

This solution answers [what this book asks
for](../02_the-problem/01_what-is-asked-for.md) by downloading a model and
running it. It collects no labels and trains nothing.

**It found 6.4 glasses in every 100 put out where the glasses stand apart, and
2.1 where they crowd. Both are the worst scores in the book by a wide margin.**
Those numbers are not a disappointment; they are the measurement this solution
was built to take. [How it compares](06_how-it-compares.md) sets them against the
other five.

The design is worth writing down because of what it does not contain. Every other
solution that uses a model pays something before it can answer: a set of labelled
pictures, a training run, and a weights file that has to be refitted whenever the
cell changes. This one pays none of that. The model it borrows was already fitted
on photographs of everyday scenes, and the list of things that model can name
already contains drinking vessels, so it answers on the first picture having never
seen this cell.

That makes it the cheapest of the six to try, and it makes it the baseline for the
sharpest comparison in the set: [the same model, fine-tuned](../08_the-same-model-fine-tuned/01_what-it-is.md)
takes these weights and continues training them on this cell's pictures. The gap
between the two is a clean measurement of what it costs to use a model on data it
was not fitted on.

![The grey picture goes to the downloaded model unchanged, the model returns a box, a name, a confidence number and an outline per object it believes it found, the outlines named as drinking vessels are kept and the names discarded, and not one number in the chain came from this project's data.](../../images/seeing-the-glasses/a-borrowed-model-as-it-downloads/borrowed-flow-what-it-does.png)

---

## 2. The main idea

The idea has three steps, and only the first two belong to this solution.

**First, run the borrowed model on the survey picture from the top.** It is an
**instance segmentation model**, which means that for every object it believes it
has found it returns four things together: a box around the object, a name from a
fixed list of categories, a number saying how sure it is, and an outline marking
which pixels inside the box belong to that object rather than to a neighbour.

That last property is the reason to try such a model here. The hard part of this
problem is deciding how many glasses are present when their shapes join in the
picture, and a model of this kind returns one outline per object rather than one
per joined shape. A model fitted on crowded photographs has met that situation
many thousands of times.

**Second, keep the outlines whose name is a drinking vessel**, and drop
everything else the model named. This step is where the solution fails, and
[how it works](03_how-it-works.md) is where the measurement of that failure sits.

The same step applies the bar on confidence. Each outline comes with a score
between 0 and 1 that says how sure the model is about it. An outline is kept
only when two things are both true: its name is on the list of drinking vessels,
and its score is 0.25 or more. An outline named "cup" with a score of 0.6 is
kept. An outline named "cup" with a score of 0.1 is dropped, and so is an outline
named "frisbee" with any score.

The bar is used twice in the code, which [the code](02_the-code.md) shows. The
model is told the bar when it runs, so it does not spend time building outlines
below it. The filter then checks the bar again, so the decision belongs to this
solution and can be tested.

The value 0.25 was not fitted. It is the value Ultralytics itself uses by
default, and it was checked by eye on the training half of the arrangements to
make sure it was not obviously wrong. The score is only useful for its order
here: the model learned its scores on photographs, so on these pictures a score
of 0.6 does not mean the outline is right 60 times in 100. The bar is therefore a
setting chosen by hand, and nobody should read it as a probability.

**Third, hand the kept outlines to the shared arithmetic.** Turning a set of
pixels into a place on the table and a width is a job [the
examiner](../03_the-examiner/01_the-examiner.md) does, the same way, for every
solution that produces masks. Nothing about that step changes here.

So the whole of this solution is the first two steps, and the second is a filter
on a list of names rather than anything fitted. **This solution contains no
numbers fitted in this cell at all.**

← [A network trained here from scratch — how it compares](../06_a-network-trained-from-scratch/06_how-it-compares.md) · [The code](02_the-code.md) →
