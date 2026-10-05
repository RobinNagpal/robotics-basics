# Latent world models

This page explains world models that predict the future as a short code instead
of as a picture, and the best-known family of them is called Dreamer. The page
answers four questions: what the "short code" is and where it comes from, how a
robot can practise a task inside the model's predictions, how such a model is
trained, and why anyone would choose it over the other kinds of world model.

It is written for a reader who has already read the
[world models overview](../01_overview.md), the page on
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md) and the
page on [video prediction models](01_video-prediction-models.md), so you should
know what a state, an action, a rollout and a policy are, because this page
joins ideas from both of those last two pages.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
   · [5.1 World Models](#51-world-models)
   · [5.2 PlaNet](#52-planet)
   · [5.3 DreamerV3](#53-dreamerv3)
   · [5.4 DayDreamer](#54-daydreamer)
   · [5.5 TD-MPC2](#55-td-mpc2)
   · [5.6 V-JEPA 2 and V-JEPA 2-AC](#56-v-jepa-2-and-v-jepa-2-ac)
   · [5.7 How to choose](#57-how-to-choose)
6. [Where this is going](#6-where-this-is-going)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What it is

A latent world model turns each camera picture into a short list of numbers,
called a **code**, and predicts how that code will change when the arm acts.

The word **latent** means "hidden", and the code is hidden in the sense that no
person chose what its numbers mean. Nobody decided that "number 3 is the cube's
position". Instead, the model found during training a set of numbers that keeps
what matters about the picture and drops the rest.

Here is an everyday example of the same habit. Imagine you are planning how to carry
a sofa up a narrow staircase. While you plan it, you do not picture every thread of
the sofa's fabric or the colour of the walls. Instead, you think about a few things
only: how long the sofa is, how wide the stairs are, and where the corner is. Then
you try out a few ways in your head before you lift anything. A latent world model
plans in the same kind of reduced description, because it keeps the things that
matter for the task and drops the rest.

This kind of model joins the two earlier pages together in one design. Like a
[learned dynamics model](../02_most-used/01_learned-dynamics-models.md) , it predicts
a short list of numbers, which is fast. Like a
[video prediction model](01_video-prediction-models.md) , it learns straight from
camera pictures, so nobody has to measure positions by hand.

---

## 2. What goes in and what comes out

Now that the code has a name, here is what actually passes in and out. A latent
world model for a robot arm has one input at the start, and after that it works
only with codes.

- **At the start: a camera picture.** For example, the picture from a camera
  above the table, showing the gripper, a cube and a bowl.
- **At each step: an action.** For example, "move the gripper 2 cm to the right".
- **At each step, it gives back the next code**, and also a **predicted score**:
  a number that says how well the task is going. The score is called the
  **reward**. For example, it could be 1 when the cube is in the bowl and 0
  otherwise.

The model can also turn a code back into a picture, so that a person can check
what it is thinking. However, it does not need to do that in order to plan or
practise.

A typical code has a few hundred to a few thousand numbers, which sounds like a
lot. However, a camera picture of 64 × 64 pixels, with 3 colours for each pixel,
is already 12,288 numbers, and real camera pictures are much larger than
that.

---

## 3. How it works inside

The last section said what passes in and out, so this section says what is
inside. A latent world model has four parts, and each one has a single job. The
first turns a picture into a code, the second predicts the next code, and the
third predicts the score. Then the fourth turns a code back into a picture, and it
is used mainly during training. The 2018 World Models paper in
[section 5.1](#51-world-models) is the clearest description of this arrangement,
and the shortlist keeps it for that reason rather than to run it. The entries you
would run rearrange these parts, and several of them leave one of the four out,
which this section points out as each part appears.

### Squeezing a picture into a code

The **encoder** is a network that takes a camera picture and gives back a short
code. The **decoder** is a network that does the opposite, because it takes a
code and draws a picture from it.

During training, the encoder and the decoder are joined together. The picture goes
into the encoder, the code goes into the decoder, and the picture that comes out is
compared with the one that went in. The training then makes the two pictures as close
as it can. The only way to do that is for the code to keep the important things about
the picture: where the gripper is, where the cube is, and whether the gripper is
open.

![A camera picture goes through an encoder into six numbers, and a decoder draws the picture back from those six numbers](../../../images/world-models/latent-world-models/picture-to-short-code.svg)

Here a picture of 768 numbers is squeezed into 6, and the picture drawn back is
close to the original but slightly blurred.

Once again, the drawing uses a tiny picture and a tiny code so that you can see
each part. Real codes are larger, as the last section said, but the idea behind
them is the same.

Whether a model keeps the decoder after training is the biggest single choice in
this family, so here is what each answer costs. Keeping it gives you two things.
The code is forced to hold enough about the picture to redraw it, which is a
strong and simple instruction that works before anybody knows what the task is.
And you can look: you can draw the rollout the model imagined and watch it, which
is the only honest way of finding out whether a policy learned something strange
because the model predicted something impossible. What keeping it costs is where
the code's room goes. Drawing a picture back rewards the model for whatever
covers the most pixels, so a patterned tablecloth takes up room that a small
screw needed.

Dropping the decoder reverses both. The code now holds only what the rest of the
model needs, which is usually the score and the value, so a small detail that
decides the task is no longer competing with the background for space. But you
can no longer draw anything, so when the predictions are bad you have the score
curves and nothing to look at. And something else now has to stop the encoder
from collapsing: with no picture to redraw, a code of all zeros would be
perfectly easy to predict and completely useless, so a model with no decoder
always carries an extra arrangement whose only job is to prevent that. The two
entries below that drop the decoder each do it in their own way, and both are
described in their own sections.

Two entries in the shortlist change this part. TD-MPC2, in
[section 5.5](#55-td-mpc2), has no decoder at all, so its code is trained only to
be good at predicting the score and the value of a state and never at drawing the
picture back. V-JEPA 2-AC, in [section 5.6](#56-v-jepa-2-and-v-jepa-2-ac), does
not learn the encoder from your robot's pictures at all, because it is trained on
a large amount of internet video before your robot has moved. DreamerV3, in
[section 5.3](#53-dreamerv3), is the entry that keeps the decoder, which is what
lets you draw what it imagined and look at it.

### Predicting the next code

The **dynamics part** is a network that takes the code now and an action, and gives
back the next code. This is exactly the learned dynamics model from the
[previous pages](../02_most-used/01_learned-dynamics-models.md#one-step) , working on
codes instead of measured positions.

Most latent world models also keep a **memory**, which is a second list of
numbers carried from step to step. That memory lets the model remember things
the current picture does not show, such as a cube the gripper is now hiding.

The **score part** is a small network that looks at a code and predicts the
reward. It lets the model say not only "what will the scene be?" but also "is
that good for the task?".

Once these parts are in place, the model can run forward on its own. It starts from
the code of one real picture, and then it predicts the next code for each
action, again and again, without drawing a single picture.

![From one real picture, the model predicts codes step by step for three actions, with a predicted score at each step, and draws no pictures in between](../../../images/world-models/latent-world-models/imagining-in-code.svg)

Only the first picture is real, and every later code and score is a prediction;
the numbers are made up to show the idea.

Predicting codes is much faster than drawing pictures, because a code has far
fewer numbers than a picture. So a small network can predict many steps in the
time a large video model takes to draw one frame, and that speed is what makes
the next idea possible.

### Practising inside the model

Because the model is fast, its predictions are sometimes called **imagination**,
or a **dream**. Those names only mean "a rollout that the model made up, not one
that happened". The key idea of the Dreamer family is that a policy can practise
inside this imagination, and it works in the three steps below. DreamerV3, in
[section 5.3](#53-dreamerv3), is the entry that does it, and DayDreamer, in
[section 5.4](#54-daydreamer), is the same idea split into two programs so that
it can run on an arm that cannot be hurried.

1. **Start from real moments.** Take codes from real pictures that the robot saw
   earlier.
2. **Imagine.** From each one, let the policy choose actions, and let the world
   model predict the codes and scores that follow, for a short stretch of steps.
3. **Improve the policy.** Change the policy so that it chooses actions that led
   to higher predicted scores.

Then a second small network helps with step 3, and it is called the **critic**. It
looks at a code and guesses the total score still to come from there. This lets
the policy learn from imagined stretches that are too short to reach the end of
the task.

Many of these imagined stretches can run in the time the real arm makes one
move. So the real arm is used only to collect new pictures now and then, and to
check that the policy works.

Practising is not the only use of a fast code. Instead of training a policy, a
program can search over sequences of actions inside the code before every move,
which is the planning on the
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md#planning-with-it)
page with codes in place of measured positions. PlaNet, in
[section 5.2](#52-planet), does that and has no policy at all, and TD-MPC2, in
[section 5.5](#55-td-mpc2), searches in the same way before each move, which is
the model predictive control its name refers to.

![On the left, three practice attempts on the real arm; on the right, many imagined attempts inside the world model](../../../images/world-models/latent-world-models/real-vs-imagined.svg)

Each real attempt feeds the world model, and the policy then practises many
times inside it.

---

## 4. How it is trained

The sections above described the parts, and this section says how they are
trained together. A latent world model learns from the robot's own recordings,
and each recording is a sequence of camera pictures, the action taken after each
one, and the reward at each step. Training then repeats a cycle of three
stages.

1. **Collect.** The robot tries the task on the real arm with its current
   policy, and records everything. At first the policy is random.
2. **Train the world model.** The encoder, decoder, dynamics part and score part
   all learn from the recordings. They learn to squeeze pictures, to draw them
   back, to predict the next code, and to predict the reward.
3. **Train the policy.** The policy and the critic practise inside the world
   model, as described above.

Then the cycle starts again, because the better policy collects more useful
recordings, which make the world model better, which in turn makes the practice
better.

The reward itself must come from somewhere, and that is easy in some places and hard
in others. In a simulator, a program can compute it exactly. On a real arm, however,
it might come from a sensor, from a person pressing a button, or from another model
that looks at the camera and says whether the task succeeded. The
[vision-language models](../../07_language-models/02_most-used/02_vision-language-models.md)
page describes models that can check success from a picture.

How much real data is needed depends on the task, but it is usually far less
than for a policy that learns without a model. That saving is the whole reason
for this kind of model.

---

## 5. Well-known models of this kind

The models below are all real, published models rather than examples invented
for this page, and this section is here so that you can pick one. The Dreamer
line is the reference point for the whole family, so three of the six entries
come from the group that built it and a fourth is a direct answer to it.

Read the table one row at a time. The left column names the model and says how
current it is. The right column holds the rest: what the model is best at, how
big it is, its licence, and when to pick it. The sizes are worth reading twice,
because the published numbers run from hundreds of parameters to hundreds of
millions, and the small numbers are not mistakes. The licences matter as much,
because two of these repositories have no licence file at all, which means you
have no stated permission to use the code. Where a number is not published, the
row says `not stated` rather than giving a guess.

| Model | What decides it |
| --- | --- |
| [**5.1 World Models**](#51-world-models), historical | It is best at showing the whole idea in three small parts. Its published parameter counts are 4,348,547 for the encoder and decoder, 422,368 for the predictor and 867 for the policy. The code repository has no licence file. Pick it when you want the shortest explanation of the design. |
| [**5.2 PlaNet**](#52-planet), historical | It is best at planning inside a learned code, with no policy anywhere. Its size is not stated, and the licence is Apache-2.0. Pick it when you want planning rather than a trained policy. |
| [**5.3 DreamerV3**](#53-dreamerv3), most used in 2026 | It is best at being one agent that works on many tasks without retuning. Its configuration blocks run from `size1m` to `size400m`. Its licence file holds the MIT licence text. Pick it when you want the complete reference agent. |
| [**5.4 DayDreamer**](#54-daydreamer), historical | It is best at learning on a real robot with no simulator. Its size is not stated, and it has no licence file. Pick it when you are wiring Dreamer to a real arm. |
| [**5.5 TD-MPC2**](#55-td-mpc2), most used in 2026 | It is best at continuous control, and it is the only entry with published checkpoints. Each single-task checkpoint holds 5 million parameters, and the 80-task agent holds up to 317 million. The licence is MIT. Pick it when you control an arm and want weights to start from. |
| [**5.6 V-JEPA 2 and V-JEPA 2-AC**](#56-v-jepa-2-and-v-jepa-2-ac), worth betting on | They are best at codes learned from internet video rather than from your own arm. The published ViT-L encoder holds about 326 million parameters. The licence is MIT. Pick them when you cannot record enough data of your own. |

### 5.1 World Models

This model is **historical**, and it is here because it is the clearest
description of the design that every later entry rearranges.

Size xs, machine not stated, and no licence file.

David Ha and Jürgen
Schmidhuber published [World Models](https://arxiv.org/abs/1803.10122) in 2018,
at the Neural Information Processing Systems conference, under the title
"Recurrent World Models Facilitate Policy Evolution". It has exactly three parts:
a network that squeezes a game picture into a code, a network that predicts the
next code, and a policy that reads the code and acts. The policy was trained
entirely inside the model's own predictions, for a car racing game.

The one idea it is built on is that the part choosing the actions should be as
small as it can possibly be, so that almost everything the agent knows sits in
the world model instead. The paper names its three parts V for the picture
squeezer, M for the predictor and C for the policy, and the project page states
the point in those terms: C is kept "as simple and small as possible, and trained
separately from V and M, so that most of our agent's complexity resides in the
world model".

What that changes, compared with every later entry here, is the order of
training. The three parts are trained one after another and never together. The
picture squeezer is trained first, on frames collected by a policy that moves at
random, until it can squeeze a frame into a few dozen numbers and draw it back.
Then the predictor is trained on the codes that squeezer produces, and the
squeezer does not change while this happens. Then the policy is trained inside
the predictor's dream, and neither of the first two changes. PlaNet and DreamerV3
do the opposite: their encoder and their predictor are trained together against
one objective, so the code ends up shaped by what the predictor finds hard as
well as by what the picture needs. Here the code is shaped by the picture alone,
and it is frozen before anything knows what the task is.

The second thing to understand is what the predictor gives back, because it is
not one next code. It is a recurrent network whose output is a set of
possibilities with weights, which the project page describes as training the
network "to output a probability density function p(z) instead of a deterministic
prediction of z". In ordinary words it says "the next code is probably around
here, or possibly around there", and the next code is then drawn at random from
that. A setting called the temperature widens or narrows the spread. That dial
matters because the policy is trained inside the dream, and a dream that is too
confident can be cheated: the policy finds a sequence of actions that works
beautifully in the model and not at all in the game. Widening the spread makes
the dream less sure of itself and makes it harder to cheat. No later entry on
this page exposes that trade so plainly.

What the idea buys is the figure that makes the paper famous. The policy is 867
numbers, which is small enough to train by an evolutionary algorithm, which here
means trying many slightly different policies and keeping what scores best,
rather than by gradients. What it costs is the frozen code. If the thing that
decides your task is something the picture squeezer judged unimportant, it is
gone from the code, and no amount of later training recovers it, because the
later training never touches the squeezer. On a robot arm that is not a
hypothetical: a thin screw on a patterned table is a few pixels, a redrawn
picture barely suffers from losing it, and the arm then cannot find it. The two
entries with no decoder, [5.5](#55-td-mpc2) and
[5.6](#56-v-jepa-2-and-v-jepa-2-ac), are both answers to that failure.

What it costs you is that the published code no longer runs. Its own notes pin
`gym 0.9.x`, say the experiments do not work on `gym 0.10.x`, and ask for
`numpy==1.13.3`. The original repository links to a later reimplementation
in TensorFlow 2.2 by Zac Wellmer at
[zacwellmer/WorldModels](https://github.com/zacwellmer/WorldModels), which runs in
a Docker container.

The library is TensorFlow 1, and the useful code sample is the installation,
because it tells you what you are taking on:

```sh
git clone https://github.com/hardmaru/WorldModelsExperiments.git
# The versions the repository asks for. Nothing newer works.
pip install gym==0.9.4 numpy==1.13.3
```

What you get is a record of an experiment rather than a tool. What you supply, if
you want the design, is an hour with the project page, which is an interactive
article holding the diagrams and the parameter counts.

### 5.2 PlaNet

This model is **historical**, and it is here because it is the version of the
design with no policy in it, which makes one thing easy to see.

Size not stated, a graphics card, Apache-2.0.

Danijar Hafner,
Timothy Lillicrap, Ian Fischer, Ruben Villegas, David Ha, Honglak Lee and James
Davidson published [Learning Latent Dynamics for Planning from
Pixels](https://arxiv.org/abs/1811.04551) at the International Conference on
Machine Learning in 2019. PlaNet encodes the pictures it has seen into a code,
then searches over sequences of actions inside the code, executes the first
action of the best sequence it found, and plans again after the next picture.

The one idea it is built on is that the thing carried from step to step should be
two things at once: a part worked out exactly, and a part drawn at random. The
paper calls the combination a recurrent state space model, and that name is used
by DreamerV3 and DayDreamer as well, so it is worth knowing.

What that changes inside, compared with the World Models design above, is that
there is one loop rather than three trained programs. The exact part is a
recurrent network that carries information forward unchanged for as many steps as
it needs to. The random part is a small set of numbers drawn from a distribution
the network itself produced. The paper's finding is that neither alone is enough,
and the reasons are different. An only-random state "makes it difficult for the
transition model to reliably remember information for multiple time steps", so
the model forgets the cube it can no longer see. An only-exact state cannot hold
two different futures at the same time, so when the future genuinely could go two
ways the model averages them, and what you get is a faint cube in two places
rather than a cube in one place or the other.

The second change is how it is trained to be right far ahead rather than one step
ahead. A model trained only to predict the next step is right one step at a time
and badly wrong by step twenty, and a planner searching twelve steps ahead
depends entirely on step twelve. PlaNet's answer, which it calls latent
overshooting, trains the model on predictions of many different lengths at once,
and checks each against what the model believes after it has actually seen those
pictures. All of that comparison happens between codes, so no picture is drawn
for the far-ahead steps, which is what makes training on them affordable.

What having no policy buys is that nothing has to be retrained when the goal
changes. The score is a function you write, so an arm that was stacking cubes can
be told to spread them out instead, and the next search does it with no gradient
steps at all. What it costs is time at the moment of acting, because the search
runs before every single move while the arm waits, and something subtler. The
search is free to propose any action sequence and it keeps the one with the
highest predicted score, and the highest predicted score is very often found
exactly where the model is most wrong. A trained policy only ever proposes
actions resembling the ones it practised, so it stumbles into the model's bad
regions far less. On a robot arm this is the choice between an arm that pauses a
few seconds before each move but obeys a new goal immediately, and DreamerV3's
arm, which moves without pausing and has to be retrained to want something else.

You would choose PlaNet's approach over DreamerV3's when you do not want a
trained policy at all. The search method is the cross-entropy method from the
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md#planning-with-it)
page, so if you have read that page, PlaNet is that planner with a learned code
in place of measured positions.

What it costs you is an old stack. Its
setup file pins `tensorflow-gpu==1.13.1` and `tensorflow_probability==0.6.0`, and
its README says the code was tested under Ubuntu 18, so treat it as a reference
rather than as a dependency.

The library is the repository, and one command trains an agent on one task:

```sh
# cheetah_run is a running task from the DeepMind Control Suite, learned from pictures
python3 -m planet.scripts.train --logdir /path/to/logdir --params '{tasks: [cheetah_run]}'
```

What you get is the planner, the model and a list of tasks in
`scripts/tasks.py` with their settings in `scripts/configs.py`. What you supply is
an environment of your own. Its README carries one warning worth repeating: it
prints `nan` as the score on iterations where it computed no summaries, which
looks like a broken training run and is not one.

### 5.3 DreamerV3

This model is **most used in 2026**, because it is the one complete agent in this
family that somebody else keeps running, and because the same settings work on
tasks that have nothing in common.

Size xs to m, depending on which of its named sizes you pick, a graphics card,
MIT.

Danijar Hafner, Jurgis Pasukonis, Jimmy Ba and
Timothy Lillicrap published it as [Mastering Diverse Domains through World
Models](https://arxiv.org/abs/2301.04104), and the
[repository](https://github.com/danijar/dreamerv3) cites the journal version as
having appeared in Nature in 2025. It is the model this page has been describing:
an encoder, a predictor, a score part, a policy and a critic, with the policy
practising inside the predictions.

The one idea it is built on is not a new part. It is that nobody should have to
tune it. Every quantity DreamerV3 learns from is first put on a scale it can
safely learn from, whatever that quantity happens to be in your task, so that
nothing needs retuning when the task changes. The abstract says it in one
sentence: "robustness techniques based on normalization, balancing, and
transformations enable stable learning across domains", with a single
configuration.

The first change from PlaNet is the shape of the code. The repository's own words
are that DreamerV3 "encodes sensory inputs into categorical representations". In
ordinary words, the code is not a list of dials that can take any value. It is a
set of multiple-choice answers: several small groups, with exactly one option
chosen in each group, like describing the scene by ticking one box in each of
many short lists. Two things follow. A tick cannot drift to an absurd value the
way a dial can, which is a large part of why the training is stable. And when the
model is unsure between two futures, it says so by splitting the probability
between two boxes, rather than by settling on a value halfway between them. That
is the same averaging problem PlaNet's random part exists to solve, solved a
different way.

The second change is on the acting side. PlaNet searches over action sequences
before every move. DreamerV3 trains a policy and a critic inside the imagined
rollouts instead, so at the moment of acting there is no search at all: one pass
through a small network gives the action, which is why the same agent can drive
something that has to respond quickly. The rescaling the abstract mentions is
what lets one policy survive across tasks, because it means a task whose reward
is 0 or 1 and a task whose reward runs into the thousands reach the policy
looking alike.

The third thing to know is that DreamerV3 keeps the decoder, and part of training
the world model is drawing the picture back. This is the choice
[section 3](#squeezing-a-picture-into-a-code) weighed. It is why you can draw a
rollout the model imagined and watch it, which on a robot arm is the difference
between knowing that the policy is bad and knowing why: you can see whether the
model imagined a cube that behaved impossibly. It is also why a visually busy
scene costs you, because the code's room goes where the pixels are. The concrete
situation where DreamerV3 rather than TD-MPC2 changes the result is a camera-only
arm whose task is going wrong for reasons nobody can name. With TD-MPC2 there is
nothing to look at. Here you watch the dream and usually find the answer in it.

You would choose it over TD-MPC2 in [5.5](#55-td-mpc2) when your robot sees
through a camera and you have no measured positions.

What it costs you is that it is a research repository rather than a package, and
JAX. JAX is a numerical library that compiles Python for graphics cards, and you
install it before the requirements file. The repository says the code is tested on
Linux and macOS and needs Python 3.11 or newer, and `--jax.platform cpu` forces it
onto the central processor, so it will start on a Mac even though training it
there is not sensible. What most often goes wrong is the first item in its own
tips: reusing an old log directory
with a changed configuration, which fails with a message about `PyTreeDef` that
says nothing about the cause.

The library is the repository, and these four commands train it on a computer
game:

```sh
git clone https://github.com/danijar/dreamerv3.git
cd dreamerv3
pip install -U -r requirements.txt            # after installing JAX, as its README says
# crafter is a small survival game; size12m is one of the model sizes it ships
python dreamerv3/main.py --logdir ~/logdir/dreamer/{timestamp} --configs crafter size12m
```

What you get is the whole agent and a list of model sizes you select by name,
from `size1m` to `size400m`, so you change how big the model is with one word
rather than by editing a network. All the options are in
`dreamerv3/configs.yaml`, including a `debug` block that shrinks everything so
that a run starts in seconds and learns nothing, which is the right way to check
your wiring.

What you supply is the robot. Every configuration it ships points at a game or a
simulated control task, so connecting it to an arm means writing an environment
class and a configuration block. That is the work the next sub-section
describes.

### 5.4 DayDreamer

This model is **historical**, and it is here because it is the proof that this
whole approach works on a real robot, with no simulator anywhere: that claim is
what you are relying on when you read the rest of this page.

Size not stated, a graphics card for the learner and a processor for the actor as
its arm commands are written, and no licence file.

Philipp Wu,
Alejandro Escontrela, Danijar Hafner, Ken Goldberg and Pieter Abbeel published
[DayDreamer: World Models for Physical Robot
Learning](https://arxiv.org/abs/2206.14176) at the Conference on Robot Learning
in 2022. The published code ships commands for three machines: a four-legged A1
robot, an xArm and a UR5 arm.

The one idea here is not a new model at all. It is the same model arranged
differently in time. Everything [section 3](#3-how-it-works-inside) describes is
unchanged; what changes is who waits for whom.

In a simulator the loop is simple, because the simulator waits. The agent takes
one step, does some training, takes the next step, and the simulator sits still
for as long as the training takes. A real arm cannot do either half of that. It
cannot be paused halfway through a movement, and it cannot be hurried; it takes
the time it takes. DayDreamer's answer is two programs running at the same time.
The paper describes them plainly: "a learner thread continuously trains the world
model and actor critic behavior, while an actor thread in parallel computes
actions for environment interaction". The actor moves the robot and writes what
happened into a store; the learner reads from that store and trains without ever
touching the robot.

The consequence the authors point out is the interesting one, because it is a
setting that disappears. In DreamerV3 you choose how often to train relative to
how often you act. In DayDreamer that choice is gone: the paper says "there is no
training frequency hyperparameter because the decoupled learner optimizes the
neural networks in parallel with data collection, without rate limiting". How
much training each real movement gets is now decided by how fast your computer
is.

What this buys is that neither the arm nor the learner is ever idle, which on
hardware is the difference between an experiment that finishes in an afternoon
and one that does not finish. What it costs is exactly what it removed. A ratio
you set in a file is a number you can write down and reproduce; a ratio decided
by your hardware is not, so the same code and the same recorded movements on a
slower machine produce a different agent, and two people cannot compare runs
without comparing computers. The policy moving the arm is also always slightly
behind the policy being trained. On a robot arm the symptom you avoid is easy to
recognise: with the simulator arrangement the arm stands still between moves
while the learner catches up, and most of the wall-clock hours of the day are
spent collecting nothing.

You would read it rather than DreamerV3's own repository for that split alone. It
is the piece of engineering a real arm needs, and this repository is where it is
written down.

What it costs you is that it is built on the previous generation. Its code is
TensorFlow 2 on top of DreamerV2, which the authors say to consult for anything
their README does not cover.

The library is the repository, and an arm is run as two programs in two
terminals:

```sh
# Terminal 1, the learner: trains the world model and the policy from stored data
python embodied/agents/dreamerv2plus/train.py --configs xarm --run learning \
    --task xarm_dummy --tf.platform gpu --logdir ~/logdir/run1

# Terminal 2, the actor: moves the real arm and records what happened
python embodied/agents/dreamerv2plus/train.py --configs xarm --run acting \
    --task xarm_real --env.kbreset True --tf.platform cpu --tf.jit False --logdir ~/logdir/run1
```

Notice `--task xarm_dummy` on the learner and `--task xarm_real` on the actor.
The learner never touches the robot, so it is given a stand-in environment that
only tells it the shapes of the pictures and the actions. Notice also
`--env.kbreset True`, which lets a person at the keyboard say that the scene has
been reset, because a real cube does not put itself back on the table.

What you supply is the environment for your own arm and a reward you trust, and
the repository holds three worked examples of exactly that.

### 5.5 TD-MPC2

This model is **most used in 2026** for control from measured positions, because
it is the only entry here that publishes trained agents, so you can run one
before you have trained anything.

Size xs to m across its published checkpoints, a big card for one task and a
workstation for the largest, MIT.

Nicklas Hansen, Hao Su and Xiaolong Wang
published [TD-MPC2: Scalable, Robust World Models for Continuous
Control](https://arxiv.org/abs/2310.16828). It has no decoder at all. Its learned
code is trained only to be good at predicting the score and the value of a
state, never at drawing the picture back.

The one idea it is built on is that the code only has to be good enough to
predict what you will get, not good enough to draw. The paper states it directly:
"rather than explicitly modeling dynamics using reconstruction, TD-MPC2 aims to
learn a maximally useful model: a model that accurately predicts outcomes
(returns) conditioned on a sequence of actions". The word "outcomes" is doing the
work. A picture is not an outcome. The score is.

What that changes inside is that something has to replace the job the decoder was
doing, which was stopping the encoder from giving a useless answer. With no
picture to draw back, an encoder that returned all zeros would make every
prediction perfectly correct and tell you nothing, so three pulls hold the code
in place instead. The code must predict the step's reward. It must predict the
value, meaning the total score still to come, which is learned by the
temporal-difference method the "TD" in the name refers to: each guess is
corrected towards the reward just received plus the next guess. And the predicted
next code must match the code the encoder itself produces for the picture that
actually arrived, with the encoder's answer held fixed during that comparison so
that the two sides cannot agree by both going blank. On top of those three, the
code is pushed through a step the paper calls SimNorm, which squeezes it in small
groups so that its size stays bounded, and the paper says this "naturally biases
the representation towards sparsity" and stops the growing values that broke the
first version of TD-MPC.

On the acting side it plans before every move, like PlaNet, but with two
differences that matter. The search only looks a short stretch of steps ahead,
and the learned value is then used to score whatever state the stretch ended in,
so a short search can still prefer an action that only pays off much later. And
some of the candidate action sequences are proposed by a learned policy rather
than drawn at random, so the search starts from plausible actions. That is a
deliberate middle position between PlaNet, which has no policy and searches from
nothing, and DreamerV3, which has a policy and does not search: here there is a
policy and it is not trusted to act by itself.

What dropping the decoder buys is that none of the code is spent on how things
look, so a small detail that decides the task is not competing with the
tablecloth. What it costs is twofold. You cannot look at anything, so when the
plans come out wrong you have reward curves and no imagined video, and in
practice this is the difference from DreamerV3 you notice first. And the code is
now defined relative to this task's reward, so changing what you reward changes
what the code ought to contain, which is why the reusable thing here is a
checkpoint for a task they trained on and not a general description of your
table. On a robot arm the case where picking this rather than DreamerV3 changes
the result is a measured one: joint angles and object poses, a reward you can
compute, a task like picking a cube in ManiSkill2. There is a published
checkpoint, so you watch the arm do it on the first day. Point a camera at a
cluttered table instead, and the decoder you gave up was doing work you would
miss.

You would choose it over DreamerV3 when nothing in your task needs a picture
drawn, and the practical reason is stronger than the architectural one. Its
authors publish more than three hundred
[trained checkpoints](https://www.tdmpc2.com/models) across four task
collections, including arm tasks from Meta-World and ManiSkill2, and the
repository states that one set of settings covers all 104 of its continuous
control tasks.

What it costs you beyond that is the installation of the task collections rather
than of TD-MPC2 itself, and the README says so about Meta-World, which
needs MuJoCo 2.1.0 and an old version of `gym`. One number in that README is not
covered by the bands above and will catch you: training on the published 80-task
dataset asks for 128 GB of ordinary system memory, which is a different machine
rather than a bigger graphics card.

The library is the repository, and a downloaded checkpoint is evaluated in one
command:

```sh
# pick-cube is a ManiSkill2 arm task; single-task checkpoints are always model_size=5
python evaluate.py task=pick-cube checkpoint=/path/to/downloaded.pt save_video=true

# Training your own on the same task, from nothing
python train.py task=pick-cube
```

What you get is the model, the planner, the task wrappers and the weights. What
you supply is your own task, and the `envs` directory holds the examples to copy.
What you decide is whether your robot's state is measured or seen. The README
offers an `obs=rgb` argument for pictures on its DeepMind Control Suite tasks, but
pictures are the setting where DreamerV3 is the better-tested choice.

### 5.6 V-JEPA 2 and V-JEPA 2-AC

These models are **worth betting on** because of the constraint this page keeps
running into. V-JEPA 2
attacks that by learning its codes from a large amount of internet video before
your robot has moved at all, and that is the direction the field is going, because
video is the one kind of data that is plentiful.

Size m for the published ViT-L encoder and larger for the ViT-g the
action-conditioned model is built on, a laptop for the published planning
notebook, MIT.

Meta published it in 2025 at
[facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) under the
MIT licence, read from its licence file.

There are two models and the difference matters. V-JEPA 2 is a video encoder with
a predictor and no action in it, so it is not yet a world model for an arm.
V-JEPA 2-AC is the action-conditioned version, post-trained from the larger
V-JEPA 2 encoder on robot recordings, and its predictor takes the code, the action
and the arm's own pose.

The one idea these are built on is in the four letters JEPA, which stand for
joint-embedding predictive architecture. It means the prediction is made and
judged entirely between codes, and never against pixels. Training hides part of a
video and asks the model to predict the hidden part, which sounds like the video
prediction models of the [previous page](01_video-prediction-models.md), except
that what it has to produce is not the missing pixels. It is the code that the
model's own encoder gives for those missing pixels. A second copy of the encoder
looks at the hidden piece and reports a code, and the predictor's job is to
produce that code without having seen the piece. There is no decoder anywhere in
the design, not even during training.

That is a bolder version of the problem TD-MPC2 faced. If the thing being
predicted is produced by the thing being trained, then both halves can agree to
report nothing and the training looks perfect. V-JEPA 2 holds the target copy of
the encoder fixed while the predictor is trained against it, which is the same
defence as TD-MPC2's held-fixed next code. The payoff for accepting that risk is
that nothing in this training needs a label, a reward or an action. It needs
video, and video exists in a quantity no robot can approach.

The second stage is where it becomes a world model for an arm, and what it does
is narrow. The video encoder is frozen, and a new predictor is trained on
unlabelled robot video from the Droid dataset. That predictor reads the code, the
action and the gripper's own pose, and its attention is block-causal, which means
every patch of a step may look at that step's action and pose and at everything
from earlier steps, and at nothing later. So a code and an action go in and the
next code comes out, exactly as this page describes, but the part that decided
what a code means never saw your robot and was never told what your task is.

What that buys is a model that already knows objects fall, shapes persist and
hands push things, before your arm has moved once, and a planner you can run
without a graphics card. What it costs is the missing half of the agent. The
repository publishes the encoders and the predictor and no reward model, critic
or policy, so the practising described in
[section 3](#practising-inside-the-model) is not available here at all. Planning
is instead done by goal picture: you photograph what you want, the planner
searches for actions whose predicted code lands closest to the goal's code, and
anything a photograph cannot express cannot be asked for. "Press until it
resists" has no goal picture. On a robot arm the situation where this rather than
DreamerV3 changes the result is a week with no dataset: V-JEPA 2-AC can move a
cube between two photographed places on the first day, while DreamerV3 is still
collecting. Give it instead a task defined by a force or by a rule rather than by
how the table should look, and there is no way to tell it.

You would choose it over DreamerV3 when you cannot record enough data yourself.
DreamerV3 starts from nothing and learns your task from your robot's own tries,
which is why it needs hours of them. V-JEPA 2-AC arrives already knowing how
objects move, and Meta's own description is that it solves manipulation tasks
without collecting data in your environment and without calibration.

The encoder is published on Hugging Face as
[facebook/vjepa2-vitl-fpc64-256](https://huggingface.co/facebook/vjepa2-vitl-fpc64-256),
and the action-conditioned checkpoint was trained from the larger ViT-g encoder,
which is the one the code sample below downloads.

The library is PyTorch Hub for the weights, and the repository for everything
else. Two lines fetch the action-conditioned world model:

```python
import torch

# Downloads a ViT-g encoder and the action-conditioned predictor trained on robot video
encoder, predictor = torch.hub.load("facebookresearch/vjepa2", "vjepa2_ac_vit_giant")

# codes: what the encoder returned for the frames the arm has already seen
# actions: seven numbers per step, of which the first three are the change in gripper position
# states: the arm's own pose at each step
next_codes = predictor(codes, actions, states)
```

Beyond the weights you also get a worked planner. The notebook
`notebooks/energy_landscape_example.ipynb` wraps the same encoder and predictor in
a small `WorldModel` class whose `infer_next_action` method searches for the best
action with the cross-entropy method, given a code for now and a code for the
goal. It is configured with `device="cpu"` and deliberately few search steps, so
it runs without a graphics card, which makes it the entry on this page most
likely to do something useful on a Mac.

What you supply is the reward or the goal picture, the loop that keeps calling
the planner, and the connection to your arm. One more thing is worth knowing
first. Book 3's
[world models that actually shipped](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies)
records that when V-JEPA 2 reached a usable robot library, in LeRobot v0.6.0 in
July 2026, it was not used for planning. In the policy called VLA-JEPA the world
model trains the network and is then discarded, and nothing searches over
imagined futures while the robot acts. So the planning described here is
published and runnable, and it is not yet what the shipped systems do.

### 5.7 How to choose

Start with DreamerV3. It is the complete agent, the settings work without tuning,
and everything this page describes is in one repository.

Three things change that choice.

If your robot's state is measured numbers rather than camera pictures, use
TD-MPC2 instead, and start from one of its published checkpoints. Having weights
to evaluate on the first day is worth more than any architectural argument on
this page.

If you cannot record hours of robot data, use V-JEPA 2-AC, and accept that you
are writing the planner rather than training a policy. Its notebook runs on a
central processor, so this is also the entry to pick if you only want to see a
latent world model work before committing to one.

If you are putting any of them on a real arm, read DayDreamer first, whichever
model you chose. The split between an actor that moves the robot and a learner
that trains from stored data is not optional on hardware, and DayDreamer is where
it is written down.

Finally, a case that sends you off this page. If a few measured numbers describe
your task, and you can measure them, a learned code is not worth its cost.

---

## 6. Where this is going

This section looks forward rather than back, and it was written on 4 October
2026. Book 3 sorts forward-looking statements into four kinds, in
[four kinds of claim](../../../03_frameworks/08_frontier/06_what-is-coming.md#1-four-kinds-of-claim-and-why-the-difference-decides-everything):
a demonstration is a recording of something working once under conditions the
publisher chose, a product announcement says a thing can be bought or
downloaded, a research result is a measured number on a stated task, and a
projection is a statement about a date that has not arrived. This section names
the kind every time, and says so where the judgement is mine rather than
somebody's published statement.

The shape of the change in this family is where the code comes from. In the
first models the code came from your own robot's pictures, which meant the robot
had to move before the model knew anything, and
[section 5](#5-well-known-models-of-this-kind) walks through eight years of
making that cheaper: one network per task, then one set of settings for many
tasks, and then codes learned from video of other people before the arm moves at
all. The same eight years did not make anybody deploy one, and that gap is the
subject of the rest of this section.

Here is the honest summary of industrial use, and it is the distinction worth
carrying away. The idea in this family is influential inside larger systems, and
almost nobody runs a latent world model on its own. There is no product whose
selling point is that a robot plans inside an imagined world. What exists instead
is a set of shipped systems in which a latent world model trains something else
and is then put away.

The checkable case is
[LeRobot v0.6.0](https://huggingface.co/blog/lerobot-release-v060), released on
6 July 2026 under Apache-2.0, which added three world-model policies you install
with `pip`. Two of them use a latent world model exactly as described above.
[VLA-JEPA](https://huggingface.co/docs/lerobot/vla_jepa) pairs a
[Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) language backbone with Meta's
[V-JEPA 2](https://github.com/facebookresearch/vjepa2) and states in its own
documentation that at inference "only Qwen + the action head are used. The world
model is not needed at inference time."
[FastWAM](https://huggingface.co/docs/lerobot/fastwam) says the same in
different words. Book 3 works through the mechanism in
[world models that actually shipped](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies).
This is a product announcement, which is the strongest kind of claim here, and
what it announces is the representation rather than the planner.

The rest of the industrial picture is weaker, and it is worth separating. You
can download the pieces: the V-JEPA 2 encoders are on Hugging Face under the MIT
licence, [TD-MPC2 publishes checkpoints](https://www.tdmpc2.com/models), and
[DreamerV3's code](https://github.com/danijar/dreamerv3) is public. None of those
is a product with a support contract behind it. Above that there are
announcements with nothing to check. On 4 June 2026 the humanoid company 1X
announced [the 1X World Model Lab](https://www.1x.tech/discover/1x-world-model-lab)
and said that advances in its own world model "enabled NEO to generalize to
completely unseen tasks with zero-shot execution". That sentence has no task
list, no success rate, no protocol and no artefact, so it is a company claim
about a demonstration rather than a result. Google DeepMind's
[Genie](https://deepmind.google/models/genie/) is further back still: Book 3
records it as
[announced rather than released](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#42-genie-the-closed-frontier),
with no weights and no interface a robot could act through.

The research front is more interesting than the product front, and four things
are moving. The first is practising inside the model at a scale that was not
possible before. [Dreamer 4](https://danijar.com/project/dreamer4/), published as
[Training Agents Inside of Scalable World Models](https://arxiv.org/abs/2509.24527)
in September 2025, trains behaviour by reinforcement learning inside its own
world model, which is what [section 3](#practising-inside-the-model) describes,
and reports being the first agent to obtain diamonds in Minecraft purely from
offline data, beating OpenAI's [VPT](https://arxiv.org/abs/2206.11795) agent
with a hundred times less data. Its authors say directly that the reason to care
is robotics, where letting the robot practise for real is impractical. That is a
research result on a stated task, and the task is Minecraft rather than a robot
arm, which is the part to keep in mind.

The second is learning what an action is from video that has no actions recorded
in it. [Latent Action Pretraining from Videos](https://arxiv.org/abs/2410.11758)
infers a small set of latent actions from ordinary video and pretrains on those
before any robot data is used. This matters because the binding constraint on
this family is action-labelled data, and the one plentiful signal is video
without actions, which is the same argument
[section 5.6](#56-v-jepa-2-and-v-jepa-2-ac) makes for V-JEPA 2.

The third is the missing half of the agent. Planning inside a latent model needs
a score for an imagined future, and that score is the part that has been absent
from the downloadable models. LeRobot v0.6.0 added two reward models alongside
the three world models, and Dreamer 4's own page reports that its reward model
identified task success inside imagined scenarios. A world model and a reward
model arriving in the same release is the combination that makes planning
possible at all.

The fourth is pressure from the other direction. NVIDIA's Cosmos 3 models, such
as [Cosmos3-Nano](https://huggingface.co/nvidia/Cosmos3-Nano), now take a
sequence of actions and predict the video those actions would cause, which the
[previous page](01_video-prediction-models.md) covers. If a model that predicts
pixels becomes action-conditioned and fast enough to roll out, the main argument
for predicting a code instead of a picture gets narrower.

Three things remain unsolved, and the first has resisted the whole history of
this family. You cannot read a wrong prediction. When a rollout goes wrong there
is still no accepted way to tell whether the fault is in the encoder, the
predictor or the reward model, because the only thing you can inspect is a list
of numbers that means nothing on its own. Every entry in
[section 5](#5-well-known-models-of-this-kind) carries this cost, and no paper
in eight years has published a method for it that other groups adopted.

The second is saying what you want. Planning by goal picture, which is how
[section 5.6](#56-v-jepa-2-and-v-jepa-2-ac) plans, cannot express "press until
it resists" or "do not let the lid tilt". A reward model can express those, but
then somebody has to train the reward model, and nobody has published a general
way to write a reward for a manipulation task that works outside the task it was
written for.

The third is that the benefit of the version that shipped is not established.
Book 3 records that there is
[no published head-to-head result](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies)
with confidence intervals showing that the three LeRobot world-model policies
beat a policy trained without the extra prediction loss. The defence against the
model learning to predict nothing is also still a trick rather than a proof: both
TD-MPC2 and V-JEPA 2 hold a copy of the target fixed, as
[section 5.5](#55-td-mpc2) and [section 5.6](#56-v-jepa-2-and-v-jepa-2-ac)
describe, and nothing bounds what the code ends up meaning.

What follows is what I expect, and it is my judgement rather than anybody's
commitment. I expect the world model as a training signal to become ordinary
inside large robot policies, and the planner to stay rare. The reason is cost on
three sides. It is already installable, it adds nothing to the time the robot
takes to act because the predictor is discarded, and it does not require the
model to be right about contact, only to be informative about it. Planning
requires all three of the opposite things. When a method that is cheap on every
axis ships at the same time as a method that is expensive on every axis, the
cheap one is what gets adopted.

I expect latent world models to be adopted for judging policies before they are
adopted for controlling robots. The reason is that evaluation is the measured
bottleneck in this field: Book 3's section on
[why two numbers are usually not comparable](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#8-why-two-numbers-on-the-same-benchmark-are-usually-not-comparable)
sets out the evidence. A model whose rollout is wrong by a tenth is useless for
choosing the next action and still useful for ranking two policies against each
other, because both policies are ranked by the same wrong model. That asymmetry
is the opening. This is my expectation and not an announcement.

I expect latent actions learned from human video to become a normal pretraining
stage rather than a research idea. The reason is that it attacks the constraint
everything else in this book keeps running into, which is the number of
action-labelled robot demonstrations, and the recipe is already published and
reproducible. The thing that would confirm it is a released policy whose model
card names an unlabelled video pretraining stage.

I expect on-robot planning to become technically possible soon and to stay
narrow in use. The possibility has a date attached from somebody with a record
of shipping: NVIDIA announced on 15 July 2026 that
[Jetson Thor hardware](https://blogs.nvidia.com/blog/jetson-thor-robotics-edge-ai-agent/)
arrives in the first quarter of 2027, and Book 3's
[section on dated commitments](../../../03_frameworks/08_frontier/06_what-is-coming.md#22-nvidias-edge-computers-with-hardware-stated-for-the-first-quarter-of-2027)
explains why that date is worth more than most. Rolling a latent model forward a
few hundred times per decision is the kind of work that hardware is for. My
guess about the use, and it is a guess, is that the first real applications will
be tasks a photograph can describe, such as arranging objects into a pictured
layout, because that is the only goal this family can currently be given without
training a reward model first.

The thing I do not expect within three years is a shipped product whose claim is
that the robot plans inside an imagined world. That needs contact accuracy, a
reward model and a search budget at the same time, and no published evidence says
any one of the three is in place. If it does happen, the most likely place is a
company that owns its whole stack and has said so, which is what 1X announced
in June 2026 — and an announcement is the weakest kind of claim in the list this
section started with.

---

## 7. Where to read next

- Go back to the [world models overview](../01_overview.md) for how the four kinds
  compare.
- [Reinforcement learning policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  explain the trial-and-error learning that a latent world model speeds up.
- [Vision-language-action models](../../07_language-models/02_most-used/01_vision-language-action-models.md)
  explain the large robot policies that, in 2026, started to use world models
  as a training signal.
- [Learned arm models](../../09_touch-and-body-models/03_also-used/02_learned-arm-models.md)
  apply the world model idea to the arm's own body.
- For more depth, read Book 3's
  [learned methods for one arm](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#2-learning-from-trial-and-error),
  which places Dreamer and TD-MPC next to the other ways an arm learns from
  trying, and
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies),
  which describes the latent world model VLA-JEPA and what it cannot yet do.
