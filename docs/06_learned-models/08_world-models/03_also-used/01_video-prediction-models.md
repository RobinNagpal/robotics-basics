# Video prediction models

This page explains world models that predict future camera pictures, and it answers
four questions about them: what it means for a model to "predict a picture", how a
robot arm can use a predicted picture to decide what to do, why predicted pictures
often come out blurry, and when this kind of model is worth its large cost.

It is written for a reader who has already read the
[world models overview](../01_overview.md) and the page on
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md), so you
should know what a model, a state, an action and a rollout are. It also assumes
you know that a camera picture is a grid of numbers, one per colour per pixel,
which [what a model is](../../01_what-models-are/01_what-a-model-is.md)
explains.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Drawing the next picture](#drawing-the-next-picture)
   · [Why the future comes out blurry](#why-the-future-comes-out-blurry)
   · [Four ways a robot uses the pictures](#four-ways-a-robot-uses-the-pictures)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
6. [A worked example: sliding a cube to a clicked spot](#6-a-worked-example-sliding-a-cube-to-a-clicked-spot)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)
11. [Using it in Python](#11-using-it-in-python)

---

## 1. What it is

A video prediction model predicts the next camera pictures from the recent
pictures and, usually, the actions the arm is about to take.

A learned dynamics model needs a short list of numbers, such as the position of
a cube, and somebody must measure those numbers first. A video prediction model
skips that step, because it works directly on the pictures from the camera. In
other words, its "state" is simply what the camera sees.

Here is an everyday example of the same skill, using a video of falling
dominoes. Watch the first half of a video of someone knocking over a row of
dominoes, and then pause the video there. You can picture
the next few seconds, because the dominoes keep falling, one after another, from
left to right. You did not measure any positions, and you only pictured what you
would see. So a video prediction model does the same thing, one frame at a time.

A **frame** is one picture in a video, and a camera on a robot arm usually records
between 10 and 30 frames every second.

---

## 2. What goes in and what comes out

Now that the idea is clear, here is what actually passes in and out of such a
model. A video prediction model for a robot arm takes two things in and gives
one back.

- **The recent frames.** For example, the last three pictures from a camera
  above the table.
- **The planned actions.** For example, "move the gripper right, then right
  again, then right again". Some models also accept a sentence instead, such as
  "put the red cube in the bowl".
- **The output: the predicted future frames.** For example, three pictures that
  show the gripper moving right and pushing the cube along.

The picture below shows this with tiny pictures of 14 × 14 pixels, so that you
can see each pixel. However, real models use pictures with a few hundred pixels
on each side.

![Three camera pictures and three planned moves go into a video model, which draws three future pictures](../../../images/world-models/video-prediction-models/frames-in-frames-out.svg)

The predicted pictures get blurrier the further ahead they are, because the
model is less sure what will happen.

A model that takes the actions as an input is called **action-conditioned**,
because it predicts a different future for each different action. That is what
makes it a world model and not only a video generator. A video generator that
ignores the action can show you *a* future. Instead, an action-conditioned model
can show you the future *that your action would cause*.

---

## 3. How it works inside

### Drawing the next picture

The last section said what goes in and what comes out, so this section says what
happens in between. A video prediction model has three parts, and they run in
the order below.

1. **An encoder** turns each recent frame into a smaller grid of numbers that
   describes what is in it. Seeing models use the same kind of part; the
   [image classification](../../03_seeing-models/03_also-used/01_image-classification.md) page
   shows how a picture becomes numbers.
2. **A predictor** combines those numbers with the action numbers. It works out
   how things in the scene will move.
3. **A decoder** turns the result back into a full picture, pixel by pixel.

To see further ahead, the model feeds its own predicted frame back in, like the
rollout on the
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md#many-steps-in-a-row)
page, and the same problem appears here: errors add up from frame to frame.

Some older models do not draw the new frame from nothing. Instead, they predict
how each pixel moves, as in "this group of red pixels shifts two pixels to the
right", and then they move the pixels of the last frame. So this works well for
pushing, where most of the scene stays the same and only a few things move.

Most newer models are **diffusion models**, which build the picture in a different
way. A diffusion model starts from a picture of pure random noise, like the snow on
an old television. It then removes the noise a little at a time, over many passes,
until a clear picture is left. At each pass, it uses the recent frames and the action
to decide what the clean picture should look like. The
[diffusion and flow policies](../../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md)
page explains the same method used to produce arm movements. So diffusion models draw
sharp pictures, but the many passes make them slow.

### Why the future comes out blurry

The future is often uncertain, even when the action is known. For example,
suppose the gripper pushes a cube exactly at its middle. Sometimes the cube
slides to the left, and sometimes it slides to the right, and both of those
happen in the training videos.

A simple model is trained to make its picture as close as possible to the real
one, on average. The safest picture, on average, is a mix of both futures: half
a cube on the left and half a cube on the right. So that is what a simple model
draws instead of one clear future.

![The gripper pushes a cube at its middle; in the data it slides left or right; a simple model draws faint half cubes in both places](../../../images/world-models/video-prediction-models/blurry-future.svg)

The right-hand picture is the average of the two real futures, and it matches
neither of them.

People fix this by letting the model pick one future at a time, and they do that
by giving the model an extra input of random numbers. Different random numbers
then make it draw different, sharp futures: one with the cube on the left, and
one with it on the right. Diffusion models do this naturally, because they start
from random noise. So running the model several times shows several possible
futures, which is more honest than one blurry picture.

### Four ways a robot uses the pictures

A predicted picture does not move the arm by itself, so something has to use it,
and robots use video prediction in the four ways listed below.

1. **To plan.** The robot imagines many action sequences, predicts the pictures
   for each one, and picks the sequence whose final picture looks most like the
   goal. This is the planning method from the
   [previous page](../02_most-used/01_learned-dynamics-models.md#planning-with-it), with pictures
   in place of numbers.
2. **To draw the task, then copy it.** The model draws a short video of the task
   being done, from a sentence such as "put the red cube in the bowl". A second,
   smaller model then works out the arm moves that turn each picture into the
   next. That second model is called an **inverse dynamics model**. It answers
   the opposite question to a world model: not "what happens if I do this?" but
   "what did I do to make this happen?". The picture below shows these steps.
3. **To make training data.** The model draws many videos of a task being done
   in new rooms or with new objects. The actions are read off with an inverse
   dynamics model, and the results are used to train a policy.
4. **As a training signal.** A policy learns to predict future frames while it
   learns to act, and the predicting part is thrown away afterwards. The
   [overview](../01_overview.md#4-three-ways-a-robot-uses-a-world-model) says more.

![A sentence becomes a generated video of the task; an inverse dynamics model reads the arm move from each pair of frames](../../../images/world-models/video-prediction-models/video-then-actions.svg)

The inverse dynamics model turns each pair of frames, such as the one in the
orange box, into one arm command.

---

## 4. How it is trained

The last section described how the model draws a frame, and this section says
where it learns to do that. A video prediction model learns from videos: it sees
the first few frames of a clip, predicts the next ones, and is corrected by the
real next frames. This needs no labels written by people, because the video
itself is the answer, and that is the main attraction of this kind of model.

The videos come from two sources, and most modern models use both.

- **Robot videos with actions.** The robot records its camera and, at the same
  time, the actions it took, so these teach the model what each action does.
  However, they are slow to collect, because a real arm must do every one.
- **Ordinary videos without actions.** Videos of people cooking, cleaning or
  building things show how objects move, fall, pour and fold, and there are vastly
  more of these than robot videos. They teach the model how the world looks and
  moves, even though they carry no robot actions.

A common recipe is to train first on a large amount of ordinary video, and then to
train a little more on robot video with actions, so that the model learns to follow
the arm's commands. Book 3's
[what is changing](../../../03_frameworks/04_one-arm-training/05_what-is-changing.md#world-models)
explains why this matters: robot demonstrations are scarce, and video is not.

Large video models are trained on far more video than any single robot lab could
record, on many graphics cards, for weeks. However, small models for one task,
such as pushing objects on one table, can learn from a few hours of the robot's
own video.

---

## 5. Well-known models of this kind

The models below are all real, published models rather than examples invented
for this page.

- **Finn, Goodfellow and Levine (2016)** trained an action-conditioned model on
  a large set of videos of robot arms pushing objects. It predicts how pixels
  move instead of drawing new ones. It is the starting point for most later work
  on video prediction for robot arms.
- **Visual Foresight** (Finn and Levine, 2017, then Ebert and others, 2018)
  planned pushes with such a model. A person clicks on an object in the picture
  and clicks where it should go. The robot searches for pushes whose predicted
  pictures move the clicked pixel there.
- **SV2P** (Babaeizadeh and others, 2018) added the random input described in
  [why the future comes out blurry](#why-the-future-comes-out-blurry), so that it
  can predict several different sharp futures.
- **UniPi** (Du and others, 2023) draws a video of the task from a sentence, and
  then reads the arm moves off it with an inverse dynamics model.
- **SuSIE** (Black and others, 2023) predicts only one future picture, the next
  subgoal, by editing the current camera picture. A policy then drives the arm
  towards that picture.
- **NVIDIA Cosmos** includes openly downloadable models that predict future
  video. Book 3's
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#43-cosmos)
  document lists them with their licences. NVIDIA's GR00T-Dreams project uses a
  video world model to make synthetic robot training data.

---

## 6. A worked example: sliding a cube to a clicked spot

Here is how Visual Foresight style planning moves a cube to a spot on the table,
step by step. Notice that no part of it measures the cube's position in
centimetres.

1. **Set the goal.** A person looks at the camera picture on a screen. They
   click on the cube, and then click the spot where the cube should end up.
2. **Imagine.** The planner makes up a few hundred short sequences of pushes.
   For each one, the video model predicts the next few pictures.
3. **Score.** In each predicted video, the model also tracks where the clicked
   pixel goes. The score is how close that pixel ends to the target spot.
4. **Act.** The arm does the first push of the best sequence.
5. **Repeat.** The camera takes a new picture, and the planner starts again from
   step 2.

The same arm can push a mug, a toy or a sponge without any change, as long as
objects like them appeared in the training videos, and that is the benefit of
working on pictures. However, the cost is time, because each planning round
needs hundreds of predicted videos, so the arm pauses between pushes.

---

## 7. What goes wrong, and what people do about it

The sections above described this kind of model at its best. This section lists
the five things that go wrong in practice, and what people do about each one.

**Pictures get blurry or wrong further ahead.** Errors add up from frame to
frame, and uncertain futures blur. So people predict only a short time ahead,
replan often, and use models that draw one sharp future at a time.

**Objects change or disappear.** A model may let a cube melt into the table, turn
a red cube orange, or make the gripper pass through an object. This happens
because it learned what videos usually look like, not the rules that objects
must obey. So people check the prediction with other models, keep predictions
short, and train on more robot video of close contact.

**It looks right but the physics is wrong.** A predicted video can look
convincing while the cube moves too far or too little, and for a robot the
distance matters more than the look. The frontier document
[simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#44-world-models-that-actually-shipped-inside-policies)
notes that no published evidence yet shows these models are accurate enough
about contact to plan with.

**It is slow.** A large diffusion model can take seconds or more to draw a short
clip on a powerful computer, which is far too slow for an arm that must react
many times a second. So people use smaller models, predict fewer pixels, or use
the model only during training and not on the robot.

**The camera moves.** If the camera is on the arm's wrist, the whole picture
changes with every move. This is harder to predict than a fixed camera above the
table, so many systems use a fixed camera for that reason.

---

## 8. Why this kind, and what it costs

The last section listed what goes wrong, so this section says when this kind of
model is still worth choosing. The obvious alternative is a
[learned dynamics model](../02_most-used/01_learned-dynamics-models.md)
that works on a few measured numbers, and it is small and fast. However, it
needs a way to measure those numbers, and it cannot describe things that have no
short list of numbers, such as a crumpled towel or a pile of beans.

A video prediction model needs no measurement at all, so it works for any object
the camera can see. It can also learn from ordinary video, which is available in
enormous amounts. That is why the largest companies in the field are building
very large video world models.

What it costs you:

- **Computing power.** Large video models need powerful graphics cards to train
  and to run. Book 3 notes that Cosmos needs substantial NVIDIA hardware.
- **Speed.** Drawing pictures is slow, so planning with them is slow.
- **Trust.** A picture that looks right can be wrong in the details that matter
  to the arm, such as a few centimetres of sliding.
- **Detail you do not need.** The model spends its effort drawing every pixel,
  including the colour of the table and the shadows, which the robot rarely needs.
  [Latent world models](03_latent-world-models.md) avoid this by
  predicting a short code instead of a picture.

---

## 9. The written alternative

This page has assumed all along that the model draws pictures, but a robot can avoid
pictures altogether. So the written alternative measures the object instead of
drawing it. The camera finds the cube with
[thresholding and colour masks](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
, and a written model of pushing predicts how it will move. Book 3's
[quasi-static planar pushing](../../../03_frameworks/02_gripping/09_pushing-and-sliding.md#3-quasi-static-planar-pushing)
is that model. The planning loop in section 6 is written code either way.
[Sampling-based optimisation and model predictive control](../../../05_programming-techniques/06_planning-and-search/03_also-used/02_sampling-based-optimisation-and-mpc.md)
tries many sequences of moves, does the first move of the best one, and plans again.

The written way wins for rigid objects that the camera can measure, because it is
fast and its predictions can be checked. The video model wins when the objects have
no short description, or when one model must handle many kinds of object.

---

## 10. Where to read next

- The [next page](02_learned-simulators.md) covers learned simulators, which
  follow cloth, liquids and other soft materials piece by piece.
- [Latent world models](03_latent-world-models.md) keep the idea of learning
  from pictures but predict a short code, which is much faster.
- [Vision-language-action models](../../07_language-models/02_most-used/01_vision-language-action-models.md)
  are the large robot policies that some video world models are trained
  together with.
- [Tracking and motion](../../03_seeing-models/03_also-used/03_tracking-and-motion.md) explains
  optical flow, which is the "how does each pixel move" idea used by early video
  prediction models.
- For the current state of the field, read Book 3's
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#4-learned-world-models).
---

## 11. Using it in Python

This page has described models that draw the next camera pictures. Of the four kinds in
this chapter, this is the only one you can download ready-made and run today, so this
section shows how. After it you will know how to get a predicted video out of a model,
and, just as importantly, what that video will not tell you.

The model is NVIDIA's Cosmos, from [section 5](#5-well-known-models-of-this-kind), and
the library is `diffusers`, from Hugging Face, which is the same library people use for
picture-drawing models in general. You install it with `pip install diffusers
transformers accelerate torch`. The code below is the Image2World example from the
library's own documentation, with the prompt changed to a robot scene.

```python
import torch
from diffusers import Cosmos2_5_PredictBasePipeline
from diffusers.utils import export_to_video, load_image

pipe = Cosmos2_5_PredictBasePipeline.from_pretrained(
    "nvidia/Cosmos-Predict2.5-2B",
    revision="diffusers/base/post-trained",
    torch_dtype=torch.bfloat16,
)
pipe = pipe.to("cuda")

frames = pipe(
    image=load_image("table.jpg"),   # the one real picture the prediction starts from
    video=None,
    prompt="A robot arm pushes the red cube to the right across the table.",
    num_frames=93,
    generator=torch.Generator().manual_seed(1),
).frames[0]

export_to_video(frames, "prediction.mp4", fps=16)
```

Now read that code against [section 2](#2-what-goes-in-and-what-comes-out), because the
difference matters. The action goes in as a sentence, not as numbers, so this model is
not action-conditioned in the sense that section described. It shows you *a* future that
matches your words, and it cannot show you the future that a particular 3 cm push would
cause. Every openly downloadable video world model in 2026 works this way, and the
action-conditioned models that Visual Foresight planned with are research code from
individual papers, with no package to install. So you can generate video today, and you
cannot plan pushes with it today.

The pretrained model gives you an enormous amount: everything about how objects fall,
slide, bend and cast shadows, learned from more video than you could ever record.

What you write is the sentence, the loop that calls the model, and anything that reads
the predicted frames. That last part is a whole model of its own, because turning
predicted pictures into arm commands needs the inverse dynamics model from
[section 3](#four-ways-a-robot-uses-the-pictures), and nothing above provides one.

What you decide is whether the cost is worth it. The `"cuda"` in the code is not
optional, because this model needs a large NVIDIA graphics card, and one call takes
a long time compared with an arm's control loop. So people use these models to make
training data overnight, not to decide the next push.
