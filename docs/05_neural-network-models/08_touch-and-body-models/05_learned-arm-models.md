# Learned arm models

This page answers one question. How can a robot arm learn how its own body behaves,
where the numbers in its manual are not quite right? It explains what such a model
predicts, how it is trained from the arm's own movements, the well-known kinds, and
when it is worth using instead of plain physics.

It is for a reader who has read the [overview of this chapter](01_overview.md) and
the first chapter of this book. You should know from Book 1 that an arm is a chain
of joints and links, and that each joint has a motor and an encoder, which is the
sensor that measures the joint's angle.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a heavier gripper on an old arm](#6-a-worked-example-a-heavier-gripper-on-an-old-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than the obvious alternative, and what it costs](#8-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

A learned arm model is a model of the arm's own body, learned from recordings of the
arm moving.

Here is an everyday example. When you start using a new bicycle, you do not know
exactly how hard to push the pedals to go at a given speed. After a few rides you
do. You have learned how this bicycle behaves: how heavy it is, how stiff its
chain is, how much its brakes grab. Nobody gave you the numbers.

A robot arm has a description of itself, too. The maker gives the length of each
link, the mass of each part, and where each part's weight is centred. From these,
physics can work out how much torque each joint needs to move in a given way. A
**torque** is a turning force: the force a motor uses to turn its joint. That
physics is called the arm's **dynamics**: how forces turn into movement.

The maker's description is close, but not exact. It leaves out the friction in the
gearboxes. It leaves out the cables that hang along the arm and pull on it. It does
not know about the gripper you bolted on, or the wear after years of use. A learned
arm model fills in what the description leaves out.

This page also covers two related jobs. **Calibration** means finding the small
errors in the arm's geometry, so that the arm goes exactly where it is told. A
**self-model** is a model an arm builds of its own shape, often by watching itself
with a camera.

## 2. What goes in and what comes out

There are two main directions, and they answer opposite questions.

![A forward model predicts where the arm will be from the torques; an inverse model gives the torques to get where you want](../../images/touch-and-body-models/learned-arm-models/forward-and-inverse.svg)

The picture shows the same arm twice. The dark arm is where it is now. The pale arm
is where it will be, or where you want it, a moment later. The orange arrows are
the torques at the joints.

A **forward model** answers: "if I apply these torques now, where will the arm be a
moment from now?" Its input is the joint angles, the joint speeds and the torques.
Its output is the joint angles and speeds a moment later.

An **inverse model** answers: "to move the way I want, what torque does each joint
need?" Its input is the joint angles, the joint speeds, and the change in speed you
want. Its output is one torque for each joint.

