# How a model learns

The [previous page](01_what-a-model-is.md) said that a model is a function
learned from examples, and that a neural network is a model made of weights.
This page answers the next question: how does a computer program find the
right weights?

It is for a reader who has read the previous page and nothing else about
machine learning. It follows one small example, a model that tells a mug from
a bowl in a photo, through every step of training. It uses no maths beyond
adding, multiplying and reading a graph.

By the end you will know the words that every later page uses: example,
label, loss, gradient descent, learning rate, epoch, training set, test set,
overfitting, underfitting and checkpoint.

> Before this page, it helps to have read [least-squares fitting](../../05_programming-techniques/04_fitting-and-estimation/02_most-used/01_least-squares-fitting.md), which finds the two numbers of a line by making the sum of squared errors as small as possible. Training a model does the same job for many more numbers.

## Contents

1. [Examples and labels](#1-examples-and-labels)
2. [The first guess is random](#2-the-first-guess-is-random)
3. [Measuring how wrong a guess is: the loss](#3-measuring-how-wrong-a-guess-is-the-loss)
4. [Changing the weights a little: gradient descent](#4-changing-the-weights-a-little-gradient-descent)
5. [Doing it many times: batches and epochs](#5-doing-it-many-times-batches-and-epochs)
6. [Keeping some examples back: the test set](#6-keeping-some-examples-back-the-test-set)
7. [Too simple and too close: underfitting and overfitting](#7-too-simple-and-too-close-underfitting-and-overfitting)
8. [What a trained model file is](#8-what-a-trained-model-file-is)
9. [Why train this way, and what it costs](#9-why-train-this-way-and-what-it-costs)
10. [Where to read next](#10-where-to-read-next)

---

## 1. Examples and labels

Training starts with a pile of examples. For the mug-or-bowl model, one example
is one photo from the arm's camera.

Each example needs the right answer written next to it. This right answer is
called the **label**. For a photo of a mug, the label is "mug". For a photo of
a bowl, the label is "bowl". Usually a person looks at each photo and types the
label. This work is called **labelling**, and it is often the slowest part of
the whole job.

A pile of examples with their labels is called a **dataset**. A small dataset
for a job like this might have a few hundred photos. A large public dataset can
have millions. ImageNet, a dataset that many seeing models learned from, has
about 1.2 million training photos sorted into 1,000 kinds of object.

The label must match what you want the model to output. If you want the model
to draw a box around the mug, each label must be a box, drawn by a person. If
you want the model to move the arm, each label must be the arm movement that a
person made. The [data page](05_where-the-data-comes-from.md) covers how robot
labels are collected.

Learning from examples that have labels is called **supervised learning**. The
labels supervise the model, in the sense that they tell it the right answer
every time. Most models in this book are trained this way. The
[reinforcement learning page](../05_movement-models/03_also-used/01_reinforcement-learning-policies.md)
describes the main other way.

---

## 2. The first guess is random

Before training, the model's weights are set to small random numbers. A model
with random weights still gives an output for every photo, because it is still
a fixed calculation. But the output has nothing to do with the photo. It might
give "mug" a score of 0.40 and "bowl" a score of 0.60 for a photo of a mug.

Training is the process of changing the weights until the outputs are right.
It repeats the same four steps, shown in the picture below:

1. Show the model one example.
2. Let the model make its guess.
3. Measure how wrong the guess is.
4. Change the weights a little, so that the guess would be a little less wrong.

![One training step: an example of a mug, the model's guess, the loss, and the weights changed a little](../../images/what-models-are/how-a-model-learns/one-training-step.svg)

The model gives the mug only 0.40, the loss measures how wrong that is as 0.92, and after each weight is changed a little the same photo would score 0.46 for "mug", with a smaller loss of 0.78.

The next two sections explain steps 3 and 4.

---

## 3. Measuring how wrong a guess is: the loss

To improve a guess, the program first needs to know how wrong the guess is. It
needs this as one number. That number is called the **loss**. A loss of 0
means the guess was exactly right. A bigger loss means the guess was more
wrong.

There are several ways to calculate a loss. The right one depends on what the
model outputs.

When the model gives a score for each kind of object, a common loss looks only
at the score the model gave to the right answer. If that score is 1, the loss
is 0. As that score gets smaller, the loss gets bigger, faster and faster. The
table below shows a few values. Read each row as one guess for a photo of a
mug.

| Score the model gave "mug" | Loss |
| --- | --- |
| 0.93 | 0.07 |
| 0.46 | 0.78 |
| 0.40 | 0.92 |
| 0.01 | 4.61 |

The loss in each row is minus the natural logarithm of the score. You do not
need to know what a logarithm is to follow this book. The only thing that
matters is the shape: a confident right answer gives a loss near 0, and a
confident wrong answer gives a big loss. This loss is called the
**cross-entropy loss**.

When the model outputs a measurement instead, such as how far to open the
gripper, the loss is usually simpler. It is the difference between the model's
number and the label's number, squared so that it is never negative. This is
called the **squared error**.

So the loss turns "how wrong is this guess?" into a single number that a
program can make smaller.

---

## 4. Changing the weights a little: gradient descent

Now the program must change the weights so that the loss goes down. It cannot
try every possible set of weights. Even a small network has thousands of them.

Instead it asks one question about each weight: "if this weight were a tiny bit
bigger, would the loss go up or down, and by how much?" The answer for one
weight is called its **slope**. The list of slopes for all the weights together
is called the **gradient**.

Once it knows the slope, the program changes the weight a small amount in the
direction that makes the loss go down. If making the weight bigger raises the
loss, it makes the weight a bit smaller. If making it bigger lowers the loss,
it makes it a bit bigger. It does this for every weight at the same time.

This method is called **gradient descent**. "Descent" means going down, and the
thing going down is the loss.

The picture below shows gradient descent for a model that has only one weight.
The curve shows the loss for every value of that weight.

![The loss curve for one weight, with seven points showing the weight moving step by step to the lowest point](../../images/what-models-are/how-a-model-learns/steps-down-the-curve.svg)

Starting from a random weight with a big loss, each step moves the weight a little way down the curve, and the steps get shorter as the curve flattens near the lowest point.

The numbers behind the picture are these. The weight starts at -1.50, where
the loss is 7.65. After the first step the weight is -0.03 and the loss is
2.77. After six steps the weight is 1.87 and the loss is 0.31. The lowest
possible loss on this curve is 0.30, at a weight of 2.0.

Two things in the picture are worth noticing.

- Each step is a fixed fraction of the slope. Where the curve is steep, the step
  is long. Near the bottom, the curve is almost flat, so the steps are short.
  The fraction is called the **learning rate**. In this picture it is 0.35.
- The program never sees the whole curve. It only knows the slope at the point
  where it is. That is enough to know which way is down.

Choosing the learning rate matters. If it is too small, training takes a very
long time. If it is too big, each step jumps right over the lowest point and
the loss can get worse instead of better.

A real network has millions of weights, not one. The curve becomes a surface
in millions of directions, which nobody can draw. But the rule for each weight
is the same: find its slope, and move it a little in the downhill direction.

The slopes for all the weights of a neural network can be worked out in one
pass backwards through the layers, from the output to the input. This method
is called **backpropagation**. You will see the word often. It is the way the
slopes are calculated, and gradient descent is what is done with them.

---

## 5. Doing it many times: batches and epochs

One step of gradient descent changes the weights only a little. Training
needs a great many steps.

In practice the program does not take one step per example. It takes a small
group of examples, for example 32 photos, and works out the average loss over
the group. Then it takes one step for the whole group. This group is called a
**batch**. Using a batch makes each step less affected by one unusual photo,
and a graphics card can work on the 32 photos at the same time.

One pass through every example in the dataset is called an **epoch**. If the
dataset has 3,200 photos and each batch has 32, one epoch is 100 steps.
Training usually runs for many epochs. The model sees each photo many times,
and each time the weights change a little more.

While training runs, the program prints the average loss after each epoch.
The loss should go down quickly at first and then more and more slowly. When it
stops going down, training has done most of what it can.

---

## 6. Keeping some examples back: the test set

A low loss on the training examples does not prove that the model is good. The
model might have learned those exact photos, instead of learning what makes a
mug a mug. The only way to find out is to try it on photos it has never seen.

So before training starts, the examples are split into separate piles:

- The **training set** is the pile that gradient descent uses to change the
  weights. It is usually the biggest pile, for example 80% of the examples.
- The **validation set** is a smaller pile, for example 10%. The model never
  trains on it. People check the loss on it during training, to decide things
  such as when to stop.
- The **test set** is the last pile, for example the other 10%. Nobody looks
  at it until training is completely finished. It gives the final, honest
  score.

The test set must be truly new to the model. If the same mug on the same table
appears in both the training set and the test set, the test score will be too
good. For a robot, a fair test set uses objects, rooms or lighting that the
training set did not have.

---

## 7. Too simple and too close: underfitting and overfitting

The test set shows two common ways for a model to go wrong. The picture below
shows both, using a model with one input number and one output number, so that
it can be drawn as a curve.

![Three curves fitted to the same points: a straight line that is too simple, a smooth curve that is about right, and a wavy curve that passes through every training point](../../images/what-models-are/how-a-model-learns/too-simple-and-too-close.svg)

The filled dots are the training examples and the hollow dots are test examples that were kept back; the error under each panel is the average distance from the curve to the dots.

Read the three panels from left to right.

- On the left, the model is a straight line. It is too simple to follow the
  shape of the points. Its error is high on the training examples, 1.11, and
  high on the test examples, 1.31. This is called **underfitting**. The model
  has not learned the pattern.
- In the middle, the model is a smooth curve. Its error is low on both: 0.25 on
  training and 0.49 on test. This is what you want.
- On the right, the model is a wavy curve that passes exactly through every
  training point. Its training error is 0.00. But between the training points it
  swings far away, and its test error, 1.64, is the worst of the three. This is
  called **overfitting**. The model has learned the exact training examples,
  including their small random errors, instead of the general pattern.

Overfitting is the more common problem with neural networks, because they have
so many weights that they can learn the training set exactly. The sign is
always the same: the training loss keeps going down while the validation loss
stops going down or starts going up.

People do four main things about overfitting:

- Collect more examples. This is the most reliable fix.
- Make more examples from the ones they have. A photo can be turned slightly,
  cropped, made darker or made lighter, and it still shows a mug. This is called
  **data augmentation**.
- Stop training when the validation loss stops going down. This is called
  **early stopping**.
- Use a smaller model, or start from a model that was already trained on a much
  larger dataset. The [data page](05_where-the-data-comes-from.md) explains
  this second idea, which is called fine-tuning.

Underfitting has the opposite fixes: a bigger model, or more training.

---

## 8. What a trained model file is

When training finishes, the program saves the weights to a file. This file is
what people mean by "a trained model" or "the model weights". It is also called
a **checkpoint**, because it is a saved state that you can load and continue
from.

The file is mostly a very long list of numbers. There is one number for every
weight in the network. It does not contain the training photos, and it does
not contain any rules written in words. Nobody can open it and read how the
model tells a mug from a bowl.

The file on its own is not enough to use the model. You also need the program
code that describes the network: how many layers, how big each one is, and how
they connect. The code says which calculation to do. The file says which
numbers to use in it. When you download a model, you usually get both, or you
get the weights and install the code from a library.

A few file types are common. You will see their names on model download pages.

- `.pt` or `.pth` files are saved by PyTorch, the most widely used library for
  training neural networks.
- `.safetensors` files hold the same kind of weights in a format that is safe
  to load from a stranger, because loading it cannot run any hidden program.
- `.onnx` files use the Open Neural Network Exchange (ONNX) format. It stores
  both the network's layout and its weights, so that other programs can run the
  model without PyTorch.

The size of the file follows from the number of weights. Each weight is usually
stored in 4 bytes. ResNet-50, a well-known network for photos, has about 25
million weights, so its file is about 100 megabytes. The largest models in this
book have billions of weights, and their files are many gigabytes.

Using a trained model to get an answer is called **inference**. Inference only
does the forward calculation, from input to output. It does not change the
weights, and it needs far less computing power than training. The
[running-a-model page](../09_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md) covers inference on a
real robot arm.

---

## 9. Why train this way, and what it costs

This section answers why gradient descent is used rather than the obvious
alternative.

The obvious alternative is to try random changes. You change a weight at
random, keep the change if the loss went down, and undo it if not. This works
for a model with a handful of weights. With millions of weights it is hopeless.
Almost every random change makes things slightly worse, and you learn nothing
about which way to go. Gradient descent uses the slope of every weight, so
every step moves every weight in a useful direction. That is why it is used to
train nearly every neural network in this book.

Gradient descent costs you three things.

- It needs a lot of arithmetic. Every step runs the whole network forwards and
  then works out the slopes backwards. A large model needs a graphics card, or
  many of them, for hours or days.
- It needs settings that you choose by hand, such as the learning rate, the
  batch size and the number of epochs. These are called **hyperparameters**, to
  tell them apart from the weights that training finds. Bad choices can make
  training fail, and finding good ones often takes several attempts.
- It only finds weights that fit the examples you gave it. If the training set
  has no photos in dim light, no amount of training teaches the model about dim
  light. The quality of a model is limited by its data.

---

## 10. Where to read next

- [Inside a neural network](03_inside-a-neural-network.md) is the next page. It
  shows what a single neuron calculates, and the layers used for pictures and
  sentences.
- [Where the data comes from](05_where-the-data-comes-from.md) explains how
  labelled examples for a robot arm are collected, and how fine-tuning reuses a
  model trained on other data.
- [The glossary in Book 3](../../03_frameworks/04_one-arm-training/06_glossary.md#learning)
  defines the robot-learning words, such as demonstration and checkpoint, in
  one place.
- [Data and demonstration](../../03_frameworks/08_frontier/03_data-and-demonstration.md)
  in Book 3 goes further into how much data robot models need today.
