# Point cloud models

This page is about neural networks that read a point cloud directly. It answers
three questions. How can a model take in a list of 3D points that has no order? What
does it give back to a robot arm? And when is it better than turning the points into
a picture and using an ordinary image model?

It is for a reader who has read the [chapter overview](../01_overview.md), which
explains what a point cloud is. You should also know, from
[inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md), that
a network is made of layers that turn a list of numbers into another list of
numbers.

> Before this page, it helps to have read [clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md), which splits a point cloud into objects with written rules and thins it onto small cubes called voxels. This page shows what a trained model adds.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
   · [The problem of order](#the-problem-of-order)
   · [One small network for every point, then the largest number](#one-small-network-for-every-point-then-the-largest-number)
   · [Looking at neighbours](#looking-at-neighbours)
   · [Two other ways in](#two-other-ways-in)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: picking a mug from a cluttered table](#6-a-worked-example-picking-a-mug-from-a-cluttered-table)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than an image model, and what it costs](#8-why-this-rather-than-an-image-model-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

A point cloud model is a neural network that takes a list of 3D points and says what
they are.

Here is an everyday example. Imagine someone gives you a sheet of paper with 1,000
rows. Each row has three numbers: the `x`, `y` and `z` of one spot on some object.
The rows are in a random order. Your job is to say whether the object is a mug, a
bottle or a book. A person would plot the dots first and then look at the shape. A
point cloud model has to do the same job without plotting anything. It only has the
numbers.

---

## 2. What goes in and what comes out

A point cloud model takes in one point cloud. Each point has at least three numbers:
`x`, `y` and `z`. Some models also take the colour of each point, as three more
numbers for red, green and blue.

Before the cloud goes in, the software usually cuts it down to a fixed number of
points, such as 1,024 or a few thousand. It does this by picking points spread evenly
over the cloud. A full depth camera shot has far more points than a model needs.

What comes out depends on the job. There are two common jobs.

- **Classification** gives one name for the whole cloud, such as "mug", with a
  number between 0 and 1 that says how sure the model is.
- **Segmentation** gives a name to every single point. On a table scene, each point
  is marked "mug", "box" or "table". On a single object, each point can be marked with
  a part name instead, such as "handle" or "body". That is called
  **part segmentation**.

The picture shows segmentation on a small table scene.

![A table scene before and after every point gets a name](../../../images/3d-models/point-cloud-models/a-label-on-every-point.svg)

On the left, the model sees only positions, so every dot is the same. On the right,
every dot has a name, shown here as its colour.

For a robot arm, segmentation is usually the more useful job. Once the arm knows which
points are the mug, it can work out where the mug is, how big it is, and where to put
its fingers.

---

## 3. How it works inside

### The problem of order

An image model can rely on order. Pixel number 5 in a row is always next to pixel
number 4 and pixel number 6. A point cloud has no such order. The camera driver can
list the points in any order it likes, and it is still the same scene.

![The same five points in two different orders](../../../images/3d-models/point-cloud-models/order-does-not-matter.svg)

List A and list B hold the same five dots in a different order, and a point cloud
model must give the same answer for both.

An ordinary network does not do this. It treats the first number in its input list
differently from the second. If you fed it list A and then list B, it would see two
different inputs and could give two different answers. A point cloud model needs a
design that ignores order.

### One small network for every point, then the largest number

The first model that solved this well is called **PointNet**. It was published in 2017
by researchers at Stanford University. It works in four steps.

1. Take one point, as its three numbers.
2. Pass it through a small network. The network turns the three numbers into a longer
   list of numbers. In the real PointNet this list has 1,024 numbers; the picture
   uses four so that you can read them.
3. Do the same for every other point, with **the same** small network. Every point
   now has its own list of numbers.
4. Look along each position in those lists and keep only the largest number. This is
   called **max pooling**. The result is one list for the whole cloud.

A last small network turns that one list into the answer, such as "mug".

![Every point goes through the same network, then the largest number in each column is kept](../../../images/3d-models/point-cloud-models/shared-network-then-max.svg)

Each row is one point's list of numbers, and the red numbers are the largest in each
column, which become the list for the whole cloud.

Step 4 is the step that removes order. The largest number in a column is the same
whichever row it sits in. So if you shuffle the points, the rows move, but the red
numbers stay the same.

Each number in the lists comes to stand for some small feature of shape. One number
might come out large for points on a curved surface. Another might come out large for
points far from the middle. Nobody chooses these features. The network learns them in
training. The largest value in a column then says "somewhere in this cloud there is a
point with this feature".

For segmentation, PointNet goes one step further. It sticks the list for the whole
cloud onto each point's own list. Each point then knows about itself and about the
whole shape. A last small network gives each point its name.

### Looking at neighbours

PointNet has a weakness. Each point goes through the small network alone. It never
looks at the points right next to it. So PointNet is poor at small details, such as
the thin gap between a handle and the side of a mug.

**PointNet++**, from the same group later in 2017, fixes this by looking at small
groups of points first.

![Small groups of nearby points, then bigger groups made from those](../../../images/3d-models/point-cloud-models/small-neighbourhoods.svg)

On the left, each red centre looks only at the dots inside its small circle; on the
right, the groups are grouped again to cover a larger area.

It works in rounds. In each round it does three things.

1. Pick a number of centre points, spread out over the cloud.
2. For each centre, collect the points within a small distance of it.
3. Run a small PointNet on just that group. The result is one list of numbers for the
   group.

The next round uses the centres of the groups as its points and uses a bigger
distance. So the model first learns the shape of small patches, then of larger parts,
and then of the whole object. This is the same pattern that image models use when they
look at small patches of pixels first. The
[seeing models chapter](../../02_seeing-models/03_also-used/01_image-classification.md) describes it
for pictures.

### Two other ways in

Two other designs are common today.

The first cuts space into small cubes, called **voxels**. A voxel is a 3D pixel. The
model marks each cube that has a point in it and then works on the grid of cubes.
Most cubes in a room are empty air. So the model only computes on the cubes that hold
points. This is called **sparse convolution**, and it is fast on large scenes.

The second design uses **attention**. Attention is a way for each point to look at
other points and decide which of them matter to it most. It is the same idea that
language models use to decide which words in a sentence matter to each other. Point
Transformer models use it on groups of nearby points.

---

## 4. How it is trained

A point cloud model learns from point clouds that people have already labelled. For
classification, each example is a whole cloud with one name. For segmentation, each
example is a cloud with a name on every point.

Most of this data comes from three places.

- **Collections of 3D shapes made on a computer**, such as ModelNet40 and ShapeNet.
  ModelNet40 has about 12,000 shapes in 40 kinds, such as chairs, cups and aeroplanes.
  Software samples points from the surface of each shape to make a cloud.
- **Scans of real rooms**, such as ScanNet, which has more than a thousand scans of
  indoor rooms made with a depth camera. People marked each part of each scan by hand.
- **Simulation.** A robot team can place 3D models of its own objects in a simulated
  bin and make a simulated depth camera look at them. The simulator knows which object
  every point came from, so the labels are free.

Training works as in
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md). The model
guesses the names. The training program compares them with the right names and
adjusts the network a little so the next guess is closer. This repeats many thousands
of times.

One more step makes a large difference. During training, the program turns each
cloud by a random angle, moves it a little, and shakes each point by a small random
amount. This teaches the model that a mug turned sideways is still a mug. It also
prepares the model for the noise a real depth camera adds.

---

## 5. Well-known models

These are real models that you will see named in robot papers and code.

- **PointNet** (2017) was the first widely used network that reads points directly.
  It uses one shared small network and max pooling, as described above.
- **PointNet++** (2017) adds groups of neighbouring points at several sizes. It is
  still a common part inside robot grasp models. Contact-GraspNet, from the
  [six-DOF grasps page](../../04_grasp-models/02_most-used/01_six-dof-grasps.md), is built on it.
- **DGCNN**, short for dynamic graph convolutional neural network (2019), links each
  point to its nearest neighbours and learns from the differences between them. It
  finds new neighbours at each layer, based on what the layer has learned.
- **MinkowskiEngine** (2019) is a library for sparse convolution on voxels. Many models
  for large indoor scenes are built with it.
- **Point Transformer** (2021) and **Point Transformer V3** (2024) use attention on
  groups of nearby points. They are among the strongest models on scans of rooms.

---

## 6. A worked example: picking a mug from a cluttered table

An arm has a depth camera on its wrist. A mug, a box and a few other things stand on a
table. The job is to pick up the mug.

1. The arm moves its camera above the table and takes one depth shot. The software
   turns it into a point cloud of about 300,000 points.
2. The software cuts the cloud down to the region over the table and picks about
   20,000 points spread evenly over it.
3. A segmentation model gives every point a name. About 1,500 points come back as
   "mug".
4. The software takes only the mug points. Their average position is roughly the
   middle of the mug. The highest mug point gives the height of the rim.
5. A part segmentation model, or a second pass of the same model, marks which mug
   points are the handle. Now the arm knows which way the handle points.
6. The mug points go to a grasp model, which picks a place for the fingers. The
   [grasp models chapter](../../04_grasp-models/01_overview.md) takes over from here.

The numbers in this example are only there to make the steps concrete. The real
counts depend on the camera and on how far away it is.

---

## 7. What goes wrong

**Missing points.** A depth camera often gets no reading on shiny, dark or
see-through surfaces. A glass has almost no points, so the model has almost nothing to
name. People fix this by predicting depth for those pixels with a model from
[depth from pictures](../../02_seeing-models/03_also-used/02_depth-from-pictures.md), or by building
the scene from many photos, as on the
[scene reconstruction page](02_scene-reconstruction.md).

**The back is missing.** The camera only sees one side. The mug points are a half
shell, not a whole mug. The average of those points is nearer the camera than the real
middle of the mug. The [shape completion page](../03_also-used/01_shape-completion.md) is about this
problem.

**A different sensor.** A model trained on clean shapes made on a computer can do
badly on real, noisy clouds. A model trained on one depth camera can do badly on
another, because each camera has its own kind of noise. The usual fix is to train with
added noise, and then to fine-tune on a few hundred labelled clouds from the real
camera. **Fine-tuning** means training an already trained model a little more on new
data.

**Objects it has never seen.** A model trained on 40 kinds of object only knows those
40 names. A new kind of object gets one of the old names. The
[3D feature maps page](../03_also-used/02_3d-feature-maps.md) describes one way around this: borrowing
names from an image model that has learned many thousands of words.

---

## 8. Why this rather than an image model, and what it costs

A point cloud model **is** a network that names a cloud of 3D points, or names every
point in it. It **does** give a robot arm the object's points directly in 3D, in the
same metres the arm moves in.

The obvious alternative is to leave the depth camera's output as a picture. A depth
camera gives a grid of distances, which looks just like a photo with one number per
pixel. You can feed that grid, with the colour photo, to an ordinary image model such
as a [segmentation model](../../02_seeing-models/02_most-used/02_segmentation.md). Then you turn the
chosen pixels into points afterwards.

Why choose a point cloud model instead? There are three reasons.

- A point cloud does not depend on where the camera is in the same way. A mug seen from
  close up covers many pixels. Seen from far away, it covers only a few. In a point
  cloud it is the same size in metres in both cases.
- You can merge several point clouds into one. Two cameras, or one camera at two
  places, give two clouds that fit together in the same room. Two pictures from
  different places cannot simply be added together.
- Many grasp models expect points. Giving them points from a point cloud model avoids
  one conversion step.

What does it cost you?

- There is far less labelled 3D data than labelled photo data. Image models learn from
  hundreds of millions of photos. The biggest 3D sets are much smaller. So an image
  model often knows many more kinds of object.
- It depends completely on the depth camera. Where the depth camera fails, the point
  cloud model has nothing.
- It needs a graphics card for large clouds, and a step that cuts the cloud down first.

In practice, many robot systems do both. They run an image model on the colour photo
to find and name the object, and then use the depth points inside its outline. A point
cloud model is the better choice when shape matters more than colour or printed
labels, for example when parts in a bin all look alike.

---

## 9. The written alternative

Book 5 finds objects in a point cloud with a written recipe, the one Book 2's
section 1.6 describes. [RANSAC](../../../05_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md), a method that fits a shape when many of
the points belong to something else, finds the table plane so that it can be
removed. [Clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md) then groups the points that are left into one
cluster per object. The recipe needs no labelled clouds, and it works on objects
the robot has never seen. The point cloud model wins when objects touch, as in a
full bin, because clustering merges touching objects and nothing in it can fix
that. It also wins when the robot must name the parts of an object, such as a
handle.

---

## 10. Where to read next

- [Shape completion](../03_also-used/01_shape-completion.md) is the next page. It deals with the
  missing back of the object.
- [Six-DOF grasps](../../04_grasp-models/02_most-used/01_six-dof-grasps.md) shows grasp models that are
  built on point cloud models.
- [Programmed methods, section 1.6](../../../02_perception/02_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster)
  in Book 2 finds objects in a point cloud without any learning. Read it to see what a
  point cloud model has to beat.
- [The one-box project](../../../02_perception/01_camera/03_one-box-intro.md) makes a real
  point cloud from a depth camera.