The inverse model is the one used most on real arms. The controller uses it to
work out the torque to send to each motor. The [collision
page](04_collision-and-failure-detection.md#31-the-gap-between-expected-and-measured)
uses the same prediction as its "expected torque".

A self-model has different inputs and outputs. Its input is the joint angles. Its
output is the arm's shape in space: which points around the robot the arm fills.

## 3. How it works inside

### 3.1 Physics plus a learned correction

Most learned arm models used in practice do not throw away physics. They keep the
textbook model and learn only the part it gets wrong. This is called **residual
learning**, because the network learns the residual: what is left over after the
physics has done its part.

![Torque against joint speed: the textbook line, the measured dots, and the textbook plus a learned correction](../../images/touch-and-body-models/learned-arm-models/textbook-plus-correction.svg)

The picture is a drawn example, not a real measurement. It shows the torque one
joint needs at different speeds. The dashed line is the textbook model, which
leaves out friction. The dots are what the real arm needs. At zero speed the dots
jump, because the joint must first overcome the friction that holds it still. The
solid line is the textbook model with a learned correction added, and it follows
the dots.

The steps are:

1. The textbook model works out a torque from the joint angles, speeds and the
   change in speed you want.
2. A small network looks at the same inputs and works out a correction.
3. The program adds the two together and sends that torque to the motor.

This has two advantages. The network has a small job, so it needs less data. And
where the network has seen nothing, the textbook model still gives a sensible
answer.

### 3.2 A network that learns the whole thing

A second kind learns the whole model from data, but is built so its answers obey
the rules of physics. For example, the energy of a moving arm cannot appear from
nowhere. A network built this way cannot give an answer that breaks that rule. It
needs less data than a plain network, and its answers are more sensible outside the
training data.

A plain network with no physics inside it can also learn the whole model. It needs
the most data, and it can give strange answers for movements it has never seen.

### 3.3 A self-model from a camera

A self-model learns the arm's shape. One way works like this.

![An arm moving at random while a camera records it, and the learned shape for new joint angles](../../images/touch-and-body-models/learned-arm-models/self-model-from-a-camera.svg)

The picture shows the two stages. On the left, the arm moves to many random poses
while a camera records it. Each picture is paired with the joint angles at that
moment. On the right, the trained model is given a pair of angles it has never
seen. For each point in space around the robot, it says whether the arm would fill
that point. The green dots are the points it says the arm fills.

Once an arm has a self-model, it can plan without being told its own shape. If a
part is bent or replaced, the arm can record itself again and learn the new shape.

### 3.4 Calibration

Calibration is usually done without a neural network. The arm moves to many poses.
A precise measuring device, such as a laser tracker, records where the tool really
is. A program then finds the small errors in the link lengths and joint angles that
best explain the difference.

Some errors are not simple length or angle errors. The links bend a little under
their own weight. The gears have a little play. A small network can learn these
left-over errors, in the same way as the residual in section 3.1. It takes the
joint angles as input, and outputs the correction to the tool's position.

## 4. How it is trained

A learned arm model trains on the arm's own recordings. This is its great
advantage: the data is cheap and safe to collect.

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

The arm reports many readings a second, so an hour of movement gives a very large
number of examples. The limit is not the number of examples. It is how varied
they are. A model trained only on slow movements does badly on fast ones.

For a self-model, the data is the joint angles paired with camera pictures, as in
section 3.3. For calibration, it is the joint angles paired with measurements from
the precise measuring device.

## 5. Well-known models

- **Locally weighted projection regression (LWPR)** (Vijayakumar and Schaal, 2000).
  This is an early learning method for arm dynamics, from before deep networks. It
  fits many small simple models, each good for one region of movement, and blends
  them. It can learn while the arm runs.
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

An arm has worked in a cell for several years. The team fits a new, heavier
gripper with a tactile sensor on each finger. Two problems appear. The arm follows
its planned paths less exactly than before. And its collision detector gives false
alarms during fast moves.

1. The team keeps the maker's physics model, but adds the new gripper's mass.
2. They run the arm through an hour of varied movements, with the gripper open and
   empty, and record the joint angles, speeds and motor currents.
3. They train a small network to predict the residual: the difference between the
   torque the physics model gives and the torque the motors actually used.
4. The network learns two things the physics model left out. The first is the
   friction in each gearbox, which has grown with wear. The second is the pull of
   the new gripper's cable, which drags on the last two joints.
5. The controller now sends the physics torque plus the learned correction. The
   arm follows its paths more closely.
6. The collision detector uses the same corrected prediction as its expected
   torque. Its gap in normal work is now smaller, so the stop line can be set lower
   without false alarms. Gentle bumps that it used to miss now cross the line.

The model will need retraining when the gripper changes again, or when the wear
changes the friction further. The team schedules a short recording run every few
months and compares the new residual with the old one.

## 7. What goes wrong

- **Movements it has not seen.** A model trained on slow movements gives poor
  answers for fast ones. People collect varied data, and keep a physics model
  underneath so that the answer is never far off.
- **Changes over time.** Friction changes as the arm warms up during the day, and
  as the gearboxes wear over years. People retrain from time to time, or use a
  method that learns while the arm runs.
- **A payload it does not know about.** The model learned the arm with an empty
  gripper. A heavy object in the gripper changes the torques. People give the model
  the payload's mass as an input, or weigh the object first with the wrist sensor.
- **Motor current is not torque.** On arms without joint torque sensors, the model
  learns from motor current. Current is only roughly proportional to torque, and
  the friction in the gearbox sits between them. People accept a coarser model, or
  use an arm that measures joint torque directly.
- **Speed.** The controller needs a torque answer many hundreds of times a second.
  A large network may be too slow. People use small networks for this job. [Running
  a model on a robot](../01_what-models-are/05_running-a-model-on-a-robot.md)
  explains the trade-off.
- **No guarantee.** A learned correction can make things worse in an odd pose. A
  controller that uses one should limit how large the correction may be.

## 8. Why this rather than the obvious alternative, and what it costs

The obvious alternative is **a better physics model, identified from data**. This
is called **system identification**. You keep the textbook equations, and you
measure the arm's real masses and friction numbers by running it through set
movements and fitting the numbers. This is a well-established method. It needs
little data, its answers can be checked and it behaves sensibly everywhere. It is
the right first step, and often enough on its own.

A learned model is worth adding when the effects left over do not fit the textbook
equations. Friction that changes with speed and temperature, a cable that pulls
differently in each pose, a link that bends under load: none of these is a simple
number to fit. A network can learn them from the same recordings.

A self-model is worth it in a different case: when the arm's shape is not known in
advance or may change, such as a new or damaged robot. For a standard factory arm
with an accurate description, it is not needed.

What it costs you:

- Recording time on the arm. It is cheap and safe, but it must be varied.
- Retraining whenever the arm, its gripper or its wear changes.
- A model that must run fast enough for the controller.
- A model that gives no guarantee. Keep the physics model underneath, and limit the
  size of the learned correction.

## 9. Where to read next

In this chapter:

- [Collision and failure detection](04_collision-and-failure-detection.md) uses
  the inverse model from this page as its expected torque.
- The [overview](01_overview.md) compares all four kinds.

In this book:

- [Learned dynamics models](../07_world-models/02_learned-dynamics-models.md)
  predict how the world changes when the arm acts. A learned arm model is the same
  idea with the arm's own body as the whole world.
- [Learned motion planners](../05_movement-models/06_learned-motion-planners.md)
  cover learned inverse kinematics: a network that turns a wanted gripper position
  into joint angles.
- [Reinforcement learning
  policies](../05_movement-models/05_reinforcement-learning-policies.md) are often
  trained in a simulator. A learned model of the arm's motors makes that simulator
  closer to the real arm.

In the other books:

- [Learned pieces inside a planned
  system](../../03_frameworks/03_arm-movement/05_learned-motion.md#3-learned-pieces-inside-a-planned-system)
  in the frameworks book describes where small learned models help a planned arm.
- [Calibration, which decides all of
  it](../../02_perception/02_object-perception/02_sensors.md#4-calibration-which-decides-all-of-it)
  in the perception book covers calibrating the camera and the arm together.
- [Controlling the move](../../03_frameworks/03_arm-movement/04_controlling-the-move.md)
  explains what the controller does with a torque.
