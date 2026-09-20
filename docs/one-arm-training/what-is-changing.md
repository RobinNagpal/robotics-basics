# What is changing in robot manipulation, and why

Every list of "what is hot in robotics" goes stale in a year. The reasons behind the
list do not, which is why this document spends most of its length on **why** things
move rather than on what moved. If you understand the mechanism, you can read next
year's announcements yourself and tell which ones matter.

This is the long version of
[the overview's status section](overview.md#7-what-is-current-and-what-is-fading).
Read that first if you only want the summary.

**What this document is for.** Two things. First, so that when you meet a tutorial,
a repository or a paper you can place it — current, superseded, or never actually
released. Second, so that when something new appears you can ask the right question
about it, which is almost never "is it better?" and almost always "**what does it
need less of?**"

## Contents

1. [The one mechanism behind every shift](#1-the-one-mechanism-behind-every-shift)
2. [The five forces driving 2026](#2-the-five-forces-driving-2026)
3. [What has clearly been superseded, and why](#3-what-has-clearly-been-superseded-and-why)
4. [What is quietly fading rather than deprecated](#4-what-is-quietly-fading-rather-than-deprecated)
5. [What is not moving at all, and why that matters](#5-what-is-not-moving-at-all-and-why-that-matters)
6. [What is arriving now, and what it can actually do](#6-what-is-arriving-now-and-what-it-can-actually-do)
7. [How to tell a real shift from a fashion](#7-how-to-tell-a-real-shift-from-a-fashion)
8. [What this means for what you learn](#8-what-this-means-for-what-you-learn)

---

## 1. The one mechanism behind every shift

**Methods rarely die of being wrong. They are displaced by something that needs less
of whatever is currently expensive.**

That sentence explains almost every transition in this document, and it has a useful
corollary: because *what is expensive* changes over time, a method can be displaced
without ever becoming worse, and can come back when the economics move again.

![What was scarce in each era, and which method won by needing less of it](../images/one-arm-training/what-is-changing/what-is-expensive.svg)

Three eras make the point.

**When compute was expensive**, the winning methods were the ones that computed
almost nothing. Teach-and-replay stores joint angles and plays them back; it needs no
model, no search and no arithmetic worth the name. That is why it won in the 1970s
and — this is the part people find surprising — why it has never gone away. Its cost
profile is unbeatable and nothing has made it worse.

**When hand-written perception was the bottleneck**, the thing that got expensive was
a specialist's time. Hand-designed visual features needed a computer-vision engineer
to tune them per object, per lighting condition, per factory. Learned perception
needed a great deal of data and no specialist, and by the mid-2010s data had become
the cheaper of the two. That is the entire reason bin picking of mixed items went
from a research problem to a product: not that networks were clever, but that the
per-object engineering cost fell to roughly zero.

**Now the expensive thing is human specification effort** — somebody sitting down and
writing out what the robot should do, in a form precise enough to execute. Every
current shift points the same way: away from methods where a person must describe the
behaviour, towards methods where the behaviour comes from examples. This is why
imitation learning beat reinforcement learning for arms despite being theoretically
weaker. Writing a reward function is specification work. Doing the task fifty times
is not.

**The corollary that keeps you honest.** A method that needs less of what is expensive
can still be worse in every other respect and win anyway. And in the places where
*verification* is the expensive thing — a factory that must certify what a machine
will do — the classical methods are still winning, because an inspectable system costs
less to verify than a learned one. That is not nostalgia. It is the same mechanism
producing the opposite answer under a different cost structure, and it is why
[the deployed systems look nothing like the papers](overview.md#9-what-real-systems-actually-do).

## 2. The five forces driving 2026

Five specific pressures are doing the work right now. Each one predicts several of
the individual changes in the sections below.

**Force one: data is the binding constraint, and everyone knows it.** The single
most sobering result in this whole repository is that ALOHA Unleashed collected
**26,241 demonstrations — about a hundred times the original's fifty per task** —
and did not end up with higher success rates. That is a scaling curve flattening in
public. If more data of the same kind does not help, the field has to find
*different* data, and that pressure explains four separate directions: learning from
human video, data-generation tools that multiply demonstrations, cheap hardware that
lets more people collect, and world models that learn from video without action
labels at all.

**Force two: pretrained perception made generalisation purchasable.** You can now
download a model that segments objects it has never seen and another that estimates
their pose without per-object training. The consequence is structural rather than
incremental: the part of a robot system that used to require bespoke engineering per
customer became a dependency you install. That is what turned modular
learned-perception pipelines into the most deployed use of machine learning on arms,
and it is why that unglamorous family keeps winning against end-to-end approaches.

**Force three: consolidation into one maintained home.** This one is badly
underappreciated and explains more "dead repositories" than any technical argument.
A research repository exists to support a paper; once the paper is published, the
incentive to maintain it disappears. What changed is that
[LeRobot](https://github.com/huggingface/lerobot) became a single maintained library
with a shared dataset format, so the methods moved there and the original repositories
went quiet. **Those methods are not dead — their homes changed.** Reading a dormant
star count as a verdict on a technique is the most common mistake in this area.

**Force four: verification pressure is why adoption is uneven.** A factory must be
able to say why a machine stopped. A method that cannot explain itself carries a
verification cost that is often larger than the engineering it saves. This force runs
*against* the other four, and it is the reason the timeline below shows classical
methods persisting for decades next to learned ones that are years old. Expect this
to be the slowest-moving force of the five, and expect regulation —
[the EU Machinery Regulation from January 2027](overview.md#and-be-honest-about-where-the-paid-work-is)
— to strengthen it rather than weaken it.

**Force five: the shape of available compute changed.** Massively parallel GPUs made
two things possible that were not: simulating thousands of robots at once, which is
what made reinforcement learning in simulation practical, and solving motion plans
fast enough to replan continuously rather than plan once. The second is quieter and
arguably more useful — a planner that replans fifty times a second is not a faster
planner, it is a reactive controller, which is a different capability.

## 3. What has clearly been superseded, and why

Before the individual cases, the shape of the whole field on one axis — roughly when
each method became common, and which are now on the way out. The long blue bars are
the point: several of the oldest methods are still current, which is what
[section 1](#1-the-one-mechanism-behind-every-shift) predicts.

![Roughly when each method became common, and which are fading](../images/one-arm-training/what-is-changing/timeline.svg)

These have explicit deprecation notices or archived repositories. The *reason* is the
part worth remembering.

**Isaac Gym → [Isaac Lab](https://github.com/isaac-sim/IsaacLab).** NVIDIA's own page
says Isaac Gym "is no longer supported" and
[its example repository](https://github.com/NVIDIA-Omniverse/IsaacGymEnvs) is
archived. *Reason:* Isaac Gym was a standalone research prototype; NVIDIA consolidated
simulation onto the Isaac Sim platform so that one physics and rendering stack serves
research and product. A consolidation, not a capability gap. If you meet a tutorial
using Isaac Gym, it is out of date.

**[D4RL](https://github.com/Farama-Foundation/D4RL) → [Minari](https://github.com/Farama-Foundation/Minari).**
The offline reinforcement-learning benchmark suite was formally deprecated.
*Reason:* the same consolidation force — the Farama Foundation took over maintenance
of the scattered reinforcement-learning ecosystem and rebuilt the dataset format
properly. The benchmarks did not become wrong; they became unmaintained, and
somebody responsible adopted them.

**[OpenAI Gym](https://github.com/openai/gym) → [Gymnasium](https://github.com/Farama-Foundation/Gymnasium).**
Same story, same foundation, and the single most common stale import in old
tutorials.

**[SERL](https://github.com/rail-berkeley/serl) → [HIL-SERL](https://github.com/rail-berkeley/hil-serl).**
Deprecated by its own authors. *Reason:* this is the most informative deprecation in
the list, because it is a genuine capability jump rather than a maintenance move.
SERL did reinforcement learning on a real robot; HIL-SERL added **human intervention**
— a person takes over when it is about to fail, and those take-overs become the
learning signal. That one change took the method from "works on some tasks" to
**100% success on every task tried, within one to two and a half hours of real-robot
training**. When authors deprecate their own work, believe them.

**[RT-1](https://github.com/google-research/robotics_transformer) archived, RT-2 never
released.** *Reason:* not technical. Google's robotics work moved into a closed
product line. This is a pattern worth naming rather than a one-off — the frontier of
this field is increasingly announced rather than released, which is why
[separating announced from downloadable](overview.md#11-how-to-read-the-numbers-in-this-field)
is now a core skill.

**ROS 1 → ROS 2.** ROS 1 reached end of life in May 2025. *Reason:* a genuine
architectural rewrite — real-time support, security, and a middleware that works on
multiple machines properly. The cost has been real: several industrial vendor drivers
never made the transition, and there is still **no maintained open-source ROS 2
driver for FANUC or Motoman**, which is a live gap rather than an oversight.

**Hand-designed visual features → learned perception.** *Reason:* force two, a decade
early. The features were the bottleneck and they needed a specialist per deployment.

**[PyBullet](https://github.com/bulletphysics/bullet3) → [MuJoCo](https://github.com/google-deepmind/mujoco).**
PyBullet has an enormous tutorial legacy and roughly one commit a year. *Reason:*
this one is almost pure licensing history. MuJoCo was commercial software with a paid
licence until DeepMind acquired it in 2021 and open-sourced it in 2022. PyBullet's
main advantage had been that it was free; the moment the better simulator was also
free, the reason to choose PyBullet evaporated. Nothing about PyBullet got worse.

### The one everybody gets wrong

**CAD model matching was NOT replaced by learned grasping.** It was replaced *for
mixed and unknown items only*. If you know the part, the industry still matches its
model, and the major 3D-vision vendors describe their products in exactly those
terms. *Reason:* a model match returns a full six-degree-of-freedom pose **plus a
geometric residual you can threshold** — a number that says "this fit badly, stop".
A learned grasp proposer returns a ranked list with a confidence, which is a much
weaker guarantee. Under verification pressure, the checkable answer wins. Both
methods are current in 2026, and which you use is decided by whether the object is in
your catalogue, not by which is more modern.

## 4. What is quietly fading rather than deprecated

Nothing here carries a deprecation notice. Each is simply not being developed, and
the reason differs in ways that matter for whether you should use it.

![Where the research repositories went](../images/one-arm-training/what-is-changing/consolidation.svg)

**The imitation-learning originals.** [ACT](https://github.com/tonyzhaozh/act) has had
no commits since 2024, [diffusion_policy](https://github.com/real-stanford/diffusion_policy)
since late 2024, [Octo](https://github.com/octo-models/octo) since mid-2024, and
[OpenVLA](https://github.com/openvla/openvla) since March 2025. *Reason: force three,
consolidation.* The methods are alive and maintained inside
[LeRobot](https://github.com/huggingface/lerobot). **Use LeRobot's versions and treat
the originals as historical references.** OpenVLA is the interesting case — still the
most-downloaded robotics model and the baseline in most papers, yet absent from
LeRobot's policy list. It is a reference point, not a foundation.

**The classical grasping repositories.**
[Contact-GraspNet](https://github.com/NVlabs/contact_graspnet) has not been touched
since 2024 and depends on a long-dead TensorFlow generation;
[GraspNet-1Billion](https://graspnet.net/) is most valuable now as a dataset rather
than code; Dex-Net and `gqcnn` have been dead since 2022. *Reason:* different from
above and worth distinguishing — the **research line moved** to diffusion models that
generate grasps, of which NVIDIA's [GraspGen](https://github.com/NVlabs/GraspGen) is
the current example, while the **commercial line moved closed**. AnyGrasp has real
traction and ships as a licence-gated binary; it is **not open source** despite
appearing so. Treat this whole corner as concepts and datasets rather than as code to
build on.

**Inverse reinforcement learning and adversarial imitation.** The flagship library
[imitation](https://github.com/HumanCompatibleAI/imitation) has had no commits since
January 2025. *Reason:* the generality is real and so is the fragility, and the
preference-learning branch found a better home tuning language models. Surveys still
treat the family as live, so "declining" is fairer than "dead" — but do not expect to
meet it in a working arm system.

**Task and motion planning.** [PDDLStream](https://github.com/caelan/pddlstream) last
committed in 2023. *Reason:* it is the most capable purely-programmed approach for
long tasks and demands the most before it does anything — somebody must write a
symbolic domain model. Industry uses behaviour trees instead because a tree is free
to write, and the research energy moved to language models doing the same sequencing
job with far less modelling effort.

**Industrial ROS glue.** The ROS-Industrial vendor drivers for FANUC, Motoman, ABB and
KUKA are dormant ROS 1 code. `moveit_calibration`, which most tutorials still
recommend, has had no commits in a year — use
[industrial_calibration](https://github.com/ros-industrial/industrial_calibration) or
OpenCV's hand-eye function directly. *Reason:* unglamorous maintenance work with no
paper attached and no vendor obliged to do it. This is the least satisfying reason in
this document and the most commonly encountered.

## 5. What is not moving at all, and why that matters

A document about change should say what has not changed, because that list is where
the durable skills are.

**Force control.** The mathematics of impedance and admittance control has been
settled for decades and is still the answer to contact-rich assembly. *Reason:*
physics did not change, and the theory was already correct. Every major vendor sells
this as a product. A learned policy that outputs positions still needs this
underneath it, which means learning to do this well has a longer shelf life than
anything in section 6.

**Behaviour trees.** Standard for sequencing, and the only competitor is a language
model choosing which subtree to invoke — with the tree still underneath, doing the
running. *Reason:* nothing has beaten them at being inspectable while staying
readable at fifty branches.

**Teach and replay is growing, not shrinking.** *Reason:* collaborative-robot
hand-guiding made it easier rather than obsolete. You guide the torch along the seam
and press start. That is *more* teaching done by *less* specialised people, which is
a cost structure moving in the right direction, not the wrong one.

**Motion planning.** Healthy and standard; the only axis moving is speed.

**Calibration.** Still the unglamorous thing that decides whether a cell works, still
mostly hand-rolled, still what separates a demo from a deployment.

**The lesson.** Four of those five are in the programmed family, and all five are
things you can learn once and use for a decade. Section 6 is where the excitement is;
this section is where the compound interest is.

## 6. What is arriving now, and what it can actually do

For each of these: the **capability** — what it lets you do that the previous
generation did not — and the **reason** it emerged, which is always one of the five
forces. Treat this section as a weather report rather than a forecast. Several of
these will not survive contact with real deployments.

### Reinforcement learning as polish, not as training

**Capability:** take a policy that works maybe half the time after demonstrations, and
make it reliable in **hours on the real robot** rather than weeks in simulation.
Physical Intelligence reported this on driving screws, fitting zip ties and inserting
connectors with about **fifteen minutes of real-world data and roughly two hours
including resets**, reaching up to three times faster execution and beating human
teleoperation on one task.

**Reason:** the two methods fail in exactly complementary ways. Demonstrations give
you the *shape* of a task cheaply but not the last few percent; exploration cannot
find the shape — a coordinated behaviour is almost never stumbled upon — but polishes
beautifully once the shape is there. Nobody designed this pairing; it was discovered
by four separate groups in one year, on laundry and box assembly, on shoe-lacing
(46% → 83% after about 150 practice episodes), on precision insertion, and in the
winning entry of a garment-folding competition.

**Status:** this is the current state of the art for a hard task, and the convergence
of four independent groups is the strongest signal in this document.
**Open tools:** [HIL-SERL](https://github.com/rail-berkeley/hil-serl) inside
[LeRobot](https://github.com/huggingface/lerobot) for the real-robot stage;
[SimpleVLA-RL](https://github.com/PRIME-RL/SimpleVLA-RL) in simulation.

### Flow matching, and an honest doubt about it

**Capability:** generate a whole action sequence that can represent "either this
motion or that one" rather than averaging them — fast enough to run at control rates.
The averaging problem is real and concrete: if some demonstrators go left around an
obstacle and some go right, a network trained to output one number per command will
learn to go straight through it.

**Reason:** diffusion solved the averaging problem but was too slow to run on a robot
at fifty hertz. Flow matching is a faster relative, and it is now the action head
inside essentially every current large policy.

**The doubt, which belongs here:** a 2026 study ([MINERVA](https://arxiv.org/abs/2609.03715))
found flow matching gave **no detectable advantage over plain regression** on its
benchmarks while being several times slower. The field is optimising a design choice
it has not fully justified. This is a good example of something everyone has adopted
that may not survive.

### Real-time action chunking

**Capability:** a large slow model producing smooth continuous motion. A
vision-language-action model might run at five to ten hertz; an arm wants commands at
fifty to two hundred. Chunking lets the model emit a block of future actions that
play out while the next block is being computed.

**Reason:** a purely practical mismatch between model size and control rate — and it
is the piece that makes the whole 2026 recipe above executable on real hardware
rather than in a video.

### World models

**Capability:** learn to predict what will happen and act through that prediction —
which, crucially, means learning from data that has **no action labels at all**, such
as ordinary video.

**Reason:** force one. If robot demonstrations are the constraint and more of them
stop helping, the way out is to learn from data that is not robot demonstrations.
Video is abundant; action-labelled robot episodes are not.

**Status:** now a first-class category in LeRobot and **not yet proven on production
arms.** Worth watching, not worth betting on.

### Learning from human video, and recording without a robot

**Capability:** use people doing tasks as training data. The scaling behaviour looks
promising and almost nothing has been released, so the honest status is "interesting".

**Reason:** the same data constraint, taken to its logical end. The numbers make the
motivation obvious — Open X-Embodiment, the famous pooled corpus, contains about 2.4
million robot episodes, against effectively unlimited video of humans manipulating
things.

**The practical spin-off you can use today** is more interesting than the research.
[Grabette](https://huggingface.co/blog/grabette) (Apache-2.0, €490) is a handheld
recorder — cameras, an inertial sensor, a gripper encoder — that you hold in your own
hand to do the task, with browser-based reconstruction producing
six-degree-of-freedom trajectories in LeRobot format. Its ancestor is
[UMI](https://github.com/real-stanford/universal_manipulation_interface). **You can
collect training data before owning a robot at all**, which removes the most common
blocker for a learner.

### Verification at run time

**Capability:** instead of trusting the policy's first answer, generate several
candidate actions and check them before acting. At least one 2026 result claims that
**scaling the checking beats scaling the policy**.

**Reason:** force one again, from a different angle. If a hundred times the data buys
no improvement, spending compute at run time rather than at training time is the
obvious other lever — and there is a suggestive precedent in how language models
gained from test-time reasoning. It also sits well with force four, because a system
that checks its candidates is a system that can explain a rejection.

### Data generation as a first-class tool

**Capability:** turn a handful of demonstrations into thousands by re-composing them
around the objects' positions, then train on the result.

**Reason:** the purest expression of force one, and a nice inversion — **programming
is used to manufacture the data that training needs.** The classical stack earns its
keep by generating what the learned stack is short of.

**Open tools:** [MimicGen](https://github.com/NVlabs/mimicgen) and its two-arm
successor [DexMimicGen](https://github.com/NVlabs/dexmimicgen) — both **research-only
under NVIDIA's licence**, so check before building anything commercial.

### Small models for cheap hardware

**Capability:** a pretrained vision-language-action policy you can actually fine-tune
and run on consumer hardware, rather than one that needs more memory than a consumer
card has.

**Reason:** a community with tens of thousands of shared datasets and hundred-dollar
arms needed a model sized for it, and the large policies are not. This is
democratisation as a technical requirement rather than a slogan.

**Open tools:** [SmolVLA](https://huggingface.co/blog/smolvla), inside LeRobot,
trained on community data. For anyone learning on a cheap arm, this is the realistic
entry point to the whole VLA family.

### Tactile foundation models

**Capability:** one model that works across many different touch sensors, rather than
one model per sensor type.

**Reason:** touch data has always been locked to a specific sensor's geometry and
physics, so nobody could pool it — exactly the fragmentation that pretrained vision
models escaped a decade ago. Whether touch has enough shared structure to make the
same trick work is genuinely unknown.

## 7. How to tell a real shift from a fashion

Five questions, roughly in order of how much signal they carry.

**Did the authors deprecate their own previous work?** The strongest signal there is.
Researchers do not willingly retire their own contribution. SERL → HIL-SERL is the
model case.

**Did independent groups converge on the same shape of solution?** Four different
groups arriving at demonstrate-then-polish, on four different tasks, in one year, is
worth more than any single impressive result.

**Is there a checkpoint you can download, or only a paper?** Several of 2026's most
impressive models have no released code or weights. Read about them; do not plan on
using them. Checking this first will save you more time than any other habit here.

**Did the benchmark move, or just the leaderboard?** A new number on an old benchmark
is incremental. A new benchmark, or a paper that reports *per-stage* success rates
instead of totals, usually signals that the field noticed it was measuring the wrong
thing.

**Does the new thing need less of what is currently expensive?** The mechanism from
[section 1](#1-the-one-mechanism-behind-every-shift). If a method is better but needs
more demonstrations, more specification, or more verification, it will lose to a
worse method that needs less — and you should plan accordingly rather than being
surprised.

**One anti-signal:** a dormant repository proves nothing on its own. Check whether
the method moved into a maintained home before concluding it died.

## 8. What this means for what you learn

**Learn the things in [section 5](#5-what-is-not-moving-at-all-and-why-that-matters)
first.** Force control, behaviour trees, motion planning and calibration have not
changed in a decade and will not change in the next one. They are also what people
are paid for.

**In the learned family, learn the loop rather than the architecture.** Collect,
train, evaluate, find what failed, collect more of that. The architecture will be
different in eighteen months; the loop will not. This is also why the cheap hardware
matters more than it looks — going round that loop once teaches you things no paper
will.

**Assume the specific model names in section 6 will be wrong within a year, and the
reasons will not.** If you remember one thing from this document, make it the
question rather than any of the answers: *what does this need less of?*

---

Back to [the overview](overview.md), or on to
[the programmed methods](programmed-methods.md) and
[the learned methods](learned-methods.md). For what changes when two arms must
cooperate, see [the two-arm folder](../two-arm-training/overview.md).
