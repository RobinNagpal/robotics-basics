# What it is

> **What it uses.** It uses the Ultralytics package, with PyTorch running on this
> machine's built-in graphics. The model is Ultralytics YOLO26-seg. It is the same
> library, model and downloaded weights as
> [solution 3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md). Here the
> model is trained further on this cell's pictures. Its list of everyday names is
> replaced by one class, "glass".
> **What it does.** It finds each glass in a survey picture from the top and
> returns one outline for each. The examiner turns each outline into a place on
> the table and a width.
> **What it costs.** Labels cost nothing here, because the examiner's id image
> gives an exact mask for each glass, as
> [what the examiner keeps to itself](../03_the-examiner/01_the-examiner.md#5-what-the-examiner-keeps-to-itself)
> explains. Training takes real time, but not much. The licence is the expensive
> part, as
> [what it costs](04_results-and-comparison.md#4-what-it-costs) explains.

> **The cell is described once, in [the cell](../01_the-cell.md).** This page
> covers only what is special to this solution.

## Contents

1. [Introduction](#1-introduction)
2. [The problem this solves](#2-the-problem-this-solves)
3. [The main idea](#3-the-main-idea)

## 1. Introduction

This chapter answers [what this book asks
for](../02_the-problem/01_what-is-asked-for.md) in a common way. It takes a model
that was trained somewhere else, and trains it further on pictures of this cell.
This is called **fine-tuning**. It is the usual way to use a borrowed model for a
particular job. It is written out in full here so that its gain can be measured.

**This solution is built and marked.** Its code is in the `robot-arm-projects`
repository, in the folder
[`v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/`](https://github.com/RobinNagpal/robot-arm-projects/tree/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned).
Every link to a code file in this chapter opens it on GitHub in a new tab. Its
scores are in
[`04-yolo-fine-tuned/README.md`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/README.md)
and in that folder's `results` files.
[Results and comparison](04_results-and-comparison.md) gives them in full.

**This solution exists to be one half of a matched pair.**
[Solution 3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md) is this
model with no training in this cell. This solution is the same model with
training in this cell. Everything else stays the same:

- The [examiner](../03_the-examiner/01_the-examiner.md) shows both the same
  pictures, in the same order.
- Both return the same record for each glass.
- The examiner marks both in the same way.
- Both use the same library, the same model and the same downloaded weights.

Only the training differs. The training brings one more change with it. The list
of everyday names becomes the single class "glass". This is part of the training,
because you cannot train a model on this cell's labels and still ask it to pick an
everyday name. So nothing differs between the two except what the training
brings.

This means **the gap between solution 3 and this one measures what fine-tuning
gains, and nothing else.** On spaced arrangements, solution 3 found 6.4 glasses in
every 100. This solution found 99.4. Few pairs of methods can be compared this
cleanly.

This chapter explains what fine-tuning is, and why it needs much less data and
time than training from random numbers. It shows which failure of solution 3 the
single class removes. It shows where the training pictures come from. It shows
which weaknesses training fixes and which it does not.

![A training step is put in front of the borrowed model: the examiner supplies an exact mask for every glass for nothing, the list of everyday categories is replaced by the single class glass, and training continues from the downloaded weights, after which the run is the borrowed model's own run.](../../images/seeing-the-glasses/the-same-model-fine-tuned/finetuned-flow-what-it-does.png)

![Training closed the gap between the pictures the model was fitted on and the pictures it is shown, and it did not change the shape of the output, so the outline is still built coarsely inside a rectangle and still marks only pixels where the camera saw the glass.](../../images/seeing-the-glasses/the-same-model-fine-tuned/finetuned-flow-what-training-changes.png)

The next section says which problem this solution is meant to fix.

## 2. The problem this solves

The introduction set up the matched pair. This section says what the training is
meant to fix.

The hard case in this book is the merge. Two glasses that stand apart can still
make one joined shape in the picture, as
[what is asked for](../02_the-problem/01_what-is-asked-for.md) explains. A model
that finds objects gives **one outline per object**, not one per joined shape. So
it can separate the two.

![One picture from the top, read two ways: a map that can only say glass or table leaves two touching glasses as a single connected shape, while a model that finds objects returns one outline per glass, each with a box of its own.](../../images/seeing-the-glasses/the-same-model-fine-tuned/09-class-map-against-instances.png)

Solution 3 already has such a model, without any training. So the question here
is narrower: **the finding is already borrowed, so what is still wrong, and does
training fix it?**

Solution 3 has a domain gap. Its model was trained on photographs, but this cell
gives grey pictures shaded from depth, as
[why it failed](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#2-why-it-failed-the-names-it-reached-for)
explains. This causes three problems:

- The model has much less of the evidence it learned to use.
- Its list of names belongs to somebody else. So it can call a glass by a name the
  filter drops, or by two names at once.
- Its confidence was learned on photographs, so it is not a probability here.

The marking shows which problem mattered. It was the names. The borrowed model
called a glass a sports ball or a frisbee, and the filter dropped almost
everything. The single class "glass" removes this failure, because the model no
longer chooses a name. Training on this cell's own pictures is the usual fix for
all three problems.

The next section shows how this solution does that.

## 3. The main idea

The section above named the problems. This section gives the fix in one sentence:
keep the borrowed weights, and train them further on this cell's pictures, with
one class instead of the general list.

Three things follow from that sentence.

**The weights do not start from nothing.** A model's weights are the numbers
inside it. Starting from random numbers would mean teaching the model everything,
even that an edge matters. The borrowed weights already know that. So training
starts from them. This is why a model this size can be trained on this machine,
which has no separate graphics card.
[What fine-tuning is](03_how-the-model-is-trained.md#1-what-fine-tuning-is)
explains which parts of the model change.

**The pictures are this cell's pictures.** Training shows the model the grey
pictures. So when it runs, it sees the same kind of picture it was trained on.
This is how fine-tuning closes the domain gap.

**The class list has one entry.** The model no longer decides which everyday
object it sees. It only finds objects. Each object it finds is a glass.

Everything else about the model stays the same. Its outline is still built
coarsely, so its masks are a little too big.
[What training closed, and what it left](04_results-and-comparison.md#2-what-training-closed-and-what-it-left)
gives the cost. The next page shows the code.

← [A borrowed model, as it downloads — results and comparison](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md) · [The code](02_the-code.md) →
