# camera_basics

The three ways a robot finds an object in a picture, as small programs you can
run: by its **colour**, by adding **depth** to turn the pixel into metres, and
with a **trained model**. The fourth program trains a model of your own.

The doc for this folder is
[docs/camera/finding-objects.md](../../docs/camera/finding-objects.md).

## Running it

```
make camera.colour     # find the box by colour, then measure it with the depth picture
make camera.model      # find objects with YOLO, a ready-made model
make camera.train      # teach YOLO this robot's box, from 80 drawn pictures (~3 minutes)
```

The same, without make:

```
pixi run python src/camera_basics/find_by_colour.py
pixi run python src/camera_basics/depth_of_object.py
pixi run -e vision python src/camera_basics/find_with_model.py
pixi run -e vision python src/camera_basics/train_a_model.py        # or: ... 12
```

The first two are plain OpenCV and NumPy and run in the normal environment. The
last two need PyTorch, which lives in a separate pixi environment called
`vision`, so they are run with `-e vision`. That keeps the large machine
learning packages out of the ROS environment. The first run of either downloads
the YOLO weights, 5.4 MB, into `models/`.

## The files

| File | What it does |
| --- | --- |
| `find_by_colour.py` | Threshold the picture in HSV, tidy the mask, take the biggest blob, and say which pixel it is on. |
| `depth_of_object.py` | Read the depth at those pixels and turn the pixel into x, y, z in metres, with the lens numbers. |
| `find_with_model.py` | Run YOLO on two photos and on the recorded table picture, and print what it found and how sure it is. |
| `train_a_model.py` | Draw 80 labelled pictures of the box, fine-tune YOLO on them, score it, and try it on the recorded picture. |

Each file runs on its own and prints its steps in order. `depth_of_object.py`
and `train_a_model.py` import from `find_by_colour.py` rather than repeat it.

## The layout

```
data/                  one frame recorded from the camera area's Gazebo simulation
  table_colour.png       the colour picture, 320 x 240
  table_depth.npz        the depth picture, one distance in metres per pixel
  table_camera.json      the lens: fx, fy, cx, cy
models/                  the downloaded YOLO weights            (ignored by git)
datasets/box/            the drawn pictures and their labels    (ignored by git)
runs/box/                what training produced, including best.pt  (ignored by git)
out/                     annotated pictures the programs write  (ignored by git)
```

The recorded frame comes from `src/camera_one_box`, the Gazebo simulation in the
camera area: a camera 0.40 m above a table, looking straight down at a red box
6 cm across. It is kept here as plain files so that this folder needs no ROS.
A real robot gets exactly these three things from its camera driver, as
`sensor_msgs/Image` and `sensor_msgs/CameraInfo` messages.
