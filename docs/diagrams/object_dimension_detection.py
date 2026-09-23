"""Generate the diagrams used in docs/07_object-dimension-detection/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/object-dimension-detection/<doc-name>/.

Every number in these pictures comes from the repo's own camera: fx = fy =
277.1 px, cx = 160, cy = 120, which is a 320x240 sensor with a 60 degree
horizontal field of view. The same four numbers the camera area uses.

Run with:  pixi run python docs/diagrams/object_dimension_detection.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,  # noqa: E402
                                Polygon, Rectangle)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'object-dimension-detection'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PURPLE: str = '#7b5aa6'
GREY: str = '#9a9a9a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'
PALE_PURPLE: str = '#ece4f5'
PALE_GREY: str = '#eeeeee'
PALE_RED: str = '#fbe4e8'

FX: float = 277.1          # pixels; the repo's camera


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


# --------------------------------------------------------------------------
# overview.md
# --------------------------------------------------------------------------

def no_scale() -> None:
    """One picture cannot give a size, and the arithmetic says why.

    Two objects, one twice as far away and twice as big, fall on exactly the
    same 60 pixels. Nothing in the picture separates them, so a size read off
    a single image is a size that was assumed somewhere else.
    """
    fig, ax = plt.subplots(figsize=(13.6, 6.6))
    ax.set_xlim(-6, 116)
    ax.set_ylim(-26, 52)
    ax.axis('off')

    eye = np.array([2.0, 14.0])
    ax.add_patch(Polygon([[eye[0] - 4, eye[1] - 5], [eye[0] - 4, eye[1] + 5],
                          [eye[0], eye[1] + 3], [eye[0], eye[1] - 3]],
                         closed=True, facecolor=PALE_GREY, edgecolor=INK, lw=1.3))
    ax.text(-2.0, 22.0, 'camera\nfx = 277.1 px', fontsize=9.2, color=INK,
            ha='center', linespacing=1.6)

    # The two rays that bound the object, at 60 px apart on the sensor.
    for sign in (1, -1):
        ax.plot([eye[0], 104], [eye[1], eye[1] + sign * 15.5], color=MUTED,
                lw=1.0, ls=(0, (5, 4)), zorder=1)

    near_z, far_z = 0.340, 0.680
    near_w = 60 * near_z / FX * 1000.0
    far_w = 60 * far_z / FX * 1000.0

    for x, z, w, colour, pale in ((40, near_z, near_w, BLUE, PALE_BLUE),
                                  (80, far_z, far_w, PURPLE, PALE_PURPLE)):
        half = (x - eye[0]) / (104 - eye[0]) * 15.5
        ax.add_patch(Rectangle((x - 5, eye[1] - half), 10, 2 * half,
                               facecolor=pale, edgecolor=colour, lw=1.8, zorder=3))
        ax.text(x, eye[1] + half + 3.2, f'{w:.1f} mm wide', fontsize=10.0,
                color=colour, ha='center')
        ax.text(x, eye[1] - half - 6.0, f'{z * 1000:.0f} mm away', fontsize=9.4,
                color=colour, ha='center')

    # Both land on the same patch of sensor.
    ax.add_patch(FancyBboxPatch((104, 4), 9, 20, boxstyle='round,pad=0.5',
                                facecolor='white', edgecolor=INK, lw=1.2))
    ax.add_patch(Rectangle((106, 8), 5, 12, facecolor=PALE_GREY,
                           edgecolor=INK, lw=1.4))
    ax.text(108.5, 26.5, 'what the sensor sees', fontsize=9.4, color=INK, ha='center')
    ax.text(108.5, 1.0, '60 px', fontsize=9.6, color=INK, ha='center')

    ax.text(55, 46,
            'One picture cannot tell you how big something is',
            fontsize=13.0, color=INK, ha='center', weight='bold')
    ax.text(55, 40.5,
            'Twice as far and twice as big fall on exactly the same pixels.',
            fontsize=10.4, color=MUTED, ha='center')

    ax.text(-6, -10,
            'To get a size you have to add one fact the picture does not contain. '
            'There are only three kinds, and every method in this document\n'
            'is one of them:   the distance to the object   ·   the plane it is '
            'standing on   ·   something of known size in the frame.',
            fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'overview', 'no-scale.svg')


def pixels_to_mm() -> None:
    """The one calculation underneath every camera measurement.

    Pixels become an angle by dividing by the focal length, and an angle becomes
    a length by multiplying by the distance. The second step is where the error
    comes from, because the distance is measured too.
    """
    fig, ax = plt.subplots(figsize=(14.2, 5.4))
    ax.set_xlim(0, 146)
    ax.set_ylim(-20, 34)
    ax.axis('off')

    steps = [
        ('what you count', '60 px', 'the width of the mask,\nedge to edge', GREY, PALE_GREY),
        ('divide by fx', '60 / 277.1\n= 0.2166', 'now it is an angle,\nnot a count', BLUE, PALE_BLUE),
        ('multiply by the depth', 'x 0.340 m', 'the one number the\npicture did not give you',
         ORANGE, PALE_ORANGE),
        ('what you get', '73.6 mm', 'a length, at last', GREEN, PALE_GREEN),
    ]

    x = 2.0
    for i, (title, body, note, colour, pale) in enumerate(steps):
        ax.add_patch(FancyBboxPatch((x, 6), 28, 17, boxstyle='round,pad=0.8',
                                    facecolor=pale, edgecolor=colour, lw=1.4))
        ax.text(x + 14, 20.0, title, fontsize=9.6, color=colour, ha='center')
        ax.text(x + 14, 14.0, body, fontsize=12.6, color=INK, ha='center',
                va='center', linespacing=1.5)
        ax.text(x + 14, 3.0, note, fontsize=8.8, color=MUTED, ha='center',
                va='top', linespacing=1.6)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + 30.5, 14.5), (x + 35.5, 14.5),
                                         color=MUTED, lw=1.5, arrowstyle='-|>',
                                         mutation_scale=14))
        x += 36

    ax.text(73, 30.5, 'One pixel is 1.227 mm at 340 mm, and 3.609 mm at one metre',
            fontsize=12.2, color=INK, ha='center', weight='bold')

    ax.text(2, -8.5,
            'The third box is the whole difficulty. Everything else is exact '
            'arithmetic on numbers you already have, and the depth is the one\n'
            'quantity that had to be measured — so the accuracy of the answer is '
            'the accuracy of the depth, multiplied through.',
            fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'overview', 'pixels-to-mm.svg')


def error_budget() -> None:
    """Where the millimetres actually go, for a 73.6 mm object at 340 mm.

    Drawn from the arithmetic above rather than from a study: each bar is the
    error in the measured width that the named mistake produces on its own.
    """
    fig, ax = plt.subplots(figsize=(12.4, 6.0))

    z = 0.340
    sources = [
        ('the mask edge is 1 px out\non each side', 2 * 1 * z / FX * 1000, BLUE),
        ('the depth reading is 7 mm out\n(a RealSense D405, +/-2% of range)', 60 * 0.007 / FX * 1000, ORANGE),
        ('the depth reading is 20 mm out\n(the same camera at a shiny rim)', 60 * 0.020 / FX * 1000, RED),
        ('hand-eye calibration is 1 deg out\nover a 340 mm reach', np.tan(np.radians(1.0)) * 340, PURPLE),
    ]

    names = [s[0] for s in sources]
    values = [s[1] for s in sources]
    colours = [s[2] for s in sources]

    y = np.arange(len(sources))[::-1]
    ax.barh(y, values, height=0.52, color=colours, alpha=0.85)
    for yi, v in zip(y, values):
        ax.text(v + 0.12, yi, f'{v:.1f} mm', fontsize=10.4, color=INK, va='center')

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.8, color=INK, linespacing=1.6)
    ax.set_xlabel('millimetres of error it puts into the final answer, for a 73.6 mm '
                  'object at 340 mm', fontsize=10.0, color=INK)
    ax.set_xlim(0, max(values) * 1.28)
    ax.tick_params(labelsize=9.2, colors=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)

    ax.set_title('Four ways to be a few millimetres wrong, at 340 mm',
                 fontsize=12.6, color=INK, pad=14)

    fig.text(0.06, -0.10,
             'The first three make the object the wrong size. The fourth makes it the '
             'right size in the wrong place, which the gripper\nfeels the same way. '
             'Neither of the bottom two improves if you swap the segmentation model for '
             'a better one.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'overview', 'error-budget.svg')


if __name__ == '__main__':
    no_scale()
    pixels_to_mm()
    error_budget()
