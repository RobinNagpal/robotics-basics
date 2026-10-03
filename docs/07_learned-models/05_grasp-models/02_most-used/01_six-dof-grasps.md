# Six-degree-of-freedom grasps

This page is about grasp models that can grasp from any direction, because a
[top-down detector](../03_also-used/01_top-down-grasp-detection.md) can only send
the gripper straight down. The models on this page can send it in from the side, at
a tilt, or under an edge instead. That is what a real bin of mixed objects needs,
and it is where most grasp research has gone since about 2019.

So the page answers these questions, one section at a time. What does "six degrees
of freedom" mean, and what does such a model take in and give back? How does it
work inside, and what is it trained on? Which real models do this, what goes wrong
with them, and what do they cost you?

It is for a reader who has read the [grasp models overview](../01_overview.md) and
[top-down grasp detection](../03_also-used/01_top-down-grasp-detection.md). Because
every model on this page starts from a point cloud, it also helps to have read
[point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md)
first.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: clearing a tote](#6-a-worked-example-clearing-a-tote)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

Since the introduction promised grasps from any direction, this section says what
"any direction" costs in numbers. A six-degree-of-freedom grasp model gives full
gripper poses in 3D, coming from any direction at all.

A **degree of freedom** is one number you can change independently, so to place a
gripper anywhere in a room, facing any way, you need six of them. Three numbers say
where it is, which is how far along, how far across and how high. Three more say
which way it faces, which is how far it is turned about each of three lines. Book
1's
[joints and degrees of freedom](../../../01_robotics-intro/05_arm-types/01_joints-and-degrees-of-freedom.md#6-degrees-of-freedom)
page explains this with pictures, and a set of all six numbers is called a
**pose**.

"Six-degree-of-freedom" is often written **6-DoF**, and a 6-DoF grasp is a gripper
pose plus an opening width. A top-down grasp fixes two of the six numbers, because
the gripper must point straight down, while a 6-DoF grasp leaves all six free.

For example, think of picking a mug off a table with your own hand. You can come
from above and pinch the rim, or from the side and wrap your fingers round the
body, or in at a tilt and hold the handle. Those are three different poses, and a
6-DoF grasp model can suggest any of them.

![Three grips on one mug, and the numbers each grip needs](../../../images/grasp-models/six-dof-grasps/many-directions.svg)

On the left are three grasps on one mug from three directions. The green gripper
comes from the side, and its two fingers close from the front and the back of the
mug, so only one finger shows. On the right is what the model must give for each
grasp, which is a position, an approach direction, a closing direction and an
opening width.

---

## 2. What goes in and what comes out

Because all six numbers are free, the model needs a fuller view of the scene than a
single picture from above. The input is therefore a **point cloud** of the scene,
which is a long list of 3D points, each one a spot on a surface that the depth
camera saw. A depth camera gives a depth picture, and a few lines of code turn each
pixel into a 3D point. Book 2's
[sensors](../../../02_perception/02_object-perception/02_sensors.md) page explains
depth cameras in more detail.

The camera sees only the sides of objects that face it, so the point cloud has no
points on the back or the bottom of anything. That means the model must guess good
grasps from this half view.

The output is a list of grasps, often hundreds of them. Each grasp has:

- a **position**: where the middle of the fingertips should be, as `x`, `y` and `z`
- an **approach direction**: the line the gripper travels along as it moves in
- a **closing direction**: the line along which the two fingers move together
- an **opening width**: how far apart the fingers should be before they close
- a **score**: a number between 0 and 1 for how likely the grasp is to hold

The approach direction and the closing direction together fix which way the gripper
faces, so together with the position they give all six numbers.

---

## 3. How it works inside

Since the answer is now defined, this section describes how a model produces it.
There are three main designs, and they appeared in the order given below.

### Sample, then check

The oldest design does not generate grasps with a network at all. Instead, ordinary
code picks thousands of random gripper poses near the point cloud. It then throws
away any pose where the gripper would pass through a point, or where the fingers
would not close on anything. A small network then looks at the points between the
fingers of each pose that is left, and says "good" or "bad". This design is easy to
follow, because each rejection has a reason you can read. It is slow, though, since
most random poses are bad.

### Generate directly

Instead of sampling at random, the second design trains a network to produce grasps
directly. One kind of network, called a **variational autoencoder**, learns to turn
random numbers into grasp poses that look like the good grasps it saw in training.
A second network then scores each grasp, and a third step moves each grasp a little
to raise its score.

### A grasp for every point

The third design is the one that most current models use. It works like the
per-pixel maps on the
[top-down page](../03_also-used/01_top-down-grasp-detection.md#3-how-it-works-inside),
except that it works on points instead of pixels.

1. The point cloud goes into a **point cloud network**, which is a network made to
    read an unordered list of 3D points. The
    [point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md)
    page explains how they work.
2. For every point, the network gives a score, an approach direction, a closing
    direction and a width.
3. The clever part is what each point stands for, because each point is treated as
    the spot where one finger would touch. In other words, the network says "if one
    finger touches here, the gripper should come in this way, close this way, and
    open this wide".
4. Code keeps the points with the best scores and turns each one into a full grasp
    pose.

![Each seen point proposes one grasp in which it is a finger contact](../../../images/grasp-models/six-dof-grasps/contact-points.svg)

On the left are the points the camera saw on a box and a tall can. On the right,
each point is coloured by its score, and the two circled points each propose a
grasp in which that point is where one finger touches.

Tying each grasp to a point that the camera actually saw makes the problem much
smaller. The network does not have to search all of space, since it only has to
answer one question about each point it was given.

Some newer models add one more step before this, because they first ask, for each
point, whether anything near there can be grasped at all. Points on a flat table or
deep in a gap get a low answer and are skipped, which saves time in cluttered
scenes.

---

## 4. How it is trained

None of those designs can work until the network has seen good grasps. So these
models learn from millions of grasps that were tested by a computer rather than by
a real robot, and the recipe is similar across models.

1. Collect thousands of 3D models of everyday objects, which are the kind of 3D
    files you could print on a 3D printer.
2. For each object, try a very large number of gripper poses in a physics
    simulator, or check them with physics formulas. Each pose gets a label, which
    is 1 if it would hold and 0 if it would slip or not close.
3. Place several objects together in a virtual bin to make a cluttered scene, and
    then throw away any grasp that would now hit a neighbouring object.
4. Make a point cloud of the scene from a virtual camera, as a real depth camera
    would see it.
5. Train the network to predict the good grasps from the point cloud.

Two datasets built this way are used more than any others.

- **ACRONYM** has millions of simulated grasps on thousands of object models, and
    it was made by NVIDIA and used to train Contact-GraspNet.
- **GraspNet-1Billion** was made at Shanghai Jiao Tong University, and it has about
    97,000 real camera pictures of 190 cluttered scenes built from 88 real objects.
    The grasps were computed on 3D models of those objects and then placed into
    each scene, which gives more than a billion labelled grasp poses.

The simulator's pictures are cleaner than a real camera's, because real depth
cameras miss thin edges and add noise. Training therefore adds noise and gaps to
the simulated point clouds on purpose, so that the model is not surprised by the
real thing. The
[where the data comes from](../../01_what-models-are/05_where-the-data-comes-from.md#4-simulation)
page explains this gap between simulation and the real world.

---

## 5. Well-known models

All three designs above appear in models you can download, and these are the real
ones. Book 3's
[models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md#4-six-degree-of-freedom-models)
lists their code, their licences and what hardware each one needs. Read it before
you choose one, because the licences in this area are unusually strict.

- **GPD**, Grasp Pose Detection, is the classic sample-then-check design, so it
    samples poses on the point cloud, checks them with geometry, and scores the
    survivors with a small network. It is the one model here that runs without a
    graphics card.
- **6-DOF GraspNet**, from NVIDIA, was an early model that generated grasps
    directly, using a variational autoencoder and a separate scoring network.
- **Contact-GraspNet**, also from NVIDIA, introduced the idea that each point
    proposes a grasp in which it is a finger contact, and most later models build
    on this.
- **AnyGrasp**, from the GraspNet-1Billion team, is one of the strongest models of
    this kind, and it can also follow grasps on an object that is moving. It is
    shipped as a closed library that needs a licence key tied to one computer.
- **GraspGen**, from NVIDIA in 2025, generates grasps with a diffusion model and
    then scores them. A **diffusion model** starts from random numbers and cleans
    them up, step by step, into a good answer, and the
    [diffusion and flow policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
    page explains the idea.

---

## 6. A worked example: clearing a tote

Those models are easier to judge once you see one running, so here is a full job. A
**tote** is a plastic box of the kind used in warehouses. This tote holds a mug, a
small box and a bottle lying on its side, and the arm must lift them out one by
one.

1. A depth camera above and to one side of the tote takes a picture, and code turns
    that picture into a point cloud.
2. Code crops the point cloud to the inside of the tote, so that the model does not
    waste time on the floor or the arm.
3. The model gives a few hundred grasps, each with a score.
4. Code checks each grasp against the things the model does not know about, and
    throws away the ones that fail.
5. The arm tries the best grasp that is left, lifts the object and puts it down
    outside the tote.
6. The camera takes a new picture, and the whole loop starts again, because the
    scene has changed and the old grasps are no longer valid.

Step 4 is the one people forget, so the picture below shows it on its own.

![The model proposes seven grips; checks keep three](../../../images/grasp-models/six-dof-grasps/propose-then-filter.svg)

On the left are seven grasps the model proposed for the tote. On the right are the
three that survive after code checks the tote walls, the gripper's opening and the
arm's reach.

---

## 7. What goes wrong

That filtering step matters because the model learned one thing only, which is
whether a grasp holds. It learned nothing else, so most failures come from what it
cannot know.

- The arm may not be able to reach the grasp, because the model knows nothing about
    your arm. A grasp that comes in from the far side of the tote may need a wrist
    angle the arm cannot make, so code must check each grasp with the arm's inverse
    kinematics, which is the maths that turns a gripper pose into joint angles.
    Book 3's
    [reaching and reachability](../../../03_frameworks/03_arm-movement/02_reaching-and-reachability.md)
    explains that check.
- The gripper may hit something on the way in, because the model checks for
    collisions only against the points it saw. It cannot see the back wall of the
    tote if the wall is hidden, so it may send the gripper straight through it.
- The model may have learned on a different gripper, since most models learned on
    one gripper such as a Franka Hand. A grasp that suits that gripper's finger
    length and opening may not suit yours.
- Shiny and see-through objects are missed, because glass and polished metal leave
    holes in the point cloud, and the model cannot grasp what it cannot see.
- The back of each object is hidden, so the model guesses what is behind each
    object from its training. When the guess is wrong, the far finger lands on
    empty air, and
    [shape completion](../../04_3d-models/03_also-used/01_shape-completion.md)
    models guess the hidden back, which can help.
- The model has no sense of the task, so it does not know that a mug of coffee must
    stay upright, or that a knife should not be held by the blade.

The fix for most of these is the same, which is to treat the model's grasps as
suggestions and put your own checks after it. Book 3's
[using a model as a candidate generator](../../../03_frameworks/02_gripping/04_models-that-grasp.md#9-using-a-model-as-a-candidate-generator)
gives the checks in order, and it also recommends logging which check rejected each
grasp. Then, when nothing is left, the log tells you whether the problem is the
model, the gripper or the cell.

---

## 8. Why this kind, and what it costs

Since the list above is long, it is worth saying what this kind buys in return. A
6-DoF grasp model takes a point cloud and gives full gripper poses from any
direction, each one with a score.

What it does for you is handle the clutter that a real bin holds. Objects in a real
bin lie at angles, lean on each other and press against walls. So many of them can
only be held from the side or at a tilt. A 6-DoF model finds those grasps on objects it has never seen.

The obvious alternative is a
[top-down detector](../03_also-used/01_top-down-grasp-detection.md), which is
smaller, faster and easier to run but only grasps straight down. So choose the
6-DoF kind when a real share of your objects cannot be picked from above. If every
object lies flat on a table, the top-down kind does the same job for less.

The other alternative is a rule you write by hand. Book 3's
[choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md) shows
that a rule is cheaper and easier to trust when you know the objects. So the 6-DoF
model is for the case where the next object could be anything.

What it costs you is large, and it comes in three parts.

- It needs strong hardware, because nearly every model of this kind needs an NVIDIA
    graphics card, and many depend on custom code that only builds for NVIDIA's
    CUDA system. Book 3's
    [what runs without CUDA](../../../03_frameworks/02_gripping/04_models-that-grasp.md#8-what-runs-without-cuda)
    gives the details for each model.
- Its licences are strict, since most of these models may only be used for
    research. Several have no licence file at all, which means you have no
    permission to use them, and
    [the licence picture](../../../03_frameworks/02_gripping/04_models-that-grasp.md#5-the-licence-picture)
    in Book 3 goes through them one by one.
- You must still write your own checks, because the model's grasps are not safe to
    use on their own. You still need reach checks, collision checks and task rules
    of your own.

---

## 9. The written alternative

Instead of a network, the written way to choose a grasp is in Book 3 rather than
Book 5. [Choosing a
grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md) finds pairs of
surface points that face each other, checks that the gripper has room to close, and
writes rules for known kinds of object. Book 5 prepares the shape those rules work
on. For example,
[clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
cuts each object out of the point cloud, and
[RANSAC](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md)
fits a plane or a cylinder to it to measure it. The written way wins when the
objects are known or have a shape you can describe. Instead, the model wins when
the next object could be anything, lying at any angle in clutter.

---

## 10. Where to read next

- [Grasp quality models](../03_also-used/02_grasp-quality-models.md) explains the
    scoring half of these models on its own.
- [Suction and affordance](02_suction-and-affordance.md) covers suction cups and
    models that know which part of an object to hold.
- [Point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md)
    explains the networks these models are built on.
- [Learned motion planners](../../06_movement-models/03_also-used/02_learned-motion-planners.md)
    covers what moves the arm to the grasp once it is chosen.
- Book 3's [models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md)
    has the full list of models, licences and hardware needs.

---

## 11. Using it in Python

Sections 1 to 4 explained what a 6-DoF grasp model takes in and how it is trained,
and section 5 named the real models. This section shows how one of them is actually
run, so that after reading it you will know what the download contains, what it
expects from you, and why the five lines of model code are the easy part.

There is no `pip install graspnet` that gives you a working 6-DoF grasp model.
Every model in section 5 is a research repository that you clone, and the code below
is the shape of the demo program in
[graspnet-baseline](https://github.com/graspnet/graspnet-baseline), the reference
model for the GraspNet-1Billion dataset. The imports `graspnet` and
`collision_detector` are files inside that repository, not installed packages, so
this code only runs from inside the clone.

```python
import torch
from graspnetAPI import GraspGroup
from graspnet import GraspNet, pred_decode              # files in the cloned repository
from collision_detector import ModelFreeCollisionDetector

net = GraspNet(input_feature_dim=0, num_view=300, num_angle=12, num_depth=4,
               cylinder_radius=0.05, hmin=-0.02, hmax_list=[0.01, 0.02, 0.03, 0.04],
               is_training=False)
net.load_state_dict(torch.load("checkpoint-rs.tar")["model_state_dict"])
net.eval().to("cuda")

with torch.no_grad():
    # points has shape (1, 20000, 3): one batch of 20,000 sampled points, in metres
    end_points = net({"point_clouds": points})
    gg = GraspGroup(pred_decode(end_points)[0].detach().cpu().numpy())

hits = ModelFreeCollisionDetector(cloud, voxel_size=0.01).detect(
    gg, approach_dist=0.05, collision_thresh=0.01)
gg = gg[~hits].nms().sort_by_score()
```

The repository gives you the network, the trained weights and the decoding step.
`pred_decode` is what turns the network's raw numbers into grasps you can read, and
without it the output means nothing. The collision detector is also included, and it
is worth understanding what it checks: it puts a box the shape of the gripper at
each grasp and counts how many points of the cloud fall inside it, so it catches a
gripper that would push through a neighbouring object. Two sets of weights are
published, `checkpoint-rs.tar` trained on RealSense pictures and
`checkpoint-kn.tar` trained on Kinect pictures, and the authors recommend the
RealSense one because it transfers better.

What you have to supply is everything before and after those lines. You need the
point cloud in `points`, which means a depth camera, its intrinsic parameters, and
the few lines that turn each depth pixel into a 3D point. You need to sample or pad
the cloud to exactly the number of points the network was built for, which is 20,000
here, and to mask out the floor and the walls of the bin first, or the model will
propose grasps on them. You need `cloud` for the collision check, as a plain array
of every point rather than the sampled subset. After the model answers, you still
have to move the grasps into the robot's base frame with your own calibration, check
that the arm can reach them, and write the approach, close and lift motion.

The environment is itself a cost you have to accept. The repository needs an NVIDIA
graphics card, because it compiles two CUDA extensions, `pointnet2` and `knn`,
before anything runs. AnyGrasp, the strongest model of this kind, is stricter again:
it ships as a compiled library that you call as
`detector.get_grasp(points, optional_params)` after
`from gsnet import create_detector`, and it will not start without a licence key
tied to the machine it runs on. Neither of these runs on an Apple Silicon Mac.

The decision that matters most is whether the gripper the model learned is close
enough to yours. These weights were trained on the two-finger gripper of the
GraspNet-1Billion dataset, so the `width` on every grasp is that gripper's opening,
in metres. If your gripper opens less far, you throw those grasps away and keep
fewer candidates; if your fingers are longer or thicker than the ones the collision
detector assumes, a grasp it passed may still collide. Nothing in the download knows
your gripper, and correcting for it is your work, not the model's.
