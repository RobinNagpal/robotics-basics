# One neuron, worked out by hand

The page before this one, [the words everyone uses](../01_what-learning-means/02_the-words-everyone-uses.md),
gave you the vocabulary of machine learning, and it said that a model is a
function with parameters in it, that a weight is one of those parameters, and
that training is the search for good values for them. This page opens one of
those models up and shows you the smallest piece it is built from, which is
called a **neuron**, and it works that piece out in full with real numbers so
that nothing is left as a word you have to take on trust.

A neuron takes a few numbers in, multiplies each one by a weight, adds the
results together, adds one more number of its own, and then passes the total
through a simple rule that decides what comes out. That is the whole of it, and
everything else in this book is built by joining many neurons together and
finding good values for their weights. So if you understand this page you
understand the part that the rest of the book repeats millions of times.

This page is for a reader who has read the two pages of the chapter before it
and who is comfortable with multiplying, adding and reading a graph with two
axes. You do not need algebra beyond putting numbers into a formula, and you do
not need to know anything about training, because the weights on this page were
chosen by hand so that you can watch what they do.

Everything is worked out on one made-up moment of one grasp: a robot arm is
reaching for a cup, and three sensors have just given their readings. Every
number in every picture on this page was worked out by
`docs/diagrams/inside_a_network_1.py`, which prints them as it draws, so the
numbers in the words and the numbers in the pictures are the same numbers.

## Contents

