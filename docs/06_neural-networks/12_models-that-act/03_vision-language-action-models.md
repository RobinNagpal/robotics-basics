# Vision-language-action models

The page before this one, [diffusion and flow policies](02_diffusion-and-flow-policies.md),
showed how a generative model can write a whole chunk of movement at once, and it left
one thing unfinished. A diffusion policy or a flow policy is trained on
demonstrations of one job, so it does that job and nothing else, and if you want the
arm to do a second job you train a second policy. This page is about the model that
removes that limit, because it takes a sentence as well as a picture, and the sentence
says which job to do.

A **vision-language-action model** is one trained model that reads camera pictures and
a written instruction, and gives back the numbers that move a robot arm. The name is
just a list of what goes in and what comes out, and it is usually shortened to VLA. The
point of it is that one model covers many jobs, because the job is named in words
rather than built into the weights.

This page is for a reader who has read the two pages before it in this chapter, so you
should already know what a policy is in the robot sense, what behaviour cloning is,
what an action chunk is, and why a chunk is better than one step at a time. Those words
are explained on [behaviour cloning and action
chunks](01_behaviour-cloning-and-action-chunks.md). You should also have read [vision-language
models](../10_language-and-multimodal-models/03_vision-language-models.md), because the
body of a vision-language-action model is a vision-language model, and this page does
not explain that part again.

The page answers four questions. What is this model made of? How is a movement written
down so that a model which was built to predict words can produce one? How is it
trained so that learning to move does not destroy everything else it knew? And what does
it really carry over to situations it was not trained on, which is the part that is most
often oversold.

Every number in the pictures below is worked out by
[`docs/diagrams/models_that_act_2.py`](../../diagrams/models_that_act_2.py). The robot
episodes are simulated, which means the arm movements come from smooth made-up curves
rather than from a real recording, but everything done to them, including the binning,
the measured errors and the small networks that are trained, is real arithmetic.

## Contents

