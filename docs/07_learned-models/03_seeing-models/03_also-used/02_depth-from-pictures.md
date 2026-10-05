# Depth from pictures

This page answers one question: how can a model tell how far away things are, when
all it has is ordinary photos? A robot arm needs distances before it can reach for
anything, but a photo alone does not contain them, so this is a harder problem than
it first looks.

It is written for a reader who has already read the earlier pages of this
chapter, and who knows what a model is from [what a model
is](../../01_what-models-are/01_what-a-model-is.md). It covers three kinds of
model: the first guesses depth from one photo, the second measures depth from
two photos taken side by side, and the third repairs the holes that a depth
camera leaves on shiny and clear objects.

> Before this page, it helps to have read [multi-view geometry](../../../06_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md), which explains how the shift of a point between two pictures gives its depth. The stereo models on this page learn the matching and keep that geometry.

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

The one-sentence idea is this: a depth model looks at one or two photos and gives
every pixel a distance from the camera.

You already do this with your own eyes, because if you close one eye and look at
a room, you still know that the chair is nearer than the wall. You know it
because the chair covers part of the wall, because the chair looks big, and
because you know how big chairs usually are. Nobody measured anything, so you
used clues you have learned over your life, and a depth model learns the same
kinds of clues from millions of photos.

Now open both eyes, because each eye sees the scene from a slightly different
place. Near things shift a lot between the two views, while far things shift only a
little. So your brain uses that shift to judge distance more precisely. A stereo
depth model does the same thing with two cameras.

There are three kinds of model on this page.

- A **monocular depth** model uses one photo, and monocular means "one eye".
- A **stereo** model uses two photos taken at the same moment by two cameras a
  known distance apart.
- A **depth completion** model takes a depth image that has holes or wrong values
  in it and fills them in, using the colour photo as a guide.

---

## 2. What goes in and what comes out

Different as those three kinds are, the output of all of them is a **depth map**,
which is a picture the same size as the photo where each pixel holds a distance
instead of a colour. People usually show it in grey, with near things light and far
things dark.

![A photo and its depth map](../../../images/seeing-models/depth-from-pictures/photo-to-depth-map.svg)

The mug is near, so its pixels are light, and the wall is far, so its pixels are
dark.

The inputs differ, however, so the table below shows what each kind of model takes
in and what its output means, and you should read each row of it across.

| Kind | What goes in | What comes out | Are the distances in metres? |
| --- | --- | --- | --- |
| Monocular | one colour photo | one distance per pixel | only for some models, and only roughly |
| Stereo | two colour photos, taken side by side | one distance per pixel | yes, if the cameras are measured carefully |
| Depth completion | a colour photo and a depth image with holes | the depth image with the holes filled | yes, because it starts from real measurements |

That last column matters a great deal, because many monocular models give only
**relative depth**. Relative depth tells you the order of things, so the mug is
nearer than the box and the box is nearer than the wall. However, it does not tell
you how many metres away anything is. A model that gives real distances in metres
gives **metric depth** instead.

![Relative depth fits a small scene and a large scene equally well](../../../images/seeing-models/depth-from-pictures/relative-vs-metric.svg)

The same relative answer fits a doll's house and a real kitchen, so relative depth
alone cannot tell the arm how far to reach.

For a robot arm, the depth map is rarely the final answer, because the robot
turns it into a **point cloud**. This is a list of 3D points, one for each
pixel, worked out from the pixel's position and its distance. The [3D models
chapter](../../04_3d-models/01_overview.md) works with point clouds.

---

## 3. How it works inside

### One photo

A monocular model is usually built from two parts, and the first part is an
**encoder**, which is a network that turns the photo into a large set of numbers
describing what is where in the picture. Many recent models use a **vision
transformer (ViT)** as that encoder, because a vision transformer cuts the picture
into small square patches and lets every patch compare itself with every other
patch. This is what helps it use clues from the whole picture at once, such as
where the floor meets the wall.

Then the second part is a **decoder**, which turns those numbers back into a
picture of the original size, with one distance per pixel. Depth Anything V2, which
section 5.1 recommends, is an encoder and a decoder in exactly this arrangement.

The model works from clues it learned in training. For example, things higher in
the picture are often further away, a thing that covers another thing is nearer,
and parallel lines, such as the edges of a table, get closer together as they go
away. Known objects, such as mugs and doors, also have typical sizes.

The shortlist in section 5 holds two variations on this shape, and both change what
goes in rather than how the network is built. Prompt Depth Anything, in section
5.3, takes the coarse depth image from a depth camera as a second input, and those
real measurements steer the model to an answer in metres instead of an order. Depth
Anything 3, in section 5.2, passes several photos of the same scene through one
encoder together, so it gives depth for all of them and also works out where each
photo was taken from. One photo on its own still works, and the further photos only
add to what the model has to go on.

### Two photos

A stereo model follows the shift idea from section 1, and the shift of a thing
between the left and the right photo is called **disparity**.

![Two cameras see a near mug shift more than a far box](../../../images/seeing-models/depth-from-pictures/two-cameras-disparity.svg)

The near mug moves a long way between the two pictures and the far box moves only
a little, so the size of the shift tells the distance.

The steps of a stereo model are these four.

1. Both photos go through the same encoder, which turns small patches into lists of
   numbers that describe them.
2. For each patch in the left photo, the model compares it with patches along the
   same row in the right photo, and the one that matches best shows how far that
   patch shifted.
3. A learned network then cleans up the matches, because it smooths flat areas and
   keeps sharp edges between objects.
4. Finally, simple geometry turns each shift into a distance, since distance equals
   a fixed number divided by the shift. That fixed number comes from the distance
   between the two cameras and the camera's lens, so a big shift means near and a
   small shift means far.

