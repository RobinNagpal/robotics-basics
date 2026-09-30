# Reward and progress models

This page answers one question. How can a robot tell, by itself, whether an attempt
at a task went well? The models that do this job look at the camera pictures of an
attempt and give back a judgement. Some say "success" or "failure". Some say how far
along the task is. Some are large models that answer a question in words. This page
calls all of them **judge models**.

The page is for a reader who has read
[reinforcement learning policies](01_reinforcement-learning-policies.md). That page
needs a **reward**, which is a number that says how well an attempt went. It assumes
someone can write a rule for that number. This page is about what to do when nobody
can write the rule, because the only way to tell is to look. Every new word is
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
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

Here is the one-sentence idea. A judge model is a network that looks at what the
camera saw during an attempt, and gives back a number that says how well the
attempt is going.

An everyday example helps. Think of a cooking teacher and a student. The student
cooks. The teacher does not cook at all. The teacher only tastes, and says "good",
"not yet" or "nearly there". The student gets better from those words. A judge model
is the teacher. The movement model, which this chapter calls the **policy**, is the
student.

Why would you need a network for this? For some tasks a short rule is enough. In a
simulator, the program knows exactly where every object is. "The peg is in the hole"
is one line of code there. On a real arm, nobody tells the program where the peg is.
There is only a camera picture. "Is the towel folded neatly?" or "Is the mug in the
bowl?" have no simple rule on a picture. So people train a network to answer the
question instead.

---

## 2. What goes in and what comes out

A judge model takes in pictures from the robot's cameras. It can take one picture,
such as the last one of an attempt. It can take the whole video of the attempt. Some
judges also take a **goal**: a picture of the finished task, or a sentence such as
"put the mug in the bowl".

It gives back a number. What the number means depends on the kind of judge. The
table below shows the three common kinds of answer. Read each row as one kind of
answer and an example of it.

| What comes out | What it means | An example |
| --- | --- | --- |
| a success score from 0 to 1 | how sure the judge is that the task is done | 0.93: "almost certainly done" |
| a progress score for each frame | how far along the task is, from 0 (start) to 1 (done) | 0.50 halfway through a fold |
| an answer in words | a yes or no, or a short explanation | "No, the mug is still in the gripper." |

The judge does not move the arm. It is used beside the policy, to score it, to stop
it, or to train it.

---

## 3. The four kinds of judge

People use four kinds of judge model on arms. They differ in what they are trained
on and in how much work they need before they can be used.

