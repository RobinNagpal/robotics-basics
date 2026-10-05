# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [What a transformer segmenter does differently](#1-what-a-transformer-segmenter-does-differently)
2. [Why that matters for this problem](#2-why-that-matters-for-this-problem)
3. [One class](#3-one-class)
4. [Set prediction](#4-set-prediction)
5. [Fine-tuning this model here](#5-fine-tuning-this-model-here)
6. [The second rung — training against the whole silhouette](#6-the-second-rung--training-against-the-whole-silhouette)

## 1. What a transformer segmenter does differently

Everything above says what is wanted. This section says how this model's shape
differs from the older shape, because the difference is the reason the rest of
the document is possible.

**The older shape is propose, then refine.** A detector of that kind first looks
over the picture and proposes rectangles that might hold an object, with no
claim about what the object is. It then takes each proposed rectangle on its
own, decides what is inside it, tightens the rectangle round it, and paints a
mask of the object's pixels **inside that rectangle only**. The mask is produced
on a small grid covering the rectangle and then stretched to the rectangle's
size, so it physically cannot reach past the rectangle's edge. The list of
proposals has no fixed length: it starts long, it is cut down, and the cutting
down is a step of its own.

**This model's shape is a fixed set of slots.** It carries a fixed number of
**queries**. A query is not a rectangle and not a region; it is a small list of
numbers that the model carries along and updates as it reads the picture, and
its job is to ask one question over the whole picture: *is there an object here,
and which pixels are it?* The number of queries is decided before training and
never changes, and it is chosen to be comfortably larger than the number of
objects any picture is expected to hold.

The programming comparison is exact enough to be worth using. The older shape is
a list that grows: candidates are appended as they are found, and the list is
then pruned down to the answers. This shape is a **fixed-size array of optional
values**, declared once. Every slot is either filled in with one object or left
empty, the array is the same length for every picture, and nothing is appended
and nothing is removed. A picture with two glasses and a picture with six
glasses produce arrays of the same length, differing only in how many slots are
filled.

The masks follow from that. Each filled slot's query is turned into a short list
of numbers describing the object it found, and separately the model produces a
description of every pixel in the picture. The mask for that object is then
"which pixels of the whole picture match this query's description", computed
pixel by pixel across the whole frame. So a mask is a statement about the entire
picture from the start, and **there is no rectangle for a mask to escape**, for
the simple reason that the mask was never drawn inside one. The model does also
report a rectangle round each object, because a rectangle is a convenient thing
to have, but the rectangle is a result of the answer rather than a container the
answer was built in.

## 2. Why that matters for this problem

That difference matters here for two reasons, one immediate and one that this
solution's second rung depends on entirely.

The immediate reason is that two glasses whose outlines join are two different
slots from the beginning. The queries work over the whole picture at once, so
nothing ever considered the joined region as one thing, and nothing has to
notice a seam or decide where to cut it. Two masks come out, and they are
allowed to overlap, because each one says "these pixels are part of me" about a
different object rather than putting one label on each pixel.

The reason that matters more is about room to grow. A glass partly covered by
the glass in front of it has evidence in the picture only on one side, so the
smallest rectangle round the pixels the camera saw of it is smaller than the
glass really is. In the older shape, that rectangle is the frame the mask is
painted in, so a mask that should cover the whole glass is clipped at an edge
decided by the evidence. Here there is no such edge. A mask may claim any pixel
in the picture it likes, so asking the model for the whole shape of a glass is a
request the architecture can express rather than one it has to be forced into.
That request is [the second
rung](#6-the-second-rung--training-against-the-whole-silhouette), and it is the
reason this architecture was chosen for this place in the set.

## 3. One class

Before the training can be described, one small change to the model has to be
stated, because it is the same change [the same YOLO fine-tuned
here](../08_the-same-model-fine-tuned/01_what-it-is.md) makes and it is easy to overstate.

A borrowed detector arrives knowing a general category list: many kinds of
everyday object, each with its own name. Here that list is replaced by a single
entry, "glass". So each query's class answer is a choice between two things
only, "glass" and "nothing", and the model is no longer being asked what sort of
object it has found. It is being asked only whether it has found one and which
pixels it is.

Two things follow, and they pull in opposite directions. In this solution's
favour, the question is easier: there is no chance of calling a glass a vase,
and the general category list was a description of a world this cell does not
contain anyway. Against it, the class answer stops being useful information. A
model with a category list can be read as saying "I am sure this is a glass
rather than a bowl", while here a high score means only "I am sure something is
here", so the score cannot be read as agreement about the kind. That is no loss
in this problem, because the kind on the table is already known, but it would be
a loss in the harder job where several kinds of glass stand on the table at once
and naming the kind is the question.

One thing does not follow. Cutting the class list down does not make the model
smaller or the training shorter in any important way, because almost all of the
weights are in the part that reads the picture and that part does not know what
the class list is.

## 4. Set prediction

With the slots and the single class in place, the next question is how the
training gets one answer per glass instead of several, and this is where this
family of models differs most sharply from the older one.

**Set prediction** means that the model's whole output is treated as one set of
answers to be compared against the set of real objects, rather than as a pile of
candidates to be sorted out afterwards. At each training step, the model's
filled slots are matched to the real glasses in the picture **one to one**: each
real glass is assigned exactly one query, each query gets at most one real
glass, and the pairing chosen is the one that fits best overall. Every query
left over is told that the right answer for it was "nothing".

The consequence is the part worth remembering. A query that reports a glass that
another query has already been matched to is not rewarded for being nearly
right; it is told that its answer should have been "nothing". So the duplicate
answers are trained out of the model rather than removed from its output. The
model learns, over the whole training set, that the slots must divide the
objects between themselves, and a picture with four glasses comes back with four
filled slots because that is what the training rewarded.

Compare that with the older shape, where several proposals land on one object
because several reference rectangles at neighbouring positions all really do
contain most of it. All of them score highly, so the output holds a cluster of
overlapping claims about one object, and a separate arithmetic step has to
reduce the cluster to one answer: sort the claims by score, keep the best,
discard every claim overlapping it by more than a chosen amount, and repeat.
That step is called non-maximum suppression, and it has one setting and one
assumption. The setting is how much overlap counts as duplication. The
assumption is that heavy overlap **means** duplication — and in this cell that
assumption is awkward, because splay can push one glass's stretched outline
right across another's, so two genuinely different objects can overlap heavily
and one of them can be thrown away for looking like a duplicate of the other.

Set prediction removes both the setting and the assumption. There is no overlap
amount to choose, so there is one fewer number that somebody has to justify
against the geometry of this cell, and two heavily overlapping objects are not
in competition with each other, because each occupies its own slot. That is a
real advantage here and it should be stated as the design expectation it is, not
as something this book has measured.

The cost of set prediction is also real and worth naming. Matching the slots to
the objects one to one is a decision the training step has to make before it can
score anything, and which query ends up responsible for which glass can change
from one step to the next early in training. Models of this family are therefore
known to need patience in training, and the published work on them is largely
about making that matching settle faster.

## 5. Fine-tuning this model here

The architecture is settled, so this section is about where its numbers come
from, because that is the other half of the design and it decides whether the
model is reasonable to build at all.

**Training** a network means showing it an example, comparing what it produced
against the answer wanted, and nudging every weight in the direction that would
have helped. **Training from a random start** means every weight begins as
noise, so the nudges have to build the whole model from nothing, including the
parts that merely find edges. **Fine-tuning** means the weights begin somewhere
useful, so the nudges have far less to do. This model arrives fitted to a large
collection of ordinary labelled pictures, and almost all of its weights are in
the part that reads a picture rather than in the queries on top, so what is
borrowed is mostly a general-purpose answer to "what is in this part of this
picture".

Why that needs less data is best said in terms of what the data has to pay for.
Every weight is a number the training data has to determine, and a weight the
data cannot pin down ends up fitted to accidents of the particular examples
given, which is called **overfitting** and shows as a model scoring well on its
training pictures and badly on new ones. The amount of data needed therefore
grows with the number of weights determined from nothing, and fine-tuning
changes that sum: most of the weights already sit at values that work and only
have to be adjusted. This is why a few hundred pictures is a sensible training
set for a model of this size, and a few hundred pictures is what this cell can
produce without difficulty.

The labels are where this cell is unusually fortunate. In the ordinary case a
person draws every mask by hand, which is why labelled data is the scarce
resource in this field. Here nothing is drawn. The bench renders, beside every
picture, an image saying which glass owns each pixel, described in [the test
bench](../03_the-test-bench.md), so one glass's mask is the set of pixels carrying its
identity and the class is always "glass". Every label is a selection over an
array the bench produced anyway. The bench hands those labels out only for the
training half of its arrangements and marks on the other half, so no model is
ever tested on an arrangement it learned from.

There is one honest warning about the pictures themselves. The cell's renderer
produces no colour: it produces a depth reading for every pixel, and the picture
the model is given is that depth shaded into grey. The borrowed weights were
fitted to ordinary pictures, which have colour varying between their channels,
edges from paint and print and shadow as well as from geometry, and texture
inside every surface. A shaded depth picture has none of that and all of its
edges are geometric. The name for that difference is the **domain gap**, meaning
the gap between the world a model was fitted on and the world it is asked to run
in. Fine-tuning does not remove the gap, but it does the one thing that matters
most: the grey pictures are not an unfamiliar input the model must survive at
run time, they are the input it is fitted on. So the gap is expected to cost
accuracy and training effort rather than correctness. That is reasoning about
the design and not a result.

There is a second warning about the training set, and it is a rule this document
prescribes rather than something any code here does. The cell's own placement
rule keeps glasses a comfortable distance apart, so a training set drawn only
from that rule never shows the model a pair that was hard to separate. The
training arrangements therefore have to include pairs standing much closer than
the rule allows and pairs whose outlines overlap heavily after splay, while
keeping the ordinary case in proportion. The principle is worth remembering:
**the edge of the specification should sit somewhere in the middle of the
training set**, so that the model has met worse than it ever will.

## 6. The second rung — training against the whole silhouette

Everything above describes a model that marks the pixels the camera can see of
each glass. This section is the step up, and it belongs to this solution rather
than to any of the other five, because this is the architecture whose masks have
room to hold it.

The step is one sentence long: **train each mask against the glass's whole
silhouette — the shape it would have if nothing stood in front of it — instead
of against only the pixels the camera can see of it.** A mask of that sort is
called an **amodal** mask, and the word is worth unpacking once. A **mode** here
means a sense: seeing, hearing, touching. Something is **modally** present when
a sense delivers it, so the part of a glass whose own surface the camera sees is
modally present in the picture. Something is **amodally** present when the
perceiver has it although no sense delivered it, which is the part of a glass
hidden behind another object: you know it is there, you know roughly where its
edge runs, and no light from it reached the camera. So a **modal mask** covers
the pixels where the glass's own surface is what the camera saw, and an **amodal
mask** covers the pixels the glass would occupy if nothing stood in front of it.
The amodal mask always contains the modal one, and the difference between the
two is the **hidden part**.

![The same arrangement from the top, shown three ways: the modal mask of the covered glass holds only the pixels where its own surface was seen, the amodal mask holds its whole silhouette, and the difference between the two is the hidden part.](../../images/seeing-the-glasses/a-transformer-segmenter-fine-tuned/10-modal-against-amodal.png)

The everyday version shows that the amodal answer is the normal one. Look at a
cat sitting behind a garden railing. What reaches your eyes, strictly, is a set
of vertical strips of cat separated by bars, and what you report is **one cat**.
The alternative report, several slices of cat of various widths, is so strange
that it takes an effort to produce. A model marking only visible pixels is a
system that reports the slices, which is exactly what it was asked for and
exactly what the picture holds. It becomes a problem only when the next step
assumes a whole object.

One property of the two masks matters for the training. **On a glass with
nothing in front of it the modal and amodal masks are the same**, because there
is no hidden part to complete. So training against whole silhouettes costs
nothing on the easy pictures, and it leaves a free test available afterwards: on
a glass with a clear view, a model that adds anything at all is adding something
wrong.

### Why it helps

The reason this is worth doing is the quiet failure named in [the problem this
solves](01_what-it-is.md#2-the-problem-this-solves), and it is worth following through to the
place where the damage appears.

Put one glass partly behind another. The camera sees the near glass's surface
where the far glass would otherwise have been, so a mask marking only visible
pixels loses every pixel of the far glass behind that surface. What is left is a
slice of the glass, cut along one side, with every remaining pixel lying towards
the side the camera could still see.

Now hand that slice to the arithmetic every solution in this book shares. It
back-projects each mask pixel with its depth reading into a point in the room
and drops the height to get a point on the table, takes the axis from the points
at the top of the glass and the width from how far the cloud reaches out from
that axis. A whole footprint gives a disc, and the arithmetic reads it
correctly. A slice is narrower than the whole and it lies off to one side of the
true centre, so the arithmetic reads a glass that is both **smaller than the
truth and standing where no glass stands**.

That failure is dangerous because of what does *not* happen. The reported width
is still a width this kind of glass is allowed to have, because a kind whose
range runs from a small glass to a much larger one has room for a short
measurement: a slice does not look like an error, it looks like a shorter glass.
So nothing in the answer objects, and the arm is sent towards a place where
there is no glass. Compare it with the loud failure these checks were built for:
when two glasses come back as one region the width comes out wider than any
glass of this kind can be, the check fires, and the region is reported as
doubtful. **A loud failure is a result; a quiet one is a trap**, and in a cell
whose next step is an arm moving, the quiet one is far worse.

A mask covering the whole silhouette repairs the thing that caused it. The far
glass becomes a region of its own, with its outline where the glass's outline
really runs, so its visible slice is attributed to the glass it came off instead
of being swallowed into the region of the glass in front, and a slice too thin
to be worth reporting on its own is reported as part of something whole.

### Why this architecture suits it

This is where the shape of the model earns its place, and the argument is short
because the work was done in [what a transformer segmenter does
differently](#1-what-a-transformer-segmenter-does-differently).

A whole silhouette sticks out beyond the visible evidence. In the older shape,
the mask is painted inside a rectangle, and the rectangle is found from what the
picture shows, so the completion is clipped at an edge the evidence drew and the
model is being asked for something it has no room to express. Making that work
means training the rectangles to be amodal as well, which is asking the
proposing stage to propose a rectangle **larger than the evidence in the
picture**. Here there is nothing to fix, because the mask is computed over the
whole picture from the start. **With no rectangle to escape, a mask is free to
grow**, and asking for the whole silhouette changes only what the mask is scored
against during training.

That is worth stating as a general lesson, because it is one of the more useful
things to know about models of this sort. **One network answers a different
question by changing its target rather than its shape.** The body learns to
describe what is in the picture, and the question being asked lives in what the
final output is compared with. Here not even the last part of the model changes
shape, so the question lives entirely in the target.

The code change being small does not make the task change small, and it would be
dishonest to let that pass. Marking visible pixels traces a boundary that is
present in the picture, which is a question about where the evidence stops.
Marking a whole silhouette traces part of a boundary that is not in the picture,
which is a question about what a glass of this kind looks like and about which
of two objects at a boundary is in front. The second question needs the model to
have learned the shape of the kind, and it needs the near-and-far relation to
come out right, because completing the wrong one of the two objects produces a
mask spreading over a glass that is actually nearer the camera. So this rung may
need more training, or a larger size of the model, than the first rung does.
Whether it does is **not known here**, and this document does not assert it.

### The trap, and it is the one thing most easily got wrong

Now the part that matters a great deal, and it is the single thing this solution
would most easily get wrong. It deserves its own section because the mistake is
invisible: it makes the mask look better while making the answer much worse.

A mask covering the whole silhouette claims pixels where the camera saw some
other object's surface. The model is asserting that the glass continues
underneath what is in front of it, and an assertion is not an observation. The
damage comes from the depth reading. **The depth reading at such a pixel belongs
to whatever stood in front**, so it says how far away the near glass is and
nothing at all about the glass being reported. Feed it into the shared
arithmetic and the point it gives sits on the near glass, somewhere between the
camera and the glass being reported, and a patch of such points drags the
computed place across the gap and onto the object in front.

So the rule is absolute. **A mask that claims pixels the camera never saw the
glass at must say which pixels those are**, handing on the observed part and the
asserted part as two things rather than one silhouette with the join hidden. The
bench then **excludes those readings rather than guessing values for them**, and
that is the bench's own stated behaviour rather than something this solution has
to arrange. Nothing is inferred in their place either: what an asserted pixel
would be worth is a question about geometry, and a guess at it inside a
segmenter would be arithmetic nobody asked for.

Working out which pixels are asserted costs nothing, which removes the only
excuse for not doing it. The depth reading at a pixel already says whether the
surface there sits at this glass's distance or at the near object's, so the
split can be read off the answer itself without any reference to the truth.

The failure if the split is skipped would pass every check the project has. The
mask would look like a better mask, the footprint fitted to it would still be
round, and the width would still be inside the range the kind allows, so what
comes out would be a plausible wrong answer of exactly the kind this rung exists
to prevent, reached by the repair instead of by the failure the repair is for.
[The test bench](../03_the-test-bench.md) reports the measurement that settles it, taken
with exact masks and no model anywhere in the chain: naming the asserted pixels
and leaving them out places a glass markedly closer to where it stands than
feeding them in does. That measurement belongs to the bench's arithmetic rather
than to any model, so it applies here unchanged.

### What the completion actually buys

Put the rule together with the exclusion, and the value of the whole silhouette
turns out to sit where a reader does not first look for it. This is worth being
exact about, because it is the easiest thing in this rung to misdescribe.

The asserted pixels are left out, so they contribute nothing to the place and
nothing to the width. The measurement is the one the observed pixels alone would
have given, and the completion supplies no measurement at all, because it has no
reading to supply. **What it buys is attribution rather than measurement.** The
model reports one region per glass, drawn round the shape the glass really has,
so the hidden glass's visible part is credited to that glass instead of being
absorbed into the region of the glass in front. A glass that would otherwise
have been left out of the report altogether is reported as itself, in roughly
the right place, with a width that comes from the part that was seen and is
therefore under the truth.

Two consequences follow, and both are honest rather than flattering. The first
is that a width from such a report is a figure for planning and not for
gripping. This project's rule is that the last millimetres are felt rather than
driven: the fingers close until they touch and then check the width. A width
fitted to part of a glass is exactly what that rule keeps away from the gripper.
The second is that where the completion covers a glass the camera barely saw,
what arrives is an outline with too little seen inside it to place, and such an
outline should be handed on as doubtful rather than placed from nothing. A glass
reported as doubtful is a result in this project and not a failure.

One further number comes free once the two parts are kept apart, and this
document prescribes carrying it. Dividing the size of the observed part by the
size of the whole mask gives the **visible fraction**, which says how much of
that glass the camera actually saw. It costs one division, it comes from the
answer itself rather than from the model's opinion of itself, and it should
travel with every reported glass, because every consumer further down has its
own tolerance for how much of an answer was asserted and none of them can apply
that tolerance once the two parts have been merged.

### The risk of inventing glass, and what bounds it

A model trained to extend evidence has an obvious failure direction, and it is
the mirror image of the failure this rung is for: it can extend evidence that
needed no extending, or extend a scrap of evidence into a whole object that is
not there. Two facts about this cell make that concrete. A narrow strip of glass
pixels looks much the same whether it is the visible sliver of a mostly hidden
glass or simply the edge of something that ends there, and splay stretches every
outline in a picture from the top outwards, so an outline's far edge can look
cut off when the glass merely ends.

This failure is loud where the one it replaces is quiet, and two cheap checks
bound it. Both are in the code, and each of them can only refuse.

**The width must lie inside the range the kind allows, unless the picture ran
out before the glass did.** Inventing glass means reporting a glass where none
stands, and every report carries a width, so a width outside the range this kind
allows is reason enough to refuse the report and hand it on as doubtful — when
the mask it was measured from lies inside the frame. When the mask reaches the
edge of the frame it is not. At the cell's own survey height one picture does not
hold the glass zone, so a glass at the far side of a station's frame is cut in
half and the width read off the half is not the glass's width; refusing on it
refuses the view and not the mask. That was measured on masks nothing can
improve on: handed the bench's own exact masks, one station at a time over 20
held-out spawned arrangements, the kind's range of footprints refuses 66 of 297
glass sightings, and **every one of those 66 reaches the frame edge**. The three
overlapping stations are the answer to such a report instead.

Notice as well that this check is useless against a mask cut short by the glass
in front of it, where the shrunken width looks like a legal smaller glass, and
useful against an invention, where claiming a glass means claiming a footprint
and a claimed footprint either fits the kind or does not.

**The asserted part must lie where the camera could not see.** A model claiming
a glass continues behind the near glass is claiming something about a part of
the scene the camera could not see, which is allowed. A model claiming a glass
continues across a patch the camera had a clear view of, where the reading comes
back off a surface standing nowhere near this glass, is contradicting a direct
observation. So every pixel of a mask that no nearer report accounts for is
back-projected with its own depth reading, and one whose surface stands further
from the report's own middle than the widest footprint the kind allows is a
pixel the camera plainly saw something else at. Those are left out of the
arithmetic like the rest of the asserted part, and a report holding more than a
small share of them is refused — wrong on arithmetic alone, with no reference to
the model, the training set or the kind. That is the strongest of the two,
because it is geometry rather than judgement, and it is the reason a learned
completion can be let near the arm at all.

There is also a free test for the quiet version of invention, where a model
completes a little on every glass whether or not anything is in front of it, so
that every footprint comes out slightly too wide and displaced slightly outwards
and no single answer looks wrong. **On a glass with nothing in front of it, the
amodal mask must equal the modal one.** So keep only the unobstructed glasses in
the marking half of the arrangements and measure what the model adds to them:
the right answer is nothing, and any systematic addition is a bias worth knowing
about before the model is trusted.

### How to tell whether the completion works at all

The last thing this rung needs is a way to tell whether the model is doing what
it was asked, because the ordinary measure of a segmenter misleads here, and a
model of this kind can be built, trained and declared a success while completing
nothing.

The ordinary measure is **overlap**: the number of pixels both the predicted and
the true mask hold, divided by the number either of them holds. Measured against
the visible truth it punishes the model for working, because every pixel of a
correct completion lies outside that truth and is counted as a mistake, so the
better the completion the lower the score and the best score goes to a model
that has learned to ignore the amodal target entirely. The lesson generalises:
**a score that rewards doing nothing will be optimised by a model that does
nothing.** Measured against the whole silhouette it is better but still a poor
guide, because for most glasses the hidden part is a minority of the silhouette
and for a glass with a clear view it is nothing, so the number mostly reports
how well the visible boundary was traced, which is the first rung's job.

So the measure to watch during training is the **overlap over the hidden part
alone**, which the bench can supply exactly by subtracting one of its own masks
from the other. That number ignores every pixel the model could have got right
by tracing a visible edge. Beside it belong the counts of glasses found, missed
and merged, because what this rung changes shows up in those counts before it
shows up in any footprint: a completion that attributes a slice to the glass it
came off adds a glass to the answer rather than improving the footprint of a
glass that was already there.

![A stand-in prediction that completes most of the hidden part but stops short of its far edge scores well when the overlap is counted over the pixels the camera saw and much worse when it is counted over the hidden part alone, which is why the hidden part alone is the number to watch.](../../images/seeing-the-glasses/a-transformer-segmenter-fine-tuned/10-measuring-whether-it-works.png)

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
