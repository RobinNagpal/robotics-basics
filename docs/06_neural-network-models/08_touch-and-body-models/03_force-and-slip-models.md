# Force and slip models

This page answers one question. How can a robot tell that an object in its fingers
is starting to slide out, early enough to do something about it? It explains the
force signals a model reads, how a slip model works and is trained, the models
people have published, and why this job is harder than it looks.

It is for a reader who has read [touch sensing models](02_touch-sensing-models.md),
because this page uses the moving dots from its section 4.3. You should also know
from [how a model learns](../01_what-models-are/02_how-a-model-learns.md) what it
means to train a model on examples.

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
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

A slip model reads the force signals from a gripper over a short stretch of time
and says whether the held object is starting to slide.

Here is an everyday example. You carry a full glass of water, and your hand is a
little wet. You feel a tiny slide on your fingertips before the glass moves far.
Without thinking, you squeeze a bit harder, and the glass stays put. You did not
wait to see it fall.

A slip model tries to give a robot that same early warning. The word **slip** means
that the object moves relative to the fingers. The useful moment to catch it is
the very start, which is called **incipient slip**. "Incipient" means just
beginning. At that moment, squeezing a little harder still works. A second later,
the object is on the floor.

This page also covers the wider family of **force models**. These read force
signals and say something else about the contact, such as how the object is
sitting in the fingers, or whether a part has clicked into place. Slip is the
most common job, so the page uses it as the main example.

## 2. What goes in and what comes out

The input is a short window of recent sensor readings. A **window** here means the
last few tenths of a second of readings, taken together. The readings can come
from different sensors:

- A tactile sensor on the finger pad, as a short run of tactile pictures, or the
  positions of the printed dots in each picture.
- A force sensor on the finger pad, giving the push straight in and the push
  sideways at each moment.
- A force-torque sensor at the wrist, giving six numbers at each moment: a push
  along three directions and a twist about three directions.
- A small vibration sensor, called an accelerometer, near the finger.

The output is usually one of two things. The first is a yes-or-no answer:
"slipping" or "not slipping". The second is a number between 0 and 1 that says how
likely a slip is. The program then compares the number with a limit it chooses.

Some force models give other outputs, such as "the grasp will hold" or "the part is
seated", but they work the same way.

## 3. What slip looks like in the signal

A slip leaves marks in the signal. A slip model learns to recognise them. It is
worth seeing them first, so the model is less of a mystery.

![One grip as a force trace: fingers close, lift, hold, then slip](../../images/touch-and-body-models/force-and-slip-models/grip-force-trace.svg)

The picture is a drawn example, not a real measurement. It shows the force on one
finger pad during one grip. The force jumps when the fingers close, and wobbles
briefly. It wobbles again when the lift starts. Then it holds steady. When the slip
starts, a fast, small shaking appears. Then the force drops as the mug slides out.

Two things make slip hard to spot by eye, and by a simple rule. The first is that
the jolts from closing and lifting look a lot like the shaking from slip. Both are
quick changes. A rule that says "a quick change means slip" fires on every lift.
The second is that the drop in force comes late. By the time the force has clearly
dropped, the object is already sliding out.

A tactile sensor shows slip in a second way, and this one comes earlier.

![Dots on a gel pad while held, while starting to slip at the rim, and while slipping](../../images/touch-and-body-models/force-and-slip-models/slip-starts-at-the-edge.svg)

The picture shows the dots on a gel pad at three moments. While the object is held,
the dots in the contact lean a little, all together. When slip starts, the dots at
the rim of the contact slide first, while the dots in the centre still stick. The
rim is where the pressure is lowest, so it lets go first. When the object slips
fully, every dot in the contact moves the same way.

Stage 2 is the moment a slip model tries to catch. The centre still holds, so there
is still time to squeeze harder.

## 4. How it works inside

### 4.1 One window at a time

A slip model does not read the whole grip at once. It reads one short window at a
time, and it moves the window forward as new readings arrive.

