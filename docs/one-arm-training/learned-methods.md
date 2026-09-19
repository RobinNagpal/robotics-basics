# Learned methods for one arm

These are the methods where the behaviour comes from data rather than from someone
writing it down — from demonstrations, from the robot's own practice, or from a
large pool of data gathered elsewhere. They cope with variety, they need a great
deal of data, and they cannot tell you why they failed.

Read [the overview](overview.md) first if you have not, and ideally
[the programmed methods](programmed-methods.md) too, because almost everything
here is best understood as a replacement for one specific part of that stack.

Each method below says which tasks it suits, what its status is in 2026,
**whether it is worth your time to learn right now**, and which open code to look
at. The task group letters — A to D — are from
[the overview's task catalogue](overview.md#1-what-an-arm-is-actually-asked-to-do).

**A warning about numbers before you start.** Robotics reporting is unusually
unreliable. Company blog posts quote success rates without saying how many trials
they ran; papers quote an average that hides the task where the method failed
completely; demonstration videos are edited. Throughout this document, where a
number has a trial count attached it is because the source published one, and
where it does not, that absence is itself the finding. Get into the habit of
looking for the denominator.

## Contents

1. [Learning from demonstrations](#1-learning-from-demonstrations)
2. [Learning from trial and error](#2-learning-from-trial-and-error)
3. [Learning from large-scale pretraining](#3-learning-from-large-scale-pretraining)
4. [Learned pieces inside a programmed system](#4-learned-pieces-inside-a-programmed-system)
5. [Directed by language](#5-directed-by-language)
6. [What to take from all five](#6-what-to-take-from-all-five)

---

## 1. Learning from demonstrations

Show the task repeatedly and let the learner copy what you did. This is the most
practical learning method for arms today, and the one to start with.

### 1.1 Behaviour cloning

A person performs the task — usually by driving the robot directly — while the
cameras, the joint angles and the commands they gave are all recorded. A network
is then trained to produce the command the person gave, given what the cameras
saw. Nothing about the task is described to it: not the objects, not the goal, not
the physics, not even that there is a gripper.

The naive version of this has been tried since the 1990s and works poorly, and the
reason is worth understanding because it explains the fixes. Asked for one command
per camera frame, the network is queried perhaps fifty times a second. Each answer
is a fresh chance to be slightly wrong. A slightly wrong command puts the arm in a
position slightly unlike anything in the training data, where the next answer is a
little worse, and within a second or two the arm is somewhere no demonstrator ever
took it and the network has no idea what to do. This is called **compounding
error**, and it is the central problem of the whole approach.

![How copying drifts, and what the two standard fixes do](../images/one-arm-training/learned-methods/compounding-error.svg)

Two developments fixed it enough to matter.

**Action chunking**: instead of predicting the next command, predict the next
hundred, and play them all out before looking again. The argument is arithmetic —
playing out *k* commands per decision cuts the number of decisions in a task by a
factor of *k*, and compounding error grows with the number of decisions. The
effect is large: the ACT paper's own ablation goes from **1% success predicting
one action at a time to 44% predicting a hundred**, then falls off again beyond
that as the policy stops reacting to what it can see. (That is an average over
simulated tasks rather than a real-robot number.) The trade is visible in that
curve: longer chunks mean less compounding error and slower reactions, and the
best chunk length is a property of your task.

**Generative action models**: demonstrators are inconsistent. Ask five people to
reach around an obstacle and some go left, some go right. A network trained to
output one number per command will average those, and the average of going left
and going right is going straight through the obstacle. **Diffusion policies**
generate the whole action sequence the way image models generate pictures, which
lets them represent "either this motion or that one" rather than collapsing to the
mean. In 2026 the same job is usually done by **flow matching**, a faster relative
of diffusion, which is the action head inside essentially every current large
policy.

It is worth knowing that this is not a settled question. A 2026 study
([MINERVA](https://arxiv.org/abs/2609.03715)) found that flow matching gave no
detectable advantage over plain regression on its benchmarks, while being several
times slower to run. The field is optimising a design choice it has not fully
justified, which is a useful thing to know before you assume the complicated
option is the right one.

**Where it stops.** Copying works for one skill and falls apart over a long
sequence. FurnitureBench, a benchmark of real IKEA-furniture assembly, is the
honest yardstick here: behaviour cloning and offline reinforcement learning
complete none of its full assemblies except the very simplest one, and the
insertion and screwing stages mostly fail outright. A twenty-step job needs
something above the policy that sequences and recovers — which is why the
programmed methods have not gone anywhere, and why
[section 5](#5-directed-by-language) exists.

**Good for:** the contact-heavy parts of Group A, and Groups C and D where no model
of the object exists and therefore nothing can be planned.
**Status in 2026:** the default first thing to try for a new learned task.
LeRobot's own documentation calls ACT "our recommended first policy", and that is
about cost as much as quality — it trains in under an hour on a single consumer
GPU where a large pretrained policy takes a day.
**Worth learning now?** Yes, and this is the one to start with. It is the cheapest
learned method to actually run end to end, it needs no simulator and no reward
function, and going once around the loop — collect, train, evaluate, collect more —
teaches you more about why learned robotics is hard than any amount of reading.

**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) (27.6k
stars, Apache-2.0, actively developed) is where all of this now lives and is the
right starting point. The original implementations are historical rather than
current — [ACT](https://github.com/tonyzhaozh/act) (2.2k stars) has had no commits
since 2024, and
[diffusion_policy](https://github.com/real-stanford/diffusion_policy) (4.6k) is
the reference implementation everyone cites and nobody develops. Neither is
archived and both methods are actively maintained inside LeRobot, so "the original
codebases are dormant" is fairer than "abandoned". Use LeRobot's versions.
[robomimic](https://github.com/ARISE-Initiative/robomimic) (1.6k) remains the
careful study of which implementation details actually matter, and is worth
reading before you blame your data for a result that is really a hyperparameter.

### 1.2 Interactive imitation: correcting it as it goes

Behaviour cloning has the structural flaw described above: the policy only ever
saw states that a competent demonstrator put the robot in, so its own small
mistakes take it somewhere unfamiliar. The fix is direct — let the policy drive,
and correct it when it goes wrong, adding those corrections to the training data.

The reason this works so much better than collecting more demonstrations is that
the corrections cover exactly the situations the policy actually reaches, rather
than the situations a skilled human would have reached. A few dozen corrections
are often worth several hundred fresh demonstrations.

**Good for:** Group A precision work on real hardware, where the last few percent
of reliability is the entire problem.
**Status in 2026:** this is how a good policy is made into a reliable one, and the
technique has merged with reinforcement learning — the human's take-overs become
the learning signal rather than just extra data.

The published numbers here are the strongest in this whole document. HIL-SERL
reached **100% success on every task it was tried on, after one to two and a half
hours of training on the real robot** — seating RAM in a motherboard, inserting an
SSD and a USB connector, clipping a cable, fitting a timing belt, assembling IKEA
panels and a car dashboard — where the strongest imitation baseline averaged under
50%. That is a peer-reviewed result in *Science Robotics*, which is worth noting
in a field where most impressive numbers are self-reported by the company that
produced them.

**Worth learning now?** Yes, as the second thing after behaviour cloning. The
pattern "train a mediocre policy, then fix it interactively" is the most
practically useful recipe in current robot learning, and it is one of the few
places where the published results are strong enough to plan around.

**Code to look at:** [the DAgger paper](https://arxiv.org/abs/1011.0686) for the
original argument, which is short; [HIL-SERL](https://hil-serl.github.io/)
([repo](https://github.com/rail-berkeley/hil-serl), 1.5k stars) for the modern
system, now shipped inside LeRobot. Its predecessor SERL is formally deprecated in
favour of it, so ignore tutorials that use it.

### 1.3 Learning the goal instead of the motion

Rather than copy what the demonstrator did, infer what they were *trying to
achieve* and then optimise for that. This is **inverse reinforcement learning**,
with relatives in adversarial imitation and learning from stated preferences. The
appeal is generality: a learned goal transfers to situations a copied motion
cannot.

**Status in 2026: a minority approach for arms.** The generality is real and so is
the fragility, and the flagship open library
([imitation](https://github.com/HumanCompatibleAI/imitation), 1.8k stars) has had
no commits since January 2025, though surveys still treat the family as live. The
preference-learning branch found its real home tuning language models rather than
robot arms.
**Worth learning now?** No. Read [GAIL](https://arxiv.org/abs/1606.03476) and
[learning from human preferences](https://arxiv.org/abs/1706.03741) for the ideas,
which are genuinely good ideas, but do not expect to meet them in a working arm
system.

---

## 2. Learning from trial and error

Reinforcement learning takes the opposite input. Instead of demonstrations you
supply a **reward** — a number saying how well things are going — and the robot
tries something, observes the result, and adjusts. The appeal is that you need not
be able to do the task yourself, only to recognise success.

Two difficulties are serious. Writing a reward is genuinely hard, because any gap
between what you wrote and what you meant will be found and exploited; the
literature is full of robots that learned to knock the target over rather than
reach it, because the reward measured distance rather than contact. And learning
from scratch takes millions of attempts, which no real arm survives — so in
practice reinforcement learning means simulation, which means a new problem, which
is that the simulation is not the world.

Four branches behave differently enough to be worth separating. **Model-free**
methods (PPO, SAC) learn directly from experience with no model of the world:
simple, general and hungry. **Model-based** methods (Dreamer, TD-MPC) learn a model
first and then plan or train inside it: far more sample-efficient, with many more
moving parts. **Offline** methods (IQL, CQL) learn from a fixed pile of recorded
behaviour with no practising at all. **Real-world** reinforcement learning
practises on the actual robot, which solves the fidelity problem and creates every
other one.

Crossing from simulation to reality is its own subject, and the dominant technique
is **domain randomisation**: rather than build one accurate simulator, train across
thousands of randomised ones — varying friction, mass, lighting, camera position,
control delays — so that the real world is simply one more variation the policy has
already coped with. The [original paper](https://arxiv.org/abs/1703.06907) is short
and worth reading in full.

**The clearest evidence that this works on arms comes from insertion.** NVIDIA's
[IndustReal](https://github.com/NVLabs/industrealkit) line trained entirely in
simulation and transferred to a real Franka arm with no real-world data at all,
reaching **83–99% across 600 trials** on parts modelled on a standard assembly test
board; its successor FORGE improved gear meshing to 98% and nut threading to 69%
while halving contact forces. Read the caveats, because they are the interesting
part. The authors deliberately used **no force-torque sensor**, relying on vision
and joint positions, on the grounds that such sensors are "costly, noisy and
fragile". The clearances were half a millimetre, which is looser than a real
electrical connector. And none of it is deployed in a factory.

**Good for:** Group A contact skills that you can simulate and score, above all
insertion, and in-hand dexterity generally.
**Status in 2026, and this has changed recently:** training a policy from scratch
with reinforcement learning is now the exception rather than the rule. The tooling
tells the story — LeRobot ships around twenty pretrained and imitation policies
against two reinforcement-learning entries. What reinforcement learning is
increasingly used for is **fine-tuning a policy that was first trained from
demonstrations**, which is [section 3](#3-learning-from-large-scale-pretraining).
Offline reinforcement learning followed the same path: its benchmark suite was
formally deprecated, and its algorithms reappeared as components inside policy
post-training.

**One deprecation worth knowing:** Isaac Gym, the GPU simulator behind a great many
reinforcement-learning papers, is officially legacy — NVIDIA's own page says it "is
no longer supported" — and [Isaac Lab](https://isaac-sim.github.io/IsaacLab/) (8.2k
stars) replaced it. If you meet a tutorial using Isaac Gym, it is out of date.

**Worth learning now?** Learn what it is and when it applies, and learn the
fine-tuning use specifically. Learning to train from scratch is a substantial
investment — a simulator, a reward, a GPU budget — for a technique the field itself
is using less each year.

**Code to look at:**
[Stable-Baselines3](https://stable-baselines3.readthedocs.io/) (13.8k) for the
algorithms themselves, which is the cleanest place to actually understand them;
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) (2.2k) for
where the practising happens; and
[HIL-SERL](https://github.com/rail-berkeley/hil-serl) for reinforcement learning on
a real arm, which is the branch most likely to be useful to you.

---

## 3. Learning from large-scale pretraining

The newest branch borrows the strategy that worked for language. Rather than train
a model for your task, train one large model on as much robot data as exists —
pooled across many robots and many tasks — and then adapt it to your task with
comparatively few examples. These are **vision-language-action models**, or VLAs:
camera images and a sentence go in, arm commands come out. The sentence is what
lets one model cover many tasks instead of one.

The bet behind this is that manipulation has shared structure the way language
does, so that a model which has seen a million pick-and-places on other robots
starts your task already knowing what a gripper approaching an object looks like.
Whether that bet pays off is now partly measurable, and the answer is a qualified
yes: the most rigorous public evaluation, from Toyota Research Institute in
*Science Robotics*, ran **1,800 real rollouts and 47,000 simulated ones** and found
that large-scale pretraining bought a genuine **three-to-five-fold improvement in
data efficiency** — and yet the pretrained model beat single-task baselines on only
about half the tasks tested. The authors' own warning is the part to remember:
much of the field may be measuring statistical noise.

**Status in 2026: the frontier, and moving fast enough that specific model names
date quickly.** Four things are worth knowing rather than any particular model.

**First, what is open and what is not.** The openly released models are π₀, π₀-FAST
and π₀.₅ from [openpi](https://github.com/Physical-Intelligence/openpi) (13.9k
stars, Apache-2.0) and [GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T) (8.1k),
which is the current version of that line — N1.5 and N1.6 are no longer maintained.
The models these same groups have published *since*, including Physical
Intelligence's π\*0.6 and π0.7, have **no released code or weights**, so read about
them but do not plan on using them. This gap between what is announced and what is
downloadable is the single most common way to waste a month in this area.

**Second, the previous generation is already historical.** RT-1 is archived, RT-2
never released code or weights at all, and Octo has had no commits since mid-2024.
[OpenVLA](https://github.com/openvla/openvla) (7.0k) is the interesting case: it is
still the most-downloaded robotics model and the baseline in most papers, yet it
has had no commits since March 2025 and is absent from LeRobot's policy list. Treat
it as a reference point, not a foundation to build on.

**Third, the 2026 recipe for a hard task is a pipeline, not a model.** Fine-tune a
pretrained policy on roughly fifty demonstrations; run it with real-time chunking
so that a slow model still produces smooth motion; then use a short burst of
reinforcement learning on the real robot to sharpen the precise phase. Physical
Intelligence reported exactly this on Group A tasks — driving screws, fitting zip
ties, inserting Ethernet and power connectors — with about fifteen minutes of
real-world data and roughly two hours including resets, reaching up to three times
faster execution and beating human teleoperation on one of them.

That recipe is worth taking seriously because it turned up four separate times in a
single year, from four different groups, on four different tasks: on laundry and
box assembly, on shoe-lacing (where success went from 46% to 83% after about 150
episodes of practice), on precision insertion, and in the winning entry of a
garment-folding competition. When independent groups converge on the same shape of
solution, that shape is the current state of the art. The Physical Intelligence
work is not released; the open equivalent of its last stage is HIL-SERL inside
LeRobot, and in simulation
[SimpleVLA-RL](https://github.com/PRIME-RL/SimpleVLA-RL) (1.9k, MIT).

**Fourth, be careful to separate demonstrations from deployment.** Almost every
headline VLA result is self-reported by the company that trained the model, and
graded on a rubric rather than as a plain success rate. The most useful public data
point is smaller and more honest: a logistics company put a VLA into production
picking for an e-commerce customer in 2026 and reported that it roughly halved the
rate of robot-caused interventions — while stating plainly that their VLAs are not
at 99.9% success on their own, that nobody's customer-deployed VLAs are, and that a
classical stack sits around the model as a "harness" catching its errors and
enforcing safety. That is the accurate picture of VLAs in production today, and it
is a much better thing to have in your head than any leaderboard.

**Good for:** Groups B and C, and any situation where you want one policy to do
several tasks rather than one policy per task.
**Worth learning now?** Yes to fine-tuning one, no to training one. Fine-tuning an
open checkpoint on your own small dataset is a realistic weekend-to-fortnight
project and is exactly the skill that distinguishes someone who has done this from
someone who has read about it. Pretraining your own is a research programme with a
six-figure compute bill.

**Code to look at:** [LeRobot](https://github.com/huggingface/lerobot) again, which
hosts twenty registered policy types including the open VLAs, plus
[openpi](https://github.com/Physical-Intelligence/openpi) and
[Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) for the models themselves.

**Data to look at, which matters more here than code.**
[Open X-Embodiment](https://github.com/google-deepmind/open_x_embodiment) is the
famous pooled corpus — 2.4 million episodes across 72 datasets — and is what the
first generation of these models was built on. Its composition is worth knowing
before you assume a model has seen what you need: it is almost entirely single-arm,
and heavily weighted towards a handful of large contributors.

---

## 4. Learned pieces inside a programmed system

The least glamorous branch, and by a very wide margin the most deployed. Keep the
classical system — planner, controller, logic, all of
[the programmed methods](programmed-methods.md) — and replace only the parts that
require *recognising* something.

**Where to grasp.** Given a point cloud of a cluttered bin, a network proposes
places the gripper could close successfully, ranked by confidence; a conventional
planner then executes the best one it can reach. This works on objects the system
has never seen, because the network learned what grippable geometry looks like in
general rather than what your particular product looks like.

**What the object is, and where.** Segmentation says which pixels belong to which
object; pose estimation says how it is oriented. The recent generation does both
without being trained on your specific object, which removed the step that used to
make the approach impractical for anyone with more than ten products.

**Whether something will work.** A learned model that scores candidates the
classical planner generated — will this grasp hold, will this stack stay up — is
often the highest-value learning in a system, because the classical part can cheaply
generate thousands of candidates and only needs help choosing between them.

**The best evidence in this whole document is for this branch.** Amazon published a
detailed account of a system that packs items into fabric storage pods, after more
than half a million real stows in a working fulfilment centre.

![Which stages of a deployed system are networks, and which are ordinary code](../images/one-arm-training/learned-methods/what-is-learned.svg)
 It reports **85.86%
success over 100,000 attempts**, with the failures broken out honestly — 9.31%
unproductive cycles, 3.77% dropped items, 0.24% damage — and a rate of 224 units
per hour against 243 for the humans working the same floor. Most usefully for
someone trying to learn the shape of these systems, it says exactly which parts are
learned and which are not. **Learned:** depth estimation, segmentation, product
identification, and the models that score risk and estimate free space.
**Classical:** motion planning, grasp planning, force control, and a hand-written
library of primitives with names like "approach", "extend blade", "sweep" and
"eject item". That is the shape of essentially every deployed system that uses
machine learning on an arm.

**Good for:** Group B above all — this is what turned bin picking of mixed items
from a demo into a product — and the perception layer of Groups C and D.
**Status in 2026:** deployed and mature, and the default way to add learning to a
working system.

But note one split carefully, because it is widely got wrong. **If you know the
part, the industry still matches its CAD model.** The major 3D-vision vendors
describe their products in exactly those terms, because a model match gives you a
full six-degree-of-freedom pose together with a geometric residual you can check
and threshold. Learned grasp proposal took over for **unknown or mixed items**,
where there is no model to match. Both are current in 2026, and which you use is
decided by whether the object is in your catalogue, not by which is more modern.

Either way the system stays inspectable: when it fails you can look at the proposed
grasps, the estimated pose and the planned path, and see which one was wrong. That
is why this pattern is deployed and the end-to-end one mostly is not.

The published numbers for unknown-object picking are strong — AnyGrasp reported
clearing bins of over 300 unseen objects at 93.3% success and more than 900 picks
an hour — but note that **no paper anywhere reports a head-to-head of a general
vision-language-action model against one of these pipelines**. The modular approach
wins here by the absence of a challenger rather than by a measured victory.

**Worth learning now?** Yes — and if you are looking for paid work rather than
research, this is very likely the most valuable section in this document. It is
what customers actually buy, it is inspectable enough to sell to people who need to
certify things, and it sits on top of skills (planning, calibration, control) that
transfer between jobs.

**Code to look at, with a health warning.** This corner of open source has aged
badly and the well-known repositories are mostly frozen:
[Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) (532 stars) has not
been touched since 2024 and depends on a long-dead TensorFlow generation;
[GraspNet-1Billion](https://graspnet.net/) (1.0k) is most valuable now as a dataset
and benchmark; Dex-Net and its `gqcnn` implementation have been dead since 2022;
and the one with real commercial traction, AnyGrasp, ships as a licence-gated binary
and is **not open source** despite appearances. Treat these as concepts and data
rather than as things to build on. The current research line is diffusion models
that generate grasps, of which NVIDIA's `GraspGen` is the notable example — visible
source, but under a research licence rather than a permissive one.

For the pieces that are genuinely maintained, use
[FoundationPose](https://github.com/NVlabs/FoundationPose) (3.6k) for pose
estimation without per-object training, and
[Segment Anything](https://github.com/facebookresearch/segment-anything) (54.9k) for
segmentation.

---

## 5. Directed by language

The last branch does not produce motion at all. It chooses what to do, sitting
above whatever does produce motion. A language model is given the task in words,
told what skills the robot has, and asked to decide the order of the steps.

This works better than it sounds, because sequencing a familiar task is a knowledge
problem rather than a physical one, and knowledge is exactly what a model trained
on the internet has. What it does not have is any idea what this particular robot
can reach, which is why the useful designs pair its suggestions with the robot's own
estimate of whether each step is achievable, and let the two vote.

Three shapes are worth knowing. The model can **propose steps** that learned skills
then execute; it can **write code** that calls the robot's perception and control
functions, which is pleasantly debuggable because the output is a short program you
can read before running; or it can **produce spatial goals** that a conventional
planner turns into motion.

**Good for:** the sequencing layer of long tasks in Groups B, C and D, especially
household-style work where the instruction varies. For Group A, where the sequence
is fixed and known, a behaviour tree remains the better answer — it is
deterministic, free, and you can prove what it will do.
**Status in 2026:** established in research, and appearing in products for
high-level task selection rather than for anything safety-critical. The sequencing
job is also being absorbed into the large policies themselves, which take an
instruction directly.
**Worth learning now?** Worth understanding; not worth specialising in. The shape
of this is changing fast and the part that will still be true in two years is the
principle — that a model which knows what to do still needs something that knows
what is possible.

**Code to look at:** [SayCan](https://say-can.github.io/),
[Code as Policies](https://code-as-policies.github.io/) and
[VoxPoser](https://voxposer.github.io/) for the three shapes respectively, and
[Inner Monologue](https://innermonologue.github.io/) for feeding failures back so
the model can replan.

---

## 6. What to take from all five

**The deployed learning is modular, and the end-to-end learning is research.**
Section 4 has the best evidence in this document and gets the least attention;
section 3 has the most attention and the weakest evidence. That is not an argument
against section 3 — it is where the field is going — but it should shape what you
build first.

**Demonstrations are the cheap input and rewards are the expensive one.** If you
can do the task, copy it. Reinforcement learning earns its keep as a second stage
that polishes a demonstrated policy, and increasingly not as a first stage at all.

**The published recipe that four independent groups converged on** — pretrain,
fine-tune on ~50 demonstrations, then a short burst of real-robot reinforcement
learning — is the most useful single thing in this document to remember, because it
tells you what the pieces are for.

**Every learned method needs the programmed stack underneath it.** The policy
outputs positions and something has to turn them into safe motion; the policy fails
and something has to catch it. The logistics company that put a VLA into production
called that surrounding classical code a "harness", which is the right word.

Next: back to [the overview](overview.md), or on to
[what changes with two arms](../two-arm-training/overview.md).
