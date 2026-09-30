# Grasp quality models

This page is about grasp models that do not propose grasps at all. Something else
proposes a grasp. A grasp quality model looks at it and gives one number: how
likely the grasp is to hold. The robot tries many possible grasps this way and
keeps the best.

The page answers these questions. Why would you split proposing from scoring? What
does a quality model take in and give back? How does it work inside? Where do its
millions of training examples come from? Which real models do this? What goes
wrong, and what does it cost?

It is for a reader who has read the [grasp models overview](../01_overview.md). The
[top-down](01_top-down-grasp-detection.md) and
[six-degree-of-freedom](../02_most-used/01_six-dof-grasps.md) pages help, because the grasps a
quality model scores often come from them. The
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md) page explains
the training loop this page relies on.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a mug on a table](#6-a-worked-example-a-mug-on-a-table)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. What it is

A grasp quality model takes one proposed grasp and gives the chance that it will
hold.

Think of choosing a melon at a market. You do not know in advance which melon is
best. You pick one up, press it, smell it and give it a mental mark. Then you pick
up the next one. After six melons you buy the one with the best mark. A grasp
quality model does the marking. Ordinary code does the picking up: it proposes
grasp after grasp and asks the model to mark each one.

This split has a name. The code that proposes grasps is the **sampler**. It makes
**candidates**: possible grasps that have not been checked yet. The quality model
is the **scorer**, and it is sometimes called an **evaluator** or a **critic**.

![Five candidate grips on a mug, each with a score, sorted](../../../images/grasp-models/grasp-quality-models/sample-then-score.svg)

On the left, five candidate grasps on a mug seen from above, each with a score from
the model. On the right, the same scores sorted. The arm tries only the top one,
which closes across the mug's body. The scores are made up for this drawing.

---

## 2. What goes in and what comes out

The input has two parts.

- What the camera sees, usually a depth picture or a point cloud of the scene.
- One candidate grasp, such as a position, an angle and how deep the jaws go.

The output is one number between 0 and 1. It is the model's guess at the chance
that this grasp will hold the object when the arm lifts. A **probability** is this
kind of number: 0 means "certainly not", 1 means "certainly", and 0.87 means "87
times out of 100".

The model is run once for each candidate. If the sampler proposes 200 grasps, the
model is run 200 times, or on all 200 together in one batch.

---

## 3. How it works inside

The best-known design is Dex-Net's **grasp quality convolutional neural network
(GQ-CNN)**. It works in four steps.

1. **Cut out a patch.** Code cuts a small square out of the depth picture, centred
   on the candidate grasp's centre.
2. **Turn the patch.** Code turns the square so that the grasp's jaws sit at its
   left and right edges. Every patch the network sees is lined up the same way.
   The network never has to learn what a grasp at 30 degrees looks like as a
   separate case.
3. **Run the network.** A small convolutional neural network reads the turned patch.
   It is also given one more number: how deep the gripper would go. The
   [inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md#4-convolutional-layers-small-pattern-detectors)
   page explains how such a network reads a picture.
4. **Give one number.** The network ends with a single output: the chance that the
   grasp holds.

![One candidate cut out, turned, scored by a network, giving one number](../../../images/grasp-models/grasp-quality-models/crop-and-score.svg)

A candidate on the depth picture, the patch cut out around it and turned so the
jaws sit left and right, a small network, and one number out.

Step 2 is the clever part. Turning each patch removes the angle from the problem.
The network only has to learn one thing: whether the shape between two jaws, lined
up left and right, can be held.

Quality models for 6-DoF grasps work the same way with a point cloud. Code takes the
points that lie between the gripper's fingers, turns them into the gripper's own
frame, and passes them to a point cloud network. The
[point cloud models](../../03_3d-models/02_most-used/01_point-cloud-models.md) page explains those
networks.

### Where the candidates come from

A quality model is only as good as the candidates it is given. Three samplers are
common.

- The simplest sampler picks at random and then checks the geometry. Code picks pairs of points on the object's edge
  that face each other, so both jaws would press straight in. Book 3's
  [antipodal test](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test)
  explains this check.
- A better sampler refines the best candidates. Code samples some candidates and scores them. It then
  samples new candidates near the best ones and scores those. After a few rounds the
  candidates gather around the best grasp. This is called the **cross-entropy
  method**.
- The candidates can also come from another model. A [6-DoF grasp model](../02_most-used/01_six-dof-grasps.md) proposes the
  candidates, and the quality model re-scores them.

---

## 4. How it is trained

Every example is a picture, a grasp and a label: 1 if the grasp held, 0 if it did
not. There are two ways to get those labels, and they cost very different amounts.

![Labels calculated on 3D models, and labels from a real arm](../../../images/grasp-models/grasp-quality-models/labels-two-ways.svg)

On the left, grasps on a 3D model are judged by physics formulas, and a depth
picture is drawn by the computer. On the right, a real arm tries each grasp, lifts,
and checks. Both give the same kind of example: a picture, a grasp and a 1 or a 0.

### Calculated on 3D models

This is how Dex-Net was trained.

1. Collect thousands of 3D models of objects.
2. On each model, place many candidate grasps.
3. For each grasp, compute a **quality metric**: a number from physics formulas
   that says how much push or twist the grasp can resist before the object slips.
   Book 3's
   [grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute)
   explains these formulas.
4. Repeat the calculation many times with small random changes: the object a little
   moved, the gripper a little off, the friction a little lower. Average the
   results. A grasp that still holds after all these small changes is called
   **robust**. The label is 1 if the average is high enough.
5. Draw a depth picture of the object from a virtual camera, as a real camera
   would see it, with added noise.

This way is cheap and fast. Dex-Net 2.0 was trained on 6.7 million examples made
like this, with no robot involved.

### Tried on a real arm

The other way is to let real arms try grasps for weeks.

1. The arm looks at a bin, picks a grasp, often at random at first, and tries it.
2. It lifts and checks whether anything is held. A camera or the gripper's finger
   position tells it.
3. The picture, the grasp and the result are saved.
4. The arm drops the object back in the bin and tries again, day and night.

Google's arm farm used this way. Between 6 and 14 arms made more than 800,000 grasp
attempts to train one quality model. Its labels are real, with no gap between
simulation and reality. It is also very slow and expensive.

---

## 5. Well-known models

These are real models of this kind.

- **Dex-Net 2.0 and its GQ-CNN** (2017), from the University of California,
  Berkeley, scores top-down grasps on depth pictures as described above. It was
  trained on 6.7 million synthetic examples. Book 3's
  [planar models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#2-planar-models-a-grasp-is-a-rectangle)
  section notes that its licence allows only education, research and not-for-profit
  use.
- **Pinto and Gupta's self-supervised grasping** (2016), from Carnegie Mellon
  University, let a real robot collect its own labels by trying grasps for hundreds
  of hours. **Self-supervised** means the robot made its own labels, with no person
  marking anything.
- **Levine and others' hand-eye coordination network** (2016), from Google, is the
  arm farm above. The network scored how likely a small movement of the gripper
  was to end in a good grasp. The arm used those scores to steer towards the object.
- **QT-Opt** (2018), also from Google, learned a quality score for arm movements
  from more than 580,000 real grasp attempts. It learned by trial and error, which
  is covered in the
  [reinforcement learning policies](../../05_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  page.
- **GPD** and **PointNetGPD** score 6-DoF candidates from a point cloud. GPD uses a
  small CNN, and PointNetGPD uses a point cloud network. Both sample candidates with
  geometry first.

Most [6-DoF models](../02_most-used/01_six-dof-grasps.md#5-well-known-models) also contain a
scorer inside them. 6-DOF GraspNet and GraspGen, for example, each have a separate
network whose only job is to score the grasps the generator made.

---

## 6. A worked example: a mug on a table

A depth camera looks down on a mug. The arm has a parallel-jaw gripper.

1. The camera takes one depth picture.
2. The sampler finds pairs of edge points on the mug that face each other. It
   makes 100 candidate grasps.
3. For each candidate, code cuts out a patch, turns it, and passes it with the
   gripper depth to the quality model. The model gives 100 scores.
4. The sampler makes 100 new candidates near the 10 best, and the model scores
   those too. This repeats three times.
5. Code drops any candidate the arm cannot reach, or that is wider than the gripper
   opens.
6. The arm tries the candidate with the highest score that is left. On the mug in
   the picture above, that is the grasp across the body, not the one on the handle
   or the rim.
7. If the grasp fails, the arm tries the next one. It does not need to run the
   model again unless the mug moved.

---

## 7. What goes wrong

- It inherits the formula's blind spots. A model trained on calculated labels
  learned to copy a physics formula. Where the formula is wrong, the model is wrong
  in the same way. Book 3's
  [trap in the epsilon metric](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#92-the-trap-in-the-epsilon-metric)
  shows one such case.
- It can only pick from what it is shown. If the sampler never proposes the
  best grasp, the model cannot choose it. A good scorer with a poor sampler gives
  poor grasps.
- It is slow with many candidates. Each candidate needs its own run of the
  network. A few hundred candidates is fine. A few hundred thousand is not.
- It can be sure and wrong. A score of 0.95 is the model's guess, not a
  promise. On a shape unlike anything in training, it may give a high score to a
  grasp that fails. The
  [running a model on a robot](../../01_what-models-are/05_running-a-model-on-a-robot.md#5-how-sure-the-model-is-and-why-it-can-be-sure-and-wrong)
  page explains why.
- It knows nothing about the task. Like every grasp model, it scores whether
  the object stays in the gripper, and nothing else.

People reduce these problems in three ways. They use a good sampler. They mix a few
real robot attempts into the calculated training data. And they add their own
checks for reach, collisions and task rules after the model.

---

## 8. Why this kind, and what it costs

A grasp quality model takes a picture and one candidate grasp, and gives the chance
that the grasp holds.

What it does for you is choose well among many options. It also lets you control
the options. Because you write the sampler, you can limit the candidates to grasps
that suit your arm, your gripper and your task before the model sees them.

The obvious alternative is to skip the network and compute the quality metric
directly, with the formulas in Book 3's
[grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute).
The formulas need a full 3D model of the object and its exact position. A quality
model needs only one noisy depth picture of an object it has never seen. That is
the reason to choose it.

The other alternative is a model that generates good grasps directly, such as a
[top-down detector](01_top-down-grasp-detection.md) or a
[6-DoF model](../02_most-used/01_six-dof-grasps.md). Those are faster, because they do not score
candidates one by one. A separate scorer is worth it when you want to control the
candidates yourself, or when you want a second opinion on another model's grasps.

What it costs you is time and training data. Scoring hundreds of candidates takes
longer than one pass of a generator. The training data needs either thousands of
3D object models or weeks of real robot time.

---

## 9. Where to read next

- [Six-degree-of-freedom grasps](../02_most-used/01_six-dof-grasps.md) covers the generators that
  most quality models are paired with today.
- [Reinforcement learning policies](../../05_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  covers learning by trial and error, which QT-Opt used.
- [Force and slip models](../../08_touch-and-body-models/02_most-used/01_force-and-slip-models.md)
  covers checking, after the fingers close, whether the grasp is really holding.
- Book 3's [choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md)
  explains the physics formulas behind calculated labels.
- Book 3's [models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md)
  lists the code and licences for Dex-Net and GPD.
