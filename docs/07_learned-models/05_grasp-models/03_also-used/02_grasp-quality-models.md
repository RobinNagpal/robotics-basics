# Grasp quality models

This page is about grasp models that do not propose grasps at all, because
something else proposes the grasp and the model only judges it. A grasp quality
model looks at one proposed grasp and gives back a single number, which is how
likely that grasp is to hold. The robot therefore tries many possible grasps this
way and keeps the one with the best number.

So the page answers these questions, one section at a time. Why would you split
proposing a grasp from scoring it, and what does a quality model take in and give
back? How does it work inside, and where do its millions of training examples come
from? Which real models do this, what goes wrong with them, and what do they cost
you?

It is for a reader who has already read the
[grasp models overview](../01_overview.md). Because the grasps a quality model
scores usually come from them, the [top-down](01_top-down-grasp-detection.md) and
[six-degree-of-freedom](../02_most-used/01_six-dof-grasps.md) pages help as well.
The [how a model learns](../../01_what-models-are/02_how-a-model-learns.md) page
explains the training loop that this page relies on.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a mug on a table](#6-a-worked-example-a-mug-on-a-table)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

Since the introduction said only that this kind of model judges grasps, this
section says what the judging actually is. A grasp quality model takes one proposed
grasp and gives back the chance that the grasp will hold.

Think of choosing a melon at a market, where you do not know in advance which melon
is the best one. You pick one up, press it, smell it and give it a mental mark.
Then you pick up the next one and do the same. After six melons you buy the one
with the best mark. A grasp quality model does the marking, while ordinary code
does the picking up. That is because the code proposes grasp after grasp and asks
the model to mark each one.

Each half of this split has a name of its own. The code that proposes grasps is the
**sampler**, and the grasps it makes are **candidates**, which are possible grasps
that nobody has checked yet. The quality model is the **scorer**, and it is
sometimes called an **evaluator** or a **critic** instead.

![Five candidate grips on a mug, each with a score, sorted](../../../images/grasp-models/grasp-quality-models/sample-then-score.svg)

On the left are five candidate grasps on a mug seen from above, each with a score
from the model. On the right, the same five scores are sorted from best to worst,
so the ordering is easy to see. The arm tries only the top one, which closes across
the mug's body. The scores are made up for this drawing, so only their order means
anything.

---

## 2. What goes in and what comes out

Because the sampler and the scorer are separate, the scorer has to be told what the
sampler already knows, so its input has two parts.

- What the camera sees, usually a depth picture or a point cloud of the scene.
- One candidate grasp, such as a position, an angle and how deep the jaws go.

The output is a single number between 0 and 1. In other words, that number is the
model's guess at the chance that this grasp will hold the object when the arm lifts
it. A number used in this way is called a **probability**. So 0 means "certainly
not", 1 means "certainly", and 0.87 means "87 times out of 100".

Because the model is run once for each candidate, a sampler that proposes 200
grasps makes the model run 200 times. Those 200 runs can happen one after another,
or on all 200 together in one batch.

---

## 3. How it works inside

Since the last section described the scorer only from the outside, this section
opens it up. The best-known design is Dex-Net's **grasp quality convolutional
neural network (GQ-CNN)**, and it works in four steps.

1. **Cut out a patch.** Code cuts a small square out of the depth picture, centred
    on the candidate grasp's centre.
2. **Turn the patch.** Code turns the square so that the grasp's jaws sit at its
    left and right edges, which means every patch the network sees is lined up the
    same way. The network therefore never has to learn what a grasp at 30 degrees
    looks like as a separate case.
3. **Run the network.** A small convolutional neural network reads the turned
    patch, and it is given one further number as well, which is how deep the
    gripper would go. The
    [inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md#4-convolutional-layers-small-pattern-detectors)
    page explains how such a network reads a picture.
4. **Give one number.** The network ends with a single output, which is the chance
    that the grasp holds.

![One candidate cut out, turned, scored by a network, giving one number](../../../images/grasp-models/grasp-quality-models/crop-and-score.svg)

A candidate on the depth picture, and the patch cut out around it and turned so the
jaws sit left and right. Then a small network reads that patch and gives one number
out.

Step 2 is the clever part, because turning each patch removes the angle from the
problem altogether. The network then only has to learn one thing, which is whether
the shape lying between two jaws, lined up left and right, can be held.

Quality models for 6-DoF grasps work the same way, except that they start from a
point cloud rather than a depth picture. Code takes the points that lie between the
gripper's fingers, turns them into the gripper's own frame, and passes them to a
point cloud network. The
[point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md) page
explains those networks in detail.

### Where the candidates come from

Because a quality model is only as good as the candidates it is given, the sampler
matters as much as the scorer does. Three kinds of sampler are common, and any of
them can feed the same scorer.

- The simplest sampler picks at random and then checks the geometry, because code
    can pick pairs of points on the object's edge that face each other so that both
    jaws would press straight in. Book 3's
    [antipodal test](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test)
    explains this check.
- A better sampler refines the best candidates instead of stopping after one round,
    so code samples some candidates and scores them, and then samples new
    candidates near the best ones and scores those as well. After a few rounds the
    candidates gather around the best grasp, and this way of searching is called the
    **cross-entropy method**.
- The candidates can also come from another model, so that a
    [6-DoF grasp model](../02_most-used/01_six-dof-grasps.md) proposes the
    candidates and the quality model then re-scores them.

---

## 4. How it is trained

Because the network described above has to learn its scores, it needs examples.
Every example is a picture, a grasp and a label, where the label is 1 if the grasp
held and 0 if it did not. There are two ways to get those labels, and they cost
very different amounts.

![Labels calculated on 3D models, and labels from a real arm](../../../images/grasp-models/grasp-quality-models/labels-two-ways.svg)

On the left, physics formulas judge grasps on a 3D model, and the computer draws a
depth picture. On the right, a real arm tries each grasp, lifts it and checks what
happened. Both routes give the same kind of example, which is a picture, a grasp
and a 1 or a 0.

### Calculated on 3D models

This is how Dex-Net was trained, and it is the cheaper of the two routes because it
never touches a robot at all.

1. Collect thousands of 3D models of objects.
2. On each model, place many candidate grasps.
3. For each grasp, compute a **quality metric**, which is a number from physics
    formulas that says how much push or twist the grasp can resist before the
    object slips. Book 3's
    [grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute)
    explains these formulas.
4. Repeat the calculation many times with small random changes, such as the object
    moved a little, the gripper a little off and the friction a little lower, and
    then average the results. A grasp that still holds after all these small
    changes is called **robust**, so the label is 1 when the average is high enough.
5. Draw a depth picture of the object from a virtual camera, as a real camera would
    see it, with added noise.

This way is cheap and fast, because a computer can make examples far quicker than
an arm can try them. Dex-Net 2.0 was trained on 6.7 million examples made like
this, with no robot involved at any point.

### Tried on a real arm

Instead of that speed, the other route buys real results by letting real arms try
grasps for weeks.

1. The arm looks at a bin, picks a grasp, often at random at first, and tries it.
2. It lifts and checks whether anything is held, and a camera or the gripper's
    finger position tells it the answer.
3. The picture, the grasp and the result are saved.
4. The arm drops the object back in the bin and tries again, day and night.

Google's arm farm used this route, and between 6 and 14 arms made more than 800,000
grasp attempts to train one quality model. Its labels are real, so there is no gap
between simulation and reality, but collecting them is very slow and very
expensive.

---

## 5. Well-known models

Since both training routes above have produced working models, this section lists
the real ones you can read about.

- **Dex-Net 2.0 and its GQ-CNN** (2017), from the University of California,
    Berkeley, scores top-down grasps on depth pictures as described above, and it
    was trained on 6.7 million synthetic examples. Book 3's
    [planar models](../../../03_frameworks/02_gripping/04_models-that-grasp.md#2-planar-models-a-grasp-is-a-rectangle)
    section notes that its licence allows only education, research and
    not-for-profit use.
- **Pinto and Gupta's self-supervised grasping** (2016), from Carnegie Mellon
    University, let a real robot collect its own labels by trying grasps for
    hundreds of hours. **Self-supervised** means that the robot made its own
    labels, so no person had to mark anything.
- **Levine and others' hand-eye coordination network** (2016), from Google, is the
    arm farm above, and its network scored how likely a small movement of the
    gripper was to end in a good grasp. The arm then used those scores to steer
    itself towards the object.
- **QT-Opt** (2018), also from Google, learned a quality score for arm movements
    from more than 580,000 real grasp attempts, and it learned by trial and error,
    which the
    [reinforcement learning policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
    page covers.
- **GPD** and **PointNetGPD** both score 6-DoF candidates taken from a point cloud,
    where GPD uses a small CNN and PointNetGPD uses a point cloud network, and both
    of them sample their candidates with geometry first.

Most [6-DoF models](../02_most-used/01_six-dof-grasps.md#5-well-known-models) also
contain a scorer inside them, so the split described on this page is common even
where you cannot see it from outside. 6-DOF GraspNet and GraspGen, for example,
each have a separate network whose only job is to score the grasps the generator
made.

---

## 6. A worked example: a mug on a table

The sampler and the scorer are easier to follow once they run together. So in this
example a depth camera looks down on a mug, and the arm has a parallel-jaw gripper.

1. The camera takes one depth picture.
2. The sampler finds pairs of edge points on the mug that face each other, and from
    them it makes 100 candidate grasps.
3. For each candidate, code cuts out a patch, turns it, and passes it together with
    the gripper depth to the quality model, which gives back 100 scores.
4. The sampler then makes 100 new candidates near the 10 best, and the model scores
    those too, and this repeats three times.
5. Code drops any candidate the arm cannot reach, or that is wider than the gripper
    opens.
6. The arm tries the candidate with the highest score that is left, and on the mug
    in the picture above that is the grasp across the body, not the one on the
    handle or the rim.
7. If the grasp fails, the arm tries the next one down the list, and it does not
    need to run the model again unless the mug moved.

---

## 7. What goes wrong

That worked example ran smoothly, but five things go wrong once a quality model
meets objects it was not trained on.

- It inherits the formula's blind spots, because a model trained on calculated
    labels has only learned to copy a physics formula, so wherever that formula is
    wrong the model is wrong in exactly the same way. Book 3's
    [trap in the epsilon metric](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#92-the-trap-in-the-epsilon-metric)
    shows one such case.
- It can only pick from what it is shown, so if the sampler never proposes the best
    grasp then the model cannot choose it, which means a good scorer with a poor
    sampler still gives poor grasps.
- It is slow when there are many candidates, because each candidate needs its own
    run of the network, so a few hundred candidates is fine while a few hundred
    thousand is not.
- It can be sure and wrong, because a score of 0.95 is the model's guess rather
    than a promise, and on a shape unlike anything in its training it may give a
    high score to a grasp that fails. The
    [running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md#5-how-sure-the-model-is-and-why-it-can-be-sure-and-wrong)
    page explains why.
- It knows nothing about the task, because like every grasp model it scores only
    whether the object stays in the gripper and nothing else.

People reduce these problems in three ways, and most systems use all three. They
use a good sampler, and they mix a few real robot attempts into the calculated
training data. After that they add their own checks for reach, collisions and task
rules, once the model has given its scores.

---

## 8. Why this kind, and what it costs

Since you have now seen what goes wrong, it is worth saying plainly what you get in
return. A grasp quality model takes a picture and one candidate grasp, and gives
back the chance that the grasp holds.

What it does for you is choose well among many options, and it also lets you
control which options exist at all. This is because you write the sampler yourself,
rather than taking whatever another model offers. That means you can limit the
candidates to grasps that suit your arm, your gripper and your task before the
model ever sees them.

The obvious alternative is to skip the network and compute the quality metric
directly, using the formulas in Book 3's
[grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute).
Those formulas need a full 3D model of the object and its exact position. Instead,
a quality model needs only one noisy depth picture of an object it has never seen,
and that is the reason to choose it.

The other alternative is a model that generates good grasps directly, such as a
[top-down detector](01_top-down-grasp-detection.md) or a
[6-DoF model](../02_most-used/01_six-dof-grasps.md). Those are faster, because they
do not score candidates one by one. So a separate scorer earns its extra time only
when you want to control the candidates yourself, or when you want a second opinion
on another model's grasps.

What it costs you is time and training data, because scoring hundreds of candidates
takes longer than one pass of a generator. The training data itself needs either
thousands of 3D object models or weeks of real robot time.

---

## 9. The written alternative

This is where Book 3 offers a written scorer in place of a learned one. Its [grasp
quality
metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute)
compute, from physics formulas, how much push or twist a grasp can resist, while
its [antipodal
test](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test)
checks that the two contacts face each other. The sampler is written code in both
cases, and its better version, the [cross-entropy
method](../../../05_programming-techniques/06_planning-and-search/03_also-used/02_sampling-based-optimisation-and-mpc.md#the-cross-entropy-method-narrow-the-search),
is explained in Book 5. The formulas win when you have a full 3D model of the
object and know exactly where it is. The quality model wins instead when you have
only one noisy depth picture of an object it has never seen.

---

## 10. Where to read next

- [Six-degree-of-freedom grasps](../02_most-used/01_six-dof-grasps.md) covers the
    generators that most quality models are paired with today.
- [Reinforcement learning policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
    covers learning by trial and error, which QT-Opt used.
- [Force and slip models](../../09_touch-and-body-models/02_most-used/01_force-and-slip-models.md)
    covers checking, after the fingers close, whether the grasp is really holding.
- Book 3's [choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md)
    explains the physics formulas behind calculated labels.
- Book 3's [models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md)
    lists the code and licences for Dex-Net and GPD.

---

## 11. Using it in Python

This page has treated the scorer as a thing on its own: you bring the candidates, and
the model tells you how good each one is. That split is visible in the code of
Dex-Net's GQ-CNN, and this section shows it, so that after reading it you will know
exactly what a quality model is a function of, and what it never sees.

The code is in [gqcnn](https://github.com/BerkeleyAutomation/gqcnn), which you clone
rather than install from the Python package index. The class below is the scorer
alone, without the sampling and searching that the full Dex-Net policy wraps around
it.

```python
import numpy as np
from autolab_core import CameraIntrinsics, DepthImage, Point, YamlConfig
from gqcnn.grasping import GQCnnQualityFunction, Grasp2D

config = YamlConfig("cfg/examples/gqcnn_pj.yaml")           # names the weights folder
quality_fn = GQCnnQualityFunction(config["policy"]["metric"])

candidates = [
    Grasp2D(Point(np.array([u, v]), frame=camera_intr.frame),
            angle=angle,        # radians, anticlockwise from the picture's x axis
            depth=depth,        # metres from the camera to the grasp centre
            width=0.05,         # how far my gripper opens, in metres
            camera_intr=camera_intr)
    for (u, v, angle, depth) in my_own_candidates
]
scores = quality_fn(state, candidates)   # one float per candidate, between 0 and 1
```

The library gives you the trained network and the cropping that feeds it. That
cropping matters more than it looks: the GQ-CNN was trained on small square patches
of depth, each one rotated so that the grasp is horizontal and centred on the grasp
point, and `quality_fn` cuts and rotates those patches out of your picture for you.
If you fed the network a whole picture instead, the numbers would be meaningless. The
`state` it needs is the same `RgbdImageState` that the previous pages used, built from
a depth picture, the camera's intrinsic parameters and a mask of the objects. The
result is a plain list of floats in the same order as the candidates, which is what
makes this model easy to drop into a system you already have.

What you have to supply is the candidates themselves, and that is the honest reason
this page exists separately from the others. A scorer with no candidates does
nothing, so you either write a sampler, use `AntipodalDepthImageGraspSampler` from
the same repository, or take the output of a generator such as a 6-DoF model. You
also have to supply the `width` on every candidate, in metres, and that number is
your gripper's, not the model's.

The decisions are the cut-off and the search. Below what score do you refuse to try,
and how many candidates do you score before choosing? Scoring is not free, so the
full Dex-Net policy uses the cross-entropy method, which scores a batch, keeps the
best few, samples more candidates near them and repeats. That policy is
`CrossEntropyRobustGraspingPolicy` in the same module, and `policy(state)` returns a
`GraspAction` whose `q_value` is the winning score, so you can start with it and pull
the scorer out later if you want your own search.

The cost is the same as on the suction page, because it is the same repository:
TensorFlow 1.15 or below, no commits since January 2022, and a licence limited to
education, research and not-for-profit use. There is one cost specific to quality
models, which section 7 called inheriting the formula's blind spots. The score is
calibrated against the way the labels were made, which for Dex-Net 2.0 was a physics
simulation with assumed friction and an assumed gripper. So a score of 0.8 does not
mean that this grasp succeeds eight times in ten on your arm. It means that the
simulated gripper, with the simulated friction, succeeded that often. So you have to
measure the real success rate against the score yourself, on your own objects, before
the number is worth anything as a threshold.
