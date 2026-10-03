# Detection and segmentation

The page before this one, [vision backbones](01_vision-backbones.md), explained
the large shared part of a vision model, which reads a picture and turns it into
numbers, and it ended with the point that the same backbone can serve several
different jobs because each job only needs its own small head. This page is about
those jobs. It explains what each one gives back, how a guess is scored against
the truth, and why the job an arm needs is often not the one a beginner reaches
for.

The page answers six questions. What are the four different jobs that people run
together under the word recognition, and which one does an arm actually need?
What is a box as a set of numbers, and how do you measure whether a guessed box
is right? Why does a detector produce a heap of overlapping guesses, and what
thins them out? How do you measure a detector honestly? How do modern detectors
avoid the whole business of overlapping guesses? And what is a mask, as numbers,
including the kind of model that gives you one without being told what the thing
is.

It is written for a reader who has read [vision
backbones](01_vision-backbones.md), because the words backbone, head, feature
grid and stride are used here without being explained again. It also assumes you
know what a score between 0 and 1 means, from [the score of being
wrong](../03_how-training-works/01_the-score-of-being-wrong.md), and the idea of
training on labelled examples from [why not just write the
rules](../01_what-learning-means/01_why-not-just-write-the-rules.md).

Everything in the pictures is worked out by the script that draws them. The
camera scene is simulated, which means it is drawn out of rectangles and ellipses
rather than photographed, and the detector's guesses are simulated too, by
jittering the true boxes with a seeded random generator and giving each guess a
score that is higher when it covers the object better, which is how a trained
detector behaves. Every method run on those guesses is the real method. The
models you can download are catalogued in [object
detection](../../07_learned-models/03_seeing-models/02_most-used/01_object-detection.md)
and
[segmentation](../../07_learned-models/03_seeing-models/02_most-used/02_segmentation.md).

## Contents

