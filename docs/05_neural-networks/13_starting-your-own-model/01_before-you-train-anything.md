# Before you train anything

The page before this one, [world models](../12_models-that-act/04_world-models.md), was the
last of the pages that take a family of model apart and show what it does inside. Together
with every page before it, it leaves you knowing what a neuron does, what a loss is, what a
transformer is for and what a policy gives back when it looks at a camera picture. It also
leaves one question open, and it is almost certainly the question that brought you here: you
would like to make one of these, so where do you start?

This chapter answers that, and it is practical from here to its last page. This first page is
the one that saves a month, because the month people lose is hardly ever lost inside the
training loop. It is lost before training starts, on a job nobody wrote down clearly, measured
by a number nobody agreed on, against nothing at all, using examples nobody looked at, split
in a way that quietly hands the answers to the model. So the page goes through five decisions
in the order you should make them: whether a model is the right answer at all, how to write
the job down as what goes in, what comes out and the one number that says it worked, which
cheap baselines have to be beaten first, how few examples you can honestly start with, and how
to split those examples before a single weight changes.

It assumes you know what weights, a loss and a held-out set are, and that you have never
started a model of your own. You should have read [why not just write the
rules](../01_what-learning-means/01_why-not-just-write-the-rules.md), because section 1 returns
to the question that page opened and answers it with measurements.

Everything below is measured on one simulated work cell. An arm picks small parts off 40 trays
of 6 parts each, and the camera measures each part 12 times as the arm comes down, so the
recording holds 240 parts and 2,880 frames. That data is invented by a seeded random number
generator, and everything done to it, including the rules, the baselines and the small
networks, is real arithmetic. The script is
[`docs/diagrams/starting_your_own_model_1.py`](../../diagrams/starting_your_own_model_1.py).

## Contents

