# Where manipulation data comes from, and what changed in 2026

A robot manipulation policy is a function from pictures to motor commands, and
somebody has to supply the examples it is fitted to. Almost every other question
in this field — which architecture, which simulator, which arm — has several
workable answers. The question of where the examples come from has, until very
recently, had one workable answer: a person drove the robot by hand, one episode
at a time, for a week. That is the constraint this document is about, and 2026 is
the year several routes round it stopped being papers and started being things
you can download.

This is the *events* document for data. It says what was released, when, by whom,
on what terms, and what it can and cannot do. The mechanism behind the events —
why the field moves the way it does, and how to judge a new announcement — is in
[what is changing](../10_one-arm-training/05_what-is-changing.md), which is worth
reading first if you want the reasoning rather than the record. Overlap with it
is deliberate and small: that document explains why the field moves, and this one
records what moved.

## Who this is for, and what it is for

This is written for someone who understands what an imitation-learning
demonstration is, and who now has to decide where to get several hundred or
several thousand of them. You do not need to have trained a policy. Every term is
explained where it first appears.

Three commitments shape it. They are the same commitments the
[object perception area](../06_object-perception/01_overview.md) makes, adapted
to a subject where the artefact in question is a pile of recordings rather than a
model.

Every item carries a maturity label, because robotics reporting routinely blurs
the difference between a thing you can buy, a thing you can download, a thing
somebody filmed once, and a press release. Section 2 defines the five labels.

Every licence was read from the project's own licence file or its dataset card,
never from a badge, a blog post or a paper. In this area that matters more than
anywhere else in the repo, because a dataset licence is as capable of stopping
your product as a code licence, and several of the largest and most attractive
corpora are not usable commercially. Section 6.5 lists the ones that will catch
you out.

Every number says what it was measured under, and in particular what one
"demonstration" or one "episode" meant in the dataset that reports it. Section
2.1 explains why that unit is not comparable between datasets, and why almost
every league table of dataset sizes you will see is therefore meaningless.

## Contents

