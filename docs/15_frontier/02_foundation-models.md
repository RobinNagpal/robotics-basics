# Foundation models and generalist policies for robot arms in 2026

For about three years a group of well-funded laboratories has been trying to build
one model that controls any robot arm at any task, the way one language model
answers any question. This document is the record of what they have actually
produced, as of 23 September 2026. It names every significant model, says what it
replaced, says how it was built, and says what it still cannot do.

This is the *events* document for that effort. Its companion, [what is changing in
robot manipulation](../10_one-arm-training/05_what-is-changing.md), is the
*mechanism* document: it explains why the field moves in the direction it does,
and it is the better thing to read if you want to understand next year's
announcements rather than this year's. The two overlap deliberately. Where they
differ in emphasis, that document is about forces and this one is about dated
facts.

## Who this is for, and what it is for

This is written for someone who can picture a robot arm, has read the
[object perception](../06_object-perception/01_overview.md) and
[gripping](../07_gripping/01_overview.md) areas or knows the equivalent, and now
keeps seeing announcements about models that supposedly do all of it at once. You
do not need to have trained a policy. Every term is explained where it first
appears, starting with the phrase "vision-language-action model" in section 1.

Four commitments shape everything below, and they exist because robotics reporting
routinely fails at all four.

Every development is written up the same way: what came before it, what changed,
how it was achieved, why that matters, and what it still cannot do. The third of
those is the one most write-ups skip, and it is the one that lets you judge
whether a result will generalise to your robot. The fifth is non-negotiable here,
because a development with no stated limits has not been understood.