1. [Four jobs that are easy to confuse](#1-four-jobs-that-are-easy-to-confuse)
2. [What a box is, and how a guess is scored](#2-what-a-box-is-and-how-a-guess-is-scored)
3. [Why a detector guesses many times](#3-why-a-detector-guesses-many-times)
4. [Measuring a detector honestly](#4-measuring-a-detector-honestly)
5. [Set prediction: slots matched one to one](#5-set-prediction-slots-matched-one-to-one)
6. [Masks, and models that take a prompt](#6-masks-and-models-that-take-a-prompt)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. Four jobs that are easy to confuse

The backbone from the last page gives back numbers that describe a picture, and
the first thing to settle is what you want those numbers turned into, because
there are four different jobs here and they are often run together under one
word. The simulated scene holds six objects of four kinds: three drinking glasses
standing close together, a mug, a box and a small bolt a long way back on the
table.

![The same table scene four times: with class scores, with a box round each object, with every pixel coloured by class, and with every pixel coloured by object](../../images/models-that-see/detection-and-segmentation/four-jobs.svg)

The same picture answered four ways: one name for the whole picture, six boxes, four class regions in which the three glasses share one colour, and six objects each with its own colour.

The first job names the picture, with no place and no count, so it cannot tell
you that there are three glasses. The second puts a **bounding box** round each
object, which is a rectangle lined up with the edges of the picture, together
with a class name and a score. The third labels every pixel with a class, marking
the glass pixels as glass and the table pixels as table. The fourth labels every
pixel with which individual object it belongs to, and that job is called
**instance segmentation**.

![The three glasses in one colour with a cross at the middle of the whole region, beside the same three in separate colours with separate middles](../../images/models-that-see/detection-and-segmentation/class-versus-instance.svg)

Labelling by class puts all 14,515 glass pixels into one region 140 pixels wide, whose middle at (217, 264) lands on no glass at all, while labelling by object gives three regions of 3,009, 5,753 and 5,753 pixels with three usable middles.

The difference between the third job and the fourth is the one that matters on a
robot arm, and the three glasses show why. The class region is 2.8 times the
width of one glass, so its middle falls in the gap between two of them, and an
arm sent to that point would close its fingers on air. Labelling by object
instead gives three regions with three middles, and each of those is a point the
arm can actually go to.

![A bar chart on a log scale of how many numbers each of the four jobs produces for one picture](../../images/models-that-see/detection-and-segmentation/output-sizes.svg)

For one 640 by 480 picture the four answers hold 4 numbers, 36 numbers, 307,200 numbers and 307,212 numbers, so the two pixel-labelling jobs give back about eight thousand times as much as the box job.

The four jobs also cost very different amounts to carry around. Naming the
picture gives four class scores and a box for each of the six objects gives 36
numbers, while labelling every pixel gives one number for each of the 640 times
480 pixels, which is 307,200 of them. That is roughly eight thousand times as
much data as the boxes, and it has to be produced and moved thirty times a second
if the camera runs at thirty pictures a second.

![The scene with the near glass shaded and markers for the point each job would give the arm](../../images/models-that-see/detection-and-segmentation/grasp-point-from-each-job.svg)

For the task of picking up the glass nearest the camera, naming the picture gives no point at all, the box middle and the object middle land 3 pixels apart and both on the glass, and the class middle lands 42 pixels away on no glass at all.

So the plain answer to which job a robot needs is this. If the arm has to say
whether anything is on the table, naming the picture is enough. If it has to
count things or point a camera at one, boxes are enough. If it has to move round
the table without touching it, labelling by class is enough, because the table is
one thing anyway. But if it has to pick one glass out of several it needs the
fourth job and not the third, because the third gives one region for all the
glasses and a point 42 pixels from the glass the arm meant to take.

---

## 2. What a box is, and how a guess is scored

Having settled which job to ask for, the next thing is to be precise about what a
box is and what it means for a guessed box to be right, because the whole of
training and of measurement rests on that one number.

![The mug with its box drawn, beside the same box written as corners, as a middle and a size, and as fractions](../../images/models-that-see/detection-and-segmentation/box-as-numbers.svg)

The box around the mug is the four numbers 370, 250, 472 and 348, which can equally be written as the middle (421, 299) with a width of 102 and a height of 98, or as the fractions 0.658, 0.623, 0.159 and 0.204 of the picture.

A box is four numbers and nothing else. They can be written as the left, top,
right and bottom edges, which for the mug are 370, 250, 472 and 348 counted in
pixels from the top left corner. They can equally be written as the middle of the
box and its size, and models usually learn this second form because the middle
and the size can be predicted separately. They are often divided by the width and
height of the picture to give fractions, so that the same numbers mean the same
thing at any picture size. Notice already that the box holds 9,996 pixels and the
mug itself only 8,177, so 82 in every hundred pixels inside this box are mug and
the rest are table.

![Two boxes over a glass with the overlapping rectangle shaded, beside the arithmetic that turns them into one number](../../images/models-that-see/detection-and-segmentation/iou-arithmetic.svg)

The overlap of the true box and the guess is 40 pixels wide and 117 tall, which is 4,680 pixels, their union is 6,600 plus 9,170 minus 4,680, which is 11,090, and dividing one by the other gives 0.422.

The measure that scores a guess is called **intersection over union**, usually
shortened to IoU, and it is exactly what the name says. The overlap runs from the
larger of the two left edges, max(150, 160) = 160, to the smaller of the two
right edges, min(200, 230) = 200, so it is 40 pixels wide, and the same working
from top to bottom gives 117, which makes the overlap 4,680 pixels. The union is
the two areas added together with the overlap taken off once, 6,600 plus 9,170
minus 4,680, or 11,090 pixels, and dividing one by the other gives 0.422. The
division is what makes the number useful, because it is 1 only when the boxes are
identical and falls towards 0 as they drift apart, whatever the size of the
object.

![Five panels of the same true box with a guess moved further each time, with the overlap falling from 1.00 to 0.10](../../images/models-that-see/detection-and-segmentation/iou-ladder.svg)

Moving the guess sideways by a tenth of the box's width drops the overlap to 0.761, by a quarter to 0.509, by nearly half to 0.291, and by three quarters to 0.096.

It is worth looking at what those numbers mean by eye, because people often set a
threshold without knowing what it allows. A guess moved by a tenth of the box
width scores 0.761 and looks almost right, one moved by a quarter scores 0.509
and is visibly off but still on the object, and one moved by three quarters
scores 0.096 and is pointing somewhere else. That is why 0.5 is the usual line
between a hit and a miss, and why a stricter 0.75 is used when the exact edges
matter.

![A bar chart of how many of the six objects count as found at each overlap threshold](../../images/models-that-see/detection-and-segmentation/iou-threshold-count.svg)

From the same 21 guesses, six objects count as found when the overlap needs only to reach 0.3, five when it must reach 0.5, three when it must reach 0.8 and one when it must reach 0.9.

The threshold is not a detail, because it changes the answer to "how many did it
find" without anything about the detector changing at all. So a sentence like "it
found almost everything" means nothing until you say which threshold it was
measured at, and this is the commonest way detector results are quoted
misleadingly.

---

## 3. Why a detector guesses many times

The last section scored one guess against one object. In practice a detector
hands you far more guesses than there are objects, and the reason is how it is
built rather than any mistake.

![The scene with a stride-32 grid and nine cell middles marked inside the mug, beside a zoomed view of the twenty-seven boxes they guess](../../images/models-that-see/detection-and-segmentation/why-many-guesses.svg)

The stride-32 grid has 20 by 15 = 300 cells, each asked the same question, so with three box shapes a cell the detector makes 900 guesses for one picture, and the nine cells whose middles fall inside the mug make 27 guesses about the mug alone.

A detector of the older and still very common kind asks the same question at
every cell of a feature grid: is there an object here, and if so where are its
edges? On the stride-32 grid of the last page a 640 by 480 picture has 300 cells,
and each cell is usually asked about several box shapes at once, so three shapes
a cell makes 900 guesses for one picture. Nine of those cells have their middles
inside the mug, and every one of them can see the mug perfectly well, so all nine
answer yes and the detector produces 27 guesses about one mug. Nothing has gone
wrong, because the cells were never told about each other.

![Six panels: all fifteen guesses, then four steps of keeping the best box and dropping those that overlap it, then the nine that survive](../../images/models-that-see/detection-and-segmentation/nms-steps.svg)

Starting from the 15 guesses that score 0.40 or more, the first step keeps the one scoring 0.91 and drops two that overlap it by 0.65 and 0.74, and after every step has run, 9 boxes are left.

The usual cure is a rule called **non-maximum suppression**, which means keeping
the box with the highest score and throwing away every lower-scoring box that
overlaps it by more than a set amount, then taking the best of what is left and
doing the same again until nothing is left to check. The pictures follow that on
the real guesses, showing only the 15 that score 0.40 or more so the boxes can be
told apart. The second step keeps 0.87 and drops one that overlaps by 0.66, the
third keeps 0.82 and drops one that overlaps by 0.60, and the fourth keeps 0.75
and drops one that overlaps by 0.70. Nine boxes are left standing, scoring 0.91,
0.87, 0.82, 0.75, 0.69, 0.67, 0.48, 0.43 and 0.42.

![A curve of the number of surviving boxes against the suppression threshold, with a line at the six real objects](../../images/models-that-see/detection-and-segmentation/nms-threshold.svg)

Suppressing at 0.1 leaves only 5 boxes, which is fewer than the 6 objects really there, while suppressing at 0.9 leaves 15, so one chosen number decides how many boxes come out.

The trouble is that the amount of overlap you allow is a number somebody has to
choose, and it is wrong in both directions. Suppressing at 0.1 leaves five boxes,
fewer than the six objects really there, because two objects standing close
together were taken for duplicates of each other, while suppressing at 0.9 leaves
fifteen, because almost nothing counted as a duplicate.

![The two glasses that stand together, then the result of suppressing at 0.3 where one is lost, then at 0.5 where both survive](../../images/models-that-see/detection-and-segmentation/nms-close-objects.svg)

The true boxes of the two glasses that stand together already overlap by 0.376, so suppressing at 0.3 leaves only one of them, while suppressing at 0.5 keeps both.

That failure is not rare, and the glasses in this scene show it exactly. Their
true boxes already overlap by 0.376 of their union, because one glass stands
partly in front of the other, so any threshold below 0.376 deletes a correct
answer and at 0.3 only the glass in front survives. There is no setting of this
one number that is right for both crowded shelves and spread out tables, and that
is the main reason the design in section 5 exists.

---

## 4. Measuring a detector honestly

Section 3 left us with nine or twenty-one boxes, depending on the threshold, and
no way of saying whether that was good. This section measures it properly, using
all 21 boxes that survive suppression with no score threshold applied, because
throwing away the low-scoring guesses before measuring is what makes a detector
look better than it is.

![A table of twelve guesses in score order with their overlap, whether each counts as right, and the running precision and recall](../../images/models-that-see/detection-and-segmentation/ranked-detections.svg)

Walking down the score order, the first five guesses are right and precision stays at 1.00 while recall climbs to 0.83, and then a guess scoring 0.67 with an overlap of 0.74 counts as wrong because that object has already been found.

The measurement starts by sorting every guess by its score and walking down the
list. A guess counts as right when it overlaps a real object by 0.5 or more and
that object has not already been claimed by a better-scoring guess. Two numbers
are kept as you walk: **precision**, the share of the guesses so far that were
right, and **recall**, the share of the real objects found so far. The sixth
guess is the interesting one, because it overlaps the glass on the right by 0.74,
which is a good box by any standard, and it still counts as wrong because a guess
scoring 0.69 already claimed that glass. That is how duplicates are punished.

![A step curve of precision against recall with the area underneath shaded](../../images/models-that-see/detection-and-segmentation/precision-recall.svg)

Precision stays at 1.00 until recall reaches 0.83 and then falls away to 0.24, and the area under the curve, which is the average precision, is 0.833.

Plotting precision against recall as you walk down the list gives the curve
above, and the area under it is called the **average precision**, which here is
0.833. The curve never reaches a recall of 1.0, and the reason is worth knowing:
the bolt is 18 pixels by 10 and no guess covers it well enough to count, which is
the small-object problem from the last page showing up as a number.

![Precision and recall plotted against the score threshold, one rising and one falling](../../images/models-that-see/detection-and-segmentation/threshold-tradeoff.svg)

Keeping only guesses that score 0.30 or more gives a precision of 0.38 with a recall of 0.83, keeping those at 0.50 or more gives 0.83 and 0.83, and keeping those at 0.70 or more gives a precision of 1.00 with a recall of 0.67.

Average precision describes the whole curve, but a robot has to pick one point on
it, because it either acts on a box or it does not. Keeping every guess that
scores 0.30 or more means most of what the arm is told about is not there, and
keeping only those at 0.70 or more means everything it is told about is real and
a third of the objects are missed. Which of those is right depends on whether a
wrong grasp or a missed object costs you more, and that is a question about the
robot and not about the model.

![A bar chart of average precision at five overlap thresholds, with their mean marked](../../images/models-that-see/detection-and-segmentation/ap-at-thresholds.svg)

The same detector scores an average precision of 0.833 when a guess must overlap by 0.5, 0.806 at 0.6 and 0.7, 0.500 at 0.8 and 0.167 at 0.9, and the mean of those five numbers is 0.622.

Because the whole measurement rests on the overlap threshold, published results
usually average the average precision over several thresholds, which is where the
figures quoted for real detectors come from. The numbers 0.833, 0.167 and 0.622
all describe the same detector on the same pictures, so when somebody quotes one
of them, the useful question is which one.

---

## 5. Set prediction: slots matched one to one

Everything in sections 3 and 4 was made harder by one thing, which is that the
detector answered many times for each object, so a clean-up step with a
hand-chosen threshold had to run afterwards. The newer design removes the cause
rather than the symptom.

![The scene with six boxes from six slots, beside a grid of all twenty slots showing which answered and which said nothing](../../images/models-that-see/detection-and-segmentation/query-slots.svg)

The model has 20 query slots, each giving back one box and one score for whether anything is there, and in this picture 6 of them name an object while 14 say nothing, so no clean-up step is needed.

A set-prediction detector has a fixed number of **query slots**, here 20, and
each slot gives back exactly one box, one class name and one score for whether
there is anything there at all. A slot is allowed to answer "nothing", and most
of them do, so the six that name an object are already the final answer, with
nothing to suppress and no overlap threshold to choose.

![Six candidate slots around three glasses, beside a table of the cost of pairing each slot with each glass, with the cheapest set ringed](../../images/models-that-see/detection-and-segmentation/matching-cost.svg)

The cost of pairing a slot with an object is one minus their overlap plus twice the distance between their middles divided by the picture diagonal of 800 pixels, and the cheapest set of three one-to-one pairings costs 0.975 against 1.081 for the next cheapest.

What makes the slots behave is how they are trained. For each training picture
the cost of pairing every slot with every real object is worked out, here as one
minus the overlap plus twice the distance between the middles divided by the
diagonal of the picture. Then the one-to-one set of pairings with the lowest
total cost is chosen, so each real object is given to exactly one slot and each
slot is given at most one object, and every slot that was not paired is trained
to answer "nothing".

![Two slots over the mug with their costs, beside a panel showing what the training asks of each](../../images/models-that-see/detection-and-segmentation/duplicate-pressure.svg)

Two slots both cover the mug well, at a cost of 0.071 and 0.173, so the matching gives the mug to the cheaper one and trains the other to answer "nothing", which is what teaches the model never to answer twice.

That one-to-one rule is the whole trick, and it is worth seeing on a single
object. Both of the slots over the mug would be perfectly good boxes, and nothing
about either of them is wrong, yet only the cheaper one is allowed to keep it,
and the other is told that the right answer there is "nothing". Over many
pictures this teaches the model that answering twice is always punished, so by
the end of training it does not do it.

![A bar chart comparing what the grid detector hands over before and after suppression with what set prediction hands over](../../images/models-that-see/detection-and-segmentation/before-and-after.svg)

The grid detector hands over 15 guesses above 0.40 and 9 after suppression, while the set-prediction model hands over 20 slots of which 6 answer, against the 6 objects really there.

What this buys you is that the output is the answer, so there is no threshold to
tune when the robot moves to a new table and nothing that deletes a real object
for standing too close to another. What it costs you is that the number of slots
is a hard limit, so a model with 20 slots can never report 21 objects, and that
these models take considerably longer to train, because early on the matching
keeps changing its mind about which slot owns which object. Named models of both
kinds are listed in [object
detection](../../07_learned-models/03_seeing-models/02_most-used/01_object-detection.md).

---

## 6. Masks, and models that take a prompt

Boxes have carried the last four sections, and section 1 showed that a box
contains a good deal that is not the object. This last section is about the
answer that does not: a **mask**, which is one number for every pixel saying
whether it belongs to the thing.

![The mug's mask shaded, beside an 8 by 8 window of the numbers the head gives and the same window after cutting at 0.5](../../images/models-that-see/detection-and-segmentation/mask-as-numbers.svg)

A mask head gives a number between 0 and 1 for every pixel, and cutting at 0.5 turns the window of numbers into zeros and ones, which for this mug gives 8,174 pixels against the true 8,177, an overlap of 0.978.

A mask is not a shape or an outline inside the computer. It is a grid of numbers
the same size as the region it describes, each between 0 and 1, saying how sure
the model is that this pixel is part of the object. Cutting at 0.5 turns them
into zeros and ones, and the window above shows that happening at the mug's left
edge, where each row climbs from near 0 on the table side to above 0.6 on the mug
side across eight pixels. The cut mask and the true one agree on 8,086 of the
8,265 pixels that either of them claims.

![A row of boxes showing the mask head, from the detector's box through four convolutions to the stretch back to the box](../../images/models-that-see/detection-and-segmentation/mask-head.svg)

The mask head is four 3 by 3 convolutions of 256 channels costing 2,360,320 parameters, one layer that doubles the grid costing 262,400, and a 1 by 1 convolution to a single number costing 257, which is 2,622,977 in all, run once for every box.

The usual way to get a mask is to put a small head on top of the detector. The
features inside each box are cut out and squashed to a fixed grid of 14 by 14, so
that the head always sees the same shape whatever size the object was. Four 3 by
3 convolutions of 256 channels run over that grid, a layer doubles the grid, and
a 1 by 1 convolution brings it down to a single number for each of the 28 by 28
places, which is 2,622,977 parameters in all. Those 784 numbers are then
stretched to the size of the box, which for the mug is 9,996 pixels. The head
runs once for every box the detector found, and that is why masks cost more than
boxes on a robot.

![The mug's mask drawn on grids of 7, 14 and 28 squares and stretched back, beside a curve of overlap against grid size](../../images/models-that-see/detection-and-segmentation/mask-resolution.svg)

Drawing the mask on a 7 by 7 grid and stretching it back overlaps the true outline by 0.915, a 14 by 14 grid by 0.937 and a 28 by 28 grid by 0.977, and at 14 by 14, 419 of the 540 pixels it gets wrong are in the thin handle.

That stretching is where the accuracy goes, and the numbers say how much. A mask
drawn on a 7 by 7 grid overlaps the true outline by 0.915 and a 56 by 56 grid by
0.989, which look like small losses until you ask where the wrong pixels are: at
14 by 14, 419 of the 540 wrong pixels lie in the thin handle of the mug. So a
coarse mask is fine for the body of a thing and poor at anything thin, which
matters a great deal when the thin part is the part the arm has to take hold
of.

![A point prompt on one glass returning that glass, the same point returning all three, and a box prompt returning the mug](../../images/models-that-see/detection-and-segmentation/prompt-to-mask.svg)

A point at (175, 266) can honestly mean the one glass, which is 5,753 pixels, or the group of glasses, which is 14,515, so a promptable model returns several masks with a confidence for each, and none of them carries a name.

The newest kind of segmentation model changes the question. Instead of being
trained on a list of classes and asked which pixels are mugs, a **promptable
segmentation** model is given a point or a box and asked which pixels belong to
the thing there, and the Segment Anything family works this way. A single point
is genuinely ambiguous, because it can mean the one glass or the group of them,
so the model returns more than one mask with a confidence for each and lets
whatever asked the question choose. None of these answers carries a class name,
because the model was never told what any of these things are called.

![The near glass's mask with the grasp line across its narrow way, beside the mug's box with the parts that are not mug shaded](../../images/models-that-see/detection-and-segmentation/mask-to-grasp.svg)

The mask of the near glass is 50 pixels across its narrow way, which is 72 millimetres at 0.80 metres from a camera 640 pixels wide, while the mug's box holds 1,819 pixels of table, or 18 in every hundred.

That is exactly why these models are used inside robot pipelines as a tool rather
than as a recogniser. Something else decides what to pick, usually a detector or
a vision-language model, and the promptable model is then handed that box or
point and asked only for the pixels, which it does well on objects nobody trained
it on. Those pixels are what the grasp is worked out from, because the narrow way
across the mask is how far the fingers have to open, and 72 millimetres is a
width a gripper can be told. A point chosen inside the box alone carries no such
promise, since 18 in every hundred of that box is table.

---

## 7. Where to read next

- [Open-vocabulary vision](03_open-vocabulary-vision.md) is the next page, and it
  removes the fixed list of class names from everything on this page, so that a
  detector can be asked for a thing nobody listed when it was trained.
- [Depth and 3D](04_depth-and-3d.md) then turns a mask on a screen into a place
  in the room, which is what the arm actually needs before it can move.
- [Vision-language
  models](../10_language-and-multimodal-models/03_vision-language-models.md)
  explains the kind of model that decides what to point a promptable segmenter
  at, by reading an instruction and a picture together.
- [Behaviour cloning and action
  chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md) shows
  what happens after the seeing, when a model turns what it saw into movement.
- [Object
  detection](../../07_learned-models/03_seeing-models/02_most-used/01_object-detection.md)
  is the catalogue page for real detectors, with what each one costs and where
  each one fails.
- [Segmentation](../../07_learned-models/03_seeing-models/02_most-used/02_segmentation.md)
  does the same for mask models, including the promptable ones and how they are
  used on an arm.

---

## 8. Using it in Python

The arithmetic in sections 2 and 3 is one line each in `torchvision`, and the
numbers below are the ones this page worked out by hand.

```python
import torch
from torchvision.ops import box_iou, nms
from torchvision.models.detection import maskrcnn_resnet50_fpn

truth = torch.tensor([[150., 203., 200., 335.]])   # section 2: the true box
guess = torch.tensor([[160., 218., 230., 349.]])   # section 2: the guess
print(box_iou(truth, guess))                       # tensor([[0.4220]])

boxes = torch.tensor([[522., 185., 614., 255.],    # section 3: three guesses
                      [513., 178., 603., 267.],    # about the same box on the table
                      [537., 185., 620., 251.]])
scores = torch.tensor([0.91, 0.77, 0.71])
print(nms(boxes, scores, iou_threshold=0.5))       # tensor([0]): only the best survives

model = maskrcnn_resnet50_fpn(weights=None).eval()  # boxes and masks together
with torch.no_grad():
    out = model([torch.zeros(3, 480, 640)])[0]      # one 640 by 480 picture
print(sorted(out.keys()))                           # ['boxes', 'labels', 'masks', 'scores']
print(out['boxes'].shape, out['masks'].shape)       # (N, 4) and (N, 1, 480, 640)
```

The library gives you the overlap arithmetic, the suppression rule and a whole
trained detector with a mask head on it, and the shapes it hands back are the
ones this page described. Note that `masks` comes back at the full picture size
even though the head drew on 28 by 28, so the stretching has already happened and
with it the loss measured in section 6.

What the library will not do is decide the two numbers that matter. The
suppression threshold in `nms` is the one from section 3, and setting it too low
deletes real objects that stand close together, as the two glasses showed. The
score threshold you apply to `out['scores']` is the operating point from section
4, and it moves precision and recall against each other with nothing to tell you
which way to go except what a mistake costs your robot.

What the library also will not tell you is whether you needed a mask at all.
Boxes are smaller, faster and enough for counting and for pointing a camera,
while a mask costs a head that runs once per box, and it earns that cost only
when something downstream uses the pixels, such as how wide to open the fingers,
or which of three glasses standing together the arm is about to take hold of.
