# Learned motion planners

The previous page covered learning by trying, which takes over the part of a
move where the arm touches something. So this page turns to the other part of
the move, which is the long travel through open space. It answers one question:
where can a neural network help an ordinary motion planner move an arm, and
where is it better to leave the planner alone? It covers three kinds of learned
helper, which are networks that plan a whole route, networks that check for
collisions, and networks that work out joint angles.

The page is for a reader who knows what a robot arm and its joints are, and who has
read the [movement models overview](../01_overview.md). You do not need to know how a
motion planner works inside, because section 1 explains just enough of it. Every new
word is explained where it first appears.

The honest summary comes first, because it is the most useful thing on the page.
For moving an arm through open space, an ordinary planner is usually the better
tool, since it is fast enough, it checks every move for collisions, and it is
free. So a learned planner earns its place in a smaller set of jobs, which this
page describes.

> Before this page, it helps to have read [sampling-based
> planning](../../../05_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md),
> which explains the ordinary planner and the collision checker that the networks on
> this page learn from. Section 1 gives just enough of it if you have not.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How a learned route planner works](#3-how-a-learned-route-planner-works)
4. [Learned collision checking](#4-learned-collision-checking)
5. [Learned inverse kinematics](#5-learned-inverse-kinematics)
6. [How they are trained](#6-how-they-are-trained)
7. [Well-known models of this kind](#7-well-known-models-of-this-kind)
8. [A worked example: reaching into a shelf](#8-a-worked-example-reaching-into-a-shelf)
9. [What goes wrong, and what people do about it](#9-what-goes-wrong-and-what-people-do-about-it)
10. [Why this kind, and what it costs](#10-why-this-kind-and-what-it-costs)
11. [The written alternative](#11-the-written-alternative)
12. [Where to read next](#12-where-to-read-next)

---

## 1. What it is

The introduction promised just enough about ordinary planners, so this section
gives it, and then states the idea in one sentence. In short, a learned motion
planner is a network that has studied a large number of answers from an ordinary
planner. So it can give a similar answer much faster, in about the same time
every run.

But first, what is an ordinary planner? A **motion planner** is a program that
finds a
route for the arm from where it is to where it needs to go, without hitting
anything.
A common kind, called a **sampling-based planner**, tries many random arm positions
and throws away the ones that hit something. Then it joins up the good ones until it
has a route from start to goal. But before it accepts any move, it asks a
**collision
checker**, which is a program that tests whether the arm's shape overlaps any
obstacle's shape.

This approach works well. But the time it takes varies, because it usually
answers quickly, while sometimes, in a tight space, it keeps trying random
positions for much longer.

![A sampling planner's time varies a lot from run to run; a learned planner's time is almost the same every run](../../../images/movement-models/learned-motion-planners/time-to-answer.svg)

The picture is a drawing of the idea, and not a measurement. The blue bars show
a sampling planner, where most runs are quick but a few take much longer. The
green bars show a learned planner, where every run takes about the same short
time.

For example, a new taxi driver in a city uses a map and works out each route,
while an experienced driver has driven thousands of routes and just knows which
way to go. So the experienced driver is quicker than the new one. But the
experienced driver can still make a wrong turn in a street that has changed, and
the map can tell them so. A learned planner matches the experienced driver,
while the ordinary planner and collision checker match the map, and they are
still needed to check the answer.

---

## 2. What goes in and what comes out

Section 1 described one learned helper, but there are three kinds, and they take
different inputs and give different outputs. The table below lists them, and you
read each row as one kind of helper.

| Kind | What goes in | What comes out | What it replaces |
| --- | --- | --- | --- |
| Learned route planner | a 3D picture of the scene, the arm's current joint angles, the goal | the next arm position, or a whole route | the search part of a sampling planner |
| Learned collision checker | a set of joint angles, and the scene | "hit" or "clear", or a distance to the nearest obstacle | the exact geometric test, while searching |
| Learned inverse kinematics | where the gripper should be, and which way it should point | one or many sets of joint angles that put it there | an iterative solver |

A **3D picture of the scene** here usually means a point cloud, which is a list
of 3D
dots on every surface a depth camera sees, and the
[point cloud models page](../../04_3d-models/02_most-used/01_point-cloud-models.md) explains these.

---

## 3. How a learned route planner works

The first row of the table was the learned route planner, and it comes in two
main designs. Both of them feed the scene and the goal into a network.

The first design proposes **the next point, over and over**, and here is how
that design goes.

1. A part of the network turns the point cloud into a short list of numbers that
   describes where the obstacles are.
2. The network looks at that description, the current arm position and the goal
   position, and then it suggests the next arm position, which is a short hop
   towards the goal.
3. The arm position moves to that suggestion, and step 2 repeats.
4. It stops when the suggestion reaches the goal.
5. A classical collision checker tests each hop, and if a hop hits something, then
   an ordinary planner finds a replacement for just that hop.

![A network proposes the next point again and again; a checker tests each hop and repairs the one that clips a wall](../../../images/movement-models/learned-motion-planners/next-waypoint.svg)

On the left, the network proposes four points in turn, from the start to the
goal. On the right, the checker passes the green hops, finds that one red hop
clips a wall, and an ordinary planner replaces it with the orange detour.

Step 5 is the important one in that list. The network has learned what good
routes usually look like, but it can be wrong, so the check makes sure a wrong
route never reaches the arm. And because only one short hop needed repairing,
the whole job is still fast.

The second design is a **learned sampler**, which keeps the ordinary planner
exactly as it is. The only change is where the planner picks its random
positions. Instead of spreading them evenly everywhere, a network suggests
positions in the places where routes usually pass, such as the gap between two
shelves. So the planner finds a route sooner, and it still checks everything
itself.

---

## 4. Learned collision checking

The second row of the table was the learned collision checker, and it exists
because a collision check has to run many thousands of times while a planner
searches. Each exact check compares the shapes of every arm link with every
obstacle, which takes time. So a **learned collision checker** is a network that
has seen many arm positions labelled "hit" or "clear", and it gives a quick
guess for a new position.

Some versions give a **distance** instead of "hit" or "clear", which is how far
the arm is from the nearest obstacle. A distance is useful to planners that
improve a route step by step, because it tells them which way to push the route
to get further from obstacles.

To see where this goes wrong, think of a simple arm with two joints and a post
beside it. Each arm position is just two angles, so you can draw every possible
position as one dot on a flat chart. Then the positions where the arm touches
the post form a grey region on that chart.

![A two-joint arm and a post; on a chart of all joint angles, the true collision region and the network's slightly wrong guess of its edge](../../../images/movement-models/learned-motion-planners/wrong-near-the-edge.svg)

The left picture shows two arm positions, one clear and one touching the post.
The right picture shows every position as a dot on a chart of the two joint
angles, where the grey region is where the arm touches the post. The red dashed
line is the network's guess of that region's edge. It is close, but not exact,
so the red dot sits in a place where the network says "clear" when the arm is
really touching.

The network is almost always right far from the edge, and its mistakes are near
the edge. But that is exactly where a planner spends its time when it squeezes
through a gap. So a learned checker is used only to guide the search, and the
exact checker still tests the final route.

---

## 5. Learned inverse kinematics

The third row of the table was learned inverse kinematics, and this section says
what that sum is. **Inverse kinematics**, often shortened to IK, is the sum that
answers "which joint angles put the gripper here, pointing this way?". The
ordinary way to solve it is to start from a guess and improve it step by step,
which is quick for easy targets. But it can be slow or fail for awkward ones,
and the answer you get depends on the starting guess.

Many arms also have more than one correct answer for the same target. An arm
with seven joints, or a flat arm with three joints reaching a point, can reach
that target in many different ways, because it can hold its elbow high or low,
for example.

![A classical solver returns one arm pose; a learned solver returns many poses that all reach the same point](../../../images/movement-models/learned-motion-planners/many-ik-answers.svg)

On the left, a classical solver gives one answer. On the right, a learned solver
gives five different arm poses at once, all putting the gripper on the red star.

A **learned IK solver** is a network trained on many pairs of joint angles and
the gripper positions they produce. The pairs are easy to make, because you pick
random joint angles and work out where the gripper ends up, using the arm's
known sizes. That sum, from angles to gripper position, is called **forward
kinematics**, and it is exact and fast, so the network only has to learn to go
the other way. Some learned solvers, such as IKFlow, give many different answers
at once, drawn from all the ways the arm can reach the target. A planner can
then choose the answer that avoids obstacles or stays far from joint limits.

But the learned answer is usually close rather than exact. So people pass it to
the ordinary solver as a starting guess, and the ordinary solver then finishes
the job in a step or two.

---

## 6. How they are trained

Sections 3 to 5 described three different networks, and all three are trained in
the same basic way. That way has one large advantage, because the training data
is made by a computer, and not collected by people.

1. **Make many scenes.** A program places random boxes, shelves and tables around a
   simulated arm.
2. **Ask the slow, correct method.** An ordinary planner finds a route in each
   scene, or an exact collision checker labels many arm positions, or forward
   kinematics works out gripper positions for many random joint angles.
3. **Save the questions and answers.** Each scene and goal is a question, and the
   planner's route is the answer to it.
4. **Train the network to give the same answers.** Show it a question, compare its
   answer with the saved one, and adjust it a little. Then repeat that many times.

Because a computer makes the data, people can make a great deal of it. Motion
Policy Networks, for example, learned from millions of planner answers, so the
cost here is computing time, and not human time.

But there is a catch in step 1, because the network only learns scenes like the
ones the program made. If the program made boxes on tables, then a real kitchen
with a hanging lamp may confuse it.

---

## 7. Well-known models of this kind

Section 6 described how all of these are trained, and the list below gives the
published models themselves. Each line says what one model is in plain words.

- **MPNet, short for Motion Planning Networks** (University of California, San
  Diego, 2019). This is one of the first learned route planners, and it proposes the
  next point over and over. It then falls back to an ordinary planner when a hop
  fails its collision check.
- **Learned sampling distributions** (Stanford University, 2018). This is a method
  that trains a network to suggest where a sampling planner should try its random
  positions, and the planner itself stays unchanged.
- **Motion Policy Networks** (NVIDIA, 2022). This is a network for a Franka arm that
  takes a point cloud from a depth camera and produces a collision-free route
  directly. It was trained on millions of routes from an ordinary planner in
  generated scenes, and it answers in a fixed time.
- **SceneCollisionNet** (NVIDIA and University of California, Berkeley, 2021). This
  is a network that takes a point cloud and an object's position, and quickly says
  whether the object would hit anything. It was used to plan where to move objects
  when tidying a cluttered table.
- **Fastron** (University of California, San Diego). This is a learning method that
  builds a quick collision guesser for one arm, and updates it as obstacles move.
- **IKFlow** (2022). This is a learned IK solver that gives many different
  joint-angle answers at once, all for the same gripper target.

---

## 8. A worked example: reaching into a shelf

The models in section 7 are general, so this section shows where one of them
would actually earn its place. Suppose a warehouse arm picks items from shelves,
where the shelves are close together and the arm often has to reach into a
narrow gap. The team uses an ordinary sampling planner, which works, but in the
narrowest gaps it sometimes takes over a second to find a route, and the whole
cell waits.

Here is how a learned helper could fit in.

1. The team keeps the ordinary planner and the exact collision checker, so nothing
   is removed.
2. They generate many simulated shelf scenes with different gaps and item places,
   and the ordinary planner solves each one, however long it takes.
3. They train a learned sampler on these solutions, and it learns that routes into a
   shelf all pass through the front of the gap.
4. On the real arm, the planner now picks most of its random positions where the
   sampler suggests, so it finds a route sooner in the narrow gaps.
5. The exact collision checker still tests the final route. If the learned sampler
   is wrong about a strange new shelf, then the planner simply takes longer, as it
   did before, and it does not crash.

Notice that the team did not replace the planner, because they only helped it
with the slow cases. That is the pattern that works best in practice.

And if the shelves were open and wide, then the ordinary planner would answer
quickly every time, so there would be nothing for a network to fix.

---

## 9. What goes wrong, and what people do about it

The worked example kept the ordinary planner in place for a reason, and the
faults below are that reason. Each one is followed by what people do about it.

**It gives no guarantee.** A network can return a route that hits something, or a
collision guess that is wrong near an edge. So people always check the final route
with an exact collision checker, and fall back to an ordinary planner when the check
fails.

**It is confused by unusual scenes.** A scene shaped unlike anything in training can
give a poor answer. So people make the training scenes as varied as they can, and
keep the ordinary planner as a fallback.

**It only works for the arm it learned.** A network trained on one arm's joint
lengths and shape does not work on a different arm. So you have to train again for
each arm you own.

**It is hard to understand when it fails.** An ordinary planner can at least say that
it ran out of time, whereas a network just gives a route. So people log the inputs, so
that they can replay a failure in simulation.

**The ordinary tools keep getting faster.** Planners that run on a graphics card now
find routes quickly for many everyday scenes. So each gain on the classical side
shrinks the gap a learned planner was built to fill, and the
[planning a path document](../../../03_frameworks/03_arm-movement/03_planning-a-path.md#6-planning-on-a-graphics-card-and-replanning-continuously)
describes this.

---

## 10. Why this kind, and what it costs

Section 9 ended with the classical tools getting faster, so this section asks
when a network is still worth adding. The obvious alternative is the ordinary
planner with its exact collision checker and its ordinary IK solver. For most
free-space moves, this is the right choice, because it is free, well tested, and
it checks every move. It also answers quickly for most scenes, and a learned
planner copies it, so it cannot do better than the planner it learned from.

You choose a learned helper only when the ordinary tools are too slow in a way
that matters. Maybe the planning time varies too much for a cell with a strict
cycle time. Or an optimiser needs a smooth distance to obstacles, or a
seven-joint arm needs many IK answers to choose from. In those cases the learned
helper gives a fast first answer, and the ordinary tools then check or finish
it.

What it gives you is speed that stays the same from run to run, and a good first
guess.

What it costs you is a training set, a training run for each arm, and extra
code. On top of that, the ordinary planner and checker have to stay in the
system as well. So the table below sums up the choice. Read each row as a
situation, and the right-hand column as the usual choice.

| Situation | Usual choice |
| --- | --- |
| Open space, and planning is already fast enough | the ordinary planner, with no learning |
| Planning is usually fast, but sometimes far too slow | a learned sampler or learned route planner, with the exact check kept |
| An optimiser needs a smooth distance to obstacles | a learned collision distance, with the exact check on the final route |
| A redundant arm needs many IK answers quickly | a learned IK solver, finished by the ordinary solver |
| The part is always in the same place | a taught, fixed route; no planner at all |

---

## 11. The written alternative

On this page the written alternative is unusually close at hand, because it is the
set of ordinary tools these networks learn from. [Sampling-based
planning](../../../05_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md)
finds the route and checks it for collisions, and [numerical inverse
kinematics](../../../05_programming-techniques/06_planning-and-search/02_most-used/02_numerical-inverse-kinematics.md)
finds the joint angles. When an optimiser needs a smooth distance to obstacles, the
written tool is a distance field, which [volumetric
maps](../../../05_programming-techniques/05_image-and-point-cloud-processing/03_also-used/02_volumetric-maps.md)
explains. Book 3's [planning a
path](../../../03_frameworks/03_arm-movement/03_planning-a-path.md) explains how
these planners behave on a real arm.

So the written tools are better for most moves through free space, and they stay
in the system even when a learned helper is added. A learned helper is better
only when the written tools are too slow, or too uneven in their speed, for the
job.

---

## 12. Where to read next

This page and the previous one both took over one part of an ordinary system. So
the reading below either compares them, or it moves on to the two methods that
supply data and scores instead.

In this chapter:

- [Reinforcement learning policies](01_reinforcement-learning-policies.md) covers
  learning by trying, which suits the contact at the end of a move.
- [Diffusion and flow policies](../02_most-used/03_diffusion-and-flow-policies.md) covers copying a
  person's movements.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Point cloud models](../../04_3d-models/02_most-used/01_point-cloud-models.md) explains how a
  network reads the 3D dots these planners take in.
- [Learned arm models](../../09_touch-and-body-models/03_also-used/02_learned-arm-models.md) covers
  networks that learn the arm's own body.
- [Collision and failure detection](../../09_touch-and-body-models/02_most-used/02_collision-and-failure-detection.md)
  covers noticing a collision that has already happened, which is a different job.

Deeper documents elsewhere in this repository:

- [Learned pieces inside a planned system](../../../03_frameworks/03_arm-movement/05_learned-motion.md#3-learned-pieces-inside-a-planned-system)
  covers the same helpers for a reader who knows planners well.
- [Sampling-based planners](../../../03_frameworks/03_arm-movement/03_planning-a-path.md#2-sampling-based-planners)
  explains the ordinary planner these networks learn from.
- [What collision checking really checks](../../../03_frameworks/03_arm-movement/03_planning-a-path.md#7-the-planning-scene-and-what-collision-checking-really-checks)
  explains the exact check that stays in the system.
- [Redundancy, and the seventh joint](../../../03_frameworks/03_arm-movement/02_reaching-and-reachability.md#6-redundancy-and-the-seventh-joint)
  explains why one gripper target can have many joint answers.
