"""Train a model to find this robot's box, by fine-tuning YOLO on 80 pictures.

A model only knows what it was trained on, and no public model knows your
robot's parts, your bins or your crates. Teaching it one new thing takes four
ingredients, and this file goes through all four:

  1. pictures
  2. a label for every object in every picture: which class, and where
  3. a small file saying where the pictures are and what the classes are called
  4. a starting model, which is trained a little further on your pictures

The fourth is called **fine-tuning**, and it is what almost everyone does. The
starting model, yolo11n, has already learned on 120,000 photos what edges,
corners and surfaces look like; only the last part of it has to learn "box".
That is why 80 pictures and a minute on a laptop are enough, when training from
nothing would need tens of thousands of pictures and a day on a graphics card.

The pictures here are drawn by this file, to look like the camera area's
simulated table, which keeps the example offline and quick, and means the labels
are exact because the drawing knows where it put the box. A real project takes
photos of the real object from every side, in the light the robot will work in,
and labels them by hand in a tool such as Label Studio or CVAT. Everything after
the drawing is what a real project does.

This file needs PyTorch, which is in the separate `vision` environment:

  pixi run -e vision python src/camera_basics/train_a_model.py       # 40 epochs, ~3 min
  pixi run -e vision python src/camera_basics/train_a_model.py 12    # quicker, less sure

Training writes to runs/ and the dataset to datasets/; both are ignored by git.
"""

import pathlib
import shutil
import sys

import cv2
from find_by_colour import as_picture, colour_mask, Found, largest_object, load_picture, tidy
import numpy as np
from numpy.typing import NDArray
from ultralytics import YOLO
from ultralytics.engine.results import Boxes, Results

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
WEIGHTS: pathlib.Path = HERE / 'models' / 'yolo11n.pt'
DATASET: pathlib.Path = HERE / 'datasets' / 'box'
RUNS: pathlib.Path = HERE / 'runs'
TABLE: pathlib.Path = HERE / 'data' / 'table_colour.png'
OUT: pathlib.Path = HERE / 'out'

WIDTH: int = 320
HEIGHT: int = 240
# Everything is drawn twice this size and then shrunk, which softens every edge
# the way a camera and a renderer do. Hard, perfectly sharp edges are one of the
# things that make drawn pictures unlike real ones.
SCALE: int = 2
TRAIN_PICTURES: int = 64
VAL_PICTURES: int = 16
DEFAULT_EPOCHS: int = 40


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def draw_table(rng: np.random.Generator) -> NDArray[np.uint8]:
    """Draw the grey table, with its grid lines, as the simulated camera sees it.

    The table in the recorded picture is grey 121 with grid lines about 20
    levels darker, three pixels wide, every 40 pixels. Each drawn picture varies
    those a little, so that the model learns "a red square on a grey table"
    rather than one exact shade.
    """
    grey: int = int(rng.integers(105, 135))          # the light is never the same twice
    table: NDArray[np.uint8] = np.full((HEIGHT * SCALE, WIDTH * SCALE, 3), grey,
                                       dtype=np.uint8)
    spacing: int = int(rng.integers(36, 46)) * SCALE
    offset: int = int(rng.integers(0, spacing))
    thickness: int = 3 * SCALE
    line: tuple[int, int, int] = (max(grey - int(rng.integers(15, 28)), 0),) * 3
    for x in range(offset, WIDTH * SCALE, spacing):
        cv2.line(table, (x, 0), (x, HEIGHT * SCALE), line, thickness)
    for y in range(offset, HEIGHT * SCALE, spacing):
        cv2.line(table, (0, y), (WIDTH * SCALE, y), line, thickness)
    return table