1. [Is a model the right answer at all](#1-is-a-model-the-right-answer-at-all)
2. [The job written down as three things](#2-the-job-written-down-as-three-things)
3. [The baseline a model has to beat](#3-the-baseline-a-model-has-to-beat)
4. [The first hundred examples](#4-the-first-hundred-examples)
5. [The split, decided before any training](#5-the-split-decided-before-any-training)
6. [The sheet you should have filled in](#6-the-sheet-you-should-have-filled-in)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. Is a model the right answer at all

The first of those five decisions comes before all the others, and the test for it is short.
If a person can write the rule down in an afternoon, and the numbers in that rule do not
change, then write the rule, because a model is for the jobs where nobody can
write the rule at all. The first job in this cell is on the easy side of that line: the arm
needs to know whether its gripper is holding anything, from how far apart the fingers are in
millimetres and how much current the motor is drawing in amperes.

![A scatter of finger gap against motor current, with grey points for an empty gripper and blue points for a held part, cut by three red threshold lines, beside a bar chart of 99.7 per cent for the rule and 99.6 per cent for a network](../../images/starting-your-own-model/before-you-train-anything/written-rule-works.svg)

The rule "the current is above 0.45 amperes and the fingers are 1.5 to 34 millimetres apart"
is right on 99.7 per cent of held-out readings, and a trained network gets 99.6 per cent.

Anybody can read those three numbers off the plot in a few minutes, and no model beats a rule
that is already right nearly every time. Robot jobs on this side include counting gripper
closes, stopping the arm when a force passes a limit, turning encoder counts into an angle and
refusing a target outside the reachable space, and in each a person knows the rule and why
each number in it is what it is. The second job is not like that, because the arm has to
choose between a pinch, a wrap and a suction cup, and the right grip depends on all five
measurements together.

![A scatter of measured width against measured shine with points coloured by the right grip, cut by two dashed hand-chosen thresholds, beside a bar chart of how much of each grip the hand rule finds](../../images/starting-your-own-model/before-you-train-anything/written-rule-fails.svg)

A sensible hand-written rule gets 75.0 per cent of held-out frames right by finding 93.8 per
cent of the wraps and 84.5 per cent of the suctions while getting only 50.9 per cent of the
pinches.

The three colours mix wherever you cut, which is what the bar chart is paying for, and the
obvious reaction is to add conditions. Jobs on this side of the line include choosing a grip
for an unfamiliar part, finding parts in a cluttered tray picture and telling a chipped part
from a sound one.

![A chart of accuracy against the number of conditions in the rule, where the holding job jumps to 98.7 per cent after one condition and the grip job climbs to 74.0 per cent after five and then stops, with the five thresholds listed](../../images/starting-your-own-model/before-you-train-anything/conditions-to-get-there.svg)

One condition finishes the holding job at 98.7 per cent, while the grip job climbs from 37.5
per cent with none to 46.0 with one, 69.8 with three and 74.0 with five, after which seven
more change nothing.

The conditions in that second curve were not written by a person. A search went through a
recording of 144 parts and picked each threshold to cut the most mistakes, arriving at a width
of 48.8 millimetres and a mass of 19.5 grams, which nobody could have written down beforehand.
That is the real test hiding inside the first one, because the moment you need a recording to
set the numbers in your rule you are already fitting a model, and a worse one. The other half
of the test is whether the rule stays written.

![Two charts: accuracy of the holding rule falling as the current sensor drifts while the re-measured threshold stays flat, and the threshold the training readings pick falling in a straight line with the drift](../../images/starting-your-own-model/before-you-train-anything/the-rule-that-changed.svg)

When the brushes wear and the current sensor reads 0.18 amperes low, the rule left at 0.45
falls from 99.7 per cent to 93.9, and measuring the threshold again brings it back to 99.2.

That is the honest cost of a rule: it usually fails by drifting rather than by being wrong,
and somebody has to notice and measure it again. The repair is one number and takes minutes, a
far smaller bill than retraining, so drift is no reason to reach for a model. A model is the
answer only when nobody can write the rule at all.

---

## 2. The job written down as three things

Section 1 settled that the grip job needs a model, but "choose the right grip" is not yet a
job. A job is three things written down: exactly what goes in, with its units and its count of
numbers; exactly what comes out; and the one number that says whether it worked. What goes in
has to be counted rather than described, because the count decides what the model costs before
you have trained anything.

![Two log-scale bar charts: the numbers in one example for four possible inputs, 5, 7, 150,528 and 602,112, and the weights a first layer of 16 units would need for each, 80, 112, 2,408,448 and 9,633,792](../../images/starting-your-own-model/before-you-train-anything/input-and-output-written-down.svg)

Five measured numbers is five numbers, one 224 by 224 colour picture is 150,528 and four of
those is 602,112, so a first layer of 16 units needs 80 weights in the first case and
2,408,448 in the third.

The five numbers here are the width in millimetres, the height in millimetres, the estimated
mass in grams, how shiny the surface is from zero to one, and how flat the top face is on the
same scale. Units matter, because feeding a working system the same quantity in a different
unit is the commonest way to break it later. What comes out is as short: one of pinch, wrap
and suction. The third thing is the one written vaguely, usually as "the arm should pick
things up reliably", which cannot be measured until somebody says what counts as a success.

![Three bars from the same 200 attempts: 92.0 per cent closed on something, 72.5 per cent reached the box in time, and 71.5 per cent did so undamaged](../../images/starting-your-own-model/before-you-train-anything/vague-becomes-measurable.svg)

Of one recording of 200 simulated attempts, 184 ended with the gripper closed on something,
145 with the part in the box within ten seconds and 143 undamaged as well, which is 92.0,
72.5 and 71.5 per cent of the same attempts.

So the worked version of the vague sentence is this: the input is the five measured numbers
for one part in the units above, the output is one of pinch, wrap and suction, and the one
number is the share of attempts in which the part ends up in the box within ten seconds and
undamaged, counted over parts from trays nobody trained on. Somebody who was not in the room
can measure that, and the gap between the first bar and the last is 20.5 points of nothing. A
second way to go wrong is to pick a number that a useless answer already scores well on, which
this cell's crack inspection shows, since about one part in ten is cracked.

![Bars showing 90.0 per cent accuracy and 0.0 per cent of cracks found for always answering "no crack" against 93.8 per cent and 75.0 per cent for a real detector, beside a histogram of detector scores](../../images/starting-your-own-model/before-you-train-anything/the-wrong-one-number.svg)

Because only 24 of the 240 parts are cracked, always answering "no crack" is 90.0 per cent
accurate while finding none, while a real detector scores 93.8 per cent accuracy and finds
75.0 per cent of the cracks.

Accuracy is worthless as the one number there, because what you care about is the share of
cracked parts found. The last thing to settle is how many attempts the number is measured
over, because a success rate from a few tries is noise.

![A chart of the spread of reported success rates for 20, 60, 200 and 600 trials of a model that really succeeds 70 per cent of the time, with the 95 per cent intervals marked](../../images/starting-your-own-model/before-you-train-anything/how-many-trials.svg)

For a model that really succeeds on 70 attempts in 100, twenty trials give a range of
possible answers 37.3 points wide, sixty trials 22.6 points, two hundred trials 12.6 points
and six hundred trials 7.3 points.

Twenty trials on a real arm is an afternoon, and that afternoon buys a number which could be
anywhere from 48 to 86 per cent for the very same model. Deciding in advance how many attempts
the final measurement needs is part of writing the job down, and it says how much arm time the
project will cost.

---

## 3. The baseline a model has to beat

The job from section 2 now has an input, an output and a number, so anything at all can be
scored on it. A **baseline** is a cheap answer that took no training, and its score is what a
model has to beat before anybody is allowed to be pleased. Three are worth running every time:
always giving the most common answer, which measures how unbalanced the job is; the rule
somebody would have written, from section 1; and **nearest neighbour**, which stores every
training example and answers a new one by copying the answer of the stored example whose
numbers are closest.

![A bar chart of five scores on the grip job: 37.5 per cent for the most common class, 75.0 for the written rule, 63.0 for nearest neighbour on the raw numbers, 79.2 for nearest neighbour on scaled numbers and 80.1 for a small network](../../images/starting-your-own-model/before-you-train-anything/three-baselines-classification.svg)

On the same 1,728 training and 576 held-out frames, always answering "pinch" scores 37.5 per
cent, the written rule 75.0, nearest neighbour on the raw numbers 63.0, nearest neighbour
after scaling each number to the same spread 79.2, and a small trained network 80.1.

That is the honest shape of most first attempts. The network wins by 1.0 points over a method
that fits in two lines and does no training, and at 78 per cent somebody would still have
called it a success. The two nearest-neighbour bars differ only in that the second divides
each number by its spread first, so a width in millimetres stops drowning a shininess between
zero and one, and that change is worth 16.1 points. The second half of the job asks for a
number in newtons instead, and there the baselines change.

![A bar chart of average error in newtons for predicting the average, a written physics rule, nearest neighbour and a network, beside a scatter showing the physics rule's error growing with shininess](../../images/starting-your-own-model/before-you-train-anything/three-baselines-regression.svg)

Always predicting the average squeeze force is wrong by 0.550 newtons on average, a rule
from school physics is wrong by 0.202, nearest neighbour by 0.175 and a small network by
0.144, while the forces themselves spread by 0.921 newtons.

That physics rule is one line, the mass times gravity times a safety factor divided by twice an
assumed friction, and its error comes within six hundredths of a newton of the network's while
costing nothing to write. It is honest about where it fails too, since its error grows with
shininess, because shiny parts are more slippery than its fixed friction number assumes.
Whenever physics or geometry gives an approximate answer, that answer is a baseline, and a
baseline does not stand still while the model learns.

![A chart of held-out accuracy against the number of training parts on a log scale, with the network's curve rising past the flat lines for the written rule and the most common class](../../images/starting-your-own-model/before-you-train-anything/baseline-moves-with-data.svg)

Trained on 4 parts the network scores 47.6 per cent, on 16 parts 60.9, on 32 parts 69.5 and
on 64 parts 78.8, which is the first point at which it passes the written rule's 75.0.

Until sixty-four parts have been recorded the model is worse than the rule, so a project that
stopped at thirty-two would have concluded that the model does not work when all it had shown
was that the recording was too small. Compare the two at the same amount of data every time,
because the curves cross somewhere and you want to know where.

![A grouped bar chart of how much of each grip the four methods find, where the most common class gets all the pinches and none of the others](../../images/starting-your-own-model/before-you-train-anything/baseline-per-class.svg)

The most common class reaches 37.5 per cent by finding every pinch and no wrap or suction at
all, while the written rule finds 50.9, 93.8 and 84.5 per cent of the three and the network
finds 72.7, 85.9 and 66.7.

Reading a score one class at a time is how you find out what a method is really doing, and here
it shows the rule and the network failing on different parts of the same job, which tells you
where the next examples should come from.

---

## 4. The first hundred examples

Section 3 showed a model that needed sixty-four parts before it passed a one-line rule, so the
obvious plan is to record as many as possible, and that plan is wrong in a specific way. A
hundred examples somebody has looked at are worth more than ten thousand nobody has, because
the faults that ruin a model are visible by eye, but only if somebody looks. The first question
is how few you can honestly start with, and the answer comes from counting kinds of situation
rather than examples.

![A curve of how many of ten kinds of part have been seen at least twice against the number of parts recorded, beside a bar chart of how many of the 240 parts fall into each kind](../../images/starting-your-own-model/before-you-train-anything/enough-to-cover-the-cases.svg)

Ten combinations of grip, surface and top shape occur among the 240 parts, and a recording of
8 parts has seen 2.1 of them at least twice, 24 parts 6.0, 48 parts 7.6, 100 parts 8.9 and
200 parts all ten.

That is a better argument for a number than any round figure, because it is specific to your
cell: three grips, shiny and dull surfaces and flat and curved tops make ten kinds here, while
six orientations and four lighting conditions would make a different number. So count the
kinds the robot will meet, ask for a few examples of each, and record that many. Then look at
a hundred of them rather than ten, because of simple arithmetic.

![Three curves of the chance of meeting a fault at least once against the number of examples you open and look at, for faults affecting 20, 5 and 2 per cent of examples](../../images/starting-your-own-model/before-you-train-anything/faults-in-the-first-hundred.svg)

A fault affecting one example in twenty shows up in a sample of ten only 40.1 per cent of the
time, in thirty 78.5 per cent and in a hundred 99.4 per cent, while a fault affecting one in
fifty needs a hundred to reach 86.7 per cent.

Looking at ten examples feels like looking and misses three faults in five, while a hundred
catches nearly everything for an hour of somebody's time. The three faults planted in this
cell are the three that happen.

![A bar chart of held-out accuracy for clean data, mislabelled parts, a stuck sensor reading, 96 different parts and 24 parts recorded four times, beside a scatter showing the stuck reading as a flat line](../../images/starting-your-own-model/before-you-train-anything/what-the-faults-cost.svg)

The recording as it stands gives 80.1 per cent, labelling 10 of the 144 parts wrongly gives
71.3, freezing the shininess reading on 8 of the 24 training trays gives 78.0, and 24 parts
recorded four times each give 65.9 against 71.4 for 96 different parts.

A wrong label costs 8.8 points from 10 parts in 144, and you find it by opening examples and
asking whether you agree with the answer beside them. A stuck sensor costs 2.1 points here and
far more in general, and you find it by plotting each input against each other and looking for
a flat line, which the right-hand picture shows as a row of red dots. The third fault is the
least obvious, since the same 1,152 frames are worth 5.5 points more from 96 different parts
than from 24 recorded four times each, because a fourth recording of a part teaches almost
nothing. One thing more is worth checking: the quality of the answers themselves.

![A bar chart of how often two labellers give the same answer, grouped by how clearly one grip is best, beside a histogram of how many parts sit near the boundary](../../images/starting-your-own-model/before-you-train-anything/labellers-disagree.svg)

Two people labelling the same 240 parts agree on 90.0 per cent of them, but on the 27 parts
where the best grip is barely ahead of the next they agree only 48.1 per cent of the time, and
on the clearest parts 100 per cent.

That 90.0 per cent is a ceiling, because a model trained on one person's answers and judged
against another's cannot beat what the two people manage against each other. Knowing it
beforehand stops you chasing ten points that are not there, and says the cheapest improvement
is often to agree what the borderline cases mean. With the examples recorded and looked at,
one decision is left.

---

## 5. The split, decided before any training

Those examples cannot all be used for training, and how they are divided has to be settled
before any weight changes, because if you divide them after seeing the results you will divide
them in whatever way makes the results look best. Why a held-back set is needed at all is
explained in [overfitting and
generalisation](../04_making-training-work/01_overfitting-and-generalisation.md); what belongs
here is the decision itself, and the robot-specific trap in it, which is that a robot records
continuously and so produces many examples of the same thing.

![A bar chart of held-out accuracy under three kinds of split, with whiskers, beside a histogram showing how much closer the nearest frame of the same part is than the nearest frame of any other part](../../images/starting-your-own-model/before-you-train-anything/three-splits-three-scores.svg)

Over five draws of each kind of split the same model scores 100.0 per cent when frames are
divided at random, 81.6 per cent when whole parts are held out and 80.6 per cent when whole
trays are, because the nearest frame of the same part sits 13.7 times closer than any other.

The first of those three is the trap. Those twelve frames are nearly the same picture, so
dividing them at random puts eleven in the training set and the twelfth in the held-out set,
and the model answers the twelfth by remembering the eleventh, scores a hundred per cent and
has learned nothing. The second and third sit inside each other's spread here, which is honest
rather than convenient, because the model has already met 24 trays and a twenty-fifth is not
much of a surprise, while in a cell whose scenes differ more that third bar falls further.

The unit you split along is whatever you want the model to work on next. By frame it answers
"how will it do on a frame it has seen", which is a question nobody has; by part, "on another
attempt at a part it has met"; by tray, "on a tray it has never seen", which is usually the
one you care about.

![Two rows of bars, one bar per tray, showing how far that tray's width reading and shine reading sit from the part's real width and real shine, with the held-out trays drawn in red](../../images/starting-your-own-model/before-you-train-anything/trays-differ.svg)

Tray by tray, the width reading sits between 12.1 millimetres under and 9.7 over the part's
real width, while the twelve frames of one part differ from each other by only 0.33.

A tray is therefore a real thing and not a label, because its alignment and its lighting shift
every reading taken on it by far more than the camera's own noise, so a model tested on
held-out trays is asked whether it copes with an alignment it has not met. Once the unit is
chosen the split is written down and never touched again, which means naming the trays rather
than saying "twenty per cent".

![A grid of 40 trays of 6 parts each, coloured pale blue for training, orange for validation and red for test, with the counts in the key](../../images/starting-your-own-model/before-you-train-anything/the-split-written-down.svg)

Twenty-four trays, 144 parts and 1,728 frames, are for training, eight trays with 48 parts are
for choosing between models, and the eight trays numbered 0, 4, 5, 10, 14, 15, 16 and 37 are
read once at the end.

There are three sets rather than two because the set you choose settings on cannot also be the
set you report, or the number reported would be the number you chose on. The last thing to
decide is how big that final set has to be, which follows from section 2.

![A chart of how often the better of two models is correctly chosen against the number of held-out attempts given to each, for a ten-point gap and a five-point gap](../../images/starting-your-own-model/before-you-train-anything/how-many-held-out-attempts.svg)

Choosing between a model that really succeeds 80 per cent of the time and one that manages 70
is right 77.0 per cent of the time on 20 attempts each and 98.2 per cent on 160, while telling
75 from 70 needs 320 attempts each to be right 92.3 per cent of the time.

So the size of the held-out set is set by the smallest difference you need to see. Two
candidates usually differ by about five points once a project is going, and a held-out set of
a few dozen cannot tell those apart, so every comparison made on it is close to a coin toss.

---

## 6. The sheet you should have filled in

Everything in the five sections above fits on one side of paper, and each line on that sheet
rules out one way of spending a month and having nothing to show. Two of the lines need a
measurement of their own, and the first is the target: the score the model has to clear, and
the amount by which it has to clear it.

![A bar chart of three networks trained on 6, 24 and 144 parts, each with its 95 per cent interval, against the written rule's score and its shaded interval](../../images/starting-your-own-model/before-you-train-anything/the-gate.svg)

Scored one vote per part on the same 48 held-out parts, the written rule gets 36 right, which
is 75.0 per cent with a range of 61.2 to 85.1, and networks trained on 6, 24 and 144 parts get
29, 41 and 38, which is 60.4, 85.4 and 79.2 per cent.

The network on 24 parts looks like the winner and has proved nothing, because its range of
72.8 to 92.8 and the rule's range of 61.2 to 85.1 overlap from 72.8 to 85.1. With 48
held-out parts nothing there is far enough from the rule to be believed, so the honest
conclusion is not that the model works or that it does not, but that the held-out set is too
small to say. Writing the target down beforehand is what makes that conclusion available,
because the alternative is to see 85.4 against 75.0, declare success and find out on the arm.
The second line names which set will be read once, because comparing candidates uses up
whatever set you compare them on by a measurable amount.

![A chart of two curves against the number of candidate models compared: the score of the chosen model on the set it was chosen on, rising, and its score on the set read once, flat](../../images/starting-your-own-model/before-you-train-anything/best-of-k.svg)

With one candidate the chosen model scores 80.1 per cent where it was chosen and 80.0 where it
is finally read, the best of 4 gives 82.8 against 78.7, and the best of 10 gives 83.5 against
78.2, a gap of 5.3 points.

The flat lower line is the point. Comparing more candidates does not make the chosen model
better, only its score on the comparison set, because whichever candidate caught that set on a
good day wins. The set you compare on is used up by the comparing, so the final number has to
come from a second set nobody has touched. The size of what these lines defend against is
worth seeing in one place.

![A horizontal bar chart of four shortcuts and how many points of free score each one gives: the random frame split, the loose definition of success, accuracy on an unbalanced job, and reading the score off the set you chose on](../../images/starting-your-own-model/before-you-train-anything/what-each-line-rules-out.svg)

Splitting frames at random rather than by tray adds 19.4 points to the reported score, calling
"the gripper closed" a success adds 20.5, reporting accuracy on a job where one part in ten is
cracked adds 90.0, and reading the score off the set the model was chosen on adds 5.3.

Those four numbers were measured on this page rather than guessed, and together they add up to
more than the whole of the model's ability. None of them is dishonesty, which is why the sheet
exists: each is a reasonable thing to do when nobody wrote down beforehand what would be done,
and each is invisible in the finished number.

![A table of eleven rows, each a line of the sheet with its value filled in: the job, the input, the output, the one number, what it is measured on, the target, three baselines, the split and the agreement between labellers](../../images/starting-your-own-model/before-you-train-anything/the-sheet-filled-in.svg)

The sheet holds eleven lines, four of them decisions and seven of them measurements, and the
longest line is the sentence saying what the job is.

Fill those eleven in for your own job and you will know, before training anything, what the
model has to beat, how many held-out examples will judge it, how far the labels can be
trusted, and which set you may read only once. The next page starts the work.

---

## 7. Where to read next

- [The order of the work](02_the-order-of-the-work.md) is the next page, and it says what to
  run first on the job you have just written down, in the order that finds faults most cheaply.
- [What to reuse and what to train](03_what-to-reuse-and-what-to-train.md) answers the question
  this page leaves open, which is whether to train a model at all or start from somebody else's.
- [Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
  explains why the split of section 5 is needed and the other ways information leaks across it.
- [Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  takes the one number of section 2 onto a real arm, where trials cost time.
- [Nearest neighbours and locally weighted regression](../../07_learned-models/02_classical-machine-learning/02_most-used/04_nearest-neighbours-and-locally-weighted-regression.md)
  is the catalogue entry for the third baseline of section 3, including when it is worth
  keeping as the finished answer.
- [Evaluation and failure](../../07_learned-models/10_making-models-work-on-an-arm/02_most-used/03_evaluation-and-failure.md)
  lists what people actually report when they measure a model on an arm, and what those
  reports leave out.

---

## 8. Using it in Python

The page's three baselines and one small model are short enough to write out in full, so the
code below builds a simpler version of the same job, splits it by part rather than by frame as
section 5 insists, runs the three baselines, and only then trains anything.

```python
import numpy as np
import torch
from torch import nn

rng = np.random.default_rng(0)
P, F = 240, 12                                       # 240 parts, 12 frames of each

width = rng.uniform(8, 95, P); flat = rng.random(P); shine = rng.random(P)
mass = width * rng.uniform(0.5, 2.5, P)              # section 2: what goes in
props = np.stack([width, mass, shine, flat], 1)
score = np.stack([1.3 - 1.6 * width / 95 - 0.9 * mass / 240,
                  0.1 + 1.5 * width / 95 + 1.1 * mass / 240 - 0.8 * flat,
                  -0.6 + 3.2 * flat * shine + 0.5 * width / 95], 1)
grip = score.argmax(1)                               # section 2: what comes out

X = np.repeat(props, F, 0) + rng.normal(0, [1.4, 3.0, 0.05, 0.07], (P * F, 4))
y = np.repeat(grip, F)
part = np.repeat(np.arange(P), F)
test = part >= 180                                   # section 5: split by part, not frame

maj = np.bincount(y[~test]).argmax()                 # section 3: baseline one
print('most common class  %.1f%%' % (100 * (y[test] == maj).mean()))
rule = np.where(X[:, 0] > 45, 1, np.where((X[:, 3] > .5) & (X[:, 2] > .4), 2, 0))
print('written rule       %.1f%%' % (100 * (rule[test] == y[test]).mean()))
d = ((X[test][:, None] - X[~test][None]) ** 2).sum(2)
print('nearest neighbour  %.1f%%' % (100 * (y[~test][d.argmin(1)] == y[test]).mean()))

Z = torch.tensor((X - X[~test].mean(0)) / X[~test].std(0), dtype=torch.float32)
t = torch.tensor(y)
net = nn.Sequential(nn.Linear(4, 24), nn.Tanh(), nn.Linear(24, 3))
opt = torch.optim.Adam(net.parameters(), lr=0.02)
for step in range(600):                              # section 6: training, allowed at last
    loss = nn.functional.cross_entropy(net(Z[~test]), t[~test])
    opt.zero_grad(); loss.backward(); opt.step()
print('small network      %.1f%%' % (100 * (net(Z[test]).argmax(1) == t[test]).float().mean()))
```

That program prints `most common class  53.3%`, `written rule       76.1%`,
`nearest neighbour  64.7%` and `small network      91.1%`. The network wins by a far wider
margin than the 0.9 points of section 3, and the reason is worth knowing: this simplified cell
has no trays in it, so a held-out part suffers no tray-to-tray variation. That is the
difference between a job as a tutorial writes it and the same job as it comes off a real
machine, and it is the commonest reason a result that looked excellent on a laptop disappoints
on the arm.

PyTorch is doing two things in those lines and nothing else. It works out the gradients of the
loss with respect to every weight, which is `loss.backward()`, and it applies the update,
which is `opt.step()`. Everything else is NumPy and arithmetic, and the three baselines take
one line each, which is the point: they cost less than the time spent reading about them.

What no library decides is any line of the sheet from section 6. You choose what goes in, and
the count of numbers fixes the size of the first layer. You choose the one number, and section
2 showed the same 200 attempts scoring 92.0 or 71.5 per cent on that choice alone. You choose
the split, and changing the single line `test = part >= 180` to a mask over frames chosen at
random is the fastest way to see what section 5 measured, because the printed score will jump
and nothing will have improved. Run that experiment before you trust any number here.