![A short window of the force signal going into a small network that says slip or no slip](../../images/touch-and-body-models/force-and-slip-models/one-window-at-a-time.svg)

The picture shows two windows on the same signal. The green one covers a steady
stretch, and the network says "no slip". The red one covers the fast shaking, and
the network says "slip". The same network runs on every window.

The steps are:

1. The program keeps the last few tenths of a second of readings in memory.
2. It passes that window to the model.
3. The model gives back "slip" or "no slip", or a number for how likely a slip is.
4. The program acts on the answer, and the window moves on.

The window length is a choice with a cost. A short window gives an answer sooner,
but it holds less evidence, so the model makes more mistakes. A long window is more
reliable, but the answer comes later.

### 4.2 What kind of network

Different signals suit different networks.

For tactile pictures, the model often uses a **convolutional neural network
(CNN)** to read each picture, as in the [touch sensing
page](02_touch-sensing-models.md#42-with-learning-a-network-reads-the-picture). A
second part then looks at how the pictures change over the window. A common choice
for that second part is a **long short-term memory (LSTM)** network. An LSTM is a
network that reads a sequence one step at a time and keeps a short memory of what
it has read so far.

For a force signal, which is just a few numbers at each moment, a simpler network
is often enough. It can read the window as a list of numbers. Some models first
turn the window into a set of frequencies, which shows the fast shaking of slip
more clearly.

### 4.3 Joining touch with a camera

Some models also look at a camera picture of the object in the gripper. The camera
can see the object move a lot, and the tactile sensor can feel it move a little.
Together, they catch more slips than either alone.

## 5. How it is trained

A slip model learns from windows of readings that each have the right answer:
"slip" or "no slip". Getting those answers is the hard part.

The usual way is to cause slips on purpose, many times, and record them. A robot
grips an object gently and lifts it, or pulls it sideways, or tilts it. Some of
those grips hold and some slip. For each window, someone needs to know whether a
slip was happening. People find that out in three ways:

- They watch the object with a camera and a tracking marker. If the object moves
  relative to the fingers, that window is marked "slip".
- They use the tactile dots. If the dots in the centre of the contact move, the
  object has slipped.
- They mark it by hand from a video. This is slow and it is done for small sets
  only.

Published slip data sets are small. They are much smaller than the data sets for
camera models, because every example costs a real grip on a real robot. That is one
reason slip models often fail on objects unlike the ones they were
trained on.

## 6. Well-known models

This area is mostly research papers, not products. These are real and often cited.

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
  book](../../03_frameworks/02_gripping/02_grippers-and-hardware.md#82-tactile-sensing-at-the-contact)
  describes. It is a product, not an open model, and the maker does not publish how
  fast it reacts.

The frameworks book says the practical point plainly. In September 2026 there was
essentially no maintained open-source slip-detection software. What exists is
research code, mostly unlicensed and mostly written for one paper. If you want slip
detection on your robot, plan to train or write it yourself.

## 7. A worked example: carrying a wet mug

A two-finger gripper with a gel sensor on each pad carries a mug that has just come
out of a sink. The outside is wet, so the friction is low.

1. The fingers close. The tactile model says the contact is centred. The program
   reads the weight from the wrist sensor and chooses a gentle squeeze.
2. The arm lifts. The slip model sees a jolt in the force. It has seen many lift
   jolts in training, so it says "no slip".
3. The arm starts to move the mug sideways. The movement adds a sideways push. The
   dots at the rim of the contact start to slide. The slip model gives a high
   number for slip.
4. The program responds. It first slows the arm down, because the slip started when
   the arm sped up. It also squeezes a little harder, after checking that the new
   force is still below the most the mug can take.
5. The dots stop sliding. The slip model's number drops. The arm carries on more
   slowly.

Without the model, the first sign of trouble would be the mug hitting the floor.
The order of the responses in step 4 comes from [holding
on](../../03_frameworks/02_gripping/05_holding-on.md#52-the-five-responses-in-order-of-cost),
which lists the responses from cheapest to most expensive.

## 8. What goes wrong

- **Jolts that look like slip.** Closing, lifting and stopping all shake the
  signal. A model that has not seen enough of them calls them slip. People add many
  jolt examples to the training set, all marked "no slip".
- **Objects unlike the training set.** A slip on soft foam looks different from a
  slip on glass. A model trained on hard objects may miss slips on soft ones.
  People train on as wide a range of surfaces as they can.
- **Watching the wrong sensor.** A slip model reading the gripper's finger position
  cannot see an object sliding down between the pads, because the gap between the
  fingers does not change. It also cannot see an object turning between the pads.
  [Holding
  on](../../03_frameworks/02_gripping/05_holding-on.md#41-the-finger-gap-check-and-what-it-cannot-see)
  explains why. No amount of training fixes a sensor that cannot observe the event.
  People use shear, vibration or a wrist torque reading instead.
- **Too slow to help.** If the model needs a long window, or runs on a slow
  computer, the answer may come after the object has gone. People measure the time
  from slip to answer on the real robot, not only the accuracy.
- **Missing readings.** If the sensor stops sending readings, a careless program
  treats the silence as "no slip". A missing reading must be treated as unknown,
  and the program should stop or refuse, as [never fall back
  silently](../../03_frameworks/02_gripping/05_holding-on.md#9-never-fall-back-silently)
  explains.

## 9. Why this rather than the obvious alternative, and what it costs

The obvious alternative is **a fixed rule on the force signal**. For example: "if
the sideways force is more than half the straight-in force, call it slip". This
rule comes from the simple physics of friction. It needs no data, it is easy to
check, and it is right for many rigid objects. The trouble is that it needs the
friction number of the pad and the object together, which you rarely know, and
which changes when the surface is wet or dusty. It also cannot tell a jolt from a
slip.

A second alternative is **a second look with a camera**. After the lift, a wrist
camera takes a picture and checks that the object has not moved. This needs no
extra hardware and catches every kind of movement. But it only works after the
movement has happened, so it cannot catch a slip in time to stop it.

A learned slip model is worth it when the rule fails because friction is unknown or
changing, and when the answer is needed before the object moves far. Wet, oily,
dusty or unfamiliar objects are the main cases.

What it costs you:

- A sensor that can see slip: a tactile sensor, a fast force sensor on the pad, or
  a vibration sensor. The gripper's own finger position is not enough.
- A training set of deliberate slips, which takes many hours of robot time.
- Your own software, since there is almost none to download.
- Testing for speed on the real robot, not only for accuracy.
- No guarantee. The model can miss a slip it has never seen. A program should
  still confirm, with the wrist sensor, that the object has the expected weight
  before a long carry.

## 10. Where to read next

In this chapter:

- [Touch sensing models](02_touch-sensing-models.md) explain the tactile pictures
  and dots this page reads.
- [Collision and failure detection](04_collision-and-failure-detection.md) covers
  what to do when a pick has already failed.

In this book:

- [Reinforcement learning policies](../05_movement-models/05_reinforcement-learning-policies.md)
  are often trained with force readings as an input, for jobs such as fitting a peg
  into a hole.
- [Tracking and motion](../02_seeing-models/08_tracking-and-motion.md) explains how
  a camera model follows an object from one picture to the next, which is the
  camera side of a second look.

In the other books:

- [Slip, and the checks that cannot
  fire](../../03_frameworks/02_gripping/05_holding-on.md#4-slip-and-the-checks-that-cannot-fire)
  in the frameworks book covers what sees slip and what does not.
- [Conditioning a force or contact
  reading](../../02_perception/02_object-perception/02_sensors.md#26-conditioning-a-force-or-contact-reading)
  in the perception book explains how to clean up a noisy force signal before
  anything reads it.
