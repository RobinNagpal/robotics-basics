# Image classification

This page explains the simplest seeing model, which is one that looks at a whole
picture and gives it one name. It answers five questions: what such a model does,
what goes in and what comes out, how it works inside, how it is trained, and when
it is the right choice for a robot arm.

It is written for a reader who has already read the [seeing models
overview](../01_overview.md) and the first chapter of this book, but you do not
need to know any machine learning, because every term is explained where it
first appears.

This page comes first in the chapter for a reason, since nearly every other seeing
model contains an image classifier, or most of one. So the ideas here come back on
every later page.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [Where to read next](#6-where-to-read-next)

---

## 1. What it is

An **image classifier** is a model that looks at a picture and says which one of a
fixed list of names fits it best.

That fixed list is chosen before training, and each name on the list is called a
**class**. A class can be a kind of object, such as "mug", "bowl" or "bottle", and
it can also be a state, such as "gripper empty" or "gripper holding something".

Here is an everyday example: imagine a sorting machine for fruit, where a camera
takes a photo of each piece of fruit on a belt. A person could look at each photo
and say "apple", "orange" or "lemon". So an image classifier does the same, because
it looks at the photo and picks one of the three names.

The classifier gives one name for the whole picture. So it does not say where in
the picture the object is, and it does not say how many objects there are either.
If a photo shows two apples and an orange, a classifier still gives just one name.
The [object detection](../02_most-used/01_object-detection.md) page covers models
that find each object separately.

---

## 2. What goes in and what comes out

The input is one picture, and to a computer a picture is simply a grid of numbers.
Each small square of the grid is a pixel, and a grey picture has one number per
pixel, which says how bright that pixel is. So the number 0 means black, and the
number 255 means white. A colour picture has three numbers per pixel instead, one
for red, one for green and one for blue.

The picture below shows a tiny grey picture of a mug, and the numbers inside one
corner of it.

![A tiny picture of a mug becoming a list of numbers](../../../images/seeing-models/image-classification/pixels-become-numbers.svg)

The left part is the picture, 12 pixels wide and 12 pixels high, while the middle
part enlarges the red square and writes each pixel's number in it. The right part
is what the model is actually given: the same numbers, one row after another.

A real camera picture is much bigger than that. For example, a picture 640
pixels wide and 480 pixels high has 307,200 pixels, and with three colour
numbers each, that is 921,600 numbers. So most classifiers first shrink the
picture to a fixed size, often a square about 224 pixels wide, so that every
picture gives the same count of numbers.

The output is one **score** for each class, where a score is a number between 0 and 1.
So a higher score means the model is more sure that the class fits. The scores
for all the classes add up to 1, and the answer is the class with the highest
score.

The picture below shows a picture of a mug going in, and five scores coming out.

![One picture in, one score per name out](../../../images/seeing-models/image-classification/one-score-per-name.svg)

The numbers in this picture are an example rather than real output. In the example,
"mug" has the highest score, 0.81, so the answer is "mug", while the second-highest
score is for "cup", which is a similar object. This is typical, because a
classifier that is wrong is usually wrong in favour of a similar-looking class.

On a robot arm, the input is usually one picture from the camera, or a small
part cut out of it. Then the output is used as a yes-or-no check, or to choose
what to do next.

---

## 3. How it works inside

A classifier is a neural network, and it is built in **layers**. This means that
each layer takes a grid of numbers in, does simple sums on it, and passes a new
grid of numbers on to the next layer. The page [inside a neural
network](../../01_what-models-are/03_inside-a-neural-network.md) explains layers
in general, while this section explains what the layers of a classifier do in
particular.

The most common kind of classifier is a **convolutional neural network (CNN)**, and
a CNN works in these steps.

1. The first layer slides a small square, often 3 pixels by 3 pixels, across the
   whole picture. At each place, it multiplies the 9 pixel numbers by 9 fixed
   numbers and adds them up, and this sliding sum is called a **convolution**. The
   9 fixed numbers are called a **filter**, and the layer has many filters, so each
   one gives its own new grid.
2. Some filters give a large number where there is an edge in the picture, so one
   filter reacts to flat edges, another reacts to upright edges, and another reacts
   to curves. Nobody chooses these filters by hand, because training finds them.
3. Every few layers, the grid is made smaller. For example, each square of 2 by 2
   numbers is replaced by the largest of the four, which keeps the important
   numbers and throws away where exactly they were.
4. The next layers do the same thing again, on the smaller grids, and because they
   combine edges, their filters react to parts: a round rim, a handle loop, or the
   neck of a bottle.
5. The last layers then combine those parts, so their numbers react to whole
   objects: a mug, a bottle, a bowl.
6. At the very end, one small layer turns those numbers into one score per class,
   and a last step makes the scores positive and makes them add up to 1.

The picture below shows this build-up, from edges to parts to whole objects.

![Early layers react to edges, middle layers to parts, last layers to objects](../../../images/seeing-models/image-classification/edges-parts-objects.svg)

The drawings in the tiles show the kind of pattern that makes each layer give a
large number. Researchers have looked inside trained networks, and they found this
same order again and again.

Both of the convolutional networks on this page's shortlist are built in those
steps: ResNet-50, in [section 5.1](#51-resnet), and MobileNetV3, in [section
5.2](#52-mobilenetv3). ResNet added one thing to the list above, and the later
networks all kept it. In a network of many layers, the output of one layer is also
added, unchanged, to the output of a layer two or three further on, and that added
shortcut is called a **skip connection**. It gives the early layers a short path
back to the score, so a network of fifty layers trains as well as a short one.

A newer kind of classifier is the **vision transformer (ViT)**, which cuts the
picture into small squares, called **patches**, often 16 pixels by 16 pixels. Then
it turns each patch into a list of numbers. After that, each patch's numbers are
updated by looking at all the other patches, and this step is called
**attention**. After many
such layers the model gives the scores. A vision transformer needs more training
pictures than a CNN, but with enough pictures it is often more accurate. The two
large backbones on the shortlist are vision transformers: DINOv2, in [section
5.3](#53-dinov2-with-a-small-head), and DINOv3, in [section 5.5](#55-dinov3).

The part of the network before the last layer is called the **backbone**, while the
last layer, which gives the scores, is called the **head**. This split matters,
because a backbone trained for classification has learned edges, parts and objects,
so other seeing models can reuse that backbone and change only the head.

The split also decides how you get a classifier of your own, and
[section 5](#5-well-known-models) sets out three ways of doing that. The first way
trains a backbone and a head together on your own pictures. The second leaves
somebody else's backbone exactly as it is and trains only a new head on top of it.
The third way has no head with one output per class at all, so it takes a word of
explanation here. A **vision-language model** is two networks: one turns a picture into a list of numbers, and the other turns a
sentence into a list of numbers of the same length. The two were trained together
on pictures paired with the sentences that describe them, so that a picture and a
true description of it come out as nearly the same numbers. You then write each of
your class names as a sentence, and a class's score is how close its sentence's
numbers are to the picture's numbers. SigLIP 2, in [section 5.4](#54-siglip-2),
works this way, and nothing in it is trained by you, which is why that third way
asks for no pictures of your own.

---

## 4. How it is trained

Training needs many pictures, and each picture needs a **label**, which is the
correct class written down by a person.

The most famous collection of labelled pictures is **ImageNet**, and the part of it
used in a yearly research contest has about 1.2 million training pictures, split
into 1,000 classes. Those classes include many animals and everyday objects, such
as "coffee mug", "water bottle" and "screwdriver".

Training itself then works in the five steps below.

1. The network starts with random numbers in its filters, so its answers are random
   too.
2. It is shown a small batch of pictures, for example 32 of them.
3. For each picture it gives its scores, and a program then measures how wrong they
   are, where the answer counts as very wrong if the correct class got a low score.
4. The program nudges every filter number a tiny amount, in the direction that
   makes the answers less wrong.
5. This repeats with the next batch, and so on, many times through all the
   pictures.

The page [how a model learns](../../01_what-models-are/02_how-a-model-learns.md)
explains this nudging in more detail.

Training from nothing on ImageNet takes many hours on many graphics cards, so a
robot project almost never does that. Instead it starts from a network that someone
else already trained on ImageNet, replaces the head with a new one for its own
classes, such as "gripper empty" and "gripper holding something", and then trains a
little more on its own pictures, which is called **fine-tuning**.

Fine-tuning works with far fewer pictures, often a few hundred per class,
because the backbone already knows edges and parts, and those are the same in
every picture. So only the head has much left to learn. Book 2 shows the same
idea for a detector in [fine-tuning: why 80 pictures are
enough](../../../02_perception/01_camera/02_finding-objects.md#64-fine-tuning-why-80-pictures-are-enough).

---

## 5. Well-known models

This section names the models a developer actually reaches for in 2026, and it
helps you decide which one to use. It also helps you decide whether you need a
classifier of your own at all.

Almost nobody trains a classifier from nothing any more, for the reason section 4
gave. What people do instead falls into three routes. The first fine-tunes a small
network on a few hundred of your own pictures. The second takes a large network
that somebody else trained, keeps it exactly as it is, and trains only a tiny last
layer on top, which is called a **frozen backbone** because the backbone's numbers
never change. The third trains nothing at all: you take a vision-language model,
which [section 3](#3-how-it-works-inside) explains, and you hand it your class
names as words.

The table has five rows, and between them they cover all three routes. Read it like
this. The left column names the model and says how current it is. The right column
is written as sentences, and the first of them says which route the model belongs
to, because that is the part to read first. The sentences after it give the model's
size, the licence on its weights, the job it is best at and when to pick it. A size
is given as a number of parameters, where a **parameter** is one of the numbers
inside the network, and the count tells you roughly how much memory and time the
model needs. Every count was taken from the file Hugging Face serves, and every
licence from that model's own model card.

| Model | What decides it |
| --- | --- |
| **ResNet-50**, historical | ResNet-50 is a convolutional network, and it belongs to the fine-tuning route. It has 25.6 million parameters, and its weights are Apache-2.0. It is best at being the number everyone compares against, so pick it when you need a baseline other people recognise. |
| **MobileNetV3-Large**, most used in 2026 | MobileNetV3-Large is a convolutional network for the fine-tuning route as well. It has 5.5 million parameters, and its weights are Apache-2.0. It is best at running fast on a small computer, so pick it when the check runs often and there is no graphics card. |
| **DINOv2, base size**, most used in 2026 | DINOv2 is a vision transformer, and it belongs to the frozen-backbone route. Its base size has 86.6 million parameters, and its weights are Apache-2.0. It is best at giving features a tiny head can classify, so pick it when you have tens of pictures per class rather than hundreds. |
| **SigLIP 2, base size, 224 pixels in**, most used in 2026 | SigLIP 2 is a vision-language model, so it belongs to the route that trains nothing. Its base model at 224 pixels has 375 million parameters for both halves together, and its weights are Apache-2.0. It is best at naming classes you can only describe in words, so pick it when you have no training pictures at all. |
| **DINOv3, base size**, worth betting on | DINOv3 is a vision transformer for the frozen-backbone route, like DINOv2 above. Its base size has 85.7 million parameters, and its weights come under a bespoke DINOv3 licence rather than a standard one. It does the same job as DINOv2 and does it better, so pick it when you have read that licence and accepted it. |

### 5.1 ResNet

ResNet is **historical** here, and it is kept because the later models borrow from
it and because every accuracy table still starts with it. Microsoft Research
published it in December 2015, in the paper [Deep Residual Learning for Image
Recognition](https://arxiv.org/abs/1512.03385), and its idea was the skip
connection from section 3. ResNet-50 is the 50-layer member of the family and has
about 25.6 million parameters.

You would not pick it for a new robot classifier. The obvious alternative is a
frozen DINOv2 with a small head, from section 5.3, which needs fewer of your own
pictures and usually gives better accuracy. Pick ResNet-50 instead when you want a
number that other developers recognise without explanation. What it costs you is
accuracy for its size, because it was trained with labels on ImageNet and its
features are weaker than those of the self-supervised backbones below.

The library is Hugging Face `transformers`, whose `pipeline` helper puts the
preparation of the picture, the network and the reading of the scores behind one
call.

```python
from transformers import pipeline

# "microsoft/resnet-50" is the Apache-2.0 checkpoint trained on ImageNet.
classifier = pipeline("image-classification", model="microsoft/resnet-50")

# The answers come back sorted, with the most likely first.
for guess in classifier("part.jpg")[:3]:
    print(guess["label"], round(guess["score"], 3))
```

The pipeline shrinks the picture to 224 by 224 pixels, normalises it the way this
model was trained, turns the scores into numbers that add up to 1, and sorts them.
What you still have to supply is your own class list, which means fine-tuning. The
thing that most often goes wrong is running it as it comes and being surprised by
the answers, because its 1,000 ImageNet classes are mostly animals and household
objects and contain nothing from a factory.

### 5.2 MobileNetV3

MobileNetV3 is **most used in 2026** when the classifier has to run on the robot
itself with no graphics card. Google published it in May 2019, in the paper
[Searching for MobileNetV3](https://arxiv.org/abs/1905.02244), and part of its
layer arrangement was found by a search program rather than chosen by a person.
The `mobilenetv3_large_100` weights have about 5.5 million parameters.

The obvious alternative is EfficientNet-B0, which reaches similar accuracy at a
similar size. MobileNetV3 is the one to pick because it is the most widely
converted: ready versions exist for the phone and microcontroller runtimes, so
the step from your trained file to the robot's processor is one that many people
have already made. Against the frozen backbone of section 5.3, MobileNetV3 wins
on cost per picture at run time, and that is what matters when the check runs
every time the gripper closes.

What it costs you is that you must train it, which the frozen-backbone route
largely avoids. Plan on a few hundred labelled pictures per class, and accept
accuracy below that of a large backbone on hard classes. The licence is
Apache-2.0 and gives you no trouble. The thing that most often goes wrong is the
preparation of the picture: resize or normalise differently from the way the
weights were trained and accuracy falls with no error message. That is why the
code below asks the library for the right transform instead of writing one.

The library is `timm`, which holds pretrained picture models and their matching
preparation settings. Its [quickstart
page](https://huggingface.co/docs/timm/quickstart) documents these calls.

```python
import timm

# num_classes=2 throws away the 1,000-class head and puts an untrained
# two-class head in its place: "holding a cup" and "empty".
model = timm.create_model("mobilenetv3_large_100", pretrained=True, num_classes=2)

# Ask the checkpoint itself how its pictures were prepared, then build
# exactly that transform.
data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
transform = timm.data.create_transform(**data_cfg)

print(sum(p.numel() for p in model.parameters()))   # the parameter count
```

What the library gives you is the trained backbone and the correct transform. What
you still have to supply is the training itself, because `timm` ships no training
loop for your own data: its documentation tells you to write a PyTorch loop or
adapt its [training script](https://huggingface.co/docs/timm/training_script). You
also supply the pictures, the split between training and testing, and the score
threshold below which the robot treats the answer as unknown.

### 5.3 DINOv2 with a small head

DINOv2 is **most used in 2026** for a custom class list, because it is the
cheapest way to get a good classifier from a small number of pictures. Meta
published it in April 2023, in the paper [DINOv2: Learning Robust Visual Features
without Supervision](https://arxiv.org/abs/2304.07193), and both the
[code](https://github.com/facebookresearch/dinov2) and the weights are
Apache-2.0. It is a vision transformer trained **self-supervised**, which means
nobody labelled its training pictures: it learned by being asked to give two
different crops of the same picture the same numbers. Its base size has about 86.6
million parameters.

The obvious alternative is to fine-tune a ResNet or a MobileNetV3, which trains
the whole network. This repository's own survey of backbones reports that a simple
classifier placed on DINOv2's features matches networks trained end to end, in
[backbones and
features](../../../02_perception/02_object-perception/04_models-that-find.md#15-backbones-and-features).
That is why the frozen route wins when pictures are scarce. You train one small
layer on a processor in seconds, and tens of pictures per class are often enough,
where fine-tuning wants hundreds.

What it costs you is run-time speed. All 86.6 million parameters run for every
picture even though you train almost none of them, so it is much slower per
picture than a fine-tuned MobileNetV3. The features are frozen, so if two of your
classes differ in a way this backbone never learned to separate, a small head
cannot repair that, and your only move is to fine-tune after all. The thing that
most often goes wrong is that your head is a second file, separate from the
backbone, and people ship the backbone without it.

The libraries are `transformers` for the backbone and `scikit-learn` for the head.
The head here is logistic regression, which this book explains in [linear and
logistic
regression](../../02_classical-machine-learning/02_most-used/01_linear-and-logistic-regression.md).

```python
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from transformers import AutoImageProcessor, AutoModel

processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
backbone = AutoModel.from_pretrained("facebook/dinov2-base").eval()

def features(paths):
    batch = processor(images=[Image.open(p) for p in paths], return_tensors="pt")
    with torch.inference_mode():
        # pooler_output is the first token of the last layer: 768 numbers
        # that describe the whole picture.
        return backbone(**batch).pooler_output.numpy()

train_paths = ["held_01.jpg", "held_02.jpg", "empty_01.jpg", "empty_02.jpg"]
labels = np.array([1, 1, 0, 0])

head = LogisticRegression(max_iter=1000).fit(features(train_paths), labels)
print(head.predict_proba(features(["test.jpg"])))
```

What the library gives you is the 768 numbers per picture and the preparation that
goes with them. What you still have to supply is a real set of pictures, because
four is only enough to show the shape of the code, and a second set the head never
saw, so that you can measure the accuracy and choose the threshold. You also save
the fitted head yourself, with `joblib` or `pickle`, because `transformers` knows
nothing about it.

### 5.4 SigLIP 2

SigLIP 2 is **most used in 2026** when you have no training pictures, because it
needs none. Google published it in February 2025, in the paper [SigLIP 2:
Multilingual Vision-Language Encoders with Improved Semantic Understanding,
Localization, and Dense Features](https://arxiv.org/abs/2502.14786). It has two
halves, one that turns a picture into numbers and one that turns a sentence into
numbers, trained so that a picture and its true description land close together.
You give it your class names as sentences, and it scores each sentence against the
picture. The base model at 224 pixels has about 375 million parameters for both
halves together, and the weights are Apache-2.0.

The obvious alternative is CLIP, which stands for contrastive language-image
pre-training, published by OpenAI in February 2021 as [Learning Transferable
Visual Models From Natural Language
Supervision](https://arxiv.org/abs/2103.00020). It does the same job and it is the
model whose name everybody knows. SigLIP changed how the two halves are trained,
and its name says how: the [Sigmoid Loss for Language Image
Pre-Training](https://arxiv.org/abs/2303.15343) paper scores each
picture-and-sentence pair on its own, where CLIP compares every picture in a batch
against every sentence at once. That is the reason to prefer it here. SigLIP's
scores do not add up to 1 across your class names, so all of them can be low at
once, and "none of these" becomes an answer you can read. What it costs you is size, speed and wording. At 375 million parameters it wants a
graphics card to be comfortable, and it is the slowest model on this page. Its
accuracy depends on the words you choose, so "a scratched metal plate" and "a
damaged plate" are different questions with different answers. It cannot separate
two parts whose difference has no ordinary name, such as two similar valve bodies,
and [models that
find](../../../02_perception/02_object-perception/04_models-that-find.md) sets out
that limit. The thing that most often goes wrong is the text padding: the Hugging
Face [SigLIP 2
documentation](https://huggingface.co/docs/transformers/en/model_doc/siglip2) says
to pass `padding="max_length"` with `max_length=64` when you call the processor
yourself, because the model was trained that way.

The library is `transformers`, with a different pipeline task from the one in
section 5.1.

```python
from transformers import pipeline

classify = pipeline("zero-shot-image-classification",
                    model="google/siglip2-base-patch16-224")

# These are not fixed classes in the model. They are sentences you choose,
# and you can change them without retraining anything.
labels = ["a gripper holding a cup", "an empty gripper"]

for guess in classify("wrist.jpg", candidate_labels=labels):
    print(guess["label"], round(guess["score"], 3))
```

What the library gives you is the whole classifier without a training step, the
right text padding, and the freedom to change the class list by editing a line.
For a SigLIP model the pipeline also scores each label on its own rather than
against the others, so the scores you print will not add up to 1. What you still
have to supply is the wording, which you should test on real pictures before you
trust it, the threshold below which you treat every score as "none of these", and
the crop, because this model names the whole picture just as a classifier does.

### 5.5 DINOv3

DINOv3 is **worth betting on**, because the direction of the field is a single
large frozen backbone with a tiny trained head, and DINOv3 is that idea done
better than DINOv2. Meta published it in August 2025, as
[DINOv3](https://arxiv.org/abs/2508.10104), and the Hugging Face
[documentation](https://huggingface.co/docs/transformers/en/model_doc/dinov3)
describes it as giving strong dense features without fine-tuning. Its base model
has about 85.7 million parameters, almost exactly the size of DINOv2's base model,
so the gain is not paid for in size.

The obvious alternative is DINOv2, from section 5.3, and the one real reason to
stay there is the licence. That is also why DINOv3 is not yet the default. DINOv2
is Apache-2.0 and you can forget about it, while DINOv3 ships Meta's own [DINOv3
licence](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md). That
licence does permit commercial use, and it attaches conditions: you pass the
agreement on to anyone you give the weights to, you acknowledge the model in
anything you publish, and you must not use it for military purposes or for
weapons. Open weights are not the same thing as open source, and this repository's
[licences and
platforms](../../../02_perception/02_object-perception/06_licences-and-platforms.md)
page lists the other models in the same position.

What it costs you, beyond reading that licence, is a step in your build. The
weights are gated on Hugging Face, so a download without a signed-in account that
has accepted the terms fails with the message that access to the model is
restricted. A one-line download becomes a login and an access token on every
machine that builds your project, including your build server.

The library is `transformers`, and the code is the code of section 5.3 with the
checkpoint name changed.

```python
from transformers import AutoImageProcessor, AutoModel

name = "facebook/dinov3-vitb16-pretrain-lvd1689m"

# This fails until you accept the DINOv3 terms on the model page and
# log in, for example with: huggingface-cli login
processor = AutoImageProcessor.from_pretrained(name)
backbone = AutoModel.from_pretrained(name).eval()
```

From there the rest of section 5.3 is unchanged, because this model also returns
its description of the picture in `pooler_output`. What you still have to supply is
the same small head and the same measured threshold, plus the account step above.

### 5.6 How to choose

Start with a frozen DINOv2 and a logistic-regression head, from section 5.3,
because it gives you a usable classifier from tens of pictures per class and
nothing more than an ordinary processor.

Six things change that choice.

- You have no training pictures, and your classes can be said in ordinary words.
  Then use SigLIP 2 from section 5.4 and write the class names as sentences.
- The classifier runs on the robot, on every gripper close, with no graphics card.
  Then collect a few hundred pictures per class and fine-tune a MobileNetV3 from
  section 5.2.
- You are shipping a product and you want the strongest frozen features. Then
  read the DINOv3 licence from section 5.5, and stay with DINOv2 if the
  conditions do not suit you.
- You need a baseline number that other developers will recognise. Then use
  ResNet-50 from section 5.1, and do not ship it.
- You need to know where the object is, or how many there are. Then you do not
  want a classifier at all, and [object
  detection](../02_most-used/01_object-detection.md) is the page to read.
- You need an answer in words rather than one name from a fixed list, such as what
  is wrong with a part. Then read [open-vocabulary
  models](../02_most-used/03_open-vocabulary-models.md), which covers the models
  that answer questions about a picture.

One more case sits outside the list. If the scene is fully controlled and the
answer depends on one thing you can measure, such as a height or a colour, write
the rule instead and skip the models entirely. ---

## 6. Where to read next

- The next page is [object detection](../02_most-used/01_object-detection.md), which adds boxes,
  so that the robot knows where each object is.
- [Segmentation](../02_most-used/02_segmentation.md) goes one step further and marks the exact
  pixels of each object.
- [Inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md)
  explains layers and sums in more detail.
- [How a model learns](../../01_what-models-are/02_how-a-model-learns.md) explains
  training.
- [The seeing models overview](../01_overview.md) compares all seven kinds of seeing
  model.
- Book 2's [models that find objects](../../../02_perception/02_object-perception/04_models-that-find.md)
  lists backbones you can download, with their licences.