Step 4 is why stereo gives real metres, because the model does not guess the scale
at all: the scale comes from the measured gap between the cameras.

RAFT-Stereo, which section 5.4 recommends, is built from these four steps, and it
repeats step 3 in many small rounds rather than doing it once. FoundationStereo, in
section 5.5, follows the same four steps, and what sets it apart is the breadth of
its training rather than a different recipe.

### Filling holes

Instead of guessing or matching, a depth completion model gets two inputs: the
colour photo, and the real depth image from a depth camera. The depth image is
good in most places, but on a clear glass or a shiny spoon it is empty or wrong,
because the camera's light passes through the glass or bounces off the metal.

So the model learns to use the good depth around the hole, plus the shape it can
see in the colour photo, to fill that hole. For example, it sees the outline and
the highlights of a glass in the colour photo, and it sees the table depth all
around the glass, so it fills in the glass as a surface standing on that table.

![A depth hole on a clear glass, and the filled depth](../../../images/seeing-models/depth-from-pictures/glass-depth-hole.svg)

The depth camera returns nothing on most of the glass (red), and the completion
model fills that area with a sensible distance.

ReMake, which section 5.6 recommends, is the completion model on this page, and it
needs one more input than the two described here, because you also give it an
outline of the object. The transparent variant of Prompt Depth Anything does a
similar job from the colour photo and the sensor's depth alone.

---

## 4. How it is trained

Whichever of those three kinds you use, a depth model learns from photos paired
with the correct depth, and getting that correct depth is the hard part, so
different models use different sources.

- **Depth cameras indoors.** A depth camera records a colour photo and a depth image
  together, and the pairs then become training examples. This gives real distances,
  but the depth has holes on shiny and dark things.
- **Laser scanners outdoors.** Self-driving car datasets drive a car with cameras
  and a laser scanner, which measures distance with light, so the scanner gives
  correct distances for part of each photo.
- **3D films.** Films shot for 3D cinema have a left and a right picture for every
  frame, and the shift between them gives relative depth. MiDaS was trained partly
  on pictures like these.
- **Computer-made scenes.** A program renders a 3D scene and knows the exact depth
  of every pixel. This is the main source for stereo models and for clear-object
  models, because real clear objects are so hard to measure.
- **Pictures labelled by another model.** Depth Anything used a large model, trained
  first on labelled pictures, to label millions of unlabelled internet photos, and a
  student model then learned from all of them. This is called **pseudo-labelling**,
  because the labels come from a model rather than from a measurement.

Relative-depth models are trained to get the order right and to ignore the scale,
which lets them learn from many datasets whose units do not agree. That is also why
their output is not in metres.

---

## 5. Well-known models

This section names the depth models a developer actually reaches for in 2026, and
it helps you decide which one belongs on your arm. The decision it has to settle
is the one from section 2: whether to guess depth from one photo, to measure it
from two photos, or to let a depth camera measure it and use a model only to
repair what the camera missed.

Two older names still appear in tutorials and should not be your starting point.
MiDaS, from Intel in 2019, proved that one network could give relative depth for
almost any photo, and ZoeDepth was its metric follow-up. Both repositories now
carry the "Public archive" label on GitHub, so nobody is fixing them.

The table compares the six models below. The left column names the model and says
how current it is. The right column holds everything you weigh up: what the model
gives you, how large it is, the licence of the weights rather than of the code, and
when to pick it. A **parameter** is one of the numbers inside the network, and the
counts come from the files Hugging Face serves and from the Depth Anything 3 model
card. Where a model ships in several sizes under different licences, the right
column says so, because that is the detail people get wrong most often.

| Model | What decides it |
| --- | --- |
| **Depth Anything V2**, most used in 2026 | Relative depth from one photo, with 24.8 million parameters in the small size and 97.5 million in the base size. The small weights are Apache-2.0, while the base and larger weights are CC BY-NC 4.0. Pick it when you have one colour camera and need order, not metres. |
| **Depth Anything 3**, worth betting on | Relative or metric depth, from one photo or several, in sizes from 0.08 to 1.4 billion parameters. Small, Base, `DA3METRIC-LARGE` and `DA3MONO-LARGE` are Apache-2.0, while Large, Giant and Nested are CC BY-NC 4.0. Pick it when you need metric depth and you have to ship it. |
| **Prompt Depth Anything**, worth betting on | Metric depth from one photo plus a coarse depth image, with 25.1 million parameters, under Apache-2.0. Pick it when you already have a depth sensor and want its reading sharpened. |
| **RAFT-Stereo**, most used in 2026 | Metric depth from two photos, under the MIT licence. Its size is `not stated`. Pick it when you can mount two cameras and measure the gap between them. |
| **FoundationStereo**, worth betting on | Metric depth from two photos, including scenes it never saw, under an NVIDIA licence that is non-commercial. Its size is `not stated`. Pick it when you are doing research, not shipping. |
| **ReMake**, worth betting on | Depth for clear and shiny objects a sensor cannot see, under the MIT licence. Its size is `not stated`. Pick it when your objects are glass or chrome. |

### 5.1 Depth Anything V2

Depth Anything V2 is **most used in 2026** for relative depth from one photo, and
it is where most robot projects start.

Size s in the small checkpoint, a laptop, Apache-2.0 for the code, Apache-2.0 for
the small weights and CC BY-NC 4.0 for the base and larger ones.

