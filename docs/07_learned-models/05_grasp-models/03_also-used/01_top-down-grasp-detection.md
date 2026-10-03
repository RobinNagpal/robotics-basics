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
11. [Using it in Python](#11-using-it-in-python)

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
model. The older way finds one rectangle for the whole picture, while the newer way
paints an answer onto every pixel instead.

### One rectangle per picture

The earliest models of the older way looked at many small patches of the picture,
one at a time, and asked a network "is there a good grasp here?" This was slow,
because the picture has thousands of patches. A later model looked at the whole
picture once and gave back the four numbers of one rectangle directly. That was
fast, but it could only give one grasp per picture.

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
object that is pushed or slides.

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

So far this page has described the method, and these four models show how it
developed over five years. Book 3's
[models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md#2-planar-models-a-grasp-is-a-rectangle)
lists their code, their licences and how old they are.

- **Lenz, Lee and Saxena's detector (2015)** was one of the first to use deep
    learning for grasp rectangles, and it checked many small patches of the picture
    one by one.
- **Redmon and Angelova's detector (2015)** looked at the whole picture once and
    gave back one rectangle directly, so it was much faster than checking patches.
- **GG-CNN**, the generative grasping convolutional neural network (2018), paints
    the quality, angle and width maps described above. It is very small, which lets
    it run again and again while the arm moves.
- **GR-ConvNet**, the generative residual convolutional neural network (2020), does
    the same job with a larger network, and it can take a colour picture as well as
    depth.

All four draw rectangles for a gripper that comes straight down. The
[grasp quality models](02_grasp-quality-models.md) page covers Dex-Net, which also
works on top-down grasps but in a different way. Instead of painting maps, it
scores grasps one at a time.

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
masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
marks what stands above the table, and then [edges and
contours](../../../05_programming-techniques/05_image-and-point-cloud-processing/03_also-used/01_edges-and-contours.md)
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

---

## 11. Using it in Python

Section 3 said that GG-CNN paints three maps over the depth picture, a quality map,
an angle map and a width map, and that the best rectangle is read off the peak of
the quality map. This section shows that reading happening in Python, so that after
reading it you will know how small this model really is and where the work goes
instead.

GG-CNN is not a package on the Python package index. You clone
[the repository](https://github.com/dougsm/ggcnn) and download the released weights,
which include the whole saved model, so no code is needed to rebuild the network.
The imports `models.common` and `utils.dataset_processing.grasp` are folders inside
the clone.

```python
import torch
from models.common import post_process_output              # in the cloned repository
from utils.dataset_processing.grasp import detect_grasps

net = torch.load("ggcnn_weights_cornell/ggcnn_epoch_23_cornell")
net.eval()

with torch.no_grad():
    # depth has shape (1, 1, 300, 300): one 300 by 300 depth picture, in metres
    pos, cos, sin, width = net(depth)

q_img, ang_img, width_img = post_process_output(pos, cos, sin, width)
grasp = detect_grasps(q_img, ang_img, width_img=width_img, no_grasps=1)[0]
print(grasp.center, grasp.angle, grasp.length)
```

The repository gives you a network small enough to run many times a second on a
laptop, and it gives you the two steps around it that you would otherwise get wrong.
`post_process_output` is one of them: the network does not output an angle, it
outputs the cosine and the sine of twice the angle, and this function turns that pair
back into an angle and then smooths all three maps, which stops the peak jumping
between neighbouring pixels from frame to frame. `detect_grasps` is the other: it
finds the peaks of the quality map and reads the angle and the width at each peak,
and it returns a `Grasp` whose `center` is the pixel as a row and a column, whose
`angle` is in radians, and whose `length` is the gripper opening in pixels.

What you have to supply is the depth picture in the exact shape the network was
trained on, which is 300 by 300 pixels of depth in metres, centred on the part of the
table you care about. Cropping and resizing to that shape is your code. Turning the
answer back into something the arm can use is also your code, and there is more of it
than the model: the pixel has to become a point in the camera's frame using the
camera's intrinsic parameters and the depth at that pixel, then a point in the
robot's frame using your calibration, then a full gripper pose by combining that
point with the angle and a straight-down approach. The opening in pixels has to
become an opening in millimetres, which depends on how far away the object is.

The decision that is yours is the cut-off on the quality map. `detect_grasps` asks
for peaks above 0.2 by default, which is low, and a low cut-off means the model
always answers even when there is nothing graspable in the picture. Raising it makes
the arm refuse more often and succeed more often when it does try. The other
decision is whether to retrain. These weights were trained on the Cornell grasping
dataset, whose rectangles were drawn for a two-finger gripper of one size, so the
width map is in that gripper's units, and the whole model assumes the gripper comes
straight down. If your gripper is a different size, the width map is simply wrong for
you, and the training script `train_ggcnn.py` in the same repository is how you fix
it, on either the Cornell or the Jacquard dataset.
