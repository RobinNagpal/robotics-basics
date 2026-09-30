# The map of techniques

This book describes 24 programming techniques. They have different names, take in
different things and give back different answers. This page is the map of all of
them. It sorts them into seven kinds, which this book calls **categories**. For
each category it says what the techniques do and where to read about them.

It answers three questions. What are the seven categories, and which techniques
are in each? Where does each category do its job when one robot arm does one
task? And in what order should you read the chapters of this book?

It is for a reader who has read the earlier pages of this chapter, especially
[programmed, not learned](01_programmed-not-learned.md). You can also come back
to it at any time, when you want to see where one technique fits among the others.
Book 6 has a page with the same shape for learned models,
[the map of models](../../06_neural-network-models/01_what-models-are/06_the-map-of-models.md).

## Contents

1. [One task, seven kinds of technique](#1-one-task-seven-kinds-of-technique)
2. [The seven categories](#2-the-seven-categories)
   · [Geometry and cameras](#geometry-and-cameras)
   · [Searching and matching](#searching-and-matching)
   · [Fitting and estimation](#fitting-and-estimation)
   · [Image and point cloud processing](#image-and-point-cloud-processing)
   · [Planning and search](#planning-and-search)
   · [Control and motion](#control-and-motion)
   · [Decisions and task logic](#decisions-and-task-logic)
3. [All 24 techniques in one table](#3-all-24-techniques-in-one-table)
4. [When each kind does its job](#4-when-each-kind-does-its-job)
5. [How the categories connect](#5-how-the-categories-connect)
6. [A suggested reading order](#6-a-suggested-reading-order)
7. [Where to read next](#7-where-to-read-next)

---

## 1. One task, seven kinds of technique

The easiest way to see all seven categories is to follow one task. A robot arm
has a camera on its wrist. There are three mugs on a table, and a rack with pegs
at one end. The task is: find the mugs with the wrist camera, and hang each one
on the rack.

To do this, the robot must do several separate things. It must turn what the
camera sees into positions measured from its own base. It must pick the mug
pixels out of the picture and ignore the table. It must find the table top and
keep each mug's position steady while the camera moves. It must decide which mug
is which from one picture to the next. It must find a path to each mug and on to
the rack that hits nothing. It must drive its motors smoothly along that path. And
it must keep track of the whole job: which mug is next, and what to do if a grasp
fails.

Each of these jobs is done by a different kind of technique.

![A robot arm with a wrist camera above three mugs and beside a rack, with seven numbered markers and a legend naming each category of technique](../../images/what-techniques-are/the-map-of-techniques/one-task.svg)

The picture shows the task with the seven categories numbered; each number sits
next to the part of the scene that its techniques work on: the camera, the mugs,
the table top, the mug pixels, the path to the rack, the joints and the task
list.

A real arm does not always use every technique in this book. A simple
pick-and-place arm may use only six or seven of them. But almost every arm task
uses at least one technique from each of the seven categories.

---

## 2. The seven categories

Each category below has one paragraph that says what its techniques do, followed
by a link to the chapter overview. The overview explains each technique in one
line and compares them.

### Geometry and cameras

Geometry and cameras turn pixels, frames and joint angles into positions you can
trust. The
[pinhole camera model](../02_geometry-and-cameras/02_pinhole-camera-model.md)
says which pixel a point in space lands on, and turns a pixel and its depth back
into a point. [Rigid transforms](../02_geometry-and-cameras/03_rigid-transforms.md)
move a position from one frame to another, such as from the camera to the arm's
base. [Calibration](../02_geometry-and-cameras/04_calibration.md) measures the
numbers that the other two need: the camera's own settings, and where the camera
sits on the arm. In the mug task, these techniques turn each mug's pixels into a
position the arm can reach. Read the
[geometry and cameras overview](../02_geometry-and-cameras/01_overview.md).

### Searching and matching

Searching and matching find the closest thing, and decide which thing is which.
[Nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md)
finds the point or object closest to a given one, as in the closest-mug example
on [the first page](01_programmed-not-learned.md#2-a-first-technique-the-closest-mug).
[Iterative closest point](../03_searching-and-matching/03_iterative-closest-point.md)
lines up two sets of points, such as a stored 3D model of a mug and a fresh scan.
[Assignment and matching](../03_searching-and-matching/04_assignment-and-matching.md)
pairs up two lists, such as the mugs seen in this picture and the mugs seen in the
last one. In the mug task, these techniques make sure that "mug 2" in one picture
is still "mug 2" in the next. Read the
[searching and matching overview](../03_searching-and-matching/01_overview.md).

### Fitting and estimation

Fitting and estimation get a clean shape or a steady number out of noisy
measurements. [Least-squares fitting](../04_fitting-and-estimation/02_least-squares-fitting.md)
finds the line, plane or circle that is closest to many points.
[Random sample consensus (RANSAC)](../04_fitting-and-estimation/03_ransac.md)
does the same while
ignoring points that are plainly wrong. The
[Kalman filter](../04_fitting-and-estimation/04_kalman-filter.md) combines each new
reading with what it already knew, to give a steady estimate of something that
may be moving. In the mug task, RANSAC finds the table top, and a Kalman filter
keeps each mug's position steady as the camera moves. Read the
[fitting and estimation overview](../04_fitting-and-estimation/01_overview.md).

### Image and point cloud processing

Image and point cloud processing clean up and cut up pictures and point clouds so
objects stand out.
[Thresholding and colour masks](../05_image-and-point-cloud-processing/02_thresholding-and-colour-masks.md)
keep the pixels whose colour or depth is in a chosen range.
[Morphology and the distance transform](../05_image-and-point-cloud-processing/03_morphology-and-distance-transform.md)
tidy up those pixels, and find the point most central in a shape.
[Edges and contours](../05_image-and-point-cloud-processing/04_edges-and-contours.md)
find the outline of each shape. [Clustering](../05_image-and-point-cloud-processing/05_clustering.md)
groups nearby points into separate objects. In the mug task, a depth threshold
removes the table, and clustering splits the remaining points into one group per
mug. Read the
[image and point cloud processing overview](../05_image-and-point-cloud-processing/01_overview.md).

### Planning and search

Planning and search find a way for the arm to get from here to there without
hitting anything. [Graph search](../06_planning-and-search/02_graph-search.md)
finds the shortest route through a grid or a graph of poses.
[Sampling-based planning](../06_planning-and-search/03_sampling-based-planning.md)
tries random arm poses and joins the safe ones into a path.
[Trajectory optimisation](../06_planning-and-search/04_trajectory-optimisation.md)
takes a path and makes it shorter, smoother and further from obstacles.
[Numerical inverse kinematics](../06_planning-and-search/05_numerical-inverse-kinematics.md)
finds the joint angles that put the gripper at a chosen pose. In the mug task,
inverse kinematics turns "gripper above mug 2" into joint angles, and a planner
finds a path to the rack that does not hit the rack itself. Read the
[planning and search overview](../06_planning-and-search/01_overview.md).

### Control and motion

Control and motion turn a planned path into smooth, safe motor commands.
[Trajectory generation](../07_control-and-motion/03_trajectory-generation.md)
decides how fast to move along the path at each moment, so the arm starts and
stops smoothly. [Proportional-integral-derivative (PID) control](../07_control-and-motion/02_pid-control.md) makes
each joint follow its target angle, many times a second.
[Impedance and force control](../07_control-and-motion/04_impedance-and-force-control.md)
makes the arm give way when it touches something, and stop if it pushes too hard.
In the mug task, these techniques move the arm to each mug, and let it feel the
peg when it hangs the mug on the rack. Read the
[control and motion overview](../07_control-and-motion/01_overview.md).

### Decisions and task logic

Decisions and task logic decide what the robot does next, and in what order. A
[finite state machine](../08_decisions-and-task-logic/02_finite-state-machines.md)
moves the robot from one named step to the next, such as "looking", "picking" and
"hanging". A [behaviour tree](../08_decisions-and-task-logic/03_behaviour-trees.md)
arranges the steps as a tree, which makes it easier to add retries and fallbacks.
[Greedy algorithms and set cover](../08_decisions-and-task-logic/04_greedy-algorithms-and-set-cover.md)
make a good choice quickly by taking the best-looking option at each step.
[Optimisation solvers](../08_decisions-and-task-logic/05_optimisation-solvers.md)
find the best order or assignment when the greedy choice is not good enough. In
the mug task, a state machine runs the job, and a greedy rule picks the closest
mug next. Read the
[decisions and task logic overview](../08_decisions-and-task-logic/01_overview.md).

---

## 3. All 24 techniques in one table

The table below lists every technique page in the book. Read each row across: the
category, the technique, what it does in one line, and what it does in the mug
task. The technique names are links to their pages.

| Category | Technique | What it does | In the mug task |
| --- | --- | --- | --- |
| Geometry and cameras | [Pinhole camera model](../02_geometry-and-cameras/02_pinhole-camera-model.md) | turns a point into a pixel, and a pixel plus its depth into a point | turns a mug's centre pixel and depth into a 3D point |
| Geometry and cameras | [Rigid transforms](../02_geometry-and-cameras/03_rigid-transforms.md) | moves a position from one frame to another | turns the mug's camera position into a base position |
| Geometry and cameras | [Calibration](../02_geometry-and-cameras/04_calibration.md) | measures the camera's settings and where it sits on the arm | done once, before the task, so the first two are right |
| Searching and matching | [Nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md) | finds the closest point or object | finds which mug is closest to the gripper |
| Searching and matching | [Iterative closest point](../03_searching-and-matching/03_iterative-closest-point.md) | lines up two sets of points | lines up a stored mug model with the scan to find the handle |
| Searching and matching | [Assignment and matching](../03_searching-and-matching/04_assignment-and-matching.md) | pairs up two lists at the lowest total cost | matches each mug in this picture to one in the last picture |
| Fitting and estimation | [Least-squares fitting](../04_fitting-and-estimation/02_least-squares-fitting.md) | finds the line, plane or circle closest to many points | fits a circle to a mug's rim to find its centre |
| Fitting and estimation | [RANSAC](../04_fitting-and-estimation/03_ransac.md) | fits a shape while ignoring wrong points | finds the table top, with the mugs ignored |
| Fitting and estimation | [Kalman filter](../04_fitting-and-estimation/04_kalman-filter.md) | combines each new reading with what it knew | keeps each mug's position steady as the camera moves |
| Image and point cloud processing | [Thresholding and colour masks](../05_image-and-point-cloud-processing/02_thresholding-and-colour-masks.md) | keeps pixels in a chosen colour or depth range | keeps the pixels closer than the table |
| Image and point cloud processing | [Morphology and distance transform](../05_image-and-point-cloud-processing/03_morphology-and-distance-transform.md) | tidies a mask, and finds its most central point | removes speckles from the mug mask |
| Image and point cloud processing | [Edges and contours](../05_image-and-point-cloud-processing/04_edges-and-contours.md) | finds outlines and their shapes | traces the outline of each mug in the picture |
| Image and point cloud processing | [Clustering](../05_image-and-point-cloud-processing/05_clustering.md) | groups nearby points into objects | splits the points above the table into three mugs |
| Planning and search | [Graph search](../06_planning-and-search/02_graph-search.md) | finds the shortest route through a graph or grid | finds a route between stored safe poses |
| Planning and search | [Sampling-based planning](../06_planning-and-search/03_sampling-based-planning.md) | tries random poses and joins the safe ones | finds a path round the rack |
| Planning and search | [Trajectory optimisation](../06_planning-and-search/04_trajectory-optimisation.md) | makes a path shorter, smoother and safer | smooths the path from the mug to the peg |
| Planning and search | [Numerical inverse kinematics](../06_planning-and-search/05_numerical-inverse-kinematics.md) | finds joint angles for a gripper pose | finds the joint angles for "gripper above mug 2" |
| Control and motion | [PID control](../07_control-and-motion/02_pid-control.md) | makes a joint follow its target | holds each joint on its planned angle |
| Control and motion | [Trajectory generation](../07_control-and-motion/03_trajectory-generation.md) | decides the speed along a path at each moment | starts and stops the arm smoothly with a full mug |
| Control and motion | [Impedance and force control](../07_control-and-motion/04_impedance-and-force-control.md) | makes the arm give way on contact, and limits force | feels the peg and stops pushing |
| Decisions and task logic | [Finite state machines](../08_decisions-and-task-logic/02_finite-state-machines.md) | moves between named steps | runs look, pick, hang, next mug |
| Decisions and task logic | [Behaviour trees](../08_decisions-and-task-logic/03_behaviour-trees.md) | arranges steps as a tree with fallbacks | tries a second grasp if the first one slips |
| Decisions and task logic | [Greedy algorithms and set cover](../08_decisions-and-task-logic/04_greedy-algorithms-and-set-cover.md) | takes the best-looking option at each step | picks the closest mug next; picks the fewest camera views that see every mug |
| Decisions and task logic | [Optimisation solvers](../08_decisions-and-task-logic/05_optimisation-solvers.md) | finds the best order or assignment | chooses which peg each mug goes on |

A few of these do the same job in two ways. Finite state machines and behaviour
trees both run the task. Least squares and RANSAC both fit shapes. Graph search
and sampling-based planning both find paths. The
[choosing a technique](03_choosing-a-technique.md) page explains how to pick
between them, and each technique page compares itself with its neighbour.

---

## 4. When each kind does its job

The map picture shows where each category works. It is also useful to see when
each one works. The task for one mug can be split into seven steps: look from
above, find the mugs, choose the next mug, plan the reach, reach and grasp, carry
the mug to the rack, and hang it and let go.

![A timeline of seven steps for one mug, with a coloured bar for each category showing the steps in which it is busy](../../images/what-techniques-are/the-map-of-techniques/when-each-runs.svg)

Each coloured bar shows the steps during which one category is busy; decisions
and task logic run for the whole task, perception techniques are busy at the
start, and control is busy from the reach to the end.

Read the picture from left to right. At the start, image and point cloud
processing and geometry turn the camera's pictures into mug positions. Fitting
and searching then tidy those positions and match them to the mugs seen before.
Planning works out the reach. Control then drives the arm for the rest of the
task. Geometry and fitting come back during the grasp, because the camera takes a
closer look as the gripper comes down. Decisions and task logic run from start to
finish, because they decide when every other step begins.

This is one way to build the task, not the only one. A task where the mugs are
always in the same place would not need the perception bars at all. A task where
the arm must avoid people would have planning running during the carry as well.

---

## 5. How the categories connect

The seven categories are separate chapters, but the techniques in them depend on
each other. The output of one is very often the input of the next.

A threshold and clustering cut the mugs out of the depth picture. The pinhole
camera model turns each mug's pixels into points. A rigid transform moves those
points into the base frame. RANSAC and least squares fit the table and the mug's
rim. Nearest-neighbour search and assignment keep track of which mug is which. A
greedy rule chooses the next mug. Inverse kinematics and a planner find the
joint angles and the path. Trajectory generation and PID control drive the
motors. A state machine or behaviour tree runs all of it in order. This chain,
from picture to motors, is the most common way to build a programmed picking
robot.

Many of the categories share the building blocks from
[the building blocks](02_the-building-blocks.md). Planning and decisions both use
graphs. Fitting, planning and optimisation solvers all minimise a cost function.
Geometry and planning both use transforms. So once you know one chapter, the next
one is easier.

The categories also connect to Book 6. Some steps in the chain are often done by
a learned model instead of a written technique. The table below shows the most
common swaps. Read each row as one job: the written technique in this book, and
the kind of learned model that can replace it.

| Job | Written technique (this book) | Learned model (Book 6) |
| --- | --- | --- |
| cut the objects out of the picture | [thresholding](../05_image-and-point-cloud-processing/02_thresholding-and-colour-masks.md), [clustering](../05_image-and-point-cloud-processing/05_clustering.md) | [segmentation](../../06_neural-network-models/02_seeing-models/04_segmentation.md) |
| find where objects are | [edges and contours](../05_image-and-point-cloud-processing/04_edges-and-contours.md) | [object detection](../../06_neural-network-models/02_seeing-models/03_object-detection.md) |
| follow objects between pictures | [assignment and matching](../03_searching-and-matching/04_assignment-and-matching.md), [Kalman filter](../04_fitting-and-estimation/04_kalman-filter.md) | [tracking and motion](../../06_neural-network-models/02_seeing-models/08_tracking-and-motion.md) |
| find an object's pose | [iterative closest point](../03_searching-and-matching/03_iterative-closest-point.md) | [keypoints and object pose](../../06_neural-network-models/02_seeing-models/05_keypoints-and-object-pose.md) |
| find a path | [sampling-based planning](../06_planning-and-search/03_sampling-based-planning.md) | [learned motion planners](../../06_neural-network-models/05_movement-models/06_learned-motion-planners.md) |
| decide the steps of a task | [behaviour trees](../08_decisions-and-task-logic/03_behaviour-trees.md) | [language models as planners](../../06_neural-network-models/06_language-models/02_language-models-as-planners.md) |

Even when a learned model takes over one job, the written techniques around it
usually stay. A detection model gives a box in the picture. The pinhole camera
model and a rigid transform still turn that box into a position the arm can reach.

---

## 6. A suggested reading order

You can read the chapters of this book in any order, because each one explains
its own terms. But some chapters are easier after others. The list below is the
order this book suggests, with the reason for each step.

1. This chapter, starting with [programmed, not learned](01_programmed-not-learned.md).
   Everything else uses its words: technique, parameter, frame, graph, noise, cost
   and loop.
2. [Geometry and cameras](../02_geometry-and-cameras/01_overview.md). Every other
   chapter needs positions in the right frame.
3. [Image and point cloud processing](../05_image-and-point-cloud-processing/01_overview.md).
   Most arm tasks start by finding the objects in a picture.
4. [Fitting and estimation](../04_fitting-and-estimation/01_overview.md). It turns
   noisy pixels and points into clean shapes and steady numbers.
5. [Searching and matching](../03_searching-and-matching/01_overview.md). It keeps
   track of which object is which, once you can find them.
6. [Planning and search](../06_planning-and-search/01_overview.md). It needs
   positions and shapes from the chapters before it.
7. [Control and motion](../07_control-and-motion/01_overview.md). It carries out
   what the planner decided.
8. [Decisions and task logic](../08_decisions-and-task-logic/01_overview.md). It
   ties all the others together into a whole task.

If you have one job in mind, you can jump straight to its chapter. For example, if
you only want the arm to move smoothly to a known pose, read planning and search,
and then control and motion.

---

## 7. Where to read next

- The [geometry and cameras overview](../02_geometry-and-cameras/01_overview.md)
  is the next chapter in the suggested order.
- [The map of models](../../06_neural-network-models/01_what-models-are/06_the-map-of-models.md)
  in Book 6 does the same job for learned models.
- [Programmed methods for one arm](../../03_frameworks/04_one-arm-training/02_programmed-methods.md)
  in Book 3 shows how these techniques are combined into whole systems.
- [Tools and libraries](../../03_frameworks/01_tools-and-libraries.md) in Book 3
  shows the software, such as MoveIt 2, OpenCV and Open3D, that provides many of
  these techniques ready to call.
