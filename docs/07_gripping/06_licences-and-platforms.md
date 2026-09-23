# Licences, platforms and the comparison grids

The cross-cutting document: what you are allowed to ship, what will run on your
machine, how gripping fits into ROS 2, and every approach in this area side by
side.

It exists separately because these questions do not belong to the hardware, to
the geometry or to the models. They are the same questions whichever you are
working on, and answering them three times is how the three quietly disagree.

If you read one section of this area, read section 1. Gripping has the worst
licence hygiene of any subject in these documents, and the specific failure — a
popular repository with no licence file at all — is the one people are least
equipped to notice, because it produces no badge, no warning and no error.

## Contents

1. [Licences, and the four traps in this area](#1-licences-and-the-four-traps-in-this-area)
2. [What runs on an Apple Silicon Mac](#2-what-runs-on-an-apple-silicon-mac)
3. [Putting it in ROS 2](#3-putting-it-in-ros-2)
4. [The comparison grids](#4-the-comparison-grids)

---

## 1. Licences, and the four traps in this area

Every licence in this document was read from the project's own licence file in
September 2026, using the GitHub licence API or by listing the repository root.
Not from a badge, not from a README, and not from a blog post. That distinction
produced a different answer in a dozen cases.

### 1.1 No licence at all

This is the commonest problem in learned grasping and the most serious, because
default copyright grants nothing. Not commercial use, not research use, not the
right to modify. A repository with no licence file is not permissive; it is
closed.

The projects below have real traction and no licence file:

| Project | Stars | What it is |
| --- | --- | --- |
| [DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) | 572 | a vision-language-action model for dexterous grasping |
| [GraspVLA](https://github.com/PKU-EPIC/GraspVLA) | 419 | the same, from a different group |
| [UniDexGrasp](https://github.com/PKU-EPIC/UniDexGrasp) | 273 | dexterous grasp generation |
| [GenDexGrasp](https://github.com/tengyu-liu/GenDexGrasp) | 210 | generalisable dexterous grasping |
| [DexGraspNet2](https://github.com/PKU-EPIC/DexGraspNet2) | 159 | a large dexterous grasp dataset and method |
| [DexGraspNet](https://github.com/PKU-EPIC/DexGraspNet) | — | its predecessor |
| [SuctionNet-1Billion](https://github.com/graspnet/suctionnet-baseline) | — | the main open suction grasp baseline |

Seven projects, thousands of stars between them, and no grant of rights on any of
them. Anyone who has built on these has done so without permission, usually
without realising there was a question.

### 1.2 A licence you cannot read

[NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet), one of the
most cited grasp models in the field, ships its licence as a file called
`License.pdf`. GitHub's licence API reports nothing. Every dependency scanner you
run will classify the project as unlicensed. To know the terms you have to
download and open a PDF, which nobody does before a prototype turns into a
product.

The maintained PyTorch reimplementation,
[elchun/contact_graspnet_pytorch](https://github.com/elchun/contact_graspnet_pytorch),
copied the PDF rather than replacing it.

### 1.3 A licence that contradicts itself

The [GraspNet-1Billion datasets page](https://graspnet.net/datasets.html) states
that all data, labels, code and models are "licensed under a Creative Commons
Attribution 4.0 Non Commercial License (BY-NC-SA)". That names three mutually
inconsistent things in one sentence. CC BY 4.0 permits commercial use. "Non
Commercial" does not. BY-NC-SA is a fourth licence again, adding a share-alike
obligation that neither of the others carries. There is no identifier you can put
in a dependency manifest that is faithful to that sentence.

The only safe reading is the most restrictive one, and the page's own commercial
contact email tells you what the authors meant.

A related case: [graspness_unofficial](https://github.com/graspnet/graspness_unofficial)
carries, verbatim, the same Shanghai Jiao Tong University non-commercial
agreement as the official baseline — including a clause stating that any
derivative you create becomes owned by the licensor, and a trademark clause
forbidding use of the name "AlphaPose", which is a completely unrelated piece of
software. A licence that has been copied without being read is a licence nobody
thought about.

### 1.4 Code and weights under different licences

Checking the repository is not checking the model. NVIDIA's GraspGen is the
clearest case and it splits four ways:

| Artefact | Licence |
| --- | --- |
| [NVlabs/GraspGen](https://github.com/NVlabs/GraspGen) code | NVIDIA License, non-commercial, with a clause permitting NVIDIA to use the work commercially |
| [NVlabs/GraspGenX](https://github.com/NVlabs/GraspGenX) code | **Apache-2.0**, with no use limitation appended |
| the published weights | NVIDIA Open Model License |
| the training dataset | CC BY 4.0 |

The successor repository is more permissive than the original, which is the
opposite of the usual direction. The weights you would actually run are still
under NVIDIA's own model licence, so the Apache badge on the code does not make a
deployment Apache-2.0.

GraspVLA is the same shape with the pieces in different places: no licence on the
code, CC BY-NC-4.0 on the weights, and no licence tag at all on its
billion-sample training dataset.

And there is a case of a third party granting rights they do not hold. A Hugging
Face repository mirroring Contact-GraspNet's weights declares them MIT. The
upstream licence is an NVIDIA agreement in a PDF and is certainly not MIT. A
licence field on a mirror is not a licence.

### 1.5 Three more that are specific to this area

**Two vendors ship their own drivers under the GPL.** Schunk's
[mechatronic gripper driver](https://github.com/SCHUNK-SE-Co-KG/schunk_mechatronic_gripper),
their [SVH hand driver](https://github.com/SCHUNK-SE-Co-KG/schunk_svh_ros_driver)
and their force-torque sensor driver are all GPL-3.0, as is GelSight's
[gsrobotics](https://github.com/gelsightinc/gsrobotics) SDK. Robotiq, OnRobot and
Franka all use permissive licences, so this is a vendor decision rather than an
industry norm — but if you link a GPL driver into a product, the obligation to
publish your source follows.

**A non-commercial Creative Commons licence on a hardware driver.** Meta's
[digit-interface](https://github.com/facebookresearch/digit-interface) is CC BY-NC
4.0 and archived. The DIGIT sensor is sold; its driver may not be used in a
product. A Creative Commons licence is also a poor fit for software, addressing
neither patents nor source distribution.

**A permissive licence covering a paid dependency.** Two well-starred dexterous
grasping projects, [GraspXL](https://github.com/zdchan/GraspXL) and
[RobustDexGrasp](https://github.com/zdchan/RobustDexGrasp), vendor the RaiSim
physics simulator. Their licence file makes the MIT grant apply only to the
wrapper directories and states that you must obtain a licence from raisim.com for
the simulator, which is then activated with a key. The physics engine these
projects need is paid software, and nothing on their GitHub pages says so.
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) has the same shape: a BSD-3
wrapper pinned to proprietary Isaac Sim.

One more that catches people who only want a simulation model.
[mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie)'s root
licence file is a machine-generated concatenation of per-model licences, and
GitHub reports the repository as unclassified. The gripper and hand models in it
differ: the Robotiq 2F-85 model is BSD-2-Clause from ROS-Industrial, the Wonik
Allegro model is BSD-2-Clause from SimLab, the Shadow Hand model is Apache-2.0,
and the LEAP Hand and UMI gripper models are MIT. Read the per-model file.

The LEAP Hand is worth stating on its own, because the answer changes with the
artefact. **Its MuJoCo model is MIT and its driver API is CC BY-NC 4.0.** You may
simulate the hand commercially and you may not drive the real one.

### 1.6 What you can actually ship

The short list, for a commercial product, verified from the files:

| What you want | The option with a usable licence |
| --- | --- |
| a grasp model on a point cloud | [GPD](https://github.com/atenpas/gpd), BSD-2-Clause — see [section 2](#2-what-runs-on-an-apple-silicon-mac) on its age |
| a fast planar grasp model | [GG-CNN](https://github.com/dougsm/ggcnn) or [GR-ConvNet](https://github.com/skumra/robotic-grasping), BSD-3-Clause |
| a modern learned model from the GraspNet lineage | [EconomicGrasp](https://github.com/iSEE-Laboratory/EconomicGrasp), MIT |
| a diffusion grasp generator's code | [GraspGenX](https://github.com/NVlabs/GraspGenX), Apache-2.0, with the weights under a separate NVIDIA licence |
| gripper drivers | Robotiq, OnRobot and Franka, all permissive; Schunk is GPL |
| force and compliance control | [ros2_controllers](https://github.com/ros-controls/ros2_controllers), Apache-2.0, and [crisp_controllers](https://github.com/learnsyslab/crisp_controllers), MIT |
| simulation | MuJoCo, Apache-2.0, with per-model licences in the menagerie |
| tactile sensing | [AnySkin](https://github.com/raunaqbhirangi/anyskin), MIT; GelSight's SDK is GPL and DIGIT's driver is non-commercial |

If you are doing research, most of the non-commercial licences permit what you are
doing. The seven projects in [section 1.1](#11-no-licence-at-all) do not, and
that is worth knowing before a paper's artefact review asks.

## 2. What runs on an Apple Silicon Mac

The honest headline for this area, unlike the perception area's, is that almost
no learned grasp model does. The reason is more specific than people expect and
it is worth knowing exactly, because it tells you what to check first on anything
new.

### 2.1 One abandoned library is the gate

[MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine) is NVIDIA's sparse
convolution library. It is MIT-licensed, it has around 2,960 stars, and it was
**last pushed in March 2024 with 236 open issues**. Its stated requirement is CUDA
10.1 or later, matching the CUDA version PyTorch was built against, and it
installs by compiling with `nvcc`.

`graspness_unofficial`, `anygrasp_sdk` and `EconomicGrasp` all import it — three
of the four significant models in the GraspNet-1Billion lineage. So the obstacle
for a Mac is not the vague "grasping needs a GPU". It is one abandoned
sparse-convolution library that three leading models depend on.

The other blockers, each fatal on its own, are custom `pointnet2` CUDA operators,
`spconv-cu120`, `flash-attn` and `xformers`. None has a CPU or Metal build.

### 2.2 The table

| Works on Apple Silicon | Does not |
| --- | --- |
| all the geometry in [choosing a grip](03_choosing-a-grip.md) — it is arithmetic on arrays | every model in the GraspNet-1Billion lineage, via MinkowskiEngine |
| Open3D and trimesh, with native `arm64` wheels | Contact-GraspNet and its PyTorch fork, via `pointnet2` and pinned CUDA |
| MuJoCo and `mujoco_menagerie`, natively | GraspGen, via `spconv-cu120` |
| [GPD](https://github.com/atenpas/gpd) in principle: C++ on PCL, Eigen and OpenCV, with no CUDA requirement | GraspVLA, via `flash-attn`, which cannot be installed at all |
| [GG-CNN](https://github.com/dougsm/ggcnn) probably: plain PyTorch with no custom operators | DexGraspVLA, via `xformers`, and its 72-billion-parameter planner |
| ROS 2 via [RoboStack](https://robostack.github.io/) | AnyGrasp, twice over: CUDA, and a machine-locked licence key |
| `ros2_controllers`, including the gripper and admittance controllers | Isaac Lab and Isaac Sim, entirely |
| the vendor gripper drivers, which are serial or Modbus | Gazebo's suction gripper, because there is not one — see [section 3](#3-putting-it-in-ros-2) |

Two of those rows carry a caveat rather than a yes. GPD is CPU-friendly and was
last pushed in January 2022, so its OpenCV 3.4 and PCL dependencies are the
practical obstacle rather than the GPU. GG-CNN is plain PyTorch and was last
pushed in July 2020, so its Python 3.6-era pinning is the obstacle.

### 2.3 The pattern worth carrying

**A clean `requirements.txt` is not evidence that a project will install.**
`graspnet-baseline`'s requirements file lists only torch, tensorboard, numpy,
scipy, open3d, Pillow and tqdm, which looks entirely portable. Its README then
tells you to compile `pointnet2` operators and a CUDA `knn` operator by hand.
Dependency scanners do not read prose. Reading the install instructions is the
only reliable check.

### 2.4 What this means in practice

Develop the geometry on the Mac and the model elsewhere, or do not use a model.
The methods in [choosing a grip](03_choosing-a-grip.md) run natively and are
tested in a second with no simulator and no weights; MuJoCo and its gripper models
run natively; the ROS 2 control stack runs through RoboStack, which is what this
repository uses. A rule-based gripping pipeline can be complete, property-tested
and working before any model is involved.

## 3. Putting it in ROS 2

Gripping in ROS 2 is smaller than most people expect, and knowing its actual
extent saves a lot of searching.

### 3.1 The message types

A gripper is commanded through
[control_msgs](https://github.com/ros-controls/control_msgs) (BSD-3-Clause). Two
actions matter.

`GripperCommand.action` is the classic. You send a position and a maximum effort,
and the result carries four fields: the current position, the current effort, and
two booleans, `stalled` and `reached_goal`. The definition's own comment on
`stalled` is "True iff the gripper is exerting max effort and not moving".

**Those two booleans are the whole of ROS 2's grasp feedback, and they say exactly
what [holding on, section 2.3](05_holding-on.md#23-the-grasp-detected-signal-answers-a-weaker-question-than-it-appears-to)
warns about.** A successful grasp appears as `stalled` true and `reached_goal`
false: the fingers stopped early and are pushing. So does a grip on the wrong
object, a grip on two objects, a grip on the tote wall, and a jammed finger. The
message has no way to express what stopped the fingers, because the gripper does
not know.

`ParallelGripperCommand.action` is the newer one, carrying a `sensor_msgs/JointState`
so that position, velocity and effort limits can be set per joint. It returns the
same two booleans.

### 3.2 The packages

| Package | Licence | What it gives you |
| --- | --- | --- |
| [control_msgs](https://github.com/ros-controls/control_msgs) | BSD-3-Clause | `GripperCommand` and `ParallelGripperCommand` |
| [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | [`parallel_gripper_controller`](https://control.ros.org/rolling/doc/ros2_controllers/parallel_gripper_controller/doc/userdoc.html), [`admittance_controller`](https://control.ros.org/rolling/doc/ros2_controllers/admittance_controller/doc/userdoc.html), `force_torque_sensor_broadcaster`, `pid_controller` |
| [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | BSD-3-Clause | Cartesian force and compliance control; last pushed October 2024 |
| [crisp_controllers](https://github.com/learnsyslab/crisp_controllers) | MIT | Cartesian **impedance** and operational-space control, for any arm with an effort interface |
| [franka_ros2](https://github.com/frankarobotics/franka_ros2) | Apache-2.0 | Cartesian and joint impedance, as example controllers, plus `franka_gripper` |
| [moveit_task_constructor](https://github.com/moveit/moveit_task_constructor) | BSD-3-Clause | sequencing a pick and place as stages; actively maintained |
| [moveit_grasps](https://github.com/moveit/moveit_grasps) | BSD-3-Clause | grasp generation for MoveIt; **last pushed November 2022** |
| [gpd_ros](https://github.com/atenpas/gpd_ros) | BSD-2-Clause | GPD in ROS; the ROS 1 lineage |

Three things about that list are worth stating outright.

**There is no impedance controller in upstream `ros2_controllers`.** Admittance
only. If you want impedance control, `crisp_controllers` is the maintained
permissive option and `franka_ros2`'s examples are the vendor one. The difference
between the two kinds, and why it is decided by your hardware, is [holding on,
section 3](05_holding-on.md#3-compliance-impedance-and-admittance).

**MoveIt 2 has no grasping and no force control.** It plans collision-free arm
motion to a pose you supply. There is no grasp package and no compliance package
anywhere in the repository. This surprises people because MoveIt is what the
pick-and-place tutorials use; the pick in those tutorials is a taught grip and a
fixed squeeze. `moveit_grasps` filled the gap and has not been pushed since
November 2022. `moveit_task_constructor` is the live route, and it sequences
stages rather than choosing grips.

**Gazebo Harmonic has no suction or vacuum gripper.** Its full system list
includes `contact`, `detachable_joint`, `force_torque`, `optical_tactile_plugin`
and `touch_plugin`, and no gripper system of any kind. A simulated suction gripper
in Harmonic is something you build from `detachable_joint` plus `contact`. Every
"Gazebo vacuum gripper" repository on GitHub is either Gazebo Classic or an
unlicensed personal fork.

### 3.3 Where the vendor drivers fit

Every gripper driver in [grippers and
hardware, section 9](02_grippers-and-hardware.md#9-drivers-ros-2-packages-and-licences)
presents itself as a `ros2_control` hardware interface, so the controller above is
the same whichever gripper you have. That is the right layering and it works. What
it does not give you is any of the semantics: the driver reports finger position
and the controller reports `stalled`, and everything about whether the grasp was
correct is yours to build.

## 4. The comparison grids

Everything in one place. These are for choosing, not for benchmarking, so speeds
are orders of magnitude rather than measured figures.

### 4.1 The six mechanisms

Read this as: what it holds, how much, how fast, and what disqualifies it.

| Mechanism | Typical payload | Speed | Needs | Ruled out by | Licence risk |
| --- | --- | --- | --- | --- | --- |
| parallel jaw, two-finger | 2 to 11 kg | 0.06 to 0.2 s to close | two opposed reachable faces | no room beside the object | none; drivers are permissive except Schunk |
| adaptive, underactuated | 2.5 to 5 kg | 0.6 to 4.3 s | the same, plus room to curl | the same, plus [the equilibrium line](02_grippers-and-hardware.md#23-the-equilibrium-line-and-grasps-you-did-not-command) | none |
| three-finger adaptive | 2.5 kg fingertip, 10 kg encompassing | about 1.5 s | the same | cost, and 70 N of fingertip force | none |
| suction | 2 kg per 40 mm cup, more in an array | 0.35 s to grip, 0.20 s to release | one flat, smooth, airtight patch | porous, ribbed, oily or wet surfaces | none |
| magnetic | 2.8 to 10 kg, orientation-dependent | 0.3 s | ferromagnetic material of sufficient thickness | aluminium, plastic, glass, most stainless | none |
| soft | 0.5 to 10 kg, shape-dependent | 32 to 120 picks per minute | a shape a finger can wrap | flat or square objects | none |
| custom tooling | whatever you design | whatever you design | the part always being the same | a changing part mix | none |

### 4.2 Choosing where to grip

| Approach | Gives you | Speed | Needs training | Unknown objects | Runs on a Mac |
| --- | --- | --- | --- | --- | --- |
| a taught grip | one pose | none | no | no | **yes** |
| [the antipodal test](03_choosing-a-grip.md#32-the-antipodal-test) | pass or fail per candidate | ~1 ms for thousands | no | **yes** | **yes** |
| [a geometric rule](03_choosing-a-grip.md#6-rules-from-a-measured-profile) | one grip, with a reason, or a refusal | ~1 ms | no | within a family | **yes** |
| [centre-of-mass ranking](03_choosing-a-grip.md#5-the-centre-of-mass-and-the-torque-nobody-budgets-for) | a score per candidate | ~1 ms | no | **yes** | **yes** |
| [the epsilon metric](03_choosing-a-grip.md#8-grasp-quality-metrics-you-can-compute) | a single quality number | ms | no | **yes** | **yes** |
| a planar grasp model | grasp rectangles, top-down only | tens of ms | pretrained | **yes** | probably |
| sampling and scoring, GPD | ranked 6-DoF poses | 0.1 to 1 s | pretrained | **yes** | in principle |
| a learned 6-DoF model | ranked 6-DoF poses | 0.1 to 1 s on a GPU | pretrained | **yes** | **no** |
| a grasping vision-language model | poses from an instruction | seconds, on a server | pretrained | **yes** | **no** |

### 4.3 The grasp models, with their licences

| Model | Licence, code / weights | Representation | CUDA | Shippable |
| --- | --- | --- | --- | --- |
| [GPD](https://github.com/atenpas/gpd) | BSD-2-Clause | 6-DoF, sampled and scored | no | **yes** |
| [GG-CNN](https://github.com/dougsm/ggcnn) | BSD-3-Clause | planar rectangles | no | **yes** |
| [GR-ConvNet](https://github.com/skumra/robotic-grasping) | BSD-3-Clause | planar rectangles | no | **yes** |
| [Dex-Net / GQ-CNN](https://github.com/BerkeleyAutomation/gqcnn) | UC Regents, research and not-for-profit only | planar, scored | yes | no |
| [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) | a PDF | 6-DoF from contact points | yes | read the PDF |
| [graspnet-baseline](https://github.com/graspnet/graspnet-baseline) | SJTU non-commercial | 6-DoF | yes | no |
| [graspness_unofficial](https://github.com/graspnet/graspness_unofficial) | SJTU non-commercial | 6-DoF | yes | no |
| [AnyGrasp](https://github.com/graspnet/anygrasp_sdk) | none; a machine-locked key | 6-DoF | yes | no |
| [EconomicGrasp](https://github.com/iSEE-Laboratory/EconomicGrasp) | **MIT** | 6-DoF | yes | **yes** |
| [GraspGen](https://github.com/NVlabs/GraspGen) | NVIDIA non-commercial | 6-DoF, diffusion | yes | no |
| [GraspGenX](https://github.com/NVlabs/GraspGenX) | **Apache-2.0** code, NVIDIA Open Model weights | 6-DoF, diffusion | yes | code yes, weights conditional |
| [M2T2](https://github.com/NVlabs/M2T2) | NVIDIA non-commercial | grasps and placements | yes | no |
| [SuctionNet-1Billion](https://github.com/graspnet/suctionnet-baseline) | **none** | suction points | yes | no |
| [GraspVLA](https://github.com/PKU-EPIC/GraspVLA) | none / CC BY-NC-4.0 | poses from text | yes | no |
| [DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) | **none** | dexterous, from text | yes | no |

### 4.4 Holding on

| Capability | What you need for it | What ROS 2 ships | Works on a Mac |
| --- | --- | --- | --- |
| commanded squeeze force | any electric gripper | `GripperCommand` | **yes** |
| grasp-detected signal | any electric gripper | `stalled` and `reached_goal` | **yes** |
| weighing the object | a wrist force-torque sensor | `force_torque_sensor_broadcaster` | **yes** |
| admittance control | a force sensor and a position-controlled arm | `admittance_controller` | **yes** |
| impedance control | torque-capable joints | **nothing upstream**; `crisp_controllers` or `franka_ros2` | **yes** |
| slip detection by finger gap | any electric gripper | nothing; write it | **yes**, and see [its blind spots](05_holding-on.md#41-the-finger-gap-check-and-what-it-cannot-see) |
| slip detection by shear | a tactile sensor | nothing | **yes** |
| a maintained slip-detection library | — | **there is none** | — |
| in-hand reorientation by sliding | force control | nothing; write it | **yes** |
| finger gaiting | a multi-finger hand | nothing | no |
