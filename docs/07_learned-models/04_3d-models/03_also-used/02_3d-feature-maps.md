# 3D feature maps

This page is about 3D maps that carry meaning. In a plain point cloud each point only
says where a surface is. In a 3D feature map, each point also says what kind of thing
it is part of. That means the arm can ask in words where the handle of the mug
is, and get back a place in 3D. So the page answers three questions. Where does the
meaning come from, and how does it get into 3D? And when is a map like this worth
building, instead of simply asking an image model about the latest photo?

It is for a reader who has read the [chapter overview](../01_overview.md) and
[scene reconstruction](../02_most-used/02_scene-reconstruction.md). It also helps to
have read
[open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md),
because this page uses the same image models, such as CLIP. The page explains what it
needs from them.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
   · [5.1 F3RM](#51-f3rm)
   · [5.2 LERF](#52-lerf)
   · [5.3 ConceptFusion](#53-conceptfusion)
   · [5.4 ConceptGraphs](#54-conceptgraphs)
   · [5.5 GraspSplats](#55-graspsplats)
   · [5.6 OpenScene](#56-openscene)
   · [5.7 How to choose](#57-how-to-choose)
6. [Where to read next](#6-where-to-read-next)

---

## 1. What it is

Since the introduction promised a map that carries meaning, this section says what
that means exactly. A 3D feature map is a 3D map in which every point stores a list of
numbers describing what the point is part of. That means the map can be searched by
meaning rather than by position.

For example, a floor plan of a shop shows where the walls and shelves are, which is
like a plain point cloud. Now write a label on every shelf, such as "milk", "bread"
and "soap". You can then find the bread by reading the labels, without knowing its
position in advance. A 3D feature map does the same for the space around a robot arm,
except that its labels are lists of numbers rather than words. That lets it answer
questions in words nobody wrote down in advance, such as "something to drink from".

![Each point keeps its position and also carries a list of numbers](../../../images/3d-models/3d-feature-maps/numbers-on-every-point.svg)

Each circled point has its `x`, `y` and `z`, and also a list of numbers that says what
kind of thing it belongs to.

A list of numbers like this is called a **feature**, which is where the page gets its
name, and a real feature has a few hundred numbers in it. Two points on similar
things, such as two mug handles, have similar lists. But two points on different
things, such as a handle and a table, have very different lists.

---

## 2. What goes in and what comes out

A feature map is built once and then asked many times, so the two halves are worth
separating. To **build** the map, three things go in.

- Photos of the scene from several places.
- The camera pose for each photo, and usually a depth picture too. On an arm with a
    wrist camera, the joint readings give the poses, as on the
    [scene reconstruction page](../02_most-used/02_scene-reconstruction.md#step-1-know-where-each-photo-was-taken).
- An image model that has already been trained, such as CLIP or DINO, because the map
    borrows all of its meaning from that model.

What comes out is the map itself, which is a point cloud, or a fitted scene like a
NeRF, where every point has its feature.

To **use** the map, only one thing goes in, and that is a question, usually a few
words such as "the handle" or "the red cup". What comes out is a score for every
point, which says how well that point matches the words. The arm then takes the points
with the highest scores as its answer.

---

## 3. How it works inside

### Step 1: a list of numbers for every pixel

All the meaning in the map comes from an image model, and two kinds of image model are
common.

**CLIP**, short for contrastive language–image pretraining, is a model with two parts.
One part turns a picture into a list of numbers, while the other part turns some words
into a list of numbers of the same length. It was trained so that a picture and a
sentence describing it get similar lists, which is why a photo of a mug and the word
"mug" end up close together. The
[open-vocabulary models page](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
explains this in more detail.

**DINO** is instead an image model that learned from photos alone, with no words. Its
lists are very good at saying that two pixels are on the same kind of part, such as
two mug handles. But it cannot compare those lists with words.

CLIP gives one list for a whole picture, while a map needs one list for every pixel.
So the map builder has two choices. It either uses a version of the model made to
give a list for each small patch of the picture, or it runs the model on many small
crops of the photo and gives each pixel the lists of the crops it falls in.
[F3RM](#51-f3rm) takes the first route and [ConceptFusion](#53-conceptfusion) takes the
second, cutting the crops out with a segmentation model. F3RM can also use DINO's lists
in place of CLIP's, and section 5.1 says how.

### Step 2: lift the lists into 3D

Now that every pixel of every photo has a list, the next step puts those lists onto
points in 3D.

![Two photos of the same spot give two lists, and the 3D map stores their average](../../../images/3d-models/3d-feature-maps/from-pictures-to-3d.svg)

The same spot on the handle shows up in both photos, so the map stores one point for
it, with the average of its two lists.

There are two ways to do this, and the first is **fusion**, which works directly on
point clouds.

1. Use the depth picture to turn each pixel into a 3D point, as for any point cloud.
2. Give that point the pixel's own list.
3. When the same spot shows up in another photo, average the new list with the old
    one.

Averaging helps because the image model makes small mistakes that differ from photo to
photo, which means the average over many views is steadier than any single view.
[ConceptFusion](#53-conceptfusion) in section 5.3 is the plainest example of this route,
and [OpenScene](#56-openscene) in section 5.6 does the same to a finished room scan.

Fusion does not have to end with one list per point.
[ConceptGraphs](#54-conceptgraphs), which section 5.4 recommends for anything larger than
a table, merges the points of each object it finds and keeps a single list for that whole
object, together with a note of where the object sits relative to the others. A room then
holds a few hundred lists rather than a few hundred thousand.

The second way is a **feature field**, and it works like a NeRF from the
[scene reconstruction page](../02_most-used/02_scene-reconstruction.md). A NeRF answers
what colour any spot is, while a feature field also answers what list of numbers that
spot has. It is fitted in the same way, because the program draws the lists from a
camera pose, compares them with the image model's lists for the real photo, and then
adjusts. Copying what one model knows into another model in this way is called
**distillation**. [LERF](#52-lerf) in section 5.2 is where this route became well known,
and [F3RM](#51-f3rm) in section 5.1 is the version built for a robot arm.

A feature field does not have to be built on a NeRF. The same scene reconstruction page
describes **3D Gaussians**, which store a scene as many soft coloured blobs and fit much
faster than a NeRF, and a blob can carry a list of numbers just as a point can.
[GraspSplats](#55-graspsplats) in section 5.5 builds its map that way, which is why
section 5.7 points to it for scenes the robot keeps changing.

### Step 3: ask with words

Once the map holds its lists, the software does three things to ask a question.

1. Give the words, such as "handle", to the text part of CLIP, which gives back one
    list.
2. Compare that list with the list of every point in the map, which gives one number
    per point. That number is high when the two lists are alike.
3. Colour the points by that number, or simply keep the points that score highest.

![The same map asked two different questions](../../../images/3d-models/3d-feature-maps/ask-with-a-word.svg)

The same map answers "handle" with the handle and "where to drink from" with the rim,
and nobody labelled either part in advance.

The map was built only once, so after that each new question is quick, because it is
only one comparison per point.

---

## 4. How it is trained

Because the meaning is borrowed, most 3D feature maps need no new training of their
own, and all the learning sits in the image model they borrow from.

That image model was trained long before, on a huge collection of pictures. CLIP was
trained on about 400 million pictures with captions, collected from the internet, and
no robot data was involved at all. So the map builder simply uses what CLIP already
learned.

The map itself is then built for one scene, in one of the two ways in section 3.
Fusion needs no fitting at all, because it only averages, while a feature field is
fitted like a NeRF, which takes seconds to minutes on a graphics card.

So there are three stages in all, and only the first is training in the usual sense.

1. Train the image model once, on internet pictures, although someone else has usually
    done this already.
2. Build the map for this scene.
3. Ask as many questions of it as you like.

---

## 5. Well-known models

This section names the systems that build a 3D feature map and let you ask it questions,
and it says plainly which of them you can install. Only one is published as a package.
The rest are repositories that came with a paper, and one of them cannot legally be used
in a product at all.

The table below has two columns. The left column names the system and says how current it
is. The right column holds everything else about it: how it stores the map, what it is
best at, which image model it borrows its meaning from, its licence, how you obtain it,
and when to pick it.

Read the licence and the install together in each row, because those two decide whether a
system is a candidate for your work. These systems hold almost no numbers of their own,
since the meaning comes from an image model somebody else trained, so each row names that
image model instead of giving a parameter count. Every licence was read from the project's
own licence file.

| System | What decides it |
| --- | --- |
| [F3RM](#51-f3rm), most used in 2026 for arms | This system stores the map as a feature field, fitted like a NeRF, and it is the best here at grasping a named object or part with a robot arm. It keeps no weights of its own and uses the CLIP ViT-L/14@336px image model, the licence is MIT, and you install it with `pip install f3rm` or clone the repository. Pick it when you have an arm, a wrist camera and an NVIDIA graphics card. |
| [LERF](#52-lerf), historical | This system stores the map as a feature field as well, fitted like a NeRF, and it is best at looking at a scene and seeing what matches a word. It uses CLIP ViT-B/16, or ViT-L/14 in its `lerf-big` size, the licence is MIT, and you clone it and install it as a Nerfstudio method. Pick it when you want to see the idea working, with no robot. |
| [ConceptFusion](#53-conceptfusion), historical | This system keeps one feature per point, fused as the camera moves, and it is best at asking with words, a click or a sound. It uses OpenCLIP with the Segment Anything Model for the masks, the licence is MIT, and you clone it along with a branch of another library. Pick it when you want the fusion route and no fitting. |
| [ConceptGraphs](#54-conceptgraphs), most used in 2026 for rooms | This system keeps one feature per object, plus a record of their relations, and it is best at whole rooms and at questions about which object is where. It uses OpenCLIP with a detector and the Segment Anything Model, the licence is MIT, and you clone it, which is the longest install here. Pick it when the scene is a room and relations matter. |
| [GraspSplats](#55-graspsplats), worth betting on | This system stores the map as 3D Gaussians carrying part-level features, and it is best at re-fitting a scene fast and at following objects that move. Its size is `not stated`, because the features come from the feature splatting code. It has no licence file and it needs research-only code, so pick it when you are doing research and not shipping. |
| [OpenScene](#56-openscene), historical | This system keeps one feature per point of a finished room scan, and it is best at naming every point of a scanned room. It uses OpenSeg or LSeg pixel features, the licence is Apache-2.0, and you clone it, after which a pre-trained 3D model downloads itself. Pick it when you have a room scan and want it labelled. |

### 5.1 F3RM

F3RM is **most used in 2026** for robot arms, because it is the only system here that is
published as an installable package and comes with the robot side of the problem already
written.

F3RM stands for Feature Fields for Robotic Manipulation. William Shen, Ge Yang and four
colleagues at MIT published it at the Conference on Robot Learning in 2023
([paper](https://arxiv.org/abs/2308.07931), [code](https://github.com/f3rm/f3rm),
[package](https://pypi.org/project/f3rm/)). It fits a feature field, as section 3
described, and then adds the part a robot needs. From a few demonstrated grasps it
searches for the gripper position and rotation whose surroundings carry the features the
demonstrations had, and you can also ask in words which object to pick.

The obvious alternative is LERF, which F3RM is built on and which is better known. You
would pick F3RM because of that pose search, as LERF stops at showing you a heat map and
leaves every robot question to you. F3RM also distils DINO features as an alternative to
CLIP with one command-line flag, and DINO is the better of the two at telling parts
apart.

What it costs you is a pinned software stack. The README requires an NVIDIA card with
CUDA 11.7 or newer, states that the code is tested on Nerfstudio 0.3.3 and 0.3.4 only,
and reports peak memory of about 6 GB while training without the viewer and about 12 GB
with it, on a 24 GB card. That version pin is what most often goes wrong, so follow the
repository's own conda recipe rather than installing on top of an environment you
already have. The licence is MIT, and the CLIP weights it downloads are OpenAI's.

Fitting a field is one command, and the package also exposes the per-patch feature step
on its own, which is what you need to build your own map.

```bash
# Install the CUDA steps from the README first; this then adds Nerfstudio and F3RM.
pip install f3rm
ns-train f3rm --data <folder of photos with known camera poses>
```

```python
import torch

from f3rm.features import clip
from f3rm.features.clip import tokenize
from f3rm.features.clip_extract import CLIPArgs, extract_clip_features

device = torch.device("cuda")

# One list of numbers per patch of each photo, not one per photo.
patches = extract_clip_features(["frame_1.png", "frame_2.png"], device)
patches /= patches.norm(dim=-1, keepdim=True)

model, _ = clip.load(CLIPArgs.model_name, device=device)   # ViT-L/14@336px
words = model.encode_text(tokenize("the handle of a mug").to(device))
words /= words.norm(dim=-1, keepdim=True)

scores = patches @ words.T        # one score for every patch of every photo
print(scores.shape)
```

The library gives you dense patch features, and it skips CLIP's usual centre crop so that
the whole photo is covered. What you still supply is the camera poses, the depth, and the
step that turns patch scores into a place in 3D, unless you let `ns-train f3rm` fit the
field and do that for you.

### 5.2 LERF

LERF is **historical**. It is the system the feature field idea became well known through,
and the one to read before F3RM.

LERF stands for Language Embedded Radiance Fields. Justin Kerr, Chung Min Kim, Ken
Goldberg, Angjoo Kanazawa and Matthew Tancik at the University of California, Berkeley
published it at the International Conference on Computer Vision in 2023
([paper](https://arxiv.org/abs/2303.09553), [code](https://github.com/kerrj/lerf)). It
adds a language field beside the colour field of a NeRF, so you type a word in the viewer
and the matching part of the scene lights up. An earlier system,
[CLIP-Fields](https://github.com/notmahi/clip-fields), had already fitted a CLIP-style
field as a robot's memory of a room ([paper](https://arxiv.org/abs/2210.05663)), and its
licence is MIT as well.

You would run LERF rather than F3RM when there is no robot in the picture, because it is
the simpler of the two to install and it ships three sizes: `lerf`, `lerf-lite` for small
graphics cards, and `lerf-big`, which uses the larger CLIP image model.

What it costs you is the same Nerfstudio stack as F3RM, and one surprise that wastes an
afternoon. The viewer shows raw match scores, and the README says values below 0.5 are
already irrelevant, so you must set the range to -1 to 1 or turn normalisation on before
the pictures mean anything. The licence is MIT.

```bash
git clone https://github.com/kerrj/lerf && cd lerf
python -m pip install -e . && ns-install-cli
ns-train lerf --data <folder of photos with known camera poses>
```

You supply the photos and their poses, which Nerfstudio can work out from the photos
themselves. LERF gives back a fitted scene and a viewer, and nothing that a robot can act
on.

### 5.3 ConceptFusion

ConceptFusion is **historical**, and it is the clearest example of the fusion route from
section 3.

Krishna Murthy Jatavallabhula and sixteen colleagues published it at Robotics: Science
and Systems in 2023 ([paper](https://arxiv.org/abs/2302.07241),
[code](https://github.com/concept-fusion/concept-fusion)). It cuts each photo into
regions, gives each region a CLIP feature, spreads those features back over the pixels,
and fuses them into one point cloud as the camera moves. Because the question and the map
meet in CLIP's numbers, you can ask with words, by clicking a point, or with a sound.

The obvious alternative is a feature field such as F3RM. Fusion wins when you cannot wait
for a fit, because the map is ready as the camera moves and every point in it was
measured rather than interpolated. The reason it is marked historical is that its own
authors moved on: ConceptGraphs, below, is by many of the same people and is the one
still being maintained.

What it costs you is an install made of other people's branches, and a repository that
says so. The README states that the released code departs from the paper, since it uses
the Segment Anything Model instead of Mask2Former for the regions and drops the
uniqueness term the paper describes. It needs a specific branch of the gradslam library,
and your data has to be in that library's dataset format, which is the real work. The
licence is MIT.

```bash
# This branch of gradslam fuses features; the main branch cannot.
git clone https://github.com/gradslam/gradslam
cd gradslam && git checkout conceptfusion && pip install -e . && cd ..

git clone https://github.com/concept-fusion/concept-fusion
cd concept-fusion/examples
python extract_conceptfusion_features.py     # regions from SAM, then CLIP per region
python run_feature_fusion_and_save_map.py    # fuses them into saved-map/
```

You supply the photos, the poses, the depth, and a dataset class if your recording is not
one the library already reads. The two scripts give back a point cloud where every point
carries a feature.

### 5.4 ConceptGraphs

ConceptGraphs is **most used in 2026** for anything larger than a table, because keeping
one feature per object instead of one per point is what makes a whole room affordable.

Qiao Gu, Ali Kuwajerwala, Sacha Morin and thirteen colleagues published it in 2023
([paper](https://arxiv.org/abs/2309.16650),
[code](https://github.com/concept-graphs/concept-graphs)). A detector and the Segment
Anything Model cut each photo into objects, the objects are matched across photos and
merged into one three-dimensional object each, and each object keeps one CLIP feature and
a note of how it sits relative to the others. A
[language model](../../07_language-models/01_overview.md) can then read that record and
answer questions about position.

The obvious alternative is a dense map such as ConceptFusion or OpenScene. ConceptGraphs
wins on memory and on relations, because a room becomes a few hundred objects rather than
a few hundred thousand points carrying a few hundred numbers each. It loses where parts
matter, since a mug is one object in the graph and its handle is not in it at all, which
is what F3RM is for.

What it costs you is the longest install on this page: a detector, the Segment Anything
Model, a pinned gradslam, PyTorch3D and the faiss search library, on Python 3.10. The
deeper cost is that the map holds only what the detector found, so an object it missed is
not in the graph and no wording of the question will find it. The licence is MIT, and the
repository's `ali-dev` branch holds a newer real-time version that reads recordings from
an iPhone.

```bash
# First, detect and segment the objects in every frame of one scene.
python scripts/generate_gsa_results.py --dataset_root $REPLICA_ROOT \
    --dataset_config $REPLICA_CONFIG_PATH --scene_id room0 --class_set none --stride 5

# Then build the object map from those detections.
python slam/cfslam_pipeline_batch.py dataset_root=$REPLICA_ROOT \
    dataset_config=$REPLICA_CONFIG_PATH scene_id=room0 stride=5 \
    gsa_variant=none class_agnostic=True skip_bg=True sim_threshold=1.2 dbscan_eps=0.1
```

You supply a recording in one of the dataset formats it reads, and the thresholds, which
decide whether two views of a mug become one object or two. It gives back a file of
objects with their features, their point clouds and their relations.

### 5.5 GraspSplats

GraspSplats is **worth betting on**, because fitting a scene as 3D Gaussians is far
faster than fitting a NeRF, and speed is what a map needs when the robot keeps moving
things. The
[simulation chapter](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md)
in Book 3 describes the same shift for reconstruction in general.

Mazeyu Ji, Ri-Zhao Qiu, Xueyan Zou and Xiaolong Wang at the University of California, San
Diego published it in 2024 ([paper](https://arxiv.org/abs/2409.02084)). It fits a scene as
3D Gaussians that carry features, so it can answer questions about parts and not only
about whole objects, and it then follows the Gaussians of an object as that object moves,
so the map does not go out of date the moment the arm touches something.

The obvious alternative is F3RM, which is easier to install. You would choose this line of
work for the two things F3RM cannot do: re-fit a changed scene quickly, and keep up with
objects that move.

What it costs you is a licence problem that no amount of engineering fixes.
[The repository](https://github.com/jimazeyu/GraspSplats) contains no licence file at all,
so no rights are granted to anyone, and it builds on a fork of Inria's Gaussian-splatting
code, whose
[licence](https://github.com/graphdeco-inria/gaussian-splatting/blob/main/LICENSE.md)
allows research and evaluation only and requires Inria's written consent for commercial
use. [LangSplat](https://github.com/minghanqin/LangSplat), the best-known general-purpose
version of the same idea, carries that same Inria licence. Treat all of this as reading
and experiment, and check the licence of every submodule before anything ships.

```bash
# The feature splatting it depends on, at the branch GraspSplats needs.
git clone --recursive https://github.com/vuer-ai/feature-splatting-inria.git
cd feature-splatting-inria && git checkout roger/graspsplats_part
pip install -e submodules/diff-gaussian-rasterization    # compiled against CUDA 11.8
pip install -e submodules/simple-knn
```

You supply photos of the scene, a graphics card with CUDA 11.8, and the calibration
between the camera and the arm. The GraspSplats repository itself holds the robot side,
including the tracking of objects that move.

### 5.6 OpenScene

OpenScene is **historical** on this page, but it is still the easiest way to see
open-vocabulary 3D labelling without owning a robot.

Songyou Peng, Kyle Genova and four colleagues published it in 2022
([paper](https://arxiv.org/abs/2211.15654),
[code](https://github.com/pengsongyou/openscene)). It takes a finished room scan, gives
every point of it a feature copied from a pixel-level image model, and then trains a 3D
network to predict those features from geometry alone, so at question time no photos are
needed.

The obvious alternative is ConceptFusion, which fuses features as the camera moves.
OpenScene is the better choice when you already have a room scan and want every point
labelled, and it is the worse choice on a robot, because it expects whole-building
datasets rather than a wrist camera's view of a table.

What it costs you is the shape of its data. The evaluation runs on room-scan datasets, so
putting your own recording through it is a day of conversion, and its pixel features come
from OpenSeg or LSeg rather than plain CLIP, which is one more model to obtain. The
licence is Apache-2.0, and the repository has an interactive demo that the README says
needs no graphics card at all.

```bash
# Downloads a pre-trained 3D model and labels every point of a scanned scene.
sh run/eval.sh out/replica_openseg config/replica/ours_openseg_pretrained.yaml ensemble
```

You supply the processed scan and the fused 2D features, both of which the repository
documents how to obtain. It gives back a labelled point cloud and, with one option
changed, the per-point features as a NumPy file you can query yourself.

### 5.7 How to choose

For a robot arm on a table, start with F3RM, because it is installable, it was built for
exactly that case, and it answers questions about parts of objects as well as whole ones.

Three things change that choice. If the scene is a whole room and the questions are about
which object is where, use ConceptGraphs, and accept that it knows objects rather than
parts. If the arm keeps moving things and you are doing research rather than shipping a
product, follow the feature splatting line that GraspSplats belongs to, after reading the
Inria licence. If you already have a finished room scan and only want every point
labelled, use OpenScene.

Two of these are worth skipping unless you are reading rather than building. LERF teaches
the idea and leaves the robot work to you, and ConceptFusion has been overtaken by
ConceptGraphs from the same authors.

Whatever you choose, remember that a map records what the camera saw on the day it was built. The map holds what the
camera saw when you built it, so the first question to answer is how often your scene
changes.

---

## 6. Where to read next

- [Open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md)
    explains CLIP, Grounding DINO and SAM, which are the image models these maps
    borrow from.
- [Scene reconstruction](../02_most-used/02_scene-reconstruction.md) explains the NeRF
    fitting that feature fields build on.
- [Language models as planners](../../07_language-models/03_also-used/01_language-models-as-planners.md)
    shows how a language model breaks a request such as "tidy the table" into steps,
    each of which can be a question to a map like this.
- [Foundation models](../../../03_frameworks/08_frontier/02_foundation-models.md) in
    Book 3 covers the large models that link words, pictures and arm movements in one
    network.
- Go back to the [chapter overview](../01_overview.md) to see how this page fits with
    the other three.
