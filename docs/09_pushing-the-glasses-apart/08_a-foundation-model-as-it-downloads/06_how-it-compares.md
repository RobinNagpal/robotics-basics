# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The strengths all come from the same source, which is that nothing is fitted.

There is nothing to collect, nothing to train and nothing to keep in step with
the cell, so this solution can be tried in an afternoon. It needs no
accelerator. It gives this book a reading on what a borrowed robot model is
worth before anybody spends a week recording pushes, which is a decision
several of the other solutions depend on. It is a genuine upper bound on
convenience, because no solution here can be cheaper to set up. And it is the
clean half of this book's sharpest pair, which is the strength that does not
depend on it working at all.

The weaknesses divide into what the borrowing costs and what it cannot be asked
to do.

What the borrowing costs is accuracy and every lever for improving it. The
domain gap is large: the model learned from real cameras and cluttered rooms,
and it is shown flat pale blue shapes on an empty rectangle. What it returns
across that gap is not movement aimed at the wrong glass but movement that
never reaches the table — a median lowest point 209 mm up, where the jaw has to
be at 50 mm to move anything, and 674 pushes in 754 touching nothing. The force
reading cannot reach it, so the only channel that observes friction is closed.
The actions arrive with no units in them, so a reading stands between the model
and the jaw and a poor one would be blamed on the model. And both the
instruction and the pose are the same at every ask, so the model is an
expensive visuomotor policy here rather than the thing it was built to be.

What it cannot be asked to do is anything that needs fitting. It cannot learn
from a push that went wrong, because it does not learn. It cannot be corrected
on the kind of glass it handles worst, because correcting it is training. It
cannot have a threshold tuned, because it has no threshold. The one repair for
all of that is to continue its training on this cell's own pushes, which is a
different solution with a different name, and that is exactly why the two are
written as a pair.

The honest position is therefore that this is among the first things to run and
not the one carried forward. Its value is the comparison it makes possible
rather than the accuracy it delivers.

## 2. The general ideas behind this

Five named ideas sit under this solution, and each is worth knowing in its own
right, including where it is normally the wrong tool.

### Robot foundation models — one model pretrained for manipulation in general

