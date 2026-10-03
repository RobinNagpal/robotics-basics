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
6. [Where it is used on a robot arm](#6-where-it-is-used-on-a-robot-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why classification, and what it costs](#8-why-classification-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

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

A newer kind of classifier is the **vision transformer (ViT)**, which cuts the
picture into small squares, called **patches**, often 16 pixels by 16 pixels. Then
it turns each patch into a list of numbers. After that, each patch's numbers are
updated by looking at all the other patches, and this step is called
**attention**. After many
such layers the model gives the scores. A vision transformer needs more training
pictures than a CNN, but with enough pictures it is often more accurate.

The part of the network before the last layer is called the **backbone**, while the
last layer, which gives the scores, is called the **head**. This split matters,
because a backbone trained for classification has learned edges, parts and objects,
so other seeing models can reuse that backbone and change only the head.

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

It helps to see those ideas in real classifiers, and these are ones that people use
or build on. Each of them is also used as a backbone inside other seeing models.

- **AlexNet** was a CNN that won the ImageNet contest in 2012 by a wide margin,
  because it showed that neural networks trained on graphics cards beat
  hand-written methods for pictures. Few people use it today, but it started the
  change.
- **ResNet** is a CNN from Microsoft Research, from 2015, and it added "skip
  connections", which pass a layer's input straight on to a later layer. These made
  it possible to train much deeper networks, so ResNet is still a common backbone.
- **MobileNet** is a family of small CNNs from Google, and they are built to run
  fast on phones and small computers, so they suit a robot with no graphics card.
- **EfficientNet** is a family of CNNs from Google that comes in many sizes, from
  small and fast to large and accurate, so you can pick one that fits your
  computer.
- **ViT**, the vision transformer, came from Google in 2020, and it showed that a
  transformer, first built for text, also works well on pictures.
- **ConvNeXt** is a CNN from Meta that copied design ideas from transformers, and
  it showed that a CNN built in the modern way can match them.

---

## 6. Where it is used on a robot arm

A classifier is useful on an arm when the question has one answer for the whole
picture, so here is a worked example of exactly that.

A robot arm picks cups from a shelf and puts them in a dish rack. However, the
gripper sometimes closes and misses the cup, and the arm should notice this before
it moves to the rack.

1. A small camera on the wrist points at the gripper fingers.
2. After the gripper closes, the program takes one picture.
3. A classifier with two classes looks at the picture: "holding a cup" and "empty".
4. If "empty" gets the higher score, the arm opens the gripper and tries again.
5. If "holding a cup" gets the higher score, the arm moves to the rack.

To build this, a person records a few hundred pictures of each case, including
different cups, different light and different places on the shelf. Then they
fine-tune a small network, such as a MobileNet, on those pictures.

Other common uses on an arm:

- Checking whether a task worked, for example by asking "is the drawer open or
  closed?"
- Sorting parts into bins by kind, when a camera sees one part at a time.
- Checking the quality of a part, which means answering "good" or "scratched".
- Naming an object that another model has already found, because a detector finds a
  box, and the program can cut out that box and give it to a classifier trained on
  finer classes, such as ten kinds of screw.

---

## 7. What goes wrong

Simple as it is, a classifier can fail in several ways, and each one has a common
fix.

First, it always picks a class, even when none of them fits, so if you show a "mug
or bowl" classifier a photo of a shoe, it still says "mug" or "bowl". The fix is to
add a class such as "something else" and train it on many unrelated pictures.
Instead, you can refuse any answer whose top score is below a chosen number, such
as 0.7, and that chosen number is called a **threshold**.

Second, it can learn the background instead of the object. Suppose every "holding a
cup" picture was taken in the morning and every "empty" picture in the afternoon:
the network might then learn the light rather than the cup. The fix is to vary the
light, the background and the place in both classes when you collect the pictures.

Third, it fails on pictures that look different from its training pictures, so a
classifier trained on clean photos may fail when the camera lens is dirty or the
light is dim. This problem is called a **domain gap**, and the fix is to include
such pictures in training. People also change their training pictures on purpose,
making copies that are darker, blurred or slightly turned, which is called **data
augmentation**.

Fourth, the score is not an honest chance, because a score of 0.95 does not mean
the model is right 95 times out of 100, and networks are often too sure of
themselves. The fix is to test the model on pictures it did not train on, and to
choose the threshold from what you measure there.

Finally, it cannot say where or how many, so if the picture holds two objects the
answer is still one name. When where or how many matters, you need
[object detection](../02_most-used/01_object-detection.md) instead.

---

## 8. Why classification, and what it costs

Now that you have seen what a classifier does and where it fails, this section
answers the four questions for it: what it is, what it does for you, why it rather
than the obvious alternative, and what it costs.

It is a network that gives one name to one picture. So it gives you a yes-or-no
check, or a choice among a few states, from a single picture.

The obvious alternative is a hand-written rule, for example "if more than 500
pixels in the gripper area are white, a cup is there". Rules like this are quick
to write and need no training pictures, but they break when the cup is a
different colour, or when the light changes. A classifier trained on varied
pictures keeps working in those cases. So choose a rule when the scene is
controlled and simple, and choose a classifier when it varies.

The other alternative is a detector, which also names objects and says where they
are. However, a detector needs a box drawn around every object in every training
picture, which takes much longer to label, and it is also bigger and slower. So if
you only need one answer for the whole picture, a classifier is simpler and
cheaper.

The costs are these. You need a few hundred labelled pictures per class, taken in
the conditions the robot will actually meet. Then you also need a computer that can
run the network, although a small classifier runs well without a graphics card.
Finally, you must accept that it will sometimes be wrong, so the robot needs a safe
action for a wrong answer, such as simply trying again.

---

## 9. The written alternative

A trained network is not the only way to answer a yes-or-no question about a
picture, because Book 5 answers some of them with a written rule. [Thresholding
and colour
masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
can check that the gripper holds something, by counting the depth pixels nearer
than the fingertips. [Edges and
contours](../../../05_programming-techniques/05_image-and-point-cloud-processing/03_also-used/01_edges-and-contours.md)
can name the shape of a flat part, such as a triangle or a hexagon, by counting
the corners of its outline. The written rule wins when the scene is controlled
and the answer depends on one thing you can measure, such as a height, a colour
or a number of corners. The classifier wins instead when the answer depends on
how things look in general, such as "scratched" or "good", or when the light and
the objects vary.

---

## 10. Where to read next

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

---

## 11. Using it in Python

The page has explained the backbone, the scores and the fine-tuning that every
other seeing model reuses. This section runs a real classifier, because it is the
shortest piece of model code in the whole book. After reading it you will be able
to get names and scores for a picture in three lines, and you will see why a
classifier alone is rarely enough for a robot arm.

Hugging Face `transformers` has a helper called a pipeline, which puts the
preparation of the picture, the network and the reading of the scores behind one
call.

```python
from transformers import pipeline

classifier = pipeline("image-classification", model="microsoft/resnet-50")

# The answers come back sorted, with the most likely first.
for guess in classifier("part.jpg")[:3]:
    print(guess["label"], round(guess["score"], 3))
```

What the pretrained model gives you out of the box is the 1,000 classes of
ImageNet, which are mostly animals, plants and everyday things. The pipeline also
does the small steps that are easy to get wrong, because it resizes the picture to
224 by 224 pixels, subtracts the mean and divides by the standard deviation that
this model was trained with, turns the scores into numbers that add up to 1, and
sorts them. Those steps are why a wrong answer is so often a preparation mistake
rather than a model mistake, and here you cannot make it.

What you still have to write yourself begins with the fact that a classifier says
nothing about where. It gives one name for the whole picture, so on a robot arm it
is useful only when you have already cut out one object, for example from a box a
detector gave you, or when the camera always sees exactly one part in a fixture.
Cropping the picture to that one object is your code, and so is everything the name
is then used for.

What you have to decide is how many of the sorted guesses to trust and how low a
score you will accept. A classifier always names something, because it must choose
one of its classes, so a picture of a brake disc gets a confident wrong answer
rather than no answer. So you set a score below which you treat the answer as
"unknown". You also decide whether to fine-tune, and for a robot the answer is
almost always yes, because your classes are your own parts and not the 1,000
classes of ImageNet.
