# Tracking and motion

This page answers one question: how does a model follow things from one video frame
to the next? A robot arm often needs to know not only where something is, but also
how it is moving, and whether the thing it sees now is the same thing it saw a
moment ago.

It is written for a reader who has already read the earlier pages of this
chapter, so you should know what a detection box and a segmentation outline are,
from [object detection](../02_most-used/01_object-detection.md) and
[segmentation](../02_most-used/02_segmentation.md). Every other page in this
chapter looks at one photo at a time, whereas this page looks at a video, which
is a series of photos, called **frames**, taken one after another. It covers
three kinds of model: optical flow, point tracking and object tracking.

> Before this page, it helps to have read the [Kalman filter](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/03_kalman-filter.md) and [assignment and matching](../../../06_programming-techniques/03_searching-and-matching/02_most-used/03_assignment-and-matching.md). The object trackers in section 3 are built from both: the filter predicts where each object will be, and assignment pairs each new box with an object.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: picking a box off a moving belt](#6-a-worked-example-picking-a-box-off-a-moving-belt)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

The one-sentence idea is this: a tracking model compares frames of a video and says
where each pixel, point or object from one frame has gone in the next.

Here is an everyday example: watch a ball roll across a floor, and you do not
see a new ball in every moment, because you see one ball that moves. You also
know which way it is going and roughly how fast. So a tracking model gives a
robot those same two things: the same identity over time, and the motion.

There are three kinds, from the finest to the coarsest.

- **Optical flow** says, for every pixel in one frame, where that pixel moved to in
  the next frame, and it works on two frames at a time.
- **Point tracking** follows a chosen set of points, such as a few dots on a mug,
  through many frames, and it keeps following them even when they are hidden for a
  while.
- **Object tracking** follows whole objects, as boxes or outlines, through many
  frames, and it gives each object a number that stays the same while the object is
  in view.

---

## 2. What goes in and what comes out

Because those three kinds work at different levels of detail, they also take and
give different things, so the table below compares them. Read each row as: what
goes in, what comes out, and what a robot arm uses it for.

| Kind | What goes in | What comes out | A typical use on an arm |
| --- | --- | --- | --- |
| Optical flow | two frames next to each other | an arrow for every pixel: how far it moved and which way | spotting what moved, for example a person's hand entering the scene |
| Point tracking | a video and some starting points | each point's position in every frame, and whether it is visible | following parts of a cloth, or the corner of a lid, while the arm moves it |
| Object tracking | a video, and boxes or outlines from a detector or a click | each object's box or outline in every frame, with the same number each time | picking an object off a moving belt, or keeping count of objects in a bin |

For optical flow, the output is often drawn as arrows on a grid, where each arrow
starts where a pixel was and points to where it went.

![Two frames and the optical flow between them](../../../images/seeing-models/tracking-and-motion/optical-flow-arrows.svg)

Only the box moved, so only its pixels get arrows, and the still mug and wall get
dots.

For point tracking, the output is a path for each point, plus a yes or no for
whether the point can be seen in each frame.

![Three points on a mug followed through four frames](../../../images/seeing-models/tracking-and-motion/tracked-points-through-frames.svg)

The gripper lifts and turns the mug, and the model keeps following the blue point
even while a finger hides it.

For object tracking, the output is a box or an outline per object per frame,
together with a number for each object that stays the same.

![Two identical mugs keep their numbers](../../../images/seeing-models/tracking-and-motion/same-id-across-frames.svg)

Mug 1 goes behind the box and comes out again, and the tracker still calls it
mug 1, not a new mug.

---

## 3. How it works inside

### Optical flow

A modern optical flow model, such as RAFT, works in these steps.

1. An encoder turns each of the two frames into a grid of small embeddings, where an
   **embedding** is a list of numbers that describes a small patch of the picture.
2. The model then compares every patch in frame 1 with every patch in frame 2, and
   stores how alike each pair is, because patches that look alike are likely to be
   the same bit of the world.
3. It starts with a guess that nothing moved at all.
4. It improves that guess in many small rounds, and in each round it looks at how
   well the current guess matches the stored comparisons, and adjusts each arrow a
   little.
5. After enough rounds, it outputs the final arrow for every pixel.

The small rounds in step 4 are what made RAFT accurate, and the same idea is
used by RAFT-Stereo on the [depth from pictures](02_depth-from-pictures.md)
page, because finding the shift between two stereo photos is the same problem as
finding motion between two frames.

### Point tracking

However, a point tracker must follow a point over many frames rather than only
two, and it must also keep going when the point is hidden.

1. For each starting point, the model records what the picture looks like around
   it.
2. In each new frame, it then searches for the patch that looks most like that
   record.
3. It does not decide each frame alone, because it looks at a window of frames
   together, so that the path stays smooth and makes sense over time.
4. When a point is hidden, the model marks it as not visible, but it still guesses
   where the point is, from the path so far and from the other points around it.

CoTracker makes that last idea stronger, because it tracks many points together, so
if one point on a mug is hidden, the other points on the same mug help place it.

### Object tracking

Most object trackers for robots use a method called **tracking by detection**.

1. A detector finds boxes in every frame, but it does not know which box in this
   frame matches which box in the last frame.
2. So a **predictor** guesses where each known object should be now, from where it
   was and how fast it was moving. A common predictor is the **Kalman filter**, an
   ordinary program that keeps a best guess of position and speed and updates it
   with each new measurement, and it is not a neural network.
3. The tracker then matches each new box to the nearest predicted position, and this
   step is called **association**.
4. A matched box keeps its object's number, while a box with no match becomes a new
   object. A known object with no box is kept for a few frames as "hidden", with its
   predicted position, in case it comes back.

Some trackers also compare how the objects look, using an embedding for each
box, so that they can tell apart two objects that pass close to each other. SAM
2 works differently, because you click once on an object in one frame, and it
then keeps a memory of what the object looked like and draws the outline in
every later frame.

---

## 4. How it is trained

Training data for motion is hard to get from real videos, because no person can
label where every pixel moved between two frames, and even labelling a few points
through a long video is slow.

So most of these models start with computer-made videos instead. A program moves 3D
objects around a scene and renders the frames, and because the program moved the
objects, it knows exactly where every pixel went.

- **Flying Chairs** is a well-known example for optical flow, and it is made of
  pictures of chairs pasted onto background photos and moved around. It looks
  nothing like a real room, yet flow models trained on it work on real videos.
- **Kubric** is a program from Google that renders scenes of objects falling and
  bouncing, and point trackers such as TAPIR learned from videos made with it.
- Some newer point trackers, such as CoTracker3, add real videos later, because a
  trained model labels the real videos itself and the new model then learns from
  those labels. This is the same pseudo-labelling idea described in
  [depth from pictures](02_depth-from-pictures.md#4-how-it-is-trained).

Instead, object trackers mostly reuse a trained detector, and the tracking step
on top is often plain code, so it needs no training at all. Trackers that
compare how objects look are trained on videos where people have drawn boxes and
numbered the objects in every frame.

---

## 5. Well-known models

It helps to see those ideas in real models, and the list below gives them in
order: the first two do optical flow, the next three follow points, and the last
two follow objects.

- **FlowNet** was one of the first convolutional neural networks (CNNs) for optical
  flow, and its authors made the Flying Chairs dataset to train it.
- **RAFT** (Recurrent All-Pairs Field Transforms) improves its flow arrows in many
  small rounds, as section 3 describes, and many later flow and stereo models build
  on its design.
- **PIPs** (Persistent Independent Particles) follows points through a window of
  frames, and it keeps going through short hidden spells.
- **TAPIR**, from Google DeepMind, follows any point you choose through a video,
  because it first finds a rough match in each frame and then refines it.
- **CoTracker**, from Meta, follows many points together, so each point helps place
  the others, and it does well when points are hidden.
- **SORT** and **ByteTrack** are tracking-by-detection methods, so they take boxes
  from any detector and link them over time with a predictor and matching.
- **SAM 2**, from Meta, follows the outline of an object you clicked on, through a
  video, as described on the
  [open-vocabulary models](../02_most-used/03_open-vocabulary-models.md) page.

Pose models can track too, because
[FoundationPose](../02_most-used/04_keypoints-and-object-pose.md#5-well-known-models)
can follow an object's full six-number pose from frame to frame in a video.

---

## 6. A worked example: picking a box off a moving belt

Tracking earns its place whenever the robot must act on a moving thing, so here
is a worked example. A conveyor belt carries boxes past a robot arm, and the arm
must pick each box as it passes without stopping the belt, while a camera above
the belt films the boxes.

1. A detector finds each box in each frame.
2. An object tracker gives each box a number and keeps it the same while the box
   moves along, which stops the robot from treating one box as a new box in every
   frame.
3. From the box's position in several frames, the tracker then works out its speed
   along the belt.
4. The robot picks the next box to grab, and predicts where that box will be in,
   say, one second, when the gripper can get there.
5. The arm moves to that predicted spot, matches the belt's speed for a moment, and
   closes the gripper.
6. The tracker keeps watching, so if the box stopped or slipped and the prediction
   is wrong, the robot sees this in time and corrects its path, or else lets that
   box go by.

Point tracking fits other jobs instead, because when the arm folds a towel, a
point tracker can follow the corners of the towel as they move and fold under
each other, so the robot can then tell whether a corner ended up where it
should. Some research systems go further, because they predict where points
should move in a video of the task, and then move the arm to make them move that
way. The [movement models chapter](../../06_movement-models/01_overview.md)
covers how models choose arm motions.

---

## 7. What goes wrong

Useful as tracking is, it fails in a few common ways, and the list below gives
them.

- **Swapped identities.** Two similar objects pass close to each other, and the
  tracker gives each one the other's number, so the robot then picks the wrong one.
  People reduce this with a good predictor and by comparing how the objects look.
- **Objects hidden too long.** A tracker keeps a hidden object for only a few
  frames, so if the object stays hidden longer, it comes back with a new number.
- **Fast motion and blur.** If an object moves a long way between frames, or the
  picture is blurred, the models lose it, although a faster camera helps.
- **The camera moves too.** On a wrist camera, the whole picture moves every time
  the arm moves, so optical flow then shows motion everywhere. The robot must remove
  the motion caused by its own arm, which it knows from its joint readings, before
  it can see what really moved.
- **Plain surfaces.** A flat white surface has nothing to follow, so flow and point
  tracking get confused on it.
- **Gaps between views.** SAM 2 and most trackers expect a smooth video, so if the
  arm takes a photo, moves to a new place, and takes another photo, there is no
  video in between and the tracker cannot bridge that gap. The deeper document
  [tracking and association](../../../02_perception/02_object-perception/10_tracking-and-association.md#36-mask-propagation-in-video-and-where-sam-2-actually-fits)
  explains this in detail.

---

## 8. Why this kind, and what it costs

Now that you have seen what tracking does and where it fails, this section answers
four questions: what these models are, what they do for you, why you would choose
them over the obvious alternative, and what they cost.

Tracking models follow pixels, points or objects from one frame of a video to the
next. So they give the robot both motion and identity. The robot can then tell how
fast something is moving, predict where it will be, and know that the mug it sees
now is the one it saw before.

The obvious alternative is to run a detector on every frame and treat each frame
alone, which is simpler and often enough when nothing on the table moves. However,
it fails as soon as there are two similar objects, because the robot cannot tell
which is which from one frame, and it also cannot see speed, because speed needs at
least two frames. So tracking is worth adding when things move, when objects look
alike, or when the robot must act on the same object over time.

The costs are these. Optical flow and point tracking models need a GPU and add
delay, because they must wait for at least one more frame. Then there is the
risk that a tracker swaps identities without any warning, and most of them need
a smooth video rather than a few separate photos. Finally, every tracker needs
something else, either a detector or a click, to tell it what to follow in the
first place.

---

## 9. The written alternative

Object tracking is already mostly written code, because a [Kalman
filter](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/03_kalman-filter.md)
predicts where each object will be, and [assignment and
matching](../../../06_programming-techniques/03_searching-and-matching/02_most-used/03_assignment-and-matching.md)
decides which new box belongs to which object. So a tracker such as SORT needs
no training beyond its detector. To follow one coloured object with no detector
at all, the mean shift method on the
[clustering](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
page moves a window to the matching pixels in each new frame. The written way
wins for a few objects that move smoothly, such as boxes on a belt, while the
optical flow and point tracking models win when the robot must follow every
pixel, or points on something that bends, such as a towel, and keep them through
hidden spells.

---

## 10. Where to read next

- [Open-vocabulary models](../02_most-used/03_open-vocabulary-models.md) is the page before this
  one, and it shows where SAM 2 comes from, and how to choose the object to follow.
- [Keypoints and object pose](../02_most-used/04_keypoints-and-object-pose.md) explains the
  six-number pose that some trackers follow.
- [Video prediction models](../../08_world-models/03_also-used/01_video-prediction-models.md) go
  one step further, because they predict future frames rather than only following
  the current ones.
- [Movement models](../../06_movement-models/01_overview.md) use tracked motion to
  choose what the arm does next.
- For the matching problem in full detail, read
  [tracking and association](../../../02_perception/02_object-perception/10_tracking-and-association.md).

---

## 11. Using it in Python

The page has separated two jobs: following an object, which needs one number that
stays with it, and measuring motion pixel by pixel with optical flow. This section
shows the Python for both. After reading it you will be able to give each object on
a moving belt a number that stays the same from frame to frame, which is the thing
a robot arm actually needs.

Ultralytics does tracking by detection, which [section 3](#3-how-it-works-inside)
described, by running a detector on each frame and matching the boxes.

```python
import cv2
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
camera = cv2.VideoCapture(0)

while True:
    ok, frame = camera.read()
    if not ok:
        break

    # persist=True tells the tracker that this frame follows the last one.
    result = model.track(frame, persist=True, tracker="bytetrack.yaml",
                         verbose=False)[0]

    # There are no ids on a frame where nothing was detected.
    if result.boxes.id is None:
        continue
    for box in result.boxes:
        middle_u, middle_v, width, height = box.xywh[0].tolist()
        print(int(box.id), result.names[int(box.cls)], round(middle_u), round(middle_v))
```

For optical flow rather than boxes, torchvision has RAFT with pretrained weights:
`from torchvision.models.optical_flow import raft_large, Raft_Large_Weights`, then
`model = raft_large(weights=Raft_Large_Weights.DEFAULT)`. Calling it on two frames
returns a list of flow fields, one per round of refinement, and the last one in the
list is the best.

What the pretrained parts give you out of the box is both halves of the pipeline
without training anything. The detector is the COCO detector from the
[object detection](../02_most-used/01_object-detection.md) page, and the matching
step is ByteTrack, which is plain code with a motion predictor rather than a
learned model, so it needs no training data at all. Swapping `bytetrack.yaml` for
`botsort.yaml` changes the matching rules without changing a line of your program.

What you still have to write yourself is everything that depends on your belt. The
tracker gives you a number and a box per frame, so you keep a short history of each
number, fit a speed to it in pixels per second, convert that to metres per second
with the camera's calibration, and work out where the object will be when the arm
arrives. You also write the rule for what to do when an id disappears, because a
robot that reaches for a vanished id will hit the belt.

What you have to decide is which tracker configuration to use and how long to keep
an id alive after the object is no longer seen. Keeping it too long invents objects
that have left the view, and dropping it too soon gives one box a new number every
few frames, which breaks any speed you measured. You also have to accept that ids
are not guaranteed, because two objects that pass each other can swap numbers, so
anything that must not be confused needs a second check, such as comparing colour
or size before the arm commits to a pick.
