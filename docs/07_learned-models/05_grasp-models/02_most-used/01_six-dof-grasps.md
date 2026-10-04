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

Sections 1 to 4 explained the kind of model. This section names the ones you can
download today, says what each one assumes about your gripper, and shows the
shortest real code for each.

Every licence below was read from the project's own licence file, and Book 3's
[models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md#4-six-degree-of-freedom-models)
explains each one in more detail. Read the table as one row per model, in the
order the sub-sections cover them. The "how big it is" column gives the
download size of the weights and the graphics memory the project's own
instructions ask for, because none of these projects publishes a parameter count.
`not stated` means the project does not say and the file is not published where
its size can be read.

| Model | How current | Best at | How big it is | Licence of the code | Pick it when |
| --- | --- | --- | --- | --- | --- |
| GPD | historical | grasps you can explain, on any processor | weights 14.5 megabytes, in the repository; no graphics card needed | BSD-2-Clause | you have no NVIDIA card, or you must sell the product |
| Contact-GraspNet | most used in 2026 | a first working 6-DoF model on a cluttered scene | weights 27 megabytes; 8 gigabytes of graphics memory to run, 24 to train | a PDF file; no machine-readable licence | you want the design the rest of the field assumes |
| graspnet-baseline | most used in 2026 | comparing your work against the standard benchmark | not stated | Shanghai Jiao Tong University, non-commercial research only | you are measuring against GraspNet-1Billion |
| AnyGrasp | most used in 2026 | the best grasps, including on moving objects | not stated | no licence file; a machine-locked key | accuracy matters more than freedom to ship |
| EconomicGrasp | worth betting on | training your own model cheaply | weights 189 megabytes each; 5.81 gigabytes of graphics memory to train | MIT | you must train on your own data and own the result |
| GraspGen and GraspGenX | worth betting on | a gripper that is not a Franka or a Robotiq | GraspGenX weights 1.7 gigabytes; 20 grasp predictions per second | GraspGen non-commercial; GraspGenX Apache-2.0 | your gripper is unusual, or you want a clean licence |

One warning before the sub-sections. A grasp pose only means something for the
gripper it was predicted for, so a model trained on a gripper that opens 80
millimetres will propose grasps a gripper that opens 38 millimetres cannot make.
Each sub-section below therefore names the gripper its model assumes.

### 5.1 GPD, the one you can read and the one you can sell

**[GPD](https://github.com/atenpas/gpd), or Grasp Pose Detection, is
historical**, because it was last changed in January 2022 and has had none of the
research since. It comes from Andreas ten Pas and Robert Platt at Northeastern
University, and it is the sample-then-check
design from [section 3](#3-how-it-works-inside): C++ code draws candidate gripper
poses on the point cloud, geometry throws away the ones that would not close on
anything, and a small network scores what is left.

You would pick it rather than Contact-GraspNet for two reasons, and neither is
accuracy. The first is that GPD is BSD-2-Clause, which lets you put it in
something you sell, while almost every model below allows research use only. The
second is that GPD asks you for your gripper's measurements instead of assuming
somebody else's. Its `cfg/hand_geometry.cfg` file holds `finger_width`,
`hand_outer_diameter`, `hand_depth` and `hand_height` in metres, and you edit
them. No other model on this page lets you do that.

What it costs you is accuracy, and the gap on cluttered scenes is large rather
than small. It also costs you a day of dependency work, because it is C++ against
Point Cloud Library 1.9, Eigen 3 and OpenCV 3.4, and OpenCV 3.4 is from 2018. The
thing that most often goes wrong is the `camera_position` line in the
configuration file, because GPD uses it to decide which way each surface faces. If
it is wrong, every surface faces inwards and the grasps are nonsense.

GPD is not a Python library. You build it with CMake and run the program it
produces, which is how its own README demonstrates it:

```bash
# Run GPD on one saved point cloud file. The first argument is the
# configuration, which points at the gripper file; the second is the cloud.
./detect_grasps ../cfg/eigen_params.cfg ../tutorials/krylon.pcd
```

The program prints the grasps it found and opens a viewer window. What you supply
is the point cloud as a `.pcd` or `.ply` file, your gripper's measurements, and
the camera's position in the cloud's own frame.
[PointNetGPD](https://github.com/lianghongzhuo/PointNetGPD) is an MIT-licensed
successor that replaces the small network with a point cloud network.

### 5.2 Contact-GraspNet, the design everything else copies

**Contact-GraspNet is the most used of these models in 2026**, because it is the
one every later paper compares itself against and the one most robot code expects
to find. Martin Sundermeyer and others published it from NVIDIA in 2021, in the
[Contact-GraspNet paper](https://arxiv.org/abs/2103.14127), and its idea is the
one [section 3](#3-how-it-works-inside) describes: each point the camera saw is
treated as a place where one finger could touch, and the network says how the
gripper should come in if it touches there.

The obvious alternative is the model it replaced,
[6-DOF GraspNet](https://arxiv.org/abs/1905.10520), from the same group two years
earlier. That one generated grasps with a variational autoencoder and then pushed
each grasp around to raise its score, which meant searching all of space. You
pick Contact-GraspNet instead because tying every grasp to a point that was
actually seen removes that search, so one pass of the network gives the whole
answer.

What it costs you is an NVIDIA card. The original
[NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet) is
TensorFlow and pins CUDA 10.1, and the maintained
[PyTorch version](https://github.com/elchun/contact_graspnet_pytorch) asks for 8
gigabytes of graphics memory to run and 24 to train. The licence costs you more
than the hardware does. Both repositories carry a file called `License.pdf`, so
there is no machine-readable licence at all and every dependency scanner reports
the project as unlicensed. You have to open the PDF and read it before you build
anything on it. The thing that most often goes wrong is handing it a whole scene
with no segmentation, because the grasps then land on the table and the bin
walls.

The PyTorch version installs as a package, and its weights are already inside the
repository rather than downloaded separately.

```python
from contact_graspnet_pytorch import config_utils
from contact_graspnet_pytorch.checkpoints import CheckpointIO
from contact_graspnet_pytorch.contact_grasp_estimator import GraspEstimator

ckpt_dir = "checkpoints/contact_graspnet"
estimator = GraspEstimator(config_utils.load_config(ckpt_dir))
CheckpointIO(checkpoint_dir=f"{ckpt_dir}/checkpoints",
             model=estimator.model).load("model.pt")

# depth is in metres, cam_K is the 3 by 3 camera matrix, and segmap gives each
# pixel an object number. z_range drops points nearer than 0.2 m or past 1.8 m.
pc_full, pc_segments, _ = estimator.extract_point_clouds(
    depth, cam_K, segmap=segmap, z_range=[0.2, 1.8])

grasps, scores, contacts, _ = estimator.predict_scene_grasps(
    pc_full, pc_segments=pc_segments,
    local_regions=True,    # look at each object's own region, not the whole scene
    filter_grasps=True)    # drop grasps whose contact is on another object
```

The library turns your depth picture into point clouds, runs the network and
gives you `grasps`, a dictionary from object number to an array of four-by-four
pose matrices in the camera's frame. What you supply is the depth picture in
metres, the camera matrix, and the segmentation that says which pixel belongs to
which object. Those poses are in the camera's frame, so moving them into the
robot's frame with your own calibration is still your work.

### 5.3 graspnet-baseline, the reference for the standard benchmark

**[graspnet-baseline](https://github.com/graspnet/graspnet-baseline) is the most
used of these models in 2026 for measurement rather than for shipping.** It comes
from Hao-Shu Fang and others at Shanghai
Jiao Tong University and is the reference implementation for the
[GraspNet-1Billion](https://graspnet.net/) dataset that
[section 4](#4-how-it-is-trained) described. Almost every published score for a
6-DoF grasp model is a score on that benchmark, produced by code descended from
this repository.

You would pick it rather than Contact-GraspNet when you need a number you can
compare with the literature. Contact-GraspNet was trained on NVIDIA's simulated
ACRONYM grasps and reports no GraspNet-1Billion score, so a measurement against
it says nothing about how your change compares with everybody else's. If you are
not measuring, pick something else, because this repository is older than the work
built on it.

What it costs you is the licence and the install. The licence is a Shanghai Jiao
Tong University agreement for academic and non-profit research only, so you cannot
sell anything built on it. The install is worse than it looks: the
`requirements.txt` file is ordinary, and then the README tells you to compile a
`pointnet2` extension and a CUDA `knn` operator by hand, which no dependency
scanner will warn you about. Of the two published sets of weights the authors
recommend `checkpoint-rs.tar`, trained on Intel RealSense pictures, over
`checkpoint-kn.tar`, trained on Microsoft Kinect pictures, because it transfers
better.

The imports below are files inside the clone rather than installed packages, so
this runs only from inside the repository. `graspnetAPI` is a real package and
holds the grasp data type.

```python
import torch
from graspnetAPI import GraspGroup
from graspnet import GraspNet, pred_decode              # files in the clone
from collision_detector import ModelFreeCollisionDetector

net = GraspNet(input_feature_dim=0, num_view=300, num_angle=12, num_depth=4,
               cylinder_radius=0.05, hmin=-0.02,
               hmax_list=[0.01, 0.02, 0.03, 0.04], is_training=False)
net.load_state_dict(torch.load("checkpoint-rs.tar")["model_state_dict"])
net.eval().to("cuda")

with torch.no_grad():
    # points has shape (1, 20000, 3): one batch of 20,000 points, in metres
    gg = GraspGroup(pred_decode(net({"point_clouds": points}))[0]
                    .detach().cpu().numpy())

# Put a box the shape of the gripper at each grasp and count the cloud points
# inside it, which catches a gripper that would push through a neighbour.
hits = ModelFreeCollisionDetector(cloud, voxel_size=0.01).detect(
    gg, approach_dist=0.05, collision_thresh=0.01)
gg = gg[~hits].nms().sort_by_score()
```

`pred_decode` is the step that turns the network's raw numbers into grasps you
can read, and the answer means nothing without it. What you supply is `points`,
sampled or padded to exactly 20,000 points with the floor and the bin walls
masked out first, and `cloud`, every point rather than the sample, for the
collision check. The `width` on every grasp is the opening of the two-finger
gripper used to build GraspNet-1Billion, so a narrower gripper of your own means
throwing those grasps away yourself.

### 5.4 AnyGrasp, the strongest and the least free

**[AnyGrasp](https://github.com/graspnet/anygrasp_sdk) is the most used of these
models in 2026 wherever accuracy decides the job.** It comes from the same
Shanghai Jiao Tong University group and was built on GraspNet-1Billion, it was
still being updated in July 2026, and it is the only model on this page that can
follow a grasp on an object that is moving rather than starting again from a new
picture.

You would pick it rather than graspnet-baseline because it is better at the same
task and because it ships as a working detector rather than as training code you
have to finish. You would not pick it if anything in your project needs certainty,
and that is the whole trade. It is a compiled library with **no licence file at
all**, which means default copyright and no permission to use it, and it will not
start without a licence key that you apply for through a form and that is tied to
one machine. The thing that most often goes wrong is that key, because the machine
it was issued for changes and the detector then stops starting.

The library is called `gsnet`, and this is the shape of its own demo program:

```python
import numpy as np
from gsnet import create_detector

# cfgs carries checkpoint_path, gripper_height and max_gripper_width.
# AnyGrasp clamps max_gripper_width to 0.1 m, because that is the widest
# gripper its weights were trained on.
detector = create_detector(cfgs)

gg = detector.get_grasp(points, {              # points: (N, 3) float32, in metres
    "collision_detection": True,
    "dense_grasp": False,
    "region_steering": object_mask,            # only grasp this object
    "approach_steering": [0, 0, 1],            # prefer this approach direction
    "approach_thresh": np.pi / 6,              # allow 30 degrees either side of it
})
gg = gg.nms().sort_by_score()
```

The detector gives you a `GraspGroup` from `graspnetAPI`, already collision
checked against the cloud. The two steering arguments are the part worth knowing,
because they push the model towards the grasps your cell can reach instead of
making you filter its answers afterwards. What you supply is the point cloud in
metres, a mask for the object you want, and the licence key. Note the clamp in the
comment: ask for a gripper wider than 0.1 metres and AnyGrasp quietly reduces it,
because no wider gripper was in its training.

### 5.5 EconomicGrasp, the one you can train yourself

**[EconomicGrasp](https://github.com/iSEE-Laboratory/EconomicGrasp) is worth
betting on**, because it is the only model in the GraspNet-1Billion family with a
real open-source licence and it is the cheapest
to train by a wide margin. Xiao-Ming Wu and others at Sun Yat-sen University
published it at the European Conference on Computer Vision in 2024, and the
repository was last changed in April 2026.

You would pick it rather than graspnet-baseline for two reasons. It is MIT
licensed, so a model you train with it is yours. And its own README reports
training in 8.3 hours using 4.2 gigabytes of main memory and 5.81 gigabytes of
graphics memory on one RTX 3090 card, which is a machine you can rent by the hour,
while training the older models in this family is a much larger job. The README
also reports 68.21, 61.19 and 25.48 average precision on the seen, similar and
novel object splits of GraspNet-1Billion with RealSense pictures, and 62.59, 51.73
and 19.54 with Kinect pictures. Those are the authors' own numbers on their own
benchmark, so read them as a claim rather than as an independent measurement.

What it costs you is the install, and the blocker is specific. It imports
[MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine), NVIDIA's sparse
convolution library, which was last changed in March 2024 and compiles with
`nvcc`. It also compiles `pointnet2` and a `knn` operator, and wants CUDA 12. The
thing that most often goes wrong is the preparation before any training starts,
because you must download GraspNet-1Billion and then run two label generation
passes over it.

There is no packaged inference call. You run its own scripts, and this is the test
command from its README.

```bash
# --test_mode picks the split: seen, similar or novel objects.
# --inference runs the model; without it the script only scores saved results.
python test.py --model economicgrasp --camera kinect \
  --checkpoint_path results/economicgrasp/economicgrasp_epoch10.tar \
  --dataset_root /path/to/graspnet --save_dir results/test_seen \
  --test_mode seen --inference
```

The repository publishes trained weights for both cameras as release files, so
you can test without training first. What you supply is the dataset, the compiled
extensions, and your own program if you want to run the model on a live camera,
because these scripts read the benchmark's files from disk.

### 5.6 GraspGen and GraspGenX, the models that ask which gripper you have

**GraspGen and GraspGenX are worth betting on**, because they are the first
models here to treat the gripper as an input rather than as a fact fixed in the
weights, which is the problem every sub-section above ran into.
[GraspGen](https://github.com/NVlabs/GraspGen) is NVIDIA's 2025 generator,
published in the [GraspGen paper](https://arxiv.org/abs/2507.13097): a diffusion
model proposes grasps and a second network scores them. A **diffusion model**
starts from random numbers and cleans them up step by step into a good answer, and
the
[diffusion and flow policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
page explains the idea.
[GraspGenX](https://github.com/NVlabs/GraspGenX), released on 1 June 2026, is the
same group's follow-up.

You would pick GraspGenX rather than Contact-GraspNet or AnyGrasp because of what
it does about grippers. GraspGen trains one model per gripper and publishes three:
a Franka Panda, a Robotiq 2F-140 and a single suction cup of 30 millimetre radius.
GraspGenX instead trains one model that is given a description of the gripper,
worked out from the volume the gripper sweeps as it closes, and its README reports
training on over 2 billion grasps across 32 generated grippers in 6 kinematic
families and more than 8,000 objects. Its checkpoints name grippers including
`franka_panda`, `robotiq_2f_85`, `robotiq_2f_140`, `unitree_g1`, `inspire_hand`,
`barrett_hand` and `ezgripper`, and `scripts/gripper_config_wizard.py` adds one
that is not on the list. No other model on this page offers that.

The licences are split, and the split runs the opposite way to the usual one.
GraspGen's code is under NVIDIA's own licence, whose section 3.3 limits use to
research or evaluation and then permits NVIDIA itself to use the work
commercially. GraspGenX's code is plain Apache-2.0, with no use limit added. The
published weights of both are under the NVIDIA Open Model License rather than
Apache-2.0, so the Apache badge does not make what you deploy Apache. Besides
that, GraspGen needs `spconv-cu120`, for which no processor-only build exists, and
its README reports 20 grasp predictions per second before any further speed work.
The thing that most often goes wrong is forgetting that both models expect one
object's points rather than a whole scene, so you segment first.

GraspGenX installs as a package, and it fetches its own weights and gripper
descriptions from Hugging Face the first time you import it. That download is
about 1.2 gigabytes for the diffusion model and 484 megabytes for the scorer.

```python
from graspgenx import get_checkpoints_version_dir
from graspgenx.grasp_server import GraspGenXSampler
from graspgenx.samplers import run_planner_on_object
from graspgenx.utils.checkpoint_io import load_model_cfg

ckpt = get_checkpoints_version_dir()      # downloaded on first import
cfg = load_model_cfg(f"{ckpt}/gen", f"{ckpt}/dis")   # generator, then scorer
sampler = GraspGenXSampler(cfg, "robotiq_2f_85", assets_dir="assets")

# obj_pc is one object's points as (N, 3), with its own mean subtracted.
grasps, scores, _, _ = run_planner_on_object(
    obj_pc, sampler, num_grasps=200, topk_num_grasps=100)
# grasps is (K, 4, 4); scores is (K,), the scorer's confidence from 0 to 1
```

The library gives you the download, the gripper description, the diffusion
sampler and the scorer. What you supply is the gripper name and one object's point
cloud with its mean subtracted, which means you segment the scene yourself. For a
gripper that is not on the published list, the configuration wizard asks you for
its measurements and its URDF file, which is the format that describes a robot's
links and joints.

### 5.7 How to choose

Start with GraspGenX. It installs with one command, its code licence is plain
Apache-2.0, and it is the only model here that was trained for more than one
gripper, so it is the only one whose scores still mean something for a gripper
that is not a Franka or a Robotiq.

Four things change that answer.

If you have no NVIDIA graphics card, your only real option here is GPD, and the
comparison that matters is then GPD against the written rules in Book 3's
[choosing a grip](../../../03_frameworks/02_gripping/03_choosing-a-grip.md)
rather than GPD against these models.

If you are going to sell the product, your shortlist is GPD under BSD-2-Clause and
EconomicGrasp under MIT, and even then you check the weights' licence separately
from the code's. Everything else here needs a negotiation, in two cases with a
university.

If accuracy on a hard bin decides whether the project works at all, and research
terms are acceptable, use AnyGrasp and accept the machine-locked key.

If you are writing a paper, use graspnet-baseline or EconomicGrasp, because a
score on GraspNet-1Billion is the only score other people can compare with
theirs.

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
[clustering](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
cuts each object out of the point cloud, and
[RANSAC](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md)
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
