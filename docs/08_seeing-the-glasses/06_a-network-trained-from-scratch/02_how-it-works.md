# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [What exists in code, and what is a design](#1-what-exists-in-code-and-what-is-a-design)
2. [What a network is, and what training from scratch means](#2-what-a-network-is-and-what-training-from-scratch-means)
3. [Why nothing is borrowed, and what that buys](#3-why-nothing-is-borrowed-and-what-that-buys)
4. [The shape of the network](#4-the-shape-of-the-network)
5. [The first head: which pixels are glass](#5-the-first-head-which-pixels-are-glass)
6. [The second head: which way is the middle of my own glass](#6-the-second-head-which-way-is-the-middle-of-my-own-glass)
7. [From votes to glasses](#7-from-votes-to-glasses)
8. [The two rungs: where the labels come from](#8-the-two-rungs-where-the-labels-come-from)
9. [Rung one — labels from the answer key](#9-rung-one--labels-from-the-answer-key)
10. [Rung two — labels from the arm's own movement](#10-rung-two--labels-from-the-arms-own-movement)
11. [The training set](#11-the-training-set)

## 1. What exists in code, and what is a design

All six solutions are built, and this one is built in two layers, so it is
worth separating them plainly before going further.

**What exists.** A network of exactly the shape described below is already
written in this project's code. It has the two heads this document describes:
one channel saying whether a pixel is glass, and two channels holding the two
parts of the arrow. It is written in PyTorch and it runs on
this machine's integrated graphics through the MPS backend, which is the
interface PyTorch uses to reach graphics hardware on this kind of machine
rather than a dedicated graphics card. Its training labels are read from the
simulator's own record of which glass each pixel shows. Its votes are piled up
into a tally and the peaks of that tally are picked off one at a time, largest
first, and the pixels that voted near a peak are that peak's glass.

Running it as one of the six solutions on the shared
[test bench](../03_the-test-bench.md) is built too. The training set is drawn
from the bench's own arrangements, half of them crowded and all of them below
the bench's dividing line, and the solution is scored on held-out arrangements
above that line and writes its own `results.json` beside itself.

**What is a design.** Four things this document describes are written here and
not built: the two fixes for the rare class in the loss, the check on a pile's
fitted width, the second alarm on how far a pile's votes sit from their own
peak, and the whole of the second rung described below, which changes where the
labels come from. Where this document prescribes a check or a threshold, it
says so, and it quotes no measurement from anywhere.

## 2. What a network is, and what training from scratch means

Before the two heads can be described, three words need defining, because
everything after this uses them.

A **neural network** is a program whose behaviour comes from numbers fitted to
examples rather than from rules anybody wrote. Those numbers are called
**weights**. They start as random noise, and **training** shows the network an
example, compares what it produced against the answer wanted, and nudges every
weight in the direction that would have helped. Nobody writes the rule the
network ends up applying, and nobody can read that rule back out afterwards.

**Fine-tuning** means not starting from random numbers. You take a network
somebody else fitted to a large collection of labelled photographs, replace its
last layer with your own, and carry on training from there. This is the
standard advice almost everywhere, and the reason is that labelled real
pictures are scarce: somebody has to draw round every object in every picture,
so a borrowed network cuts the number of labels you need by a large factor.

**Training from scratch** is the other option: start from random numbers and
learn everything from your own examples. It is normally the worse choice, for
exactly the reason fine-tuning is the standard advice. It is the right choice
here, and the next section is why.

## 3. Why nothing is borrowed, and what that buys

The usual argument for fine-tuning rests on labels being scarce, so the first
thing to check is whether they are scarce here. They are not.

**Labels in this cell are free and exact.** The bench renders every picture
itself, so it also knows, for every pixel, which glass that pixel shows. Asking
for that record costs no more than asking for the picture. There is no
annotator, so there is no annotator's budget, no annotator's fatigue and no
annotator's mistakes. The scarcity that fine-tuning exists to solve is simply
not present, and training from scratch on an endless supply of exact labels is
a quite different proposition from training from scratch on a few hundred
hand-drawn ones.

**And borrowing brings a domain gap, which this solution is the only learned one
without.** A borrowed model's weights say what the world looked like in the
pictures it was fitted to, and those were photographs of real rooms with real
objects. This cell is a simulator with one table, one lens and four kinds of
glass that no photograph collection contains. Nobody can say in advance how
much of what such a model learned still applies here, and the honest way to
find out is to measure it. That is this solution's job in the comparison: it is
the line with no borrowed knowledge in it at all, so the distance between it
and the four borrowed ones is a measurement of what borrowing was worth.

There is a third, smaller reason, which decides nothing by itself but removes
the last practical argument for borrowing. Many ready-made models expect a
dedicated graphics card and this machine has none. A network small enough to
be written for this cell does not.

What all of that costs is set out in [what it needs](05_what-it-needs.md#1-what-it-needs), and the
short version is a training set, a training run and a file of weights to keep
in step with the cell. Those are real costs and rules on the table does
not pay any of them.

## 4. The shape of the network

With the choice of a random start settled, the shape of the network can be
described, and it is the standard shape for labelling every pixel of a picture.

The network has a **down path** and an **up path**, and the two are joined
across the middle.

The down path starts with the picture and applies **convolutions**. A
convolution takes a small square window, slides it over the picture, and at
each position multiplies the values inside the window by a fixed set of weights
and adds them up. One set of weights produces one output channel, and many
sets produce many channels, so a convolution turns a picture of a few channels
into a block of numbers of many channels. Between groups of convolutions the
block is **halved**, meaning it comes out half as wide and half as tall, while
the number of channels is doubled.

Two things happen on the way down and they pull against each other. Each
halving throws away exactly *where* something is, because one unit now stands
for a whole patch of the original picture. But each halving also means the next
window covers four times as much of the original picture as it did before. So
deeper units know less and less precisely where they are looking, and more and
more about what is around them. **That trade is the entire reason for going
down**, because an arrow towards the middle of a glass cannot be predicted by a
pixel that can only see itself. The pixel has to see enough of the glass around
it to tell which way the middle lies.

The up path reverses the halving, enlarging the block step by step until it is
back to the size of the picture it started from, and narrowing the channels as
it goes. A final convolution with a window of exactly one pixel, so no mixing
across space at all, collapses the channels to the handful of output values
this solution wants at each pixel.

The up path alone cannot work, and the reason is the first of the two things
that happened on the way down. The deepest layer knows there is a glass roughly
over *there*, but the halvings destroyed which exact pixel its rim sits on, and
enlarging the block again cannot invent a detail that was thrown away. So the
detail is not thrown away: before each halving a copy of the block is kept, and
on the way back up the copy is attached on as extra channels. The fine detail
comes across on the copy, the sense of context comes up from below, and the
convolution after the join mixes the two. Those copies are called **skip
connections**, and a network built this way is a **U-Net**, from Ronneberger,
Fischer and Brox, 2015 ([arXiv:1505.04597](https://arxiv.org/abs/1505.04597)).

### What goes in

The network is given the depth reading turned into something like a height
above the table, and two further channels that say where in the frame each
pixel sits. All three go in at half size, which is four times quicker to train
on and still leaves a glass many pixels across.

The last of those needs explaining, because it looks like a strange thing to
tell a network. A camera looking straight down throws a glass's outline
outwards from the point directly below the lens, and it throws it further the
taller the glass is. So the direction from a pixel to the middle of its own
glass depends on where in the frame that pixel is seen, which means a pixel
cannot answer the question from appearance alone. Telling the network where
each pixel sits hands it the one fact it cannot see.

### The warning worth checking before training

There is one piece of arithmetic worth doing **before** trusting this shape,
and it follows directly from the trade on the down path. How much of the
original picture one deep unit depends on is called its **receptive field**,
and it is easy to work out: each convolution extends the field a little at
whatever scale it is working at, and each halving doubles that scale, so the
field grows slowly at first and then in larger and larger jumps.

Turn the deepest layer's field into a distance on the table, using how much
table one pixel covers from the height the camera flies at, and compare it with
the smallest gap the cell guarantees between two glasses. **If that patch of
table is smaller than the gap, then the one layer with enough context to reason
about a neighbour cannot see two glasses at once**, and it is structurally
incapable of the comparison you might have hoped it was making. Adding one more
halving fixes it, at the price of several times as many weights in the deepest
block, because a convolution's weight count grows with the product of its two
channel counts.

Whether the extra depth is actually needed here is not known, and this document
is not going to pretend otherwise. Two things could rescue the shallower shape:
the up path's own convolutions widen the field further, and the evidence that
separates two joined outlines may be entirely local to the seam, in which case
no unit ever needs to see both glasses at once. It is flagged here because it
is far cheaper to check with arithmetic beforehand than to diagnose afterwards,
when all you have is a network that quietly never separates anything.

## 5. The first head: which pixels are glass

The shape is settled, so the two heads can be taken in turn, and the first is
the simpler. It has one output channel, it gives one number per pixel, and that
number is how sure the network is that the pixel is glass. A function that
squashes any number into the range zero to one turns it into a probability, and
a threshold on that probability is the mask.

Training needs a **loss**, which is one number saying how wrong an answer was
and which the nudging then tries to reduce. The ordinary loss for a yes-or-no
answer per pixel is **binary cross entropy**: for a pixel that really is glass
the penalty is smaller the higher the probability the network gave it, so being
sure and right costs almost nothing while being sure and wrong costs a great
deal, and for a table pixel it is the same with the probability flipped. Then
the penalty is averaged over every pixel in the picture.

**That average is where the trouble is**, and the trouble comes straight out of
this cell's geometry. Seen from the top, a glass covers a small patch of a large
picture, and there are only a handful of glasses, so the great majority of every
picture is bare table. Glass is the rare class by a wide margin. A network can
therefore lower the average a long way by learning exactly one thing, which is
to say "not glass" everywhere: the many table pixels then cost almost nothing
each, and the few glass pixels cost a great deal each but there are few of
them. The network has been rewarded for producing an empty picture, and this is
worst early in training, when saying nothing is the easiest improvement
available.

Two standard fixes exist, and **both are prescriptions here rather than
descriptions of what is built**.

The first is to **weight the rare class up**, multiplying every glass pixel's
contribution by the ratio of the two class sizes, so that the glass pixels and
the table pixels contribute equally to the total. Saying nothing is then no
longer an improvement at all.

The second is to **add a loss that measures overlap rather than counting
pixels**. The **Dice coefficient** is twice the number of pixels that both the
answer and the truth call glass, divided by the total number either of them
calls glass. It is one for a perfect match and zero when they share nothing,
and it has no term for the table at all. Using one minus Dice alongside the
weighted cross entropy is the usual recipe, from Milletari and colleagues, 2016
([arXiv:1606.04797](https://arxiv.org/abs/1606.04797)).

![Bare table outnumbers glass by a wide margin in every picture from the top, so a score that counts pixels is already high for a network that answers table everywhere, while a score that measures overlap gives that same network nothing.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-most-pixels-are-table.png)

The general lesson is worth more than the detail: **a score that rewards saying
nothing will be optimised by a network that says nothing.**

## 6. The second head: which way is the middle of my own glass

The first head stops exactly where the problem starts asking which glass is
which, so this is where the second head comes in. It keeps the network's shape
and its training recipe unchanged and adds two more output channels, holding
the two parts of an arrow. Nothing else about the network changes, which is why
the two heads are one network and not two.

### Why the arrow is an easier question than it looks

The arrow runs from a pixel to the middle of that pixel's own glass, so the
longest arrow that can ever occur is half the widest footprint the cell
handles. Every training target is therefore a pair of numbers inside a small
and known box, and **a target that is bounded is far easier to fit than an
unbounded one**. The network is never asked for a large number, so it never has
to learn how large numbers scale.

The second head also spends none of its capacity on the easy question, because
the loss is applied **over glass pixels only**. Most pixels in a picture from
the top are table, and a table pixel has no correct arrow at all, since there
is no glass for it to point at. So the arrow loss is multiplied by the mask
before it is added up, and the network is scored on the arrow only where the
question has an answer.

One more choice inside the loss matters. The arrow is scored by how far it is
from the true arrow, measured in a way that does not let a handful of wild
pixels dominate every update. Pixels right at the edge of a glass, where a
pixel may genuinely belong to either of two glasses, are exactly the wild ones,
and a loss that squares every error would let them drown out the many pixels
that are nearly right.

### Which frame the arrow is measured in

This is the one decision inside the second head that is worth going through
slowly, because the two reasonable answers give the network two different jobs.

**The arrow can be measured in the picture.** Then the target is a shift of so
many pixels across and so many down, and the network is predicting something
about the photograph. This is what the built network does, and it is why the
network is also told where in the frame each pixel sits: the same glass seen
near the middle of the frame and seen out at the edge needs a different arrow,
and the position channels are what let the network tell those two cases apart.

**Or the arrow can be measured on the table.** Every glass pixel has a depth
reading, and depth with the camera's own pose turns a pixel into a point in the
room, which drops onto a place on the table. So the arrow could be a distance
on the table instead, and then it would not depend on the camera at all: the
same glass would demand the same answer wherever the camera stood and wherever
in the frame it appeared. The price is that the arrow then needs the depth
reading at run time, so the solution would lose the one thing it gets for free
by working on the picture, which is an answer that does not depend on depth
coming back. That matters because real glassware returns almost no depth, and
it is the reason this choice is worth stating rather than assuming.

![An arrow measured in the picture is a different number for the same glass at every range, while an arrow measured on the table is the same number wherever the camera stood, which is the whole of the choice between the two frames.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-image-space-against-table-space.png)

Either way the votes are what comes next, and the rest of this document does
not depend on which frame was chosen.

## 7. From votes to glasses

Each glass pixel now has a vote, so the remaining question is how a cloud of
votes becomes a count of glasses. One glass's votes should land in one tight
pile, so the question is where the votes pile up.

**What is built counts them.** Every vote is added into a tally the size of the
picture, the tally is smoothed a little so that votes landing on neighbouring
places reinforce each other, and then the largest place in the tally is taken
as a middle, the votes around it are set aside, and the next largest place is
taken, until no place has enough votes left to be a glass. The pixels whose
votes landed near one middle are that middle's glass.

**The published method for the same job is mean shift**, and it is worth
knowing because it is what the general idea is called. Put a circular window
down on one vote, move the window to the average position of the votes inside
it, and repeat until it stops moving; each move is a step uphill towards
thicker votes, and the votes whose windows stop in the same place are one pile
(Comaniciu and Meer, 2002). Its important property is what it does **not** need
to be told: unlike methods that divide data into a fixed number of groups,
nothing has to say how many piles to expect. That matters here more than
usually, because in this problem the count *is* the answer.

![One glass's votes land in one thick patch and two glasses' votes in two, and the published method for finding those patches slides a window uphill to the average of the votes inside it until it stops, so the starts that stop together are one glass.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-vote-cloud-and-mean-shift.png)

Both forms have exactly one number to choose, which is how close two votes have
to be to count as the same pile, and it is pinned at both ends before anything
is run. The **floor** is the spread of one glass's own votes, because a window
much smaller than that scatter fits inside one pile and climbs some lump within
it, so one glass comes back as several peaks. The **ceiling** is the closest
two middles can ever be, which is two of the narrowest glasses of the kind
standing as close as the cell allows, because a window reaching much more than
half of that covers both middles at once and the two piles merge into one.
There is comfortable room between those two limits. It is worth seeing what a
careless choice costs, because the failure is quiet: a window large enough to
span the narrowest possible gap between middles swallows two middles whole, so
it merges exactly the pairs this solution exists to separate, and it does so
without complaining, because a merged pile looks perfectly tight.

Two checks go with the counting. The first is in the built code; the second is
a prescription.

**A pile needs enough votes.** A glass seen from the top covers many pixels, so
a pile built from a small fraction of the votes a whole glass should cast is
doubtful however tight it looks. This is the check that catches confident
agreement between witnesses who all stood in the same wrong place: a glass
reduced to a crescent down one edge votes only from that crescent, and those
votes agree closely with each other while being wrong together.

**A pile needs a believable width.** The pixels that voted into one pile are
fitted with a circle on the table, and a pile whose fitted width falls outside
the range this kind of glass can be is not reported as a glass, whatever the
votes say. So the network proposes and the arithmetic disposes, which is what
keeps this solution inside the same safety argument as rules on the table: a
learned part decides which pixels group together, and a rule nobody trained
decides whether the result is believable.

## 8. The two rungs: where the labels come from

Everything up to here is one method, and nothing in it says where the training
labels come from. That question has two answers, and the rest of the method
does not change between them. The network is the same network, the two heads
are the same two heads, the votes are the same votes and the checks are the
same checks. **Only the source of the labels changes**, which is why the two
are two rungs of one solution rather than two solutions.

The first rung takes its labels from the bench's answer key, which makes them
free and exact. The second rung takes its labels from the arm's own movement,
which makes them neither free nor exact, and buys something else instead. The
second rung is the point of this document, and the first is best read as the
thing it is a step up from.

## 9. Rung one — labels from the answer key

The bench renders every picture itself, so alongside the grey picture and the
depth reading it has an **id image**: at every pixel, which glass that pixel
shows, or nothing. The [test bench](../03_the-test-bench.md) describes it in full,
including the rule that a method may be trained on id images from the training
half of the arrangements and is never given one while answering. This rung is
built on that permission.

From an id image both heads' labels fall out by arithmetic.

**The first head's label is the id image with the identities forgotten.** A
pixel is glass if the id image names any glass there, and table otherwise.
There is nothing to judge and nothing to draw.

**The second head's label is a subtraction.** For a pixel the id image assigns
to one particular glass, the target arrow is that glass's middle minus the
pixel's own position. The bench knows where each glass stands because it put it
there, so both ends of the subtraction are known exactly, and the arrow is a
calculation rather than an opinion.

So the labels are free, in the sense that asking for them costs no more than
asking for the picture, and exact, in the sense that there is no judgement in
them anywhere to be wrong. That is a better position than almost any real
vision project is in, and it is the whole reason training from scratch is
sensible here. No annotator also means no limit on how many arrangements can be
labelled beyond the time it takes to render them.

The honest weakness of this rung is not in the labels. It is in what they
depend on. The id image comes from the simulator's own record of what it
rendered, and a real camera on a real table has no such record. So everything
this rung learns is learned from a source that exists only while the glasses
are simulated, and the day the cell meets real glasses, this rung has to be
labelled again by somebody drawing round things. The second rung is what
removes that dependency.

## 10. Rung two — labels from the arm's own movement

The second rung asks the same network the same two questions and fits it with
no answer key at all. Nothing in the simulator's record is read, not even
during training.

What replaces the answer key is a fact about this cell that is easy to pass
over. **The camera is on the wrist, so the arm knows exactly how it moved the
camera between two pictures.** That movement is not estimated from the
pictures. It is commanded, and then read back from the joint encoders. So for
two pictures of a scene that stood still while the camera moved, geometry says
where each surface point must have landed in the second picture, given how far
away it is. Points on one glass therefore move together, and points on a
different glass at a different distance move by a different amount. **That
agreement is the label.**

![The arm's own encoders say exactly how far it slid the camera between two pictures of a still scene, and every pixel of the near glass then shifts by one amount while every pixel of the far glass shifts by another, which is the agreement this rung uses in place of an answer key.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-two-views-parallax.png)

### Parallax: the shift goes as one divided by the depth

The effect the rung lives on is called **parallax**, and you have seen it from
a moving train, where the near fence races past the window while the far hills
barely move. When the camera slides sideways, a surface moves across the
picture by an amount equal to the slide divided by how far away the surface is.
Near things move a lot, far things move a little, and things infinitely far
away do not move at all.

Two consequences matter. The first is that the relationship is one divided by
the depth, so it is steep close up and nearly flat far away: the same
difference in depth is worth a great deal of separation near the camera and
almost nothing far from it. The second is that the separation between two
surfaces' shifts grows in step with the slide, so **a longer slide buys more
separation, in proportion**. That turns the arm into a dial it can set
deliberately, and it is the reason this rung can say in advance how far it must
move to settle a particular doubt.

![How far a surface moves between the two pictures goes as one divided by its depth, so the effect is steep close up and nearly flat far away, and the separation between two glasses' shifts grows in step with the slide, which is what turns the arm into a dial.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-depth-against-shift.png)

### Why the slide has to be sideways, and why the top view is the weak case

Parallax separates two surfaces by how far apart **in depth** they are, so it
separates two glasses only when the gap between them is much larger than the
range of depths each glass covers by itself. That condition is worth checking
against the two places this cell puts the camera, because it comes out
differently in each.

**From the top it is a weak signal, for two reasons.** Two glasses of one kind
have their rims at nearly the same height, so from a camera looking straight
down they are at nearly the same distance from the lens, and there is almost no
depth gap between the two objects to work with. Worse, each glass on its own
runs from its rim, well up towards the camera, down to the table far below it,
so each glass by itself covers a wide range of depths and both cover the same
wide range. Two ranges of shifts lying on top of each other cannot be told
apart however far the camera slides.

**From the side the geometry turns over.** A glass standing in line behind
another is much further back than either glass is wide, so the gap between the
two objects is now large while the range of depths each covers by itself is
only its own width, which is small. The two sets of shifts end up far apart,
which is exactly what parallax needs. And the arm already slides the camera
sideways at every survey station, because a station takes two pictures a short
distance apart; a slide taken deliberately for this purpose is the same kind of
movement, just longer and from the side.

![The loop this rung prescribes would not take another picture and hope: it would name the doubt in pixels, divide by how much separation one millimetre of slide is worth, move the arm exactly that far, and check each region that came back against the range this kind of glass can be.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-deliberate-motion-loop.png)

So this rung's labels come mostly from pictures taken from the side, which has
a plain consequence worth stating rather than hiding. **The labels for the
hardest case, which is the merge in a picture from the top, are the ones this
rung is worst at producing**, because that is exactly where parallax is weak.
The rung still trains the network that runs on pictures from the top, because
training and running are separate, and only the trained network is used at run
time, on exactly the input the bench hands every solution. But the supervision
it gets for the merge is weaker than the answer key's, and that is the price of
not reading the answer key.

### What an embedding is

The first rung could turn its labels into targets directly, because the answer
key says which glass a pixel belongs to and therefore where its arrow should
point. Movement gives something weaker: it says whether two pixels belong
together, and nothing about which glass they are or how many glasses there are.
So the network's output has to change shape to carry that weaker information,
and the shape it changes to is called an embedding.

An **embedding** is a short list of numbers the network produces at every
pixel, arranged so that **two lists being close together means the two pixels
belong together**. The numbers themselves mean nothing on their own. There is
no channel that says "glass number two" and no number that counts anything.
Only the distances between lists carry information.

A comparison helps here. Think of giving every pixel a position on a map, where
the map has no place names and no scale, and the only thing you may ask is how
far apart two pixels are. Pixels on one surface are put in one neighbourhood,
pixels on a different surface are put in a different neighbourhood, and
grouping the pixels afterwards is reading the neighbourhoods off the map. The
map is the embedding, and the network's job is to draw it.

### What contrastive training does

With that output shape in place, the labels from movement are exactly the right
kind of label for it.

Two pixels whose shifts between the two pictures agree to within the
measurement noise are a **positive pair**, meaning they are on the same
surface. Two pixels whose shifts differ by clearly more than the noise are a
**negative pair**, meaning they are not. Those two verdicts are all movement
gives, and they are all this training needs.

**Contrastive training** turns them into a loss. Pick a pixel, take its
positive partner and a handful of negative ones, and make the loss low only
when the partner's list is closer to the pixel's list than every one of the
negatives' lists is. Training therefore **pulls** a pixel and its positive
partner together on the map and **pushes** a pixel and its negatives apart. Do
that over many pixels and many pairs, and the map arranges itself so that the
pixels of one surface sit together and the pixels of different surfaces sit
apart, without anybody ever having said what a glass is.

![Every pixel becomes a short list of numbers, and training pulls a pixel and its positive partner together while pushing it away from its negatives, so the pixels of one surface end up in one neighbourhood without anything ever naming a glass.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-embedding-space.png)

What that gets right is worth naming, because no appearance-based rule can do
it. The line the embedding draws runs where the **depth jumps**, and not where
the brightness changes. So two glasses of the same kind, the same colour and
the same shape are no harder for this rung than two different ones, which is
the exact case that defeats a method relying on how things look.

What it does not get is equally worth naming. **Nothing in an embedding names a
glass and nothing counts them.** The map says which pixels belong together, and
something else has to decide how many neighbourhoods there are. So the lists
are grouped, each group becomes a candidate region, and every candidate region
goes through the same checks rung one's piles go through: enough pixels, a
circle fitted on the table, and a width inside the range this kind of glass
can be. The grouping step here is doing the job mean shift does for the votes,
and it has the same one number to choose and the same two limits pinning it.

That makes the check after the network less optional here than anywhere else in
this document, because a merged pair comes back from an embedding as one tidy
region with no complaint attached to it at all.

![Two glasses of one kind standing the same distance from the lens shift by the same amount however far the camera slides, so there is nothing for parallax to separate them by; and where there is, an embedding still says only which pixels are alike and never how many glasses there are.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-the-limit.png)

### What this rung buys and what it costs

It buys one thing, and the thing is about the future rather than about this
problem. **This is the only rung whose supervision a real arm also has.** A
real arm has joint encoders and a wrist camera, which is everything this rung
needs. Every other solution here that is fitted in this cell, including rung
one, is fitted to labels that exist only because the pictures were rendered, so
every one of them would have to be labelled again from nothing on the day the
code met real hardware. This one would not.

![A person drawing round every glass, the simulator's record of which glass each pixel shows, and the arm's own encoders are three ways to get the answer written beside a picture, and only the last of them is one a real arm would still have.](../../images/seeing-the-glasses/a-network-trained-from-scratch/07-where-the-labels-come-from.png)

It costs three things. The labels are **weaker**, as the section above says,
and weakest exactly where the problem is hardest. The labels are **not free**,
because collecting them means moving the arm, and an arm movement costs seconds
while a picture costs milliseconds and a pass of the network costs less than
that; so a training set gathered this way is paid for in arm time rather than
in render time. And the whole rung depends on there being something to match
between two pictures, so it is weakest where the pictures are plainest, which
is a surface of one even shade.

The honest conclusion is that rung one is the rung to build for this problem
and rung two is the rung to reach for when the cell leaves the simulator. This
cell has a working depth camera, which measures directly what parallax is being
trained to infer, so inside this problem rung two is doing hard work for
information the cell already has. It earns its place the day that stops being
true.

## 11. The training set

Both rungs need a set of arrangements to learn from, and two decisions about
that set decide whether the network works at all. They apply to each rung
equally.

**Spawn the hard case.** The cell's own rule keeps glasses a comfortable
distance apart, and a training set drawn only from that rule never once shows
the network a pair that a page of arithmetic could not already separate. So the
teaching has to happen on pairs standing far closer than the rule allows, which
is what the bench's crowded family of arrangements is for. But keep the easy
case too, in proportion, or the network quietly learns that there is always a
pair to find. As a general rule, **the edge of the specification should sit
somewhere in the middle of the training set**, so that the network has met
worse than it ever will in use.

**Randomise everything that is not shape.** A simulator will render the same
table under the same light for ever, and a network given a constant will use it
as a clue: if every training picture has the table at the same shade, the
network is free to learn that glass means the pixels that are not that shade.
That rule scores perfectly on the training pictures and on the held-out ones
too, because both came out of the same renderer, and then somebody changes a
light and the network fails for a reason that appears in no number.
**Domain randomisation** is the fix, and it is blunt: vary the lighting, the
table's colour and texture, the glass tint, the exposure, the picture noise,
the camera pose and the number and placement of the glasses, over a range wider
than anything expected, so that none of them is a reliable shortcut and shape
is the only thing left that predicts the answer (Tobin and colleagues, 2017,
[arXiv:1703.06907](https://arxiv.org/abs/1703.06907)).

![The same kind of arrangement rendered under different lighting, table colour and texture, glass tint, exposure, picture noise and camera pose, with the lens and the picture size held fixed on purpose, so that shape is the only thing left that predicts the answer.](../../images/seeing-the-glasses/a-network-trained-from-scratch/06-domain-randomisation.png)

One thing would **not** be varied, which is the camera's lens. The focal length
and the picture size are facts about the camera this cell has rather than
nuisances to be made robust against, and teaching the network to cope with
lenses it will never meet would spend its limited capacity on nothing.

And the split between learning and marking is the bench's, not this solution's.
The bench divides its arrangements into a training half and a test half, so a
network fitted on the first is marked on the second and is never tested on an
arrangement it learned from.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
