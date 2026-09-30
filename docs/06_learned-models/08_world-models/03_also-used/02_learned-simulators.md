# Learned simulators

This page explains world models that predict how cloth, rope, dough, liquids
and sand move. Because these materials change shape as they move, a few numbers
cannot describe them. The page answers four questions: how a model can follow a
material that has no fixed shape, what happens inside such a model at each step,
where its training data comes from, and when it is better than a hand-written
physics simulator.

It is written for a reader who has already read the
[world models overview](../01_overview.md) and the page on
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md), so you
should know what a state, an action and a rollout are. It also helps, but is not
needed, to have read
[point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md),
because a learned simulator often starts from a point cloud.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [Turning the material into a graph](#turning-the-material-into-a-graph)
   · [One step: passing messages](#one-step-passing-messages)
   · [Many steps](#many-steps)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
6. [A worked example: folding a towel in half](#6-a-worked-example-folding-a-towel-in-half)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

A learned simulator splits a material into many small pieces, and predicts
where each piece will move next from where its neighbours are.

A **simulator** is a program that calculates how things move, step by step, and
the simulators in Book 3, such as MuJoCo, are written by hand from the laws of
physics. A **learned** simulator does the same job, but a neural network works
out each step. That network learned how to do its job from examples of the
material moving.

Here is an everyday example of the same idea, using a crowd of people leaving a
stadium. Each person only looks at the few people right around them, so they
step forward when there is space and slow down when someone is close in front.
Nobody follows a plan for the whole crowd, and yet the crowd as a whole still
flows through the exits in a sensible way. A learned simulator works in the same
way, because each small piece of the material looks only at its close
neighbours, and the whole material then moves sensibly.

The small pieces are called **particles**, and what one particle stands for
depends on the material. For example, for water or sand each particle stands for
a small drop or a small pile of grains. Instead, for cloth each particle is a
point on the cloth, and neighbouring points are joined by threads in a grid,
called a **mesh**.

---

## 2. What goes in and what comes out

Now that the particles have a name, here is what actually passes in and out. A
learned simulator for a robot arm takes two things in and gives one back.

- **The particles now.** The position of each particle, and how fast it has
  been moving over the last few steps. A towel might be 200 particles, while a
  tray of water might be thousands.
- **What the arm is doing.** The gripper is usually added as a few extra
  particles whose movement is known, because the robot controls it.
- **The output: where every particle will be one small step later.** A step is
  usually a small fraction of a second.

On a real arm, the particles come from a **depth camera**, which measures how far
away each pixel is. That gives a **point cloud**, which is a set of 3D dots on the
surface of the material. The [3D models chapter](../../04_3d-models/01_overview.md)
explains point clouds in full, so this page takes them as given. The simulator then
uses a selection of those dots as its particles.

---

## 3. How it works inside

### Turning the material into a graph

The last section said what the particles are, so this section says what the
model does with them. The first step joins nearby particles together, and two
particles are joined if they are closer than a chosen distance, called the
**connection radius**. For cloth, the threads of the mesh are also kept as
joins.

The result is called a **graph**, which in this sense is not a chart. It is a set of
points, called **nodes**, and the lines that join them, called
**edges**. So a neural network that works on a graph is called a **graph neural
network**, or **GNN**.

![Water in a tray drawn as particles; on the right, each particle is joined to the others close to it, and one particle's neighbours are highlighted](../../../images/world-models/learned-simulators/particles-and-edges.svg)

The red particle is joined only to the orange ones inside the dashed circle, so
only those influence it.

Because particles move and their neighbours change, the graph is built again at
every step.

### One step: passing messages

Each step has three parts, and they happen to every particle at the same
time.

1. **Each neighbour sends a message.** A small network looks at a pair of joined
   particles: their positions and their speeds. It gives back a short list of
   numbers, called a **message**. You can think of the message as "how much this
   neighbour pushes or pulls on me". Nobody tells the network what the message
   should be, because it learns whatever numbers help the prediction.
2. **The particle adds up its messages.** It sums all the messages it received,
   and adds gravity.
3. **It moves a small step.** A second small network turns the sum into a change
   of speed, and the program adds that to the particle's speed and moves the
   particle.

![One particle receives a message from each neighbour, adds them up with gravity, and moves a small step](../../../images/world-models/learned-simulators/message-passing-step.svg)

So every particle does this at once, and then the whole process repeats for the
next step.

Parts 1 and 2 are usually repeated several times within one step before part 3.
Each repeat lets information travel one more join across the graph, so after ten
repeats a particle is influenced by particles up to ten joins away. This is how
a pull on one corner of a towel reaches the far corner.

The same small networks are used for every particle and every pair, and this is
the key idea of the whole design. The model learns one rule for "how neighbours
affect each other", and it does not learn a separate rule for every particle. So
a model trained on a small towel can often run on a bigger towel, which simply
has more particles.

### Many steps

To predict a whole fold or a whole pour, the simulator runs many steps in a row,
feeding each result back in. This is the rollout from the
[learned dynamics models](../02_most-used/01_learned-dynamics-models.md#many-steps-in-a-row)
page. So learned simulators often run hundreds of steps, because each step is short.
Errors add up here too, and section 7 says what people do about it.

---

## 4. How it is trained

The sections above described the model, and this section says where its examples
come from. A learned simulator needs examples of the material moving, with the
position of every particle at every step, and there are two places to get them.

The first place is a **hand-written simulator** that is very accurate but slow.
Engineers already have careful simulators for cloth, fluids and sand, and these
can take a long time to compute each step, but they give the exact position of
every particle. So the learned simulator watches thousands of runs and learns to copy
them: it predicts one step, is compared with the careful simulator's next step,
and is corrected.

The second place to get examples is the **real world** itself. The robot pokes,
pinches or lifts the material while a depth camera records it, and this teaches the
model the real material rather than a simulated one. However, it is harder, because a
camera cannot say which dot in one frame is the same bit of material as which dot in
the next frame. So the training compares the predicted shape with the real shape as a
whole: for each predicted dot, how far is the nearest real dot?

Because the data is cheap, training on simulated runs is common. Then a small
amount of real data is often added, so that the model matches the real
material.

---

## 5. Well-known models of this kind

The models below are all real, published models rather than examples invented
for this page.

- **Interaction Networks** (Battaglia and others, 2016) introduced the idea of
  predicting how objects move from messages between pairs of objects. Most later
  learned simulators build on it.
- **DPI-Net** (Li and others, 2019) applied the idea to particles of rigid
  objects, soft objects and fluids, and used it to plan how to manipulate soft
  objects.
- **Graph Network-based Simulators**, or **GNS** (Sanchez-Gonzalez and others,
  2020), learned to simulate water, sand and a sticky, goo-like material from a
  careful simulator. It showed that one simple design works for very different
  materials.
- **MeshGraphNets** (Pfaff and others, 2021) works on meshes, such as cloth
  flapping in wind. Its authors reported that it ran faster than the careful
  simulator it learned from.
- **RoboCraft** (Shi and others, 2022) and **RoboCook** (Shi and others, 2023)
  used learned particle simulators on real robot arms to shape plasticine and
  dough. RoboCook used several tools to make dumplings.
- **VCD** (Lin and others, 2021) learned a graph model of the visible part of a
  cloth and used it to plan how to smooth a crumpled cloth.

---

## 6. A worked example: folding a towel in half

Here is how a learned simulator helps an arm fold a small towel, step by
step.

1. **See the towel.** A depth camera above the table gives a point cloud of the
   towel. The program picks about 200 of those dots as particles and joins
   neighbours into a mesh.
2. **Choose candidate moves.** A fold is a pick and a place: grab a point on the
   towel, lift it, and put it down somewhere else. The planner makes up many
   candidates, such as "grab the left corner and put it on the right corner".
3. **Simulate each one.** For each candidate, the learned simulator runs the
   gripper particles along the move and predicts the towel's shape at the end.
4. **Score each one.** The goal is a towel folded neatly in half, so the score
   compares each predicted shape with that goal shape.
5. **Do the best move.** The arm grabs the chosen corner and moves it.
6. **Look again.** The camera takes a new point cloud, and if the fold is not
   neat, the planner runs again from the real shape.

![A towel lying flat, then predicted with one corner lifted, then predicted folded in half](../../../images/world-models/learned-simulators/cloth-fold-prediction.svg)

These are the simulator's predictions at three moments during one planned fold,
before the arm has moved at all.

In principle a hand-written simulator could do step 3 too. However, it would
need the towel's
stiffness, weight and friction, which nobody has measured. Instead, the learned
simulator learned how this kind of towel behaves from watching it.

---

## 7. What goes wrong, and what people do about it

The sections above described the model when it works. This section lists the
five things that go wrong in practice, and what people do about each one.

**Errors add up over hundreds of steps.** Water can slowly lose volume, and
cloth can slowly stretch. So people add small random changes to the particle
positions during training, and the model then learns to correct small errors
instead of making them bigger.

**The camera cannot see every part.** When a towel is folded, the bottom layer is
hidden under the top, and a point cloud shows only the top. So people keep track
of particles from earlier frames, or they model only what the camera can see, as
VCD does. The [shape completion](../../04_3d-models/03_also-used/01_shape-completion.md) page
covers guessing the hidden part of an object.

**Many particles make it slow.** A tray of water with thousands of particles and
hundreds of steps is a lot of work for every candidate move. So people use
fewer, larger particles and plan only a few candidate moves.

**Rigid objects need care.** A metal cup made of particles may slowly bend,
because nothing in the network forces it to stay rigid. So some models treat
rigid objects separately, and they move all of an object's particles together.

**New materials break it.** A model trained on cotton towels may not know how a
silk scarf moves. So people train on a range of materials, or they give each
particle a few numbers describing the material.

---

## 8. Why this kind, and what it costs

The last section listed what goes wrong, so this section weighs those problems
against the alternatives. The obvious alternative is a **hand-written simulator** for
cloth or fluids, and such simulators do exist and are very accurate, as long as they
are given the right material numbers. However, for a real towel or real dough nobody
knows those numbers, and the simulator also cannot easily start from a real point
cloud. A learned simulator instead starts from the point cloud and learns the real
material's behaviour, and it is often faster. Because it is a neural network, a
program can also work out how a small change in the move would change the result.
This lets a planner improve a move step by step, instead of only trying moves at
random.

The second alternative is a [video prediction model](01_video-prediction-models.md),
which also needs no material numbers of any kind. However, it predicts pictures, and a
picture of a towel does not say where each part of the towel is in 3D. A robot
needs 3D positions to grab a corner, and the particles of a learned simulator
give it those positions directly.

What it costs you:

- **A good 3D view.** You need a depth camera and a way to turn its point cloud
  into particles.
- **Training data for your material.** Usually a careful simulator and some real
  recordings.
- **Computing time.** Many particles and many steps for each candidate move.
- **Limited reach.** It knows the materials it was trained on, and it struggles
  with parts it cannot see.

---

## 9. The written alternative

This page has argued for learning the simulator, so the last question is when a
written one is enough. So the written alternative is a hand-written physics
simulator, given the right material numbers. Book 3's
[the simulators](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#2-the-simulators)
describes the ones people run. Book 5's
[system identification](../../../05_programming-techniques/04_fitting-and-estimation/03_also-used/01_system-identification.md)
explains how to measure the numbers inside a physical model from the real thing. It
works when there are a few numbers, such as a joint's friction or a finger's
stiffness. That page itself notes that cloth, soft objects and tangled cables have no
small set of numbers that fits.

So the written simulator wins for rigid objects and for materials whose numbers are
known, while the learned simulator wins for a real towel or real dough. In both
cases, the planning in section 6 is written code, of the kind
[sampling-based optimisation and model predictive control](../../../05_programming-techniques/06_planning-and-search/03_also-used/02_sampling-based-optimisation-and-mpc.md)
explains.

---

## 10. Where to read next

- The [next page](03_latent-world-models.md) covers latent world models, which
  predict a short code instead of particles or pictures.
- [Point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md) explain the 3D
  dots that a learned simulator starts from.
- [Scene reconstruction](../../04_3d-models/02_most-used/02_scene-reconstruction.md) covers
  building a whole 3D scene from pictures.
- [Touch sensing models](../../09_touch-and-body-models/03_also-used/01_touch-sensing-models.md)
  cover the sense that tells a gripper how soft a material is when it holds it.
- For the hand-written simulators that learned simulators are compared with,
  read Book 3's
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#2-the-simulators).
