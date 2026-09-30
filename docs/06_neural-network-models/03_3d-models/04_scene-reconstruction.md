# Scene reconstruction: NeRF and Gaussian splatting

This page is about building a whole 3D scene from many ordinary photos. The two
best-known methods are called NeRF and Gaussian splatting. This page answers four
questions. What do these methods build? How do they turn flat photos into 3D? Why must
they be fitted again for every new scene? And when is this worth doing on a robot arm
that already has a depth camera?

It is for a reader who has read the [chapter overview](01_overview.md). You should
know what a point cloud is, and, from
[how a model learns](../01_what-models-are/02_how-a-model-learns.md), that training
means adjusting a model a little at a time until its answers match the examples.

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
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

Scene reconstruction builds one 3D description of a scene from many photos taken from
different places, so that you can draw the scene from any point of view.

Think of walking round a statue with a phone and taking a photo every few steps. Each
photo is flat. But together, the photos hold enough to work out the whole shape of the
statue. A spot on the statue's nose shows up in many photos, each time from a
different direction. Where those directions cross is where the nose is.

A NeRF or a Gaussian splat stores the result in a form that can draw a new photo from
any place, even a place where no photo was taken. It can also draw a depth picture
from that place, which says how far away each surface is.

---

## 2. What goes in and what comes out

What goes in is two things.

- **Many photos of the same scene**, taken from different places. Tens of photos is
  common. The photos can come from an ordinary colour camera. No depth camera is
  needed.
- **Where the camera was for each photo**, and which way it pointed. This is the
  camera's **pose**: three numbers for its position and three for its direction.

![A wrist camera takes pictures of a mug from many known places](../../images/3d-models/scene-reconstruction/pictures-from-many-places.svg)

The arm carries its camera round the mug and takes ten photos, and its joint readings
say exactly where the camera was for each one.

What comes out is a stored scene. From it you can get:

- a new colour photo from any camera pose you choose,
- a depth picture from any camera pose, which turns into a point cloud in the usual way,
- a surface, if you run one more program to pull a surface out of it.

---

## 3. How it works inside

### Step 1: know where each photo was taken

Everything depends on knowing the camera pose for each photo. There are two ways to
get it.

A robot arm has an easy way. If the camera sits on the wrist, the arm's joint readings
say where the wrist was, and so where the camera was, with no extra work.
Book 2 points this out in
[models that measure](../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not).
It also means the scene comes out at its real size, in metres.

Without an arm, a program such as COLMAP works out the poses from the photos alone. It
finds the same small spots in many photos and works back to where each camera must
have been. This takes time, and the result has no real size until you measure
something in the scene.

### Step 2 with NeRF: a network that answers questions about any spot

**NeRF** stands for **neural radiance field**. "Radiance" here means the light and
colour that comes from a spot. A NeRF is one neural network that answers a question
about any spot in the scene.

- You give it the `x`, `y` and `z` of a spot, and the direction you are looking from.
- It gives back two things: how solid that spot is, and what colour it looks from that
  direction.

"How solid" is a number. Zero means empty air. A large number means the spot is inside
something that blocks light. The direction matters for colour because a shiny surface
looks different from different sides.

To draw one pixel of a photo, NeRF follows the line of sight from the camera through
that pixel, out into the scene.

