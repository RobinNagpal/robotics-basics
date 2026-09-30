# World models

This chapter is about models that predict what will happen next if the arm does
something. This page is its overview. It says what this family of models is for,
names its four main kinds, and shows how they connect to the other models in
this book.

It is for a reader who has read the first chapter of this book,
[What models are](../01_what-models-are/01_what-a-model-is.md). You should know
that a model is a function learned from examples, and that its inputs and
outputs are lists of numbers. You do not need to know anything else about
machine learning.

## Contents

1. [What a world model is for](#1-what-a-world-model-is-for)
2. [The question it answers for a robot arm](#2-the-question-it-answers-for-a-robot-arm)
3. [The four kinds](#3-the-four-kinds)
4. [Three ways a robot uses a world model](#4-three-ways-a-robot-uses-a-world-model)
5. [How this chapter connects to the others](#5-how-this-chapter-connects-to-the-others)
6. [Why learn a world model, and what it costs](#6-why-learn-a-world-model-and-what-it-costs)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What a world model is for

Most models in this book look at the world as it is now. A seeing model looks at
a photo and says "there is a mug here". A grasp model looks at the mug and says
"hold it by the handle". Neither of them says what happens after the arm moves.

A **world model** does. It is a model that predicts what will happen next if the
arm does something. You give it two things. The first is what the world looks
like now. The second is an **action**, which is one thing the arm could do, such
as "move the gripper 10 cm to the left". The world model gives back what the
world will look like after that action.

People make the same kind of prediction all the time. Before you push a glass
across a table, you already expect it to slide and not to tip over. Before you
lift a full bag, you expect it to be heavy. You learned these expectations from
years of watching things move. A world model learns them in the same way: from
many recordings of things moving.

The word "world" here means only the small part of the world that the robot
cares about. For a robot arm, that is usually a table, the objects on it and the
arm itself.

---

## 2. The question it answers for a robot arm

Every chapter of this book answers one question for the arm. For this chapter
the question is: **"If I do this, what will happen?"**

That question matters because a robot arm can break things. It can push a mug
off a table, drop a plate or crush a box. Trying each action for real, to see
what happens, is slow and sometimes costly. A world model lets the arm try the
action in its prediction first.

The picture below shows the idea. A mug stands close to the edge of a table. The
arm could do three different things. The world model predicts the result of each
one before the arm moves.

![A world model predicts what three different actions would do to a mug near the edge of a table](../../images/world-models/overview/predict-then-choose.svg)

The model predicts that one push sends the mug off the table, so the arm does
not choose it.

This is how a world model helps with a decision. The model itself does not
decide anything. It only answers "what if?" questions. Some other part of the
robot asks the questions and picks the action with the best predicted result.

---

## 3. The four kinds

World models differ mainly in *what* they predict. Some predict a few numbers,
some predict whole camera pictures, and some predict thousands of small pieces
of cloth or water. This chapter has one page for each of the four main kinds.

The pages are in two groups. The **most used** group has one page, learned
dynamics models. They are the kind most often run on a real arm today, because
they are small, fast and easy to check. The same page also shows the most common
way to combine a physics formula with a network: keep the formula and learn only
the part it gets wrong. The **also used** group has the other three kinds. They
are used often in research and in new robot models, but less often on a working
arm, because they are slower, need more data, or suit only some materials.

1. [Learned dynamics models](02_most-used/01_learned-dynamics-models.md) predict the next
   state of the arm and the objects, written as a short list of numbers, from
   the current state and an action. Most used.
2. [Video prediction models](03_also-used/01_video-prediction-models.md) predict the next
   camera pictures, pixel by pixel. Also used.
3. [Learned simulators](03_also-used/02_learned-simulators.md) predict how cloth, liquids,
   sand and other soft or loose materials move, by following many small pieces
   of the material at once. Also used.
4. [Latent world models](03_also-used/03_latent-world-models.md) squeeze each camera picture
   into a short code and predict how that code changes. The best-known family is
   called Dreamer. Also used.

The picture below shows what each kind predicts for the same kind of scene.

![The four kinds of world model side by side, each showing what it predicts](../../images/world-models/overview/four-kinds.svg)

From left to right, the predictions get less like pictures and more like numbers,
except the learned simulator, which predicts the positions of many small pieces.

The table below compares the four kinds. Each row is one kind. Read across a row
to see which group it is in, what that kind takes in, what it gives back, and what
it is best at.

| Kind | Group | What goes in | What comes out | Best at | Main weakness |
| --- | --- | --- | --- | --- | --- |
| [Learned dynamics model](02_most-used/01_learned-dynamics-models.md) | most used | a few numbers about the arm and objects, and an action | the same numbers one step later | fast planning for pushing, reaching and holding | someone must first measure those numbers |
| [Video prediction model](03_also-used/01_video-prediction-models.md) | also used | recent camera pictures, and planned actions | future camera pictures | learning from ordinary video, showing a person what it expects | slow, and the pictures get blurry or wrong further ahead |
| [Learned simulator](03_also-used/02_learned-simulators.md) | also used | the positions of many small pieces of material | where each piece will be next | cloth, rope, dough, water and sand | needs the material to be turned into pieces first |
| [Latent world model](03_also-used/03_latent-world-models.md) | also used | a short code made from a camera picture, and an action | the next code, and a score for how well the task is going | practising many times inside the model | hard to check, because you cannot look at the code |

---

## 4. Three ways a robot uses a world model

A prediction on its own does not move the arm. A robot uses a world model in one
of three ways.

The first way is **planning**. The robot imagines many possible actions, asks the
world model what each one would do, and picks the best. It then does the first
part of that plan, looks at the world again, and plans again. The
[learned dynamics models](02_most-used/01_learned-dynamics-models.md#3-how-it-works-inside)
page shows this step by step.

The second way is **practising inside the model**. Another model, called a
**policy**, decides what the arm does from moment to moment. The
[movement models chapter](../05_movement-models/01_overview.md) is about
policies. A policy normally improves by trying things on the real arm. With a
world model, the policy can try things inside the model's predictions instead.
Those tries are fast and break nothing. The
[latent world models](03_also-used/03_latent-world-models.md) page explains how.

The third way is as a **training signal**. Here the world model is part of a
policy while the policy is being trained, and it is thrown away afterwards.
Learning to predict the next picture forces the policy to learn what actions do
to objects. The policy then decides better. Several robot models released in
2026 use a world model in this way. The frontier document
[Simulation and evaluation](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#4-learned-world-models)
describes them, and points out that none of them plans with its prediction.

---

## 5. How this chapter connects to the others

A world model rarely works alone. The table below lists the other chapters of this
book and how each one connects to world models. Read each row as "this other kind
of model does this for, or with, a world model".

| Other chapter | How it connects |
| --- | --- |
| [Seeing models](../02_seeing-models/01_overview.md) | They turn pictures into the object positions that a learned dynamics model needs as input. |
| [3D models](../03_3d-models/01_overview.md) | They turn camera images into 3D points, which a learned simulator can use as its small pieces. |
| [Grasp models](../04_grasp-models/01_overview.md) | A world model can check a proposed grasp by predicting whether the object stays in the gripper. |
| [Movement models](../05_movement-models/01_overview.md) | A policy can practise inside a world model, or use one as a training signal. |
| [Language models](../06_language-models/01_overview.md) | A sentence such as "put the cube in the bowl" can steer a video prediction model to draw the task being done. |
| [Touch and body models](../08_touch-and-body-models/01_overview.md) | A model of the arm's own body is a world model for one special object: the arm. |

The last row is worth a sentence more. The
[learned arm models](../08_touch-and-body-models/03_also-used/02_learned-arm-models.md) page
predicts how the arm itself moves when its motors push. That is the same idea as
a learned dynamics model, pointed at the arm instead of at the objects.

---

## 6. Why learn a world model, and what it costs

The obvious alternative to a learned world model is a **physics simulator**. A
simulator is a program that people wrote by hand from the laws of physics. You
describe the table, the mug and the arm to it, and it calculates how they move.
Book 3 uses simulators such as MuJoCo throughout.

A simulator is exact about the things it models well, such as a rigid arm
swinging through the air. It is weak in three places. Someone has to describe
every object to it by hand, with its shape, weight and friction. It is often
wrong about contact, meaning what happens when two things touch, slide or
squash. And it is poor at soft things such as cloth, dough and liquids.

A learned world model answers those three weaknesses in a different way. It does
not need a hand-written description of each object, because it learns from
recordings. It learns contact from what really happened, not from a formula. And
it can learn soft materials from examples of them moving.

The costs are real, and they are the same for all four kinds.

- **It needs data.** Recordings of the arm acting and the world responding. Some
  kinds can use ordinary video, which is plentiful. Others need recordings from
  the robot itself, which are slow to collect.
- **It is only right about what it has seen.** Show it a heavier mug than any in
  its training data, and its prediction may be wrong without any warning.
- **Errors add up.** Each prediction starts from the last one. A small mistake
  in step one becomes a larger mistake by step ten.
- **It can be slow.** A model that draws whole pictures can take far longer
  than the arm has to decide.

In practice many robot teams use both. They train in a hand-written simulator,
and they use a learned model for the parts the simulator gets wrong. The
learned dynamics page shows the simplest form of this, a
[residual model](02_most-used/01_learned-dynamics-models.md#7-learning-only-the-part-physics-gets-wrong-residual-models),
with a worked example of a pushed block.

---

## 7. Where to read next

Start with [learned dynamics models](02_most-used/01_learned-dynamics-models.md). It is the
simplest kind, and the planning idea it explains is used by the other three.

For the other chapters, the [map of models](../01_what-models-are/07_the-map-of-models.md)
lists all seven. The two closest to this one are
[movement models](../05_movement-models/01_overview.md), which decide what the arm
does, and [reinforcement learning policies](../05_movement-models/03_also-used/01_reinforcement-learning-policies.md),
which learn from trying.

For a deeper and more critical view, three documents in Book 3 cover the same
ground:

- [Learned methods for one arm](../../03_frameworks/04_one-arm-training/03_learned-methods.md#2-learning-from-trial-and-error)
  describes model-based learning, such as Dreamer and TD-MPC, next to the other
  ways an arm can learn from trying.
- [Simulation and evaluation](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#4-learned-world-models)
  describes the world models that were released in 2026 and what they cannot yet
  do.
- [What is changing](../../03_frameworks/04_one-arm-training/05_what-is-changing.md#world-models)
  explains why people expect world models to matter: they can learn from video
  that has no robot actions attached to it.