Every item carries a maturity label, defined in [section 2](#2-how-to-read-this-document).
The difference between weights you can download tonight and a video with a date on
it is enormous, and a great deal of writing about this field blurs the two.

Every licence was read from the project's own licence file or its own model card,
not from a badge or a blog post. Code and weights are frequently under different
licences, and in this area the weights are usually the more restrictive of the two.

Everything says whether it runs without an NVIDIA graphics card, because this
repository is used on an Apple Silicon Mac and most of this field assumes
otherwise. [Section 12](#12-what-runs-on-an-apple-silicon-mac) collects the
answers in one place.

## Contents

1. [What a vision-language-action model is](#1-what-a-vision-language-action-model-is)
2. [How to read this document](#2-how-to-read-this-document)
3. [Where the line comes from: RT-1 to OpenVLA](#3-where-the-line-comes-from-rt-1-to-openvla)
4. [Physical Intelligence, and the pi models](#4-physical-intelligence-and-the-pi-models)
5. [Google DeepMind: Gemini Robotics 2 and ER 2](#5-google-deepmind-gemini-robotics-2-and-er-2)
6. [NVIDIA Isaac GR00T](#6-nvidia-isaac-gr00t)
7. [Figure: Helix 02, Index and Helix 2.5](#7-figure-helix-02-index-and-helix-25)
8. [Dyna Robotics and the million-hour scaling law](#8-dyna-robotics-and-the-million-hour-scaling-law)
9. [Skild: learning from one video, and self-play](#9-skild-learning-from-one-video-and-self-play)
10. [The open shelf: what you can download today](#10-the-open-shelf-what-you-can-download-today)
11. [What none of them can do yet](#11-what-none-of-them-can-do-yet)
12. [What runs on an Apple Silicon Mac](#12-what-runs-on-an-apple-silicon-mac)
13. [The whole field on one page](#13-the-whole-field-on-one-page)
14. [Which of these claims will age worst](#14-which-of-these-claims-will-age-worst)

---

## 1. What a vision-language-action model is

A **vision-language-action model**, almost always shortened to **VLA**, is a
single neural network that takes camera images and a sentence in ordinary English,
and outputs the numbers that move a robot. There is no separate object detector,
no separate grasp planner and no separate motion planner in the path. You give it
a picture of a kitchen and the words "put the mug in the sink", and it emits joint
or end-effector commands at some rate until the mug is in the sink.

The idea has one specific ancestor. Somebody noticed that a **vision-language
model** — a network already trained on hundreds of millions of internet images
paired with text, which can answer questions about a photograph — already contains
most of what a robot needs in order to know what a mug is, where it is, and that
sinks are for putting things in. What it lacks is a way to say "move 3 mm to the
left". So you take that pretrained model and teach it to emit actions as well as
words. The robot inherits everything the internet taught the model about objects,
and you only have to supply the part about moving.

The word **generalist** attached to such a model means it was trained on many
tasks and often many different robots at once, and is meant to be used on tasks it
was not specifically trained for. A **policy** is the older and more general term
for anything that maps an observation to an action; every VLA is a policy, but not
every policy is a VLA.

Two mechanisms come up constantly below, so they are worth defining once.

**Action chunking** means the model predicts a short sequence of future actions in
one go — typically half a second to two seconds of motion — rather than one
command at a time. This exists because the models are large and slow. If you can
only run the network ten times a second but the arm needs commands at fifty hertz,
predicting a chunk of fifty commands per network call solves the arithmetic. It
also makes the motion smoother, because consecutive commands come from one
decision rather than from ten independent ones.

**Flow matching** is the method almost all of these models use to turn the
network's internal state into those continuous numbers. It starts from random
noise and repeatedly nudges it towards a plausible action sequence, learning the
direction of each nudge during training. It is used because ordinary regression
tends to average over the several different correct ways of doing a task and
produce the average, which is usually wrong. Whether it actually earns its cost is
an open question, and the [mechanism
document](../10_one-arm-training/05_what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do)
records a 2026 study that found no measurable advantage over plain regression.

## 2. How to read this document

Every item below carries one of five maturity labels. The table gives the label,
what it means, and the question you should ask before believing anything else
about that item. Read it as a ladder: things at the top you can have today, and
things at the bottom you cannot have at all.

| Label | What it means | The question it answers |
| --- | --- | --- |
| **Shipped** | Weights or a product you can obtain today, possibly for money or through an approval process | Can I get it? |
| **Downloadable** | Open weights, with a named licence, from a public host | Can I get it without asking anyone? |
| **Demonstrated** | Shown working on real hardware, by its authors, but not obtainable | Has anyone outside the company run it? |
| **Paper only** | Results published, no artefact released | Is there anything but the PDF? |
| **Announced** | Stated with a date, nothing shown working | Is there anything but the press release? |

Two conventions about numbers apply throughout. Where a number was stated in words
by its source, it appears here as a plain figure. Where it was only plotted on a
chart, the text says so and gives it as approximate, because reading a value off
somebody's bar chart is not the same as being told it.

One convention about licences applies throughout. When a project's code and its
weights are under different licences, both are named. When a model card declares
no licence at all, that is recorded as a fact about the model, because weights
published with no licence grant you no rights by default.

## 3. Where the line comes from: RT-1 to OpenVLA

You cannot judge any 2026 model without knowing what the 2023 state of the art
actually was, so this section is the "what came before" for everything after it.

### 3.1 RT-2, and the trick the whole field is built on

**What it was before.** Until 2023, a robot that could do many tasks was a robot
with many programs. Each task had its own perception code, its own grasp logic and
its own motion sequence, written by a person. Learned policies existed, but a
policy trained on one set of objects failed on objects it had never seen, because
nothing in the training data told it what a "mug" was in general.

**What changed.** Google's [RT-2](https://robotics-transformer2.github.io/),
published in 2023, showed that a robot could act on objects and instructions that
appeared nowhere in its robot training data. The project page reports roughly
twice the generalisation of its predecessors across several axes, measured over
6,000 trials, and 90 per cent against a previous best of 77 per cent on the
language-table benchmark.

**How it was achieved.** The mechanism is one sentence and it is the foundation of
everything below. RT-2 represented robot actions as text. A movement became a
string of numbers such as `1 128 91 241 5 101 127 217`, and the model was then
fine-tuned on robot trajectories and ordinary internet image-and-text questions at
the same time. Because actions were just more text, no new output machinery was
needed, and the model's existing knowledge of the visual world survived the
fine-tuning instead of being overwritten by it. Two versions were built, one on a
12-billion-parameter backbone and one on a 55-billion-parameter backbone.

**Why it matters.** It established that robot generalisation could be bought from
internet data rather than earned from robot data. Every model in this document
descends from that claim.

**What it still cannot do.** RT-2 was never released. There are no weights, no
code and no way to reproduce it, and it ran on hardware and a robot fleet that
existed inside one company. Its practical legacy is the idea, not the artefact.
Maturity: **Paper only**, and permanently so.

### 3.2 Open X-Embodiment, and the data that made openness possible

The same group organised
[Open X-Embodiment](https://robotics-transformer-x.github.io/), a pooled dataset
gathered from many laboratories and many different robots. This mattered because
the binding constraint on the whole field is robot data, and no single laboratory
had enough. Pooling let an outsider train a cross-robot model without owning a
robot fleet. The [mechanism
document](../10_one-arm-training/05_what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do)
puts the corpus at about 2.4 million episodes, which is large for robotics and
minuscule next to an internet image dataset.

### 3.3 OpenVLA, which made the idea public

**What it was before.** RT-2's weights were unavailable, so a university group
could read about the method and not use it.

**What changed.** [OpenVLA](https://arxiv.org/abs/2406.09246), published in June
2024, released a working VLA that anyone could download. Its paper reports beating
RT-2-X, the 55-billion-parameter version, by 16.5 percentage points of absolute
task success across 29 tasks, while being seven times smaller.

**How it was achieved.** OpenVLA is a 7-billion-parameter model trained on 970,000
real robot demonstrations drawn from Open X-Embodiment. The size reduction came
from using a vision-language backbone chosen for efficiency rather than for
maximum capability, and the performance came from training on far more distinct
robots than RT-2 had seen.

**Why it matters.** It is still, in September 2026, the most-downloaded robotics
model on Hugging Face, at roughly 437,000 downloads. That is not because it is the
best; it is because it was first, it is genuinely open, and every later paper
benchmarks against it.

**What it still cannot do.** The original model emits one action at a time, which
makes it slow. Its own successor recipe,
[OpenVLA-OFT](https://openvla-oft.github.io/), fixed that with parallel decoding
and action chunking, reporting 97.1 per cent average success across the four
LIBERO simulation task suites, 26 times faster action generation and three times
lower latency. Both repositories have been quiet since 2025 —
[openvla](https://github.com/openvla/openvla) last saw a commit in March 2025 and
[openvla-oft](https://github.com/moojink/openvla-oft) in September 2025. As the
mechanism document warns, a dormant repository is not a verdict on a method, but
in this case the frontier genuinely has moved on. Maturity: **Downloadable**, MIT
licence for both the code and the weights, verified from the repositories' own
licence files and the model card.

## 4. Physical Intelligence, and the pi models

Physical Intelligence is a San Francisco company whose models are named with the
Greek letter pi. It is the most important single actor in this document, partly
because its models are good and partly because it is the only frontier laboratory
that has released any of them.

### 4.1 π0 and π0.5, the part that is open

**What it was before.** OpenVLA and its relatives emitted discrete action tokens,
one step at a time, and were trained on pooled academic data.

**What changed.** [π0](https://www.pi.website/blog), announced on 31 October 2024
and open-sourced on 4 February 2025, produced continuous actions through flow
matching at rates high enough for dexterous two-armed tasks such as folding
laundry. [π0.5](https://www.pi.website/blog/pi05), announced on
22 April 2025, added what its authors call open-world generalisation, meaning it
could work in homes it had never seen.

**How it was achieved.** π0 attached a flow-matching action expert to a pretrained
vision-language model, so the language model handled understanding and a separate
small network handled the continuous numbers. The base checkpoints were trained on
what the [openpi repository](https://github.com/Physical-Intelligence/openpi) calls
10,000 or more hours of robot data. π0.5 added a training technique the company
calls knowledge insulation, which keeps the fine-tuning on robot actions from
degrading what the language model already knew. A separate model, π0-FAST, took
the alternative route of compressing action sequences with a tokenizer called FAST
and staying autoregressive.

**Why it matters.** These are the only frontier-laboratory VLA weights that anyone
can download. The openpi repository is Apache-2.0, verified from its licence file,
and provides base checkpoints for π0, π0-FAST and π0.5 plus fine-tuned checkpoints
for the ALOHA and DROID robot platforms.

**What it still cannot do.** It cannot run on your Mac. The openpi repository
states plainly that it requires an NVIDIA graphics card — more than 8 GB of video
memory for inference, more than 70 GB for full fine-tuning — and that it has only
been tested on Ubuntu 22.04. The repository's own update log has not recorded a
new model since September 2025, and its most recent commits, through August 2026,
are documentation and dependency work. Maturity: **Downloadable**, Apache-2.0 for
the code, with checkpoints served from the project's own storage bucket.

### 4.2 π0.6 and π*0.6: a policy that improves by practising

**What it was before.** Every model above learns by copying demonstrations. That
gives a policy the shape of a task quickly, and then stops improving, because the
demonstrations show what success looks like and never show how to recover from the
particular mistakes this policy makes.

**What changed.** [π*0.6](https://www.pi.website/blog/pistar06), published on 17
November 2025, learns from its own experience. The company's text claims the method
"more than doubles the throughput on some of the hardest tasks", and describes a
robot making espresso drinks from 5:30 in the morning to 11:30 at night, folding
50 different novel laundry items in a home it had not seen, and assembling and
labelling 59 boxes used for packaging chocolates in a real factory. The per-task
throughput and success figures appear only as bar charts on that page and not in
the text; read off those charts, box assembly moves from roughly 3 to roughly 14
completions an hour and from roughly 40 to roughly 90 per cent success, and
laundry folding from roughly 15 to roughly 65 completions an hour.

**How it was achieved.** The base π0.6 is a 5-billion-parameter vision-language
model with an action expert attached, slightly larger than π0.5 and able to accept
more varied conditioning than plain instructions. The method on top is called
Recap, which stands for reinforcement learning with experience and corrections via
advantage-conditioned policies. It has three stages. The robot first learns from
ordinary demonstrations. Then a human teleoperator watches it work and takes over
when it starts to go wrong, which supplies corrections for the failures this
particular policy actually makes rather than for failures in general. Then the
robot practises alone. The technical problem with practising is knowing which
earlier action caused a failure that only became visible much later, and Recap
solves it by training a value function that scores how good each situation is.
The difference between consecutive scores says whether the action in between
helped, and the policy is trained with that difference as an input, so at run time
it can be asked for the actions it has learned are good ones.

**Why it matters.** This is the clearest published evidence that a large policy can
get better by working rather than by being shown more examples. The [mechanism
document](../10_one-arm-training/05_what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do)
identifies demonstrate-then-polish as the most important arrival of the year, and
this is the most-documented instance of it.

**What it still cannot do.** The company itself names the bottleneck: the quality
of the corrections depends on a person noticing the right moment to intervene,
which works for obvious mistakes and not for subtle ones. Each application still
needed its own task-specific demonstrations and its own on-robot practice, so
these are specialists built from a generalist, not a generalist that does the
tasks. And none of it is released. Maturity: **Demonstrated**.

### 4.3 π0.7, the current frontier model

**What it was before.** π*0.6 produced excellent specialists, one per task, each
needing its own reinforcement learning run.

**What changed.** [π0.7](https://www.pi.website/blog/pi07), published on 16 April
2026 with a paper at [arXiv 2604.15483](https://arxiv.org/abs/2604.15483), is a
single generalist that the company reports matching those specialists. On laundry
with T-shirts and shorts it reports 1.5 times the normalised throughput of the
π*0.6 specialist, and on diverse laundry items 2.0 times. It also reports folding
laundry on a two-armed UR5e system that had never been trained on either that task
or that robot, at a success rate matching human teleoperators with more than 375
hours of experience.

**How it was achieved.** The mechanism is worth stating carefully, because it is
the most interesting idea of the year and it is not an architecture change. π0.7 is
trained with unusually rich conditioning attached to every episode. Alongside the
instruction, each training example carries language describing the individual
sub-steps, metadata describing *how* the task was performed — its speed, its
quality — a label saying whether the actions are joint angles or end-effector
poses, and images of visual subgoals. At run time a high-level policy proposes the
next sub-task in language, a small world model turns that language into a picture
of what the scene should look like next, and π0.7 acts towards that picture. The
payoff of the metadata is that data which would normally be thrown away, such as
failed autonomous attempts and sloppy demonstrations, can be kept and labelled as
such, because the model has been taught what the labels mean.

**Why it matters.** It makes a generalist steerable. You are no longer limited to
naming a task; you can tell the model how fast to go, which control mode to use,
and show it a picture of the intended outcome. That is a much richer interface
than a sentence, and it is the reason the model can absorb data from sources that
disagree with each other.

**What it still cannot do.** On a genuinely novel appliance — an air fryer — the
blog reports the model making a reasonable attempt and not finishing, and needing
step-by-step language coaching to complete it. The authors also say the training
set is now large and varied enough that they cannot trace which episodes produced
a given behaviour, which is a real problem for anyone who has to certify what a
machine will do. Every demonstration is tabletop or domestic manipulation. And
π0.7 is not in openpi and has no released weights. Maturity: **Demonstrated**.

## 5. Google DeepMind: Gemini Robotics 2 and ER 2

This is the line that actually descends from RT-2, through RT-X and the first
Gemini Robotics models of 2025.

**What it was before.** Gemini Robotics 1.5, in September 2025, controlled the
upper body of a robot doing tabletop tasks, with a separate reasoning model for
planning. An intermediate reasoning release, [Gemini Robotics ER
1.6](https://deepmind.google/blog/gemini-robotics-er-1-6/), arrived on 14 April
2026 and added multi-view reasoning and the ability to read gauges and dials,
which it reports doing with 93 per cent success when its agentic vision mode is
enabled.

**What changed.** On 30 July 2026 Google DeepMind published [Gemini Robotics
2](https://deepmind.google/blog/gemini-robotics-2-brings-whole-body-intelligence-to-robots)
and [Gemini Robotics ER
2](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-robotics-er-2/).
Three things are new: control of a whole humanoid body rather than an upper body,
manipulation with multi-fingered hands rather than grippers, and two robots
working on the same task together.

**How it was achieved.** The system is split in two on purpose. Gemini Robotics ER
2 is the reasoning half — a vision-language model that plans, watches video to
check whether a step worked, talks to people, and can call tools including Google
Search. Gemini Robotics 2 is the acting half, the VLA that turns images and
language into motor commands. A third model, Gemini Robotics On-Device 2, is a
smaller VLA meant to run on the robot's own computer. The interesting mechanism in
the on-device model is what Google calls motion transfer, which the announcement
says adapts the model to a new robot body in a few hours and typically with fewer
than 200 examples.

**Why it matters.** The numbers are the most transparent in this document, because
the announcement publishes per-skill success rates rather than a single headline,
and states that each figure is an average success rate over several tasks within
that skill category. The table below gives them. Read it as evidence of where
whole-body humanoid manipulation actually stands: reaching for things is roughly a
two-in-three proposition, and fine finger work is usually worse than a coin toss.

| Robot and hand | Skill | Success rate |
| --- | --- | --- |
| Apptronik Apollo 2, Inspire hands | pick from a shelf | 76.3% |
| Apptronik Apollo 2, Inspire hands | pick from a table | 68.4% |
| Apptronik Apollo 2, Inspire hands | pick from the floor | 45.7% |
| Apptronik Apollo 2, SharpaWave hands | unscrew a bulb | 92% |
| Apptronik Apollo 2, SharpaWave hands | tie a bin bag | 44% |
| Apptronik Apollo 2, SharpaWave hands | use a ziplock bag | 40% |
| Apptronik Apollo 2, SharpaWave hands | screw in a bulb | 36% |
| Apptronik Apollo 2, SharpaWave hands | use a dustpan | 32% |
| Franka Duo, Robotiq gripper | precise insertion | 89.6% |
| Franka Duo, Robotiq gripper | diverse tool kitting | 78.9% |
| Franka Duo, Robotiq gripper | general pick and place | 74.2% |

The ER 2 model publishes its own numbers separately: 57.4 per cent accuracy at
classifying how far through a task a robot is, and 91.3 per cent at finding the
moment in a video when something happened, with a mean absolute error of 0.96
seconds.

**What it still cannot do.** Google states three limits itself. The robots need to
move faster. Multi-finger dexterous manipulation remains difficult, which the
36 per cent and 32 per cent rows above confirm. And the reasoning model has to
self-correct when a step fails, which is listed as a requirement rather than an
achievement. The unscrew-a-bulb figure of 92 per cent against screw-in-a-bulb at
36 per cent is worth sitting with: taking things apart is far easier than putting
them together, because assembly requires the kind of force and alignment control
that [the gripping area](../07_gripping/01_overview.md) is about and that none of
these models expose.

Maturity is split, which is why the split matters. Gemini Robotics ER 2 is
**Shipped**: it is available through the Gemini application programming interface
and Google AI Studio, and in private preview on Google's enterprise agent
platform, so you can use it today without owning a robot. The VLA and the
on-device VLA are **Demonstrated**: access is limited to early-access partners
through a sign-up form, and no weights are published. Nothing in this family is
downloadable, and nothing in it runs locally on a Mac, because the reasoning half
is an API call and the acting half is not distributed at all.

## 6. NVIDIA Isaac GR00T

GR00T is NVIDIA's open humanoid manipulation model, and it is the only frontier-
scale VLA whose weights you can fetch without an approval process.

**What it was before.** N1 appeared in June 2025 and N1.5 in December 2025, both
built on NVIDIA's own Eagle vision-language backbone, and both trained
predominantly on robot demonstrations and simulation.

**What changed.** [GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T) was tagged on
18 April 2026 as a general-availability release, which NVIDIA defines as carrying
support and stability guarantees rather than being an experiment. The repository
describes it as delivering performance comparable to N1.6 with better
generalisation and better instruction-following. Note what that sentence does not
say: the headline claim is not a higher score.

**How it was achieved.** Three changes matter. The vision-language backbone
changed from NVIDIA's Eagle to Cosmos-Reason2-2B, built on the Qwen3-VL
architecture, which lets the model take images at their native aspect ratio
without padding. The action space became *relative* to the end-effector's current
pose rather than absolute, which the repository identifies as the key factor in
cross-robot performance, because a movement of three centimetres to the left means
the same thing on every body while a target coordinate does not. And the model was
pretrained on 20,000 hours of human video from a corpus NVIDIA calls EgoScale,
alongside robot demonstrations — which only works because the relative
end-effector representation is the same for a human hand and a robot gripper. The
action head remains a flow-matching diffusion transformer, reduced from 32 layers
to 16, while the state and action dimensions grew from 29 to 132 and the action
chunk grew from 16 steps to 40.

**Why it matters.** Human video is abundant and robot demonstrations are not, and
this is a released model that demonstrates the transfer working at scale. It is
also the model most likely to be the one you actually try, because it is 3 billion
parameters rather than 7, it is integrated into LeRobot, and NVIDIA supports it.

**What it still cannot do.** It needs an NVIDIA graphics card, and there is no way
around that: inference wants 16 GB or more of video memory, fine-tuning wants 40 GB
or more, and the supported platforms are CUDA 12.8 desktop cards, Jetson Thor and
Orin on JetPack 7.2, and DGX Spark. Nothing about it runs on a Mac.

The licence needs care, because the repository contradicts itself. The prose near
the top of the README says GR00T N1.7 "is fully commercially licensable under
Apache 2.0". The licence section of the same README, and the [model card on
Hugging Face](https://huggingface.co/nvidia/GR00T-N1.7-3B), both say something
narrower: the *code* is Apache-2.0, which the repository's licence file confirms,
and the *weights* are under the [NVIDIA Open Model License
Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).
That agreement does permit commercial use and does let you own derivative models,
so it is genuinely usable, but it carries conditions Apache-2.0 does not: an
attribution notice on redistribution, a clause terminating the licence if you
disable a safety guardrail without substituting a similar one, and a requirement
that use stays consistent with NVIDIA's separately published trustworthy-AI terms.
Treat the weights as commercially usable with conditions, and treat the Apache-2.0
sentence in the README as loose writing about the code. Maturity: **Downloadable**,
with the two licences above.

## 7. Figure: Helix 02, Index and Helix 2.5

Figure builds a humanoid and the model that runs it. Its 2026 work is the most
aggressive bet in this document on one idea: that the way out of the data problem
is to record enormous quantities of ordinary people doing ordinary things.

### 7.1 Helix 02

**What it was before.** The original Helix controlled the robot's upper body from
camera images. Walking and balance were handled by conventional control code
underneath.

**What changed.** [Helix 02](https://www.figure.ai/news/helix-02), published on 27
January 2026, controls the whole robot as one system — walking, manipulating and
balancing together. Figure reports a continuous four-minute dishwasher-loading
task comprising 61 separate locomotion-and-manipulation actions, and states that
the neural controller replaced 109,504 lines of hand-written C++.

**How it was achieved.** The model is a three-layer stack running at three
different rates, and the rates are the point. A 10-million-parameter network
called System 0 runs at 1,000 hertz and handles balance and whole-body
coordination; it was trained on more than 1,000 hours of human motion retargeted
to the robot's joints, across more than 200,000 parallel simulated environments.
System 1 runs at 200 hertz and is a transformer that turns perception into joint
targets, taking head cameras, palm cameras, fingertip touch sensors and
whole-body proprioception. System 2 is the slow layer that understands the scene
and the language and produces goals. The fingertip sensors are reported as
detecting forces as small as three grams.

**Why it matters.** It is the clearest demonstration that the split between
"controller" and "policy" can be collapsed into one learned stack, and the
109,504-line figure is a concrete measure of how much hand-written specification
that removes.

**What it still cannot do.** Figure says only that the results are early and names
no failure modes, which is itself a limitation of the report rather than of the
robot. There is no published success rate for the dishwasher task, no comparison
against the C++ it replaced, and no released artefact. Maturity: **Demonstrated**.

### 7.2 Index

**What it was before.** Robot training data came from teleoperation, which means
somebody drives the robot through the task. It is accurate, it is slow, and it
requires a robot per collector.

**What changed.** [Index](https://www.figure.ai/news/introducing-index), announced
on 25 August 2026, is a phone app. People record themselves doing ordinary tasks
and upload the video. Figure reports 44,000 weekly active users across 108
countries, more than 16 million videos uploaded, and an intake of 30 minutes of
video every second. It also publishes a diversity measure: per 1,000 hours
collected, the corpus contains 373 unique tasks, 1,146 unique objects and 116
unique environments.

**How it was achieved.** The mechanism is distribution rather than technology.
Figure says it built the pipeline itself because data vendors could not meet its
throughput, diversity or quality requirements.

**Why it matters.** The diversity figures are the interesting part, not the volume.
A thousand hours of teleoperation in one laboratory might contain a dozen tasks and
one room. A thousand hours of Index contains 373 tasks and 116 environments, and
the [mechanism
document](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
explains why that distinction decides everything: more data of the same kind
stopped helping years ago.

**What it still cannot do.** Human video has no robot actions in it. Somebody has
to bridge from a hand in a video to a gripper on an arm, and the announcement does
not say how. The corpus is not published. Maturity: **Shipped** as a product you
can install and contribute to, and not obtainable as a dataset.

### 7.3 Helix 2.5

**What it was before.** Helix 02 needed task-specific data collected in the
environment where the robot would be deployed. That is the industry's standard
practice and it does not scale, because it means visiting every home.

**What changed.** [Helix
2.5](https://www.figure.ai/news/helix-2-5-zero-shot-30-home-generalization),
published on 17 September 2026, performs three long tasks — tidying a living room,
folding towels and making a bed — in 30 real homes in the Bay Area where no data
was collected, with no weights adapted to those homes. Figure reports 56 per cent
success for the Index-pretrained model against 9 per cent for the same model
trained from scratch. Success was scored with no partial credit: every toy in the
basket, every towel folded, the bed completely made. The evaluation criteria were
fixed before testing began.

**How it was achieved.** The striking choice is what Helix 2.5 did *not* start
from. Helix 02 began with a pretrained vision-language model, as every other model
in this document does. Helix 2.5 was pretrained from random initialisation
entirely on Index — that is, on human video rather than on the internet. Figure
also reports a scaling law: using four nested subsets of Index spanning an
eightfold range of data, it predicted the largest run's held-out loss before
training it, with a forecasting error of 0.54 per cent. The company states it has
committed 3.5 billion dollars of compute to training Helix, and, on this page, puts
Index intake at roughly 35 minutes of new human experience every second — higher
than the 30 minutes per second reported three weeks earlier, which is consistent
with a growing user base.

**Why it matters.** Two things. The first is that pretraining on human video alone
beat pretraining on nothing by more than six times, on real homes, on complete
tasks. The second is quieter and more important: a predictable scaling law is what
turns robot learning from a research activity into an engineering one, because it
lets you decide whether a run is worth its cost before you spend it.

**What it still cannot do.** Figure says in the announcement that the point is not
that general humanoid robotics is solved, and the honest reading of 56 per cent is
that roughly two attempts in five fail outright. The scaling-law result held model
size and downstream training fixed, so it says nothing about whether more compute
or a bigger model helps. Three tasks in one metropolitan area is a narrow test.
And nothing is released. Maturity: **Demonstrated**.

## 8. Dyna Robotics and the million-hour scaling law

Dyna Robotics is the development I would have missed by relying on memory, and it
is the most quantitatively serious piece of work in this document.

**What it was before.** Every model above learns a policy: observation in, action
out. Nothing in the model represents what will happen next, so nothing in it can
learn from video of a task being done by somebody it cannot imitate.

**What changed.** [Dyna-2](https://www.dyna.co/research/dyna-2), published in
August 2026, is what the company calls a world-action model. It was pretrained on
more than one million hours of first-person human video, which the company
describes as about 170 years of waking experience, and the results are reported as
scaling laws rather than as headline successes.

**How it was achieved.** Dyna-2 is a single generative model built on a
video-diffusion backbone, using a mixture-of-transformers arrangement of diffusion
transformer layers trained with flow matching. It denoises future video and future
actions, jointly or separately. That design is what lets it train on video with no
action labels: predicting the next frames is a supervised problem that ordinary
video can answer, and the action head shares the representation the video head
learned. The human video was processed through a pipeline that extracts and
validates three-dimensional hand poses, which is the bridge from a hand to a
gripper that Figure's Index announcement leaves unspecified.

**Why it matters.** The company reports three results, and the middle one is the
one to remember. On held-out human video, error falls as a power law, from 0.062
to 0.053 mean squared error across the data ladder with a coefficient of
determination of 0.919. On the robot, the mean normalised score across 14
manipulation tasks rises from 20 to 28 to 45 to 53 per cent as pretraining scales
from one thousand to one million hours. And the company claims this is the first
scaling law demonstrated across the embodiment gap — held-out *robot* validation
metrics improving monotonically as purely *human* data grows. If that holds, it
means the data problem in robotics has an answer that does not involve robots.
Individual task results include 90 per cent on turning a key in a lockbox at the
one-million-hour scale, 50 per cent on untwisting a bottle cap with only ten
minutes of task-specific data, and 83 per cent on retrieving a named drink. The
robots were bimanual six-degree-of-freedom YAM arms with parallel jaws, a 20-degree-
of-freedom WUJI-2 multi-fingered hand, and an early semi-humanoid prototype. In a
separate post dated 27 August 2026 the company reports a restaurant customer, Din
Tai Fung, expanding from pilot sites to all its locations.

**What it still cannot do.** The company explicitly defers compute and model-size
scaling to future work, which means the scaling law it published varies one axis
only. A mean normalised score of 53 per cent across 14 tasks is a research result,
not a product specification, and the post does not give per-task success rates for
most of the 14. Nothing is released — no weights, no code, no dataset. Maturity:
**Demonstrated**, with the deployment claim separately **Shipped** as a commercial
service.

## 9. Skild: learning from one video, and self-play

Skild AI's public work moved faster in 2026 than any other company's in this
document, and the two most recent items are less than six weeks old.

### 9.1 S1

**What it was before.** Every model above is told what to do in words. That is a
narrow channel. "Fold the towel" does not say which fold, in which order, to what
standard, and the model has to guess from its training distribution.

**What changed.** [Skild S1](https://www.skild.ai/blogs/s1), published on 18
August 2026, takes a video instead. You show it one recording of the task and it
performs the task, with no fine-tuning. The company reports 66 per cent success on
unseen long-horizon tasks lasting four to ten minutes, against 9 per cent for
language-prompted VLAs, both trained on 100,000 hours; 96 per cent on tasks it has
seen; and that one video demonstration is worth roughly 380 post-training
episodes.

**How it was achieved.** The company gives little architectural detail, saying
only that S1 was built from the ground up as an in-context learner — meaning the
demonstration is supplied as input at run time rather than folded into the weights
by training. Its data mixture has three tiers: robot teleoperation, which is
accurate but does not scale; recordings from the universal manipulation interface,
a handheld gripper rig, which is moderate on every axis; and first-person human
video, which scales best. The company states it spends three dollars on quality
control for every dollar spent collecting, and reports a data ladder from 1,000 to
100,000 hours. Training ran on NVIDIA infrastructure.

**Why it matters.** In-context learning is how language models became useful
without fine-tuning, and this is the first well-documented claim that the same
thing works for manipulation. It also changes what a deployment looks like: if one
video is worth 380 episodes, then teaching a robot a new task becomes a recording
rather than a data-collection campaign. The robustness claim is the one worth
checking independently — the company reports that language-conditioned policies
degraded up to three times as much as S1 under distribution shift.

**What it still cannot do.** The post states no limitations, which the standard in
this document treats as a gap rather than as an absence of limits. It does not
name the robots used. It gives no architecture, no parameter count and no
independent evaluation. And S1 is available only to commercial partners and
through an early-access sign-up. Maturity: **Shipped** in the narrow sense that it
is in commercial use, and not obtainable by you.

### 9.2 Physical self-play

**What it was before.** A model pretrained on human data can, at best, do what the
humans in its data did.

**What changed.** On 23 September 2026 Skild published [physical
self-play](https://www.skild.ai/blogs/physical-self-play), in which S1 improves by
playing football against itself in simulation. The company reports 140 years of
simulated play in NVIDIA's Isaac Sim before the policy was transferred to a
physical humanoid, which then played real matches.

**How it was achieved.** Self-play is the method that produced AlphaGo Zero, which
the post cites as having beaten the original AlphaGo 100 games to nil after three
days. In simulation, two copies of the policy compete, and the reward is simply
whether you won, so no human has to write down what good play looks like. That is
the appeal: football has a score, and a score is a reward function nobody has to
specify.

**Why it matters.** It attacks the one ceiling that imitation learning cannot pass.
If a model only ever copies people, it cannot exceed people, and the post says so
directly.

**What it still cannot do.** The post states that robot football remains far below
human level, and that extending the approach to everyday tasks is ongoing work.
The unstated difficulty is the important one: football has a score and tidying a
kitchen does not, so it is not obvious that this transfers to the tasks anybody
wants. Maturity: **Demonstrated**, and closer to a research note than a result.

## 10. The open shelf: what you can download today

This section exists because the sections above are mostly about things you cannot
have. The list below is what a person with a laptop and a cheap arm can actually
obtain in September 2026, with the licence read from each project's own licence
file or model card.

The table is ordered by how likely it is to be useful to somebody learning, not by
capability. Read the licence column carefully: two of these declare no licence at
all on their weights, which means you have no granted rights to them whatever the
paper says.

| Model | Size | Code licence | Weights licence | Why you would choose it |
| --- | --- | --- | --- | --- |
| [SmolVLA](https://huggingface.co/lerobot/smolvla_base) | 450M | Apache-2.0 | Apache-2.0 | the only one that runs on consumer hardware and a Mac |
| [GR00T N1.7](https://huggingface.co/nvidia/GR00T-N1.7-3B) | 3B | Apache-2.0 | NVIDIA Open Model License | the most capable open model, supported by its vendor |
| [π0 / π0-FAST / π0.5](https://github.com/Physical-Intelligence/openpi) | not stated | Apache-2.0 | served from the project bucket | the only frontier-laboratory weights in existence |
| [MolmoAct2](https://huggingface.co/allenai/MolmoAct2) | 5B | Apache-2.0 | none declared on the card | the most thoroughly evaluated open model |
| [OpenVLA](https://huggingface.co/openvla/openvla-7b) | 7B | MIT | MIT | the baseline everything is compared against |
| [X-VLA](https://huggingface.co/2toINF/X-VLA-Pt) | not stated | not checked | Apache-2.0 | a cross-embodiment alternative, in LeRobot |
| [GigaBrain-0.7](https://huggingface.co/open-gigaai/GigaBrain-0.7-3.5B-Base) | 3.5B | Apache-2.0 | Apache-2.0 | the newest open frontier-style model |
| [OpenWAM-α](https://github.com/OpenWAM-Official/OpenWAM) | 5B backbone | Apache-2.0 | Apache-2.0 | the only open world-action model |

Four of those deserve a paragraph each.

**SmolVLA** is a 450-million-parameter model released on 3 June 2025 by Hugging
Face, combining a SmolVLM2 vision-language backbone with a roughly 100-million-
parameter flow-matching action expert. It was trained on about 10 million frames
from 487 community-contributed datasets, which its authors note is at least an
order of magnitude smaller than the standard benchmark corpora, and it reports
about 78 per cent success on real SO-100 arm tasks. Its
[announcement](https://huggingface.co/blog/smolvla) states it is small enough to
run on a central processing unit, train on a single consumer graphics card, or run
on a MacBook. For anyone learning on a hundred-dollar arm, this is the entry point.

**MolmoAct2**, published by the Allen Institute for AI on 4 May 2026 with a paper
at [arXiv 2605.02881](https://arxiv.org/abs/2605.02881), is a 5-billion-parameter
model that grafts a flow-matching continuous-action expert onto an autoregressive
vision-language model through per-layer key-value conditioning. It ships three new
datasets including 720 hours of two-armed teleoperation, an open action tokenizer
called OpenFAST, and an adaptive-depth reasoning variant called MolmoThink that
trades reasoning depth for latency. Its authors claim the most extensive empirical
study of any open VLA, spanning seven simulated and real benchmarks, and report
beating π0.5, and report that its embodied-reasoning backbone beats GPT-5 and
Gemini Robotics ER 1.5 across 13 embodied-reasoning benchmarks. The
[code](https://github.com/allenai/molmoact2) is Apache-2.0, verified from its
licence file. The [weights card](https://huggingface.co/allenai/MolmoAct2) declares
no licence in its metadata at all, which is almost certainly an oversight and is
nonetheless the legal position today. Ask before you build a product on it.

**GigaBrain-0.7**, published on 24 August 2026 with a paper at [arXiv
2608.15875](https://arxiv.org/abs/2608.15875), is a 3.5-billion-parameter model
trained on more than 37,000 hours of heterogeneous embodied data, using a
three-system architecture that unifies understanding, prediction and action with a
single-stage alignment step. It is Apache-2.0 on both code and weights. It reports
improvements over π0.5 on zero-shot and instruction-following tasks. It is the
closest thing on this shelf to an open equivalent of the frontier models in
sections 4 to 8, and it is six weeks old, so treat its claims as unreplicated.

**OpenWAM-α**, published on 4 September 2026 with a paper at [arXiv
2609.07398](https://arxiv.org/abs/2609.07398), is the open counterpart to Dyna-2.
It uses a Wan2.2-TI2V-5B video backbone with its native encoder and a dual-system
joint self-attention arrangement, pretrained on 518.5 million frames — about 6,400
hours — mixing 70 per cent robot data, split 40 per cent real and 30 per cent
simulated, with 30 per cent first-person human video. It is Apache-2.0. Note the
scale: 6,400 hours against Dyna-2's million. The open world-action model is smaller
than the closed one by a factor of about 150.

**[LeRobot](https://github.com/huggingface/lerobot)** is the thing that makes the
shelf usable, and it is more important than any single model on it. It is
Apache-2.0, it reached version 0.6.1 on 3 August 2026, and it now implements π0,
π0-FAST, π0.5, GR00T N1.7, SmolVLA, X-VLA, EO-1, MolmoAct2, WALL-OSS and EVO1 in
one library with one dataset format and one training script. The [mechanism
document](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
calls this consolidation the third and most underappreciated force in the field,
and this list is what it looks like in practice: ten separate research projects
with one installation procedure.

Two of the models LeRobot supports have licence problems worth naming. WALL-OSS,
published by X Square Robot in September 2025, declares no licence on its Hugging
Face card. EO-1 is MIT on its card. Check both yourself before shipping anything.

## 11. What none of them can do yet

This section is the one to read if you only read one, because it is the part the
announcements omit.

**None of them controls force.** Every model in this document outputs positions,
joint angles or end-effector poses. Not one of them exposes the contact forces
that [the gripping area](../07_gripping/01_overview.md) shows are what actually
decide whether a grip survives. Gemini Robotics 2's own numbers make the
consequence visible: 92 per cent at unscrewing a bulb and 36 per cent at screwing
one in. Taking apart needs position control and putting together needs force
control, and the gap between those two numbers is the gap between what VLAs do and
what assembly requires.

**None of them can refuse.** A policy always emits an action. There is no
mechanism in any of these models for saying "I do not recognise this, so I am
leaving it alone". The [object perception
overview](../06_object-perception/01_overview.md#21-when-a-model-makes-things-worse)
makes this argument in general and it applies with full force here: where doing
nothing is cheaper than being wrong, you need a checking step with a threshold you
chose, and none of these models provides one.

**They break in ways that are not obvious from benchmarks.** A September 2026
study, [LIBERO-VPro](https://arxiv.org/abs/2609.24350), tested six foundation
models — three VLAs and three world-action models — across 12 categories of visual
disturbance, 3,296 task-condition cases, roughly 196,000 simulated episodes and 200
real trials on a Franka Research 3 arm. Its finding is counterintuitive and worth
carrying around: the models tolerate severe occlusion of whole objects, and
degrade sharply when the small local cues at the point of interaction are
disturbed. They are also highly sensitive to stale or missing camera frames. A
benchmark that assumes clean, current, consistent images is not measuring the
thing that will fail.

**Generalising is not the same as running on your robot.** An August 2026 survey,
[The Embodiment Gap in Robot Foundation Models](https://arxiv.org/abs/2608.18433),
makes this its central point: a model can generalise and still require substantial
work before it runs on a particular body, and the amount of that work differs by
method and by robot in ways a success rate never reveals. The survey proposes a
reporting framework for exactly that hidden work. Until people adopt it, assume
that "works zero-shot" means "worked zero-shot on the authors' robot".

**The frontier is not reproducible.** π0.6, π*0.6, π0.7, Helix 02, Helix 2.5,
Dyna-2, Skild S1, Gemini Robotics 2 and Gemini Robotics On-Device 2 have all been
demonstrated and none of them has been released. Every headline number in sections
4 to 9 was produced and measured by the organisation that benefits from it, on
robots nobody outside can obtain, with evaluation protocols nobody outside can
repeat. That does not make the numbers false. It makes them unaudited, and the
distinction should change how much weight you put on them.

**The success rates are lower than the videos suggest.** Collected in one place:
56 per cent for Helix 2.5 across 30 homes, 53 per cent mean normalised score for
Dyna-2 across 14 tasks, 66 per cent for Skild S1 on unseen long tasks, 45.7 per
cent for Gemini Robotics 2 picking from the floor, 32 per cent using a dustpan.
These are genuinely impressive research results and they are nowhere near the
99-point-something per cent that an industrial cell requires. The [mechanism
document's fourth force](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
explains why that gap will close more slowly than the technology improves.

## 12. What runs on an Apple Silicon Mac

The answer is short and it is mostly no, and the useful part is knowing exactly
where the line falls.

[LeRobot installs and runs on macOS](https://huggingface.co/docs/lerobot/installation).
Its documentation gives Apple Silicon instructions explicitly, uses the Metal
Performance Shaders backend that PyTorch provides on Apple hardware, and notes
that on platforms where the default video decoder is unavailable it falls back to
a different one automatically. So the tooling is not the problem.

The models are. LeRobot's own [compute hardware
guide](https://huggingface.co/docs/lerobot/hardware_guide) groups policies by the
memory they need for training at batch size 8. The table below is that grouping,
and you should read it as a filter: find your hardware, and everything below your
row is out of reach.

| Policy group | Which policies | Video memory for training | Feasible on a Mac? |
| --- | --- | --- | --- |
| light behaviour cloning | ACT, VQ-BeT, TD-MPC | about 2 to 6 GB | yes, slowly |
| diffusion | diffusion policy, multi-task DiT | about 8 to 14 GB | marginal |
| small VLA | SmolVLA | about 10 to 16 GB | marginal |
| large VLA | π0, π0-FAST, π0.5, X-VLA, WALL-OSS | about 24 to 40 GB | no |
| multimodal | GR00T, EO-1 | about 24 to 40 GB | no |

The guide gives one explicit Apple Silicon data point: training ACT at batch size
4 on an M1, M2 or M3 Max takes roughly 6 to 14 hours for five epochs over a
45,000-frame dataset, against roughly 30 to 60 minutes for the same run on an RTX
4090. It also says, of training on a central processing unit alone, simply not to.

Three practical conclusions follow. You can train ACT and diffusion policies on a
Mac if you are patient, which is enough to go round the collect-train-evaluate
loop that the [mechanism
document](../10_one-arm-training/05_what-is-changing.md#8-what-this-means-for-what-you-learn)
says matters more than the architecture. You can run SmolVLA inference on a Mac,
because its authors say so. You cannot train or run any of the large models, and
openpi and GR00T do not merely run badly on a Mac — openpi states it requires an
NVIDIA card and has only been tested on Ubuntu 22.04, and GR00T targets CUDA and
Jetson. For those, rent a cloud graphics card.

## 13. The whole field on one page

The table collects every item in this document with its date and its maturity
label. Read the maturity column first and the claim second: a Demonstrated row
means nobody outside the organisation has verified anything in it.

| Development | Date | Organisation | Maturity | Licence |
| --- | --- | --- | --- | --- |
| RT-2 | 2023 | Google DeepMind | Paper only | none |
| OpenVLA | Jun 2024 | Stanford and others | Downloadable | MIT, code and weights |
| π0 | Oct 2024, open Feb 2025 | Physical Intelligence | Downloadable | Apache-2.0 code |
| OpenVLA-OFT | 2025 | Stanford | Downloadable | MIT |
| π0.5 | Apr 2025 | Physical Intelligence | Downloadable | Apache-2.0 code |
| SmolVLA | Jun 2025 | Hugging Face | Downloadable | Apache-2.0 |
| GR00T N1 | Jun 2025 | NVIDIA | Downloadable | Apache-2.0 code, NVIDIA weights |
| π*0.6 and Recap | Nov 2025 | Physical Intelligence | Demonstrated | none |
| X-VLA | Nov 2025 | academic | Downloadable | Apache-2.0 weights |
| GR00T N1.5 | Dec 2025 | NVIDIA | Downloadable | Apache-2.0 code, NVIDIA weights |
| Helix 02 | Jan 2026 | Figure | Demonstrated | none |
| Skild learning from human video | Jan 2026 | Skild | Demonstrated | none |
| Gemini Robotics ER 1.6 | Apr 2026 | Google DeepMind | Shipped via API | none |
| GR00T N1.7 | Apr 2026 | NVIDIA | Downloadable | Apache-2.0 code, NVIDIA weights |
| π0.7 | Apr 2026 | Physical Intelligence | Demonstrated | none |
| MolmoAct2 | May 2026 | Allen Institute for AI | Downloadable | Apache-2.0 code, none declared on weights |
| Gemini Robotics 2 | Jul 2026 | Google DeepMind | Demonstrated | none |
| Gemini Robotics ER 2 | Jul 2026 | Google DeepMind | Shipped via API | none |
| Dyna-2 | Aug 2026 | Dyna Robotics | Demonstrated | none |
| Skild S1 | Aug 2026 | Skild | Shipped to partners | none |
| Figure Index | Aug 2026 | Figure | Shipped as an app | none |
| GigaBrain-0.7 | Aug 2026 | GigaBrain | Downloadable | Apache-2.0 |
| OpenWAM-α | Sep 2026 | academic consortium | Downloadable | Apache-2.0 |
| Helix 2.5 | Sep 2026 | Figure | Demonstrated | none |
| Skild physical self-play | Sep 2026 | Skild | Demonstrated | none |

Three patterns are visible in that column and none of them is in any press
release.

Everything at the frontier is closed. Every Downloadable row is either academic, a
vendor giving away a model to sell hardware, or Physical Intelligence releasing a
model two generations behind the one it is talking about.

The open shelf lags the frontier by roughly eighteen months, and the gap is
stable. π0.5 is open and π0.7 is not. GR00T N1.7 is open and Gemini Robotics 2 is
not.

The distinguishing work of 2026 is about data, not architecture. Index, EgoScale,
Dyna-2's million hours and Skild's three-tier mixture are all answers to the same
question, and every one of them answers it with human video rather than with robot
demonstrations.

## 14. Which of these claims will age worst

Four predictions, offered as the honest weak points of everything above rather
than as forecasts.

**The scaling laws are the most likely to break.** Figure's 0.54 per cent
forecasting error and Dyna-2's coefficient of determination of 0.919 are both
measured over a single axis, holding model size and compute fixed, over ranges of
eight and one thousand times respectively. Scaling laws in language models held
over many more orders of magnitude before anyone trusted them, and they still bent.
These are early, narrow and self-reported.

**The zero-shot cross-embodiment claims will shrink under scrutiny.** π0.7 folding
laundry on an untrained UR5e, Dyna-2 transferring from human video to robot arms,
Gemini Robotics On-Device 2 adapting in under 200 examples: each is a real result
on the authors' hardware, and the [embodiment gap
survey](https://arxiv.org/abs/2608.18433) exists precisely because success rates
conceal how much adaptation work was involved. Expect the phrase "zero-shot" to
mean less each year.

**The success rates will not reach industrial levels on this trajectory.** A model
at 56 per cent needs roughly a hundredfold reduction in failure rate to be
deployable in a cell that cannot be supervised, and nothing in this document shows
a mechanism that delivers that. The demonstrate-then-polish result in section 4.2
is the most promising candidate, and it works by adding task-specific practice,
which is the opposite of generality.

**The maturity labels will move, and mostly in one direction.** Half this document
is Demonstrated. Historically most Demonstrated robotics results stay Demonstrated:
RT-2 never shipped, and it was the most influential result of its year. Assume
each Demonstrated row stays where it is until a checkpoint appears, and you will be
right more often than not.

One last thing, which is the habit rather than the prediction. The single question
that separates a real development from an announcement is the third of the five
this document asks of each item: *how was it achieved*. A result with a stated
mechanism can be judged, argued with and transferred. A result with a number and a
video cannot. When the next model appears — and one will, before you finish reading
this — look for the mechanism first, and treat everything else as marketing until
you find it.

---

For why the field moves the way it
does rather than what it has produced, read [what is
changing](../10_one-arm-training/05_what-is-changing.md). For the parts of a robot
system that none of these models replaces, read [object
perception](../06_object-perception/01_overview.md),
[gripping](../07_gripping/01_overview.md) and [arm
movement](../08_arm-movement/01_overview.md).