**A success classifier.** A **classifier** is a model that puts an input into one of
a few groups. Here the groups are "success" and "failure". You train it on
pictures of your own task, each marked by a person as success or failure.
It then gives a score from 0 to 1 for any new picture. It is small and fast. It only
knows your one task. HIL-SERL, the real-arm learning system in the
[reinforcement learning page](01_reinforcement-learning-policies.md#5-well-known-models-and-methods),
uses one of these as its reward.

**A progress estimator.** This gives a score for every frame of the video, not just
the last one. The score rises as the task gets closer to done. The best-known ones
are trained on large amounts of video of people doing everyday tasks. They turn each
picture into a short list of numbers, called an **embedding**. An embedding is made
so that similar pictures get similar lists. The progress is then read from how close
the current embedding is to the embedding of the goal picture. Section 4 works
through this with real numbers.

**A vision-language model used as the judge.** A
[vision-language model](../../06_language-models/02_most-used/02_vision-language-models.md)
is a large model that takes pictures and a question in words, and answers in words.
You ask it "Is the red mug in the bowl?" and it answers. You can also ask it to rate
progress. It needs no training on your task. It is slow, and it can be wrong in ways
that are hard to predict.

**A reward learned from demonstrations.** This is called **inverse reinforcement
learning**. Normal reinforcement learning starts from a reward and learns a movement.
Inverse reinforcement learning goes the other way. It starts from recorded
movements by a person, and learns a reward that would explain why the person moved
that way. The idea is that the reward carries over to new situations better than the
copied movement does. It is rarely used on real arms today. The
[learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#13-learning-the-goal-instead-of-the-motion)
explains why.

---

## 4. A worked example: scoring progress from pictures

This example shows how a progress estimator turns pictures into a score. The
numbers are small and made up so that you can follow them by hand. The arithmetic
was run in Python, and the results below are copied from that run.

A real estimator turns each picture into an embedding of hundreds of numbers. Here
each picture becomes only three numbers. The task is to put a mug in a bowl. The
camera sees six frames. The last one is the goal.

1. **Turn the goal picture into numbers.** The goal embedding is (0.9, 0.1, 0.8).
2. **Turn each frame into numbers.** Frame 0, at the start, is (0.1, 0.7, 0.2).
   Frame 1 is (0.3, 0.6, 0.3), and so on until frame 5, which equals the goal.
3. **Measure how far each frame is from the goal.** The distance is the ordinary
   straight-line distance between two points. For frame 0 the differences are -0.8,
   0.6 and -0.6. Square them, add them and take the square root: the square root of
   1.36, which is 1.166. The six distances are 1.166, 0.927, 0.583, 0.520, 0.173 and 0.
4. **Turn distance into progress.** Progress is 1 minus the current distance divided
   by the starting distance. Frame 0 gives 1 − 1.166 / 1.166 = 0. Frame 1 gives
   1 − 0.927 / 1.166 = 0.205. The six progress scores are 0, 0.205, 0.500, 0.554,
   0.851 and 1.000.
5. **Turn progress into a reward.** The reward for each step is the progress after
   the step minus the progress before it. The five rewards are 0.205, 0.295, 0.054,
   0.297 and 0.149. They add up to exactly 1, the whole distance from start to goal.

Step 5 is how VIP, one of the best-known progress estimators, is used as a reward
for reinforcement learning. A step that moves towards the goal earns a positive
reward. A step that moves away earns a negative one. The small reward from frame 2 to
frame 3 means that step did little.

![Left: bars for the six progress scores of the worked example, with the step rewards below. Right: three whole attempts scored frame by frame](../../../images/movement-models/reward-and-progress-models/progress-along-an-attempt.svg)

The left picture shows the six scores from the example, with the step rewards in
orange underneath. The right picture shows why a score for every frame is useful. It
shows three made-up attempts. The green one rises steadily and crosses the line
where the task counts as done. The grey one gets stuck halfway. The red one gets
close, then falls sharply when the mug slips, and then climbs again. A judge that
only looked at the last frame would call the red attempt a success. It would never
notice that it went wrong on the way.

---

## 5. A second worked example: where to put the cut-off

A success classifier gives a score, not a yes or no. You have to choose a
**cut-off**: the score above which you count the attempt as a success. This choice
matters more than it seems.

This example uses made-up scores for 100 attempts that really succeeded and 100
that really failed. They were drawn at random in Python with a fixed seed. The
counts below come from that run. There are two kinds of mistake:

- A **false success** is a failed attempt that the judge calls a success.
- A **missed success** is a real success that the judge calls a failure.

The table shows what three cut-offs give. Read each row as one choice of cut-off,
and the two numbers as the mistakes it makes out of 100 of each kind.

| Cut-off | False successes (of 100 failures) | Missed successes (of 100 successes) |
| --- | --- | --- |
| 0.5 | 10 | 7 |
| 0.7 | 2 | 21 |
| 0.9 | 0 | 69 |

![Histograms of classifier scores for real failures and real successes, with dashed lines at 0.5, 0.7 and 0.9](../../../images/movement-models/reward-and-progress-models/choosing-the-threshold.svg)

The picture shows the same scores as two piles. Red is the failures, which mostly
score low. Green is the successes, which mostly score high. The piles overlap in the
middle. Wherever you put the line, some attempts land on the wrong side.

Which mistake is worse depends on the job. For reinforcement learning, a false
success is worse. The policy is rewarded for failing, and it will learn to fail in
exactly that way. For deciding when a task is done, a false success is also worse,
because the robot moves on and hides the mistake. A missed success mostly costs
time. So people usually pick a high cut-off. But a very high cut-off, such as 0.9
here, throws away most real successes, and then the policy is rarely rewarded at all.

---

## 6. Where it is used on a robot arm

Judge models appear in four places.

**Reinforcement learning on a real arm.** In a simulator the reward is a line of
code. On a real arm there is no such line. A success classifier or a progress
estimator provides the reward instead. This is how HIL-SERL learns on real hardware.
The person collects pictures of success and failure before practice starts. A
classifier is trained on them. Then the policy practises, and the classifier scores
each attempt. π\*0.6, described in the
[foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md),
goes one step further. It trains a network that scores how good each moment is, and
uses the change in that score to tell which actions helped.

**Deciding when a task is done.** A robot has to know when to stop and start the
next step. A judge answers "Is the mug in the bowl yet?". The
[vision-language models page](../../06_language-models/02_most-used/02_vision-language-models.md)
calls this success detection and shows a worked example of it.

**Filtering bad demonstrations.** Recorded demonstrations are the training data for
[behaviour cloning](../02_most-used/01_behaviour-cloning.md). Some recordings are
poor. The person fumbled, or gave up, or the task was not finished. A progress
estimator can score every recording, and the poor ones can be dropped before
training.

![24 demonstrations as bars of their final progress score; 19 above the line are kept, 5 are dropped](../../../images/movement-models/reward-and-progress-models/filtering-demonstrations.svg)

The picture shows 24 made-up demonstrations, scored by the progress method of
section 4. The script that draws it applies two rules. The last score must be above
0.9, and the score must never fall back by more than 0.25 on the way. Three
recordings stopped halfway and fail the first rule. Two finished, but dropped the
mug on the way and fail the second rule. That leaves 19 of 24. The second rule
matters. Those two recordings end well, and a check of only the last frame would
have kept them.

**Evaluating policies.** To compare two policies, you run each many times and count
successes. A person watching every run is slow and expensive. A judge can count
instead. AutoEval, described in the
[evaluation section of the frontier documents](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation),
does this with automatic success detection on real arms, so that tests can run day
and night.

---

## 7. Well-known models and libraries

These are real models and tools, grouped by the kind of judge from section 3.

Success classifiers:

- **HIL-SERL** (University of California, Berkeley, 2024). A system for learning on
  a real arm. Its reward is a small image classifier trained on the person's own
  success and failure pictures. It ships inside
  [LeRobot](https://github.com/huggingface/lerobot), Hugging Face's robot learning
  library, and LeRobot's HIL-SERL guide covers training the classifier.
- **SuccessVQA** (Du and colleagues, 2023). It turns "did the task succeed?" into a
  question a vision-language model answers about a video, and fine-tunes the model
  on marked examples. The
  [collision and failure detection page](../../08_touch-and-body-models/02_most-used/02_collision-and-failure-detection.md#5-well-known-methods-and-models)
  also lists it.

Progress estimators:

- **VIP**, Value-Implicit Pre-training (Ma and colleagues, University of Pennsylvania
  and Meta, 2022). It learns embeddings from videos of people doing everyday tasks,
  so that distance to the goal embedding works as a progress score. Section 4 used
  its method.
- **LIV**, Language-Image Value learning (Ma and colleagues, 2023). It extends the
  VIP idea so that the goal can be a sentence as well as a picture.
- **Robometer** (2026). A pretrained reward model that scores progress and success
  from a video and a written instruction. It became downloadable in LeRobot 0.6.0.
  The
  [frontier document](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation)
  notes that nobody has yet shown how often it agrees with a careful person on a
  task it was not trained for.

Vision-language models as judges:

- **VLM-RMs** (Rocamonde and colleagues, 2023). They showed that CLIP, a model that
  scores how well a picture matches a sentence, can serve as a reward with no extra
  training, for simple tasks in simulation.
- **RoboCLIP** (Sontakke and colleagues, 2023). It scores a whole attempt by how
  closely its video matches one demonstration video or one sentence.
- **Generative Value Learning, or GVL** (Google DeepMind, 2024). It asks a large
  vision-language model to guess the progress of every frame of a video. It shuffles
  the frames first, so that the model cannot just guess that later frames are
  further along.
- **Eureka** (NVIDIA, 2023) is a relative. It does not judge pictures. A large
  language model writes the reward as code for a simulator, then improves the code
  from the training results.

Rewards learned from demonstrations:

- **Maximum entropy inverse reinforcement learning** (Ziebart and colleagues, 2008)
  is the classic method.
- **GAIL**, generative adversarial imitation learning (Ho and Ermon, 2016), trains a
  judge that tells the person's movements from the policy's, and uses it as the
  reward.
- The [imitation](https://github.com/HumanCompatibleAI/imitation) library holds
  open versions of these. The
  [learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#13-learning-the-goal-instead-of-the-motion)
  notes that it has had no new work since January 2025.

---

## 8. What goes wrong, and what people do about it

**The policy learns to fool the judge.** This is **reward hacking**, which the
[reinforcement learning page](01_reinforcement-learning-policies.md#7-what-goes-wrong-and-what-people-do-about-it)
describes for written rules. A learned judge makes it more likely, not less. A
written rule is wrong in a way you can read. A learned judge is wrong in ways you
cannot see until the policy finds them. A policy trained against a success
classifier may learn to hold the mug in front of the camera in a place that looks
like the bowl. The sign is a policy whose judged success keeps rising while a person
watching sees it fail. People fix this by adding the fooling pictures to the
classifier's training set as failures and training it again. They also keep a person
checking a sample of the runs.

**False success from one camera.** The judge sees only what the camera sees. From
above, a mug held just over the bowl can look the same as a mug in the bowl.

![Side view: the mug is still held above the bowl. Top view: the mug appears inside the bowl, and the classifier says success](../../../images/movement-models/reward-and-progress-models/false-success-one-camera.svg)

The left picture shows what really happened. The gripper has not let go, and there
is a gap under the mug. The right picture shows the only thing the top camera can
see. The classifier's answer, "success" with a score of 0.93, is an example, not a
measurement. People fix this by judging from two cameras, by asking the opposite
question as well ("is the gripper still holding something?"), and by checking with a
sensor such as how far the gripper has closed.

**The judge does not carry over to a new place.** A classifier trained in one room,
with one table and one light, can fail in another room. The sign is a success rate
that changes when nothing about the policy changed. People collect a few judge
examples in every new place.

**Progress that is not smooth.** A progress estimator trained on videos of people
may score a robot's frames unevenly. It may jump when the arm enters the picture, or
drop when the arm hides the object. The policy then learns from those jumps. People
smooth the scores over time, or fine-tune the estimator on a few robot videos.

**A slow judge.** A large vision-language model takes from a fraction of a second to
a few seconds per answer. That is fine at the end of an attempt. It is far too slow
to give a reward many times a second during learning.

---

## 9. Why this kind, and what it costs

A judge model is a model that tells you whether the task is done or how far along it
is. What it does for you is replace a check that a person would otherwise make by
eye, on every attempt.

The obvious alternative is a written rule on a measurement. You can weigh the bowl
on a scale. You can mark the mug with a tag that the camera finds exactly. You can
check how far the gripper closed. These rules are fast, cheap and easy to check. When
such a rule exists, use it. A judge model is worth it when no measurement answers
the question: "Is the towel folded neatly?", "Is the cable seated?", or any task
where the only evidence is how the scene looks.

The second alternative is a person. A person watching is the most reliable judge.
But a person cannot score thousands of practice attempts, or watch a test that runs
all night. A judge model is worth it when the number of attempts is too large for
people.

What it costs you is trust. You now have two models that can be wrong: the policy
and the judge. When the judged success rate is high, you do not know which one to
believe until a person checks. It also costs the work of collecting marked examples,
at least for a success classifier. And a policy trained against a judge learns
whatever the judge rewards, which is not always what you meant.

The table below sums up the usual choice. Read each row as a situation, and the
right column as what people usually use.

| Situation | Usual choice |
| --- | --- |
| A sensor or a simple measurement answers "is it done?" | a written rule, not a model |
| One task, on one real arm, for reinforcement learning | a success classifier trained on your own pictures |
| Many long recordings to sort, or a reward at every step | a progress estimator |
| Many different tasks, answer needed only at the end | a vision-language model as the judge, backed by a second check |
| You want the reward to carry over to new situations | inverse reinforcement learning, knowing it is fragile |

---

## 10. Where to read next

In this chapter:

- [Reinforcement learning policies](01_reinforcement-learning-policies.md) is the
  learner that most often uses a judge model as its reward.
- [Learning from human video](04_learning-from-human-video.md) is the next page. The
  progress estimators on this page are trained on the same kind of video.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Vision-language models](../../06_language-models/02_most-used/02_vision-language-models.md)
  explains the large models used as judges, with a worked example of success
  detection.
- [Collision and failure detection](../../08_touch-and-body-models/02_most-used/02_collision-and-failure-detection.md)
  covers judges that use force and joint signals instead of pictures.

Deeper documents elsewhere in this repository:

- [What is being done about evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#9-what-is-being-done-about-evaluation)
  covers AutoEval, `lerobot-eval` and the Robometer reward model.
- [LeRobot's 2026 releases](../../../03_frameworks/08_frontier/06_what-is-coming.md#23-lerobot-which-now-releases-on-a-predictable-rhythm)
  explains why reward models arriving as downloads matters.
- [Interactive imitation](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#12-interactive-imitation-correcting-it-as-it-goes)
  gives the evidence for HIL-SERL.
