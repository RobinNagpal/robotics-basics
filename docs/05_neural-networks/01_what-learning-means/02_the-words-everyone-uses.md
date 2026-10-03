# The words everyone uses

The page before this one,
[why not just write the rules](01_why-not-just-write-the-rules.md), fitted a
straight line to six measurements of how far a robot arm's tool tip drops under a
load, and named the parts of that job: input, output, feature, label, example,
dataset, prediction and fitting. This page carries straight on from there and
names everything else, because once the numbers inside a program are chosen by a
search rather than by a person, a whole vocabulary comes with them.

The words here are model, parameter, weight, training, inference, generalisation,
supervised learning, self-supervised learning, reinforcement learning, artificial
intelligence, machine learning, deep learning and foundation model. Every later
page of this book uses them without explaining them again, so this is the page
they all point back to. They are grouped by what they describe rather than listed
in alphabetical order, because the groups are the point: three of them describe
the thing itself, two describe what you do with it, three describe where the
right answers come from, and four are the names people give to the whole field.

The page is for a reader who has finished the page before it and still knows
nothing else about machine learning. The only maths is multiplying, adding and
reading a graph. Every number and every picture comes from
[`docs/diagrams/what_learning_means.py`](../../diagrams/what_learning_means.py),
and the two jobs the examples use are the wrist-sag job from the page before and
a job of telling a full cup from an empty one, using 1,600 simulated cups
described by three measured numbers each.

## Contents

