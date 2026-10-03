# Collision and failure detection

This page answers two related questions about noticing trouble. The first is how a
robot arm notices that it has bumped into something it should not have touched. The
second is how it notices that a task has gone wrong, such as a mug dropped halfway
through a carry. To answer both, the page explains the simple method most arms
already use, where a learned model improves on it, and where a learned model must not
be trusted on its own.

It is written for a reader who has already read the
[overview of this chapter](../01_overview.md), and it also helps to have read
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md). You do not
need to know any physics beyond this: a motor that has to push harder uses more
electric current.

> Before this page, it helps to have read [arm
> dynamics](../../../05_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md),
> which works out the torque each joint should need, and [sensor
> streams](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md),
> which turns a noisy reading into a clean alarm. This page uses the first as the
> expected torque and the second to raise the alarm.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known methods and models](#5-well-known-methods-and-models)
6. [A worked example: a pick-and-place cell next to a person](#6-a-worked-example-a-pick-and-place-cell-next-to-a-person)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than the obvious alternative, and what it costs](#8-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

A collision detector compares what the arm's sensors measure with what they should
measure, and raises an alarm when the two differ too much. A failure detector does
the same for a whole task.

Here is an everyday example of the same comparison. You walk through a dark room
you know well. So you expect the floor to be flat and the path to be clear. If your
shin meets a chair, you feel a push you did not expect, and you stop at once. So you
did not need to see the chair at all. Instead, you noticed that what you felt was
different from what you expected.

So a robot arm can do the same thing. It knows what torque each joint should need to
follow its planned path, where a **torque** is a turning force, the force that
turns a joint. So if something pushes on the arm, the joints need a different
torque from the one expected, and that difference is the signal.

This page covers two jobs that use this same idea:

- **Collision detection** notices unexpected contact on the arm's body, within a
  few thousandths of a second, so the arm can stop or yield.
- **Failure detection** notices that a task has gone wrong: the object was not
  picked, it was dropped, or it was placed in the wrong spot. This can take longer,
  from a fraction of a second to a few seconds.

## 2. What goes in and what comes out

The last section said what the signal is, so this section lists the readings that
carry it. For collision detection, the inputs are the arm's own joint readings over
the last moment:

- The angle of each joint, from its **encoder**, which is the sensor that measures a
  joint's angle.
- The speed of each joint.
- The electric current in each motor, or the torque from a torque sensor in each
  joint, on arms that have one.
- The commands the controller sent.

The output is "collision" or "no collision", often with a number that says how sure
the model is, and some methods also say which part of the arm was hit.

For failure detection, the inputs are wider than that. They can include the wrist
force, the gripper's finger position, tactile readings, and pictures from a camera.
The output is "the task is going normally" or "something is wrong", and sometimes
also the kind of failure.

## 3. How it works inside

### 3.1 The gap between expected and measured

The last section listed the readings, and this section says what is done with them.
The core idea is the same for the simple method and for most learned ones. Two
numbers are compared, and the difference between them is called the **residual**,
where "residual" means what is left over.

1. Some model predicts the torque each joint should need right now, given its
   angle, its speed and how fast it is speeding up.
2. The sensors measure the torque each joint actually uses.
3. The program subtracts one from the other.
4. If the difference stays near zero, all is well. If it jumps above a limit, the
   program reports a collision and the arm stops.

![The torque a model expects on one joint, the torque the motor measures, and the gap between them](../../../images/touch-and-body-models/collision-and-failure-detection/expected-against-measured.svg)

The picture is a drawn example, not a real measurement. The top half shows the
expected torque on one joint as a dashed line, and the measured torque as a solid
line, and they match closely until the forearm hits a box. The bottom half shows
the gap between them, and when that gap crosses the stop line, the arm stops.

So the quality of the whole method depends on step 1. If the prediction is poor, the
gap is never near zero, even with no collision. Then the stop line has to be set
high, and gentle collisions are missed. This is where learning helps most, because
a learned model can predict the expected torque better than the textbook physics
can. It manages that by learning the friction and other effects the textbook leaves
out, and the [learned arm models](../03_also-used/02_learned-arm-models.md) page
explains how.

### 3.2 Where the arm was hit

Besides saying that something was hit, the residuals at all the joints also say
roughly where the contact was.

![A push on the forearm shows up at the joints before it, but not at the joint after it](../../../images/touch-and-body-models/collision-and-failure-detection/which-link-was-hit.svg)

The picture shows a three-joint arm whose forearm touches a box. Because a push on
the forearm turns the joints between the base and the forearm, those joints show a
gap. However, it cannot turn the joint beyond the forearm, so that joint shows no
gap. This means the last joint with a gap tells you which part of the arm was
hit.

### 3.3 Learned collision detectors

A learned collision detector either skips the explicit subtraction or adds to it.
It is a network that reads a short window of joint readings and outputs "collision"
or "no collision", where a window means the last few hundredths of a second of
readings taken together.

Then the network learns patterns that a single limit cannot. For example, a fast
movement makes a large gap for a moment, and so does a hard stop, while a gentle
bump makes a small gap with a particular shape over time. So a network trained on
many examples of both can tell them apart better than one fixed stop line can.

### 3.4 Learned failure detectors

However, a failure detector usually watches a whole task rather than one moment,
and there are two common ways to build one.

The first way learns what a normal run looks like, from many runs that went well.
Then it flags any run that looks different. This is called **anomaly
detection**, where "anomaly" means something unusual. It needs no examples of
failures at all, which is its great advantage, because failures are rare.

![Many good picks form a grey band; one pick leaves the band when the mug falls](../../../images/touch-and-body-models/collision-and-failure-detection/outside-the-normal-band.svg)

The picture is a drawn example, not a real measurement. It shows the weight felt at
the wrist during 25 picks that went well, as grey lines. Those lines form a narrow
band, because the weight rises at the lift and falls at the put-down. One pick, in
red, leaves the band halfway through the carry, because the weight vanished when
the mug fell. So an anomaly detector learns the band and flags any run that leaves
it.

A common network for this is an **autoencoder**, which is a network trained to
squeeze its input down to a few numbers and then rebuild the input from them. It
learns to rebuild normal runs well, so when it is shown an odd run, it rebuilds
that run badly. This means a bad rebuild is a sign that the run is unusual.

The second way instead trains a model on labelled examples of success and failure. A
**vision-language model** is a model that reads a picture and answers a question
about it in words, so it can look at a picture after a task and answer "did the mug
end up on the shelf?" The
[vision-language models](../../07_language-models/02_most-used/02_vision-language-models.md)
page covers this.

## 4. How it is trained

The last section described the detectors, and this section says where their
examples come from. For a learned collision detector, you need windows of joint
readings marked "collision" or "no collision".

The "no collision" examples are easy to get in bulk. You run the arm through many normal
movements at many speeds, with and without loads in the gripper, and record
everything.

The "collision" examples are harder, because you have to hit things on purpose.
People push the arm by hand at different places, or let it move into soft padded
objects at low speeds, and each contact is marked from the time it happened.
Because this is slow and needs care, collision sets are much smaller than
normal-motion sets.

For an anomaly detector, you need only normal runs. You record the task many times
while it succeeds, and you train the model to rebuild those runs. Then you set the
alarm limit using a separate batch of normal runs, so that normal variation does
not trigger it.

For a success detector that uses a camera, you need pictures of finished tasks
marked "success" or "failure". People often collect these for free, because a robot
cell that is already running records its own results.

## 5. Well-known methods and models

- **The momentum observer.** This is the classic non-learned method. It was
  developed by Alessandro De Luca, Sami Haddadin and colleagues, for lightweight
  arms at the German Aerospace Center (DLR). It computes the residual from section
  3.1 in a way that needs the joint speeds but not their rate of change, which is
  noisy to measure. It is the standard method in textbooks on this job. Haddadin and
  colleagues wrote a well-known survey of the whole field in 2017, called "Robot
  Collisions: A Survey on Detection, Isolation, and Identification".
- **CollisionNet** (Heo and colleagues, 2019). A CNN that reads a short window of
  joint signals from a collaborative arm and outputs whether a collision happened,
  and it was trained on real collisions caused on purpose.
- **The multimodal anomaly detector for robot-assisted feeding** (Park, Hoshi and
  Kemp, 2018). A robot fed a person with a spoon, and the model watched force, sound
  and motion signals and flagged anything unusual. It used a kind of autoencoder
  built from long short-term memory (LSTM) networks, where an LSTM is a network that
  reads a signal one step at a time and keeps a short memory of what it has read.
  It learned only from runs that went well.
- **SuccessVQA** (Du and colleagues, 2023). It turns "did the task succeed?" into a
  question a vision-language model can answer about a video. It showed that such a
  model, once trained on examples, can serve as a success detector for many tasks.
- **REFLECT** (Liu and colleagues, 2023). It turns a robot's sensor readings into a
  written summary of what happened, and asks a large language model to explain
  why a task failed and suggest a fix.

## 6. A worked example: a pick-and-place cell next to a person

Here is how the three detectors work together in one cell. A collaborative arm
picks mugs from a tray and puts them on a shelf. While that happens, a person works
at the next bench and sometimes reaches across.

1. The arm has a built-in safety function, which stops it if a joint torque goes far
   above what it expects. This function is certified, and the learned models below
   never replace it.
2. On top, a learned model predicts the torque each joint needs. It was trained on
   the arm's own normal movements, so it knows this arm's friction and the weight of
   its gripper. The gap between its prediction and the measured torque is small in
   normal work.
3. The person's elbow brushes the arm's forearm. The gap on joints 1 and 2 rises.
   It rises much less than a hard hit would make, but it is well above the small
   normal gap. The program slows the arm and moves it away from the contact.
4. A few picks later, the wrist weight vanishes halfway through a carry, so the
   anomaly detector flags the run. The program then stops the cell and reports
   "object lost during carry", with the time.
5. At the end of each place, a camera takes one picture of the shelf. A success
   detector checks that a mug is in the expected spot before the next pick.

In this cell each layer catches something that the others miss. The certified
function catches hard hits, while the learned residual catches gentle ones. The
anomaly detector catches the dropped mug, which is not a collision at all, and the
camera check catches a mug that was placed but fell over afterwards.

## 7. What goes wrong

The sections above described these detectors at their best. This list gives the six
things that go wrong in practice, and what people do about each one.

- **False alarms.** A detector that stops the arm every few minutes for nothing is
  soon switched off, and the main cause is a poor prediction of the expected torque.
  So people improve the prediction, or they allow a larger gap during fast
  movements.
- **Missed gentle contacts.** A stop line high enough to avoid false alarms may miss
  a soft bump, so people improve the prediction until the stop line can be lower.
- **A new payload.** If the gripper picks up something heavier than usual, the
  torques change, and the detector may call it a collision. So people tell the model
  the payload, or they weigh it first with the wrist sensor.
- **Rare failures.** A failure that never happened during training may look normal
  to a classifier trained on labelled failures. That is why people use anomaly
  detection instead, because it flags anything unusual.
- **Wear.** As the arm's gearboxes wear, friction changes, and the normal gap grows,
  so people retrain or recalibrate from time to time.
- **Trusting it for safety.** A learned detector has no guarantee. It must never be
  the only thing that keeps a person safe, so the certified safety function stays
  in place. The frameworks book makes the same point in
  [compliance](../../../03_frameworks/02_gripping/05_holding-on.md#3-compliance-impedance-and-admittance):
  a safety function is separate, certified equipment.

## 8. Why this rather than the obvious alternative, and what it costs

The last section listed what goes wrong, so this section weighs those problems
against the alternatives. The obvious alternative is **a fixed torque limit on each
joint**, with no model of what the torque should be. This is simple and
predictable, and every arm has it. However, the torque in normal work changes a lot
with speed and pose, so a fixed limit must be set above the largest normal torque.
This means a gentle bump during a slow movement never reaches it.

The next alternative is **the momentum observer with a textbook physics model**,
which is what good collaborative arms already do. It is fast, well understood and
needs no training data. So a learned model is worth adding only when this is not
enough: when the textbook model's errors force the stop line so high that gentle
contacts are missed, or when you want to catch failures that are not collisions at
all, such as a dropped object.

What it costs you:

- Data. You need many normal runs, and for a collision classifier, some real
  collisions caused carefully on purpose.
- Tuning. Someone has to choose the alarm limit, and choose between false alarms
  and missed contacts.
- Upkeep. The model must be retrained when the gripper, the payload or the arm's
  wear changes.
- No guarantee. It adds to the certified safety function and never replaces it.

## 9. The written alternative

This page has argued for adding a learned model, so the last question is what the
written version alone gives you. The written alternative is the
expected-against-measured check with a textbook physics model, which is the second
alternative in section 8, and Book 5 gives the pieces.
[Arm dynamics](../../../05_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md)
works out the torque each joint should need, and
[sensor streams](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#thresholds-that-do-not-flicker-hysteresis-and-debouncing)
turns the gap into an alarm that does not flicker.
[Safety monitoring](../../../05_programming-techniques/07_control-and-motion/02_most-used/04_safety-monitoring.md)
covers the software checks that act on such an alarm, and where certified safety
equipment must take over.

Because it is fast, needs no training data and is well understood, the written
check wins on most arms. A learned model wins when the textbook model's errors force
the stop line so high that gentle contacts are missed. It also wins when the failure
is not a collision at all, such as a dropped mug.

## 10. Where to read next

In this chapter:

- [Learned arm models](../03_also-used/02_learned-arm-models.md) explain how a model learns to
  predict the torque each joint needs, which is the "expected" half of this page.
- [Force and slip models](01_force-and-slip-models.md) cover a failure that starts
  in the fingers rather than on the arm.

In this book:

- [Vision-language models](../../07_language-models/02_most-used/02_vision-language-models.md) can
  look at a picture and say whether a task succeeded.
- [Learned motion planners](../../06_movement-models/03_also-used/02_learned-motion-planners.md)
  include learned collision checks, which predict a collision with an obstacle
  before the arm moves. This page is about noticing one after it happens.

In the other books:

- [Holding on](../../../03_frameworks/02_gripping/05_holding-on.md#8-letting-go)
  explains how to confirm that a release really happened, which is failure
  detection without a model.
- [Controlling the move](../../../03_frameworks/03_arm-movement/04_controlling-the-move.md)
  explains what the controller does between a planned path and the motors.

## 11. Using it in Python

Section 3.1 said that the whole method is a subtraction: the torque the physics says
each joint should need, taken away from the torque the motors really used. This
section shows that subtraction as code, because the expected torque is the one part
you do not have to write, and after reading it you will know which library computes it
and what you still have to supply.

```python
import numpy as np
import pinocchio as pin

# Reads the arm's own description: the links, their masses and where their weight
# sits. Most robot arms ship this file, and ROS uses the same one.
model = pin.buildModelFromUrdf('arm.urdf')
data = model.createData()

# q, v and a are the joint angles, the joint speeds and how fast those speeds are
# changing, all read from the arm. measured is the torque the motors really used.
expected = pin.rnea(model, data, q, v, a)
residual = measured - expected

hit = np.abs(residual) > limit            # limit: one number per joint
if hit.any():
    stop_the_arm()
    # Section 3.2: the last joint that shows a gap is the one nearest the contact.
    print('contact at or just past joint', int(np.flatnonzero(hit)[-1]))
```

Pinocchio gives you the expected torque, and that is the hard half. Its `rnea` is the
recursive Newton-Euler algorithm, which is the standard way of computing the torques a
chain of links needs, and it is fast enough to run inside a control loop, which a
version you wrote in NumPy would not be. It reads the arm's masses and lengths from a
URDF file, where "URDF" stands for unified robot description format and is the same
file that
[ROS](../../../04_ros-and-rviz/01_ros/02_ros-basics.md) and most simulators read, so
you normally already have it.

What you have to supply is everything the arm side of the subtraction needs. You read
`q`, `v` and `a` from the joints, and on most arms you have to work `a` out from the
speeds yourself, which is noisy, and that is exactly why the momentum observer in
section 5 avoids it. You also have to turn the motor current into `measured`, because
an arm without joint torque sensors reports current rather than torque, and the two
are only roughly proportional. Finally you have to run the arm through normal work to
see how big the residual gets when nothing has been hit, since that is the only honest
way to choose `limit`.

What you have to decide is `limit`, one number per joint, and section 7 says what each
choice costs: too low and the arm stops for nothing, too high and it misses a gentle
bump. For the failure detector of section 3.4, where you have only good runs and no
failures, scikit-learn's `sklearn.ensemble.IsolationForest` is the short version: you
fit it on features from your normal runs and its `predict` method then returns `-1` for
a run that does not look like them. Neither of these replaces the arm's certified
safety function, for the reason section 7 gives.
