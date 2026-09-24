# Working without an NVIDIA graphics card

This document answers one question in one place: if your computer has no NVIDIA
graphics card, what robot arm work can you still do, and what can you not?

It is written for somebody developing on an Apple Silicon Mac, which is the
machine this whole repository assumes. Apple Silicon means the processors Apple
has shipped in its own computers since 2020, the M-series chips, which use an
architecture called `arm64` and a graphics interface called Metal rather than
NVIDIA's CUDA. CUDA, which stands for Compute Unified Device Architecture, is
NVIDIA's programming interface for its own graphics cards. A very large amount of
robotics software is written against CUDA directly, and that is the source of
nearly every problem in this document.

The answer to the question already exists in this repository, but it is spread
across four documents, one per area, and none of them sees the whole picture.
**This document is the index over those four, not a replacement for any of
them.** Each area's own document has the licences, the library-by-library detail
and the comparison grids. This one has the cross-cutting argument: which kinds of
failure exist, which are real, which are imaginary, and what to do about each.
The four are:

- [perception: licences and platforms](../06_object-perception/06_licences-and-platforms.md)
- [gripping: licences and platforms](../07_gripping/07_licences-and-platforms.md)
- [arm movement: licences and platforms](06_licences-and-platforms.md)
- [the frontier: simulation and evaluation](../15_frontier/04_simulation-and-evaluation.md)

Every platform claim below was checked against a live source on 24 September
2026: a package index, a repository's own installation instructions, a
distribution channel, or a published support table. Where a claim could not be
checked, the text says so. The claims that disagree with the four documents above
are marked, because a document that quietly repeats a stale fact is worse than no
document.

There are no diagrams here. This document is a map over other documents rather
than an explanation of a mechanism, and its content is tables of verified facts.

## Contents

