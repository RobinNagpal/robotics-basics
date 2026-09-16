"""Find objects in a picture with a trained model: YOLO, in about three lines.

Colour only works when the object's colour is unique. To find a person, a chair
or a cup, a robot uses a model: a program whose behaviour was learned from
labelled example pictures rather than written by hand. It takes a picture and
gives back a list of boxes, each with a label and a confidence between 0 and 1.

The model here is **YOLO**, "you only look once", from Ultralytics. It is the
detector most robotics projects reach for, because one small file finds
everything in a picture in one pass, fast enough for a live camera even without
a graphics card. This uses yolo11n, the smallest of the family, 5.4 MB, trained
on **COCO**, a public set of 120,000 labelled photos covering 80 everyday
classes. The file downloads itself the first time into models/.

The pictures are the two that ship inside the ultralytics package, a street
photo and a football photo, plus this folder's own recorded frame of the table.

This file needs PyTorch, which is in the separate `vision` environment, so it is
run with -e vision:

  pixi run -e vision python src/camera_basics/find_with_model.py
"""

import pathlib

import cv2
import numpy as np
from ultralytics import ASSETS, YOLO
from ultralytics.engine.results import Boxes, Results

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
WEIGHTS: pathlib.Path = HERE / 'models' / 'yolo11n.pt'
TABLE: pathlib.Path = HERE / 'data' / 'table_colour.png'
OUT: pathlib.Path = HERE / 'out'

# Below this confidence, a detection is ignored. 0.25 is the usual starting
# point: lower finds more and invents more, higher is surer but misses things.
CONFIDENCE: float = 0.25


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def detect(model: YOLO, picture: pathlib.Path) -> Results:
    """Run the model on one picture, and give back what it found.

    These are the three lines that matter in the whole file: load the model,
    call it with a picture, take the first (and here only) result. A robot node
    does exactly this in its camera callback, with the array from cv_bridge in
    place of the path.
    """
    # Calling the model can also take a list of pictures, so it always answers
    # with a list of results; this asks for the one result of the one picture.
    # (ultralytics' type information covers every one of those ways of calling
    # it, so mypy is told to allow this one.)
    return model(picture, conf=CONFIDENCE, verbose=False)[0]  # type: ignore[index,return-value]


def describe(result: Results) -> None:
    """Print every detection: its label, how sure the model is, and where it is."""
    # A result has no boxes at all if the model was not run for detection, and
    # an empty list of them if it found nothing.
    boxes: Boxes | None = result.boxes
    if boxes is None or len(boxes) == 0:
        print('  nothing found')
        return
    print(f'  {"label":<10} {"sure":>5}  {"middle (u, v)":>16}  {"box (w x h)":>14}')
    for index in range(len(boxes)):
        box: Boxes = boxes[index]
        label: str = result.names[int(box.cls)]
        confidence: float = float(box.conf)
        # xywh is the box as its middle and its size, in pixels; xyxy would be
        # its two corners. Both are on the original picture's scale.
        middle_u: float
        middle_v: float
        width: float
        height: float
        middle_u, middle_v, width, height = (float(v) for v in box.xywh[0])
        print(f'  {label:<10} {confidence:>5.2f}  ({middle_u:6.1f}, {middle_v:6.1f})  '
              f'{width:6.0f} x {height:<5.0f}')


def main() -> None:
    """Run YOLO on two photos and on the recorded table picture."""
    OUT.mkdir(exist_ok=True)
    WEIGHTS.parent.mkdir(exist_ok=True)

    heading('1. The model')
    # YOLO(path) loads the weights, and downloads them first if the file is not
    # there yet. The weights are the numbers learned during training; the code
    # that uses them is the same for every YOLO model.
    model: YOLO = YOLO(str(WEIGHTS))
    print(f'{WEIGHTS.name}: {WEIGHTS.stat().st_size / 1e6:.1f} MB, '
          f'{len(model.names)} classes it can name')
    print('the first ten:', ', '.join(model.names[i] for i in range(10)))

    heading('2. A street photo')
    street: Results = detect(model, ASSETS / 'bus.jpg')
    describe(street)
    # How long each step took, in milliseconds.
    looking_ms: float = float(street.speed['inference'] or 0.0)
    print(f'  took {looking_ms:.0f} ms to look, on the processor, '
          f'for a {street.orig_shape[1]} x {street.orig_shape[0]} picture')
    cv2.imwrite(str(OUT / 'found_by_model_street.png'), street.plot())

    heading('3. A football photo')
    football: Results = detect(model, ASSETS / 'zidane.jpg')
    describe(football)
    cv2.imwrite(str(OUT / 'found_by_model_football.png'), football.plot())

    heading('4. The table from the simulation')
    table: Results = detect(model, TABLE)
    describe(table)
    print('  COCO has no class for "box", and this picture looks nothing like a')
    print('  photo, so the model has nothing useful to say about it. A model only')
    print('  knows what it was trained on. train_a_model.py trains one that does')
    print('  know this box.')
    cv2.imwrite(str(OUT / 'found_by_model_table.png'), table.plot())

    heading('5. From a detection to a place')
    street_boxes: Boxes | None = street.boxes
    if street_boxes is not None and len(street_boxes):
        best: Boxes = street_boxes[int(np.argmax(street_boxes.conf))]
        label: str = street.names[int(best.cls)]
        middle_u: float = float(best.xywh[0][0])
        middle_v: float = float(best.xywh[0][1])
        print(f'the surest detection is "{label}" at pixel '
              f'({middle_u:.1f}, {middle_v:.1f})')
    print('A box in a picture is still only a direction. To reach for the object,')
    print('the robot reads the depth at those pixels and turns them into metres,')
    print('with the same two lines as depth_of_object.py.')
    print(f'\nwrote the annotated pictures to {OUT}')


if __name__ == '__main__':
    main()
