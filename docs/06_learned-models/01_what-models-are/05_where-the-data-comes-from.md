# Where the data comes from

A model learns from examples. [Inside a neural network](03_inside-a-neural-network.md)
showed what is inside a neural network,
[learning signals](04_learning-signals.md) showed the kinds of learning, and
[how a model learns](02_how-a-model-learns.md) showed how the numbers inside it are
changed, one example at a time. This document answers the question that comes before
both of them. Where do the examples come from?

It is for a complete beginner. You do not need to know anything about machine
learning. You only need to remember one idea from the earlier documents: a model is
shown many examples, each with a question and the right answer, and it slowly
changes its numbers until its own answers match the right ones.

By the end you will know the five main places that robot data comes from. You will
know what "pretraining", "fine-tuning" and "foundation model" mean. And you will have
a rough idea of how much data each kind of model needs.

## Contents

1. [Why the data matters so much](#1-why-the-data-matters-so-much)
2. [Labelled pictures](#2-labelled-pictures)
3. [Human demonstrations](#3-human-demonstrations)
4. [Simulation](#4-simulation)
   · [The gap between simulation and the real world](#the-gap-between-simulation-and-the-real-world)
   · [Domain randomisation](#domain-randomisation)
5. [Internet-scale data](#5-internet-scale-data)
6. [Self-supervised learning](#6-self-supervised-learning)
7. [Pretraining, then fine-tuning](#7-pretraining-then-fine-tuning)
8. [What a foundation model is](#8-what-a-foundation-model-is)
9. [How much data each kind needs](#9-how-much-data-each-kind-needs)
10. [Why not just collect robot data?](#10-why-not-just-collect-robot-data)
11. [Where to read next](#11-where-to-read-next)

---

## 1. Why the data matters so much

A model only knows what its examples showed it. Suppose every training picture shows
a white mug on a wooden table. The model may then learn "a white thing on brown wood"
instead of "a mug". Show it a blue mug on a grey table, and it can fail.

So the examples must look like the jobs the robot will really do. They must cover
the different colours, shapes, lights and positions the robot will meet. A set of
examples used for training is called a **dataset**.

Each example in a dataset has two parts. The first part is what the model is given,
such as a picture. This is called the **input**. The second part is the right answer,
such as the word "mug". This is called the **label**, or the **target**.

Getting inputs is usually easy. A camera takes thirty pictures every second. Getting
the right answers is the hard part. Somebody, or something, has to supply them. Each
section below is a different way of supplying them.

---

## 2. Labelled pictures

The oldest way is simple. A person looks at each picture and writes down the answer.
This is called **labelling**, or **annotation**, and the person is an **annotator**.

The answer can take several forms, depending on what the model must learn:

- a single word for the whole picture, such as "mug";
- a box drawn around each object, with a name on each box;
- an exact outline of each object, traced pixel by pixel;
- a few marked points, such as the rim and the handle of the mug.

Each form takes longer than the one before. A person can give a word to a picture in
a second or two. Tracing the exact outline of every object in a busy kitchen picture
takes much longer. So outline datasets are usually much smaller than word datasets.

A famous example is ImageNet. It is a dataset of about 1.2 million training
pictures, each labelled with one of 1,000 names, such as "coffee mug" or "golden
retriever". People labelled it by hand. For many years it was the standard test
for models that recognise pictures.

Labelled pictures are how most [seeing models](../03_seeing-models/01_overview.md)
are trained. Their weakness is cost. Every label costs a person's time, and a new
object or a new kind of answer means labelling again.

---

## 3. Human demonstrations

A seeing model answers "what is in this picture?". A
[movement model](../06_movement-models/01_overview.md) answers a different
question: "what should the arm do next?". No one can easily write that answer down
by hand. So instead, a person shows the robot what to do. This is called a
**demonstration**.

The most common way to demonstrate is **teleoperation**. The word means "operating
from a distance". The person does not push the robot itself. They move a controller,
and the robot copies the controller's movements.

A popular kind of controller is a small second arm, called the **leader arm**. It has
the same joints as the real robot, which is called the **follower arm**. The person
moves the leader arm by hand. The computer reads the leader's joint angles many times
a second and sends the same angles to the follower. Other controllers include a
game controller, a virtual reality headset with hand controllers, and a handheld
gripper that the person carries around.

![A person moves a leader arm, the robot copies it, and each moment is saved](../../images/what-models-are/where-the-data-comes-from/teleoperation.svg)

The picture shows one demonstration being recorded. At each moment the computer saves
two things together: what the camera saw, and what the arm did at that moment.

While the person works, the computer records everything at each moment:

1. the pictures from every camera;
2. the angle of every joint;
3. whether the gripper is open or closed;
4. the command that was sent to the arm.

One complete recording of one task, from start to finish, is called an **episode**.
For example, one episode might be "pick up the mug from the left of the table and
put it on the plate". It might last twenty seconds.

Later, a movement model is trained on many episodes. It is shown the picture at each
moment, and the right answer is the command the person gave at that moment. The model
learns to give the same command when it sees a similar picture. Copying a person like
this is called **behaviour cloning**. The
[behaviour cloning page](../06_movement-models/02_most-used/01_behaviour-cloning.md) explains it
in full.

Demonstrations have one big strength. They are real. The pictures come from the
robot's own cameras, and the movements are movements the robot can actually make.

They also have one big weakness. They are slow to collect. A person must sit at the
controller for every episode, and one person can record only so many episodes in a
day. The [data and demonstration document](../../03_frameworks/08_frontier/03_data-and-demonstration.md)
describes the rigs people use and what they cost.

---

## 4. Simulation

A **simulator** is a program that pretends to be the real world. It holds a 3D model
of the robot, the table and the objects. It works out how they move when the robot
pushes them, using the rules of physics. It can also draw what a camera would see.

A simulator can make data very fast. It can run many copies of the same scene at
once. It never gets tired. It never breaks a real mug. And it knows every right
answer for free, because it placed every object itself. It knows exactly where the
mug is, where its handle points and which pixels belong to it. Nobody has to label
anything.

A simulator can also let a robot practise. The robot tries something, the
simulator says whether it worked, and the robot tries again, many thousands of times.
Learning by trying like this is called **reinforcement learning**. The
[reinforcement learning page](../06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
explains it.

### The gap between simulation and the real world

A simulator is never exactly like the real world. Its pictures look a little too
clean. Its light falls a little differently. Its mug slides a little differently
from a real one, because real friction is hard to copy exactly.

A model trained only in simulation learns these small differences as if they were
true. Then it meets the real world and does worse than it did in simulation. The
difference between how a model does in simulation and how it does in the real world
is called the **sim-to-real gap**. "Sim" is short for simulation.

### Domain randomisation

The most common fix is called **domain randomisation**. Here "domain" means the look
and feel of the world the model is trained in. "Randomisation" means changing it at
random.

Instead of making one simulated world as close to the real one as possible, you make
thousands of different ones. In each training picture, the computer picks the table
colour, the mug colour, the brightness of the lamps, the camera position and the
other objects at random. It can also change the weight of the mug and how slippery
the table is.

![Eight simulated pictures with random colours and one real picture](../../images/what-models-are/where-the-data-comes-from/domain-randomisation.svg)

The eight pictures on the left are all simulated, and no two look alike. The real
picture on the right looks different again, but the model has already learned to
ignore colour and light.

The model cannot rely on any one colour or lamp, because they keep changing. The only
thing that stays the same in every picture is the shape of the mug. So the model
learns the shape. To such a model, the real world looks like just one more random
variation.

Domain randomisation has a cost. The model must learn to cope with far more
variety than the real job needs, so it needs more training. It also cannot fix every
difference. Physics that the simulator gets badly wrong, such as cloth or liquids,
stays wrong however much you randomise it. The
[simulation and evaluation document](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md)
describes the other fixes people use today.

---

## 5. Internet-scale data

The internet holds billions of pictures, videos and pages of text. Many of the
pictures come with a few words next to them, such as a caption under a photo or the
text of a web page. Those words are a kind of label that nobody had to write for
the purpose of training.

A well-known model called CLIP (Contrastive Language-Image Pretraining) was trained
on 400 million pairs of pictures and captions collected from the internet. It learned
to match a picture with the words that describe it. It was never told "this is a
mug" in the careful way ImageNet was. It worked it out from millions of loosely
matched pictures and captions. The
[open-vocabulary models page](../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
explains how robots use models like it.

Text alone is also data. Large language models, which the
[language models chapter](../07_language-models/01_overview.md) covers, learned from
huge amounts of text written by people.

Internet data has three strengths. There is an enormous amount of it. It covers
almost every everyday object and word. And it costs little to collect.

It also has weaknesses. It is messy: many captions are wrong or unrelated to the
picture. And it contains almost no robot actions. The internet can show a model what
a mug looks like and what the word "mug" means. It cannot show the model how this
particular arm should move its joints to pick the mug up.

---

## 6. Self-supervised learning

The methods above all need somebody to supply the right answer. A person, a
simulator or a caption writer. **Self-supervised learning** is a trick that makes
the right answer come from the data itself.

Here is one example. Take a picture. Cover some patches of it with grey squares. Ask
the model to guess what was under the grey squares. The right answer is the part of
the picture you covered, so you already have it. No person had to label anything.

To guess well, the model must learn what things usually look like. It must learn
that a mug handle is curved and that a table edge is straight. That knowledge is
useful later for other jobs, such as finding mugs.

Here is a second example, using text. Take a sentence, hide the next word, and ask
the model to guess it. "Put the red mug in the ..." The right answer, "sink", was in
the sentence all along. Large language models learn mainly this way.

A third example uses video. Show the model the first frames of a clip and ask it to
guess the next frame. The real next frame is the right answer.
[World models](../08_world-models/01_overview.md) are often trained like this.

The name "self-supervised" means the data supervises itself. It supplies both the
question and the answer. This matters because it means any picture, any video and
any text can be used, not only the ones a person has labelled.

---

## 7. Pretraining, then fine-tuning

Most models used on robots today are not trained in one go. They are trained in two
steps.

The first step is **pretraining**. A model is trained on a very large, general
dataset, often from the internet and often with self-supervised learning. It learns
general things: what objects look like, what words mean, how things usually move.
Pretraining is expensive. It can use many powerful computers for weeks. Usually a
large company or a research lab does it once, and then shares or sells the result.

The second step is **fine-tuning**. You take the pretrained model, with all the
numbers it has learned, and train it a little more on a small dataset for your own
job. For a robot arm, this small dataset is often a few hundred demonstrations
recorded on your own robot. Fine-tuning changes the numbers only a little. It is
much cheaper than pretraining. It can often run on one computer in hours or days.

![Pretraining on a large general pile of data, then fine-tuning on a small pile of robot data](../../images/what-models-are/where-the-data-comes-from/pretrain-then-fine-tune.svg)

The same network appears twice in the picture. Fine-tuning keeps what pretraining
learned and changes only a small part of it, shown by the red lines.

Why does this work? Because most of what the robot needs is general. Knowing what a
mug looks like, from any angle and in any light, is the same skill for every robot.
Only the last part, how this arm moves to this mug, is special to your robot. So the
expensive general part is learned once, from cheap general data. The cheap special
part is learned from a little expensive robot data.

An everyday example is a person who already speaks English and starts a new job in a
kitchen. They do not need to learn English again. They only need to learn where the
pans are kept and how this kitchen does things. That takes days, not years.

---

## 8. What a foundation model is

A **foundation model** is a large model pretrained on a very large, broad dataset, so
that many different jobs can be built on top of it by fine-tuning or by simply asking
it. The name was made popular by a 2021 report from Stanford University. It is called
a "foundation" because other models and products are built on it, the way a house is
built on its foundation.

CLIP is a foundation model for pictures and words. The large language models behind
chat assistants are foundation models for text. In robotics, people now build
**vision-language-action models**. These take in camera pictures and a spoken or
typed instruction, and give out arm movements. They usually start from a foundation
model for pictures and words, and are then trained further on large collections of
robot demonstrations. The
[vision-language-action models page](../07_language-models/02_most-used/01_vision-language-action-models.md)
explains them. The [foundation models document](../../03_frameworks/08_frontier/02_foundation-models.md)
lists the ones that exist in 2026.

One large robot dataset shows how these collections are built. Open X-Embodiment
gathered more than a million robot episodes from 22 different kinds of robot, which
many labs had recorded separately. Pooling them gave one dataset large enough to
pretrain on.

Being a foundation model does not make a model always right. It only means it
starts from a broad base. It still needs to be tested on your robot, and it still
often needs fine-tuning.

---

## 9. How much data each kind needs

The amount of data a model needs depends on the job and on whether it starts from a
pretrained model. Exact numbers vary a great deal from one model to the next. The
table below gives only rough sizes, to show how the kinds compare. Read each row
across: the kind of data, how much a typical project uses, and what it mostly
trains.

| Kind of data | Rough amount | Mostly trains |
| --- | --- | --- |
| Labelled pictures for a new seeing model, from scratch | hundreds of thousands to millions of pictures | [seeing models](../03_seeing-models/01_overview.md) |
| Labelled pictures to fine-tune a pretrained seeing model on your objects | hundreds to a few thousand pictures | [seeing models](../03_seeing-models/01_overview.md) |
| Demonstrations for one task on one robot | tens to hundreds of episodes | [movement models](../06_movement-models/01_overview.md) |
| Demonstrations to pretrain a general robot model | hundreds of thousands to millions of episodes, from many robots | [vision-language-action models](../07_language-models/02_most-used/01_vision-language-action-models.md) |
| Simulated examples | millions or more, because they are cheap | [grasp models](../05_grasp-models/01_overview.md), [movement models](../06_movement-models/01_overview.md) |
| Internet pictures, captions, text and video | hundreds of millions or more | foundation models for pictures and words |

Two patterns stand out. First, cheap data is used in huge amounts, and expensive data
is used in small amounts. Second, fine-tuning a pretrained model needs far less data
than training from nothing. That is the main reason pretraining is so widely used.

---

## 10. Why not just collect robot data?

The obvious alternative to all of this is simple. Record lots of real demonstrations
on your own robot, and train on nothing else. Real data is exactly right for the real
job, with no sim-to-real gap and no messy captions.

For one narrow task, this does work. Some movement models learn one task, such as
putting a battery into a slot, from about fifty demonstrations recorded on that
robot.

It stops working when you want variety. To handle every mug, every table and every
kitchen, you would need to demonstrate on every one of them. A person can record
only so many episodes in a day. So people mix the sources: internet data and
self-supervised learning for general knowledge, simulation for volume, and real
demonstrations for the final, exact skill.

That mix has its own costs. Pretrained models are large, and large models are slower
to run on a robot. [Running a model on a robot](../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md),
in the last chapter of this book, is about that. You also depend on whoever did the pretraining, and on the licence they chose.
And a model built from many sources is harder to understand when it fails, because
you did not see most of the data it learned from.

---

## 11. Where to read next

- [Running a model on a robot](../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md) is the next
  document. It explains what happens after training, when the model is used.
- [The map of models](06_the-map-of-models.md) shows every kind of model in this book
  and what data each one uses.
- [How a model learns](02_how-a-model-learns.md) explains what the model does with
  each example.
- For much more detail on teleoperation rigs and open robot datasets, read
  [where manipulation data comes from](../../03_frameworks/08_frontier/03_data-and-demonstration.md).
- For simulators and the sim-to-real gap, read
  [simulation, world models and evaluation](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md).
- [Learned methods for one arm](../../03_frameworks/04_one-arm-training/03_learned-methods.md)
  shows how these kinds of data are used to teach one arm a task.
