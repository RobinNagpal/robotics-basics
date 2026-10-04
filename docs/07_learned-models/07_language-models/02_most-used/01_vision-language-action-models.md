# Vision-language-action models

This page answers one question: how can one model take a camera picture and a
sentence, and move a robot arm to do what the sentence says?

This is a page for a reader who has read the two pages before it, [language models as
planners](../03_also-used/01_language-models-as-planners.md) and [vision-language
models](02_vision-language-models.md). So you should already know what a token is, and
how a picture is cut into patches. It also helps to have read the [movement models
overview](../../06_movement-models/01_overview.md), which explains the words
**policy**, **observation** and **action**, because this page uses those words in the
same way.

This page explains how these models work, but it does not try to list the newest ones.
For that, read [foundation models and generalist
policies](../../../03_frameworks/08_frontier/02_foundation-models.md), which records
what each laboratory has released or shown, as of September 2026.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [The starting point: a vision-language model](#the-starting-point-a-vision-language-model)
   · [Way 1: write the movement as tokens](#way-1-write-the-movement-as-tokens)
   · [Way 2: add a small action expert](#way-2-add-a-small-action-expert)
   · [Why it outputs a chunk of actions](#why-it-outputs-a-chunk-of-actions)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
   · [SmolVLA, the one to start with](#51-smolvla-the-one-to-start-with)
   · [The pi models from Physical Intelligence](#52-the-pi-models-from-physical-intelligence)
   · [GR00T N1.7 from NVIDIA](#53-gr00t-n17-from-nvidia)
   · [MolmoAct2 from the Allen Institute for AI](#54-molmoact2-from-the-allen-institute-for-ai)
   · [X-VLA](#55-x-vla)
   · [OpenVLA](#56-openvla)
   · [The ones you will read about but cannot have](#57-the-ones-you-will-read-about-but-cannot-have)
   · [How to choose](#58-how-to-choose)
6. [A worked example: teaching a small arm to put a mug in a bowl](#6-a-worked-example-teaching-a-small-arm-to-put-a-mug-in-a-bowl)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why use a vision-language-action model, and what it costs](#8-why-use-a-vision-language-action-model-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

Here is the idea in one sentence. A **vision-language-action model**, or **VLA**, is
a vision-language model that has been taught to output arm movements as well as
words.

Think of asking a person to "put the mug in the bowl". They do not write a plan first,
and they do not say where the mug is, because they look, understand and move all at
once. So a VLA tries to do the same in one model.

The two pages before this one split the job into parts. A planner chose the steps, a
vision-language model found the mug and checked the result, and other models and
ordinary code did the moving. A VLA replaces all of those parts with one network. So
it is a policy, in the sense of the [movement models
chapter](../../06_movement-models/01_overview.md), because it turns an observation
into an action, many times a second. What makes it different from the other policies
in that chapter is where it starts, since it starts from a vision-language model that
already knows what mugs and bowls are, and what the words mean.

---

## 2. What goes in and what comes out

Three things go in, each time the model runs:

- one or more camera pictures, often one from above the table and one from a small
  camera on the wrist
- the instruction, in words, such as "put the mug in the bowl"
- the arm's current joint angles, read from the sensors in the joints

One thing comes out, which is the next movements of the arm. Depending on the model, a
movement is given as target joint angles, or as how far to move and turn the gripper,
and it also says whether the gripper should open or close. Most VLAs output a short
sequence of movements each time they run, not just one.

The instruction stays the same for the whole task, while the pictures and the joint
angles change every time the model runs. So the model sees the result of its last
movement before it chooses the next one.

---

## 3. How it works inside

### The starting point: a vision-language model

Every VLA starts from a vision-language model, as described on the [previous
page](02_vision-language-models.md#3-how-it-works-inside). The picture is cut into
patches, the patches and the words become one row of tokens, and a transformer reads
the row. That model already knows a great deal about everyday objects, but what it
cannot do is say "move 3 mm to the left". So there are two main ways to teach it that.

### Way 1: write the movement as tokens

The first way was shown by Google's RT-2 in 2023, and it writes each movement as text.
The model then outputs a movement in exactly the same way that it outputs a word. RT-2
was never released, so it appears here only because it is the clearest example of the
method, and the models you can actually use are in [section
5](#5-well-known-models-of-this-kind).

![A movement cut into eight parts, each written as one of 256 steps, giving the string 1 128 91 241 5 101 127 217](../../../images/language-models/vision-language-action-models/actions-as-words.svg)

The picture shows how this works. A movement of the gripper has several parts, because
it moves along three directions, called x, y and z, and it turns about three
directions, called roll, pitch and yaw. It also opens or closes, and RT-2 adds one
more part that says whether the task is finished. Each part has a smallest and a
largest allowed value, and that range is cut into 256 equal steps, numbered 0 to 255.
So the model does not need to write an exact distance, and it only needs to name the
step, such as step 128, which is near the middle and means "almost no movement". A
whole movement therefore becomes eight numbers, such as `1 128 91 241 5 101 127 217`.

The benefit is that no new part is needed, because the model already writes numbers as
tokens. So the training simply adds examples in which the right answer to a picture
and an instruction is a string of eight numbers. OpenVLA, the first open VLA, uses the
same idea, and [section 5.6](#56-openvla) is about it. Of the models in section 5, only
OpenVLA and π0-FAST write movements this way.

The drawback is that 256 steps is coarse, and the model writes the numbers one token
at a time. Writing one token takes about as long as writing one word in a chat
window. So a model that writes eight tokens for every movement is slow.

### Way 2: add a small action expert

The second way keeps the vision-language model for the understanding, and adds a
second, smaller network that only produces movements. This smaller network is called
the **action expert**, and most of the models in [section
5](#5-well-known-models-of-this-kind) work this way:
[SmolVLA](#51-smolvla-the-one-to-start-with) from Hugging Face, [π0 and
π0.5](#52-the-pi-models-from-physical-intelligence) from Physical Intelligence, [GR00T
N1.7](#53-gr00t-n17-from-nvidia) from NVIDIA,
[MolmoAct2](#54-molmoact2-from-the-allen-institute-for-ai) from the Allen Institute for
AI, and [X-VLA](#55-x-vla) from an academic group.

![What goes in, then ten random points being moved step by step into a smooth path of gripper positions](../../../images/language-models/vision-language-action-models/backbone-and-action-expert.svg)

The picture below shows what happens, in four steps.

1. The vision-language model reads the pictures and the instruction once, and then
   passes its internal numbers to the action expert.
2. The action expert starts from random numbers, which in the picture are ten random
   points, and each point is one future position of the gripper.
3. The action expert moves every point a little towards where it should be, and it
   does this a few times, for example ten times. At each step it uses the numbers from
   the vision-language model, so it "knows" where the mug and the bowl are.
4. After the last step, the points form a smooth path from where the gripper is now to
   where it should go next.

This method of starting from random numbers and moving them step by step is called
**flow matching**, and every model named just above produces its movements this way,
which is why those two words come up again in section 5. The page on
[diffusion and flow policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
explains it in more detail, and why it copes well when a task can be done in more
than one way.

The benefit is that the output is smooth, exact numbers rather than 256 coarse
steps. The action expert is also small, so it is quick to run.

### Why it outputs a chunk of actions

Both ways are slow compared with an arm, because an arm's controller wants a new
target many times a second, while a large model may take a noticeable part of a second
to run once.

So the fix is to output a short sequence of movements each time, instead of one. This
sequence is called a **chunk**, and the arm works through the chunk while the model is
already working out the next one.

![Two timelines: one command per model run, with pauses, against a chunk of eight commands per model run, with no pauses](../../../images/language-models/vision-language-action-models/one-step-vs-chunk.svg)

The picture compares the two. In the top row, the model sends one command each time it
finishes, and the arm waits in between. In the bottom row, each run of the model gives
eight commands, spread over the time of the next run, so the arm gets a steady flow of
commands. The movement is also smoother, because the commands in one chunk come from
one decision. The page on [action chunking
transformers](../../06_movement-models/02_most-used/02_action-chunking-transformers.md)
explains chunks in detail.

---

## 4. How it is trained

A VLA is trained in three stages, one after another. The first stage is the
vision-language model's own training, from the [previous
page](02_vision-language-models.md#4-how-it-is-trained), while the next two stages use
robot data.

A **demonstration** is one recording of the task being done well. A person usually
drives the robot through the task, and the robot records the camera pictures and
joint angles many times a second. Each recording also has a sentence that says what
the task was. The page on
[where the data comes from](../../01_what-models-are/05_where-the-data-comes-from.md)
describes how demonstrations are recorded.

1. **Train on many robots.** The model is trained on a large pool of demonstrations,
   from many laboratories and many kinds of robot arm, and the training teaches it to
   output the recorded movement for each recorded picture and sentence. For example,
   OpenVLA was trained on 970,000 demonstrations from a shared pool called Open
   X-Embodiment, while the π0 models were trained on 10,000 hours or more of robot
   data. Some laboratories also mix in the internet pictures and questions from the
   vision-language model's own training, because this keeps the model from forgetting
   what it knew about objects and words.
2. **Fine-tune on your robot and your task.** The model from stage 1 is then trained a
   little more, on demonstrations of your task on your robot. This extra training is
   called **fine-tuning**, and it usually needs far fewer demonstrations than stage 1,
   often tens to hundreds.

Robot demonstrations are slow and expensive to record, because each one needs a robot
and a person, and this is the main limit on the whole field. So in 2026 several
laboratories started to replace part of the robot data with video of people doing
everyday tasks with their own hands. NVIDIA's GR00T N1.7, for example, was trained on
20,000 hours of such video alongside robot demonstrations. The [data and demonstration
document](../../../03_frameworks/08_frontier/03_data-and-demonstration.md) covers this
in depth.

---

## 5. Well-known models of this kind

This section names the models you will actually meet, says what each one is for, and
ends with one recommendation you can follow. The size of a model is given as its number
of **parameters**, and a parameter is one of the adjustable numbers inside the network
that training sets.

The table has two columns, so read a row from left to right as one sentence about one
model. The left column names the model and says how current it is. The right column
holds everything else: the size, the licence on the code and the licence on the trained
numbers, what the model is best at, and the case for choosing it. A model has two
licences because the programs and the trained numbers are published separately and often
on different terms, so each row names the code licence first and the weights second.
Every licence here was read from the project's own files in September 2026 by the
[frontier
document](../../../03_frameworks/08_frontier/02_foundation-models.md#10-the-open-shelf-what-you-can-download-today),
which is the page to check when you want to know what is current.

| Model | What decides it |
| --- | --- |
| [SmolVLA](https://huggingface.co/lerobot/smolvla_base), most used in 2026 | It has 450 million parameters, and both its code and its weights are Apache-2.0. It is the one model here that runs on hardware you already own. Pick it when you are learning, with a small arm and one computer. |
| [π0, π0-FAST and π0.5](https://github.com/Physical-Intelligence/openpi), most used in 2026 | Their size is not stated, their code is Apache-2.0, and their weights are served from the project's own storage with no licence of their own. They are the best models here at smooth two-armed tasks such as folding cloth. Pick them when you have an NVIDIA card and a robot like ALOHA or DROID. |
| [GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T), most used in 2026 | It has 3 billion parameters, its code is Apache-2.0, and its weights are under the NVIDIA Open Model License. It is the best model here at working on a robot it was not trained on. Pick it when you want the most capable open model and you have NVIDIA hardware. |
| [MolmoAct2](https://huggingface.co/allenai/MolmoAct2), worth betting on | It has 5 billion parameters, its code is Apache-2.0, and its model card declares no licence for the weights. It publishes more evidence about itself than anything else here. Pick it when you have to justify the choice with numbers, or when you own an SO-100. |
| [X-VLA](https://huggingface.co/2toINF/X-VLA-Pt), worth betting on | It has 0.9 billion parameters, its code licence has not been checked, and its weights are Apache-2.0. It is built to be adapted to an unusual robot. Pick it when the licence on the weights themselves has to be permissive. |
| [OpenVLA](https://huggingface.co/openvla/openvla-7b), historical | It has 7 billion parameters, and its code and its weights are both MIT. It is the number everyone compares against. Pick it when you want that baseline, or one whole model you can read. |

### 5.1 SmolVLA, the one to start with

SmolVLA is **most used in 2026** by people learning on a small arm, because it is the
only model in the table that runs without an NVIDIA graphics card. Hugging Face released
it on 3 June 2025. It has 450 million parameters: a SmolVLM2 vision-language backbone
and a flow-matching action expert of roughly 100 million, the arrangement of [way
2](#way-2-add-a-small-action-expert). Its authors trained it on about 10 million frames
from 487 public datasets and report about 78 per cent success on real tasks with an
SO-100 arm.

The obvious alternative is π0.5, which is the stronger model. You pick SmolVLA anyway
when you lack the hardware for π0.5, and that is most people: the π0 repository asks for
an NVIDIA card with more than 8 GB of video memory, while SmolVLA's
[announcement](https://huggingface.co/blog/smolvla) says the model runs on a central
processing unit and on a MacBook.

It costs you accuracy, because it is the smallest model here and the weakest on a task
far from its training data, and it must be fine-tuned on your own recordings first.
LeRobot's [guide](https://huggingface.co/docs/lerobot/smolvla) recommends about 50
recorded episodes and puts 20,000 training steps at roughly four hours on one A100
graphics card, while its [hardware
guide](https://huggingface.co/docs/lerobot/hardware_guide) puts that training at 10 to
16 GB of video memory, so a Mac is slow rather than useless. The usual mistake is too
few recordings of each variation: the authors found 25 episodes of their task not enough
and 50 enough.

The library is [LeRobot](https://github.com/huggingface/lerobot), and SmolVLA is driven
from the command line rather than from Python. Two commands do the whole job.

```bash
pip install -e ".[smolvla]"   # the SmolVLA extras, inside a LeRobot checkout

# Fine-tune the public base model on your own recordings.
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/mydataset \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/my_smolvla \
  --policy.device=cuda

# Run the fine-tuned model on the real arm.
lerobot-rollout \
  --policy.path=${HF_USER}/my_smolvla \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30}}" \
  --task="Grasp a lego block and put it in the bin."
```

LeRobot gives you the training loop, the dataset format, the cameras and the arm driver.
You supply the dataset, recorded as [section
6](#6-a-worked-example-teaching-a-small-arm-to-put-a-mug-in-a-bowl) describes, and your
own serial port and camera index. The sentence after `--task` must be the sentence you
recorded with, because the model learned to connect those words to that movement.

### 5.2 The pi models from Physical Intelligence

These are **most used in 2026** by people who have an NVIDIA graphics card, because they
are the only weights from a frontier laboratory that anyone can download. Physical
Intelligence announced π0 on 31 October 2024 and published it on 4 February 2025, then
announced π0.5 on 22 April 2025. π0 attaches a flow-matching action expert to a
pretrained vision-language model, π0.5 adds training that stops robot fine-tuning from
damaging what the language model already knew, and π0-FAST writes movements as tokens
instead, as in [way 1](#way-1-write-the-movement-as-tokens). The [openpi
repository](https://github.com/Physical-Intelligence/openpi) puts their training data at
10,000 hours or more.

The obvious alternative is GR00T N1.7, which is also open and also uses an action
expert. You pick a pi model when your robot resembles ALOHA or DROID, because fine-tuned
checkpoints exist for those two platforms, and when you read research, because π0.5 is
what most 2026 papers measure themselves against.

It costs you an NVIDIA card and a Linux machine. The repository asks for more than 8 GB
of video memory to run a model, more than 22.5 GB to fine-tune part of it and more than
70 GB to fine-tune all of it, and says only Ubuntu 22.04 has been tested. The code is
Apache-2.0, but the weights come from the project's own storage with no separate
licence, so read the repository before shipping a product. The first failure is usually
a licence prompt, not a crash: the π0.5 recipe in LeRobot uses Google's gated
`google/paligemma-3b-pt-224` tokenizer, which you must accept on the Hugging Face
website first.

The library is openpi, written in JAX, and the same models are in
[LeRobot](https://huggingface.co/docs/lerobot/pi05) for people who prefer PyTorch. This
is openpi's own example, with a checkpoint fine-tuned on the DROID robot.

```python
from openpi.training import config as _config
from openpi.policies import policy_config
from openpi.shared import download

config = _config.get_config("pi05_droid")
checkpoint_dir = download.maybe_download("gs://openpi-assets/checkpoints/pi05_droid")

policy = policy_config.create_trained_policy(config, checkpoint_dir)

example = {
    "observation/exterior_image_1_left": ...,   # the camera looking at the table
    "observation/wrist_image_left": ...,        # the camera on the wrist
    "prompt": "pick up the fork",
}
action_chunk = policy.infer(example)["actions"]
```

The library downloads the checkpoint, runs both networks, and hands back a chunk of
movements. You supply the contents of `example`: real pictures, the arm's joint angles,
and the key names this checkpoint expects, which is why they say `exterior` and `left`.
You also write the loop that reads the cameras and sends the chunk to the arm.

### 5.3 GR00T N1.7 from NVIDIA

GR00T N1.7 is **most used in 2026** where capability matters more than the price of the
graphics card, and it is the most capable open model on the shelf. NVIDIA tagged it on
18 April 2026 as a general-availability release, which for NVIDIA means a supported
product rather than an experiment. It has 3 billion parameters, a Cosmos-Reason2-2B
backbone built on the Qwen3-VL architecture, and a flow-matching action head, and it was
pretrained on 20,000 hours of human video alongside robot demonstrations.

The obvious alternative is π0.5. You pick GR00T when the robot you own is not the robot
the model was trained on. Its movements are distances from the gripper's current pose
rather than absolute positions, and NVIDIA names that one choice as the key factor in
its cross-robot performance, because three centimetres to the left means the same thing
on every arm while a coordinate does not. The same choice is what let NVIDIA train on
human video, since a hand and a gripper move in the same relative terms.

It costs you NVIDIA hardware, with no way round it: 16 GB or more of video memory to run
the model, 40 GB or more to fine-tune it, and a supported platform, which means a
desktop card on CUDA 12.8, a Jetson Thor or Orin, or a DGX Spark. The licence needs
care. The code is Apache-2.0, while the weights are under the [NVIDIA Open Model
License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/),
which allows commercial use but adds conditions Apache-2.0 does not, such as attribution
when you redistribute and the loss of the licence if you switch off a safety check
without putting a similar one in its place. The repository's own sentence about being
"fully commercially licensable under Apache 2.0" describes the code. The first run
usually fails for a smaller reason: the backbone is a gated download, so without Hugging
Face access the model refuses to load.

The library is the [Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) repository, and
the model is also in [LeRobot](https://huggingface.co/docs/lerobot/groot). NVIDIA runs
the model as a server and the robot as a client, so the graphics card does not have to
sit on the robot.

```bash
# On the machine with the graphics card.
uv run python gr00t/eval/run_gr00t_server.py \
    --model-path nvidia/GR00T-N1.7-3B \
    --embodiment-tag OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT \
    --device cuda:0
```

```python
from gr00t.policy.server_client import PolicyClient

policy = PolicyClient(host="localhost", port=5555)

obs, info = env.reset()                  # your robot, or your simulator
action, info = policy.get_action(obs)    # one chunk of movements
obs, reward, done, truncated, info = env.step(action)
```

The server loads the model and does the thinking. You supply `env`, your own code around
the real arm or the simulator, which must produce the picture and joint-angle names
GR00T expects and accept the movements it returns. You also choose the embodiment tag,
which tells the model which robot it is driving and so decides how its numbers are read.

### 5.4 MolmoAct2 from the Allen Institute for AI

MolmoAct2 is **worth betting on**, because no other open model publishes as much
evidence about itself, and because the field is moving towards models that reason about
the scene before they move. The Allen Institute for AI published it on 4 May 2026, with
a paper at [arXiv 2605.02881](https://arxiv.org/abs/2605.02881). It has 5 billion
parameters and attaches a flow-matching action expert to a vision-language model that
writes words, so one model both reasons and moves. It ships with its training data,
including 720 hours of two-armed teleoperation, and with fine-tuned versions for the
DROID Franka arm, a two-armed YAM robot, and the SO-100 and SO-101 learning arms.

The obvious alternative is again π0.5. You pick MolmoAct2 when you have to defend the
choice to somebody, because its authors claim the widest evaluation of any open
vision-language-action model, across seven simulated and real benchmarks, and publish
the datasets with it. They report beating π0.5, and report that the vision-language
model underneath beats GPT-5 and Gemini Robotics ER 1.5 across 13 tests of reasoning
about the physical world. The second reason is narrower: it has a ready checkpoint for
the SO-100 and SO-101, the arms a beginner is likely to own, and neither π0.5 nor GR00T
has one.

It costs you memory and legal certainty. Each checkpoint is about 22 GB to download, and
the project's inference server fits under 16 GB of video memory at reduced precision
while its full-precision setting wants around 96 GB free. The code is Apache-2.0, read
from its licence file, but the model card on Hugging Face declares no licence at all in
its metadata, even though the repository's README says Apache 2.0, so ask the authors
before building a product on the weights. The project also warns that it has been
checked only on the SO-100 and the Franka DROID setup, and only for simple tasks of the
kind it was trained on.

The library is [LeRobot](https://huggingface.co/docs/lerobot/molmoact2), which carries
MolmoAct2 as a policy, and the original training code is in
[allenai/molmoact2](https://github.com/allenai/molmoact2). This is LeRobot's own command
for the SO-100 checkpoint.

```bash
lerobot-rollout \
  --policy.path=lerobot/MolmoAct2-SO100_101-LeRobot \
  --rename_map='{"observation.images.top": "observation.images.cam0", "observation.images.side": "observation.images.cam1"}' \
  --robot.type=so100_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras='{
      top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
      side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}
  }' \
  --task="pick up the red cube" --duration=30
```

LeRobot supplies the model, the cameras and the arm driver. You supply two cameras in
the positions the checkpoint expects, a primary view and a second view, and the
`--rename_map` that says which of yours is which. People leave that mapping out, and the
model then reads the side view as if it were the view from above.

### 5.5 X-VLA

X-VLA is **worth betting on**, because it attacks the problem that [section
7](#7-what-goes-wrong-and-what-people-do-about-it) calls the field's worst, which is a
model that works on its builders' robot and not on yours. An academic group published it
in November 2025, with a paper at [arXiv 2510.10274](https://arxiv.org/abs/2510.10274).
The released base model has 0.9 billion parameters, as LeRobot's page for it states, and
was trained on 290,000 recorded episodes from seven robot platforms. Each robot and each
dataset is described by a small set of learned numbers, called a **soft prompt**, which
goes into the model with the pictures and the instruction, so adapting to a new robot
means learning a new soft prompt.

The obvious alternative at this size is SmolVLA. You pick X-VLA when the licence
matters, because Apache-2.0 covers the weights themselves, and when your robot differs
from everything in the training data, because its authors report nearly reaching π0's
scores on two benchmarks while adjusting 1 per cent of the model, or 9 million numbers.
Treat that as the best case, not the recipe: LeRobot's own guidance for a new robot is
to train the vision and language parts as well.

It costs you a graphics card, because LeRobot's hardware guide places X-VLA with the
large models at about 24 to 40 GB of video memory for training, so it is not a Mac model
despite its size. The frontier document records its code licence as not checked, which
is worth checking yourself. Its checkpoints are uneven too: the simulation one reports
93 per cent on the LIBERO benchmark, while each real-robot one is tied to one platform,
so you will probably fine-tune.

The library is [LeRobot](https://huggingface.co/docs/lerobot/xvla), which carries X-VLA
as a policy type.

```bash
pip install -e .[xvla]

lerobot-train \
  --dataset.repo_id=YOUR_DATASET \
  --policy.path=lerobot/xvla-base \
  --policy.repo_id=HF_USER/xvla-your-robot \
  --policy.dtype=bfloat16 \
  --policy.action_mode=auto \
  --steps=20000 \
  --policy.device=cuda \
  --policy.train_soft_prompts=true
```

LeRobot holds the pretrained model and the training loop. You supply the dataset,
recorded on your own robot, and the decision about what to train: the last flag trains
the soft prompt, and the guidance is to let the vision and language parts train too.

### 5.6 OpenVLA

OpenVLA is **historical**, and it is here because it explains how the others work and
because every paper you read compares against it. A group from Stanford, UC Berkeley,
Google DeepMind and the Toyota Research Institute published it in June 2024, with a
paper at [arXiv 2406.09246](https://arxiv.org/abs/2406.09246). It has 7 billion
parameters, it was trained on 970,000 real robot demonstrations from the pooled Open
X-Embodiment dataset, and it writes movements as tokens exactly as [way
1](#way-1-write-the-movement-as-tokens) describes. That method came from Google's
[RT-2](https://robotics-transformer2.github.io/) in 2023, which was never released, so
OpenVLA was the first such model anybody could download, and in September 2026 it was
still the most downloaded robotics model on Hugging Face.

You would not pick it to drive a robot today, because SmolVLA and π0.5 are maintained
while the OpenVLA repository has had no commit since March 2025. You would pick it for
two other reasons. It is the baseline that published results are measured against, so
you may have to run it to compare. And its code and its weights are both MIT, the most
permissive pair in the table, so you can read, change and publish it without asking
anybody.

It costs you speed above all. It writes one movement at a time, which is slow in the way
the [chunking section](#why-it-outputs-a-chunk-of-actions) explains, and its own
successor recipe, [OpenVLA-OFT](https://openvla-oft.github.io/), exists to fix that. Its
7 billion parameters also need an NVIDIA graphics card, so it does not run on a Mac.

The library is `transformers` from Hugging Face, because OpenVLA is published as an
ordinary Hugging Face model. This is the example from its own [model
card](https://huggingface.co/openvla/openvla-7b), with the instruction changed.

```python
import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

processor = AutoProcessor.from_pretrained("openvla/openvla-7b", trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(
    "openvla/openvla-7b",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
).to("cuda:0")

image = Image.open("table.jpg")
# The wording is fixed: OpenVLA was trained with "In:" before the instruction
# and "Out:" at the end, and other wordings give worse movements.
prompt = "In: What action should the robot take to put the mug in the bowl?\nOut:"

inputs = processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)
# unnorm_key names the recorded dataset whose ranges turn the model's
# 0-to-255 steps back into real distances.
action = vla.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)
```

The library gives you the seeing, the reading of the instruction and the choice of
movement in one call, and `predict_action` turns the tokens back into numbers. You
supply everything that touches the robot. The numbers say how far to move and turn the
gripper and whether to open or close it, so your program turns them into joint commands,
and you write the loop and the success check, because the model never stops by itself.

### 5.7 The ones you will read about but cannot have

The strongest models of 2026 are not downloadable, and knowing their names matters
anyway, because every claim you read about what robots can now do comes from one of
them. π0.7 from Physical Intelligence, Gemini Robotics 2 from Google DeepMind, Helix 2.5
from Figure and Dyna-2 from Dyna Robotics were all demonstrated rather than released.

One of them is different in kind rather than in strength, and it is the reason this book
has a page on the idea. [Skild S1](https://www.skild.ai/blogs/s1), announced in August
2026, is not told what to do in words at all. It is shown one video of the task and then
does the task, with no fine-tuning. Everything else on this page learns a task by having
that task trained into its weights, so a model that takes the task as an input instead
is a different arrangement rather than a better model of the same arrangement.
[Prompting with a
demonstration](../../10_making-models-work-on-an-arm/03_also-used/02_prompting-with-a-demonstration.md)
explains how that works and what it costs, and it is honest about how thin the published
evidence still is.

### 5.8 How to choose

Start with SmolVLA. On a small arm, with one computer and no NVIDIA graphics card, it is
the only model here you can actually run, and the loop of recording demonstrations,
fine-tuning and watching the arm fail teaches you more than the choice of model does.

Four things change that answer.

- **You have an NVIDIA graphics card with 16 GB or more.** Then use π0.5 if your robot
  resembles ALOHA or DROID, and GR00T N1.7 if it does not, because GR00T's relative
  movements transfer between robot bodies better.
- **You own an SO-100 or SO-101 and SmolVLA is not accurate enough.** Then try the
  MolmoAct2 checkpoint for those arms, which is the only frontier-style open model with
  a checkpoint for that hardware.
- **Somebody has to approve the licence.** Then choose from the models that are
  permissive on the weights themselves, which here are X-VLA and OpenVLA, or
  [GigaBrain-0.7](https://huggingface.co/open-gigaai/GigaBrain-0.7-3.5B-Base), a
  3.5-billion-parameter model from August 2026 that is Apache-2.0 on both and sits on
  the frontier document's shelf.
- **You need a number to compare against.** Then run OpenVLA, because that is the
  comparison everybody else publishes.

Do not choose on success rates reported by different laboratories. Each number was
measured by the group that benefits from it, on a robot you do not have, as [section
7](#7-what-goes-wrong-and-what-people-do-about-it) explains. The honest way to choose
between two models is to fine-tune both on your own recordings and count the successes
on your own arm.

---

## 6. A worked example: teaching a small arm to put a mug in a bowl

Here is SmolVLA on a small learning arm, such as the SO-101. The arm has a camera
above the table and a camera on the wrist, and the software is
[LeRobot](https://github.com/huggingface/lerobot), a free library that records
demonstrations, trains models and runs them.

1. **Record demonstrations.** You move a second, identical arm by hand, and the robot
   arm copies it. This setup is called a **leader arm** and a **follower arm**. You
   put a mug in a bowl a few dozen times, and each time you place the mug and the bowl
   somewhere different. LeRobot records both camera pictures and the joint angles,
   with the sentence "put the mug in the bowl".
2. **Fine-tune.** You start from the SmolVLA model that Hugging Face trained on many
   robots, and train it further on your recordings. SmolVLA's authors say this can be
   done on a single ordinary graphics card.
3. **Run it.** Each time the model runs, it reads the two pictures, the joint angles
   and the sentence, and then outputs a chunk of joint targets. The arm's controller
   moves through the chunk, and the model runs again with new pictures.
4. **Check the result.** The model does not report whether it succeeded, because it
   simply keeps outputting movements. So you add a check, such as a [vision-language
   model](02_vision-language-models.md#6-a-worked-example-fetching-the-right-mug)
   asking "Is the mug in the bowl?", or a person watching.

Then try things that you did not record at all. Put a different mug on the table, or
say "put the cup in the bowl" instead of "mug". A model that started from a
vision-language model has a better chance with these than a policy trained from
nothing, because it already knows that a cup and a mug are alike. It is still not
certain to work, so the only way to know is to try each change several times and count
the successes.

---

## 7. What goes wrong, and what people do about it

VLAs are the newest kind of model in this book, and their limits are important. The
list below gives the main ones, with what people do about each. The [frontier
document](../../../03_frameworks/08_frontier/02_foundation-models.md#11-what-none-of-them-can-do-yet)
gives the evidence for each.

- **They do not control force.** A VLA outputs positions, not forces. So it is good at
  tasks where the position is what matters, and weak at tasks where pressing gently or
  firmly matters. Google's own figures for Gemini Robotics 2 show this: 92 per cent
  success at unscrewing a light bulb, but 36 per cent at screwing one in. People put a
  force-aware controller underneath the VLA for contact tasks. The [touch and body
  models](../../09_touch-and-body-models/01_overview.md) chapter covers the models
  that sense force.
- **They cannot refuse.** A VLA always outputs a movement, even when it has never seen
  anything like the scene in front of it, because it has no way to say "I do not
  know". So the arm's ordinary safety limits must stay switched on, and a separate
  check decides when to stop.
- **They are upset by small changes near the gripper.** A 2026 study found that these
  models cope well with a whole object being hidden, but get much worse when small
  details at the point of contact change. They are also upset when a camera picture
  arrives late. So you test with the lighting, objects and cameras you will really
  use.
- **They need work on each new robot.** A model that works on its builders' robot may
  need new demonstrations and fine-tuning before it works on yours. Treat "works with
  no extra training" as "worked on the authors' robot".
- **They succeed less often than the videos suggest.** Published success rates for the
  best models are often between one-half and three-quarters on hard tasks, while a
  factory needs close to every attempt to succeed. So people add a success check, a
  retry, and a person who can take over.
- **You cannot easily tell why they failed.** A pipeline of separate models lets you
  see which part went wrong. A VLA is one network, so a failure has no obvious cause.
  Recording every run, with its pictures, is the usual fix.
- **They need a large computer.** Except for the smallest ones, VLAs need an NVIDIA
  graphics card with many gigabytes of memory. The [frontier
  document](../../../03_frameworks/08_frontier/02_foundation-models.md#12-what-runs-on-an-apple-silicon-mac)
  lists what runs on a Mac.

---

## 8. Why use a vision-language-action model, and what it costs

A VLA is one network that turns camera pictures, an instruction and joint angles
into arm movements. It lets one model handle many tasks and many objects, including
some it has not been shown on your robot, because it inherits knowledge about
objects and words from a vision-language model.

There are two obvious alternatives to using a VLA at all. The first is a pipeline of
separate parts: a [planner](../03_also-used/01_language-models-as-planners.md), a
[seeing model](../../03_seeing-models/01_overview.md), a [grasp
model](../../05_grasp-models/01_overview.md) and a motion planner. Each part can be
tested on its own, and a failure can be traced to one part. The second is a small
policy trained from nothing on one task, such as an [action chunking
transformer](../../06_movement-models/02_most-used/02_action-chunking-transformers.md).
It is much smaller, it can be trained on a Mac, and on one fixed task it often works
just as well.

So the VLA earns its place when the objects and the instructions keep changing, and
you cannot write or train a separate part for each case. For one fixed task, the
small policy or the pipeline is usually the better choice.

It costs you a large graphics card, a pile of demonstrations for fine-tuning, and a
model whose failures are hard to explain. It also costs certainty: the success rates
of today's best VLAs are well below what a production line needs.

---

## 9. The written alternative

The written alternative is a pipeline made only of ordinary code. A [behaviour
tree](../../../06_programming-techniques/08_decisions-and-task-logic/02_most-used/02_behaviour-trees.md)
holds the order of the steps and the retries. [Pose from
points](../../../06_programming-techniques/02_geometry-and-cameras/02_most-used/04_pose-from-points.md)
finds a known object, and [sampling-based
planning](../../../06_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md)
moves the arm to it. Book 3's [programmed
methods](../../../03_frameworks/04_one-arm-training/02_programmed-methods.md) shows
these parts working together on one arm.

The written pipeline wins for one fixed task with known objects, because each part can
be tested on its own, and it does the same thing every time. But the VLA wins when the
objects and the instructions keep changing.

---

## 10. Where to read next

- [Foundation models and generalist
  policies](../../../03_frameworks/08_frontier/02_foundation-models.md) is the record
  of the current state of the art, and it covers every important VLA as of September
  2026, with what it can do, what it cannot, and whether you can download it.
- [Action chunking
  transformers](../../06_movement-models/02_most-used/02_action-chunking-transformers.md)
  and [diffusion and flow
  policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
  explain the two ideas that VLAs borrowed from the movement models chapter.
- [World models](../../08_world-models/01_overview.md) is the next chapter, because
  some of the newest robot models predict the next camera picture as well as the next
  movement.
- [Learned methods](../../../03_frameworks/04_one-arm-training/03_learned-methods.md)
  in the frameworks book compares VLAs with the other ways of training one arm.