1. [What one neuron is made of](#1-what-one-neuron-is-made-of)
2. [The weighted sum, line by line](#2-the-weighted-sum-line-by-line)
3. [What changes when a weight or the bias changes](#3-what-changes-when-a-weight-or-the-bias-changes)
4. [Why multiplying and adding is not enough](#4-why-multiplying-and-adding-is-not-enough)
5. [The rectified linear unit](#5-the-rectified-linear-unit)
6. [GELU and SiLU, and why networks use them now](#6-gelu-and-silu-and-why-networks-use-them-now)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. What one neuron is made of

Since the page before this one described a model as a function with parameters
in it, the first thing to do is to look at the smallest function of that kind
that is worth looking at, and that is one neuron with three inputs. A neuron is
a very small function: it takes some numbers in, and it gives exactly one number
out. The numbers that go in are called its **inputs**, the one number that comes
out is called its **output**, and between the two there are only four numbers
that belong to the neuron itself.

![One neuron drawn as three input circles joined through weight boxes to a circle that adds up to 0.725, then a box holding the rule, then an output circle holding 0.725](../../images/inside-a-network/one-neuron/neuron-parts.svg)

The three readings 0.42, 0.55 and 0.30 are multiplied by the weights -2.00,
+1.50 and +0.80, the three products and the bias +0.50 are added to make 0.725,
and the rule passes that through unchanged because it is above 0.

The three inputs here are three real readings from a robot arm that is about to
close its gripper on a cup. The first is the distance from the gripper to the
cup in metres, which a depth camera has measured as 0.42. The second is how far
open the gripper is, which the gripper reports as 55 millimetres. The third is
how bright the patch of the camera picture is where the cup should be, which
matters because a patch that is almost black and a patch that is burnt out are
both hard to see anything in.

Those three readings arrive in three different sorts of unit, and a neuron
cannot do anything sensible with a 0.42 next to a 55, because the weight needed
to make the second one matter would have to be about a hundred times smaller
than the weight on the first. So each reading is first turned into a number
somewhere between 0 and 1, which is called scaling it, and the next picture
shows exactly how each of the three was scaled.

![Three rows showing 0.42 m passing through unchanged, 55 mm divided by 100 to give 0.55, and a 4 by 4 grid of grey pixel values averaging 76.5 and divided by 255 to give 0.30](../../images/inside-a-network/one-neuron/scaling-the-readings.svg)

The distance is already between 0 and 1 so it goes in as it is, the opening of
55 millimetres is divided by 100 because the jaws open to 100 millimetres, and
the sixteen pixel values in the patch add up to 1,224, which is an average of
76.5 out of 255, and dividing that by 255 gives 0.300.

So the three numbers that reach the neuron are 0.42, 0.55 and 0.30, and those
three numbers describe this one moment of this one grasp. Now the neuron's own
four numbers come in. Each input has a **weight**, which is a number that says
how much that input counts and in which direction, and the whole neuron has one
more number called its **bias**, which is added to the total whatever the inputs
are.

![A bar chart of the four numbers this neuron owns: weight on distance -2.00, weight on opening +1.50, weight on brightness +0.80, and bias +0.50](../../images/inside-a-network/one-neuron/the-four-parameters.svg)

The weight on the distance is -2.00, the weight on the opening is +1.50, the
weight on the brightness is +0.80 and the bias is +0.50, which is four numbers
for a neuron with three inputs.

A weight below 0 means that the bigger that reading gets, the smaller the
neuron's answer gets, and a weight above 0 means the opposite. The weights here
were picked so that this neuron answers one question: is the arm near a bright
object with its gripper open, which is the moment when closing the gripper is
likely to work. The distance gets a minus weight because being far away counts
against that, and the opening and the brightness get plus weights because both
count for it. In a real network nobody picks these four numbers by hand, because
training picks them, and the chapter [how training
works](../03_how-training-works/01_the-score-of-being-wrong.md) is where that
search is explained. For now they are fixed, so you can see what each one does.

---

## 2. The weighted sum, line by line

Now that the three inputs and the four parameters are all on the table, the
neuron can do its first job, which is to work out the **weighted sum**. This
means multiplying each input by its own weight, adding those products together,
and then adding the bias. There is nothing hidden in it, and it is short enough
to write out completely.

```
distance     0.42  x  -2.00  =  -0.840      running total  -0.840
opening      0.55  x  +1.50  =  +0.825      running total  -0.015
brightness   0.30  x  +0.80  =  +0.240      running total  +0.225
bias                  +0.50  =  +0.500      running total  +0.725
```

![A five column table giving each reading, its weight, the product and the running total, ending at +0.725](../../images/inside-a-network/one-neuron/weighted-sum-lines.svg)

The products are -0.840, +0.825 and +0.240, the bias adds another +0.500, and
the running total after the last line is +0.725, which is the weighted sum.

The running total in the last column is worth following, because it shows that
the answer swings about on the way. After the distance alone the total is below
0, and only when the opening is added does it climb back towards 0, so no single
reading decides the answer on its own. That is the whole point of a weighted
sum, which is that it lets several readings argue with each other and settles
the argument by weight.

![A bar chart with one bar for each line of the sum, the distance bar going down to -0.840 and the other three going up, and a final bar at +0.725](../../images/inside-a-network/one-neuron/contribution-bars.svg)

Only the distance pulls this sum down, because it is the only reading with a
minus weight, and the opening pushes it up the hardest at +0.825.

So far the arm has been standing still at 0.42 metres. The more interesting
question is what the neuron does as the arm moves, so the next picture holds the
opening at 0.55 and the brightness at 0.30 and sweeps the distance from 0 to 1
metre. Because the only thing changing is multiplied by one fixed weight, the
answer must be a straight line, and it falls by exactly 2.00 for every extra
metre of distance.

![A graph of the weighted sum against distance, falling in a straight line from 1.565 at 0 metres through 0.725 at 0.42 metres and reaching 0 at 0.7825 metres](../../images/inside-a-network/one-neuron/sum-against-distance.svg)

At 0 metres the sum is 1.565, at our reading of 0.42 metres it is 0.725, and it
crosses 0 at 0.7825 metres, after which the rule holds the output at 0.

That crossing point of 0.7825 metres is worth remembering, because it is the
distance at which this neuron falls silent, and the next section moves it about
on purpose. Two of the three readings can be swept at the same time, and when
they are, the place where the sum crosses 0 is a straight line across the
picture rather than a single point.

![A coloured map of the weighted sum over distance and gripper opening, with a straight black line marking where the sum is 0 and a white dot at our reading](../../images/inside-a-network/one-neuron/sum-over-two-readings.svg)

Over the whole square the sum runs from -1.260 to +2.240, and the line where it
is exactly 0 runs from an opening of 0.84 at a distance of 1 metre down to the
bottom edge, with our reading sitting well inside the part where the sum is
above 0.

The straightness of that line is the most important limit of a single neuron,
and section 4 comes back to it. First, though, it is worth seeing what the four
numbers the neuron owns actually control.

---

## 3. What changes when a weight or the bias changes

The weighted sum in the section before this one used one particular set of four
numbers, so the natural question is what would have happened with different
ones. The answer is easiest to see by changing one number at a time and working
the same sum out again, and the clearest single change is to flip the sign of
the weight on the distance from -2.00 to +2.00.

![Two tables side by side with the same three readings, one using the weight -2.00 on the distance and reaching +0.725, the other using +2.00 and reaching +2.405](../../images/inside-a-network/one-neuron/flipping-one-weight.svg)

With the weight -2.00 the distance contributes -0.840 and the sum is +0.725,
and with the weight +2.00 the same reading contributes +0.840 and the sum is
+2.405, which is more than three times as large.

Nothing about the robot changed between those two tables, and nothing about the
other two readings changed either. Only one of the neuron's own numbers moved,
and the neuron now answers a different question, because a neuron with a plus
weight on the distance is answering "is the arm far from a bright object with
the gripper open" instead. So a weight is not a detail of the arithmetic, since
it is the thing that decides what the neuron is for.

The size of a weight matters as well as its sign, and the easiest way to see
that is to look again at the line where the sum is exactly 0, because that is
the line the neuron draws across the readings.

![Three straight lines across a square of distance against gripper opening, for weights on the distance of -1.00, -2.00 and -4.00, each tilting more steeply than the last](../../images/inside-a-network/one-neuron/weight-size-lines.svg)

With the weight -1.00 the line only reaches an opening of 0.173 at the far right
of the square, with -2.00 it reaches 0.840, and with -4.00 it crosses the whole
square, so a bigger weight on the distance makes the line stand more upright and
leaves the neuron caring about the distance more and about the opening less.

A weight of +2.00 is missing from that picture for a good reason. With a plus
weight that size the smallest sum anywhere in the square is +0.740, so the sum
never reaches 0 at all and the neuron is switched on for every reading it could
ever see. A neuron that answers something above 0 no matter what is of no use to
anybody, and watching for that is part of the craft of training.

The bias does something different again. It is added whatever the readings are,
so it slides the whole line up or down without tilting it, and that moves the
point at which the neuron falls silent.

![Three lines of the neuron's output against distance, for biases of +0.50, 0.00 and -1.00, each reaching 0 at a different distance](../../images/inside-a-network/one-neuron/moving-the-bias.svg)

With the bias +0.50 the output reaches 0 at 0.7825 metres, with the bias 0.00 it
reaches 0 at 0.5325 metres, and with the bias -1.00 it reaches 0 at only 0.0325
metres, which leaves the neuron silent almost everywhere.

So the weights decide which way the line leans and the bias decides where it
sits, and between them those four numbers are the only freedom this neuron has.
That freedom is real but it is also narrow, because whatever you do to the four
numbers the dividing line stays straight, and the next section shows why that is
a problem that cannot be fixed by adding more neurons of the same kind.

---

## 4. Why multiplying and adding is not enough

The sections before this one kept finding straight lines, and that is not an
accident of the numbers chosen. Multiplying by a weight and adding a bias can
only ever make a straight line, and the surprising part is that doing it twice
does not help, because two of these neurons in a row are exactly equal to one
neuron with different numbers.

![A chain of two boxes, the first multiplying 0.42 by -2.00 and adding 0.50 to give -0.340, the second multiplying by 3.00 and subtracting 0.40 to give -1.420, above a single box that multiplies by -6.00 and adds 1.10 to give the same -1.420](../../images/inside-a-network/one-neuron/two-plain-layers.svg)

The first neuron turns 0.42 into -0.340 and the second turns -0.340 into -1.420,
and one neuron with the weight -6.00 and the bias +1.10 turns 0.42 straight into
-1.420 without the stop in the middle.

The reason is ordinary arithmetic. The second neuron multiplies whatever it
receives by 3.00, and what it receives is -2.00 times the distance plus 0.50, so
the pair works out 3.00 times -2.00 times the distance, which is -6.00 times the
distance, plus 3.00 times 0.50 minus 0.40, which is 1.10. The two weights
multiply together and the first bias is scaled by the second weight, and that is
all that is left of the first neuron.

![A graph showing the two plain layers and the single equivalent neuron lying exactly on top of each other as one straight line, and a third line that bends at 0.25 metres when the rule is put between the two layers](../../images/inside-a-network/one-neuron/collapse-curves.svg)

Across the whole sweep of distances the two plain layers and the single neuron
never differ by more than 0.0000000000000009, while putting the rule between
them gives a line that bends at 0.250 metres and is a different shape
altogether.

The same thing happens however many you chain together, which is worth checking
because it is easy to believe that three in a row must be able to do something
two cannot.

![A table of three layers with weights -2.00, +3.00 and +0.50 and biases +0.50, -0.40 and +1.20, giving -0.340, -1.420 and +0.490, and a last row showing that one neuron with weight -3.00 and bias +1.75 also gives +0.490](../../images/inside-a-network/one-neuron/three-plain-layers.svg)

The three weights multiply to -3.00 and the biases gather into +1.75, so three
layers in a row give exactly the same +0.490 that one layer with those two
numbers gives.

This matters because plenty of useful jobs cannot be done by a straight line at
all. Here is one, taken from the same robot. The brightness of the patch is good
in the middle and bad at both ends, since a patch that is nearly black shows
nothing and a patch that is burnt out shows nothing either, so the best
brightness is somewhere around the middle of the range.

![Two graphs, the left one showing a tent-shaped target with the best flat straight line through it leaving an average error of 0.251, the right one showing two rule-neurons adding up to the same tent exactly](../../images/inside-a-network/one-neuron/a-bend-is-needed.svg)

The best straight line through this target is flat at 0.499, which is wrong by
0.251 on average, while two neurons with the rule rebuild the tent exactly, with
a biggest gap of zero.

So a network made only of multiplying and adding could have a thousand layers
and would still only be able to draw one straight line, and the thing that
rescues it is the simple rule applied at the end of each neuron, which the next
section finally looks at properly.

---

## 5. The rectified linear unit

The rule that section 4 kept putting between the layers has a name. It is called
the **activation function**, which is a rule applied to the weighted sum to give
the neuron's output, and the number that comes out of it is called the neuron's
**activation**. The one used everywhere is the **rectified linear unit (ReLU)**,
and the whole of it is this: if the sum is below 0 give 0, and otherwise give
the sum unchanged.

![A graph of the rectified linear unit, flat at 0 for inputs below 0 and climbing at 45 degrees above 0, beside a table of eight inputs and outputs](../../images/inside-a-network/one-neuron/relu-curve.svg)

An input of -2.000 gives 0.000, an input of -1.000 gives 0.000, an input of
+0.725 gives 0.725, and an input of +2.000 gives 2.000, so every number below 0
is flattened to 0 and every number above it is passed on untouched.

This looks almost too simple to be doing any work, and the reason it does so
much work is the corner at 0. A neuron with this rule is two different things
joined at one point, since on one side of the corner it ignores its inputs
completely and on the other side it follows them exactly. The place where it
changes from one to the other is the elbow that section 3 moved about with the
bias, and once several neurons each have an elbow in a different place, the
elbows can be added up into any shape at all.

![A graph of a smooth bump-shaped curve with a six-piece line and a twelve-piece line drawn over it, the six elbows marked with dotted lines](../../images/inside-a-network/one-neuron/relu-pieces.svg)

Six neurons with elbows at 0.08, 0.25, 0.42, 0.58, 0.75 and 0.92 follow the
smooth curve to within 0.107 everywhere, and twelve of them bring that gap down
to 0.030.

That is the answer to the question section 4 raised, and it is worth saying
plainly. A network can bend because each neuron can switch off, and a network
with more neurons can bend in more places. What it costs is that half of every
neuron's range gives nothing at all, and a neuron whose sum happens to be below
0 for every reading it ever meets is a neuron that never does anything.

![A grid of 64 squares, one per neuron, each holding the percentage of 200 readings that neuron answered above 0, with 25 of them outlined in red and holding 0](../../images/inside-a-network/one-neuron/relu-dead-units.svg)

Of 64 neurons with randomly chosen weights reading 200 simulated moments, 25
never answered above 0 at all, and the average neuron answered on 36.6 per cent
of them; the readings and the weights here are simulated, drawn from a fixed
seed so that the picture can be made again.

A neuron in that state is usually called a dead unit, and it is dead in a strong
sense, because the training methods in the next chapter work by nudging each
weight in the direction that would improve the answer, and a neuron whose output
is 0 for every example gives no direction to nudge in. The reason for that shows
up in the slope of the rule.

![A graph of the slope of the rectified linear unit, which is 0 to the left of zero and 1 to the right of it, with open circles at the jump](../../images/inside-a-network/one-neuron/relu-slope.svg)

To the left of 0 the slope is 0, which means that moving the sum a little
changes nothing at all, and to the right of 0 the slope is 1, which means the
output follows the sum exactly, and at the point 0 itself there is no single
slope because the rule jumps.

That flat left half and that jump at 0 are the two things the newer rules in the
next section change.

---

## 6. GELU and SiLU, and why networks use them now

The rectified linear unit has those two awkward places, so two smoother rules
have taken over much of its work in the models built today, and both of them
keep its shape while rounding off its corner. They are the **Gaussian error
linear unit (GELU)** and the **sigmoid linear unit (SiLU)**, which is also
called swish, and both of them multiply the sum by a number between 0 and 1 that
grows as the sum grows, instead of switching flatly between 0 and 1.

![The three rules drawn on the same axes from minus four to plus four, with an inset showing the left half close up, beside a table of their outputs at eight inputs](../../images/inside-a-network/one-neuron/three-rules.svg)

All three give almost the same answer for a sum of +2.000, which is 2.0000 for
the rectified linear unit, 1.9545 for GELU and 1.7616 for SiLU, but on the left
they differ, because at -1.000 the rectified linear unit gives 0.0000 while GELU
gives -0.1587 and SiLU gives -0.2689; the lowest GELU ever gives is -0.170 and
the lowest SiLU is -0.278.

The small dip below 0 is the first real difference, and it means that a neuron
whose sum is a little below 0 still gives a small answer rather than nothing at
all, so it is never completely silent and never completely dead. The second
difference is in the slope, which is what the training methods in the next
chapter actually use.

![A graph of the slope of each of the three rules, with the rectified linear unit jumping from 0 to 1 and the other two changing smoothly and dipping below 0 on the left](../../images/inside-a-network/one-neuron/three-slopes.svg)

The rectified linear unit's slope is 0 at an input of -2 and 1 at +2 with a jump
between them, while GELU's slope runs from -0.0852 at -2 to +1.0852 at +2 and
SiLU's from -0.0908 to +1.0908, and both of them dip below 0 on the left, GELU
down to -0.129 near -1.42 and SiLU down to -0.100 near -2.40.

Put back on the neuron from section 1, with the opening and the brightness held
still and the distance sweeping, the three rules give three slightly different
answers, and the difference is only visible near the elbow.

![Two graphs of the neuron's output against distance under all three rules, the right one zoomed in on the elbow at 0.7825 metres where GELU and SiLU dip a little below zero](../../images/inside-a-network/one-neuron/neuron-three-rules.svg)

At our reading of 0.42 metres the sum of +0.725 becomes 0.7250 under the
rectified linear unit, 0.5552 under GELU and 0.4884 under SiLU, and at 0.85
metres, where the sum is -0.1350, the rectified linear unit gives exactly 0
while GELU gives -0.0603 and SiLU gives -0.0630.

So why use the smooth ones rather than the obvious alternative, which is the
rectified linear unit that is simpler and older? Because the smooth change in
slope gives the training methods something to work with everywhere instead of
nothing on one side and a jump in the middle, and because in practice the large
models built today train a little more steadily with them. Most transformer
models, which the chapter [the
transformer](../06_the-transformer/02_a-transformer-block.md) explains, use GELU
or SiLU inside, and the rectified linear unit remains common in smaller vision
models and anywhere speed matters most.

What they cost is arithmetic. The rectified linear unit is a single comparison
against 0, while GELU and SiLU both need a curve that a computer works out with
an exponential, which takes several times as long per number. That sounds
expensive until you count how often each thing happens inside one layer.

![Two bar charts, the left showing 1,048,576 multiply-adds against 1,024 uses of the rule in a 1024 into 1024 layer, the right showing the extra work as a percentage for rules costing 1, 5, 10 and 20 multiply-adds](../../images/inside-a-network/one-neuron/activation-cost.svg)

A layer with 1,024 inputs and 1,024 neurons does 1,048,576 multiply-adds and
uses the rule only 1,024 times, which is one use of the rule for every 1,024
multiply-adds, so even a rule that costs as much as 20 multiply-adds adds only
1.95 per cent to the work of that layer.

That picture quietly introduces the subject of the next page, which is that a
layer of 1,024 neurons has over a million weights in it, and that those weights
are arranged in a grid that a computer multiplies in one go.

---

## 7. Where to read next

- [Layers and depth](02_layers-and-depth.md) is the next page, and it joins many
  copies of this neuron into a layer, stacks the layers, and explains what each
  extra layer adds and what it costs.
- [The shape of the numbers](03_the-shape-of-the-numbers.md) explains how those
  weights are stored and multiplied, and why the hardware is built the way it
  is.
- [What a network can learn](04_what-a-network-can-learn.md) picks up the
  argument of section 4 and shows why stacking layers with a rule between them
  can follow any shape at all.
- [The score of being wrong](../03_how-training-works/01_the-score-of-being-wrong.md)
  starts the chapter that finds the weights and biases this page chose by hand.
- [Backpropagation](../03_how-training-works/03_backpropagation.md) explains why
  the slopes drawn in sections 5 and 6 matter so much.
- [Inside a neural network](../../07_learned-models/01_what-models-are/03_inside-a-neural-network.md)
  is the short version of the same ideas in the catalogue of models, and it
  carries on into the layer types used for pictures and sentences.

---

## 8. Using it in Python

Everything on this page is one line of PyTorch, which is the library most of
this book's models are built with. The code below builds the same neuron as
section 1, puts the same three readings through it, and then checks the
arithmetic of sections 2, 5 and 6 against the numbers printed above.

```python
import torch
from torch import nn

neuron = nn.Linear(in_features=3, out_features=1)   # section 1: 3 weights + 1 bias
with torch.no_grad():                               # fix them by hand, as this page did
    neuron.weight.copy_(torch.tensor([[-2.0, 1.5, 0.8]]))
    neuron.bias.copy_(torch.tensor([0.5]))

readings = torch.tensor([[0.42, 0.55, 0.30]])       # distance, opening/100, brightness/255
total = neuron(readings)                            # section 2: the weighted sum
print(total.item())                                 # 0.7250000238418579
print(sum(p.numel() for p in neuron.parameters()))  # 4

print(torch.relu(total).item())                     # section 5: 0.7250000238418579
print(torch.nn.functional.gelu(total).item())       # section 6: 0.5552042722702026
print(torch.nn.functional.silu(total).item())       # section 6: 0.48836731910705566

below = torch.tensor([-0.135])                      # the sum at 0.85 m, from section 6
print(torch.relu(below).item())                     # 0.0
print(torch.nn.functional.gelu(below).item())       # -0.06025080755352974
```

The class is called `nn.Linear` rather than `nn.Neuron` because it is written to
hold a whole layer of neurons at once, and asking for one output is the way to
get a single neuron out of it. The library gives you the weights, the bias, the
multiplying and the adding, and when a model is trained it also gives you the
machinery that changes those numbers; you never write the arithmetic of section
2 yourself.

The numbers printed differ from the ones in this page in the last few digits,
and that is not a mistake. PyTorch works in a number format called float32 that
keeps about seven digits, so 0.725 comes back as 0.7250000238418579, and the
page [the shape of the numbers](03_the-shape-of-the-numbers.md) explains that
format and the smaller ones that models are run in.

What you have to decide is none of the arithmetic and all of the shape. You
choose how many inputs the layer takes and how many neurons it has, which the
next page is about, and you choose which rule to apply after it, which section 6
weighed up. You do not choose the weights or the bias, because training chooses
those, and choosing them by hand as this page did is only useful for seeing what
they do.