def draw_box(picture: NDArray[np.uint8],
             rng: np.random.Generator) -> tuple[int, int, int, int]:
    """Draw one red box somewhere on the table, and say which pixels it covers.

    The box is drawn as the camera sees it from above: the lit top face, and one
    darker side face where the box is not straight below the camera. The
    returned corners are the label: the smallest box round everything drawn.
    """
    size: int = int(rng.integers(26, 70)) * SCALE
    left: int = int(rng.integers(10, WIDTH - size // SCALE - 10)) * SCALE
    top: int = int(rng.integers(10, HEIGHT - size // SCALE - 10)) * SCALE
    shade: int = int(rng.integers(-25, 25))
    # OpenCV colours are blue, green, red. The simulated box's top is (202, 121,
    # 112) in red, green, blue, and its side is (98, 56, 51).
    face: tuple[int, int, int] = (112 + shade, 121 + shade, 202 + shade)
    side_colour: tuple[int, int, int] = (51 + shade // 2, 56 + shade // 2, 98 + shade // 2)

    side: int = int(rng.integers(0, size // 4 + 1))  # how much of a side face shows
    on_the_left: bool = bool(rng.integers(0, 2))
    box_left: int = left - side if on_the_left else left
    if side:
        cv2.rectangle(picture, (box_left, top), (box_left + side + size, top + size),
                      side_colour, -1)
    cv2.rectangle(picture, (left, top), (left + size, top + size), face, -1)
    return min(left, box_left), top, max(left + size, box_left + side + size), top + size


def draw_picture(rng: np.random.Generator) -> tuple[NDArray[np.uint8], tuple[float, ...]]:
    """Draw one training picture, and give back its label.

    A YOLO label is five numbers: the class number, then the middle and the size
    of the box, each divided by the picture's width or height so that they are
    between 0 and 1. Dividing like that means the same label still fits after
    the picture is made bigger or smaller, which training does all the time.
    """
    picture: NDArray[np.uint8] = draw_table(rng)
    left: int
    top: int
    right: int
    bottom: int
    left, top, right, bottom = draw_box(picture, rng)

    # Shrink to the real size. INTER_AREA averages the pixels it merges, which
    # is what softens the edges.
    picture = as_picture(cv2.resize(picture, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA))
    # A camera's picture is never perfectly smooth, so add a little noise. Some
    # pictures get none, because the simulated camera's are clean.
    spread: float = float(rng.uniform(0.0, 2.5))
    noise: NDArray[np.int16] = rng.normal(0, spread, picture.shape).astype(np.int16)
    picture = np.clip(picture.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    middle_u: float = (left + right) / 2 / (WIDTH * SCALE)
    middle_v: float = (top + bottom) / 2 / (HEIGHT * SCALE)
    box_width: float = (right - left) / (WIDTH * SCALE)
    box_height: float = (bottom - top) / (HEIGHT * SCALE)
    return picture, (middle_u, middle_v, box_width, box_height)


def make_dataset() -> pathlib.Path:
    """Draw the pictures and write them, their labels and the dataset file.

    YOLO expects one folder of pictures and one of labels, split into train and
    val, with a label file per picture under the same name. The **train**
    pictures are the ones it learns from; the **val** (validation) pictures it
    never learns from, and they are how you find out whether it learned the
    object or just memorised the training pictures.
    """
    if DATASET.exists():
        shutil.rmtree(DATASET)
    rng: np.random.Generator = np.random.default_rng(seed=0)
    for split, count in (('train', TRAIN_PICTURES), ('val', VAL_PICTURES)):
        (DATASET / 'images' / split).mkdir(parents=True)
        (DATASET / 'labels' / split).mkdir(parents=True)
        for index in range(count):
            picture: NDArray[np.uint8]
            label: tuple[float, ...]
            picture, label = draw_picture(rng)
            cv2.imwrite(str(DATASET / 'images' / split / f'{index:03d}.png'), picture)
            numbers: str = ' '.join(f'{value:.6f}' for value in label)
            # "0" is the class number: this dataset has one class, and it is box.
            (DATASET / 'labels' / split / f'{index:03d}.txt').write_text(f'0 {numbers}\n')

    yaml: pathlib.Path = DATASET / 'box.yaml'
    yaml.write_text(f'path: {DATASET}\n'
                    'train: images/train\n'
                    'val: images/val\n'
                    'names:\n'
                    '  0: box\n')
    return yaml


def main() -> None:
    """Draw a dataset, fine-tune YOLO on it, and try the result on the real picture."""
    epochs: int = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_EPOCHS
    OUT.mkdir(exist_ok=True)

    heading('1. The pictures and their labels')
    yaml: pathlib.Path = make_dataset()
    print(f'{TRAIN_PICTURES} pictures to learn from and {VAL_PICTURES} to be tested on, '
          f'in {DATASET}')
    example: pathlib.Path = DATASET / 'labels' / 'train' / '000.txt'
    print(f'{example.relative_to(DATASET)} says: {example.read_text().strip()}')
    print('  that is: class 0 (box), middle across, middle down, width, height,')
    print('  each as a share of the picture, so all between 0 and 1')

    heading('2. The dataset file')
    print(yaml.read_text().strip())

    heading(f'3. Training for {epochs} epochs')
    print('An epoch is one pass through all the training pictures. After each one')
    print('the model is tested on the val pictures, and the best is kept.')
    model: YOLO = YOLO(str(WEIGHTS))
    model.train(data=str(yaml), epochs=epochs, imgsz=WIDTH, batch=8, device='cpu',
                project=str(RUNS), name='box', exist_ok=True, seed=0, plots=False,
                verbose=False, val=True)

    heading('4. How well it does on the pictures it never learned from')
    scores = model.val(data=str(yaml), imgsz=WIDTH, device='cpu', verbose=False, plots=False)
    print(f'mAP50    {scores.box.map50:.3f}   how well the boxes it draws match the')
    print('                  labels, counting a box right when it overlaps the true')
    print('                  one by more than half. 1.000 is perfect.')
    print(f'mAP50-95 {scores.box.map:.3f}   the same, averaged over stricter and')
    print('                  stricter overlaps: the number papers quote.')

    heading('5. The trained model on the real recorded picture')
    best: pathlib.Path = RUNS / 'box' / 'weights' / 'best.pt'
    print(f'the trained weights are {best.relative_to(HERE)}, '
          f'{best.stat().st_size / 1e6:.1f} MB')
    trained: YOLO = YOLO(str(best))
    found: Results = trained(TABLE, conf=0.25, verbose=False)[0]  # type: ignore[index,assignment]
    boxes: Boxes | None = found.boxes
    if boxes is None or len(boxes) == 0:
        print('nothing found. A short training ranks boxes well but is not sure of')
        print('them, so its confidence stays under the 0.25 needed here: train for')
        print('more epochs.')
    for index in range(len(boxes) if boxes is not None else 0):
        assert boxes is not None            # it cannot be, inside this loop
        box: Boxes = boxes[index]
        middle_u: float
        middle_v: float
        width: float
        height: float
        middle_u, middle_v, width, height = (float(v) for v in box.xywh[0])
        print(f'{found.names[int(box.cls)]} {float(box.conf):.2f} at pixel '
              f'({middle_u:.1f}, {middle_v:.1f}), {width:.0f} x {height:.0f} pixels')
    cv2.imwrite(str(OUT / 'trained_on_table.png'), found.plot())

    # The same box, found by colour, for comparison.
    by_colour: Found | None = largest_object(tidy(colour_mask(load_picture(TABLE))))
    if by_colour is not None:
        print(f'find_by_colour.py says   ({by_colour.u:.1f}, {by_colour.v:.1f}), '
              f'{by_colour.width} x {by_colour.height} pixels')

    print('\nThe pictures it learned from were drawn, and the picture it was just')
    print('tested on came from the simulated camera, so this is the real test:')
    print('it was never shown this picture, or anything rendered like it.')
    print(f'wrote {OUT / "trained_on_table.png"}')


if __name__ == '__main__':
    main()
