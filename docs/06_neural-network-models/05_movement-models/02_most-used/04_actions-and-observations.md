# Actions and observations

This page is about the numbers that go into a policy and the numbers that come
out. The earlier pages of this chapter said that a policy turns an observation
into an action. This page opens both of those up. It shows what each number
means, how it is written down, and why the choice matters.

It answers six questions. Should the action be joint angles or a position for the
gripper? Should it be a place to go to, or a change from where the arm is now? How
do you write down a turn? Why must every number be rescaled before training? How
fast should the policy run? And when can data recorded on one robot be used to
train a policy for another?

It is for a reader who has read [behaviour cloning](01_behaviour-cloning.md) and
knows what a policy, an observation and an action are. These choices look like
small details. In practice they decide whether a policy trains at all, and whether
someone else's recordings are any use to you.

> Before this page, it helps to have read [rigid
> transforms](../../../05_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md),
> which explains frames, rotation matrices and quaternions. Sections 3 to 5 of this
> page use all three.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [What an observation is made of](#2-what-an-observation-is-made-of)
3. [Joint angles or gripper pose](#3-joint-angles-or-gripper-pose)
4. [A place to go to, or a change from here](#4-a-place-to-go-to-or-a-change-from-here)
5. [How a turn is written down](#5-how-a-turn-is-written-down)
6. [The gripper number](#6-the-gripper-number)
7. [Rescaling every number before training](#7-rescaling-every-number-before-training)
8. [How often the policy decides, and chunks](#8-how-often-the-policy-decides-and-chunks)
9. [A worked example: one recorded moment](#9-a-worked-example-one-recorded-moment)
10. [Using data from another robot](#10-using-data-from-another-robot)
11. [What goes wrong](#11-what-goes-wrong)
12. [Libraries and models](#12-libraries-and-models)
13. [Why these choices matter, and what they cost](#13-why-these-choices-matter-and-what-they-cost)
14. [The written alternative](#14-the-written-alternative)
15. [Where to read next](#15-where-to-read-next)

---

## 1. The idea in one sentence

A policy only ever sees lists of numbers, so what each number means, and what size
it is, decides what the policy can learn.

Here is an everyday example. Imagine you give a friend directions to your house.
You could say "go to 12 Station Road". That is an address, and it works from
anywhere. You could say "turn left, then walk 200 metres". That is a change from
where they stand, and it only works if they start in the right place. You could
also give the directions in miles to someone who thinks in kilometres. All three
describe the same house. But some of them will get your friend lost.

A policy has the same problem. The same movement of the arm can be written down
in several ways. The network has to learn from whichever way you chose. Some ways
are easy for a network to learn, and some are not.

---

## 2. What an observation is made of

The **observation** is everything the policy is given at one moment. For a robot
arm, it usually has three parts.

- **Camera pictures.** Often one camera looks at the table from a fixed place, and
  one camera sits on the arm's wrist. The pictures are usually made smaller before
  they go in. Many policies use 224 by 224 pixels. ACT uses 480 by 640.
- **The arm's own state.** This is the angle of each joint and how open the gripper
  is, read from the arm's own sensors. People call this **proprioception**, which
  means the body's sense of its own position. Some policies also get the gripper's
  position in space, worked out from the joint angles.
- **Sometimes more.** A sentence saying what task to do, as in
  [vision-language-action models](../../06_language-models/02_most-used/01_vision-language-action-models.md).
  The last one or two moments, so the policy can tell which way things are moving.
  Force readings, for tasks with a lot of pressing.

Each picture goes through a seeing network first, which turns it into a list of
numbers. The rest of the policy then sees one long list of numbers. The joint
angles, the gripper width and the picture numbers all sit side by side in that
list. This is why the rest of this page matters. Nothing in the list says "this
number is in radians" or "this number is in metres". The network only sees values.

The **action** is what the policy gives back. It has three parts: where the arm
should move, how it should be turned, and how open the gripper should be. Sections
3 to 6 go through them one at a time.

---

## 3. Joint angles or gripper pose

There are two common ways to say where the arm should go.

The first is **joint angles**. The action is one target angle for each joint. For a
six-joint arm, that is six numbers. ACT on ALOHA works this way, and so do most
policies trained with cheap LeRobot arms such as the SO-101.

The second is the **gripper pose**, also called the **end-effector pose**. The
**end-effector** is the tool at the end of the arm, here the gripper. Its **pose** is
where it is, as three numbers (x, y and z), and how it is turned. The action says
where the gripper should be. Ordinary code then works out the joint angles that put
it there. That code is called **inverse kinematics**, and Book 5 explains it in
[numerical inverse kinematics](../../../05_programming-techniques/06_planning-and-search/02_most-used/02_numerical-inverse-kinematics.md).

The picture below shows why the choice matters. Two different arms put the gripper
in exactly the same place, pointing straight down at a block. The script that drew
it worked out each arm's joint angles.

![Two arms with different link lengths put the gripper at the same pose using different joint angles](../../../images/movement-models/actions-and-observations/joints-or-gripper-pose.svg)

The gripper pose is the same for both arms: 40 cm out, 10 cm up, pointing down.
The joint angles are not. Arm A needs 59°, −72° and −77°. Arm B needs 71°, −104°
and −56°.

So the two ways have different strengths.

- **Joint angles** need no extra code. They say exactly what each motor should do,
  so the arm can never be asked for a pose it cannot reach. They are the natural
  choice when the recording comes from a leader arm, which already records joint
  angles. But they only mean something on one kind of arm.
- **Gripper pose** means the same thing on any arm. "Put the gripper 2 cm above the
  block" makes sense for every robot. It is also closer to the task, because the
  task is about where the gripper goes. But it needs inverse kinematics underneath,
  and that can fail near the edge of the arm's reach.

---

## 4. A place to go to, or a change from here

The second choice is whether the action names a place or a change.

An **absolute** action names a place. "Move the gripper to x = 42 cm, y = 10 cm."
The numbers are measured from a fixed point, usually the base of the robot.

A **relative** action, also called a **delta** action, names a change from where
the arm is now. "Move the gripper 1 cm to the left." The word **delta** is the name
of the Greek letter Δ, which people use to mean "a change in".

The picture below shows the same kind of recording made on two robots. On both,
a person reached from a resting spot to a mug somewhere on the table. The only
difference is that robot B is bolted to the table in a different place. Each dot
is one recorded moment.

![Left: absolute targets from two robots form two separate clouds. Right: the changes from one moment to the next form one shared cloud](../../../images/movement-models/actions-and-observations/absolute-or-relative.svg)

On the left, the targets are measured from each robot's own base, so the two
robots' clouds sit in different places. The middle of robot A's cloud is at about
(42, 10) cm and the middle of robot B's is at about (56, −16) cm. On the right, the
same movements are written as the change from one moment to the next. Now both
clouds are in the same place. For both robots, the average change is about 5 mm
along x and about −7 to −8 mm along y.

This is the main reason people like relative actions. A network trained on the
left-hand numbers has to learn two separate things, one for each robot. A network
trained on the right-hand numbers learns one thing, and the recordings from the two
robots help each other.

Relative actions have costs too.

- **Small errors add up.** Each change is added to where the arm is now. If each
  step is a little short, the arm ends up well short after a hundred steps. An
  absolute target does not drift in this way.
- **The change depends on the step length.** "1 cm per step" means 50 cm a second
  at 50 steps a second, and 10 cm a second at 10 steps a second. Section 8 comes
  back to this.

Many recent models use a middle way. The action chunk is written relative to the
pose the gripper had at the start of the chunk, not relative to the step before.
Every target in the chunk then refers to the same starting point, so small errors
do not add up inside the chunk.

---

## 5. How a turn is written down

The action also says how the gripper should be turned. A turn in 3D has three
degrees of freedom, but there are several ways to write it as numbers. Book 5's
page on [rigid transforms](../../../05_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md#quaternions-in-plain-words)
explains each one. Here the question is which one a network can learn.

- **Three angles**, often called roll, pitch and yaw, or **Euler angles**. They are
  easy for people to read.
- A **quaternion**, which is four numbers that store the axis of the turn and how
  far it turns.
- A **rotation matrix**, which is nine numbers.
- The **six-number form**, which keeps only the first two columns of the rotation
  matrix. The third column can always be worked out from the other two. This form
  was proposed for neural networks by Zhou and others in 2019.

The problem is that some of these forms jump. The picture below turns the gripper
smoothly from 150° to 210° about the vertical, with a small tilt, and plots the
numbers each form gives.

![As the gripper turns smoothly past 180°, the yaw angle jumps by 360°, the quaternion's numbers jump, and the six numbers change smoothly](../../../images/movement-models/actions-and-observations/rotation-number-jumps.svg)

At 179°, the yaw number is 179. At 181°, it is −179. The gripper moved by 2°, but
the number moved by 358°. The quaternion jumps as well. Many libraries keep its
last number positive, so its z number flips from 0.996 to −0.996 at the same place.
The six numbers change by only about 0.03 each.

A jump like this is bad for a network. A network gives outputs that change
smoothly with its inputs. Near 180°, the recorded answers are sometimes 179 and
sometimes −179 for nearly the same picture. The network is trained to be close to
both, so it learns their average, which is 0. That is a turn of 0° instead of 180°,
which is the gripper facing the wrong way. This is the same averaging problem that
[behaviour cloning](01_behaviour-cloning.md#two-good-ways-become-one-bad-way)
describes, caused only by how the number is written.

For this reason many policies output the six-number form, and people usually
store rotations as quaternions and show them to people as three angles. Small
changes of rotation from one step to the next are less of a problem. A change of a
few degrees stays far from the jump, so three angles are often used for relative
actions.

---

## 6. The gripper number

The last number in the action says how open the gripper should be. There are two
common forms.

- **A width.** A number from fully closed to fully open, such as 0 to 8 cm. It lets
  the policy close gently on something soft.
- **Open or closed.** One number that is 0 or 1. The gripper's own controller then
  closes until it feels resistance. Many datasets use this form.

Datasets disagree about which way round it goes. In some, 1 means open. In others,
1 means closed. If you mix them without checking, the policy learns to open when it
should close for half of its data. Always check the gripper convention of every
dataset you use.

---

## 7. Rescaling every number before training

The numbers in one observation have very different sizes. A joint angle in
radians is often between −3 and 3. A wrist speed can be 5 or more. A gripper
width in metres is between 0 and 0.08. A change in position per step might be
0.002 m.

The picture below shows four such numbers from a made-up set of recordings. The
coloured box covers the middle half of the values, and the line covers nearly all
of them.

![Left: four numbers on their own scales, where the gripper width and the change in x are too small to see. Right: after normalising, all four have the same spread](../../../images/movement-models/actions-and-observations/normalising-each-number.svg)

On the left, the gripper width and the change in x are so small that they almost
vanish. On the right, each number has had its average taken off and has been
divided by its **spread**. The spread here is the **standard deviation**, a
measure of how far the values usually are from their average. After this, every
number has an average of 0 and a spread of 1. This step is called **normalising**.

It matters for two reasons.

The first is the loss. Training adds up the error in every number. Suppose the
policy is wrong by one spread in each of the four numbers. Without normalising, the
script found that the wrist speed makes up 94.6% of the loss. The gripper width
makes up 0.016%, and the change in x makes up 0.0002%. So training works hard on the
wrist speed and almost ignores the gripper, which is often the number that decides
whether the task succeeds.

The second is the network's inside. The layers of a network work best when their
inputs are around −1 to 1. Very large or very small inputs make training slow or
unstable.

There are two common ways to normalise.

- **Mean and spread.** Take off the average, divide by the standard deviation.
- **Smallest to largest.** Stretch the values so that the smallest becomes −1 and
  the largest becomes 1. Diffusion and flow policies usually do this for actions,
  because their cleaning-up process assumes the answer lies in a fixed range.

The statistics come from the training data. They must be saved with the policy,
because the same numbers must be used when the policy runs on the robot. The
policy's output is then turned back into real units with the same numbers, in
reverse. LeRobot does this for you. Each dataset keeps a file of statistics, in
`meta/stats.json`, with the average, standard deviation, smallest and largest
value of every number. Each policy's settings say which of the two ways to use for
pictures, for the arm's state and for actions.

---

## 8. How often the policy decides, and chunks

The **control rate** is how many times a second the arm gets a new target. It is
measured in **hertz**, written Hz, which means "times a second". ALOHA records at
50 Hz. The DROID dataset records at 15 Hz. The Bridge dataset, recorded on small
WidowX arms, records at 5 Hz.

The control rate is part of what an action means. This matters most for relative
actions. Say a recording at 50 Hz has the gripper move 2 mm each step, which is
10 cm a second. If a policy trained on it runs at 10 Hz and sends the same 2 mm
each step, the arm moves at 2 cm a second. It moves the right way at a fifth of the
speed, and it may never reach the mug before the time runs out.

An **action chunk** is a list of the next few actions, predicted together. The
[action chunking page](02_action-chunking-transformers.md) explains why chunks help.
A chunk's length only means something together with the control rate. ACT's chunk
of 100 steps at 50 Hz covers 2 seconds. A chunk of 16 steps at 10 Hz covers 1.6
seconds. A chunk of 16 steps at 50 Hz covers only a third of a second.

So when you use a policy or a dataset, write down three things together: the
control rate, the chunk length, and how many steps of each chunk the arm plays
before the policy is asked again. How fast the policy itself must run is covered
in [running a model on a robot](../../09_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md#2-how-fast-is-fast-enough).

---

## 9. A worked example: one recorded moment

Here is one moment from a recording on arm A, the arm on the left of the first
picture. The numbers come from the diagram script for this page,
`docs/diagrams/movement_models_3.py`, which prints them when it runs.

The arm is holding the gripper 40 cm out and 10 cm up, pointing straight down. At
the next moment of the recording, the gripper has moved 1 cm towards the robot
and turned 2°. The table below writes that one movement in four ways. Read each
row as one way a dataset could store the same action.

| Way of writing the action | The numbers |
| --- | --- |
| Absolute joint angles | 61.19°, −75.77°, −73.42° |
| Relative joint angles | +2.61°, −4.23°, +3.63° |
| Absolute gripper pose | x = 39 cm, y = 10 cm, turned −88° |
| Relative gripper pose | x −1 cm, y 0 cm, turn +2° |

Notice two things. The relative gripper pose is the only row that a person could
read and understand at once. And a small, simple move of the gripper can need all
three joints to change, by different amounts.

Now the turn. In 3D, a turn of 30° about the vertical axis, written in the
six-number form, is (0.866, 0.5, 0, −0.5, 0.866, 0). A network never outputs six
numbers that fit together exactly. Say it outputs (0.80, 0.55, 0.05, −0.45, 0.84,
0.02). The program tidies this into a real rotation in three steps.

1. Make the first three numbers length 1. This gives (0.823, 0.566, 0.051).
2. Remove from the second three numbers any part that points along the first, and
   make the rest length 1. This gives (−0.567, 0.823, 0.015).
3. Work out the third column from the first two with a **cross product**, which
   gives the direction at right angles to both. This gives (−0.034, −0.042, 0.999).

The result is a turn of about 34.5° about the vertical, close to what the network
meant. The same repair cannot be done for three angles that jumped by 358°.

Last, the rescaling. In the made-up recordings, the gripper width has an average
of 0.0387 m and a spread of 0.0326 m. An open gripper at 0.07 m becomes
(0.07 − 0.0387) / 0.0326 = 0.96. A change in x of 0.010 m, with an average of
0.0020 m and a spread of 0.0040 m, becomes 2.0. After rescaling, both numbers are
of an ordinary size, and the loss treats them fairly.

---

## 10. Using data from another robot

Robot recordings are slow and costly to collect. So people want to train one policy
on recordings from many different robots. This is called **cross-embodiment**
training. An **embodiment** is one kind of robot body: its arms, joints, gripper and
cameras. Whether this works depends almost entirely on the choices above.

The first large attempt was **Open X-Embodiment**, from 2023. More than twenty
laboratories pooled recordings from 22 kinds of robot into one dataset. Book 3
tells its story in
[the foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md#32-open-x-embodiment-and-the-data-that-made-openness-possible).
The policies trained on it, RT-1-X and RT-2-X, wrote every robot's action as the
same seven numbers: a change in gripper position, a change in gripper turn, and the
gripper. But the numbers were not put into the same frame or the same scale for
every robot. So the same seven numbers could mean different movements on different
robots, and the policy had to guess which robot it was on from the pictures.

**Octo**, from 2024, was trained on about 800,000 recordings from Open
X-Embodiment. It normalised each dataset's actions with that dataset's own
statistics, so that a large arm and a small arm gave numbers of the same size. Its
authors also showed that it can be fine-tuned for a robot with a different kind of
action, such as joint angles, by giving it a new output part.

**NVIDIA's GR00T N1.7**, released in 2026, went further. Its actions are written
relative to the gripper's current pose. The
[foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md#6-nvidia-isaac-gr00t)
records that NVIDIA names this as the key factor in how well it works across
robots. A move of 3 cm to the left means the same thing on every body, but a target
position does not. The same choice let it learn from 20,000 hours of video of human
hands. A human hand moving 3 cm to the left is written the same way as a gripper
moving 3 cm to the left. The page on
[learning from human video](../03_also-used/04_learning-from-human-video.md) goes
further into this.

**Physical Intelligence's π0.7**, from 2026, takes another route. Each training
recording carries a label that says whether its actions are joint angles or gripper
poses. The model learns what the label means, and you can choose the kind of action
when you run it. The
[foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md#4-physical-intelligence-and-the-pi-models)
describes it.

The pattern is the same in all four. Data from another robot helps only when its
numbers mean the same thing as yours, or when the model is told what they mean.
The questions to ask of any dataset are the ones on this page. Are the actions
joint angles or gripper poses? Absolute or relative? Which rotation form, and which
frame? Which way round is the gripper? What control rate? And were the numbers
normalised, and with what statistics?

---

## 11. What goes wrong

**The arm moves at the wrong speed.** It goes the right way, but too slowly or too
fast. The usual cause is relative actions played at a different control rate from
the recording. Check the rate the data was recorded at.

**The gripper spins suddenly by nearly a full turn.** The usual cause is three
angles or a quaternion with a jump in it, near 180°. Use the six-number form for the
network's output, or keep all training turns away from the jump.

**The gripper opens when it should close.** The usual cause is two datasets with
opposite gripper conventions. Check the convention of every dataset.

**The arm ignores the gripper, or moves only one joint.** The usual cause is
numbers that were not normalised, so the loss was dominated by one large number. Or
the statistics saved with the policy do not match the ones used in training.

**The arm drifts further and further from where it should be.** Relative actions
add up small errors. Write the chunk relative to its starting pose, or use absolute
targets for the final approach.

**The arm stops at the edge of its reach, or jerks.** Gripper-pose actions need
inverse kinematics, which can fail or jump near the edge of the reach. Keep the
task well inside the reach, or use joint angles.

**Mixed data makes the policy worse, not better.** The datasets' numbers mean
different things. Convert them to one convention before training, or give the
model a label for each kind.

---

## 12. Libraries and models

These are real tools and models that make these choices for you, or let you make
them.

- **LeRobot**, from Hugging Face, stores recordings in one standard format. Each
  dataset lists its numbers by name, such as `observation.state` and `action`, and
  keeps their statistics in `meta/stats.json`. Each policy's settings choose how to
  normalise pictures, state and actions. Book 3 describes it in
  [data and demonstration](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#71-what-it-is-and-why-it-won).
- **Octo** normalises each dataset separately and can be given a new output part
  for a new kind of action.
- **Open X-Embodiment** stores many robots' recordings in one file format. Read
  each dataset's description before mixing it with others.
- **GR00T N1.7** writes its actions relative to the gripper's current pose.
- **SciPy's** `scipy.spatial.transform.Rotation` class converts between three
  angles, quaternions and rotation matrices. The six-number form is the first two
  columns of the matrix it gives.
- The **Universal Manipulation Interface**, or **UMI** (2024), records
  demonstrations with a handheld gripper and a wrist camera. It writes its actions
  relative to the gripper's current pose, so that the same recordings can train
  policies for different arms.

---

## 13. Why these choices matter, and what they cost

It helps to look at this through four questions: what it is, what it does for you,
why you would pick it over the obvious alternative, and what it costs.

The choices on this page are the way a movement is written as numbers for a policy.

Choosing them well makes a policy train faster and more reliably, and it decides
whether other people's recordings can help you.

The obvious alternative is to store whatever numbers your robot happens to produce.
Usually that is absolute joint angles in the robot's own units at the robot's own
rate. This is the right choice for a single robot trained only on its own data. It
is simple, and nothing needs converting. A policy trained with ACT on one SO-101
arm works well this way. The other choices start to pay when you want to mix data
from more than one robot, or from human video, or to reuse a model someone else
trained. Then relative gripper-pose actions, the six-number rotation form and
careful normalising are what make the numbers mean the same thing everywhere.

What it costs you:

- Gripper-pose actions need inverse kinematics and a correct model of the arm.
- Relative actions drift, and they tie the data to one control rate.
- Converting a dataset means reading its conventions carefully. A single wrong
  sign or axis order gives no error message, only a policy that does not work.
- The statistics must travel with the policy. If they are lost or mismatched, the
  policy's outputs are the wrong size.

---

## 14. The written alternative

None, because this page does not describe a model that does a job. It describes the
numbers that every policy reads and writes. Written code makes the same choices, and
Book 5 explains them there. [Rigid
transforms](../../../05_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md)
covers the ways to write down a turn, and [numerical inverse
kinematics](../../../05_programming-techniques/06_planning-and-search/02_most-used/02_numerical-inverse-kinematics.md)
turns a gripper pose into joint angles.

The difference is what a bad choice costs. A number that jumps, such as a yaw angle
passing 180°, can trouble written code too, but a programmer can handle the jump
with a special case. A network cannot. It learns the average of the two sides
instead, as section 5 shows.

---

## 15. Where to read next

- [Action chunking transformers](02_action-chunking-transformers.md) use absolute
  joint-angle chunks, and are a good place to see these choices in a working
  policy.
- [Diffusion and flow policies](03_diffusion-and-flow-policies.md) explain why
  their actions are rescaled to a fixed range.
- [Learning from human video](../03_also-used/04_learning-from-human-video.md)
  depends on relative gripper-pose actions.
- Book 5's [rigid transforms](../../../05_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md)
  explains rotation matrices, quaternions and three angles in detail, and Book 3's
  [Euler angles, intrinsic and extrinsic](../../../03_frameworks/03_arm-movement/08_frames-and-conventions.md#24-euler-angles-intrinsic-and-extrinsic)
  explains why three angles need a stated convention.
- To go back to the list of all the kinds of policy, read
  [the chapter overview](../01_overview.md).
