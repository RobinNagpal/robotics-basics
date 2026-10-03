# Diffusion: making an answer out of noise

The page before this one, [making a model smaller and
faster](../07_pretraining-and-adapting/04_making-a-model-smaller-and-faster.md),
finished the run of pages about getting a trained model ready to use, and every
one of those pages quietly assumed that the model's job was to look at an input
and give back the one right answer. This page is where that assumption breaks,
because a great many of the jobs a robot arm has to do have several right
answers at once, and a model that gives back one answer for them gives back a
wrong one.

So this page answers three questions. Why is making something up a different
job from predicting it? How does a **generative model**, which is a model that
produces a whole new example rather than a single answer, actually work? And
what does the most widely used kind of generative model, called **diffusion**,
cost you in time?

It is for a reader who knows what a [neural
network](../02_inside-a-network/01_one-neuron.md) is, what a
[loss](../03_how-training-works/01_the-score-of-being-wrong.md) is and what
[training](../03_how-training-works/04_the-training-loop.md) does. It does not
assume you have met any generative model before, so every word on the page is
explained where it first appears.

Everything below is worked through on one small example that you can see all of
at once: a robot arm moves its gripper past a round obstacle, and the recorded
demonstrations go either above it or below it, so each waypoint is a point in
two dimensions and every step of the method can be drawn rather than described.
The data is simulated, and every number in every picture is worked out and
printed by `docs/diagrams/models_that_generate.py`, including the timings,
which were measured on the machine that drew the pictures.

## Contents

