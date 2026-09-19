# Learned methods for two arms

These are the methods where the behaviour comes from data rather than from
someone writing it down — from demonstrations, from the robot's own practice, or
from a large pool of data gathered elsewhere. They cope with variety, they need a
great deal of data, and they cannot tell you why they failed.

**This is where two-arm work is actually happening.** The tasks that justify a
second arm — cloth, re-grasping, holding one thing while working on another — are
exactly the tasks nobody can write down, and the best-known bimanual system was
built for two arms from the start rather than adapted to them.

Read [the overview](overview.md) first if you have not — it sets out the tasks
these methods are for, the three kinds of two-arm coordination they have to
support, and a grid saying which method suits which task. The programmed methods
those are compared against are in
[the companion document](programmed-methods.md).

Each method below says which tasks it suits, **what changes when there are two
arms instead of one**, what its status is in 2026, and which open code to look
at. The task group letters — A to D — are the ones from
[the overview's task catalogue](overview.md#2-the-tasks-two-arms-are-asked-to-do).

## Contents

1. [Learning from demonstrations](#1-learning-from-demonstrations)
2. [Learning from trial and error](#2-learning-from-trial-and-error)
3. [Learning from large-scale pretraining](#3-learning-from-large-scale-pretraining)
4. [Learned pieces inside a programmed system](#4-learned-pieces-inside-a-programmed-system)
5. [Directed by language](#5-directed-by-language)

---

## 1. Learning from demonstrations

Show the task repeatedly and let the learner copy. This is the most practical
learning method for arms today, and this repo works through it in detail in the
[full training](../full-training/overview.md) docs.

**It is also the method most shaped by two arms.** The best-known bimanual
learning work is not a two-arm adaptation of a one-arm method — it was built for
two arms from the start, because copying is the one approach that does not need
the coordination between the arms to be described. You never write down that the
left hand should hold the shirt taut while the right hand smooths it: you do it,
several hundred times, and the coordination is in the data.

### 1.1 Behaviour cloning

A person performs the task while the cameras, the joint angles and the commands
they gave are all recorded. A network is trained to produce the command the
person gave, given what the cameras saw. Nothing about the task is described to
it — not the objects, not the goal, not the physics.

The naive version has been tried since the 1990s and works poorly. Asked for one
command per camera frame, the network is queried fifty times a second, each
answer is a fresh chance to be slightly wrong, the errors compound, and the arm
drifts into situations no demonstrator ever visited. Two developments fixed this
enough to matter.

**Action chunking**: predict the next hundred commands rather than one, and play
them out before looking again. A hundred steps at fifty a second is two seconds
of coherent motion decided in one go, which removes the jitter and keeps two arms
in step with each other. This is what ACT does.

**Generative action models**: demonstrators are inconsistent, and a network
trained to output one number per command averages their different approaches,
where the average of two good motions is often a bad one. Diffusion policies
generate the action sequence the way image models generate pictures, which lets
them represent "either this motion or that one". In 2026 the same job is usually
done by **flow matching**, a faster relative of diffusion, which is the action
head inside every current large policy. It is worth knowing that this is not
settled: a 2026 study
([MINERVA](https://arxiv.org/abs/2609.03715)) found flow matching gave no
detectable advantage over plain regression on its benchmarks while being
several times slower, so the field is optimising a choice it has not fully
justified.

**Where it stops.** Copying works for one skill and falls apart over a long
sequence. FurnitureBench, a benchmark of real IKEA-furniture assembly, is the
honest yardstick: behaviour cloning and offline reinforcement learning complete
none of its full assemblies except the simplest one, and the insertion and
screwing stages mostly fail outright. A twenty-step job needs something above the
policy that sequences and recovers, which is why
[section 5](#5-directed-by-language) exists.

**What two arms change here.** Four things, and the first is the one that matters.

*One policy controls both arms, not two policies.* The network's output is the
commands for both arms at once — for two six-joint arms with a gripper each, that
is fourteen numbers per step. This is not an implementation detail: it is why the
approach works. The coordination between the arms is inside a single prediction,
so the policy cannot produce a left-arm motion that contradicts its own right-arm
motion. Splitting into two policies and a coordinator throws that away and is not
what the successful systems do.

*Chunking matters more with two arms than with one.* Predicting a whole burst of
future commands keeps the arms coherent with each other over the whole burst
rather than re-deciding fifty times a second, which is exactly when two arms drift
out of step. A one-arm policy that jitters looks clumsy; a two-arm policy that
jitters drops the object it is holding between them.

*Demonstrating is genuinely harder.* Somebody has to drive fourteen joints at
once, in a coordinated way, for hundreds of episodes. This is why the standard rig
is a pair of small **leader** arms that a person holds one in each hand, with the
real arms following: it is the only method where controlling both arms at once is
natural. This repo covers the practicalities in
[collecting the data](../full-training/collecting-data.md#2-how-a-person-drives-two-arms).

*You need a camera that can see the pair.* One overhead view plus one camera on
each wrist is the usual arrangement, because the overhead view shows the relation
between the arms and the wrist views show what each is about to touch.

**Good for:** the contact-heavy parts of Group A, and Groups C and D where no
model of the object exists. Laundry folding is the flagship case, and a flagship
specifically for *two* arms: nobody can write down how to flatten a shirt, the
shape is determined by where both hands hold it, and demonstrating it is easy.
**Status in 2026:** the default first thing to try for a new learned task.
LeRobot's own documentation calls ACT "our recommended first policy", which is
about cost as much as quality — it trains in under an hour on a single consumer
GPU where a large policy takes a day.
**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) (27.6k
stars, pushed today) is where all of this now lives. Note that the original
implementations are historical: [ACT](https://github.com/tonyzhaozh/act) (2.2k)
has not been touched since 2024, and
[diffusion_policy](https://github.com/real-stanford/diffusion_policy) (4.6k) is
the reference implementation everyone cites and nobody develops. Use LeRobot's
versions. [robomimic](https://github.com/ARISE-Initiative/robomimic) (1.6k)
remains the careful study of which details matter.

### 1.2 Interactive imitation: correcting it as it goes

Behaviour cloning has a structural flaw: the policy only ever saw states a
competent demonstrator put the robot in, so its own small mistakes take it
somewhere unfamiliar, where its next action is worse. The fix is to let it drive
and correct it when it goes wrong, adding those corrections to the data. A few
dozen corrections are often worth several hundred fresh demonstrations, because
they cover exactly the situations the policy actually reaches.

**With two arms** the correction rig is the same leader-arm pair used to collect
the demonstrations, so a person can grab either arm the moment it goes wrong —
which is usually the arm that was *not* being watched. The failures worth
correcting are mostly coordination failures rather than single-arm ones: the
holding arm drifted, the handover released early, the two arms pulled the cloth
out of each other's grip. These are hard to anticipate when collecting data and
obvious the moment you see them, which is exactly what this method is for.

**Good for:** Group A precision work on real hardware, where the last few percent
of reliability is the whole problem.
**Status in 2026:** this is how a good policy is made reliable, and the technique
has merged with reinforcement learning — the human's take-overs become the
learning signal. The published numbers are the best in this whole document:
HIL-SERL reached **100% success on every task it was tried on, after one to two
and a half hours of training on the real robot** — seating RAM in a motherboard,
inserting an SSD and a USB connector, clipping a cable, fitting a timing belt,
assembling IKEA panels and a car dashboard — where the strongest imitation
baseline averaged under 50%. That is a peer-reviewed result in *Science Robotics*
rather than a blog post, which is worth noting in a field where most impressive
numbers are self-reported.
**Code to look at:** [the DAgger paper](https://arxiv.org/abs/1011.0686) for the
original argument; [HIL-SERL](https://hil-serl.github.io/)
([repo](https://github.com/rail-berkeley/hil-serl), 1.5k stars) for the modern
system, now shipped inside LeRobot. Its predecessor SERL is formally deprecated
in favour of it.

### 1.3 Learning the goal instead of the motion

Rather than copy what the demonstrator did, infer what they were *trying to
achieve* and optimise that — inverse reinforcement learning, with relatives in
adversarial imitation and learning from preferences.

**Status in 2026: a minority approach for arms.** The generality is real and so
is the fragility, and the flagship open library
([imitation](https://github.com/HumanCompatibleAI/imitation), 1.8k stars) has had
no commits since January 2025, though surveys still treat the family as live. The
preference-learning branch found its real home tuning language models rather than
arms. Read [GAIL](https://arxiv.org/abs/1606.03476) and
[learning from human preferences](https://arxiv.org/abs/1706.03741) for the ideas;
do not expect to meet them in a working arm system.

---

## 2. Learning from trial and error

Reinforcement learning takes the opposite input: instead of demonstrations you
supply a **reward**, a number saying how well things are going, and the robot
tries, observes, and adjusts. The appeal is that you need not be able to do the
task, only to recognise success. The difficulties are that writing a reward is
genuinely hard — any gap between what you wrote and what you meant gets found and
exploited — and that learning from scratch takes millions of attempts, which no
real arm survives, so in practice it means simulation.

Four branches behave differently enough to separate:

**Model-free** (PPO, SAC) learns directly from experience with no model of the
world: simple, general, and hungry. **Model-based** (Dreamer, TD-MPC) learns a
model first and plans or trains inside it: far more sample-efficient, more moving
parts. **Offline** (IQL, CQL) learns from a fixed pile of recorded behaviour with
no practising at all. **Real-world** RL practises on the actual robot, which
solves the fidelity problem and creates every other one.

Crossing from simulation to reality is its own subject, and the dominant
technique is **domain randomisation**: rather than build one accurate simulator,
train across thousands of randomised ones — friction, mass, lighting, delays — so
the real world is one more variation.

The clearest evidence that this works on arms comes from insertion. NVIDIA's
[IndustReal](https://github.com/NVLabs/industrealkit) line trained entirely in
simulation and transferred to a real Franka with no real-world data at all,
reaching 83–99% across 600 trials on parts modelled on a standard assembly test
board, and its successor FORGE improved gear meshing to 98% and nut threading to
69% while halving contact forces. Read the caveats, because they are the
interesting part: the authors deliberately used **no force-torque sensor**,
relying on vision and joint positions, because such sensors are "costly, noisy
and fragile"; the clearances were half a millimetre, which is looser than real
connectors; and none of it is deployed in a factory.

**Two arms make reinforcement learning harder in a way worth understanding.** The
robot learns by trying things at random and keeping what worked, and with two arms
the space of things to try is the product of both arms' possibilities rather than
the sum. Worse, most of the useful two-arm behaviours only pay off when both arms
do the right thing *at the same time* — a handover gives no reward at all unless
one arm has arrived and the other releases at the right moment — so random
exploration almost never stumbles on the behaviour that would earn the reward.
This is the technical reason two-arm systems are usually taught by demonstration
rather than by practice: the demonstration supplies the coordinated behaviour that
exploration cannot find, and practice is then used to polish it.

**Good for:** Group A contact skills you can simulate and score, above all
insertion; and in-hand dexterity generally. For two arms it is most useful as a
*second* stage after demonstrations, rather than on its own.
**Status in 2026, and this has changed recently:** training a policy from scratch
with RL is now the exception. The tooling tells the story — LeRobot ships around
twenty pretrained and imitation policies against two RL entries. What RL is
increasingly used for is **fine-tuning a policy that was first trained from
demonstrations**, which is [section 3](#3-learning-from-large-scale-pretraining).
Offline RL followed the same path: its benchmark suite was formally deprecated,
and its algorithms reappeared as components inside policy post-training.
**One deprecation worth knowing:** Isaac Gym, the GPU simulator many RL papers
used, is officially legacy — NVIDIA's own page says it "is no longer supported"
and points at [Isaac Lab](https://isaac-sim.github.io/IsaacLab/) (8.2k stars,
pushed today). If you meet a tutorial using Isaac Gym, it is out of date.
**Code to look at:** [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
(13.8k) for the algorithms themselves;
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) (2.2k)
for where the practising happens; the
[domain randomisation paper](https://arxiv.org/abs/1703.06907), which is short
and worth reading in full; and [HIL-SERL](https://github.com/rail-berkeley/hil-serl)
for RL on a real arm.

---

## 3. Learning from large-scale pretraining

The newest branch borrows the strategy that worked for language. Rather than
train a model for your task, train one large model on as much robot data as
exists — pooled across many robots and many tasks — then adapt it to your task
with comparatively few examples. These are **vision-language-action models**, or
VLAs: camera images and a sentence in, arm commands out. The instruction is what
lets one model cover many tasks.

**Are these models bimanual? Mostly by accommodation rather than by design, and
the data explains why.** It is tempting to assume that a model trained on
everything has seen plenty of two-arm work. It has not. Open X-Embodiment, the
pooled cross-robot corpus these models were built on, labels just **two of its
seventy-two datasets as bimanual** — about **520 episodes out of 2.4 million,
roughly two hundredths of one percent**. Counting a third, misfiled two-arm
dataset barely changes it. The field's flagship shared corpus is, in effect,
entirely single-armed, and that is the plainest explanation of why two-arm
learning lagged behind single-arm learning.

That history is visible in how the models are built. Most of them define one long
action vector and pad it out to whatever the robot needs, so two arms are an
accommodated special case. One model inverts this: **RDT was designed bimanual
first**, splitting its state vector into a right-arm half and a left-arm half, and
its documentation instructs you that if your robot has one arm you should write
its values into the *right-arm* portion — single-arm as the padded special case,
which is the opposite of everyone else. Its 2026 successor H-RDT continues that
line. It is a good illustration that "supports two arms" and "is built for two
arms" are different claims.

The data situation is now changing quickly, and this is the most useful thing in
this section. Purpose-built two-arm datasets have arrived at a scale the old
pooled corpus never had: AgiBot World, gathered on a dual-arm platform and
published at a major robotics conference; RoboMIND 2.0, which is bimanual by
deliberate design — over **310,000 dual-arm trajectories across 739 tasks and six
platforms**, with even its single-arm robots re-rigged as pairs — and Galaxea's
open dataset of 500-plus hours on one dual-arm platform. If you are training
anything two-armed, these rather than Open X-Embodiment are where the data is.

**Good for:** Groups B and C, and any situation where you want one policy to do
several tasks rather than one policy per task. This is where laundry folding and
household clutter have produced their most convincing demonstrations — all of them
two-armed, because those tasks cannot be done with one arm.
**Status in 2026: the frontier, and moving fast enough that specific model names
date quickly.** Three things are worth knowing rather than any particular model.

First, **what is open and what is not.** The openly released models are π₀,
π₀-FAST and π₀.₅ from [openpi](https://github.com/Physical-Intelligence/openpi)
(13.9k stars, Apache-2.0) and
[GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T) (8.1k), which is the current
version of that line — N1.5 and N1.6 are no longer maintained. The models these
groups have published since, including Physical Intelligence's π\*0.6 and π0.7,
have **no released code or weights**, so read about them but do not plan on using
them.

Check what is *downloadable* rather than what is supported, because for two arms
they differ. GR00T's code carries embodiment definitions for two-armed humanoid
platforms, with separate left-arm and right-arm entries — but every fine-tuned
checkpoint released for it is single-arm. On the openpi side there is a
configuration for the two-armed ALOHA platform with no published checkpoint behind
it. The base models are genuinely usable for two arms; you will usually be
fine-tuning one yourself rather than downloading a two-arm policy someone else
trained.

Second, **the previous generation is already historical.** RT-1 is archived, RT-2
never released code or weights at all, and Octo has had no commits since mid-2024.
[OpenVLA](https://github.com/openvla/openvla) (7.0k) is the interesting case: it
is still the most-downloaded robotics model and the baseline in most papers, yet
it has had no commits since March 2025 and is absent from LeRobot's policy list.
It is a reference point, not a foundation to build on.

Third, **the 2026 recipe for a hard task is a pipeline, not a model**: fine-tune
a pretrained policy on roughly fifty demonstrations, run it with real-time
chunking so a slow model produces smooth motion, and then use a short burst of
reinforcement learning on the real robot to sharpen the precise phase. Physical
Intelligence reported exactly this on tasks from Group A — driving screws,
fitting zip ties, inserting Ethernet and power connectors — with about fifteen
minutes of real-world data and roughly two hours including resets, reaching up to
three times faster execution and beating human teleoperation on one of them. That
work is not released; the open equivalent of its last stage is HIL-SERL inside
LeRobot, and in simulation
[SimpleVLA-RL](https://github.com/PRIME-RL/SimpleVLA-RL) (1.9k, MIT).

That recipe is worth taking seriously because it turned up four separate times in
a single year, from four different groups, on four different tasks: on laundry and
box assembly, on shoe-lacing (where success went from 46% to 83% after about 150
episodes of practice), on precision insertion, and in the winning entry of a
garment-folding competition, which built on the open π₀.₅ and added a
reinforcement-learning loop. When independent groups converge on the same shape
of solution, that shape is the current state of the art.

Fourth, **be careful to separate demonstrations from deployment.** Almost every
headline VLA result is self-reported by the company that trained the model, and
graded on a rubric rather than as a plain success rate. The most useful public
data point is smaller and more honest: a logistics company put a VLA into
production picking for an e-commerce customer in 2026 and reported that it roughly
halved the rate of robot-caused interventions — while stating plainly that their
VLAs are not at 99.9% success on their own, that nobody's customer-deployed VLAs
are, and that a classical stack sits around the model as a "harness" catching its
errors and enforcing safety. That is the accurate picture of VLAs in production
today. The most rigorous evaluation anyone has published, from Toyota Research
Institute in *Science Robotics*, points the same way: across 1,800 real rollouts
and 47,000 simulated ones, large-scale pretraining bought a genuine three-to-five
fold improvement in data efficiency, and yet the pretrained model beat
single-task baselines on only about half the tasks tested — with the authors
warning that much of the field may be measuring statistical noise.

**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) again, which
hosts twenty registered policy types including the open VLAs, plus
[openpi](https://github.com/Physical-Intelligence/openpi) and
[Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) for the models themselves.
For the bimanual-first alternative see [RDT](https://github.com/thu-ml/RoboticsDiffusionTransformer)
and its successor [H-RDT](https://github.com/HongzheBi/H_RDT) (MPL-2.0).

**Data to look at, which matters more here than code.**
[Open X-Embodiment](https://github.com/google-deepmind/open_x_embodiment) is the
famous pooled corpus and is almost entirely single-arm, as above. The two-arm data
is elsewhere: [AgiBot World](https://github.com/OpenDriveLab/AgiBot-World)
(dual-arm platform, published at IROS 2025; note the repository carries no licence
file, and the stated terms live only in the README),
[RoboMIND 2.0](https://arxiv.org/abs/2512.24653) (310,000 dual-arm trajectories,
Apache-2.0, but a preprint with no venue and around 112 TB to download) and
[Galaxea's open dataset](https://arxiv.org/abs/2509.00576) (500-plus hours on one
dual-arm platform, in LeRobot format).

---

## 4. Learned pieces inside a programmed system

The least glamorous branch, and by a wide margin the most deployed. Keep the
classical system — planner, controller, logic — and replace only the parts that
require recognising something.

**Where to grasp.** Given a point cloud of a cluttered bin, a network proposes
places the gripper could close successfully, ranked; a conventional planner
executes the best reachable one. It works on objects the system has never seen,
because the network learned what grippable geometry looks like in general.

**What the object is, and where.** Segmentation says which pixels belong to which
object; pose estimation says how it is oriented. The recent generation does this
without being trained on your specific object, which removed the step that used
to make the approach impractical.

**Whether something will work.** A learned model that scores candidates the
planner generated — will this grasp hold, will this stack stay up — is often the
highest-value learning in a system, because the classical part can generate
thousands of candidates and only needs help choosing.

**The best evidence in this whole document is for this branch.** Amazon published
a detailed account of a system that packs items into fabric storage pods, after
more than half a million real stows in a working fulfilment centre. It reports
**85.86% success over 100,000 attempts**, with the failures broken out honestly —
9.31% unproductive cycles, 3.77% dropped items, 0.24% damage — and a rate of 224
units per hour against 243 for the humans working the same floor. Most usefully,
it says exactly which parts are learned and which are not: **learned** are the
depth estimation, the segmentation, the product identification and the models that
score risk and estimate free space; **classical** are the motion planning, the
grasp planning, the force control and a hand-written library of primitives with
names like "approach", "extend blade", "sweep" and "eject item". That is the
shape of essentially every deployed system that uses machine learning on an arm.

**With two arms, one thing is added and it is not perception itself.** The
networks are the same, and they neither know nor care how many arms will use their
output. What changes is the *choice* made with their output: a grasp proposer
returns many candidate grasps, and with two arms you are choosing which arm takes
which one — whether both can be reached, whether taking this one with the left arm
leaves the right arm able to reach the next, and whether the pair of motions
collide. That selection is ordinary code sitting between the network and the
planner, and it is where most of the two-arm engineering in such a system lives.

**Good for:** Group B above all — this is what made bin picking of mixed items a
product rather than a demo — and the perception layer of Groups C and D.
**Status in 2026:** deployed and mature, and the default way to add learning to a
working system. But note the split carefully, because it is widely got wrong:
**if you know the part, the industry still matches its CAD model**, and the major
3D-vision vendors describe their products in exactly those terms, because a model
match gives a full six-degree-of-freedom pose with a geometric residual you can
check. Learned grasp proposal took over for **unknown or mixed items**, where
there is no model to match. Both are current; which you use is decided by whether
the object is in your catalogue. Either way the system stays inspectable: when it
fails you can look at the proposed grasps, the estimated pose and the planned
path and see which was wrong.

The published numbers for unknown-object picking are strong — AnyGrasp reported
clearing bins of over 300 unseen objects at 93.3% success and more than 900 picks
an hour — but note that **no paper anywhere reports a head-to-head of a general
vision-language-action model against one of these pipelines**. The modular
approach wins here by the absence of a challenger rather than by a measured
victory.

**Code to look at, with a health warning.** This corner of open source has aged
badly and the well-known repositories are mostly frozen:
[Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) (532 stars) has
not been touched since 2024 and depends on a long-dead TensorFlow generation;
[GraspNet-1Billion](https://graspnet.net/) (1.0k) is most valuable as a dataset
and benchmark; Dex-Net and its `gqcnn` implementation have been dead since 2022;
and the one with real commercial traction, AnyGrasp, ships as a licence-gated
binary and is **not open source** despite appearances. Treat these as concepts and
data rather than as things to build on. The current research line is diffusion
models that generate grasps, of which NVIDIA's `GraspGen` is the notable example —
visible source, but under a research licence rather than a permissive one. For the
pieces that are genuinely maintained, use
[FoundationPose](https://github.com/NVlabs/FoundationPose) (3.6k) for pose
estimation without per-object training and
[Segment Anything](https://github.com/facebookresearch/segment-anything) (54.9k)
for segmentation.

---

## 5. Directed by language

The last branch does not produce motion at all: it chooses what to do, sitting
above whatever does produce motion. A language model is given the task in words,
told what skills the robot has, and asked to decide the order of the steps.

This works better than it sounds, because sequencing a familiar task is a
knowledge problem rather than a physical one, and knowledge is what a model
trained on the internet has. What it does not know is what this particular robot
can reach, which is why the useful designs pair its suggestions with the robot's
own estimate of whether each step is achievable and let the two vote.

Three shapes are worth knowing. The model can **propose steps** that learned
skills execute; it can **write code** that calls the robot's perception and
control functions, which is pleasantly debuggable because the output is a short
program you can read; or it can **produce spatial goals** that a conventional
planner uses.

**With two arms** the interesting possibility is that the model also assigns the
roles — deciding that the left arm should hold the bag while the right arm fills
it, rather than a person writing that down. Of the three shapes, the code-writing
one fits two arms best, because a short program can say plainly which arm does
what and in which order, and you can read it and check it. Treat this as a
promising direction rather than as how systems are built today: role assignment in
working two-arm systems is written by hand, as
[the overview](overview.md#5-the-layers-of-a-two-arm-system) says.

**Good for:** the sequencing layer of long tasks in Groups B, C and D —
especially household-style work where the instruction varies. For Group A, where
the sequence is fixed and known, a behaviour tree remains the better answer: it
is deterministic and free.
**Status in 2026:** established in research, appearing in products for
high-level task selection rather than for anything safety-critical. The
sequencing layer is also being absorbed into the large policies themselves, which
take an instruction directly.
**Code to look at:** [SayCan](https://say-can.github.io/),
[Code as Policies](https://code-as-policies.github.io/) and
[VoxPoser](https://voxposer.github.io/) for the three shapes;
[Inner Monologue](https://innermonologue.github.io/) for feeding failures back so
the model can replan.
