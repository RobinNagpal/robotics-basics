# Learned arm models

This page answers one question: how can a robot arm learn how its own body behaves,
where the numbers in its manual are not quite right? To answer that, it explains what
such a model predicts, how it is trained from the arm's own movements, the well-known
kinds, and when it is worth using instead of plain physics.

It is written for a reader who has already read the
[overview of this chapter](../01_overview.md) and the first chapter of this book. You
should know from Book 1 that an arm is a chain of joints and links, and that each
joint has a motor and an encoder, which is the sensor that measures the joint's
angle.

> Before this page, it helps to have read [arm
> dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md),
> which explains the textbook model of the torque each joint needs, and [system
> identification](../../../06_programming-techniques/04_fitting-and-estimation/03_also-used/01_system-identification.md),
> which measures the numbers inside it. This page learns the part that those two
> leave out.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a heavier gripper on an old arm](#6-a-worked-example-a-heavier-gripper-on-an-old-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than the obvious alternative, and what it costs](#8-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

A learned arm model is a model of the arm's own body, learned from recordings of the
arm moving.

Here is an everyday example of the same learning. When you start using a new bicycle,
you do not know exactly how hard to push the pedals to go at a given speed. However,
after a few rides you do. By then you have learned how this bicycle behaves: how
heavy it is, how stiff its chain is, and how much its brakes grab, and nobody gave
you any of those numbers.

A robot arm has a description of itself, too. The maker gives the length of each
link, the mass of each part, and where each part's weight is centred, and from those
numbers physics can work out how much torque each joint needs to move in a given
way. A **torque** is a turning force, the force a motor uses to turn its joint. This
is the arm's **dynamics**: how forces turn into movement.

However, the maker's description is close rather than exact. It leaves out the
friction in the gearboxes, and it also leaves out the cables that hang along the arm
and pull on it. It also does not know about the gripper you bolted on, or the wear after
years of use. So a learned arm model fills in what the description leaves out.

This page also covers two related jobs of the same kind. **Calibration** means
finding the small errors in the arm's geometry, so that the arm goes exactly where
it is told. A **self-model** is a model an arm builds of its own shape, often by
watching itself with a camera.

## 2. What goes in and what comes out

Now that the job is clear, here is what passes in and out. There are two main
directions for such a model, and they answer opposite questions.

![A forward model predicts where the arm will be from the torques; an inverse model gives the torques to get where you want](../../../images/touch-and-body-models/learned-arm-models/forward-and-inverse.svg)

The picture shows the same arm twice. The dark arm is where it is now, while the pale
arm is where it will be, or where you want it, a moment later. The orange arrows are
the torques at the joints.

A **forward model** answers: "if I apply these torques now, where will the arm be a
moment from now?" Its input is the joint angles, the joint speeds and the torques.
Its output is the joint angles and speeds a moment later.

An **inverse model** answers: "to move the way I want, what torque does each joint
need?" Its input is the joint angles, the joint speeds, and the change in speed you
want, and its output is one torque for each joint.

Because the controller uses it to work out the torque to send to each motor, the
inverse model is the one used most on real arms. The
[collision page](../02_most-used/02_collision-and-failure-detection.md#31-the-gap-between-expected-and-measured)
uses the same prediction as its "expected torque".

A self-model has different inputs and outputs from both of those. Its input is the
joint angles, and its output is the arm's shape in space, meaning which points around
the robot the arm fills.

## 3. How it works inside

### 3.1 Physics plus a learned correction

The last section said what the model predicts, and this section says how it does it.
Most learned arm models used in practice do not throw away physics. Instead, they
keep the textbook model and learn only the part it gets wrong. This is called
**residual learning**, because the network learns the residual, which is what is left
over after the physics has done its part.

![Torque against joint speed: the textbook line, the measured dots, and the textbook plus a learned correction](../../../images/touch-and-body-models/learned-arm-models/textbook-plus-correction.svg)

The picture is a drawn example, not a real measurement, and it shows the torque one
joint needs at different speeds. The dashed line is the textbook model, which leaves
out friction, while the dots are what the real arm needs. At zero speed the dots
jump, because the joint must first overcome the friction that holds it still. The
solid line is the textbook model with a learned correction added, and it follows the
dots.

The steps are these:

1. The textbook model works out a torque from the joint angles, speeds and the
   change in speed you want.
2. A small network looks at the same inputs and works out a correction.
3. The program adds the two together and sends that torque to the motor.

This has two advantages over learning everything from nothing. The network has a
small job, so it needs less data. Where the network has seen nothing, the textbook
model also still gives a sensible answer.

### 3.2 A network that learns the whole thing

Instead, a second kind learns the whole model from data, but it is built so that its
answers obey the rules of physics. For example, the energy of a moving arm cannot
appear from nowhere, so a network built this way cannot give an answer that breaks
that rule. This means it needs less data than a plain network, and its answers are
more sensible outside the training data.

A plain network with no physics inside it can also learn the whole model. However, it
needs the most data of all, and it can give strange answers for movements it has
never seen.

### 3.3 A self-model from a camera

A self-model learns the arm's shape instead of its torques, and one way of building
one works as follows.

![An arm moving at random while a camera records it, and the learned shape for new joint angles](../../../images/touch-and-body-models/learned-arm-models/self-model-from-a-camera.svg)

The picture shows the two stages. On the left, the arm moves to many random poses
while a camera records it, and each picture is paired with the joint angles at that
moment. On the right, the trained model is given a pair of angles it has never seen.
For each point in space around the robot, it then says whether the arm would fill
that point. The green dots are the points it says the arm fills.

Once an arm has a self-model, it can plan without being told its own shape. So if a
part is bent or replaced, the arm can record itself again and learn the new shape.

### 3.4 Calibration

Calibration is usually done without a neural network at all. The arm moves to many
poses, and a precise measuring device, such as a laser tracker, records where the
tool really is. A program then finds the small errors in the link lengths and joint
angles that best explain the difference.

However, some errors are not simple length or angle errors. The links bend a little
under their own weight, and the gears have a little play. So a small network can
learn these left-over errors, in the same way as the residual in section 3.1. It
takes the joint angles as input, and it outputs the correction to the tool's
position.

## 4. How it is trained

The last section described the model, and this section says where its recordings come
from. A learned arm model trains on the arm's own movements. This is its great
advantage, because that data is cheap and safe to collect.

1. The arm moves through many different movements. People often use smooth
   movements that sweep each joint through its range at different speeds, so the
   model sees a wide variety.
2. At each moment, the program records the joint angles, the joint speeds, and the
   torque or current in each motor. The speed change is worked out from the
   speeds.
3. For an inverse model, each moment becomes one example. The input is the angles,
   the speeds and the speed change. The right answer is the torque that was
   actually used.
4. The network is trained to give the right answer for each example.

Because the arm reports many readings a second, an hour of movement gives a very
large number of examples. This means the limit is not the number of examples but how
varied they are, because a model trained only on slow movements does badly on fast
ones.

For a self-model, the data is the joint angles paired with camera pictures, as in
section 3.3. For calibration, it is the joint angles paired with measurements from
the precise measuring device.

## 5. Well-known models

- **Locally weighted projection regression (LWPR)** (Vijayakumar and Schaal, 2000).
  This is an early learning method for arm dynamics, from before deep networks. It
  fits many small simple models, each good for one region of movement, and blends
  them, and it can learn while the arm runs.
- **Local Gaussian process regression** (Nguyen-Tuong, Seeger and Peters). A
  Gaussian process is a learning method that gives both a prediction and how sure
  it is. This work made it fast enough to learn an arm's inverse model while the
  arm runs.
- **Deep Lagrangian Networks (DeLaN)** (Lutter, Ritter and Peters, 2019). A
  network built so that its answers follow the rules of physics for moving bodies,
  as in section 3.2. It learned an arm's inverse model from less data than a plain
  network, and gave more sensible answers for new movements.
- **The actuator network** (Hwangbo and colleagues, 2019). The team learned a model
  of each motor of a four-legged robot, ANYmal, from recordings. They put that
  model inside a simulator, so that the simulated motors behaved like the real
  ones. Policies trained in that simulator then worked on the real robot. It is a
  legged robot, not an arm, but the idea transfers directly to arm motors.
- **Task-agnostic self-modeling machines** (Kwiatkowski and Lipson, 2019). A robot
  arm moved at random, learned a model of itself from the recordings, and then used
  that model to plan tasks. When a part was damaged, it learned the change.
- **Full-body visual self-modeling** (Chen and colleagues, 2022). An arm watched
  itself with cameras and learned which points in space its body fills for any set
  of joint angles, as in section 3.3.

## 6. A worked example: a heavier gripper on an old arm

Here is one arm and one upgrade, step by step. An arm has worked in a cell for
several years. Then the team fits a new, heavier gripper with a tactile sensor on
each finger. Two problems then appear. The arm follows its planned paths less exactly
than before, and its collision detector gives false alarms during fast moves.

1. The team keeps the maker's physics model, but adds the new gripper's mass.
2. They run the arm through an hour of varied movements, with the gripper open and
   empty, and record the joint angles, speeds and motor currents.
3. They train a small network to predict the residual: the difference between the
   torque the physics model gives and the torque the motors actually used.
4. The network learns two things the physics model left out. The first is the
   friction in each gearbox, which has grown with wear. The second is the pull of
   the new gripper's cable, which drags on the last two joints.
5. The controller now sends the physics torque plus the learned correction, so the
   arm follows its paths more closely.
6. The collision detector uses the same corrected prediction as its expected
   torque. Its gap in normal work is now smaller, so the stop line can be set lower
   without false alarms. Gentle bumps that it used to miss now cross the line.

The model will need retraining when the gripper changes again, or when the wear
changes the friction further. So the team schedules a short recording run every few
months, and compares the new residual with the old one.

## 7. What goes wrong

The sections above described this kind of model at its best. This list gives the six
things that go wrong in practice, and what people do about each one.

- **Movements it has not seen.** A model trained on slow movements gives poor
  answers for fast ones. So people collect varied data, and they keep a physics
  model underneath so that the answer is never far off.
- **Changes over time.** Friction changes as the arm warms up during the day, and
  as the gearboxes wear over years. So people retrain from time to time, or they use
  a method that learns while the arm runs.
- **A payload it does not know about.** The model learned the arm with an empty
  gripper, so a heavy object in the gripper changes the torques. People give the
  model the payload's mass as an input, or they weigh the object first with the
  wrist sensor.
- **Motor current is not torque.** On arms without joint torque sensors, the model
  learns from motor current, but current is only roughly proportional to torque,
  because the friction in the gearbox sits between them. So people accept a coarser
  model, or they use an arm that measures joint torque directly.
- **Speed.** The controller needs a torque answer many hundreds of times a second,
  and a large network may be too slow. So people use small networks for this job.
  [Running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains the trade-off.
- **No guarantee.** A learned correction can make things worse in an odd pose. A
  controller that uses one should limit how large the correction may be.

## 8. Why this rather than the obvious alternative, and what it costs

The last section listed what goes wrong, so this section weighs those problems
against the alternative. The obvious alternative is **a better physics model,
identified from data**, and that is called **system identification**. You keep the
textbook equations, and you measure the arm's real masses and friction numbers by
running it through set movements and fitting the numbers. This is a well-established
method, because it needs little data, its answers can be checked and it behaves
sensibly everywhere. So it is the right first step, and it is often enough on its
own.

A learned model is worth adding when the effects left over do not fit the textbook
equations. Friction that changes with speed and temperature, a cable that pulls
differently in each pose, and a link that bends under load are all examples, because
none of them is a simple number to fit. Instead, a network can learn them from the
same recordings.

A self-model is worth it in a different case, which is when the arm's shape is not
known in advance or may change, such as a new or damaged robot. For a standard
factory arm with an accurate description, it is not needed.

What it costs you:

- Recording time on the arm. It is cheap and safe, but it must be varied.
- Retraining whenever the arm, its gripper or its wear changes.
- A model that must run fast enough for the controller.
- A model that gives no guarantee. Keep the physics model underneath, and limit the
  size of the learned correction.

## 9. The written alternative

This page has argued for adding a learned correction, so the last question is what
the written model alone gives you. The written alternative is the textbook model with
its numbers measured on your own arm, which is the first alternative in section 8.
Book 5's
[arm dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md)
explains the model.
[System identification](../../../06_programming-techniques/04_fitting-and-estimation/03_also-used/01_system-identification.md)
explains how to move the arm so that the data can tell the numbers apart, and how to
fit them. The geometry calibration in section 3.4 is written code too: a fit of the
kind that
[least-squares fitting](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/01_least-squares-fitting.md)
explains.

Because it needs little data and behaves sensibly everywhere, the written model wins
as a first step, and it is often enough on its own. A learned correction wins only
for effects that are not a simple number to fit, such as friction that changes with
temperature, or a cable that pulls differently in each pose.

## 10. Where to read next

In this chapter:

- [Collision and failure detection](../02_most-used/02_collision-and-failure-detection.md) uses
  the inverse model from this page as its expected torque.
- The [overview](../01_overview.md) compares all four kinds.

In this book:

- [Learned dynamics models](../../08_world-models/02_most-used/01_learned-dynamics-models.md)
  predict how the world changes when the arm acts. A learned arm model is the same
  idea with the arm's own body as the whole world.
- [Learned motion planners](../../06_movement-models/03_also-used/02_learned-motion-planners.md)
  cover learned inverse kinematics: a network that turns a wanted gripper position
  into joint angles.
- [Reinforcement learning
  policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md) are often
  trained in a simulator. A learned model of the arm's motors makes that simulator
  closer to the real arm.

In the other books:

- [Learned pieces inside a planned
  system](../../../03_frameworks/03_arm-movement/05_learned-motion.md#3-learned-pieces-inside-a-planned-system)
  in the frameworks book describes where small learned models help a planned arm.
- [Calibration, which decides all of
  it](../../../02_perception/02_object-perception/02_sensors.md#4-calibration-which-decides-all-of-it)
  in the perception book covers calibrating the camera and the arm together.
- [Controlling the move](../../../03_frameworks/03_arm-movement/04_controlling-the-move.md)
  explains what the controller does with a torque.

## 11. Using it in Python

Section 3.1 said that a learned arm model in practice keeps the textbook physics and
learns only the part it gets wrong. This section shows that in code, because the split
is visible in it: one library computes the physics, and a network of about six lines
learns the leftover. After reading it you will be able to turn an hour of recordings
into a correction that the controller can add.

```python
import numpy as np
import pinocchio as pin
import torch
from torch import nn

model = pin.buildModelFromUrdf('arm.urdf')
data = model.createData()

# One row per recorded moment, from the run described in section 4: the joint
# angles, the joint speeds, how fast those speeds changed, and the torque used.
q, v, a, tau = (np.load(f'{name}.npy') for name in ('q', 'v', 'a', 'tau'))
physics = np.array([pin.rnea(model, data, qi, vi, ai) for qi, vi, ai in zip(q, v, a)])

x = torch.tensor(np.hstack([q, v, a]), dtype=torch.float32)
y = torch.tensor(tau - physics, dtype=torch.float32)   # only what the physics missed

net = nn.Sequential(nn.Linear(x.shape[1], 64), nn.Tanh(), nn.Linear(64, y.shape[1]))
loss_fn = nn.MSELoss()
optimiser = torch.optim.Adam(net.parameters(), lr=1e-3)

for _ in range(2000):
    optimiser.zero_grad()
    loss = loss_fn(net(x), y)
    loss.backward()
    optimiser.step()
```

At run time the controller then adds the two parts together, and it limits how much the
network is allowed to change, for the reason the last point of section 7 gives. Here
`q` and `v` are the arm's reading at this moment rather than the whole recording, and
`a_wanted` is the change in speed the controller is asking for.

```python
with torch.inference_mode():
    correction = net(torch.tensor(np.hstack([q, v, a_wanted]), dtype=torch.float32))
send_to_motors(pin.rnea(model, data, q, v, a_wanted) + np.clip(correction.numpy(), -5, 5))
```

Pinocchio gives you the physics half, through the same `rnea` call that the
[collision page](../02_most-used/02_collision-and-failure-detection.md#11-using-it-in-python)
uses, and it reads the masses and lengths from the arm's own URDF description file. It
is fast enough to run in a control loop, which matters here because this model is asked
hundreds of times a second rather than once per picture. PyTorch gives you the network,
and it can be small precisely because the physics has already done most of the work,
which is the first advantage that section 3.1 lists.

What you have to collect yourself is the recording, and section 4 says how: sweep every
joint through its range at many speeds, with the gripper empty, and log the angles, the
speeds and the motor torque or current at every reading. You also have to work out `a`
from the speeds, because most arms do not report it, and you have to keep the same
units on both sides of the subtraction, since a current in amps minus a torque in
newton metres is not a residual but a mistake.

What you have to decide is how varied the recording is, how large the network may be
and still answer in time, and what the clipping limit should be. The first of those
matters most, because a model trained only on slow movements is confidently wrong on
fast ones, and the physics model underneath is the only thing that keeps the answer
sensible there. Retrain after every change to the gripper, the payload or the arm's
wear, as the worked example in section 6 does.
