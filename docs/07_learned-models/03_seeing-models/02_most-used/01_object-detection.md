# Object detection

This page explains object detection, which means models that find each object in a
picture, draw a box around it and then name it. It answers five questions: what a
detector does, what goes in and what comes out, how it works inside, how it is
trained, and how a robot arm uses its boxes to pick something up.

It is written for a reader who has already read the page on [image
classification](../03_also-used/01_image-classification.md), because that page
explains pixels, scores, layers, the backbone and fine-tuning, and this page
uses those words without explaining them again.

Object detection is the most used seeing model on robot arms, and it is often the
first model a robot project tries, because good detectors are free to download and
fast enough for a live camera.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
   · [5.1 Ultralytics YOLO26](#51-ultralytics-yolo26)
   · [5.2 RT-DETR](#52-rt-detr)
   · [5.3 RF-DETR](#53-rf-detr)
   · [5.4 D-FINE](#54-d-fine)
   · [5.5 Faster R-CNN](#55-faster-r-cnn)
   · [5.6 DETR](#56-detr)
   · [5.7 How to choose](#57-how-to-choose)
6. [Where to read next](#6-where-to-read-next)

---

## 1. What it is

An **object detector** is a model that finds every object it knows in a picture,
and for each one it gives a box around the object, the object's class and a score.

The box is called a **bounding box**, because it is the smallest upright
rectangle that holds the whole object. The class is a name from a fixed list,
just as it is for a classifier. Then the score says how sure the model is, on a
scale from 0 to 1. On a detector that score is usually called the
**confidence**.

Here is an everyday example: think of a person counting cars in a car park from a
photo, who looks over the photo, points at each car in turn, and says "car, car,
van, car". A detector does the same thing, because it points at each object with a
box and then gives each box a name.

The difference from a classifier is that a classifier gives one name for the whole
picture, while a detector gives one answer per object and says where each object
is. So a detector can tell the robot that there are three cups, and also which one
of them is nearest.

---

## 2. What goes in and what comes out

Now that you know what question a detector answers, here is the exact form of its
input and its output. The input is one camera picture, which on a robot arm is
usually a picture of the table or bin in front of the arm, taken from a camera on a
stand or on the arm's wrist.

The output is a list, in which each item describes one object with four numbers, a
name and a confidence:

- four numbers for the box, in pixels, which are usually the left and top edges
  together with the right and bottom edges. Some models give the middle of the box,
  its width and its height instead.
- the class, such as "mug" or "bottle".
- the confidence, such as 0.94.

The picture below shows the answer a detector gives for a photo of two mugs and a
bottle.

![A box, a name and a confidence for each object on the table](../../../images/seeing-models/object-detection/boxes-on-a-table.svg)

Each box has a tag with the class and the confidence, and those confidence numbers
are examples rather than real output.

The list can be empty, which means the model found nothing it knows, and it can
also hold objects the model is not at all sure about. So every program that uses
a detector sets a **confidence threshold**, and throws away every box whose
confidence is lower than that number. A threshold of 0.25 to 0.5 is a common
start. Book 2 discusses this choice in [confidence, and the
threshold](../../../02_perception/01_camera/02_finding-objects.md#53-confidence-and-the-threshold).

---

## 3. How it works inside

That list of boxes has to come from somewhere, and a detector begins the work just
as a classifier does. So a backbone turns the picture into grids of numbers that
describe edges, parts and objects, and then a detection **head** turns those grids
into boxes. There are three main ways to build that head, and this section takes
them in turn. The shortlist in [section 5](#5-well-known-models) holds models of
all three ways, and each way below names the ones that belong to it.

### Two stages: first guess the places, then check each one

The oldest way of building the head splits the work into two separate steps.

1. The first step looks over the backbone's grids and suggests a few hundred places
   that might hold an object, where each suggestion is a rough box. These
   suggestions are called **region proposals**.
2. The second step then looks at each proposal on its own, and gives that proposal
   a class and a confidence, as a classifier would. It also moves the edges of the
   box a little, so that the box fits the object better.

This way is accurate, but it is slower, because the second step runs once for each
proposal. The best-known model of this kind is Faster R-CNN, and
[section 5.5](#55-faster-r-cnn) recommends it for fine-tuning in plain PyTorch.
Faster R-CNN is also the only two-stage model in that shortlist, because the two
ways below are both faster.

### One stage: look once, answer for every cell

A faster way does all of that in one step. So the name of the best-known model of
this kind says it directly: YOLO, short for "you only look once".

1. The picture is split into a grid of cells. A real model uses several grids at
   once, with small cells for small objects and large cells for large ones.
2. For each cell, the head asks: is the middle of an object inside this cell?
3. If the answer is yes, that cell gives the object's box, its class and a
   confidence.

The picture below shows the idea with one coarse grid.

![The cell that holds the middle of an object reports its box](../../../images/seeing-models/object-detection/grid-of-cells.svg)

The white dot marks the middle of each object, and the yellow cell around each dot
is the cell that reports that object. Its box can be larger than the cell itself,
because the backbone's numbers for each cell already carry information about the
area around it.

The whole picture goes through the network only once, which is why one-stage
detectors are fast enough to run on every frame of a live camera. The one-stage model
in the shortlist is Ultralytics YOLO26, the current release of that same YOLO family,
and [section 5.1](#51-ultralytics-yolo26) recommends it.

### Cleaning up the extra boxes

Both of the ways described so far share one side effect, because a one-stage or
two-stage detector usually gives several boxes for the same object. Nearby cells,
or nearby proposals, all see the same mug, and each one of them reports it
separately.

So the detector runs a cleanup step after the network, and that step is called
**non-maximum suppression**, or NMS, which works like this.

1. Sort all the boxes of one class by confidence, highest first.
2. Keep the box with the highest confidence.
3. Remove every other box that overlaps the kept box by more than a set amount.
4. Repeat with the next highest box that is still left.

The overlap is measured as the area the two boxes share, divided by the area they
cover together, and this number is called **intersection over union (IoU)**. It is
1 when the two boxes are the same and 0 when they do not touch at all, so a common
setting removes boxes with an IoU above 0.5 or so.

The picture below shows five boxes for one mug, and the one box that is left after
the cleanup.

![Five overlapping boxes for one mug become one box after the cleanup step](../../../images/seeing-models/object-detection/many-guesses-one-box.svg)

The cleanup has one weakness, because two real objects that stand very close
together have boxes that overlap a lot, so the cleanup may then remove one of those
boxes by mistake.

### Transformers: a fixed set of answers

A newer way avoids that cleanup step altogether by using a transformer, the kind
of network that the [classification
page](../03_also-used/01_image-classification.md#3-how-it-works-inside)
mentioned. The first model of this kind was DETR, short for "detection
transformer", and it is the clearest one to explain the idea with. The shortlist
keeps DETR in [section 5.6](#56-detr) for that reason rather than for use on a
robot.

1. The model starts with a fixed number of empty answer slots, for example 100.
   These slots are called **queries**.
2. Each query looks at all of the backbone's grids through the attention step, and
   gathers from them whatever it needs to describe one object.
3. Each query then gives one box and one class, and a query that found nothing can
   give the class "no object" instead.

During training, each real object is matched to exactly one query, so the model
learns to give one box per object and needs no cleanup step at all. This is also
simpler for the program after the network, and it avoids the weakness with close
objects described above.

Three of the models the shortlist recommends for real work are built this way, each
changing a different part of DETR's design: RT-DETR in
[section 5.2](#52-rt-detr), RF-DETR in [section 5.3](#53-rf-detr) and D-FINE in
[section 5.4](#54-d-fine).

---

## 4. How it is trained

Whichever of those three heads a detector uses, it learns in the same way, from
pictures where a person has drawn a box around every object and written its class.
This work is called **labelling**, or **annotation**, and drawing boxes is quick
compared with tracing outlines, but it is still slower than writing one name per
picture.

The most used collection is **COCO**, short for "Common Objects in Context", which
has about 120,000 labelled photos for training, with 80 classes. Those classes
include "cup", "bottle", "bowl", "scissors" and "person", and most detectors you
can download were trained on COCO.

Training a detector works in the same way as training a classifier. The network
makes its guesses for a batch of pictures. Then a program compares each guess
with the drawn boxes and measures three kinds of error: the box is in the wrong
place, the class is wrong, or an object was missed. It then nudges the network's
numbers to reduce those errors, and repeats.

A robot project almost always fine-tunes rather than training from nothing. So
it starts from a detector trained on COCO and trains it further on its own
pictures with its own classes. A few hundred labelled pictures is a common
starting point, and Book 2 walks through a complete example with 80 pictures in
[training a model of your
own](../../../02_perception/01_camera/02_finding-objects.md#6-training-a-model-of-your-own).

Some projects make their training pictures in a simulator instead. This is
because the simulator draws the objects itself and already knows exactly where
every box is, so nobody has to label anything by hand. The page [where the data
comes from](../../01_what-models-are/05_where-the-data-comes-from.md) explains
this.

---

## 5. Well-known models

This section is the shortlist a real project chooses from. For each model it says
what the model is, why you would pick it rather than the obvious alternative, what
it costs you, and what to type to run it.

Read the table as a shortlist and not as a ranking. The left column names the model
and says how current it is. The right column holds everything else about it: the job
it is best at, its size, its licence, and when to pick it. A size is given as the
number of parameters, which is the count of numbers the network learned during
training, written in millions. Every number was read from the project's own
published table or model card, and each sub-section names which. Two projects
measure on different machines, so treat the sizes as a rough guide to scale.

| Model | What decides it |
| --- | --- |
| **Ultralytics YOLO26**, most used in 2026 | It is a one-stage detector, and its five sizes hold 2.4 to 55.7 million parameters under AGPL-3.0 or under a paid Enterprise licence. It is best at getting a working detector running in an afternoon. Pick it when you can publish your own source code, or when you pay for the other licence. |
| **RT-DETR**, most used in 2026 | It is a transformer detector, and its ResNet-50 checkpoint holds 43.0 million parameters, with Apache-2.0 on both the code and the weights. It is the most familiar permissive transformer detector, because it sits inside a library you may already use. Pick it when you want no licence restriction, and no cleanup step after the network. |
| **RF-DETR**, worth betting on | It is a transformer detector, and its sizes hold 30.5 to 33.9 million parameters for Nano to Large, and 126.4 and 126.9 million for XL and 2XL. Nano to Large are Apache-2.0, while XL and 2XL are PML 1.0. It gives the best boxes available at a given speed under a permissive licence. Pick it when the licence must stay permissive and the boxes must be good. |
| **D-FINE**, worth betting on | It is a transformer detector, and its largest checkpoint holds 62.9 million parameters under Apache-2.0. It is best at placing the edges of the box precisely. Pick it when you fine-tune on your own objects and you measure from the box. |
| **Faster R-CNN**, historical | It is a two-stage detector, and `fasterrcnn_resnet50_fpn_v2` holds 43.7 million parameters under BSD-3-Clause. It is best at fine-tuning in plain PyTorch with no new dependency. Pick it when you already use torchvision, and you do not need 30 frames a second. |
| **DETR**, historical | It is the first transformer detector, and its ResNet-50 checkpoint holds 41.6 million parameters, with Apache-2.0 on both the code and the weights. It is best at explaining how a query-based detector works. Pick it when you are learning the design rather than shipping a robot. |

### 5.1 Ultralytics YOLO26

**Most used in 2026**, because a developer who has never trained a model can
install one package and have boxes on their own photo within minutes.

Ultralytics is the company that publishes the YOLO family as a Python package, and
YOLO26 is its current release. Its
[documentation page](https://docs.ultralytics.com/models/yolo26/) describes it as
released in January 2026 and cites the paper "Ultralytics YOLO26: Unified Real-Time
End-to-End Vision Models" ([arXiv:2606.03748](https://arxiv.org/abs/2606.03748)).
The letter in the file name is the size, so `yolo26n.pt` is the smallest of the five
and `yolo26x.pt` is the largest.

The obvious alternative is RT-DETR in section 5.2, which has a permissive licence.
Pick Ultralytics when you are short of time, because it downloads its own weights,
it trains on your own pictures with a single call, and almost every tutorial you
will find online uses it. Pick RT-DETR instead when your product cannot carry the
AGPL licence, which the next paragraph explains.

The cost is mostly the licence. Ultralytics is published under AGPL-3.0, which
obliges you to publish the source of anything you combine it with, including
software you never hand out but only run as a service for other people. The weights
carry the same terms. A paid Enterprise licence removes that obligation and is
[priced by negotiation](https://www.ultralytics.com/license). Book 2 explains the
trap in [licences, and the one that will catch you
out](../../../02_perception/02_object-perception/06_licences-and-platforms.md#1-licences-and-the-one-that-will-catch-you-out).
The other costs are small. The documentation's own table gives `yolo26n` 2.4
million parameters, 40.9 mAP on COCO and 1.7 milliseconds on an NVIDIA T4 graphics
card with TensorRT, against 55.7 million parameters, 57.5 mAP and 11.8 milliseconds
for `yolo26x`. Here mAP is short for mean average precision, which is the standard
score for a detector, and a higher number is better. The same table gives `yolo26n`
38.9 milliseconds on a processor, so the smallest size runs without a graphics card.
What goes wrong most often is the class list, because people assume the 80 COCO
classes include their own parts.

The library is `ultralytics`, which you install with `pip install ultralytics`.

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")                 # the weights download on first use
result = model("table.jpg", conf=0.25)[0]  # conf is the confidence threshold

for box in result.boxes:
    name = result.names[int(box.cls)]
    # xywh is the box as its middle and its size; xyxy would be its two corners.
    middle_u, middle_v, width, height = box.xywh[0].tolist()
    print(f"{name} {float(box.conf):.2f} at pixel ({middle_u:.0f}, {middle_v:.0f})")
```

You supply the picture and the threshold. The library downloads the weights, resizes
the picture, runs the network, and runs the non-maximum suppression of [section
3](#3-how-it-works-inside) for you. It can also skip that cleanup step, because the
documentation describes a second head that you select with `nms=False` and that
returns at most 300 boxes with no suppression pass. What you still have to write is
everything after the box, which is section
6.

### 5.2 RT-DETR

**Most used in 2026** among teams that read the licence first, because it is a
permissive detector with an API that anyone who has used Hugging Face already
knows.

RT-DETR is short for "real-time detection transformer". Its paper, "DETRs Beat YOLOs
on Real-time Object Detection"
([arXiv:2304.08069](https://arxiv.org/abs/2304.08069)), appeared in April 2023, and
it is the model that made the transformer design of section 3 fast enough for a live
camera. The weights are published as
[PekingU/rtdetr_r50vd](https://huggingface.co/PekingU/rtdetr_r50vd).

The obvious alternative is Ultralytics YOLO26. Pick RT-DETR when you are building
something you will sell or run as a service without publishing its source, because
both the code and the weights are Apache-2.0, which puts no such condition on you.
You also get the transformer's own advantage, which is that the model gives one box
per object and needs no cleanup step, so two cups standing against each other do
not lose a box to the suppression step.

The costs are a bigger model and a slower start. The published checkpoint holds 43.0
million parameters, read from the model card's file listing, against 2.4 million for
the smallest YOLO26. The paper reports 53.1 mAP and 108 frames a second for this
size on a T4 graphics card, which is quoted on the library's
[RT-DETR page](https://huggingface.co/docs/transformers/en/model_doc/rt_detr).
Fine-tuning means writing a training loop rather than calling one method. The thing
that goes wrong most often is the picture size, because that page states the model
expects 640 by 640 and that other sizes usually make it worse.

The library is `transformers`, which you install with `pip install transformers`.
The code below is the example from that page, shortened.

```python
import torch
from PIL import Image
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

processor = RTDetrImageProcessor.from_pretrained("PekingU/rtdetr_r50vd")
model = RTDetrForObjectDetection.from_pretrained("PekingU/rtdetr_r50vd")

image = Image.open("table.jpg")
inputs = processor(images=image, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

# target_sizes wants the height first, so that the boxes come back in the
# original picture's pixels rather than in the resized picture's pixels.
results = processor.post_process_object_detection(
    outputs, target_sizes=torch.tensor([(image.height, image.width)]), threshold=0.3
)[0]
for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
    print(model.config.id2label[label.item()], round(score.item(), 2), box.tolist())
```

You supply the picture and the threshold, as before. The processor resizes the
picture and scales the boxes back to it, and the model carries the 80 COCO class
names, which is why `id2label` can give you the word "cup". What you have to supply
yourself is a graphics card if you want this on every frame of a live camera.

### 5.3 RF-DETR

**Worth betting on**, because it is the direction the field is going: a transformer
detector with a permissive licence that beats the YOLO family on accuracy at the
same latency, measured by its authors in one harness rather than quoted from
separate papers.

RF-DETR comes from Roboflow, a company that sells computer vision tooling, with
co-authors at Carnegie Mellon University. Its paper "RF-DETR: Neural Architecture
Search for Real-Time Detection Transformers"
([arXiv:2511.09554](https://arxiv.org/abs/2511.09554)) is from November 2025, and
its [repository](https://github.com/roboflow/rf-detr) publishes six sizes, from Nano
to 2XLarge.

The obvious alternative is again Ultralytics YOLO26, because the two packages are
about equally easy to use. Pick RF-DETR when you want the permissive licence and the
better boxes at once. Its README reports every row measured in one harness on the
5,000 pictures of the COCO validation split, with latency on an NVIDIA T4 graphics
card using TensorRT: RF-DETR-Nano reaches 48.4 average precision at 2.3
milliseconds, where YOLO26-N reaches 40.3 at 1.7 milliseconds. Those are the
authors' measurements of their own model against a competitor, so read them as a
claim with a method attached rather than as a neutral result.

The costs are size and a licence detail. RF-DETR-Nano holds 30.5 million parameters,
more than ten times the smallest YOLO26, because its backbone is a DINOv2 vision
transformer, so there is no very small version for a tiny computer. The two largest
sizes are not Apache-2.0 at all: the README states that XL and 2XL live in a
separate `rfdetr_plus` package under a licence called PML 1.0, so the permissive
promise covers Nano, Small, Medium and Large only. The project is also young, so its
API still changes between releases.

The library is `rfdetr`, which you install with `pip install rfdetr`. It returns
its answers as a `Detections` object from the `supervision` library, which is the
same type several other detectors in this family use.

```python
from rfdetr import RFDETRMedium
from rfdetr.assets.coco_classes import COCO_CLASSES

model = RFDETRMedium()                    # replace with RFDETRNano for the small one
detections = model.predict("table.jpg", threshold=0.5)

for class_id, confidence, box in zip(detections.class_id, detections.confidence,
                                     detections.xyxy):
    # xyxy is the box as its left, top, right and bottom edges, in pixels.
    print(COCO_CLASSES[class_id], round(float(confidence), 2), box.tolist())
```

You supply the picture and the threshold, and the package downloads the weights and
returns boxes in your picture's pixels. The `COCO_CLASSES` list above applies only to
the COCO-trained weights, and the README says to read `detections.data["class_name"]`
instead once you have fine-tuned the model on your own classes.

### 5.4 D-FINE

**Worth betting on** for work where the edges of the box have to be right, because
it changes how the network predicts those edges rather than how fast it runs.

D-FINE is a detection transformer that predicts each edge of the box as a
probability distribution over where that edge lies, sharpened step by step, instead
of one guess at four numbers. The Hugging Face
[D-FINE page](https://huggingface.co/docs/transformers/en/model_doc/d_fine)
summarises the paper's results as 54.0 and 55.8 average precision on COCO for the
Large and XLarge sizes, at 124 and 78 frames a second on an NVIDIA T4 graphics card.
The code is at [Peterande/D-FINE](https://github.com/Peterande/D-FINE).

The obvious alternative is RT-DETR, which D-FINE is built from. Pick D-FINE when you
do something with the box edges other than point at the middle, for example measuring
an object's width in pixels or cutting the object out to pass to another model,
because that is the part it improves. Pick RT-DETR when you want the older and more
widely used model, which has more tutorials and more people who have met your
problem already.

The costs are the usual ones for this family. The largest checkpoint holds 62.9
million parameters, read from its
[model card](https://huggingface.co/ustc-community/dfine_x_coco), so it wants a
graphics card. The model is also less written about than RT-DETR, so fewer people
have published training settings for it. The licence is Apache-2.0, read from the
repository.

The library is `transformers` again, and the code differs from section 5.2 in two
lines only, which is the practical reason to prefer Hugging Face over each
project's own repository.

```python
from transformers import AutoImageProcessor, DFineForObjectDetection

processor = AutoImageProcessor.from_pretrained("ustc-community/dfine_x_coco")
model = DFineForObjectDetection.from_pretrained("ustc-community/dfine_x_coco")
# Everything after this point is the RT-DETR code of section 5.2, unchanged,
# because post_process_object_detection is shared by both models.
```

What you supply is the same as for RT-DETR. What the library gives you is one
interface over many detectors, so swapping the two names above compares two models on
your own photos in an afternoon.

### 5.5 Faster R-CNN

**Historical**, kept because it is the two-stage design of section 3 in a library
you already have, and because it is still the shortest way to fine-tune a detector
without adding a dependency.

Faster R-CNN was published in 2015, and its name comes from "region-based
convolutional neural network". It established the two-step shape: suggest a few
hundred places, then classify each one. It ships inside torchvision, the image half
of PyTorch, and the newer of its two versions is `fasterrcnn_resnet50_fpn_v2`.

The obvious alternative is any of the four models above, all of which are faster.
Pick Faster R-CNN anyway when your project is already a PyTorch project, when you
want to fine-tune with code you can read end to end, and when the camera gives you a
picture every second rather than thirty times a second. Its BSD-3-Clause licence is
the most permissive in this table.

The costs are speed and age. The torchvision
[model page](https://pytorch.org/vision/stable/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn_v2.html)
gives this version 43.7 million parameters and 46.7 box mAP on the COCO validation
split. It states no speed, and the second step runs once per proposal, so this is the
slowest model here. It also needs the cleanup step of section 3, with its weakness
for objects that touch.

The library is `torchvision`, which arrives with PyTorch.

```python
import torch
from torchvision.io import decode_image
from torchvision.models.detection import (fasterrcnn_resnet50_fpn_v2,
                                          FasterRCNN_ResNet50_FPN_V2_Weights)

weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
model = fasterrcnn_resnet50_fpn_v2(weights=weights).eval()

image = decode_image("table.jpg")
# weights.transforms() is the exact preparation these weights were trained with.
batch = [weights.transforms()(image)]
with torch.no_grad():
    prediction = model(batch)[0]

for label, score, box in zip(prediction["labels"], prediction["scores"],
                             prediction["boxes"]):
    if score > 0.5:                       # torchvision applies no threshold for you
        print(weights.meta["categories"][label], round(float(score), 2), box.tolist())
```

You supply the picture and, this time, the threshold test itself, because torchvision
returns every box the network produced. The `weights.transforms()` call is the part
worth copying, because getting that preparation wrong is the usual reason a
torchvision model gives poor answers.

### 5.6 DETR

**Historical**, kept because it explains the query idea that RT-DETR, RF-DETR and
D-FINE are all built on.

DETR, short for "detection transformer", came from Facebook AI Research in 2020, and
it is the model section 3 describes under "a fixed set of answers". Each of its 100
queries gives one box or the answer "no object", and training matches one query to
each real object, which removes the need for a cleanup step.

The obvious alternative is RT-DETR, which is the same idea made fast, and there is no
case today for putting DETR on a robot instead. Pick DETR only to read, because its
weakness explains why the later models exist: it took far longer to train than a
one-stage detector of its day, and it was poor on small objects. If you do run it,
the ResNet-50 checkpoint holds 41.6 million parameters and no real-time speed, and
its licence is Apache-2.0 for both code and weights, read from the
[model card](https://huggingface.co/facebook/detr-resnet-50).

The library is `transformers`, and the code is the RT-DETR code of section 5.2 with
the names changed.

```python
from transformers import AutoImageProcessor, AutoModelForObjectDetection

processor = AutoImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = AutoModelForObjectDetection.from_pretrained("facebook/detr-resnet-50")
# The rest is section 5.2's code, because the post-processing call is the same.
```

What you supply is a picture. What you get back is a list of 100 answers of which
most say "no object", and that is the clearest way to see what a query-based detector
does.

### 5.7 How to choose

Start with Ultralytics YOLO26 if you may publish your source code or pay for the
Enterprise licence, because nothing else gets you from an empty folder to boxes on
your own photo as quickly.

Four things change that answer.

- **You are selling a product, or running a service, and will not publish your
  source.** Then the AGPL licence rules Ultralytics out, and you take RF-DETR for
  the best boxes or RT-DETR for the most familiar code. Check that you stay within
  RF-DETR's Nano to Large sizes, because XL and 2XL are under a different licence.
- **The computer has no graphics card.** Then take the smallest Ultralytics
  checkpoint, measure it on your own pictures, and read [running a model on a
  robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  before you promise anyone a frame rate.
- **Your objects stand against each other, or they overlap.** Then prefer a model
  that needs no cleanup step, which means RT-DETR, RF-DETR, D-FINE, or Ultralytics
  with `nms=False`, because the suppression step is what loses one of two touching
  objects.
- **Your objects are not among the 80 COCO classes.** Then the model matters less
  than the labelling, because you will fine-tune whichever one you pick. Choose the
  one whose training code you can live with, which today usually means Ultralytics
  or RF-DETR.

If you cannot list your objects in advance at all, no model in this section will find
them, and the page you want is [open-vocabulary
models](03_open-vocabulary-models.md). Book 2's [models that find
objects](../../../02_perception/02_object-perception/04_models-that-find.md#11-box-detectors)
lists more detectors, each with the licence read from its own licence file.

---

## 6. Where to read next

- The next page is [segmentation](02_segmentation.md), which replaces the box with
  the exact outline of each object.
- [Image classification](../03_also-used/01_image-classification.md) explains the backbone and
  the fine-tuning that every detector uses.
- [Open-vocabulary models](03_open-vocabulary-models.md) find objects from a word,
  without training on them first.
- [Tracking and motion](../03_also-used/03_tracking-and-motion.md) follows detected objects from
  one picture to the next.
- [Running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains how fast a model must be, and where it runs.
- Book 2 goes deeper in
  [finding an object in a picture](../../../02_perception/01_camera/02_finding-objects.md),
  which runs a real YOLO detector, and in
  [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md).
