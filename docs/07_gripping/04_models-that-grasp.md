# Models that grasp: the ones you download

Models that take a picture or a point cloud and return gripper poses. This is the
other half of [choosing a grip](03_choosing-a-grip.md): reach for these when the
objects share no structure you can write down, which in practice means a mixed
tote of things nobody has listed.

The [perception area introduces this family
briefly](../06_object-perception/04_models-that-find.md#2-models-that-choose-where-to-grip)
as a fifth kind of answer a vision system can give. Everything here is
consistent with that and goes considerably further: what each family actually
predicts, which ones have survived to 2026, which will run without an NVIDIA
graphics card, and the licence position, which in this corner of robotics is the
worst in the whole field.

Every licence below was read from the project's own licence file in September
2026 using the GitHub licence API or by listing the repository root, never from a
badge or a blog post. That distinction matters more here than anywhere else in
these documents, and [section 5](#5-the-licence-picture) explains why with
twelve specific cases.

## Who this is for

Someone who has decided a rule will not do, and now has to pick a grasp model and
ship something. If you have not read [choosing a grip](03_choosing-a-grip.md),
read at least [its section 10](03_choosing-a-grip.md#10-why-a-rule-beats-a-network)
first, because the most common mistake in this area is reaching for a model
before the cheaper option has genuinely run out.

## Contents

1. [What a grasp model actually predicts](#1-what-a-grasp-model-actually-predicts)
2. [Planar models: a grasp is a rectangle](#2-planar-models-a-grasp-is-a-rectangle)
3. [Sampling and scoring: the geometric ancestors](#3-sampling-and-scoring-the-geometric-ancestors)
4. [Six-degree-of-freedom models](#4-six-degree-of-freedom-models)
5. [The licence picture](#5-the-licence-picture)
6. [Suction models](#6-suction-models)
7. [Dexterous hands, and grasping language models](#7-dexterous-hands-and-grasping-language-models)
8. [What runs without CUDA](#8-what-runs-without-cuda)
9. [Using a model as a candidate generator](#9-using-a-model-as-a-candidate-generator)

---

## 1. What a grasp model actually predicts

Every model in this document was trained on the same label: **the object did not
fall out**. Attempts were made, in simulation or on real hardware, and each one
was recorded as a success or a failure according to whether the object was still
held at the end. That is the entire supervision signal.

Two things follow, and both are easy to forget once the model is producing
convincing pictures.

**The model is an expert on slipping and knows nothing else.** It has no
representation of which part of the object must not be touched, whether the grasp
permits the next operation, how much force the object can take, or whether your
particular arm can reach the pose. These are not weaknesses to be fixed with more
data; there is nothing in the loss function that could learn them.

**Success in the dataset is not success in your cell.** The benchmarks report
grasp success on a specific gripper — usually a Franka Hand or a Robotiq 2F-85 —
with a specific stroke, specific fingertips and a specific approach. A grasp pose
that is excellent for an 80 mm parallel jaw is meaningless for a 38 mm one, and
the model has no idea which you have. Most of them take a gripper width as a
parameter and were trained at one value.

### 1.1 Two ways to represent a grasp

The literature splits cleanly in two, and the split decides what the model can
express.

**A planar, or four-degree-of-freedom, grasp** is a rectangle on a depth image:
a position in the image, an angle in the image plane, a width, and an approach
straight down the camera axis. This is the older representation. It is cheap, it
is easy to learn, and it can only ever produce top-down grasps.

**A six-degree-of-freedom grasp** is a full pose in space: position and
orientation, with the approach direction free. This can express a grasp coming in
from the side, at an angle, or under an overhang. It is what a real bin needs and
it is much harder to learn.

Almost every model before about 2019 is planar and almost every model since is
six-degree-of-freedom. If a model is described as producing "grasp rectangles",
it is the first kind, and for a bin of objects lying at angles that is a real
restriction rather than a detail.

## 2. Planar models: a grasp is a rectangle

These take a depth image and return grasp rectangles. They are small, fast, old,
and — the reason they are still worth knowing — the only family in this document
that plausibly runs on a laptop.

| Model | What it is | Licence, read from the file | State in September 2026 |
| --- | --- | --- | --- |
| [Dex-Net / GQ-CNN](https://github.com/BerkeleyAutomation/gqcnn) | the original: a network scoring sampled top-down grasps, trained on analytically computed quality | **UC Regents custom — "educational, research, and not-for-profit purposes" only**, with a named contact for commercial licensing | Python 3.7 era; TensorFlow 1 |
| [GG-CNN](https://github.com/dougsm/ggcnn) | predicts grasp quality, angle and width at every pixel in one small convolutional pass | BSD-3-Clause | last pushed July 2020 |
| [GR-ConvNet](https://github.com/skumra/robotic-grasping) | a larger generative residual network in the same style | BSD-3-Clause | last pushed November 2021 |

Dex-Net is the historically important one. [Dex-Net
2.0](https://arxiv.org/abs/1703.09312) trained a network on millions of
synthetic depth images labelled by an analytic grasp quality metric — the
[epsilon metric](03_choosing-a-grip.md#9-grasp-quality-metrics-you-can-compute) —
rather than by real attempts. That is a genuinely clever move, because it means
the labels are free and exact, and it is also the family's limitation: the model
learned to reproduce an analytic metric, so it inherits that metric's blind spots
rather than escaping them. The [project
page](https://berkeleyautomation.github.io/dex-net/) is still up.

The licence on both `gqcnn` and `dex-net` is a University of California grant for
"educational, research, and not-for-profit purposes" with a Berkeley technology
licensing office contact for anything else. It is not a standard open-source
licence and it is not commercially usable as written.

Five jobs a planar model suits:

- a conveyor or table where every object is lying flat and top-down is correct
- a first working system, because these are the only ones that install easily
- running on modest hardware, including without a graphics card
- suction-like problems where the question is really "which patch, and at what
  angle in the image"
- teaching, because the representation is visible and the failures are obvious

Five jobs it cannot do:

- any grasp that is not straight down, which is most grasps in a full tote
- objects lying against a wall, where the only feasible approach is from the side
- reasoning about the object's far side, having only a depth image
- anything on modern Python without work, since all three are pinned to
  2020-era toolchains
- shipping commercially in the Dex-Net case, for the licence reason above

## 3. Sampling and scoring: the geometric ancestors

Before learned six-degree-of-freedom generation, the approach was to sample a
large number of geometrically plausible grasps from the point cloud and then
score them. That is still the most transparent approach in this document, and one
of its implementations is the only thing here with a genuinely permissive licence
and no CUDA requirement.

**[GPD, Grasp Pose Detection](https://github.com/atenpas/gpd)** samples candidate
grasps on a point cloud, checks each for the geometric conditions in
[choosing a grip](03_choosing-a-grip.md#3-friction-cones-and-the-antipodal-test),
and classifies the survivors with a small network. It is **BSD-2-Clause**, it is
C++ built on PCL, Eigen and OpenCV, and it states no CUDA requirement. It was
last pushed in January 2022, so treat it as finished rather than maintained — the
OpenCV 3.4 and PCL dependencies are the practical obstacle, not the algorithm.
[PointNetGPD](https://github.com/lianghongzhuo/PointNetGPD) is the MIT-licensed
successor idea, last pushed May 2025.

The reason to know about GPD in 2026 is not that it is the best. It is that it is
the only model in this area you can put in a commercial product without either a
licence negotiation or a lawyer, and the only one with a plausible path to running
on a machine without an NVIDIA card. That combination is rare enough to be worth
a paragraph.

Five jobs a sampling-and-scoring approach suits:

- commercial work, where the licence position of everything else is a problem
- machines without a graphics card
- pipelines where you want to see and log why each candidate was rejected
- adding your own geometric constraints, since the sampling stage is explicit
- producing a large candidate set for something else to filter

Five jobs it cannot do:

- match the accuracy of the learned six-degree-of-freedom models on cluttered
  scenes, which is a real gap and not a small one
- run on a modern dependency stack without effort
- handle transparent or reflective objects, having no point cloud to sample from
- benefit from any of the last four years of research, being frozen
- produce grasps for a multi-finger hand

## 4. Six-degree-of-freedom models

This is where the field is, and where the licence problem is.

### 4.1 The Contact-GraspNet line

[6-DOF GraspNet](https://arxiv.org/abs/1905.10520) introduced generating grasps
directly rather than sampling and filtering: a variational model proposes poses
and a second network refines them.
[Contact-GraspNet](https://arxiv.org/abs/2103.14127) made it practical by
predicting grasps as *contact points on the observed point cloud*, which reduces
the search space enormously and is the idea most later work builds on.

The [NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet)
repository has 533 stars and was last pushed in November 2024. **Its licence is a
file called `License.pdf`.** There is no machine-readable licence, GitHub's
licence API reports nothing, and every dependency scanner you run will report the
project as unlicensed. You have to open the PDF and read it, which is exactly the
kind of thing nobody does before a prototype turns into a product.

The maintained PyTorch reimplementation is
[elchun/contact_graspnet_pytorch](https://github.com/elchun/contact_graspnet_pytorch),
87 stars, last pushed February 2025. **It copied the PDF rather than fixing it**,
so switching to the fork does not solve the licence problem.

### 4.2 The GraspNet-1Billion line

The other major lineage comes from Shanghai Jiao Tong University and is built
around the [GraspNet-1Billion](https://graspnet.net/) dataset. Four pieces of
software matter.

| Project | Licence, read from the file | State |
| --- | --- | --- |
| [graspnet-baseline](https://github.com/graspnet/graspnet-baseline) | SJTU academic and non-profit **non-commercial research use only** | the reference implementation |
| [graspness_unofficial](https://github.com/graspnet/graspness_unofficial) | the identical SJTU non-commercial agreement, despite the name | last pushed June 2024 |
| [AnyGrasp SDK](https://github.com/graspnet/anygrasp_sdk) | **no licence file at all**; a compiled library plus a machine-locked key you apply for through a form | pushed July 2026; the strongest of them |
| [EconomicGrasp](https://github.com/iSEE-Laboratory/EconomicGrasp) | **MIT** | pushed April 2026 |

Three things about this group are worth stating precisely.

**The dataset licence is self-contradictory.** The GraspNet
[datasets page](https://graspnet.net/datasets.html) says that all data, labels,
code and models are licensed under a "Creative Commons Attribution 4.0 Non
Commercial License (BY-NC-SA)". That names three mutually inconsistent licences
in one sentence — CC BY 4.0 is not non-commercial, and BY-NC-SA is a fourth
thing again. There is no identifier you can safely put in a dependency manifest.
The only safe reading is non-commercial and share-alike, and the page gives an
email address for commercial queries, which tells you how the authors intend it.

**The "unofficial" reimplementation carries the original's terms, and more.** The
licence file in `graspness_unofficial` is verbatim the SJTU agreement, including
a derivatives clause stating that any modification you make becomes owned by the
licensor. It also, because it was copied from another SJTU project, contains a
trademark clause forbidding use of the name "AlphaPose" — a completely unrelated
piece of software. A licence that has been copy-pasted without being read is a
licence you should assume was not thought about.

**EconomicGrasp is the exception and is genuinely MIT.** It is also the most
recently pushed of the four. If you want something from this lineage and need a
real licence, this is where to look first.

### 4.3 GraspGen, and the one genuinely permissive modern model

[GraspGen](https://arxiv.org/abs/2507.13097) is NVIDIA's 2025 diffusion-based
grasp generator. Its licence position is split four ways, and the split runs in a
direction nobody guesses:

| Artefact | Licence, verified |
| --- | --- |
| [NVlabs/GraspGen](https://github.com/NVlabs/GraspGen) code | NVIDIA License — **non-commercial**, with a clause permitting NVIDIA itself to use the work commercially |
| [NVlabs/GraspGenX](https://github.com/NVlabs/GraspGenX) code | **Apache-2.0**, plain, with no use limitation appended |
| its published weights | NVIDIA Open Model License |
| its training dataset | CC BY 4.0 |

The successor repository is more permissive than the original, which is the
opposite of the usual direction and worth knowing. The weights you would actually
run are still under NVIDIA's own model licence rather than Apache-2.0, so the
Apache badge on `GraspGenX` does not make a deployment Apache-2.0 — the same
shape of trap as [Isaac ROS's
transport](../06_object-perception/06_licences-and-platforms.md#4-putting-it-in-ros-2)
in the perception area.

[M2T2](https://github.com/NVlabs/M2T2) is NVIDIA's earlier multi-task transformer
producing both grasps and placements, under the same non-commercial NVIDIA
License.

Five jobs a six-degree-of-freedom grasp model suits:

- bin picking of mixed, unknown, opaque objects with no shared structure
- warehouse totes, where the next item is genuinely unpredictable
- generating many candidates for a geometric filter to reduce
- a first pass at an object family before you have worked out a rule
- research, where the licence terms are satisfied by construction

Five jobs it cannot do:

- respect any constraint that is not about slipping
- work on transparent or reflective objects, having no usable point cloud
- explain why it chose a grip, which is what you need when one fails
- run without an NVIDIA graphics card, for every model in section 4 — see
  [section 8](#8-what-runs-without-cuda)
- be shipped commercially, for every model in section 4 except `EconomicGrasp`
  and `GraspGenX`'s code

## 5. The licence picture

This subject has the worst licence hygiene of any area in these documents. That
is a strong claim, so here is the evidence, all of it read from the projects'
own files in September 2026.

### 5.1 The six patterns

**No licence file at all.** This is the commonest case and the most dangerous,
because default copyright grants nothing — not commercial use, not research use,
not the right to modify. Verified examples with real traction:
[DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) (572 stars),
[GraspVLA](https://github.com/PKU-EPIC/GraspVLA) (419),
[UniDexGrasp](https://github.com/PKU-EPIC/UniDexGrasp) (273),
[GenDexGrasp](https://github.com/tengyu-liu/GenDexGrasp) (210),
[DexGraspNet2](https://github.com/PKU-EPIC/DexGraspNet2) (159),
[DexGraspNet](https://github.com/PKU-EPIC/DexGraspNet), and
[suctionnet-baseline](https://github.com/graspnet/suctionnet-baseline). Seven
widely used projects, none of which you have permission to use.

**A licence in a format nothing can read.** Contact-GraspNet's `License.pdf`, and
its maintained fork's copy of the same PDF.

**A licence that contradicts itself.** GraspNet-1Billion's three-labels-in-one-
sentence, above.

**A licence copied without being read.** `graspness_unofficial`'s stray AlphaPose
trademark clause.

**Code and weights under different licences.** GraspGen's four-way split.
GraspVLA's weights on Hugging Face are CC BY-NC-4.0 while its code carries no
licence at all, and its billion-scale training dataset carries no licence tag
either.

**Someone else relabelling a licence.** There is a Hugging Face repository
mirroring Contact-GraspNet's weights that declares them MIT. The upstream licence
is an NVIDIA agreement in a PDF and is certainly not MIT. A third party cannot
grant rights they do not hold, and a licence field on a mirror is not a licence.

### 5.2 The one that will catch you out

There is also a trap that has nothing to do with grasping and everything to do
with what the research code depends on.
[GraspXL](https://github.com/zdchan/GraspXL) (271 stars) and
[RobustDexGrasp](https://github.com/zdchan/RobustDexGrasp) (174) both vendor the
RaiSim physics simulator. Their licence file makes the MIT grant apply only to
the wrapper directories, and states that you must obtain a valid licence from
raisim.com for the simulator itself, which is then activated with a key they send
you. **The physics engine these projects need is paid software.** GitHub shows
the repository as unclassified and nothing on the project page says so.

### 5.3 What this means in practice

If you are building something you will sell, the shortlist of grasp models you
can legitimately use is very short: **GPD** (BSD-2-Clause), **GG-CNN** and
**GR-ConvNet** (BSD-3-Clause), **PointNetGPD**, **6-DOF GraspNet's PyTorch
ports** and **EconomicGrasp** (MIT), and **GraspGenX's code** (Apache-2.0, with
the weights under a separate NVIDIA licence). Everything else needs a
negotiation, and several need one with a university technology transfer office.

If you are doing research, most of the non-commercial licences permit what you
are doing — but the seven projects with no licence file at all do not, and that
is worth knowing before a paper's artefact review.

## 6. Suction models

A suction grasp is a simpler prediction than a finger grasp: the question is
whether a patch is flat enough, smooth enough and reachable enough to seal
against, and which way its normal points. There is correspondingly less
machinery, and correspondingly less software.

**Dex-Net 3.0** extended the Dex-Net family to suction, with the same analytic
labelling approach and the same UC Regents licence.

**[SuctionNet-1Billion](https://github.com/graspnet/suctionnet-baseline)** is the
suction counterpart of GraspNet-1Billion, from the same group. It was last pushed
in August 2023 and **has no licence file at all**.

In practice most working suction systems do not use a model. They fit planes to
the depth image, reject patches whose residual is too large or whose normal is
too far from the approach direction, and rank what is left by area and by
distance from the edge. That is a dozen lines of Open3D, it runs in milliseconds
on a laptop, and it is genuinely competitive — which is the strongest argument in
these documents for trying the geometric method first.

Five jobs suction grasp selection suits:

- cartons, bags, books, envelopes and anything with a large flat face
- objects lying in a way that gives no side access at all
- high-rate picking, since the cycle time is the vacuum's and not the arm's
- objects too heavy or too large for two fingers to get around
- any cell where the perception requirement needs to stay cheap

Five jobs it cannot do:

- porous or textured surfaces, where no seal forms
- ribbed, corrugated or sharply curved surfaces, for the same reason
- oily or dusty parts, which foul the cup and leak
- anything where the only reachable face is a thin edge
- anything where the object must be held precisely, since a cup permits rotation
  about its own axis

## 7. Dexterous hands, and grasping language models

Two active research areas that produce a great deal of work and almost nothing
you can deploy.

**Dexterous grasping** generates joint configurations for a multi-finger hand
rather than a pose for two fingers. The output is far larger — twenty or more
numbers rather than six — and the evaluation is harder, because a
multi-finger grasp can be stable in simulation and impossible on the real hand.
The projects with traction are [DRO-Grasp](https://github.com/zhenyuwei2003/DRO-Grasp)
(MIT, pushed April 2026), [DexGrasp-Anything](https://github.com/4DVLab/DexGrasp-Anything)
(MIT, December 2025) and [UniDexGrasp2](https://github.com/PKU-EPIC/UniDexGrasp2)
(MIT), against a larger group with no licence at all.

**Grasping vision-language-action models** take an instruction in words and
produce grasps directly. [GraspVLA](https://github.com/PKU-EPIC/GraspVLA) and
[DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) are the visible ones.
Both have no code licence. DexGraspVLA's planner runs a 72-billion-parameter
vision-language model and its own documentation describes an eight-GPU server;
it is not something you evaluate on a workstation, let alone a laptop.

Five jobs dexterous and language-conditioned grasping suits:

- research, which is what it is for and where it is genuinely exciting
- tasks where the object must be re-oriented in the hand rather than put down
- tool use, where the grasp has to permit the tool's function
- human-hand teleoperation and imitation, where the hand matches the demonstrator
- exploring what will be possible in three years

Five jobs it cannot do:

- run on affordable hardware, for the language-conditioned ones especially
- be deployed, since most of the leading repositories grant no rights at all
- transfer reliably from simulation to a real multi-finger hand, which remains
  the open problem
- justify the hardware cost against a two-finger gripper for ordinary pick and
  place
- be maintained, in the sense that most of these are paper artefacts rather than
  products

## 8. What runs without CUDA

The honest answer for this document, in contrast to the perception area's, is
**almost nothing**, and the reason concentrates in a single library.

### 8.1 One abandoned library is the gate

[MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine) is NVIDIA's sparse
convolution library. It is MIT-licensed, it has 2,960 stars, and **it was last
pushed in March 2024 with 236 open issues**. Its documented requirement is CUDA
10.1 or later, matching the CUDA version PyTorch was built against, and the
install path compiles with `nvcc`.

`graspness_unofficial`, `anygrasp_sdk` and `EconomicGrasp` all import it. That
is three of the four models in the GraspNet-1Billion lineage. So the barrier for
an Apple Silicon reader is not the vague one people expect — it is one specific
abandoned sparse-convolution library that three leading models depend on and
nobody maintains.

The second-tier blockers, each of which is also fatal on its own, are custom
`pointnet2` CUDA operators (Contact-GraspNet, graspnet-baseline, graspness,
EconomicGrasp, GraspGen), `spconv-cu120` (GraspGen), `flash-attn` (GraspVLA) and
`xformers` (DexGraspVLA). None of these has a CPU or Metal build.

### 8.2 The table

Read this as: what specifically stops it, rather than a yes or a no. Every
blocker named was read from the project's own requirements file, environment file
or README.

| Model | What blocks it | Runs on an Apple Silicon Mac? |
| --- | --- | --- |
| [GPD](https://github.com/atenpas/gpd) | nothing GPU-related; PCL 1.9, Eigen, OpenCV 3.4 | **yes in principle** — the obstacle is the ageing C++ dependencies |
| [GG-CNN](https://github.com/dougsm/ggcnn) | plain PyTorch, no custom operators | **probably**, but it is pinned to a 2020 Python |
| [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) | TensorFlow `pointnet2` operators compiled with `nvcc`; its environment file pins CUDA 10.1 | no |
| its [PyTorch fork](https://github.com/elchun/contact_graspnet_pytorch) | environment pinned to CUDA 11.7 | no |
| [graspnet-baseline](https://github.com/graspnet/graspnet-baseline) | its `requirements.txt` looks innocent; the README then tells you to compile `pointnet2` and a CUDA `knn` operator | no |
| [graspness_unofficial](https://github.com/graspnet/graspness_unofficial) | MinkowskiEngine, `pointnet2`, and a CUDA `knn` operator | no |
| [AnyGrasp](https://github.com/graspnet/anygrasp_sdk) | CUDA, a modified MinkowskiEngine fork, and a **machine-locked licence key** | no, twice over |
| [EconomicGrasp](https://github.com/iSEE-Laboratory/EconomicGrasp) | MinkowskiEngine, `pointnet2`, CUDA 12 | no |
| [GraspGen](https://github.com/NVlabs/GraspGen) | `spconv-cu120`, for which no CPU build exists | no |
| [GraspVLA](https://github.com/PKU-EPIC/GraspVLA) | `flash-attn`, which cannot be installed on Apple Silicon at all | no |
| [DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) | `xformers`, plus an eight-GPU server for the planner | no |

The pattern worth noticing is in the `graspnet-baseline` row. **A clean
`requirements.txt` is not evidence that a project will install.** The CUDA
dependency is a manual compilation step described in prose in the README, which
no dependency scanner and no quick look at the repository will show you. Reading
the install instructions rather than the requirements file is the only reliable
check.

### 8.3 What this means if you are on a Mac

Develop the geometry on the Mac and the model somewhere else, or do not use a
model. Concretely: the methods in [choosing a grip](03_choosing-a-grip.md) all
run natively, MuJoCo and its model collection run natively, the ROS 2 control
stack runs through RoboStack, and a rule-based pipeline can be complete and
tested before any model is involved. That is a real workflow rather than a
consolation, and it is what this repository does.

## 9. Using a model as a candidate generator

The structural recommendation of this document is short. **Use the model to
propose and something else to decide.**

A grasp model's output is a ranked list of poses. Treat that list as candidates
and pass it through the same filters a geometric planner would apply, in this
order:

1. Reject any pose the arm cannot reach, which needs an inverse kinematics query
   and not a guess — the
   [reachability document](../08_arm-movement/02_reaching-and-reachability.md)
   is about how much that question hides.
2. Reject any pose whose gripper body collides with the table, the tote or a
   neighbour — the [bound-the-search
   argument](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body),
   applied to somebody else's candidates.
3. Reject any pose whose required opening is outside your gripper's usable
   stroke, which is not the catalogue stroke once fingertips are fitted.
4. Reject any pose that puts a finger on a region you have marked as
   not-to-be-touched.
5. Reject any pose that does not permit the next operation — the placement
   orientation, the insertion direction, the pour.
6. Rank what survives by your own criteria, not by the model's confidence.

Every one of those is a constraint the model cannot be told, and applying them
after the model rather than instead of it gets you the model's breadth and your
own task knowledge at the same time.

The other half of the recommendation is a reporting rule. **Log which filter
rejected each candidate.** When the pipeline returns nothing, the useful output
is "forty-eight candidates, thirty-one unreachable, fifteen colliding, two too
wide", which tells you immediately whether the problem is the model, the gripper
or the cell. A pipeline that returns an empty list with no reasons is one you
will debug by guessing.
