# Simulation, world models and evaluation: what happened in 2026

Almost everything in robot manipulation research is measured in a simulator, and
almost none of those measurements can be compared with each other. This document is
about both halves of that sentence. It covers the simulators people actually run, the
learned models that are starting to stand in for simulators, the work that made a
policy trained in simulation survive contact with a real arm, and the benchmarks the
field reports its progress on.

It answers one question in particular: **when a paper says a policy scored 95% on a
benchmark, what has been measured, and can you compare it with the 93% in the paper
next to it?** The short answer is usually no, and section 8 sets out the evidence.

This is written for somebody who has read the rest of this repository, works on an
Apple Silicon Mac with no NVIDIA graphics card, and wants to know which of these tools
they can actually run and which numbers they can actually trust. Every term is
explained where it first appears. No previous knowledge of any specific simulator is
assumed.

It is a companion to [what is changing in robot
manipulation](../10_one-arm-training/05_what-is-changing.md), which explains the
*mechanisms* behind change in this field. This document is the *events* document: what
specifically happened, when, and with what evidence. Where the two overlap, that one
has the reasoning and this one has the dates.

Everything here was checked against a live source in September 2026. Where a claim
could not be checked, the text says so.

## Contents

1. [How to read this document](#1-how-to-read-this-document)
2. [The simulators](#2-the-simulators)
3. [What runs on an Apple Silicon Mac](#3-what-runs-on-an-apple-silicon-mac)
4. [Learned world models](#4-learned-world-models)
5. [Sim-to-real: what actually closed the gap](#5-sim-to-real-what-actually-closed-the-gap)
6. [Synthetic data generation](#6-synthetic-data-generation)
7. [The benchmarks, and what each one measures](#7-the-benchmarks-and-what-each-one-measures)
8. [Why two numbers on the same benchmark are usually not comparable](#8-why-two-numbers-on-the-same-benchmark-are-usually-not-comparable)
9. [What is being done about evaluation](#9-what-is-being-done-about-evaluation)
10. [Everything that happened after May 2026, in one list](#10-everything-that-happened-after-may-2026-in-one-list)
11. [What to do with all this](#11-what-to-do-with-all-this)

---

## 1. How to read this document

### 1.1 The five questions asked of every development

Announcements in this field are written to sound like capabilities. Most of them are
not. Every substantial item below is therefore written up in the same five steps, in
the same order, and you should be suspicious of any description elsewhere that skips
one of them.

The first step is **what it was before**: the thing this replaced, stated concretely
enough that you could have used it. The second is **what changed**: the actual claim,
stated precisely rather than enthusiastically. The third is **how it was achieved**:
the mechanism that makes it faster, more accurate or more transferable, because a
claim with no mechanism behind it is a press release. The fourth is **why it
matters**: what becomes possible that was not. The fifth is **what it still cannot
do**, and that one is not optional.

### 1.2 The maturity labels

Every item carries one of five labels. They describe how close the thing is to being
something you could use this afternoon, and nothing else. They say nothing about
quality.

The labels run from most available to least. Read the table as a ladder: each row is
harder to get hold of than the one above it.

| Label | What it means |
| --- | --- |
| **Shipped** | You can obtain and run it today through the normal channel for that kind of thing. |
| **Downloadable** | Code or weights are published, with the licence named. You may still need hardware you do not have. |
| **Demonstrated** | It has been shown working on real hardware by its authors, but you cannot obtain it. |
| **Paper only** | There is a written description and results. There is no artefact. |
| **Announced** | Somebody said it exists. |

The distinction between **Downloadable** and **Demonstrated** is the one that matters
most in practice, and it is the one press coverage collapses most often.

### 1.3 Two words used throughout

A **simulator** here means a program that computes what happens when modelled rigid
and soft bodies push on each other, and draws a picture of the result. It contains a
**physics engine**, which does the computing, and a **renderer**, which does the
drawing. Those two parts are increasingly sold and swapped separately, and section 2.4
is largely about that separation.

A **policy** is the thing being evaluated: a function that takes camera images and the
arm's joint positions and returns the next arm command. A **vision-language-action
model**, abbreviated VLA, is a policy that also takes a written instruction as input.
Nearly every benchmark number quoted below is a success rate for some VLA.

## 2. The simulators

### 2.1 MuJoCo

MuJoCo, which stands for Multi-Joint dynamics with Contact, is the physics engine this
repository and most manipulation research now runs on. It is published by Google
DeepMind at [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) under
Apache-2.0, read from the repository's licence file. Its history — commercial software
until DeepMind bought it in 2021 and opened it in 2022 — is covered in [the mechanism
document](../10_one-arm-training/05_what-is-changing.md).

**What it was before.** Until the end of 2025, MuJoCo was a fast, accurate,
single-threaded rigid-body engine with a serviceable renderer, and its release
cadence was roughly one minor version a quarter. If you wanted thousands of
simulations in parallel you used something else.

**What changed.** MuJoCo shipped eleven releases between February and September
2026, versions 3.5.0 through 3.14.0, and several of them changed the physics rather
than the packaging. The dates and contents are in
[the changelog](https://mujoco.readthedocs.io/en/stable/changelog.html), which is
generated from the repository and is the source for every version number in this
section. Status: **Shipped**.

Four of those changes are worth knowing about individually.

Version 3.5.0, on 12 February 2026, added a **system identification toolbox** in
Python. System identification means fitting a simulator's parameters — masses,
friction coefficients, motor gains — to measurements taken from the real machine,
rather than guessing them. The same release added **delays**: actuators and sensors
can now be given an arbitrary lag, and sensors can be computed at intervals longer
than the simulation timestep. Both are discussed in section 5, because together they
are the largest single change to sim-to-real practice in the year.

Version 3.9.0, on 27 May 2026, redesigned what the contact parameters `margin` and
`gap` mean. The changelog says the redesign was for "conceptual clarity and
consistency with Newton". This is a small change with a large lesson attached, and
section 8.3 uses it.

Version 3.13.0, on 8 September 2026, added an integrator called `discrete`. An
**integrator** is the rule that advances the simulation one timestep. The `discrete`
integrator folds the constraint solve and the velocity update into a single operation,
so that spring stiffness and damping are handled implicitly — meaning the solver
accounts for where the spring will be at the end of the step rather than where it was
at the start. The practical consequence is stated in the changelog: passive springs
and actuator position gains become "stable at timesteps far beyond the explicit
stability limit". A stiff position-controlled servo used to force a tiny timestep, and
now does not.

Version 3.14.0, on 22 September 2026 — the day before this was written — added an
experimental contact mode called `ipc`, for penetration-free contact on deformable
meshes. Every position update is checked to be intersection-free by continuous
collision detection, which means the simulator tests the whole swept path between two
timesteps rather than the endpoints, so a fast-moving thin object cannot pass through
a surface between frames.

**How it was achieved.** The `discrete` integrator works by solving in an effective
mass matrix that already contains the damping and stiffness terms, so the stiffness
no longer sets the stability limit on the timestep. The `ipc` mode works by
minimising an incremental potential subject to linearised contact constraints. Both
are established ideas from computer graphics arriving in a robotics engine.

**Why it matters.** Contact-rich manipulation is where simulators have always been
weakest, and two of these four changes attack exactly that. Cloth, cable and soft
objects have been effectively untrustworthy in MuJoCo; `ipc` is the first mechanism
that makes non-penetration a guarantee rather than a hope.

**What it still cannot do.** The changelog is unusually honest about the limits, and
they are severe. The contacts that `ipc` resolves "are frictionless", which rules
out most grasping. It "keeps contact multipliers across steps that no state
specification covers", so `mj_getState` and `mj_setState` do not capture the full
state and "exact replay is not supported" — meaning a run cannot be reproduced
exactly, which is disqualifying for evaluation. And none of this touches the
deeper problem named in
[what simulation will not tell you](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you):
friction and softness numbers in a model are plausible, not measured.

### 2.2 MuJoCo Warp and MJX, and the parallel-simulation question

**What it was before.** Running thousands of simulations at once on a graphics card
required either NVIDIA's Isaac Gym, which was discontinued, or MJX, a
re-implementation of MuJoCo in JAX. JAX is a numerical library that compiles Python
to run on graphics cards and tensor processing units. MJX worked but was slow on
scenes with many contacts, because collision detection involves a lot of branching
and branching is what graphics cards are worst at.

**What changed.** MuJoCo Warp, at
[google-deepmind/mujoco_warp](https://github.com/google-deepmind/mujoco_warp)
(Apache-2.0), was officially released in MuJoCo 3.5.0 on 12 February 2026, and now
ships a version tagged in lockstep with MuJoCo itself — v3.14.0 on 22 September
2026. It is a second implementation of the MuJoCo physics pipeline written in
NVIDIA Warp, a Python framework that compiles kernels for CUDA. The umbrella
package MJX now covers both: [the MJX documentation](https://mujoco.readthedocs.io/en/stable/mjx.html)
distinguishes MJX-JAX, which "runs on: Nvidia and AMD GPUs, Apple Silicon, and
Google Cloud TPUs", from MJX-Warp, which "optimizes performance specifically for
NVIDIA GPUs". Status: **Shipped**.

**How it was achieved.** Warp compiles to CUDA directly rather than going through
XLA, the compiler JAX uses, which lets the authors hand-write the branchy parts of
collision detection instead of expressing them as array operations. The measured
effect, from the MJX documentation's own table, is 3.35M physics steps per second
on a humanoid scene in pure Warp against 2.96M through the JAX foreign-function
interface. The documentation does not say which graphics card produced those
numbers, which is worth noticing in a document about unsourced numbers.

**Why it matters.** Reinforcement learning in simulation needs billions of steps,
and the throughput is what decides whether a training run takes a day or a month.
It also matters politically: NVIDIA's own Isaac Lab now offers MuJoCo Warp as a
physics backend, which is covered in section 2.4.

**What it still cannot do.** MJX-Warp needs an NVIDIA card. MJX-JAX does not, but
the documentation is blunt that "for a single scene, MJX-JAX can be 10x slower than
MuJoCo", and it has hard limits on mesh complexity: a convex decomposition should
have "roughly 200 vertices or less", and for convex-convex collisions "roughly fewer
than 32 vertices". A detailed gripper mesh does not fit in that budget without
simplification, and simplifying a gripper mesh changes where it touches things.

### 2.3 Newton

**What it was before.** Every research group that wanted to mix rigid bodies with
cloth, granular material or soft tissue wrote its own coupling code, usually on top
of `warp.sim`, a module NVIDIA has since deprecated.

**What changed.** [Newton](https://github.com/newton-physics/newton) reached version
1.0.0 — dated 10 March 2026 in its changelog, with the GitHub release published on
13 April 2026 — and was at 1.6.0 by 10 September 2026. Its README describes it as "a
GPU-accelerated physics simulation engine built upon NVIDIA Warp, specifically
targeting roboticists and simulation researchers", says it "was initiated by Disney
Research, Google DeepMind, and NVIDIA", and states that it is now "a Linux
Foundation project that is community-built and maintained". Code is Apache-2.0 and
the documentation is CC-BY-4.0, both read from the README. Status: **Shipped**.

**How it was achieved.** Newton is a container rather than a new solver. It
"extends and generalizes Warp's deprecated `warp.sim` module, and integrates MuJoCo
Warp as its primary backend". The engineering content is in the couplings — rigid
bodies against deformables, particles and material-point-method solvers — and in a
shared asset and sensor layer so that several solvers can operate on one scene.

**Why it matters.** Three organisations that would normally each build their own
simulator built one together and gave it to a foundation. Whatever else that is, it
is a strong signal about where the maintained code will be in three years.

**What it still cannot do.** It does not run on a graphics card unless that card is
made by NVIDIA. The README's requirements are exact: "OS: Linux (x86-64, aarch64),
Windows (x86-64), or macOS (CPU only)" and "GPU: NVIDIA GPU (Maxwell or newer),
driver 545 or newer (CUDA 12)". On an Apple Silicon Mac you get the central
processor and nothing else. Newton is also young: seven minor versions in six
months means the interface is still moving under you.

### 2.4 Isaac Sim and Isaac Lab

**What it was before.** NVIDIA's robot learning stack was a single tall column. To
train a policy you installed Isaac Sim, a large application built on the Omniverse
Kit platform, and then Isaac Lab on top of it, and you used NVIDIA's PhysX physics
and NVIDIA's ray-traced renderer because those were what the column contained.

**What changed.** Isaac Lab 3.0 Early Access was published on 16 September 2026 at
[isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) (BSD-3-Clause). Its
release notes describe "one task API across multiple physics, rendering, and
visualization backends; kit-less execution; Warp-native data paths". In plain terms:
the column came apart. Physics, rendering and visualisation are now three separate
choices, selected at the command line, and the release notes list `newton_mjwarp` as
a physics backend alongside NVIDIA's own PhysX. "Many Isaac Lab workflows can now
run without installing or launching Isaac Sim." It is built for Isaac Sim 6.1,
Python 3.12, PyTorch 2.11, NVIDIA Warp 1.16 and Newton 1.5.2, and general
availability is "targeted toward the end of October 2026". Status: **Downloadable**,
as an early-access branch under BSD-3-Clause.

**How it was achieved.** A factory pattern: common asset, sensor and scene interfaces
dispatch to whichever implementation was selected. Underneath, simulation data moved
to a type called `ProxyArray` that exposes the same buffer as either a Warp array or
a PyTorch tensor with no copy, which is what makes swapping the physics engine cheap
rather than a rewrite.

**Why it matters.** The most-used robot learning framework in the world can now run
DeepMind's physics engine instead of NVIDIA's, and can run at all without NVIDIA's
simulator application. That is a real reduction in how much you must adopt to use
any of it.

**What it still cannot do.** It cannot run on your Mac, and this is not a detail
that might change. [The Isaac Sim requirements
page](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)
lists Ubuntu 22.04 or 24.04 and Windows 11, a GeForce RTX 4080 or equivalent with
16GB of video memory as the minimum, and states that "GPUs without RT Cores (A100,
H100) are not supported". There is no macOS entry at all. Nor is Isaac Sim as open
as the Apache-2.0 badge on [its repository](https://github.com/isaac-sim/IsaacSim)
suggests: the licence file itself says that "Building or using the software requires
additional components licenced under other terms", naming the Omniverse Kit software
development kit and the 3D models and textures. Read the licence file, not the badge.

Isaac Lab 3.0 also breaks compatibility in a way worth flagging, because it will
silently corrupt results rather than crash. Quaternions — the four numbers that
represent a rotation — changed order from `(w, x, y, z)` in version 2.x to `(x, y, z,
w)` in 3.0, so the identity rotation changed from `(1, 0, 0, 0)` to `(0, 0, 0, 1)`.
Any hard-coded rotation carried across from a 2.x project is now wrong.

### 2.5 Genesis World

**What it was before.** Genesis appeared in December 2024 with very large speed
claims and a generative component that was announced rather than released. It was
built on Taichi, a Python compiler for parallel kernels, which stopped being
maintained.

**What changed.** The project renamed itself Genesis World, released version 1.0.0
on 27 May 2026, and was at 1.4.2 on 23 September 2026. The repository is now
[Genesis-Embodied-AI/genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world)
(Apache-2.0). Its README describes a platform that "combines a unified multi-physics
engine, a photo-realistic renderer (Nyx), and a cross-platform compiler (Quadrants)".
Status: **Shipped**.

**How it was achieved.** The interesting part is the compiler. Genesis forked Taichi
in June 2025 and renamed the fork [Quadrants](https://github.com/Genesis-Embodied-AI/quadrants)
(Apache-2.0), whose README states plainly that "the original Taichi is no longer
being maintained" and lists its own targets: "NVIDIA GPUs (CUDA)", "Vulkan-compatible
GPUs (SPIR-V)", "Apple Metal GPUs", "AMD GPUs (ROCm HIP)", and "x86 and ARM64 CPUs".
Metal is Apple's graphics and compute interface. Because the physics is written once
in Quadrants and compiled per platform, Genesis gets Apple Silicon support as a
consequence of its compiler rather than as a port.

The 1.0.0 release notes add "robust non-convex multi-contact collision detection" and
state that the rigid solver "should now be up to 35% for contact-reach scenes with
about 64 dofs", where dofs means degrees of freedom. The sentence is missing a word in
the original; read as written it claims up to 35% faster, under that one condition.

**Why it matters.** It is the only physics engine in this document that runs its
simulation on the graphics processor of an Apple Silicon Mac. Section 3 gives the support
table.

**What it still cannot do.** The original Genesis publicity involved throughput
claims that were widely disputed at the time, and the current documentation makes no
comparable claim — the README says only that the platform is "designed to scale from
a single laptop kernel to datacenter-grade GPUs". Treat any speed comparison you
find for Genesis, in either direction, as unverified unless you ran it. The
generative world-model component announced in 2024 is still not in the repository;
what shipped is a physics engine and a renderer.

### 2.6 The ones that did not move much

Three more simulators appear constantly in papers and all three are in a steadier
state. Each entry says what it is for and what its platform situation is.

[ManiSkill](https://github.com/mani-skill/ManiSkill) (Apache-2.0) reached a stable
3.0.1 on 21 April 2026 after roughly twenty-two beta releases, which is itself
informative about how long "version 3" had been quoted in papers before it existed. It
is the environment suite SimplerEnv is built on, and a usual home for
graphics-card-parallel manipulation environments outside the NVIDIA and MuJoCo stacks.
[Its installation
page](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html)
says: "We currently best support Linux based systems. There is limited support for
windows and no support for MacOS at the moment." Status: **Shipped**.

[robosuite](https://github.com/ARISE-Initiative/robosuite) (MIT, read from its licence
file) is the MuJoCo-based framework that LIBERO and RoboCasa are both built on. Its
last release was 1.5.2 on 24 December 2025. It is not abandoned — there were commits
in July 2026 — but it is stable rather than moving. Status: **Shipped**.

Gazebo, which this repository uses for camera work, is on the Jetty long-term support
release, supported from September 2025 to May 2031. It installs on macOS through
Homebrew with `brew install gz-jetty`, and [the macOS install
page](https://gazebosim.org/docs/latest/install_osx/) says the binaries are built for
Ventura and Sonoma. Status: **Shipped**.

## 3. What runs on an Apple Silicon Mac

This is the section a reader of this repository should read first, because several of
the headline simulators do not run on a Mac at all and finding that out after two days
of setup is an avoidable waste.

Read the table one row at a time: the second column is what you can do with no NVIDIA
card present, and the third gives the source for that claim. "CPU" means the
simulation runs on the Mac's central processor, which works and is slower. "Metal"
means it runs on the Mac's own graphics processor.

| Tool | On an Apple Silicon Mac | Where that comes from |
| --- | --- | --- |
| MuJoCo | Full support, native universal binaries | shipped Mac wheels and the `mjpython` launcher |
| MJX-JAX | Runs, effectively on the CPU | the MJX page lists Apple Silicon; see the caveat below |
| MuJoCo Warp | No | NVIDIA Warp compiles to CUDA |
| MuJoCo Playground | Installs, but its own instructions assume CUDA | its README installs `jax[cuda12]` |
| Newton | CPU only | README: "macOS (CPU only)" |
| Isaac Sim | No | requirements list only Ubuntu and Windows 11 |
| Isaac Lab | No | no macOS in its docs; every backend needs Isaac Sim or CUDA |
| Isaac Lab Arena | No | its LeRobot page requires "Linux (Ubuntu 22.04 / 24.04)" |
| Genesis World | Yes, including simulation on the Metal GPU | its support table, quoted below |
| ManiSkill | CPU simulation and rendering only | "no support for MacOS at the moment" |
| Gazebo Jetty | Yes, via Homebrew | the macOS install page |
| robosuite | Yes, it is MuJoCo underneath | MuJoCo's own Mac support |
| LIBERO through LeRobot | No | the LeRobot page requires `sys_platform == 'linux'` |
| BEHAVIOR-1K | No | OmniGibson runs on Isaac Sim |

Three of those rows deserve more than a line.

**Genesis World is the surprise, and it is real.**
[Its installation page](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html)
carries a support table whose macOS row is ticked for GPU simulation, CPU
simulation, interactive viewer and headless rendering alike. It is the only entry in
this document that gives a Mac owner graphics-processor physics. The mechanism is the
Quadrants compiler described in section 2.5, and because it is a compiler target
rather than a special case, it is more likely to keep working than a port would be.

**The MJX-JAX row needs a caveat that the documentation does not give.** The MJX page
says MJX-JAX "runs on: Nvidia and AMD GPUs, Apple Silicon, and Google Cloud TPUs".
JAX itself runs perfectly well on a Mac's processor. Using the Mac's *graphics*
processor from JAX requires Apple's `jax-metal` plugin, and
[its PyPI page](https://pypi.org/project/jax-metal/) shows the most recent release as
version 0.1.1 on 8 October 2024 — no release in nearly two years. Read "runs on Apple
Silicon" as "runs on the Apple Silicon CPU", and plan accordingly.

**The consolation is larger than it sounds.** The MJX documentation times a single
humanoid on four machines and publishes the figures: 650,000 physics steps per second
for CPU MuJoCo on an Apple M3 Max, 1.8 million for CPU MuJoCo on a 64-core AMD 3995WX,
950,000 for MJX-JAX on an NVIDIA A100 at a batch size of 8192, and 2.7 million for an
eight-chip v5 tensor processing unit at a batch size of 16384. A laptop beat the A100
on this scene. That result does not generalise — the same page shows MJX throughput
falling away faster than MuJoCo's as the number of humanoids rises, because accelerators
handle branching badly and collision detection branches — but for the single-arm,
single-scene work this repository is about, a Mac is not the handicap it appears to be.
The handicap arrives when you want ten thousand arms at once.

## 4. Learned world models

### 4.1 What a world model is, and why anyone wants one

A **world model** is a neural network trained to predict what the next observations
will be, given the current ones and an action. You can then plan or train inside the
prediction instead of inside a hand-built simulator.

The attraction is entirely about data. Building a simulated kitchen requires somebody
to model a kitchen. Training a world model requires video, and video of people doing
things is effectively unlimited. If the binding constraint on robot learning is the
number of action-labelled robot demonstrations — and the evidence in [the mechanism
document](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
is that it is — then a model that learns physics from unlabelled video is attacking
the constraint directly.

That is the promise. What follows is what exists.

### 4.2 Genie: the closed frontier

**What it was before.** Video generation models produced clips. They did not respond
to a control input, so there was nothing to act in.

**What changed.** Google DeepMind's Genie line produces interactive worlds that
respond to navigation input in real time.
[The Genie model page](https://deepmind.google/models/genie/) describes access
through "Project Genie", which it calls "an experimental research prototype that lets
you create and explore infinitely diverse worlds". Status: **Announced** for
robotics purposes. There are no weights, there is no interface a robot could act
through, and the page describes exploration rather than manipulation.

**How it was achieved.** Not disclosed in any detail that would let anyone reproduce
it.

**Why it matters.** It establishes that real-time, controllable, visually coherent
world generation is possible at all, which two years ago was not obvious.

**What it still cannot do.** Everything a robot needs. It has no contact model you can
read, no forces, no way to attach a gripper, and no published evaluation on any
manipulation benchmark. It belongs in this document as evidence about the direction of
travel, not as a tool. It is also the clearest current example of the pattern named in
[the mechanism document](../10_one-arm-training/05_what-is-changing.md): the frontier
of this field is increasingly announced rather than released.

### 4.3 Cosmos

**What it was before.** Turning a simulated scene into a photorealistic one meant
building better assets and better lighting by hand, which is slow, skilled work.

**What changed.** NVIDIA publishes the Cosmos family openly. The two that matter here
are [cosmos-predict2.5](https://github.com/nvidia-cosmos/cosmos-predict2.5), which
predicts future video, and
[cosmos-transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5), which
"produces high-quality world simulations conditioned on multiple spatial control
inputs" — in practice, taking a crude simulated render plus depth and segmentation
maps and producing a photorealistic video of the same scene. A third,
`cosmos-reason2`, is a model that reasons about physical plausibility rather than
generating video. Status: **Downloadable**, with a licence split that matters: the
README states that "NVIDIA Cosmos source code is released under the Apache 2 License"
while "NVIDIA Cosmos models are released under the NVIDIA Open Model License". The
code licence is not the model licence. Check the model licence before shipping
anything.

**How it was achieved.** Conditioning a video diffusion model on spatial control
signals that a simulator can produce for free, which is the same trick that
image-generation models use for pose control, applied to a rendering pipeline.

**Why it matters.** It addresses the specific failure named in
[what simulation will not tell you](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you):
segmentation and detection are easier in simulation than they have any right to be,
because simulated images have clean lighting and no sensor noise. Transferring the
appearance without transferring the physics is a targeted fix for a targeted problem.

**What it still cannot do.** It does not fix physics, only pictures. A policy trained
on Cosmos-transferred images still learned its contact behaviour from the underlying
simulator, with that simulator's guessed friction. It also needs substantial NVIDIA
hardware to run, which puts it out of reach on a Mac.

### 4.4 World models that actually shipped, inside policies

This is the development I did not expect, and it is the answer to the question of
whether any world model is usable rather than merely impressive.

**What it was before.** World models in robotics were a research category. You read
about them; you did not install them. As of mid-2026 they were a first-class category
in LeRobot with nothing production-ready in it.

**What changed.** [LeRobot v0.6.0](https://huggingface.co/blog/lerobot-release-v060),
released on 6 July 2026 under Apache-2.0 and titled "Imagine, Evaluate, Improve",
shipped three world-model policies you can install with `pip`. They are
[VLA-JEPA](https://huggingface.co/docs/lerobot/vla_jepa), which pairs a Qwen3-VL
language backbone with Meta's [V-JEPA 2](https://github.com/facebookresearch/vjepa2)
video model (MIT) and a flow-matching action head; LingBot-VA, which predicts future
video and actions together in chunks; and
[FastWAM](https://huggingface.co/docs/lerobot/fastwam), which pairs a roughly
five-billion-parameter video-generation model with a compact action model. Status:
**Downloadable** under Apache-2.0, on hardware with an NVIDIA card.

**How it was achieved.** Here is the mechanism, and it is the part worth carrying
away. In both VLA-JEPA and FastWAM the world model is a *training-time* component and
is thrown away afterwards. VLA-JEPA's documentation states it directly: during
training, "the world model predictor uses the action tokens extracted from Qwen to
predict future V-JEPA2 frame embeddings; a regression loss on those predictions is
added to the action loss", and at inference "only Qwen + the action head are used.
The world model is not needed at inference time." FastWAM's page says the same thing
in different words: it "keeps video modeling during training, but uses direct action
prediction at inference time instead of iteratively generating future observations."

**Why it matters.** The world model is being used as a *supervision signal*, not as a
simulator. Predicting the next frame forces the network's internal representation to
encode what actions do to the scene, and that representation is what the action head
then reads. This is a much weaker claim than "the robot plans inside an imagined
world", and it is a much more achievable one, which is presumably why it is the
version that shipped.

**What it still cannot do.** It cannot plan. Nothing in these three policies searches
over imagined futures or rejects an action because the prediction looked bad. A world
model good enough to plan through would have to be accurate about contact, and no
published evidence says any of them are. There is also no published head-to-head
result showing these three beating a policy trained without the auxiliary loss on a
benchmark with confidence intervals, which by the standard of section 8 means the
benefit is not yet established.

### 4.5 One more, for the record

NVIDIA's [GR00T-Dreams](https://github.com/NVIDIA/GR00T-Dreams) (Apache-2.0) uses a
video world model to generate synthetic robot trajectories rather than to control
anything. Its last commit was in October 2025, so it is a reference implementation
rather than a live project. A newer application of the same idea, Cosmos-H-Dreams for
surgical robotics, was [described on the Hugging Face blog on 27 July
2026](https://huggingface.co/blog/nvidia/cosmos-h-dreams). Status: **Downloadable**
for GR00T-Dreams; **Demonstrated** for the surgical work.

## 5. Sim-to-real: what actually closed the gap

### 5.1 The honest summary

The phrase "sim-to-real gap" covers three different problems that get confused with
each other. Separating them is most of the value in this section.

The **appearance gap** is that simulated images do not look like real ones. This is
the one that generative rendering and domain randomisation address, and it is the one
closest to being solved.

The **dynamics gap** is that the simulated arm does not move like the real arm,
because the masses, frictions, motor gains and communication delays in the model are
guesses. This is the one that got a real answer in 2026.

The **contact gap** is that the simulated fingers do not touch things like real
fingers do. This one has not been solved and there is no current claim that it has.

### 5.2 Measuring the robot instead of randomising over it

**What it was before.** The standard method was domain randomisation: randomise the
simulator's physical parameters over a wide range during training, so the policy learns
something that works across the whole range and therefore, with luck, on the real
machine somewhere inside it. It works. It also wastes capacity learning to cope with
machines that do not exist, and the width of the randomisation range is a hyperparameter
nobody can set from first principles.

**What changed.** MuJoCo 3.5.0, on 12 February 2026, shipped a system identification
toolbox in the main Python package, with a Colab notebook. Fitting the simulator's
parameters to measurements from your actual arm went from a research exercise to a
documented feature of the standard install. Status: **Shipped** under Apache-2.0.

**How it was achieved.** The toolbox fits model parameters to recorded trajectories.
The same release added the second half of what this needs: actuators and sensors can
now carry arbitrary delays through history buffers, and sensors can be sampled at
intervals longer than the physics timestep. A real robot's control loop has latency and
its sensors run slower than any simulation timestep, and until 3.5.0 expressing that in
MuJoCo meant writing it yourself.

**Why it matters.** Latency is the single most under-modelled property of a real robot
and the one that most often turns a policy that works in simulation into one that
oscillates on hardware. Making delay a first-class model property, next to a toolbox
that fits the rest of the parameters from data, moves the default practice from "randomise
over your ignorance" to "measure, then randomise over what is left". That is a better
default.

**What it still cannot do.** System identification fits the parameters of the model you
have. It cannot fit a phenomenon your model has no term for, and contact is full of
those: gear backlash, cable stiffness that changes with temperature, the way a rubber
pad's grip depends on how long it has been pressed. A perfectly identified rigid-body
model of a gripper is still a rigid-body model of a gripper.

### 5.3 Real-to-sim: rebuilding the room instead of modelling it

**What it was before.** Building a simulated version of your actual workspace meant
somebody measuring it and making meshes. For a benchmark it was done once, carefully,
by the benchmark's authors. For your own bench it was usually not done at all.

**What changed.** Reconstructing a usable simulation scene from a phone scan, or from a
single image, became a recurring published result through 2026. Representative examples
are [RoboSnap](https://arxiv.org/abs/2607.06699), on one-shot real-to-sim scene
generation from July 2026, and [ReVeal](https://arxiv.org/abs/2609.23910), from
September 2026, which applies the idea specifically to evaluating VLA policies. Status:
**Paper only** for most of this family — check each repository individually, because
release practice in this corner is poor.

**How it was achieved.** Three-dimensional Gaussian splatting, a reconstruction method
that represents a scene as a large collection of translucent blobs rather than as
triangles, produces photorealistic novel views from ordinary photographs far faster than
earlier neural reconstruction methods. Pairing that appearance with collision geometry
fitted to the same scan gives something a physics engine can use.

**Why it matters.** It attacks the appearance gap and the scene-building cost together,
and it does so per-user rather than per-benchmark. If evaluating a policy in a
reconstruction of your own bench becomes routine, the comparability problem in section 8
changes shape: everyone still reports different numbers, but each number is at least
about the setting its author cares about.

**What it still cannot do.** A splat reconstruction has no mass, no friction and no
articulation. Drawers do not open in it unless somebody says which part is a drawer. The
reconstruction is of appearance; the physics still has to be authored or guessed, which
means this technique moves the appearance gap and leaves the contact gap untouched.

### 5.4 What still does not transfer

Be concrete about this, because the literature is not.

Nothing published in 2026 claims to have closed the contact gap. MuJoCo's own new
penetration-free contact mode, described in section 2.1, resolves *frictionless*
contacts. Genesis's headline 1.0 feature is non-convex collision *detection*, which is
about finding contacts, not about modelling what they feel like. The parameters that
decide whether a grasp holds — friction coefficient, surface compliance, the stiffness
of a rubber pad — are still numbers somebody typed in.

The consequence for anyone reading this repository is unchanged from [what simulation
will not tell
you](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you):
simulation tells you whether your *reasoning* is right, not whether your grasp will
hold.

## 6. Synthetic data generation

**What it was before.** If you needed a thousand demonstrations, somebody teleoperated a
robot a thousand times. The original ALOHA work used about fifty demonstrations per task;
ALOHA Unleashed used 26,241 and did not achieve higher success rates, which is the single
most sobering number in this repository and is discussed in
[the mechanism document](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026).

**What changed.** Data multiplication moved from a research technique to the way large
simulated datasets are built. The visible result is the size of what is now published:
[RoboCasa365](https://robocasa.ai/), released on 18 February 2026, ships "365 tasks, 2500+
kitchen scenes, 2200+ hours of robot demonstration data", and on 7 July 2026 added
per-frame subtask annotations in which "every timestep is labeled with a subtask index,
atomic-skill name, stage (i.e. pick / place / navigate), and a natural-language
instruction". Status: **Downloadable**; the RoboCasa repository's licence file is the MIT
licence, copyright 2026 the RoboCasa Team, despite GitHub reporting the licence as
unrecognised.

NVIDIA's equivalents ship inside Isaac Lab 3.0, whose release notes list "Isaac Lab
Mimic and SkillGen demonstration-generation workflows". Status: **Downloadable** under
BSD-3-Clause, on NVIDIA hardware.

**How it was achieved.** The core trick, from the MimicGen line of work, is that a
demonstration of a manipulation task is mostly a sequence of object-relative motions. If
you record one demonstration and then move the objects, you can transform the recorded
end-effector path into the new object frames and replay it, keeping the attempts that
succeed in simulation and discarding the rest. One human demonstration becomes hundreds of
machine-checked ones. RoboTwin 2.0, at [arXiv 2506.18088](https://arxiv.org/abs/2506.18088),
adds heavy domain randomisation on top of the same idea.

**Why it matters.** It breaks the linear relationship between human hours and dataset size
for exactly the class of tasks — pick, place, insert, open — that most manipulation work is
about.

**What it still cannot do.** The generated data inherits every property of the source
demonstration and of the simulator. It contains no recovery behaviour that the demonstrator
did not perform, no failure the simulator cannot produce, and no contact subtlety the
contact model does not have. Generating a hundred variations of a grasp that only works
because the simulated friction is generous produces a hundred instances of the same wrong
belief. The success filter checks success *in the simulator*, which is the thing you were
trying not to trust.

## 7. The benchmarks, and what each one measures

Each entry below says what the benchmark actually measures, what it does not, and its
current maintenance state. Section 8 then argues that comparing two numbers from it is
usually invalid.

### 7.1 LIBERO

[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) (MIT, from its licence
file) is the benchmark most manipulation papers report. It is a set of 130 simulated
tabletop tasks in five suites — LIBERO-Spatial, LIBERO-Object and LIBERO-Goal with ten
tasks each, LIBERO-90 with ninety, and LIBERO-Long with ten — built on robosuite and
therefore on MuJoCo. It was published at [arXiv
2306.03310](https://arxiv.org/abs/2306.03310) in 2023 to study lifelong learning,
meaning how well a robot transfers knowledge from tasks it has already learned to new
ones.

**What it measures.** Whether a policy trained on a fixed set of demonstrations can
reproduce those tasks from the same initial-state distribution.

**What it does not measure.** Almost everything else, and section 8.1 gives the evidence.

**Maintenance.** The original repository's last commit was 15 March 2025. It is stable
because it stopped, not because it is finished. Status: **Downloadable** under MIT.

### 7.2 RoboCasa and RoboCasa365

[RoboCasa](https://github.com/robocasa/robocasa) simulates kitchens. The original, at
[arXiv 2406.02523](https://arxiv.org/abs/2406.02523), was published in 2024;
RoboCasa365 arrived on 18 February 2026 with the scale quoted in section 6, and its
leaderboard opened on 6 April 2026. It is robosuite and MuJoCo underneath.

**What it measures.** Multi-task performance across a wide range of kitchen activities in a
wide range of kitchen layouts. Its diversity of scenes is its genuine contribution.

**What it does not measure.** Anything outside a kitchen, and anything about the physical
variability of objects, since the layouts vary but the physics parameters do not.

**Maintenance.** Actively developed, which as section 8.3 shows is a mixed blessing for
comparability. Status: **Downloadable** under MIT.

### 7.3 SimplerEnv

[SimplerEnv](https://github.com/simpler-env/SimplerEnv) (MIT), from [arXiv
2405.05941](https://arxiv.org/abs/2405.05941), took a different approach: instead of
inventing simulated tasks, it built simulated versions of two specific real robot
setups — Google's robot and a WidowX arm on the BridgeData setup — and then checked
whether the simulated scores predicted the real ones. The paper reports "strong
correlation between policy performance in SIMPLER environments and in the real world".

**What it measures.** Whether a policy that works in simulation will work on *those two*
real setups. That is a genuinely different and more useful question than the others ask.

**What it does not measure.** Performance on any other robot. And its relevance decays: the
robots it models are the ones that were common when it was written, and the field has moved
to other arms.

**Maintenance.** Last commit 20 December 2025. Status: **Downloadable** under MIT.

### 7.4 BEHAVIOR-1K

[BEHAVIOR-1K](https://github.com/StanfordVL/BEHAVIOR-1K) (MIT) is the most ambitious
benchmark in the field and the only one that starts from what people said they wanted.
Its site describes "1,000 activities, instantiated in 50 fully interactive scenes with
10,000+ objects", and calls itself "the first simulation benchmark grounded in real
human needs". It runs on OmniGibson, which runs on Isaac Sim.

The [2026 BEHAVIOR Challenge](https://behavior.stanford.edu/challenge/index.html)
launched on 2 July 2026 with 100 full-length household tasks across seven scenes,
submissions due 16 October 2026 and winners announced 4 November 2026. The ranking
metric is "Average task success score with BDDL partial credit", where BDDL is the
logical language the benchmark uses to state what counts as the task being done — so a
run gets credit for satisfying some of the goal conditions rather than all-or-nothing.
The organisers are explicit about the difficulty: "Agents must search across rooms,
manipulate many objects, handle object state changes, and satisfy symbolic BDDL goal
conditions after several minutes of autonomous execution."

**What it measures.** Long-horizon mobile manipulation with semantic goals, which is much
closer to a useful task than anything else on this list.

**What it does not measure.** Anything you can check on a Mac, or on a machine without a
recent NVIDIA card, because of the Isaac Sim dependency. Its difficulty is also its
weakness as a research instrument: a benchmark where scores are low and sparse produces
rankings dominated by noise.

Status: **Downloadable** under MIT, on Linux with an NVIDIA card.

### 7.5 RoboTwin-Phys, and the dimension nobody was varying

This one is new enough to be worth a full entry, because it names a hole in every
benchmark above.

**What it was before.** Simulated benchmarks vary appearance, layout and camera position.
[RoboTwin-Phys](https://arxiv.org/abs/2609.26292), from 22 September 2026, points out what
they hold fixed: "While large-scale simulation benchmarks increasingly incorporate
variations in object appearance, scene layout, and visual observations, they typically keep
the underlying physical parameters fixed."

**What changed.** RoboTwin-Phys varies thirteen physical attributes — mass, friction, joint
dynamics — continuously within plausible ranges, and releases "more than 5,000 expert
demonstrations with ground-truth physical parameters". Status: **Paper only** as of 23
September 2026; the paper was posted the day before this was written.

**How it was achieved.** By treating the physics parameters as an explicit axis of the
benchmark design rather than as fixed constants of the environment.

**Why it matters.** It measures the thing a real deployment will actually hit. Objects in a
real kitchen differ in weight and surface far more than they differ in camera angle.

**What it still cannot do.** The physical parameters are still the simulator's parameters,
varied within ranges its authors chose. A policy robust across a simulator's friction range
has not been shown robust to a real surface the simulator cannot represent.

The finding is the part to remember: "models that remain effective under existing
visual and layout randomization can degrade markedly under changes in physical
conditions."

## 8. Why two numbers on the same benchmark are usually not comparable

This is the most important section in the document, and it is the one with the best
evidence behind it.

### 8.1 What a high LIBERO score is actually measuring

Three independent pieces of work in the last year took models that score above 90% on
LIBERO and asked what those scores rest on. The answers agree, and they are worse than
"benchmarks are imperfect".

[LIBERO-PRO](https://arxiv.org/abs/2510.03827) perturbed four things a real deployment
would perturb — the manipulated objects, the initial states, the task instructions and
the environment — and reports that "although existing models achieve over 90% accuracy
under the standard LIBERO evaluation, their performance collapses to 0.0% under our
generalized setting". The failure mode is specific and damning: "models persist in
executing grasping actions when the target object is replaced with irrelevant items,
and their outputs remain unchanged even when given corrupted instructions or even
messy tokens."

[LIBERO-Plus](https://arxiv.org/abs/2510.13626) perturbed seven dimensions including
camera viewpoint, lighting, background texture and sensor noise, and found
"performance dropping from 95% to below 30% under modest perturbations". It also found
something that should stop anyone quoting a language-conditioned success rate: "models
are largely insensitive to language variations, with further experiments revealing
that models tend to ignore language instructions completely."

[MINERVA](https://arxiv.org/abs/2609.03715), from 3 September 2026, approached it from
the opposite direction by asking how small a policy can be and still pass. Its
comparison point is π0.5, one of the large general-purpose manipulation policies of
the current generation, as packaged in LeRobot. A policy with 540,000 parameters —
7,700 times fewer than that baseline — reached "95.1% average success over 2,000
rollouts on the four standard LIBERO suites, only 2.4 points below the reported
LeRobot π0.5 result". It runs in 5 to 9 milliseconds per action chunk on a laptop CPU
with no graphics card. And it includes the cleanest diagnostic of the three: "A
task-ID permutation probe shows that standard LIBERO instruction conditioning
primarily selects among memorized tasks: changing only the task-ID mapping reduces
success to near chance."

Put those together. A benchmark that a half-million-parameter network passes at 95%,
on which the instruction is a task selector rather than an instruction, and whose
scores fall to near zero when you move the camera, is not measuring the capability its
scores are quoted as evidence for. MINERVA's own LIBERO-Plus results put the same
0.54M policy at 46 to 56%, "with near-zero robustness to photometric shifts", which is
at least an honest number.

This is also why this repository's other document notes MINERVA's finding that flow
matching gave no detectable advantage over plain regression: a benchmark this
saturated cannot resolve architectural questions, so architectural conclusions drawn
from it are not supported.

### 8.2 The statistical problem underneath

Even where a benchmark measures something real, the sample sizes do not support the
comparisons being made. [PhAIL](https://arxiv.org/abs/2605.29710), from 28 May 2026,
states the current practice plainly: real-world VLA evaluation "still rests on binary
success rate at a fixed timeout with N <= 25 rollouts per condition, almost always
without confidence intervals or paired statistical comparison; these cohort sizes
struggle to resolve close comparisons reliably."

Consider what twenty-five trials can support. If a policy succeeds 20 times out of 25,
the exact 95% confidence interval on that 80% — the Clopper-Pearson interval, which is
the standard conservative one for a proportion — runs from 59.3% to 93.2%. A rival
scoring 76%, which is 19 out of 25, has an interval from 54.9% to 90.6%. The two
overlap almost completely, so no honest test separates them. Yet papers routinely
report such pairs as one method beating another. Those two intervals were computed for
this document from the binomial distribution; you can reproduce them in three lines of
Python.

PhAIL's proposed fix is instructive about how much work resolving these comparisons
takes. It replaces the binary success rate with the full distribution of
time-to-success, scores with a throughput measure anchored to human teleoperation on
the same fixture, and applies a Kolmogorov-Smirnov test per object. Even then, of
three close comparisons among four public VLAs, it resolves two and reports that "the
closest pair (OpenPI vs. GR00T) remains unresolved within our budget". That is what it
looks like when somebody does this properly: one of your three comparisons stays
unanswered. Status: **Paper only**, with a benchmark and reference implementation
described as open.

PhAIL also supplies a number worth keeping for perspective. The best
vision-language-action model it evaluated is about seven times slower per operation
than a human doing the same task by teleoperation on the same fixture, measured as a
ratio of restricted mean survival times — that is, of average time taken, with runs
that never finished handled properly rather than discarded.

### 8.3 The versioning problem, with a clean example

Set aside statistics. Two papers can report numbers on the same named benchmark and be
measuring different things, because the benchmark changed between them.

Here is a documented case. RoboCasa's own update log records, for 12 May 2026:
"v1.0.1: Updated horizon lengths (1.5x increase) across all tasks for consistency.
Please update to the latest version for running evals." The horizon is the number of
timesteps a policy gets before the episode is scored as a failure. Increasing it by
half across every task raises every success rate, by an amount that depends on how
close each policy was to finishing when the old clock ran out — which is different for
every policy. A paper submitted in April 2026 and a paper submitted in June 2026, both
reporting "RoboCasa365 success rate", are reporting two different quantities. Neither
is wrong. They are not comparable, and almost no paper states which version it ran.

MuJoCo supplies a second instance. Version 3.9.0, on 27 May 2026, redesigned what the
contact parameters `margin` and `gap` mean, so that contacts are now detected when the
distance is below `margin + gap` rather than below `margin`. The changelog notes that
with the default values of zero the behaviour is unchanged — but any model that set
those parameters deliberately, which includes most careful gripper models, behaves
differently before and after that release.

The general rule this supports: **a benchmark score is a measurement of a policy, a
benchmark version, a simulator version, an episode limit and a success criterion, and
papers report only the first of those five.**

### 8.4 What this adds up to

Evaluation is the weakest link in robot manipulation research, and the evidence above
is sufficient to say so without hedging. The situation, stated fairly:

A high score on a standard simulated benchmark is evidence that a policy fits that
benchmark's training distribution. It is not evidence of capability, because networks
thousands of times too small also achieve it and because the scores collapse under
perturbations any deployment would apply. Numbers from two papers on the same
benchmark are generally not comparable, because the sample sizes cannot resolve the
differences claimed and because the benchmark's own definition changes between
releases. And the field knows this: at least six papers in the past year exist
specifically to say so, which is itself the strongest possible evidence that the
problem is real.

What this does not mean is that benchmarks are worthless. A benchmark score is a
useful regression test — it tells you whether your change broke something — and a
useful sanity check that a training pipeline runs at all. Those are real uses. Ranking
methods is not one of them.

## 9. What is being done about evaluation

Four responses exist, and they attack the problem from different directions. The table
summarises what each one is for; the paragraphs after it give the mechanism and the
limit.

| Effort | Its answer to the problem |
| --- | --- |
| RoboArena | give up on standard tasks, crowd-source double-blind pairwise comparisons |
| AutoEval | automate real-robot evaluation so that large sample sizes become affordable |
| RoboChallenge | run everyone's policy on the same real robots, centrally |
| `lerobot-eval` | at least make the simulated runs use identical code |

[RoboArena](https://arxiv.org/abs/2506.18123) abandons standardisation deliberately.
Evaluators at seven academic institutions, all using the DROID robot platform, each
choose their own tasks and environments, but must run **double-blind pairwise
comparisons** — two policies on the same task without knowing which is which — and the
rankings come from aggregating those preferences. The paper reports "more than 600
pairwise real-robot evaluation episodes across seven generalist policies". The
mechanism is the same one that ranks chess players: you do not need everyone to play
the same opponent if enough pairs play each other. The limit is that it ranks policies
against each other and tells you nothing about whether any of them is good enough for
a job. Status: **Shipped** as an open network.

[AutoEval](https://arxiv.org/abs/2503.24278) attacks the cost instead. It provides
automatic success detection and automatic scene resets on WidowX arms in the
BridgeData setup, so policies can be evaluated "around the clock with minimal human
intervention", with results that "correspond closely to ground truth evaluations
conducted by hand". The mechanism is that the expensive part of real evaluation is a
person resetting the scene, and that can be automated for a restricted class of task.
The limit is exactly that restriction: scenes that reset themselves are scenes where
nothing is consumed, broken or permanently moved. Status: **Shipped**, with public
access to scenes.

[RoboChallenge](https://arxiv.org/abs/2510.17950) is the centralised option: an online
system where you submit a policy and it runs on the operators' real robots, with an
initial benchmark called Table30. The mechanism is that one operator running
everything removes every source of variation between labs at once. The limit is that
it introduces a single point of authority and a single set of tasks, which is the
standardisation RoboArena argues does not scale. Status: **Shipped**.

`lerobot-eval`, which arrived in [LeRobot
v0.6.0](https://huggingface.co/blog/lerobot-release-v060) on 6 July 2026, is the least
glamorous and possibly the most useful. It is one command-line tool that runs six
simulated benchmarks — LIBERO-plus, RoboTwin 2.0, RoboCasa365, RoboCerebra, RoboMME
and VLABench — through a single harness. The mechanism is boring and correct: if
everyone runs the same evaluation code with the same defaults, one large family of
discrepancies disappears. Note which LIBERO it integrates. LeRobot chose
[LIBERO-Plus](https://arxiv.org/abs/2510.13626), the robustness variant, rather than
plain LIBERO, which is a quiet institutional judgement about what the original is
worth. Status: **Shipped** under Apache-2.0, and on Linux only for LIBERO, per [the
LeRobot LIBERO page](https://huggingface.co/docs/lerobot/libero).

The same release added something adjacent worth knowing about: pretrained reward
models, including [Robometer](https://huggingface.co/docs/lerobot/robometer), a
4-billion-parameter model from [arXiv 2603.02115](https://arxiv.org/abs/2603.02115)
that scores task progress and success from a video and a written instruction.
Automatic success detection is the bottleneck in every scheme above, so a
general-purpose success detector is load-bearing infrastructure. It is also a model
being judged by a model, which is a failure mode with a long history, and no published
work establishes how often Robometer agrees with a careful human on a task it was not
trained for.

## 10. Everything that happened after May 2026, in one list

Gathered here because these are the items a reader working from knowledge that ends in
May 2026 will not have. Read the table chronologically; every row is sourced in the
section named in the last column.

| Date | What happened | Status | Section |
| --- | --- | --- | --- |
| 27 May 2026 | Genesis World 1.0.0: non-convex multi-contact collision detection | Shipped | [2.5](#25-genesis-world) |
| 27 May 2026 | MuJoCo 3.9.0 redesigns `margin` and `gap` semantics | Shipped | [2.1](#21-mujoco) |
| 28 May 2026 | PhAIL proposes distributional real-robot evaluation | Paper only | [8.2](#82-the-statistical-problem-underneath) |
| 22 Jun 2026 | MuJoCo 3.10.0: thread pool, unified logging | Shipped | [2.1](#21-mujoco) |
| 2 Jul 2026 | 2026 BEHAVIOR Challenge opens, 100 tasks, 7 scenes | Shipped | [7.4](#74-behavior-1k) |
| 6 Jul 2026 | LeRobot v0.6.0: three world-model policies, `lerobot-eval`, reward models | Downloadable | [4.4](#44-world-models-that-actually-shipped-inside-policies) |
| 7 Jul 2026 | RoboCasa adds per-frame subtask annotations | Downloadable | [6](#6-synthetic-data-generation) |
| 27 Jul 2026 | MuJoCo 3.11.0: surface velocity and contact adhesion | Shipped | [2.1](#21-mujoco) |
| 27 Jul 2026 | Cosmos-H-Dreams applies world-model simulation to surgical robotics | Demonstrated | [4.5](#45-one-more-for-the-record) |
| 11 Aug – 10 Sep 2026 | Newton reaches 1.5.0 then 1.6.0 | Shipped | [2.3](#23-newton) |
| 8 Sep 2026 | MuJoCo 3.13.0: the `discrete` integrator | Shipped | [2.1](#21-mujoco) |
| 10 Sep 2026 | Isaac Sim 6.1.0 | Shipped | [2.4](#24-isaac-sim-and-isaac-lab) |
| 16 Sep 2026 | Isaac Lab 3.0 Early Access: kit-less, multi-backend, Newton physics | Downloadable | [2.4](#24-isaac-sim-and-isaac-lab) |
| 18 Sep 2026 | Isaac Sim 7.0.0 Alpha 1 | Announced | [2.4](#24-isaac-sim-and-isaac-lab) |
| 22 Sep 2026 | MuJoCo 3.14.0: `ipc` penetration-free flex contact | Shipped | [2.1](#21-mujoco) |
| 22 Sep 2026 | RoboTwin-Phys: benchmarks vary appearance but not physics | Paper only | [7.5](#75-robotwin-phys-and-the-dimension-nobody-was-varying) |
| 23 Sep 2026 | Genesis World 1.4.2 | Shipped | [2.5](#25-genesis-world) |

Two things stand out from that list once it is assembled. The first is that MuJoCo
shipped eleven releases in the eight months to September 2026, several of them
changing the physics itself, which is a pace no other simulator in this field is
matching. The second is that the three largest efforts — MuJoCo Warp, Newton and Isaac
Lab 3.0 — are all converging on the same architecture: a Warp-compiled physics core
with swappable solvers and renderers above it. Competitors do not usually agree on an
architecture unless it is the right one or unless one of them is paying.

## 11. What to do with all this

Four practical conclusions follow, for somebody working on a Mac.

**Run MuJoCo, and do not apologise for it.** It is the best-supported physics engine on
Apple Silicon, it is where the physics research is happening, and the throughput figures in
section 3 show that for single-scene work a Mac's processor is in the same range as an A100
running MJX. The case for an NVIDIA card is parallel reinforcement learning, not simulation
quality.

**Try Genesis World if you want graphics-processor physics on the Mac.** It is the only
option, its support table claims it plainly, and the mechanism behind the claim — a compiler
with a Metal target — is the kind that keeps working.

**Do not plan around Isaac anything.** Isaac Sim, Isaac Lab,
[Isaac Lab Arena](https://github.com/isaac-sim/IsaacLab-Arena), OmniGibson and therefore
BEHAVIOR-1K are all unavailable to you without different hardware, and that is a stated
platform requirement rather than a temporary gap.

**Treat every benchmark number you read as a regression test result rather than a
measurement of capability.** When a paper reports a LIBERO score, the questions to ask are
which version, how many rollouts, with what episode limit, and whether the authors ran the
perturbation suites. If the paper does not say, you have learned something about the paper. The
one measurement that has consistently meant something in this repository is still the one in
[making it work](../06_object-perception/07_making-it-work.md#1-how-to-tell-whether-it-is-working):
count the attempts that succeeded, the attempts that failed after committing, and the times the
system declined with a reason. Nobody can publish that on a leaderboard, which is precisely why
it is worth measuring.
