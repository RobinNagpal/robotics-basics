# Point cloud models

This page is about neural networks that read a point cloud directly, so it answers
three questions. How can a model take in a list of 3D points that has no order, and
what does it give back to a robot arm? And when is it better than turning the points
into a picture and using an ordinary image model?

It is for a reader who has read the [chapter overview](../01_overview.md), which
explains what a point cloud is. You should also know, from
[inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md),
that a network is made of layers that turn a list of numbers into another list of
numbers.

> Before this page, it helps to have read [clustering](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md), which splits a point cloud into objects with written rules and thins it onto small cubes called voxels. This page shows what a trained model adds.

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
   · [5.1 PointNet](#51-pointnet)
   · [5.2 PointNet++](#52-pointnet)
   · [5.3 MinkowskiEngine and spconv](#53-minkowskiengine-and-spconv)
   · [5.4 Point Transformer V3](#54-point-transformer-v3)
   · [5.5 Sonata](#55-sonata)
   · [5.6 How to choose](#56-how-to-choose)
6. [A worked example: picking a mug from a cluttered table](#6-a-worked-example-picking-a-mug-from-a-cluttered-table)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than an image model, and what it costs](#8-why-this-rather-than-an-image-model-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

Since the overview explained what a point cloud is, this section says what a model
does with one. A point cloud model is a neural network that takes a list of 3D
points and says what they are.

For example, imagine someone gives you a sheet of paper with 1,000 rows. Each row
has three numbers, which are the `x`, `y` and `z` of one spot on some object.
The rows are in a random order, and your job is to say whether the object is a mug,
a bottle or a book. A person would plot the dots first and then look at the shape.
But a point cloud model has to do the same job without plotting anything, because it
only has the numbers.

---

## 2. What goes in and what comes out

The sheet of paper in the last section is close to what the model really gets. A
point cloud model takes in one point cloud, and each point in it has at least three
numbers, which are `x`, `y` and `z`. Some models also take the colour of each
point, as three more numbers for red, green and blue.

Before the cloud goes in, the software usually cuts it down to a fixed number of
points, such as 1,024 or a few thousand. It does this by picking points spread
evenly over the cloud, because a full depth camera shot has far more points than a
model needs.

What comes out depends on the job, and there are two common jobs.

- **Classification** gives one name for the whole cloud, such as "mug", together
    with a number between 0 and 1 that says how sure the model is.
- **Segmentation** gives a name to every single point, so on a table scene each
    point is marked "mug", "box" or "table". On a single object, each point can be
    marked with a part name instead, such as "handle" or "body", and that is called
    **part segmentation**.

The picture below shows segmentation on a small table scene.

![A table scene before and after every point gets a name](../../../images/3d-models/point-cloud-models/a-label-on-every-point.svg)

On the left the model sees only positions, so every dot looks the same. On the right
every dot has a name, shown here as its colour.

For a robot arm, segmentation is usually the more useful of the two jobs. Once the
arm knows which points are the mug, it can work out where the mug is, how big it is,
and where to put its fingers.

---

## 3. How it works inside

The random order of those rows is the first thing the design has to deal with, so
this section starts there.

### The problem of order

An image model can rely on order, because pixel number 5 in a row is always next to
pixel number 4 and pixel number 6. A point cloud has no such order, since the camera
driver can list the points in any order it likes and it is still the same scene.

![The same five points in two different orders](../../../images/3d-models/point-cloud-models/order-does-not-matter.svg)

List A and list B hold the same five dots in a different order, and a point cloud
model must give the same answer for both.

An ordinary network cannot do that, because it treats the first number in its input
list differently from the second. So if you fed it list A and then list B, it would
see two different inputs and could give two different answers. That means a point
cloud model needs a design that ignores order altogether.

### One small network for every point, then the largest number

The first model that solved this well is called **PointNet**, and researchers at
Stanford University published it in 2017. It is explained here because every later
model on this page reuses its two ideas, and [section 5.1](#51-pointnet) says why you
should read it rather than run it. It works in four steps.

1. Take one point, as its three numbers.
2. Pass it through a small network, which turns those three numbers into a longer
    list of numbers. In the real PointNet this list has 1,024 numbers, while the
    picture uses four so that you can read them.
3. Do the same for every other point, with **the same** small network, so that every
    point now has its own list of numbers.
4. Look along each position in those lists and keep only the largest number, which
    is called **max pooling**. The result is one list for the whole cloud.

A last small network then turns that one list into the answer, such as "mug".

![Every point goes through the same network, then the largest number in each column is kept](../../../images/3d-models/point-cloud-models/shared-network-then-max.svg)

Each row is one point's list of numbers, and the red numbers are the largest in each
column, which become the list for the whole cloud.

Step 4 is the step that removes order, because the largest number in a column is the
same whichever row it sits in. So if you shuffle the points, the rows move but the
red numbers stay the same.

Each number in the lists comes to stand for some small feature of shape. One number
might come out large for points on a curved surface, while another might come out
large for points far from the middle. Nobody chooses these features, because the
network learns them during training. The largest value in a column then says that
somewhere in this cloud there is a point with this feature.

For segmentation, PointNet goes one step further and sticks the list for the whole
cloud onto each point's own list. Each point then knows about itself and about the
whole shape, so a last small network can give each point its name.

### Looking at neighbours

PointNet has one weakness, which is that each point goes through the small network
alone and never looks at the points right next to it. So PointNet is poor at small
details, such as the thin gap between a handle and the side of a mug.

Instead, **PointNet++**, from the same group later in 2017, fixes this by looking at
small groups of points first. [Section 5.2](#52-pointnet) recommends it, and explains
that you usually meet it inside a grasp model rather than calling it yourself.

![Small groups of nearby points, then bigger groups made from those](../../../images/3d-models/point-cloud-models/small-neighbourhoods.svg)

On the left, each red centre looks only at the dots inside its small circle, while on
the right the groups are grouped again to cover a larger area.

It works in rounds, and in each round it does three things.

1. Pick a number of centre points, spread out over the cloud.
2. For each centre, collect the points within a small distance of it.
3. Run a small PointNet on just that group, which gives one list of numbers for the
    whole group.

The next round then uses the centres of those groups as its points, with a bigger
distance. So the model first learns the shape of small patches, then of larger parts,
and then of the whole object. This is the same pattern that image models use when
they look at small patches of pixels first. The
[seeing models chapter](../../03_seeing-models/03_also-used/01_image-classification.md)
describes that pattern for pictures.

### Two other ways in

Besides PointNet and its neighbour groups, two other designs are common today.

The first cuts space into small cubes called **voxels**, where a voxel is simply a 3D
pixel. The model marks each cube that has a point in it and then works on the grid of
cubes. Most cubes in a room are empty air, so the model only computes on the cubes
that hold points. That trick is called **sparse convolution**, and it is fast on
large scenes. [Section 5.3](#53-minkowskiengine-and-spconv) recommends the two
libraries that people run it with.

The second design uses **attention**, which is a way for each point to look at other
points and decide which of them matter to it most. It is the same idea that language
models use to decide which words in a sentence matter to each other. Point
Transformer models use it on groups of nearby points.
[Section 5.4](#54-point-transformer-v3) recommends the current one, Point Transformer
V3, which reaches its neighbours by sorting the points into an order rather than by
searching for them.

---

## 4. How it is trained

Whichever of those designs a model uses, it learns from point clouds that people
have already labelled. For classification, each example is a whole cloud with one
name, while for segmentation each example is a cloud with a name on every point. Most
of that data comes from one of three places.

- **Collections of 3D shapes made on a computer**, such as ModelNet40 and ShapeNet,
    where ModelNet40 has about 12,000 shapes in 40 kinds such as chairs, cups and
    aeroplanes. Software then samples points from the surface of each shape to make a
    cloud.
- **Scans of real rooms**, such as ScanNet, which has more than a thousand scans of
    indoor rooms made with a depth camera, and people marked each part of each scan
    by hand.
- **Simulation**, where a robot team places 3D models of its own objects in a
    simulated bin and makes a simulated depth camera look at them. The simulator
    knows which object every point came from, so the labels cost nothing.

All three of those places need somebody to label the points first, and there is a
fourth route that does not. A model can be trained on unlabelled clouds, by giving it
a task whose answer is already in the cloud, and then it needs only a few labelled
clouds of yours to finish the job. [Section 5.5](#55-sonata) recommends Sonata, which
is a Point Transformer V3 trained that way.

Training itself works as in
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md). The model
guesses the names first. Then the training program compares them with the right
names and adjusts the network a little so that the next guess is closer. This whole loop
repeats many thousands of times before the model is any good.

One more step in training makes a large difference to the result. The program turns
each cloud
by a random angle, moves it a little, and shakes each point by a small random amount.
This teaches the model that a mug turned sideways is still a mug, and it also
prepares the model for the noise a real depth camera adds.

---

## 5. Well-known models

The designs above appear in real code under real names, and this section is the
shortlist. It says what each one is best at, what it costs you, and what to type to
run it.

Read the table as a first pass, then read the sub-section for the one or two you are
considering. The left column names the model and says how current it is. The right
column holds everything that decides between them: what the model is best at, how big
the download is, what its licence allows, and when to pick it. Read the download part
carefully, because several of these ship code with no trained weights at all, and a
model with no weights is a model you have to train yourself. Every licence below was
read from the project's own licence file.

| Model | What decides it |
| --- | --- |
| [PointNet](https://github.com/charlesq34/pointnet), historical | It gives one name to one object that has already been cut out of the scene. The download is code only, because no weights were released, and the licence is MIT. Pick it when you are learning how these models work. |
| [PointNet++](https://github.com/charlesq34/pointnet2), most used in 2026 | It names one object and its parts, from a few thousand points. The download is code only, because no weights were released, and the licence is MIT. Pick it when the grasp model you want already contains it. |
| [MinkowskiEngine](https://github.com/NVIDIA/MinkowskiEngine) and [spconv](https://github.com/traveller59/spconv), most used in 2026 | They carry whole rooms and full bins, of hundreds of thousands of points. What you download is a library rather than a model, under MIT for MinkowskiEngine and Apache-2.0 for spconv. Pick them when speed on a large cloud decides the job. |
| [Point Transformer V3](https://github.com/Pointcept/PointTransformerV3), most used in 2026 | It puts a name on every point of a room scan. The ScanNet checkpoint is 554 MB, and the code is MIT licensed. Pick it when accuracy on a whole scene matters most. |
| [Sonata](https://github.com/facebookresearch/sonata), worth betting on | It does the same job with far fewer labels of your own. The download is 434 MB, with about 108 million learned numbers, and the code is Apache-2.0 while the weights are CC BY-NC 4.0. Pick it when you have few labelled clouds and no product to ship. |

### 5.1 PointNet

PointNet is **historical**, and it is on this list because every later model here
reuses the two ideas in
[section 3](#one-small-network-for-every-point-then-the-largest-number). Charles Qi
and colleagues at Stanford University published it at the 2017 Computer Vision and
Pattern Recognition conference, usually written CVPR. It is the one shared small
network per point, followed by max pooling.

The obvious alternative is its own successor, PointNet++, and you should normally use
that instead. There is one case for plain PointNet: it does no neighbour search at
all, so it is the only model here that runs at a sensible speed on an ordinary
processor with no graphics card, and on a single object already cut out of the scene
it is often accurate enough.

What it costs you is detail. Because no point ever sees its neighbours, PointNet
cannot tell a thin handle from the side of a mug, and that is the fault you will meet
first. The code is MIT licensed, but no weights for everyday objects were released, so
you have to train it. The original repository will not run on a current install, since
its own instructions say it was tested with Python 2.7, TensorFlow 1.0.1 and CUDA 8.0.

PyTorch Geometric supplies the pieces, as `MLP` for the small network and
`global_max_pool` for the pooling step.

```python
import torch
from torch_geometric.nn import MLP, global_max_pool

pos = torch.rand(1024, 3)                      # one cloud of 1,024 points
batch = torch.zeros(1024, dtype=torch.long)    # every point belongs to cloud 0

# The same small network runs on every point on its own, turning each point's
# three numbers into 1,024 numbers.
per_point = MLP([3, 64, 64, 1024])(pos)

# Keep the largest number in each of those 1,024 columns. This is the step that
# makes the answer the same whatever order the points arrive in.
cloud = global_max_pool(per_point, batch)      # one row of 1,024 numbers

# A last small network turns that row into one score per object kind.
scores = MLP([1024, 512, 40], norm=None)(cloud)
```

The library gives you the layers and the pooling. You supply everything else: the
labelled clouds, the training loop, and the step that cuts each object out of the
scene before it reaches this code. The `batch` vector is not an optional detail,
because it is how PyTorch Geometric tells one cloud from another when you pass
several at once.

### 5.2 PointNet++

PointNet++ is **most used in 2026**, although usually not by you directly, because it
sits inside grasp models that you call instead. The same Stanford group posted it in
June 2017. It adds the rounds of neighbour grouping described in
[section 3](#looking-at-neighbours), and each round picks centre points, collects the
points near each centre, and runs a small PointNet on each group.

The obvious alternative is Point Transformer V3 in section 5.4, which is more accurate
on scenes. Pick PointNet++ for two reasons. The first is that your input is one object
rather than a room, and with a few thousand points grouping is cheap while the extra
machinery of a transformer buys little. The second is practical: Contact-GraspNet and
several other grasp models were built on PointNet++, so if you use one of them, as the
[six-DOF grasps page](../../05_grasp-models/02_most-used/01_six-dof-grasps.md)
describes, you are already running it and the choice is made.

One other design from those years is worth recognising by name.
[DGCNN](https://github.com/WangYueFt/dgcnn) finds each point's neighbours again at
every layer, in the space of learned features rather than in metres, which makes it
good at naming the parts of a single object. Its repository last changed in 2022, so
read about it rather than build on it.

What it costs you is time that grows faster than the number of points. The two slow
steps are picking spread-out centres, which is called farthest point sampling, and
collecting the points within a distance of each centre. Both compare points against
other points, so doubling the cloud more than doubles the work, and that is why people
cut the cloud down first and why section 5.3 exists. The code is MIT licensed. There
is no `pip install pointnet2`, no released weights for your objects, and the original
repository needs TensorFlow 1.

PyTorch Geometric supplies the one round, which the PointNet++ paper calls set
abstraction, out of `fps`, `radius` and `PointNetConv`.

```python
import torch
from torch_geometric.nn import MLP, PointNetConv, fps, radius

class SetAbstraction(torch.nn.Module):
    """One PointNet++ round: pick centres, group neighbours, run a PointNet."""

    def __init__(self, ratio, r, nn):
        super().__init__()
        self.ratio, self.r = ratio, r
        self.conv = PointNetConv(nn, add_self_loops=False)

    def forward(self, x, pos, batch):
        idx = fps(pos, batch, ratio=self.ratio)        # keep a fraction of the
                                                       # points, spread out
        row, col = radius(pos, pos[idx], self.r, batch, batch[idx],
                          max_num_neighbors=64)        # neighbours within r metres
        edge_index = torch.stack([col, row], dim=0)
        x_dst = None if x is None else x[idx]
        x = self.conv((x, x_dst), (pos, pos[idx]), edge_index)
        return x, pos[idx], batch[idx]                 # fewer points, richer features

# A first round over 20 cm neighbourhoods, keeping half the points.
layer = SetAbstraction(0.5, 0.2, MLP([3, 64, 64, 128]))
```

The library gives you the sampling, the neighbour search and the grouping. You supply
the stack of rounds, the head that produces names, the training data, and the radius
for each round. That radius is in metres, so it is the one number you must set from
the real size of your objects.

### 5.3 MinkowskiEngine and spconv

Sparse convolution is **most used in 2026** whenever the cloud is a whole room or a
full bin, and these two libraries are how people run it. Both do the same thing: they
cut space into small cubes, called voxels, and do convolution only on the cubes that
contain points. MinkowskiEngine comes from Chris Choy and NVIDIA, with its paper at
CVPR 2019, and spconv is a separate library that installs from `pip` in a build that
matches your CUDA version. These are libraries rather than single models, so you pick
a network, such as the MinkUNet family, and run it on top.

The obvious alternative is the neighbour grouping of PointNet++. Voxels win on large
clouds because they make the neighbour question free: a cube knows which cubes are
next to it from their addresses alone, so there is no distance search at all, while
PointNet++ must search every time. That one difference is why sparse convolution
carries scans of whole rooms and grouping does not.

What it costs you starts with the voxel size, which you choose and which sets the
finest detail the network can ever see: anything thinner than one cube disappears
before the network starts. Then there is the install, which is the usual place this
goes wrong. Both libraries compile CUDA code against your exact PyTorch version.
MinkowskiEngine's repository last changed in March 2024, so building it against a
current PyTorch and CUDA is now the common failure, and the host that its own example
downloads pretrained weights from no longer answers. spconv is the better-maintained
of the two, it is Apache-2.0 rather than MIT, and Point Transformer V3 in the next
sub-section is built on it, so you may end up installing it anyway.

MinkowskiEngine's own `examples/indoor.py` names every point of an indoor scan with a
MinkUNet34C trained on ScanNet.

```python
import numpy as np, open3d as o3d, torch
import MinkowskiEngine as ME
from examples.minkunet import MinkUNet34C

model = MinkUNet34C(3, 20).cuda().eval()      # 3 colour channels in, 20 names out
model.load_state_dict(torch.load("weights.pth"))

cloud = o3d.io.read_point_cloud("room.ply")
coords = np.asarray(cloud.points)
colors = torch.from_numpy(np.asarray(cloud.colors)).float() - 0.5

voxel_size = 0.02                             # 2 cm cubes, so 2 cm is the limit
field = ME.TensorField(
    features=colors,
    # Dividing by the voxel size turns metres into cube numbers.
    coordinates=ME.utils.batched_coordinates([coords / voxel_size],
                                             dtype=torch.float32),
    quantization_mode=ME.SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE,
    device="cuda")

with torch.no_grad():
    out = model(field.sparse())               # one row per occupied cube
    names = out.slice(field).F.argmax(dim=1)  # back to one name per point
```

The library gives you the grouping of points into cubes, the convolution that skips
empty space, and the `slice` call that maps each cube's answer back onto the original
points. You supply the network and its weights, and because of the broken download
above you should expect to train on your own labelled scans. You also supply the 20
names, because this network was trained on ScanNet's furniture classes, such as wall,
floor, chair and table, which are not the objects on a workbench.

### 5.4 Point Transformer V3

Point Transformer V3, written PTv3, is **most used in 2026** when the job is to put a
name on every point of a scene and accuracy decides the job. The Pointcept group
posted it in December 2023 and presented it at CVPR 2024. Its idea is to stop
searching for neighbours. Instead it sorts the points along a path that visits space
in a fixed order, so that a run of points in the sorted list is a patch of space, and
then it applies attention within each run.

The obvious alternative is sparse convolution from section 5.3, and PTv3 itself uses
spconv internally for its first layer, so this is not a choice between two worlds. The
reason to go further is that attention lets each point weigh its neighbours
differently, while a convolution applies the same fixed pattern everywhere. The
numbers the authors report are the argument. Against their own earlier Point
Transformer V2, PTv3 reports three times the processing speed and ten times the
memory efficiency, while the area each point can draw from grows from 16 points to
1,024. On the ScanNet validation set the Pointcept model zoo reports 77.6 for PTv3,
measured as mean intersection over union, which is a score out of 100 for how well
the named points overlap the right answer.

What it costs you is set-up work. There is no `pip install`, because the authors ship
PTv3 as files you copy into your project. It needs spconv, and for its full speed it
needs the FlashAttention package, which needs CUDA 11.6 or newer; without it you must
turn attention's fast path off and reduce the patch size, and it gets slower. The code
is MIT licensed. The weights are the catch: the repository's own model zoo carries a
note that the released weights are temporarily invalid because the model structure
was changed, so if you want working weights today, use Sonata in section 5.5.

There is no package to install, so you copy two things into your project.

```bash
git clone https://github.com/Pointcept/PointTransformerV3.git
cp PointTransformerV3/model.py my_project/
cp -r PointTransformerV3/serialization my_project/
```

Then the model takes a plain dictionary rather than a tensor.

```python
import torch
from model import PointTransformerV3

model = PointTransformerV3(in_channels=6).cuda().eval()   # x, y, z plus r, g, b

point = {
    "coord": coord,          # (N, 3) positions in metres, on the GPU
    "feat": feat,            # (N, 6) the six numbers per point
    "grid_size": 0.02,       # the voxel size, as in section 5.3
}
with torch.inference_mode():
    out = model(point)       # out.feat holds one feature vector per point
```

The code gives you the sorting, the attention and the encoder and decoder around them.
What comes back is a feature vector per point, not a name, so you supply the last small
layer that turns features into your own names and the labelled scans to train it. You
also supply `offset` or `batch` when you pass more than one cloud, since with neither
of them the model assumes a single cloud.

### 5.5 Sonata

Sonata is **worth betting on**, because it attacks the shortage of labelled 3D data
that [section 8](#8-why-this-rather-than-an-image-model-and-what-it-costs) names as
the biggest cost of this whole family. Pointcept and Meta published it at CVPR 2025.
It is not a new design: it is a PTv3 that has been trained on unlabelled point clouds
by giving it a task that needs no labels, and what you download is that trained
encoder.

The obvious alternative is to train PTv3 yourself on your own labelled clouds.
Sonata wins when you do not have many, which is the normal situation. Its repository
ships a demo in which a single extra layer on top of the frozen model names the points
of a ScanNet scan, and that is the shape of the work you would do: train one small
layer instead of a whole network. It is also, today, the easiest way to get working
PTv3 weights at all.

What it costs you is the licence, and this is the detail to read twice. The code is
Apache-2.0 from Meta, so the code is not the problem. The weights are released under
Creative Commons Attribution-NonCommercial 4.0, because the data sets they were
trained on forbid commercial use. So Sonata is for research and for deciding whether
this approach works for you, and not for a product you sell. The checkpoint is 434 MB
with about 108 million learned numbers, and a smaller one of 155 MB is published as
well. Like PTv3 it prefers FlashAttention, and without it you pass
`enable_flash=False` and a smaller patch size.

The `sonata` package downloads the weights for you from Hugging Face.

```python
import torch
import sonata

model = sonata.model.load("sonata", repo_id="facebook/sonata").cuda().eval()
transform = sonata.transform.default()   # the same preparation used in training

# Each value is a NumPy array with one row per point.
point = {"coord": coord, "color": color, "normal": normal}

point = transform(point)                 # thins onto a grid and scales the colours
for key, value in point.items():
    if isinstance(value, torch.Tensor):
        point[key] = value.cuda(non_blocking=True)

with torch.inference_mode():
    out = model(point)                   # one feature vector per surviving point
```

The package gives you the download, the preparation pipeline and the encoder. You
supply the normals, which Open3D can estimate with `estimate_normals`, and the layer
on top. One detail will confuse you otherwise: `transform` thins the cloud onto a 2 cm
grid, so the features come back for the surviving points rather than for every point
you passed in, and the pipeline keeps an `inverse` entry so that you can map them
back.

### 5.6 How to choose

Start with Sonata, which gives you a trained Point Transformer V3 and the only
working weights in this list, and put a small layer of your own on top of it.

Four things change that choice.

- **You are shipping a product.** Sonata's weights forbid commercial use. Then take
  PTv3 or a MinkUNet on spconv, both of which have permissive code licences, and
  train the weights yourself on your own labelled scans.
- **You want grasps, not names.** Do not choose a point cloud model at all. Use a
  grasp model from the
  [grasp models chapter](../../05_grasp-models/01_overview.md); it contains a
  PointNet++ and you never touch it.
- **The cloud is large and the time budget is tight.** Sparse convolution on voxels
  is the safest answer, because its cost follows the number of occupied cubes rather
  than the number of points, and you control that with the voxel size.
- **You are learning, or you have no graphics card.** Read PointNet, run it on single
  objects on an ordinary processor, then read PointNet++. You will understand every
  other model on this list afterwards.

One warning about speed, because it is the question everybody asks first. This page
gives no frames-per-second figures, because such a number depends on the graphics
card, the number of points and the voxel size together, so a figure measured on
someone else's machine will mislead you. The only safe comparison is a relative one
measured by the same people on the same hardware, which is why the PTv3 figures above
are given against PTv2 and nothing else. Measure on your own card, with your own cloud
size, before you commit.

---

## 6. A worked example: picking a mug from a cluttered table

Those models are easier to judge once one of them runs in a real job. An arm has a
depth camera on its wrist, and a mug, a box and a few other things stand on a table.
The job is to pick up the mug.

1. The arm moves its camera above the table and takes one depth shot, and the
    software turns that shot into a point cloud of about 300,000 points.
2. The software cuts the cloud down to the region over the table and picks about
    20,000 points spread evenly over it.
3. A segmentation model gives every point a name, and about 1,500 points come back
    as "mug".
4. The software takes only the mug points, whose average position is roughly the
    middle of the mug, while the highest mug point gives the height of the rim.
5. A part segmentation model, or a second pass of the same model, marks which mug
    points are the handle, so the arm now knows which way the handle points.
6. The mug points go to a grasp model, which picks a place for the fingers, and the
    [grasp models chapter](../../05_grasp-models/01_overview.md) takes over from
    there.

The numbers in this example are only there to make the steps concrete, because the
real counts depend on the camera and on how far away it is.

---

## 7. What goes wrong

That example assumed the points were there to be named, and four things go wrong when
they are not.

**Missing points.** A depth camera often gets no reading on shiny, dark or
see-through surfaces, so a glass has almost no points and the model has almost
nothing to name. People fix this in two ways. They predict depth for those pixels with a model from
[depth from pictures](../../03_seeing-models/03_also-used/02_depth-from-pictures.md),
or they build the scene from many photos, as on the
[scene reconstruction page](02_scene-reconstruction.md).

**The back is missing.** The camera only sees one side, so the mug points are a half
shell rather than a whole mug. That means the average of those points is nearer the
camera than the real middle of the mug, and the
[shape completion page](../03_also-used/01_shape-completion.md) is about this problem.

**A different sensor.** A model trained on clean shapes made on a computer can do
badly on real, noisy clouds. A model trained on one depth camera can also do badly on
another, because each camera has its own kind of noise. The usual fix is to train
with added noise and then to fine-tune on a few hundred labelled clouds from the real
camera. Here **fine-tuning** means training an already trained model a little more on
new data.

**Objects it has never seen.** A model trained on 40 kinds of object only knows
those 40 names, so a new kind of object gets one of the old names. The
[3D feature maps page](../03_also-used/02_3d-feature-maps.md) describes one way around
this, which is borrowing names from an image model that has learned many thousands of
words.

---

## 8. Why this rather than an image model, and what it costs

Since those limits are real, it is worth saying plainly what this kind buys you. A
point cloud model **is** a network that names a cloud of 3D points, or names every
point in it. It **does** give a robot arm the object's points directly in 3D, in the
same metres the arm moves in.

The obvious alternative is to leave the depth camera's output as a picture. This is
because a depth camera gives a grid of distances that looks just like a photo with
one number per pixel. You can feed that grid, together with the colour photo, to an ordinary
image model such as a
[segmentation model](../../03_seeing-models/02_most-used/02_segmentation.md), and
then turn the chosen pixels into points afterwards.

So why choose a point cloud model instead? There are three reasons, and they all
come from working in metres rather than in pixels.

- A point cloud does not depend on where the camera is in the same way, because a
    mug seen from close up covers many pixels while the same mug seen from far away
    covers only a few. In a point cloud it is the same size in metres in both cases.
- You can merge several point clouds into one, since two cameras, or one camera at
    two places, give two clouds that fit together in the same room. Two pictures
    taken from different places cannot simply be added together like that.
- Many grasp models expect points, so giving them points from a point cloud model
    saves one conversion step.

What it costs you comes in three parts, and the first of them is the biggest.

- There is far less labelled 3D data than labelled photo data, because image models
    learn from hundreds of millions of photos while the biggest 3D sets are much
    smaller. So an image model often knows many more kinds of object.
- It depends completely on the depth camera, so where the depth camera fails the
    point cloud model has nothing to work with.
- It needs a graphics card for large clouds, and a step that cuts the cloud down
    first.

So in practice many robot systems do both of these. They run an image model on the
colour photo
to find and name the object, and then they use the depth points inside its outline.
So a point cloud model is the better choice when shape matters more than colour or
printed labels, for example when parts in a bin all look alike.

---

## 9. The written alternative

Book 5 finds objects in a point cloud with a written recipe instead, the one that
Book 2's section 1.6 describes.
[RANSAC](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/02_ransac.md),
a method that fits a shape when many of the points belong to something else, finds
the table plane so that it can be removed. Then
[clustering](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
groups the points that are left into one cluster per object. The recipe needs no
labelled clouds, and it works on objects the robot has never seen. The point cloud
model wins when objects touch, as they do in a full bin, because clustering merges
touching objects and nothing in it can fix that. It also wins when the robot must
name the parts of an object, such as a handle.

---

## 10. Where to read next

- [Shape completion](../03_also-used/01_shape-completion.md) is the next page, and it
    deals with the missing back of the object.
- [Six-DOF grasps](../../05_grasp-models/02_most-used/01_six-dof-grasps.md) shows
    grasp models that are built on point cloud models.
- [Programmed methods, section 1.6](../../../02_perception/02_object-perception/03_programmed-methods.md#16-point-clouds-remove-the-plane-then-cluster)
    in Book 2 finds objects in a point cloud without any learning, so read it to see
    what a point cloud model has to beat.
- [The one-box project](../../../02_perception/01_camera/03_one-box-intro.md) makes a
    real point cloud from a depth camera.
