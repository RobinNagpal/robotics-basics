# What is coming to robot arms, and what is only being promised

This document is about robot arm manipulation in 2027 and shortly after. It is
written on 23 September 2026, and everything dated in it was checked against a
primary source on that day.

It is the hardest document in this folder to write honestly, and the reason is
worth stating at the start rather than hiding in a caveat. Almost everyone who
publishes about the future of robot manipulation is selling something: a product,
a funding round, a paper, or a job. That does not make them dishonest. It does
mean that the ordinary evidence you would use to judge a claim — a demonstration
video, a success rate, a partnership announcement — has been selected by someone
with a reason to select it. So this document is organised around **how strong the
evidence is**, not around how exciting the claim is.

## Who this is for, and how it is built

This is for someone who has read
[what is changing in robot manipulation](../10_one-arm-training/05_what-is-changing.md)
and now wants to know what happens next. That document explains the *mechanism* —
why methods rise and fall — and its
[section on telling a real shift from a fashion](../10_one-arm-training/05_what-is-changing.md#7-how-to-tell-a-real-shift-from-a-fashion)
gives five questions to ask about any new thing. This document applies those
questions to claims that have not happened yet, which is harder, because there is
no repository to check and no deprecation notice to read.

Three rules govern everything below, and they are the only reason to trust it
over a press summary.

**Every forward-looking claim names who said it, when, and what exactly they
said.** Where I can establish what that organisation's last comparable prediction
turned out like, I say so. Where I cannot, I say that too.

**Every number comes from the organisation's own page, its own filing, or the
paper itself.** Not from reporting about those things. Where the only available
source was a company claim relayed by a partner, I say that it is a claim.

**Where I could not establish something, it is written down as not established.**
[Section 9](#9-what-i-could-not-establish) is a list of those. A forward-looking
document with no such list has either done no checking or is not telling you
about it.

## Contents

1. [Four kinds of claim, and why the difference decides everything](#1-four-kinds-of-claim-and-why-the-difference-decides-everything)
2. [Announced with a date, by people who have shipped before](#2-announced-with-a-date-by-people-who-have-shipped-before)
3. [Announced with a date, by people who have not](#3-announced-with-a-date-by-people-who-have-not)
4. [Demonstrated but not productised](#4-demonstrated-but-not-productised)
5. [Research directions with momentum, measured rather than asserted](#5-research-directions-with-momentum-measured-rather-than-asserted)
6. [Structural forces, which predict better than roadmaps](#6-structural-forces-which-predict-better-than-roadmaps)
7. [What is promised that the evidence does not support](#7-what-is-promised-that-the-evidence-does-not-support)
8. [How to read this document in a year](#8-how-to-read-this-document-in-a-year)
9. [What I could not establish](#9-what-i-could-not-establish)

---

## 1. Four kinds of claim, and why the difference decides everything

People use one word, "announcement", for four things that carry completely
different weight. Sorting them is the single most useful habit in this area, and
it costs nothing.

A **demonstration** is a recording of a system doing something once, or some
number of times that the publisher chose. It proves the thing is possible under
conditions the publisher controlled. It says nothing about how often it works,
how long the hardware lasts, or what it costs. A video is never evidence of a
shipped capability.

A **product announcement** is a statement that something can be bought or
downloaded, usually with a date. It is checkable, which makes it the most
valuable kind of claim in this document. You can go to the page and see whether
the thing is there.

A **research result** is a measured number on a stated task with a stated
protocol. It is the only kind of claim that comes with an error bar, and the
protocol is usually where the interesting detail hides.
[Section 7.3](#73-robots-now-learn-a-new-task-from-a-single-video) contains a
case where reading the protocol changes the meaning of the headline number
completely.

A **projection** is a statement about a date that has not arrived. It is the
weakest kind of claim, and the only way to weigh one is to ask what that
organisation's last projection turned out like.

The table below is how to read the rest of this document. The left column is the
kind of claim, the middle column is what it is fair to conclude from it, and the
right column is the question that separates a strong instance from a weak one.

| Kind of claim | What you may conclude | The question that tests it |
| --- | --- | --- |
| demonstration | the thing is physically possible | how many attempts produced this recording |
| product announcement | the thing exists, if the page says so today | can you download or buy it now, or only apply for access |
| research result | a number, under one protocol | what exactly was counted, and who helped |
| projection | nothing on its own | what happened to the last one from these people |

There is a fifth category that most roadmaps omit, and it is the most predictive
of all. A **structural force** is a change that happens regardless of what any
company intends: a price moving, a support window ending, a regulation applying,
a supply chain being restricted. Nobody announces these as robotics news, and
they decide more than the announcements do.
[Section 6](#6-structural-forces-which-predict-better-than-roadmaps) is about
them.

## 2. Announced with a date, by people who have shipped before

This section holds dated commitments from organisations with a public record of
meeting dated commitments. These are the claims in this document most likely to
come true, and it is not a coincidence that three of the four are unexciting.

### 2.1 ROS 2 support windows, and the migration that 2027 forces

The Robot Operating System version 2, usually written ROS 2, is the middleware
that most research and much industry uses to connect the parts of a robot
together. It releases one distribution each May and supports each one for a
published number of years. The dates below come from the ROS 2 documentation's own
[releases table](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases.rst),
and the column to read is the third one rather than the second.

| Distribution | Released | End of life |
| --- | --- | --- |
| Humble Hawksbill | 23 May 2022 | May 2027 |
| Jazzy Jalisco | 23 May 2024 | May 2029 |
| Kilted Kaiju | 23 May 2025 | December 2026 |
| Lyrical Luth | 22 May 2026 | May 2031 |

The two end-of-life dates are what matter here. Kilted Kaiju stops being
supported in December 2026, three months from now. Humble Hawksbill stops in May
2027, and Humble is the distribution that a very large number of existing robots,
tutorials and vendor drivers still target. A support
window ending is not a capability change, and it will move more engineering
effort in 2027 than any model release in this document.

The track record here is good and easy to check in the same table. Every ROS 2
distribution since Galactic Geochelone in 2021 has appeared on or within one day
of 23 May. The project has hit its announced month six years running.

### 2.2 NVIDIA's edge computers, with hardware stated for the first quarter of 2027

On 15 July 2026 NVIDIA
[announced three new Jetson Thor computers](https://blogs.nvidia.com/blog/jetson-thor-robotics-edge-ai-agent/):
the Jetson T3000, the IGX T3000 with integrated functional safety for machines
that work near people, and the smaller Jetson T2000. Jetson is NVIDIA's family of
small computers for running models on the robot itself rather than in a data
centre. The announcement puts emulation support in JetPack 7.2.1 later in July
2026 and **physical hardware in the first quarter of 2027**.

NVIDIA's recent record of shipping what it announces is good, and it is checkable
without trusting me. Its GR00T N1.7 robot policy has been downloadable on the
Hugging Face Hub [since 25 February 2026](https://huggingface.co/nvidia/GR00T-N1.7-3B).
It [put GR00T N1.7 and a teleoperation framework into LeRobot on 6 July 2026](https://blogs.nvidia.com/blog/hugging-face-lerobot-models-frameworks-open-robotics/),
and LeRobot's own release notes confirm that N1.7 replaced N1.5 in version 0.6.0.
It [released Isaac ROS 5.0 on 22 September 2026](https://blogs.nvidia.com/blog/isaac-ros-5-0-agentic-open-source-robotics/)
with support for Lyrical Luth and Ubuntu 24.04. Three announcements, three things
you can go and fetch.

I could not establish whether the original Jetson Thor slipped against its first
announced date, so I make no claim about that. See
[section 9](#9-what-i-could-not-establish).

### 2.3 LeRobot, which now releases on a predictable rhythm

[LeRobot](https://github.com/huggingface/lerobot) is Hugging Face's robot learning
library, and the
[published release history](https://github.com/huggingface/lerobot/releases)
shows versions 0.4.1 through 0.6.1 arriving between 10 November 2025 and 3 August
2026, roughly every six to eight weeks. Version 0.6.0, on 6 July 2026, is the
substantive one for this document. Its
[release notes](https://huggingface.co/blog/lerobot-release-v060) add three world
models, five vision-language-action models and two reward models as downloadable
policies.

A world model is a model that learns to predict what will happen next and then
chooses actions through that prediction. A vision-language-action model, written
VLA throughout the rest of this document, is a policy that takes camera images
and a sentence and emits robot actions. A reward model is a separate model that
scores whether an attempt is going well.

That release is worth pausing on, because it settles a question that the
[mechanism document left open in 2026](../10_one-arm-training/05_what-is-changing.md#world-models).
That document said world models were "worth watching, but not worth betting on".
Five months later they are a first-class, downloadable category with three
implementations and pretrained checkpoints. The honest reading is that the
prediction was right about the direction and cautious about the pace. Reward
models arriving at the same time is the more interesting half, because a reward
model is what lets a system judge its own attempt, and that is the missing piece
in every practice-based method.

### 2.4 The European Union's machinery rules, which apply on 20 January 2027

The European Commission's own machinery page states that
[Regulation (EU) 2023/1230](https://single-market-economy.ec.europa.eu/sectors/mechanical-engineering/machinery_en)
was adopted on 14 June 2023 and "applies on a mandatory basis as of 20 January
2027". The same page says the Regulation "integrates provisions for machinery
with safety functions that are AI-powered", and that machinery placed on the
European Union market before that date must comply with the older Machinery
Directive 2006/42/EC.

This is the most reliable date in this document, because a regulation's
application date is fixed by a published legal text rather than by an engineering
estimate. It is also the date that most directly touches anyone selling a robot
arm into Europe, and
[the mechanism document already flagged it as a force](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026).
What is new since then is covered in
[section 6.3](#63-two-regulatory-dates-that-have-already-moved-once).

## 3. Announced with a date, by people who have not

The organisations in this section have made dated commitments and have no public
record of delivering a comparable one. That is not an accusation. It is a
statement about how much weight the date can bear, and the right amount is less.

### 3.1 The 1X NEO home robot, promised for 2026

On its own product page, 1X states that
[NEO is available for pre-order](https://www.1x.tech/discover/neo-home-robot),
"with first orders shipping to consumer homes in 2026". The page sets Early
Access at 20,000 US dollars including "priority delivery in 2026", offers a
subscription at 499 US dollars a month "which will be shipped at a later date",
and says the company will "start delivering NEOs primarily in the U.S in 2026 and
expand to other markets starting in 2027". The 1X homepage today takes a 200 US
dollar deposit.

Here is what I can establish about the progress of that commitment, entirely from
1X's own [updates page](https://www.1x.tech/discover). Its posts in 2026 are: a
new head of people on 23 April, a NEO factory in Hayward, California on 30 April,
a World Model Lab on 4 June, a vice president of engineering on 25 June, a chief
financial officer on 2 July, and a 25-degree-of-freedom tendon-driven hand on 9
July. **There is no post announcing that a NEO has been delivered to a customer's
home.** Three months of 2026 remain, so the commitment is not yet broken. It is
also not yet evidenced, and 1X has never shipped a consumer product before.

What would change my reading: a post on that page describing a delivery, with a
plain statement of how much of the robot's behaviour is autonomous.

### 3.2 Skild AI, which has partners rather than dates

Skild AI announced its S1 model on 18 August 2026 and, before that, a
[partnership with ABB Robotics, Universal Robots, Mobile Industrial Robots and NVIDIA on 19 March 2026](https://www.skild.ai/blogs/reindustrial-revolution).
The partnership post says ABB Robotics and Universal Robots plan to integrate
Skild's model into their robot ranges, and that Skild will ship its model "to
control dual robotic arms on NVIDIA's Blackwell GPU production lines" with
Foxconn. It gives no date for either.

That is worth noticing in both directions. A partnership with two established
industrial arm vendors is a stronger signal than a demonstration video, because
those vendors have integrators, service contracts and customers who will complain.
A commitment with no date, however, cannot be checked, and an uncheckable
commitment is a projection.

NVIDIA's
[10 September 2026 post about Skild](https://blogs.nvidia.com/blog/skild-ai-s1-physical-ai/)
relays two further figures: more than 60 commercial deployment partnerships and a
100 million US dollar annual revenue run rate. Those are Skild's claims, repeated
by a partner. They are not audited figures and I have not treated them as
established.

### 3.3 Figure, which has one robot at one customer

Figure's own post of
[30 June 2026](https://figure.ai/news/f-03-at-bmw) describes a Figure 03 robot at
BMW performing a sequencing task, which means selecting and sorting parts for an
assembly line. The post describes **one robot**. It states that the earlier Figure
02 "contributed to the assembly of 30,000 cars at BMW last year", which is a claim
about a number of cars rather than a number of robots, hours, or tasks completed
without help.

Figure has therefore done something real that most of its competitors have not:
put hardware into a paying customer's building and left it there. It has not
published anything that would let you estimate a fleet size or an uptime. Both
halves of that sentence matter.

## 4. Demonstrated but not productised

Everything in this section works. The open question is manufacturing, cost and
release, not feasibility. This is the most interesting section to watch, because
things move out of it in both directions: some become products, and some quietly
stop being mentioned.

### 4.1 Physical Intelligence's π0.7, and a release pattern that has stopped

Physical Intelligence published
[π0.7 on 16 April 2026](https://www.pi.website/blog/pi07). The post claims
compositional generalisation, meaning the model combines skills it learned
separately to do a task it never saw, and reports that it folds laundry on a
bimanual UR5e system for which it has no training data, matching expert human
teleoperators' zero-shot success rate. Those are strong claims and I have no way
to check them, because **the weights are not released**.

The useful thing here is not the claim. It is the company's own release record,
which is checkable and which has changed. The table below lists each model, the
date of its announcement post and the date its weights became downloadable. The
last column is the one to read, because the first two rows set an expectation that
the last two have not met.

| Model | Blog post | Open release | Gap |
| --- | --- | --- | --- |
| π0 | 31 October 2024 | 4 February 2025 | about 3 months |
| π0.5 | 22 April 2025 | [9 September 2025](https://huggingface.co/lerobot/pi05_base) | about 4.5 months |
| π*0.6 | 17 November 2025 | not released | 10 months and counting |
| π0.7 | 16 April 2026 | not released | 5 months and counting |

The first two gaps are three to five months. Two models have now passed that
window with nothing published. I checked this by reading
[openpi](https://github.com/Physical-Intelligence/openpi), the company's own
Apache-2.0 repository, which as of today lists checkpoints for π0 and π0.5 and
none for π*0.6 or π0.7.

The honest conclusion is narrow and I want to keep it narrow. I am not predicting
that π0.7 will never be released. I am saying that the company's open-release
behaviour has changed, that two models in a row are now past the historical gap,
and that anyone planning to build on π0.7 should plan for it not arriving. That is
the same pattern the mechanism document named when it observed that
[the frontier of this field is increasingly announced rather than released](../10_one-arm-training/05_what-is-changing.md#3-what-has-clearly-been-superseded-and-why).

### 4.2 Gemini Robotics 2, where one model of three is actually available

Google DeepMind published
[Gemini Robotics 2 on 30 July 2026](https://deepmind.google/blog/gemini-robotics-2-brings-whole-body-intelligence-to-robots/),
describing three models: a VLA for whole-body control, an embodied reasoning model
called [Gemini Robotics ER 2](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-robotics-er-2/),
and an on-device VLA. The access position is stated plainly in the post and is
the part that matters: "Gemini Robotics ER 2, our reasoning model, is now
available on Google AI Studio and in private preview on Gemini Enterprise Agent
Platform", while "Our VLA and On-Device models are available to early-access
partners."

So one of the three is a product announcement you can act on today, and two are
demonstrations with an application form. The post names the hardware the models
were shown on, which includes the Apptronik Apollo 2, a Franka Duo with a Robotiq
gripper, and the SO-101 — the same low-cost arm covered elsewhere in this
repository.

The most useful sentence in the whole post is the one admitting a limit: "While
Gemini Robotics 2 achieves a medium to high success rate for whole-body and
gripper-based dexterous tasks, the multi-finger dexterous manipulation remains
challenging." An organisation naming what its system cannot do is worth more than
any success rate it reports, because nobody is required to publish it.

### 4.3 Figure's Helix 2.5, and the most useful scaling number published this year

Figure published
[Helix 2.5 on 17 September 2026](https://figure.ai/news/helix-2-5-zero-shot-30-home-generalization),
six days before this document was written. It is a research result, not a
product: nothing is downloadable. The numbers are specific enough to argue with,
which is why it is the best evidence in this section.

The headline is **56 per cent zero-shot success across 30 unseen Bay Area homes**,
against 9 per cent for the same architecture trained from scratch, on three tasks:
tidying a living room of 13 to 15 toys, folding towels, and making beds. "Zero
shot" means no data was collected in the evaluation homes. Figure also reports
that its pretraining scaling relationship predicted results across an eightfold
data range with a forecasting error of 0.54 per cent of the variation.

Two readings of that result are both correct, and most coverage picks one.

The optimistic reading is that pretraining on a large, varied corpus accounts for
most of the capability, that the scaling relationship is precise enough to
forecast, and that a six-fold improvement over training from scratch is a large
effect. All of that is supported by Figure's own numbers.

The sober reading is that 56 per cent means the robot fails about four times in
nine, on three chosen household tasks, in homes in one region, with no statement
of what a failure costs. Figure's forecast covers an eightfold data range, not the
hundredfold range that would be needed to reach a rate anyone would tolerate in
their own home.

### 4.4 Dexterous hands, which now exist and are not sold

Two independent data points from this year say that the hand is no longer the
blocker it was. 1X published a
[25-degree-of-freedom tendon-driven hand on 9 July 2026](https://www.1x.tech/discover),
and Google DeepMind ran Gemini Robotics 2 on an Apptronik Apollo 2 fitted with
third-party multi-finger hands. Meanwhile Google's own post says multi-finger
manipulation remains the hard part.

The fair summary is that building a hand with enough degrees of freedom has been
demonstrated by more than one group, and that controlling one well enough to be
useful has not. A software problem now stands behind a hardware problem
that has been solved. Problems in that position sometimes move very quickly and
sometimes stay three years away for six years. I do not know which this one is.

## 5. Research directions with momentum, measured rather than asserted

Everybody says a research area is "growing". Almost nobody counts. The counts
below come from the arXiv application programming interface, restricted to the
cs.RO robotics category, searching abstracts, and they are reproducible: anyone
can issue the same query and get the same answer.

The method matters for reading the table, so here it is. I counted all cs.RO
submissions in each period, then counted submissions whose abstract contains each
phrase, then divided. The 2026 column runs from 1 January to 23 September, so its
raw counts are for a partial year and are not comparable to the full years. The
**shares** are comparable, which is why the table reports those.

| Phrase in the abstract | 2024 | 2025 | 2026 to 23 September |
| --- | --- | --- | --- |
| all cs.RO submissions | 8,650 | 10,564 | 10,661 |
| "vision-language-action" | 0.52% | 4.25% | 10.78% |
| "world model" | not counted | 2.39% | 5.48% |
| "benchmark" | not counted | 15.27% | 20.04% |
| "humanoid" | not counted | 4.20% | 5.59% |
| "dexterous" | not counted | 3.64% | 4.16% |
| "tactile" | not counted | 2.72% | 3.53% |

Four things follow, and I have tried to separate what the numbers show from what
I think they mean.

**VLAs went from a curiosity to a tenth of robotics research in two years.** The
share went from one paper in 200 to more than one in ten. This is not an artefact
of arXiv growing, because the denominator is arXiv's own robotics output. It is
the clearest measured trend in this document.

**World models more than doubled their share in one year.** That matches what
LeRobot shipped in [section 2.3](#23-lerobot-which-now-releases-on-a-predictable-rhythm),
which is the useful kind of agreement: an independent measure of research
attention and an independent measure of released software pointing the same way.

**Evaluation is growing faster than most of the methods.** One in five robotics
abstracts now mentions a benchmark. Reading the titles submitted in the week
before this document makes the reason concrete: on 21 and 22 September alone,
arXiv received
[LIBERO-VPro](https://arxiv.org/abs/2609.24350), on closed-loop visual robustness
of robot foundation models, and
[IndustrialVLA-Bench](https://arxiv.org/abs/2609.25562), which proposes a shared
reporting format for comparing open policies. A field that starts building
measuring instruments is a field that has stopped believing its own headline
numbers, and that is a healthy development rather than a discouraging one.

**Touch is growing slowly, and dexterity barely at all.** Tactile sensing went
from 2.72 per cent to 3.53 per cent of abstracts, and "dexterous" from 3.64 to
4.16. Both are rising, and both are rising far more slowly than VLAs or world
models. The mechanism document listed
[tactile foundation models as a thing to watch](../10_one-arm-training/05_what-is-changing.md#6-what-is-arriving-now-and-what-it-can-actually-do);
a year on, the research attention has not arrived in the volume that would
suggest a sudden improvement is near.

### 5.1 Three specific directions visible in this month's submissions

Counting phrases shows scale but not content. Reading the titles does. Three
patterns are unmistakable in cs.RO submissions from the week of 19 to 22 September
2026, and each of them is a VLA acquiring something that classical control always
had.

**Force and compliance are being pulled inside the policy.**
[CompVLA](https://arxiv.org/abs/2609.23614) predicts a stiffness matrix alongside
the motion, so that the same model that decides where to go also decides how hard
to push. [ForceRFT](https://arxiv.org/abs/2609.22840) refines a VLA's actions using
force-guided reinforcement learning. This is a direct answer to something
[the mechanism document said was not moving](../10_one-arm-training/05_what-is-changing.md#5-what-is-not-moving-at-all-and-why-that-matters):
impedance control is settled mathematics that learned policies have so far run
above rather than used. These papers are attempts to merge the two layers.

**Models are being shrunk to fit the robot.**
[FoldQuantVLA](https://arxiv.org/abs/2609.24433) reports four-bit weights and
four-bit activations with speedups of 1.20 to 1.33 times. Quantisation means
storing numbers with fewer bits so the model fits in less memory and runs faster.
This direction has an obvious external cause, which is that
[NVIDIA's entry-level 2027 part](#22-nvidias-edge-computers-with-hardware-stated-for-the-first-quarter-of-2027)
has 16 gigabytes of memory and current VLAs do not comfortably fit in it.

**Policies are being given memory.** Several September submissions add persistent
state so that a policy can tell apart two moments that look identical but require
different actions. This is the least glamorous of the three and probably the most
consequential for long tasks, because a policy that cannot remember what it
already did cannot recover from its own mistakes.

## 6. Structural forces, which predict better than roadmaps

None of the following is robotics news. All of it will affect robot arms in 2027
more reliably than any model release in this document, because none of it depends
on anyone's intentions.

### 6.1 The magnets in every joint, and a suspension that expires

Every servo motor in a robot arm contains a permanent magnet, and the strongest
practical magnets are made from neodymium, iron and boron. The United States
Geological Survey publishes an annual summary of the rare-earth market, and the
[February 2026 edition](https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-rare-earths.pdf)
gives the following, all of which are that agency's own estimates.

World mine production in 2025 was 390,000 tonnes of rare-earth oxide equivalent,
of which China produced 270,000 tonnes, or 69 per cent. Neodymium oxide averaged
56 US dollars per kilogram in 2024 and 73 in 2025, a rise of 30 per cent in one
year, after three years of falling. United States net import reliance rose from 53
per cent in 2024 to 67 per cent in 2025. The survey states that the leading global
use of rare earths is magnets.

The dated part is the part to watch. The survey records that China tightened
export controls on rare earths in April 2025, adding samarium, gadolinium,
terbium, dysprosium, lutetium, scandium and yttrium; expanded them in October 2025
to include europium, holmium, erbium, thulium and ytterbium; and then **suspended
the October controls for one year in November 2025**, while the April controls
stayed in force.

A one-year suspension announced in November 2025 expires around November 2026.
Whatever happens then will move the cost of every actuator on Earth, and it will
do so without reference to anything happening in robot learning. If you want one
prediction from this document that has nothing to do with models, it is that the
price of a robot arm in 2027 is a materials story before it is an algorithms
story.

### 6.2 A data format quietly becoming the standard

The mechanism document identified
[consolidation into one maintained home](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
as a force, with LeRobot as the example. That force has continued, and it is now
possible to put a number on it.

On 23 September 2026 I counted the datasets on the Hugging Face Hub carrying the
LeRobot tag, by paging through the public dataset application programming
interface until it returned no further pages. The count was **77,598**. For
comparison, Open X-Embodiment, the pooled corpus that the field treated as large,
gathered about 2.4 million episodes from roughly 60 contributing datasets.

You can reproduce that count from the
[dataset listing](https://huggingface.co/datasets?other=LeRobot), and the number
will be larger by the time you do. What it means is that a single dataset layout
has become the default way people publish robot demonstrations. That has a
consequence worth spelling out: a method that cannot read that format now has an
adoption problem that has nothing to do with whether it works. NVIDIA's release of
an open teleoperation framework "for standardized human demonstrations" alongside
GR00T N1.7 in July 2026 is the same force acting on data collection rather than
data storage.

### 6.3 Two regulatory dates that have already moved once

[Section 2.4](#24-the-european-unions-machinery-rules-which-apply-on-20-january-2027)
established that the European Union Machinery Regulation applies on 20 January
2027. A second regulation interacts with it, and the interaction changed after
May 2026, which is why it is worth setting out carefully.

The European Union Artificial Intelligence Act, Regulation (EU) 2024/1689,
entered into force on 1 August 2024 and became generally applicable on 2 August
2026. Its rules for high-risk artificial intelligence systems were originally due
on two dates. According to the European Commission's
[own page on the Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai),
a simplification proposal known as the AI Omnibus was adopted on 19 November 2025,
reached political agreement on 7 May 2026, and entered into force on 27 July 2026.
As a result, the rules for high-risk systems in sensitive areas now apply from 2
December 2027, and **the rules for artificial intelligence embedded in regulated
products, which is the category machinery falls into, now have an extended
transition until 2 August 2028**. The same page says the Omnibus clarified the
interplay between the AI Act and the Machinery Regulation to avoid duplication.

Two conclusions follow, and the second is the one usually missed.

In 2027 the machinery rules apply and the artificial intelligence product rules do
not. Anyone planning compliance work should be doing it against Regulation (EU)
2023/1230 next year, not against the AI Act.

And a legislature moved its own date by a year. That is the clearest available
evidence for the general claim this document is built on: dated commitments slip,
including commitments made by bodies with published procedures, legal drafting and
no commercial incentive to be optimistic. When a startup's date slips, that is not
a scandal. It is the base rate.

### 6.4 The cost floor of an arm you can learn on

The parts for a leader-follower pair of SO-101 arms cost 229.88 US dollars,
according to the
[bill of materials](https://github.com/TheRobotStudio/SO-ARM100) in the project's
own repository, which is published under the Apache-2.0 licence. A single follower
arm is 121.94 US dollars. The leader is the arm you move by hand; the follower
copies it, which is how demonstrations get recorded.

That number is a structural force rather than a product fact, and the reason is in
[section 4.2](#42-gemini-robotics-2-where-one-model-of-three-is-actually-available):
Google DeepMind demonstrated its 2026 flagship model on this arm alongside
industrial hardware. When the cheapest arm in the field is also one of the
platforms the largest models are shown on, the barrier to entering this subject
has effectively gone. That is what produced the 77,598 datasets in
[section 6.2](#62-a-data-format-quietly-becoming-the-standard), and it will keep
producing them.

### 6.5 Third-party inspection capacity being built

Verification cost is the force that runs against all the others, and it is the
reason deployment lags demonstration. NVIDIA's
[21 September 2026 post on physical AI safety](https://blogs.nvidia.com/blog/physical-ai-halos-safety/)
is a useful indicator of that force, not because of what NVIDIA claims but because
of the institutions it names: TÜV SÜD certifying software processes against ISO
26262, TÜV Rheinland inspecting hardware for functional-safety certification
readiness, and the ANSI National Accreditation Board accrediting an inspection
laboratory to ISO/IEC 17020. The post also names ISO/IEC TS 22440 as an emerging
standard for risks specific to artificial intelligence.

The detail to take from that is not any individual certificate. It is that
certification bodies are building capacity to assess learned systems, which is a
slow, expensive, unglamorous process, and which has to happen before a learned
policy runs next to a person in a factory. Watch whether that capacity exists,
because it gates everything in [section 4](#4-demonstrated-but-not-productised).

## 7. What is promised that the evidence does not support

This is the most useful section and the one most likely to be unfair, so each item
follows the same three steps. I name the claim. I name the evidence that exists,
usually from the promising organisation itself. Then I say what would have to be
true for the claim to hold, so that you can check it yourself later rather than
taking my word.

### 7.1 "Humanoid robots will be working in factories in numbers in 2027"

**The evidence.** The best-documented humanoid deployment at a named customer is
Figure's, and Figure's own post of 30 June 2026 describes **one robot** at BMW
doing part sequencing. The figure it publishes for the previous generation is that
Figure 02 "contributed to the assembly of 30,000 cars at BMW last year", which
counts cars rather than robot hours. No manufacturer of humanoid robots has
published a fleet size, a mean time between interventions, or an uptime
percentage for a customer site.

**What would have to be true.** A number of robots at a named site, a number of
hours they ran, and a count of how often a person had to intervene. Those three
numbers are what any industrial automation vendor publishes as a matter of course.
Until one appears, "working in factories" is doing a great deal of work in that
sentence.

### 7.2 "You will be able to buy a useful home humanoid"

**The evidence.** 1X has taken pre-orders since October 2025 at 20,000 US dollars
with "priority delivery in 2026", takes a 200 dollar deposit today, and has
published nothing on its own updates page indicating that a unit has reached a
customer's home. Separately, Figure's Helix 2.5 result of 17 September 2026 —
which is the strongest published measurement of a general home policy — reports 56
per cent zero-shot success on three household tasks across 30 homes.

**What would have to be true.** For the pre-order claim: a delivery announcement
before 31 December 2026. For usefulness: a success rate on unscripted household
tasks high enough that a person would not simply do the task themselves, together
with a statement of how much of the behaviour is remotely operated by a human. I
could not establish 1X's current position on remote operation from its own
website, which is itself informative, because it is the first question any buyer
would ask.

### 7.3 "Robots now learn a new task from a single video"

This one deserves the most care, because the underlying result is genuinely
interesting and the headline is genuinely misleading.

**The claim.** Skild AI's [S1 model](https://www.skild.ai/blogs/s1), announced
on 18 August 2026, learns a new task from one video demonstration with no
fine-tuning. NVIDIA's post of 10 September
2026 repeats this and quotes a 66 per cent success rate against 9 per cent for
comparable systems.

**The evidence, from Skild's own post.** The post states: "We report the average of
cumulative per-step success rate across all tasks." The 96 per cent figure applies
to tasks that appeared in pretraining. The 66 per cent figure applies to unseen
tasks at 100,000 hours of pretraining data. And the methodology note says: "To
ensure all steps are graded cumulatively, we use human intervention to recover
from failures during policy rollouts."

**What that means.** The number is measured per step, not per task, and a human
puts the robot back on track when a step fails. Those are legitimate research
choices and Skild states both of them plainly, which is more than many groups do.
They are not what "learns a new task from one video" conveys to somebody reading
a headline. A per-step rate cannot be multiplied out into a task rate by a reader,
because the steps are not independent and because the human intervention has
already removed the compounding that a task rate would capture.

**What would have to be true.** A whole-task success rate on unseen tasks, without
human recovery, on named hardware, with the number of trials stated. Skild has not
published one. Until it does, S1 is a strong research result about in-context
learning and not a statement about what a robot will do unattended.

### 7.4 "Foundation models remove the need for robot engineering"

**The evidence.** The three organisations furthest along all say otherwise in
their own words. Google DeepMind says multi-finger dexterity remains challenging.
Skild's route to industrial deployment runs through ABB Robotics and Universal
Robots, meaning conventional industrial arms, their controllers, their safety
systems and their integrators. Figure's result depends on a proprietary data
pipeline and a stated one billion US dollar commitment to data and compute over
twelve months, which is an engineering programme rather than the absence of one.

**What would have to be true.** Someone deploying a general policy onto an
unmodified customer cell, with no task-specific data collection, and publishing
the result. Nobody has.

### 7.5 "The open-weight releases will keep coming at this rate"

**The evidence.** It is genuinely split, which is why this belongs here rather than
in a confident prediction either way. Against: Physical Intelligence has not
released π*0.6 or π0.7; Figure has released neither Helix nor Index; Skild has
released no weights for S1; two of Google DeepMind's three robotics models are
limited to early-access partners. In favour: LeRobot 0.6.0 shipped roughly ten
downloadable policies in July 2026, and NVIDIA's GR00T N1.7 is open and has been
downloaded about 110,000 times in the last month.

**What that suggests.** The frontier is closing and the second tier is opening,
which is the same pattern the mechanism document described when it noted that
RT-2 was never released while the open ecosystem consolidated. If you are learning
this subject, that is a better situation than it sounds, because the open second
tier is what runs on hardware you can afford.

## 8. How to read this document in a year

A forward-looking document that does not date itself is dishonest, so here is
which parts of this one I expect to look worst, in order.

**The 1X reading will settle first, and could settle either way.** Three months
remain in 2026. If 1X publishes a delivery post in November, section 3.1 will read
as unnecessarily sceptical. I have tried to write it so that it says only what I
checked, which is that no such post existed on 23 September 2026.

**The π0.7 paragraph is the claim most likely to be overtaken.** If Physical
Intelligence releases those weights next month, the table in section 4.1 becomes a
historical curiosity. The claim as written is about what has happened rather than
what will, which is deliberate, but the framing will still look dated.

**The arXiv shares for 2026 are a partial year.** Submissions are not spread evenly
through a year, and if the last quarter is unusually heavy in one area the shares
will move. I would not be surprised by two or three percentage points in either
direction. I would be surprised if the direction of any of the six trends
reversed.

**The rare-earth prediction may simply not fire.** A suspension expiring is not the
same as controls returning. If nothing happens in November 2026, section 6.1 will
look like alarm about a non-event. I have stated it as a thing to watch rather
than a thing that will happen, and that is the most I can support.

**The regulatory dates could move again.** The European Union has already moved
one of them by a year. Anyone reading this in 2027 should check both dates rather
than trusting this document, and the Commission pages linked in section 6.3 are
where to check.

**The safest claims here are the least interesting ones.** The ROS 2 support
windows, the Machinery Regulation date, and the cost of an SO-101 are set by
published processes and bills of materials. If you want to know what this document
got right in a year, look there first, and notice that none of those items would
make a headline.

There is one more thing worth saying about how to read any successor to this
document, including next year's version of it. The five questions in
[the mechanism document's section on telling a real shift from a fashion](../10_one-arm-training/05_what-is-changing.md#7-how-to-tell-a-real-shift-from-a-fashion)
are still the right questions, and this document has really only added one more to
them: **has this organisation met a dated commitment before?** That question costs
five minutes on a company's own updates page, and it separates more claims than
any technical judgement.

## 9. What I could not establish

Listed plainly, because a forward-looking document is judged on its honesty rather
than its coverage.

**A dated production commitment for Tesla's Optimus from a Tesla primary source.**
I read Tesla's annual report for 2025, filed with the United States Securities and
Exchange Commission on 29 January 2026, and its quarterly report filed on 23 July
2026. The annual report calls Optimus "a general purpose, autonomous humanoid
robot in development" and says it belongs to "a nascent industry that has yet to
develop commercially". The quarterly report says Tesla is making "preparations and
investments in large-scale production". Neither contains a date or a volume. Those
filings are public on the Commission's EDGAR system under Tesla's central index
key 0001318605, as accession numbers 0001628280-26-003952 and
0001628280-26-049270. I have not linked them, because the Commission's servers
refuse the request that this repository uses to verify links, and an unverifiable
link does not go in. Tesla's investor relations site also refused my requests, so
I have not used any reported account of what was said on an earnings call.

**Whether NVIDIA's Jetson Thor slipped against its first announced date.** I could
not find NVIDIA's original announcement on its own pages, and I will not infer a
slip from secondary accounts.

**A patent expiry that will matter in 2027.** The claim that key patents on
strain-wave gearing, the compact gearbox in most robot joints, are expiring and
will lower actuator costs is widely repeated. I could not verify it against a
patent office record, so it does not appear in
[section 6](#6-structural-forces-which-predict-better-than-roadmaps). If somebody
tells you 2027 is the year robot gearboxes get cheap for patent reasons, ask them
for the patent number.

**1X's position on remote human operation of NEO.** Nothing on the company's own
website addressed it.

**Skild AI's revenue and deployment counts.** The figures of more than 60
deployment partnerships and a 100 million US dollar run rate come from NVIDIA's
post relaying Skild's claims. They are not audited and I have treated them as
claims throughout.

**The exact size of the Index dataset.** Figure's
[post of 25 August 2026](https://figure.ai/news/introducing-index) gives
density figures — 373 unique tasks, 1,146 unique objects and 116 unique
environments per 1,000 hours collected — and an ingestion rate, but no total. A
rate is not a size.

---

Back to [what is changing and why it changes](../10_one-arm-training/05_what-is-changing.md)
for the mechanism this document applies, or to
[object perception](../06_object-perception/01_overview.md) for the part of the
stack where the claims are easiest to check against a measurement. The other
documents in this folder cover the rest of the frontier.
