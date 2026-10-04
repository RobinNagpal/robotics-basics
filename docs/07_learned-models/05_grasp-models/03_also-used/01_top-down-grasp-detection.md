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
6. [A worked example: a mug on a table](#6-a-worked-example-a-mug-on-a-table)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

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

GG-CNN is the generative grasping convolutional neural network. Douglas Morrison,
Peter Corke and Jürgen Leitner published it at the Robotics: Science and Systems
conference in 2018, in a paper called
[Closing the Loop for Robotic Grasping](https://arxiv.org/abs/1804.05172). It takes
one 300 by 300 depth picture and paints the quality, the angle and the width maps
that section 3 described. The [repository](https://github.com/dougsm/ggcnn) also
holds a second and slightly larger version called GG-CNN2.

The obvious alternative is GR-ConvNet in the next sub-section, which paints the same
three maps with a much larger network. Choose GG-CNN instead when the arm has to
keep looking while it reaches. GG-CNN has 62,420 weights and GR-ConvNet has
1,900,900, counted from the layer sizes the two projects publish, so GG-CNN is about
thirty times smaller. Running the model again during the reach was the problem the
paper set out to solve, and the small network is how it solved it, because a small
network finishes in time for the next camera frame.

What it costs you is mostly age. The repository was written for Python 3.6 on Ubuntu
16.04 and was last pushed in July 2020, so the install takes more work than the model
does. It needs no graphics card and no compiled extensions, so that install is still
possible on a current machine. The thing that most often goes wrong is the depth
picture itself,
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
the winning pixel to a gripper pose that section 6 sets out, and the cut-off on the
quality map. That last one is a real decision, because `detect_grasps` accepts peaks
above 0.2 by default, and a low cut-off means the model always answers even when
nothing in the picture can be grasped.

### 5.2 GR-ConvNet, the same three maps from a larger network

**Most used in 2026** when depth alone is not enough, because it is the only model
on this page that reads the colour picture as well and still carries a licence you
can ship.

GR-ConvNet is the generative residual convolutional neural network. Sulabh Kumra,
Shirin Joshi and Ferat Sahin published it in 2020, from the Multi-Agent Bio-Robotics
Laboratory at the Rochester Institute of Technology, in a paper called
[Antipodal Robotic Grasping using Generative Residual Convolutional Neural
Network](https://arxiv.org/abs/1909.04810). It paints the same quality, angle and
width maps as GG-CNN, from a 224 by 224 input with four channels, which are red,
green, blue and depth. Between its downward and upward halves sit five residual
blocks, which are pairs of convolutional layers that add their input back to their
output so that a deeper network still trains.

The obvious alternative is GG-CNN. Choose GR-ConvNet instead when a depth camera
sees your objects badly, because a flat object lying on a flat table is almost
invisible in depth and obvious in colour. Its
[repository](https://github.com/skumra/robotic-grasping) also commits its trained
weights into Git rather than attaching them to a release, so they are there as soon
as you clone it. Those two differences are the whole case for it.

What it costs you is thirty times as many weights as GG-CNN, so it is the wrong
choice if you wanted the model to run on every camera frame without a graphics card.
It was last pushed in November 2021, so it has the same ageing install, although its
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

FC-GQ-CNN is the fully convolutional grasp quality convolutional neural network,
published in 2019 by the AUTOLAB group at the University of California, Berkeley, as
part of Dex-Net 4.0. It started as a scorer rather than a detector. Dex-Net 2.0 cut
a 96 by 96 patch around one proposed grasp and gave that grasp a single number,
which the [grasp quality models](02_grasp-quality-models.md) page describes in full.
The fully convolutional version runs that same small network as a convolution over
the whole depth picture, so one pass scores a grasp at every fourth pixel and at
each of 16 different gripper heights.

The obvious alternative is GG-CNN, which also answers for every pixel in one pass.
Choose FC-GQ-CNN instead for one reason: it chooses the gripper's height as well as
the pixel and the angle. GG-CNN reads the height out of the depth picture at the
winning pixel, which is wrong whenever the best place to close the jaws is not at
the surface the camera can see, such as around the body of a mug below its rim.

What it costs you is everything else. The code pins TensorFlow at 1.15 or below and
its own packaging names Python 3.5 to 3.7, so it needs an environment of its own.
The licence is a University of California Regents grant for education, research and
not-for-profit purposes only, with a Berkeley technology licensing contact for
anything else, so you cannot ship it. The thing that most often goes wrong is the
picture size, because the fully convolutional network is built for one fixed height
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

Joseph Redmon and Anelia Angelova published
[Real-Time Grasp Detection Using Convolutional Neural Networks](https://arxiv.org/abs/1412.3128)
in 2015. Their network looked at the whole picture once and gave back the four
numbers of one grasp rectangle directly, instead of testing candidate patches one at
a time. It replaced the patch classifier in the next sub-section because looking
once is far cheaper than looking at every patch.

The reason not to use it today is that it gives one rectangle for the whole picture.
If two objects are on the table, the network chooses between them before you do, and
you cannot ask it for the second-best grasp or for a grasp on a particular object.
GG-CNN's three maps give you every grasp in the picture for the same cost, which is
why nobody went back. There is no maintained implementation to install, so read the
paper for the idea rather than the code.

### 5.5 Lenz, Lee and Saxena's patch classifier

**Historical.** It is here because it is the first deep learning grasp detector, and
because knowing what it cost explains why the maps in section 3 exist at all.

Ian Lenz, Honglak Lee and Ashutosh Saxena published
[Deep Learning for Detecting Robotic Grasps](https://arxiv.org/abs/1301.3592) in
2015, from Cornell University. Their system cut many small rectangles out of the
picture, asked a small network of each one whether a grasp there would hold, and
kept the best answer. The Cornell grasping dataset that section 4 described was
built for this work.

The three usable models above exist because of this model's cost. Asking a network
about every candidate rectangle separately means thousands of network runs for one
picture, and everything since has been an argument about how to get all of those
answers from one run. Its own answer to the cost, which was a cheap first network
that threw most candidates away and an expensive second network on the survivors,
survives today in the samplers that the
[grasp quality models](02_grasp-quality-models.md) page describes. There is nothing
to install: read the paper, and use the dataset.

### 5.6 How to choose

Start with GG-CNN. It is the smallest, its BSD-3-Clause licence lets you sell what
you build, it needs no compiled extensions, and it will put a grasp rectangle on
your screen the same day.

Four things change that choice.

- If a depth camera sees your objects badly, which happens with flat, thin, shiny or
    see-through things, use GR-ConvNet, because it reads the colour picture as well.
    You pay for that with thirty times as many weights.
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
    instead, and read section 8 below first, because that choice costs you a
    graphics card and usually a licence.

One thing should not change your choice, and that is the age of these models. The
newest usable one was published in 2020. That is because research attention moved to
six-degree-of-freedom grasps, and not because the planar models stopped working. A
flat table has not changed since 2020, and neither has the answer to it.

---

## 6. A worked example: a mug on a table

Once the pieces above run in order they are easier to follow, so here is how a
top-down detector picks up a mug, step by step.

1. A depth camera is fixed above the table, looking straight down, and it takes one
    depth picture.
2. The picture is cut down to the square the model expects and passed to the
    network.
3. The network paints its three maps, and the quality map is brightest in the
    middle of the mug's body, where the jaws can close across the mug.
4. Code finds the brightest pixel, and there it reads an angle of 60 degrees and a
    width a little wider than the mug.
5. Code turns that pixel into a point on the table, using the camera's position.
    Book 2's
    [finding objects](../../../02_perception/01_camera/02_finding-objects.md) page
    shows how a pixel becomes a point in the room.
6. The arm moves the open gripper above that point, turns its wrist to 60 degrees,
    goes straight down to the depth read from the picture, and closes.
7. The arm lifts, and if the model runs fast enough it keeps looking during step 6
    and corrects the grasp if the mug moved.

Notice that the model never saw this mug before. It still works, because the mug's
shape from above, which is a round blob of near pixels, looks like thousands of
shapes it saw in training.

---

## 7. What goes wrong

That example went well, but the biggest limit is built into the answer itself,
because a rectangle can only describe a gripper that comes straight down.

![A box in a bin, and a box on a shelf](../../../images/grasp-models/top-down-grasp-detection/straight-down-only.svg)

On the left, straight down works and a rectangle describes it. On the right, the
shelf board is in the way, so the only grasp that fits comes from the front
instead.

So that limit and four others show up as the problems below.

- Some objects need a side grasp, so a plate leaning on a wall, a box on a shelf or
    a bottle lying against the side of a bin cannot be held from above. The model
    has no way to say "from the side", which is why people switch to a
    [six-degree-of-freedom model](../02_most-used/01_six-dof-grasps.md) for these.
- Tall objects are hard, because the model sees only the top of a tall object and
    cannot tell whether the jaws are long enough to reach down its sides.
- Shiny and see-through objects are often missed, because a depth camera often
    gives no depth for glass or polished metal, so the model sees a hole where the
    object is. Book 2's
    [models that find](../../../02_perception/02_object-perception/04_models-that-find.md#17-transparent-and-shiny-objects)
    covers ways around this, and the
    [depth from pictures](../../03_seeing-models/03_also-used/02_depth-from-pictures.md)
    page covers models that fill in missing depth.
- Your gripper may differ from the one in training, because the model learned
    widths for the gripper in its own training data. If your gripper opens less far
    then some of its grasps will be too wide, and code must throw those away.
- The model has no sense of the task, so it does not know that a knife should be
    held by the handle. The
    [suction and affordance](../02_most-used/02_suction-and-affordance.md) page
    covers models that do.

---

## 8. Why this kind, and what it costs

Since you have now seen the limits, it is worth setting out plainly what this kind
buys you. A top-down grasp detector takes one depth picture and gives the best place to close
two jaws, coming straight down.

What it does for you is give a fast, simple answer for objects you have never seen.
The model is small, so it runs on an ordinary computer without a graphics card, and
its answer is easy to draw on the picture and check by eye.

The obvious alternative is a
[six-degree-of-freedom grasp model](../02_most-used/01_six-dof-grasps.md), which
can grasp from any direction. The reason to choose the top-down kind instead is
that many real jobs never need another direction. For example, parts on a conveyor,
parcels on a table and objects spread out on a flat surface can all be picked from
above. For those jobs the six-degree-of-freedom model adds cost and gives nothing
back. That is because it needs a point cloud, a strong NVIDIA graphics card and
usually a licence that forbids selling what you build.

The other alternative is a rule you write yourself, such as "close across the
narrowest part of the object's outline". Book 3's
[choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#10-why-a-rule-beats-a-network)
argues that a rule is better when the objects are known, while the model is better
when they are not.

What it costs you is the straight-down limit, and it also costs you the age of the
code. The best-known models were written around 2018 to 2020, so they need some
work to run on current software.

---

## 9. The written alternative

Instead of a network, a written top-down grasp is built from Book 5's picture
methods and Book 3's rules. A depth limit from [thresholding and colour
masks](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
marks what stands above the table, and then [edges and
contours](../../../06_programming-techniques/05_image-and-point-cloud-processing/03_also-used/01_edges-and-contours.md)
traces each object's outline. The smallest turned rectangle round that outline
gives the angle for the wrist, while the outline's width checks that the part fits
between the fingers. Book 3's [choosing a
grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md) then chooses where
on the outline to close. The written way wins for known objects spread out on a
flat surface, and the model wins on objects nobody has listed.

---

## 10. Where to read next

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

