# How the model is trained

This page explains the training step in detail: what goes into it, which
library does the work and why, and what each line of the training call asks
for. It follows [the code](02_the-code.md), which shows the fitting step in
three numbered steps, and it takes those steps one at a time. Every file it
names is in the solution's folder on GitHub.

## Contents

1. [What fine-tuning is](#1-what-fine-tuning-is)
2. [The inputs: scenes, pictures and label files](#2-the-inputs-scenes-pictures-and-label-files)
3. [The library: Ultralytics](#3-the-library-ultralytics)
4. [Loading the borrowed weights](#4-loading-the-borrowed-weights)
5. [The training call, argument by argument](#5-the-training-call-argument-by-argument)
6. [What the run did, and what it produced](#6-what-the-run-did-and-what-it-produced)
7. [Two ways training on one cell's pictures goes wrong](#7-two-ways-training-on-one-cells-pictures-goes-wrong)

## 1. What fine-tuning is

The code calls one method to do the training, so it is worth saying first what
that method does to the model.

**Training** a network means showing it an example, comparing what it produced
with the answer that was wanted, and nudging every weight a little in the
direction that would have helped. A weight is one of the numbers inside the
model. **Training from a random start** means the weights begin as noise, so the
nudges have to build every part of the model out of nothing. **Fine-tuning**
means the weights begin at values somebody else's training already settled, so
the nudges have much less to do.

The saving comes from the early layers of the model. They answer to things
common to all pictures, such as an edge or a corner. A grey picture shaded from
depth is full of edges, because the rim of a glass against the table is a large
jump in distance and therefore a large jump in grey. So those layers carry over
almost unchanged. The later layers hold the judgement about what an object is,
and that judgement was fitted to the colour and texture of photographs, which
this cell does not render. Those are the layers training has to change.
Yosinski and colleagues measured this
([arXiv:1411.1792](https://arxiv.org/abs/1411.1792)): how well a layer
transfers falls away with its depth in the network.

![The early layers of the borrowed model answer to edges and simple texture, which a grey picture shaded from depth holds as much of as a photograph, so they transfer almost untouched; the later layers carry the judgement fitted to colour and texture this cell does not render, and those are the ones training has to re-fit.](../../images/seeing-the-glasses/the-same-model-fine-tuned/09-what-a-backbone-brings.png)

Knowing what training changes, the next question is what it is shown, because
the library will not read the examiner's scenes as they are.

## 2. The inputs: scenes, pictures and label files

This section covers step 1 of the fitting step in [the code](02_the-code.md),
because the inputs have to exist on disk before any training can start.

**The scenes.** `dataset.scenes` in
[`dataset.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/dataset.py)
draws the arrangements to train on. Half of them are spaced, as the cell's own
placement rule spaces them, and half are crowded closer than that rule allows.
The crowded half is there so that the model meets pairs of glasses that are hard
to separate. A training set of spaced scenes alone would never show it one.
Every scene comes from below the examiner's dividing line, which separates the
arrangements a solution may learn from and the ones it is marked on. Two checks
refuse a scene from above that line: one in `data.training_seeds` and one in
`dataset.write`.

**The split.** `fit` holds every fourth scene back, so that the training run
can check its own progress on pictures it is not trained on. It takes every
fourth scene rather than the last quarter because the scenes arrive spaced first
and crowded afterwards. A check made on the last quarter would be a check on
crowded scenes only. These held-back scenes are not the examiner's held-out
arrangements; both parts come from below the dividing line.

**The pictures.** Each scene is seen from three survey stations, so each scene
gives three pictures. `dataset.write` saves each one as a PNG file. The picture
is the same grey shaded from depth that every solution is shown, 320 pixels
wide and 240 high, with the grey copied into all three colour channels.

**The label files.** Beside every picture, `dataset.write` saves a text file of
the same name with one line per glass. A line holds the class number, which is
always `0`, and then the corners of the glass's outline as pairs of numbers. Each
corner is written as a fraction of the picture's width and height, so a corner
in the middle of the picture is `0.5 0.5`. The first picture in the training set,
`crowded-00050-station-0`, has four lines, with 151, 106, 154 and 29 corners.
Its first line begins like this:

```
0 0.112500 0.491667 0.109375 0.495833 0.100000 0.495833 ...
```

The outlines come from the examiner's **id image**, which marks each pixel with
the glass it shows, or with nothing. The examiner never hands that image to a
solution at run time. It does hand it over as a training label, on scenes below
the dividing line only. `dataset.label` turns one glass's pixels into an
outline with three rules:

- It skips a glass the camera sees with fewer than 100 pixels at this station.
  That is the same count below which the shared arithmetic says there is too
  little of a glass to fit anything to.
- It keeps only the largest connected piece of a glass's pixels. When something
  stands in front of part of a glass, its visible pixels can come apart into
  patches, and each line of a label file is one object. Writing every patch
  would teach the model that one glass is several glasses in a row.
- It labels the pixels the camera saw, not the whole silhouette. A glass partly
  behind another is labelled with the slice that showed. Training towards the
  whole silhouette is [solution
  6](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md)'s choice.

A picture with no glass in it is still written, with an empty label file,
because the model has to be told that the answer there is nothing.

**These labels cost nothing here.** On real photographs somebody would draw
every outline by hand, and that is usually the most expensive part of the whole
exercise. This is a privilege of working in a simulator, and every judgement
about what fine-tuning costs in this chapter has to carry it.

**The description file.** Last, `dataset.describe` writes a small YAML file
that says where the two halves are and what the classes are called. YAML is a
plain-text format for settings. The run's file reads like this, with the full
path shortened:

```yaml
# Written by dataset.py. One class, which is the point of this solution.
path: .../04-yolo-fine-tuned/dataset
train: images/train
val: images/val
names:
  0: glass
```

The `names` list is where the one class comes from. The borrowed model knows 80
everyday categories, and this file names one. So the trained model is no longer
asked which everyday object it sees. It is asked only where the instances are,
and each one it returns is a glass or a mistake. That removes the failure that
sank [solution 3](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#2-why-it-failed-the-names-it-reached-for),
which called glasses sports balls and frisbees.

`dataset.build` empties the folder before writing it. Ultralytics keeps a cache
of the labels it read beside them, and a set written over an older one could
otherwise be trained from the older labels without any warning.

With the inputs on disk, the next section introduces the library that reads
them.

## 3. The library: Ultralytics

The previous section wrote the inputs in one particular shape, and this section
says whose shape that is and why this solution accepts it.

**What it is.** Ultralytics is a Python package that holds the YOLO family of
models together with the code to train them, run them and measure them. It runs
on PyTorch. On this machine PyTorch reaches the integrated graphics through MPS,
which is PyTorch's way of using the graphics processor on an Apple machine.

**What it does for you.** It owns the whole training loop. Given the YAML file
and a starting weights file, one call reads the pictures and labels, rebuilds
the model's last layers for the new list of classes, chooses an optimiser,
which is the rule that turns a measured error into a change of weights, varies
the pictures as it goes, checks itself after every pass, and keeps the best
weights. The training is therefore one line of this solution's code.

**Why this one rather than the obvious alternative.** The obvious alternative is
to write the training loop by hand in PyTorch, as [solution
2](../06_a-network-trained-from-scratch/01_what-it-is.md) does for its own small
network. That would mean writing the loss for boxes and masks, the matching of
predictions to labels and the measurement of the result again. The deciding
reason is the matched pair. Solution 3 uses this library and this weights file
untouched, and this solution has to differ from it in the training alone. Using
the same library's own training method keeps everything else the same.

**What it costs.** Three things.

- It reads a training set only from a folder in its own format, which is why
  `dataset.py` exists.
- Most of the training is decided by defaults the code never names, such as the
  optimiser and the ways the pictures are varied. The run keeps a record of
  every one of them, in `runs/fine-tune/args.yaml`, and [what the run
  did](#6-what-the-run-did-and-what-it-produced) reads the ones that matter from
  it.
- Its licence is the AGPL-3.0, and a weights file trained from its model carries
  that licence too. [The results page](04_results-and-comparison.md#4-what-it-costs)
  says what that means for this solution.

[The Ultralytics training guide](https://docs.ultralytics.com/modes/train/) lists
every setting, and [its page on segmentation
datasets](https://docs.ultralytics.com/datasets/segment/) describes the
label-file format. Both open in a new tab.

The library's first job is to load the starting weights, which the next section
describes.

## 4. Loading the borrowed weights

Step 2 of the fitting step begins by loading the model, and this section shows
where that file comes from.

```python
model = YOLO(str(borrowed()), task="segment")
```

`borrowed()` in
[`yolo_fine_tuned.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/yolo_fine_tuned.py)
returns the path of `yolo26n-seg.pt`, the smallest YOLO26 segmentation model.
It calls Ultralytics' `attempt_download_asset`, which fetches the file on the
first run and finds it on disk afterwards. The file is kept in the solution's
own `weights/` folder rather than the home directory, so that deleting that
folder starts everything again. Solution 3 names the same file, and the
solution's README records that a test checks the model is named in one place
only.

`YOLO(...)` builds a model object around those weights. `task="segment"` says
the model returns outlines as well as boxes. Nothing is trained yet: at this
point the object is exactly solution 3's model, with its 80 categories.

The next section is the line that turns it into this solution's model.

## 5. The training call, argument by argument

With the model loaded and the inputs on disk, the training is the one call
below, and this section reads it one argument at a time.

```python
model.train(
    data=str(described),
    epochs=epochs,
    imgsz=PICTURE,
    batch=BATCH,
    device=device.pick(),
    project=str(Path(__file__).parent / "runs"),
    name="fine-tune",
    exist_ok=True,
    workers=0,
    seed=FITTING_SEED,
    deterministic=True,
    plots=False,
    verbose=False,
)
```

The table below gives each argument in the first column, the value the run that
was marked used in the second, and what it asks for in the third.

| Argument | Value in the marked run | What it asks for |
|---|---|---|
| `data` | the YAML file from `dataset.build` | Where the pictures and labels are, and the one class. |
| `epochs` | 60 | How many passes over the 225 training pictures. `train.py --epochs` sets it; the default is 10. |
| `imgsz` | 320 | The size of square the picture is fitted into. The model works in multiples of 32, so the 320 × 240 picture is padded to 320 × 320. The same size is used when the model answers, because a model shown one size and asked about another is being asked about a different picture. |
| `batch` | 8 | How many pictures go through the model at once. Small, because the graphics processor shares its memory with the main processor. |
| `device` | `mps` | Where the work runs. `device.pick()` chooses the integrated graphics when PyTorch can reach them. |
| `project`, `name`, `exist_ok` | `runs/fine-tune` | Where the run writes its record and its weights, overwriting the last run there. |
| `workers` | 0 | Read the pictures in the main process. The set is small and already on disk, so a separate reading process per core costs more to start than it saves. |
| `seed`, `deterministic` | 0, true | Make the run come out the same every time it is given the same scenes, so a score claimed on it can be repeated. |
| `plots`, `verbose` | false | Do not draw charts or print every step. |

Two values appear nowhere in that call, and both matter. The first is the
number of classes. `train` reads the YAML, finds one class where the loaded
model has 80, and builds a fresh model with one class. It then copies into the
fresh model every borrowed weight whose shape still fits, which is every weight
outside the layer that scores the classes. That layer has one row per class.
Ultralytics would copy a row across if a borrowed category had the same name,
but none of the 80 is called "glass", so that row starts from nothing.

The second is the bar on confidence. Training does not use it. It is set later,
when the trained model answers, and it stays at solution 3's 0.25, with the
overlap allowed between two candidates at solution 3's 0.7. A bar moved here
would be a second difference between the pair, and its effect could be mistaken
for the effect of training.

When the call returns, `model.trainer.best` is the path of the best weights the
run kept, and step 3 copies that file to `weights/fine-tuned.pt`, which
[`run.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/run.py)
loads to be marked. `model.trainer.metrics` holds what the run measured on its
held-back pictures, and `fit` returns it beside the counts of what went in.

The call names few settings and leaves the rest to the library, so the next
section reads what the library chose and what came out.

## 6. What the run did, and what it produced

This section uses the run's own record, `runs/fine-tune/args.yaml`, together
with Ultralytics' source code, to say what happened inside the call above. The
run was started with `train.py --scenes 100 --epochs 60`.

**What went in.** 100 scenes, 50 spaced and 50 crowded. 75 of them were fitted
on, which is 225 pictures holding 1034 outlines. The other 25 scenes, 75
pictures, were held back for the run to check itself on.

**The optimiser it chose.** The setting was left at `auto`. Ultralytics then
counts the weight updates the run will make. It adds up the errors from eight
batches of eight pictures before it changes any weight, so each change rests on
64 pictures, and 225 pictures make about four changes per pass. Over 60 passes
the library counts that as 240 changes. Below 10,000 changes the library chooses AdamW, a common optimiser
that adjusts how far each weight moves, with a learning rate worked out from the
number of classes. For one class that rate is 0.002. The first few passes
raise the rate gradually from almost nothing, so that the new class row does
not pull the borrowed weights about while it is still random.

**How it varied the pictures.** Ultralytics changes every training picture a
little each time it shows it, so that the model cannot learn one picture by
heart. The run used the defaults: it flipped pictures left to right half the
time, moved and rescaled them, varied their brightness, and joined four pictures
into one mosaic. It stopped making mosaics for the last 10 passes, so that the
model ends on pictures shaped like the ones it will be asked about.

**How it chose the best weights.** After every pass the run measured itself on
the 75 held-back pictures. The measure is the **mean average precision**, or
mAP, which scores how well predicted outlines match the labelled ones. It kept
the weights from the pass with the best mAP for masks and boxes together, as
`best.pt`.

**What came out.** The run took 39 minutes. At the last pass its mAP for masks,
counting an outline as right when it overlaps the label by at least half, was
0.995 on its held-back pictures. That number is not this solution's score,
because those pictures come from below the dividing line. It only shows that the
fit settled. The marked score is on [the results
page](04_results-and-comparison.md).

**A short run is not enough.** The defaults in `train.py`, 16 scenes and 10
passes, finish in 52 seconds. The model they produce never scores a candidate
above 0.02, so at the bar of 0.25 it finds nothing at all. The class row starts
from nothing, and it needs real training before its confidence can clear the
bar.

Training this long on one cell's pictures has risks of its own, and the last
section names them.

## 7. Two ways training on one cell's pictures goes wrong

The run above trained hard on a narrow set of pictures, and that is exactly what
the two classic risks of fine-tuning come from.

**Catastrophic forgetting.** Continuing a model's training on a narrow set of
pictures moves its weights away from what they knew, so the model becomes better
at this cell and worse everywhere else. Within this project that costs nothing,
because the model is only ever shown this cell's pictures. It does mean the
weights file has to be kept in step with the cell. Change the camera, the way
depth is shaded into grey, or the proportions a kind of glass is drawn at, and
the file is out of date in a way no test of the code would notice.

**Overfitting.** A model fitted on a small set can learn the examples instead of
what they are examples of, here the arrangements instead of the glasses. Two
things guard against it. The examiner marks a solution only on arrangements it
was not trained on, so overfitting shows up as a lower score rather than hiding.
And the labels are free, so the training set can be made larger at the cost of
rendering time alone.

The two risks grow with the amount of training, while the domain gap shrinks
with it. So there is a sensible amount of training rather than a maximum, and
the held-out arrangements are what decide it. The next page gives what the
held-out arrangements said about this run, and sets the result beside the other
five solutions.

← [The code](02_the-code.md) · [Results and comparison](04_results-and-comparison.md) →
