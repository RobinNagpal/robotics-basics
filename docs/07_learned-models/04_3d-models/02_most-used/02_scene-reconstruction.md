# Scene reconstruction: NeRF and Gaussian splatting

This page is about building a whole 3D scene from many ordinary photos. The two
best-known methods for it are called NeRF and Gaussian splatting. So the page answers
four questions. What do these methods build, and how do they turn flat photos into
3D? Why must they be fitted again for every new scene? And when is this worth doing
on a robot arm that already has a depth camera?

It is for a reader who has read the [chapter overview](../01_overview.md), and who
knows what a point cloud is. You should also know, from
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md), that training
means adjusting a model a little at a time until its answers match the examples.

> Before this page, it helps to have read [multi-view geometry](../../../06_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md), which explains how lines of sight from known camera places cross at a point. NeRF and Gaussian splatting use the same idea with many photos.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Step 1: know where each photo was taken](#step-1-know-where-each-photo-was-taken)
   · [Step 2 with NeRF: a network that answers questions about any spot](#step-2-with-nerf-a-network-that-answers-questions-about-any-spot)
   · [Step 2 with Gaussian splatting: many soft blobs](#step-2-with-gaussian-splatting-many-soft-blobs)
   · [Step 3: fit it to the photos](#step-3-fit-it-to-the-photos)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
   · [5.1 The NeRF line: the original and Instant-NGP](#51-the-nerf-line-the-original-and-instant-ngp)
   · [5.2 3D Gaussian Splatting](#52-3d-gaussian-splatting)
   · [5.3 Nerfstudio](#53-nerfstudio)
   · [5.4 NeuS](#54-neus)
   · [5.5 VGGT and the DUSt3R family](#55-vggt-and-the-dust3r-family)
   · [5.6 How to choose](#56-how-to-choose)
6. [A worked example: grasping a drinking glass](#6-a-worked-example-grasping-a-drinking-glass)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than a depth camera, and what it costs](#8-why-this-rather-than-a-depth-camera-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

The introduction named two methods, so this section says what they both build. Scene
reconstruction builds one 3D description of a scene from many photos taken from
different places, so that you can draw the scene from any point of view.

For example, think of walking round a statue with a phone and taking a photo every
few steps. Each photo on its own is flat, but together the photos hold enough to work
out the whole shape of the statue. A spot on the statue's nose shows up in many
photos, each time from a different direction, and where those directions cross is
where the nose is.

A NeRF or a Gaussian splat stores the result in a form that can draw a new photo from
any place, even a place where no photo was taken. It can also draw a depth picture
from that place, which says how far away each surface is.

---

## 2. What goes in and what comes out

Because the scene is built from photos rather than measured directly, what goes in is
two things.

- **Many photos of the same scene**, taken from different places, and tens of photos
    is common. The photos can come from an ordinary colour camera, so no depth camera
    is needed.
- **Where the camera was for each photo**, and which way it pointed. This is the
    camera's **pose**, which is three numbers for its position and three for its
    direction.

![A wrist camera takes pictures of a mug from many known places](../../../images/3d-models/scene-reconstruction/pictures-from-many-places.svg)

The arm carries its camera round the mug and takes ten photos. Its joint readings say
exactly where the camera was for each one.

What comes out is one stored scene, and it will give you:

- a new colour photo from any camera pose you choose,
- a depth picture from any camera pose, which turns into a point cloud in the usual way,
- a surface, if you run one more program to pull a surface out of it.

---

## 3. How it works inside

### Step 1: know where each photo was taken

Everything depends on knowing the camera pose for each photo, and there are two ways
to get it.

A robot arm has the easier of the two ways. If the camera sits on the wrist, then the
arm's joint
readings say where the wrist was, and so where the camera was, with no extra work.
Book 2 points this out in
[models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not).
It also means the scene comes out at its real size, in metres.

Without an arm, a program such as COLMAP works out the poses from the photos alone.
It finds the same small spots in many photos and works back to where each camera must
have been. This takes time, and the result has no real size until you
measure something in the scene. COLMAP is not one of the models in
[section 5](#5-well-known-models), but it is the step in front of most of them, and
[section 5.3](#53-nerfstudio) recommends the toolkit that runs it for you.

### Step 2 with NeRF: a network that answers questions about any spot

**NeRF** stands for **neural radiance field**, where "radiance" means the light and
colour that comes from a spot. So a NeRF is one neural network that answers a
question about any spot in the scene.

- You give it the `x`, `y` and `z` of a spot, and the direction you are looking from.
- It gives back two things: how solid that spot is, and what colour it looks from that
  direction.

How solid a spot is comes back as a number, where zero means empty air and a large
number means the spot is inside something that blocks light. The direction matters
for the colour, because a shiny surface looks different from different sides.

To draw one pixel of a photo, NeRF then follows the line of sight from the camera
through that pixel and out into the scene.

![One pixel's line of sight passes through air, the near wall of a mug, and a far wall](../../../images/3d-models/scene-reconstruction/a-ray-through-the-scene.svg)

The network is asked about each point along the line. The first solid point gives the
pixel its colour, and the points hidden behind it count for almost nothing.

The steps for one pixel are the four below.

1. Pick points along the line, from near the camera to far away.
2. Ask the network about each point, which means how solid it is and what colour it
    is.
3. Walk along the line from the camera, where points in empty air add nothing and the
    first solid point adds most of the colour. Points behind it add very little,
    because the solid point blocks the view.
4. Add all those contributions together, and the total is the colour of the pixel.

That same walk also gives the depth of the pixel, which is the distance to where the
line first becomes solid.

The original NeRF is described here because it is the clearest version of this idea,
and not because you should run it.
[Section 5.1](#51-the-nerf-line-the-original-and-instant-ngp) calls it historical and
names the models to use instead. One variation on it is worth knowing now, because the
shortlist recommends it. Instead of asking the network how solid a point is, you can
ask how far that point is from the nearest surface, and the surface is then exactly the
set of points where that distance is zero. That is NeuS, in
[section 5.4](#54-neus), and it is how this design gives back a surface you can
measure.

### Step 2 with Gaussian splatting: many soft blobs

Instead of a network, **Gaussian splatting** stores the scene as a long list of small
soft blobs, and it uses no network at all to draw. The word "Gaussian" is the name of
the smooth bell shape that each blob's edge fades with. The word "splatting" is the
name for drawing each blob flat onto the picture, one after another.

![A mug drawn normally, and the same mug stored as many soft blobs](../../../images/3d-models/scene-reconstruction/mug-made-of-blobs.svg)

Each blob stores a place, a size, a direction, a colour and how see-through it is.
Thousands of them drawn over each other make the picture.

To draw a photo, the program sorts the blobs from near to far and paints them onto
the picture, so that near blobs cover far ones. This is much faster than asking a
network about many points along every line of sight, which means a splat can be drawn
many times a second.

Gaussian splatting is therefore not a neural network at all. It belongs in this book
because it is fitted in the same way, from the same inputs, and because robot teams
use it for the same jobs as NeRF. It is also the method the shortlist points you at
first. [Section 5.2](#52-3d-gaussian-splatting) covers the paper that everybody means
by "splatting", and [section 5.3](#53-nerfstudio) recommends the toolkit to run it
with on a real job.

### Step 3: fit it to the photos

Whichever of the two you use, both methods start with a scene that is wrong. A NeRF
starts with random numbers inside its network, while a splat starts with blobs in
rough places. Then the program repeats these steps many thousands of times.

1. Pick one of the real photos and its camera pose.
2. Draw the scene from that same pose.
3. Compare the drawing with the real photo, pixel by pixel.
4. Adjust the network, or the blobs, a little so the drawing gets closer to the photo.

When the drawings match all the photos, the scene is finished, because it must now be
right from every direction that had a photo. Since the photos came from all round,
the only way to match them all is to have the shape in the right place.

One entry in the shortlist does none of this. VGGT, in
[section 5.5](#55-vggt-and-the-dust3r-family), is trained once on many scenes
beforehand, so you hand it a few photos and it answers straight away, with no fitting
and no camera poses of your own. [Section 4](#4-how-it-is-trained) explains the
difference between the two ways of training.

---

## 4. How it is trained

The word "trained" means something different here from the other pages in this book.
Most models are trained once, on a large collection of examples, and then used on new
inputs. Instead, a NeRF or a splat is fitted to **one** scene and knows only that
scene. So if the arm moves a cup, the old fit is out of date and a new one is needed.

The data is just the photos and the poses, and nobody labels anything, because the
photos are the right answers and the drawings are the guesses.

The first NeRF took hours or days of computing on a graphics card to fit one scene,
and later methods cut that sharply. Instant-NGP and Gaussian splatting can fit a
small scene in minutes on a good graphics card.

There is also a newer kind of model that is trained once, in the ordinary way, from
many thousands of scenes. Then, given a few photos of a new scene, it gives the 3D
points straight away with no fitting at all. DUSt3R, in the next section, is one of
these.

---

## 5. Well-known models

Both methods above exist as code you can download, and this section is the shortlist.
It says what each one is best at, what it costs you, and what to type to run it, and
it answers the question the two methods raise: which of them is ready for a work cell
and which is still a research result.

Read the table as a first pass, then read the sub-section for the one or two you are
considering. The left column names the project and says how current it is. The right
column holds everything that decides between them: what the project is best at, how
big the download is, what its licence allows, and when to pick it. The download part
means different things in different rows, because a fitted scene is not a trained
model. Most of these projects ship code and no weights, so what you download is a
program that then needs a graphics card and hours of your time, while the last row
ships a trained model in the ordinary sense. Every licence below was read from the
project's own licence file.

| Model | What decides it |
| --- | --- |
| [NeRF](https://github.com/bmild/nerf) and [Instant-NGP](https://github.com/NVlabs/instant-ngp), historical | They give you a field you can ask about any point in space. The download is code only, with no weights, and the licence is MIT for NeRF and NVIDIA's research-and-evaluation-only terms for Instant-NGP. Pick them when the scene is transparent or shiny and pictures are not enough. |
| [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting), most used in 2026 | It is best at new views of a still scene, drawn fast. The download is code only, although the authors' set of fitted scenes is a separate 14 GB download, and the Inria and Max Planck licence is research only. Pick it when you are reproducing the paper's results. |
| [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio), most used in 2026 | It runs either method on your own photos. It installs with `pip install` under Apache-2.0, and fitting needs about 6 GB of graphics memory, or 12 GB for the larger setting. Pick it when this is a real job in a real work cell. |
| [NeuS](https://github.com/Totoro97/NeuS), most used in 2026 | It gives you a measured surface you can ship. The download is code only, with no weights, and the licence is MIT. Pick it when you need a surface in millimetres rather than a picture. |
| [VGGT](https://github.com/facebookresearch/vggt), worth betting on | It gives you 3D from a few photos with no fitting at all. The download is 5.0 GB, with about 1.26 billion learned numbers, and the code allows commercial use while the open checkpoint does not. Pick it when you cannot wait minutes for a fit. |

### 5.1 The NeRF line: the original and Instant-NGP

Both of these are **historical**. They are here because the original is the design
that [section 3](#step-2-with-nerf-a-network-that-answers-questions-about-any-spot)
explains, and because together they show why the field then moved on. Ben Mildenhall
and five colleagues published NeRF at the 2020 European Conference on Computer Vision:
one small network, asked about points along each line of sight. NVIDIA's Instant-NGP
followed in the ACM Transactions on Graphics in July 2022. It keeps that design but
moves most of what the network knows into a lookup table indexed by position, so the
network itself becomes small and quick to ask, and that is what cut fitting from the
original's hours or days per scene, as [section 4](#4-how-it-is-trained) says, down to
minutes.

The obvious alternative is 3D Gaussian Splatting in section 5.2, and for a new job
that is what to choose. A NeRF still wins in one case. It keeps a real radiance field,
which means a network you can ask about any point in space, and the transparent-object
trick in [section 6](#6-a-worked-example-grasping-a-drinking-glass) depends on exactly
that. A splat has no network to ask, so what it gives you is pictures and a depth
picture worked out from the blobs. The one robot result worth knowing from this
generation is [Dex-NeRF](https://arxiv.org/abs/2110.14217), by Jeffrey Ichnowski and
colleagues at the 2021 Conference on Robot Learning, which is the method section 6
describes.

What they cost you is time, and for Instant-NGP a licence as well. The original is MIT
licensed and asks for TensorFlow 1.15, so you will use somebody's reimplementation
rather than the authors' code. It is still the one worth reading, because at about
1,100 lines across two files it is the only version of this idea you can read end to
end in an afternoon. Instant-NGP has the opposite problem. Its code is fast, but the
NVIDIA Source Code License allows use for research and evaluation only, in its own
words non-commercially, so you cannot put it in a product, and because it is CUDA it
needs an NVIDIA card. Book 2 records the same restriction for Neuralangelo, which is
the most accurate radiance-field method in
[its table](../../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not)
and also NVIDIA's. That pattern is the thing to notice about this corner of the
field.

There is no short Python call for either of them, because fitting is the run. If you
want this design without the licence problem, nerfstudio reimplements it, so the
command is `ns-train instant-ngp` and section 5.3 covers that toolkit. Its
[Instant-NGP page](https://docs.nerf.studio/nerfology/methods/instant_ngp.html) is
honest that the reimplementation covers the main ideas rather than every detail.

### 5.2 3D Gaussian Splatting

Three-dimensional Gaussian splatting is **most used in 2026**, and when people say
"splatting" today they mean this paper. Bernhard Kerbl, Georgios Kopanas, Thomas
Leimkühler and George Drettakis published it in 2023, at Inria in France and the Max
Planck Institute for Informatics in Germany. It is the soft blobs described in
[section 3](#step-2-with-gaussian-splatting-many-soft-blobs), with no network
anywhere in the drawing step.

The obvious alternative is a NeRF, and this is the comparison the whole page turns on.
The paper's own claim is the reason splatting won: 30 frames a second or more at
1080p picture size, which no NeRF method reached for whole scenes, while also matching
the best NeRF quality. Drawing a blob is rasterisation, the same operation a graphics
card does for triangles in a game, so it is not a saving of a few percent: it is a
different kind of work from asking a network about points along a line.

What it costs you is the licence first of all. The Inria and Max Planck licence is
research only, and
[Book 2's reconstruction table](../../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not)
shows that almost the whole family of surface-oriented variants inherits it. Then the
hardware: the repository asks for a graphics card of compute capability 7.0 or higher
and 24 GB of graphics memory to reach the quality in the paper, which is more than a
laptop has. Then the accuracy, which is the fault people miss. The same table
measures plain Gaussian splatting at 1.96 mm of error on a laboratory object about
25 cm across, the worst of every method in it, because a blob centre is not a point on
the surface.

There is no Python call, because fitting is the run, and these are the repository's
own commands.

```bash
# Work out where each photo was taken, with COLMAP, and undistort the photos.
# Your photos go in <scene>/input/ first.
python convert.py -s <scene>

# Fit the blobs to the photos. This is the long step.
python train.py -s <scene>

# Draw the scene again from every photo's pose, into images on disk.
python render.py -m <path to the trained model>
```

The repository gives you the fitting, the fast drawing and a viewer. You supply the
photos and the 24 GB graphics card. You also supply the real size, because COLMAP
recovers the camera poses only up to an unknown scale, and
[section 4.2 of Book 2's page](../../../02_perception/02_object-perception/05_models-that-measure.md#42-and-none-of-it-has-a-scale)
explains the fix: give the fitting your arm's own camera poses, which are already in
metres. For a real job, use section 5.3 rather than these commands, because the
licence there is one you can keep.

### 5.3 Nerfstudio

Nerfstudio is **most used in 2026** for actual work, and it is the answer to "which of
these is practical in a work cell". It is an open-source toolkit that fits both NeRFs
and splats behind one set of commands, under the Apache-2.0 licence. Its splatting
model is called splatfacto and its NeRF model is called nerfacto, and the drawing is
done by [gsplat](https://github.com/nerfstudio-project/gsplat), a separate Apache-2.0
library that reimplements the splatting rasteriser.

The obvious alternative is the original code in section 5.2. Nerfstudio wins for one
reason that outranks every technical argument: its licence permits commercial use and
the Inria licence does not, so this is the version you can put in a product. Two
practical reasons follow. Switching between a NeRF and a splat becomes one word on the
command line, and the toolkit does the whole preparation step, including running
COLMAP for you.

What it costs you is that splatfacto is not the paper. Nerfstudio's own documentation
says it is a blend of several splatting methods and that it will drift away from the
original as features are added, so published numbers are not what you will get. The
memory it needs is documented:
about 6 GB of graphics memory for splatfacto and about 12 GB for splatfacto-big, which
keeps more blobs and runs slower. The most common failure is upstream of nerfstudio
entirely: COLMAP fails on blurry photos or photos that barely overlap, and then
nothing after it works.

The toolkit is driven from the command line, and these are its
[documented commands](https://docs.nerf.studio/quickstart/first_nerf.html).

```bash
# Recover the camera poses from the photos, and write a dataset nerfstudio reads.
ns-process-data images --data photos/ --output-dir processed/

# Fit a splat. Use `ns-train nerfacto` here instead to fit a NeRF.
ns-train splatfacto --data processed/

# Write the result out as a point cloud that Open3D and PCL can read.
ns-export pointcloud --load-config outputs/processed/splatfacto/<run>/config.yml \
    --output-dir exports/pcd/
```

The toolkit gives you the pose recovery, the fitting, a viewer in the browser and the
export. You supply the photos, which means a program of your own that moves the arm to
tens of viewpoints and saves a picture at each one, and you supply everything after
the export, where the result is an ordinary point cloud and the
[point cloud models page](01_point-cloud-models.md) applies. One detail decides
whether the numbers mean anything: a splat fitted from COLMAP poses is in the scene's
own units, so feed nerfstudio the poses from your arm's joint readings, or measure one
known distance in the export and scale by what you find.

### 5.4 NeuS

NeuS is **most used in 2026** for the one job that splats are bad at, which is giving
back a surface you can measure and then ship. Peng Wang and colleagues published it in
2021. It is a NeRF-shaped method with one change: instead of asking the network how
solid a point is, it asks how far that point is from the nearest surface, and a
surface is then exactly the set of points where that distance is zero.

The obvious alternative is Gaussian splatting, and the reason to leave it is the fault
named in [section 7](#7-what-goes-wrong). A blob centre is placed to make pictures
look right, so it is not a point on the object, while NeuS has a surface by
construction and writes it out as a mesh. Book 2's table measures NeuS at 0.84 mm
against 1.96 mm for plain Gaussian splatting on the same laboratory objects, and NeuS
is MIT licensed while that whole splatting family is not. Accuracy together with a
licence you can keep is an unusual combination in this field, and it is why this
sub-section exists.

What it costs you is fitting time. NeuS is a NeRF underneath with none of
Instant-NGP's acceleration, so expect the hours that
[section 4](#4-how-it-is-trained) describes rather than splatting's minutes. It also
wants more of you before it starts: the camera poses have to be supplied in a specific
file format, and the quality improves if you also supply a mask marking the object in
each photo. The repository was written for PyTorch 1.8, so expect to pin old versions
or to port it.

NeuS is run from the command line, and these are the repository's own commands.

```bash
# Fit the scene. womask.conf is the setting for photos with no object masks.
python exp_runner.py --mode train --conf ./confs/womask.conf --case <case_name>

# Pull the surface out of the fitted network, as a mesh file.
python exp_runner.py --mode validate_mesh --conf ./confs/womask.conf \
    --case <case_name> --is_continue
```

The repository gives you the fitting and the step that turns the fitted network into a
mesh in `exp/<case_name>/<exp_name>/meshes/`. You supply the photos, the camera poses
in the file format its README describes, and the masks if you want the better result.
You also supply the scale, for the same reason as every other row here.

### 5.5 VGGT and the DUSt3R family

VGGT is **worth betting on**, because it removes the step that makes everything above
awkward for a robot: there is no fitting. It is a model trained once, in the ordinary
way, on many scenes, so you hand it photos and it answers. The Visual Geometry Group
at the University of Oxford and Meta published it at CVPR 2025, where it won the best
paper award. It follows DUSt3R and MASt3R, from Naver, which did the same thing for
two photos at a time; VGGT takes one photo, a few, or hundreds, and returns the camera
poses, a depth picture per photo and 3D points, all at once.

The obvious alternative is everything above, and the comparison is not about quality.
It is that fitting a scene costs minutes while this answers, in the paper's own words,
in under a second, and that it needs no camera poses as input, because it works them
out itself. For an arm that must look and then act, that difference decides whether
the method can be used at all. Against DUSt3R and MASt3R specifically, pick VGGT
because it takes many photos in one pass rather than pairs that then have to be
stitched together, and because its licence is better, as the next paragraph
explains.

What it costs you is the licence, read carefully, and this is exactly the trap this
book exists to point out. Since July 2025 the repository's code licence permits
commercial use, excluding military use. The weights are a separate matter: the open
`VGGT-1B` checkpoint stays non-commercial, and there is a second checkpoint,
`VGGT-1B-Commercial`, which you may use commercially but which is handed out through
an application form. DUSt3R and MASt3R are simpler and stricter, because both are
Creative Commons Attribution-NonCommercial-ShareAlike 4.0, so neither is shippable in
any form. The other
costs are size and accuracy. The checkpoint is 5.0 GB with about 1.26 billion learned
numbers, so it needs a serious graphics card, and a model that answers in one pass is
less accurate than minutes of fitting against your own photos.

The package downloads the checkpoint from Hugging Face.

```python
import torch
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images

model = VGGT.from_pretrained("facebook/VGGT-1B").cuda()   # 5.0 GB on first run

images = load_and_preprocess_images(["view0.png", "view1.png", "view2.png"]).cuda()

with torch.no_grad():
    # bfloat16 halves the memory on recent cards and costs little accuracy.
    with torch.cuda.amp.autocast(dtype=torch.bfloat16):
        out = model(images)   # camera poses, depth per photo and 3D point maps
```

The model gives you the poses, the depth and the points, so it replaces both
[step 1](#step-1-know-where-each-photo-was-taken) and the fitting of
[step 3](#step-3-fit-it-to-the-photos). You supply the photos and the scale, which is
unknown here as everywhere else on this page. One route is worth knowing: the
repository ships a script that writes VGGT's answer in COLMAP's format, which
nerfstudio and gsplat read directly, so you can use VGGT to skip COLMAP and still fit
a splat afterwards.

### 5.6 How to choose

For a real job, fit a splat with nerfstudio. Its licence lets you ship, it runs both
methods, and it does the pose recovery for you.

Four things change that choice.

- **You need a measurement rather than a picture.** Use NeuS, and expect hours
  instead of minutes. A splat is accurate enough to look at and not accurate enough
  to grasp from, which is the 0.84 mm against 1.96 mm in Book 2's table.
- **The arm cannot wait.** Use VGGT, which answers in under a second instead of
  fitting for minutes, and check the checkpoint licence before it reaches a product.
- **You are reproducing a published result.** Use the original code of whichever
  paper it is, and accept its licence, because a reimplementation drifts away from
  the paper it started from, which is what nerfstudio's documentation says about
  splatfacto.
- **You want a splat with a clean licence and no CUDA.**
  [Brush](https://github.com/ArthurBrussee/brush) is an Apache-2.0 splat trainer that
  runs on other makes of graphics card, and Book 2 lists it among the few shippable
  options in this family.

One point about all of them, because it is the mistake that wastes the most time.
None of these methods knows the real size of anything, since photographs measure
directions and not distances. On an arm you already have the answer, because the
joint readings say where the camera was in metres for each photo, so feed those poses
in rather than letting COLMAP guess them. Nothing you build on top of a reconstruction
is worth anything until that is done.

---

## 6. A worked example: grasping a drinking glass

The clearest case for all this is an object a depth camera cannot see, so here an arm
has to pick up a clear drinking glass from a table with a depth camera on its wrist.
The depth camera's light passes straight through the glass, so the point cloud shows
the table where the glass should be. That means a
[point cloud model](01_point-cloud-models.md) has nothing to work with.

Here are the five steps in which scene reconstruction solves it.

1. The arm moves its wrist camera along an arc round the glass, as in the picture in
    section 2, and it takes a colour photo at each stop.
2. At each stop the software saves the joint readings, and from them it works out the
    camera pose for that photo.
3. A NeRF is fitted to the photos and poses. The edges of the glass bend and reflect
    light in a way that changes from photo to photo, so to match all the photos the
    NeRF has to put something solid where the glass is.
4. The software asks the NeRF for a depth picture from a camera pose straight above
    the glass, and now the glass has depth readings.
5. That depth picture becomes a point cloud, and a grasp model chooses where to put
    the fingers. The [grasp models chapter](../../05_grasp-models/01_overview.md)
    takes over from there.

This is the idea behind Dex-NeRF. The whole job takes much longer than one depth
shot, because the arm has to move and the NeRF has to be fitted. So it is worth it
only when the depth camera cannot see the object.

---

## 7. What goes wrong

That example worked because the glass stayed where it was, and five things go wrong
when conditions are less kind.

**The scene must stay still.** Fitting assumes every photo shows the same scene, so
if something moves between photos the fit gets confused and draws blurry or doubled
objects. Even a person walking past in the background can spoil it.

**Too few views.** With only a few photos, the method can match them all with the
wrong shape. Small bits of fog or stray blobs then appear floating in the air.
They look fine from the photo positions and wrong from anywhere else, so more photos
from more directions is the main fix.

**Bad camera poses.** If the poses are off, the lines of sight from different photos
do not meet in the right places, and the result is blurry. On an arm this comes from
poor calibration between the camera and the wrist, and Book 2 covers that calibration
in [the sensors document](../../../02_perception/02_object-perception/02_sensors.md).

**A splat is not a surface.** The blobs are placed to make the pictures look right,
so their centres are not points on the real surface. Book 2 measured plain Gaussian
splatting as the least accurate method in its table. So if you need a surface to
grasp, use a variant made for surfaces, or ask for a depth picture and check it.

**It is slow.** Even fast methods take seconds to minutes to fit, which is far too
slow for an arm that has to react to things moving. Scene reconstruction therefore
suits jobs where the arm can stop, look carefully, and then act.

---

## 8. Why this rather than a depth camera, and what it costs

Since the list above is long, it is worth setting out what this buys you. Scene
reconstruction **is** a way to build one 3D scene from many photos with known camera
poses. It **does** give the arm a scene it can view from any direction, including
depth where a depth camera fails.

The obvious alternative is a depth camera, with no fitting at all, because it gives a
point cloud in one shot, many times a second. If you need more sides, then you take
depth shots from several places and merge the point clouds.

So why fit a scene instead?

- A depth camera fails on see-through, shiny and very dark surfaces, while scene
    reconstruction works from colour photos and uses the fact that these surfaces
    look different from different sides.
- It fills the gaps between views, because merged point clouds have holes and
    overlaps while a fitted scene is one smooth whole.
- It works with a plain colour camera, which is cheaper and smaller than a depth
    camera on a small arm.
- It can draw realistic new photos, so teams use it to make extra training pictures
    for other models from views the camera never took.

What it costs you comes in the four parts below.

- Time, because the arm has to move round the scene and the fit has to run, which is
    seconds at best and often minutes.
- A graphics card, since fitting on an ordinary processor is very slow.
- The scene must not change while you fit it, and the fit is thrown away when it
    does.
- Licences, because much of the Gaussian splatting code is for research only, so
    check before you build a product on it.

So use a depth camera for everyday picking, and use scene reconstruction when the
depth camera cannot see the object, or when you need a detailed, complete model of a
scene that will stay still.

---

## 9. The written alternative

Instead of fitting a scene, Book 5 builds 3D from many views with written methods.
[Multi-view geometry](../../../06_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md)
finds points seen from two or more known camera places, and measures the height of
glass from how far its outline shifts. Then
[volumetric maps](../../../06_programming-techniques/05_image-and-point-cloud-processing/03_also-used/02_volumetric-maps.md)
combine many depth pictures into one map of small cubes, each marked free, occupied
or not yet seen, and
[iterative closest point](../../../06_programming-techniques/03_searching-and-matching/02_most-used/02_iterative-closest-point.md)
lines up point clouds taken from several places to remove small errors in the camera
poses. These need no fitting and no graphics card, and they give measured shapes.
Instead, scene reconstruction wins when the arm needs new pictures from views it
never took, or when a clear or shiny object gives neither depth readings nor a sharp
outline.

---

## 10. Where to read next

- [3D feature maps](../03_also-used/02_3d-feature-maps.md) is the next page, and it
    adds meaning to a reconstructed scene so that the arm can find things in it by
    name.
- [Depth from pictures](../../03_seeing-models/03_also-used/02_depth-from-pictures.md)
    guesses depth from one or two photos with no fitting, so it is faster and less
    accurate.
- [Models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md)
    in Book 2 compares the accuracy and licences of many reconstruction methods.
- [Simulation and evaluation, section 5.3](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#53-real-to-sim-rebuilding-the-room-instead-of-modelling-it)
    in Book 3 uses Gaussian splats to rebuild a real room inside a simulator.
