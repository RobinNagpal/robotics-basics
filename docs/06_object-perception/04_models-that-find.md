# Models that find objects

Models you download and run, which answer "what is this and which pixels is it
on". This is the other half of [the methods you write
yourself](03_programmed-methods.md): reach for these when the object is not one
colour, not one shape, or not something you can describe with a rule.

The document ends with training a model of your own, because that is what you do
when no downloadable model knows your objects — and with the datasets and
labelling tools that step needs.

Every licence below was read from the project's own `LICENSE` file or model card
in September 2026, not from a blog post. Where the code and the weights carry
different licences, both are given, because that catches people out regularly.
The full picture is in [licences and
platforms](06_licences-and-platforms.md).

## Contents

1. [Models you can download](#1-models-you-can-download)
2. [Models you would train yourself](#2-models-you-would-train-yourself)
3. [Datasets](#3-datasets)
4. [Labelling tools](#4-labelling-tools)

---

## 1. Models you can download

Everything in this section has weights you can fetch today and run without
training anything. Section 2 is the other case: models you train on your own
objects.

### 1.1 Box detectors

**What they are.** Models that return a rectangle and a class for each object they
recognise. They are the cheapest useful answer, they run fastest, and for a robot
working with well-separated objects on a table they are often all you need.

The table lists the ones worth knowing. Read it as: the first column is the model,
the second is what it is good at, and the third is the licence you would be
agreeing to.

| Model | What it is good at | Licence (code / weights) | Where |
| --- | --- | --- | --- |
| Ultralytics YOLO | the easiest to use, by a distance; fast; huge community | **AGPL-3.0** — see [section 10](#10-licences-and-the-one-that-will-catch-you-out) | [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) |
| RT-DETR | transformer detector with no need for non-maximum suppression; accurate at similar speed | Apache-2.0 / Apache-2.0 | [lyuwenyu/RT-DETR](https://github.com/lyuwenyu/RT-DETR), [weights](https://huggingface.co/PekingU/rtdetr_r50vd) |
| D-FINE | a refinement of RT-DETR, currently among the strongest real-time detectors | Apache-2.0 | [Peterande/D-FINE](https://github.com/Peterande/D-FINE) |
| DEIM | a training scheme that improves DETR-style detectors | Apache | [Intellindust-AI-Lab/DEIM](https://github.com/Intellindust-AI-Lab/DEIM) |
| RF-DETR | Ultralytics-like ergonomics without the AGPL; actively developed | Apache-2.0 | [roboflow/rf-detr](https://github.com/roboflow/rf-detr) |
| YOLOX | anchor-free YOLO with a genuinely permissive licence | Apache-2.0 | [Megvii-BaseDetection/YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) |
| Faster R-CNN, RetinaNet | the classics, in torchvision, trivially available | BSD-3 | [pytorch/vision](https://github.com/pytorch/vision) |

Five jobs a box detector suits:

- picking well-separated objects off a table or a conveyor
- counting things, where the box is only needed to say "one here"
- cueing a promptable segmenter, which needs a box to start from
- tracking objects between frames, where a box is enough to follow
- any job where the object is roughly as wide as it is long, so the box fits it

Five jobs it cannot do:

- gripping an odd shape, where the box's corners are not the object
- measuring, since the box of a tilted object belongs to no real dimension
- separating objects that overlap, where boxes overlap too
- anything needing the outline: avoiding a handle, finding a rim, fitting a
  profile
- finding an object whose class is not in the model's list

### 1.2 Mask models

**What they are.** Models that return the pixels of each object rather than a box.
This is the answer a robot usually wants, because it supports measuring and
gripping round a shape.

| Model | What it is good at | Licence | Where |
| --- | --- | --- | --- |
| Mask R-CNN | the workhorse; well understood; easy to fine-tune | torchvision BSD-3 throughout; Detectron2 code Apache-2.0 but its **weights are CC BY-SA 3.0** | [pytorch/vision](https://github.com/pytorch/vision), [detectron2](https://github.com/facebookresearch/detectron2) |
| Mask2Former | stronger masks; one architecture for all three kinds of segmentation | MIT, but the repository is **archived** | [facebookresearch/Mask2Former](https://github.com/facebookresearch/Mask2Former) |
| OneFormer | one model trained once, doing semantic, instance and panoptic | MIT | [SHI-Labs/OneFormer](https://github.com/SHI-Labs/OneFormer) |
| SegFormer | efficient semantic segmentation | **NVIDIA Source Code License — non-commercial** | [NVlabs/SegFormer](https://github.com/NVlabs/SegFormer) |
| mmdetection / mmsegmentation | a large library of implementations to train from | Apache-2.0 | [mmdetection](https://github.com/open-mmlab/mmdetection), [mmsegmentation](https://github.com/open-mmlab/mmsegmentation) |

Two notes that matter more than the accuracy numbers. Mask2Former's repository is
archived, which means no fixes and no new dependencies supported; its weights
still work and the code will rot. And mmdetection has not had a push since August
2024, so while it is still the widest collection of implementations, it is drifting
away from current PyTorch.

Five jobs a mask model suits:

- gripping round a shape, where the outline decides where the fingers go
- measuring an object's silhouette, which is the input to the
  [dimension document](05_models-that-measure.md)
- separating touching objects of the same class, which instance segmentation does
  by design
- excluding a handle, a spout or a label from a grasp
- any job where you need the area of something rather than a box around it

Five jobs it cannot do:

- run at high frame rate on a small computer, which is where a box detector wins
- recognise objects outside its training classes
- produce reliable boundaries on transparent or reflective objects
- give orientation, which a mask does not contain
- tell you anything in millimetres

### 1.3 Promptable segmenters: the Segment Anything family

**What it is.** You give the model a point, a box, or a rough region; it returns
the exact mask containing it. It does not name anything. Its strength is the
boundary, which is markedly better than anything trained per-class, and its
weakness is that something else must decide where to point.

**Why this rather than a mask model.** Because it works on objects it has never
seen, which a closed-set mask model cannot. In a robot cell this is the difference
between handling your five known parts and handling whatever a customer puts on
the table.

| Model | What it is | Licence (code / weights) | Where |
| --- | --- | --- | --- |
| SAM | the original; excellent boundaries; slow | Apache-2.0 / Apache-2.0 | [segment-anything](https://github.com/facebookresearch/segment-anything) |
| SAM 2 | adds video and is faster; the safe default | Apache-2.0 / Apache-2.0 | [sam2](https://github.com/facebookresearch/sam2) |
| SAM 3 | the newest; segments *every* instance matching a phrase | **bespoke "SAM License"**, weights gated | [sam3](https://github.com/facebookresearch/sam3) |
| SAM 3.1 | a drop-in update to SAM 3, March 2026 | same as SAM 3 | [weights](https://huggingface.co/facebook/sam3.1) |
| EdgeSAM, EdgeTAM | the two that run properly on Apple hardware | EdgeSAM **non-commercial**; EdgeTAM Apache-2.0 | [EdgeSAM](https://github.com/chongzhou96/EdgeSAM), [EdgeTAM](https://github.com/facebookresearch/EdgeTAM) |
| MobileSAM | a much smaller SAM for embedded use | Apache-2.0 | [MobileSAM](https://github.com/ChaoningZhang/MobileSAM) |
| FastSAM | a fast approximation, built on Ultralytics | **AGPL-3.0** | [FastSAM](https://github.com/CASIA-LMC-Lab/FastSAM) |

If the licence matters to you, SAM 2 is the one to reach for: it is the most
recent of the family that is plainly Apache-2.0 in both code and weights. SAM 3's
licence is a Meta community licence that does permit commercial use, but it is a
bespoke agreement with its own acceptable-use terms rather than a standard open
licence, so it needs reading rather than assuming. FastSAM is AGPL because it is
built on Ultralytics, which is the most commonly missed licence inheritance in
this whole field — and note that FastSAM's own README claims Apache-2.0 while its
`LICENSE` file is AGPL-3.0. When a repository contradicts itself, the licence file
is the one that counts.

SAM 3 is also more than a faster SAM. It does *promptable concept segmentation*:
given a short phrase it returns **every** instance matching it, which is the job
that previously needed Grounding DINO and SAM chained together. That makes it a
replacement for the pairing described in section 1.4, at the cost of a licence
that is not a standard open one.

Five jobs the SAM family suits:

- objects the robot has never seen and you cannot enumerate
- turning a detector's rough box into an accurate outline, which is the standard
  pairing
- labelling data: a human clicks, SAM produces the mask, which is how most
  labelling tools now work
- cluttered scenes where per-class models fall apart
- anything where boundary quality is what limits you

Five jobs it cannot do:

- start a pipeline, since nothing in it decides what to point at
- name the object, which is the entire "what is it" question
- run fast on a small computer, unless you use MobileSAM and accept the drop
- give consistent object identity across frames, without the video variant
- handle transparent objects, whose boundary is genuinely ambiguous in the image

### 1.4 Open-vocabulary models

**What they are.** Models you prompt with words. They were trained on pictures
paired with text, so they can find things that were never a class in any list.

| Model | What it does | Licence (code / weights) | Where |
| --- | --- | --- | --- |
| Grounding DINO | text in, boxes out; the standard choice | Apache-2.0 / Apache-2.0 | [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO), [weights](https://huggingface.co/IDEA-Research/grounding-dino-base) |
| Grounded-SAM | Grounding DINO for the box, SAM for the mask: text in, masks out | Apache-2.0 | [Grounded-Segment-Anything](https://github.com/IDEA-Research/Grounded-Segment-Anything) |
| OWLv2 | open-vocabulary detection from Google; strong and simple to run | Apache-2.0 | [weights](https://huggingface.co/google/owlv2-base-patch16-ensemble) |
| YOLO-World | real-time open-vocabulary detection | **GPL-3.0** | [YOLO-World](https://github.com/AILab-CVC/YOLO-World) |
| Florence-2 | one small model doing captioning, detection and grounding | MIT | [weights](https://huggingface.co/microsoft/Florence-2-large) |

The pairing worth knowing is **Grounding DINO plus SAM**, usually packaged as
Grounded-SAM. Between them they take a phrase and return a mask, with no training
and no class list, and both halves are Apache-2.0. For a robot that has to handle
objects you cannot enumerate in advance, this is the current default.

Five jobs open-vocabulary models suit:

- objects you can describe but not collect pictures of
- a long tail of rare items, as in a warehouse or a laboratory
- prototypes, where the class list is still changing every week
- taking an instruction in words — "pick up the blue mug" — and acting on it
- generating training labels for a smaller, faster model you then train yourself

Five jobs they cannot do:

- run in a few milliseconds on a small computer, which they are far from
- give repeatable answers to two phrasings of the same request
- distinguish things whose difference has no ordinary name — two similar valve
  bodies
- work where the object has no common-language description at all, which is most
  of manufacturing
- offer any guarantee, which is why safety-relevant decisions are not made this
  way

### 1.5 Backbones and features

**What they are.** Not object finders, but the feature extractors other things are
built on. They matter here because a strong backbone with a small trained head is
often the cheapest route to a good custom model.

[DINOv2](https://github.com/facebookresearch/dinov2) is Apache-2.0 and produces
features good enough that a simple classifier on top of them matches models
trained end to end. [DINOv3](https://github.com/facebookresearch/dinov3) is newer
and stronger, but is published under a bespoke DINOv3 licence rather than Apache,
so it needs reading before commercial use.

### 1.6 Open-vocabulary models that are not downloadable

One correction that catches people regularly. **Grounding DINO 1.5, 1.6, 1.6 Pro
and DINO-X have no open weights.** The repositories with those names contain
client code for a paid hosted service, and the Apache-2.0 licence on them covers
the client, not the model. Only the original Grounding DINO has downloadable
weights. A great many blog posts present the later versions as though you could
`pip install` them.

Similarly, Ultralytics **YOLO27 is announced and not released**, and Depth
Anything V2's Giant checkpoint has said "coming soon" for a long time.

### 1.7 Transparent and shiny objects

This deserves its own entry because it is the case that defeats everything above,
and because the honest state of it is not what people expect.

The classical approach is the depth hole from [section 5.7](03_programmed-methods.md#17-the-depth-hole-for-glass-and-chrome).
The reference work is [Lysenkov, Eruhimov and Bradski, RSS
2012](https://roboticsproceedings.org/rss08/p35.html), which deliberately used the
depth sensor's *failure* as the segmentation cue. The code from that lineage
([wg-perception/transparent_objects](https://github.com/wg-perception/transparent_objects))
is long unmaintained.

Since then the field has moved to learned depth completion, and the licensing is
awkward:

| Project | Licence | State |
| --- | --- | --- |
| [ClearGrasp](https://github.com/Shreeyak/cleargrasp) | Apache-2.0 | abandoned in 2021; still the standard citation for the problem |
| TransCG | **CC BY-NC-SA 4.0** | abandoned in 2022; the largest real dataset, and non-commercial |
| [ReMake](https://github.com/ChengYaofeng/ReMake) | **MIT** | 2026, and the most usable recent option: a monocular depth model plus an instance mask, completing the depth |
| [FoundationStereo](https://github.com/NVlabs/FoundationStereo) | **NVIDIA, non-commercial** | excellent, and not shippable |

Polarisation imaging is frequently suggested for this and, as
[section 4.5](02_sensors.md#22-thermal-polarisation-and-the-rest) says, there is essentially no
open-source work behind the suggestion.

## 2. Models you would train yourself

Everything so far assumes somebody else's classes. The moment your objects are
specific — your parts, your products — you train.

**You almost never train from scratch.** You fine-tune: take a model that already
knows what edges, textures and objects look like in general, and teach it your
classes with a few hundred labelled pictures. The camera area
[works through this](../05_camera/02_finding-objects.md#6-training-a-model-of-your-own)
with eighty pictures of one object, which is enough to see it work.

The choices, in the order most people should consider them:

| Route | When it is right | Licence |
| --- | --- | --- |
| [RF-DETR](https://github.com/roboflow/rf-detr) | a permissive detector with good ergonomics; the sensible default in 2026 | Apache-2.0 |
| [torchvision references](https://github.com/pytorch/vision/tree/main/references) | you want no framework at all, just PyTorch | BSD-3 |
| [segmentation_models_pytorch](https://github.com/qubvel-org/segmentation_models.pytorch) | semantic segmentation with a wide choice of backbones | MIT |
| [Hugging Face transformers](https://github.com/huggingface/transformers) | fine-tuning DETR, Mask2Former, OneFormer and friends | Apache-2.0 |
| [Detectron2](https://github.com/facebookresearch/detectron2) | you specifically need its Mask R-CNN recipes | Apache-2.0 code, **CC BY-SA 3.0 weights** |
| [Ultralytics](https://github.com/ultralytics/ultralytics) | the fastest path to a working model, if AGPL is acceptable | **AGPL-3.0** |
| [mmdetection](https://github.com/open-mmlab/mmdetection) | you need an implementation that exists nowhere else | Apache-2.0, **last updated August 2024** |

A newer route is worth knowing because it changes the economics. Use an
open-vocabulary model to *label* your data — Grounding DINO or SAM 3 generating
boxes and masks from a text prompt — then train a small, fast, permissively
licensed model on those labels. You get a model that runs in milliseconds on a
cheap computer, trained on data nobody had to draw by hand.

Five jobs training your own model suits:

- a fixed set of objects that a general model does not know
- anything that has to run fast on a small computer
- distinguishing objects that differ in ways with no common name
- a task where you need to control and version the model's behaviour
- meeting a licence constraint, by training your own weights on permissive code

Five jobs it does not:

- objects that change every week, where you would retrain every week
- a long tail of thousands of rare items
- projects with no way to collect and label a few hundred pictures
- proving anything before the mechanical and lighting side is settled
- one-off jobs, where an open-vocabulary model costs nothing and works today

## 3. Datasets

If you are training, you need data, and the licences here are stricter than the
code licences. Read this table as: what the annotations allow, then separately
what the images allow, because they are usually different and the images are
where the restriction bites.

| Dataset | Annotations | Images | Commercial use |
| --- | --- | --- | --- |
| [Open Images V7](https://storage.googleapis.com/openimages/web/index.html) | CC BY 4.0 | CC BY 2.0 | **yes — the only large one that is cleanly clear** |
| [COCO](https://cocodataset.org/) | CC BY 4.0 | Flickr terms, copyright per image | annotations yes, images are your own risk |
| [LVIS](https://www.lvisdataset.org/) | BSD | inherits COCO's | as COCO |
| [ADE20K](https://groups.csail.mit.edu/vision/datasets/ADE20K/) | BSD-3 | **non-commercial research and education only** | **no** |
| [Cityscapes](https://www.cityscapes-dataset.com/) | — | **non-commercial** | **no** |
| [Objects365](https://www.objects365.org/) | CC BY 4.0 | **academic purposes only**, registration required | **no** |
| [SA-1B](https://ai.meta.com/datasets/segment-anything/) | research licence | same | **no** |
| [GraspNet-1Billion](https://graspnet.net/) | CC BY-NC-SA 4.0 | same | **no** |

The short version for anyone building a product: **Open Images V7 is the one you
can use without thinking about it.** COCO's annotations are fine and its images
are a judgement call. The rest forbid commercial use, and a model trained on them
inherits the problem.

## 4. Labelling tools

| Tool | Licence | Self-hosted | Notes |
| --- | --- | --- | --- |
| [CVAT](https://github.com/cvat-ai/cvat) | MIT | yes | the standard; has SAM-assisted labelling built in |
| [Label Studio](https://github.com/HumanSignal/label-studio) | Apache-2.0 | yes | broader than vision; model-assisted via a backend |
| [FiftyOne](https://github.com/voxel51/fiftyone) | Apache-2.0 | yes | for looking at and curating a dataset rather than drawing on it |
| [X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) | **GPL-3.0** | yes | a wide model zoo for assisted labelling |
| [labelme](https://github.com/wkentaro/labelme) | **GPL-3.0** | yes | widely assumed to be MIT; it is not |
| [Roboflow](https://roboflow.com/) | hosted service | no | see the note below |

One thing about Roboflow's free tier that is easy to miss and matters
commercially: on the free plan your **data and models are public** on Roboflow
Universe. Keeping a dataset private requires a paid plan.

