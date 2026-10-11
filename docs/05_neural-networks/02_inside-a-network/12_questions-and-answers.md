# Questions and answers

This page collects the questions that the rest of the chapter raises but does not
stop to answer, either because the answer belongs to a later chapter or because
the honest answer is shorter than a section. It is the last page of the chapter,
and it assumes you have read some of the others, because every answer here points
at the page where the idea is worked out properly.

Nothing on this page is new. If an answer seems too short, that is because it is a
summary of a page, and the link after it goes to the full treatment. Read it
either straight through as a review of the chapter, or one question at a time when
that question comes up.

## Contents

1. [How many layers and how many neurons should I use?](#1-how-many-layers-and-how-many-neurons-should-i-use)
2. [Which rule should follow each layer?](#2-which-rule-should-follow-each-layer)
3. [How large is a network, and how do I tell?](#3-how-large-is-a-network-and-how-do-i-tell)
4. [Why use a neural network rather than something simpler?](#4-why-use-a-neural-network-rather-than-something-simpler)
5. [Can anyone say what a neuron in a trained network is doing?](#5-can-anyone-say-what-a-neuron-in-a-trained-network-is-doing)
6. [Where do the weights come from?](#6-where-do-the-weights-come-from)
7. [What if a reading is not a number?](#7-what-if-a-reading-is-not-a-number)
8. [Is a neural network like a brain?](#8-is-a-neural-network-like-a-brain)
9. [What is the difference between a neural network and deep learning?](#9-what-is-the-difference-between-a-neural-network-and-deep-learning)
10. [Where to read next](#10-where-to-read-next)

---

## 1. How many layers and how many neurons should I use?

There is no formula, and anyone who gives you one is selling something. The
working answer has two parts.

The first part is the rule of thumb. Start with the simplest network that could
possibly do the job, and make it more complicated only when it is not good enough.
If no hidden layer does the job, stop there. If one hidden layer does the job,
stop there. Each step up costs memory, arithmetic and training time, and it buys
nothing when the simpler network was already good enough.

The second part is that the choice is settled by trying. People try a few widths,
keep the one that works best on examples the network was not trained on, and move
on. Widths are usually powers of two, which is habit and convenience rather than
anything deeper. Making a network larger stops helping at some point and then
starts hurting, because a network with too many numbers can learn its examples
instead of the job, which is what
[overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
is about.

What the chapter can tell you is what each choice buys and what it costs.
[Layers, depth and width](08_layers-and-depth.md) covers what width and depth each
add, and [layers, depth and width, worked
out](09_layers-and-depth-worked-out.md#2-what-depth-and-width-cost) counts the
cost: doubling the width of a layer costs about four times as much, while doubling
the depth costs about twice as much.

---

## 2. Which rule should follow each layer?

Split the question in two, because the hidden layers and the output layer are
decided in completely different ways.

For the hidden layers it is a free choice, and the default is easy. Use the
rectified linear unit unless you have a reason not to; it is simple, it is fast,
and it works. The models built today mostly use GELU or SiLU instead, which are
smoothed versions of the same shape that train a little more steadily.
[Activation functions](07_activation-functions.md) compares all three and says
what each costs.

For the output layer it is not a choice at all. The rule has to be able to produce
the kind of answer the job needs, so the job decides it. An answer that is one
probability needs a rule that can only give a number between 0 and 1, which is
what the sigmoid does. An answer that is a plain number, such as a distance in
millimetres, needs no rule at all, because any number is allowed. An answer that
picks one of several named possibilities needs a rule that gives several numbers
that add up to 1.

So the useful habit is to decide what the answer has to look like first, and let
that fix the last rule, before thinking about anything in the middle.

---

## 3. How large is a network, and how do I tell?

A network's size is the number of weights and biases it owns, and those two
together are called its parameters. You can count them from the shape alone,
without training anything and without running anything.

A fully connected layer owns one weight for every joining of an input to a neuron,
which is the number of inputs multiplied by the number of neurons, and one bias
for each neuron. Add that up over the layers and you have the network.
[Layers, depth and width, worked
out](09_layers-and-depth-worked-out.md#1-counting-the-numbers-one-network-owns)
does it on a whole network: 29 numbers in, 16 neurons and 1 out comes to 497
parameters.

It is worth doing by hand the first few times, because the count behaves in a way
that surprises people. It grows with the product of the two sides a layer joins
rather than with their sum, so widening one layer from 16 neurons to 1,024 takes
that same network from 497 parameters to 31,745. The biases are almost nothing in
the total and the weights are almost everything.

The count is also the number that decides whether a model fits on the machine you
have, once you know how many bytes each parameter takes.
[The shape of the numbers](10_the-shape-of-the-numbers.md) turns the count into
gigabytes.

---

## 4. Why use a neural network rather than something simpler?

Two things decide it, and they usually pull in opposite directions.

The first is whether anything simpler would do. If your readings are already the
quantities that matter, which is what [neural networks and
neurons](01_networks-and-neurons.md#2-why-there-is-anything-in-the-middle) calls
structured data, then older methods are often as good and sometimes better, and
they need far less data and far less computing. A neural network earns its place
when the raw input is a picture, a sound or a long sensor trace, because then
somebody would otherwise have to invent the useful quantities by hand.

The second is whether you need to be able to explain the answer. Simpler models
can be read: a coefficient in a fitted line tells you what that input did. A
network cannot be read that way, which the next question is about. When somebody
has to justify a decision to a person who will not accept "the model said so", a
model you can explain is worth losing some accuracy for.

[Rules against models](../01_what-learning-means/04_rules-against-models.md) sets
out the same trade for written rules against fitted models, and
[the map of models](../14_using-a-model-for-real/02_the-map-of-models.md) covers
choosing between kinds of model.

---

## 5. Can anyone say what a neuron in a trained network is doing?

Not usually, and it is worth being exact about which part is hard.

Following one input through the network is not hard at all. Every number is known,
every multiplication is known, and you can print the value of any neuron for any
input you like. There is no mystery in the mechanism, and nothing is hidden.

What is hard is saying what a neuron is for. On [one neuron of that
network](06_one-neuron-of-that-network.md) the four neurons have descriptions you
can read, but only because the weights were chosen by hand to make that true.
Training chooses weights that work, not weights that can be described, so the
features that come out of a trained layer rarely line up with anything a person
has a word for. A single answer is then built from hundreds of these, and saying
which reading deserves the credit for it is not a question the arithmetic answers.

There is a field of research devoted to this, usually called interpretability, and
it has real results. But the plain answer for someone building something today is
that a network tells you its answer and not its reasoning.

---

## 6. Where do the weights come from?

Training, and nothing else. Nobody sets them by hand in a working model, and the
only reason this chapter sets them by hand is so that the arithmetic is small
enough to follow.

The short version is that the weights start as small random numbers, the network
is run on examples where the right answer is known, a score says how wrong it was,
and every weight is nudged in the direction that would have made the score better.
Repeat that a very large number of times. The whole of the next chapter,
starting at [the score of being
wrong](../03_how-training-works/01_the-score-of-being-wrong.md), is about how that
is done.

Two things follow from it that matter even before you read that chapter. The
weights are the expensive part of a model, because they are what the computing
time and the data bought, which is why a model's weights are the thing people
publish or keep. And the weights are the only thing training can change: the shape
of the network, the number of layers and the rules between them are all fixed
before training starts and are not touched by it.

---

## 7. What if a reading is not a number?

Then it has to be turned into numbers before it reaches a layer, because a layer
can only multiply numbers.

If the reading is a choice from a short list, such as which of three tools is
fitted, give each option a number of its own and set the chosen one to 1 and the
rest to 0. That is called one-hot encoding, and
[layers, depth and width, worked
out](09_layers-and-depth-worked-out.md#1-counting-the-numbers-one-network-owns)
shows it. The reason not to just number the options 1, 2 and 3 is that a single
number carries an order and a spacing that the options do not have.

If the reading is a picture, a sound or a piece of text, the answer is longer and
it has a chapter of its own: [turning the world into
numbers](../05_turning-the-world-into-numbers/01_tokens-and-embeddings.md).

One thing applies to every reading that already is a number. Readings arrive in
different units, and a reading measured in millimetres would otherwise count for a
hundred times more than the same thing measured in metres. So readings are scaled
to a comparable range first, as [the three
readings](02_the-grasp-example.md#2-the-three-readings) of the grasp example are.

---

## 8. Is a neural network like a brain?

The name came from a loose comparison with how nerve cells were thought to work,
and the comparison has not aged well. A neuron here is a multiplication, an
addition and a simple rule. That is all it is, and the resemblance to anything
biological ends about there.

The honest position is that the connection between neuroscience and these models
is argued over by people who know far more about both than this book covers, and
that you do not need any of it. Nothing in this chapter, and nothing you will
build, depends on the comparison being true. Treat **neuron** as the name of a
small piece of arithmetic and you will never be misled by it.

---

## 9. What is the difference between a neural network and deep learning?

Deep learning is the use of neural networks with many layers. There is no other
difference, and there is no particular number of layers at which one becomes the
other.

The word exists because depth is what changed. Networks with one or two hidden
layers had been around for decades without being especially useful. What made them
work was the arrival of three things at the same time: much more data, hardware
that could do the arithmetic fast enough, and a few changes that made deep stacks
trainable at all, of which [residual
connections](08_layers-and-depth.md#5-residual-connections) is one.

[The words everyone uses](../01_what-learning-means/06_the-words-everyone-uses.md)
places both terms next to artificial intelligence, machine learning and foundation
models, which are the other words you will meet in the same sentence.

---

## 10. Where to read next

- [The score of being wrong](../03_how-training-works/01_the-score-of-being-wrong.md)
  starts the next chapter, which answers the largest question this one leaves
  open: how the weights are actually found.
- [Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
  is where the size of a network stops being only a cost and starts being a risk.
- [Tokens and embeddings](../05_turning-the-world-into-numbers/01_tokens-and-embeddings.md)
  deals with the inputs this chapter kept simple, such as text and pictures.
- [Attention](../06_the-transformer/01_attention.md) begins the architecture that
  nearly every model in this book is built from.
- [The map of models](../14_using-a-model-for-real/02_the-map-of-models.md) is the
  overview of which kind of model suits which job.
