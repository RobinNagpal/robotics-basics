# Licences, platforms and the comparison grids

The cross-cutting document: what you are allowed to ship, what will run on your
machine, how it all fits into ROS 2, and every method in this area side by side.

It exists separately because these questions do not belong to finding or to
measuring. They are the same questions whichever half you are working on, and
answering them twice is how the two halves quietly drift apart.

If you read one section of this whole area, read section 1. The most popular
object detector in the world is published under a licence that makes it unusable
in a commercial product without paying, and most tutorials do not mention it.

## Contents

1. [Licences, and the one that will catch you out](#1-licences-and-the-one-that-will-catch-you-out)
2. [Frameworks and libraries](#2-frameworks-and-libraries)
3. [What runs on an Apple Silicon Mac](#3-what-runs-on-an-apple-silicon-mac)
4. [Putting it in ROS 2](#4-putting-it-in-ros-2)
5. [The comparison grids](#5-the-comparison-grids)

---

## 1. Licences, and the one that will catch you out

**Ultralytics YOLO is AGPL-3.0.** It is the most popular object detector in the
world, it is what almost every tutorial uses, and its licence obliges you to
publish the source of anything you combine it with — including, because of the
AGPL's network clause, software you never distribute but merely run as a service.
Ultralytics' own documentation states that the pretrained weights carry the same
terms regardless of how you obtained them. A commercial licence is available and
is priced by negotiation.

That is not a criticism of the licence, which is a legitimate choice. It is a
warning that a great many projects have adopted it without noticing, and the
noticing usually happens late.

The same inheritance catches anything built on Ultralytics, including FastSAM,
YOLOE, and the popular `yolo_ros` wrapper.

**The permissive alternatives exist and are good.** RF-DETR, RT-DETR, D-FINE,
DEIM and YOLOX are all Apache-2.0, all competitive, and none of them will make a
lawyer unhappy.

Beyond that, five patterns are worth recognising:

- **Code permissive, weights not.** Depth Anything V2's small weights are
  Apache-2.0 and its large ones are CC BY-NC. YOLO-NAS has Apache-2.0 code and
  non-commercial weights. Detectron2's code is Apache-2.0 and its weights are
  CC BY-SA. Always check the model card, not the repository badge.
- **NVIDIA research licences are non-commercial** and asymmetric: they permit
  NVIDIA to use the same work commercially. SegFormer, FoundationPose,
  FoundationStereo, DOPE and CenterPose are all in this group.
- **Open weights are not open source.** SAM 3, DINOv3 and the Gemma family ship
  bespoke agreements that permit commercial use with conditions attached. They
  need reading, not assuming.
- **No licence is worse than a restrictive one.** SAM-6D has no licence file at
  all, which means default copyright and no permission to use it for anything.
- **The dataset licence flows into your model.** Training on ADE20K or
  GraspNet-1Billion gives you weights with a provenance problem.

## 2. Frameworks and libraries

Read these as: what state each one is in, verified by its last commit in
September 2026. A stale framework is a slow problem rather than an obvious one.

### 2.1 For finding objects


| Framework | Licence | State |
| --- | --- | --- |
| [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 since 4.5; BSD-3 at 4.4 and earlier | very active. **5.0.0 shipped June 2026** and restructured the modules, so 4.x code does not port straight across; 4.x is still maintained in parallel |
| [PyTorch](https://github.com/pytorch/pytorch) / [torchvision](https://github.com/pytorch/vision) | BSD-3 | the foundation of nearly everything here |
| [Hugging Face transformers](https://github.com/huggingface/transformers) | Apache-2.0 | very active; version 5 landed January 2026 |
| [Open3D](https://github.com/isl-org/Open3D) | MIT | active; v0.20.0 in September 2026, with native Apple Silicon wheels |
| [PCL](https://github.com/PointCloudLibrary/pcl) | BSD-3 | active in C++; its **Python bindings are dead** |
| [Detectron2](https://github.com/facebookresearch/detectron2) | Apache-2.0 | frozen — no tagged release since 2021 |
| [mmdetection](https://github.com/open-mmlab/mmdetection) / [mmsegmentation](https://github.com/open-mmlab/mmsegmentation) | Apache-2.0 | **two years stale**, both last pushed August 2024 |
| [supervision](https://github.com/roboflow/supervision) | MIT | active; the glue between detectors, trackers and annotations |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | MIT | the portable way to deploy, including on Apple hardware |
| [coremltools](https://github.com/apple/coremltools) | BSD-3 | the route to Apple's Neural Engine |
| [MLX](https://github.com/ml-explore/mlx) | MIT | Apple Silicon machine learning; the realistic way to run large vision-language models on a Mac |

### 2.2 For measuring objects

| [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 since 4.5 | calibration, markers, contours, stereo | native wheels |
| [Open3D](https://github.com/isl-org/Open3D) | MIT | point clouds, plane fitting, oriented boxes, registration | native `arm64` wheels |
| [PCL](https://github.com/PointCloudLibrary/pcl) | BSD-3 | the same, in C++, and what ROS uses | C++ yes, Python no |
| [trimesh](https://github.com/mikedh/trimesh) | MIT | meshes, volumes, oriented bounds, minimum cylinders | pure Python |
| [COLMAP](https://github.com/colmap/colmap) | BSD-3 | photogrammetry; the reference implementation | prebuilt `arm64` build; **dense reconstruction needs CUDA** |
| [OpenMVG](https://github.com/openMVG/openMVG) | MPL-2.0 | structure from motion | CPU |
| [OpenMVS](https://github.com/cdcseacave/openMVS) | **AGPL-3.0** | dense reconstruction and meshing | CUDA disabled on macOS, so CPU |
| [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | Apache-2.0 | neural reconstruction | `nerfacto` works on MPS; `splatfacto` does not |
| [Brush](https://github.com/ArthurBrussee/brush) | Apache-2.0 | Gaussian splatting | **yes, natively** — the only one in this list that is both permissive and Apple-native |
| [mrcal](https://github.com/dkogan/mrcal) | Apache-2.0 | calibration with uncertainty estimates | CPU |
| [CGAL](https://www.cgal.org/) | **split GPL and LGPL** | computational geometry | — |
| [libigl](https://github.com/libigl/libigl) | core MPL-2.0, **some modules GPL** | geometry processing | — |

Two licence notes. **CGAL's kernel is LGPL but most of the algorithms you would
actually want are GPL**, so it must be checked package by package. And
**libigl's GitHub badge says GPL-3.0 and is misleading** — the core is MPL-2.0
and only some optional modules are GPL. In both cases, read the files.

## 3. What runs on an Apple Silicon Mac

For finding objects, the general answer is better than its reputation, because of one pattern worth
knowing.

**A great many models whose original repository requires CUDA have a pure-PyTorch
reimplementation in Hugging Face `transformers` that does not.** Deformable DETR's
port now uses plain PyTorch `grid_sample` by default, with the compiled kernel an
opt-in download; Mask2Former's
and OneFormer's ports never had one; Grounding DINO's port is pure PyTorch; and —
the useful one — **SAM 3 is in `transformers` from version 5.0.0, with no compiled
kernels at all**, including its tracker and video heads. So "the repository needs
CUDA" and "it will not run on your Mac" are different statements, and the second
is often false.

| Works on Apple Silicon | Does not |
| --- | --- |
| OpenCV, Open3D (native wheels), PCL in C++ | NVIDIA Isaac ROS, entirely — it needs a Jetson or an Ampere-or-newer NVIDIA card |
| torchvision detectors and Mask R-CNN, on MPS | Deformable DETR, DINO-DETR, Mask2Former and OneFormer **from their original repositories** |
| RT-DETR, D-FINE, DEIM, RF-DETR, YOLOX — no compilation needed | Grounded-SAM's local install |
| Ultralytics, with `device="mps"` | YOLACT++ and SOLOv2's deformable-convolution variants |
| SAM, SAM 2 and SAM 3 via `transformers` | mmcv's CUDA operators |
| EdgeTAM, which has a real CoreML build; EdgeSAM too, but it is **S-Lab License 1.0, non-commercial** | NVIDIA TAO Toolkit |
| ONNX Runtime, CoreML, MLX | TensorRT |

Four measured figures worth quoting, because most Apple Silicon claims in this
field are guesses. Each is given with its source, since that is the difference
between a figure and a rumour.

| Figure | Machine | Source |
| --- | --- | --- |
| Depth Anything V2 Small, **24.58 ms** | M3 Max, Neural Engine dominant | [Apple's own model card](https://huggingface.co/apple/coreml-depth-anything-v2-small) |
| the same model, **32.80 ms** | M1 Max | the same card |
| EdgeSAM, **38.7 frames per second** | iPhone 14 | [the authors' own table](https://github.com/chongzhou96/EdgeSAM) |
| FastSAM-s **58.0 ms**, MobileSAM **23,802 ms** | 2025 M4 Air, 16 GB, CPU | [Ultralytics' benchmark](https://docs.ultralytics.com/models/fast-sam/) |

The last row looks like a four-hundredfold difference between two models that are
both meant to be small, and it is worth reading the footnote before drawing that
conclusion. Ultralytics measured the YOLO-derived models through ONNX Runtime and
the SAM-derived ones through PyTorch, so part of that gap is the runtime rather
than the model. The safe reading is the weaker one: **on Apple hardware, what
decides your speed is usually whether anyone has done the export work — to CoreML,
to ONNX — and not how many parameters the model has.** A small model nobody has
exported is a slow model.

### 3.1 For measuring objects


| Works | Does not |
| --- | --- |
| OpenCV, Open3D, trimesh, PCL in C++ | every NVIDIA research model: FoundationPose, FoundationStereo, Instant-NGP, Neuralangelo |
| COLMAP's sparse reconstruction, from a prebuilt `arm64` build | COLMAP's **dense** stage, which needs CUDA |
| OpenMVS, which disables CUDA on macOS | `gsplat`, and Nerfstudio's `splatfacto` |
| Brush, for Gaussian splatting | NVIDIA Isaac ROS, entirely |
| Marigold, which has an explicit `--apple_silicon` flag | Depth Anything 3 as documented, which expects XFormers |
| HappyPose, which documents a CPU path | every other 6-DoF method in [models that measure](05_models-that-measure.md#3-pose-estimation-when-you-have-a-model) |
| librealsense and OrbbecSDK v2, with some friction | Zivid and Photoneo, which have no macOS build at all |
| ROS 2, through [RoboStack](https://robostack.github.io/) | ROS 2 from official binaries — Apple Silicon has no support tier at all |

The last row is worth stating plainly, because it is not documented anywhere
obvious. In every ROS 2 platform table, macOS appears only in the `amd64` row at
tier 3. **The macOS cell in the `arm64` row is empty in every distribution.**
RoboStack, a community conda redistribution, is the only practical route, and it
is what this repo uses.

## 4. Putting it in ROS 2

ROS 2's current long-term release is **Lyrical Luth**, from May 2026 — listed as
active in `rosdistro`'s own index, though note that REP 2000 has not been updated
to carry it and still ends at Kilted Kaiju. Jazzy
Jalisco remains supported to 2029 and is the safer choice today.

Perception results travel as
[vision_msgs](https://github.com/ros-perception/vision_msgs) (Apache-2.0), which
defines `Detection2DArray`, `Detection3DArray` and the classification types.
Anything you write should publish those rather than invent its own.

| Package | Licence | What it is for |
| --- | --- | --- |
| [vision_msgs](https://github.com/ros-perception/vision_msgs) | Apache-2.0 | the standard message types for detections |
| [vision_opencv](https://github.com/ros-perception/vision_opencv) | Apache-2.0 | `cv_bridge`, between ROS images and OpenCV |
| [image_pipeline](https://github.com/ros-perception/image_pipeline) | BSD | rectification, calibration, stereo |
| [perception_pcl](https://github.com/ros-perception/perception_pcl) | BSD-3 | PCL inside ROS |
| [yolo_ros](https://github.com/mgonzs13/yolo_ros) | **GPL-3.0** | the de facto Ultralytics wrapper — note the licence, twice over |
| [Isaac ROS](https://github.com/NVIDIA-ISAAC-ROS) | mixed | see below |

**A warning about Isaac ROS that is easy to miss.** Its perception packages are
Apache-2.0, which looks reassuring. But `isaac_ros_nitros`, the zero-copy
transport every one of those nodes depends on, is under NVIDIA's own proprietary
Isaac ROS Software License. An Apache-2.0 badge on `isaac_ros_yolov8` does not
make your deployment Apache-2.0. It also runs only on a Jetson or an
Ampere-or-newer NVIDIA card — there is no CPU-only path and no Apple Silicon path.

### 4.1 Packages for measuring

| [vision_opencv](https://github.com/ros-perception/vision_opencv) | Apache-2.0 | `image_geometry`'s `PinholeCameraModel` is the pixels-to-metres tool |
| [image_pipeline](https://github.com/ros-perception/image_pipeline) | BSD | rectification, stereo, camera calibration |
| [perception_pcl](https://github.com/ros-perception/perception_pcl) | BSD-3 | PCL inside ROS |
| [octomap](https://github.com/OctoMap/octomap) | BSD | occupancy mapping, which MoveIt uses for obstacles |
| [easy_handeye2](https://github.com/marcoesposito1988/easy_handeye2) | LGPL-3.0 | hand-eye calibration |
| [happypose_ros](https://github.com/agimus-project/happypose_ros) | BSD-2 | 6-DoF pose, and the one with a CPU path |

**One thing MoveIt's perception pipeline is not for.** It builds an octomap of
unknown obstacles so the planner can avoid them. It does not measure objects and
was never meant to. Using it for dimensioning is a category error, and a common
one.

## 5. The comparison grids

Everything in one place. Speed is an order of magnitude on ordinary hardware
rather than a benchmark figure, because the benchmark figure depends on a card
you probably do not have.

### 5.1 Finding the object


| Approach | Gives you | Speed | Needs training | Unknown objects | Licence risk |
| --- | --- | --- | --- | --- | --- |
| colour range | mask | ~1 ms | no | no | none |
| background subtraction | mask | ~1 ms | no | yes | none |
| contours, connected components | regions | ~1 ms | no | yes | none |
| template matching | position | ms to s | no | no | none |
| watershed, GrabCut | mask | tens of ms | no | yes | none |
| plane removal and clustering | 3D clumps | ~10 ms | no | **yes** | none |
| depth hole | transparent regions | ~1 ms | no | yes | none |
| box detector, trained | boxes and classes | ~10 ms | yes | no | **AGPL if Ultralytics** |
| mask model, trained | masks and classes | tens of ms | yes | no | check the weights |
| SAM family | masks, no labels | 0.1 to 1 s | no | **yes** | SAM 2 safest |
| open-vocabulary | boxes or masks from text | 0.1 to 1 s | no | **yes** | mixed |
| SAM 3 | every instance matching a phrase | ~30 ms on a large GPU | no | **yes** | bespoke licence |

### 5.2 Measuring the object

| known depth, two-line calculation | one dimension | a few per cent | a depth sensor | no |
| the plane it stands on | full profile | about a millimetre | a calibrated table | **yes** |
| a marker of known size | scale on that plane | 0.6 to 3 mm in X and Y, ~3x worse in Z | a printed marker | yes |
| smallest rotated rectangle | length, width, angle | pixel-limited | a mask, and a face-on view | no |
| oriented box from a point cloud | all three dimensions | as good as the cloud | a depth sensor | no |
| solid of revolution | the complete profile | about a millimetre | one side-on picture | **yes** |
| touch | one dimension | hundredths of a millimetre | a contact sensor, and seconds | **yes** |
| consumer depth sensor | everything visible | 2 to 5 mm at 1 m | the sensor | no |
| industrial scanner | everything visible | 0.2 to 0.5 mm | thousands of pounds | partly |
| monocular metric depth | a dense guess | **5 to 20 per cent** | a GPU | no |
| stereo matching | dense depth | baseline-limited | two cameras, calibrated | no |
| 6-DoF pose from a model | position and orientation | millimetres | a CAD model | no |
| photogrammetry or splatting | a full 3D model | sub-millimetre, **once scaled** | many views, and a scale | no |