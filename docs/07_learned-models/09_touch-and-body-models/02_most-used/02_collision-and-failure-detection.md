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
> dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md),
> which works out the torque each joint should need, and [sensor
> streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md),
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

This section names the methods people actually use, and it keeps this page's two jobs
apart, because the honest answer is different for each. For noticing that the arm has hit
something, the method used almost everywhere is not a learned model at all. It is a limit
on the difference between the torque the physics expects and the torque the motors
measured, which is the subtraction in section 3.1, and learning helps there only by making
the expected torque more accurate. For noticing that a whole task has failed, learned
models have arrived properly, and the last three entries below are all of that kind.

Read the table as: the method, which of the two jobs it does, what it is best at, how big
it is, its licence, and the one case that should make you choose it. A cell says `not
stated` where nobody has published the figure. "Yours" in the licence column means the
model comes out of your own training run, so no licence restricts it.

| Method | Which job | Best at | Size | Licence | Pick it when |
| --- | --- | --- | --- | --- | --- |
| [5.1 The momentum observer](#51-the-momentum-observer-with-a-textbook-physics-model) | the arm hit something | an answer in milliseconds, with no training data at all | not a learned model | Pinocchio is BSD-2 | always, and first |
| [5.2 A learned torque model behind the same limit](#52-a-learned-torque-model-behind-the-same-limit) | the arm hit something | lowering the limit until gentle contacts reach it | yours to choose; one small model per joint | yours; scikit-learn is BSD 3-Clause | section 5.1 misses a push you can feel by hand |
| [5.3 CollisionNet](#53-collisionnet-a-classifier-that-reads-the-window) | the arm hit something | explaining why the field kept the subtraction | `not stated`; 8,449 numbers in the version below | none published | your arm reports current and has no description file |
| [5.4 An anomaly detector on good runs only](#54-an-anomaly-detector-trained-on-good-runs-only) | the task failed | flagging a failure you have no example of | yours to choose; 200 small trees below | yours; scikit-learn is BSD 3-Clause | you have many good runs and almost no failures |
| [5.5 A vision-language model as the judge](#55-a-vision-language-model-as-the-judge-of-a-finished-attempt) | the task failed | answering "did this attempt succeed?" for a task it has never seen | 8.9 GB, on a 4-billion-parameter backbone | Apache-2.0 | one cell does many different tasks |
| [5.6 Sentinel](#56-sentinel-for-an-arm-driven-by-a-learned-policy) | the task failed | catching a learned policy going wrong before the task does | no weights; it watches your own policy | MIT | a generative policy drives the arm |

### 5.1 The momentum observer, with a textbook physics model

This is the method **most used in 2026**, and the most useful thing this section can tell
you is that it contains no learning at all. Alessandro De Luca and Raffaella Mattone
introduced it, and Sami Haddadin, De Luca and Alin Albu-Schäffer collected the whole
family of such methods in a 2017 survey in IEEE Transactions on Robotics called "Robot
Collisions: A Survey on Detection, Isolation, and Identification". It computes the
residual of section 3.1 from the arm's **momentum**, which here means the mass matrix of
the arm multiplied by its joint speeds. The rate of change of that momentum equals the
torques acting on the arm, so if you subtract the torque you commanded and the torque the
physics explains, what is left over is the push from outside.

You would pick this rather than the obvious alternative, which is the direct subtraction
of the expected torque from the measured torque, because of one missing input. The direct
version needs the acceleration of every joint, meaning how fast each joint's speed is
changing. An encoder measures angles, so the acceleration has to be worked out by
differentiating twice, and the noise in it swamps a gentle contact. The momentum observer
needs the angles, the speeds and the commanded torques only. It is also the method already
running on collaborative arms, which is the strongest practical reason: [franka_ros2](https://github.com/frankarobotics/franka_ros2)
publishes a field called `tau_ext_hat_filtered`, described in its own
`FrankaRobotState.msg` as the filtered external torque, so on a Franka arm the residual
arrives on a topic and you write none of this.

What it costs you is the physics model and the limit. You need the arm's own description
file with honest masses, and every error in that file lands in the residual, so the limit
has to sit above the worst of those errors. Friction in the gearboxes is the largest such
error, and it is the reason section 5.2 exists. There is no training and no graphics card,
and the code below runs inside a control loop on an ordinary processor. What most often
goes wrong is the measured half rather than the predicted half: an arm without torque
sensors in its joints reports motor current, and current times a constant is only roughly
the torque, which puts a floor under how small a contact you can see.

The library is [Pinocchio](https://github.com/stack-of-tasks/pinocchio), which reads the
arm's description file and computes its dynamics. It is BSD-2, recorded in the frameworks
book's [licence table](../../../03_frameworks/03_arm-movement/06_licences-and-platforms.md#22-kinematics-and-trajectories).

```python
import numpy as np
import pinocchio as pin

model = pin.buildModelFromUrdf('arm.urdf')   # the arm's own description file
data = model.createData()

dt = 0.001                        # the control period, in seconds
gain = 50.0                       # how fast the residual catches up, in 1/seconds
limit = np.full(model.nv, 2.0)    # the gap allowed at each joint, in newton metres
running_sum = np.zeros(model.nv)
residual = np.zeros(model.nv)

while True:
    q, v, tau = read_joints()     # angles, speeds, and the torque each motor used
    momentum = pin.crba(model, data, q) @ v              # the mass matrix times speeds
    coriolis = pin.computeCoriolisMatrix(model, data, q, v)
    gravity = pin.computeGeneralizedGravity(model, data, q)
    explained = gravity - coriolis.T @ v   # the torque the arm's own motion explains
    running_sum += (tau - explained + residual) * dt
    residual = gain * (momentum - running_sum)
    hit = np.abs(residual) > limit
    if hit.any():
        stop_the_arm()
        # Section 3.2: the last joint with a gap is the one nearest the contact.
        print('contact at or just past joint', int(np.flatnonzero(hit)[-1]))
```

Pinocchio supplies the three hard quantities. `crba` is the composite rigid body
algorithm, which builds the mass matrix; `computeCoriolisMatrix` gives the matrix of the
forces that come from the arm's own motion; and `computeGeneralizedGravity` gives the
torque needed to hold the arm still against gravity. None of them needs an acceleration.

What you supply is `read_joints`, which talks to your arm, and the two numbers you choose.
The gain decides how quickly the residual rises to the real outside push, and the limit
decides what counts as a collision. Section 5.2 shows how to measure the limit instead of
guessing it.

The loop above was run on Pinocchio's own sample six-joint arm, inside a program that
simulated the arm as well, with the gain and period shown and a 3 newton metre push
appearing at one joint. Twenty milliseconds later the residual at that joint read 1.87
newton metres, after one hundred milliseconds it read 2.98, and the other five joints
stayed below 0.01 throughout. That is what the gain buys and costs: a higher one reaches
the true push sooner and carries more of the sensors' noise with it.

### 5.2 A learned torque model behind the same limit

This is also **most used in 2026** wherever a learned model touches this job at all, and it
is the smallest change that helps. You keep the whole of section 5.1 and replace only its
prediction. The physics model predicts the torque, a small learned model predicts what the
physics got wrong, and the two together leave a much smaller residual when nothing has
been hit. Because the residual is smaller, the limit can be lower, and a contact you can
barely feel by hand now crosses it. The
[learned arm models](../03_also-used/02_learned-arm-models.md#52-a-residual-torque-network-on-top-of-the-makers-model)
page covers the correction itself, and this section is the detector built on top of it.

You would pick this rather than the obvious alternative, which is the end-to-end classifier
of section 5.3, for three reasons. The training set is the easy one to collect, because it
contains ordinary work and no collisions at all. The answer stays in newton metres, so the
limit is a quantity you can argue about and compare with the force a person can tolerate.
And you keep the isolation of section 3.2, because a classifier that answers "collision"
does not tell you which part of the arm was touched.

What it costs you is a recording and the discipline to keep it clean. You need ordinary
motion at the speeds and with the payloads you will really use, because a model trained on
an empty gripper calls a full one a collision. You have to retrain when the gripper, the
payload or the arm's wear changes, as section 7 says. The thing that most often goes wrong
is that a collision gets into the recording: if somebody leaned on the arm while it was
being recorded, the correction learns to explain that push away, and the detector then
ignores exactly the event it exists to catch.

The library is scikit-learn, whose own `COPYING` file is the BSD 3-Clause licence. The code
below does not train the detector, because there is nothing to train: it measures the limit.

```python
import numpy as np
import pinocchio as pin
from sklearn.ensemble import HistGradientBoostingRegressor

# A recording of ordinary work with nothing touching the arm. The accelerations are
# worked out from the speeds, which is noisy, and the learned part absorbs that too.
q, v, a, measured = (np.load(f'normal_{name}.npy') for name in ('q', 'v', 'a', 'tau'))

model = pin.buildModelFromUrdf('arm.urdf')
data = model.createData()
physics = np.array([pin.rnea(model, data, *row) for row in zip(q, v, a)])

# Friction is most of what the physics misses, and friction depends on which way the
# joint is turning, so the direction of travel goes in as an input of its own.
left_over = measured - physics
inputs = np.hstack([q, v, np.sign(v)])
split = int(0.8 * len(q))                  # the first four fifths train the correction
learned = [HistGradientBoostingRegressor().fit(inputs[:split], left_over[:split, j])
           for j in range(model.nv)]

# Nothing touched the arm in the held-back fifth either, so every gap left there is an
# error of the model. The limit has to sit above almost all of them.
held_back = np.column_stack([one.predict(inputs[split:]) for one in learned])
gap = np.abs(left_over[split:] - held_back)
print('limit per joint, in newton metres:', np.quantile(gap, 0.999, axis=0).round(2))
```

scikit-learn fits one small tree ensemble for each joint, which needs no graphics card and
no choice of features beyond the three inputs above. Pinocchio's `rnea` is the recursive
Newton-Euler algorithm, the standard way of computing the torque a movement needs.

What you supply is the recording, and the recording is the whole job. What you decide is
the 0.999 above, which says that one reading in a thousand of ordinary work may cross the
limit. That is still too many stops, so the limit is not used alone: the alarm should
require the gap to stay above it for several readings in a row, which the programming
techniques book's [sensor
streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#thresholds-that-do-not-flicker-hysteresis-and-debouncing)
page builds.

### 5.3 CollisionNet, a classifier that reads the window

This one is **historical**, and it is here because it explains why the methods above keep
the subtraction. Young Jin Heo, Dayeon Kim, Woongyong Lee, Hyoungkyun Kim, Jonghoon Park
and Wan Kyun Chung at the Pohang University of Science and Technology published it in IEEE
Robotics and Automation Letters in April 2019, under the title "Collision Detection for
Industrial Collaborative Robots: A Deep Learning Approach". It drops the physics model
altogether. A network reads a short window of joint signals and answers "collision" or "no
collision", so feature extraction and the decision are learned together, and nothing in it
has to be told what the arm weighs.

You would read it rather than use it, because section 5.2 beats it on the thing that
decides this job in practice, which is where the training examples come from. This
classifier needs real collisions, recorded on purpose, at the speeds and poses where you
want them caught, and section 4 says what that costs. It also has to be collected again
when the payload or the gripper changes, while section 5.2 only needs fresh ordinary
motion. There is one case that still points here: an old arm that reports motor current
and has no trustworthy description file gives you no expected torque to subtract, and then
a classifier on the raw window is all that is left.

What it costs you, besides the collisions, is the explanation. The answer is yes or no with
no number behind it, so you cannot say how hard the contact was, and section 3.2's reading
of which link was hit is gone. There is no public implementation to install, so the code
below is the shape the paper describes, written again.

```python
import torch
from torch import nn

JOINTS, WINDOW = 6, 20     # six joints, and the last twenty readings

# Three signals for each joint at each moment: the angle, the speed and the motor
# current. A one-dimensional convolution slides along time, so a pattern is recognised
# wherever inside the window it happens rather than only at one position.
net = nn.Sequential(
    nn.Conv1d(JOINTS * 3, 32, kernel_size=5), nn.ReLU(),
    nn.Conv1d(32, 32, kernel_size=5), nn.ReLU(),
    nn.Flatten(), nn.Linear(32 * (WINDOW - 8), 1))

# The answer is one of two things, so this is the loss to train it with. It expects the
# raw output, and torch.sigmoid turns that output into a number between 0 and 1.
loss = nn.BCEWithLogitsLoss()

windows = torch.load('collision_windows.pt')   # shape (examples, JOINTS * 3, WINDOW)
answers = torch.load('collision_answers.pt')   # shape (examples, 1), 1.0 or 0.0
print('numbers in the network:', sum(p.numel() for p in net.parameters()))
print('loss before any training:', float(loss(net(windows), answers).detach()))
```

PyTorch supplies the convolution, the loss and the training loop you would write around it.
The network above holds 8,449 numbers, counted by running the last two lines, and a network
that small trains on a laptop. What you supply is the two files, and that means causing
collisions on purpose and writing down when each one started. What you decide is
the window length, which sets how late the answer can arrive, and the cut-off on the
output, which trades false alarms against missed contacts.

### 5.4 An anomaly detector trained on good runs only

This is the shape **most used in 2026** for the second job on this page, because it is the
only one that needs no examples of failure. It is the first way described in section 3.4.
You describe each finished run with a handful of numbers, you fit a model to the runs that
went well, and you report any later run that does not look like them.

The published landmark is the multimodal anomaly detector of Daehyung Park, Yuuna Hoshi and
Charles Kemp, from [November 2017](https://arxiv.org/abs/1711.00614). A robot fed a person
with a spoon, and their model watched seventeen raw signals at once through a variational
autoencoder built from long short-term memory networks. An autoencoder is the kind of
network section 3.4 described, and a long short-term memory network is one that reads a
signal one step at a time and keeps a short memory of what it has read. It was tested on
1,555 feeding attempts and twelve kinds of anomaly, and the paper reports 0.8710 on a
measure called the area under the curve, which is the chance that the detector gives a
failed attempt a worse score than a good one. A score of one would be perfect, and one
half would be no better than guessing.

You would pick an anomaly detector rather than the obvious alternative, a classifier
trained on labelled successes and failures, because of which failures you have. A cell that
works most of the time gives you a few dozen failures a year, all of the same two or three
kinds, and a classifier trained on those recognises those and nothing else. The anomaly
detector flags anything unfamiliar, so the failure nobody anticipated is still caught. You
would pick the classifier instead only when one particular failure matters more than all
the others and you can produce it on purpose.

What it costs you is false alarms and the features. It flags anything unusual, including a
new and perfectly good way of succeeding, so a cell that changes its task rate or its
lighting will produce alarms that mean nothing. It also needs a second batch of good runs
that the model never saw, because the alarm limit measured on the training runs is always
too generous. The published version above is a sequence model with no code linked from the
paper, so most people start with the cheap version below instead, which is a few hundred
small decision trees on summary numbers and trains in seconds.

The library is scikit-learn again, and the class is
[IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html),
which finds unusual rows by how easily a random split separates them from the rest.

```python
import numpy as np
from sklearn.ensemble import IsolationForest

# One row per recorded run that went well, and six numbers describing each run.
good = np.load('good_runs.npy')            # shape (number of runs, 6)

# contamination is the share of the training rows the detector may treat as odd. Keep
# it small, because every row here is a run you believe went well.
detector = IsolationForest(n_estimators=200, contamination=0.01,
                           random_state=0).fit(good[:400])

# The limit comes from good runs the detector never saw. A run that scores worse than
# the worst one per cent of those is reported.
limit = np.quantile(detector.score_samples(good[400:]), 0.01)

def looks_normal(run):                     # run: the same six numbers, one finished run
    return detector.score_samples(run.reshape(1, -1))[0] >= limit
```

scikit-learn does the fitting and the scoring, where a higher score means more ordinary.
What you supply is the six numbers, and they decide what the detector is able to notice.
For the dropped mug of section 3.4, at least one of them has to depend on the weight at the
wrist during the carry, because no amount of training lets a model see a quantity that is
not in its input. What you decide is the one per cent above, and what the program does when
`looks_normal` returns false. Stopping the cell and reporting the run is the right default,
because a detector whose alarm is ignored is worse than no detector.

### 5.5 A vision-language model as the judge of a finished attempt

This one is **worth betting on**, because a robot that practises without a person watching
needs something that can judge its own attempts, and the frontier chapter's
[section on LeRobot's releases](../../../03_frameworks/08_frontier/06_what-is-coming.md#23-lerobot-which-now-releases-on-a-predictable-rhythm)
calls such a model the missing piece in every method of that kind. It is the second way described in section 3.4. You give a model the frames
of a finished attempt and the sentence that describes the task, and it answers whether the
task succeeded.

The idea was named by Yuqing Du and colleagues in [March 2023](https://arxiv.org/abs/2303.07280),
in a paper that treated success detection as a question asked about a video, called
SuccessVQA, and answered it with Flamingo, a vision-language model of the time. What has
changed since is that such judges now arrive as ordinary downloads. This book covers them
in one place, the
[reward and progress models](../../06_movement-models/03_also-used/03_reward-and-progress-models.md#7-well-known-models-and-libraries)
page, which names each one, states its licence and shows how to set it up. Read that page
for the judges themselves. This section is only about using one as a failure detector.

You would pick a judge rather than the obvious alternative, a small image classifier trained
on your own pictures of the finished shelf, because of how many tasks your cell does. The
classifier is faster and more accurate on the one task it knows, and the reward page's
[section 7.1](../../06_movement-models/03_also-used/03_reward-and-progress-models.md#71-the-hil-serl-reward-classifier-which-you-train-on-your-own-pictures)
recommends it for exactly that reason. However, twenty different tasks need twenty
classifiers and twenty sets of marked pictures, while one judge answers all twenty from the
sentence you give it.

What it costs you is a graphics card, seconds rather than milliseconds, and an unmeasured
level of agreement. The downloadable judge named on that page, Robometer, is a checkpoint of
about 8.9 GB on a 4-billion-parameter backbone, and its
[LeRobot page](https://huggingface.co/docs/lerobot/robometer) says a graphics card is
strongly recommended. That page also says it reads at most eight frames of an attempt by
default, which is the detail people miss: eight frames spread over a one-minute carry can
miss the moment the mug fell. And nobody has published how often such a judge agrees with
a careful person on a task it was not trained for, so this belongs after a finished step
rather than inside a control loop.

The library is LeRobot, which is Apache-2.0, and the call below is the one its own
Robometer page documents.

```python
from lerobot.rewards.robometer import RobometerConfig, RobometerRewardModel
from lerobot.rewards.robometer.modeling_robometer import ROBOMETER_FEATURE_PREFIX
from lerobot.rewards.robometer.processor_robometer import RobometerEncoderProcessorStep

# "success" asks for 1.0 or 0.0 rather than a number saying how far along the attempt is.
cfg = RobometerConfig(pretrained_path='lerobot/Robometer-4B', device='cuda',
                      reward_output='success')
judge = RobometerRewardModel.from_pretrained(cfg.pretrained_path, config=cfg)
encoder = RobometerEncoderProcessorStep(
    base_model_id=cfg.base_model_id, use_multi_image=cfg.use_multi_image,
    use_per_frame_progress_token=cfg.use_per_frame_progress_token,
    max_frames=cfg.max_frames)

frames = record_the_attempt()   # whole numbers, shaped time by height by width by colour
encoded = encoder.encode_samples([(frames, 'put the red mug on the shelf')])
batch = {f'{ROBOMETER_FEATURE_PREFIX}{key}': value for key, value in encoded.items()}
if judge.compute_reward(batch)[0] < 1.0:
    stop_the_cell('the judge did not see the mug on the shelf')
```

LeRobot supplies the download, the preparation of the frames and the sentence for the
backbone, and the one call that returns a number. What you supply is the frames and the
sentence, and the sentence is not a formality: it is the only thing that tells the model
what success means here. What you decide is when to ask, because asking after every
put-down costs seconds of cell time, and what to do with an answer you cannot check. When a judge
says a task failed and you want to know why, REFLECT, by Zeyi Liu and colleagues in
[June 2023](https://arxiv.org/abs/2306.15724), is the paper to read: it turns the robot's
own readings into a written summary and asks a large language model to explain the failure
and suggest a fix.

### 5.6 Sentinel, for an arm driven by a learned policy

This one is also **worth betting on**, and it is the entry that did not exist as a category
a few years ago, because it watches the policy rather than the arm. Christopher Agia,
Rohan Sinha, Jingyun Yang, Zi-ang Cao, Rika Antonova, Marco Pavone and Jeannette Bohg, at
Stanford University with NVIDIA Research, published it in
[October 2024](https://arxiv.org/abs/2410.04640) and presented it at the Conference on
Robot Learning that year. It joins two detectors. The first measures whether the chunks of
future actions that a generative policy produces agree with each other from one step to the
next, which catches the policy behaving erratically. A **generative policy** is one that
samples its actions from a learned distribution and so gives a different answer each time
you ask it, which the
[diffusion and flow policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md#2-what-goes-in-and-what-comes-out)
page describes. The second shows the video to a vision-language model, which catches the
opposite case, where the policy keeps acting steadily and makes no progress. The paper
reports that the two together detect 18 per cent more failures than either one alone.

You would pick this rather than the obvious alternative, the anomaly detector on sensor
features in section 5.4, when a learned policy drives the arm. A policy that has drifted
away from what it was trained on often moves smoothly and safely while making no progress,
so the forces and the positions all look normal and only the policy's own output gives it
away. Section 5.4 cannot see that output at all.

What it costs you is applicability and upkeep. The first detector requires a policy you can
sample several times at the same moment, so a policy that returns one fixed action gives it
nothing to compare. The repository is research code: it is managed with Poetry, tested on
Ubuntu 20.04 with Python 3.10.13, it does not train policies, and its released evaluation
datasets need about 319 GB of disk space. Its vision-language half calls a hosted model, so
its scripts read that model's key from the environment. The licence in the repository's own
`LICENSE` file is MIT, which is the easy part.

The repository is [agiachris/sentinel](https://github.com/agiachris/sentinel). Its own
detectors run over recorded attempts, so the few lines below are the first detector's idea
in the smallest live form, to show what it measures.

```python
import numpy as np

previous = None
while running:
    # A generative policy returns a chunk of future actions rather than one action.
    # Ask it several times at the same moment: the answers differ, and that is the point.
    chunks = np.array([policy(observation) for _ in range(8)])   # (8, steps, joints)
    if previous is not None:
        # The part of the previous chunk that covers the same future steps as this one.
        overlap = min(previous.shape[1], chunks.shape[1]) - 1
        disagreement = np.abs(previous[:, 1:overlap + 1].mean(0)
                              - chunks[:, :overlap].mean(0)).mean()
        if disagreement > limit:    # the limit comes from the calibration attempts
            stop_and_ask_for_help()
    previous = chunks
```

What the repository supplies, and what you should not write yourself, is the proper version
of that comparison and the calibration behind the limit. It measures the disagreement as a
statistical distance between the two sets of samples rather than between their averages,
and it fixes the limit from a set of recorded attempts made in the conditions the policy was
trained for, which its dataset naming calls the calibration set. What you supply is a
policy you can sample repeatedly, those calibration attempts, and the response, because an
arm that detects its own confusion and carries on has gained nothing.

### 5.7 How to choose

Use section 5.1 for collisions and section 5.4 for failed tasks, and treat everything else
here as an answer to a problem you have measured. The momentum observer is already on most
arms, it needs no data, and a day spent recording how big its residual gets in ordinary
work tells you whether you need anything more. The anomaly detector needs only the good
runs you are already producing.

Four things change that.

- **Section 5.1 misses a contact you can feel with your hand.** Then section 5.2, which
  learns what the physics model got wrong so that the limit can come down. This is the
  only entry here that makes gentle collisions catchable.
- **The arm gives you no expected torque at all**, because it reports motor current and
  its description file is not trustworthy. Then the classifier shape of section 5.3, and
  expect to cause real collisions to train it.
- **One cell does many different tasks, or you need the failure described in words.** Then
  section 5.5, with the judges themselves taken from the
  [reward and progress models](../../06_movement-models/03_also-used/03_reward-and-progress-models.md#7-well-known-models-and-libraries)
  page. Ask after a step rather than during one, because the answer takes seconds.
- **A generative policy drives the arm.** Then section 5.6 as well as section 5.4, because
  the policy's own output shows the failure before the sensors do.

One thing should not change your choice. None of these six replaces the arm's certified
safety function, for the reason section 7 gives, and a learned detector that has to be
right to keep a person safe is a learned detector in the wrong place.

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
[Arm dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md)
works out the torque each joint should need, and
[sensor streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#thresholds-that-do-not-flicker-hysteresis-and-debouncing)
turns the gap into an alarm that does not flicker.
[Safety monitoring](../../../06_programming-techniques/07_control-and-motion/02_most-used/04_safety-monitoring.md)
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