A **foundation model** is one fitted on a very large and very broad pool of
data, with the intention that it be used on tasks nobody had in mind when it
was fitted. The robot version pools demonstrations from many robots and many
tasks, which is sometimes called **cross-embodiment** pretraining, because the
robots in the pool are not the same machine.
[LeRobot](https://github.com/huggingface/lerobot) carries several, among them
π0, π0.5, GR00T N1.7 and SmolVLA.

This is normally the right move when your task resembles the pool and your own
data is scarce, because you get a competent starting point for the price of a
download. It is normally wrong when your input does not look like the pool's
input, which is the case here, and wrong when the task needs a quantity the
model has no input for, which is also the case here. It is also the wrong thing
to reach for when a few lines of geometry would settle the question, which
[solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) is in
this book to demonstrate.

### Zero-shot transfer — using a model on a task it was never fitted for

A model is used **zero-shot** when it is applied with no examples of the new
task at all, relying entirely on what it learned elsewhere. It works when the
new task is genuinely a special case of the old one.

It is normally the right first move whenever a general model exists and data is
expensive, because it costs an afternoon and tells you how hard your problem
really is. It is normally wrong as a final answer when the input differs
visibly from what the model was fitted on, and the standard repair is to
continue the training on your own data, which is [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md). This book is built
to measure exactly that repair.

### Language conditioning — the sentence that selects the task

Taking an instruction in ordinary words lets one set of weights serve many
tasks, which is what the middle word of the model's name refers to.

It is right whenever the tasks are many and the boundaries between them are the
sort of thing a person can describe in a sentence, because then the sentence is
doing real work and no code has to enumerate the cases. It is wrong — or rather
simply idle — when there is one task, which is the situation here. A constant
input carries no information, so the capability is paid for and not used, and
nothing about this cell can be concluded about language conditioning in
general.

### Action chunking — predicting a run of movement rather than one step

Policies in this family emit a short run of future actions together rather than
one action at a time, which [solution
3](../06_imitation-from-demonstrations/01_what-it-is.md) explains properly,
since ACT is named for it. SmolVLA returns 50 at a time. The reason it matters
here is the contract: because these architectures produce movement in runs,
[the examiner](../02_the-examiner.md) accepts a run of waypoints directly
instead of demanding three numbers describing a push.

Predicting a run is right when the motion is a smooth committed thing, as a
push is, because it keeps the policy consistent across the motion instead of
wobbling from one step to the next. It is wrong when the situation can change
faster than the run takes to execute, because a committed run cannot react
inside itself — which is the gap that [the learned early
abort](../01_the-problem/03_pushing-without-toppling.md) exists to cover, and
it is a shared mechanism rather than anything this solution provides.

### The domain gap, and the honest reading of a failure across one

The difference between the data a model was fitted on and the data it is used
on is the single most common reason a borrowed model disappoints. The
characteristic symptom is usually confident wrong output rather than nonsense,
and this run is a reminder that it is not always: here the output is confident,
well formed as movement, and in the wrong half of the room.

The useful discipline is to say which side of the gap you intend to move before
you measure anything. Moving the model is fine-tuning, which is solution 6.
Moving the data means making the rendered pictures resemble real ones, which is
a large piece of work in its own right and is not attempted anywhere in this
book. The failure to avoid is concluding that the method is poor when what has
actually been measured is the gap, and the whole reason this document and the
next are written as a pair is to make that confusion impossible.

## 3. Where it sits among the other five

This solution sits at one end of this book's main axis, and the axis is the
useful way to see all six.

The axis is **where the numbers came from**. [Solution
1](../04_one-fixed-nudge/01_what-it-is.md) has no fitted numbers at all and no
model; it is arithmetic and it is the floor. [Solution
2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) writes the
candidates by hand and fits only the ranker, so one small component came from
this cell. [Solution 3](../06_imitation-from-demonstrations/01_what-it-is.md)
fits a whole policy on demonstrations recorded here, borrowing an architecture
but no weights. [Solution
4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) fits a model of the
table here and then searches through it at run time. This solution is the only
one whose numbers came entirely from **somewhere else**, and [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) is the same numbers
with this cell's own pushes added on top.

Read in that order, [the six
solutions](../03_the-six-solutions/01_how-the-six-compare.md) measure what each
kind of fitting buys, and this one is the borrowed extreme they are read
against. It is also, by a wide margin, the worst of the six: 56 of 251 glasses
racked and no table finished, against 195 and 33 tables for the arithmetic of
solution 1.

One of those comparisons is sharper than the rest, and it is the reason this
document and the next one should be read together. **Solution 6 is this same
model, from this same library, starting from these same downloaded weights,
with its training continued on this cell's own pushes, running on this same
examiner.** The input is held still, the output is held still, the marking is
held still, the reading that turns the model's actions into jaw waypoints is
held still, and the topple refusal runs first in both. Nothing varies between
the pair except the training. So the gap between their scores is a measurement
of what that training bought and of nothing else, and no other pair in this
book is that clean.

Measured, that gap is not a simple improvement, and it is worth stating plainly
here rather than leaving to the next document. Fine-tuning takes the glasses
racked from 56 to 77 and the tables finished from none to four. It also takes
the glasses toppled from 6 to 46 and the tables scored *wrong* from 5 to 38.
Both of those are medians over three runs, and neither solution's three runs come
anywhere near the other's: this one toppled between 5 and 8 glasses and solution
6 between 38 and 49. So
what the training bought was a model that reaches the table, and the price was
a model that reaches it hard enough to knock things over. Two qualifications
belong with the number and solution 6 makes both in full: the training there
adapts the model through a low-rank correction rather than by moving every
weight, so the gap is a lower bound on what fine-tuning could buy; and a
solution that topples glasses has failed at the thing this problem cares most
about.

That is also the closing argument for building this solution despite expecting
it to do badly. A baseline is valuable in proportion to how cleanly it isolates
one variable, and this one isolates fine-tuning exactly. If it scored well,
there would be little room left for solution 6 to show anything, and the
sharpest question these six were arranged to answer, what does fine-tuning a
foundation model buy, would have no range to be answered in. A poor score here
is therefore not a disappointing result. It is the measurement working.

← [What it needs](05_what-it-needs.md) · [The same foundation model, fine-tuned here — what it is](../09_the-same-model-fine-tuned-here/01_what-it-is.md) →
