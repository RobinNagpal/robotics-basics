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

> Before this page, it helps to have read [multi-view geometry](../../../05_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md), which explains how lines of sight from known camera places cross at a point. NeRF and Gaussian splatting use the same idea with many photos.

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
measure something in the scene.

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
use it for the same jobs as NeRF.

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

Both methods above appear in tools you can download, and these are the real ones that
robot teams use.

- **NeRF** (2020) was the first neural radiance field, and it showed that one network,
    fitted to photos, can draw new views of a scene with fine detail.
- **Instant-NGP** (2022), from NVIDIA, stores most of what the network knows in a
    fast lookup table, which made fitting a NeRF far faster.
- **3D Gaussian Splatting** (2023), from the Inria research institute in France,
    introduced the soft blobs described above, and it can draw new views in real time
    on a good graphics card. Its code has a research-only licence, and Book 2 lists
    the licences of this whole family in
    [models that measure](../../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not).
- **Nerfstudio** is an open-source toolkit, with an Apache-2.0 licence, that fits
    both NeRFs and splats with the same commands.
- **Dex-NeRF** (2021) used a NeRF to find and grasp transparent objects with a robot
    arm, where a depth camera gives no usable points.
- **DUSt3R** (2024) is instead trained once on many scenes, so that from two or more
    photos of a new scene it gives 3D points for every pixel, even when the camera
    poses are unknown.

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
[Multi-view geometry](../../../05_programming-techniques/02_geometry-and-cameras/03_also-used/01_multi-view-geometry.md)
finds points seen from two or more known camera places, and measures the height of
glass from how far its outline shifts. Then
[volumetric maps](../../../05_programming-techniques/05_image-and-point-cloud-processing/03_also-used/02_volumetric-maps.md)
combine many depth pictures into one map of small cubes, each marked free, occupied
or not yet seen, and
[iterative closest point](../../../05_programming-techniques/03_searching-and-matching/02_most-used/02_iterative-closest-point.md)
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
