"""Generate the pictures used in docs/camera/finding-objects.md.

The images go to docs/images/camera/finding-objects/.

Photographs and camera pictures are saved as PNG, and the one drawn diagram as
SVG. Everything comes from the code in src/camera_basics, so the doc's pictures
cannot drift from what that code does.

The model parts need PyTorch, so run this in the vision environment:

  pixi run -e vision python docs/diagrams/finding_objects.py

The last figure needs the trained weights, which are made by:

  pixi run -e vision python src/camera_basics/train_a_model.py
"""

import pathlib
import sys
import textwrap

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
CODE: pathlib.Path = REPO_ROOT / 'src' / 'camera_basics'
sys.path.insert(0, str(CODE))

import cv2  # noqa: E402
from find_by_colour import (  # noqa: E402
    annotate,
    colour_mask,
    Found,
    largest_object,
    load_picture,
    tidy,
)
import matplotlib  # noqa: E402
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402  (must follow use)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
from train_a_model import draw_picture, HEIGHT, WIDTH  # noqa: E402
from ultralytics import ASSETS, YOLO  # noqa: E402
from ultralytics.engine.results import Results  # noqa: E402

IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'camera' / 'finding-objects'
TABLE: pathlib.Path = CODE / 'data' / 'table_colour.png'
WEIGHTS: pathlib.Path = CODE / 'models' / 'yolo11n.pt'
TRAINED: pathlib.Path = CODE / 'runs' / 'box' / 'weights' / 'best.pt'

INK: str = '#222222'
MUTED: str = '#777777'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'


def _save(fig: Figure, name: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, bbox_inches='tight', pad_inches=0.25, facecolor='white')
    plt.close(fig)
    print(f'wrote {IMAGES / name}')


def _show(ax: Axes, picture: NDArray[np.uint8], title: str) -> None:
    """Draw one picture on one panel, with a title. OpenCV's order is blue, green, red."""
    ax.imshow(cv2.cvtColor(picture, cv2.COLOR_BGR2RGB) if picture.ndim == 3 else picture,
              cmap=None if picture.ndim == 3 else 'grey')
    ax.set_title(title, fontsize=9.5, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])


def colour_steps() -> None:
    """Draw the three steps of finding the box by colour: picture, mask, and the blob."""
    picture: NDArray[np.uint8] = load_picture(TABLE)
    mask: NDArray[np.uint8] = tidy(colour_mask(picture))
    found: Found | None = largest_object(mask)
    assert found is not None                 # the box is always in this recorded picture

    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.1), facecolor='white')
    _show(axes[0], picture, 'the picture from the camera')
    _show(axes[1], mask, f'the mask: {int((mask > 0).sum()):,} red pixels')
    _show(axes[2], annotate(picture, found),
          f'the biggest blob: ({found.u:.1f}, {found.v:.1f})')
    _save(fig, 'colour_steps.png')


def dataset_samples() -> None:
    """Four of the pictures the training example draws, with the labels it writes."""
    rng: np.random.Generator = np.random.default_rng(seed=3)
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 4, figsize=(12, 2.6), facecolor='white')
    for panel in range(4):
        picture: NDArray[np.uint8]
        label: tuple[float, ...]
        picture, label = draw_picture(rng)
        middle_u: float
        middle_v: float
        box_width: float
        box_height: float
        middle_u, middle_v, box_width, box_height = label
        ax: Axes = axes[panel]
        _show(ax, picture, f'0 {middle_u:.3f} {middle_v:.3f} {box_width:.3f} {box_height:.3f}')
        ax.add_patch(Rectangle(((middle_u - box_width / 2) * WIDTH,
                                (middle_v - box_height / 2) * HEIGHT),
                               box_width * WIDTH, box_height * HEIGHT,
                               fill=False, edgecolor=GREEN, lw=1.4))
    fig.suptitle('drawn training pictures, and the label written for each one',
                 fontsize=10, color=INK, y=1.04)
    _save(fig, 'dataset_samples.png')


