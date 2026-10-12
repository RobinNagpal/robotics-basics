# Results and comparison

This page gives the results of this solution and the judgement on them. It
reports what the trained model scored in the two kinds of arrangement the
examiner uses, says which of solution 3's failures training removed and which it
left, places the solution beside the other five, and gives its bill. It follows
[how the model is trained](03_how-the-model-is-trained.md), and every number on
it was marked by [the examiner](../03_the-examiner/01_the-examiner.md).

## Contents

1. [The results in the two kinds of arrangement](#1-the-results-in-the-two-kinds-of-arrangement)
2. [What training closed, and what it left](#2-what-training-closed-and-what-it-left)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)
4. [What it costs](#4-what-it-costs)

## 1. The results in the two kinds of arrangement

The training page ended with a model that had settled on its own check
pictures, and this section gives the score that counts, on arrangements it never
saw. The examiner marks every solution on **spaced** arrangements, where the
glasses stand as far apart as the cell's own rule asks, and on **crowded** ones,
where they stand closer than that rule allows. Each kind is marked over five
blocks of 20 held-out arrangements.

**This solution reports 99.4 glasses in every 100 when they are spaced, and 72.0
when they are crowded.** The five spaced blocks run from 99.0 to 100.0, and the
five crowded blocks from 70.8 to 72.9, so the numbers are settled. On the spaced
arrangements it misses 3 glasses in 499 and splits one, which means it reports
one glass as two. Its places are 6.6 mm from the truth at the median on the
spaced arrangements and 0.6 mm on the crowded ones. Solution 3, the same model
untrained, reports 6.4 and 2.1.

In the picture below, each mark is one block of 20 arrangements. The spread of
one solution's marks is how much its score varies from block to block, and the
distance between the two groups is what training bought.

![Found per 100 for the borrowed model and for the same model fine-tuned, on spaced and on crowded arrangements, with each of the five blocks of 20 held-out arrangements drawn as its own mark: the block-to-block spread of either solution is small beside the distance between them.](../../images/seeing-the-glasses/the-same-model-fine-tuned/07-the-pair-block-by-block.png)

Read the crowded score against the examiner's own floor before calling it a
disappointment. The floor is the same arithmetic given the renderer's exact
masks, and on the crowded arrangements it reports 86.4 glasses per 100, because
the rest are covered so completely that no method reading pictures can find
them. So this solution is 14.4 per 100 short of what there was to find, not 28.
In each crowded block the width check also hands over between 25 and 47
candidates as having a width no glass of the kind could have. The scorecard does
not separate how many of the missing glasses were refused that way, how many
left too few pixels and how many were covered outright, so neither does this
page.

**The masks cover the whole glass and a little more.** At the median the masks
cover 99.6 to 99.7 per cent of a glass, for all four kinds. The two kinds with a
stem are not the worst of the four, although the single glass covered least
well in the whole run was a stemmed one, at 46.1 per cent. The rule written by
hand, [solution 1](../05_rules-on-the-table/01_what-it-is.md), loses the stem:
its masks cover 82.1 per cent of a stemmed glass and 89.1 per cent of a short
stemmed one. The cost is on the other side. At the median 4.6 per cent of this
solution's mask is not the glass, against 0.0 for the written rule.

![How much of a glass the masks covered, kind by kind, for a rule written by hand and for this fine-tuned model, over five blocks of spaced arrangements: the rule's coverage collapses on the two kinds with a stem and the model's does not move.](../../images/seeing-the-glasses/the-same-model-fine-tuned/08-training-holds-the-stem.png)

Those numbers show training repairing some of solution 3's trouble and not all
of it, and the next section separates the two.

## 2. What training closed, and what it left

The score above is solution 3's score with the training added, so this section
reads it against [why solution 3
failed](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#2-why-it-failed-the-names-it-reached-for).

**The domain gap closed.** The domain gap is the difference between the
pictures a model was fitted on and the pictures it is shown. Solution 3 was
fitted on photographs and shown grey pictures shaded from depth. This model was
trained on the grey pictures themselves, so the gap is gone by construction.

**The naming failure closed.** Solution 3 called most glasses a sports ball or a
frisbee, and its filter on names threw them away. With one class there is no
name to get wrong and no filter, so a found glass cannot be named out of the
answer. That one change accounts for most of the distance between 6.4 and 99.4.

**The approximate edge stayed.** A model of this kind builds each outline as a
short weighted sum of a few coarse pattern images, cuts it at a threshold and
enlarges it to the size of the picture. Training changes the weights in that
sum, but not the fact that the patterns are coarse. So the edge stays a little
generous, which is the 4.6 per cent margin above. The examiner reads a glass's
width from that edge, and the enlargement errs the same way each time, so the
error does not average away over many glasses.

**The partly hidden glass stayed.** The outline is **modal**, which means it
marks only the pixels the camera saw. When one glass stands partly behind
another, the mask of the one behind is a slice of it, and the examiner reports a
narrower glass, pulled towards the part that showed. Training cannot repair
this, because the labels have the same limit. If the slice's width still falls
inside the kind's range, nothing refuses it.

**The completely hidden glass stayed.** A glass covered completely leaves no
pixel in any picture, so no model can find it. Here the pair scores the same,
because training changes what a model does with pixels and there are none.
[Looking again at what was
hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md) is the shared
answer: work out where a glass could be standing unseen, and send the arm to
look.

**The confidence number is not a check on the mask.** It comes from the same
weights as the outline. It says how sure the model is that a glass is there, not
whether the outline round it is right, so a glass cut short by a neighbour can
still be scored highly.

So training fixed the finding and left the outline's limits where they were.
The next section asks how that result compares with the other ways of finding
glasses.

## 3. Where it sits among the other five

The previous section measured this solution against its own untrained partner,
and this section sets it beside the other four, using [the six
solutions](../04_the-six-solutions/01_how-the-six-compare.md) as the frame.
[The results](../11_the-results.md) sets all six rows side by side.

**Against solution 3, nothing differs but the training.** Solution 3's page
already explains [why the pair is a clean
measurement](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#5-where-it-sits-among-the-other-five).
The result is that **6.4 glasses per 100 against 99.4 is what fine-tuning
bought** on spaced arrangements.

**Against [solution 1](../05_rules-on-the-table/01_what-it-is.md), the rule
written by hand is better in almost every way except separating glasses that
touch.** On spaced arrangements it finds 100.0 per 100 against this solution's
99.4. On crowded arrangements it finds 73.0 against 72.0, but it merges 10.7
reports per 100 to get there, where this solution merges 0.8. So the rule
reaches its count by calling two glasses one. The rule also needs no training
set, no weights file and no licence, and it can explain its own failures. This
model cannot: when it is wrong, you can look at the picture and guess why.

**Against [solution 2](../06_a-network-trained-from-scratch/01_what-it-is.md),
the comparison is borrowing against building.** Solution 2 fits a small network
from random numbers, so the project owns every number in it. This solution
borrows the general machinery of vision and adjusts it, which costs less
training, and the price is a downloaded file the project cannot reproduce and
the licence that comes with it.

**Against [solution 5](../09_a-foundation-model-with-a-keeper/01_what-it-is.md),
the comparison is how much to fit.** Solution 5 borrows a larger model untouched
and fits only a small keeper that decides which of its outlines are glasses. Its
borrowed weights never see this cell's pictures, so its domain gap stays open.
This solution fits the whole model.

**Against [solution
6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md), the comparison is
architecture.** Both are fine-tuned on this cell's pictures with one class and
free labels, so the training is held still and the model is what differs.
Solution 6 also trains towards the whole silhouette, which is the repair for the
partly hidden glass that this solution cannot make.

Every one of those comparisons weighs accuracy against what a solution costs,
and the last section gives this one's bill.

## 4. What it costs

The comparison above keeps returning to cost, so this section lists it.

**At run time, very little.** One picture takes 0.089 seconds with the model
already loaded, which is a small fraction of the time one movement of the arm
takes.

**To build, a training run.** The marked run took 39 minutes on this machine's
integrated graphics, with 225 pictures labelled for nothing by the examiner.
[How the model is trained](03_how-the-model-is-trained.md#6-what-the-run-did-and-what-it-produced)
gives the details, including why a short run produces a model that finds
nothing.

**To keep, a weights file in step with the cell.** The file has to be trained
again whenever the camera, the shading of depth into grey or the proportions of
the glasses change, and no test of the code would notice that it was out of
date.

**The licence, twice over.** Ultralytics YOLO26-seg is AGPL-3.0, and solution
3's page explains [what that licence
asks](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#6-what-it-costs-to-run-and-the-licence).
This solution carries one more condition than solution 3. It produces a new
weights file by continuing the training of the borrowed one, and a file derived
from an AGPL work is bound by the same terms. So the trained file is not an asset
the project owns outright, and training it here does not change its licence.
For these six solutions that costs nothing, because nothing is shipped or
served. If this method were carried into a product, solution 6 shows the way
out: it fine-tunes a segmenter licensed under Apache 2.0, and nothing in this
solution's design depends on the model being this one.

The next chapter is solution 5, which takes the opposite choice on how much to
fit: it leaves a large borrowed model untouched and trains only a small keeper
beside it.

← [How the model is trained](03_how-the-model-is-trained.md) · [SAM 2 with a keeper — what it is](../09_a-foundation-model-with-a-keeper/01_what-it-is.md) →
