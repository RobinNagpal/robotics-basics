# The same foundation model, fine-tuned here — how it works

This page explains what happens inside this solution, part by part. It follows
[what it is](01_what-it-is.md), which states the question the solution answers
and the single idea it rests on, and it assumes you have read that page first.
By the end of this one you will understand what the method is built from, what
each part does with what the part before it produced, and which part decides
the answer.

## Contents

1. [Fine-tuning — continuing somebody else's training](#1-fine-tuning--continuing-somebody-elses-training)
2. [Low-rank adaptation — a small correction instead of a large change](#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
3. [Where the demonstrations come from, and what they cost](#3-where-the-demonstrations-come-from-and-what-they-cost)
4. [Whether anything but the training differs](#4-whether-anything-but-the-training-differs)
5. [What fine-tuning closes, and what it cannot touch](#5-what-fine-tuning-closes-and-what-it-cannot-touch)
6. [Two ways training on one cell's pushes goes wrong](#6-two-ways-training-on-one-cells-pushes-goes-wrong)
7. [A second rung: the same fine-tune on a larger model](#7-a-second-rung-the-same-fine-tune-on-a-larger-model)

## 1. Fine-tuning — continuing somebody else's training

Because fine-tuning is the single thing that separates this solution from its
partner, it is worth setting out carefully and in plain words.

**Training** a network means showing it an example, comparing what it produced
against the answer that was wanted, and nudging every weight a little in the
direction that would have helped. Repeat that over many examples and the
weights settle at values that produce good answers. **Training from a random
start** means the weights begin as noise, so the nudges have to build every
part of the model out of nothing. **Fine-tuning** means the weights begin at
values somebody else's training already settled, so the nudges have much less
to do.

The reason that is so much cheaper is clearest when it is stated in terms of
what the data has to pay for. Every weight in a model is a number the training
data has to determine. If the data does not hold enough information to pin a
weight down, that weight ends up fitted to accidents of the particular
examples it was shown rather than to anything real. So the amount of data
needed grows with the number of weights that have to be determined from
nothing, and fine-tuning changes that sum almost entirely: the great majority
of the weights already sit at values that work, and the data only has to adjust
them.

A comparison from mathematics makes the shape of this clear. Fitting from a
random start is like solving for every coefficient of a long polynomial with no
idea of any of them. Fine-tuning is like being handed a polynomial that already
fits a similar curve and being asked to adjust its coefficients a little. The
second problem needs far fewer points before it is well determined, because
most of the answer is already there.

There is a second saving, about time rather than data, and for a model that
acts rather than describes it has two halves. A model fitted on pictures holds,
in its early layers, detectors for things common to all vision: an edge, a
corner, a shading that runs across a curved surface. Those transfer almost
completely, because an edge is an edge, and a rendered glass standing on a bare
table has a strong edge round it. A model fitted on robot motion holds
something similar about motion: that a trajectory is smooth, that a jaw
approaches a thing before it touches it, that a motion has a beginning and an
end. Those transfer too, because they are properties of moving a tool rather
than properties of any one robot. A random start spends much of its training
discovering both of those again. Fine-tuning does not, so only the later
judgement has to change — what in this picture is a glass worth pushing, which
way, and how far.

That gives an honest expectation rather than a result, and it should be read as
one. What carries over best is the cheap general machinery at the bottom of the
model. What carries over worst is the judgement at the top, which was fitted to
decide what to do next in rooms that look nothing like this one, with grippers
shaped nothing like this one, on tasks that were mostly not pushing. So
fine-tuning here has more work to do than the usual advice about borrowed
models implies, and still far less work than a random start. That last claim is
the one [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md) exists to check from
the other side, because it fits a policy here from random numbers on the very
same demonstrations.

## 2. Low-rank adaptation — a small correction instead of a large change

Fine-tuning as described above moves every weight, and on a model of this size
that is the expensive way to do it. Low-rank adaptation is the cheap way, and
it is what this solution uses.

Start with what a layer of a network does. It takes a list of numbers in,
multiplies it by a table of numbers, and hands a list of numbers out. The table
is the weights of that layer, and a model of this size holds many such tables,
some of them large. Ordinary fine-tuning changes every number in every table.

**Low-rank adaptation leaves every borrowed number exactly where it is, and
learns a correction that is added to it.** The correction is the same size as
the table it corrects, so the layer still does the same work. What makes it
cheap is that the correction is not allowed to be an arbitrary table. It is
forced to be the product of two thin tables: one that squeezes the incoming
list down to a handful of numbers, and one that expands that handful back out
to full width. Because the squeeze is narrow, the two thin tables together hold
far fewer numbers than the table they correct, even though their product is as
wide as it.

The comparison from mathematics is the useful one, and it is the same move this
project meets elsewhere. A table of numbers can be written as a sum of simple
patterns, each pattern being one outward direction paired with one inward
direction, and the number of patterns needed is the table's **rank**. Forcing
the correction through a narrow squeeze is forcing it to be a sum of only a
handful of such patterns, which is exactly the move of approximating a large
table by a few of its strongest patterns, or a curve by a few terms of a
series.

**The practical reason this matters here is accelerator memory, and the
arithmetic is worth doing.** Training does not only have to hold the weights.
For every weight that is being changed it also has to hold that weight's
gradient, which says which way to nudge it, and the optimiser's running
averages of that gradient, which are what make the nudges stable. Those add up
to several times the size of the model itself. With low-rank adaptation only
the correction's numbers are being changed, so only they carry gradients and
optimiser state, and the borrowed weights sit there as a fixed cost. What has
to fit in the accelerator is then the model's own size plus a little, rather
than several times the model's size.

The brief numbers for the larger family make the difference plain. On π0,
which holds about 3.3 billion parameters, a low-rank fine-tune needs more than
22 GB of accelerator memory and a full fine-tune needs more than 70 GB. The
first is an accelerator that can be rented by the hour; the second is not
something this project is going to reach for. SmolVLA is much smaller — about
450 million parameters, a few gigabytes at inference, and it runs on a laptop
— and **at that size the saving is larger than it needs to be**: the measured
figure for the training below is 1.02 GiB, which fits on this machine without
anything being rented. The arithmetic above is still what makes that true, but
the conclusion it was written to support — that an accelerator has to be
rented — is only the conclusion for the larger model.

**The trade is that it adapts less deeply, and this has to be stated plainly
because it decides how the pair's result should be read.** The correction is
confined to a handful of directions in each table, so a change that genuinely
needs the whole table cannot be expressed. Where the new task is near the old
one, that costs nothing, because the change needed is small and a few
directions hold it comfortably. Where the new task is far from the old one, a
full fine-tune would go further. This cell is far: rendered pictures of a
simulated table, one gripper, one motion, and a kind of outcome none of the
borrowed datasets contained. So this is exactly the case where the trade bites,
and the consequence for the comparison is that **the gap this pair measures is
a lower bound on what fine-tuning could buy**, not the whole of it. A result
that says low-rank fine-tuning bought little does not say that fine-tuning
bought little.

One more property of the correction is worth knowing, because it decides the
compute column on the scorecard. Once training has finished, the two thin
tables can be multiplied out and the result added into the borrowed table, so
what is left is a single table of the original size. The fine-tuned model is
then exactly as large and exactly as fast as the downloaded one. **So this
solution and its partner cost the same to run**, and whatever separates their
scores cannot be explained by one of them having been given more computation
at run time.

## 3. Where the demonstrations come from, and what they cost

Fine-tuning needs examples, which here means recorded pushes with what was
seen beside what was done, and this is where the arrangement of the six
helps.

[Solution 2](../05_geometry-generates-a-model-ranks/01_what-it-is.md) generates pushes by geometry and ranks them
with a fitted ranker, and it is a working chooser of pushes. Run it on the
bench over the training half of the tables and almost every push it makes is a
demonstration. The observation is what this model takes as its input: the
rendered view of the table from the top taken at the moment the push was
chosen, the one instruction, and the arm's own pose. The action is the path the
jaw really followed, which the bench writes down on every action, so a
demonstration is a recording of the shared contract being satisfied and nothing
in it had to be drawn, labelled or judged by a person.

What that came to, measured: **800 training tables, 22 minutes of simulator
time on this laptop, 2,012 demonstrations.** Two things about the count are
worth knowing. **Most of the teacher's pushes are not demonstrations**: of the
3,554 pushes it made, 1,533 were the 5 mm test pushes that settle whether a
glass slides, and those belong to the shared tipping check rather than to the
chooser, so none of them is a target. And of the remaining 2,021 real pushes,
**only 9 had to be thrown away** — 8 toppled a glass and 1 pushed one out of
the zone. The section below warns at length about what filtering to successes
throws out, and on this bench the answer is four tenths of one per cent. That
is a quantity worth having rather than a worry worth carrying.

Two things about that recording are worth noticing, because they decide what
the policy can and cannot learn. The teacher works from the numeric readings
`look()` hands over, and the student works from the picture of the same table
at the same moment, which is the same information in a different form. So the
student has to recover from a picture what its teacher was given as numbers,
and any push that depended on a difference of a millimetre between two readings
is a push the student is being asked to justify from pixels. And the jaw's
report of what it felt during the push — the force, and how far it travelled
before touching — arrives after the chunk has been chosen, so it is in the
recording but not in the observation the model is asked to act on.

**That makes the data free in the sense that matters, and it is worth saying
why that is a privilege of working in a simulator.** On a real arm this is the
expensive part of the whole exercise and usually the part that decides whether
a method is affordable at all: somebody sits with a controller and teleoperates
the task hundreds of times, the recordings disagree with each other, and the
robot wears out. Here a program does it unattended. Any judgement made in this
book about whether fine-tuning is worth its price should carry that
qualification, because on a real arm the price would be quite different.

**But free data is not neutral data, and this solution inherits two things
from its teacher that have to be said without softening.**

**Its ceiling is solution 2.** Behaviour cloning fits the teacher's choices.
There is no reward in it, nothing scores the policy's own attempts, and nothing
ever shows it a push better than one the teacher made. So on the pushes it
imitates, this solution cannot be better at pushing than solution 2 is at its
best. If this solution scores above solution 2 on the scorecard, that is a
result that needs explaining rather than a result to celebrate, and the next
section gives the one explanation that is honest.

**Filtering to successes trains it on a biased sample of its teacher.** A
demonstration that toppled a glass, pushed one out of the zone or ended in a
jam is not something to imitate, so those recordings are discarded. That is the
right thing to do and it has a cost that is easy to miss: what is discarded is
exactly the set of situations the teacher handled badly. What is left is a
picture of solution 2 in the cases where solution 2 was right. The policy is
therefore fitted on the easy half of its teacher's own experience, and the hard
half — the glass that stuck, the jaw that met a neighbour first, the push that
went nowhere — is missing from its training by construction.

**On this bench that half is tiny, and knowing the size changes what the
argument is worth.** Solution 2 is good enough that 9 pushes in 2,021 had to be
discarded. So the missing hard half is not a hole in the training set; it is
nine examples. What this really says is something less comfortable than the
usual worry: the hard cases the teacher handled badly are nearly absent not
because they were filtered out but because the teacher almost never meets one,
and a student fitted on that set has never been shown a difficult table because
the teacher does not produce difficult tables. DAgger is still the repair, and
it is the repair for a different reason than the filtering: it would put the
*learner* in states the teacher never visits, and there are plenty of those
however good the teacher is.

**So what can fine-tuning add beyond its teacher?** One thing, and it is worth
being precise about it, because it is the only honest claim in this direction.
Not better pushes: the best push in the training set is the best push the
policy has ever seen. What it can add is **robustness in situations the teacher
handled badly**. Where the teacher's ranking was close to arbitrary between two
candidates, averaging over many tables gives something less arbitrary than
either. Where the teacher's geometry was brittle because a measurement was a
couple of millimetres out, a policy fitted on what actually happened across
many such cases can behave sensibly rather than following the arithmetic into a
mistake. And the borrowed weights contribute a general sense of how a pushing
motion goes, which is a thing the teacher does not have at all, because the
teacher's motion comes from a macro. That is the whole of the upside, and it is
about not falling over in unfamiliar situations rather than about pushing
better.

The standard repair for the missing hard half has a name and it is cheap here.
**DAgger**, dataset aggregation, runs the half-trained policy, lets it reach
states the teacher never visits, and asks the teacher what it would have done
at each of those states. The dataset then covers where the learner goes rather
than where the teacher goes. It normally costs a person to label every such
state; here it costs a call into solution 2, which is a program. This is a
prescription in this document rather than code that exists, and it belongs to
this solution and to solution 3 equally, since both learn from the same
demonstrations.

One last point about the data holds the comparison with solution 3 still. Both
solutions learn from the same demonstration set, drawn from the same training
half of the tables. So between those two the data is held still and the
borrowing is what differs, which makes that pair a test of whether borrowed
weights are worth having when the examples are the same. This solution is
therefore in two pairs at once, and they ask different questions.

## 4. Whether anything but the training differs

A matched pair invites one particular mistake, and it is the mistake of saying
that nothing varies except the training when something else does. [The matched
pair in the book on telling the glasses
apart](../../08_seeing-the-glasses/08_the-same-model-fine-tuned/01_what-it-is.md) shows
how to avoid it. There, the fine-tuning also replaces the model's borrowed list
of everyday categories with a single class, and that document does not claim
otherwise. What it does instead is show that the second change comes **with**
the training and cannot be had separately, so that nothing varies which the
training did not bring. The same care is owed here, but that answer cannot
simply be carried across, so it has to be worked out: beyond the weights, what
else is really different between solution 5 and this one?

Going through the contract item by item, most of it is genuinely held still.
The tables are the same tables, drawn from the same numbers, and the first look
at a given table is identical for every solution. The readings carry the same
error. The rendered view from the top is the same view. The output is a chunk
of waypoints in both. The marking is the same scorecard. The shared topple
check runs on both, unchanged. And the instruction in words is the same
instruction, because the task has one — which is a thing to keep deliberately
rather than assume, since giving the fine-tuned model a better-worded
instruction would quietly add a second variable to the pair.

**At the output there is something that looks like a second change, and it is
worth seeing why it is not one.** A model like this produces numbers in an
action space: so many values per waypoint, each with a range and a meaning
fixed by the robots the model was fitted on. This cell's action space is not
one of those. It is a jaw, held level, travelling a short distance across a
table at one height, on an arm the borrowed recordings were not made on. So the
numbers the model returns have to be read as waypoints for this jaw, and
[solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) sets out what that reading involves
and settles it: **the convention is chosen once and used by both**, so that
what a waypoint number means, which frame it is in and where a height of zero
sits are the same in both halves of the pair. That is held still, and it has to
be, because a pair is only clean while everything except the training is held
still.

What the training changes is not that convention but whether the model has
ever been asked to speak in it. Solution 5 depends on the borrowed model
happening to emit numbers that, read through the agreed convention, make sense
for this table; nothing fitted them, so nothing guarantees their scale. This
solution's training targets are recordings of real pushes on this bench,
already expressed in that same convention, so the ranges the model is trained
to produce are this cell's ranges. **That is a property of the trained weights
rather than a second thing changed beside them.** That other pair needed its
argument because its second change was a real one: a list of category names is
part of how a model is configured and not only a value inside it, so it could
in principle have been altered without any training, and that document had to
show that the training forced it. Here there is no such separate part. The
configuration, which is the convention for reading an action, is held still for
both, and the scale of what comes out is whatever the weights emit, so saying
the weights were trained and saying the scale moved are one statement said
twice. So **nothing varies between the two that the training did not bring**,
and the pair is a clean measurement.

**One thing the convention settles turned out to reach into the physics, and it
is worth naming because it was not obvious until the code was written.** A
chunk holds the number of waypoints the borrowed model emits in one pass, which
is fifty, and the bench consumes waypoints a fixed period apart, so a chunk is
two and a half seconds of motion whatever it contains. The teacher's push, once
the bench has sampled it, is a hundred waypoints or more, because the teacher
feels forward at 10 mm/s and pushes at 20. Fitting that push into a chunk means
resampling it, and resampling it means the student's jaw travels about 36 mm/s
where its teacher travelled at 10 and 20. So **the student does not merely
imitate its teacher's pushes; it makes them faster**, and the glasses are
pushed by a jaw with more momentum behind it. It is not free to go as fast as
it likes: the bench holds a commanded path to the jaw's top speed of 200 mm/s,
past which a leg simply takes longer, so spacing buys speed only up to the
speed the arm has. A demonstration's 36 mm/s is nowhere near that, but a
chunk the model invents can be, and then the cap decides how fast the push
really is. This is forced rather than
chosen: the alternatives are to change the chunk length, which is the borrowed
model's own, or to ask the model several times during one push, which would
spend several of the shared budget's pushes on one. It does not disturb the
pair, because solution 5's chunks are two and a half seconds of motion too.

**There is one place where the pair could nonetheless be made unfair, and it
should be named rather than hidden.** The agreed convention is a choice, and a
careless choice hurts solution 5 much more than it hurts this solution, because
this solution's training can absorb a poor convention while its partner's
cannot. If the convention puts the borrowed model's natural range badly out of
scale for this table, solution 5 fails at something other than the question
being asked, and the gap this pair reports is then the sum of what training
bought and what a careless convention cost, with no way to separate the two
afterwards. So the convention has to be chosen as well as it can be, recorded
with solution 5, and left alone once both have run.

## 5. What fine-tuning closes, and what it cannot touch

This is the section the matched pair exists for. Solution 5's weaknesses are
known, and the honest exercise is to go through them one at a time and say
which the training repairs and which it inherits untouched, rather than letting
"it is fine-tuned" stand in for an answer.

**The domain gap closes, and this is the large one.** Solution 5 is shown a
kind of input it was never fitted on, and a model used across such a gap fails
in a characteristic way: not by producing nonsense, but by producing confident,
plausible, wrong answers, which is worse because nothing further along looks
suspicious. A chunk of waypoints that is smooth and well formed and aimed at
nothing in particular is exactly that kind of failure.

**That gap has now been measured, and the number is larger than the prose
suggests.** Before the training has taken a single step the correction is
still zero, so the model is exactly solution 5, and asking it for a chunk on
tuning tables the teacher had also been run over puts its waypoints a median of
**320 mm** from the teacher's, and 660 mm away at worst. The glass zone is
320 mm by 360 mm. So the borrowed model's answer is not a push aimed at the
wrong glass; it is a smooth motion somewhere else on the table entirely, which
is what reading a model across a domain gap this wide actually looks like.

Fine-tuning removes the gap by construction, because the inputs the model is
fitted on are the inputs it will be asked about. The pale blue of a glass against the tan of the table,
the same blue whatever the kind, the outline leaning outwards from the point
below the camera, the bare table, one kind of glass to a table: all of those
are simply what a table looks like, as far as the fine-tuned model is
concerned, because that is what every table in its training set looked like.

**The scale of the actions stops being left to chance**, for the reason the
previous section gives. The model is trained towards recordings of real pushes
on this bench, so the size of the motion it proposes is the size this table
needs, rather than the size the borrowed recordings happened to use.

**That turns out to be two claims, and only one of them held.** The *height*
was learned, and convincingly. Solution 5 measures its own chunks and reports
that they come no lower than 209 mm above the table: the borrowed model
essentially never brings the jaw down to the glasses at all. The fine-tuned
model's chunks come down to 50 mm, which is the height the gripper pushes at.
That is the model having learned from this bench's own pushes that a push
happens on the table rather than above it, and it is the clearest single sign
in these measurements that the domain gap closed.

The *length* was not learned. The fine-tuned chunks still cover about 315 mm
of table where the teacher's covered 89, and the jaw moves through them at
about 90 mm/s where the demonstrations it learned from run at 36 — better than
solution 5's 844 mm, and still three times too far.
So the model learned where a push happens long before it learned how far one
goes, and a push three times too long on a crowded table is a push into a
neighbour. The toppled count in this solution's own README is that. The
honest answer to "does the scale of the actions stop being left to chance" is
therefore: partly, and the part that was left is the part that topples
glasses.

**Something like friction is absorbed, and this one needs care rather than
celebration.** Nothing in the cell measures friction and the bench never
reveals it, so neither solution can know it. But the bench holds the same three
coefficients on every table, and every demonstration was produced under them.
So a fine-tuned policy can absorb this bench's own friction into its weights
without any term in it standing for friction: it learns how far a glass of this
kind tends to go for a push of this length, which is a consequence of the
friction it was never told. That is a real gain on this bench and a liability
anywhere else. What the model holds is a constant, not a way of measuring one.
Change the table and the policy is confidently wrong in exactly the direction
that topples a glass, because the height at which a glass slides rather than
tips is set by that same coefficient. So part of whatever this solution gains
over its partner is a memorised property of the bench, and that part would not
survive the move to a real table. Solution 5 has no such memory — and no such
ability either.

Now the weaknesses that survive.

**The force reading still has nowhere to go.** [The test
bench](../02_the-test-bench.md) calls the jaw's report of what it felt the only channel
through which friction is observable at all, and this model's inputs are a
picture, a sentence and the joint readings. Training cannot add a fourth input,
so that channel stays closed in both halves of the pair, exactly as [solution
5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) describes it. What the training gives instead
is the absorbed constant above, which is not a way of reading the channel.

**The instruction is still nearly dead weight.** SmolVLA is a
vision-language-action model, and the language is the part that lets one model
be told to do different things in different words. This problem has one task, so
there is one instruction, and the same words go in on every table. Fine-tuning
does not change that, because the task is what it is. Worse, the training makes
it harder to pretend otherwise: when every example in a training set carries
the identical instruction, nothing in the training penalises a model for
ignoring the language channel entirely, so the sensible expectation is that the
fine-tuned model learns to ignore it. That is a fact about a cell with one task
and not about the language half itself, which this problem never asks for, so
nothing here is evidence for or against vision-language-action models in
general. The model is therefore paying for a capability neither solution uses,
and that cost appears in its size, in its memory and in the price of its
forward pass. It is a real argument for [solution
3](../06_imitation-from-demonstrations/01_what-it-is.md), whose ACT policy carries no language
machinery at all and is far smaller for it.

**The refusal still is not the policy's, and it cannot become the policy's.** A
policy is a function from an observation to an action; there is no field in it
for a rule, so there is no way to tell it never to topple a glass. The topple
limit therefore stays where [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) puts it, outside all six solutions,
as a check that reads every proposed push before the jaw moves. Fine-tuning
leaves that exactly as it was, and in one respect it makes the policy's own
behaviour here worse rather than better. The demonstrations were filtered to
successes and the teacher refused the glasses it should refuse, so the training
set contains no example of a glass that must not be pushed. The policy has
therefore never been shown the case. It will propose a push on such a glass as
readily as on any other, and the shared check will stop it. The safety work is
being done by the geometry, in both solutions, and that should not be credited
to the model in either.

**It still cannot explain a refusal.** Solution 2 can say that a glass tips
before it slides because its foot is narrow enough that the limit falls below
the jaw's top edge, and the number can be printed. A policy that was stopped
has nothing to say, and this project treats a refusal as a result that has to
carry a reason. So the reason comes from the shared check, not from the model,
in both halves of the pair.

**A surprise in the middle of a chunk is still carried out.** The model commits
to a short run of waypoints at once, which is the mechanism that keeps it
steady over a motion rather than wobbling from one step to the next, and it is
the reason [the bench](../02_the-test-bench.md) accepts waypoints at all instead of
forcing every solution down to three numbers. The cost of committing is that
something unexpected during the chunk — a glass that sticks, a neighbour met
earlier than the readings implied — is met by a policy that is still executing
what it decided before. Fine-tuning changes how often a surprise arrives, by
making the predictions better suited to this table. It does not change what
happens when one does.

**And the thing that was supposed to act inside a push is not built.** The
early abort — the monitor that reads the jaw's force as the push develops and
stops it the moment the contact stops behaving like a slide — is a design in
[pushing without toppling](../01_the-problem/03_pushing-without-toppling.md) and nothing in the
bench does it. What the bench does is stop at a jam, which is a much higher
force than a glass beginning to tip, and `follow()` is explicit that below that
level the chunk is carried out as it was given, because carrying it out as
given is the point of accepting one. So a surprise inside a chunk is not caught
by anything today. That falls on solution 5 and this solution equally, so it
does not disturb the pair; it does mean the pair's topple counts are what the
limit computed before the jaw moves achieves on its own.

**The run-time cost is unchanged.** It is a large neural network forward pass
per chunk in both, since the correction folds into the weights, and that cost
is why the scorecard carries a compute column at all.

**And the input's own error is unchanged.** Both solutions are handed readings
that carry the error measured for [telling the glasses apart in a
picture](../../08_seeing-the-glasses/11_the-results.md), and no amount of
training makes a measurement truer than it was. What training can do is make
the policy behave sensibly when a reading is a little wrong, because it was
fitted on recordings in which readings were a little wrong. That is a different and smaller claim
than making the reading right.

## 6. Two ways training on one cell's pushes goes wrong

Fine-tuning is cheap and it is not free of risk, and the two risks have names
worth knowing.

**Catastrophic forgetting.** Continuing a model's training on a narrow set of
examples moves its weights away from the general answer they held, so the model
becomes better at this cell and worse everywhere else. Low-rank adaptation
softens this, for a reason worth understanding rather than taking on trust: the
borrowed numbers are never overwritten, so what was general is still in there,
and the correction can in principle be removed to get the original model back.
Softened is not absent. The corrected model is the one that runs, and at run
time it describes a world of rendered tables with one kind of glass to a table.
It would be a poor policy for any other robot or any other task, and asking it
for one would be asking it about a world it was trained away from. Within this
project that is not a loss, because the only tables this model will be shown
are this bench's. It does mean the correction is a narrow asset that has to be
kept in step with the cell, and that is one more thing to maintain rather than
a fixed file to keep.

**Overfitting.** A model fitted on a small set of examples can learn the
examples instead of the thing the examples are of. Here that would mean
learning the tables rather than the pushing: which parts of the glass zone tend
to hold a glass, how many glasses tend to be present, which crowded pairs the
bench likes to draw, and in the worst case which push follows which table. Such
a policy scores well on the tables it was trained on and poorly on new ones.
Two things guard against it, and the bench already provides both. The tables
are numbered and the numbers are split, so no solution is ever marked on a
table it learned from, and overfitting appears as a gap between the two halves
rather than hiding inside one number. And the demonstrations cost only
simulator time, so the training set can be made large and varied for nothing,
which is the cheapest defence against overfitting there is.

The two risks pull in opposite directions in one respect, and knowing that
saves confusion. Training longer and harder on this bench's pushes closes the
domain gap further while making both forgetting and overfitting more likely. So
there is a sensible amount of training rather than a maximum, and the held-out
half of the tables is what decides where it is.

A third thing is not a risk of training but a consequence of it, and it belongs
here because it decides how this solution is measured at all. A policy of this
kind is stochastic: asked the same question twice it may act differently,
because the action is drawn rather than computed. Training itself varies with
its own random seed, so the same recipe run twice gives two policies of
different quality. [The bench](../02_the-test-bench.md) requires several training seeds
and several evaluation runs for exactly this reason, and the scorecard carries
the spread. **This matters most to this document of any in this book**, because
the thing being measured is the gap between two solutions, and a gap smaller
than either solution's own spread has not been shown to exist.

## 7. A second rung: the same fine-tune on a larger model

Everything above is about one model, and there is an obvious next question that
one model cannot answer: would a markedly larger foundation model do better?
That question is this solution's second rung.

**The rung is the same fine-tune on π0.5.** The same demonstrations, the same
low-rank adaptation, the same bench, the same marking, with a much larger
borrowed model in the middle. Because everything except the model is held
still, the gap between the two rungs measures what size is worth on this task,
in the same way the gap between this solution and solution 5 measures what
training is worth. It is also less work than it sounds: the version of LeRobot
this problem installs carries π0.5 beside SmolVLA, so the rung is the same
training loop pointed at a different policy and a different set of weights,
rather than new machinery. What it is not is affordable here, and that is the
whole of why it stays a prescription.

**Its cost is a weekend on a rented accelerator, which is of order a hundred
dollars.** That is honest and it is not nothing. It is also the affordable
corner of this family: π0, which belongs to it too, holds about 3.3 billion
parameters, and a full fine-tune of it needs more than 70 GB of accelerator
memory, which is why no full fine-tune of a model this size appears anywhere in
this book. Low-rank adaptation is what brings a model of that size within
reach at all, and it is the only way the rung is reached.

**It is a rung rather than the main line for one practical reason, and the
reason is about where mistakes are found.** Almost everything that will go
wrong in this solution is in the pipeline rather than in the model: rendering
the view from the top, recording the demonstrations in a form the training loop
accepts, carrying the action space across, choosing how long to train, and
getting the evaluation to run the trained policy against the bench at all. Each
of those is found by a run that fails. SmolVLA uses a few gigabytes at
inference and runs on a laptop, so on the small model every one of those
mistakes is found for nothing, and only a training run that is already correct
ever reaches rented hardware. Starting on the large model instead means
debugging a pipeline at a hundred dollars a weekend, which is how a budget
disappears without a single comparison being produced.

So the order is: get the small model working end to end, measure it against
solution 5, and only then rent the accelerator for the weekend that answers
whether size helps. If the small model's fine-tune turns out to buy little, the
rung is also the thing most worth trying next, because "a larger model" and "a
full fine-tune rather than a low-rank one" are the two directions the result
leaves open, and only the first of them is affordable here.

← [The same foundation model, fine-tuned here — what it is](01_what-it-is.md) · [The same foundation model, fine-tuned here — the code](03_the-code.md) →
