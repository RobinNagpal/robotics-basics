# Force and slip models

This page answers one question: how can a robot tell that an object in its fingers
is starting to slide out, early enough to do something about it? To answer that, it
explains the force signals a model reads, how a slip model works and is trained,
the models people have published, and why this job is harder than it looks.

It is written for a reader who has already read
[touch sensing models](../03_also-used/01_touch-sensing-models.md), because this page
uses the moving dots from its section 4.3. You should also know from
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md) what it means
to train a model on examples.

> Before this page, it helps to have read [sensor
> streams](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md),
> which explains windows of readings, smoothing, rates of change and thresholds that
> do not flicker. A slip model reads the same kind of window.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [What slip looks like in the signal](#3-what-slip-looks-like-in-the-signal)
4. [How it works inside](#4-how-it-works-inside)
5. [How it is trained](#5-how-it-is-trained)
6. [Well-known models](#6-well-known-models)
7. [A worked example: carrying a wet mug](#7-a-worked-example-carrying-a-wet-mug)
8. [What goes wrong](#8-what-goes-wrong)
9. [Why this rather than the obvious alternative, and what it costs](#9-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
10. [The written alternative](#10-the-written-alternative)
11. [Where to read next](#11-where-to-read-next)
12. [Using it in Python](#12-using-it-in-python)

---

## 1. What it is

A slip model reads the force signals from a gripper over a short stretch of time
and says whether the held object is starting to slide.

Here is an everyday example of the same skill in a person. You carry a full glass of
water, and your hand is a little wet. You feel a tiny slide on your fingertips before
the glass moves far, so without thinking you squeeze a bit harder, and the glass
stays put. In other words, you did not wait to see it fall.

So a slip model tries to give a robot that same early warning. The word **slip** means
that the object moves relative to the fingers, and the useful moment to catch it is
the very start, which is called **incipient slip**. "Incipient" means just
beginning, and at that moment squeezing a little harder still works. However, a
second later the object is already on the floor.

This page also covers the wider family of **force models**, which do a related job.
These read force signals and say something else about the contact, such as how the
object is sitting in the fingers, or whether a part has clicked into place. However,
slip is the most common job, so the page uses it as the main example.

## 2. What goes in and what comes out

Now that slip has a name, here is what the model actually reads. The input is a
short window of recent sensor readings, where a **window** means the last few
tenths of a second of readings, taken together. Those readings can come from
several different sensors:

- A tactile sensor on the finger pad, as a short run of tactile pictures, or the
  positions of the printed dots in each picture.
- A force sensor on the finger pad, giving the push straight in and the push
  sideways at each moment.
- A force-torque sensor at the wrist, giving six numbers at each moment: a push
  along three directions and a twist about three directions.
- A small vibration sensor, called an accelerometer, near the finger.

Then the output is usually one of two things. The first is a yes-or-no answer,
"slipping" or "not slipping", and the second is a number between 0 and 1 that says
how likely a slip is. In the second case the program then compares that number with
a limit it chooses.

Some force models give other outputs, such as "the grasp will hold" or "the part is
seated", but they all work in the same way.

## 3. What slip looks like in the signal

The last section said what goes in and out, and this section shows what the signal
itself looks like. A slip leaves marks in the signal, and a slip model learns to
recognise them, so it is worth seeing those marks first.

![One grip as a force trace: fingers close, lift, hold, then slip](../../../images/touch-and-body-models/force-and-slip-models/grip-force-trace.svg)

The picture is a drawn example, not a real measurement, and it shows the force on
one finger pad during one grip. The force jumps when the fingers close, and it
wobbles briefly. Then it wobbles again when the lift starts, and after that it
holds steady. When the slip starts, a fast, small shaking appears, and then the
force drops as the mug slides out.

However, two things make slip hard to spot by eye, and by a simple rule. The first is
that the jolts from closing and lifting look a lot like the shaking from slip,
because both are quick changes. So a rule that says "a quick change means slip" fires
on every lift. The second is that the drop in force comes late, because by the time
the force has clearly dropped, the object is already sliding out.

But a tactile sensor shows slip in a second way, and this one comes earlier.

![Dots on a gel pad while held, while starting to slip at the rim, and while slipping](../../../images/touch-and-body-models/force-and-slip-models/slip-starts-at-the-edge.svg)

The picture shows the dots on a gel pad at three moments. While the object is held,
the dots in the contact lean a little, all together. When slip starts, the dots at
the rim of the contact slide first, while the dots in the centre still stick, and
the rim goes first because that is where the pressure is lowest. Once the object
slips fully, every dot in the contact moves the same way.

Stage 2 is the moment a slip model tries to catch, because the centre still holds
and there is still time to squeeze harder.

## 4. How it works inside

### 4.1 One window at a time

The last section showed what slip looks like, so this section says how a model
picks it out. A slip model does not read the whole grip at once. Instead, it reads
one short window at a time, and it moves the window forward as new readings
arrive.

![A short window of the force signal going into a small network that says slip or no slip](../../../images/touch-and-body-models/force-and-slip-models/one-window-at-a-time.svg)

The picture shows two windows on the same signal. The green one covers a steady
stretch, so the network says "no slip", while the red one covers the fast shaking,
so the network says "slip", and the same network runs on every window.

The steps are these:

1. The program keeps the last few tenths of a second of readings in memory.
2. It passes that window to the model.
3. The model gives back "slip" or "no slip", or a number for how likely a slip is.
4. The program acts on the answer, and the window moves on.

The window length is a choice with a cost attached to it. A short window gives an
answer sooner, but it holds less evidence, so the model makes more mistakes.
Instead, a long window is more reliable, but its answer comes later.

### 4.2 What kind of network

The window is the same idea for every sensor, but different signals suit different
networks.

For tactile pictures, the model often uses a **convolutional neural network (CNN)**
to read each picture, as in the
[touch sensing page](../03_also-used/01_touch-sensing-models.md#42-with-learning-a-network-reads-the-picture)
. A second part then looks at how the pictures change over the window. Then a common
choice for that second part is a **long short-term memory (LSTM)** network. An LSTM
is a network that reads a sequence one step at a time and keeps a short memory of
what it has read so far.

For a force signal, which is only a few numbers at each moment, a simpler network
is often enough, because it can read the window as one list of numbers. Some models
first turn the window into a set of frequencies, which shows the fast shaking of
slip more clearly.

### 4.3 Joining touch with a camera

Some models also look at a camera picture of the object in the gripper. The camera
can see the object move a lot, while the tactile sensor can feel it move a little,
so together they catch more slips than either one alone.

## 5. How it is trained

The last section described the network, and this section says where its examples
come from. A slip model learns from windows of readings that each have the right
answer, "slip" or "no slip", and getting those answers is the hard part.

So the usual way is to cause slips on purpose, many times over, and record them. A
robot grips an object gently and lifts it, or pulls it sideways, or tilts it, so
that some of those grips hold and some slip. For each window, someone then needs to
know whether a slip was happening, and people find that out in three ways:

- They watch the object with a camera and a tracking marker. If the object moves
  relative to the fingers, that window is marked "slip".
- They use the tactile dots. If the dots in the centre of the contact move, the
  object has slipped.
- They mark it by hand from a video. This is slow and it is done for small sets
  only.

Published slip data sets are small, and they are much smaller than the data sets
for camera models, because every example costs a real grip on a real robot. That is
one reason slip models often fail on objects unlike the ones they were trained
on.

## 6. Well-known models

This area is mostly research papers rather than products, so the list below is of
papers. All of them are real and often cited.

- **Veiga and colleagues (2015)** trained a model to predict slip from a BioTac, a
  fingertip-shaped sensor filled with fluid that measures pressure and vibration.
  The robot then adjusted its grip to keep new objects from sliding.
- **Li and colleagues (2018)** joined GelSight tactile pictures with an ordinary
  camera picture. A CNN read each picture and an LSTM read how they changed over
  time. The model said whether the object was slipping.
- **"Making Sense of Vision and Touch"** (Lee and colleagues, 2019). This model
  joins a camera picture, a wrist force-torque signal and the arm's joint readings
  into one set of numbers. It was trained partly without labels, by asking the
  model to predict things such as "will the gripper touch something in the next
  step". A robot used it to learn to fit a peg into a hole.
- **Contactile's PapillArray** controller works out when slip starts from its
  pillar sensors, as the [frameworks
  book](../../../03_frameworks/02_gripping/02_grippers-and-hardware.md#82-tactile-sensing-at-the-contact)
  describes. It is a product, not an open model, and the maker does not publish how
  fast it reacts.

The frameworks book states the practical point plainly. In September 2026 there was
essentially no maintained open-source slip-detection software, and what exists is
research code, mostly unlicensed and mostly written for one paper. So if you want
slip detection on your robot, plan to train or write it yourself.

## 7. A worked example: carrying a wet mug

Here is one grip on a wet mug from start to finish. A two-finger gripper with a gel
sensor on each pad carries a mug that has just come out of a sink, and the outside
is wet, so the friction is low.

1. The fingers close, and the tactile model says the contact is centred. The program
   then reads the weight from the wrist sensor and chooses a gentle squeeze.
2. The arm lifts, and the slip model sees a jolt in the force. Because it has seen
   many lift jolts in training, it says "no slip".
3. The arm starts to move the mug sideways, and that movement adds a sideways push.
   So the dots at the rim of the contact start to slide, and the slip model gives a
   high number for slip.
4. The program responds. It first slows the arm down, because the slip started when
   the arm sped up. It also squeezes a little harder, after checking that the new
   force is still below the most the mug can take.
5. The dots stop sliding, so the slip model's number drops, and the arm carries on
   more slowly.

Without the model, the first sign of trouble would be the mug hitting the floor. The
order of the responses in step 4 comes from Book 3's
[holding on](../../../03_frameworks/02_gripping/05_holding-on.md#52-the-five-responses-in-order-of-cost)
, which lists the responses from cheapest to most expensive.

## 8. What goes wrong

The sections above described this kind of model at its best. This list gives the
five things that go wrong in practice, and what people do about each one.

- **Jolts that look like slip.** Closing, lifting and stopping all shake the
  signal, so a model that has not seen enough of them calls them slip. People
  therefore add many jolt examples to the training set, all marked "no slip".
- **Objects unlike the training set.** A slip on soft foam looks different from a
  slip on glass, so a model trained on hard objects may miss slips on soft ones.
  People therefore train on as wide a range of surfaces as they can.
- **Watching the wrong sensor.** A slip model reading the gripper's finger position
  cannot see an object sliding down between the pads, because the gap between the
  fingers does not change. It also cannot see an object turning between the pads.
  [Holding
  on](../../../03_frameworks/02_gripping/05_holding-on.md#41-the-finger-gap-check-and-what-it-cannot-see)
  explains why. No amount of training fixes a sensor that cannot observe the event,
  so people use shear, vibration or a wrist torque reading instead.
- **Too slow to help.** If the model needs a long window, or runs on a slow
  computer, the answer may come after the object has gone. So people measure the
  time from slip to answer on the real robot, and not only the accuracy.
- **Missing readings.** If the sensor stops sending readings, a careless program
  treats the silence as "no slip". A missing reading must be treated as unknown,
  and the program should stop or refuse, as [never fall back
  silently](../../../03_frameworks/02_gripping/05_holding-on.md#9-never-fall-back-silently)
  explains.

## 9. Why this rather than the obvious alternative, and what it costs

The last section listed what goes wrong, so this section weighs those problems
against the alternatives. The obvious alternative is **a fixed rule on the force
signal**, for example "if the sideways force is more than half the straight-in
force, call it slip". This rule comes from the simple physics of friction, so it
needs no data, it is easy to check, and it is right for many rigid objects.
However, it needs the friction number of the pad and the object together, which you
rarely know and which changes when the surface is wet or dusty. It also cannot tell
a jolt from a slip.

A second alternative is **a second look with a camera** after the grip. After the
lift, a wrist camera takes a picture and checks that the object has not moved, and
this needs no extra hardware and catches every kind of movement. However, it only
works after the movement has happened, so it cannot catch a slip in time to stop it.

So a learned slip model is worth it when the rule fails because friction is unknown
or changing, and when the answer is needed before the object moves far. Wet, oily,
dusty or unfamiliar objects are the main cases.

What it costs you:

- A sensor that can see slip, which means a tactile sensor, a fast force sensor on
  the pad, or a vibration sensor, because the gripper's own finger position is not
  enough.
- A training set of deliberate slips, which takes many hours of robot time.
- Your own software, since there is almost none to download.
- Testing for speed on the real robot, not only for accuracy.
- No guarantee. The model can miss a slip it has never seen. A program should
  still confirm, with the wrist sensor, that the object has the expected weight
  before a long carry.

## 10. The written alternative

This page has argued for learning the model, so the last question is when a written
rule is enough. The written alternative is the fixed rule in section 9, built with
the tools in Book 5's
[sensor streams](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md)
. That page shows how to smooth a force reading, find how fast it is changing, and
turn it into a flag that does not flicker on and off. Book 3's
[slip, and the checks that cannot fire](../../../03_frameworks/02_gripping/05_holding-on.md#4-slip-and-the-checks-that-cannot-fire)
explains which sensors can see slip at all.

The written rule wins for rigid objects with a known, steady friction, because it
needs no data and is easy to check. The slip model wins when the friction is unknown
or changing, as with wet, oily or dusty objects.

## 11. Where to read next

In this chapter:

- [Touch sensing models](../03_also-used/01_touch-sensing-models.md) explain the tactile pictures
  and dots this page reads.
- [Collision and failure detection](02_collision-and-failure-detection.md) covers
  what to do when a pick has already failed.

In this book:

- [Reinforcement learning policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  are often trained with force readings as an input, for jobs such as fitting a peg
  into a hole.
- [Tracking and motion](../../03_seeing-models/03_also-used/03_tracking-and-motion.md) explains how
  a camera model follows an object from one picture to the next, which is the
  camera side of a second look.

In the other books:

- [Slip, and the checks that cannot
  fire](../../../03_frameworks/02_gripping/05_holding-on.md#4-slip-and-the-checks-that-cannot-fire)
  in the frameworks book covers what sees slip and what does not.
- [Conditioning a force or contact
  reading](../../../02_perception/02_object-perception/02_sensors.md#26-conditioning-a-force-or-contact-reading)
  in the perception book explains how to clean up a noisy force signal before
  anything reads it.

## 12. Using it in Python

Sections 5 and 6 said that you will almost certainly train this model yourself, and
the [chapter overview](../01_overview.md#9-using-it-in-python) shows that training
loop, because it is the same one for every kind in this chapter. So this section shows
the other half, which is the part that runs while the arm carries the mug. After
reading it you will be able to turn a stream of force readings into the flag that
section 7 acts on.

```python
import collections

import numpy as np
import torch
from torch import nn

# The same network the overview trained, rebuilt so the saved numbers fit into it.
net = nn.Sequential(nn.Linear(6 * 20, 32), nn.ReLU(), nn.Linear(32, 1))
net.load_state_dict(torch.load('slip_model.pt'))
net.eval()                               # switch off the parts that only train

window = collections.deque(maxlen=20)    # keeps only the last 20 readings
slipping = False

while carrying:
    window.append(read_wrist_force())    # your own driver, giving six numbers
    if len(window) < window.maxlen:
        continue
    # Transposed, because training laid each window out one sensor at a time, and
    # the same numbers in a different order are a different input to the network.
    x = torch.tensor(np.array(window).T.reshape(1, -1), dtype=torch.float32)
    with torch.inference_mode():         # nothing is learned here, so keep no gradients
        chance = torch.sigmoid(net(x)).item()
    # Two limits rather than one: the flag turns on above 0.8 and only turns off
    # again below 0.4, so it does not flicker while the number sits near a limit.
    slipping = chance > 0.4 if slipping else chance > 0.8
    if slipping:
        slow_down_and_squeeze_a_little_harder()
```

PyTorch gives you three things here that are easy to miss. `net.eval()` and
`torch.inference_mode()` between them switch off everything that belongs to training,
and the second one also makes each answer faster, because the network no longer keeps
the extra numbers it would need in order to learn. `torch.sigmoid` turns the network's
raw output into the number between 0 and 1 that section 2 described. Python's own
`collections.deque` with a `maxlen` is the window: it throws the oldest reading away
by itself, so you never have to trim a list.

What you have to write yourself is `read_wrist_force` and
`slow_down_and_squeeze_a_little_harder`, and both of them are specific to your
hardware. The first talks to your force sensor or your tactile sensor, and the second
is the response that Book 3's
[holding on](../../../03_frameworks/02_gripping/05_holding-on.md#52-the-five-responses-in-order-of-cost)
page puts in order of cost. You also have to produce `slip_model.pt`, because there is
no slip model to download.

What you have to decide is the two limits and the window length, and section 8 says
why you cannot choose them from accuracy alone. Measure how long the whole loop takes
on the computer that will sit next to the arm, from the reading arriving to the flag
turning on, because a model that is right but answers after the mug has gone is no
use. If the loop is too slow, shorten the window before you shrink the network, since
a shorter window cuts the delay directly.
