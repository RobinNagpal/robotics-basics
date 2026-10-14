# How it compares

This page judges this solution. It says where the solution is strong and where
it breaks. It names the general ideas behind it. Then it places it beside the
other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

All of the strengths come from one fact: nothing is fitted.

There is nothing to collect, nothing to train and nothing to keep up to date.
So this solution can be tried in an afternoon, without an accelerator. It tells
you what a borrowed robot model is worth before anyone spends a week recording
pushes. No solution here is cheaper to set up. And it is the clean half of this
book's best-matched pair, which is useful even though it scores badly.

The weaknesses come in two kinds.

The first kind is what borrowing costs. [How it
works](03_how-it-works.md) explains each of these in full:

- The [domain gap](03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
  is large, and most answers [never reach the
  glasses](03_how-it-works.md#8-what-was-expected-and-what-happened).
- The model has [no input for
  force](03_how-it-works.md#6-the-force-reading-has-nowhere-to-go), so it never
  sees the only evidence of friction.
- The actions [have no
  units](03_how-it-works.md#4-the-actions-arrive-with-no-units-in-them), so a
  chosen scale stands between the model and the jaw.
- The sentence and the pose [never
  change](03_how-it-works.md#5-two-of-the-three-inputs-say-the-same-thing-every-time).

The second kind is what it cannot do, because it does not learn. It cannot learn
from a bad push. It cannot be corrected on the glass it handles worst. It has no
threshold to tune. The one fix for all of this is more training on this cell's
own pushes. That is a different solution, and that is why the two are written as
a pair.

So this is one of the first things to run, but not the one to keep. Its value is
the comparison it allows, not its accuracy.

Those are the strengths and weaknesses. The next section names the general ideas
they come from.

## 2. The general ideas behind this

The last section judged this solution on its own. This section names five
general ideas behind it, and says when each one is usually the wrong tool.

### Robot foundation models — one model pretrained for manipulation in general

A **foundation model** is trained on a very large and broad set of data. It is
meant to be used on tasks nobody planned for. The robot version uses
demonstrations from many robots and many tasks. This is called
**cross-embodiment** pretraining, because the robots in the data are different
machines. [LeRobot](https://github.com/huggingface/lerobot) includes several,
such as π0, π0.5, GR00T N1.7 and SmolVLA.

It is usually the right choice when your task looks like the training data and
your own data is scarce. Then a download gives you a good starting point. It is
usually wrong when your input looks different from the training data. It is
also wrong when the task needs a value the model has no input for. Both are true
here. And it is the wrong tool when a few lines of geometry would do. [Solution
2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) shows that case.

### Zero-shot transfer — using a model on a task it was never fitted for

A model is used **zero-shot** when it gets no examples of the new task at all.
It relies only on what it learned elsewhere. This works when the new task is
really a special case of the old ones.

It is usually the right first step when a general model exists and data is
costly. It takes an afternoon and shows how hard your problem really is. It is
usually wrong as a final answer when your input looks different from the
training data. The usual fix is more training on your own data. That is
[solution 6](../09_the-same-model-fine-tuned-here/01_what-it-is.md), and this
book is built to measure that fix.

### Language conditioning — the sentence that selects the task

A model that takes an instruction in words can do many tasks with one set of
weights. The sentence says which task to do.

This is useful when there are many tasks and a person can describe each one in
a sentence. It does nothing when there is only one task, as here. [How it
works](03_how-it-works.md#5-two-of-the-three-inputs-say-the-same-thing-every-time)
explains why. So this cell tells us nothing about language conditioning in
general.

### Action chunking — predicting a run of movement rather than one step

Models of this kind give a short run of future actions at once, not one action
at a time. [Solution
3](../06_imitation-from-demonstrations/01_what-it-is.md) explains this in full.
SmolVLA gives 50 at a time. Because models like this give movement in runs,
[the examiner](../01_the-problem/03_the-examiner.md) accepts a run of waypoints
directly.

A run is right when the motion is smooth and steady, as a push is. It keeps the
motion consistent from step to step. It is wrong when the scene can change
faster than the run takes, because a run cannot react inside itself. [The early
abort](../01_the-problem/05_pushing-without-toppling.md) covers that gap. It is
shared by all six solutions, not part of this one.

### The domain gap, and the honest reading of a failure across one

[How it
works](03_how-it-works.md#7-the-domain-gap-which-is-the-heart-of-this-document)
explains the domain gap and how this model failed across it.

The useful habit is to decide which side of the gap you will move before you
measure. Moving the model means more training, which is solution 6. Moving the
data means making the drawn pictures look real. That is a large job, and this
book does not try it. The mistake to avoid is to blame the method when you have
really measured the gap. This chapter and the next are written as a pair to
prevent that mistake.

These are the ideas behind the solution. The last section places it among the
other five.

## 3. Where it sits among the other five

The last section named the ideas. This section places the solution on the one
line that best sorts all six.

That line is **where the numbers came from**. [Solution
1](../04_one-fixed-nudge/01_what-it-is.md) has no fitted numbers and no model.
It is arithmetic, and it is the floor. [Solution
2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) writes its
candidates by hand and fits only the ranker. [Solution
3](../06_imitation-from-demonstrations/01_what-it-is.md) fits a whole policy on
demonstrations recorded here. It borrows a design but no weights. [Solution
4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) fits a model of the
table here and searches through it. This solution is the only one whose numbers
all came from **somewhere else**. [Solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md) is the same numbers
with this cell's own pushes added on top.

Read in that order, [the six
solutions](../03_the-six-solutions/01_how-the-six-compare.md) show what each
kind of fitting gives. This one is the borrowed end of the line, and it racks
the fewest glasses of the six. It racked 48 of 251 glasses and finished 1 table. The
arithmetic of solution 1 racked 107 and finished 14 tables. **The 48 it racked
are exactly the 48 glasses that had room before anything was pushed.** Racking
a glass gives its neighbours more room. So a solution that freed any glass would
rack more than 48. This one frees none.

One comparison is sharper than the rest, so read this chapter and the next
together. **Solution 6 is this same model, with the same weights and the same
examiner.** It only adds more training on this cell's own pushes. The input, the output, the marking, the scale and the topple rule are
all the same. Only the training changes. So the gap between their scores
measures what the training gave, and nothing else. No other pair in this book is
that clean.

The gap is not a simple improvement. Training raises the glasses racked from 48
to 56. It also raises the glasses toppled from 12 to 40, and the tables marked
*wrong* from 9 to 36. These are medians over three runs. So training gave a
model that reaches the table, but it hits the glasses hard enough to knock them
over. [Solution 6's comparison
page](../09_the-same-model-fine-tuned-here/06_how-it-compares.md) explains
this result in full.

This is also why the solution was worth building, even though it was expected
to do badly. A baseline is useful when it isolates one change cleanly. This one
isolates fine-tuning exactly. If it had scored well, solution 6 would have little
room to show anything. So a poor score here is not a disappointment. It is the
measurement working.

← [What it needs](05_what-it-needs.md) · [The same foundation model, fine-tuned here — what it is](../09_the-same-model-fine-tuned-here/01_what-it-is.md) →