1. [Why generating is a different job from predicting](#1-why-generating-is-a-different-job-from-predicting)
2. [Adding noise, one small step at a time](#2-adding-noise-one-small-step-at-a-time)
3. [Training one network to name the noise](#3-training-one-network-to-name-the-noise)
4. [The reverse walk, from a round blob back to the arcs](#4-the-reverse-walk-from-a-round-blob-back-to-the-arcs)
5. [Conditioning: the same denoiser told what to make](#5-conditioning-the-same-denoiser-told-what-to-make)
6. [Guidance: pushing further in the direction the condition adds](#6-guidance-pushing-further-in-the-direction-the-condition-adds)
7. [The cost: many passes through the network instead of one](#7-the-cost-many-passes-through-the-network-instead-of-one)
8. [Where to read next](#8-where-to-read-next)
9. [Using it in Python](#9-using-it-in-python)

---

## 1. Why generating is a different job from predicting

Everything in this book so far has trained a model by showing it an input,
asking for an answer and scoring how far that answer was from the right one.
That works whenever there is one right answer, but it quietly falls apart as
soon as there are two, and the example below is the smallest honest case of
that.

![6,000 waypoints forming two arcs that pass above and below a round obstacle at the origin, with a start marker on the left and a goal marker on the right](../../images/models-that-generate/diffusion/two-ways-round.svg)

The 6,000 recorded gripper waypoints form two separate arcs, because 2,959 of the demonstrations went above the obstacle and 3,041 went below it.

The arm starts on the left, finishes on the right and must not touch the round
obstacle in the middle, which has a radius of 0.5 m. Both ways round are
correct, nobody prefers one, and so the recorded demonstrations hold both. The
spread of the waypoints is 0.984 m across and 0.793 m up, which is useful to
know because it means the data is already about one unit wide in each direction.

Now look at what happens where the two answers are furthest apart, which is
directly above and below the obstacle.

![The waypoints within 0.15 m of x equals 0, in two tight clusters at plus and minus 1.4 m, with a cross marking their average inside the obstacle circle](../../images/models-that-generate/diffusion/average-is-wrong.svg)

In the narrow band where x is within 0.15 m of zero, the waypoints above average y = +1.408 m and those below average y = -1.417 m, and the average of all of them together sits at y = +0.109 m, inside the obstacle.

There are 275 waypoints above in that band and 234 below, which is why their
average is not exactly zero, but it makes no difference: +0.109 m is 0.109 m
from the centre of an obstacle whose radius is 0.5 m, so the average answer is
well inside the one place the gripper must never be. This is the whole problem
in one number. The two right answers are both far from the obstacle, and the
thing halfway between them is in it.

A model trained in the ordinary way does not merely risk this answer. It is
driven straight to it.

![A network's fitted curve running flat through the middle of the two arcs and through the obstacle, beside a bar chart showing its squared error is 0.628 against 1.257 for always answering the upper arc](../../images/models-that-generate/diffusion/what-a-predictor-gives.svg)

A small network trained to predict the sideways position from the forward position settles on the average, which spends 29.4 per cent of its path inside the obstacle, and it does so because that answer scores 0.628 against 1.257 for always choosing the upper arc.

The curve the network learned never leaves the band between -0.076 m and
+0.155 m anywhere near the obstacle, so it is effectively the straight line
through the middle. That is not a failure of training, because training did
exactly what it was told. Squared error rewards being close to every example,
and the single number closest to all of the examples at once is their average,
even when no example is anywhere near it.

The last picture of this section shows why, by trying every possible single
answer and scoring each one.

![A histogram of the real sideways positions at x equals zero showing two peaks near plus and minus 1.4 m, beside a parabola of squared error against the chosen single answer with its lowest point at plus 0.110 m](../../images/models-that-generate/diffusion/many-right-answers.svg)

Scoring every possible single answer against the 509 real waypoints in the band gives a curve whose lowest point is y = +0.110 m with a score of 1.988, while answering the upper arc at y = +1.43 m scores 3.732.

So the answer the method prefers is nearly twice as good, by its own score, as
either of the answers that a person would accept. No amount of extra training
data, extra layers or extra patience changes this, because the problem is the
question and not the model. What is needed instead is a model that is asked to
produce *an* answer drawn from the whole set of right ones, rather than *the*
answer, and the rest of this page builds one.

---

## 2. Adding noise, one small step at a time

A generator has to turn something easy into something hard: it has to start
from a shape nobody had to learn, such as plain round random noise, and finish
on the shape the data actually has. Diffusion builds that journey backwards. It
first destroys the data in small steps, writing down exactly what it did, and
then trains a network to undo one of those steps at a time.

Destroying it is the easy half, because adding noise needs no learning at all.
Each step shrinks the point a little towards zero and mixes in a little fresh
random noise, and after enough steps nothing of the original is left.

![Six panels showing the two arcs at steps 0, 20, 40, 60, 80 and 100, losing their shape until the points form a round cloud](../../images/models-that-generate/diffusion/forward-noise-steps.svg)

The same 900 waypoints after 0, 20, 40, 60, 80 and 100 noise steps, with the multiplier on the data falling from 1.000 to 0.003 while the multiplier on the noise rises from 0.000 to 1.000.

Nothing in the picture is a network. At step t the noisy point is simply the
real waypoint multiplied by one number plus a fresh random draw multiplied by
another, and the pair of numbers is fixed in advance for every step. That fixed
pair of numbers, read off step by step, is called the **noise schedule**.

![Two line charts: the data multiplier falling from 1 to 0 and the noise multiplier rising from 0 to 1, crossing at step 50, and the share of the point replaced at each single step rising sharply after step 80](../../images/models-that-generate/diffusion/noise-schedule.svg)

The schedule used here keeps 0.986 of the data at step 10, 0.920 at step 25, 0.703 at step 50, 0.380 at step 75 and 0.003 at step 100, and the two multipliers are equal at step 50, where each is 0.703.

The left half of that picture is the schedule as the forward process uses it,
jumping straight from the real data to step t. The right half is the same
schedule read one step at a time, and it shows that a single early step barely
changes the point while a single late step replaces almost all of it, with the
largest single step replacing 0.959 of the point at step 100. This matters
later, because the network will find the late steps easy and the early ones
hard.

It helps to watch one single waypoint rather than the whole cloud.

![Six coloured curves showing one waypoint's noisy copies drifting away from 1.43 m towards zero as the step rises, beside histograms at steps 25, 50 and 100 widening around that start point](../../images/models-that-generate/diffusion/one-point-walk.svg)

One waypoint at (0.00, 1.43) m has noisy copies that still average +1.338 m with a spread of 0.379 m at step 25, and by step 100 they average +0.061 m with a spread of 0.970 m.

Each coloured line is the same waypoint with one fixed random draw, and the
dashed line is where the waypoint itself has got to once it has been shrunk.
The point does not wander at random; it is pulled steadily towards zero while
the noise around it grows, so by the end the original position has no influence
worth measuring.

That end state is the one the generator will start from, so it is worth
checking that it really is plain noise and not something that still remembers
the arcs.

![Two scatter plots side by side, the data after 100 noise steps and freshly drawn round noise, both round clouds, beside a chart of the spreads in x and y meeting at 1.0](../../images/models-that-generate/diffusion/blob-is-round.svg)

After 100 steps the noisy data has an average of (+0.000, -0.023) and a spread of 1.014 across and 1.020 up, while freshly drawn round noise has an average of (+0.048, +0.008) and a spread of 1.016 in both directions.

The mismatch score between those two clouds is 0.0017, against 0.0014 for two
halves of the real data compared with each other, and that second number is the
floor: it is what you get when two sets of points really do come from the same
place. The mismatch score used throughout this page is one number that is near
zero when two clouds of points look alike and grows when they do not. So after
100 steps the data is indistinguishable from noise, which means a generator can
start from noise without having cheated.

---

## 3. Training one network to name the noise

The forward process from the last section added a known amount of known noise
at every step, which means that for any step there is a training example
nobody had to label: the noisy point, the step number, and the exact noise that
was mixed in. One network is trained to look at the first two and name the
third.

![One waypoint at (0.00, 1.43), the same point shrunk to (0.00, 1.00), an arrow of added noise reaching the noisy point at (0.78, -0.13), and a dashed arrow showing where taking the named noise back out puts the clean waypoint](../../images/models-that-generate/diffusion/noise-prediction-target.svg)

At step 50 the waypoint (0.00, 1.43) is shrunk by 0.703 and a noise draw of (1.10, -1.60) is added with multiplier 0.711, giving the point (0.78, -0.13) that the network is shown.

The network is handed (0.78, -0.13) together with the step number, and it
answers (0.34, -0.08). The real noise was (1.10, -1.60), so it is a long way
out, and the dashed arrow shows the consequence: taking the named noise back
out puts the clean waypoint between the two arcs rather than on either of them.
That is not a bug, and section 4 explains why it is in fact the correct answer.

Training is an ordinary training loop. Each step picks a batch of real
waypoints, picks a random step number for each one, builds the noisy version,
and scores the network on the squared difference between the noise it named and
the noise that was really added.

![A training curve falling steeply from 0.437 to about 0.33 in the first thousand steps and then flattening to 0.301 by step 12,000](../../images/models-that-generate/diffusion/training-curve.svg)

Twelve thousand training steps on batches of 512 examples take about two minutes on one processor core, and the average squared error falls from 0.437 to 0.301.

The curve flattens at 0.301 rather than at zero, and no amount of further
training brings it down, because a large part of that number is not a mistake.
The next picture shows where it comes from.

![Three scatter plots of named noise against real noise at steps 10, 50 and 90, with the points spread widely at step 10 and lying almost on the diagonal at step 90](../../images/models-that-generate/diffusion/predicted-vs-true-noise.svg)

At step 10 the network scores a squared error of 0.59 and its answers agree with the real noise only 0.63 as measured by correlation, while at step 90 the error is 0.02 and the agreement is 0.99.

At step 90 almost nothing of the waypoint is left, so the point the network is
shown is nearly the noise itself and it can read the answer straight off. At
step 10 the opposite holds: the point is almost the original waypoint, and a
great many different small noises could have produced it from a great many
different nearby waypoints. The network cannot know which, so the best it can
do is answer the average of them, and the leftover error is the spread of the
possibilities rather than a failure of learning.

![A curve of squared error against the step the network is asked about, falling from 0.96 at step 1 to 0.00 at step 100, with a dashed line at 1.0 marking what guessing zero would score](../../images/models-that-generate/diffusion/error-by-time.svg)

Measured step by step, the error is 0.96 at step 1, 0.50 at step 25, 0.41 at step 50, 0.12 at step 75 and 0.005 at step 100, so the single hardest step is the very first one.

Guessing zero every time would score 1.0, so at step 1 the network is barely
better than useless, and at step 100 it is nearly perfect. One network covers
all of them, because the step number is one of its inputs, and that is what
lets a single trained model be used a hundred times in a row with a different
job each time.

---

## 4. The reverse walk, from a round blob back to the arcs

Now the pieces fit together. Start from a point of plain round noise, which
section 2 showed is what step 100 looks like. Ask the network what noise is in
it, take some of that noise back out, add a smaller amount of fresh noise, and
you have a point that looks like step 99. Repeat ninety-nine more times.

![Six panels showing 900 points at steps 100, 80, 60, 40, 20 and 0 of the reverse walk, starting as a round cloud and ending on the two arcs](../../images/models-that-generate/diffusion/reverse-walk-panels.svg)

Nine hundred points of pure noise walked back one step at a time: 11.9 per cent of them are inside the obstacle at step 100, 9.4 per cent at step 40, 2.7 per cent at step 20 and 0.1 per cent at the end.

The shape appears late. Two thirds of the way back the cloud is still round,
and only in the last twenty steps do the points pull apart into the two arcs
and clear the obstacle, which is another way of seeing that the early steps
carry most of the fine detail. Here is one of those steps written out in full.

![One point at (0.620, 1.050) moving to a new middle at (0.612, 1.040), with 200 pale draws of the next point scattered around it, beside the same arithmetic written out line by line](../../images/models-that-generate/diffusion/the-step-rule.svg)

Going back from step 40 to step 39 for the point (0.620, 1.050): the network names the noise (0.399, 0.586), the share removed is 0.0224, the new middle is (0.612, 1.040), and fresh noise with a spread of 0.146 is added on top.

Two things are worth noticing in that arithmetic. The step barely moves the
middle of the point, by less than a centimetre, and yet the fresh noise added
on top has a spread fourteen times larger than that movement. So a single step
looks almost like pure randomness, and only the hundred steps together add up
to a shape. That is also why the path a point takes is such a wandering one.

![Two panels of three coloured paths from noise to the arcs, the left one jagged and wandering and the right one smooth, with the travelled distance 17.3 and 1.38 times the straight line](../../images/models-that-generate/diffusion/one-sample-path.svg)

With fresh noise put back at every step, three points travel 27.9 m on average to cover 2.0 m of ground, a ratio of 17.3, while the same three with the noise left out travel 0.66 m to cover 0.48 m, a ratio of 1.38.

The right-hand panel is the same model and the same starting points with one
change: the fresh noise is left out and only the correction is kept. The path
becomes short and smooth, which is the first hint that most of the hundred
steps are not buying anything. The next page follows that hint. For now the
question is whether the walk produces the right points at all.

![Real demonstrations beside 2,000 generated waypoints, both forming the two arcs and both avoiding the obstacle, with a bar chart comparing mismatch scores of 0.0014 and 0.0021](../../images/models-that-generate/diffusion/generated-vs-real.svg)

Two thousand generated waypoints score a mismatch of 0.0021 against a floor of 0.0014, land 0.0237 m from the nearest real waypoint on average, split 47.3 per cent above and 52.7 per cent below, and put 0.05 per cent of themselves inside the obstacle.

Compare that last number with the 29.4 per cent of section 1. The predictor
spent nearly a third of its path in the obstacle because it answered the
average; the generator keeps almost everything out of it because it answers
whole examples instead. It also keeps both ways round, roughly half and half,
which no single answer can do.

---

## 5. Conditioning: the same denoiser told what to make

A generator that produces a fair sample of everything in the data is a curious
object rather than a useful one, because a robot is not asked for a typical
waypoint, it is asked for a waypoint that suits the situation in front of it.
Making that possible is called **conditioning**, and it needs no new idea at
all. The extra information is simply handed to the denoiser alongside the noisy
point, every time it is asked.

![A row of 13 numbered cells shown three times, the first ten identical and the last three changing between above, below and not told, each row ending with the noise the network names](../../images/models-that-generate/diffusion/conditioning-input.svg)

The denoiser used here takes one row of 13 numbers: two for the point, eight worked out from the step number, and three saying what to produce, and for the same point at step 40 it names (+0.48, +0.47) when told above, (-0.51, +2.18) when told below and (+0.40, +0.59) when not told.

Only three numbers changed between those rows, and the answer changed
completely. During training the condition is set to the true side of each
example, except that on one example in five it is set to "not told" instead, so
the same network learns both the conditioned job and the unconditioned one.
That choice looks like a detail here and turns out to be the whole basis of
section 6.

![Three panels of 1,200 generated waypoints: not told, giving both arcs; told above, giving the upper arc; told below, giving the lower arc](../../images/models-that-generate/diffusion/conditional-samples.svg)

Run with no condition the model sends 49.9 per cent of its waypoints above, told to go above it sends 96.1 per cent and told to go below it sends 3.8 per cent.

The same trained weights produced all three panels, and the only difference
between the runs was three numbers in the input. This is what makes the method
useful on a robot, because the condition does not have to be a side label. It
can be the camera picture, the arm's current joint angles and a sentence of
instruction, all turned into numbers and fed in the same way, which is exactly
what a diffusion policy does.

![A stacked bar chart of which side each run chose, beside a bar chart of the share landing in the obstacle: 29.4 per cent for the predictor and under 0.3 per cent for all three generator runs](../../images/models-that-generate/diffusion/condition-accuracy.svg)

Choosing the side costs nothing in safety: the conditioned runs put 0.00 per cent of their waypoints inside the obstacle and the unconditioned run 0.25 per cent, against 29.4 per cent of the predictor's path in section 1.

So conditioning gives back the control that was lost by refusing to average.
The asker picks which of the right answers they want, and the model still only
ever produces answers that the data supports. What it does not yet give is a
dial, because 96.1 per cent obedience is good but not certain, and the next
section is about the dial.

---

## 6. Guidance: pushing further in the direction the condition adds

Because the network was trained with the condition missing one time in five, it
can be run twice on the same point: once told what to produce and once not
told. The difference between the two answers is the part of the answer that the
condition is responsible for, and that difference can be multiplied by a number
larger than one before it is used. This is called **classifier-free guidance**,
and the number is the guidance strength.

![Four arrows from a common origin showing the noise named when not told, when told above, and the guided results at strengths 2 and 4, with a dashed arrow marking the difference between the first two](../../images/models-that-generate/diffusion/guidance-arrows.svg)

At the point (0.00, 0.25) and step 55 the network names (+0.01, +0.27) when not told and (+0.02, -0.27) when told above, so the condition contributes (+0.01, -0.54), and guiding at strength 2 gives (+0.03, -0.81) while strength 4 gives (+0.06, -1.88).

Strength 1 is just the ordinary conditioned answer, because taking the untold
answer and adding the whole difference once gives the told answer back.
Strength 0 is the unconditioned answer. Anything above 1 goes further in the
direction the condition pointed than the network itself asked to go, which is
why the guided arrow at strength 4 is nearly seven times the length of the
untold one.

![Five panels of generated waypoints at guidance strengths 0, 0.5, 1, 2 and 4, the first spread over both arcs and the last bunched in the middle of the upper arc](../../images/models-that-generate/diffusion/guidance-sweep.svg)

Asked for the upper arc at strengths 0, 0.5, 1, 2 and 4, the model sends 49.5, 83.6, 95.7, 99.0 and 100.0 per cent of its waypoints above, while the spread along the arc goes 0.994, 1.064, 0.966, 0.763 and 0.514 m against 0.999 m for the real upper arc.

So the dial works in both directions at once. Turning it up makes the condition
more reliably obeyed, which is what it is for, and it also squeezes the answers
towards the middle of what the condition asks for, which is not. By strength 4
every waypoint is on the right side, and they are bunched into roughly half the
stretch of path that the real demonstrations cover.

![Three charts against guidance strength: the share obeying the condition rising to 100 per cent, the two spreads falling below the real values, and the mismatch score dipping to its lowest at strength 1](../../images/models-that-generate/diffusion/guidance-tradeoff.svg)

Across strengths from 0 to 4 the obedience rises from 50 to 100 per cent while the spread along the arc falls from 0.973 m to 0.519 m, and the mismatch against the real upper arc is lowest at strength 1 with 0.0032, against 0.2530 at strength 0 and 0.2881 at strength 4.

The last of those three charts is the one to remember, because it shows that
there is a best setting and it is neither end of the dial. Too little guidance
and the model ignores what it was asked for; too much and it produces a
caricature of it, confident, repetitive and no longer a fair sample of
anything. On a robot the symptom of too much guidance is a policy that always
does the same thing even where the situation calls for variety, and the symptom
of too little is a policy that sometimes ignores the instruction entirely.
Values between about 1 and 3 are where most of the useful settings lie.

---

## 7. The cost: many passes through the network instead of one

Everything above has one price, and it is the same price throughout: a
predictor runs the network once to produce an answer, and a diffusion model
runs it once per step. The honest way to see what that buys is to generate the
same points with fewer and fewer steps and measure the result.

![A log-log chart of mismatch against the number of steps, falling from 1.586 at 2 steps to 0.002 at 100, beside a bar chart of the share landing in the obstacle at each step count](../../images/models-that-generate/diffusion/steps-vs-error.svg)

Generating with 2, 5, 10, 25, 50 and 100 steps gives mismatch scores of 1.586, 0.023, 0.014, 0.006, 0.003 and 0.002, and puts 0.07, 0.87, 0.40, 0.67, 0.13 and 0.20 per cent of the waypoints inside the obstacle.

Two steps is useless, five steps is already roughly in the right shape, and
after about twenty-five the improvement is small. The obstacle figures are
noisier because they count rare events, but the five-step run is the worst of
them at 0.87 per cent, which on a real arm would be a collision roughly once in
every hundred and fifteen waypoints. Seeing the clouds makes the numbers
concrete.

![Five panels of generated waypoints at 2, 5, 10, 25 and 100 steps, the first an almost empty scatter and the last two forming clean arcs](../../images/models-that-generate/diffusion/samples-at-few-steps.svg)

The same model asked for its answer in 2, 5, 10, 25 and 100 steps, with mismatch scores of 1.586, 0.023, 0.014, 0.006 and 0.002.

Time, unlike quality, is perfectly predictable, because every step is one full
pass of the network and nothing else.

![A straight line of generation time against step count, beside four lines for networks of different speeds crossing dashed budget lines at 100 ms and 33 ms](../../images/models-that-generate/diffusion/steps-vs-time.svg)

One pass of this small denoiser over a single point was measured at 29.1 microseconds, so 2 steps take 0.058 ms, 25 steps take 0.728 ms and 100 steps take 2.910 ms, while 64 points at once cost 0.149 ms per pass and so 14.908 ms for 100 steps.

The network on this page is tiny, so its own timings are not a guide to
anything real. The arithmetic is, though, and the right-hand chart does it for
networks of four plausible speeds. A robot arm that takes a new command ten
times a second has 100 ms to produce each one, and a network needing 2 ms per
pass therefore fits fifty steps and nothing else. At thirty commands a second
the same network fits sixteen steps, and at fifty commands a second it fits
ten. Those are the numbers that decide whether a diffusion model can drive an
arm at all, and they are why
[diffusion policies](../12_models-that-act/02_diffusion-and-flow-policies.md)
care so much about the step count.

There are three ways out. Use fewer steps and accept the loss, which the chart
above prices. Make each pass cheaper, which is what [making a model smaller and
faster](../07_pretraining-and-adapting/04_making-a-model-smaller-and-faster.md)
is about. Or change the method so that fewer steps are needed in the first
place, which is where the next page starts.

---

## 8. Where to read next

- [Flow matching and other
  generators](02_flow-matching-and-other-generators.md) is the next page, and it
  takes the hint from section 4 that most of the hundred steps were wasted, and
  builds the generator that needs four.
- [Diffusion and flow
  policies](../12_models-that-act/02_diffusion-and-flow-policies.md) puts this
  page's machinery on a real arm, with camera pictures as the condition and a
  control rate as the deadline.
- [Vision backbones](../09_models-that-see/01_vision-backbones.md) explains how
  a camera picture becomes the numbers that a conditioned denoiser can be
  handed.
- [World models](../12_models-that-act/04_world-models.md) uses generation for a
  different job: predicting what the scene will look like after an action
  rather than what action to take.
- [Diffusion and flow policies in the model
  catalogue](../../07_learned-models/06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
  lists the named models of this kind that people actually run on arms, with
  their costs.

---

## 9. Using it in Python

Sections 2, 3 and 4 built a noise schedule, trained a network to name the noise
and then walked back one step at a time. The code below does all three on the
same two-dimensional problem in PyTorch, so you can see that each named idea is
a few lines rather than a library. It is shortened to fit, so it trains for far
fewer steps than the model that drew the pictures and its answers are
correspondingly rough.

```python
import torch
from torch import nn

T = 100                                              # section 2: how many steps
tt = torch.arange(T + 1) / T
f = torch.cos((tt + 0.008) / 1.008 * torch.pi / 2) ** 2
kept = (f / f[0]).clamp(1e-5, 1.0)                   # section 2: the schedule
print(f'{kept[50].sqrt():.3f}')                      # 0.703, as in section 2

net = nn.Sequential(nn.Linear(3, 128), nn.Tanh(),    # 2 for the point, 1 for t
                    nn.Linear(128, 128), nn.Tanh(),
                    nn.Linear(128, 2))               # section 3: names the noise
opt = torch.optim.Adam(net.parameters(), lr=2e-3)

for _ in range(4000):                                # section 3: the training loop
    x0 = waypoints[torch.randint(0, len(waypoints), (512,))]
    t = torch.randint(1, T + 1, (512,))
    eps = torch.randn_like(x0)
    xt = kept[t].sqrt()[:, None] * x0 + (1 - kept[t]).sqrt()[:, None] * eps
    loss = ((net(torch.cat([xt, t[:, None] / T], 1)) - eps) ** 2).mean()
    opt.zero_grad(); loss.backward(); opt.step()

x = torch.randn(1000, 2)                             # section 4: start from noise
for t in range(T, 0, -1):                            # section 4: the reverse walk
    eps = net(torch.cat([x, torch.full((1000, 1), t / T)], 1))
    beta = (1 - kept[t] / kept[t - 1]).clamp(0, 0.999)
    x = (x - beta / (1 - kept[t]).sqrt() * eps) / (1 - beta).sqrt()
    if t > 1:
        x = x + (beta * (1 - kept[t - 1]) / (1 - kept[t])).sqrt() * torch.randn_like(x)
```

The library gives you the automatic differentiation, the optimiser and the
layers, and nothing else here is hidden: the schedule is four lines of
arithmetic, the training loop is six, and the reverse walk is five. That is
worth knowing, because diffusion sounds much heavier than it is, and the whole
method really does fit on one screen once the network itself is handed to you.

In practice nobody writes those lines, because Hugging Face's `diffusers`
package provides the schedules as `DDPMScheduler` and `DDIMScheduler`, the
reverse step as `scheduler.step`, and ready-built denoisers such as
`UNet2DModel` for pictures and `UNet1DModel` for sequences of actions. LeRobot
ships a complete diffusion policy for robot arms built on those pieces. Using
them means your schedule matches everybody else's, which matters more than it
sounds, because a sampler written for one schedule gives wrong answers on
another.

What you still have to decide is the part that no library chooses for you: how
many steps to train with, how many to generate with, how often to drop the
condition during training, and what guidance strength to use when running.
Section 6 showed that the last of those has a best value in the middle rather
than at an end, and section 7 showed that the second one is set by your control
rate rather than by your taste.