1. [Why data is the binding constraint](#1-why-data-is-the-binding-constraint)
2. [How to read the numbers on this page](#2-how-to-read-the-numbers-on-this-page)
3. [Teleoperation rigs, and the collapse in their price](#3-teleoperation-rigs-and-the-collapse-in-their-price)
4. [Handheld grippers: collecting without a robot](#4-handheld-grippers-collecting-without-a-robot)
5. [Exoskeletons, gloves and ambient capture](#5-exoskeletons-gloves-and-ambient-capture)
6. [The open datasets, and their licences](#6-the-open-datasets-and-their-licences)
7. [LeRobot, and the tooling that grew round it](#7-lerobot-and-the-tooling-that-grew-round-it)
8. [Human video instead of teleoperation](#8-human-video-instead-of-teleoperation)
9. [Data scaling laws, and what they actually say](#9-data-scaling-laws-and-what-they-actually-say)
10. [Making demonstrations instead of collecting them](#10-making-demonstrations-instead-of-collecting-them)
11. [What changed between May and September 2026](#11-what-changed-between-may-and-september-2026)
12. [What none of this fixes](#12-what-none-of-this-fixes)

---

## 1. Why data is the binding constraint

A large language model is fitted to text that already existed. Nobody wrote the
internet in order to train one. A manipulation policy is fitted to recordings of
a robot being moved through a task, and those recordings did not exist before
somebody decided to make them. There is no found corpus. Every episode was paid
for in somebody's time.

The size of the gap is easy to state. [Open
X-Embodiment](https://robotics-transformer-x.github.io/), the pooled corpus that
the field treats as its largest public asset, was assembled by merging sixty
existing datasets from 34 laboratories, and its live index now lists 72 member
datasets totalling 2,419,193 episodes across 27 distinct robots. A single modern
language-model pretraining run consumes text on a scale that is not usefully
comparable. The whole of public robot manipulation data, pooled from every
laboratory willing to contribute, is a rounding error next to what the adjacent
fields consider a starting point.

That shortage is what every development in this document is a response to. There
are only five routes round it, and the rest of the document is organised by them.

- Make the robot rig cheaper, so more people collect. That is section 3.
- Remove the robot from collection entirely, and record a person holding an
  instrumented gripper. That is section 4.
- Record the person's own body instead, with an exoskeleton, a glove or a room
  full of cameras. That is section 5.
- Pool what exists, publish it, and standardise the format so it can be pooled.
  That is sections 6 and 7.
- Stop collecting and start generating, either from video of people doing the
  task, or from a simulator. That is sections 8 and 10.

Section 9 is the question that decides how much any of it is worth: whether more
data reliably buys more capability, and at what rate.

## 2. How to read the numbers on this page

### 2.1 What a "demonstration" means, and why the counts do not compare

Every dataset in this document reports a number of episodes, demonstrations,
trajectories or hours. Those units are not the same thing, and even within one
unit the underlying object differs enough that arithmetic across datasets is
meaningless. Three examples make the point.

In the ALOHA simulation tasks that most people start with, one episode is one
continuous recording of a
two-armed robot performing one short task from a randomised start, typically
around twenty seconds, recorded at 50 Hz with the leader-arm command stored as
the action. Fifty of those is a working dataset for that task.

In [ABC-130K](https://arxiv.org/abs/2606.27375), released in June 2026, one
episode is also a continuous teleoperated recording, but the corpus holds 3,553
hours over 134,806 episodes across 195 tasks — a mean of about 95 seconds. The
mean hides the important part. Individual episodes run from about 7 seconds for
"put the screwdriver in the bin" to 469 seconds for "folding t-shirt pile and
stacking", a sixty-seven-fold spread *inside one dataset*. An episode there is a
whole task attempt of whatever length the task took.

In [YUBI](https://arxiv.org/abs/2606.10244), released the same month, one episode
is a recording made by a person holding a gripper with no robot in the room, and
the corpus reports 8,434 hours over 1.20 million episodes — about 25 seconds
each. Those episodes contain no robot joint angles at all, because there was no
robot; they contain a six-degree-of-freedom end-effector pose recovered from
tracking, plus a gripper width.

In AIRoA MoMa 5k, released in July 2026, one episode is not a task at all. It is
a single *primitive action*, a sub-step of a task, kept independently
addressable with metadata pointing back at the task it came from. The corpus
reports 1,184,259 episodes over 5,025 hours, which is about 15 seconds each.
Comparing that episode count with ABC-130K's is a six-fold unit error before any
other consideration.

So one figure counts robot joint trajectories, one counts whole task attempts,
one counts human hand trajectories no robot has ever executed, and one counts
fragments of tasks. A "1.2 million episodes" headline conceals all of that.
Whenever this document quotes a count, it says what the unit contained.

The other trap is that hours and episodes measure different things and are often
quoted interchangeably. Hours measure how long somebody was working. Episodes
measure how many attempts exist. A corpus of long episodes has fewer resets, and
resets are where the diversity comes from, so hours flatter a dataset whose
episodes are long. Where both are published, this document gives both.

### 2.2 The five maturity labels

Every item below carries one of five labels. They are in descending order of how
much you can actually do with the thing today.

The table reads as a promise about what you can do this afternoon, not as a
quality judgement. A paper-only result can be more important than a shipped
product.

| Label | What it means |
| --- | --- |
| **Shipped** | You can buy it today, at a published price, from a named seller |
| **Downloadable** | You can obtain the files today; the licence is always named alongside |
| **Demonstrated** | It has been shown working, but no code, hardware or data release exists |
| **Paper only** | A result exists in a paper with no artefact of any kind released |
| **Announced** | It has been described publicly and is not yet obtainable by anyone outside the group that made it |

A thing can carry two labels for two of its parts, and several do. The most
common pattern in 2026 is a dataset that is downloadable while the rig that
produced it is proprietary.

## 3. Teleoperation rigs, and the collapse in their price

### 3.1 ALOHA, and what it made ordinary

Before 2023, collecting fine bimanual manipulation data meant high-end arms,
accurate sensors and careful calibration, which in practice meant a funded
laboratory.

[ALOHA](https://arxiv.org/abs/2304.13705) changed the shape of the problem. Its
claim was that a low-cost puppeteering rig, paired with a policy called Action
Chunking with Transformers, learned six genuinely fine tasks — opening a
translucent condiment cup, slotting a battery — at 80 to 90 per cent success from
about ten minutes of demonstrations each.

The mechanism is direct joint-to-joint puppeteering. Two full-size follower arms
are driven by two smaller leader arms that the operator holds, one in each hand,
with four cameras recording. The operator's hands are doing the task; the robot
copies. That is why a person can control fourteen joints at once, which no
gamepad or keyboard scheme achieves.

It matters because it set the default recipe that everything since has reacted
to, and because the data it produced is what most people's first policy is
trained on.

What it cannot do is move, feel or scale. The original is bolted to a table, has
no force feedback, and the ten-minute figure is for six narrow tasks in the room
where the data was collected. [Mobile ALOHA](https://arxiv.org/abs/2401.02117)
added a wheeled base with the operator physically tethered to it, and reported
that co-training on the existing stationary corpus raised mobile task success by
up to 90 per cent from 50 demonstrations per task — a best case across tasks
rather than an average. [ALOHA 2](https://arxiv.org/abs/2405.02292) redesigned the
gripper and frame for durability and published the designs plus a MuJoCo model
with system identification, which is the part most people now use. That tech
report gives no reliability numbers of its own. The original ALOHA's dollar cost
is widely quoted at around twenty thousand and does not appear in the paper; this
document will not repeat a figure it could not source.

### 3.2 The hundred-dollar arm

Before the community hardware line, "low cost" in this field meant five figures.

What changed is [SO-101](https://github.com/TheRobotStudio/SO-ARM100), designed by
The Robot Studio with Hugging Face, whose own bill of materials prices a complete
leader-and-follower pair at **$229.88** in the United States or **€226.30** in
Europe, excluding 3D printing. A follower arm on its own is $121.94. Individual
servos are $13.89.

The mechanism is the same leader-follower puppeteering ALOHA used, built from
Feetech STS3215 servos instead of industrial hardware. The interesting detail is
the gearing. The follower uses 1/345 reduction throughout. The leader mixes
ratios — 1/191 on shoulder pan and elbow, 1/345 on shoulder lift, 1/147 on the
wrist and gripper — so that the leader holds its own weight against gravity while
still being easy to push around by hand. That single choice is why the rig is
usable for an hour rather than a few minutes.

It matters because the price of the rig stopped being the reason not to collect
data. A person can own a two-armed demonstration setup for the price of a games
console, and the data lands directly in the format section 7 describes.

Three things it cannot do. The structure is 3D-printed plastic, so the payload is
around a kilogram and a half at best. There is no force feedback and no torque
sensing, so the leader arm is position-only and the operator feels nothing of the
contact. And availability is the real constraint rather than price: of the two
vendors whose prices I could read on 23 September 2026 — Seeed Studio at $200 and
WowRobo at $199 — both listed every variant as out of stock. Its maturity is
**Downloadable** under Apache-2.0 for the designs, and **Shipped** through
third-party kit vendors when they have stock.

Two relatives are worth a line. SO-100 is the previous version and its own
repository marks it deprecated, though a large installed base and many published
datasets still use it. [LeKiwi](https://github.com/SIGRobotics-UIUC/LeKiwi) puts
an SO-arm on a three-wheel omnidirectional base with a Raspberry Pi 5, priced in
its own bill of materials at $482 for the complete 12-volt robot; its stated
limitation is that keyboard base control needs a global key backend and therefore
does not work on Wayland or on a headless Linux machine. XLeRobot combines two
SO-101 arms with a LeKiwi base for a stated $660 total.

### 3.3 What a full rig costs today

Prices in this field are quoted loosely, so the table gives only figures printed
on the vendor's own product page on 23 September 2026. Read it as a ladder: each
step up buys payload, reach and somebody else's assembly time.

| Rig | Price | Maturity |
| --- | --- | --- |
| SO-101 pair, self-sourced parts | $229.88 | Downloadable design; kits Shipped when in stock |
| LeKiwi mobile base with arm | $482 | Downloadable design |
| [Reachy Mini](https://pollen-robotics.com/reachy-mini/) | $399 tethered, $499 wireless | Shipped, 10,000+ units |
| [Trossen Solo AI](https://www.trossenrobotics.com/solo-ai) single-arm kit | $11,385.95 | Shipped |
| [MEVION](https://arxiv.org/abs/2607.17970) four-arm rig | about $14,000 in parts | Downloadable |
| [Trossen Stationary AI](https://www.trossenrobotics.com/stationary-ai) two-arm kit | $23,995.95 | Shipped |
| [Trossen Mobile AI](https://www.trossenrobotics.com/mobile-ai) | $33,695.95, or $40,025.80 with laptop | Shipped |

Two notes on that table, because both are easy to get wrong.

Trossen retired the ALOHA brand in March 2025 and the legacy ALOHA line reached
end of life on 1 July 2025, so the discontinued product pages carry no price. The
current products still contain "Aloha" inside their full names, which causes
persistent confusion. Their own pages also contradict each other on whether the
WidowX AI arm has six or seven degrees of freedom, and this document could not
resolve which is right.

Reachy Mini is in the table because it is the highest-volume open robot in the
list and people assume it collects manipulation data. It does not. It is an
expressive desktop robot with a six-degree-of-freedom head and no arms.

### 3.4 The three 2026 reactions

The cheap rig succeeded, and 2026 produced three distinct responses to what it
could not do.

The first says the cheap rig is too weak.
[MEVION](https://arxiv.org/abs/2607.17970), July 2026, states the complaint
plainly: ALOHA-style hardware is the de facto standard but cannot generate high
forces or speeds, so heavy objects and fast manipulation are out of reach. It
answers with four six-degree-of-freedom arms at 7.0 kg payload and 60 N·m maximum
torque, buildable for about $14,000 from parts orderable online, using sheet-metal
welding for the large structure and a closed-link elbow borrowed from quadruped
design to keep mass off the far end of the arm. All hardware and software are
released. Its maturity is **Downloadable**. What it does not report is a
comparison of data quality against the rig it criticises.

The second says the cheap rig should be run as a fleet.
[ArmnetBench](https://arxiv.org/abs/2607.24481), July 2026, ran an "arm farm" of
SO-101 cells under light on-site supervision and compared seven policies across
twelve tasks, each trained on 50 demonstrations, producing 2,518 policy rollouts
and 600 reference demonstrations, every episode labelled three ways as
successful, suboptimal or failed and released in LeRobot format. It matters
because it is the first evidence of the $230 arm being used as evaluation
infrastructure rather than as a hobby project, and evaluation is the expensive
half of this discipline.

The third says the controller should be a phone.
[Phone2Act](https://arxiv.org/abs/2605.01948), May 2026, turns a commodity
smartphone into a six-degree-of-freedom controller through Google ARCore and
exports natively into the LeRobot format; fine-tuning GR00T-N1.5 on 130 episodes
reached 90 per cent on a real multi-stage pick-and-place.
[COBALT](https://arxiv.org/abs/2605.19138), the same month, runs teleoperation in
the cloud with dozens of concurrent users, sub-100-millisecond latency for up to
eight users per graphics card, and a pilot dataset of over 7,500 demonstrations
and 50 hours collected with smartphones across nine countries in five days. Its
user study reports that phone teleoperation performed comparably to or better
than specialised hardware, which is the least expected result in this document.
Both are **Paper only** as regards a product.

Virtual-reality teleoperation sits alongside these rather than replacing them.
[Open-TeleVision](https://arxiv.org/abs/2407.01512) is the reference open stack
and introduced active stereoscopic feedback, where the operator's head motion
moves the robot's camera so they can look around rather than watch a fixed view.
The 2026 successors are honest about its ceiling.
[Dexora](https://arxiv.org/abs/2605.18722), May 2026, uses a headset for *fingers
only* and an exoskeleton backpack for the arms, because head-mounted hand
tracking is not accurate enough for arm pose — which is the most useful single
sentence anyone has published about Vision Pro teleoperation. LeRobot ships
supported plugins for WebXR phones and headsets, Meta Quest and PICO 4 including
controller-free hand tracking, so the software is **Shipped**; no
Vision-Pro-specific teleoperation product is for sale.

### 3.5 What a teleoperation rig still cannot do

Four things, and they are why sections 4, 5 and 8 exist at all.

It needs the robot present, so data can only be collected where a robot is, at
the rate one robot can be driven, by a person who is doing nothing else.

It gives the operator no sense of touch, on almost every affordable rig. Force
feedback exists — the I2RT YAM active leader arm and the OpenArm line are
bilateral, and the LeRobot plugin catalogue now lists the Haply Inverse3 and the
Force Dimension omega.7 — but it is not what a $230 pair of arms does, and the
tasks that most need it are the contact-rich ones.

It tires the operator. Mobile ALOHA's whole-body teleoperation is physically
demanding, and that is a hard limit on how many hours a person can produce.

It records one embodiment. Everything collected on a particular pair of arms is
tied to those arms' kinematics, and section 9.2's finding that
single-embodiment data can transfer *better* than pooled multi-embodiment data is
the one piece of good news on that front.

## 4. Handheld grippers: collecting without a robot

This is the largest single change in how manipulation data is collected, and
almost all of it has happened since early 2024. The idea is simple. Instead of
putting a person behind a robot, put the robot's gripper in the person's hand,
record what the hand does, and use that as the action label.

### 4.1 The Universal Manipulation Interface, and what it replaced

Before [UMI](https://umi-gripper.github.io/), there were two ways to get
manipulation data and both had a hard ceiling. Teleoperation needed the robot
present during collection, so data could only be gathered in rooms that contained
a robot, at the rate one robot could be driven. Video of people doing tasks
scaled without limit but carried no action labels and showed a hand rather than a
gripper. Earlier instrumented handheld grippers existed, and the UMI paper is
direct about why they did not take over: their recorded actions were confined to
simple grasping and quasi-static pick-and-place, because end-effector tracking
was not good enough for anything faster.

What changed is that demonstrations recorded by a person holding a gripper, with
no robot in the room, became good enough to train visuomotor policies that deploy
zero-shot on several different robots, including on dynamic, bimanual and
precise tasks.

The mechanism is a 3D-printed parallel-jaw gripper with soft fingers and a
trigger, carrying a GoPro as its only sensor. A 155-degree fisheye lens gives the
wide view a wrist camera needs, and the paper deliberately does not rectify it,
because rectifying a 155-degree view to a pinhole model stretches the periphery
and compresses the centre where the useful information is. Two side mirrors sit
in the camera's peripheral view and act as a pair of virtual cameras, giving
implicit stereo without a second camera's cost or weight. The GoPro writes its
accelerometer and gyroscope into the video file, and an inertial-monocular
system built on ORB-SLAM3 recovers the six-degree-of-freedom trajectory at
absolute scale. The gripper weighs 780 g and has an 80 mm finger stroke. The
published cost is two numbers, not one: the printed gripper has a bill of
materials of **$73**, and the GoPro with accessories comes to **$298**.

This matters because it decoupled collecting data from owning a robot, and
because it standardised on one video file per episode, which is what made
sharing data between laboratories plausible at all. Every item in the rest of
this section descends from it.

It still cannot do three things, and the paper says all three. The kinematic
limits of the robot that will eventually run the policy are unknown at collection
time, so infeasible trajectories have to be filtered out afterwards. The tracking
inherits visual SLAM's need for texture and fails in plain rooms with blank
walls; the
[data scaling laws study](https://arxiv.org/abs/2410.18647), which collected with
UMI, lost roughly ten per cent of its data this way. And collecting with the
gripper is slower than using your own hands, because it is bulky and has fewer
degrees of freedom. An independent user study in March 2026
([arXiv 2603.17189](https://arxiv.org/abs/2603.17189)) put eight participants
through opening sterile medical packaging with two gripper designs and with bare
hands, and found both grippers substantially slower and less effective than
hands.

Its maturity is **Downloadable**: the [code and hardware
files](https://github.com/real-stanford/universal_manipulation_interface) are
MIT-licensed, and you print and assemble the device yourself.

### 4.2 The 2026 variants, and what each one added

Through 2025 and 2026 the original design sprouted a family. Each member fixes
one named weakness of the original, which makes the family a useful map of what
the weaknesses actually were.

The table lists the ones with a released artefact or a measured result. Read the
middle column as "the UMI limitation this attacks", and the last as what you can
do with it today.

| Device | The weakness it attacks | Maturity |
| --- | --- | --- |
| [FastUMI](https://arxiv.org/abs/2409.19499) | the ORB-SLAM3 pipeline is hard to deploy; replaces it with an off-the-shelf tracker | Downloadable, MIT code |
| [DexUMI](https://arxiv.org/abs/2505.21864) | one gripper degree of freedom cannot teach a dexterous hand; uses a wearable hand exoskeleton and inpaints the robot hand into the video | Downloadable, MIT |
| [UMI-on-Legs](https://arxiv.org/abs/2407.10353) | the policy assumed a fixed base; adds a quadruped whole-body controller trained in simulation | Downloadable, MIT |
| [UMI-FT](https://arxiv.org/abs/2601.09988) | no force signal; adds a coin-sized six-axis force sensor per finger | Downloadable, MIT |
| [UMI-3D](https://arxiv.org/abs/2604.14089) | monocular SLAM fails in texture-poor rooms; adds a wrist LiDAR | Downloadable |
| [TacUMI](https://arxiv.org/abs/2601.14550) | contact events are invisible in pixels; adds tactile, force-torque and pose sensing | Demonstrated |
| [YUBI](https://arxiv.org/abs/2606.10244) | the pistol grip is ergonomically poor for fine work; drives the jaw directly from finger motion | Downloadable hardware and software |
| [Whole-Body UMI](https://arxiv.org/abs/2609.22829) | an end-effector trajectory underdetermines a humanoid's whole body | Demonstrated |

Two of these deserve more than a row.

**YUBI**, published in June 2026 by Toyota Motor Corporation's Frontier Research
Center with AIRoA, is the first time the family acquired a reference device
backed by a manufacturer. Before it, the pistol grip was the default and its
ergonomic cost was anecdotal. What changed is a finger-aligned gripper whose jaw
is driven directly by the operator's finger rather than by a trigger, tracked by
a virtual-reality system rather than by SLAM, and a corpus behind it of 8,434
hours over 1.20 million episodes and 119 tasks. The mechanism of the corpus is
worth stating precisely, because it is the part nobody can replicate casually:
179 operators working 22 desks around the clock for over two months. A single
policy trained on it transferred to UR, Franka and ELEY bimanual robots by
bolting the gripper onto each. It matters because the hardware licence is
unusually permissive for a manufacturer — the hardware is CERN-OHL-W-2.0 with an
explicit note permitting commercial manufacture and sale, and the software is
Apache-2.0. What it cannot do yet is give you the data: the full corpus was still
marked as coming soon in September 2026, and only a gated subset exists.

**HiFi-UMI**, published in July 2026 by Simple AI, is the most consequential
result in this whole section. Before it, standard practice treated robot-free
handheld data as suitable for pretraining only, with a small quantity of real
teleoperated data added at the end to anchor the policy to the robot — because
the handheld trajectories were not accurate enough to train on alone. What
changed is the claim that raising the fidelity of the handheld data removes the
need for that anchor entirely. A policy post-trained only on handheld
demonstrations deployed directly on a real robot and matched in-domain
teleoperation across three different model backbones, with success-rate
differences of −2.5, +3.1 and −0.6 percentage points; the strongest reached 85 %
on a precision insertion task, and the teleoperation baseline it was compared
against had been collected in the evaluation scene while no handheld trajectory
had. The mechanism is four hardware decisions: head-mounted offline
stereo-inertial SLAM rather than wrist SLAM, natively measured rather than
reconstructed pose between the two grippers, a shared microsecond-level trigger
synchronising the sensors, and two wide-angle cameras per hand covering about 200
degrees. Together they reach 3 mm workspace-local end-effector accuracy with no
external tracking hardware in the room.

One honest qualification belongs with that result, and the paper makes it. The
headline comparison used 3,200 handheld trajectories per task against 300
teleoperated ones. It is a comparison of two data *pipelines* at their natural
throughputs, not a claim that one handheld demonstration is worth as much as one
teleoperated demonstration. Comparing pipelines is the right comparison to make,
because the whole argument is that one pipeline is far cheaper per hour than the
other, but it is not the comparison people will remember.

It matters because it removes the last structural reason to own a robot in order
to produce a deployable policy for a task. What it cannot do is let you build the
rig: the hardware is proprietary,
and what you can have is
[2,000 hours of its data](https://huggingface.co/datasets/simple-world-lab/HiFi-UMI-2K)
under CC BY 4.0. The accuracy figure is also workspace-local rather than global,
which is the right number for a tabletop task and not for a mobile one. Its
maturity is therefore split: the dataset is **Downloadable**, the rig is
**Demonstrated**.

### 4.3 The scale nobody had claimed before

One July 2026 result is worth recording separately, because of what it implies
about where this is going.

Before it, the largest published handheld corpora were measured in thousands of
hours. [Xiaomi-Robotics-1](https://arxiv.org/abs/2607.15330) reports pretraining
a vision-language-action policy on **over 100,000 hours of real-world
manipulation trajectories collected with UMI devices**. The mechanism that makes
that quantity usable is an automatic labelling pipeline that annotates trajectory
clips with sentences describing how the scene changed, so that the actions have
language to condition on without anybody writing it. The paper reports that
performance improves consistently with both data scale and model size during
pretraining, and that the improvement carries through to out-of-the-box
performance on real robots in unseen rooms.

It matters because it is the first evidence that handheld collection scales into
the range where the word "foundation model" is not aspirational, and because that
scale was reached without a robot fleet.

What it cannot do is let anybody check it. Neither the corpus nor the collection
infrastructure is released, the comparison is against the authors' own baselines
plus simulation benchmarks, and 100,000 hours is not a quantity a reader can
sanity-check. Its maturity is **Paper only**.

### 4.4 What you can buy, and what it costs

Until 2026 a handheld rig meant a printer and a weekend. Two vendors now sell
assembled ones, and the prices are worth setting against UMI's own $73 plus $298.

The table lists only devices with a published price and stock on the vendor's own
page as of 23 September 2026. Read the price column as what leaves the shop, and
the last column as what you still have to add.

| Device | Price | Maturity | What it does not include |
| --- | --- | --- | --- |
| [TRumi](https://www.trossenrobotics.com/trumi), Trossen Robotics | $2,195.99 a pair with cameras; $949.95 without | Shipped | memory cards, batteries and bag are a $399.95 bundle |
| [Mantis UMI](https://www.almond.bot/mantis-umi), Almond AI | $1,799 a pair | Shipped | camera kit, compute and pose tracking are all extra |
| [Grabette](https://huggingface.co/blog/grabette), Pollen Robotics | about €490 in parts | Downloadable, not shipped | you build it; the matching €120 Gripette gripper is what runs the data |

TRumi replaces UMI's printed gear trigger with a zero-backlash cam drive on
linear rails with constant-force springs and a 0.4 lb pull, and widens the field
of view from 155 to 177 degrees. Mantis matches its gripper geometry to the
vendor's own arm so that data transfers directly. Grabette, announced in July
2026, is not a product at all but a published design — two cameras including a
depth camera, an inertial sensor, magnetic encoders and a Raspberry Pi — that
writes straight into the LeRobot dataset format as a camera-local
six-degree-of-freedom pose plus gripper state.

The honest summary is that the printed original is still an order of magnitude
cheaper than anything assembled, and what the premium buys is backlash-free
mechanics, a wider lens and somebody else's assembly time.

One device that is frequently written about is not buyable. BeingBeyond
announced **U1**, described as the first commercial dexterous-hand handheld rig,
in March 2026, with claimed figures of 680 g, eleven joints of which six are
active, 5 kg payload, sub-millimetre tracking error and tactile sensing on all
five fingertips. Its research basis,
[RealDexUMI](https://arxiv.org/abs/2606.06033), reports 88.75 % average success
across eight real-robot tasks. There is no published price and no purchase path;
the product page offers only a consultation booking. Its maturity is
**Announced**, and the stated limitation from its own project page is that the
in-hand camera view limits global scene awareness, so it fails when the target or
a progress cue falls outside that view.

### 4.5 The shared evaluation floor that did not exist

One thing the handheld family conspicuously lacked until this autumn was any way
to compare two claimed success rates. Every group evaluated on its own robot,
objects and tasks.

The [UMI Arena](https://umi-arena.airoa.io/), a CoRL 2026 workshop scheduled for
12 November 2026 and run by AIRoA, is the first attempt at a common floor. It
runs three tracks: a policy competition judged by the organisers on real Franka,
TX-G2 or OpenArm arms, a device exhibition judged by attendee vote on ergonomics,
dexterity, strength, reproducibility and cost, and a paper track. The competition
uses eight tasks of which three are held out until final evaluation, so the
leaderboard measures generalisation rather than practice. Submissions opened on
21 September 2026 and registration closes on 9 October.

It matters because a claimed success rate in this family has until now been
uninterpretable. What it cannot do is serve as a neutral standard: the evaluation
runs on the organisers' robots, against a dataset collected with
organiser-affiliated hardware, and that dataset is gated behind a signed
agreement whose terms are themselves behind the gate. Three of the eight tasks
are secret. Its maturity is **Announced**, and no results exist yet.

## 5. Exoskeletons, gloves and ambient capture

A handheld gripper records where the gripper went. It records nothing about the
arm that carried it, and nothing about the fingers. This section is the three
ways people record those instead: a frame worn on the arm, a glove worn on the
hand, and a room instrumented to watch the whole body.

### 5.1 Exoskeletons, which record the whole arm

Before exoskeletons, the choice was teleoperation, which is expensive, or a
handheld gripper, which captures the end-effector only. Behaviours that use the
whole arm — gathering objects towards you, supporting something with your forearm
— cannot be recorded by a device that only knows where your hand is.

[AirExo](https://airexo.github.io/), 2023, is the origin of this line. Its claim
was that three minutes of teleoperated demonstrations, augmented with
exoskeleton data collected outside the laboratory, matched or beat a policy
trained on over twenty minutes of teleoperation, and was more robust to
disturbance. The mechanism is a passive dual-arm frame worn by the person,
carrying joint encoders and nothing else, at a stated **$300 per arm**. Its code
and CAD are MIT-licensed, and its maturity is **Downloadable**. Its limits are
that the comparison is on a small task set, that a passive frame gives the wearer
no force feedback, and that it needs adapting to each robot's kinematics.

[AirExo-2](https://airexo.tech/airexo2/), 2025, made the cost argument explicit:
**$600 for the exoskeleton system against roughly $60,000 for a teleoperation
platform**, a hundredfold ratio. Its contribution beyond price is the idea of an
*adaptor*, a preprocessing step that converts captured human motion into
pseudo-robot demonstrations, so no robot fine-tuning stage is needed afterwards.
A policy trained solely on adapted in-the-wild data reached performance
comparable to one trained on teleoperation — against the authors' own baseline on
their own tasks. Its maturity is **Downloadable**, with a caveat that matters:
the repository's licence resolves to "no assertion", so the CAD terms are
unclear.

Three 2026 papers push the line further and each attacks a different weakness.
[ExoGS](https://arxiv.org/abs/2601.18629), January 2026, introduces AirExo-3, a
robot-isomorphic passive exoskeleton, and rebuilds the robot, objects and
environment as editable Gaussian-splatting assets so one human demonstration can
be replayed and augmented in simulation; its repository carries no licence file
at all. The [Universal Manipulation
Exoskeleton](https://arxiv.org/abs/2606.14218), June 2026, adds real-time haptic
torque feedback and records joint torques as well as configurations, with the
striking demonstration that operators could unsheathe kinematically constrained
objects while blindfolded; it publishes no cost, no degree-of-freedom count and
no success rates, so its maturity is **Demonstrated**.
[DexEXO](https://arxiv.org/abs/2603.17323), March 2026, attacks fit, supporting
hand lengths from 140 mm to 217 mm so that many different people can use one rig,
and gives the exoskeleton a passive hand that visually matches the deployed
robot, which removes the image-inpainting step that DexUMI needs.

For humanoids specifically, [HOMIE](https://homietele.github.io/) is the one to
know. It is an isomorphic exoskeleton cockpit at a stated **$500**, with a
reinforcement-learning locomotion policy driven by a foot pedal, isomorphic
exoskeleton arms, and gloves that use Hall sensors rather than servos so that a
compact glove reaches more than fifteen degrees of freedom. It claims half the
task completion time of prior teleoperation systems. What it cannot give you is
direct control of the legs: the body is policy-driven, so the operator commands a
gait rather than a stride.

### 5.2 Gloves, which record the fingers

Before 2024, hand motion capture was not portable and did not turn into policies.
[DexCap](https://dex-cap.github.io/) changed that by combining SLAM for the wrist
with electromagnetic sensing for the fingers, which is the part that survives
occlusion, and publishing an imitation algorithm that consumed the result. Its
weakness is inherent to the sensing: electromagnetic tracking degrades near
metal, and retargeting to a non-human hand is still required afterwards.

The 2025 and 2026 glove work converges on one idea, and naming it is more useful
than listing the devices. **The embodiment gap is being closed in hardware rather
than in software.** Rather than recording a human hand and then correcting for
the fact that the robot's hand is different, these systems arrange for the two to
be the same thing, or to look the same, or to show the operator what the robot
would have felt.

The table lists the open ones with a published number. Read the middle column as
the specific gap each closes.

| Glove | What it closes | Numbers | Maturity |
| --- | --- | --- | --- |
| [DOGlove](https://arxiv.org/abs/2502.07730) | cost and force feedback | under $600; 21 degrees of freedom captured; 5-degree-of-freedom cable-driven force feedback | Downloadable |
| [FSGlove](https://arxiv.org/abs/2509.21242) | measurement accuracy | one inertial sensor per joint, up to 48 degrees of freedom, joint-angle error under 2.7° against optical motion capture | Downloadable |
| [OSMO](https://arxiv.org/abs/2512.08920) | the need for robot data at all | 12 three-axis tactile sensors; a policy trained only on human demonstrations reached 72 % on a sustained-pressure wiping task | Downloadable |
| [T-800](https://arxiv.org/abs/2603.26403) | sampling rate | 800 Hz full-hand tracking, showing human dexterity carries motion energy above 100 Hz that slower rigs discard entirely | Demonstrated |
| [Touch2Robot](https://arxiv.org/abs/2609.24660) | contacts the robot cannot reproduce | shows the demonstrator live how the robot hand would contact the object; replay completion rose from 37.9 % to 72.1 %, and collection time per usable demonstration fell from 58.6 s to 18.2 s | Demonstrated |

The commercial side is thinner than it looks. MANUS is the clearest vendor
positioning itself at robot training, with Metagloves Pro and Metagloves Pro
Haptic listed at €4,500 and the older Quantum Metagloves at €2,500 and marked end
of life; those figures came from the vendor's landing page rather than a checkout
page. A new MANUS product is announced for IROS 2026, which opens four days after
this document's date, so anyone choosing a commercial glove should wait a week.
Rokoko's glove product page returns a 404 and this document could not establish
what, if anything, replaced it.

### 5.3 Ambient capture, which records the room

The newest idea in this section is to stop instrumenting the person and
instrument the building.

Before it, every capture method fragmented the experience. One rig recorded the
hand, another the body, another the objects, and nothing recorded how they
evolved together while a person pursued a goal over several minutes.

[ACE-Data-0](https://arxiv.org/abs/2607.28625), July 2026, turns real homes into
calibrated, synchronised recording studios at two scales: a table-scale
configuration that resolves hand-object manipulation and a room-scale
configuration that captures walking, whole-body motion and interaction across a
furnished home. It records egocentric and multi-view exocentric video, full-body
and articulated hand motion, object geometry and six-degree-of-freedom object
trajectories, audio and touch as one stream. The planned release is 150 hours, 17
million frames, 75,000 interaction episodes over 200 task categories, performed
by 50 participants in two environments, with individual takes running up to 20 to
30 minutes. Participants are given goal-level instructions rather than
step-by-step ones, deliberately, to preserve natural variation.

It matters because it is the only method here that captures the whole
perception-action loop of a person doing a real task in a real house, which is
the thing every other method approximates.

Two things it cannot do. The data does not exist yet: the dataset card says the
figures describe the planned release and the files are marked as coming soon, so
its maturity is **Announced**. And when it arrives it will be research-only —
the licence is a bespoke one granting non-commercial academic use, with manual
per-person approval and no redistribution. Do not plan a product around it.

## 6. The open datasets, and their licences

### 6.1 Why the licence comes before the size

In most areas of this repository a licence is a thing you check before shipping.
Here it is the first thing to check, before you download anything, and there are
two reasons.

The first is that a dataset licence propagates into the weights. A model trained
on a corpus published under a non-commercial licence is a derivative of that
corpus, and several of the largest and most attractive robot datasets are
published exactly that way. Discovering this after a training run has cost you
the training run.

The second is that there is no index. I looked for a current, maintained register
of robot manipulation datasets with their sizes and licences, and there is not
one. Open X-Embodiment's spreadsheet is the closest thing, and it has no licence
column at all. The two community lists on GitHub have one star and zero stars
respectively. Anyone writing about this has to read the dataset cards one at a
time, and so does anyone using them.

### 6.2 Open X-Embodiment, the pool that stopped growing

Before it, every laboratory's dataset was an island. There was no way to train
one model on data from several robots because there was no common format and no
common place to put it.

What changed in October 2023 is that 34 institutions agreed to convert their data
into one format and publish it together. The current index lists 72 member
datasets, 2,419,193 episodes, 27 distinct robots and about 8,965 GB.

The mechanism was conversion rather than collection, and that is where the
interesting detail sits. The index records how each member dataset was gathered,
and the answer is not what the phrase "robot demonstrations" suggests. Twenty-five
member datasets were collected by a person in virtual reality, fifteen by a
script, thirteen by an expert policy, six with a space mouse, four by
puppeteering and two by moving the arm by hand. The two largest members are not
human demonstrations at all: VIMA contributes 660,103 scripted episodes and
QT-Opt contributes 580,392 episodes generated by a learned policy, and between
them those two are about half of every episode in the pool.

It matters because it is the reason cross-embodiment models exist at all, and
because it proved that laboratories would pool data if somebody did the
conversion work.

Three things it cannot do. There is no global definition of an episode, so the
unit varies across members from a three-hertz scripted rollout to a
thirty-hertz human demonstration. There is no central licence record, so a
commercial user has to clear 72 licences individually, and at least one member —
the non-commercial half of RH20T — is CC BY-NC 4.0 and sits inside mixtures
people train on without noticing. And it has effectively stopped: the maintaining
repository was last updated in November 2025. Its maturity is **Downloadable**,
with the licence unresolvable centrally.

### 6.3 DROID, and a licence that is simply missing

Before DROID, large manipulation datasets came from one laboratory's robot in one
laboratory's building.

[DROID](https://droid-dataset.github.io/), published in 2024, collected 76,000
teleoperated trajectories totalling 350 hours across 564 scenes and 84 tasks,
using 50 data collectors across North America, Asia and Europe over twelve
months. The mechanism was a standardised mobile cart carrying a Franka Panda, so
that the same rig could be wheeled into a genuinely different room. One episode
is one teleoperated trajectory with up to three alternative language
instructions and a seven-dimensional action.

It matters because scene diversity, not episode count, is what section 9 says
buys generalisation, and DROID was the first serious attempt to buy scene
diversity deliberately.

What it cannot give you is a licence. There is no licence file in the dataset
repository, no licence statement in its documentation, and none in the storage
bucket; only the separate policy-learning code is MIT. A commercial user cannot
clear DROID from public documents, and this document is not going to guess on
their behalf. Its documentation also records that about twenty per cent of
episodes were lost while face-blurring and copying the raw release, which affects
the raw video version and not the converted one. No successor had appeared by
September 2026. Its maturity is **Downloadable, licence unnamed**.

### 6.4 The 2026 wave

Six large corpora arrived between June and September 2026, and they changed what
is available far more than anything in the two preceding years. The table lists
them with the three numbers that matter and the licence read from the dataset
card. Read the "one episode is" column first, because it is what makes the size
column mean anything.

| Dataset | Size | One episode is | Licence | Commercial |
| --- | --- | --- | --- | --- |
| [ABC-130K](https://huggingface.co/datasets/XDOF/ABC-130k) | 3,553 h, 134,806 episodes, 195 tasks | a whole two-armed task attempt, 7 s to 469 s | Apache-2.0 | yes |
| [HIW-500](https://huggingface.co/datasets/BitRobot/HIW-500) | 500+ h, 23,000+ episodes, 12 real homes | one in-home humanoid teleoperation, about 6 subtasks long | CC BY 4.0 | yes |
| [HiFi-UMI-2K](https://huggingface.co/datasets/simple-world-lab/HiFi-UMI-2K) | 2,000 h released from a 20,000 h corpus | a human two-handed take, no robot involved | CC BY 4.0 | yes |
| AIRoA MoMa 5k | 5,025 h, 1,184,259 episodes, 44 robots | one primitive action, about 15 s | custom, research-only | no |
| OpenNeoData | 5,000+ h, 200,000+ trajectories, 6 embodiments | one trajectory on one of six platforms | CC BY-NC-SA 4.0 | no |
| [PrimeBot challenge data](https://arxiv.org/abs/2609.03591) | 1,500 h over four batches | one two-armed household demonstration | CC BY-SA 4.0 | yes, with ShareAlike |

Two of them deserve the full treatment.

**ABC-130K** is the most useful thing released this year for somebody who wants
to train on open data and sell the result. Before it, DROID's 350 hours of
single-arm Franka data was the reference open teleoperation set and nothing open
was bimanual at scale. What changed is a complete open stack: 3,553 hours of
two-armed teleoperation, plus 400 hours of simulated teleoperation across 20
scenes, plus over 100 hours of real evaluation runs published with their scoring
rubrics, plus the hardware design, the training code and the simulation pipeline.
The mechanism is a standardised station: two I2RT YAM arms on an aluminium
extrusion rail, three Intel RealSense D405 cameras — one on a metre-high post and
one on each wrist — inside a cage whose dimensions replicate the simulated scene
exactly, so that a simulated evaluation predicts the real one. The 195 tasks fall
into seven categories: pick-and-place, folding, sorting, tool use, handover,
insertion and assembly. It matters because the correlation between the simulated
and real evaluations gives you a way to compare model choices without running a
real robot each time, which is the expensive part of this whole discipline. What
it cannot tell you is what the rig costs: the hardware page is a full bill of
materials with live supplier links and no total anywhere, and neither the paper
nor the site states one. Its maturity is **Downloadable** under Apache-2.0, with
a click-through gate that adds no terms.

**HIW-500** is the answer to a different question. Before it, humanoid data was
collected in laboratories and staged environments. What changed is 500-plus hours
of whole-body teleoperation of a Unitree G1 recorded in twelve real homes in
Southeast Asia, where the layout, the object states, the lighting, the clutter
and the operator's style all vary between episodes. The mechanism is ordinary
whole-body teleoperation with head and wrist cameras at 480p and 30 frames a
second, 29 joint states, inertial and odometry data, and 148,000 subtask
annotations drawn from a vocabulary of 161 labels. It matters because it is the
largest humanoid corpus a commercial user may actually use, released under CC BY
4.0 with attribution and no gate. What it cannot offer is task breadth: the
diversity is in the twelve homes, and the card claims only "10+ tasks".

Three more are worth naming without the full treatment. AgiBot World remains the
largest single-programme collection, with 1,003,672 trajectories in its Beta
release across 217 tasks and 100 robots, and it is published under CC BY-NC-SA
4.0, which puts the largest robot dataset in the world out of reach of a product.
[RoboMIND](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND) has
55,000 teleoperated trajectories over 279 tasks and four embodiments under
Apache-2.0, which makes it unusually well-placed for its size. And the Galaxea
Open-World Dataset has 500-plus hours of mobile manipulation on a single uniform
embodiment, under CC BY-NC-SA 4.0.

### 6.5 Which licences stop a commercial user

This is the section to read twice. Every entry was read from the dataset card or
the licence file. The table sorts by whether you can ship a model trained on the
data. Read the middle column as the exact instrument, not a paraphrase.

| Dataset | Licence | What it means for a product |
| --- | --- | --- |
| ABC-130K | Apache-2.0 | usable; the most permissive large corpus that exists |
| HIW-500 | CC BY 4.0 | usable with attribution |
| HiFi-UMI-2K | CC BY 4.0 | usable with attribution |
| RoboMIND | Apache-2.0 | usable |
| BridgeData V2 | CC BY 4.0 | usable with attribution |
| MolmoAct2-BimanualYAM | Apache-2.0 | usable; same arms as ABC-130K, so the two co-train |
| Unitree G1 releases | Apache-2.0 | usable |
| PrimeBot challenge data | CC BY-SA 4.0 | usable, but ShareAlike obligations attach |
| RH20T, commercial half | CC BY-SA 4.0 | usable, with ShareAlike |
| **AgiBot World, all editions** | **CC BY-NC-SA 4.0** | **blocked, and ShareAlike infects derivatives** |
| **Galaxea Open-World** | **CC BY-NC-SA 4.0** | **blocked** |
| **OpenNeoData** | **CC BY-NC-SA 4.0** | **blocked** |
| **RH20T, non-commercial half** | **CC BY-NC 4.0** | **blocked, and it sits inside Open X-Embodiment** |
| **AIRoA MoMa 5k** | **custom terms** | **blocked in practice: derived models may not be redistributed** |
| **ACE-Data-0** | **bespoke research licence** | **blocked: non-commercial academic research only** |
| DROID | none published | unresolvable; treat as unclear |
| Open X-Embodiment as a mixture | 72 separate licences | unresolvable centrally; at least one member is non-commercial |

Three practical warnings follow from that table.

The non-commercial licences are concentrated at the top of the size rankings.
AgiBot World, Galaxea and OpenNeoData are among the largest things available and
none of them may be used in a product. If your plan is "train on the biggest open
dataset", your plan currently ends in a licence review.

ShareAlike is not the same as non-commercial and is often worse in practice. CC
BY-SA and CC BY-NC-SA both carry an obligation to license derivatives on the same
terms, and a model is a derivative. A company that can live with attribution
frequently cannot live with publishing its weights.

A mixture is only as permissive as its most restrictive member. Training on a
blend that includes Open X-Embodiment means inheriting whatever is in it,
including the non-commercial half of RH20T, and there is no central record to
check against.

### 6.6 One headline that does not survive arithmetic

Unitree's whole-body teleoperation release has been described as the largest open
humanoid teleoperation dataset. It is worth working through, because the shape of
the error is common.

There is no single repository of that name. What exists is a collection pointing
at 59 separate per-task repositories on the Hugging Face Hub. Summing the frame
counts in each repository's own metadata file, at the 30 frames a second those
files declare, the whole-body teleoperation group comes to roughly 12,900
episodes and about 136 hours. Unitree's entire public dataset corpus, including
every other robot and end effector, comes to about 496 hours.

HIW-500, on the same robot, is 500-plus hours. So the whole-body release is
around a quarter the size of a single other humanoid dataset, and Unitree's
complete public output is smaller than that one dataset. The claim is only
defensible if it is read as counting *tasks* rather than hours, or if it counts
data that has not been released.

The lesson generalises. A dataset distributed as many repositories has no single
number attached to it, which means the number in the announcement came from
somewhere other than the files. The check takes an hour and is worth doing before
you plan around a figure. The Unitree data itself is genuinely useful and
genuinely permissive — Apache-2.0, ungated — and none of that is in question.

## 7. LeRobot, and the tooling that grew round it

### 7.1 What it is, and why it won

Before LeRobot, every laboratory that collected demonstrations invented its own
file layout. A dataset from one group could not be loaded by another group's
training code without a conversion script, and the conversion script was usually
the thing that got lost. Open X-Embodiment's answer in 2023 was to convert sixty
datasets into a single TensorFlow-based format, which worked but tied everything
to one framework and one storage style.

What changed is that [LeRobot](https://github.com/huggingface/lerobot), Hugging
Face's robot-learning library, became the place where the format, the training
code, the pretrained policies, the hardware drivers and the published datasets
all live together. As of 23 September 2026 the repository has about 27,700 stars
and is under Apache-2.0, which is the permissive end of the spectrum and one
reason it spread.

The mechanism is the
[LeRobotDataset](https://huggingface.co/docs/lerobot/lerobot-dataset-v3) format,
which stores frames in Parquet files, pictures go into MP4
shards, and a `meta/` folder carries the frame rate, the field shapes, the
normalisation statistics and the task sentences. Because pictures are stored as
video, a few hundred episodes are megabytes rather than gigabytes, and because
everything sits on the Hugging Face Hub, publishing a dataset is a push rather
than a hosting project.

This matters more than a file format usually would. The entire community
hardware line in section 3 is only useful because the data it produces lands
somewhere that training code already reads.

What it cannot do is make datasets comparable. Two LeRobot datasets can share
every key name and still differ in frame rate, camera placement, action
convention and what counts as an episode boundary, and nothing in the format
records the difference.

### 7.2 What the 2026 releases added

The library shipped four releases in 2026 that are worth knowing about, and two
of them landed after May.

The table gives the dates from the repository's own release list and the change
that matters most to someone collecting data. Read it as a compatibility warning
as much as a feature list, because each of these releases broke something.

| Release | Date | What it changed for data collection |
| --- | --- | --- |
| v0.5.0 | 9 March 2026 | the first release of the year; pin here only if something later broke you |
| v0.5.1 | 7 April 2026 | the last release carrying the GR00T N1.5 policy, which v0.6.0 replaces with N1.7 |
| **v0.6.0** | **6 July 2026** | hardware-accelerated video encoding, depth-camera support end to end, automatic language annotation of episodes by a vision-language model, and roughly twice as fast data loading through parallel multi-camera decoding |
| **v0.6.1** | **3 August 2026** | improved vision-language annotation, including seeded relabelling and a recipe for serving the annotating model yourself |

The v0.6.0 release is the substantial one, and its
[release notes](https://huggingface.co/blog/lerobot-release-v060) are worth
reading in full before upgrading. Three changes matter to anyone collecting.

Depth is now a first-class citizen rather than something you bolted on, with
Intel RealSense integration and separate codec settings for colour and depth
streams. Before this, most people either discarded depth or stored it as a
side-car that the training code did not know about.

Episodes can now be annotated with language automatically. The `lerobot-annotate`
command runs a vision-language model over the recorded video and writes the task
sentences, replacing the per-frame `subtask_index` annotations that earlier
versions used. This matters because hand-writing a sentence per episode is one of
the genuinely tedious parts of preparing a dataset, and because
vision-language-action policies need those sentences.

Data loading is about twice as fast, through decoding several camera streams in
parallel. Video decoding was already the slow part of training a policy on image
data, so this is a real change to how long an experiment takes rather than a
benchmark improvement.

Two things v0.6.0 will break. Installing `lerobot` no longer pulls in dataset or
training dependencies, so `pip install lerobot[training]` is now required; the
base install dropped roughly forty per cent of its dependencies. And the minimum
PyTorch version moved to 2.7, which on an older machine is not a small ask.

Its maturity is **Shipped** and **Downloadable** under Apache-2.0.

### 7.3 The size of the pile

One artefact gives the scale of what the format unlocked. In July 2026 the
LeRobot project published `community_dataset_v3`, an aggregate of 791 datasets
covering 46 robot types from 235 community contributors, under Apache-2.0 and
with no gate. Each of those datasets is small. Most were recorded on one cheap
arm by one person in one room, and most will never be used by anybody but their
author.

That is not a criticism, and it is worth being clear about why. The value of the
pile is not that any one dataset in it is good. It is that the format has enough
gravity that publishing became the default rather than an afterthought, and
section 9 is about the conditions under which many small, varied datasets are
worth more than one large uniform one. On the evidence there, 791 rooms is the
kind of diversity the scaling results say you want, and 235 different people
holding the controls is the kind they warn you about.

## 8. Human video instead of teleoperation

### 8.1 Why the idea keeps coming back

The arithmetic is unavoidable. Pooled robot data across the whole field is
measured in millions of episodes. Video of people manipulating objects is
effectively unbounded, and a large amount of it is already recorded, already
egocentric, and already public. If any usable fraction of that could substitute
for teleoperation, the constraint in section 1 would stop binding.

The reason it does not simply work is that a video of a person contains no
actions. It shows a hand, not a gripper, moving under a body the robot does not
have, filmed from a viewpoint the robot's cameras do not occupy. Turning it into
supervision means inventing the missing action labels, and the quality of that
invention is the whole subject.

Through 2025 this was, in the honest assessment the repo's own
[mechanism document](../10_one-arm-training/05_what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do)
gave it, interesting rather than proven, with almost nothing released. That is
the part which changed in 2026.

### 8.2 The result that changed the argument

Before June 2026, the defensible position was that human video is a useful source
of visual priors and a poor source of actions, so you pretrain on it and then
collect robot data for everything that matters.

[HumanScale](https://arxiv.org/abs/2606.20521), published on 18 June 2026, claims
something stronger. Holding the amount of pretraining data fixed and holding the
post-training and validation protocols fixed, a model pretrained on egocentric
human video beat the same model pretrained on teleoperated real-robot
trajectories: 24 % lower validation loss on real-robot action prediction, 52.5 %
higher success on in-distribution real-robot tasks and 90 % higher on
out-of-distribution ones.

The mechanism is not a new architecture. It is a filtering and labelling pipeline
applied to the human video before pretraining, and the paper's own framing is
that the pipeline is the contribution: egocentric data works as a pretraining
source *when processed carefully*, and the recipe is to pretrain on human video
for diverse world representations and then adapt with a small amount of labelled
robot data purely for action-space alignment.

This matters because it inverts the default. If it holds, the expensive robot
data is a small alignment step at the end rather than the bulk of the budget.

What it cannot do is remove robot data. The claim is explicitly about
pretraining, with real-robot adaptation still required, and the comparison holds
the data quantity fixed rather than the collection cost — which is the more
favourable framing for human video, since human video is far cheaper per hour.
Its maturity is **Paper only** as regards the pipeline; the claim has not yet
been independently replicated at the time of writing.

### 8.3 The three mechanisms people actually use

Underneath the individual papers there are only three ways to get supervision out
of a video of a person, and knowing which one a paper uses tells you most of what
you need.

The table names each route and what it actually supplies to the policy. Read the
last column as the thing that still has to come from somewhere else.

| Route | What the human video supplies | What still needs robot data |
| --- | --- | --- |
| **visual pretraining** | a representation of scenes, objects and contact, with no actions | everything about how the robot moves |
| **retargeting** | a hand pose per frame, converted into an end-effector pose the robot could reach | the robot's own dynamics, and whether the retargeted contact is achievable |
| **video editing** | frames in which the human hand has been replaced by a rendered robot, plus the aligned state | the correctness of the edit, which is not verified by physics |

Four 2026 releases sit on those routes, and each is worth a line with its number.

[HuRo](https://arxiv.org/abs/2609.10706), September 2026, takes the retargeting
route at scale. It converts heterogeneous human videos into robot-aligned
observations and action trajectories and publishes a dataset of about 630,000
robotized episodes and 142 million processed frames drawn from five human-video
sources. On four real manipulation tasks, increasing the amount of robotized
video raised overall completion from 51.5 % to 80.3 %, and completion under
spatial and visual shift from 34.9 % to 72.2 %. Here an "episode" is a segment of
human video with inferred robot actions attached, which no robot has ever
executed. Its maturity is **Paper only** as regards an obtainable dataset at the
time of writing.

[RoboEdit](https://arxiv.org/abs/2608.18948), August 2026, takes the editing
route. It reconstructs and retargets three-dimensional interactions from ordinary
RGB video and rewrites the video so the human hand becomes a robot, producing
174,000 aligned video pairs totalling 14 million frames across seven robot
embodiments. An "aligned pair" here is one human clip and its edited robot
counterpart, not a robot trajectory.

[ACE-Ego-0](https://arxiv.org/abs/2606.17200), June 2026, is the most careful
about mixing. It trains on 4,530 hours of robot and simulation data together with
1,480 hours of egocentric human data converted to pseudo-actions, and adds a
reliability-weighted objective so that the noisy human labels contribute less
where they are least trustworthy. The interesting part is the admission built
into the method: the human labels are known to be wrong some of the time, and the
training has to be told so.

[UMI-Bridge](https://arxiv.org/abs/2609.18232), September 2026, uses the handheld
gripper of section 4 as a translator between human video and robot data, aligning
them by equivalence of action rather than similarity of pixels. It reports 91.7 %
mean success against 73.3 % for naive co-training of human and robot data, and
matches a robot-only baseline using a quarter of the robot demonstrations.

If you want the field's own summary rather than four results, the survey
[Robot Learning from Human Videos](https://arxiv.org/abs/2604.27621), April 2026,
is the current one.

### 8.4 What human video still cannot supply

Three things, and they are the same three every paper in the area runs into.

Force is absent. A video shows where a hand went and not how hard it pressed, and
for the tasks in the [gripping area](../07_gripping/01_overview.md) that are
about contact rather than position, that is the signal you needed.

The hand is not a gripper. A person manipulating an object uses fingers, wrist
rotation and the other hand in ways a parallel jaw cannot reproduce, so a large
fraction of any human video corpus shows behaviour that is not executable and has
to be filtered out or silently mislearned.

Reachability is unverified. A retargeted trajectory can be geometrically sensible
and kinematically impossible for the robot that will run it, and nothing in the
video says so. This is the same limitation the handheld grippers have, and for
the same reason: the robot was not there.

## 9. Data scaling laws, and what they actually say

### 9.1 The one published law

Before October 2024, the honest answer to "how many demonstrations do I need" was
that nobody knew, and the practical answer was to train on 50, then 100, then
200, and plot the curve.

[Data Scaling Laws in Imitation Learning for Robotic
Manipulation](https://arxiv.org/abs/2410.18647) is still the reference study, and
its last revision is dated 26 June 2026. It collected over 40,000 demonstrations
and ran more than 15,000 real-world robot rollouts under a fixed evaluation
protocol, varying three things independently: the number of training
environments, the number of objects, and the number of demonstrations per
environment-object pair.

Its central claim is that generalisation follows a power law in the *diversity*
of the data and saturates in the *quantity*. The fitted relationships, where the
optimality gap is the distance from perfect performance, are that the gap falls
as the number of objects to the power −0.32, as the number of environments to the
power −0.26, and as the number of environment-object pairs to the power −0.35.
Against that, performance plateaus once the number of demonstrations reaches
about 800 in their largest setting, and the recommendation is 50 demonstrations
per environment-object pair and no more.

The recipe that follows is the memorable part. Thirty-two environment-object
pairs, one distinct object per environment, 50 demonstrations each — about 1,600
demonstrations in total — collected by four people in one afternoon, reached
roughly 90 % success on novel environments with unseen objects. The data was
collected with UMI handheld grippers and the policy trained was Diffusion Policy
with a DINOv2 ViT-L/14 visual encoder. One demonstration there is one short
handheld recording of one task in one room with one object, so the numbers
transfer directly to anybody collecting the same way and need adjusting for
anybody whose episodes are longer.

This matters because it converts a vague instinct into a budget. If you are
collecting in one room with three objects, another hundred episodes is close to
worthless and a fourth room is worth a great deal.

The paper's own stated limitations are unusually clear, and they bound the claim
tightly. It studies single-task policies, not generalisation across tasks. It
studies imitation learning only, not reinforcement learning. It uses UMI's
demonstrations including their errors and does not study the effect of data
quality. It tests one policy algorithm. And it validates on four tasks, which the
authors attribute to resource limits. Its maturity is **Paper only** as a law,
though the [code](https://github.com/Fanqi-Lin/Data-Scaling-Laws) is MIT-licensed
and downloadable.

### 9.2 The results that complicate it

Two later studies pull in different directions, and both are worth knowing
because they are the strongest available check on the headline.

[Is Diversity All You Need for Scalable Robotic
Manipulation?](https://arxiv.org/abs/2507.06219), July 2025, takes the diversity
conclusion apart along three axes. It finds that task diversity does matter more
than demonstrations per task, which agrees. It finds that multi-embodiment
pretraining data is *optional*, and that models trained on high-quality
single-embodiment data transfer to other platforms with better scaling behaviour
during fine-tuning — which cuts against the assumption behind pooled
cross-embodiment corpora. And it finds that diversity of *demonstrator* is
actively harmful: different people's operating preferences produce a
multimodality in velocity that confuses the policy. Correcting for that gave a
15 % gain, which the authors equate to using 2.5 times as much pretraining data.

[Scaling Bimanual Household Manipulation](https://arxiv.org/abs/2609.03591),
September 2026, reports the opposite of saturation on its own corpus: releasing
1,500 hours of two-armed household demonstrations, it finds task success rising
steadily with both the quantity of expert data and with added on-policy
correction data, "at our current data scale". The qualifier is the honest part.

The two results are not contradictory, and the reconciliation is the useful
lesson. Saturation in the 2024 study was measured for a single task in a fixed
set of environments. Continued scaling in the 2026 study is measured across many
tasks. Quantity saturates within a narrow distribution and diversity does not,
which is the same statement twice.

### 9.3 What to do with this

Three practical consequences, in the order they will save you time.

Count your environment-object pairs before you count your episodes. If that
number is small, collecting more episodes is the wrong move and rearranging the
room is the right one.

Fifty demonstrations per pair is a defensible default, and it is the same number
the two-arm benchmark leaderboards settled on independently.

Be careful about how many different people collect. The velocity-multimodality
result means that three demonstrators who each have a personal style can be worse
than one, which is the opposite of the instinct that more collectors means more
diversity. Diversity of scene helps; diversity of operator hurts.

## 10. Making demonstrations instead of collecting them

### 10.1 Replaying a few demonstrations into thousands

Before MimicGen, generating training data in simulation meant scripting a
controller for each task, which is exactly the work that policy learning was
supposed to remove.

[MimicGen](https://github.com/NVlabs/mimicgen), 2023, changed that by taking a
small number of human demonstrations and adapting each one to new object poses,
producing over 50,000 demonstrations across 18 tasks from about 200 human
demonstrations. Its two-armed successor
[DexMimicGen](https://github.com/NVlabs/dexmimicgen), 2024, generated 21,000
demonstrations across nine bimanual dexterous tasks from just 60 source human
demonstrations.

The mechanism is segment-and-transform. A demonstration is cut into
object-centric segments, each segment is rewritten relative to wherever the
object now is, and the result is replayed in the simulator; a replay that fails
is discarded. The demonstrations it produces are therefore not new strategies,
they are the same strategy relocated.

This matters because it makes the cost of a dataset depend on the number of
*strategies* you need rather than the number of *situations* you want covered,
which is the right way round.

What it cannot do is invent a behaviour the seed demonstrations did not contain,
and it only works where a simulator can check the replay, which excludes
deformable objects, most contact-rich assembly and anything whose success depends
on force. Both tools are also **research-only** under NVIDIA's own licence rather
than a standard open-source one — the GitHub API reports the licence for both as
"Other" — so read the file before building a product on either. Their maturity is
**Downloadable**, with that restriction.

### 10.2 The simulation benchmarks that now ship the data

Two large simulated corpora are worth naming because LeRobot v0.6.0 wired both
into its evaluation command, which is the practical sign that they have become
standard.

[RoboCasa](https://github.com/robocasa/robocasa) supplies kitchen scenes with
thousands of 3D assets across more than 150 object categories, and its 2026
incarnation RoboCasa365 supplies 365 tasks. [RoboTwin
2.0](https://arxiv.org/abs/2506.18088) supplies 50 bimanual tasks with over
100,000 generated trajectories and strong domain randomisation; the RoboTwin
platform repository is MIT-licensed. Both are **Downloadable**.

The limitation both share is worth stating plainly:
a generated demonstration is only as good as the program that generated it, and
its contact behaviour is whatever the controller did, which is often unlike a
person. For a task whose difficulty is in the last centimetre, that is exactly
the part the generator gets wrong.

### 10.3 Two 2026 ideas that change the collection loop itself

[AXIS](https://arxiv.org/abs/2607.21588), July 2026, is a community data engine
rather than a dataset. Before it, contributing to a shared corpus meant owning
the specific hardware the corpus was defined on. AXIS runs teleoperation in a
browser, generates and validates new tasks automatically, and passes
community-collected demonstrations through automatic success checking, quality
filtering, trajectory smoothing and visual and physical augmentation before they
enter the training set. It currently holds 207 tasks and over 50,000
trajectories, and continual pretraining on it improved π0.5's overall success by
5.8 points. Its maturity is **Paper only** as regards an obtainable release at
the time of writing.

[RoboPocket](https://arxiv.org/abs/2603.05504), March 2026, attacks a different
waste. Handheld collection is open-loop: the collector does not know where the
policy is weak, so coverage of the states that matter is accidental. RoboPocket
runs the current policy remotely during collection and draws its predicted
trajectory into the collector's phone screen in augmented reality, so the person
can see a failure coming and deliberately collect there. It reports roughly
double the data efficiency of offline scaling. The same instinct appears in
[HIL-UMI](https://arxiv.org/abs/2609.20659), September 2026, which triggers
collection only where an energy score says the policy is out of its depth.

Both matter for the same reason, and it is the reason section 9 gives: if
quantity saturates and coverage does not, then knowing *where* to collect is
worth more than collecting faster.

## 11. What changed between May and September 2026

Four months is a short window and an unusually dense one. The table lists what
landed in it, in date order, with the label that says what you can do with each.
Read the last column as the reason it is on the list rather than as a summary.

| Date | What | Maturity | Why it is here |
| --- | --- | --- | --- |
| 8 June | [YUBI](https://arxiv.org/abs/2606.10244) gripper and its 8,434-hour corpus | hardware and software Downloadable; corpus Announced | a car manufacturer published open handheld hardware under a licence that permits commercial manufacture |
| 15 June | [HIW-500](https://huggingface.co/datasets/BitRobot/HIW-500) | Downloadable, CC BY 4.0 | the first large humanoid corpus recorded in real homes, and the most permissive one |
| 18 June | [HumanScale](https://arxiv.org/abs/2606.20521) | Paper only | claims egocentric human video beats teleoperated robot data for pretraining, at equal data volume |
| 25 June | [ABC-130K](https://huggingface.co/datasets/XDOF/ABC-130k) | Downloadable, Apache-2.0 | 3,553 hours of two-armed teleoperation, with the rig, the code and the evaluation logs |
| 6 July | [LeRobot v0.6.0](https://huggingface.co/blog/lerobot-release-v060) | Shipped | depth support, automatic language annotation, twice as fast data loading |
| 16 July | [Xiaomi-Robotics-1](https://arxiv.org/abs/2607.15330) | Paper only | a policy pretrained on over 100,000 hours of handheld data, which is a scale nobody had claimed before |
| 21 July | [Grabette](https://huggingface.co/blog/grabette) | Downloadable design | a €490 handheld recorder writing straight into the LeRobot format |
| 23 July | [AXIS](https://arxiv.org/abs/2607.21588) | Paper only | browser-based teleoperation with automatic task generation and quality filtering |
| 28 July | [HiFi-UMI](https://arxiv.org/abs/2607.25895) | data Downloadable, rig Demonstrated | a policy trained only on robot-free data matched teleoperation on a real robot |
| 30 July | [ACE-Data-0](https://arxiv.org/abs/2607.28625) | Announced, research-only | whole homes turned into synchronised capture studios |
| 3 August | LeRobot v0.6.1 | Shipped | better automatic annotation of episodes |
| 19 August | [RoboEdit](https://arxiv.org/abs/2608.18948) | Paper only | 174,000 human clips rewritten as robot clips across seven embodiments |
| 3 September | [PrimeBot 1,500 hours](https://arxiv.org/abs/2609.03591) | Downloadable, CC BY-SA 4.0 | reports continued scaling where the 2024 law reported saturation |
| 9 September | [HuRo](https://arxiv.org/abs/2609.10706) | Paper only | 630,000 human-video episodes converted to robot actions |
| 16 September | [UMI-Bridge](https://arxiv.org/abs/2609.18232) | Paper only | matches a robot-only baseline using a quarter of the robot data |
| 19 September | [Whole-Body UMI](https://arxiv.org/abs/2609.22829) | Demonstrated | handheld data driving a humanoid's whole body |
| 21 September | [UMI Arena](https://umi-arena.airoa.io/) opens | Announced | the first shared evaluation floor for handheld-collected policies |

Read down that list and one shape emerges. Nothing in it is a new policy
architecture. Almost everything is either a way to collect without a robot, a way
to make already-collected data trainable, or a corpus published under a licence
that lets somebody else use it. The field spent the summer on its data supply.

The second shape is a divergence between two claims that cannot both stay true.
HiFi-UMI and HumanScale, six weeks apart, argue that robot-free data is
sufficient and that human video is superior. PrimeBot, in September, argues that
more teleoperated robot data keeps paying. Both are honest about their evidence
and both may be right about their own setting, and the resolution will be an
empirical question about which tasks fall on which side of the line. It is the
most interesting open question in this document.

## 12. What none of this fixes

Five things survive everything above, and a development that claims to fix one of
them deserves more scrutiny than it will usually get.

**Nobody can compare two numbers.** Section 2.1 is not a pedantic preamble, it is
the state of the field. An episode count means nothing without knowing what an
episode was, an hours count flatters long episodes, and there is no maintained
index that records either. Until there is, every league table of dataset sizes is
a comparison of incompatible units, and the UMI Arena is a workshop competition
rather than a standard.

**The robot was not there.** Every route that removes the robot from collection —
handheld grippers, exoskeletons, human video — produces trajectories that nothing
has verified the robot can execute. The kinematic limits are unknown at
collection time, so infeasible motions have to be filtered afterwards, and the
filter is a heuristic. This is the single limitation shared by section 4, section
5 and section 8, and it is structural rather than an engineering gap.

**Force is still missing from almost everything.** Colour video and joint angles
are cheap to record and are what nearly every corpus contains. How hard the
gripper pressed is expensive to record, is absent from every large open dataset
except RH20T and a handful of research rigs, and is exactly the signal the
[gripping area](../07_gripping/01_overview.md) says decides whether contact-rich
tasks work. Adding a force channel to a dataset format is easy; adding it to
three thousand hours of recordings that were made without a force sensor is
impossible.

**Evaluation costs more than collection.** Every claim in this document about
success rates rests on real-robot rollouts, and those are slow, are run by the
authors, and are almost never reproduced. ABC-130K publishing its evaluation logs
and rubrics is notable precisely because it is unusual. The reason simulated
evaluation gets so much attention is not that anyone thinks it is accurate; it is
that the real thing does not scale.

**Cheaper collection does not make collection free.** The hardware price has
fallen by more than an order of magnitude, and the cost that remains is a
person's attention, one episode at a time. The scaling results in section 9 say
what that person should spend their attention on — more rooms and more objects,
not more repetitions — and that is a change in what you do, not a change in how
long it takes. A week of collecting is still a week.
