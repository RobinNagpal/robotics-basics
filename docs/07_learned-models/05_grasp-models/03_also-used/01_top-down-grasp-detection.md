# Top-down grasp detection

This page is about the simplest kind of grasp model, which looks at one picture
taken from above and draws rectangles on that picture. Each rectangle says where
the two jaws of a gripper should close. The gripper then comes straight down and
closes there.

So the page answers these questions, one section at a time. What does such a model
take in, and what does it give back? How does it work inside, and what was it
trained on? Which real models do this, and when is this kind the right choice
rather than the wrong one?

It is for a reader who has read the [grasp models overview](../01_overview.md), and
who already knows what a pixel is and what a depth picture is. Both of those are
covered by the [camera basics](../../../02_perception/01_camera/01_basics.md) page
in Book 2. The page
[inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md#4-convolutional-layers-small-pattern-detectors)
explains the convolutional layers that this kind of model is built from.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [Where this is going](#6-where-this-is-going)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What it is

Since the introduction called this the simplest kind of grasp model, this section
says what it actually produces. A top-down grasp detector draws grasp rectangles on
a picture taken from above, and nothing else.

Imagine you look down at a table from a ladder, where you see a mug from the top as
a ring with a handle sticking out. Someone asks you to show where to pinch the mug
with a pair of tongs. So you draw a short line across the mug, with a mark at each
end where the tongs touch. That drawing is all a top-down grasp detector gives. It
draws that kind of mark on the picture, many times over, and gives each one a
score.

The word **detection** is borrowed from
[object detection](../../03_seeing-models/02_most-used/01_object-detection.md),
because the two jobs have the same shape. An object detector finds objects in a
picture and draws a box around each one. That means a grasp detector finds grasps
in a picture and draws a rectangle for each one, in exactly the same way.

---

## 2. What goes in and what comes out

Now that the answer is a rectangle, it is worth being exact about the numbers on
each side. The input is one **depth picture** taken by a camera that looks straight
down. Each pixel of a depth picture holds a distance from the camera rather than a
colour. Because a tall object is close to the camera, its pixels hold small
numbers, while the table is further away and its pixels hold larger numbers. Some
models also take the ordinary colour picture, but many use depth alone.

The output is a list of **grasp rectangles**, where a grasp rectangle is a
rectangle drawn on the picture with a jaw at each short end. Each rectangle
therefore carries three pieces of information about the grasp.

- The **centre**: the pixel where the middle of the gripper should go, as an `x`
    and a `y` on the picture.
- The **angle**: how far the gripper should turn around the up-down line before it
    closes.
- The **opening width**: how far apart the jaws should be just before they close.

That is four numbers in all, because the centre is two of them: `x`, `y`, angle and
width. A fifth number, how far down the gripper should go, is read from the depth
picture at the centre pixel. The direction the gripper comes from is not a number
at all, since it is always straight down, along the line the camera looks.

![A grasp rectangle seen from above and from the side](../../../images/grasp-models/top-down-grasp-detection/grasp-rectangle.svg)

On the left are the four numbers drawn on a picture of a mug. On the right is the
same grasp seen from the side, where the camera looks down and the gripper comes
down along the same line.

Most models also give a **score** for each rectangle, which is a number between 0
and 1. A high score means the model thinks a grasp there is likely to hold. So the
robot usually tries the rectangle with the highest score.

---

## 3. How it works inside

Since the last section described the rectangles that come out, this section
describes how they are produced. There are two main ways to build this kind of
model, and one variation on the newer of the two. The older way finds one rectangle
for the whole picture, while the newer way paints an answer onto every pixel
instead. The variation scores a grasp at every pixel rather than painting one. Every
model named below is also in section 5, which says which of them to use.

### One rectangle per picture

The earliest models of the older way looked at many small patches of the picture,
one at a time, and asked a network "is there a good grasp here?" This was slow,
because the picture has thousands of patches. Lenz, Lee and Saxena's patch
classifier worked that way, and
[section 5.5](#55-lenz-lee-and-saxenas-patch-classifier) describes it. A later model
looked at the whole picture once and gave back the four numbers of one rectangle
directly, which was Redmon and Angelova's detector in
[section 5.4](#54-redmon-and-angelovas-single-pass-detector). That was fast, but it
could only give one grasp per picture. Both models are named here because they are
the clearest way to see where this kind came from, and section 5 marks both of them
as historical rather than as models to install.

### A map for every pixel

Instead of one answer per picture, the newer way gives an answer for every pixel at
once, and it works in three steps.

1. The depth picture goes into a **convolutional neural network (CNN)**, which is a
    network built from small pattern detectors that slide across the picture. The
    [inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md#4-convolutional-layers-small-pattern-detectors)
    page explains how they work.
2. The network gives back three new pictures, each the same size as the input, and
    these are called **maps**.
    - The **quality map** holds, for each pixel, how good a grasp centred on that
      pixel would be.
    - The **angle map** holds, for each pixel, which way the jaws should close.
    - The **width map** holds, for each pixel, how far the jaws should open.
3. A short piece of ordinary code finds the pixel with the highest quality and then
    reads the angle and the width at that same pixel. Those three values, plus the
    pixel's own position, are the grasp.

![The depth picture and the three maps the network paints](../../../images/grasp-models/top-down-grasp-detection/three-maps.svg)

The network fills in a quality, an angle and a width for every pixel in one pass,
and the red cross marks the best pixel, which is in the middle of the mug.

It is worth being exact about what an answer for every pixel means, because it is
the idea this whole family turns on. A 300 by 300 depth picture has 90,000 pixels.
The quality map is a picture of the same size, so it holds 90,000 numbers, one for
every pixel of the input, and the number at a pixel answers one question: how well
would a grasp centred on this pixel hold? The angle map and the width map hold
90,000 numbers each, in the same way. Nothing inside the network chooses a grasp.
The network fills in the whole table of answers, and ordinary code reads the largest
one afterwards.

That is also why the search disappeared. The patch classifier searched because it
could answer only one question per run, so covering 90,000 possible centres meant
running it 90,000 times, and the patches it cut out overlapped almost completely, so
nearly all of that work was the same work done again. A convolutional network does
the overlapping work once. Its small pattern detectors slide across the whole
picture, and what they compute at one place is reused by every answer that needs it,
so one pass fills every cell of all three maps. The search was not replaced by a
cleverer search. It was removed by arranging for every candidate's answer to come
out of the same pass.

Because the network generates a grasp for every pixel rather than checking grasps
one at a time, this design is called **generative**. Its big advantage is speed,
since one pass through a small network gives every possible grasp in the picture. A
model this fast can run again while the arm is moving, so the grasp can follow an
object that is pushed or slides. GG-CNN and GR-ConvNet are both built this way, and
[section 5.1](#51-gg-cnn-the-small-network-that-can-run-on-every-frame) and
[section 5.2](#52-gr-convnet-the-same-three-maps-from-a-larger-network) recommend
them.

### A score for every pixel, and a height as well

This variation starts from a scorer rather than from a map painter. A small network
that gives one proposed grasp a score can be run as a convolution over the whole
depth picture, and then one pass scores a grasp at every fourth pixel and at each of
16 different gripper heights. The answer is the best pixel, angle and height
together, rather than a height read out of the depth picture afterwards.
FC-GQ-CNN works this way, and
[section 5.3](#53-fc-gq-cnn-the-dex-net-top-down-policy) says when to choose it. The
scorer it is built from is a kind of model in its own right, and the
[grasp quality models](02_grasp-quality-models.md) page describes that kind.

---

## 4. How it is trained

Because the maps described above are not obvious from the picture alone, the model
has to learn them from pictures in which people or programs have already marked
good grasps.

A **grasp dataset** here is a set of depth pictures, each with a list of good grasp
rectangles drawn on it. During training the network sees a picture, paints its
three maps, and is told how far its maps are from the marked rectangles. Then it
changes its weights a little to be less wrong next time, and the
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md) page
explains this loop in full. Since those marked rectangles have to come from
somewhere, two datasets are used more often than any others.

- The **Cornell grasping dataset** has under a thousand pictures of about 240
    everyday objects, and people drew the good and bad rectangles by hand. It is
    small, but most early models were tested on it.
- The **Jacquard dataset** has more than 50,000 pictures of about 11,000 objects.
    The pictures were made in a simulator, and the grasps were tested in the
    simulator too, so no person drew them at all.

These datasets are small compared with the ones that other kinds of model use.
That is possible because the task itself is narrow, since the network only has to
learn which shapes in a depth picture two jaws can close around and nothing more.

To make the data go further, the pictures are turned, shifted and cropped during
training. This is because a mug turned by 30 degrees is still a mug, and its good
grasps turn with it. Reusing one picture many times in this way is called **data
augmentation**.

---

## 5. Well-known models

So far this page has described the method. This section names the models that
implement it, so that you can choose one and start work instead of reading five
papers first. The last sub-section is a short rule for choosing, and a reader in a
hurry can read only that.

Read the table one row at a time. The left column names the model, the year it was
published and how current it is. The right column holds everything else: what the
model is best at, how many weights it has, the licence on its code, and the one
condition that should make you choose that row rather than another. The weights are
counted because that number decides whether the model runs on a computer with no
graphics card. Each licence is the licence on the code, and Book 3's
[models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md#2-planar-models-a-grasp-is-a-rectangle)
read every one of them from the project's own licence file in September 2026.

| Model | What decides it |
| --- | --- |
| [**GG-CNN**](https://github.com/dougsm/ggcnn) (2018), most used in 2026 | It is best at running many times a second on a small computer. It has 62,420 weights, and its code licence is BSD-3-Clause. Pick it when the arm has to keep looking while it reaches. |
| [**GR-ConvNet**](https://github.com/skumra/robotic-grasping) (2020), most used in 2026 when depth is not enough | It is best at reading colour and depth together. It has 1,900,900 weights, and its code licence is BSD-3-Clause. Pick it when a depth camera alone sees your objects badly. |
| [**FC-GQ-CNN**](https://github.com/BerkeleyAutomation/gqcnn) (2019), historical | It is best at choosing the gripper's height as well as the pixel. Its size in weights is `not stated`, and its code licence is a University of California Regents grant for education, research and not-for-profit use only. Pick it when you are doing research and want the sampler and the search as well as the network. |
| **Redmon and Angelova's detector** (2015), historical | It is best at nothing you would use today. Its size in weights is `not stated` and its licence is `not stated`. Never pick it, and read the paper instead to see where the single-pass idea came from. |
| **Lenz, Lee and Saxena's detector** (2015), historical | It is best at nothing you would use today. Its size in weights is `not stated` and its licence is `not stated`. Never pick it, and read the paper instead to see what the first deep version cost. |

The two 2015 rows are in the table because this page would be dishonest without
them, not because you should install them.

### 5.1 GG-CNN, the small network that can run on every frame

**Most used in 2026** of the models on this page, because it is the smallest of
them, its licence lets you sell what you build, and it installs from ordinary Python
packages with no compiled extensions.

Size xs, a laptop, BSD-3-Clause.

GG-CNN is the generative grasping convolutional neural network. Douglas Morrison,
Peter Corke and Jürgen Leitner published it at the Robotics: Science and Systems
conference in 2018, in a paper called
[Closing the Loop for Robotic Grasping](https://arxiv.org/abs/1804.05172). It takes
one 300 by 300 depth picture and paints the quality, the angle and the width maps
that section 3 described. The [repository](https://github.com/dougsm/ggcnn) also
holds a second and slightly larger version called GG-CNN2.

The one idea GG-CNN is built on is that a grasp should be read off the picture
rather than searched for. The paper calls it a one-to-one mapping from the depth
picture to the grasp: every pixel of the input has its own cell in each output map,
and no candidate grasp is ever proposed, scored or thrown away.

Inside, the network is six layers and nothing else. Three convolutions shrink the
picture, with strides of 3, 2 and 2, so by the middle of the network the picture is
twelve times smaller in each direction. Three transposed convolutions then grow it
back to the size it came in at, a transposed convolution being the growing twin of a
convolution: where one turns several neighbouring pixels into one, the other turns
one pixel into several. Four small output layers read the last grown picture. One
gives the quality map, one the width map, and the other two give the angle, because
the network does not output an angle at all. It outputs the cosine and the sine of
twice the angle. A parallel-jaw grasp looks the same if you turn it by half a turn,
so a single angle runs out of range and jumps back to the other end as the jaws turn
past that limit, and a network cannot learn a value that jumps, while a cosine and a
sine move smoothly all the way round. The code after the network turns the pair back
into an angle, and GR-ConvNet in the next sub-section uses the same pair for the
same reason. The rest of GG-CNN is as plain as a network gets: the widest layer
carries 32 channels, nothing skips from the shrinking half to the growing half, and
there is no normalisation anywhere.

What that buys is one pass over a tiny network, which finishes in time for the next
camera frame, and that was the problem the paper set out to solve. What it costs is
detail. Because the picture in the middle of the network is twelve times smaller
and nothing skips past that middle, the maps come back blurred, which is why the
library smooths all three maps
before it looks for the peak. The deeper cost is that each pixel gets one angle and
one width. Where two different grasps would both work at the same centre, the
network cannot hold both, and a value trained towards two good angles settles
somewhere between them, which is not a good angle at all.

On a robot arm the difference shows up when the object moves. If the gripper nudges
the mug on the way in, or the part is on a belt that creeps, GG-CNN can look again
on every camera frame and move its target with the object. FC-GQ-CNN in
[section 5.3](#53-fc-gq-cnn-the-dex-net-top-down-policy) answers a richer question,
but it pushes sixteen copies of the picture through its network for one answer, so
by the time it replies the mug has moved.

The obvious alternative is GR-ConvNet in the next sub-section, which paints the same
three maps from a much larger network. Choose GG-CNN instead when the arm has to
keep looking while it reaches. The two models answer the same question in the same
form, so the whole of the choice is how much machinery sits between the picture and
the answer, and GG-CNN's is small enough to answer again before the camera sends the
next frame. The table above gives both weight counts if you want to see how far
apart they are.

What it costs you is mostly age. The repository was written for Python 3.6 on Ubuntu
16.04 and was last pushed in July 2020, so the install takes more work than the model
does. Nothing in it is a compiled extension, so that install is still possible on a
current machine. The thing that most often goes wrong is the depth picture itself,
because the network wants one channel of 300 by 300 pixels holding metres, and if
you hand it millimetres or a 480 by 640 picture it still answers and the answer
means nothing.

GG-CNN is not on the Python package index. You clone the repository and download
the released weights, which hold the whole saved model, so no code rebuilds the
network. The two imports below name folders inside the clone.

```python
import torch
from models.common import post_process_output              # in the cloned repository
from utils.dataset_processing.grasp import detect_grasps

net = torch.load("ggcnn_weights_cornell/ggcnn_epoch_23_cornell")
net.eval()

with torch.no_grad():
    # depth has shape (1, 1, 300, 300): one 300 by 300 depth picture, in metres
    pos, cos, sin, width = net(depth)

# The network does not output an angle. It outputs the cosine and the sine of twice
# the angle, and this call turns that pair back into an angle. It also smooths all
# three maps, which stops the peak jumping between neighbouring pixels.
q_img, ang_img, width_img = post_process_output(pos, cos, sin, width)

# Finds the peaks of the quality map and reads the angle and the width at each peak.
grasp = detect_grasps(q_img, ang_img, width_img=width_img, no_grasps=1)[0]
print(grasp.center, grasp.angle, grasp.length)   # pixel, radians, opening in pixels
```

The library gives you the network and the two steps around it that you would
otherwise get wrong, which are the angle arithmetic and the peak finding. What you
have to supply is the cropping and resizing to that exact shape, the conversion from
the winning pixel to a gripper pose in the robot's own frame, and the cut-off on the
quality map. That last one is a real decision, because `detect_grasps` accepts peaks
above 0.2 by default, and a low cut-off means the model always answers even when
nothing in the picture can be grasped.

### 5.2 GR-ConvNet, the same three maps from a larger network

**Most used in 2026** when depth alone is not enough, because it is the only model
on this page that reads the colour picture as well and still carries a licence you
can ship.

Size xs, a laptop, BSD-3-Clause.

GR-ConvNet is the generative residual convolutional neural network. Sulabh Kumra,
Shirin Joshi and Ferat Sahin published it in 2020, from the Multi-Agent Bio-Robotics
Laboratory at the Rochester Institute of Technology, in a paper called
[Antipodal Robotic Grasping using Generative Residual Convolutional Neural
Network](https://arxiv.org/abs/1909.04810). It paints the same quality, angle and
width maps as GG-CNN, from a 224 by 224 input with four channels, which are red,
green, blue and depth.

The one idea GR-ConvNet is built on is that the three maps do not have to come from a
small network, and that the picture they are painted from does not have to be depth
alone. Its paper describes the input as an n-channel picture, which means that
the first layer is written to take as many channels as you give it, and the released
weights take four.

Inside, it keeps GG-CNN's shape and changes every proportion of it. Its three
shrinking convolutions use strides of 1, 2 and 2, so the picture in the middle is
four times smaller in each direction rather than twelve. Between the shrinking and
the growing halves sit five residual blocks of 128 channels. A residual block is a
pair of convolutional layers that adds its own input back to its output, and the
addition is what lets a stack this deep train at all, because it gives each block an
easy path to pass its input straight through, so the block only has to learn the
change it wants to make. Every layer is followed by batch normalisation, which
rescales the numbers passing through so that they stay in a useful range, and
dropout sits in front of the outputs. Those outputs are the same four maps as
GG-CNN's, with the angle arriving as the same cosine and sine pair.

What that buys is detail and colour. Shrinking by four instead of twelve, and
putting most of the weights into a middle that never loses more resolution, means
the peak of the quality map lands where the grasp is rather than near it. Reading
colour means the model can see what depth cannot. What it costs is that the colour
has to be there and has to be right. You must give it a colour picture and a depth
picture of the same moment, lined up pixel for pixel, which a depth camera does only
if you ask it to align its two streams, and a model that learned on one dataset's
colours has one more thing about your scene that can be unfamiliar. It is also no
longer the model you run on every camera frame without a graphics card.

On a robot arm the difference shows up on anything a depth camera cannot see. A
paper label, a plastic lid, a knife or a clear bottle lying on a flat table is, in
depth, the table: the distance is the same everywhere, so GG-CNN's quality map has
no peak to find. GR-ConvNet also has the colour picture, where the edges of those
objects are plain, and it puts a rectangle across them. Turn the scene around, into
a bin of identical parts all of one colour, and the colour channels say nothing that
depth has not already said, and GG-CNN's speed is the only difference left.

The obvious alternative is GG-CNN. Choose GR-ConvNet instead when a depth camera
sees your objects badly, because a flat object lying on a flat table is almost
invisible in depth and obvious in colour. Its
[repository](https://github.com/skumra/robotic-grasping) also commits its trained
weights into Git rather than attaching them to a release, so they are there as soon
as you clone it. Those two differences are the whole case for it.

What it costs you is the install and one mistake about units. It was last pushed in
November 2021, so it has the same ageing install as GG-CNN, although its
requirements file pins nothing and names no compiled extension. The thing that most
often goes wrong is the width map, because the library divides the training widths
by 150 and multiplies them back afterwards, so the widths that come out are in
pixels of a 224 by 224 crop and not in millimetres of your gripper.

The code below is the shortest path through the repository's own `run_offline.py`.

```python
import numpy as np
import torch
from PIL import Image

from inference.post_process import post_process_output
from utils.data.camera_data import CameraData
from utils.dataset_processing.grasp import detect_grasps

# The weights are committed in the clone, so there is nothing to download.
net = torch.load("trained-models/cornell-randsplit-rgbd-grconvnet3-drop1-ch32/epoch_19_iou_0.98")
net.eval()

rgb = np.array(Image.open("scene_rgb.png"))
depth = np.expand_dims(np.array(Image.open("scene_depth.tiff")), axis=2)

# CameraData crops both pictures to the centred 224 by 224 square the network
# expects, normalises them, and stacks them into the four channels.
img_data = CameraData(include_depth=True, include_rgb=True)
x, depth_img, rgb_img = img_data.get_data(rgb=rgb, depth=depth)

with torch.no_grad():
    pred = net.predict(x)       # a dict with the keys pos, cos, sin and width

q_img, ang_img, width_img = post_process_output(
    pred["pos"], pred["cos"], pred["sin"], pred["width"])
grasp = detect_grasps(q_img, ang_img, width_img=width_img, no_grasps=1)[0]
```

The library does the cropping and the normalising for you, which is the part GG-CNN
leaves to you, and `CameraData` is where you say what size your camera gives. What
you have to supply is a colour picture and a depth picture of the same scene, taken
at the same moment and already lined up pixel for pixel, which a depth camera will
do only if you ask it to align its two streams. Everything after the grasp is the
same work as in the previous sub-section.

### 5.3 FC-GQ-CNN, the Dex-Net top-down policy

**Historical.** It is kept here because it explains how the current models work and
because it is the top-down model people ask about most, but its licence forbids
commercial use and its code needs TensorFlow 1.

Size not stated, a laptop, and a University of California Regents licence for
education, research and not-for-profit use only.

FC-GQ-CNN is the fully convolutional grasp quality convolutional neural network,
published in 2019 by the AUTOLAB group at the University of California, Berkeley, as
part of Dex-Net 4.0. It started as a scorer rather than a detector. Dex-Net 2.0 cut
a 96 by 96 patch around one proposed grasp and gave that grasp a single number,
which the [grasp quality models](02_grasp-quality-models.md) page describes in full.
The fully convolutional version runs that same small network as a convolution over
the whole depth picture, so one pass scores a grasp at every fourth pixel and at
each of 16 different gripper heights.

The one idea it is built on is that you can keep the scorer and delete the search.
The scorer answered one question: given this patch and this gripper height, does the
grasp hold? Running it over a scene meant proposing patches and searching through
them. FC-GQ-CNN rewrites the scorer so that one pass over the whole picture answers
that question everywhere at once, and the search becomes a lookup in a table the
network has filled in.

The rewrite is the part worth understanding, because it is not the design GG-CNN
uses. A patch scorer ends in fully connected layers, which accept an input of one
fixed size only, and that fixed size is what forces the patch. Those layers can be
rewritten as convolutions that compute exactly the same thing, and a network made
only of convolutions does not care how large the picture is, so the same weights now
turn a whole depth picture into a grid of scores. That grid is coarser than a pixel,
because the shrinking inside the network leaves one answer for every fourth pixel in
each direction. The angle is not a number this network predicts either. Its last
layer has one output channel for each slice of a half turn, so the angle is whichever
channel scored highest, and the number of channels is the finest angle it can say.

The gripper's height is handled outside the network, and this is the part nothing
else on the page does. The code looks at the depth picture, takes the nearest point
on an object and the furthest point in the scene, and cuts the range between them
into sixteen heights. It then copies the depth picture sixteen times, once per
height, and sends all sixteen copies through the network together. What comes back
is one score for every combination of a row, a column, an angle slice and a height.
The grasp is the combination that scored best, so the height was chosen by a score
rather than read off the surface the camera happened to see.

What that buys is the height and an honest number. The score was trained against
Dex-Net's labels, so it estimates the chance that the grasp holds, rather than
reproducing a quality that somebody drew on a picture. What it costs is sixteen
passes instead of one, a grid that answers every fourth pixel instead of every
pixel, an angle no finer than the output channels allow, and a network built for one
picture size. On a robot arm the case where all that pays is a grasp below the
surface: a mug held around its body under the rim, or a part sitting in a recess.
GG-CNN reads the height at the winning pixel, which is the height of the rim, so its
jaws close in the air above the body. FC-GQ-CNN has a height slice down at the body
and a score for it, so it can choose it.

The obvious alternative is GG-CNN, which also answers for every pixel in one pass.
Choose FC-GQ-CNN instead for one reason, which is the height. Everything else about
it is harder than GG-CNN, so the height has to be worth the trouble, and it is worth
the trouble only when the surface the camera sees is not where you want the jaws.

What it costs you is everything else. The code pins TensorFlow at 1.15 or below and
its own packaging names Python 3.5 to 3.7, so it needs an environment of its own.
Its own installer looks for an NVIDIA card and falls back to the processor-only
TensorFlow when it finds none, which is why a laptop is enough to run it, though
sixteen passes on a laptop are sixteen times the wait. Commercial use needs a
separate agreement from Berkeley's technology licensing office, whose contact the
licence names. The thing that most often goes wrong is the picture size, because
the fully convolutional network is built for one fixed height
and width, and you have to write your own picture's size into the configuration
before the policy is created.

The library is [gqcnn](https://github.com/BerkeleyAutomation/gqcnn), which you clone
rather than install, and the code below is the shortest path through its own
`examples/policy.py`.

```python
import numpy as np
from autolab_core import (CameraIntrinsics, ColorImage, DepthImage, RgbdImage,
                          YamlConfig)
from gqcnn.grasping import FullyConvolutionalGraspingPolicyParallelJaw, RgbdImageState

config = YamlConfig("cfg/examples/fc_gqcnn_pj.yaml")   # names the weights folder
camera_intr = CameraIntrinsics.load("data/calib/primesense/primesense.intr")

depth_im = DepthImage(np.load("data/examples/clutter/primesense/depth_0.npy"),
                      frame=camera_intr.frame)
depth_im = depth_im.inpaint(rescale_factor=0.5)        # fills the holes in the depth
color_im = ColorImage(np.zeros([depth_im.height, depth_im.width, 3], np.uint8),
                      frame=camera_intr.frame)         # this model ignores colour

# The network is built for one picture size, so tell it yours before it is created.
config["policy"]["metric"]["fully_conv_gqcnn_config"]["im_height"] = depth_im.height
config["policy"]["metric"]["fully_conv_gqcnn_config"]["im_width"] = depth_im.width

state = RgbdImageState(RgbdImage.from_color_and_depth(color_im, depth_im),
                       camera_intr,
                       segmask=depth_im.invalid_pixel_mask().inverse())

action = FullyConvolutionalGraspingPolicyParallelJaw(config["policy"])(state)
print(action.grasp.center, action.grasp.angle, action.grasp.depth, action.q_value)
```

The library gives you a finished answer rather than three maps, which is the real
difference from the two models above. `action.grasp` already carries a centre, an
angle and a depth in metres, and `action.q_value` is the score the network gave it.
What you have to supply is the camera's intrinsic parameters in Berkeley's own
`.intr` file format, a depth picture in metres, and a mask saying which pixels are
objects. The code above uses the pixels with valid depth as that mask, which works
on a clean table and not in a bin. You also have to set `gripper_width` in the
configuration to your gripper's opening in metres, because the shipped value is
0.05.

### 5.4 Redmon and Angelova's single-pass detector

**Historical.** It is the ancestor of the three models above, and reading it shows
you the one idea they all kept.

Size not stated, nothing to run, and no licence, because neither the code nor the
weights were released.

Joseph Redmon and Anelia Angelova published
[Real-Time Grasp Detection Using Convolutional Neural Networks](https://arxiv.org/abs/1412.3128)
in 2015. Their network looked at the whole picture once and gave back the four
numbers of one grasp rectangle directly, instead of testing candidate patches one at
a time. It replaced the patch classifier in the next sub-section because looking
once is far cheaper than looking at every patch.

The one idea is to ask the question once. Their own description of the network is a
single-stage regression to a graspable rectangle, with no sliding window and no
region proposals. A sliding window is the patch search of the next sub-section, and
a region proposal is a cheap first pass whose job is to suggest the few places worth
looking at properly. This network does neither. The whole picture goes in, and the
rectangle's four numbers come out.

Inside, it is a picture-classification network of its day with its last layer
changed. A classifier ends in a layer that gives one number per object class, and
those numbers are read as a list of guesses. Here that final layer gives the numbers
of a grasp rectangle instead, and training pushes those numbers towards the
rectangle a person drew on that picture. The paper reports a second version as well,
which cuts the picture into a grid of cells and predicts one rectangle inside each
cell, and it says the grid version did significantly better, especially on objects
that can be held in several different ways.

What asking once buys is the speed that the rest of this page inherited. What the
first version costs is choice. One rectangle per picture means the network decides
which object to grasp before you ever see its answer, so you cannot ask it for the
second-best grasp and you cannot ask it about one particular object, because a
single rectangle is the only sentence it can say. The grid version is the first step
away from that, and GG-CNN's maps are where that step ends up, with a cell for every
pixel instead of a cell for every grid square.

On a robot arm the limit bites as soon as two objects are on the table. With GG-CNN
you can take the outline of the object you want from a
[seeing model](../../03_seeing-models/01_overview.md), keep only the part of the
quality map that lies inside that outline, and take the peak there, which is how a
top-down detector is pointed at a chosen object. With one rectangle per picture
there is nothing to mask, and cropping the picture before the network sees it is the
only control you have left.

The reason not to use it today is that there is nothing to install. No maintained
implementation exists, so read the paper for the idea rather than the code.

### 5.5 Lenz, Lee and Saxena's patch classifier

**Historical.** It is here because it is the first deep learning grasp detector, and
because knowing what it cost explains why the maps in section 3 exist at all.

Size not stated, nothing to run, and no licence, because neither the code nor the
weights were released.

Ian Lenz, Honglak Lee and Ashutosh Saxena published
[Deep Learning for Detecting Robotic Grasps](https://arxiv.org/abs/1301.3592) in
2015, from Cornell University. Their system cut many small rectangles out of the
picture, asked a small network of each one whether a grasp there would hold, and
kept the best answer. The Cornell grasping dataset that section 4 described was
built for this work.

The one idea is that grasping can be treated as a question asked about one candidate
at a time, and that the measurements for answering it should be learned rather than
thought up by a person. That second half was the new part in 2015. The systems
before it described each patch with quantities somebody had designed, such as edges
or gradients, and this work let the network decide what to measure.

Inside, there are two networks in a row rather than one, and the paper calls the
arrangement a cascade. The first network is small, so it is cheap to run, and its
job is to throw away the candidates that are obviously bad. The few survivors go to
a second and larger network, which gives the answer that counts. The other piece of
the paper is about the input, which carries colour and depth channels together.
During training the weights were penalised in groups, grouped by which input channel
they read, so that the network could not lean on the colour channels and leave the
depth ones unused.

What the cascade buys is a separate, honest answer for every candidate, and the
freedom to ask about any candidate at all, including one your own code invented for
reasons of its own. What it costs is the running. Asking about every rectangle in a
picture means thousands of network runs, and because neighbouring rectangles overlap
almost completely, nearly all of that work is the same work repeated. The cascade
reduces the bill rather than removing it, and it adds a weakness of its own, because
anything the cheap first network discards is gone before the good network ever sees
it. Everything on this page since has been an argument about how to get all of those
answers out of one run instead.

On a robot arm this shape is still the right one whenever the candidates have to
come from you. If your gripper is an unusual shape, or a rule in your task says the
jaws must come down on one named part of the object, a model that paints its own
maps has no way to be told, while a scorer that answers about the candidates you
hand it does. That is the arrangement the
[grasp quality models](02_grasp-quality-models.md) page is about, and this is where
it started. There is nothing to install: read the paper, and use the dataset.

### 5.6 How to choose

Start with GG-CNN. It is the smallest, its BSD-3-Clause licence lets you sell what
you build, it needs no compiled extensions, and it will put a grasp rectangle on
your screen the same day.

Four things change that choice.

- If a depth camera sees your objects badly, which happens with flat, thin, shiny or
    see-through things, use GR-ConvNet, because it reads the colour picture as well.
    You pay for that with a much larger network, and with a colour picture that has
    to be lined up with the depth one.
- If the right place to close the jaws is not at the surface the camera sees, such
    as below the rim of a mug or inside a recess, use FC-GQ-CNN, because it chooses
    the gripper's height itself. Use it only for research, because its licence
    forbids anything else.
- If your gripper's opening is far from the one in the training data, no released
    set of weights is right for you, and the width map will be wrong rather than
    approximate. Both GG-CNN and GR-ConvNet ship a training script and both read the
    Jacquard dataset, so retraining is the answer and not a workaround.
- If anything in your scene needs a grasp that is not straight down, no model on
    this page can express it. Read the
    [six-degree-of-freedom grasps](../02_most-used/01_six-dof-grasps.md) page
    instead, and weigh that choice first, because it costs you a
    graphics card and usually a licence.

One thing should not change your choice, and that is the age of these models. The
newest usable one was published in 2020. That is because research attention moved to
six-degree-of-freedom grasps, and not because the planar models stopped working. A
flat table has not changed since 2020, and neither has the answer to it.

---

## 6. Where this is going

The sections above describe a method that has stopped changing, and this section says
what that means for the next two or three years. It was written on 4 October 2026,
every link in it answered on that day, and where I counted something I say how, so that
you can run the count again.

Book 3's frontier chapter sorts forward-looking statements into
[four kinds of claim](../../../03_frameworks/08_frontier/06_what-is-coming.md#1-four-kinds-of-claim-and-why-the-difference-decides-everything),
and this section uses those words. A demonstration is a recording of something working
once, under conditions the publisher chose. A product announcement says that something
can be bought or downloaded, so you can go and check it. A research result is a measured
number on a stated task. A projection is a statement about a date that has not arrived,
and it is the weakest of the four. Where a sentence below is my own judgement rather
than somebody else's claim, it says so.

The arc that brought this method here was short. In 2015 a network was asked about one
cut-out patch at a time, so covering a picture cost thousands of runs. By 2018 a network
of the same kind painted an answer for every pixel in a single pass, and the search was
not made faster but removed. That is the whole shape of the change, and it finished
there, because four numbers drawn on a picture cannot describe a grasp arriving from any
direction but straight down. Asking the next question meant changing the
representation, and that is the
[six-degree-of-freedom](../02_most-used/01_six-dof-grasps.md) page rather than this one.

Where this method is used in industry is mostly not published, and that has to be said
before any company is named. A vendor selling a picking cell publishes throughput,
uptime and the kinds of item it handles, not the shape of its model's output. I looked
for a vendor stating in its own words that it predicts grasp rectangles and did not find
one, so the honest statement is that nobody has published it.

The clearest documented line from this page to something you can buy runs through Ambi
Robotics. The University of California, Berkeley's own licensing office
[states](https://ipira.berkeley.edu/node/171) that the company "grew from the
Dexterity Network (Dex-Net) project at UC Berkeley", and names Ken Goldberg and Jeff
Mahler among its founders. Dex-Net is the work behind FC-GQ-CNN in
[section 5.3](#53-fc-gq-cnn-the-dex-net-top-down-policy). The company's own
[site](https://www.ambirobotics.com/) today names four products, AmbiSort A-Series,
AmbiSort B-Series, AmbiStack and AmbiOS, which sort parcels from a bulk input flow into
sacks and containers and stack them. Those are product announcements, because you can
ask to buy them. What the site does not say is which representation the model inside
uses now, so the lineage is documented and the present-day method is not. Treat it as
history rather than as evidence that a grasp rectangle is running in a warehouse today.

One fact about this method's place in industry is checkable, and it points downwards.
Planar detection reached ordinary robot software through [MoveIt](https://moveit.ai/),
the motion planning framework for the Robot Operating System, usually written ROS.
[PickNik Robotics](https://picknik.ai/) published
[deep_grasp_demo](https://github.com/PickNikRobotics/deep_grasp_demo), which wrapped
Dex-Net's depth-picture scorer and [GPD](https://github.com/atenpas/gpd)'s point-cloud
scorer as grasp generators inside the
[MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor). GitHub's
own application programming interface reports that repository as archived, with its last
push on 12 August 2026 and 146 stars, and I read that on 4 October 2026. Archived means
read-only, so nobody will update it for a newer MoveIt. That is a withdrawal of tooling rather than of the method, and it is the
strongest single piece of evidence that nobody with a maintenance budget is carrying
planar grasp detection forward.

What is being worked on right now, in this exact area, is very little, and the way to
see that is to count rather than to assert. The table below is a search of GitHub
repository descriptions and readme files, restricted to repositories pushed to since 1
January 2026, run on 4 October 2026. Read the left column as the phrase searched for,
the middle as how many repositories matched, and the right as the star count of the
most-starred match, which is the column that matters, because a count of repositories
with no stars is a count of coursework.

| Phrase in the readme, pushed to in 2026 | Repositories | Stars on the top match |
| --- | --- | --- |
| "grasp rectangle" | 33 | 1 |
| "GG-CNN" | 28 | 6 |
| "6-DoF grasp" | 221 | 19,892 |

Two cautions apply before anything is read into that table. The star count in the last
row belongs to a paper-list repository rather than to a grasp model, so that row is
inflated by reading lists and is not a like-for-like comparison of working code. And a
search of words is not a search of methods, so a planar model whose readme never uses
the phrase is missed. What survives both cautions is the first two rows: new planar
grasp code in 2026 is student work and single-author projects, and none of it has an
audience.

The repositories this page recommends tell the same story in dates. GitHub reports the
last push to [GG-CNN](https://github.com/dougsm/ggcnn) as 21 July 2020, to
[GR-ConvNet](https://github.com/skumra/robotic-grasping) as 9 November 2021, and to
[gqcnn](https://github.com/BerkeleyAutomation/gqcnn) as 25 April 2024. Nobody has
abandoned them in the sense of taking them down, and all three still have hundreds of
stars, but nobody is developing them. The training data has not moved either. The
[Jacquard dataset](https://jacquard.liris.cnrs.fr/) is still up and still the large one,
the Cornell grasping dataset's original download page no longer answers, and I found no
replacement for either.

The research effort that touches this method's niche is not about the method at all. It
is about making models small enough to run on the computer bolted to the robot, and
Book 3's frontier chapter records both halves of that: quantisation work reporting
four-bit weights and activations, and NVIDIA's announcement of 15 July 2026 putting new
Jetson edge computers in
[the first quarter of 2027](../../../03_frameworks/08_frontier/06_what-is-coming.md#22-nvidias-edge-computers-with-hardware-stated-for-the-first-quarter-of-2027)
with 16 gigabytes of memory on the entry part. The date has not arrived, so that half
is a projection. It matters here because the pressure it describes is the pressure this
method was already the answer to.

Three things here are still unsolved, and the first has been unsolved since 2018. The
width map belongs to one gripper. No released planar model takes the gripper's opening
as an input, so a gripper unlike the training gripper gets a width map that is wrong
rather than approximate, and the only fix is retraining. The six-degree-of-freedom
family has begun to answer this, because
[GraspGenX](https://github.com/NVlabs/GraspGenX) takes the gripper as part of the
question. The planar family has not answered it at all.

The second is the depth camera. A planar model's only input is a depth picture, so what
the camera cannot measure, the model cannot grasp, and shiny, transparent, thin and
dark objects are still what a depth camera measures worst. No work on the network
changes that, because the information is missing before the network runs.

The third is measurement, and it is the one that would matter most if anybody fixed it.
Papers on this method report how far a predicted rectangle is from a labelled rectangle
on Cornell or Jacquard. That measures agreement with a label rather than whether an
object was lifted, and the two come apart whenever the label set is incomplete, which
it always is, because a mug has many good grasps and the dataset drew a few. Book 3's
frontier chapter counts one in five robotics abstracts now mentioning a benchmark, in
[its measured research directions](../../../03_frameworks/08_frontier/06_what-is-coming.md#5-research-directions-with-momentum-measured-rather-than-asserted),
and planar grasp detection has received none of that attention. No public benchmark for
it states a real-robot protocol.

Now for the next two to three years. Everything in the rest of this section is my
expectation and not an announcement, and each one gives the reason, because a
prediction without a reason is worth nothing.

I expect the planar method to survive, and to survive because it is cheap and
predictable rather than because it is advancing. The reason is a price comparison that
does not depend on anybody's roadmap. GG-CNN is 62,420 weights and runs many times a
second on a computer with no graphics card. Every six-degree-of-freedom model in this
chapter needs an NVIDIA card, according to Book 3's
[what runs without CUDA](../../../03_frameworks/02_gripping/04_models-that-grasp.md#8-what-runs-without-cuda),
most need a segmentation model in front of them, and several carry licences you cannot
ship. A fixed camera looking down at a flat conveyor is a problem whose geometry does
not change from year to year, and the cheapest adequate answer to an unchanging problem
usually stays in place. Advancing and useful are different claims, and this page is
about a method that is the second without being the first.

I expect it to stop being a model you install and become a function inside something
larger. The reason is the archived MoveIt integration above, the absence of any
maintained planar package to replace it, and the shape of what did ship in 2026, where
a project like [GraspGen](https://github.com/NVlabs/GraspGen) delivers the sampler, the
scorer and the gripper handling in one piece rather than as parts you wire together. A
method with no packaging is still used, but it is used by people who copy a file into
their own repository. To check this
prediction, watch whether a planar grasp package appears in a ROS 2 distribution's
package list. My expectation is that none does.

I expect your own work on this method to be retraining rather than choosing, and the
reason is the width map. The failure you will meet is a gripper whose opening differs
from the training gripper's, no released model can be told about yours, and both GG-CNN
and GR-ConvNet ship a training script that reads Jacquard. That makes retraining the
normal path rather than the fallback. This one is easy to falsify: if a planar model
appears that takes the gripper's geometry as an input, the paragraph is wrong, and the
six-degree-of-freedom family has already shown that the idea works.

I expect cheap edge hardware to keep the price gap open rather than close it, and the
reason is arithmetic. Fitting a quantised vision-language-action model into 16 gigabytes
is an achievement; a 62,420-weight convolutional network fits in any computer sold in
the last decade. Each generation of edge hardware that makes a large model barely
possible also makes a small model free, so the planar method's advantage is not eroded
by hardware improving.

What I do not expect is a new flagship planar model, or a planar benchmark with a
real-robot protocol, and the reason is where the attention is. Book 3's frontier
chapter measures vision-language-action models rising from 0.52 per cent of robotics
abstracts in 2024 to 10.78 per cent by 23 September 2026, and 33 repositories whose best
match has one star is not a community that produces a flagship. If I am wrong, the
route will not be a standalone paper. It will be a per-pixel grasp head added inside a
larger model by somebody who needs a grasp every frame and cannot afford to generate
one, and then this method will have survived by being absorbed rather than by being
developed.

---

## 7. Where to read next

- [Six-degree-of-freedom grasps](../02_most-used/01_six-dof-grasps.md) removes the
    straight-down limit.
- [Grasp quality models](02_grasp-quality-models.md) scores top-down grasps one at
    a time instead of painting maps.
- [Object detection](../../03_seeing-models/02_most-used/01_object-detection.md) is
    the seeing model that this kind borrows its name and its methods from.
- Book 3's
    [models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md)
    lists the code and the licences.
- Book 3's [grippers and hardware](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md)
    explains parallel-jaw grippers and how far they open.