![One pixel's line of sight passes through air, the near wall of a mug, and a far wall](../../images/3d-models/scene-reconstruction/a-ray-through-the-scene.svg)

The network is asked about each point along the line; the first solid point gives the
pixel its colour, and the points hidden behind it count for almost nothing.

The steps for one pixel are:

1. Pick points along the line, from near the camera to far away.
2. Ask the network about each point: how solid is it, and what colour is it?
3. Walk along the line from the camera. Points in empty air add nothing. The first
   solid point adds most of the colour. Points behind it add very little, because the
   solid point blocks the view.
4. The total is the colour of the pixel.

The same walk also gives the depth of the pixel. It is the distance to where the line
first becomes solid.

### Step 2 with Gaussian splatting: many soft blobs

**Gaussian splatting** stores the scene in a different way. It uses no network at all
to draw. The scene is a long list of small soft blobs. The word "Gaussian" is the name
of the smooth bell shape that each blob's edge fades with. "Splatting" is the name for
drawing each blob flat onto the picture, one after another.

![A mug drawn normally, and the same mug stored as many soft blobs](../../images/3d-models/scene-reconstruction/mug-made-of-blobs.svg)

Each blob stores a place, a size, a direction, a colour and how see-through it is, and
thousands of them drawn over each other make the picture.

To draw a photo, the program sorts the blobs from near to far and paints them onto the
picture. Near blobs cover far ones. This is much faster than asking a network about
many points along every line of sight, so a splat can be drawn many times a second.

Gaussian splatting is not a neural network. It belongs in this book because it is
fitted in the same way, from the same inputs, and robot teams use it for the same
jobs as NeRF.

### Step 3: fit it to the photos

Both methods start with a scene that is wrong. A NeRF starts with random numbers
inside its network. A splat starts with blobs in rough places. Then the program
repeats these steps many thousands of times:

1. Pick one of the real photos and its camera pose.
2. Draw the scene from that same pose.
3. Compare the drawing with the real photo, pixel by pixel.
4. Adjust the network, or the blobs, a little so the drawing gets closer to the photo.

When the drawings match all the photos, the scene is finished. It must now be right
from every direction that had a photo. Because the photos came from all round, the
only way to match them all is to have the shape in the right place.

---

## 4. How it is trained

Here "trained" means something different from the other pages in this book. Most
models are trained once, on a large collection of examples, and then used on new
inputs. A NeRF or a splat is fitted to **one** scene. It knows only that scene. If the
arm moves a cup, the old fit is out of date and a new one is needed.

The data is just the photos and the poses. Nobody labels anything. The photos are the
right answers, and the drawings are the guesses.

The first NeRF took hours to days of computing on a graphics card to fit one scene.
Later methods cut this sharply. Instant-NGP and Gaussian splatting can fit a small
scene in minutes on a good graphics card.

There is also a newer kind of model that is trained once, the ordinary way. It learns
from many thousands of scenes. Then, given a few photos of a new scene, it gives the 3D
points straight away with no fitting. DUSt3R, in the next section, is one of these.

---

## 5. Well-known models

These are real methods and tools that robot teams use.

- **NeRF** (2020) was the first neural radiance field. It showed that one network,
  fitted to photos, can draw new views of a scene with fine detail.
- **Instant-NGP** (2022), from NVIDIA, stores most of what the network knows in a
  fast lookup table. This made fitting a NeRF far faster.
- **3D Gaussian Splatting** (2023), from the Inria research institute in France,
  introduced the soft blobs described above. It can draw new views in real time on a
  good graphics card. Its code has a research-only licence. Book 2 lists the licences
  of this whole family in
  [models that measure](../../02_perception/02_object-perception/05_models-that-measure.md#4-reconstruction-when-you-do-not).
- **Nerfstudio** is an open-source toolkit, with an Apache-2.0 licence, that fits both
  NeRFs and splats with the same commands.
- **Dex-NeRF** (2021) used a NeRF to find and grasp transparent objects with a robot
  arm, where a depth camera gives no usable points.
- **DUSt3R** (2024) is trained once on many scenes. From two or more photos of a new
  scene, it gives 3D points for every pixel, even when the camera poses are unknown.

---

## 6. A worked example: grasping a drinking glass

An arm has to pick up a clear drinking glass from a table. The arm has a depth camera
on its wrist. The depth camera's light passes straight through the glass, so the point
cloud shows the table where the glass should be. A
[point cloud model](02_point-cloud-models.md) has nothing to work with.

Here is how scene reconstruction solves it.

1. The arm moves its wrist camera along an arc round the glass, as in the picture in
   section 2. It takes a colour photo at each stop.
2. At each stop, the software saves the joint readings. From them it works out the
   camera pose for that photo.
3. A NeRF is fitted to the photos and poses. The edges of the glass bend and reflect
   light in a way that changes from photo to photo. To match all the photos, the NeRF
   has to put something solid where the glass is.
4. The software asks the NeRF for a depth picture from a camera pose straight above
   the glass. Now the glass has depth readings.
5. That depth picture becomes a point cloud, and a grasp model chooses where to put
   the fingers. The [grasp models chapter](../04_grasp-models/01_overview.md) takes
   over from here.

This is the idea behind Dex-NeRF. The whole job takes much longer than one depth shot,
because the arm has to move and the NeRF has to be fitted. It is worth it only when
the depth camera cannot see the object.

---

## 7. What goes wrong

**The scene must stay still.** Fitting assumes every photo shows the same scene. If
something moves between photos, the fit gets confused and draws blurry or doubled
objects. A person walking past in the background can spoil it.

**Too few views.** With only a few photos, the method can match them all with the
wrong shape. Small bits of fog or stray blobs appear floating in the air. They look
fine from the photo positions and wrong from anywhere else. More photos from more
directions is the main fix.

**Bad camera poses.** If the poses are off, the lines of sight from different photos
do not meet in the right places. The result is blurry. On an arm this comes from poor
calibration between the camera and the wrist. Book 2 covers this calibration in
[the sensors document](../../02_perception/02_object-perception/02_sensors.md).

**A splat is not a surface.** The blobs are placed to make the pictures look right.
Their centres are not points on the real surface. Book 2 measured plain Gaussian
splatting as the least accurate method in its table. If you need a surface to grasp,
use a variant made for surfaces, or ask for a depth picture and check it.

**It is slow.** Even fast methods take seconds to minutes to fit. That is far too slow
for an arm that has to react to things moving. Scene reconstruction suits jobs where
the arm can stop, look carefully, and then act.

---

## 8. Why this rather than a depth camera, and what it costs

Scene reconstruction **is** a way to build one 3D scene from many photos with known
camera poses. It **does** give the arm a scene it can view from any direction,
including depth where a depth camera fails.

The obvious alternative is a depth camera, with no fitting at all. It gives a point
cloud in one shot, many times a second. If you need more sides, you take depth shots
from several places and merge the point clouds.

Why fit a scene instead?

- A depth camera fails on see-through, shiny and very dark surfaces. Scene
  reconstruction works from colour photos, and it uses the fact that these surfaces
  look different from different sides.
- It fills gaps between views. Merged point clouds have holes and overlaps.
  A fitted scene is one smooth whole.
- It works with a plain colour camera. That is cheaper and smaller than a depth camera
  on a small arm.
- It can draw realistic new photos. Teams use this to make extra training pictures
  for other models from views the camera never took.

What does it cost you?

- Time. The arm has to move round the scene, and the fit has to run. This is seconds
  at best, and often minutes.
- A graphics card. Fitting on an ordinary processor is very slow.
- The scene must not change while you fit it, and the fit is thrown away when it does.
- Licences. Much of the Gaussian splatting code is for research only. Check before you
  build a product on it.

So use a depth camera for everyday picking, and use scene reconstruction when the
depth camera cannot see the object, or when you need a detailed, complete model of a
scene that will stay still.

---

## 9. Where to read next

- [3D feature maps](05_3d-feature-maps.md) is the next page. It adds meaning to a
  reconstructed scene, so the arm can find things in it by name.
- [Depth from pictures](../02_seeing-models/06_depth-from-pictures.md) guesses depth
  from one or two photos, with no fitting. It is faster and less accurate.
- [Models that measure](../../02_perception/02_object-perception/05_models-that-measure.md)
  in Book 2 compares the accuracy and licences of many reconstruction methods.
- [Simulation and evaluation, section 5.3](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#53-real-to-sim-rebuilding-the-room-instead-of-modelling-it)
  in Book 3 uses Gaussian splats to rebuild a real room inside a simulator.