It was published in June 2024 as [Depth Anything
V2](https://arxiv.org/abs/2406.09414), and section 4 described how it was trained.

The one idea is that the model measures nothing at all. It has learned what the
world usually looks like, and it returns the depth that best fits the picture in
front of it. What V2 added to that idea is about where the learning comes from.
Real photos paired with measured depth are noisy, and a measuring device misses
exactly the surfaces that matter to an arm, such as thin edges, shiny metal and
glass. So the authors trained their teacher model only on computer-made pictures,
whose depth is exact in every pixel, then had that teacher label millions of
ordinary unlabelled photos, and trained the model you download on those
teacher-labelled photos. The computer-made pictures supply exactness and the real
photos carry it over to real scenes.

Inside, it is the encoder and decoder of [section 3](#3-how-it-works-inside), and
its encoder is a DINOv2 vision transformer, the same backbone the [image
classification](01_image-classification.md#53-dinov2-with-a-small-head) page
recommends for frozen features. The part worth understanding is what the decoder
is asked to produce. It is not a distance. It is a number that rises as the
distance falls, and the training treats any multiplication and addition of that
number as the same answer, so the model is never told what the units are. That
freedom is what lets one model learn from many datasets whose units disagree, and
it is the whole reason a value of 8 means "nearer than 4" and nothing more.
Nothing in this network produces metres, and no amount of further training would,
because the quantity it was asked for has no units.

What this buys is depth from any photo, with no calibration, no second camera, no
sensor and no light of its own, and a value in every pixel, including on surfaces
where a depth camera returns nothing. What it costs is that the answer is a guess,
and a guess fails in ways a measurement never does. Appearance is all this model
has, so a photograph of a scene is given the depth of the scene depicted rather
than of the flat paper, which means a poster, a screen or a printed label in the
workspace is read as the space it shows. A surface the model has no clues about
gets whatever usually fits a surface in that position.

On an arm the difference from the stereo model of section 5.4 is not that one is
more accurate. The two fail in different places. A blank white panel or a plain
plastic tray gets a smooth, confident surface from this model, while the stereo
matcher has nothing to match there and returns an unusable patch. A printed box
lid is the reverse: this model follows the picture printed on the lid, and the
stereo pair measures the flat lid correctly. That is why a cell that must not drop
anything measures the distance and uses a monocular model only for the places the
measurement missed.

The obvious alternative among the monocular models is Marigold, which starts from
an image-generating model. Depth Anything V2 is the one to pick because it is far
smaller, far faster, and carried by `transformers`, so one line loads it. Pick it
when you have one colour camera and you need to know which thing is in front, not
how many millimetres away it is.

What it costs you is the units, and the one thing to watch in the licence is that
the Apache-2.0 badge on the GitHub repository covers the code rather than the
base and larger weights. The other thing that goes wrong often is trusting the
depth at the edge of an object, which is where a gripper closes and where these
models are least accurate.

The library is `transformers`, which has a pipeline for depth.

```python
from PIL import Image
from transformers import pipeline

# The "-Small-hf" checkpoint is the Apache-2.0 one.
pipe = pipeline("depth-estimation",
                model="depth-anything/Depth-Anything-V2-Small-hf")

prediction = pipe(Image.open("table.jpg"))

depth = prediction["predicted_depth"].numpy()   # one number per pixel
picture = prediction["depth"]                   # the same thing as a grey image
print(depth.shape, float(depth.min()), float(depth.max()))
```

What the library gives you is a number for every pixel of any ordinary photo, with
no camera calibration, no second camera and no training. What you still have to
supply is the scale: either fit the output against a few real distances, such as
the known height of the table, or use one of the metric models below.

### 5.2 Depth Anything 3

Depth Anything 3 is **worth betting on**, because it is where this family is
going: one network that handles one photo or many, and that comes in a metric size
whose weights you are allowed to ship.

Size m for `DA3METRIC-LARGE`, a small card, Apache-2.0 for the code and for the
Small, Base, `DA3METRIC-LARGE` and `DA3MONO-LARGE` weights, CC BY-NC 4.0 for the
Large, Giant and Nested ones.

ByteDance published it in November 2025, as [Depth Anything 3: Recovering the
Visual Space from Any Views](https://arxiv.org/abs/2511.10647). The checkpoint to
know about is `DA3METRIC-LARGE`, which gives metric depth and is Apache-2.0
according to the project's own model card.

The one idea is to answer with one shape of prediction, whatever number of
pictures you hand over, and to use as little special machinery as possible to do
it. The report states two findings behind that. A plain transformer encoder of the
DINO kind is enough as the backbone, with nothing added for depth in particular.
And a single prediction target removes the need to train several heads for several
different tasks.

What changes inside, compared with Depth Anything V2 above, is that the pictures
are not processed one at a time. V2 takes one photo and returns one depth map, and
if you give it two photos of the same bin you get two maps whose scales have
nothing to do with one another. Depth Anything 3 passes every picture you hand it
through the same encoder together, and the attention step runs across the patches
of all the pictures at once, so each picture's answer can use what the others show.
The single target is the second change. For each pixel the model predicts how far
along a ray the surface lies, together with the direction of that ray, which the
report calls a depth-ray target. That is enough to place the pixel in space, and
because the rays from several pictures have to agree on one scene, where each
camera stood falls out of the same prediction rather than being computed by a
separate network.

What this buys is one geometry that several views agree on, the camera positions
for free, and checkpoints that give metres and may be shipped. What it costs is
more than V2 in every direction: a graphics card, the project's own package rather
than `transformers`, memory that grows with the number of pictures you pass at
once, and a scale that is still not in metres until you apply the conversion
below.

On an arm the difference shows up as soon as there are two cameras that are not a
stereo pair, which is the usual arrangement: one fixed above the cell and one on
the wrist. V2 gives you two depth maps with two unknown scales, and no arithmetic
turns them into one point cloud. Depth Anything 3 given both pictures returns
depth for both in one frame, plus where the two cameras were, which is exactly what
merging needs. Against Prompt Depth Anything in the next sub-section, the trade is
the other way: if you already own a depth camera, that model takes its metres from
the sensor, where this one has learned its metres and can be wrong about them on a
scene unlike its training.

The obvious alternative for permissive metric depth is MoGe-2, from Microsoft,
which is MIT for both code and weights. This repository's survey in [models that
measure](../../../02_perception/02_object-perception/05_models-that-measure.md#12-the-models-and-their-licences)
names those two as the strongest metric models with genuinely permissive weights.
Pick Depth Anything 3 when you also want the multi-view ability, because the same
model estimates camera positions from several photos.

The split licence is the trap in this family, because the largest checkpoints are
the ones you may not ship, and people reach for the largest by habit. The thing
that most often goes wrong is the metric output
itself, because it is not in metres until you scale it. The project's own answers
page gives the conversion, `metric_depth = focal * net_output / 300`, where
`focal` is the focal length in pixels.

The library is the project's own `depth_anything_3` package, from its [GitHub
repository](https://github.com/ByteDance-Seed/Depth-Anything-3).

```python
import torch
from depth_anything_3.api import DepthAnything3

# DA3METRIC-LARGE is the Apache-2.0 metric checkpoint.
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE")
model = model.to(device=torch.device("cuda"))

# inference takes a list of image paths, even when the list has one entry.
prediction = model.inference(["table.jpg"])

print(prediction.depth.shape)   # [1, height, width], float32
print(prediction.conf.shape)    # how sure the model is, per pixel
```

What the library gives you is the depth, a confidence number per pixel, and, when
you pass several photos, the camera positions as well. That confidence is worth
having, because most depth models give you no way to
tell a good pixel from a bad one. What you supply is the focal length in pixels,
from your camera calibration, and the conversion above.

### 5.3 Prompt Depth Anything

Prompt Depth Anything is **worth betting on**, because it settles the argument
between a learned model and a depth sensor by using both, and that is the shape
the problem has on a real arm. The paper is [Prompting Depth Anything for 4K
Resolution Accurate Metric Depth Estimation](https://arxiv.org/abs/2412.14015),
from December 2024, and its abstract reports that the result helps "generalized
robotic grasping".

Size s, a small card, Apache-2.0 for the code and the weights.

You give the model a colour photo and a coarse depth image, and the sensor's
reading steers the model to a sharp depth map in metres.

The one idea is in the name. The sensor's coarse depth is handed to the model as a
**prompt**, which here means an extra input that steers an existing model rather
than a new model trained for a new job. The abstract puts it as using a low-cost
laser depth sensor as the prompt that guides the Depth Anything model towards an
accurate answer in metres.

What changes inside, compared with section 5.1, is only where that extra input
enters. It is not pasted over the answer at the end, and it is not used to scale
the answer afterwards. The abstract describes a prompt fusion design that brings
the sensor's depth into the depth decoder at several scales, so the measured
metres influence the answer at every level of detail, from the coarse layout of
the scene down to the fine edges. Compare that with the alternative of fitting a
section 5.1 output to a few measured points: that fit is one multiplication and
one addition applied to the whole picture, so an error that varies from one part
of the scene to another survives it untouched.

What this buys is the sensor's scale together with the model's sharpness, at a
resolution far above what the sensor itself produces. What it costs is that the
model is now only as metric as the sensor. With no depth image to hand it falls
back to relative monocular depth, and you are back in section 5.1 with its units
problem.

On an arm the difference shows up at the rim of a thin-walled mug. The sensor
measures the table and the body of the mug in metres but smears the rim across a
wide band, and the monocular model of section 5.1 draws the rim sharply with no
idea how far away it is. The gripper closes on the rim, so neither answer is
enough, and fitting the monocular output to a few measured points does not help,
because one correction for the whole picture cannot fix a rim whose error differs
from the table's. This model's answer at the rim is steered by the measurements
around it, which is the case it was built for.

The obvious alternative is the monocular route of section 5.1, followed by fitting
the result to a few measured points. That fitting is one correction for the whole
picture, so it cannot repair a scale that drifts across the scene. Prompt Depth
Anything uses the sensor's measurements everywhere at once, so pick it whenever you
already own a depth camera. Against the camera alone, it gives you the camera's
metres with the model's sharp object edges.

The thing that most often goes wrong is the units in your own code, because the
model returns metres and depth cameras usually report millimetres, so a factor of
a thousand is easy to lose.

The library is `transformers`, and the call differs from section 5.1 by one
argument.

```python
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

name = "depth-anything/prompt-depth-anything-vits-hf"
processor = AutoImageProcessor.from_pretrained(name)
model = AutoModelForDepthEstimation.from_pretrained(name)

image = Image.open("glass.jpg")
coarse = Image.open("sensor_depth.png")   # the depth camera's own image

# prompt_depth is what makes the answer metric. Pass None and you get
# relative depth instead.
inputs = processor(images=image, prompt_depth=coarse, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

result = processor.post_process_depth_estimation(
    outputs, target_sizes=[(image.height, image.width)])
metres = result[0]["predicted_depth"]
```

What you still have to supply is the coarse depth image, in the same view as the
colour photo, which means your camera's colour and depth streams must already be
aligned. There is also a variant trained for transparent objects,
`prompt-depth-anything-vits-transparent-hf`, which is worth trying before you
reach for section 5.6.

### 5.4 RAFT-Stereo

RAFT-Stereo is **most used in 2026** as the first stereo model to try, and this
repository's survey calls it the sensible default.

Size not stated, a small card, MIT for the code and the weights.

It came from Princeton University in September 2021, as [RAFT-Stereo: Multilevel
Recurrent Field Transforms for Stereo
Matching](https://arxiv.org/abs/2109.07547), and it works the way section 3
described, improving its guess of the shift for every pixel over many small
rounds.

The one idea is the opposite of section 5.1's. This model measures instead of
guessing, and the only things it learned are how to compare two patches and how to
improve a guess. Nothing inside it has any opinion about how big a mug usually is
or where the floor meets the wall, and that is deliberate: everything that
determines the distance comes from the two pictures and from the gap you measured
between the cameras.

Inside, the two pictures are first lined up, so that whatever appears in a row of
the left picture appears in the same row of the right one. One encoder then
describes the patches of both pictures, and the model builds a large table of how
well each left patch matches the right patches along its row. Because of the
lining up, that search runs in one direction only, which is the difference between
this model and RAFT, the motion model on the [tracking and
motion](03_tracking-and-motion.md#56-raft-for-motion-at-every-pixel) page, where
the same machinery has to search in two. A small network with a memory of its own
previous answer then updates the whole field of shifts many times over, and in
each round it reads the match scores near where the current guess points and
nudges every shift a little. "Multilevel" in the title means those readings happen
at several coarsenesses of the table at once, so a large shift is found on the
coarse version and sharpened on the fine one. Where the monocular model of section
5.1 ends with a number that has no units, this one ends with a shift in pixels,
and step 4 of section 3 turns that shift into metres using the measured gap and
the focal length.

What this buys is metres with no scale to fit, and an accuracy you can improve by
mounting the cameras further apart. What it costs is that it can only measure what
both cameras can see and what carries distinguishing texture. A blank surface
gives the matcher nothing to compare, and the learned cleanup step then fills that
area by smoothing inwards from its edges, which looks plausible and is not a
measurement. A pixel visible to one camera only has no match at all. And since the
distance is a fixed number divided by the shift, one pixel of uncertainty in the
shift is a small error on a near object and a large one on a far one.

On an arm this is the model to pick when the grasp point is on a textured surface
and the number has to be right: a printed cardboard box gives millimetres here and
only an ordering from section 5.1. It is the model to avoid when the surfaces are
blank or clear, because the region the matcher cannot measure is filled in by the
cleanup step and looks no different from a measured region, whereas the monocular
model at least fails smoothly and in a way you can test against a known height.

The obvious alternative is OpenCV's `StereoSGBM`, which matches the two pictures
with a written algorithm and needs no model and no graphics card. That function is
the baseline every stereo paper is measured against, and on a textured scene in
good light it is often enough. Pick RAFT-Stereo when it leaves holes, which happens
on weakly textured surfaces and at the edges of objects, because the learned
matcher fills those in. The [multi-view
geometry](../../../06_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md)
page shows that written route in full.

What it costs you is the rig, because stereo needs two cameras held rigidly apart
and calibrated carefully, and the depth gets worse as soon as they shift. Its
custom CUDA kernel is optional, so the model runs without one. The thing that most
often goes wrong is the conversion from shift to distance, because the
repository's own note warns that the focal length in that formula is in pixels and
not in millimetres.

There is no package to install. You clone the
[repository](https://github.com/princeton-vl/RAFT-Stereo), download the weights
with its script, and run its demo on your own pair of pictures.

```bash
# Downloads the pretrained weights into models/
bash download_models.sh

# --save_numpy writes the shift for every pixel as a .npy file.
python demo.py \
    --restore_ckpt models/raftstereo-middlebury.pth \
    -l=left.png -r=right.png \
    --save_numpy
```

The repository recommends those Middlebury weights for everyday pictures. What you
still have to supply is the geometry, because the model gives you the shift per
pixel and you turn that into metres yourself, from the focal length in pixels and
the measured gap between the two cameras.

### 5.5 FoundationStereo

FoundationStereo is **worth betting on**, because it brings to stereo what Depth
Anything brought to one photo: a model trained so broadly that it works on scenes
unlike anything in its training set, with no retraining from you. NVIDIA published
it in January 2025, as [FoundationStereo: Zero-Shot Stereo
Matching](https://arxiv.org/abs/2501.09898), and its repository records a best
paper nomination at the 2025 Computer Vision and Pattern Recognition conference
and first place on the Middlebury and ETH3D leaderboards.

Size not stated, a big card from NVIDIA, a non-commercial NVIDIA research licence
on the weights.

The one idea is to give a stereo matcher what the monocular models know. Matching
fails exactly where there is nothing distinctive to match, and that is the hole in
section 5.4. A monocular model has an opinion about a blank surface anyway,
because it learned what such surfaces usually are, so this model feeds that
opinion into the matching rather than choosing between the two routes.

Inside, it follows the same four steps as RAFT-Stereo, with two changes. The
abstract calls the first a side-tuning feature backbone. A vision model trained on
single pictures is kept as it is, and a smaller network trained alongside it turns
that model's output into the patch descriptions that go into the match table, so a
patch is already described in terms of what a monocular model knows about that
kind of surface before any matching happens. The second change is in the cleanup:
the abstract describes long-range context reasoning for filtering the match table,
meaning the cleanup considers the table as a whole rather than each small
neighbourhood on its own. The training set is its own, about a million
computer-made stereo pairs, passed through an automatic filter that drops the
ambiguous ones.

What this buys is a stereo model that works on scenes unlike its training with no
retraining from you, and it buys it precisely in the places where RAFT-Stereo's
pure matching has nothing to go on. What it costs is work per frame, because the
model now carries a monocular backbone as well as a matcher, and it costs the
licence and the hardware described below.

On an arm the difference shows up over a bin of matte black parts under flat
light. RAFT-Stereo can barely tell one patch of that bin from the next, so its
cleanup smooths the whole area inwards from the edges, while FoundationStereo's
patch descriptions carry a monocular model's view of the surface and the parts
keep their shape. Its repository also reports that it runs on the monochrome and
infrared pair an Intel RealSense D4-series camera produces, so a depth camera you
already own becomes the stereo rig for a better model. If the cell is going to be
sold, none of that is available to you, and the answer is RAFT-Stereo with more
light or a projected pattern to add texture.

The obvious alternative is RAFT-Stereo from section 5.4. FoundationStereo is
stronger on scenes it has never seen, and its repository reports that it works on
the monochrome and infrared pictures an Intel RealSense D4-series camera produces,
which turns a depth camera you already own into a stereo pair for a better model.
Pick RAFT-Stereo anyway if your work will be sold, for the reason below.

What it costs you is the licence, and that cost is absolute. The weights come
under an NVIDIA research licence whose own words limit use to research purposes
only, so this model cannot go into a product, although the repository says a
commercial model is available from NVIDIA on request. It also needs an NVIDIA
graphics card, and this repository's page on [working without a
GPU](../../../03_frameworks/03_arm-movement/10_working-without-a-gpu.md) lists it
among the models with no route at all on other hardware.

There is no package. You clone the
[repository](https://github.com/NVlabs/FoundationStereo), download its checkpoint,
and run its demo script.

```bash
python scripts/run_demo.py \
    --left_file ./assets/left.png \
    --right_file ./assets/right.png \
    --ckpt_dir ./pretrained_models/23-51-11/model_best_bp2.pth \
    --out_dir ./test_outputs/
```

What you still have to supply, to get a point cloud rather than a picture of
shifts, is an intrinsics file. The repository states its format exactly: the first
line holds the nine numbers of the camera matrix, and the second line holds the
distance between the two cameras in metres.

### 5.6 ReMake

ReMake is **worth betting on** for clear and shiny objects, because it is the
first recent depth completion model with a licence you can use.

Size not stated, a big card, MIT for the code; the checkpoint comes from a
file-sharing link rather than a model hub.

It accompanies a 2026 paper in *IEEE Robotics and Automation Letters*,
"Rethinking Transparent Object Grasping: Depth Completion With Monocular Depth
Estimation and Instance Mask", and its
[repository](https://github.com/ChengYaofeng/ReMake) carries an MIT licence file.
It takes a monocular depth estimate and a mask of the object, and fills the
camera's missing depth inside that mask.

The one idea is to tell the network which pixels are the problem instead of making
it work that out. The project's own page makes the argument: earlier completion
models were handed the colour photo and the broken depth together and had to learn
by themselves which depth values to trust, and because the mixture of missing,
wrong and valid values changes completely with the light and the surface, a model
that learned that mixture on one dataset does badly on a real cell. The instance
mask marks the transparent object explicitly, so training only ever asks the model
to produce depth where the depth is genuinely unreliable.

Inside, three inputs are encoded separately and then fused, which is the part that
differs from every other model on this page. The colour picture with the mask
attached to it goes through a transformer. The relative depth map from a monocular
model, which is the kind of output section 5.1 produces, is encoded on its own.
The camera's own depth image is encoded on its own as well. The three sets of
features are fused and decoded into one complete depth map, and the mask is used a
second time afterwards to cut the object's points out of the cloud. Each input has
a clear job: the camera's depth carries the metres of everything around the hole,
the relative map carries how the object sits against its surroundings, and the
mask says where to replace rather than trust.

What this buys is a filled surface in the sensor's own metres, and the authors'
claim for it is generalisation to real scenes rather than a better score on a
benchmark. What it costs is a second model in front of this one, because the mask
has to come from somewhere, and that model's mistakes become depth mistakes with
nothing downstream to catch them. The filled surface is still produced by a
network, so it is a plausible surface and not a measured one.

On an arm the choice is between this and Prompt Depth Anything from section 5.3,
and it turns on how your sensor fails. Where the sensor returns nothing on the
glass, section 5.3 needs no mask, needs no segmentation model and sharpens the
whole picture at once, which is less work for the same result. Where the sensor
returns a confident wrong value on the glass, because light bounced off it into
the camera, section 5.3 has nothing that marks that value as untrustworthy and
takes it as a measurement, and that is exactly the failure ReMake's mask was
introduced to prevent.

The obvious alternative is ClearGrasp, which is still the paper everyone cites for
this problem and which was built from computer-made pictures of glass, in the way
section 4 described. It was abandoned in 2021. The other alternative, TransCG, has
the largest real dataset of clear objects and a CC BY-NC-SA 4.0 licence, so it
cannot be sold. Pick ReMake because it is
maintained, permissive and recent, and this repository's survey of [transparent and
shiny
objects](../../../02_perception/02_object-perception/04_models-that-find.md#17-transparent-and-shiny-objects)
reaches the same conclusion.

You supply the mask yourself, from a model such as the ones on the
[segmentation](../02_most-used/02_segmentation.md) page, and the project's
checkpoint comes from a file-sharing link rather than Hugging Face, so your build
cannot simply download it. The thing that most often goes wrong is that the filled
surface is invented, so a glass lying on its side can be filled in as a glass
standing up.

There is no package and no Python entry point. You clone the repository, place
its checkpoint, and run its scripts.

```bash
# Fill the depth for one set of pictures.
bash ./scripts/inference.sh

# The same thing on a live Intel RealSense D435 camera.
bash ./scripts/realworld_inference.sh
```

What you still have to supply is the configuration file those scripts read, the
mask, and the camera's own depth image. If that is more work than you want, try the
transparent variant of Prompt Depth Anything first, because it needs only
`transformers`.

### 5.7 How to choose

Start from the sensor, not from the model. If the robot has a depth camera and the
objects are ordinary, use the camera's own depth and add no model at all, because a depth camera is more accurate than any monocular model.

Six things change that.

- The camera's depth is coarse or noisy, and you want sharp edges in metres. Then
  add Prompt Depth Anything from section 5.3, which keeps the camera's scale.
- The objects are glass or chrome, so the camera returns holes. Then segment the
  object and fill the holes with ReMake from section 5.6, or try the transparent
  variant of Prompt Depth Anything first.
- There is no depth camera, but you can mount two cameras and measure the gap
  between them. Then use RAFT-Stereo from section 5.4, or OpenCV's `StereoSGBM` if
  your scene is well textured.
- You need the strongest stereo result and you are not selling the product. Then
  use FoundationStereo from section 5.5, and read its licence first.
- There is one colour camera and you need metres. Then use `DA3METRIC-LARGE` from
  section 5.2, or MoGe-2, and expect to check the numbers against something real.
- There is one colour camera and you only need to know what is in front of what.
  Then use Depth Anything V2 Small from section 5.1, which is the cheapest answer
  on this page.

Whichever you choose, do not let a learned depth value be the last word before the
gripper closes.

---

## 6. Where this is going

This section is about what to expect from learned depth next. Of the three
subjects in this part of the chapter it is the one with a genuinely positive
forward view, because depth from pictures has improved fast enough to replace
hardware in shipping products, and this section names where.

Everything below is labelled by what kind of claim it is, using the four kinds
that Book 3 sets out in [four kinds of claim, and why the difference decides
everything](../../../03_frameworks/08_frontier/06_what-is-coming.md#1-four-kinds-of-claim-and-why-the-difference-decides-everything).
A demonstration shows something working once, a product announcement says
something can be bought or downloaded, a research result is a measured number
under a stated protocol, and a projection is a statement about a date that has
not arrived. Product announcements carry the most weight because you can check
them, and projections the least. Where I give my own judgement the sentence says
so, and every link below was checked on 4 October 2026.

### 6.1 How it got here

The shape of the change is that depth stopped being a measurement and became a
prediction. Stereo depth used to be a geometry calculation written by hand,
matching patches between two pictures, and it worked where there was texture and
failed where there was not. Then training one network on many datasets whose
units did not agree gave relative depth from a single photo of almost any scene,
which is the MiDaS lineage that [section 5](#5-well-known-models) describes.
Metric depth, several pictures at once, and the sharpening of a sensor's own
reading all followed from that same idea. What is left unresolved is the part
geometry gave you for free, which is the scale.

### 6.2 Where it is used in industry today

The clearest case of a learned model replacing a hand-written one inside a
product is Stereolabs, which sells the ZED depth cameras. Its current
documentation says the three neural modes `NEURAL`, `NEURAL_LIGHT` and
`NEURAL_PLUS` are the ones to choose between in ZED SDK version 5, and that the
older computer-vision modes `PERFORMANCE`, `QUALITY` and `ULTRA` "are deprecated
since ZED SDK 5.0 but still available in the API" ([ZED depth
modes](https://www.stereolabs.com/docs/depth-sensing/depth-modes)). That is a
product announcement, and it is the strongest single fact in this section: a
camera company deprecated its own classical stereo algorithm in favour of
networks. NVIDIA ships the same idea for robots as `isaac_ros_ess`, a learned
stereo node in Isaac ROS whose documentation says the model predicts the
disparity of each pixel from a stereo image pair
([isaac_ros_dnn_stereo_depth](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_dnn_stereo_depth)),
and which you can download today.

Monocular depth replacing a depth sensor outright has happened at consumer
scale. Google's ARCore Depth API computes depth from the motion of a single
camera, and Google's own page says it "uses a depth-from-motion algorithm to
create depth images and merges data from available hardware sensors" ([ARCore
Depth API](https://developers.google.com/ar/develop/depth)). The hardware depth
sensor is an optional extra there rather than the source. That is a product
announcement, and it covers a large number of Android phones. In vehicles, Tesla
removed the ultrasonic distance sensors from new Model 3 and Model Y production
in October 2022 and replaced their output with a camera-based occupancy
prediction. Its "Transitioning to Tesla Vision" support page is the source, and
I am naming it without a link because tesla.com refuses automated requests, so I
have no checked link to show you. Mobileye sells SuperVision, a camera-based
driver-assistance system, and its own announcement says SuperVision will be in
future Porsche production models ([Mobileye and
Porsche](https://www.mobileye.com/news/porsche-mobileye-supervision-collaboration/)).
In drones, the Skydio X10 page says "six custom-designed navigation lenses
provide 360-degree visibility" and does not mention lidar anywhere ([Skydio
X10](https://www.skydio.com/x10)), so obstacle avoidance there is vision only.

Depth sensors are not dying, and a section that only listed the replacements
would mislead you. RealSense completed its spin-out from Intel in July 2025 with
50 million dollars of funding to keep building depth cameras for robotics
([RealSense
spin-out](https://www.intelcapital.com/realsense-completes-spin-out-from-intel-raises-50-million-to-accelerate-ai-powered-vision-for-robotics-and-biometrics/)),
and Luxonis sells cameras that run stereo and networks on the camera itself
([DepthAI documentation](https://docs.luxonis.com/)). Those are product
announcements too. Meanwhile platform vendors are packaging monocular depth for
on-device use: Apple publishes a Core ML conversion of Depth Anything V2 Small
([apple/coreml-depth-anything-v2-small](https://huggingface.co/apple/coreml-depth-anything-v2-small)),
which is a download rather than a claim.

### 6.3 What is being worked on right now

The first front is metric depth from one picture, meaning depth in metres rather
than in order. The difficulty is that one picture does not contain its own
scale, so these models learn a prior over how large things usually are and how a
given focal length maps to a given size. Depth Anything 3 from [section
5.2](#52-depth-anything-3) is one line of attack, and the others you will meet
are UniDepth ([UniDepth](https://github.com/lpiccinelli-eth/UniDepth)), Metric3D
([Metric3D](https://github.com/YvanYin/Metric3D)) and MoGe
([MoGe](https://github.com/microsoft/MoGe)). All three publish code and numbers.

The second front is reconstructing a scene from several pictures without knowing
where the cameras were. VGGT infers camera parameters, depth maps, point maps
and point tracks in one forward pass, and its repository records a best paper
award at CVPR 2025 ([VGGT](https://github.com/facebookresearch/vggt)). For a
robot this matters because the work it removes is calibration, which is a task
that takes engineers days and that every new camera arrangement needs again.

The third front is consistency over time. A single-frame depth model gives a
slightly different answer on each frame of a still scene, and a plan computed
from a flickering depth map makes the arm move when nothing moved. Video Depth
Anything addresses exactly this, as a research result with open weights ([Video
Depth Anything](https://github.com/DepthAnything/Video-Depth-Anything)).

The fourth front combines a sensor with a model instead of choosing between
them, which is Prompt Depth Anything from [section
5.3](#53-prompt-depth-anything). The sensor supplies the scale it measured and
the model supplies the sharp edges it predicted. Alongside it, hard surfaces are
a front of their own: ClearGrasp began the work on transparent objects
([ClearGrasp](https://sites.google.com/view/cleargrasp)) and ReMake from
[section 5.6](#56-remake) is the current answer. Apple's Depth Pro is worth
knowing as well, because it targets sharp object boundaries from one image with
open weights ([ml-depth-pro](https://github.com/apple/ml-depth-pro)).

### 6.4 What is still unsolved

Scale from a single camera is not a gap in effort, it is a property of the
problem. Two scenes that differ only in size can produce the same picture, so
any model that prints metres has made an assumption about how large things are.
That assumption is usually right about chairs and doorways and usually wrong
about a custom fixture on a bench, and there is no amount of training that
removes the ambiguity. Treat a metric number from one camera as a good starting
guess and never as a measurement.

Accuracy at the point where the gripper closes is the number that decides
whether depth is usable for picking, and it is not the number these models are
ranked on. Published comparisons report average error over a whole image, while
a grasp depends on a few square centimetres, often on a thin or shiny part.
Papers that add depth to a manipulation policy exist, such as "Depth Helps"
([Depth Helps](https://arxiv.org/abs/2408.05107)) and 3D-CAVLA
([3D-CAVLA](https://arxiv.org/abs/2505.05800)), but I did not find a published
study that reports grasp success as a function of depth error on a stated set of
objects, which is the measurement a developer would want before removing a
sensor.

Three categories of surface stay unreliable for every model on this page: thin
structures such as cables and wire baskets, polished metal, and dark matte
material that returns almost no light. ReMake exists because of the second of
those, and [section 5.7](#57-how-to-choose) still tells you to segment the
object first, so the problem is handled rather than solved. Uncertainty is the
fourth gap. Most models output one number per pixel and nothing about how sure
they are, so nothing tells the planner which pixels to distrust, and I did not
find a monocular depth model that publishes a calibrated per-pixel uncertainty.

### 6.5 The next two to three years

Everything in this part is my expectation rather than anybody's announcement,
and each item gives its reason, because the reason is the content and the
prediction on its own is noise.

I expect learned stereo to become the default inside depth cameras and robot
stacks rather than an option you switch on. This is the best-supported item
here, and the reason is that it is already most of the way done by a route that
does not depend on anybody's roadmap: the hardware is unchanged, the change is a
software update, and the vendor has already deprecated the alternative. A
deprecation that has shipped is much stronger evidence than a promise, so I
would bet on this item before any of the others.

I expect monocular metric depth to keep displacing depth sensors where cost or
shape decides the design, and not to displace them where accuracy decides it.
The reason is in the two halves of this section. ARCore and the vehicle examples
show that a model is good enough when the job is to know a wall is two metres
away and the alternative costs money, power and space. The scale argument of
[section 6.4](#64-what-is-still-unsolved) shows why the same model is not good
enough to put a gripper on a specific edge. My expectation is therefore split:
cheap mobile robots and inspection devices drop the depth camera, and arms doing
precise picking keep it.

I expect pose-free multi-view reconstruction to become a standard block in robot
perception, the way a detector already is. The reason is the labour it removes
rather than the accuracy it adds. Calibrating several cameras into one frame is
a task that every cell needs and nobody enjoys, and a model that infers the
camera parameters from the pictures removes it. The code is already open, so
this is a prediction about adoption rather than about a capability arriving.

I expect the winning arrangement on a robot arm to be a sensor and a model
together rather than either alone, with the sensor supplying scale and the model
supplying edges and filled holes. The reason is that this is the only
arrangement whose weak points do not overlap, and Prompt Depth Anything shows it
can be built. This is my judgement, and the way to check it is to watch whether
depth camera vendors ship this combination in their own software development
kits rather than leaving it to users.

The last expectation is about licences rather than accuracy, and I think it will
decide more adoption than any benchmark. The table in [section
5](#5-well-known-models) shows the pattern already: several of the strongest
checkpoints are released under non-commercial terms while the smaller ones are
Apache-2.0. A company shipping a product will use the weaker model it is allowed
to sell, so the practical state of the art in industry will keep lagging the
published state of the art, and the gap will be a licence rather than a
capability.

---

## 7. Where to read next

- [Keypoints and object pose](../02_most-used/04_keypoints-and-object-pose.md) is the page before
  this one, and most pose models need good depth.
- [Open-vocabulary models](../02_most-used/03_open-vocabulary-models.md) is the next page, and it
  shows how to find an object from words before you measure it.
- [Point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md) and
  [shape completion](../../04_3d-models/03_also-used/01_shape-completion.md) work on the 3D points a
  depth map turns into.
- [Running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains why a GPU matters and how fast a model must be.
- For the sensors themselves, read
  [the sensors, and the software for each](../../../02_perception/02_object-perception/02_sensors.md).
- For measured accuracy and licences, read
  [models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md).
