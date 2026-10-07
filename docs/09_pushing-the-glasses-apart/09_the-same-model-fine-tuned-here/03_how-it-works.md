# How it works

This page explains what happens inside this solution, part by part. It follows
[the code](02_the-code.md), and explains what each part of that code is doing.

## Contents

1. [Fine-tuning — continuing somebody else's training](#1-fine-tuning--continuing-somebody-elses-training)
2. [Low-rank adaptation — a small correction instead of a large change](#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
3. [Where the demonstrations come from, and what they cost](#3-where-the-demonstrations-come-from-and-what-they-cost)
4. [Whether anything but the training differs](#4-whether-anything-but-the-training-differs)
5. [What fine-tuning closes, and what it cannot touch](#5-what-fine-tuning-closes-and-what-it-cannot-touch)
6. [Two ways training on one cell's pushes goes wrong](#6-two-ways-training-on-one-cells-pushes-goes-wrong)
7. [A second way — the same fine-tune on a larger model](#7-a-second-way--the-same-fine-tune-on-a-larger-model)

## 1. Fine-tuning — continuing somebody else's training

Fine-tuning is the single thing that separates this solution from its partner,
so it is worth setting out in plain words.

Training a network means showing it an example, comparing what it produced
against the answer that was wanted, and nudging every weight a little in the
direction that would have helped. Repeat that over many examples and the
weights settle at values that produce good answers. Training from a random
start means the weights begin as noise, so the nudges have to build every part
of the model out of nothing. **Fine-tuning means the weights begin at values
somebody else's training already settled**, so the nudges have much less to do.

Why that is so much cheaper is clearest in terms of what the data has to pay
for. Every weight is a number the training data has to determine, and a weight
the data cannot pin down ends up fitted to accidents of the particular examples
it was shown. So the amount of data needed grows with the number of weights
that have to be settled from nothing, and fine-tuning changes that sum almost
entirely: the great majority of the weights already sit at values that work,
and the data only has to adjust them. It is the difference between solving for
every coefficient of a long polynomial and being handed one that already fits a
similar curve.

There is a second saving, about time rather than data. A model fitted on
pictures holds, in its early layers, detectors for things common to all vision:
an edge, a corner, a shading that runs across a curved surface. A model fitted
on robot motion holds something similar about motion: that a trajectory is
smooth, that a jaw approaches a thing before it touches it, that a motion has a
beginning and an end. Both transfer almost completely, because an edge is an
edge and those are properties of moving a tool rather than of any one robot,
and a random start spends much of its training discovering them again.

What carries over worst is the judgement at the top, which was fitted to decide
what to do next in rooms that look nothing like this one, with grippers shaped
nothing like this one, on tasks that were mostly not pushing. So fine-tuning
here has more work to do than the usual advice about borrowed models implies,
and still far less work than a random start. That last claim is the one
[solution 3](../06_imitation-from-demonstrations/01_what-it-is.md) exists to
check from the other side, because it fits a policy here from random numbers on
the very same demonstrations.

## 2. Low-rank adaptation — a small correction instead of a large change

Fine-tuning as described above moves every weight, and on a model of this size
that is the expensive way to do it. Low-rank adaptation is the cheap way, and
it is what this solution uses.

A layer of a network takes a list of numbers in, multiplies it by a table of
numbers, and hands a list of numbers out. That table is the layer's weights,
and ordinary fine-tuning changes every number in it. **Low-rank adaptation
leaves every borrowed number where it is and learns a correction that is added
to it.** The correction is as wide as the table it corrects, so the layer still
does the same work, but it is not allowed to be an arbitrary table: it is
forced to be the product of two thin tables, one that squeezes the incoming
list down to a handful of numbers and one that expands that handful back out to
full width. Because the squeeze is narrow, the two thin tables together hold
far fewer numbers than the table they correct.

A table of numbers can be written as a sum of simple patterns, and the number
of patterns needed is the table's **rank**. Forcing the correction through a
narrow squeeze is forcing it to be a sum of only a handful of them, which is
the same move as approximating a curve by a few terms of a series.

What that buys is memory. Training does not only have to hold the weights: for
every weight being changed it also holds that weight's gradient, which says
which way to nudge it, and the optimiser's running averages of that gradient,
which are what make the nudges stable. Those add up to several times the size
of the model. With low-rank adaptation only the correction carries gradients
and optimiser state, and the borrowed weights sit there as a fixed cost, so
what has to fit is the model's own size plus a little. On π0, which holds about
3.3 billion parameters, that is the difference between more than 22 GB of
accelerator memory and more than 70 GB. SmolVLA is much smaller — about 450
million parameters — and at that size **the saving is larger than it needs to
be**: the measured figure for the training below is 1.02 GiB, which fits on
this machine with nothing rented. The arithmetic is still what makes that true;
the conclusion it was written to support, that an accelerator has to be rented,
is only the conclusion for the larger model.

**The trade is that it adapts less deeply, and this decides how the pair's
result should be read.** The correction is confined to a handful of directions
in each table, so a change that genuinely needs the whole table cannot be
expressed. Where the new task is near the old one that costs nothing. Where it
is far, a full fine-tune would go further, and this cell is far: rendered
pictures of a simulated table, one gripper, one motion, and a kind of outcome
none of the borrowed datasets contained. So **the gap this pair measures is a
lower bound on what fine-tuning could buy**, and a result saying low-rank
fine-tuning bought little does not say that fine-tuning bought little.

One more property of the correction decides the compute column on the
scorecard. Once training has finished the two thin tables can be multiplied out
and added into the borrowed table, leaving a single table of the original size.
The fine-tuned model is then exactly as large and exactly as fast as the
downloaded one, so **this solution and its partner cost the same to run**, and
whatever separates their scores cannot be put down to one of them being given
more computation.

## 3. Where the demonstrations come from, and what they cost

Fine-tuning needs examples, which here means recorded pushes with what was seen
beside what was done, and this is where the arrangement of the six helps.

[Solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) generates
pushes by geometry and ranks them with a fitted ranker. Run it on the examiner
over the training half of the tables and almost every push it makes is a
demonstration. The observation is what this model takes as its input: the
rendered view of the table from the top taken at the moment the push was
chosen, the one instruction, and the arm's own pose. The action is the path the
jaw really followed, which the examiner writes down on every action. So a
demonstration is a recording of the shared contract being satisfied, and
nothing in it had to be drawn, labelled or judged by a person.

What that came to, measured: **800 training tables, 22 minutes of simulator
time on this laptop, 2,012 demonstrations.** Most of the teacher's pushes are
not demonstrations. Of the 3,554 pushes it made, 1,533 were the 5 mm test
pushes that settle whether a glass slides, and those belong to the shared
tipping check rather than to the chooser. Of the remaining 2,021 real pushes,
only **9 had to be thrown away** — 8 toppled a glass and 1 pushed one out of
the zone.

Two things about the recording decide what the policy can and cannot learn. The
teacher works from the numeric readings `look()` hands over, and the student
works from the picture of the same table at the same moment, so any push that
turned on a difference of a millimetre between two readings is a push the
student is being asked to justify from pixels. And the jaw's report of what it
felt during the push arrives after the chunk has been chosen, so it is in the
recording but not in the observation the model is asked to act on.

**The data is free in the sense that matters, and that is a privilege of
working in a simulator.** On a real arm this is the expensive part of the whole
exercise and usually the part that decides whether a method is affordable at
all: somebody sits with a controller and teleoperates the task hundreds of
times, the recordings disagree with each other, and the robot wears out. Here a
program does it unattended. Any judgement in this book about whether
fine-tuning is worth its price should carry that qualification.

Free data is not neutral data, and this solution inherits two things from its
teacher.

**Its ceiling is solution 2.** Behaviour cloning fits the teacher's choices.
There is no reward in it, nothing scores the policy's own attempts, and nothing
ever shows it a push better than one the teacher made. So on the pushes it
imitates, this solution cannot be better at pushing than solution 2 is at its
best. If it scores above solution 2, that needs explaining rather than
celebrating.

**It is fitted on a biased sample of its teacher.** A demonstration that
toppled a glass, pushed one out of the zone, jammed or never touched anything
is not something to imitate, so it is discarded — and what is discarded is
exactly the set of situations the teacher handled badly. What is left is a
picture of solution 2 in the cases where solution 2 was right. On this examiner
that missing half is tiny, though: 9 pushes in 2,021, four tenths of one per
cent. Knowing the size changes what the worry is. The hard cases are nearly
absent not because they were filtered out but because **the teacher almost
never meets one**, so a student fitted on that set has never been shown a
difficult table.

**So what can fine-tuning add beyond its teacher?** Not better pushes: the best
push in the training set is the best push the policy has ever seen. What it can
add is robustness where the teacher was brittle. Where the teacher's ranking
was close to arbitrary between two candidates, averaging over many tables gives
something less arbitrary than either. Where the teacher's geometry turned on a
measurement two millimetres out, a policy fitted on what actually happened
across many such cases can behave sensibly rather than following the arithmetic
into a mistake. And the borrowed weights contribute a general sense of how a
pushing motion goes, which the teacher does not have at all, because the
teacher's motion comes from a macro.

The standard repair for the states the teacher never visits has a name and is
cheap here. **DAgger**, dataset aggregation, runs the half-trained policy, lets
it reach those states, and asks the teacher what it would have done at each of
them. The dataset then covers where the learner goes rather than where the
teacher goes. It normally costs a person to label every such state; here it
costs a call into solution 2, which is a program. It is a prescription in this
document rather than code that exists, and it belongs to this solution and to
solution 3 equally.

One last point holds the comparison with solution 3 still. Both solutions learn
from the same demonstration set, drawn from the same training half of the
tables, so between those two the data is held still and the borrowing is what
differs. This solution is therefore in two pairs at once, and they ask
different questions.

## 4. Whether anything but the training differs

A matched pair invites one particular mistake: saying that nothing varies
except the training when something else does. Going through the contract item
by item, most of it is genuinely held still. The tables are the same tables and
the first look at a given table is identical for every solution. The readings
carry the same error. The rendered view from the top is the same view. The
output is a chunk of waypoints in both. The marking is the same scorecard. The
shared topple check runs on both, unchanged. And the instruction in words is
the same instruction, which is a thing to keep deliberately rather than assume,
since giving the fine-tuned model better-worded instructions would quietly add
a second variable.

**At the output there is something that looks like a second change.** A model
like this produces numbers in an action space: so many values per waypoint,
each with a range and a meaning fixed by the robots the model was fitted on.
This cell's action space is not one of those. It is a jaw, held level,
travelling a short distance across a table at one height, on an arm the
borrowed recordings were not made on. So the numbers the model returns have to
be read as waypoints for this jaw, and [solution
5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) settles what that
reading involves: **the convention is chosen once and used by both**, so that
what a waypoint number means, which frame it is in and where a height of zero
sits are the same in both halves of the pair.

What the training changes is not that convention but whether the model has ever
been asked to speak in it. Solution 5 depends on the borrowed model happening
to emit numbers that, read through the agreed convention, make sense for this
table; nothing fitted them, so nothing guarantees their scale. This solution's
training targets are recordings of real pushes on this examiner, already
expressed in that same convention, so the ranges it is trained to produce are
this cell's ranges. **That is a property of the trained weights rather than a
second thing changed beside them.** The configuration is held still for both,
and the scale of what comes out is whatever the weights emit, so saying the
weights were trained and saying the scale moved are one statement said twice.
The pair is a clean measurement. [The matched pair in the book on telling the
glasses
apart](../../08_seeing-the-glasses/08_the-same-model-fine-tuned/01_what-it-is.md)
needed a longer argument at this point because its second change was a real
one: a list of category names is part of how a model is configured and could in
principle have been altered with no training at all. Here there is no such
separate part.

**One thing the convention settles reaches into the physics, and it was not
obvious until the code was written.** A chunk holds the number of waypoints the
borrowed model emits in one pass, which is fifty, and the examiner consumes
waypoints a fixed period apart, so a chunk is two and a half seconds of motion
whatever it contains. The teacher's push, once the examiner has sampled it, is
a hundred waypoints or more, because the teacher feels forward at 10 mm/s and
pushes at 20. Fitting that push into a chunk means resampling it, and that
makes the student's jaw travel about 36 mm/s where its teacher travelled at 10
and 20. So **the student does not merely imitate its teacher's pushes; it makes
them faster**, and the glasses are pushed by a jaw with more momentum behind
it. It is not free to go as fast as it likes — the examiner holds a commanded
path to the jaw's top speed of 200 mm/s, past which a leg simply takes longer —
but a chunk the model invents can reach that cap, and then the cap decides how
fast the push really is. The alternatives are to change the chunk length, which
is the borrowed model's own, or to ask the model several times during one push,
which would spend several of the shared budget's pushes on one. It does not
disturb the pair, because solution 5's chunks are two and a half seconds of
motion too.

**There is one place where the pair could be made unfair, and it should be
named rather than hidden.** A careless convention hurts solution 5 much more
than it hurts this solution, because this solution's training can absorb a poor
convention while its partner's cannot. If the convention puts the borrowed
model's natural range badly out of scale for this table, solution 5 fails at
something other than the question being asked, and the gap this pair reports is
then the sum of what training bought and what a careless convention cost, with
no way to separate the two afterwards. So the convention has to be chosen as
well as it can be, recorded with solution 5, and left alone once both have run.

## 5. What fine-tuning closes, and what it cannot touch

This is the section the matched pair exists for. Solution 5's weaknesses are
known, and the honest exercise is to go through them one at a time and say
which the training repairs and which it inherits untouched.

**The domain gap closes, and this is the large one.** A model used across such
a gap fails in a characteristic way: not by producing nonsense, but by
producing confident, plausible, wrong answers, which is worse because nothing
further along looks suspicious. A chunk of waypoints that is smooth and well
formed and aimed at nothing in particular is exactly that kind of failure.

That gap has now been measured, and it is wider than the prose suggested.
Before the training has taken a single step the correction is still zero, so
the model is exactly solution 5, and asking it for a chunk on tuning tables
puts its waypoints a median of **320 mm** from the teacher's, and 658 mm away
at worst. The glass zone is 320 mm by 360 mm. So the borrowed model's answer is
not a push aimed at the wrong glass; it is a smooth motion somewhere else on
the table entirely. Five hundred steps of training cut that to 84 mm.

![The glass zone drawn to scale with a teacher's push on it, and two rings round that push: one of 320 mm, the median distance from the teacher's waypoints to the untrained model's, which is as wide as the zone itself, and one of 84 mm, the same measurement after five hundred steps of training.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-how-far-the-answer-was.png)

Fine-tuning removes the gap by construction, because the inputs the model is
fitted on are the inputs it will be asked about. The pale blue of a glass
against the tan of the table, the outline leaning outwards from the point below
the camera, the bare table, one kind of glass to a table: all of those are
simply what a table looks like, as far as the fine-tuned model is concerned.

**The scale of the actions stops being left to chance** — and that turns out to
be two claims, of which only one held.

The *height* was learned, convincingly. Solution 5 measures its own chunks and
reports that they come no lower than 209 mm above the table, so the borrowed
model essentially never brings the jaw down to the glasses at all. The
fine-tuned model's chunks come down to 50 mm, which is the height the gripper
pushes at. That is the model having learned from this examiner's own pushes
that a push happens on the table rather than above it, and it is the clearest
single sign in these measurements that the domain gap closed.

The *length* was not. The fine-tuned chunks still cover about 315 mm of table
where the teacher's covered 89, and the jaw moves through them at a median of
about 90 mm/s where the demonstrations run at 36. That is better than solution
5's 844 mm, and still three times too far. So the model learned where a push
happens long before it learned how far one goes, and a push three times too
long on a crowded table is a push into a neighbour.

![The same table seen from the side with three chunks drawn on it: the borrowed model's, which stays 209 mm up and runs 844 mm across, the fine-tuned model's, which comes down to the 50 mm the jaw pushes at but still runs 315 mm across, and the teacher's, which is at the same height and 89 mm long.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-the-height-not-the-length.png)

**Something like friction is absorbed, and this needs care rather than
celebration.** Nothing in the cell measures friction and the examiner never
reveals it, so neither solution can know it. But the examiner holds the same
coefficients on every table, and every demonstration was produced under them,
so a fine-tuned policy can absorb this examiner's own friction into its weights
without any term in it standing for friction: it learns how far a glass of this
kind tends to go for a push of this length. That is a real gain on this
examiner and a liability anywhere else. What the model holds is a constant, not
a way of measuring one. Change the table and the policy is confidently wrong in
exactly the direction that topples a glass, because the height at which a glass
slides rather than tips is set by that same coefficient. Solution 5 has no such
memory — and no such ability either.

Now the weaknesses that survive.

**The force reading still has nowhere to go.** [The
examiner](../02_the-examiner.md) calls the jaw's report of what it felt the only
channel through which friction is observable at all, and this model's inputs
are a picture, a sentence and the joint readings. Training cannot add a fourth
input, so that channel stays closed in both halves of the pair. The absorbed
constant above is not a way of reading it.

**The instruction is still nearly dead weight.** SmolVLA is a
vision-language-action model, and the language is the part that lets one model
be told to do different things in different words. This problem has one task,
so the same words go in on every table. Worse, the training makes it harder to
pretend otherwise: when every example carries the identical instruction,
nothing penalises a model for ignoring the language channel, so the sensible
expectation is that the fine-tuned model learns to ignore it. That is a fact
about a cell with one task and not about the language half itself, so nothing
here is evidence for or against vision-language-action models in general. But
the model is paying for a capability neither solution uses, and that cost
appears in its size, its memory and the price of its forward pass. It is a real
argument for [solution
3](../06_imitation-from-demonstrations/01_what-it-is.md), whose ACT policy
carries no language machinery at all.

**The refusal still is not the policy's, and it cannot become the policy's.** A
policy is a function from an observation to an action; there is no field in it
for a rule, so there is no way to tell it never to topple a glass. The topple
limit therefore stays where [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) puts it, outside all
six solutions. In one respect fine-tuning makes this worse rather than better:
the teacher refused the glasses it should refuse, so the training set contains
no example of a glass that must not be pushed, and the policy has never been
shown the case. It proposes a push on such a glass as readily as on any other,
and the shared check stops it. The safety work is being done by the geometry,
in both solutions.

**It still cannot explain a refusal.** Solution 2 can say that a glass tips
before it slides because its foot is narrow enough that the limit falls below
the jaw's top edge, and the number can be printed. A policy that was stopped
has nothing to say, and this project treats a refusal as a result that has to
carry a reason.

**A surprise in the middle of a chunk is still carried out.** Committing to a
short run of waypoints is what keeps the policy steady over a motion rather
than wobbling from one step to the next, and it is the reason [the
examiner](../02_the-examiner.md) accepts waypoints at all instead of forcing
every solution down to three numbers. The cost of committing is that something
unexpected during the chunk — a glass that sticks, a neighbour met earlier than
the readings implied — is met by a policy still executing what it decided
before. Fine-tuning changes how often a surprise arrives. It does not change
what happens when one does, and nothing else does either: the early abort that
would read the jaw's force as the push develops is a design in [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) and nothing in the
examiner does it. What the examiner does is stop at a jam, which is a much
higher force than a glass beginning to tip, and `follow()` is explicit that
below that level the chunk is carried out as it was given. That falls on both
halves of the pair equally, so it does not disturb the pair; it does mean the
pair's topple counts are what the limit computed before the jaw moves achieves
on its own.

**The run-time cost is unchanged**, because the correction folds into the
weights. **And the input's own error is unchanged.** Both solutions are handed
readings carrying the error measured for [telling the glasses apart in a
picture](../../08_seeing-the-glasses/11_the-results.md), and no amount of
training makes a measurement truer than it was. What training can do is make
the policy behave sensibly when a reading is a little wrong, because it was
fitted on recordings in which readings were a little wrong. That is a smaller
claim than making the reading right.

## 6. Two ways training on one cell's pushes goes wrong

Fine-tuning is cheap and it is not free of risk, and the two risks have names
worth knowing.

**Catastrophic forgetting.** Continuing a model's training on a narrow set of
examples moves its weights away from the general answer they held, so the model
becomes better at this cell and worse everywhere else. Low-rank adaptation
softens this, because the borrowed numbers are never overwritten and the
correction can in principle be removed to get the original model back. Softened
is not absent, though: the corrected model is the one that runs, and it would
be a poor policy for any other robot or any other task. Within this project
that is not a loss, because the only tables this model will be shown are this
examiner's. It does mean the correction is a narrow asset that has to be kept
in step with the cell.

**Overfitting.** A model fitted on a small set of examples can learn the
examples instead of the thing the examples are of. Here that would mean
learning the tables rather than the pushing, and in the worst case which push
follows which table. The examiner guards against it twice. The tables are
numbered and the numbers are split, so no solution is ever marked on a table it
learned from, and overfitting appears as a gap between the two halves rather
than hiding inside one number. And the demonstrations cost only simulator time,
so the training set can be made large and varied for nothing.

The two risks pull in opposite directions in one respect. Training longer and
harder on this examiner's pushes closes the domain gap further while making
both forgetting and overfitting more likely. So there is a sensible amount of
training rather than a maximum, and the held-out half of the tables is what
decides where it is. That is how the training below stopped at a thousand
steps: between step 500 and step 1,000 the fitting loss halved while the error
on tuning tables did not improve.

A third thing is not a risk of training but a consequence of it, and it decides
how this solution is measured at all. A policy of this kind is stochastic:
asked the same question twice it may act differently, because the action is
drawn rather than computed. Training itself varies with its own random seed, so
the same recipe run twice gives two policies of different quality. [The
examiner](../02_the-examiner.md) requires several training seeds and several
evaluation runs for exactly this reason, and the scorecard carries the spread.
**This matters most to this document of any in this book**, because the thing
being measured is the gap between two solutions, and a gap smaller than either
solution's own spread has not been shown to exist.

## 7. A second way — the same fine-tune on a larger model

One model cannot answer the obvious next question: would a markedly larger
foundation model do better? **The second way is the same fine-tune on π0.5** —
the same demonstrations, the same low-rank adaptation, the same examiner and
the same marking, with a much larger borrowed model in the middle. Everything
except the model is held still, so the gap would measure what size is worth.
The library this problem installs already carries π0.5 beside SmolVLA, so it is
the same training loop pointed at different weights rather than new machinery.

**It is not built, and the reason is about where mistakes are found rather than
about the model.** Almost everything that goes wrong here is in the pipeline —
rendering the view from the top, recording the demonstrations in a form the
training loop accepts, carrying the action space across, getting the evaluation
to run at all — and each is found by a run that fails. SmolVLA runs on a
laptop, so those mistakes are found for nothing. Starting on the large model
means debugging at a weekend of rented accelerator, of order a hundred dollars,
which is how a budget disappears without a single comparison being produced.

← [The code](02_the-code.md) · [A worked example](04_a-worked-example.md) →
