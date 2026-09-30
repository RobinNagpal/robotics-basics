# Collision and failure detection

This page answers two related questions. How does a robot arm notice that it has
bumped into something it should not have touched? And how does it notice that a
task has gone wrong, such as a mug dropped halfway through a carry? It explains the
simple method most arms already use, where a learned model improves on it, and
where a learned model must not be trusted on its own.

It is for a reader who has read the [overview of this chapter](01_overview.md). It
helps to have read [how a model learns](../01_what-models-are/02_how-a-model-learns.md).
You do not need to know any physics beyond this: a motor that has to push harder
uses more electric current.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known methods and models](#5-well-known-methods-and-models)
6. [A worked example: a pick-and-place cell next to a person](#6-a-worked-example-a-pick-and-place-cell-next-to-a-person)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than the obvious alternative, and what it costs](#8-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

A collision detector compares what the arm's sensors measure with what they should
measure, and raises an alarm when the two differ too much. A failure detector does
the same for a whole task.

Here is an everyday example. You walk through a dark room you know well. You expect
the floor to be flat and the path to be clear. If your shin meets a chair, you feel
a push you did not expect, and you stop at once. You did not need to see the chair.
You noticed that what you felt was different from what you expected.

A robot arm can do the same. It knows what torque each joint should need to follow
its planned path. A **torque** is a turning force: the force that turns a joint. If
something pushes on the arm, the joints need a different torque from the one
expected. The difference is the signal.

This page covers two jobs that use this same idea:

- **Collision detection** notices unexpected contact on the arm's body, within a
  few thousandths of a second, so the arm can stop or yield.
- **Failure detection** notices that a task has gone wrong: the object was not
  picked, it was dropped, or it was placed in the wrong spot. This can take longer,
  from a fraction of a second to a few seconds.

## 2. What goes in and what comes out

For collision detection, the inputs are the arm's own joint readings over the last
moment:

- The angle of each joint, from its **encoder**, which is the sensor that measures a
  joint's angle.
- The speed of each joint.
- The electric current in each motor, or the torque from a torque sensor in each
  joint, on arms that have one.
- The commands the controller sent.

The output is "collision" or "no collision", often with a number that says how
sure the model is. Some methods also say which part of the arm was hit.

For failure detection, the inputs are wider. They can include the wrist force, the
gripper's finger position, tactile readings, and pictures from a camera. The output
is "the task is going normally" or "something is wrong", and sometimes the kind of
failure.

## 3. How it works inside

### 3.1 The gap between expected and measured

The core idea is the same for the simple method and for most learned ones. Two
numbers are compared, and the difference is called the **residual**. "Residual"
means what is left over.

1. Some model predicts the torque each joint should need right now, given its
   angle, its speed and how fast it is speeding up.
2. The sensors measure the torque each joint actually uses.
3. The program subtracts one from the other.
4. If the difference stays near zero, all is well. If it jumps above a limit, the
   program reports a collision and the arm stops.

![The torque a model expects on one joint, the torque the motor measures, and the gap between them](../../images/touch-and-body-models/collision-and-failure-detection/expected-against-measured.svg)

The picture is a drawn example, not a real measurement. The top half shows the
expected torque on one joint as a dashed line, and the measured torque as a solid
line. They match closely until the forearm hits a box. The bottom half shows the
gap between them. When the gap crosses the stop line, the arm stops.

The quality of the whole method depends on step 1. If the prediction is poor, the
gap is never near zero, even with no collision. Then the stop line has to be set
high, and gentle collisions are missed. This is where learning helps most. A
learned model can predict the expected torque better than the textbook physics
can, because it learns the friction and other effects the textbook leaves out. The
[learned arm models](05_learned-arm-models.md) page explains how.

### 3.2 Where the arm was hit

The residuals at all the joints also say roughly where the contact was.

![A push on the forearm shows up at the joints before it, but not at the joint after it](../../images/touch-and-body-models/collision-and-failure-detection/which-link-was-hit.svg)

The picture shows a three-joint arm whose forearm touches a box. A push on the
forearm turns the joints between the base and the forearm, so those joints show a
gap. It cannot turn the joint beyond the forearm, so that joint shows no gap. The
last joint with a gap tells you which part of the arm was hit.

### 3.3 Learned collision detectors

A learned collision detector skips the explicit subtraction, or adds to it. It is a
network that reads a short window of joint readings and outputs "collision" or "no
collision". A window here means the last few hundredths of a second of readings
taken together.

The network learns patterns that a single limit cannot. A fast movement makes a
large gap for a moment, and so does a hard stop. A gentle bump makes a small gap
with a particular shape over time. A network trained on many examples of both can
tell them apart better than one fixed stop line.

### 3.4 Learned failure detectors

A failure detector usually watches a whole task, not one moment. There are two
common ways to build one.

The first way learns what a normal run looks like, from many runs that went well.
It then flags any run that looks different. This is called **anomaly detection**.
"Anomaly" means something unusual. It does not need examples of failures, which is
its great advantage, because failures are rare.

![Many good picks form a grey band; one pick leaves the band when the mug falls](../../images/touch-and-body-models/collision-and-failure-detection/outside-the-normal-band.svg)

The picture is a drawn example, not a real measurement. It shows the weight felt at
the wrist during 25 picks that went well, as grey lines. They form a narrow band:
the weight rises at the lift and falls at the put-down. One pick, in red, leaves the
band halfway through the carry. The weight vanished, because the mug fell. An
anomaly detector learns the band and flags any run that leaves it.

A common network for this is an **autoencoder**. It is a network trained to squeeze
its input down to a few numbers and then rebuild the input from them. It learns to
rebuild normal runs well. When it is shown an odd run, it rebuilds it badly. A bad
rebuild means the run is unusual.

The second way trains a model on labelled examples of success and failure. A
**vision-language model** is a model that reads a picture and answers a question
about it in words. It can look at a picture after a task and answer "did the mug
end up on the shelf?" The [vision-language
models](../06_language-models/03_vision-language-models.md) page covers this.

## 4. How it is trained

For a learned collision detector, you need windows of joint readings marked
"collision" or "no collision".

The "no collision" examples are easy. You run the arm through many normal movements
at many speeds, with and without loads in the gripper, and record everything.

The "collision" examples are harder. You have to hit things on purpose. People
push the arm by hand at different places, or let it move into soft padded objects,
at low speeds. Each contact is marked from the time it happened. Because this is
slow and needs care, collision sets are much smaller than normal-motion sets.

For an anomaly detector, you need only normal runs. You record the task many times
while it succeeds, and train the model to rebuild those runs. You then set the
alarm limit using a separate batch of normal runs, so that normal variation does
not trigger it.

For a success detector that uses a camera, you need pictures of finished tasks
marked "success" or "failure". People often collect these for free, because a
robot cell that is already running records its own results.

## 5. Well-known methods and models

- **The momentum observer.** This is the classic non-learned method. It was
  developed by Alessandro De Luca, Sami Haddadin and colleagues, for lightweight
  arms at the German Aerospace Center (DLR). It computes the residual from section
  3.1 in a way that needs the joint speeds but not their rate of change, which is
  noisy to measure. It is the standard method in textbooks on this job. Haddadin and
  colleagues wrote a well-known survey of the whole field in 2017, called "Robot
  Collisions: A Survey on Detection, Isolation, and Identification".
- **CollisionNet** (Heo and colleagues, 2019). A CNN that reads a short window of
  joint signals from a collaborative arm and outputs whether a collision happened.
  It was trained on real collisions caused on purpose.
- **The multimodal anomaly detector for robot-assisted feeding** (Park, Hoshi and
  Kemp, 2018). A robot fed a person with a spoon. The model watched force, sound
  and motion signals and flagged anything unusual. It used a kind of autoencoder
  built from long short-term memory (LSTM) networks. An LSTM is a network that
  reads a signal one step at a time and keeps a short memory of what it has read. It learned only from runs that went well.
- **SuccessVQA** (Du and colleagues, 2023). It turns "did the task succeed?" into a
  question a vision-language model can answer about a video. It showed that such a
  model, once trained on examples, can serve as a success detector for many tasks.
- **REFLECT** (Liu and colleagues, 2023). It turns a robot's sensor readings into a
  written summary of what happened, and asks a large language model to explain
  why a task failed and suggest a fix.

## 6. A worked example: a pick-and-place cell next to a person

A collaborative arm picks mugs from a tray and puts them on a shelf. A person works
at the next bench and sometimes reaches across.

1. The arm has a built-in safety function. It stops if a joint torque goes far
   above what it expects. This function is certified. The learned models below
   never replace it.
2. On top, a learned model predicts the torque each joint needs. It was trained on
   the arm's own normal movements, so it knows this arm's friction and the weight of
   its gripper. The gap between its prediction and the measured torque is small in
   normal work.
3. The person's elbow brushes the arm's forearm. The gap on joints 1 and 2 rises.
   It rises much less than a hard hit would make, but it is well above the small
   normal gap. The program slows the arm and moves it away from the contact.
4. A few picks later, the wrist weight vanishes halfway through a carry. The
   anomaly detector flags the run. The program stops the cell and reports "object
   lost during carry", with the time.
5. At the end of each place, a camera takes one picture of the shelf. A success
   detector checks that a mug is in the expected spot before the next pick.

Each layer catches something the others miss. The certified function catches hard
hits. The learned residual catches gentle ones. The anomaly detector catches the
dropped mug, which is not a collision at all. The camera check catches a mug that
was placed but fell over afterwards.

## 7. What goes wrong

- **False alarms.** A detector that stops the arm every few minutes for nothing is
  soon switched off. The main cause is a poor prediction of the expected torque.
  People improve the prediction, or allow a larger gap during fast movements.
- **Missed gentle contacts.** A stop line high enough to avoid false alarms may miss
  a soft bump. People improve the prediction so the stop line can be lower.
- **A new payload.** If the gripper picks up something heavier than usual, the
  torques change, and the detector may call it a collision. People tell the model
  the payload, or weigh it first with the wrist sensor.
- **Rare failures.** A failure that never happened during training may look normal
  to a classifier trained on labelled failures. That is the reason to use anomaly
  detection, which flags anything unusual.
- **Wear.** As the arm's gearboxes wear, friction changes, and the normal gap grows.
  People retrain or recalibrate from time to time.
- **Trusting it for safety.** A learned detector has no guarantee. It must never be
  the only thing that keeps a person safe. The certified safety function stays in
  place. The frameworks book makes the same point in
  [compliance](../../03_frameworks/02_gripping/05_holding-on.md#3-compliance-impedance-and-admittance):
  a safety function is separate, certified equipment.

## 8. Why this rather than the obvious alternative, and what it costs

The obvious alternative is **a fixed torque limit on each joint**, with no model of
what the torque should be. This is simple and predictable, and every arm has it.
Its trouble is that the torque in normal work changes a lot with speed and pose. A
fixed limit must be set above the largest normal torque. That means a gentle bump
during a slow movement never reaches it.

The next alternative is **the momentum observer with a textbook physics model**.
This is what good collaborative arms already do. It is fast, well understood and
needs no training data. A learned model is worth adding only when this is not
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

## 9. Where to read next

In this chapter:

- [Learned arm models](05_learned-arm-models.md) explain how a model learns to
  predict the torque each joint needs, which is the "expected" half of this page.
- [Force and slip models](03_force-and-slip-models.md) cover a failure that starts
  in the fingers rather than on the arm.

In this book:

- [Vision-language models](../06_language-models/03_vision-language-models.md) can
  look at a picture and say whether a task succeeded.
- [Learned motion planners](../05_movement-models/06_learned-motion-planners.md)
  include learned collision checks, which predict a collision with an obstacle
  before the arm moves. This page is about noticing one after it happens.

In the other books:

- [Holding on](../../03_frameworks/02_gripping/05_holding-on.md#8-letting-go)
  explains how to confirm that a release really happened, which is failure
  detection without a model.
- [Controlling the move](../../03_frameworks/03_arm-movement/04_controlling-the-move.md)
  explains what the controller does between a planned path and the motors.
