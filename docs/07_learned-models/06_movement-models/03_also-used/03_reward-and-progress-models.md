# Reward and progress models

The reinforcement learning page assumed that somebody can write a rule for the
score. The two pages before it assumed that somebody can tell a good recording
from a bad one. So this page answers the question both of those left open: how
can a robot tell, by itself, whether an attempt at a task went well? The models
that do this job look at the camera pictures of an attempt and give back a
judgement. Some say "success" or "failure", some say how far along the task is,
and some are large models that answer a question in words. This page calls all
of them **judge models**, whatever form their answer takes.

The page is for a reader who has read
[reinforcement learning policies](01_reinforcement-learning-policies.md). That page
needs a **reward**, which is a number that says how well an attempt went, and it
assumes someone can write a rule for that number. This page is about what to do when
nobody can write the rule, because the only way to tell is to look. Every new
word is
explained where it first appears.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [The four kinds of judge](#3-the-four-kinds-of-judge)
4. [A worked example: scoring progress from pictures](#4-a-worked-example-scoring-progress-from-pictures)
5. [A second worked example: where to put the cut-off](#5-a-second-worked-example-where-to-put-the-cut-off)
6. [Where it is used on a robot arm](#6-where-it-is-used-on-a-robot-arm)
7. [Well-known models and libraries](#7-well-known-models-and-libraries)
8. [What goes wrong, and what people do about it](#8-what-goes-wrong-and-what-people-do-about-it)
9. [Why this kind, and what it costs](#9-why-this-kind-and-what-it-costs)
10. [The written alternative](#10-the-written-alternative)
11. [Where to read next](#11-where-to-read-next)

---

## 1. What it is

The introduction called these models judges, so here is the idea in one
sentence. A judge model is a network that looks at what the camera saw during an
attempt, and gives back a number that says how well the attempt is going.

For example, think of a cooking teacher and a student, where the student cooks
and the teacher does not cook at all. The teacher only tastes, and says "good",
"not yet" or "nearly there", and the student gets better from those words. So a
judge model matches the teacher, while the movement model, which this chapter
calls the **policy**, matches the student.

But why would you need a network for this at all? For some tasks a short rule is
enough, because in a simulator the program knows exactly where every object is.
There, "the peg is in the hole" is one line of code. On a real arm, nobody tells
the program where the peg is, and there is only a camera picture. Questions like
"is the towel folded neatly?" or "is the mug in the bowl?" have no simple rule
on a picture. So people train a network to answer the question instead.

---

## 2. What goes in and what comes out

Section 1 said that a judge looks at pictures, and this section says exactly
which ones. A judge model takes in pictures from the robot's cameras. It can
take one picture, such as the last one of an attempt, or it can take the whole
video of the attempt. Some judges also take a **goal**, which is a picture of
the finished task, or a sentence such as "put the mug in the bowl".

It gives back a number, and what that number means depends on the kind of judge.
The table below shows the three common kinds of answer. Read each row as one
kind of answer and an example of it.

| What comes out | What it means | An example |
| --- | --- | --- |
| a success score from 0 to 1 | how sure the judge is that the task is done | 0.93: "almost certainly done" |
| a progress score for each frame | how far along the task is, from 0 (start) to 1 (done) | 0.50 halfway through a fold |
| an answer in words | a yes or no, or a short explanation | "No, the mug is still in the gripper." |

Notice that the judge does not move the arm. It is used beside the policy, to
score it, to stop it, or to train it.

---

## 3. The four kinds of judge

Section 2 listed three kinds of answer, and those answers come from four kinds
of judge model that people use on arms. They differ in what they are trained on,
and in how much work they need before they can be used.

**A success classifier.** A **classifier** is a model that puts an input into one of
a few groups, and here the groups are "success" and "failure". You train it on
pictures of your own task, each marked by a person as success or failure. Then it
gives a score from 0 to 1 for any new picture. It is small and fast, but it only
knows your one task. HIL-SERL, the real-arm learning system in the
[reinforcement learning page](01_reinforcement-learning-policies.md#5-well-known-models-and-methods),
uses one of these as its reward.

**A progress estimator.** This gives a score for every frame of the video, and not
just for the last one. The score then rises as the task gets closer to done. The
best-known ones are trained on large amounts of video of people doing everyday
tasks.
They turn each picture into a short list of numbers, called an **embedding**, and an
embedding is made so that similar pictures get similar lists. The progress is then
read from how close the current embedding is to the embedding of the goal picture,
and section 4 works through this with real numbers.

**A vision-language model used as the judge.** A
[vision-language model](../../07_language-models/02_most-used/02_vision-language-models.md)
is a large model that takes pictures and a question in words, and answers in words.
So you ask it "Is the red mug in the bowl?" and it answers, and you can also ask it
to rate progress. It needs no training on your task, but it is slow, and it can be
wrong in ways that are hard to predict.

**A reward learned from demonstrations.** This is called **inverse reinforcement
learning**. Normal reinforcement learning starts from a reward and learns a
movement,
while inverse reinforcement learning goes the other way. It starts from
recorded movements by a person, and learns a reward that would explain why the
person
moved that way. The idea is that the reward carries over to new situations better
than the copied movement does. But it is rarely used on real arms today, and the
[learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#13-learning-the-goal-instead-of-the-motion)
explains why.

---

## 4. A worked example: scoring progress from pictures

The second kind of judge was the progress estimator, and this example shows how
one turns pictures into a score. The numbers are small and made up, so that you
can follow them by hand. The arithmetic was run in Python, so the results below
are copied from that run.

A real estimator turns each picture into an embedding of hundreds of numbers,
but here each picture becomes only three numbers. The task is to put a mug in a
bowl, the camera sees six frames, and the last one is the goal.

1. **Turn the goal picture into numbers.** The goal embedding is (0.9, 0.1, 0.8).
2. **Turn each frame into numbers.** Frame 0, at the start, is (0.1, 0.7, 0.2).
   Frame 1 is (0.3, 0.6, 0.3), and so on until frame 5, which equals the goal.
3. **Measure how far each frame is from the goal.** The distance is the ordinary
   straight-line distance between two points. For frame 0 the differences are -0.8,
   0.6 and -0.6, so you square them, add them and take the square root, which is the
   square root of 1.36, or 1.166. The six distances are 1.166, 0.927, 0.583, 0.520,
   0.173 and 0.
4. **Turn distance into progress.** Progress is 1 minus the current distance divided
   by the starting distance, so frame 0 gives 1 − 1.166 / 1.166 = 0, and frame 1
   gives 1 − 0.927 / 1.166 = 0.205. The six progress scores are 0, 0.205, 0.500,
   0.554, 0.851 and 1.000.
5. **Turn progress into a reward.** The reward for each step is the progress after
   the step minus the progress before it. The five rewards are 0.205, 0.295, 0.054,
   0.297 and 0.149, and they add up to exactly 1, which is the whole distance from
   start to goal.

Step 5 is how VIP, one of the best-known progress estimators, is used as a
reward for reinforcement learning. A step that moves towards the goal earns a
positive reward, while a step that moves away earns a negative one. So the small
reward from frame 2 to frame 3 means that step did very little.

![Left: bars for the six progress scores of the worked example, with the step rewards below. Right: three whole attempts scored frame by frame](../../../images/movement-models/reward-and-progress-models/progress-along-an-attempt.svg)

The left picture shows the six scores from the example, with the step rewards in
orange underneath. The right picture shows why a score for every frame is
useful, and it shows three made-up attempts. The green one rises steadily and
crosses the line where the task counts as done, while the grey one gets stuck
halfway. The red one gets close, then falls sharply when the mug slips, and then
climbs again. So a judge that only looked at the last frame would call the red
attempt a success, and it would never notice that the attempt went wrong on the
way.

---

## 5. A second worked example: where to put the cut-off

Section 4 scored progress, and this example scores success, which brings a
choice with it. A success classifier gives a score rather than a yes or no. So
you have to choose a **cut-off**, which is the score above which you count the
attempt as a success. This choice matters more than it seems at first.

This example uses made-up scores for 100 attempts that really succeeded and 100
that really failed, and they were drawn at random in Python with a fixed seed.
The counts below come from that run, and there are two kinds of mistake:

- A **false success** is a failed attempt that the judge calls a success.
- A **missed success** is a real success that the judge calls a failure.

The table shows what three cut-offs give. Read each row as one choice of
cut-off, and the two numbers as the mistakes it makes out of 100 of each kind.

| Cut-off | False successes (of 100 failures) | Missed successes (of 100 successes) |
| --- | --- | --- |
| 0.5 | 10 | 7 |
| 0.7 | 2 | 21 |
| 0.9 | 0 | 69 |

![Histograms of classifier scores for real failures and real successes, with dashed lines at 0.5, 0.7 and 0.9](../../../images/movement-models/reward-and-progress-models/choosing-the-threshold.svg)

The picture shows the same scores as two piles. Red is the failures, which
mostly score low, and green is the successes, which mostly score high. But the
piles overlap in the middle, so wherever you put the line, some attempts land on
the wrong side.

Which of the two mistakes is worse depends on the job. For reinforcement
learning a false success
is worse, because the policy is rewarded for failing, and it will learn to fail in
exactly that way. For deciding when a task is done a false success is also worse,
because the robot moves on and hides the mistake, whereas a missed success mostly
costs time. So people usually pick a cut-off towards the high end. But a very
high cut-off, such as
0.9 here, throws away most real successes, and then the policy is rarely rewarded at
all.

---

## 6. Where it is used on a robot arm

The two examples above scored single attempts, and this section shows the four
places where that scoring is used.

**Reinforcement learning on a real arm.** In a simulator the reward is a line of
code, but on a real arm there is no such line. So a success classifier or a progress
estimator provides the reward instead, and this is how HIL-SERL learns on real
hardware.
The person collects pictures of success and failure before practice starts, and a
classifier is trained on them. Then the policy practises, and the classifier scores
each attempt. π\*0.6, described in the
[foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md),
goes one step further. It trains a network that scores how good each moment is, and
it uses the change in that score to tell which actions helped.

**Deciding when a task is done.** A robot has to know when to stop and start the next
step, so a judge answers "Is the mug in the bowl yet?". The
[vision-language models page](../../07_language-models/02_most-used/02_vision-language-models.md)
calls this success detection and shows a worked example of it.

**Filtering bad demonstrations.** Recorded demonstrations are the training data for
[behaviour cloning](../02_most-used/01_behaviour-cloning.md), but some recordings are
poor, because the person fumbled, or gave up, or the task was not finished. So a
progress estimator can score every recording, and the poor ones can be dropped
before
training.

![24 demonstrations as bars of their final progress score; 19 above the line are kept, 5 are dropped](../../../images/movement-models/reward-and-progress-models/filtering-demonstrations.svg)

The picture shows 24 made-up demonstrations, scored by the progress method of
section 4. The script that draws it applies two rules, which are that the last
score must be above 0.9, and that the score must never fall back by more than
0.25 on the way. Three recordings stopped halfway and fail the first rule, while
two finished but dropped the mug on the way and fail the second rule, so that
leaves 19 of 24. The second rule matters, because those two recordings end well,
and a check of only the last frame would have kept them.

**Evaluating policies.** To compare two policies, you run each many times and count
successes, but a person watching every run is slow and expensive, so a judge can
count instead. AutoEval, described in the
[evaluation section of the frontier documents](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation),
does this with automatic success detection on real arms, so that tests can run day
and night.

---

## 7. Well-known models and libraries

Section 6 described the four jobs a judge does, and this section names the judges
themselves. Most of the published work in this area is research code, so each
model below says plainly whether you can run it today, and the first one is the
one most people should start with.

Read the table one row at a time. The size column says what you have to download
or train, because that matters more here than a parameter count. A cell that says
`not stated` means the project does not publish the figure, and every licence was
read from the project's own licence file or model card.

| Judge | What it is best at | Size | Licence | Pick it when |
| --- | --- | --- | --- | --- |
| The HIL-SERL reward classifier, in LeRobot | one task, on your own arm, with a fast answer | you train it; it starts from a ResNet-10 encoder | Apache-2.0, as part of LeRobot | you are training with reinforcement learning on a real arm |
| Robometer, in LeRobot | progress and success on a task it has never seen | 8.9 GB checkpoint, on a 4-billion-parameter backbone | Apache-2.0, on its model card | you want a score without collecting or marking anything |
| TOPReward, in LeRobot | the same, with no reward model to download at all | no weights of its own; it uses an 8-billion-parameter vision-language model | Apache-2.0, as part of LeRobot | you already run a vision-language model and want a score from it |
| SARM, in LeRobot | long tasks made of several steps | you train it; it starts from CLIP ViT-B/32 features | Apache-2.0, as part of LeRobot | one attempt passes through stages you can name |
| VIP, and LIV after it | progress from videos of people, which is where the idea started | not stated | VIP is Creative Commons Attribution-NonCommercial 4.0; LIV is MIT | you are reading the research rather than shipping |
| GAIL, in the `imitation` library | a reward learned from recorded movements | you train it | MIT | you are comparing inverse reinforcement learning for yourself |

### 7.1 The HIL-SERL reward classifier, which you train on your own pictures

This is the judge **most used in 2026** for work on a real arm, because it is
small, it is fast enough to answer at every step, and you know exactly what is in
its training data.

HIL-SERL is the real-arm learning system from the University of California,
Berkeley, published in 2024, and its reward is a small image classifier rather
than a written rule. The classifier ships inside
[LeRobot](https://github.com/huggingface/lerobot), Hugging Face's robot learning
library, which is Apache-2.0. It is a classifier head on top of a pretrained
picture encoder, and the encoder the configuration names by default is a
ResNet-10, which is a small network already trained on ordinary photographs.

Why pick it rather than Robometer or a vision-language model, which need no
training at all? Because of speed first: a large model takes from a fraction of a
second to a few seconds for one answer, which is far too slow for a reward at
every control step, and this classifier keeps up. Because it judges your task, in
your room, under your light, rather than a general idea of success. And because
you can see every picture it learned from, so when it is wrong you know where to
look. The reason not to pick it is that it knows one task and nothing else.

What it costs you is the recordings. You collect pictures of your own attempts
and mark each one as a success or a failure, and the failures are the part people
forget. A classifier trained only on successes has nothing to contrast them with,
and one trained on failures that all fail the same way learns only that way, so
you have to make the arm fail in several different ways on purpose. The thing
that most often goes wrong afterwards is the cut-off, which section 5 was a whole
worked example about.

The library is LeRobot. Training runs from a configuration file, as
[its HIL-SERL guide](https://huggingface.co/docs/lerobot/hilserl) describes, and
the command is one line.

```bash
# the configuration names the dataset you recorded, the encoder to start from,
# your camera keys and the number of training steps
lerobot-train --config_path path/to/reward_classifier_train_config.json
```

Using the trained classifier is a few lines of Python.

```python
from lerobot.rewards import RewardClassifierConfig, make_reward_model

config = RewardClassifierConfig(
    pretrained_path="your-name/mug-in-bowl-reward",  # the classifier you trained
    num_cameras=2,
    device="cuda",
)
reward_model = make_reward_model(config)

# batch holds one or more camera images under keys that start with
# "observation.image"; the threshold is the cut-off from section 5
reward = reward_model.predict_reward(batch, threshold=0.7)
```

What LeRobot supplies is the encoder download, the rescaling of the pictures, a
set of optimiser settings that work, and the accuracy printed beside the loss
during training, which is the number you actually watch. What you supply is the
marked recordings, the camera keys, and the threshold. Note that
`compute_reward` uses a fixed cut-off of 0.5, so if you want a different one, as
section 5 argues you often should, call `predict_reward` with your own
`threshold`.

### 7.2 Robometer, a reward model you download rather than train

This one is **worth betting on**, because it is the first general-purpose reward
model that arrives as an ordinary download, and a general success detector is the
missing piece in every scheme that practises without a person watching.

Robometer is a video-and-language reward model from the paper
[Robometer: Scaling General-Purpose Robotic Reward Models via Trajectory
Comparisons](https://arxiv.org/abs/2603.02115), and it became downloadable in
LeRobot version 0.6.0 on 6 July 2026. You give it frames from an attempt and the
written instruction for the task, and it predicts how far along each frame is and
how likely that frame is to be a success. It is a Qwen3-VL-4B-Instruct
vision-language model with three small heads added, which
[its LeRobot page](https://huggingface.co/docs/lerobot/robometer) describes.

Why pick it rather than the classifier in section 7.1? Because you collect and
mark nothing. It scores a task it was not trained on, which is exactly what the
classifier cannot do, so it suits sorting a pile of recordings or scoring an
evaluation that runs overnight. Why not pick it? Because nobody has yet published
how often it agrees with a careful person on a task it was not trained for, which
the repository's
[frontier document](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation)
states, and because a model judging a model is a mistake with a long history.

What it costs you is a graphics card and patience. The published checkpoint,
[lerobot/Robometer-4B](https://huggingface.co/lerobot/Robometer-4B), is a single
file of about 8.9 GB, licensed Apache-2.0 on its model card. Its LeRobot page
says a graphics card is strongly recommended, and the integration is
inference-only, so you cannot train it further there. By default it reads at most
eight frames of an attempt, which is a detail worth knowing, because eight frames
of a one-minute attempt can miss the moment things went wrong.

The library is LeRobot again.

```python
from lerobot.rewards.robometer import RobometerConfig, RobometerRewardModel

cfg = RobometerConfig(
    pretrained_path="lerobot/Robometer-4B",
    device="cuda",
    reward_output="progress",   # or "success" for a 0 or 1 answer
)
reward_model = RobometerRewardModel.from_pretrained(cfg.pretrained_path, config=cfg)
```

What LeRobot supplies is the download, the frame and text preparation for the
Qwen backbone, and one `compute_reward` call that returns the last frame's
progress clamped between 0 and 1. What you supply is the frames, as whole numbers
in an array shaped time by height by width by colour, and the task instruction as
a sentence. The instruction is not a formality: it is the only thing telling the
model what success means, so "put the red mug in the bowl" and "tidy the table"
will be scored differently.

### 7.3 TOPReward, which asks a vision-language model how likely success is

This one is also **worth betting on**, for a different reason: it needs no reward
model at all, so it improves whenever the vision-language model you already use
improves.

TOPReward comes from the paper
[TOPReward: Token Probabilities as Hidden Zero-Shot Rewards for
Robotics](https://arxiv.org/abs/2602.19313) and ships in LeRobot. It builds a
prompt that shows the video, states that the robot completed the task, and ends
with "The answer is: True". Then it reads how likely the model thought that last
word was. That likelihood is the reward. Nothing is fine-tuned, which is what
**zero-shot** means: the model is used as it comes.

The idea has a history, and these are the papers people cite for it. VLM-RMs,
from [Vision-Language Models are Zero-Shot Reward Models for Reinforcement
Learning](https://arxiv.org/abs/2310.12921), showed in 2023 that CLIP, a model
that scores how well a picture matches a sentence, works as a reward with no
training for simple tasks in simulation. RoboCLIP scored a whole attempt against
one demonstration video. SuccessVQA fine-tuned a vision-language model on marked
examples of the question. Generative Value Learning asked a large model to rate
every frame, shuffling the frames first so that it could not simply assume later
frames are further along. TOPReward is the same family, and it is the packaged
one.

Why pick it rather than Robometer? Because there is no checkpoint to download and
nothing to keep up to date, and because you can swap the backing model for a
better one later. Why pick Robometer instead? Because its heads were trained on
robot videos for this exact job, where TOPReward borrows a general model's
opinion. Which of the two is more accurate on your task is something you have to
measure, and neither paper settles it for you.

What it costs you is the vision-language model. The default backbone is
Qwen3-VL-8B-Instruct, which is larger than Robometer's, so this is not the cheap
option even though nothing is trained, and the LeRobot port supports the Qwen
backbone only. The answer is also a log-probability rather than a score from 0 to
1, which is useful for ranking attempts and awkward as an absolute cut-off.

```python
from lerobot.rewards.topreward import TOPRewardConfig, TOPRewardModel

cfg = TOPRewardConfig(
    vlm_name="Qwen/Qwen3-VL-8B-Instruct",   # any model you can run locally
    device="cuda",
)
reward_model = TOPRewardModel(cfg)
```

What LeRobot supplies is the prompt building, the masking that isolates the last
word, and the reading of its probability, which is the whole trick and is fiddly
to write yourself. What you supply is a machine that can hold the model, the
frames, and the instruction. There is also a script that labels a whole dataset
offline and writes the scores to a file, which is the sensible way to use a slow
judge.

### 7.4 SARM, which judges a long task one stage at a time

This one is **worth betting on** for long tasks, because a single progress number
for a task with four steps in it is a weak signal, and this is the packaged model
that fixes that.

SARM, which stands for stage-aware reward modelling, comes from the paper
[SARM: Stage-Aware Reward Modeling for Long Horizon Robot
Manipulation](https://arxiv.org/abs/2509.25358), and it ships in LeRobot. It
predicts which stage of the task the arm is in and how far through that stage it
is, and combines the two into one progress score between 0 and 1. You name the
stages in words, such as grabbing the near side of a towel and making the first
fold.

Why pick it rather than Robometer, which also gives progress? Because Robometer
scores the whole task, so a long attempt that finished three of four steps and
then stopped looks much the same as one that drifted. SARM knows the steps are
there, and because it normalises each stage by how long that stage usually takes,
the same point in two recordings of different lengths gets the same score. Why
not pick it? Because it has no published general checkpoint to download: you
train it on your own dataset, which is the cost section 7.1 described all over
again.

What it costs you is annotation. You name the stages, and a vision-language model
then marks where each stage starts and ends in each recording, which is a model
call for every episode. There is a `single_stage` mode that needs no annotation
at all and treats progress as a straight line from the start to the end of the
episode, and that mode is the honest starting point, because it tells you whether
stages are worth the work.

```bash
# mark the stages in each episode, using a vision-language model
python src/lerobot/data_processing/sarm_annotations/subtask_annotation.py \
  --repo-id your-name/towel-folding \
  --dense-only \
  --dense-subtasks "Lift the arms,First fold,Second fold,Third fold" \
  --video-key observation.images.base

# then train the judge on those stages
lerobot-train --dataset.repo_id=your-name/towel-folding \
  --policy.type=sarm --policy.annotation_mode=dense_only \
  --policy.image_key=observation.images.base --steps=5000
```

What LeRobot supplies is the annotation script, the stage arithmetic, the
training, and a way to use the score to weight imitation learning, so that frames
where the arm was making real progress count for more. What you supply is the
list of stages and the judgement of whether your task really has any. A task that
is one continuous motion does not.

### 7.5 VIP and LIV, where the progress estimator came from

These are **historical**. They are where the method in section 4 comes from, and
they are research repositories rather than packages.

VIP, short for Value-Implicit Pre-training, came from the University of
Pennsylvania and Meta in 2022 and was published at the 2023 International
Conference on Learning Representations. It learns from videos of people doing
everyday tasks to turn a picture into an embedding, and the distance to the goal
embedding then works as a progress score, which is the arithmetic section 4
worked through. LIV, short for Language-Image Value learning, came from the same
group in 2023 and lets the goal be a sentence instead of a picture.

Why read these rather than use Robometer? Because they explain what every progress
estimator is doing, and because VIP gives you the embedding itself, which is
useful for other things, such as finding the nearest frame in a dataset. Why not
use them in a product? Because
[VIP's repository](https://github.com/facebookresearch/vip) is licensed Creative
Commons Attribution-NonCommercial 4.0, read from its licence file, which rules
out commercial use. [LIV's repository](https://github.com/penn-pal-lab/LIV) is
MIT and was last changed in 2023.

What it costs you is the fitting together, because there is no reward model in
these repositories, only the encoder. You write the distance and the progress
arithmetic yourself, which is five lines, and you decide what the goal picture
is.

```python
import torch
from vip import load_vip

vip = load_vip()   # the model pretrained on Ego4D, a large set of videos of people
vip.eval()

# images are 224 by 224 and the model expects values from 0 to 255
with torch.no_grad():
    embedding = vip(preprocessed_image * 255.0)   # shape [1, 1024]
```

What the library supplies is that encoder, and its README also points at a
ready-made version inside TorchRL. What you supply is the preprocessing, which
the repository's `encoder_example.py` shows as a resize to 256, a centre crop to
224 and a scaling back to the range 0 to 255, and then the whole of the reward:
the goal embedding, the distance, and the step-to-step difference.

### 7.6 GAIL and the `imitation` library, for a reward learned from movements

This one is **historical** too, and it is the fourth kind of judge from section 3,
kept because the idea keeps coming back.

Generative adversarial imitation learning, written GAIL, is from 2016. It trains
a judge whose job is to tell the person's recorded movements apart from the
policy's, and the policy is rewarded for being hard to tell apart. Maximum
entropy inverse reinforcement learning, from 2008, is the older classic in the
same family, and open versions of both are in
[the `imitation` library](https://github.com/HumanCompatibleAI/imitation), which
is MIT.

Why pick this rather than a classifier or a progress model? Only when the thing
you cannot write down is the goal itself rather than the finish line, and you
believe a learned reward carries over to new situations better than copied
movements do. Why not? Because the library's last change was in January 2025, as
the repository's
[learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#13-learning-the-goal-instead-of-the-motion)
notes, and because two models now train against each other, so when the result is
bad it is hard to say which one was at fault.

What it costs you is a simulator, because the library is built around Gymnasium
environments rather than real arms. It is the right place to try inverse
reinforcement learning and the wrong place to run a reward in production, and its
own documentation is a better guide than anything shortened here, because the
training loop has several parts.

### 7.7 How to choose

Train the HIL-SERL classifier on your own pictures. That is the default for one
task on one real arm, and it is the only judge here whose training data you can
look at.

Four things change that answer.

If you have nothing marked and want a score tonight, download Robometer, and read
its answers against your own eyes on a handful of attempts before you trust it on
hundreds. If you already run a large vision-language model, TOPReward gets the
same kind of answer out of it without a second model.

If the task has named steps and you care where an attempt stopped, use SARM, and
start in its `single_stage` mode so that you find out whether the stages were
worth annotating.

If the reward is needed many times a second during learning, none of the large
models will do, and you are back to the small classifier. Section 8 explains why.

If a sensor or a measurement can answer "is it done?", use that instead of
everything on this page. Section 10 shows how to write one, and a rule you can
read is worth more than a model you cannot.

One more case sits beside all of these. If you work in a simulator, where the
program knows where every object is, then Eureka, from NVIDIA in 2023, has a
large language model write the reward as code and improve it from the training
results. It judges no pictures, and the reward it writes is a rule you can read,
so it belongs with the written alternatives rather than with the judges.

---

## 8. What goes wrong, and what people do about it

Section 7 listed the tools, and this section lists what they get wrong. Each
problem is followed by what people do about it.

**The policy learns to fool the judge.** This is **reward hacking**, which the
[reinforcement learning page](01_reinforcement-learning-policies.md#7-what-goes-wrong-and-what-people-do-about-it)
describes for written rules. But a learned judge makes it more likely rather than
less. A written rule is wrong in a way you can read, whereas a learned judge is
wrong
in ways you cannot see until the policy finds them. For example, a policy trained
against a success classifier may learn to hold the mug in front of the camera in a
place that looks like the bowl. The sign is a policy whose judged success keeps
rising
while a person watching sees it fail. So people fix this by adding the fooling
pictures to the classifier's training set as failures, and then training it again.
They also keep a person checking a sample of the runs.

**False success from one camera.** The judge sees only what the camera sees, so from
above, a mug held just over the bowl can look the same as a mug in the bowl.

![Side view: the mug is still held above the bowl. Top view: the mug appears inside the bowl, and the classifier says success](../../../images/movement-models/reward-and-progress-models/false-success-one-camera.svg)

The left picture shows what really happened, because the gripper has not let go,
and there is a gap under the mug. The right picture shows the only thing the top
camera can see. The classifier's answer, "success" with a score of 0.93, is an
example and not a measurement. So people fix this by judging from two cameras,
by asking the opposite question as well ("is the gripper still holding
something?"), and by checking with a sensor such as how far the gripper has
closed.

**The judge does not carry over to a new place.** A classifier trained in one room,
with one table and one light, can fail in another room. The sign is a success rate
that changes when nothing about the policy changed, so people collect a few judge
examples in every new place.

**Progress that is not smooth.** A progress estimator trained on videos of people may
score a robot's frames unevenly. For example, it may jump when the arm enters the
picture, or drop when the arm hides the object. The policy then learns from
those jumps, so
people smooth the scores over time, or fine-tune the estimator on a few robot
videos.

**A slow judge.** A large vision-language model takes from a fraction of a second to
a few seconds per answer. That is fine at the end of an attempt, but it is far too
slow to give a reward many times a second during learning.

---

## 9. Why this kind, and what it costs

Section 8 listed the faults, so this section asks when a judge is worth them. A
judge model is a model that tells you whether the task is done, or how far along
it is. So what it does for you is replace a check that a person would otherwise
make by eye, on every single attempt.

The obvious alternative is a written rule on a measurement. You can weigh the
bowl on a scale, or mark the mug with a tag that the camera finds exactly, or
check how far the gripper closed. These rules are fast, cheap and easy to check,
so when such a rule exists, use it. A judge model is worth it only when no
measurement answers the question, as with "Is the towel folded neatly?", "Is the
cable seated?", or any task where the only evidence is how the scene looks.

The second alternative is a person, and a person watching is the most reliable
judge of all. But a person cannot score thousands of practice attempts, or watch
a test that runs all night. So a judge model is worth it when the number of
attempts is too large for people.

What it costs you most of all is trust. You now have two models that can be
wrong, which are the policy and the judge. So when the judged success rate is
high, you do not know which one to believe until a person checks. It also costs
the work of collecting marked examples, at least for a success classifier. And a
policy trained against a judge learns whatever the judge rewards, which is not
always what you meant.

The table below sums up the usual choice for each case. Read each row as a
situation, and the right column as what people usually use.

| Situation | Usual choice |
| --- | --- |
| A sensor or a simple measurement answers "is it done?" | a written rule, not a model |
| One task, on one real arm, for reinforcement learning | a success classifier trained on your own pictures |
| Many long recordings to sort, or a reward at every step | a progress estimator |
| Many different tasks, answer needed only at the end | a vision-language model as the judge, backed by a second check |
| You want the reward to carry over to new situations | inverse reinforcement learning, knowing it is fragile |

---

## 10. The written alternative

The first row of the table above was a written rule, and this section says how to
build one. Book 5 covers the three parts of that job. [Sensor
streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#thresholds-that-do-not-flicker-hysteresis-and-debouncing)
turns a reading, such as how far the gripper closed or the weight on a scale, into a
clean yes-or-no flag. [Thresholding and colour
masks](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
checks a picture for a known colour in a known place. And [pose from
points](../../../06_programming-techniques/02_geometry-and-cameras/02_most-used/04_pose-from-points.md)
measures where an object with a printed marker is.

So the written rule is better whenever a measurement like these answers "is it
done?", because it is fast and easy to check. A judge model is better only when
the answer can only be seen, such as whether a towel is folded neatly.

---

## 11. Where to read next

This page supplied the score that the earlier methods needed, and the next page
supplies the data they needed, so the reading below follows that thread.

In this chapter:

- [Reinforcement learning policies](01_reinforcement-learning-policies.md) is the
  learner that most often uses a judge model as its reward.
- [Learning from human video](04_learning-from-human-video.md) is the next page, and
  the progress estimators on this page are trained on the same kind of video.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Vision-language models](../../07_language-models/02_most-used/02_vision-language-models.md)
  explains the large models used as judges, with a worked example of success
  detection.
- [Collision and failure detection](../../09_touch-and-body-models/02_most-used/02_collision-and-failure-detection.md)
  covers judges that use force and joint signals instead of pictures.

Deeper documents elsewhere in this repository:

- [What is being done about evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation)
  covers AutoEval, `lerobot-eval` and the Robometer reward model.
- [LeRobot's 2026 releases](../../../03_frameworks/08_frontier/06_what-is-coming.md#23-lerobot-which-now-releases-on-a-predictable-rhythm)
  explains why reward models arriving as downloads matters.
- [Interactive imitation](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#12-interactive-imitation-correcting-it-as-it-goes)
  gives the evidence for HIL-SERL.
