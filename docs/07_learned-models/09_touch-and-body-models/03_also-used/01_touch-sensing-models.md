# Touch sensing models

This page answers one question: how does a robot turn a picture of its finger pad
into facts about what it is touching? To answer that, it explains the sensors that
make such a picture, what a model learns to read from it, how that model is trained,
and where it helps a robot arm.

It is written for a reader who has already read the [overview of this
chapter](../01_overview.md) and the first chapter of this book, especially [how a
model learns](../../01_what-models-are/02_how-a-model-learns.md). You do not need to
know anything about touch sensors. However, you should know what a digital picture
is: a grid of small squares called pixels, each with a number for its brightness.

## Contents

1. [What it is](#1-what-it-is)
2. [The sensor that makes the picture](#2-the-sensor-that-makes-the-picture)
3. [What goes in and what comes out](#3-what-goes-in-and-what-comes-out)
4. [How it works inside](#4-how-it-works-inside)
5. [How it is trained](#5-how-it-is-trained)
6. [Well-known models and tools](#6-well-known-models-and-tools)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What it is

A touch sensing model takes a small picture of a contact and says where the
contact is, what shape it has and how hard it presses.

Here is an everyday example of the same skill. Close your eyes and pick up a pen,
and your fingertip skin bends around the pen. From how it bends, you know the pen is
round, you know roughly where it sits on your finger, and you know how hard you are
pressing. In other words, you did not need to see it.

A robot finger with a tactile sensor gets a similar signal, where "tactile" means to
do with touch, and the sensor reports how its soft surface has bent. So a touch sensing
model is the part that turns that raw signal into the facts you would have known
with your eyes closed.

## 2. The sensor that makes the picture

Before a model can read a tactile picture, something has to make one. Most of the
models on this page work with one kind of sensor, called a **vision-based tactile
sensor**. This is a small camera that films the inside of a soft pad.

![A cut-through of a camera-behind-gel touch sensor, and the picture the camera takes](../../../images/touch-and-body-models/touch-sensing-models/gel-camera-sensor.svg)

The left half of the picture shows the inside of the sensor. The right half shows
the kind of picture its camera takes when a screw presses into the pad.

So the sensor has four parts, and they are listed below from the outside in.

1. A soft pad made of a clear rubbery material called gel. It is a few millimetres
   thick.
2. A thin painted skin on the outside of the gel. The paint stops the camera from
   seeing through to the object, so the camera sees only the shape of the skin.
3. Small coloured lights around the edge. Each one shines across the gel from a
   different side.
4. A small camera underneath, looking up at the skin.

Once an object presses into the pad, the skin bends. A slope that faces one light
looks bright in that light's colour, while a slope that faces away looks dark. So
the camera picture shows the shape of the dent as coloured shading.

The best-known sensors of this kind are **GelSight**, first built at the
Massachusetts Institute of Technology (MIT), and **DIGIT**, a low-cost design from
Meta. Another kind, **TacTip** from the Bristol Robotics Laboratory, uses a soft skin
with small pins on the inside, and the camera watches the pins move. The frameworks
book lists what you can buy, with prices, in
[tactile sensing at the contact](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md#82-tactile-sensing-at-the-contact)
.

Some sensors are not cameras at all, and two other designs are common. For example, a
pressure array is a grid of small pressure sensors, each giving one number, and a
magnetic skin such as AnySkin has tiny magnets in soft rubber, with a chip underneath
that measures how the magnets move. Both of those still produce a grid of numbers, so
the same kind of model can read them.

## 3. What goes in and what comes out

Now that the sensor is described, here is what passes in and out of the model. The
input is one tactile picture, or a short run of them. For a camera-based sensor,
that picture is an ordinary small colour image, while for a pressure array it is a
grid of pressure numbers.

![A grid of tactile numbers going into a small network, and the answers that come out](../../../images/touch-and-body-models/touch-sensing-models/tactile-image-to-answers.svg)

The picture shows a simplified tactile image as a grid of numbers, where each number
says how deep the gel is pressed at that spot. The network reads the whole grid and
gives back the answers.

The outputs a robot arm needs most are these:

- Contact or no contact. Is the pad touching anything at all?
- Where on the pad the contact is. Is the object in the middle of the pad, or near
  the edge?
- The shape of the contact. Is it a flat face, an edge, a corner or a round
  surface?
- The force. How hard is the pad pressed straight in? This is called the **normal
  force**. How hard is it pushed sideways? This is called the **shear force**.
- A height map. For each pixel, how deep is the dent? This gives a small 3D shape
  of the part of the object that touches the pad.

Some models give only one of these answers, while others give several at once.

## 4. How it works inside

The last section listed the answers, and this section says how the model reaches
them. There are two ways to get from the picture to the answers: the first uses no
learning, and the second does.

### 4.1 Without learning: the shape from the shading

Because the coloured shading in the picture follows a simple rule, the depth can be
worked out without any learning at all. The brighter a spot is in the red light, the
more that spot's slope faces the red light, and the same holds for each colour. So
with three lights you can work out the slope at every pixel, and if you add up the
slopes across the picture you get the depth of the dent. This method is called
**photometric stereo**, where "photometric" means measuring light, and "stereo" here
means using more than one view of the light.

However, the method needs a calibration before it can be used. You press a small ball
of known size into the pad and record how each slope looks. After that, it works for
any shape.

GelSight's own software ships a small network that does almost this job, with the same
calibration on a ball, and
[section 6.1](#61-gelsights-own-depth-network-inside-gsrobotics) recommends it for shape
on a gel sensor.

### 4.2 With learning: a network reads the picture

Instead, a neural network can learn the same thing, and more besides. The network
used is usually a **convolutional neural network (CNN)**, which is the kind of
network the [seeing models](../../03_seeing-models/01_overview.md) chapter uses for
ordinary photos. It slides small filters across the picture, looks for simple
patterns such as edges, and then combines them into larger patterns.

The steps are:

1. The camera takes a tactile picture.
2. The model subtracts a picture of the same pad with nothing touching it. What
   is left is only the change caused by the contact.
3. The CNN reads the change and builds up a set of numbers that describe it.
4. A small last part of the network turns those numbers into the answers: contact
   or not, where, what shape, how much force.

In practice you rarely train the whole of such a network yourself. You take the first
part from a model somebody else has already trained, and you train only step 4 on your
own presses, which is what
[section 6.2](#62-an-image-backbone-of-your-own-fine-tuned) recommends. Two models
later in this page are first parts of that kind, trained on tactile pictures rather than
on photographs. [Section 6.4](#64-sparsh-from-meta) covers Sparsh, and
[section 6.5](#65-transferable-tactile-transformers-t3) covers T3, which keeps one shared
middle section and a small separate part for each sensor and each task.

A sensor that gives only a handful of numbers rather than a picture has nothing for a
CNN to slide a filter across. There the whole model is a small one you fit yourself on
those few numbers, and
[section 6.3](#63-a-small-model-on-a-magnetic-skin) recommends that for a magnetic skin
or an array.

### 4.3 Seeing the sideways push

The shading shows how deep the pad is pressed, but it does not show well how hard
the pad is pushed sideways. So for that, many gel sensors have a grid of small black
dots printed on the gel.

![Dots on the gel sitting still, spreading when pressed, and all moving when pushed sideways](../../../images/touch-and-body-models/touch-sensing-models/dots-show-sideways-force.svg)

The picture shows the same grid of dots three times. When nothing touches, the dots
sit on their grid. When something presses straight in, the dots near the contact
spread outwards a little. When something presses and also pushes sideways, the dots
in the contact all move the same way.

A model can track each dot from one picture to the next. Then how far and in which
direction the dots move tells it the sideways force. This is the signal the
[force and slip page](../02_most-used/01_force-and-slip-models.md) uses to catch an
object starting to slide.

## 5. How it is trained

The last section described the model, and this section says where its examples come
from. A touch sensing model learns from examples, and each example is a tactile
picture together with the right answer. So the hard part is getting those right
answers.

For contact shape and height maps, people use the photometric stereo method from
section 4.1 to make the answers. Instead, they may press objects of known shape,
such as balls, cylinders and cubes, into the pad at known places.

For force, people mount the tactile sensor on top of a separate force sensor. Then
they press many objects into it at many angles and record both at once, so the force
sensor gives the right answer for each tactile picture. Thousands of presses is a
normal size for such a set.

A newer way needs no answers at all, and it is called **self-supervised learning**.
The model is given a very large number of tactile pictures with no labels. Then it
learns by solving a made-up puzzle: parts of each picture are hidden, and it must
guess what was hidden. Because it can only do that well by learning what tactile
pictures are like in general, the puzzle teaches it something useful. Afterwards, a
small extra part is trained on a few labelled examples for the task you actually
need. [Where the data comes
from](../../01_what-models-are/05_where-the-data-comes-from.md) explains this idea in
more detail.

There is a second route to large amounts of data, and that is simulation. A tactile
simulator draws the picture the sensor would take for a given object and contact.
Two of them are free to use: TACTO and Taxim. However, the pictures are not
quite the same as real ones, so a model trained only on simulated pictures usually
needs some real ones too.

## 6. Well-known models and tools

This area has far fewer models than the camera side of robotics, and the sensor you own
decides which of the few you can use at all. So this section is organised by hardware. A
camera-behind-gel sensor such as GelSight Mini or DIGIT, a magnetic skin such as
AnySkin, and an array of pressure elements inside a bought hand each lead to a different
answer. For the arrays, and for any sensor nobody has published a model for, the answer
is that you train a small model of your own on a few hundred presses, and here that is
the usual case rather than the exception.

Read the table one row at a time. The left column names the model and says whether a
developer starting today would reach for it. The right column holds everything else, and
it opens with the sensor the model needs, because that is what decides most of this
choice. After that it gives what the model is best at, how big it is, its licence, and
the one case that should make you choose it. A cell says `not stated` where nobody has
published the figure. Where the licence is yours, the model comes out of your own
training run, so no licence restricts it.

| Model | What decides it |
| --- | --- |
| [**6.1 GelSight's depth network**](#61-gelsights-own-depth-network-inside-gsrobotics), most used in 2026 | It needs a camera behind a gel. It is best at a height map of the dent, pixel by pixel. It has 8,834 numbers, counted from its own source, and the licence is GPL-3.0. Pick it when you want shape from a gel sensor. |
| [**6.2 An image backbone of your own**](#62-an-image-backbone-of-your-own-fine-tuned), most used in 2026 | It needs any sensor that gives a picture. It is best at contact place, shape and force from a few thousand presses. ResNet-18 has 11,689,512 numbers, a figure published by torchvision. The model comes out of your own training run, so the licence is yours. Pick it when the answer you need is not one anybody published. |
| [**6.3 A small model on a magnetic skin**](#63-a-small-model-on-a-magnetic-skin), most used in 2026 | It needs AnySkin, eFlesh, or any taxel array. It is best at force and shear from fifteen numbers. It is smaller than a photograph, and the licence is yours. Pick it when your sensor is a skin or an array. |
| [**6.4 Sparsh**](#64-sparsh-from-meta), worth betting on | It needs a DIGIT, a GelSight'17 or a GelSight Mini. It is best at starting from few labels on those three sensors. There is a small backbone and a base one, and their parameter counts are `not stated`. The licence is CC BY-NC 4.0, with no commercial use. Pick it when you own one of those three, and sell nothing. |
| [**6.5 Transferable Tactile Transformers (T3)**](#65-transferable-tactile-transformers-t3), worth betting on | It works with thirteen camera-based sensors. Its strength is that you do not have to train from scratch when the sensor changes. Its size is `not stated`, and the licence is MIT. Pick it in the same case as section 6.4, when you sell something. |

### 6.1 GelSight's own depth network, inside gsrobotics

This is **most used in 2026** by anyone with a GelSight sensor, because it ships with the
sensor and answers the question people buy the sensor for. It turns one tactile picture
into a height map, and it is the part of
[gsrobotics](https://github.com/gelsightinc/gsrobotics), GelSight's own software
development kit, called `Reconstruction3D`. It is not quite the method in
[section 4.1](#41-without-learning-the-shape-from-the-shading). A very small network
takes five numbers for each pixel, its red, green and blue values and its position
across and down the picture, and gives back the slope of the surface there in each
direction. A classical step then integrates all those slopes into a height by solving
Poisson's equation, so the learning replaced the calibration rather than the physics.

You would pick this rather than fine-tuning an image backbone of your own, which is
section 6.2, because the shape is already solved and the trained numbers come in the box.
The network holds 8,834 numbers, counted from the four layer sizes in the repository's
own source, so it runs on an ordinary processor, and nothing you could train on a few
thousand presses would do this job better.

What it costs you is the licence and the sensor. The repository is GPL-3.0, read from its
own licence file and recorded in the frameworks book's
[licence table](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md#9-drivers-ros-2-packages-and-licences),
so linking it into a product obliges you to publish the source of the result. The trained
numbers were learned on GelSight's own gel and lights, so another maker's sensor needs
its own training set. What most often goes wrong is the zero: the first fifty pictures
record what the untouched pad looks like, so if anything is touching it then, every later
height map is measured from the wrong surface.

```python
from utilities.gelsightmini import GelSightMini
from utilities.reconstruction import Reconstruction3D

camera = GelSightMini(target_width=320, target_height=240)  # the size in default_config.json
camera.select_device(0)
camera.start()

depth = Reconstruction3D(image_width=320, image_height=240, use_gpu=False)
depth.load_nn('./models/nnmini.pt')      # the trained numbers that ship with the kit

# The first fifty pictures record the untouched pad. Do not touch it during these.
for _ in range(50):
    depth.get_depthmap(image=camera.update(dt=1 / 25), markers_threshold=(0, 70))

# markers_threshold hides the printed dots, whose darkness is not a dent in the gel.
height_map, contact_mask, slope_x, slope_y = depth.get_depthmap(
    image=camera.update(dt=1 / 25), markers_threshold=(0, 70))
print('height map size and range:', height_map.shape, height_map.min(), height_map.max())
```

gsrobotics opens the sensor, which the computer sees as an ordinary camera, loads the
trained numbers, runs the network over every pixel, integrates the slopes, and masks out
the printed dots. What you supply is the meaning. The height map is in the repository's
own units, so if you need millimetres you press something of a known thickness and work
out the scale, and deciding how many touched pixels count as "touching something" is
yours. GelSight publishes 25 frames per second for the Mini, which makes one picture 40
milliseconds and sets how fast you can act.

### 6.2 An image backbone of your own, fine-tuned

This is also **most used in 2026**, and it is where most people end up, because the
answer they need is rarely one somebody has published. You take a network already trained
on ordinary photographs, replace its last layer with one that gives the numbers you want,
and train that last layer on your own presses. The
[fine-tuning](../../10_making-models-work-on-an-arm/02_most-used/01_fine-tuning.md#2-three-ways-to-fine-tune)
page explains the three ways to do this, and keeping the backbone fixed is the cheapest.

You would pick this rather than Sparsh in section 6.4 for two reasons that have nothing
to do with accuracy. Sparsh forbids commercial use and a torchvision backbone does not.
And Sparsh works with three named sensors, while this works with any sensor that produces
a picture, including a pressure array, which is a small picture of numbers. What you give
up is that the backbone learned from photographs, so it has never seen a tactile picture
and needs more of your presses to make up for that.

What it costs you is a labelled set of presses, which section 5 describes how to make.
What most often goes wrong is that the blank picture is taken once at startup and the gel
then warms up, so every later subtraction is measured from a pad that no longer looks
like that.

```python
import numpy as np
import torch
from digit_interface import Digit
from torchvision.models import ResNet18_Weights, resnet18

sensor = Digit('D20001')                        # the serial number on the sensor
sensor.connect()
blank = sensor.get_frame().astype(np.float32)   # the pad with nothing touching it

# A backbone pretrained on ordinary photos, with a new head of three numbers: where
# on the pad the contact sits, across and down, and how hard it presses.
net = resnet18(weights=ResNet18_Weights.DEFAULT)
net.fc = torch.nn.Linear(net.fc.in_features, 3)
net.eval()

frame = sensor.get_frame().astype(np.float32)
change = (frame - blank) / 255.0                # step 2 of section 4.2
x = torch.from_numpy(change).permute(2, 0, 1).unsqueeze(0)   # colour first, then one batch
with torch.inference_mode():
    across, down, force = net(x)[0].tolist()
```

`digit-interface` gives you the frames, named by the serial number printed on the
sensor's back, so the camera, the lights and the video stream are not your problem. Two
warnings come with it: its licence is Creative Commons Attribution-NonCommercial 4.0,
read from the repository's own licence file, and the repository is a public archive that
nobody will fix. A GelSight needs no such library, because it appears as an ordinary
camera and OpenCV's `cv2.VideoCapture` reads it. Torchvision hands you the backbone with
its trained numbers downloaded, and replacing `net.fc` is the whole of "train a new
head".

What you supply is the training, because the code above only runs the network. Section 5
says how to get the right answers, and you also have to take `blank` again before each
grasp rather than once at startup. What you decide is which three numbers the head gives,
and when a worn gel means the model must be checked again.

### 6.3 A small model on a magnetic skin

This is **most used in 2026** on any sensor that is not a camera, and it is the cheapest
route into touch that exists. A magnetic skin is a rubber sheet with tiny magnets in it
over a board of magnetometers, which are the chips a phone uses to find north. Five of
them give fifteen numbers, three per chip. The open designs are
[AnySkin](https://github.com/raunaqbhirangi/anyskin) and its successor
[eFlesh](https://github.com/notvenky/eFlesh), both MIT, read from their own licence
files, and the frontier chapter's
[section on touch sensing](../../../03_frameworks/08_frontier/05_hardware.md#62-touch-sensing-became-something-you-buy-for-tens-of-dollars)
records the manufactured versions and their prices.

With fifteen numbers there is no backbone to reuse, so the model is a small one you fit
yourself. You would pick this rather than a gel sensor and section 6.1 when you want
force and shear at many places on a hand, and when a replaceable part matters: the
electronics stay on the robot and the skin slips over them, so the part that wears out is
the cheap part.

What it costs you is shape. Fifteen numbers tell you how hard and in which direction
something presses, and not whether it is an edge or a corner. The reading also moves as
the skin warms up, so you have to take a fresh untouched reading often, and every skin is
a little different, so a model fitted on one is not safe on the next without a reference
press.

```python
import numpy as np
from anyskin import AnySkinBase
from sklearn.linear_model import Ridge

# Five magnetometer boards, three numbers each, over the port the skin is plugged in on.
skin = AnySkinBase(num_mags=5, port='/dev/ttyACM0', temp_filtered=True)

# The untouched reading, averaged over 100 samples. Retake this often, not once.
baseline = np.mean([skin.get_sample()[1] for _ in range(100)], axis=0)

# Your own recording: for each press, the fifteen numbers and where it was pressed.
presses = np.load('skin_presses.npy') - baseline   # shape (number of presses, 15)
places = np.load('skin_places.npy')                # shape (number of presses, 2), in mm

model = Ridge().fit(presses, places)   # fifteen numbers in, a place on the skin out

_, reading = skin.get_sample()         # get_sample gives a timestamp and the numbers
print('pressed at, in mm:', model.predict((reading - baseline).reshape(1, -1)))
```

The library does the serial port and the message framing, and with `temp_filtered=True`
it drops each chip's temperature reading, so the fifteen numbers are the ones you want
and nothing else. `Ridge` is ordinary linear regression with a penalty that keeps the
fitted numbers small, which is the right first model for fifteen inputs and a few hundred
presses.

What you supply is the two recordings, and that means a rig: you have to press the skin
at places you know, which in practice means mounting it under the robot and letting the
arm's own position be the answer. What you decide is how often to retake the baseline,
and whether a straight line is enough, because a press near the edge of the skin behaves
differently from one in the middle.

### 6.4 Sparsh, from Meta

Sparsh is **worth betting on** rather than most used, because one model that works across
many sensors is the direction the field is going, and this one is held back by its licence
and by a measured failure rather than by its idea. It is a family of self-supervised touch
models from Meta's Fundamental AI Research group with Carnegie Mellon University and the
University of Washington, published in [October 2024](https://arxiv.org/abs/2410.24090).
It was trained on more than 460,000 unlabelled tactile pictures by hiding parts of a
picture and asking the model to fill them in, which is the idea section 5 describes. It
supports DIGIT, GelSight'17 and GelSight Mini, and the repository also carries TacBench,
six tasks that include force, slip, object pose, grasp stability and recognising
textiles. The grasp stability task runs on the recordings of
[Calandra and colleagues, 2017](https://arxiv.org/abs/1710.05512), who put a GelSight on
each finger of a gripper, collected more than 9,000 grasping trials, and showed that
camera and touch together predict a grasp better than either alone. That 2017 result is
the one everything else on this page assumes, and its recordings are still the way to
measure a model of your own without collecting anything.

You would pick this rather than the backbone of your own in section 6.2 to save labels,
because it starts from numbers learned on tactile pictures instead of on photographs. Its
paper reports that the self-supervised start beat training end to end for one task and
one sensor by 95.1 per cent on average across TacBench.

What it costs you is checkable, and worth checking. The licence in the repository's own
`LICENSE.md` is Creative Commons Attribution-NonCommercial 4.0, which forbids commercial
use and covers the weights as well as the code. The repository is a public archive, read
only since February 2025. Its own pretraining used eight A100 80GB graphics cards, so
only the head on top is realistically yours to train. And it does not travel between
sensors yet: a study in [September 2026](https://arxiv.org/abs/2609.08673) reports a
frozen classifier on Sparsh scoring 6.86 per cent on a sensor it was not trained on,
rising to 87.09 per cent once a tenth of the new sensor's recordings are labelled. That is
the number to remember before buying a sensor, and it is why section 6.5 exists.

```bash
# The normal and shear field, live, on one GelSight Mini. The video id comes from
# `ls -l /dev/video*`, because the sensor appears to the computer as a webcam.
python demo_forcefield.py +experiment=downstream_task/forcefield/gelsight_dino \
    paths=${YOUR_PATHS} paths.output_dir=${YOUR_PATH}/checkpoints/ \
    test.demo.gelsight_device_id=0

# Train a head of your own on your own labelled presses, backbone frozen.
python train_task.py --config-name=experiment/downstream_task/${EXPERIMENT} \
    paths=${YOUR_PATHS} wandb=${YOUR_WANDB}
```

The repository gives you the backbone, the training loop, and readers for its own
recordings, which it releases for the force, slip and pose tasks. What you supply is a
`paths` file saying where your data and checkpoints live, the downloaded weights, and,
past the demo, your own labelled presses in the layout its readers expect.

### 6.5 Transferable Tactile Transformers (T3)

This is also **worth betting on**, and it is the better bet of the two for most readers,
because its licence does not stop you using it. T3 comes from MIT's Computer Science and
Artificial Intelligence Laboratory, published in
[June 2024](https://arxiv.org/abs/2406.13640). Its arrangement is the interesting part:
one shared middle section, a small separate part at the front for each sensor, and a small
separate part at the back for each task. So the middle learns from every sensor at once,
while the front absorbs the difference between one gel and another. It was trained on a
dataset the authors published, Foundation Tactile, which gathers over 3 million tactile
pictures from 13 sensors and 11 tasks into one format.

You would pick this rather than Sparsh in section 6.4 for three reasons. Its
[licence is MIT](https://github.com/alanzjl/t3), read from the repository's own licence
file, so you may use it in a product. It covers thirteen sensors rather than three, so an
unusual sensor has a better chance of being one of them. And its paper reports zero-shot
transfer working for some sensor and task pairings, which is the problem the September
2026 study measured on Sparsh.

What it costs you is maturity. It is one research group's repository rather than a
maintained library, the weights and the dataset are hosted away from the code, and the
size of the shared middle is not published. Its strongest published result is a task
success rate 25 per cent higher than a tactile encoder trained from scratch, on inserting
multi-pin electronics, so treat it as evidence that the idea works rather than as a
number for your own job.

```bash
git clone https://github.com/alanzjl/t3 && cd t3 && pip install -e .

# Fine-tune on your own sensor and task, with the shared middle section frozen so
# only the small sensor and task parts learn.
python scripts/train_nn.py network=finetune_exp_cls datasets=[your_dataset] \
    train.finetune_from=/path/to/checkpoint.pth train.freeze_trunk=true
```

The repository gives you the arrangement, the training loop and the readers for Foundation
Tactile. What you supply is a file in its `configs/datasets/` folder describing your own
recordings, and the downloaded checkpoint. What you decide is which existing sensor part
your sensor is closest to, because starting from a part trained on a similar gel is the
whole reason to use this rather than section 6.2.

### 6.6 How to choose

Start from the sensor, not from the model. If you own a gel sensor with a camera behind
it, use section 6.1 for shape, because nothing you train will beat it at that job. If you
own anything else, or need an answer that is not a height map, fine-tune a backbone of
your own with section 6.2 on a few thousand presses. Those two cover most readers.

Four things change that.

- **You want force or slip rather than shape, and you own a DIGIT, a GelSight'17 or a
  GelSight Mini.** Then section 6.4 reaches a usable answer from far fewer labelled
  presses, as long as you sell nothing.
- **The same, but you sell something, or your sensor is an unusual one.** Then section
  6.5, which is MIT and was trained across thirteen sensors.
- **Your sensor is a skin or an array of elements rather than a camera.** Then section
  6.3, and expect force and shear rather than shape.
- **You want the object's whole shape and position while a hand turns it, rather than
  facts about one contact.** Then
  [NeuralFeels](https://github.com/facebookresearch/neuralfeels) (Meta, 2024, MIT), which
  joins touch with a camera to rebuild the object as the hand moves it, and which the
  [perception book](../../../02_perception/02_object-perception/02_sensors.md#25-models)
  describes.

Two tools are worth knowing although they are not models. TACTO and Taxim, both MIT, draw
the picture a sensor would take for a given contact, so you can build and test everything
around the model before a sensor arrives, as section 5 explains.

One thing should not change your choice, and it is the number in section 6.4. A tactile
model loses almost all of its accuracy on a sensor it was not trained on, and the recovery
is a labelling job. So decide which model you intend to use before you buy the sensor, and
not the other way round.

## 7. Where to read next

In this chapter:

- [Force and slip models](../02_most-used/01_force-and-slip-models.md) use the moving dots from
  section 4.3 to catch an object starting to slide.
- [Collision and failure detection](../02_most-used/02_collision-and-failure-detection.md) covers
  the failures that a tactile sensor cannot see.
- The [overview](../01_overview.md) compares all four kinds.

In this book:

- [Image classification](../../03_seeing-models/03_also-used/01_image-classification.md) explains
  how a CNN reads an ordinary picture. A tactile picture is read the same way.
- [Grasp quality models](../../05_grasp-models/03_also-used/02_grasp-quality-models.md) score a
  grasp before the fingers close. Touch models check it after.

In the other books:

- [Measuring by
  touch](../../../02_perception/02_object-perception/02_sensors.md#2-measuring-by-touch)
  in the perception book covers what touch can and cannot measure.
- [Tactile sensing at the
  contact](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md#82-tactile-sensing-at-the-contact)
  covers the sensors you can buy.