1. [The model and the numbers inside it](#1-the-model-and-the-numbers-inside-it)
2. [Training and inference, the two things you do with a model](#2-training-and-inference-the-two-things-you-do-with-a-model)
3. [The dataset, and what generalisation means](#3-the-dataset-and-what-generalisation-means)
4. [Three ways a model is told what is right](#4-three-ways-a-model-is-told-what-is-right)
5. [Artificial intelligence, machine learning, deep learning and foundation models](#5-artificial-intelligence-machine-learning-deep-learning-and-foundation-models)
6. [Every word on one job from start to finish](#6-every-word-on-one-job-from-start-to-finish)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. The model and the numbers inside it

The page before fitted the formula sag = 1.4 x mass + 0.5, and that formula has a
name. A **model** is a formula with adjustable numbers inside it, together with
the particular values those numbers have been given. So the shape of the formula
is fixed by whoever built it, and the numbers in it are what fitting chose.

Each adjustable number is a **parameter**, and the sag model has two of them. The
picture below is the same model three times over, with nothing changed but its two
parameters.

![Three copies of the same six points of mass against drop, with the line set to slope 2.0 and offset -1.0, slope 1.0 and offset 0.0, and slope 1.4 and offset 0.5](../../images/what-learning-means/the-words-everyone-uses/two-numbers-inside.svg)

With slope 2.0 and offset -1.0 the typical miss is 0.934 mm, with slope 1.0 and offset 0.0 it is 1.079 mm, and with slope 1.4 and offset 0.5 it is 0.216 mm.

That is the whole idea of a model. The formula stays put, the parameters move, and
good parameters are the difference between a useless answer and a useful one. The
number of parameters is the main thing that separates the sag model from the
models later in this book.

![A bar chart on a log scale of the parameter count of a fitted line, a tiny three-layer network, a network reading a 64 by 64 picture, and a stack of 48 blocks each 2,048 wide](../../images/what-learning-means/the-words-everyone-uses/parameter-count.svg)

A fitted line has 2 parameters, a tiny network taking 3 inputs through 8 neurons to 1 output has 41, a network reading a 64 by 64 grey picture through two layers of 256 has 1,114,881, and a stack of 48 blocks each 2,048 wide has 2,415,919,104.

Those four counts were all worked out from the shapes of the layers, which
[the shape of the numbers](../02_inside-a-network/03_the-shape-of-the-numbers.md)
explains. The point here is only that every one of those four is a model in
exactly the sense defined above, and that nothing changes about the idea between
2 parameters and two and a half billion.

A **weight** is a parameter that multiplies one of the inputs, and its size says
how much that input counts towards the answer. The sag model's slope is a weight,
because it multiplies the mass. The cup model used throughout this page has three
weights, one for each measured number.

![A horizontal bar chart of the three weights the cup model was given, with the brightness inside the rim at -7.50, the spread at +3.08 and the brightness of the cup wall at +6.41](../../images/what-learning-means/the-words-everyone-uses/weights-are-the-dials.svg)

Training gave the brightness inside the rim a weight of -7.50, the spread of that brightness +3.08 and the brightness of the cup wall +6.41, so the first and third work against each other.

Nobody told the model to subtract the wall brightness from the inside brightness,
and the page before showed that a person had to think for an afternoon to find
that trick. The first and third weights came out with opposite signs and almost
the same size, which is that subtraction, found by searching. The model's fourth
parameter is not a weight, because it multiplies nothing and is simply added at
the end, and [one neuron](../02_inside-a-network/01_one-neuron.md) calls that one
the bias.

A parameter count is also a file size, because every parameter has to be stored.

![A grouped bar chart of the storage each of the four models needs at four bytes, two bytes and one byte per parameter](../../images/what-learning-means/the-words-everyone-uses/model-file-size.svg)

At four bytes each the fitted line takes 8 bytes, the tiny network 164 bytes, the picture network 4.3 MB and the 48-block stack 9.00 GB, and at one byte each those last two fall to 1.1 MB and 2.25 GB.

Nine gigabytes will not fit in the memory of a small computer bolted to a robot
arm, which is why how many bytes a number takes is a decision anybody running a
large model has to make.
[Making a model smaller and faster](../07_pretraining-and-adapting/04_making-a-model-smaller-and-faster.md)
is about that decision. Having named the model and its parameters, the next
question is how the parameters got their values.

---

## 2. Training and inference, the two things you do with a model

Section 1 said that fitting chose the values 1.4 and 0.5, and when the model is
bigger than two numbers that search has its own name. **Training** is the process
of choosing the parameters, by repeatedly measuring how wrong the model's answers
are on the examples and nudging every parameter in the direction that makes that
measurement smaller. One such nudge is a **step**, and training is thousands or
millions of steps.

![A loss curve on a log scale falling from 6.5383 at step 0 to 0.0467 by step 300, beside a table of the slope, the offset and the miss at five moments during the run](../../images/what-learning-means/the-words-everyone-uses/training-curve.svg)

Starting both parameters at 0, the average squared miss falls from 6.5383 to 0.0566 in ten steps and reaches 0.0467 by step 100, with the slope moving 0.0000, 1.2924, 1.3777, 1.3968, 1.4000 and the offset 0.0000, 0.6732, 0.5366, 0.5052, 0.5000.

The number that training makes small is the score of being wrong, which on this
page is the average squared miss from the page before and which
[the score of being wrong](../03_how-training-works/01_the-score-of-being-wrong.md)
calls the loss. The training run above reached exactly the slope and offset that
the page before worked out by hand, which is worth noticing: the arithmetic
recipe and the step-by-step search arrive at the same two numbers, and only the
search still works when there are a billion parameters instead of two.

The search is easier to picture when there are only two parameters, because then
every possible model is a point on a map.

![A contour map of the average squared miss over slope and offset, with the training run's path starting at the origin and ending at the lowest point](../../images/what-learning-means/the-words-everyone-uses/parameters-walking.svg)

The run starts at slope 0.00 and offset 0.00, where the miss is 6.5383, and walks downhill to slope 1.4000 and offset 0.5000, where the miss is 0.0467.

[Gradient descent](../03_how-training-works/02_gradient-descent.md) is the page
that explains how each step knows which way is downhill. What matters here is
that training is a search over parameter values, that it happens once, and that
it is expensive.

Using a trained model is the other thing you do with it, and it has its own name.
**Inference** means running the model forwards on one new input, with the
parameters held fixed, to get one answer. The word is confusing at first, because
nothing is being inferred in the everyday sense, but it is what everybody says.

![A bar chart on a log scale of the multiply-and-add steps taken by one answer and by a whole training run, for the sag model and the cup model](../../images/what-learning-means/the-words-everyone-uses/training-vs-inference-cost.svg)

One answer from the sag model is 2 multiply-and-add steps and training it is 10,800, while one answer from the cup model is 7 steps and training it over 400 passes through 800 examples is 4,160,000, which is 594,285 times as much.

That ratio is why the two words are kept apart. Training is paid for once, in a
data centre, before anybody uses the model. Inference is paid for every single
time the robot looks at a cup, on whatever computer is bolted to the robot, and
it has to finish before the arm reaches the cup. The two have completely
different budgets, and
[running and evaluating a model](../13_using-a-model-for-real/01_running-and-evaluating-a-model.md)
is about the second of them. Both of them depend on the examples, which is the
next thing to name.

---

## 3. The dataset, and what generalisation means

The page before called a collection of examples a dataset, and training in
section 2 used one. The thing that was not said is that training must never be
scored on the same examples it trained on.

![Two boxes showing 800 cups used for training with an accuracy of 0.943 and 800 cups kept back with an accuracy of 0.926, with a row of dots underneath standing for individual examples](../../images/what-learning-means/the-words-everyone-uses/dataset-split.svg)

The cup dataset holds 1,600 simulated examples, of which 800 were used to choose the four parameters and 800 were kept back, and the model is right on 0.943 of the first half and 0.926 of the second.

**Generalisation** is how well a model does on inputs it was never trained on,
and it is the only score that means anything, because the robot will meet cups
that were not in the dataset. The 0.926 is the honest number here and the 0.943 is
not, because the parameters were chosen to make the 0.943 as large as possible.

The gap between those two numbers is small for the cup model, and the reason is
that it has only four parameters. Give a model more parameters and the gap grows,
which is the single most important fact about training.

![Two panels: the miss on ten examples falling steadily as parameters are added while the miss on inputs in between falls and then rises, and the fitted curves for 3 and 9 parameters](../../images/what-learning-means/the-words-everyone-uses/seen-vs-unseen.svg)

Fitting curves of 2 to 9 parameters to ten examples, the miss on those examples falls from 0.2153 to 0.0234 without ever rising, while the miss on inputs in between falls to 0.0171 at 3 parameters and then climbs to 0.0827 at 9.

The 9-parameter curve is the better model by the only measurement it was given,
and it is the worse model by the measurement that matters. It passes very close to
all ten examples and wanders between them, chasing the wobble in the labels
instead of the shape underneath. That failure has a name,
[overfitting](../04_making-training-work/01_overfitting-and-generalisation.md),
and the whole of that page is about spotting it and stopping it.

The flexible model is not wrong to exist, because the same curve generalises
perfectly well once there are enough examples to pin its parameters down.

![A curve on log scales of the miss on unseen inputs for an 8-parameter curve against the number of examples it was fitted to, falling from 1.2893 at 9 examples to 0.0103 at 200](../../images/what-learning-means/the-words-everyone-uses/generalisation-vs-size.svg)

The same 8-parameter curve misses unseen inputs by 1.2893 when fitted to 9 examples, by 0.0393 at 25 and by 0.0103 at 200, which is 126 times better.

That is why the number of parameters and the number of examples always have to be
talked about together, and why so much of this book is about where more examples
come from. Where they come from is the subject of the next section.

---

## 4. Three ways a model is told what is right

Section 3 assumed somebody had written the right answer beside every example, and
that is only one of the three arrangements in use. They differ in who supplies the
right answer, not in the arithmetic, and all three are still called learning.

**Supervised learning** is the arrangement in the last two sections, where every
example carries a label that a person or an instrument wrote down. It gives the
clearest training signal of the three, and its cost is the labelling.

![A bar chart on a log scale of the person-hours needed to label 1,600, 20,000 and 200,000 examples at 25 seconds each, and 200,000 at 120 seconds each](../../images/what-learning-means/the-words-everyone-uses/supervised-labels.svg)

At 25 seconds a cup, labelling 1,600 cups takes 11 person-hours, 20,000 takes 139 and 200,000 takes 1,389, and at 120 seconds each, as a careful outline drawn round an object takes, 200,000 examples take 6,667 person-hours.

Those hours are why the next arrangement exists. **Self-supervised learning**
hides part of the data and asks the model to produce the hidden part, so the data
supplies its own answers and nobody writes a label at all.

![A six-second joint angle recording with half a second hidden across a peak, the hidden part drawn as a dashed line and the model's filled-in guess drawn over it](../../images/what-learning-means/the-words-everyone-uses/self-supervised-fill-the-gap.svg)

Hiding 25 samples of a simulated joint recording, including the moment the joint turns round, and filling them in from the samples either side gives a guess out by 3.56 degrees on average and 5.26 degrees at worst.

The gap in that picture was not labelled by anybody, because the recording
already contained the answer and it was simply covered up. This matters far more
than it looks, because it means a model can be trained on data nobody has
annotated, which is almost all the data there is.
[Self-supervised pretraining](../07_pretraining-and-adapting/01_self-supervised-pretraining.md)
shows that nearly every large model in use today was trained this way.

The third arrangement has no answers at all, only outcomes. **Reinforcement
learning** lets the model try something, scores whether the attempt worked, and
uses that score to change what it tries next.

![Two panels: the share of each block of twenty reach attempts that worked, rising from 0.00 to 0.75, and every attempt's grasp height coloured green for success and red for failure](../../images/what-learning-means/the-words-everyone-uses/reinforcement-tries.svg)

Over 400 simulated attempts at a grasp whose best height is 42 millimetres above the table, the share that worked rises from 0.00 in the first twenty to 0.75 in the last twenty, 264 attempts succeeded in all, and the search settled on 37.4 millimetres.

Nobody ever told that search what the right height was, and it found 37.4
millimetres from nothing but 400 answers of the form "that worked" or "that did
not". The cost is in that sentence, because the 136 failures were real attempts on
a real arm with a real object falling on the floor.
[Reinforcement learning](../11_learning-from-outcomes/01_reinforcement-learning.md)
goes through how the scores turn into better attempts and why most of this
happens in simulation.

The three arrangements are easiest to compare by what a person has to supply.

![A bar chart on a log scale of what a person writes for each of the three kinds of learning, with 1,600 answers for supervised, 0 for self-supervised and 1 scoring rule for reinforcement](../../images/what-learning-means/the-words-everyone-uses/three-signals-cost.svg)

For the cup job, supervised learning needs 1,600 written answers, self-supervised learning needs none because the hidden samples are the answer, and reinforcement learning needs one written scoring rule plus 400 attempts on the real arm.

Read that chart with care, because the shortest bar is not the cheapest method.
Writing the scoring rule for reinforcement learning is one line of work and
getting it slightly wrong produces a robot that scores well while doing something
useless, which
[rewards, preferences and verifiers](../11_learning-from-outcomes/02_rewards-preferences-and-verifiers.md)
is entirely about. Self-supervised learning needs no labels and needs enormous
amounts of unlabelled data instead. The three are usually combined rather than
chosen between, and the next section places all three inside the four names people
give to this field as a whole.

---

## 5. Artificial intelligence, machine learning, deep learning and foundation models

The last four sections used four more words without defining them, and they are
the four that people outside the field use interchangeably. They are not
interchangeable, because each one sits inside the one before it.

![Four nested rectangles labelled artificial intelligence, machine learning, deep learning and foundation models, each with one concrete example and its count of learned numbers](../../images/what-learning-means/the-words-everyone-uses/four-names-nested.svg)

The joint-limit check from the page before sits in the outer ring with 0 learned numbers, the fitted sag line in the second with 2, the picture network in the third with 1,114,881, and a 48-block stack in the innermost with 2,415,919,104.

**Artificial intelligence** is the outer ring, and it is any program that does a
job people would call clever. The joint-limit check is inside it, which shows how
wide the term is, and it is wide because it was named after the goal rather than
after any method. The term is in every headline and carries almost no information,
so this book uses it as little as possible.

**Machine learning** is the second ring, and it is the part of artificial
intelligence where the program finds the numbers inside itself from examples
instead of being told them. Everything on the page before this one, from the six
measurements onwards, is machine learning, and so is the fitted line with its two
parameters. The boundary is exactly the one drawn on that page, between a rule
somebody wrote and a formula somebody fitted.

**Deep learning** is the third ring, and it is the part of machine learning where
the model is made of many layers of neurons stacked on top of each other, so the
output of one layer is the input of the next. The word deep means that there are
many such layers, and nothing more.

![Two panels: the miss on unseen inputs against the number of hidden layers, and the curves a one-layer and a three-layer network produce on the same simulated target](../../images/what-learning-means/the-words-everyone-uses/depth-helps.svg)

On one simulated job, networks of 1 to 5 hidden layers of 12 neurons miss unseen inputs by 0.2873, 0.2421, 0.0237, 0.0291 and 0.0257, so three layers is 12.1 times better than one while holding 349 parameters against 37.

The second panel shows what those numbers mean, because the one-layer network
rounds off every bend in the target while the three-layer network follows them.
[What a network can learn](../02_inside-a-network/04_what-a-network-can-learn.md)
explains why stacking layers has that effect, and
[layers and depth](../02_inside-a-network/02_layers-and-depth.md) explains what a
layer is. Almost every model this book describes after chapter 2 is a deep model,
which is why deep learning and machine learning are so often confused.

A **foundation model** is the innermost ring. It is one large deep model, trained
once on a huge and mixed pile of data, and then adapted to many different jobs
instead of being built for one. The reason anybody pays for a model with billions
of parameters is that the cost is shared.

![A bar chart on a log scale of the shared part of a foundation model against the extra parameters needed to add three different jobs to it](../../images/what-learning-means/the-words-everyone-uses/one-model-many-jobs.svg)

A shared 48-block stack holds 2,415,919,104 parameters, while adding a job that names one of 500 objects costs 1,024,500 more, telling a full cup from an empty one costs 4,098 and giving three finger positions costs 6,147, so all three together are 2,335 times smaller than the shared part.

So the nesting is that every foundation model is a deep model, every deep model is
a machine learning model, and every machine learning model is artificial
intelligence, while none of those arrows runs the other way.
[Fine-tuning and adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md)
is the page about how a job is actually added to a shared model. With all four
names placed, the last section puts every word on this page onto one job at once.

---

## 6. Every word on one job from start to finish

The cup job has appeared in every section above, and this section runs through it
once from end to end, naming each word as it arrives, so that the vocabulary
hangs together rather than sitting in a list.

![Four boxes in a row labelled dataset, training, the model and inference, each filled with the cup job's real numbers](../../images/what-learning-means/the-words-everyone-uses/words-on-one-job.svg)

The dataset holds 1,600 examples of 3 features and 1 label, split 800 for training and 800 held back; training runs 400 steps and drops the score of being wrong from 0.693 to 0.140; the model is 3 weights and 1 offset; and inference turns one new cup into one number, right on 0.926 of the held-back cups.

Follow it left to right. Somebody photographs 1,600 cups and writes beside each
one whether it is full, which makes 1,600 examples and therefore a dataset, and
that is supervised learning. Three numbers are measured from each photograph, and
those are the features. Half the examples are set aside and never shown to the
training, so that the score on them at the end is a measurement of
generalisation. The model is chosen to be three weights and one offset, which
makes four parameters, and all four start at zero. Training then runs 400 steps,
and each step changes all four a little.

![Two panels: the score of being wrong falling over 400 steps from 0.693 to 0.140, and a histogram of the one number the model gives for each held-back cup](../../images/what-learning-means/the-words-everyone-uses/train-and-run-the-cup-model.svg)

The score of being wrong is 0.693 at step 0, 0.192 at step 50, 0.145 at step 200 and 0.140 at the end, and the model is then right on 0.926 of the 800 held-back cups.

The right-hand panel is inference happening 800 times. Each held-back cup goes in
as three numbers and one number comes out, and the model calls the cup full when
that number is above 0.5. Most of the empty cups pile up near 0 and most of the
full ones near 1, and the cups in the middle are the ones it gets wrong.

The last thing to see is what separates training from inference, which is simply
whether the four numbers are allowed to move.

![The four parameters plotted against training step, rising and flattening over 400 steps and then drawn as flat dotted lines through a shaded region labelled inference](../../images/what-learning-means/the-words-everyone-uses/which-word-when.svg)

The three weights move from -0.080, +0.080 and -0.080 after one step to -7.497, +3.081 and +6.414 after 400, and the offset from +0.080 to +0.183, after which they never change again.

They are called parameters throughout, during training and afterwards, and the
only difference is that training moves them and inference does not. Everything
that follows in this book is this same picture with more parameters in it. The
next chapter opens the model box and shows what is inside when the formula is not
a straight line but a network, starting with
[one neuron](../02_inside-a-network/01_one-neuron.md) worked out by hand.

---

## 7. Where to read next

- [One neuron](../02_inside-a-network/01_one-neuron.md) is the next page, and it
  replaces this page's four-parameter formula with the smallest piece of a neural
  network, worked out with real numbers.
- [Gradient descent](../03_how-training-works/02_gradient-descent.md) explains how
  each of section 2's steps knows which way to move every parameter.
- [Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
  takes section 3 much further, including how to split a dataset honestly and what
  to do when the gap between the two scores opens up.
- [Self-supervised pretraining](../07_pretraining-and-adapting/01_self-supervised-pretraining.md)
  shows how section 4's second arrangement became the way almost every large model
  is trained.
- [Reinforcement learning](../11_learning-from-outcomes/01_reinforcement-learning.md)
  is the full version of section 4's third arrangement, with the words for states,
  actions and rewards.
- [Learning signals](../../07_learned-models/01_what-models-are/04_learning-signals.md)
  is the catalogue entry for section 4, and lists which real robot models are
  trained in which of the three ways.

---

## 8. Using it in Python

The cup model used all through this page is small enough to build in one screen of
NumPy, which is the array library most Python numerical work is built on. The code
below makes the same 1,600 simulated cups, fits four parameters to half of them
and scores itself on the other half, and the comments say which section each line
belongs to.

```python
import numpy as np

rng = np.random.default_rng(31)                                 # section 3: the dataset
n = 1600
full = rng.integers(0, 2, n).astype(float)                      # the label of each example
base = rng.uniform(90, 180, n) * rng.uniform(0.8, 1.2, n)       # cup colour times lighting
inside = base + np.where(full > 0.5, -18.0, 4.0) + rng.normal(0, 8, n)   # feature 1
spread = np.where(full > 0.5, 9.0, 4.0) + rng.normal(0, 2.2, n)          # feature 2
wall = base + rng.normal(0, 6, n)                                       # feature 3

X = np.column_stack([inside, spread, wall, np.ones(n)])   # section 1: 3 weights + 1 offset
train, test = slice(0, 800), slice(800, 1600)             # section 3: the split

w, *_ = np.linalg.lstsq(X[train], full[train], rcond=None)   # section 2: training
print(np.round(w, 4))                  # [-0.0166  0.0704  0.0159  0.0476]
print(X.shape, w.size)                 # (1600, 4) 4

seen = float(((X[train] @ w > 0.5) == (full[train] > 0.5)).mean())
unseen = float(((X[test] @ w > 0.5) == (full[test] > 0.5)).mean())
print(round(seen, 3), round(unseen, 3))   # 0.941 0.93    section 3: generalisation

one = X[test][0]                                             # section 2: inference
print(round(float(one @ w), 3), bool(one @ w > 0.5))         # 0.776 True
```

The library does two things here. It gives you arrays, so `X[train] @ w` works out
all 800 answers in one expression rather than a loop, and it gives you
`np.linalg.lstsq`, which finds the four parameters that make the total squared
miss as small as possible. That one call replaces the whole training run of
section 2, and it is exact rather than step by step, which is possible only
because this model is a weighted sum. Every model later in this book needs the
step-by-step search instead, and then the library you reach for is PyTorch, where
the same four parameters would be an `nn.Linear(3, 1)` layer.

What the library will not decide is the shape of the problem. You choose the three
features, you choose to put a column of ones in so there is an offset, you choose
where to split the dataset, and you choose 0.5 as the point above which a cup is
called full. Moving that last number trades one kind of mistake for the other,
since a lower threshold calls more cups full and therefore catches more full cups
while wrongly calling some empty ones full.

Notice also that the printed scores are 0.941 on the half that was trained on and
0.930 on the half that was not, which are the two numbers section 3 said must
always be reported together. The exact fit here and the step-by-step fit used for
the diagrams reach slightly different parameters and nearly the same scores, which
is the ordinary situation rather than a problem: two training methods that reach
the same quality of answer are both correct, and the one you pick is decided by
cost rather than by the answer.
