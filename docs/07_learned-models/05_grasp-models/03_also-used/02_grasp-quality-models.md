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
[Section 5.1](#51-dex-nets-gq-cnn-the-design-everything-else-argues-with) describes
GQ-CNN as a model and marks it historical, because it is the clearest way to see the
design and not the one to run today.

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
explains those networks in detail. There are two ways to finish that step, and
section 5 recommends one model of each. GPD draws those points as a small picture
first and scores the picture, which
[section 5.2](#52-gpd-the-scorer-you-are-allowed-to-sell) covers, while PointNetGPD
passes the points themselves to the network, which
[section 5.3](#53-pointnetgpd-scoring-the-raw-points-instead-of-a-picture-of-them)
covers.

One model in section 5 scores something else again. QT-Opt, in
[section 5.5](#55-qt-opt-what-real-robot-labels-cost), scores a small movement of the
arm rather than a finished grasp, so its number says how good it would be to move
the gripper a little in one direction. It is in the list for what its training data
cost rather than as a design to copy.

### Where the candidates come from

Because a quality model is only as good as the candidates it is given, the sampler
matters as much as the scorer does. Three kinds of sampler are common, and any of
them can feed the same scorer.

- The simplest sampler picks at random and then checks the geometry, because code
    can pick pairs of points on the object's edge that face each other so that both
    jaws would press straight in. Book 3's
    [antipodal test](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test)
    explains this check. GPD carries a sampler of this kind in the same program as
    its scorer, which is why section 5 recommends it to anybody who has no sampler
    of their own.
- A better sampler refines the best candidates instead of stopping after one round,
    so code samples some candidates and scores them, and then samples new
    candidates near the best ones and scores those as well. After a few rounds the
    candidates gather around the best grasp, and this way of searching is called the
    **cross-entropy method**.
- The candidates can also come from another model, so that a
    [6-DoF grasp model](../02_most-used/01_six-dof-grasps.md) proposes the
    candidates and the quality model then re-scores them. The newest scorers are
    trained in that arrangement from the start, beside the model that proposes the
    candidates rather than on their own, and GraspGen's discriminator in
    [section 5.4](#54-graspgens-discriminator-the-modern-scorer-inside-a-generator)
    is the example to take apart.

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

Both training routes above have produced working models, and this section names
them. It also answers the question a developer actually has about this family, which
is whether a grasp quality model is something you run or something you understand.
Two of these five are something you run on their own, one is something you run
inside a bigger model, and two are something you only read about.

Read the table one row at a time. The left column names the model, the year it was
published and how current it is, and the two rows marked historical are the two you
only read about. The right column holds everything else: what the model is given and
what it gives back, how big it is and what hardware it needs, the licence on its
code, and the one condition that should make you choose that row. What a model is
given comes first in that column, because it differs more here than in any other
family. Each licence is the licence on the code, and Book 3's
[models that grasp](../../../03_frameworks/02_gripping/04_models-that-grasp.md)
read every one of them from the project's own licence file in September 2026.

| Model | What decides it |
| --- | --- |
| [**GQ-CNN**](https://github.com/BerkeleyAutomation/gqcnn), from Dex-Net 2.0 (2017), historical | It scores one top-down grasp, from a 96 by 96 depth patch. It is four convolutional layers of 16 filters and two fully connected layers of 128, and it needs TensorFlow 1.15 or below. Its code licence is a University of California Regents grant for education, research and not-for-profit use only. Pick it when you are reproducing Dex-Net, or learning the design it started. |
| [**GPD**](https://github.com/atenpas/gpd) (2017), most used in 2026 | It scores one six-degree-of-freedom candidate, from the points between the jaws. It is a small network in C++, and it requires no graphics card. Its code licence is BSD-2-Clause. Pick it when you need a scorer you can sell, on a machine with no NVIDIA card. |
| [**PointNetGPD**](https://github.com/lianghongzhuo/PointNetGPD) (2019), worth betting on | It scores one candidate, from 500 raw points between the jaws. It is a small point cloud network in PyTorch. Its code licence is MIT. Pick it when your point cloud is sparse, or when you want to retrain the scorer yourself. |
| [**GraspGen**](https://github.com/NVlabs/GraspGen)'s discriminator (2025), worth betting on | It scores many six-degree-of-freedom grasps against one object's point cloud. Its size is `not stated`, and it needs an NVIDIA graphics card. The code is under the non-commercial NVIDIA License, and the weights are under the NVIDIA Open Model License. Pick it when you already run GraspGen and want it to rank candidates of your own. |
| **QT-Opt** (2018), historical | It scores a small movement of the arm, rather than a finished grasp. Its size is `not stated`, and no code or weights were published, so its licence is `not stated` as well. Never pick it, and read it instead to see what labels from real robots cost. |

### 5.1 Dex-Net's GQ-CNN, the design everything else argues with

**Historical.** It is the model this whole page is describing, and it is the one to
understand, but its code needs TensorFlow 1 and its licence forbids commercial use,
so it is not the one to run.

GQ-CNN is the grasp quality convolutional neural network, published in 2017 by Jeff
Mahler and others in the AUTOLAB group at the University of California, Berkeley, in
[Dex-Net 2.0](https://arxiv.org/abs/1703.09312). It is the four-step design in
section 3: cut a patch, turn it so the jaws are level, run a small network on that
patch together with the gripper's height, and give one number out. Its configuration
file shows how small that network is. It takes a 96 by 96 patch, and it has four
convolutional layers of 16 filters each, then two fully connected layers of 128.

The obvious alternative is to compute the quality metric from physics instead, with
the formulas in Book 3's
[grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute).
Choose GQ-CNN when you do not have a 3D model of the object and do not know exactly
where it is, which is the whole point of it. Dex-Net 2.0 used those formulas once, in
simulation, to make 6.7 million training examples, and the network then reproduces
their judgement from a single noisy depth picture of an object it has never seen.

What it costs you is the install and the licence. The code pins TensorFlow at 1.15
or below and names Python 3.5 to 3.7, so it needs an environment of its own, and the
project has had no commits since January 2022. The licence is a University of
California Regents grant for education, research and not-for-profit purposes only.
The thing that most often goes wrong is not the code at all, and section 7 named it:
the score is calibrated against the way the labels were made, which was a simulation
with an assumed friction and an assumed gripper, so a score of 0.8 does not mean
that this grasp succeeds eight times in ten on your arm.

The library is [gqcnn](https://github.com/BerkeleyAutomation/gqcnn), which you clone
rather than install. The class below is the scorer alone, without the sampling and
the searching that the full Dex-Net policy wraps around it.

```python
import numpy as np
from autolab_core import Point, YamlConfig
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

The library gives you the trained network and the cropping that feeds it, and the
cropping matters more than it looks. `quality_fn` cuts a patch out of your picture
around each candidate and turns it so the grasp is level, which is how the network
was trained; feed it a whole picture instead and the numbers mean nothing. What you
have to supply is the `state`, which is an `RgbdImageState` built from a depth
picture, the camera's intrinsic parameters and a mask of the objects, and the
candidates themselves with a `width` in metres on each, which is your gripper's
number and not the model's. If you have no sampler,
`AntipodalDepthImageGraspSampler` in the same repository is one, and
`CrossEntropyRobustGraspingPolicy` is the full search from section 3.

### 5.2 GPD, the scorer you are allowed to sell

**Most used in 2026** of the scorers that run on their own, because it is the only
one with a licence that permits commercial use and no NVIDIA graphics card in its
requirements.

GPD stands for grasp pose detection. Andreas ten Pas, Marcus Gualtieri, Kate Saenko
and Robert Platt published it in 2017, from Northeastern University, in a paper
called [Grasp Pose Detection in Point Clouds](https://arxiv.org/abs/1706.09911). It
is a sampler and a scorer in one C++ program: it samples candidate grasps on a point
cloud, keeps the ones that pass the geometric test in Book 3's
[antipodal test](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test),
turns the points between the jaws into a small picture, and scores that picture with
a small network.

The obvious alternative is Dex-Net's GQ-CNN. Choose GPD instead for two reasons
that have nothing to do with accuracy. Its licence is BSD-2-Clause, so you may put
it in a product, and its stated requirements are PCL, Eigen and OpenCV with no CUDA,
so it is the only model on this page with a plausible path to running on a machine
without an NVIDIA card. It also scores grasps from any direction rather than only
from above.

What it costs you is its age and its language. It was last pushed in January 2022,
so treat it as finished rather than maintained, and the obstacle is the dependencies
rather than the algorithm, because it asks for OpenCV 3.4 and PCL 1.9. It is C++, so
there is no Python API, only a [ROS wrapper](https://github.com/atenpas/gpd_ros).
The thing that most often goes wrong is the configuration file, because the gripper
geometry and the search volume both live in it, and a search volume left at the
example's value finds nothing in your scene.

The library is the compiled package itself. The quickest check that your install
works is its own example, which scores the grasps in one supplied point cloud file.

```bash
cd gpd/build
./detect_grasps ../cfg/eigen_params.cfg ../tutorials/krylon.pcd
```

Once that runs, the code below is the same work from your own program.

```cpp
#include <gpd/grasp_detector.h>

// The config file holds the gripper geometry, the search volume, the number of
// samples and the path to the weights. Your gripper goes in there, not here.
gpd::GraspDetector detector("cfg/eigen_params.cfg");

// view_points is a 3 by 1 matrix holding where the camera was.
gpd::util::Cloud cloud("scene.pcd", view_points);
detector.preprocessPointCloud(cloud);

// Samples candidates, scores every one, and returns the survivors.
auto hands = detector.detectGrasps(cloud);

for (const auto &hand : hands) {
  std::cout << hand->getScore()                      // the scorer's number
            << " " << hand->getPosition().transpose()
            << " " << hand->getApproach().transpose()
            << " " << hand->getGraspWidth() << std::endl;
}
```

The library gives you the sampler as well as the scorer, which is the difference
from every other row in the table. What you have to supply is a point cloud, the
camera position so that GPD knows which side of each surface was seen, and your
gripper's geometry in the configuration file. `filterGraspsDirection` throws away
every candidate whose approach is more than a given angle from a direction you
choose, which is how you make GPD answer the top-down question that the
[top-down page](01_top-down-grasp-detection.md) asks.

### 5.3 PointNetGPD, scoring the raw points instead of a picture of them

**Worth betting on**, because scoring the points between the fingers directly is
what the newest models do as well, and this is the smallest and most permissive
example of it.

PointNetGPD was published in 2019 by Hongzhuo Liang and others at the University of
Hamburg, in a paper called
[PointNetGPD: Detecting Grasp Configurations from Point Sets](https://arxiv.org/abs/1809.06267).
It keeps GPD's sampler and replaces GPD's scorer. Instead of turning the points
between the jaws into a small picture, it passes the points themselves to a point
cloud network, which the
[point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md) page
explains. The released model reads 500 points.

The obvious alternative is GPD, whose sampler it borrows. Choose PointNetGPD instead
when the points between the jaws are few, because drawing a sparse set of points as
a picture leaves most of that picture empty, and a point cloud network does not care
how many points there are. Its licence is MIT and it was last pushed in May 2025, so
of the two it is the one that still installs, with its own instructions setting up a
Python 3.10 environment.

What it costs you is the rest of the repository. The clone carries modified copies of
Berkeley's `meshpy` and `dex-net` packages, which you install from source, and the
instructions warn you not to have packages of those names already. The thing that
most often goes wrong is the frame, because the network wants the points expressed in
the gripper's own frame and nothing will tell you that you forgot to transform
them.

The library is the cloned repository, and the code below is the shortest path through
its own `main_test.py`.

```python
import numpy as np
import torch

# The released file holds the whole saved model, so nothing rebuilds the network.
model = torch.load("../data/pointnetgpd_3class.model", map_location="cpu")
model.eval()
torch.set_grad_enabled(False)

# local_pc holds the points that lie between the fingers for one candidate,
# already transformed into the gripper's own frame. Shape (500, 3), in metres.
x = torch.FloatTensor(local_pc.T[np.newaxis, ...])     # becomes (1, 3, 500)

out, _ = model(x)                 # log probabilities, one per class
scores = out.softmax(1)           # three classes: bad, fair and good
print(scores)
```

The library gives you the network and the code that trained it, on 350,000 point
clouds and grasps built from the YCB object set. What you have to supply is the
candidate sampling, the transform into the gripper's frame, and the cropping to the
points inside the jaws, all three of which GPD does for you. The released model gives
three classes rather than one probability, so you also have to turn three numbers
into one ordering, and taking the "good" class on its own is the usual choice.

### 5.4 GraspGen's discriminator, the modern scorer inside a generator

**Worth betting on**, because the field has stopped shipping standalone scorers and
started shipping a generator with its own scorer attached, and this is the clearest
example you can take apart.

GraspGen is NVIDIA's 2025 grasp generator, published in a paper called
[GraspGen](https://arxiv.org/abs/2507.13097). A diffusion model proposes
six-degree-of-freedom grasps and a second network, which the project calls the
**discriminator**, scores and ranks them. A discriminator here is exactly the grasp
quality model this page describes, trained alongside the generator rather than on
its own. The project names as its own contribution a training recipe in which the
discriminator learns on the generator's output rather than on a fixed set of
candidates.

The obvious alternative is to keep the scorer separate, as GQ-CNN and GPD do. That
training recipe is the reason to prefer this shape. A separate scorer learns on
candidates from a sampler and is then asked, at run time, about candidates from a
generator, which are different candidates, so some of its confidence is misplaced.
The scorer here sees in training the mistakes it will be asked about later. You can
still use it on its own, because the function that runs the discriminator alone is a
public part of the code.

What it costs you is hardware and licence. Book 3's
[what runs without CUDA](../../../03_frameworks/02_gripping/04_models-that-grasp.md#8-what-runs-without-cuda)
section records that it depends on `spconv-cu120`, for which no processor-only build
exists, so it needs an NVIDIA card and will not run on an Apple Silicon Mac. The
licence splits four ways: the [GraspGen](https://github.com/NVlabs/GraspGen) code is
under NVIDIA's own non-commercial licence, the successor repository
[GraspGenX](https://github.com/NVlabs/GraspGenX) is Apache-2.0, the weights are
under the NVIDIA Open Model License and the training dataset is CC BY 4.0. That
Apache licence does not make a deployment permissive, because the weights you would
run carry their own terms.

The library is `grasp_gen`, inside the cloned repository and its Docker image. The
whole pipeline is one call, and so is the scorer on its own.

```python
from grasp_gen.grasp_server import (GraspGenSampler, load_grasp_cfg,
                                    score_grasps_with_discriminator)

cfg = load_grasp_cfg("/models/checkpoints/graspgen_robotiq_2f_140.yml")
sampler = GraspGenSampler(cfg)          # loads the generator and the discriminator

# object_pc is (N, 3) points on one object, in metres. Generate and rank in one call.
grasps, conf = GraspGenSampler.run_inference(object_pc, sampler,
                                             grasp_threshold=0.8, num_grasps=200)

# Or score candidates of your own. Both inputs must be moved so that the point
# cloud's own mean sits at the origin, because that is how the model was trained.
centre = object_pc.mean(dim=0)
my_grasps[:, :3, 3] -= centre           # my_grasps is (M, 4, 4) gripper poses
scores = score_grasps_with_discriminator(sampler.model,
                                         object_pc - centre, my_grasps)
```

The library gives you a working scorer for two named grippers, a Franka Hand and a
Robotiq two-finger, and a suction model. What you have to supply is a point cloud of
one object rather than of the whole scene, so you need a segmentation model first,
and the centring shown above, which the one-call path does for you and the
discriminator path does not. If your gripper is neither of the two, the project's own
advice is to reuse the nearer model and shift the grasp along the approach direction,
which is a guess rather than a calibration. The threshold is yours:
`grasp_threshold=0.8` keeps only grasps the discriminator is sure about, and `-1.0`
returns the best 100 whatever their scores.

### 5.5 QT-Opt, what real robot labels cost

**Historical.** No code or weights were published, so this is a result to know
rather than a model to use, and the result is about the price of training data.

QT-Opt was published in 2018 by Dmitry Kalashnikov and others at Google, in a paper
called [QT-Opt](https://arxiv.org/abs/1806.10293). It scored a small movement of the
arm rather than a finished grasp, so the robot asks how good it would be to move the
gripper a centimetre in some direction, and then makes the best movement, over and
over. It learned by trial and error, which the
[reinforcement learning policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
page covers, from more than 580,000 real grasp attempts.

The obvious alternative is Dex-Net's route, which bought its labels from a physics
simulation. QT-Opt measures what the other route costs: it removes the gap between
simulation and reality completely, and the bill is more than half a million attempts
and months of robot time. That is the number to quote when somebody proposes
collecting their own grasp data instead. Nothing was released, so there is no code.

### 5.6 How to choose

If you want a grasp quality model running this week, use GPD. It brings its own
sampler, its BSD-2-Clause licence lets you sell what you build, and it is the only
one here that does not ask for an NVIDIA graphics card. Budget your time for its
2022-era C++ dependencies rather than for the model.

Three things change that choice.

- If you already run a six-degree-of-freedom generator, do not add a separate
    scorer. Use the one inside it, which for GraspGen means
    `score_grasps_with_discriminator` on your own candidates. A scorer trained
    beside the generator matches the generator's mistakes better than any scorer
    added afterwards.
- If your points between the jaws are few, because the object is thin or the camera
    sees it edge on, use PointNetGPD. It reads the points as points rather than
    drawing them as a picture, and it is MIT and still installs.
- If you have a full 3D model of the object and know where it is, do not use a
    learned scorer at all. Compute the quality metric from the physics formulas in
    Book 3's
    [grasp quality metrics](../../../03_frameworks/02_gripping/03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute),
    which is exact and needs no training data. Section 9 below sets out that
    comparison in full.

Whichever you pick, the sampler decides more than the scorer does, and section 7
said why: a good scorer cannot choose a grasp nobody proposed. Spend your effort on
the candidates before you spend it comparing scorers.

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
method](../../../06_programming-techniques/06_planning-and-search/03_also-used/02_sampling-based-optimisation-and-mpc.md#the-cross-entropy-method-narrow-the-search),
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