1. [The three questions people conflate](#1-the-three-questions-people-conflate)
2. [The honest map of the stack](#2-the-honest-map-of-the-stack)
3. [The pattern that rescues most of it](#3-the-pattern-that-rescues-most-of-it)
4. [What is genuinely impossible, and why](#4-what-is-genuinely-impossible-and-why)
5. [ROS 2 on Apple Silicon, precisely](#5-ros-2-on-apple-silicon-precisely)
6. [The practical strategies, ranked](#6-the-practical-strategies-ranked)
7. [When it does not matter](#7-when-it-does-not-matter)

---

## 1. The three questions people conflate

Almost every claim of the form "that does not work on a Mac" is about one of
three different things, and the person making the claim rarely says which. The
three are independent. A piece of software can fail any one of them while passing
the other two, so the blanket statement is usually wrong in a way that costs you
either two wasted days or an abandoned approach that would have worked.

### 1.1 Can I run it?

This is inference: loading a trained model and asking it for an answer. One
image in, a set of detected objects out. One observation in, one joint command
out.

Inference is the cheapest of the three and the one a Mac is best at. It needs the
model's weights to fit in memory and it needs the operations the model uses to be
implemented for whatever hardware you have. A Mac has two accelerators for this.
The first is the graphics processor, reached from PyTorch through a backend
called MPS, short for Metal Performance Shaders. The second is the Neural Engine,
a fixed-function accelerator reached through Apple's CoreML.

### 1.2 Can I train it?

Training means adjusting a model's weights from data. It needs several times the
memory that inference needs, because the optimiser keeps its own copy of the
weights and the backward pass keeps the intermediate activations. It also needs
throughput rather than latency: you are doing the same arithmetic several hundred
thousand times, and how long the whole run takes is what matters.

This is where a Mac loses, and the losses are of two kinds. Some training simply
will not fit. Some will fit and will take a week instead of an afternoon.

The clearest published statement of the memory requirement in this field is
[openpi](https://github.com/Physical-Intelligence/openpi)'s, which is a family of
vision-language-action policies for robot arms. Its README gives three modes and
the memory each needs, and the table is worth reading as the shape of the general
problem rather than as facts about one model. Read it as: what you want to do,
how much graphics memory it takes, and what card the authors suggest.

| Mode | Memory required | Example card the README names |
| --- | --- | --- |
| inference | more than 8 GB | RTX 4090 |
| fine-tuning with LoRA | more than 22.5 GB | RTX 4090 |
| full fine-tuning | more than 70 GB | A100 80 GB, or H100 |

LoRA stands for Low-Rank Adaptation, a way of fine-tuning that trains a small
number of extra parameters instead of all of them, which is why its requirement
is a third of the full figure rather than the same. The pattern generalises:
inference costs single-digit gigabytes, cheap fine-tuning costs about twenty, and
full fine-tuning costs about seventy. A Mac with 32 GB of unified memory is in
the first two rows and nowhere near the third.

### 1.3 Can I develop against it?

This is the one people forget, and it is the commonest cause of a lost day. It
asks whether the software installs at all, before any question of speed.

A Python package that contains a hand-written CUDA kernel has to be compiled by
NVIDIA's compiler, `nvcc`, against a CUDA toolkit. There is no CUDA toolkit for
Apple Silicon and there never will be. So `pip install` fails during the build,
with an error about a missing compiler rather than a missing graphics card, and
no amount of patience or CPU time helps.

The clean way to check this before committing to anything is to look at what the
Python Package Index publishes for the package. A package that ships a file named
`...macosx_14_0_arm64.whl` has a prebuilt Apple Silicon binary. A package that
ships only a source archive, or only files named `...linux_x86_64.whl`, does not.
Checked today, the contrast is exact:

| Package | What the index publishes for its current release |
| --- | --- |
| [`torch`](https://pypi.org/project/torch/) 2.14.0 | `macosx_14_0_arm64` wheels |
| [`torchvision`](https://pypi.org/project/torchvision/) 0.29.0 | `macosx_14_0_arm64` wheels |
| [`mujoco`](https://pypi.org/project/mujoco/) 3.14.0 | `macosx_11_0_arm64` wheels |
| [`pin`](https://pypi.org/project/pin/) 4.1.0, which is Pinocchio | `macosx_11_0_arm64` wheels |
| [`drake`](https://pypi.org/project/drake/) 1.57.0 | `macosx_15_0_arm64` wheels only, so it needs macOS 15 |
| [`toppra`](https://pypi.org/project/toppra/) 0.6.10 | no macOS wheel at all; build it yourself |
| [`flash-attn`](https://pypi.org/project/flash-attn/) 2.8.3 | a source archive and nothing else |
| [`xformers`](https://pypi.org/project/xformers/) 0.0.35 | a source archive and nothing else |
| [`tensorrt`](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/support-matrix.html) 11.3.0 | a source archive that pulls NVIDIA binaries |

The two source-only entries near the bottom are the ones that bite. `flash-attn`
and `xformers` are attention implementations that a great many recent models
import, and neither can be installed on a Mac by any route. When a model's
requirements file names either of them, the answer to question three is no, and
questions one and two never arise.

### 1.4 Why keeping them apart matters

The three questions have three different remedies, and applying the wrong remedy
is the usual waste.

Read the table below as: the failure you observed, what it actually means, and
what you do about it.

| What you see | Which question failed | What actually helps |
| --- | --- | --- |
| `pip install` stops with an `nvcc` or CUDA toolkit error | can I develop against it | find a reimplementation without the kernel; see [section 3](#3-the-pattern-that-rescues-most-of-it) |
| it installs, then raises `AssertionError: Torch not compiled with CUDA enabled` | can I run it | set the device to `mps` or `cpu` instead of `cuda` |
| it runs and produces the right answer in 40 seconds instead of 40 milliseconds | can I run it, slowly | export to CoreML, or accept it for development |
| it runs out of memory partway through a training run | can I train it | rent a machine, or train something smaller |
| the training run would finish in eleven days | can I train it | rent a machine; see [section 6.4](#64-rent-a-machine-by-the-hour) |

## 2. The honest map of the stack

This section is the consolidated version of the three per-area tables. Each area
keeps its full detail, its licences and its reasoning in its own document; what
follows is the platform column, lifted out and put side by side, because the
cross-cutting shape is not visible from inside any one area.

### 2.1 How to read the tables

Four states matter, and conflating them is how people end up believing the whole
field is closed to them. Every row in the tables that follow is one of these
four.

**Native** means there is a prebuilt Apple Silicon binary and it uses the Mac's
own hardware, either the graphics processor through Metal or the Neural Engine
through CoreML. This is as good as it gets.

**CPU only** means it installs and runs correctly on the Mac's central processor.
The answer is right; the time it takes is the question. For geometry, planning
and control this is almost always fine, because those workloads are small. For
neural networks it is usually between ten and a hundred times slower than a
graphics card, though the honest position is that nobody has published careful
figures for robot policies specifically, so treat that range as an order of
magnitude and not a measurement.

**CUDA absolutely** means the software contains hand-written NVIDIA code with no
other path through it. No amount of configuration changes this.

**Metal or MPS path** means somebody has done the work to make it use the Mac's
graphics processor. This is rarer than it should be and is the single best
predictor of whether a tool is pleasant to use here.

### 2.2 Perception

Perception is the area with the best news, and the reason is
[section 3](#3-the-pattern-that-rescues-most-of-it). The table below summarises
[the perception area's own platform section](../06_object-perception/06_licences-and-platforms.md#3-what-runs-on-an-apple-silicon-mac),
which has the per-library detail and the licences. Read the second column as the
state from section 2.1 and the third as what you do in practice.

| Thing | State | In practice |
| --- | --- | --- |
| OpenCV, Open3D, trimesh, PCL in C++ | native | classical vision and point-cloud geometry are unaffected; this is most of the work |
| PyTorch detectors and segmenters | Metal path, through `mps` | works; [Apple's own page](https://developer.apple.com/metal/pytorch/) states the requirements as an Apple Silicon Mac on macOS 14.0 or later |
| models in Hugging Face `transformers` | pure Python and PyTorch | installs and runs; see [section 3](#3-the-pattern-that-rescues-most-of-it) |
| the same models from their original repositories | CUDA absolutely, often | the repository and the port are different software; check both |
| CoreML exports, where one exists | native, and fast | [the measured figures](#26-the-numbers-that-are-actually-measured) are good |
| NVIDIA research models: FoundationPose, FoundationStereo, Instant-NGP | CUDA absolutely | no route |
| Isaac ROS | CUDA absolutely | see [section 4.1](#41-nvidia-isaac-ros) |
| COLMAP's dense reconstruction stage | CUDA absolutely | the sparse stage runs; the dense stage does not |
| `ros-jazzy-realsense2-camera` | Linux only | the RoboStack build exists for `linux-64` and `linux-aarch64` and for nothing else; the Python library `pyrealsense2-macosx` is what LeRobot uses on a Mac instead |

The last row is new here and is not in the perception document. It was checked
today against the RoboStack channel. It matters because a depth camera is the
most likely piece of real hardware a reader will attach, and the ROS 2 driver
package for the commonest one has no Apple Silicon build.

### 2.3 Gripping

Gripping is the area with the worst news, and the reason is unusually specific.
The full argument is in
[the gripping area's platform section](../07_gripping/07_licences-and-platforms.md#2-what-runs-on-an-apple-silicon-mac).

The gate is a single abandoned library.
[MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine) is NVIDIA's sparse
convolution library; it is what three of the four significant models in the
GraspNet-1Billion lineage import. Checked today through the GitHub interface, its
last push was 5 March 2024, it has about 2,960 stars, and the Python Package
Index has no macOS wheel for it in any version. It installs by compiling with
`nvcc`. So the obstacle to learned grasping on a Mac is not a vague shortage of
compute. It is one unmaintained dependency, and it has not moved in two and a
half years.

Read this table as: what you want to do about grasping, and whether the Mac can
do it.

| Thing | State | In practice |
| --- | --- | --- |
| antipodal tests, grasp quality metrics, centre-of-mass ranking | native | it is arithmetic on arrays; thousands of candidates in about a millisecond |
| MuJoCo and `mujoco_menagerie` gripper models | native | simulate the gripper and the contact |
| `ros2_controllers`, including the gripper and admittance controllers | native, via RoboStack | see [section 5.2](#52-what-robostack-actually-packages) |
| vendor gripper drivers | native | they are serial or Modbus; no compute involved |
| every model in the GraspNet-1Billion lineage | CUDA absolutely | via MinkowskiEngine |
| Contact-GraspNet and its PyTorch fork | CUDA absolutely | via custom `pointnet2` operators |
| GraspGen | CUDA absolutely | via `spconv-cu120`, which publishes no source archive and no macOS wheel |
| GraspVLA, DexGraspVLA | cannot be installed | via `flash-attn` and `xformers` |

The practical consequence, which the gripping document states and which is worth
repeating because it changes how you plan a project: build the rule-based
gripping pipeline first. It runs natively, it can be property-tested in a second
with no weights and no simulator, and it is complete enough to drive a real arm
before any model is involved.

### 2.4 Movement

Movement is the area where the Mac does best in absolute terms, and the reason is
that motion planning and control are small computations. A plan is milliseconds
of work on a few dozen numbers. The full detail is in
[this area's own platform section](06_licences-and-platforms.md#3-what-runs-on-an-apple-silicon-mac).

Read this table the same way as the two above.

| Thing | State | In practice |
| --- | --- | --- |
| MoveIt 2, OMPL, Pilz, MoveIt Task Constructor, `moveit_servo` | native, via RoboStack | the whole planning stack, verified package by package in [section 5.2](#52-what-robostack-actually-packages) |
| `ros2_control` and `ros2_controllers` | native, via RoboStack | trajectory execution, admittance control, the sensor broadcasters |
| Pinocchio | native | kinematics and dynamics from a robot description file, `macosx_11_0_arm64` wheel |
| Drake | native, with a condition | `macosx_15_0_arm64` wheel only, so macOS 15 or later |
| MuJoCo and MuJoCo MPC | native | universal binaries; see the numbers in [section 2.5](#26-the-numbers-that-are-actually-measured) |
| LeRobot | Metal path | its device selection tries CUDA, then Metal, then Intel's accelerator, then the processor; verified in its source today |
| TOPP-RA | CPU only, and build it yourself | no macOS wheel is published for 0.6.10 |
| ViSP, the visual servoing library | native from conda-forge; **not** in RoboStack | `visp` 3.7.0 has an `osx-arm64` conda-forge build; `ros-jazzy-visp` does not exist, so call the library directly |
| cuRobo | CUDA absolutely | see [section 4.3](#43-curobo-and-tensorrt) |
| Isaac ROS cuMotion | CUDA absolutely, and proprietary besides | see [section 4.1](#41-nvidia-isaac-ros) |
| openpi | CUDA absolutely | its README states plainly that it is tested on Ubuntu 22.04 and supports no other operating system |

### 2.5 Simulation, and the one engine with Metal physics

Simulation deserves separating out, because it is where the difference between a
Mac and a Linux machine with a card is largest, and because one recent result
changes the picture. The full treatment, with every simulator's history and
licence, is in
[the frontier document's platform section](../15_frontier/04_simulation-and-evaluation.md#3-what-runs-on-an-apple-silicon-mac).

The result worth knowing is Genesis World.
[Its installation page](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html),
read today, states that the engine "runs on Linux, macOS, and Windows, on the CPU
and on NVIDIA, AMD, and Apple Silicon GPUs", names the Apple Silicon backend
`gs.metal`, and carries a support table whose macOS and Apple Silicon row is
ticked in all four columns: graphics-processor simulation, processor simulation,
interactive viewer and headless rendering. It is the only physics engine in this
repository that runs its physics on the graphics processor of a Mac. The reason
is structural rather than a favour: Genesis writes its physics once in its own
compiler, Quadrants, which targets Metal alongside CUDA, so Apple Silicon support
is a compiler target rather than a port somebody has to keep alive.

Read the table below as the state of each simulator today, with what the claim
rests on.

| Simulator | On an Apple Silicon Mac | Verified from |
| --- | --- | --- |
| MuJoCo | native, universal binaries | `macosx_11_0_arm64` wheels for 3.14.0 on the package index |
| Genesis World | native, **including physics on the Metal graphics processor** | its installation page's support table |
| Gazebo Jetty | native, through Homebrew | [its macOS install page](https://gazebosim.org/docs/latest/install_osx/); binaries are built for Ventura and Sonoma |
| robosuite | native | it is MuJoCo underneath |
| ManiSkill | **CPU simulation and standard rendering, with a Vulkan install** | [its macOS install page](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/macos_install.html) — this has changed, see below |
| MJX-JAX | CPU only in practice | [the MJX page](https://mujoco.readthedocs.io/en/stable/mjx.html) says Apple Silicon; the caveat is below |
| Newton | CPU only, and it says so | its README: "macOS (CPU only)" and "macOS runs on CPU" |
| MuJoCo Warp | no | it compiles through NVIDIA Warp to CUDA |
| Isaac Sim, Isaac Lab | no | see [section 4.2](#42-isaac-sim-and-isaac-lab) |

Two rows need more than a line.

**ManiSkill's position has changed and the frontier document is now out of date on
it.** That document quotes the installation page as saying "no support for MacOS
at the moment". The page no longer says that. It now says that most macOS users
need to install a Vulkan driver, and links to a macOS installation page whose
first sentence is that ManiSkill "supports MacOS and can let you run CPU
simulation and the standard rendering", with graphics-processor simulation "not
yet supported on MacOS". The setup is the Vulkan software development kit, which
on a Mac runs through MoltenVK, a translation layer from Vulkan to Metal. So
ManiSkill moved from a no to a qualified yes, and the qualification is the same
one as everywhere else: no parallel environments.

**The MJX claim needs the same caveat the frontier document gives it, and it still
holds.** MJX is the JAX re-implementation of MuJoCo; JAX is a numerical library
that compiles Python for accelerators. The MJX page says MJX-JAX "runs on: Nvidia
and AMD GPUs, Apple Silicon, and Google Cloud TPUs". JAX runs on the Mac's
central processor without difficulty. Using the Mac's graphics processor from JAX
needs Apple's `jax-metal` plugin, and
[its package index page](https://pypi.org/project/jax-metal/), checked today,
still shows version 0.1.1 released on 8 October 2024 and nothing since — now
almost two years without a release. Read "runs on Apple Silicon" as "runs on the
Apple Silicon processor".

One more nuance that the frontier document's "MuJoCo Warp: no" row hides.
`warp-lang`, NVIDIA's Warp itself, does publish a `macosx_11_0_arm64` wheel, so
the library installs on a Mac. What it has there is a processor device and no
graphics device. So Warp-based code will import and may run; it will not be fast,
and anything that asks for a CUDA device will fail at that point rather than at
install time.

### 2.6 The numbers that are actually measured

Most Apple Silicon claims in robotics are guesses. Four are not, and they are
worth carrying because they bound the argument in both directions.

Read this table as: what was measured, on what machine, and what the figure
tells you.

| Measurement | Machine | Figure | Source |
| --- | --- | --- | --- |
| Depth Anything V2 Small, float16, through CoreML | MacBook Pro, M3 Max | 24.58 ms per image, Neural Engine dominant | [Apple's model card](https://huggingface.co/apple/coreml-depth-anything-v2-small) |
| the same model | MacBook Pro, M1 Max | 32.80 ms per image | the same card |
| MuJoCo on the processor, one humanoid | Apple M3 Max | 650,000 physics steps per second | [the MJX page](https://mujoco.readthedocs.io/en/stable/mjx.html) |
| MJX-JAX, one humanoid, batch size 8192 | NVIDIA A100 | 950,000 physics steps per second | the same page |

Put the last two side by side and the result is startling enough that it is worth
saying in a sentence. **On a single humanoid scene, a laptop's central processor
reached two-thirds of the throughput of a data-centre graphics card running 8,192
copies in parallel.** The same page shows the advantage reversing as the number of
bodies rises, because accelerators handle branching badly and collision detection
branches constantly. That is the shape of the whole argument in this document:
one scene at a time is fine here, and thousands at once is not.

The first two rows say the other useful thing. A depth model running in 25
milliseconds on the Neural Engine is a 40 Hz perception loop on a laptop. The
work that made that possible was somebody exporting the model to CoreML, not any
property of the model itself.

## 3. The pattern that rescues most of it

This is the single most useful fact in this document, and it is why the perception
area's position is so much better than the gripping area's.

**A great many models whose own repository requires a compiled CUDA kernel have a
pure-PyTorch reimplementation in Hugging Face `transformers` that does not.**
`transformers` is a library of model implementations rewritten to a common
interface. Because it has to run everywhere the library runs, the rewrite
generally has no compiled extensions at all: it is Python calling PyTorch
operations, and PyTorch operations exist for the Mac's graphics processor.

So "the repository needs CUDA" and "it will not run on your Mac" are different
statements, and the second is often false.

### 3.1 Verifying that it still holds

The claim was checked today against the library's own source on its main branch,
not against its documentation.

Deformable DETR is the informative case, because it is the model the original
pattern was named after, and the mechanism has changed since the perception
document was written. The `transformers` implementation defines its attention as
an ordinary PyTorch function built on `nn.functional.grid_sample`, and decorates
the module with `use_kernel_forward_from_hub("MultiScaleDeformableAttention")`.
That decorator is an opt-in acceleration: when a separate `kernels` package is
installed and a compiled kernel is available for the hardware, the fast path is
substituted, and otherwise the decorator returns the class unchanged. The default
is the pure PyTorch path.

This is a better arrangement than the one the perception document describes, which
was a fallback when a CUDA kernel was missing. The plain path is now the plain
path, and the kernel is the exception. Grounding DINO, Mask2Former, OneFormer,
RF-DETR and SAM 3 were each checked the same way, and none of them references a
compiled extension at all.

### 3.2 The current list

`transformers` 5.17.0 was released on 9 September 2026. Its model directory,
listed today, contains 521 model implementations. These are the ones that matter
for robot perception, grouped by what they do. Read the list as: if you wanted
this capability and the original repository refused to install, look here first.

**Segmentation and tracking.** `sam`, `sam2`, `sam2_video`, `sam3`, `sam3_video`,
`sam3_tracker`, `sam3_tracker_video`, `sam3_lite_text`, `sam_hq`, `edgetam`,
`edgetam_video`, `mask2former`, `maskformer`, `oneformer`, `segformer`,
`eomt_dinov3`.

**Detection, including from a text phrase.** `detr`, `deformable_detr`,
`conditional_detr`, `dab_detr`, `rt_detr`, `rt_detr_v2`, `d_fine`, `deimv2`,
`rf_detr`, `lw_detr`, `yolos`, `grounding_dino`, `mm_grounding_dino`, `owlvit`,
`owlv2`.

**Depth.** `depth_anything`, `prompt_depth_anything`, `depth_pro`, `zoedepth`.

**Backbones and features.** `dinov2`, `dinov2_with_registers`, `dinov3_vit`,
`dinov3_convnext`, `superpoint`, `vjepa2`.

That list has grown substantially since the perception document was written,
which recorded SAM 3 arriving in version 5.0.0. The whole SAM 3 family is now
present, including its tracker and its video heads, and `edgetam` has been added
alongside. RF-DETR, D-FINE and DEIM — the permissive detectors the perception
area recommends over the AGPL-licensed Ultralytics YOLO — are all in the library
now, which they were not.

### 3.3 What the pattern does not rescue

Three limits, so that this is not read as a universal escape.

The reimplementation is not always faithful. A port is a rewrite, and a rewrite
can differ from the original in postprocessing, in default thresholds, or in
which checkpoint it expects. If you are reproducing a published number, check
against the original; if you are building a system, the port is what you want.

The pattern is a perception phenomenon. There is no equivalent library for
grasping or for motion planning. The grasp models in
[the gripping area's table](../07_gripping/07_licences-and-platforms.md#43-the-grasp-models-with-their-licences)
have no portable reimplementations, which is exactly why that area's answer is so
much worse.

And a licence is not a platform. A model that installs and runs on your Mac may
still be non-commercial, or have no licence at all. The three area documents
carry those findings and this one deliberately does not repeat them.

## 4. What is genuinely impossible, and why

Four things are closed, and it is worth knowing the reason for each rather than
just the name, because the reasons predict which new arrival will also be closed.

### 4.1 NVIDIA Isaac ROS

Isaac ROS is NVIDIA's collection of CUDA-accelerated ROS 2 packages: stereo
depth, visual odometry, detection, pose estimation, and the cuMotion planner.

The reason it is closed is stated in
[its own getting-started page](https://nvidia-isaac-ros.github.io/getting_started/index.html),
read today. The supported platforms are exactly three: a Jetson Thor or Jetson
Orin running JetPack 7.2; an `x86_64` machine with an "Ampere or higher NVIDIA GPU
Architecture with 8 GB RAM or higher" running Ubuntu 24.04 with CUDA 13.2 or
later and driver 595 or later; or a DGX Spark. There is no macOS entry and no
processor-only path.

The deeper reason is architectural rather than a packaging choice. Every Isaac ROS
node passes data through `isaac_ros_nitros`, a zero-copy transport that hands
graphics memory between nodes without going back through the processor. The whole
performance argument for the collection is that transport. Removing CUDA would
remove the reason for the packages to exist.

The same page records something else worth noting: Isaac ROS now targets ROS 2
Lyrical. That is relevant to [section 5](#5-ros-2-on-apple-silicon-precisely).

### 4.2 Isaac Sim and Isaac Lab

Isaac Sim is NVIDIA's simulator and [Isaac Lab](https://github.com/isaac-sim/IsaacLab)
is the reinforcement learning framework built on it. Isaac Lab is the most widely
used robot learning framework in the world, so its absence is felt.

The reason is the renderer as much as the physics. Isaac Sim's requirements name
Ubuntu 22.04 or 24.04 and Windows 11, a GeForce RTX 4080 or equivalent with 16 GB
of video memory as a minimum, and state that cards without ray-tracing cores are
not supported — which excludes the A100 and H100, never mind a Mac. Ray-tracing
cores are fixed-function hardware for tracing light paths, and there is no
software path to them.

Isaac Lab 3.0, published in September 2026, separated physics, rendering and
visualisation into swappable backends and can now run some workflows without
launching Isaac Sim. That is a real loosening and it is covered in
[the frontier document](../15_frontier/04_simulation-and-evaluation.md#24-isaac-sim-and-isaac-lab).
It does not open a Mac path, because every available backend needs either Isaac
Sim or CUDA.

### 4.3 cuRobo and TensorRT

These two are closed for the plainest reason of all: they are CUDA programs. The
acceleration is not a feature of the library; it is the library.

[cuRobo](https://github.com/NVlabs/curobo) is NVIDIA's motion generation library —
inverse kinematics, collision checking and trajectory optimisation, all written as
graphics-card kernels. Its licence file is Apache-2.0, read today through the
GitHub licence interface, which surprises people who expect NVIDIA research code
to be restricted. Permissive and unusable are independent properties. Its README
now describes cuRoboV2 as "a significant rewrite" with a changed public interface
and tells users of the old interface to pin the `v0.7.8` tag; the platform
position is unchanged either way.

TensorRT is NVIDIA's inference compiler. It takes a trained network and produces
an engine specialised to one card. Its
[support matrix](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/support-matrix.html),
read today, offers exactly four kinds of platform: Ubuntu 20.04 through 26.04,
Windows 10 and 11, JetPack, and server-class Arm. There is no macOS option in the
list. The output is also specific to the card it was built for, so there would be
nothing portable to move even if the compiler ran here.

The Mac equivalent of TensorRT is CoreML, and the comparison is covered in
[section 6.3](#63-use-coreml-or-mlx-where-an-export-exists).

### 4.4 A hand-written kernel with no fallback

This is the general case, and the one to learn to recognise, because it is what
closes individual models rather than whole product lines.

A kernel here means a function written in CUDA C and compiled for NVIDIA
hardware. Somebody writes one when the operation they need is not expressible
efficiently as standard array operations. Sparse convolution, the deformable
attention in the DETR family, and the point-cloud grouping operations in
`pointnet2` are all of this kind.

Two outcomes follow from one decision the author made. If they also wrote a plain
PyTorch version and fall back to it, the model runs anywhere, slowly. If they did
not, the model does not run anywhere but on an NVIDIA card. The authors of
`transformers` always write the plain version; research repositories usually do
not.

The named blockers, each fatal on its own, checked against the package index
today:

| Blocker | What it is | Why it is fatal |
| --- | --- | --- |
| [MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine) | sparse convolution | no macOS wheel; compiles with `nvcc`; last pushed March 2024 |
| `pointnet2` custom operators | point-cloud grouping and sampling | not a package at all; compiled by hand from a repository's own source |
| `spconv-cu120` | sparse convolution again | the name contains the CUDA version; no source archive, no macOS wheel |
| [`flash-attn`](https://pypi.org/project/flash-attn/) | a fast attention implementation | source archive only; the build needs `nvcc` |
| [`xformers`](https://pypi.org/project/xformers/) | memory-efficient attention | source archive only; the same |

### 4.5 Checking a new project in five minutes

The gripping document makes a point that generalises past gripping and is the
right habit to end this section on. **A clean requirements file is not evidence
that a project will install.** A requirements file that lists only `torch`,
`numpy` and `open3d` looks entirely portable, and the README two paragraphs later
may tell you to compile a `pointnet2` operator by hand. Dependency scanners do not
read prose.

So the check, in order, is: read the installation instructions rather than the
requirements file; search the repository for `nvcc`, `.cu` and `setup.py build_ext`;
look up each unfamiliar dependency on the package index and see whether it
publishes a macOS wheel; and only then try to install it.

## 5. ROS 2 on Apple Silicon, precisely

This section states the position exactly, because it is nowhere documented
plainly and the vague version — "ROS does not really work on a Mac" — is both
demoralising and wrong.

### 5.1 What REP 2000 says, and what it does not

REP 2000 is the ROS Enhancement Proposal that defines the target platforms for
every ROS 2 distribution. Each distribution gets a table whose rows are processor
architectures and whose columns are operating systems, and each cell holds a
support tier. Tier 1 means continuous integration runs on it and failures block a
release. Tier 3 means source builds only, with no guarantee.

[The document](https://github.com/ros-infrastructure/rep/blob/master/rep-2000.rst)
was fetched and read today. For Jazzy Jalisco, the `amd64` row gives macOS Tier 3
with source builds only, and the `arm64` row's macOS cell is **empty**. For Kilted
Kaiju, the table has the same shape and the same empty cell.

So the position is exact: **ROS 2 has no support tier of any kind for macOS on
`arm64`.** Not a weak tier. No tier. Official binaries are not built, source
builds are not tested, and nothing about an Apple Silicon Mac is anybody's
responsibility upstream. That confirms what both the perception and the movement
documents say.

There is a wrinkle the other documents do not have, and it should be corrected
there rather than repeated. **REP 2000 has no section for Lyrical Luth at all.**
Its last distribution section is Kilted Kaiju, and the file's most recent commit
was in July 2025. Lyrical is nonetheless a real, active distribution:
[rosdistro](https://github.com/ros/rosdistro), the index of ROS distributions,
lists `lyrical` with `distribution_status: active`, and NVIDIA's Isaac ROS
documentation states that its packages target ROS 2 Lyrical. The movement
document attributes its Lyrical dates to REP 2000, and REP 2000 does not carry
them. The distribution exists; the platform document has not caught up with it.

### 5.2 What RoboStack actually packages

[RoboStack](https://robostack.github.io/) is a community project that rebuilds
ROS 2 as conda packages. Conda is a package manager that installs compiled
binaries and their system libraries into a self-contained environment, which is
what makes this possible: RoboStack builds the whole dependency tree for
`osx-arm64` and ships it, so nothing is compiled on your machine.

**Why this rather than the obvious alternative.** The alternatives are building
ROS 2 from source on macOS, which is a multi-hour exercise against an untested
configuration that breaks on upgrades, and running Linux in a virtual machine,
which works and costs you direct access to the Mac's camera, its graphics
processor and its file system. RoboStack is one command and behaves like a normal
installation.

**What it costs you.** It is a community effort with no upstream guarantee, its
package set is smaller than a full Debian installation, and version numbers lag
the official release. If a package you need is missing there is no escalation
path.

The channel was queried today, package by package. Every one of these publishes an
`osx-arm64` build:

| Package | Version | What it gives you |
| --- | --- | --- |
| `ros-jazzy-desktop` | 0.11.0 | the base installation, including RViz |
| `ros-jazzy-moveit` | 2.12.4 | planning, inverse kinematics, collision checking, the planning scene |
| `ros-jazzy-moveit-py` | 2.12.4 | the Python interface to it |
| `ros-jazzy-moveit-servo` | 2.12.4 | real-time Cartesian and joint jogging |
| `ros-jazzy-moveit-task-constructor-core` | 0.1.5 | planning a task as stages |
| `ros-jazzy-pilz-industrial-motion-planner` | 2.12.4 | point-to-point, linear and circular motion |
| `ros-jazzy-ompl` | 2.0.1 | the sampling planners underneath MoveIt |
| `ros-jazzy-ros2-control` | 4.47.0 | the control loop and the hardware interface |
| `ros-jazzy-ros2-controllers` | 4.42.1 | trajectory, gripper and admittance controllers |
| `ros-jazzy-control-msgs` | 5.9.0 | the gripper command action types |
| `ros-jazzy-ur-robot-driver` | 3.8.0 | the Universal Robots driver |
| `ros-jazzy-octomap` | 1.10.0 | occupancy mapping for unknown obstacles |
| `ros-jazzy-rviz2` | 14.1.23 | visualisation |
| `ros-jazzy-ros-gz` | 1.0.23 | the bridge to Gazebo |
| `ros-jazzy-cv-bridge` | 4.1.0 | between ROS images and OpenCV |
| `ros-jazzy-image-pipeline` | 5.0.13 | rectification, calibration, stereo |
| `ros-jazzy-vision-msgs` | 4.1.1 | the standard detection message types |
| `ros-jazzy-perception-pcl` | 2.6.5 | the Point Cloud Library inside ROS |

That is a complete arm: perceive, plan, execute, visualise and simulate. It is
considerably more than the reputation suggests.

### 5.3 What RoboStack does not have

Three gaps found in the same sweep, two of which are not recorded anywhere else in
this repository.

`ros-jazzy-visp` and `ros-jazzy-vision-visp` do not exist in the channel at all.
The underlying library does: conda-forge publishes `visp` 3.7.0 with an
`osx-arm64` build. So visual servoing on a Mac means calling ViSP directly instead
of through ROS, and the GPL obligation described in
[the movement document's licence section](06_licences-and-platforms.md#12-visp-the-visual-servoing-library-is-gpl-20-or-later)
comes with it either way.

`ros-jazzy-realsense2-camera` publishes `linux-64` and `linux-aarch64` builds and
nothing else. The commonest depth camera has no ROS 2 driver package for Apple
Silicon.

`ros-jazzy-franka-description` has no build at all in the channel, for any
platform, so a Franka arm's description files have to come from the upstream
repository.

### 5.4 Which distribution to start on

Four distributions are currently listed as active in rosdistro: Humble Hawksbill,
Jazzy Jalisco, Kilted Kaiju and Lyrical Luth. RoboStack's channels were checked
directly today: `robostack-humble`, `robostack-jazzy`, `robostack-kilted` and
`robostack-noetic` all exist and all publish `osx-arm64`. There is **no
`robostack-lyrical` channel** — the request returns a 404.

That settles the question for a Mac. Jazzy is supported to May 2029 by REP 2000's
own table, it has the fullest RoboStack package set, and it is what this
repository uses. Kilted ends in November 2026, which is two months away. Lyrical
is the newest distribution and has no Apple Silicon redistribution at all yet, so
choosing it means choosing Linux.

## 6. The practical strategies, ranked

Ranked by how much they give you for how little they cost, best first.

### 6.1 Choose a simulator that runs natively

This is first because it is free and because the choice of simulator determines
more of your day-to-day experience than any other decision.

MuJoCo, Genesis World, Gazebo Jetty and robosuite all run natively; Genesis runs
its physics on the Mac's graphics processor. ManiSkill runs its physics on the
processor after a Vulkan install. Isaac Sim, Isaac Lab and MuJoCo Warp do not run
at all.

**Why this rather than the obvious alternative.** The obvious alternative is to
pick the simulator the paper you are reading used, which for manipulation
reinforcement learning is usually Isaac Lab, and then to rent a machine for every
experiment. That turns a five-second iteration into a ten-minute one, and the
cost of a slow loop compounds across a project in a way that a rental bill does
not.

**What it costs you.** You are not running the benchmark suites that only exist on
the other stack, and you will occasionally have to reimplement an environment
somebody else has already written. The frontier document's
[section on benchmarks](../15_frontier/04_simulation-and-evaluation.md#7-the-benchmarks-and-what-each-one-measures)
argues that those numbers are much less comparable than they look, which softens
the loss.

### 6.2 Do inference locally and training elsewhere

This is the division that makes almost everything workable, and it follows
directly from [section 1](#1-the-three-questions-people-conflate): inference needs
single-digit gigabytes and low latency, training needs tens of gigabytes and high
throughput. They want different machines.

In practice this means: write the code on the Mac, run the tests on the Mac, run
the policy on the Mac, and send the training run somewhere with a card. Datasets
and checkpoints move over the network, which is slow but happens once per run
rather than once per iteration.

LeRobot supports this arrangement well, which is why it is worth naming. Its
device selection, read from its source today, tries CUDA, then Metal, then Intel's
accelerator, then falls back to the processor with a warning. The same script runs
in both places. Its dependency declarations also show where the line sits: it pins
the LIBERO benchmark extra to `sys_platform == 'linux'`, and selects a macOS-specific
RealSense package on a Mac.

**What it costs you.** Two environments to keep in step, and the discipline never
to let the remote machine become the only place the code runs.

### 6.3 Use CoreML or MLX where an export exists

CoreML is Apple's model format and runtime. Converting a PyTorch model to it,
through [coremltools](https://github.com/apple/coremltools), lets the system place
the work on the Neural Engine, which is fixed-function hardware for neural network
arithmetic and is both faster and far more power-efficient than the graphics
processor for the models it suits.

The measured evidence for bothering is in
[section 2.6](#26-the-numbers-that-are-actually-measured): Depth Anything V2 Small
runs in 24.58 milliseconds on an M3 Max through CoreML with the Neural Engine
dominant. That is a usable perception rate on a laptop.

[MLX](https://github.com/ml-explore/mlx) is Apple's array framework for its own
hardware, written for unified memory, and it is the realistic way to run a large
vision-language model locally. [ONNX Runtime](https://github.com/microsoft/onnxruntime)
is the portable middle path: one exported file that runs on several backends,
including [a CoreML execution provider](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html).

**Why these rather than just using PyTorch with `mps`.** PyTorch on Metal is the
lowest-effort option and it works, but it uses only the graphics processor, not
the Neural Engine, and it carries the framework's overhead into every call. An
export is what buys the Neural Engine.

**What it costs you.** The export is work, and it is work you redo whenever the
model changes. Conversion frequently fails on a model with unusual control flow,
and the failure is a tooling error some way from the model's own code. Do this for
the two or three models that sit in a loop, not for everything.

There is also a structural advantage on the Mac's side that is easy to miss. A
Mac's memory is unified: the processor and the graphics processor address the same
pool. A 64 GB Mac can hold a model that no single consumer NVIDIA card can hold,
and will run it slowly rather than not at all. For inference on a large model, the
Mac's weakness is speed and its strength is capacity, which is the reverse of the
usual assumption.

### 6.4 Rent a machine by the hour

When training will not fit, rent. The prices below were read today from two
providers' own public pricing pages and are on-demand rates per graphics card per
hour, before tax. They are quoted to show the shape of the market rather than to
recommend a supplier, and they move.

Read the table as: the card, what it is useful for here, and the rate each
provider lists.

| Card | Memory | [RunPod](https://www.runpod.io/pricing), community / secure | [Lambda](https://lambda.ai/service/gpu-cloud), on demand |
| --- | --- | --- | --- |
| RTX A6000 | 48 GB | $0.33 / $0.53 | $1.09 |
| RTX 4090 | 24 GB | $0.34 / $0.74 | — |
| A40 | 48 GB | $0.35 / $0.49 | — |
| L40S | 48 GB | $0.79 / $1.09 | — |
| A100 PCIe | 80 GB on RunPod, 40 GB on Lambda | $1.19 / $1.59 | $1.99 |
| H100 PCIe | 80 GB | $1.99 / $2.89 | $3.29 |
| H100 SXM | 80 GB | $2.69 / $3.49 | $4.29 |

Now put those rates against the memory requirements from
[section 1.2](#12-can-i-train-it), which is the calculation that actually decides
things.

A LoRA fine-tune of a vision-language-action policy needs more than 22.5 GB. The
cheapest card in the table that clears that is an RTX A6000 at $0.33 an hour. An
overnight twelve-hour run therefore costs about four dollars. That is less than
the electricity, and it is the number that should stop anyone concluding they
cannot do this work on a Mac.

A full fine-tune needs more than 70 GB, so an H100 with 80 GB at $2.69 an hour. A
full day of that is about $65. Still not a barrier for one run; a real cost if
you need twenty.

**Why renting rather than the obvious alternative.** The obvious alternative is a
managed training service that hides the machine. Renting a bare machine keeps your
environment reproducible — the same container, the same package versions — and
that reproducibility is what makes a remote run debuggable from a laptop.

**What it costs you.** Setup time on every fresh machine unless you maintain an
image, data transfer in and out, and the running risk of leaving an instance
switched on. The community tier of any provider is cheaper because the hardware is
somebody's spare capacity and can be reclaimed, so checkpoint often.

### 6.5 Decide honestly when to buy a Linux box

There is a point at which renting is worse than owning, and it is worth being
honest about rather than defensive.

Buy when one of these is true. You need the NVIDIA stack itself — Isaac ROS,
Isaac Sim or Isaac Lab — because none of those has any path on a Mac or through
a rental that is pleasant to iterate on. You are training most days, so the rental
meter never stops. You need a real-time control loop against physical hardware
with a graphics-accelerated perception stage in it, where network latency to a
rented machine is disqualifying. Or you want ROS 2 at Tier 1, which means Ubuntu
Noble on `amd64` or `arm64` and nothing else.

The break-even is arithmetic you can do with your own numbers rather than one this
document can do for you, because hardware prices vary by region and by week. The
form is: divide the price of the machine by the hourly rate of the card you would
otherwise rent, and that is how many hours of rental it buys. At the community
rate for a 24 GB card in the table above, thirty-four cents an hour, a machine
costing two thousand of the same currency units buys roughly 5,900 hours of
rental, which is about eight months of continuous use. If your honest estimate of
usage is a few overnight runs a month, renting wins by a wide margin. If you would
keep a card busy most of the working day, owning wins within the year.

The one thing not to do is buy a machine because a tutorial assumed one. Work out
which of the three questions in [section 1](#1-the-three-questions-people-conflate)
is actually blocking you first. In this repository's experience the answer is
usually question three, installation, and question three is solved by finding the
reimplementation rather than by buying hardware.

## 7. When it does not matter

The last section, because it is the conclusion the rest of the document is
evidence for.

### 7.1 Where a Mac is not a handicap

For a single arm doing look-then-move on a scene with a handful of objects, a Mac
is a good development machine and occasionally a better one than a Linux box with
a card.

Concretely, all of this runs natively and at full speed: every geometric
calculation in perception and in grasp selection, because those are arithmetic on
small arrays; motion planning in MoveIt, because a plan is milliseconds of work;
trajectory execution and admittance control through `ros2_control`; single-scene
physics in MuJoCo, at 650,000 steps per second on an M3 Max; physics on the
graphics processor in Genesis World; simulation and sensor models in Gazebo Jetty;
classical vision in OpenCV and point-cloud work in Open3D; a CoreML-exported
perception model at 40 Hz; and a downloaded policy run for inference through
PyTorch on Metal.

That list is a complete arm. It perceives, it chooses a grip, it plans, it moves,
and it can be tested in simulation. Nothing in it is waiting on a graphics card.

### 7.2 Where the line is

The line is not about the size of the model. It is about whether your work is
dominated by latency or by throughput.

**Latency work is one thing at a time and you are waiting for it.** One image
segmented, one plan computed, one policy step. A Mac is good at this, because
low-latency single-stream work is what a laptop processor and a Neural Engine are
built for, and because the MJX figures show a laptop within striking distance of a
data-centre card on a single scene.

**Throughput work is many things at once and you are waiting for all of them.**
Thousands of parallel simulated environments for reinforcement learning. A
gradient step over a batch of two hundred and fifty demonstrations. A domain
randomisation sweep over a thousand friction values. A Mac loses these by one to
two orders of magnitude, and no amount of patience or cleverness closes that.

Three specific thresholds, from the verified numbers above, are where the line
actually falls:

| Threshold | Which side |
| --- | --- |
| more than one simulated environment at a time | you want a card, and above about a hundred you need one |
| more than roughly 22 GB of model state during training | you want a rented card; see [section 6.4](#64-rent-a-machine-by-the-hour) |
| anything in the NVIDIA Isaac stack, or built on a compiled CUDA kernel | you need a card, and no strategy substitutes |

Everything on the near side of those three lines is work you can do today, on the
machine you have, without renting anything.

---

The four documents this one indexes carry the per-area detail, the licences and
the comparison grids:
[perception](../06_object-perception/06_licences-and-platforms.md),
[gripping](../07_gripping/07_licences-and-platforms.md),
[movement](06_licences-and-platforms.md) and
[simulation](../15_frontier/04_simulation-and-evaluation.md).

Back to [the overview](01_overview.md).
