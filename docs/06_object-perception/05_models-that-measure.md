# Models that measure

Models you download that answer "how big is it" and "which way is it turned".

Read [the methods you write yourself](03_programmed-methods.md) first. For most
table-top work the geometry there is more accurate than anything in this
document, and the models here earn their place in the cases geometry cannot
reach: an object you have no depth reading for, a scene you have only one
photograph of, or a part whose orientation you need and whose CAD model you have.

One warning governs the whole document, and section 1.3 makes the case with
numbers. **Learned depth is not a measuring instrument.** It is for recovering a
rough scale that real geometry then pins down.

## Contents

1. [Depth from a single picture](#1-depth-from-a-single-picture)
2. [Stereo matching](#2-stereo-matching)
3. [Pose estimation, when you have a model](#3-pose-estimation-when-you-have-a-model)
4. [Reconstruction, when you do not](#4-reconstruction-when-you-do-not)
5. [Datasets and benchmarks](#5-datasets-and-benchmarks)

---

## 1. Depth from a single picture

There is a family of models that takes one ordinary photograph and returns a
depth for every pixel. They are remarkable, they are widely misunderstood, and
using one to measure an object is usually a mistake. This section explains why,
because the mistake is easy to make and hard to notice.

### 1.1 Relative depth and metric depth are not the same thing

Most of these models predict **relative** depth, also called affine-invariant
depth. That means the output preserves only the *order* of distances: it tells you
that the mug is nearer than the wall, and it is defined up to an unknown scale and
an unknown offset. The same model gives the same answer for a doll's house and a
real room.

Models are trained this way on purpose. Dropping the requirement to be metric lets
them learn from many datasets at once, none of which agree about units, and that
is exactly what buys their famous ability to work on any picture. The
generalisation and the uselessness for measurement have the same cause.

**Metric** models predict actual metres. They are the ones you would need, and
they generalise noticeably worse, for the reason just given.

### 1.2 The models, and their licences

The weights licence is the one that binds you, and it is often not the code
licence. Read this table as: code first, then weights, then whether the output is
in real units.

| Model | Code | Weights | Metric? | Where |
| --- | --- | --- | --- | --- |
| Depth Anything 3 | Apache-2.0 | **split**: Small, Base, `DA3METRIC-LARGE`, `DA3MONO-LARGE` are Apache-2.0; Large, Giant, Nested are **CC BY-NC 4.0** | `DA3METRIC-LARGE` yes | [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) |
| Depth Anything V2 | Apache-2.0 | **Small Apache-2.0; Base, Large, Giant CC BY-NC 4.0** | fine-tunes only | [DepthAnything/Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2) |
| Metric3D v2 | BSD-2-Clause | no separate licence stated | yes | [YvanYin/Metric3D](https://github.com/YvanYin/Metric3D) |
| MoGe-2 | MIT | MIT | yes | [microsoft/MoGe](https://github.com/microsoft/MoGe) |
| UniDepth v2 | **CC BY-NC 4.0** | non-commercial | yes | [lpiccinelli-eth/UniDepth](https://github.com/lpiccinelli-eth/UniDepth) |
| Depth Pro (Apple) | Apple sample-code licence, no patent grant | same | yes, and needs no focal length | [apple/ml-depth-pro](https://github.com/apple/ml-depth-pro) |
| Marigold | Apache-2.0 | RAIL++-M | no, relative only | [prs-eth/Marigold](https://github.com/prs-eth/Marigold) |
| ZoeDepth, MiDaS | MIT | — | ZoeDepth yes | **both archived — do not start here** |

Two things to take from that table. `DA3METRIC-LARGE` and MoGe-2 are the strongest
metric models with genuinely permissive weights, and that is a recent development:
until Depth Anything 3, the useful sizes of the most popular model were all
non-commercial. And the Apache-2.0 badge on the Depth Anything repositories refers
to the *code*; the large weights are not Apache, which is the single most common
licence misreading in this area.

### 1.3 What accuracy they actually achieve

The published tables and the independent evaluations do not agree, and the
difference is large enough to change decisions.

On their own benchmarks these models look superb. Metric3D v2 reports an absolute
relative error of 0.045 on NYUv2, and Depth Anything V2 reports 0.056. An absolute
relative error of 0.05 means five per cent of the true distance, so at one metre
that is **fifty millimetres**.

Read that again, because it is the point. The best published number on the
friendliest benchmark is ±50 mm at a metre. A three-hundred-pound RealSense gives
two to five.

Independent evaluations are worse still. A 2025 benchmark that measured these
models against ChArUco ground truth outside their training distribution found
Depth Anything V2 at 21.1% relative error and Depth Pro at 33.6% — and a plain
geometric projection baseline beat three of the four learned models. A robotics
paper measuring off-the-shelf Depth Anything for grasping found a mean absolute
error of 121 to 141 mm, and concluded in its own words that these models are
"insufficiently precise for tasks involving physical interaction".

The same paper got to 13.4 mm by aligning the model's output against a handful of
real measured points, which is the honest way to use these things: as a dense
guess that a few real measurements pin down.

Five jobs monocular depth suits:

- recovering scale for a reconstruction that has none, roughly, before refining it
- separating foreground from background, where ordering is all you need
- filling holes where a real depth sensor returned nothing
- checking that a scene looks the way you expect, as a sanity test
- working from an archive of ordinary photographs, where no other option exists

Five jobs it cannot do:

- measure an object to millimetres, which is this document's whole subject
- give trustworthy answers on objects unlike its training data
- measure transparent or reflective things, which it confidently hallucinates
- provide any error bar, so you cannot tell a good prediction from a bad one
- replace a depth sensor, at any price point

## 2. Stereo matching

A stereo pair of ordinary cameras a known distance apart gives metric depth by
triangulation, and the quality depends entirely on how well the two pictures are
matched. That matching is where learned models have genuinely helped.

| Model | Licence | Notes |
| --- | --- | --- |
| [RAFT-Stereo](https://github.com/princeton-vl/RAFT-Stereo) | **MIT** | the sensible default; its custom CUDA kernel is optional, so it runs without one |
| [IGEV / IGEV++](https://github.com/gangweiX/IGEV) | MIT | stronger on the KITTI benchmarks |
| [FoundationStereo](https://github.com/NVlabs/FoundationStereo) | **NVIDIA, non-commercial** | very strong; a separate commercial model is available from NVIDIA on request |
| CREStereo | Apache-2.0 | last touched in 2023, effectively dead |
| OpenCV `StereoSGBM` | Apache-2.0 | the classical baseline everything is measured against, and no GPU needed |

Five jobs stereo matching suits:

- outdoor and brightly lit scenes, where projected-pattern sensors wash out
- large working volumes, where you can afford a wide baseline
- textured objects, which give the matcher something to work with
- situations where you want to choose your own cameras and resolution
- refining a cheap depth sensor's output using the same two images

Five jobs it cannot do:

- textureless surfaces, without projecting a pattern — at which point it is active
  stereo
- transparent and mirrored objects, whose apparent position differs between the
  two views
- very close range, where the two cameras see too little in common
- thin structures, which fall between matched patches
- give better accuracy than the baseline and the calibration allow, regardless of
  the model

## 3. Pose estimation, when you have a model

If you already have a CAD model of the object, the measuring problem changes
shape. You no longer need to work out how big it is — you know. What you need is
where it is and which way it is turned, which is the 6-DoF pose from
[section 1 of the segmentation document](01_overview.md#1-four-answers-and-which-one-you-need).

This is the mature end of the field, and it is also where the licences are worst.
Read the table as: whether you need a CAD model, what the licence permits, and
whether it will run without an NVIDIA card.

| Method | Needs a model? | Licence | Commercial use | Runs without CUDA |
| --- | --- | --- | --- | --- |
| [HappyPose](https://github.com/agimus-project/happypose) (CosyPose + MegaPose) | yes | **BSD-2-Clause** | **yes** | **yes, documented CPU path** |
| [MegaPose](https://github.com/megapose6d/megapose6d) | yes | Apache-2.0 | yes | GPU assumed |
| [FoundationPose](https://github.com/NVlabs/FoundationPose) | CAD or a few reference images | **NVIDIA, non-commercial** | **no** | no, needs nvdiffrast and pytorch3d |
| [GigaPose](https://github.com/nv-nguyen/gigapose) | yes, as templates | MIT | yes | GPU assumed |
| [SAM-6D](https://github.com/JiehongLin/SAM-6D) | yes | **no licence file at all** | **no** | no |
| [DOPE](https://github.com/NVlabs/Deep_Object_Pose), [CenterPose](https://github.com/NVlabs/CenterPose) | trained per object | **NVIDIA, non-commercial** | **no** | no |
| [OnePose++](https://github.com/zju3dv/OnePose_Plus_Plus) | a reference video | **registration-gated** since 2026 | conditional | no |
| [Gen6D](https://github.com/liuyuan-pal/Gen6D) | reference images | **GPL-3.0** | copyleft | no |

Three things in that table are worth saying plainly.

**HappyPose is the practical answer for most people.** It is BSD-2-Clause, it is
actively developed, it packages CosyPose and MegaPose behind one interface, it has
a [ROS 2 wrapper](https://github.com/agimus-project/happypose_ros), and it is the
only entry here with a documented path that does not need an NVIDIA card.

**FoundationPose is the best-known and you probably cannot ship it.** Its licence
restricts use to research and evaluation. It is genuinely excellent and it is not
a product component.

**SAM-6D has no licence file at all**, which is legally worse than a
non-commercial licence: with no licence, default copyright applies and you have no
permission to use it for anything.

The benchmark for all of this is the [BOP
challenge](https://bop.felk.cvut.cz/), whose leaderboards are the place to look
for current standings. One caution about reading them: the headline number, AR, is
a recall rate — the fraction of object instances localised within a set of pose
error thresholds. It is not a measurement in millimetres and cannot be converted
into one.

Five jobs model-based pose suits:

- assembly, where the part must go in the right way round
- bin picking of a known part, which is the industry's single biggest application
- putting an object down in a specified orientation
- inspection, by comparing a fitted pose against a nominal one
- grasp planning against a known model, where good grasps can be precomputed

Five jobs it cannot do:

- objects you have no model of, which rules out most of the natural world
- deformable objects, whose shape is not a rigid transform of a model
- objects that vary between instances, such as produce or castings
- measuring an unknown size, since it assumes the size is known
- telling you which of several identical parts you are looking at

## 4. Reconstruction, when you do not

If you have neither a depth sensor nor a model, you can build a 3D model from many
pictures. This is photogrammetry, and its modern relatives are neural radiance
fields and Gaussian splatting.

The table gives the accuracy each method achieves on the DTU benchmark, in
millimetres of Chamfer distance, on objects roughly 20 to 30 cm across
photographed by about 50 calibrated cameras in a laboratory. Treat these as a best
case rather than a field result.

| Method | DTU error | Licence |
| --- | --- | --- |
| Neuralangelo | 0.61 mm | NVIDIA, non-commercial, and locked to NVIDIA processors |
| [NeuS](https://github.com/Totoro97/NeuS) | 0.84 mm | **MIT — the permissive one in this family** |
| PGSR | 0.47 mm | non-commercial |
| 2DGS, GOF, RaDe-GS | 0.68 to 0.80 mm | Inria licence, non-commercial |
| [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting) | 1.96 mm | **Inria licence, research only** |
| [COLMAP](https://github.com/colmap/colmap) | — | **BSD-3** — classical photogrammetry, still the backbone |

### 4.1 Two warnings

**The licensing here is unusually bad.** Almost the entire Gaussian-splatting
surface-reconstruction ecosystem carries Inria's research-only licence, and the
variants inherit it verbatim. If you intend to ship something, the options are
COLMAP, [OpenMVG](https://github.com/openMVG/openMVG) (MPL-2.0), NeuS (MIT),
[Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) (Apache-2.0) and
[Brush](https://github.com/ArthurBrussee/brush) (Apache-2.0). Note that
[OpenMVS](https://github.com/cdcseacave/openMVS) is AGPL-3.0, whose network clause
can oblige you to publish your own source if you run it behind a service.

**A Gaussian splat is not a surface.** The centres of the Gaussians are not points
on the object; they are blob centres optimised to make renders look right. Plain
3D Gaussian Splatting comes last in that table at 1.96 mm on a 25 cm laboratory
object — about 0.8% — which is worse than a RealSense. The surface-oriented
variants do much better and are the non-commercial ones.

### 4.2 And none of it has a scale

Every method in this section reconstructs up to an unknown scale, because a
pinhole camera measures directions and the reprojection error is unchanged if you
scale the whole scene and all the camera positions together. The DTU numbers above
are in millimetres only because DTU supplies external ground truth to register
against.

For a robot there is a neat answer that most write-ups miss. **The arm already
knows where the camera was.** If the camera is on the wrist, every viewpoint's
position is known in millimetres from the joint encoders, so feeding those known
camera positions into the reconstruction makes the result metric with no markers
in the scene at all. The accuracy is then bounded by your hand-eye calibration,
which is the next section.

Five jobs reconstruction suits:

- building a model of an object you will then track with the pose methods in section 3
- measuring something too large or awkward for a single view
- capturing shape where no CAD exists, such as a casting or a natural object
- inspection against a nominal model, once the scale is fixed
- documentation and simulation assets

Five jobs it cannot do:

- measure anything, until the scale has been supplied from outside
- work quickly — this is minutes to hours, not milliseconds
- handle transparent, shiny or textureless objects, which defeat the matching
- run unattended in a cell, in most current implementations
- be shipped commercially, for most of the newest and best methods

## 5. Datasets and benchmarks

Measurement is harder to benchmark than detection, because ground truth has to be
metric. The ones worth knowing:

| Benchmark | What it measures | Licence |
| --- | --- | --- |
| [BOP](https://bop.felk.cvut.cz/) | 6-DoF pose, across many datasets | **per-dataset; some are CC BY-NC-SA** |
| [DTU](https://roboimagedata.compute.dtu.dk/) | reconstruction accuracy, in millimetres | academic |
| [NYU Depth v2](https://cs.nyu.edu/~fergus/datasets/nyu_depth_v2.html) | monocular depth, indoors | research |
| [KITTI](https://www.cvlibs.net/datasets/kitti/) | depth and stereo, outdoors | CC BY-NC-SA |
| [ETH3D](https://www.eth3d.net/) | stereo and multi-view | research |
| [GraspNet-1Billion](https://graspnet.net/) | grasp poses on real scans | **CC BY-NC-SA 4.0** |

BOP's newest group, **BOP-Industrial**, is the most relevant to a table-top or
bin-picking cell: cluttered scenes of real industrial parts, contributed by XYZ
Robotics, MVTec and Intrinsic.

One caution about reading any of these. BOP's headline number, AR, is a recall
rate — the fraction of object instances localised within a set of error
thresholds. It is not millimetres and does not convert to millimetres.