1. [What a vision-language-action model is](#1-what-a-vision-language-action-model-is)
2. [The body: a vision-language model with an action output](#2-the-body-a-vision-language-model-with-an-action-output)
3. [Way one: every action number becomes a token](#3-way-one-every-action-number-becomes-a-token)
4. [Way two: a small continuous action head](#4-way-two-a-small-continuous-action-head)
5. [Co-training: robot episodes and web pictures together](#5-co-training-robot-episodes-and-web-pictures-together)
6. [Cross-embodiment: episodes from many different robots](#6-cross-embodiment-episodes-from-many-different-robots)
7. [What generalisation really looks like, and what it costs to run](#7-what-generalisation-really-looks-like-and-what-it-costs-to-run)
8. [Where to read next](#8-where-to-read-next)
9. [Using it in Python](#9-using-it-in-python)

---

## 1. What a vision-language-action model is

The place to start is the outside of the model, because once you can see exactly what
goes in and exactly what comes out, everything inside is easier to follow. The picture
below shows one call of the model, with the sizes worked out for two cameras of 224
pixels by 224 pixels and a six-joint arm.

![A layout showing two camera pictures cut into 16 by 16 patch grids, an instruction box and a joint state box feeding one model, and a table of ten rows by seven columns of joint movement numbers coming out](../../images/models-that-act/vision-language-action-models/vla-input-output.svg)

One call takes 525 tokens of input and gives back 70 numbers, which are ten steps of
seven numbers each.

Each camera picture is cut into squares of 14 pixels by 14 pixels, which gives 16 rows
of 16 squares, so 256 squares for each camera and 512 for the two together. The
instruction "pick up the red block and put it in the bowl" is eleven words, which comes
to about 12 tokens once an end marker is added, and the six joint readings are packed
into one more token. That makes 512 plus 12 plus 1, which is 525 tokens in the
sequence. What comes out is a chunk of ten steps, and each step holds six joint
movements and one gripper command, so 70 numbers in all. At 20 commands a second that
chunk covers half a second of movement.

The reason this is worth doing is that the instruction changes the answer. The next
picture takes the same cameras and the same joint readings and shows what two different
instructions ask the arm to do.

![Two line charts side by side, each showing six coloured lines of commanded joint movement over ten steps, with clearly different shapes under the two instruction titles](../../images/models-that-act/vision-language-action-models/same-picture-two-sentences.svg)

The two chunks differ by 2.53 degrees for each joint at each step, which is larger than
the 1.32 degrees a joint moves in an average step, so the instruction is not a small
nudge to the answer but the thing that decides it.

This is what a per-task policy cannot do, because a per-task policy has no input that
says which task to do. The practical effect is on how many models you have to train and
keep working, and on how much data each one learns from.

![A bar chart comparing 150 episodes for one per-task policy with 1,800 for one shared policy, beside a line chart where the number of separate models grows with the number of tasks while the shared count stays at one](../../images/models-that-act/vision-language-action-models/one-model-many-tasks.svg)

With twelve tasks and 150 demonstrations recorded for each of them, each separate
policy learns from 150 episodes while one instruction-conditioned policy learns from all
1,800.

That is 45,000 frames against 540,000 frames, twelve times as many, and the shared model
also gets to reuse what it learned about one task when it does another. The cost is
that this model is much larger and much slower than a per-task policy, which is what
section 7 is about.

---

## 2. The body: a vision-language model with an action output

Now that you know what goes in and what comes out, the next question is what sits in
between, and the answer is a model you have already met. A vision-language-action model
is a [vision-language model](../10_language-and-multimodal-models/03_vision-language-models.md)
with an action output bolted on, which means almost all of it was built and trained to
read pictures and write words, and only the last part is new.

The picture below follows the real shapes through one call, so that the words "patch",
"token" and "width" have sizes attached to them.

![Seven stacked rows, each naming a stage and giving its arithmetic, from two camera pictures of 301,056 numbers down to an action chunk of 70 numbers](../../images/models-that-act/vision-language-action-models/vla-body-shapes.svg)

Every number here follows from three choices: the picture size, the patch size and the
width of one token inside the model.

Two colour pictures of 224 by 224 pixels are 301,056 numbers. Each patch of 14 by 14
pixels in colour is 588 numbers, and one layer of 588 by 1,024 weights, which is 602,112
weights, turns each patch into one token of 1,024 numbers. The words are looked up in a
table of 32,000 by 1,024, which is 32,768,000 numbers, and the six joint readings go
through a layer of 6 by 1,024 to make one more token. The 525 tokens are then 537,600
numbers, and inside every attention layer the model compares every token with every
token, which is 275,625 pairs.

That last count is why the camera resolution is such an expensive choice.

![Two bar charts, the left showing tokens rising from 525 to 4,621 as the picture grows from 224 to 672 pixels, the right showing attention work rising to 77.5 times the starting cost](../../images/models-that-act/vision-language-action-models/resolution-and-tokens.svg)

Going from 224 pixels to 672 pixels on a side multiplies the tokens by about nine and the
attention work by 77.5.

Doubling the width of the picture puts four times as many patches in, and because
attention compares every pair of tokens, four times as many tokens is about sixteen times
as much attention work. A robot that must see a small screw therefore pays for that
sharpness in time at every single call, which is why many of these models send one
low-resolution view of the whole scene and one close view from a camera on the wrist,
rather than one very sharp view of everything.

The new part is the output. The model's last token is 1,024 numbers, and something has to
turn those 1,024 numbers into the 70 numbers of an action chunk. There are two ways of
doing that, and the choice between them is the real design split in this family of
models.

![A branch diagram from the model's last token into two boxes, one describing a 32,768,000-weight output layer producing 70 tokens one after another, the other a 364,358-weight head producing all 70 numbers at once](../../images/models-that-act/vision-language-action-models/two-ways-to-get-an-action.svg)

The first way reuses the layer the model already has for words, which holds 32,768,000
weights, and the second adds a small new network of 364,358 weights.

The first way is to treat each action number as a word, giving it a place in the
vocabulary, so the model produces actions in exactly the way it produces text. The
second way is to attach a small network that produces the whole chunk of numbers
directly. The next two sections take them one at a time.

---

## 3. Way one: every action number becomes a token

The first way starts from a problem of types. A language model chooses, at each step,
one entry from a fixed list of possible entries, and a joint movement is not an entry in
a list but a number that can take any value. **Action tokenisation** is the name for
fixing that mismatch by chopping the range of each action number into a fixed set of
bins and treating each bin as one entry in the vocabulary, so that saying "bin 137" is
the same kind of act as saying the word "bowl".

The first thing to settle is the range the bins cover, and it is settled from the
training data rather than from the arm's data sheet.

![A histogram of one joint's commanded movement with two red lines at the 1st and 99th percentile, beside a close-up histogram crossed by twelve evenly spaced bin edges](../../images/models-that-act/vision-language-action-models/binning-one-dimension.svg)

For the first joint of the simulated arm the 1st and 99th percentile of the recorded
movements fall at -3.06 and +3.20 degrees for one step, and with 256 bins one bin is
0.0244 degrees wide.

Anything outside that range is pushed back to the end bin, which happens to 2.0 per cent
of this joint's numbers. Once the range is fixed, the only remaining question seems to be
how many bins to use, and the measured answer is that it stops mattering very quickly.

![Two charts, the left showing rounding error falling steadily with bin count while the total error flattens, the right showing the rounding error at the fingertip falling from 0.587 mm at 32 bins to 0.018 mm at 1,024 bins](../../images/models-that-act/vision-language-action-models/quantisation-error-vs-bins.svg)

At 256 bins the rounding alone is 0.0070 degrees for one joint in one step, which is 0.074
millimetres at a fingertip 0.60 metres from the joint, and the worst single rounding is
0.0125 degrees.

That is far below what any arm can repeat, so rounding is not the cost of this method.
The cost hides in the 2.7 per cent of numbers that fall outside the chosen range and get
pushed back, because those are exactly the fastest movements, and pushing them back
always shortens them rather than lengthening them. Since the model is producing
movements rather than positions, those shortfalls add up.

![Two bar charts, the left showing the one-step error for four choices of range at 256 bins, the right showing fingertip drift after ten steps and after three hundred steps for the same four choices](../../images/models-that-act/vision-language-action-models/percentile-range-matters.svg)

All four cases use 256 bins, and only the range the bins cover changes, which moves the
one-step error from 0.156 degrees down to 0.016 degrees and the drift after one chunk from
18.70 millimetres down to 0.54 millimetres.

Cutting at the 1st and 99th percentile pushes back 2.72 per cent of the numbers and leaves
the fingertip 18.70 millimetres out of place after only ten steps. Cutting at the 0.1st
and 99.9th percentile pushes back 0.59 per cent and halves that to 9.71 millimetres.
Making the range a third wider than anything ever recorded pushes back almost nothing
and leaves 0.54 millimetres after a chunk, which is the floor set by rounding alone.
So the lesson is that the number of bins is the part people argue about and the range is
the part that costs them millimetres.

The real price of this method is not accuracy at all, but the number of tokens, because
every action token is produced one at a time with a full pass through the model for
each.

![A bar chart of token counts for three cases beside a curve showing the error of a rebuilt chunk falling as more frequency terms are kept](../../images/models-that-act/vision-language-action-models/tokens-per-chunk.svg)

A chunk of ten steps costs 60 tokens for six joints, a chunk of fifty steps costs 300,
and describing that longer chunk by its first six frequency terms instead costs 36 tokens
while rebuilding it to within 0.053 degrees.

The right-hand chart uses a discrete cosine transform, which is an exact way of
rewriting a sequence of numbers as a sum of waves of different speeds. A demonstrated
movement is smooth, so almost all of it lives in the slowest few waves, and keeping four
terms per joint already rebuilds the chunk to 0.110 degrees while using 24 tokens instead
of 300. Several real systems compress the chunk this way before tokenising it, and that
is the honest answer to the token-count problem rather than a smaller number of bins.

So the case for action tokenisation is this. It is the simplest thing that can be done,
it needs no new machinery at all, it trains with exactly the loss the language model was
already trained with, and because the actions live in the same vocabulary as the words,
the model can be trained on robot data and text data in the same batch without any
special handling. Its cost is one pass through the whole model for every single number
it produces, and the rest of this page shows what that costs in time.

---

## 4. Way two: a small continuous action head

The alternative keeps the same body and replaces the output. Instead of asking the model
to name a bin, a small extra network, called an **action head**, takes the model's last
token and produces all 70 numbers of the chunk at once, as ordinary numbers rather than
as choices from a list. The head is almost always a generative one, built with flow
matching or diffusion, for the reason given on [diffusion and flow
policies](02_diffusion-and-flow-policies.md): a plain network trained with squared error
answers an ambiguous situation by averaging the possible movements, and the average of
two good movements is usually a bad one.

A flow-matching head works by starting from a list of random numbers and walking it,
in a few equal steps, into a list of action numbers, following a direction the head has
learned to predict. The head used in the pictures below is real: it is a small network
trained in NumPy on the simulated chunks, by the method described on [flow matching and
other generators](../08_models-that-generate/02_flow-matching-and-other-generators.md).
What it is told about the situation is the ten actions just before the chunk, which
stands in for the pictures and the instruction a real model would be given.

![Two charts, the left showing one noise sample walked into an action in one, two, four and thirty-two steps, the right showing twenty-four different noise samples converging towards a narrow band](../../images/models-that-act/vision-language-action-models/flow-head-path.svg)

With one big step this joint lands 0.245 degrees away from where thirty-two small steps
land it, with two steps 0.190 degrees away and with four steps 0.053 degrees away.

The paths are nearly straight, which is what flow matching is for, and that straightness
is why a handful of steps is enough. The right-hand chart starts twenty-four different
random lists from the same instruction and the same picture, and they end close together,
which is the head agreeing with itself about what to do.

The number of steps is the knob that trades exactness for time, and the trade can be
measured.

![A log-log chart showing the distance from a 128-step answer falling from 0.615 degrees at one step to 0.007 degrees at thirty-two steps](../../images/models-that-act/vision-language-action-models/flow-steps-vs-error.svg)

Taking one step instead of many leaves the chunk 0.615 degrees out, two steps leaves
0.178 degrees, four leaves 0.077 degrees and eight leaves 0.035 degrees, which is 0.363
millimetres at the fingertip.

Eight steps is therefore already below what the arm can repeat, and that is the whole
argument for this design, because eight passes through a small head is nothing next to
seventy passes through the whole model.

![Two charts, the left a bar chart of the time to make one chunk with action tokens at 310 ms against the head at about 33 ms, the right showing how many fresh looks a second each allows](../../images/models-that-act/vision-language-action-models/head-vs-tokens-latency.svg)

If reading the 525 input tokens costs 30 milliseconds, one more action token costs 4
milliseconds and one head step costs 0.4 milliseconds, then 70 action tokens take 310
milliseconds and the head at eight steps takes 33.2 milliseconds.

Those two numbers decide how often the model gets to look at a fresh picture, which is
3.2 times a second with action tokens and 30.1 times a second with the head. At 20
commands a second the arm runs 6.2 commands on old information in the first case and 0.7
in the second, and a robot that must react to something moving cares about that
difference much more than it cares about a hundredth of a degree.

The last comparison is what the two outputs actually produce for one chunk.

![A line chart of one joint's movement falling over ten steps, with the demonstrated chunk and the binned version lying on top of each other and the head's two outputs tracking them with a small wobble](../../images/models-that-act/vision-language-action-models/continuous-vs-binned.svg)

Writing this chunk through 256 bins moves it by 0.0073 degrees, while the head's own
chunk sits 0.326 degrees from the demonstrated one, and over 200 situations the head
lands 0.315 degrees away for each joint at each step.

That comparison is worth reading carefully, because it says the binned version is the one
that copies a given chunk most exactly. The head is not trying to copy a given chunk; it
is drawing one of the movements that fit the situation, and its wobble is partly the price
of being able to choose and partly the price of a small head trained for a few seconds in
NumPy rather than a large one trained for days. So the honest summary of the two ways is
that tokens are simpler, copy more exactly and train with no new machinery, while the head
is roughly ten times faster in practice and handles ambiguity properly, and most recent
systems take the head.

---

## 5. Co-training: robot episodes and web pictures together

Both ways of producing an action leave the same question open, which is how to train the
thing without ruining it. The body of the model knows what a bowl is and what the word
"left" means, and it knows that because it was trained on an enormous amount of ordinary
pictures and text. Training it on robot episodes alone destroys exactly that knowledge,
for the reason set out under catastrophic forgetting on [fine-tuning and
adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md): the weights
that held the old skill are free to move, and gradient descent moves them wherever the
new job wants them.

The effect is easy to measure on a small simulated version of the same situation, where
one network is first trained on a general job and then taught a second job.

![Two charts of accuracy against training steps, the left showing the general job falling from 96 to 59 per cent while the robot job rises, the right showing both staying high when a quarter of the batches are general data](../../images/models-that-act/vision-language-action-models/forgetting-curve.svg)

Trained on the robot job alone, the general job falls from 95.9 per cent right to 59.2
per cent, and with one batch in four still drawn from the general data it stays at 96.2
per cent while the robot job reaches 97.4 per cent.

**Co-training** is the name for the fix shown on the right, which is to keep feeding the
old data while the new job is learned, so that every batch is partly robot episodes and
partly ordinary pictures and text. It is not a clever method, it is simply refusing to
stop showing the model the thing you want it to remember, and the question is how much
of the old data is needed.

![A line chart of final accuracy on both jobs against the share of general data in the batches, with the general job jumping from 59 to 96 per cent as soon as five per cent of the batches are general](../../images/models-that-act/vision-language-action-models/mixture-sweep.svg)

Five per cent of the batches is enough to bring the general job back from 59 to 95.5 per
cent, and going further to three quarters general data gains only another 1.4 points
while the robot job starts to slip.

The reason this needs saying out loud is that the natural sizes of the two sets are
nothing like the sizes you want.

![Two bar charts, the left comparing 540,000 robot frames with 400,000,000 web pairs on a log scale, the right showing that pouring them together gives robot data a share of 0.1348 per cent](../../images/models-that-act/vision-language-action-models/data-sizes.svg)

A recording of 1,800 episodes is 540,000 frames, a modest web set is 400,000,000 pairs of
picture and text, and simply pouring the two together would make robot frames 0.1348 per
cent of the batches.

At that share the model would barely learn to move at all. So the mixture is chosen on
purpose and enforced by the sampler, and at a share of three quarters robot data every
robot frame is seen about 2,222 times for each single pass through the web set. The cost
of co-training is therefore paid in two places. It makes training longer, because the
model is doing two jobs instead of one, and it makes the robot data get repeated many
times, which is its own risk of memorising rather than learning.

---

## 6. Cross-embodiment: episodes from many different robots

Co-training deals with keeping old knowledge while adding robot data, and the next
question is where more robot data comes from, since one laboratory's arm produces very
little of it. **Cross-embodiment** training is the answer that pools episodes recorded on
many different robots into one training set, and the word embodiment just means the
particular body the episodes were recorded on.

The difficulty is that two robots do not speak the same numbers, even when they are
doing the same thing.

![Two drawings of a two-link arm at a fixed pose, each with the small joint turns needed to move the fingertip twenty millimetres across and ten millimetres up](../../images/models-that-act/vision-language-action-models/action-spaces-do-not-match.svg)

To move the fingertip 20 millimetres across and 10 millimetres up, an arm with links of
0.40 and 0.30 metres must turn its joints by +2.006 and -7.236 degrees, while an arm with
links of 0.25 and 0.45 metres must turn its joints by +0.186 and -3.064 degrees.

The same job at the fingertip is a completely different pair of numbers at the joints, so
an action recorded on one arm is not an instruction that means anything on the other.
There are two standard ways round this. The first is to describe the action at the
fingertip rather than at the joints, by recording how far the gripper should move in
space and leaving each robot's own controller to work out the joint turns. The second,
which is used alongside it, is to scale each robot's numbers by that robot's own range,
so that the recorded numbers of every robot fill the same interval.

![Two histograms, the left showing arm A spread between about minus three and plus three degrees a step while arm B sits in a narrow peak, the right showing both filling the same range after scaling](../../images/models-that-act/vision-language-action-models/normalising-per-robot.svg)

Arm A's first joint runs from -3.06 to +3.20 degrees in a step and arm B's from -1.07 to
+1.11 degrees, and after each is divided by its own range the two distributions sit on top
of each other.

With the numbers made comparable, the pooling can be tried, and the result depends
entirely on one detail.

![A bar chart of three cases: arm B's own fifty episodes at 6.17 degrees of error, the pooled set with a robot tag at 5.17 degrees, and the pooled set with no tag at 37.87 degrees](../../images/models-that-act/vision-language-action-models/pooling-helps.svg)

Adding 2,000 episodes from another arm cuts the error from 6.17 degrees to 5.17 degrees
when the model is told which arm it is driving, and raises it to 37.87 degrees when it is
not.

That third bar is the whole reason real systems add an embodiment tag to the input: a
model that cannot tell the two arms apart has to give one answer for both, and the only
answer that fits both is the average of two different answers, which fits neither. With
the tag in place, the pooled data helps, and the next chart says when it helps.

![A line chart of error against the number of arm B examples, with the pooled line below the alone line at twenty-five and fifty examples and above it from a hundred onwards](../../images/models-that-act/vision-language-action-models/pooling-vs-data.svg)

With 25 of its own examples arm B does better with the pool, 7.61 degrees against 8.82,
and with 50 the two are level, while from 100 examples upwards its own data alone is the
better teacher.

That is the honest shape of the result in this small experiment, and it matches what the
method is for. Pooling other robots' episodes buys the most where a new robot has almost
no data of its own, because the shared part of the job, which here is working out where
the object is from the camera, gets learned from everybody's data at once. Once the new
robot has a few hundred episodes of its own, the shared network has to split its capacity
between bodies, and that costs more than the pooling gains. So cross-embodiment data is a
way of starting a new robot quickly rather than a way of making a well-served robot
better.

---

## 7. What generalisation really looks like, and what it costs to run

Everything so far has been about building and training the model, and this last section
is about what you actually get, which is the part most often described too generously.
The claim people hear is that these models generalise. The useful question is not whether
they generalise but which specific change they survive, and the four changes below behave
very differently.

The first change is moving the object, and that one works, inside limits that are easy to
measure.

![A scatter of training object positions filling the middle 36 per cent of a camera view, beside a bar chart of error by distance from the middle rising from 0.36 to 13.07 degrees](../../images/models-that-act/vision-language-action-models/position-coverage.svg)

Where the training objects covered 36 per cent of the camera view, the error stays
between 0.36 and 0.47 degrees anywhere inside that area and rises to 2.62 and then 13.07
degrees in the two bands outside it.

So "the same task with the object moved" is two different claims. Moved within the patch
of table that the demonstrations covered, the model is fine, and this is the thing people
see in a demonstration video. Moved to a corner nobody ever put an object in, the model
is thirty times worse, and no amount of instruction wording fixes it.

The second change is a new object of a kind the model has seen, and it separates cleanly
from a new kind altogether.

![A scatter of object widths and heights showing two separated clusters, beside a bar chart of grasp error at 0.08 cm for a new object of the trained kind, 1.30 cm for the untrained kind and 0.12 cm once 150 of them are added](../../images/models-that-act/vision-language-action-models/new-object-kind.svg)

A rule learned from 200 tall narrow objects places the fingers on a new tall narrow object
to within 0.08 centimetres, and on a wide flat object it is 1.30 centimetres out, which is
sixteen times worse, until 150 wide flat objects are added and the error drops to 0.12
centimetres.

The reason is not that the rule changed between the two kinds, because in this simulation
it is literally the same rule. The reason is that the new kind sits in a part of the
object's description that the training set never visited, so the model is guessing rather
than recalling. That is worth stating plainly, because it means a model can fail on a new
object even when the right answer follows from something it already knows.

The third change is rewording the instruction, and this is the one that genuinely works.

![A horizontal bar chart showing three rewordings of a trained task reusing 75 to 86 per cent of the training vocabulary while two new tasks reuse only 40 and 50 per cent](../../images/models-that-act/vision-language-action-models/instruction-overlap.svg)

Three different ways of saying the same trained task reuse between 75 and 86 per cent of
the words that appear in the training instructions, while two genuinely new tasks reuse
only 40 and 50 per cent.

The word count here is a crude stand-in rather than a measurement of what the model does,
and the real reason rewording works is that the language half of the model was trained on
far more text than the robot data contains, so it already treats "place the red block
into the bowl" and "put the red block in the bowl" as near neighbours. This is the one
place where the web pretraining pays off directly.

The fourth change is a genuinely new task, and today it does not work. A model shown
twelve tasks does not do a thirteenth because it was asked nicely, and the honest
description of what people call zero-shot success in this field is almost always one of
the first three cases rather than the fourth.

![A five-row table of changes, verdicts and reasons, with three rows marked as not working and two as working](../../images/models-that-act/vision-language-action-models/four-cases.svg)

The five rows gather the measurements above, with the error figures taken from the same
experiments shown earlier on this page.

That leaves the cost of actually running one of these models, which is the last practical
obstacle. A large model that takes 310 milliseconds to produce a chunk cannot be asked for
a new command every 20 milliseconds, and there are three things people do about it.

![A log-log chart of the shortest workable chunk length against the arm's command rate for three model speeds, beside a timeline of one big model firing three times while thirty steps of a small policy run underneath](../../images/models-that-act/vision-language-action-models/cost-of-running.svg)

At 100 commands a second the chunk must cover at least 31 steps if the actions come out as
tokens, 3.3 steps if they come from the head, and 0.3 steps from a distilled model ten
times faster.

The first fix is a longer chunk, which costs you reaction time, because the arm is running
on a picture that is by then old. The second is a smaller model trained to copy the big
one, which is the distillation described on [making a model smaller and
faster](../07_pretraining-and-adapting/04_making-a-model-smaller-and-faster.md), and
which costs you some of the big model's knowledge. The third, shown on the right of the
picture, is to run the big model slowly to decide what to aim for and a small fast policy
underneath it to actually move the joints, so the big model fires about once for every 31
steps of the fast one. That split is now the usual arrangement, and it is also the
arrangement that makes the next page's subject useful, because a model that decides what
to aim for is close to a model that predicts what will happen.

---

## 8. Where to read next

- [World models](04_world-models.md) is the next page, and it covers the models that
  predict what will happen next rather than reacting to what is there now, including
  what goes wrong when a model's idea of the physics is slightly wrong.
- [Diffusion and flow policies](02_diffusion-and-flow-policies.md) is worth rereading
  for the generative machinery the action head of section 4 is built from.
- [Fine-tuning and adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md)
  explains catastrophic forgetting in full, which is the problem that co-training exists
  to solve.
- [Running and evaluating a model](../13_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  takes the latency arithmetic of section 7 further, and says how to test a policy
  honestly rather than on the task it was demonstrated on.
- [Vision-language-action models](../../07_learned-models/07_language-models/02_most-used/01_vision-language-action-models.md)
  in the next book is the catalogue page for this family, with the named models that
  exist, what each one costs and where each one fails.
- [Vision-language models](../../07_learned-models/07_language-models/02_most-used/02_vision-language-models.md)
  is the catalogue page for the body these models are built from.

---

## 9. Using it in Python

Section 3 measured what binning does to an action and section 4 measured what a flow head
does instead, and both of those are a handful of lines of real code. The lines below use
NumPy and PyTorch to do the two things on a batch of chunks, so that you can see that the
binning is arithmetic rather than a library and that the head is an ordinary small
network. No library gives you a whole vision-language-action model as a single call, so
this shows the output end, which is the part that differs between designs.

```python
import numpy as np
import torch
from torch import nn

# Section 1: a chunk is CHUNK steps by ACTION_DIM numbers.
CHUNK, ACTION_DIM, BINS = 10, 7, 256
rng = np.random.default_rng(0)
chunks = rng.normal(0.0, 0.02, (64, CHUNK, ACTION_DIM))   # stand-in for recorded actions

# Section 3: the range comes from the data, then every number becomes a whole number.
lo = np.percentile(chunks.reshape(-1, ACTION_DIM), 1.0, axis=0)
hi = np.percentile(chunks.reshape(-1, ACTION_DIM), 99.0, axis=0)
z = np.clip(2.0 * (chunks - lo) / (hi - lo) - 1.0, -1.0, 1.0)
ids = np.clip(((z + 1.0) / 2.0 * BINS).astype(int), 0, BINS - 1)   # the action tokens
back = (ids + 0.5) / BINS * 2.0 - 1.0
rebuilt = (back + 1.0) / 2.0 * (hi - lo) + lo
print('tokens per chunk:', ids.size // len(chunks))                # 70
print('worst rounding, degrees:',
      round(float(np.degrees(np.abs(rebuilt - chunks).max())), 4))

# Section 4: the head is a small network that predicts a direction to walk in.
head = nn.Sequential(nn.Linear(CHUNK * ACTION_DIM + 1 + 1024, 256), nn.ReLU(),
                     nn.Linear(256, 256), nn.ReLU(),
                     nn.Linear(256, CHUNK * ACTION_DIM))
print('weights in the head:', sum(p.numel() for p in head.parameters()))

def sample(context, steps=8):                 # context is the model's last token
    x = torch.randn(len(context), CHUNK * ACTION_DIM)
    for k in range(steps):                    # section 4's walk, in equal steps
        t = torch.full((len(context), 1), k / steps)
        x = x + (1.0 / steps) * head(torch.cat([x, t, context], dim=1))
    return x.reshape(-1, CHUNK, ACTION_DIM)

print('chunk shape from the head:', tuple(sample(torch.zeros(4, 1024)).shape))
```

PyTorch gives you the layers, the gradients and the optimiser, and a library such as
Hugging Face `transformers` gives you the vision-language model that would supply the
1,024-number context in the last line. What no library decides for you is everything this
page has been about. You choose the range the bins cover, and section 3 showed that this
choice costs millimetres while the number of bins costs almost nothing. You choose
between the two output styles, and section 4 showed that choice is worth about ten times
in speed. You choose the mixture of robot and web data, and section 5 showed that five
per cent of the old data is the difference between keeping and losing what the model
knew.

The one line above that is doing something subtle is the walk inside `sample`. It starts
from random numbers and takes equal steps in a direction the head predicts, and the
number of steps is the knob measured in section 4: one step leaves the chunk 0.615 degrees
out and eight steps leaves it 0.035 degrees out. Training that head is not shown here,
because it needs the flow-matching loss described on [flow matching and other
generators](../08_models-that-generate/02_flow-matching-and-other-generators.md), but it
is a handful of lines more: draw a random list, mix it with a real chunk in some
proportion, and train the head to predict the difference between them.

The honest thing to say about running this for real is that none of the code above is the
hard part. The hard part is collecting the demonstrations, and the measurements in
section 7 say why, because what the model can do is set almost entirely by where the
objects were when somebody recorded them.