def model_photos() -> None:
    """Draw what the ready-made YOLO finds in the two photos that ship with it."""
    model: YOLO = YOLO(str(WEIGHTS))
    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), facecolor='white')
    for panel, photo in enumerate(('bus.jpg', 'zidane.jpg')):
        result: Results = model(ASSETS / photo, conf=0.25, verbose=False)[0]
        labels: str = ', '.join(
            f'{result.names[int(result.boxes.cls[i])]} {float(result.boxes.conf[i]):.2f}'
            for i in range(len(result.boxes)))
        _show(axes[panel], result.plot(), textwrap.fill(labels, 38))
    fig.suptitle('yolo11n, trained on COCO, on the two photos inside the ultralytics package',
                 fontsize=10, color=INK, y=1.0)
    _save(fig, 'model_photos.png')


def trained_on_the_table() -> None:
    """Draw the box found by colour beside the one found by the trained model."""
    if not TRAINED.exists():
        print(f'no trained weights at {TRAINED}: run train_a_model.py first')
        return
    picture: NDArray[np.uint8] = load_picture(TABLE)
    found: Found | None = largest_object(tidy(colour_mask(picture)))
    assert found is not None
    result: Results = YOLO(str(TRAINED))(TABLE, conf=0.25, verbose=False)[0]

    fig: Figure
    axes: NDArray[np.object_]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), facecolor='white')
    _show(axes[0], annotate(picture, found),
          f'by colour: ({found.u:.1f}, {found.v:.1f}), {found.width} x {found.height} pixels')
    if len(result.boxes):
        middle_u: float
        middle_v: float
        box_width: float
        box_height: float
        middle_u, middle_v, box_width, box_height = (float(v) for v in result.boxes.xywh[0])
        _show(axes[1], result.plot(line_width=1, font_size=8),
              f'by the trained model: ({middle_u:.1f}, {middle_v:.1f}), '
              f'{box_width:.0f} x {box_height:.0f} pixels')
    else:
        _show(axes[1], picture, 'by the trained model: nothing found')
    _save(fig, 'colour_and_model.png')


def three_ways() -> None:
    """Draw how the three ways fit together: colour or model gives a pixel, depth gives metres."""
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(11, 4.0), facecolor='white')
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 8)
    ax.axis('off')

    def box(x: float, y: float, width: float, height: float, text: str, colour: str,
            edge: str) -> None:
        ax.add_patch(Rectangle((x, y), width, height, facecolor=colour, edgecolor=edge,
                               lw=1.4, joinstyle='round'))
        ax.text(x + width / 2, y + height / 2, text, ha='center', va='center',
                fontsize=9.5, color=INK)

    def arrow(start: tuple[float, float], end: tuple[float, float], colour: str) -> None:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=13,
                                     color=colour, lw=1.3, shrinkA=0, shrinkB=0))

    box(0.3, 3.2, 3.6, 1.6, 'the colour\npicture', PALE_BLUE, BLUE)
    box(5.2, 5.4, 5.0, 1.6, 'a colour range\nfind_by_colour.py', PALE_GREEN, GREEN)
    box(5.2, 1.0, 5.0, 1.6, 'a trained model\nfind_with_model.py', PALE_GREEN, GREEN)
    box(11.5, 3.2, 3.4, 1.6, 'a pixel\n(u, v)', PALE_BLUE, BLUE)
    box(11.5, 0.2, 3.4, 1.3, 'the depth\npicture', PALE_BLUE, BLUE)
    box(16.2, 3.2, 5.4, 1.6, 'x, y, z in metres\ndepth_of_object.py', PALE_ORANGE, ORANGE)

    arrow((3.9, 4.4), (5.2, 6.0), GREEN)
    arrow((3.9, 3.6), (5.2, 1.9), GREEN)
    arrow((10.2, 6.0), (11.5, 4.4), GREEN)
    arrow((10.2, 1.9), (11.5, 3.6), GREEN)
    arrow((14.9, 4.0), (16.2, 4.0), ORANGE)
    arrow((14.9, 0.9), (16.2, 3.4), ORANGE)

    ax.text(7.7, 7.4, 'two ways to find the object', ha='center', fontsize=9.5, color=GREEN)
    ax.text(18.9, 5.2, 'the same arithmetic\nfor either way', ha='center', fontsize=9.5,
            color=ORANGE)
    ax.text(13.2, 2.1, 'a pixel is only a direction:\nthe depth makes it a place',
            ha='center', fontsize=9, color=MUTED)
    _save(fig, 'three_ways.svg')


if __name__ == '__main__':
    colour_steps()
    dataset_samples()
    model_photos()
    trained_on_the_table()
    three_ways()
